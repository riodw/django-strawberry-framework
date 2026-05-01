# Reference Trees

Side-by-side directory listings of the two upstream Django + GraphQL integrations this package draws from. Captured for reference while shaping `django-strawberry-framework`'s own subpackage layout (see `docs/README.md` "Package architecture"). Filters applied: `__pycache__/` directories, package-internal `tests/` directories, `conftest.py`, and `*.pyc` files are excluded so both trees show only the library logic surface (the strawberry-django source checkout already keeps tests outside the package directory; graphene-django ships its tests inside the installed package, so they're filtered here for comparability).

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

The Layer 1 + Layer 2 subpackage migration is complete: `types/`, `optimizer/`, and `utils/` are on disk as subpackages. Layer 3 modules (`filters/`, `orders/`, `aggregates/`, `fieldset.py`, `permissions.py`, `connection.py`, `apps.py`, `management/`) do not exist yet and will land as their respective specs ship.

```text
django_strawberry_framework/
├── __init__.py              # re-exports DjangoType, DjangoOptimizerExtension, auto
├── py.typed
├── conf.py                  # settings reader (DJANGO_STRAWBERRY_FRAMEWORK)
├── exceptions.py            # error hierarchy
├── registry.py              # model→type registry
├── types/                   # DjangoType subsystem (Layer 2) — shipped
│   ├── __init__.py
│   ├── base.py              # DjangoType, _validate_meta, _build_annotations
│   ├── converters.py        # convert_scalar, convert_choices_to_enum, convert_relation
│   └── resolvers.py         # _make_relation_resolver, _attach_relation_resolvers
├── optimizer/               # N+1 optimizer subsystem (Layer 2) — O1–O3/O5–O6 + B1–B7 shipped, O4 pending
│   ├── __init__.py          # re-exports DjangoOptimizerExtension
│   ├── extension.py         # DjangoOptimizerExtension (root-gated resolve hook, O3, B1/B2/B3/B5)
│   ├── walker.py            # selection-tree walker (plan_optimizations, O2/O5/B2/B4/B7)
│   ├── plans.py             # OptimizationPlan data structure
│   ├── hints.py             # OptimizerHint typed wrapper (B4)
│   └── field_meta.py        # FieldMeta precomputed field metadata (B7)
└── utils/                   # cross-cutting helpers
    ├── __init__.py
    ├── strings.py           # snake_case / PascalCase conversion
    └── typing.py            # type unwrapping (unwrap_return_type)
```

## django_strawberry_framework (target layout)

The target shape adds Layer 3 modules on top of the current layout. Derived from the three reference trees above and the dependency-graph reasoning in [`README.md`](README.md) "Package architecture".

```text
django_strawberry_framework/
├── __init__.py              # public-API re-exports
├── py.typed
├── apps.py                  # Django AppConfig
├── conf.py                  # settings reader (DJANGO_STRAWBERRY_FRAMEWORK)
├── exceptions.py            # error hierarchy
├── registry.py              # model→type registry
├── fieldset.py              # FieldSet (declarative scalar/relation selection)
├── permissions.py           # apply_cascade_permissions, per-field permission hooks
├── connection.py            # DjangoConnectionField (Relay-style connection)
├── types/                   # DjangoType subsystem (Layer 2)
│   ├── __init__.py
│   ├── base.py              # DjangoType, _validate_meta, _build_annotations
│   ├── converters.py        # convert_scalar, convert_choices_to_enum, convert_relation
│   └── resolvers.py         # _make_relation_resolver, _attach_relation_resolvers
├── optimizer/               # N+1 optimizer subsystem (Layer 2)
│   ├── __init__.py
│   ├── extension.py         # DjangoOptimizerExtension (Strawberry SchemaExtension)
│   ├── walker.py            # selection-tree walker (plan_optimizations)
│   └── plans.py             # OptimizationPlan, Prefetch chain helpers
├── filters/                 # Filtering subsystem (Layer 3)
│   ├── __init__.py
│   ├── base.py              # individual Filter classes
│   ├── sets.py              # FilterSet
│   ├── factories.py         # filterset + GraphQL-arguments factories
│   └── inputs.py            # input types + input-data adapters
├── orders/                  # Ordering subsystem (Layer 3)
│   ├── __init__.py
│   ├── base.py              # Order classes
│   ├── sets.py              # OrderSet
│   └── factories.py         # GraphQL-arguments factory
├── aggregates/              # Aggregation subsystem (Layer 3)
│   ├── __init__.py
│   ├── base.py              # Sum/Count/Avg/Min/Max/GroupBy result types
│   ├── sets.py              # AggregateSet
│   └── factories.py         # GraphQL-arguments factory
├── management/              # Django management commands
│   └── commands/
│       ├── __init__.py
│       └── export_schema.py # schema export (mirrors strawberry_django's command)
└── utils/                   # cross-cutting helpers
    ├── __init__.py
    ├── strings.py           # snake_case / camelCase / PascalCase conversion
    ├── typing.py            # type unwrapping (list[T], of_type, Optional[T])
    └── queryset.py          # queryset introspection, prefetch-cache awareness
```

