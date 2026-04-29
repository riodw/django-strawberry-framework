# django-strawberry-framework

## Goal

`django-strawberry-framework` is a **DRF-inspired Django integration framework for [Strawberry GraphQL](https://github.com/strawberry-graphql/strawberry)**.

The intention is to give Django developers the same `Meta`-class-driven, "batteries-included" developer experience they already get from Django REST Framework — but for GraphQL — while leveraging Strawberry as the underlying type-safe, async-friendly GraphQL engine.

Concretely, the package aims to provide:

- A `DjangoType` (or similarly named) class that generates a Strawberry type from a Django model with a familiar `Meta` configuration block.
- Declarative filtering, ordering, aggregation, and permission rules — all configured in `Meta`, all composable, all introspectable from a single class definition.
- A migration path that feels natural for teams coming from `django-filter`, `DRF`, or `graphene-django`.
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

## Status

Pre-alpha. The public API is not stable and is expected to change rapidly until `0.1.0`.
