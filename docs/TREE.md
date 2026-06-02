# Reference Trees

This file is the detailed layout reference. It exists to preserve the package/test tree rationale, upstream layout comparisons, and per-file responsibilities without turning [`../README.md`][readme] into a second architecture document.

For install, local development, testing, and the canonical documentation map, start from [`../README.md`][readme].

The upstream trees are captured for reference while shaping `django-strawberry-framework`'s own subpackage layout. Filters applied: `__pycache__/` directories, package-internal `tests/` directories, `conftest.py`, and `*.pyc` files are excluded so both trees show only the library logic surface (the strawberry-django source checkout already keeps tests outside the package directory; graphene-django ships its tests inside the installed package, so they're filtered here for comparability).

## graphene_django

Source: `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django`

```text
graphene_django/
├── debug/
│   ├── exception/
│   │   ├── __init__.py
│   │   ├── formating.py
│   │   └── types.py
│   ├── sql/
│   │   ├── __init__.py
│   │   ├── tracking.py
│   │   └── types.py
│   ├── __init__.py
│   ├── middleware.py
│   └── types.py
├── filter/
│   ├── filters/
│   │   ├── __init__.py
│   │   ├── array_filter.py
│   │   ├── global_id_filter.py
│   │   ├── list_filter.py
│   │   ├── range_filter.py
│   │   └── typed_filter.py
│   ├── __init__.py
│   ├── fields.py
│   ├── filterset.py
│   └── utils.py
├── forms/
│   ├── __init__.py
│   ├── converter.py
│   ├── forms.py
│   ├── mutation.py
│   └── types.py
├── management/
│   ├── commands/
│   │   ├── __init__.py
│   │   └── graphql_schema.py
│   └── __init__.py
├── rest_framework/
│   ├── __init__.py
│   ├── models.py
│   ├── mutation.py
│   ├── serializer_converter.py
│   └── types.py
├── static/
│   └── graphene_django/
│       └── graphiql.js
├── templates/
│   └── graphene/
│       └── graphiql.html
├── utils/
│   ├── __init__.py
│   ├── str_converters.py
│   ├── testing.py
│   └── utils.py
├── __init__.py
├── compat.py
├── constants.py
├── converter.py
├── fields.py
├── registry.py
├── settings.py
├── types.py
└── views.py
```

## strawberry_django

Source: `/Users/riordenweber/projects/strawberry-django-main/strawberry_django`

```text
strawberry_django/
├── auth/
│   ├── __init__.py
│   ├── mutations.py
│   ├── queries.py
│   └── utils.py
├── extensions/
│   ├── __init__.py
│   ├── django_cache_base.py
│   └── django_validation_cache.py
├── federation/
│   ├── __init__.py
│   ├── field.py
│   ├── resolve.py
│   └── type.py
├── fields/
│   ├── __init__.py
│   ├── base.py
│   ├── field.py
│   ├── filter_order.py
│   ├── filter_types.py
│   └── types.py
├── integrations/
│   ├── __init__.py
│   └── guardian.py
├── management/
│   ├── commands/
│   │   ├── __init__.py
│   │   └── export_schema.py
│   └── __init__.py
├── middlewares/
│   ├── __init__.py
│   └── debug_toolbar.py
├── mutations/
│   ├── __init__.py
│   ├── fields.py
│   ├── mutations.py
│   ├── resolvers.py
│   └── types.py
├── relay/
│   ├── __init__.py
│   ├── cursor_connection.py
│   ├── list_connection.py
│   └── utils.py
├── templates/
│   └── strawberry_django/
│       └── debug_toolbar.html
├── test/
│   ├── __init__.py
│   └── client.py
├── utils/
│   ├── __init__.py
│   ├── gql_compat.py
│   ├── inspect.py
│   ├── patches.py
│   ├── pyutils.py
│   ├── query.py
│   ├── requests.py
│   └── typing.py
├── __init__.py
├── apps.py
├── arguments.py
├── descriptors.py
├── exceptions.py
├── filters.py
├── optimizer.py
├── ordering.py
├── pagination.py
├── permissions.py
├── py.typed
├── queryset.py
├── resolvers.py
├── routers.py
├── settings.py
└── type.py
```

