# Spec 043 Follow-up Review

Verdict: the previous blockers are mostly fixed. The spec now owns sync/async
`query()`, gives `url=` a non-mutating transport path, collapses the terms CSV
to one row per anchor, and makes Test 8 prove target selection without relying
on a `/percall/` 404. One blocker remains: the test-placement and slice plan
still conflicts with the repo's live-first coverage rule and the 100% coverage
gate.

## Findings

### P1 - The test plan still puts live-reachable request coverage in `tests/`, and the slice split makes that hard to fix

Decision 11 says the live switchover is primary coverage, but the test plan
then assigns real fakeshop `/graphql/` request cases to
`tests/testing/test_client.py`: happy path, GraphQL errors, operation-name
dispatch, login, multipart upload, async request paths, and TestCase-family
end-to-end requests. The repo rule is stricter: any coverage line achievable by
a live fakeshop GraphQL request belongs in `examples/fakeshop/test_query/`;
`tests/` is only the fallback when the line is genuinely unreachable from a
real-world query.

References:

- [spec-043][spec-043] #"Decision 11 -- Test strategy: the live switchover is the primary coverage"
- [spec-043][spec-043] #"tests/testing/test_client.py` (the card's DoD row) then owns only what the switched suites cannot pin"
- [spec-043][spec-043] #"The sync client -- request shapes (real fakeshop `/graphql/` requests)"
- [agents][agents] #"any coverage line achievable via a real GraphQL query against fakeshop in examples/fakeshop/test_query/ MUST be earned that way"
- [agents][agents] #"Add tests in the same change as code"
- [pyproject][pyproject] #"fail_under = 100"

This is also a slice-order problem. Slice 1 adds `testing/client.py`, which is
package code under a 100% coverage gate, while Slice 2 does the live-suite
switchover that the spec says is the primary coverage. If Slice 1 covers those
branches in `tests/testing/test_client.py`, it violates the live-first rule. If
Slice 1 waits for Slice 2 to cover them, Slice 1 is not independently shippable.

Root-cause fix: recut the slices so the implementation slice includes the
targeted live fakeshop coverage for the sync HTTP behaviors that are reachable
as normal user requests. A clean shape is:

- Slice 1: `testing/client.py`, settings/re-exports, a small
  `examples/fakeshop/test_query/` live file or targeted live conversions that
  cover sync JSON, `assert_no_errors`, `operation_name`, login, and multipart;
  plus `tests/testing/test_client.py` only for mechanics that cannot be
  expressed as ordinary live API usage.
- Slice 2: the broad live-suite cleanup/switchover, deleting duplicate helpers
  and preserving assertions.

Alternatively, collapse the current Slice 1 and Slice 2. Do not make
package-tier real-request tests the coverage substitute for live tests.

### P2 - Package-owned public checks should not be implemented with `assert`

The spec now correctly says this package owns sync and async `query()` and the
body/multipart builder, but it still adopts upstream-style `assert` statements
for public behavior: `assert_no_errors=True` and `files=` with
`variables=None`. It even says the `assert` gate being stripped under
`python -O` is acceptable because it is inherited, but the relevant code is no
longer inherited.

References:

- [spec-043][spec-043] #"the package **owns** the `.query()` orchestration"
- [spec-043][spec-043] #"The sync **and** async `query()` orchestration"
- [spec-043][spec-043] #"`assert`-statement error gate (stripped under `python -O`) is inherited and acceptable"
- [spec-043][spec-043] #"files=` with `variables=None` raises the retained `AssertionError`"
- [strawberry-client][strawberry-client]::BaseGraphQLTestClient.query #"if assert_no_errors:"

Upstream compatibility requires the public failure shape, not the optimizer
fragility. Since this package already owns the methods, use explicit checks:
`if assert_no_errors and response.errors is not None: raise AssertionError(response.errors)`
and an explicit guard for invalid `files=` input. That preserves the documented
`AssertionError` behavior under normal Python and under `python -O`, and it
removes the false claim that the package is merely inheriting the base gate.

### P3 - The public `Response` field order is described inconsistently

Most of the spec follows Strawberry's field order
`Response(errors, data, extensions, response)`, but Goal 1 says
`Response(data, errors, extensions, response)`. The base dataclass field order
is `errors`, `data`, `extensions`, and the package subclass adds `response`
after those fields.

References:

- [spec-043][spec-043] #"`Response(data, errors, extensions, response)`"
- [spec-043][spec-043] #"`Response(errors, data, extensions, response)`"
- [strawberry-client][strawberry-client]::Response #"errors:"

Root-cause fix: document the public shape consistently as
`errors, data, extensions, response`, or avoid positional constructor language
entirely and show keyword construction in implementation-facing prose. The
client should also construct it by keyword.

### P3 - Two closeout convention details still need cleanup

The spec's link-definition block has the required groups, but the `docs/` group
is not alphabetized: `[glossary]` appears after the `glossary-*` refs. The
final DoD command line also says ``uv run ruff format .` / `ruff check --fix .``
and leaves a pytest carve-out for "the slices' own test additions", while the
repo instruction for this workspace is `uv run ruff check --fix .` and no
pytest unless explicitly asked.

References:

- [start][start] #"Defs are alphabetical within each group"
- [spec-043][spec-043] #"[glossary-auth-mutations]: GLOSSARY.md#auth-mutations"
- [spec-043][spec-043] #"[glossary]: GLOSSARY.md"
- [spec-043][spec-043] #"`uv run ruff format .` / `ruff check --fix .` clean"
- [agents][agents] #"Run uv run ruff format . and uv run ruff check --fix . after every edit"
- [agents][agents] #"Do not run pytest after edits; run only when explicitly asked"

These are not design blockers, but they are cheap to fix before this becomes
the implementation handoff.

## Resolved Since Prior Review

- `query()` ownership is now accurately package-owned instead of base-owned.
- Per-call `url=` now has an explicit non-mutating `request(..., *, url=None)`
  path.
- Test 8 now records the effective URL through an instrumented subclass, so it
  cannot pass via a non-JSON 404.
- The terms CSV is now one row per anchor and passed the spec/glossary checker.
- The WIP card state is coherent with `KANBAN.md` and `docs/TREE.md`.

## Verification

I reviewed the updated spec, the companion terms CSV, `AGENTS.md`, `START.md`,
`pyproject.toml`, Strawberry's installed `BaseGraphQLTestClient`, the local
strawberry-django test client, and graphene-django's testing helpers. I ran
`uv run python scripts/check_spec_glossary.py --spec docs/spec-043-test_client-0_0_14.md`
successfully and checked the terms CSV for duplicate anchors. I did not run
pytest.

<!-- LINK DEFINITIONS -->

<!-- Root -->

[agents]: ../AGENTS.md
[pyproject]: ../pyproject.toml
[start]: ../START.md

<!-- docs/ -->

[spec-043]: spec-043-test_client-0_0_14.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

[strawberry-client]: ../.venv/lib/python3.14/site-packages/strawberry/test/client.py

<!-- External -->
