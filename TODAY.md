# Today

`TODAY.md` is the current-state playbook for **what `django-strawberry-framework` (the package) can do right now**, demonstrated through one canonical example: `examples/fakeshop/apps/products/`. It answers: "if I wire a model app with this package today, what works?"

> **Scope of this file — keep it this way.** This document is about **package capabilities**, not the example apps. `products` is the *single canonical demonstration vehicle* and the only app this file talks about. The other fakeshop apps (`library`, `scalars`, `kanban`, `glossary`) deliberately re-exercise the same package surface against different model shapes — cataloguing them here would only repeat these capabilities. Do **not** broaden this file to enumerate the other apps; keep every example and edit products-centric and capability-focused.
>
> For the package-wide capability catalog, shipped/planned status, optimizer hints, strictness modes, and future work, see [`docs/GLOSSARY.md`][glossary].

## What products demonstrates today

`examples/fakeshop/apps/products/` is a full model-backed GraphQL app over `Category` / `Item` / `Property` / `Entry`. As of `0.0.11` it exercises, end to end, the package capabilities a real consumer reaches for:

- **`DjangoType` schema** — four types configured entirely through `class Meta` (`model` + `fields`), with forward-FK + reverse-FK traversal and four root Relay connection fields (`allCategories` / `allItems` / `allProperties` / `allEntries`, each a `DjangoConnectionField` as of `0.0.9`).
- **Relay nodes** — every type declares `Meta.interfaces = (relay.Node,)`, so each `id` is a Relay `GlobalID` (own-PK GlobalID filtering, `node(id:)` refetch shape). As of `0.0.9` the default `GlobalID` payload is the Django model label (`products.item:<pk>`) rather than the GraphQL type name, so a `CategoryType` → `ProductCategoryType` rename no longer invalidates cached IDs; `Meta.globalid_strategy` / `RELAY_GLOBALID_STRATEGY` select `model` (default) / `type` (legacy opt-out) / `type+model` (transitional) / callable.
- **Filtering** — `Meta.filterset_class` on every type (declared in `apps/products/filters.py`), surfaced on each connection field via a synthesized `filter:` argument. Includes a per-field `check_name_permission` denial gate on `CategoryFilter` (active-input-only).
- **Ordering** — `Meta.orderset_class` on every type (declared in `apps/products/orders.py`), surfaced via a synthesized `orderBy:` argument. Includes the matching `check_name_permission` gate on `CategoryOrder`.
- **Optimizer cooperation** — `DjangoConnectionField` hands its pre-slice `QuerySet` to `DjangoOptimizerExtension`, which plans `select_related` / `prefetch_related` / `only()` across the connection's `edges { node }` selection (and any nested `<field>Connection`s) without per-resolver boilerplate.
- **Filter + order composition** — each connection runs the same `get_queryset` visibility → `filter` → `orderBy` → deterministic pk-order → optimizer-plan → cursor-slice pipeline the hand-written resolvers used to spell (visibility scopes, filter narrows, order arranges).
- **`DjangoMutation` write surface** — as of `0.0.11` products also exposes a live `Mutation` (`createItem` / `updateItem` / `deleteItem` + `createCategory`), each an unannotated `DjangoMutationField` over a `DjangoMutation` subclass, with the shared `errors: list[FieldError]` envelope, `DjangoModelPermission` write authorization, `get_queryset`-scoped update/delete lookups, and an optimizer-backed post-write re-fetch (see "Mutations on products today").
- **Form-based mutation write surface** — as of `0.0.12` products also exposes form-validated mutations on the same `Mutation` type: `createItemViaForm` / `updateItemViaForm` (a `DjangoModelFormMutation` over an `ItemModelForm`, the `ModelForm` flavor reusing the same `FieldError` envelope), `createItemWithFileViaForm` (a multipart `Upload` through a form `FileField`), `createStampedItemViaForm` (a `get_form_kwargs` override injecting `user`), and `submitContact` (a model-less `DjangoFormMutation` over a plain `ContactForm`, returning the `{ ok, errors }` payload). The input shape is derived from each form's declared fields, and `form.errors` maps onto the same envelope (`clean_<field>` keyed to its field; the `unique_item_per_category` constraint keyed to `"__all__"`). See "Mutations on products today".