## django_graphene_filters

Source: `/Users/riordenweber/projects/django-graphene-filters/django_graphene_filters`

```text
django_graphene_filters/
├── __init__.py
├── aggregate_arguments_factory.py
├── aggregate_types.py
├── aggregateset.py
├── conf.py
├── connection_field.py
├── fieldset.py
├── filter_arguments_factory.py
├── filters.py
├── filterset.py
├── filterset_factories.py
├── input_data_factories.py
├── input_types.py
├── mixins.py
├── object_type.py
├── order_arguments_factory.py
├── orders.py
├── orderset.py
├── permissions.py
└── utils.py
```

## django_strawberry_framework (current on-disk layout)

The shared infrastructure plus model/type, optimizer, filters, testing, and utility subpackages are on disk: `types/`, `optimizer/`, `filters/`, `testing/`, and `utils/`. Every other module shown in the target package layout below — the remaining query-surface subpackages, the mutation cluster, the auth / forms / DRF integrations, the full test client, and the Channels router — is not on disk yet and will land as the corresponding `KANBAN.md` cards ship.
The fakeshop example project uses the standard explicit-package layout under `examples/fakeshop/`: orchestration lives in `config/` (`settings.py`, `schema.py`, `urls.py`, `wsgi.py`), and domain apps live in `apps/` (`apps.products`, `apps.library`, `apps.scalars`). `apps.products` is the catalog example (Category / Item / Property / Entry); `apps.library` is the deeper relation example (Branch / Shelf / Book / Patron / Loan, with `Patron.lifetime_fines_cents` as a real-domain `BigIntegerField → BigInt` proof); `apps.scalars` is a test substrate carrying the paired `ScalarSpecimen` (every scalar non-null + self-FK) / `NullableScalarSpecimen` (every scalar nullable + cross-model FK to `ScalarSpecimen` with `on_delete=SET_NULL`) layout that pins every non-trivial converter row in both shapes via live `/graphql/` tests. `pytest.ini` adds the example project root (`examples/fakeshop`) to `pythonpath` so `config` and `apps` resolve as normal packages; it does not add `examples/fakeshop/apps`, so app imports must use dotted paths such as `apps.products.models`. The project root itself is intentionally not a Python package.

