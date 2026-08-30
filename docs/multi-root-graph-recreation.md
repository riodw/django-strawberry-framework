# Multi-root graph dashboard: the reproduction context

## Purpose

This doc preserves the **demonstration context** for the graph-shaped
multi-root dashboard problem that drove the two graph foundation cards. It
records the failing shape, how to recreate it against the existing fakeshop
project, and the invariants a fix has to satisfy.

It is **not** the acceptance surface. The normative reproductions live in the
two specs' test plans:

- [`spec-058`][spec-058] (card `TODO-BETA-058-0.1.1`) — the graph substrate:
  reproductions R2–R6 and R9.
- [`spec-068`][spec-068] (card `TODO-BETA-068-0.1.6`) — structural templates
  and nested sidecar batching: reproductions R1, R7, R8, R10, plus the R3
  filtered-connection arm `spec-058` pins as characterized-only.

R11 (an optional PostgreSQL repeatable-read snapshot policy) is non-gating and
unscheduled. R12 was consumer-repository work and is closed there.

Class and function names below that do not resolve to a current source symbol
are **design vocabulary, not shipped API**. Where current behavior is named, it
is named by an existing symbol.

## The problem shape

One dashboard operation selects **five interval-scoped, model-backed
connection roots** whose subtrees traverse overlapping relation paths under
per-viewer visibility. The roots share one request scope and one permission
audience, then expose their natural nested relations.

The originating case replaced a REST endpoint that flattened five model
families into a single denormalized response. The load-bearing correction —
and the reason this doc exists rather than a "support UNION roots" card — is
that the GraphQL replacement is **not** one model pretending to be a
heterogeneous UNION. A model-rooted architecture is the right starting point;
what was missing was operation-level cooperation, graph-shaped visibility,
row-preserving predicates, computed relation dependencies, nested batching, and
optimizer cache granularity.

### Canonical shape decision

The canonical shape is **five model-backed connection fields beneath a single
non-model container field**. The container is canonical because resolving it is
the natural operation boundary for:

- normalizing the interval and other shared input;
- computing the audience once;
- validating an explicitly targeted subject once;
- publishing immutable scope data to the five child resolvers.

It also gives one unambiguous owner for scope-validation errors, so an invalid
scope fails once at the container rather than five times with potentially
divergent behavior.

Flat sibling fields directly on `Query` remain a supported alternative. They
are not wrong, but choosing them changes where shared scope is normalized and
validated, which field owns a scope-level error and whether siblings still
execute, the response paths used by optimizer root identity and explain keys,
and whether partial execution can produce roots resolved under differently
derived scopes.

**Framework work must not assume the container exists.** Both shapes must work
through the same operation-scoped dependency mechanism, and neither is a
prerequisite for root-subtree plan caching.

### Shared input, per-model adapters

The consumer-facing scope is model-independent — one normalized input object —
while each root owns a typed adapter that translates common semantics instead
of sharing fragile ORM path strings. Three properties are required of any such
adapter API:

1. the request input is normalized once;
2. model paths are validated at definition / finalization time;
3. request values bind only at execution time and never enter a cross-request
   structural plan.

The interval predicate every root re-implements is carded separately as
[`interval_overlap_filter_primitive`][backlog-interval-overlap] — a
FilterSet-layer concern, not substrate.

### Root cardinality

Each connection retains model identity: one edge per root row of that model.
Selecting nested members must not multiply root edges. A client that genuinely
needs one row per (root, member) pair wants a separate connection over the
membership model, not a multiplied parent.

## Required invariants

### Authorization

1. A hidden root never appears.
2. A visible root cannot qualify through a hidden related row.
3. A visible root cannot expose hidden children through a selected edge.
4. Conditions declared as same-related-row constraints must be satisfied by
   **one** related row, not by siblings.
5. Exact type identity is preserved when a relation path re-enters a model
   that has primary and secondary GraphQL types.
6. Cached audience and permission decisions never cross requests, tenants,
   database aliases, or viewer identities.
7. Search, filter, ordering, aggregate, and field-read gates compose by
   intersection; none implies another.

### Cardinality and pagination

1. Framework-generated visibility and search predicates preserve outer row
   multiplicity.
2. A to-many authorization arm compiles to a correlated predicate, not an
   outer fan-out plus `DISTINCT`.
3. `totalCount` counts root identities.
4. Nested window counts and row numbers are used only when the child query is
   proven to preserve one SQL row per child identity.
5. Deterministic ordering ends in a unique value.
6. Page flags and cursors derive from root rows, not multiplied join rows.

### Query growth

For a fixed selection, moving from one parent to one hundred parents must not
add per-parent queries. Query count may grow with selected root connections,
whether each root selects `totalCount`, selected computed dependency families,
and distinct nested aliases carrying different arguments. It must not grow with
returned parent rows.

### Cache safety

1. Structural cache entries contain no request user, tenant, audience,
   queryset, database alias, router answer, or argument value.
2. An unrelated sibling selection, alias, directive, or pagination variable
   does not invalidate another root's structural template.
3. Request-bound visibility is attached **after** a structural cache hit.
4. Explain data records every root plan; it is not last-wins.

## Recreating it in fakeshop

Most of the failures reproduce without new models.

### Topology mapping

