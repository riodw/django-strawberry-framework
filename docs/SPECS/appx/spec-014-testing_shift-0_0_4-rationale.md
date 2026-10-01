# Rationale: spec-014 — IRL API test shift (deliberation, rejected alternatives)

Deliberative companion to [`spec-014-testing_shift-0_0_4.md`][spec-014]. The spec is the contract;
this file records why the test-placement split is drawn where it is. The spec has no numbered
Decisions, so each entry is keyed to a spec section.

## Why the split exists

Bears on [Problem statement][spec-014-problem].

A test-only fixture model loaded through the example project's settings entangles package-test
substrate with the example project, and an unmanaged fixture model has no table: its relation edges
can be asserted as annotation shape but never resolved through a query. A real example app with
migrated models and a real schema removes both problems.

- **Replace package tests wholesale with live tests.** Rejected: the split becomes sharper, not
  absent. Intentionally broken app states (invalid `Meta`, unresolved targets, registry failure
  atomicity) are not forced through `/graphql/` to reach internal failure paths.

## Why a separate `library` app

Bears on [Shipped outcome][spec-014-shipped-outcome] and [Settled decisions][spec-014-settled].

The app exists to exercise framework behavior through real models without polluting the
product-catalog example, so it is its own app rather than more models on `products`. Its first seven
models map one relationship shape each: `Branch`/`Shelf` is the FK pair, `Branch → Shelf → Book →
Loan → Patron` the multi-hop graph, `Patron`/`MembershipCard` the OneToOne pair, `Book`/`Genre` the
M2M pair, and `Book` carries the choice and nullable scalar fields. Later surfaces follow the same
rule: `scalars`, `accounts`, `kanban`, and `glossary` are separate apps for separate surfaces.

## Why the library schema declares types out of dependency order

Bears on [Settled decisions][spec-014-settled].

The example schema must prove definition-order-independent finalization at real app-import time,
which only a module declaring types out of dependency order can do. The order is therefore stated
as a contract in the spec rather than left to class docstrings: an editor who tidies the module reads
the order as an accident, and the coverage retires with no test failing.

## Why the live tier rebuilds project schema state

Bears on [Live HTTP coverage][spec-014-live-http].

Package tests clear the global registry for their own isolation, so a live suite that trusted a
cached `config.schema` would build against a registry another module emptied, failing
order-dependently (`DuplicatedTypeName`, `LazyType` `KeyError`). The rebuild is single-sited in
`examples/fakeshop/schema_reload.py::reload_all_project_schemas` so every contributing app schema
module is reloaded from one list, and the per-test guard in `examples/fakeshop/test_query/conftest.py`
rebuilds only the cheap schema and URLconf shell, falling back to the full rebuild only when a test
mutated registrations.

- **Describe the fixture generically ("an autouse fixture rebuilds schema state").** Rejected: the
  mechanism is the contract. The single list is what stops a new app being added to one reload list
  and not another, and the identity fingerprint is what makes the cheap per-test path safe.

## Why the forward FK is stated as a two-query `Prefetch`

Bears on [Live HTTP coverage][spec-014-live-http].

`Book.shelf` is planned as `select_related`, but `ShelfType` declares a `get_queryset` hook, and a
join would surface shelf rows the hook excludes. The optimizer therefore executes the edge as a
visibility-scoped `Prefetch`, and the live test pins the two-query shape. Stating only "forward FK
traversal" would be unfalsifiable; stating a join would be false.

## Why some coverage stays package-level

Bears on [Package-level tests that intentionally remain][spec-014-package-level].

Registry lifecycle, finalizer atomicity, and similar tests validate state transitions directly, and
no wire response can observe those transitions. That reason, not the list, decides whether a new
internal belongs package-level: anything reachable from a real query belongs in the live tier.

- **Manual relation overrides are layered.** Package tests pin Strawberry's resolver-attachment
  shapes so an upstream change fails early; the live tier pins the consumer-visible contract through
  response data.
- **Query-count assertions use `CaptureQueriesContext(connection)` and broad SQL shape.** Counting
  only database queries keeps request-stack changes (middleware, authentication, view behavior) out
  of the assertion, and broad shape survives SQL text differences that full-string comparisons do
  not.
- **The plan stays a context entry.** The optimizer publishes it for introspection on the context;
  surfacing it in every HTTP response would add a debug surface to the wire contract.

## Why Layer-3 features are routed, not described

Bears on [Optimizer extension behavior across the tiers][spec-014-optimizer-tiers].

Filters, orders, permissions, Relay nodes, `DjangoConnectionField`, fieldsets, and aggregates each
have their own owner. The spec routes a reader to "its own spec or card" without naming ids, because
card ids move under board renumbering and a copied id is a second source that drifts.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-014]: ../spec-014-testing_shift-0_0_4.md
[spec-014-live-http]: ../spec-014-testing_shift-0_0_4.md#live-http-coverage
[spec-014-optimizer-tiers]: ../spec-014-testing_shift-0_0_4.md#optimizer-extension-behavior-across-the-tiers
[spec-014-package-level]: ../spec-014-testing_shift-0_0_4.md#package-level-tests-that-intentionally-remain
[spec-014-problem]: ../spec-014-testing_shift-0_0_4.md#problem-statement
[spec-014-settled]: ../spec-014-testing_shift-0_0_4.md#settled-decisions
[spec-014-shipped-outcome]: ../spec-014-testing_shift-0_0_4.md#shipped-outcome

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
