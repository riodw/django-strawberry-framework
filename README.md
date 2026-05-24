# 🍓 Django Strawberry Framework

[![build][build-image]][build-url] [![coveralls][coveralls-image]][coveralls-url] [![license][license-image]][license-url] [![changelog][changelog-image]][changelog-url]

[build-image]: https://github.com/riodw/django-strawberry-framework/actions/workflows/django.yml/badge.svg
[build-url]: https://github.com/riodw/django-strawberry-framework/actions
[coveralls-image]: https://coveralls.io/repos/github/riodw/django-strawberry-framework/badge.svg?branch=main
[coveralls-url]: https://coveralls.io/github/riodw/django-strawberry-framework?branch=main
[license-image]: https://img.shields.io/github/license/riodw/django-strawberry-framework
[license-url]: https://github.com/riodw/django-strawberry-framework/blob/main/LICENSE
[changelog-image]: https://img.shields.io/badge/changelog-CHANGELOG.md-blue
[changelog-url]: https://github.com/riodw/django-strawberry-framework/blob/main/CHANGELOG.md

A DRF-shaped Django integration for [Strawberry GraphQL](https://github.com/strawberry-graphql/strawberry). Build GraphQL APIs from Django models with `class Meta`, not decorators — and get a cooperative N+1 optimizer in the box.

```python
from django_strawberry_framework import DjangoType, finalize_django_types

class ItemType(DjangoType):
    class Meta:
        model = Item
        fields = ("id", "name", "category")

finalize_django_types()
```

That's the entire surface for a model-backed GraphQL type. Relations are wired automatically; nested selections become Django ORM `select_related` / `prefetch_related` / `only` calls without you touching the resolver.

## Why this package exists

Django developers think in `class Meta`, querysets, DRF Serializers, and django-filter. The Python GraphQL world has moved to [Strawberry](https://github.com/strawberry-graphql/strawberry) — but Strawberry's Django ecosystem leans on decorators and Strawberry-shaped configuration, not Django-shaped configuration.

This package closes that gap: Strawberry stays as the engine, `class Meta` becomes the configuration surface, your existing querysets stay yours, and the shipped N+1 optimizer *cooperates* with the `select_related` / `prefetch_related` you've already written instead of replacing them. The result feels like `graphene-django` evolved onto a modern engine instead of replaced by a different one.

## Is this for you?

**Coming from `graphene-django`?** Your `class Meta` shape stays — `DjangoObjectType` becomes `DjangoType`, you drop the Graphene runtime, and you gain the N+1 optimizer for free. Same mental model, modern Strawberry engine.

**Coming from `strawberry-graphql-django`?** Keep Strawberry; lose the decorators. Configuration moves into `class Meta` so it's consistent with the rest of your Django app. Bonus: plan caching, FK-id elision, queryset diffing, strictness mode.

**Coming from DRF + django-filter?** Your `Meta.model` / `fields` / `exclude` / `filterset_class` mental model travels straight over. Mutations land as `DjangoMutation` classes with the same nested-`Meta` shape; DRF Serializers integrate via `Meta.serializer_class`.

## Status

**`0.0.7`, single-maintainer, alpha-quality.** Fine for internal tools and prototypes; not production. The public names are stable; correctness and edge-case behavior are still hardening. Newest shipped surface: `DjangoListField` — the non-Relay `list[T]` factory for root Query fields, new in `0.0.7` (default resolver pulls `model._default_manager.all()` and applies `cls.get_queryset(...)` in sync + async contexts).

For the current capability snapshot — what the package can actually do in the example project right now — see [`TODAY.md`](TODAY.md). The full shipped / planned / deferred catalog and the `0.1.0` → `1.0.0` milestone framing live in [`docs/GLOSSARY.md`](docs/GLOSSARY.md). Per-card sequencing for both releases lives in [`KANBAN.md`](KANBAN.md).

## Get started → [`docs/README.md`](docs/README.md)

Installation, quick start, schema-setup walkthrough, running the example project, and seeding test data live in [`docs/README.md`](docs/README.md). That's the next stop if this looks like your shape.

## Project documentation

- [`docs/README.md`](docs/README.md) — install, quick start, walkthrough, status
- [`docs/GLOSSARY.md`](docs/GLOSSARY.md) — shipped/planned/deferred capability catalog + migration notes
- [`GOAL.md`](GOAL.md) — long-term destination and rich-schema north star
- [`TODAY.md`](TODAY.md) — current package capability snapshot for examples and early adopters
- [`docs/TREE.md`](docs/TREE.md) — package and test layout reference
- [`KANBAN.md`](KANBAN.md) — contributor/maintainer board for shipped, planned, and blocked work
- [`BACKLOG.md`](BACKLOG.md) — strategic differentiators beyond parity (post-`1.0.0`)
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — dev setup, format, test, build, publish

## Inspired by

- <https://github.com/riodw/django-graphene-filters>
- <https://github.com/encode/django-rest-framework>
- <https://github.com/strawberry-graphql/strawberry-graphql-django>

## Contributing & Security

- Contribution workflow: [`CONTRIBUTING.md`](CONTRIBUTING.md)
- Vulnerability reporting: [`SECURITY.md`](SECURITY.md)
- Release notes: [`CHANGELOG.md`](CHANGELOG.md)
