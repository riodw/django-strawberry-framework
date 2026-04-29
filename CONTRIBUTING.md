# Contributing

Thanks for your interest in contributing to `django-strawberry-framework`. The project is in early development and contributions of all sizes are welcome — bug reports, doc fixes, tests, feature work, design feedback.

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
uv run ruff check .
uv run ruff format .
```

CI runs both checks; please run them locally before pushing.

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
