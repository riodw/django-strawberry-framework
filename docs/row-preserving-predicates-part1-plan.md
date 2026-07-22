# Part 1 plan: row-preserving predicate machinery, enacted now (Rev 3)

## Purpose

This plan enacts the "now" half of the to-many fan-out investigation
([`to-many-search-optimizer-reproduction.md`][repro]): everything that fixes
shipped behavior or builds search-independent machinery lands ahead of card
`TODO-BETA-049-0.1.2`, so that card later wires the `search:` surface onto a
finished engine ([spec-049][spec-049], Decision 7). The postponed half — the
`search:` argument, `Meta.search_fields` validation, the pipeline step, live
search fixtures, benchmarking — stays with the respecced card.

Rev 2 incorporated the first adversarial review ([`feedback.md`][feedback])
in full; Rev 3 folds in the second round (empirically verified against
fakeshop / Django 6.0.5 / django-filter 25.2): the adapter's no-op
detection contract (C.3), the metadata build-site mechanics (C.2), and the
explicit eligibility of the package's own filter classes (C.2/C.4). The
first review's verified corrections reshape the plan:

- **The integration seam is `FilterSet.filter_queryset`, not
  `_apply_lookups`.** Flat leaves are delegated wholesale to
  `django_filters.filterset.BaseFilterSet.filter_queryset` by
  `django_strawberry_framework/filters/sets.py::FilterSet.filter_queryset`
  #"super().filter_queryset(queryset)"; an ordinary generated `CharFilter`
  runs upstream `django_filters.filters.Filter.filter` (empty-value short
  circuit → `qs.distinct()` when `self.distinct` → the lookup call).
  `_apply_lookups` covers only the package's custom filter classes.
- **There are two shipped defects, not one** (both verified in fakeshop):
  1. Explicit deep generated paths are stamped `distinct=True` by
     `django_strawberry_framework/filters/sets.py::FilterSet.filter_for_field`
     — correct rows, expensive outer fan-out and distinct-wrapper counts.
  2. Flattened `RelatedFilter` leaves are **`distinct=False`**:
     `django_strawberry_framework/filters/sets.py::_expand_related_filter`
     deep-copies a filter generated against the *child* model and only then
     prefixes `field_name`, so root-model to-many classification never runs.
     `BookFilter.get_filters()["genres__name__icontains"]` carries
     `field_name="genres__name"`, `distinct=False` — and these flattened
     fields are public by default
     (`django_strawberry_framework/conf.py::hide_flat_filters_setting`
     defaults `HIDE_FLAT_FILTERS` to `False`). A flat `genresName` filter
     can duplicate root rows and corrupt `totalCount` **today**.
