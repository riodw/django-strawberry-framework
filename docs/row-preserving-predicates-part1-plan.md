# Part 1 plan: row-preserving predicate machinery, enacted now (Rev 4)

## Identity and completion ownership

This document is the working plan for the **pre-card groundwork slice of
[spec 049][spec-049]** (its "Slice 0"): the shipped-defect fixes and
search-independent machinery land ahead of card `TODO-BETA-049-0.1.2`, and
that card owns the completion bookkeeping for everything this plan ships —
`docs/GLOSSARY.md`, `docs/TREE.md`, `KANBAN.md`, and the
`django_strawberry_framework/exceptions.py::OptimizerError` raise-site
documentation (second Part 1 review, findings 9 and 10). The plan itself
carries a final documentation slice (Slice D) so the shipped `FilterSet`
semantics change and the new `optimizer/predicates.py` module never sit
undocumented between Part 1 landing and card 049 wrapping. Version and
`CHANGELOG.md` ownership stay with the maintainer; no `CHANGELOG.md` entry
is added unless separately requested.

## Purpose

This plan enacts the "now" half of the to-many fan-out investigation
([`to-many-search-optimizer-reproduction.md`][repro]): everything that fixes
shipped behavior or builds search-independent machinery lands ahead of card
`TODO-BETA-049-0.1.2`, so that card later wires the `search:` surface onto a
finished engine ([spec-049][spec-049], Decision 7). The postponed half — the
`search:` argument, `Meta.search_fields` validation, the pipeline step, live
search fixtures, benchmarking — stays with the respecced card.

Rev 2 incorporated the first adversarial review ([`feedback.md`][feedback])
in full; Rev 3 folded in the Fable-agent round (adapter no-op detection,
metadata build-site mechanics, package filter-class eligibility). Rev 4
incorporates the second maintainer review (all claims empirically
verified): origin-scoped classification (finding 1), frozen
generation-provenance records replacing the boolean marker and the
class allowlist (finding 2), candidate metadata inside the atomic
expansion/reset lifecycle (finding 3), `distinct` suppression inside the
existence body (finding 4 — `Query.exists()` clears select and ordering
but never the `distinct` flag), the compositional multiset contract for
pre-fanned inputs (finding 5, maintainer-decided), removal of the
evaluated-outer-queryset rejection (finding 6), the permanent test-local
baseline oracle (finding 7), the direct-deep live proof (finding 8), and
the identity/documentation ownership above (findings 9–10).

The first review's verified corrections continue to shape the plan:

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

## The multiset contract (finding 5 — maintainer-decided)

Every framework-generated relational predicate behaves like a **SQL
selection over the queryset it receives**: each existing root-row
occurrence is either retained exactly once or removed. A framework
predicate never multiplies rows through framework-generated joins and
never collapses duplicates already present because of the consumer's
`get_queryset()`, annotations, joins, or earlier custom filters. Consumer
ordering and any explicit consumer-authored `.distinct()` are preserved
untouched.

The framework-added global `.distinct()` is removed: deduplicating
arbitrary input is outside a filter predicate's responsibility, and today
it masks consumer query semantics as a side effect. The root-cause fix is
row-preserving correlation that leaves the incoming queryset's
multiplicity alone — **not** inspecting Django's private `alias_map`,
**not** rejecting valid pre-fanned querysets, and **not** a normalization
boundary. Consumers that relied on the accidental global deduplication
were depending on incorrect legacy behavior; the correction is documented
as a behavioral fix (Slice D), without a `CHANGELOG.md` entry unless
separately requested.

This contract is testable and tested (C.4): ordered primary-key
**sequences** — never sets — plus duplicate multiplicity, `count()`, and
pagination, across non-fanned, pre-fanned, explicitly-`distinct`, and
custom-filter-produced inputs. Generated predicates introduce no
duplicates; existing consumer duplicates survive unchanged; live
`/graphql/` regression coverage wherever the shape is reachable.

## Architecture: three layers, filter semantics live in the adapter

Per first-review finding 8, the reusable machinery stays neutral and the
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
   decomposition included — with the framework-added `distinct` flag
   scoped out for the duration, per C.3a), and asks layer 2 to attach the
   positive `Exists(filtered_inner)`.

