START.md README.md GOAL.md docs/README.md docs/TREE.md docs/GLOSSARY.md KANBAN.md TODAY.md CHANGELOG.md BACKLOG.md
strawberry_django `~/projects/strawberry-django-main/strawberry_django` graphene_django `~/projects/django-graphene-filters/.venv/lib/python*/site-packages/graphene_django`
DRF first, strawberry second: every public surface uses Meta classes (never stacked Strawberry decorators on consumer-facing classes — that is strawberry-graphql-django's API and the explicit reason this package exists), and crib from django-graphene-filters and DRF idioms rather than from strawberry-graphql-django's decorator API
Package source lives in django_strawberry_framework/; example project in examples/fakeshop/ with pythonpath = examples/fakeshop
Test placement: three test trees with no overlap — tests/ (package tests, system-under-test is django_strawberry_framework itself, may use real example-project models as fixtures), examples/fakeshop/tests/ (example-project tests not hitting /graphql HTTP), examples/fakeshop/test_query/ (live GraphQL-API tests pinging /graphql over HTTP via django.test.Client); tests/base/ holds exactly test_init.py and test_conf.py (both may grow, no new files added); do not add __init__.py under examples/fakeshop/tests/ or examples/fakeshop/test_query/ (collides on the tests package name once examples/fakeshop is on pythonpath); examples/fakeshop/apps/products/tests/ stays empty as the per-Django-app convention placeholder
First line of every catalog/auth test: seed_data(N) or create_users(N) from apps.products.services; never hand-roll Category/Item/Property/Entry/User (seed-helper tests are the only exception)
Library acceptance tests use inline Model.objects.create; the library app has no services.py
Test through real usage and prefer the example project: any coverage line achievable via a real GraphQL query against fakeshop in examples/fakeshop/test_query/ MUST be earned that way (live /graphql HTTP via django.test.Client); fall back to examples/fakeshop/tests/ (in-process schema.execute_sync, admin, services, management commands via call_command, URLs via Client, models via Model.objects.create) or tests/ (package-internal) only when the line is genuinely unreachable from a real-world query; mock only when the real path is impossible (mock behaviour, not the class)
Coverage source is django_strawberry_framework only; example apps and example tests run end-to-end but stay outside the fail_under gate
fail_under = 100 in pyproject.toml [tool.coverage.report]; CI gates every push and PR
pragma no cover is only for branches genuinely unreachable under the test runner
Add tests in the same change as code; sweep all three test trees for orphan imports when removing code
Do not run pytest after edits; run only when explicitly asked
Run uv run ruff format . and uv run ruff check --fix . after every edit
Line length 110
COM812 enabled: trailing comma on multi-arg calls expands the layout and locks it in; do not remove
ERA001 enabled but TODO-anchored Pseudo blocks are exempt; suppress inline with noqa ERA001 if needed; do not refactor pseudo code to satisfy the lint
django_strawberry_framework.conf.settings reads DJANGO_STRAWBERRY_FRAMEWORK from the consumer's settings dict; missing keys raise AttributeError
Add settings keys only when the feature that needs them lands; do not preemptively populate
Do not update CHANGELOG.md unless explicitly instructed
Do not bulk-delete or bulk-overwrite under docs/review/; rev-*.md, REVIEW.md, review-*.md, worker-*.md are committed source of truth; restore via git checkout HEAD -- docs/review/ if anything goes missing
docs/shadow/ is regenerable; scripts/bug_hunt.py and scripts/review_current_from_commit.py wipe the entire docs/shadow/ tree before refreshing
Generated docs/bug_hunt/bug_hunt.*.md files are regenerable; docs/bug_hunt/dicta.md is maintainer-edited and stays
When clearing tool output, target the specific subdirectory; never recursively delete from docs/review/ itself
Design docs and TODO anchors: new in-flight design docs go in docs/ as spec-<NNN>-<topic>-<0_0_X>.md (NNN matches the KANBAN card number; see docs/builder/BUILD.md for the full pattern), completed design docs stay at their working location with shipped behavior folded into docs/GLOSSARY.md / docs/TREE.md / KANBAN.md (no archival default), and staged-but-not-implemented slices get a source-site TODO comment naming the active design doc and slice (paired with NotImplementedError if the call path must fail loudly), removed in the same change that ships the slice
FAKESHOP_SHARDED=1 swaps DATABASES to db_shard_a.sqlite3 (default) and db_shard_b.sqlite3 (shard_b); modes are mutually exclusive; seed_shards materializes both shards idempotently
Sharded-specific tests live behind FAKESHOP_SHARDED and do not run under the default pytest invocation
Bump pyproject.toml [project].version and django_strawberry_framework/__init__.py __version__ together; both must match
Only the maintainer commits; do not auto-commit unless explicitly asked
