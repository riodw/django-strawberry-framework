# Spec-043 Implementation Review (test-client family) — adversarial pass

Scope: the shipped spec-043 implementation across `c0b10ba4` (Slice 1),
`4490a069` (review fixes + Slice 2/3 wrap), and `5c71995d` (feedback2 fixes) —
`django_strawberry_framework/testing/client.py`, `testing/__init__.py`,
`conf.py::testing_endpoint_setting`, `tests/testing/test_client.py`,
`examples/fakeshop/test_query/test_client_api.py`, the
`examples/fakeshop/graphql_client.py` re-seat, and the Slice-2 suite
conversions + Slice-3 doc wrap. Every claim below was verified against source
(the installed `strawberry/test/client.py`, Django's `test/client.py`, the
spec, the build artifact) — not taken from docstrings.

The uncommitted working-tree changes (`optimizer/walker.py`,
`connection.py`, `types/resolvers.py`, `test_library_api.py`, etc.) are the
concurrent session's WIP and are **out of this review's scope** per the
AGENTS.md unexpected-modifications rule; the committed `test_library_api.py`
conversion (in `3ca7b291`) was reviewed.

Checks run for this review: `ruff format --check` and `ruff check` (clean),
`scripts/check_trailing_commas.py --check` (clean), ASCII-only scan on every
new/changed `.py` (clean), forbidden-footer scan on the five unpushed commits
(clean). pytest was **not** run (the AGENTS.md "Do not run pytest" rule); the
build artifact records the maintainer-side runs (124 passed targeted;
3038-passed full sweep; `testing/client.py` 87/87 statements).

**Verdict: ship-quality.** The core module is correct, the guard philosophy
is applied consistently (explicit `raise AssertionError`, never a bare
`assert`, at all five guard sites — survives `python -O`, verified against
the base's stripped-assert hazard), and the test placement is the strongest
live-first reading in the repo so far. Four findings, none blocking: one
missing test direction against a stated DoD claim (F1), one spec-realignment
sweep (F2), and two small hardening nits (F3, F4).

---

## F1 — DoD claims multipart "on both clients"; the async `files=` direction has no test anywhere (medium)

The spec's DoD row states: *"Multipart file upload works through
`query(..., files=...)` on **both clients**"*
(`docs/spec-043-test_client-0_0_14.md` #"Multipart file upload works
through"). Shipped coverage: the sync multipart path is proven live twice
(`test_uploads_api.py`, nested two-file input object + `operation_name`) and
the builder's shapes are pinned package-tier — but **no test anywhere drives
`AsyncTestClient.query(..., files=...)`**. The async tests in
`test_client_api.py` are JSON-only.

Mechanically it should work — `AsyncRequestFactory` overrides only
`_base_scope` / `request` / `generic` and inherits `post()`'s
`MULTIPART_CONTENT` encoding from `RequestFactory`, and the builder/decode
are shared with the sync client — but "should work" is exactly what the
repo's claim-verification standard exists to replace. The async multipart
round trip (ASGI-scope multipart parse through `AsyncClientHandler` into the
strawberry view) is genuinely unexercised, and it IS achievable live:
fakeshop's `createMediaSpecimen` + `AsyncTestClient` + the existing
`transactional_db` sync-seeding fixture pattern + `MEDIA_ROOT=tmp_path`.

**Fix (the root-cause one, per the highest-standard rule):** add one live
async multipart test to
`examples/fakeshop/test_query/test_client_api.py` — the async color of
`test_uploads_api.py::test_multipart_create_uploads_real_files_over_http`
(superuser created in a sync `transactional_db` fixture, awaited
`query(..., files={"data.attachment": ..., "data.image": ...},
operation_name=...)`, assert both files persisted). Do **not** resolve this
by narrowing the DoD wording — the claim is the right claim; it just needs
its test.

## F2 — The spec's test-placement text was not realigned to the shipped (better) placement (medium, doc-only)

The implementation moved the live-reachable coverage live — correctly: the
AGENTS.md live-first mandate says any package line earnable via a real
`/graphql/` request MUST be earned in `test_query/`. The shipped split is
`test_client_api.py` (sync raising direction, both async tests, the whole
unittest family end-to-end, the endpoint rungs against a real probe view)
vs. `tests/testing/test_client.py` (DB-free mechanics only). Both file
docstrings state this split accurately.

The spec still says otherwise at several load-bearing spots:

- `docs/spec-043-test_client-0_0_14.md::Decision 11` — *"The
  `AsyncTestClient` — … the async client's real-request tests live **here**"*
  and *"The unittest family's mechanics …"* both describe
  `tests/testing/test_client.py` as the owner; they shipped live.
- Test plan intro #"Only the assertions a live request cannot pin — the
  `assert_no_errors=True` raising direction" — the raising direction shipped
  **live**
  (`test_client_api.py::test_assert_no_errors_default_raises_with_the_errors_list`),
  which also disproves the premise that a live request "cannot pin" it.
- Scenario 2 #"pinned package-tier in `tests/testing/test_client.py`" — same.
- Scenario 3 #"fails GraphQL-side (errors present)" — live reality differs:
  Strawberry's HTTP layer defaults an absent `operationName` to the
  document's **first operation** (no error). The shipped test
  (`test_products_api.py::test_operation_name_dispatch_via_test_client`)
  pins the real behaviour and documents the divergence; the spec still
  states the wrong expectation.
- Slice-1 checklist #"the `AsyncTestClient` real-request paths (the live
  tier is sync-only)" — the premise ("the live tier is sync-only") is now
  false; the live tier runs the async tests fine.
- The DoD row for `tests/testing/test_client.py` #"async tests through
  `AsyncClient`" — describes async request-driving tests in the package
  tier.

The build artifact records the endpoint-ladder letter-deviation (four named
tests vs. one parametrized) but **not** this placement deviation, so today
neither standing document tells the truth about where the request-driving
tests live. **Fix:** one realignment sweep over the spec's Decision 11 /
Test plan / Slice-1 checklist / DoD wording to match the shipped split (the
spec is the standing doc — realign it rather than growing the build-doc
deviation list), including scenario 3's first-operation reality.

## F3 — `operation_name=""` is silently dropped instead of failing loudly (low)

`django_strawberry_framework/testing/client.py::TestClient._build_body`
#"if operation_name:" gates on truthiness, so an explicit empty string is
silently treated as absent and the server executes the document's first
operation — a silent reinterpretation of a malformed call, which cuts
against the module's own fail-at-the-source philosophy (the placeholder
walker exists precisely to reject malformed calls before the wire). The
docstring contract is "sent … only when provided"; `""` *is* provided.
**Fix:** `if operation_name is not None:` — the server then rejects the
invalid name with a real GraphQL error naming the problem. One package-tier
builder assertion covers it.