This "invoke the original filter against the correlated inner root" shape is
what makes the rewrite semantics-preserving without reimplementing any
filter class: multi-lookup invocations keep their per-condition Django
compilation (including `split_exclude` for excludes) *inside* the subquery,
where the correlation — not a hand-built body — is the only new element.

## Slice A — structured path classification

Files: `django_strawberry_framework/utils/relations.py`,
`tests/utils/test_relations.py`.

Per first-review finding 5, classification and lookup validation are
**separate contracts**:

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
  loud — but **only on inputs proven to be framework-generated model
  paths** (see C.2's origin rule; declared/custom names are never fed to
  the strict classifier).
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
    implementation**, per first-review finding 6: on the validated runtime
    it compiles composite pks to a correct tuple comparison. The version
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
  - Input validation covers what actually creates hazards: the inner root
    model matches the outer model and both resolve to the same database
    alias. **There is no evaluated-outer-queryset rejection** (second
    review, finding 6): Django permits further construction after
    evaluation — `.filter()` / `.alias()` clone the query and execute a
    fresh statement — and today's FilterSet path accepts such querysets;
    an outer `_result_cache` is never embedded in SQL. That the *inner*
    queryset must never execute independently is an implementation
    invariant documented on the primitive, not an input guard. Test:
    `list(source_qs)` followed by an eligible filter application, with
    parity against the never-evaluated source.

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

Guards and claims, per first-review finding 9:

- Empty/no-op input returns the queryset untouched **before** any guard
  runs (the identity contract wins first).
- The combined-queryset preflight (`queryset.query.combinator`) runs only
  when attachment is actually required, and raises a typed error whose
  family is chosen deliberately: this is runtime query state, not consumer
  configuration, so it raises `OptimizerError` rather than
  `ConfigurationError`, with a message naming the combinator. The branch is
  genuinely unreachable from a live `/graphql/` query (the pipeline never
  produces combined querysets), so its coverage lands in `tests/` under
  the live-first mandate's unreachability fallback. Slice D extends the
  `OptimizerError` docstring with this raise site (second review,
  finding 10); if a live consumer can ever reach it, the GraphQL wrapping
  path is tested there too.
- The count invariant is phrased and tested as "**the compiler adds no
  distinct wrapper**": flat-`COUNT(*)` assertions start from a plain root
  queryset; the multiset contract's C.4 rows cover consumer querysets that
  are already distinct/annotated/projected/pre-fanned.

Core SQL-shape tests: root `alias_map` excludes membership/child tables,
`query.distinct is False`, `EXISTS` present and correlated on the root pk,
one row per parent with duplicate matching children, aliases absent from
selected columns, database alias preserved, **no `SELECT DISTINCT` inside
the existence body** (finding 4's inner-shape assertion, proven end to end
at the adapter in C.3a).

## Slice C — candidate metadata + the FilterSet leaf adapter

Files: `django_strawberry_framework/filters/sets.py` (adapter + metadata),
`django_strawberry_framework/sets_mixins.py` (lifecycle registration),
filter tests, live fakeshop coverage under `examples/fakeshop/test_query/`.

### C.1 — freeze both defects first

Failing tests pinning today's behavior before any change: a direct deep
generated path fans out through JOIN+`distinct=True`; a flattened
`RelatedFilter` leaf (`genres__name__icontains`-shaped) duplicates parent
rows and corrupts a connection `totalCount` with `distinct=False`.

### C.2 — frozen generation provenance + origin-scoped classification

Second-review findings 1 and 2 rework this slice's mechanics. Two rules
replace Rev 3's "classify every entry" build and its boolean
pre-stamp marker:

**Origin before classification (finding 1).** Declared/custom filters and
`Meta.filter_overrides` products may legitimately target an annotation,
alias, or method-owned name that is not a Django model path (a declared
method filter with `field_name="computed_rank"` is valid when its method
interprets that name). Strictly classifying such a name would turn a
working, intentionally ineligible declaration into a finalization failure
— violating both "ineligible leaves keep today's behavior byte-for-byte"
and "the failure mode is a missed optimization." Therefore:

