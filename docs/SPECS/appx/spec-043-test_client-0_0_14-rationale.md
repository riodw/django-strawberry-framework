# Rationale: spec-043 — Test client helper (deliberation and rejected alternatives)

Deliberative companion to [`spec-043-test_client-0_0_14.md`][spec-043]. The spec is the contract;
this file carries the alternatives each decision rejected and why each lost, and the derivations
that do not change how a decision is implemented.

## How to read this file

- **One entry per spec decision**, named by the decision's own heading and linked to its anchor,
  so a citation such as "Decision 9's rejected alternatives" resolves to exactly one place. The two
  spec sections that carry deliberation without being numbered decisions — `## Borrowing posture`
  and `## Risks and open questions` — get their own entries under `## Non-decision entries`.
- **Where this file and the spec disagree, the spec is the contract.**
- **What stays in the spec even though it reads like deliberation.** Decision 9's account of why
  the `content_type` argument is *omitted* rather than passed (and its instruction not to "fix"
  upstream's inert `format="multipart"` kwarg back in), the `operationName` omitted-never-`null`
  reasoning, the explicit-`raise`-not-bare-`assert` reasoning that makes every guard survive
  `python -O`, Decision 7's "`self.path` is never mutated" non-persistence reasoning, and Decision
  11's live-first placement rule are instructions to a builder: one who never reads them passes the
  constant explicitly, sends `operationName: null`, writes a bare `assert`, mutates `self.path` per
  call, or restates a live behaviour as a package-tier stand-in.

## Decision entries

### Decision 1 — Spec filename and canonical naming

Spec: [Decision 1][d1].

**Alternatives rejected.**

- **`spec-043-test_client_helper-0_0_14.md`.** The `_helper` suffix adds length without
  disambiguation — no other card touches the test-client surface.
- **`spec-043-testing_client-0_0_14.md`.** The slug names the card's subject (the test client),
  not the module path; the established slug style is subject-first (`debug_toolbar`,
  `channels_router`, `auth_mutations`).

### Decision 2 — Card-scope boundary

Spec: [Decision 2][d2].

**Alternatives rejected.**

- **Adopt the Channels session-auth verification here.** Wrong vehicle (communicators, not test
  clients), wrong dependency posture (soft `channels` in a zero-new-dependency card), and an M card
  would swell past its size for a deliverable that belongs to the auth / router surface.
- **Adopt the toolbar async smoke.** It would make this card's test suite import a soft dependency
  (`django-debug-toolbar`) and reproduce the toolbar suite's settings fixture for one assertion the
  toolbar's own test module can carry.

**Justification.** The card's DoD names exactly the in-scope set; the two adjacent handoffs are
disjunctions this spec resolves but does not absorb — [`START.md`][start]'s "resist scope creep"
rule applied to a card that two sibling specs point at.

### Decision 3 — The symbols are upstream's own names

Spec: [Decision 3][d3].

**Alternatives rejected.**

- **`DjangoTestClient` / package-prefixed names.** The package's `Django*` prefix marks
  schema-side public API (`DjangoType`, `DjangoConnectionField`); test utilities are namespaced by
  their module path, and a renamed symbol breaks the one-line migration for zero gain.
- **`GraphQLTransactionTestCase` shortened to `GraphQLTxTestCase`.** Graphene migrants grep for
  the upstream name; abbreviation saves nothing.
- **A single `GraphQLTestCase` with a class flag for transaction behavior.** Django's own
  `TestCase` / `TransactionTestCase` are distinct classes with distinct semantics; flattening them
  into a flag would be a package-invented indirection over a Django concept.

**Derivation.** A symbol whose public identity is "the thing you import from the package" needs no
invented name (the [`spec-042`][spec-042] Decision 3 argument), and the concrete pair keeps
graphene's exact `TestCase` / `TransactionTestCase` split because that split is Django's own
testing vocabulary rather than a graphene-ism.

### Decision 4 — Module, export, and test locations

Spec: [Decision 4][d4].

**Alternatives rejected.**

- **Submodule-only (`from django_strawberry_framework.testing.client import TestClient`), the
  `relay` posture.** The light-import rationale that justifies the `relay` exception does not
  apply: the client module imports `django.test` and `strawberry.test`, both already imported by
  any process running Django tests, which is the only process that imports `testing` at all.
- **Package-root export.** Pollutes the schema-building `__all__` with test-only names; neither
  upstream does it.
- **A new top-level `test/` subpackage mirroring upstream's path exactly.** It would shadow the
  Python stdlib `test` package, and two test-utility subpackages is a migration aid for nobody.

**Derivation.** The three postures the subpackage holds at once (root-re-exported
`safe_wrap_connection_method`, deliberately submodule-only `relay`, and this card's
root-re-exported family) are a locality contrast worth reading before proposing a fourth.

### Decision 5 — Subclass Strawberry's `BaseGraphQLTestClient`

Spec: [Decision 5][d5].

**Alternatives rejected.**

- **Roll a package-owned base.** Rejected on the decision's three grounds; the only surface it
  would free is already free in the subclass.
- **Wrap (compose) instead of subclass.** Composition would re-declare `query()`'s full signature
  just to delegate, and the base is an ABC designed for exactly this subclass shape.
- **Subclass but keep the base's `_build_multipart_file_map` (no owned builder).** The base's
  folder heuristic returns an empty map for fakeshop's nested input-object uploads, so keeping it
  would force the upload suites onto raw `client.post(...)` and shrink the consumer-facing
  contract.
- **Fork/patch the base's map builder into the package.** It forks engine-internal code and
  inherits its folder-key guessing; the public path-keyed `files=` contract lets the package's own
  builder be independent of the base's heuristic.
- **`client or Client()` as the default-transport selection.** A caller-supplied client whose
  `__bool__` / `__len__` reports false would be silently discarded onto a fresh client with a
  different session — the `or`-fallback-on-a-legitimately-falsy-left-operand shape
  [`docs/builder/BUILD.md`][build] `### Fail-open shapes` catalogues.

**The card's counterargument, and the answer.** The card observed that "the package's DRF-first
stance argues for considering the from-scratch alternative". The coupling actually at stake: the
base pins `_decode` and `Response` field names, both of which the package **wants** pinned to the
engine (the wire format is the engine's); the body build the package owns outright, and the
package-shaped surface (endpoint resolution, `operation_name`, the raw-response field, the
unittest family) lands in the subclass anyway. DRF-first governs the *consumer configuration
surface* (`class Meta`, settings keys) — which this card does shape itself — not the reuse of the
engine `_decode` / `Response` seams the package's own read/write paths already treat as the wire
contract.

**Derivation — the shared response tail.** Owning `query()` in both colors does not mean two
copies of the tail: `_finish_response` factors the un-colored `_decode` → `Response` construction
→ `assert_no_errors` raise *below* the not-calling-`super().query()` decision, not around it, so
the async color still owns its own `await self.request(...)`.

### Decision 6 — `.query()` returns the typed `Response`

Spec: [Decision 6][d6].

**Alternatives rejected.**

- **Raw `HttpResponse` return (graphene's flavor).** The card recommends against it; every
  consumer then re-decodes the body, and the "200 plus an `errors` key" trap returns to every call
  site.
- **Strawberry's `Response` unmodified (no raw-response field).** Strands status/header/cookie
  assertions on raw posts, so the live tier could not move onto the client without losing them.
- **Two return flavors behind a flag (`raw=True`).** The card says pick one; a mode flag is both
  flavors' costs with neither's clarity.
- **A `mutate()` alias for `query()`.** No upstream has it, and an alias that changes nothing
  invites the false belief it does something (e.g. auto-prefixing `mutation`).

**The card's `.mutate()` claim vs. the source.** The card attributed a `.mutate()` surface to the
upstream base and to `strawberry_django.test.client.TestClient`, but neither has one, nor does
graphene's mixin. On a factual claim about upstream source the source wins, so the package ships
no `mutate()`.

**Derivation — the `response` default.** The `response` field takes a `None` default. The
engine's `Response` declares three fields with no defaults, so a defaultless child field would
construct fine too; the default stays because `Response` is re-exported public surface and
removing a default narrows a constructor consumers may already call. Both in-repo construction
sites pass `response=` explicitly, so the default is never observed in practice.

### Decision 7 — Endpoint resolution: the settings key is `TESTING_ENDPOINT`

Spec: [Decision 7][d7].

**Alternatives rejected.**

- **`GRAPHQL_TESTING_ENDPOINT` (the card's working name).** A redundant prefix inside the
  namespaced dict; it breaks the graphene name parity the card itself cites.
- **A Django-global settings name (top-level `GRAPHQL_TESTING_ENDPOINT`).** The package's one
  settings surface is the `DJANGO_STRAWBERRY_FRAMEWORK` dict (`conf.py`'s documented contract); a
  second top-level name fragments it.
- **Default `"/graphql"` (graphene's).** Fakeshop and Strawberry both use the trailing slash; a
  slash-less default would not match that `/graphql/` mount — under `APPEND_SLASH` a body-bearing
  POST raises `RuntimeError` in `DEBUG` (or is 301-redirected in a way that drops the body), never
  cleanly reaching the view.
- **Re-reading the settings key on every request.** The settings-derived default resolves once at
  construction (upstream's posture); the explicit per-call `url=` override covers the legitimate
  per-request need.
- **Dropping the per-call override** (constructor + class attribute only). The card names a
  per-call override; honoring it is one keyword-only parameter on `query()` plus the widened
  `request(..., *, url=None)` transport hook.
- **A `self.path`-mutation shim for the per-call override.** It would persist the override past
  its call and let concurrent or async calls race on shared state.
- **Reject a non-`str` endpoint at the accessor.** `TESTING_ENDPOINT = reverse_lazy(...)` is a lazy
  proxy, not a `str`, and works because `django.test.RequestFactory.generic` coerces the path
  (`urlsplit(str(path))`); a `str` gate would break it, and admitting the proxy would import a
  Django-internal type into [`conf.py`][conf] and make this key the module's first shape gate
  against its thin-reader siblings. There is no gap to close: `None`, `7`, and `["/graphql/"]` post
  to `/None`, `/7`, `/['graphql/']` and produce the same 404 plus non-JSON `ValueError` a typo'd
  string does. (`TESTING_ENDPOINT = ""` is the value that does **not** 404 — it routes to the
  URLconf root — which is why the spec says "ordinarily a 404".)

**Naming derivation.** Inside a settings dict named `DJANGO_STRAWBERRY_FRAMEWORK` every key is
about this package's GraphQL surface, so a `GRAPHQL_` prefix is pure redundancy — and the
unprefixed name is byte-identical to graphene's own `TESTING_ENDPOINT` key. Existing keys set the
style: none carry a `GRAPHQL_` prefix (`NESTED_CONNECTION_STRATEGY`, `APPLY_UPSTREAM_PATCHES`;
`RELAY_GLOBALID_STRATEGY`'s prefix names the Relay subsystem, not GraphQL).

### Decision 8 — Async shape: sibling clients over one shared base

Spec: [Decision 8][d8].

**Alternatives rejected.**

- **Upstream's `AsyncTestClient(TestClient)`.** The is-a relationship is false where it matters:
  the async `query()` / `login()` are coroutine-colored, so an `AsyncTestClient` accepted where a
  `TestClient` is expected returns an un-awaited coroutine from `query()`.
- **Two flat clients each subclassing `BaseGraphQLTestClient`.** Re-declares the constructor,
  `request()`, the body builder, the placeholder walker, and the response tail twice — exactly the
  un-colored code the shared base holds once.
- **One class with sync/async auto-detection** (the package's `is_async_callable` machinery from
  `DjangoListField`). That machinery exists for *consumer-supplied* resolvers whose color the
  package cannot know; here the caller chooses the color by picking the class, and a dual-color
  `query()` would return `Response | Coroutine` — the ambiguity the typed helper exists to remove.

### Decision 9 — Multipart uploads: `files=` maps variable paths to file parts

Spec: [Decision 9][d9].

**Alternatives rejected.**

- **Infer file paths from the `variables` structure** (the base's approach — walk the dict, guess
  folders, number lists). That heuristic is exactly what returns an empty map for nested input
  objects; an explicit path-keyed `files=` is unambiguous, trivially recursive, and self-documents
  where each file lands.
- **Copy `format="multipart"` verbatim.** Knowingly shipping an inert kwarg that implies a DRF
  client is in play misleads every future reader; the borrow is of behavior, not typos.
- **Explicit `content_type=MULTIPART_CONTENT`.** It states the intent, but Django's test client
  encodes the data dict itself only when `content_type` is the default sentinel value; passing the
  constant explicitly is equivalent today but couples to the constant's identity. The omission,
  plus the comment, is the documented idiom.
- **Gate `operationName` on truthiness (`if operation_name:`).** An explicit `""` would be
  silently reinterpreted as "no operation name"; gating on `is not None` sends it for the server to
  reject with a real GraphQL error.
- **Let the trailing `**files` spread take any key.** A `files` key named `operations` or `map`
  (with a matching placeholder) would overwrite the envelope and post a corrupt body the server has
  to diagnose; refusing it at the source matches the sibling guards.
- **Delete the empty-`variables` guard as subsumed by the walker.** The walker does not catch a
  *falsy container carrying real placeholders* — a `dict` subclass whose `__bool__` returns
  `False` holding `{"file": None}`: the walker accepts it while the emission writes no `variables`
  member, so the builder would emit `operations` without `variables` beside a `map` pointing into
  `variables.file`, an envelope Strawberry rejects with "File(s) missing in form data", a message
  that blames files which are present. The guard decides that verdict, and its message for
  `variables=None` is clearer than the walker's would be.
- **Spell the guard as a truthiness test on the `variables` argument.** It would duplicate the
  emission's own truthiness test, so a change to the emission rule would have to move two sites;
  reading `"variables" not in body` derives the guard from the envelope it protects.
- **`segment.isdigit() and int(segment) < len(current)` for array indexes.** The two domains
  disagree: `isdigit()` accepts superscripts `int()` rejects, and digit-like Unicode and very long
  decimal strings do not share `int()`'s acceptance domain, so a non-canonical index could be
  accepted where the emitted `object-path` segment could not name it.
- **`{x!r}` in guard diagnostics.** A hostile `__repr__` on a consumer-supplied path or value would
  escape the guard as a raw exception; `_safe_arg_repr` contains it.

### Decision 10 — Mixin-first: `GraphQLTestMixin` composes over `TestClient`

Spec: [Decision 10][d10].

**Alternatives rejected.**

- **Concrete test cases only, no mixin.** The card pins mixin-first and names the custom-base
  composition use case.
- **The mixin re-implements the POST (graphene's actual internals).** Two body-builders drift; the
  delegate costs one object per call in test code.
- **Renamed assertion helpers (`assert_no_errors` snake_case).** The helpers exist for graphene
  migrants; unittest's own assertion vocabulary is camelCase (`assertEqual`), so the graphene names
  are also the idiomatic unittest names.
- **`assert_no_errors=True` on the mixin's `query()` for family-wide uniformity.** It silently
  breaks the graphene migration's central pattern — auto-raising from inside `query()` breaks every
  ported `assertResponseHasErrors` test at the call site, before the assertion helper runs;
  uniformity of defaults is worth less than both migrations working.

**Derivation.** The keyword-only signature after `query` trades graphene positional-call fidelity
for one uniform keyword signature across the pytest client and the mixin: graphene's own
positional order `(query, operation_name, input_data, variables, headers)` cannot survive dropping
`input_data` intact anyway. The flipped `assert_no_errors=False` default is the same trade in the
other direction — each flavor defaults to its own upstream's behavior.

### Decision 11 — Test strategy: the live switchover is the primary coverage

Spec: [Decision 11][d11].

**Alternatives rejected.**

- **A package-only test suite.** Without the live tier on the client, the package tests would
  duplicate live coverage the live-first mandate says belongs in the live tier — the
  "package-only stand-in" pattern the live-first promotion rule exists to retire.
- **Switch only one representative live file.** A partial move leaves two idioms in the tree
  indefinitely, which is worse for readers than either.
- **Mock-based unit tests for `request()`.** Real fakeshop requests are available in-process; mock
  only when the real path is impossible. The package tier's recording transports replace the
  wrapped Django client, never `request()` itself, so the real target selection is what they read.
- **A "custom-view plumbing" exemption class for raw posts.** A raw post whose only reason was
  per-file plumbing meets no wire-shape class and goes through the client (with `path=` / `url=`
  for a test-owned mount); a declared exemption that is false forecloses the next reader's
  question.

**Conversion traps.** `assert_no_errors=False` is required even where **no** error is expected
when a row asserts on `errors` itself, or the client's own raise relocates that assertion; and a
row asserting `"errors" not in payload` needs the decoded dict, not a payload rebuilt from the
typed `Response`. A raw multipart POST spelled `client.generic("POST", ...)` is invisible to a
`.post(` grep, so a census of raw posts searches both spellings.

### Decision 12 — Version bumps are owned by the joint `0.0.14` cut

Spec: [Decision 12][d12].

**Alternatives rejected.**

- **Bump to `0.0.14` in Slice 3.** Other cards shipped into `0.0.14` too; a per-card bump races the
  joint cut and would be reconciled twice over.

## Non-decision entries

### Borrowing posture — the two-upstream split

Spec: [Borrowing posture][borrowing].

**The upstream source readings.** The package cannot ride the base's `query()`: its signature is
fixed (`query(query, variables=None, headers=None, files=None, assert_no_errors=True)`: no
`operation_name`, no `url`), it calls `request(body, headers, files)` with no target argument, and
it constructs the base `Response` directly — the derivation behind Decision 5 ground 2. Owning the
**sync** `query()` is not a new posture: upstream's own `AsyncTestClient.query()` already fully
re-implements the flow rather than calling `super().query()`.

**The upstream inventories.** `strawberry_django/test/client.py` (the two clients, `login`, the
`format="multipart"` request kwarg, `@override` on the async `query()`) and
`graphene_django/utils/testing.py` (`graphql_query`'s envelope building and `input_data`
convenience, the mixin's deprecated `_client` property shim, graphene's `TESTING_ENDPOINT`
default of `"/graphql"`) are the evidence the borrow decisions rest on; the decisions and the
non-borrow list stay in the spec.

**`_safe_arg_repr` is not a borrow.** Neither upstream contributes it; it is the package's own
hostile-metadata containment helper from `django_strawberry_framework/exceptions.py`, which is why
it sits in the spec's `## Helper-reuse obligations (DRY)` as D5 rather than in the borrowing list.

### Risks and open questions — the preferred-answer / fallback weighing

Spec: [Risks and open questions][risks].

- **Upstream reshapes the base later.** *Preferred:* accept the remaining coupling; the
  request-driving tests fail loudly under a refreshed lock and the fix tracks upstream's change.
  *Fallback:* pin the reshaped pieces locally — `_decode` is small enough to own too if it ever
  moves.
- **Async DB tests joining a suite with known async-connection hazards.** *Preferred:* the
  `AsyncTestClient` rows mark `django_db(transaction=True)` (or seed through a sync
  `transactional_db` fixture) and follow `tests/conftest.py`'s existing hygiene. *Fallback:* a
  surfaced flake is fixed at source in the shared conftest, never by weakening `-W error`.
- **The mixin's flipped `assert_no_errors=False` default.** *Preferred:* each flavor matches its
  own upstream's behavior (the property that makes both migrations work unchanged); both
  docstrings state the other's default. *Fallback:* if real-world confusion outweighs migration
  fidelity, a future minor can align the mixin to `True` — a deliberate breaking change for
  graphene-ported error tests, acceptable only pre-`1.0.0`.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[start]: ../../../START.md

<!-- docs/ -->

<!-- docs/SPECS/ -->
[borrowing]: ../spec-043-test_client-0_0_14.md#borrowing-posture
[d1]: ../spec-043-test_client-0_0_14.md#decision-1--spec-filename-and-canonical-naming
[d10]: ../spec-043-test_client-0_0_14.md#decision-10--mixin-first-graphqltestmixin-composes-over-testclient-the-graphene-assertion-helpers-keep-their-names-typed-response-shaped
[d11]: ../spec-043-test_client-0_0_14.md#decision-11--test-strategy-the-live-switchover-is-the-primary-coverage-teststestingtest_clientpy-owns-the-rest
[d12]: ../spec-043-test_client-0_0_14.md#decision-12--version-bumps-are-owned-by-the-joint-0014-cut
[d2]: ../spec-043-test_client-0_0_14.md#decision-2--card-scope-boundary-the-test-client-family-ships-channels-session-auth-verification-the-toolbars-async-smoke-and-fakeshop-runtime-changes-stay-out
[d3]: ../spec-043-test_client-0_0_14.md#decision-3--the-symbols-are-upstreams-own-names--testclient--asynctestclient--graphqltestmixin--graphqltestcase--graphqltransactiontestcase-distinctly-ours-import-path
[d4]: ../spec-043-test_client-0_0_14.md#decision-4--module-export-and-test-locations-testingclientpy-re-exported-from-the-testing-root-teststestingtest_clientpy
[d5]: ../spec-043-test_client-0_0_14.md#decision-5--subclass-strawberrys-basegraphqltestclient--engine-owned-base-over-a-hard-dependency-no-soft-dependency-machinery
[d6]: ../spec-043-test_client-0_0_14.md#decision-6--query-returns-the-typed-response-dataclass-extended-with-the-raw-httpresponse-operation_name-is-supported
[d7]: ../spec-043-test_client-0_0_14.md#decision-7--endpoint-resolution-the-settings-key-is-testing_endpoint-default-graphql--resolving-the-cards-graphql_testing_endpoint-working-name
[d8]: ../spec-043-test_client-0_0_14.md#decision-8--async-shape-asynctestclient-is-a-sibling-of-testclient-over-one-shared-base
[d9]: ../spec-043-test_client-0_0_14.md#decision-9--multipart-uploads-files-maps-variable-paths-to-file-parts-the-package-owns-the-bodymultipart-builder-upstreams-no-op-format-kwarg-is-dropped
[risks]: ../spec-043-test_client-0_0_14.md#risks-and-open-questions
[spec-042]: ../spec-042-debug_toolbar-0_0_14.md
[spec-043]: ../spec-043-test_client-0_0_14.md

<!-- docs/builder/ -->
[build]: ../../builder/BUILD.md

<!-- django_strawberry_framework/ -->
[conf]: ../../../django_strawberry_framework/conf.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
