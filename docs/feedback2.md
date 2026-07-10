# Spec 043 Follow-up Implementation Review

Verdict: the implementation is much closer. I did not find a runtime blocker in
the `TestClient`/`AsyncTestClient` code or in the ordinary live-suite switchover:
the package client owns the body/decode path, malformed/raw-envelope cases remain
raw with comments, and the package-tier test file is now DB-free. The remaining
issues are closeout consistency problems that matter because this repository
treats the spec, build artifact, generated Kanban export, and [`AGENTS.md`][agents]
rules as part of the release contract.

## Findings

### P2 - The card is marked Done while the controlling spec and build artifact still say it is unbuilt

[`KANBAN.md`][kanban] now exports card 043 as `DONE-043-0.0.14` with all DoD
items checked, but [`docs/spec-043-test_client-0_0_14.md`][spec-043] still opens
with `WIP-ALPHA-043-0.0.14`, says `Status: **PLANNED -- no slice built yet.**`,
and leaves Slice 1, Slice 2, Slice 3, and the Definition of done boxes
unchecked. The build record still says, in
[`docs/builder/build-043-test_client-0_0_14.md`][build-043], `This build ran
Slice 1 only.`

That creates a release-evidence split: a reviewer following the Done card sees
completion, while the spec/build trail still says the broad live-suite
switchover and docs/card wrap did not happen. This is not just cosmetic in this
repo; [`AGENTS.md`][agents] makes design docs, generated TREE/GLOSSARY/KANBAN
state, and card-close discipline part of the work product.

Root fix: update the spec status/checklists and append or rewrite the build
artifact so they reflect the actual final state: Slice 2 live-suite switchover
landed, Slice 3 docs/card wrap landed, version bump/status flips remain deferred
to the joint `0.0.14` cut. Keep the GLOSSARY term statuses as `planned for
0.0.14` in [`docs/GLOSSARY.md`][glossary] until that joint cut; the problem is
the spec/build saying "not built," not the release-status wording.

### P2 - The Done card marks the current package file as historical

The Done card's Package files section lists
`django_strawberry_framework/testing/client.py` as `historical` in
[`KANBAN.md`][kanban], but the file exists and is the main package surface for
this card. [`docs/TREE.md`][tree] correctly shows it in the current package tree,
so the generated Kanban evidence disagrees with the generated tree.

This usually means the DB-backed `TrackedPath` row for the card is still flagged
non-current from the WIP/planned phase. Since `KANBAN.md`/`KANBAN.html` are
generated exports, the fix should be in the kanban DB source row, followed by
regenerating both exports, not a hand edit to the rendered markdown.

Root fix: mark the card's tracked path for
`django_strawberry_framework/testing/client.py` as current in
`examples/fakeshop/db.sqlite3`, regenerate `KANBAN.md` with
[`scripts/build_kanban_md.py`][build-kanban-md] and the matching HTML export,
and verify the Done card no longer says the live package file is historical.

### P3 - The new class-based live tests still do extra schema reload work before seeding

The function-style fixes now satisfy the products seed-helper rule: the products
`TestClient` login test and the async writer fixture start with `create_users(1)`
or `seed_data(1)`. The new class-based tests in
[`examples/fakeshop/test_query/test_client_api.py`][test-client-api] still call
`reload_all_project_schemas()` inside each `setUp()` before `seed_data(1)`, even
though the file already has the standard autouse
`_reload_project_schema_for_acceptance_tests` fixture.

This is lower severity because the data is still seeded by the approved helper
and no models are hand-rolled. But `AGENTS.md` is deliberately strict about the
first line of catalog/auth setup, and the duplicate reload makes these tests
harder to audit against that rule.

Root fix: rely on the autouse reload fixture for schema freshness, remove the
manual `reload_all_project_schemas()` calls from the class `setUp()` methods,
and leave `seed_data(1)` as the first domain setup step after `super().setUp()`.

## What Looks Solid

- Ordinary live GraphQL helper calls now flow through
  [`examples/fakeshop/graphql_client.py`][graphql-client] and the package
  [`TestClient`][client], while raw POSTs are limited to the documented
  malformed/raw envelope cases.
- [`tests/testing/test_client.py`][test-client-tests] is now DB-free and owns
  mechanics that are not naturally live HTTP behavior.
- The multipart file placeholder walker now fails malformed `files=` paths at
  the source instead of emitting invalid envelopes.
- I found no new root export, dependency, version bump, or `CHANGELOG.md` drift.

## Verification

I reviewed the staged implementation diff and the unstaged Kanban script changes,
including `testing/client.py`, the shared fakeshop GraphQL helper, the converted
live acceptance files, the new `test_client_api.py`, `tests/testing/test_client.py`,
`KANBAN.md`, `docs/GLOSSARY.md`, `docs/TREE.md`, the spec, and the build record.
I did not run pytest, per the repository instruction.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[kanban]: ../KANBAN.md

<!-- docs/ -->
[glossary]: GLOSSARY.md
[spec-043]: spec-043-test_client-0_0_14.md
[tree]: TREE.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[build-043]: builder/build-043-test_client-0_0_14.md

<!-- django_strawberry_framework/ -->
[client]: ../django_strawberry_framework/testing/client.py

<!-- tests/ -->
[test-client-tests]: ../tests/testing/test_client.py

<!-- examples/ -->
[graphql-client]: ../examples/fakeshop/graphql_client.py
[test-client-api]: ../examples/fakeshop/test_query/test_client_api.py

<!-- scripts/ -->
[build-kanban-md]: ../scripts/build_kanban_md.py

<!-- .venv/ -->

<!-- External -->
