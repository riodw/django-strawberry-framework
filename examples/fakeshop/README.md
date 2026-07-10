# Fakeshop Example Django Project

A Django + Strawberry GraphQL example project that exercises
`django-strawberry-framework` end-to-end. It ships six app surfaces:

- **`apps.library`** — acceptance app with a real `DjangoType` schema
  (FK, reverse FK, OneToOne, M2M, Relay `Node`, optimizer hints,
  consumer relation overrides) plus `FilterSet` / `OrderSet` sidecars on
  every type, the root `node(id:)` / `nodes(ids:)` Relay refetch fields,
  and a `totalCount`-enabled genre connection. This is the primary
  acceptance slice.
- **`apps.products`** — working `DjangoType` schema over `Category` /
  `Item` / `Property` / `Entry`. The four root fields
  (`allCategories` / `allItems` / `allProperties` / `allEntries`) are
  `DjangoConnectionField` Relay connections with synthesized `filter:` /
  `orderBy:` arguments from the `FilterSet` / `OrderSet` sidecars
  (`Meta.filterset_class` / `Meta.orderset_class`). Also carries the
  package's full write surface — model-driven `DjangoMutation`,
  form-backed (`0.0.12`), and DRF-serializer-backed (`0.0.13`) mutation
  flavors on one `Mutation` type — plus migrations, models, admin,
  services, and management commands so the seed / delete / user flows
  work.
- **`apps.scalars`** — converter-table substrate for scalar wire formats,
  plus the `MediaSpecimen` file/image surface (structured
  `DjangoFileType` / `DjangoImageType` read output and a live multipart
  `Upload` mutation).
- **`apps.accounts`** — schema-only session-auth surface: `login` /
  `logout` / `register` mutations and the `me` query over `auth.User`.
- **`apps.kanban`** — relational source for the exported root `KANBAN.md`
  and the `KANBAN.html` dashboard's data block.
- **`apps.glossary`** — relational source for the exported `docs/GLOSSARY.md`
  and the spec-term audit rows that link specs to glossary terms. Generic
  prose sections share `apps.kanban.BoardDoc` under `namespace="glossary"`.

The project root layout:

```
examples/fakeshop/
├── apps/
│   ├── accounts/     # schema-only session auth (login / logout / register / me)
│   ├── glossary/     # glossary terms + spec-term audit rows + GraphQL schema
│   ├── kanban/       # KANBAN.md / KANBAN.html source tables + GraphQL schema
│   ├── library/      # working DjangoType schema (acceptance)
│   ├── products/     # working connection+mutation schema + seed/admin tooling
│   └── scalars/      # scalar converter substrate + file/image upload surface
│                     # (each app carries its own tests/ package)
├── config/
│   ├── schema.py     # composes per-app Query/Mutation + DjangoOptimizerExtension
│   ├── settings.py   # single-DB default; FAKESHOP_SHARDED / FAKESHOP_PG_DSN tiers
│   ├── urls.py       # /, /graphql/, /admin/, /login/, /logout/, debug-toolbar routes
│   └── wsgi.py
├── media/            # runserver upload target (tests use a temp MEDIA_ROOT)
├── tests/            # project/config-level tests (schema export, URLs)
├── test_query/       # end-to-end /graphql/ HTTP tests
├── graphql_client.py # shared live-/graphql/ HTTP helpers for the test suites
├── schema_reload.py  # full config.schema reload helper for registry-clearing tests
├── strategy_schemas.py # shared schema builders for pg-parity tests + benchmarks
└── manage.py
```

# Setup

Fakeshop does not have its own `pyproject.toml`. It imports the
package from the repo root, so run everything from there with `uv`:

```bash
cd /path/to/django-strawberry-framework

# Install package + dev dependencies
uv sync
```

Now set up the database:

```bash
# Apply migrations (example apps + Django built-ins)
uv run python examples/fakeshop/manage.py migrate

# Create an admin user (for /admin and /login)
uv run python examples/fakeshop/manage.py createsuperuser
```

Start the server:

```bash
uv run python examples/fakeshop/manage.py runserver
```

Then open:

- <http://127.0.0.1:8000/> — landing page with dev links
- <http://127.0.0.1:8000/graphql/> — GraphiQL IDE
- <http://127.0.0.1:8000/admin/> — Django admin

Dev pages render django-debug-toolbar; the package's middleware subclass
(`django_strawberry_framework.middleware.debug_toolbar`) gives the SQL
panel visibility into `/graphql/` requests, so you can watch the
optimizer's query plans from GraphiQL.

# Sample Queries

The `library` app exposes the working schema. Try these in GraphiQL
after seeding (see below):

```graphql
{
  allLibraryBranches {
    id
    name
    city
    shelves {
      id
      code
      topic
    }
  }
}
```

```graphql
{
  allLibraryBooks {
    id
    title
    circulationStatus
    shelf {
      code
      topic
    }
    genres {
      id
      name
    }
    loans {
      id
      note
    }
  }
}
```

```graphql
{
  allLibraryPatrons {
    id
    name
    card {
      barcode
    }
    loans {
      id
      note
      book {
        title
      }
    }
  }
}
```

Filtering and ordering compose on any root list (`filter:` narrows the
rows, `orderBy:` arranges them):

```graphql
{
  allLibraryBooks(
    filter: {
      circulationStatus: {
        exact: available
      }
    }
    orderBy: [
      {
        title: ASC
      }
    ]
  ) {
    title
    circulationStatus
  }
}
```

The `products` app exposes a working catalog schema; every root field
(`allCategories` / `allItems` / `allProperties` / `allEntries`) is a
Relay connection taking the same `filter:` and `orderBy:` arguments:

```graphql
{
  allItems(
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

Products also carries the package's write surface — the model-driven,
form-backed, and DRF-serializer-backed mutation flavors all share the
same `errors` envelope:

```graphql
mutation {
  createItem(
    data: {
      name: "Widget"
      categoryId: "<GlobalID: base64 of products.category:<pk>>"
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

The `accounts` app exposes the session-auth surface. After
`create_users` (see below), log in as a test user and read the session
actor back:

```graphql
mutation {
  login(
    username: "staff_1"
    password: "<printed by create_users>"
  ) {
    node {
      username
      email
    }
    errors {
      field
      messages
    }
  }
}
```

```graphql
{
  me {
    username
    email
  }
}
```

The `glossary` app exposes the term database that exports
`docs/GLOSSARY.md`:

```graphql
{
  allGlossaryTerms(
    filter: {
      anchor: {
        exact: "filterset"
      }
    }
  ) {
    title
    statusText
    specMentions {
      specName
    }
  }
}
```

To regenerate the exported markdown from glossary DB rows:

```bash
uv run python scripts/build_glossary_md.py
```

# Generate Dummy Data

The `seed_data` command discovers Faker providers at runtime and
populates `Category`, `Property`, `Item`, and `Entry` rows in the
`products` app. It is idempotent — it only creates the shortfall to
reach the requested count per provider.

```bash
# 5 items per Faker provider (default)
uv run python examples/fakeshop/manage.py seed_data

# 50 items per provider
uv run python examples/fakeshop/manage.py seed_data 50
```

You can also seed through `/admin` via the index page's quick links:

- <http://127.0.0.1:8000/admin/products/item/?seed_data=5>
- <http://127.0.0.1:8000/admin/products/item/?seed_data=50>

# Delete Data

The `delete_data` command removes products data:

```bash
# Delete the first 10 items (cascading entries)
uv run python examples/fakeshop/manage.py delete_data 10

# Delete every item and entry
uv run python examples/fakeshop/manage.py delete_data all

# Wipe Category / Property / Item / Entry tables
uv run python examples/fakeshop/manage.py delete_data everything
```

Or through `/admin`:

- <http://127.0.0.1:8000/admin/products/item/?delete_data=10>
- <http://127.0.0.1:8000/admin/products/item/?delete_data=all>
- <http://127.0.0.1:8000/admin/products/item/?delete_data=everything>

# Test Users

The `create_users` command creates a set of test users for exercising
permission branches. Each set creates 6 users:

- `staff_N` — `is_staff=True`
- `regular_N` — no permissions
- `view_category_N` — has `products.view_category`
- `view_item_N` — has `products.view_item`
- `view_property_N` — has `products.view_property`
- `view_entry_N` — has `products.view_entry`

All share the password printed by the command.

```bash
# 1 set (default)
uv run python examples/fakeshop/manage.py create_users

# 3 sets
uv run python examples/fakeshop/manage.py create_users 3

# Delete the first 5 non-superusers
uv run python examples/fakeshop/manage.py delete_users 5

# Delete every non-superuser
uv run python examples/fakeshop/manage.py delete_users all
```

Via `/admin`:

- <http://127.0.0.1:8000/admin/auth/user/?create_users=1>
- <http://127.0.0.1:8000/admin/auth/user/?delete_users=all>

# Sharded Mode (Optional)

Fakeshop ships an optional multi-DB layout for exercising the
package against querysets bound to non-default aliases. The layout
is **additive**: `default` keeps pointing at `db.sqlite3` in both
single-DB and sharded modes, and `FAKESHOP_SHARDED=1` ADDS
`shard_b → db_shard_b.sqlite3` on top of the existing layout. The
committed `db_shard_b.sqlite3` fixture ships with `seed_shards`
already applied so the sharded mode works out of the box:

```bash
# Populate the secondary shard with migrations + canonical test
# users + at least one Item per Faker provider
FAKESHOP_SHARDED=1 uv run python examples/fakeshop/manage.py seed_shards

# Run the server against the shards (default = db.sqlite3, shard_b
# = db_shard_b.sqlite3)
FAKESHOP_SHARDED=1 uv run python examples/fakeshop/manage.py runserver
```

# Postgres Tier (Optional)

`FAKESHOP_PG_DSN` swaps the `default` alias to a real Postgres server —
the vendor tier the optimizer's LATERAL-join fetch strategy (and any
other `connection.vendor`-sensitive behavior) is verified on. Mutually
exclusive with `FAKESHOP_SHARDED`. Requires the `pg` dependency group
(`psycopg`); the default SQLite install carries no Postgres dependency:

```bash
# Install psycopg
uv sync --group pg

# Start a local Postgres
docker compose -f docker-compose.postgres.yml up -d

# Run the full suite against it
FAKESHOP_PG_DSN=postgres://fakeshop:fakeshop@127.0.0.1:5432/fakeshop uv run pytest
```

CI runs the same tier via the `test-postgres` job's GitHub Actions
service container.

# Testing

Three test tiers live alongside the example project:

```bash
# Per-app in-process tests: models, admin, services, management
# commands, in-process schema via schema.execute_sync (no HTTP)
uv run pytest examples/fakeshop/apps

# Project/config-level tests: schema export, type inspection, URLs
uv run pytest examples/fakeshop/tests

# Live API tests: real /graphql/ HTTP requests through the full
# Django + Strawberry stack
uv run pytest examples/fakeshop/test_query

# Everything
uv run pytest examples/fakeshop

# Sharded variant
FAKESHOP_SHARDED=1 uv run pytest examples/fakeshop
```

Each app carries its own `tests/` package (namespaced
`apps.<app>.tests`), so deleting an app loses only that app's tests.
See [`test_query/README.md`][readme] for the live-API
test conventions and the schema-reload fixture pattern used to keep
package-level and example-level registries isolated.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->
[readme]: test_query/README.md

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
