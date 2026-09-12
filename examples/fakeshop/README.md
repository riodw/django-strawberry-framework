# Fakeshop tutorial

A Django project that exercises the shipped surface of `django-strawberry-framework`
end to end, and the tutorial that walks through it. Every declaration below is the real code in
`examples/fakeshop/`, and every query is lifted from the live test suite in
[`test_query/`][test-query-readme], so what you paste into GraphiQL is what the
package is tested against. It is the preliminary shape of the full documentation the
project will grow into; until then it sits between the pitch in the
[root `README.md`][readme] and the reference in [`docs/README.md`][docs-readme].

How to read it alongside the other files:

| You want | Read |
|---|---|
| The one-page case for the package | [`README.md`][readme] |
| A worked path from models to a running API | this file |
| The reference for each surface, transport, and the production profile | [`docs/README.md`][docs-readme] |
| Whether a capability is shipped, planned, or deferred, by anchor | [`docs/GLOSSARY.md`][glossary] |
| What the canonical `products` app can do today | [`TODAY.md`][today] |
| Where the project is going, with the acceptance app it must run | [`GOAL.md`][goal] |
| The design record behind a surface | `docs/SPECS/spec-NNN-*.md`, linked per section |

> **Fakeshop is a fixture, never a deployment.** `DEBUG=True`, a checked-in
> `SECRET_KEY`, GraphiQL, the debug toolbar, multipart uploads, and intentional
> `permission_classes = []` demonstrations are all deliberate, and
> [`config/settings.py`][config-settings] refuses to load with `DEBUG` off. A real
> deployment is a separate project built against the
> [production security profile][docs-readme-security].

## Contents

