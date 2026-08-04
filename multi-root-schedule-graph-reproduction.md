# Multi-root schedule graph optimization: findings, reproduction, and implementation guide

## Purpose

This guide records the complete architecture audit prompted by a production schedule
calendar, recreates the important query and permission shapes in the fakeshop project, and
defines the framework work required to make Django Strawberry Framework (DSF) plug-and-play
for a graph-shaped, multi-model dashboard.

The production calendar currently flattens five model families into one REST response:

- events;
- shift assignments;
- curriculum sessions;
- rotation schedules;
- approved time-off requests.

The GraphQL replacement is **not** one model pretending to be that heterogeneous UNION and
is **not** a request to teach DSF to reproduce the raw UNION. The intended replacement is
one GraphQL operation selecting five separate, concrete, model-backed roots or connections.
They share one request scope and one permission audience, then expose their natural nested
relations.

That correction is load-bearing. DSF's model-rooted architecture is the right starting
point. The remaining problems are operation-level cooperation, graph-shaped visibility,
row-preserving predicates, computed relation dependencies, nested batching, and optimizer
cache granularity.

The guide has four audiences:

1. A DSF maintainer deciding which framework abstractions need to land before 1.0.
2. A card author amending the FieldSet, search, aggregation, explain, or adversarial-test
   specifications.
3. A Medtrics developer recreating the calendar as GraphQL.
4. A reviewer who needs runnable failure cases and objective acceptance criteria rather
   than an architectural assertion alone.

Proposed class and function names in this document are design vocabulary, not shipped API.
Current behavior is always identified by an existing source symbol.

The five-root `scheduleCalendar` operation, its scope input, graph-planning classes, edge
scopes, computed fields, and operation explain map are proposed target behavior. They are
not shipped DSF or fakeshop APIs. Existing fakeshop roots and relations are used as
reproduction fixtures; the schedule-shaped dashboard itself is a future acceptance
activation.

## Executive conclusion

DSF can represent the target API cleanly:

```text
scheduleCalendar(scope)
├── events
├── shifts
├── sessions
├── rotations
└── offRequests
```

Each child is a real Django model connection. Shared scope is computed once, each root
translates it to model-specific ORM paths, and clients select only the roots and nested
fields they need.

DSF is not yet seamless for this shape. A correct implementation currently requires the
consumer to hand-build too much infrastructure:

- operation-scoped audience caching;
- five visibility adapters;
- custom correlated `EXISTS` predicates for graph permissions;
- explicit same-related-row authorization;
- edge-specific child scoping;
- eager-loading plans for computed participants and invitees;
- manual avoidance of filtered nested-connection N+1 fallbacks;
- cache workarounds for request-bound `get_queryset` hooks.

If every non-Done KANBAN card lands exactly as currently written, search and computed scalar
fields improve substantially, but the complete schedule graph remains unowned. The most
important strategic change is to promote card 054's graph path, exact-owner, per-hop
visibility, correlated `EXISTS`, and same-row machinery into a framework-wide graph-planning
substrate before FieldSet, search, and AggregateSet freeze separate abstractions.

Two foundational work items are recommended:

1. A graph policy and dependency planning card before FieldSet.
2. An operation structural planning and nested batching card before optimizer explain mode
   and the 1.0 API freeze.

After those foundations, the target has a bounded query shape: root work grows with selected
root types, selected computed dependencies, and distinct nested aliases, not with the number
of parent rows.

## Alignment with the 1.0.0 vision

Everything proposed here must fold into the [`GOAL.md`][goal] north star — the DRF-shaped,
`class Meta`-driven Django integration for Strawberry — without bending it. Four constraints
keep this guide inside that mission:

1. The consumer surface stays Meta-declared. `GraphPathPlan`, `PredicatePlan`, `EdgeScope`,
   and `FieldDependencyPlan` are the normalized internal planning vocabulary that Meta
   declarations compile into, exactly as `Meta.depends_on` column tuples normalize to
   `FieldDependencyPlan(columns=...)`. Whatever public declaration shape ships for edge
   scopes and graph predicates, it must arrive as `class Meta` keys or sidecar `Set`
   classes consistent with `filterset_class` / `orderset_class` / `fields_class` — never
   stacked decorators on consumer-facing classes and never a parallel imperative
   registration API.
2. The astronomy six-file shape in [`GOAL.md`][goal] is unchanged. The substrate makes the
   graph-shaped dashboard achievable with the same shape: models, one `DjangoType` schema
   file, and declarative sidecars. GOAL.md's failure criterion — users routinely
   hand-building the machinery the package should generate — is precisely the current
   state listed in the executive conclusion; the substrate exists to remove that
   hand-building, not to add a second framework beside the Meta surface.
3. No ORM abstraction layer. Predicate plans are selections over consumer-shaped querysets
   (the multiset contract card 054 already anchors to [`GOAL.md`][goal]): they never
   multiply rows, never collapse consumer duplicates, never hide Django querysets behind a
   new query language.
4. The two recommended cards are pre-`1.0.0` Beta-milestone foundation work in service of
   the five Layer-3 Meta keys the 1.0.0 contract already promises. They change how cards
   053, 054, and 056 are built — one shared substrate instead of three private ones — not
   what [`GOAL.md`][goal]'s success criteria promise. The "Defer graph foundations until
   after 1.0" entry under rejected approaches is the inverse statement: landing them after
   the API freeze would force incompatible public concepts into the stable surface.

## Adoption precondition: dependency compatibility

The audited consumer cannot install current DSF without a framework upgrade:

- DSF declares Django 5.2 or newer and django-filter 25.2 or newer in
  `pyproject.toml #"Django>=5.2"`.
- The consumer declares Django 4.2.25 and django-filter 24.3 in
  `medtrics/pyproject.toml #"django==4.2.25"`.

This is independent from the graph design. It is an adoption blocker, not an optimizer
defect, and should remain visible in any implementation estimate.

Required decision before the consumer recreation is scheduled: either the consumer upgrades
to the supported Django/django-filter floor, or DSF deliberately widens its supported range
with the compatibility testing that implies. The framework work in this guide can proceed
independently, but no end-to-end adoption date can be promised until that decision is made
and owned. Treat it as separate work from the graph substrate, not as a phase inside it.

## Source topology

### Current REST projection

The current endpoint builds one UNION in
`medtrics/src/apps/api/schedules/viewsets.py::SchedulesViewSet._build_schedule_query`.
Every branch projects the same flattened row vocabulary:

```text
id
program / program_name
type
schedule
display_name
start_date / end_date
user identity and profile fields
css_color
venue
```

The flattened row identity is wider than the schedule entity. One schedule may emit one row
per user and per program. The REST paginator therefore needs a total order that ends in:

```text
type, id, user_id, program
```

GraphQL should not preserve this accidental storage-neutral row as its primary object model.
It should preserve the natural identity of each root model and express users, programs, and
venues as selected relations.

### Permission audience

`medtrics/src/apps/schedules/services.py::ScheduleAudience` contains independent widening
dimensions:

- unrestricted access;
- rotation IDs;
- `(block_id, rotation_id)` director grants;
- block-program IDs;
- shift-program IDs;
- curriculum-program IDs;
- event-program IDs;
- always-visible user IDs, including self.

`medtrics/src/apps/schedules/services.py::get_schedule_audience` derives those
request-scoped ID sets from administrators, supervisors, directors, program schedulers,
custom permissions, curriculum permissions, calendar coordinators, and role grants.

The current `ScheduleAudience` dataclass is mutable: it is an ordinary `@dataclass` whose
dimensions are mutable `set` fields populated incrementally during derivation. That shape is
appropriate for the builder, but it must not be the value that is memoized, shared across
roots, or used in a cache key. The execution value defined later in this guide is a frozen
snapshot whose dimensions are `frozenset`s, converted once at the end of derivation. Wrapping
a mutable audience in a frozen outer dataclass does not make it immutable and must not be
treated as sufficient.

Each root consumes a different projection of the same audience:

| Root | Model | Program or user visibility |
|---|---|---|
| Events | `Event` with `Attendance` children | event-program grants or self attendance |
| Shifts | `AssignDateToShift` | shift-program grants or self assignee |
| Sessions | `SessionSchedule` | block/curriculum program grants or self participant |
| Rotations | `UserSchedule` | rotation, exact block-and-rotation, block-program, or self |
| Off requests | `AccountRequest` | self through account users; no program widening |

The exact `(block_id, rotation_id)` pair is a security invariant. A block belongs to a
program schedule and may contain many rotations. Checking `block_id` and `rotation_id` in
independent predicates can combine grants or rows that were never authorized together.

### Graph-shaped fields

Several response values are not ordinary columns or one-hop relations:

- `SessionSchedule.get_users_list()` combines `individuals` with users reached through
  `groups -> group_user -> user`.
- `SessionSchedule.get_user_schedules()` is a separate classmethod that builds filtered
  `SessionSchedule` querysets; it is not the participant assembler.
- `Event.get_users()` combines roles, individual users, speakers, groups, group members,
  programs, a date-sensitive affiliation status, and institution-wide behavior.
- rotation display values combine rotation, dates, and user data.
- `AccountRequest` has no equivalent participant helper; its production UNION branch reaches
  users through `Account.users`, while the flattened program is reached through each user's
  primary affiliation.

These are data-dependency graphs. Treating them as arbitrary Python resolvers hides their
query requirements from the optimizer and produces query growth proportional to the parent
row count.

## Target GraphQL architecture

### One operation, five model-backed roots

A representative operation is:

```graphql
query ScheduleCalendar($scope: ScheduleScopeInput!) {
  scheduleCalendar(
    scope: $scope
  ) {
    events(
      first: 50
    ) {
      totalCount
      edges {
        node {
          id
          title
          startDatetime
          endDatetime
          programs {
            id
            name
          }
          attendees {
            user {
              id
              firstName
              lastName
            }
          }
        }
      }
    }
    shifts(
      first: 50
    ) {
      totalCount
      edges {
        node {
          id
          start
          end
          displayName
          assignees {
            id
            firstName
            lastName
          }
        }
      }
    }
    sessions(
      first: 50
    ) {
      totalCount
      edges {
        node {
          id
          start
          end
          displayName
          participants {
            id
            firstName
            lastName
          }
          venue {
            id
            name
          }
        }
      }
    }
    rotations(
      first: 50
    ) {
      totalCount
      edges {
        node {
          id
          startDate
          endDate
          user {
            id
            firstName
            lastName
          }
          rotation {
            id
            name
          }
        }
      }
    }
    offRequests(
      first: 50
    ) {
      totalCount
      edges {
        node {
          id
          specificDate
          endDate
          category {
            id
            name
          }
          users {
            id
            firstName
            lastName
          }
        }
      }
    }
  }
}
```

#### Canonical shape decision

