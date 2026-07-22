# Adversarial review: row-preserving predicates Part 1

## Verdict

Do not implement the [Part 1 plan][part1-plan] unchanged. The architectural direction is
correct: predicate construction belongs outside the selection plan, correlated `EXISTS`
is the right row-preserving primitive, and the final owning model must be the metadata
root. However, the plan is not implementation-ready because its integration seam is
misidentified, its negation contract has a demonstrated result-set counterexample, and
its current-state model omits the already-public flattened `RelatedFilter` path.

The smallest high-quality revision is not to retreat to `DISTINCT`. It is to make the
compiler preserve one complete django-filter invocation inside the correlated subquery,
then use a separate low-level helper for card 049's future same-value OR grouping.

## Blocking findings

### 1. `_apply_lookups` is not the general `distinct` seam

The Purpose section says
`django_strawberry_framework/filters/base.py::_apply_lookups` consumes the generated
filter's `distinct` flag. That is true only for the package's custom filters that call
that helper. An ordinary generated `CharFilter`, `NumberFilter`, or other upstream filter
executes `django_filters.filters.Filter.filter`, which independently performs:

1. the empty-value short circuit;
2. `qs.distinct()` when `self.distinct`;
3. `self.get_method(qs)(**{lookup: value})`.

The framework's actual flat-leaf integration seam is
`django_strawberry_framework/filters/sets.py::FilterSet.filter_queryset`, and it currently
delegates all leaves wholesale to
`django_filters.filterset.BaseFilterSet.filter_queryset` before adding the logic tree.
Changing `_apply_lookups` cannot reroute an ordinary generated `icontains` leaf and would
leave the headline defect intact.

The plan must choose and specify the interception mechanism. The recommended mechanism is
a framework-owned flat-leaf applicator called by
`django_strawberry_framework/filters/sets.py::FilterSet.filter_queryset`. It should mirror
upstream's loop exactly:

- iterate `self.form.cleaned_data` in order;
- call the original filter unchanged for non-candidates;
- route a proven candidate through the correlated subquery adapter;
- retain upstream's `QuerySet` return assertion and message;
- then run the existing
  `django_strawberry_framework/filters/sets.py::FilterSet._evaluate_logic_tree` step.

This preserves the direct `FilterSet(...).qs` path as well as `apply_sync` and
`apply_async`. Replacing filter instances dynamically or post-processing
`queryset.query` would be a weaker and more fragile abstraction.

Required regression coverage must include an ordinary generated `CharFilter`; tests only
through `IntegerRangeFilter`, `GlobalIDMultipleChoiceFilter`, or `_apply_lookups` would
not prove the common path.

### 2. One `NOT EXISTS` for a negated multi-lookup leaf changes Django semantics

Slice B says `negated=True` should return `~Q(<alias>=True)`, and the investigation
grounding says predicates from the same leaf may share one subquery body. Those two rules
are not jointly valid for a filter invocation that calls `exclude()` with multiple
lookup kwargs.

This was reproduced on Django 6.0.5 with a parent-to-children reverse FK. Given:

- `single-in-range` with child value `{5}`;
- `split-across-rows` with child values `{0, 10}`;
- `outside` with child value `{20}`;
- `empty` with no children;

the baseline:

`Parent.objects.exclude(children__value__gte=1, children__value__lte=9)`

returns `outside` and `empty`. Django compiles the predicate as the complement of two
independent existence tests: the split-row parent is excluded because one child satisfies
`gte` and another child satisfies `lte`.

A single `NOT EXISTS` whose body contains both comparisons returns
`split-across-rows`, `outside`, and `empty`, because no one split-row child satisfies both
comparisons. That is a result-set regression. The package already has a relevant
multi-lookup implementation in
`django_strawberry_framework/filters/base.py::IntegerRangeFilter.filter`.

The safe compiler contract is one of:

1. Correlate an inner queryset to the outer root, invoke the original filter operation on
   that inner queryset—including its actual `filter()` or `exclude()` boolean
   semantics—and attach positive `Exists(filtered_inner)` to the outer queryset.
2. Accept a structured boolean predicate tree rich enough to represent Django's separate
   existence branches and negation placement exactly.

The first option is substantially safer for generated filters because it also preserves
empty-list handling, GlobalID decoding, integer-range decomposition, and future upstream
filter behavior without reimplementing each filter class in the compiler.

The scalar `negated: bool` API may remain only for an explicitly atomic predicate whose
single-branch semantics are proven. It is not a sufficient abstraction for a general
django-filter invocation.

Required tests:

- the split-across-rows negated-range case above;
- positive range comparisons that must bind to the same related row;
- `exclude=True` with one lookup;
- `isnull=True` and `isnull=False`, including a parent with no related rows;
- a logical `not` input through
  `django_strawberry_framework/filters/sets.py::FilterSet._q_for_branch`, proving branch
  negation remains outside the child queryset and is not incorrectly pushed into a leaf.

### 3. The current-state model misses flattened `RelatedFilter` leaves

The plan says `FilterSet.filter_for_field` stamps `distinct=True` on any generated path
that crosses a to-many hop. That is not true after related-filter expansion.

`django_strawberry_framework/filters/sets.py::_expand_related_filter` deep-copies a filter
that was generated against the child model and only then prefixes its `field_name`.
Classification is not rerun against the owning root model. In the current fakeshop:

- `BookFilter.get_filters()["genres__name__icontains"]` has
  `field_name="genres__name"` and `distinct=False`;
- `BookFilter.get_filters()["loans__note__icontains"]` has
  `field_name="loans__note"` and `distinct=False`.

Those are public fields by default:
`django_strawberry_framework/conf.py::hide_flat_filters_setting` defaults
`HIDE_FLAT_FILTERS` to `False`, and
`django_strawberry_framework/filters/inputs.py::_build_input_fields` emits the flattened
GraphQL fields. A flat `genresName` or `booksTitle` filter can therefore duplicate root
rows today without even the correctness repair of `DISTINCT`.

Part 1 consequently has two shipped defects, not one:

1. Explicit deep `Meta.fields` paths are stamped `distinct=True`: correct rows, expensive
   outer fan-out.
2. Flattened `RelatedFilter` children are prefixed after generation and remain
   `distinct=False`: duplicate rows and corrupted counts are possible.

The candidate decision must run against the final filter path and the final owning
`FilterSet._meta.model`, after expansion. It must not trust the child filter's original
`distinct` value or path classification.

The strongest no-migration live fixture already exists:

- use `GenreFilter.books` from
  `examples/fakeshop/apps/library/filters_genre.py::GenreFilter`;
- query `allLibraryGenresConnection`, which already exposes `totalCount`;
- use the public flat input `booksTitle`, not the nested `books` input;
- give one genre two matching books;
- assert one edge and `totalCount == 1`.

The nested `books: {title: ...}` spelling is only a control:
`django_strawberry_framework/filters/sets.py::FilterSet._apply_related_constraints`
already makes it row-preserving through a parent-PK subquery. A live test that uses only
the nested spelling does not exercise the new compiler and cannot earn its acceptance
coverage.

### 4. “Existential-safe” has no enforceable provenance rule

Slice C intends to preserve consumer-requested `distinct`, consumer `method=`, and
ambiguous behavior. The current `Filter` object does not carry enough provenance to make
those decisions:

- after `FilterSet.filter_for_field` assigns `requires_distinct`, the boolean does not say
  whether the value came from the consumer, django-filter's generated filter class, or the
  framework's to-many stamp;
- an explicitly declared filter can have `method is None` while overriding `filter()`;
- `Meta.filter_overrides` can generate a consumer-supplied filter class whose behavior is
  not a standard single ORM lookup;
- a flattened `RelatedFilter` leaf is generated, but the owning class did not create it
  through its own `filter_for_field`.

“No `method=`” is therefore necessary but not sufficient, and “`distinct` was not already
set upstream for another reason” cannot be evaluated after the current assignment.

The revised plan must define immutable candidate metadata and where it is built. A robust
shape is a class-level mapping keyed by final form-filter name, produced after
`get_filters()` expansion, containing:

- the final classified path rooted at the owning model;
- the filter origin: direct generated leaf, expanded generated leaf, or declared/custom;
- the pre-framework distinct provenance;
- whether the filter class is eligible for inner-query invocation.

