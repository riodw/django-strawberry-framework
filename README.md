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

## Why it's fast

Four optimizer wins over `strawberry-graphql-django`, all on the mainstream (concretely-typed) path:

- **Cross-request plan cache** — upstream re-walks the selection tree every request; we walk once, serve from a 256-entry LRU (`cache_info()`). Structurally, every repeat of a cacheable query is a hit (one miss, then all hits). The per-request selection-tree walk this eliminates — which upstream pays on every request — measured ~85–150 µs depending on selection depth in one local run ([`bench_plan_cache.py`][bench-plan-cache]); absolute µs vary by machine and dataset, so read them as a single benchmark, not a fixed package property.
- **Strictness / N+1 detection** — `strictness="raise"` → `OptimizerError` on unplanned lazy load; a CI gate. Upstream: preventive-only, no detective mode.
- **FK-id join elision** — `{ relation { id } }` reads the parent's existing FK column — no join/prefetch. Upstream resolves the same selection with a `select_related` JOIN.
- **Class-creation-time metadata** — frozen at type creation, not memoized on first request.

Run it: `uv run python scripts/bench_plan_cache.py`.

## Is this for you?

**Coming from `graphene-django`?** Your `class Meta` shape stays — `DjangoObjectType` becomes `DjangoType`, you drop the Graphene runtime, and you gain the N+1 optimizer for free. Same mental model, modern Strawberry engine.

**Coming from `strawberry-graphql-django`?** Keep Strawberry; lose the decorators. Configuration moves into `class Meta` so it's consistent with the rest of your Django app. Plus the optimizer wins above, and queryset diffing.

**Coming from DRF + django-filter?** Your `Meta.model` / `fields` / `exclude` / `filterset_class` mental model travels straight over — and filtering *and* ordering ship today via `Meta.filterset_class` / `Meta.orderset_class`. Mutations are on the roadmap: the `DjangoMutation` foundation lands in `0.0.11` with the same nested-`Meta` shape, and a DRF-serializer flavor via `Meta.serializer_class` follows in `0.0.13`.

## Status

**`0.0.10`, single-maintainer, alpha-quality.** Fine for internal tools and prototypes; not production. The public names are stable; correctness and edge-case behavior are still hardening. Newest shipped surface: the cascade-permissions subsystem (`0.0.10`) — `apply_cascade_permissions` / `aapply_cascade_permissions`, one call inside a type's `get_queryset` that cascades visibility across the type's single-column forward FK / OneToOne edges (cycle-guarded, nullable-FK-preserving, caller-alias-pinned, with a sync + `sync_to_async` async pair) and composes with the shipped `check_<field>_permission` gates, connections, node refetch, and list fields at zero added query round-trips. It builds on connection-aware optimizer planning (`0.0.9`), which closes the Relay story — a nested `<field>Connection`'s `edges { node }` selection now gets a windowed `Prefetch` (one window-function query per relation per request instead of one per parent, with `pageInfo` / `totalCount` served from the same query's annotations), pagination-aware plan-cache keys, and strictness coverage of unplanned nested-connection access; the products example reshapes to the connections-only cookbook mirror to dogfood it. It lands on top of the full Relay story (`0.0.9`) — root `node(id:)` / `nodes(ids:)` refetch via `DjangoNodeField` / `DjangoNodesField` (bare interface and typed forms; `id: strawberry.ID` raw-string arguments — the Relay spec's literal `node(id: ID!)` — decoded server-side through the strategy system, returning `null` for hidden and missing rows with no existence leak and `GraphQLError` with `extensions={"code": "GLOBALID_INVALID"}` for malformed ids; `nodes` is per-type-batched and order-preserving), the relation-as-Connection upgrade — every Relay-Node-shaped type's many-side relations whose target is also Relay-Node-shaped gain a `<field>Connection` sibling by default (`"both"`), with `Meta.relation_shapes` narrowing per relation (`"connection"` suppresses the list field; `"list"` suppresses the connection) — and the `testing.relay` helpers (the strategy-aware `global_id_for(type_cls, id)` and the public re-export `decode_global_id(gid)`). It lands alongside the model-anchored Relay `GlobalID` default (`0.0.9`) — every Relay-Node-shaped `DjangoType` encodes its `id` as the Django model label (`app_label.modelname:<pk>`) instead of the GraphQL type name, so renaming a GraphQL type no longer invalidates cached IDs; `Meta.globalid_strategy` (per type) and `RELAY_GLOBALID_STRATEGY` (schema-wide) select `model` (default) / `type` (legacy opt-out) / `type+model` (transitional) / callable, with `Meta` → setting → default precedence — and `DjangoConnectionField` (`0.0.9`) — the Relay connection field over a Relay-Node-shaped `DjangoType`, with `edges` / `node` / `pageInfo` cursor pagination, `filter:` / `orderBy:` arguments derived from the wrapped type's `Meta.filterset_class` / `Meta.orderset_class` sidecars, and an opt-in `totalCount` via `Meta.connection` (and the `DjangoConnection[T]` return alias) — and the ordering subsystem (`0.0.8`): `OrderSet` declarative ordering classes, `RelatedOrder` cross-relation ordering traversal, the public `Ordering` enum (six members with NULLS positioning), the `order_input_type` consumer helper, and `Meta.orderset_class` wiring, alongside the filter symbols promoted in `DONE-027-0.0.8`'s Slice 5 (`FilterSet`, `RelatedFilter`, `filter_input_type`, `Meta.filterset_class`), all integrated through the finalizer's phase-2.5 binding pass and the optimizer / `get_queryset` visibility hook.

The optimizer also gained two robustness guards in `0.0.10` — it will not touch a queryset the consumer already evaluated (it passes an evaluated root queryset through unchanged instead of re-executing a `.only()` / `select_related` clone), and it suppresses column projection on non-query operations (mutation / subscription querysets keep `select_related` / `prefetch_related` but carry no `.only()` column deferral). No public API change.

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
[bench-plan-cache]: scripts/bench_plan_cache.py

<!-- .venv/ -->

<!-- External -->