- **A scalar `negated` flag on a multi-lookup body is a result-set
  regression.** Django compiles `exclude(rel__a=..., rel__b=...)` as the
  complement of *independent* existence tests (one `split_exclude` per
  condition); a single `NOT EXISTS` whose body ANDs both comparisons keeps
  split-across-rows parents that Django excludes. The compiler therefore
  never synthesizes boolean bodies for filter semantics — it preserves one
  complete original filter invocation inside the correlated subquery
  (Slice C's adapter), and negation stays wherever Django's own machinery
  puts it.

Investigation grounding that still stands (validated on Django 6.0.5 /
fakeshop / SQLite): the `Exists` form removes membership tables from the
outer `alias_map`, keeps `query.distinct` False, returns one row per parent
with multiple matching children, and adds no distinct wrapper to `.count()`;
`EXISTS` distributes over OR for same-value disjunctions (card 049's future
grouping is a cost choice there); no surveyed prior art implements a
positive-filter `EXISTS` rewrite (Django core does it only for `exclude()`;
admin's `lookup_spawns_duplicates` detects m2m only and misses reverse FK).

## Architecture: three layers, filter semantics live in the adapter

Per review finding 8, the reusable machinery stays neutral and the
django-filter semantics live in one adapter:

1. **`utils/relations.py`** — immutable model-path classification
   (Slice A). No lookup execution, no queryset knowledge.
2. **`optimizer/predicates.py`** — correlation, alias allocation, and
   attachment of `Exists` for an **already-defined inner queryset**
   (Slice B). It never builds predicate bodies, never ORs groups, and knows
   nothing about django-filter or Strawberry. Card 049 later builds its
   same-value OR groups and calls this layer directly.
3. **`filters/sets.py`** — the django-filter leaf adapter (Slice C): builds
   the correlated inner root, applies **one original eligible filter
   invocation** to that inner root (its actual `filter()` / `exclude()`
   boolean semantics, empty-list handling, GlobalID decoding, range
   decomposition included), and asks layer 2 to attach the positive
   `Exists(filtered_inner)`.

This "invoke the original filter against the correlated inner root" shape is
what makes the rewrite semantics-preserving without reimplementing any
filter class: multi-lookup invocations keep their per-condition Django
compilation (including `split_exclude` for excludes) *inside* the subquery,
where the correlation — not a hand-built body — is the only new element.

## Slice A — structured path classification

Files: `django_strawberry_framework/utils/relations.py`,
`tests/utils/test_relations.py`.

Per review finding 5, classification and lookup validation are **separate
contracts**:

- `classify_path(model, field_path)` classifies a **model-field path only**
  (the shape `FilterSet.filter_for_field` and card 049 declarations
  actually hold — `lookup_expr` arrives separately at every real call
  site). It returns an immutable plan: relation hops (segment, kind, target
  model, many-side flag), the terminal — either a concrete field **or the
  terminal relation descriptor** (relation-terminal paths like the `isnull`
  relation filters need it; `None` would discard required information) —
  and the index of the first row-multiplying hop (or `None`).
- A separate `validate_lookup_expr(terminal, lookup_expr)` helper validates
  a lookup expression against the classified terminal, walking chained
  transforms via each transform's `output_field` (never re-validating
  against the original field) and ending on `get_lookup`. Whether the ORM
  alias `pk` is accepted is decided explicitly (accept it; it is a valid
  ORM name the generated surface can produce).
- Strictness contract: `classify_path` raises one named, typed resolution
  error (message naming model, path, offending segment).
  `path_traverses_to_many` is reimplemented over `classify_path`, catching
  **only that typed error** to retain its lenient legacy `False` for
  existing callers; new machinery calls `classify_path` directly and fails
  loud. The reimplementation preserves the existing `lru_cache`
  characteristics and an explicit output-parity test covers garbage-tail
  inputs (today's walker returns `False` at the first non-relation or
  unresolvable segment regardless of trailing segments; `orders/sets.py`
  consumes the helper too, so parity is load-bearing beyond filters).
- The complete relation chain is exposed as the (future) subquery grouping
  key — never reconstructed by callers.

Coverage matrix: forward FK/O2O chains, MTI-inherited fields, reverse FK,
forward and reverse M2M, `GenericRelation`, reverse O2O as single-valued,
self-referential paths of differing depth, chained transforms (execution
tests, not classifier-output-only), relation-terminal paths, unresolvable
paths, `related_name="+"`, forward `GenericForeignKey`.

## Slice B — the neutral correlated-EXISTS primitive

Files: `django_strawberry_framework/optimizer/predicates.py` (new),
`tests/optimizer/test_predicates.py` (new).

A pure ORM utility, independent of
`django_strawberry_framework/optimizer/plans.py::OptimizationPlan` (which
stays selection-only; the module lives in `optimizer/` because the package's
`_dst_` reserved-alias namespace lives there).

Surface (two pieces, both value-free and filter-semantics-free):

- `correlated_inner_root(queryset)` — returns
  `queryset.model._base_manager.using(queryset.db)` correlated to the outer
  row. `_base_manager` is deliberate: the outer queryset has already applied
  visibility and the consumer manager; the inner row only tests relation
  existence for an already-qualified outer pk, so a filtered default
  manager could only introduce false negatives. `queryset.db` pins the
  outer queryset's resolved alias onto the inner root (on a hint-less
  outer queryset `.db` invokes the router at build time); the inner never
  executes independently — it compiles inside the outer query — so the pin
  exists to keep the alias pair consistent, not to re-run routing.
  - Correlation is `pk=OuterRef("pk")` **as the default and only
    implementation**, per review finding 6: on the validated runtime it
    compiles composite pks to a correct tuple comparison. The version
    matrix step (see Sequencing) pins its compilation and execution on
    Django 5.2 and 6.0 for both single-column and composite pks; a
    per-column expansion is added only if a supported runtime demonstrably
    fails, derived from `_meta.pk_fields` (never naming convention) and
    tested with custom `db_column` values.
