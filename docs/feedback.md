# Adversarial Implementation Review: Spec-050 (`list_field_arguments-0_0_15`) Post-Remediation

**Target Spec:** [docs/spec-050-list_field_arguments-0_0_15.md][spec-050]  
**Target Plan & Build Record:**
[docs/builder/DONE/build-050-list_field_arguments-0_0_15.md][build-050]  
**Remediation Commit Evaluated:**
`5873f5ce` (*fix(spec-050): classify an ordering term by what the compiler resolves it into*)  
**Governance:** [AGENTS.md][agents] & [GOAL.md][goal]

---

## 1. Executive Summary & Status of Prior Findings

Commit `5873f5ce` significantly hardened the `DjangoListField` implementation against compiler
indirection. The maintainer thoroughly addressed five of the six areas flagged in the previous
review round:

| Finding ID | Title & Summary | Status Post-`5873f5ce` | Verdict |
|---|---|---|---|
| **Prior P1-1** | Opaque `extra(order_by=...)` terms bypassing determinism guard | Remediated via `_is_nondeterministic_order_name` and `_is_nondeterministic_order_term` inspecting compiler resolution targets. | **Resolved** |
| **Prior P2-1** | Dead `alias` defect branch in `_validate_post_orderset_result` | Remediated. Documented why `expected_routing` check in `_seal_or_defect` catches routing changes first, with fail-closed defense via `_defect_message`. | **Resolved** |
| **Prior P2-2** | `require_unevaluated=False` on `_LIST_ARGUMENT_VISIBILITY_POLICY` | Remediated. Spec and docstrings clarify the architectural boundary between consumer `get_queryset` results and internal post-apply `OrderSet` seals. | **Resolved** |
| **Prior P2-3** | Normalization purity check scoped to positive offset | Remediated. Spec Decision 6 and `_order_normalization_scope` formally state the single- vs double-invocation invariants. | **Resolved** |
| **Prior P3-1** | Build record floor verification count discrepancy | Remediated. Build record explicitly documents that the 4-path floor run was a focused seam check, with full 17-path verification owed at delivery HEAD. | **Resolved** |
| **Prior P3-2** | Async generator sync wrapper returning unawaited coroutines | Remediated. Documented `DjangoListField` reliance on graphql-core's async executor awaiting coroutines returned by sync resolvers. | **Resolved** |

However, our adversarial deep-audit of the newly introduced term-determinism classifier in
`django_strawberry_framework/list_field.py::`[`_is_nondeterministic_order_term`][list-field]
uncovered a **critical bypass vulnerability**: raw SQL expressions instantiated as
`django.db.models.expressions.RawSQL` completely evade detection and are certified as deterministic
by the non-zero offset guard.

---

## 2. Critical Vulnerability: P1-1 (Soundness & Specification Violation)

### P1-1: Direct, Annotated, and Composed `RawSQL` Ordering Terms Bypass the Determinism Classifier and Execute Non-Deterministic SQL Across Offset Windows

#### 1. Specification & Invariant Violation
[docs/spec-050-list_field_arguments-0_0_15.md][spec-050] lines 1580-1582 explicitly mandate:
> *"A term resolving into `query.extra` - a select alias, or the dotted form handed through as
> `RawSQL` - is opaque rather than deterministic and cannot back an offset window. An `extra`
> ordering naming a real field is unaffected."*

And [django_strawberry_framework/list_field.py::`_is_nondeterministic_order_name`][list-field] states:
> *"Raw SQL reached through `extra` is opaque, which is not the same as deterministic. Those
> strings are passed through verbatim and this package parses no SQL, so it cannot say what such
> a term orders by - and a term it cannot read is one it must not certify as repeatable across the
> two queries an offset window spans."*

The declared architectural invariant is unambiguous: **raw SQL cannot be parsed by the package, is
opaque, and must never be certified as deterministic across an offset window.**

