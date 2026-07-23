# Implementation-gate review: dynamic row-preserving search

## Verdict

**Part 1 is ready in principle; card 049 is not yet ready to implement.**

The shared row-preserving predicate design in
[`row-preserving-predicates-part1-plan.md`][part1-plan] addresses the original
cardinality defect at its source. For a plain `UserSchedule` root queryset, a
DSF search plan shaped like
`user -> group-user membership -> group -> name` can keep direct search arms
on the outer queryset and compile the membership arm as a correlated `EXISTS`.
That removes the search-created membership JOIN from the root query, so one
root row remains one SQL row and search needs no `.distinct()`. `totalCount`,
page boundaries, and cursor positions therefore operate on root rows rather
than membership rows.

The Part 1 plan also now preserves the incoming queryset as a multiset:
framework-generated predicates neither multiply rows nor collapse duplicates
already introduced by consumer SQL. That is the correct compositional
contract. The original Medtrics query starts from a plain root queryset, so its
expected result remains one occurrence per matching `UserSchedule`; a
consumer-supplied pre-fanned queryset deliberately remains pre-fanned.

Card 049's direct-OR-`EXISTS` composition can solve the complete Medtrics
search shape, including a root matching both a direct arm and the relational
arm, **after the five implementation blockers below are resolved**. Findings
1 and 2 are authorization correctness issues, not optional refinements.

## Blocking findings

### P0-1 — Hop visibility and the terminal predicate must share each to-many join alias

[Decision 12][spec-049] says each related visibility queryset is composed as a
membership constraint on its hop and ANDed with the terminal predicate. It
does not state the load-bearing ORM rule: every visibility membership
constraint and terminal predicate for one relational search arm must be
submitted in one conjunctive `.filter(branch_q)` call, or otherwise compiled
with an equally strong same-related-row guarantee.

[Django intentionally treats conditions across separate `.filter()` calls on a
multi-valued relation as conditions on potentially different related
rows][django-spanning-multivalued].
An isolated compile-time probe using the exact Part 1 reproduction path showed:

- sequential `book__loans__in=<visible loans>` and
  `book__loans__patron__email__icontains="Cardio"` filters allocated two
  separate inner `library_loan` relation aliases; and
- one filter containing both conjuncts allocated one shared relation alias.

The sequential form creates a related-data leak. A visible loan whose patron
email does not match can satisfy the visibility constraint while a hidden
sibling loan whose patron email does match satisfies the search predicate.
The visible root then qualifies solely because of the hidden sibling—the
precise existence oracle Decision 12 promises to prevent.

Required design change:

- Define one structured predicate branch per relational search arm or
  same-chain group.
- Build every hop-visibility membership predicate and that branch's terminal
  `icontains` predicate into one `Q` tree.
- Apply that tree in one `.filter()` call to the correlated inner root.
- For direct to-one relational arms, keep the hop visibility inside that arm's
  parentheses; never lift it outside the final search OR.
- Do not implement hop visibility as a loop of successive `.filter()` calls.
- If a compiler refactor cannot make alias sharing an explicit invariant,
  use separately correlated nested existence predicates rather than relying on
  accidental alias reuse.

Required regression:

- One root has two children on the same to-many hop: a visible nonmatching
  child and a hidden matching child. It must not match.
- The inverse control—a visible matching child—must match.
- Assert the inner query has one alias for the shared to-many path, in addition
  to asserting the result set. The result-only test is insufficient because a
  future fixture can accidentally make both aliases point at the same row.
- Repeat the counterexample at the `book__loans` root-model re-entry used by
  the Medtrics reproduction, not only on a direct M2M path.

### P0-2 — Root-model re-entry contradicts the registry-primary rule

Decision 12 makes two incompatible promises:

- every hop resolves its visibility type through the registry primary; and
- when a path re-enters the root model, the exact root type's own visibility
  hook is applied to the inner row.

Those are equal only in the single-type case or when the connection happens to
serve the primary type. They diverge when a connection serves a secondary
`DjangoType`, which Decision 14 and the exact-owner tests explicitly support.
For a secondary `LoanType`, `book__loans` currently points back to the `Loan`
model; a model-only `registry.get(Loan)` resolves the primary, not the
connection's exact secondary owner. A hidden inner loan under the secondary
hook could therefore qualify the secondary connection if the primary hook
allows it.