Declared filters, `filter_overrides`, and custom filter subclasses should fail closed
unless their entire invocation is deliberately supported. Do not infer safety from a
class name or from `method is None`.

Required tests:

- explicit `distinct=True` remains untouched;
- explicit custom filter subclass with no `method=` remains untouched;
- `Meta.filter_overrides` remains untouched;
- generated direct deep path is optimized;
- generated flattened related path is optimized;
- a copied expanded filter is classified against the root model, not the child model.

## Major plan revisions

### 5. Separate model-path classification from lookup validation

`classify_path(model, field_path)` currently has two incompatible advertised contracts:
it classifies a model-field path, but it also identifies trailing
lookup/transform segments. The real call sites do not provide one uniform string:

- `FilterSet.filter_for_field` receives `field_name` and `lookup_expr` separately;
- card 049 stores a declared field path and adds `icontains` later;
- relation-terminal filters need the relation descriptor plus `isnull`;
- an explicit transformed lookup can carry multiple transform segments before its final
  lookup.

Define the boundary explicitly. Either:

- classify only the model path and validate a separate lookup expression against the
  returned terminal field; or
- accept a complete lookup string everywhere and have callers assemble it through one
  named helper.

The first option matches the existing APIs more naturally. In either design:

- retain the terminal relation descriptor for relation-terminal filters; `None` discards
  information needed to validate and compile them;
- after each transform, validate the next segment against the transform's
  `output_field`, not the original field;
- decide explicitly whether the valid ORM alias `pk` is accepted or deliberately outside
  this helper's vocabulary;
- name the strict exception type and message contract;
- make `path_traverses_to_many` catch only that typed resolution failure to retain its
  lenient legacy behavior.

Add chained-transform and relation-terminal execution tests, not only classifier-output
tests.

### 6. The composite-PK branch is currently unsupported complexity

Slice B states that `pk=OuterRef("pk")` is unsafe for composite primary keys. On the
validated Django 6.0.5 runtime, it compiled correctly to a tuple comparison:

`(inner.student_id, inner.course_id) = (outer.student_id, outer.course_id)`.

Individual per-column correlations also compiled, but the plan has not demonstrated why
they are required. `django_strawberry_framework/utils/relations.py::has_composite_pk`
currently exists for an unrelated FK-id projection rule; reusing it does not establish a
predicate-correlation requirement.

Before adding a second correlation implementation:

1. pin `pk=OuterRef("pk")` compilation and execution on both supported Django lines, 5.2
   and 6.0;
2. retain per-column expansion only if one supported runtime fails or a documented
   backend produces wrong SQL;
3. if expansion remains, test custom `db_column` values and derive fields from
   `_meta.pk_fields`, never by naming convention.

The simpler, framework-native `pk` comparison should remain the default unless the
supported-version matrix proves it incorrect.

### 7. Alias collision checks must cover Django's full annotation namespace

Allocating only against `queryset.query.annotations` does not satisfy “collision-checked,
never guessed.” `QuerySet.alias()` also rejects aliases that collide with model field
names, and query state can carry legacy `extra(select=...)` names or projected names.
The `_dst_` prefix is a package convention, not an enforced prohibition on consumer model
fields.

The allocator must account for at least:

- model field names and attnames;
- existing annotations and aliases;
- `extra_select` names;
- names already selected/projected where Django treats them as conflicts;
- every alias allocated earlier in the same compiler call.

Prefer a deterministic allocator that advances until Django's effective alias namespace
is free. Add tests for a colliding consumer alias, a colliding model field, multiple
compiler invocations on the same queryset, and coexistence with `_dst_order_*` and window
annotations.

### 8. Keep the low-level compiler neutral; put filter semantics in an adapter

Slice B currently bakes “OR the group's predicates” into the reusable compiler. That is
card 049 search behavior, not the neutral primitive Part 1's generated-filter cut-over
needs. Generated leaves are sequential django-filter invocations, and joining two active
leaves merely because their relation chains match would break Django's cross-row
multi-`filter()` semantics.

Use three layers:

1. `utils/relations.py` owns immutable model-path classification.
2. `optimizer/predicates.py` owns correlation, alias allocation, and attachment of
   `Exists` for an already-defined inner predicate/queryset.
3. `filters/sets.py` owns the django-filter adapter: it builds the correlated inner root,
   applies one original eligible filter invocation to that inner root, and asks the
   low-level helper to attach the result.

Card 049 can later build same-value OR groups and call layer 2 directly. This keeps
`optimizer/predicates.py` independent of django-filter and Strawberry while preventing a
search-specific grouping rule from becoming the filter subsystem's accidental boolean
model.

### 9. Clarify runtime guards and claims about count shape

The combinator preflight should run only when a non-empty predicate requires queryset
mutation; the documented empty-input identity must win first. The plan should also justify
the exception family. A combined queryset is runtime query state, so
`ConfigurationError` is not self-evidently more accurate than `OptimizerError` or a
predicate-specific typed error.

The count invariant must be phrased as “the compiler adds no distinct wrapper.” A consumer
queryset may already be distinct, grouped, projected, or annotated and legitimately
require a count subquery. Tests should start from a plain queryset when asserting flat
`COUNT(*)`, and separate that compiler-owned invariant from compatibility tests over
consumer-shaped querysets.

## Required acceptance matrix before cut-over

### Behavioral equivalence

For every supported candidate, compare baseline and rewritten primary-key sets before
removing the old `distinct` behavior:

- reverse FK, forward M2M, reverse M2M, and `GenericRelation`;
- duplicate matching children and no matching children;
- no related rows;
- nullable child field with `isnull=True` and `isnull=False`;
- two active leaves on the same relation that may match different children;
- a single positive multi-lookup invocation that must match one child;
- the negated split-row counterexample;
- `in=[]`, mixed valid/invalid integer `in`, and GlobalID list handling;
- direct, `and`, `or`, and `not` GraphQL filter-tree positions;
- explicit consumer `distinct`, method filters, custom filter classes, and
  `filter_overrides`.

### SQL shape

On a plain root queryset:

- the outer `alias_map` excludes membership and child tables;
- `query.distinct` is false;
- `EXISTS` is present;
- generated aliases are absent from selected columns;
- count SQL has no compiler-introduced distinct wrapper;
- separate active leaves produce separate existence branches;
- the database alias survives;
- alias collisions advance deterministically.

### Live fakeshop proof

Use the existing `Genre -> books` reverse-M2M surface over
`allLibraryGenresConnection`:

- seed one genre linked to two books whose titles both match;
- call the flat `booksTitle` filter;
- select `totalCount`, edges, and page info;
- assert one genre edge and a root count of one;
- include the nested `books` spelling as a row-preserving control, not as the primary
  regression.

This earns the production path through real GraphQL input generation and connection
counting without adding models or migrations.

## Recommended revised sequence

1. Freeze both current defects: direct deep generated paths with `distinct=True`, and
   flattened related paths with `distinct=False`.
2. Define final-path candidate metadata and provenance after filter expansion.
3. Add the strict path classifier with a separate, explicit lookup-validation contract.
4. Add a neutral correlated-`EXISTS` attachment primitive and complete alias allocator.
5. Add the FilterSet leaf adapter that invokes one original eligible filter against the
   correlated inner root.
6. Prove positive, negated, multi-lookup, null, and cross-row equivalence before changing
   production routing.
7. Cut over direct and flattened generated leaves.
8. Add the live `booksTitle` connection regression and SQL-shape assertions.
9. Validate Django 5.2/6.0, SQLite/PostgreSQL, and multi-database behavior.
10. Leave search grouping and the `search:` surface to card 049 as planned.

With these revisions, Part 1 remains the root-cause fix described by the
[reproduction guide][repro] and supplies the correct neutral substrate for
[spec 049][spec-049] without changing shipped filter semantics.

# Adversarial review: spec 049 after the Part 1 anchor pass

## Verdict

Do not implement [spec 049][spec-049] unchanged. Its central direction is sound:
`Meta.search_fields` belongs on the exact `DjangoTypeDefinition`, request values must stay
out of `OptimizationPlan`, search must run before ordering/pagination, and to-many paths
must compile through the neutral row-preserving predicate layer. The GlobalID setting
placement raised in the review prompt is also sound and is not a request-time performance
problem.

