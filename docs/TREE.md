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
├── apps.py                       # Django ``AppConfig`` - registers the package and applies its upstream patches at app load.
├── conf.py                       # Package settings, read from the host project's ``DJANGO_STRAWBERRY_FRAMEWORK`` dict.
├── connection.py                 # ``DjangoConnection[T]`` + ``DjangoConnectionField`` - the Relay cursor-pagination surface.
├── exceptions.py                 # Exceptions raised by django-strawberry-framework.
├── keyset.py                     # Keyset (value-encoded) stable cursors - the ``Meta.cursor_field`` opt-in.
├── list_field.py                 # ``DjangoListField`` - non-Relay ``list[T]`` field for root Query fields.
├── permissions.py                # Call-time cascade visibility: ``apply_cascade_permissions`` (sync + async).
├── py.typed
├── registry.py                   # Registry for ``DjangoType`` metadata, pending relations, choice enums, and subsystem lifecycles.
├── relay.py                      # Root Relay refetch fields - ``DjangoNodeField`` / ``DjangoNodesField``.
├── routers.py                    # Channels ASGI router: GraphQL on HTTP + WebSocket in one import (spec-041).
├── scalars.py                    # Public GraphQL scalars + the ``strawberry_config()`` schema-config factory.
├── schema.py                     # ``DjangoSchema`` - the schema whose mutation transactions span response completion.
├── sets_mixins.py                # Mixins and lifecycle machinery shared by the ``FilterSet`` and ``OrderSet`` families.
├── auth/    # Opt-in session-auth field factories (spec-040).
│   ├── mutations.py              # Session-auth mutation factories + the phase-2.5 auth bind (spec-040).
│   └── queries.py                # The ``current_user()`` query-field factory + its return-alias namespace (spec-040).
├── extensions/    # Strawberry schema extensions supplied by django-strawberry-framework.
│   └── debug.py                  # ``DjangoDebugExtension`` - Django query-log SQL and execution exceptions in the response.
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
│       ├── _imports.py           # Import helpers that translate bad management-command paths to ``CommandError``.
│       ├── export_schema.py      # manage.py export_schema - print or write the GraphQL SDL for a Strawberry schema symbol.
│       └── inspect_django_type.py  # manage.py inspect_django_type - print a DjangoType's per-field GraphQL resolution table.
├── middleware/    # Django HTTP middleware integrations for django-strawberry-framework.
│   └── debug_toolbar.py          # Debug-toolbar middleware exposing panels for Strawberry Django GraphQL views.
├── mutations/    # Mutations subsystem - the write side (spec-036).
│   ├── fields.py                 # ``DjangoMutationField`` - the write-side field factory (spec-036 Slice 3).
│   ├── inputs.py                 # Generated mutation-input namespace, the public ``FieldError`` envelope, and the payload wrapper.
│   ├── permissions.py            # Shared mutation authorization: permission execution, model permissions, and model-less deny-by-default.
│   ├── resolvers.py              # The sync + async create / update / delete write pipeline (spec-036 Slice 3).
│   └── sets.py                   # ``DjangoMutation`` base + metaclass + ``Meta`` validation + the phase-2.5 bind (spec-036 Slice 2).
├── optimizer/    # Optimizer subsystem - selection-driven queryset planning via ``DjangoOptimizerExtension`` (N+1 prevention).
│   ├── _context.py               # Shared context read/write helpers for optimizer <-> resolver hand-off.
│   ├── extension.py              # ``DjangoOptimizerExtension`` - Strawberry schema extension solving N+1 via queryset plans.
│   ├── field_meta.py             # ``FieldMeta`` - precomputed Django field metadata for the optimizer walker.
│   ├── hints.py                  # ``OptimizerHint`` - typed wrapper for ``Meta.optimizer_hints`` values.
│   ├── join_taxonomy.py          # Parent/child join-condition taxonomy for nested-connection fetch planning.
│   ├── lateral_fetch.py          # Postgres ``CROSS JOIN LATERAL`` fetch strategy for nested connections.
│   ├── nested_fetch.py           # Pluggable nested-connection fetch strategies (the Prisma-style seam).
│   ├── nested_planner.py         # Transactional planner for nested Relay connection selections.
│   ├── plans.py                  # ``OptimizationPlan`` - the shape the walker emits and the extension consumes.
│   ├── selections.py             # Selection-tree traversal substrate - the AST and converted-selection adapters.
│   ├── single_parent_fetch.py    # Runtime single-parent degenerate fast path for the windowed nested prefetch.
│   └── walker.py                 # Selection walker that delegates nested Relay connections to their private planner.
├── orders/    # Ordering subsystem - declarative ``OrderSet`` classes that become GraphQL ``orderBy:`` arguments.
│   ├── base.py                   # ``RelatedOrder`` - the nested-path ordering primitive.
│   ├── factories.py              # Order input-class BFS factory; dynamic ``OrderSet`` generation is deferred.
│   ├── inputs.py                 # Order input namespace, direction enum, and input-data adapters.
│   └── sets.py                   # ``OrderSet`` + ``OrderSetMetaclass`` - declaration, validation, and the apply pipeline.
├── rest_framework/    # DRF serializer mutations: generated inputs, conversion, binding, and execution behind an import guard.
│   ├── hook_context.py           # The frozen serializer-hook context + upload metadata (the hardening pass).
│   ├── inputs.py                 # DRF-serializer-derived ``@strawberry.input`` generation substrate (spec-039 Slice 1).
│   ├── resolvers.py              # The sync + async serializer-mutation resolver pipeline (spec-039 Slice 3).
│   ├── serializer_converter.py   # DRF serializer-field -> Strawberry input conversion + the per-input-field reverse map (spec-039).
│   └── sets.py                   # The ``SerializerMutation`` base + ``Meta`` validation + the phase-2.5 bind (spec-039 Slice 2).
├── templates/
│   └── django_strawberry_framework/
│       └── debug_toolbar.html
├── testing/    # Consumer test utilities for GraphQL clients, connection wrapping, and Relay GlobalID helpers.
│   ├── _wrap.py                  # Cooperative connection-method wrapping for consumer test instrumentation.
│   ├── client.py                 # Consumer-facing GraphQL test client family - live HTTP test ergonomics (spec-043).
│   └── relay.py                  # Public Relay test helpers - ``global_id_for`` / ``decode_global_id``.
├── types/    # Type-system subsystem - ``DjangoType``, field/relation conversion, Relay integration, and finalization.
│   ├── base.py                   # ``DjangoType`` - Meta-class-driven Django-model-to-Strawberry-type adapter.
│   ├── converters.py             # Convert Django model fields to Strawberry-compatible Python types.
│   ├── definition.py             # ``DjangoTypeDefinition`` - canonical metadata for collected ``DjangoType`` classes.
│   ├── finalizer.py              # ``finalize_django_types()`` - the once-only finalization gate for collected ``DjangoType`` classes.
│   ├── relations.py              # Pending relation records for definition-order-independent ``DjangoType`` finalization.
│   ├── relay.py                  # Internal Relay helpers - interface injection, node resolver defaults, and GlobalID strategies.
│   └── resolvers.py              # Generated relation and file-field resolvers for finalized ``DjangoType`` classes.
└── utils/    # Cross-cutting infrastructure shared across django-strawberry-framework subsystems.
    ├── connections.py            # Shared connection contracts for sidecars, fetch modes, offset/keyset windows, and pagination bounds.
    ├── converters.py             # Fail-loud converter-dispatch skeleton shared by the form + serializer converters (spec-039 P1.4).
    ├── errors.py                 # Neutral ``FieldError`` / write-error constructors shared by every write flavor.
    ├── imports.py                # Import helpers for best-effort, loaded-only, strict, and guarded optional-dependency lookups.
    ├── input_values.py           # Set-input traversal substrate shared by the FilterSet and OrderSet families.
    ├── inputs.py                 # Generated-input construction and lifecycle primitives shared by set and write families.
    ├── permissions.py            # Shared permission traversal and Django/Channels request-context decoding.
    ├── querysets.py              # Shared query-source, field-coercion, sync/async hook, and visibility contracts.
    ├── relations.py              # Relation-shape helpers shared by converters, resolvers, and the optimizer.
    ├── strings.py                # GraphQL/Django naming helpers for case conversion and lookup-path flattening.
    ├── typing.py                 # Async-callable detection and type-unwrapping helpers for Strawberry, Python, and GraphQL types.
    ├── write_transaction.py      # Write-transaction plumbing: the managed alias, alias pinning, row locks, and conflicts.
    └── write_values.py           # Neutral write-value primitives shared by the model, form, and serializer flavors.
