# Reference Trees

This file is the detailed layout reference. It exists to preserve the package/test tree rationale, upstream layout comparisons, and per-file responsibilities without turning [`../README.md`][readme] into a second architecture document.

For install, local development, testing, and the canonical documentation map, start from [`../README.md`][readme].

The upstream trees are captured for reference while shaping `django-strawberry-framework`'s own subpackage layout. Filters applied: `__pycache__/` directories, package-internal `tests/` directories, `conftest.py`, and `*.pyc` files are excluded so both trees show only the library logic surface (the strawberry-django source checkout already keeps tests outside the package directory; graphene-django ships its tests inside the installed package, so they're filtered here for comparability).

## graphene_django

Source: `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django`

```bash
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

```bash
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

```bash
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
├── _cross_web_patches.py         # Defensive patches for upstream ``cross_web`` bugs, applied at app load.
├── _django_patches.py            # Defensive patches for upstream Django bugs, applied at app load.
├── _strawberry_patches.py        # Defensive patches for upstream Strawberry bugs, applied at app load.
├── apps.py                       # Django ``AppConfig`` - registers the package and applies its Django patches at app load.
├── conf.py                       # Package settings, read from the host project's ``DJANGO_STRAWBERRY_FRAMEWORK`` dict.
├── connection.py                 # ``DjangoConnection[T]`` + ``DjangoConnectionField`` - the Relay cursor-pagination surface.
├── exceptions.py                 # Exceptions raised by django-strawberry-framework.
├── list_field.py                 # ``DjangoListField`` - non-Relay ``list[T]`` field for root Query fields.
├── permissions.py                # Call-time cascade visibility: ``apply_cascade_permissions`` (sync + async).
├── py.typed
├── registry.py                   # Type registry for ``DjangoType`` metadata, pending relations, and choice enums.
├── relay.py                      # Root Relay refetch fields - ``DjangoNodeField`` / ``DjangoNodesField``.
├── scalars.py                    # Public GraphQL scalars + the ``strawberry_config()`` schema-config factory.
├── sets_mixins.py                # Mixins and lifecycle machinery shared across the FilterSet / OrderSet / AggregateSet family.
├── auth/    # Opt-in session-auth field factories (spec-040).
│   ├── mutations.py              # Session-auth mutation factories + the phase-2.5 auth bind (spec-040).
│   └── queries.py                # The ``current_user()`` query-field factory + its return-alias namespace (spec-040).
├── filters/    # Filtering subsystem - declarative ``FilterSet`` classes that become GraphQL ``filter:`` arguments.
│   ├── base.py                   # Filter primitives + ``RelatedFilter``.
│   ├── factories.py              # Filter input-class BFS factory + the (currently unconsumed) dynamic-FilterSet cache.
│   ├── inputs.py                 # Filter input namespace, lookup-name scaffolding, and shape converters.
│   └── sets.py                   # ``FilterSet`` + ``FilterSetMetaclass`` - declaration, validation, and the apply pipeline.
├── forms/    # Form-mutations subsystem - the Django-``Form`` / ``ModelForm`` write side (spec-038).
│   ├── converter.py              # Form-field -> Strawberry annotation conversion + the per-input-field reverse map (spec-038).
│   ├── inputs.py                 # Form-derived ``@strawberry.input`` generation substrate (spec-038 Slice 1).
│   ├── resolvers.py              # The sync + async form-mutation resolver pipeline (spec-038 Slice 3).
│   └── sets.py                   # The ``DjangoFormMutation`` / ``DjangoModelFormMutation`` bases + ``Meta`` validation + bind (Slice 2).
├── management/    # Django management namespace for the framework's ``manage.py`` commands.
│   └── commands/    # Implementations of the framework's ``manage.py`` commands (``export_schema``, ``inspect_django_type``).
│       ├── _imports.py           # Shared importer-to-``CommandError`` helper for the framework's management commands.
│       ├── export_schema.py      # manage.py export_schema - print or write the GraphQL SDL for a Strawberry schema symbol.
│       └── inspect_django_type.py  # manage.py inspect_django_type - print a DjangoType's per-field GraphQL resolution table.
├── mutations/    # Mutations subsystem - the write side (spec-036).
│   ├── fields.py                 # ``DjangoMutationField`` - the write-side field factory (spec-036 Slice 3).
│   ├── inputs.py                 # Generated mutation-input namespace, the public ``FieldError`` envelope, and the payload wrapper.
│   ├── permissions.py            # ``DjangoModelPermission`` - the DRF-shaped default write-authorization class (spec-036).
│   ├── resolvers.py              # The sync + async create / update / delete write pipeline (spec-036 Slice 3).
│   └── sets.py                   # ``DjangoMutation`` base + metaclass + ``Meta`` validation + the phase-2.5 bind (spec-036 Slice 2).
├── optimizer/    # Optimizer subsystem - selection-driven queryset planning via ``DjangoOptimizerExtension`` (N+1 prevention).
│   ├── _context.py               # Shared context read/write helpers for optimizer <-> resolver hand-off.
│   ├── extension.py              # ``DjangoOptimizerExtension`` - Strawberry schema extension solving N+1 via queryset plans.
│   ├── field_meta.py             # ``FieldMeta`` - precomputed Django field metadata for the optimizer walker.
│   ├── hints.py                  # ``OptimizerHint`` - typed wrapper for ``Meta.optimizer_hints`` values.
│   ├── plans.py                  # ``OptimizationPlan`` - the shape the walker emits and the extension consumes.
│   ├── selections.py             # Selection-tree traversal substrate - the AST and converted-selection adapters.
│   └── walker.py                 # Selection-tree walker that converts GraphQL selections into an ``OptimizationPlan``.
├── orders/    # Ordering subsystem - declarative ``OrderSet`` classes that become GraphQL ``orderBy:`` arguments.
│   ├── base.py                   # ``RelatedOrder`` - the nested-path ordering primitive.
│   ├── factories.py              # Order input-class BFS factory; dynamic ``OrderSet`` generation is deferred.
│   ├── inputs.py                 # Order input namespace, direction enum, and input-data adapters.
│   └── sets.py                   # ``OrderSet`` + ``OrderSetMetaclass`` - declaration, validation, and the apply pipeline.
├── rest_framework/    # The DRF soft-dependency guard shared by every serializer-mutation module (spec-039 Decision 12).
│   ├── inputs.py                 # DRF-serializer-derived ``@strawberry.input`` generation substrate (spec-039 Slice 1).
│   ├── resolvers.py              # The sync + async serializer-mutation resolver pipeline (spec-039 Slice 3).
│   ├── serializer_converter.py   # DRF serializer-field -> Strawberry input conversion + the per-input-field reverse map (spec-039).
│   └── sets.py                   # The ``SerializerMutation`` base + ``Meta`` validation + the phase-2.5 bind (spec-039 Slice 2).
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
    ├── connections.py            # Connection planner/resolver shared contracts: window bounds + sidecar kwargs.
    ├── converters.py             # Fail-loud converter-dispatch skeleton shared by the form + serializer converters (spec-039 P1.4).
    ├── input_values.py           # Set-input traversal substrate shared by the FilterSet and OrderSet families.
    ├── inputs.py                 # Generated-input substrate shared by the filter and order set families.
    ├── permissions.py            # Active-input permission traversal shared by the FilterSet and OrderSet families.
    ├── querysets.py              # Query-source + ``DjangoType.get_queryset`` visibility contract, single-sited.
    ├── relations.py              # Relation-shape helpers shared by converters, resolvers, and the optimizer.
    ├── strings.py                # String-case helpers for the GraphQL <-> Django name boundary.
    └── typing.py                 # Type-unwrapping helpers for Strawberry / Python / GraphQL types.
```