The spec nevertheless has four blocking architecture gaps:

1. it assigns path validation to both `get_model_field` and the new strict classifier;
2. its advertised `build_search_q(search_fields, value)` cannot implement its own
   to-many contract without the queryset and frozen path plan;
3. “visibility before search” protects only root rows, while relational search can still
   qualify a root through a related row hidden by the related type's visibility hook;
4. search has no permission contract and the planned fakeshop activation demonstrably
   bypasses an existing field-filter permission gate.

Those are semantic/API decisions, not implementation details. Resolve them in the spec
before production work begins. The remaining findings are major regression, performance,
test-placement, and documentation gaps that should be incorporated into the same revision.

## Blocking inconsistencies and contradictions

### 1. Path validation has two owners

Slice 1 and Decision 2 make `validate_search_fields` resolve paths with
`django_filters.utils.get_model_field`. Slice 2, Decision 7, and the helper-reuse section
then require the strict structured classifier from
`django_strawberry_framework/utils/relations.py`. This means every declaration is walked
twice under two contracts that already disagree on important cases:

- the ORM alias `pk`;
- a relation reached as the terminal segment;
- forward `GenericForeignKey` versus reverse `GenericRelation`;
- transforms and lookup validation;
- the typed error and offending-segment message;
- self-referential and MTI paths.

The pre-card groundwork exists specifically to make this metadata single-sited. Search
should call one helper that classifies the model path, rejects an invalid terminal for
search, validates `icontains` against that terminal, and returns the frozen path plan.
`get_model_field` should not be a second acceptance oracle. A separate declaration-shape
normalizer may still reject non-list/tuple values, empty entries, and reserved prefixes.

Recommended contract:

1. `_normalize_search_fields(meta_value)` handles container/string shape only.
2. `build_search_path_plan(type_name, model, normalized_paths)` calls the strict relation
   classifier and lookup validator exactly once per unique path.
3. The completed immutable plan is assigned to the definition only after every path
   succeeds, keeping finalization retry-safe.

### 2. `build_search_q(search_fields, value)` contradicts row-preserving compilation

The spec repeatedly defines Slice 1's runtime primitive as
`build_search_q(search_fields, value)`, returning one OR'd `Q`. That signature can only
produce direct Django traversal predicates. It has neither:

- the current queryset/model/database alias needed by `correlated_inner_root`;
- the frozen direct/to-many classification;
- an alias-allocation surface for `attach_exists`;
- a queryset on which to attach those aliases.

If it emits `Q(genres__name__icontains=value)`, it reintroduces the exact outer fan-out the
card is designed to remove. If Slice 3 silently replaces it with a queryset compiler, then
Slice 1's API and tests describe a helper that is not the real runtime abstraction.

Use one honest runtime entry point, for example
`apply_search(queryset, path_plan, value) -> QuerySet`. It should:

- return the original queryset by identity for inactive input;
- construct direct `Q` branches;
- build and attach the to-many `Exists` branches through
  `optimizer/predicates.py`;
- apply the final OR once;
- contain no Strawberry or connection logic.

A smaller `build_direct_search_q(paths, value)` may exist as an internal helper, but it
must not be presented as the complete search compiler.

### 3. Root visibility does not imply related-row visibility

Decision 6 says visibility runs before search so search “never sees” hidden rows. That is
true only for rows of the connection's root model. It is false for relational paths.

The planned correlated inner root starts from the outer model's `_base_manager` and
correlates its primary key. A predicate such as `genres__name__icontains=value` or
`user__group_list__group__name__icontains=value` then traverses the related tables as raw
ORM relations. It does not invoke the related `DjangoType.get_queryset`, an explicit
`RelatedFilter.queryset`, or the related FilterSet's permission gates. A visible parent can
therefore appear only because a related row hidden on its own GraphQL surface matched the
search. That is a related-data existence oracle.

This is especially important because `apply_cascade_permissions` intentionally covers
forward single-valued edges, not arbitrary reverse/M2M search traversals. The products
fixture's forward category paths happen to be cascade-protected; a library
`Genre -> books` or `Book -> genres` to-many fixture is not proof of the same security
property.

The spec must choose one explicit contract:

- **Visibility-aware relational search.** Resolve the exact related type for each hop and
  compose its sealed visibility queryset into the predicate. This likely makes search
  colored: a related type may have async `get_queryset`, so Decision 6's “one colorless
  helper” claim would need revision and the sync/async pipelines would need the same kind
  of derivation split already used by `FilterSet`.
- **Declaration-as-authorization.** State plainly that `Meta.search_fields` grants search
  access to those database paths independently of related GraphQL visibility, and that
  authors must not declare paths through sensitive related rows. Then narrow every claim
  from “hidden rows” to “hidden root rows” and add a security warning plus a live proof of
  the chosen behavior.

Silence is not acceptable. The current prose promises the stronger first contract while
the proposed compiler implements the second.

### 4. Search bypasses existing filter permission gates

Decision 1 explicitly says search has no permission gates. That is not automatically
wrong, but it conflicts with the package's layered-permission expectations and with the
exact fixture the spec activates:

- `examples/fakeshop/apps/products/filters.py::CategoryFilter.check_name_permission`
  permits filtering by category name only to staff;
- Slice 4 activates `CategoryType.Meta.search_fields = ("name", "description")`;
- an anonymous caller can then probe category names through `search:` even though the
  equivalent `filter: {name: ...}` operation is denied.

The spec must define whether a search declaration is a distinct public authorization
grant or whether search must honor field-level filter/search gates. Reusing FilterSet
methods mechanically is not necessarily correct—a type can declare search with no
FilterSet, and `icontains` search is not the same input surface—but shipping an accidental
bypass is worse.

Reasonable designs include a type-level `check_search_permission` plus optional per-path
gates, or an explicit “search fields are public regardless of FilterSet gates” contract.
Whichever is selected needs anonymous/staff live tests using the existing Category name
gate. If a permission hook may touch the database, the claim that the search step is
colorless must again be narrowed.

### 5. Whitespace no-op semantics conflict with the sidecar guard

Decision 11 says `None`, `""`, and whitespace-only input are no-ops and may return the
same queryset object. Decision 3 proposes extending
`connection_sidecar_inputs_from_kwargs` / `has_connection_sidecar_input` with a third
search value. The existing presence predicate uses `is not None`; the obvious extension
would classify `""` and `"   "` as active sidecars and reject a non-queryset resolver
before the no-op gate runs.

That makes whitespace search observable as an error, not a no-op. Define active search
once and share it between the guard and compiler:

`active_search = search_input is not None and bool(search_input.strip())`.

Then a list-backed resolver rejects only a non-empty search. If supplied-token semantics
are preferred instead, the spec must stop calling empty/whitespace input an unconditional
no-op and pin the error behavior explicitly.

### 6. Slice 5 contradicts the repository's completion rule

Decision 10 says card 049 should flip done while leaving the generated GLOSSARY entry at
“planned” until card 050 performs the joint release cut. [`AGENTS.md`][agents] requires
shipped behavior to fold into `docs/GLOSSARY.md`, `docs/TREE.md`, and `KANBAN.md` in the
completing spec's Slice 5.

Version/changelog ownership may remain with card 050, but implementation status cannot be
left falsely “planned.” Card 049 should update the glossary database and regenerate the
GLOSSARY to a precise intermediate status such as “implemented on main; release pending
the joint 0.1.2 cut.” README release marketing and the version quintet can still wait.
This satisfies both the source-of-truth rule and the joint-cut boundary.

## Missing edge cases and regression risks

### 7. Terminal lookup compatibility is not validated

Existence of a model field does not prove `<field>__icontains` is portable. Search paths
can terminate on integers, UUIDs, choices, JSON/HStore, arrays, file fields, binary fields,
or relation descriptors. Some backends cast some of these; others reject or assign
surprising semantics.

The path-plan builder must validate `icontains` through Slice A's
`validate_lookup_expr(terminal, "icontains")`, reject relation terminals, and execution-test
every terminal family the public contract intends to allow on SQLite and PostgreSQL. The
spec should state the accepted field categories rather than implying every resolvable
model path is searchable.

