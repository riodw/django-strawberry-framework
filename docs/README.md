# django-strawberry-framework

## Goal

`django-strawberry-framework` is a **DRF-inspired Django integration framework for [Strawberry GraphQL](https://github.com/strawberry-graphql/strawberry)**.

The intention is to give Django developers the same `Meta`-class-driven, "batteries-included" developer experience they already get from Django REST Framework — but for GraphQL — while leveraging Strawberry as the underlying type-safe, async-friendly GraphQL engine.

Concretely, the package aims to provide:

- **Shipped:** A `DjangoType` base class that generates a Strawberry type from a Django model via a familiar nested `Meta` configuration block — scalar, relation, and choice-enum conversion, the type registry, and the `get_queryset` hook.
- **Shipped:** A built-in N+1 optimizer — cardinality-aware relation resolvers (O1), a selection-tree walker (O2), the `OptimizationPlan` data structure, the root-gated `resolve` hook with async parity and type-tracing (O3), `only()` projection (O5), and the `get_queryset` + `Prefetch` downgrade rule (O6). The optimizer is effective end-to-end for depth-1 queries. Nested prefetch chains (O4) are specified in `spec-optimizer.md` but not yet implemented.
- **Shipped:** Optimizer improvements beyond strawberry-graphql-django (B-slices from `spec-optimizer_beyond.md`): AST-cached plans with directive-variable extraction (B1), precomputed field metadata eliminating per-request `_meta.get_fields()` (B7), plan introspection via `info.context` (B5), N+1 detection with `strictness` API — `"off"` / `"warn"` / `"raise"` (B3), `Meta.optimizer_hints` with typed `OptimizerHint` wrapper — `SKIP`, `.select_related()`, `.prefetch_related()`, `.prefetch(Prefetch(...))` (B4), and schema-build-time audit (B6). Forward-FK-id elision (B2) and queryset diffing (B8) are specified but not yet implemented.
- **Planned:** Declarative filtering, ordering, aggregation, and permission rules — all configured in `Meta`, all composable, all introspectable from a single class definition. These are the Layer-3 subsystems described below; none are implemented yet.
- A migration path that feels natural for teams coming from `django-filter`, DRF, or `graphene-django`.
- Zero dependency on `strawberry-graphql-django`. We build directly on `strawberry-graphql` so we control the API surface end-to-end.

## Why this will be better than the existing options

### vs. `graphene-django`

`graphene-django` is the Django integration most existing GraphQL-on-Django shops use today, but it has aged poorly:

- **Maintenance velocity**: graphene-django releases are slow and infrequent; the wider Graphene ecosystem has effectively stalled compared to Strawberry's release cadence.
- **No first-class async**: Graphene was designed pre-async-Django and adds async support awkwardly. Strawberry was async-native from day one.
- **Older type system**: Graphene's type system predates modern Python typing; you write `graphene.String()` etc. Strawberry uses standard type hints and dataclasses, which integrate naturally with `mypy`/`pyright` and modern editors.
- **Smaller, slower-moving community**: Strawberry is where new investment in the Python GraphQL ecosystem is happening.

By targeting Strawberry while keeping a Django-shaped API, this package gives graphene-django shops a clear, low-friction migration path.

### vs. `strawberry-graphql-django`

`strawberry-graphql-django` is the official Strawberry integration for Django and is well-built — but it makes a few API choices that don't suit teams coming from DRF:

- **Decorator-driven configuration**: Filters, orderings, and permissions are configured via stacked decorators on type classes. This works, but it scatters configuration across decorators and makes the "shape" of a type harder to read at a glance. By contrast, a `Meta` class concentrates configuration in one place — the same convention DRF, django-filter, and Django itself all use.
- **Less familiar to Django/DRF teams**: Most production Django teams already know the DRF idiom (`class Meta: model = ..., fields = ..., filterset_class = ...`). Reusing that mental model dramatically lowers onboarding cost for new contributors.
- **Manual wiring for filters/aggregations**: Out of the box, `strawberry-graphql-django` covers the basics, but advanced filter trees (and/or/not), aggregation pipelines, and cascade permissions still require custom plumbing. This package aims to make those first-class, declared in `Meta`, consistent across types.

In short: `strawberry-graphql-django` gives you Strawberry on Django; this package aims to give you **DRF on Django on Strawberry**.

## Package architecture

The package is organized around a **layered dependency graph**: a small shared-infrastructure base, a type-system foundation built on it, and a set of GraphQL surface generators built on the foundation. Each layer depends only on layers below it; circular imports between layers are impossible to write by accident. Every non-trivial subsystem lives in its own subpackage so dependency boundaries stay explicit, and consumer-facing names are re-exported from the top-level `__init__.py` so import paths in user code stay short.

### Subsystems

**Layer 1 — Shared infrastructure** *(shipped)* (no internal dependencies). `conf` reads the `DJANGO_STRAWBERRY_FRAMEWORK` settings dict; `exceptions` defines the package error hierarchy (`DjangoStrawberryFrameworkError` and its subclasses); `registry` owns the model→type registry; `utils/` is a focused-submodule subpackage covering string-case conversion (`utils/strings.py`) and type unwrapping (`utils/typing.py`). Every other layer depends on these; nothing here depends on any layer above. *Not yet on disk:* `apps.py` (Django `AppConfig`) and `utils/queryset.py` (queryset introspection) land when the features that need them ship.

**Layer 2 — Type system** *(shipped / in progress)* (depends on Layer 1). Two subsystems sit at this layer because they're tightly coupled — one consumes the other's registry — but each is large enough to deserve its own dependency boundary:

- `types/` *(shipped)* — the `DjangoType` base class, scalar/relation/choice converters, and the cardinality-aware relation resolvers. This is the `Meta`-class-driven Django-model-to-Strawberry-type adapter and is the heart of the package.
- `optimizer/` *(O1–O3/O5–O6 + B1/B3–B7 shipped)* — `DjangoOptimizerExtension`, the selection-tree walker (`walker.py`, O2), and the `OptimizationPlan` shape (`plans.py`). Reads relation metadata off types registered in `types/`; nothing in `types/` reads anything from `optimizer/`. The optimizer ships in the foundation rather than as an opt-in afterthought because nested-prefetch correctness is too load-bearing to leave to consumer plumbing. `DjangoOptimizerExtension` is importable from both `django_strawberry_framework.optimizer` (subpackage path) and the top-level `django_strawberry_framework` namespace (`__all__`).

**Layer 3 — GraphQL surface generators** *(planned — not yet implemented)* (depend on Layer 2). Each subsystem follows the same `Meta`-class-driven, factory-emitting shape pioneered by `django-filter` and DRF:

- `filters/` — individual `Filter` classes, the `FilterSet` base, the filterset factory (auto-build a `FilterSet` from a model), the GraphQL argument factory, and the input-type / input-data adapters. This is the core of the original `django-graphene-filters`, ported to Strawberry.
- `orders/` — `Order` classes, `OrderSet`, GraphQL argument factory.
- `aggregates/` — aggregate result types (`Sum`, `Count`, `Avg`, `Min`, `Max`, `GroupBy`), `AggregateSet`, GraphQL argument factory.
- `fieldset.py` — `FieldSet`, the declarative scalar/relation selection class consumed by both `DjangoType.Meta.fields` semantics and `DjangoConnectionField`. Single-file Layer-3 module because the surface is one class.
- `connection.py` — `DjangoConnectionField` (Relay-style connection that composes filtering, ordering, aggregation, and field selection). Single-file Layer-3 module; promotes to a `relay/` subpackage if/when full Relay (`Node`, `Edge`, `cursor_connection` vs `list_connection`) lands.
- `permissions.py` — `apply_cascade_permissions` (cascade a permission decision through nested relations, integrated with the optimizer's `Prefetch` downgrade rule) and per-field permission hooks declared via `Meta`. Single-file Layer-3 module; promotes to `permissions/` if DRF-style `BasePermission` classes plus cascade plus hooks accumulate enough material.

The **current** top-level re-exports from `django_strawberry_framework/__init__.py` are `DjangoType`, `DjangoOptimizerExtension`, `OptimizerHint`, and `auto` (re-exported from `strawberry`). The **eventual** public surface will add `FilterSet`, `Filter`, `OrderSet`, `Order`, `AggregateSet`, `FieldSet`, `DjangoConnectionField`, and `apply_cascade_permissions` as their respective Layer-3 specs land. Internal helpers — factories, walkers, converters, individual filter / order / aggregate primitives — stay reachable via dotted paths (`from django_strawberry_framework.optimizer.walker import plan_optimizations`) for power users and tests but are not in the top-level namespace.

### Folder layout

#### Current (on disk today)

```text
django_strawberry_framework/
├── __init__.py              # public-API re-exports (DjangoType, DjangoOptimizerExtension, OptimizerHint, auto)
├── py.typed
├── conf.py                  # settings reader (DJANGO_STRAWBERRY_FRAMEWORK)
├── exceptions.py            # error hierarchy
├── registry.py              # model→type registry (+ iter_types() public iterator)
├── types/                   # DjangoType subsystem (Layer 2) — shipped
│   ├── __init__.py
│   ├── base.py              # DjangoType, _validate_meta, _build_annotations
│   ├── converters.py        # convert_scalar, convert_choices_to_enum, convert_relation
│   └── resolvers.py         # _make_relation_resolver, _attach_relation_resolvers, B3 N+1 detection
├── optimizer/               # N+1 optimizer subsystem (Layer 2) — O1–O3/O5–O6 + B1/B3–B7 shipped
│   ├── __init__.py          # re-exports DjangoOptimizerExtension
│   ├── extension.py         # DjangoOptimizerExtension (O3 hook, B1 cache, B3 strictness, B5 context stash)
│   ├── walker.py            # selection-tree walker (O2, O5 only fields, B4 hints, B7 cached field map)
│   └── plans.py             # OptimizationPlan data structure
│   ├── hints.py             # OptimizerHint typed wrapper (B4)
│   └── field_meta.py        # FieldMeta precomputed field metadata (B7)
└── utils/                   # cross-cutting helpers
    ├── __init__.py
    ├── strings.py           # snake_case / camelCase / PascalCase conversion
    └── typing.py            # type unwrapping (list[T], of_type, Optional[T])
```

#### Target (as Layer-3 subsystems land)

```text
django_strawberry_framework/
├── __init__.py              # public-API re-exports
├── py.typed
├── apps.py                  # Django AppConfig
├── conf.py                  # settings reader (DJANGO_STRAWBERRY_FRAMEWORK)
├── exceptions.py            # error hierarchy
├── registry.py              # model→type registry (+ iter_types() public iterator)
├── fieldset.py              # FieldSet (declarative scalar/relation selection)
├── permissions.py           # apply_cascade_permissions, per-field permission hooks
├── connection.py            # DjangoConnectionField (Relay-style connection)
├── types/                   # DjangoType subsystem (Layer 2)
│   ├── __init__.py
│   ├── base.py              # DjangoType, _validate_meta, _build_annotations
│   ├── converters.py        # convert_scalar, convert_choices_to_enum, convert_relation
│   └── resolvers.py         # _make_relation_resolver, _attach_relation_resolvers, B3 N+1 detection
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

Subpackage internals reuse the same module names across the tree — `base.py` for declarative classes, `sets.py` for the `*Set` aggregator, `factories.py` for the GraphQL argument factories, `inputs.py` where applicable. Contributors moving between filters / orders / aggregates always know where each kind of code lives without having to relearn the layout. This is the same convention DRF, `django-filter`, and `strawberry-graphql-django` adopt for their analogous trees, and it pays back the most when a single change touches multiple subsystems at once.

Single-file Layer-3 modules (`fieldset.py`, `permissions.py`, `connection.py`) live flat at the package root rather than each in their own one-file subpackage. The rule, borrowed from `strawberry_django`'s layout: a concept becomes a subpackage when it earns 3+ files of its own; below that, a single module at the root is clearer than `permissions/permissions.py`. If `permissions.py` later grows DRF-style `BasePermission` classes plus the cascade plus per-field hooks plus optimizer integration, it graduates to `permissions/`; same for `connection.py` graduating to `relay/` if full Relay support lands. Until then, flat is honest about how small the surface is.

`utils/` is a subpackage from day one because both reference packages — `graphene_django/utils/` and `strawberry_django/utils/` — converge on the same shape: string conversion, type unwrapping, and queryset introspection are different enough concerns that splitting them across submodules avoids a single 500-line `utils.py` accumulating later. We don't ship a top-level `mixins.py`; neither reference does, and `django_graphene_filters`'s lone `mixins.py` was a haphazard catch-all worth not repeating. Shared mixins, when they appear, will live close to whichever subsystem first surfaces the duplication.

### Tests mirror the package

The package-test tree under [`tests/`](../tests/) follows the same shape one-to-one. Every non-trivial source module gets its own test module at the parallel path; every subpackage gets a directory.

```text
tests/
├── base/                    # FROZEN: only conf and version checks
│   ├── test_init.py
│   └── test_conf.py
├── test_apps.py
├── test_registry.py
├── test_exceptions.py
├── test_fieldset.py
├── test_permissions.py
├── test_connection.py
├── types/
│   ├── test_base.py
│   ├── test_converters.py
│   └── test_resolvers.py
├── optimizer/
│   ├── test_extension.py
│   ├── test_walker.py
│   └── test_plans.py
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
```

Why mirror? Three reasons:

1. **Discoverability**. When a contributor opens `django_strawberry_framework/filters/factories.py`, the corresponding tests are at `tests/filters/test_factories.py`. No grep, no thinking. The reverse holds too — a failing test path immediately points at the source module under test, with no mental indirection.
2. **Coverage signal**. `fail_under = 100` on the package means coverage gaps surface as missing or thin test files. With a mirrored tree, a missing `tests/<subpkg>/test_<module>.py` is visually obvious in a `git status` review or a directory listing; in a flat `tests/` layout the same gap would only surface as a partial-coverage line in a coverage report, after the gap had already shipped.
3. **No name collisions**. `tests/types/test_base.py` and `tests/orders/test_base.py` both exist and don't fight, because pytest sees their full relative paths. A flat tree would force `test_types_base.py` / `test_orders_base.py` and the prefix would creep over time as more `*_base` files arrived.

The placement rules from [`AGENTS.md`](../AGENTS.md) still apply on top of this:

- `tests/base/` is **frozen** at exactly two files (`test_init.py`, `test_conf.py`); no new test files ever land there. It exists to test `__init__.py` (version) and `conf.py` (settings), and stays minimal.
- Tests whose system-under-test is the **fakeshop example project** (admin actions, management commands, services, models, in-process schema execution via `schema.execute_sync`) belong in [`examples/fakeshop/tests/`](../examples/fakeshop/tests/), not in `tests/` at the repo root. They exercise the package end-to-end via real Django flows but are example code, not shipping code, and don't gate the 100% coverage threshold.
- Tests that **ping `/graphql/` over HTTP** belong in [`examples/fakeshop/test_query/`](../examples/fakeshop/test_query/). These exercise the full Django + Strawberry HTTP stack via `django.test.Client.post("/graphql/", ...)`; they're slower and run alongside (not in place of) the in-process schema tests.

Future example projects mirror the same two-folder split: `examples/<project>/tests/` and `examples/<project>/test_query/`.

## Design docs

Feature-by-feature design documents live in [`docs/`](.) as committed `spec-*.md` files. The current set:

- [`spec-django_types.md`](spec-django_types.md) — the `DjangoType` foundation: Meta-driven model-to-type generation, scalar and relation field conversion, choice-to-enum generation, the type registry, and the `get_queryset` hook.
- [`spec-optimizer.md`](spec-optimizer.md) — the built-in N+1 optimizer subsystem, forked out of the `DjangoType` spec mid-implementation to redesign around a top-level selection-tree walker plus thin custom resolvers (including the load-bearing `select_related` → `Prefetch` downgrade rule when the target type carries a custom `get_queryset`).

- [`spec-optimizer_beyond.md`](spec-optimizer_beyond.md) — eight optimizer improvements beyond what strawberry-graphql-django ships: AST-cached plans (B1, shipped), forward-FK-id elision (B2), N+1 detection in dev mode (B3, shipped), `Meta.optimizer_hints` (B4, shipped), plan introspection via context (B5, shipped), schema-build-time optimization audit (B6), precomputed optimizer field metadata (B7, shipped), and queryset optimization diffing (B8).

Subsequent specs will layer `FilterSet`, `OrderSet`, `AggregateSet`, `FieldSet`, the `DjangoConnectionField`, and the permissions subsystem on top of that foundation — one `spec-<topic>.md` per Layer-3 subsystem in the architecture above.

## Status

Pre-alpha. The shipped surface is Layer 1 (shared infrastructure) and Layer 2 (DjangoType + optimizer foundation). Layer 3 (filters, orders, aggregates, permissions, connection fields) is designed and spec'd but not yet implemented. The public API is not stable and is expected to change rapidly until `0.1.0`.
