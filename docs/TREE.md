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

Source: `django_strawberry_framework/`

```text
django_strawberry_framework/    # Public API of django-strawberry-framework, a DRF-inspired Django integration for Strawberry GraphQL.
├── _django_patches.py            # Defensive patches for upstream Django bugs, applied at app load.
├── apps.py                       # Django ``AppConfig`` - registers the package and applies its Django patches at app load.
├── conf.py                       # Package settings, read from the host project's ``DJANGO_STRAWBERRY_FRAMEWORK`` dict.
├── connection.py                 # ``DjangoConnection[T]`` + ``DjangoConnectionField`` - the Relay cursor-pagination surface.
├── exceptions.py                 # Exceptions raised by django-strawberry-framework.
├── list_field.py                 # ``DjangoListField`` - non-Relay ``list[T]`` field for root Query fields.
├── py.typed
├── registry.py                   # Type registry for ``DjangoType`` metadata, pending relations, and choice enums.
├── relay.py                      # Root Relay refetch fields - ``DjangoNodeField`` / ``DjangoNodesField``.
├── scalars.py                    # Public GraphQL scalars + the ``strawberry_config()`` schema-config factory.
├── sets_mixins.py                # Mixins shared across the FilterSet / OrderSet / AggregateSet / FieldSet family.
├── filters/    # Filtering subsystem - declarative ``FilterSet`` classes that become GraphQL ``filter:`` arguments.
│   ├── base.py                   # Filter primitives + ``RelatedFilter``.
│   ├── factories.py              # Filter input-class BFS factory + the dynamic-FilterSet cache for connection fields.
│   ├── inputs.py                 # Filter input namespace, lookup-name scaffolding, and shape converters.
│   └── sets.py                   # ``FilterSet`` + ``FilterSetMetaclass`` - declaration, validation, and the apply pipeline.
├── management/    # Django management namespace for the framework's ``manage.py`` commands.
│   └── commands/    # Implementations of the framework's ``manage.py`` commands (``export_schema``, ``inspect_django_type``).
│       ├── export_schema.py      # manage.py export_schema - print or write the GraphQL SDL for a Strawberry schema symbol.
│       └── inspect_django_type.py  # manage.py inspect_django_type - print a DjangoType's per-field GraphQL resolution table.
├── optimizer/    # Optimizer subsystem - selection-driven queryset planning via ``DjangoOptimizerExtension`` (N+1 prevention).
│   ├── _context.py               # Shared context read/write helpers for optimizer <-> resolver hand-off.
│   ├── extension.py              # ``DjangoOptimizerExtension`` - Strawberry schema extension solving N+1 via queryset plans.
│   ├── field_meta.py             # ``FieldMeta`` - precomputed Django field metadata for the optimizer walker.
│   ├── hints.py                  # ``OptimizerHint`` - typed wrapper for ``Meta.optimizer_hints`` values.
│   ├── plans.py                  # ``OptimizationPlan`` - the shape the walker emits and the extension consumes.
│   └── walker.py                 # Selection-tree walker that converts GraphQL selections into an ``OptimizationPlan``.
├── orders/    # Ordering subsystem - declarative ``OrderSet`` classes that become GraphQL ``orderBy:`` arguments.
│   ├── base.py                   # ``RelatedOrder`` - the nested-path ordering primitive.
│   ├── factories.py              # Order input-class BFS factory; dynamic ``OrderSet`` generation is deferred.
│   ├── inputs.py                 # Order input namespace, direction enum, and input-data adapters.
│   └── sets.py                   # ``OrderSet`` + ``OrderSetMetaclass`` - declaration, validation, and the apply pipeline.
├── testing/    # Consumer-facing test utilities - cooperative Django connection-method wrapping (Trac #37064 defense).
│   ├── _wrap.py                  # Cooperative connection-method wrapping for consumer test instrumentation.
│   └── relay.py                  # Public Relay test helpers - ``global_id_for`` / ``decode_global_id``.
├── types/    # Type-system subsystem - ``DjangoType``, field/relation conversion, Relay integration, and finalization.
│   ├── base.py                   # ``DjangoType`` - Meta-class-driven Django-model-to-Strawberry-type adapter.
│   ├── converters.py             # Convert Django model fields to Strawberry-compatible Python types.
│   ├── definition.py             # ``DjangoTypeDefinition`` - canonical metadata for collected ``DjangoType`` classes.
│   ├── finalizer.py              # ``finalize_django_types()`` - the once-only finalization gate for collected ``DjangoType`` classes.
│   ├── relations.py              # Pending relation records for definition-order-independent ``DjangoType`` finalization.
│   ├── relay.py                  # Internal Relay helpers - interface injection, node resolver defaults, and GlobalID strategies.
│   └── resolvers.py              # Relation-field resolvers for ``DjangoType`` relation annotations.
└── utils/    # Cross-cutting helpers shared by every subsystem - relation shapes, string casing, and type unwrapping.
    ├── relations.py              # Relation-shape helpers shared by converters, resolvers, and the optimizer.
    ├── strings.py                # String-case helpers for the GraphQL <-> Django name boundary.
    └── typing.py                 # Type-unwrapping helpers for Strawberry / Python / GraphQL types.
```