- framework-default-generated direct and expanded leaves are strict
  candidates; a path-resolution failure **there** is a
  framework/configuration defect and raises;
- declared/custom and `filter_overrides` leaves are immediately
  ineligible and are **never fed to the strict classifier** — their
  metadata row carries `path_plan=None` (equivalently, the candidate
  mapping contains only proven generated candidates);
- an expanded leaf **inherits the child leaf's origin**; appearing in
  `_expand_related_filter`'s output does not make a declared child
  "expanded generated."

Tests: a declared method filter and a declared custom-subclass filter
whose `field_name` is not model-resolvable both still build and execute
unchanged.

**Frozen provenance record, not a saved boolean (finding 2).** A private
"pre-framework distinct" attribute on `default` cannot carry the origin
decisions eligibility needs, verified on the shipped code:

- `filter_for_field` receives a `default` already produced through
  `django_filters.filterset.BaseFilterSet.filter_for_lookup`, whose
  defaults are pre-merged with `Meta.filter_overrides` — a bare `True`
  cannot distinguish upstream default from consumer override;
- the own-PK and Relay-relation branches of the package's
  `filter_for_field` return **new** `GlobalIDFilter` /
  `GlobalIDMultipleChoiceFilter` instances — an attribute left on
  `default` never reaches the replacement;
- upstream synthesizes dynamic `ConcreteInFilter` / `ConcreteRangeFilter`
  subclasses inside `filter_for_lookup`, so an exact-class allowlist is
  version-sensitive and drifts (Rev 3's M2 enumerated-class list is
  **withdrawn** as the eligibility mechanism);
- a consumer overriding `filter_for_field` can replace or mutate the
  framework result, which must not retain a stale "safe" marker.

The replacement: **one frozen provenance record persisted on the actual
returned filter instance** at the moment of generation. It distinguishes
at least framework-default generation, package-owned replacement
(the GlobalID branches — safe because the framework constructed them),
declared filter, and `filter_overrides` generation; records whether the
framework added `distinct`; and survives every replacement and deepcopy
explicitly — the package's replacement branches stamp the new instance
themselves, and `_expand_related_filter`'s expanded copies inherit the
child's record and **append** "expanded from `<name>`" rather than
overwriting origin. Eligibility follows construction provenance:
package-owned and framework-default generation reached through the
unmodified default path are safe; declared, override-generated, and
consumer-overridden generation fail closed. This is stricter and more DRY
than any class list. A consumer that overrides `filter_for_field` and
returns its own object simply produces an instance without a
framework-stamped record — fail closed by construction.

The candidate metadata row (built only for proven generated candidates)
carries: the final classified path rooted at the owning
`FilterSet._meta.model` (Slice A), the provenance record (origin +
framework-added-`distinct` bit), and the inner-invocation eligibility
bit. Eligible = framework-generated leaf (direct or expanded, per the
provenance record), no consumer `method`, no consumer-origin `distinct`,
path crosses a many-side hop. Eligibility is never inferred from a class
name or from `method is None`. Ineligible leaves keep today's behavior
byte-for-byte — the failure mode is a missed optimization, never a
changed result set.

**Build-site mechanics** (Fable review M1, retained):

- The two filter surfaces diverge until lazy `RelatedFilter` targets
  resolve: `FilterSet.get_filters` writes the expanded set to
  `cls.base_filters` only under its `should_cache_expansion` gate
  (unresolved string targets skip the cache), and
  `FilterSetMetaclass.__new__` rebuilds `base_filters` bypassing the
  expansion override. The metadata mapping is therefore built **inside the
  same expansion build, under the same gate as `should_cache_expansion`**
  — never as a separate "after get_filters()" pass that could observe the
  unexpanded surface. Expanded origins are tracked per
  `_expand_related_filter` call, never rediscovered from prefixed strings.
- The adapter treats a `cleaned_data` name **absent from the mapping as a
  non-candidate** (fail closed). This path is reachable: a filterset
  constructed directly before finalization resolves lazy targets presents
  the unexpanded 5-field surface and must degrade to today's behavior.

