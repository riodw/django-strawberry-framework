# django-strawberry-framework

`django-strawberry-framework` is a DRF-shaped Django integration for Strawberry GraphQL. It lets Django teams build GraphQL APIs from Django models using the familiar `class Meta` style instead of a decorator-heavy surface.

For the project pitch, migration context, and the canonical documentation map, start from [`../README.md`][readme]. For the long-term destination, see [`../GOAL.md`][goal]. For the current capability snapshot, see [`../TODAY.md`][today]. For contributor / maintainer workflow (dev setup, format, test, build, publish), see [`../CONTRIBUTING.md`][contributing].

## Installation

```shell
# pip
pip install django-strawberry-framework
# uv
uv add django-strawberry-framework
```

## Quick start

```python
import strawberry
from django_strawberry_framework import DjangoOptimizerExtension, DjangoType, finalize_django_types, strawberry_config
from myapp.models import Category, Item


class CategoryType(DjangoType):
    class Meta:
        model = Category
        fields = ("id", "name", "items")


class ItemType(DjangoType):
    class Meta:
        model = Item
        fields = ("id", "name", "category")


@strawberry.type
class Query:
    @strawberry.field
    def all_items(self) -> list[ItemType]:
        return Item.objects.all()


finalize_django_types()

_optimizer = DjangoOptimizerExtension()
schema = strawberry.Schema(
    query=Query,
    config=strawberry_config(),
    extensions=[lambda: _optimizer],
)
```

The optimizer is a module-level singleton wrapped in a factory — that preserves the instance-bound [Plan cache][glossary-plan-cache] (Strawberry runs the callable per request and gets the same instance back) and emits no deprecation warning (the entry is a callable, not an instance).

That is the shipped surface: `class Meta` configures the type, `finalize_django_types()` resolves relations after all `DjangoType` modules are imported, and the optimizer extension turns nested selections into Django ORM `select_related`, `prefetch_related`, and `only` calls. Relation fields can point at target types declared earlier or later, as long as every target type is registered before finalization.

### Relay Node

Add `Meta.interfaces = (relay.Node,)` to declare a Relay-node-shaped type. The package wires `id: GlobalID!`, the four `resolve_*` defaults, and `is_type_of` injection without any decorators on the consumer class.

```python
import strawberry
from strawberry import relay
from django_strawberry_framework import DjangoType, finalize_django_types
from myapp.models import Category


class CategoryNode(DjangoType):
    class Meta:
        model = Category
        fields = ("id", "name")
        interfaces = (relay.Node,)


finalize_django_types()
```

