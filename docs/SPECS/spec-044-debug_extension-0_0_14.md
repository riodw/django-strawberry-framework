# Spec: Response-extensions debug middleware — `DjangoDebugExtension` in `extensions/debug.py`, Django-recorded query-log SQL and raised exceptions in the GraphQL response's `extensions["debug"]` map

Shipped in `0.0.14` (card [`DONE-044-0.0.14`][kanban]). This card adds the
package's **in-response debug surface**:
`django_strawberry_framework/extensions/debug.py` exposes
`DjangoDebugExtension`, a Strawberry `SchemaExtension` that captures the
Django-recorded query-log SQL and execution exceptions for the in-flight GraphQL
operation and attaches them to the response's `extensions` map under the
`debug` key — so frontend clients, Apollo DevTools, and programmatic consumers
can read them **inside the GraphQL response itself**, without the server-side
toolbar. It is a Required **single-upstream** parity item
([Single-upstream parity][glossary-single-upstream-parity]): ⚛️
`graphene-django` ships the `DjangoDebug` subsystem
([`graphene_django/debug/`][upstream-debug-init] — the
[`DjangoDebugMiddleware`][upstream-debug-middleware] Graphene resolver
middleware, the [`DjangoDebug`][upstream-debug-types] object type, the
[`DjangoDebugSQL`][upstream-sql-types] / [`DjangoDebugException`][upstream-exception-types]
row shapes, the thread-local [cursor wrap][upstream-sql-tracking], and the
[`wrap_exception`][upstream-exception-formating] serializer), while 🍓
`strawberry-graphql-django` ships **no** equivalent (no upstream file
references `connection.queries` and no `*debug*` module exists outside the
toolbar middleware tracked by [`DONE-042-0.0.14`][kanban]). The mechanism is
deliberately distinct from the [Debug-toolbar
middleware][glossary-debug-toolbar-middleware] sibling: that is the server-side
`django-debug-toolbar` SQL-panel UI over `/graphql/` traffic; this is
in-response surfacing through the GraphQL `extensions` envelope. Both
mechanisms are useful and not mutually exclusive.