**Atomic lifecycle (finding 3).** `SetLifecycleAttrs.binding_attrs` names
exactly owner / expansion cache / reentry guard, and
`django_strawberry_framework/utils/inputs.py::clear_generated_input_namespace`
deletes only those three — a fourth free-floating class attribute would
survive `registry.clear()` and pair stale metadata with a rebuilt
`base_filters`. The fix is single-sited: filters and candidate metadata
are published as **one immutable expansion snapshot** — the completed
build produces a frozen record owning both the filter mapping and the
candidate metadata, stored under the existing per-class `cls.__dict__`
gate, with `get_filters()` continuing to return the snapshot's filter
mapping for API compatibility. The snapshot's storage slot(s) are
registered in `SetLifecycleAttrs` (extended with family-specific extra
reset attributes if a second slot is needed) so `registry.clear()` resets
filters and metadata together, by construction. Both values publish only
after a successful build. Tests: build failure (nothing published), retry
after failure, subclass isolation (a subclass never observes its parent's
snapshot), unresolved lazy targets (no snapshot cached), and
clear/rebuild (no stale metadata observable between the clear and the
next completed expansion).

### C.3 — the flat-leaf applicator

Per first-review finding 1, `FilterSet.filter_queryset` stops delegating
leaves wholesale to `BaseFilterSet.filter_queryset` and instead runs a
framework-owned applicator mirroring upstream's loop exactly:

- iterate `self.form.cleaned_data` in order;
- non-candidates (including names absent from the C.2 mapping): call the
  original filter unchanged;
- candidates: build `correlated_inner_root(queryset)`, apply **the
  original filter invocation** to that inner root through the C.3a
  invocation helper (so `filter()` vs `exclude()`, multi-lookup
  decomposition, `in=[]` semantics, GlobalID decoding all run exactly as
  upstream wrote them — Django's own `split_exclude` handles negation
  *inside* the subquery), then `attach_exists` and
  `.filter(positive_branch)`;
- **no-op detection (Fable review B1 — load-bearing control flow):**
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

### C.3a — suppress the framework `distinct` inside the existence body

Second-review finding 4, verified in Django source: `Query.exists()`
clears the select list and ordering but **does not clear the `distinct`
flag**, so invoking an eligible `distinct=True` filter unchanged against
the inner root compiles `EXISTS(SELECT DISTINCT 1 … LIMIT 1)` — logically
equivalent but not performance-inert (unique/sort planning inside every
correlated branch), and this rewrite exists for performance. Rev 3's "the
old stamp is inert inside the body" claim is withdrawn.

The adapter therefore invokes eligible filters through a **named
invocation helper** that suppresses the framework-added `distinct` for
the duration of the inner invocation while still calling the filter's
original `filter()` method. Only the framework-added flag (known from the
C.2 provenance record) is suppressed — consumer-origin `distinct` filters
are ineligible and never reach this helper. No class-level or base filter
is ever mutated: the live FilterSet owns a per-instance deepcopy, so the
helper scopes the change with `try/finally`, restoring the instance flag
even when decoding or queryset construction raises (an isolated
invocation copy is an acceptable alternative only with its cost
measured).

Assertions on emitted SQL, both sides: no outer `DISTINCT`, no inner
`SELECT DISTINCT`, and the filter instance's flag restored after success
**and** after an exception. The PostgreSQL plan artifact compares the
actually emitted distinct-free inner shape, never an idealized
hand-written query.

### C.4 — acceptance matrix (behavioral equivalence before cut-over)

**The permanent baseline oracle (finding 7).** "Freeze failing tests" is
the local red/green sequence, but the committed final suite cannot depend
on old production routing after cut-over. The suite therefore defines a
**test-local oracle** that directly invokes the same filter instance on
the outer queryset to obtain django-filter's baseline, while the
production FilterSet invokes it inside `EXISTS`. The oracle is visibly
test-local — no strategy flag, no second production compiler ships.
Comparisons use **ordered rows and counts wherever multiplicity is part
of the contract** (the multiset contract makes it part of the contract
almost everywhere); sets appear only where a test explicitly targets
boolean membership semantics. The flattened-path defect additionally
asserts the old oracle duplicates while the production result does not.

