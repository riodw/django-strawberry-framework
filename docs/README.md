# django-strawberry-framework

`django-strawberry-framework` is a DRF-shaped Django integration for Strawberry GraphQL: you declare GraphQL types from Django models with `class Meta` instead of stacking decorators on consumer classes.

This is the how-to guide — install it, wire a schema, read data, write data, deploy it. For the project pitch and the documentation map, start from [`../README.md`][readme]; for contributor workflow, [`../CONTRIBUTING.md`][contributing].

## Installation

```shell
pip install django-strawberry-framework
uv add django-strawberry-framework
```

Add `"django_strawberry_framework"` to `INSTALLED_APPS` so Django's check and signal hooks resolve through the package's `AppConfig`.

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

The optimizer is a module-level singleton wrapped in a factory. That preserves the instance-bound [plan cache][glossary-plan-cache] (Strawberry runs the callable once per request and gets the same instance back) and emits no deprecation warning, because the entry is a callable rather than an instance.

Relation fields may point at target types declared earlier or later; `finalize_django_types()` resolves them all once every `DjangoType` module has been imported.

### Relay Node

Add `Meta.interfaces = (relay.Node,)` to declare a Relay-node-shaped type; the package wires `id: GlobalID!`, the four `resolve_*` defaults, and `is_type_of` injection with no decorators on your class.

```python
from strawberry import relay


class CategoryNode(DjangoType):
    class Meta:
        model = Category
        fields = ("id", "name")
        interfaces = (relay.Node,)
```

The default `GlobalID` payload is the Django model label (`products.item:42`), not the GraphQL type name, so renaming a type does not invalidate cached IDs. `Meta.globalid_strategy` (per type) and `RELAY_GLOBALID_STRATEGY` (schema-wide) select `model` (default), `type`, `type+model` (decoding old type-anchored IDs while emitting model-anchored ones), or a callable encoder.

> **Multiple `DjangoType`s per model under the `model` default.** A model-label payload is shared by every `DjangoType` over that model and always decodes to the model's **primary** type (`Meta.primary`), so a secondary Relay-Node type's IDs refetch as the primary, taking the primary's `get_queryset` scope with them. Finalization warns and names the collapsing secondaries; give a secondary its own identity with `Meta.globalid_strategy = "type"`.

See [the Relay Node integration entry][glossary-relay-node-integration] and [`Meta.globalid_strategy`][glossary-metaglobalid_strategy].

## What just happened?

- `class Meta` tells the package which Django model and fields become a Strawberry type.
- Returning a `QuerySet` from the root resolver gives the optimizer something it can shape.
- `DjangoOptimizerExtension()` walks the selected fields once at the root and applies one ORM plan.
- Nested relations become joins, prefetches, and projections without replacing your queryset.

## Schema setup

`finalize_django_types()` must run once during single-threaded import/schema setup, after every module that defines `DjangoType` classes has been imported and before `strawberry.Schema(...)` is constructed. The most common failure mode is forgetting to import a module that contains a related type before finalization.

```python
from django_strawberry_framework import finalize_django_types, strawberry_config

from myapp import types as _types  # noqa: F401

finalize_django_types()
_optimizer = DjangoOptimizerExtension()
schema = strawberry.Schema(query=Query, config=strawberry_config(), extensions=[lambda: _optimizer])
```

Calling `finalize_django_types()` after the `Schema(...)` construction instead builds the schema before relation targets are finalized, so exposed relations whose target type was still pending cannot resolve into concrete `DjangoType`s.

`manage.py inspect_django_type <type>` prints a finalized type's per-field resolution table when a conversion is not what you expected, and `manage.py export_schema <dotted.path.to.schema>` prints or writes the SDL.

### `DjangoSchema` is required for generated mutations

A schema exposing any generated mutation (`DjangoMutationField` over a `DjangoMutation` / `DjangoModelFormMutation` / `DjangoFormMutation` / `SerializerMutation`) must be constructed as `DjangoSchema`:

```python
from django_strawberry_framework import DjangoSchema

schema = DjangoSchema(
    query=Query,
    mutation=Mutation,
    config=strawberry_config(),
    extensions=[lambda: _optimizer],
)
```

`DjangoSchema` installs `DjangoMutationExecutionContext`, which holds each generated top-level mutation field's `transaction.atomic()` open **through GraphQL response completion**: a payload that cannot be serialized rolls the write back instead of committing behind a `data: null` response. Under plain `strawberry.Schema` the write pipeline refuses to run, failing with a `ConfigurationError` before any database work. Serial top-level mutation fields each get an independent transaction, query-only schemas are unaffected, and your own execution context subclasses `DjangoMutationExecutionContext` and arrives as `execution_context_class=`.

### Production error policy

`DjangoSchema` also resolves a production error policy once at construction and installs the extension that applies it. Under `settings.DEBUG = False` an **unexpected** resolver or hook exception no longer puts its own message on the wire: the client gets `"message": "An unexpected error occurred."` plus an identifier under `extensions.correlationId`, and the original exception and traceback are logged under that identifier through the `django_strawberry_framework` logger at `ERROR`. Deliberate client-facing errors keep their contract, and the rule that decides is structural rather than an allowlist of codes:

| Error shape | Reaches the client as |
|---|---|
| parse / syntax / validation error (no originating exception) | unchanged |
| a raised `GraphQLError` — every framework rejection (`GLOBALID_INVALID`, `RESOURCE_LIMIT_EXCEEDED`, the argument rejections, the `Not authorized to ...` denial) and any you raise yourself | unchanged, `extensions.code` included |
| any other exception escaping a resolver or hook | the policy message + a fresh `correlationId` |

A validation envelope (`FieldError` rows on a mutation payload) is `data`, not an error, and is untouched. Under `settings.DEBUG` the policy is a pass-through. Configure it with `DjangoSchema(error_policy=...)` or the `DJANGO_STRAWBERRY_FRAMEWORK["ERROR_POLICY"]` mapping (the constructor argument wins), and opt out explicitly:

```python
schema = DjangoSchema(
    query=Query,
    error_policy={
        "message": "Something went wrong. Quote the correlation id when you report it.",
        "correlation_extension_key": "traceId",
    },
)

# Opt-out, for a consumer who owns their own masking:
schema = DjangoSchema(query=Query, error_policy={"enabled": False})
```

The extension is **prepended** to `extensions=`, because Strawberry unwinds teardowns LIFO and masking must happen after every extension that reads `GraphQLError.original_error` has had its turn; your own `DjangoErrorPolicyExtension` entry suppresses the prepend and keeps your position. Subscriptions served through the package's ASGI router are covered per event rather than per operation, so every event carries the policy message and its own `correlationId`.