#### 2. Root Cause Mechanism
In `django_strawberry_framework/list_field.py`, `_is_nondeterministic_order_term` is implemented as:
```python
def _is_nondeterministic_order_term(query: Any, term: Any) -> bool:
    if isinstance(term, str):
        return _is_nondeterministic_order_name(query, term)
    if isinstance(term, models.F):
        return _is_nondeterministic_order_name(query, term.name)
    if isinstance(term, Random):
        return True
    sources = getattr(term, "get_source_expressions", None)
    if sources is None:
        return False
    return any(_is_nondeterministic_order_term(query, source) for source in sources())
```

In
[tests/test_list_field.py::`test_order_term_classifier_resolves_indirection_and_opaque_sql`][test-list-field],
line 4038 asserts:
```python
# A term with no source expressions to walk has nowhere to hide one.
assert _is_nondeterministic_order_term(random_alias.query, 42) is False
```
This assumption ("a term with no source expressions to walk has nowhere to hide one") is **fatally
violated by `django.db.models.expressions.RawSQL`**.

`RawSQL` inherits from `Expression`. Django defines its `get_source_expressions()` method as:
```python
def get_source_expressions(self):
    return []
```
Because `isinstance(term, RawSQL)` is not checked:
1. `isinstance(term, str)` evaluates to `False`.
2. `isinstance(term, models.F)` evaluates to `False`.
3. `isinstance(term, Random)` evaluates to `False`.
4. `sources = getattr(term, "get_source_expressions", None)` resolves to
   `RawSQL.get_source_expressions`.
5. `sources()` returns the empty list `[]`.
6. `any(...)` over an empty sequence evaluates to `False`.
7. `_is_nondeterministic_order_term(query, RawSQL(...))` returns `False` (claiming the term is
   deterministic)!
8. Consequently, `_has_deterministic_ordering(queryset)` returns `True`!

#### 3. Empirical Verification: Live HTTP Exploit
We confirmed this vulnerability end-to-end against the live GraphQL endpoint (`/graphql/`) in the
`fakeshop` example project.

When an `OrderSet.apply_sync` method introduces a `RawSQL` ordering:
```python
def _rawsql_ordering(cls, order_input, queryset, info):
    return queryset.order_by(RawSQL("RANDOM()", []))

BranchOrder.apply_sync = classmethod(_rawsql_ordering)
```
And a client issues an offset query with active order arguments:
```graphql
query {
  allLibraryBranchesViaListField(orderBy: [{ city: ASC }], offset: 1, limit: 1) {
    name
  }
}
```
**Actual Result:**
- HTTP 200 OK.
- Response payload: `{"data": {"allLibraryBranchesViaListField": [{"name": "Bravo"}]}}`.
- Errors: `None`.
- The database executed: `SELECT ... FROM "library_branch" ORDER BY RANDOM() LIMIT 1 OFFSET 1`.

The non-zero offset guard (`_check_nonzero_offset_guard`) was completely bypassed. The exact same
vulnerability allows all of the following shapes to be certified as deterministic:
1. `queryset.order_by(RawSQL("RAND()", []))`
2. `queryset.order_by(RawSQL("RANDOM()", []))`
3. `queryset.order_by(RawSQL("NEWID()", []))`
4. `queryset.order_by(OrderBy(RawSQL("RAND()", [])))`
5. `queryset.annotate(rnd=RawSQL("RAND()", [])).order_by("rnd")`
6. `queryset.annotate(rnd=RawSQL("RAND()", [])).order_by(models.F("rnd"))`
7. `queryset.order_by(Coalesce(RawSQL("RAND()", []), Value(0)))`
8. `class Meta: ordering = [RawSQL("RAND()", [])]` on a model's default ordering.