```text
Schedule root identity        -> Book / Periodical / Product models
Nested participants           -> Book.loans -> Loan.patron
Group-like to-many search     -> Book.genres
Root-model re-entry           -> Loan.book -> Book.loans -> Loan
Custom child visibility       -> IssueType.get_queryset
Nested paginated children     -> Periodical.issuesConnection
Five sibling model roots      -> Category, Item, Property, Entry, Periodical
```

### Required fixture capabilities

1. A Loan visibility hook that hides rows marked by a stable flag for
   non-staff.
2. A Book computed `borrowers` field, once `FieldSet` lands.
3. A five-root dashboard query (below).
4. An Issue child queryset that can deliberately introduce a multiplying
   sibling join, for row-identity tests.
5. A counter-backed operation dependency.

The first four need no new model. Prefer settings-gated or dedicated test types
where changing a permanent public type would disturb unrelated examples. If an
operation dependency needs tenant identity, use the existing request user plus
a test-local immutable key.

### The five-root operation

```graphql
query Dashboard($includeEntries: Boolean!, $issueFirst: Int!) {
  allCategories(
    first: 5
  ) {
    edges {
      node {
        id
        name
      }
    }
  }
  allItems(
    first: 5
  ) {
    edges {
      node {
        id
        name
      }
    }
  }
  allProperties(
    first: 5
  ) {
    edges {
      node {
        id
        name
      }
    }
  }
  allEntries(
    first: 5
  ) @include(if: $includeEntries) {
    edges {
      node {
        id
        value
      }
    }
  }
  allLibraryPeriodicalsConnection(
    first: 5
  ) {
    edges {
      node {
        id
        issuesConnection(
          first: $issueFirst
        ) {
          edges {
            node {
              id
              title
            }
          }
        }
      }
    }
  }
}
```

Four runs demonstrate the cache-granularity failure:

1. `includeEntries=true`, `issueFirst=1`;
2. `includeEntries=false`, `issueFirst=1`;
3. the same Category subtree under a different response alias;
4. the same Category subtree in a document carrying an unrelated sixth root.

Under whole-operation cache keys every run misses for every root. The target
asserts a structural hit for each unchanged subtree and a miss only for the
subtree that actually changed.

### Test placement

Consumer-visible GraphQL behavior belongs in `examples/fakeshop/test_query/`.
Package mechanics belong under `tests/` beside the subsystem they exercise
(`tests/optimizer/`, `tests/filters/`, `tests/permissions/`, and — with the
substrate — `tests/graph/`). PostgreSQL plan artifacts belong in a standing doc
only when they record repeatable fixture shape, versions, indexes, and complete
before/after SQL.

## Expected query bounds

With every root selected, every `totalCount` selected, and the nested fields in
the operation above:

- one operation dependency computation for the shared audience;
- at most one count and one page statement per root, unless the selected
  strategy combines them;
- a fixed prefetch family per selected nested relation.

The exact constant depends on selected fields and backend strategy. The
invariant is:

```text
queries(page size 1) == queries(page size 100)
```

for the same selection and a data-independent authorization path.

### Query-count matrix

Every shape runs with one and one hundred parents:

| Shape | Allowed growth |
|---|---|
| Five root pages without counts | O(selected roots) |
| Five root pages with counts | O(selected roots) |
| Computed member field over related rows | O(selected dependency families) |
| One nested alias | O(1) child batches |
| Two divergent nested aliases | O(2) child batches |
| Same alias over 100 parents | no parent-count growth |
| Shared audience over five roots | one computation |

**Growth classes alone are not a sufficient gate.** Parent-count equality is
satisfied by an implementation that consistently issues far more queries than
necessary, so every shape also pins an exact expected integer **per backend**,
derived from a measured baseline and recorded in the test. A change to one of
those integers is a deliberate reviewable change, never a threshold to relax.
Do not pin one universal count across SQLite and PostgreSQL where backend
strategy legitimately differs; pin the backend-specific constant, the
one-versus-one-hundred equality, and the SQL/cardinality invariants.

## PostgreSQL profiling

A stress fixture worth building once the architecture is prototyped: 20,000
roots across five root models; 20 child memberships per graph-heavy root;
multiple matching children per qualifying parent; sparse direct matches; sparse
audience grants; and enough shared parent groupings to expose same-related-row
errors. Use `bulk_create()` for rows and through models — not `.save()` or
`.add()` in large loops.

Record alongside any measurement: root count per model; average and maximum
child rows; the share of roots visible per audience arm; matching children per
root; selected page sizes; aliases and sidecar arguments; PostgreSQL / Django /
DSF versions; indexes; and warm-versus-cold cache status.

Capture plans with `queryset.explain(analyze=True, buffers=True,
format="json")` and compare: outer rows emitted before pagination; rows removed
by filters; join loops over through tables; `Sort` / `Unique` /
`HashAggregate` / distinct-wrapper nodes; semi-join versus correlated `EXISTS`
behavior; window partition rows; the count plan; the page plan; shared and temp
blocks; and planning versus execution time.

Do not add wall-clock percentage gates to the normal test suite. Gate
structural invariants and keep repeatable explain artifacts as performance
evidence.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[backlog-interval-overlap]: ../BACKLOG.md#interval_overlap_filter_primitive

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-058]: SPECS/spec-058-graph_substrate-0_1_1.md
[spec-068]: SPECS/spec-068-structural_templates-0_1_6.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
