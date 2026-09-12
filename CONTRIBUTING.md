# Contributing

Thanks for your interest in contributing to `django-strawberry-framework`. The project is in early development and contributions of all sizes are welcome — bug reports, doc fixes, tests, feature work, design feedback.

## Where things live

- **Package layout & test placement** — [`docs/TREE.md`][tree] is the canonical layout reference: upstream tree comparisons, the current on-disk shape, the target shape with `[alpha]` / `[beta]` / `[stable]` milestone tags, and the test-placement rules across the package and example-project test trees.
- **Capability catalog** — [`docs/GLOSSARY.md`][glossary] is the source of truth for what's shipped / planned / deferred plus the `0.1.0` / `1.0.0` milestone framing.
- **Per-card sequencing** — [`KANBAN.md`][kanban] tracks all planned work as `TODO-ALPHA-*`, `TODO-BETA-*`, `BLOCKED-*`, and `DONE-*` cards with version pins.
- **Strategic differentiation roadmap** — [`BACKLOG.md`][backlog] holds post-`1.0.0` items that aren't on the milestone roadmap. Items graduate to `KANBAN.md` cards when scheduled.
- **In-flight design work** — the one spec being built lives at `docs/spec-<NNN>-<topic>-<0_0_X>.md` (NNN is the 3-digit KANBAN card number; naming and slice mechanics are in [`docs/builder/BUILD.md`][build]). When the next spec is authored, every prior spec moves to [`docs/SPECS/`][specs] and its `-terms.csv` / `-rationale.md` companions to `docs/SPECS/appx/`, so `docs/SPECS/` is the archive and `docs/` holds exactly one spec at a time.
- **Tutorial through the example project** — [`examples/fakeshop/README.md`][fakeshop-readme] walks the shipped surface end to end with live queries; it is the seed of the full documentation.
- **Current example-project capability snapshot** — [`TODAY.md`][today] shows what the package can do in the fakeshop `products` app right now.
- **Long-term destination** — [`GOAL.md`][goal] describes the rich-schema north star the milestone roadmap is heading toward.
- **Agent handbooks** — [`AGENTS.md`][agents] and [`START.md`][start] are the rules and terrain for AI agents working on this checkout. They are dense by design and not the place to start as a human contributor, but they are binding on any agent you point at the repo.

## Getting started