### 8. Multiple `DjangoType`s over one model need an exact-owner test

The production topology in the reproduction guide uses two types over `UserSchedule` with
different `search_fields`. The spec stores the plan on `DjangoTypeDefinition`, which is the
right design, but its test plan never proves the connection uses the exact target type's
definition instead of falling back through the model registry to the primary type.

Add a primary/secondary test where only the secondary includes a to-many path. Assert:

- both SDL fields expose `search:` independently;
- a group-only term matches the secondary connection and not the primary;
- each type's plan and visibility hook remain distinct;
- plan caching does not collapse them by model identity.

This is a direct acceptance requirement, not a synthetic corner case.

### 9. Combined querysets fail inconsistently

The Part 1 primitive raises a typed `OptimizerError` when `attach_exists` is required on a
combined queryset. A direct-only search instead reaches Django's unsupported
post-`union()`/`intersection()`/`difference()` `filter()` operation and can leak a raw
`NotSupportedError`. The spec discusses non-queryset and sliced sources but not combined
querysets.

Apply one active-search preflight before choosing direct versus `Exists` compilation and
raise one typed, actionable error naming the combinator. Inactive search must return before
that guard.

### 10. Duplicate and whitespace-padded declarations are unspecified

`search_fields=("name", "name")` produces redundant predicates, aliases, and parameters;
`(" name",)` passes the stated “non-empty string” shape check and fails later with a less
useful path error. Decide now:

- reject exact duplicate paths at declaration time (preferred fail-loud posture), or
- stable-deduplicate them before planning.

Also reject leading/trailing whitespace in declared paths with an immediate corrective
message. Do not silently strip a model-path declaration.

### 11. Nested connection search inherits a documented N+1 fallback

Adding `search` to the connection sidecar family makes every search-bearing nested
connection unwindowable under the current optimizer. It will fall back per parent, just as
filter/order sidecars do today. The spec advertises `search:` on every connection field but
tests only roots and does not state this performance consequence.

At minimum, pin that the walker recognizes `search` as a sidecar, creates no dead cached
window, and leaves strictness able to report the per-parent access. Add a live nested
connection query proving correct results and expected bounded/unbounded query behavior.
If strictness=`raise` makes nested search unusable by design, document that explicitly.

### 12. The flat `COUNT(*)` claim is overbroad

The spec repeats that `totalCount` “stays a flat `COUNT(*)`.” That is true only when search
starts from a plain root queryset. A consumer-provided queryset may already be distinct,
grouped, annotated, or projected and legitimately require a count subquery. This was
already corrected in the Part 1 review and must also be corrected in spec 049.

The invariant is: **search adds no distinct wrapper or outer fan-out**. SQL-shape tests for
flat `COUNT(*)` should start from a plain root; separate tests should prove search composes
without corrupting consumer-shaped counts.

### 13. Runtime values need explicit cache-isolation coverage

The prose correctly keeps request data out of the frozen plan, but no acceptance test
proves it. Execute the same operation document twice with different `$search` values and
also execute two aliases with different search values in one operation. Results and
`totalCount` must remain independent while the selection plan cache is reused.

### 14. Database routing is covered by the primitive, not by search integration

Part 1 pins `queryset.db` on the generic `Exists` helper, but card 049 still needs one
integration test proving its runtime compiler passes the current routed queryset rather
than constructing from definition-time metadata or a default manager. Cover an explicit
non-default alias for direct-only and to-many plans. No database alias, queryset, or router
answer may enter the frozen path plan.

### 15. Search input length is an unbounded request-cost multiplier

Decision 11 explicitly declines a length cap. A client-controlled string is duplicated
across every direct and `Exists` branch and normally becomes a leading-wildcard
`icontains` predicate. Transport body limits bound the request envelope, not necessarily a
reasonable database pattern size.

This is not an argument for an ad hoc setting, but it is a public contract that becomes
harder to narrow after release. Before 0.1.2, either choose a documented maximum with a
typed GraphQL error or document that consumers must enforce a limit in transport/middleware
and add an abuse-case test at that boundary. Do not dismiss it merely because the number
of predicates is fixed by the schema.

## Configuration and performance assessment

### The `types/relay.py` setting anchor is not a card-049 runtime risk

Card 049 introduces no setting. `Meta.search_strategy` is explicitly reserved for later.
The setting named in the review prompt is `RELAY_GLOBALID_STRATEGY`, owned by the already
shipped [spec 031][spec-031]. Its actual lifecycle is:

1. `django_strawberry_framework/conf.py::relay_globalid_strategy_setting` performs the
   thin raw read from the package settings mapping.
2. `django_strawberry_framework/types/relay.py::_validated_globalid_setting` validates the
   value where the GlobalID strategy vocabulary and shared Meta validator live.
3. `django_strawberry_framework/types/finalizer.py::finalize_django_types` calls it once
   before the Relay loop and stores the validated snapshot on the registry.
4. Each type receives that snapshot during finalization; the installed resolver closure
   captures the effective strategy. Query execution reads no Django setting and repeats no
   validation.

Consequences:

- **Runtime overhead:** none beyond the already-installed resolver call. There is no lazy
  per-request setting lookup.
- **Thread safety:** safe under the package's single-threaded schema-finalization contract.
  The `Settings` cache and registry are intentionally not safe for concurrent mutation,
  but neither is mutated on request paths.
- **Redundant validation:** no per-type or per-query validation. A partial-finalization
  retry re-reads/revalidates once before comparing the registry snapshot; that small build
  cost is deliberate protection against a mixed-strategy schema.
- **Override behavior:** changing the Django setting after successful finalization has no
  effect until a clean registry/schema rebuild. That is correct for schema-static ID
  encoding and should remain documented.

Moving domain validation into `conf.py` would be architecturally worse: `conf.py` is the
thin settings layer near the bottom of the import graph, while the allowed strategy names,
callable signature rules, and Meta validation belong to the Relay/type domain. If a future
search strategy setting is added, it should follow the same split—thin raw reader in
`conf.py`, semantic validation in the search/predicate owner—and its snapshot-versus-runtime
lifecycle must be chosen explicitly. Nothing search-related belongs in `types/relay.py`.

### Performance evidence is still missing

The structural choice avoids outer fan-out, but the spec acknowledges that many correlated
`Exists` branches can lose on low-selectivity workloads and then defers all benchmark
evidence. Because performance is the reason for rejecting JOIN-plus-DISTINCT, require a
non-gating PostgreSQL artifact before shipping:

- identical data and indexes for both shapes;
- root cardinality and relation fan-out recorded;
- page and count `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)`;
- high- and low-selectivity terms;
- direct-only, one to-many group, and several independent groups;
- warm/cold-cache context and PostgreSQL/Django versions.

Do not gate on elapsed-time percentages, but do not choose the permanent compiler shape
without retaining evidence. Also document that `%term%` `icontains` generally needs a
PostgreSQL trigram index for selective text lookup; row preservation and text-indexability
are separate concerns.

## Test and documentation gaps against the live-tier contract

The [live test tier README][live-tier-readme] says every package line reachable through a
real GraphQL request must earn coverage there first. The spec's current split leaves too
much consumer-visible behavior in package tests and names one nonexistent test location.

### Required placement corrections

- Replace `tests/connection/` in the implementation table with
  `tests/test_connection.py`; that is the source-mirror home for internal connection
  mechanics.
- Keep classifier/grouping/alias-namespace/combinator tests in package tests because they
  inspect internal query objects or unreachable state.
- Put SDL presence/absence, query results, phrase semantics, visibility, permission,
  pagination, `totalCount`, sidecar guards, and sync/async consumer behavior under
  `examples/fakeshop/test_query/` whenever a real field can expose them.
- Product catalog tests belong in `test_products_api.py` and must begin their test bodies
  with `seed_data(N)`/`create_users(N)` rather than hand-created catalog rows. Library
  acceptance tests belong in `test_library_api.py` and use inline model creation under the
  library rule.
- Any settings-dependent schema rebuild must use the live tier's
  `project_schema_override`/shared reload machinery, never ad hoc module reloads that leave
  the aggregate registry incomplete.