This guide uses one canonical shape: **five model-backed connection fields beneath a single
non-model `scheduleCalendar` container**. "Five roots" throughout this document means these
five model-backed connections, whether or not they sit under the container.

The container is canonical because resolving it is the natural operation boundary for:

- normalizing the interval and other common input;
- computing the audience once;
- validating an explicitly targeted user once;
- publishing immutable scope data to the five child resolvers.

It also gives one unambiguous owner for scope validation errors, so an invalid scope fails
once at the container rather than five times with potentially divergent behavior.

Flat sibling fields directly on `Query` remain a supported alternative, but they are not the
shape this guide specifies against. Choosing flat fields changes:

- where shared scope is normalized and validated;
- which field owns a scope-level error and whether siblings still execute;
- the response paths used by optimizer root identity and explain keys;
- whether partial execution can produce roots resolved under differently derived scopes.

Both shapes must work through the same operation-scoped dependency mechanism, and neither is
a prerequisite for root-subtree plan caching. Framework work must not assume the container
exists; consumer specifications and acceptance fixtures in this guide assume it does.

### Shared input, model-specific adapters

The consumer-facing scope should be model-independent:

```python
@strawberry.input
class ScheduleScopeInput:
    start: datetime
    end: datetime
    program_id: strawberry.ID | None = None
    target_user_id: strawberry.ID | None = None
    site_id: strawberry.ID | None = None
    rotation_id: strawberry.ID | None = None
    search: str | None = None
```

Each root owns a typed adapter. The adapter translates common semantics rather than sharing
fragile ORM strings:

```python
class EventScheduleScope:
    interval = IntervalPath(start="start_datetime", end="end_datetime", nullable_end=True)
    program = "programs__id"
    search = ("title",)


class RotationScheduleScope:
    interval = IntervalPath(start="start_date", end="end_date")
    program = "block__program_schedule__program_id"
    user = "user_id"
    search = ("rotation__name",)
```

The exact API is open, but three properties are required:

1. The request input is normalized once.
2. Model paths are validated at definition/finalization time.
3. Request values bind only at execution time and never enter a cross-request structural
   plan.

### Root cardinality

Each connection must retain model identity:

- one Event edge per Event;
- one Shift edge per `AssignDateToShift`;
- one Session edge per `SessionSchedule`;
- one Rotation edge per `UserSchedule`;
- one Off edge per `AccountRequest`.

Selecting nested users must not multiply root edges. If a client explicitly needs one row
per schedule-user pair, that is a separate connection over the appropriate membership model,
such as Attendance, not accidental fan-out in the Event connection.

## Required invariants

### Authorization

1. A hidden root never appears.
2. A visible root cannot qualify through a hidden related row.
3. A visible root cannot expose hidden children through a selected edge.
4. Conditions declared as same-related-row constraints must be satisfied by one related
   row, not by siblings.
5. Exact type identity is preserved when a relation path re-enters a model that has primary
   and secondary GraphQL types.
6. Cached audience and permission decisions never cross requests, tenants, database aliases,
   or viewer identities.
7. Search, filter, ordering, aggregate, and field-read gates compose by intersection; none
   implies another.

### Cardinality and pagination

1. Framework-generated visibility and search predicates preserve outer row multiplicity.
2. A to-many authorization arm compiles to a correlated predicate, not an outer fan-out plus
   `DISTINCT`.
3. `totalCount` counts root identities.
4. Nested window counts and row numbers are used only when the child query is proven to
   preserve one SQL row per child identity.
5. Deterministic ordering ends in a unique value.
6. Page flags and cursors are derived from root rows, not multiplied join rows.

### Query growth

For a fixed selection, moving from one parent to one hundred parents must not add
per-parent queries. Query count may grow with:

- selected root connections;
- whether each root selects `totalCount`;
- selected computed dependency families;
- distinct nested aliases carrying different arguments.

It must not grow with returned parent rows.

### Cache safety

1. Structural cache entries contain no request user, tenant, audience, queryset, database
   alias, router answer, or argument value.
2. An unrelated sibling selection, alias, directive, or pagination variable does not
   invalidate another root's structural template.
3. Request-bound visibility is attached after a structural cache hit.
4. Explain data records every root plan; it is not last-wins.

## Required product and security decisions

These are consumer-facing contracts, not framework internals. Each one changes schema shape,
authorization tests, or both, so each must be decided and written down before schema work
begins. They are listed here as open decisions with a recommended default, not as settled
behavior.

1. **Unauthorized `targetUserId`.** Choose one contract for the whole operation: a field
   error, a null container, or an empty result set. Recommended default is an explicit
   error, because a silent empty page is indistinguishable from "no schedules" and hides
   authorization mistakes. Whatever is chosen, every root must behave identically; one root
   must never honor the requested target while another silently coerces to self.
2. **Public schedule access.** Define exactly which institution setting or policy enables
   unauthenticated or unscoped access, and what it exposes. State whether it grants root
   visibility only, or also nested user data.
3. **Uniformity of public access across roots.** Decide whether the public policy applies to
   all five model families or only to events. The production SQL branches do not treat every
   family identically, so this must be stated per root rather than assumed global.
4. **Nested-user exposure per edge.** Attendees, assignees, participants, and account users
   are separate edges with separate policies. For each, state which users a given viewer may
   see, and whether the answer depends on the viewer, the scope's target user, or both.
   Recommended default is viewer-based edge scope, with target-user filtering treated as a
   query filter rather than a permission.
5. **Session `speakers`.** Decide whether speakers merge into one `participants` field or
   remain a separate GraphQL field. Merging changes the meaning of an existing production
   helper; keeping them separate preserves it. Recommended default is a separate field, with
   any merged field named distinctly so it cannot be confused with
   `SessionSchedule.get_users_list()`.
6. **Off-request program exposure.** Confirm that program data reached through an account
   user's primary affiliation is intended to be visible, since it is derived rather than
   directly granted.

Until these are resolved, the per-root specifications later in this guide describe ORM shape
and cardinality requirements, not final authorization behavior.

## Current DSF strengths

The audit found important existing foundations that should be reused rather than replaced.

### Strict relation-path classification

`django_strawberry_framework/utils/relations.py` classifies reverse FK, forward and reverse
M2M, generic relations, reverse one-to-one, and multi-level paths. It records the first
row-multiplying hop and the complete relation chain. Card 054 already depends on this strict
classification.

### Row-preserving generated filters

`django_strawberry_framework/optimizer/predicates.py::correlated_inner_root` constructs an
inner queryset over the outer model's `_base_manager`, pins it to the outer database alias,
and correlates it on the primary key.

`django_strawberry_framework/optimizer/predicates.py::attach_exists` attaches the resulting
`Exists` expression under an unselected reserved alias and returns the `Q(alias=True)` branch
to the semantic caller.

`django_strawberry_framework/filters/sets.py::FilterSet._apply_flat_leaves` uses those
primitives for audited framework-generated to-many filter leaves. The outer query has no
framework-introduced membership fan-out and no framework-introduced `DISTINCT`.

The PostgreSQL proof is recorded in
[`docs/row-preserving-predicates-part1-pg-explain.md`][row-preserving-pg].

### Row-preserving `RelatedFilter`

`django_strawberry_framework/filters/sets.py::FilterSet._apply_related_constraints` uses a
parent-primary-key subquery. It is a sibling row-preserving strategy, not a reason to rewrite
either implementation into the other.

### Selection-driven relation loading

`django_strawberry_framework/optimizer/walker.py::plan_optimizations` and
`django_strawberry_framework/optimizer/plans.py::OptimizationPlan.apply` correctly separate
selection loading from predicate meaning. The plan applies:

```text
only -> select_related -> prefetch_related
```

It does not attempt to infer or rewrite arbitrary filter semantics from Django's internal
join tree.

### Supported nested connection batching

For a simple, row-preserving child queryset,
`django_strawberry_framework/optimizer/nested_planner.py::plan_connection_relation` can
build one windowed child query per selected connection response key rather than one query
per parent.

`django_strawberry_framework/optimizer/nested_fetch.py::NestedConnectionRequest` is already
a pluggable strategy boundary. The windowed and PostgreSQL lateral strategies share the same
row-attachment contract described by the
[`connection optimizer specification`][connection-optimizer-spec].

### Visibility and cascade boundaries

Type `get_queryset` hooks are normalized through shared sync/async visibility helpers.
`django_strawberry_framework/permissions.py::apply_cascade_permissions` narrows concrete
forward FK and one-to-one edges through subqueries, with strong validation around custom
target querysets. Its intended security boundary is recorded in the
[`permissions specification`][permissions-spec].

Cascade is intentionally not a general child-collection policy. That limitation is correct
as long as DSF adds a separate edge-policy abstraction rather than silently broadening
cascade semantics.

### Strictness

Optimizer strictness can detect many unplanned relation accesses. This is a valuable
acceptance mechanism. The missing piece is letting computed dependency and contextual edge
plans publish accurate resolver keys only after their plans have actually attached.

## Finding 1: operation dependencies have no framework-owned memo

### Current behavior

The optimizer has per-execution memoization for optimization plans and cache-key parts, but
no public operation-scoped dependency cache for arbitrary immutable policy data.

`ScheduleAudience` can require roughly a dozen permission queries for a role-bearing,
non-admin user. Calling `get_schedule_audience()` from each of five root visibility hooks can
repeat that work roughly five times before loading any schedule rows. Contextual child
visibility can repeat it again.

### Required behavior

Provide an execution-bound API:

```python
audience = get_or_compute(
    info,
    key=(
        "schedule-audience",
        request_user.pk,
        institution.pk,
        queryset.db,
        scope.mode,
    ),
    factory=build_schedule_audience,
)
```

The contract must be:

- installed and cleared at the GraphQL execution boundary;
- safe for sync and async resolvers;
- request-local;
- exception-safe;
- concurrency-safe when sibling async resolvers request the same key;
- capable of caching immutable dataclasses and primitive ID sets;
- documented not to cache evaluated querysets or model instances.

The same substrate can memoize repeated permission gate decisions when their scope key is
explicit. Existing per-FilterSet fired sets remain useful but do not replace operation-wide
dependency reuse.

### Reproduction

Create an operation with five root connections whose type visibility hooks all call one
counter-backed dependency factory. Execute once and assert:

```text
current/manual behavior without consumer memo: 5 calls
target framework behavior:                    1 call
```

Repeat under async sibling execution with a factory that yields once before returning. The
target still calls the factory once and gives every waiter the same immutable result.

Execute a second GraphQL request with a different user and assert a second factory call and a
different result. This prevents a cross-request policy leak.

## Finding 2: plan cache keys are whole-operation-shaped

### Current behavior

`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._build_cache_key`
includes:

- the selected operation's printed AST and reachable fragment definitions;
- relevant directive and nested-pagination variable values from the whole operation;
- target model;
- root response path;
- origin type.

