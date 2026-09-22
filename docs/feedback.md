# Adversarial review: spec-050 candidate after the connection-test cleanup

Date: 2026-09-22

I reviewed the current clean tree at `HEAD` (`e5914bc4`) against
[`spec-050`][spec-050], its rationale, [`build-050`][build-050], [`GOAL.md`][goal],
[`START.md`][start], [`AGENTS.md`][agents], the live-suite rules, and the relevant
implementation seams in `list_field.py`, `connection.py`, `utils/querysets.py`,
`resource_policy.py`, `orders/sets.py`, and the optimizer visibility path. I also
reviewed the commits after the previous candidate record (`5ee86193` and
`e5914bc4`). The working tree was clean when this pass began. No pytest run was
performed.

## Verdict

The previous implementation findings are resolved in the current tree:

- the sync and async connection matrices still exercise the shared post-sidecar
  seal, including the materialized-list, `None`, projection, malformed deferred
  filter, non-awaitable, and residual-awaitable shapes;
- the residual-awaitable row checks both coroutine disposal and that its body was
  never advanced;
- the async field really selects the async connection pipeline through an
  `async def` consumer resolver;
- the three prohibited test-body loops were moved into named assertion helpers,
  while the parametrized cases retain their individual `ids=`; and
- the ordering classifier, source seal, resource-policy authority, extension
  isolation, and visibility-before-order pipeline remain present and internally
  consistent.

I found no new Decision-20 production security defect in this pass. Spec-050 is
still not releasable because the exact-tree Decision-22 gate and its evidence-only
follow-up do not exist, and the candidate record no longer identifies the complete
tree now at `HEAD`.

## P1 — the closure gate is still missing, and the candidate identity has drifted

### Contract

Decision 22 requires one immutable candidate implementation tree, the complete
default, sharded, supported-floor, structural, documentation, link, citation,
tracked-path, `manage.py check`, and migration checks on that exact tree, one
Decision-20 review of that gated tree, and an evidence-only follow-up whose parent
is the gated candidate. The card remains open until that sequence is recorded.

### Evidence

[`build-050`][build-050] still says `Status: Candidate`, leaves **Final exact-
commit gate** unchecked, says `No gate is recorded`, and has no closing gate table
or evidence-only follow-up.

The record was last reconciled at `29ddc0a8`, but the current tree also contains
`5ee86193` (the assertion-helper cleanup) and `e5914bc4` (the additional live
visibility coverage and its suite-map/tree updates). The record describes the
candidate as “this commit” without naming a SHA or the complete parent chain.
That is not an identified immutable gate target. Earlier figures, even if green,
cannot certify `e5914bc4` or its later bytes.

### Required disposition

Choose the exact candidate SHA that includes the intended implementation and all
accepted test/documentation fixes, excluding unrelated work. In a clean checkout
of that SHA, run and record every declared Decision-22 gate, including:

- the default suite with `fail_under = 100`;
- the sharded suite and the declared supported-floor scope;
- formatting, structural, documentation, link, citation, and tracked-path checks;
- `manage.py check`; and
- `makemigrations --check --dry-run`.

Then review that same SHA under Decision 20 and make the evidence-only follow-up
whose sole change is the builder record, naming the candidate parent and the
commands/results. Do not mark the card closed from the current record or copy
figures from an ancestor/dirty tree.

This is a release-process blocker required by the spec, not a newly discovered
wire-reachable vulnerability.

## P2 — the post-candidate changes need an explicit spec/build reconciliation

The latest commits are legitimate evidence improvements, but they are not named
in the spec's revision/change record or the builder's candidate parent chain. The
visibility additions are already within the declared floor/live scope, and the
assertion-helper move is a test-only structural correction, so this is not a
production defect. It is still a freshness problem for the release record: a
future gate runner cannot tell from the standing documents whether these commits
are intentionally part of the candidate or merely concurrent work.

Before the gate, either fold these commits into the explicitly named candidate
chain or record that they are out of scope and gate the earlier tree. If they are
included, update the candidate's predicted-path/reconciliation text and rerun the
tracked-path and documentation checks on the resulting SHA. The gate must not be
recorded against one SHA while the review conclusion describes another.

## Verified corrections and non-findings

- A syntax/AST census of
  `examples/fakeshop/test_query/test_connection_pagination_api.py` finds no
  `for`, `async for`, or `while` inside a `test_*` body. The only repeated
  assertion loop is in `_assert_rejection_message`, a named helper called by the
  parametrized rows.
- The README's live-suite rule requiring no test-body loops and per-case `ids=` is
  now satisfied for the connection matrices.
- The async matrices' positive controls and entry sentinels still establish that
  the intended sidecar method and pipeline ran; the residual row still proves a
  second awaitable is closed rather than recursively awaited.
- The shared sidecar seal still freezes routing before the public override,
  validates captured model/lazy/slice/combination/projection state, and pins the
  accepted result to the source's effective connection.
- The offset guard still classifies the ordering collection Django actually
  selects, follows relation `Meta.ordering` for string terms, keeps `F` references
  as column references, and reads both sides of conditional predicates.
- No new resource-policy, extension-isolation, raw-list ceiling, queryset-seal,
  async-cleanup, or visibility-before-order bypass was reachable through the
  supported wire/configuration surfaces in this pass.
- `git diff --check`, targeted Ruff lint, and targeted formatting checks pass. They
  are not substitutes for the outstanding full Decision-22 gate.

## Required disposition summary

1. Freeze and name one candidate SHA that includes or explicitly excludes the two
   post-record commits.
2. Run the complete Decision-22 gate against that exact SHA.
3. Perform the final Decision-20 review against the same gated SHA.
4. Add the evidence-only builder follow-up whose parent is that candidate.

Until steps 2 through 4 exist, spec-050 remains a candidate. The implementation
and the prior test-structure remediation reviewed here are otherwise in good
shape.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[goal]: ../GOAL.md
[start]: ../START.md
[agents]: ../AGENTS.md

<!-- docs/ -->
[spec-050]: spec-050-list_field_arguments-0_0_15.md
[build-050]: builder/DONE/build-050-list_field_arguments-0_0_15.md
