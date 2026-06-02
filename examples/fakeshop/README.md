# Fakeshop Example Django Project

A Django + Strawberry GraphQL example project that exercises
`django-strawberry-framework` end-to-end. It ships several app surfaces:

- **`apps.library`** — acceptance app with a real `DjangoType` schema
  (FK, reverse FK, OneToOne, M2M, Relay `Node`, optimizer hints,
  consumer relation overrides). This is the working slice.
- **`apps.products`** — placeholder schema (the `DjangoType` /
  `DjangoConnectionField` declarations are intentionally commented
  out). The app still ships migrations, models, admin, services, and
  management commands so the seed / delete / user flows work.
- **`apps.scalars`** — converter-table substrate for scalar wire formats.
- **`apps.kanban`** — relational source for the exported root `KANBAN.md`.
- **`apps.glossary`** — relational source for the exported `docs/GLOSSARY.md`
  and the spec-term audit rows that link specs to glossary terms. Generic
  prose sections share `apps.kanban.BoardDoc` under `namespace="glossary"`.

The project root layout:

```
examples/fakeshop/
├── apps/
│   ├── glossary/     # glossary terms + spec-term audit rows + GraphQL schema
│   ├── kanban/       # KANBAN.md source tables + GraphQL schema
│   ├── library/      # working DjangoType schema (acceptance)
│   ├── products/     # placeholder schema + seed/admin tooling
│   └── scalars/      # scalar converter substrate
├── config/
│   ├── schema.py     # composes per-app Query + DjangoOptimizerExtension
│   ├── settings.py
│   └── urls.py       # /, /graphql/, /admin/, /login/, /logout/
├── tests/            # in-process schema/service/admin/url tests
├── test_query/       # end-to-end /graphql/ HTTP tests
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
    shelf { code topic }
    genres { id name }
    loans { id note }
  }
}
```

```graphql
{
  allLibraryPatrons {
    id
    name
    card { barcode }
    loans { id note book { title } }
  }
}
```

The `products` app currently only exposes a placeholder field:

```graphql
{ hello }   # → "fakeshop placeholder"
```

The `glossary` app exposes the term database that exports
`docs/GLOSSARY.md`:

```graphql
{
  allGlossaryTerms(filter: { anchor: { exact: "filterset" } }) {
    title
    statusText
    specMentions { specName }
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

# Testing

Two test suites live alongside the example project:

```bash
# In-process tests: schemas, services, models, admin, management
# commands, URLs (no HTTP)
uv run pytest examples/fakeshop/tests

# Live API tests: real /graphql/ HTTP requests through the full
# Django + Strawberry stack
uv run pytest examples/fakeshop/test_query

# Both
uv run pytest examples/fakeshop

# Sharded variant
FAKESHOP_SHARDED=1 uv run pytest examples/fakeshop
```

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
