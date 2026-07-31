# Code review: commit `bbd216fc`

## [P1] Validate a lookup's direct RHS before calling its source accessor

`django_strawberry_framework/utils/querysets.py::_expr_graph_defect` now validates
four sequence-valued expression state slots before it calls
`node.get_source_expressions()`, which closes the `Case.cases` iterator gap.
That does not make the bound accessor generally safe. Django's exact
`Lookup.get_source_expressions()` first calls `rhs_is_direct_value()`, which
performs `hasattr(self.rhs, "as_sql")`. An arbitrary direct RHS can therefore
run its own attribute hook during the proof. When the RHS has no `as_sql`, the
accessor returns only `lhs`, so that RHS is never passed back through
`_expr_graph_defect` at all even though the database adapter will consume it
later.

This contradicts the boundary's promise that every lookup operand is validated
and gives consumer state a callback before the query is cloned. Validate an
exact Django lookup's raw `lhs` and `rhs` state directly, without calling a
bound discovery method first; a direct RHS must satisfy the inert-value rules,
while an expression RHS must recurse through the graph proof. Add a regression
using an exact Django lookup whose direct RHS has an attribute hook, and assert
that the hook is not invoked and the seal returns an `untrusted` defect.

## [P1] Rebuild the complete query graph instead of retaining candidate nodes

`django_strawberry_framework/utils/querysets.py::_rebuild_query_payloads`
detaches only the lists stored in `table_map`. The cloned query still shares
lookup leaves, annotation expressions, joins, `FilteredRelation` objects, and
raw-SQL parameter containers with the candidate. The function's own docstring
acknowledges that a retained lookup can have its `rhs` changed after sealing,
including the lookup that carries the visibility predicate. Consequently the
result is not a detached execution query: code retaining a reference to the
candidate graph can still change which rows the sealed queryset selects before
compilation.

The root fix is the canonical reconstruction already identified by spec-045:
derive a validated, inert description of the query and rebuild fresh
framework-owned AST nodes and payload containers from it. Extending the
one-container copy does not close the ownership boundary. Add a regression that
seals a visibility-filtered queryset, mutates a retained candidate leaf and a
raw parameter container, and proves the sealed SQL and parameters remain
unchanged.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