## Reading data

### `DjangoListField` — a plain list

The smallest root field: a non-Relay `list[T]` with no pagination, edges, or page info.

```python
from django_strawberry_framework import DjangoListField


@strawberry.type
class Query:
    all_branches: list[BranchType] = DjangoListField(BranchType)
    some_branches: list[BranchType] = DjangoListField(BranchType, max_rows=50)
```

Outer nullability comes from your annotation: `list[T]` renders `[T!]!`, `list[T] | None` renders `[T!]`. The default resolver pulls `model._default_manager.all()` and applies the type's `get_queryset` in sync and async contexts; your own `resolver=` overrides the body, and a `Manager` or `QuerySet` return still goes through `get_queryset`.

Every list field is row-bounded: the resource policy supplies `max_list_rows` whether or not the field says anything, `max_rows=` narrows it, and `trusted_max_rows=True` is the only way to widen past the policy. Row order is **not** guaranteed unless the query supplies an ordering or the model declares `Meta.ordering`. See [`GLOSSARY.md#djangolistfield`][glossary-djangolistfield].

<!-- TODO(spec-050 slice 5): Replace this complete DjangoListField bullet after
implementation. Pseudocode: enumerate nullable offset/limit, conditional
Meta.orderset_class-derived orderBy under the active name converter, the
get_queryset -> order -> one-window pipeline, returned-row and skip ceilings,
the nonzero-offset active-order rule, async-safe queryset completion, and the
no-pk/no-DISTINCT/unique-final-term contract. Do not claim raw nested windows
or a response envelope. -->

### `DjangoConnectionField` — Relay connections

Over a Relay-Node-shaped type, one line gives you `edges` / `node` / `pageInfo` cursor pagination, plus `filter:` and `orderBy:` arguments derived from the type's `Meta.filterset_class` / `Meta.orderset_class`:

```python
from django_strawberry_framework import DjangoConnection, DjangoConnectionField


@strawberry.type
class Query:
    all_categories: DjangoConnection[CategoryType] = DjangoConnectionField(CategoryType)
    all_items: DjangoConnection[ItemType] = DjangoConnectionField(ItemType)
```

No hand-written list resolver, no parallel argument declarations. `totalCount` is opt-in per type with `Meta.connection = {"total_count": True}`, counted on the post-filter, pre-slice queryset and gated on selection. The pipeline is `get_queryset` visibility, `filter`, `orderBy`, a deterministic pk tiebreaker, the optimizer plan, then the cursor slice; keyset cursors come from `Meta.cursor_field`. See [`GLOSSARY.md#djangoconnectionfield`][glossary-djangoconnectionfield].

Many-side relations on a Relay-Node type whose target is also Relay-Node-shaped render as a `<field>Connection` alone; `Meta.relation_shapes = {"<field>": "list" | "connection" | "both"}` selects per relation, and an opted-in raw list is row-bounded by the resource policy.

### Node refetch

```python
from django_strawberry_framework import DjangoNodeField, DjangoNodesField


@strawberry.type
class Query:
    node: relay.Node | None = DjangoNodeField()
    nodes: list[relay.Node | None] = DjangoNodesField()
    genre: GenreType | None = DjangoNodeField(GenreType)  # typed form
```

The `id:` argument is a raw `ID!` decoded server-side, so the client's claim about which type an id belongs to is never trusted. Resolution honors `get_queryset`: hidden, missing, and uncoercible-pk ids return `null` with no existence leak, while a malformed id raises a `GraphQLError` with `extensions={"code": "GLOBALID_INVALID"}`. `nodes` is per-type batched and order-preserving, with duplicate ids and `null` holes supported. For tests, `django_strawberry_framework.testing.relay` exports `global_id_for(type_cls, id)` and `decode_global_id(gid)`. See [`GLOSSARY.md#djangonodefield`][glossary-djangonodefield].

### Filtering with `FilterSet`

Declare filters the `django-filter` way:

```python
from graphql import GraphQLError

from django_strawberry_framework.filters import FilterSet, RelatedFilter


class CategoryFilter(FilterSet):
    class Meta:
        model = models.Category
        fields = {
            "id": "__all__",
            "name": "__all__",
            "items__name": ["icontains"],
        }

    def check_name_permission(self, request):
        """Only staff may filter by Category.name."""
        user = getattr(request, "user", None)
        if not user or not user.is_staff:
            raise GraphQLError("You must be a staff user to filter by Category name.")


class ItemFilter(FilterSet):
    category = RelatedFilter(CategoryFilter, field_name="category")
    entries = RelatedFilter("EntryFilter", field_name="entries")

    class Meta:
        model = models.Item
        fields = {"id": "__all__", "name": "__all__", "category__name": "__all__"}
```

Name the class on the wrapping type's `Meta.filterset_class` (shown with `orderset_class` below) and every `DjangoConnectionField` over it grows a `filter:` argument. `Meta.fields` takes the dict form or the `"__all__"` shorthand (every concrete lookup valid for that field). `RelatedFilter` traverses relations and accepts a class, an absolute import path, or an unqualified name for circular cases. `check_<field>_permission(self, request)` gates a field and fires only when the input names it. Logical `and` / `or` / `not` operators come with the generated input, and an orphan sidecar is a loud error at finalization.

Three membership rules worth knowing. An explicit empty list on a membership lookup means "in the empty set" and matches no rows, while omitting the filter or sending `null` is the no-constraint form. Generated integer `in` filters coerce every member through the Django model field and discard failures, so an all-invalid list matches no rows rather than widening into an unfiltered query. Generated flat paths crossing a reverse FK or M2M apply `distinct` automatically. See [`GLOSSARY.md#filterset`][glossary-filterset].

### Ordering with `OrderSet`

```python
from django_strawberry_framework.orders import OrderSet, RelatedOrder


class ItemOrder(OrderSet):
    category = RelatedOrder("CategoryOrder", field_name="category")

    class Meta:
        model = models.Item
        fields = ["name", "created_date"]


class ItemType(DjangoType):
    class Meta:
        model = models.Item
        fields = ("id", "name", "category", "entries")
        interfaces = (relay.Node,)
        filterset_class = filters.ItemFilter
        orderset_class = orders.ItemOrder
```