## Test layout going forward

Tests live across three roots, each with a focused responsibility. The root `tests/` tree mirrors the package source one-to-one and grows alongside the package; the two `examples/fakeshop/` test trees hold tests whose system-under-test is the example project, split by whether they exercise the GraphQL HTTP endpoint. The placement rules themselves are pinned in [`AGENTS.md`](../AGENTS.md) "Test placement is mandatory"; this section is the visual map of the trees and a per-folder reference for what kind of test goes where.

### Current shape (on disk today)

```text
tests/                       # Package-internal tests (current state)
├── __init__.py
├── test_registry.py         # model→type registry
├── base/                    # FROZEN: only conf and version checks
│   ├── __init__.py
│   ├── test_conf.py
│   └── test_init.py
├── types/                   # mirrors django_strawberry_framework/types/
│   ├── __init__.py
│   ├── test_base.py         # ← DjangoType + Meta validation + scalar/relation synthesis
│   ├── test_converters.py   # ← convert_scalar / convert_relation / convert_choices_to_enum
│   └── test_resolvers.py    # ← O1 _make_relation_resolver / _attach_relation_resolvers
├── optimizer/               # mirrors django_strawberry_framework/optimizer/
│   ├── __init__.py
│   ├── test_extension.py    # ← DjangoOptimizerExtension (root-gated resolve hook, O3)
│   ├── test_walker.py       # ← O2 selection-tree walker
│   └── test_plans.py        # ← OptimizationPlan data structure
└── utils/                   # mirrors django_strawberry_framework/utils/
    ├── __init__.py
    ├── test_strings.py      # ← snake_case / pascal_case
    └── test_typing.py       # ← unwrap_return_type

examples/fakeshop/tests/     # Example-project tests, NO /graphql HTTP
├── test_admin.py            # admin actions via django.test.Client on /admin/...
├── test_commands.py         # management commands via call_command
├── test_models.py           # __str__ etc. on fakeshop models
├── test_schema.py           # in-process schema execution via schema.execute_sync
├── test_services.py         # Faker-driven seed_data / delete_data / create_users
└── test_urls.py             # fakeshop project urls (index view)

examples/fakeshop/test_query/   # Example-project tests, LIVE /graphql HTTP
└── README.md                # placeholder; reserved for HTTP-level GraphQL tests
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
├── test_permissions.py      # apply_cascade_permissions, per-field hooks
├── test_connection.py       # DjangoConnectionField
├── types/
│   ├── test_base.py
│   ├── test_converters.py
│   └── test_resolvers.py
├── optimizer/
│   ├── test_extension.py
│   ├── test_walker.py       # spec-optimizer.md O2 selection-tree walker
│   └── test_plans.py        # OptimizationPlan / Prefetch chain helpers
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

`examples/fakeshop/test_query/` — **Example-project tests, live `/graphql/` HTTP.** The system-under-test is the same fakeshop project, but exercised end-to-end through the Django + Strawberry HTTP stack via `django.test.Client.post("/graphql/", ...)`. Verifies the full request pipeline: URL routing, view, schema execution, JSON response serialization. Currently empty (placeholder `README.md` only); fills in as the example schema gains real types and resolvers. Same coverage and discovery rules as the sibling `examples/fakeshop/tests/` tree.

`examples/<project>/...` — **Future example projects** mirror the same two-folder split: every additional example app under `examples/` ships its own `tests/` and `test_query/` directories with the same in-process / HTTP separation. `pytest.ini`'s `testpaths` will be extended one entry per pair when a second example lands; nothing about the package or the existing fakeshop test trees changes.

`examples/fakeshop/fakeshop/products/tests/` — **Per-Django-app convention placeholder.** Empty by design — the per-app `tests/` folder is where Django expects an app's own tests to live by convention, but the fakeshop example consolidates all example tests at the project level (`examples/fakeshop/tests/` and `examples/fakeshop/test_query/`) rather than per-app. The empty directory stays committed as documentation of the convention; do not add files there.