## django_strawberry_framework (target package layout)

The current package tree merged with every not-yet-existing path linked from a WIP/TODO card in [`KANBAN.md`](../KANBAN.md). Each planned entry names the card that introduces it; backlog cards and DONE-card historical paths are ignored.

Source: `django_strawberry_framework/ (+ planned card paths)`

```text
django_strawberry_framework/    # Public API of django-strawberry-framework, a DRF-inspired Django integration for Strawberry GraphQL.
├── _cross_web_patches.py         # Defensive patches for upstream ``cross_web`` bugs, applied at app load.
├── _django_patches.py            # Defensive patches for upstream Django bugs, applied at app load.
├── _strawberry_patches.py        # Defensive patches for upstream Strawberry bugs, applied at app load.
├── apps.py                       # Django ``AppConfig`` - registers the package and applies its Django patches at app load.
├── conf.py                       # Package settings, read from the host project's ``DJANGO_STRAWBERRY_FRAMEWORK`` dict.
├── connection.py                 # ``DjangoConnection[T]`` + ``DjangoConnectionField`` - the Relay cursor-pagination surface.
├── exceptions.py                 # Exceptions raised by django-strawberry-framework.
├── list_field.py                 # ``DjangoListField`` - non-Relay ``list[T]`` field for root Query fields.
├── permissions.py                # Call-time cascade visibility: ``apply_cascade_permissions`` (sync + async).
├── py.typed
├── registry.py                   # Type registry for ``DjangoType`` metadata, pending relations, and choice enums.
├── relay.py                      # Root Relay refetch fields - ``DjangoNodeField`` / ``DjangoNodesField``.
├── routers.py                    # planned by WIP-ALPHA-041-0.0.14 - Channels ASGI router (migration aid)
├── scalars.py                    # Public GraphQL scalars + the ``strawberry_config()`` schema-config factory.
├── sets_mixins.py                # Mixins and lifecycle machinery shared across the FilterSet / OrderSet / AggregateSet family.
├── aggregates/    # planned by TODO-BETA-049-0.1.3 - Aggregation subsystem
├── auth/    # Opt-in session-auth field factories (spec-040).
│   ├── mutations.py              # Session-auth mutation factories + the phase-2.5 auth bind (spec-040).
│   └── queries.py                # The ``current_user()`` query-field factory + its return-alias namespace (spec-040).
├── extensions/    # planned by TODO-ALPHA-044-0.0.14 - Response-extensions debug middleware
│   └── debug.py                  # planned by TODO-ALPHA-044-0.0.14 - Response-extensions debug middleware
├── fieldset/    # planned by TODO-BETA-046-0.1.1 - `FieldSet`
├── filters/    # Filtering subsystem - declarative ``FilterSet`` classes that become GraphQL ``filter:`` arguments.
│   ├── base.py                   # Filter primitives + ``RelatedFilter``.
│   ├── factories.py              # Filter input-class BFS factory + the (currently unconsumed) dynamic-FilterSet cache.
│   ├── inputs.py                 # Filter input namespace, lookup-name scaffolding, and shape converters.
│   └── sets.py                   # ``FilterSet`` + ``FilterSetMetaclass`` - declaration, validation, and the apply pipeline.
├── forms/    # Form-mutations subsystem - the Django-``Form`` / ``ModelForm`` write side (spec-038).
│   ├── converter.py              # Form-field -> Strawberry annotation conversion + the per-input-field reverse map (spec-038).
│   ├── inputs.py                 # Form-derived ``@strawberry.input`` generation substrate (spec-038 Slice 1).
│   ├── resolvers.py              # The sync + async form-mutation resolver pipeline (spec-038 Slice 3).
│   └── sets.py                   # The ``DjangoFormMutation`` / ``DjangoModelFormMutation`` bases + ``Meta`` validation + bind (Slice 2).
├── management/    # Django management namespace for the framework's ``manage.py`` commands.
│   └── commands/    # Implementations of the framework's ``manage.py`` commands (``export_schema``, ``inspect_django_type``).
│       ├── _imports.py           # Shared importer-to-``CommandError`` helper for the framework's management commands.
│       ├── export_schema.py      # manage.py export_schema - print or write the GraphQL SDL for a Strawberry schema symbol.
│       └── inspect_django_type.py  # manage.py inspect_django_type - print a DjangoType's per-field GraphQL resolution table.
├── middleware/    # planned by TODO-ALPHA-042-0.0.14 - Debug-toolbar middleware
│   └── debug_toolbar.py          # planned by TODO-ALPHA-042-0.0.14 - Debug-toolbar middleware
├── mutations/    # Mutations subsystem - the write side (spec-036).
│   ├── fields.py                 # ``DjangoMutationField`` - the write-side field factory (spec-036 Slice 3).
│   ├── inputs.py                 # Generated mutation-input namespace, the public ``FieldError`` envelope, and the payload wrapper.
│   ├── permissions.py            # ``DjangoModelPermission`` - the DRF-shaped default write-authorization class (spec-036).
│   ├── resolvers.py              # The sync + async create / update / delete write pipeline (spec-036 Slice 3).
│   └── sets.py                   # ``DjangoMutation`` base + metaclass + ``Meta`` validation + the phase-2.5 bind (spec-036 Slice 2).
├── optimizer/    # Optimizer subsystem - selection-driven queryset planning via ``DjangoOptimizerExtension`` (N+1 prevention).
│   ├── _context.py               # Shared context read/write helpers for optimizer <-> resolver hand-off.
│   ├── extension.py              # ``DjangoOptimizerExtension`` - Strawberry schema extension solving N+1 via queryset plans.
│   ├── field_meta.py             # ``FieldMeta`` - precomputed Django field metadata for the optimizer walker.
│   ├── hints.py                  # ``OptimizerHint`` - typed wrapper for ``Meta.optimizer_hints`` values.
│   ├── plans.py                  # ``OptimizationPlan`` - the shape the walker emits and the extension consumes.
│   ├── selections.py             # Selection-tree traversal substrate - the AST and converted-selection adapters.
│   └── walker.py                 # Selection-tree walker that converts GraphQL selections into an ``OptimizationPlan``.
├── orders/    # Ordering subsystem - declarative ``OrderSet`` classes that become GraphQL ``orderBy:`` arguments.
│   ├── base.py                   # ``RelatedOrder`` - the nested-path ordering primitive.
│   ├── factories.py              # Order input-class BFS factory; dynamic ``OrderSet`` generation is deferred.
│   ├── inputs.py                 # Order input namespace, direction enum, and input-data adapters.
│   └── sets.py                   # ``OrderSet`` + ``OrderSetMetaclass`` - declaration, validation, and the apply pipeline.
├── permissions/    # planned by TODO-BETA-051-0.1.4 - Opt-in node-sentinel redaction tier (`Meta.redaction_mode`)
├── rest_framework/    # The DRF soft-dependency guard shared by every serializer-mutation module (spec-039 Decision 12).
│   ├── inputs.py                 # DRF-serializer-derived ``@strawberry.input`` generation substrate (spec-039 Slice 1).
│   ├── resolvers.py              # The sync + async serializer-mutation resolver pipeline (spec-039 Slice 3).
│   ├── serializer_converter.py   # DRF serializer-field -> Strawberry input conversion + the per-input-field reverse map (spec-039).
│   └── sets.py                   # The ``SerializerMutation`` base + ``Meta`` validation + the phase-2.5 bind (spec-039 Slice 2).
├── testing/    # Consumer-facing test utilities - cooperative Django connection-method wrapping (Trac #37064 defense).
│   ├── _wrap.py                  # Cooperative connection-method wrapping for consumer test instrumentation.
│   ├── client.py                 # planned by TODO-ALPHA-043-0.0.14 - Test client helper
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
    ├── connections.py            # Connection planner/resolver shared contracts: window bounds + sidecar kwargs.
    ├── converters.py             # Fail-loud converter-dispatch skeleton shared by the form + serializer converters (spec-039 P1.4).
    ├── input_values.py           # Set-input traversal substrate shared by the FilterSet and OrderSet families.
    ├── inputs.py                 # Generated-input substrate shared by the filter and order set families.
    ├── permissions.py            # Active-input permission traversal shared by the FilterSet and OrderSet families.
    ├── querysets.py              # Query-source + ``DjangoType.get_queryset`` visibility contract, single-sited.
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
├── conftest.py                   # Shared pytest fixtures and test-suite instrumentation.
├── test_apps.py                  # AppConfig tests for package registration and Django patch application.
├── test_clean_up.py              # Script tests for clean_up generated-artifact deletion boundaries.
├── test_connection.py            # DjangoConnection and DjangoConnectionField tests for Relay pagination behavior.
├── test_cross_web_patches.py     # Tests for the ``cross_web`` non-UTF-8 request-body patch.
├── test_django_patches.py        # Django patch tests for DB connection wrapping and multi-database safety.
├── test_list_field.py            # DjangoListField tests for root list fields, queryset visibility, and sidecars.
├── test_permissions.py           # Cascade-permission tests - ``apply_cascade_permissions`` / ``aapply_cascade_permissions``.
├── test_registry.py              # TypeRegistry unit tests for model/type lookup, primary types, and registry reset.
├── test_relay_connection.py      # Relation-as-Connection tests for cursor conformance and Relay field upgrades.
├── test_relay_node_field.py      # Root Relay refetch tests for DjangoNodeField and DjangoNodesField.
├── test_scalars.py               # Scalar tests for BigInt and the framework StrawberryConfig helper.
├── test_strawberry_patches.py    # Tests for the Strawberry request-body patch.
├── auth/    # Package-internal tests for the opt-in auth subsystem (spec-040).
│   ├── test_mutations.py         # Package-internal tests for ``django_strawberry_framework/auth/mutations.py`` (spec-040).
│   └── test_queries.py           # Package-internal tests for ``django_strawberry_framework/auth/queries.py`` (spec-040).
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
├── forms/    # Package tests for the forms subsystem (form-derived inputs + the converter, spec-038).
│   ├── test_converter.py         # Converter tests for the form-field -> Strawberry annotation registry (spec-038 Slice 1).
│   ├── test_inputs.py            # Form-derived input tests for the generated ``<FormClass>Input`` / ``PartialInput`` (spec-038).
│   ├── test_resolvers.py         # Form-mutation resolver-pipeline tests (spec-038 Slice 3).
│   └── test_sets.py              # ``DjangoFormMutation`` / ``DjangoModelFormMutation`` bases, ``Meta`` validation, and the bind (spec-038 Slice 2).
├── management/    # Package tests for django-strawberry-framework management commands.
│   ├── test_export_schema.py     # Management command tests for export_schema SDL output and failure modes.
│   ├── test_imports.py           # Tests for the shared ``import_or_command_error`` management-command helper.
│   └── test_inspect_django_type.py  # Management command tests for inspect_django_type field-resolution tables.
├── mutations/    # Package tests for the mutations subsystem (DjangoMutation + generated inputs).
│   ├── test_fields.py            # ``DjangoMutationField`` factory tests (spec-036 Slice 3).
│   ├── test_inputs.py            # Mutation input tests for generated Input/PartialInput, FieldError, and the payload wrapper.
│   ├── test_permissions.py       # ``DjangoModelPermission`` class behavior + write-auth enforcement (spec-036 Slice 2 + Slice 3).
│   ├── test_resolvers.py         # Write-pipeline resolver tests (spec-036 Slice 3).
│   └── test_sets.py              # ``DjangoMutation`` base, ``Meta`` validation, registration, and the phase-2.5 bind.
├── optimizer/    # Package tests for optimizer planning and DjangoOptimizerExtension.
│   ├── test_definition_order.py  # Optimizer tests for definition-order-independent DjangoType relation graphs.
│   ├── test_extension.py         # DjangoOptimizerExtension tests for root-gated planning and queryset optimization.
│   ├── test_field_meta.py        # FieldMeta tests for precomputed relation metadata used by optimizer planning.
│   ├── test_hints.py             # OptimizerHint tests for Meta.optimizer_hints normalization and validation.
│   ├── test_multi_db.py          # Optimizer-plan tests for multi-database cooperation and DB-alias preservation.
│   ├── test_plans.py             # OptimizationPlan tests for plan structure, keys, paths, and select/prefetch state.
│   ├── test_relay_id_projection.py  # Optimizer tests for Relay GlobalID projection and connector-column invariants.
│   ├── test_selections.py        # Tests for the selection-traversal substrate (``optimizer/selections.py``).
│   └── test_walker.py            # Selection-walker tests for GraphQL selection to ORM OptimizationPlan conversion.
├── orders/    # Package tests for the OrderSet subsystem.
│   ├── test_base.py              # RelatedOrder tests for nested ordering paths and lazy related-class handling.
│   ├── test_composition.py       # Filter and order composition smoke tests for Layer-3 read-side integration.
│   ├── test_factories.py         # OrderArgumentsFactory tests for BFS input generation.
│   ├── test_finalizer.py         # Finalizer tests for order binding, Meta.orderset_class promotion, and orphan validation.
│   ├── test_inputs.py            # Order input tests for Ordering enum, input materialization, reset, and normalization.
│   └── test_sets.py              # OrderSet tests for Meta collection, validation, sync/async apply, and permission scope.
├── rest_framework/    # Package-internal DRF serializer-mutation tests (spec-039).
│   ├── test_converter.py         # Converter tests for the DRF serializer-field -> Strawberry annotation registry (spec-039 Slice 1).
│   ├── test_inputs.py            # Serializer-derived input tests for the generated ``<Serializer>Input`` / ``PartialInput`` (spec-039).
│   ├── test_resolvers.py         # Serializer-mutation resolver internals a live products `/graphql/` cannot drive (spec-039 Slice 3).
│   ├── test_sets.py              # ``SerializerMutation`` base, ``Meta`` validation, and the phase-2.5 bind (spec-039 Slice 2).
│   └── test_soft_dependency.py   # The DRF soft-dependency import guard (spec-039 Decision 12, Slice 2).
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
    ├── test_connections.py       # Unit tests for the shared connection planner/resolver contracts.
    ├── test_converters.py        # Tests for the shared fail-loud converter-dispatch skeleton (``utils/converters.py``, spec-039 P1.4).
    ├── test_input_values.py      # Tests for the neutral set-input traversal substrate (``utils/input_values.py``).
    ├── test_inputs.py            # Tests for the shared generated-input substrate (``utils/inputs.py``).
    ├── test_permissions.py       # Tests for the shared active-input permission substrate (``utils/permissions.py``).
    ├── test_querysets.py         # Tests for the shared query-source / visibility substrate (``utils/querysets.py``).
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
│       ├── test_commands.py      # Kanban command tests for changed-file and predicted-file import workflows.
│       ├── test_services.py      # Kanban service tests for structured card creation and rollback behavior.
│       └── test_signals.py       # Kanban signal tests for dependencies, done-card guards, blocking, and ordering.
├── library/
│   └── tests/    # Non-live app tests for library models and in-process schema execution.
│       ├── test_models.py        # Library model tests for __str__ output and computed field behavior.
│       └── test_schema.py        # Library schema tests for in-process GraphQL execution without HTTP.
├── products/
│   └── tests/    # Non-live app tests for products admin, commands, models, schema, and services.
│       ├── conftest.py           # Shared fixtures for the in-process ``apps.products`` schema tests.
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
├── conftest.py                   # Shared fixtures for the fakeshop acceptance (live ``/graphql/``) suites.
├── test_auth_api.py              # Live ``/graphql/`` auth API acceptance tests (spec-040).
├── test_glossary_api.py          # Live GraphQL HTTP tests for the glossary docs-as-data API.
├── test_kanban_api.py            # Live GraphQL HTTP tests for the kanban board docs-as-data API.
├── test_library_api.py           # Live GraphQL HTTP tests for library relations, optimizer behavior, and Relay fields.
├── test_multi_db.py              # Live GraphQL HTTP tests for sharded fakeshop multi-database cooperation.
├── test_mutation_atomicity.py    # Live ``/graphql/`` regression: a mutation must not commit a partial write.
├── test_products_api.py          # Live GraphQL HTTP tests for the products catalog API surface.
├── test_scalars_api.py           # Live GraphQL HTTP tests for scalar conversion and wire-format coverage.
├── test_scalars_filter_api.py    # Live GraphQL HTTP tests for scalar filter input and queryset behavior.
└── test_uploads_api.py           # Live GraphQL HTTP tests for the spec-037 file/image wire contract.
```