For every supported candidate shape, baseline-vs-rewritten equivalence
before the old behavior is removed:

- reverse FK, forward M2M, reverse M2M, `GenericRelation`;
- duplicate matching children; no matching children; no related rows;
- nullable child field `isnull=True` / `isnull=False` (including a parent
  with zero related rows);
- two active leaves on the same relation matching different children
  (cross-row AND — separate existence branches asserted in SQL);
- one positive multi-lookup invocation that must bind to a single child
  row;
- the negated split-across-rows range counterexample from the first review
  (baseline `exclude(children__value__gte=1, children__value__lte=9)`
  keeps split-row parents excluded);
- `exclude=True` single-lookup leaves;
- `in=[]`, mixed valid/invalid integer `in`, GlobalID list handling;
- direct, `and`, `or`, `not` GraphQL filter-tree positions — with every
  consumer-visible behavior here that the fakeshop schema can reach also
  proven at the live HTTP tier (finding 8);
- untouched: explicit consumer `distinct=True`, `method=` filters, custom
  filter subclasses, `Meta.filter_overrides` — plus declared
  method/custom filters with **non-model-resolvable** `field_name`s that
  must build and execute unchanged (finding 1), and a test that an
  expanded generated leaf is classified against the root model, not the
  child;
- **multiset-contract rows (finding 5):** ordered primary-key sequences,
  duplicate multiplicity, `count()`, and connection pagination over
  (a) a non-fanned input, (b) a deliberately pre-fanned consumer
  `get_queryset`, (c) an explicitly consumer-`distinct()` input, and
  (d) a custom-filter-produced input — generated predicates introduce no
  duplicates, existing consumer duplicates survive unchanged, consumer
  ordering preserved;
- an **evaluated outer queryset** (`list(source_qs)` first) filtered by an
  eligible candidate, with parity against the unevaluated source
  (finding 6);
- **inactive candidate leaves attach nothing**: a request activating one
  filter on a form with many to-many candidates produces exactly one
  `EXISTS` and one `_dst_` alias (the B1 no-op rule, asserted in SQL);
- a filterset constructed directly before finalization (unexpanded
  surface, names absent from the C.2 mapping) degrades to today's
  behavior;
- regression coverage through an **ordinary generated `CharFilter`** (the
  common upstream path), not only the package's custom filter classes.

Provenance/origin internals, snapshot-lifecycle transitions, and alias-map
assertions stay in package tests; consumer-visible `and` / `or` / `not`,
empty-list, GlobalID, count, and pagination behavior moves to live HTTP
wherever the existing fakeshop schema can reach it (finding 8).

### C.5 — live fakeshop proof, both origins

Two live regressions, one per generated-origin branch (finding 8 — the
live-tier rule requires a live proof for each reachable metadata-origin
path):

1. **Expanded generated origin** (the public flattened-`RelatedFilter`
   defect): the existing `Genre -> books` reverse-M2M surface over
   `allLibraryGenresConnection` (no models, no migrations): seed one genre
   linked to two books whose titles both match, filter via the **public
   flat `booksTitle` input** (the defective path today), select
   `totalCount` + edges + page info, assert one genre edge and root count
   of one. The nested `books: {title: ...}` spelling rides along only as
   the row-preserving control — it already goes through
   `_apply_related_constraints` and cannot earn the new compiler's
   coverage.
2. **Direct deep generated origin**: a non-colliding direct deep to-many
   lookup added to an existing library FilterSet (or, if none fits, a
   small no-migration FilterSet/type surface over an existing model),
   executed over HTTP: a duplicate-matching to-many relation yields one
   edge and a correct `totalCount`.

## Slice D — documentation of the shipped semantics (completion slice)

Owned by card 049's completion bookkeeping (see Identity above), but the
Part 1 landing itself updates the source-of-truth artifacts its changes
make stale:

- the **multiset contract** becomes the documented production contract for
  framework-generated relational predicates, including the note that the
  removed global deduplication was accidental legacy behavior (no
  `CHANGELOG.md` entry unless separately requested);
