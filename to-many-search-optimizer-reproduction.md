# To-many search optimization: reproduction, architecture, and implementation guide

## Purpose

This guide gives another developer a reproducible case for a GraphQL search that crosses a
to-many Django relation, explains why the current selection optimizer cannot repair the
resulting SQL, and defines the root-cause implementation and validation plan.

The motivating production topology is:

```text
UserSchedule -> User -> GroupUser -> Group
             \-> Rotation
```

A schedule search spans ordinary single-valued paths such as user name and rotation name,
plus the reverse-FK group-membership path:

```text
user__group_list__group__name
```

The equivalent fakeshop topology already exists and needs no model or migration changes:

```text
Book -> library_book_genres -> Genre
```

`Book` is the root row, `library_book_genres` is the membership fan-out, and `Genre.name`
stands in for `Group.name`. The reproduction uses the mixed search paths:

```python
(
    "title",
    "subtitle",
    "shelf__branch__name",
    "genres__name",
)
```

The guide assumes the [`Meta.search_fields` spec][search-fields-spec] has landed. The
ORM-only baseline can be run before that card lands; the live GraphQL portion is the
acceptance fixture for the implementation.

## Executive conclusion

The card-049 design as currently written protects result correctness but not database cost:

1. The compiler builds direct Django traversal predicates such as
   `genres__name__icontains=value`.
2. `path_traverses_to_many()` detects that at least one path multiplies root rows.
3. The connection pipeline applies `.distinct()`.
4. Django emits an outer JOIN through the membership table plus `SELECT DISTINCT`.
5. Selecting `totalCount` also counts the deduplicated, joined queryset.

The optimizer does not rewrite this shape. `OptimizationPlan.apply()` only applies
`.only()`, `.select_related()`, and `.prefetch_related()`. It is a selection-driven N+1
optimizer, not a predicate compiler.

The target query shape is row-preserving:

- Keep local and forward-single search paths as normal outer predicates.
- Compile every path that crosses a reverse FK, M2M, or generic to-many relation as a
  correlated `Exists(...)` branch.
- OR the direct predicates and `EXISTS` branches together.
- Do not add search-driven `.distinct()`.
- Keep search before ordering, optimization, counting, and pagination.

This removes the outer membership fan-out and makes one root model row remain one SQL row
through counting and pagination.

## Important architecture boundary

The framework currently has two distinct optimization concerns.

### Predicate construction

Filtering and search decide *which root rows qualify*. The relevant seams are:

- `django_strawberry_framework/filters/search.py` after card 049 lands.
- `django_strawberry_framework/filters/sets.py::FilterSet._apply_related_constraints`.
- `django_strawberry_framework/utils/relations.py::path_traverses_to_many`.
- `django_strawberry_framework/connection.py::_pipeline_sync`.
- `django_strawberry_framework/connection.py::_pipeline_async`.

### Selection optimization

The GraphQL selection tree decides *how qualified rows and their selected relations are
loaded*. The relevant seams are:

- `django_strawberry_framework/optimizer/walker.py::plan_optimizations`.
- `django_strawberry_framework/optimizer/plans.py::OptimizationPlan`.
- `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.apply_to`.
- `django_strawberry_framework/connection.py::_finalize_queryset`.

`OptimizationPlan.apply()` intentionally has no `.filter()`, `.exclude()`, `.alias()`,
`.annotate()`, or `.distinct()` directive. It applies:

```python
if self.only_fields:
    queryset = queryset.only(*self.only_fields)
if self.select_related:
    queryset = queryset.select_related(*self.select_related)
if self.prefetch_related:
    queryset = queryset.prefetch_related(*self.prefetch_related)
```

That boundary explains why changing only the current selection walker cannot solve this
case.

Do not post-process `queryset.query` to infer and rewrite Django's internal alias/join tree.
That would rely on private compiler structures, would be fragile across supported Django
versions, and could not reliably recover the original boolean semantics after filters have
been combined.

The correct framework design is:

1. Put reusable row-preserving predicate machinery in the optimizer package if it is meant
   to serve search, generated filters, and future predicate surfaces.
2. Invoke it from the search compiler while the declared paths and OR grouping are still
   explicit.
3. Keep the existing `OptimizationPlan` focused on selection loading.

A suitable new module is
`django_strawberry_framework/optimizer/predicates.py`. It should expose a runtime
predicate/queryset compiler, not add request values to the cached selection plan.

## Why runtime values must not enter `OptimizationPlan`