### Target test shape

The current test trees merged with the not-yet-existing test paths linked from WIP/TODO cards, annotated the same way as the target package layout. Test roots without planned additions match their current trees above.

Source: `tests/ (+ planned card paths)`

```text
tests/    # Package-internal tests for django_strawberry_framework.
├── conftest.py                   # Shared pytest fixtures and test-suite instrumentation.
├── test_apps.py                  # AppConfig tests for package registration and Django patch application.
├── test_clean_up.py              # Script tests for clean_up generated-artifact deletion boundaries.
├── test_connection.py            # DjangoConnection and DjangoConnectionField tests for Relay pagination behavior.
├── test_cross_web_patches.py     # Tests for the ``cross_web`` non-UTF-8 request-body patch.
├── test_django_patches.py        # Django patch tests for DB connection wrapping and multi-database safety.
├── test_list_field.py            # DjangoListField tests for root list fields, queryset visibility, and sidecars.
├── test_permissions.py           # Cascade-permission tests - ``apply_cascade_permissions`` / ``aapply_cascade_permissions``.
├── test_registry.py              # TypeRegistry unit tests for model/type lookup, primary types, and registry reset.
├── test_relay_connection.py      # Relation-as-Connection tests for cursor conformance and Relay field upgrades.
├── test_relay_node_field.py      # Root Relay refetch tests for DjangoNodeField and DjangoNodesField.
├── test_scalars.py               # Scalar tests for BigInt and the framework StrawberryConfig helper.
├── test_strawberry_patches.py    # Tests for the Strawberry request-body patch.
├── auth/    # Package-internal tests for the opt-in auth subsystem (spec-040).
│   ├── test_mutations.py         # Package-internal tests for ``django_strawberry_framework/auth/mutations.py`` (spec-040).
│   └── test_queries.py           # Package-internal tests for ``django_strawberry_framework/auth/queries.py`` (spec-040).
├── base/    # Frozen base tests for package configuration and version sanity.
│   ├── test_conf.py              # Package settings-reader tests for DJANGO_STRAWBERRY_FRAMEWORK.
│   └── test_init.py              # Package init tests for version metadata and public exports.
├── extensions/    # planned by TODO-ALPHA-044-0.0.14 - Response-extensions debug middleware
├── filters/    # Package tests for the FilterSet subsystem.
│   ├── test_base.py              # Filter primitive tests for typed, list, range, global-ID, and related filters.
│   ├── test_factories.py         # FilterArgumentsFactory tests for BFS input generation and dynamic FilterSet caching.
│   ├── test_finalizer.py         # Finalizer tests for filter binding, owner-aware materialization, and orphan validation.
│   ├── test_inputs.py            # Filter input tests for lookup naming, annotation conversion, and value normalization.
│   ├── test_pg_full_text.py      # planned by TODO-BETA-048-0.1.2 - Postgres full-text search filter primitives
│   ├── test_search_fields.py     # planned by TODO-BETA-047-0.1.2 - `Meta.search_fields` support
│   ├── test_sets.py              # FilterSet tests for Meta collection, validation, sync/async apply, and tree overrides.
│   └── fixtures/    # Fixture modules for filter lazy-resolution tests.
│       └── filtersets.py         # Fixture FilterSet declarations for cross-module lazy-resolution tests.
├── forms/    # Package tests for the forms subsystem (form-derived inputs + the converter, spec-038).
│   ├── test_converter.py         # Converter tests for the form-field -> Strawberry annotation registry (spec-038 Slice 1).
│   ├── test_inputs.py            # Form-derived input tests for the generated ``<FormClass>Input`` / ``PartialInput`` (spec-038).
│   ├── test_resolvers.py         # Form-mutation resolver-pipeline tests (spec-038 Slice 3).
│   └── test_sets.py              # ``DjangoFormMutation`` / ``DjangoModelFormMutation`` bases, ``Meta`` validation, and the bind (spec-038 Slice 2).
├── management/    # Package tests for django-strawberry-framework management commands.
│   ├── test_export_schema.py     # Management command tests for export_schema SDL output and failure modes.
│   ├── test_imports.py           # Tests for the shared ``import_or_command_error`` management-command helper.
│   └── test_inspect_django_type.py  # Management command tests for inspect_django_type field-resolution tables.
├── mutations/    # Package tests for the mutations subsystem (DjangoMutation + generated inputs).
│   ├── test_fields.py            # ``DjangoMutationField`` factory tests (spec-036 Slice 3).
│   ├── test_inputs.py            # Mutation input tests for generated Input/PartialInput, FieldError, and the payload wrapper.
│   ├── test_permissions.py       # ``DjangoModelPermission`` class behavior + write-auth enforcement (spec-036 Slice 2 + Slice 3).
│   ├── test_resolvers.py         # Write-pipeline resolver tests (spec-036 Slice 3).
│   └── test_sets.py              # ``DjangoMutation`` base, ``Meta`` validation, registration, and the phase-2.5 bind.
├── optimizer/    # Package tests for optimizer planning and DjangoOptimizerExtension.
│   ├── test_definition_order.py  # Optimizer tests for definition-order-independent DjangoType relation graphs.
│   ├── test_extension.py         # DjangoOptimizerExtension tests for root-gated planning and queryset optimization.
│   ├── test_field_meta.py        # FieldMeta tests for precomputed relation metadata used by optimizer planning.
│   ├── test_hints.py             # OptimizerHint tests for Meta.optimizer_hints normalization and validation.
│   ├── test_multi_db.py          # Optimizer-plan tests for multi-database cooperation and DB-alias preservation.
│   ├── test_plans.py             # OptimizationPlan tests for plan structure, keys, paths, and select/prefetch state.
│   ├── test_relay_id_projection.py  # Optimizer tests for Relay GlobalID projection and connector-column invariants.
│   ├── test_selections.py        # Tests for the selection-traversal substrate (``optimizer/selections.py``).
│   └── test_walker.py            # Selection-walker tests for GraphQL selection to ORM OptimizationPlan conversion.
├── orders/    # Package tests for the OrderSet subsystem.
│   ├── test_base.py              # RelatedOrder tests for nested ordering paths and lazy related-class handling.
│   ├── test_composition.py       # Filter and order composition smoke tests for Layer-3 read-side integration.
│   ├── test_factories.py         # OrderArgumentsFactory tests for BFS input generation.
│   ├── test_finalizer.py         # Finalizer tests for order binding, Meta.orderset_class promotion, and orphan validation.
│   ├── test_inputs.py            # Order input tests for Ordering enum, input materialization, reset, and normalization.
│   └── test_sets.py              # OrderSet tests for Meta collection, validation, sync/async apply, and permission scope.
├── rest_framework/    # Package-internal DRF serializer-mutation tests (spec-039).
│   ├── test_converter.py         # Converter tests for the DRF serializer-field -> Strawberry annotation registry (spec-039 Slice 1).
│   ├── test_inputs.py            # Serializer-derived input tests for the generated ``<Serializer>Input`` / ``PartialInput`` (spec-039).
│   ├── test_resolvers.py         # Serializer-mutation resolver internals a live products `/graphql/` cannot drive (spec-039 Slice 3).
│   ├── test_sets.py              # ``SerializerMutation`` base, ``Meta`` validation, and the phase-2.5 bind (spec-039 Slice 2).
│   └── test_soft_dependency.py   # The DRF soft-dependency import guard (spec-039 Decision 12, Slice 2).
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
    ├── test_connections.py       # Unit tests for the shared connection planner/resolver contracts.
    ├── test_converters.py        # Tests for the shared fail-loud converter-dispatch skeleton (``utils/converters.py``, spec-039 P1.4).
    ├── test_input_values.py      # Tests for the neutral set-input traversal substrate (``utils/input_values.py``).
    ├── test_inputs.py            # Tests for the shared generated-input substrate (``utils/inputs.py``).
    ├── test_permissions.py       # Tests for the shared active-input permission substrate (``utils/permissions.py``).
    ├── test_querysets.py         # Tests for the shared query-source / visibility substrate (``utils/querysets.py``).
    ├── test_relations.py         # Relation utility tests for relation_kind classification and package re-exports.
    ├── test_strings.py           # String utility tests for snake_case, camelCase, and PascalCase conversion.
    └── test_typing.py            # Typing utility tests for Strawberry, Python, and GraphQL type unwrapping.
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
    ├── accounts/    # Schema-only fakeshop accounts app exercising the session-auth surface (spec-040).
    ├── glossary/    # Glossary app storing documentation terms and spec-term audit rows.
    ├── kanban/    # Kanban app storing board cards, dependencies, docs prose, and markdown export metadata.
    ├── library/    # Library app modeling branch, shelf, book, patron, and loan relations for acceptance queries.
    ├── products/    # Products app modeling the seedable catalog used by admin, service, command, and query examples.
    │   ├── admin.py              # Admin registrations and shortcuts for inspecting and resetting products fixtures.
    │   ├── apps.py               # Django app configuration for the fakeshop products domain.
    │   ├── fields.py             # AdvancedFieldSet declarations for computed and permission-gated products fields.
    │   ├── filters.py            # FilterSet declarations for the fakeshop products app.
    │   ├── forms.py              # Consumer Django forms for the products live form-mutation surface (spec-038 Slice 4).
    │   ├── models.py             # Faker-shaped product catalog.
    │   ├── orders.py             # OrderSet declarations for the fakeshop products app.
    │   ├── schema.py             # GraphQL schema for the fakeshop products app.
    │   ├── serializers.py        # DRF serializers for the products live serializer-mutation surface (spec-039 Slice 3).
    │   ├── services.py           # Dynamic data seeding service using Faker providers.
    │   ├── management/    # Management-command namespace for products data and user fixtures.
    │   │   └── commands/    # Django management commands for products fixture setup and teardown.
    │   │       ├── create_users.py  # Create permission-shaped products test users for admin and API access checks.
    │   │       ├── delete_data.py  # Delete seeded products catalog rows by count, item scope, or full catalog scope.
    │   │       ├── delete_users.py  # Delete generated products test users without touching superusers.
    │   │       ├── seed_data.py  # Seed Faker-backed products catalog rows up to a requested per-provider count.
    │   │       └── seed_shards.py  # Prepare the secondary shard SQLite DB for multi-DB products coverage.
    │   └── tests/    # Non-live app tests for products admin, commands, models, schema, and services.
    │       ├── conftest.py       # Shared fixtures for the in-process ``apps.products`` schema tests.
    │       ├── test_admin.py     # Products admin tests for changelist query-param branches.
    │       ├── test_commands.py  # Products command tests for service-backed seed and delete management commands.
    │       ├── test_models.py    # Products model tests for example-domain __str__ implementations.
    │       ├── test_schema.py    # Products schema tests for in-process GraphQL execution without HTTP.
    │       └── test_services.py  # Products service tests for Faker-driven seed_data, create_users, and delete_data.
    └── scalars/    # Scalars app modeling converter specimens for wire-format and filter coverage.
```

