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

class CategoryType(DjangoType):
    class Meta:
        model = Category
        fields = ("id", "name")

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

**Coming from DRF + django-filter?** Your `Meta.model` / `fields` / `exclude` / `filterset_class` mental model travels straight over — and filtering *and* ordering ship today via `Meta.filterset_class` / `Meta.orderset_class`. Mutations are on the roadmap (`0.0.11`): planned as `DjangoMutation` classes with the same nested-`Meta` shape, including a DRF-serializer flavor via `Meta.serializer_class`.

## Status

<!--
TODO(spec-032-full_relay-0_0_9 Slice 7): Update the status paragraph's
newest-shipped-surface line: the full Relay story (root `node(id:)` / `nodes(ids:)` via
`DjangoNodeField` / `DjangoNodesField`, the relation-as-Connection upgrade with
`Meta.relation_shapes`, and the `testing.relay` helpers) becomes the newest shipped
surface, alongside the existing GlobalID-strategy and DjangoConnectionField sentences.
No version-number change here - the 0.0.8 -> 0.0.9 bump is owned by the joint cut
(spec-032 Decision 13).
-->

**`0.0.8`, single-maintainer, alpha-quality.** Fine for internal tools and prototypes; not production. The public names are stable; correctness and edge-case behavior are still hardening. Newest shipped surface: the model-anchored Relay `GlobalID` default (`0.0.9`) — every Relay-Node-shaped `DjangoType` now encodes its `id` as the Django model label (`app_label.modelname:<pk>`) instead of the GraphQL type name, so renaming a GraphQL type no longer invalidates cached IDs; `Meta.globalid_strategy` (per type) and `RELAY_GLOBALID_STRATEGY` (schema-wide) select `model` (default) / `type` (legacy opt-out) / `type+model` (transitional) / callable, with `Meta` → setting → default precedence. It lands alongside `DjangoConnectionField` (`0.0.9`) — the Relay connection field over a Relay-Node-shaped `DjangoType`, with `edges` / `node` / `pageInfo` cursor pagination, `filter:` / `orderBy:` arguments derived from the wrapped type's `Meta.filterset_class` / `Meta.orderset_class` sidecars, and an opt-in `totalCount` via `Meta.connection` (and the `DjangoConnection[T]` return alias) — and the ordering subsystem (`0.0.8`): `OrderSet` declarative ordering classes, `RelatedOrder` cross-relation ordering traversal, the public `Ordering` enum (six members with NULLS positioning), the `order_input_type` consumer helper, and `Meta.orderset_class` wiring, alongside the filter symbols promoted in `DONE-027-0.0.8`'s Slice 5 (`FilterSet`, `RelatedFilter`, `filter_input_type`, `Meta.filterset_class`), all integrated through the finalizer's phase-2.5 binding pass and the optimizer / `get_queryset` visibility hook.

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