The optimizer's cross-request plan cache is keyed by GraphQL operation structure, return
type, and selection information. A client will commonly reuse one operation document while
changing only `$search`.

If a cached `OptimizationPlan` captures `"Needle"` from one request, a later execution of
the same operation with `"Other"` could reuse the wrong predicate. Therefore:

- Definition-time metadata may cache path classification and grouping.
- The structural plan may say “this group needs one correlated EXISTS”.
- The actual search string must be bound when the connection pipeline handles the current
  request.
- The selection optimizer plan cache must remain independent of the search value.

## Fast reproduction using the existing fakeshop

### Prerequisites

From the repository root:

```bash
uv sync
```

The default SQLite tier is enough for behavioral and SQL-shape development. Use PostgreSQL
for execution-plan and CPU comparisons.

### Temporary schema activation

Once card 049 is implemented, update
`examples/fakeshop/apps/library/schema.py::BookType.Meta`:

```python
class BookType(DjangoType):
    @classmethod
    def get_queryset(cls, queryset: Any, info: Info) -> Any:
        if _user_is_staff(info):
            return queryset
        return queryset.exclude(
            circulation_status=models.Book.CirculationStatus.REPAIR,
        )

    class Meta:
        model = models.Book
        primary = True
        fields = (
            "id",
            "title",
            "subtitle",
            "circulation_status",
            "shelf",
            "genres",
            "loans",
        )
        interfaces = (relay.Node,)
        filterset_class = filters.BookFilter
        orderset_class = orders.BookOrder
        connection = {"total_count": True}
        search_fields = (
            "title",
            "subtitle",
            "shelf__branch__name",
            "genres__name",
        )
```

Add a root connection to `examples/fakeshop/apps/library/schema.py::Query`:

```python
all_library_search_books: DjangoConnection[BookType] = DjangoConnectionField(
    BookType,
)
```

This uses the existing:

- `Book`, `Genre`, `Shelf`, and `Branch` models.
- `BookType.get_queryset()` visibility rule.
- `BookFilter`.
- `BookOrder`.
- M2M through table.
- live `/graphql/` test harness.
- optimizer extension configured by the aggregate fakeshop schema.

No migration is required.

### Live GraphQL regression fixture

Add the acceptance test to
`examples/fakeshop/test_query/test_library_api.py`. Consumer-visible behavior must be
covered through the live endpoint rather than only through an in-process schema test.

The fixture should create:

1. A visible book whose title does not match but which has *two* matching genres.
2. A visible book whose title matches and which has no matching genre.
3. A hidden `circulation_status="repair"` book with a matching genre.
4. A visible search match excluded only by the explicit filter.
5. A visible non-match.

An implementation-ready test shape is:

```python
@pytest.mark.django_db
def test_to_many_search_is_row_preserving_over_http():
    branch = models.Branch.objects.create(name="Central", city="Boston")
    shelf = models.Shelf.objects.create(
        code="SEARCH",
        topic="Search benchmark",
        branch=branch,
    )

    related_match = models.Book.objects.create(
        title="Related match",
        subtitle="included",
        shelf=shelf,
    )
    related_match.genres.add(
        models.Genre.objects.create(name="Needle Alpha"),
        models.Genre.objects.create(name="Needle Beta"),
    )

    models.Book.objects.create(
        title="Needle in title",
        subtitle="included",
        shelf=shelf,
    )

    hidden_match = models.Book.objects.create(
        title="Hidden related match",
        subtitle="included",
        circulation_status=models.Book.CirculationStatus.REPAIR,
        shelf=shelf,
    )
    hidden_genre = models.Genre.objects.create(name="Needle Hidden")
    hidden_match.genres.add(hidden_genre)
    models.Book.objects.create(
        title="Needle filtered out",
        subtitle="excluded",
        shelf=shelf,
    )

    models.Book.objects.create(
        title="No match",
        subtitle="included",
        shelf=shelf,
    )

    query = """
    query SearchBooks($search: String!, $first: Int!) {
      allLibrarySearchBooks(
        search: $search
        filter: { subtitle: { exact: "included" } }
        orderBy: [{ title: ASC }]
        first: $first
      ) {
        totalCount
        edges {
          node {
            id
            title
          }
        }
        pageInfo {
          hasNextPage
          endCursor
        }
      }
    }
    """

    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(
            query,
            variables={"search": "Needle", "first": 10},
        )

    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["allLibrarySearchBooks"]
    assert result["totalCount"] == 2
    assert [edge["node"]["title"] for edge in result["edges"]] == [
        "Needle in title",
        "Related match",
    ]

    book_queries = [
        query["sql"]
        for query in captured
        if "library_book" in query["sql"].lower()
    ]
    assert len(book_queries) == 2
    for sql in book_queries:
        normalized = sql.upper()
        assert "SELECT DISTINCT" not in normalized
        assert "EXISTS" in normalized
```