## Test layout

Tests live in four deliberate places, each chosen by what the test is proving. The root `tests/` tree protects package internals and mirrors `django_strawberry_framework/`. `examples/fakeshop/apps/<app>/tests/` protects one Django app at a time without live HTTP. `examples/fakeshop/tests/` protects project-level fakeshop behavior that belongs to no single app. `examples/fakeshop/test_query/` is the live `/graphql/` acceptance surface.

**Coverage priority.** If a package line can be covered by a real fakeshop GraphQL request, put that test in `examples/fakeshop/test_query/`. Use the non-live fakeshop trees for services, models, admin, commands, URLs, or in-process schema execution. Use root `tests/` for package internals, invalid configuration, registry/finalizer mechanics, and paths unreachable through a realistic GraphQL request. Mock only when the real path is impossible. These placement rules are pinned in [`AGENTS.md`][agents].

### Current test trees

Source: `tests/`

```text
tests/    # Package-internal tests for django_strawberry_framework.
├── test_apps.py                  # AppConfig tests for package registration and Django patch application.
├── test_clean_up.py              # Script tests for clean_up generated-artifact deletion boundaries.
├── test_connection.py            # DjangoConnection and DjangoConnectionField tests for Relay pagination behavior.
├── test_django_patches.py        # Django patch tests for DB connection wrapping and multi-database safety.
├── test_list_field.py            # DjangoListField tests for root list fields, queryset visibility, and sidecars.
├── test_registry.py              # TypeRegistry unit tests for model/type lookup, primary types, and registry reset.
├── test_relay_connection.py      # Relation-as-Connection tests for cursor conformance and Relay field upgrades.
├── test_relay_node_field.py      # Root Relay refetch tests for DjangoNodeField and DjangoNodesField.
├── test_scalars.py               # Scalar tests for BigInt and the framework StrawberryConfig helper.
├── base/    # Frozen base tests for package configuration and version sanity.
│   ├── test_conf.py              # Package settings-reader tests for DJANGO_STRAWBERRY_FRAMEWORK.
│   └── test_init.py              # Package init tests for version metadata and public exports.
├── filters/    # Package tests for the FilterSet subsystem.
│   ├── test_base.py              # Filter primitive tests for typed, list, range, global-ID, and related filters.
│   ├── test_factories.py         # FilterArgumentsFactory tests for BFS input generation and dynamic FilterSet caching.
│   ├── test_finalizer.py         # Finalizer tests for filter binding, owner-aware materialization, and orphan validation.
│   ├── test_inputs.py            # Filter input tests for lookup naming, annotation conversion, and value normalization.
│   ├── test_sets.py              # FilterSet tests for Meta collection, validation, sync/async apply, and tree overrides.
│   └── fixtures/    # Fixture modules for filter lazy-resolution tests.
│       └── filtersets.py         # Fixture FilterSet declarations for cross-module lazy-resolution tests.
├── management/    # Package tests for django-strawberry-framework management commands.
│   ├── test_export_schema.py     # Management command tests for export_schema SDL output and failure modes.
│   └── test_inspect_django_type.py  # Management command tests for inspect_django_type field-resolution tables.
├── optimizer/    # Package tests for optimizer planning and DjangoOptimizerExtension.
│   ├── test_definition_order.py  # Optimizer tests for definition-order-independent DjangoType relation graphs.
│   ├── test_extension.py         # DjangoOptimizerExtension tests for root-gated planning and queryset optimization.
│   ├── test_field_meta.py        # FieldMeta tests for precomputed relation metadata used by optimizer planning.
│   ├── test_hints.py             # OptimizerHint tests for Meta.optimizer_hints normalization and validation.
│   ├── test_multi_db.py          # Optimizer-plan tests for multi-database cooperation and DB-alias preservation.
│   ├── test_plans.py             # OptimizationPlan tests for plan structure, keys, paths, and select/prefetch state.
│   ├── test_relay_id_projection.py  # Optimizer tests for Relay GlobalID projection and connector-column invariants.
│   └── test_walker.py            # Selection-walker tests for GraphQL selection to ORM OptimizationPlan conversion.
├── orders/    # Package tests for the OrderSet subsystem.
│   ├── test_base.py              # RelatedOrder tests for nested ordering paths and lazy related-class handling.
│   ├── test_composition.py       # Filter and order composition smoke tests for Layer-3 read-side integration.
│   ├── test_factories.py         # OrderArgumentsFactory tests for BFS input generation and dynamic OrderSet caching.
│   ├── test_finalizer.py         # Finalizer tests for order binding, Meta.orderset_class promotion, and orphan validation.
│   ├── test_inputs.py            # Order input tests for Ordering enum, input materialization, reset, and normalization.
│   └── test_sets.py              # OrderSet tests for Meta collection, validation, sync/async apply, and permission scope.
├── testing/    # Package tests for public consumer testing utilities.
│   ├── test_relay.py             # Public Relay helper tests for global_id_for and decode_global_id.
│   └── test_wrap.py              # Connection-method wrapping tests for cooperative consumer instrumentation.
├── types/    # Package tests for the DjangoType subsystem.
│   ├── test_base.py              # DjangoType tests for Meta validation, scalar mapping, relations, registry, and get_queryset.
│   ├── test_converters.py        # Converter tests for scalar mapping, choice enums, and relation annotations.
│   ├── test_definition_order.py  # Acceptance tests for definition-order-independent DjangoType relation finalization.
│   ├── test_definition_order_schema.py  # Schema-build tests for definition-order-independent DjangoType finalization.
│   ├── test_definition_relations.py  # DjangoTypeDefinition tests for related_target_for relation lookup.
│   ├── test_generic_foreign_key.py  # DjangoType tests for GenericForeignKey rejection and GenericRelation support.
│   ├── test_relations.py         # PendingRelation tests for identity hashing and dataclass field contracts.
│   ├── test_relay_interfaces.py  # DjangoType Relay interface tests for Node wiring and resolver contracts.
│   ├── test_resolvers.py         # Relation resolver tests for Django relation managers and optimizer hand-off.
│   └── fixtures/    # Fixture modules for cross-module DjangoType resolution tests.
│       ├── branch_module.py      # Cross-module fixture declaring BranchType and BranchFilter together.
│       └── shelf_module.py       # Cross-module fixture declaring ShelfType and ShelfFilter together.
└── utils/    # Package tests for shared utility helpers.
    ├── test_relations.py         # Relation utility tests for relation_kind classification and package re-exports.
    ├── test_strings.py           # String utility tests for snake_case, camelCase, and PascalCase conversion.
    └── test_typing.py            # Typing utility tests for Strawberry, Python, and GraphQL type unwrapping.
```


