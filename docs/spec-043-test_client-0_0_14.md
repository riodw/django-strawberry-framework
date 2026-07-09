# Spec: Test client helper — `TestClient` / `AsyncTestClient` + the `GraphQLTestMixin` test-case family in `testing/client.py`, the package's live-HTTP test ergonomics

Planned for `0.0.14` (card [`WIP-ALPHA-043-0.0.14`][kanban]). This card adds the
package's **consumer-facing GraphQL test client**: a new
`django_strawberry_framework/testing/client.py` module exposing `TestClient` /
`AsyncTestClient` (thin wrappers over Django's `django.test.Client` /
`AsyncClient` that post GraphQL operations with the right content type, decode
the response, and return a typed `Response`) plus the unittest-flavored
`GraphQLTestMixin` and its two concrete two-line combinations
`GraphQLTestCase` (`(Mixin, TestCase)`) and `GraphQLTransactionTestCase`
(`(Mixin, TransactionTestCase)`), and a project-wide endpoint settings key
(`TESTING_ENDPOINT` under `DJANGO_STRAWBERRY_FRAMEWORK`,
[Decision 7](#decision-7--endpoint-resolution-the-settings-key-is-testing_endpoint-default-graphql--resolving-the-cards-graphql_testing_endpoint-working-name)).
It is a Required **dual-upstream** parity item (the card's own tags — the first
`0.0.14` card whose surface both reference libraries ship):
🍓 [`strawberry_django/test/client.py`][upstream-client] ships `TestClient` /
`AsyncTestClient` over Strawberry's
[`strawberry.test.BaseGraphQLTestClient`][venv-strawberry-test-client], and
⚛️ [`graphene_django/utils/testing.py`][upstream-testing] ships the
`graphql_query` function, `GraphQLTestMixin`, `GraphQLTestCase`, and
`GraphQLTransactionTestCase` with a `TESTING_ENDPOINT` settings knob
([`graphene_django/settings.py`][upstream-settings] `#"TESTING_ENDPOINT"`,
default `/graphql`). The package's own live acceptance suites prove the need:
every file under [`examples/fakeshop/test_query/`][test-query-readme] hand-rolls
the same POST-decode-assert pattern today (per-file helpers like
[`test_kanban_api.py`][test-kanban-api] `::_graphql_data` and
[`test_library_api.py`][test-library-api] `::_post_graphql_as_staff`, plus raw
multipart `operations` / `map` blocks in
[`test_uploads_api.py`][test-uploads-api]) — centralizing the pattern is a small
win for consumers and keeps the package's own HTTP tests crisp (the card's "Why
it matters", verbatim).

The helper is deliberately **thin and engine-riding**: Strawberry's
`BaseGraphQLTestClient` (part of the package's **hard** `strawberry-graphql`
dependency — no [soft dependency][glossary-soft-dependency], no guard, no
install hint; the first `0.0.14` card that adds **zero** new dependencies) is
the engine-owned base the package subclasses for its response decode
(`_decode`), its typed-result base (the `Response` field schema), and the
abstract `request()` seam; the package **owns** the `.query()` orchestration
itself — both colors, since the signature and return type both change
([Decision 5](#decision-5--subclass-strawberrys-basegraphqltestclient--engine-owned-base-over-a-hard-dependency-no-soft-dependency-machinery)
ground 2) — plus a small body/multipart builder (the base's cannot
express this repo's nested input-object uploads,
[Decision 9](#decision-9--multipart-uploads-files-maps-variable-paths-to-file-parts-the-package-owns-the-bodymultipart-builder-upstreams-no-op-format-kwarg-is-dropped)),
the Django-shaped `request()` (JSON POST,
multipart when `files=` is provided; a keyword-only `url=` routes one call), the endpoint resolution
(`TESTING_ENDPOINT` → constructor override), the `login()` context managers,
the typed [`Response`](#decision-6--query-returns-the-typed-response-dataclass-extended-with-the-raw-httpresponse-operation_name-is-supported)
carrying the raw `HttpResponse` beside `data` / `errors` / `extensions`, and
the graphene-shaped unittest family. `Upload`-scalar multipart mutations
([`DONE-037-0.0.11`][kanban], the card's declared dependency) drive through the
same `query(..., files=...)` call instead of dropping back to raw
`client.post(...)`.

**Version boundary** (see
[Decision 12](#decision-12--version-bumps-are-owned-by-the-joint-0014-cut)):
this card **shares the `0.0.14` patch line** with one open sibling —
[`TODO-ALPHA-044-0.0.14`][kanban] ([Response-extensions debug
middleware][glossary-response-extensions-debug-middleware]) — and follows two
landed predecessors, [`DONE-041-0.0.14`][kanban]
([`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter]) and
[`DONE-042-0.0.14`][kanban] ([Debug-toolbar
middleware][glossary-debug-toolbar-middleware]), each of which already deferred
its own cut to the same [joint `0.0.14`
cut][glossary-joint-version-cut]. So the `pyproject.toml` / `__version__` /
[`tests/base/test_init.py::test_version`][test-base-init] bump from `0.0.13` to
`0.0.14` is owned by the **joint cut** (the last `0.0.14` card to land), not by
this card — the same shared-cut posture [`spec-042`][spec-042] Decision 10 and
[`spec-041`][spec-041] Decision 10 took. No slice below bumps the version.

Status: **PLANNED — no slice built yet.**
Three slices (the card is an M with one module, one settings key, one unit-test
file, and a mechanically-wide but semantically-shallow live-suite switchover):
Slice 1 (**the `TESTING_ENDPOINT` settings key + `testing/client.py` + the
`testing` root re-exports + the targeted live coverage + `tests/testing/test_client.py`**
— the whole public surface lands in one commit; the sync request-shape
behaviours reachable as ordinary GraphQL calls (JSON, `assert_no_errors`,
`operation_name`, `login`, multipart) are earned **live** by converting the
matching `examples/fakeshop/test_query/` cases onto the helper in this slice,
and `tests/testing/test_client.py` covers only what a live request cannot pin,
so the slice is independently green under the
[live-first mandate][glossary-live-first-coverage-mandate] and the
`fail_under = 100` gate), Slice 2 (**the remaining live-suite switchover** —
the rest of `examples/fakeshop/test_query/` moves onto the helper, per-file
hand-rolled post helpers deleted where the helper's contract covers them; a
cleanup/dedup pass that adds no new package coverage), and Slice 3 (**docs +
card wrap** — the implemented-contract GLOSSARY updates, the regenerated
[`docs/TREE.md`][tree], and the kanban card flip; the release-status wording
and the version bump stay deferred to the joint cut).

Owner: package maintainer.

Predecessors: [`spec-042-debug_toolbar-0_0_14.md`][spec-042] (the most recent
spec and the canonical voice / depth / section-layout reference; its Risks
section hands this card the async-verification note its Decision 2 deferred —
resolved below as **not adopted**,
[Decision 2](#decision-2--card-scope-boundary-the-test-client-family-ships-channels-session-auth-verification-the-toolbars-async-smoke-and-fakeshop-runtime-changes-stay-out));
[`spec-041-channels_router-0_0_14.md`][spec-041] (whose Decision 11 left
Channels session-**mutating** auth execution unverified, "scoped to the
`TestClient` card or a dedicated follow-on card" — resolved below to the
follow-on, because this card's helpers wrap Django's HTTP test clients, not
Channels communicators); [`spec-037-upload_file_image_mapping-0_0_11.md`][spec-037] (the
card's declared dependency — the [`Upload` scalar][glossary-upload-scalar]
inputs the multipart path exists to drive). [`docs/GLOSSARY.md`][glossary]
carries [`TestClient`][glossary-testclient] and
[`GraphQLTestCase`][glossary-graphqltestcase] as `planned for 0.0.14`; Slice 3
updates both entry bodies to the implemented contract while the `shipped
(0.0.14)` status flips ride the joint cut.

Revision history (kept inline so the spec is self-contained):

- **Revision 1** — initial draft authored from the [`TODO-ALPHA-043-0.0.14`][kanban]
  card body via the [`docs/SPECS/NEXT.md`][next] flow (2026-07-08). Pinned: the
  canonical structured filename
  ([Decision 1](#decision-1--spec-filename-and-canonical-naming)); the
  card-scope boundary — the test-client family ships; Channels session-auth
  verification, the debug-toolbar async smoke, and fakeshop runtime changes
  stay out
  ([Decision 2](#decision-2--card-scope-boundary-the-test-client-family-ships-channels-session-auth-verification-the-toolbars-async-smoke-and-fakeshop-runtime-changes-stay-out));
  the symbol names taken verbatim from the two upstreams and distinguished by
  the import path
  ([Decision 3](#decision-3--the-symbols-are-upstreams-own-names--testclient--asynctestclient--graphqltestmixin--graphqltestcase--graphqltransactiontestcase-distinctly-ours-import-path));
  the `testing/client.py` module with the `testing` root re-exports the
  subpackage docstring already promises
  ([Decision 4](#decision-4--module-export-and-test-locations-testingclientpy-re-exported-from-the-testing-root-teststestingtest_clientpy));
  the Strawberry base-class decision resolved **for** subclassing
  `strawberry.test.BaseGraphQLTestClient` — an engine-owned base over a hard
  dependency, reusing its `_decode`, the `Response` field schema, and the
  abstract `request()` seam while **owning** the `.query()` orchestration (both
  colors) and the body/multipart builder the base cannot
  express for nested input-object uploads, with the from-scratch alternative
  rejected with reasons
  ([Decision 5](#decision-5--subclass-strawberrys-basegraphqltestclient--engine-owned-base-over-a-hard-dependency-no-soft-dependency-machinery));
  the `.query()` return-type decision resolved **for** the typed dataclass (the
  card's own recommendation), extended with the raw `HttpResponse` so the
  live-suite switchover is not blocked on status / header / cookie assertions,
  plus `operation_name=` support the Strawberry base lacks
  ([Decision 6](#decision-6--query-returns-the-typed-response-dataclass-extended-with-the-raw-httpresponse-operation_name-is-supported));
  the endpoint settings key pinned as `TESTING_ENDPOINT` (graphene's own name
  inside the already-namespaced package dict), resolving the card's
  `GRAPHQL_TESTING_ENDPOINT` working name
  ([Decision 7](#decision-7--endpoint-resolution-the-settings-key-is-testing_endpoint-default-graphql--resolving-the-cards-graphql_testing_endpoint-working-name));
  the async inheritance shape ported as-is
  ([Decision 8](#decision-8--async-shape-asynctestclient-subclasses-testclient-ported-as-is));
  the multipart mechanism stated honestly — Django's multipart encoding via an
  omitted `content_type`, upstream's no-op `format="multipart"` extra dropped
  ([Decision 9](#decision-9--multipart-uploads-files-maps-variable-paths-to-file-parts-the-package-owns-the-bodymultipart-builder-upstreams-no-op-format-kwarg-is-dropped));
  the mixin-first shape with the graphene assertion-helper names kept,
  typed-Response-shaped
  ([Decision 10](#decision-10--mixin-first-graphqltestmixin-composes-over-testclient-the-graphene-assertion-helpers-keep-their-names-typed-response-shaped));
  the test strategy — the live switchover is the primary coverage per
  the [live-first mandate][glossary-live-first-coverage-mandate] (the
  request-shape-earning subset in Slice 1, the remainder in Slice 2), with
  `tests/testing/test_client.py` owning the branches a switched suite cannot
  reach
  ([Decision 11](#decision-11--test-strategy-the-live-switchover-is-the-primary-coverage-teststestingtest_clientpy-owns-the-rest));
  and the joint-cut version deferral
  ([Decision 12](#decision-12--version-bumps-are-owned-by-the-joint-0014-cut)).
  One card-vs-source conflict is recorded in
  [Risks](#risks-and-open-questions) rather than silently reconciled: the
  card claims a `.mutate(...)` surface twice — its "Verified in upstream"
  section says `BaseGraphQLTestClient` carries `.query(...)` / `.mutate(...)`,
  and its "Why it matters" says the `strawberry_django.test.client.TestClient`
  subclass "exposes `.query(...)` / `.mutate(...)`" — but the base class read
  for this spec ships **no `mutate()`** and neither does that subclass, so
  this card ships none either, with the alias named as a cheap fallback if the
  maintainer wants the
  card's wording honored literally.

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the
vocabulary used throughout the spec:

- [`TestClient`][glossary-testclient] — the subject. The glossary already pins
  the planned contract: `TestClient` and `AsyncTestClient` helpers for live
  HTTP-level testing patterns, mirroring `strawberry-django`'s
  `test/client.py` shape. Slice 3 updates the entry body to the implemented
  contract (the status flip to `shipped (0.0.14)` rides the joint cut).
- [`GraphQLTestCase`][glossary-graphqltestcase] — the companion entry: the
  `unittest.TestCase` subclass family whose name and mixin-first shape come
  from `graphene-django`'s `utils/testing.py` and whose underlying HTTP client
  mirrors `strawberry-django`'s. Slice 3 updates this body too.
- [`Upload` scalar][glossary-upload-scalar] — the card's declared dependency
  ([`DONE-037-0.0.11`][kanban], shipped): the multipart `files=` path exists so
  `Upload`-scalar mutations drive through the helper instead of raw
  `client.post(...)` multipart blocks
  ([Decision 9](#decision-9--multipart-uploads-files-maps-variable-paths-to-file-parts-the-package-owns-the-bodymultipart-builder-upstreams-no-op-format-kwarg-is-dropped)).
- [Live-first coverage mandate][glossary-live-first-coverage-mandate] — the
  test-placement rule
  [Decision 11](#decision-11--test-strategy-the-live-switchover-is-the-primary-coverage-teststestingtest_clientpy-owns-the-rest)
  answers: the helper's primary coverage IS the switched live acceptance
  suites (the card's own DoD names the switchover); `tests/testing/test_client.py`
  covers only what a switched suite cannot reach (endpoint-resolution
  precedence, the assertion-failure directions, the unittest family's
  mechanics, the async client).
- [Schema reload discipline][glossary-schema-reload-discipline] — the fixture
  obligation any package test that executes real GraphQL through the aggregate
  fakeshop schema inherits: `tests/testing/test_client.py`'s request-driving
  tests call the single-sited
  [`schema_reload.reload_all_project_schemas()`][schema-reload] on setup, the
  same order-independence-by-reconstruction the acceptance suites use.
- [`seed_data`][glossary-seed-data] — the repo's seed-helper rule applied to
  the [Test plan](#test-plan): every product-query test's first executable
  line is `seed_data(1)` (or an explicit `seed_data(N)`) from
  `apps.products.services`.
- [Joint version cut][glossary-joint-version-cut] — why no slice here bumps
  the version: the `0.0.14` line has one open sibling and two landed
  predecessors that already deferred; the last card to land owns the version
  quintet and the release-status flips
  ([Decision 12](#decision-12--version-bumps-are-owned-by-the-joint-0014-cut)).
- [Soft dependency][glossary-soft-dependency] — cited as the **contrast**:
  this card needs none of it. `strawberry.test` ships inside the package's
  hard `strawberry-graphql>=0.262.0` dependency and `django.test` inside
  Django itself, so there is no guard, no install hint, no
  [eviction-simulated absence][glossary-eviction-simulated-absence] fixture,
  and no dependency gate — the first `0.0.14` card with a zero-dependency
  Slice 1
  ([Decision 5](#decision-5--subclass-strawberrys-basegraphqltestclient--engine-owned-base-over-a-hard-dependency-no-soft-dependency-machinery)).
- [Auth mutations][glossary-auth-mutations] — the entry whose Channels
  caveat names this card: session-mutating auth over Channels consumers is
  "scoped to the `TestClient` card (`TODO-ALPHA-043-0.0.14`) or a dedicated
  follow-on card". This spec resolves that disjunction to the **follow-on**
  ([Decision 2](#decision-2--card-scope-boundary-the-test-client-family-ships-channels-session-auth-verification-the-toolbars-async-smoke-and-fakeshop-runtime-changes-stay-out));
  Slice 3 updates the entry's wording accordingly.
- [Debug-toolbar middleware][glossary-debug-toolbar-middleware] — the landed
  `0.0.14` sibling ([`DONE-042-0.0.14`][kanban]) whose spec's Risks named
  this card's `AsyncTestClient` "the natural owner" of its async-path
  verification. This card ships the **vehicle** (an async client) but does not
  adopt the toolbar's async smoke test as its own DoD; with 042 shipped
  without it, that smoke is a follow-on (the joint cut or a dedicated card)
  reusing 042's now-landed fixture — recorded in
  [Risks](#risks-and-open-questions), not silently absorbed.
- [`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter] — the
  landed `0.0.14` predecessor. Its Channels transport is **not** what this
  card's clients drive: `TestClient` wraps `django.test.Client` (WSGI-shaped),
  `AsyncTestClient` wraps `django.test.AsyncClient` (Django's own ASGI
  handler) — neither is a Channels communicator, which is why the Channels
  session-auth verification stays a follow-on.
- [`FieldError` envelope][glossary-fielderror-envelope] — untouched here, but
  the reason the typed `Response` composes well: mutation tests read
  `res.data["createItem"]["errors"]` through the same decoded `data` mapping,
  so the helper needs no envelope-specific surface.
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] — untouched;
  noted because several live tests assert query *counts* via
  `CaptureQueriesContext` around the HTTP call, and the switchover must not
  change how many queries a request emits (the helper adds no queries — it is
  transport only).
- [`ConfigurationError`][glossary-configurationerror] — NOT used by this card
  (worth saying explicitly): a malformed `DJANGO_STRAWBERRY_FRAMEWORK` dict
  already raises it through [`conf.py`][conf]'s shared reader; the endpoint
  key itself needs no new validation beyond that existing seam, and a wrong
  endpoint value surfaces as an ordinary 404 at request time
  ([Error shapes](#error-shapes)).

## Slice checklist

Each top-level item maps to one commit / PR. **Three slices: the settings key +
module + targeted live coverage + unit tests (Slice 1), the remaining
live-suite switchover (Slice 2), and docs + card wrap (Slice 3).** The card is
an M — the client module is ~120 lines
riding an engine-owned base, and the weight is in the switchover's breadth and
the decision hygiene around the two upstream flavors.

- [ ] **Slice 1 — `TESTING_ENDPOINT` + `testing/client.py` + re-exports +
  `tests/testing/test_client.py`**
  - [ ] **The Strawberry test-module gate rides the first commit**: confirm
        `strawberry.test.BaseGraphQLTestClient` (and its `Response` dataclass)
        is importable at the package's pinned `strawberry-graphql==0.262.0`
        floor in an isolated throwaway venv (never the shared `.venv` — the
        [`spec-041`][spec-041] / [`spec-042`][spec-042] gate discipline; per
        the repo rule, `uv pip install --python <isolated-venv-python>`).
        Presence at the installed strawberry 0.316.0 is verified now
        ([`strawberry/test/client.py`][venv-strawberry-test-client] defines
        `BaseGraphQLTestClient`, `Response`, `Body`); the floor-presence check
        is upstream history re-confirmed at the gate. If it is missing at the
        floor, bump the project's Strawberry floor instead. The command and
        outcome are recorded in the build artifact
        ([Definition of done](#definition-of-done)). **No dependency gate
        otherwise** — this card adds nothing to `[project].dependencies` or
        `[dependency-groups].dev`, and `uv.lock` is untouched
        ([Decision 5](#decision-5--subclass-strawberrys-basegraphqltestclient--engine-owned-base-over-a-hard-dependency-no-soft-dependency-machinery)).
  - [ ] [`django_strawberry_framework/conf.py`][conf] — the `TESTING_ENDPOINT`
        key constant (`TESTING_ENDPOINT_KEY = "TESTING_ENDPOINT"`) and the
        `testing_endpoint_setting()` accessor defaulting to `"/graphql/"`,
        following the existing
        `conf.py::nested_connection_strategy_setting` precedent (key constant +
        thin accessor; validation stays at the consumer)
        ([Decision 7](#decision-7--endpoint-resolution-the-settings-key-is-testing_endpoint-default-graphql--resolving-the-cards-graphql_testing_endpoint-working-name)).
  - [ ] `django_strawberry_framework/testing/client.py` (new) — the package
        [`Response`](#decision-6--query-returns-the-typed-response-dataclass-extended-with-the-raw-httpresponse-operation_name-is-supported)
        dataclass (subclassing `strawberry.test.client.Response`, adding the
        raw `response`); `TestClient(BaseGraphQLTestClient)` with `__test__ =
        False`, the endpoint-resolving constructor
        (`TestClient(path=None, client=None)`), the **owned** `_build_body` +
        path-keyed file-map builder (the base's cannot express nested
        input-object uploads,
        [Decision 9](#decision-9--multipart-uploads-files-maps-variable-paths-to-file-parts-the-package-owns-the-bodymultipart-builder-upstreams-no-op-format-kwarg-is-dropped)),
        the Django-shaped `request(body, headers=None, files=None, *,
        url=None)` (JSON POST via `content_type="application/json"`; multipart
        when `files=` is provided; `url` defaults to `self.path`), the **owned**
        `query()` orchestration (adds `operation_name=` and a per-call `url=`
        override routed through `request(..., url=...)`, returns the package
        `Response`), and the
        `login(user)` context manager (`force_login` / `logout`);
        `AsyncTestClient(TestClient)` with the `AsyncClient` default, the
        `async query()` override, and the async `login()`; `GraphQLTestMixin`
        (class-attr `GRAPHQL_URL = None`, `.query(...)` delegating to a
        `TestClient` over the test case's own `self.client`, and the
        `assertResponseNoErrors` / `assertResponseHasErrors` helpers);
        `GraphQLTestCase(GraphQLTestMixin, TestCase)` and
        `GraphQLTransactionTestCase(GraphQLTestMixin, TransactionTestCase)`
        ([Decisions 3](#decision-3--the-symbols-are-upstreams-own-names--testclient--asynctestclient--graphqltestmixin--graphqltestcase--graphqltransactiontestcase-distinctly-ours-import-path)–[10](#decision-10--mixin-first-graphqltestmixin-composes-over-testclient-the-graphene-assertion-helpers-keep-their-names-typed-response-shaped)).
  - [ ] [`django_strawberry_framework/testing/__init__.py`][testing-init] —
        re-export `TestClient`, `AsyncTestClient`, `Response`,
        `GraphQLTestMixin`, `GraphQLTestCase`, `GraphQLTransactionTestCase`
        (extending `__all__`), discharging the docstring's own "Future
        exports" promise; the `relay` submodule stays submodule-only, and
        nothing is re-exported from the **package root**
        ([Decision 4](#decision-4--module-export-and-test-locations-testingclientpy-re-exported-from-the-testing-root-teststestingtest_clientpy)).
  - [ ] Targeted live coverage in [`examples/fakeshop/test_query/`][test-query-readme]
        — the sync request-shape behaviours reachable as ordinary GraphQL calls
        (JSON happy path + typed `Response`, the `assert_no_errors=False` errors
        outcome, `operation_name` dispatch, `login()` scoping, and the nested
        multipart upload) are earned **live** by converting the matching
        `test_query/` cases onto `TestClient` in this slice — not restated as
        package-tier tests, per the
        [live-first mandate][glossary-live-first-coverage-mandate]
        ([Decision 11](#decision-11--test-strategy-the-live-switchover-is-the-primary-coverage-teststestingtest_clientpy-owns-the-rest)).
  - [ ] `tests/testing/test_client.py` (new) — the package-tier tests per the
        [Test plan](#test-plan) for **only what a live request cannot pin**:
        endpoint-resolution precedence (DB-free), the `assert_no_errors=True`
        raising direction and both mixin assertion-helper failure modes, the
        `files=`-with-`variables=None` guard, the `AsyncTestClient` real-request
        paths (the live tier is sync-only), the unittest family's mechanics
        (`GRAPHQL_URL`, `self.client` delegation, the transaction case), and the
        `__test__ = False` collection guard + export surface — the async and
        unittest request-driving tests run under the
        [schema-reload][glossary-schema-reload-discipline] +
        [`seed_data`][glossary-seed-data] disciplines
        ([Decision 11](#decision-11--test-strategy-the-live-switchover-is-the-primary-coverage-teststestingtest_clientpy-owns-the-rest)).
  - [ ] Every new symbol carries its docstring (the [`docs/TREE.md`][tree]
        render fails on missing module docstrings) and any
        staged-but-not-implemented seam carries a `TODO(spec-043 Slice N)`
        source anchor per [`AGENTS.md`][agents].
- [ ] **Slice 2 — the remaining live-suite switchover** (Slice 1 already
      converted the subset that earns the helper's package coverage; this is
      the wide cleanup/dedup pass over the rest and adds no new package
      coverage)
  - [ ] Every **remaining** file under `examples/fakeshop/test_query/` whose
        hand-rolled POST-decode helper is covered by the client's contract
        switches to `TestClient` (or the mixin where a file is already
        TestCase-shaped): the per-file `_graphql_data` /
        `_post_graphql_as_staff`-style helpers are **deleted**, JSON posts go
        through `.query(...)`, multipart uploads through
        `.query(..., files=...)`, and authenticated flows through `.login(...)`
        or the underlying `client` (the raw Django client stays reachable as
        `TestClient(...).client` for session-cookie assertions).
  - [ ] The documented exemption: a test whose **subject is the raw HTTP
        envelope itself** (hand-built multipart `operations` / `map`
        assertions, malformed-body negatives, content-type negotiation, the
        [`test_multi_db.py`][test-multi-db] custom-view plumbing) keeps its
        raw `client.post(...)` with a one-line comment naming this exemption —
        the helper exists to remove boilerplate, not to launder tests whose
        point is the wire shape
        ([Decision 11](#decision-11--test-strategy-the-live-switchover-is-the-primary-coverage-teststestingtest_clientpy-owns-the-rest)).
  - [ ] Query-count assertions (`CaptureQueriesContext` blocks) re-verified
        unchanged — the helper is transport-only and must not move any query
        boundary.
- [ ] **Slice 3 — docs + card wrap (no version bump)**
  - [ ] [`docs/GLOSSARY.md`][glossary] [`TestClient`][glossary-testclient] and
        [`GraphQLTestCase`][glossary-graphqltestcase] entry bodies updated to
        the implemented contract (import path, constructor / endpoint
        resolution, the typed `Response` + raw-response field, multipart,
        login, async, the mixin family, the no-new-dependency posture); the
        [Auth mutations][glossary-auth-mutations] entry's "scoped to the
        `TestClient` card or a dedicated follow-on card" sentence resolved to
        the follow-on; the **statuses stay `planned for 0.0.14`** until the
        joint cut flips them
        ([Decision 12](#decision-12--version-bumps-are-owned-by-the-joint-0014-cut)).
  - [ ] [`docs/TREE.md`][tree] regenerated via
        [`scripts/build_tree_md.py`][build-tree-md] (never hand-edited): the
        `testing/client.py` row moves from `planned by WIP-ALPHA-043-0.0.14`
        to the real docstring-derived row, and `tests/testing/test_client.py`
        appears in the test tree.
  - [ ] [`KANBAN.md`][kanban] card wrap: `043` → Done with the next
        `DONE-043-0.0.14` id and its `SpecDoc` pointing at this spec (kanban
        DB edit + [`scripts/build_kanban_md.py`][build-kanban-md] /
        `build_kanban_html.py` re-render, never a hand-edit).
  - [ ] **Deferred to the joint `0.0.14` cut** (not this slice): the version
        quintet (`pyproject.toml`, `__version__`,
        [`tests/base/test_init.py::test_version`][test-base-init], the
        GLOSSARY package-version line, the `django-strawberry-framework`
        `version` entry in `uv.lock`), the GLOSSARY status flips to `shipped
        (0.0.14)`, the [`README.md`][readme] / [`docs/README.md`][docs-readme]
        "Coming next" → "Shipped today" moves, and the `CHANGELOG.md` bullets.
        Per [`AGENTS.md`][agents] #"Do not update CHANGELOG.md unless
        explicitly instructed", the `CHANGELOG.md` edit additionally requires
        the joint-cut slice's maintainer prompt to grant it explicitly; this
        spec describes the edit but cannot grant the permission.

## Problem statement

Testing a GraphQL endpoint over Django's test client is the same six lines
every time: build the `{"query": ..., "variables": ...}` envelope, `json.dumps`
it, POST it with `content_type="application/json"`, assert 200, decode the
body, and split `data` from `errors` — remembering that GraphQL returns **200
with an `errors` key** for most failures, so a status assertion alone proves
nothing. Multipart uploads are worse: the GraphQL multipart request spec's
`operations` / `map` envelope is fiddly enough that
[`test_uploads_api.py`][test-uploads-api] and
[`test_products_api.py`][test-products-api] each hand-build it inline today.
Both reference libraries ship exactly this helper — 🍓 `strawberry-graphql-django`
as `strawberry_django.test.client.TestClient` / `AsyncTestClient` (a thin
wrapper over `django.test.Client` returning a typed `Response`), ⚛️
`graphene-django` as `graphene_django.utils.testing`'s `graphql_query` /
`GraphQLTestMixin` / `GraphQLTestCase` / `GraphQLTransactionTestCase` family
(raw `HttpResponse` + parsing assertion helpers, endpoint from a
`TESTING_ENDPOINT` settings knob) — so a consumer migrating from either
upstream currently loses their test ergonomics at the door, against
[`GOAL.md`][goal] success criterion 7 (migrate "without bringing the source
package along").

The package's own repo is the loudest consumer: ten-plus live acceptance files
under [`examples/fakeshop/test_query/`][test-query-readme] re-spell the
pattern per file, each with its own slightly-different helper
(`_graphql_data(query, *, client=None)` in the kanban suite,
`_post_graphql_as_staff(query)` in the library suite, raw posts elsewhere).
The card's "Why it matters" names this directly: the fakeshop live tests
already do this by hand; centralizing the pattern is a small win for consumers
and keeps our HTTP tests crisp. Unlike the other three `0.0.14` cards, this
surface needs **no new dependency and no soft-dependency machinery** — the
Strawberry engine already ships the base client — so the design weight is in
the two API decisions the card flags as "decide before writing the spec" (the
`.query()` return type; base-class reuse vs. from-scratch), the endpoint
settings key, and doing the switchover without changing what any live test
proves.

## Current state

A true description of the repo as this spec is authored:

- **The `testing/` subpackage exists and already promises these exports.**
  [`django_strawberry_framework/testing/__init__.py`][testing-init] ships
  [`safe_wrap_connection_method`][glossary-safe-wrap-connection-method] (in
  `__all__`) and the `relay` submodule (deliberately not re-exported), and its
  docstring's "Future exports" block names `TestClient`, `AsyncTestClient`,
  and `GraphQLTestCase` for `0.0.14` — "The subpackage exists now so consumers
  have a stable import path". This card discharges that promise
  ([Decision 4](#decision-4--module-export-and-test-locations-testingclientpy-re-exported-from-the-testing-root-teststestingtest_clientpy)).
- **[`docs/TREE.md`][tree] reserves the module.** The target package layout
  carries `testing/client.py # planned by WIP-ALPHA-043-0.0.14 - Test client
  helper`; the target test tree carries no `tests/testing/test_client.py` row
  yet (the current `tests/testing/` holds `test_relay.py` and `test_wrap.py`).
  The regenerated tree adds both in Slice 3.
- **The engine base is present, at a hard dependency.**
  [`strawberry/test/client.py`][venv-strawberry-test-client] (installed
  strawberry 0.316.0) defines `BaseGraphQLTestClient` — `query()` building the
  body, calling the abstract `request()`, decoding, and returning the
  `Response(errors, data, extensions)` dataclass with an `assert_no_errors`
  gate — plus the static `_build_multipart_file_map(variables, files)` and
  `_decode` (multipart → `json.loads(response.content)`, json →
  `response.json()`). **The base's `_build_body` / `_build_multipart_file_map`
  are insufficient for this repo:** the map builder treats any dict-valued
  variable as a single "folder" (keying off `next(iter(values.keys()))`) and
  drops any map entry whose key is not itself a `files` key, so it returns an
  **empty map** for fakeshop's nested `variables.data.attachment` /
  `variables.data.image` shape, and `_build_body` sends no `operationName` at
  all — the two reasons the package owns its body/map builder
  ([Decision 5](#decision-5--subclass-strawberrys-basegraphqltestclient--engine-owned-base-over-a-hard-dependency-no-soft-dependency-machinery)
  ground 2,
  [Decision 9](#decision-9--multipart-uploads-files-maps-variable-paths-to-file-parts-the-package-owns-the-bodymultipart-builder-upstreams-no-op-format-kwarg-is-dropped)).
  `_decode` and the `Response` base are reused; the base's `query()` is **not**
  — it takes no `operation_name`/`url` and builds the base `Response` directly,
  so the package owns its own sync and async `query()` (Decision 5 ground 2).
  The package's
  floor is `strawberry-graphql>=0.262.0` ([`pyproject.toml`][pyproject]); the
  Slice-1 gate re-confirms the module at that floor.
- **Async test infrastructure exists.** [`pytest.ini`][pytest-ini] sets
  `asyncio_mode = auto` and the dev group carries `pytest-asyncio>=1.0.0`, so
  `async def` tests run today (the auth, connection, and mutation suites
  already use them). `django.test.AsyncClient` needs no `asgi.py` in fakeshop —
  it drives Django's own `AsyncClientHandler` in-process — so `AsyncTestClient` is
  testable against the existing WSGI-only example.
- **The endpoint is `/graphql/` everywhere the repo touches it.** Fakeshop's
  [`config/urls.py`][config-urls] mounts `graphql/`; Strawberry's own base
  defaults its (unused-by-upstream) `url` to `"/graphql/"`; graphene defaults
  `TESTING_ENDPOINT` to `"/graphql"` (no trailing slash — against a
  slash-mounted endpoint a body-bearing POST never cleanly reaches the view
  under `APPEND_SLASH`: `RuntimeError` in `DEBUG`, a body-dropping 301
  otherwise; the package default keeps the trailing slash that matches both
  fakeshop and the Strawberry ecosystem).
- **[`conf.py`][conf] has the accessor precedent.** Settings keys live as
  module constants with thin accessor functions
  (`conf.py::nested_connection_strategy_setting`,
  `conf.py::upstream_patches_enabled`); the reader already fails loud on a
  malformed non-mapping settings dict via `conf.py::_normalize_user_settings`.
  The `TESTING_ENDPOINT` key follows the same shape — and per the
  [`START.md`][start] rule ("add a settings key only when the feature that
  needs it lands"), it lands in this card's Slice 1, not before.
- **The live suites hand-roll the pattern.** Per-file helpers:
  [`test_kanban_api.py`][test-kanban-api] `::_graphql_data`,
  [`test_library_api.py`][test-library-api] `::_post_graphql_as_staff` and
  `::_post_node`, [`test_mutation_atomicity.py`][test-mutation-atomicity]'s
  `_post_update` / `_post_create` / `_post_delete` family, and raw multipart
  `operations` / `map` blocks in [`test_uploads_api.py`][test-uploads-api] and
  [`test_products_api.py`][test-products-api]. The acceptance suites share the
  [schema-reload][glossary-schema-reload-discipline] autouse fixture through
  [`test_query/conftest.py`][test-query-conftest].
- **The version line reads `0.0.13`, and the `0.0.14` joint cut is already in
  motion.** [`DONE-041-0.0.14`][kanban] and [`DONE-042-0.0.14`][kanban] both
  landed with their version bumps deferred; `TODO-ALPHA-044` is still non-Done
  at this card's patch version, so the [joint-cut rule][glossary-joint-version-cut]
  applies
  ([Decision 12](#decision-12--version-bumps-are-owned-by-the-joint-0014-cut)).

## Goals

1. **One import replaces the boilerplate.** A consumer (and the package's own
   live suites) posts a GraphQL operation, gets back a typed
   `Response(errors, data, extensions, response)`, and asserts on it — no
   `json.dumps`, no content-type string, no manual envelope split
   ([Decision 6](#decision-6--query-returns-the-typed-response-dataclass-extended-with-the-raw-httpresponse-operation_name-is-supported)).
2. **Both upstream migration paths keep their shape.** A
   `strawberry-graphql-django` migrant's `TestClient("/graphql/")` /
   `client.query(...)` / `client.login(user)` calls work with the import line
   changed; a `graphene-django` migrant's `GraphQLTestCase` subclass keeps
   `self.query(...)`, `self.assertResponseNoErrors(...)`,
   `self.assertResponseHasErrors(...)`, and the `GRAPHQL_URL` /
   `TESTING_ENDPOINT` knobs — with three documented deltas (recorded for the
   migration guide, [Out of scope](#out-of-scope-explicitly-tracked-elsewhere)):
   `query()` returns the typed `Response` rather than a raw `HttpResponse`,
   graphene's `input_data=` convenience is not carried, and everything after
   `query` is keyword-only (graphene's positional `operation_name` becomes
   `operation_name=`)
   ([Decision 3](#decision-3--the-symbols-are-upstreams-own-names--testclient--asynctestclient--graphqltestmixin--graphqltestcase--graphqltransactiontestcase-distinctly-ours-import-path)
   / [Decision 10](#decision-10--mixin-first-graphqltestmixin-composes-over-testclient-the-graphene-assertion-helpers-keep-their-names-typed-response-shaped)).
3. **Multipart uploads ride the same call, including nested input objects.**
   `query(..., variables={"file": None}, files={"file": f})` for a top-level
   file, and `query(..., variables={"data": {"attachment": None, "image":
   None}}, files={"data.attachment": f1, "data.image": f2})` for a nested
   two-file input object — the path-keyed `files=` contract the owned builder
   makes possible (the base's builder cannot), so [`Upload`-scalar][glossary-upload-scalar]
   mutations are one call — the card's `DONE-037-0.0.11` coupling, discharged
   ([Decision 9](#decision-9--multipart-uploads-files-maps-variable-paths-to-file-parts-the-package-owns-the-bodymultipart-builder-upstreams-no-op-format-kwarg-is-dropped)).
4. **The endpoint is configurable once, project-wide, with overrides at every
   layer.** `DJANGO_STRAWBERRY_FRAMEWORK["TESTING_ENDPOINT"]` with per-instance
   (constructor `path=`), per-class (`GRAPHQL_URL`), and per-call (`url=`)
   overrides — graphene's knob, package-namespaced; the per-call override is the
   card's explicitly-named constraint
   ([Decision 7](#decision-7--endpoint-resolution-the-settings-key-is-testing_endpoint-default-graphql--resolving-the-cards-graphql_testing_endpoint-working-name)).
5. **The package's own live suites get crisper.** The Slice-2 switchover
   deletes the per-file helpers and raw multipart blocks where the client's
   contract covers them, with every suite still proving exactly what it proved
   before (query counts included)
   ([Decision 11](#decision-11--test-strategy-the-live-switchover-is-the-primary-coverage-teststestingtest_clientpy-owns-the-rest)).
6. **Zero new dependencies.** No `[project].dependencies` change, no dev-group
   change, no lockfile change, no guard, no install hint
   ([Decision 5](#decision-5--subclass-strawberrys-basegraphqltestclient--engine-owned-base-over-a-hard-dependency-no-soft-dependency-machinery)).

## Non-goals

- **Channels / WebSocket test transport.** `TestClient` wraps
  `django.test.Client`; `AsyncTestClient` wraps `django.test.AsyncClient`
  (Django's in-process ASGI handler). Neither drives a Channels communicator,
  so the [`spec-041`][spec-041] deferral — session-mutating
  [auth mutations][glossary-auth-mutations] executed through Channels
  consumers — is **not** discharged here; it resolves to the dedicated
  follow-on card
  ([Decision 2](#decision-2--card-scope-boundary-the-test-client-family-ships-channels-session-auth-verification-the-toolbars-async-smoke-and-fakeshop-runtime-changes-stay-out)).
- **The debug-toolbar async smoke test.** [`spec-042`][spec-042]'s Risks named
  this card's `AsyncTestClient` the "natural owner" of the toolbar's async
  verification. The vehicle ships here; the toolbar smoke itself is that
  card's (or the joint cut's) to add — adopting it would couple this card's
  DoD to a soft-dependency middleware it otherwise never imports
  ([Risks](#risks-and-open-questions)).
- **A `mutate()` method.** Neither upstream base actually ships one (the
  card's contrary claim is a recorded conflict —
  [Risks](#risks-and-open-questions)); a GraphQL mutation posts through
  `query()` like any operation, and the docstring says so plainly.
- **graphene's `input_data=` convenience.** `graphql_query`'s `input_data`
  kwarg injects `variables["input"]` — a convention from graphene's Relay
  mutation shape (`$input`). The package's mutations take `data:` (and
  `id:`), so the convenience would encode a foreign convention; a migrant
  writes `variables={"input": ...}` explicitly. Documented as a deliberate
  non-borrow ([Borrowing posture](#borrowing-posture)).
- **Fakeshop runtime changes.** No URLs, settings, or app changes in the
  example project; Slice 2 touches only `test_query/` files.
- **Response-shape helpers beyond the envelope.** No assertion DSL, no
  snapshot helpers, no `FieldError`-envelope-specific accessors — `res.data`
  is a plain decoded mapping and test code indexes into it.
- **A package-root export.** The family stays under
  `django_strawberry_framework.testing`; the package root's public surface is
  schema-building API, and test utilities do not belong in `__all__` at the
  root ([Decision 4](#decision-4--module-export-and-test-locations-testingclientpy-re-exported-from-the-testing-root-teststestingtest_clientpy)).

## Borrowing posture

Per the [`START.md`][start] "do both libraries provide it?" test this card is
**dual-upstream, foundational**: both reference libraries ship the surface, so
the package needs it, and the borrow splits cleanly — the **client** shape
comes from `strawberry-graphql-django`, the **unittest family and settings
knob** from `graphene-django`. The card's `Verified in upstream` section names
three sources and all three were read in full for this spec (plus the
Strawberry core base class both this card and upstream ride); every behavior
below is taken from the source directly, not from memory.

### From `strawberry-graphql-django` — the client pair, near-verbatim

[`strawberry_django/test/client.py`][upstream-client] is, in full (90 lines):

- **`TestClient(BaseGraphQLTestClient)`** with `__test__ = False` (the pytest
  collection guard — the class name starts with `Test`, so without it pytest
  tries to collect the class as a test suite and warns), a
  `__init__(path, client=None)` storing `self.path` and defaulting the wrapped
  client to `django.test.Client()`, a `client` property over the base's
  `self._client`, and `request(body, headers=None, files=None)`: multipart
  kwargs when `files` is provided, else
  `content_type="application/json"`, posted to `self.path`.
- **`login(user)`** — a `contextlib.contextmanager` that `force_login`s the
  wrapped Django client, yields, and `logout()`s.
- **`AsyncTestClient(TestClient)`** — defaults the wrapped client to
  `django.test.AsyncClient` and **fully re-implements** `query()` as
  `async def` (it does **not** call the base `query()`; the flow is re-declared
  with the request awaited — the sync `request()` is reused via
  `cast("Awaitable", ...)`), and `login()` as an `asynccontextmanager` wrapping
  `force_login` / `logout` in `sync_to_async`.
- The base **ships** a `query()` orchestration on Strawberry core's
  [`BaseGraphQLTestClient`][venv-strawberry-test-client] — the build →
  `request()` → `_decode` → construct `Response` → `assert_no_errors` flow — but
  its signature is fixed (`query(query, variables=None, headers=None,
  files=None, assert_no_errors=True)`: no `operation_name`, no `url`), it calls
  `request(body, headers, files)` with no target argument, and it constructs the
  base `Response(errors, data, extensions)` directly. A client that needs
  `operation_name=`, a per-call `url=`, and the package `Response` (carrying the
  raw `HttpResponse`) therefore **cannot ride that method** — it must own its
  own `query()`. This is not a new posture: upstream's own
  `AsyncTestClient.query()` already fully re-implements the flow rather than
  calling `super().query()`, so owning the **sync** `query()` here is the same
  move applied to both colors. What the package genuinely reuses from the base
  is narrower and load-bearing: `_decode` (the JSON / multipart response split),
  the `Response` **field schema** (the package `Response` subclasses
  `strawberry.test.client.Response`, inheriting `errors` / `data` /
  `extensions`), and the `request()` **ABC seam** (the one abstract method). The
  base also ships `_build_body` / `_build_multipart_file_map`, which the package
  **does not** reuse either — the map builder returns an empty
  map for nested input-object uploads and there is no `operationName` support,
  so the package owns an equivalent path-keyed builder
  ([Decision 5](#decision-5--subclass-strawberrys-basegraphqltestclient--engine-owned-base-over-a-hard-dependency-no-soft-dependency-machinery)
  ground 2,
  [Decision 9](#decision-9--multipart-uploads-files-maps-variable-paths-to-file-parts-the-package-owns-the-bodymultipart-builder-upstreams-no-op-format-kwarg-is-dropped)).

Borrowed as-is: the class names, the inheritance shape (async subclasses
sync), `__test__ = False`, the `login` context managers, `_decode`, the
`Response` field schema, and the `request()` ABC seam. Owned outright: the
sync **and** async `query()` orchestration (the signature and return type both
change) and the body/multipart-map build (above). The deltas from upstream's
concrete client: the constructor's `path` becomes optional (endpoint
resolution,
[Decision 7](#decision-7--endpoint-resolution-the-settings-key-is-testing_endpoint-default-graphql--resolving-the-cards-graphql_testing_endpoint-working-name));
the concrete `request()` gains a keyword-only `url=` (default `self.path`) so
the package-owned `query()` can route a single call without mutating stored
state
([Decision 7](#decision-7--endpoint-resolution-the-settings-key-is-testing_endpoint-default-graphql--resolving-the-cards-graphql_testing_endpoint-working-name));
`query()` gains `operation_name=` and the per-call `url=` and returns the package
`Response` carrying the raw `HttpResponse`
([Decision 6](#decision-6--query-returns-the-typed-response-dataclass-extended-with-the-raw-httpresponse-operation_name-is-supported));
the `files=` contract becomes path-keyed for nested uploads; and upstream's
no-op `format="multipart"` extra is dropped
([Decision 9](#decision-9--multipart-uploads-files-maps-variable-paths-to-file-parts-the-package-owns-the-bodymultipart-builder-upstreams-no-op-format-kwarg-is-dropped)).

### From `graphene-django` — the unittest family and the settings knob

[`graphene_django/utils/testing.py`][upstream-testing] (162 lines):

- **`graphql_query(...)`** — module-level function building the JSON envelope
  (`query`, optional `operationName`, optional `variables`, the `input_data`
  convenience) and posting it with `content_type="application/json"` to
  `graphql_url or graphene_settings.TESTING_ENDPOINT`.
- **`GraphQLTestMixin`** — the reusable piece: class attribute `GRAPHQL_URL =
  graphene_settings.TESTING_ENDPOINT`, a `query(...)` method delegating to
  `graphql_query` with `client=self.client`, the deprecated `_client`
  property shim, and the two assertion helpers — `assertResponseNoErrors`
  (status 200 **and** no `errors` key) and `assertResponseHasErrors` (an
  `errors` key present; the docstring warns "Even with errors, GraphQL
  returns status 200!").
- **`GraphQLTestCase(GraphQLTestMixin, TestCase)`** and
  **`GraphQLTransactionTestCase(GraphQLTestMixin, TransactionTestCase)`** —
  the two-line concrete combinations.
- [`graphene_django/settings.py`][upstream-settings] `#"TESTING_ENDPOINT"` —
  the project-wide endpoint default (`"/graphql"`) read from graphene's own
  settings dict.

Borrowed: the mixin-first shape and all three class names, the assertion
helper names and their **semantics** (no-errors asserts HTTP 200 too; both
raise with the decoded content as the failure message), `operation_name`
support, and the settings-knob idea under the package's own dict. The mixin's
`query()` delegates to the package `TestClient` rather than a module-level
function, so the body-building logic exists once
([Decision 10](#decision-10--mixin-first-graphqltestmixin-composes-over-testclient-the-graphene-assertion-helpers-keep-their-names-typed-response-shaped)).

### Explicitly do not borrow

- **graphene's raw-`HttpResponse` return.** The card's architectural posture
  asks for one flavor, pinned; the typed dataclass wins (the card's own
  recommendation), with the raw response carried as a field so nothing the
  raw flavor could do is lost
  ([Decision 6](#decision-6--query-returns-the-typed-response-dataclass-extended-with-the-raw-httpresponse-operation_name-is-supported)).
- **graphene's `input_data=` kwarg** — the `$input` Relay-mutation
  convention is not this package's mutation shape ([Non-goals](#non-goals)).
- **graphene's `_client` deprecation shim** — legacy compatibility for
  graphene's own history; the package has no such history to shim.
- **graphene's module-level `graphql_query` function** — the free-function
  flavor duplicates the client's body building; consumers who want a bare
  function instantiate `TestClient()` in a fixture. Rejected to keep one
  body-builder ([Decision 10](#decision-10--mixin-first-graphqltestmixin-composes-over-testclient-the-graphene-assertion-helpers-keep-their-names-typed-response-shaped)).
- **upstream strawberry-django's `format="multipart"` kwarg** — a no-op
  against Django's test client (the multipart behavior actually comes from
  omitting `content_type`); dropped, with the real mechanism documented
  ([Decision 9](#decision-9--multipart-uploads-files-maps-variable-paths-to-file-parts-the-package-owns-the-bodymultipart-builder-upstreams-no-op-format-kwarg-is-dropped)).
- **`typing_extensions.override`** — upstream decorates `AsyncTestClient.query`
  with `@override`; the package does not depend on `typing_extensions`
  directly (the [`spec-042`][spec-042] precedent), so the override intent is
  carried by docstrings and tests.
- **graphene's `"/graphql"` default** — the package default is `"/graphql/"`
  (trailing slash), matching fakeshop's URLconf, Strawberry core's own base
  default, and Django's `APPEND_SLASH` convention
  ([Decision 7](#decision-7--endpoint-resolution-the-settings-key-is-testing_endpoint-default-graphql--resolving-the-cards-graphql_testing_endpoint-working-name)).

## User-facing API

The pytest-flavored client (the shape the package's own suites use):

```python
from django_strawberry_framework.testing import TestClient

def test_items(db):
    client = TestClient()  # endpoint: DJANGO_STRAWBERRY_FRAMEWORK["TESTING_ENDPOINT"], default "/graphql/"
    res = client.query(
        "query Items($first: Int) { allItems(first: $first) { edges { node { name } } } }",
        variables={"first": 2},
    )
    assert res.errors is None          # already asserted by default (assert_no_errors=True)
    assert res.data["allItems"]["edges"]
    assert res.response.status_code == 200   # the raw django.http.HttpResponse rides along
```

Expecting errors, authenticated flows, and multipart uploads:

```python
res = client.query("{ nope }", assert_no_errors=False)
assert res.errors and res.errors[0]["message"]

with client.login(user):               # force_login / logout around the block
    res = client.query(CREATE_ITEM, variables={"data": {...}})

# Upload-scalar mutation — a nested input object with two file fields.
# Each files= key is the variable path the file binds to; variables carries
# a None placeholder at each path.
res = client.query(
    """
    mutation Create($data: MediaSpecimenInput!) {
      createMediaSpecimen(data: $data) {
        result { label attachment { name size } image { name width } }
        errors { field messages }
      }
    }
    """,
    variables={"data": {"label": "uploaded", "attachment": None, "image": None}},
    files={
        "data.attachment": SimpleUploadedFile("up.txt", b"hi"),
        "data.image": SimpleUploadedFile("up.png", png_bytes),
    },
    operation_name="Create",
)
assert res.data["createMediaSpecimen"]["errors"] == []
```

The async twin (Django's in-process ASGI handler — no `asgi.py` required):

```python
from django_strawberry_framework.testing import AsyncTestClient

async def test_items_async(db):
    client = AsyncTestClient()
    res = await client.query("{ allItems(first: 1) { edges { node { name } } } }")
    assert res.data["allItems"]["edges"]
```

The unittest family (graphene-django's shape):

```python
from django_strawberry_framework.testing import GraphQLTestCase

class ProductsTests(GraphQLTestCase):
    # GRAPHQL_URL = "/graphql/"        # optional per-class override of the settings key

    def test_items(self):
        res = self.query("query Items { allItems(first: 1) { edges { node { name } } } }",
                         operation_name="Items")
        self.assertResponseNoErrors(res)   # HTTP 200 AND res.errors is None

    def test_bad_selection(self):
        res = self.query("{ nope }")
        self.assertResponseHasErrors(res)
```

The project-wide endpoint knob, the per-call override, and both migration diffs:

```python
# settings.py (only needed when the endpoint is not /graphql/)
DJANGO_STRAWBERRY_FRAMEWORK = {
    "TESTING_ENDPOINT": "/api/graphql/",
}
```

```python
# Overrides, highest precedence first: per-call > constructor > class attr > settings > default
res = client.query("{ __typename }", url="/other/graphql/")   # this one request only
client = TestClient("/api/graphql/")                          # this client instance
class MyTests(GraphQLTestCase):
    GRAPHQL_URL = "/api/graphql/"                             # this test-case class
```

```diff
- from strawberry_django.test.client import TestClient
+ from django_strawberry_framework.testing import TestClient
```

```diff
- from graphene_django.utils.testing import GraphQLTestCase
+ from django_strawberry_framework.testing import GraphQLTestCase
```

Consumer-visible behavior:

- **`query()` posts and decodes.** The body is `{"query": ...}` plus
  `variables` and `operationName` when provided; the POST carries
  `content_type="application/json"`; the return is the typed
  `Response(errors, data, extensions, response)`. With `assert_no_errors=True`
  (the default) a response carrying `errors` raises `AssertionError`
  immediately, so the un-asserted happy path stays one line.
- **The mixin's `query()` is the same call routed through the test case's own
  `self.client`** (so `self.client.force_login(...)`, cookie state, and
  per-test-case client configuration all apply), returning the same typed
  `Response`; the graphene-named assertion helpers take that `Response`.
- **`files=` switches to multipart.** Each `files=` key is the variable path
  the file binds to (`"file"`, `"data.image"`, `"tags.0"`); `variables` holds a
  matching `None` placeholder at each path; the client's owned builder emits the
  GraphQL multipart spec's `operations` / `map` fields, one uniform
  `map[key] = ["variables." + key]` rule
  ([Decision 9](#decision-9--multipart-uploads-files-maps-variable-paths-to-file-parts-the-package-owns-the-bodymultipart-builder-upstreams-no-op-format-kwarg-is-dropped)).
- **`login(user)`** wraps the block in `force_login` / `logout` (sync context
  manager on `TestClient`, async on `AsyncTestClient`).
- **The raw Django client stays reachable** as `.client` for anything the
  helper does not wrap (session-cookie inspection, `enforce_csrf_checks`
  clients passed into the constructor, custom headers per POST via
  `headers=`).

### Error shapes

- **GraphQL errors under the default `assert_no_errors=True`** —
  `AssertionError` carrying the errors list. The engine base uses a bare
  `assert response.errors is None`, and strawberry-django's async override uses
  the message form `assert response.errors is None, response.errors`; because
  this package **owns** both `query()` overrides
  ([Decision 5](#decision-5--subclass-strawberrys-basegraphqltestclient--engine-owned-base-over-a-hard-dependency-no-soft-dependency-machinery)),
  it does not inherit that gate — it raises explicitly,
  `raise AssertionError(response.errors)`, **not** a bare `assert` statement, so
  the documented failure survives `python -O` (which strips `assert`s). The
  `AssertionError` type and the errors-in-the-message form match both upstreams;
  only the optimizer-fragile statement form is dropped. Tests that *expect*
  errors pass `assert_no_errors=False` and assert on `res.errors`.
- **A non-JSON response body** (wrong endpoint → 404 HTML page, a
  misconfigured middleware returning HTML) — for the JSON path (the default),
  `_decode` calls Django's `response.json()`, which checks the `Content-Type`
  header **first** and raises **`ValueError`**
  (`'Content-Type header is "text/html", not "application/json"'`) when it is
  not JSON — **not** `json.JSONDecodeError` (verified against
  [`django/test/client.py`][django-client] `::ClientMixin._parse_json`).
  `json.JSONDecodeError` (a `ValueError` subclass) surfaces only when the header
  *is* `application/json` but the body is malformed, or on the multipart decode
  path (`json.loads(response.content.decode())`, which does not sniff the
  header). Deliberately **not** wrapped either way: the raise happens before the
  `Response` is built (so `res` never exists), the traceback carries the failing
  status, and the consumer's first debugging question ("what did the server
  actually return?") is answered directly — the honest failure for a
  transport-level misconfiguration. The docstring names the two usual causes
  (endpoint typo; `TESTING_ENDPOINT` not matching the project's URLconf) and the
  `ValueError`/`JSONDecodeError` split.
- **A malformed `DJANGO_STRAWBERRY_FRAMEWORK` settings value** (non-mapping) —
  [`ConfigurationError`][glossary-configurationerror] from
  [`conf.py`][conf]'s existing `_normalize_user_settings` seam, unchanged by
  this card; the endpoint accessor adds no validation of its own (a wrong
  *string* is a 404 at request time, which the previous bullet covers).
- **`files=` with `variables=None`** — the owned `_build_body` guards this with
  an explicit `if files is not None and variables is None: raise
  AssertionError(...)` (the multipart `map` needs variable paths to point at) —
  an explicit raise rather than the base's bare `assert variables is not None`,
  so it holds under `python -O`. Documented: every file's path must appear
  as a `None` placeholder in `variables`.
- **Async misuse** — calling `AsyncTestClient.query(...)` without awaiting is
  the standard un-awaited-coroutine failure; pytest-asyncio's `asyncio_mode =
  auto` plus the suite's `-W error` posture turns the `RuntimeWarning` into a
  loud failure. No package-specific guard is added (nothing package-specific
  is wrong).

## Architectural decisions

### Decision 1 — Spec filename and canonical naming

This spec lives at `docs/spec-043-test_client-0_0_14.md`: card NNN `043`, topic
slug `test_client` (the card's subject), version segment `0_0_14` from the
card's trailing `-0.0.14`. Follows the [`docs/SPECS/NEXT.md`][next] convention.

Alternatives considered (and rejected):

- **`spec-043-test_client_helper-0_0_14.md`.** Rejected: the `_helper` suffix
  adds length without disambiguation — no other card touches the test-client
  surface.
- **`spec-043-testing_client-0_0_14.md`.** Rejected: the slug names the
  card's subject (the test client), not the module path; the established slug
  style is subject-first (`debug_toolbar`, `channels_router`,
  `auth_mutations`).

### Decision 2 — Card-scope boundary: the test-client family ships; Channels session-auth verification, the toolbar's async smoke, and fakeshop runtime changes stay out

**In scope:** `testing/client.py` (the `TestClient` / `AsyncTestClient` /
`Response` / `GraphQLTestMixin` / `GraphQLTestCase` /
`GraphQLTransactionTestCase` surface), the `TESTING_ENDPOINT` settings key +
[`conf.py`][conf] accessor, the `testing` root re-exports,
`tests/testing/test_client.py`, and the Slice-2 live-suite switchover.

**Out of scope, with owners:**

- **Channels session-auth verification.** The [Auth
  mutations][glossary-auth-mutations] glossary entry and [`spec-041`][spec-041]
  Decision 11 left session-mutating auth over Channels consumers unverified,
  "scoped to the `TestClient` card (`TODO-ALPHA-043-0.0.14`) or a dedicated
  follow-on card". This spec resolves the disjunction to the **follow-on**:
  the card's own DoD, predicted files, and both upstream references are
  HTTP-client-shaped (`django.test.Client` / `AsyncClient`); a Channels
  verification needs a communicator-based vehicle
  (`channels.testing.HttpCommunicator` / `WebsocketCommunicator`, the
  [`tests/test_routers.py`][test-routers] machinery), which is a different
  helper with a different soft-dependency posture (`channels` is soft; this
  card's dependencies are all hard). Bolting a communicator wrapper onto this
  card would smuggle a soft-dependency surface into a zero-dependency card.
  Slice 3 updates the glossary sentence to name the follow-on plainly.
- **The debug-toolbar async smoke.** [`spec-042`][spec-042]'s Risks named
  `AsyncTestClient` the natural owner of the toolbar's async verification.
  This card ships the vehicle and stops there: the toolbar is a soft
  dependency this card's modules never import, and — with 042 now shipped
  without the smoke — its async claim belongs to a follow-on (the joint cut
  or a dedicated card), not this zero-dependency card
  ([Risks](#risks-and-open-questions)).
- **Fakeshop runtime surface.** No settings, URL, or app changes; Slice 2
  edits `test_query/` only.
- **Migration-guide prose.** The two import-diff rows and the
  `query()`-return-type delta are recorded for [`TODO-BETA-056-0.1.6`][kanban]
  ([Out of scope](#out-of-scope-explicitly-tracked-elsewhere)).

Justification: the card's DoD names exactly the in-scope set; the two
adjacent handoffs are disjunctions this spec must resolve but not absorb —
[`START.md`][start]'s "resist scope creep" rule applied to a card that two
sibling specs point at.

Alternatives considered (and rejected):

- **Adopt the Channels verification here** (the other arm of the glossary's
  disjunction). Rejected: wrong vehicle (communicators, not test clients),
  wrong dependency posture (soft `channels` in a zero-new-dependency card),
  and an M card would swell past its size for a deliverable the router card
  already scoped out of itself.
- **Adopt the toolbar async smoke.** Rejected: it would make this card's test
  suite import a soft dependency (`django-debug-toolbar`) and reproduce
  spec-042's settings fixture for one assertion a follow-on can add by reusing
  042's now-landed fixture and machinery.

### Decision 3 — The symbols are upstream's own names — `TestClient` / `AsyncTestClient` / `GraphQLTestMixin` / `GraphQLTestCase` / `GraphQLTransactionTestCase`, distinctly-ours import path

All five public class names are taken verbatim from the upstream that ships
them: `TestClient` / `AsyncTestClient` from `strawberry_django.test.client`,
`GraphQLTestMixin` / `GraphQLTestCase` / `GraphQLTransactionTestCase` from
`graphene_django.utils.testing`. The distinguishing identity is the import
path — `django_strawberry_framework.testing` — exactly the
[`spec-042`][spec-042] Decision 3 argument (a symbol whose public identity is
"the thing you import from the package" needs no invented name): a migrant
swaps only the import line — the symbol names carry over verbatim. For a
`strawberry-graphql-django` client migrant that is the entire change,
[`GOAL.md`][goal] success criterion 7 in its most literal form; a
`graphene-django` mixin migrant swaps the same one import line and inherits
only the three documented behavioral deltas ([Goal 2](#goals)). `Response` is
likewise kept as the typed-result name (Strawberry core's own), re-exported so
consumers can annotate helpers.

The concrete test-case pair keeps graphene's exact split — `TestCase` vs.
`TransactionTestCase` — because that split is Django's own testing vocabulary,
not a graphene-ism: consumers reach for the transaction flavor when the code
under test uses `transaction.on_commit` or needs real commits (the package's
own [`test_mutation_atomicity.py`][test-mutation-atomicity] concern).

Alternatives considered (and rejected):

- **`DjangoTestClient` / package-prefixed names.** Rejected: the package's
  `Django*` prefix marks schema-side public API ([`DjangoType`][glossary-djangotype],
  [`DjangoConnectionField`][glossary-djangoconnectionfield]); test utilities are namespaced by their module
  path, and a renamed symbol breaks the one-line migration for zero gain.
- **`GraphQLTransactionTestCase` shortened to `GraphQLTxTestCase`.**
  Rejected: graphene migrants grep for the upstream name; abbreviation saves
  nothing.
- **A single `GraphQLTestCase` with a class flag for transaction behavior.**
  Rejected: Django's own `TestCase` / `TransactionTestCase` are distinct
  classes with distinct semantics; flattening them into a flag would be a
  package-invented indirection over a Django concept.

### Decision 4 — Module, export, and test locations: `testing/client.py`, re-exported from the `testing` root, `tests/testing/test_client.py`

The module lands at `django_strawberry_framework/testing/client.py` — the
card's predicted file, [`docs/TREE.md`][tree]'s reserved row, and the exact
mirror of upstream's `test/client.py` under the package's existing `testing/`
subpackage (the subpackage is named `testing/`, not `test/`, because a
top-level `test/` would shadow the Python stdlib `test` package — the reason
recorded for the package's own earlier `test/` → `testing/` rename). The
public import
path is the `testing` **root**: [`testing/__init__.py`][testing-init]
re-exports `TestClient`, `AsyncTestClient`, `Response`, `GraphQLTestMixin`,
`GraphQLTestCase`, and `GraphQLTransactionTestCase`, extending `__all__` —
discharging the docstring's own "Future exports" promise, which names three of
these six (`TestClient`, `AsyncTestClient`, `GraphQLTestCase`) against this
path ("so consumers have a stable import path
`from django_strawberry_framework.testing import ...`"); this card lands all
six there.

Two locality contrasts worth pinning, because the subpackage now holds all
three postures at once: `safe_wrap_connection_method` is root-re-exported (it
predates this card), the `relay` helpers are deliberately submodule-only
(their docstring: keeping them out of `__init__` keeps the import light —
their `types`-package imports are paid only by suites that use them), and
this card's family is root-re-exported **by prior written commitment**. The
import-weight argument that kept `relay` out does not bite here: the client
module imports `django.test` and `strawberry.test` — both already imported by
any process running Django tests, which is the only process that imports
`testing` at all.

Tests land at `tests/testing/test_client.py` (the card's DoD row) beside the
subpackage's existing `test_relay.py` / `test_wrap.py`.

Nothing is exported from the **package root**:
`getattr(django_strawberry_framework, "TestClient")` raises `AttributeError`
(the root's [`__getattr__`][init] PEP 562 seam), and the
`from django_strawberry_framework import TestClient` **statement form** surfaces
that as `ImportError` — Python's import machinery converts a module
`__getattr__`'s `AttributeError` into `ImportError` for `from ... import ...`.
The [Test plan](#test-plan) (Test 14) pins the accurate shapes, not a single
`AttributeError` around the import statement. The root's `__all__` is the
schema-building surface; test utilities live where consumers' test code
imports from, and both upstreams make the same separation (`strawberry_django.test`,
`graphene_django.utils.testing`).

Alternatives considered (and rejected):

- **Submodule-only (`from django_strawberry_framework.testing.client import
  TestClient`), the `relay` posture.** Rejected: it contradicts the
  subpackage docstring's standing promise, and the light-import rationale that
  justified the `relay` exception does not apply (see above).
- **Package-root export.** Rejected: pollutes the schema-building `__all__`
  with test-only names; neither upstream does it.
- **A new top-level `test/` subpackage mirroring upstream's path exactly.**
  Rejected: the `testing/` subpackage exists, is documented, and already
  carries the "Future exports" plan; two test-utility subpackages is a
  migration aid for nobody.

### Decision 5 — Subclass Strawberry's `BaseGraphQLTestClient` — engine-owned base over a hard dependency; no soft-dependency machinery

This resolves the card's second "decide before writing the spec" item —
"subclass `strawberry.test.BaseGraphQLTestClient` (less code, couples our
`.query()` / `.mutate()` shape to upstream Strawberry's choices) vs. roll our
own base (more code, full control over the public surface)" — **for
subclassing**, upstream strawberry-django's own choice.

Three grounds:

1. **The base is engine-owned over a hard dependency.** `strawberry.test`
   ships inside `strawberry-graphql>=0.262.0` — the package's first-listed
   hard dependency — so riding it costs no guard, no install hint, no
   [eviction-simulated absence][glossary-eviction-simulated-absence] fixture,
   and no lockfile change. This is the same posture [`spec-041`][spec-041]
   Decision 7 took for `strawberry.channels`'s consumers ("engine-owned,
   never subclassed" there; here the base is *designed* for subclassing — it
   is an ABC whose one abstract method is `request()`).
2. **The package owns the `query()` orchestration and the body/map build; the
   base owns the decode, the `Response` field schema, and the `request()`
   seam.** What subclassing genuinely reuses is `_decode` (the JSON/multipart
   split), the `Response` **field schema** (`errors` / `data` / `extensions`,
   which the package `Response` subclasses), and the `request()` ABC seam — all
   worth pinning to the engine. What it does **not** reuse is the base's
   `query()`: that method takes no `operation_name` and no `url`, calls
   `request(body, headers, files)` with no target, and constructs the base
   `Response` directly, so a client that adds those keywords and returns the
   raw-response-carrying package `Response` must own its own `query()` (sync and
   async alike — upstream already re-implements the async one). Nor does it
   reuse the body builder: the base's
   `_build_multipart_file_map` cannot express this repo's own upload shapes.
   Read for this spec (`strawberry/test/client.py`), it treats any dict-valued
   variable as a single-list "folder", takes `next(iter(values.keys()))` as
   the folder key, and finally drops any map entry whose key is not itself a
   `files` key — so fakeshop's nested input object
   `variables={"data": {"attachment": None, "image": None}}` yields an **empty
   map**, not `variables.data.attachment` / `variables.data.image` (proven
   against [`test_uploads_api.py`][test-uploads-api] and
   [`test_products_api.py`][test-products-api]). The base also has **no
   `operationName` support at all**, and its `_build_body` JSON-encodes
   `operations` before the package could inject one. So the package owns a
   small `_build_body` + path-keyed file-map builder
   ([Decision 9](#decision-9--multipart-uploads-files-maps-variable-paths-to-file-parts-the-package-owns-the-bodymultipart-builder-upstreams-no-op-format-kwarg-is-dropped)) —
   ~15 lines, simpler than the base's because the public `files=` contract
   carries the variable path explicitly. This is still a narrower own-surface
   than a from-scratch base: the package owns its `query()` and body build
   either way, but subclassing lets it ride the engine's `_decode` and
   `Response` field schema rather than re-declaring those wire-format seams too.
3. **Migration parity.** Subclassing keeps `.query()`'s signature and
   `Response`'s field names byte-compatible with what a strawberry-django
   migrant's test suite already calls.

The card's counterargument — "the package's DRF-first stance argues for
considering the from-scratch alternative" — was considered and is answered by
the coupling actually at stake: the base pins `_decode` and `Response` field
names, both of which the package **wants** pinned to the engine (the wire
format is the engine's); the body build the package owns outright (ground 2),
and the package-shaped surface (endpoint resolution, `operation_name`, the
raw-response field, the unittest family) all lands in the subclass anyway.
DRF-first governs the *consumer configuration surface* (`class Meta`, settings
keys) — which this card does shape itself — not the reuse of the engine
`_decode` / `Response` seams the package's own read/write paths already treat
as the wire contract.

Consequences, stated plainly: a future Strawberry release reshaping
`BaseGraphQLTestClient` (signature or `Response` fields) breaks the subclass —
the same upstream-coupling class of risk as every engine seam the package
rides, contained the same way (the floor gate at `0.262.0`, the suite failing
loudly under a refreshed lock, [Risks](#risks-and-open-questions)). Because the
package **owns** `query()` (it does not inherit the base's), the
`assert_no_errors` gate is package code: it is implemented as an explicit
`raise AssertionError(response.errors)`, not a bare `assert` statement, so the
documented failure survives `python -O` (which strips `assert`s). The
`AssertionError` type and the errors-in-the-message form match both upstreams;
only the optimizer-fragile statement form is dropped.

**No soft-dependency machinery, stated as a contract:** no `require_*()`
guard, no install-hint constant, no [PEP 562 export][glossary-pep-562-lazy-export],
no absence tests. The
[Test plan](#test-plan) has no absence matrix — a deliberate first for the
`0.0.14` line, and the reason Slice 1 has no dependency gate beyond the floor
re-confirmation.

Alternatives considered (and rejected):

- **Roll a package-owned base.** Rejected on the three grounds above; the
  only surface it would free is already free in the subclass.
- **Wrap (compose) instead of subclass.** Rejected: composition would
  re-declare `query()`'s full signature just to delegate, and the base is an
  ABC designed for exactly this subclass shape.
- **Subclass but keep the base's `_build_multipart_file_map` (no owned
  builder).** Rejected on the finding in ground 2: the base's folder heuristic
  returns an empty map for fakeshop's nested input-object uploads, so keeping
  it would force the existing upload suites to stay on raw `client.post(...)`
  and shrink the consumer-facing contract this card is meant to ship. The
  package owns a path-keyed builder instead.
- **Fork/patch the base's map builder into the package.** Rejected: it forks
  engine-internal code and inherits its folder-key guessing; the public
  path-keyed `files=` contract lets the package's own builder be ~15 lines and
  independent of the base's heuristic
  ([Decision 9](#decision-9--multipart-uploads-files-maps-variable-paths-to-file-parts-the-package-owns-the-bodymultipart-builder-upstreams-no-op-format-kwarg-is-dropped)).

### Decision 6 — `.query()` returns the typed `Response` dataclass, extended with the raw `HttpResponse`; `operation_name=` is supported

This resolves the card's first "decide before writing the spec" item — the
typed `Response` dataclass (strawberry-django) vs. the raw Django
`HttpResponse` + parsing assertion helpers (graphene-django); "the two flavors
are not interchangeable — pick one and pin it (the typed-dataclass shape is
the more DRF-shaped choice and composes better with future typed-error
work)". **Pinned: the typed dataclass**, per the card's own recommendation —
preserved here as the Decision, not re-litigated — with one extension that
makes the pick total instead of partial:

```python
@dataclass
class Response(strawberry.test.client.Response):   # errors / data / extensions
    response: Any = None   # the raw django.http.HttpResponse the operation rode
```

The `response` field is what lets **every** consumer of the raw flavor move
over: the graphene mixin's `assertResponseNoErrors` asserts HTTP 200 (needs
`status_code`); the package's own live suites assert session cookies, response
headers, and status codes around GraphQL calls. Without the field, the Slice-2
switchover would strand exactly those tests on raw `client.post(...)` and the
card's "live HTTP tests switch to the helper" DoD would quietly shrink. With
it, the typed shape is a strict superset of both upstream flavors: `res.data`
/ `res.errors` / `res.extensions` for the strawberry-django migrant,
`res.response.<anything>` for the graphene migrant and the package's own
suites. The field takes a `None` default as a deliberate choice (the parent's
three fields carry no defaults, so a defaultless child field would be legal
too) — but the client always populates it, so the default is never observed
in practice.

Because the subclassed `Response` must be constructed by the client, `query()`
is overridden in `TestClient` (sync) and `AsyncTestClient` (async — upstream
already overrides it there). The override adds two keyword-only signature
extensions, both **appended after** the base's positional parameters
(`query, variables, headers, files, assert_no_errors`) so strawberry-django
migrants' positional calls keep working: **`operation_name=`** and a per-call
**`url=`** endpoint override
([Decision 7](#decision-7--endpoint-resolution-the-settings-key-is-testing_endpoint-default-graphql--resolving-the-cards-graphql_testing_endpoint-working-name)).
The Strawberry base cannot send `operationName` at all; graphene can; multi-
operation documents (and the [Debug-toolbar
middleware][glossary-debug-toolbar-middleware]'s named-operation tests, per
its spec's Test 3) need it. The body gains `operationName` only when the
argument is provided — an absent key, never an explicit `null` — matching
graphene's `if operation_name:` behavior.

**No `mutate()`.** The card attributes a `.mutate()` surface twice — its
"Verified in upstream" section to the upstream base (`BaseGraphQLTestClient`),
its "Why it matters" to the `strawberry_django.test.client.TestClient`
subclass — but the base read for this spec has no `mutate()` and neither does
that subclass or graphene's mixin.
A mutation is an operation; it posts through `query()` (the docstring says so,
and every mutation example in [User-facing API](#user-facing-api) does so).
The conflict is recorded in [Risks](#risks-and-open-questions) per the
[`docs/SPECS/NEXT.md`][next] prefer-the-card rule, with the one-line alias as
the named fallback if the maintainer wants the card's wording honored.

Alternatives considered (and rejected):

- **Raw `HttpResponse` return (graphene's flavor).** Rejected: the card
  recommends against it; every consumer then re-decodes the body, and the
  "200 plus an `errors` key" trap returns to every call site.
- **Strawberry's `Response` unmodified (no raw-response field).** Rejected:
  strands status/header/cookie assertions on raw posts and shrinks the
  switchover (above).
- **Two return flavors behind a flag (`raw=True`).** Rejected: the card says
  pick one; a mode flag is both flavors' costs with neither's clarity.
- **A `mutate()` alias for `query()`.** Rejected as scope (no upstream has
  it; an alias that changes nothing invites the false belief it does
  something — e.g. auto-prefixing `mutation`); named as the fallback in
  [Risks](#risks-and-open-questions).

### Decision 7 — Endpoint resolution: the settings key is `TESTING_ENDPOINT`, default `"/graphql/"` — resolving the card's `GRAPHQL_TESTING_ENDPOINT` working name

The project-wide endpoint knob is
`DJANGO_STRAWBERRY_FRAMEWORK["TESTING_ENDPOINT"]`, read through a new
[`conf.py`][conf] accessor `testing_endpoint_setting()` (key constant
`TESTING_ENDPOINT_KEY`, default `"/graphql/"`) — the exact shape of the
existing `conf.py::nested_connection_strategy_setting` precedent. The card's
working name was `GRAPHQL_TESTING_ENDPOINT`, "final name pinned during
implementation"; this spec pins the final name **without** the `GRAPHQL_`
prefix: inside a settings dict named `DJANGO_STRAWBERRY_FRAMEWORK`, every key
is about this package's GraphQL surface, so the prefix is pure redundancy —
and the unprefixed name is byte-identical to graphene's own `TESTING_ENDPOINT`
key, which is the knob's lineage (the card's own "mirrors graphene's
`TESTING_ENDPOINT`" sentence). Existing keys set the style: none carry a
`GRAPHQL_` prefix (`NESTED_CONNECTION_STRATEGY`, `APPLY_UPSTREAM_PATCHES`;
`RELAY_GLOBALID_STRATEGY`'s prefix names the Relay subsystem, not GraphQL).

Resolution precedence, highest first, uniform across the family:

1. **Per-call:** `query(..., url=...)` (on both the pytest client and the
   mixin) — the card's explicitly-named per-call override, honored for that one
   request only and never persisted on the client; `url=None` (default) falls
   through.
2. **Per-instance:** `TestClient(path=...)` / `AsyncTestClient(path=...)` —
   the constructor override, strawberry-django's `path` argument kept
   positional-first so migrant calls work unchanged; `path=None` (the new
   default) falls through.
3. **Per-class (mixin family):** the `GRAPHQL_URL` class attribute
   (graphene's name), default `None` → falls through. A subclass pins its own
   endpoint by assignment, exactly as graphene consumers do today.
4. **Project-wide:** `testing_endpoint_setting()` →
   `DJANGO_STRAWBERRY_FRAMEWORK["TESTING_ENDPOINT"]`.
5. **Default:** `"/graphql/"` — fakeshop's real path, Strawberry core's own
   base default, trailing slash per Django convention (graphene's
   slash-less `"/graphql"` is a documented non-borrow).

The construction-time default (rungs 2–5) is resolved **once** and stored on
the client as `self.path`, matching upstream's constructor-time `path`. The
transport contract is explicit: the concrete `request()` is widened to
`request(body, headers=None, files=None, *, url=None)`, where `url` defaults to
`self.path`; the package-owned `query()` resolves the per-call `url=` (rung 1)
and threads it through as `request(..., url=<resolved>)` for that single call,
without re-reading settings. `self.path` is **never mutated**, so the per-call
override never persists and concurrent or async calls cannot race on shared
state (the reason a `self.path`-mutation shim was rejected). The mixin resolves
rungs 3–5 per `query()` call (it constructs its delegate client lazily against
`self.client`), so a test that overrides settings mid-class still behaves
predictably; [`conf.py`][conf]'s `setting_changed` receiver keeps the accessor
fresh under `override_settings` either way.

No validation beyond [`conf.py`][conf]'s existing malformed-dict guard: a
wrong endpoint string is an ordinary 404 at request time
([Error shapes](#error-shapes)), and validating URL shapes in a test helper
is ceremony.

Alternatives considered (and rejected):

- **`GRAPHQL_TESTING_ENDPOINT` (the card's working name).** Rejected:
  redundant prefix inside the namespaced dict; breaks the graphene name
  parity the card itself cites. The card text explicitly delegates the final
  name ("final name pinned during implementation" — pinned here instead,
  where the alternatives can be recorded).
- **A Django-global settings name (top-level `GRAPHQL_TESTING_ENDPOINT`).**
  Rejected: the package's one settings surface is the
  `DJANGO_STRAWBERRY_FRAMEWORK` dict ([`conf.py`][conf]'s documented
  contract); a second top-level name fragments it.
- **Default `"/graphql"` (graphene's).** Rejected: fakeshop and Strawberry
  both use the trailing slash; a slash-less default would not match that
  `/graphql/` mount — under `APPEND_SLASH` a body-bearing POST raises
  `RuntimeError` in `DEBUG` (or is 301-redirected in a way that drops the
  body), never cleanly reaching the view.
- **Re-reading the settings key on every request.** Rejected: the
  settings-derived default resolves once at construction (upstream's posture);
  the explicit per-call `url=` override (rung 1) covers the legitimate
  per-request need without a settings read per call.
- **Dropping the card's per-call override entirely** (constructor + class
  attribute only). Rejected: the card explicitly names a per-call override
  ("with constructor / per-call override"); honoring it is one keyword-only
  parameter on the package-owned `query()` plus the widened `request(..., *,
  url=None)` transport hook, so there is no cost worth trading the card
  constraint away for.

### Decision 8 — Async shape: `AsyncTestClient` subclasses `TestClient`, ported as-is

The card asks the spec to either port upstream's inheritance shape —
`AsyncTestClient(TestClient)`, taking a `django.test.AsyncClient`, overriding
only `query()` and `login()` — or pick a flatter alternative explicitly.
**Pinned: the port.** The shape is small and honest: `request()` is
sync-*shaped* but returns whatever the wrapped client's `post()` returns — an
awaitable when the wrapped client is `AsyncClient` — so the async `query()`
awaits it (upstream's `cast("Awaitable", ...)` becomes a plain `await` with
the same comment); the package's owned `_build_body`, file-map builder, and the
widened `request(body, headers=None, files=None, *, url=None)` transport hook
are shared with the sync client (the async override re-colors only the awaiting
of the transport, not the body build or the per-call `url=` routing,
[Decision 7](#decision-7--endpoint-resolution-the-settings-key-is-testing_endpoint-default-graphql--resolving-the-cards-graphql_testing_endpoint-working-name));
the async `login()` wraps `force_login` / `logout` in
`sync_to_async` (session writes are ORM work). The package's async `query()`
override is where the [Decision
6](#decision-6--query-returns-the-typed-response-dataclass-extended-with-the-raw-httpresponse-operation_name-is-supported)
`Response` and `operation_name=` land, mirroring the sync override.

`AsyncClient` drives Django's `AsyncClientHandler` in-process, so the async client
works against the WSGI-only fakeshop example without an `asgi.py` — which is
what makes the [Test plan](#test-plan)'s async tests real requests rather
than mocks. It is **not** a Channels transport
([Decision 2](#decision-2--card-scope-boundary-the-test-client-family-ships-channels-session-auth-verification-the-toolbars-async-smoke-and-fakeshop-runtime-changes-stay-out)).

Alternatives considered (and rejected):

- **A flat `AsyncTestClient(BaseGraphQLTestClient)`.** Rejected: it
  re-declares the constructor, `request()`, and `login()` just to avoid an
  is-a relationship that is actually true (the async client IS the sync
  client with an awaited transport).
- **One class with sync/async auto-detection** (the package's
  `is_async_callable` machinery from [`DjangoListField`][glossary-djangolistfield]).
  Rejected: that machinery exists for *consumer-supplied* resolvers whose
  color the package cannot know; here the caller chooses the color explicitly
  by picking the class, and a dual-color `query()` would return
  `Response | Coroutine` — the exact ambiguity the typed helper exists to
  remove.

### Decision 9 — Multipart uploads: `files=` maps variable paths to file parts; the package owns the body/multipart builder; upstream's no-op `format` kwarg is dropped

When `files=` is provided, the package's **owned** `_build_body` produces the
GraphQL multipart request spec envelope — `operations` (the JSON-encoded
`{query, operationName?, variables}` body), `map` (the file-part → variable-path
mapping), plus the file parts — and the package's `request()` posts it
**without** a `content_type` argument, so `django.test.Client.post` falls back
to its default `MULTIPART_CONTENT` encoding, which is what actually turns the
dict into a multipart body.

**The public `files=` contract (pinned here): each key is the variable path
the file binds to.** A key `"data.attachment"` means "the file at
`variables.data.attachment`"; the builder emits a multipart part named
`"data.attachment"` and a `map` entry `{"data.attachment":
["variables.data.attachment"]}`. Every path is one uniform rule —
`map[key] = ["variables." + key]` — so the same builder covers a top-level file
(`"file"` → `variables.file`), a nested input-object field
(`"data.image"` → `variables.data.image`), and a list index
(`"data.files.0"` → `variables.data.files.0`). The caller carries a matching
`None` placeholder at each path inside `variables`
(`variables={"data": {"attachment": None, "image": None}}`), and `_build_body`
enforces this with an explicit `raise AssertionError` guard (not the base's
bare `assert variables is not None`, so it holds under `python -O`).

This builder is **owned, not inherited**, for the reasons pinned in
[Decision 5](#decision-5--subclass-strawberrys-basegraphqltestclient--engine-owned-base-over-a-hard-dependency-no-soft-dependency-machinery)
ground 2: the base's `_build_multipart_file_map` treats a dict-valued variable
as a single "folder", keys off `next(iter(values.keys()))`, and finally drops
any map entry whose key is not itself a `files` key — so it returns an **empty
map** for fakeshop's nested `variables.data.attachment` / `variables.data.image`
shape, and it has **no `operationName` support** (the base's `_build_body`
JSON-encodes `operations` with only `query` / `variables`). Because the public
contract carries the path explicitly, the owned builder is ~15 lines and needs
none of the base's folder-key guessing. `operationName` is injected into the
`operations` body **before** JSON-encoding, so a named upload operation lands
in the right field (the failure mode the base's shape would produce if the name
were appended after wrapping).

The `content_type` omission is a deliberate, documented divergence from
upstream's letter while keeping its behavior: strawberry-django's `request()`
sets `kwargs["format"] = "multipart"` — a **DRF-`APIClient`-shaped kwarg that
Django's own test client does not accept**; it lands in `Client.post(...)`'s
`**extra` and becomes an inert WSGI-environ entry, while the real multipart
switch is (and always was) the *omission* of `content_type`. The package's
`request()` keeps the real mechanism and drops the inert kwarg, with a comment
naming this divergence so a future diff against upstream doesn't "fix" it back
in. (Verified against [`strawberry_django/test/client.py`][upstream-client]
`::TestClient.request` and Django's `Client.post` signature.)

The multipart path is the card's [`DONE-037-0.0.11`][kanban] coupling: live
`Upload`-scalar mutations (fakeshop's `createMediaSpecimen` /
`createItemWithFileViaForm`, the `scalars` app's upload surface) drive through
`query(..., files=...)`, and Slice 2 replaces the hand-built `operations` /
`map` blocks in [`test_uploads_api.py`][test-uploads-api] /
[`test_products_api.py`][test-products-api] accordingly — **including** the
nested two-file (`attachment` + `image`) shape, which the owned builder now
expresses, so it converts rather than staying a wire-shape exemption. The
wire-shape exemption ([Decision 11](#decision-11--test-strategy-the-live-switchover-is-the-primary-coverage-teststestingtest_clientpy-owns-the-rest))
is reserved for tests whose subject IS a *malformed* or hand-crafted envelope,
not for well-formed nested uploads the contract covers.

Alternatives considered (and rejected):

- **Infer file paths from the `variables` structure** (the base's approach —
  walk the dict, guess folders, number lists). Rejected: that heuristic is
  exactly what returns an empty map for nested input objects; an explicit
  path-keyed `files=` is unambiguous, trivially recursive, and self-documents
  where each file lands.
- **Copy `format="multipart"` verbatim.** Rejected: knowingly shipping an
  inert kwarg that implies a DRF client is in play misleads every future
  reader; the borrow is of behavior, not typos.
- **Explicit `content_type=MULTIPART_CONTENT`.** Considered — it states the
  intent — but Django's test client treats the *default* argument specially
  (it encodes the data dict itself only when `content_type` is the default
  sentinel value); passing the constant explicitly is equivalent today but
  couples to the constant's identity. The omission, plus the comment, is the
  documented idiom.

### Decision 10 — Mixin-first: `GraphQLTestMixin` composes over `TestClient`; the graphene assertion helpers keep their names, typed-Response-shaped

The reusable unittest piece is `GraphQLTestMixin` (graphene's convention, the
card's own architectural posture: "consumers with their own custom TestCase
base can compose the mixin in directly"); `GraphQLTestCase` and
`GraphQLTransactionTestCase` are the two-line concrete combinations. The
mixin's surface:

- **`GRAPHQL_URL = None`** — the per-class endpoint override
  ([Decision 7](#decision-7--endpoint-resolution-the-settings-key-is-testing_endpoint-default-graphql--resolving-the-cards-graphql_testing_endpoint-working-name)).
- **`query(query, *, variables=None, operation_name=None, headers=None,
  files=None, url=None, assert_no_errors=False)`** — delegates to a `TestClient`
  constructed over the test case's **own `self.client`** (so `force_login`,
  cookies, and `enforce_csrf_checks` state on the case's client all apply) at
  the resolved class/settings endpoint (rungs 3–5), and forwards the per-call
  `url=` (rung 1) to that client's `query()`, which routes it through the
  widened `request(..., url=...)` hook so it wins over `GRAPHQL_URL` and the
  settings key for that one call without persisting
  ([Decision 7](#decision-7--endpoint-resolution-the-settings-key-is-testing_endpoint-default-graphql--resolving-the-cards-graphql_testing_endpoint-working-name)),
  and returns the typed
  [`Response`](#decision-6--query-returns-the-typed-response-dataclass-extended-with-the-raw-httpresponse-operation_name-is-supported).
  The signature is keyword-only after `query`, so graphene's positional
  `operation_name` (its 2nd positional arg) becomes `operation_name=` — the
  third documented graphene-migration delta ([Out of scope](#out-of-scope-explicitly-tracked-elsewhere)),
  a deliberate trade of graphene positional-call fidelity for one uniform
  keyword signature across the pytest client and the mixin (graphene's own
  positional order `(query, operation_name, input_data, variables, headers)`
  cannot survive dropping `input_data` intact anyway).
  Note the flipped default: **`assert_no_errors=False` on the mixin** —
  graphene's mixin never auto-asserted, and its documented flow is "call
  `self.query(...)`, then `assertResponseNoErrors` / `assertResponseHasErrors`";
  auto-raising `AssertionError` from inside `query()` would break every
  ported `assertResponseHasErrors` test at the call site, before the
  assertion helper runs. The pytest-flavored `TestClient` keeps the base's
  `True` default (strawberry-django parity). The asymmetry is deliberate and
  documented in both docstrings: each flavor defaults to its own upstream's
  behavior.
- **`assertResponseNoErrors(resp, msg=None)`** — asserts
  `resp.response.status_code == 200` **and** `resp.errors is None` (graphene's
  two checks, against the typed shape), failing with the decoded content.
- **`assertResponseHasErrors(resp, msg=None)`** — asserts `resp.errors` is
  non-empty; deliberately no status assertion (graphene's comment kept:
  GraphQL returns 200 with errors).

The mixin owns **no** body-building, decoding, or endpoint logic — that is
the delegate client's, so the logic exists once (the reason graphene's
module-level `graphql_query` free function is a non-borrow).

Alternatives considered (and rejected):

- **Concrete test cases only, no mixin.** Rejected: the card pins mixin-first
  and names the custom-base composition use case.
- **The mixin re-implements the POST (graphene's actual internals).**
  Rejected: two body-builders drift; the delegate costs one object per call
  in test code.
- **Renamed assertion helpers (`assert_no_errors` snake_case).** Rejected:
  the helpers exist for graphene migrants; unittest's own assertion
  vocabulary is camelCase (`assertEqual`), so the graphene names are also the
  idiomatic unittest names.
- **`assert_no_errors=True` on the mixin's `query()` for family-wide
  uniformity.** Rejected: silently breaks the graphene migration's central
  pattern (see above); uniformity of defaults is worth less than both
  migrations working.

### Decision 11 — Test strategy: the live switchover is the primary coverage; `tests/testing/test_client.py` owns the rest

Per the [live-first mandate][glossary-live-first-coverage-mandate], the
helper's happy paths are covered **by being used**: the switchover moves the
live acceptance suites onto it — the coverage-earning subset in Slice 1, the
remainder in Slice 2 — after which every `test_query/` run exercises
`TestClient.query()` (JSON, variables, operation names, login flows,
multipart uploads) against real fakeshop `/graphql/` requests — the strongest
possible form of "the covering test lives in the live tier", since the
covering tests are the package's actual acceptance suites. `tests/testing/test_client.py`
(the card's DoD row) then owns only what the switched suites cannot pin:

- **Endpoint-resolution precedence** (constructor > class attr > settings key
  > default) — the live suites all use the default, so the override ladder
  needs targeted tests (settings via the `pytest-django` `settings` fixture;
  no live suite should ever need a non-default endpoint).
- **Both `assert_no_errors` directions and both mixin assertion helpers'
  failure modes** — a live suite asserts *outcomes*, not the helper's own
  raising behavior.
- **The `AsyncTestClient`** — the live tier is sync (`django.test.Client`
  through WSGI); the async client's real-request tests live here, driving the
  same fakeshop schema through `AsyncClient` / `AsyncClientHandler` (`pytest-asyncio`,
  `asyncio_mode = auto`, `django_db` marking — and the suite's known
  order-dependence hazards around async DB work mean these tests follow the
  [`tests/conftest.py`][tests-conftest] connection-hygiene patterns already
  in place).
- **The unittest family's mechanics** (`GRAPHQL_URL` override, the delegate
  using `self.client`, `GraphQLTransactionTestCase` smoke) — the live suites
  are pytest-function-shaped, not TestCase-shaped.
- **The `__test__ = False` collection guard and the export surface.**

Because these package-tier tests execute real GraphQL through the aggregate
fakeshop schema, the request-driving ones inherit the
[schema-reload][glossary-schema-reload-discipline] obligation (setup-time
`reload_all_project_schemas()`, the [`spec-042`][spec-042] Decision 9
precedent for package tests driving fakeshop requests) and the
[`seed_data`][glossary-seed-data] rule (every product-query test's first
executable line). Pure-mechanics tests (precedence resolution, the collection
guard) stay DB-free and unmarked.

**The switchover's own discipline** (Slices 1–2): each file converts
mechanically — helper deleted, calls rewritten, assertions unchanged — and
the exemption is narrow and commented: a test keeps raw `client.post(...)`
only when the raw envelope is the test's subject (hand-built multipart
negatives, malformed-body tests, content-type probes,
[`test_multi_db.py`][test-multi-db]'s custom-view plumbing). Query-count
assertions (`CaptureQueriesContext`) are re-verified unchanged — the helper
adds no queries. No live test's *assertion* weakens in the conversion; if a
conversion would weaken one, that test takes the exemption instead.

No absence matrix, no eviction fixture, no hint tests — there is no optional
dependency ([Decision 5](#decision-5--subclass-strawberrys-basegraphqltestclient--engine-owned-base-over-a-hard-dependency-no-soft-dependency-machinery)).

Alternatives considered (and rejected):

- **A package-only test suite with the switchover deferred.** Rejected: the
  card's DoD names the switchover, and without it the package tests would
  duplicate live coverage the mandate says belongs in the live tier —
  the exact "package-only stand-in" pattern the
  [live-first promotion rule][glossary-live-first-coverage-mandate] exists to
  retire.
- **Switch only one representative live file.** Rejected: the DoD says "live
  HTTP tests ... switch to the helper", plural; a partial switchover leaves
  two idioms in the tree indefinitely, which is worse for readers than
  either.
- **Mock-based unit tests for `request()`.** Rejected: real fakeshop requests
  are available in-process ([`pytest.ini`][pytest-ini] runs the suite against
  fakeshop settings); mock only when the real path is impossible.

### Decision 12 — Version bumps are owned by the joint `0.0.14` cut

No slice in this card edits the package-version state: `[project].version` in
[`pyproject.toml`][pyproject], `__version__` in [`__init__.py`][init], or
[`tests/base/test_init.py::test_version`][test-base-init]. This card **shares
the `0.0.14` patch line** with one open sibling —
[`TODO-ALPHA-044-0.0.14`][kanban] — and two landed predecessors,
[`DONE-041-0.0.14`][kanban] and [`DONE-042-0.0.14`][kanban], whose specs'
Decision 10 already deferred the bump to the **[joint `0.0.14`
cut][glossary-joint-version-cut]** (the last `0.0.14` card to land). The
release-status wording splits the same way: Slice 3 updates
**implemented-on-main** docs (the GLOSSARY entry bodies, the regenerated
[`docs/TREE.md`][tree]) but the public `shipped (0.0.14)` status flips, the
[`README.md`][readme] / [`docs/README.md`][docs-readme] "Coming next" →
"Shipped today" moves, and the `CHANGELOG.md` bullets defer to the joint cut.

Unlike [`spec-041`][spec-041] / [`spec-042`][spec-042], this card does not
touch `uv.lock` at all — there is no dependency to add
([Decision 5](#decision-5--subclass-strawberrys-basegraphqltestclient--engine-owned-base-over-a-hard-dependency-no-soft-dependency-machinery))
— so the lockfile-vs-version reconciliation those specs pinned has no
instance here.

Justification: per [`docs/SPECS/NEXT.md`][next] Step 3 / Step 6, when multiple
cards target one patch version the bump belongs to the joint cut, not any
individual card's spec. At authoring time one other non-Done card
([`TODO-ALPHA-044-0.0.14`][kanban]) sits at `0.0.14` beside this one; whichever
`0.0.14` card lands last owns the version quintet.

Alternatives considered (and rejected):

- **Bump to `0.0.14` in Slice 3.** Rejected: the open sibling (and this card)
  still ship into `0.0.14`; a per-card bump races the joint cut and would be
  reconciled twice over.

## Implementation plan

The file-level delta map for the build handoff (each row's contract is
specified in the decisions cited; **no slice bumps the version** — the joint
`0.0.14` cut owns it,
[Decision 12](#decision-12--version-bumps-are-owned-by-the-joint-0014-cut)):

| File | Change | Slice |
| --- | --- | --- |
| [`django_strawberry_framework/conf.py`][conf] | `TESTING_ENDPOINT_KEY` constant + `testing_endpoint_setting()` accessor, default `"/graphql/"` ([Decision 7](#decision-7--endpoint-resolution-the-settings-key-is-testing_endpoint-default-graphql--resolving-the-cards-graphql_testing_endpoint-working-name)) | 1 |
| `django_strawberry_framework/testing/client.py` (new) | `Response` (typed + raw response); `TestClient(BaseGraphQLTestClient)` with `__test__ = False`, endpoint resolution, owned `_build_body` + path-keyed file-map builder, `request(..., *, url=None)` (JSON / multipart), owned `query()` (`operation_name=`, per-call `url=` via `request(url=)`, package `Response`), `login()`; `AsyncTestClient(TestClient)`; `GraphQLTestMixin` + `GraphQLTestCase` + `GraphQLTransactionTestCase` ([Decisions 3](#decision-3--the-symbols-are-upstreams-own-names--testclient--asynctestclient--graphqltestmixin--graphqltestcase--graphqltransactiontestcase-distinctly-ours-import-path)–[10](#decision-10--mixin-first-graphqltestmixin-composes-over-testclient-the-graphene-assertion-helpers-keep-their-names-typed-response-shaped)) | 1 |
| [`django_strawberry_framework/testing/__init__.py`][testing-init] | Re-export the six public names; extend `__all__`; docstring's "Future exports" block resolved to current exports ([Decision 4](#decision-4--module-export-and-test-locations-testingclientpy-re-exported-from-the-testing-root-teststestingtest_clientpy)) | 1 |
| `tests/testing/test_client.py` (new) | The package-tier scenarios per the [Test plan](#test-plan) — the `assert_no_errors=True` raising direction + mixin failure modes, the `files=`/`variables=None` guard, endpoint precedence, the async client, the unittest family, and the surface guards (request-shape scenarios 1–5 are earned live, not here) | 1 |
| `examples/fakeshop/test_query/*.py` (targeted subset) | Slice-1 live coverage: convert the cases that earn the sync request-shape lines (JSON, errors outcome, `operation_name`, `login`, multipart) onto `TestClient`; assertions unchanged, query-counts re-verified | 1 |
| `examples/fakeshop/test_query/*.py` (remainder) | Slice-2 switchover: remaining per-file post helpers deleted, calls moved to `TestClient` / the mixin; wire-shape exemptions commented; query-count assertions re-verified ([Decision 11](#decision-11--test-strategy-the-live-switchover-is-the-primary-coverage-teststestingtest_clientpy-owns-the-rest)) | 2 |
| [`docs/GLOSSARY.md`][glossary] | [`TestClient`][glossary-testclient] + [`GraphQLTestCase`][glossary-graphqltestcase] entry bodies to implemented contract; [Auth mutations][glossary-auth-mutations] Channels sentence resolved to the follow-on; status flips deferred | 3 |
| [`docs/TREE.md`][tree] | Regenerated (script-rendered) after the card flips Done | 3 |
| [`KANBAN.md`][kanban] / `KANBAN.html` | Card wrap via DB edit + re-render | 3 |

## Helper-reuse obligations (DRY)

Reuse is named per item, and deliberate *non*-reuse carries its reason (the
[`spec-041`][spec-041] / [`spec-042`][spec-042] discipline).

- [ ] **D1** — the response decode, the `Response` field schema, and the
  `request()` ABC seam ride Strawberry's `BaseGraphQLTestClient`
  (`_decode`, the `Response` base, the abstract `request()`) — never
  re-implemented
  ([Decision 5](#decision-5--subclass-strawberrys-basegraphqltestclient--engine-owned-base-over-a-hard-dependency-no-soft-dependency-machinery)).
  The sync **and** async `query()` orchestration (its signature and return type
  both change) and the body/file-map build are the **owned** exceptions
  (D-N4 below covers the builder).
- [ ] **D2** — the settings accessor follows the
  [`conf.py`][conf] key-constant + thin-accessor precedent
  (`conf.py::nested_connection_strategy_setting`); no new settings-reading
  pattern
  ([Decision 7](#decision-7--endpoint-resolution-the-settings-key-is-testing_endpoint-default-graphql--resolving-the-cards-graphql_testing_endpoint-working-name)).
- [ ] **D3** — the mixin delegates to `TestClient`; there is exactly one
  body-builder and one decoder in the package
  ([Decision 10](#decision-10--mixin-first-graphqltestmixin-composes-over-testclient-the-graphene-assertion-helpers-keep-their-names-typed-response-shaped)).
- [ ] **D4** — the request-driving package tests reuse the single-sited
  [`schema_reload.reload_all_project_schemas()`][schema-reload] and
  [`seed_data`][glossary-seed-data] helpers — never private reload or
  hand-built catalog rows
  ([Decision 11](#decision-11--test-strategy-the-live-switchover-is-the-primary-coverage-teststestingtest_clientpy-owns-the-rest)).
- [ ] **D-N1** (non-reuse) — the client does **not** route through
  [`request_from_info`][glossary-request-from-info]: that helper decodes
  resolver-context shapes server-side; this module never sees a resolver
  context — it *originates* HTTP requests from the test process.
- [ ] **D-N2** (non-reuse) — no shared "GraphQL post" helper is factored into
  `utils/`: the surface is consumer-facing test API under `testing/`, not a
  cross-subsystem substrate, and no package runtime module may import test
  utilities.
- [ ] **D-N3** (non-reuse) — the async client does not reuse the
  `is_async_callable` construction-time detection from
  [`DjangoListField`][glossary-djangolistfield]: the caller picks the color
  by class here; detection machinery exists for consumer-supplied callables
  whose color the package cannot know
  ([Decision 8](#decision-8--async-shape-asynctestclient-subclasses-testclient-ported-as-is)).
- [ ] **D-N4** (non-reuse) — the body build and multipart file map do **not**
  reuse the base's `_build_body` / `_build_multipart_file_map`: the base's
  builder returns an empty map for nested input-object uploads and carries no
  `operationName`, so the package owns a ~15-line path-keyed builder instead.
  This is a *deliberate* non-reuse of an engine internal (unlike D1's reuse of
  `_decode` / `Response`), justified by the base's insufficiency, not by
  preference
  ([Decision 5](#decision-5--subclass-strawberrys-basegraphqltestclient--engine-owned-base-over-a-hard-dependency-no-soft-dependency-machinery)
  ground 2,
  [Decision 9](#decision-9--multipart-uploads-files-maps-variable-paths-to-file-parts-the-package-owns-the-bodymultipart-builder-upstreams-no-op-format-kwarg-is-dropped)).

## Edge cases and constraints

- **`__test__ = False` on `TestClient` / `AsyncTestClient`.** Without it,
  pytest collects any imported name matching `Test*` as a suite and emits
  `PytestCollectionWarning` — which the repo's `-W error` posture turns into
  a hard failure the moment a test module imports the class. Upstream carries
  the same guard; the package must not drop it, and the [Test plan](#test-plan)
  pins it (Test 13). The mixin family needs no guard (`GraphQL*` names do not
  match pytest's collection patterns).
- **CSRF.** `django.test.Client(enforce_csrf_checks=False)` is Django's
  default, so the helper posts without a token even though fakeshop's
  `/graphql/` view is `ensure_csrf_cookie`-wrapped. A consumer testing CSRF
  enforcement passes their own `TestClient(client=Client(enforce_csrf_checks=True))`
  — the constructor's `client=` seam exists for exactly this.
- **Session state and cookies.** `login()` covers the force-login block; for
  cookie/session assertions the raw client rides along
  (`test_client.client.cookies`, and `res.response.cookies` per response) —
  the live auth suite ([`test_auth_api.py`][test-auth-api]) asserts session
  cookies across a login round trip and switches over using these seams.
- **`files=` requires placeholder variables.** The owned `_build_body` guards
  this with an explicit `raise AssertionError` when `files` is passed with
  `variables=None` (not the base's bare `assert`, so it holds under
  `python -O`), and the path-keyed `files=` contract requires a `None`
  placeholder at each file's variable path. Documented in the `query()` docstring with the canonical
  single-file and nested-input-object examples
  ([Decision 9](#decision-9--multipart-uploads-files-maps-variable-paths-to-file-parts-the-package-owns-the-bodymultipart-builder-upstreams-no-op-format-kwarg-is-dropped)).
- **Multi-file, nested-input-object, and list uploads** are handled by the
  owned path-keyed builder — `files={"data.attachment": f1, "data.image": f2}`
  for a nested input object, `files={"tags.0": f1, "tags.1": f2}` for a list —
  one uniform `map[key] = ["variables." + key]` rule. This is the surface the
  base could **not** express (its folder heuristic returns an empty map for
  nested objects), which is why the package owns the builder
  ([Decision 5](#decision-5--subclass-strawberrys-basegraphqltestclient--engine-owned-base-over-a-hard-dependency-no-soft-dependency-machinery)
  ground 2).
- **GET is not supported.** Both upstreams' helpers POST unconditionally;
  queries-via-GET (persisted-query CDNs, the debug-toolbar spec's
  `Accept: application/json` GET test) stay on the raw client — one of the
  named wire-shape exemptions in the switchover.
- **`headers=` passes through** to Django's `Client.post(headers=...)`
  (Django ≥ 4.2 shape; the package floor is `Django>=5.2`, so no
  `HTTP_`-prefixed-extra fallback is carried — graphene's version shim is a
  non-borrow by obsolescence).
- **The raw-response field under multipart decode.** `_decode` reads
  `response.content` directly for multipart posts (upstream behavior); the
  package `Response.response` carries the same `HttpResponse` either way, so
  status/header assertions are uniform across JSON and multipart calls.
- **`AsyncTestClient` + the ORM.** Async tests touching the database mark
  `django_db` and run through Django's async-safety machinery
  (`sync_to_async` inside the ORM); the suite's existing async-connection
  hygiene ([`tests/conftest.py`][tests-conftest]'s leaked-async-connection
  handling) applies to these tests as to every other async DB test — no new
  mechanism, but the [Test plan](#test-plan) notes the marking so the
  known order-dependence class never enters through this file.
- **`operationName` is omitted, never `null`.** The body carries the key only
  when `operation_name` is provided — a `null` `operationName` against a
  multi-operation document is a GraphQL validation error, and an absent key
  against a single anonymous operation is the spec-correct shape (the
  [`spec-042`][spec-042] Test-3 lesson, encoded in the builder).
- **`Response` equality/reprs.** The dataclass carries a live `HttpResponse`;
  reprs stay readable (dataclass default) and no test should compare whole
  `Response` objects — the [Test plan](#test-plan) asserts fields, and the
  docstring says to.
- **Mixin on a custom TestCase base.** The mixin reads only `self.client`
  (Django's `TestCase` provides it) and its own class attributes; composing
  it over a consumer's custom base works exactly as graphene documents —
  the mixin is deliberately state-free beyond `GRAPHQL_URL`.

## Test plan

The numbered scenarios below are the behaviours this card must prove; they
split across two tiers per
[Decision 11](#decision-11--test-strategy-the-live-switchover-is-the-primary-coverage-teststestingtest_clientpy-owns-the-rest).
The **sync request-shape scenarios (1–5)** are reachable as ordinary GraphQL
calls, so — per the [live-first mandate][glossary-live-first-coverage-mandate] —
they are earned **live**, by converting the matching
[`examples/fakeshop/test_query/`][test-query-readme] cases onto `TestClient` in
Slice 1 (the Slice-2 switchover then converts the rest); they are **not**
restated as package-tier tests. Only the assertions a live request cannot pin —
the `assert_no_errors=True` raising direction and the `files=`/`variables=None`
guard that scenarios 2 and 5 also carry — live in
`tests/testing/test_client.py`, alongside everything in scenarios 6–14
(endpoint precedence, the async client, the unittest family, the surface
guards). Request-driving tests (the live conversions, and the package-tier
async / unittest cases) call
[`schema_reload.reload_all_project_schemas()`][schema-reload] on setup (fixture,
before any request) and mark `django_db`; product-query tests start with
[`seed_data(1)`][glossary-seed-data]. Mechanics tests (endpoint precedence,
collection guard, exports) are DB-free and unmarked.

**Sync request shapes (scenarios 1–5) — earned live in Slice 1 (converted
`test_query/` cases), not package-tier tests:**

1. **Happy path.** `seed_data(1)`, `TestClient().query(<named allItems
   query>, variables={"first": 1})` → `res.errors is None`, `res.data`
   carries edges, `res.extensions` is the decoded value (or `None`),
   `res.response.status_code == 200` and
   `res.response["Content-Type"].startswith("application/json")` — the typed
   shape and the raw ride-along in one assertion set.
2. **Errors, both directions.** An invalid selection with
   `assert_no_errors=False` returns `res.errors` non-empty with `res.data`
   `None` — earned live. The raising direction (the same call under the default
   `assert_no_errors=True` raises `AssertionError`, via `pytest.raises`, its
   message carrying the errors list) is the helper's own behaviour, pinned
   package-tier in `tests/testing/test_client.py`.
3. **`operation_name` dispatch.** A two-operation document
   (`query A { ... } query B { ... }`) with `operation_name="B"` executes B
   (assert on a B-only field); the same document with no `operation_name`
   fails GraphQL-side (errors present) — proving the key is sent when given
   and *absent* when not (never `null`).
4. **`login()` scoping.** `seed_data(1)`, a write-auth-gated products
   mutation: denied anonymous (top-level error), succeeds inside
   `with client.login(user_with_perm):`, denied again after the block —
   the force-login/logout bracket proven on the same client instance.
5. **Multipart upload — nested input object, two files, with
   `operation_name`.** The live `createMediaSpecimen` mutation through
   `query(mutation, variables={"data": {"label": ..., "attachment": None,
   "image": None}}, files={"data.attachment": SimpleUploadedFile(...),
   "data.image": SimpleUploadedFile(...)}, operation_name="Create")` → success
   payload, both files persisted — the exact nested two-field shape the base's
   `_build_multipart_file_map` **cannot** produce (it returns an empty map),
   proving the owned path-keyed builder and that `operationName` rides inside
   `operations` under multipart wrapping
   ([Decision 9](#decision-9--multipart-uploads-files-maps-variable-paths-to-file-parts-the-package-owns-the-bodymultipart-builder-upstreams-no-op-format-kwarg-is-dropped)).
   This is the [`DONE-037`][kanban] coupling discharged through the helper — a
   live fakeshop nested upload with two file fields combined with a named
   operation, the case that proves the owned builder is load-bearing. Plus the
   guard direction — `files=` with `variables=None` raises `AssertionError`
   from the owned `_build_body`'s explicit guard — is the helper's own
   behaviour, pinned package-tier in `tests/testing/test_client.py`. A top-level
   single-file upload (`files={"file": f}`) rounds out the shape coverage.

**Endpoint resolution (mechanics, DB-free):**

6. **Default.** `TestClient().path == "/graphql/"` with no settings key.
7. **Settings key.** Under the `pytest-django` `settings` fixture setting
   `DJANGO_STRAWBERRY_FRAMEWORK = {"TESTING_ENDPOINT": "/alt/"}`, a fresh
   `TestClient().path == "/alt/"` — and the [`conf.py`][conf]
   `setting_changed` receiver restores the default after the fixture exits
   (assert in a follow-up test or via a second client post-override).
8. **Precedence ladder.** `TestClient("/explicit/").path == "/explicit/"`
   even with the settings key set (constructor > settings > default), and a
   per-call `query(..., url="/percall/")` routes to `/percall/` even on a client
   constructed with a different `path` — the per-call rung (rung 1) pinned as
   overriding the constructor. Because this is a **DB-free mechanics** test of
   *target selection* (not of a live view), the per-call routing is proven
   without a request: a tiny in-file `TestClient` subclass overrides
   `request(self, body, headers=None, files=None, *, url=None)` to record the
   effective `url` it receives and return a canned `HttpResponse`, and the test
   asserts the recorded `url == "/percall/"` while `self.path` is **unchanged**
   afterward (the non-persistence guarantee, [Decision 7](#decision-7--endpoint-resolution-the-settings-key-is-testing_endpoint-default-graphql--resolving-the-cards-graphql_testing_endpoint-working-name)).
   Recording the transport target directly means the test cannot accidentally
   pass on a `/percall/` 404 or non-JSON body. Pinned in one parametrized test;
   the mixin's class-attribute and per-call rungs are Test 11's (proven
   end-to-end against a probe URLconf).

**The async client (real requests through `AsyncClientHandler`; `django_db` +
`pytest-asyncio` auto mode):**

9. **Async happy path.** `seed_data(1)` (sync fixture), then
   `await AsyncTestClient().query(...)` → same typed-shape assertions as
   Test 1 — proving the awaited `request()`, the async decode, and the
   package `Response` construction.
10. **Async `login()`.** The Test-4 bracket through
    `async with client.login(user):` — `sync_to_async`-wrapped session
    round trip.

**The unittest family (TestCase-shaped, in-file subclasses):**

11. **`GraphQLTestCase` end-to-end.** An in-file subclass runs a seeded query
    via `self.query(...)`, `assertResponseNoErrors` passes; an invalid query
    via `self.query(...)` (no raise — the mixin's `assert_no_errors=False`
    default) then `assertResponseHasErrors` passes; and the two remaining
    precedence rungs (Test 8's deferral) — a `GRAPHQL_URL = "/alt/"` subclass
    and a per-call `self.query(..., url="/alt/")` — both route to the alternate
    endpoint, verified against a **probe URLconf** that maps `"/alt/"` to the
    same schema view (a positive hit on the real view, not an exception shape).
    If a *miss* is asserted anywhere in the endpoint tests instead, it is
    Django's `ValueError` from `response.json()` on the non-JSON 404 body — not
    `json.JSONDecodeError` ([Error shapes](#error-shapes)).
12. **Assertion-helper failure directions.** `assertResponseNoErrors` fails
    (with the decoded content in the message) on an errors response;
    `assertResponseHasErrors` fails on a clean one; plus a
    `GraphQLTransactionTestCase` smoke (one clean query) proving the second
    concrete combination is wired.

**Surface guards (DB-free):**

13. **Collection guard.** `TestClient.__test__ is False` and
    `AsyncTestClient.__test__ is False` — the pytest-collection contract
    ([Edge cases](#edge-cases-and-constraints)) pinned mechanically.
14. **Export surface.** The six names import from
    `django_strawberry_framework.testing` and appear in its `__all__`; the
    no-package-root-export contract is pinned by its **two accurate shapes** —
    `not hasattr(django_strawberry_framework, "TestClient")` (and
    `pytest.raises(AttributeError)` around `getattr(...)`), plus
    `pytest.raises(ImportError)` around `from django_strawberry_framework import
    TestClient` (the statement form, which the import machinery raises as
    `ImportError`, not `AttributeError`)
    ([Decision 4](#decision-4--module-export-and-test-locations-testingclientpy-re-exported-from-the-testing-root-teststestingtest_clientpy)).

**The remaining live switchover (Slice 2) — verification, not new tests:** every
converted file passes with assertions unchanged; `CaptureQueriesContext`
counts unchanged; each retained raw `client.post(...)` carries the
wire-shape-exemption comment. The implementation worker **records the exact
pytest commands** (e.g. `uv run pytest tests/testing/test_client.py` and the
converted `test_query/` files) for the maintainer to run, and does not run
the suite itself unless the maintainer explicitly authorizes pytest for the
slice — the [`AGENTS.md`][agents] #"Do not run pytest" workflow rule; this
spec describes the verification but does not override it.

Coverage: the package gate is `fail_under = 100` and `testing/client.py` is
package code — every branch has a named owner. Reached by the request-driving
tests (1–5, 9–12): the JSON and multipart `request()` branches, both `query()`
overrides, `login()` both colors, the mixin delegate and both assertion
helpers. Reached by the mechanics tests (6–8, 13–14): the endpoint ladder and
the export/guard surface. If implementation finds a branch unreachable
through these (e.g. a defensive re-raise), it gets its own targeted unit the
same way — named owner, never a blanket claim.

## Doc updates

Slice 3 — implemented-on-main docs update here; release-status wording defers
to the joint `0.0.14` cut
([Decision 12](#decision-12--version-bumps-are-owned-by-the-joint-0014-cut)):

- [`docs/GLOSSARY.md`][glossary] — the [`TestClient`][glossary-testclient]
  entry body grows the implemented contract: the
  `django_strawberry_framework.testing` import path, the
  `BaseGraphQLTestClient` inheritance and zero-dependency posture, the typed
  `Response` (+ raw `response` field), endpoint resolution
  (`TESTING_ENDPOINT`, constructor, default `"/graphql/"`), `operation_name=`,
  multipart `files=`, `login()`, and the async twin's `AsyncClientHandler` (not
  Channels) transport. The [`GraphQLTestCase`][glossary-graphqltestcase]
  entry body grows the mixin-first family shape, the flipped
  `assert_no_errors` default, the assertion helpers' typed-Response
  signatures, and the `GRAPHQL_URL` rung. The
  [Auth mutations][glossary-auth-mutations] entry's "scoped to the
  `TestClient` card (`TODO-ALPHA-043-0.0.14`) or a dedicated follow-on card"
  sentence is resolved to the follow-on (this card shipped HTTP-client
  helpers only). Statuses **stay `planned for 0.0.14`** until the joint cut.
- [`docs/TREE.md`][tree] — regenerated via
  [`scripts/build_tree_md.py`][build-tree-md] after the card flips Done (the
  file is script-rendered; missing module docstrings fail the render): the
  package tree's planned `testing/client.py` annotation resolves to the real
  docstring-derived row; the test tree gains `tests/testing/test_client.py`.
- [`KANBAN.md`][kanban] / `KANBAN.html` — card wrap via the DB + re-render
  (Slice 3 checklist).
- **Deferred to the joint cut:** [`README.md`][readme] /
  [`docs/README.md`][docs-readme] "Coming next — remaining alpha (`0.0.14`)" →
  "Shipped today" moves, the GLOSSARY status flips + package-version line,
  [`TODAY.md`][today]'s coming-next wording, and `CHANGELOG.md` (which
  additionally requires the explicit maintainer grant per
  [`AGENTS.md`][agents]).

## Risks and open questions

- **The card's `.query()` / `.mutate()` claim vs. the read source.** The
  card claims a `.mutate()` surface in two sections: "Verified in upstream"
  attributes `.query(...)` / `.mutate(...)` to the upstream
  `BaseGraphQLTestClient`, and "Why it matters" attributes them to the
  `strawberry_django.test.client.TestClient` subclass. The base class read
  for this spec ([`strawberry/test/client.py`][venv-strawberry-test-client],
  installed 0.316.0) defines `query()` only — no `mutate()` exists there, in
  strawberry-django's subclass, or in graphene's mixin. Recorded per the
  [`docs/SPECS/NEXT.md`][next] prefer-the-card rule rather than silently
  reconciled — but on a *factual claim about upstream source*, the source
  wins, so **preferred answer:** ship no `mutate()`
  ([Decision 6](#decision-6--query-returns-the-typed-response-dataclass-extended-with-the-raw-httpresponse-operation_name-is-supported));
  mutations post through `query()`, docstring-documented. **Fallback:** if
  the maintainer wants the card's wording honored literally, `mutate = query`
  as a documented alias is a one-line follow-up — deliberately not shipped
  by default (an alias implies a behavioral difference that does not exist).
- **`BaseGraphQLTestClient` presence and shape at the Strawberry floor.**
  Verified at the installed 0.316.0; the Slice-1 gate re-confirms
  importability (and the `Response` field names) at the pinned
  `strawberry-graphql==0.262.0` floor in a throwaway venv. **Preferred
  answer:** present and shape-stable (the class long predates the floor).
  **Fallback:** bump the project's Strawberry floor — the same recourse
  [`spec-041`][spec-041] / [`spec-042`][spec-042] named for their engine
  gates.
- **Upstream reshapes the base later.** The subclass couples to `_decode` and
  the `Response` field names — private-ish machinery upstream could reshape in a
  future release (the [`spec-042`][spec-042] `_postprocess` risk class, milder:
  `query()` and `Response` are documented public test API upstream). The body
  build the package already **owns**, so a reshape of `_build_body` /
  `_build_multipart_file_map` upstream cannot break the package (a narrower
  coupling surface than a full inherit). **Preferred posture:** accept the
  remaining coupling; the request-driving tests fail loudly under a refreshed
  lock and the fix tracks upstream's change. **Fallback:** pin the reshaped
  pieces locally — `_decode` is small enough to own too if it ever moves.
- **The switchover's breadth.** Slice 2 touches every live file; the risk is
  a conversion that silently weakens an assertion (a dropped status check, a
  loosened multipart shape). **Preferred answer:** the Decision 11 rule —
  assertions unchanged or the test takes the wire-shape exemption — plus the
  raw `response` field existing precisely so no assertion *needs* weakening;
  the maintainer's diff review is the gate ([`AGENTS.md`][agents] commit
  discipline). **Fallback:** any file whose conversion proves contentious
  stays unconverted with the exemption comment; the DoD's "switch to the
  helper" is satisfied by the suites whose helpers the client's contract
  covers, with the exemption list visible in the diff.
- **Async DB tests joining a suite with known async-connection hazards.**
  The repo has history with lingering executor-thread sqlite connections
  under async tests. **Preferred answer:** the `AsyncTestClient` tests mark
  `django_db`, follow [`tests/conftest.py`][tests-conftest]'s existing
  hygiene, and stay few (two tests — the client is transport, not ORM
  machinery). **Fallback:** if a flake surfaces, it is fixed at source in the
  shared conftest (never by weakening `-W error`), the repo's established
  posture.
- **The debug-toolbar async handoff.** [`spec-042`][spec-042]'s Risks point
  at `AsyncTestClient` as the natural owner of the toolbar's async smoke.
  **Preferred answer for `0.0.14`:** the vehicle ships here; with 042 now
  landed without the smoke, it is a small follow-on inside the toolbar card's
  now-landed test module (or the joint cut), where its soft-dependency fixture
  already lives
  ([Decision 2](#decision-2--card-scope-boundary-the-test-client-family-ships-channels-session-auth-verification-the-toolbars-async-smoke-and-fakeshop-runtime-changes-stay-out)).
  **Fallback:** if the joint cut wants it bundled here after all, it is one
  test reusing spec-042's fixture — an addition, not a redesign.
- **The mixin's flipped `assert_no_errors=False` default.** Two defaults in
  one family is a documented asymmetry
  ([Decision 10](#decision-10--mixin-first-graphqltestmixin-composes-over-testclient-the-graphene-assertion-helpers-keep-their-names-typed-response-shaped))
  and a foreseeable confusion source. **Preferred answer:** each flavor
  matches its own upstream's behavior (the property that makes both
  migrations work unchanged); both docstrings state the other's default.
  **Fallback:** if real-world confusion outweighs migration fidelity, a
  future minor can align the mixin to `True` — a deliberate breaking change
  for graphene-ported error tests, acceptable only pre-`1.0.0`.

## Out of scope (explicitly tracked elsewhere)

- **Channels session-auth verification** (session-mutating
  [auth mutations][glossary-auth-mutations] through Channels consumers) — a
  dedicated follow-on card, per
  [Decision 2](#decision-2--card-scope-boundary-the-test-client-family-ships-channels-session-auth-verification-the-toolbars-async-smoke-and-fakeshop-runtime-changes-stay-out);
  Slice 3 resolves the glossary's disjunction wording.
- **The debug-toolbar async smoke test** — a follow-on to
  [`DONE-042-0.0.14`][kanban] (its now-landed test module) or the joint cut;
  this card ships the vehicle only.
- **Response-extensions debug middleware** — the sibling
  [`TODO-ALPHA-044-0.0.14`][kanban]; when its tests want HTTP ergonomics,
  the helper is available to them like any other suite.
- **The migration guide itself** — [`TODO-BETA-056-0.1.6`][kanban]; this card
  hands it two import-diff rows
  (`strawberry_django.test.client.TestClient` →
  `django_strawberry_framework.testing.TestClient`;
  `graphene_django.utils.testing.GraphQLTestCase` →
  `django_strawberry_framework.testing.GraphQLTestCase`) plus the three
  documented deltas: (1) the mixin's `query()` returns the typed `Response`,
  not a raw `HttpResponse`; (2) graphene's `input_data=` kwarg is not carried —
  write `variables={"input": ...}`; (3) the mixin's `query()` is keyword-only
  after the query string, so graphene's positional `operation_name` (its 2nd
  positional arg) becomes `operation_name=`.
- **The `0.0.14` version bump and release-status flips** — the joint
  `0.0.14` cut
  ([Decision 12](#decision-12--version-bumps-are-owned-by-the-joint-0014-cut)).

## Definition of done

- [ ] `django_strawberry_framework/testing/client.py` exists, with module +
      symbol docstrings, exposing `TestClient` / `AsyncTestClient` (both
      `__test__ = False`, subclassing `strawberry.test.BaseGraphQLTestClient`
      per
      [Decision 5](#decision-5--subclass-strawberrys-basegraphqltestclient--engine-owned-base-over-a-hard-dependency-no-soft-dependency-machinery)),
      the package `Response` carrying the raw `HttpResponse`, `login()` both
      colors, `GraphQLTestMixin`, and the two concrete `(Mixin, TestCase)` /
      `(Mixin, TransactionTestCase)` combinations — the card's DoD rows 1–2,
      sharpened by
      [Decisions 6](#decision-6--query-returns-the-typed-response-dataclass-extended-with-the-raw-httpresponse-operation_name-is-supported)
      and [10](#decision-10--mixin-first-graphqltestmixin-composes-over-testclient-the-graphene-assertion-helpers-keep-their-names-typed-response-shaped).
- [ ] The mixin carries `assertResponseNoErrors` / `assertResponseHasErrors`
      named for the typed `Response` (the card's "or the equivalent named for
      the chosen `.query()` return type" — the names kept, the parameter
      typed).
- [ ] The endpoint settings key is live:
      `DJANGO_STRAWBERRY_FRAMEWORK["TESTING_ENDPOINT"]` (the card's
      `GRAPHQL_TESTING_ENDPOINT` working name resolved per
      [Decision 7](#decision-7--endpoint-resolution-the-settings-key-is-testing_endpoint-default-graphql--resolving-the-cards-graphql_testing_endpoint-working-name)),
      default `"/graphql/"`, with the constructor (`path=`), class-attribute
      (`GRAPHQL_URL`), and per-call (`url=`, the card's named per-call override)
      rungs and the full precedence ladder tested.
- [ ] Multipart file upload works through `query(..., files=...)` on both
      clients — a live `Upload`-scalar mutation drives through the helper
      (the card's `DONE-037-0.0.11` coupling), and the `variables`-placeholder
      contract is documented.
- [ ] `from django_strawberry_framework.testing import TestClient,
      AsyncTestClient, Response, GraphQLTestMixin, GraphQLTestCase,
      GraphQLTransactionTestCase` all resolve; nothing is added to the
      package root
      ([Decision 4](#decision-4--module-export-and-test-locations-testingclientpy-re-exported-from-the-testing-root-teststestingtest_clientpy)).
- [ ] **No new dependencies**: `[project].dependencies`,
      `[dependency-groups].dev`, and `uv.lock` are untouched; the Strawberry
      test-module gate ran (`strawberry.test.BaseGraphQLTestClient`
      importable at `strawberry-graphql==0.262.0` in an isolated throwaway
      venv, never the shared `.venv`), or the project's Strawberry floor was
      bumped instead; the command and outcome are recorded in the build
      artifact.
- [ ] `tests/testing/test_client.py` covers the package-tier scenarios per the
      [Test plan](#test-plan) (the raising/guard directions, precedence, the
      async client, the unittest family, the surface guards — scenarios 1–5 are
      earned live, not here) — async tests through `AsyncClient`, the async /
      unittest request-driving tests under the schema-reload + `seed_data`
      disciplines and `django_db` marking, mechanics tests DB-free — and the
      package coverage gate (`fail_under = 100`) holds with `testing/client.py`
      included, each branch mapped to a named owner.
- [ ] The Slice-1 targeted live conversions landed: the
      `examples/fakeshop/test_query/` cases that earn the sync request-shape
      lines (JSON, errors outcome, `operation_name`, `login`, multipart) run
      through `TestClient` with assertions and `CaptureQueriesContext` counts
      unchanged.
- [ ] The Slice-2 remaining switchover landed: the rest of
      `examples/fakeshop/test_query/` uses the helper; per-file post helpers
      are deleted; every retained raw `client.post(...)` carries the
      wire-shape-exemption comment; all assertions and `CaptureQueriesContext`
      counts unchanged (the card's "live HTTP tests switch to the helper" DoD,
      scoped per
      [Decision 11](#decision-11--test-strategy-the-live-switchover-is-the-primary-coverage-teststestingtest_clientpy-owns-the-rest)).
- [ ] The migration-guide handoff rows are recorded for
      [`TODO-BETA-056-0.1.6`][kanban] (the two import diffs + the three
      documented deltas) ([Out of scope](#out-of-scope-explicitly-tracked-elsewhere)).
- [ ] Slice 3 doc updates land per [Doc updates](#doc-updates): both GLOSSARY
      entry bodies (status flips deferred), the auth entry's Channels
      sentence resolved, the regenerated [`docs/TREE.md`][tree], and the
      kanban card wrap (DB edit + re-render).
- [ ] **No slice bumps the version** — `pyproject.toml` / `__version__` /
      [`tests/base/test_init.py`][test-base-init] still read `0.0.13` when
      this card flips Done; the joint `0.0.14` cut owns the bump
      ([Decision 12](#decision-12--version-bumps-are-owned-by-the-joint-0014-cut)).
- [ ] `uv run ruff format .` / `ruff check --fix .` clean; no `pytest` unless
      the maintainer asks (the [`START.md`][start] workflow rule).

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[goal]: ../GOAL.md
[kanban]: ../KANBAN.md
[pyproject]: ../pyproject.toml
[pytest-ini]: ../pytest.ini
[readme]: ../README.md
[start]: ../START.md
[today]: ../TODAY.md

<!-- docs/ -->
[docs-readme]: README.md
[glossary]: GLOSSARY.md
[glossary-auth-mutations]: GLOSSARY.md#auth-mutations
[glossary-configurationerror]: GLOSSARY.md#configurationerror
[glossary-debug-toolbar-middleware]: GLOSSARY.md#debug-toolbar-middleware
[glossary-djangoconnectionfield]: GLOSSARY.md#djangoconnectionfield
[glossary-djangographqlprotocolrouter]: GLOSSARY.md#djangographqlprotocolrouter
[glossary-djangolistfield]: GLOSSARY.md#djangolistfield
[glossary-djangooptimizerextension]: GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: GLOSSARY.md#djangotype
[glossary-eviction-simulated-absence]: GLOSSARY.md#eviction-simulated-absence
[glossary-fielderror-envelope]: GLOSSARY.md#fielderror-envelope
[glossary-graphqltestcase]: GLOSSARY.md#graphqltestcase
[glossary-joint-version-cut]: GLOSSARY.md#joint-version-cut
[glossary-live-first-coverage-mandate]: GLOSSARY.md#live-first-coverage-mandate
[glossary-pep-562-lazy-export]: GLOSSARY.md#pep-562-lazy-export
[glossary-request-from-info]: GLOSSARY.md#request_from_info
[glossary-response-extensions-debug-middleware]: GLOSSARY.md#response-extensions-debug-middleware
[glossary-safe-wrap-connection-method]: GLOSSARY.md#safe_wrap_connection_method
[glossary-schema-reload-discipline]: GLOSSARY.md#schema-reload-discipline
[glossary-seed-data]: GLOSSARY.md#seed_data
[glossary-soft-dependency]: GLOSSARY.md#soft-dependency
[glossary-testclient]: GLOSSARY.md#testclient
[glossary-upload-scalar]: GLOSSARY.md#upload-scalar
[tree]: TREE.md

<!-- docs/SPECS/ -->
[next]: SPECS/NEXT.md
[spec-037]: SPECS/spec-037-upload_file_image_mapping-0_0_11.md
[spec-041]: SPECS/spec-041-channels_router-0_0_14.md
[spec-042]: SPECS/spec-042-debug_toolbar-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[conf]: ../django_strawberry_framework/conf.py
[init]: ../django_strawberry_framework/__init__.py
[testing-init]: ../django_strawberry_framework/testing/__init__.py

<!-- tests/ -->
[test-base-init]: ../tests/base/test_init.py
[test-routers]: ../tests/test_routers.py
[tests-conftest]: ../tests/conftest.py

<!-- examples/ -->
[config-urls]: ../examples/fakeshop/config/urls.py
[schema-reload]: ../examples/fakeshop/schema_reload.py
[test-auth-api]: ../examples/fakeshop/test_query/test_auth_api.py
[test-kanban-api]: ../examples/fakeshop/test_query/test_kanban_api.py
[test-library-api]: ../examples/fakeshop/test_query/test_library_api.py
[test-multi-db]: ../examples/fakeshop/test_query/test_multi_db.py
[test-mutation-atomicity]: ../examples/fakeshop/test_query/test_mutation_atomicity.py
[test-products-api]: ../examples/fakeshop/test_query/test_products_api.py
[test-query-conftest]: ../examples/fakeshop/test_query/conftest.py
[test-query-readme]: ../examples/fakeshop/test_query/README.md
[test-uploads-api]: ../examples/fakeshop/test_query/test_uploads_api.py

<!-- scripts/ -->
[build-kanban-md]: ../scripts/build_kanban_md.py
[build-tree-md]: ../scripts/build_tree_md.py

<!-- .venv/ -->
[django-client]: ../.venv/lib/python3.14/site-packages/django/test/client.py
[venv-strawberry-test-client]: ../.venv/lib/python3.14/site-packages/strawberry/test/client.py

<!-- External -->
[upstream-client]: ../../strawberry-django-main/strawberry_django/test/client.py
[upstream-settings]: ../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/settings.py
[upstream-testing]: ../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/utils/testing.py
