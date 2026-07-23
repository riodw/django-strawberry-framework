# Adversarial implementation review: row-preserving predicates Part 1

## Verdict

The correlated-`EXISTS` architecture is still the correct root-cause design.
The implementation has strong foundations:

- `django_strawberry_framework/utils/relations.py::classify_path` correctly
  separates semantic relation kind from `PathInfo.m2m` multiplicity and identifies
  the reverse-FK boundary in the Medtrics-shaped path.
- `django_strawberry_framework/optimizer/predicates.py::attach_exists` keeps
  predicate bodies out of the selection optimizer, allocates reserved aliases,
  and preserves the incoming queryset's multiplicity.
- `django_strawberry_framework/filters/sets.py::FilterSet._apply_flat_leaves`
  invokes the original filter in the correlated inner query and preserves
  independent-leaf AND semantics.
- The exact Python 3.10 / `Django==5.2.0` CI node exists on every push and pull
  request.

Part 1 is not ready to sign off as fully implemented, however. The candidate
authorization mechanism is not actually fail-closed under supported
django-filter customization seams. This can route consumer-owned filter
semantics through the new compiler and suppress consumer `distinct`, contrary
to the core compatibility contract. There is also one adjacent `to_field`
correctness defect and several mandatory acceptance rows are explicitly
deferred or marked N/A.

No production files were changed during this review. Per repository policy,
pytest was not run because this was a review request rather than an explicit
test-run request. The concrete provenance results below were reproduced in
isolated Django processes against the current checkout.

## Blocker 1 — the frozen candidate row is stale authority, not fail-closed provenance

The intended invariant in the [Part 1 plan][part1-plan] is:

> A consumer override or mutation must fail closed to the original outer
> invocation; only a filter proven to be framework-generated may enter the
> correlated adapter.

The implementation does not enforce that invariant. It authorizes a request
using only the filter name and the class-time
`CandidateFilterMetadata.eligible` bit:

```python
candidate = snapshot.candidates.get(name)
filter_instance = self.filters[name]
if candidate is None or not candidate.eligible:
    return_original_behavior()
else:
    invoke_live_filter_inside_exists(filter_instance)
```

There is no proof that the live `self.filters[name]` is still the generated
filter for which the frozen candidate row was built. The snapshot never checks
the live instance's provenance token, class, `field_name`, `lookup_expr`,
`method`, `exclude`, or other semantic state before moving its invocation into
the inner query.

This is reachable through several normal django-filter extension seams:

1. A consumer `filter_for_field()` override that calls `super()`, mutates the
   returned filter, and returns it retains the framework stamp. The production
   docstring acknowledges this residual and calls it harmless, but it is the
   exact consumer-mutation case the plan says must fail closed.
2. A consumer `filter_for_lookup()` override returns a custom generated filter
   class before the package's `filter_for_field()` wrapper stamps the result as
   `framework_default`.
3. A consumer class-level `FILTER_DEFAULTS` override is a standard
   django-filter generation hook, but
   `FilterSet._generation_origin_for_field()` inspects only
   `Meta.filter_overrides`.
4. A consumer `FilterSet.__init__()` can replace or mutate
   `self.filters[name]` after django-filter deep-copies `base_filters`; the
   adapter still consults the class snapshot by name.
5. `ExpansionSnapshot` is a frozen dataclass, but its `filters` member is the
   same mutable `OrderedDict` returned by `get_filters()` and assigned to
   `base_filters`. A caller can therefore mutate the supposedly atomic filter
   half without rebuilding the candidate half.

The following results were reproduced against the current code:

```text
MutatesSuper CharFilter exclude=True framework_default eligible=True
OverridesLookup CustomGenerated exclude=False framework_default eligible=True
Custom FILTER_DEFAULTS CustomText framework_default eligible=True
ReplacesAtInit field_name=title live_stamp=False snapshot_path=genres__name eligible=True
```

The last case is especially direct: the live request filter is an unstamped
`title` filter, while the adapter authorizes it using a stale
`genres__name` candidate row. An active request will invoke that consumer
replacement inside a correlated subquery even though the replacement itself
has no provenance.

This is not merely an optimization-boundary concern. A consumer filter can
depend on outer annotations, introduce joins or annotations, intentionally
deduplicate the incoming queryset, or implement an `exclude` contract. Moving
that invocation to a fresh `_base_manager` root can change the result set, not
just its SQL shape.

### Required root-cause correction

Candidate authorization must be a live capability check, not a name lookup:

1. Mint an opaque generation token only for an invocation that completed
   through the package-owned, unmodified generation path. A subclass override
   of `filter_for_field`, `filter_for_lookup`, or `FILTER_DEFAULTS` must fail
   closed unless the framework has an explicit, proven contract for it.
2. Store that token plus an immutable semantic fingerprint in the candidate
   row. At minimum the fingerprint must cover the generated filter class,
   `field_name`, `lookup_expr`, `method`, `exclude`, and the distinct ownership
   decision.