```text
django_strawberry_framework/
├── __init__.py              # public-API re-exports (DjangoType, DjangoOptimizerExtension, OptimizerHint, BigInt, finalize_django_types, auto)
├── py.typed
├── apps.py                  # AppConfig
├── conf.py                  # settings reader (DJANGO_STRAWBERRY_FRAMEWORK)
├── exceptions.py            # error hierarchy
├── registry.py              # model→type registry (Meta.primary shipped in 0.0.6: primary_for, types_for, models_with_multiple_types; unregister test-fixture helper)
├── scalars.py               # BigInt public scalar (NewType-based; Strawberry deprecation suppressed at definition site)
├── list_field.py            # DjangoListField (non-Relay list[T] factory for root Query fields; shipped in 0.0.7)
├── management/              # Django management commands (shipped in 0.0.7)
│   ├── __init__.py
│   └── commands/
│       ├── __init__.py
│       └── export_schema.py  # `manage.py export_schema` — print/write GraphQL SDL
├── testing/                 # consumer testing utilities
│   ├── __init__.py          # safe_wrap_connection_method re-export
│   └── _wrap.py             # cooperative connection-method wrapping for Trac #37064
├── types/                   # DjangoType subsystem (Layer 2) — shipped
│   ├── __init__.py
│   ├── base.py              # DjangoType, _validate_meta, _build_annotations
│   ├── converters.py        # convert_scalar, convert_choices_to_enum, convert_relation
│   ├── definition.py        # DjangoTypeDefinition (canonical per-type metadata with Meta.primary flag and forward-reserved Layer-3 slots)
│   ├── finalizer.py         # finalize_django_types(): _audit_primary_ambiguity + Phase 1 unresolved-target detection + Phase 2 resolver attachment + Phase 2.5 interfaces/Relay + Phase 3 strawberry.type decoration
│   ├── relations.py         # PendingRelationAnnotation sentinel + metaclass
│   ├── relay.py             # Relay Node interface wiring (resolve_* defaults, id suppression, is_type_of injection)
│   └── resolvers.py         # _make_relation_resolver, _attach_relation_resolvers, B3 N+1 detection
├── optimizer/               # N+1 optimizer subsystem (Layer 2) — O1–O6 + B1–B8 shipped
│   ├── __init__.py          # re-exports DjangoOptimizerExtension
│   ├── _context.py          # context-key constants and get_context_value helper
│   ├── extension.py         # DjangoOptimizerExtension (O3 hook, B1 cache w/ H2 origin-typed key, B2 elision stash, B3 strictness, B5 context stash, B6 schema audit w/ H3 multi-type dedupe)
│   ├── walker.py            # selection-tree walker (O2, O5 only fields, B2 FK-id elision, B4 hints, B7 cached field map, H2 source_type origin routing)
│   ├── plans.py             # OptimizationPlan data structure + resolver_key / runtime_path helpers
│   ├── hints.py             # OptimizerHint typed wrapper (B4)
│   └── field_meta.py        # FieldMeta precomputed field metadata (B7)
├── filters/                 # Filtering subsystem (Layer 3 read-side) — shipped 0.0.8
│   ├── __init__.py          # FilterSet, RelatedFilter, filter_input_type re-exports
│   ├── base.py              # Filter / TypedFilter / ArrayFilter / RangeFilter / ListFilter / GlobalIDFilter / GlobalIDMultipleChoiceFilter / RelatedFilter / LazyRelatedClassMixin
│   ├── sets.py              # FilterSet + FilterSetMetaclass + apply_sync / apply_async + filter_queryset tree-form override
│   ├── factories.py         # FilterArgumentsFactory BFS + _dynamic_filterset_cache
│   └── inputs.py            # input-class module-globals namespace + LOOKUP_NAME_MAP / LOOKUP_PREFIXES / convert_filter_to_input_annotation / normalize_input_value / construct_search
└── utils/                   # cross-cutting helpers
    ├── __init__.py
    ├── relations.py         # relation_kind / RelationKind / is_many_side_relation_kind
    ├── strings.py           # snake_case / camelCase / PascalCase conversion
    └── typing.py            # unwrap_return_type (one layer), unwrap_graphql_type (full peel)
```

## django_strawberry_framework (target package layout)

This package target layout is separate from the fakeshop example-project layout above. It adds query-surface modules on top of the current `django_strawberry_framework/` package. It is derived from the three reference trees above and the package direction captured in [`GLOSSARY.md`][glossary].

Modules are tagged with `[alpha]`, `[beta]`, or `[stable]` to indicate which development phase they land in (matching the `MILESTONE` convention in [`../KANBAN.md`][kanban]). `[alpha]` modules land before `0.1.0` and `[beta]` modules land before `1.0.0` — both are tracked in [`../KANBAN.md`][kanban]. `[stable]` modules are post-`1.0.0` and tracked in [`../BACKLOG.md`][backlog]; they appear here only so the tree is comprehensive, not because they are committed.