```

## django_strawberry_framework (target package layout)

The current package tree merged with every not-yet-existing path linked from a WIP/TODO card in [`KANBAN.md`](../KANBAN.md). Each planned entry names the card that introduces it; backlog cards and DONE-card historical paths are ignored.

Source: `django_strawberry_framework/ (+ planned card paths)`

```text
django_strawberry_framework/    # Public API of django-strawberry-framework, a DRF-inspired Django integration for Strawberry GraphQL.
├── _cross_web_patches.py         # Defensive patches for upstream ``cross_web`` bugs, applied at app load.
├── _django_patches.py            # Defensive patches for upstream Django bugs, applied at app load.
├── _strawberry_patches.py        # Defensive patches for upstream Strawberry bugs, applied at app load.
├── apps.py                       # Django ``AppConfig`` - registers the package and applies its upstream patches at app load.
├── conf.py                       # Package settings, read from the host project's ``DJANGO_STRAWBERRY_FRAMEWORK`` dict.
├── connection.py                 # ``DjangoConnection[T]`` + ``DjangoConnectionField`` - the Relay cursor-pagination surface.
├── exceptions.py                 # Exceptions raised by django-strawberry-framework.
├── keyset.py                     # Keyset (value-encoded) stable cursors - the ``Meta.cursor_field`` opt-in.
├── list_field.py                 # ``DjangoListField`` - non-Relay ``list[T]`` field for root Query fields.
├── py.typed
├── registry.py                   # Registry for ``DjangoType`` metadata, pending relations, choice enums, and subsystem lifecycles.
├── relay.py                      # Root Relay refetch fields - ``DjangoNodeField`` / ``DjangoNodesField``.
├── routers.py                    # Channels ASGI router: GraphQL on HTTP + WebSocket in one import (spec-041).
├── scalars.py                    # Public GraphQL scalars + the ``strawberry_config()`` schema-config factory.
├── schema.py                     # ``DjangoSchema`` - the schema whose mutation transactions span response completion.
├── sets_mixins.py                # Mixins and lifecycle machinery shared by the ``FilterSet`` and ``OrderSet`` families.
├── aggregates/    # planned by TODO-BETA-051-0.1.3 - Declarative AggregateSet output types with related, permissioned, selection-aware sync/async statistics.
├── auth/    # Opt-in session-auth field factories (spec-040).
│   ├── mutations.py              # Session-auth mutation factories + the phase-2.5 auth bind (spec-040).
│   └── queries.py                # The ``current_user()`` query-field factory + its return-alias namespace (spec-040).
├── extensions/    # Strawberry schema extensions supplied by django-strawberry-framework.
│   └── debug.py                  # ``DjangoDebugExtension`` - Django query-log SQL and execution exceptions in the response.
├── fieldset/    # planned by TODO-BETA-048-0.1.1 - FieldSet computed fields, resolver overrides, field permissions, and optimizer dependencies.
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
│       ├── _imports.py           # Import helpers that translate bad management-command paths to ``CommandError``.
│       ├── export_schema.py      # manage.py export_schema - print or write the GraphQL SDL for a Strawberry schema symbol.
│       └── inspect_django_type.py  # manage.py inspect_django_type - print a DjangoType's per-field GraphQL resolution table.
├── middleware/    # Django HTTP middleware integrations for django-strawberry-framework.
│   └── debug_toolbar.py          # Debug-toolbar middleware exposing panels for Strawberry Django GraphQL views.
├── mutations/    # Mutations subsystem - the write side (spec-036).
│   ├── fields.py                 # ``DjangoMutationField`` - the write-side field factory (spec-036 Slice 3).
│   ├── inputs.py                 # Generated mutation-input namespace, the public ``FieldError`` envelope, and the payload wrapper.
│   ├── permissions.py            # Shared mutation authorization: permission execution, model permissions, and model-less deny-by-default.
│   ├── resolvers.py              # The sync + async create / update / delete write pipeline (spec-036 Slice 3).
│   └── sets.py                   # ``DjangoMutation`` base + metaclass + ``Meta`` validation + the phase-2.5 bind (spec-036 Slice 2).
├── optimizer/    # Optimizer subsystem - selection-driven queryset planning via ``DjangoOptimizerExtension`` (N+1 prevention).
│   ├── _context.py               # Shared context read/write helpers for optimizer <-> resolver hand-off.
│   ├── extension.py              # ``DjangoOptimizerExtension`` - Strawberry schema extension solving N+1 via queryset plans.
│   ├── field_meta.py             # ``FieldMeta`` - precomputed Django field metadata for the optimizer walker.
│   ├── hints.py                  # ``OptimizerHint`` - typed wrapper for ``Meta.optimizer_hints`` values.
│   ├── join_taxonomy.py          # Parent/child join-condition taxonomy for nested-connection fetch planning.
│   ├── lateral_fetch.py          # Postgres ``CROSS JOIN LATERAL`` fetch strategy for nested connections.
│   ├── nested_fetch.py           # Pluggable nested-connection fetch strategies (the Prisma-style seam).
│   ├── nested_planner.py         # Transactional planner for nested Relay connection selections.
│   ├── plans.py                  # ``OptimizationPlan`` - the shape the walker emits and the extension consumes.
│   ├── selections.py             # Selection-tree traversal substrate - the AST and converted-selection adapters.
│   ├── single_parent_fetch.py    # Runtime single-parent degenerate fast path for the windowed nested prefetch.
│   └── walker.py                 # Selection walker that delegates nested Relay connections to their private planner.
├── orders/    # Ordering subsystem - declarative ``OrderSet`` classes that become GraphQL ``orderBy:`` arguments.
│   ├── base.py                   # ``RelatedOrder`` - the nested-path ordering primitive.
│   ├── factories.py              # Order input-class BFS factory; dynamic ``OrderSet`` generation is deferred.
│   ├── inputs.py                 # Order input namespace, direction enum, and input-data adapters.
│   └── sets.py                   # ``OrderSet`` + ``OrderSetMetaclass`` - declaration, validation, and the apply pipeline.
├── permissions/    # planned by TODO-BETA-053-0.1.4 - Cascade-permission package migration plus opt-in node-sentinel redaction (``Meta.redaction_mode``).
├── rest_framework/    # DRF serializer mutations: generated inputs, conversion, binding, and execution behind an import guard.
│   ├── hook_context.py           # The frozen serializer-hook context + upload metadata (the hardening pass).
│   ├── inputs.py                 # DRF-serializer-derived ``@strawberry.input`` generation substrate (spec-039 Slice 1).
│   ├── resolvers.py              # The sync + async serializer-mutation resolver pipeline (spec-039 Slice 3).
│   ├── serializer_converter.py   # DRF serializer-field -> Strawberry input conversion + the per-input-field reverse map (spec-039).
│   └── sets.py                   # The ``SerializerMutation`` base + ``Meta`` validation + the phase-2.5 bind (spec-039 Slice 2).
├── templates/
│   └── django_strawberry_framework/
│       └── debug_toolbar.html
├── testing/    # Consumer test utilities for GraphQL clients, connection wrapping, and Relay GlobalID helpers.
│   ├── _wrap.py                  # Cooperative connection-method wrapping for consumer test instrumentation.
│   ├── client.py                 # Consumer-facing GraphQL test client family - live HTTP test ergonomics (spec-043).
│   └── relay.py                  # Public Relay test helpers - ``global_id_for`` / ``decode_global_id``.
├── types/    # Type-system subsystem - ``DjangoType``, field/relation conversion, Relay integration, and finalization.
│   ├── base.py                   # ``DjangoType`` - Meta-class-driven Django-model-to-Strawberry-type adapter.
│   ├── converters.py             # Convert Django model fields to Strawberry-compatible Python types.
│   ├── definition.py             # ``DjangoTypeDefinition`` - canonical metadata for collected ``DjangoType`` classes.
│   ├── finalizer.py              # ``finalize_django_types()`` - the once-only finalization gate for collected ``DjangoType`` classes.
│   ├── relations.py              # Pending relation records for definition-order-independent ``DjangoType`` finalization.
│   ├── relay.py                  # Internal Relay helpers - interface injection, node resolver defaults, and GlobalID strategies.
│   └── resolvers.py              # Generated relation and file-field resolvers for finalized ``DjangoType`` classes.
└── utils/    # Cross-cutting infrastructure shared across django-strawberry-framework subsystems.
    ├── connections.py            # Shared connection contracts for sidecars, fetch modes, offset/keyset windows, and pagination bounds.
    ├── converters.py             # Fail-loud converter-dispatch skeleton shared by the form + serializer converters (spec-039 P1.4).
    ├── errors.py                 # Neutral ``FieldError`` / write-error constructors shared by every write flavor.
    ├── imports.py                # Import helpers for best-effort, loaded-only, strict, and guarded optional-dependency lookups.
    ├── input_values.py           # Set-input traversal substrate shared by the FilterSet and OrderSet families.
    ├── inputs.py                 # Generated-input construction and lifecycle primitives shared by set and write families.
    ├── permissions.py            # Shared permission traversal and Django/Channels request-context decoding.
    ├── querysets.py              # Shared query-source, field-coercion, sync/async hook, and visibility contracts.
    ├── relations.py              # Relation-shape helpers shared by converters, resolvers, and the optimizer.
    ├── strings.py                # GraphQL/Django naming helpers for case conversion and lookup-path flattening.
    ├── typing.py                 # Async-callable detection and type-unwrapping helpers for Strawberry, Python, and GraphQL types.
    ├── write_transaction.py      # Write-transaction plumbing: the managed alias, alias pinning, row locks, and conflicts.
    └── write_values.py           # Neutral write-value primitives shared by the model, form, and serializer flavors.
