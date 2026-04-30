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

A DRF-inspired Django integration framework for [Strawberry GraphQL](https://github.com/strawberry-graphql/strawberry) — `Meta`-class-driven type generation and N+1 optimization today, with filtering, ordering, aggregation, and permissions on the roadmap.

> **Status: pre-alpha.** The shipped surface is `DjangoType` (model-to-type generation with scalar, relation, and choice-enum conversion) and the N+1 optimizer (cardinality-aware relation resolvers, selection-tree walker, root-gated resolve hook with async parity). The full Layer-3 surface (FilterSet, OrderSet, AggregateSet, permissions, connection fields) is designed but not yet implemented. The public API is not stable and is expected to change rapidly until `0.1.0`. See [`docs/README.md`](docs/README.md) for the package's goals and positioning vs. `graphene-django` and `strawberry-graphql-django`.

#### This package takes inspiration from:

- <https://github.com/riodw/django-graphene-filters>
- <https://github.com/encode/django-rest-framework>
- <https://github.com/strawberry-graphql/strawberry-graphql-django>

## Installation

```shell
# pip
pip install django-strawberry-framework
# uv
uv add django-strawberry-framework
```

## Development Setup

```shell
# Install uv (if not already installed)
# https://docs.astral.sh/uv/getting-started/installation/

# Clone and install
git clone https://github.com/riodw/django-strawberry-framework.git
cd django-strawberry-framework
uv sync
uv sync --upgrade
```

## Running

```shell
# Apply migrations to the example app
uv run python examples/fakeshop/manage.py migrate

# Start the dev server (admin + GraphiQL at /graphql/)
uv run python examples/fakeshop/manage.py runserver
```

The dev landing page at `/` links to GraphiQL, the admin, and the seed/delete query-param triggers.

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

The same actions are also reachable from the admin via query-param triggers — see the dev landing page at `/` for clickable links.

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

The example ships with a two-DB layout for stress-testing multi-database scenarios. Toggle it via `FAKESHOP_SHARDED=1`:

```shell
# Materialize both shard SQLite files (idempotent)
FAKESHOP_SHARDED=1 uv run python examples/fakeshop/manage.py seed_shards

# Larger seed for stress testing
FAKESHOP_SHARDED=1 uv run python examples/fakeshop/manage.py seed_shards --count 5000
```

In sharded mode `default` → `db_shard_a.sqlite3` and `shard_b` → `db_shard_b.sqlite3`. The single-DB `db.sqlite3` is invisible while the env var is set.

## Testing

```shell
# Run the full test suite (coverage runs automatically; build fails below 100%)
uv run pytest

# Run a single test file
uv run pytest tests/base/test_conf.py
```

CI runs the suite across a Python × Django matrix on every push and PR. The full matrix is also available via `workflow_dispatch`. See [`.github/workflows/django.yml`](.github/workflows/django.yml).

### Formatting and Linting

```shell
# pyproject.toml [tool.ruff]
uv run ruff format .
uv run ruff check --fix .
```

### Updating Version

- `pyproject.toml`
- `django_strawberry_framework/__init__.py`

## Build

```shell
uv lock
rm -rf dist/
uv build
```

## Publish

```shell
uv publish --token PASSWORD
```

### Updating dependencies

```shell
# Show outdated packages
uv pip list --outdated

# Add a dev dependency
uv add --group dev <package>

# Remove the virtual environment
rm -rf .venv
```

### Local usage in another project

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

## Contributing & Security

- Contribution workflow: [`CONTRIBUTING.md`](CONTRIBUTING.md)
- Vulnerability reporting: [`SECURITY.md`](SECURITY.md)
- Release notes: [`CHANGELOG.md`](CHANGELOG.md)