The live `/graphql/` HTTP suite at `examples/fakeshop/test_query/test_products_api.py` pins all of the above end to end.

## What's in `products/schema.py` today

One representative type (`ItemType` / `PropertyType` / `EntryType` follow the same `class Meta` shape), the connections-only `Query`, and — as of `0.0.11` — the `DjangoMutation` write surface (`Mutation`). As of `0.0.9` the four root fields are `DjangoConnectionField` class attributes — the `django-graphene-filters` cookbook mirror — and the hand-written `filter:` / `orderBy:` resolver signatures are gone: `DjangoConnectionField` synthesizes those arguments from the same `Meta.filterset_class` / `Meta.orderset_class` sidecars and runs the same `get_queryset` → `filter` → `orderBy` → deterministic-order → optimizer composition the resolvers spelled by hand. The `Mutation` block below declares one `DjangoMutation` subclass per operation (`class Meta` with `model` + `operation`), each surfaced as an unannotated `DjangoMutationField` — no Strawberry decorators on the mutation classes, the same Meta-driven shape as the types.

```python
import strawberry
from strawberry import relay

from django_strawberry_framework import (
    DjangoConnection,
    DjangoConnectionField,
    DjangoMutation,
    DjangoMutationField,
    DjangoType,
)

from . import filters, models, orders


class CategoryType(DjangoType):
    class Meta:
        model = models.Category
        fields = (
            "id",
            "name",
            "description",
            "items",
            "properties",
            "is_private",
            "created_date",
            "updated_date",
        )
        interfaces = (relay.Node,)
        filterset_class = filters.CategoryFilter
        orderset_class = orders.CategoryOrder
        # Future Layer-3 keys — uncomment each as the relevant card ships:
        # search_fields = ("name", "description")        # 0.1.2
        # aggregate_class = aggregates.CategoryAggregate # 0.1.3
        # fields_class = fieldsets.CategoryFieldSet      # 0.1.1


@strawberry.type
class Query:
    all_categories: DjangoConnection[CategoryType] = DjangoConnectionField(CategoryType)
    all_items: DjangoConnection[ItemType] = DjangoConnectionField(ItemType)
    all_properties: DjangoConnection[PropertyType] = DjangoConnectionField(PropertyType)
    all_entries: DjangoConnection[EntryType] = DjangoConnectionField(EntryType)


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


class CreateCategory(DjangoMutation):
    class Meta:
        model = models.Category
        operation = "create"


@strawberry.type
class Mutation:
    # Each field is an unannotated DjangoMutationField — the <Name>Payload return
    # is materialized at finalization, so the factory types the field via a
    # strawberry.lazy forward-ref. Defaults apply: DjangoModelPermission write-auth.
    create_item = DjangoMutationField(CreateItem)
    update_item = DjangoMutationField(UpdateItem)
    delete_item = DjangoMutationField(DeleteItem)
    create_category = DjangoMutationField(CreateCategory)
```

## What to put in `config/schema.py` today

Enable the optimizer at the project-schema boundary and finalize every imported `DjangoType` before constructing the Strawberry schema:

```python
import strawberry
from apps.products.schema import Mutation as ProductsMutation
from apps.products.schema import Query as ProductsQuery

from django_strawberry_framework import (
    DjangoOptimizerExtension,
    finalize_django_types,
    strawberry_config,
)


@strawberry.type
class Query(ProductsQuery):
    """Top-level Query — extend with each app's Query as bases."""


@strawberry.type
class Mutation(ProductsMutation):
    """Top-level Mutation — extend with each app's Mutation as bases."""


finalize_django_types()

_optimizer = DjangoOptimizerExtension()
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    config=strawberry_config(),
    extensions=[lambda: _optimizer],
)
```

Two rules the package enforces: `finalize_django_types()` must run **after** every module that defines `DjangoType` classes is imported and **before** `strawberry.Schema(...)` is constructed — the same call also materializes each mutation's `<Model>Input` / `<Model>PartialInput` / `<Name>Payload` classes and binds every `DjangoMutationField`, so the schema build can resolve their lazy references; and the optimizer is added as a module-level `DjangoOptimizerExtension` singleton wrapped in a factory (`extensions=[lambda: _optimizer]`), which preserves the instance-bound plan cache and emits no deprecation warning.