The proposed `build_search_path_plan(type_name, model, paths)` signature also
lacks the owning type or definition needed to implement the exact-owner rule.
A type name is diagnostic text, not an identity-safe visibility target.

Required design change:

- Pass the exact owning `DjangoTypeDefinition` (or its `origin`) into the
  finalize-time plan builder.
- When a relation hop re-enters the plan's root model, record the exact owning
  type as that hop's visibility type.
- Use the registry primary only for other related models whose search path has
  no exact schema-owner identity.
- Keep the exact type reference in the frozen plan; do not rediscover it from
  the model at request time.

Required regression:

- Register primary and secondary types over `Loan` with deliberately divergent
  `get_queryset` hooks.
- Execute search through the secondary connection.
- Make an inner loan visible to the primary but hidden to the secondary.
- Prove that it cannot qualify a visible secondary root through
  `book__loans__patron__email`.

### P1-3 — The async search path must put permission gates on the sync worker

The spec says only related visibility differs between
`apply_search_sync` and `apply_search_async`, while permission dispatch remains
shared, un-awaited helper code. That is incompatible with the current gate
contract.

[`FilterSet.apply_async`][filtersets] routes permission checks, form
validation, custom filter bodies, and queryset evaluation through
[`run_in_one_sync_boundary`][querysets]. [`OrderSet.apply_async`][ordersets]
does the same for permission gates. This permits a synchronous consumer gate
to perform a blocking ORM read without blocking the event loop, while
[`invoke_permission_method`][permission-utils] still rejects an `async def`
gate loudly.

Calling the same synchronous gate runner directly from `apply_search_async`
would instead:

- raise Django's async-safety error when a gate performs an ORM read; or
- block the event loop for other synchronous I/O.

Required design change:

- Keep one synchronous, path-driven permission runner.
- `apply_search_sync` calls it directly.
- `apply_search_async` awaits
  `run_in_one_sync_boundary(permission_runner, ...)`, exactly as the existing
  filter and order surfaces do.
- Preserve the stated order: inactive check, length cap, permission denial,
  combined-queryset preflight, visibility derivation, compilation.

Required regression:

- Drive the real async connection pipeline with an active search and a
  synchronous gate that performs an ORM read.
- Prove the gate fires once, the request succeeds or denies with the gate's
  own error, and no async-safety error escapes.
- Retain the `async def check_<field>_permission` rejection test on both sync
  and async search surfaces.

### P1-4 — “Reuse the permission helpers” is not yet an implementable adapter

The current permission core is input-driven.
[`run_active_input_permission_checks`][permission-utils] requires a concrete
filter/order input and calls the family class's `_active_permission_targets`.
Search has no filter input to traverse. The private flat-path helper can fire a
target gate chain once an owning path has already been selected, but it does
not discover every declared filter whose `field_name` is a segment-prefix of a
search path. Calling `FilterSet._run_permission_checks` with fabricated input
would couple search authorization to input normalization and lookup coercion
and would still fail for search-only paths.

The spec also does not pin when permission applicability is resolved.
`RelatedFilter` targets, expanded flat leaves, bound owners, and hidden-flat
policy are not settled until [`_bind_filtersets`][finalizer] completes. A search
plan built before that subpass cannot safely freeze the gate chain described by
Decision 13.

Required design change:

- Add one named, path-driven helper in
  `django_strawberry_framework/utils/permissions.py`; do not synthesize a
  filter input.
- Build an immutable permission-dispatch plan from the fully bound and expanded
  FilterSet after `_bind_filtersets`.
- Assign the completed search plan only after both path classification and
  permission planning succeed, preserving finalize retry safety.
- For each search path, record the owning flat/source-path gates, every renamed
  `RelatedFilter` parent-branch gate, and each resolved child terminal gate.
- Invoke through the existing `invoke_permission_method` primitive and its
  per-class fired sets so aliases and repeated paths deduplicate exactly as the
  filter surface does.