### The planned fakeshop activation does not exercise to-many search

All four staged product declarations are local or forward-FK paths. None crosses a
row-multiplying relation. Therefore Slice 4, as written, cannot earn live coverage of the
card's defining row-preserving behavior.

Add an existing no-migration library surface, preferably `GenreType.search_fields =
("name", "books__title")` on `allLibraryGenresConnection` or the corresponding
`BookType.genres__name` shape. Seed one parent with two matching children and assert:

- one edge and one root in `totalCount`;
- count and page SQL contain `EXISTS` and no search-driven `SELECT DISTINCT`;
- the root query owns no membership join (package-level alias-map assertion; live SQL
  assertion for the emitted statements);
- a second page and `hasNextPage` operate on root rows.

This is separate from the Part 1 live `booksTitle` filter regression: one proves the
shipped flat-filter fix, the other proves the new `search:` surface invokes the same engine.

### Missing live acceptance cases

Add live HTTP coverage for:

- SDL introspection: `search: String` present exactly on declaring types and absent on a
  non-declaring control; no nested `filter.search` key;
- null, empty, whitespace-only, and raw leading/trailing-space behavior;
- multi-word phrase semantics (the deliberate upstream divergence);
- `%`, `_`, and quotes as literals on both SQLite and PostgreSQL-supported tiers;
- direct-only, forward-relation, and to-many search;
- `search + filter + orderBy + totalCount`, first page, second page, and keyset mode;
- hidden root rows plus the chosen related-visibility contract;
- the Category-name search/filter permission interaction;
- two aliases with different search values and repeated operation documents with changed
  variables;
- a non-queryset consumer resolver with inactive and active search values;
- an actual async consumer resolver so `_pipeline_async` is earned through HTTP if the
  line is reachable in the example schema;
- nested-connection search fallback and strictness behavior;
- selected related output alongside search, proving selection optimization still adds the
  expected bounded relation load and no new N+1.

### Documentation must state the security and performance contracts

Before the surface is marked complete, the spec and generated/public docs must state:

- whether search paths honor related-type visibility;
- whether search is independent of FilterSet field permissions;
- that declared paths need not be exposed output fields and therefore act as an explicit
  data-discovery grant;
- whole-phrase semantics and raw surrounding-whitespace behavior;
- top-level `search:` only (no nested filter spelling), with migration guidance from
  django-graphene-filters;
- nested connection fallback/strictness behavior;
- leading-wildcard index guidance and the unbounded-input posture;
- the precise intermediate “implemented, joint release pending” status after card 049.

## Required spec revision before implementation

1. Replace dual path validation with one strict plan builder.
2. Replace the misleading `build_search_q` contract with a queryset-level compiler.
3. Decide and document related-row visibility and search permission semantics.
4. Define inactive search once and share it with the non-queryset guard.
5. Add terminal-lookup, combined-queryset, duplicate-path, multi-type, multi-DB, cache-value,
   and nested-connection contracts.
6. Narrow the count claim to “search adds no fan-out/distinct wrapper.”
7. Add a real to-many live fixture and move every reachable behavioral check to the live
   HTTP tier.
8. Reconcile Slice 5 with the generated GLOSSARY completion rule.
9. Retain PostgreSQL before/after plan evidence without wall-clock test gates.

After those revisions, the design has a clean architecture: immutable schema metadata,
one runtime value-free plan, one request-time queryset compiler, one neutral `Exists`
primitive, and explicit security boundaries. Without them, the implementation would bake
authorization ambiguity and duplicated validation into a public API that will be costly to
correct after `0.1.2`.

# Second adversarial review: row-preserving predicates Part 1 (Rev 3)

## Verdict

Rev 3 of the [Part 1 plan][part1-plan] is materially stronger than the version reviewed
above. It now identifies the correct flat-leaf seam, preserves one complete filter
invocation inside the correlated query, keeps negation under Django's control, handles
inactive form fields by identity, and recognizes the two distinct shipped defects. The
three-layer split is the right architecture and should remain.

It is still not implementation-ready. Four issues are blocking because the proposed
mechanics cannot yet implement the advertised fail-closed and compatibility contracts:

1. the metadata build strictly classifies filters that the plan promises to leave
   untouched;
2. a pre-stamp `distinct` boolean cannot carry the origin/provenance decisions the
   eligibility rule needs, and the marker is lost on replacement-filter branches;
3. the candidate map is not part of the existing registry-reset lifecycle;
4. invoking the filter unchanged retains the framework's `distinct=True` inside every
   eligible `EXISTS`, so the plan removes the outer wrapper but does not actually remove
   the redundant distinct operation it introduced.

There is also an unresolved compatibility decision: current framework-added `distinct`
deduplicates pre-existing outer-query fan-out as a side effect, while the rewrite does
not. Comparing primary-key *sets* cannot detect that observable list/count change.

Resolve these points in the plan and update the staged TODO pseudocode before production
implementation. The correlated-`EXISTS` direction itself does not need to change.

## Blocking findings

### 1. “Classify every filter” contradicts fail-closed treatment of declared filters

Slice C.2 says to classify the final `field_name` of **every** entry in `all_filters`, then
marks declared/custom filters ineligible. Those instructions conflict. Explicit
django-filter declarations may legitimately target an annotation, alias, or entirely
method-owned name that is not a Django model path. They bypass model-derived filter
generation precisely because the consumer owns their meaning. For example, a declared
method filter with `field_name="computed_rank"` can be valid when its method annotates or
otherwise interprets that name, even though `classify_path(model, "computed_rank")` must
raise.

Strictly classifying that entry during `FilterSet.get_filters` turns an intentionally
ineligible, currently working declaration into a finalization failure. That violates both
“ineligible leaves keep today's behavior byte-for-byte” and “the failure mode is a missed
optimization.” Expanded declared filters have the same problem after their names are
prefixed by `django_strawberry_framework/filters/sets.py::_expand_related_filter`.

Determine origin before strict path classification:

- framework-default-generated direct and expanded leaves are strict candidates and a
  path-resolution failure is a framework/configuration defect;
- declared/custom and `Meta.filter_overrides` leaves are immediately ineligible and need
  no structured path at all;
- an expanded leaf inherits the child leaf's origin; merely appearing in the result of
  `_expand_related_filter` does not make a declared child “expanded generated.”

The metadata row should therefore permit `path_plan=None` for a proven non-candidate, or
the candidate mapping should contain only proven generated candidates. Add declared
method and declared custom-subclass tests whose `field_name` is not model-resolvable; both
must still build and execute unchanged.

### 2. Provenance must be a frozen origin record, not a saved boolean

The proposed private “pre-framework distinct” attribute is insufficient for the rule the
plan describes:

- `FilterSet.filter_for_field` receives a `default` already produced through
  `django_filters.filterset.BaseFilterSet.filter_for_lookup`, whose defaults have already
  been merged with `Meta.filter_overrides`. A `True` value alone cannot identify whether
  it came from an upstream standard class default or a consumer override.
- The own-PK and Relay-relation branches of
  `django_strawberry_framework/filters/sets.py::FilterSet.filter_for_field` return a **new**
  `GlobalIDFilter` or `GlobalIDMultipleChoiceFilter`. A private attribute placed only on
  `default` is not forwarded to that replacement, so expanded GlobalID leaves lose the
  marker the plan relies on.
- `_expand_related_filter` can preserve attributes through `deepcopy`, but it cannot
  recover whether the child was model-generated, declared, or override-generated unless
  that full origin was recorded on the child first.
- Upstream synthesizes dynamic `ConcreteInFilter` and `ConcreteRangeFilter` subclasses in
  `django_filters.filterset.BaseFilterSet.filter_for_lookup`. Consequently, “enumerate
  the standard upstream classes the generator emits” is not a stable exact-class
  allowlist and will drift with field defaults and django-filter releases.
- A consumer can override `filter_for_field`; calling the framework implementation and
  then replacing or mutating its result must not accidentally retain a stale “safe”
  marker.

