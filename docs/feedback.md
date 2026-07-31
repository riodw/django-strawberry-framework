# Code review: spec-045 visibility boundary

## [P1] Validate expression-owned state before calling `get_source_expressions`

`django_strawberry_framework/utils/querysets.py::_expr_graph_defect` proves an
expression's type and method shadows, then calls the bound
`node.get_source_expressions()`. That call is not necessarily dispatch-free.
For example, Django's exact `Case.get_source_expressions()` expands
`[*self.cases, self.default]`; if `cases` has been replaced with a list
subclass, its iterator runs during the proof. The outer query's `where` tree
has already been accepted at that point, so the iterator can modify it before
`sql.Query.clone()` runs. The seal then reports no defect and clones the
modified query, losing the visibility predicate.

The root fix is to validate and canonicalize every expression-owned state slot
that a genuine Django accessor reads before invoking that accessor. A
per-expression inventory is still version-sensitive, so the stronger fix is
the canonical reconstruction identified in spec-045: rebuild a trusted
expression/query representation without calling methods on the candidate
graph. Add a regression with an exact Django `Case` whose internal `cases`
container is non-exact and assert that sealing fails before its iterator runs.

## [P1] Validate the payloads of retained `Query` containers

`django_strawberry_framework/utils/querysets.py::_query_container_defect`
requires containers such as `alias_refcount`, `table_map`, and
`external_aliases` to be exact builtins, but it validates only their keys.
Their values survive the shallow copies in `sql.Query.clone()`. A consumer
`int` subclass stored as an `alias_refcount` value is therefore accepted and
retained; ordinary downstream `.filter()` composition invokes its arithmetic
from Django's alias bookkeeping. That callback can modify the cloned query's
`where` tree before the new filter is added, leaving only the downstream
predicate and dropping the visibility predicate.

Validate every retained container's complete Django shape before cloning, not
only its container type and keys. At minimum, alias refcounts must be exact
integers, table-map entries exact lists of exact alias strings, and the other
maps/sets must enforce their corresponding exact value types. Rebuild those
payloads into fresh trusted containers rather than shallow-copying candidate
objects. Pin the fix with a normal `.filter()` composition regression proving
the original visibility predicate survives.

## [P2] Reject cycles instead of treating them as validated shared nodes

`django_strawberry_framework/utils/querysets.py::_expr_graph_defect` and
`django_strawberry_framework/utils/querysets.py::_deferred_value_defect` use one
`seen` set for both completed shared nodes and nodes currently being visited.
Revisiting either kind returns success. Consequently a self-referential list,
dict, `Q`, or expression graph is accepted as trusted even though Django does
not produce cyclic query graphs and later cloning/compilation can recurse until
a raw `RecursionError`.

Use separate `visiting` and `validated` identity sets (or an equivalent
three-state walk): a node reached while still active is an `untrusted` cycle,
while a node reached after complete validation is a legitimate shared diamond.
Update
`tests/utils/test_querysets.py::test_expr_graph_walk_terminates_on_self_referential_containers`
and
`tests/utils/test_querysets.py::test_deferred_value_walk_terminates_on_self_referential_values`
to require a typed defect rather than `None`.

## [P2] Require an actual Django model class in `_concrete_or_none`

`django_strawberry_framework/utils/querysets.py::_concrete_or_none` says it
returns a concrete model only when its input is a model, but the implementation
duck-types any object exposing `_meta.concrete_model`. Such an object passes the
public `QuerySet.model` check and is then installed as `sealed.model`, even when
the SQL-bearing `Query.model` is the real registered model. Downstream code
widely treats `queryset.model` as a model class, so the malformed state escapes
the typed boundary and can fail later through missing class attributes or
consumer-defined attribute access.

Require `candidate` to be a Django model class before reading its metadata, and
return `None` otherwise. Add coverage for an object and a non-model class that
both expose a convincing `_meta.concrete_model`; both should produce the
existing typed `table` defect and no consumer attribute hook should run.

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