1. [Run it](#part-1-run-it)
2. [A model becomes a type](#part-2-a-model-becomes-a-type)
3. [Relay nodes and connections](#part-3-relay-nodes-and-connections)
4. [Filtering and ordering](#part-4-filtering-and-ordering)
5. [Visibility](#part-5-visibility)
6. [Two views of one model](#part-6-two-views-of-one-model)
7. [Writing data, three ways](#part-7-writing-data-three-ways)
8. [Uploads](#part-8-uploads)
9. [Session auth](#part-9-session-auth)
10. [Testing what you built](#part-10-testing-what-you-built)
11. [What fakeshop does not show yet](#part-11-what-fakeshop-does-not-show-yet)
12. [Reference: the example project](#reference-the-example-project)

## Part 1: Run it

Fakeshop has no `pyproject.toml` of its own. It imports the package from the
repository root, so everything runs from there with [`uv`][uv]:

```bash
cd /path/to/django-strawberry-framework
uv sync
uv run python examples/fakeshop/manage.py migrate
uv run python examples/fakeshop/manage.py createsuperuser
uv run python examples/fakeshop/manage.py seed_data
uv run python examples/fakeshop/manage.py create_users
uv run python examples/fakeshop/manage.py runserver
```

`seed_data` discovers Faker providers and creates one `Category` per provider with
`Item`, `Property`, and `Entry` rows beneath it. `create_users` creates a set of six
test users, all with the password `admin`: `staff_1` (`is_staff`), `regular_1` (no
permissions), and one `view_<model>_1` holder per products model. Both commands are
idempotent. The shipped `db.sqlite3` already carries a few `library` rows, so the
first queries below return data immediately.

**`db.sqlite3` is tracked by git.** It carries the board and glossary tables the
repository's rendered docs are built from, so every user, catalog row, and upload you
create while following this tutorial lands in a binary file that `git status` will
show as modified. Do not commit that diff. To keep the shipped file clean, work on a
copy: the settings honour `DJANGO_STRAWBERRY_KANBAN_DB`, which points the default
database alias at another file, and every command in this tutorial runs unchanged
with it exported:

```bash
cp examples/fakeshop/db.sqlite3 /tmp/fakeshop-scratch.sqlite3
export DJANGO_STRAWBERRY_KANBAN_DB=/tmp/fakeshop-scratch.sqlite3
```

Then open:

- <http://127.0.0.1:8000/> for the landing page with every dev link
- <http://127.0.0.1:8000/graphql/> for GraphiQL
- <http://127.0.0.1:8000/admin/> for the Django admin

The GraphiQL page carries django-debug-toolbar. After each query, open the toolbar's
SQL panel to see the exact statements the optimizer emitted; that panel is the
instrument this tutorial keeps pointing at. The toolbar sees `/graphql/` traffic
because fakeshop installs the package's
[debug-toolbar middleware][glossary-debug-toolbar-middleware] in place of the stock
one. Setup for your own project is in
[`docs/README.md`][docs-readme-toolbar]; the design record is [spec-042][spec-042].

## Part 2: A model becomes a type

The `library` app is a small circulation system: `Branch` has `Shelf` rows, a `Shelf`
holds `Book` rows, a `Book` has many `Genre` rows, and a `Patron` borrows books
through `Loan` rows and owns one `MembershipCard`. The models in
[`apps/library/models.py`][lib-models] are plain Django with no GraphQL coupling.

Here is the type over `Book`, from [`apps/library/schema.py`][lib-schema], with its
comments removed:

```python
from strawberry import relay

from django_strawberry_framework import DjangoType


class BookType(DjangoType):
    @classmethod
    def get_queryset(cls, queryset, info):
        if _user_is_staff(info):
            return queryset
        return queryset.exclude(circulation_status=models.Book.CirculationStatus.REPAIR)

    class Meta:
        model = models.Book
        primary = True
        fields = (
            "id",
            "title",
            "subtitle",
            "circulation_status",
            "shelf",
            "genres",
            "loans",
        )
        interfaces = (relay.Node,)
        relation_shapes = {"genres": "both"}
        filterset_class = filters.BookFilter
        orderset_class = orders.BookOrder
```

Everything about model mapping and generated schema shape is declared in `class Meta`;
the one method is a hook, not configuration. That is the whole idea of the package:
Strawberry is the engine, and the configuration surface is the one Django developers
already know from DRF and django-filter. Nothing is decorated.

- [`Meta.model`][glossary-metamodel] and [`Meta.fields`][glossary-metafields] pick the
  columns and relations. `shelf` is a forward FK, `genres` is an M2M, `loans` is a
  reverse FK; all three become typed fields with resolvers you did not write.
- `circulation_status` is a `TextChoices` column, so the package generates a GraphQL
  enum for it ([choice enum generation][glossary-choice-enum-generation]).
- [`Meta.interfaces`][glossary-metainterfaces] with `relay.Node` makes it a Relay node.
  Part 3 uses that.
- [`Meta.filterset_class`][glossary-metafilterset_class] and
  [`Meta.orderset_class`][glossary-metaorderset_class] attach the sidecars Part 4 uses.
- `get_queryset` is the DRF-style visibility hook. Part 5 uses that.

Types are collected as they are defined and resolved once, after every module has
been imported. [`config/schema.py`][config-schema] composes the per-app `Query` and
`Mutation` classes and then does the three things every consumer project does:

```python
finalize_django_types()

_optimizer = DjangoOptimizerExtension()
schema = DjangoSchema(
    query=Query,
    mutation=Mutation,
    config=strawberry_config(),
    extensions=[lambda: _optimizer],
)
```

[`finalize_django_types()`][glossary-finalize_django_types] resolves every relation
target, in any definition order, and raises if a relation points at a model with no
registered type. The optimizer is a module-level singleton wrapped in a callable so
its cross-request [plan cache][glossary-plan-cache] survives. `DjangoSchema` rather
than `strawberry.Schema` is what lets generated mutations span their transaction
across the response ([why][docs-readme-djangoschema]).

Now run this in GraphiQL:

```graphql
{
  allLibraryBooks {
    title
    circulationStatus
    shelf {
      code
      topic
    }
    genres {
      name
    }
  }
}
```

Open the SQL panel. The book list, the shelf prefetch, and the genre prefetch arrive
in a constant number of statements no matter how many books there are. The
[`DjangoOptimizerExtension`][glossary-djangooptimizerextension] walked the selection
once at the root and applied one ORM plan. Nothing in the resolver asked for it.

Look at how the shelf arrived. A forward FK would normally be a `JOIN` on the book
query, but `ShelfType` declares a [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook],
so the optimizer plans it as a separate prefetch through that hook instead. A `JOIN`
would surface shelf rows the hook hides; the prefetch cannot. One shelf statement
alongside the book statement, no `JOIN`, and the visibility rule still applies to the
nested object.

For the cheapest shape of all, switch to the `scalars` app, whose `ScalarSpecimen`
has a self-referential `parent` FK and no hook on its type:

```graphql
{
  allScalarSpecimens {
    label
    parent {
      id
    }
  }
}
```

One statement, no `JOIN`, no prefetch. The `id` of a forward FK is the column already
sitting on the source row, and the optimizer reads it from there
([FK-id elision][glossary-fk-id-elision]). Elision needs a target type without a
visibility hook; `shelf { id }` on the books query stays a prefetch for the reason above.

Under test you can make an unplanned lazy load a failure instead of a slow request:
`DjangoOptimizerExtension(strictness="raise")` is the detective mode
([strictness mode][glossary-strictness-mode]). Fakeshop's aggregate schema runs the
default so every demo below tolerates consumer-authored resolvers.

Design records: [spec-001][spec-001] (types), [spec-002][spec-002] (optimizer).

## Part 3: Relay nodes and connections

`GenreType` is a Relay node with a connection over it:

```python
class GenreType(DjangoType):
    class Meta:
        model = models.Genre
        fields = ("id", "name", "books")
        interfaces = (relay.Node, Named)
        relation_shapes = {"books": "both"}
        filterset_class = filters_genre.GenreFilter
        orderset_class = orders_genre.GenreOrder
        connection = {"total_count": True}
```

and the root field is one line:

```python
all_library_genres_connection: DjangoConnection[GenreType] = DjangoConnectionField(GenreType)
```

Page through it:

```graphql
{
  allLibraryGenresConnection(
    first: 2
  ) {
    totalCount
    edges {
      cursor
      node {
        id
        name
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

Copy `endCursor` into `after:` for the next page. `totalCount` is there because
[`Meta.connection`][glossary-metaconnection] opted in; without it the field is not
in the schema at all. [`DjangoConnectionField`][glossary-djangoconnectionfield]
derives `filter:` and `orderBy:` arguments from the sidecars on the node type, so the
Part 4 arguments work on connections too.

Every `id` you just received is a `GlobalID`. Copy one and refetch it through the root
node fields, which `Query` declares with
[`DjangoNodeField`][glossary-djangonodefield] and `DjangoNodesField`:

```graphql
{
  node(
    id: "PASTE_A_GENRE_ID"
  ) {
    ... on GenreType {
      name
    }
  }
  genre(
    id: "PASTE_THE_SAME_ID"
  ) {
    name
  }
}
```

The default payload inside a `GlobalID` is the Django model label, `library.genre:7`,
not the GraphQL type name, so renaming a type does not invalidate ids a client cached
([Relay Node integration][glossary-relay-node-integration],
[`Meta.globalid_strategy`][glossary-metaglobalid_strategy]).

The `products` app shows the same shape on a bigger catalog. All four of its root
fields are connections, and `seed_data` filled them:

```graphql
{
  allItems(
    first: 5
  ) {
    edges {
      node {
        id
        name
        category {
          name
        }
      }
    }
  }
}
```

`relation_shapes = {"books": "both"}` on `GenreType` is the opt-in for a raw list
beside the connection. Since `0.0.14` a many-side relation on a Relay node renders as
a connection only, so `genre { books { title } }` and `genre { booksConnection { ... } }`
coexist here because the type asked for both
([`Meta.relation_shapes`][glossary-metarelation_shapes]).

For a plain list without cursors, `DjangoListField` is the alternative. `Query`
declares `allLibraryBranchesViaListField` that way; it publishes `offset` and `limit`
and, because `BranchType` has an `OrderSet`, an `orderBy` argument
([`DjangoListField`][glossary-djangolistfield],
[list offset order precondition][glossary-list-offset-order-precondition]).

`IssueType` in the same file declares `cursor_field = ("-number", "id")`, which turns
its connections into keyset mode: value-encoded cursors that survive inserts and
deletes, exercised by [`test_keyset_api.py`][test-keyset-api].

Design records: [spec-030][spec-030] (connection field), [spec-031][spec-031]
(GlobalID encoding), [spec-032][spec-032] (full Relay), [spec-020][spec-020] (list field).

## Part 4: Filtering and ordering

The sidecars are declared once, next to the models, in
[`apps/library/filters.py`][lib-filters] and [`apps/library/orders.py`][lib-orders]:

```python
from django_strawberry_framework.filters import FilterSet, RelatedFilter
from django_strawberry_framework.orders import OrderSet, RelatedOrder


class BookFilter(FilterSet):
    shelf = RelatedFilter("ShelfFilter", field_name="shelf")
    genres = RelatedFilter("apps.library.filters_genre.GenreFilter", field_name="genres")
    loans = RelatedFilter("LoanFilter", field_name="loans")

    class Meta:
        model = models.Book
        fields = {
            "id": ["exact", "in"],
            "title": ["exact", "icontains"],
            "subtitle": ["exact", "icontains", "isnull"],
            "circulation_status": ["exact", "in"],
        }


class BookOrder(OrderSet):
    shelf = RelatedOrder("ShelfOrder", field_name="shelf")
    genres = RelatedOrder("apps.library.orders_genre.GenreOrder", field_name="genres")
    loans = RelatedOrder("LoanOrder", field_name="loans")

    class Meta:
        model = models.Book
        fields = [
            "id",
            "title",
            "subtitle",
            "circulation_status",
            "shelf__code",
        ]
```

If you have used django-filter, the `Meta.fields` dict is the one you know. The
package's [`FilterSet`][glossary-filterset] is a `django_filters` `BaseFilterSet`
subclass, so an existing filterset migrates with a parent-class swap.
[`RelatedFilter`][glossary-relatedfilter] and [`RelatedOrder`][glossary-relatedorder]
traverse relations, and accept a class, an import path string, or an unqualified
name from the same module for the circular cases.

`BookType.Meta` bound both sidecars in Part 2, so the arguments are already on
`allLibraryBooks`:

```graphql
{
  allLibraryBooks(
    filter: {
      circulationStatus: {
        in: [
          available
          checked_out
        ]
      }
      title: {
        iContains: "the"
      }
      shelf: {
        topic: {
          iContains: "fiction"
        }
      }
    }
    orderBy: [
      {
        shelf: {
          code: ASC
        }
      }
      {
        title: DESC
      }
    ]
  ) {
    title
    circulationStatus
    shelf {
      code
    }
  }
}
```

`available` and `checked_out` are the enum values generated from the model's
`TextChoices`. Lookup names camel-case on the wire, so the `icontains` you declared
is `iContains` in the query. The `shelf: { topic: ... }` branch is `BookFilter.shelf` reaching into
`ShelfFilter`. The `shelf__code` path shorthand in `BookOrder.Meta.fields` also
renders as a flat `shelfCode: ASC` on the same input type.

Sidecars carry per-field permission gates. `BranchOrder` denies an anonymous order by
`name` but lets `city` through:

```python
class BranchOrder(OrderSet):
    shelves = RelatedOrder("ShelfOrder", field_name="shelves")

    class Meta:
        model = models.Branch
        fields = ["id", "name", "city"]

    @classmethod
    def check_name_permission(cls, request):
        user = getattr(request, "user", None)
        if user is None or not getattr(user, "is_staff", False):
            raise GraphQLError("staff only", extensions={"code": "ORDER_PERMISSION_DENIED"})
```

Run `allLibraryBranches(orderBy: [{ name: ASC }]) { name }` while logged out and you
get that error with its extension code; `orderBy: [{ city: ASC }]` is quiet. The gate
fires only when the input names the guarded field
([per-field permission hooks][glossary-per-field-permission-hooks]).

Reference: [filtering][docs-readme-filtering] and [ordering][docs-readme-ordering] in
`docs/README.md`. Design records: [spec-027][spec-027], [spec-028][spec-028].

## Part 5: Visibility

`BookType.get_queryset` in Part 2 hides `repair` books from anyone who is not staff.
That one hook is the row-level rule for every path to a book: the root list, the
connection, the `node(id:)` refetch, a nested `shelf { books { ... } }`, and the
locate step of a mutation ([`get_queryset` visibility hook][glossary-get_queryset-visibility-hook]).

See it flip. First, logged out:

```graphql
{
  allLibraryBooks {
    title
    circulationStatus
  }
}
```

No `repair` rows. Now log in as the staff test user through the auth surface (Part 9
covers it fully). GraphiQL keeps the session cookie, so every query after this one is
authenticated:

```graphql
mutation {
  login(
    username: "staff_1"
    password: "admin"
  ) {
    node {
      username
    }
    errors {
      field
      messages
    }
  }
}
```

Run the book query again and the `repair` rows are back.

The `products` app applies the same hook with a cascade. Every non-staff branch
narrows the queryset and wraps it in `apply_cascade_permissions`, so a visible
`Item` can never point at a `Category` the viewer cannot see, and a nested non-null
FK selection never surfaces a row the parent rule hid
([`apply_cascade_permissions`][glossary-apply_cascade_permissions]). Condensed from
`CategoryType.get_queryset`:

```python
@classmethod
def get_queryset(cls, queryset, info):
    user = getattr(getattr(info.context, "request", None), "user", None)
    if user and user.is_staff:
        return queryset
    return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)
```

Log in as `regular_1` and `staff_1` in turn and compare
`allCategories { edges { node { name isPrivate } } }`.

The hook is enforced at the queryset boundary, not by a list of resolver call sites,
which is why a consumer-authored resolver or a custom `Prefetch` cannot route around
it ([visibility boundary][glossary-visibility-boundary]).

Reference: [visibility and permissions][docs-readme-visibility]. Design records:
[spec-034][spec-034], [spec-045][spec-045].

## Part 6: Two views of one model

A model may have more than one type. `Patron` has an internal view and a public one,
both in [`apps/library/schema.py`][lib-schema]:

```python
class PatronType(DjangoType):
    class Meta:
        model = models.Patron
        primary = True
        fields = ("id", "name", "lifetime_fines_cents", "card", "loans")
        interfaces = (Named,)
        filterset_class = filters.PatronFilter
        orderset_class = orders.PatronOrder


class PublicPatronType(DjangoType):
    class Meta:
        model = models.Patron
        primary = False
        exclude = ("email", "lifetime_fines_cents")
        name = "PublicPatron"
        description = "A patron projection with PII (email) and financial columns removed."
```

`fields` is the allow-list and [`Meta.exclude`][glossary-metaexclude] is the
deny-list; a type uses one or the other. Exactly one type per model is
[`primary`][glossary-metaprimary], and that is the one every relation to `Patron`
resolves to. [`Meta.name`][glossary-metaname] decouples the GraphQL name from the
class, and [`Meta.description`][glossary-metadescription] shows up in introspection.

The shipped database has no patrons, so add one:

```bash
uv run python examples/fakeshop/manage.py shell -c "
from apps.library import models
p = models.Patron.objects.create(name='Ada', email='ada@example.com')
models.MembershipCard.objects.create(patron=p, barcode='0001')
models.Loan.objects.create(patron=p, book=models.Book.objects.first(), note='first loan')
"
```

Then compare the two root fields:

```graphql
{
  allLibraryPatrons {
    name
    lifetimeFinesCents
    card {
      barcode
    }
  }
  allLibraryPublicPatrons {
    name
    card {
      barcode
    }
    loans {
      note
    }
  }
}
```

Ask GraphiQL for `lifetimeFinesCents` on the public field and the query fails
validation: the column is not in that type. Design record: [spec-018][spec-018].

## Part 7: Writing data, three ways

Mutations are declared the same way types are. The `products` app writes the same
`Item` model three ways, in [`apps/products/schema.py`][products-schema]:

```python
class CreateItem(DjangoMutation):
    class Meta:
        model = models.Item
        operation = "create"


class CreateItemViaForm(DjangoModelFormMutation):
    class Meta:
        form_class = forms.ItemModelForm
        operation = "create"


class CreateItemViaSerializer(SerializerMutation):
    class Meta:
        serializer_class = serializers.ItemSerializer
        operation = "create"


@strawberry.type
class Mutation:
    create_item = DjangoMutationField(CreateItem)
    create_item_via_form = DjangoMutationField(CreateItemViaForm)
    create_item_via_serializer = DjangoMutationField(CreateItemViaSerializer)
```

The `ModelForm` in [`apps/products/forms.py`][products-forms] and the
`ModelSerializer` in [`apps/products/serializers.py`][products-serializers] are
ordinary Django and DRF classes with their own `clean_name` and `validate_name`. The
package generates the input type from whichever source you named
([input type generation][glossary-input-type-generation]): `ItemInput`,
`ItemModelFormInput`, and `ItemSerializerInput` here. All three return the same
payload shape, `node` plus an `errors` list of
[`FieldError`][glossary-fielderror-envelope].

Writes are denied by default. [`DjangoModelPermission`][glossary-djangomodelpermission]
requires Django's `add_item` for a create, and the test users do not have it, so log
in as the superuser you created in Part 1 (use the `login` mutation from Part 5 with
your own credentials). Then fetch a category id and create an item:

```graphql
{
  allCategories(
    first: 1
  ) {
    edges {
      node {
        id
        name
      }
    }
  }
}
```

```graphql
mutation {
  createItem(
    data: {
      name: "Widget"
      categoryId: "PASTE_THE_CATEGORY_ID"
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

`categoryId` is the FK, taking the same `GlobalID` string the read side emits. Now
send the same data through the other two flavors and watch the envelope stay
identical:

```graphql
mutation {
  createItemViaForm(
    data: {
      name: "Widget via form"
      categoryId: "PASTE_THE_CATEGORY_ID"
    }
  ) {
    node {
      name
    }
    errors {
      field
      messages
    }
  }
  createItemViaSerializer(
    data: {
      name: "Widget via serializer"
      categoryId: "PASTE_THE_CATEGORY_ID"
    }
  ) {
    node {
      name
    }
    errors {
      field
      messages
    }
  }
}
```

Validation flows through the same envelope. The example form rejects the name
`__rejected__` and the serializer rejects `__serializer_rejected__`; send either and
`errors` comes back with `field: "name"` and the message your `clean_name` or
`validate_name` raised. A model-wide constraint failure keys to `field: "__all__"`.

Each mutation runs in one transaction that spans the response, so a failure after the
write leaves nothing behind. Update and delete are `operation = "update"` and
`operation = "delete"` on the same `Meta`; the update flavors take `id:` plus a
`PartialInput` where every field is optional.

Reference: [writing data][docs-readme-writing] in `docs/README.md`. Design records:
[spec-036][spec-036] (model), [spec-038][spec-038] (form), [spec-039][spec-039]
(serializer).

## Part 8: Uploads

`MediaSpecimen` in the `scalars` app has a `FileField` and an `ImageField`. On read
they convert to structured [`DjangoFileType`][glossary-djangofiletype] and
[`DjangoImageType`][glossary-djangoimagetype]; on write both map to Strawberry's
[`Upload`][glossary-upload-scalar] scalar in the generated `MediaSpecimenInput`. The
mutation is the same two-line declaration as Part 7, over
`models.MediaSpecimen`, in [`apps/scalars/schema.py`][scalars-schema].

GraphiQL cannot attach files, so this one is a
[GraphQL multipart request][graphql-multipart] from the shell. Fakeshop's `/graphql/`
keeps CSRF protection on (deliberately, see [spec-046][spec-046]), so fetch the cookie
first and echo it back as a header. The write needs `add_mediaspecimen`, so the same
`curl` session logs in as your superuser before it uploads. A successful login rotates
the CSRF secret and the `-c` flag writes the new cookie into the jar, so the token is
read from the jar a second time after the login; reusing the pre-login value gets a
403. The two fixture files are created first, the PNG through Pillow so that the
`ImageField` validation accepts it:

```bash
printf 'first attachment\n' > notes.txt
uv run python -c "from PIL import Image; Image.new('RGB', (4, 4), 'red').save('photo.png')"
curl -s -c /tmp/fakeshop.jar http://127.0.0.1:8000/graphql/ > /dev/null
TOKEN=$(awk '/csrftoken/ {print $7}' /tmp/fakeshop.jar)
curl -s -b /tmp/fakeshop.jar -c /tmp/fakeshop.jar -H "X-CSRFToken: $TOKEN" \
  -H "Content-Type: application/json" http://127.0.0.1:8000/graphql/ \
  -d '{"query":"mutation { login(username: \"YOUR_SUPERUSER\", password: \"YOUR_PASSWORD\") { errors { field messages } } }"}'
TOKEN=$(awk '/csrftoken/ {print $7}' /tmp/fakeshop.jar)
curl -b /tmp/fakeshop.jar -H "X-CSRFToken: $TOKEN" http://127.0.0.1:8000/graphql/ \
  -F operations='{"query":"mutation Create($data: MediaSpecimenInput!) { createMediaSpecimen(data: $data) { result { label attachment { name size url } image { name width height } } errors { field messages } } }","variables":{"data":{"label":"first","attachment":null,"image":null}}}' \
  -F map='{"0":["variables.data.attachment"],"1":["variables.data.image"]}' \
  -F 0=@notes.txt \
  -F 1=@photo.png
```

`MediaSpecimenType` is not a Relay node, so the payload carries the row in `result`
rather than `node`. The `url` in the response is a public URL; the server's
filesystem path is never on the wire. The package bounds upload bytes through the
[execution resource policy][glossary-execution-resource-policy]; scanning and content
rules belong to the deployment ([uploads in the production profile][docs-readme-uploads]).

Design record: [spec-037][spec-037].

## Part 9: Session auth

The `accounts` app is schema only. It declares a `UserType` over `auth.User` and
wires the four opt-in auth fields, all in
[`apps/accounts/schema.py`][accounts-schema]:

```python
from django_strawberry_framework.auth import (
    current_user,
    login_mutation,
    logout_mutation,
    register_mutation,
)


class UserType(DjangoType):
    class Meta:
        model = get_user_model()
        fields = ("id", "username", "email")
        interfaces = (relay.Node,)


@strawberry.type
class Query:
    me = current_user()


@strawberry.type
class Mutation:
    login = login_mutation()
    logout = logout_mutation()
    register = register_mutation()
```

`UserType`'s field list is the authenticated read surface: whatever it selects is what
`login`, `register`, and `me` return, which is why it names its fields and keeps
`password`, `is_staff`, and `is_superuser` off.

Walk the session:

```graphql
{
  me {
    username
  }
}
```

`null` while logged out. Register, which logs the new user in:

```graphql
mutation {
  register(
    data: {
      username: "reader"
      password: "a-long-enough-passphrase"
    }
  ) {
    node {
      username
    }
    errors {
      field
      messages
      codes
    }
  }
}
```

Django's password validators run, so a weak password comes back in `errors` with
structured `codes`. Run `me` again, then:

```graphql
mutation {
  logout {
    ok
  }
}
```

`login` rotates the session key on success and collapses wrong password, unknown user,
and inactive user into one byte-identical failure envelope. The framework ships no
throttling for these anonymous surfaces; the production profile shows where to put it
([login and registration][docs-readme-auth-throttle]).

Reference: [session auth][docs-readme-session-auth]. Design record: [spec-040][spec-040].

## Part 10: Testing what you built

Everything above is pinned by live HTTP tests in [`test_query/`][test-query-readme],
which post real requests to `/graphql/` through Django's test client. Read them as the
long-form version of this tutorial: [`test_library_api.py`][test-library-api] for
Parts 2 through 6, [`test_products_api.py`][test-products-api] for Part 7,
[`test_uploads_api.py`][test-uploads-api] for Part 8, and
[`test_auth_api.py`][test-auth-api] for Part 9.

For your own project, the package ships a [`TestClient`][glossary-testclient] family
that drives the in-process test client and returns a typed response:

```python
from django_strawberry_framework.testing import TestClient


def test_books():
    response = TestClient().query("{ allLibraryBooks { title } }")

    assert response.errors is None
    assert response.data["allLibraryBooks"]
```

A `GraphQLTestCase` unittest flavor exists as well
([reference][docs-readme-testing], [spec-043][spec-043]).

Run fakeshop's own suites from the repository root:

```bash
uv run pytest examples/fakeshop
```

The tiers, the isolation contract between them, and the sharded and Postgres
variants are contributor territory and documented in
[`CONTRIBUTING.md`][contributing].

## Part 11: What fakeshop does not show yet

The [`astronomy` app in `GOAL.md`][goal] declares three sidecars fakeshop cannot run
today. Each has an owning card on the [board][kanban]; the first two also have a
design record, and the aggregation card lists authoring its spec as still open:

- `Meta.fields_class` and [`FieldSet`][glossary-fieldset], for per-field redaction,
  denial gates, and computed fields ([spec-059][spec-059]).
- [`Meta.search_fields`][glossary-metasearch_fields], for a generated `search:`
  argument across scalar and relation paths ([spec-060][spec-060]).
- `Meta.aggregate_class` and [`AggregateSet`][glossary-aggregateset], for per-type
  `count` / `min` / `max` / custom stats over the filtered queryset (spec pending).

The `products` app carries commented-out `Meta` lines for all three, so the day a
slice ships the demonstration is one uncomment away.
[`TODAY.md`][today] tracks that list against the canonical app.

## Reference: the example project

### Apps

- **`apps.library`**: the acceptance app this tutorial is built on. FK, reverse FK,
  OneToOne, M2M, Relay nodes, keyset cursors, optimizer hints, consumer relation
  overrides, `FilterSet` / `OrderSet` on every type, root `node` / `nodes` refetch.
- **`apps.products`**: the canonical consumer app and the subject of
  [`TODAY.md`][today]. Four Relay connections over `Category` / `Item` / `Property` /
  `Entry`, the full write surface in all three flavors, cascade visibility, plus the
  admin, services, and management commands.
- **`apps.scalars`**: one specimen row per scalar wire format, and the
  `MediaSpecimen` file and image surface.
- **`apps.accounts`**: the schema-only session-auth surface.
- **`apps.kanban`** and **`apps.glossary`**: docs-as-data. Relational sources for
  the rendered [`KANBAN.md`][kanban] and [`docs/GLOSSARY.md`][glossary], regenerated by
  [`build_kanban_md.py`][build-kanban-md] and [`build_glossary_md.py`][build-glossary].
  Not part of the tutorial.

### Layout

```
examples/fakeshop/
├── apps/
│   ├── accounts/       # schema-only session auth
│   ├── glossary/       # glossary terms + spec-term audit rows
│   ├── kanban/         # board source tables
│   ├── library/        # acceptance schema (this tutorial)
│   ├── products/       # canonical consumer app + seed/admin tooling
│   └── scalars/        # scalar converter substrate + file/image surface
├── config/
│   ├── schema.py       # composes per-app Query/Mutation, finalizes, mounts the optimizer
│   ├── settings.py     # single-DB default; FAKESHOP_SHARDED / FAKESHOP_PG_DSN tiers
│   ├── test_settings.py
│   ├── urls.py         # /, /graphql/, /admin/, /login/, /logout/, toolbar routes
│   └── wsgi.py
├── media/              # runserver upload target (tests use a temp MEDIA_ROOT)
├── tests/              # project/config-level tests
├── test_query/         # live /graphql/ HTTP tests
├── db.sqlite3          # tracked fixture: seeded rows plus the board and glossary tables
├── db_shard_b.sqlite3  # tracked secondary shard for FAKESHOP_SHARDED=1
├── graphql_client.py   # shared live-/graphql/ helpers for the test suites
├── schema_reload.py    # full config.schema reload for registry-clearing tests
├── strategy_schemas.py # shared schema builders for pg-parity tests + benchmarks
└── manage.py
```

### Management commands

All from the repository root, all idempotent where that makes sense. The landing page
at `/` links the admin equivalents of the products commands.

```bash
uv run python examples/fakeshop/manage.py seed_data 50        # 50 items per Faker provider
uv run python examples/fakeshop/manage.py delete_data 10      # first 10 items (cascading entries)
uv run python examples/fakeshop/manage.py delete_data all     # every item and entry
uv run python examples/fakeshop/manage.py delete_data everything  # wipe all four tables
uv run python examples/fakeshop/manage.py create_users 3      # 3 sets of 6 test users, password admin
uv run python examples/fakeshop/manage.py delete_users all    # every non-superuser
```

### Database modes

The default is one SQLite file. `FAKESHOP_SHARDED=1` adds a `shard_b` alias on
`db_shard_b.sqlite3` beside `default`, for exercising querysets bound to non-default
aliases ([multi-database cooperation][glossary-multi-database-cooperation],
[spec-023][spec-023]):

```bash
FAKESHOP_SHARDED=1 uv run python examples/fakeshop/manage.py seed_shards --count 5
FAKESHOP_SHARDED=1 uv run python examples/fakeshop/manage.py runserver
```

`FAKESHOP_PG_DSN` swaps `default` to a Postgres server, the vendor the optimizer's
`LATERAL` nested-pagination strategy is verified on. It is mutually exclusive with
`FAKESHOP_SHARDED` and needs the `pg` dependency group:

```bash
uv sync --group pg
docker compose -f docker-compose.postgres.yml up -d
FAKESHOP_PG_DSN=postgres://fakeshop:fakeshop@127.0.0.1:5432/fakeshop uv run pytest
```

<!-- LINK DEFINITIONS -->

<!-- Root -->
[contributing]: ../../CONTRIBUTING.md
[goal]: ../../GOAL.md
[kanban]: ../../KANBAN.md
[readme]: ../../README.md
[today]: ../../TODAY.md

<!-- docs/ -->
[docs-readme]: ../../docs/README.md
[docs-readme-auth-throttle]: ../../docs/README.md#login-and-registration-are-anonymous-surfaces--throttle-them
[docs-readme-djangoschema]: ../../docs/README.md#djangoschema-is-required-for-generated-mutations
[docs-readme-filtering]: ../../docs/README.md#filtering-with-filterset
[docs-readme-ordering]: ../../docs/README.md#ordering-with-orderset
[docs-readme-security]: ../../docs/README.md#production-security-profile
[docs-readme-session-auth]: ../../docs/README.md#session-auth
[docs-readme-testing]: ../../docs/README.md#testing-graphql-endpoints
[docs-readme-toolbar]: ../../docs/README.md#django-debug-toolbar
[docs-readme-uploads]: ../../docs/README.md#uploads-the-package-bounds-bytes-the-deployment-owns-content
[docs-readme-visibility]: ../../docs/README.md#visibility-and-permissions
[docs-readme-writing]: ../../docs/README.md#writing-data
[glossary]: ../../docs/GLOSSARY.md
[glossary-aggregateset]: ../../docs/GLOSSARY.md#aggregateset
[glossary-apply_cascade_permissions]: ../../docs/GLOSSARY.md#apply_cascade_permissions
[glossary-choice-enum-generation]: ../../docs/GLOSSARY.md#choice-enum-generation
[glossary-debug-toolbar-middleware]: ../../docs/GLOSSARY.md#debug-toolbar-middleware
[glossary-djangoconnectionfield]: ../../docs/GLOSSARY.md#djangoconnectionfield
[glossary-djangofiletype]: ../../docs/GLOSSARY.md#djangofiletype
[glossary-djangoimagetype]: ../../docs/GLOSSARY.md#djangoimagetype
[glossary-djangolistfield]: ../../docs/GLOSSARY.md#djangolistfield
[glossary-djangomodelpermission]: ../../docs/GLOSSARY.md#djangomodelpermission
[glossary-djangonodefield]: ../../docs/GLOSSARY.md#djangonodefield
[glossary-djangooptimizerextension]: ../../docs/GLOSSARY.md#djangooptimizerextension
[glossary-execution-resource-policy]: ../../docs/GLOSSARY.md#execution-resource-policy
[glossary-fielderror-envelope]: ../../docs/GLOSSARY.md#fielderror-envelope
[glossary-fieldset]: ../../docs/GLOSSARY.md#fieldset
[glossary-filterset]: ../../docs/GLOSSARY.md#filterset
[glossary-finalize_django_types]: ../../docs/GLOSSARY.md#finalize_django_types
[glossary-fk-id-elision]: ../../docs/GLOSSARY.md#fk-id-elision
[glossary-get_queryset-visibility-hook]: ../../docs/GLOSSARY.md#get_queryset-visibility-hook
[glossary-input-type-generation]: ../../docs/GLOSSARY.md#input-type-generation
[glossary-list-offset-order-precondition]: ../../docs/GLOSSARY.md#list-offset-order-precondition
[glossary-metaconnection]: ../../docs/GLOSSARY.md#metaconnection
[glossary-metadescription]: ../../docs/GLOSSARY.md#metadescription
[glossary-metaexclude]: ../../docs/GLOSSARY.md#metaexclude
[glossary-metafields]: ../../docs/GLOSSARY.md#metafields
[glossary-metafilterset_class]: ../../docs/GLOSSARY.md#metafilterset_class
[glossary-metaglobalid_strategy]: ../../docs/GLOSSARY.md#metaglobalid_strategy
[glossary-metainterfaces]: ../../docs/GLOSSARY.md#metainterfaces
[glossary-metamodel]: ../../docs/GLOSSARY.md#metamodel
[glossary-metaname]: ../../docs/GLOSSARY.md#metaname
[glossary-metaorderset_class]: ../../docs/GLOSSARY.md#metaorderset_class
[glossary-metaprimary]: ../../docs/GLOSSARY.md#metaprimary
[glossary-metarelation_shapes]: ../../docs/GLOSSARY.md#metarelation_shapes
[glossary-metasearch_fields]: ../../docs/GLOSSARY.md#metasearch_fields
[glossary-multi-database-cooperation]: ../../docs/GLOSSARY.md#multi-database-cooperation
[glossary-per-field-permission-hooks]: ../../docs/GLOSSARY.md#per-field-permission-hooks
[glossary-plan-cache]: ../../docs/GLOSSARY.md#plan-cache
[glossary-relatedfilter]: ../../docs/GLOSSARY.md#relatedfilter
[glossary-relatedorder]: ../../docs/GLOSSARY.md#relatedorder
[glossary-relay-node-integration]: ../../docs/GLOSSARY.md#relay-node-integration
[glossary-strictness-mode]: ../../docs/GLOSSARY.md#strictness-mode
[glossary-testclient]: ../../docs/GLOSSARY.md#testclient
[glossary-upload-scalar]: ../../docs/GLOSSARY.md#upload-scalar
[glossary-visibility-boundary]: ../../docs/GLOSSARY.md#visibility-boundary

<!-- docs/SPECS/ -->
[spec-001]: ../../docs/SPECS/spec-001-django_types-0_0_1.md
[spec-002]: ../../docs/SPECS/spec-002-optimizer-0_0_2.md
[spec-018]: ../../docs/SPECS/spec-018-meta_primary-0_0_6.md
[spec-020]: ../../docs/SPECS/spec-020-list_field-0_0_7.md
[spec-023]: ../../docs/SPECS/spec-023-multi_db-0_0_7.md
[spec-027]: ../../docs/SPECS/spec-027-filters-0_0_8.md
[spec-028]: ../../docs/SPECS/spec-028-orders-0_0_8.md
[spec-030]: ../../docs/SPECS/spec-030-connection_field-0_0_9.md
[spec-031]: ../../docs/SPECS/spec-031-globalid_encoding-0_0_9.md
[spec-032]: ../../docs/SPECS/spec-032-full_relay-0_0_9.md
[spec-034]: ../../docs/SPECS/spec-034-permissions-0_0_10.md
[spec-036]: ../../docs/SPECS/spec-036-mutations-0_0_11.md
[spec-037]: ../../docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md
[spec-038]: ../../docs/SPECS/spec-038-form_mutations-0_0_12.md
[spec-039]: ../../docs/SPECS/spec-039-serializer_mutations-0_0_13.md
[spec-040]: ../../docs/SPECS/spec-040-auth_mutations-0_0_13.md
[spec-042]: ../../docs/SPECS/spec-042-debug_toolbar-0_0_14.md
[spec-043]: ../../docs/SPECS/spec-043-test_client-0_0_14.md
[spec-045]: ../../docs/SPECS/spec-045-visibility_boundary-0_0_14.md
[spec-046]: ../../docs/SPECS/spec-046-transport_security-0_0_14.md
[spec-059]: ../../docs/SPECS/spec-059-fieldset-0_1_1.md
[spec-060]: ../../docs/SPECS/spec-060-search_fields-0_1_2.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->
[accounts-schema]: apps/accounts/schema.py
[config-schema]: config/schema.py
[config-settings]: config/settings.py
[lib-filters]: apps/library/filters.py
[lib-models]: apps/library/models.py
[lib-orders]: apps/library/orders.py
[lib-schema]: apps/library/schema.py
[products-forms]: apps/products/forms.py
[products-schema]: apps/products/schema.py
[products-serializers]: apps/products/serializers.py
[scalars-schema]: apps/scalars/schema.py
[test-auth-api]: test_query/test_auth_api.py
[test-keyset-api]: test_query/test_keyset_api.py
[test-library-api]: test_query/test_library_api.py
[test-products-api]: test_query/test_products_api.py
[test-query-readme]: test_query/README.md
[test-uploads-api]: test_query/test_uploads_api.py

<!-- scripts/ -->
[build-glossary]: ../../scripts/build_glossary_md.py
[build-kanban-md]: ../../scripts/build_kanban_md.py

<!-- .venv/ -->

<!-- External -->
[graphql-multipart]: https://github.com/jaydenseric/graphql-multipart-request-spec
[uv]: https://docs.astral.sh/uv/