Notes:

- The hidden repair row satisfies both search and the explicit filter, so its absence proves
  visibility still runs before search.
- `"Needle filtered out"` satisfies search and visibility but not the explicit filter, so
  its absence proves filter and search intersect.
- `len(book_queries) == 2` is the expected root behavior when `totalCount` and a page are
  both selected: one count query and one page query.
- The query selects no related output field, so no relation prefetch should be needed.
- A result/query-count test alone is insufficient. JOIN-plus-DISTINCT also returns the
  correct two rows and can use the same two query round-trips.
- The SQL-shape assertions are the regression's load-bearing checks.

### Stronger outer-query assertions

An SQL string containing an `EXISTS` subquery will still contain
`library_book_genres`, so a blanket “membership table not in SQL” assertion would be
wrong. Assert that the membership table is absent from the *root query's* alias map.

At the package/compiler test level, inspect:

```python
root_tables = {
    join.table_name
    for join in queryset.query.alias_map.values()
}
assert "library_book_genres" not in root_tables
assert "library_genre" not in root_tables
assert queryset.query.distinct is False
assert "EXISTS" in str(queryset.query).upper()
```

The correlated subquery owns its own `Query` and alias map, so this precisely distinguishes
an outer fan-out from a contained semijoin.

If a helper returns an expression rather than the final queryset, test the queryset after
the connection/search application step where aliases and predicates have been attached.

## ORM-only baseline runnable before card 049

The following command recreates the card-049-equivalent SQL without needing the GraphQL
argument to exist:

```bash
PYTHONPATH=examples/fakeshop \
DJANGO_SETTINGS_MODULE=config.settings \
uv run django-admin shell -c '
from django.db.models import Q
from apps.library.models import Book

value = "Needle"
queryset = Book.objects.filter(
    Q(title__icontains=value)
    | Q(subtitle__icontains=value)
    | Q(shelf__branch__name__icontains=value)
    | Q(genres__name__icontains=value)
).distinct()

print(queryset.query)
print("distinct:", queryset.query.distinct)
print(
    "root tables:",
    sorted({join.table_name for join in queryset.query.alias_map.values()}),
)
'
```

Expected properties:

- `SELECT DISTINCT`.
- An outer JOIN to `library_book_genres`.
- An outer JOIN to `library_genre`.
- `LEFT OUTER JOIN` promotion where the to-many predicate is one arm of an OR and other
  arms must still match books without genres.

This is a single expensive fan-out query, not an N+1 query.

## Target ORM shape

A generic row-preserving prototype can be built from the root model. Rooting the subquery
at the same model avoids hand-coding reverse correlation columns for every relation shape:

```python
from django.db.models import Exists, OuterRef, Q

value = "Needle"
genre_match = (
    Book._base_manager.using(queryset.db)
    .filter(pk=OuterRef("pk"))
    .filter(Q(genres__name__icontains=value))
)

queryset = queryset.alias(
    _dst_search_many_0=Exists(genre_match),
).filter(
    Q(title__icontains=value)
    | Q(subtitle__icontains=value)
    | Q(shelf__branch__name__icontains=value)
    | Q(_dst_search_many_0=True),
)
```

Expected SQL structure:

```sql
SELECT book.*
FROM library_book AS book
INNER JOIN library_shelf AS shelf
  ON book.shelf_id = shelf.id
INNER JOIN library_branch AS branch
  ON shelf.branch_id = branch.id
WHERE (
  UPPER(book.title) LIKE UPPER('%Needle%')
  OR UPPER(book.subtitle) LIKE UPPER('%Needle%')
  OR UPPER(branch.name) LIKE UPPER('%Needle%')
  OR EXISTS (
    SELECT 1
    FROM library_book AS search_book
    INNER JOIN library_book_genres AS membership
      ON search_book.id = membership.book_id
    INNER JOIN library_genre AS genre
      ON membership.genre_id = genre.id
    WHERE search_book.id = book.id
      AND UPPER(genre.name) LIKE UPPER('%Needle%')
    LIMIT 1
  )
)
ORDER BY book.id ASC
```