## F4 — `files=` keys can silently clobber the reserved multipart fields (low)

`TestClient._build_body` #"return {\"operations\": json.dumps(body)" spreads
`**files` last, so a pathological `files={"operations": f}` or
`files={"map": f}` (with matching `None` placeholders in `variables`, which
the walker would happily verify) silently overwrites the envelope's
`operations`/`map` fields and posts a corrupt multipart body the server has
to diagnose. The engine base shares the flaw, but the package owns this
builder precisely because the base's was insufficient — a ~2-line guard
(`raise AssertionError` on a `files` key in `{"operations", "map"}`) matches
the sibling guards' shape and message style. Low likelihood, but the fix is
cheaper than the caveat.

---

## Minor notes (no action required)

- **`permitted_writer` duplication.** The create-users → seed → `add_item`
  grant → stale-cache refetch → category-GlobalID block now exists twice
  (`test_client_api.py::permitted_writer` and
  `test_products_api.py::test_create_item_login_bracket_via_test_client`).
  ~15 lines, two sites, both correct (seed-helper-first per the AGENTS.md
  seeding rule). A shared `test_query/conftest.py` fixture is a candidate if
  a third site appears; not worth churn at two.
- **`post_graphql` `variables={}` delta.** The old helper sent
  `"variables": {}` when passed an empty dict; `TestClient._build_body`'s
  truthiness drops the key. Semantically identical server-side; no caller
  passes `{}`. Noting for completeness.
- **Double decode in the `graphql_client.py` chain.** `query()` decodes via
  `_decode` → `response.json()`, then `graphql_payload` calls
  `response.json()` again — Django's test client caches (`response._json`),
  so this is free. Keeping the raw-`HttpResponse` return contract instead of
  retrofitting the typed `Response` into ~8 suites was the right
  blast-radius call, and it is documented in the module docstring.

