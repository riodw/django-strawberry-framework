# Build plan: spec-041 Channels ASGI router (`0.0.14`)

Input contract: `docs/spec-041-channels_router-0_0_14.md`. Two slices per the
spec's slice checklist: Slice 1 (dependency gate + `routers.py` +
`tests/test_routers.py` + the `request_from_info()` Channels branch), Slice 2
(docs + card wrap; no version bump - the joint `0.0.14` cut owns it).

## Slice 1 - dependency gate record

- `channels[daphne]>=4.3.2` added to `[dependency-groups].dev` in
  `pyproject.toml`; `uv.lock` regenerated in the same commit (`uv lock`).
  Resolved: `channels 4.3.2`, `daphne 4.2.2`.
- **Strawberry-floor gate** (spec DoD item): in an isolated throwaway venv
  (never the shared `.venv`):

  ```
  uv venv "$SCRATCH/floorenv" --python 3.12
  uv pip install --python "$SCRATCH/floorenv/bin/python" \
      'strawberry-graphql==0.262.0' 'channels>=4.3.2' 'django>=5.2'
  "$SCRATCH/floorenv/bin/python" -c \
      "from strawberry.channels import GraphQLHTTPConsumer, GraphQLWSConsumer"
  ```

  Outcome: **PASS** - both consumers import at `strawberry-graphql==0.262.0`
  with `channels 4.3.2`; no Strawberry floor bump needed.

## Slice 1 - file delta (per the spec's Implementation plan table)

- `pyproject.toml` + `uv.lock` - the dependency gate (above).
- `django_strawberry_framework/utils/imports.py` -
  `require_optional_module(module_name, *, install_hint)` + unit tests.
- `django_strawberry_framework/routers.py` - guard / builder / PEP 562
  `__getattr__` / `DjangoGraphQLProtocolRouter` (Decisions 3, 5, 6, 7).
- `django_strawberry_framework/utils/permissions.py` - Channels context
  branch + wrapping adapter (Decision 11).
- `tests/test_routers.py`, `tests/utils/test_imports.py`,
  `tests/utils/test_permissions.py` - Tests 1-18 per the spec Test plan.
- `tests/utils/test_inputs.py` - one rider test closing a pre-existing
  coverage gap the Slice-1 full-sweep gate surfaced: `_safe_import`'s
  attr-lenient `except AttributeError` branch (`utils/inputs.py`, left
  untested by the Revision-6 `utils/` DRY refactor) had no covering test;
  without it the `fail_under = 100` gate fails at 99.97%.

## Slice 1 - gate results

- Full parallel sweep: `uv run pytest` - **2846 passed, 4 skipped, 4 xfailed;
  coverage 100.00%** (`fail_under = 100` holds with `routers.py` included).
- `uv run ruff format .` / `uv run ruff check --fix .` clean;
  `uvx pre-commit run --all-files` clean (ASCII-only + trailing commas).
- Build note: the communicator tests carry `django_db` marks - Channels'
  consumer dispatch runs `aclose_old_connections()` outside the windows
  `channels.testing` no-op-patches, and under pytest-django's blocker an
  unmarked test trips `Database access not allowed` whenever another test's
  executor-thread connection lingers (in-memory sqlite `close()` is a no-op).
  Test 18 (authenticated session) landed on the preferred path - no
  weakened-wording fallback needed.

## Slice 2 - docs + card wrap

- GLOSSARY router entry body to the implemented contract (status stays
  `planned for 0.0.14`); Auth-mutations deferral sentence re-worded.
- `docs/TREE.md` regenerated via `scripts/build_tree_md.py`.
- Kanban card `WIP-ALPHA-041-0.0.14` -> `DONE-041-0.0.14` via DB edit +
  re-render.

## Migration-guide handoff row (for `TODO-BETA-056-0.1.6`)

`strawberry_django.routers.AuthGraphQLProtocolTypeRouter` ->
`django_strawberry_framework.routers.DjangoGraphQLProtocolRouter`
(constructor signature unchanged:
`(schema, django_application=None, url_pattern="^graphql")`).