The exact quoting, aliases, and case-insensitive lookup SQL are backend-specific. The
invariants are:

- The outer query has no membership JOIN.
- The outer query is not `DISTINCT`.
- The membership test is correlated to the outer root primary key.
- Multiple matching genres cannot multiply the outer book row.
- Search remains one OR expression.

## Why not aggregate names into a scalar

A consumer application constrained to a scalar-only search API can annotate a correlated
`StringAgg` of group names and search that alias. That is a reasonable application-level
escape hatch.

The framework owns the declared relation paths and the boolean expression, so it should not
aggregate all child strings. A direct `EXISTS`:

- can stop at the first match;
- does not concatenate child data;
- is portable across supported databases;
- preserves the semantics of an ordinary Django relation lookup;
- avoids a PostgreSQL-specific aggregate dependency;
- generalizes to non-string lookups when reused by generated filters.

## `totalCount` and pagination effects

The connection order is:

1. Normalize the base queryset.
2. Apply type visibility.
3. Apply `FilterSet`.
4. Apply search.
5. Apply `OrderSet`.
6. Append deterministic total ordering.
7. Apply the selection optimizer.
8. Count the post-search, pre-slice queryset if `totalCount` is selected.
9. Apply cursor pagination.

Under JOIN-plus-DISTINCT, `totalCount` generally requires a shape equivalent to:

```sql
SELECT COUNT(*)
FROM (
  SELECT DISTINCT book.<selected columns>
  FROM library_book AS book
  LEFT OUTER JOIN library_book_genres AS membership ...
  LEFT OUTER JOIN library_genre AS genre ...
  WHERE ...
) AS subquery
```

The page query repeats the fan-out and deduplication.

Under the row-preserving design:

```sql
SELECT COUNT(*)
FROM library_book AS book
WHERE <direct predicates OR EXISTS (...)>
```

and the page query uses the same row-preserving predicate before its ordering and limit.

The implementation must retain:

- one edge per parent even when multiple children match;
- correct `totalCount`;
- correct page size;
- stable `endCursor`;
- correct second-page results;
- no hidden-row discovery;
- `filter:` AND search intersection.

## Exact production-style two-surface schema

The motivating application has two consumers over the same `UserSchedule` model:

- Rotations includes group-name search.
- Academic Progress excludes group-name search.

Because `Meta.search_fields` belongs to a `DjangoType`, not an individual root field, use
two registered types.

```python
BASE_USER_SCHEDULE_SEARCH_FIELDS = (
    "user__first_name",
    "user__last_name",
    "user__class_of",
    "user__role__name",
    "rotation__name",
)


def scope_user_schedules_for_request(queryset, info):
    """Apply the shared visibility policy once for both GraphQL views."""
    ...


class AcademicProgressUserScheduleFilter(FilterSet):
    class Meta:
        model = UserSchedule
        fields = {
            "confirmed": ["exact"],
            "start_date": ["gte", "lte"],
        }


class RotationUserScheduleFilter(FilterSet):
    class Meta:
        model = UserSchedule
        fields = {
            "confirmed": ["exact"],
            "start_date": ["gte", "lte"],
        }


class AcademicProgressUserScheduleType(DjangoType):
    @classmethod
    def get_queryset(cls, queryset, info):
        return scope_user_schedules_for_request(queryset, info)

    class Meta:
        model = UserSchedule
        primary = True
        interfaces = (relay.Node,)
        globalid_strategy = "type"
        fields = (
            "id",
            "start_date",
            "end_date",
            "confirmed",
            "user",
            "rotation",
        )
        filterset_class = AcademicProgressUserScheduleFilter
        orderset_class = UserScheduleOrder
        search_fields = BASE_USER_SCHEDULE_SEARCH_FIELDS
        connection = {"total_count": True}


class RotationUserScheduleType(DjangoType):
    @classmethod
    def get_queryset(cls, queryset, info):
        return scope_user_schedules_for_request(queryset, info)

    class Meta:
        model = UserSchedule
        primary = False
        interfaces = (relay.Node,)
        globalid_strategy = "type"
        fields = (
            "id",
            "start_date",
            "end_date",
            "confirmed",
            "user",
            "rotation",
        )
        filterset_class = RotationUserScheduleFilter
        orderset_class = UserScheduleOrder
        search_fields = (
            *BASE_USER_SCHEDULE_SEARCH_FIELDS,
            "user__group_list__group__name",
        )
        connection = {"total_count": True}


@strawberry.type
class Query:
    academic_progress_user_schedules: DjangoConnection[
        AcademicProgressUserScheduleType
    ] = DjangoConnectionField(AcademicProgressUserScheduleType)

    rotation_user_schedules: DjangoConnection[
        RotationUserScheduleType
    ] = DjangoConnectionField(RotationUserScheduleType)
```

