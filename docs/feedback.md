# Adversarial review: spec-050 candidate

Date: 2026-09-21

Reviewed candidate commit `ec0d21de` and the current working tree against
`docs/spec-050-list_field_arguments-0_0_15.md`, its rationale, the builder record,
`GOAL.md`, `START.md`, `AGENTS.md`, and the current Strawberry/Django integration code.
The working tree also contains an uncommitted `tests/test_connection.py` change that is
spec-050-related, plus two unrelated spec-034 documentation edits; none was reverted.

Verdict: the runtime hardening previously reported is in place, but this candidate is not
ready for the Decision-22 close. The new async connection evidence does not exercise the
async pipeline it claims to prove, and the builder's exact-tree gate and scope ledger are
still not a reliable release record.

## Verified fixes

- `django_strawberry_framework/utils/policies.py::resolve_policy` now canonicalizes the
  no-override/default path. Mutating an exported default policy no longer changes a later
  schema's authority.
- `django_strawberry_framework/error_policy.py::ErrorPolicy.__post_init__` rejects string
  subclasses for both string options, keeping consumer formatting hooks out of the masking
  path.
- `django_strawberry_framework/utils/querysets.py::apply_orderset_sync` and
  `::apply_orderset_async` freeze routing before the public override and re-seal the returned
  queryset. `connection.py::_pipeline_sync` and `::_pipeline_async` now use those helpers,
  matching the list-field `OrderSet` contract.
- `optimizer/walker.py::_build_child_queryset` uses the strict sliced-child policy for plain
  list relations, while `_build_connection_child_queryset` retains the slice licence only for
  the nested-connection planner that classifies and degrades it.
- The historical builder/DRY references now name the shared `utils/querysets.py` helpers.
  The `FilterSet.apply_*` return remains explicitly deferred to card 053; it is not silently
  treated as closed by this card.

## P1 — the new async connection matrix does not reach `apply_async`

### Broken claim

The candidate says the new rows drive `GenreOrder.apply_async` through
`connection.py::_pipeline_async`, and the test module docstring says the async mount makes the
shipped connection take that pipeline. That is false for the field being exercised.

### Evidence

The shipped field in `examples/fakeshop/apps/library/schema.py::Query.all_library_genres_connection`
is constructed as `DjangoConnectionField(GenreType)` with no `resolver=`. In
`django_strawberry_framework/connection.py::_build_connection_resolver`, `resolver=None` makes
`is_async_callable(resolver)` false and selects the synchronous `_resolve` closure. That closure
always calls `_pipeline_sync`, which calls `GenreOrder.apply_sync` for `orderBy`.

A read-only probe of the candidate's actual Strawberry field reports:

```text
_build_connection_resolver.<locals>._resolve
False
```

The new rows in `examples/fakeshop/test_query/test_connection_pagination_api.py` monkeypatch
only `GenreOrder.apply_async`. Under the real `/graphql-async/` request, those replacements are
therefore never invoked. The malformed rows will either fail their `data is None` assertion
because the normal sync order path succeeds, or fail earlier for an unrelated setup reason;
neither outcome proves the async seal. The healthy row likewise cannot prove async delegation.

This is a supported public shape, not a theoretical branch: `DjangoConnectionField` explicitly
accepts an async consumer resolver, and the production async pipeline is the code that must
await and validate `OrderSet.apply_async`.

### Required fix

Use a test-local schema/mount with the same `GenreType` and a real `async def` connection
resolver returning the base `Genre` queryset, then construct the `DjangoConnectionField` with
that resolver. Keep the shipped sync field for the synchronous matrix. Add a call counter or
sentinel assertion proving that `apply_async` was entered, in addition to the typed rejection
and no-raw-exception assertions. Update the module docstring and README to distinguish the
shipped sync fixture from the test-local async-resolver fixture; do not claim the shipped field
is async when its public resolver is synchronous.

Until this is corrected, the new candidate test coverage is not merely incomplete: it is aimed
at the wrong execution branch and cannot catch a regression in the code it names.

## P1 — the Decision-22 exact-tree gate is still open

The builder remains `Status: Candidate`, leaves the final exact-commit gate unchecked, and
records no gate or evidence-only follow-up. That is still a release blocker under spec Decision
22, independent of whether the runtime rows above are corrected.

The current checkout is not the candidate tree: `tests/test_connection.py` has uncommitted
spec-related changes, while the two spec-034 documentation changes are concurrent work. No
full default coverage gate, sharded gate, supported-floor scope, structural/documentation gate,
`manage.py check`, migration check, or exact-tree adversarial review has been recorded for the
post-fix candidate.

Required sequence:

1. Correct the async proof and incorporate the intended spec-050 test changes into a new clean
   candidate commit, leaving unrelated concurrent files out.
2. Update the builder to name that candidate by its exact SHA and keep it `Candidate` until the
   gate is green.
3. Run every Decision-22 gate on that exact commit: default `fail_under = 100`, sharded,
   supported-floor, structural/layout, citations, tracked paths, generated docs, `manage.py
   check`, and `makemigrations --check --dry-run`.
4. Re-run the adversarial review on that immutable tree, then make the evidence-only follow-up
   whose parent is the gated candidate and whose only file change is the gate record.

Historical results from earlier candidates cannot discharge this sequence.

## P2 — the builder's scope and ancestry ledger is internally inconsistent

The candidate record now lists twenty-seven floor paths (including the new connection and
sharded live modules), but its close-cycle checklist still says “the twenty-five-path floor
scope.” A gate runner following the checklist can silently omit the two paths the reconciliation
just added.

The top candidate narrative is also not a complete ancestry description. It says the candidate
stands on three post-first-candidate changes, but the history contains additional spec-owned
changes after the earlier candidate, including the default-policy authority fix (`9350eb8d`) and
the async/list test cleanup (`1f68871a`), alongside the connection seal and optimizer policy
fixes. The record intentionally defers exact commit ids to the evidence follow-up, but it still
has to enumerate the complete content delta or the follow-up cannot explain what tree was gated.

Reconcile the count to twenty-seven everywhere it names the floor scope, and either enumerate
all spec-owned post-candidate changes by content or make the final evidence record name the
complete parent chain. Separate unrelated concurrent commits from the candidate description.

## Deliberately not admitted as new spec-050 defects

- `connection.py` still passes `FilterSet.apply_*` returns without a result seal. The rationale
  and builder now correctly assign that half to card `TODO-ALPHA-053-0.0.15`; it must not be
  represented as a spec-050 closure claim.
- A consumer-supplied sliced `Prefetch` remains Django/application behavior under the trusted
  application-code boundary. The newly strict policy is for the package-generated plain-list
  child; the nested-connection planner retains its explicit slice-degrade path.
- A foreign `_result_cache` on an exact consumer queryset remains a documented robustness item
  with no supported wire or configuration input, not a Decision-20 release blocker.

## Required disposition

Keep the production hardening now present. Repair the async live proof so it actually selects
`_pipeline_async`, reconcile the builder's path count and ancestry ledger, then run the complete
Decision-22 gate on a new clean candidate and review that exact tree. Until those steps are
recorded, spec-050 remains a candidate rather than a finished release feature.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[goal]: ../GOAL.md