```text
django_strawberry_framework/
├── __init__.py              # public-API re-exports
├── py.typed
├── apps.py                  # Django AppConfig
├── conf.py                  # settings reader (DJANGO_STRAWBERRY_FRAMEWORK)
├── exceptions.py            # error hierarchy
├── registry.py              # model→type registry (Meta.primary shipped in 0.0.6)
├── scalars.py               # BigInt public scalar (NewType-based; Strawberry deprecation suppressed at definition site)
├── fieldset.py              # [beta] FieldSet (declarative field selection)
├── list_field.py            # [alpha] DjangoListField (non-Relay list[T])
├── permissions.py           # [alpha] apply_cascade_permissions, per-field permission hooks
├── connection.py            # [alpha] DjangoConnectionField (Relay)
├── routers.py               # [alpha] DjangoGraphQLProtocolRouter (Channels; soft dep)
├── types/                   # DjangoType subsystem (Layer 2)
│   ├── __init__.py
│   ├── base.py              # DjangoType, _validate_meta, _build_annotations
│   ├── converters.py        # convert_scalar, convert_choices_to_enum, convert_relation
│   ├── definition.py        # DjangoTypeDefinition (canonical per-type metadata)
│   ├── finalizer.py         # finalize_django_types() three-phase finalizer
│   ├── relations.py         # PendingRelationAnnotation sentinel + metaclass
│   ├── relay.py             # Relay Node interface wiring
│   └── resolvers.py         # _make_relation_resolver, _attach_relation_resolvers
├── optimizer/               # N+1 optimizer subsystem (Layer 2)
│   ├── __init__.py
│   ├── _context.py          # context-key constants and get_context_value helper
│   ├── extension.py         # DjangoOptimizerExtension (Strawberry SchemaExtension)
│   ├── walker.py            # selection-tree walker (plan_optimizations)
│   ├── plans.py             # OptimizationPlan, Prefetch chain helpers
│   ├── hints.py             # OptimizerHint typed wrapper
│   └── field_meta.py        # FieldMeta precomputed field metadata
├── orders/                  # [alpha] Ordering subsystem (Layer 3 read-side)
│   ├── __init__.py
│   ├── base.py              # Order classes
│   ├── sets.py              # OrderSet
│   ├── factories.py         # GraphQL-arguments factory
│   └── inputs.py            # TODO(spec-028-orders-0_0_8 Slice 5): flip orders/ to current on-disk layout with mirrored tests/orders tree; do not touch package version fields unless explicitly commanded
├── aggregates/              # [beta] Aggregation subsystem (Layer 3)
│   ├── __init__.py
│   ├── base.py              # Sum/Count/Avg/Min/Max/GroupBy result types
│   ├── sets.py              # AggregateSet
│   └── factories.py         # GraphQL-arguments factory
├── mutations/               # [alpha] Mutations subsystem (Layer 3 write-side)
│   ├── __init__.py
│   ├── base.py              # DjangoMutation base + Meta.input_class / Meta.partial_input_class
│   ├── fields.py            # DjangoMutationField
│   ├── resolvers.py         # sync + async write resolvers
│   ├── types.py             # auto-generated Input / PartialInput type factories
│   └── errors.py            # shared `errors: list[FieldError]` envelope
├── forms/                   # [alpha] Form-based mutations (Django Forms / ModelForms)
│   ├── __init__.py
│   ├── mutation.py          # DjangoFormMutation, DjangoModelFormMutation (DRF-style Meta)
│   └── converter.py         # Django form field → Strawberry input type
├── rest_framework/          # [alpha] DRF serializer-driven mutations (soft dep on rest_framework)
│   ├── __init__.py
│   ├── mutation.py          # SerializerMutation (DRF-style Meta)
│   └── serializer_converter.py  # DRF field → Strawberry input/output type
├── auth/                    # [alpha] Auth mutations (opt-in import)
│   ├── __init__.py
│   ├── mutations.py         # login_mutation, logout_mutation, register_mutation
│   └── queries.py           # current_user query helper
├── extensions/              # [alpha] Strawberry SchemaExtension implementations
│   ├── __init__.py
│   └── debug.py             # response-extensions debug (SQL + exceptions in `extensions`)
├── middleware/              # [alpha] Django middleware
│   ├── __init__.py
│   └── debug_toolbar.py     # django-debug-toolbar SQL-panel capture during /graphql/
├── testing/                 # [alpha] Testing utilities for consumers
│   ├── __init__.py
│   └── client.py            # TestClient, AsyncTestClient, GraphQLTestCase
├── management/              # Django management commands
│   ├── __init__.py
│   └── commands/
│       ├── __init__.py
│       └── export_schema.py # GraphQL schema SDL export (`manage.py export_schema`)
└── utils/                   # cross-cutting helpers
    ├── __init__.py
    ├── relations.py         # relation_kind / RelationKind / is_many_side_relation_kind
    ├── strings.py           # snake_case / camelCase / PascalCase conversion
    ├── typing.py            # unwrap_return_type, unwrap_graphql_type
    └── queryset.py          # [stable] queryset introspection, prefetch-cache awareness
```

## Test layout going forward

Tests live across three roots, each with a focused responsibility. The root `tests/` tree mirrors the package source one-to-one and grows alongside the package; the two `examples/fakeshop/` test trees hold tests whose system-under-test is the example project, split by whether they exercise the GraphQL HTTP endpoint. The placement rules themselves are pinned in [`AGENTS.md`][agents] "Test placement"; this section is the visual map of the trees and a per-folder reference for what kind of test goes where.