This project uses [`uv`](https://docs.astral.sh/uv/) for dependency and environment management.

```bash
git clone https://github.com/riodw/django-strawberry-framework.git
cd django-strawberry-framework
uv sync
uvx pre-commit install
```

`uv sync` installs the `dev` group. `uv sync --group pg` adds `psycopg` for the Postgres tier below. Never `pip install` into `.venv`; go through `uv`.

## Running the test suite

```bash
uv run pytest
```

Coverage runs automatically and the build will fail if total coverage of `django_strawberry_framework` drops below 100%. Example apps and tests run but never count toward the gate. Warnings are errors.

The default invocation is parallel (`-n auto --dist loadscope`). For one test:

```bash
uv run pytest -n0 tests/test_connection.py::test_name
```

Four test trees run under one `pytest.ini`:

| Tree | Tests | Style |
|---|---|---|
| `tests/` | the package itself | in-process; fakeshop models are fine as fixtures |
| `examples/fakeshop/test_query/` | any package line reachable by a real query | live `/graphql/` HTTP through Django's test client; the first place to add a test |
| `examples/fakeshop/apps/<app>/tests/` | one app's models, admin, services, commands | in-process `schema.execute_sync`; each app owns its package |
| `examples/fakeshop/tests/` | project and config only (URLs, settings guard, schema export) | not a package |

Anything a real GraphQL query can reach must be covered from `test_query/`, with the other trees as fallback for lines a query cannot reach. [`examples/fakeshop/test_query/README.md`][test-query-readme] documents the isolation contract between the trees and the schema-reload fixture. `apps.accounts` is schema-only and has no `tests/` package; its coverage lives in the live tier.

Two environment knobs, mutually exclusive, un-skip their tiers:

```bash
# Two SQLite aliases: default + shard_b (db_shard_b.sqlite3)
FAKESHOP_SHARDED=1 uv run pytest

# Postgres as the default alias; needs the pg group and a local server
uv sync --group pg
docker compose -f docker-compose.postgres.yml up -d
FAKESHOP_PG_DSN=postgres://fakeshop:fakeshop@127.0.0.1:5432/fakeshop uv run --group pg pytest
```

CI runs the SQLite tiers on every push and pull request, at the exact dependency floor and at latest. The Postgres workflow is manual dispatch.

## Linting, formatting, and pre-commit

```bash
uv run ruff check --fix .
uv run ruff format .
uvx pre-commit run --files <paths you changed>
```

The hooks in `.pre-commit-config.yaml` check things ruff does not, and CI runs the same checks:

- **kanban-tracked-path-constants** regenerates `examples/fakeshop/apps/kanban/constants.py` from git's tracked file set. Adding or deleting a tracked package or test file means committing the regenerated constants with it; the hook only sees a new file once it is staged.
- **source-layout** enforces trailing-comma explosion at four or more elements (two in any `models.py`), ASCII-only `.py` source, the markdown link-definition scaffold described below, and brace explosion inside JSON and GraphQL blocks. It auto-fixes, then fails the run so you re-stage.
- **ruff-format** and **ruff-check**.
- **check-kanban-anchors** and **check-citations**. Every `path::Symbol` reference in first-party source and on the board must resolve, so a rename means sweeping `::OldName` in the same change. Cite by symbol, never by line number.

## The example project and the rendered docs

`examples/fakeshop/` is a development fixture and the host of two docs-as-data apps. Its settings refuse to load with `DEBUG` off. It never deploys.

`examples/fakeshop/db.sqlite3` is tracked. It carries the seeded catalog rows and the source tables for [`KANBAN.md`][kanban] and [`docs/GLOSSARY.md`][glossary]. Do not reset or regenerate it casually; a board or glossary edit is a database edit.

Three files are rendered, and CI fails if a hand edit makes them disagree with their generator. Edit the source, then re-render:

| Rendered file | Source | Renderer |
|---|---|---|
| `KANBAN.md`, `KANBAN.html` | fakeshop `kanban` app tables | `uv run python scripts/build_kanban_md.py`, `scripts/build_kanban_html.py` |
| `docs/GLOSSARY.md` | fakeshop `glossary` app tables | `uv run python scripts/build_glossary_md.py` |
| `docs/TREE.md` | package module docstrings plus board rows | `uv run python scripts/build_tree_md.py` |

Every module in the package needs a docstring; `build_tree_md.py` fails without one.

## Markdown links

Every `.md` file with cross-file links uses reference style: `[text][ref-id]` in the body, and all definitions in one `<!-- LINK DEFINITIONS -->` block at the bottom, grouped under ten fixed headers by where the target lives (`Root`, `docs/`, `docs/SPECS/`, `docs/builder/`, `django_strawberry_framework/`, `tests/`, `examples/`, `scripts/`, `.venv/`, `External`), alphabetical within a group. The `source-layout` hook enforces the scaffold and appends missing headers. URLs, in-page anchors, and anything inside a fenced block stay inline. `AGENTS.md` and `CLAUDE.md` are exempt.

## Updating the package version

The version is single-sourced: `__version__` in `django_strawberry_framework/__init__.py`. `pyproject.toml` declares `version` as dynamic and hatchling reads it from there, so a release bump touches that one literal. `tests/base/test_init.py` pins the expected string, so update the test in the same change.

## Building

```bash
uv lock
rm -rf dist/
uv build
```

## Publishing

```bash
uv publish --token PASSWORD
```

## Updating dependencies

```bash
# Show outdated packages
uv pip list --outdated

# Add a dev dependency
uv add --group dev <package>

# Remove the virtual environment
rm -rf .venv
```

Dependabot rewrites `uv.lock` and action SHAs weekly. Soft dependencies (`cryptography`, `channels`, `django-debug-toolbar`, `djangorestframework`) never join `[project].dependencies`; tests cover both their presence and their absence.

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/) where reasonable, e.g.:

```
feat: add DjangoType base class
fix: handle empty user_settings dict
docs: clarify filter Meta options
```

## Pull requests

1. Fork the repository and create your branch from `main`.
2. Add tests that cover any new behavior — coverage must remain at 100%. Prefer a live test in `examples/fakeshop/test_query/` when a real query can reach the line.
3. Run `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, and `uvx pre-commit run --files <your paths>` locally.
4. If you touched a rendered doc's source, re-render it and commit the result.
5. Open a pull request against `main` with a clear description of the change and the motivation behind it.

## Reporting issues

Please open issues at <https://github.com/riodw/django-strawberry-framework/issues> with as much context as possible — Python version, Django version, a minimal reproducer if available. Security reports follow [`SECURITY.md`][security].

## Code of conduct

Be respectful, assume good intent, and focus discussion on the work. Harassment or hostile behavior will not be tolerated.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: AGENTS.md
[backlog]: BACKLOG.md
[goal]: GOAL.md
[kanban]: KANBAN.md
[security]: SECURITY.md
[start]: START.md
[today]: TODAY.md

<!-- docs/ -->
[glossary]: docs/GLOSSARY.md
[tree]: docs/TREE.md

<!-- docs/SPECS/ -->
[specs]: docs/SPECS/

<!-- docs/builder/ -->
[build]: docs/builder/BUILD.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->
[fakeshop-readme]: examples/fakeshop/README.md
[test-query-readme]: examples/fakeshop/test_query/README.md

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