Source: `examples/fakeshop/apps/*/tests/`

```text
examples/fakeshop/apps/    # Per-Django-app, non-live tests that stay beside the app they protect.
├── glossary/
│   └── tests/    # Non-live app tests for glossary models, factories, and import commands.
│       ├── test_factories.py     # Glossary factory tests for default values, aliases, categories, and spec mentions.
│       ├── test_import_spec_terms.py  # Glossary import command tests for DONE-card spec term extraction.
│       └── test_models.py        # Glossary model tests for term edges, aliases, categories, and spec mentions.
├── kanban/
│   └── tests/    # Non-live app tests for kanban services, signals, and board invariants.
│       ├── test_services.py      # Kanban service tests for structured card creation and rollback behavior.
│       └── test_signals.py       # Kanban signal tests for dependencies, done-card guards, blocking, and ordering.
├── library/
│   └── tests/    # Non-live app tests for library models and in-process schema execution.
│       ├── test_models.py        # Library model tests for __str__ output and computed field behavior.
│       └── test_schema.py        # Library schema tests for in-process GraphQL execution without HTTP.
├── products/
│   └── tests/    # Non-live app tests for products admin, commands, models, schema, and services.
│       ├── test_admin.py         # Products admin tests for changelist query-param branches.
│       ├── test_commands.py      # Products command tests for service-backed seed and delete management commands.
│       ├── test_models.py        # Products model tests for example-domain __str__ implementations.
│       ├── test_schema.py        # Products schema tests for in-process GraphQL execution without HTTP.
│       └── test_services.py      # Products service tests for Faker-driven seed_data, create_users, and delete_data.
└── scalars/
    └── tests/    # Non-live app tests for scalar substrate models.
        └── test_models.py        # Scalars model tests for __str__ output and nullable specimen relationships.
```