Use separate `FilterSet` subclasses for separate Relay owners. Sharing one owner-bound
filterset between two GraphQL type identities is unsafe, particularly when either type has
a custom `get_queryset`. An `OrderSet` may be shared only when finalization resolves its
targets identically for both owners.

Exactly one registered type must be primary. Type-based GlobalIDs make each GraphQL view
refetch as its own type. With the default model-label strategy, a secondary view's ID can
route through the model registry to the primary view instead.

Search paths do not have to be exposed as GraphQL output fields. Group and membership
types are needed only if clients select those relations.

### Rotations operation

```graphql
query RotationSchedules($search: String!, $first: Int!) {
  rotationUserSchedules(
    search: $search
    filter: {
      confirmed: {
        exact: true
      }
    }
    orderBy: [
      {
        startDate: DESC
      }
    ]
    first: $first
  ) {
    totalCount
    edges {
      node {
        id
        startDate
        endDate
        user {
          firstName
          lastName
        }
        rotation {
          name
        }
      }
    }
  }
}
```

### Academic Progress operation

```graphql
query AcademicProgressSchedules($search: String!, $first: Int!) {
  academicProgressUserSchedules(
    search: $search
    first: $first
  ) {
    totalCount
    edges {
      node {
        id
        startDate
        user {
          firstName
          lastName
        }
      }
    }
  }
}
```

The same group-only term should match the Rotations connection and not the Academic
Progress connection. The Academic Progress SQL must contain no group-membership table at
all.

### Academic Progress response-shape caveat

The existing REST Academic Progress endpoint is not merely a schedule list. It transforms
schedules into a user -> graded-course-rotation -> child-rotation hierarchy with calculated
weeks and role statistics.

The second schedule connection above models the source queryset and its search scope. A
faithful GraphQL replacement needs dedicated Academic Progress result and aggregate types;
it should not present the transformed response as if it were a raw `UserSchedule`
connection.

## Proposed reusable predicate optimizer

### Public behavior

No new consumer-facing configuration is required. A developer continues to write:

```python
class Meta:
    search_fields = (
        "title",
        "shelf__branch__name",
        "genres__name",
    )
```

The framework chooses a row-preserving compilation strategy from model metadata.

### Internal structural model

Introduce an immutable definition-time path plan, for example:

```python
@dataclass(frozen=True)
class SearchPathPlan:
    direct_paths: tuple[str, ...]
    to_many_groups: tuple[ToManyPathGroup, ...]


@dataclass(frozen=True)
class ToManyPathGroup:
    first_many_prefix: str
    relation_chain: tuple[str, ...]
    paths: tuple[str, ...]
```

`first_many_prefix` is the path through the first row-multiplying hop:

- `genres__name` -> `genres`
- `user__group_list__group__name` -> `user__group_list`
- `shelf__books__genres__name` -> `shelf__books`

The first-many prefix determines whether the path must leave the outer query. It is not, by
itself, a safe grouping key.

Group paths only when their complete relation chain is identical and only the terminal
scalar differs, for example `genres__name` and `genres__description`. Keep
`genres__books__title` in a separate `EXISTS` even though it shares the first `genres` hop.
Combining divergent later relation chains can create a child cross-product inside the
subquery. When compatibility is uncertain, one `EXISTS` per declared path is the correct
fallback.

### Runtime compiler shape

The runtime helper should accept the current queryset because it needs the current database
alias and model:

```python
def apply_row_preserving_search(
    queryset: models.QuerySet,
    path_plan: SearchPathPlan,
    value: str,
) -> models.QuerySet:
    ...
```

For each direct path, build the ordinary `Q(<path>__icontains=value)`.

For each to-many group:

1. Start from `queryset.model._base_manager.using(queryset.db)`.
2. Correlate `pk=OuterRef("pk")`.
3. OR that group's `<path>__icontains=value` predicates inside the subquery.
4. Wrap the subquery in `Exists`.
5. Attach it with a package-reserved alias such as `_dst_search_many_0`.
6. OR `Q(_dst_search_many_0=True)` into the outer predicate.