3. Require the live per-request filter to carry the same token and match the
   frozen fingerprint immediately before correlated invocation. A missing or
   mismatched token/fingerprint runs the original filter on the outer queryset.
4. Ensure mutation of the cached filter mapping cannot silently leave candidate
   metadata authoritative. Either stop exposing the owned mutable mapping or
   make the live capability check invalidate every such mutation.
5. Add executable regressions for all five seams above, including a custom
   filter whose result differs when run against the fresh inner root. Assertions
   must prove the original outer behavior, not only the absence of an exception.

This should not be repaired with a filter-class allowlist. The plan correctly
rejects that architecture because django-filter creates dynamic lookup
subclasses and consumer classes are open-ended.

## Blocker 2 — `Meta.filter_overrides` origin detection uses the wrong field

Even without subclass hooks or post-generation mutation, a declared
`Meta.filter_overrides` product can be misclassified as
`framework_default`.

`django_filters.filterset.BaseFilterSet.filter_for_lookup` chooses its override
after resolving the lookup's effective field. In particular, `isnull` selects
the `BooleanField` filter override regardless of the original model field.
`django_strawberry_framework/filters/sets.py::FilterSet._generation_origin_for_field`
instead checks the original field passed to `filter_for_field()`.

The concrete current result for a generated many-side
`genres__name__isnull` leaf with a consumer
`Meta.filter_overrides[models.BooleanField] = CustomBoolean` is:

```text
filter class: CustomBoolean
recorded origin: framework_default
candidate eligible: True
```

That directly contradicts the plan's rule that every `filter_overrides`
product is consumer-origin and ineligible. It also means the current
`test_generation_provenance_override_generated_for_meta_filter_overrides`
proves only a direct-field case, not django-filter's output-field and
lookup-specific branches.

Origin must be captured at the same resolved-field decision that actually
selects the filter class. Do not independently re-derive it later from the
unresolved model field. Required tests include at least:

- `BooleanField` override selected by an `isnull` lookup on a many-side path;
- a transform whose output field selects a different override;
- a class-level `FILTER_DEFAULTS` override;
- a consumer `filter_for_lookup()` override.

This can share the capability-token correction from Blocker 1; it should not
grow into another parallel origin oracle.

## High 3 — stripping `to_field_name` fixes form construction but can return wrong rows

`django_strawberry_framework/filters/sets.py::_strip_model_choice_extras`
removes both `queryset` and `to_field_name` when replacing an upstream
model-choice relation filter with `GlobalIDFilter` or
`GlobalIDMultipleChoiceFilter`. Removing incompatible form-field kwargs is
necessary, but it is not a complete semantic conversion.

`django_strawberry_framework/filters/base.py::GlobalIDFilter.filter` decodes a
GlobalID to its node id and delegates that raw value to:

```python
queryset.filter(<relation field>=decoded_node_id)
```

For `ForeignKey(to_field="code")`, Django interprets that scalar as the remote
`code`, not as the target object's primary key. A normal Relay GlobalID
contains the target node's primary key. When `target.pk != target.code`, the
newly constructible filter therefore compares the wrong values and returns the
wrong rows. The new tests prove only that the form field constructs; they do
not execute a `to_field` relation filter.

The root fix is to preserve relation-target metadata outside the incompatible
form kwargs and compile GlobalID relation predicates explicitly against the
target primary key, for example the semantic equivalent of
`relation__pk=<decoded node id>` / `relation__pk__in=<decoded ids>`. That keeps
Relay identity independent of the FK storage column and avoids a pre-query
object lookup. Add a real execution test where the target pk and referenced
non-pk value are intentionally different, covering both single and list
GlobalID forms where supported.

This finding is adjacent to, but more severe than, the Part 1 matrix's missing
`to_field` traversal row: it is a consumer-visible correctness hole in code
added by the implementation.

## High 4 — the committed acceptance suite does not satisfy the plan

The implementation comments explicitly defer requirements that the plan marks
mandatory:

### Missing ORM topology and compatibility proofs

- `tests/filters/test_sets.py` labels the `to_field` C.4 row N/A because
  fakeshop has no such model and says an inline package-test model is out of
  scope. That is contrary to the plan and to this repository's test-placement
  policy: package tests may use an inline model when no live example topology
  exists.
- `tests/optimizer/test_predicates.py::test_composite_pk_correlation_is_outerref_pk`
  inspects a single-column `Book` predicate and explicitly defers composite-pk
  compilation and execution to a future matrix step. It does not prove the
  plan's composite-pk claim on Django 5.2.0 or Django 6.0.
- The exact Python 3.10 / Django 5.2.0 CI node is correctly present, but it can
  only prove the cases that exist. It does not turn the single-column
  introspection test into composite-pk execution evidence.

### Incomplete Medtrics-shaped production oracle

The permanent raw ORM test correctly freezes the five-row fan-out sequence for:

```python
Q(note__icontains="Cardio")
| Q(book__loans__patron__email__icontains="Cardio")
```

The production adapter tests never execute the matching mixed direct/relational
OR. They execute only the relational leaf and therefore return two rows,
excluding `direct_only`. Consequently they do not prove the plan's central
production oracle:

```text
[relation_and_direct, relation_only, direct_only]
```

The live direct-deep test uses `allLibraryLoans`, which is a list field. It
asserts only two IDs and has no `totalCount`, cursor, or page-boundary
assertions. The package-tier offset slices added as a substitute do not satisfy
the live-first requirement or the stated connection contract. The expanded
genre origin has a good live connection test, but it does not substitute for
the independent reverse-FK-behind-to-one category.

### Other unproven matrix rows

- There is no executable `exclude=True` single-lookup leaf row. The test text
  instead declares generated flat leaves never carry `exclude=True`.
- The new eligible-candidate tests cover direct application and `not`, but do
  not cover eligible leaves in all required `and` and `or` GraphQL tree
  positions.
- No Part 1 PostgreSQL `EXPLAIN`/plan artifact was added for the actually
  emitted distinct-free inner query.
- Database alias tests validate construction and mismatch guards, but there is
  no predicate execution proof on the sharded alias.

These are acceptance gaps, not requests for redundant unit coverage. Each one
pins a distinct semantic or compatibility boundary named by the plan. Either
implement them or revise the plan explicitly before calling Part 1 complete;
do not leave mandatory rows marked N/A/deferred inside the final suite.

## Medium 5 — the plan and implementation now disagree on legacy leniency

The latest implementation correctly noticed that simply catching
`PathResolutionError` and returning `False` changes legacy behavior for a path
such as `genres__nonexistent`: the old walker returned `True` as soon as it saw
the many-side `genres` hop. The new
`django_strawberry_framework/utils/relations.py::_lenient_traverses_to_many`
fallback preserves that behavior.

The [Part 1 plan][part1-plan] still says
`path_traverses_to_many` catches the typed error to retain its lenient legacy
`False`. That statement is no longer accurate. The implementation and its
32-path compatibility matrix are stronger than that sentence; update the plan
to state the actual rule:

- resolved valid paths use `classify_path()` / `PathInfo.m2m`;
- rejected paths replay the legacy walk so early many-side detection is
  preserved;
- the unique reverse-FK behavior is the one deliberate resolved-path
  correction.

Related documentation drift should be cleaned in the same pass:

- `FilterSet.filter_queryset` still says flat leaves are delegated through the
  inherited `super().filter_queryset()` call, immediately above code that no
  longer does that.
- `FilterSet.get_fields` contains the per-field `"__all__"` bullet twice.
- `ExpansionSnapshot` calls itself immutable even though its `filters`
  `OrderedDict` is externally mutable; either make that statement true or
  describe the narrower frozen-record/read-only-candidate guarantee.

## Medium 6 — inactive candidates still pay per-leaf construction cost

The no-op branch successfully prevents inactive candidates from attaching an
`EXISTS` alias, but it detects identity only after
`correlated_inner_root(queryset)` has been built and the filter has been
invoked. A form with sixteen inactive eligible leaves therefore performs
sixteen router/manager/query-clone/correlation constructions even though the
outer queryset remains unchanged.

This does not issue SQL and is not a correctness defect, but it weakens the
performance motivation for the no-op design. The existing test asserts only
that no aliases were attached; it does not pin how many inner roots were
constructed.

Do not add a blanket `if value in EMPTY_VALUES` shortcut: the package
deliberately gives explicit empty membership lists restrictive semantics in
some filters. Instead, either:

- freeze an explicit no-op policy as part of the same proven generation
  metadata and short-circuit only values whose original filter contract is
  known to be identity; or
- benchmark the construction cost and document that no-op means “no SQL
  attachment,” not “no inner-query construction.”

The first option is preferable if profiling shows meaningful overhead, but the
capability/provenance blockers must be fixed before adding more metadata to the
current snapshot design.

## Recommended correction order

1. Replace name-only candidate authorization with a live generation capability
   and semantic-fingerprint check.
2. Single-site resolved lookup-origin tracking so `Meta.filter_overrides`,
   `FILTER_DEFAULTS`, and generation method overrides fail closed.
3. Correct GlobalID relation filtering for `to_field` targets.
4. Add the missing topology, composite-pk, mixed-OR, live connection,
   exclude/tree-position, PostgreSQL-plan, and database-alias proofs.
5. Reconcile plan/source documentation with the behavior that remains.
6. Measure inactive-candidate construction overhead and encode a no-op policy
   only if the measurement justifies it.

The neutral classifier and `attach_exists()` primitive do not need to be
abandoned. The required architectural change is at the authorization boundary
between mutable/customizable django-filter objects and the neutral compiler.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[part1-plan]: row-preserving-predicates-part1-plan.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