## Package scalar conversions

`DjangoType` converts these model fields to Strawberry scalars. **Products exercises the integer / text / boolean / datetime subset** (its models are `TextField` / `BooleanField` / `DateTimeField` + FK + the `BigAutoField` PK); the remaining conversions are package capabilities covered by the package test suite.

- `BigAutoField` / `AutoField` / `IntegerField` → `int`  *(products: every PK)*
- `TextField` / `CharField` → `str`  *(products: `name` / `value` / `description`)*
- `BooleanField` → `bool`  *(products: `is_private`)*
- `DateTimeField` / `DateField` / `TimeField` / `DurationField` → Python-native time types  *(products: `created_date` / `updated_date`)*
- `BigIntegerField` / `PositiveBigIntegerField` → `BigInt` (JSON-safe string-serialized; `PositiveBigIntegerField` switched from `int` to `BigInt` in `0.0.6` — breaking wire-format change)
- `DecimalField` → `decimal.Decimal`
- `FloatField` → `float`
- `UUIDField` → `uuid.UUID`
- `BinaryField` → `bytes`
- `FileField` / `ImageField` → structured `DjangoFileType` / `DjangoImageType` read output — the output object itself is **nullable by default** (an empty / absent stored file resolves to `null`, regardless of the column's `null` / `blank`; `required_overrides` is the opt-in to a non-null object), with `name` non-null and `path` / `size` / `url`, plus image `width` / `height`, nullable / storage-safe inside it; via `FIELD_OUTPUT_TYPE_MAP`; switched from `str` in `0.0.11` — breaking wire-format change. The filter / scalar-input value stays `str`; the generated `DjangoMutation` input is the `Upload` scalar
- `JSONField` → `strawberry.scalars.JSON`
- PostgreSQL `ArrayField` → `list[T]` (recursive through `field.base_field`; soft-registered when `django.contrib.postgres.fields` imports)
- PostgreSQL `HStoreField` → `strawberry.scalars.JSON` (soft-registered)
- `null=True` → `T | None`
- `CharField` / `TextField` with `choices` → generated Strawberry enum
- Relay `GlobalID` when `Meta.interfaces = (relay.Node,)` is declared  *(products: every type)*

## Package relation conversions

- forward `ForeignKey` → related `DjangoType`  *(products: `Item.category` / `Property.category` / `Entry.item` / `Entry.property`)*
- reverse `ForeignKey` → `list[RelatedType]` **+ a `<field>Connection` Relay sibling**  *(products: `Category.items` / `Category.properties` / `Item.entries` / `Property.entries`, each also live as `itemsConnection` / `propertiesConnection` / `entriesConnection`)*
- forward `OneToOneField` → related `DjangoType` or `None`
- reverse `OneToOneField` → related `DjangoType` or `None`
- forward `ManyToManyField` → `list[RelatedType]` **+ a `<field>Connection` Relay sibling**
- reverse `ManyToManyField` → `list[RelatedType]` **+ a `<field>Connection` Relay sibling**

As of `0.0.9`, every to-many relation between two Relay-Node-shaped types gains a paginated `<field>Connection` sibling alongside the plain `list[T]` field — the relation-as-connection upgrade that carries the package's **Relay-node-shaped output** north star (see [`GOAL.md`][goal]) down into nested relations rather than weakening rich relations into generic lists. Products exercises it directly: `CategoryType`'s `itemsConnection` / `propertiesConnection` and the `Item` / `Property` `entriesConnection`s are all live, each accepting the target type's synthesized `filter:` / `orderBy:` arguments and `first` / `last` pagination. Products keeps both shapes (the default); the per-relation list-only / connection-only selector is a non-GOAL knob documented in [`docs/GLOSSARY.md#metarelation_shapes`][glossary-metarelation_shapes].

Products' graph is FK-only; `OneToOneField` and `ManyToManyField` conversions are package capabilities covered by the package test suite.

## Optimized products queries that work today

The connection fields hand their pre-slice `QuerySet`s to `DjangoOptimizerExtension` (added in `config/schema.py`), so the `edges { node }` selection is planned into one ORM query.

```graphql
{
  allItems {
    edges {
      node {
        name
        category {
          name
        }
      }
    }
  }
}
```

Expected: `select_related("category")`.

```graphql
{
  allEntries {
    edges {
      node {
        value
        item {
          name
          category {
            name
          }
        }
        property {
          name
          category {
            name
          }
        }
      }
    }
  }
}
```

Expected: nested `select_related` paths and `only()` projections. (A connection with no `first` / `last` caps the default page at `relay_max_results` and appends a deterministic `ORDER BY pk`.)

A nested relation `<field>Connection` plans the same way — one windowed `Prefetch` per relation, no per-parent query:

```graphql
{
  allCategories {
    edges {
      node {
        name
        itemsConnection(
          first: 2
        ) {
          edges {
            node {
              name
            }
          }
        }
      }
    }
  }
}
```

Expected: one root-slice query plus one windowed `itemsConnection` prefetch covering every category's first two items (a `RowNumber()` window bounds each parent's page; `totalCount`, when opted in, rides a `Count(1) OVER`) — the N+1-safe nested planning of [`GOAL.md`][goal] success-criterion 5, now reaching connection-shaped relations.

