# django-strawberry-framework

## Goal
`django-strawberry-framework` is a DRF-shaped Django integration for Strawberry GraphQL. It lets Django teams build GraphQL APIs from Django models using the familiar `class Meta` style instead of a decorator-heavy surface.

The package sits on top of Django's ORM and Strawberry's GraphQL engine. Django remains responsible for models, querysets, database routing, and relations; Strawberry remains responsible for schema execution; this package provides the Django-native bridge between them.

This file is the friendly docs landing page. It should stay short: enough to explain what the package is, what exists today, and where the deeper references live.

## Documentation map
- [`../README.md`](../README.md) — install, run, seed example data, test, build, publish, and contributor operations.
- [`FEATURES.md`](FEATURES.md) — detailed package capability catalog, including optimizer behavior and comparisons with `strawberry-graphql-django` and `graphene-django`.
- [`TREE.md`](TREE.md) — detailed architecture and layout reference, including upstream package trees and test placement rules.
- [`../KANBAN.md`](../KANBAN.md) — active project board for shipped, planned, deferred, and blocked work.

## Why this package exists
- Django developers already know `Meta.model`, `fields`, `exclude`, filtersets, serializers, and queryset hooks.
- Strawberry is the modern Python GraphQL engine, but its Django ecosystem is decorator-oriented.
- This package keeps the Strawberry engine while making the public API feel like DRF, django-filter, and Django itself.

## Current surface
Shipped today:
- `DjangoType` for model-backed Strawberry types
- scalar, relation, and choice-enum conversion
- generated relation resolvers
- `get_queryset` visibility hook
- model/type registry
- `DjangoOptimizerExtension` for automatic ORM optimization
- `OptimizerHint` for per-field optimizer overrides
- `auto` re-export from Strawberry

Planned next layers:
- `FieldSet`
- filters
- orders
- aggregates
- `DjangoConnectionField`
- permissions and cascade permissions
- schema export helpers

## Package architecture
The package is layered:
- Layer 1: shared infrastructure (`conf`, exceptions, registry, utilities)
- Layer 2: model-backed types and query optimization (`DjangoType`, optimizer)
- Layer 3: GraphQL query surfaces planned on top of Layer 2 (filters, orders, aggregates, connections, permissions)

Layer 1 and Layer 2 are shipped. Layer 3 is planned.

## Current tree
```text
django_strawberry_framework/
├── __init__.py
├── py.typed
├── conf.py
├── exceptions.py
├── registry.py
├── types/
├── optimizer/
└── utils/
```

For per-file responsibilities and the matching test tree, see [`TREE.md`](TREE.md).

## Target tree
```text
django_strawberry_framework/
├── __init__.py
├── py.typed
├── apps.py
├── conf.py
├── exceptions.py
├── registry.py
├── fieldset.py
├── connection.py
├── permissions.py
├── types/
├── optimizer/
├── filters/
├── orders/
├── aggregates/
├── management/
│   └── commands/
│       └── export_schema.py
└── utils/
    └── queryset.py
```

The target tree is intentionally DRF-shaped: small core primitives first, then focused subsystems for filtering, ordering, aggregation, connection fields, permissions, and management helpers. The detailed target layout, including planned files inside each subsystem, lives in [`TREE.md`](TREE.md).

## Tests
Package tests mirror package source under `tests/` and gate package coverage. Example-project tests live under `examples/fakeshop/tests/`; live HTTP GraphQL tests belong under `examples/fakeshop/test_query/`.

## Design docs
Future design work continues to use `docs/spec-<topic>.md`.

The existing completed specs are being archived for 0.0.4 after their shipped behavior is consolidated into the docs and their unfinished work is preserved in [`../KANBAN.md`](../KANBAN.md).

## Status
Pre-alpha. The shipped foundation is `DjangoType` plus the ORM optimizer. Layer 3 features are planned but not implemented. Public API changes are expected until `0.1.0`.