This is safe but unnecessarily coarse for sibling roots.

Examples:

- changing an Off-request `@include` variable invalidates the Event plan;
- changing a nested Session pagination value invalidates the Rotation plan;
- aliasing the Events root differently changes its runtime root path;
- the same root subtree embedded in a larger dashboard operation receives a different
  document key.

Five roots across 32 combinations of five binary directive/pagination choices can occupy
160 cache entries for one logical dashboard. The extension cache is capped at 256 entries
and evicts a quarter when full, so unrelated sibling variation can churn otherwise reusable
plans.

### Required behavior

Cache an immutable `StructuralOptimizationTemplate` by:

- exact owning GraphQL type identity;
- root field/return type identity;
- normalized root-subtree selection fingerprint;
- only the directive and nested-pagination slots referenced inside that subtree;
- strategy/static schema configuration.

Do not key a sibling plan by:

- unrelated operation text;
- unrelated variables;
- the root response alias;
- request-bound visibility;
- a database alias.

Runtime binding should add:

- absolute response paths used by strictness;
- current argument values;
- database alias;
- viewer/tenant visibility;
- `Prefetch` querysets;
- current connection strategy execution details.

### Reproduction

Use the existing fakeshop roots:

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

Run:

1. `includeEntries=true`, `issueFirst=1`;
2. `includeEntries=false`, `issueFirst=1`;
3. the same Category subtree under a different response alias;
4. the same Category subtree in a document with an unrelated sixth root.

Current cache instrumentation should demonstrate avoidable misses. The target asserts a
structural hit for every unchanged subtree and a miss only for the affected subtree.

## Finding 3: request-bound related visibility makes plans uncacheable

### Current behavior

`django_strawberry_framework/optimizer/walker.py::_plan_prefetch_relation` detects a target
type with custom `get_queryset`, builds its child queryset while walking, embeds that
queryset in a `Prefetch`, and sets `OptimizationPlan.cacheable = False`.

That is necessary for safety under the current representation: a queryset built from
`info.context` must not enter a cross-request cache. It is also expensive:

- the same visible User subtree can be planned independently under five roots;
- custom visibility can run at plan-build time for every root;
- the entire parent plan loses cross-request reuse.

The existing per-execution memo helps identical cache keys, but different root paths prevent
the five sibling roots from necessarily sharing one child plan.

### Required behavior

Split:

```text
structural relation template
    relation lookup
    exact target type
    child structural template
    projection
    strictness identities relative to the subtree

request binding
    target get_queryset(info)
    database alias
    contextual edge scope
    concrete Prefetch object
    absolute resolver keys
```

A visibility-bearing relation template should remain cross-request cacheable because it
contains only the instruction to bind a visibility factory, not its request-specific
queryset.

### Reproduction

The existing `IssueType.get_queryset` hook and
`PeriodicalType.issuesConnection` provide the basic fixture. Select the same Issue subtree
under multiple response aliases and inspect:

- current plan `cacheable`;
- number of child-plan walks;
- number of visibility-hook calls;
- cache hits on a second request with the same document.

The target keeps the structural template cacheable, binds the hook per request, and reuses
one request-bound child recipe for identical relation/argument/scope keys.

## Finding 4: root visibility does not scope selected to-many edges

### Current behavior

Root visibility answers whether an Event, Shift, Session, Rotation, or Off request is
visible. It does not answer which children may be returned from:

- Event attendees or invitees;
- Shift assignees;
- Session participants;
- Group members;
- Account users and affiliations.

`apply_cascade_permissions` deliberately walks forward single-valued relations. It does not
filter reverse FK or M2M collections attached to an already-visible parent.

A visible Shift can therefore expose every assignee unless the consumer hand-builds a
scoped `Prefetch`. A visible Event can expose attendees outside the viewer's audience.

### Required behavior

Add contextual, edge-specific scope:

```python
EdgeScope(
    relation="shift_assinee_user",
    queryset_factory=visible_shift_assignees,
    cache_scope=audience.cache_key,
    to_attr="_dst_visible_shift_assignees",
)
```

`shift_assinee_user` is the consumer's actual field name, reproduced faithfully; it is not
a typo in this guide.

The factory receives:

- `info`;
- the normalized operation scope;
- the immutable audience;
- the live database alias;
- the optimizer's selected child structural template.

It returns a lazy child queryset or a typed prefetch recipe. The framework combines the
scope with child projection and nested optimization, attaches through a reserved `to_attr`,
and makes the generated resolver consume only that attribute.

The edge plan must publish strictness resolver keys only after successful attachment.
Planning failure must remain visible; it must not mark an edge planned and then resolve
lazily.

### Reproduction

Use a visible Book with two Loans:

- a visible loan to Patron A;
- a hidden loan to Patron B.

Make the Book visible to the request and hide the second Loan through `LoanType.get_queryset`.
Select:

```graphql
allLibraryBooks {
  id
  loans {
    id
    note
    patron {
      name
    }
  }
}
```

Current root visibility alone returns both loans. The target edge scope returns only Patron
A's loan in a bounded prefetch and does not remove the Book.

Repeat with two Book rows and one hundred Book rows. Query count must be identical.

## Finding 5: custom graph visibility can still create outer fan-out

### Current behavior

The row-preserving predicate primitives are intentionally semantic-free. They do not rewrite
arbitrary consumer `Q` expressions.

A custom visibility hook such as:

```python
queryset.filter(
    Q(programs__id__in=audience.program_ids)
    | Q(individuals__id__in=audience.user_ids)
    | Q(groups__group_user__user_id__in=audience.user_ids)
)
```

creates outer to-many joins. Multiple matching children multiply root rows unless the
consumer adds `DISTINCT`, which retains the fan-out and pushes deduplication into count and
page queries.

The current generated-filter rewrite correctly declines consumer subclasses, method
filters, filter overrides, and other unaudited semantics. That safety boundary should stay.
The missing feature is an explicit public graph predicate API, not a more aggressive
after-the-fact rewrite.

### Required behavior

Provide composable, row-preserving predicate plans:

```python
PredicatePlan.any_of(
    PredicatePlan.direct(Q(owner_id__in=audience.user_ids)),
    PredicatePlan.related(
        "programs",
        Q(id__in=audience.program_ids),
    ),
    PredicatePlan.related(
        "groups__group_user",
        Q(user_id__in=audience.user_ids),
    ),
)
```

Required operators:

- `any_of`;
- `all_of`;
- `not_`;
- direct scalar `Q` branches;
- correlated to-many branches;
- explicit same-related-row groups;
- per-hop visibility composition;
- exact-owner identity for root-model re-entry.

The compiler should reuse `correlated_inner_root` and `attach_exists`. Predicate meaning
remains with the caller; the optimizer provides validated relation planning and
row-preserving attachment.

### Reproduction

Use `Book` as the root:

```python
Book.objects.filter(
    Q(genres__name__icontains="needle")
    | Q(loans__patron__email__icontains="needle")
)
```

Seed one Book with:

- two matching Genres;
- two matching Loans.

The outer queryset emits multiple SQL rows. Adding `.distinct()` repairs the returned Python
identities but not the root fan-out.

Compile the same boolean meaning through the proposed predicate plan. Assert:

- one Book row;
- no outer Genre, membership, Loan, or Patron aliases;
- no framework-added `DISTINCT`;
- correlated `EXISTS` branches;
- direct `COUNT(*)` over the row-preserving root.

## Finding 6: same-related-row authorization is not a first-class construct

### Current behavior

Django intentionally gives different semantics to conditions applied in one `.filter()` and
conditions split across successive `.filter()` calls over a multi-valued relation.

This is dangerous for authorization. Consider an account with two users:

- user A satisfies account membership;
- user B has the required primary program affiliation.

Independent relation predicates can let the account qualify even though no single related
user satisfies both conditions.

The rotation director rule has the same conceptual requirement: `block_id` and
`rotation_id` must match one `UserSchedule` row.

Card 054 already recognizes the alias-sharing rule for relational search: visibility and
terminal predicates for one relation arm must build into one `Q` tree submitted in one
`.filter()` call.

### Required behavior

Expose an explicit construct:

```python
PredicatePlan.same_related_row(
    path="account__users__user_profile__affiliations",
    conditions=(
        Q(account__users__id=target_user_id),
        Q(account__users__user_profile__affiliations__program_id=program_id),
        Q(account__users__user_profile__affiliations__primary_program=True),
    ),
)
```

The exact syntax may use a relation-relative body instead. The semantic requirement is
fixed: all conditions share the same related-row chain inside one correlated body.

Do not silently change ordinary flat filter semantics. Same-row grouping must be explicit
for consumer predicates and preserved by search when visibility and the terminal condition
share a relation arm.

### Reproduction

The existing library topology can prove the ORM rule:

- root Book;
- visible Loan A whose note passes the visibility condition but whose Patron email does not
  match;
- hidden Loan B whose Patron email matches but whose note fails visibility.

Successive filters:

```python
Book.objects.filter(
    loans__note="visible",
).filter(
    loans__patron__email__icontains="needle",
)
```

incorrectly qualify the Book for the intended same-loan rule. One filter call carrying both
conditions does not.

The package test must assert both result behavior and inner alias sharing. A result-only
fixture can accidentally let two aliases land on the same child.

## Finding 7: computed field dependencies are column-only in the FieldSet plan

### Current planned behavior

Card 053 and its [`FieldSet specification`][fieldset-spec] add:

- field resolvers;
- `check_<field>_permission`;
- denial and redaction;
- computed fields;
- selection-aware `Meta.depends_on`.

The current specification limits `Meta.depends_on` to concrete model columns merged into
`OptimizationPlan.only_fields`. This is correct for a resolver such as:

```python
def resolve_display_name(root, info):
    return f"{root.name} ({root.start} - {root.end})"
```

It cannot describe Session participants or Event invitees.

### Required behavior

Expand the dependency vocabulary before card 053 freezes:

```python
FieldDependencyPlan(
    columns=("id",),
    select_related=(
        "session_course_rotation__course_rotation__academic_level__program",
    ),
    prefetch_related=(
        "individuals",
        "groups",
        "groups__group_user__user",
        "speakers",
        "venue",
    ),
    annotations=(),
    contextual_prefetches=(visible_group_members,),
    assembler=assemble_session_participants,
)
```

The tuple shorthand remains useful:

```python
Meta.depends_on = {
    "resolve_display_name": ("start", "end"),
}
```

It should normalize to `FieldDependencyPlan(columns=(...))`.

The full plan needs:

- concrete columns;
- `select_related` paths;
- plain prefetch paths;
- request-scoped prefetch factories;
- annotations;
- a batch assembler;
- related visibility composition;
- child projection;
- strictness resolver identities.

