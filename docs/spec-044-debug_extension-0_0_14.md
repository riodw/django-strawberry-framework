# Spec: Response-extensions debug middleware — `DjangoDebugExtension` in `extensions/debug.py`, Django-recorded query-log SQL and raised exceptions in the GraphQL response's `extensions["debug"]` map

Planned for `0.0.14` (card [`WIP-ALPHA-044-0.0.14`][kanban]); **this card
completes the joint `0.0.14` cut and owns the version bump**
([Decision 12](#decision-12--this-card-completes-the-joint-0014-cut-and-owns-the-version-bump)).
This card adds the package's **in-response debug surface**: a new
`django_strawberry_framework/extensions/debug.py` module exposing
`DjangoDebugExtension`, a Strawberry `SchemaExtension` that captures the
Django-recorded query-log SQL and execution exceptions for the in-flight GraphQL
operation and attaches them to the response's `extensions` map under the
`debug` key — so frontend clients, Apollo DevTools, and programmatic consumers
can read them **inside the GraphQL response itself**, without the server-side
toolbar. It is a Required **single-upstream** parity item
([Single-upstream parity][glossary-single-upstream-parity], the card's own
Parity line): ⚛️ `graphene-django` ships the `DjangoDebug` subsystem
([`graphene_django/debug/`][upstream-debug-init] — the
[`DjangoDebugMiddleware`][upstream-debug-middleware] Graphene resolver
middleware, the [`DjangoDebug`][upstream-debug-types] object type, the
[`DjangoDebugSQL`][upstream-sql-types] / [`DjangoDebugException`][upstream-exception-types]
row shapes, the thread-local [cursor wrap][upstream-sql-tracking], and the
[`wrap_exception`][upstream-exception-formating] serializer — all read in full
for this spec), while 🍓 `strawberry-graphql-django` ships **no** equivalent
(the card's verified claim: no upstream file references `connection.queries`
and no `*debug*` module exists outside the toolbar middleware tracked by
[`DONE-042-0.0.14`][kanban]); the other's absence is recorded plainly rather
than fabricated. The mechanism is deliberately distinct from the landed
[Debug-toolbar middleware][glossary-debug-toolbar-middleware] sibling: that is
the server-side `django-debug-toolbar` SQL-panel UI over `/graphql/` traffic;
this is in-response surfacing through the GraphQL `extensions` envelope.
"Both mechanisms are useful and not mutually exclusive" (the card's "Why it
matters", verbatim).

The surface is deliberately **thin and engine-riding**: Strawberry's
[`SchemaExtension`][venv-base-extension] base (part of the package's **hard**
`strawberry-graphql` dependency — no [soft dependency][glossary-soft-dependency],
no guard, no install hint; like [`DONE-043-0.0.14`][kanban] before it, a card
that adds **zero** new dependencies) supplies the operation lifecycle hook
(`on_operation`) and the response-extensions merge seam (`get_results`), and
Django itself supplies the SQL fidelity — the extension brackets each
configured connection with Django's own debug cursor
(`force_debug_cursor`, the exact mechanism of
[`django.test.utils.CaptureQueriesContext`][venv-django-test-utils]) and reads
the per-connection `queries_log`, so capture works **independent of
`settings.DEBUG`**
([Decision 4](#decision-4--fidelity-djangos-own-debug-cursor-via-a-force_debug_cursor-bracket-not-a-cursor-wrap-port)).
Exceptions come off the execution result's `GraphQLError.original_error`
chain, serialized to graphene's `excType` / `message` / `stack` field names
([Decision 9](#decision-9--exception-capture-the-results-original_error-chain-serialized-like-graphenes-wrap_exception--no-resolver-wrapping))
— no per-resolver wrapping, because Strawberry already funnels resolver
exceptions into `result.errors` with the original exception preserved. The
extension is **off by default**; the opt-in is passing the class in the
`extensions=` list of `strawberry.Schema(...)`
([Decision 6](#decision-6--opt-in-shape-pass-the-class--one-fresh-instance-per-operation-requires-strawberry-03160)),
exactly the card's "Off by default; opt-in via the extensions list" DoD row.

**Version boundary** (see
[Decision 12](#decision-12--this-card-completes-the-joint-0014-cut-and-owns-the-version-bump)):
this card is the **last non-Done card at `0.0.14`**. Its three landed
predecessors — [`DONE-041-0.0.14`][kanban]
([`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter]),
[`DONE-042-0.0.14`][kanban]
([Debug-toolbar middleware][glossary-debug-toolbar-middleware]), and
[`DONE-043-0.0.14`][kanban] ([`TestClient`][glossary-testclient] /
[`GraphQLTestCase`][glossary-graphqltestcase]) — each deferred its version
bump and release-status wording to the [joint `0.0.14`
cut][glossary-joint-version-cut], and per that rule the **last card of the
patch line to land owns the cut**. That card is this one. So unlike
[`spec-041`][spec-041] Decision 10 / [`spec-042`][spec-042] Decision 10 /
[`spec-043`][spec-043] Decision 12 (all deferrals), this spec's Slice 3
carries the version quintet, the GLOSSARY `shipped (0.0.14)` status flips for
all four `0.0.14` cards, and the release-status doc moves — mirroring the
lone-card ownership shape of [`spec-038`][spec-038] Decision 14.

Status: **COMPLETE (card `DONE-044-0.0.14`) — all three slices built and the card-wrap landed; this card owned and applied the joint `0.0.14` version cut (the version quintet, the GLOSSARY `shipped (0.0.14)` status flips for `041` / `042` / `043` / `044`, and the release-status doc moves).**
Three slices (the card is an M with one module, two test files, and the joint
cut's mechanically-wide doc alignment): Slice 1 (**the `extensions/`
subpackage + `extensions/debug.py` + split live/mechanics coverage** — the
whole public surface and its coverage land in one commit, green under the
`fail_under = 100` gate), Slice 2 (**implemented-contract docs; no card wrap
and no version bump** — the
implemented-contract [`docs/GLOSSARY.md`][glossary] entry-body update, the
regenerated [`docs/TREE.md`][tree], the stale
[`config/schema.py`][config-schema] docstring sentence, and the
[`GOAL.md`][goal] clarification), and Slice 3 (**the joint `0.0.14` cut +
final card wrap** — the version quintet, the
GLOSSARY status flips for `041` / `042` / `043` / `044`, the
[`README.md`][readme] / [`docs/README.md`][docs-readme] / [`TODAY.md`][today]
release-status moves, and the `CHANGELOG.md` `0.0.14` section, whose edit
permission this spec's Slice 3 grants explicitly per the
[`docs/SPECS/NEXT.md`][next] convention).

Owner: package maintainer.

Predecessors: [`spec-043-test_client-0_0_14.md`][spec-043] (the most recent
spec and the canonical voice / depth / section-layout reference; its
[`TestClient`][glossary-testclient] is available to this card's tests as HTTP
ergonomics); [`spec-042-debug_toolbar-0_0_14.md`][spec-042] (the sibling
debug mechanism — this card is documented as its response-side counterpart,
the card's own DoD row); [`spec-041-channels_router-0_0_14.md`][spec-041]
(whose Decision 10 first pinned the `0.0.14` joint-cut deferral this card now
discharges); [`spec-038-form_mutations-0_0_12.md`][spec-038] (the most recent
**lone-card** version-bump decision, mirrored here as
[Decision 12](#decision-12--this-card-completes-the-joint-0014-cut-and-owns-the-version-bump)).
[`docs/GLOSSARY.md`][glossary] carries [Response-extensions debug
middleware][glossary-response-extensions-debug-middleware] as `planned for
0.0.14`; Slice 2 updates the entry body to the implemented contract and
Slice 3 flips the status to `shipped (0.0.14)` alongside the other three
`0.0.14` entries.

Revision history (kept inline so the spec is self-contained):

- **Revision 1** — initial draft authored from the [`WIP-ALPHA-044-0.0.14`][kanban]
  card body via the [`docs/SPECS/NEXT.md`][next] flow (2026-07-10). Pinned:
  the canonical structured filename
  ([Decision 1](#decision-1--spec-filename-and-canonical-naming)); the
  card-scope boundary — the extension ships alone, with no Django middleware,
  no schema-level field, and no fakeshop always-on wiring
  ([Decision 2](#decision-2--card-scope-boundary-the-extension-ships-alone--no-django-middleware-no-schema-field-no-fakeshop-always-on-wiring));
  the card's first "pick one before writing the spec" choice resolved **for**
  the response-`extensions` map (the card's own proposed Strawberry-native
  shape and its named default), with the graphene schema-level `_debug` field
  rejected with reasons
  ([Decision 3](#decision-3--exposure-the-response-extensions-map-under-the-debug-key-not-a-schema-level-_debug-field));
  the card's second choice resolved **for** `connection.queries` fidelity (the
  card's named default), sharpened to Django's own debug-cursor bracket
  (`force_debug_cursor`, the `CaptureQueriesContext` mechanism) so capture
  does not silently depend on `settings.DEBUG`, with the cursor-wrap port
  rejected with reasons
  ([Decision 4](#decision-4--fidelity-djangos-own-debug-cursor-via-a-force_debug_cursor-bracket-not-a-cursor-wrap-port));
  the symbol pinned as `DjangoDebugExtension` at the
  `django_strawberry_framework.extensions` subpackage — never the package
  root
  ([Decision 5](#decision-5--symbol-and-home-djangodebugextension-in-extensionsdebugpy-exported-from-the-extensions-subpackage--never-the-package-root));
  the opt-in shape pinned as passing the **class** (one fresh instance per
  operation), explicitly not the optimizer's singleton-in-a-factory pattern,
  and the Strawberry floor raised to `0.316.0` because earlier sync execution
  cached extension instances
  ([Decision 6](#decision-6--opt-in-shape-pass-the-class--one-fresh-instance-per-operation-requires-strawberry-03160));
  the hook shape — one sync `on_operation` generator serving both execution
  colors, payload assembly at teardown, `get_results` returning the stash,
  with the pre-execution-error no-`debug`-key consequence derived from the
  engine's verified call ordering
  ([Decision 7](#decision-7--hook-shape-one-sync-on_operation-generator-assembly-at-teardown-get_results-returns-the-stash));
  the SQL row shape — graphene's wire names, narrowed to the six fields
  Django's own log supports, every omission named
  ([Decision 8](#decision-8--the-sql-row-shape-graphenes-wire-names-narrowed-to-what-djangos-log-supports));
  exception capture off the result's `original_error` chain
  ([Decision 9](#decision-9--exception-capture-the-results-original_error-chain-serialized-like-graphenes-wrap_exception--no-resolver-wrapping));
  the multi-database bracket over `connections.all()`
  ([Decision 10](#decision-10--multi-database-capture-every-alias-in-connectionsall-one-bracket-each));
  the test strategy — real HTTP through a probe URLconf in
  `examples/fakeshop/test_query/test_debug_extension_api.py`, with only
  request-impossible mechanics in `tests/extensions/test_debug.py`
  ([Decision 11](#decision-11--test-strategy-split-live-http-behavior-from-package-tier-mechanics));
  and the joint-cut ownership
  ([Decision 12](#decision-12--this-card-completes-the-joint-0014-cut-and-owns-the-version-bump)).
  One card-vs-shipped-shape conflict is recorded in
  [Risks](#risks-and-open-questions) rather than silently reconciled: the
  card's **title** says "middleware" while its own Architectural posture
  section says the Strawberry-native shape is a `SchemaExtension`, not a
  Django (or Graphene) middleware — resolved per the card's own posture, with
  the title's word kept only as the card-facing feature name.
- **Revision 2** — validation pass against the installed `0.316.0` engine,
  the cached `0.262.0` wheel, Django's query-log implementation, graphene's
  exception middleware, and the repository's test-placement law
  (2026-07-10). Corrected six implementation-blocking defects: raised the
  Strawberry floor to `0.316.0` because the old floor and verified `0.315.3`
  cache sync extension instances and race `execution_context`; split live HTTP
  tests into `examples/fakeshop/test_query/` and retained only
  request-impossible mechanics under `tests/extensions/`; required traceback
  serialization from `exc.__traceback__`; required walking nested
  `GraphQLError.original_error` links so explicitly raised GraphQL errors
  retain graphene parity; replaced the inaccurate bounded-log clamp guarantee
  with Django's actual best-effort length-snapshot semantics; and added a
  lock-protected reference-counted flag bracket so overlapping async
  operations cannot restore `force_debug_cursor` out of order. Added
  concurrent sync isolation, concurrent async restore, and nested-error-chain
  tests as regression gates.
- **Revision 3** — cross-checked the corrected design against
  [`GOAL.md`][goal], the requested
  [`cookbook/recipes/schema.py`][upstream-cookbook-recipes-schema], the
  cookbook's aggregate [`cookbook/schema.py`][upstream-cookbook-schema], and
  its Graphene settings (2026-07-10). Added the explicit goal/cookbook mapping
  and migration diff; confirmed that debug is project-level aggregate-schema
  configuration rather than recipe-app schema surface; and recorded the one
  deliberate wire migration (`_debug` selection → `response.extensions.debug`)
  required to remain Strawberry-native and avoid a Graphene compatibility
  runtime.
- **Revision 4** — DRY-review fold-in (2026-07-11). Applied the maintainer's
  review of the planned module against all thirteen
  `django_strawberry_framework/utils` modules: the
  [DRY section](#helper-reuse-obligations-dry) gains D4–D6 (module-level
  wire serializers with one `_SLOW_QUERY_SECONDS` constant; the
  single-sited collector / two-seam coordinator / log-slice /
  payload-builder inventory; idiom conformance — no `__init__`, the
  optimizer's generator-hook shape, the bounded-walk posture for the
  `original_error` peel, the eager-subpackage export shape, and the
  "database connection" docstring vocabulary) and D-N5–D-N7 (the
  `utils/connections.py` Relay-vocabulary disambiguation with the
  coordinator-placement constraint; the no-utils-import posture with its
  named near-misses; no `exceptions.py` addition), and D-N1 gains the
  sharper ground (at the `0.316.0` floor a ContextVar stash has no shared
  instance left to coordinate). Downstream: Decision 8 records the
  casing-helper rejection and the wire keys as serializer-and-test
  literals; Decision 9 records the bounded-walk conformance; Decisions 5
  and 7 record the export-shape and no-`__init__` / two-seam notes; the
  [Test plan](#test-plan) pins the anti-DRY literal rule and the
  seam-targeting rule; [Non-goals](#non-goals) records the `conf.py`
  non-surface reason. One review citation was corrected during
  verification: `middleware/__init__.py` deliberately re-exports nothing
  (spec-042's soft-dependency boundary), so the eager-export precedent
  cited is `utils/__init__.py` / `testing/__init__.py`.
- **Revision 5** — second-review reconciliation (2026-07-11). A parallel
  DRY review, written at the same time against the same Revision-3 text,
  was squared with Revision 4's fold-in; its suggested checklist items map
  onto this spec's D3–D6 / D-N5–D-N8 numbering. Genuinely new pins carried
  in: the direct-`CaptureQueriesContext` rejection gains two stronger
  grounds (the process-global `request_started → reset_queries` signal
  toggle — verified at `django/test/utils.py`
  `#"reset_queries_disconnected"` — and the refcount-free single-context
  restore); the coordinator map is keyed by connection object identity,
  never by alias; teardown iterates immutable per-alias snapshot records
  (connection + starting length) and never re-calls `connections.all()` to
  match by position; the collector also guards `errors is None`, preserves
  result-error order, and never speculatively dedups; `get_results` never
  writes `execution_context` or an existing `ExecutionResult.extensions`,
  and the stash's absent sentinel is `None`; D-N6's import list gains
  `graphql`; the new D-N8 rejects the premature abstractions (package base
  extension class, merged row dispatcher, dataclass/Strawberry wire rows,
  per-key constants); D3 gains the named acceptance-reload fixture,
  `create_users`, the one-holder probe-module shape with its
  copy-not-promote ground (`FAKESHOP_SHARDED` gating), and the
  never-sort-the-`extensions=`-list rule; and the Test plan gains the
  real-objects and parametrization rules, the happy-path-only debug
  accessor, the bracket-boundary-only fake (scenario 8), and the
  floor run selected by node id (scenario 13). Where the two reviews
  differed, the reconciliation is recorded in place: the coordinator may
  surface its two seams as methods or as one per-connection context
  manager (the pin is single ownership, not the callable shape), and the
  no-`__init__` rule keeps the first review's default with the second's
  constrained escape (`execution_context` passthrough only, no `**kwargs`
  sink).

- **Revision 6** — round-3 DRY review fold-in (2026-07-11). The review
  confirmed the Revision-4/5 shape (its audit re-ran clean against all
  thirteen `utils/` modules) and required three pins, none a design change:
  [Test plan](#test-plan) scenario 2 composes the optimizer through the
  **canonical consumer shape** — one module-local
  `DjangoOptimizerExtension()` singleton returned by `lambda: _optimizer`
  (the shipped [`config/schema.py`][config-schema] wiring, plan cache
  retained) beside the debug **class** entry, with no helper normalizing
  the two deliberately different lifetimes into one factory form; the
  probe module's URLconf **activation** is single-sited in
  [DRY D3](#helper-reuse-obligations-dry) — one module-level
  `pytest.mark.urls(__name__)` application (or one module-wide fixture),
  never per-test `override_settings(ROOT_URLCONF=...)` /
  `clear_url_caches()` blocks; and the no-`__init__` stash sentinel got a
  concrete home in
  [Decision 7](#decision-7--hook-shape-one-sync-on_operation-generator-assembly-at-teardown-get_results-returns-the-stash)
  — one immutable class-level `_payload = None` default, read directly by
  `get_results` and overridden on the instance only at successful
  teardown.
- **Revision 7** — source-verification correction pass (2026-07-11).
  Corrected seven contracts against Strawberry 0.316.0, Django 6.0.5, and
  asgiref internals: Strawberry constructs extensions with zero arguments and
  assigns `execution_context` afterward; response-extension merging includes
  async context-result precedence and replacement of any pre-existing result
  map; repeated `get_results()` calls are tied to the early-result plus
  teardown-failure recovery path rather than generic recovery; final card wrap
  moves behind the mandatory Slice-3 cut; SQL scope is narrowed to Django's
  `queries_log` and explicitly excludes `callproc()`; async overlap coverage
  pre-materializes and proves shared wrapper identity; and nested same-thread
  sync execution is documented as restoration-safe but cross-attributed.
- **Revision 8** — deep architectural review fold-in (2026-07-11; the
  review's 21 findings applied as one coherent pass, each verified against
  the installed Strawberry 0.316.0, Django 6.0.5, asgiref, and repository
  sources before editing). The five implementation blockers: Test plan
  scenario 2 and Goals item 5 rewritten to the **visibility-safe two-query
  prefetch shape** (`CategoryType.get_queryset` makes the optimizer plan
  `Prefetch`, never a joined single query — the existing
  `test_products_api.py` proof is the assertion precedent); the
  byte-identical / off-by-default overclaim replaced with the narrow
  no-instrumentation/no-key claim plus
  [Decision 6](#decision-6--opt-in-shape-pass-the-class--one-fresh-instance-per-operation-requires-strawberry-03160)'s
  release-wide floor **migration notes** (zero-argument construction,
  direct-instance deprecation, per-operation lifecycle; `uv.lock` + tests —
  not the open bound — pin semantics; the stale `optimizer/extension.py`
  `__init__` comment joins the Slice-1 file map); a **two-phase failure
  policy** in [Error shapes](#error-shapes) (setup fail-loud after
  `ExitStack` unwind; post-execution diagnostic failures caught as
  `Exception`, logged, degrading the payload — never replacing the real
  result — with the generic-recovery claim qualified to
  stash-published-only); the **cursor-construction capture-interval
  boundary** documented in Decision 4 / Edge cases (Django selects the
  wrapper at `connection.cursor()` time and never re-checks — pre-opened
  and retained cursors are named boundary cases, not fixed by a wrap port);
  and the Slice-3 wrap re-ordered **DB-mutations → Done flip →
  `import_spec_terms` → GLOSSARY/TREE renders → KANBAN renders → `--check`
  modes**, with the glossary flips enumerated from the companion terms CSV.
  Also folded: transaction scope narrowed to brackets completing inside the
  hook (enclosing `ATOMIC_REQUESTS` excluded); a real sharded-tier capture
  proof (scenario 16); experimental incremental execution and
  `inc_thread_sharing()` cross-thread wrappers excluded explicitly;
  sibling-hook SQL ordering documented and tested; the `original_error`
  walk gains a 64-hop ceiling with deterministic stop; the enabled-cost
  language replaced with exact complexity/retention wording; the async
  follow-on's false universal-executor premise corrected
  (`ThreadSensitiveContext` is per-request under ASGI HTTP — a prototype,
  not prose, decides the follow-on); the security disclosure enumerates
  interpolated SQL values, traceback paths, retention, and downstream
  copies; targeted pytest commands gain the coverage-free
  `-o addopts="-v -n0"` override; the Strawberry floor gains a durable CI
  node (`.github/workflows/django.yml` joins the file map); live scenarios
  gain their `django_db` / `django_db(transaction=True)` markers and
  scenario 3 its full permitted-writer + required-`categoryId` setup;
  scenario 13 drops threaded ORM in favor of exception/identity markers;
  and scenarios 17–21 add the non-interference, cursor-lifetime,
  transaction-boundary, sibling-order, and hop-policy regressions. Two
  findings required no spec change, recorded so they are not re-litigated:
  the settings-lookup concern (F12) does not occur — this spec introduces
  no settings key, and the shipped `conf.py` / `types/relay.py` split is
  correct as-is; and the temporary fail-loud stub needs no import-guard
  test (F21) — `pyproject.toml` already excludes `raise
  NotImplementedError` from coverage, so the staged
  `tests/extensions/test_debug.py` guard is deleted rather than kept.

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the
vocabulary used throughout the spec:

- [Response-extensions debug middleware][glossary-response-extensions-debug-middleware]
  — the subject. The glossary already pins the planned contract: Django
  query-log SQL
  and raised exceptions surfaced through the GraphQL response's `extensions`
  envelope so frontend clients can read them without the toolbar. Slice 2
  updates the entry body to the implemented contract; Slice 3 flips the
  status to `shipped (0.0.14)`.
- [`DjangoDebugExtension`][glossary-djangodebugextension] — the public,
  off-by-default class exported from `django_strawberry_framework.extensions`;
  the entry is the shortest route from the import path to the complete
  response payload, lifecycle, and security contracts.
- [Strawberry extension lifecycle][glossary-strawberry-extension-lifecycle] /
  [Per-operation extension isolation][glossary-per-operation-extension-isolation] /
  [Debug payload availability][glossary-debug-payload-availability] /
  [Response-extension merge semantics][glossary-response-extension-merge-semantics]
  — the four engine boundaries a new implementer must keep together:
  `on_operation` teardown, one instance per operation, the pre-execution
  no-key rule, and extension-list merging, async context-result precedence,
  and replacement of an existing `ExecutionResult.extensions` map.
- [Django debug-cursor capture][glossary-django-debug-cursor-capture] /
  [Reference-counted cursor coordinator][glossary-reference-counted-cursor-coordinator] /
  [Bounded query-log rollover][glossary-bounded-query-log-rollover] /
  [Async SQL-capture boundary][glossary-async-sql-capture-boundary] — the SQL
  capture mechanism and its correctness limits: concrete-wrapper-identity
  overlap-safe restore, best-effort bounded-log slicing, no `callproc()`
  capture, nested-sync cross-attribution, and thread-local async fidelity.
- [Debug SQL row][glossary-debug-sql-row] /
  [Debug exception row][glossary-debug-exception-row] — the two concrete
  wire-row contracts under `extensions.debug`, including the deliberate SQL
  field narrowing and terminal `GraphQLError.original_error` walk.
- [Masking-extension ordering][glossary-masking-extension-ordering] /
  [Developer-only debug posture][glossary-developer-only-debug-posture] —
  the LIFO ordering requirement and the security boundary created by exposing
  raw exception and interpolated-SQL details to clients.
- [Graphene debug migration][glossary-graphene-debug-migration] /
  [Cookbook parity][glossary-cookbook-parity] — the exact project-level move
  from `_debug` plus `DjangoDebugMiddleware` to the extension class, validated
  against the working cookbook rather than a hypothetical app.
- [Probe URLconf][glossary-probe-urlconf] — the repository test pattern that
  gives this opt-in schema shape real HTTP coverage without enabling it in
  fakeshop's shipped aggregate schema.
- [Hard dependency][glossary-hard-dependency] — the positive dependency
  posture behind this card's zero-new-dependency claim: Django and Strawberry
  are always installed, so their debug-cursor and extension APIs need no
  optional-import boundary.
- [Debug-toolbar middleware][glossary-debug-toolbar-middleware] — the landed
  `0.0.14` sibling ([`DONE-042-0.0.14`][kanban]) this card is documented
  against: that entry's "Distinct from" paragraph already names this card as
  the in-response counterpart; both mechanisms coexist, and this spec touches
  none of the toolbar's machinery.
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] — the
  package's only existing `SchemaExtension` and the structural precedent this
  module follows (engine-owned base, package-owned hooks) **and** deliberately
  diverges from on lifecycle: the optimizer is a module-level singleton in a
  factory because its [plan cache][glossary-plan-cache] is cross-request
  state; the debug extension has no cross-request state, so its opt-in is the
  class form
  ([Decision 6](#decision-6--opt-in-shape-pass-the-class--one-fresh-instance-per-operation-requires-strawberry-03160)).
- [Joint version cut][glossary-joint-version-cut] — the rule this card
  discharges rather than defers: `041` / `042` / `043` all landed with their
  bumps deferred to the last `0.0.14` card, and this is that card
  ([Decision 12](#decision-12--this-card-completes-the-joint-0014-cut-and-owns-the-version-bump)).
- [Live-first coverage mandate][glossary-live-first-coverage-mandate] — the
  test-placement rule
  [Decision 11](#decision-11--test-strategy-split-live-http-behavior-from-package-tier-mechanics)
  applies directly: a probe URLconf is still a live fakeshop GraphQL API test,
  so request-visible behavior lives in `examples/fakeshop/test_query/` even
  though the shipped aggregate schema remains off by default. Only serializer
  and lifecycle mechanics that an HTTP request cannot isolate remain in
  `tests/extensions/`.
- [Schema reload discipline][glossary-schema-reload-discipline] — the fixture
  obligation this card's request-driving live tests inherit: any test that
  builds a schema against fakeshop types calls the single-sited
  [`schema_reload.reload_all_project_schemas()`][schema-reload] machinery so
  registry state never leaks across collection orders.
- [`seed_data`][glossary-seed-data] — the repo's seed-helper rule applied to
  the [Test plan](#test-plan): every products-backed scenario's first
  domain-setup line is `seed_data(1)` (or an explicit `seed_data(N)`) from
  `apps.products.services`.
- [`TestClient`][glossary-testclient] / [`GraphQLTestCase`][glossary-graphqltestcase]
  — the landed `0.0.14` HTTP test ergonomics; this card's request-driving
  tests post through [`TestClient`][glossary-testclient] (with
  `assert_no_errors=False` where a scenario expects a GraphQL error) instead
  of hand-rolled `client.post(...)` blocks.
- [`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter] — the
  landed `0.0.14` predecessor whose status flip Slice 3 carries; otherwise
  untouched (this card is HTTP-response surfacing, not transport).
- [Soft dependency][glossary-soft-dependency] — cited as the **contrast**:
  this card needs none of it. `strawberry.extensions.SchemaExtension` ships
  inside the package's hard `strawberry-graphql` dependency and the debug
  cursor inside Django itself, so there is no guard, no install hint, no
  [eviction-simulated absence][glossary-eviction-simulated-absence] fixture,
  and no [`require_optional_module`][glossary-require-optional-module] call —
  the second `0.0.14` card (after `043`) with a zero-dependency Slice 1.
- [Strictness mode][glossary-strictness-mode] — the adjacent-but-different
  diagnostic: strictness detects *unplanned lazy loads* (a specific failure);
  the debug extension reports *everything that executed* (a general
  observability surface). They compose — a strictness `OptimizerError` raised
  during execution surfaces in the debug payload's `exceptions` list like any
  other execution exception.
- [`only()` projection][glossary-only-projection] /
  [Multi-database cooperation][glossary-multi-database-cooperation] — noted
  because the debug payload makes both *visible*: the captured `sql` strings
  show the optimizer's projected column lists, and each row's `alias` field
  shows which database served it
  ([Decision 10](#decision-10--multi-database-capture-every-alias-in-connectionsall-one-bracket-each)).
- [`ConfigurationError`][glossary-configurationerror] — NOT used by this card
  (worth saying explicitly): the extension has no `Meta` surface, no settings
  key, and no constructor validation; there is no consumer configuration to
  reject. Misuse shapes are engine-owned (Strawberry's own extension
  machinery) or documented pass-throughs ([Error shapes](#error-shapes)).
- [`get_queryset` visibility hook][glossary-get-queryset] — untouched; noted
  because the captured SQL includes whatever the visibility hooks and the
  optimizer's `Prefetch` downgrades actually emitted — the debug payload is a
  read-only window, never a queryset participant.

## Goal and cookbook cross-reference

This design was checked against [`GOAL.md`][goal] and the working
`django-graphene-filters` cookbook rather than only against graphene-django's
debug implementation:

- **The north star is a modern Strawberry foundation without Graphene runtime
  baggage.** A Strawberry `SchemaExtension` is the engine-native aggregate
  configuration seam already demonstrated by [`GOAL.md`][goal]'s canonical
  schema (`extensions=[lambda: _optimizer]`). Requiring
  `strawberry-graphql>=0.316.0` for per-request extension isolation follows
  that foundation instead of building a compatibility runtime around an old
  engine race. This supports success criterion 7 (remove the source package)
  and the explicit non-goals "direct port of Graphene internals" and
  "Graphene compatibility runtime".
- **The recipe app does not own debug configuration.** The exact file named by
  the working-reference link,
  [`cookbook/recipes/schema.py`][upstream-cookbook-recipes-schema], defines
  only the domain nodes and `Query`. The project aggregate
  [`cookbook/schema.py`][upstream-cookbook-schema] composes that query, imports
  `DjangoDebug`, and adds `_debug`;
  [`cookbook/settings.py`][upstream-cookbook-settings] separately installs
  `DjangoDebugMiddleware`. The Strawberry port preserves
  that ownership boundary: app schemas remain untouched and the aggregate
  `strawberry.Schema(...)` owns the one debug opt-in.
- **The migration is capability-equivalent, not wire-compatible.** A Graphene
  cookbook consumer removes the aggregate `_debug` field and the
  `GRAPHENE["MIDDLEWARE"]` entry, then adds `DjangoDebugExtension` to the
  Strawberry aggregate schema. Debugging clients stop selecting `_debug` and
  read `response.extensions.debug`. This is a deliberate exception to
  success criterion 7's "only the import line changes" migration promise,
  and the spec is precise about the exception's ground: the `_debug` wire
  contract *could* be preserved without any Graphene runtime (the
  Strawberry-native schema-field facade recorded as the fallback in
  [Risks](#risks-and-open-questions)), so the reason it is not preserved is
  [Decision 3](#decision-3--exposure-the-response-extensions-map-under-the-debug-key-not-a-schema-level-_debug-field)'s
  rejection of a permanent schema surface — not the goal's
  no-Graphene-runtime constraints. Because criterion 7 as written carves
  out no such case, Slice 2 carries the corresponding [`GOAL.md`][goal]
  clarification: the import-only promise covers `Meta`-driven domain
  declarations; project-level engine configuration (a schema's
  `extensions=` list, the `GRAPHENE` settings block) migrates by documented
  recipe.
- **The payload still proves core success criteria.** Captured SQL makes
  success criterion 5's automatic ORM optimization visible, including
  `select_related` / `prefetch_related` / `only()` behavior, while exception
  rows expose failures from the declarative permission and mutation surfaces
  in criteria 4 and 6 without participating in their execution.
- **The tests belong to the target example.** `GOAL.md` names fakeshop as the
  shipped proof project. Therefore real debug-enabled HTTP behavior belongs
  in `examples/fakeshop/test_query/`; package-tier tests cover only lifecycle
  mechanics that a request cannot isolate
  ([Decision 11](#decision-11--test-strategy-split-live-http-behavior-from-package-tier-mechanics)).

The resulting cookbook migration is a **debug-only delta applied after the
cookbook's broader Strawberry port** — [`GOAL.md`][goal]'s "Cookbook parity"
target example, whose ported aggregate `cookbook/schema.py` takes the
canonical shape [`config/schema.py`][config-schema] demonstrates today
(`finalize_django_types()`, `_optimizer = DjangoOptimizerExtension()`,
`strawberry.Schema(query=Query, config=strawberry_config(),
extensions=[lambda: _optimizer])`). That baseline port — a separate effort
this card does not own — supplies the `strawberry` / `strawberry_config`
imports, the `_optimizer` construction, and the `Query` conversion; this
card's delta is only the debug lines. On the Graphene side, shown against
the original [`cookbook/schema.py`][upstream-cookbook-schema], the aggregate
field goes:

```diff
- from graphene_django.debug import DjangoDebug

  class Query(
      cookbook.recipes.schema.Query,
      graphene.ObjectType,
  ):
-     debug = graphene.Field(DjangoDebug, name="_debug")
```

with the [`cookbook/settings.py`][upstream-cookbook-settings] entry deleted:

```diff
- "MIDDLEWARE": ("graphene_django.debug.DjangoDebugMiddleware",),
```

and on the Strawberry side, one entry is added to the ported aggregate's
`extensions=` list:

```diff
+ from django_strawberry_framework.extensions import DjangoDebugExtension

  schema = strawberry.Schema(
      query=Query,
      config=strawberry_config(),
-     extensions=[lambda: _optimizer],
+     extensions=[lambda: _optimizer, DjangoDebugExtension],
  )
```

(The complete consumer recipe with every import spelled out is in
[User-facing API](#user-facing-api).) No recipe-app `DjangoType`, sidecar
`Meta`, visibility hook, or domain query field changes for debug. That is the
package goal's ownership model applied to the real cookbook, not a
hypothetical migration.

## Slice checklist

Each top-level item maps to one commit / PR. **Three slices: the extension +
tests (Slice 1), implemented-contract docs while the card remains WIP
(Slice 2), and the joint `0.0.14` cut + final card wrap (Slice 3).** The card
is an M — the module is one `SchemaExtension` subclass
plus a serializer helper riding two engine seams, and the weight is in the
decision hygiene around the two "pick one" choices and in the joint cut's
doc breadth.

- [ ] **Slice 1 — `extensions/` subpackage + `extensions/debug.py` + split
  live/mechanics tests**
  - [ ] **The engine isolation correction rides the first commit**:
        `[project].dependencies` raises `strawberry-graphql>=0.262.0` to
        `strawberry-graphql>=0.316.0`, and `uv.lock` is re-resolved. The old
        floor caches the sync extension list on `Schema._sync_extensions`, so
        even a class entry becomes one shared instance whose
        `execution_context` races across requests. Installed `0.316.0`
        materializes classes/factories in `Schema.get_extensions()` for every
        operation. Record both source inspections and run the concurrent sync
        isolation scenario at the new floor in an isolated throwaway venv
        (never the shared `.venv`, and with the coverage-free
        `-o addopts=...` override — [Test plan](#test-plan)) before calling
        the floor supported. The floor must also be **durably exercised**,
        not a one-time throwaway run: the existing minimum-support CI node in
        [`.github/workflows/django.yml`][workflow-django] force-installs
        exactly `strawberry-graphql==0.316.0` and runs the suite with
        coverage disabled (the latest node keeps the coverage gate); at
        minimum a repeatable floor job installs the dev dependencies,
        force-installs `0.316.0`, records the resolved versions, and runs the
        lifecycle/isolation node ID
        ([Decision 6](#decision-6--opt-in-shape-pass-the-class--one-fresh-instance-per-operation-requires-strawberry-03160)).
        This is a constraint bump, not a new dependency;
        `[dependency-groups].dev` remains untouched. The package's own
        `uv.lock` version entry still moves only in Slice 3 with the cut.
  - [ ] `django_strawberry_framework/extensions/__init__.py` (new) — the
        subpackage docstring (the [`docs/TREE.md`][tree] render fails on a
        missing module docstring) and the `DjangoDebugExtension` re-export in
        `__all__`
        ([Decision 5](#decision-5--symbol-and-home-djangodebugextension-in-extensionsdebugpy-exported-from-the-extensions-subpackage--never-the-package-root)).
  - [ ] `django_strawberry_framework/extensions/debug.py` (new) —
        `DjangoDebugExtension(SchemaExtension)`: the sync `on_operation`
        generator (pre-yield: acquire the module-private reference-counted
        debug-cursor bracket + snapshot per alias in `connections.all()`
        through `contextlib.ExitStack`, so partial setup unwinds;
        post-yield, inside `finally`: materialize and slice
        each alias's `queries_log`, serialize the SQL rows
        ([Decision 8](#decision-8--the-sql-row-shape-graphenes-wire-names-narrowed-to-what-djangos-log-supports)),
        collect the terminal exceptions from each result error's nested
        `original_error` chain — cycle-safe and `None`-guarded for the
        pre-execution teardown paths
        ([Decision 9](#decision-9--exception-capture-the-results-original_error-chain-serialized-like-graphenes-wrap_exception--no-resolver-wrapping)) —
        stash the payload, and release every bracket token so the final
        overlapping operation restores the original `force_debug_cursor`
        value), plus the idempotent `get_results()`
        returning `{"debug": <stash>}` when the stash exists and `{}`
        otherwise
        ([Decision 7](#decision-7--hook-shape-one-sync-on_operation-generator-assembly-at-teardown-get_results-returns-the-stash)).
        Module shape per [DRY D4–D6](#helper-reuse-obligations-dry): the
        `_SLOW_QUERY_SECONDS` constant, the two module-level wire
        serializers, one `None`-guarded exception collector, one two-seam
        bracket coordinator (lock + active-capture map), one log-slice
        helper, one payload builder — and no `__init__`.
        Module + symbol docstrings state the off-by-default posture, the
        class-form opt-in, the dev-only security caveat with the full
        disclosure surface (unmasked exceptions, **interpolated SQL
        parameter values**, traceback file paths, in-process query-log
        retention, downstream response copies), the
        masking-extension ordering (list the debug class after `MaskErrors`),
        `callproc()` omission, the cursor-construction capture-interval
        boundary (pre-opened and retained cursors), the transaction-boundary
        scope (resolver-owned `atomic()` in, enclosing `ATOMIC_REQUESTS`
        out), nested-sync attribution boundary, and the async
        SQL caveat
        ([Edge cases](#edge-cases-and-constraints)).
  - [ ] `examples/fakeshop/test_query/test_debug_extension_api.py` (new) —
        request-visible scenarios from the [Test plan](#test-plan), posting
        real HTTP through a probe URLconf mounting a debug-enabled schema over
        the fakeshop apps (the [`test_multi_db.py`][test-multi-db] plumbing
        precedent), under the shared schema-reload + `seed_data` disciplines
        and through [`TestClient`][glossary-testclient].
  - [ ] `tests/extensions/test_debug.py` (new) — request-impossible mechanics
        only: serializers and nested error-chain handling, saved-value restore
        and bounded-log behavior, no-stash/idempotent results, masking order,
        async exception shape, and concurrent sync request isolation
        ([Decision 11](#decision-11--test-strategy-split-live-http-behavior-from-package-tier-mechanics)).
  - [ ] `tests/extensions/__init__.py` (new) — the package marker and
        `TODO(spec-044 Slice 1)` placement anchor, matching every sibling test
        package; it exports no test helpers.
  - [ ] Every new symbol carries its docstring and any
        staged-but-not-implemented seam carries a `TODO(spec-044 Slice N)`
        source anchor per [`AGENTS.md`][agents]; `uv run ruff format .` /
        `ruff check --fix .` after the edit, no pytest run unless the
        maintainer asks.
- [ ] **Slice 2 — implemented-contract docs (card remains WIP; no version
  bump)**
  - [ ] [`docs/GLOSSARY.md`][glossary] — the
        [Response-extensions debug middleware][glossary-response-extensions-debug-middleware]
        entry body updated to the implemented contract (import path, the
        class-form opt-in, the `debug` key, the six SQL fields and the named
        omissions, the exception triple, the debug-cursor mechanism and its
        `DEBUG`-independence, the dev-only caveat, the async SQL caveat, and
        the real cookbook migration (remove `_debug`, remove
        `DjangoDebugMiddleware`, add the extension class, read
        `response.extensions.debug`));
        via the glossary app's **database** + a
        [`scripts/build_glossary_md.py`][build-glossary-md] re-render, never
        a hand-edit of the generated file. The status stays `planned for
        0.0.14` in this slice — Slice 3 flips it with the cut.
  - [ ] [`docs/TREE.md`][tree] regenerated via
        [`scripts/build_tree_md.py`][build-tree-md] (never hand-edited): the
        `extensions/` and `tests/extensions/` rows move from `planned by
        TODO-ALPHA-044-0.0.14` to the real docstring-derived rows (the
        kanban `TrackedPath` rows flip `is_current=True` at the DB so the
        exports agree).
  - [ ] [`config/schema.py`][config-schema] — the module docstring's "The
        graphene-only `DjangoDebug` field has no direct Strawberry analogue
        and is left out for now" sentence is now false; reword it to name
        the shipped `DjangoDebugExtension` and fakeshop's deliberate
        opt-out
        ([Decision 2](#decision-2--card-scope-boundary-the-extension-ships-alone--no-django-middleware-no-schema-field-no-fakeshop-always-on-wiring)).
  - [ ] [`GOAL.md`][goal] — success criterion 7 gains the one-sentence
        scoping clarification: the "only the import line changes" promise
        covers `Meta`-driven domain declarations; project-level engine
        configuration (a schema's `extensions=` list, the `GRAPHENE`
        settings block) migrates by documented recipe
        ([Goal and cookbook cross-reference](#goal-and-cookbook-cross-reference)).
- [ ] **Slice 3 — the joint `0.0.14` cut + final card wrap**
  - [ ] The version quintet: `[project].version` in
        [`pyproject.toml`][pyproject] → `0.0.14`; `__version__` in
        [`__init__.py`][init]; [`tests/base/test_init.py::test_version`][test-base-init];
        the [`docs/GLOSSARY.md`][glossary] package-version line; the
        `django-strawberry-framework` `version` entry in `uv.lock`.
  - [ ] The GLOSSARY status flips to `shipped (0.0.14)` for **all four**
        `0.0.14` surfaces — [`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter]
        (plus its [Channels request adapter][glossary-channels-request-adapter]
        and [`require_optional_module`][glossary-require-optional-module]
        companions), [Debug-toolbar middleware][glossary-debug-toolbar-middleware],
        [`TestClient`][glossary-testclient] /
        [`GraphQLTestCase`][glossary-graphqltestcase], and
        [Response-extensions debug middleware][glossary-response-extensions-debug-middleware]
        — plus the [Joint version cut][glossary-joint-version-cut] entry's
        "in force for `0.0.14`" wording updated to record the applied cut;
        all through the glossary DB + re-render.
  - [ ] [`README.md`][readme] / [`docs/README.md`][docs-readme] — the
        "Already landed on `main` ahead of the `0.0.14` release" framing and
        the "Coming next — remaining alpha (`0.0.14`)" list resolve into the
        shipped-`0.0.14` status wording (the Status section's version line,
        the newest-shipped-surface paragraph, and the shipped-capability
        bullets for the router, the toolbar middleware, the test-client
        family, and this extension).
  - [ ] [`TODAY.md`][today] — the "Shipped package capabilities not
        exercised by products" section currently lists only the `0.0.14`
        router (`DONE-041`, already in shipped tense); the cut **adds** the
        missing `0.0.14` capabilities — the toolbar middleware, the
        test-client family, and this extension — in the section's
        established shipped-tense shape (there is no "planned" phrasing to
        flip); the file's products-centric scope is otherwise untouched.
  - [ ] `CHANGELOG.md` — the `0.0.14` release section covering all four
        cards. Per [`AGENTS.md`][agents] #"Do not update CHANGELOG.md unless
        explicitly instructed", this edit needs explicit permission: **this
        spec's Slice 3 grants it** for exactly the `0.0.14` release section,
        per the [`docs/SPECS/NEXT.md`][next] convention that the owning
        spec's release slice carries the grant; the maintainer's commit
        review remains the final gate.
  - [ ] **Only after every preceding cut item succeeds**, wrap the card in
        the **DB-mutations-first, renders-last** order (the importer writes
        glossary-link rows the KANBAN builders render, so rendering before
        importing would ship stale generated artifacts):
        1. apply all remaining card, `SpecDoc`, `TrackedPath`,
           glossary-status, and version DB updates — the GLOSSARY status
           flips cover **every** spec-044 glossary term whose `planned for
           0.0.14` status changes, derived from the companion
           `docs/spec-044-debug_extension-0_0_14-terms.csv`, not only the
           four headline release surfaces;
        2. flip `044` → Done with the `DONE-044-0.0.14` id and its
           `SpecDoc` pointing at this spec (the importer processes only
           Done cards);
        3. run `manage.py import_spec_terms` for the companion terms CSV;
        4. render [`docs/GLOSSARY.md`][glossary] and [`docs/TREE.md`][tree]
           after their final DB mutations (`TrackedPath.is_current`
           synchronized for all new files/directories first);
        5. render [`KANBAN.md`][kanban] / `KANBAN.html` via
           [`scripts/build_kanban_md.py`][build-kanban-md] /
           `build_kanban_html.py` **after** the terms import (never a
           hand-edit);
        6. finish with every available importer/builder `--check` mode
           after the last DB mutation.

## Problem statement

When a GraphQL request misbehaves — too many queries, a slow query, or an
execution exception — the developer's first question is "what did
this operation actually execute?", and today the package has no in-response
answer. The [Debug-toolbar middleware][glossary-debug-toolbar-middleware]
(`0.0.14`, landed) answers it **server-side**: a browser panel over
`/graphql/` traffic, gated on `DEBUG` / `INTERNAL_IPS`, invisible to the
JavaScript client that issued the request. `graphene-django` ships the
complementary mechanism this card ports: its
[`DjangoDebugMiddleware`][upstream-debug-middleware] accumulates SQL recorded
by its own instrumentation and raised resolver exceptions into a
[`DjangoDebug`][upstream-debug-types] object **inside the GraphQL response
itself**, so frontend clients and Apollo DevTools read the diagnosis from the
payload they already have. A `graphene-django` migrant loses that surface at
the door — against [`GOAL.md`][goal] success criterion 7 (migrate "without
bringing the source package along") — and `strawberry-graphql-django` offers
nothing to borrow back (the card verified its absence), so the package must
supply its own Strawberry-native equivalent.

The Strawberry-native shape is small and the card names it: a
`SchemaExtension` that captures SQL and exceptions for the in-flight
operation and attaches them to the response's `extensions` map under the
`debug` key. The design weight is in the two choices the card flags as "pick
one before writing the spec" — the **exposure mechanism** (response-extensions
map vs. graphene's schema-level `_debug` field) and the **fidelity mechanism**
(port graphene's thread-local cursor wrap vs. read `connection.queries`) —
plus the lifecycle questions a response-extensions surface inherits from the
engine: where the payload is assembled relative to Strawberry's
`get_results` call ordering, how instrumentation brackets Django's
thread-local connections without depending on `settings.DEBUG`, and how the
opt-in composes with the package's documented optimizer-singleton pattern
without inheriting its shared-instance hazards.

## Current state

A true description of the repo as this spec is authored:

- **The package ships exactly one `SchemaExtension`.**
  [`optimizer/extension.py`][optimizer-extension] —
  [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] — is the
  structural precedent: engine base `strawberry.extensions.SchemaExtension`,
  package-owned hooks (`on_execute`, `resolve`), module-level singleton
  wrapped in a factory to preserve its cross-request
  [plan cache][glossary-plan-cache]. No `extensions/` subpackage exists; the
  optimizer lives under `optimizer/`.
- **[`docs/TREE.md`][tree] reserves the module.** The target package layout
  carries `extensions/ # planned by TODO-ALPHA-044-0.0.14` with
  `debug.py` under it, and the target test tree carries `tests/extensions/
  # planned by TODO-ALPHA-044-0.0.14`. The regenerated tree resolves both in
  Slice 2.
- **The fakeshop project schema names this card's absence.**
  [`config/schema.py`][config-schema]'s module docstring reads "The
  graphene-only `DjangoDebug` field has no direct Strawberry analogue and is
  left out for now" — written when the aggregate schema was first composed.
  This card creates the analogue; the sentence gets rewritten in Slice 2
  (fakeshop still deliberately does not enable the extension,
  [Decision 2](#decision-2--card-scope-boundary-the-extension-ships-alone--no-django-middleware-no-schema-field-no-fakeshop-always-on-wiring)).
- **The engine seams are present, at a hard dependency.**
  [`strawberry/extensions/base_extension.py`][venv-base-extension] (installed
  strawberry 0.316.0) defines `SchemaExtension` with the `on_operation`
  lifecycle generator hook and the `get_results()` seam;
  [`strawberry/extensions/runner.py`][venv-runner] merges every extension's
  `get_results()` dict into one map; and
  [`strawberry/schema/schema.py`][venv-schema] assigns that completed map as
  the `ExecutionResult.extensions` the HTTP layer serializes into the
  response JSON, replacing rather than merging any pre-existing result map.
  Among extension outputs, later entries win same-key collisions; on async
  execution only, `ExecutionContext.extensions_results` is then overlaid and
  has final precedence. **Call-ordering fact this spec builds on** (verified
  in the 0.316.0
  source, both colors): on the happy path the final
  `get_extensions_results_sync()` / `await get_extensions_results(...)` runs
  **after** the `operation()` context exits — i.e. after `on_operation`'s
  post-yield teardown — while on the early parse-error and validation-error
  returns it runs **inside** the operation context (the `return` expression
  evaluates before the `with` unwinds), i.e. **before** teardown. So a
  payload assembled at teardown is present for every executed operation and
  absent for parse and validation failures. (One narrow third path: the
  engine's generic coerced-exception handlers — both colors — sit *outside*
  the operation context, so an operation aborted by a non-GraphQL exception
  that escapes the hooks returns an error response *with* the `debug` key,
  reflecting whatever executed before the abort. [Error
  shapes](#error-shapes) records it.)
  ([Decision 7](#decision-7--hook-shape-one-sync-on_operation-generator-assembly-at-teardown-get_results-returns-the-stash)).
  Extension classes passed in `extensions=` are instantiated **per
  operation** (`schema.py::Schema.get_extensions` `#"ext()"`) at the new
  `strawberry-graphql>=0.316.0` floor. The old `0.262.0` floor cached
  `Schema._sync_extensions`, sharing both extension state and the engine-set
  `execution_context` across sync requests; that upstream race is why this
  card must raise the floor rather than merely verify hook names
  ([Decision 6](#decision-6--opt-in-shape-pass-the-class--one-fresh-instance-per-operation-requires-strawberry-03160)).
  Strawberry calls each class/factory with no execution-context argument and
  then assigns `extension.execution_context` before runner construction;
  `SchemaExtension.__init__` does not perform that binding
  ([Decision 7](#decision-7--hook-shape-one-sync-on_operation-generator-assembly-at-teardown-get_results-returns-the-stash)).
- **Django's own debug cursor is the fidelity source, and it is not
  `DEBUG`-bound.** [`django/db/backends/base/base.py`][venv-django-base]
  `#"queries_logged"` enables query logging when `force_debug_cursor` is set
  **or** `settings.DEBUG` is true; each connection keeps a bounded
  `queries_log` deque (`maxlen` = `queries_limit`, default 9000).
  [`django/db/backends/utils.py`][venv-django-utils] `::CursorDebugWrapper`
  logs, per `execute()`, the **interpolated** statement
  (`use_last_executed_query=True` → `self.db.ops.last_executed_query(...)`)
  and a `"%.3f"`-formatted duration; `executemany()` logs the raw
  parameterized SQL prefixed `"<N> times: "`. `CursorDebugWrapper` does not
  instrument `callproc()`, so stored-procedure calls produce no log row and
  are outside this extension's SQL contract.
  [`django/test/utils.py`][venv-django-test-utils]
  `::CaptureQueriesContext` is the canonical bracket: save
  `force_debug_cursor`, set it `True`, snapshot the log index, and restore on
  exit — the exact mechanism
  [Decision 4](#decision-4--fidelity-djangos-own-debug-cursor-via-a-force_debug_cursor-bracket-not-a-cursor-wrap-port)
  adopts. Under `pytest-django` the suite runs `DEBUG=False`, so an
  implementation that read bare `connection.queries` without the bracket
  would capture nothing in every test and in every production-shaped
  deployment — the trap the bracket exists to close.
- **The upstream source is read, in full.** The card's seven
  `Verified in upstream` files
  ([`debug/__init__.py`][upstream-debug-init],
  [`middleware.py`][upstream-debug-middleware],
  [`types.py`][upstream-debug-types], [`sql/types.py`][upstream-sql-types],
  [`sql/tracking.py`][upstream-sql-tracking],
  [`exception/types.py`][upstream-exception-types],
  [`exception/formating.py`][upstream-exception-formating]) are the borrowing
  ground truth; the [Borrowing posture](#borrowing-posture) section names
  what each contributes and what is deliberately not carried.
- **HTTP test ergonomics exist.** [`DONE-043-0.0.14`][kanban] shipped
  [`TestClient`][glossary-testclient]; this card's request-driving tests use
  it rather than re-spelling the POST-decode pattern its spec just deleted
  from the suites. The probe-URLconf plumbing this card's tests need — a
  per-test schema over freshly-reloaded fakeshop types behind a module-level
  `urlpatterns` — is already proven in
  [`test_multi_db.py`][test-multi-db] `#"_current"`.
- **The version line reads `0.0.13`, and this card is the joint cut's last
  leg.** [`DONE-041-0.0.14`][kanban], [`DONE-042-0.0.14`][kanban], and
  [`DONE-043-0.0.14`][kanban] all landed with their bumps deferred to the
  [joint `0.0.14` cut][glossary-joint-version-cut]; `044` is the only
  non-Done card at `0.0.14`, so the cut lands here
  ([Decision 12](#decision-12--this-card-completes-the-joint-0014-cut-and-owns-the-version-bump)).

## Goals

1. **The response carries its own diagnosis.** With the extension enabled, a
   consumer (or Apollo DevTools) reads `extensions.debug.sql` — one row per
   new `queries_log` entry produced by Django's instrumented
   `execute()` / `executemany()`, plus transaction boundaries whose logging
   completes while the debug hook is active (an enclosing
   `ATOMIC_REQUESTS` / middleware transaction brackets the view outside the
   hook and is excluded, [Edge cases](#edge-cases-and-constraints)), with
   vendor / alias / logged SQL / duration; `CursorDebugWrapper` does not
   instrument `callproc()`, so stored-procedure calls are outside this
   contract —
   and `extensions.debug.exceptions` — one row per execution exception
   represented by graphql-core's `original_error` chain,
   with type / message / stack — from the same JSON payload that carried
   `data`
   ([Decision 3](#decision-3--exposure-the-response-extensions-map-under-the-debug-key-not-a-schema-level-_debug-field),
   [Decision 8](#decision-8--the-sql-row-shape-graphenes-wire-names-narrowed-to-what-djangos-log-supports),
   [Decision 9](#decision-9--exception-capture-the-results-original_error-chain-serialized-like-graphenes-wrap_exception--no-resolver-wrapping)).
2. **Ordinary non-overlapping sync capture is deterministic, not
   `DEBUG`-dependent.** The `force_debug_cursor` bracket makes the same
   ordinary sync operation produce the same capture under `DEBUG=True` dev
   servers, `DEBUG=False` test runs, and production-shaped settings —
   enabling the extension is the only switch; nested same-thread operations
   share one log and therefore cross-attribute rows
   ([Decision 4](#decision-4--fidelity-djangos-own-debug-cursor-via-a-force_debug_cursor-bracket-not-a-cursor-wrap-port)).
3. **Off by default, one-line opt-in, zero new dependencies.** Absent from
   the `extensions=` list, **no debug instrumentation runs and no `debug`
   response key is added**; present (as the class), every executed operation
   on that schema carries the payload, while parse and validation failures
   follow the documented no-key rule. No package is added and no dev-group
   or settings key changes;
   the existing Strawberry requirement is raised to `>=0.316.0` for
   per-request isolation. The floor raise is deliberately **not** claimed as
   a debug-only no-op: it is a release-wide engine lifecycle change that
   applies to every consumer schema whether or not the extension is enabled
   ([Decision 6](#decision-6--opt-in-shape-pass-the-class--one-fresh-instance-per-operation-requires-strawberry-03160)'s
   migration notes,
   [Decision 2](#decision-2--card-scope-boundary-the-extension-ships-alone--no-django-middleware-no-schema-field-no-fakeshop-always-on-wiring)).
4. **A graphene migrant recognizes the shape.** The row field names are
   graphene's own wire names (`vendor`, `alias`, `sql`, `duration`,
   `isSlow`, `isSelect`; `excType`, `message`, `stack`), the `is_slow`
   threshold keeps graphene's 10-second constant, and every narrowed-away
   field is named in the docs rather than silently absent
   ([Decision 8](#decision-8--the-sql-row-shape-graphenes-wire-names-narrowed-to-what-djangos-log-supports)).
5. **It composes with the optimizer.** A schema carrying both extensions
   works, and the debug payload becomes the optimizer's demonstration
   surface: the captured row list *shows* the optimizer's planned
   **visibility-safe two-query shape** — exactly one `products_item` slice
   plus one `products_category` prefetch, no per-item category queries —
   where a naive resolver chain would show N+1. Not a joined single query:
   `CategoryType` defines a custom `get_queryset` visibility hook, so the
   optimizer deliberately downgrades the forward FK to a `Prefetch` rather
   than `select_related` (the shipped rule the existing live proof
   `test_products_api.py::test_products_optimizer_merges_duplicate_root_field_nodes_over_http`
   already pins) ([Test plan](#test-plan) scenario 2).
6. **The `0.0.14` release becomes real.** Slice 3 aligns the version quintet
   and flips the release-status wording for all four `0.0.14` cards — the
   joint cut the three predecessors deferred
   ([Decision 12](#decision-12--this-card-completes-the-joint-0014-cut-and-owns-the-version-bump)).

## Non-goals

- **A Django (or Graphene) middleware.** The card's title word "middleware"
  is graphene's name for its resolver-wrapping callable; the card's own
  Architectural posture pins our shape as a Strawberry `SchemaExtension`
  under `extensions/`, and nothing in this card touches `MIDDLEWARE`,
  request/response objects, or the [Debug-toolbar
  middleware][glossary-debug-toolbar-middleware]'s machinery.
- **A schema-level `_debug` field.** graphene's pay-for-what-you-select
  exposure is rejected with reasons in
  [Decision 3](#decision-3--exposure-the-response-extensions-map-under-the-debug-key-not-a-schema-level-_debug-field);
  no `DjangoDebug` GraphQL type, no Query field, no schema surface at all.
- **A port of graphene's cursor wrap.** No `sql/tracking.py` equivalent —
  no `NormalCursorWrapper`, no `ExceptionCursorWrapper` /
  `SQLQueryTriggered` (a django-debug-toolbar templates-panel artifact with
  no consumer here), no package-owned thread-local state
  ([Decision 4](#decision-4--fidelity-djangos-own-debug-cursor-via-a-force_debug_cursor-bracket-not-a-cursor-wrap-port)).
  Consequently no Postgres-specific `transId` / `transStatus` / `isoLevel` /
  `encoding` fields and no `rawSql` / `params` / `startTime` / `stopTime` —
  the documented narrowing
  ([Decision 8](#decision-8--the-sql-row-shape-graphenes-wire-names-narrowed-to-what-djangos-log-supports)).
- **Fakeshop always-on wiring.** The shipped [`config/schema.py`][config-schema]
  does not enable the extension: an always-on debug payload would tax every
  acceptance response, bloat every live suite's decoded body, and misteach
  the off-by-default posture the card pins. A future opt-in (the fakeshop
  activation card is the natural host) can replace the probe URLconf with the
  shipped URLconf while the request tests remain in the live tier
  ([Decision 11](#decision-11--test-strategy-split-live-http-behavior-from-package-tier-mechanics)).
- **Production gating knobs.** No `is_slow` threshold argument, no
  redaction hooks, no per-request enable predicate, no settings key — the
  v1 class needs no constructor or configuration, and the dev-only posture is
  documentation ([Edge cases](#edge-cases-and-constraints)). The absent
  settings key is a decision, not a gap: `conf.py` keys exist only where a
  knob must vary per deployment without code changes
  (`NESTED_CONNECTION_STRATEGY`, `TESTING_ENDPOINT`); a debug tool toggled
  at schema construction adds no such case. Knobs are
  follow-on material once a real consumer asks
  ([Risks](#risks-and-open-questions)).
- **Subscriptions.** The package ships no subscription surface; the
  extension's contract is pinned for query / mutation operations. Whatever
  Strawberry's subscription lifecycle does with `get_results` is untested
  and undocumented here.
- **Experimental incremental execution (`@defer` / `@stream`).** With
  Strawberry's `enable_experimental_incremental_execution` config,
  `Schema._handle_execution_result` returns incremental result objects
  before the ordinary extension-result assignment — the two-list,
  one-final-map contract does not define which of the initial and
  subsequent payloads would carry debug data. The `0.0.14` contract covers
  **non-incremental query/mutation `ExecutionResult`s only**; no
  transport-universal behavior is implied until incremental payload
  semantics are designed and tested (a follow-on, not a v1 promise).
- **Async SQL-capture fidelity.** Exception capture is
  execution-color-agnostic; SQL capture is guaranteed on the ordinary
  non-reentrant sync execution path and documented as **typically empty**
  under async execution, where
  Django's per-thread connections mean the `sync_to_async` executor
  threads' queries escape a bracket set from the event-loop thread — the
  same thread-local constraint graphene's own wrap carries. The
  async-instrumentation follow-on is named in
  [Risks](#risks-and-open-questions), not shipped here.

## Borrowing posture

Per the [`START.md`][start] "do both libraries provide it?" test this card is
**single-upstream, Required**: ⚛️ `graphene-django` ships the subsystem; 🍓
`strawberry-graphql-django` verifiably does not (the card's own grep-backed
claim), so the package claims parity with the single upstream and records the
absence plainly — the [Single-upstream parity][glossary-single-upstream-parity]
posture spec-040 / spec-041 / spec-042 established. All seven upstream files
the card names were read in full for this spec; every borrow below cites the
source directly, not memory.

### From `graphene-django` — the payload shapes and their semantics

- **The two-list payload.** [`types.py`][upstream-debug-types]'s
  `DjangoDebug` carries exactly `sql: [DjangoDebugSQL]` and
  `exceptions: [DjangoDebugException]`. Borrowed as the `debug` map's two
  keys — always both present, each a (possibly empty) list.
- **The SQL row.** [`sql/types.py`][upstream-sql-types] pins the field
  vocabulary. Borrowed where Django's own log can honestly populate them:
  `vendor` (connection vendor string), `alias` (the Django database alias),
  `sql` (the recorded query-log statement — graphene also logs
  `ops.last_executed_query`, so the semantics match, not just the name),
  `duration` (seconds, float), `isSlow` (graphene's `duration > 10`
  constant, kept verbatim), `isSelect` (graphene's
  `sql.lower().strip().startswith("select")` sniff, kept verbatim). The wire
  casing is camelCase because that is what a graphene client actually
  receives (graphene auto-camelCases `is_slow` → `isSlow` at the GraphQL
  boundary; this payload IS the wire, so it carries the wire form).
- **The exception row.** [`exception/types.py`][upstream-exception-types] +
  [`exception/formating.py`][upstream-exception-formating]: `excType` =
  `force_str(type(exception))` (the `"<class 'ValueError'>"` form — kept
  byte-compatible), `message` = `force_str(exception)`, `stack` =
  `"".join(traceback.format_exception(...))`. Borrowed as the serializer,
  minus `force_str` (plain `str` suffices — the values are Python
  exception reprs, not Django lazy strings; a lazy translation proxy inside
  an exception message still stringifies correctly through `str`).
- **The accumulate-then-attach lifecycle idea.**
  [`middleware.py`][upstream-debug-middleware]'s `DjangoDebugContext`
  instruments at operation start and disables at completion. Borrowed as the
  `on_operation` bracket — the Strawberry-native home for exactly that
  lifecycle.

### From Django itself — the capture mechanism

- **The debug-cursor bracket.** [`django/test/utils.py`][venv-django-test-utils]
  `::CaptureQueriesContext.__enter__` / `__exit__`: save
  `force_debug_cursor`, set `True`, snapshot the log length, restore on
  exit. Borrowed as the per-connection bracket, applied to every alias in
  `connections.all()` (which is also graphene's own
  `enable_instrumentation` loop shape). This is the load-bearing sharpening
  of the card's "`connection.queries`" default: the bare property is empty
  under `DEBUG=False`, the bracket is not.

### Explicitly do not borrow

- **The Graphene resolver-middleware mechanism.** graphene wraps every
  field resolution and detects the `DjangoDebug`-typed field to know when to
  finalize (`info.schema.get_type("DjangoDebug") == info.return_type`); our
  exposure has no schema field to detect and the operation hook brackets the
  whole execution in one place. Wrapping every resolver to accumulate
  results graphene-style would re-implement what `result.errors` already
  carries.
- **The thread-local cursor wrap** ([`sql/tracking.py`][upstream-sql-tracking]) —
  rejected in
  [Decision 4](#decision-4--fidelity-djangos-own-debug-cursor-via-a-force_debug_cursor-bracket-not-a-cursor-wrap-port);
  with it go `rawSql` / `params` / `startTime` / `stopTime`, the four
  Postgres fields, and the `ExceptionCursorWrapper` / `recording()` /
  `SQLQueryTriggered` templates-panel machinery (dead weight even upstream —
  it exists for a django-debug-toolbar panel graphene does not ship).
- **The `context.django_debug` writable-context requirement.** graphene
  stores its accumulator on `info.context` and hard-fails on non-writable
  contexts; a per-operation extension instance IS the accumulator, so the
  consumer's context object is never touched.
- **The `DjangoDebug` / `DjangoDebugSQL` / `DjangoDebugException` GraphQL
  object types.** The payload is a plain JSON map inside `extensions` — no
  Strawberry types, no schema surface, nothing introspectable
  ([Decision 3](#decision-3--exposure-the-response-extensions-map-under-the-debug-key-not-a-schema-level-_debug-field)).
- **graphene's `sql` backwards-compatibility comment and Postgres
  transaction-ID logger protocol** (`self.logger.get_transaction_id(alias)`)
  — coupled to the cursor wrap; gone with it.

## User-facing API

Enabling the extension — the class goes in the `extensions=` list beside the
optimizer's factory (the two lifecycles differ deliberately,
[Decision 6](#decision-6--opt-in-shape-pass-the-class--one-fresh-instance-per-operation-requires-strawberry-03160)):

```python
import strawberry

from django_strawberry_framework import (
    DjangoOptimizerExtension,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.extensions import DjangoDebugExtension

finalize_django_types()

_optimizer = DjangoOptimizerExtension()
schema = strawberry.Schema(
    query=Query,
    config=strawberry_config(),
    extensions=[
        lambda: _optimizer,     # singleton-in-a-factory: preserves the plan cache
        DjangoDebugExtension,   # the CLASS: one fresh instance per operation
    ],
)
```

([`finalize_django_types`][glossary-finalize-django-types] and
[`strawberry_config`][glossary-strawberry-config] are the standard
schema-setup pieces, unchanged by this card — shown so the example is a
complete consumer recipe.)

Every operation executed through that schema then carries the payload:

```json
{
  "data": {
    "allItems": {
      "edges": [
        {
          "node": {
            "name": "Widget"
          }
        }
      ]
    }
  },
  "extensions": {
    "debug": {
      "sql": [
        {
          "vendor": "sqlite",
          "alias": "default",
          "sql": "SELECT \"products_item\".\"id\", \"products_item\".\"name\" FROM \"products_item\" ORDER BY \"products_item\".\"id\" ASC LIMIT 2",
          "duration": 0.001,
          "isSlow": false,
          "isSelect": true
        }
      ],
      "exceptions": []
    }
  }
}
```

A resolver that raises populates the second list (and the standard GraphQL
`errors` still appear — the debug payload adds the server-side detail the
spec-compliant `errors` entry deliberately omits):

```json
{
  "data": {
    "boom": null
  },
  "errors": [
    {
      "message": "division by zero",
      "path": [
        "boom"
      ]
    }
  ],
  "extensions": {
    "debug": {
      "sql": [],
      "exceptions": [
        {
          "excType": "<class 'ZeroDivisionError'>",
          "message": "division by zero",
          "stack": "Traceback (most recent call last):\n  ..."
        }
      ]
    }
  }
}
```

Consumer-visible behavior:

- **The payload appears for every executed operation** on an enabled schema
  — queries and mutations, with data or with errors, including
  introspection (whose `sql` list is simply empty). It does **not** appear
  for parse or validation failures (a syntax error, an unknown-field
  validation error): nothing executed, so there is nothing to report
  (one narrow exception — the engine's coerced-exception recovery path —
  is recorded in [Error shapes](#error-shapes))
  ([Decision 7](#decision-7--hook-shape-one-sync-on_operation-generator-assembly-at-teardown-get_results-returns-the-stash)).
- **`sql` rows are Django's own `queries_log` entries, per alias.** Each row reports
  the connection's `vendor` and `alias`, the interpolated statement Django's
  debug cursor logged, and Django's measured duration (3-decimal precision —
  the log stores `"%.3f"`). Rows appear in per-connection log order,
  concatenated across aliases in `connections.all()` order. Instrumented
  `execute()` / `executemany()` and transaction statements are in scope;
  stored-procedure calls through `callproc()` are absent because Django's
  `CursorDebugWrapper` does not log them.
- **`exceptions` rows are execution exceptions**, not GraphQL validation
  errors: an entry appears when a `result.errors` member carries an
  `original_error`. This includes resolver-thrown Python exceptions,
  explicitly raised `GraphQLError`s, and engine-raised completion or scalar
  serialization exceptions. A query for a nonexistent field produces a
  GraphQL error but no `exceptions` row. This is intentionally a little
  broader than graphene's resolver-only middleware and is the honest cost of
  using Strawberry's operation result instead of wrapping every field.
- **The two keys are always both present** when the payload appears —
  `{"sql": [], "exceptions": []}` for a no-op operation — so client code
  indexes without existence checks.
- **Combining with a masking extension is order-sensitive.** Hook
  teardowns unwind LIFO, and Strawberry's `MaskErrors` rewrites
  `result.errors` with `original_error=None` in *its* teardown — so the
  unmasked `exceptions` rows appear only when `DjangoDebugExtension` is
  listed **after** the masking extension (torn down first, reading the
  originals). Listed before it, the debug teardown sees only stripped
  errors and reports `exceptions: []`
  ([Decision 9](#decision-9--exception-capture-the-results-original_error-chain-serialized-like-graphenes-wrap_exception--no-resolver-wrapping),
  [Edge cases](#edge-cases-and-constraints)); the docstring states the
  required ordering.
- **Nothing else about the response changes.** The extension never mutates
  the queryset, the context, or the result's `data` / `errors`; it is a
  read-only window, and its diagnostic collection is forbidden from
  replacing an already-produced result even when serialization fails
  ([Error shapes](#error-shapes)). With the extension absent, no debug
  instrumentation runs and no `debug` key is added. (That is the precise
  claim — not "byte-identical to `0.0.13`": the release's Strawberry-floor
  raise is a separate, engine-wide lifecycle change that applies with or
  without the extension,
  [Decision 6](#decision-6--opt-in-shape-pass-the-class--one-fresh-instance-per-operation-requires-strawberry-03160)'s
  migration notes.)

### Error shapes

- **A raised execution exception** — unchanged GraphQL behavior (the error
  appears in `errors`, masked or not per the consumer's other extensions)
  plus one `exceptions` row carrying the **unmasked** type / message /
  stack (when the debug extension is ordered after any masking extension —
  the LIFO teardown dependency,
  [User-facing API](#user-facing-api) /
  [Edge cases](#edge-cases-and-constraints)). That asymmetry is the
  feature (the client-visible diagnosis) and the security caveat in one:
  the extension is a development tool and its docstring says so — never
  enable it on an internet-facing schema
  ([Edge cases](#edge-cases-and-constraints)).
- **A parse or validation failure** — the standard GraphQL `errors`
  response with **no** `debug` key (nothing executed; the engine calls
  `get_results` before the hook's teardown on those paths, and the
  extension deliberately returns `{}` rather than a half-initialized
  payload).
- **A coerced non-GraphQL exception** — the engine's generic recovery
  handlers (both colors) sit *outside* the operation context: an exception
  escaping the hooks or the executor (the sync parse handler catches only
  `GraphQLError`, so a non-`GraphQLError` parse crash lands here too) is
  coerced to a GraphQL error **after** teardown ran, so that error response
  carries the `debug` key **when the debug hook was entered and its
  teardown completed enough to publish the stash** — an earlier sibling
  hook's setup failure can abort before the debug hook ever enters, in
  which case no stash exists and the key is absent; the qualified claim is
  the honest one. Generic recovery alone does not imply two
  `get_results()` calls.
  Two calls occur only when an early parse/validation return has already
  evaluated `_handle_execution_result` (and therefore `get_results()`), then
  an `on_operation` teardown raises while that return unwinds: the outer
  recovery handler abandons the first return and builds a replacement,
  invoking `get_results()` again. The method is therefore pinned idempotent:
  return the stash, never mutate or pop it
  ([Decision 7](#decision-7--hook-shape-one-sync-on_operation-generator-assembly-at-teardown-get_results-returns-the-stash),
  Test plan scenario 11).
- **An exception inside the extension's own machinery** — governed by an
  explicit **two-phase failure policy**, because an exception escaping
  `on_operation` teardown makes Strawberry abandon the real result and
  construct a replacement `PreExecutionError`: a "read-only window" that
  can discard the operation's `data` / `errors` through a diagnostic
  serialization failure would betray its own contract.
  - **Setup (pre-`yield`) stays fail-loud**: an acquisition failure
    propagates after `ExitStack` restores every previously acquired
    wrapper — nothing executed yet, so no result is at risk.
  - **Teardown (post-execution) never replaces the result**: query-log
    materialization, snapshot slicing, SQL-row serialization, exception
    stringification, and traceback formatting are wrapped so a failure is
    caught as `Exception` (never `BaseException`), logged server-side, and
    **degrades** the payload to whatever rows serialized successfully (or
    an empty list) — the wire contract is unchanged (a completed payload
    still owns both `sql` and `exceptions` lists; no third error shape),
    and the original `data` / `errors` survive (Test plan scenario 17).
  The known pre-execution corner remains designed-in: on the sync
  parse/validation paths teardown runs during the early return's unwind
  with `execution_context.result` still unset, so the exception collector
  is `None`-guarded by contract
  ([Decision 9](#decision-9--exception-capture-the-results-original_error-chain-serialized-like-graphenes-wrap_exception--no-resolver-wrapping));
  an unguarded read would raise out of the `with`-unwind and the engine
  would coerce *that* into the response, discarding the real parse error.
  Independently, the restore of every connection's `force_debug_cursor`
  rides a `finally` so no failure mode can leave a connection permanently
  instrumented — flag restoration and result preservation are separately
  protected.
- **A consumer extension also publishing a `debug` extensions key** — among
  extension outputs, the runner merges `get_results()` dicts in
  extensions-list order ([`runner.py`][venv-runner] `#"data.update"`), so
  the later-listed extension wins. On async execution,
  `ExecutionContext.extensions_results` is overlaid afterward and has final
  precedence; the sync runner has no equivalent overlay. Schema result
  handling assigns the completed map rather than merging a pre-existing
  `ExecutionResult.extensions` map. Documented, not guarded: the key is the
  card's pinned contract and namespacing it away from a hypothetical
  collision would break the graphene-shaped expectation.

## Architectural decisions

### Decision 1 — Spec filename and canonical naming

This spec lives at `docs/spec-044-debug_extension-0_0_14.md`: card NNN `044`,
topic slug `debug_extension` (the card's subject as shipped — a debug
`SchemaExtension`), version segment `0_0_14` from the card's trailing
`-0.0.14`. Follows the [`docs/SPECS/NEXT.md`][next] convention.

Alternatives considered (and rejected):

- **`spec-044-response_extensions_debug-0_0_14.md`.** Rejected: the long
  slug restates the mechanism twice (`response_extensions` + `debug`); the
  established slug style is short subject-first (`debug_toolbar`,
  `channels_router`, `test_client`).
- **`spec-044-debug_middleware-0_0_14.md`.** Rejected: "middleware" is the
  card title's graphene-inherited word, and the card's own Architectural
  posture disavows it for our shape — naming the file after the rejected
  shape would mislead every future grep.

### Decision 2 — Card-scope boundary: the extension ships alone — no Django middleware, no schema field, no fakeshop always-on wiring

This card ships exactly one consumer-facing unit: `DjangoDebugExtension` and
its subpackage home, plus tests and docs. Three adjacent-looking pieces stay
out:

- **No Django middleware and no toolbar coupling.** The
  [Debug-toolbar middleware][glossary-debug-toolbar-middleware] is a
  different mechanism over a different seam (the HTTP response), already
  landed; this card adds no `MIDDLEWARE` entry, imports nothing from
  `middleware/`, and shares no code with it. The two are documented as
  complements — the card's own DoD row ("Documented as the response-side
  counterpart to `DONE-042-0.0.14`").
- **No schema surface.** No GraphQL type, no Query field, no `Meta` key, no
  finalizer participation — the extension is invisible to introspection
  ([Decision 3](#decision-3--exposure-the-response-extensions-map-under-the-debug-key-not-a-schema-level-_debug-field)).
- **No fakeshop always-on wiring.** The shipped
  [`config/schema.py`][config-schema] does not add the extension: it would
  change every acceptance response's body and pay capture cost on every
  live test, and it would misrepresent the off-by-default posture in the
  package's own showcase. Slice 2 rewrites the docstring sentence that
  claimed no analogue exists; the example's opt-in is future work
  ([Decision 11](#decision-11--test-strategy-split-live-http-behavior-from-package-tier-mechanics),
  [Out of scope](#out-of-scope-explicitly-tracked-elsewhere)).

Justification: the card is an M and each excluded piece has its own owner —
the toolbar card is Done, the schema-field exposure is a rejected
alternative, and the fakeshop activation line item already exists on the
beta board. Alternatives considered (and rejected): **bundling a fakeshop
demo field or dev-settings toggle** — rejected as scope creep that turns a
one-module card into an example-project design discussion; the probe-URLconf
tests demonstrate the wiring shape a consumer copies.

### Decision 3 — Exposure: the response-`extensions` map under the `debug` key, not a schema-level `_debug` field

The payload rides `ExecutionResult.extensions["debug"]` via the engine's
`get_results()` seam — the card's proposed Strawberry-native shape and its
named default. graphene's alternative exposure is a schema-level field
(consumers add `_debug: DjangoDebug` to their Query type and select
`{ _debug { sql { duration } } }`), which buys per-query selectivity at the
cost of schema surface.

Grounds:

1. **It is the engine's purpose-built seam.** `SchemaExtension.get_results`
   exists exactly to attach per-operation metadata to the response
   (`ApolloTracingExtension` upstream uses it the same way); the HTTP layer
   serializes `extensions` without any package code touching the view,
   so the surface works over every transport that returns an
   `ExecutionResult` — the Django view, `schema.execute_sync`, the async
   `schema.execute`, and the [`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter]'s
   consumers alike.
2. **No schema pollution and no `Meta` growth.** A `_debug` field would need
   a package-owned GraphQL type, a finalizer hook or a consumer-authored
   field declaration on every Query, and documentation of its interplay with
   introspection-driven tooling — permanent public surface for a
   development-time diagnostic. The extensions map is invisible to the
   schema contract.
3. **The GraphQL spec reserves `extensions` for exactly this** ("reserved
   for implementors to extend the protocol however they see fit") — client
   tooling (Apollo DevTools, GraphiQL) already renders unknown extensions
   keys.
4. **The card pre-picked it.** The card's proposed shape and its "default
   both to the simpler choice" instruction both name the extensions map;
   this decision confirms rather than re-litigates.
5. **It preserves the real cookbook's ownership boundary.** The requested
   [`recipes/schema.py`][upstream-cookbook-recipes-schema] contains no debug
   field or middleware coupling. Debug is added only by the project aggregate
   [`cookbook/schema.py`][upstream-cookbook-schema], with middleware installed
   separately in [`cookbook/settings.py`][upstream-cookbook-settings]. The
   Strawberry aggregate schema's `extensions=` list replaces both project
   integration points without changing any recipe-app domain type or `Meta`
   surface, matching [`GOAL.md`][goal]'s working-reference posture.

Alternatives considered (and rejected):

- **The graphene schema-level `_debug` field.** Rejected: everything in
  ground 2, plus a mechanism problem — a field resolver cannot know when the
  operation's *other* fields have finished executing, which is why graphene
  needs its promise-chained `get_debug_result()` dance
  ([`middleware.py`][upstream-debug-middleware] `::DjangoDebugContext`); the
  operation hook gets completion for free. The selectivity loss (the map is
  all-or-nothing per enabled schema, where graphene consumers pull only
  `{ _debug { sql } }` per query) is real and recorded in
  [Risks](#risks-and-open-questions).
- **Both at once.** Rejected: two exposure surfaces for one payload doubles
  the documentation and test matrix for zero new capability; a future card
  can add the field flavor over the same capture core if a consumer asks.

### Decision 4 — Fidelity: Django's own debug cursor via a `force_debug_cursor` bracket, not a cursor-wrap port

The SQL source is Django's per-connection `queries_log`, enabled for the
operation's duration by the [`CaptureQueriesContext`][venv-django-test-utils]
mechanism: for each configured connection, save `force_debug_cursor`, set it
`True`, and record `len(connection.queries_log)`. This extension performs the
same transition through the reference-counted coordinator pinned in
[Decision 7](#decision-7--hook-shape-one-sync-on_operation-generator-assembly-at-teardown-get_results-returns-the-stash):
the first active bracket saves and enables the flag, overlapping brackets
increase its depth, and the final release restores the saved value. Each
extension instance owns its own log-length snapshot; at teardown it
materializes and slices the log from that index. This is the card's named
default ("`connection.queries`"), sharpened in one load-bearing way: the extension
**owns the instrumentation flag** instead of relying on `settings.DEBUG`
having populated the log, because bare `connection.queries` is empty under
`DEBUG=False` — which is every `pytest-django` run and every
production-shaped deployment. An extension that silently returned
`{"sql": []}` outside dev servers would fail its one job in exactly the
environments where enabling it is a deliberate act.

**The capture interval is defined by cursor construction, not only by
operation entry/exit.** Django selects the wrapper class in
`BaseDatabaseWrapper._prepare_cursor()` when `connection.cursor()` is
called — `queries_logged` is read **once**, at cursor creation, and
`CursorDebugWrapper.execute()` never re-checks it. Two boundary cases
follow, documented rather than papered over: a normal cursor **created
before** the hook entered stays uninstrumented even when executed during
the operation, and a debug cursor created while the flag was true **remains
a debug wrapper** — if a consumer retains it, executions after the hook
restored the flag keep appending to `queries_log`. The SQL guarantee
therefore covers the normal case — short-lived cursors acquired while the
operation hook is active (every ORM call opens and closes its own cursor) —
and the two long-lived-cursor directions are pinned by Test plan
scenario 18 and named in the class docstring, [Edge
cases](#edge-cases-and-constraints), and the GLOSSARY entry. Flag
restoration is the coordinator's job; it does not by itself define a
perfect logging interval, and porting the rejected cursor wrap to "fix"
this would abandon the chosen Django-native fidelity source.

Grounds:

1. **No package-owned cursor instrumentation.** Django's
   `CursorDebugWrapper` is
   maintained, backend-aware (it logs `ops.last_executed_query`, the same
   interpolated form graphene logs), and already battle-tested by every
   `assertNumQueries` in the ecosystem. The package adds a bracket, not a
   wrapper. The bracket has one module-private coordination map protected by
   `threading.Lock`: overlapping brackets on the same connection increment a
   depth and only the last release restores the original flag. Entries exist
   only while active and are deleted at depth zero. This state is required to
   make async teardown order-independent; it never observes or transforms a
   query.
2. **Thread-safety story equals graphene's.** Django connections are
   thread-local; the bracket instruments the calling thread's connections —
   the same scope graphene's own thread-local wrap has (its
   [`middleware.py`][upstream-debug-middleware] `::enable_instrumentation`
   loops `connections.all()` from the calling thread too, handing each
   connection to [`sql/tracking.py`][upstream-sql-tracking]'s
   single-connection `wrap_cursor`). No new hazard is
   introduced and none is fixed; the async caveat is shared and documented
   ([Edge cases](#edge-cases-and-constraints)).
3. **The narrowing is honest and bounded.** What the log lacks —
   `rawSql`, `params`, `startTime` / `stopTime`, and the four
   Postgres-transaction fields — is exactly the card's anticipated "shape
   narrowing (e.g., omitted Postgres-specific fields)", documented
   explicitly per its DoD
   ([Decision 8](#decision-8--the-sql-row-shape-graphenes-wire-names-narrowed-to-what-djangos-log-supports)).
4. **The card pre-picked it** ("default both to the simpler choice ...
   `connection.queries`").

Alternatives considered (and rejected):

- **Port graphene's cursor wrap** ([`sql/tracking.py`][upstream-sql-tracking]).
  Rejected: it buys the four omitted timing/params fields and the Postgres
  quartet at the price of package-owned monkey-patching of
  `connection.cursor` (with the attendant unwrap-ordering hazards the
  package already defends *against* elsewhere — the
  [Django Trac #37064 hardening][glossary-django-trac-37064] exists because
  cursor/connection wrapping goes wrong in the wild), a thread-local state
  module, and a per-vendor conditional block. The fidelity delta serves a
  minority diagnostic need; the follow-on path stays open (the capture core
  is one private function swap away from a richer source) and is recorded in
  [Risks](#risks-and-open-questions).
- **Read bare `connection.queries` without the bracket.** Rejected: the
  `DEBUG=False` silent-empty trap above — a correctness bug dressed as
  simplicity.
- **Wrap with `CaptureQueriesContext` instances directly.** Rejected on
  three grounds worth recording: (a) `CaptureQueriesContext.__enter__` calls
  `connection.ensure_connection()` eagerly, which would open a database
  connection on every alias for every operation — including aliases the
  operation never touches (fakeshop's sharded mode has two); (b) `__enter__`
  also disconnects the process-global `request_started → reset_queries`
  signal and `__exit__` reconnects it
  ([`django/test/utils.py`][venv-django-test-utils]
  `#"reset_queries_disconnected"`) — per-operation toggling of global signal
  state, with overlapping operations racing the reconnect; (c) its
  save/restore is a single-context shape with no overlap reference counting,
  so two overlapping operation contexts on one connection would restore out
  of order — the exact failure the coordinator exists to prevent. The
  extension reuses the class's *semantic contract* — save the flag, enable
  logging, snapshot the log length, restore the saved value — without its
  test-oriented connection and signal side effects; an untouched alias
  contributes zero rows and zero connections.

### Decision 5 — Symbol and home: `DjangoDebugExtension` in `extensions/debug.py`, exported from the `extensions` subpackage — never the package root

The class is `DjangoDebugExtension`, defined in
`django_strawberry_framework/extensions/debug.py` (the card's predicted
path), re-exported from `django_strawberry_framework.extensions` (a new
subpackage `__init__.py` with a docstring and `__all__ =
["DjangoDebugExtension"]`). Nothing is added to the package root's
`__all__` or `__getattr__`.

Grounds:

1. **The name follows the package's own extension precedent** —
   [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] — and
   says what it is (a Django-aware debug `SchemaExtension`), where
   graphene's `DjangoDebugMiddleware` name would import the wrong mechanism
   word and `DjangoDebug` is graphene's *output type* name (reusing it for
   a class that is not a GraphQL type invites exactly the confusion the
   distinct name avoids).
2. **The subpackage-not-root export matches the package's opt-in
   geography.** The root's public surface is the always-on schema-building
   API; every optional or specialized surface lives one level down
   (`testing/`, `auth/`, `middleware/`, `routers`). The optimizer is root
   because it is the recommended default for every consumer; a debug
   diagnostic is not. The import line
   `from django_strawberry_framework.extensions import DjangoDebugExtension`
   also mirrors the graphene migrant's muscle memory
   (`from graphene_django.debug import DjangoDebugMiddleware` — subpackage
   there too).
3. **Eager re-export, no lazy machinery.** `extensions/__init__.py` imports
   `debug.py` directly: the module's imports are `django.db` and
   `strawberry` (both hard dependencies), so there is no
   [soft-dependency][glossary-soft-dependency] boundary to defend and a
   [PEP 562 lazy export][glossary-pep-562-lazy-export] would be ceremony
   without a payer. The file mirrors the package's eager-subpackage export
   shape — docstring + explicit re-export + `__all__`, as
   `utils/__init__.py` and `testing/__init__.py` do; no wildcard, no
   `__getattr__`. (`middleware/__init__.py`'s deliberate *no*-re-export
   marker is the soft-dependency contrast, not the precedent here — its
   emptiness exists to keep an optional import boundary this subpackage
   does not have.)

Alternatives considered (and rejected):

- **Package-root export beside `DjangoOptimizerExtension`.** Rejected per
  ground 2 — and the asymmetry is informative rather than confusing: the
  import path itself signals "this one is not part of the default recipe".
- **`optimizer/debug.py`.** Rejected: the debug extension is not optimizer
  machinery (it reports *all* SQL, planned or not) and the card's predicted
  path pins `extensions/`; parking it under `optimizer/` would also block
  the `extensions/` subpackage the target tree already reserves.
- **Naming the module `extensions/debug_extension.py`.** Rejected: the
  subpackage already says `extensions`; `debug.py` matches upstream
  strawberry-django's `middlewares/debug_toolbar.py` leaf-naming style the
  package adopted for `middleware/debug_toolbar.py`.

### Decision 6 — Opt-in shape: pass the class — one fresh instance per operation requires Strawberry 0.316.0

The documented opt-in is `extensions=[DjangoDebugExtension]` (the class
object; a zero-argument factory is equivalently correct). At the required
`strawberry-graphql>=0.316.0` floor, Strawberry instantiates non-instance
entries per operation ([`schema.py`][venv-schema] `::Schema.get_extensions`
`#"ext()"`), so each operation gets a fresh instance and the extension keeps
its per-operation state (the per-alias snapshots and assembled payload) as
plain instance attributes.

Grounds:

1. **Per-operation state demands per-operation instances.** The engine
   assigns `extension.execution_context` per request and the hook stores
   capture state between pre-yield and teardown; on a shared instance two
   concurrent operations would interleave those writes. The optimizer
   tolerates the shared-singleton pattern because its per-request state
   rides `ContextVar`s and `info.context` — machinery this extension does
   not need if it simply is not shared.
2. **The old floor is provably unsafe for this design.** Strawberry 0.262.0
   and verified 0.315.3 cache class-created sync extensions on
   `Schema._sync_extensions`. Concurrent requests then overwrite the same
   instance's engine-owned `execution_context`, so a response can expose a
   sibling request's exception payload. Strawberry 0.316.0 removes that
   cache and constructs classes/factories per request. A `ContextVar` inside
   this extension cannot repair the engine's shared `execution_context`
   attribute, so the root fix is the floor bump. This is the exact upstream
   race reported and fixed in [Strawberry issue #4369][upstream-strawberry-extension-isolation].
3. **The two patterns differ for a stated reason, in the same code
   example.** The optimizer's factory exists to preserve its cross-request
   [plan cache][glossary-plan-cache]; the debug extension has no
   cross-request state, so the class form is both simpler and safer. The
   [User-facing API](#user-facing-api) example shows both side by side with
   the reason inline, and both docstrings state their own lifecycle.
4. **It is the engine's mainstream shape** — Strawberry's documentation and
   its own bundled extensions take classes in `extensions=`; instances are
   the deprecated path (the engine emits a `DeprecationWarning` for bare
   instances at `Schema.__init__`).

**Release/migration notes — the floor is a release-wide engine change, not
a debug-only no-op.** Raising `[project].dependencies` to
`strawberry-graphql>=0.316.0` changes engine behavior for every consumer
schema, including schemas that never import `DjangoDebugExtension`, and the
`0.0.14` docs must say so rather than claiming byte-identical behavior:

- pre-`0.316` sync execution **cached** extension instances; `0.316`
  constructs class/factory entries **per operation**, rebuilding the
  middleware manager each time;
- `0.316` invokes classes and factories with **zero arguments** and assigns
  `extension.execution_context` afterward — a consumer factory that relied
  on the old `execution_context=` call shape can fail after the upgrade;
- direct **instance** entries now draw a `DeprecationWarning` and a changed
  lifecycle.

The floor is justified — the old cached-sync lifecycle is unsafe for this
extension — but the honest wording is that `>=0.316.0` **excludes the known
cached-sync lifecycle**; an open lower bound does not "pin today's
semantics". What pins the resolved behavior is `uv.lock` plus the
regression tests (Test plan scenario 13 at the exact floor). The
`CHANGELOG.md` `0.0.14` section and the GLOSSARY entry carry these
migration notes ([Doc updates](#doc-updates)). One in-repo casualty of the
same change: `optimizer/extension.py`'s `__init__` comment still says
Strawberry instantiates extension classes *with* the `execution_context`
keyword — false at the new floor. The parameter stays (direct-construction
compatibility) but Slice 1 corrects the comment's rationale (the
[Implementation plan](#implementation-plan) carries the row).

Alternatives considered (and rejected):

- **Singleton-in-a-factory, ContextVar state (the optimizer's shape).**
  Rejected: buys nothing (there is no cache to preserve) and costs a
  ContextVar lifecycle with reset-token hygiene — machinery whose only
  consumer would be a usage pattern the docs steer away from anyway.
- **Retain `strawberry-graphql>=0.262.0` and rely on the class form.**
  Rejected: the sync path still caches the resulting instance before 0.316.0;
  class syntax alone does not provide isolation at the old floor.
- **Guard against shared instances at runtime** (e.g. detect a second
  concurrent `on_operation` on one instance and raise). Rejected: the
  engine already owns instance lifecycle and deprecation signaling for the
  bare-instance form; a package-side tripwire would fire only in the
  misuse case it documents away, and false-positive risk (serialized
  sequential operations on one instance are harmless) outweighs the catch.

### Decision 7 — Hook shape: one sync `on_operation` generator, assembly at teardown, `get_results` returns the stash

`DjangoDebugExtension` implements exactly two engine seams — and no
`__init__`. Strawberry constructs class/factory entries with no
execution-context argument, then `Schema.execute()` / `Schema.execute_sync()`
assigns `extension.execution_context` before creating the runner. No
constructor is needed because this class has no instance configuration, not
because the base constructor binds context
([DRY D6](#helper-reuse-obligations-dry)):

- **`on_operation`** — a **sync** generator: pre-yield it uses
  `contextlib.ExitStack` to acquire a reference-counted bracket token and
  snapshot for every
  alias ([Decision 4](#decision-4--fidelity-djangos-own-debug-cursor-via-a-force_debug_cursor-bracket-not-a-cursor-wrap-port),
  [Decision 10](#decision-10--multi-database-capture-every-alias-in-connectionsall-one-bracket-each));
  post-yield — inside a `try` / `finally` so restore always runs — it
  slices each alias's `queries_log`, serializes the SQL rows and the
  exceptions off `self.execution_context`, stashes the completed payload on
  the instance, and releases every token. The last overlapping token for a
  connection restores its saved `force_debug_cursor`.
- **`get_results`** — returns `{"debug": <stash>}` when the stash was
  assembled and `{}` otherwise — **idempotent** (a pure read of the stash:
  never a mutate-or-pop, never a write to `execution_context` or to an
  existing `ExecutionResult.extensions`): the early-result plus
  teardown-failure recovery path can invoke it twice for one operation
  ([Error shapes](#error-shapes)). The stash is one instance attribute
  whose absent sentinel is `None` — unambiguous because a completed payload
  is always a dict, even when both lists are empty. The sentinel's home is
  pinned concretely: one **immutable class-level default** (an annotated
  `_payload = None` on the class body), read directly by `get_results` and
  overridden on the instance only when teardown assigns the completed
  payload dict. That one default preserves every neighboring rule at once —
  no constructor duplicated from `SchemaExtension`
  ([DRY D6](#helper-reuse-obligations-dry)), no
  `getattr(self, "_payload", None)` fallback re-spelled at read sites, no
  separate has-payload boolean, no mutable class-level dict shared across
  instances, and no eager empty dict that would falsely publish `debug`
  before execution.

Grounds:

1. **A sync generator serves both execution colors.** The engine wraps a
   sync generator hook in `contextlib.contextmanager` and enters it
   synchronously on the async path's `AsyncExitStack` too
   ([`extensions/context.py`][venv-extensions-context] `::__aenter__`
   `#"enter_context"`); an `async def` hook would instead make sync
   execution fail (the sync `__enter__` raises `RuntimeError` for any
   async hook). One hook, both colors, no duplication.
2. **Teardown is the only point that is both complete and ordered.** The
   verified call ordering ([Current state](#current-state)): on the happy
   path `get_results` runs *after* teardown (stash ready); on pre-execution
   error paths it runs *before* teardown (stash absent → `{}` → no `debug`
   key). Assembling in `get_results` instead would sometimes observe a
   half-open bracket (the error paths), and assembling in `on_execute`'s
   teardown would miss nothing today but couples to a subtler ordering for
   zero gain — `on_operation` is the outermost, symmetric bracket.
3. **`ExitStack`-owned, overlap-safe restore is the non-negotiable part.**
   Whatever the operation did — including raising through the engine — connections must
   come back to their prior instrumentation state, or one enabled operation
   would leave `force_debug_cursor` stuck `True` process-wide (and, in a
   test run, silently corrupt every later `assertNumQueries`-style
   snapshot). `ExitStack` also unwinds aliases already acquired if a later
   alias fails during setup, before the hook reaches `yield`. The saved-value
   restore (not `False`) also keeps the bracket nestable inside a consumer's
   own `CaptureQueriesContext`; reference
   counting prevents overlapping async operation contexts from restoring the
   same loop-thread connection out of order. The coordinator behind the
   tokens is module-private with exactly two seams (`acquire` / `release` —
   [DRY D5](#helper-reuse-obligations-dry)), `ExitStack.callback(...)` wires
   each release declaratively, and the hook reads as the package's one
   established generator-hook idiom — the optimizer's `on_execute`
   acquire-pre-yield / `finally`-guarded reverse-order release — conformance
   a reviewer can see across both hooks, not shared code
   ([DRY D6](#helper-reuse-obligations-dry)).

Alternatives considered (and rejected):

- **Assemble inside `get_results`.** Rejected per ground 2: on the
  early-error paths it would read a bracket that has not restored yet, and
  it would need its own idempotence guard for the paths where the engine
  calls it after teardown anyway.
- **`resolve`-hook accumulation (graphene's mechanism).** Rejected: the
  per-resolver hook exists for per-field concerns; SQL is per-operation and
  exceptions already accumulate on the result. A `resolve` implementation
  would also put the extension on the engine's per-field hot path
  (`_implements_resolve` adds the middleware wrapper) for pure overhead.
- **An `async def on_operation` twin class** for async schemas. Rejected:
  ground 1 makes it unnecessary; the async-color SQL fidelity gap is a
  thread-locality property, not a hook-color property
  ([Edge cases](#edge-cases-and-constraints)), so an async hook would not
  close it anyway.

### Decision 8 — The SQL row shape: graphene's wire names, narrowed to what Django's log supports

Each captured `queries_log` entry serializes to a plain dict with exactly six
keys, in graphene's wire casing:

| Key | Value | graphene source |
| --- | --- | --- |
| `vendor` | `connection.vendor` (`"sqlite"`, `"postgresql"`, ...) | `DjangoDebugSQL.vendor` |
| `alias` | the connection's Django alias (`"default"`, `"shard_b"`, ...) | `DjangoDebugSQL.alias` |
| `sql` | the logged statement — interpolated via `ops.last_executed_query` for `execute()`; `"<N> times: <sql>"` raw form for `executemany()` (Django's own log format, verbatim) | `DjangoDebugSQL.sql` |
| `duration` | `float(entry["time"])` — seconds at Django's 3-decimal log precision | `DjangoDebugSQL.duration` |
| `isSlow` | `duration > 10` — graphene's constant, kept verbatim | `DjangoDebugSQL.is_slow` |
| `isSelect` | `sql.lower().strip().startswith("select")` — graphene's sniff, kept verbatim | `DjangoDebugSQL.is_select` |

Explicitly omitted, each because the chosen fidelity source
([Decision 4](#decision-4--fidelity-djangos-own-debug-cursor-via-a-force_debug_cursor-bracket-not-a-cursor-wrap-port))
does not carry it — the card's required "document any shape narrowing
explicitly", discharged here and mirrored in the GLOSSARY entry body:

- `rawSql` (the pre-interpolation statement) and `params` (JSON-encoded
  parameters) — Django's log stores only the final `sql` string.
- `startTime` / `stopTime` — the log stores only the duration; graphene's
  absolute `time()` stamps come from its own wrapper.
- The Postgres quartet `transId` / `transStatus` / `isoLevel` / `encoding` —
  cursor-wrap-only introspection of the psycopg connection.
- Stored-procedure calls through `callproc()` — Django's
  `CursorDebugWrapper` deliberately does not instrument `callproc()`, so the
  chosen `queries_log` source has no row to serialize.

The exception row carries graphene's triple, byte-compatible in form:
`excType` (`str(type(exc))`, the `"<class 'ValueError'>"` shape), `message`
(`str(exc)`), `stack` (`"".join(traceback.format_exception(type(exc), exc,
exc.__traceback__))`). The explicit traceback argument is load-bearing:
serialization happens after graphql-core's `except` block has finished, so
`traceback.format_exc()` would produce `NoneType: None`.

Grounds: the card's DoD pins "mirrors graphene's `DjangoDebugSQL` /
`DjangoDebugException` field names where the chosen fidelity supports them".
CamelCase is the *wire* form a graphene client actually parses (graphene's
schema auto-camelCases `is_slow` → `isSlow`; since this payload never passes
through a GraphQL type, the extension emits the wire form directly).
`duration` stays float-seconds (not the log's string) so client tooling can
compare and sum without parsing.

Alternatives considered (and rejected):

- **snake_case keys** (the Python-side names). Rejected: the payload is
  wire, not Python; a migrant's existing DevTools formatter reads `isSlow`.
- **Carrying `startTime` / `stopTime` measured by the extension around the
  whole operation.** Rejected: per-operation stamps on per-query rows would
  be actively misleading — worse than absent.
- **A `time` string field mirroring Django's raw log entry.** Rejected:
  duplicates `duration` in a worse type; anyone needing Django's exact
  string can reformat.
- **Deriving the camelCase keys through `utils/strings.graphql_camel_name`.**
  Rejected: the six keys are a **wire contract** — a graphene migrant's
  existing DevTools formatter parses these exact bytes — so they must not be
  a function of a casing helper's future acronym/underscore behavior. They
  are spelled as literals inside the one row serializer
  ([DRY D4](#helper-reuse-obligations-dry)), and the mechanics tests
  re-spell them as independent literals for the same reason
  ([Test plan](#test-plan)).

### Decision 9 — Exception capture: the result's `original_error` chain, serialized like graphene's `wrap_exception` — no resolver wrapping

At teardown the extension reads the operation's errors from
`self.execution_context` (the engine sets `.result` when execution ran;
`result.errors` carries the operation's `GraphQLError`s — and the read is
**`None`-guarded**, because on the sync parse/validation paths teardown
runs during the early return's unwind before any result exists,
[Error shapes](#error-shapes)) and serializes
**only** those members whose `original_error` is non-`None` —
Strawberry/graphql-core's marker distinguishing an execution exception from a
pure GraphQL validation error. Starting from that first original, a private helper
walks nested `GraphQLError.original_error` links to the terminal exception.
The walk is **doubly bounded**: an identity set terminates malformed cycles,
and a local maximum-hop constant (64 — `utils/typing.py`'s existing
`_MAX_TYPE_WRAPPER_DEPTH` ceiling, re-spelled locally) bounds a long acyclic
chain, which an identity set alone cannot (calling a cycle guard "bounded"
would conflict with the repository's Power-of-Ten loop discipline). The stop
behavior is deterministic: return the **last unique candidate seen** before
a repeated identity or the hop ceiling. The bound covers only the
`original_error` traversal — traceback cause/context formatting and string
byte size remain unbounded, acknowledged in [Edge
cases](#edge-cases-and-constraints)' cost language. The walk follows the
bounded-walk posture `utils/typing.py` pins for attribute-chain peels (never
a bare unbounded `while` loop) with a deliberately different failure policy
— stop and keep the best-effort terminal, so a malformed consumer exception
chain degrades to best-effort capture instead of failing the response — the
policy difference that keeps it a local helper rather than a shared
extraction ([DRY D6](#helper-reuse-obligations-dry)); Test plan scenario 21
pins a self-cycle, a multi-node cycle, and a long acyclic chain. A terminal
`GraphQLError` is retained: graphql-core uses that exact two-link shape when
a resolver explicitly raises `GraphQLError`, and graphene's resolver
middleware records it. Each match serializes via the
`wrap_exception`-shaped triple
([Decision 8](#decision-8--the-sql-row-shape-graphenes-wire-names-narrowed-to-what-djangos-log-supports)),
using the original exception's own `__traceback__` for `stack`.

Grounds:

1. **The engine already accumulates what graphene's middleware wraps every
   resolver to collect.** graphql-core attaches the raised exception to the
   located `GraphQLError`; wrapping resolvers to catch it first would be
   re-implementation with a hot-path cost
   ([Decision 7](#decision-7--hook-shape-one-sync-on_operation-generator-assembly-at-teardown-get_results-returns-the-stash)
   alternatives).
2. **The `original_error` filter and chain walk define a deliberate,
   documented widening from graphene.** Graphene's `on_resolve_error` fires
   only for resolver-raised exceptions; GraphQL
   validation errors never reach it. Requiring the outer result error's
   `original_error is not None` draws the same line: a bad selection yields
   `errors` but an empty `exceptions` list. Walking nested GraphQL wrappers
   then preserves the original Python exception, while retaining a terminal
   explicitly raised `GraphQLError` rather than misclassifying it as
   validation output. graphql-core also supplies `original_error` for
   execution-time completion and scalar serialization failures; those are
   included because result-level capture cannot distinguish them from
   resolver failures without adding the rejected per-field wrapper.
3. **Unmasked by design, stated loudly — and order-dependent, stated just
   as loudly.** The debug payload exposes the raw exception type, message,
   and stack even when a masking extension sanitizes `errors` — that is
   the tool's purpose and its danger; the docstring and GLOSSARY entry
   both carry the never-in-production caveat
   ([Edge cases](#edge-cases-and-constraints)). The guarantee holds only
   under the LIFO teardown ordering: `MaskErrors` rewrites `result.errors`
   with `original_error=None` in its own `on_operation` teardown, so the
   debug class must be listed **after** it in `extensions=` (torn down
   first, reading the originals); listed before it, the filter finds
   nothing and `exceptions` reads `[]` — documented in the
   [User-facing API](#user-facing-api) and pinned by Test plan
   scenario 12.

Alternatives considered (and rejected):

- **A `resolve` hook capturing exceptions per field.** Rejected per
  ground 1.
- **Serializing every outer result `GraphQLError`** (no `original_error`
  gate). Rejected per ground 2 — it would spam the list with validation
  entries the standard `errors` array already carries. This is distinct from
  retaining a terminal `GraphQLError` reached through a non-`None` original
  link, which proves it was raised during resolver execution.
- **Capturing exceptions the resolvers swallowed** (graphene cannot either).
  Out of scope by construction: only errors that reached the result exist
  to report.

### Decision 10 — Multi-database capture: every alias in `connections.all()`, one bracket each

The pre-yield bracket loops `django.db.connections.all()` — every configured
alias, whether or not the operation will touch it — saving and setting each
connection's flag and snapshotting each log independently; teardown slices
and restores per alias and concatenates the rows (each already carrying its
`alias`,
[Decision 8](#decision-8--the-sql-row-shape-graphenes-wire-names-narrowed-to-what-djangos-log-supports))
in `connections.all()` order.

Grounds: it is graphene's own loop
([`middleware.py`][upstream-debug-middleware] `::enable_instrumentation`
iterates `connections.all()`), it is the only shape that captures fakeshop's
sharded mode and any consumer router setup without alias knowledge, and the
per-alias `alias` field is what makes the payload useful under
[multi-database cooperation][glossary-multi-database-cooperation] — the
debug view shows *which* database served each statement. An untouched alias
contributes zero rows at the cost of its wrapper materialization, one
saved-flag record, and one teardown log copy ([Edge
cases](#edge-cases-and-constraints) carries the exact complexity language);
per
[Decision 4](#decision-4--fidelity-djangos-own-debug-cursor-via-a-force_debug_cursor-bracket-not-a-cursor-wrap-port)'s
third alternative, no connection is force-opened. The per-alias contract is
a **documented promise and therefore needs a real proof**: Test plan
scenario 16 executes a real `shard_b` query through a debug-enabled probe
schema on the `FAKESHOP_SHARDED=1` tier and asserts the captured
`alias == "shard_b"` row plus both-alias restoration — serializer units and
fake partial-acquisition tests alone do not prove a second alias appears in
the response.

Alternatives considered (and rejected): **bracketing only
`connections["default"]`** — rejected, silently blind on sharded setups;
**lazily bracketing on first use via the `connection_created` signal** —
rejected, misses the common case of aliases whose connections already exist
from prior requests, and signal (dis)connection per operation is its own
leak surface.

### Decision 11 — Test strategy: split live HTTP behavior from package-tier mechanics

The card predicts `tests/extensions/`, but predicted files do not override the
repository's test-placement law. The card also requires coverage "against a
fakeshop request that emits SQL", so the tests split by behavior:

- **The request-driving group** lives in
  `examples/fakeshop/test_query/test_debug_extension_api.py` and posts
  **real HTTP** to a debug-enabled
  schema mounted on a probe URLconf (`@pytest.mark.urls` /
  a module-level `urlpatterns` over Strawberry's Django view — the
  [`test_multi_db.py`][test-multi-db] `#"_current"` plumbing precedent),
  built over the freshly-reloaded fakeshop apps per the
  [schema-reload discipline][glossary-schema-reload-discipline], seeded via
  [`seed_data`][glossary-seed-data], posted through
  [`TestClient`][glossary-testclient]. These are fakeshop requests emitting
  real SQL — the card's phrase, literally.
- **The mechanics group** lives in `tests/extensions/test_debug.py` and pins
  what a request cannot isolate: serializer and nested-chain edges, the
  restore contract, bounded-log behavior, no-stash/idempotent results,
  masking order, async exception shape, and concurrent sync isolation.

**The [live-first mandate][glossary-live-first-coverage-mandate]
application:** `examples/fakeshop/test_query/` owns live GraphQL HTTP tests for
any app or package surface. A module-local probe URLconf does not change that
classification; it is the established way to exercise an opt-in schema shape
without enabling it in the shipped aggregate schema. Package-tier tests remain
only for mechanics that cannot be proved by a real request.

Alternatives considered (and rejected):

- **Enable the extension in fakeshop's shipped schema so tests go live.**
  Rejected in
  [Decision 2](#decision-2--card-scope-boundary-the-extension-ships-alone--no-django-middleware-no-schema-field-no-fakeshop-always-on-wiring)
  — every acceptance response pays body weight and capture cost, and the
  example stops modeling the off-by-default posture.
- **Put all scenarios in the card's predicted `tests/extensions/` path.**
  Rejected: a live `/graphql/` request belongs to `test_query/` under the
  explicit repository rule. Predicted paths guide planning; they do not
  authorize a placement exception.
- **In-process `schema.execute_sync` instead of HTTP.** Rejected for the
  request-driving group (the card says "request", and HTTP exercises the
  serialization of `extensions` into the response body — JSON round-trip
  included); retained where it is the *point* — the async-color scenario
  drives in-process async execution precisely because Django's async test
  client cannot change the thread-locality story the scenario documents.

### Decision 12 — This card completes the joint `0.0.14` cut and owns the version bump

Unlike [`spec-041`][spec-041] / [`spec-042`][spec-042] / [`spec-043`][spec-043]
(each of which shared `0.0.14` with open siblings and so deferred), **`044`
is the last non-Done card at `0.0.14`** — the board shows no other WIP /
To-Do card at this patch version, and all three Done `0.0.14` cards
explicitly deferred their cut to "the last `0.0.14` card to land". Per the
[joint version cut][glossary-joint-version-cut] rule and
[`docs/SPECS/NEXT.md`][next] Step 3's ownership rule, that makes this card
the cut's owner — the same lone-ownership shape [`spec-038`][spec-038]
Decision 14 pinned for `0.0.12`. Leaving the version at `0.0.13` after `044`
ships would strand four cards' worth of shipped surface under a stale
identity, and nobody else would ever bump it.

Slice 3 therefore aligns the version quintet — exactly the
[glossary][glossary-joint-version-cut]-pinned set:

- `[project].version` in [`pyproject.toml`][pyproject] → `0.0.14`
- `__version__` in [`__init__.py`][init]
- [`tests/base/test_init.py::test_version`][test-base-init]
- the [`docs/GLOSSARY.md`][glossary] package-version line
- the `django-strawberry-framework` `version` entry in `uv.lock`

— plus the release-status flips the rule also assigns to the cut: the
GLOSSARY `shipped (0.0.14)` status flips for the router (and its adapter /
`require_optional_module` companions), the toolbar middleware, the
test-client family, and this card's own entry; the [`README.md`][readme] /
[`docs/README.md`][docs-readme] "Coming next" → "Shipped today" moves; the
[`TODAY.md`][today] shipped-capabilities additions; and the `CHANGELOG.md` `0.0.14`
section under the Slice 3 grant. `0.0.14` is a routine patch cut, **not** a
milestone (`.0`) cut — the alpha → beta milestone chores (the `0.1.0`
GLOSSARY constraint lifts, the board's progress section, the README
milestone prose) belong to [`TODO-BETA-045-0.1.0`][kanban], not here.

The bump moves only in Slice 3, after the extension and its docs are
complete — never in Slice 1.

Alternatives considered (and rejected):

- **Defer to yet another card.** Rejected: no later `0.0.14` card exists; a
  deferral would orphan the cut the three predecessors are waiting on.
- **Bump in Slice 1.** Rejected: the version should move only after the
  feature and docs are complete (the [`spec-038`][spec-038] rule), and a
  Slice-1 bump would publish `0.0.14` identity while `044`'s own surface is
  mid-flight.

## Implementation plan

The file-level delta map for the build handoff (each row's contract is
specified in the decisions cited; the version moves **only** in Slice 3,
[Decision 12](#decision-12--this-card-completes-the-joint-0014-cut-and-owns-the-version-bump)):

| File | Change | Slice |
| --- | --- | --- |
| `django_strawberry_framework/extensions/__init__.py` (new) | Subpackage docstring + `DjangoDebugExtension` re-export in `__all__` ([Decision 5](#decision-5--symbol-and-home-djangodebugextension-in-extensionsdebugpy-exported-from-the-extensions-subpackage--never-the-package-root)) | 1 |
| `django_strawberry_framework/extensions/debug.py` (new) | `DjangoDebugExtension(SchemaExtension)`: sync `on_operation` generator (per-alias reference-counted `force_debug_cursor` bracket + snapshot pre-yield; `finally`-guarded materialize / slice / serialize / stash / release at teardown), `get_results()` returning the stash under `"debug"`, SQL/exception serializers, and the lock-protected active-bracket coordinator ([Decisions 4](#decision-4--fidelity-djangos-own-debug-cursor-via-a-force_debug_cursor-bracket-not-a-cursor-wrap-port)–[10](#decision-10--multi-database-capture-every-alias-in-connectionsall-one-bracket-each); module shape per [DRY D4–D6](#helper-reuse-obligations-dry)) | 1 |
| `examples/fakeshop/test_query/test_debug_extension_api.py` (new) | The [Test plan](#test-plan) request-driving scenarios: real probe-URLconf HTTP via [`TestClient`][glossary-testclient], under schema-reload + `seed_data` disciplines ([Decision 11](#decision-11--test-strategy-split-live-http-behavior-from-package-tier-mechanics)) | 1 |
| `tests/extensions/__init__.py` (new) | Test-package marker and placement anchor; no shared helper exports | 1 |
| `tests/extensions/test_debug.py` (new) | Request-impossible serializer, lifecycle, masking, async-shape, bounded-log, and concurrent-isolation mechanics ([Decision 11](#decision-11--test-strategy-split-live-http-behavior-from-package-tier-mechanics)) | 1 |
| [`pyproject.toml`][pyproject] / `uv.lock` | Raise the existing Strawberry floor to `>=0.316.0` and re-resolve for per-request extension isolation ([Decision 6](#decision-6--opt-in-shape-pass-the-class--one-fresh-instance-per-operation-requires-strawberry-03160)); the package's own version still moves only in Slice 3 | 1 |
| [`docs/GLOSSARY.md`][glossary] | [Response-extensions debug middleware][glossary-response-extensions-debug-middleware] entry body → implemented contract (glossary DB + re-render); status flip deferred to Slice 3 | 2 |
| [`docs/TREE.md`][tree] | Regenerated (script-rendered) after the `TrackedPath.is_current` updates while the card remains WIP; `extensions/` + `tests/extensions/` planned rows resolve and the live test row appears | 2 |
| `examples/fakeshop/apps/kanban/constants.py` | Register the new package/test files and directories in the sorted tracked-path allowlists that feed the Slice-2 `TrackedPath.is_current` updates and `docs/TREE.md` render | 2 |
| [`config/schema.py`][config-schema] | Docstring's "no direct Strawberry analogue" sentence rewritten to name the shipped extension and fakeshop's deliberate opt-out | 2 |
| [`GOAL.md`][goal] | Scope success criterion 7's import-only promise to `Meta`-driven declarations; engine configuration migrates by documented recipe | 2 |
| [`pyproject.toml`][pyproject] / [`__init__.py`][init] / [`tests/base/test_init.py`][test-base-init] / `uv.lock` / GLOSSARY version line | The version quintet → `0.0.14` ([Decision 12](#decision-12--this-card-completes-the-joint-0014-cut-and-owns-the-version-bump)) | 3 |
| [`docs/GLOSSARY.md`][glossary] | `shipped (0.0.14)` status flips for all four `0.0.14` surfaces + companions + the [Joint version cut][glossary-joint-version-cut] wording (glossary DB + re-render) | 3 |
| [`README.md`][readme] / [`docs/README.md`][docs-readme] / [`TODAY.md`][today] | "Coming next / already landed ahead of the release" → shipped-`0.0.14` status wording | 3 |
| `CHANGELOG.md` | The `0.0.14` release section (all four cards) — under this spec's explicit Slice-3 grant | 3 |
| [`KANBAN.md`][kanban] / `KANBAN.html` | Final card wrap: DB edits + Done flip + `import_spec_terms` **first**, generated renders **last**, `--check` modes after the final DB mutation (the ordered wrap sequence in the [Slice checklist](#slice-checklist)) | 3 |
| [`.github/workflows/django.yml`][workflow-django] | Make the minimum-support CI node force-install `strawberry-graphql==0.316.0` (coverage disabled on that node; the latest node keeps the coverage gate) so the advertised floor is durably exercised, not a one-time throwaway run ([Decision 6](#decision-6--opt-in-shape-pass-the-class--one-fresh-instance-per-operation-requires-strawberry-03160)) | 1 |
| [`optimizer/extension.py`][optimizer-extension] | Correct the `__init__` comment's rationale: Strawberry no longer passes `execution_context=` to class entries at the `0.316` floor; the parameter stays for direct-construction compatibility ([Decision 6](#decision-6--opt-in-shape-pass-the-class--one-fresh-instance-per-operation-requires-strawberry-03160) migration notes) | 1 |
| [`test_multi_db.py`][test-multi-db] (or a dedicated `FAKESHOP_SHARDED`-gated debug module) | Real sharded-tier capture proof: a `shard_b` query through a debug-enabled probe schema asserts `alias == "shard_b"` + vendor + both-alias restoration ([Decision 10](#decision-10--multi-database-capture-every-alias-in-connectionsall-one-bracket-each), Test plan scenario 16) | 1 |

## Helper-reuse obligations (DRY)

Reuse is named per item, and deliberate *non*-reuse carries its reason (the
[`spec-041`][spec-041] / [`spec-042`][spec-042] / [`spec-043`][spec-043]
discipline). Two independent, simultaneously-written reviews of the planned
module against all thirteen `django_strawberry_framework/utils` modules
(2026-07-11) reached the same headline this section now records in full:
**almost nothing in `utils/` is directly callable from `debug.py`, and that
is the correct outcome, not a gap** — the utils charter is the
query/write/input pipeline (visibility, inputs, windows, write decode); the
debug extension is an engine-lifecycle instrument over
`django.db.connections` and the execution result, and forcing reuse would
invert DRY into coupling. The real DRY work is (a) single-siting inside
`debug.py` itself (D4–D5), (b) conformance with the package's established
idioms (D6), and (c) writing the non-reuse reasons down (D-N1–D-N8) so the
discipline survives review.

- [ ] **D1** — the operation lifecycle and the response-extensions merge
  ride Strawberry's `SchemaExtension` seams (`on_operation`, `get_results`)
  — never a view patch, never a transport hook
  ([Decision 3](#decision-3--exposure-the-response-extensions-map-under-the-debug-key-not-a-schema-level-_debug-field),
  [Decision 7](#decision-7--hook-shape-one-sync-on_operation-generator-assembly-at-teardown-get_results-returns-the-stash)).
- [ ] **D2** — SQL instrumentation rides Django's own `CursorDebugWrapper`
  via the `force_debug_cursor` flag — the package owns only the minimal
  reference-counted bracket coordinator needed for overlap-safe restoration,
  not a cursor wrapper or query recorder
  ([Decision 4](#decision-4--fidelity-djangos-own-debug-cursor-via-a-force_debug_cursor-bracket-not-a-cursor-wrap-port)).
- [ ] **D3** — the request-driving tests reuse the single-sited
  [`schema_reload.reload_all_project_schemas()`][schema-reload] and
  [`seed_data`][glossary-seed-data] helpers, post through
  [`TestClient`][glossary-testclient], and mirror the
  [`test_multi_db.py`][test-multi-db] probe-URLconf plumbing — never private
  reload logic, hand-built catalog rows, or hand-rolled POST-decode blocks
  ([Decision 11](#decision-11--test-strategy-split-live-http-behavior-from-package-tier-mechanics)).
  Sharpened by the DRY review: the live module's schema fixture depends on
  the acceptance suite's `_reload_project_schema_for_acceptance_tests` and
  imports the freshly-reloaded app types *inside* the fixture body — no
  local `registry.clear()`, no second module-reload list, no import-time
  app-type imports; domain rows come from `seed_data(N)` /
  `create_users(N)` with only the permission a scenario needs (mutation
  auth through `with client.login(user):`, expected-error posts through
  `assert_no_errors=False`; the "first domain-setup line is `seed_data`"
  rule governs product/catalog setup — auth setup may precede the seed
  when a scenario needs a user first, and a write scenario grants its one
  write permission on top of a non-staff fixture user rather than
  reaching for the superuser); the module keeps **one** schema holder, one
  view, one `urlpatterns` — a fixture swaps the held schema per scenario
  (debug-only, optimizer + debug, no-debug, raising field) rather than
  duplicating the holder — and the schema-construction seam never sorts,
  normalizes, or deduplicates the `extensions=` list, because order is part
  of the contract
  ([Decision 9](#decision-9--exception-capture-the-results-original_error-chain-serialized-like-graphenes-wrap_exception--no-resolver-wrapping)).
  URLconf **activation** is likewise single-sited: one module-level
  `pytestmark = pytest.mark.urls(__name__)` application covers every
  request-driving scenario (if the marker cannot serve, one fixture owns
  the equivalent `ROOT_URLCONF` override and `clear_url_caches()` cleanup
  for the whole module) — never a per-test
  `override_settings(ROOT_URLCONF=__name__)` / `clear_url_caches()`
  enter/exit block (the boilerplate [`test_multi_db.py`][test-multi-db]
  repeats around each request), and never routing setup hidden inside
  [`TestClient`][glossary-testclient].
  The [`test_multi_db.py`][test-multi-db] holder is the behavioral
  precedent but is deliberately **copied, not promoted** into a shared
  helper: that module is import-gated by `FAKESHOP_SHARDED` while this one
  is always collected, and URLconf modules must expose real module-level
  `urlpatterns` — promote a narrowly named test helper only when a third
  always-collected module needs the exact same mutable-schema URLconf.
- [ ] **D4** — the two wire serializers are **module-level functions**, not
  closures or methods: one exception serializer owns the triple — including
  the load-bearing explicit arguments
  `traceback.format_exception(type(exc), exc, exc.__traceback__)`
  ([Decision 8](#decision-8--the-sql-row-shape-graphenes-wire-names-narrowed-to-what-djangos-log-supports)) —
  and one SQL-row serializer owns the `float(entry["time"])` cast, the slow
  predicate against a single module constant (`_SLOW_QUERY_SECONDS = 10`,
  graphene's threshold, never an inline `> 10` at two sites), the
  `select`-prefix sniff, and the six wire keys spelled as **literals**;
  `isSlow` / `isSelect` derive *inside* the serializer, never at a call
  site. Module level so the [Risks](#risks-and-open-questions)
  `_debug`-facade fallback (or any future card) imports them without
  instantiating the extension.
- [ ] **D5** — every remaining debug rule is **single-sited inside
  `extensions/debug.py`**: one `None`-guarded exception collector owns the
  `result is None` / `errors is None` guards, the
  `original_error is not None` filter, and the chain-walk + serialize
  compose — preserving result-error order and emitting one row per
  qualifying outer error with **no speculative deduplication**; teardown and
  `get_results` never each re-spell the guards
  ([Decision 9](#decision-9--exception-capture-the-results-original_error-chain-serialized-like-graphenes-wrap_exception--no-resolver-wrapping)).
  One module-private, lock-protected bracket coordinator exposes exactly
  **two seams** — `acquire(connection) → token` / `release(token)`, whether
  surfaced as methods or as one per-connection context manager (the pin is
  the single ownership, not the callable shape) — and is
  the only code that touches the active-capture map, the saved flag values,
  and `connection.force_debug_cursor`; the map is keyed by **connection
  object identity, never by alias** (aliases name settings entries, while
  the mutable flag lives on a concrete per-thread connection wrapper — one
  alias names different objects on different threads), and
  `ExitStack.callback(...)` keeps the per-alias unwind declarative in
  `on_operation`
  ([Decision 7](#decision-7--hook-shape-one-sync-on_operation-generator-assembly-at-teardown-get_results-returns-the-stash)).
  One immutable per-alias snapshot record retains exactly what teardown
  needs — the acquired connection object and the starting log length
  (named for the query log, never "window": the D-N5 vocabulary rule);
  alias and vendor are read from that same retained connection at
  serialization, and teardown iterates the retained snapshots — never a
  second `connections.all()` call matched by position, since configured
  aliases or thread-local wrappers could differ by then. One log-slice
  helper owns the `list(connection.queries_log)`
  materialization and the `min(snapshot, len(entries))` clamp, so the
  best-effort rollover caveat is documented on that one function
  ([Edge cases](#edge-cases-and-constraints)); and one payload builder owns
  the `{"sql": [...], "exceptions": [...]}` spelling — `get_results` reads
  the stash and never constructs shape, and each operation gets fresh
  containers (never class-level or module-level empty lists). The mechanics
  tests target those seams, not the hook body
  ([Test plan](#test-plan)).
- [ ] **D6** — pattern conformance with the package's established idioms
  (conformance, not code sharing): **no `__init__`** — the class has no
  instance config, and Strawberry assigns `execution_context` after
  zero-argument construction; DRY-by-omission, where
  [`optimizer/extension.py`][optimizer-extension] defines a constructor only
  because it carries strictness/strategy/cache config. If future
  configuration requires an explicit constructor, initialize only that
  configuration and do not claim that
  `super().__init__(execution_context=...)` performs the binding;
  `execution_context` remains engine-assigned. The generator hook
  reads as the same idiom as the package's one existing extension generator
  hook (`DjangoOptimizerExtension.on_execute` — acquire pre-yield,
  `finally`-guarded reverse-order release). The `original_error` walk
  follows the bounded-walk posture `utils/typing.py` pins with
  `_MAX_TYPE_WRAPPER_DEPTH` — never a bare unbounded
  `while error.original_error:` peel; the identity set terminates cycles
  and a local 64-hop ceiling bounds acyclic chains
  ([Decision 9](#decision-9--exception-capture-the-results-original_error-chain-serialized-like-graphenes-wrap_exception--no-resolver-wrapping)) — while
  its *failure policy* deliberately differs (stop-on-cycle and retain the
  terminal, versus the type unwrappers' loud terminal raise), which is why
  it stays a local helper: extraction of a shared `peel_attr_chain` into
  `utils/typing.py` is deferred until a **fourth** chain-peel appears
  (rule of three — recorded so a future worker finds the decision instead
  of re-litigating it). The new `extensions/__init__.py` mirrors the
  eager-subpackage export shape — docstring + explicit re-export +
  `__all__`, as `utils/__init__.py` and `testing/__init__.py` do
  ([Decision 5](#decision-5--symbol-and-home-djangodebugextension-in-extensionsdebugpy-exported-from-the-extensions-subpackage--never-the-package-root)).
  And every helper docstring says "database connection", never bare
  "connection" — the D-N5 disambiguation made structural, so a grep across
  `utils/` and `extensions/` stays partitionable by noun.
- [ ] **D-N1** (non-reuse) — the optimizer's `_context` ContextVar /
  context-stash machinery is **not** reused: that machinery exists because
  the optimizer instance is shared across requests and must publish
  per-execution state out-of-band; a per-operation
  instance ([Decision 6](#decision-6--opt-in-shape-pass-the-class--one-fresh-instance-per-operation-requires-strawberry-03160))
  makes plain attributes the simpler correct shape — and the ground is
  sharper than "unnecessary": at the `0.316.0` floor there is no shared
  instance left for a ContextVar to coordinate, so carrying the stash
  machinery forward would be complexity with no coordinating role, plus
  reset-token hygiene that can only add failure modes.
- [ ] **D-N2** (non-reuse) — no `utils/imports.py` guard
  ([`require_optional_module`][glossary-require-optional-module] /
  `require_*`): both imports are hard dependencies; a guard would be
  ceremony with no absent-dependency case to serve — and falsely advertise a
  soft dependency. No `import_attr` deferred-import seam either: `debug.py`
  sits at the leaf of the import graph; nothing imports back into it. Plain
  top-of-module imports.
- [ ] **D-N3** (non-reuse) — graphene's [`sql/tracking.py`][upstream-sql-tracking]
  is **not** ported ([Decision 4](#decision-4--fidelity-djangos-own-debug-cursor-via-a-force_debug_cursor-bracket-not-a-cursor-wrap-port)
  alternatives); the borrow is the *field vocabulary and its semantics*
  ([Decision 8](#decision-8--the-sql-row-shape-graphenes-wire-names-narrowed-to-what-djangos-log-supports)),
  not the instrumentation.
- [ ] **D-N4** (non-reuse) — nothing is shared with
  [`middleware/debug_toolbar.py`][middleware-debug-toolbar]: the toolbar
  subclasses a third-party Django middleware over the HTTP response; this is
  an engine extension over the execution result. Verified down to the atoms:
  the toolbar's `_HTML_TYPES` / payload-injection helpers share nothing with
  the extensions-map merge — there is not even a constant to lift. The only
  relationship is documentation ("distinct from", both directions,
  [Doc updates](#doc-updates)).
- [ ] **D-N5** (non-reuse) — **nothing is shared with
  `utils/connections.py`**, despite the name: that module's entire surface
  (window bounds, sidecar kwargs, range plans, probe arithmetic,
  `UnwindowableConnection`) serves **Relay pagination windows**; the debug
  extension's subject is `django.db.connections` — a different noun that
  happens to share the module name. The constraint runs both directions: no
  debug helper may be added to `utils/connections.py` (the "connections
  helpers live in `utils/connections`" instinct would put DB instrumentation
  state inside the Relay-window contract module), and the bracket
  coordinator stays module-private in `extensions/debug.py` — one consumer,
  the same rule-of-three reasoning D-N3 applies to graphene's tracking port.
  Promote it only when another production feature needs the same overlap
  semantics, not merely another `try`/`finally`.
- [ ] **D-N6** (non-reuse) — `debug.py` imports **nothing from
  `django_strawberry_framework.utils` at all**: its imports are stdlib
  (`contextlib`, `threading`, `traceback`, plus `dataclasses` / `typing`
  where the private records want them), `django.db`, `graphql` (the
  `GraphQLError` the chain walk types against), and
  `strawberry.extensions` — all hard dependencies, imported directly with
  no wrapper functions around them. The full thirteen-module utils inventory was
  reviewed; the modules serve the query/write/input pipeline the extension
  never touches (queryset visibility, generated inputs, input traversal,
  permissions, write decode, relation classification, converter dispatch).
  Three tempting near-misses, each rejected: `strings.graphql_camel_name`
  must not manufacture `isSlow` / `isSelect` (the keys are a wire contract —
  [Decision 8](#decision-8--the-sql-row-shape-graphenes-wire-names-narrowed-to-what-djangos-log-supports)'s
  rejected alternative); `errors.field_error` must not shape the exception
  row (the write-envelope `FieldError` is a different wire contract with
  field keys, paths, and codes — the only shared atom is `str()` coercion,
  beneath extraction); and `typing.is_async_callable` /
  `querysets.reject_async_in_sync_context` have no seam here (the extension
  ships one sync generator hook whose color dispatch the engine owns, and it
  calls no consumer-overridable hook).
- [ ] **D-N7** (non-reuse) — **no addition to `exceptions.py` and no
  module-local exception class**: the extension raises nothing of its own —
  capture is best-effort, and the coordinator's acquire/release seams are
  private and bracketed, so their contract violations cannot occur. If a
  later revision needs a raise, it goes through `exceptions.py` (the
  bottom-of-import-graph single home), never a module-local class; the
  `UnwindowableConnection` precedent in `utils/connections.py` is the one
  sanctioned exception to that rule (a control-flow sentinel that must not
  be catchable as a package error), and debug has no such sentinel need.
- [ ] **D-N8** (non-reuse / premature abstraction) — the module introduces
  **no abstraction the one feature does not need**: no package
  `BaseDjangoSchemaExtension` (Strawberry's `SchemaExtension` +
  `get_results` already *is* that abstraction; a package base storing a
  key/payload would save a few lines while hiding the
  absent-before-teardown rule, conditional double-call idempotence, the masking
  order, and the security posture — those are the feature, not
  boilerplate); no merged `serialize_debug_row(kind, value)` dispatcher
  (the SQL and exception serializers share a return type and nothing else —
  different inputs, keys, normalization, ordering, and security
  properties); no runtime dataclasses or Strawberry types for the **wire
  rows** (plain dicts built once already match the response protocol; a
  dataclass row would need a second conversion pass before JSON, and a
  Strawberry type would re-create the schema surface
  [Decision 3](#decision-3--exposure-the-response-extensions-map-under-the-debug-key-not-a-schema-level-_debug-field)
  rejects — private `TypedDict`s and the small internal state records are
  fine where they aid static readability); and no per-key module constants
  beyond `_SLOW_QUERY_SECONDS` (the serializer's fixed dict is the single
  source of the wire spelling, [D4](#helper-reuse-obligations-dry);
  constantizing every key would scatter the shape across declarations and
  uses — the top-level `"debug"` key earns a name only if it is otherwise
  repeated across both production methods).

## Edge cases and constraints

- **Restore is saved-value, `ExitStack`-owned, overlap-safe, and nest-safe.**
  The bracket restores each connection's *prior* `force_debug_cursor` (not `False`), so
  an operation running inside a consumer's own `CaptureQueriesContext` (or
  under `DEBUG=True`, where `queries_logged` is true anyway) leaves the
  outer state intact. A lock-protected active-bracket map counts overlapping
  users of the same connection object and restores only when the count reaches
  zero, so async teardown order cannot leave a stale flag. The `finally`
  guarantees release even when the operation or serializer raises, and
  unwinds earlier aliases if a later alias fails during acquisition. Without
  this, one enabled operation could leave process connections instrumented
  forever
  ([Decision 7](#decision-7--hook-shape-one-sync-on_operation-generator-assembly-at-teardown-get_results-returns-the-stash)).
- **`queries_log` is a bounded deque.** Django caps the per-connection log
  (`queries_limit`, default 9000), and a deque is not sliceable. Teardown
  first materializes `entries = list(connection.queries_log)`, then reads
  `entries[min(snapshot, len(entries)):]`. This mirrors Django's
  length-snapshot approach and cannot raise if `reset_queries()` shortened
  the log, but it is explicitly **best effort after rollover**: once a full
  deque evicts old rows while remaining the same length, a length snapshot
  cannot distinguish old from new entries and may omit some or all operation
  queries. `CaptureQueriesContext` has the same limitation. The docstring
  names it; 9000 statements remains a pathological operation for this dev
  tool. Over HTTP, the normal `request_started` reset happens before the
  view and therefore before this bracket.
- **Async execution: exceptions always, SQL typically nothing.** Django
  connections are strictly per-thread (`ConnectionHandler.thread_critical`);
  under async execution the extension's hook runs on the event-loop thread,
  whose connection objects are `@async_unsafe`-barred from executing SQL,
  while ORM work runs in `sync_to_async` executor threads with *their own*
  connection objects the bracket never touched — so expect an **empty**
  `sql` list under async execution, not a partial one. Exception capture
  reads the execution result and is color-agnostic. Two sharper corners,
  both documented: concurrent async tasks can share connection-wrapper
  objects inherited from a parent context, but tasks that materialize an
  alias independently may receive distinct wrappers. Coordinator overlap is
  guaranteed only when wrappers are materialized before task creation and
  inherited by both tasks. For shared wrappers, the reference-counted
  bracket prevents flag leakage but cannot attribute rows per operation; under
  `DJANGO_ALLOW_ASYNC_UNSAFE` (which lets the loop thread run ORM directly),
  concurrent operations can capture each other's statements. The docstring
  carries all of it; the follow-on is a [Risk](#risks-and-open-questions).
  The ordinary non-reentrant sync path — Django's default `/graphql/` view,
  `schema.execute_sync`, every fakeshop surface — captures Django's query-log
  rows fully. Nested or reentrant sync GraphQL execution on the same thread
  shares one wrapper and log: restoration remains correct, but overlapping
  length snapshots are not operation-local, so the outer payload includes
  SQL emitted by the nested operation.
- **Nested sync attribution is intentionally best effort.** The coordinator
  owns only `force_debug_cursor` restoration, not row attribution.
  Same-thread nested operations share `queries_log`; the outer snapshot
  includes the inner interval. Strict operation-local attribution would
  require a different instrumentation source.
- **Pre-execution failures carry no `debug` key.** Parse and validation
  errors return before execution; the engine calls `get_results` before the
  hook's teardown on those paths, the stash does not exist, and the
  extension contributes `{}` — deliberately, since nothing executed
  ([Decision 7](#decision-7--hook-shape-one-sync-on_operation-generator-assembly-at-teardown-get_results-returns-the-stash)).
  Client code must treat the key as operation-conditional, and the
  docstring says so.
- **`executemany` rows keep Django's raw form.** The log stores
  `"<N> times: <parameterized sql>"` for `executemany` (no interpolation;
  `<N>` reads `"?"` when the params came from an iterator Django could not
  count); the row's `sql` carries it verbatim and `isSelect` correctly reads
  `False` (batch DML is never a select). Documented, not normalized — the
  log is the fidelity contract.
- **Transaction statements appear as rows only when their logging completes
  while the hook is active.** Savepoint statements (`SAVEPOINT`, `RELEASE
  SAVEPOINT`) route through the debug cursor, and connection-level
  `BEGIN` / `COMMIT` / `ROLLBACK` are appended to `queries_log` by Django's
  own `debug_transaction` bracket
  ([`django/db/backends/base/base.py`][venv-django-base] `#"debug_transaction"`
  wraps `_commit` / `_rollback` / `set_autocommit` whenever `queries_logged`
  is true — Django ≥ 4.2). So an `atomic()` block **entered and exited
  inside a resolver** emits `BEGIN` / `COMMIT` rows beside its `INSERT`
  (each with `isSelect: false`). Explicitly **excluded**: transaction
  boundaries that enclose the GraphQL execution itself —
  `ATOMIC_REQUESTS` / transaction middleware wrap the *view*, so their
  outer `BEGIN` runs before the extension enters and their final
  `COMMIT` / `ROLLBACK` (plus any commit failure and `on_commit` work) runs
  after it tears down; those rows are never captured (Test plan
  scenario 19 pins the inclusion/exclusion boundary). Within scope, this
  matches `assertNumQueries` visibility — the payload shows what
  Django's own accounting shows — and it is why the [Test plan](#test-plan)'s
  row assertions filter by `isSelect` / statement prefix rather than
  asserting positional indices or raw totals.
- **The capture interval follows cursor construction.** Django picks
  `CursorDebugWrapper` when `connection.cursor()` is called and never
  re-checks per `execute()`
  ([Decision 4](#decision-4--fidelity-djangos-own-debug-cursor-via-a-force_debug_cursor-bracket-not-a-cursor-wrap-port)):
  a normal cursor pre-opened before the operation stays silent inside it,
  and a retained debug cursor keeps logging after the flag restores. The
  guarantee covers normally short-lived cursors acquired while the hook is
  active; both boundary directions are pinned by Test plan scenario 18.
- **SQL from sibling extensions' lifecycle hooks is order-dependent.**
  `on_operation` hooks enter in `extensions=`-list order and unwind in
  reverse, so SQL performed by another extension's setup/teardown is
  captured only when it happens to fall inside the debug hook's active
  interval. Resolver/engine SQL is the stable core contract; sibling-hook
  SQL is documented as ordering-dependent, like masking and key collisions
  already are (Test plan scenario 20 pins both list orders with marker
  SQL).
- **Explicitly cross-thread-shared wrappers are unsupported / best
  effort.** Django permits sharing a connection wrapper across threads via
  `inc_thread_sharing()`. The coordinator's lock protects flag/depth
  transitions, but concurrent `queries_log` appends versus teardown's deque
  materialization are not synchronized, and operation-local attribution is
  impossible on a shared log. The two-phase failure policy ([Error
  shapes](#error-shapes)) still applies: whatever a concurrent mutation
  does to the deque, the GraphQL response must not be corrupted — the
  payload degrades, the result survives.
- **Stored procedures are not recorded.** Calls through `callproc()` are
  outside this SQL contract because Django's `CursorDebugWrapper` does not
  instrument them; there is no `queries_log` entry for the extension to
  serialize.
- **Introspection is not special-cased.** An `IntrospectionQuery` on an
  enabled schema carries `{"sql": [], "exceptions": []}` — harmless, and a
  skip rule (the toolbar's `IntrospectionQuery` guard exists to protect its
  request *history*, a concern with no analogue here) would add a branch
  with no payer. Considered and rejected.
- **Masking extensions and exposure order.** The `exceptions` rows carry
  unmasked type / message / stack by design; a schema combining a masking
  extension with this one exposes to the client what masking hid in
  `errors`. The docstring's security posture covers it: development
  schemas only, never internet-facing production. (graphene's `DjangoDebug`
  has the same property and the same posture.) The disclosure surface is
  named in full, not just the exception headline: Django's
  `last_executed_query` output **interpolates parameter values** into the
  captured `sql` strings — secrets, tokens, email addresses, and other PII
  included — and tracebacks expose filesystem/source paths; the response
  containing them is routinely **copied downstream** (browser DevTools,
  HTTP logs, tracing systems, caches, bug reports, test snapshots), and the
  rows also persist in the in-process query log after the response (the
  retention point above). The class docstring, the GLOSSARY entry, and this
  section all carry that enumeration; the off-by-default, code-level opt-in
  remains the accepted v1 boundary — no settings gate or redaction
  subsystem for this card ([Risks](#risks-and-open-questions)).
- **`extensions`-map cohabitation.** Among extension outputs, the runner
  merges `get_results()` in list order and the later-listed same-key value
  wins. Async execution then overlays
  `ExecutionContext.extensions_results`, which has final precedence; sync
  has no equivalent overlay. The completed map replaces rather than merges
  any pre-existing `ExecutionResult.extensions`
  ([Error shapes](#error-shapes)). The payload is
  JSON-serializable by construction (str / float / bool / list / dict
  only), so no transport encoder can choke on it.
- **Zero debug cost when disabled; cardinality-bounded — not generally
  bounded — cost when enabled.** Disabled, no debug code runs (the class is
  not in the list) — though "disabled" does not undo the release-wide
  Strawberry-floor change ([Goals](#goals) item 3). Enabled, the exact
  per-operation complexity is: `connections.all()` materializes a Django
  wrapper for **every configured alias** (no raw DB connection is opened,
  but wrapper construction can import a backend and surface an invalid
  alias/backend configuration); setup writes one saved-flag record per
  alias; execution pays Django's own debug-cursor overhead (the same cost
  `DEBUG=True` dev servers already pay); and teardown performs
  `list(connection.queries_log)` per alias — copying up to `queries_limit`
  (default 9000) entry references even when an old, already-full log holds
  no rows from this operation — plus one serialization pass. Under async
  schema execution that synchronous teardown runs **on the event-loop
  thread** and can stall it. Row count is capped per alias by Django's
  bounded deque, but SQL string length, exception count/message/traceback
  size, alias count, and total response bytes are **not** usefully bounded
  — v1 enforces no row/byte caps and does not claim to
  ([Risks](#risks-and-open-questions) keeps caps as follow-on knobs).
  Retention: captured rows also remain in Django's per-connection deque
  after the response; over HTTP the `request_started` signal resets the log
  before the next view, but non-HTTP in-process execution has no such
  reset, so interpolated values persist in memory until reset or eviction.
  No plan interaction, no [plan-cache][glossary-plan-cache] key change, no
  queryset touch.
- **The subscription lifecycle is out of contract.** The package ships no
  subscription surface; the extension's documented behavior covers query /
  mutation operations ([Non-goals](#non-goals)).

## Test plan

Scenarios 1–7 live in
`examples/fakeshop/test_query/test_debug_extension_api.py`; scenarios 8–15
and the Revision-8 additions 17–21 live in `tests/extensions/test_debug.py`;
the sharded-tier scenario 16 lives with the `FAKESHOP_SHARDED=1`
infrastructure ([`test_multi_db.py`][test-multi-db] or a dedicated gated
debug module) — numbering appends rather than renumbers so every existing
scenario reference stays stable
([Decision 11](#decision-11--test-strategy-split-live-http-behavior-from-package-tier-mechanics)).
The **request-driving group (1–7)** posts real HTTP through the probe
URLconf (a debug-enabled schema over freshly-reloaded fakeshop types; the
[schema-reload][glossary-schema-reload-discipline] +
[`seed_data`][glossary-seed-data] disciplines; posts through
[`TestClient`][glossary-testclient] with `assert_no_errors=False` where a
scenario expects errors). A tiny local accessor may validate-and-return
`(res.extensions or {})["debug"]` for the happy executed-operation
scenarios, but never for the absence scenarios (5, 7) — those assert the
missing key explicitly. The **mechanics group (8–15)** needs no request; it
drives **real objects** wherever practical — real `GraphQLError` wrappers
for the chain cases, real `MaskErrors` (scenario 12), real Strawberry
execution for lifecycle and idempotence, real connection wrappers and a
real bounded `deque` for the restore/rollover cases — and parametrizes
genuinely identical bodies (prior-flag `False`/`True`, both masking orders,
the serializer's select / non-select / `executemany` cases, repeated
`get_results` calls) while distinct-setup scenarios stay distinct tests.
Two of the mechanics group's rules are deliberate
([DRY D4–D5](#helper-reuse-obligations-dry)): assertions re-spell the wire
keys and the 10-second threshold as **independent literals** — never
importing `_SLOW_QUERY_SECONDS` or building expected rows through the
production serializer, because a self-referential assertion would let a key
rename pass green (the same reason the mutation-envelope tests pin
`"__all__"` as a literal rather than importing the sentinel) — and the
concurrency/lifecycle scenarios 8 and 9 exercise the coordinator's two seams
and the log-slice clamp rather than `on_operation`'s body; scenario 13
exercises per-operation extension isolation on distinct thread-local wrappers,
not same-wrapper reference counting. A future
hook refactor (e.g. the [Risks](#risks-and-open-questions) facade fallback)
does not churn the overlap-safety suite.
Per the repo rule the implementation worker records the exact pytest
commands for the maintainer and does not run the suite unless explicitly
authorized — the [`AGENTS.md`][agents] #"Do not run pytest" workflow rule;
this spec describes the verification but does not override it. The
**targeted** development commands must replace `pytest.ini`'s `addopts`
(which always adds `--cov`, while `pyproject.toml` enforces
repository-wide `fail_under = 100` — a single-file run passes its tests
and then fails the global coverage gate):

- `uv run pytest -o addopts="-v -n0" examples/fakeshop/test_query/test_debug_extension_api.py`
- `uv run pytest -o addopts="-v -n0" tests/extensions/test_debug.py`
- the isolated Strawberry-floor node-ID run uses the same override.

The **full-suite** command (plain `uv run pytest`) — and CI's
coverage-owning node — remain the sole owners of the 100% gate.

**Request-driving (probe URLconf, real HTTP):** the ORM-touching read
scenarios (1–2) are marked `django_db`; the mutation scenario (3) is marked
`django_db(transaction=True)` — its assertions include connection-level
`BEGIN` / `COMMIT` rows, which the default savepoint-wrapped test
transaction would suppress. Scenario 16 is the sharded-tier capture proof
and runs only under `FAKESHOP_SHARDED=1`.

1. **Happy-path SQL capture, `DEBUG=False`.** `seed_data(1)`; a products
   connection query through the probe `/graphql/` → `res.data` intact,
   `res.extensions["debug"]["sql"]` non-empty; the first **`isSelect`**
   row (never positional indexing — transaction rows are in-contract,
   [Edge cases](#edge-cases-and-constraints)) carries
   `vendor == connection.vendor`, `alias == "default"`, an interpolated
   `sql` containing `SELECT`, a `float` `duration`, `isSlow is False`,
   `isSelect is True`; `exceptions == []`. The test asserts
   `settings.DEBUG is False` first — proving the bracket, not Django's
   `DEBUG` logging, produced the capture
   ([Decision 4](#decision-4--fidelity-djangos-own-debug-cursor-via-a-force_debug_cursor-bracket-not-a-cursor-wrap-port)).
2. **Optimizer composition.** The probe schema carries **both** extensions
   in the canonical consumer shape ([User-facing API](#user-facing-api),
   the shipped [`config/schema.py`][config-schema] wiring): one
   module-local `_optimizer = DjangoOptimizerExtension()` singleton
   returned by `lambda: _optimizer` — retaining the instance-bound plan
   cache the factory exists to preserve — beside `DjangoDebugExtension` as
   the **class** entry. The two entries stay visibly different — no helper
   normalizes both into one common factory form, because the shape
   difference documents their intentionally different lifetimes (one
   shared cached optimizer, one fresh uncached debug instance per
   operation, [Decision 6](#decision-6--opt-in-shape-pass-the-class--one-fresh-instance-per-operation-requires-strawberry-03160));
   a nested `allItems { edges { node { name category { name } } } }`
   selection over `seed_data(2)` rows → the captured **SELECT rows**
   (filter on `isSelect` — transaction rows may interleave,
   [Edge cases](#edge-cases-and-constraints)) match the optimizer's
   planned **visibility-safe two-query shape**: exactly one
   `products_item` slice and exactly one `products_category` prefetch
   query, with **no** `products_item`/`products_category` JOIN and no
   per-item category queries ([Goals](#goals) item 5 — `CategoryType`'s
   custom `get_queryset` makes the optimizer plan a `Prefetch`, never
   `select_related`, so a joined-single-query assertion would contradict
   the shipped visibility contract; reuse the semantic row assertions the
   existing
   `test_products_api.py::test_products_optimizer_merges_duplicate_root_field_nodes_over_http`
   proof already pins). The item row's `sql` shows the projected column
   list — the payload demonstrating
   [`only()` projection][glossary-only-projection] / planning in one
   assertion set.
3. **Mutation capture.** A products `createItem` mutation with fully
   specified setup — no such pre-permissioned writer exists in
   `create_users`' fixture set, so the scenario builds one: `create_users(1)`
   and `seed_data(1)` (auth setup may precede the catalog seed — the
   "first domain-setup line" rule governs product/catalog setup, [DRY
   D3](#helper-reuse-obligations-dry)); grant the **non-staff**
   `view_item_1` user only
   `Permission(codename="add_item", content_type__app_label="products")`
   (the `test_client_api.py` permitted-writer precedent — never the staff
   superuser, per the least-permission rule), re-fetch the user after the
   grant to discard the stale permission cache; derive a **visible**
   category `GlobalID` from the seeded data and pass it as the mutation's
   required `categoryId` (`Item.category` is non-null); authenticate via
   `with client.login(user):` → `debug.sql` contains an `INSERT` row with
   `isSelect is False`, beside the pipeline's SELECTs (and any
   `BEGIN` / `COMMIT` rows Django's own transaction accounting logs —
   assert by statement prefix, never by position or total, [Edge
   cases](#edge-cases-and-constraints)) — the write path captured like the
   read path.
4. **Resolver exception.** A probe-schema field that raises
   (`ZeroDivisionError`) → response carries the GraphQL error AND
   `debug.exceptions == [one row]` with `excType ==
   "<class 'ZeroDivisionError'>"`, the message, and a `stack` containing
   `"Traceback"`; `debug.sql` present (empty or not) — the two lists are
   independent
   ([Decision 9](#decision-9--exception-capture-the-results-original_error-chain-serialized-like-graphenes-wrap_exception--no-resolver-wrapping)).
5. **Validation versus execution error boundary.** An
   unknown-field selection → `errors` present, `"debug" not in
   (res.extensions or {})` — the pre-execution path
   ([Decision 7](#decision-7--hook-shape-one-sync-on_operation-generator-assembly-at-teardown-get_results-returns-the-stash)).
   A second probe field returns `None` for a non-null type: execution occurs,
   graphql-core raises a completion `TypeError`, and the response carries one
   `exceptions` row. This pins the documented result-level widening beyond
   graphene's resolver-only middleware rather than falsely treating
   `original_error` as a resolver-only marker.
6. **No-SQL operation.** `{ __typename }` → `debug == {"sql": [],
   "exceptions": []}` — both keys present, both empty
   ([User-facing API](#user-facing-api)).
7. **Off-by-default.** The same probe view mounted with a schema whose
   `extensions=` omits the debug class → response `extensions` carries no
   `debug` key and no unrelated envelope widening (asserted on the envelope
   keys — the honest claim; the release-wide Strawberry floor means
   "byte-identical to `0.0.13`" is not this scenario's contract,
   [Goals](#goals) item 3).

**Mechanics (no request):**

8. **Restore contract.** Around a direct `schema.execute_sync(...)` on an
   enabled schema: a connection whose `force_debug_cursor` was pre-set
   `True` still reads `True` after the operation (saved-value restore, the
   nested-`CaptureQueriesContext` guarantee), and one whose flag was
   `False` reads `False`; a shorter-than-snapshot `queries_log` (simulated
   reset) returns `[]` rather than raising, and a full bounded deque test
   pins the documented best-effort rollover behavior without claiming exact
   capture. A simulated failure while acquiring a later database alias proves
   the `ExitStack` restores every earlier alias and empties the active-bracket
   map before propagating the error — the one behavior a real request cannot
   produce safely, so the fake sits at the private bracket boundary, never a
   mock of Strawberry's runner ([Edge cases](#edge-cases-and-constraints)).
9. **Async color and overlap-safe restore.** An `async def` test overlaps two
   `schema.execute(...)` calls with raising async resolvers. Before creating
   either task, materialize every tested alias through `connections[...]` in
   the parent async context and record the wrapper identities. Create both
   tasks so they inherit those wrappers; assert each operation observes the
   same concrete wrapper objects, and block both resolvers until the
   coordinator depth reaches two. Release them in both completion orders.
   Each response
   populates its own exception row and carries the `debug` key; after both
   complete, every involved connection has its original
   `force_debug_cursor` value, depth returns to zero, and the private
   active-bracket map is empty. SQL content is deliberately **not**
   asserted beyond type (the documented thread-locality caveat — this test
   pins the contract that holds, not fidelity the design cannot provide);
   marked `django_db` only if it touches the ORM, per the suite's
   async-connection hygiene ([`tests/conftest.py`][tests-conftest]).
10. **Serializer units.** The exception serializer over a hand-raised
    exception (the triple's exact forms, including the
    `"<class '...'>"` `excType` shape and chained-traceback stacks); the
    SQL-row serializer over canned log entries including an `executemany`
    `"3 times: ..."` entry (`isSelect is False`, verbatim `sql`) and a
    `duration` string → float conversion; the `original_error` collector over
    a mixed error list (pure validation `GraphQLError` skipped, wrapped
    Python exception kept, explicitly raised nested `GraphQLError` kept,
    malformed cycles terminate) and over a `result is None` execution
    context (the sync pre-execution teardown shape — no rows, no raise,
    [Error shapes](#error-shapes)).
11. **`get_results` no-stash shape and idempotence.** A fresh instance's
    `get_results()` returns `{}` (never `{"debug": None}`) — the read of
    the immutable class-level `None` default, since no instance write has
    happened yet
    ([Decision 7](#decision-7--hook-shape-one-sync-on_operation-generator-assembly-at-teardown-get_results-returns-the-stash)) —
    and after a
    completed operation returns the stash under exactly the `"debug"` key
    — **twice in a row, identically** (direct proof that the read is pure);
    the payload round-trips `json.dumps` (the JSON-serializability guard).
    Separately, an instrumented validation-failure operation whose
    `on_operation` teardown raises proves the real engine path calls
    `get_results()` once for the abandoned early result and once for the
    recovery result ([Error shapes](#error-shapes)).
12. **Masking-extension ordering.** Two direct `schema.execute_sync(...)`
    runs over a raising resolver: with
    `extensions=[MaskErrors, DjangoDebugExtension]` the response's
    `errors` are masked while `debug.exceptions` carries the one unmasked
    row; with the order reversed
    (`[DjangoDebugExtension, MaskErrors]`), `debug.exceptions == []` —
    the LIFO teardown dependency pinned in both directions
    ([Decision 9](#decision-9--exception-capture-the-results-original_error-chain-serialized-like-graphenes-wrap_exception--no-resolver-wrapping)).
13. **Concurrent sync isolation at the floor.** One schema with the class
    opt-in executes two distinguishable blocking resolvers concurrently in a
    `ThreadPoolExecutor`, synchronized by one small barrier/event helper;
    the two resolver variants are one parameterized body distinguished by
    marker/message values, not two copied bodies. The resolvers perform
    **no ORM work in the executor threads** — actual concurrent SQLite ORM
    would add transaction-visibility, locking, and connection-lifetime
    problems unrelated to the lifecycle regression being pinned. Isolation
    is proved by distinct resolver **exception/argument markers**, the
    captured per-thread wrapper identities, and each thread-local wrapper's
    restored flag: each response must contain only its own exception marker,
    and both connections must restore their prior debug flags — together
    proving fresh extension instances. (If a future revision insists on SQL
    markers here, it must instead require `transactional_db`, committed seed
    data, and each worker closing its thread-local database connection
    before the thread exits — the no-ORM shape is simpler and proves the
    same 0.315-vs-0.316 lifecycle contract.) Run
    this scenario in the isolated `strawberry-graphql==0.316.0` floor
    environment as well as the normal suite — selected by **node id**, the
    same test both times, never a copied script, with the coverage-free
    `-o addopts=...` override for the targeted run. This is the regression
    that fails under the old cached `_sync_extensions` lifecycle and proves
    the dependency bump's stated reason. Because each executor thread owns
    distinct thread-local database wrappers, this scenario does not prove
    same-wrapper coordinator refcounting; scenario 9 owns that assertion.

14. **Merge precedence and result-map replacement.** Small same-key probe
    extensions prove later extension-list entries win in both sync and async
    execution. The async case also seeds
    `ExecutionContext.extensions_results` and proves that overlay has final
    precedence. A pre-populated `ExecutionResult.extensions` map is replaced,
    not merged, by schema result handling.

15. **Nested sync attribution boundary.** A same-thread outer operation
    invokes a nested sync operation while sharing one concrete database
    wrapper and query log. Both flags restore correctly, the inner payload
    contains its interval, and the outer payload intentionally also contains
    the inner SQL rows.

**Revision-8 additions (16 live-sharded; 17–21 mechanics):**

16. **Sharded-tier multi-database capture** (live, gated on
    `FAKESHOP_SHARDED=1` — the existing [`test_multi_db.py`][test-multi-db]
    infrastructure). A real query routed to `shard_b` through a
    debug-enabled probe schema → a captured row reports
    `alias == "shard_b"` and the correct vendor, and **both** configured
    aliases restore their prior flags. This is the only real
    multi-database proof — Decision 10's per-alias contract must not rest
    solely on `alias == "default"` assertions plus fakes
    ([Decision 10](#decision-10--multi-database-capture-every-alias-in-connectionsall-one-bracket-each)).
17. **Diagnostic non-interference.** Inject a malformed backend log entry
    (or a failing snapshot/serializer) at the private boundary so teardown
    collection fails after execution produced a result → the original
    `data` / `errors` survive untouched, every saved flag restores, and the
    payload degrades to the successfully captured rows or empty lists —
    the two-phase failure policy's post-execution half
    ([Error shapes](#error-shapes)).
18. **Cursor-construction lifetime boundary.** Both directions of the
    documented boundary
    ([Decision 4](#decision-4--fidelity-djangos-own-debug-cursor-via-a-force_debug_cursor-bracket-not-a-cursor-wrap-port)):
    a cursor opened *before* acquire stays uninstrumented when executed
    inside the bracket, and a debug cursor opened *inside* keeps logging
    when executed after release — pinned as documentation of the
    Django-native boundary, never "fixed" by porting the rejected cursor
    wrap.
19. **Transaction-boundary scope.** An `atomic()` block owned by a
    resolver emits captured `BEGIN` / `COMMIT` rows (inclusion); a schema
    execution wrapped by an **outer** `transaction.atomic()` proves the
    enclosing boundary's statements are not captured (exclusion — the
    `ATOMIC_REQUESTS` shape without rebuilding HTTP infrastructure)
    ([Edge cases](#edge-cases-and-constraints)).
20. **Sibling-hook SQL ordering.** A small sibling extension whose
    `on_operation` performs marker SQL before and after its `yield`, run
    in both `extensions=` list orders → prove exactly which markers land
    in the debug payload per order — documenting the SQL-scope ordering
    dependency beside the masking/key-collision ones
    ([Edge cases](#edge-cases-and-constraints)).
21. **`original_error` hop policy.** A self-cycle, a multi-node cycle, and
    a long acyclic chain exceeding the 64-hop ceiling each terminate
    deterministically, returning the last unique candidate seen
    ([Decision 9](#decision-9--exception-capture-the-results-original_error-chain-serialized-like-graphenes-wrap_exception--no-resolver-wrapping)).

Coverage: the package gate is `fail_under = 100` and `extensions/debug.py`
is package code — every branch has a named owner above: the bracket loop and
both restore directions (1, 8), the bounded-log fallback (8), both
serializers, the chain walk/cycle guard, and its `result is None` guard (4,
10), the empty and populated
`get_results` directions plus direct and real-engine idempotence (6, 7, 11),
the masking-order dependency (12), per-request sync isolation (13),
merge/replacement semantics (14), nested sync attribution (15), the async
hook color and shared-wrapper overlap (9), the mutation/query independence
(3), the real sharded per-alias capture (16), the post-execution
non-interference degrade path (17), both cursor-lifetime directions (18),
the transaction inclusion/exclusion boundary (19), sibling-hook SQL
ordering (20), and the hop-capped chain walk (21). If
implementation finds a branch unreachable through these (e.g. a defensive
guard), it gets its own targeted unit the same way — named owner, never a
blanket claim.

## Doc updates

Slice 2 — implemented-on-main docs; Slice 3 — the release-status wording
(this card owns both,
[Decision 12](#decision-12--this-card-completes-the-joint-0014-cut-and-owns-the-version-bump)):

- [`docs/GLOSSARY.md`][glossary] (Slice 2, via the glossary DB +
  [`scripts/build_glossary_md.py`][build-glossary-md] — the file is
  DB-rendered, never hand-edited) — the
  [Response-extensions debug middleware][glossary-response-extensions-debug-middleware]
  entry body grows the implemented contract: the
  `django_strawberry_framework.extensions` import path and class-form
  opt-in, the `debug` key and two-list payload, the six SQL fields with the
  named omissions and the `executemany` form, the exception triple and the
  nested `original_error` walk (including the documented result-level
  widening), the reference-counted `force_debug_cursor` bracket and its
  `DEBUG`-independence, the best-effort bounded-log behavior, the
  `strawberry-graphql>=0.316.0` isolation floor **with its release-wide
  migration notes** ([Decision 6](#decision-6--opt-in-shape-pass-the-class--one-fresh-instance-per-operation-requires-strawberry-03160)),
  the per-alias multi-DB
  behavior, the `callproc()` omission, the cursor-construction
  capture-interval boundary, the transaction-boundary scope (enclosing
  `ATOMIC_REQUESTS` excluded), the two-phase failure policy (setup
  fail-loud, post-execution non-interfering degrade), the nested-sync
  attribution boundary,
  extension-list merge precedence, async context-results precedence, result-map
  replacement, the
  pre-execution-error no-key rule, the dev-only security caveat with the
  full disclosure enumeration (interpolated SQL values, traceback paths,
  retention, downstream copies), and the
  async SQL caveat; the real cookbook migration from the aggregate `_debug`
  field + `GRAPHENE["MIDDLEWARE"]` pair to the one extension class; and the
  resulting client move to `response.extensions.debug` — plus the "distinct
  from the [Debug-toolbar middleware][glossary-debug-toolbar-middleware]" paragraph
  updated to shipped tense in both entries' cross-references.
- [`docs/TREE.md`][tree] (Slice 2) — regenerated via
  [`scripts/build_tree_md.py`][build-tree-md] after the
  `TrackedPath.is_current` updates while the card remains WIP:
  the package tree's planned `extensions/` rows resolve to real
  docstring-derived rows; the test tree gains `tests/extensions/test_debug.py`
  and `examples/fakeshop/test_query/test_debug_extension_api.py`.
- [`config/schema.py`][config-schema] (Slice 2) — the docstring's "has no
  direct Strawberry analogue" sentence rewritten
  ([Decision 2](#decision-2--card-scope-boundary-the-extension-ships-alone--no-django-middleware-no-schema-field-no-fakeshop-always-on-wiring)).
- [`GOAL.md`][goal] (Slice 2) — success criterion 7's scoping
  clarification (the import-only promise covers `Meta`-driven domain
  declarations; engine configuration migrates by documented recipe), so the
  debug migration becomes a documented application of the criterion rather
  than an unresolved exception to it
  ([Goal and cookbook cross-reference](#goal-and-cookbook-cross-reference)).
- **Slice 3 (the cut):** the GLOSSARY status flips (`shipped (0.0.14)`) for
  all four `0.0.14` surfaces and their companion entries
  ([Channels request adapter][glossary-channels-request-adapter],
  [`require_optional_module`][glossary-require-optional-module]) plus the
  package-version line and the [Joint version cut][glossary-joint-version-cut]
  wording; [`README.md`][readme]'s Status section and capability bullets;
  [`docs/README.md`][docs-readme]'s "Coming next — remaining alpha
  (`0.0.14`)" block resolving into "Shipped today"; [`TODAY.md`][today]'s
  "Shipped package capabilities not exercised by products" section gaining
  the missing `0.0.14` capabilities (only the router is listed today, in
  shipped tense already); and `CHANGELOG.md`'s `0.0.14` section — the
  last under this spec's explicit Slice-3 grant (per [`AGENTS.md`][agents]
  the file is otherwise off-limits; the [`docs/SPECS/NEXT.md`][next]
  convention places the grant in the owning spec's release slice, and the
  maintainer's commit review remains the final gate). Only after those cut
  items succeed, the final card wrap runs in the ordered sequence the
  [Slice checklist](#slice-checklist) pins: DB updates and the Done flip,
  **then** the companion `*-terms.csv` import, **then** the
  GLOSSARY/TREE/KANBAN renders (the importer writes rows the builders
  render), closing with every importer/builder `--check` mode. The GLOSSARY
  status flips enumerate every spec-044 term in the companion CSV whose
  `planned for 0.0.14` status changes — not only the headline surfaces.

## Risks and open questions

- **The card's "middleware" word vs. the shipped shape.** The card title
  (and the feature's board name) says middleware; the shipped unit is a
  `SchemaExtension`, per the card's own Architectural posture ("our
  Strawberry-native shape is a `SchemaExtension` (operation-scoped), not a
  Django middleware"). Recorded per the
  [`docs/SPECS/NEXT.md`][next] prefer-the-card rule rather than silently
  reconciled — but the card resolves its own title here, so **preferred
  answer:** ship the extension, keep "Response-extensions debug middleware"
  as the card-facing feature name (the GLOSSARY heading stays, its body
  names the class). **Fallback:** none needed — no reading of the card asks
  for an actual Django middleware.
- **Exposure selectivity: all-or-nothing vs. graphene's per-query pull.**
  With the map exposure, an enabled schema pays capture + payload on every
  operation, where graphene consumers select `_debug` only on the queries
  they are diagnosing. **Preferred answer for `0.0.14`:** accept it — the
  intended deployment is a development settings branch (`DEBUG`-gated
  `extensions=` assembly in the consumer's schema module), where always-on
  is the point. **Fallback:** a constructor predicate
  (`DjangoDebugExtension.when(callable)`) or a request-header gate as a
  follow-on knob once a real consumer asks — additive, no shape change
  (any such gate reads the request through
  `utils/permissions.request_from_info`, the package's one sanctioned
  request-access entry point — the v1 extension itself never touches the
  context).
- **The cookbook debug migration is not import-only.** [`GOAL.md`][goal]
  criterion 7 promises the `Meta` mental model carries over with "only the
  import line" changing, but the real cookbook's debug integration is not a
  `Meta` surface: it is an aggregate `_debug` field plus a settings
  middleware entry, and clients select that field. A Strawberry-native
  `_debug` facade could preserve that wire contract without any Graphene
  runtime, so the no-Graphene non-goals do not by themselves decide this —
  the deciding ground is
  [Decision 3](#decision-3--exposure-the-response-extensions-map-under-the-debug-key-not-a-schema-level-_debug-field)'s
  rejection of a permanent schema surface. **Preferred answer:** keep the
  Strawberry-native response-extension design, document the exact
  three-part migration in [Goal and cookbook cross-reference](#goal-and-cookbook-cross-reference),
  and resolve the criterion-7 contradiction at its source: Slice 2 edits
  [`GOAL.md`][goal] to scope the import-only promise to `Meta`-driven
  domain declarations, with project-level engine configuration migrating by
  documented recipe ([Doc updates](#doc-updates)). **Fallback / follow-on:**
  add a schema-field facade only if real migrations demonstrate that
  preserving `_debug` wire compatibility outweighs the permanent schema
  surface and duplicate exposure matrix (the facade imports the
  module-level serializers [DRY D4](#helper-reuse-obligations-dry) pins —
  nothing re-spelled).
- **Cross-operation SQL attribution.** Statements executed on `sync_to_async` executor
  threads escape the event-loop thread's bracket — under async execution
  the `sql` list is typically empty. Concurrent async tasks overlap the same
  coordinator entry only when they inherit pre-materialized wrapper objects;
  independently materialized aliases may be distinct. For shared wrappers,
  restoration is safe but rows are not operation-local if async-unsafe ORM
  work runs on the loop thread. Likewise, nested same-thread sync operations
  restore safely but the outer length snapshot includes the inner interval
  ([Edge cases](#edge-cases-and-constraints)).
  **Preferred answer:** guarantee clean restoration and document the fidelity
  and best-effort attribution caveats (ordinary non-reentrant sync paths —
  every fakeshop surface and Django's default view — capture fully;
  exceptions capture is color-agnostic); this matches the
  single upstream's own thread-local scope. **Fallback / follow-on:** a
  per-operation-isolated instrumentation design — worth its own card if
  async consumers report gaps. (An earlier draft's categorical rejection of
  routing the bracket through `sync_to_async(thread_sensitive=True)` rested
  on a **false universal premise** — that thread-sensitive work always
  shares one process-wide thread. That is only asgiref's *fallback*:
  Django's ASGI handler wraps each HTTP request in a
  `ThreadSensitiveContext`, which selects a per-request single-thread
  executor, so worker-thread bracketing **may be viable** for normal ASGI
  HTTP inside the inherited request context. It is still not universal —
  direct `schema.execute()`, batching, and work escaping that context lack
  the per-request executor — so the follow-on must be accepted or rejected
  against a **real ASGI-request prototype**, not this spec's prose. v1's
  honest "async SQL is typically empty" limitation stands either way.)
- **Engine ordering coupling.** The no-`debug`-key-on-pre-execution-errors
  behavior rides the verified 0.316.0 call ordering (`get_results` inside
  the operation context on early returns, after it on the happy path). A
  future Strawberry release could reorder — the failure mode is benign (the
  key appearing with empty lists on validation errors, or vanishing on
  happy paths, both caught loudly by scenarios 1 and 5 under a refreshed
  lock). **Preferred answer:** accept; `uv.lock` plus the regression tests
  pin the resolved version's semantics, and the `>=0.316.0` lower bound
  excludes the known cached-sync lifecycle (an open bound cannot itself
  "pin" future semantics —
  [Decision 6](#decision-6--opt-in-shape-pass-the-class--one-fresh-instance-per-operation-requires-strawberry-03160)'s
  migration notes).
  **Fallback:** assemble defensively in both teardown *and* `get_results`
  (idempotent build) if a reorder ever lands.
- **`queries_log` eviction under pathological operations.** An operation
  that rolls over a full bounded deque can lose old operation rows and, when
  the length remains unchanged from the snapshot, can report no rows at all
  ([Edge cases](#edge-cases-and-constraints)). **Preferred answer:** accept
  and document the exact best-effort boundary; Django's own capture context
  has the same length-snapshot limitation. A reliable `truncated: true`
  marker would require operation-local instrumentation or a monotonic query
  counter, not merely another comparison against deque length. **Fallback:**
  a separate fidelity card that changes the capture source.
- **Payload size on large operations.** A thousand-row capture serializes a
  thousand interpolated SQL strings into every response. **Preferred
  answer:** accept for a dev tool — the operation that emits a thousand
  statements is exactly the one the developer needs to see, and the N+1 it
  reveals is the package's whole pitch. **Fallback:** a row-cap knob,
  follow-on with the other knobs.

## Out of scope (explicitly tracked elsewhere)

- **The schema-level `_debug` field flavor** — rejected for `0.0.14`
  ([Decision 3](#decision-3--exposure-the-response-extensions-map-under-the-debug-key-not-a-schema-level-_debug-field));
  a future card could add it over the same capture core if per-query
  selectivity earns a payer.
- **Cursor-wrap fidelity** (`rawSql` / `params` / absolute timestamps / the
  Postgres transaction quartet) — the documented narrowing
  ([Decision 8](#decision-8--the-sql-row-shape-graphenes-wire-names-narrowed-to-what-djangos-log-supports));
  a fidelity upgrade is a swap of the capture source behind the same row
  shape.
- **Fakeshop opting into the extension** (and replacing the probe URLconf
  with the shipped URLconf in the existing live tests) — the
  fakeshop-activation beta card
  ([`TODO-BETA-053-0.1.5`][kanban]) is the natural host
  ([Decision 11](#decision-11--test-strategy-split-live-http-behavior-from-package-tier-mechanics)).
- **Production-gating knobs** (enable predicates, slow-query thresholds,
  row caps, redaction) — follow-on once a consumer asks
  ([Risks](#risks-and-open-questions)).
- **Thread-sensitive async instrumentation** — the named follow-on
  ([Risks](#risks-and-open-questions)).
- **Subscriptions** — no package subscription surface exists
  ([Non-goals](#non-goals)).
- **Experimental incremental execution** (`@defer` / `@stream` payload
  semantics) — excluded from the `0.0.14` contract
  ([Non-goals](#non-goals)); design work for initial/subsequent payload
  debug data is a follow-on.
- **Explicitly cross-thread-shared connection wrappers**
  (`inc_thread_sharing()`) — unsupported / best-effort
  ([Edge cases](#edge-cases-and-constraints)); the non-interference rule
  still protects the response.
- **The `0.1.0` milestone chores** (alpha-constraint lifts, the board's
  progress section, milestone prose) — [`TODO-BETA-045-0.1.0`][kanban]; this
  card's cut is a routine patch cut
  ([Decision 12](#decision-12--this-card-completes-the-joint-0014-cut-and-owns-the-version-bump)).

## Definition of done

- [ ] `django_strawberry_framework/extensions/debug.py` exists, with module
      + symbol docstrings, exposing `DjangoDebugExtension(SchemaExtension)`
      implementing the sync `on_operation` bracket and `get_results` per
      [Decisions 4](#decision-4--fidelity-djangos-own-debug-cursor-via-a-force_debug_cursor-bracket-not-a-cursor-wrap-port)–[10](#decision-10--multi-database-capture-every-alias-in-connectionsall-one-bracket-each)
      — the card's DoD row 1, with the exposure and fidelity choices pinned
      in this spec
      ([Decision 3](#decision-3--exposure-the-response-extensions-map-under-the-debug-key-not-a-schema-level-_debug-field)
      / [Decision 4](#decision-4--fidelity-djangos-own-debug-cursor-via-a-force_debug_cursor-bracket-not-a-cursor-wrap-port),
      the card's DoD row 2 — both resolved to the card's own named
      defaults, sharpened).
- [ ] The payload lands under `extensions["debug"]` with `sql` rows carrying
      `vendor` / `alias` / `sql` / `duration` / `isSlow` / `isSelect` and
      `exceptions` rows carrying `excType` / `message` / `stack` — graphene's
      wire names where the fidelity supports them, every narrowing — including
      the `callproc()` omission and nested-sync attribution boundary — named
      in the GLOSSARY entry and the module docstring (the card's DoD row 3)
      ([Decision 8](#decision-8--the-sql-row-shape-graphenes-wire-names-narrowed-to-what-djangos-log-supports)).
- [ ] Off by default; the opt-in is the class in `strawberry.Schema(...)`'s
      `extensions=` list (the card's DoD row 4); with the extension absent,
      no debug instrumentation runs and no `debug` key is added (Test plan
      scenario 7 — the Strawberry-floor raise is a separate release-wide
      change with its own migration notes)
      ([Decision 6](#decision-6--opt-in-shape-pass-the-class--one-fresh-instance-per-operation-requires-strawberry-03160)).
- [ ] `from django_strawberry_framework.extensions import DjangoDebugExtension`
      resolves; nothing is added to the package root
      ([Decision 5](#decision-5--symbol-and-home-djangodebugextension-in-extensionsdebugpy-exported-from-the-extensions-subpackage--never-the-package-root)).
- [ ] **No new dependency is added**, but the existing Strawberry constraint
      is raised to `strawberry-graphql>=0.316.0` in `[project].dependencies`
      and `uv.lock`; `[dependency-groups].dev` remains untouched. Concurrent
      sync isolation passes at that exact floor in an isolated throwaway venv
      (never the shared `.venv`; coverage disabled via the `-o addopts=...`
      override), the command/outcome are recorded, and the floor is durably
      exercised by a CI node force-installing `0.316.0`
      ([`.github/workflows/django.yml`][workflow-django]).
- [ ] The split tests cover the [Test plan](#test-plan):
      `examples/fakeshop/test_query/test_debug_extension_api.py` owns real
      probe-URLconf HTTP against fakeshop models (the card's DoD row 5,
      "against a fakeshop request that emits SQL") under schema-reload,
      `seed_data`, and [`TestClient`][glossary-testclient] disciplines;
      `tests/extensions/test_debug.py` owns request-impossible mechanics.
      [Decision 11](#decision-11--test-strategy-split-live-http-behavior-from-package-tier-mechanics)
      records the placement rule. The package coverage gate (`fail_under =
      100`) holds with `extensions/` included, each branch mapped to a named
      owner.
- [ ] The Slice 2 doc updates land per [Doc updates](#doc-updates): the
      GLOSSARY entry body (via the DB + re-render), the regenerated
      [`docs/TREE.md`][tree], the [`config/schema.py`][config-schema]
      docstring correction, the [`GOAL.md`][goal] clarification, and the
      "documented as the
      response-side counterpart to `DONE-042-0.0.14`" cross-references in
      both entries. The GLOSSARY entry includes the concrete cookbook
      migration from `_debug` + `DjangoDebugMiddleware` to the aggregate
      extension opt-in and response-map read (the card's DoD row 6).
- [ ] **The joint `0.0.14` cut lands in Slice 3**
      ([Decision 12](#decision-12--this-card-completes-the-joint-0014-cut-and-owns-the-version-bump)):
      the version quintet reads `0.0.14`
      ([`pyproject.toml`][pyproject], [`__init__.py`][init],
      [`tests/base/test_init.py`][test-base-init], the GLOSSARY
      package-version line, the `uv.lock` package entry); the GLOSSARY
      statuses for `041` / `042` / `043` / `044` (+ companions) read
      `shipped (0.0.14)`; the [`README.md`][readme] /
      [`docs/README.md`][docs-readme] / [`TODAY.md`][today] release wording
      moved; the `CHANGELOG.md` `0.0.14` section written under this spec's
      Slice-3 grant; and only then the card reads `DONE-044-0.0.14` after the
      DB-backed final wrap and terms import.
- [ ] `uv run ruff format .` / `ruff check --fix .` clean after every slice;
      pre-commit hooks run before any commit the maintainer requests; no
      `pytest` unless the maintainer asks (the [`START.md`][start] workflow
      rules).

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[workflow-django]: ../.github/workflows/django.yml
[goal]: ../GOAL.md
[kanban]: ../KANBAN.md
[pyproject]: ../pyproject.toml
[readme]: ../README.md
[start]: ../START.md
[today]: ../TODAY.md

<!-- docs/ -->
[docs-readme]: README.md
[glossary]: GLOSSARY.md
[glossary-async-sql-capture-boundary]: GLOSSARY.md#async-sql-capture-boundary
[glossary-bounded-query-log-rollover]: GLOSSARY.md#bounded-query-log-rollover
[glossary-channels-request-adapter]: GLOSSARY.md#channels-request-adapter
[glossary-configurationerror]: GLOSSARY.md#configurationerror
[glossary-cookbook-parity]: GLOSSARY.md#cookbook-parity
[glossary-debug-exception-row]: GLOSSARY.md#debug-exception-row
[glossary-debug-payload-availability]: GLOSSARY.md#debug-payload-availability
[glossary-debug-sql-row]: GLOSSARY.md#debug-sql-row
[glossary-debug-toolbar-middleware]: GLOSSARY.md#debug-toolbar-middleware
[glossary-developer-only-debug-posture]: GLOSSARY.md#developer-only-debug-posture
[glossary-django-debug-cursor-capture]: GLOSSARY.md#django-debug-cursor-capture
[glossary-django-trac-37064]: GLOSSARY.md#django-trac-37064-hardening
[glossary-djangodebugextension]: GLOSSARY.md#djangodebugextension
[glossary-djangographqlprotocolrouter]: GLOSSARY.md#djangographqlprotocolrouter
[glossary-djangooptimizerextension]: GLOSSARY.md#djangooptimizerextension
[glossary-eviction-simulated-absence]: GLOSSARY.md#eviction-simulated-absence
[glossary-finalize-django-types]: GLOSSARY.md#finalize_django_types
[glossary-get-queryset]: GLOSSARY.md#get_queryset-visibility-hook
[glossary-graphene-debug-migration]: GLOSSARY.md#graphene-debug-migration
[glossary-graphqltestcase]: GLOSSARY.md#graphqltestcase
[glossary-hard-dependency]: GLOSSARY.md#hard-dependency
[glossary-joint-version-cut]: GLOSSARY.md#joint-version-cut
[glossary-live-first-coverage-mandate]: GLOSSARY.md#live-first-coverage-mandate
[glossary-masking-extension-ordering]: GLOSSARY.md#masking-extension-ordering
[glossary-multi-database-cooperation]: GLOSSARY.md#multi-database-cooperation
[glossary-only-projection]: GLOSSARY.md#only-projection
[glossary-pep-562-lazy-export]: GLOSSARY.md#pep-562-lazy-export
[glossary-per-operation-extension-isolation]: GLOSSARY.md#per-operation-extension-isolation
[glossary-plan-cache]: GLOSSARY.md#plan-cache
[glossary-probe-urlconf]: GLOSSARY.md#probe-urlconf
[glossary-reference-counted-cursor-coordinator]: GLOSSARY.md#reference-counted-cursor-coordinator
[glossary-require-optional-module]: GLOSSARY.md#require_optional_module
[glossary-response-extension-merge-semantics]: GLOSSARY.md#response-extension-merge-semantics
[glossary-response-extensions-debug-middleware]: GLOSSARY.md#response-extensions-debug-middleware
[glossary-schema-reload-discipline]: GLOSSARY.md#schema-reload-discipline
[glossary-seed-data]: GLOSSARY.md#seed_data
[glossary-single-upstream-parity]: GLOSSARY.md#single-upstream-parity
[glossary-soft-dependency]: GLOSSARY.md#soft-dependency
[glossary-strawberry-config]: GLOSSARY.md#strawberry_config
[glossary-strawberry-extension-lifecycle]: GLOSSARY.md#strawberry-extension-lifecycle
[glossary-strictness-mode]: GLOSSARY.md#strictness-mode
[glossary-testclient]: GLOSSARY.md#testclient
[tree]: TREE.md

<!-- docs/SPECS/ -->
[next]: SPECS/NEXT.md
[spec-038]: SPECS/spec-038-form_mutations-0_0_12.md
[spec-041]: SPECS/spec-041-channels_router-0_0_14.md
[spec-042]: SPECS/spec-042-debug_toolbar-0_0_14.md
[spec-043]: SPECS/spec-043-test_client-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[init]: ../django_strawberry_framework/__init__.py
[middleware-debug-toolbar]: ../django_strawberry_framework/middleware/debug_toolbar.py
[optimizer-extension]: ../django_strawberry_framework/optimizer/extension.py

<!-- tests/ -->
[test-base-init]: ../tests/base/test_init.py
[tests-conftest]: ../tests/conftest.py

<!-- examples/ -->
[config-schema]: ../examples/fakeshop/config/schema.py
[schema-reload]: ../examples/fakeshop/schema_reload.py
[test-multi-db]: ../examples/fakeshop/test_query/test_multi_db.py

<!-- scripts/ -->
[build-glossary-md]: ../scripts/build_glossary_md.py
[build-kanban-md]: ../scripts/build_kanban_md.py
[build-tree-md]: ../scripts/build_tree_md.py

<!-- .venv/ -->
[venv-base-extension]: ../.venv/lib/python3.14/site-packages/strawberry/extensions/base_extension.py
[venv-django-base]: ../.venv/lib/python3.14/site-packages/django/db/backends/base/base.py
[venv-django-test-utils]: ../.venv/lib/python3.14/site-packages/django/test/utils.py
[venv-django-utils]: ../.venv/lib/python3.14/site-packages/django/db/backends/utils.py
[venv-extensions-context]: ../.venv/lib/python3.14/site-packages/strawberry/extensions/context.py
[venv-runner]: ../.venv/lib/python3.14/site-packages/strawberry/extensions/runner.py
[venv-schema]: ../.venv/lib/python3.14/site-packages/strawberry/schema/schema.py

<!-- External -->
[upstream-cookbook-recipes-schema]: ../../django-graphene-filters/examples/cookbook/cookbook/recipes/schema.py
[upstream-cookbook-schema]: ../../django-graphene-filters/examples/cookbook/cookbook/schema.py
[upstream-cookbook-settings]: ../../django-graphene-filters/examples/cookbook/cookbook/settings.py
[upstream-debug-init]: ../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/__init__.py
[upstream-debug-middleware]: ../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/middleware.py
[upstream-debug-types]: ../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/types.py
[upstream-exception-formating]: ../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/exception/formating.py
[upstream-exception-types]: ../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/exception/types.py
[upstream-sql-tracking]: ../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/sql/tracking.py
[upstream-sql-types]: ../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/sql/types.py
[upstream-strawberry-extension-isolation]: https://github.com/strawberry-graphql/strawberry/issues/4369
