# Phase 0.5 -- `other`-section reclassification report

REPORT ONLY. No `Section` rows created, no data moved. This proposes a home
for each of the 378 card items currently parked in the `other` dumping-ground
section, for maintainer sign-off before any migration.

Proposed section keys drawn from: `test_plan`, `decision`, `open_question`,
`risk`, `scope`, `definition_of_done`, `dependency`, `note` (residual).
Classification is heuristic (keyword-based) and advisory.

## Proposed distribution

| proposed section | items |
|---|---|
| note | 257 |
| file_reference | 81 |
| scope | 15 |
| test_plan | 12 |
| decision | 6 |
| open_question | 4 |
| dependency | 2 |
| definition_of_done | 1 |
| **total** | **378** |

## Per-item proposals

| card # | card title | item order | first 80 chars | proposed section |
|---|---|---|---|---|
| 1 | DjangoType core foundation | 0 | `DjangoObjectType` (graphene-django) / `@strawberry_django.type` (strawberry-gra | note |
| 1 | DjangoType core foundation | 1 | core foundational subsystem: `DjangoType` base, Meta validation, scalar/relation | note |
| 1 | DjangoType core foundation | 2 | `django_strawberry_framework/types/base.py` | file_reference |
| 1 | DjangoType core foundation | 3 | `django_strawberry_framework/types/converters.py` | file_reference |
| 1 | DjangoType core foundation | 4 | `django_strawberry_framework/types/resolvers.py` | file_reference |
| 1 | DjangoType core foundation | 5 | `tests/types/test_base.py` | file_reference |
| 1 | DjangoType core foundation | 6 | `tests/types/test_converters.py` | file_reference |
| 1 | DjangoType core foundation | 7 | `tests/types/test_resolvers.py` | file_reference |
| 1 | DjangoType core foundation | 8 | The public shape is intentionally narrow and explicit. | note |
| 1 | DjangoType core foundation | 9 | Deferred Meta keys are rejected, not silently accepted. | decision |
| 1 | DjangoType core foundation | 10 | Definition-order independence is now covered by `{{card_ref:0}}`. | note |
| 2 | Optimizer O1-O6 foundation | 0 | strawberry-graphql-django ships a heavy optimizer extension; graphene-django has | note |
| 2 | Optimizer O1-O6 foundation | 1 | heavy optimizer extension: relation resolvers, selection-tree walker, root-gated | note |
| 2 | Optimizer O1-O6 foundation | 2 | `django_strawberry_framework/optimizer/extension.py` | file_reference |
| 2 | Optimizer O1-O6 foundation | 3 | `django_strawberry_framework/optimizer/walker.py` | file_reference |
| 2 | Optimizer O1-O6 foundation | 4 | `django_strawberry_framework/optimizer/plans.py` | file_reference |
| 2 | Optimizer O1-O6 foundation | 5 | `tests/optimizer/test_extension.py` | file_reference |
| 2 | Optimizer O1-O6 foundation | 6 | `tests/optimizer/test_walker.py` | file_reference |
| 2 | Optimizer O1-O6 foundation | 7 | `tests/optimizer/test_plans.py` | file_reference |
| 2 | Optimizer O1-O6 foundation | 8 | Shipped behavior is consolidated into `docs/GLOSSARY.md`; source/tests are the t | note |
| 3 | Optimizer O4 nested prefetch chains | 3 | Design record for the O4 slice split out from the broader optimizer foundation. | note |
| 4 | Optimizer beyond slices B1-B8 | 0 | continuation of {{card_ref:0}}'s optimizer lineage (⚛️ parity-adjacent). | note |
| 4 | Optimizer beyond slices B1-B8 | 1 | eight optimizer sub-features B1–B8: AST plan cache, FK-id elision, strictness mo | note |
| 4 | Optimizer beyond slices B1-B8 | 2 | `django_strawberry_framework/optimizer/extension.py` | file_reference |
| 4 | Optimizer beyond slices B1-B8 | 3 | `django_strawberry_framework/optimizer/hints.py` | file_reference |
| 4 | Optimizer beyond slices B1-B8 | 4 | `django_strawberry_framework/optimizer/field_meta.py` | file_reference |
| 4 | Optimizer beyond slices B1-B8 | 5 | `django_strawberry_framework/optimizer/plans.py` | file_reference |
| 4 | Optimizer beyond slices B1-B8 | 6 | `tests/optimizer/test_extension.py` | file_reference |
| 4 | Optimizer beyond slices B1-B8 | 7 | `tests/optimizer/test_hints.py` | file_reference |
| 4 | Optimizer beyond slices B1-B8 | 8 | `tests/optimizer/test_field_meta.py` | file_reference |
| 4 | Optimizer beyond slices B1-B8 | 9 | `tests/optimizer/test_plans.py` | file_reference |
| 4 | Optimizer beyond slices B1-B8 | 10 | B8 went beyond the initial simple exact-match diff and now handles subtree-aware | note |
| 4 | Optimizer beyond slices B1-B8 | 11 | Fragment-spread directive and multi-operation cache-key bugs have been fixed in  | note |
| 5 | DjangoType contract and boundary | 3 | Contract companion to the 0.0.3 public-surface documentation pass. | note |
| 6 | Documentation/status positioning for shipped Layer 2 | 0 | internal docs / status-positioning card — no upstream-parity surface. | note |
| 6 | Documentation/status positioning for shipped Layer 2 | 1 | docs pass: `docs/README.md`, `docs/GLOSSARY.md`, `docs/TREE.md` quickstart + sta | note |
| 6 | Documentation/status positioning for shipped Layer 2 | 2 | `docs/README.md` | file_reference |
| 6 | Documentation/status positioning for shipped Layer 2 | 3 | `docs/GLOSSARY.md` | file_reference |
| 6 | Documentation/status positioning for shipped Layer 2 | 4 | `docs/TREE.md` | file_reference |
| 6 | Documentation/status positioning for shipped Layer 2 | 5 | User-facing docs avoid internal slice shorthand; maintainer docs can still use i | note |
| 7 | 0.0.4 onboarding docs and spec consolidation | 0 | internal docs cleanup / spec consolidation — no upstream-parity surface. | note |
| 7 | 0.0.4 onboarding docs and spec consolidation | 1 | onboarding-doc consolidation across README / docs / CHANGELOG; completed spec co | note |
| 7 | 0.0.4 onboarding docs and spec consolidation | 2 | `README.md` | file_reference |
| 7 | 0.0.4 onboarding docs and spec consolidation | 3 | `docs/README.md` | file_reference |
| 7 | 0.0.4 onboarding docs and spec consolidation | 4 | `docs/GLOSSARY.md` | file_reference |
| 7 | 0.0.4 onboarding docs and spec consolidation | 5 | `docs/TREE.md` | file_reference |
| 7 | 0.0.4 onboarding docs and spec consolidation | 6 | `CHANGELOG.md` | file_reference |
| 7 | 0.0.4 onboarding docs and spec consolidation | 7 | Future in-flight design docs use the `docs/spec-<NNN>-<topic>-<0_0_X>.md` conven | note |
| 8 | Definition-order independence design | 3 | Problem-space design record for definition-order independence. | note |
| 9 | Rich schema architecture | 3 | Architecture design record paired with the narrower 0.0.4 foundation implementat | note |
| 10 | 0.0.4 foundation slice (definition-order independence) | 0 | internal Layer-2 foundation (`DjangoTypeDefinition`, finalizer, pending-relation | note |
| 10 | 0.0.4 foundation slice (definition-order independence) | 1 | definition-order-independent finalizer, pending-relation registry, manual-overri | note |
| 10 | 0.0.4 foundation slice (definition-order independence) | 2 | `django_strawberry_framework/types/definition.py` | file_reference |
| 10 | 0.0.4 foundation slice (definition-order independence) | 3 | `django_strawberry_framework/types/relations.py` | file_reference |
| 10 | 0.0.4 foundation slice (definition-order independence) | 4 | `django_strawberry_framework/types/finalizer.py` | file_reference |
| 10 | 0.0.4 foundation slice (definition-order independence) | 5 | `django_strawberry_framework/types/base.py` | file_reference |
| 10 | 0.0.4 foundation slice (definition-order independence) | 6 | `django_strawberry_framework/types/converters.py` | file_reference |
| 10 | 0.0.4 foundation slice (definition-order independence) | 7 | `django_strawberry_framework/types/resolvers.py` | file_reference |
| 10 | 0.0.4 foundation slice (definition-order independence) | 8 | `django_strawberry_framework/registry.py` | file_reference |
| 10 | 0.0.4 foundation slice (definition-order independence) | 9 | `tests/types/test_definition_order.py` | file_reference |
| 10 | 0.0.4 foundation slice (definition-order independence) | 10 | `tests/types/test_definition_order_schema.py` | file_reference |
| 10 | 0.0.4 foundation slice (definition-order independence) | 11 | `tests/optimizer/test_definition_order.py` | file_reference |
| 10 | 0.0.4 foundation slice (definition-order independence) | 12 | `tests/test_registry.py` | file_reference |
| 10 | 0.0.4 foundation slice (definition-order independence) | 13 | `examples/fakeshop/apps/library/models.py` | file_reference |
| 10 | 0.0.4 foundation slice (definition-order independence) | 14 | `examples/fakeshop/apps/library/schema.py` | file_reference |
| 10 | 0.0.4 foundation slice (definition-order independence) | 15 | `examples/fakeshop/test_query/test_library_api.py` | file_reference |
| 10 | 0.0.4 foundation slice (definition-order independence) | 16 | `CHANGELOG.md` | file_reference |
| 10 | 0.0.4 foundation slice (definition-order independence) | 17 | `docs/SPECS/spec-010-foundation-0_0_4.md` | file_reference |
| 10 | 0.0.4 foundation slice (definition-order independence) | 18 | `docs/feedback.md` | file_reference |
| 10 | 0.0.4 foundation slice (definition-order independence) | 19 | The forward-reserved slots on `DjangoTypeDefinition` are the architectural seam  | note |
| 10 | 0.0.4 foundation slice (definition-order independence) | 20 | The pending-resolution pattern (record at class creation, resolve at finalizatio | note |
| 10 | 0.0.4 foundation slice (definition-order independence) | 21 | The previous foundation-slice in-progress cards have been retired; this card is  | note |
| 11 | Stale placeholder cleanup | 0 | internal test/doc cleanup. | test_plan |
| 11 | Stale placeholder cleanup | 1 | replace stale M2M / forward-reference skips with definition-order tests. | scope |
| 11 | Stale placeholder cleanup | 2 | `tests/types/test_definition_order.py` | file_reference |
| 11 | Stale placeholder cleanup | 3 | `tests/types/test_definition_order_schema.py` | file_reference |
| 11 | Stale placeholder cleanup | 4 | `tests/optimizer/test_definition_order.py` | file_reference |
| 11 | Stale placeholder cleanup | 5 | `{{card_ref:0}}` | note |
| 12 | 0.0.4 version and release alignment | 0 | release housekeeping (version alignment). | note |
| 12 | 0.0.4 version and release alignment | 1 | align package metadata / runtime version / lockfile / tests / changelog on `0.0. | note |
| 12 | 0.0.4 version and release alignment | 2 | `pyproject.toml` | file_reference |
| 12 | 0.0.4 version and release alignment | 3 | `django_strawberry_framework/__init__.py` | file_reference |
| 12 | 0.0.4 version and release alignment | 4 | `tests/base/test_init.py` | file_reference |
| 12 | 0.0.4 version and release alignment | 5 | `uv.lock` | note |
| 12 | 0.0.4 version and release alignment | 6 | `CHANGELOG.md` | file_reference |
| 13 | Real M2M coverage | 0 | test hygiene. | test_plan |
| 13 | Real M2M coverage | 1 | replace test-only M2M / cardinality fixtures with real `library` models; add pac | test_plan |
| 13 | Real M2M coverage | 2 | `examples/fakeshop/apps/library/models.py` | file_reference |
| 13 | Real M2M coverage | 3 | `examples/fakeshop/test_query/test_library_api.py` | file_reference |
| 13 | Real M2M coverage | 4 | `tests/types/test_definition_order.py` | file_reference |
| 13 | Real M2M coverage | 5 | `tests/optimizer/test_definition_order.py` | file_reference |
| 14 | Move test fixture out of example settings | 0 | test hygiene. | test_plan |
| 14 | Move test fixture out of example settings | 1 | remove the `tests.fixtures.apps` fixture app + unmanaged cardinality fixtures; s | scope |
| 14 | Move test fixture out of example settings | 2 | `examples/fakeshop/config/settings.py` | file_reference |
| 14 | Move test fixture out of example settings | 3 | `examples/fakeshop/apps/library/models.py` | file_reference |
| 14 | Move test fixture out of example settings | 4 | `docs/SPECS/spec-014-testing_shift-0_0_4.md` | file_reference |
| 14 | Move test fixture out of example settings | 5 | `AGENTS.md` | file_reference |
| 14 | Move test fixture out of example settings | 6 | `docs/TREE.md` | file_reference |
| 15 | 0.0.5 Relay interfaces and Node foundation | 0 | both upstreams ship Relay Node interfaces; this shipped our 🍓-shaped Relay Node  | note |
| 15 | 0.0.5 Relay interfaces and Node foundation | 1 | Relay Node foundation: `Meta.interfaces`, four `resolve_*` defaults, `id: Global | note |
| 15 | 0.0.5 Relay interfaces and Node foundation | 2 | `django_strawberry_framework/types/base.py` | file_reference |
| 15 | 0.0.5 Relay interfaces and Node foundation | 3 | `django_strawberry_framework/types/relay.py` | file_reference |
| 15 | 0.0.5 Relay interfaces and Node foundation | 4 | `django_strawberry_framework/types/finalizer.py` | file_reference |
| 15 | 0.0.5 Relay interfaces and Node foundation | 5 | `tests/types/test_relay_interfaces.py` | file_reference |
| 15 | 0.0.5 Relay interfaces and Node foundation | 6 | `tests/types/test_definition_order_schema.py` | file_reference |
| 15 | 0.0.5 Relay interfaces and Node foundation | 7 | `tests/optimizer/test_relay_id_projection.py` | file_reference |
| 15 | 0.0.5 Relay interfaces and Node foundation | 8 | `tests/test_registry.py` | file_reference |
| 15 | 0.0.5 Relay interfaces and Node foundation | 9 | `examples/fakeshop/test_query/test_library_api.py` | file_reference |
| 15 | 0.0.5 Relay interfaces and Node foundation | 10 | `examples/fakeshop/apps/library/schema.py` (`GenreType` declares `Meta.interface | note |
| 15 | 0.0.5 Relay interfaces and Node foundation | 11 | `CHANGELOG.md` | file_reference |
| 15 | 0.0.5 Relay interfaces and Node foundation | 12 | `docs/GLOSSARY.md` | file_reference |
| 15 | 0.0.5 Relay interfaces and Node foundation | 13 | `docs/README.md` | file_reference |
| 15 | 0.0.5 Relay interfaces and Node foundation | 14 | `TODAY.md` | file_reference |
| 15 | 0.0.5 Relay interfaces and Node foundation | 15 | `pyproject.toml` | file_reference |
| 15 | 0.0.5 Relay interfaces and Node foundation | 16 | `django_strawberry_framework/__init__.py` | file_reference |
| 15 | 0.0.5 Relay interfaces and Node foundation | 17 | `tests/base/test_init.py` | file_reference |
| 15 | 0.0.5 Relay interfaces and Node foundation | 18 | `uv.lock` | note |
| 15 | 0.0.5 Relay interfaces and Node foundation | 19 | Borrowed patterns from `strawberry-django` (spec "Borrowing posture", Decision 3 | decision |
| 15 | 0.0.5 Relay interfaces and Node foundation | 20 | `Meta.interfaces` is the first `0.0.4`-reserved `DjangoTypeDefinition` slot that | note |
| 16 | `FieldMeta` single-source-of-truth consolidation and mirror retirement | 0 | internal metadata-architecture refactor; no consumer-visible API change. | scope |
| 16 | `FieldMeta` single-source-of-truth consolidation and mirror retirement | 1 | consolidate field metadata onto `DjangoTypeDefinition` (single source of truth)  | note |
| 16 | `FieldMeta` single-source-of-truth consolidation and mirror retirement | 2 | Commit `de35a62` (`refactor(types,optimizer): consolidate metadata onto DjangoTy | scope |
| 16 | `FieldMeta` single-source-of-truth consolidation and mirror retirement | 3 | `django_strawberry_framework/types/base.py` | file_reference |
| 16 | `FieldMeta` single-source-of-truth consolidation and mirror retirement | 4 | `django_strawberry_framework/types/converters.py` | file_reference |
| 16 | `FieldMeta` single-source-of-truth consolidation and mirror retirement | 5 | `django_strawberry_framework/types/resolvers.py` | file_reference |
| 16 | `FieldMeta` single-source-of-truth consolidation and mirror retirement | 6 | `django_strawberry_framework/optimizer/walker.py` | file_reference |
| 16 | `FieldMeta` single-source-of-truth consolidation and mirror retirement | 7 | `django_strawberry_framework/optimizer/extension.py` | file_reference |
| 16 | `FieldMeta` single-source-of-truth consolidation and mirror retirement | 8 | `CHANGELOG.md` (under `[Unreleased] → Changed`) | note |
| 16 | `FieldMeta` single-source-of-truth consolidation and mirror retirement | 9 | Originally tracked as `BACKLOG.md` item 35 ("`FieldMeta` single-source-of-truth  | note |
| 16 | `FieldMeta` single-source-of-truth consolidation and mirror retirement | 10 | The consolidation eliminates ~7 sites of duplicated relation-shape logic and rem | note |
| 16 | `FieldMeta` single-source-of-truth consolidation and mirror retirement | 11 | Internal refactor only; no `Meta` key changes, no public surface changes, no con | scope |
| 17 | Deferred scalar conversions | 0 | both upstreams ship scalar conversion for `BigIntegerField` / `JSONField` / `HSt | note |
| 17 | Deferred scalar conversions | 1 | `BigInt` scalar + strict parser/serializer, `JSONField` / `ArrayField` / `HStore | note |
| 17 | Deferred scalar conversions | 2 | Public `BigInt` scalar (`django_strawberry_framework/scalars.py`, `NewType`-base | note |
| 17 | Deferred scalar conversions | 3 | Strict `BigInt` parser via regex `^(0\|-?[1-9][0-9]*)$` — rejects `bool`, `float` | note |
| 17 | Deferred scalar conversions | 4 | Strict `BigInt` serializer — rejects `bool`, `float`, `str`, `Decimal`, and any  | note |
| 17 | Deferred scalar conversions | 5 | `BigIntegerField → BigInt` and `PositiveBigIntegerField → BigInt` in `SCALAR_MAP | note |
| 17 | Deferred scalar conversions | 6 | `JSONField → strawberry.scalars.JSON` in `SCALAR_MAP`. | note |
| 17 | Deferred scalar conversions | 7 | `ArrayField` and `HStoreField` mapped via sentinel-guarded branches in `convert_ | note |
| 17 | Deferred scalar conversions | 8 | `ArrayField` rejects nested arrays and outer `choices` with `ConfigurationError` | note |
| 17 | Deferred scalar conversions | 9 | `SCALAR_MAP`'s declared value type widened from `dict[type[models.Field], type]` | note |
| 17 | Deferred scalar conversions | 10 | `BigInt` added to `django_strawberry_framework.__all__`; `tests/base/test_init.p | note |
| 17 | Deferred scalar conversions | 11 | Atomic version-bump quintet: `pyproject.toml`, `__init__.py`, `tests/base/test_i | note |
| 17 | Deferred scalar conversions | 12 | 100% coverage via `tests/test_scalars.py` (new flat file) and `tests/types/test_ | test_plan |
| 17 | Deferred scalar conversions | 13 | Docs: `docs/GLOSSARY.md`, `docs/README.md`, `README.md`, `docs/TREE.md`, `TODAY. | note |
| 17 | Deferred scalar conversions | 14 | The internal Strawberry deprecation about passing a class (or `NewType`) to `str | note |
| 18 | Multiple DjangoTypes per model with `Meta.primary` | 0 | 🍓 parity-adjacent (strawberry-graphql-django has an implicit primary-type concep | note |
| 18 | Multiple DjangoTypes per model with `Meta.primary` | 1 | registry stores multiple types per model, `Meta.primary` flag, ambiguity audit a | note |
| 18 | Multiple DjangoTypes per model with `Meta.primary` | 2 | Registry stores multiple types per model (`_types: dict[Model, list[Type]]`). | note |
| 18 | Multiple DjangoTypes per model with `Meta.primary` | 3 | New `Meta.primary: bool` flag (default `False`); validated in `_validate_meta`. | note |
| 18 | Multiple DjangoTypes per model with `Meta.primary` | 4 | `registry.register(..., *, primary: bool = False) -> bool` and | note |
| 18 | Multiple DjangoTypes per model with `Meta.primary` | 5 | New registry surface: `primary_for(model)`, `types_for(model)`, | note |
| 18 | Multiple DjangoTypes per model with `Meta.primary` | 6 | `registry.get(model)` returns the primary if declared, else the single | note |
| 18 | Multiple DjangoTypes per model with `Meta.primary` | 7 | `finalize_django_types()` runs `audit_primary_ambiguity()` first: any | note |
| 18 | Multiple DjangoTypes per model with `Meta.primary` | 8 | Two primary types for the same model: rejected at registration time | decision |
| 18 | Multiple DjangoTypes per model with `Meta.primary` | 9 | Relation conversion in `types/base.py` defers all **auto-synthesized** | note |
| 18 | Multiple DjangoTypes per model with `Meta.primary` | 10 | Optimizer planning threads the resolved origin Strawberry type from | note |
| 18 | Multiple DjangoTypes per model with `Meta.primary` | 11 | Schema audit (`optimizer/extension.py`) iterates every reachable | note |
| 18 | Multiple DjangoTypes per model with `Meta.primary` | 12 | `model_for_type` continues to work for any registered type so | note |
| 18 | Multiple DjangoTypes per model with `Meta.primary` | 13 | `DjangoTypeDefinition` gains `primary: bool = False`. | note |
| 18 | Multiple DjangoTypes per model with `Meta.primary` | 14 | 100% coverage across `tests/test_registry.py`, `tests/types/test_base.py`, | test_plan |
| 18 | Multiple DjangoTypes per model with `Meta.primary` | 15 | Single-type-no-primary stays backward compatible: `registry.get(model)` | note |
| 18 | Multiple DjangoTypes per model with `Meta.primary` | 16 | `Meta.primary` is a per-class declaration, not a registry-level | note |
| 18 | Multiple DjangoTypes per model with `Meta.primary` | 17 | Already-shipped consumer relation overrides (direct annotation | note |
| 19 | Consumer override semantics (scalar fields) | 0 | both upstreams support consumer-authored scalar field overrides on model-backed  | scope |
| 19 | Consumer override semantics (scalar fields) | 1 | annotation/assigned scalar-override contract (four-corner matrix), `relay.Node`  | note |
| 19 | Consumer override semantics (scalar fields) | 2 | `DjangoType.__init_subclass__` collected `consumer_annotated_scalar_fields` | note |
| 19 | Consumer override semantics (scalar fields) | 3 | `DjangoTypeDefinition` gained `consumer_annotated_scalar_fields: frozenset[str]` | note |
| 19 | Consumer override semantics (scalar fields) | 4 | The previously-skipped `test_consumer_annotation_overrides_synthesized` | note |
| 19 | Consumer override semantics (scalar fields) | 5 | End-to-end test pinned the override surviving `strawberry.type(...)` | test_plan |
| 19 | Consumer override semantics (scalar fields) | 6 | **Consumer annotation overrides are authoritative.** `_build_annotations`'s | note |
| 19 | Consumer override semantics (scalar fields) | 7 | **`relay.Node` `id` collision rejected at type-creation time.** A consumer | decision |
| 19 | Consumer override semantics (scalar fields) | 8 | No new public API. No `Meta.field_overrides = {...}`-style key. Opt-out | note |
| 19 | Consumer override semantics (scalar fields) | 9 | 100% coverage was reached across `tests/types/test_definition_order.py` | test_plan |
| 19 | Consumer override semantics (scalar fields) | 10 | The four `consumer_*_fields` sets on `DjangoTypeDefinition` | note |
| 19 | Consumer override semantics (scalar fields) | 11 | Resolver / metadata overrides for scalars stay on the assigned | note |
| 19 | Consumer override semantics (scalar fields) | 12 | Type-annotation overrides are the consumer's responsibility for runtime | note |
| 20 | `DjangoListField` (non-Relay list) | 0 | graphene-django ships `DjangoListField`; strawberry-graphql-django has no non-Re | note |
| 20 | `DjangoListField` (non-Relay list) | 1 | `DjangoListField` factory: default + consumer resolver, `Manager → QuerySet` coe | note |
| 21 | `apps.py` and Django app config | 0 | both upstreams ship an `apps.py` `AppConfig` for `INSTALLED_APPS`-driven discove | note |
| 21 | `apps.py` and Django app config | 1 | tiny `AppConfig` (two class attributes, no `ready()` body in 0.0.7) + tests. | note |
| 22 | Schema export management command | 0 | strawberry-graphql-django ships `manage.py export_schema`; graphene-django's dif | note |
| 22 | Schema export management command | 1 | one management command (positional `schema`, `--path`, SDL via `print_schema`, ` | note |
| 23 | Multi-database cooperation contract | 0 | multi-DB is a Django capability neither upstream specifies a contract around (⚛️ | note |
| 23 | Multi-database cooperation contract | 1 | pin the multi-DB cooperation contract (router-aware FK-id stubs, `.using()` pres | note |
| 24 | Django Trac #37064 hardening + `safe_wrap_connection_method` | 0 | defensive hardening unique to this package; neither upstream ships a Django Trac | note |
| 24 | Django Trac #37064 hardening + `safe_wrap_connection_method` | 1 | two-half defense for Trac #37064: a package-level unwrap patch (auto-applied at  | note |
| 25 | Warning-free scalar registration via `StrawberryConfig.scalar_map` | 0 | package-specific scalar-registration plumbing (`StrawberryConfig.scalar_map` via | note |
| 25 | Warning-free scalar registration via `StrawberryConfig.scalar_map` | 1 | `strawberry_config()` factory registering `BigInt` via `scalar_map` and removing | note |
| 26 | Scalar conversion end-to-end coverage in the fakeshop example | 0 | both upstreams ship scalar conversion for the full numeric / date / JSON / UUID  | note |
| 26 | Scalar conversion end-to-end coverage in the fakeshop example | 1 | new `apps.scalars` example app (paired non-null / nullable models, self-FK + cro | note |
| 26 | Scalar conversion end-to-end coverage in the fakeshop example | 2 | `ScalarSpecimen` — every scalar field non-null, exposed via `ScalarSpecimenType` | note |
| 26 | Scalar conversion end-to-end coverage in the fakeshop example | 3 | `NullableScalarSpecimen` — every scalar field nullable (`null=True, blank=True`) | note |
| 26 | Scalar conversion end-to-end coverage in the fakeshop example | 4 | The pairing is deliberate (not a single model with paired fields). It exercises  | note |
| 26 | Scalar conversion end-to-end coverage in the fakeshop example | 5 | `apps.scalars.schema` composes two root resolvers (`all_scalar_specimens`, `all_ | note |
| 26 | Scalar conversion end-to-end coverage in the fakeshop example | 6 | Full non-null wire-format sweep covering every field on `ScalarSpecimen` | scope |
| 26 | Scalar conversion end-to-end coverage in the fakeshop example | 7 | Signed-negative `BigInt` round-trip | note |
| 26 | Scalar conversion end-to-end coverage in the fakeshop example | 8 | `BigInt`-at-zero edge case | note |
| 26 | Scalar conversion end-to-end coverage in the fakeshop example | 9 | Schema introspection asserting `BigInt` converter resolves correctly in both sha | note |
| 26 | Scalar conversion end-to-end coverage in the fakeshop example | 10 | All-NULL nullable wire format covering every nullable converter branch | scope |
| 26 | Scalar conversion end-to-end coverage in the fakeshop example | 11 | Cross-model `partner` FK linkage round-trip | note |
| 26 | Scalar conversion end-to-end coverage in the fakeshop example | 12 | Reverse-FK `nullablePartners` exposure | note |
| 26 | Scalar conversion end-to-end coverage in the fakeshop example | 13 | Self-FK `parent` / `children` traversal | note |
| 27 | Filtering subsystem | 0 | both upstreams ship a FilterSet / filter surface; `django-graphene-filters` is t | note |
| 27 | Filtering subsystem | 1 | the milestone anchor: six-layer lazy-resolution filtering pipeline, `FilterSet`  | note |
| 28 | Ordering subsystem | 0 | Shipped the ordering subsystem in `0.0.8`. [`OrderSet`][glossary-orderset], [`Re | note |
| 29 | `DjangoType` consumer-DX cleanup pass | 0 | three independent slices: Slice 1 `extensions=` factory-form sweep (XS, ~30 min, | note |
| 29 | `DjangoType` consumer-DX cleanup pass | 1 | **Slice 1**: defensive — both upstreams already use the factory-callable form in | note |
| 29 | `DjangoType` consumer-DX cleanup pass | 2 | **Slice 2**: differentiating — neither `graphene-django` nor `strawberry-graphql | note |
| 29 | `DjangoType` consumer-DX cleanup pass | 3 | **Slice 3**: ⚛️&🍓 required — `strawberry_django.field(required=True/False)` allo | note |
| 30 | `DjangoConnectionField` | 0 | Filtering and Ordering ship before this card lands, so `DjangoConnectionField` c | note |
| 30 | `DjangoConnectionField` | 1 | both upstreams ship Relay-shaped connection fields. | note |
| 30 | `DjangoConnectionField` | 2 | the central read-side primitive — the Relay surface and all Layer-3 arguments co | note |
| 30 | `DjangoConnectionField` | 3 | central Relay-shaped connection field plus cursor-pagination math; the integrati | note |
| 31 | Django-model-based GlobalID encoding | 0 | Original backlog score: Realistic 9/10, Impact 8/10, Difficulty 3/10; bang-for-b | note |
| 31 | Django-model-based GlobalID encoding | 1 | Legitimate legacy mode remains available: projects that intentionally scope iden | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 0 | eight-goal umbrella for the complete Relay surface (Root `node`/`nodes` fields,  | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 1 | ~~`Meta.interfaces` design~~ — `Meta.interfaces` accepted end-to-end for any Str | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 2 | ~~`GlobalID` mapping decision~~ — Strawberry-supplied `id: GlobalID!` from the R | decision |
| 32 | Full Relay story (Node + Connection + Root + validation) | 3 | ~~Default `resolve_*` injection~~ — `resolve_id_attr`, `resolve_id`, `resolve_no | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 4 | ~~`is_type_of` injection~~ — Unconditional on every `DjangoType`; consumer-decla | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 5 | ~~`CompositePrimaryKey` rejection~~ — Django 5.2+ composite-pk models raise `Con | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 6 | `node(id: GlobalID!): Node` — single-object refetch. Decodes the GlobalID, dispa | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 7 | `nodes(ids: [GlobalID!]!): [Node]!` — batch refetch. Decodes each GlobalID, disp | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 8 | **Implicit upgrade** (default): every `DjangoType` whose `Meta.interfaces` inclu | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 9 | **Explicit-only**: consumers who want only Connections (or only lists) on a rela | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 10 | **Cursor format**: opaque base64-encoded payload by default (`b64("offset:N")`). | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 11 | **Required arguments**: `first: Int`, `after: String`, `last: Int`, `before: Str | dependency |
| 32 | Full Relay story (Node + Connection + Root + validation) | 12 | **`pageInfo`**: emits the four standard fields (`hasNextPage`, `hasPreviousPage` | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 13 | **Edge cases**: `first: 0` returns empty edges + `pageInfo`. `first: N` with N > | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 14 | **`totalCount`**: an opt-in field on every Connection (`Meta.connection = {"tota | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 15 | `filter: <Type>FilterInput` — generated from `Meta.filterset_class` (composes wi | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 16 | `orderBy: [<Type>OrderInput!]` — generated from `Meta.orderset_class` (composes  | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 17 | `search: String` — generated from `Meta.search_fields` (composes with `{{card_re | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 18 | decode the GlobalID server-side (never trust the client's claim of which type th | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 19 | dispatch to the resolved type's `resolve_node` (which honors `cls.get_queryset(q | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 20 | return `null` for rows the user can't see (not an error — the Relay spec require | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 21 | never reveal *existence* of hidden rows through error timing or status codes | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 22 | `relay.GlobalID`, `relay.NodeID[...]`, `relay.Connection`, `relay.ListConnection | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 23 | Non-Strawberry-interface classes in `Meta.interfaces` → rejected at validation w | decision |
| 32 | Full Relay story (Node + Connection + Root + validation) | 24 | `Meta.connection = {...}` declared on a type that doesn't include `relay.Node` i | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 25 | A `DjangoNodeField()` query field on a schema with **no** `DjangoType`s declarin | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 26 | `node(id:)` and `nodes(ids:)` resolve real product / category / item / entry Glo | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 27 | Reverse-FK and M2M relations on those types expose their Connection counterparts | scope |
| 32 | Full Relay story (Node + Connection + Root + validation) | 28 | Live HTTP tests under `examples/fakeshop/test_query/` exercise the full Relay qu | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 29 | Type-rename GlobalID migrations (Django-migrations-style history that lets old-f | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 30 | Polymorphic connections (`Connection[Interface]` with auto-dispatched concrete t | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 31 | `Meta.cursor_field` for stable cursors keyed on a deterministic column | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 32 | Auto-upgrade reverse FK / M2M to Connection based on a row-count threshold | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 33 | Refetchable container schema metadata for `useRefetchableFragment` | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 34 | Permission-aware cursor decoding (cursor decode re-runs `get_queryset` so privil | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 35 | `{{card_ref:0}}` (`DjangoConnectionField`) — **hard dependency**; this card unbl | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 36 | `{{card_ref:1}}` (Filtering subsystem) — soft dependency for the filter argument | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 37 | `{{card_ref:2}}` (Ordering subsystem) — soft dependency for the orderBy argument | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 38 | `{{card_ref:7}}` (Connection-aware optimizer planning) — ships in parallel; the  | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 39 | `{{card_ref:8}}` (Permissions subsystem) — soft dependency; the Node entry point | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 51 | `django_strawberry_framework/connection.py` — main implementation (shipped as pa | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 52 | `django_strawberry_framework/relay.py` (new) — `DjangoNodeField`, `DjangoNodesFi | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 53 | `django_strawberry_framework/types/base.py` — `Meta.connection` / `Meta.relation | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 54 | `django_strawberry_framework/types/finalizer.py` — auto-upgrade reverse-FK / M2M | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 55 | `django_strawberry_framework/testing/relay.py` (new) — test helpers | test_plan |
| 32 | Full Relay story (Node + Connection + Root + validation) | 56 | `tests/test_relay_node_field.py`, `tests/test_relay_connection.py` (new) | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 57 | `examples/fakeshop/test_query/test_library_api.py` — Relay-shape HTTP tests | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 58 | `examples/fakeshop/apps/products/schema.py` — Relay surface activation (lit up a | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 59 | `docs/spec-032-full_relay-0_0_9.md` (new) | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 60 | `docs/GLOSSARY.md` — Relay surface description | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 61 | Relay node refetch from Apollo / Relay Compiler clients (the *"Relay just works" | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 62 | Fakeshop product-catalog Relay activation (Goal 8) | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 63 | Per-type `useFragment` / `useRefetchableFragment` patterns (mechanics; the schem | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 64 | Every BETTER item 39 sub-feature builds on this card's mechanics | note |
| 32 | Full Relay story (Node + Connection + Root + validation) | 65 | Fakeshop products-app activation (`examples/fakeshop/apps/products/schema.py`):  | note |
| 33 | Connection-aware optimizer planning | 0 | gated on `{{card_ref:0}}` / Relay decisions. | dependency |
| 33 | Connection-aware optimizer planning | 1 | strawberry-graphql-django plans connection selections natively; graphene-django  | note |
| 33 | Connection-aware optimizer planning | 2 | bounded optimizer extension: teach the selection-walker to recognize Relay `edge | note |
| 33 | Connection-aware optimizer planning | 3 | The optimizer's plan cache, `select_related` / `prefetch_related` planning, FK-i | note |
| 33 | Connection-aware optimizer planning | 4 | Relay-style nested connection selections (`{ allObjects { edges { node { values  | note |
| 33 | Connection-aware optimizer planning | 5 | The cookbook reference `AdvancedDjangoFilterConnectionField` does its own argume | note |
| 33 | Connection-aware optimizer planning | 6 | Selection-tree walker awareness of Relay `edges { node { ... } }` pattern. | note |
| 33 | Connection-aware optimizer planning | 7 | Connection-pagination-aware queryset planning (`Prefetch` downgrade for `connect | note |
| 33 | Connection-aware optimizer planning | 8 | Plan-cache key hygiene for paginated selections (skip pagination args that do no | note |
| 33 | Connection-aware optimizer planning | 9 | Strictness-mode interaction with connection paths so unplanned nested connection | note |
| 33 | Connection-aware optimizer planning | 10 | Unblocked the fakeshop products connections-only conversion (the fakeshop-activa | note |
| 34 | Permissions subsystem | 0 | for the fakeshop example and real usage. | note |
| 34 | Permissions subsystem | 1 | django-graphene-filters ships rich cascade + per-field permissions; strawberry-g | note |
| 34 | Permissions subsystem | 2 | permissions/visibility is security-relevant and blocks the fakeshop real-usage s | note |
| 34 | Permissions subsystem | 3 | full subsystem: `apply_cascade_permissions`, per-field `Meta` permission hooks,  | note |
| 34 | Permissions subsystem | 4 | Open question — hidden-FK semantics: when a parent row references a hidden targe | open_question |
| 34 | Permissions subsystem | 5 | Open question — cascade performance: subquery-per-FK (one extra round-trip per F | open_question |
| 34 | Permissions subsystem | 6 | Open question — M2M / reverse-relation visibility: the upstream cascade explicit | open_question |
| 34 | Permissions subsystem | 7 | Open question — `check_permissions` API surface: does the existing per-field fil | open_question |
| 35 | Optimizer robustness hardening (upstream-comparison guards) | 0 | Deferred audit finding (owned elsewhere): windowed nested-prefetch pagination (` | note |
| 35 | Optimizer robustness hardening (upstream-comparison guards) | 1 | Deferred audit finding (not scheduled): annotation hints - upstream supports `fi | note |
| 35 | Optimizer robustness hardening (upstream-comparison guards) | 2 | Deferred audit finding (deliberate non-adoption, record as a spec non-goal): pre | note |
| 35 | Optimizer robustness hardening (upstream-comparison guards) | 3 | Deferred audit findings (out of scope, record as spec non-goals): GenericForeign | note |
| 35 | Optimizer robustness hardening (upstream-comparison guards) | 4 | Audit method note: both inventories were produced from source on 2026-06-11 (36  | note |
| 36 | Mutations + auto-generated Input types | 0 | mutations are the single largest unscoped gap vs strawberry-graphql-django (crea | note |
| 36 | Mutations + auto-generated Input types | 1 | no on-board predecessor. | note |
| 36 | Mutations + auto-generated Input types | 2 | `{{card_ref:6}}`-scale. The single largest unscoped gap versus strawberry-graphq | note |
| 37 | Upload scalar and file / image field mapping | 0 | strawberry-graphql-django maps `FileField` / `ImageField` to `Upload` (input) an | note |
| 37 | Upload scalar and file / image field mapping | 1 | pairs with `{{card_ref:0}}` for the write side. | note |
| 37 | Upload scalar and file / image field mapping | 2 | bounded converter-table addition: `FileField` / `ImageField` → file/image output | note |
| 38 | Form-based mutations (Django Forms / ModelForms) | 0 | graphene-django ships `DjangoFormMutation` / `DjangoModelFormMutation`. | note |
| 38 | Form-based mutations (Django Forms / ModelForms) | 1 | no on-board predecessor. | note |
| 38 | Form-based mutations (Django Forms / ModelForms) | 2 | new `forms/` subpackage (form-field converter + `Form`/`ModelForm` mutation clas | note |
| 39 | DRF serializer mutations (`SerializerMutation`) | 0 | graphene-django ships `SerializerMutation`; the highest-leverage write-side feat | note |
| 39 | DRF serializer mutations (`SerializerMutation`) | 1 | no on-board predecessor. | note |
| 39 | DRF serializer mutations (`SerializerMutation`) | 2 | new `rest_framework/` subpackage (serializer converter dual-purposed for inputs  | note |
| 40 | Auth mutations (login / logout / register) | 0 | strawberry-graphql-django ships a small auth-mutations module. | note |
| 40 | Auth mutations (login / logout / register) | 1 | depends on `{{card_ref:0}}`. | note |
| 40 | Auth mutations (login / logout / register) | 2 | new `auth/` module (`login` / `logout` / `register` + `current_user` query helpe | note |
| 41 | Channels ASGI router (migration aid) | 0 | small slice; explicit migration aid. | note |
| 41 | Channels ASGI router (migration aid) | 1 | strawberry-graphql-django ships a Channels `ProtocolTypeRouter` helper; graphene | note |
| 41 | Channels ASGI router (migration aid) | 2 | small `routers.py` (~30 lines) with a soft `channels` dependency; tests for both | note |
| 42 | Debug-toolbar middleware | 0 | developer experience. | note |
| 42 | Debug-toolbar middleware | 1 | strawberry-graphql-django ships a debug-toolbar middleware; graphene-django ship | note |
| 42 | Debug-toolbar middleware | 2 | subclass django-debug-toolbar's middleware with two injection paths (GraphiQL HT | note |
| 43 | Test client helper | 0 | developer experience. | note |
| 43 | Test client helper | 1 | both upstreams ship a GraphQL test client / mixin. | test_plan |
| 43 | Test client helper | 2 | `test/client.py` (sync + async `TestClient`, a `GraphQLTestMixin`, two `(Mixin,  | test_plan |
| 44 | Response-extensions debug middleware | 0 | developer experience. | note |
| 44 | Response-extensions debug middleware | 1 | graphene-django ships an in-response `DjangoDebug` SQL/exception subsystem; stra | note |
| 44 | Response-extensions debug middleware | 2 | distinct from `{{card_ref:0}}` (Django debug toolbar). | note |
| 44 | Response-extensions debug middleware | 3 | a Strawberry `SchemaExtension` that captures SQL + exceptions into `extensions[' | note |
| 47 | Beta release (cleanup, verification, alpha → beta) | 0 | release card. | note |
| 47 | Beta release (cleanup, verification, alpha → beta) | 1 | release / verification card — gates the alpha → beta cut; not an upstream-parity | note |
| 47 | Beta release (cleanup, verification, alpha → beta) | 2 | release-blocking. | note |
| 47 | Beta release (cleanup, verification, alpha → beta) | 3 | final card in the Alpha queue; gates the alpha → beta milestone. | note |
| 47 | Beta release (cleanup, verification, alpha → beta) | 4 | release / verification card, no new subsystem: full `(Python, Django, Strawberry | note |
| 48 | `FieldSet` | 0 | the smallest Layer-3 subsystem: `fieldset.py` + `docs/spec-fieldset.md` + tests; | note |
| 49 | `Meta.search_fields` support | 0 | a single `search: String` argument fanning out as an OR'd `icontains` across dec | note |
| 49 | `Meta.search_fields` support | 1 | `django-graphene-filters` exposes `Meta.search_fields = ("name", "description",  | note |
| 50 | Postgres full-text search filter primitives | 0 | Postgres-only filter family (`SearchQuery` / `SearchRank` / `Trigram`) layered o | note |
| 50 | Postgres full-text search filter primitives | 1 | The only cookbook filter-surface gap found in the 0.0.7 DRY-cycle kwarg-parity a | note |
| 51 | Aggregation subsystem | 0 | full subsystem, parallel to Ordering: reuses `{{card_ref:0}}`'s six-layer archit | note |
| 52 | Layer 3 Meta key promotion | 0 | each Layer 3 subsystem implementation | note |
| 52 | Layer 3 Meta key promotion | 1 | `filterset_class` | note |
| 52 | Layer 3 Meta key promotion | 2 | `orderset_class` | note |
| 52 | Layer 3 Meta key promotion | 3 | `aggregate_class` | note |
| 52 | Layer 3 Meta key promotion | 4 | `fields_class` | note |
| 52 | Layer 3 Meta key promotion | 5 | `search_fields` | note |
| 52 | Layer 3 Meta key promotion | 6 | Do not move a key from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS` until the pip | note |
| 52 | Layer 3 Meta key promotion | 7 | mechanical bookkeeping: move keys from `DEFERRED_META_KEYS` → `ALLOWED_META_KEYS | note |
| 54 | Stable choice enum naming override | 0 | bounded override surface (`Meta.choice_enum_names`) preserving `(model, field)`  | note |
| 54 | Stable choice enum naming override | 1 | Choice fields generate Strawberry enums and cache them by `(model, field_name)`. | note |
| 54 | Stable choice enum naming override | 2 | The first `DjangoType` to read a choice column wins the generated enum's GraphQL | note |
| 54 | Stable choice enum naming override | 3 | This is deterministic for a fixed import order but still makes schema naming dep | note |
| 54 | Stable choice enum naming override | 4 | Add a stable override surface such as `Meta.choice_enum_names = {"status": "Item | scope |
| 54 | Stable choice enum naming override | 5 | Decide whether this belongs in the consumer-overrides spec or a small choice-enu | note |
| 54 | Stable choice enum naming override | 6 | Preserve enum reuse by `(model, field_name)` while making the published schema n | note |
| 55 | Fakeshop GraphQL schema activation | 0 | example-wiring card: uncomment the product-catalog schema portions whose depende | note |
| 55 | Fakeshop GraphQL schema activation | 1 | `examples/fakeshop/apps/products/schema.py` exposes a placeholder `hello` field  | note |
| 55 | Fakeshop GraphQL schema activation | 2 | The aspirational schema block depends on `DjangoConnectionField`, Relay interfac | note |
| 56 | Product-catalog Layer 3 HTTP GraphQL tests | 0 | activating the product-catalog fakeshop GraphQL schema | note |
| 56 | Product-catalog Layer 3 HTTP GraphQL tests | 1 | connection/query fields and other Layer 3 public surfaces | note |
| 56 | Product-catalog Layer 3 HTTP GraphQL tests | 2 | The library app already has live `/graphql/` acceptance tests under `examples/fa | definition_of_done |
| 56 | Product-catalog Layer 3 HTTP GraphQL tests | 3 | Future product-catalog HTTP tests should use the same placement and schema-reloa | note |
| 56 | Product-catalog Layer 3 HTTP GraphQL tests | 4 | In-process `schema.execute_sync` tests still go under `examples/fakeshop/tests/` | note |
| 56 | Product-catalog Layer 3 HTTP GraphQL tests | 5 | bounded test suite: live `/graphql/` acceptance tests for the activated product- | test_plan |
| 57 | Mutation transactions and idempotency | 0 | Original backlog score: Realistic 10/10, Impact 8/10, Difficulty 3/10; bang-for- | note |
| 57 | Mutation transactions and idempotency | 1 | Neither graphene-django nor strawberry-graphql-django ships mutation idempotency | note |
| 58 | Migration and adoption guides | 0 | docs-only but substantial: two full migration guides (graphene-django → and stra | note |
| 58 | Migration and adoption guides | 1 | The package is intentionally shaped for teams coming from `django-filter`, DRF,  | note |
| 58 | Migration and adoption guides | 2 | The feature docs explain the positioning, but there are no dedicated migration g | note |
| 58 | Migration and adoption guides | 3 | Add ability to set dsf settings to cap the number of schema hookups per model an | scope |
| 58 | Migration and adoption guides | 4 | Add a `graphene-django` migration guide covering `DjangoObjectType` to `DjangoTy | scope |
| 58 | Migration and adoption guides | 5 | Add a `strawberry-graphql-django` migration guide covering decorator-to-`Meta` t | scope |
| 58 | Migration and adoption guides | 6 | Add concise notes for DRF / django-filter users mapping serializers/filtersets/o | scope |
| 59 | Adversarial non-live test suite (try to break it, not just cover lines) | 0 | An in-process `tests/` (NON-`/graphql/`) hardening pass whose goal is to BREAK t | note |
| 59 | Adversarial non-live test suite (try to break it, not just cover lines) | 1 | Root `tests/` historically mixed genuinely-unreachable-from-live cases with some | note |
| 59 | Adversarial non-live test suite (try to break it, not just cover lines) | 2 | There is no deliberate "try to break it" suite; adversarial inputs are covered o | note |
| 59 | Adversarial non-live test suite (try to break it, not just cover lines) | 3 | Property-based / fuzz-style tests (e.g. Hypothesis) for the filter input normali | note |
| 59 | Adversarial non-live test suite (try to break it, not just cover lines) | 4 | Pathological structure: logic-tree nesting past `_MAX_LOGIC_DEPTH`, cyclic / sel | note |
| 59 | Adversarial non-live test suite (try to break it, not just cover lines) | 5 | Hostile wire values: bad-base64 / wrong-`type_name` GlobalIDs, oversized `in` li | scope |
| 59 | Adversarial non-live test suite (try to break it, not just cover lines) | 6 | Scale / resource: very large `"__all__"` field sets and many-relation BFS; asser | note |
| 59 | Adversarial non-live test suite (try to break it, not just cover lines) | 7 | Extend the same philosophy to the future order / aggregate / fieldset subsystems | note |
| 60 | Optimizer explain mode | 0 | Original backlog score: Realistic 10/10, Impact 8/10, Difficulty 2/10; bang-for- | note |
| 62 | Stable release (API freeze, cleanup, verification, beta → stable) | 0 | the heaviest release card: API freeze + `__all__` audit, a security review of ev | note |
| 63 | Investigate SQLAlchemy 2.0 compiler architecture | 0 | Research only; no implementation commitment unless this is promoted out of backl | note |

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
