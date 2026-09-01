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

Django developers think in `class Meta`, querysets, DRF, and django-filter. The Python GraphQL world has moved to [Strawberry](https://github.com/strawberry-graphql/strawberry) — but Strawberry's Django ecosystem leans on decorators and Strawberry-shaped configuration, not Django-shaped configuration.

This package closes that gap: Strawberry stays as the engine, `class Meta` becomes the configuration surface, your existing querysets stay yours, and the shipped N+1 optimizer *cooperates* with the `select_related` / `prefetch_related` you've already written instead of replacing them. The result feels like `graphene-django` evolved onto a modern engine instead of replaced by a different one.

## Why it's fast

Five optimizer wins over `strawberry-graphql-django`, all on the mainstream (concretely-typed) path:

- **Cross-request plan cache** — upstream re-walks the selection tree every request; we walk once, serve from a 256-entry LRU (`cache_info()`). Structurally, every repeat of a cacheable query is a hit (one miss, then all hits). The per-request selection-tree walk this eliminates — which upstream pays on every request — measured ~85–150 µs depending on selection depth in one local run ([`bench_plan_cache.py`][bench-plan-cache]); absolute µs vary by machine and dataset, so read them as a single benchmark, not a fixed package property.
- **Strictness / N+1 detection** — `strictness="raise"` → `OptimizerError` on unplanned lazy load; a CI gate. Upstream: preventive-only, no detective mode.
- **FK-id join elision** — `{ relation { id } }` reads the parent's existing FK column — no join/prefetch. Upstream resolves the same selection with a `select_related` JOIN.
- **Class-creation-time metadata** — frozen at type creation, not memoized on first request.
- **Postgres lateral nested pagination** (shipped `0.0.14`) — nested Relay connection pages can fetch via `CROSS JOIN LATERAL`, paging per parent at O(parents × page) instead of the windowed prefetch's O(all children); measured 6.4× on dense count-free pages in one local run ([`bench_nested_fetch.py`][bench-nested-fetch]), same benchmark caveat as above. Opt-in per extension instance (`nested_connection_strategy="lateral"` / `"auto"`, or the `NESTED_CONNECTION_STRATEGY` setting); the windowed strategy stays the default everywhere, while `"auto"` selects lateral only when the nested queryset's effective routed alias is PostgreSQL and executes the same bounded window on every other vendor. Upstream paginates nested relations with window functions only.

Run it: `uv run python scripts/bench_plan_cache.py`. The lateral benchmark needs a Postgres server: `FAKESHOP_PG_DSN=... uv run python scripts/bench_nested_fetch.py`.

## Is this for you?

**Coming from `graphene-django`?** Your `class Meta` shape stays — `DjangoObjectType` becomes `DjangoType`, you drop the Graphene runtime, and you gain the N+1 optimizer for free. Same mental model, modern Strawberry engine.

**Coming from `strawberry-graphql-django`?** Keep Strawberry; lose the decorators. Configuration moves into `class Meta` so it's consistent with the rest of your Django app. Plus the optimizer wins above, and queryset diffing.

**Coming from DRF + django-filter?** Your `Meta.model` / `fields` / `exclude` / `filterset_class` mental model travels straight over — and filtering *and* ordering ship today via `Meta.filterset_class` / `Meta.orderset_class`. All three mutation flavors ship today on the same nested-`Meta` shape and shared `FieldError` envelope: the model-driven `DjangoMutation` create/update/delete foundation (`0.0.11` — auto-generated `<Model>Input` / `<Model>PartialInput` and the `DjangoMutationField` factory), form-based mutations via `Meta.form_class` (`0.0.12` — `DjangoModelFormMutation` for a `ModelForm`, `DjangoFormMutation` for a plain `Form`, errors populated from `form.errors`), and the DRF-serializer flavor via `Meta.serializer_class` (`SerializerMutation`, `0.0.13`), plus opt-in session-auth mutations (`login` / `logout` / `register` + a `current_user` query, imported from the `django_strawberry_framework.auth` submodule, `0.0.13`).

## Status

**`0.0.15`, single-maintainer, alpha-quality.** Fine for internal tools and prototypes; not production. The public names are stable; correctness and edge-case behavior are still hardening. The bundled example project (`examples/fakeshop/`) is a **development fixture, never a deployment**: its `DEBUG=True`, checked-in `SECRET_KEY`, GraphiQL, and open permission demonstrations are intentional, it cannot be made production-ready by editing settings (its settings module refuses to load with `DEBUG` off), and taking this package to production means a separate project built against [`docs/README.md`'s production security profile][readme].

**Newest released (`0.0.14`); active prerelease (`0.0.15`).** The `0.0.14` cut is the security-and-integration alpha described below; `0.0.15` development is tracked in [`KANBAN.md`][kanban], and its release notes are open in [`CHANGELOG.md`][changelog]:

- **Channels ASGI router** (`DONE-041`; redesigned on `main` by the transport-security card `046`) — `DjangoGraphQLProtocolRouter`, imported from `django_strawberry_framework.routers`: GraphQL over WebSocket behind Host + Origin validation and `AuthMiddlewareStack`, while HTTP dispatches straight to your own Django ASGI application. Since `046`: `django_application` is required, `url_pattern` became `websocket_url_pattern` (exact match), the Channels HTTP branch is gone — GraphQL over HTTP is the package's own `DjangoGraphQLView` / `AsyncDjangoGraphQLView` in your URLconf, with a cumulative request-body cap (`413`) and a strict UTF-8 wire contract — and the router is no longer constructor-compatible with upstream `AuthGraphQLProtocolTypeRouter`. `channels` is a soft dependency.
- **Debug-toolbar middleware** (`DONE-042`) — `DebugToolbarMiddleware`, imported from `django_strawberry_framework.middleware.debug_toolbar`: teaches `django-debug-toolbar`'s SQL panel to see Strawberry `/graphql/` traffic (`django-debug-toolbar` is a soft dependency).
- **Test-client family** (`DONE-043`) — `TestClient` / `AsyncTestClient` plus the `GraphQLTestMixin` / `GraphQLTestCase` unittest family, imported from `django_strawberry_framework.testing`: in-process requests against `/graphql/` returning a typed `Response` (`errors` / `data` / `extensions`), with the multipart-upload ergonomics the `Upload` scalar awaited.
- **`DjangoDebugExtension`** (`DONE-044`) — a Strawberry `SchemaExtension` capturing an operation's SQL and resolver exceptions into `extensions.debug`, the Strawberry-native equivalent of graphene-django's `_debug` field; never for an internet-facing schema. Ships alongside the pluggable nested-connection fetch-strategy seam (`"windowed"` default / Postgres `"lateral"` / `"auto"`, via `nested_connection_strategy=` or the `NESTED_CONNECTION_STRATEGY` setting).
- **Secure output and error defaults** (`048`, on `main`) — file/image read output drops the server's absolute filesystem path (`DjangoFileType` / `DjangoImageType` are now `name` / `size` / `url` + image `width` / `height`; `Meta.filesystem_path_fields` opts a column back in, swapping it onto `DjangoFilePathType` / `DjangoImagePathType` — the second intentional break); `DjangoDebugExtension` fails closed under `DEBUG=False` unless explicitly acknowledged, with its payload capped; and `DjangoSchema` gains a production error policy — an unexpected exception reaches the client as a stable message plus a `correlationId` (logged server-side under the same id) while deliberate `GraphQLError`s keep their contract, configurable via `error_policy=` / `ERROR_POLICY`. The resource-policy (`047`) and dependency/CI (`049`) cards complete the program.

Earlier alpha surfaces, each detailed in [`CHANGELOG.md`][changelog] and [`docs/GLOSSARY.md`][glossary]:

- `0.0.13` — DRF-serializer mutations (`SerializerMutation` via `Meta.serializer_class`, a soft DRF dependency) + opt-in session-auth mutations (`login` / `logout` / `register` + `current_user`, from the `django_strawberry_framework.auth` submodule).
- `0.0.12` — form-based mutations: `DjangoModelFormMutation` (a `ModelForm`) and `DjangoFormMutation` (a plain `Form`) via `Meta.form_class`, `form.errors` mapped onto the shared `FieldError` envelope.
- `0.0.11` — the model-driven `DjangoMutation` create/update/delete foundation: generated `<Model>Input` / `<Model>PartialInput` types, the shared `FieldError` envelope, `DjangoModelPermission` write authorization, plus the `Upload` scalar and the structured file/image read output.
- `0.0.10` — cascade visibility permissions (`apply_cascade_permissions`: one call in `get_queryset` cascades visibility across FK / OneToOne edges at zero added round-trips) and two optimizer robustness guards (evaluated querysets pass through untouched; mutations get no `.only()` deferral).
- `0.0.9` — the Relay release: `DjangoConnectionField` (cursor pagination + sidecar-derived `filter:` / `orderBy:` + opt-in `totalCount`), root `node(id:)` / `nodes(ids:)` refetch with no existence leak, the relation-as-connection upgrade with `Meta.relation_shapes` (**since `0.0.14` the default is `"connection"` alone**), model-anchored `GlobalID`s (`app_label.modelname:<pk>`, so type renames keep cached IDs valid), and connection-aware optimizer planning (one windowed `Prefetch` per relation per request).
- `0.0.8` — the filtering (`FilterSet` / `RelatedFilter` / `filter_input_type` / `Meta.filterset_class`) and ordering (`OrderSet` / `RelatedOrder` / `Meta.orderset_class`) subsystems, with active-input-only `check_<field>_permission` gates.
- `0.0.7` — `DjangoListField`, the non-Relay `list[T]` root Query field (default `_default_manager.all()` resolver, `get_queryset` cooperation in sync and async contexts, root-gated optimizer planning, consumer-annotation-driven outer nullability), plus the `DjangoStrawberryFrameworkConfig` app config, the `manage.py export_schema` SDL command, the multi-database cooperation contract, the Django Trac #37064 hardening with its `safe_wrap_connection_method` consumer helper, and warning-free scalar registration through `strawberry_config()`.

<!-- TODO(spec-050 slice 5): Fold the shipped list-argument surface into the
0.0.7 capability sentence without rewriting its historical introduction.
Pseudocode: say that every DjangoListField now publishes nullable offset/limit,
that orderBy is published only from Meta.orderset_class, that nonzero offset
requires visible stable ordering, and that returned/skip coordinates are
bounded by ResourcePolicy with no pk or DISTINCT injection. Keep version and
release-note wording owned by spec-053's joint cut. -->

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