`Meta.fields` is a list, or `"__all__"` for every column-backed field (forward FK columns included, reverse relations and M2M managers excluded). The public `Ordering` enum carries six members with NULLS positioning, `RelatedOrder` mirrors `RelatedFilter` (class, import path, or the unqualified name shown above), the `check_<field>_permission` gates apply on the same active-input-only terms, and `Min` / `Max` ordering across a to-many path is row-preserving. Omitted fields and explicit `null` directions contribute no ordering term. See [`GLOSSARY.md#orderset`][glossary-orderset].

Outside a connection field, wire either sidecar onto a hand-written resolver with the argument helpers:

```python
from django_strawberry_framework.filters import filter_input_type
from django_strawberry_framework.orders import order_input_type


@strawberry.field
def all_patrons(
    self,
    info: strawberry.Info,
    filter: filter_input_type(filters.PatronFilter) | None = None,  # noqa: A002
    order_by: list[order_input_type(orders.PatronOrder)] | None = None,
) -> list[PatronType]:
    queryset = PatronType.get_queryset(models.Patron.objects.order_by("id"), info)
    if filter is not None:
        queryset = filters.PatronFilter.apply_sync(filter, queryset, info)
    if order_by is not None:
        queryset = orders.PatronOrder.apply_sync(order_by, queryset, info)
    return queryset
```

### Nested connection indexing

A nested `<field>Connection`'s `edges { node }` selection is fetched with one windowed `Prefetch` per relation per request rather than one query per parent. The backend is a pluggable strategy — `"windowed"` (default), Postgres `"lateral"`, or `"auto"` — chosen per extension instance with `nested_connection_strategy=` or the `NESTED_CONNECTION_STRATEGY` setting, and overridable for a single field:

```python
from django_strawberry_framework import DjangoType, OptimizerHint


class ShelfType(DjangoType):
    class Meta:
        model = Shelf
        fields = "__all__"
        optimizer_hints = {
            # Force the Postgres LATERAL backend for this field only.
            "books": OptimizerHint.strategy("lateral"),
        }
```

The name is validated when `Meta.optimizer_hints` is built, so a typo raises `ConfigurationError` at import rather than at query time, and the override never enters the plan cache key.

Both backends partition each parent's page by the child connector column and order by the connection's deterministic order, so the database can serve a page **from an index** when a composite index leads with the window's columns: `(connector, order columns..., pk)` for a reverse FK or M2M, `(content_type_id, object_id, order columns..., pk)` for a `GenericRelation`. Direction matters — a B-tree serves the requested order or its full reverse after the equality-constrained prefix, never a partial flip, so `ORDER BY title ASC, id DESC` needs `(shelf_id, title, -id)`. With `settings.DEBUG` on, the optimizer logs a one-time advisory per plan shape naming the recommended index when the model's declared metadata carries no covering one; it claims coverage only for ordinary B-tree shapes and stays silent when it cannot prove absence.

**Single-parent fast path.** Numbering every child of a partition is wasteful when a prefetch runs for exactly one parent, so a default-on optimization detects that case — one parent id, a direct FK, a count-free bounded first page — and runs a plain filtered `LIMIT`, synthesizing row numbers in Python. Every other shape degrades to the identical windowed body: a performance downgrade, never a wrong page. Disable it with `DJANGO_STRAWBERRY_FRAMEWORK["SINGLE_PARENT_FAST_PATH"] = False`, read at fetch time.

### File and image output

`FileField` and `ImageField` columns read as the structured `DjangoFileType` / `DjangoImageType` objects: `name`, `size`, `url`, plus `width` / `height` on images. The object is nullable regardless of the column's `null` / `blank`, so an empty stored file resolves to `null`. The server's absolute filesystem `path` is deliberately **not** in the default output: it is deployment metadata that can carry usernames, release directories, container mounts, and tenant layout, none of which a client needs to render a file. If a selection breaks, it was selecting `path` — either drop it (`url` fetches the file, `name` is the stored key) or opt the column in:

```python
class MediaSpecimenType(DjangoType):
    class Meta:
        model = MediaSpecimen
        fields = ("id", "label", "attachment", "image")
        # `attachment` gains `path`; `image` does not.
        filesystem_path_fields = ("attachment",)
```

The opt-in is per column, so one class shows every path it publishes. The opted-in column's GraphQL type name changes with it (`DjangoFileType` becomes `DjangoFilePathType`, `DjangoImageType` becomes `DjangoImagePathType`) and every other subfield is unchanged, so `{ attachment { name path url } }` ports as written. Naming a column that cannot work raises `ConfigurationError` at type creation rather than silently no-opping. `Meta.nullable_overrides` / `Meta.required_overrides` separately decouple a non-relation field's GraphQL nullability from its Django column without a migration; see [`GLOSSARY.md#metanullable_overrides`][glossary-metanullable_overrides].

## Visibility and permissions

Row visibility is one classmethod, and every surface the package ships routes through it: list fields, connections, node refetch, relation traversal, and the mutation `update` / `delete` locate.

```python
from django_strawberry_framework import DjangoType, apply_cascade_permissions


class ItemType(DjangoType):
    class Meta:
        model = models.Item
        fields = ("id", "name", "category", "entries")
        interfaces = (relay.Node,)

    @classmethod
    def get_queryset(cls, queryset, info):
        user = getattr(getattr(info.context, "request", None), "user", None)
        if user and user.is_staff:
            return queryset
        return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)
```

`apply_cascade_permissions(cls, queryset, info)` (async twin `aapply_cascade_permissions`) cascades this type's visibility across its single-column concrete forward FK and OneToOne edges, dropping parent rows whose targets the target type's own `get_queryset` hides. That is what stops a nested non-null `category { ... }` selection from reaching a row the viewer cannot see, and it adds no round-trips: the `__in` subqueries compile into the caller's single `SELECT`. It fails closed on every boundary that SQL depends on — a recursive graph raises a path-rich `ConfigurationError` (`fields=[]` is the one permitted re-entrant shape), MTI parent links cascade, `GenericForeignKey` and composite forward relations preflight closed. See [`GLOSSARY.md#apply_cascade_permissions`][glossary-apply-cascade-permissions].

The hook's return is treated as untrusted query state. Every framework-owned invocation runs through one hardened boundary that validates the extracted SQL state (concrete model, base table, database alias, and on read surfaces the projection shape) and rebuilds a framework-owned plain `QuerySet` from it; the consumer object's executable behavior is never dispatched, and anything unprovable fails closed with a `ConfigurationError`. Full contract: [the sealed execution queryset entry][glossary-sealed-execution-queryset].

Two narrower gates sit alongside it: `check_<field>_permission(self, request)` on a `FilterSet` or `OrderSet` denies a single filter or ordering field, and `Meta.permission_classes` on a mutation decides who may **write** — a separate contract, because can-view is not can-write.