Persist one frozen provenance record on the **actual returned filter instance**. It should
distinguish at least framework-default generation, package-owned replacement, declared
filter, and `filter_overrides` generation; record whether the framework added `distinct`;
and survive every replacement/deepcopy explicitly. Expanded copies inherit the child's
record and add “expanded from `<name>`” rather than overwriting its origin.

Eligibility should follow that construction provenance, not a growing class allowlist.
Package-owned replacements are safe because the framework created them; upstream dynamic
classes are safe only when reached through the unmodified default-generation path;
declared, override-generated, and consumer-overridden generation paths fail closed. This
is both stricter and more DRY than maintaining a version-sensitive list of classes.

### 3. Candidate metadata is not in the reset lifecycle

Building the candidate map “under the same gate” as `_expanded_filters` makes the two
writes temporally adjacent, but does not make their lifecycle atomic.
`django_strawberry_framework/sets_mixins.py::SetLifecycleAttrs.binding_attrs` currently
contains exactly the owner, expansion cache, and reentry guard.
`django_strawberry_framework/utils/inputs.py::clear_generated_input_namespace` deletes
only those three attributes from every subclass. A fourth class attribute therefore
survives `registry.clear()` while `_expanded_filters` and `_owner_definition` disappear.

That stale map directly violates C.2's stated “constructed before finalization degrades to
today's behavior” rule: after a clear, direct construction can observe old candidate
metadata before the next completed expansion. It also risks pairing rebuilt `base_filters`
with metadata from the previous owner/finalization cycle.

Make the reset contract explicit and single-sited. Two sound shapes are:

1. extend `SetLifecycleAttrs` with family-specific extra reset attributes and include the
   candidate map there; or
2. store filters and candidate metadata in one immutable expansion snapshot, with
   `get_filters()` continuing to return the snapshot's filter mapping for API
   compatibility.

Whichever shape is chosen, publish both filter and metadata values only after a successful
build, clear both on registry reset, and test build failure, retry, subclass isolation,
unresolved lazy targets, and clear/rebuild. “Ensure reset cannot expose stale metadata” is
not enough pseudocode for this load-bearing state transition.

### 4. The unchanged invocation preserves `DISTINCT` inside `EXISTS`

Every direct deep generated candidate is stamped `distinct=True` by
`django_strawberry_framework/filters/sets.py::FilterSet.filter_for_field`. Rev 3 then
passes that same filter unchanged to the correlated inner root. Ordinary upstream
`Filter.filter` and the package's `_apply_lookups` both execute `.distinct()` before the
lookup. Django's `Query.exists()` clears the select list and ordering but does **not** clear
the `distinct` flag, so the resulting shape is generally `EXISTS(SELECT DISTINCT 1 ...
LIMIT 1)`, not a distinct-free existence test.

That is logically equivalent, but it is not performance-inert. It can retain unnecessary
unique/sort planning inside every correlated branch, and it contradicts the plan's claim
that the old stamp is inert inside the body. Because performance is the reason for this
rewrite, leaving the redundant operation in the permanent primitive is technical debt.

The adapter needs a named invocation helper that suppresses `distinct` **inside the
existence body** for proven eligible filters while still calling the filter's original
`filter()` method. Do not mutate a class-level/base filter. The live FilterSet owns a
per-instance deepcopy, so a scoped change with `try/finally` can restore the instance flag
even when decoding or queryset construction raises; an isolated invocation copy is also
valid if its cost is measured. Consumer-origin `distinct` filters remain ineligible as
already planned.

Add assertions for both outer and inner SQL: no outer `DISTINCT`, no inner `SELECT
DISTINCT`, and the filter instance's flag restored after success and after an exception.
The PostgreSQL plan artifact must compare the actually emitted distinct-free inner shape,
not an idealized hand-written query.

### 5. Primary-key-set equality misses an outer multiplicity regression

The current framework stamp does more than remove duplicates introduced by the candidate
lookup. `.distinct()` applies to the whole current queryset, so it also deduplicates rows
already multiplied by a consumer `get_queryset`, an earlier custom filter, or another
outer join. Replacing the candidate join with `EXISTS` and dropping outer distinct leaves
those pre-existing duplicates visible.

For a plain row-preserving input this is the desired result: the candidate adds no
duplicates. For a pre-fanned input it changes edge multiplicity, `totalCount`, page size,
and cursor behavior relative to today's observable result. The C.4 oracle compares
primary-key **sets**, which necessarily hides the regression, and the “currently-correct
paths have identical rows” claim is therefore too broad.

The plan must make an explicit contract choice before cut-over:

- define and enforce that FilterSet input querysets must already be root-row-preserving,
  with a typed failure or an existing framework invariant that can actually prove it; or
- accept and document the multiplicity change as a deliberate correction to accidental
  global deduplication, including migration notes and a live consumer-queryset test; or
- design a row-normalizing boundary that preserves arbitrary consumer querysets without
  reintroducing the outer `DISTINCT` the work exists to remove.

Do not silently choose the second option by testing sets. Add an ordered primary-key list,
connection count, and pagination case over a deliberately pre-fanned consumer queryset.

## Major implementation and contract gaps

### 6. Rejecting evaluated querysets is an unnecessary breaking guard

Slice B says `attach_exists` validates that both inputs are “unevaluated” querysets. Django
allows further queryset construction after evaluation: `.filter()` / `.alias()` clone the
query and execute a fresh statement, and today's FilterSet path accepts such a queryset.
The outer `_result_cache` is not embedded in SQL and creates no correlation hazard.

The inner queryset produced by `correlated_inner_root` will naturally be unevaluated and
must never be executed independently, but that is an implementation invariant—not a
reason to reject a valid evaluated outer queryset. Remove the outer evaluation-state
guard unless a concrete wrong-result reproduction exists. Test `list(source_qs)` followed
by application of an eligible filter and require parity with the unevaluated source.

### 7. The final test suite needs an explicit baseline oracle

“Freeze failing tests” is a useful local red/green sequence, but a committed final suite
cannot depend on old production routing after cut-over. Likewise, “compare baseline and
rewritten sets before the old behavior is removed” does not say how that comparison
survives in the finished tree.

Define a test-only oracle that directly invokes the same filter instance on the outer
queryset to obtain django-filter's baseline, while the production FilterSet invokes it
inside `EXISTS`. Keep that oracle visibly test-local; do not ship a strategy flag or a
second production compiler. Compare ordered rows/counts where multiplicity is part of the
contract, and sets only where the test explicitly targets boolean membership semantics.
The flattened-path defect additionally needs a direct assertion that the old oracle
duplicates while the production result does not.

### 8. C.5 proves only the expanded-origin branch

The proposed live `booksTitle` test is exactly the right regression for the public
flattened `RelatedFilter` defect, but it exercises only expanded generated provenance.
Direct deep generated leaves take a separate metadata-origin path and are reachable from a
real GraphQL filter input, so the [live-tier rule][live-tier-readme] requires a live proof
for that branch too.

Add a non-colliding direct deep lookup to an existing library FilterSet, or add a small
no-migration FilterSet/type surface over an existing model, and execute it over HTTP. The
test must prove a duplicate-matching to-many relation yields one edge and correct
`totalCount`. Keep origin/provenance internals and alias-map assertions in package tests;
move consumer-visible `and` / `or` / `not`, empty-list, GlobalID, count, and pagination
behavior to live HTTP wherever the existing fakeshop schema can reach it.

### 9. The plan needs a completion/documentation slice of its own

This work changes shipped `FilterSet` result multiplicity and adds
`django_strawberry_framework/optimizer/predicates.py`, but “What this deliberately does
not change” excludes every release-state artifact and the sequence has no documentation
step. That conflicts with [`AGENTS.md`][agents]: shipped behavior must fold into
`docs/GLOSSARY.md`, `docs/TREE.md`, and `KANBAN.md` when its work completes. The new
optimizer module also makes the current tree inventory stale.

The free-standing filename `docs/row-preserving-predicates-part1-plan.md` is not the
required `spec-<NNN>-<topic>-<version>.md` form for an in-flight production design. Either
make this groundwork an explicit pre-card slice of [spec 049][spec-049], with card-owned
completion bookkeeping, or allocate it a real KANBAN card/spec identity. In either case,
add a final docs slice for the shipped FilterSet semantics and tree inventory. Version and
`CHANGELOG.md` ownership may remain wherever the maintainer assigns them; source-of-truth
documentation may not.

