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

Five optimizer wins over `strawberry-graphql-django`, all on the mainstream (concretely-typed) path:

- **Cross-request plan cache** — upstream re-walks the selection tree every request; we walk once, serve from a 256-entry LRU (`cache_info()`). Structurally, every repeat of a cacheable query is a hit (one miss, then all hits). The per-request selection-tree walk this eliminates — which upstream pays on every request — measured ~85–150 µs depending on selection depth in one local run ([`bench_plan_cache.py`][bench-plan-cache]); absolute µs vary by machine and dataset, so read them as a single benchmark, not a fixed package property.
- **Strictness / N+1 detection** — `strictness="raise"` → `OptimizerError` on unplanned lazy load; a CI gate. Upstream: preventive-only, no detective mode.
- **FK-id join elision** — `{ relation { id } }` reads the parent's existing FK column — no join/prefetch. Upstream resolves the same selection with a `select_related` JOIN.
- **Class-creation-time metadata** — frozen at type creation, not memoized on first request.
- **Postgres lateral nested pagination** (landed on `main`, unreleased) — nested Relay connection pages can fetch via `CROSS JOIN LATERAL`, paging per parent at O(parents × page) instead of the windowed prefetch's O(all children); measured 6.4× on dense count-free pages in one local run ([`bench_nested_fetch.py`][bench-nested-fetch]), same benchmark caveat as above. Opt-in per extension instance (`nested_connection_strategy="lateral"` / `"auto"`, or the `NESTED_CONNECTION_STRATEGY` setting); the windowed strategy stays the default everywhere, and every non-Postgres vendor windows. Upstream paginates nested relations with window functions only.

Run it: `uv run python scripts/bench_plan_cache.py`. The lateral benchmark needs a Postgres server: `FAKESHOP_PG_DSN=... uv run python scripts/bench_nested_fetch.py`.

## Is this for you?

**Coming from `graphene-django`?** Your `class Meta` shape stays — `DjangoObjectType` becomes `DjangoType`, you drop the Graphene runtime, and you gain the N+1 optimizer for free. Same mental model, modern Strawberry engine.

**Coming from `strawberry-graphql-django`?** Keep Strawberry; lose the decorators. Configuration moves into `class Meta` so it's consistent with the rest of your Django app. Plus the optimizer wins above, and queryset diffing.

**Coming from DRF + django-filter?** Your `Meta.model` / `fields` / `exclude` / `filterset_class` mental model travels straight over — and filtering *and* ordering ship today via `Meta.filterset_class` / `Meta.orderset_class`. Mutations ship today too: the model-driven `DjangoMutation` create/update/delete foundation lands in `0.0.11` with the same nested-`Meta` shape — auto-generated `<Model>Input` / `<Model>PartialInput`, the shared `FieldError` envelope, and the `DjangoMutationField` factory — and form-based mutations follow in `0.0.12` via `Meta.form_class`: `DjangoModelFormMutation` (a `ModelForm`) and `DjangoFormMutation` (a plain `Form`), both reusing that same `FieldError` envelope (populated from `form.errors`). A DRF-serializer flavor via `Meta.serializer_class` (`SerializerMutation`) and opt-in session-auth mutations (`login` / `logout` / `register` + a `current_user` query, imported from the `django_strawberry_framework.auth` submodule) ship in `0.0.13`.

## Status
<!-- TODO(spec-044 Slice 3): After the extension, implemented-contract docs,
joint 0.0.14 version quintet, and release artifacts all land, rewrite this
status block for shipped 0.0.14. Include the router, toolbar middleware,
test-client family, and response-extensions debug extension; only then remove
the "ahead of release / still to come" framing below. -->

