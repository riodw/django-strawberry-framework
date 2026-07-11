# Spec: Response-extensions debug middleware — `DjangoDebugExtension` in `extensions/debug.py`, executed SQL and raised exceptions in the GraphQL response's `extensions["debug"]` map

Planned for `0.0.14` (card [`WIP-ALPHA-044-0.0.14`][kanban]); **this card
completes the joint `0.0.14` cut and owns the version bump**
([Decision 12](#decision-12--this-card-completes-the-joint-0014-cut-and-owns-the-version-bump)).
This card adds the package's **in-response debug surface**: a new
`django_strawberry_framework/extensions/debug.py` module exposing
`DjangoDebugExtension`, a Strawberry `SchemaExtension` that captures the
executed SQL queries and execution exceptions for the in-flight GraphQL
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

Status: **PLANNED — no slice built yet.**
Three slices (the card is an M with one module, two test files, and the joint
cut's mechanically-wide doc alignment): Slice 1 (**the `extensions/`
subpackage + `extensions/debug.py` + split live/mechanics coverage** — the
whole public surface and its coverage land in one commit, green under the
`fail_under = 100` gate), Slice 2 (**docs + card wrap** — the
implemented-contract [`docs/GLOSSARY.md`][glossary] entry-body update, the
regenerated [`docs/TREE.md`][tree], the stale
[`config/schema.py`][config-schema] docstring sentence, and the kanban card
flip), and Slice 3 (**the joint `0.0.14` cut** — the version quintet, the
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

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the
vocabulary used throughout the spec:

- [Response-extensions debug middleware][glossary-response-extensions-debug-middleware]
  — the subject. The glossary already pins the planned contract: executed SQL
  and raised exceptions surfaced through the GraphQL response's `extensions`
  envelope so frontend clients can read them without the toolbar. Slice 2
  updates the entry body to the implemented contract; Slice 3 flips the
  status to `shipped (0.0.14)`.
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
tests (Slice 1), docs + card wrap (Slice 2), and the joint `0.0.14` cut
(Slice 3).** The card is an M — the module is one `SchemaExtension` subclass
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
        (never the shared `.venv`) before calling the floor supported
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
        Module + symbol docstrings state the off-by-default posture, the
        class-form opt-in, the dev-only security caveat, the
        masking-extension ordering (list the debug class after `MaskErrors`),
        and the async SQL caveat
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
  - [ ] Every new symbol carries its docstring and any
        staged-but-not-implemented seam carries a `TODO(spec-044 Slice N)`
        source anchor per [`AGENTS.md`][agents]; `uv run ruff format .` /
        `ruff check --fix .` after the edit, no pytest run unless the
        maintainer asks.
- [ ] **Slice 2 — docs + card wrap (no version bump yet)**
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
  - [ ] [`KANBAN.md`][kanban] card wrap: `044` → Done with the
        `DONE-044-0.0.14` id and its `SpecDoc` pointing at this spec (kanban
        DB edit + [`scripts/build_kanban_md.py`][build-kanban-md] /
        `build_kanban_html.py` re-render, never a hand-edit), and the spec's
        companion terms CSV imported via `manage.py import_spec_terms`.
- [ ] **Slice 3 — the joint `0.0.14` cut**
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

## Problem statement

When a GraphQL request misbehaves — too many queries, a slow query, or an
execution exception — the developer's first question is "what did
this operation actually execute?", and today the package has no in-response
answer. The [Debug-toolbar middleware][glossary-debug-toolbar-middleware]
(`0.0.14`, landed) answers it **server-side**: a browser panel over
`/graphql/` traffic, gated on `DEBUG` / `INTERNAL_IPS`, invisible to the
JavaScript client that issued the request. `graphene-django` ships the
complementary mechanism this card ports: its
[`DjangoDebugMiddleware`][upstream-debug-middleware] accumulates every
executed SQL statement and raised resolver exception into a
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
  [`strawberry/schema/schema.py`][venv-schema] attaches that map as the
  `ExecutionResult.extensions` the HTTP layer serializes into the response
  JSON. **Call-ordering fact this spec builds on** (verified in the 0.316.0
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
- **Django's own debug cursor is the fidelity source, and it is not
  `DEBUG`-bound.** [`django/db/backends/base/base.py`][venv-django-base]
  `#"queries_logged"` enables query logging when `force_debug_cursor` is set
  **or** `settings.DEBUG` is true; each connection keeps a bounded
  `queries_log` deque (`maxlen` = `queries_limit`, default 9000).
  [`django/db/backends/utils.py`][venv-django-utils] `::CursorDebugWrapper`
  logs, per `execute()`, the **interpolated** statement
  (`use_last_executed_query=True` → `self.db.ops.last_executed_query(...)`)
  and a `"%.3f"`-formatted duration; `executemany()` logs the raw
  parameterized SQL prefixed `"<N> times: "`. 
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
   executed statement, with vendor / alias / interpolated SQL / duration —
   and `extensions.debug.exceptions` — one row per execution exception
   represented by graphql-core's `original_error` chain,
   with type / message / stack — from the same JSON payload that carried
   `data`
   ([Decision 3](#decision-3--exposure-the-response-extensions-map-under-the-debug-key-not-a-schema-level-_debug-field),
   [Decision 8](#decision-8--the-sql-row-shape-graphenes-wire-names-narrowed-to-what-djangos-log-supports),
   [Decision 9](#decision-9--exception-capture-the-results-original_error-chain-serialized-like-graphenes-wrap_exception--no-resolver-wrapping)).
2. **Capture is deterministic, not `DEBUG`-dependent.** The
   `force_debug_cursor` bracket makes the same operation produce the same
   capture under `DEBUG=True` dev servers, `DEBUG=False` test runs, and
   production-shaped settings — enabling the extension is the only switch
   ([Decision 4](#decision-4--fidelity-djangos-own-debug-cursor-via-a-force_debug_cursor-bracket-not-a-cursor-wrap-port)).
3. **Off by default, one-line opt-in, zero new dependencies.** Absent from
   the `extensions=` list, the package's behavior is byte-identical to
   `0.0.13`; present (as the class), every operation on that schema carries
   the payload. No package is added and no dev-group or settings key changes;
   the existing Strawberry requirement is raised to `>=0.316.0` for
   per-request isolation
   ([Decision 6](#decision-6--opt-in-shape-pass-the-class--one-fresh-instance-per-operation-requires-strawberry-03160),
   [Decision 2](#decision-2--card-scope-boundary-the-extension-ships-alone--no-django-middleware-no-schema-field-no-fakeshop-always-on-wiring)).
4. **A graphene migrant recognizes the shape.** The row field names are
   graphene's own wire names (`vendor`, `alias`, `sql`, `duration`,
   `isSlow`, `isSelect`; `excType`, `message`, `stack`), the `is_slow`
   threshold keeps graphene's 10-second constant, and every narrowed-away
   field is named in the docs rather than silently absent
   ([Decision 8](#decision-8--the-sql-row-shape-graphenes-wire-names-narrowed-to-what-djangos-log-supports)).
5. **It composes with the optimizer.** A schema carrying both extensions
   works, and the debug payload becomes the optimizer's demonstration
   surface: the captured row list *shows* the single planned query where a
   naive resolver chain would show N+1 ([Test plan](#test-plan) scenario 2).
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
  v1 constructor is the bare engine signature, and the dev-only posture is
  documentation ([Edge cases](#edge-cases-and-constraints)). Knobs are
  follow-on material once a real consumer asks
  ([Risks](#risks-and-open-questions)).
- **Subscriptions.** The package ships no subscription surface; the
  extension's contract is pinned for query / mutation operations. Whatever
  Strawberry's subscription lifecycle does with `get_results` is untested
  and undocumented here.
- **Async SQL-capture fidelity.** Exception capture is
  execution-color-agnostic; SQL capture is guaranteed on the sync execution
  path and documented as **typically empty** under async execution, where
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
  `sql` (the executed statement — graphene also logs
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
- **`sql` rows are Django's own log entries, per alias.** Each row reports
  the connection's `vendor` and `alias`, the interpolated statement Django's
  debug cursor logged, and Django's measured duration (3-decimal precision —
  the log stores `"%.3f"`). Rows appear in per-connection log order,
  concatenated across aliases in `connections.all()` order.
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
- **Nothing else changes.** The extension never mutates the queryset, the
  context, or the result's `data` / `errors`; it is a read-only window. With
  the extension absent, response bytes are identical to `0.0.13`.

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
  *does* carry the `debug` key, reflecting whatever executed before the
  abort. On this path the engine also invokes `get_results` **twice** (the
  abandoned early return plus the recovery return) — the method is
  therefore pinned idempotent: return the stash, never mutate or pop it
  ([Decision 7](#decision-7--hook-shape-one-sync-on_operation-generator-assembly-at-teardown-get_results-returns-the-stash),
  Test plan scenario 11).
- **An exception inside the extension's own teardown** — designed against
  rather than assumed away: on the sync parse/validation paths teardown
  runs during the early return's unwind with `execution_context.result`
  still unset, so the exception collector is `None`-guarded by contract
  ([Decision 9](#decision-9--exception-capture-the-results-original_error-chain-serialized-like-graphenes-wrap_exception--no-resolver-wrapping));
  an unguarded read would raise out of the `with`-unwind and the engine
  would coerce *that* into the response, discarding the real parse error.
  Independently, the restore of every connection's `force_debug_cursor`
  rides a `finally` so an unexpected serializer failure cannot leave a
  connection permanently instrumented.
- **A consumer extension also publishing a `debug` extensions key** — the
  runner merges `get_results()` dicts in extensions-list order
  ([`runner.py`][venv-runner] `#"data.update"`), so the later-listed
  extension wins the key. Documented, not guarded: the key is the card's
  pinned contract and namespacing it away from a hypothetical collision
  would break the graphene-shaped expectation.

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
- **Wrap with `CaptureQueriesContext` instances directly.** Rejected on a
  technicality worth recording: `CaptureQueriesContext.__enter__` calls
  `connection.ensure_connection()` eagerly, which would open a database
  connection on every alias for every operation — including aliases the
  operation never touches (fakeshop's sharded mode has two). The extension
  applies the same flag-and-slice logic without forcing connections; an
  untouched alias contributes zero rows and zero connections.

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
   without a payer.

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

`DjangoDebugExtension` implements exactly two engine seams:

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
  assembled and `{}` otherwise — **idempotent** (a pure read of the stash,
  never a mutate-or-pop): the engine's coerced-exception recovery paths
  invoke it twice for one operation
  ([Error shapes](#error-shapes)).

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
   same loop-thread connection out of order.

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

Each captured statement serializes to a plain dict with exactly six keys, in
graphene's wire casing:

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
walks nested `GraphQLError.original_error` links to the terminal exception,
with an identity set preventing malformed cycles. A terminal
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
costs one attribute write and contributes zero rows; per
[Decision 4](#decision-4--fidelity-djangos-own-debug-cursor-via-a-force_debug_cursor-bracket-not-a-cursor-wrap-port)'s
third alternative, no connection is force-opened.

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
| `django_strawberry_framework/extensions/debug.py` (new) | `DjangoDebugExtension(SchemaExtension)`: sync `on_operation` generator (per-alias reference-counted `force_debug_cursor` bracket + snapshot pre-yield; `finally`-guarded materialize / slice / serialize / stash / release at teardown), `get_results()` returning the stash under `"debug"`, SQL/exception serializers, and the lock-protected active-bracket coordinator ([Decisions 4](#decision-4--fidelity-djangos-own-debug-cursor-via-a-force_debug_cursor-bracket-not-a-cursor-wrap-port)–[10](#decision-10--multi-database-capture-every-alias-in-connectionsall-one-bracket-each)) | 1 |
| `examples/fakeshop/test_query/test_debug_extension_api.py` (new) | The [Test plan](#test-plan) request-driving scenarios: real probe-URLconf HTTP via [`TestClient`][glossary-testclient], under schema-reload + `seed_data` disciplines ([Decision 11](#decision-11--test-strategy-split-live-http-behavior-from-package-tier-mechanics)) | 1 |
| `tests/extensions/test_debug.py` (new) | Request-impossible serializer, lifecycle, masking, async-shape, bounded-log, and concurrent-isolation mechanics ([Decision 11](#decision-11--test-strategy-split-live-http-behavior-from-package-tier-mechanics)) | 1 |
| [`pyproject.toml`][pyproject] / `uv.lock` | Raise the existing Strawberry floor to `>=0.316.0` and re-resolve for per-request extension isolation ([Decision 6](#decision-6--opt-in-shape-pass-the-class--one-fresh-instance-per-operation-requires-strawberry-03160)); the package's own version still moves only in Slice 3 | 1 |
| [`docs/GLOSSARY.md`][glossary] | [Response-extensions debug middleware][glossary-response-extensions-debug-middleware] entry body → implemented contract (glossary DB + re-render); status flip deferred to Slice 3 | 2 |
| [`docs/TREE.md`][tree] | Regenerated (script-rendered) after the card flips Done; `extensions/` + `tests/extensions/` planned rows resolve and the live test row appears | 2 |
| [`config/schema.py`][config-schema] | Docstring's "no direct Strawberry analogue" sentence rewritten to name the shipped extension and fakeshop's deliberate opt-out | 2 |
| [`KANBAN.md`][kanban] / `KANBAN.html` | Card wrap via DB edit + re-render; `import_spec_terms` for the companion CSV | 2 |
| [`pyproject.toml`][pyproject] / [`__init__.py`][init] / [`tests/base/test_init.py`][test-base-init] / `uv.lock` / GLOSSARY version line | The version quintet → `0.0.14` ([Decision 12](#decision-12--this-card-completes-the-joint-0014-cut-and-owns-the-version-bump)) | 3 |
| [`docs/GLOSSARY.md`][glossary] | `shipped (0.0.14)` status flips for all four `0.0.14` surfaces + companions + the [Joint version cut][glossary-joint-version-cut] wording (glossary DB + re-render) | 3 |
| [`README.md`][readme] / [`docs/README.md`][docs-readme] / [`TODAY.md`][today] | "Coming next / already landed ahead of the release" → shipped-`0.0.14` status wording | 3 |
| `CHANGELOG.md` | The `0.0.14` release section (all four cards) — under this spec's explicit Slice-3 grant | 3 |

## Helper-reuse obligations (DRY)

Reuse is named per item, and deliberate *non*-reuse carries its reason (the
[`spec-041`][spec-041] / [`spec-042`][spec-042] / [`spec-043`][spec-043]
discipline).

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
- [ ] **D-N1** (non-reuse) — the optimizer's `_context` ContextVar /
  context-stash machinery is **not** reused: that machinery exists because
  the optimizer instance is shared across requests; a per-operation
  instance ([Decision 6](#decision-6--opt-in-shape-pass-the-class--one-fresh-instance-per-operation-requires-strawberry-03160))
  makes plain attributes the simpler correct shape.
- [ ] **D-N2** (non-reuse) — no `utils/imports.py` guard
  ([`require_optional_module`][glossary-require-optional-module] /
  `require_*`): both imports are hard dependencies; a guard would be
  ceremony with no absent-dependency case to serve.
- [ ] **D-N3** (non-reuse) — graphene's [`sql/tracking.py`][upstream-sql-tracking]
  is **not** ported ([Decision 4](#decision-4--fidelity-djangos-own-debug-cursor-via-a-force_debug_cursor-bracket-not-a-cursor-wrap-port)
  alternatives); the borrow is the *field vocabulary and its semantics*
  ([Decision 8](#decision-8--the-sql-row-shape-graphenes-wire-names-narrowed-to-what-djangos-log-supports)),
  not the instrumentation.
- [ ] **D-N4** (non-reuse) — nothing is shared with
  [`middleware/debug_toolbar.py`][middleware-debug-toolbar]: the toolbar
  subclasses a third-party Django middleware over the HTTP response; this is
  an engine extension over the execution result. The only relationship is
  documentation ("distinct from", both directions,
  [Doc updates](#doc-updates)).

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
  both documented: **concurrent** async operations on one loop share the
  loop-thread connection objects, so the reference-counted bracket prevents
  flag leakage but cannot attribute rows per operation; under
  `DJANGO_ALLOW_ASYNC_UNSAFE` (which lets the loop thread run ORM directly),
  concurrent operations can capture each other's statements. The docstring
  carries all of it; the follow-on is a [Risk](#risks-and-open-questions).
  The sync path — Django's default
  `/graphql/` view, `schema.execute_sync`, every fakeshop surface — captures
  fully.
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
- **Transaction management statements appear as rows.** Savepoint
  statements (`SAVEPOINT`, `RELEASE SAVEPOINT`) route through the debug
  cursor, and connection-level `BEGIN` / `COMMIT` / `ROLLBACK` are appended
  to `queries_log` by Django's own `debug_transaction` bracket
  ([`django/db/backends/base/base.py`][venv-django-base] `#"debug_transaction"`
  wraps `_commit` / `_rollback` / `set_autocommit` whenever `queries_logged`
  is true — Django ≥ 4.2). So a mutation inside `transaction.atomic` emits
  `BEGIN` / `COMMIT` rows beside its `INSERT` (each with `isSelect: false`).
  This matches `assertNumQueries` visibility — the payload shows what
  Django's own accounting shows — and it is why the [Test plan](#test-plan)'s
  row assertions filter by `isSelect` / statement prefix rather than
  asserting positional indices or raw totals.
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
  has the same property and the same posture.)
- **`extensions`-map cohabitation.** The runner merges every extension's
  `get_results()` in list order; the `debug` key collides only if a
  consumer extension publishes the same key, in which case the later-listed
  wins ([Error shapes](#error-shapes)). The payload is
  JSON-serializable by construction (str / float / bool / list / dict
  only), so no transport encoder can choke on it.
- **Zero cost when disabled, bounded cost when enabled.** Disabled, no code
  runs (the class is not in the list). Enabled, the per-operation cost is
  the per-alias flag writes, Django's own debug-cursor overhead (the same
  cost `DEBUG=True` dev servers already pay), and one serialization pass —
  no plan interaction, no [plan-cache][glossary-plan-cache] key change, no
  queryset touch.
- **The subscription lifecycle is out of contract.** The package ships no
  subscription surface; the extension's documented behavior covers query /
  mutation operations ([Non-goals](#non-goals)).

## Test plan

Scenarios 1–7 live in
`examples/fakeshop/test_query/test_debug_extension_api.py`; scenarios 8–13
live in `tests/extensions/test_debug.py`
([Decision 11](#decision-11--test-strategy-split-live-http-behavior-from-package-tier-mechanics)).
The **request-driving group (1–7)** posts real HTTP through the probe
URLconf (a debug-enabled schema over freshly-reloaded fakeshop types; the
[schema-reload][glossary-schema-reload-discipline] +
[`seed_data`][glossary-seed-data] disciplines; posts through
[`TestClient`][glossary-testclient] with `assert_no_errors=False` where a
scenario expects errors). The **mechanics group (8–13)** needs no request.
Per the repo rule the implementation worker records the exact pytest
commands (`uv run pytest examples/fakeshop/test_query/test_debug_extension_api.py`
and `uv run pytest tests/extensions/test_debug.py`) for the maintainer
and does not run the suite unless explicitly authorized — the
[`AGENTS.md`][agents] #"Do not run pytest" workflow rule; this spec
describes the verification but does not override it.

**Request-driving (probe URLconf, real HTTP):**

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
2. **Optimizer composition.** The probe schema carries **both**
   `DjangoOptimizerExtension` (fresh instance) and `DjangoDebugExtension`;
   a nested `allItems { edges { node { name category { name } } } }`
   selection over `seed_data(2)` rows → the captured **SELECT-row** count
   (filter on `isSelect` — transaction rows may interleave,
   [Edge cases](#edge-cases-and-constraints)) matches the optimizer's
   planned shape (the joined single query, not N+1), and
   the row's `sql` contains the join — the payload demonstrating
   [`only()` projection][glossary-only-projection] / planning in one
   assertion set ([Goals](#goals) item 5).
3. **Mutation capture.** A products `createItem` mutation (write-auth
   satisfied via `TestClient.login(...)` with a permissioned user) →
   `debug.sql` contains an `INSERT` row with `isSelect is False`, beside
   the pipeline's SELECTs (and any `BEGIN` / `COMMIT` rows Django's own
   transaction accounting logs — assert by statement prefix, never by
   position or total, [Edge cases](#edge-cases-and-constraints)) — the
   write path captured like the read path.
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
   `debug` key (and, where the optimizer is the only extension, matches
   `0.0.13` behavior byte-for-byte on the envelope keys).

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
   map before propagating the error ([Edge cases](#edge-cases-and-constraints)).
9. **Async color and overlap-safe restore.** An `async def` test overlaps two
   `schema.execute(...)` calls with raising async resolvers. Each response
   populates its own exception row and carries the `debug` key; after both
   complete, every involved connection has its original
   `force_debug_cursor` value and the private active-bracket map is empty,
   regardless of completion order. SQL content is deliberately **not**
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
    `get_results()` returns `{}` (never `{"debug": None}`), and after a
    completed operation returns the stash under exactly the `"debug"` key
    — **twice in a row, identically** (the engine's coerced-exception
    recovery paths call it twice, [Error shapes](#error-shapes)); the
    payload round-trips `json.dumps` (the JSON-serializability guard).
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
    `ThreadPoolExecutor`, synchronized so both operations overlap. Each
    response must contain only its own exception message and query-derived
    marker, and both connections must restore their prior debug flags. Run
    this scenario in the isolated `strawberry-graphql==0.316.0` floor
    environment as well as the normal suite. This is the regression that
    fails under the old cached `_sync_extensions` lifecycle and proves the
    dependency bump's stated reason.

Coverage: the package gate is `fail_under = 100` and `extensions/debug.py`
is package code — every branch has a named owner above: the bracket loop and
both restore directions (1, 8), the bounded-log fallback (8), both
serializers, the chain walk/cycle guard, and its `result is None` guard (4,
10), the empty and populated
`get_results` directions plus idempotence (6, 7, 11), the masking-order
dependency (12), per-request sync isolation (13), the async hook color (9),
and the mutation/query independence (3). If
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
  `strawberry-graphql>=0.316.0` isolation floor, the per-alias multi-DB
  behavior, the
  pre-execution-error no-key rule, the dev-only security caveat, and the
  async SQL caveat; the real cookbook migration from the aggregate `_debug`
  field + `GRAPHENE["MIDDLEWARE"]` pair to the one extension class; and the
  resulting client move to `response.extensions.debug` — plus the "distinct
  from the [Debug-toolbar middleware][glossary-debug-toolbar-middleware]" paragraph
  updated to shipped tense in both entries' cross-references.
- [`docs/TREE.md`][tree] (Slice 2) — regenerated via
  [`scripts/build_tree_md.py`][build-tree-md] after the card flips Done:
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
- [`KANBAN.md`][kanban] / `KANBAN.html` (Slice 2) — card wrap via the DB +
  re-render; the companion `*-terms.csv` imported via
  `manage.py import_spec_terms` so the Done card's glossary-terms table
  renders.
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
  maintainer's commit review remains the final gate).

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
  follow-on knob once a real consumer asks — additive, no shape change.
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
  surface and duplicate exposure matrix.
- **Async SQL fidelity.** Statements executed on `sync_to_async` executor
  threads escape the event-loop thread's bracket — under async execution
  the `sql` list is typically empty. Concurrent async operations share the
  loop-thread connection wrappers; the reference-counted coordinator makes
  flag restoration safe, but cannot attribute rows if async-unsafe ORM work
  runs on that thread ([Edge cases](#edge-cases-and-constraints)).
  **Preferred answer:** guarantee clean restoration and document the fidelity
  caveat (the sync path — every fakeshop surface and Django's default view —
  captures fully; exceptions capture is color-agnostic); this matches the
  single upstream's own thread-local scope. **Fallback / follow-on:** a
  per-operation-isolated instrumentation design — worth its own card if
  async consumers report gaps. (An earlier draft's idea — route the
  bracket through `sync_to_async(thread_sensitive=True)` — is recorded
  here as **rejected**, not deferred: asgiref's thread-sensitive executor
  is one shared thread for *all* concurrent requests' ORM work, so a
  bracket planted there cannot provide per-operation row attribution.)
- **Engine ordering coupling.** The no-`debug`-key-on-pre-execution-errors
  behavior rides the verified 0.316.0 call ordering (`get_results` inside
  the operation context on early returns, after it on the happy path). A
  future Strawberry release could reorder — the failure mode is benign (the
  key appearing with empty lists on validation errors, or vanishing on
  happy paths, both caught loudly by scenarios 1 and 5 under a refreshed
  lock). **Preferred answer:** accept; the Slice-1 floor gate pins today's
  semantics at the new `0.316.0` floor and the tests pin them at the
  installed version.
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
      wire names where the fidelity supports them, every narrowing named in
      the GLOSSARY entry and the module docstring (the card's DoD row 3)
      ([Decision 8](#decision-8--the-sql-row-shape-graphenes-wire-names-narrowed-to-what-djangos-log-supports)).
- [ ] Off by default; the opt-in is the class in `strawberry.Schema(...)`'s
      `extensions=` list (the card's DoD row 4); with the extension absent,
      behavior is unchanged from `0.0.13` (Test plan scenario 7)
      ([Decision 6](#decision-6--opt-in-shape-pass-the-class--one-fresh-instance-per-operation-requires-strawberry-03160)).
- [ ] `from django_strawberry_framework.extensions import DjangoDebugExtension`
      resolves; nothing is added to the package root
      ([Decision 5](#decision-5--symbol-and-home-djangodebugextension-in-extensionsdebugpy-exported-from-the-extensions-subpackage--never-the-package-root)).
- [ ] **No new dependency is added**, but the existing Strawberry constraint
      is raised to `strawberry-graphql>=0.316.0` in `[project].dependencies`
      and `uv.lock`; `[dependency-groups].dev` remains untouched. Concurrent
      sync isolation passes at that exact floor in an isolated throwaway venv
      (never the shared `.venv`), and the command/outcome are recorded.
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
      docstring correction, the kanban card wrap, and the "documented as the
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
      Slice-3 grant.
- [ ] `uv run ruff format .` / `ruff check --fix .` clean after every slice;
      pre-commit hooks run before any commit the maintainer requests; no
      `pytest` unless the maintainer asks (the [`START.md`][start] workflow
      rules).

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[goal]: ../GOAL.md
[kanban]: ../KANBAN.md
[pyproject]: ../pyproject.toml
[readme]: ../README.md
[start]: ../START.md
[today]: ../TODAY.md

<!-- docs/ -->
[docs-readme]: README.md
[glossary]: GLOSSARY.md
[glossary-channels-request-adapter]: GLOSSARY.md#channels-request-adapter
[glossary-configurationerror]: GLOSSARY.md#configurationerror
[glossary-debug-toolbar-middleware]: GLOSSARY.md#debug-toolbar-middleware
[glossary-django-trac-37064]: GLOSSARY.md#django-trac-37064-hardening
[glossary-djangographqlprotocolrouter]: GLOSSARY.md#djangographqlprotocolrouter
[glossary-djangooptimizerextension]: GLOSSARY.md#djangooptimizerextension
[glossary-eviction-simulated-absence]: GLOSSARY.md#eviction-simulated-absence
[glossary-finalize-django-types]: GLOSSARY.md#finalize_django_types
[glossary-get-queryset]: GLOSSARY.md#get_queryset-visibility-hook
[glossary-graphqltestcase]: GLOSSARY.md#graphqltestcase
[glossary-joint-version-cut]: GLOSSARY.md#joint-version-cut
[glossary-live-first-coverage-mandate]: GLOSSARY.md#live-first-coverage-mandate
[glossary-multi-database-cooperation]: GLOSSARY.md#multi-database-cooperation
[glossary-only-projection]: GLOSSARY.md#only-projection
[glossary-pep-562-lazy-export]: GLOSSARY.md#pep-562-lazy-export
[glossary-plan-cache]: GLOSSARY.md#plan-cache
[glossary-require-optional-module]: GLOSSARY.md#require_optional_module
[glossary-response-extensions-debug-middleware]: GLOSSARY.md#response-extensions-debug-middleware
[glossary-schema-reload-discipline]: GLOSSARY.md#schema-reload-discipline
[glossary-seed-data]: GLOSSARY.md#seed_data
[glossary-single-upstream-parity]: GLOSSARY.md#single-upstream-parity
[glossary-soft-dependency]: GLOSSARY.md#soft-dependency
[glossary-strawberry-config]: GLOSSARY.md#strawberry_config
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