### 10. Update the runtime-error ownership documentation

Using `OptimizerError` for a required attachment to a combined queryset is reasonable,
but `django_strawberry_framework/exceptions.py::OptimizerError` currently documents only
selection/window-planning raise sites. The Part 1 completion slice must add predicate
attachment to that public exception contract and test the GraphQL wrapping path if a live
consumer can reach it. Otherwise the implementation and exception documentation diverge
on the first new raise site.

## Downstream issues still present in the revised search spec

These do not require changing the neutral Part 1 primitive, but the updated
[spec 049][spec-049] still needs two clarifications before it can safely consume the
groundwork.

### 11. Direct relational branches must carry per-branch visibility

Decision 12 first promises visibility composition for every relation hop, then says
forward single-valued hops on the root side are already covered by cascade narrowing.
That is not a framework invariant: `apply_cascade_permissions` is an explicit helper a
consumer may or may not call, search paths need not be exposed output fields, and a type's
custom `get_queryset` may narrow only its own model.

For `search_fields=("title", "category__name")`, the `category__name` branch must include
the registered Category type's visibility constraint even when the Item type does not
call cascade. Applying that constraint to the whole query would incorrectly suppress an
Item that matches `title`, so it must be ANDed only into the relational OR arm. The same
rule applies to a chain of forward hops before the first to-many hop.

Specify direct branches as structured `(hop visibility AND terminal icontains)` branches,
not bare lookup `Q`s, and add a live forward-FK test without root cascade. Otherwise the
spec's strongest security claim is true only for the staged fakeshop types that happen to
call the helper.

### 12. “Exactly when they could filter” overstates the permission contract

Decision 13 can reuse applicable FilterSet gates, but it cannot make search permission
identical to filter permission. A type may declare a search path absent from its
FilterSet, or may declare no FilterSet at all—both are explicitly supported. In those
cases the viewer cannot issue the equivalent `filter:` input, yet the spec says search is
allowed because no gate exists.

Narrow the contract to: “active search fires every applicable gate exposed by the
declaring type's FilterSet; `Meta.search_fields` is the authorization grant for paths with
no corresponding filter gate.” Then define what happens when several filter aliases map
to one `field_name`, when only a prefix relation is gated, and when an expanded child path
has no public flat filter because `HIDE_FLAT_FILTERS` is enabled. Tests should cover an
ungated search-only path on a type that also has a FilterSet, not only the all-gated
Category example and the no-FilterSet case.

## Required Rev 4 changes before implementation

1. Classify only proven generated candidates; leave declared/custom non-model paths
   untouched.
2. Replace the boolean marker and class allowlist with a frozen generation-provenance
   record propagated to every actual returned/replacement/expanded filter.
3. Make candidate metadata part of the atomic expansion/reset lifecycle.
4. Suppress and restore `distinct` during eligible inner invocation; assert no inner or
   outer distinct in emitted SQL.
5. Decide the pre-fanned-input multiplicity contract and test ordered rows, counts, and
   pages—not only PK sets.
6. Remove the evaluated-outer-queryset rejection unless a real incompatibility is proven.
7. Define the permanent baseline oracle and move every reachable adapter behavior to the
   live HTTP tier, including a direct-deep generated origin.
8. Give the groundwork a card/spec completion owner and update GLOSSARY/TREE/KANBAN plus
   `OptimizerError` documentation.
9. In spec 049, make forward-relation visibility branch-local and narrow the FilterSet
   permission claim to applicable gates.

With those changes, Rev 4 would have a clean implementation path: origin is captured once
at generation, expansion transports it without inference, one atomic cache owns filters
and metadata, the adapter invokes the original semantic operation without carrying a
redundant distinct into `EXISTS`, and both current compatibility and future search
security have explicit testable boundaries.

# Cross-spec review: the Medtrics DRF reproduction against the project goal

## Verdict

The production reproduction from Medtrics makes the purpose of both plans clearer, but it
does **not** call for copying the application's `StringAgg` workaround or adding a dynamic
per-connection search API. Read together with [`GOAL.md`][goal], it confirms four project
contracts:

1. the framework owns fan-out introduced by its generated relational predicates;
2. consumer-shaped Django querysets remain visible and compositional, so the framework
   must not silently normalize their pre-existing multiplicity;
3. `Meta.search_fields` is frozen metadata owned by the exact `DjangoType` definition,
   not mutable DRF-view-action state; and
4. a schema author declaring an ordinary reverse-relation search must receive portable,
   row-preserving SQL without hand-building an aggregate alias in `get_queryset`.

The current Part 1 Rev 4 architecture and spec 049's correlated-`EXISTS` decision are the
right root-cause answer. The reproduction contributes sharper acceptance oracles and one
documentation clarification for each spec.

## What the reproduction establishes

The concrete path is
`UserSchedule.user -> User.group_list -> GroupUser.group -> Group.name`:

- `UserSchedule.user` is a forward FK (to-one);
- `User.group_list` is the reverse side of `GroupUser.user` (to-many);
- `GroupUser.group` is a forward FK (to-one).

One user may belong to several groups even though `GroupUser` makes each `(user, group)`
pair unique. A search over `user__group_list__group__name` therefore multiplies each
outer schedule by the number of matching memberships. DRF 3.14 detects that multiplying
path and applies one global `distinct()` after combining it with the scalar name, class,
role, and rotation branches. That keeps the response superficially correct while making
the to-many branch's join and deduplication policy observable in count and pagination.

This is important classifier evidence: the multiplying relation is a **reverse FK**, not
a concrete `ManyToManyField`, and it appears after a to-one prefix. Any classifier or test
fixture that proves only direct M2M traversal is incomplete.

The Medtrics patch's scalar correlated `StringAgg` removes the outer fan-out, but it is an
application-specific workaround, not prior art to adopt:

- it is PostgreSQL-specific while this project promises portable basic `icontains` search;
- it processes all related strings where `EXISTS` may stop at the first match;
- an aliased aggregate may be expanded once per DRF search term;
- concatenation erases related-row boundaries; and
- it has no natural place to compose each related type's visibility constraint.

The reproduction therefore validates the desired **query shape**, not the workaround:
the membership join belongs inside a correlated `EXISTS`; the outer query has neither the
membership join nor a framework-added `DISTINCT`.

## Non-negotiable executable reproduction shared by both specs

The specifications should not leave the production issue as prose. Add one named,
deterministic reproduction fixture that Part 1 and card 049 both consume. The existing
fakeshop library models provide the Medtrics topology without a migration:

```text
Loan.book -> Book.loans -> Loan.patron -> Patron.email
   to-one       to-many        to-one        scalar
```

Library acceptance tests may create these models inline. Build exactly four root loans:

1. `relation_and_direct`: on `shared_book`, `note="Cardio direct"`, patron email
   `"Cardio A"`;
2. `relation_only`: on the same `shared_book`, an unrelated note, patron email
   `"Cardio B"`;
3. `direct_only`: on a second book, `note="Cardio direct"`, patron email
   `"Neurology"`; and
4. `unrelated`: on a third book, with neither field containing `"Cardio"`.

The test-local pre-rewrite oracle is the literal outer predicate:

```python
baseline = Loan.objects.order_by("id").filter(
    Q(note__icontains="Cardio")
    | Q(book__loans__patron__email__icontains="Cardio")
)
```

Because `shared_book` has two matching loans, that query's ordered primary-key sequence is
`[relation_and_direct, relation_and_direct, relation_only, relation_only, direct_only]`.
Its raw count is five. Adding DRF-style global `distinct()` makes the visible sequence
look correct and reduces the count to three, but the SQL retains the outer joins and a
distinct count shape. This is the exact failure signature the test must freeze; a set
comparison cannot recreate it.

The production oracle for both specs is the ordered sequence
`[relation_and_direct, relation_only, direct_only]`, count three, with each row appearing
once. On a two-edge page, page one contains the first two IDs, page two contains only
`direct_only`, and `totalCount` remains three. The root SQL contains no `library_loan`
self-join for `Book.loans`, no patron join, and no framework-added `DISTINCT`; one
correlated `EXISTS` owns those inner joins. The row matching both direct and relational
branches remains one row.

