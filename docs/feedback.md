# Follow-up review: multiplicity detection and the compatibility floor

## Verdict

The corrected understanding of Django's
`lookup_spawns_duplicates()` changes one Part 1 implementation detail and the
prior-art explanation shared by both parts. It does **not** invalidate the
row-preserving `EXISTS` architecture, the multiset contract, or the executable
Medtrics reproduction.

The implementation should distinguish two questions that the current design
already needs to answer:

- `relation_kind(field)` describes the semantic relation topology, such as a
  reverse FK, M2M, `GenericRelation`, or forward single-valued relation.
- Django's `PathInfo.m2m` flag describes whether the ORM traversal can multiply
  rows. Despite its historical name, this flag is true for an ordinary reverse
  FK as well as an M2M traversal.

This behavior is present at the package's minimum compatibility floor:
Python 3.10 with Django 5.2.0. Django 5.2.0's reverse-path construction sets
`PathInfo.m2m` to `not self.unique`, so the reverse side of an ordinary
non-unique `ForeignKey` is multiplying, while the reverse side of a unique
one-to-one relation is not. Django 5.2.0's admin helper consequently returns
`True` for the complete
`Loan.book -> Book.loans -> Loan.patron -> Patron.email` path.

## Finding 1 — Correct the prior-art statement in Part 1

The investigation-grounding paragraph in the [Part 1 plan][part1-plan]
currently says that Django admin's `lookup_spawns_duplicates()` detects M2M
only and misses reverse FK. That statement is false and must not remain in the
implementation-ready spec.

The misleading part is Django's own `m2m` terminology. The helper does not
test `field.many_to_many`; it walks `field.path_infos` and tests
`any(path_info.m2m for path_info in path_infos)`. A `ManyToOneRel` reached by a
reverse FK supplies a `PathInfo` whose `m2m` flag is true.

Recommended replacement:

> Django admin's `lookup_spawns_duplicates()` detects potentially multiplying
> reverse-FK and M2M traversals through `PathInfo.m2m`, but returns only a
> boolean. It neither exposes a reusable structured path plan nor compiles
> positive relational predicates into correlated `EXISTS` expressions.

The adjacent conclusion that no surveyed prior art supplies Part 1's positive,
row-preserving `EXISTS` rewrite can remain. Detection of possible fan-out is
not the same operation as preventing framework-owned fan-out while preserving
the incoming queryset's multiplicity.

## Finding 2 — Part 1 should use `PathInfo` as the SQL-multiplicity authority

Slice A should make the source of each hop's `many_side` bit explicit. The
classifier should use the resolved relation field for semantic kind and the
field's Django path information for ORM multiplicity and traversal target:

```python
# Pseudocode: one declared field segment may expand to multiple ORM PathInfo
# records, so collapse multiplicity at the declared-segment boundary.
field = current_opts.get_field(segment)
kind = relation_kind(field)
path_infos = tuple(field.path_infos)

if not path_infos:
    raise PathResolutionError.for_segment(root_model, field_path, segment)

many_side = any(path_info.m2m for path_info in path_infos)
target_opts = path_infos[-1].to_opts

hop = RelationPathHop(
    segment=segment,
    kind=kind,
    target_model=target_opts.model,
    many_side=many_side,
)

if many_side and first_many_index is None:
    first_many_index = len(hops)

hops.append(hop)
current_opts = target_opts
```

The production plan need not retain Django's `PathInfo` objects. It should
freeze only the package-owned values its consumers require: segment, relation
kind, target model, many-side bit, terminal descriptor, first-many index, and
relation-chain grouping key. This keeps the public/internal package plan small
and immutable while still deriving its SQL cardinality from the same metadata
used by Django's query traversal.

The existing `relation_kind()` logic in
`django_strawberry_framework/utils/relations.py::relation_kind` already
recognizes a reverse FK through `one_to_many=True` and
`auto_created=True`. This finding therefore refines the new classifier rather
than identifying a defect in the legacy helper. `relation_kind()` should remain
because `PathInfo.m2m` deliberately collapses reverse FK and M2M into one
boolean and cannot describe the topology needed by visibility, generic
relation, diagnostics, and test assertions.