A batch assembler receives the materialized parent page and prefetched caches. It must not
call `.filter()`, `.exists()`, or `.count()` on a relation manager after prefetch; those
bypass the cache. It deduplicates users by primary key in Python over `.all()` results.

### Bounded Session participant plan

For any page size:

1. Session root query.
2. Direct individuals prefetch.
3. Groups prefetch.
4. Group memberships prefetch with `select_related("user")`.
5. Speakers prefetch, only when included by the field contract.
6. Venue prefetch, only when selected separately.

The assembler combines already-loaded users and never re-queries.

### Bounded Event invitee plan

Event invitees may require:

1. Event root query.
2. Programs.
3. Individual users.
4. Speaker users.
5. Groups.
6. Group memberships with users.
7. Roles.
8. One batched role/program/date affiliation query for all selected Events.

The last step is a real batch dependency, not representable as one static
`prefetch_related` path. The dependency API must permit a batch assembler or loader keyed by
the selected parent set.

### Reproduction

After FieldSet lands, add a computed `borrowers` field to Book:

```python
class BookFieldSet(FieldSet):
    borrowers: list[PatronType]

    def resolve_borrowers(self, root, info):
        return dedupe_by_pk(loan.patron for loan in root.loans.all())
```

With column-only `depends_on`, selecting `borrowers` over one hundred Books performs lazy
Loan and Patron reads. With the structured plan it performs:

```text
1 Book query
1 Loan query joined to Patron
```

Query count must be identical for one and one hundred Books.

## Finding 8: filtered or ordered nested connections fall back per parent

### Current behavior

`django_strawberry_framework/optimizer/nested_planner.py::_divergent_key_windows` classifies
`filter:` or `orderBy:` as sidecar arguments and leaves that response key unplanned.

`django_strawberry_framework/connection.py::_build_relation_connection_resolver` then runs
the ordinary connection pipeline against each parent's relation manager. Strictness warns or
raises, but the fallback remains:

```text
parents × page query
```

Selecting `totalCount` can add:

```text
parents × count query
```

One hundred Sessions with a filtered participant connection can therefore issue one hundred
or two hundred child statements.

Card 047 plans to make `connection` the secure default for many-side relation shape. That
increases the urgency of this gap.

### Required behavior

Normalize a nested sidecar once:

1. Start from the visibility- and edge-scoped child base queryset.
2. Apply the target FilterSet once.
3. Apply the target OrderSet once.
4. Append deterministic ordering.
5. Prove one SQL row per child identity.
6. Partition by the parent join key.
7. Window or lateral-page each parent.
8. Attach one result list per parent under a response-key-specific `to_attr`.

Cache the request-bound sidecar plan by:

- relation identity;
- normalized sidecar arguments;
- viewer/edge-scope key;
- database alias;
- target type;
- response-key-independent structural child selection.

Two aliases with different arguments should cost two batched child queries, not
`parents × 2`.

### Reproduction

Use the existing `PeriodicalType.issuesConnection` and `IssueOrder`.

Seed:

- one Periodical with five Issues;
- then one hundred Periodicals with five Issues each.

Select:

```graphql
query OrderedIssues {
  allLibraryPeriodicalsConnection(
    first: 100
  ) {
    edges {
      node {
        id
        issuesConnection(
          first: 2
          orderBy: [
            {
              number: DESC
            }
          ]
        ) {
          totalCount
          edges {
            node {
              id
              number
            }
          }
        }
      }
    }
  }
}
```

Current behavior is a strictness-visible per-parent fallback. The target query count is
constant:

```text
1 parent query
1 batched child page/count query
```

If the backend/strategy requires separate count and page statements, the allowed constant is
three total, still independent of parent count.

Add divergent aliases with `number DESC` and `number ASC`. The target adds one batched child
query per alias.

## Finding 9: nested window safety does not prove child row identity

### Current behavior

`django_strawberry_framework/optimizer/nested_fetch.py::unwindowable_child_queryset_reason`
rejects:

- sliced querysets;
- `select_for_update`;
- combined querysets;
- `distinct`;
- values querysets.

It does not reject a custom queryset carrying an unexplained to-many join.

For example:

```python
Issue.objects.filter(
    periodical__issues__embargoed=False,
)
```

can emit one Issue row per qualifying sibling Issue. It passes the current gate. Applying
`ROW_NUMBER()` and `COUNT() OVER (...)` counts multiplied SQL rows:

- duplicate edges;
- inflated `totalCount`;
- incorrect page boundaries;
- incorrect next-page flags.

### Required behavior

Carry a `RowIdentityProof` with framework-generated query-shape operations:

```text
PROVEN_BASE
PROVEN_CORRELATED_EXISTS
PROVEN_PARENT_PK_SUBQUERY
PROVEN_TO_ONE_JOIN
UNPROVEN_CONSUMER_SHAPE
KNOWN_MULTIPLYING
```

The proof composes:

- plain model base queryset: proven;
- `select_related`: remains proven;
- framework correlated `EXISTS`: remains proven;
- framework parent-PK subquery: remains proven;
- unexplained consumer join across a multiplying path: unproven;
- consumer `DISTINCT`: still unwindowable under the current semantic contract.

Strict mode must refuse to window an unproven shape with a targeted error. Non-strict mode
may use the existing per-parent fallback, but must not inject `DISTINCT`: that would silently
change a consumer multiset.

The long-term goal is proof by construction, not reverse-engineering every Django alias.
Consumer querysets that bypass framework shaping remain unproven unless they explicitly
assert a validated contract.

### Reproduction

Package-level:

```python
queryset = models.Issue.objects.filter(
    periodical__issues__embargoed=False,
)
assert unwindowable_child_queryset_reason(queryset) is None
```

Seed one Periodical with three Issues and two non-embargoed siblings. Show that evaluating a
window over the queryset produces repeated child identities or an inflated partition count.

Target:

- the shape reports `UNPROVEN_CONSUMER_SHAPE`;
- strict mode raises before attaching a window plan;
- non-strict mode leaves the relation unplanned;
- a semantically equivalent `Exists` shape remains proven and windowable.

## Finding 10: optimizer explain state is last-wins

### Current behavior

`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._publish_plan_to_context`
unions correctness sentinel sets so nested plans coexist, but stores
`DST_OPTIMIZER_PLAN` as last-wins introspection data.

One five-root operation therefore exposes only the last published plan. Under asynchronous
sibling resolution, the surviving plan can depend on completion order.

Card 062's current explain design assumes this single context plan.

### Required behavior

Publish an operation plan map keyed by an immutable root execution identity and rendered by
response path:

```text
scheduleCalendar.events
scheduleCalendar.shifts
scheduleCalendar.sessions
scheduleCalendar.rotations
scheduleCalendar.offRequests
```

Each explain entry should include:

- root field, type, and model;
- structural template fingerprint;
- structural cache hit or miss;
- request binding identity without secret values;
- select, prefetch, and computed dependencies;
- direct and correlated predicate branches;
- contextual edge scopes;
- nested strategy and sidecar plan;
- row-identity proof;
- fallback reasons;
- estimated query families;
- strictness keys;
- database alias;
- whether total count and page share a statement or use separate statements.

Shared operation dependencies should appear once with redacted keys and hit/miss counts.

### Reproduction

Run the five-root fakeshop operation from Finding 2 and inspect context after execution.

Current:

```text
one plan, last root wins
```

Target:

```text
five root entries
all selected root response paths represented exactly once
shared dependency entry reports one compute and four reuses
```

Run async execution with delays that reverse root completion order. The explain map remains
complete and deterministic.

## Finding 11: separate root statements can observe different snapshots

### Current behavior

Five connections and optional counts execute multiple statements. Under PostgreSQL's
default `READ COMMITTED` isolation, each statement can observe a newer committed snapshot.

Possible inconsistencies:

- one root's count disagrees with its page;
- Events and Sessions represent different points in time;
- audience IDs are derived before a grant change while later data statements observe data
  committed after the change;
- a schedule moves from one root-relevant state to another during the operation.

This is not unique to DSF. GraphQL's one HTTP operation does not imply one database snapshot.

### Optional behavior, explicitly non-gating

This finding is classified as an optional capability. It is not required for the graph
substrate to be correct, it does not appear in the acceptance criteria, and it must not block
any release. Every other finding in this guide describes required behavior; this one does not.

Offer an opt-in operation transaction policy for consumers that require a coherent
read snapshot:

```text
PostgreSQL transaction
isolation level REPEATABLE READ
read only
operation-scoped
```

It must be optional because it:

- holds a transaction for the full GraphQL execution;
- can increase connection usage and vacuum pressure;
- is backend-specific;
- may be inappropriate for operations mixing mutations or external I/O.

Document that ordinary operations retain backend defaults.

### Reproduction

PostgreSQL-only integration:

1. Open the GraphQL operation in connection A.
2. Resolve the first root and pause.
3. In connection B, insert or update a row affecting a later root and commit.
4. Resume connection A.

Under default `READ COMMITTED`, the later root may observe the change. Under the opt-in
repeatable-read policy, every root observes the initial snapshot.

Also reproduce count/page drift by pausing between those statements when the connection
implementation uses separate count and page queries.

## Finding 12: a shared interval-overlap vocabulary is missing

Every root implements the same conceptual interval:

```text
row.start <= scope.end
AND (row.end >= scope.start OR row.end IS NULL when the model permits it)
```

The model paths and null behavior differ. Repeating this in five custom filters is easy to
drift:

- an inclusive endpoint becomes exclusive;
- an end-null rule is lost;
- Session and Event use different timezone normalization;
- one root filters start-within-range instead of interval overlap.

### Recommendation

Add or document a compound filter primitive:

```python
IntervalOverlap(
    start_field="start_datetime",
    end_field="end_datetime",
    nullable_end=True,
)
```

It should:

- validate both paths at finalization;
- accept one normalized input object;
- bind values at execution time;
- preserve row identity;
- produce one `Q` tree;
- share sync/async behavior because the predicate itself is colorless;
- define inclusive endpoints explicitly.

This can remain a FilterSet feature. It does not need to become optimizer core, but the
model-independent schedule scope adapters should be able to consume it.

## Consumer security defect found during the audit

This issue belongs to the audited consumer, not DSF. It is separately owned work: it lands in
the Medtrics repository, with its own change and its own tests, against the current REST
implementation. It is not a phase of the DSF graph work and does not depend on any framework
change.

It must be fixed before shared audience memoization amplifies the result, because memoizing a
wrong permission answer makes it both faster and more consistently wrong.

`medtrics/src/apps/schedules/services.py::_resolve_permission_program_ids` filters:

- user or role;
- active permission row;
- permission name.

It does not require `allowed_permission` to be `View` or `Edit`, even though its docstring
states that contract. `UserSitePermission.allowed_permission` and
`RoleSitePermission.allowed_permission` accept blank values. A blank row can therefore widen
block or shift schedule visibility.