### App roles

Each app owns a focused example surface: products for catalog data and seed tooling, library for deeper relation graphs, scalars for converter coverage, and kanban/glossary for repository docs rendered from database rows.

The namespace stays intentionally concrete: every app contributes real Django models, schema objects, and tests that exercise django-strawberry-framework through project configuration instead of synthetic package-only fixtures.

`apps.glossary/`

It backs the exported ``docs/GLOSSARY.md`` file and keeps term aliases, categories, relationships, and spec mentions queryable through the same GraphQL surface used by the markdown exporter.

It also ties completed design specs back to the board: spec companion CSVs become ``GlossarySpecMention`` rows, and done-card glossary links are reconciled so rendered documentation, kanban metadata, and GraphQL API reads describe the same vocabulary.

Management commands:
- `manage.py import_spec_terms` - Import spec companion CSVs into glossary mentions and done-card links.

`apps.kanban/`

It is the database source for the root ``KANBAN.md`` export, including card ordering, dependency integrity, release targeting, glossary links, and reusable prose sections shared with other docs-as-data exporters.

It owns the board invariants rather than leaving them in importer scripts: card numbers, status placement, dependency edges, dependency prose, card references, and reusable BoardDoc prose are validated in app services/signals so every entry point behaves the same way.

Management commands:
- `manage.py import_card_changed_files` - Replace kanban card changed-file links.
- `manage.py import_card_predicted_files` - Replace kanban card predicted-path links.