Part 1 should **not** import or call
`django.contrib.admin.utils.lookup_spawns_duplicates` in production. The
helper is admin-owned, returns only a boolean, stops at the first multiplying
hop, and leniently ignores unresolved lookup/transform segments. Part 1 needs
strict model-path validation, the exact first boundary, the complete relation
chain, a terminal descriptor, and typed failures. Reimplementing those richer
semantics over Django model metadata is not duplication of the admin helper's
contract.

## Finding 3 — Keep the reverse-FK reproduction and independent M2M proof

The corrected Django behavior does not make the reverse-FK tests redundant.
The shared fixture must still prove that Part 1:

- identifies `Book.loans` as the first multiplying hop after the to-one
  `Loan.book` prefix;
- constructs the correlated predicate without an outer self-join;
- preserves mixed direct/relational OR semantics;
- returns the exact ordered ID sequence and correct `count()`;
- preserves the two-page connection boundary; and
- adds neither framework-owned outer fan-out nor framework-owned `DISTINCT`.

The direct/nested M2M fixture remains a separate structural category. A
boolean agreement with `lookup_spawns_duplicates()` cannot replace the exact
`first_many_index`, relation-kind, SQL-shape, and live cardinality assertions.
If the admin helper is used as a package-test differential oracle, it should be
an additional assertion over valid Django-native paths only; it must not become
the sole oracle or a production dependency.

## Finding 4 — Part 2 consumes the richer plan; its architecture does not change

The [Part 2 search specification][part2-spec] should continue to consume the
frozen Part 1 path plan created at type finalization. It should not call
`lookup_spawns_duplicates()` during request execution and should not replace
the plan with a `search_requires_distinct` boolean.

Part 2 still needs the structured plan because search must:

- separate direct predicates from row-multiplying relational predicates;
- group compatible relational arms without reconstructing paths;
- compose hop visibility and terminal matching with the required same-row
  semantics;
- attach correlated `EXISTS` branches under reserved aliases; and
- preserve the incoming queryset rather than normalizing it with
  `.distinct()`.

Any Part 2 rationale saying or implying that the Medtrics reverse FK is needed
because Django cannot detect reverse-FK fan-out should be replaced. The fixture
is needed because detecting possible fan-out is insufficient: the package must
compile the correct row-preserving query and prove its observable GraphQL
cardinality.

No change is required to the Part 2 phrase-boundary fixture, related-visibility
requirements, exact ordered IDs, `totalCount`, or pagination acceptance tests.
Those verify behaviors the Django admin helper does not provide.

## Finding 5 — Make Python 3.10 and Django 5.2.0 an exact acceptance floor

Both parts should name **Python 3.10 with Django 5.2.0**, not merely
`Django>=5.2` or the latest 5.2 patch, as the minimum compatibility job. A
dependency range normally resolves to the newest compatible release and does
not prove that code works on 5.2.0.

The implementation may rely on `field.path_infos`, `PathInfo.m2m`, and
`PathInfo.to_opts`: all are present with the required reverse-FK semantics in
Django 5.2.0. New code must not rely on APIs added by later Django 5.2 patch
releases, Django 6.0, or Python 3.11+, including convenience typing APIs unless
the project supplies an existing compatibility import.

Required compatibility evidence when implementation is tested:

1. Run the Part 1 classifier and predicate suites under Python 3.10 and an
   exact `Django==5.2.0` pin.
2. Run the Part 2 live Medtrics-shaped search reproduction under that same
   floor, so compatibility is proven through the real `/graphql/` path rather
   than import-only coverage.
3. Retain the current-version job as the other end of the supported range.

This compatibility requirement changes neither runtime caching nor lazy
evaluation. Classification remains a type-finalization operation, while
database aliases, routers, visibility querysets, and request values remain
resolve-time inputs as already specified.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[part1-plan]: row-preserving-predicates-part1-plan.md
[part2-spec]: spec-049-search_fields-0_1_2.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