## Verified strengths (claims checked against source)

- **The bare-assert hazard is actually closed.** The engine base's `query()`
  gates on `assert response.errors is None` (verified in
  `strawberry/test/client.py`) — stripped under `python -O`. The package
  owns both `query()` overrides and raises explicitly; all five guard sites
  (`query` ×2, `_build_body`, `_assert_file_placeholders` ×2 shapes) use
  explicit `raise AssertionError(...)`. The `noqa: TRY004` on the
  scalar-descend branch is correct and correctly justified (uniform guard
  type for `pytest.raises(AssertionError)`).
- **The base-builder insufficiency claim is true.** Traced
  `_build_multipart_file_map` against the nested input-object shape: the
  folder heuristic takes the FIRST key (`label`), builds
  `map["data"] = ["variables.data.label"]`, then filters on `k in files` →
  empty map. The owned path-keyed builder is load-bearing, and the live
  nested two-file + `operation_name` test is exactly the envelope the base
  cannot produce.
- **The Slice-1 review round's fixes hold.** `files={}` is falsy on all
  three switches (pinned); `variables={}` hits the placeholder guard
  (pinned); the base `url` attribute is forwarded and pinned in sync with
  `path`; `assertResponseNoErrors` failures carry both fields.
- **Slice 2 is a root-cause conversion, and it is complete.** The shared
  `graphql_client.post_graphql` re-seats onto `TestClient`, converting all
  eight helper-riding suites transitively; the four per-file wrappers were
  converted/deleted; every retained raw `client.post(...)` carries the
  wire-shape exemption comment (both `test_products_api.py` raw-multipart
  sites verified); the remaining raw usages in `test_debug_toolbar_api.py`
  are GETs (content negotiation — legitimately outside a POST-JSON client);
  no orphan imports (ruff clean).
- **The endpoint ladder is fully pinned.** All five rungs, the per-call
  non-persistence guarantee, the settings-receiver restore, and the two
  mixin rungs proven END-TO-END against a real view via the request-time
  `resolve("/graphql/")` probe URLconf — a positive hit, not an exception
  shape.
- **Live-first placement is exemplary.** Async request tests use sync
  `transactional_db` seeding fixtures (the executor-thread SQLite visibility
  constraint, correctly explained in the module docstring); the unittest
  family is exercised end-to-end live including the `TransactionTestCase`
  combination; only genuinely non-live-reachable mechanics stay
  package-tier, each with a named owner.

## AGENTS.md compliance

| Rule | Status |
| --- | --- |
| Highest standard / root-cause fix | ✓ — the Slice-2 shared-helper re-seat and the owned builder are root-cause moves; the Slice-1 review round fixed causes, not symptoms |
| Test placement (tests/ vs test_query/) | ✓ — split verified file-by-file; see F2 for the spec text lagging it |
| Live-first mandate + fail_under=100 | ✓ — 87/87 recorded; every package-tier test justifies why it cannot be live. F1 is the one unproven claimed direction |
| seed_data/create_users first line | ✓ — all new catalog/auth tests lead with the helpers |
| Tests in the same change; orphan-import sweep | ✓ |
| No pytest unless asked | ✓ — not run for this review; maintainer-side runs recorded in the build artifact |
| ruff format + check --fix; trailing commas; ASCII-only .py | ✓ — re-verified clean in this review |
| Settings key lands with its feature | ✓ — `TESTING_ENDPOINT` follows the key-constant + thin-accessor precedent |
| CHANGELOG untouched; version bump deferred | ✓ — still `0.0.13` everywhere; joint-cut items correctly listed as deferred |
| Symbol-qualified refs; no `path:NN` in standing docs/code | ✓ in all new code and doc edits |
| TODO anchors removed with the shipping slice | ✓ — no `TODO(spec-043)` residue in the package |
| KANBAN/GLOSSARY/TREE via DB + re-render | ✓ — Done card with the `is_current` fix; GLOSSARY statuses correctly stay `planned for 0.0.14`; TREE rows regenerated |
| Commit hygiene (no footers, current branch) | ✓ — five unpushed commits scanned, clean, all on `main` |
