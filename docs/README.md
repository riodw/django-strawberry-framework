# django-strawberry-framework

## Goal

`django-strawberry-framework` is a **DRF-inspired Django integration framework for [Strawberry GraphQL](https://github.com/strawberry-graphql/strawberry)**.

The intention is to give Django developers the same `Meta`-class-driven, "batteries-included" developer experience they already get from Django REST Framework — but for GraphQL — while leveraging Strawberry as the underlying type-safe, async-friendly GraphQL engine.

Concretely, the package aims to provide:

- A `DjangoType` base class that generates a Strawberry type from a Django model via a familiar nested `Meta` configuration block.
- Declarative filtering, ordering, aggregation, and permission rules — all configured in `Meta`, all composable, all introspectable from a single class definition.
- A built-in N+1 optimizer that respects per-type `get_queryset` overrides (downgrading `select_related` to `Prefetch` so visibility filters are honored across joins). Borrowed behaviorally from `strawberry-graphql-django`'s optimizer; we ship it in the foundation, not as an opt-in afterthought.
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

## Design docs

Feature-by-feature design documents live in [`docs/`](.) as committed `spec-*.md` files. The current set:

- [`spec-django_types.md`](spec-django_types.md) — the `DjangoType` foundation: Meta-driven model-to-type generation, scalar and relation field conversion, choice-to-enum generation, the type registry, and the `get_queryset` hook.
- [`spec-optimizer.md`](spec-optimizer.md) — the built-in N+1 optimizer subsystem, forked out of the `DjangoType` spec mid-implementation to redesign around a top-level selection-tree walker plus thin custom resolvers (including the load-bearing `select_related` → `Prefetch` downgrade rule when the target type carries a custom `get_queryset`).

Subsequent specs will layer `FilterSet`, `OrderSet`, `AggregateSet`, `FieldSet`, and the connection field on top of that foundation.

## Status

Pre-alpha. The public API is not stable and is expected to change rapidly until `0.1.0`.