## Filtering and ordering on products today

Both ship in `0.0.8`; as of `0.0.9` the `filter:` / `orderBy:` arguments are synthesized onto every products connection field from the type's `Meta.filterset_class` / `Meta.orderset_class` sidecars (no hand-written `filter_input_type(...)` / `order_input_type(...)` signatures). `filter:` narrows, `orderBy:` arranges, and they compose:

```graphql
{
  allItems(
    filter: {
      category: {
        id: {
          exact: "<GlobalID: base64 of products.category:<pk>>"
        }
      }
    }
    orderBy: [
      {
        name: ASC
      }
    ]
  ) {
    edges {
      node {
        name
        category {
          name
        }
      }
    }
  }
}
```

`CategoryFilter` / `CategoryOrder` additionally declare a `check_name_permission` gate, so an anonymous request that filters or orders by `Category.name` is denied — the gate fires only when the input actually names the gated field (active-input-only scope).

> **Breaking wire-format change in `0.0.9` (the model-anchored `GlobalID` default).** Through `0.0.8` a products `GlobalID` was the base64 of `<GraphQL type name>:<pk>` (`CategoryType:42`). As of `0.0.9` the default is the Django model label (`products.category:42`), so **every emitted products `GlobalID` changes** and the filter examples above use the model-label payload. This is parallel to the `PositiveBigIntegerField → BigInt` `0.0.6` breaking-wire-format change above; it is acceptable pre-`1.0.0` and there is a clean per-type / project-wide opt-out (`type` reproduces the byte-identical pre-`0.0.9` payload). In `0.0.9` the break lands **live** alongside its consumer — root `node(id:)` / `nodes(ids:)` (`DONE-032-0.0.9`) decode every emitted ID, so every old client-cached type-anchored ID is undecodable under the `model` default the moment the upgrade deploys. The migration-safe upgrade sequence for a deployed schema:
>
> 1. Deploy `RELAY_GLOBALID_STRATEGY = "type+model"` **while the old GraphQL type names still exist** — new IDs emit model-anchored, old type-anchored IDs still decode.
> 2. Let clients receive model-label IDs and age out the cached old type-name IDs.
> 3. **Only then** rename GraphQL types (or `Meta.name`) or flip to `model`.
>
> The step-3 ordering is load-bearing: `type+model` decodes an old type-anchored ID only while its old GraphQL type name still resolves. Renaming a type / `Meta.name` *during* the window still orphans cached old-type-name IDs — `type+model` is a strategy bridge, **not** a rename-history alias map (that is `BACKLOG.md` item 39). A consumer who must rename mid-window owns a consumer alias / callable migration until then.
>
> **One more upgrade hazard — multiple `DjangoType`s over one model.** A model-label payload (`app_label.model:pk`) is shared by *every* type registered for that model and always decodes to the model's **primary** type (`Meta.primary`). So if two Relay-Node types map to one model and both take the `model` default, the secondary's `GlobalID`s become byte-identical to the primary's and refetch *as* the primary — the secondary's distinct identity and `get_queryset` visibility scope silently collapse onto the primary's. Under the pre-`0.0.9` type-name default those two types had distinct, self-routing IDs, so this is a behavioral change on upgrade, not just a cache-invalidation. Finalization emits a warning naming the collapsing secondaries. If the two types need disjoint identity / auth scopes (the public-vs-admin pattern), set `Meta.globalid_strategy = "type"` on the secondary so its IDs stay self-routing.