## Writing data

Three write flavors share one `class Meta` surface, one `FieldError` envelope, and one authorization contract. Each is exposed on the schema's `Mutation` type through the `DjangoMutationField` factory, assigned with **no** class annotation, since the generated payload has no importable name at import time.

Every mutation returns a generated `<Name>Payload` carrying the written object in a uniform slot (`node` for a Relay-Node target, `result` otherwise) plus `errors: [FieldError!]!`, each `FieldError` a `field` path and `messages`. Validation failures populate that envelope and return a null object; a **write-authorization denial is a top-level `GraphQLError`**, never an envelope entry. `Meta.permission_classes` defaults to `[DjangoModelPermission]` (the Django `add` / `change` / `delete` model perms), and an explicit `permission_classes = []` is the deliberate allow-any opt-out.

### Model mutations

```python
from django_strawberry_framework import DjangoMutation, DjangoMutationField


class CreateItem(DjangoMutation):
    class Meta:
        model = models.Item
        operation = "create"


class UpdateItem(DjangoMutation):
    class Meta:
        model = models.Item
        operation = "update"


class DeleteItem(DjangoMutation):
    class Meta:
        model = models.Item
        operation = "delete"


@strawberry.type
class Mutation:
    create_item = DjangoMutationField(CreateItem)
    update_item = DjangoMutationField(UpdateItem)
    delete_item = DjangoMutationField(DeleteItem)
```

`<Model>Input` and `<Model>PartialInput` are generated from `Meta.model` reusing the read-side converters (forward FK / OneToOne become `<field>_id`, M2M `list[id]`, `FileField` / `ImageField` `Upload`); `Meta.fields` / `Meta.exclude` narrow them and `Meta.input_class` / `Meta.partial_input_class` replace them. The pipeline is visibility-scoped locate (update and delete only), authorize, decode relations, `full_clean()`, write, optimizer-planned re-fetch. Authorizing before decoding is deliberate, so a denied caller cannot probe related-object visibility, and locating through `get_queryset` first means a hidden row is not-found rather than forbidden.

Four behaviors are easy to trip over. M2M inputs are **replacements**: a list becomes the complete membership, `[]` clears, omission leaves an update unchanged, explicit `null` is a field error. Relation visibility exists only where the related model has a registered primary `DjangoType`; without one, raw primary keys get existence checks only and any existing row may be attached. The post-write row is re-fetched through the **default manager**, so an update moving a row out of the actor's read scope still returns it. And because the transaction spans response completion, external effects must be scheduled with `transaction.on_commit(...)`.

Every model-backed flavor locks its target and relation rows by default (`Meta.select_for_update`; `False` opts out), and a row that disappears mid-operation returns the in-band `conflict` `FieldError` rather than a silent success. See [`GLOSSARY.md#djangomutation`][glossary-djangomutation] for the full contract, including row locking, the single write alias, and the point-in-time authorization rule.

### Form mutations

Reuse a Django form you already have. `Meta.form_class` (plus optional `fields` / `exclude`) is the whole declaration:

```python
from django_strawberry_framework import DjangoFormMutation, DjangoModelFormMutation


class CreateItemViaForm(DjangoModelFormMutation):
    class Meta:
        form_class = forms.ItemModelForm
        operation = "create"


class SubmitContact(DjangoFormMutation):
    class Meta:
        form_class = forms.ContactForm
        permission_classes = []
```

The two bases return different payloads on purpose. `DjangoModelFormMutation` is a `DjangoMutation` subclass, so it returns the saved object in `node` / `result` plus `errors`, and takes `operation = "create"` or `"update"` (there is no form delete). `DjangoFormMutation` is model-less: no object slot, a payload pinned to `ok: Boolean!` and `errors: [FieldError!]!`, and a `perform_mutate` hook for the side effect. Input shape comes from the form's declared fields, so a plain `Form` can declare fields no model has, and `form.errors` map onto the same envelope keyed under `"__all__"` for non-field errors.

One sharp edge: a `ModelForm` update is partial only at the GraphQL input boundary. The resolver reconstructs omitted fields from the current instance and binds a complete form, so Django revalidates every declared field, and an untouched stored value that no longer satisfies the form blocks the requested change. Send a valid replacement in the same request, or repair the row out of band. See [`DjangoFormMutation`][glossary-djangoformmutation] and [`DjangoModelFormMutation`][glossary-djangomodelformmutation].

### Serializer mutations

If your validation already lives in a DRF serializer, point at it:

```python
from django_strawberry_framework import SerializerMutation


class CreateItemViaSerializer(SerializerMutation):
    class Meta:
        serializer_class = serializers.ItemSerializer
        operation = "create"
```

`SerializerMutation` subclasses `DjangoMutation` and rides the same pipeline and envelope; the input is serializer-derived rather than model-column derived, and `serializer.errors` key to the GraphQL **wire** name, so a renamed field's error arrives as the client spelled it. `Meta.operation` is `"create"` or `"update"` only, and the update target is located by decoding `id:` through `get_queryset` rather than a `lookup_field`.

The construction hooks are hardened, so a migration from a looser setup hits `ConfigurationError`s rather than silent behavior changes: `get_serializer_kwargs` is constructor-only, the framework owns `data` / `instance` / `partial` / `context["request"]` / `context["write_alias"]`, and every hook receives a frozen `SerializerHookContext` plus an immutable data view instead of the live located row. Consumer-reachable phases are database-read-only under a pipeline-wide alias guard; writes happen only inside `serializer.save()`. `djangorestframework` is a **soft** dependency, so `SerializerMutation` is a lazy root export resolved through `__getattr__` and absent from `__all__`. See [`GLOSSARY.md#serializermutation`][glossary-serializermutation].

### Session auth

Opt-in `login` / `logout` / `register` field factories plus a `current_user` query helper live in `django_strawberry_framework.auth` and are not re-exported from the package root:

```python
from django_strawberry_framework.auth import current_user, login_mutation, logout_mutation, register_mutation


@strawberry.type
class Query:
    me = current_user()


@strawberry.type
class Mutation:
    login = login_mutation()
    logout = logout_mutation()
    register = register_mutation()
```

The family defaults to `AllowAny` — the documented inversion of the write family's deny-by-default, since login and register must serve the anonymous caller — and every factory still takes `permission_classes=`. `register` rides the create pipeline adding `validate_password` and `set_password`, so the plaintext password is never persisted; it derives its input from `USERNAME_FIELD`, distinct `REQUIRED_FIELDS`, and `password`, and refuses to auto-expose `is_active` / `is_staff` / `is_superuser` / `groups` / `user_permissions`. The user type's field selection **is** the authenticated read surface, so keep `password` and privilege columns out of it.