```


## Test layout

Tests live in four deliberate places, each chosen by what the test is proving. The root `tests/` tree protects package internals and repository tooling; its subsystem directories broadly mirror `django_strawberry_framework/`. `examples/fakeshop/apps/<app>/tests/` protects one Django app at a time without live HTTP. `examples/fakeshop/tests/` protects project-level fakeshop behavior that belongs to no single app. `examples/fakeshop/test_query/` is the live `/graphql/` acceptance surface.

**Coverage priority.** If a package line can be covered by a real fakeshop GraphQL request, put that test in `examples/fakeshop/test_query/`. Use the non-live fakeshop trees for services, models, admin, commands, URLs, or in-process schema execution. Use root `tests/` for repository tooling, package internals, invalid configuration, registry/finalizer mechanics, and paths unreachable through a realistic GraphQL request. Mock only when the real path is impossible. These placement rules are pinned in [`AGENTS.md`][agents].

### Current test trees

Source: `tests/`

```text
tests/    # Package, integration, and repository-tool tests for django_strawberry_framework.
├── _soft_dependency.py           # Shared soft-dependency absence simulation for the optional-import guards.
├── conftest.py                   # Shared pytest fixtures and test-suite instrumentation.
├── test_apps.py                  # AppConfig tests for package registration and upstream patch dispatch.
├── test_bug_hunt.py              # Focused tests for the autonomous bug-hunt progress generator.
├── test_build_kanban_html.py     # Tests for KANBAN version-tuple parsing edge cases.
├── test_build_tree_md.py         # Tests for TREE renderer planned descriptions, replacements, and source discovery.
├── test_clean_up.py              # Script tests for clean_up generated-artifact deletion boundaries.
├── test_connection.py            # DjangoConnection tests for generated types, fields, resolvers, sidecars, optimization, and pagination.
├── test_cross_web_patches.py     # Tests for the ``cross_web`` non-UTF-8 request-body patch.
├── test_django_patches.py        # Django patch tests for DB connection wrapping and multi-database safety.
├── test_exceptions.py            # Exception hierarchy: inheritance, GraphQL translation, hostile message args.
├── test_export_dry_review.py     # Focused tests for the standalone DRY review toolkit.
├── test_keyset.py                # Package-side keyset-cursor tests: codec, bounds, window shapes, lateral seek.
├── test_keyset_connection.py     # Keyset connection tests for resolve routing, slicer guards, order state, and nested-planner helpers.
├── test_lateral_pg_parity.py     # Postgres lateral-fetch tests for parity, SQL shape, cleanup, custom joins, adaptation, and index seeks.
├── test_list_field.py            # DjangoListField tests for validation, resolvers, visibility, optimization, sidecars, and permissions.
├── test_permissions.py           # Cascade-permission tests - ``apply_cascade_permissions`` / ``aapply_cascade_permissions``.
├── test_registry.py              # TypeRegistry and finalization tests for lookups, primaries, lifecycle callbacks, retries, and reset.
├── test_relay_connection.py      # Relation-as-Connection tests for synthesis, pagination, optimized windows, fallbacks, and cleanup.
├── test_relay_node_field.py      # Root Relay refetch tests for DjangoNodeField and DjangoNodesField.
├── test_routers.py               # Channels router tests for HTTP/WebSocket routing, wrappers, lazy imports, and request context.
├── test_scalars.py               # Scalar tests for BigInt, Upload, and the framework StrawberryConfig helper.
├── test_strawberry_patches.py    # Tests for the Strawberry request-body patch.
├── auth/    # Package-internal tests for the opt-in auth subsystem (spec-040).
│   ├── test_mutations.py         # Auth mutation tests for declaration and bind lifecycles, operations, registration, and permissions.
│   └── test_queries.py           # Current-user query tests for alias binding, visibility, permission gates, and sync/async resolution.
├── base/    # Frozen base tests for settings, initialization, version, logging, and public exports.
│   ├── test_conf.py              # Package settings-reader tests for DJANGO_STRAWBERRY_FRAMEWORK.
│   └── test_init.py              # Package init tests for version metadata and public exports.
├── extensions/    # Tests for package Strawberry schema extensions.
│   └── test_debug.py             # DjangoDebugExtension tests for payload serialization, SQL capture, errors, and execution isolation.
├── filters/    # Package tests for the FilterSet subsystem.
│   ├── test_base.py              # Filter primitive tests for typed, list, range, global-ID, and related filters.
│   ├── test_factories.py         # FilterArgumentsFactory tests for BFS input generation and dynamic FilterSet caching.
│   ├── test_finalizer.py         # Finalizer tests for filter binding, owner-aware materialization, and orphan validation.
│   ├── test_inputs.py            # Filter input-generation tests for lookup naming, field construction, normalization, references, and reset.
│   ├── test_sets.py              # FilterSet tests for Meta validation, relations, Relay fields, permissions, visibility, and logic trees.
│   └── fixtures/    # Fixture modules for filter lazy resolution and cyclic input-generation tests.
│       └── filtersets.py         # Fixture FilterSet declarations for cross-module lazy resolution and self-referential cycle handling.
├── forms/    # Package tests for form conversion, generated inputs, and form-backed mutation behavior (spec-038).
│   ├── test_converter.py         # Converter tests for the form-field -> Strawberry annotation registry (spec-038 Slice 1).
│   ├── test_inputs.py            # Form-derived input tests for the generated ``<FormClass>Input`` / ``PartialInput`` (spec-038).
│   ├── test_resolvers.py         # Form-mutation resolver-pipeline tests (spec-038 Slice 3).
│   └── test_sets.py              # ``DjangoFormMutation`` / ``DjangoModelFormMutation`` bases, ``Meta`` validation, and the bind (spec-038 Slice 2).
├── management/    # Package tests for django-strawberry-framework management commands.
│   ├── test_export_schema.py     # Management command tests for export_schema selector errors, schema validation, and CLI contracts.
│   ├── test_imports.py           # Tests for management-command import error translation and path validation.
│   └── test_inspect_django_type.py  # Management command tests for inspect_django_type field-resolution tables.
├── middleware/    # Tests for package Django middleware integrations.
│   └── test_debug_toolbar.py     # DebugToolbarMiddleware tests for import guards, payload injection, response rewriting, and templates.
├── mutations/    # Package tests for the mutations subsystem (DjangoMutation + generated inputs).
│   ├── test_fields.py            # ``DjangoMutationField`` factory tests (spec-036 Slice 3).
│   ├── test_inputs.py            # Mutation input tests for generated Input/PartialInput, FieldError, and the payload wrapper.
│   ├── test_permissions.py       # ``DjangoModelPermission`` class behavior + write-auth enforcement (spec-036 Slice 2 + Slice 3).
│   ├── test_resolvers.py         # Write-pipeline resolver tests (spec-036 Slice 3).
│   ├── test_sets.py              # ``DjangoMutation`` base, ``Meta`` validation, registration, and the phase-2.5 bind.
│   └── test_write_transaction.py # The BETA-055 write-transaction contract (``DjangoSchema`` + ``utils/write_transaction.py``).
├── optimizer/    # Package tests for optimizer plans, application, extensions, selections, and nested-fetch strategies.
│   ├── _builders.py              # Shared builders for the optimizer test package.
│   ├── test_definition_order.py  # Optimizer tests for definition-order-independent DjangoType relation graphs.
│   ├── test_extension.py         # DjangoOptimizerExtension tests for gating, caching, strictness, schema audit, context, and querysets.
│   ├── test_field_meta.py        # FieldMeta tests for precomputed relation metadata used by optimizer planning.
│   ├── test_hints.py             # OptimizerHint tests for Meta.optimizer_hints normalization and validation.
│   ├── test_join_taxonomy.py     # Tests for the join-condition taxonomy (``optimizer/join_taxonomy.py``).
│   ├── test_lateral_fetch.py     # Tests for the Postgres lateral fetch strategy (``optimizer/lateral_fetch.py``).
│   ├── test_multi_db.py          # Optimizer-plan tests for multi-database cooperation and DB-alias preservation.
│   ├── test_nested_fetch.py      # Tests for the nested-connection fetch-strategy seam (``optimizer/nested_fetch.py``).
│   ├── test_nested_index_advisory.py  # Composite-index advisory unit matrix (optimizer-improvement-plan WS-D D2).
│   ├── test_plans.py             # OptimizationPlan tests for lifecycle, ORM reconciliation, paths, ordering, and window pagination.
│   ├── test_relay_id_projection.py  # Optimizer tests for Relay GlobalID projection and connector-column invariants.
│   ├── test_selections.py        # Tests for the selection-traversal substrate (``optimizer/selections.py``).
│   ├── test_single_parent_fetch.py  # Tests for the single-parent window fast path (``optimizer/single_parent_fetch.py``).
│   └── test_walker.py            # Selection-walker tests for GraphQL selection to ORM OptimizationPlan conversion.
├── orders/    # Package tests for the OrderSet subsystem.
│   ├── test_base.py              # RelatedOrder binding and lazy-resolution tests plus Meta.orderset_class promotion and validation.
│   ├── test_composition.py       # Filter and order composition smoke tests for Layer-3 read-side integration.
│   ├── test_factories.py         # OrderArgumentsFactory tests for BFS generation, annotations, caching, idempotency, and validation.
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
│   ├── test_client.py            # DB-free test-client tests for endpoints, multipart bodies, responses, mixin assertions, and exports.
│   ├── test_relay.py             # Public Relay helper tests for global_id_for and decode_global_id.
│   └── test_wrap.py              # Connection-method wrapping tests for cooperative consumer instrumentation.
├── types/    # Package tests for the DjangoType subsystem.
│   ├── test_base.py              # DjangoType tests for Meta validation, scalar mapping, relations, registry, and get_queryset.
│   ├── test_converters.py        # Converter tests for scalars, enums, relations, PostgreSQL containers, and file/image output objects.
│   ├── test_definition_order.py  # Acceptance tests for definition-order-independent DjangoType relation finalization.
│   ├── test_definition_order_schema.py  # Schema-build tests for definition-order-independent DjangoType finalization.
│   ├── test_definition_relations.py  # DjangoTypeDefinition tests for related-target lookup and custom Relay ID-resolver detection.
│   ├── test_generic_foreign_key.py  # DjangoType tests for GenericForeignKey rejection and GenericRelation support.
│   ├── test_relations.py         # PendingRelation tests for identity hashing and dataclass field contracts.
│   ├── test_relay_interfaces.py  # DjangoType Relay interface tests for Node wiring and resolver contracts.
│   ├── test_resolvers.py         # Relation resolver tests for cardinality, FK-ID elision, N+1 strictness, and multi-database routing.
│   └── fixtures/    # Fixture modules for cross-module DjangoType resolution tests.
│       ├── branch_module.py      # Cross-module fixture declaring BranchType and BranchFilter together.
│       └── shelf_module.py       # Cross-module fixture declaring ShelfType and ShelfFilter together.
└── utils/    # Package tests for shared utility helpers.
    ├── test_connections.py       # Unit tests for the shared connection planner/resolver contracts.
    ├── test_converters.py        # Tests for the shared fail-loud converter-dispatch skeleton (``utils/converters.py``, spec-039 P1.4).
    ├── test_imports.py           # Tests for the shared optional-import helpers (``utils/imports.py``, spec-041 Slice 1).
    ├── test_input_values.py      # Tests for the neutral set-input traversal substrate (``utils/input_values.py``).
    ├── test_inputs.py            # Tests for the shared generated-input substrate (``utils/inputs.py``).
    ├── test_permissions.py       # Tests for input permissions, relation-path gates, and Django/Channels request decoding.
    ├── test_querysets.py         # Tests for the shared query-source / visibility substrate (``utils/querysets.py``).
    ├── test_relations.py         # Relation utility tests for kinds, many-side detection, instance accessors, and package re-exports.
    ├── test_strings.py           # String utility tests for snake/camel/Pascal case conversion and Django lookup-path flattening.
    ├── test_typing.py            # Typing utility tests for async-callable detection and Strawberry, Python, and GraphQL unwrapping.
    └── test_write_values.py      # Tests for the shared write-value decoding substrate.