See [`GLOSSARY.md`'s Relay Node integration subsection][glossary-relay-node-integration] for the resolver list, composite-pk constraint, and the `is_type_of` injection contract.

As of `0.0.9` the default Relay `GlobalID` payload is the Django model label (`app_label.modelname:<pk>`, e.g. `products.item:42`) rather than the GraphQL type name, so renaming a GraphQL type no longer invalidates cached IDs. `Meta.globalid_strategy` (per type) and `RELAY_GLOBALID_STRATEGY` (schema-wide) select `model` (default), `type` (the legacy GraphQL-type-name opt-out), `type+model` (transitional decode of old type-anchored IDs while emitting model-anchored ones), or a callable encoder. See [`GLOSSARY.md`'s `Meta.globalid_strategy` subsection][glossary-metaglobalid_strategy].

> **Multiple `DjangoType`s per model under the `model` default.** A model-label payload is shared by every `DjangoType` over that model and always decodes to the model's **primary** type (`Meta.primary`). So if two Relay-Node types over one model both use the `model` default, the secondary's `GlobalID`s refetch as the primary — its distinct identity and `get_queryset` scope collapse onto the primary's (under the pre-`0.0.9` type-name default they were distinct and self-routing). This is intentional (a model-anchored ID cannot distinguish secondaries), and finalization emits a warning naming the collapsing secondaries; give a secondary disjoint identity with `Meta.globalid_strategy = "type"`.

## What just happened?

- `class Meta` tells the package which Django model and fields become a Strawberry type.
- Returning a Django `QuerySet` from the root resolver gives the optimizer something it can shape.
- `DjangoOptimizerExtension()` walks the selected GraphQL fields once at the root and applies one ORM plan.
- Nested relations become joins, prefetches, projections, and strictness checks without replacing your queryset.

## Today and coming next

For the current capability snapshot — what the package can actually do in the example project right now — see [`../TODAY.md`][today]. For the per-feature glossary covering every shipped / planned / deferred capability (deep-linkable by anchor — `GLOSSARY.md#filterset`, `GLOSSARY.md#fk-id-elision`, …), see [`GLOSSARY.md`][glossary]. For the long-term destination and the migration-shape diffs against `graphene-django` and `strawberry-graphql-django`, see [`../GOAL.md`][goal].

A quick summary:
<!-- TODO(spec-044 Slice 3): After the joint 0.0.14 cut and final card wrap,
change this to shipped 0.0.14. Add the test-client and
DjangoDebugExtension capability bullets, retain the already landed router and
toolbar bullets, and remove the remaining-alpha list only after every release
artifact is aligned. -->

**Shipped today** (`0.0.13`, plus `0.0.14` work already landed on `main`):
- `DjangoType` — model-backed Strawberry types via `class Meta`
- scalar conversion (text, integer, boolean, float, decimal, date/time, UUID, binary, choice enums; file/image read output as the structured `DjangoFileType` / `DjangoImageType` objects — nullable by default, so an empty stored file resolves to `null` regardless of the column's `null` / `blank` — with the filter / scalar-input value staying `str`)
- specialized scalar conversions (`BigIntegerField` / `PositiveBigIntegerField` → `BigInt`, `JSONField` → `JSON`, PostgreSQL `ArrayField` → `list[T]`, PostgreSQL `HStoreField` → `JSON`)
- relation conversion (forward / reverse FK, forward / reverse OneToOne, forward / reverse M2M)
- `Meta.interfaces = (relay.Node,)` for Relay-node-shaped types with `id: GlobalID!`
- generated relation resolvers, with annotation-only and `strawberry.field` consumer overrides preserved
- definition-order-independent relation finalization via `finalize_django_types()`
- `get_queryset` visibility hook (cooperates with the optimizer via `Prefetch` downgrade)
- `DjangoOptimizerExtension` — automatic ORM optimization: one selection-tree walk produces a `select_related` / `prefetch_related` / `only()` plan that cooperates with querysets you've already shaped (consumer entries are respected, not clobbered). Plan caching, FK-id elision for `{ relation { id } }`, `get_queryset` → `Prefetch` downgrade so visibility filters survive joins, and strictness mode (`off` / `warn` / `raise`) for accidental-N+1 detection are all in the box. As of `0.0.9` the walk is connection-aware: a nested `<field>Connection`'s `edges { node }` selection gets a windowed `Prefetch` (one window-function query per relation per request instead of one per parent) and strictness flags an unplanned, unserved nested-connection access. As of the `0.0.14` work on `main`, *how* a recognized nested connection is fetched is a pluggable strategy seam: the windowed prefetch is the default backend (`"windowed"`), a Postgres `CROSS JOIN LATERAL` backend pages per parent (O(parents × page) instead of the window's O(all children)), and the backend is selected per extension instance via the `nested_connection_strategy=` constructor kwarg, the `NESTED_CONNECTION_STRATEGY` setting, or `"auto"`; auto keeps one cache-stable lateral-capable window plan, selects lateral only when the nested queryset's effective routed alias is PostgreSQL, and executes the same bounded window on every other vendor. A consumer-authored `NestedConnectionStrategy` instance is also accepted. A keyset-mode nested connection always orders by its target type's declared `Meta.cursor_field`, matching root keyset cursor bytes; supplying that field's `orderBy:` sidecar deliberately leaves it unplanned for the per-parent pipeline rather than overriding the cursor order. As of `0.0.10` the optimizer will not touch a queryset the consumer already evaluated (it passes an evaluated root queryset through unchanged rather than re-executing a clone) and applies no column projection on non-query operations (mutation / subscription querysets keep `select_related` / `prefetch_related` but carry no `.only()` deferral). See [`GLOSSARY.md`][glossary] for the full optimizer surface.
- `DjangoListField` — non-Relay `list[T]` factory for root Query fields (new in `0.0.7`); default resolver pulls `model._default_manager.all()` and applies the type's `get_queryset` in sync + async contexts. See [`GLOSSARY.md#djangolistfield`][glossary-djangolistfield].
- `OptimizerHint` — per-relation overrides (`SKIP`, `select_related`, `prefetch_related`, custom `Prefetch`)
- model / type registry and `auto` re-export from Strawberry
- `Meta.primary` — multiple `DjangoType` subclasses per Django model with explicit primary-flag opt-in
- annotation-only and `strawberry.field` consumer overrides for scalar fields, symmetric with the shipped relation-override contract (consumer overrides bypass `convert_scalar` validations; `relay.Node` `id` collisions raise `ConfigurationError` at type-creation time)
- `Django AppConfig` — `django_strawberry_framework/apps.py` ships `DjangoStrawberryFrameworkConfig` so consumers can list `"django_strawberry_framework"` in `INSTALLED_APPS` and Django's check / signal hooks resolve through it (new in `0.0.7`).
- `manage.py export_schema` — Django management command that prints or writes the GraphQL SDL for a `strawberry.Schema` symbol (positional dotted path, optional `--path`); migration-parity with `strawberry-django`'s command of the same name. See [`GLOSSARY.md#schema-export-management-command`][glossary-schema-export-management-command].
- filtering subsystem (new in `0.0.8`) — `FilterSet` declarative filter classes with `Meta.fields` (dict / `"__all__"` shorthand) and the full `django-filter` lookup surface; `RelatedFilter` for cross-relation traversal (class / absolute import path / unqualified-name); `Meta.filterset_class` consumer wiring; the `filter_input_type` resolver-argument helper; finalizer phase-2.5 binding with orphan validation; per-field `check_*_permission` denial gates with active-input-only scope; clean composition with `get_queryset` visibility and the optimizer. See [`GLOSSARY.md#filterset`][glossary-filterset].
- ordering subsystem (new in `0.0.8`) — `OrderSet` declarative ordering classes with `Meta.fields` (list form or `"__all__"` shorthand for every column-backed model field); `RelatedOrder` cross-relation ordering traversal (class / absolute import path / unqualified-name); `Meta.orderset_class` consumer wiring (promoted out of `DEFERRED_META_KEYS`); the public `Ordering` enum (six members with NULLS positioning); the `order_input_type` resolver-argument helper; finalizer phase-2.5 binding with orphan validation; per-field `check_*_permission` denial gates with active-input-only scope plus active-branch dispatch on `RelatedOrder` branches; row-preserving `Min` / `Max` ordering across to-many paths; omitted fields and explicit `null` directions both contribute no ordering term; clean composition with the shipped filter subsystem, root connection cursor pages, and the optimizer's deliberate per-parent fallback for nested connections carrying `orderBy:`. See [`GLOSSARY.md#orderset`][glossary-orderset].
- `DjangoConnectionField` (new in `0.0.9`) — Relay connection field over a Relay-Node-shaped `DjangoType`: `edges` / `node` / `pageInfo` cursor pagination on Strawberry's native `relay.connection()`, with `filter:` / `orderBy:` arguments derived from the wrapped type's `Meta.filterset_class` / `Meta.orderset_class` sidecars (no hand-written list resolver, no parallel argument declarations) and an opt-in `totalCount` via `Meta.connection = {"total_count": True}` (counted on the post-filter pre-slice queryset, selection-gated, per connection instance). Composition pipeline runs `get_queryset` visibility → `filter` → `orderBy` → default deterministic pk-ordering → optimizer-plan → cursor slice; the field owns its own optimizer cooperation point. `DjangoConnection[T]` is the generic return-type alias. See [`GLOSSARY.md#djangoconnectionfield`][glossary-djangoconnectionfield].
- `DjangoNodeField` / `DjangoNodesField` (new in `0.0.9`) — root Relay refetch fields, bare interface (`node: relay.Node | None = DjangoNodeField()`, `nodes: list[relay.Node | None] = DjangoNodesField()`) and typed (`genre: GenreType | None = DjangoNodeField(GenreType)`) forms; `id: ID!` raw-string arguments decoded server-side via the strategy-aware dispatch; dispatch to the type's `resolve_node` / `resolve_nodes` honoring `get_queryset`; `null` for hidden/missing/uncoercible-pk ids (no existence leak), `GraphQLError` with `extensions={"code": "GLOBALID_INVALID"}` for malformed ids; `nodes` is per-type-batched, order-preserving, with `null` holes and duplicate-id support. See [`GLOSSARY.md#djangonodefield`][glossary-djangonodefield].
- relation-as-Connection upgrade + `Meta.relation_shapes` (new in `0.0.9`) — every Relay-Node-shaped type's many-side relations whose target is also Relay-Node-shaped gain a `<field>Connection` sibling by default (`"both"`); `Meta.relation_shapes = {"<field>": "list" | "connection" | "both"}` narrows per relation; synthesized at finalization Phase 2.5 reusing the shipped connection machinery (per-target connection classes, sidecar `filter:` / `orderBy:` arguments, target-driven `totalCount`). See [`GLOSSARY.md#metarelation_shapes`][glossary-metarelation_shapes].
- `testing.relay` helpers (new in `0.0.9`) — `django_strawberry_framework.testing.relay.global_id_for(type_cls, id)` (the strategy-aware encoded `GlobalID` a finalized Relay-Node-shaped type emits) and `decode_global_id(gid)` (public re-export of the decode dispatch). See the [`GLOSSARY.md#djangonodefield`][glossary-djangonodefield] cross-refs (the helpers have no own entry; the spec does not create one).
- `Meta.nullable_overrides` / `Meta.required_overrides` (new in `0.0.9`) — two tuple-set `Meta` keys that decouple a non-relation field's GraphQL nullability from its Django column (`T!`→`T` or `T`→`T!`) without an `AlterField` migration or a consumer-authored annotation. Validated at type-creation (unknown / excluded / consumer-authored / relation / Relay-suppressed-pk targets and the both-sets collision raise `ConfigurationError`); the scope is non-relation model fields — scalar columns and, as of `0.0.11`, the file/image output objects — and the override flips a choice field's generated enum nullability for free. See [`GLOSSARY.md#metanullable_overrides`][glossary-metanullable_overrides].
- `manage.py inspect_django_type` (new in `0.0.9`) — diagnostic command printing a finalized `DjangoType`'s per-field GraphQL resolution table (Django field → resolved GraphQL type → nullability → converter row). Dispatches the positional arg by shape (dotted path vs unique bare-name registry lookup) and accepts `--schema <selector>` to register + finalize on a cold CLI process. See [`GLOSSARY.md#schema-introspection-management-command`][glossary-inspect-django-type].
- `apply_cascade_permissions` / `aapply_cascade_permissions` (new in `0.0.10`) — cascade-permissions subsystem: one call inside a type's `get_queryset` cascades that type's visibility across its single-column forward FK / OneToOne edges, dropping parent rows whose targets a target type's own `get_queryset` hides. Four invariants (`ContextVar` cycle guard, single-column forward scope, nullable-FK preservation, caller-alias pinning), loud `fields=` validation, a sync + `sync_to_async` async pair, and zero added query round-trips (the `__in` subqueries compile into the caller's single `SELECT`); composes with the shipped `check_<field>_permission` gates, connections, node refetch, and list fields through their existing seams. Exported from the package root. See [`GLOSSARY.md#apply_cascade_permissions`][glossary-apply-cascade-permissions].
- mutations + auto-generated `Input` types (new in `0.0.11`) — the package's write side: a `DjangoMutation` base configured through a nested `class Meta` (`model` + `operation` ∈ `{"create", "update", "delete"}`, the DRF shape, not Strawberry decorators), exposed on the schema's `Mutation` type through the `DjangoMutationField` factory (the write-side sibling of `DjangoConnectionField`). Auto-generated `<Model>Input` (each editable field required only when it has no usable Django `default` / `blank` / `null`, else optional) / `<Model>PartialInput` (all-optional) derive from `Meta.model` reusing the read-side scalar / relation converters (forward FK / OneToOne → `<field>_id`, M2M → `list[id]`); the shared `FieldError` envelope (`field` + `messages`) surfaces `full_clean()` validation through a `<Name>Payload` carrying the mutated object in a uniform `node` / `result` slot plus `errors: list[FieldError]!`. Write authorization is a separate, DRF-shaped contract — `Meta.permission_classes` (default `[DjangoModelPermission]`, the Django `add` / `change` / `delete` model perms) plus an overridable `check_permission` — kept distinct from `get_queryset` visibility (can-view ≠ can-write). `update` / `delete` lookups run through the target type's `get_queryset` (a hidden row is not-found, no existence leak); the post-write row is re-fetched and optimizer-planned (`select_related` / `prefetch_related`, no `.only()` under the mutation operation). Sync + async. As of the `0.0.14` work on `main`, generated mutations require the schema to be built as `DjangoSchema` (its execution context holds each mutation's transaction open through GraphQL response completion — an unserializable payload rolls the write back; plain `strawberry.Schema` execution fails before writing), every model-backed flavor locks its target and relation rows by default (`Meta.select_for_update`, base-manager `FOR UPDATE` under a visibility pk subquery; explicit `False` opts out), and a row that disappears mid-operation returns the in-band `conflict` `FieldError` instead of a silent success. `DjangoMutation` / `DjangoMutationField` / `FieldError` / `DjangoModelPermission` / `DjangoSchema` / `DjangoMutationExecutionContext` are exported from the package root. See [`GLOSSARY.md#djangomutation`][glossary-djangomutation].
- `Upload` scalar + file/image field mapping (new in `0.0.11`) — the `Upload` scalar (Strawberry's built-in, re-exported from the package root) and the generated `DjangoMutation` input mapping of `FileField` / `ImageField` editable columns → `Upload` (required per the shipped per-field rule, `Upload | None` on `blank` / `null`); on the read side, `FileField` / `ImageField` columns convert to the structured `DjangoFileType` / `DjangoImageType` output objects — the object itself is nullable by default in the generated SDL regardless of the Django column's `null` / `blank` (an empty stored file resolves to `null`; `required_overrides` opts into a non-null `DjangoFileType!`), with `name` non-null and `path` / `size` / `url`, plus image `width` / `height`, nullable and storage-safe inside it — via the new `FIELD_OUTPUT_TYPE_MAP`. This is the scalar and generated mutation-field typing — not full multipart HTTP upload ergonomics, which await the `0.0.14` `TestClient`. `Upload` / `DjangoFileType` / `DjangoImageType` are exported from the package root. See [`GLOSSARY.md#upload-scalar`][glossary-upload-scalar].
- form-based mutations (new in `0.0.12`) — the form-validated write flavor on the same `class Meta` surface: `DjangoModelFormMutation` (a `ModelForm`, subclassing `DjangoMutation` via the `_resolve_model` seam so it returns the post-save object in the uniform `node` / `result` slot) and `DjangoFormMutation` (a plain model-less `Form` sibling — its own metaclass, returning the pinned `ok: Boolean!` + `errors: [FieldError!]!` payload, with a `perform_mutate` write hook), both declared through `Meta.form_class` (+ optional `fields` / `exclude`). The input shape is derived from the form's declared fields via `forms/converter.py` (reusing the read-side scalar / choice-enum / `Upload` converters where the field types overlap, so a plain `Form` can declare fields a model does not have), and `form.errors` maps onto the same frozen `FieldError` envelope (the form's `NON_FIELD_ERRORS` bucket keyed to `"__all__"`). Relation ids are visibility-checked through the related primary type's `get_queryset` before the form runs; the `ModelForm` `update` locates its row through the target type's `get_queryset` (a hidden row is not-found, no existence leak) and re-fetches optimizer-planned. Sync + async, inside the one `transaction.atomic()` boundary. Both bases are exported from the package root. See [`GLOSSARY.md#djangoformmutation`][glossary-djangoformmutation].
- DRF serializer mutations (new in `0.0.13`) — `SerializerMutation`, the serializer-validated write flavor via `Meta.serializer_class` over a DRF `Serializer` / `ModelSerializer`. It rides the shipped `DjangoMutation` write pipeline and the same frozen `FieldError` envelope (a `serializer.is_valid()` field error keys to its field; the serializer's non-field errors key to `"__all__"`); `djangorestframework` is a **soft** dependency — `import django_strawberry_framework` and `from django_strawberry_framework import *` both stay DRF-free, and `SerializerMutation` is a lazy root export resolved through the package `__getattr__`, deliberately **not** in `__all__`. See [`GLOSSARY.md#serializermutation`][glossary-serializermutation].
- session-auth mutations (new in `0.0.13`) — opt-in `login` / `logout` / `register` field factories plus a `current_user` query helper, imported from the `django_strawberry_framework.auth` submodule (**no** package-root re-export — they are absent from `__all__`). All ride the shared `FieldError` envelope; `register` is a `DjangoMutation` rider adding `validate_password` + `set_password` over the shipped create pipeline (the plaintext password is never persisted). The family defaults to `AllowAny` — the documented inversion of the write family's deny-by-default `DjangoModelPermission`, since login/register must serve the anonymous caller — with per-schema `permission_classes=` still available on every factory. Session-transport only (no Channels). The user type's field selection is the authenticated read surface, so exclude `password` and privilege columns from it. See [`GLOSSARY.md#auth-mutations`][glossary-auth-mutations].
- Channels ASGI router (new in `0.0.14`, `DONE-041`) — `DjangoGraphQLProtocolRouter`, imported from `django_strawberry_framework.routers` (a lazy PEP 562 submodule export, never a package-root export): a `channels.routing.ProtocolTypeRouter` subclass serving GraphQL on both HTTP and WebSocket in one import, with `AuthMiddlewareStack` (sessions + `scope["user"]` on both protocols) and the WebSocket `AllowedHostsOriginValidator` composed in — constructor-compatible with upstream `strawberry_django.routers.AuthGraphQLProtocolTypeRouter`, so a migrant changes exactly the import line. `channels` is the package's second **soft** dependency (after `djangorestframework`): importing the package or the submodule stays channels-free, and only symbol access raises the install-hint `ImportError`. See [`GLOSSARY.md#djangographqlprotocolrouter`][glossary-djangographqlprotocolrouter].
- debug-toolbar middleware (new in `0.0.14`, `DONE-042`) — `DebugToolbarMiddleware`, imported from `django_strawberry_framework.middleware.debug_toolbar` (the leaf-module import is the opt-in boundary, never a package-root export): a subclass of the stock `debug_toolbar.middleware.DebugToolbarMiddleware` that teaches `django-debug-toolbar`'s SQL panel to see Strawberry `/graphql/` traffic — `process_view` tags Strawberry-view requests and `_postprocess` appends the GraphiQL bridge template to the IDE's HTML and injects a `debugToolbar` panel payload (per-panel `title` / `nav_subtitle` + the toolbar `requestId`) into JSON operation responses (`IntrospectionQuery` skipped). `django-debug-toolbar` is the package's third **soft** dependency (after `djangorestframework` and `channels`): importing the package stays toolbar-free and only importing this leaf raises the install-hint `ImportError`, while omitting `"debug_toolbar"` from `INSTALLED_APPS` raises `ImproperlyConfigured` at leaf import. See [`GLOSSARY.md#debug-toolbar-middleware`][glossary-debug-toolbar-middleware].

**Coming next — remaining alpha (`0.0.14`):**
- `0.0.14` — test-client helper, response-extensions debug middleware (the Channels ASGI router and debug-toolbar middleware halves of `0.0.14` already landed as `DONE-041` and `DONE-042`, above)

**`0.1.0`** — beta release: feature parity with `graphene-django` and `strawberry-graphql-django` (alpha → beta cut-over).

**Beta (`0.1.x`)** — Layer-3 depth on the road to `1.0.0`:
- `0.1.1` — `FieldSet` (declarative `fields_class`)
- `0.1.2` — `Meta.search_fields` + Postgres full-text-search filter primitives
- `0.1.3` — `AggregateSet` (`Sum` / `Count` / `Avg` / `Min` / `Max` / `GroupBy`, `aggregate_class`) + Layer-3 `Meta`-key promotion
- `0.1.4` — stable choice-enum naming overrides
- `0.1.5` — fakeshop GraphQL schema activation end-to-end + product-catalog Layer-3 HTTP tests
- `0.1.6` — migration and adoption guides

**`1.0.0`** — stable release: full `django-graphene-filters` depth + **API freeze** (strict SemVer applies from `1.0.0` forward).

## Schema setup boundary

`finalize_django_types()` must run once during single-threaded import/schema setup, after every module that defines `DjangoType` classes has been imported and before `strawberry.Schema(...)` is constructed. The most common failure mode is forgetting to import a module that contains a related type before finalization.

Recommended:

```python
from django_strawberry_framework import finalize_django_types, strawberry_config

from myapp import types as _types  # noqa: F401

finalize_django_types()
_optimizer = DjangoOptimizerExtension()
schema = strawberry.Schema(query=Query, config=strawberry_config(), extensions=[lambda: _optimizer])
```

Wrong order:

```python
_optimizer = DjangoOptimizerExtension()
schema = strawberry.Schema(query=Query, config=strawberry_config(), extensions=[lambda: _optimizer])
finalize_django_types()
```

The second form constructs the Strawberry schema before relation targets are finalized, so exposed relations whose target type was still pending cannot be resolved into concrete `DjangoType`s.

### `DjangoSchema` is required for generated mutations

A schema that exposes any generated mutation (`DjangoMutationField` over a `DjangoMutation` / `DjangoModelFormMutation` / `DjangoFormMutation` / `SerializerMutation`) must be constructed as `DjangoSchema`, not plain `strawberry.Schema`:

```python
from django_strawberry_framework import DjangoSchema

schema = DjangoSchema(
    query=Query,
    mutation=Mutation,
    config=strawberry_config(),
    extensions=[lambda: _optimizer],
)
```

`DjangoSchema` installs `DjangoMutationExecutionContext`, which holds each generated top-level mutation field's `transaction.atomic()` open **through GraphQL response completion**: a payload that cannot be serialized (a non-nullable field completing `null`, a corrupt scalar) rolls the write back instead of committing behind a `data: null` response. Under plain `strawberry.Schema` the write pipeline refuses to run — the mutation fails with a `ConfigurationError` naming this requirement before any database work. Serial top-level mutation fields in one operation each get an independent transaction, per the GraphQL spec's serial-mutation semantics. Query-only schemas are unaffected. A consumer with its own execution context subclasses `DjangoMutationExecutionContext` and passes it via `execution_context_class=`.

## Session-auth deployment boundary

The opt-in `login_mutation()` authenticates and establishes a Django session, but the framework does **not** provide brute-force throttling, lockout, or rate limiting. Attach a consumer-owned `permission_classes` gate or middleware before exposing login publicly. The login permission gate receives the attempted username for account-scoped controls but never receives the password.

CSRF enforcement also belongs to the HTTP transport: it depends on the Strawberry view and Django middleware around the GraphQL endpoint, not the auth field resolver. Keep Django's CSRF protection enabled for cookie-backed session authentication, follow [Django's CSRF guidance][django-csrf], and exercise the deployed GraphQL view with `Client(enforce_csrf_checks=True)` as described by [Django's test-client CSRF checks][django-test-client-csrf].

`register_mutation()` derives its input from the user model's `USERNAME_FIELD`, distinct `REQUIRED_FIELDS`, and `password`. It refuses to auto-expose Django's account-control fields (`is_active`, `is_staff`, `is_superuser`, `groups`, and `user_permissions`); custom registration flows must initialize privileges and activation state in server-owned logic.

## Form mutation contracts

The two form mutation bases intentionally return different payload shapes. A model-backed `DjangoModelFormMutation` returns the same object payload as `DjangoMutation`: the saved object in `node` or `result`, plus `errors`. A model-less `DjangoFormMutation` has no object slot and always returns exactly `ok: Boolean!` and `errors: [FieldError!]!`; validation or write failure sets `ok` to `false`, while success sets it to `true`. See the [`DjangoFormMutation`][glossary-djangoformmutation] and [`DjangoModelFormMutation`][glossary-djangomodelformmutation] contracts.

A `DjangoModelFormMutation` update is partial only at the GraphQL input boundary. The resolver reconstructs omitted fields from the current instance and binds a complete `ModelForm`, so Django revalidates every declared form field. If an untouched stored value no longer satisfies the form -- for example, after a validator is tightened -- the mutation fails without writing the requested change. Send a valid replacement for that field in the same request; if `Meta.fields` / `Meta.exclude` removed it from the generated input, broaden the mutation input or repair the row out of band first.

## Model mutation write contracts

`DjangoMutation` authorizes before decoding relation IDs. For updates and deletes,
the target row is first located through the target type's `get_queryset`; a hidden
row is therefore not-found before authorization can reveal that it exists.
Permission denial then raises a top-level `GraphQLError` and nulls the mutation
field. It is not returned in the payload's typed `errors` list, which is reserved
for relation decoding, validation, and database-constraint failures.

Relation visibility exists only when the related model has a registered primary
`DjangoType`. Global IDs and raw primary keys for such targets are resolved through
that type's `get_queryset`, so hidden and missing rows produce the same field-keyed
relation error. If the related model has no registered primary type, there is no
GraphQL visibility policy to apply: raw primary keys are existence-checked through
the model's default manager, and any existing row may be attached. Do not assume
that a target model's application-level visibility rules protect a relation unless
those rules are implemented by its registered primary type.

Many-to-many inputs use replace semantics. Providing a list on create or update
sets the complete membership to exactly that list; omitted members are removed.
An empty list clears the relation, omitting the field leaves it unchanged on
update, and explicit `null` is a field error. There is no additive `add` / `remove`
input shape.

After a successful write, the payload object is re-fetched through the model's
default manager rather than the target type's visibility-scoped queryset. This is
intentional: the actor can round-trip the row it just wrote. Consequently, an
update that moves a previously visible row outside the actor's `get_queryset`
scope still returns that row in the success payload; subsequent read operations
apply normal visibility and may no longer return it.

### Concurrency: row locks and the `conflict` error

Every model-backed mutation flavor defaults to `Meta.select_for_update = True` (as of the `0.0.14` work on `main`): the update / delete locate and every FK / M2M relation-target check acquire a `SELECT ... FOR UPDATE` inside the write transaction. The lock rides the model's **base manager** constrained by the visibility queryset reduced to a primary-key subquery — never `select_for_update()` attached to a custom `get_queryset` result, whose joins, unions, or annotations could not legally carry the lock. On a backend without `FOR UPDATE` support (SQLite) Django skips the clause silently. An explicit `Meta.select_for_update = False` opts into weaker concurrency.

A row that disappears mid-operation anyway — a concurrent delete under the opt-out or on a lockless backend — is never a silent success or a resurrecting insert. Direct model updates save with `force_update=True`; a zero-row forced update, a delete whose target row was already gone, and a missing post-write re-fetch all return the in-band `FieldError` on `id` with code `conflict` (retryable, distinct from `not_found`), and the transaction rolls back. Every error envelope marks the transaction for rollback, so visibility-hook or custom-`delete()` side effects never outlive a failed operation.

### One write alias; no distributed transactions

The database router's write alias is resolved once per operation and the whole pipeline — locate, relation visibility checks, validation, the write, M2M assignment, the re-fetch, and rollback — is pinned to it. A custom `get_queryset` hook that explicitly re-routes to a different alias (`.using("other")`) fails closed with a `ConfigurationError`, as does an instance-sensitive router whose answer changes once the row is known: the package offers single-transaction atomicity on one alias and will not pretend to coordinate a cross-database write.

### Authorization is a point-in-time decision

`check_permission`, each `Meta.permission_classes` entry, and `user.has_perm` run exactly once per operation — after the target row is located and locked, before relation decoding — and must return an actual `bool` (a truthy non-bool return is a `ConfigurationError`, never a silent allow). The decision is point-in-time: a permission revoked by a concurrent transaction after the check is not re-observed. A custom policy that needs revocation-linearizable behavior must lock or re-read its own policy rows inside the transaction from its permission class. Side-effectful hooks are not re-run. Because the transaction now spans response completion, any external effect (email, webhook, queue publish) triggered by a mutation must be scheduled with `transaction.on_commit(...)`, never fired inline.

## Serializer mutation contracts

`SerializerMutation`'s construction hooks are hardened (an intentional pre-`1.0` security break, no compatibility shim): `get_serializer_kwargs` is **constructor-only**. The framework builds the serializer's `data` itself from the decoded client input plus the declared injection, locates and authorizes the update `instance`, injects `partial=True` on update, and sets `context["request"]` (the authorized actor's request) and `context["write_alias"]` (the pinned write alias) — all five are framework-owned. Consumer hooks never receive the live located instance: every hook (`get_serializer_kwargs`, `get_serializer_injected_data`, `get_serializer_save_kwargs`) takes a frozen `SerializerHookContext(operation, write_alias, instance_pk)` plus an **immutable data view** — dicts as read-only mapping proxies, lists and tuples as tuples, sets as frozensets, `bytearray` as `bytes`, and each uploaded file replaced by a frozen `UploadMetadata(name, size, content_type)` descriptor, so the stateful authoritative upload objects reach only the serializer's own validation. Genuinely-immutable scalar leaves (str, int, `Decimal`, `datetime`, `UUID`, …) pass through by reference; an opaque, possibly-mutable leaf with no immutable rendering **fails closed** with a `ConfigurationError` rather than being aliased under a false promise of immutability (a hook could otherwise mutate it and thereby mutate the authoritative data). The reserved returns are checked by omission-sentinel plus object identity, never deep equality (a deep comparison recurses on deep valid payloads, and a plain `pop` default would make an explicit `None` indistinguishable from omission) — a returned `data` must be omitted or the exact frozen object the hook received, and *any* returned `instance` key is rejected outright (the framework injects the authorized row itself); anything else — an explicit `data=None`, a rebuilt-equal copy, any `partial`, a different `context["request"]` object, a conflicting `context["write_alias"]` — is a `ConfigurationError` before any write. The previous behavior let an override replace the located, authorized row or the decoded client data, which was an authorization bypass.

Narrowing a required field out of a create input pairs `Meta.injected_fields` with `get_serializer_injected_data(info, *, data, hook_context)`: its returned keys must exactly match the declaration (missing or extra keys fail loud), and every declared field must be writable on the same schema-time basis used by input generation (`read_only` and `HiddenField` entries are rejected). An injected field must also be narrowed out of the GraphQL input. `get_serializer_save_kwargs` may carry **only non-model custom arguments**: a key colliding with the serializer's actual `validated_data` (renamed `source=`, injected, defaulted, and `HiddenField` keys included) or naming *any* model field is rejected — model-field injection goes exclusively through the declared, validated, visibility-checked `Meta.injected_fields` channel. A writable serializer `source` must be unique across the whole write surface (input fields and `Meta.injected_fields`): the shared collision detector rejects two differently-named fields feeding one model attribute at class creation, since DRF resolves the collision last-write-wins and an injected value could silently replace the client's. A whole-object `source="*"` writable field is rejected outright — it owns no single key, so DRF merges its returned mapping into `validated_data` and it could overwrite any client or injected key; the model-column converter only catches an *exposed* star field, so the runtime-field guard additionally rejects narrowed-out, `HiddenField`, or defaulted `source="*"` fields that never reach the converter. The frozen data views are built iteratively: client-controlled JSON nesting depth cannot crash the pipeline with a `RecursionError`, a cyclic container fails loud as a `ConfigurationError` instead of looping forever, and a merely shared (diamond) reference freezes once and stays shared. The DRF error flattener is iterative, cycle-rejecting, and budget-capped the same way — pathological error fan-out ends in a single `"__all__"`-keyed `truncated` marker.

The pipeline is phase-separated. Every consumer-reachable phase — the permission hook, relation decode, validation with author validators, the hooks, and save-kwargs preparation — is **database-read-only**: the pipeline-wide alias guard (shared by all three write flavors, delete included) rejects every SQL statement on a non-pinned configured connection with no read/write classification (a lexical keyword test is bypassable via leading SQL comments, PostgreSQL `EXPLAIN ANALYZE UPDATE`, and write-capable functions invoked through `SELECT`), and rejects write-shaped SQL on the *pinned* connection outside the flavor's write phase (there the conservative comment-stripped allow-list is phase-ordering enforcement, not the atomicity boundary — a false negative still rolls back with the pinned transaction). Writes are permitted only inside the flavor's save step (`serializer.save()`, `Model.save()` + the M2M assignment, `form.save()`, `instance.delete()`); side effects belong in `transaction.on_commit(...)`. The guard is thread-scoped, and grants exactly one narrow, phase-scoped exception: a dedicated authorization phase wraps only the single permission-evaluation call and permits statements on the explicitly identified auth aliases (the router's read answer for the user model, `auth.Permission` / `Group`, and `contenttypes`), so a divergent read/write router that keeps auth off the write alias can resolve the user and permission set. The boundary there is transactional and database-enforced, not lexical — each non-pinned auth alias runs inside a transaction placed in a backend-enforced read-only mode (PostgreSQL `SET TRANSACTION READ ONLY`, SQLite `PRAGMA query_only` — read and restored to its prior value on exit, so a pre-existing setting or an enclosing barrier survives) and unconditionally rolled back when the phase ends, so an *ordinary* write a permission backend attempts on it is refused by the database itself and discarded on rollback. Forced rollback alone is not a portable barrier even against ordinary writes — non-transactional tables and implicitly-committed DDL can escape it — so a backend that cannot provide the read-only guarantee fails closed (the pipeline raises rather than route auth there), with the forced rollback kept as additional containment. This is *not* a complete sandbox against a hostile permission backend: backend read-only mode is a high-level restriction that still permits side-effecting functions (PostgreSQL `nextval`/`setval` advance a sequence and are never rolled back; a session-scope advisory lock outlives the transaction). The security model therefore **trusts permission backends to perform reads only** — the barrier contains ordinary/accidental writes as defense-in-depth, not deliberate volatile side effects; a deployment that cannot make that trust assumption must give divergent-router authorization genuinely capability-restricted database credentials. The exception closes the instant authorization returns — decode, hooks, and validation cannot reach the auth alias, and evaluating permissions there fills the per-user cache as a side effect. It is gated on the mutation declaring permission classes: the explicit `permission_classes = []` opt-out grants no auth-alias access and never resolves the lazy user. `serializer.save()` runs inside its own savepoint, rolled back *before* a caught DRF/Django `ValidationError` or `IntegrityError` converts into the `FieldError` envelope — a custom `save()` that wrote rows and then raised leaves no partial write.

The authorized target is protected end to end. Its canonical pk **and** loaded concrete field values are snapshotted immediately after the locked locate — before the permission hook, the first consumer-controlled code, can touch the mutable instance — and published on the write-pipeline context; immediately before the save, the serializer flavor rejects any in-memory drift of the located row (permission methods, hooks, and validators must treat the target as read-only). Mutable container values (`JSONField`/`ArrayField`) are snapshotted as iterative structural fingerprints and a `FieldFile` by its database-relevant `name` string — not aliased by reference — so an in-place mutation (`instance.data["x"] = …`, `instance.file.name = …`) on the same object is still detected as drift. Pk equality everywhere goes through the model pk field's own `to_python` canonicalization, never string comparison (a `UUID` pk spells the same row several ways; a forged pk of the wrong shape reads as a mismatch). After authorization — never before — the write step snapshots the target's write-surface direct-M2M memberships. Every top-level and nested DRF relation field's queryset is scoped to the author's own queryset AND the target type's visibility, pinned to the operation's write alias, and locked when `Meta.select_for_update` locks; queryset-backed DRF validators are shallow-copied per request and pinned recursively as well. On top of that scoping sits the **relation-intent ledger**: each relation field's `run_validation()` return (top-level and nested, one record per `many=True` list item, custom `pk_field` implementations included) is recorded before field- or object-level validators can replace it, and the final `validated_data` must carry those exact objects by identity — covering renamed sources, injected fields, single relations, lists (length + pairwise identity, so DRF's duplicate and explicit-empty-list set semantics pass through), and nested paths; a validator may reject or pop a relation, never substitute or inject one. After the save, the returned top-level row is **attested against the database**: every supplied FK/OneToOne column is read back and must hold the validated target's pk, every supplied M2M must match the validated pk set (explicit `[]` means cleared; duplicates collapse per DRF `.set()` semantics), and every omitted partial-update M2M on the write surface must equal its pre-save snapshot — a custom `create()`/`update()` that ignored or replaced validated relations is a loud `ConfigurationError`, never a plausible payload (arbitrary same-alias behavior inside custom write code otherwise remains trusted). The serializer write phase additionally runs under a thread-scoped write witness recording every actual write of the backing model with a pk snapshot taken at the `post_save` signal; the `serializer.save()` result must be `serializer.instance` itself, a persisted instance of the backing model (non-null pk, not `_state.adding`) living exactly on the pinned alias, matching a witnessed `created=True` write on create or the immutable authorized-pk snapshot on update (enforced again by a flavor-independent backstop, and by the delete branch for pk drift during authorization). Returning the existing instance without saving it is rejected rather than reported as a successful no-op. Custom serializer code that queries should use `context["write_alias"]`.

## Filter membership semantics

For `ListFilter` and Relay-aware `GlobalIDMultipleChoiceFilter` membership lookups, an explicit empty list means membership in the empty set and therefore matches no rows. Omitting the filter or sending `null` remains the no-constraint form. An excluded empty membership predicate matches every row.

Generated integer `in` filters coerce every member through the Django model field before binding it to the database. Members that fail model-field coercion or range validation are discarded; a mixed list filters on its valid members, while a non-empty list whose members all fail validation matches no rows. This prevents an invalid or out-of-range integer from reaching the backend without widening an all-invalid restrictive filter into an unfiltered query.

Generated flat filter paths that cross a reverse foreign key or many-to-many relation automatically apply `distinct`, so multiple matching related rows cannot duplicate a parent in list or connection results.

## Development debug responses

### django-debug-toolbar middleware

The optional `DebugToolbarMiddleware` integrates Strawberry's Django view with
`django-debug-toolbar`. Install `django-debug-toolbar>=7.0.0`, then wire the
toolbar's normal prerequisites with one package-specific replacement:

```python
from debug_toolbar.toolbar import debug_toolbar_urls

INSTALLED_APPS = [
    # ...
    "django.contrib.staticfiles",
    "debug_toolbar",
    "django_strawberry_framework",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django_strawberry_framework.middleware.debug_toolbar.DebugToolbarMiddleware",
    # ...
]

INTERNAL_IPS = ["127.0.0.1"]

urlpatterns = [
    # ...
]
urlpatterns += debug_toolbar_urls()
```

The package middleware **replaces**
`"debug_toolbar.middleware.DebugToolbarMiddleware"`; never list both, because
the subclass already runs the stock toolbar pipeline and stacking them runs it
twice. Keep `debug_toolbar_urls()` in the URLconf while the middleware is
active: the stock postprocessor reverses its panel routes for every processed
response, so omitting them raises `NoReverseMatch` rather than merely breaking
panel links.

The integration inherits the stock toolbar's `DEBUG`,
`SHOW_TOOLBAR_CALLBACK`, and `INTERNAL_IPS` gating. Injection is view-scoped,
not GraphiQL-client-scoped: whenever that gate enables the toolbar, every JSON
response from a Strawberry Django view except an `IntrospectionQuery` gains a
top-level `debugToolbar` key, including responses to programmatic clients. The
GraphiQL bridge removes the key only inside the IDE. Consequently this remains
a development-only integration; production exposure requires the stock toolbar
to be misconfigured to run there. If a tagged response declares
`application/json` but contains malformed or undecodable content, the package
performs no package-specific body or `Content-Length` rewrite.

See the [Debug-toolbar middleware glossary entry][glossary-debug-toolbar-middleware]
for the complete import, template, and failure-mode contract.

### GraphQL response extension

`DjangoDebugExtension` is an opt-in development diagnostic imported from `django_strawberry_framework.extensions`. Pass the **class**, not a constructed instance, in Strawberry's `extensions=` list:

```python
from django_strawberry_framework.extensions import DjangoDebugExtension

_optimizer = DjangoOptimizerExtension()
schema = strawberry.Schema(
    query=Query,
    config=strawberry_config(),
    extensions=[
        lambda: _optimizer,
        DjangoDebugExtension,
    ],
)
```

Strawberry constructs the class with zero arguments for every operation, keeping its capture state operation-local. A pre-constructed instance is deprecated engine usage and would share the engine-assigned execution context and completed payload across operations; the optimizer intentionally uses the different singleton-in-a-factory shape to retain its plan cache.

Executed operations add `extensions["debug"]` with `sql` and `exceptions` lists. The extension brackets every configured Django database connection separately and aggregates rows from every alias used during the operation into that one `sql` list; each row's `alias` and `vendor` identify its source. Rows retain per-connection log order and the per-connection groups follow Django's `connections.all()` order, so the combined list is not a cross-database execution timeline. An alias the operation never uses contributes no rows and is not forced open.

Never enable this extension on an internet-facing production schema: it returns interpolated SQL values and unmasked exception messages and tracebacks. See the [`DjangoDebugExtension` glossary entry][glossary-djangodebugextension] for the complete payload and lifecycle contract.

## Testing GraphQL endpoints

Import the sync or async HTTP helper from `django_strawberry_framework.testing`. Both drive
Django's in-process test client, decode the GraphQL response, and return a typed
`Response` carrying `errors`, `data`, `extensions`, and the raw Django response:

```python
from django_strawberry_framework.testing import TestClient


def test_items():
    response = TestClient().query("{ allItems(first: 1) { edges { node { name } } } }")

    assert response.errors is None
    assert response.response.status_code == 200
```

Endpoint selection follows this precedence order:

1. Per-call `query(..., url=...)`.
2. `TestClient(path=...)` / `AsyncTestClient(path=...)`.
3. `GraphQLTestMixin.GRAPHQL_URL` for the unittest family.
4. `DJANGO_STRAWBERRY_FRAMEWORK["TESTING_ENDPOINT"]`.
5. `"/graphql/"`.

The constructor and class-attribute rungs belong to their respective client flavors; both
outrank the project setting, and a per-call URL outranks every stored choice without mutating
it.

The two flavors intentionally have different error-assertion defaults. `TestClient.query()`
and `AsyncTestClient.query()` default to `assert_no_errors=True` and raise `AssertionError`
when the GraphQL response carries `errors`. `GraphQLTestMixin.query()` defaults to
`assert_no_errors=False`, returning the response so unittest-style tests can call
`assertResponseNoErrors()` or `assertResponseHasErrors()`. Pass the flag explicitly when a
test switches styles.

An endpoint typo is a transport misconfiguration, not a GraphQL error. The client deliberately
does not wrap it: Django returns an HTML 404, then `response.json()` raises `ValueError` naming
the non-JSON `Content-Type`. If the response declares JSON but contains malformed JSON,
`json.JSONDecodeError` surfaces instead. Check the endpoint and URLconf rather than catching
either error as an application-level GraphQL result.

See the [`TestClient`][glossary-testclient] and
[`GraphQLTestCase`][glossary-graphqltestcase] glossary entries for multipart uploads,
authentication brackets, async usage, and the complete unittest-family contract.

## Running the example project

The repository ships with a fakeshop example project that exercises the shipped surface against a real Django app.

```shell
# Apply migrations to the example app
uv run python examples/fakeshop/manage.py migrate

# Start the dev server (admin + GraphiQL at /graphql/)
uv run python examples/fakeshop/manage.py runserver
```

The dev landing page at `/` links to GraphiQL, the admin, and the seed/delete query-param triggers. For the full example walkthrough see [`../examples/fakeshop/README.md`][fakeshop-readme].

### Seeding the example database

The fakeshop example dynamically discovers **all** Faker providers at runtime and seeds the database accordingly. The command is idempotent — it ensures at least N items exist per provider and only creates the shortfall.

```shell
# Ensure 5 items per provider (default)
uv run python examples/fakeshop/manage.py seed_data

# Ensure 50 items per provider
uv run python examples/fakeshop/manage.py seed_data 50

# Delete the first 10 items (and their cascading entries)
uv run python examples/fakeshop/manage.py delete_data 10

# Delete all items and entries
uv run python examples/fakeshop/manage.py delete_data all

# Wipe all four tables (Category, Property, Item, Entry)
uv run python examples/fakeshop/manage.py delete_data everything
```

The same actions are reachable from the admin via query-param triggers — see the dev landing page at `/` for clickable links.

### Test users

Create test users with individual Django `view_*` permissions for exercising `get_queryset` permission branches. Each set creates 6 users: 1 staff, 1 regular (no perms), and 4 per-model permission users (`view_category`, `view_item`, `view_property`, `view_entry`). All share password `admin`. Superusers are never deleted.

```shell
# Create 1 set of test users (6 users)
uv run python examples/fakeshop/manage.py create_users

# Create 3 sets (18 users)
uv run python examples/fakeshop/manage.py create_users 3

# Delete all non-superusers
uv run python examples/fakeshop/manage.py delete_users all

# Delete the first 5 non-superusers
uv run python examples/fakeshop/manage.py delete_users 5
```

### Sharded mode (multi-DB)

The example ships with an additive two-alias layout for exercising multi-database scenarios. Toggle the secondary shard via `FAKESHOP_SHARDED=1`:

```shell
# Materialize the secondary shard SQLite file (idempotent)
FAKESHOP_SHARDED=1 uv run python examples/fakeshop/manage.py seed_shards

# Larger seed for stress testing
FAKESHOP_SHARDED=1 uv run python examples/fakeshop/manage.py seed_shards --count 5000
```

In sharded mode `default` keeps pointing at `db.sqlite3` (same file as single-DB mode) and `shard_b` adds `db_shard_b.sqlite3`. The two modes share the same `default` file, so a single dev workflow (`manage.py seed_data`, etc.) populates the default alias either way; the sharded mode only ADDS the secondary shard. The committed `db_shard_b.sqlite3` ships with a minimal seed via `seed_shards` so the sharded mode works out of the box.

For the cooperation contract these shards run against — explicit `.using()` `_db` preservation, FK-id elision router hints, consumer-provided `Prefetch(queryset=…)` alias round-trips, and strictness-mode behavior under non-default aliases — see [`GLOSSARY.md#multi-database-cooperation`][glossary-multi-database-cooperation].

## Using the package in your own project

If you want to develop against a local checkout of this package from another Django project:

1. Go to the project you want to install the package in.
2. Add `django-strawberry-framework` to your `pyproject.toml` dependencies.
3. Point it at your local checkout:

```toml
# In your project's pyproject.toml
[tool.uv.sources]
django-strawberry-framework = { path = "../django-strawberry-framework", editable = true }
```

Then run:

```shell
uv sync
```

For status, the milestone roadmap, and contributor signposts, see [`../README.md`'s status section][readme-status] and [`../CONTRIBUTING.md`][contributing].

<!-- LINK DEFINITIONS -->

<!-- Root -->
[contributing]: ../CONTRIBUTING.md
[goal]: ../GOAL.md
[readme]: ../README.md
[readme-status]: ../README.md#status
[today]: ../TODAY.md

<!-- docs/ -->
[glossary]: GLOSSARY.md
[glossary-apply-cascade-permissions]: GLOSSARY.md#apply_cascade_permissions
[glossary-auth-mutations]: GLOSSARY.md#auth-mutations
[glossary-debug-toolbar-middleware]: GLOSSARY.md#debug-toolbar-middleware
[glossary-djangoconnectionfield]: GLOSSARY.md#djangoconnectionfield
[glossary-djangodebugextension]: GLOSSARY.md#djangodebugextension
[glossary-djangoformmutation]: GLOSSARY.md#djangoformmutation
[glossary-djangographqlprotocolrouter]: GLOSSARY.md#djangographqlprotocolrouter
[glossary-djangolistfield]: GLOSSARY.md#djangolistfield
[glossary-djangomodelformmutation]: GLOSSARY.md#djangomodelformmutation
[glossary-djangomutation]: GLOSSARY.md#djangomutation
[glossary-djangonodefield]: GLOSSARY.md#djangonodefield
[glossary-filterset]: GLOSSARY.md#filterset
[glossary-graphqltestcase]: GLOSSARY.md#graphqltestcase
[glossary-metaglobalid_strategy]: GLOSSARY.md#metaglobalid_strategy
[glossary-metanullable_overrides]: GLOSSARY.md#metanullable_overrides
[glossary-inspect-django-type]: GLOSSARY.md#schema-introspection-management-command
[glossary-metarelation_shapes]: GLOSSARY.md#metarelation_shapes
[glossary-multi-database-cooperation]: GLOSSARY.md#multi-database-cooperation
[glossary-orderset]: GLOSSARY.md#orderset
[glossary-plan-cache]: GLOSSARY.md#plan-cache
[glossary-relay-node-integration]: GLOSSARY.md#relay-node-integration
[glossary-schema-export-management-command]: GLOSSARY.md#schema-export-management-command
[glossary-serializermutation]: GLOSSARY.md#serializermutation
[glossary-testclient]: GLOSSARY.md#testclient
[glossary-upload-scalar]: GLOSSARY.md#upload-scalar

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->
[fakeshop-readme]: ../examples/fakeshop/README.md

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[django-csrf]: https://docs.djangoproject.com/en/5.2/howto/csrf/
[django-test-client-csrf]: https://docs.djangoproject.com/en/5.2/topics/testing/tools/#the-test-client
