# Adversarial review: spec-050 candidate after the async-matrix remediation

Date: 2026-09-21

I reviewed the current candidate at `HEAD` (`29ddc0a8`) against
[`spec-050`][spec-050], its rationale, the builder record, [`GOAL.md`][goal],
[`START.md`][start], [`AGENTS.md`][agents], the live-suite rules, and the
production seams in `list_field.py`, `connection.py`, `utils/querysets.py`,
`resource_policy.py`, and `orders/sets.py`. At the start of the pass the only
dirty path was the unrelated Kanban constants file. Additional library-app
files appeared while the review was in progress; those concurrent changes were
also left untouched and excluded from the candidate assessment. No pytest run
was performed.

## Verdict

The production fixes from the prior rounds are present. The post-sidecar seal is
shared by OrderSet and FilterSet, in both sync and async connection pipelines;
the async test mount really selects `_pipeline_async`; the async matrices now
include the added materialized/none/projection/malformed-deferred/residual-
awaitable shapes; and the positive tests use named seed helpers.

I found no new Decision-20 production security defect in this pass. Spec-050 is
still not closable because its exact-tree Decision-22 gate has not been run or
recorded. I also found a remaining live-suite style violation in the newest
connection evidence.

## P1 — the exact-tree closure gate is still outstanding

### Contract

Decision 22 requires one identified candidate tree, the complete default,
sharded, supported-floor, structural, documentation, link, citation, tracked-
path, `manage.py check`, and migration checks on that exact tree, one review of
that gated tree under Decision 20, and an evidence-only follow-up whose parent
is the gated candidate. The card is not closed before that sequence.

### Evidence

[`build-050`][build-050] still says `Status: Candidate`, leaves **Final exact-
commit gate** unchecked, says `No gate is recorded`, and has no closing gate
table or evidence-only follow-up. The spec's opening status correctly says that
the required work must run against the exact tree and that none of it is yet
evidence; this is now internally consistent, but it also confirms the release
condition is unmet.

The current candidate contains the implementation and the test/documentation
reconciliation, but earlier suite figures cannot certify it. A dirty-tree run or
a run against an ancestor is not a Decision-22 result.

### Required disposition

Produce the intended candidate commit without absorbing the unrelated Kanban or
library-app changes. In a clean checkout of that exact SHA, run and record every declared
gate, including `fail_under = 100`, the sharded mode, the supported-floor scope,
all structural/link/citation/tracked-path checks, `manage.py check`, and
`makemigrations --check --dry-run`. Review that same SHA, then make the
evidence-only follow-up whose sole change is the builder record and whose parent
is the gated candidate. Do not mark the card closed from the current record.

This is a release-process blocker, not a new wire-reachable implementation
vulnerability; it remains mandatory because the spec explicitly made the exact
tree gate its closure contract.

## P3 — three test-body loops still violate the live-suite rule

[`test_query/README.md`][test-query-readme] requires “No loop in a test body;
every case own node id with `ids=`.” The current connection evidence still has
these statement-level loops:

- `examples/fakeshop/test_query/test_connection_pagination_api.py::test_connection_branches_a_malformed_apply_sync_result_names_its_own_defect`
- `examples/fakeshop/test_query/test_connection_pagination_api.py::test_connection_async_branches_a_malformed_apply_async_result_names_its_own_defect`
- `examples/fakeshop/test_query/test_connection_pagination_api.py::test_connection_async_branches_a_malformed_filter_apply_async_result_names_its_defect`

Each contains `for substring in substrings` in the parametrized test body. The
loop is not the matrix itself, but it still violates the same structural rule:
the assertion work is hidden inside one node body instead of being owned by a
named helper. The third loop was added by the latest FilterSet matrix
remediation; the first two remain in the candidate and therefore still fail the
current suite contract.

Move the repeated message assertion into one module helper (the helper may own
the loop), and have each test body call that helper. Keep the `ids=` matrix and
the exact per-row message prefixes. Then rerun the structural/live-test gate as
part of the exact-tree closure run.

This is governance/test-quality debt, not a production security defect, but it
means the new release evidence does not currently satisfy the repository's
acceptance-test contract.

## Verified corrections and non-findings

- The async OrderSet and FilterSet matrices now carry the eleven intended rows,
  including residual-awaitable disposal. The residual coroutine is closed and
  its body sentinel remains untouched.
- The async connection field is constructed with a genuine `async def` consumer
  resolver, so the rows reach `connection.py::_pipeline_async` rather than the
  sync path.
- The shared `_apply_sidecar_sync` / `_apply_sidecar_async` seal validates the
  captured model, lazy state, routing intent, slice state, combinators, and
  projection before the Relay window.
- The positive async FilterSet control proves a real `filter:` argument invokes
  `GenreFilter.apply_async` and still returns the filtered page.
- The prior `UnboundLocalError` theory for `_post_async_genres` is not admitted:
  an exception raised inside its `try` re-raises through `finally`, so Python
  does not continue to the post-`finally` `result` read. The helper can still be
  made clearer with an `else` block, but that is not a reproduced defect.
- No new relation-ordering, predicate-classification, resource-budget, or
  extension-isolation bypass was found in this pass under the project's
  Decision-20 reachability standard.

## Required disposition summary

1. Remove the three test-body assertion loops through a shared helper.
2. Create one immutable candidate SHA that excludes unrelated dirty work.
3. Run and record the complete Decision-22 gate against that SHA.
4. Review that same gated SHA and add the evidence-only follow-up.

Until item 3 and item 4 exist, spec-050 remains a candidate even though the
implementation-side remediation reviewed here is in place.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[goal]: ../GOAL.md
[start]: ../START.md
[agents]: ../AGENTS.md

<!-- docs/ -->
[spec-050]: spec-050-list_field_arguments-0_0_15.md
[build-050]: builder/DONE/build-050-list_field_arguments-0_0_15.md

<!-- examples/fakeshop/test_query/ -->
[test-query-readme]: ../examples/fakeshop/test_query/README.md