```


Source: `examples/fakeshop/apps/*/tests/`

```text
examples/fakeshop/apps/    # Per-Django-app, non-live tests that stay beside the app they protect.
├── glossary/
│   └── tests/    # Non-live app tests for glossary models, factories, and import commands.
│       ├── test_factories.py     # Glossary factory tests for canonical reuse, unique identities, overrides, and relationships.
│       ├── test_import_spec_terms.py  # Glossary import command tests for DONE-card spec term extraction.
│       └── test_models.py        # Glossary model tests for term edges, aliases, categories, and spec mentions.
├── kanban/
│   └── tests/    # Non-live app tests for kanban commands, services, signals, and board invariants.
│       ├── test_commands.py      # Kanban command tests for the merged import_card_files workflow (and aliases).
│       ├── test_mutations.py     # In-process wiring + error-mapping tests for the kanban GraphQL mutation surface (WS-3B).
│       ├── test_services.py      # Kanban service tests for card resolution, creation, tracked paths, validation, and rollback.
│       ├── test_services_gaps.py # Service-layer gap coverage for branches the main service suite leaves open.
│       ├── test_signals.py       # Kanban signal tests for dependencies, done-card guards, blocking, and ordering.
│       ├── test_uuid.py          # Tests for the UUID side-table wiring and its one-hot link constraint.
│       └── test_worklog.py       # Tests for the Phase 2 work-tracking dimension.
├── library/
│   └── tests/    # Non-live app tests for library models, schema exposure, and declaration-order invariants.
│       ├── test_generic_connection.py  # In-process windowed GenericRelation connection acceptance tests (WS-B).
│       ├── test_generic_connection_sharded.py  # Sharded (``FAKESHOP_SHARDED=1``) GenericRelation connection alias-late morph test.
│       ├── test_models.py        # Library model tests for string rendering, relation traversal, and per-shelf title uniqueness.
│       └── test_schema.py        # Library schema tests for project-schema exposure and declaration-order invariants without HTTP.
├── products/
│   └── tests/    # Non-live app tests for products admin, commands, models, schema, and services.
│       ├── conftest.py           # Shared fixtures for the in-process ``apps.products`` schema tests.
│       ├── test_admin.py         # Products admin tests for changelist query-param branches.
│       ├── test_commands.py      # Products command tests for catalog/user lifecycle and shard seeding.
│       ├── test_models.py        # Products model tests for example-domain __str__ implementations.
│       ├── test_schema.py        # Products schema tests for in-process GraphQL execution without HTTP.
│       └── test_services.py      # Products service tests for Faker discovery, catalog lifecycle, and user lifecycle.
└── scalars/
    └── tests/    # Non-live app tests for scalar substrate models.
        └── test_models.py        # Scalars model tests for string rendering, relation traversal, and tag-label uniqueness.
```


Source: `examples/fakeshop/tests/`

```text
examples/fakeshop/tests/    # Project/config-level fakeshop tests that belong to no single app and do not use live /graphql HTTP.
├── test_export_schema.py         # Fakeshop project command tests for export_schema against the configured schema.
├── test_inspect_django_type.py   # Fakeshop project command tests for inspect_django_type against example DjangoTypes.
└── test_urls.py                  # Fakeshop project URL tests for the index view and URL configuration.
```


Source: `examples/fakeshop/test_query/`

```text
examples/fakeshop/test_query/    # Live GraphQL HTTP tests for fakeshop's consumer-visible API.
├── README.md                     # Guide to the fakeshop live GraphQL HTTP acceptance-test tier and its isolation contract.
├── conftest.py                   # Shared fixtures for the fakeshop acceptance (live ``/graphql/``) suites.
├── test_auth_api.py              # Live ``/graphql/`` auth API acceptance tests (spec-040).
├── test_client_api.py            # Live GraphQL HTTP acceptance tests for the spec-043 test-client family.
├── test_debug_extension_api.py   # Live GraphQL HTTP tests for ``DjangoDebugExtension`` (spec-044 Test plan 1-7).
├── test_debug_toolbar_api.py     # Live HTTP tests for ``DebugToolbarMiddleware`` across GraphQL, panel, and pass-through routes.
├── test_glossary_api.py          # Live GraphQL HTTP tests for the glossary docs-as-data API.
├── test_kanban_api.py            # Live GraphQL HTTP tests for the kanban board docs-as-data API.
├── test_kanban_mutations_api.py  # Live GraphQL HTTP tests for the kanban write surface (WS-3B).
├── test_keyset_api.py            # Live GraphQL HTTP tests for keyset (``Meta.cursor_field``) cursor pagination.
├── test_library_api.py           # Live GraphQL HTTP tests for the library app's read/write, Relay, keyset, and optimizer surface.
├── test_multi_db.py              # Live GraphQL HTTP tests for sharded resolver isolation and multi-database debug capture.
├── test_mutation_atomicity.py    # Live ``/graphql/`` acceptance for the BETA-055 response-completion transaction contract.
├── test_optimizer_auto_api.py    # Live ``/graphql/`` coverage for routed nested-fetch strategy selection.
├── test_products_api.py          # Live GraphQL HTTP tests for products reads, mutations, permissions, optimization, and request parsing.
├── test_scalars_api.py           # Live GraphQL HTTP tests for scalar wire formats, filtering, relations, and optimizer behavior.
├── test_scalars_filter_api.py    # Live GraphQL HTTP tests for scalar filtering, ordering, and related-queryset behavior.
├── test_single_parent_fastpath_api.py  # Live GraphQL HTTP tests for the single-parent windowed-prefetch fast path.
└── test_uploads_api.py           # Live GraphQL HTTP tests for the spec-037 file/image wire contract.
```


### Target test shape

The current test trees merged with the not-yet-existing test paths linked from WIP/TODO cards, annotated the same way as the target package layout. Test roots without planned additions match their current trees above.

Source: `tests/ (+ planned card paths)`

```text
tests/    # Package, integration, and repository-tool tests for django_strawberry_framework.
├── _soft_dependency.py           # Shared soft-dependency absence simulation for the optional-import guards.
├── conftest.py                   # Shared pytest fixtures and test-suite instrumentation.
├── test_apps.py                  # AppConfig tests for package registration and upstream patch dispatch.
├── test_bug_hunt.py              # Focused tests for the autonomous bug-hunt progress generator.
├── test_build_kanban_html.py     # Tests for KANBAN version-tuple parsing edge cases.
├── test_build_tree_md.py         # Tests for TREE renderer planned descriptions, replacements, and source discovery.
├── test_clean_up.py              # Script tests for clean_up generated-artifact deletion boundaries.
├── test_connection.py            # DjangoConnection tests for generated types, fields, resolvers, sidecars, optimization, and pagination.
├── test_cross_web_patches.py     # Tests for the ``cross_web`` non-UTF-8 request-body patch.
├── test_django_patches.py        # Django patch tests for DB connection wrapping and multi-database safety.
├── test_exceptions.py            # Exception hierarchy: inheritance, GraphQL translation, hostile message args.
├── test_export_dry_review.py     # Focused tests for the standalone DRY review toolkit.
├── test_keyset.py                # Package-side keyset-cursor tests: codec, bounds, window shapes, lateral seek.
├── test_keyset_connection.py     # Keyset connection tests for resolve routing, slicer guards, order state, and nested-planner helpers.
├── test_lateral_pg_parity.py     # Postgres lateral-fetch tests for parity, SQL shape, cleanup, custom joins, adaptation, and index seeks.
├── test_list_field.py            # DjangoListField tests for validation, resolvers, visibility, optimization, sidecars, and permissions.
├── test_permissions.py           # Cascade-permission tests - ``apply_cascade_permissions`` / ``aapply_cascade_permissions``.
├── test_registry.py              # TypeRegistry and finalization tests for lookups, primaries, lifecycle callbacks, retries, and reset.
├── test_relay_connection.py      # Relation-as-Connection tests for synthesis, pagination, optimized windows, fallbacks, and cleanup.
├── test_relay_node_field.py      # Root Relay refetch tests for DjangoNodeField and DjangoNodesField.
├── test_routers.py               # Channels router tests for HTTP/WebSocket routing, wrappers, lazy imports, and request context.
├── test_scalars.py               # Scalar tests for BigInt, Upload, and the framework StrawberryConfig helper.
├── test_strawberry_patches.py    # Tests for the Strawberry request-body patch.
├── auth/    # Package-internal tests for the opt-in auth subsystem (spec-040).
│   ├── test_mutations.py         # Auth mutation tests for declaration and bind lifecycles, operations, registration, and permissions.
│   └── test_queries.py           # Current-user query tests for alias binding, visibility, permission gates, and sync/async resolution.
├── base/    # Frozen base tests for settings, initialization, version, logging, and public exports.
│   ├── test_conf.py              # Package settings-reader tests for DJANGO_STRAWBERRY_FRAMEWORK.
│   └── test_init.py              # Package init tests for version metadata and public exports.
├── extensions/    # Tests for package Strawberry schema extensions.
│   └── test_debug.py             # DjangoDebugExtension tests for payload serialization, SQL capture, errors, and execution isolation.
├── filters/    # Package tests for the FilterSet subsystem.
│   ├── test_base.py              # Filter primitive tests for typed, list, range, global-ID, and related filters.
│   ├── test_factories.py         # FilterArgumentsFactory tests for BFS input generation and dynamic FilterSet caching.
│   ├── test_finalizer.py         # Finalizer tests for filter binding, owner-aware materialization, and orphan validation.
│   ├── test_inputs.py            # Filter input-generation tests for lookup naming, field construction, normalization, references, and reset.
│   ├── test_pg_full_text.py      # planned by TODO-BETA-050-0.1.2 - Postgres full-text search filter primitives
│   ├── test_search_fields.py     # planned by TODO-BETA-049-0.1.2 - `Meta.search_fields` support
│   ├── test_sets.py              # FilterSet tests for Meta validation, relations, Relay fields, permissions, visibility, and logic trees.
│   └── fixtures/    # Fixture modules for filter lazy resolution and cyclic input-generation tests.
│       └── filtersets.py         # Fixture FilterSet declarations for cross-module lazy resolution and self-referential cycle handling.
├── forms/    # Package tests for form conversion, generated inputs, and form-backed mutation behavior (spec-038).
│   ├── test_converter.py         # Converter tests for the form-field -> Strawberry annotation registry (spec-038 Slice 1).
│   ├── test_inputs.py            # Form-derived input tests for the generated ``<FormClass>Input`` / ``PartialInput`` (spec-038).
│   ├── test_resolvers.py         # Form-mutation resolver-pipeline tests (spec-038 Slice 3).
│   └── test_sets.py              # ``DjangoFormMutation`` / ``DjangoModelFormMutation`` bases, ``Meta`` validation, and the bind (spec-038 Slice 2).
├── management/    # Package tests for django-strawberry-framework management commands.
│   ├── test_export_schema.py     # Management command tests for export_schema selector errors, schema validation, and CLI contracts.
│   ├── test_imports.py           # Tests for management-command import error translation and path validation.
│   └── test_inspect_django_type.py  # Management command tests for inspect_django_type field-resolution tables.
├── middleware/    # Tests for package Django middleware integrations.
│   └── test_debug_toolbar.py     # DebugToolbarMiddleware tests for import guards, payload injection, response rewriting, and templates.
├── mutations/    # Package tests for the mutations subsystem (DjangoMutation + generated inputs).
│   ├── test_fields.py            # ``DjangoMutationField`` factory tests (spec-036 Slice 3).
│   ├── test_inputs.py            # Mutation input tests for generated Input/PartialInput, FieldError, and the payload wrapper.
│   ├── test_permissions.py       # ``DjangoModelPermission`` class behavior + write-auth enforcement (spec-036 Slice 2 + Slice 3).
│   ├── test_resolvers.py         # Write-pipeline resolver tests (spec-036 Slice 3).
│   ├── test_sets.py              # ``DjangoMutation`` base, ``Meta`` validation, registration, and the phase-2.5 bind.
│   └── test_write_transaction.py # The BETA-055 write-transaction contract (``DjangoSchema`` + ``utils/write_transaction.py``).
├── optimizer/    # Package tests for optimizer plans, application, extensions, selections, and nested-fetch strategies.
│   ├── _builders.py              # Shared builders for the optimizer test package.
│   ├── test_definition_order.py  # Optimizer tests for definition-order-independent DjangoType relation graphs.
│   ├── test_extension.py         # DjangoOptimizerExtension tests for gating, caching, strictness, schema audit, context, and querysets.
│   ├── test_field_meta.py        # FieldMeta tests for precomputed relation metadata used by optimizer planning.
│   ├── test_hints.py             # OptimizerHint tests for Meta.optimizer_hints normalization and validation.
│   ├── test_join_taxonomy.py     # Tests for the join-condition taxonomy (``optimizer/join_taxonomy.py``).
│   ├── test_lateral_fetch.py     # Tests for the Postgres lateral fetch strategy (``optimizer/lateral_fetch.py``).
│   ├── test_multi_db.py          # Optimizer-plan tests for multi-database cooperation and DB-alias preservation.
│   ├── test_nested_fetch.py      # Tests for the nested-connection fetch-strategy seam (``optimizer/nested_fetch.py``).
│   ├── test_nested_index_advisory.py  # Composite-index advisory unit matrix (optimizer-improvement-plan WS-D D2).
│   ├── test_plans.py             # OptimizationPlan tests for lifecycle, ORM reconciliation, paths, ordering, and window pagination.
│   ├── test_relay_id_projection.py  # Optimizer tests for Relay GlobalID projection and connector-column invariants.
│   ├── test_selections.py        # Tests for the selection-traversal substrate (``optimizer/selections.py``).
│   ├── test_single_parent_fetch.py  # Tests for the single-parent window fast path (``optimizer/single_parent_fetch.py``).
│   └── test_walker.py            # Selection-walker tests for GraphQL selection to ORM OptimizationPlan conversion.
├── orders/    # Package tests for the OrderSet subsystem.
│   ├── test_base.py              # RelatedOrder binding and lazy-resolution tests plus Meta.orderset_class promotion and validation.
│   ├── test_composition.py       # Filter and order composition smoke tests for Layer-3 read-side integration.
│   ├── test_factories.py         # OrderArgumentsFactory tests for BFS generation, annotations, caching, idempotency, and validation.
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
│   ├── test_client.py            # DB-free test-client tests for endpoints, multipart bodies, responses, mixin assertions, and exports.
│   ├── test_relay.py             # Public Relay helper tests for global_id_for and decode_global_id.
│   └── test_wrap.py              # Connection-method wrapping tests for cooperative consumer instrumentation.
├── types/    # Package tests for the DjangoType subsystem.
│   ├── test_base.py              # DjangoType tests for Meta validation, scalar mapping, relations, registry, and get_queryset.
│   ├── test_converters.py        # Converter tests for scalars, enums, relations, PostgreSQL containers, and file/image output objects.
│   ├── test_definition_order.py  # Acceptance tests for definition-order-independent DjangoType relation finalization.
│   ├── test_definition_order_schema.py  # Schema-build tests for definition-order-independent DjangoType finalization.
│   ├── test_definition_relations.py  # DjangoTypeDefinition tests for related-target lookup and custom Relay ID-resolver detection.
│   ├── test_generic_foreign_key.py  # DjangoType tests for GenericForeignKey rejection and GenericRelation support.
│   ├── test_relations.py         # PendingRelation tests for identity hashing and dataclass field contracts.
│   ├── test_relay_interfaces.py  # DjangoType Relay interface tests for Node wiring and resolver contracts.
│   ├── test_resolvers.py         # Relation resolver tests for cardinality, FK-ID elision, N+1 strictness, and multi-database routing.
│   └── fixtures/    # Fixture modules for cross-module DjangoType resolution tests.
│       ├── branch_module.py      # Cross-module fixture declaring BranchType and BranchFilter together.
│       └── shelf_module.py       # Cross-module fixture declaring ShelfType and ShelfFilter together.
└── utils/    # Package tests for shared utility helpers.
    ├── test_connections.py       # Unit tests for the shared connection planner/resolver contracts.
    ├── test_converters.py        # Tests for the shared fail-loud converter-dispatch skeleton (``utils/converters.py``, spec-039 P1.4).
    ├── test_imports.py           # Tests for the shared optional-import helpers (``utils/imports.py``, spec-041 Slice 1).
    ├── test_input_values.py      # Tests for the neutral set-input traversal substrate (``utils/input_values.py``).
    ├── test_inputs.py            # Tests for the shared generated-input substrate (``utils/inputs.py``).
    ├── test_permissions.py       # Tests for input permissions, relation-path gates, and Django/Channels request decoding.
    ├── test_querysets.py         # Tests for the shared query-source / visibility substrate (``utils/querysets.py``).
    ├── test_relations.py         # Relation utility tests for kinds, many-side detection, instance accessors, and package re-exports.
    ├── test_strings.py           # String utility tests for snake/camel/Pascal case conversion and Django lookup-path flattening.
    ├── test_typing.py            # Typing utility tests for async-callable detection and Strawberry, Python, and GraphQL unwrapping.
    └── test_write_values.py      # Tests for the shared write-value decoding substrate.
```


## Fakeshop example project

### Project tree

Source: `examples/fakeshop/`

```text
examples/fakeshop/    # A Django + Strawberry GraphQL example project that exercises django-strawberry-framework end-to-end.
├── graphql_client.py             # Shared live-``/graphql/`` HTTP helpers for the fakeshop acceptance suites.
├── manage.py                     # Django command-line entry point for the fakeshop example project.
├── schema_reload.py              # Shared complete-reload helper for fakeshop tests that rebuild ``config.schema``.
├── strategy_schemas.py           # Shared DjangoType/schema builders for strategy comparison harnesses.
├── config/    # Project orchestration package for fakeshop settings, URLs, WSGI, and schema composition.
│   ├── schema.py                 # Project GraphQL schema composing every app query and mutation with finalization and optimization.
│   ├── settings.py               # Django settings for fakeshop's SQLite, sharded-SQLite, and Postgres modes.
│   ├── test_settings.py          # Pytest-only settings layered over the shipped fakeshop configuration.
│   ├── urls.py                   # Fakeshop routes for index, admin, auth, multipart GraphQL/CSRF, and debug-toolbar endpoints.
│   └── wsgi.py                   # WSGI application entry point for the fakeshop example project.
└── apps/    # Domain-app namespace imported as ``apps.<app_name>`` from the fakeshop project root.
    ├── accounts/    # Schema-only accounts app exposing session-auth fields over Django's ``auth.User``.
    │   ├── apps.py               # Django app configuration for the schema-only accounts surface.
    │   └── schema.py             # Fakeshop GraphQL auth surface (spec-040).
    ├── glossary/    # Glossary app storing documentation terms and spec-term audit rows.
    │   ├── admin.py              # Admin registrations for the glossary data app.
    │   ├── apps.py               # Django app configuration for the glossary data app.
    │   ├── factories.py          # Test-data factories for the glossary app.
    │   ├── filters.py            # FilterSet declarations for the glossary data app.
    │   ├── models.py             # Relational source of truth for ``docs/GLOSSARY.md``.
    │   ├── orders.py             # OrderSet declarations for the glossary data app.
    │   ├── schema.py             # GraphQL schema for the glossary data app.
    │   └── management/    # Django management namespace for glossary import workflows.
    │       └── commands/    # Glossary management commands for importing spec-term companion data.
    │           └── import_spec_terms.py  # Import spec companion CSVs into glossary mentions and done-card links.
    ├── kanban/    # Kanban app storing board data and export metadata for ``KANBAN.md`` and ``KANBAN.html``.
    │   ├── admin.py              # Admin registrations so the board is browsable at ``/admin``.
    │   ├── apps.py               # Django app configuration that registers kanban consistency signals at startup.
    │   ├── constants.py          # Generated kanban allowlist of tracked repository paths (files + directories).
    │   ├── constraints.py        # Custom DB expression that keeps the UUIDModel one-hot constraint flat in migrations.
    │   ├── factories.py          # Test-data factories for the kanban app.
    │   ├── filters.py            # FilterSet declarations for the kanban board.
    │   ├── models.py             # Relational source of truth for this repository's ``KANBAN.md`` and ``KANBAN.html`` exports.
    │   ├── orders.py             # OrderSet declarations for the kanban board app.
    │   ├── schema.py             # GraphQL schema for the kanban board.
    │   ├── services.py           # The sanctioned write API for the kanban app.
    │   ├── signals.py            # Kanban signal receivers: guards + side-table wiring only.
    │   └── management/    # Django management namespace for kanban tracked-path imports.
    │       └── commands/    # Kanban management commands for changed-file and predicted-path imports.
    │           └── import_card_files.py  # manage.py import_card_files - replace kanban card package/path links.
    ├── library/    # Library app exercising relation graphs, keyset connections, and live model/form/serializer mutations.
    │   ├── apps.py               # Django app configuration for the library acceptance app.
    │   ├── filters.py            # FilterSet declarations for the library acceptance app (Slice 4).
    │   ├── filters_genre.py      # Cross-module fixture for the absolute-import-path ``RelatedFilter`` (Slice 4).
    │   ├── forms.py              # Forms for the library app's live form-mutation surface.
    │   ├── models.py             # Managed models for library acceptance coverage.
    │   ├── orders.py             # OrderSet declarations for library relation-graph and keyset-cursor acceptance coverage.
    │   ├── orders_genre.py       # Cross-module fixture for the absolute-import-path ``RelatedOrder`` (Slice 4).
    │   ├── schema.py             # Library GraphQL relation, optimizer, Relay/keyset, and model/form/serializer mutation surface.
    │   └── serializers.py        # DRF serializers for library mutation hooks, input shapes, visibility, locking, and nested writes.
    ├── products/    # Products app exercising a seedable catalog, Relay permissions, uploads, and three mutation flavors.
    │   ├── admin.py              # Admin registrations and shortcuts for inspecting, seeding, and deleting catalog data and test users.
    │   ├── apps.py               # Django app configuration for the fakeshop products domain.
    │   ├── fields.py             # Dormant cookbook-shaped FieldSet examples staged for the planned products fieldset surface.
    │   ├── filters.py            # FilterSet declarations for the fakeshop products app.
    │   ├── forms.py              # Consumer Django forms for the products live form-mutation surface (spec-038 Slice 4).
    │   ├── models.py             # Faker-shaped product catalog.
    │   ├── orders.py             # OrderSet declarations for the fakeshop products app.
    │   ├── schema.py             # Products Relay connections and permissioned model-, form-, and serializer-backed mutations.
    │   ├── serializers.py        # DRF serializers for the products live serializer-mutation surface (spec-039 Slice 3).
    │   ├── services.py           # Faker catalog seeding, user lifecycle, cascade fixtures, and catalog cleanup services.
    │   └── management/    # Management-command namespace for products data and user fixtures.
    │       └── commands/    # Django management commands for products fixture setup and teardown.
    │           ├── create_users.py  # Create permission-shaped products test users for admin and API access checks.
    │           ├── delete_data.py  # Delete seeded products catalog rows by count, item scope, or full catalog scope.
    │           ├── delete_users.py  # Delete generated products test users without touching superusers.
    │           ├── seed_data.py  # Seed Faker-backed products catalog rows up to a requested per-provider count.
    │           └── seed_shards.py  # Prepare the secondary shard SQLite DB for multi-DB products coverage.
    └── scalars/    # Scalars app exercising wire formats, filtering, file/image output, and multipart mutations.
        ├── apps.py               # Django app configuration for the scalar acceptance app.
        ├── filters.py            # FilterSet declarations for the scalars acceptance app.
        ├── forms.py              # Consumer Django forms for the scalars app's live form-mutation surface (spec-038).
        ├── models.py             # Models for scalar conversion, optimizer visibility, consumer overrides, and file/image uploads.
        ├── orders.py             # OrderSet declarations for the scalars acceptance app.
        └── schema.py             # GraphQL schema for scalar conversion, overrides, optimizer visibility, and file/image uploads.
```

### App roles

Each app owns a focused example surface: accounts for session auth, products for catalog and write APIs, library for relation and mutation matrices, scalars for converter and upload coverage, and kanban/glossary for repository docs rendered from database rows.

The namespace stays concrete: model-backed apps contribute real models, schema objects, and app-local tests, while schema-only accounts exercises Django's ``auth.User`` through the shared live HTTP suite.

`apps.accounts/`

It owns ``UserType`` plus login, logout, and register mutations and the ``me`` query without introducing app models; live ``/graphql/`` coverage lives in ``test_query/test_auth_api.py``.

`apps.glossary/`

It backs the exported ``docs/GLOSSARY.md`` file and keeps term aliases, categories, relationships, and spec mentions queryable through the same GraphQL surface used by the markdown exporter.

It also ties completed design specs back to the board: spec companion CSVs become ``GlossarySpecMention`` rows, and done-card glossary links are reconciled so rendered documentation, kanban metadata, and GraphQL API reads describe the same vocabulary.

Management commands:
- `manage.py import_spec_terms` - Import spec companion CSVs into glossary mentions and done-card links.

`apps.kanban/`

It is the database source for the root ``KANBAN.md`` export and ``KANBAN.html`` dashboard data, including card ordering, dependency integrity, release targeting, glossary links, and reusable prose sections shared with other docs-as-data exporters.

It owns the board invariants rather than leaving them in importer scripts: card numbers, status placement, dependency edges, dependency prose, card references, and reusable BoardDoc prose are validated in app services/signals so every entry point behaves the same way.

Management commands:
- `manage.py import_card_files` - Replace kanban card package/path links.

`apps.library/`

It is the primary relational acceptance surface: live GraphQL tests use it to prove foreign keys, reverse relations, one-to-one links, many-to-many joins, Relay nodes, optimizer hints, consumer queryset shaping, BigInt round-tripping, periodical/issue keyset connections, and mutation edge cases including raw-PK relations and nested writes.

It deliberately stays service-free: tests create rows inline so relation behavior, queryset planning, and computed fields remain visible without a fixture abstraction hiding the model graph being exercised.

`apps.products/`

It carries Category, Item, Property, and Entry data plus Faker-backed services, management commands, admin shortcuts, Relay connections, filter/order sidecars, cascade visibility, upload inputs, and model/form/serializer mutations.

It is the operational fixture app: services and management commands create users, seed/delete catalog rows, and prepare sharded data; non-live tests cover admin and tooling, while schema behavior is exercised both in-process and through live GraphQL HTTP.

Management commands:
- `manage.py create_users` - Create permission-shaped products test users for admin and API access checks.
- `manage.py delete_data` - Delete seeded products catalog rows by count, item scope, or full catalog scope.
- `manage.py delete_users` - Delete generated products test users without touching superusers.
- `manage.py seed_data` - Seed Faker-backed products catalog rows up to a requested per-provider count.
- `manage.py seed_shards` - Prepare the secondary shard SQLite DB for multi-DB products coverage.

`apps.scalars/`

It provides nullable and non-null scalar fixtures, relation edges, and override cases that let live GraphQL tests pin scalar conversion, serialization, filtering, schema introspection, structured file/image reads, and model/form Upload mutations.

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