## Visibility filtering via `get_queryset`

A `DjangoConnectionField` applies the type's `get_queryset` visibility hook automatically as the first step of its composition pipeline (already part of the filter/order chain above), so a root connection respects the same rules a type declares:

```python
class ItemType(DjangoType):
    class Meta:
        model = models.Item
        fields = (
            "id",
            "name",
            "description",
            "category",
            "is_private",
        )

    @classmethod
    def get_queryset(cls, queryset, info, **kwargs):
        user = getattr(info.context, "user", None)
        if user and user.is_staff:
            return queryset
        return queryset.filter(is_private=False)
```

Relation traversal into a type with a custom `get_queryset` is handled by the optimizer with a `Prefetch` downgrade, so target visibility filters are not bypassed by raw joins. As of `0.0.10` the four `products/schema.py` types' `get_queryset` hooks are live and call `apply_cascade_permissions(cls, ..., info)`, so visibility cascades across the `Entry → Item → Category` / `Entry → Property → Category` FK chain: an anonymous request loses any entry whose item or property points at a private category, staff sees everything, and a `view_<model>` user sees non-private rows but still loses entries under hidden targets (the cascade composes per edge). See [`docs/GLOSSARY.md#apply_cascade_permissions`][glossary-apply-cascade-permissions].

## Mutations on products today

As of `0.0.11` products exposes a `Mutation` type (in `products/schema.py`) alongside its connections-only `Query` — the package's write side, declared in the same `class Meta` shape as everything else (no Strawberry decorators). It carries `createItem` / `updateItem` / `deleteItem` plus a `createCategory`, each an unannotated `DjangoMutationField` over a `DjangoMutation` subclass; as of `0.0.12` it also carries the form-backed mutations (`createItemViaForm` / `updateItemViaForm` / `createItemWithFileViaForm` / `createStampedItemViaForm` / `submitContact`, see below). `config/schema.py` wires `mutation=Mutation` into the project schema. The full pipeline runs live over `/graphql/`:

```graphql
mutation {
  createItem(
    data: {
      name: "Widget"
      categoryId: "<GlobalID: products.category:<pk>>"
    }
  ) {
    node {
      name
      category {
        name
      }
    }
    errors {
      field
      messages
    }
  }
}
```

- **`create` / `update` / `delete`.** `createItem` takes a generated `ItemInput!` (each editable field required only when it has no usable Django `default` / `blank` / `null`, so `name` / `categoryId` are required while `description` / `isPrivate` are optional); `updateItem(id:, data:)` takes the all-optional `ItemPartialInput!`; `deleteItem(id:)` takes just the id. Forward FK becomes `categoryId` (a Relay `GlobalID`, type-checked against `Category` at decode — a wrong-type id is a `FieldError`, never a cross-model lookup).
- **The shared `errors: list[FieldError]` envelope.** A `full_clean()` failure does not raise at the GraphQL boundary — it returns the payload with a null `node` and one `FieldError` (`field` + `messages`) per offending field. A duplicate that trips `Item`'s `unique_item_per_category` constraint is caught by `validate_constraints()` before `save()` and keyed to Django's `"__all__"` sentinel (the multi-field-constraint key).
- **Permission-scoped `update` / `delete` lookups.** Both locate the row through `ItemType.get_queryset(...)`, so a caller who cannot *see* a private item gets a not-found `FieldError` on `id` — never an existence leak. Visibility (`get_queryset`) and write authorization are separate layers.
- **Separate write authorization (`DjangoModelPermission`).** Every operation runs `Meta.permission_classes` (default `[DjangoModelPermission]`, the Django `add` / `change` / `delete` model perms). An anonymous caller or one missing the model perm is denied with a top-level `GraphQLError` before any write — distinct from the field-keyed `FieldError` envelope, and distinct from `get_queryset` visibility (can-view ≠ can-write).
- **Optimizer-backed post-write re-fetch.** On success the payload's `node` is the mutated row re-fetched and optimizer-planned for the response selection. Because the operation is a mutation, the `spec-035` **G2** gate keeps `select_related` / `prefetch_related` but suppresses `.only(...)` column deferral — so selecting `node { category { name } }` plans the join without a deferred-field set. The live `CaptureQueriesContext` test pins the bounded query count.

