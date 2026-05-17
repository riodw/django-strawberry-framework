# Contributing

Thanks for your interest in contributing to `django-strawberry-framework`. The project is in early development and contributions of all sizes are welcome — bug reports, doc fixes, tests, feature work, design feedback.

## Where things live

- **Package layout & test placement** — [`docs/TREE.md`](docs/TREE.md) is the canonical layout reference: upstream tree comparisons, the current on-disk shape, the target shape with `[alpha]` / `[beta]` / `[stable]` milestone tags, and the test-placement rules across the package and example-project test trees.
- **Capability catalog** — [`docs/FEATURES.md`](docs/FEATURES.md) is the source of truth for what's shipped / planned / deferred plus the `0.1.0` / `1.0.0` milestone framing.
- **Per-card sequencing** — [`KANBAN.md`](KANBAN.md) tracks all planned work as `TODO-ALPHA-*`, `TODO-BETA-*`, `BLOCKED-*`, and `DONE-*` cards with version pins.
- **Strategic differentiation roadmap** — [`BETTER.md`](BETTER.md) holds post-`1.0.0` items that aren't on the milestone roadmap. Items graduate to `KANBAN.md` cards when scheduled.
- **In-flight design work** — new features use the `docs/spec-<NNN>-<topic>-<0_0_X>.md` convention (NNN is the 3-digit KANBAN card number, e.g. `docs/spec-013-deferred_scalars-0_0_6.md`; see `docs/builder/BUILD.md` "Spec filename pattern"). Once a slice ships, its behavior is folded into `docs/FEATURES.md` or `docs/TREE.md` and the spec stays at its working location as the historical record.
- **Current example-project capability snapshot** — [`TODAY.md`](TODAY.md) shows what the package can do in the fakeshop example right now.
- **Long-term destination** — [`GOAL.md`](GOAL.md) describes the rich-schema north star the milestone roadmap is heading toward.

## Getting started

This project uses [`uv`](https://docs.astral.sh/uv/) for dependency and environment management.

```bash
git clone https://github.com/riodw/django-strawberry-framework.git
cd django-strawberry-framework
uv sync
```

## Running the test suite

```bash
uv run pytest
```

Coverage runs automatically and the build will fail if total coverage drops below 100%.

## Linting and formatting

```bash
uv run ruff check --fix .
uv run ruff format .
```

CI runs both checks; please run them locally before pushing.

## Updating the package version

Bump the version in both places before tagging a release:

- `pyproject.toml`
- `django_strawberry_framework/__init__.py`

`tests/base/test_init.py` pins the expected version against `pyproject.toml`, so a missed bump fails the test suite loudly.

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

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/) where reasonable, e.g.:

```
feat: add DjangoType base class
fix: handle empty user_settings dict
docs: clarify filter Meta options
```

## Pull requests

1. Fork the repository and create your branch from `main`.
2. Add tests that cover any new behavior — coverage must remain at 100%.
3. Run `uv run pytest`, `uv run ruff check .`, and `uv run ruff format --check .` locally.
4. Open a pull request against `main` with a clear description of the change and the motivation behind it.

## Reporting issues

Please open issues at <https://github.com/riodw/django-strawberry-framework/issues> with as much context as possible — Python version, Django version, a minimal reproducer if available.

## Code of conduct

Be respectful, assume good intent, and focus discussion on the work. Harassment or hostile behavior will not be tolerated.