Use the same fixture at three levels rather than creating three subtly different
reproductions:

- **Part 1 adapter test:** add the generated deep filter path
  `book__loans__patron__email` to `LoanFilter`, activate its `icontains` leaf, and compare
  the test-local outer-invocation baseline with the row-preserving production adapter.
- **Spec 049 integration test:** declare
  `LoanType.Meta.search_fields = ("note", "book__loans__patron__email")`, expose an
  acceptance-only `DjangoConnectionField(LoanType)`, and issue the real `/graphql` search
  request. Assert the exact ordered IDs, `totalCount`, both page boundaries, and the mixed
  direct/relational OR behavior above.
- **SQL-shape test:** inspect the package-level queryset separately to prove that the live
  result came from a correlated `EXISTS`, not JOIN-plus-DISTINCT or a scalar aggregate.

Add a second fixture to pin related-row boundaries. Put two loans on one book whose patron
emails are both `"red"`, and one loan on another book whose patron email is `"red red"`.
With unrelated notes, `search: "red red"` must match only the latter loan. Aggregating the
first book's two child values with a space would manufacture `"red red"` and fail this
test regardless of child order; a terminal predicate evaluated per related row cannot.

These tests are the acceptance definition of “recreate the original issue.” A test that
only asserts three unique IDs after deduplication, or merely checks that `DISTINCT` is
absent, is insufficient.

## Required improvements to the Part 1 plan

### 1. Tie the multiset contract directly to the north star

Rev 4's maintainer-decided multiset contract is correct and should remain unchanged.
[`GOAL.md`][goal] supplies the architectural reason: automatic planning must “cooperate
with consumer-shaped querysets,” and the package must not become an ORM abstraction that
hides Django querysets. A framework predicate is therefore a selection over the incoming
queryset, not a normalization boundary over consumer SQL.

Add that rationale to the contract section. It makes clear that preserving consumer
duplicates is not merely the least expensive answer to finding 5; it follows from the
package's public queryset-composition promise. Continue preserving explicit consumer
`distinct()`, annotations, ordering, and pre-existing multiplicity while preventing only
framework-owned fan-out.

### 2. Make reverse-FK-after-to-one a named classifier and adapter oracle

Slice A and C coverage should include the exact structural category demonstrated here:

```text
root --forward FK--> intermediate --reverse FK--> membership --forward FK--> terminal
```

Require the frozen path plan to identify the reverse FK as the first multiplying boundary
and require the adapter's emitted outer query to exclude both membership and terminal
tables. Keep the existing direct M2M cases as a separate category; neither test subsumes
the other.

At least one consumer-visible fakeshop case should use a reverse FK rather than earning
all live cardinality coverage through `Book.genres`. The test must use ordered IDs,
`totalCount`, and a page boundary with several matching children.

### 3. Do not use the DRF response as the multiset oracle

The Medtrics example starts from a plain `UserSchedule.objects.all()` path for the SQL
assertion. It proves that search itself no longer fans out, but it says nothing about a
consumer queryset that was already fanned before search. DRF's old global `distinct()` is
the behavior Part 1 deliberately corrects.

Keep Rev 4's permanent test-local baseline and its pre-fanned, explicitly-distinct, and
custom-filter-produced inputs. Do not weaken those cases to match the original endpoint's
set-like response behavior.

## Required improvements to spec 049

### 4. State that search scope is type-definition-wide and immutable

The Medtrics patch solves a second application concern: group-name search belongs on
`detail_list`, but not on three Academic Progress actions. That is a DRF view/action
distinction. It must not be translated into request-time mutation of
`DjangoType.Meta.search_fields` or a resolver-specific escape hatch.

The goal's public shape is one declarative `DjangoType.Meta` sidecar, and spec 049 already
assigns the frozen plan to the exact type definition. Add an explicit contract:

- every connection serving the same `DjangoType` definition exposes the same static
  search capability;
- runtime request, resolver, and connection context never mutate or narrow the declared
  path tuple;
- viewer-dependent denial belongs to existing visibility and FilterSet gates;
- a report/custom GraphQL field that is not the model connection need not expose the
  generated search sidecar; and
- a genuinely different model-backed GraphQL surface uses a distinct `DjangoType`
  definition, whose exact-owner plan is already covered by the multi-type tests.

This should be documented as intentional scope, not left as an accidental limitation.
Do not add a field-level override mechanism without a separate demonstrated GraphQL use
case; doing so now would work against the Meta-first, no-hand-rolled north star.

### 5. Add a row-boundary oracle that makes `StringAgg` observably wrong

Whole-input phrase semantics make a particularly strong regression test possible. Give
one parent two related rows whose values are `"red"` and `"dwarf"`, and another parent one
related row whose value is `"red dwarf"`. Searching for `"red dwarf"` must match only the
second parent.

A `StringAgg(..., delimiter=" ")` implementation can incorrectly manufacture the phrase
across the first parent's two children. A correctly correlated terminal predicate cannot.
Run this through the live GraphQL surface and assert ordered edges and `totalCount`, then
keep SQL-shape assertions in package tests proving the implementation is `EXISTS`, not a
scalar aggregate that merely happens to avoid outer fan-out.

### 6. Prove reverse FK and M2M search independently

Decision 7 and its test plan currently speak generically about to-many declarations. Add
two explicit search-path categories:

- a reverse FK after a to-one prefix, matching the Medtrics topology; and
- a direct or nested M2M path, matching the library fixture.

For the reverse-FK case, combine a scalar direct path and the relational path in the same
search OR. Include a root that matches the scalar branch and has several matching related
rows, a root that matches only the related branch, and an unrelated root. This pins both
boolean semantics and cardinality under the precise mixed-branch shape that caused the
production issue.

### 7. Clarify DRF-shaped compatibility versus DRF SearchFilter parity

[`GOAL.md`][goal] promises a DRF-shaped, Meta-driven developer experience and unchanged
reuse of django-filter `FilterSet` primitives. It does not promise byte-for-byte parity
with DRF's `SearchFilter`. Spec 049 intentionally differs in two visible ways:

- whole-input phrase semantics instead of DRF's whitespace-split term-AND; and
- static type-definition scope instead of `SearchFilter.get_search_fields(view, request)`
  action/request dynamism.

Put both differences together in the borrowing/migration documentation. The existing
`"Cardio Cohort"` Medtrics test cannot distinguish the contracts because one group name
contains both terms. Keep spec 049's distinct multi-field phrase test, and add the
split-across-children negative above, so future maintainers cannot accidentally import
DRF term splitting or aggregate semantics while pursuing “DRF first.”

## Cross-spec acceptance checklist from the reproduction

Before production implementation, the two documents together should require:

1. strict classification of forward-FK -> reverse-FK -> forward-FK paths;
2. separate M2M classification coverage;
3. one outer root occurrence for several matching related rows;
4. scalar OR relational search returning both kinds of matches;
5. a row matching both branches still appearing once;
6. no membership/child joins in the outer query;
7. one correlated `EXISTS` containing the relational joins;
8. no framework-added outer or inner `DISTINCT` on a plain input;
9. preserved consumer multiplicity, ordering, and explicit `distinct()`;
10. correct ordered edges, `totalCount`, and page boundaries;
11. no phrase manufactured across separate related rows;
12. visibility and permission constraints composed inside only the relational branch;
13. immutable exact-type ownership of the frozen search plan; and
14. explicit documentation of phrase and scope differences from DRF SearchFilter.

With those additions, the original issue becomes a high-value acceptance fixture rather
than an architectural template: it proves the user-facing failure, while Part 1 and spec
049 supply the portable, visibility-aware, compositional root-cause fix that the source
application had to hand-build.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[goal]: ../GOAL.md
[repro]: ../to-many-search-optimizer-reproduction.md

<!-- docs/ -->
[part1-plan]: row-preserving-predicates-part1-plan.md
[spec-049]: spec-049-search_fields-0_1_2.md

<!-- docs/SPECS/ -->
[spec-031]: SPECS/spec-031-globalid_encoding-0_0_9.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->
[live-tier-readme]: ../examples/fakeshop/test_query/README.md

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