`apps.library/`

It is the primary relational acceptance surface: live GraphQL tests use it to prove foreign keys, reverse relations, one-to-one links, many-to-many joins, Relay nodes, optimizer hints, consumer queryset shaping, and BigInt round-tripping.

It deliberately stays service-free: tests create rows inline so relation behavior, queryset planning, and computed fields remain visible without a fixture abstraction hiding the model graph being exercised.

`apps.products/`

It carries Category, Item, Property, and Entry data plus Faker-backed services, management commands, admin shortcuts, and filter/order sidecars for a practical catalog-style GraphQL schema.

It is the operational fixture app: services and management commands create users, seed/delete catalog rows, and prepare sharded data, while admin and schema tests prove those same paths work both in-process and through live GraphQL HTTP.

Management commands:
- `manage.py create_users` - Create permission-shaped products test users for admin and API access checks.
- `manage.py delete_data` - Delete seeded products catalog rows by count, item scope, or full catalog scope.
- `manage.py delete_users` - Delete generated products test users without touching superusers.
- `manage.py seed_data` - Seed Faker-backed products catalog rows up to a requested per-provider count.
- `manage.py seed_shards` - Prepare the secondary shard SQLite DB for multi-DB products coverage.

`apps.scalars/`

It provides nullable and non-null scalar fixtures, relation edges, and override cases that let live GraphQL tests pin scalar conversion, serialization, filtering, and schema introspection behavior.

It keeps scalar edge cases isolated from richer domain fixtures so converter behavior can be tested directly, then rechecked through live query filters and GraphQL response serialization without catalog or library model noise.

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