- Match applicability from the final declared filter metadata, not GraphQL
  exposure. `HIDE_FLAT_FILTERS` must not remove a gate.
- A search path with no applicable filter remains authorized by the
  `Meta.search_fields` declaration, as Decision 13 requires.

Required regressions:

- several filter aliases sharing one `field_name`;
- a renamed `RelatedFilter` branch whose public attribute differs from its ORM
  `field_name`;
- a prefix-only relation gate;
- an expanded generated flat leaf hidden from the public filter input;
- a search-only path on a type that still has a FilterSet;
- repeated paths/aliases proving each `(FilterSet class, gate method)` fires at
  most once.

### P1-5 — `active_search` cannot introduce an eager filters-package import

Decision 3 and the DRY obligations place the sole `active_search` definition in
`filters/search.py` and require `utils/connections.py` to import it.
[`utils/connections.py`][connection-utils] is imported at package-root load
through [`connection.py`][connection], while importing a
`filters.search` submodule first executes `filters/__init__.py` and its full
filter subsystem imports.

That would violate an existing package invariant documented directly in
[`connection.py::_synthesized_signature`][connection]: bare
`import django_strawberry_framework` must not eagerly import the filters or
orders subpackages. The current function-local sidecar imports exist
specifically to preserve that contract, and
[`test_registry_clear_works_without_filters_imported`][filter-finalizer-test]
pins it in a subprocess.

Required design change:

- Put the canonical predicate in a cycle-safe neutral utility and re-export it
  from `filters/search.py`, or use an equivalently lazy design that does not
  import the filters package when search is absent.
- Do not make every call to the connection sidecar detector import the filter
  subsystem merely to classify `None`.
- Keep the planner and resolver on the same predicate object so whitespace-only
  search is inactive on both sides.

Required regressions:

- Bare package import still leaves `django_strawberry_framework.filters` and
  `django_strawberry_framework.orders` absent from `sys.modules`.
- Nested planner and resolver agree for omitted, empty, whitespace-only, literal
  active, and variable-provided active search values.

## Confirmed strengths

### The Part 1 compiler seam is now correct

The plan correctly intercepts
[`FilterSet.filter_queryset`][filtersets], the general django-filter leaf seam,
rather than only the package's custom lookup helper. It invokes the original
eligible filter against the correlated inner root, preserving django-filter
coercion, `exclude` behavior, multi-lookup decomposition, GlobalID handling,
and Django's own `split_exclude` semantics. It does not attempt to reimplement
those semantics with a scalar negation flag.

The provenance design is also appropriately fail-closed: only
framework-generated leaves proven safe by generation metadata are rewritten.
Declared filters, `filter_overrides`, consumer methods, custom subclasses, and
consumer-origin `distinct` retain their original behavior.

### The multiset and SQL-shape contracts answer the original failure

[`correlated_inner_root` and `attach_exists`][part1-plan] keep the membership
tables inside the subquery and preserve the incoming outer query. The required
Medtrics-shaped fixture tests the important topology that a direct M2M-only
fixture would miss: a forward to-one prefix followed by a reverse FK and then a
forward to-one terminal path.

The plan's required oracles are the right ones:

- ordered primary-key sequences and counts, not set equality;
- outer `alias_map` free of membership tables;
- no framework-added outer `DISTINCT`;
- no redundant inner `SELECT DISTINCT`;
- same-table inner aliasing when `Loan` re-enters `Loan`;
- exact page boundaries and `totalCount`.

These assertions distinguish the root-cause fix from JOIN-plus-`DISTINCT`,
post-query deduplication, and scalar aggregation.

### Search OR composition is compatible with row preservation

Attaching each correlated expression as an outer alias and applying one final
OR between direct predicates and positive `EXISTS` predicates preserves a root
that matches either branch and does not duplicate a root that matches both.
Grouping same-value paths with an identical full relation chain is a valid cost
optimization, provided Finding 1's same-related-row visibility invariant is
maintained. Separate existence branches remain the safe fallback.

### Connection and optimizer integration is otherwise well targeted

The spec correctly recognizes that `CONNECTION_SIDECAR_KWARGS` is currently
documentation rather than executable iteration. It explicitly widens
`connection_sidecar_inputs_from_kwargs`,
`has_connection_sidecar_input`, source guards, synthesized signatures, and
resolver pipelines.