**`0.0.13`, single-maintainer, alpha-quality.** Fine for internal tools and prototypes; not production. The public names are stable; correctness and edge-case behavior are still hardening. Newest shipped surface (`0.0.13`): the DRF-serializer mutation flavor — `SerializerMutation` via `Meta.serializer_class` over a DRF `Serializer` / `ModelSerializer`, riding the same `DjangoMutation` write pipeline and `FieldError` envelope (a soft DRF dependency, lazily resolved and never added to the package root `__all__`) — plus opt-in session-auth mutations imported from the `django_strawberry_framework.auth` submodule: `login` / `logout` / `register` field factories and a `current_user` query helper, all on the same shared `FieldError` envelope, defaulting to `AllowAny` (the documented inversion of the write family's deny-by-default) and constrained to the session transport (no Channels). These land on top of form-based mutations (`0.0.12`) — `DjangoModelFormMutation` (a `ModelForm`) and `DjangoFormMutation` (a plain `Form`) on the `class Meta` surface (`Meta.form_class` + optional `fields` / `exclude`), with the input shape derived from the form's declared fields and `form.errors` mapped onto the shared `FieldError` envelope (the `ModelForm` flavor returns the post-save object in the uniform `node` / `result` slot; the plain `Form` flavor returns the pinned `ok` + `errors` payload). It lands on top of the `Upload` scalar + generated `FileField` / `ImageField` mutation-input typing and the structured `DjangoFileType` / `DjangoImageType` read output (`0.0.11`, the read object nullable by default in the generated SDL regardless of the Django column, so an empty stored file resolves to `null`) — the scalar and generated mutation-field typing, not full multipart HTTP upload ergonomics, which await the `0.0.14` `TestClient`. It lands on top of the model-driven `DjangoMutation` create/update/delete foundation (`0.0.11`) and the cascade-permissions subsystem (`0.0.10`) — `apply_cascade_permissions` / `aapply_cascade_permissions`, one call inside a type's `get_queryset` that cascades visibility across the type's single-column forward FK / OneToOne edges (cycle-guarded, nullable-FK-preserving, caller-alias-pinned, with a sync + `sync_to_async` async pair) and composes with the shipped `check_<field>_permission` gates, connections, node refetch, and list fields at zero added query round-trips. It builds on connection-aware optimizer planning (`0.0.9`), which closes the Relay story — a nested `<field>Connection`'s `edges { node }` selection now gets a windowed `Prefetch` (one window-function query per relation per request instead of one per parent, with `pageInfo` / `totalCount` served from the same query's annotations), pagination-aware plan-cache keys, and strictness coverage of unplanned nested-connection access; the products example reshapes to the connections-only cookbook mirror to dogfood it. It lands on top of the full Relay story (`0.0.9`) — root `node(id:)` / `nodes(ids:)` refetch via `DjangoNodeField` / `DjangoNodesField` (bare interface and typed forms; `id: strawberry.ID` raw-string arguments — the Relay spec's literal `node(id: ID!)` — decoded server-side through the strategy system, returning `null` for hidden and missing rows with no existence leak and `GraphQLError` with `extensions={"code": "GLOBALID_INVALID"}` for malformed ids; `nodes` is per-type-batched and order-preserving), the relation-as-Connection upgrade — every Relay-Node-shaped type's many-side relations whose target is also Relay-Node-shaped gain a `<field>Connection` sibling by default (`"both"`), with `Meta.relation_shapes` narrowing per relation (`"connection"` suppresses the list field; `"list"` suppresses the connection) — and the `testing.relay` helpers (the strategy-aware `global_id_for(type_cls, id)` and the public re-export `decode_global_id(gid)`). It lands alongside the model-anchored Relay `GlobalID` default (`0.0.9`) — every Relay-Node-shaped `DjangoType` encodes its `id` as the Django model label (`app_label.modelname:<pk>`) instead of the GraphQL type name, so renaming a GraphQL type no longer invalidates cached IDs; `Meta.globalid_strategy` (per type) and `RELAY_GLOBALID_STRATEGY` (schema-wide) select `model` (default) / `type` (legacy opt-out) / `type+model` (transitional) / callable, with `Meta` → setting → default precedence — and `DjangoConnectionField` (`0.0.9`) — the Relay connection field over a Relay-Node-shaped `DjangoType`, with `edges` / `node` / `pageInfo` cursor pagination, `filter:` / `orderBy:` arguments derived from the wrapped type's `Meta.filterset_class` / `Meta.orderset_class` sidecars, and an opt-in `totalCount` via `Meta.connection` (and the `DjangoConnection[T]` return alias) — and the ordering subsystem (`0.0.8`): `OrderSet` declarative ordering classes, `RelatedOrder` cross-relation ordering traversal, the public `Ordering` enum (six members with NULLS positioning), the `order_input_type` consumer helper, and `Meta.orderset_class` wiring, alongside the filter symbols promoted in `DONE-027-0.0.8`'s Slice 5 (`FilterSet`, `RelatedFilter`, `filter_input_type`, `Meta.filterset_class`), all integrated through the finalizer's phase-2.5 binding pass and the optimizer / `get_queryset` visibility hook.

Already landed on `main` ahead of the `0.0.14` release: the Channels ASGI router (`DONE-041`) — `DjangoGraphQLProtocolRouter`, imported from `django_strawberry_framework.routers` (a lazy PEP 562 submodule export, never a package-root export), a `channels.routing.ProtocolTypeRouter` subclass serving GraphQL on both HTTP and WebSocket in one import with `AuthMiddlewareStack` (sessions + `scope["user"]` on both protocols) and the WebSocket `AllowedHostsOriginValidator` composed in, constructor-compatible with upstream `strawberry_django.routers.AuthGraphQLProtocolTypeRouter` so a migrant changes exactly the import line (`channels` is the package's second soft dependency, after `djangorestframework`) — and the pluggable nested-connection fetch-strategy seam: the windowed prefetch is the `"windowed"` default backend, a Postgres `CROSS JOIN LATERAL` backend pages per parent, and the `nested_connection_strategy=` constructor kwarg / `NESTED_CONNECTION_STRATEGY` setting / `"auto"` vendor sniff select the backend per extension instance. Still to come in `0.0.14`: debug-toolbar middleware, the test-client helper, and the response-extensions debug middleware.

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
[bench-nested-fetch]: scripts/bench_nested_fetch.py
[bench-plan-cache]: scripts/bench_plan_cache.py

<!-- .venv/ -->

<!-- External -->