`medtrics/src/apps/schedules/services.py::user_has_any_schedule_grant` has the same omission
in its boolean fast path.

Required correction:

```python
allowed_permission__in=(
    ALLOWED_PERMISSION_VIEW,
    ALLOWED_PERMISSION_EDIT,
)
```

Use the existing constants imported from `users.models`, and apply the predicate to direct
and role permission branches in both the audience and boolean paths. Do not introduce new
permission-value names.

Required tests:

- direct blank permission does not widen;
- direct View widens;
- direct Edit widens;
- role blank permission does not widen;
- role View widens;
- role Edit widens;
- inactive rows never widen;
- an unrelated permission name never widens;
- audience and boolean fast path agree.

## Proposed shared graph-planning substrate

The search specification already contains the strongest graph design in the roadmap. The
root-cause fix is to extract it into shared infrastructure rather than reproduce it in each
Layer 3 subsystem.

### Required public declaration specification

The plan objects below are internal vocabulary. Sharing internal vocabulary is not by itself
enough to prevent cards 053, 054, and 056 from shipping incompatible public surfaces, because
those cards are consumed through declarations, not through plan classes.

A dedicated framework specification must therefore define the public declaration surface
before implementation begins. It must settle:

- the exact `class Meta` keys that compile into each plan object;
- which declarations live on sidecar `Set` classes and what those classes own;
- signatures for every consumer-supplied callable, including the sync and async forms;
- when declarations are validated, finalized, and bound to a request;
- inheritance, override, and composition behavior across type hierarchies;
- strictness and error semantics for undeclared or unresolvable declarations;
- which declarations are cacheable structure and which force request binding;
- whether a consumer may assert row identity for a custom queryset, and if so, how that
  assertion is validated rather than trusted.

That specification is a prerequisite for the foundation card described under recommended
roadmap additions. Implementing plan objects without it reintroduces exactly the divergence
this substrate exists to prevent.

### `GraphPathPlan`

Definition-time, immutable metadata:

```python
@dataclass(frozen=True)
class GraphPathPlan:
    owner_definition: DjangoTypeDefinition
    relation_hops: tuple[RelationHop, ...]
    terminal_field: models.Field
    first_multiplying_hop: int | None
    complete_relation_chain: tuple[str, ...]
    exact_owner_reentries: tuple[TypeIdentity, ...]
```

It contains:

- validated query and instance-accessor names;
- relation kind at every hop;
- target model and registered target type;
- exact owning type for root-model re-entry;
- multiplying-hop classification;
- no request values or querysets.

Search, generated filters, custom graph predicates, field dependencies, aggregate child
paths, and edge scopes consume this one path vocabulary.

### `PredicatePlan`

Definition-time boolean structure plus request-time value binding:

```python
@dataclass(frozen=True)
class PredicatePlan:
    operator: PredicateOperator
    branches: tuple[PredicateBranch, ...]
```

It owns:

- `any_of`, `all_of`, and `not_`;
- direct branches;
- correlated branches;
- same-related-row groups;
- per-hop visibility targets;
- row-identity proof output.

It does not own:

- arbitrary consumer `Q` introspection;
- request values in structural caches;
- silent `DISTINCT`;
- selection loading.

### `EdgeScope`

An edge is `(owner type, relation field, target type, context)`, not merely a target model.
Two fields reaching User may intentionally expose different user sets.

```python
@dataclass(frozen=True)
class EdgeScope:
    owner: TypeIdentity
    relation: GraphPathPlan
    target: TypeIdentity
    queryset_factory: Callable
    cache_key_factory: Callable | None = None
```

Search uses edge visibility while deciding whether a hidden child may qualify a parent.
Selection loading uses it while deciding which children may be returned. AggregateSet uses
it while deciding which children may contribute to a statistic.

These are different operations over one policy abstraction.

### `FieldDependencyPlan`

```python
@dataclass(frozen=True)
class FieldDependencyPlan:
    columns: tuple[str, ...] = ()
    select_related: tuple[GraphPathPlan, ...] = ()
    prefetch_related: tuple[GraphPathPlan, ...] = ()
    annotations: tuple[AnnotationPlan, ...] = ()
    contextual_prefetches: tuple[ContextualPrefetchPlan, ...] = ()
    assemblers: tuple[BatchAssemblerPlan, ...] = ()
```

The planner activates dependencies only when the computed field is selected. It reconciles
them with consumer querysets and ordinary relation selections through the same directive
ownership rules as `OptimizationPlan`.

### Structural template and bound plan

```text
StructuralOptimizationTemplate
    cacheable across requests
    relative paths
    field dependency graph
    visibility binding slots
    nested argument slots
    row-identity proof recipe

BoundOptimizationPlan
    request-local
    absolute resolver paths
    database alias
    visibility querysets
    contextual Prefetch objects
    normalized argument values
```

`OptimizationPlan` can remain the final ORM directive bag, but it should be produced by
binding a structural template. A request-bound queryset must never be stored in the
cross-request template.

### Selection-aware queryset shaping stage

The connection pipeline needs a named stage after visibility, filter, search, and ordering,
but before count and slice:

```text
source normalization
-> root visibility
-> FilterSet
-> search
-> OrderSet
-> deterministic order
-> selected annotations and field dependencies
-> row-identity validation
-> count and pagination
-> materialization and batch assemblers
```

The existing selection optimizer already runs before root count and pagination. The change
is to make computed annotations, edge recipes, and identity proof explicit participants
rather than invisible resolver behavior.

## KANBAN roadmap assessment

All 21 non-Done cards were reviewed. Landing them unchanged improves DSF but does not fully
close the schedule gaps.

### Directly relevant cards

#### `TODO-BETA-053` — FieldSet

Direct benefits:

- custom resolvers;
- field read gates;
- redaction and denial;
- computed fields;
- selection-sensitive column dependencies.

Gap:

- `Meta.depends_on` is limited to concrete columns.

Required amendment:

- normalize dependencies to `FieldDependencyPlan`;
- keep the column tuple as shorthand;
- add relation, annotation, contextual prefetch, and assembler dependencies;
- let strictness observe undeclared computed relation access where possible.

Without the amendment, FieldSet helps rotation `displayName` but does not safely optimize
Session participants or Event invitees.

#### `TODO-BETA-054` — `Meta.search_fields`

This is the most important graph-aware card. It remains planned: current synthesized
connections expose `filter:` and `orderBy:`, not `search:`. Its
[`search specification`][search-spec] already requires:

- strict relation path planning;
- correlated `EXISTS` for to-many search;
- no search-driven `DISTINCT`;
- per-hop related visibility;
- exact owner identity on root-model re-entry;
- same-related-row alias sharing;
- FilterSet permission gates;
- sync/async visibility derivation.

Required amendment:

- extract `GraphPathPlan`, `PredicatePlan`, visibility binding, and exact-owner handling into
  a shared package boundary;
- make search a consumer of that boundary;
- do not let search own the only correct graph compiler.

Remaining gap:

- nested filtered search still falls back per parent under the current spec.
- search scope is immutable and type-definition-wide; two roots over one model that need
  different path sets require distinct primary/secondary GraphQL types.

#### `TODO-BETA-056` — Aggregation

Directly useful concepts:

- `RelatedAggregate`;
- `get_child_queryset`;
- per-stat permissions;
- selection-aware computation.

Required amendment:

- consume `EdgeScope`, `GraphPathPlan`, and `FieldDependencyPlan`;
- do not create an aggregate-private child visibility abstraction;
- require row-identity/cardinality semantics for child aggregates.

#### `TODO-BETA-058` — `Meta.redaction_mode`

This card handles hidden forward non-null targets with optional sentinel redaction. It does
not scope selected to-many children.

It is useful for a different permission presentation problem and deliberately exposes an
existence signal in sentinel mode. It is not a blocker or solution for schedule assignees,
participants, invitees, group members, or account users.

#### `TODO-ALPHA-047` — execution resource policy

Direct benefits:

- depth, selection, alias, page, and list budgets;
- bounded many-side output;
- connection as the secure default relation shape.

Required coordination:

- filtered/ordered nested connection batching must land with or before broad connection
  defaulting;
- otherwise more queries enter the current per-parent sidecar fallback;
- the resource estimator should account for explicit fallback cost until batching exists.

#### `TODO-BETA-062` — optimizer explain mode

Direct benefit:

- makes optimizer decisions reviewable.

Required amendment:

- replace single last-wins context plan with an operation plan map;
- expose every root, cache hit/miss, visibility binding, predicate shape, edge scope,
  row-identity proof, nested strategy, and fallback reason.

#### `TODO-BETA-066` — adversarial tests

Add:

- five-root operations;
- related-row existence leaks;
- selected child leakage;
- same-related-row authorization;
- custom visibility outer fan-out;
- duplicate child rows under windows;
- whole-operation cache fragmentation;
- request memo scope isolation;
- async plan-map ordering;
- snapshot consistency in the PostgreSQL tier.

### Supporting cards

#### `TODO-ALPHA-051` — boundary hardening and DRY squeeze

Shared relation traversal and budget walkers are useful prerequisites. It adds no graph
semantics by itself.

The new graph-planning boundary should be decided before this card freezes optimizer
subsystem boundaries.

#### `TODO-BETA-055` — PostgreSQL full-text search

Useful for search ranking and annotation planning. It does not solve graph permissions.
Its annotation mechanism should consume the shared selection-aware shaping stage.

#### `TODO-BETA-057` — Layer 3 Meta-key promotion

Useful binding/finalization bookkeeping. It does not add graph behavior.

#### `TODO-BETA-060` and `TODO-BETA-061` — fakeshop activation and HTTP coverage

Useful acceptance vehicles, but their current KANBAN scope is narrower: card 060 owns the
product-catalog `node` / `nodes` roots and `totalCount`, while card 061 owns the related
product-catalog live HTTP tests. Neither card currently ships the schedule-shaped five-root
dashboard. That dashboard and its graph-security fixtures may use these test-placement
patterns only through a separately scoped future slice whose dependencies are explicit.

#### `TODO-BETA-065` — migration and adoption guides

Document the correct DRF migration:

- one denormalized REST endpoint does not imply one GraphQL root;
- create a scoped non-model container or sibling fields;
- preserve model identities;
- compute shared scope once;
- give each model a scope adapter;
- declare nested edge visibility independently from root visibility.

#### `TODO-STABLE-067` — stable release

Release verification only. The graph foundations must land before its public API freeze.

### No meaningful direct impact

- `TODO-ALPHA-048` — secure output/error defaults.
- `TODO-ALPHA-049` — dependency and CI hardening, except runtime compatibility hygiene.
- `TODO-ALPHA-050` — debug package extraction.
- `TODO-ALPHA-052` — beta release.
- `TODO-BETA-059` — enum naming.
- `TODO-BETA-063` — mutation idempotency.
- `TODO-BETA-064` — configurable filter key names.