The live `/graphql/` suite at `examples/fakeshop/test_query/test_products_api.py` pins all of the above — the happy paths, the constraint envelope (including a partial update that collides on `unique_item_per_category` by changing only `name`), write-auth denial vs. success, the visibility-scoped not-found, the wrong-type `GlobalID`, and the G2 query-shape assertion that discharges the `spec-035` live-test handoff. See [`docs/GLOSSARY.md#djangomutation`][glossary-djangomutation].

**Form-backed mutations (`0.0.12`).** Alongside the model-driven `DjangoMutation` fields, products demonstrates the form-validated write flavor — the same `class Meta` shape, `Meta.form_class` instead of `model` + `operation`. `createItemViaForm` / `updateItemViaForm` wrap an `ItemModelForm` (a `forms.ModelForm` over `Item`) in `DjangoModelFormMutation`: the input shape is derived from the form's declared fields, the FK writes through the form's `category` field via the generated `categoryId`, a `clean_name` failure keys to `name`, and the `unique_item_per_category` constraint surfaces through `_post_clean` keyed to `"__all__"` — all on the shared `FieldError` envelope, with the `ModelForm` returning the post-save object in the uniform `node` / `result` slot (re-fetched and optimizer-planned). `createItemWithFileViaForm` drives a multipart `Upload` through a form `FileField` (a raw `django.test.Client` multipart request); `createStampedItemViaForm` exercises a `get_form_kwargs` override that injects `user` at runtime. `submitContact` wraps a model-less plain `ContactForm` in `DjangoFormMutation`, returning the pinned `{ ok, errors }` payload (its mutation declares an explicit `Meta.permission_classes` because no `DjangoModelPermission` default applies to a model-less form). `test_products_api.py` pins the create / update / partial-update preservation, the `form.errors` envelope, write authorization, the visibility-scoped update, the multipart upload, and the plain form's success / validation-failure shapes. See [`docs/GLOSSARY.md#djangoformmutation`][glossary-djangoformmutation].

## What products is still waiting for

Products grows toward its `1.0.0` Relay shape as these unshipped surfaces land (tracked in [`KANBAN.md`][kanban]). Filtering and ordering are **not** on this list — they shipped in `0.0.8` and are wired today. `DjangoConnectionField` (Relay connections) is **not** on this list either — it shipped in `0.0.9` and products' four root fields are now connections (the cookbook-mirror conversion). The root `node(id:)` / `nodes(ids:)` Relay entry points and any `Meta.connection` (`totalCount`) opt-ins are **not** on this list either: both **shipped as package capabilities in `0.0.9`** (`DONE-032`) — see "Shipped package capabilities not exercised by products" below — and products simply hasn't wired them into its connections-only `Query` yet (deferred to the fakeshop-activation card, `TODO-BETA-053-0.1.5`).

- `Meta.fields_class` — `FieldSet` (`0.1.1`)
- `Meta.search_fields` (`0.1.2`)
- `Meta.aggregate_class` — aggregation (`0.1.3`)

## Shipped package capabilities not exercised by products

These ship today but products' model shapes don't reach them; they're covered by the package test suite (see [`docs/GLOSSARY.md`][glossary]):