The framework provides no brute-force throttling or rate limiting; attach a `permission_classes` gate or edge middleware before exposing login publicly (a worked gate is under [Production security profile](#production-security-profile)). Wrong password, unknown user, inactive user, and backend `PermissionDenied` all collapse to one byte-identical failed-login envelope, though there is no constant-time guarantee across custom backends. `logout` returns `ok: true` only when an authenticated actor existed before teardown.

**Transport support.** `login` and `logout` classify the request transport before any credential work:

| Transport | `login` | `logout` |
|---|---|---|
| Django `HttpRequest` (sync or async) | supported | supported |
| Channels HTTP scope | supported | supported |
| Channels WebSocket, server-side session engine | **rejected before authentication** | supported |
| Channels WebSocket, signed-cookie session engine | **rejected before authentication** | **rejected before mutation** |
| Missing session middleware | rejected | rejected |

WebSocket `login` is rejected because login rotates the session key and an established socket cannot return the replacement cookie: a "success" would establish a session the browser could never claim. WebSocket `logout` is rejected on the signed-cookie engine because there is no server-side record to revoke — the check resolves the configured engine's `SessionStore` and rejects only when it subclasses Django's signed-cookie store, so a custom client-side engine that does not is treated as server-side and must not be used with WebSocket logout. Both rejections are top-level execution errors, distinct from the failed-login envelope. See [`GLOSSARY.md#auth-mutations`][glossary-auth-mutations].

## Transport

GraphQL over **HTTP** is a normal Django view in your own URLconf; GraphQL over **WebSocket** is the Channels router. Splitting them is the point: every GraphQL HTTP request traverses your project's real `MIDDLEWARE` — the `ALLOWED_HOSTS` check, `CsrfViewMiddleware`, `SecurityMiddleware`'s headers, session and authentication, cache policy — exactly as under WSGI. You do not need `channels` for the HTTP half: `django_strawberry_framework.views` is channels-free.

```python
# myproject/urls.py
from django.urls import path

from django_strawberry_framework.views import DjangoGraphQLView

from myproject.schema import schema

urlpatterns = [
    path("graphql/", DjangoGraphQLView.as_view(schema=schema)),
]
```

`AsyncDjangoGraphQLView` is the async twin, mounted identically, and is generally what an ASGI deployment wants since `as_view()` returns a coroutine function Django dispatches with no thread hop. Both are leaf-module imports, deliberately not package-root exports. The subclasses add two boundary policies over the raw body — a cumulative byte cap enforced before parsing or execution (`MAX_REQUEST_BODY_BYTES`, default 1 MiB, per-mount `as_view(max_request_body_bytes=...)`, returning `413`) and a strict UTF-8 wire contract — neither riding the `APPLY_UPSTREAM_PATCHES` kill switch. See [`GLOSSARY.md#djangographqlview`][glossary-djangographqlview].

**`APPEND_SLASH`.** Mounting at `"graphql/"` means a client POSTing to `/graphql` gets a `301` under `DEBUG=False` and a `RuntimeError` about lost POST data under `DEBUG=True`, and most clients do not re-POST a redirect, so point them at the exact path. For the slash-less spelling, mount at `path("graphql", ...)` and set `TESTING_ENDPOINT` to match.

### The Channels router

The router is only needed for **subscriptions over WebSocket**; an HTTP-only deployment serves `get_asgi_application()` (or WSGI) with just the `urlpatterns` entry above.

```python
# myproject/asgi.py
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")

from django.core.asgi import get_asgi_application

django_asgi_app = get_asgi_application()

from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter

from myproject.schema import schema

# `django_asgi_app` IS the "http" value: every HTTP request, GraphQL included,
# goes through Django. The router composes WebSocket only - Host check >
# AllowedHostsOriginValidator > AuthMiddlewareStack > URLRouter > the consumer.
application = DjangoGraphQLProtocolRouter(
    schema,
    django_asgi_app,
    websocket_url_pattern=r"^graphql/?$",  # the default; shown for the rename
)
```

`channels` is a soft dependency: importing the package or the submodule stays channels-free, and only symbol access raises the install-hint `ImportError`. See [`GLOSSARY.md#djangographqlprotocolrouter`][glossary-djangographqlprotocolrouter].

#### Migrating from `0.0.14`

The `0.0.14` router constructor is deliberately broken in three ways, because the API freeze begins at `1.0.0` and correcting a security-boundary error during alpha beats preserving an unsafe migration convenience.

| `0.0.14` | now | what a migrant hits |
|---|---|---|
| `django_application=None`, optional | `django_application`, **required** | omitting it is a `TypeError`; passing `None` (or any non-callable) is a `ConfigurationError` whose message names this migration |
| `url_pattern="^graphql"` — a prefix, applied to **both** protocols | `websocket_url_pattern=r"^graphql/?$"` — exact at both ends, **WebSocket only** | the keyword is renamed; the default no longer matches `/graphql-admin`, `/graphqlanything`, or `/graphql/extra` |
| the router served GraphQL over HTTP through Strawberry's `GraphQLHTTPConsumer`, with `django_application` behind it as a `^` fallback | the router's `"http"` value **is** your Django ASGI application, dispatched directly | nothing serves GraphQL over HTTP until you add the `urlpatterns` entry above — the step with no automatic equivalent |

Neither `DjangoGraphQLProtocolRouter(schema)` nor `DjangoGraphQLProtocolRouter(schema, django_asgi_app, url_pattern=r"^graphql")` — both valid `0.0.14` spellings — works now.

### Deployment guidance

**CSRF.** The endpoint is an ordinary CSRF-protected Django view, so cookie-backed session authentication is protected on the same terms as the rest of your site. Keep it enabled, follow [Django's CSRF guidance][django-csrf], and exercise the deployed view with `Client(enforce_csrf_checks=True)` ([Django's test-client CSRF checks][django-test-client-csrf]). If you serve the in-browser IDE, wrap the mount in `ensure_csrf_cookie` so the GET that serves it sets the `csrftoken` cookie the POST needs. The callback is marked `csrf_exempt` on the outside as an **ordering mechanism, not a bypass**: the request re-enters Django's public `csrf_protect` inside the body cap, so the complete implementation still runs and the endpoint stays protected even where `CsrfViewMiddleware` was omitted.

**If you subclass `CsrfViewMiddleware`, install the boundary middleware.** `csrf_protect` is built from Django's *stock* class, so a project whose `MIDDLEWARE` names a subclass would quietly lose those additions here. Move the ordering into the chain, **immediately before your CSRF entry**:

```python
MIDDLEWARE = [
    # ...
    "django_strawberry_framework.middleware.request_body.GraphQLRequestBodyBoundaryMiddleware",
    "myproject.middleware.MyCsrfViewMiddleware",  # your CsrfViewMiddleware subclass
    # ...
]
```

It runs the body boundary from that position, then your CSRF class runs in full. Listing it after a CSRF entry is refused at startup with `ConfigurationError` rather than allowed to fail open; a project that never edits `MIDDLEWARE` keeps the view-local arrangement.

**The request-body cap is two layers, and you need both.** The application cap guarantees nothing is parsed, allocated, or executed from an over-limit body, but not that the bytes were never *received*: Django's ASGI handler has already drained the request into a spooled temporary file before any application cap can run, and Uvicorn, Hypercorn, and Daphne ship no total-body limit of their own. An edge cap is therefore a co-requirement, never an alternative:

```nginx
location /graphql/ {
    client_max_body_size 1m;   # nginx answers 413 itself
    proxy_pass http://asgi_upstream;
}
```

For a `multipart/form-data` POST the bound is the declared `Content-Length`, enforced before `MultiPartParser` runs, so an over-limit declaration is refused with the same `413`, no part parsed. Per-file count, per-file size, and aggregate upload size are **not** bounded by `MAX_REQUEST_BODY_BYTES` — bound those at the proxy, with `DATA_UPLOAD_MAX_NUMBER_FILES` / `FILE_UPLOAD_MAX_MEMORY_SIZE`, or in your own validation.

**One UTF-8 wire.** A package view accepts UTF-8 and only UTF-8; UTF-16 / UTF-32 and a leading UTF-8 BOM get the same controlled `400` a malformed body gets, and the contract reaches the two multipart control fields (`operations` and `map`) too.

**Cache and headers.** An authenticated response must never be served from a shared cache to a different actor: Django patches `Vary: Cookie` once the session is read, but a proxy or CDN has to honor it, so mark the location uncacheable at the edge. `SecurityMiddleware`'s headers now apply to the route because it is a Django view; under `0.0.14`'s Channels HTTP branch they did not, so verify yours land after migrating.

**WebSocket handshakes are validated on `Host` and on `Origin`.** Two separate router-owned checks, neither substituting for the other. `Origin` is Channels' `AllowedHostsOriginValidator`; `Host` is the package's own private validator, composed outermost, which projects the handshake's host metadata into a minimal `HttpRequest` and calls `request.get_host()`, so your existing `ALLOWED_HOSTS` and `USE_X_FORWARDED_HOST` govern a handshake exactly as they govern an HTTP request. **No new setting exists.** Only a `DisallowedHost` becomes a denial, and it precedes authentication and consumer construction. A Channels consumer runs no `CsrfViewMiddleware`, so these two checks are that protocol's handshake defence rather than a token.

**WebSocket freshness and revocation.** The default consumer revalidates the session actor when an operation is admitted and again before every information-bearing frame an already-admitted operation puts on the wire, because admission alone never sees a running subscription again. A revoked actor can therefore neither admit another operation nor emit another frame; at whichever checkpoint notices first, the whole connection closes with `4403` / `"Forbidden"`. `websocket_revalidation_window=` (seconds, default `0.0` = revalidate every time) is the maximum age of a validation that may still authorize one. Detection is event-boundary-driven, so a revoked socket that never produces another event stays open: a resource-exhaustion concern to budget for, not an authorization hole.

**Connection lifetime.** The package imposes no maximum, because there is no correct default; enforce it in the deployment (Daphne's `--websocket_timeout` and message/frame size flags, nginx's `proxy_read_timeout` on the WebSocket location). Upstream's `connection_init_wait_timeout`, `keep_alive`, and `max_subscriptions_per_connection` are set on a consumer class passed as `websocket_consumer_class=`. An injected consumer still sits inside all three wrappers, but opts **out** of the package's revalidation, which is why injecting one alongside a positive `websocket_revalidation_window` is a construction error rather than a silently ignored argument.

## Production security profile

One auditable list for taking a schema from "runs" to "internet-facing". Start with Django's own [deployment checklist and `manage.py check --deploy`][django-deploy-checklist], which audits the Django-settings half; nothing below repeats it. Two settings it will not flag: set `SECURE_PROXY_SSL_HEADER` and `USE_X_FORWARDED_HOST` **only** behind a proxy you control that strips the client's own values for those headers, since each turns a client-forgeable header into trusted fact.

**The declared Django floor is not a secure-version recommendation.** `pyproject.toml` declares `Django>=5.2.16` as an API-compatibility statement frozen at release time; install the newest security patch in whichever supported series you have chosen (`5.2.x`, `6.0.x`, `6.1.x`).

### What the package already defaults to safe

Verify these on the deployed endpoint rather than configuring them; the two SDL rows read the `manage.py export_schema` output.

| Guarantee | Since | Mechanical check |
|---|---|---|
| Unexpected resolver/hook exceptions are masked under `DEBUG=False` — see [Production error policy](#production-error-policy) | `0.0.14` | force one; the response carries the policy message + `correlationId`, never the exception's text |
| `DjangoDebugExtension` fails closed under `DEBUG=False` | `0.0.14` | a schema listing it answers with no `extensions.debug` unless `allow_unsafe_production=True` is in the code |
| One execution resource budget (document tokens, depth, selections, aliases, variable cardinality, list rows, uploads, deadline) | `0.0.14` | an over-budget document or variable payload is refused with `extensions.code = "RESOURCE_LIMIT_EXCEEDED"` |
| Cumulative request-body cap applied before parsing | `0.0.14` | POST `MAX_REQUEST_BODY_BYTES` + 1 junk bytes → `413` |
| Strict UTF-8 wire contract | `0.0.14` | a UTF-16 body → the controlled `400` |
| Many-side relations expose the bounded connection only | `0.0.14` | the exported SDL carries no raw list sibling you did not opt into |
| File/image output carries no filesystem `path` unless `Meta.filesystem_path_fields` names the column | `0.0.14` | grep the exported SDL for `path` |
| Generated writes deny by default (`[]` is the explicit opt-out) | `0.0.11` | an unauthorized generated mutation → the `Not authorized to ...` error |
| WebSocket handshakes validate `Host` **and** `Origin`; established sockets revalidate the session actor | `0.0.14` | a hostile handshake is denied; a socket surviving an external logout closes `4403` on its next frame |

### The production GraphQL mount

```python
from graphql import NoSchemaIntrospectionCustomRule
from strawberry.extensions import AddValidationRules

from django_strawberry_framework import DjangoSchema, strawberry_config
from django_strawberry_framework.views import DjangoGraphQLView

schema = DjangoSchema(
    query=Query,
    mutation=Mutation,
    config=strawberry_config(),
    # A factory, not an instance: an instance would be shared across requests.
    extensions=[lambda: AddValidationRules([NoSchemaIntrospectionCustomRule])],
)

urlpatterns = [
    path(
        "graphql/",
        DjangoGraphQLView.as_view(
            schema=schema,
            graphql_ide=None,            # no GraphiQL / Pathfinder HTML
            allow_queries_via_get=False, # POST-only
        ),
    ),
]
```

Disabling introspection narrows reconnaissance; it is **not** an authorization boundary. `__typename` still answers, field names leak through error messages, and a client that already knows the schema loses nothing — row visibility and permission classes remain the boundary. The recipe is exercised as one unit by the live transport suite, so it is a supported configuration rather than a suggestion.

**CORS.** The package adds no CORS headers and needs none for same-origin use; the strongest configuration is not installing CORS middleware here at all. If cross-origin browser clients are real, scope it precisely — explicit origins, never `*` with credentials — since a permissive credentialed policy re-opens exactly the cross-site request class CSRF protection otherwise closes.

**Edge cache and rate limiting.** Mark the GraphQL location uncacheable at the edge and rate-limit it there: the resource budget bounds what one operation may cost, not how many a client may send.

### Relay GlobalIDs are encodings, not capabilities

A `GlobalID` is an addressing scheme: under the default `model` strategy it decodes to a model label and a predictable primary key, so any client can mint the ID of any row by guessing small integers. Possession of one **must never be treated as permission**. The authorization boundary is the type's visibility policy, which node refetch, connections, and generated mutations all locate through. Application code that takes a `GlobalID` to the ORM directly has stepped around that boundary and owns the check itself.

### Uploads: the package bounds bytes, the deployment owns content

With `multipart_uploads_enabled=True` the package bounds the declared multipart request size and the budget's upload count, per-file bytes, and aggregate bytes. The *content* of an accepted file is a deployment responsibility, as for any Django upload:

- extension / content-type / magic-byte validation, plus malware scanning where the threat model calls for it;
- storage permissions and a location never served as executable content;
- `Content-Disposition: attachment` (or a sandboxed domain) on browser-reachable downloads, so a stored HTML/SVG file cannot become stored XSS on your origin;
- signed or private URL policy on the storage backend, plus `DATA_UPLOAD_MAX_NUMBER_FILES` / `FILE_UPLOAD_MAX_MEMORY_SIZE` and the proxy body cap.

`name` is the **storage object key** and under many layouts embeds user-supplied filenames or tenant conventions, so treat it as published application data; `url` is whatever the backend builds, public and permanent on some backends and signed and expiring on others.

### Login and registration are anonymous surfaces — throttle them

`login_mutation()` / `register_mutation()` default to `AllowAny` and the framework adds no brute-force protection. Throttling is consumer-owned; the smallest real gate is a permission class over Django's cache:

```python
from django.core.cache import cache

from django_strawberry_framework.auth import login_mutation


class LoginAttemptThrottle:
    # At most 5 login attempts per username per 5 minutes, fail-closed.
    def has_permission(self, info, mutation, operation, data, instance=None):
        key = f"login-attempts:{data['username']}"
        if cache.add(key, 1, timeout=300):
            return True
        return cache.incr(key) <= 5


class Mutation:
    login = login_mutation(permission_classes=[LoginAttemptThrottle])
```

A cache-keyed counter is a floor, not a ceiling: it resets on eviction and counts attempts, not outcomes. A deployment needing lockout, per-IP dimensions, or audit trails should use its edge rate limiter and keep this as defense in depth.

### The example project is a fixture, never a deployment

`examples/fakeshop/` exists to exercise the package: `DEBUG=True`, a checked-in `SECRET_KEY`, GraphiQL, the debug toolbar, multipart uploads, and intentional `permission_classes = []` demonstrations are all deliberate. Its settings module refuses to load with `DEBUG` off, so the likeliest accident fails loudly. Copy the mount recipe above into a separate project, not the fakeshop settings.

## Development tooling

### Response debug extension

`DjangoDebugExtension` captures an operation's SQL and raised resolver exceptions into `extensions.debug`. Pass the **class**, not an instance, so Strawberry constructs a fresh one per operation and its capture state stays operation-local:

```python
from django_strawberry_framework.extensions import DjangoDebugExtension

schema = strawberry.Schema(
    query=Query,
    config=strawberry_config(),
    extensions=[lambda: _optimizer, DjangoDebugExtension],
)
```

It brackets every configured connection separately and aggregates rows from every alias used into one `sql` list, each row carrying its `alias` and `vendor`; rows keep per-connection log order, so the list is not a cross-database timeline, and an unused alias contributes nothing.

Never enable it on an internet-facing schema: it returns interpolated SQL values and unmasked exception messages and tracebacks. **It fails closed if you do** — with `settings.DEBUG` false and no acknowledgement it acquires no cursor, publishes no `debug` key, and logs one warning, while the operation runs normally. For a controlled reason to run it with `DEBUG` off, say so with `DjangoDebugExtension(allow_unsafe_production=True)` inside the factory. See [`GLOSSARY.md#djangodebugextension`][glossary-djangodebugextension].

### django-debug-toolbar

`DebugToolbarMiddleware` teaches the toolbar's SQL panel to see Strawberry `/graphql/` traffic. Install `django-debug-toolbar>=7.0.0`, then wire the toolbar's normal prerequisites with one replacement:

```python
from debug_toolbar.toolbar import debug_toolbar_urls

INSTALLED_APPS = ["django.contrib.staticfiles", "debug_toolbar", "django_strawberry_framework"]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django_strawberry_framework.middleware.debug_toolbar.DebugToolbarMiddleware",
]

INTERNAL_IPS = ["127.0.0.1"]

urlpatterns += debug_toolbar_urls()
```

The package middleware **replaces** `"debug_toolbar.middleware.DebugToolbarMiddleware"`; never list both, since the subclass already runs the stock pipeline. Keep `debug_toolbar_urls()` in the URLconf while it is active — the stock postprocessor reverses its panel routes for every processed response, so omitting them raises `NoReverseMatch`. Gating is the stock toolbar's (`DEBUG`, `SHOW_TOOLBAR_CALLBACK`, `INTERNAL_IPS`), but injection is view-scoped rather than IDE-scoped: whenever the gate is open, every JSON response from a Strawberry Django view except an `IntrospectionQuery` gains a top-level `debugToolbar` key, programmatic clients included, and the GraphiQL bridge removes it only inside the IDE. A development-only integration. See [the debug-toolbar middleware entry][glossary-debug-toolbar-middleware].

### Testing GraphQL endpoints

```python
from django_strawberry_framework.testing import TestClient


def test_items():
    response = TestClient().query("{ allItems(first: 1) { edges { node { name } } } }")

    assert response.errors is None
    assert response.response.status_code == 200
```

`TestClient` / `AsyncTestClient` and the `GraphQLTestMixin` / `GraphQLTestCase` unittest family all drive Django's in-process test client and return a typed `Response` carrying `errors`, `data`, `extensions`, and the raw Django response. Endpoint selection runs per-call `query(..., url=...)`, constructor `path=`, `GraphQLTestMixin.GRAPHQL_URL`, `DJANGO_STRAWBERRY_FRAMEWORK["TESTING_ENDPOINT"]`, `"/graphql/"`.

The flavors differ on error assertions on purpose: `TestClient.query()` and `AsyncTestClient.query()` default to `assert_no_errors=True` and raise, while `GraphQLTestMixin.query()` defaults to `False` so a test can call `assertResponseNoErrors()` / `assertResponseHasErrors()`. An endpoint typo is a transport misconfiguration, not a GraphQL error, and the client does not wrap it: `response.json()` raises `ValueError` naming the non-JSON `Content-Type`. See [`TestClient`][glossary-testclient] and [`GraphQLTestCase`][glossary-graphqltestcase] for multipart uploads, authentication brackets, and async usage.

## Running the example project

The repository ships a fakeshop example exercising the shipped surface against a real Django app.

```shell
# Apply migrations to the example app
uv run python examples/fakeshop/manage.py migrate

# Start the dev server (admin + GraphiQL at /graphql/)
uv run python examples/fakeshop/manage.py runserver
```

The dev landing page at `/` links to GraphiQL, the admin, and the seed/delete triggers. For the full walkthrough see [`../examples/fakeshop/README.md`][fakeshop-readme].

### Seeding the example database

The example discovers all Faker providers at runtime. `seed_data` is idempotent: it ensures at least N items exist per provider and creates only the shortfall.

```shell
uv run python examples/fakeshop/manage.py seed_data       # 5 items per provider
uv run python examples/fakeshop/manage.py seed_data 50
uv run python examples/fakeshop/manage.py delete_data 10  # first 10 items + entries
uv run python examples/fakeshop/manage.py delete_data all
uv run python examples/fakeshop/manage.py delete_data everything  # wipe all four tables
```

### Test users

Each set creates 6 users for exercising `get_queryset` permission branches: 1 staff, 1 with no perms, 4 per-model `view_*` holders. All share password `admin`; superusers are never deleted.

```shell
uv run python examples/fakeshop/manage.py create_users      # 1 set (6 users)
uv run python examples/fakeshop/manage.py create_users 3    # 3 sets (18 users)
uv run python examples/fakeshop/manage.py delete_users all
uv run python examples/fakeshop/manage.py delete_users 5
```

### Sharded mode (multi-DB)

An additive two-alias layout for exercising multi-database scenarios, toggled with `FAKESHOP_SHARDED=1`:

```shell
# Materialize the secondary shard SQLite file (idempotent)
FAKESHOP_SHARDED=1 uv run python examples/fakeshop/manage.py seed_shards --count 5000
```

`default` keeps pointing at `db.sqlite3` and `shard_b` adds `db_shard_b.sqlite3`, so one dev workflow populates the default alias either way. For the cooperation contract these shards run against — explicit `.using()` `_db` preservation, FK-id elision router hints, consumer `Prefetch(queryset=…)` alias round-trips, and strictness under non-default aliases — see [`GLOSSARY.md#multi-database-cooperation`][glossary-multi-database-cooperation].

## Using the package from a local checkout

To develop against a local checkout from another Django project, add `django-strawberry-framework` to that project's `pyproject.toml` dependencies, point it at the checkout, and run `uv sync`:

```toml
# In your project's pyproject.toml
[tool.uv.sources]
django-strawberry-framework = { path = "../django-strawberry-framework", editable = true }
```

## Where next

[`../TODAY.md`][today] is the current capability snapshot. [`GLOSSARY.md`][glossary] is the per-feature catalog of every shipped, planned, and deferred capability, deep-linkable by anchor (`GLOSSARY.md#filterset`). [`../KANBAN.md`][kanban] carries the roadmap, including the beta line still ahead — `FieldSet`, `Meta.search_fields` and full-text search, aggregates, mutation idempotency keys. [`../GOAL.md`][goal] is the destination and the migration-shape diffs against the two upstreams.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[contributing]: ../CONTRIBUTING.md
[goal]: ../GOAL.md
[kanban]: ../KANBAN.md
[readme]: ../README.md
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
[glossary-djangographqlview]: GLOSSARY.md#djangographqlview
[glossary-djangolistfield]: GLOSSARY.md#djangolistfield
[glossary-djangomodelformmutation]: GLOSSARY.md#djangomodelformmutation
[glossary-djangomutation]: GLOSSARY.md#djangomutation
[glossary-djangonodefield]: GLOSSARY.md#djangonodefield
[glossary-filterset]: GLOSSARY.md#filterset
[glossary-graphqltestcase]: GLOSSARY.md#graphqltestcase
[glossary-metaglobalid_strategy]: GLOSSARY.md#metaglobalid_strategy
[glossary-metanullable_overrides]: GLOSSARY.md#metanullable_overrides
[glossary-multi-database-cooperation]: GLOSSARY.md#multi-database-cooperation
[glossary-orderset]: GLOSSARY.md#orderset
[glossary-plan-cache]: GLOSSARY.md#plan-cache
[glossary-relay-node-integration]: GLOSSARY.md#relay-node-integration
[glossary-sealed-execution-queryset]: GLOSSARY.md#sealed-execution-queryset
[glossary-serializermutation]: GLOSSARY.md#serializermutation
[glossary-testclient]: GLOSSARY.md#testclient

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
[django-deploy-checklist]: https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/
[django-test-client-csrf]: https://docs.djangoproject.com/en/5.2/topics/testing/tools/#the-test-client