**Coverage priority.** Any package coverage line in `django_strawberry_framework/` that can be earned by a real-world GraphQL query against fakeshop MUST be earned in `examples/fakeshop/test_query/` (live `/graphql/` HTTP via `django.test.Client`). Fall back to `examples/fakeshop/tests/` (in-process schema execution, services, admin, management commands, URLs) or the package-internal `tests/` tree only when the code path is genuinely unreachable from a live query. Mock only when the real path is impossible. The package coverage gate (`fail_under = 100`) is reached *because* the live HTTP tests exercise the package end-to-end — that is the point of the example project's existence in the test suite.

### Current shape (on disk today)

```text
tests/                       # Package-internal tests (current state)
├── __init__.py
├── management/             # mirrors django_strawberry_framework/management/
│   ├── __init__.py
│   └── test_export_schema.py  # ← export_schema Command — happy paths + failure modes
├── test_apps.py             # AppConfig (single-file Layer-3 module)
├── test_list_field.py       # DjangoListField (single-file Layer-3 module)
├── test_registry.py         # model→type registry
├── testing/                 # mirrors django_strawberry_framework/testing/
│   ├── __init__.py
│   └── test_wrap.py         # ← safe_wrap_connection_method consumer helper
├── base/                    # FROZEN: only conf and version checks
│   ├── __init__.py
│   ├── test_conf.py
│   └── test_init.py
├── types/                   # mirrors django_strawberry_framework/types/
│   ├── __init__.py
│   ├── test_base.py         # ← DjangoType + Meta validation + scalar/relation synthesis
│   ├── test_converters.py   # ← convert_scalar / convert_relation / convert_choices_to_enum
│   ├── test_definition_order.py        # ← consumer override contract (four-corner matrix) + definition-order-independent relation finalization
│   ├── test_definition_order_schema.py # ← schema-build / strawberry.type decoration interactions
│   ├── test_generic_foreign_key.py     # ← GenericForeignKey rejection contract
│   ├── test_relay_interfaces.py        # ← Meta.interfaces + Relay Node wiring
│   └── test_resolvers.py    # ← O1 _make_relation_resolver / _attach_relation_resolvers
├── optimizer/               # mirrors django_strawberry_framework/optimizer/
│   ├── __init__.py
│   ├── test_definition_order.py     # ← optimizer behavior under definition-order-independent relations
│   ├── test_extension.py    # ← DjangoOptimizerExtension (root-gated resolve hook, O3)
│   ├── test_field_meta.py   # ← FieldMeta precomputed field metadata
│   ├── test_hints.py        # ← OptimizerHint typed wrapper
│   ├── test_plans.py        # ← OptimizationPlan data structure
│   ├── test_relay_id_projection.py  # ← Relay GlobalID projection / connector-column behavior
│   └── test_walker.py       # ← O2 selection-tree walker
├── filters/                 # mirrors django_strawberry_framework/filters/
│   ├── __init__.py
│   ├── test_base.py         # ← Filter primitives + ArrayFilter / RangeFilter / ListFilter / GlobalIDFilter / RelatedFilter / LazyRelatedClassMixin
│   ├── test_sets.py         # ← FilterSet + FilterSetMetaclass + apply_sync / apply_async + filter_queryset tree-form override
│   ├── test_factories.py    # ← FilterArgumentsFactory BFS + _dynamic_filterset_cache
│   ├── test_inputs.py       # ← input-class module-globals namespace + LOOKUP_NAME_MAP / convert_filter_to_input_annotation / normalize_input_value
│   └── test_finalizer.py    # ← finalizer phase 2.5 binding + owner-aware materialization + filter_input_type orphan validation
└── utils/                   # mirrors django_strawberry_framework/utils/
    ├── __init__.py
    ├── test_relations.py    # ← relation_kind / is_many_side_relation_kind
    ├── test_strings.py      # ← snake_case / camelCase / PascalCase conversion
    └── test_typing.py       # ← unwrap_return_type / unwrap_graphql_type

examples/fakeshop/tests/     # Example-project tests, NO /graphql HTTP
├── test_admin.py            # admin actions via django.test.Client on /admin/...
├── test_commands.py         # management commands via call_command
├── test_models.py           # __str__ etc. on fakeshop models
├── test_schema.py           # in-process schema execution via schema.execute_sync
├── test_services.py         # Faker-driven seed_data / delete_data / create_users
└── test_urls.py             # fakeshop project urls (index view)

examples/fakeshop/test_query/   # Example-project tests, LIVE /graphql HTTP
├── README.md                # HTTP-test placement notes
├── test_library_api.py      # live GraphQL acceptance tests for the library app
├── test_multi_db.py         # live tests under FAKESHOP_SHARDED=1 (skipped otherwise)
└── test_scalars_api.py      # live wire-format / introspection tests for the scalars app
```