- `attach_exists(queryset, inner_queryset)` — wraps the caller-built inner
  queryset in `Exists`, attaches it under a freshly allocated `_dst_`
  alias, and returns `(queryset, Q(<alias>=True))` for the caller to
  compose. No `negated` parameter: negation placement belongs to the caller
  whose boolean semantics are proven (the adapter never needs it — see
  Slice C; card 049's positive OR never needs it either).

Alias allocation, per first-review finding 7, checks Django's **effective
alias namespace**, not just `queryset.query.annotations`: model field names
and attnames, the literal name `pk` (Django *accepts* it as an alias),
existing annotations and aliases, `extra_select` names, already
projected/selected names, and every alias allocated earlier in the same
compiler call — advancing a deterministic counter until free. The check is
load-bearing because Django is lax in the dangerous direction (verified):
`.alias()` raises only for model-field collisions; a **duplicate alias
silently overwrites** and an `extra(select=)` collision compiles to
ambiguous SQL without raising. Tests: colliding consumer alias, colliding
model field, repeated invocations on one queryset, coexistence with
`_dst_order_*` and window annotations.

Guards and claims, per review finding 9:

- Empty/no-op input returns the queryset untouched **before** any guard
  runs (the identity contract wins first).
- The combined-queryset preflight (`queryset.query.combinator`) runs only
  when attachment is actually required, and raises a typed error whose
  family is chosen deliberately: this is runtime query state, not consumer
  configuration, so it raises the optimizer's runtime error type rather
  than `ConfigurationError`, with a message naming the combinator. The
  branch is genuinely unreachable from a live `/graphql/` query (the
  pipeline never produces combined querysets), so its coverage lands in
  `tests/` under the live-first mandate's unreachability fallback.
- The count invariant is phrased and tested as "**the compiler adds no
  distinct wrapper**": flat-`COUNT(*)` assertions start from a plain root
  queryset; separate compatibility tests cover consumer querysets that are
  already distinct/annotated/projected and legitimately count through a
  subquery.

Core SQL-shape tests: root `alias_map` excludes membership/child tables,
`query.distinct is False`, `EXISTS` present and correlated on the root pk,
one row per parent with duplicate matching children, aliases absent from
selected columns, database alias preserved.

## Slice C — candidate metadata + the FilterSet leaf adapter

Files: `django_strawberry_framework/filters/sets.py` (adapter + metadata),
filter tests, live fakeshop coverage under `examples/fakeshop/test_query/`.

### C.1 — freeze both defects first

Failing tests pinning today's behavior before any change: a direct deep
generated path fans out through JOIN+`distinct=True`; a flattened
`RelatedFilter` leaf (`genres__name__icontains`-shaped) duplicates parent
rows and corrupts a connection `totalCount` with `distinct=False`.

### C.2 — immutable candidate metadata with provenance

Per first-review finding 4, eligibility is decided from a class-level
mapping keyed by final form-filter name, classified against the final
owning `FilterSet._meta.model` and final prefixed path — never trusting
the child filter's original classification or `distinct` value — carrying:

- the final classified path rooted at the owning model (Slice A);
- filter origin: direct generated leaf, expanded generated leaf, or
  declared/custom;
- pre-framework `distinct` provenance;
- inner-invocation eligibility.

**Build-site mechanics** (second review, M1 — the hard part, pinned
explicitly):

- The two filter surfaces diverge until lazy `RelatedFilter` targets
  resolve: `django_strawberry_framework/filters/sets.py::FilterSet.get_filters`
  writes the expanded set to `cls.base_filters` only under its
  `should_cache_expansion` gate (unresolved string targets skip the cache),
  and `FilterSetMetaclass.__new__` rebuilds `base_filters` bypassing the
  expansion override. The metadata mapping is therefore built **inside the
  same expansion build, under the same gate as `should_cache_expansion`**
  — never as a separate "after get_filters()" pass that could observe the
  unexpanded surface.
- The mapping is stored with the same per-class `cls.__dict__` guard the
  expansion cache uses, so subclasses never inherit a parent's mapping.
- Pre-stamp `distinct` provenance cannot be recovered post-hoc: the
  to-many stamp (`FilterSet.filter_for_field`
  #"default.distinct = requires_distinct") runs at *child* filterset class
  build, before `_expand_related_filter`'s `copy.deepcopy` and before
  `BaseFilterSet.__init__`'s per-instance deepcopy. The pre-stamp value is
  therefore **persisted on the filter instance inside `filter_for_field`
  at the moment of stamping** (a private attribute the deepcopies carry),
  and the mapping build reads it from the expanded instance.
- The adapter treats a `cleaned_data` name **absent from the mapping as a
  non-candidate** (fail closed). This path is reachable: a filterset
  constructed directly before finalization resolves lazy targets presents
  the unexpanded 5-field surface and must degrade to today's behavior.

**Fail-closed eligibility rule:** declared filters,
`Meta.filter_overrides` products, and unknown custom filter subclasses are
ineligible unless their entire invocation is deliberately supported.
Eligibility is never inferred from a class name or from `method is None`
(an explicitly declared filter can override `filter()` with `method`
unset). Per second-review M2, the package's **own generated filter
classes are enumerated as deliberately supported** — without this, the
`in=[]` / range / GlobalID rows of the acceptance matrix would be
untestable: `django_strawberry_framework/filters/base.py::IntegerInFilter`,
`IntegerRangeFilter`, `GlobalIDFilter`, `GlobalIDMultipleChoiceFilter`,
`ArrayFilter`, `ListFilter` (audited: `IntegerInFilter` reads only
`self.parent._meta.model`; GlobalID decoding is queryset-independent;
`_apply_lookups`' `distinct` is inert inside an `EXISTS` body), alongside
the standard upstream classes the generator emits. Their identity-return
branches fold into C.3's no-op detection. Eligible = framework-generated
leaf (direct or expanded), filter class on that enumerated list, no
consumer `method`, no consumer-origin `distinct`, path crosses a many-side
hop. Ineligible leaves keep today's behavior byte-for-byte — the failure
mode is a missed optimization, never a changed result set.

### C.3 — the flat-leaf applicator

Per review finding 1, `FilterSet.filter_queryset` stops delegating leaves
wholesale to `BaseFilterSet.filter_queryset` and instead runs a
framework-owned applicator mirroring upstream's loop exactly:

- iterate `self.form.cleaned_data` in order;
- non-candidates (including names absent from the C.2 mapping): call the
  original filter unchanged;
- candidates: build `correlated_inner_root(queryset)`, apply **the
  original filter invocation** to that inner root (so `filter()` vs
  `exclude()`, multi-lookup decomposition, `in=[]` semantics, GlobalID
  decoding all run exactly as upstream wrote them — Django's own
  `split_exclude` handles negation *inside* the subquery), then
  `attach_exists` and `.filter(positive_branch)`;
- **no-op detection (second review, B1 — load-bearing control flow):**
  `cleaned_data` contains every declared form field, almost all empty on a
  real request (measured: 17 entries, 16 empty, for a one-filter
  `GenreFilter` input). Upstream's empty-value short circuit returns the
  queryset **by identity**, so the adapter skips `attach_exists` whenever
  the invocation returns the inner root unchanged
  (`result is inner_root`). Without this, every inactive to-many candidate
  attaches a tautological `EXISTS(SELECT 1 … WHERE U0.id = outer.id)` —
  row-set-safe but one correlated subquery + one `_dst_` alias per
  inactive leaf per query, and it breaks the C.4 SQL-shape assertions.
  The identity rule also covers the package's own identity-return
  branches (`django_strawberry_framework/filters/base.py::_match_none_queryset`
  under `exclude=True` returns `qs` unchanged — baseline is match-all, so
  skipping is equivalent — and upstream `MultipleChoiceFilter.is_noop`).
  The inverse composes correctly with no special case: a restrictive-empty
  input's `qs.none()` on the inner root gives `Exists(none) = False`,
  matching the baseline empty result;
- retain upstream's `QuerySet` return assertion and message;
- then run the existing `_evaluate_logic_tree` step unchanged.

This preserves the direct `FilterSet(...).qs` path and `apply_sync` /
`apply_async`. The logic tree's `not` branches stay outside the child
queryset (`_q_for_branch`'s `Q(pk__in=...)` composition is untouched) — a
regression test proves branch negation is never pushed into a leaf.

Explicitly left alone:
`django_strawberry_framework/filters/sets.py::FilterSet._apply_related_constraints`
and `_q_for_branch` — already row-preserving via the parent-pk `pk__in`
subquery; the `Exists`/`pk__in` equivalence is noted in
`optimizer/predicates.py`'s docstring so the idioms cannot silently
diverge.

### C.4 — acceptance matrix (behavioral equivalence before cut-over)

For every supported candidate shape, baseline-vs-rewritten primary-key-set
equality before the old behavior is removed:

- reverse FK, forward M2M, reverse M2M, `GenericRelation`;
- duplicate matching children; no matching children; no related rows;
- nullable child field `isnull=True` / `isnull=False` (including a parent
  with zero related rows);
- two active leaves on the same relation matching different children
  (cross-row AND — separate existence branches asserted in SQL);
- one positive multi-lookup invocation that must bind to a single child
  row;
- the negated split-across-rows range counterexample from the review
  (baseline `exclude(children__value__gte=1, children__value__lte=9)`
  keeps split-row parents excluded);
- `exclude=True` single-lookup leaves;
- `in=[]`, mixed valid/invalid integer `in`, GlobalID list handling;
- direct, `and`, `or`, `not` GraphQL filter-tree positions;
- untouched: explicit consumer `distinct=True`, `method=` filters, custom
  filter subclasses, `Meta.filter_overrides` — plus a test that an
  expanded leaf is classified against the root model, not the child;
- **inactive candidate leaves attach nothing**: a request activating one
  filter on a form with many to-many candidates produces exactly one
  `EXISTS` and one `_dst_` alias (the B1 no-op rule, asserted in SQL);
- a filterset constructed directly before finalization (unexpanded
  surface, names absent from the C.2 mapping) degrades to today's
  behavior;
- regression coverage through an **ordinary generated `CharFilter`** (the
  common upstream path), not only the package's custom filter classes.

### C.5 — live fakeshop proof

The primary regression uses the existing `Genre -> books` reverse-M2M
surface over `allLibraryGenresConnection` (no models, no migrations): seed
one genre linked to two books whose titles both match, filter via the
**public flat `booksTitle` input** (the defective path today), select
`totalCount` + edges + page info, assert one genre edge and root count of
one. The nested `books: {title: ...}` spelling rides along only as the
row-preserving control — it already goes through
`_apply_related_constraints` and cannot earn the new compiler's coverage.

## What this deliberately does not change

- `OptimizationPlan` and the selection walker/cache — no predicate or
  request value enters the plan cache.
- `OrderSet`'s row-preserving `Min`/`Max` to-many ordering.
- The nested `RelatedFilter` branch machinery (`pk__in` composition).
- Consumer-visible result sets for currently-**correct** paths — identical
  rows, better SQL. (The flattened-leaf duplicate-row defect is a bug fix:
  result sets there change to the correct ones.)
- Everything card-049-shaped: no `search:` argument, no `Meta.search_fields`
  handling, no pipeline step, no same-value OR grouping, no
  `Meta.search_strategy`, no benchmark harness, no release-state artifacts.

## Sequencing and validation

1. Freeze both defects (C.1 failing tests).
2. Candidate metadata + provenance after expansion (C.2).
3. Strict classifier + separate lookup validation (Slice A).
4. Neutral correlated-`EXISTS` primitive + full-namespace alias allocator
   (Slice B); pin `pk=OuterRef("pk")` on Django 5.2 and 6.0 (isolated
   `/tmp` venvs per the matrix-testing rule) before considering per-column
   expansion.
5. FilterSet leaf adapter invoking the original filter against the
   correlated inner root (C.3).
6. Prove the acceptance matrix (C.4) before changing production routing.
7. Cut over direct and flattened generated leaves.
8. Live `booksTitle` connection regression + SQL-shape assertions (C.5).
9. Validate Django 5.2/6.0, SQLite/PostgreSQL, multi-database aliases.
10. Leave search grouping and the `search:` surface to card 049.

After every edit: `uv run ruff format .` and `uv run ruff check --fix .`
only; tests run when explicitly requested; the change must hold
`fail_under = 100` when the suite runs. Before any commit: pre-commit hooks
— and the tracked-path hook may require a constants-only sync commit since
the previous commit added tracked files.

## Risks

- **SQL-shape change on shipped filters.** Same rows on correct paths,
  different plans; accepted per the root-cause mandate. The flattened-leaf
  fix changes wrong result sets to right ones — called out in review notes.
- **Low-selectivity regime.** Many independent `EXISTS` branches over a
  large root set can lose to one multi-join + `DISTINCT` on some planners.
  No escape hatch here (card 049 holds `Meta.search_strategy` in reserve);
  structure is gated in tests, wall-clock never.
- **Eligibility misclassification.** Fail-closed provenance means the
  failure mode is a missed optimization, never a wrong result set.
- **Upstream drift.** The applicator mirrors
  `BaseFilterSet.filter_queryset`'s loop; a django-filter upgrade that
  changes that loop shows up as a loud test diff against the retained
  upstream assertion, not silent divergence.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[repro]: ../to-many-search-optimizer-reproduction.md

<!-- docs/ -->
[feedback]: feedback.md
[part1-plan]: row-preserving-predicates-part1-plan.md
[spec-049]: spec-049-search_fields-0_1_2.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