Use `_base_manager` for the correlated root because the outer queryset has already applied
the consumer manager and visibility policy. The inner root row exists only to evaluate the
relation predicate for the already-qualified outer primary key; reapplying a filtered
default manager could introduce false negatives.

Respect `queryset.db` so routers and multi-database querysets do not cross aliases.

### Why alias the `Exists`

Using `.alias()` rather than `.annotate()`:

- keeps the boolean out of the selected columns;
- gives the OR expression a stable `Q(alias=True)` representation;
- avoids relying on expression-combination behavior varying across Django versions;
- makes package-reserved names inspectable in tests;
- composes with the later `.only()` selection plan.

The alias namespace must use the package's reserved `_dst_` prefix and detect or avoid
collisions with consumer aliases.

### Relation metadata helper

`path_traverses_to_many()` returns only a boolean. Add a companion helper in
`django_strawberry_framework/utils/relations.py`, for example:

```python
@lru_cache(maxsize=2048)
def first_to_many_path_prefix(model: type, field_path: str) -> str | None:
    ...
```

It should reuse:

- `relation_kind()`;
- `is_many_side_relation_kind()`;
- Django model metadata traversal;
- the same unresolved terminal behavior as `path_traverses_to_many()`.

Then implement `path_traverses_to_many()` in terms of the companion helper or a shared
single traversal so relation-shape logic cannot drift.

The shared traversal should also expose the complete relation chain used as the safe
subquery grouping key. Do not reconstruct it independently in the predicate optimizer.

Cover:

- forward FK/OneToOne chains;
- reverse FK;
- forward M2M;
- reverse M2M;
- generic many-side relations;
- reverse OneToOne as single-valued;
- invalid/unresolvable paths;
- transforms/lookups after the terminal model field.

## Detailed implementation plan

### Phase 1: Freeze the regression

Add failing tests before changing compilation:

- A path-plan unit test classifies local/forward paths as direct.
- Reverse-FK and M2M paths receive a first-many prefix.
- Two paths with the same complete relation chain form one group.
- Divergent relation chains form separate groups, including paths that share their first
  to-many hop.
- One parent with two matching children returns one edge.
- A local-field match with no children still returns.
- A hidden matching row does not return.
- `filter:` and search intersect.
- `totalCount` and the page both equal the unique parent count.
- Root `alias_map` has no membership or child-table joins.
- Root `query.distinct` is false.
- SQL contains `EXISTS`.

The live behavior test belongs in `examples/fakeshop/test_query/`. Internal path grouping
and alias-map inspection belong in package tests, likely
`tests/filters/test_search_fields.py` and a focused optimizer predicate test module.

### Phase 2: Add relation-prefix metadata

Update:

- `django_strawberry_framework/utils/relations.py`.
- `tests/utils/test_relations.py`.

Implement and cache first-many-prefix discovery. Keep relation taxonomy single-sited.

Do not cache a model instance, queryset, search value, or database alias.

### Phase 3: Add the reusable row-preserving compiler

Create:

- `django_strawberry_framework/optimizer/predicates.py`.
- `tests/optimizer/test_predicates.py`.

Responsibilities:

- immutable path-plan structures;
- definition-time grouping;
- runtime `Exists` construction;
- database-alias preservation;
- package-reserved alias allocation;
- direct-only fast path with no aliases/subqueries;
- empty-value no-op;
- composable OR expression;
- no `.distinct()`.

Keep this module independent of Strawberry AST selections. It is an ORM predicate
optimization utility consumed by higher-level framework surfaces.

### Phase 4: Integrate card-049 search

Update the card-049 implementation points:

- `django_strawberry_framework/filters/search.py`.
- `django_strawberry_framework/types/definition.py`.
- `django_strawberry_framework/types/finalizer.py`.
- `django_strawberry_framework/connection.py`.
- search tests and live fakeshop tests.

Replace `search_requires_distinct: bool` with the immutable structural path plan.

At finalization:

1. Validate all declared paths.
2. Classify and group them.
3. Store the frozen plan on `DjangoTypeDefinition`.

At runtime:

1. Ignore `None` and whitespace-only values according to card-049 semantics.
2. Bind the raw current request value.
3. Call the row-preserving compiler.
4. Do not call `.distinct()`.

Retain the pipeline:

```text
visibility -> filter -> search -> orderBy -> deterministic order -> selection optimizer
```

Do not move search after the selection optimizer or after pagination.

### Phase 5: Generalize generated to-many filters