- `django_strawberry_framework/exceptions.py::OptimizerError`'s docstring
  gains the predicate-attachment (combined-queryset) raise site
  (finding 10);
- `docs/TREE.md` regenerates for the new `optimizer/predicates.py` and
  `tests/optimizer/test_predicates.py` modules (script-rendered — module
  docstrings required);
- `docs/GLOSSARY.md` / `KANBAN.md` updates flow through card 049's DB
  fold-in per the shipping-slice rule; the staged TODO pseudocode blocks
  in `filters/sets.py`, `optimizer/predicates.py`, and
  `utils/relations.py` are consumed (deleted) by their implementing
  steps.

## What this deliberately does not change

- `OptimizationPlan` and the selection walker/cache — no predicate or
  request value enters the plan cache.
- `OrderSet`'s row-preserving `Min`/`Max` to-many ordering.
- The nested `RelatedFilter` branch machinery (`pk__in` composition).
- Consumer-visible result sets for currently-**correct** paths over
  row-preserving inputs — identical rows, better SQL. (Two deliberate
  corrections are documented: the flattened-leaf duplicate-row defect fix,
  and the multiset contract's end to accidental global deduplication of
  pre-fanned consumer inputs.)
- Everything card-049-shaped: no `search:` argument, no `Meta.search_fields`
  handling, no pipeline step, no same-value OR grouping, no
  `Meta.search_strategy`, no benchmark harness. Release-state artifacts
  beyond Slice D's source-of-truth updates stay with card 049.

## Sequencing and validation

1. Freeze both defects (C.1 failing tests).
2. Provenance records at generation + origin-scoped candidate metadata in
   the atomic expansion snapshot (C.2, including the `SetLifecycleAttrs`
   registration).
3. Strict classifier + separate lookup validation (Slice A).
4. Neutral correlated-`EXISTS` primitive + full-namespace alias allocator,
   no evaluated-outer guard (Slice B); pin `pk=OuterRef("pk")` on Django
   5.2 and 6.0 (isolated `/tmp` venvs per the matrix-testing rule) before
   considering per-column expansion.
5. FilterSet leaf adapter invoking the original filter against the
   correlated inner root through the distinct-suppressing helper
   (C.3 + C.3a).
6. Prove the acceptance matrix against the test-local baseline oracle
   (C.4) before changing production routing.
7. Cut over direct and flattened generated leaves; remove the
   framework-added global `distinct` per the multiset contract.
8. Live proofs for both generated origins + SQL-shape assertions (C.5).
9. Validate Django 5.2/6.0, SQLite/PostgreSQL, multi-database aliases;
   capture the PostgreSQL plan artifact from actually emitted SQL.
10. Slice D documentation updates; leave search grouping and the `search:`
    surface to card 049.

After every edit: `uv run ruff format .` and `uv run ruff check --fix .`
only; tests run when explicitly requested; the change must hold
`fail_under = 100` when the suite runs. Before any commit: pre-commit hooks
— and the tracked-path hook may require a constants-only sync commit since
the previous commit added tracked files.

## Risks

- **SQL-shape change on shipped filters.** Same rows on correct
  row-preserving paths, different plans; accepted per the root-cause
  mandate. The flattened-leaf fix and the multiset contract change wrong
  or accidental result sets to correct ones — both called out in Slice D.
- **Low-selectivity regime.** Many independent `EXISTS` branches over a
  large root set can lose to one multi-join + `DISTINCT` on some planners.
  No escape hatch here (card 049 holds `Meta.search_strategy` in reserve);
  structure is gated in tests, wall-clock never.
- **Eligibility misclassification.** Fail-closed construction provenance
  means the failure mode is a missed optimization, never a wrong result
  set — and never a finalization failure for a working declared filter.
- **Upstream drift.** The applicator mirrors
  `BaseFilterSet.filter_queryset`'s loop; a django-filter upgrade that
  changes that loop shows up as a loud test diff against the retained
  upstream assertion, not silent divergence. Provenance is stamped at the
  package's own generation sites, so upstream's dynamic
  `ConcreteInFilter`/`ConcreteRangeFilter` synthesis cannot drift the
  eligibility rule.

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
