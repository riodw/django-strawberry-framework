# Adversarial review: spec-050 candidate

Date: 2026-09-21

Reviewed the current tree at `357e5487` against
`docs/spec-050-list_field_arguments-0_0_15.md`, its rationale, the builder record,
`GOAL.md`, `START.md`, and `AGENTS.md`. The current tree includes the policy-authority
fix (`9350eb8d`), the connection `OrderSet` seal (`fee87ac4`), and the sliced plain-relation
fix (`44712901`). The working tree has two unrelated concurrent spec-034 documentation
edits; they were not changed.

Verdict: the implementation is materially safer than the previously reviewed candidate, and
the two previously reported policy defects are fixed. It is still not ready to mark DONE: the
exact-tree release gate has not run, and the current spec/build records disagree with the
latest implementation. One lower-severity live-test gap remains for the new connection async
seal.

## Verified fixes

- `utils/policies.py::resolve_policy` now canonicalizes the no-override path. Mutating the
  exported `DEFAULT_RESOURCE_POLICY` or `DEFAULT_ERROR_POLICY` no longer changes a newly built
  schema or the package fallback.
- `error_policy.py::ErrorPolicy.__post_init__` rejects `str` subclasses for both string options,
  so a consumer dunder cannot run while a masked error is rendered.
- `connection.py::_pipeline_sync` and `::_pipeline_async` route the order sidecar through the
  shared `utils/querysets.py::apply_orderset_sync` / `::apply_orderset_async` seal. The result is
  checked for model, laziness, slicing, projection, combinations, and routing before Relay
  windowing.
- `optimizer/walker.py::_build_child_queryset` now uses the strict plain-list child policy, while
  `::_build_connection_child_queryset` retains the sliced-child licence only for the planner
  path that classifies and degrades it. This closes the raw Django sliced-refilter error on the
  plain relation path without removing the nested-connection fallback.

## P1 — the exact-tree release gate is still open

### Broken contract

Spec Decision 22 and the builder's close-cycle checklist require one named candidate commit,
then the complete gate on that exact commit, then an adversarial review of that same tree, and
finally an evidence-only follow-up whose parent is the gated candidate. The builder still says
`Status: Candidate`, leaves the final gate unchecked, and says that no gate is recorded.

### Evidence

The builder's candidate narrative predates the latest fixes. The current `HEAD` is `357e5487`,
while the earlier candidate was `08801efb`; the policy, connection, optimizer, and associated
test/documentation changes landed after that candidate. The working tree is also not clean because
the concurrent spec-034 edits remain present. Historical suite figures therefore cannot describe
the tree now being reviewed.

### Required disposition

1. Finish the implementation/documentation tree and create the candidate commit that contains
   these latest fixes.
2. Update the builder record to name that exact SHA; keep the status as candidate until the gate
   is green.
3. On a clean checkout of that SHA, run every declared gate: the default suite at
   `fail_under = 100`, the sharded suite, the declared supported-floor scope, structural/layout
   checks, citation and tracked-path checks, generated-document checks, `manage.py check`, and
   `makemigrations --check --dry-run`.
4. Re-run this review against that exact tree. If no Decision-20 finding remains, make the
   evidence-only follow-up that changes the builder record alone and names the candidate parent.

Until this sequence exists, the board's DONE state and prior probe results are not release
evidence. This is a release blocker even though the current code fixes the earlier runtime
defects.

## P1 — the spec/rationale/build ledger is stale after the connection fix

### Broken contract

The implementation and the governing records must describe the same trust boundary. The current
code seals connection `OrderSet` results, but the records still describe that exact seam as an
unresolved defect.

### Evidence

- `docs/spec-050-list_field_arguments-0_0_15-rationale.md` Decision 20 still says that
  `connection.py::_pipeline_sync` / `::_pipeline_async` apply both `FilterSet` and `OrderSet`
  results without a routing snapshot or re-seal.
- `docs/builder/DONE/build-050-list_field_arguments-0_0_15.md`'s deferred-work catalog repeats
  that `OrderSet` is unsealed on connections.