Source: `examples/fakeshop/tests/`

```text
examples/fakeshop/tests/    # Example-project tests for fakeshop behavior without live /graphql HTTP.
├── test_export_schema.py         # Fakeshop project command tests for export_schema against the configured schema.
├── test_inspect_django_type.py   # Fakeshop project command tests for inspect_django_type against example DjangoTypes.
└── test_urls.py                  # Fakeshop project URL tests for the index view and URL configuration.
```


Source: `examples/fakeshop/test_query/`

```text
examples/fakeshop/test_query/    # Live GraphQL HTTP tests for fakeshop's consumer-visible API.
├── README.md                     # Live GraphQL-API tests for the fakeshop example project.
├── test_glossary_api.py          # Live GraphQL HTTP tests for the glossary docs-as-data API.
├── test_kanban_api.py            # Live GraphQL HTTP tests for the kanban board docs-as-data API.
├── test_library_api.py           # Live GraphQL HTTP tests for library relations, optimizer behavior, and Relay fields.
├── test_multi_db.py              # Live GraphQL HTTP tests for sharded fakeshop multi-database cooperation.
├── test_products_api.py          # Live GraphQL HTTP tests for the products catalog API surface.
├── test_scalars_api.py           # Live GraphQL HTTP tests for scalar conversion and wire-format coverage.
└── test_scalars_filter_api.py    # Live GraphQL HTTP tests for scalar filter input and queryset behavior.
```


## Fakeshop example project

### Project tree

Source: `examples/fakeshop/`