- **`Meta.primary`** (shipped `0.0.6`) — multiple `DjangoType` subclasses per model with one explicit primary. Products declares one type per model. See [`docs/GLOSSARY.md#metaprimary`][glossary-metaprimary].
- **Consumer override semantics for scalar fields** (shipped `0.0.6`) — annotation-only and `strawberry.field` scalar overrides bypass `convert_scalar`; `relay.Node` `id` collisions raise `ConfigurationError` at type-creation time. Products exercises no scalar override. See [`docs/GLOSSARY.md#scalar-field-override-semantics`][glossary-scalar-field-override-semantics].
- **OneToOne / M2M relation conversion, choice-enum generation, and the specialized scalar conversions** (`BigInt`, `JSON`, `UUID`, `Decimal`, `Array`, `HStore`) — products has no OneToOne, M2M, `choices`, or those field types.
- **`Meta.nullable_overrides` / `Meta.required_overrides`** (shipped `0.0.9`) — force a non-relation field's GraphQL nullability independent of its Django column (`T!`→`T` or `T`→`T!`), validated at type creation; the scope is non-relation model fields — scalar columns and, as of `0.0.11`, the file/image output objects (e.g. `required_overrides = ("attachment",)` asserts a non-null `DjangoFileType!`), not relations. Products declares no override; the library app's `NullabilityOverrideBookType` exercises both directions. See [`docs/GLOSSARY.md#metanullable_overrides`][glossary-metanullable_overrides].
- **Root `node(id:)` / `nodes(ids:)` refetch fields** (`DjangoNodeField` / `DjangoNodesField`, shipped `0.0.9`) — the single-object and batch Relay refetch entry points that [`GOAL.md`][goal]'s astronomy `Query` declares (`galaxy: GalaxyNode | None = DjangoNodeField(GalaxyNode)`). Each decodes a model-anchored `GlobalID` to its type and reruns that type's `get_queryset`; resolution is nullable by contract (a decodable id identifying no row resolves to `null` / a positional `null` hole with no existence-probing query), while an undecodable payload surfaces a `GLOBALID_INVALID` error. `nodes` batches one query per decoded type and returns results in input order, preserving duplicates and null holes. Products' `Query` is connections-only, so it declares neither yet (`TODO-BETA-053-0.1.5`). See [`docs/GLOSSARY.md#djangonodefield`][glossary-djangonodefield] / [`#djangonodesfield`][glossary-djangonodesfield].
- **`Meta.connection` (`totalCount`)** (shipped `0.0.9`) — opts a connection into the Relay `totalCount` field, served from a `Count(1) OVER` window on the optimizer fast path. Products' connections omit it; the library app's `BookType` declares `connection = {"total_count": True}`. See [`docs/GLOSSARY.md#metaconnection`][glossary-metaconnection].
- **`Upload` scalar + file/image mapping** (shipped `0.0.11`) — the re-exported `Upload` scalar, the structured `DjangoFileType` / `DjangoImageType` read output, and the generated `DjangoMutation` `FileField` / `ImageField` → `Upload` mutation-input mapping. **Products** declares no file/image column, so it exercises none of these directly; the **`scalars` acceptance app** now does, via its `MediaSpecimen` model — live `/graphql/` tests in `examples/fakeshop/test_query/test_uploads_api.py` cover the read output objects, the default-nullable SDL shape, the empty-file object-`null` case, the `Upload` input SDL, and a real multipart upload. The synthetic-model package tests retain the storage-backend fault-injection / corrupt-image edges (unreachable from a live request). The broader products/fakeshop activation stays `TODO-BETA-053-0.1.5`. See [`docs/GLOSSARY.md#upload-scalar`][glossary-upload-scalar] / [`#djangofiletype`][glossary-djangofiletype] / [`#djangoimagetype`][glossary-djangoimagetype].

<!-- LINK DEFINITIONS -->

<!-- Root -->
[kanban]: KANBAN.md
[goal]: GOAL.md

<!-- docs/ -->
[glossary]: docs/GLOSSARY.md
[glossary-apply-cascade-permissions]: docs/GLOSSARY.md#apply_cascade_permissions
[glossary-djangofiletype]: docs/GLOSSARY.md#djangofiletype
[glossary-djangoformmutation]: docs/GLOSSARY.md#djangoformmutation
[glossary-djangoimagetype]: docs/GLOSSARY.md#djangoimagetype
[glossary-djangomutation]: docs/GLOSSARY.md#djangomutation
[glossary-djangonodefield]: docs/GLOSSARY.md#djangonodefield
[glossary-djangonodesfield]: docs/GLOSSARY.md#djangonodesfield
[glossary-metaconnection]: docs/GLOSSARY.md#metaconnection
[glossary-metanullable_overrides]: docs/GLOSSARY.md#metanullable_overrides
[glossary-metaprimary]: docs/GLOSSARY.md#metaprimary
[glossary-metarelation_shapes]: docs/GLOSSARY.md#metarelation_shapes
[glossary-scalar-field-override-semantics]: docs/GLOSSARY.md#scalar-field-override-semantics
[glossary-upload-scalar]: docs/GLOSSARY.md#upload-scalar

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