Audit generated leaf filters that currently set `distinct=True` through
`path_traverses_to_many()`. Where the boolean semantics are equivalent, route them through
the same row-preserving predicate compiler.

Use `FilterSet._apply_related_constraints()` as a semantic precedent: it already avoids
outer row multiplication with a parent-PK subquery instead of mutating the consumer-visible
queryset with `.distinct()`.

This phase is required for a coherent developer experience. Search should not become
row-preserving while an equivalent generated relation filter silently retains the same
fan-out regression.

Do not mechanically rewrite every `.distinct()` in the filtering subsystem. First prove
that each caller represents an existential relation predicate rather than consumer-requested
deduplication or another semantic.

### Phase 6: Complete pagination and backend coverage

Add acceptance coverage for:

- `first` page without `totalCount`;
- `first` page with `totalCount`;
- second offset-cursor page;
- keyset connection if the search fixture type supports `Meta.cursor_field`;
- sync and async connection pipelines;
- SQLite;
- PostgreSQL;
- multi-database alias preservation;
- consumer-applied `.only()` and `.defer()` compatibility;
- search plus selected relations, confirming the selection optimizer still adds only the
  expected `select_related`/`prefetch_related` work.

### Phase 7: Document and benchmark

Update the card-049 spec before implementation is considered complete:

- Replace conditional DISTINCT as the prescribed strategy.
- Document `EXISTS` compilation.
- Document path grouping.
- Document the selection-optimizer boundary.
- Update SQL examples and definition-of-done assertions.

Add a benchmark script only if it produces repeatable plan artifacts and reports data shape
with the result. Do not make wall-clock thresholds part of the normal test suite.

## Test matrix

### Relation shapes

- Local scalar.
- Forward FK scalar.
- Multi-level forward FK scalar.
- Reverse FK scalar.
- Forward M2M scalar.
- Reverse M2M scalar.
- GenericRelation scalar.
- Reverse OneToOne scalar.
- Mixed direct and to-many OR.
- Multiple paths with the same complete relation chain.
- Multiple independent to-many prefixes.
- A shared first to-many hop followed by divergent later relation chains.

### Behavioral cases

- Null search: unchanged queryset.
- Empty search: unchanged queryset.
- Whitespace-only search: unchanged queryset.
- One direct match.
- One related match.
- Multiple related matches for one parent.
- Direct match with no related rows.
- Related match hidden by root visibility.
- Search plus filter intersection.
- Search plus explicit ordering.
- Search plus selected relations.
- No matching rows.
- `%`, `_`, and quote characters remain literal under Django lookup escaping.

### SQL invariants

- Direct-only search creates no `EXISTS`.
- Direct-only search creates no search-driven `DISTINCT`.
- To-many search creates `EXISTS`.
- Root alias map excludes the to-many join tables.
- Root query is not distinct.
- Search aliases are not selected columns.
- Count SQL has no distinct-wrapper subquery.
- Page SQL has no outer fan-out.
- Database alias is preserved.

### Pagination invariants

- Duplicate children never duplicate edges.
- `totalCount` is the number of root rows.
- `first: N` returns at most N unique roots.
- `hasNextPage` reflects root rows, not joined child rows.
- Cursors replay correctly for a fixed search value.
- Changing the search value between pages has the same contract as changing `filter:`.

## PostgreSQL profiling

### Start the local PostgreSQL tier

```bash
docker compose -f docker-compose.postgres.yml up -d
uv sync --group pg
export FAKESHOP_PG_DSN="postgres://fakeshop:fakeshop@127.0.0.1:5432/fakeshop"
```

Run the focused tests:

```bash
FAKESHOP_PG_DSN="$FAKESHOP_PG_DSN" \
uv run pytest -n0 \
  examples/fakeshop/test_query/test_library_api.py \
  tests/filters/test_search_fields.py \
  tests/optimizer/test_predicates.py
```

### Benchmark data shape

Use a disposable test database and record:

- root-book count;
- average and maximum genres per book;
- percentage of books matching by title;
- percentage matching by genre;
- number of matching genres per matching book;
- PostgreSQL and Django versions;
- warm-cache versus cold-cache run;
- indexes present.

A useful stress shape is:

- 20,000 books;
- 20 genres per book;
- 400,000 through rows;
- a small set of title matches;
- several genres matching the term for each related match.

Create books and through rows with `bulk_create()`. Do not call `.add()` in a large loop.

### Compare plans

Capture both query variants with:

```python
queryset.explain(
    analyze=True,
    buffers=True,
    format="json",
)
```