```text
examples/fakeshop/    # A Django + Strawberry GraphQL example project that exercises django-strawberry-framework end-to-end.
├── manage.py                     # Django command-line entry point for the fakeshop example project.
├── config/    # Project orchestration package for fakeshop settings, URLs, WSGI, and schema composition.
│   ├── settings.py               # Django settings for fakeshop and its single-database or sharded test modes.
│   ├── schema.py                 # Project-level GraphQL schema that composes every fakeshop app query.
│   ├── urls.py                   # URL routing for fakeshop's index, admin, auth, and GraphQL endpoints.
│   └── wsgi.py                   # WSGI application entry point for the fakeshop example project.
└── apps/    # Domain-app namespace imported as ``apps.<app_name>`` from the fakeshop project root.
    ├── glossary/    # Glossary app storing documentation terms and spec-term audit rows.
    ├── kanban/    # Kanban app storing board cards, dependencies, docs prose, and markdown export metadata.
    ├── library/    # Library app modeling branch, shelf, book, patron, and loan relations for acceptance queries.
    ├── products/    # Products app modeling the seedable catalog used by admin, service, command, and query examples.
    │   ├── admin.py              # Admin registrations and shortcuts for inspecting and resetting products fixtures.
    │   ├── apps.py               # Django app configuration for the fakeshop products domain.
    │   ├── fields.py             # AdvancedFieldSet declarations for computed and permission-gated products fields.
    │   ├── filters.py            # FilterSet declarations for the fakeshop products app.
    │   ├── models.py             # Faker-shaped product catalog.
    │   ├── orders.py             # OrderSet declarations for the fakeshop products app.
    │   ├── schema.py             # GraphQL schema for the fakeshop products app.
    │   ├── services.py           # Dynamic data seeding service using Faker providers.
    │   ├── management/    # Management-command namespace for products data and user fixtures.
    │   │   └── commands/    # Django management commands for products fixture setup and teardown.
    │   │       ├── create_users.py  # Management command for creating permission-shaped products test users.
    │   │       ├── delete_data.py  # Management command for deleting seeded products catalog data.
    │   │       ├── delete_users.py  # Management command for deleting generated products test users.
    │   │       ├── seed_data.py  # Management command for seeding Faker-backed products catalog rows.
    │   │       └── seed_shards.py  # Populate the secondary shard SQLite DB used by the multi-DB / stress-test flow.
    │   └── tests/    # Non-live app tests for products admin, commands, models, schema, and services.
    │       ├── test_admin.py     # Products admin tests for changelist query-param branches.
    │       ├── test_commands.py  # Products command tests for service-backed seed and delete management commands.
    │       ├── test_models.py    # Products model tests for example-domain __str__ implementations.
    │       ├── test_schema.py    # Products schema tests for in-process GraphQL execution without HTTP.
    │       └── test_services.py  # Products service tests for Faker-driven seed_data, create_users, and delete_data.
    └── scalars/    # Scalars app modeling converter specimens for wire-format and filter coverage.
```

### App roles

Each app owns a focused example surface: products for catalog data and seed tooling, library for deeper relation graphs, scalars for converter coverage, and kanban/glossary for repository docs rendered from database rows.

`apps.glossary/`

It backs the exported ``docs/GLOSSARY.md`` file and keeps term aliases, categories, relationships, and spec mentions queryable through the same GraphQL surface used by the markdown exporter.

`apps.kanban/`

It is the database source for the root ``KANBAN.md`` export, including card ordering, dependency integrity, release targeting, glossary links, and reusable prose sections shared with other docs-as-data exporters.

`apps.library/`

It is the primary relational acceptance surface: live GraphQL tests use it to prove foreign keys, reverse relations, one-to-one links, many-to-many joins, Relay nodes, optimizer hints, consumer queryset shaping, and BigInt round-tripping.

`apps.products/`

It carries Category, Item, Property, and Entry data plus Faker-backed services, management commands, admin shortcuts, and filter/order sidecars for a practical catalog-style GraphQL schema.

`apps.scalars/`

It provides nullable and non-null scalar fixtures, relation edges, and override cases that let live GraphQL tests pin scalar conversion, serialization, filtering, and schema introspection behavior.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[readme]: ../README.md

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
