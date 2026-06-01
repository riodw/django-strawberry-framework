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

<!-- TODO(spec-028-orders-0_0_8 Slice 5): update the public status paragraph for
0.0.8 after the ordering subsystem and joint-cut version bump land. Pseudo: name
the newest shipped surface as OrderSet / RelatedOrder / Ordering /
order_input_type / Meta.orderset_class without widening top-level __all__. -->

**`0.0.7`, single-maintainer, alpha-quality.** Fine for internal tools and prototypes; not production. The public names are stable; correctness and edge-case behavior are still hardening. Newest shipped surface: `DjangoListField` — the non-Relay `list[T]` factory for root Query fields, new in `0.0.7` (default resolver pulls `model._default_manager.all()` and applies `cls.get_queryset(...)` in sync + async contexts).

For the current capability snapshot — what the package can actually do in the example project right now — see [`TODAY.md`][today]. The full shipped / planned / deferred catalog and the `0.1.0` → `1.0.0` milestone framing live in [`docs/GLOSSARY.md`][glossary]. Per-card sequencing for both releases lives in [`KANBAN.md`][kanban].

## Get started → [`docs/README.md`][readme]

Installation, quick start, schema-setup walkthrough, running the example project, and seeding test data live in [`docs/README.md`][readme]. That's the next stop if this looks like your shape.

## Project documentation

- [`docs/README.md`][readme] — install, quick start, walkthrough, status
- [`docs/GLOSSARY.md`][glossary] — shipped/planned/deferred capability catalog + migration notes
- [`GOAL.md`][goal] — long-term destination and rich-schema north star
- [`TODAY.md`][today] — current package capability snapshot for examples and early adopters
- [`docs/TREE.md`][tree] — package and test layout reference
- [`KANBAN.md`][kanban] — contributor/maintainer board for shipped, planned, and blocked work
- [`BACKLOG.md`][backlog] — strategic differentiators beyond parity (post-`1.0.0`)
- [`CONTRIBUTING.md`][contributing] — dev setup, format, test, build, publish

## Inspired by

- <https://github.com/riodw/django-graphene-filters>
- <https://github.com/encode/django-rest-framework>
- <https://github.com/strawberry-graphql/strawberry-graphql-django>

## Contributing & Security

- Contribution workflow: [`CONTRIBUTING.md`][contributing]
- Vulnerability reporting: [`SECURITY.md`][security]
- Release notes: [`CHANGELOG.md`][changelog]

<!-- LINK DEFINITIONS -->

<!-- Root -->
[backlog]: BACKLOG.md
[changelog]: CHANGELOG.md
[contributing]: CONTRIBUTING.md
[goal]: GOAL.md
[kanban]: KANBAN.md
[security]: SECURITY.md
[today]: TODAY.md

<!-- docs/ -->
[glossary]: docs/GLOSSARY.md
[readme]: docs/README.md
[tree]: docs/TREE.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
