# Rationale: spec-004 — Optimizer beyond strawberry-graphql-django (deliberation, rejected alternatives)

Deliberative companion to [`spec-004-optimizer_beyond-0_0_3.md`][spec-004]. The spec is the
contract; this file records what each slice buys and why it is shaped as it is. Entries are keyed to
the slice headings under [The eight improvements][spec-004-improvements].

## What the eight slices buy

Bears on [Problem statement][spec-004-problem].

strawberry-graphql-django re-walks the selection tree on every request, joins a forward FK even when
only the target's id is selected, and leaves N+1 detection to SQL logs. The slices close those gaps
(B1, B2, B3), make the optimizer observable and configurable the DRF way (B4, B5), audit the schema
at build time (B6), stop rebuilding field metadata per walk (B7), and stop stacking the optimizer's
directives on top of a consumer's own (B8).

## Build order

Bears on [The eight improvements][spec-004-improvements].

The slices build in the dependency order each slice's `**Depends on.**` paragraph states: B5 first,
because B2's elisions and B3's sentinel ride on its stash; B1 and B7 next, removing per-request
introspection; B3 and B4 on a well-exercised walker; B2 after resolvers, projection, visibility, field
metadata, strictness, and hints; B6 after hints; B8 last, because it reconciles a finished plan
against the consumer's queryset. The dependencies themselves are contract and live in the spec.

## B1 — AST-cached plans

- **The printed operation, not a hash.** A hash admits a collision, and a collision here serves one
  document's plan to a structurally different document with no failure a test can catch. Storing the
  printed text removes the class; the longer key is memoized per document.
- **Five key components.** The model separates root fields over different models; the root path and
  the origin type close the same collision one level further (two root fields over one model, a
  primary and a secondary type over one model).
- **Only selection-affecting variables.** Keying on every variable explodes the cache (ten filter
  variables, 1024 entries for one shape). Collection over-collects by name, because a duplicate entry
  is the cost of over-collecting and a wrong plan the cost of under-collecting; values are kept as
  `(name, value)` pairs because a bare name cannot tell two executions apart.
- **Why the cache is bound to the extension instance.** Strawberry instantiates any `extensions=`
  entry that is not already an extension instance per request, so a bare class or a constructing
  lambda starts every request with a cold cache, and a bare instance draws Strawberry's deprecation
  warning. A module-level singleton wrapped in a factory hands back one shared instance per request,
  which [`spec-029`][spec-029] Decision 3 owns.
- **A hand-rolled LRU, not `functools.lru_cache`.** The decorator caches a function, and this cache
  belongs to an instance; it also evicts one entry at a time, where this cache drops a quarter per
  sweep so eviction cost amortizes.

## B2 — Forward-FK-id elision

- **Why each guard exists.** A custom `get_queryset` on the target needs the join to filter; a custom
  id resolver may read columns the stub does not carry; a `to_field` FK stores a non-pk value; a
  reverse OneToOne has no source column; one column cannot carry a composite key.
- **A branch-sensitive key, not a field name.** `category { id }` in one branch and
  `category { id name }` in another must elide in the first only, which a flat field-name flag cannot
  express.
- **Loud fallback.** When a consumer projection defers the FK column the stub cannot be built, and the
  resolver falls back visibly to strictness rather than lazy-loading silently.

## B3 — N+1 detection in dev mode

- **A three-valued `strictness` literal, not a boolean.** A boolean `strict=True` cannot carry the
  third level (`"raise"`) without a deprecation cycle.
- **The resolver rebuilds its path from `info.path`.** A stashed `(parent_type, field_name) -> path`
  mapping would trade bookkeeping for lookup speed; it is not needed, because the forward resolver
  walks `info.path` once per row and shares that walk between the B2 elision test and the B3
  lazy-load test.
- **Already-loaded relations are skipped.** A relation the consumer preloaded is not an N+1, so the
  check probes whether the access would actually load before reporting it.

## B4 — `Meta.optimizer_hints`

- **Hints live on `Meta`.** strawberry-graphql-django's hints are per-field decorator arguments, which
  suit its API and not this package's.
- **A typed `OptimizerHint`.** Raw strings, bare `Prefetch` objects, and dicts sharing one value
  position read awkwardly and need ad hoc validation; one frozen class gives one shape and one
  validation path.
- **Positive overrides, not only opt-out.** A boolean "disable optimization" marker is strictly weaker
  than a hint that can force a strategy or supply a specific `Prefetch`.
- **No dispatch order to specify.** `OptimizerHint` rejects incompatible flag combinations at
  construction, so no hint can match two branches and no precedence between them is observable.

## B5 — Plan introspection via context

The optimizer's decisions are observable rather than magic: a consumer or test reads the published
plan instead of reverse-engineering SQL logs. The `dst_` prefix avoids collision with consumer keys.
The set-valued keys accumulate because a nested-connection fallback stashes a second batch in one
execution, and the whole family is cleared at the start of each execution so a reused
`context_value` cannot carry one operation's elisions into the next.

## B6 — Schema-build-time optimization audit

An unregistered relation target lazy-loads on every access; the audit surfaces it at startup instead
of in production traffic. Walking only schema-reachable types avoids false positives from types
registered but never exposed, the interface arm keeps an interface-only type from being skipped, and
the `(model, field)` dedupe keeps a relation exposed by two types over one model from warning twice.

## B7 — Precomputed optimizer field metadata

Without the map, every walk rebuilds a field dictionary from `model._meta.get_fields()`. Building it
once per type at class creation removes that per-request introspection, and keeping it on the
registered definition (with no class-attribute mirror, [`spec-016`][spec-016]) gives it one lifetime.

## B8 — Queryset optimization diffing

- **Why reconcile at all.** Django merges a duplicate `select_related`, but stacking the optimizer's
  directive on a consumer's masks the consumer's intentional optimization and clutters debug output.
  A consumer projection that defers a column on a planned join path also makes Django refuse the
  join, so dropping that path avoids a `FieldError`.
- **A delta plan plus a queryset.** Reconciliation can upgrade a consumer's plain string lookup to the
  optimizer's `Prefetch`, which rewrites the queryset side; a plan-only delta cannot express that.
- **Copy, never mutate.** The same plan object is served from B1's cache across requests, so an
  in-place edit would corrupt every later request.
- **Wildcard `select_related()` is no overlap.** Django's wildcard follows only non-null forward FKs,
  so treating it as covering the plan would drop nullable joins the plan needs.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-004]: ../spec-004-optimizer_beyond-0_0_3.md
[spec-004-improvements]: ../spec-004-optimizer_beyond-0_0_3.md#the-eight-improvements
[spec-004-problem]: ../spec-004-optimizer_beyond-0_0_3.md#problem-statement
[spec-016]: ../spec-016-fieldmeta_consolidation-0_0_6.md
[spec-029]: ../spec-029-consumer_dx_cleanup-0_0_9.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
