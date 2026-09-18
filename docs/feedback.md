# Adversarial review: spec-050 current tree

Date: 2026-09-18

Verdict: **not ready to close.** The recent expression whitelist work fixed the
generic `Func`/`Transform` recursion problem, but the exact-type boundary is not
propagated to the two reference forms that can still carry arbitrary compiler
behavior. Both bypasses are reachable from an ordinary Django model declaration
and a normal positive-offset GraphQL request. Independently, the checkout is still
the WIP/pre-candidate tree described by the build record, so it cannot yet provide
release evidence.

I reviewed the current `HEAD` (`ccf46e11`), the complete spec, the build record, the
classifier and its package/live tests. I also ran fresh Django probes against the
current code. I did not run pytest, per the repository rule. The non-pytest
governance checks currently pass: glossary consistency (43 terms), citations (1,121
resolved), generated tree freshness, and tracked-path constants.

## P1-1 — `F` and `Q` subclasses bypass the exact approved-node boundary

**Broken contract.** Spec-050 Decision 6 defines positive certification as an
explicit whitelist of exact approved forms and says that *any subclass of an
approved class is refused*. The same rule appears in the Decision 6 edge cases,
the Slice 2 acceptance rule, Test plan row 27, and the build inventory. A model
default that is certified as stable must therefore not emit SQL whose ordering
semantics this package cannot inspect.

**Supported project shape and wire input.** Django applications may declare custom
expression subclasses in ordinary model Python and place them in `Meta.ordering`.
No private queryset mutation, forged GraphQL value, or unsupported transport is
needed. A client then sends the normal list-field request:

```graphql
{ shelves(offset: 1, limit: 1) { code } }
```

### Reproduction A: an `F` subclass

```python
class VolatileF(models.F):
    def resolve_expression(
        self, query=None, allow_joins=True, reuse=None,
        summarize=False, for_save=False,
    ):
        return Random()

class ProbeShelf(models.Model):
    code = models.CharField(max_length=100)

    class Meta:
        app_label = "probe050"
        managed = False
        db_table = "library_shelf"
        ordering = (VolatileF("code"),)
```

The public model declaration reached a real `DjangoListField`/`DjangoSchema`
request. The classifier returned `True`, the response was successful, and the
captured row query contained:

```sql
ORDER BY RAND() ASC LIMIT 1 OFFSET 1
```

The implementation takes this path in
`django_strawberry_framework/list_field.py::_is_deterministic_order_term`: the
`isinstance(term, models.F)` branch trusts the name and never asks what the
subclass's `resolve_expression` returns.

### Reproduction B: a `Q` subclass inside a conditional ordering

```python
class VolatileQ(models.Q):
    def resolve_expression(self, query, *args, **kwargs):
        return Random()

ordering = (
    models.Case(
        models.When(VolatileQ(code__gt="x"), then=models.Value(0)),
        default=models.Value(1),
    ),
)
```

The current classifier again returned `True`, while Django compiled the selected
ordering as:

```sql
ORDER BY CASE WHEN RAND() THEN 0 ELSE 1 END ASC
```

The `isinstance(term, models.Q)` branch has the same flaw. This is a second spelling
of the same contract breach, not a hypothetical extension of the first example:
`Q` is a public Django predicate class and `Case`/`When` is an approved transparent
composition in the spec.

### Root cause and required fix

The whitelist is exact for the expression sets, but the two early reference arms
still use subclass admission. Replace those arms with exact-type checks (or an
equivalent identity check) so only `type(term) is models.F` and `type(term) is
models.Q` enter the reference/predicate logic. A subclass must fall through to the
unapproved-node refusal before any consumer override can run. Do not add deny-list
names for `Random`, and do not rely on inspecting a subclass's method or source
expressions: the contract is exact approved identity.

Add the missing evidence in the same change:

- package classifier cases for exact `models.F`/`models.Q` acceptance and custom
  subclasses' refusal;
- synchronous and asynchronous live `/graphql` rows for both model-default shapes,
  each asserting `order_required` and zero row SQL, beside stable controls;
- a conditional-order row proving the `Q` subclass is rejected through the predicate
  path, including the normal `Case`/`When` composition;
- Decision 6, its edge cases, Test plan row 27, the Slice 2 checklist, and the build
  inventory updated to name this exact boundary.

Until this is fixed, a positive offset can silently page a random result while the
package claims that the selected order is repeatable. That is a release-blocking
implementation defect under the spec's own trust-boundary rule.

## P1-2 — The checkout still cannot establish a releasable exact tree

This is independent of the classifier defect.

- `docs/builder/DONE/build-050-list_field_arguments-0_0_15.md` still declares
  `Status: WIP`.
- Slice 5 and the final exact-commit gate remain unchecked; the final gate section
  explicitly says no current default, sharded, supported-floor, structural, or
  adversarial-review result is evidence for this checkout.
- The spec remains `WIP — pre-candidate` with its completion protocol still open.
- The working tree contains unrelated concurrent modifications, including the
  tracked SQLite database. Because the database is one binary shared by multiple
  owners, it cannot be treated as a clean card-050 candidate input merely by
  staging the file.

The required disposition is the protocol already specified in Decision 22: make one
candidate implementation commit after reconciling concurrent database work and
regenerating derived outputs; run the default, sharded, supported-floor, structural,
documentation, citation, link, migration, and adversarial gates against that exact
parent; then make an evidence-only follow-up that names the gated parent. Do not
mark the card DONE from this working tree or carry results from an earlier hash.

## P2-1 — Historical build measurements need to be refreshed at candidate time

The build record labels its pre-flight counts as historical, but the recorded spec
sizes (147,842 bytes/2,056 lines before and 141,617 bytes/1,979 lines after) do not
describe the current spec (247,637 bytes/3,260 lines). This is not a runtime defect,
and it is not evidence that the specification is wrong; it is an evidence-integrity
hazard if those figures are read as measurements of the candidate.

At the candidate step, replace the stale measurements with counts from the exact
candidate parent, state which generated/documentation checks were run on that tree,
and keep the evidence-only follow-up limited to the gated parent it names.

## What this pass confirms

- The generic “any readable children means deterministic” bug is no longer present:
  unknown `Func`/`Transform`/`Window`/aggregate forms and subclasses of approved
  functions are rejected by the named-node whitelist.
- Relation-string expansion follows Django's related-model defaults, while ordinary
  expression references do not accidentally expand relations.
- Conditional predicates inspect both the reference and value sides, including
  annotation aliases and approved transform/lookup chains.
- The runner-owned operation state, authority construction, lease cleanup, refusal
  chain, row-source sealing, evaluated-queryset handling, and manager/proxy coverage
  remain aligned with the current spec on code inspection.
- The four non-pytest governance checks listed at the top of this review pass. No
  full-suite, sharded, or supported-floor result is claimed here.

## Required disposition

1. Close the exact-type `F`/`Q` subclass bypass in the production classifier.
2. Add the package and live sync/async regressions and update the corresponding spec
   and build rows.
3. Reconcile the concurrent SQLite/working-tree state and create the exact candidate
   implementation commit.
4. Run every declared gate on that candidate, perform one final adversarial review of
   that exact tree, and only then write the evidence-only closure record.