The surface is deliberately **thin and engine-riding**: Strawberry's
[`SchemaExtension`][venv-base-extension] base (part of the package's **hard**
`strawberry-graphql` dependency — no [soft dependency][glossary-soft-dependency],
no guard, no install hint, zero new dependencies) supplies the lifecycle hooks
(`on_operation`, `on_execute`) and the response-extensions merge seam
(`get_results`), and Django itself supplies the SQL fidelity — the extension
brackets each configured connection with Django's own debug cursor
(`force_debug_cursor`, the exact mechanism of
[`django.test.utils.CaptureQueriesContext`][venv-django-test-utils]) and reads
the per-connection `queries_log`, so the **capture mechanism** works
independent of `settings.DEBUG`
([Decision 4](#decision-4--fidelity-djangos-own-debug-cursor-via-a-force_debug_cursor-bracket-not-a-cursor-wrap-port)).
Exceptions come off the execution result's `GraphQLError.original_error`
chain, serialized to graphene's `excType` / `message` / `stack` field names
([Decision 9](#decision-9--exception-capture-the-results-original_error-chain-serialized-like-graphenes-wrap_exception--no-resolver-wrapping))
— no per-resolver wrapping, because Strawberry already funnels resolver
exceptions into `result.errors` with the original exception preserved. The
extension is **off by default**; the opt-in is passing the class in the
`extensions=` list of `strawberry.Schema(...)` or `DjangoSchema(...)`
([Decision 6](#decision-6--opt-in-shape-pass-the-class--one-fresh-instance-per-operation-requires-strawberry-03160)).

Two properties of the shipped class are owned by
[`spec-048`][spec-048] and only referenced here: the extension **fails closed
under `settings.DEBUG = False`** — a bare class entry is inert and logs one
warning unless the deployment spells
`lambda: DjangoDebugExtension(allow_unsafe_production=True)` (the
[debug fail-closed gate][glossary-debug-fail-closed-gate], spec-048 Decision 5) —
and the published payload is bounded by deterministic, marked
[debug payload caps][glossary-debug-payload-caps] (spec-048 Decision 6).
Everything below describes what the extension captures and publishes once that
gate admits the operation.

Status: **COMPLETE (card `DONE-044-0.0.14`).**
Three slices: Slice 1 (**the `extensions/` subpackage + `extensions/debug.py` +
split live/mechanics coverage**), Slice 2 (**implemented-contract docs**: the
[`docs/GLOSSARY.md`][glossary] entries, [`docs/TREE.md`][tree], the
[`config/schema.py`][config-schema] docstring, and the [`GOAL.md`][goal]
criterion-7 clarification), and Slice 3 (**the joint `0.0.14` cut + card
wrap**,
[Decision 12](#decision-12--this-card-completes-the-joint-0014-cut-and-owns-the-version-bump)).

Owner: package maintainer.

Related specs: [`spec-042-debug_toolbar-0_0_14.md`][spec-042] (the sibling
debug mechanism — this card is its response-side counterpart);
[`spec-043-test_client-0_0_14.md`][spec-043] (its
[`TestClient`][glossary-testclient] is the HTTP ergonomics this card's live
tests post through); [`spec-048-secure_output_defaults-0_0_14.md`][spec-048]
(the fail-closed gate, the payload caps, and the extension-order rules of the
auto-installed error policy). [`docs/GLOSSARY.md`][glossary] carries
[Response-extensions debug middleware][glossary-response-extensions-debug-middleware]
as `shipped (0.0.14)`.

Deliberative layer: the rejected alternatives and the derivations that do not
change how a decision is implemented live in the companion
[`spec-044-debug_extension-0_0_14-rationale.md`][rationale], keyed to the
decision each belongs to.

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the
vocabulary used throughout the spec:

- [Response-extensions debug middleware][glossary-response-extensions-debug-middleware]
  — the subject: Django query-log SQL and raised exceptions surfaced through
  the GraphQL response's `extensions` envelope so frontend clients can read
  them without the toolbar.
- [`DjangoDebugExtension`][glossary-djangodebugextension] — the public,
  off-by-default class exported from `django_strawberry_framework.extensions`;
  the entry is the shortest route from the import path to the complete
  response payload, lifecycle, and security contracts.
- [Strawberry extension lifecycle][glossary-strawberry-extension-lifecycle] /
  [Per-operation extension isolation][glossary-per-operation-extension-isolation] /
  [Debug payload availability][glossary-debug-payload-availability] /
  [Response-extension merge semantics][glossary-response-extension-merge-semantics]
  — the four engine boundaries an implementer must keep together: hook
  teardown, one operation state per operation, the pre-execution no-key rule,
  and extension-list merging, async context-result precedence, and
  replacement of an existing `ExecutionResult.extensions` map.
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
  posture behind the zero-new-dependency claim: Django and Strawberry are
  always installed, so their debug-cursor and extension APIs need no
  optional-import boundary.
- [Debug-toolbar middleware][glossary-debug-toolbar-middleware] — the
  `0.0.14` sibling ([`DONE-042-0.0.14`][kanban]): both mechanisms coexist,
  and this extension shares none of the toolbar's machinery.
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] — the
  structural precedent (engine-owned base, package-owned hooks, per-operation
  state bound through the shared `_OperationBoundExtension` base) **and** the
  deliberate lifecycle contrast: the optimizer is documented as a module-level
  singleton in a factory because its [plan cache][glossary-plan-cache] is
  cross-request state; the debug extension has no cross-request state, so its
  documented opt-in is the class form
  ([Decision 6](#decision-6--opt-in-shape-pass-the-class--one-fresh-instance-per-operation-requires-strawberry-03160)).
- [Joint version cut][glossary-joint-version-cut] — the rule under which this
  card, the last `0.0.14` card to land, carried the `0.0.14` cut
  ([Decision 12](#decision-12--this-card-completes-the-joint-0014-cut-and-owns-the-version-bump)).
- [Live-first coverage mandate][glossary-live-first-coverage-mandate] — the
  test-placement rule
  [Decision 11](#decision-11--test-strategy-split-live-http-behavior-from-package-tier-mechanics)
  applies directly: a probe URLconf is still a live fakeshop GraphQL API test,
  so request-visible behavior lives in `examples/fakeshop/test_query/` even
  though the shipped aggregate schema stays off by default. Only serializer
  and lifecycle mechanics that an HTTP request cannot isolate stay in
  `tests/extensions/`.
- [Schema reload discipline][glossary-schema-reload-discipline] — the fixture
  obligation the request-driving live tests inherit: any test that builds a
  schema against fakeshop types runs through the single-sited
  [`schema_reload.reload_all_project_schemas()`][schema-reload] machinery so
  registry state never leaks across collection orders.
- [`seed_data`][glossary-seed-data] — the repo's seed-helper rule applied to
  the [Test plan](#test-plan): every products-backed scenario's first
  domain-setup line is `seed_data(N)` from `apps.products.services`.
- [`TestClient`][glossary-testclient] / [`GraphQLTestCase`][glossary-graphqltestcase]
  — the `0.0.14` HTTP test ergonomics; the request-driving tests post through
  [`TestClient`][glossary-testclient] (with `assert_no_errors=False` where a
  scenario expects a GraphQL error) instead of hand-rolled `client.post(...)`
  blocks.
- [`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter] /
  [Channels request adapter][glossary-channels-request-adapter] — the
  `0.0.14` transport surface; its `graphql-transport-ws` consumer serves every
  operation through `Schema.stream`, the streaming seam
  [Decision 7](#decision-7--hook-shape-one-sync-on_operation-generator-assembly-at-teardown-get_results-returns-the-stash)'s
  `on_execute` stash exists for.
- [Soft dependency][glossary-soft-dependency] — cited as the **contrast**:
  `strawberry.extensions.SchemaExtension` ships inside the package's hard
  `strawberry-graphql` dependency and the debug cursor inside Django itself,
  so there is no guard, no install hint, no
  [eviction-simulated absence][glossary-eviction-simulated-absence] fixture,
  and no [`require_optional_module`][glossary-require-optional-module] call.
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
- [`ConfigurationError`][glossary-configurationerror] — raised by the
  constructor for a non-`bool` `allow_unsafe_production` (spec-048
  Decision 5's acknowledgement); the extension has no `Meta` surface and no
  settings key. Other misuse shapes are engine-owned (Strawberry's own
  extension machinery) or documented pass-throughs ([Error shapes](#error-shapes)).
- [`get_queryset` visibility hook][glossary-get-queryset] — untouched; noted
  because the captured SQL includes whatever the visibility hooks and the
  optimizer's `Prefetch` downgrades actually emitted — the debug payload is a
  read-only window, never a queryset participant.

## Goal and cookbook cross-reference

This design is checked against [`GOAL.md`][goal] and the working
`django-graphene-filters` cookbook rather than only against graphene-django's
debug implementation:

- **The north star is a modern Strawberry foundation without Graphene runtime
  baggage.** A Strawberry `SchemaExtension` is the engine-native aggregate
  configuration seam already demonstrated by [`GOAL.md`][goal]'s canonical
  schema (`extensions=[lambda: _optimizer]`). Per-operation extension
  construction (Strawberry `0.316.0` and later, inside the package's
  `strawberry-graphql>=0.322.2` floor) follows that foundation instead of
  building a compatibility runtime around an old engine race. This supports
  success criterion 7 (remove the source package) and the explicit non-goals
  "direct port of Graphene internals" and "Graphene compatibility runtime".
- **The recipe app does not own debug configuration.** The exact file named by
  the working-reference link,
  [`cookbook/recipes/schema.py`][upstream-cookbook-recipes-schema], defines
  only the domain nodes and `Query`. The project aggregate
  [`cookbook/schema.py`][upstream-cookbook-schema] composes that query, imports
  `DjangoDebug`, and adds `_debug`;
  [`cookbook/settings.py`][upstream-cookbook-settings] separately installs
  `DjangoDebugMiddleware`. The Strawberry port preserves
  that ownership boundary: app schemas remain untouched and the aggregate
  schema owns the one debug opt-in.
- **The migration is capability-equivalent, not wire-compatible.** A Graphene
  cookbook consumer removes the aggregate `_debug` field and the
  `GRAPHENE["MIDDLEWARE"]` entry, then adds `DjangoDebugExtension` to the
  Strawberry aggregate schema. Debugging clients stop selecting `_debug` and
  read `response.extensions.debug`. The `_debug` wire contract *could* be
  preserved without any Graphene runtime (the Strawberry-native schema-field
  facade recorded as the fallback in [Risks](#risks-and-open-questions)), so
  the reason it is not preserved is
  [Decision 3](#decision-3--exposure-the-response-extensions-map-under-the-debug-key-not-a-schema-level-_debug-field)'s
  rejection of a permanent schema surface — not the goal's no-Graphene-runtime
  constraints. [`GOAL.md`][goal] criterion 7 carries the matching scope: the
  import-only promise covers `Meta`-driven domain declarations; project-level
  engine configuration (a schema's `extensions=` list, the `GRAPHENE` settings
  block) migrates by documented recipe.
- **The payload still proves core success criteria.** Captured SQL makes
  success criterion 5's automatic ORM optimization visible, including
  `select_related` / `prefetch_related` / `only()` behavior, while exception
  rows expose failures from the declarative permission and mutation surfaces
  in criteria 4 and 6 without participating in their execution.
- **The tests belong to the target example.** `GOAL.md` names fakeshop as the
  shipped proof project. Real debug-enabled HTTP behavior therefore lives in
  `examples/fakeshop/test_query/`; package-tier tests cover only lifecycle
  mechanics that a request cannot isolate
  ([Decision 11](#decision-11--test-strategy-split-live-http-behavior-from-package-tier-mechanics)).

The resulting cookbook migration is a **debug-only delta applied after the
cookbook's broader Strawberry port** — [`GOAL.md`][goal]'s "Cookbook parity"
target example, whose ported aggregate `cookbook/schema.py` takes the
query-only shape (`finalize_django_types()`,
`_optimizer = DjangoOptimizerExtension()`,
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
`Meta`, visibility hook, or domain query field changes for debug.

## Slice checklist

Each top-level item maps to one commit / PR.

- [ ] **Slice 1 — `extensions/` subpackage + `extensions/debug.py` + split
  live/mechanics tests**
  - [ ] **Per-operation extension construction is a dependency floor.** The
        package's `strawberry-graphql` floor (`>=0.322.2` in
        `[project].dependencies`) includes Strawberry `0.316.0`'s per-operation
        construction of class/factory entries in `Schema.get_extensions()`;
        earlier releases cache the sync extension list on
        `Schema._sync_extensions`, so even a class entry becomes one shared
        instance whose `execution_context` races across requests. The floor is
        durably exercised: the minimum-support CI nodes in
        [`.github/workflows/django.yml`][workflow-django] force-install exactly
        `strawberry-graphql==0.322.2` with coverage disabled (the latest node
        keeps the coverage gate), and the suite there includes the concurrent
        sync isolation test
        ([Decision 6](#decision-6--opt-in-shape-pass-the-class--one-fresh-instance-per-operation-requires-strawberry-03160)).
  - [ ] `django_strawberry_framework/extensions/__init__.py` — the
        subpackage docstring (the [`docs/TREE.md`][tree] render fails on a
        missing module docstring) and the eager `DjangoDebugExtension`
        re-export in `__all__`, beside the root-exported policy extensions
        ([Decision 5](#decision-5--symbol-and-home-djangodebugextension-in-extensionsdebugpy-exported-from-the-extensions-subpackage--never-the-package-root)).
  - [ ] `django_strawberry_framework/extensions/debug.py` —
        `DjangoDebugExtension`, an `_OperationBoundExtension` (a
        `SchemaExtension` whose per-operation state is bound, not stored on the
        instance): the sync `on_operation` generator (pre-yield: the
        fail-closed gate, then acquire the module-private reference-counted
        debug-cursor bracket + snapshot per alias in `connections.all()`
        through `contextlib.ExitStack`, so partial setup unwinds; post-yield,
        inside `finally`: rebuild the payload and release every bracket token
        so the final overlapping operation restores the original
        `force_debug_cursor` value), the `on_execute` stash for the streaming
        seam, and the idempotent `get_results()` returning `{"debug": <stash>}`
        when the stash exists and `{}` otherwise
        ([Decision 7](#decision-7--hook-shape-one-sync-on_operation-generator-assembly-at-teardown-get_results-returns-the-stash)).
        The payload serializes the SQL rows
        ([Decision 8](#decision-8--the-sql-row-shape-graphenes-wire-names-narrowed-to-what-djangos-log-supports))
        and the terminal exceptions from each result error's nested
        `original_error` chain, cycle-safe and `None`-guarded for the
        pre-execution teardown paths
        ([Decision 9](#decision-9--exception-capture-the-results-original_error-chain-serialized-like-graphenes-wrap_exception--no-resolver-wrapping)).
        Module shape per [DRY D4–D6](#helper-reuse-obligations-dry).
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
  - [ ] `examples/fakeshop/test_query/test_debug_extension_api.py` —
        request-visible scenarios from the [Test plan](#test-plan), posting
        real HTTP through a probe URLconf mounting a debug-enabled
        `DjangoSchema` over the fakeshop apps (the
        [`test_multi_db.py`][test-multi-db] holder precedent), under the shared
        schema-reload + `seed_data` disciplines and through
        [`TestClient`][glossary-testclient].
  - [ ] `tests/extensions/test_debug.py` — request-impossible mechanics
        only: serializers and nested error-chain handling, saved-value restore
        and bounded-log behavior, no-stash/idempotent results, masking order,
        merge precedence, async overlap, concurrent sync isolation, the
        streaming seam, and the diagnostic degrade paths
        ([Decision 11](#decision-11--test-strategy-split-live-http-behavior-from-package-tier-mechanics)).
  - [ ] `tests/extensions/__init__.py` — the test-package marker whose
        docstring maps where each kind of debug test lives; it exports no test
        helpers.
  - [ ] Every symbol carries its docstring; `uv run ruff format .` /
        `ruff check --fix .` after the edit, no pytest run unless the
        maintainer asks.
- [ ] **Slice 2 — implemented-contract docs**
  - [ ] [`docs/GLOSSARY.md`][glossary] — the
        [Response-extensions debug middleware][glossary-response-extensions-debug-middleware]
        entry and its focused companion entries carry the implemented contract
        (import path, the class-form opt-in, the `debug` key, the six SQL
        fields and the named omissions, the exception triple, the debug-cursor
        mechanism, the dev-only caveat, the async SQL caveat, and the real
        cookbook migration), via the glossary app's **database** + a
        [`scripts/build_glossary_md.py`][build-glossary-md] re-render, never
        a hand-edit of the generated file.
  - [ ] [`docs/TREE.md`][tree] rendered via
        [`scripts/build_tree_md.py`][build-tree-md] (never hand-edited), with
        the docstring-derived `extensions/` and `tests/extensions/` rows.
  - [ ] [`config/schema.py`][config-schema] — the module docstring names the
        response-side `DjangoDebugExtension` as opt-in and deliberately
        omitted from the aggregate schema, with live coverage through a probe
        URLconf
        ([Decision 2](#decision-2--card-scope-boundary-the-extension-ships-alone--no-django-middleware-no-schema-field-no-fakeshop-always-on-wiring)).
  - [ ] [`GOAL.md`][goal] — success criterion 7's scope: the import-only
        promise covers `Meta`-driven domain declarations; project-level engine
        configuration (a schema's `extensions=` list, the `GRAPHENE`
        settings block) migrates by documented recipe
        ([Goal and cookbook cross-reference](#goal-and-cookbook-cross-reference)).
- [ ] **Slice 3 — the joint `0.0.14` cut + final card wrap**
        ([Decision 12](#decision-12--this-card-completes-the-joint-0014-cut-and-owns-the-version-bump)),
        with the card wrap in **DB-mutations-first, renders-last** order: card,
        `SpecDoc`, `TrackedPath`, and glossary-status DB updates; the Done flip
        with the `SpecDoc` pointing at this spec; `manage.py import_spec_terms`
        for the companion terms CSV; then the [`docs/GLOSSARY.md`][glossary],
        [`docs/TREE.md`][tree], [`KANBAN.md`][kanban] / `KANBAN.html` renders
        ([`scripts/build_kanban_md.py`][build-kanban-md] /
        `build_kanban_html.py`) and every importer/builder `--check` mode.

## Problem statement

When a GraphQL request misbehaves — too many queries, a slow query, or an
execution exception — the developer's first question is "what did
this operation actually execute?". The [Debug-toolbar
middleware][glossary-debug-toolbar-middleware] answers it **server-side**: a
browser panel over `/graphql/` traffic, gated on `DEBUG` / `INTERNAL_IPS`,
invisible to the JavaScript client that issued the request. `graphene-django`
ships the complementary mechanism this card ports: its
[`DjangoDebugMiddleware`][upstream-debug-middleware] accumulates SQL recorded
by its own instrumentation and raised resolver exceptions into a
[`DjangoDebug`][upstream-debug-types] object **inside the GraphQL response
itself**, so frontend clients and Apollo DevTools read the diagnosis from the
payload they already have. Without an equivalent, a `graphene-django` migrant
loses that surface at the door — against [`GOAL.md`][goal] success criterion 7
(migrate "without bringing the source package along") — and
`strawberry-graphql-django` offers nothing to borrow back, so the package
supplies its own Strawberry-native equivalent.

The Strawberry-native shape is small: a `SchemaExtension` that captures SQL and
exceptions for the in-flight operation and attaches them to the response's
`extensions` map under the `debug` key. The design weight is in two choices —
the **exposure mechanism** (response-extensions map vs. graphene's schema-level
`_debug` field) and the **fidelity mechanism** (port graphene's thread-local
cursor wrap vs. read `connection.queries`) — plus the lifecycle questions a
response-extensions surface inherits from the engine: where the payload is
assembled relative to Strawberry's `get_results` call ordering, how
instrumentation brackets Django's thread-local connections without depending
on `settings.DEBUG`, and how the opt-in composes with the package's documented
optimizer-singleton pattern without inheriting its shared-instance hazards.

## Current state

The engine and Django facts the decisions build on:

- **The package's `SchemaExtension`s share one per-operation state base.**
  [`DjangoOptimizerExtension`][glossary-djangooptimizerextension]
  ([`optimizer/extension.py`][optimizer-extension]), the two policy extensions
  `DjangoSchema` installs, and `DjangoDebugExtension` all derive from
  `django_strawberry_framework/extensions/operation_state.py::_OperationBoundExtension`:
  `execution_context` and each extension's per-operation scratch are read
  from the state the package runner
  (`django_strawberry_framework/extensions/operation_state.py::DjangoExtensionsRunner`)
  binds for the operation being answered. On a plain `strawberry.Schema`
  there is no package runner, so the state is the fresh instance's own.
- **The engine seams are present, at a hard dependency.**
  [`strawberry/extensions/base_extension.py`][venv-base-extension] defines
  `SchemaExtension` with the `on_operation` / `on_execute` lifecycle generator
  hooks and the `get_results()` seam;
  [`strawberry/extensions/runner.py`][venv-runner] merges every extension's
  `get_results()` dict into one map; and
  [`strawberry/schema/schema.py`][venv-schema] assigns that completed map as
  the `ExecutionResult.extensions` the HTTP layer serializes into the
  response JSON, replacing rather than merging any pre-existing result map.
  Among extension outputs, later entries win same-key collisions; on async
  execution only, `ExecutionContext.extensions_results` is then overlaid and
  has final precedence. **Call-ordering fact this spec builds on** (both
  colors): on the happy path of `execute` / `execute_sync` the final
  `get_extensions_results_sync()` / `await get_extensions_results(...)` runs
  **after** the `operation()` context exits — i.e. after `on_operation`'s
  post-yield teardown — while on the early parse-error and validation-error
  returns it runs **inside** the operation context (the `return` expression
  evaluates before the `with` unwinds), i.e. **before** teardown. The
  streaming path (`Schema.stream`, which the package's `graphql-transport-ws`
  consumer calls for every operation type) reads the results inside the
  still-open operation context on the happy path too, after `on_execute`'s
  teardown
  ([Decision 7](#decision-7--hook-shape-one-sync-on_operation-generator-assembly-at-teardown-get_results-returns-the-stash)).
  Extension classes and factories passed in `extensions=` are invoked **per
  operation** (`strawberry/schema/schema.py::Schema.get_extensions`) with no
  execution-context argument; Strawberry then assigns
  `extension.execution_context` before runner construction
  ([Decision 6](#decision-6--opt-in-shape-pass-the-class--one-fresh-instance-per-operation-requires-strawberry-03160)).
- **Django's own debug cursor is the fidelity source, and it is not
  `DEBUG`-bound.** [`django/db/backends/base/base.py`][venv-django-base]
  enables query logging (`queries_logged`) when `force_debug_cursor` is set
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
- **The upstream source is the borrowing ground truth.** The seven graphene
  files ([`debug/__init__.py`][upstream-debug-init],
  [`middleware.py`][upstream-debug-middleware],
  [`types.py`][upstream-debug-types], [`sql/types.py`][upstream-sql-types],
  [`sql/tracking.py`][upstream-sql-tracking],
  [`exception/types.py`][upstream-exception-types],
  [`exception/formating.py`][upstream-exception-formating]); the
  [Borrowing posture](#borrowing-posture) section names what each contributes
  and what is deliberately not carried.
- **HTTP test ergonomics exist.** [`TestClient`][glossary-testclient] is what
  the request-driving tests post through, and the probe-URLconf plumbing they
  need — a per-test schema over freshly-reloaded fakeshop types behind a
  module-level `urlpatterns` — follows the holder in
  [`test_multi_db.py`][test-multi-db].

## Goals

1. **The response carries its own diagnosis.** With the extension enabled and
   admitted by the gate, a consumer (or Apollo DevTools) reads
   `extensions.debug.sql` — one row per new `queries_log` entry produced by
   Django's instrumented `execute()` / `executemany()`, plus transaction
   boundaries whose logging completes while the debug hook is active (an
   enclosing `ATOMIC_REQUESTS` / middleware transaction brackets the view
   outside the hook and is excluded, [Edge cases](#edge-cases-and-constraints)),
   with vendor / alias / logged SQL / duration; `CursorDebugWrapper` does not
   instrument `callproc()`, so stored-procedure calls are outside this
   contract — and `extensions.debug.exceptions` — one row per execution
   exception represented by graphql-core's `original_error` chain, with type /
   message / stack — from the same JSON payload that carried `data`
   ([Decision 3](#decision-3--exposure-the-response-extensions-map-under-the-debug-key-not-a-schema-level-_debug-field),
   [Decision 8](#decision-8--the-sql-row-shape-graphenes-wire-names-narrowed-to-what-djangos-log-supports),
   [Decision 9](#decision-9--exception-capture-the-results-original_error-chain-serialized-like-graphenes-wrap_exception--no-resolver-wrapping)).
2. **Ordinary non-overlapping sync capture is deterministic and its mechanism
   is not `DEBUG`-dependent.** The `force_debug_cursor` bracket makes the same
   ordinary sync operation produce the same capture under `DEBUG=True` dev
   servers and under an acknowledged `DEBUG=False` deployment; whether the
   payload is published at all is the fail-closed gate's decision (spec-048
   Decision 5). Nested same-thread operations share one log and therefore
   cross-attribute rows
   ([Decision 4](#decision-4--fidelity-djangos-own-debug-cursor-via-a-force_debug_cursor-bracket-not-a-cursor-wrap-port)).
3. **Off by default, one-line opt-in, zero new dependencies.** Absent from
   the `extensions=` list, **no debug instrumentation runs and no `debug`
   response key is added**; present and admitted, every executed operation on
   that schema carries the payload, while parse and validation failures
   follow the documented no-key rule. No package is added and no settings key
   exists; per-request isolation rests on the existing Strawberry floor
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
   surface: the captured row list *shows* the optimizer's planned
   **visibility-safe two-query shape** — exactly one `products_item` slice
   plus one `products_category` prefetch, no per-item category queries —
   where a naive resolver chain would show N+1. Not a joined single query:
   `CategoryType` defines a custom `get_queryset` visibility hook, so the
   optimizer deliberately downgrades the forward FK to a `Prefetch` rather
   than `select_related` (the shipped rule the live proof
   `test_products_api.py::test_products_optimizer_merges_duplicate_root_field_nodes_over_http`
   also pins) ([Test plan](#test-plan) scenario 2).

## Non-goals

- **A Django (or Graphene) middleware.** The feature name's word "middleware"
  is graphene's name for its resolver-wrapping callable; the shipped shape is
  a Strawberry `SchemaExtension` under `extensions/`, and nothing here touches
  `MIDDLEWARE`, request/response objects, or the [Debug-toolbar
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
  the off-by-default posture. A future opt-in (the fakeshop activation card
  is the natural host) can replace the probe URLconf with the shipped URLconf
  while the request tests remain in the live tier
  ([Decision 11](#decision-11--test-strategy-split-live-http-behavior-from-package-tier-mechanics)).
- **Further production knobs.** The one constructor argument is spec-048's
  keyword-only `allow_unsafe_production` acknowledgement; there is no
  `is_slow` threshold argument, no redaction hook, no per-request enable
  predicate, and no settings key. The absent settings key is a decision, not a
  gap: `conf.py` keys exist only where a knob must vary per deployment without
  code changes (for example `NESTED_CONNECTION_STRATEGY`, `TESTING_ENDPOINT`); a debug tool
  configured at schema construction adds no such case. Knobs are follow-on
  material once a real consumer asks ([Risks](#risks-and-open-questions)).
- **Subscriptions.** The extension's contract is pinned for query / mutation
  operations, over `execute` / `execute_sync` and over the streaming seam.
  What a subscription's per-event results carry is untested and undocumented
  here.
- **Experimental incremental execution (`@defer` / `@stream`).** With
  Strawberry's `enable_experimental_incremental_execution` config,
  `Schema._handle_execution_result` returns incremental result objects
  before the ordinary extension-result assignment — the two-list,
  one-final-map contract does not define which of the initial and
  subsequent payloads would carry debug data. The contract covers
  **non-incremental query/mutation `ExecutionResult`s only**.
- **Async SQL-capture fidelity.** Exception capture is
  execution-color-agnostic; SQL capture is guaranteed on the ordinary
  non-reentrant sync execution path and documented as **typically empty**
  under async execution, where Django's per-thread connections mean the
  `sync_to_async` executor threads' queries escape a bracket set from the
  event-loop thread — the same thread-local constraint graphene's own wrap
  carries. The async-instrumentation follow-on is named in
  [Risks](#risks-and-open-questions).

## Borrowing posture

Per the [`START.md`][start] "do both libraries provide it?" test this card is
**single-upstream, Required**: ⚛️ `graphene-django` ships the subsystem; 🍓
`strawberry-graphql-django` does not, so the package claims parity with the
single upstream and records the absence plainly — the [Single-upstream
parity][glossary-single-upstream-parity] posture. Every borrow below cites the
upstream source directly.

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
  of a bare "`connection.queries`" read: the bare property is empty under
  `DEBUG=False`, the bracket is not.

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
  contexts; the extension's per-operation state IS the accumulator, so the
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
schema-setup pieces — shown so the example is a complete consumer recipe.) The
same entry works in a `DjangoSchema(...)` `extensions=` list. Under
`settings.DEBUG = False` the bare class entry withholds the payload and logs
one warning; a deliberate non-debug deployment spells the factory
`lambda: DjangoDebugExtension(allow_unsafe_production=True)` instead (spec-048
Decision 5).

Every executed operation through an admitted schema then carries the payload:

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

- **The payload appears for every executed operation** on an admitted schema
  — queries and mutations, with data or with errors, including
  introspection (whose `sql` list is simply empty), over `execute`,
  `execute_sync`, and the streaming seam. It does **not** appear for parse or
  validation failures (a syntax error, an unknown-field validation error):
  nothing executed, so there is nothing to report
  ([Error shapes](#error-shapes) records the engine's coerced-exception
  recovery path)
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
  broader than graphene's resolver-only middleware and is the cost of
  using Strawberry's operation result instead of wrapping every field.
- **The two keys are always both present** when the payload appears —
  `{"sql": [], "exceptions": []}` for a no-op operation — so client code
  indexes without existence checks. The payload caps never remove a key
  (spec-048 Decision 6).
- **Combining with a masking extension is order-sensitive.** Hook
  teardowns unwind LIFO, and Strawberry's `MaskErrors` rewrites
  `result.errors` with `original_error=None` in *its* teardown — so the
  unmasked `exceptions` rows appear only when `DjangoDebugExtension` is
  listed **after** the masking extension (torn down first, reading the
  originals). Listed before it, the debug teardown sees only stripped
  errors and reports `exceptions: []`
  ([Decision 9](#decision-9--exception-capture-the-results-original_error-chain-serialized-like-graphenes-wrap_exception--no-resolver-wrapping),
  [Edge cases](#edge-cases-and-constraints)); the docstring states the
  required ordering. The error policy `DjangoSchema` installs is prepended
  and masks a copy, so it never hides originals from the debug extension
  (spec-048 Decisions 10 and 11).
- **Nothing else about the response changes.** The extension never mutates
  the queryset, the context, or the result's `data` / `errors`; it is a
  read-only window, and its diagnostic collection is forbidden from
  replacing an already-produced result even when serialization fails
  ([Error shapes](#error-shapes)). With the extension absent, no debug
  instrumentation runs and no `debug` key is added.

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
  response with **no** `debug` key. Two facts hold it: the engine calls
  `get_results` before the hook's teardown on those paths, and the stash is
  written only when `execution_context.result` is a graphql-core
  `ExecutionResult` — sync early returns leave `result` as `None`, and the
  async path assigns a Strawberry `PreExecutionError`, neither of which is
  one.
- **A coerced non-GraphQL exception** — the engine's generic recovery
  handlers (both colors) sit *outside* the operation context: an exception
  escaping the hooks or the executor is coerced to a GraphQL error **after**
  teardown ran, so that error response carries the `debug` key **only when
  execution assigned a graphql-core `ExecutionResult` and a debug teardown
  stashed the payload** before the abort. A non-`GraphQLError` parse crash
  (the sync parse handler catches only `GraphQLError`) never assigned one, so
  it carries no key; an earlier sibling hook's setup failure can abort before
  the debug hook ever enters, in which case no stash exists either. Generic
  recovery alone does not imply two `get_results()` calls.
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
  - **Teardown (post-execution) never replaces the result**: the two
    collection phases each catch `Exception` (never `BaseException`), log
    server-side, and degrade independently. SQL degrades **per row**
    (`_serialized_sql_row_or_dropped`): a row that cannot be serialized —
    including the non-finite duration the serializer refuses because it is
    not JSON-encodable — is dropped and every other row keeps its log order;
    a failure draining a connection's query log degrades to the rows
    serialized so far. Exception collection degrades to an empty list. The
    wire contract is unchanged (a completed payload still owns both `sql` and
    `exceptions` lists; no third error shape), and the original `data` /
    `errors` survive (Test plan scenarios 17 and 23).
  The known pre-execution corner remains designed-in: on the sync
  parse/validation paths teardown runs during the early return's unwind
  with `execution_context.result` still unset, so the exception collector
  is `None`-guarded by contract
  ([Decision 9](#decision-9--exception-capture-the-results-original_error-chain-serialized-like-graphenes-wrap_exception--no-resolver-wrapping));
  an unguarded read would raise out of the `with`-unwind and the engine
  would coerce *that* into the response, discarding the real parse error.
  Independently, the restore of every connection's `force_debug_cursor`
  rides a `finally` so no failure mode — an abandoned hook generator
  included — can leave a connection permanently instrumented; flag
  restoration and result preservation are separately protected.
- **A consumer extension also publishing a `debug` extensions key** — among
  extension outputs, the runner merges `get_results()` dicts in
  extensions-list order ([`runner.py`][venv-runner]), so the later-listed
  extension wins. On async execution, `ExecutionContext.extensions_results`
  is overlaid afterward and has final precedence; the sync runner has no
  equivalent overlay. Schema result handling assigns the completed map rather
  than merging a pre-existing `ExecutionResult.extensions` map. Documented,
  not guarded: the key is the pinned contract and namespacing it away from a
  hypothetical collision would break the graphene-shaped expectation.

## Architectural decisions

### Decision 1 — Spec filename and canonical naming

This spec lives at `docs/SPECS/spec-044-debug_extension-0_0_14.md`: card NNN `044`,
topic slug `debug_extension` (the card's subject as shipped — a debug
`SchemaExtension`), version segment `0_0_14` from the card's trailing
`-0.0.14`. Follows the [`docs/SPECS/NEXT.md`][next] convention.

*Rejected alternatives: [rationale companion, Decision 1][rationale-d1].*

### Decision 2 — Card-scope boundary: the extension ships alone — no Django middleware, no schema field, no fakeshop always-on wiring

This card ships exactly one consumer-facing unit: `DjangoDebugExtension` and
its subpackage home, plus tests and docs. Three adjacent-looking pieces stay
out:

- **No Django middleware and no toolbar coupling.** The
  [Debug-toolbar middleware][glossary-debug-toolbar-middleware] is a
  different mechanism over a different seam (the HTTP response); this card
  adds no `MIDDLEWARE` entry, imports nothing from `middleware/`, and shares
  no code with it. The two are documented as complements.
- **No schema surface.** No GraphQL type, no Query field, no `Meta` key, no
  finalizer participation — the extension is invisible to introspection
  ([Decision 3](#decision-3--exposure-the-response-extensions-map-under-the-debug-key-not-a-schema-level-_debug-field)).
- **No fakeshop always-on wiring.** The shipped
  [`config/schema.py`][config-schema] does not add the extension: it would
  change every acceptance response's body and pay capture cost on every
  live test, and it would misrepresent the off-by-default posture in the
  package's own showcase. Its docstring says so, and a live test pins that the
  project's real `/graphql/` publishes no `debug` key
  ([Decision 11](#decision-11--test-strategy-split-live-http-behavior-from-package-tier-mechanics),
  [Out of scope](#out-of-scope-explicitly-tracked-elsewhere)).

*Scope justification and the rejected bundled-demo alternative: [rationale companion, Decision 2][rationale-d2].*

### Decision 3 — Exposure: the response-`extensions` map under the `debug` key, not a schema-level `_debug` field

The payload rides `ExecutionResult.extensions["debug"]` via the engine's
`get_results()` seam. graphene's alternative exposure is a schema-level field
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
   both to the simpler choice" instruction both name the extensions map.
5. **It preserves the real cookbook's ownership boundary.**
   [`recipes/schema.py`][upstream-cookbook-recipes-schema] contains no debug
   field or middleware coupling. Debug is added only by the project aggregate
   [`cookbook/schema.py`][upstream-cookbook-schema], with middleware installed
   separately in [`cookbook/settings.py`][upstream-cookbook-settings]. The
   Strawberry aggregate schema's `extensions=` list replaces both project
   integration points without changing any recipe-app domain type or `Meta`
   surface, matching [`GOAL.md`][goal]'s working-reference posture.

*Rejected exposures (graphene's `_debug` field; both at once): [rationale companion, Decision 3][rationale-d3].*

### Decision 4 — Fidelity: Django's own debug cursor via a `force_debug_cursor` bracket, not a cursor-wrap port

The SQL source is Django's per-connection `queries_log`, enabled for the
operation's duration by the [`CaptureQueriesContext`][venv-django-test-utils]
mechanism: for each configured connection, save `force_debug_cursor`, set it
`True`, and record `len(connection.queries_log)`. This extension performs the
same transition through the reference-counted coordinator
(`django_strawberry_framework/extensions/debug.py::_CursorCaptureCoordinator`,
pinned in
[Decision 7](#decision-7--hook-shape-one-sync-on_operation-generator-assembly-at-teardown-get_results-returns-the-stash)):
the first active bracket saves and enables the flag, overlapping brackets
increase its depth, and the final release restores the saved value. Each
operation's state owns its own log-length snapshots; at teardown the payload
builder materializes and slices each log from its index. The extension
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
scenario 18 and named in the module docstring, [Edge
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
   Postgres-transaction fields — is documented explicitly
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
- **Wrap with `CaptureQueriesContext` instances directly.** Rejected on
  three grounds: (a) `CaptureQueriesContext.__enter__` calls
  `connection.ensure_connection()` eagerly, which would open a database
  connection on every alias for every operation — including aliases the
  operation never touches (fakeshop's sharded mode has two); (b) `__enter__`
  also disconnects the process-global `request_started → reset_queries`
  signal and `__exit__` reconnects it
  ([`django/test/utils.py`][venv-django-test-utils]
  `::CaptureQueriesContext`) — per-operation toggling of global signal
  state, with overlapping operations racing the reconnect; (c) its
  save/restore is a single-context shape with no overlap reference counting,
  so two overlapping operation contexts on one connection would restore out
  of order — the exact failure the coordinator exists to prevent. The
  extension reuses the class's *semantic contract* — save the flag, enable
  logging, snapshot the log length, restore the saved value — without its
  test-oriented connection and signal side effects; an untouched alias
  contributes zero rows and zero connections.

*The rejected bare-`connection.queries` read: [rationale companion, Decision 4][rationale-d4].*

### Decision 5 — Symbol and home: `DjangoDebugExtension` in `extensions/debug.py`, exported from the `extensions` subpackage — never the package root

The class is `DjangoDebugExtension`, defined in
`django_strawberry_framework/extensions/debug.py`, re-exported from
`django_strawberry_framework.extensions`. The subpackage `__init__.py` carries
a docstring and `__all__ = ["DjangoDebugExtension",
"DjangoErrorPolicyExtension", "DjangoResourcePolicyExtension"]`; the two
policy extensions are also root-exported because `DjangoSchema` installs them
on every schema, while `DjangoDebugExtension` is added to neither the package
root's `__all__` nor its `__getattr__`.

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
   (`testing/`, `auth/`, `middleware/`, `routers`). The optimizer and the
   policy extensions are root because they are part of the default recipe; a
   debug diagnostic is not. The import line
   `from django_strawberry_framework.extensions import DjangoDebugExtension`
   also mirrors the graphene migrant's muscle memory
   (`from graphene_django.debug import DjangoDebugMiddleware` — subpackage
   there too).
3. **Eager re-export, no lazy machinery.** `extensions/__init__.py` imports
   `debug.py` directly: every import behind it is a hard dependency, so there
   is no [soft-dependency][glossary-soft-dependency] boundary to defend and a
   [PEP 562 lazy export][glossary-pep-562-lazy-export] would be ceremony
   without a payer. The file mirrors the package's eager-subpackage export
   shape — docstring + explicit re-export + `__all__`, as
   `utils/__init__.py` and `testing/__init__.py` do; no wildcard, no
   `__getattr__`. (`middleware/__init__.py`'s deliberate *no*-re-export
   marker is the soft-dependency contrast, not the precedent here — its
   emptiness exists to keep an optional import boundary this subpackage
   does not have.)

*Rejected homes (package root, `optimizer/debug.py`, `extensions/debug_extension.py`): [rationale companion, Decision 5][rationale-d5].*

### Decision 6 — Opt-in shape: pass the class — one fresh instance per operation requires Strawberry 0.316.0

The documented opt-in is `extensions=[DjangoDebugExtension]` (the class
object; a factory that builds a fresh instance is equivalently correct, and is
how the spec-048 acknowledgement is spelled). From Strawberry `0.316.0`,
non-instance entries are invoked per operation
([`schema.py`][venv-schema] `::Schema.get_extensions`), so each operation gets
a fresh instance; the package's `strawberry-graphql>=0.322.2` floor includes
that release.

Grounds:

1. **Per-operation state demands per-operation isolation.** The engine
   assigns `extension.execution_context` per request and the hook keeps
   capture state between pre-yield and teardown; on a shared instance two
   concurrent operations would interleave those writes. The extension keeps
   that state — the snapshots and the assembled payload — on
   `django_strawberry_framework/extensions/debug.py::_DebugOperationState`,
   bound through `_OperationBoundExtension`, never on the instance. Under a
   `DjangoSchema` the package runner binds one state per operation, so even an
   entry that resolves to one shared object answers each operation with its
   own payload; on a plain `strawberry.Schema` the state is the fresh
   instance's own, so a class entry or a fresh factory is operation-local
   there and a shared instance is outside the guarantee.
2. **Releases before `0.316.0` are unsafe for this design.** They cache
   class-created sync extensions on `Schema._sync_extensions`. Concurrent
   requests then overwrite the same instance's engine-owned
   `execution_context`, so a response can expose a sibling request's
   exception payload. `0.316.0` removes that cache and constructs
   classes/factories per request. This is the upstream race reported and
   fixed in [Strawberry issue #4369][upstream-strawberry-extension-isolation];
   the dependency floor, not package code, excludes it.
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

**Engine lifecycle notes — the floor applies to every consumer schema.**
Per-operation construction changes engine behavior for every schema, including
schemas that never import `DjangoDebugExtension`:

- releases before `0.316` **cached** sync extension instances; from `0.316`
  class/factory entries are constructed **per operation**, rebuilding the
  middleware manager each time;
- classes and factories are invoked with **zero arguments** and
  `extension.execution_context` is assigned afterward — a consumer factory
  that relied on an `execution_context=` call shape fails;
- direct **instance** entries draw a `DeprecationWarning`.

The lower bound **excludes the known cached-sync lifecycle**; it does not
"pin" future semantics. What pins the resolved behavior is `uv.lock` plus the
regression tests (Test plan scenario 13 at the exact floor).
`optimizer/extension.py`'s `__init__` keeps its `execution_context`
parameter for direct-construction compatibility only, and its comment says
Strawberry itself never passes that keyword.

*Rejected opt-in shapes (the optimizer's singleton, a lower floor, a runtime tripwire): [rationale companion, Decision 6][rationale-d6].*

### Decision 7 — Hook shape: one sync `on_operation` generator, assembly at teardown, `get_results` returns the stash

`DjangoDebugExtension` implements three engine seams. Its one `__init__`
takes only spec-048's keyword-only `allow_unsafe_production` (default `False`,
so Strawberry's zero-argument construction of a class entry is the fail-closed
instance) and settles it into the module-private `_ACKNOWLEDGEMENT` authority;
`execution_context` stays engine-assigned and is read through
`_OperationBoundExtension` ([DRY D6](#helper-reuse-obligations-dry)):

- **`on_operation`** — a **sync** generator. Pre-yield it reads the
  fail-closed gate first (an inert operation acquires nothing, snapshots
  nothing, and builds nothing), then uses `contextlib.ExitStack` to acquire a
  reference-counted bracket token and a query-log snapshot for every
  alias ([Decision 4](#decision-4--fidelity-djangos-own-debug-cursor-via-a-force_debug_cursor-bracket-not-a-cursor-wrap-port),
  [Decision 10](#decision-10--multi-database-capture-every-alias-in-connectionsall-one-bracket-each))
  and records the snapshots on the operation state. Post-yield — inside a
  `try` / `finally` so restore always runs — it **rebuilds** the payload from
  the completed logs and the result, stashes it on the operation state, and
  the stack releases every token. The last overlapping token for a
  connection restores its saved `force_debug_cursor`.
- **`on_execute`** — a sync generator whose teardown stashes the payload the
  moment graphql-core returned. It contributes nothing for an operation that
  never bracketed (the inert path, or no operation state).
- **`get_results`** — returns `{"debug": <stash>}` when the operation's
  state holds a payload and `{}` otherwise — **idempotent** (a pure read:
  never a mutate-or-pop, never a write to `execution_context` or to an
  existing `ExecutionResult.extensions`): the early-result plus
  teardown-failure recovery path can invoke it twice for one operation
  ([Error shapes](#error-shapes)). The absent sentinel is `None` on
  `_DebugOperationState.payload` — unambiguous because a completed payload is
  always a dict, even when both lists are empty — so no eager empty dict ever
  falsely publishes `debug` before execution.

Both teardowns call the one stash writer
(`django_strawberry_framework/extensions/debug.py::DjangoDebugExtension._stash_payload_if_executed`),
which builds the payload **only when** `execution_context.result` is a
graphql-core `ExecutionResult`; every other shape (`None` on the sync early
returns, a Strawberry `PreExecutionError` on the async path) leaves the stash
absent.

Grounds:

1. **A sync generator serves both execution colors.** The engine wraps a
   sync generator hook in `contextlib.contextmanager` and enters it
   synchronously on the async path's `AsyncExitStack` too
   ([`extensions/context.py`][venv-extensions-context] `::__aenter__`); an
   `async def` hook would instead make sync execution fail (the sync
   `__enter__` raises `RuntimeError` for any async hook). One hook, both
   colors, no duplication.
2. **Two teardowns, because the engine reads the results at two different
   points.** On `execute` / `execute_sync` the happy path reads `get_results`
   *after* `on_operation` teardown, so the rebuild there is what those paths
   publish — including the masking-order behavior
   [Decision 9](#decision-9--exception-capture-the-results-original_error-chain-serialized-like-graphenes-wrap_exception--no-resolver-wrapping)
   pins. On the streaming path the engine reads the results *inside* the
   still-open operation context, before `on_operation` teardown, so without
   the `on_execute` stash a streaming transport could never carry
   `extensions["debug"]`; that seam publishes the payload the executing hook
   saw (the transport masks each frame's `errors` itself). On pre-execution
   error paths the results are read before any teardown and no stash exists
   (→ `{}` → no `debug` key). Assembling in `get_results` instead would
   sometimes observe a half-open bracket.
3. **`ExitStack`-owned, overlap-safe restore is the non-negotiable part.**
   Whatever the operation did — including raising through the engine or
   abandoning the hook generator — connections must come back to their prior
   instrumentation state, or one enabled operation would leave
   `force_debug_cursor` stuck `True` process-wide (and, in a test run,
   silently corrupt every later `assertNumQueries`-style snapshot).
   `ExitStack` also unwinds aliases already acquired if a later alias fails
   during setup, before the hook reaches `yield`. The saved-value restore (not
   `False`) also keeps the bracket nestable inside a consumer's own
   `CaptureQueriesContext`; reference counting prevents overlapping async
   operation contexts from restoring the same loop-thread connection out of
   order. The coordinator behind the tokens is module-private with exactly two
   seams (`acquire` / `release` — [DRY D5](#helper-reuse-obligations-dry)),
   and `ExitStack.callback(...)` wires each release declaratively.

*Rejected hook shapes (assemble in `get_results`, a `resolve` hook, an async twin): [rationale companion, Decision 7][rationale-d7].*

### Decision 8 — The SQL row shape: graphene's wire names, narrowed to what Django's log supports

Each captured `queries_log` entry serializes to a plain dict with exactly six
keys, in graphene's wire casing:

| Key | Value | graphene source |
| --- | --- | --- |
| `vendor` | `connection.vendor` (`"sqlite"`, `"postgresql"`, ...) | `DjangoDebugSQL.vendor` |
| `alias` | the connection's Django alias (`"default"`, `"shard_b"`, ...) | `DjangoDebugSQL.alias` |
| `sql` | the logged statement — interpolated via `ops.last_executed_query` for `execute()`; `"<N> times: <sql>"` raw form for `executemany()` (Django's own log format, verbatim) | `DjangoDebugSQL.sql` |
| `duration` | `float(entry["time"])` — seconds at Django's 3-decimal log precision; a non-finite value is refused (not JSON-encodable) and that row alone is dropped | `DjangoDebugSQL.duration` |
| `isSlow` | `duration > 10` — graphene's constant, kept verbatim | `DjangoDebugSQL.is_slow` |
| `isSelect` | `sql.lower().strip().startswith("select")` — graphene's sniff, kept verbatim | `DjangoDebugSQL.is_select` |

Explicitly omitted, each because the chosen fidelity source
([Decision 4](#decision-4--fidelity-djangos-own-debug-cursor-via-a-force_debug_cursor-bracket-not-a-cursor-wrap-port))
does not carry it — the narrowing is documented here and mirrored in the
GLOSSARY entry body:

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

The `sql`, `message`, and `stack` strings are then subject to spec-048
Decision 6's per-row truncation, row-count caps, and shared text budget; the
key set never changes.

Grounds: the card's DoD pins "mirrors graphene's `DjangoDebugSQL` /
`DjangoDebugException` field names where the chosen fidelity supports them".
CamelCase is the *wire* form a graphene client actually parses (graphene's
schema auto-camelCases `is_slow` → `isSlow`; since this payload never passes
through a GraphQL type, the extension emits the wire form directly).
`duration` stays float-seconds (not the log's string) so client tooling can
compare and sum without parsing.

*Rejected row shapes (snake_case keys, extension-measured timestamps, a `time` string field, a casing helper): [rationale companion, Decision 8][rationale-d8].*

### Decision 9 — Exception capture: the result's `original_error` chain, serialized like graphene's `wrap_exception` — no resolver wrapping

At teardown the payload builder reads the operation's errors from the
execution result (`result.errors` carries the operation's `GraphQLError`s —
and the read is **`None`-guarded**, because on the sync parse/validation
paths teardown runs during the early return's unwind before any result
exists, [Error shapes](#error-shapes)) and serializes
**only** those members whose `original_error` is non-`None` —
Strawberry/graphql-core's marker distinguishing an execution exception from a
pure GraphQL validation error. Starting from that first original, a private
helper (`django_strawberry_framework/extensions/debug.py::_terminal_original_error`)
walks nested `GraphQLError.original_error` links to the terminal exception.
The walk is **doubly bounded**: an identity set terminates malformed cycles,
and a local maximum-hop constant (`_MAX_ORIGINAL_ERROR_HOPS = 64` —
`utils/typing.py`'s `MAX_TYPE_WRAPPER_DEPTH` ceiling, re-spelled locally)
bounds a long acyclic chain, which an identity set alone cannot. The stop
behavior is deterministic: return the **last unique candidate seen** before
a repeated identity or the hop ceiling. The bound covers only the
`original_error` traversal; string sizes are bounded afterward by spec-048
Decision 6's caps. The walk follows the bounded-walk posture `utils/typing.py`
pins for attribute-chain peels (never a bare unbounded `while` loop) with a
deliberately different failure policy — stop and keep the best-effort
terminal, so a malformed consumer exception chain degrades to best-effort
capture instead of failing the response — the policy difference that keeps
it a local helper rather than a shared extraction
([DRY D6](#helper-reuse-obligations-dry)); Test plan scenario 21 pins a
self-cycle, a multi-node cycle, and a long acyclic chain. A terminal
`GraphQLError` is retained: graphql-core uses that exact two-link shape when
a resolver explicitly raises `GraphQLError`, and graphene's resolver
middleware records it. Each match serializes via the
`wrap_exception`-shaped triple
([Decision 8](#decision-8--the-sql-row-shape-graphenes-wire-names-narrowed-to-what-djangos-log-supports)),
using the original exception's own `__traceback__` for `stack`. Result-error
order is preserved and distinct outer errors are never speculatively
deduplicated.

Grounds:

1. **The engine already accumulates what graphene's middleware wraps every
   resolver to collect.** graphql-core attaches the raised exception to the
   located `GraphQLError`; wrapping resolvers to catch it first would be
   re-implementation with a hot-path cost
   ([Decision 7](#decision-7--hook-shape-one-sync-on_operation-generator-assembly-at-teardown-get_results-returns-the-stash)'s
   rejected `resolve` hook: [rationale companion][rationale-d7]).
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

*Rejected capture shapes (a per-field `resolve` hook, ungated result errors, swallowed exceptions): [rationale companion, Decision 9][rationale-d9].*

### Decision 10 — Multi-database capture: every alias in `connections.all()`, one bracket each

The pre-yield bracket loops `django.db.connections.all()` — every configured
alias, whether or not the operation will touch it — saving and setting each
connection's flag and snapshotting each log independently; teardown slices
each retained snapshot and concatenates the rows (each already carrying its
`alias`,
[Decision 8](#decision-8--the-sql-row-shape-graphenes-wire-names-narrowed-to-what-djangos-log-supports))
in `connections.all()` order, and the stack restores per alias.

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
rejection of wrapping `CaptureQueriesContext` directly, no connection is
force-opened. The per-alias contract has a real proof: Test plan scenario 16
executes a real `shard_b` query through a debug-enabled probe schema on the
`FAKESHOP_SHARDED=1` tier and asserts the captured `alias == "shard_b"` row
plus both-alias restoration.

*Rejected bracket scopes (default alias only, `connection_created`-lazy): [rationale companion, Decision 10][rationale-d10].*

### Decision 11 — Test strategy: split live HTTP behavior from package-tier mechanics

The card predicts `tests/extensions/`, but predicted files do not override the
repository's test-placement law. The card also requires coverage "against a
fakeshop request that emits SQL", so the tests split by behavior:

- **The request-driving group** lives in
  `examples/fakeshop/test_query/test_debug_extension_api.py` and posts
  **real HTTP** to a debug-enabled `DjangoSchema` mounted on a probe URLconf
  (one module-level `pytest.mark.urls(__name__)` over Strawberry's Django
  view — the [`test_multi_db.py`][test-multi-db] holder precedent), built
  over the freshly-reloaded fakeshop apps per the
  [schema-reload discipline][glossary-schema-reload-discipline], seeded via
  [`seed_data`][glossary-seed-data], posted through
  [`TestClient`][glossary-testclient]. These are fakeshop requests emitting
  real SQL.
- **The mechanics group** lives in `tests/extensions/test_debug.py` and pins
  what a request cannot isolate: serializer and nested-chain edges, the
  restore contract, bounded-log behavior, no-stash/idempotent results,
  masking order, merge precedence, async overlap, concurrent sync isolation,
  the streaming seam (fakeshop mounts no ASGI/WS route), and the degrade
  paths.

**The [live-first mandate][glossary-live-first-coverage-mandate]
application:** `examples/fakeshop/test_query/` owns live GraphQL HTTP tests for
any app or package surface. A module-local probe URLconf does not change that
classification; it is the established way to exercise an opt-in schema shape
without enabling it in the shipped aggregate schema. Package-tier tests remain
only for mechanics that cannot be proved by a real request.

*Rejected placements (fakeshop always-on, all in `tests/extensions/`, in-process only): [rationale companion, Decision 11][rationale-d11].*

### Decision 12 — This card completes the joint `0.0.14` cut and owns the version bump

`044` was the last `0.0.14` card to land, so under the
[joint version cut][glossary-joint-version-cut] rule and the
[`docs/SPECS/NEXT.md`][next] ownership rule its Slice 3 carried the `0.0.14`
cut: the `__version__` bump (the single source; hatchling derives the packaging
version from it) with `tests/base/test_init.py::test_version`,
the GLOSSARY `shipped (0.0.14)` status flips for the
router (and its [Channels request adapter][glossary-channels-request-adapter] /
[`require_optional_module`][glossary-require-optional-module] companions), the
toolbar middleware, the test-client family, and this card's own entries, the
release-status doc moves, and the `CHANGELOG.md` `0.0.14` section under an
explicit Slice-3 grant. The bump moved only after the extension and its docs
were complete. `0.0.14` is a routine patch cut, not a milestone cut — the
alpha → beta milestone chores belong to [`TODO-ALPHA-057-0.1.0`][kanban].

*Rejected cut owners (defer to another card, bump in Slice 1): [rationale companion, Decision 12][rationale-d12].*

## Implementation plan

The file map (each row's contract is specified in the decisions cited):

| File | Holds | Slice |
| --- | --- | --- |
| `django_strawberry_framework/extensions/__init__.py` | Subpackage docstring + eager `DjangoDebugExtension` re-export in `__all__` ([Decision 5](#decision-5--symbol-and-home-djangodebugextension-in-extensionsdebugpy-exported-from-the-extensions-subpackage--never-the-package-root)) | 1 |
| `django_strawberry_framework/extensions/debug.py` | `DjangoDebugExtension`: sync `on_operation` generator (fail-closed gate, per-alias reference-counted `force_debug_cursor` bracket + snapshot pre-yield; `finally`-guarded rebuild / stash / release at teardown), the `on_execute` streaming stash, `get_results()` returning the stash under `"debug"`, SQL/exception serializers, the payload builder, and the lock-protected active-bracket coordinator ([Decisions 4](#decision-4--fidelity-djangos-own-debug-cursor-via-a-force_debug_cursor-bracket-not-a-cursor-wrap-port)–[10](#decision-10--multi-database-capture-every-alias-in-connectionsall-one-bracket-each); module shape per [DRY D4–D6](#helper-reuse-obligations-dry)) | 1 |
| `examples/fakeshop/test_query/test_debug_extension_api.py` | The [Test plan](#test-plan) request-driving scenarios: real probe-URLconf HTTP via [`TestClient`][glossary-testclient], under schema-reload + `seed_data` disciplines ([Decision 11](#decision-11--test-strategy-split-live-http-behavior-from-package-tier-mechanics)) | 1 |
| `tests/extensions/__init__.py` | Test-package marker; no shared helper exports | 1 |
| `tests/extensions/test_debug.py` | Request-impossible serializer, lifecycle, masking, merge, async-overlap, streaming, bounded-log, degrade, and concurrent-isolation mechanics ([Decision 11](#decision-11--test-strategy-split-live-http-behavior-from-package-tier-mechanics)) | 1 |
| [`test_multi_db.py`][test-multi-db] | Real sharded-tier capture proof: a `shard_b` query through a debug-enabled probe schema asserts `alias == "shard_b"` + vendor + both-alias restoration ([Decision 10](#decision-10--multi-database-capture-every-alias-in-connectionsall-one-bracket-each), Test plan scenario 16) | 1 |
| [`docs/GLOSSARY.md`][glossary] | The debug entries (glossary DB + re-render) | 2 |
| [`docs/TREE.md`][tree] | Rendered `extensions/` + `tests/extensions/` rows | 2 |
| [`config/schema.py`][config-schema] | Docstring naming the opt-in extension and fakeshop's deliberate omission | 2 |
| [`GOAL.md`][goal] | Success criterion 7's import-only scope; engine configuration migrates by documented recipe | 2 |
| [`KANBAN.md`][kanban] / `KANBAN.html` | Card wrap: DB edits + Done flip + `import_spec_terms` **first**, generated renders **last** | 3 |

## Helper-reuse obligations (DRY)

Reuse is named per item, and deliberate *non*-reuse carries its reason. The
headline: **almost nothing in `utils/` is directly callable from `debug.py`,
and that is the correct outcome, not a gap** — the utils charter is mostly the
query/write/input pipeline (visibility, inputs, windows, write decode); the
debug extension is an engine-lifecycle instrument over `django.db.connections`
and the execution result, and forcing reuse would invert DRY into coupling.
The real DRY work is (a) single-siting inside `debug.py` itself (D4–D5), (b)
conformance with the package's established idioms and its shared
per-operation state base (D6, D-N1), and (c) writing the non-reuse reasons
down (D-N2–D-N8).

- [ ] **D1** — the operation lifecycle and the response-extensions merge
  ride Strawberry's `SchemaExtension` seams (`on_operation`, `on_execute`,
  `get_results`) — never a view patch, never a transport hook
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
  Specifically: the live module's schema fixture depends on
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
  rather than duplicating the holder — and the schema-construction seam never
  sorts, normalizes, or deduplicates the `extensions=` list, because order is
  part of the contract
  ([Decision 9](#decision-9--exception-capture-the-results-original_error-chain-serialized-like-graphenes-wrap_exception--no-resolver-wrapping)).
  URLconf **activation** is likewise single-sited: one module-level
  `pytestmark = pytest.mark.urls(__name__)` covers every request-driving
  scenario — never a per-test `override_settings(ROOT_URLCONF=__name__)` /
  `clear_url_caches()` enter/exit block, and never routing setup hidden
  inside [`TestClient`][glossary-testclient].
  The [`test_multi_db.py`][test-multi-db] holder is the behavioral
  precedent but is deliberately **copied, not promoted** into a shared
  helper: that module is import-gated by `FAKESHOP_SHARDED` while this one
  is always collected, and URLconf modules must expose real module-level
  `urlpatterns` — promote a narrowly named test helper only when a third
  always-collected module needs the exact same mutable-schema URLconf.
- [ ] **D4** — the two wire serializers are **module-level functions**, not
  closures or methods: one exception serializer
  (`django_strawberry_framework/extensions/debug.py::_serialize_exception`)
  owns the triple — including the load-bearing explicit arguments
  `traceback.format_exception(type(exc), exc, exc.__traceback__)`
  ([Decision 8](#decision-8--the-sql-row-shape-graphenes-wire-names-narrowed-to-what-djangos-log-supports)) —
  and one SQL-row serializer
  (`django_strawberry_framework/extensions/debug.py::_serialize_sql_row`)
  owns the `float(entry["time"])` cast and its finiteness refusal, the slow
  predicate against a single module constant (`_SLOW_QUERY_SECONDS = 10`,
  graphene's threshold, never an inline `> 10` at two sites), the
  `select`-prefix sniff, and the six wire keys spelled as **literals**;
  `isSlow` / `isSelect` derive *inside* the serializer, never at a call
  site. Module level so the [Risks](#risks-and-open-questions)
  `_debug`-facade fallback (or any future card) imports them without
  instantiating the extension.
- [ ] **D5** — every remaining debug rule is **single-sited inside
  `extensions/debug.py`**: one `None`-guarded exception collector
  (`django_strawberry_framework/extensions/debug.py::_collect_exceptions`)
  owns the `result is None` / `errors is None` guards, the
  `original_error is not None` filter, and the chain-walk + serialize
  compose — preserving result-error order and emitting one row per
  qualifying outer error with **no speculative deduplication**; the hooks and
  `get_results` never re-spell the guards
  ([Decision 9](#decision-9--exception-capture-the-results-original_error-chain-serialized-like-graphenes-wrap_exception--no-resolver-wrapping)).
  One module-private, lock-protected bracket coordinator exposes exactly
  **two seams** — `acquire(connection) → token` / `release(token)` — and is
  the only code that touches the active-capture map, the saved flag values,
  and `connection.force_debug_cursor`; the map is keyed by **connection
  object identity, never by alias** (aliases name settings entries, while
  the mutable flag lives on a concrete per-thread connection wrapper — one
  alias names different objects on different threads), and
  `ExitStack.callback(...)` keeps the per-alias unwind declarative in
  `on_operation`
  ([Decision 7](#decision-7--hook-shape-one-sync-on_operation-generator-assembly-at-teardown-get_results-returns-the-stash)).
  One immutable per-alias snapshot record (`_ConnectionSnapshot`) retains
  exactly what teardown needs — the acquired connection object and the
  starting log length (named for the query log, never "window": the D-N5
  vocabulary rule); alias and vendor are read from that same retained
  connection at serialization, and teardown iterates the retained snapshots —
  never a second `connections.all()` call matched by position, since
  configured aliases or thread-local wrappers could differ by then. One
  log-slice helper (`_query_log_entries_since`) owns the
  `list(connection.queries_log)` materialization and the
  `min(snapshot, len(entries))` clamp, so the best-effort rollover caveat is
  documented on that one function ([Edge cases](#edge-cases-and-constraints));
  one per-row SQL guard (`_serialized_sql_row_or_dropped`) owns the drop-one-row
  degrade; one stash writer (`_stash_payload_if_executed`) owns the
  graphql-core-`ExecutionResult` test both teardowns share; and one payload
  builder (`_build_payload`) owns the `{"sql": [...], "exceptions": [...]}`
  spelling and routes every payload through spec-048's `_apply_payload_caps` —
  `get_results` reads the stash and never constructs shape, and each
  operation gets fresh containers (never class-level or module-level empty
  lists). The mechanics tests target those seams, not the hook body
  ([Test plan](#test-plan)).
- [ ] **D6** — pattern conformance with the package's established idioms
  (conformance, not code sharing): the **one `__init__`** initializes only
  configuration — the keyword-only `allow_unsafe_production` bool, validated
  at construction and settled into a `utils/private_state.py::PrivateAuthority`
  so a resolver cannot rewrite it through an attribute — and reaches
  `_OperationBoundExtension.__init__`; never a `**kwargs` sink, and never a
  claim that a constructor binds `execution_context`, which stays
  engine-assigned. The generator hooks read as the package's established
  generator-hook idiom (acquire pre-yield, `finally`-guarded release). The
  `original_error` walk follows the bounded-walk posture `utils/typing.py`
  pins with `MAX_TYPE_WRAPPER_DEPTH` — never a bare unbounded
  `while error.original_error:` peel; the identity set terminates cycles
  and a local 64-hop ceiling bounds acyclic chains
  ([Decision 9](#decision-9--exception-capture-the-results-original_error-chain-serialized-like-graphenes-wrap_exception--no-resolver-wrapping)) — while
  its *failure policy* deliberately differs (stop-on-cycle and retain the
  terminal, versus the type unwrappers' loud terminal raise), which is why
  it stays a local helper: extraction of a shared chain-peel into
  `utils/typing.py` waits until a **fourth** chain-peel appears (rule of
  three). `extensions/__init__.py` mirrors the eager-subpackage export
  shape — docstring + explicit re-export + `__all__`, as
  `utils/__init__.py` and `testing/__init__.py` do
  ([Decision 5](#decision-5--symbol-and-home-djangodebugextension-in-extensionsdebugpy-exported-from-the-extensions-subpackage--never-the-package-root)).
  And helper docstrings say "database connection", never bare
  "connection" — the D-N5 disambiguation made structural, so a grep across
  `utils/` and `extensions/` stays partitionable by noun.
- [ ] **D-N1** (no debug-local state mechanism) — per-operation state rides
  the package's shared `_OperationBoundExtension` binding
  (`_DebugOperationState` holds the snapshots and the payload), the same base
  the optimizer and the policy extensions derive from; the extension keeps no
  ContextVar, reset token, or instance stash of its own
  ([Decision 6](#decision-6--opt-in-shape-pass-the-class--one-fresh-instance-per-operation-requires-strawberry-03160)).
- [ ] **D-N2** (non-reuse) — no `utils/imports.py` guard
  ([`require_optional_module`][glossary-require-optional-module] /
  `require_*`): every import is a hard dependency; a guard would be
  ceremony with no absent-dependency case to serve — and falsely advertise a
  soft dependency. No `import_attr` deferred-import seam either: only
  `extensions/__init__.py` imports `debug.py`. Plain top-of-module imports.
- [ ] **D-N3** (non-reuse) — graphene's [`sql/tracking.py`][upstream-sql-tracking]
  is **not** ported ([Decision 4](#decision-4--fidelity-djangos-own-debug-cursor-via-a-force_debug_cursor-bracket-not-a-cursor-wrap-port)
  alternatives); the borrow is the *field vocabulary and its semantics*
  ([Decision 8](#decision-8--the-sql-row-shape-graphenes-wire-names-narrowed-to-what-djangos-log-supports)),
  not the instrumentation.
- [ ] **D-N4** (non-reuse) — nothing is shared with
  [`middleware/debug_toolbar.py`][middleware-debug-toolbar]: the toolbar
  subclasses a third-party Django middleware over the HTTP response; this is
  an engine extension over the execution result. The toolbar's payload
  helpers share nothing with the extensions-map merge — there is not even a
  constant to lift. The only relationship is documentation ("distinct from",
  both directions).
- [ ] **D-N5** (non-reuse) — **nothing is shared with
  `utils/connections.py`**, despite the name: that module's surface
  (window bounds, sidecar kwargs, range plans, probe arithmetic,
  `UnwindowableConnection`) serves **Relay pagination windows**; the debug
  extension's subject is `django.db.connections` — a different noun that
  happens to share the module name. The constraint runs both directions: no
  debug helper may be added to `utils/connections.py` (the "connections
  helpers live in `utils/connections`" instinct would put DB instrumentation
  state inside the Relay-window contract module), and the bracket
  coordinator stays module-private in `extensions/debug.py` — one consumer.
  Promote it only when another production feature needs the same overlap
  semantics, not merely another `try`/`finally`.
- [ ] **D-N6** (non-reuse) — `debug.py`'s imports are stdlib (`math`,
  `threading`, `traceback`, `collections.abc`, `contextlib`, `dataclasses`,
  `typing`), `django.conf` / `django.db`, `graphql` (the `ExecutionResult`
  the stash writer tests for and the `GraphQLError` the chain walk types
  against), `typing_extensions`, and from the package only the root `logger`,
  `exceptions.ConfigurationError` / `describe_value`,
  `utils/private_state.py::PrivateAuthority`, and `extensions/operation_state.py`
  — nothing from the query/write/input pipeline modules of `utils/`, which
  serve concerns the extension never touches (queryset visibility, generated
  inputs, input traversal, permissions, write decode, relation
  classification, converter dispatch). Three tempting near-misses, each
  rejected: `strings.graphql_camel_name` must not manufacture `isSlow` /
  `isSelect` (the keys are a wire contract —
  [Decision 8](#decision-8--the-sql-row-shape-graphenes-wire-names-narrowed-to-what-djangos-log-supports)'s
  wire-casing table, with the casing-helper rejection recorded in the
  [rationale companion][rationale-d8]); `errors.field_error` must not shape
  the exception row (the write-envelope `FieldError` is a different wire
  contract with field keys, paths, and codes — the only shared atom is
  `str()` coercion, beneath extraction); and `typing.is_async_callable` /
  `querysets.reject_async_in_sync_context` have no seam here (the extension
  ships sync generator hooks whose color dispatch the engine owns, and it
  calls no consumer-overridable hook).
- [ ] **D-N7** (non-reuse) — **no addition to `exceptions.py` and no
  module-local exception class**: the constructor raises the existing
  `ConfigurationError` for a non-`bool` acknowledgement; the SQL serializer's
  `ValueError` for a non-finite duration is internal and is caught by the
  per-row degrade; capture is otherwise best-effort, and the coordinator's
  acquire/release seams are private and bracketed. A later raise goes
  through `exceptions.py` (the bottom-of-import-graph single home), never a
  module-local class; the `UnwindowableConnection` precedent in
  `utils/connections.py` is the one sanctioned exception to that rule (a
  control-flow sentinel that must not be catchable as a package error), and
  debug has no such sentinel need.
- [ ] **D-N8** (non-reuse / premature abstraction) — the module introduces
  **no abstraction the one feature does not need**: no package base that owns
  a results key or payload (the shared `_OperationBoundExtension` binds
  operation state only; a base storing a key/payload would save a few lines
  while hiding the absent-before-teardown rule, conditional double-call
  idempotence, the masking order, and the security posture — those are the
  feature, not boilerplate); no merged `serialize_debug_row(kind, value)`
  dispatcher (the SQL and exception serializers share a return type and
  nothing else — different inputs, keys, normalization, ordering, and
  security properties); no runtime dataclasses or Strawberry types for the
  **wire rows** (plain dicts built once already match the response protocol;
  a dataclass row would need a second conversion pass before JSON, and a
  Strawberry type would re-create the schema surface
  [Decision 3](#decision-3--exposure-the-response-extensions-map-under-the-debug-key-not-a-schema-level-_debug-field)
  rejects — private `TypedDict`s and the small internal state records are
  fine where they aid static readability); and no per-key module constants
  beyond `_SLOW_QUERY_SECONDS` (the serializer's fixed dict is the single
  source of the wire spelling, [D4](#helper-reuse-obligations-dry);
  constantizing every key would scatter the shape across declarations and
  uses).

## Edge cases and constraints

- **Restore is saved-value, `ExitStack`-owned, overlap-safe, and nest-safe.**
  The bracket restores each connection's *prior* `force_debug_cursor` (not `False`), so
  an operation running inside a consumer's own `CaptureQueriesContext` (or
  under `DEBUG=True`, where `queries_logged` is true anyway) leaves the
  outer state intact. A lock-protected active-bracket map counts overlapping
  users of the same connection object and restores only when the count reaches
  zero, so async teardown order cannot leave a stale flag. The `finally`
  guarantees release even when the operation or serializer raises or the hook
  generator is abandoned, and unwinds earlier aliases if a later alias fails
  during acquisition. Without this, one enabled operation could leave process
  connections instrumented forever
  ([Decision 7](#decision-7--hook-shape-one-sync-on_operation-generator-assembly-at-teardown-get_results-returns-the-stash)).
- **An inert operation touches nothing.** Under the fail-closed gate
  (spec-048 Decision 5) the hook never enumerates the connections: no
  acquire, no snapshot, no flag write, no payload; the operation itself runs
  normally.
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
  rows fully.
- **Nested sync attribution is intentionally best effort.** The coordinator
  owns only `force_debug_cursor` restoration, not row attribution.
  Same-thread nested operations share one wrapper and `queries_log`;
  restoration remains correct, but the outer snapshot includes the inner
  interval, so the outer payload includes SQL emitted by the nested
  operation. Strict operation-local attribution would require a different
  instrumentation source.
- **Pre-execution failures carry no `debug` key.** Parse and validation
  errors return before execution; the engine calls `get_results` before the
  hook's teardown on those paths, and the stash writer refuses every result
  shape that is not a graphql-core `ExecutionResult`, so the extension
  contributes `{}` — deliberately, since nothing executed
  ([Decision 7](#decision-7--hook-shape-one-sync-on_operation-generator-assembly-at-teardown-get_results-returns-the-stash)).
  This holds on the streaming seam too. Client code must treat the key as
  operation-conditional, and the docstring says so.
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
  ([`django/db/backends/base/base.py`][venv-django-base] wraps `_commit` /
  `_rollback` / `set_autocommit` in it whenever `queries_logged` is true).
  So an `atomic()` block **entered and exited inside the operation** — the
  generated mutation's own transaction included — emits `BEGIN` / `COMMIT`
  rows beside its `INSERT` (each with `isSelect: false`). Explicitly
  **excluded**: transaction boundaries that enclose the GraphQL execution
  itself — `ATOMIC_REQUESTS` / transaction middleware wrap the *view*, so
  their outer `BEGIN` runs before the extension enters and their final
  `COMMIT` / `ROLLBACK` (plus any commit failure and `on_commit` work) runs
  after it tears down; those rows are never captured, and the inner write's
  `atomic()` shows as a `SAVEPOINT` (Test plan scenario 19 pins the
  inclusion/exclusion boundary). Within scope, this matches `assertNumQueries`
  visibility — the payload shows what Django's own accounting shows — and it
  is why the [Test plan](#test-plan)'s row assertions filter by `isSelect` /
  statement prefix rather than asserting positional indices or raw totals.
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
  admitted schema carries `{"sql": [], "exceptions": []}` — harmless, and a
  skip rule (the toolbar's `IntrospectionQuery` guard exists to protect its
  request *history*, a concern with no analogue here) would add a branch
  with no payer.
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
  retention point below). The module docstring, the GLOSSARY entry, and this
  section all carry that enumeration. The boundary is the off-by-default,
  code-level opt-in plus spec-048's `DEBUG` gate; there is no redaction
  subsystem ([Risks](#risks-and-open-questions)).
- **`extensions`-map cohabitation.** Among extension outputs, the runner
  merges `get_results()` in list order and the later-listed same-key value
  wins. Async execution then overlays
  `ExecutionContext.extensions_results`, which has final precedence; sync
  has no equivalent overlay. The completed map replaces rather than merges
  any pre-existing `ExecutionResult.extensions`
  ([Error shapes](#error-shapes)). The payload is JSON-serializable by
  construction (str / float / bool / list / dict only, and a non-finite
  duration is refused), so no transport encoder can choke on it.
- **Zero debug cost when disabled; bounded payload when enabled.** Disabled,
  no debug code runs (the class is not in the list). Enabled and admitted,
  the per-operation cost is: `connections.all()` materializes a Django
  wrapper for **every configured alias** (no raw DB connection is opened,
  but wrapper construction can import a backend and surface an invalid
  alias/backend configuration); setup writes one saved-flag record per
  alias; execution pays Django's own debug-cursor overhead (the same cost
  `DEBUG=True` dev servers already pay); and teardown performs
  `list(connection.queries_log)` per alias — copying up to `queries_limit`
  (default 9000) entry references even when an old, already-full log holds
  no rows from this operation — plus one serialization pass per teardown (two per
  executed operation). Under async schema execution that
  synchronous teardown runs **on the event-loop thread** and can stall it.
  The published payload is bounded by spec-048 Decision 6's row-count caps,
  per-row character limits, and shared text budget. Retention: captured rows
  also remain in Django's per-connection deque after the response; over HTTP
  the `request_started` signal resets the log before the next view, but
  non-HTTP in-process execution has no such reset, so interpolated values
  persist in memory until reset or eviction. No plan interaction, no
  [plan-cache][glossary-plan-cache] key change, no queryset touch.

## Test plan

Scenarios 1–7 and 19 live in
`examples/fakeshop/test_query/test_debug_extension_api.py`; scenarios 8–15,
17, 18, and 20–23 live in `tests/extensions/test_debug.py`; the
operation-owned-payload rows span both modules; the sharded-tier
scenario 16 lives in [`test_multi_db.py`][test-multi-db] behind
`FAKESHOP_SHARDED=1`
([Decision 11](#decision-11--test-strategy-split-live-http-behavior-from-package-tier-mechanics)).
The spec-048 gate and cap rows live in the same two modules and belong to
[`spec-048`][spec-048]'s Test plan.

The suite runs with `settings.DEBUG = False` — the extension's fail-closed
condition — so every payload-expecting test declares its posture: the live
tier builds the extension through the acknowledgement factory, and the
mechanics tier uses `override_settings(DEBUG=True)` where the case is about the
bare class entry's own semantics, keeping the factory where `DEBUG=False` is
itself the point. The **request-driving group** posts real HTTP through the
probe URLconf (a debug-enabled `DjangoSchema` over freshly-reloaded fakeshop
types; the [schema-reload][glossary-schema-reload-discipline] +
[`seed_data`][glossary-seed-data] disciplines; posts through
[`TestClient`][glossary-testclient] with `assert_no_errors=False` where a
scenario expects errors). A local accessor validates-and-returns the debug
payload — both keys present, every row's key set, a `float` `duration` — for
the executed-operation scenarios, but never for the absence scenarios, which
assert the missing key explicitly. The **mechanics group** needs no request; it
drives **real objects** wherever practical — real `GraphQLError` wrappers for
the chain cases, real `MaskErrors`, real Strawberry execution for lifecycle and
idempotence, real connection wrappers and a real bounded `deque` for the
restore/rollover cases — and parametrizes genuinely identical bodies.
Two of its rules are deliberate ([DRY D4–D5](#helper-reuse-obligations-dry)):
assertions re-spell the wire keys and the 10-second threshold as
**independent literals** — never importing `_SLOW_QUERY_SECONDS` or building
expected rows through the production serializer, because a self-referential
assertion would let a key rename pass green — and the concurrency/lifecycle
scenarios exercise the coordinator's two seams and the log-slice clamp rather
than `on_operation`'s body.
Per the repo rule the suite is not run unless the maintainer asks — the
[`AGENTS.md`][agents] #"No pytest after edits" workflow rule. The **targeted**
development commands must replace `pytest.ini`'s `addopts` (which always adds
`--cov`, while `pyproject.toml` enforces repository-wide `fail_under = 100` —
a single-file run passes its tests and then fails the global coverage gate):

- `uv run pytest -o addopts="-v -n0" examples/fakeshop/test_query/test_debug_extension_api.py`
- `uv run pytest -o addopts="-v -n0" tests/extensions/test_debug.py`
- the isolated Strawberry-floor node-ID run uses the same override.

The **full-suite** command (plain `uv run pytest`) — and CI's
coverage-owning node — remain the sole owners of the 100% gate.

**Request-driving (probe URLconf, real HTTP):**

- **1. Happy-path SQL capture, `DEBUG=False`** —
   `test_query_capture_uses_the_forced_debug_cursor_not_debug_query_logging`.
   `seed_data(1)` plus one anonymous-visible item; a products connection query
   → `res.data` intact, `debug.sql` non-empty; the first **`isSelect`** row
   (never positional indexing — transaction rows are in-contract,
   [Edge cases](#edge-cases-and-constraints)) carries
   `vendor == connection.vendor`, `alias == "default"`, an interpolated `sql`
   containing `SELECT` and no `%s`, a `float` `duration`, `isSlow is False`,
   `isSelect is True`; `exceptions == []`. The test asserts
   `settings.DEBUG is False` first — proving the bracket, not Django's
   `DEBUG` logging, produced the capture
   ([Decision 4](#decision-4--fidelity-djangos-own-debug-cursor-via-a-force_debug_cursor-bracket-not-a-cursor-wrap-port)).
- **2. Optimizer composition** —
   `test_optimizer_composition_shows_the_two_query_prefetch_shape`. The probe
   schema carries one module-local `_optimizer = DjangoOptimizerExtension()`
   singleton returned by `lambda: _optimizer` beside the debug factory — no
   helper normalizes the two entries, because the shape difference documents
   their intentionally different lifetimes
   ([Decision 6](#decision-6--opt-in-shape-pass-the-class--one-fresh-instance-per-operation-requires-strawberry-03160));
   a nested `allItems { edges { node { name category { name } } } }`
   selection over `seed_data(2)` rows → the captured **SELECT rows** match the
   optimizer's planned **visibility-safe two-query shape**: exactly one
   `products_item` slice and exactly one `products_category` prefetch query,
   with **no** `products_item`/`products_category` JOIN and no per-item
   category queries ([Goals](#goals) item 5). The item row's `sql` shows the
   projected column list — the payload demonstrating
   [`only()` projection][glossary-only-projection].
- **3. Mutation capture** — `test_mutation_capture_includes_the_insert_row`
   (`django_db(transaction=True)`, so the generated mutation's own
   completion-spanning transaction emits real `BEGIN` / `COMMIT`).
   `create_users(1)` and `seed_data(1)`; the **non-staff** `view_item_1` user
   is granted only `add_item` and re-fetched to drop the stale permission
   cache; a **visible** category `GlobalID` is the required `categoryId`;
   authenticated via `with client.login(user):` → `debug.sql` contains an
   `INSERT` row with `isSelect is False`, the pipeline's SELECTs, and `BEGIN` /
   `COMMIT` rows — asserted by statement prefix, never by position or total.
- **4. Resolver exception** —
   `test_resolver_exception_produces_an_unmasked_exception_row`. A probe field
   that raises `ZeroDivisionError` → the GraphQL error AND
   `debug.exceptions == [one row]` with `excType ==
   "<class 'ZeroDivisionError'>"`, the message, and a `stack` containing
   `"Traceback"`; `debug.sql` present — the two lists are independent
   ([Decision 9](#decision-9--exception-capture-the-results-original_error-chain-serialized-like-graphenes-wrap_exception--no-resolver-wrapping)).
- **5. Validation versus execution error boundary** —
   `test_validation_versus_execution_error_boundary`. An unknown-field
   selection → `errors` present, no `debug` key. A probe field returning
   `None` for a non-null type: execution occurs, graphql-core raises a
   completion error, and the response carries one `exceptions` row — the
   documented result-level widening beyond graphene's resolver-only
   middleware.
- **6. No-SQL operation** — `test_no_sql_operation_carries_both_empty_lists`.
   `{ __typename }` → `debug == {"sql": [], "exceptions": []}`.
- **7. Off-by-default** — `test_off_by_default_publishes_no_debug_key` (the same
   probe view with no debug entry → no `debug` key and no unrelated envelope
   widening) and `test_project_graphql_endpoint_publishes_no_debug_key` (the
   project's real `/graphql/` carries no `debug` key).
- **19. Transaction-boundary scope** — inclusion is scenario 3's `BEGIN` /
    `COMMIT` around the generated write;
    `test_enclosing_atomic_requests_transaction_is_not_captured` proves the
    exclusion: with `ATOMIC_REQUESTS` on for the request's alias (and
    `DEBUG=True` with the toolbar dropped), the payload carries the write's
    `SAVEPOINT` and no `BEGIN` / `COMMIT`
    ([Edge cases](#edge-cases-and-constraints)).

**Mechanics (no request):**

- **8. Restore contract** — `test_coordinator_saved_value_restore_and_depth`
   (both prior flag values, depth, exact saved-value restore, identity-keyed
   map), `test_coordinator_isolates_distinct_wrappers_for_one_alias`,
   `test_execute_sync_restores_the_prior_flag_value` (around real
   `schema.execute_sync`), `test_query_log_slicing_suffix_clamp_and_rollover`
   (a shortened log returns `[]`; full-deque rollover is pinned as best
   effort), and `test_partial_acquisition_failure_unwinds_earlier_connections`
   (the one fake, at the private acquisition boundary — never a mock of
   Strawberry's runner).
- **9. Async color and overlap-safe restore** —
   `test_async_overlapping_operations_share_the_wrapper_and_restore`. Two
   overlapping `schema.execute(...)` calls with raising async resolvers, the
   wrapper materialized in the parent context before task creation and
   asserted by identity inside each operation, both resolvers blocked until
   coordinator depth two, released in both completion orders. Each response
   carries its own exception row; afterward the flag is restored and the map
   is empty. SQL content is deliberately **not** asserted beyond type (the
   documented thread-locality caveat).
- **10. Serializer units** — `test_exception_serializer_triple_forms`,
    `test_exception_serializer_chained_traceback_stack`,
    `test_sql_row_serializer_slow_threshold_and_executemany_form` (the
    strictly-greater-than-10 cut and the verbatim `"3 times: ..."` form),
    `test_exception_collector_guards_filter_order_and_no_dedup` (both `None`
    guards, validation errors skipped, a terminal explicitly raised
    `GraphQLError` kept, order preserved, no dedup), and
    `test_nested_original_error_chain_reaches_the_terminal_python_exception`.
- **11. `get_results` no-stash shape and idempotence** —
    `test_get_results_no_stash_shape_and_idempotent_read` (`{}` outside an
    operation and before a payload, never `{"debug": None}`; the stash under
    exactly `"debug"`, identical on two reads; `json.dumps` round-trip);
    `test_validation_failure_with_raising_teardown_calls_get_results_twice`
    (the real engine's double call, both `{}`);
    `test_parse_failure_with_raising_teardown_publishes_no_debug_key`;
    `test_async_validation_failure_with_raising_teardown_publishes_no_debug_key`
    (a `PreExecutionError` is not execution); and
    `test_generic_recovery_alone_calls_get_results_once`.
- **12. Masking-extension ordering** —
    `test_mask_errors_ordering_controls_exception_visibility`: with
    `MaskErrors` before the debug class the masked `errors` sit beside one
    unmasked `exceptions` row; reversed, `debug.exceptions == []`
    ([Decision 9](#decision-9--exception-capture-the-results-original_error-chain-serialized-like-graphenes-wrap_exception--no-resolver-wrapping)).
- **13. Concurrent sync isolation at the floor** —
    `test_concurrent_sync_operations_use_isolated_instances`. Two blocking
    resolvers run concurrently in a `ThreadPoolExecutor` behind a barrier,
    with **no ORM work in the executor threads**; isolation is proved by each
    response carrying only its own exception marker, distinct per-thread
    wrapper identities, and each thread-local wrapper's restored flag. Run in
    the isolated `strawberry-graphql==0.322.2` floor environment as well as
    the normal suite — selected by **node id**, never a copied script, with
    the coverage-free `-o addopts=...` override. This is the regression that
    fails under the old cached `_sync_extensions` lifecycle; it does not
    prove same-wrapper refcounting, which scenario 9 owns.
- **14. Merge precedence and result-map replacement** —
    `test_extension_list_order_wins_same_key_collisions_sync`,
    `test_extension_list_order_wins_same_key_collisions_async`,
    `test_async_context_results_overlay_has_final_precedence`,
    `test_sync_runner_has_no_context_results_overlay`, and
    `test_prepopulated_result_extensions_map_is_replaced_not_merged`.
- **15. Nested sync attribution boundary** —
    `test_nested_sync_operations_share_the_log_and_cross_attribute`: the inner
    payload holds only its interval, the outer payload also holds the inner
    SQL, and the flag restores.
- **17. Diagnostic non-interference** —
    `test_sql_diagnostic_failure_degrades_payload_and_preserves_the_result`
    (a malformed log entry costs its own row; `data` intact; flag restored),
    `test_a_failing_query_log_drain_degrades_to_the_rows_serialized_so_far`,
    and `test_exception_diagnostic_failure_degrades_to_an_empty_list`
    ([Error shapes](#error-shapes)).
- **18. Cursor-construction lifetime boundary** —
    `test_cursor_construction_defines_the_capture_interval`: a cursor opened
    *before* acquire stays uninstrumented inside the bracket, and a debug
    cursor opened *inside* keeps logging after release
    ([Decision 4](#decision-4--fidelity-djangos-own-debug-cursor-via-a-force_debug_cursor-bracket-not-a-cursor-wrap-port)).
- **20. Sibling-hook SQL ordering** —
    `test_sibling_hook_sql_capture_is_list_order_dependent`: a sibling whose
    `on_operation` runs marker SQL around its `yield`, in both list orders.
- **21. `original_error` hop policy** —
    `test_hop_policy_self_cycle_terminates_deterministically`,
    `test_hop_policy_multi_node_cycle_returns_last_unique_candidate`, and
    `test_hop_policy_long_acyclic_chain_stops_at_the_ceiling`
    ([Decision 9](#decision-9--exception-capture-the-results-original_error-chain-serialized-like-graphenes-wrap_exception--no-resolver-wrapping)).
- **22. The streaming seam** —
    `test_streaming_seam_publishes_the_payload_the_engine_reads` (a streamed
    operation carries `extensions["debug"]` like `execute` does),
    `test_streaming_clean_operation_carries_both_lists`, and
    `test_streaming_parse_failure_publishes_no_debug_key`
    ([Decision 7](#decision-7--hook-shape-one-sync-on_operation-generator-assembly-at-teardown-get_results-returns-the-stash)).
- **23. Hostile shapes degrade, never raise** —
    `test_a_non_finite_duration_is_refused_at_the_serializer`,
    `test_a_nan_duration_costs_only_its_own_row_and_the_rest_keep_their_order`
    (only the NaN row is lost; the rows after it keep log order),
    `test_hostile_exception_str_degrades_to_an_empty_list`,
    `test_non_iterable_errors_scalar_degrades_to_an_empty_list`, and
    `test_abandoned_hook_generator_close_restores_the_flag`
    ([Error shapes](#error-shapes)).
- **The payload belongs to the operation** —
    `test_one_operations_payload_is_not_the_extensions` (two operations on one
    shared entry under a `DjangoSchema` get two payloads, and nothing is left
    on the extension), with the live
    `test_a_parse_failure_never_republishes_the_previous_operations_payload`
    proving a shared entry's parse failure publishes no stale payload
    ([Decision 6](#decision-6--opt-in-shape-pass-the-class--one-fresh-instance-per-operation-requires-strawberry-03160)).

**Sharded tier:**

- **16. Multi-database capture** —
    `test_multi_db.py::test_debug_extension_captures_shard_b_alias_rows`
    (`FAKESHOP_SHARDED=1`). A real query routed to `shard_b` through a
    debug-enabled probe schema → a captured row reports `alias == "shard_b"`
    and the correct vendor, and **both** configured aliases restore their
    prior flags
    ([Decision 10](#decision-10--multi-database-capture-every-alias-in-connectionsall-one-bracket-each)).

Coverage: the package gate is `fail_under = 100` and `extensions/debug.py`
is package code; every branch above has a named owner. A branch unreachable
through these gets its own targeted unit — named owner, never a blanket claim.

## Doc updates

- [`docs/GLOSSARY.md`][glossary] (via the glossary DB +
  [`scripts/build_glossary_md.py`][build-glossary-md] — the file is
  DB-rendered, never hand-edited) — the
  [Response-extensions debug middleware][glossary-response-extensions-debug-middleware]
  entry and its focused companions carry the implemented contract: the
  `django_strawberry_framework.extensions` import path and class-form
  opt-in, the `debug` key and two-list payload, the six SQL fields with the
  named omissions and the `executemany` form, the exception triple and the
  nested `original_error` walk (including the documented result-level
  widening), the reference-counted `force_debug_cursor` bracket, the
  best-effort bounded-log behavior, per-operation isolation, the per-alias
  multi-DB behavior, the `callproc()` omission, the cursor-construction
  capture-interval boundary, the transaction-boundary scope (enclosing
  `ATOMIC_REQUESTS` excluded), the two-phase failure policy, the nested-sync
  attribution boundary, extension-list merge precedence, async context-results
  precedence, result-map replacement, the pre-execution-error no-key rule, the
  dev-only security caveat with the full disclosure enumeration (interpolated
  SQL values, traceback paths, retention, downstream copies), and the async SQL
  caveat; the real cookbook migration from the aggregate `_debug` field +
  `GRAPHENE["MIDDLEWARE"]` pair to the one extension class; and the resulting
  client move to `response.extensions.debug` — plus the "distinct from the
  [Debug-toolbar middleware][glossary-debug-toolbar-middleware]" cross-references
  in both entries.
- [`docs/TREE.md`][tree] — rendered via
  [`scripts/build_tree_md.py`][build-tree-md]: the package tree's
  docstring-derived `extensions/` rows and the test tree's
  `tests/extensions/test_debug.py` and
  `examples/fakeshop/test_query/test_debug_extension_api.py` rows.
- [`config/schema.py`][config-schema] — the docstring names the opt-in
  extension and its deliberate omission
  ([Decision 2](#decision-2--card-scope-boundary-the-extension-ships-alone--no-django-middleware-no-schema-field-no-fakeshop-always-on-wiring)).
- [`GOAL.md`][goal] — success criterion 7's scope (the import-only promise
  covers `Meta`-driven domain declarations; engine configuration migrates by
  documented recipe), so the debug migration is a documented application of
  the criterion rather than an exception to it
  ([Goal and cookbook cross-reference](#goal-and-cookbook-cross-reference)).
- The `0.0.14` cut's release-status moves ([`README.md`][readme],
  [`docs/README.md`][docs-readme], [`TODAY.md`][today], `CHANGELOG.md`) are
  Decision 12's
  ([Decision 12](#decision-12--this-card-completes-the-joint-0014-cut-and-owns-the-version-bump)).

## Risks and open questions

- **Exposure selectivity: all-or-nothing vs. graphene's per-query pull.**
  With the map exposure, an admitted schema pays capture + payload on every
  operation, where graphene consumers select `_debug` only on the queries
  they are diagnosing. **Preferred answer:** accept it — the intended
  deployment is a development schema, where always-on is the point, and
  spec-048's gate keeps a non-debug deployment inert unless it acknowledges
  the disclosure. **Fallback:** a constructor predicate or a request-header
  gate as a follow-on knob once a real consumer asks — additive, no shape
  change (any such gate reads the request through
  `utils/permissions.request_from_info`, the package's one sanctioned
  request-access entry point — the extension itself never touches the
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
  and scope criterion 7's import-only promise to `Meta`-driven domain
  declarations, as [`GOAL.md`][goal] does. **Fallback / follow-on:**
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
  async consumers report gaps, decided against a real ASGI-request prototype
  ([rationale companion][rationale-risks]).
- **Engine ordering coupling.** The no-`debug`-key-on-pre-execution-errors
  behavior and the two-teardown stash ride the engine's call ordering
  (`get_results` inside the operation context on early returns and on the
  streaming path, after it on the `execute` / `execute_sync` happy path). A
  future Strawberry release could reorder — the failure mode is caught loudly
  by scenarios 1, 5, 11, and 22 under a refreshed lock. **Preferred answer:**
  accept; `uv.lock` plus the regression tests pin the resolved version's
  semantics, and the `>=0.322.2` lower bound excludes the known cached-sync
  lifecycle (an open bound cannot itself "pin" future semantics —
  [Decision 6](#decision-6--opt-in-shape-pass-the-class--one-fresh-instance-per-operation-requires-strawberry-03160)).
- **`queries_log` eviction under pathological operations.** An operation
  that rolls over a full bounded deque can lose old operation rows and, when
  the length remains unchanged from the snapshot, can report no rows at all
  ([Edge cases](#edge-cases-and-constraints)). **Preferred answer:** accept
  and document the exact best-effort boundary; Django's own capture context
  has the same length-snapshot limitation. A reliable `truncated: true`
  marker would require operation-local instrumentation or a monotonic query
  counter, not merely another comparison against deque length. **Fallback:**
  a separate fidelity card that changes the capture source.

## Out of scope (explicitly tracked elsewhere)

- **The schema-level `_debug` field flavor** — rejected
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
  fakeshop-activation beta card ([`TODO-BETA-066-0.1.5`][kanban]) is the
  natural host
  ([Decision 11](#decision-11--test-strategy-split-live-http-behavior-from-package-tier-mechanics)).
- **Further knobs** (enable predicates, slow-query thresholds, redaction) —
  follow-on once a consumer asks ([Risks](#risks-and-open-questions)).
- **Thread-sensitive async instrumentation** — the named follow-on
  ([Risks](#risks-and-open-questions)).
- **Subscriptions** — no debug contract for per-event results
  ([Non-goals](#non-goals)).
- **Experimental incremental execution** (`@defer` / `@stream` payload
  semantics) — excluded from the contract ([Non-goals](#non-goals)).
- **Explicitly cross-thread-shared connection wrappers**
  (`inc_thread_sharing()`) — unsupported / best-effort
  ([Edge cases](#edge-cases-and-constraints)); the non-interference rule
  still protects the response.

## Definition of done

- [ ] `django_strawberry_framework/extensions/debug.py` exists, with module
      + symbol docstrings, exposing `DjangoDebugExtension` (an
      `_OperationBoundExtension`) implementing the sync `on_operation`
      bracket, the `on_execute` streaming stash, and `get_results` per
      [Decisions 4](#decision-4--fidelity-djangos-own-debug-cursor-via-a-force_debug_cursor-bracket-not-a-cursor-wrap-port)–[10](#decision-10--multi-database-capture-every-alias-in-connectionsall-one-bracket-each),
      with the exposure and fidelity choices pinned
      ([Decision 3](#decision-3--exposure-the-response-extensions-map-under-the-debug-key-not-a-schema-level-_debug-field)
      / [Decision 4](#decision-4--fidelity-djangos-own-debug-cursor-via-a-force_debug_cursor-bracket-not-a-cursor-wrap-port)).
- [ ] The payload lands under `extensions["debug"]` with `sql` rows carrying
      `vendor` / `alias` / `sql` / `duration` / `isSlow` / `isSelect` and
      `exceptions` rows carrying `excType` / `message` / `stack` — graphene's
      wire names where the fidelity supports them, every narrowing — including
      the `callproc()` omission and nested-sync attribution boundary — named
      in the GLOSSARY entry and the module docstring
      ([Decision 8](#decision-8--the-sql-row-shape-graphenes-wire-names-narrowed-to-what-djangos-log-supports)).
- [ ] Off by default; the opt-in is the class in the schema's `extensions=`
      list; with the extension absent, no debug instrumentation runs and no
      `debug` key is added (Test plan scenario 7)
      ([Decision 6](#decision-6--opt-in-shape-pass-the-class--one-fresh-instance-per-operation-requires-strawberry-03160)).
- [ ] `from django_strawberry_framework.extensions import DjangoDebugExtension`
      resolves; nothing is added to the package root
      ([Decision 5](#decision-5--symbol-and-home-djangodebugextension-in-extensionsdebugpy-exported-from-the-extensions-subpackage--never-the-package-root)).
- [ ] **No new dependency is added**; the `strawberry-graphql>=0.322.2`
      floor in `[project].dependencies` includes per-operation extension
      construction, concurrent sync isolation passes at that exact floor, and
      the floor is durably exercised by CI nodes force-installing `0.322.2`
      ([`.github/workflows/django.yml`][workflow-django]).
- [ ] The split tests cover the [Test plan](#test-plan):
      `examples/fakeshop/test_query/test_debug_extension_api.py` owns real
      probe-URLconf HTTP against fakeshop models ("against a fakeshop request
      that emits SQL") under schema-reload, `seed_data`, and
      [`TestClient`][glossary-testclient] disciplines;
      `tests/extensions/test_debug.py` owns request-impossible mechanics.
      [Decision 11](#decision-11--test-strategy-split-live-http-behavior-from-package-tier-mechanics)
      records the placement rule. The package coverage gate (`fail_under =
      100`) holds with `extensions/` included, each branch mapped to a named
      owner.
- [ ] The Slice 2 doc updates hold per [Doc updates](#doc-updates): the
      GLOSSARY entries (via the DB + re-render), the rendered
      [`docs/TREE.md`][tree], the [`config/schema.py`][config-schema]
      docstring, the [`GOAL.md`][goal] criterion-7 scope, and the
      response-side-counterpart cross-references to the toolbar middleware in
      both entries. The GLOSSARY entry includes the concrete cookbook
      migration from `_debug` + `DjangoDebugMiddleware` to the aggregate
      extension opt-in and response-map read.
- [ ] **The joint `0.0.14` cut landed in Slice 3**
      ([Decision 12](#decision-12--this-card-completes-the-joint-0014-cut-and-owns-the-version-bump))
      and the card reads `DONE-044-0.0.14` after the DB-backed final wrap and
      terms import.
- [ ] `uv run ruff format .` / `ruff check --fix .` clean after every slice;
      pre-commit hooks run before any commit the maintainer requests; no
      `pytest` unless the maintainer asks (the [`START.md`][start] workflow
      rules).

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[goal]: ../../GOAL.md
[kanban]: ../../KANBAN.md
[readme]: ../../README.md
[start]: ../../START.md
[today]: ../../TODAY.md
[workflow-django]: ../../.github/workflows/django.yml

<!-- docs/ -->
[docs-readme]: ../README.md
[glossary]: ../GLOSSARY.md
[glossary-async-sql-capture-boundary]: ../GLOSSARY.md#async-sql-capture-boundary
[glossary-bounded-query-log-rollover]: ../GLOSSARY.md#bounded-query-log-rollover
[glossary-channels-request-adapter]: ../GLOSSARY.md#channels-request-adapter
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-cookbook-parity]: ../GLOSSARY.md#cookbook-parity
[glossary-debug-exception-row]: ../GLOSSARY.md#debug-exception-row
[glossary-debug-fail-closed-gate]: ../GLOSSARY.md#debug-fail-closed-gate
[glossary-debug-payload-availability]: ../GLOSSARY.md#debug-payload-availability
[glossary-debug-payload-caps]: ../GLOSSARY.md#debug-payload-caps
[glossary-debug-sql-row]: ../GLOSSARY.md#debug-sql-row
[glossary-debug-toolbar-middleware]: ../GLOSSARY.md#debug-toolbar-middleware
[glossary-developer-only-debug-posture]: ../GLOSSARY.md#developer-only-debug-posture
[glossary-django-debug-cursor-capture]: ../GLOSSARY.md#django-debug-cursor-capture
[glossary-django-trac-37064]: ../GLOSSARY.md#django-trac-37064-hardening
[glossary-djangodebugextension]: ../GLOSSARY.md#djangodebugextension
[glossary-djangographqlprotocolrouter]: ../GLOSSARY.md#djangographqlprotocolrouter
[glossary-djangooptimizerextension]: ../GLOSSARY.md#djangooptimizerextension
[glossary-eviction-simulated-absence]: ../GLOSSARY.md#eviction-simulated-absence
[glossary-finalize-django-types]: ../GLOSSARY.md#finalize_django_types
[glossary-get-queryset]: ../GLOSSARY.md#get_queryset-visibility-hook
[glossary-graphene-debug-migration]: ../GLOSSARY.md#graphene-debug-migration
[glossary-graphqltestcase]: ../GLOSSARY.md#graphqltestcase
[glossary-hard-dependency]: ../GLOSSARY.md#hard-dependency
[glossary-joint-version-cut]: ../GLOSSARY.md#joint-version-cut
[glossary-live-first-coverage-mandate]: ../GLOSSARY.md#live-first-coverage-mandate
[glossary-masking-extension-ordering]: ../GLOSSARY.md#masking-extension-ordering
[glossary-multi-database-cooperation]: ../GLOSSARY.md#multi-database-cooperation
[glossary-only-projection]: ../GLOSSARY.md#only-projection
[glossary-pep-562-lazy-export]: ../GLOSSARY.md#pep-562-lazy-export
[glossary-per-operation-extension-isolation]: ../GLOSSARY.md#per-operation-extension-isolation
[glossary-plan-cache]: ../GLOSSARY.md#plan-cache
[glossary-probe-urlconf]: ../GLOSSARY.md#probe-urlconf
[glossary-reference-counted-cursor-coordinator]: ../GLOSSARY.md#reference-counted-cursor-coordinator
[glossary-require-optional-module]: ../GLOSSARY.md#require_optional_module
[glossary-response-extension-merge-semantics]: ../GLOSSARY.md#response-extension-merge-semantics
[glossary-response-extensions-debug-middleware]: ../GLOSSARY.md#response-extensions-debug-middleware
[glossary-schema-reload-discipline]: ../GLOSSARY.md#schema-reload-discipline
[glossary-seed-data]: ../GLOSSARY.md#seed_data
[glossary-single-upstream-parity]: ../GLOSSARY.md#single-upstream-parity
[glossary-soft-dependency]: ../GLOSSARY.md#soft-dependency
[glossary-strawberry-config]: ../GLOSSARY.md#strawberry_config
[glossary-strawberry-extension-lifecycle]: ../GLOSSARY.md#strawberry-extension-lifecycle
[glossary-strictness-mode]: ../GLOSSARY.md#strictness-mode
[glossary-testclient]: ../GLOSSARY.md#testclient
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[next]: NEXT.md
[rationale]: appx/spec-044-debug_extension-0_0_14-rationale.md
[rationale-d1]: appx/spec-044-debug_extension-0_0_14-rationale.md#decision-1--spec-filename-and-canonical-naming
[rationale-d10]: appx/spec-044-debug_extension-0_0_14-rationale.md#decision-10--multi-database-capture-every-alias-in-connectionsall-one-bracket-each
[rationale-d11]: appx/spec-044-debug_extension-0_0_14-rationale.md#decision-11--test-strategy-split-live-http-behavior-from-package-tier-mechanics
[rationale-d12]: appx/spec-044-debug_extension-0_0_14-rationale.md#decision-12--this-card-completes-the-joint-0014-cut-and-owns-the-version-bump
[rationale-d2]: appx/spec-044-debug_extension-0_0_14-rationale.md#decision-2--card-scope-boundary-the-extension-ships-alone--no-django-middleware-no-schema-field-no-fakeshop-always-on-wiring
[rationale-d3]: appx/spec-044-debug_extension-0_0_14-rationale.md#decision-3--exposure-the-response-extensions-map-under-the-debug-key-not-a-schema-level-_debug-field
[rationale-d4]: appx/spec-044-debug_extension-0_0_14-rationale.md#decision-4--fidelity-djangos-own-debug-cursor-via-a-force_debug_cursor-bracket-not-a-cursor-wrap-port
[rationale-d5]: appx/spec-044-debug_extension-0_0_14-rationale.md#decision-5--symbol-and-home-djangodebugextension-in-extensionsdebugpy-exported-from-the-extensions-subpackage--never-the-package-root
[rationale-d6]: appx/spec-044-debug_extension-0_0_14-rationale.md#decision-6--opt-in-shape-pass-the-class--one-fresh-instance-per-operation-requires-strawberry-03160
[rationale-d7]: appx/spec-044-debug_extension-0_0_14-rationale.md#decision-7--hook-shape-one-sync-on_operation-generator-assembly-at-teardown-get_results-returns-the-stash
[rationale-d8]: appx/spec-044-debug_extension-0_0_14-rationale.md#decision-8--the-sql-row-shape-graphenes-wire-names-narrowed-to-what-djangos-log-supports
[rationale-d9]: appx/spec-044-debug_extension-0_0_14-rationale.md#decision-9--exception-capture-the-results-original_error-chain-serialized-like-graphenes-wrap_exception--no-resolver-wrapping
[rationale-risks]: appx/spec-044-debug_extension-0_0_14-rationale.md#risks-and-open-questions
[spec-042]: spec-042-debug_toolbar-0_0_14.md
[spec-043]: spec-043-test_client-0_0_14.md
[spec-048]: spec-048-secure_output_defaults-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[middleware-debug-toolbar]: ../../django_strawberry_framework/middleware/debug_toolbar.py
[optimizer-extension]: ../../django_strawberry_framework/optimizer/extension.py

<!-- tests/ -->

<!-- examples/ -->
[config-schema]: ../../examples/fakeshop/config/schema.py
[schema-reload]: ../../examples/fakeshop/schema_reload.py
[test-multi-db]: ../../examples/fakeshop/test_query/test_multi_db.py

<!-- scripts/ -->
[build-glossary-md]: ../../scripts/build_glossary_md.py
[build-kanban-md]: ../../scripts/build_kanban_md.py
[build-tree-md]: ../../scripts/build_tree_md.py

<!-- .venv/ -->
[venv-base-extension]: ../../.venv/lib/python3.14/site-packages/strawberry/extensions/base_extension.py
[venv-django-base]: ../../.venv/lib/python3.14/site-packages/django/db/backends/base/base.py
[venv-django-test-utils]: ../../.venv/lib/python3.14/site-packages/django/test/utils.py
[venv-django-utils]: ../../.venv/lib/python3.14/site-packages/django/db/backends/utils.py
[venv-extensions-context]: ../../.venv/lib/python3.14/site-packages/strawberry/extensions/context.py
[venv-runner]: ../../.venv/lib/python3.14/site-packages/strawberry/extensions/runner.py
[venv-schema]: ../../.venv/lib/python3.14/site-packages/strawberry/schema/schema.py

<!-- External -->
[upstream-cookbook-recipes-schema]: ../../../django-graphene-filters/examples/cookbook/cookbook/recipes/schema.py
[upstream-cookbook-schema]: ../../../django-graphene-filters/examples/cookbook/cookbook/schema.py
[upstream-cookbook-settings]: ../../../django-graphene-filters/examples/cookbook/cookbook/settings.py
[upstream-debug-init]: ../../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/__init__.py
[upstream-debug-middleware]: ../../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/middleware.py
[upstream-debug-types]: ../../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/types.py
[upstream-exception-formating]: ../../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/exception/formating.py
[upstream-exception-types]: ../../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/exception/types.py
[upstream-sql-tracking]: ../../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/sql/tracking.py
[upstream-sql-types]: ../../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/sql/types.py
[upstream-strawberry-extension-isolation]: https://github.com/strawberry-graphql/strawberry/issues/4369