- `KANBAN.md` now records the correct split: the `OrderSet` half is discharged and the remaining
  follow-up is the `FilterSet` return seal at both fields (card 053).

This is not a cosmetic discrepancy. It makes the spec claim a shipped security gap that the code
has closed, while the builder's close procedure cannot tell whether the latest connection changes
belong to the candidate being gated. It also leaves future reviewers likely to re-open or remove
the shared seal while trying to satisfy an already-discharged row.

### Required disposition

Reconcile the records before the final gate:

- state in Decision 20 and the rationale that connection `OrderSet` sealing is discharged by
  `utils/querysets.py::apply_orderset_sync` / `::apply_orderset_async` and their two callers;
- leave only the `FilterSet.apply_*` connection/list seal as the explicitly deferred card-053
  work, with its owner and reason;
- update the builder's candidate description, predicted paths, and deferred catalog to the
  latest candidate SHA and the same OrderSet/FilterSet split; and
- keep the overall status candidate until Decision 22's gate and evidence-only follow-up are
  complete.

## P2 — the new connection async seal has no live transport proof

The production code now promises the same post-`OrderSet` contract in both connection pipelines,
but the live malformed-result matrix in
`examples/fakeshop/test_query/test_connection_pagination_api.py` is synchronous. The package
suite has async unit rows in `tests/test_connection.py`, but there is no live
`/graphql-async/` connection row exercising an async consumer resolver and
`OrderSet.apply_async` through Strawberry's Relay window and error rendering.

This is a supported public shape: a `DjangoConnectionField` with an async resolver and a declared
`orderset_class`, reached by a real `orderBy` request. A regression in awaitability handling,
connection completion, or error masking could therefore pass the current live suite while
breaking the advertised async path.

If the connection hardening remains part of the shipped implementation, add a live async control
and malformed rows (at least evaluated, sliced/combined, wrong-model or wrong-route, and a
healthy delegation) over the async mount, asserting the typed GraphQL error and the absence of a
raw exception. If this extra connection guarantee is intentionally outside spec-050, narrow the
implementation/documentation claim instead of leaving the async behavior implied but untested.

## P2 — committed review artifacts retain dead helper references

`docs/builder/bld-050-close-trust_docs.md` and `docs/dry/dry-file-utils__querysets.md` still refer
to `list_field.py::_apply_orderset_sync` / `::_apply_orderset_async`. Those helpers were moved to
`utils/querysets.py::apply_orderset_sync` / `::apply_orderset_async` and the old symbols no longer
exist. The stale references make the historical audit hard to replay and can fail a future
citation/source sweep even though they do not change runtime behavior.

Update the references to the shared helper paths, or explicitly mark the artifacts as superseded
by the connection-seal change while preserving their historical conclusions. Do not silently
delete the worker records.

## Deliberately not admitted as new spec-050 defects

- `connection.py` still passes `FilterSet.apply_*` results through without the new seal. This is
  now explicitly owned by card 053 and must not be represented as closed by spec-050.
- A consumer-supplied sliced `Prefetch` without `to_attr` can still receive Django's own
  refiltering `TypeError`. That is application Python under Decision 20's trusted boundary; the
  package-generated plain-list child is the path that now fails with the typed seal defect.
- The exact-queryset foreign-result-cache case remains the builder's documented robustness item;
  it has no supported wire/configuration input and is not a Decision-20 release blocker.

## Required disposition summary

The runtime hardening currently looks correct for the reviewed rows. Reconcile the rationale and
builder with the discharged connection `OrderSet` fix, add or explicitly scope the async live
connection proof, repair the dead helper references, then run the complete Decision-22 gate on a
newly named clean candidate. Until that evidence-only closeout exists, spec-050 remains a
candidate rather than a finished release feature.

<!-- LINK DEFINITIONS -->

<!-- Root -->

[agents]: ../AGENTS.md
[goal]: ../GOAL.md

<!-- docs/ -->