#### 4. Required Root-Cause Remediation
In accordance with [AGENTS.md][agents] ("Always give the root-cause fix even when slower; never
offer defer-the-real-fix sequencing"),
`django_strawberry_framework/list_field.py::`[`_is_nondeterministic_order_term`][list-field]
must explicitly classify `RawSQL` alongside `Random`:

```python
from django.db.models.expressions import RawSQL

def _is_nondeterministic_order_term(query: Any, term: Any) -> bool:
    if isinstance(term, str):
        return _is_nondeterministic_order_name(query, term)
    if isinstance(term, models.F):
        return _is_nondeterministic_order_name(query, term.name)
    if isinstance(term, (Random, RawSQL)):
        return True
    sources = getattr(term, "get_source_expressions", None)
    if sources is None:
        return False
    return any(_is_nondeterministic_order_term(query, source) for source in sources())
```

When `RawSQL` is classified as non-deterministic/opaque:
- Direct `order_by(RawSQL(...))` returns `True` for `_is_nondeterministic_order_term`.
- Wrapped `order_by(OrderBy(RawSQL(...)))` recurses into `RawSQL` and returns `True`.
- Annotated `annotate(rnd=RawSQL(...)).order_by("rnd")` resolves `query.annotations["rnd"]` to
  `RawSQL` and returns `True`.
- `models.F("rnd")` referencing an annotated `RawSQL` recurses to `RawSQL` and returns `True`.
- Model `Meta.ordering = [RawSQL(...)]` returns `True`.
- Real database columns and deterministic Django expressions (`Lower`, `Coalesce` over columns)
  remain unaffected and evaluate to `False`.

Acceptance tests must be added to [tests/test_list_field.py][test-list-field] and
[examples/fakeshop/test_query/test_list_field_api.py][test-list-field-api] covering both sync and
async execution paths.

---

## 3. Medium & Architectural Findings

### P2-1: Asymmetry Between Dotted Legacy `extra` SQL and First-Class `RawSQL`
Commit `5873f5ce` classified dotted `extra_order_by` terms (such as
`Category.objects.extra(order_by=["products_category.name"])`) as opaque because
`"products_category.name"` is raw SQL passed through verbatim without parsing.
However, because `RawSQL` was omitted from `_is_nondeterministic_order_term`, a consumer using modern
`RawSQL` syntax (`Category.objects.order_by(RawSQL("products_category.name", []))`) was accepted as
deterministic.
Remediating P1-1 by treating `RawSQL` as opaque restores syntactic symmetry across both legacy
`extra` and modern `RawSQL` expressions.

### P2-2: Subquery Boundaries Stop Expression Walking
When an ordering term is an instance of `django.db.models.expressions.Subquery`:
```python
sub = Subquery(Item.objects.annotate(r=Random()).values("r")[:1])
qs = Item.objects.order_by(sub)
```
`Subquery.get_source_expressions()` returns a list containing a
`django.db.models.sql.query.Query` instance (`[query]`).
Because a `Query` object does not implement `get_source_expressions`,
`_is_nondeterministic_order_term` halts traversal and returns `False` (claiming deterministic
ordering).
While correlated subqueries in `order_by` are rare and usually represent deterministic scalar
lookups, this demonstrates that expression tree recursion terminates whenever it encounters an
inner SQL query encapsulation boundary.

---

## 4. Specification & Verification Governance Matrix

| Check / Gate | Target Requirement | Evaluation & Status |
|---|---|---|
| **Root-Cause Fix Standard** | No deferrals or workarounds; fix the abstraction ([AGENTS.md][agents]) | P1-1 fix directly addresses `RawSQL` expression tree classification in `_is_nondeterministic_order_term`. |
| **Fail-Closed Sealing** | Sealing boundaries fail closed on unhandled defect codes | Verified in `_defect_message` and `_validate_post_orderset_result`. |
| **No Unsolicited Pytest** | `uv run pytest` executed only upon explicit user request | Compliant. Zero unauthorized pytest runs performed. |
| **Test Placement** | Package tests in `tests/`, live HTTP tests in `examples/fakeshop/test_query/` | Compliant. Live HTTP proof demonstrated in `test_query` harness. |
| **Citation Resolution** | All symbol citations must resolve via `scripts/check_citations.py` | Compliant. 1023 citations resolve cleanly. |

---

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[goal]: ../GOAL.md

<!-- docs/ -->
[spec-050]: spec-050-list_field_arguments-0_0_15.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[build-050]: builder/DONE/build-050-list_field_arguments-0_0_15.md

<!-- django_strawberry_framework/ -->
[list-field]: ../django_strawberry_framework/list_field.py
[utils-querysets]: ../django_strawberry_framework/utils/querysets.py

<!-- tests/ -->
[test-list-field]: ../tests/test_list_field.py

<!-- examples/ -->
[test-list-field-api]: ../examples/fakeshop/test_query/test_list_field_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