These cards may be important to the project but do not close schedule graph planning.

## BACKLOG differentiation cards to reconcile

[`BACKLOG.md`][backlog] is unscheduled by policy, but several of its cards already describe
fragments of the abstractions this guide proposes. If they are promoted independently after
the graph substrate exists, they must consume it; if they are promoted first, their
vocabulary becomes the substrate's constraint. Either way the overlap should be explicit.

### Overlapping the graph substrate directly

- [`cascade_permission_prefetch_enforcement`][backlog-cascade-prefetch] is the closest
  sibling of Finding 4. It plans visibility inside every optimizer-built `Prefetch` and
  downgrades boundary-crossing `select_related` to filtered prefetches. Its "visibility
  combinator seam" and `EdgeScope` are one abstraction: the card must not ship a
  permission-private child-scoping mechanism parallel to the contextual edge scope proposed
  here. [`soft_delete_cooperation`][backlog-soft-delete] declares the same seam for
  soft-delete filtering and should compose through it as a third consumer.
- [`computed_field_optimizer_hints`][backlog-computed-hints] (with
  [`computed_fields_binding`][backlog-computed-binding]) is the precursor of Finding 7. Its
  two-halves rule — relation traversals extend `select_related`/`prefetch_related` **and**
  column reads extend the `only()` projection — is a requirement `FieldDependencyPlan`
  already absorbs, as is its strictness contract (report the property name and the hint
  that would fix it). The hint dict should normalize into `FieldDependencyPlan` rather than
  freeze a second dependency vocabulary next to `Meta.depends_on`.
- [`selection_aware_annotations`][backlog-selection-annotations] supplies the annotation arm
  of the selection-aware shaping stage, including the injection triggers this guide needs
  (selected field, active filter, active `orderBy`). Its cacheability split — static ORM
  expressions bake into the cached plan while `Info`-receiving callables mark the plan
  non-cacheable — is exactly the structural-template versus request-binding boundary of
  Finding 3. Under the template split, the callable arm should become a binding slot instead
  of reusing the whole-plan `cacheable = False` path it currently piggybacks on.
- [`request_lifecycle_cancellation_and_reuse`][backlog-request-lifecycle] carries the
  cross-request sibling of Finding 1: an opt-in short-TTL auth/visibility context keyed on
  user and registry epoch. The operation-scoped memo proposed here is the safe default tier;
  the TTL cache is an explicit escalation with a documented revocation window. They should
  share one keying discipline (viewer, tenant, database alias, epoch) so opting into reuse
  never widens a scope the memo kept isolated. Its cancellation half also feeds R2's
  requirement that a cancelled factory not leak an in-progress future.
- [`operation_document_and_plan_cache`][backlog-operation-cache] caches parse, validation,
  and plan by exact document hash and registry epoch. It is complementary to Finding 2, not
  a substitute: the document cache accelerates byte-identical repeats, while root-subtree
  structural templates fix sibling invalidation inside one changing document. Both layers
  must agree on schema-epoch keying, and the structural template is what the document-level
  entry should bind against.

### Overlapping the nested and pagination work

- [`sqlite_correlated_json_nested_fetch`][backlog-sqlite-json],
  [`backward_nested_keyset_pagination`][backlog-backward-keyset], and
  [`mti_aware_lateral_nested_fetch`][backlog-mti-lateral] all extend the pluggable
  nested-fetch strategy boundary. Each must consume the sidecar normalization of Finding 8
  and the `RowIdentityProof` gate of Finding 9; a new strategy that self-certifies child row
  identity would reopen the window-safety hole in a new backend.
- [`stable_cursor_field`][backlog-stable-cursor] and
  [`permission_aware_cursor_decoding`][backlog-cursor-decoding] harden the cursor semantics
  R7 asserts. Cursor decode re-applying `get_queryset` visibility is the pagination-time
  form of the same rule as edge scope: a value minted under one viewer must not leak rows
  under another.

### Reinforcing the validation posture

- [`anti_n1_ci_audit`][backlog-anti-n1] turns this guide's query-count matrix into an
  enforceable CI contract. Its seeding rule — at least two rows on every many side, with the
  command refusing to certify a thin seed — matches the fixture guidance here and should be
  the acceptance vehicle for the one-versus-one-hundred-parent invariants.
- [`matrix_dimensions_and_measures`][backlog-matrix] independently arrives at the
  cardinality stance of Finding 5: aggregate fan-out across a many-join is a planner error
  by default, never a silently multiplied result. The shared fan-out contract it names
  should be stated once by the graph substrate and consumed by matrices, aggregation, and
  generated predicates alike.

## Recommended roadmap additions

Neither card exists yet. Both are recommendations from this audit: they are not present in
[`KANBAN.md`][kanban], they have no card numbers, and the amendments they imply for cards
053, 054, 056, 062, and 066 have not been written into those cards. Acting on the existing
cards before these are created and sequenced risks producing exactly the divergent Layer 3
abstractions this guide argues against.

Required order: write the public declaration specification described under the shared
graph-planning substrate, create these two cards with real numbers and dependencies, amend
the affected cards, and only then plan implementation.

Both cards are Beta-milestone (pre-`1.0.0`) foundation work. Their consumer-facing surface,
where one exists, is Meta-declared per the alignment constraints above; the plan objects
themselves are framework-internal vocabulary.

### New foundation card: graph policy and field dependency planning

Land before card 053.

Scope:

- `GraphPathPlan`;
- exact owner identity;
- per-hop target visibility metadata;
- `PredicatePlan`;
- `any_of`, `all_of`, `not_`;
- explicit same-related-row groups;
- `EdgeScope`;
- operation-scoped immutable dependency memo;
- `FieldDependencyPlan`;
- row-identity proof metadata;
- sync/async request binding.

Consumers:

- FilterSet;
- search;
- FieldSet;
- AggregateSet;
- edge-scoped selection loading;
- nested planner;
- explain mode.

### New optimizer card: structural templates and nested sidecar batching

Land before card 062 and before stable.

Scope:

- root-subtree structural fingerprints;
- separation of structural templates from request binding;
- response-path rebasing;
- operation plan map;
- request-bound `Prefetch` recipes;
- filtered/ordered/search nested connection batching;
- row-identity proof gate;
- per-alias batched nested plans;
- cache and fallback explain metadata.

### Proposed order

```text
047 execution budgets
051 boundary/DRY preparation
graph policy and dependency foundation
053 FieldSet on shared dependencies
054 search on shared predicates and visibility
055 full-text on shared annotation shaping
056 aggregation on shared edge scope
057/058 Layer 3 binding and redaction
structural templates and nested sidecar batching
062 explain over operation plan map
066 adversarial graph suite
065 migration guide update
067 stable audit
```

Cards without dependencies on this work can continue independently. The order above is about
preventing incompatible public graph abstractions, not serializing the whole roadmap.

## Planning artifact boundary

This guide is a reproduction and architecture specification, not the implementation plan
for the separate Medtrics raw-SQL pagination work. That plan covers `ScheduleQuery`,
`ScheduleQueryExecutor`, `COUNT(*) OVER()` / pagination execution, ordering tiebreakers, and
schedule API tests. It does not plan the multi-root GraphQL graph, shared audience binding,
edge visibility, computed dependencies, or nested graph batching. A graph implementation
requires its own approved plan before execution; the raw-SQL pagination plan must not be
listed as the plan that lands this guide.

## Faithful Medtrics recreation specification

This section defines the consumer implementation expected after the framework foundations
land.

### Scope object

Normalize once:

```python
@dataclass(frozen=True)
class FrozenScheduleAudience:
    unrestricted: bool
    rotation_ids: frozenset[int]
    block_director_grants: frozenset[tuple[int, int]]
    block_program_ids: frozenset[int]
    shift_program_ids: frozenset[int]
    curriculum_program_ids: frozenset[int]
    event_program_ids: frozenset[int]
    extra_user_ids: frozenset[int]

    def session_program_ids(self) -> frozenset[int]:
        return self.block_program_ids | self.curriculum_program_ids


@dataclass(frozen=True)
class ResolvedScheduleScope:
    start: datetime
    end: datetime
    program_id: int | None
    target_user_id: int | None
    site_id: int | None
    rotation_id: int | None
    search: str | None
    audience: FrozenScheduleAudience
    database_alias: str
```

The object contains immutable IDs and normalized values, not querysets or model instances.

The audience must be a genuinely immutable snapshot, not the mutable builder. The production
`ScheduleAudience` is an ordinary dataclass whose dimensions are mutable `set` fields, so
storing it inside a frozen wrapper would leave every dimension mutable after resolution.
Convert each dimension to a `frozenset` exactly once, when derivation finishes, and treat the
frozen snapshot as the only value that may be memoized, shared across roots, used in a cache
key, or read by a nested edge scope. `session_program_ids()` remains a derived union so the
existing production semantics are preserved rather than duplicated at each call site.

This matters beyond style: an audience that can still be mutated after resolution allows one
root to widen the scope another root already used, breaks memo key stability, and is unsafe
to share across concurrently resolving async siblings.

Explicit target-user validation occurs once. An out-of-scope target fails closed according
to the chosen API contract; it must not let one root silently use the requested target while
another coerces to self.

Every adapter first applies the operation's global access decision:

- public schedule policy when institution settings permit it;
- unrestricted staff/institution/program administration;
- widened audience;
- otherwise authenticated self-only scope.

The per-root rules below describe the model-specific widened/self predicates after that
shared precedence has been resolved.

### Event root

Base model:

```text
Event
```

Root visibility:

```text
public policy
OR program in audience.event_program_ids
OR attendance user in audience.extra_user_ids
```

Root ORM requirements:

- interval overlap on `start_datetime` and nullable `end_datetime`;
- optional program filter;
- search title;
- `select_related("event_type")`;
- selected program prefetch;
- selected Attendance prefetch with `select_related("user", "user__role")`;
- contextual edge scope for attendees/invitees.

If the client needs Attendance status as the primary row, expose a separate Attendance
connection. Do not multiply Event rows.

### Shift root

Base model:

```text
AssignDateToShift
```

Root visibility:

```text
shift_date.call_schedule_add_shift.program in audience.shift_program_ids
OR assignee in audience.extra_user_ids
```

Root ORM requirements:

- derive effective start/end from applied date and override/default time;
- optional site filter;
- search `shift_date__shift_name`;
- `select_related` through shift, call schedule program, program, site, and location;
- contextual assignee prefetch.

The effective datetime calculation should be a validated annotation plan, not repeated
Python parsing per row.

### Session root

Base model:

```text
SessionSchedule
```

Root visibility:

```text
course program in audience.session_program_ids()
OR individuals contains self
OR groups has a membership for self
```

Root ORM requirements:

- `is_published=True`;
- interval overlap;
- optional program and venue-site filters;
- phrase search over session code/title and course code/title composition;
- `select_related` through course rotation, academic level, program, and event type;
- structured participant dependency;
- venue prefetch only when selected.

The participant assembler combines direct individuals, selected group memberships, and the
separately selected `speakers` relation according to the consumer's GraphQL field contract.
It uses prefetched `.all()` results and deduplicates by user primary key. The current
`SessionSchedule.get_users_list()` implementation itself covers only direct individuals and
group members; adding speakers to one computed GraphQL field is proposed behavior.

### Rotation root

Base model:

```text
UserSchedule
```

Root visibility is one row-preserving `any_of`:

```text
rotation_id in audience.rotation_ids
OR same row has (block_id, rotation_id) in audience.block_director_grants
OR block.program_schedule.program_id in audience.block_program_ids
OR user_id in audience.extra_user_ids
```

Root ORM requirements:

- `confirmed=True`;
- interval overlap;
- optional program, site, and rotation filters;
- search rotation name;
- `select_related` for `user`, `user__role`, `rotation`, `block__program_schedule`, and
  `block__program_schedule__program`;
- site prefetch only when selected.

Director grants should compile as correlated exact pair predicates. Independent
`block_id__in` and `rotation_id__in` filters are forbidden.

### Off-request root

Base model:

```text
AccountRequest
```

Root visibility:

```text
approved status
AND account has the requesting user in the same scoped account-user path
```

Program widening does not apply. Program information, if selected, comes through the visible
account user's primary affiliation and must retain same-related-row semantics.

Root ORM requirements:

- interval overlap on `specific_date` and `end_date`;
- `select_related("account", "category", "status")`;
- scoped account-user prefetch;
- scoped primary-affiliation prefetch;
- search category name.

### Expected query bounds

With every root selected, every `totalCount` selected, and the nested fields in the example
operation:

- one operation dependency computation for the audience;
- at most one count and one page statement per root unless the selected strategy combines
  them;
- fixed Event prefetch families;
- one Shift assignee prefetch;
- fixed Session participant/venue prefetch families;
- one Rotation site prefetch if selected;
- fixed Off account-user/affiliation prefetch families.

The exact constant depends on selected fields and backend strategy. The invariant is:

```text
queries(page size 1) == queries(page size 100)
```

for the same selection and data-independent authorization path.

## Fakeshop recreation plan

Most failures can be reproduced without new models.

### Existing topology mapping

```text
Schedule root identity        -> Book / Periodical / Product models
Nested participants           -> Book.loans -> Loan.patron
Group-like to-many search     -> Book.genres
Root-model re-entry           -> Loan.book -> Book.loans -> Loan
Custom child visibility       -> IssueType.get_queryset
Nested paginated children     -> Periodical.issuesConnection
Five sibling model roots      -> Category, Item, Property, Entry, Periodical
```

### Temporary acceptance activation

Use settings-gated or dedicated test types where changing a permanent public type would
disturb unrelated examples.

Required fixture capabilities:

1. A Loan visibility hook that hides rows marked by a stable note value for non-staff.
2. A Book computed `borrowers` field after FieldSet lands.
3. A five-root dashboard query.
4. An Issue child queryset that can intentionally introduce a multiplying sibling join for
   row-identity tests.
5. A counter-backed operation dependency.

No new model is necessary for the first four. If an operation dependency needs tenant
identity, use the existing request user and a test-local immutable key.

### Live HTTP placement

Consumer-visible GraphQL behavior belongs in:

```text
examples/fakeshop/test_query/
```

Feature-specific package mechanics belong in:

```text
tests/optimizer/
tests/filters/
tests/fieldset/
tests/permissions/
```

PostgreSQL plan artifacts belong in a standing doc only when they record repeatable fixture
shape, versions, indexes, and complete before/after SQL.

## Reproduction suite

### R1: five-root structural cache isolation

Use the operation in Finding 2.

Assert:

- each root produces one explain entry;
- toggling `includeEntries` invalidates only Entries;
- changing `issueFirst` invalidates or rebinds only the Issue subtree;
- aliasing Categories does not require a new structural Category template;
- a second identical request hits all structural templates;
- request-bound paths are correctly rebased under aliases.

### R2: operation dependency isolation

Execute five roots with one shared dependency factory.

Assert:

- one compute per operation;
- four or more request-local hits;
- second request recomputes;
- different user, tenant key, or DB alias never shares;
- sync and async results agree;
- a failing factory does not leave a poisoned completed entry;
- cancellation does not leak an in-progress future into a later request.

### R3: root visibility versus edge visibility

Seed one visible Book with one visible and one hidden Loan.

Assert:

- Book remains visible;
- hidden Loan cannot be selected;
- hidden Loan cannot qualify Book search;
- hidden Loan cannot contribute to a count/aggregate;
- staff sees both when its policy allows both;
- one and one hundred Books use the same query count.

### R4: same-related-row authorization

Seed visible nonmatching child A and hidden matching child B.

Assert:

- sequential Django filters demonstrate the false positive;
- one same-row predicate does not qualify the root;
- generated SQL shares the intended relation alias inside one body;
- the public predicate API emits one correlated branch;
- negation keeps the intended quantifier semantics.

### R5: custom predicate cardinality

Seed one Book with multiple matching Genres and Loans.

Assert:

- baseline custom `Q` query fans out;
- `.distinct()` baseline returns correct identities but retains outer joins;
- predicate plan returns one row;
- root alias map has no child tables;
- no framework-added `DISTINCT`;
- count and page both use row-preserving predicates.

### R6: computed dependency batching

Seed one and one hundred Books, each with multiple Loans and Patrons.

Assert:

- `borrowers` returns unique Patrons;
- no deferred-column query;
- no per-Book relation query;
- no per-Loan Patron query;
- declared prefetch is consumed through `.all()`;
- query count is constant;
- omitting `borrowers` omits its Loan/Patron query;
- a redacted or denied field does not run its unnecessary assembler when policy can decide
  before data loading.

### R7: ordered nested connection batching

Use `Periodical.issuesConnection(orderBy:)`.

Assert:

- one and one hundred Periodicals use the same child query count;
- each parent gets its own first two Issues;
- `totalCount` is per parent;
- cursors replay;
- two argument-divergent aliases use two batched child queries;
- strictness does not report a planned edge;
- explain reports the sidecar normalization and strategy.

### R8: row-identity window gate

Use the multiplying Issue queryset.

Assert:

- current classifier misses the multiplying join, documenting the baseline;
- strict target raises a targeted unproven-row-identity error;
- non-strict target falls back;
- no automatic `DISTINCT`;
- replacing the join with correlated `EXISTS` restores a proven window plan;
- duplicate child identities never enter row numbering or partition count.

### R9: exact-owner root-model re-entry

Register primary and secondary Loan GraphQL types with different visibility. Search through:

```text
Loan.book -> Book.loans -> Loan.patron.email
```

Assert:

- a connection over the secondary Loan type applies the secondary visibility to the
  re-entered Loan hop;
- registry primary lookup is not substituted;
- a hidden matching primary-visible Loan cannot qualify the secondary root;
- structural cache identities differ by exact owner type.

### R10: operation explain completeness

Run the five-root query in sync and async modes.

Assert:

- all roots appear;
- completion order does not change content;
- no response contains only the last plan;
- shared dependencies appear once;
- fallback reasons are attached to the correct response key;
- sensitive scope values are redacted.

### R11: repeatable-read snapshot

PostgreSQL only. This reproduction covers the optional snapshot policy and is not release
gating; it applies only if that policy is implemented.

Assert:

- default mode demonstrates statement-level snapshot change;
- opt-in mode keeps five roots coherent;
- transaction is read-only;
- transaction closes after success, GraphQL error, cancellation, and resolver exception;
- mutation operations reject or bypass the read-only policy according to explicit
  configuration.

### R12: Medtrics permission value gate

Consumer repository.

Assert the View/Edit/blank matrix listed in the security finding for:

- direct `UserSitePermission`;
- `RoleSitePermission`;
- full audience;
- boolean fast path.

This test is required before operation memoization because a fast, shared wrong permission
answer is worse than a repeated wrong answer.

## SQL-shape assertions

Round-trip counts alone are insufficient. A JOIN-plus-`DISTINCT` query can use the same
number of SQL statements as a row-preserving query.

For each custom graph predicate:

```python
root_tables = {
    join.table_name
    for join in queryset.query.alias_map.values()
}
assert child_membership_table not in root_tables
assert child_table not in root_tables
assert queryset.query.distinct is False
assert "EXISTS" in str(queryset.query).upper()
```

The child table may appear inside the correlated subquery SQL. The invariant is that it is
not an alias in the outer root query.

For nested windows:

- selected child primary keys are unique within each parent partition;
- partition count equals unique child model rows under the proven shape;
- row number is monotonic under deterministic ordering;
- the parent connector and ordering columns match a suitable composite index advisory.

For computed fields:

- inspect captured SQL for relation tables;
- verify fixed query families;
- separately assert the resolver consumes prefetched caches.

## Query-count matrix

Every selected shape should run with one and one hundred parents:

| Shape | Allowed growth |
|---|---|
| Five root pages without counts | O(selected roots) |
| Five root pages with counts | O(selected roots) |
| Session participants | O(selected dependency families) |
| Event invitees | O(selected dependency families) |
| One nested alias | O(1) child batches |
| Two divergent nested aliases | O(2) child batches |
| Same alias over 100 parents | no parent-count growth |
| Shared audience over five roots | one computation |

Do not pin one universal numeric count across SQLite and PostgreSQL if backend strategy
legitimately differs. Pin:

- a backend-specific expected constant;
- equality between one-parent and one-hundred-parent cases;
- SQL/cardinality invariants.

Growth classes alone are not a sufficient gate. Parent-count equality is satisfied by an
implementation that consistently issues far more queries than necessary, so every shape above
must also pin an exact expected integer per backend once the chosen architecture is
prototyped. Derive those integers from a measured baseline, record them in the test, and treat
any change to them as a deliberate reviewable change rather than a threshold to relax.

## PostgreSQL profiling

### Data shape

Record:

- root count per model;
- average and maximum child rows;
- percentage of roots visible by each audience arm;
- number of matching children per root;
- selected page sizes;
- aliases and sidecar arguments;
- PostgreSQL, Django, and DSF versions;
- indexes;
- warm/cold cache status.

A useful schedule-like stress fixture:

- 20,000 roots across five root models;
- 20 child memberships per graph-heavy root;
- multiple matching children for each qualifying parent;
- sparse direct matches;
- sparse audience grants;
- enough shared blocks/programs to expose same-row errors.

Use `bulk_create()` for fixture rows and through models. Do not call `.save()` or `.add()` in
large loops.

### Plans to compare

Capture:

```python
queryset.explain(
    analyze=True,
    buffers=True,
    format="json",
)
```

Compare:

- outer rows emitted before pagination;
- rows removed by filters;
- join loops over through tables;
- Sort, Unique, HashAggregate, and distinct-wrapper nodes;
- semi-join or correlated `EXISTS` behavior;
- window partition rows;
- count plan;
- page plan;
- shared/temp blocks;
- planning and execution time.

Do not add wall-clock percentage gates to the normal test suite. Gate structural invariants
and retain repeatable explain artifacts as performance evidence.

## Implementation phases

### Phase 1: freeze current failures

Add R1 through R10 as failing or baseline-characterization tests before production changes.
Add R12 in the consumer repository before caching audience results.

### Phase 2: operation dependency context

Implement the request-local dependency memo and execution lifecycle cleanup.

Prove:

- sync;
- async;
- concurrent siblings;
- failure cleanup;
- request isolation;
- database/tenant/viewer keying.

### Phase 3: shared graph path and predicate plans

Extract relation metadata used by card 054 into shared immutable plans.

Implement:

- direct and correlated branches;
- boolean composition;
- same-related-row groups;
- exact-owner re-entry;
- sync/async visibility binding;
- row-identity proof propagation.

Migrate only framework surfaces whose semantics are explicitly proven. Do not inspect and
rewrite arbitrary consumer Django joins.

### Phase 4: contextual edge scope

Add request-bound child scope factories and reserved `to_attr` resolution.

Integrate with:

- ordinary many-side fields;
- nested connections;
- search qualification;
- AggregateSet child rows;
- strictness.

### Phase 5: structured FieldSet dependencies

Expand `Meta.depends_on` before card 053 implementation is finalized.

Add:

- relation directives;
- annotations;
- contextual prefetches;
- batch assemblers;
- selection-sensitive activation;
- consumer reconciliation;
- strictness metadata.

### Phase 6: structural templates

Replace whole-operation structural identity with root-subtree fingerprints.

Split request binding from template caching. Rebase runtime paths late and publish a complete
operation plan map.

### Phase 7: nested sidecar batching and row proof

Normalize filtered, ordered, and search-bearing child querysets once. Apply window/lateral
strategies only to proven row-identity shapes.

### Phase 8: explain and adversarial coverage

Amend cards 062 and 066 to expose and attack every new abstraction.

### Phase 9: Medtrics recreation

Build the five model-backed roots, the shared container/scope, and the structured computed
fields. Compare functional results against the REST endpoint during migration, but compare
natural GraphQL identities rather than requiring one flattened UNION row per user/program.

### Phase 10: optional snapshot policy

Add PostgreSQL repeatable-read execution only after ordinary query shape is bounded. Keep it
opt-in and measure transaction duration under representative operations.

## Acceptance criteria

The framework work is complete only when:

1. One operation can select five model-backed connections with one shared immutable
   dependency computation.
2. Unrelated sibling changes do not invalidate unchanged structural templates.
3. Request-bound `get_queryset` visibility does not make the structural template
   uncacheable.
4. A visible parent cannot expose hidden children.
5. A hidden child cannot qualify a parent through search, filter, or aggregate.
6. Consumer graph permissions can use public row-preserving predicates without
   JOIN-plus-`DISTINCT`.
7. Same-related-row authorization is explicit and tested.
8. FieldSet can declare relation, annotation, contextual prefetch, and assembler
   dependencies.
9. Computed Session participants and Event invitees have query counts independent of parent
   count.
10. Filtered and ordered nested connections batch by argument-distinct alias, not parent.
11. Window planning refuses unproven row-multiplying child shapes.
12. `totalCount`, edges, page flags, and cursors use root/child identities correctly.
13. Explain mode reports every root and shared dependency.
14. Sync and async behavior agree.
15. SQLite behavioral tests and PostgreSQL SQL/plan tests pass.
16. Multi-database aliases remain pinned correctly.
17. Strictness reports real fallbacks and never accepts a plan that failed to attach.
18. The migration guide teaches the scoped multi-root pattern.
19. Cards 053, 054, and 056 consume one graph substrate.
20. No request value, user, tenant, queryset, or database alias enters a cross-request
    structural cache.

## Rejected approaches

### Recreate the raw UNION as one GraphQL model

It discards natural model identity, bypasses most DSF optimizer behavior, and makes nested
relations artificial. The intended GraphQL query already has five roots.

### Return one materialized mixed Python list

It loses queryset composition, per-model filtering, connection pagination, selection
optimization, and visibility hooks.

### Add `.distinct()` to every graph permission

It repairs returned identities after fan-out but retains expensive joins, count wrappers,
and ambiguous ordering/cardinality. It can also change a consumer's intentional multiset.

### Add more `prefetch_related()` to root visibility

Prefetch controls selected relation loading. It cannot remove row-multiplying joins already
introduced by a filter predicate.

### Make `apply_cascade_permissions` walk every edge

Forward target visibility and contextual to-many edge scope are different policies.
Automatically cascading every collection can remove children under the wrong context,
explode query planning, and make cycles harder to reason about.

### Cache evaluated permission querysets

Querysets and model instances are request-, transaction-, router-, and snapshot-sensitive.
Cache immutable IDs and decisions with explicit scope keys.

### Store audience values in `OptimizationPlan`

The plan cache is cross-request. Request data belongs only in a bound execution plan.

### Infer arbitrary resolver dependencies

Python resolvers can use helpers, dynamic attribute access, loops, and external services.
Explicit dependency plans have an honest failure mode; static inference would provide false
confidence.

### Let every Layer 3 subsystem invent child policy

Search, FieldSet, AggregateSet, and permissions would drift on owner identity, async
visibility, alias sharing, database pinning, and strictness. One graph substrate is the
root-cause fix.

### Automatically trust any custom queryset for windows

A queryset can carry a multiplying join without `distinct` or another currently-detected
flag. Window counts over duplicate SQL rows are incorrect.

### Automatically add `DISTINCT` before windows

That changes consumer semantics and can conflict with ordering. Refuse or fall back unless
row identity is proven.

### Treat GraphQL operation atomicity as implied

One GraphQL document can execute many SQL statements. Snapshot consistency requires an
explicit transaction policy.

### Defer graph foundations until after 1.0

FieldSet, search, AggregateSet, and explain would expose separate public concepts that are
harder to unify after stable API commitments. The shared substrate should precede them.

## Validation commands

After implementation edits:

```bash
uv run ruff format .
uv run ruff check --fix .
uv run python scripts/check_trailing_commas.py --check
git diff --check
```

Run focused tests appropriate to the shipped slices, for example:

```bash
uv run pytest -n0 \
  tests/optimizer \
  tests/filters \
  tests/fieldset \
  tests/permissions \
  examples/fakeshop/test_query
```

Run the full SQLite suite:

```bash
uv run pytest
```

Run the PostgreSQL tier with the repository's configured DSN:

```bash
FAKESHOP_PG_DSN="$FAKESHOP_PG_DSN" uv run pytest -n0 \
  tests/optimizer \
  tests/filters \
  examples/fakeshop/test_query
```

The exact focused file list should follow the implementation slices. Preserve 100% package
coverage.

## Handoff checklist

This guide is an architecture audit and roadmap input. It is not a line-by-line coding
specification, and the items below are not optional preliminaries: each one resolves a
decision the implementation would otherwise have to invent.

Before implementation:

- Read this guide.
- Read the [`FieldSet specification`][fieldset-spec] and
  [`search specification`][search-spec].
- Resolve every item under required product and security decisions, and record the chosen
  contracts.
- Write the public declaration specification for the graph substrate.
- Create the two recommended foundation cards in [`KANBAN.md`][kanban] with real numbers and
  dependencies, and amend cards 053, 054, 056, 062, and 066 accordingly.
- Create an approved implementation plan for the graph work; the raw-SQL pagination plan does
  not cover it.
- Run R1, R5, R7, R8, and R10 to capture current baselines.
- Fix and test the consumer's blank `allowed_permission` widening defect as separately owned
  Medtrics work.
- Decide and own the dependency compatibility resolution.

During implementation:

- Keep structural metadata separate from request binding.
- Use exact GraphQL type identity, not only model identity.
- Keep values and querysets out of cross-request caches.
- Compile to-many authorization row-preservingly.
- Use one filter body for same-related-row semantics.
- Scope selected edges independently from root visibility.
- Audit every changed queryset for N+1 behavior.
- Consume prefetched relations through `.all()`, never a new `.filter()` or `.exists()`.
- Prove row identity before windows.
- Publish strictness metadata only for successfully attached work.

Before review:

- Attach before/after SQL for graph predicates.
- Attach one-parent and one-hundred-parent query counts.
- Attach cache hit/miss evidence for sibling variations.
- Attach operation explain output with all roots.
- Attach PostgreSQL plans for fan-out, correlated predicates, and nested windows.
- State snapshot policy explicitly.
- Confirm all 21 planned-card interactions remain coherent.
- Confirm the resulting API uses five natural roots rather than a synthetic UNION model.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[backlog]: BACKLOG.md
[backlog-anti-n1]: BACKLOG.md#anti_n1_ci_audit
[backlog-backward-keyset]: BACKLOG.md#backward_nested_keyset_pagination
[backlog-cascade-prefetch]: BACKLOG.md#cascade_permission_prefetch_enforcement
[backlog-computed-binding]: BACKLOG.md#computed_fields_binding
[backlog-computed-hints]: BACKLOG.md#computed_field_optimizer_hints
[backlog-cursor-decoding]: BACKLOG.md#permission_aware_cursor_decoding
[backlog-matrix]: BACKLOG.md#matrix_dimensions_and_measures
[backlog-mti-lateral]: BACKLOG.md#mti_aware_lateral_nested_fetch
[backlog-operation-cache]: BACKLOG.md#operation_document_and_plan_cache
[backlog-request-lifecycle]: BACKLOG.md#request_lifecycle_cancellation_and_reuse
[backlog-selection-annotations]: BACKLOG.md#selection_aware_annotations
[backlog-soft-delete]: BACKLOG.md#soft_delete_cooperation
[backlog-sqlite-json]: BACKLOG.md#sqlite_correlated_json_nested_fetch
[backlog-stable-cursor]: BACKLOG.md#stable_cursor_field
[goal]: GOAL.md
[kanban]: KANBAN.md

<!-- docs/ -->
[row-preserving-pg]: docs/row-preserving-predicates-part1-pg-explain.md

<!-- docs/SPECS/ -->
[connection-optimizer-spec]: docs/SPECS/spec-033-connection_optimizer-0_0_9.md
[fieldset-spec]: docs/SPECS/spec-053-fieldset-0_1_1.md
[permissions-spec]: docs/SPECS/spec-034-permissions-0_0_10.md
[search-spec]: docs/SPECS/spec-054-search_fields-0_1_2.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
