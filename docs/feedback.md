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

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
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