Compare:

- execution time;
- planning time;
- shared hit/read blocks;
- temporary blocks;
- rows emitted before deduplication;
- Sort, Unique, HashAggregate, or distinct-subquery nodes;
- semijoin/EXISTS execution;
- loops and rows on the through table;
- count-query plan;
- page-query plan.

Do not encode a universal “EXISTS must be X% faster” assertion. PostgreSQL can choose
different equivalent plans as statistics and versions change. Gate structural invariants
in tests and use `EXPLAIN (ANALYZE, BUFFERS)` as evidence for the performance assessment.

For `%term%` `icontains`, a trigram index may be needed to optimize text matching at scale.
That is separate from the row-multiplication defect: test the JOIN/DISTINCT versus EXISTS
shape under the same index configuration.

## Validation commands

After implementation edits:

```bash
uv run ruff format .
uv run ruff check --fix .
uv run python scripts/check_trailing_commas.py --check
git diff --check
```

Focused tests:

```bash
uv run pytest -n0 \
  tests/utils/test_relations.py \
  tests/optimizer/test_predicates.py \
  tests/filters/test_search_fields.py \
  examples/fakeshop/test_query/test_library_api.py
```

Then run the full SQLite suite:

```bash
uv run pytest
```

Run the focused PostgreSQL tier with the command in the profiling section. The final change
must preserve 100% package coverage.

## Acceptance criteria

The work is complete only when all of the following are true:

1. A mixed direct/to-many `Meta.search_fields` declaration requires no consumer annotation,
   subquery, or custom resolver.
2. A parent with multiple matching children appears once.
3. Root SQL has no to-many JOIN introduced by search.
4. Root SQL has no search-driven `SELECT DISTINCT`.
5. The related branch compiles to a correlated `EXISTS`.
6. `totalCount` counts the row-preserving queryset directly.
7. Offset and keyset pagination operate on root rows.
8. Visibility is applied before search.
9. `filter:` and search intersect.
10. Direct-only search retains its simple query shape.
11. SQLite and PostgreSQL behavior match.
12. Database routing is preserved.
13. Selection-driven N+1 optimization remains unchanged and independently testable.
14. Equivalent generated to-many filter paths use the shared row-preserving machinery
    wherever their semantics are existential.
15. The card-049 spec no longer promises JOIN-plus-DISTINCT as the implementation strategy.

## Rejected approaches

### Keep JOIN-plus-DISTINCT

Correct rows do not imply an acceptable query. It preserves the fan-out and can force both
the count and page query to deduplicate.

### Add more `prefetch_related()`

Prefetching affects selected relation loading after root rows qualify. It cannot remove
filter JOINs already present in the root query.

### Teach the selection walker to inspect `queryset.query`

This is a late private-API rewrite with insufficient semantic information. The search
compiler already has exact paths and boolean grouping and should emit the correct predicate
the first time.

### Put the search value in the cached optimization plan

GraphQL variables change across executions of the same operation. Capturing a value in a
cross-request plan risks returning results for a previous request.

### Use a test-only SQL substitution

The production abstraction is wrong if it creates a fan-out and repairs cardinality with
DISTINCT. Tests must pin the production compiler's row-preserving behavior.

### Use `StringAgg` in the generic framework

It is PostgreSQL-specific, processes all child strings, and is unnecessary when the
framework can express the existential relation predicate directly.

### Apply `.distinct("pk")`

That is PostgreSQL-specific, interacts with ordering constraints, and still retains the
outer fan-out.

## Handoff checklist

Before beginning:

- Read this guide.
- Read the card-049 spec.
- Confirm the working tree and preserve unrelated changes.
- Run the ORM-only baseline and save the SQL.

During implementation:

- Add failing behavior and SQL-shape tests first.
- Keep definition-time classification separate from request-time value binding.
- Preserve the visibility/filter/search/order pipeline.
- Audit every changed queryset for N+1 behavior independently from this fan-out issue.
- Avoid branch, commit, or unrelated documentation changes unless the maintainer requests
  them.

Before review:

- Run formatting, lint, scaffold, and diff checks.
- Run focused SQLite tests.
- Run the full suite.
- Run focused PostgreSQL tests.
- Attach before/after SQL.
- Attach before/after PostgreSQL JSON plans for the same fixture and indexes.
- State query counts separately from query shape.
- Confirm no `DISTINCT` or root membership aliases remain.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[search-fields-spec]: spec-049-search_fields-0_1_2.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