Treating active nested search as an unwindowable sidecar is correct under the
current optimizer. The per-parent fallback may be expensive and strictness may
surface it, but it does not create a dead window or return unsearched rows.
Using the shared `active_search` predicate for both planner and resolver is
essential so whitespace-only input remains a true no-op.

The combined-queryset preflight, live-database alias binding, immutable
request-free frozen plan, text-terminal validation, raw literal handling, and
length cap are all appropriate implementation gates.

## Answer for the original Medtrics application

If the application used DSF, the proposed architecture can eliminate the
original `UserSchedule` JOIN/`DISTINCT` failure:

1. The connection's exact `DjangoType.get_queryset` narrows visible
   `UserSchedule` roots.
2. Direct search fields become outer `Q(...__icontains=value)` branches.
3. The group-membership path becomes one correlated `EXISTS` branch rooted on
   the same `UserSchedule` primary key.
4. Direct and relational branches are ORed once.
5. No search-created membership JOIN reaches the root query, so no
   search-driven `.distinct()` is needed.
6. Count and pagination operate on root rows.

That conclusion is conditional on Findings 1 and 2: visibility must constrain
the same related row that supplies the match, and a path that re-enters
`UserSchedule` must use the exact connection type's visibility hook rather than
silently switching to the registry primary.

### Static DSF scope versus DRF action-dependent scope

DSF as specified does **not** reproduce DRF
`SearchFilter.get_search_fields(view, request)`. One `DjangoType` has one frozen
search tuple, and every connection serving it exposes the same `search:`
capability.

The original Rotations-versus-Academic-Progress policy is representable, but
only as distinct GraphQL type definitions:

- a Rotations `UserSchedule` type declares the group-membership path; and
- an Academic Progress `UserSchedule` type omits it or declares a narrower
  tuple.

Each connection must serve its exact type. Reusing one type across both
connections does not meet the original policy and must be documented as such.
Because both types register over one model, one must be `Meta.primary = True`.
For Relay types with distinct GraphQL names, current
[`_check_filterset_owner_pk_identity`][finalizer] also means they generally
need separate FilterSet subclasses rather than sharing one bound FilterSet.
If the types need distinct node identity instead of secondary IDs decoding to
the primary, their GlobalID strategy must likewise be chosen explicitly; that
is an existing multi-type concern, not a search compiler defect.

This static split is a valid Meta-first DSF design, but it is not a transparent
port of a single DRF viewset whose action mutates search scope at request time.
The migration documentation should say that plainly.

## Implementation gates

Do not begin card 049 runtime wiring until all of the following are explicit in
the spec and tests:

1. One-filter-call or equivalent same-related-row semantics for hop visibility
   plus terminal matching.
2. Exact-owner visibility for root-model re-entry, including a secondary-type
   regression.
3. A sync-worker boundary for search permission gates on the async pipeline.
4. A named path-driven permission-plan helper built after FilterSet binding and
   expansion.
5. A cycle-safe owner for `active_search` that preserves lazy subpackage
   imports.

After those changes, the design has the necessary architecture and acceptance
oracles to fix the original issue without replacing it with a visibility leak,
an async-only failure, or a static-scope misunderstanding.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[part1-plan]: row-preserving-predicates-part1-plan.md
[spec-049]: spec-049-search_fields-0_1_2.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection]: ../django_strawberry_framework/connection.py
[connection-utils]: ../django_strawberry_framework/utils/connections.py
[filtersets]: ../django_strawberry_framework/filters/sets.py
[finalizer]: ../django_strawberry_framework/types/finalizer.py
[ordersets]: ../django_strawberry_framework/orders/sets.py
[permission-utils]: ../django_strawberry_framework/utils/permissions.py
[querysets]: ../django_strawberry_framework/utils/querysets.py

<!-- tests/ -->
[filter-finalizer-test]: ../tests/filters/test_finalizer.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[django-spanning-multivalued]: https://docs.djangoproject.com/en/6.0/topics/db/queries/#spanning-multi-valued-relationships
