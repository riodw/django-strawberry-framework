# 🦄🍓 Django Strawberry Framework

[![build][build-image]][build-url] [![coveralls][coveralls-image]][coveralls-url] [![license][license-image]][license-url] [![changelog][changelog-image]][changelog-url]

[build-image]: https://github.com/riodw/django-strawberry-framework/actions/workflows/django.yml/badge.svg
[build-url]: https://github.com/riodw/django-strawberry-framework/actions
[coveralls-image]: https://coveralls.io/repos/github/riodw/django-strawberry-framework/badge.svg?branch=main
[coveralls-url]: https://coveralls.io/github/riodw/django-strawberry-framework?branch=main
[license-image]: https://img.shields.io/github/license/riodw/django-strawberry-framework
[license-url]: https://github.com/riodw/django-strawberry-framework/blob/main/LICENSE
[changelog-image]: https://img.shields.io/badge/changelog-CHANGELOG.md-blue
[changelog-url]: https://github.com/riodw/django-strawberry-framework/blob/main/CHANGELOG.md

GraphQL for Django the way DRF taught you: `class Meta`, not decorators. Built on [Strawberry](https://github.com/strawberry-graphql/strawberry), with a cooperative N+1 optimizer in the box.

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

That's a complete model-backed type. Relations wire themselves; nested selections become `select_related` / `prefetch_related` / `only()` without you touching a resolver.

## Why this package exists

Django developers think in `class Meta`, querysets, DRF, and django-filter. Strawberry's existing Django integration thinks in decorators. This package keeps Strawberry as the engine and makes `class Meta` the configuration surface, so it feels like `graphene-django` evolved onto a modern engine rather than replaced by a different one.

## What you get

**Everything hangs off one `Meta`.** Fields, Relay, filtering, ordering, all on the type:

```python
class ItemType(DjangoType):
    class Meta:
        model = Item
        fields = ("id", "name", "category", "entries")
        interfaces = (relay.Node,)
        filterset_class = ItemFilter   # a django-filter-shaped FilterSet
        orderset_class = ItemOrder     # its OrderSet twin
```

**Root fields in one line.** `DjangoConnectionField` gives Relay cursor pagination with `filter:` / `orderBy:` derived from the type above; `DjangoListField` is the plain-list alternative.

```python
@strawberry.type
class Query:
    all_items: DjangoConnection[ItemType] = DjangoConnectionField(ItemType)
    all_categories: list[CategoryType] = DjangoListField(CategoryType)
```

<!-- TODO(spec-050 slice 5): Fold the shipped list-argument surface into the
0.0.7 capability sentence without rewriting its historical introduction.
Pseudocode: say that every DjangoListField now publishes nullable offset/limit,
that orderBy is published only from Meta.orderset_class, that nonzero offset
requires visible stable ordering, and that returned/skip coordinates are
bounded by ResourcePolicy with no pk or DISTINCT injection. Keep version and
release-note wording owned by spec-053's joint cut. -->

**Three mutation flavors, one shape.** Write against the model, a Django form, or a DRF serializer. Inputs are generated, and all three report validation through the same `FieldError` envelope.

```python
class CreateItem(DjangoMutation):
    class Meta:
        model = Item
        operation = "create"

class CreateItemViaForm(DjangoModelFormMutation):
    class Meta:
        form_class = ItemModelForm
        operation = "create"

class CreateItemViaSerializer(SerializerMutation):
    class Meta:
        serializer_class = ItemSerializer
        operation = "create"
```

**And the rest:**

- **N+1 detection.** `DjangoOptimizerExtension(strictness="raise")` turns an unplanned lazy load into an error, so N+1 fails CI instead of surprising production.
- **Visibility that cascades.** Override `get_queryset` as you already do; `apply_cascade_permissions` pushes it across FK / OneToOne edges with zero extra queries.
- **Write permissions by default.** Generated mutations deny unless `DjangoModelPermission` (Django's `add` / `change` / `delete`) or your own class says yes.
- **Production defaults.** Unexpected exceptions are masked behind a `correlationId`, request bodies are capped, and file output never leaks the server's filesystem path.
- **Session auth.** Opt-in `login` / `logout` / `register` mutations and a `current_user` query.
- **Tooling.** `TestClient` for in-process GraphQL tests, `DjangoDebugExtension` for SQL in `extensions.debug`, django-debug-toolbar integration, and a Channels router for subscriptions.

## Why it's fast

Five optimizer wins over `strawberry-graphql-django`:

- **Cross-request plan cache.** The selection tree is walked once, not on every request.
- **N+1 detection.** Upstream is preventive only; `strictness="raise"` is a detective mode.
- **FK-id join elision.** `{ relation { id } }` reads the FK column already on the parent, no join.
- **Class-creation-time metadata.** Frozen when the type is created, not memoized on first request.
- **Postgres lateral nested pagination.** Nested connection pages via `CROSS JOIN LATERAL`, paging per parent instead of numbering every child. Opt-in; measured 6.4× on dense pages in one local run.

Benchmarks: [`bench_plan_cache.py`][bench-plan-cache] and [`bench_nested_fetch.py`][bench-nested-fetch] (needs `FAKESHOP_PG_DSN`). Numbers are from one machine; run them on yours.

## Is this for you?

| | `graphene-django` | `strawberry-graphql-django` | this package |
| --- | --- | --- | --- |
| Config surface | `class Meta` | decorators + annotations | `class Meta` |
| N+1 handling | no bundled optimizer | bundled optimizer | cooperative optimizer that respects your own `select_related` / `prefetch_related` |
| N+1 detection | none | preventive only | `strictness="raise"` |
| Filtering | django-filter `FilterSet` | `filter_type` decorated classes | `FilterSet` + `Meta.filterset_class` |
| Mutations | form and serializer classes | create / update / delete decorators | model, form, and serializer on one `Meta` |
| Unregistered relation target | silently dropped | `DjangoModelType { pk }` stub | raises at `finalize_django_types()`, naming the field |

Coming from `graphene-django`: your `Meta` stays, `DjangoObjectType` becomes `DjangoType`. Coming from `strawberry-graphql-django`: keep Strawberry, lose the decorators. Coming from DRF: `model` / `fields` / `exclude` / `filterset_class` mean what you think they mean.

## Status

**`0.0.15`, alpha, single maintainer.** Good for internal tools and prototypes, not production yet; public names are stable, edge cases are still hardening. The bundled `examples/fakeshop/` is a development fixture and refuses to run with `DEBUG` off. Going to production means your own project built against the [production security profile][readme-security].

## Get started → [`docs/README.md`][readme]

Install, quick start, reading and writing data, transport, and deployment all live in [`docs/README.md`][readme].

- [`docs/GLOSSARY.md`][glossary] — every shipped / planned / deferred capability, by anchor
- [`TODAY.md`][today] — what the example project can do right now
- [`GOAL.md`][goal] — where this is going
- [`KANBAN.md`][kanban] / [`BACKLOG.md`][backlog] — roadmap and post-`1.0.0` ideas
- [`docs/TREE.md`][tree] — package layout
- [`CHANGELOG.md`][changelog] · [`CONTRIBUTING.md`][contributing] · [`SECURITY.md`][security]

## Inspired by

- <https://github.com/riodw/django-graphene-filters>
- <https://github.com/encode/django-rest-framework>
- <https://github.com/strawberry-graphql/strawberry-graphql-django>

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
[readme-security]: docs/README.md#production-security-profile
[tree]: docs/TREE.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->
[bench-nested-fetch]: scripts/bench_nested_fetch.py
[bench-plan-cache]: scripts/bench_plan_cache.py

<!-- .venv/ -->

<!-- External -->
