# Adversarial review: spec-050 current candidate

Date: 2026-09-18

Verdict: **the isolation, relation-expansion, predicate-LHS, evaluated-queryset, and
manager fixes are materially better, but this candidate still has one wire-reachable
ordering-certification bypass and is not closeable yet.** The bypass is in the same
Decision 6 contract, not a theoretical hostile-object concern. The build record also
still correctly says WIP: the exact-tree gate has not been run and the checkout carries
an uncommitted database change.

I reviewed the current `HEAD` (`02e266df`) and the current working tree. I did not run
pytest, per the repository rule. I did run direct Django/HTTP probes in fresh Python
processes, plus the structural tracked-path and tree checks that do not execute pytest.

## P1-1 — Generic expression recursion certifies custom SQL as deterministic

**Broken contract:** spec-050 Decision 6 says a positive offset is allowed only when
the selected order can be read down to columns and literals. It explicitly says that
`Func`, `RawSQL`, `Subquery`, and other SQL the classifier cannot read must be refused,
and Test plan row 27 requires the refusal to be observable before row SQL. The same
contract applies to a model default selected after visibility; it is not limited to
`OrderSet.apply_*` output.

**Supported project shape:** Django's public expression API permits a project to put a
custom `Func` or `Transform` in `Meta.ordering`. This does not require a private Django
write, a forged queryset, or a malicious GraphQL scalar. The application owns the model
and registers the expression in ordinary Python.

**Wire input:** a normal `DjangoListField` request with a positive `offset` and a
`limit`, for example `{ shelves(offset: 1, limit: 1) { code } }`. The resolver can be
the ordinary `Shelf.objects.all()` resolver used by the fakeshop holder probes.

### Reproduction A: a custom `Func` with a readable child

```python
class Volatile(Func):
    function = "RANDOM"

    def as_sql(self, compiler, connection, **kwargs):
        return "RANDOM()", []

Shelf._meta.ordering = (Volatile(F("code")),)
```

The current `_is_deterministic_order_term` sees a non-empty
`get_source_expressions()` result, recursively certifies the child `F("code")`, and
returns `True`. It never certifies the SQL emitted by `Volatile`. The direct helper
reported `True`; the synchronous HTTP request was served with:

```sql
ORDER BY RANDOM() ASC LIMIT 1 OFFSET 1
```

The asynchronous HTTP request was also served successfully with the same random
ordering. The guard did not return `order_required`, and row SQL was executed.

### Reproduction B: a custom `Transform` hidden in a conditional predicate

```python
class Jitter(Transform):
    lookup_name = "jitter"
    output_field = models.FloatField()

    def as_sql(self, compiler, connection):
        return "RANDOM()", []

models.TextField.register_lookup(Jitter)
Shelf._meta.ordering = (
    Case(When(code__jitter__gt=0.5, then=Value(0)), default=Value(1)),
)
```

The current `_is_deterministic_order_predicate_reference` finds `code` as a valid
field head and accepts the remaining transform/lookup suffix without classifying the
transform. The helper again reported `True`; the live SQL was:

```sql
ORDER BY CASE WHEN RANDOM() > 0.5 THEN 0 ELSE 1 END ASC
             LIMIT 1 OFFSET 1
```

This is the same failure mode as the earlier random-alias predicate defect, but it is
now past the alias check: the unreadable SQL is supplied by a standard Django
transform rather than by an annotation alias.

### Root cause

The generic branch in `django_strawberry_framework/list_field.py::_is_deterministic_order_term`
uses “has source expressions” as a proxy for “transparent composition.” That is not a
Django contract. `Func`, `Transform`, `Aggregate`, `Window`, and consumer expression
subclasses can all have readable children while their own compiler method contributes
arbitrary SQL. The predicate reader has the same gap: it separates a field/annotation
head from trailing pieces but does not establish that each trailing transform is a
known, deterministic operation.

This is not an application-code trust-boundary exception. The project is trusted to
declare a model default, but the list-field contract still promises not to certify an
order it cannot read. A page that spans two executions under `RANDOM()` is a concrete
violation of that promise.

### Required root fix

1. Replace the generic source-expression recursion with an explicit classifier for the
   expression forms the package has decided are transparent. Unknown expression nodes,
   custom `Func`/`Transform`/`Aggregate`/`Window` subclasses, and any node whose own
   compiler contributes SQL must fail closed. Do not fix this by adding another
   `Random` class name to a deny-list.
2. Keep the existing positive handling for the deliberately supported forms (`F`,
   `OrderBy`, `Case`/`When`, readable leaves, and the relation-string expansion), but
   make the exact/approved node boundary explicit. If a built-in function such as a
   deterministic `Lower` or `Cast` is to remain accepted, name and test it as an
   approved form; otherwise reject it as opaque. The rule must not depend on the
   function's runtime name or on whether its children happen to be readable.