The example project code itself is organized as:

```text
examples/fakeshop/
├── manage.py
├── config/                  # project orchestration
│   ├── __init__.py
│   ├── settings.py
│   ├── schema.py
│   ├── urls.py
│   └── wsgi.py
└── apps/                    # domain apps; import as apps.<app_name>
    ├── __init__.py
    ├── library/             # Branch/Shelf/Book/Patron/Loan + Patron.lifetime_fines_cents BigInt
    ├── products/            # Category/Item/Property/Entry catalog example
    └── scalars/             # ScalarSpecimen + NullableScalarSpecimen converter substrate
```

### Target shape (as Layer-3 subsystems land)

Each new source subpackage gets a parallel directory under `tests/`; each new flat single-file module gets a `tests/test_<module>.py`. The example test trees grow new files in place — no new subdirectories needed there.

```text
tests/                       # Package-internal tests (target as Layer-3 subsystems land)
├── base/                    # FROZEN
│   ├── test_init.py
│   └── test_conf.py
├── test_apps.py             # AppConfig
├── test_registry.py         # model→type registry
├── test_exceptions.py       # error hierarchy
├── test_fieldset.py         # FieldSet (single-file Layer-3 module)
├── test_list_field.py       # DjangoListField (single-file Layer-3 module)
├── test_permissions.py      # apply_cascade_permissions, per-field hooks
├── test_connection.py       # DjangoConnectionField
├── types/
│   ├── test_base.py
│   ├── test_converters.py
│   ├── test_definition_order.py
│   ├── test_definition_order_schema.py
│   ├── test_generic_foreign_key.py
│   ├── test_relay_interfaces.py
│   └── test_resolvers.py
├── optimizer/
│   ├── test_definition_order.py
│   ├── test_extension.py
│   ├── test_field_meta.py   # FieldMeta precomputed field metadata
│   ├── test_hints.py        # OptimizerHint typed wrapper
│   ├── test_plans.py        # OptimizationPlan / Prefetch chain helpers
│   ├── test_relay_id_projection.py
│   └── test_walker.py       # selection-tree walker
├── filters/
│   ├── test_base.py
│   ├── test_sets.py
│   ├── test_factories.py
│   └── test_inputs.py
├── orders/
│   ├── test_base.py
│   ├── test_sets.py
│   └── test_factories.py
├── aggregates/
│   ├── test_base.py
│   ├── test_sets.py
│   └── test_factories.py
├── management/
│   └── test_export_schema.py
└── utils/
    ├── test_relations.py
    ├── test_strings.py
    ├── test_typing.py
    └── test_queryset.py

examples/fakeshop/tests/     # unchanged shape; new files land here per concern
examples/fakeshop/test_query/   # unchanged shape; HTTP-level GraphQL tests land here
```

### What each folder holds

`tests/` — **Package-internal tests.** The system-under-test is `django_strawberry_framework` itself, even when fakeshop models are used as fixtures. This tree mirrors the package source one-to-one: every source subpackage becomes a directory, every source module gets a `test_<module>.py` at the parallel path. Coverage of this tree gates `fail_under = 100` against `[tool.coverage.run] source = ["django_strawberry_framework"]`.

`tests/base/` — **Frozen.** Holds exactly two files: `test_init.py` (version sanity check) and `test_conf.py` (`django_strawberry_framework/conf.py` settings reader). Both files may grow as `conf.py` changes, but no new files are ever added here. This is the conf+version baseline that gates the package's most fundamental contract.