3. In `_is_deterministic_order_predicate_reference`, distinguish a field/annotation
   reference from its trailing lookups and transforms. A transform suffix is not a
   certified column reference unless it is one of the explicitly approved forms. The
   same rule must hold when the head is an annotation, and when a reference is lifted
   through a related-model ordering prefix.
4. Add both sync and async live `/graphql` rows in
   `examples/fakeshop/test_query/test_list_field_api.py` and
   `examples/fakeshop/test_query/test_list_field_async_api.py` for the two reproductions:
   each must return `order_required`, execute no model-row SQL, and sit beside a
   deterministic control. Add package-level classifier tests for the exact expression
   boundary and for an approved deterministic form if one is retained.
5. Amend Decision 6, its edge-case bullets, rationale, Test plan row 27, the Slice 2
   checklist, and the build record so the documented positive-certification rule names
   custom functions/transforms and the chosen whitelist. Do not leave the prose saying
   “every other leaf is opaque” while the implementation treats every non-empty source
   list as transparent.

Until this is fixed, the offset guard can serve a random page while claiming that the
order is materially active and repeatable. That is a release-blocking implementation
finding.

## P1-2 — The close record still cannot identify a releasable tree

This is a release-integrity blocker independent of the runtime finding.

- `docs/builder/DONE/build-050-list_field_arguments-0_0_15.md` still says `Status: WIP`.
- Slice 5 and the final exact-commit gate are unchecked, and the final gate section says
  that no current default, sharded, supported-floor, structural, or adversarial-review
  result is evidence for this checkout.
- The spec itself remains explicitly `WIP — pre-candidate` with unchecked completion
  rows. That is currently the truthful state, not a close.
- `git status --short` still reports an uncommitted `examples/fakeshop/db.sqlite3`
  change. The build record documents that this SQLite file contains concurrent library
  data as well as card-owned lifecycle data; it cannot safely be absorbed into a
  candidate by staging the binary as one file.

The required fix remains the two-commit protocol already written in Decision 22:
create one candidate implementation commit, run the complete default/sharded/floor and
structural/documentation gates against that exact parent, perform the final adversarial
review, then make an evidence-only follow-up that names the gated parent. Disentangle
the SQLite data before the candidate commit and regenerate its derived outputs. Do not
mark the card DONE from the current working tree or from figures produced on an earlier
hash.

## P2-1 — The build inventory does not describe the latest in-scope fixture changes

The latest in-scope library test commit (`02e266df`) adds and modifies the proxy-targeted
prefetch fixture: a new `BranchNote` model and migration, schema surfaces, app-model
tests, live library tests, and both SQLite databases. The build text still contains the
sentence that `test_resource_policy_api.py` is the predicted addition and that “no new
tracked path is added.” That sentence is no longer true for the current candidate.

The generated tree and tracked-path checker are currently green, but those checks do not
make the build record's inventory accurate. A future close reviewer cannot tell whether
`examples/fakeshop/apps/library/migrations/0005_branchnote.py` and the proxy fixture are
intentional spec-050 evidence or unrelated concurrent work.

Update the build's predicted-file/cohort and floor-scope sections to name every fixture
path actually carried by the candidate, explain that the proxy fixture is the live proof
for the prefetch-seal row, and remove the “no new tracked path” assertion. Then rerun
the tracked-path, tree, citation, and documentation checks on the candidate commit.

## What is now fixed and not reopened

- Per-operation state is runner-owned and token/lease scoped across sync, async, nested,
  and streamed execution; the previous shared-instance overlap bypass is not reproduced
  by the current architecture.
- Enforcement authorities are schema-owned; direct declarations are folded into the
  construction record, while mutable factories and authority subclasses fail closed.
- Relation-name ordering now follows Django's recursive related-model default expansion,
  while `F` references remain foreign-key column references.
- Conditional ordering predicates classify both the lookup reference and its value, so
  random annotation aliases in either `alias()` or `annotate()` are rejected.
- Evaluated exact querysets, project `as_manager()` relations, pending reverse predicates,
  and proxy/concrete prefetch targets now have the intended live/package coverage.
- The current static tree check and tracked-path check pass. No pytest result is claimed
  here.

## Required disposition

1. Fix the expression/transform classifier at the production abstraction and add the
   sync/async live regressions and package controls.
2. Reconcile the build inventory with the proxy fixture and current tracked paths.
3. Resolve the concurrent SQLite state and create the exact candidate commit.
4. Run the declared default, sharded, supported-floor, structural, link, citation,
   migration, and documentation gates on that candidate.
5. Re-review that exact tree; only an evidence-only follow-up may then record closure.