`tests/<subpkg>/` — **Subsystem tests** for the parallel source subpackage. `tests/types/` covers `django_strawberry_framework/types/`; `tests/optimizer/` covers `django_strawberry_framework/optimizer/`; `tests/filters/` will cover `django_strawberry_framework/filters/`; and so on. Each test module exercises the named source module: `tests/types/test_base.py` ↔ `types/base.py`, `tests/types/test_converters.py` ↔ `types/converters.py`, etc. Subdirectories carry an `__init__.py` shell to match the existing `tests/__init__.py` + `tests/base/__init__.py` convention so pytest collects them as `tests.<subpkg>.<module>`.

`tests/test_<module>.py` (flat, at the root) — **Single-file Layer-3 module tests.** When a Layer-3 module lives flat at the package root (`fieldset.py`, `permissions.py`, `connection.py`) rather than as its own subpackage, its test file lives flat at `tests/test_<module>.py` rather than under a one-file subdirectory. If/when the source module graduates to a subpackage (e.g. `permissions/` once it earns 3+ files), the flat `tests/test_permissions.py` graduates to `tests/permissions/` at the same time.

`examples/fakeshop/tests/` — **Example-project tests, no HTTP `/graphql/`.** The system-under-test is the fakeshop example project, exercised through real Django flows but in-process: management commands via `django.core.management.call_command`, admin actions via `django.test.Client.get("/admin/...")`, URL views via `django.test.Client.get("/")`, schema execution via `strawberry.Schema.execute_sync(...)` directly. Slow enough that they live in their own tree but fast enough not to need an HTTP server. Outside the package coverage gate (the example is example code, not shipping code) but still runs under `uv run pytest` because `pytest.ini` lists it in `testpaths`.

`examples/fakeshop/test_query/` — **Example-project tests, live `/graphql/` HTTP. First place to add a test.** The system-under-test is the same fakeshop project, but exercised end-to-end through the Django + Strawberry HTTP stack via `django.test.Client.post("/graphql/", ...)`. Verifies the full request pipeline: URL routing, view, schema execution, JSON response serialization. **Any new package code whose coverage can be earned by a real GraphQL query lands a test here first** — only fall back to the sibling `tests/` tree or the package-internal `tests/` tree when the code path cannot be reached from a live `/graphql/` request. `test_library_api.py` is the live acceptance suite for the `library` app (relation traversal, nullable scalars, choice enums, optimizer SQL shape, optimizer hints, consumer-shaped querysets, consumer relation override, `Patron.lifetime_fines_cents` BigInt round-trip past JS safe-integer range). `test_scalars_api.py` is the live converter-coverage suite for the `scalars` app — pins every non-trivial `SCALAR_MAP` entry in both nullable and non-null shapes, plus self-FK (`parent`/`children`) and cross-model FK (`partner`/`nullable_partners`) traversal. `test_multi_db.py` runs only under `FAKESHOP_SHARDED=1`. Same coverage and discovery rules as the sibling `examples/fakeshop/tests/` tree.
HTTP tests that import the project schema must preserve the reload pattern from `test_library_api.py`: clear the global registry, reload app schema modules, then reload the project schema and URLconf. That keeps package tests that clear the registry from leaving cached example `DjangoType` classes detached from the active registry.

`examples/<project>/...` — **Future example projects** mirror the same two-folder split: every additional example app under `examples/` ships its own `tests/` and `test_query/` directories with the same in-process / HTTP separation. `pytest.ini`'s `testpaths` will be extended one entry per pair when a second example lands; nothing about the package or the existing fakeshop test trees changes.

`examples/fakeshop/apps/products/tests/` — **Per-Django-app convention placeholder.** Empty by design — the per-app `tests/` folder is where Django expects an app's own tests to live by convention, but the fakeshop example consolidates all example tests at the project level (`examples/fakeshop/tests/` and `examples/fakeshop/test_query/`) rather than per-app. The empty directory stays committed as documentation of the convention; do not add files there.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[backlog]: ../BACKLOG.md
[kanban]: ../KANBAN.md
[readme]: ../README.md

<!-- docs/ -->
[glossary]: GLOSSARY.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
