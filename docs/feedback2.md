# DRY flow review: after the rewrite

The core design is substantially better. Keep it. The vocabulary, per-axis change challenges,
responsibility-based ownership, explicit lifetime, independent oracles, and measured rejection
standard now express the condenser's purpose without reducing it to line-count golf.

The remaining problems are primarily instructions that conflict when an agent follows the whole
cycle, rather than missing DRY techniques. I would resolve the three High findings before using
this flow for a write-enabled cycle. No new plugin or additional worker role is needed to fix them.

## Findings

### 1. High — each new item treats the cycle's own earlier changes as untouchable concurrent work

[DRY.md][dry] #"Per item Worker 0 records" takes a fresh baseline before every dispatch, then
says all baseline-dirty files are concurrent work and must never be edited.

Suppose family A extracts a shared owner into `sets_mixins.py`, leaving it uncommitted as required.
Family B then needs to extend that owner. At B's baseline the file is dirty, so B cannot edit it.
The same problem hits an integration repair or a reopened item. The mechanism rejects exactly
the cross-family consolidation the flow is intended to produce. A mid-item external edit to a
previously clean file has the opposite problem: the initial dirty listing does not identify it.

Separate the cycle-entry protected state from the per-item comparison baseline. Track which
changes the cycle owns, permit later items to build on those changes, and stop/reconcile when
external edits overlap. Attribute by inspected content, not simply by path or dirty status.
Record one cycle baseline for the final net-change measurement as well; the current prose only
instructs recording item baselines, while the planner leaves `Cycle baseline` as a placeholder.

Also include new files in the verifier's evidence: ordinary `git diff <baseline> -- <paths>` does
not display untracked additions. A new shared owner and its new tests must not disappear from the
item-scoped review just because nothing has been staged.

### 2. High — “run on a COPY there” does not define a safe use of the prescribed proof tool

[DRY.md][dry] #"Source-mutating experiments run on a COPY there" is the right intent, but the
Tests section specifically directs agents to [prove_failability.py][proof-tool]. Its execution
root is derived from the script's location, not from the manifest or shell working directory:

- `scripts/prove_failability.py` #"REPO_ROOT =" fixes the source root.
- `scripts/prove_failability.py::_resolve_target` resolves targets against that root.
- `scripts/prove_failability.py::_run_scope` runs pytest with that root as its working directory.
- `scripts/prove_failability.py::execute_entry` overwrites the target and restores a saved copy.
- `scripts/prove_failability.py::_resolve_scratch_root` rejects scratch storage inside that root.

Copying a target into `temp-tests/<scope>/` does not make normal package imports resolve to it.
Moving the manifest or changing directory also does not isolate this script. Invoking the live
script with a normal package target still mutates the shared checkout; restoring it can erase
an intervening edit. This is an operational gap, not permission granted by the document to do so.

Specify a complete disposable execution workspace containing the runner, relevant source,
tests, and configuration; invoke that workspace's runner. Verify imported package paths and
database/storage targets before execution, and give its restore evidence a separate unique
scratch directory. Include dirty and untracked inputs deliberately. Do not create branches
implicitly. The already-written isolation requirements in [HUNT.md][hunt]
#"A scratch directory is not a sandbox" provide a useful existing reference.

Authorization must explicitly cover the pytest subprocess too. Running this script is a test
run, not a non-test substitute for the authorization rule.

### 3. High — omission is classified both as duplication to implement and as a defect never to fix

[DRY.md][dry] #"Flavors lacking the guard = second owner by absence" makes absence itself proof
of duplication. The Defects section then names a guard missing from one flavor as a
non-duplication defect that must never be fixed inside the item. Worker 1 is told both to implement
confirmed consolidations and to leave non-duplication bugs unfixed.

These are materially different decisions. Two existing guards may implement one contract and
be consolidated without changing behavior. Adding a previously absent unknown-Meta-key guard
changes which declarations are accepted. Sibling behavior alone does not prove that rejection
is the missing flavor's contract, even when it is a compelling reason to investigate.

Keep omission as a mandatory discovery axis, but call it a possible enforcement gap, not a second
definition. Require a contract source establishing that the guard applies to the missing member.
Route ambiguous or newly proposed contracts to Rio. Record a confirmed behavior defect separately
from any shared-mechanism consolidation, and explicitly state whether an authorized combined fix
is required before the family can close. Do not declare observable equivalence for adding a guard.

This also resolves the collision between “coupled findings must land together” and “defects are
never fixed inside the item”: a necessary correctness repair cannot merely be carded while the
dependent consolidation is accepted.

### 4. Medium — resumed plans have no rule for discovering new inputs or migrating old verification

[DRY.md][dry] #"Plan already exists for the release" tells Worker 0 to continue the plan and
reopen items whose named inputs changed. It does not require reconciling the plan with the current
package inventory. New files have no old item or freshness entry to invalidate; new family members
can introduce another owner without changing any of the old listed files.

This matters immediately for the supported legacy path. [dry-0_0_14.md][old-plan] has checked
file items from the old method but no responsibility index or per-item freshness evidence.
Appending a dated heading does not establish that those checks satisfy the new contract.

At start/resume and before the final gate, reconcile the complete current path population with
the plan: additions, removals, renames, and newly discovered family members. Treat legacy checks
without comparable evidence as unverified, not unchanged. Record stable input fingerprints or
equivalent exact snapshots, including the searched population, tests, and contract sources.
Naming a mutable path is not enough to determine later whether its inspected bytes changed.

### 5. Medium — the gate requirement conflates behavior regression, structural reuse, and proof execution

[DRY.md][dry] #"One owner + no oracle able to detect a second = a finding" is broader than
the earlier rule that a finding must relieve a change obligation. It creates a finding on an
already-single-owned implementation solely because it lacks an architectural enforcement test.
That may be valuable, but it is a distinct outcome, not a measured consolidation.

More importantly, a behavior-preserving hand copy can pass every independent behavior oracle.
A structural guard must detect bypassing the owner; a behavior oracle must detect the wrong
result. Removing a permission check proves the latter, not necessarily the former. The pilot's
function-name test is a good concrete demonstration: its three name assertions in
`tests/mutations/test_resolvers.py::test_write_flavors_share_resolver_entry_factory` cannot
distinguish a factory-produced function from a hand-written one with the same name.

Separate the record into behavioral proof and architectural gate, each with the defect or
mutation it is meant to reject. Use a behavior-preserving hand-copy/bypass as the structural
negative control where appropriate. Classify gate-only repairs explicitly and require a scoped,
justified population; do not generate a bespoke existence test for every helper.

Finally define acceptance when execution is not authorized. The document permits
`execution-deferred` but Worker 2 must confirm that every gate actually can fail and then assigns
the undifferentiated status `verified`. State which obligations inspection can discharge and
which remain pending execution. A green unmutated full suite does not discharge a deferred
failability experiment automatically.

### 6. Medium — closeout can discard the evidence needed for the next verification

[DRY.md][dry] #"their evidence survives only here" makes Outcomes the durable replacement for
item artifacts. Its required contents summarize results, owners, rejections, line changes, and
the test result, but do not preserve the findings' inspected inputs, proof commands, negative
controls, per-axis challenges, or verification judgments.

After scratch artifacts cease to be available, the next run cannot apply the freshness rule or
reproduce the verdict from that summary. A list of owners whose counts dropped is not the evidence
that those counts or the behavioral equivalence were established.

Either retain the completed item records at run-qualified durable paths, or explicitly require
Outcomes to carry the minimal evidence and references needed to reproduce and invalidate each
verdict. Give each run an unambiguous identity beyond the release and date. Existing artifact
names are shared across releases, and a dated heading alone does not identify which artifact
status belongs to which run. Cleanup must name only that run's owned paths, including worker memory.

### 7. Medium — the final gate is invalidated by fewer inputs than can change its result

[DRY.md][dry] #"Package source change after the gate invalidates it" leaves out test changes,
fixtures, pytest/coverage configuration, dependencies, and environment/database-mode changes.
Those can remove exercised behavior or alter the meaning of the reported 100% without touching
package source. This is particularly relevant in a concurrently edited tree.

Bind the final result to the tested source, tests, configuration, dependency environment, and
selected mode. Changes to relevant inputs invalidate it; irrelevant prose need not. Include
collection/execution and skip information so that coverage is not mistaken for all modes being
exercised. The default run does not execute the sharded-specific tests by repository policy;
report that limitation and request any needed additional authorization, rather than silently
claiming those behaviors verified.

### 8. Medium — the dispatch contract is incomplete at pause, final-gate, and file-item boundaries

The command advertises `pause-after-each-item`, but neither [DRY.md][dry] nor
[worker-0.md][worker-0] tells the coordinator when to pause or what resumes it. The ordinary
dispatch rule says `verified` means advance in both modes. A selectable mode needs an explicit
transition: finish independent verification, report the outcome, and wait for Rio before the
next item in pause mode.

The coordinator's closeout also says to dispatch the final gate only after *every item* is
verified, while the generated plan includes the final gate itself as an item. Say every
non-final-gate item, and define how the gate result receives verification and completes its row.
Clarify who asks for test authorization: DRY says the gate Worker 1 asks, while Worker 0 says it
cannot dispatch that worker until authorization already exists.

Finally, file items deliberately make no consolidations; they map rules into family items.
Worker 2's universal zero-edit instruction to search for a real consolidation needs a file-item
acceptance rule: independently validate coverage and assignment, then route candidates to the
holding family. Finding a real candidate assigned to that family is not a reason to demand a
production edit from a worker explicitly forbidden to make one.

### 9. Medium — the “keep a wrapper for its words” exception preserves machinery for a movable explanation

[DRY.md][dry] #"the wrapper is the only site stating a pairing/separation" permits retaining an
otherwise unnecessary wrapper solely because its prose records the relationship. That explanation
can often move to the surviving caller or owner when the wrapper is removed. Keeping it on the
wrapper and recording the keep risks making that decision self-perpetuating.

A one-caller wrapper may genuinely provide a useful semantic name, isolate effects, or preserve
an extension boundary. Keep it for that concrete responsibility, not merely because its current
location contains the only explanation. The deletion challenge should include moving valuable
prose while removing redundant execution machinery. This matches the vocabulary's distinction
between an authoritative definition and its explanation.

## What the pilot establishes

The supplied account is useful evidence of discovery quality. The current source still supports
the specific concern about the resolver-factory name-only test, and registration still spells
its own sync/async entry pair in `auth/mutations.py`. The lifecycle worked example also matches
`sets_mixins.py::SetLifecycleAttrs` and the reset consumer in `utils/inputs.py`.

The pilot does not establish that the entire cycle works: it intentionally stopped at design,
without exercising migration, independent post-edit verification, inter-item ownership, resumed
inventory, or final closeout. Those are exactly where most findings above sit. Preserve its
successful discovery instructions while testing those transitions with small controlled cases.

I inspected the complete revised DRY document and all three DRY role files, the planner and proof
runner's relevant implementation, builder integration, and selected cited package/test owners.
The two full pilot artifacts were not supplied as file paths in this request; I have not treated
the quoted report as independently verified evidence for every underlying candidate or count.
This is a review of the flow, not authorization to apply those candidates or start a DRY cycle.
No tests, mutation proofs, subagents, or production fixes were performed for this review.
The mandatory repository-wide formatter reported one existing Python file reformatted; lint passed.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[dry]: dry/DRY.md
[hunt]: bug_hunt/HUNT.md
[old-plan]: dry/dry-0_0_14.md
[worker-0]: dry/worker-0.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->
[proof-tool]: ../scripts/prove_failability.py

<!-- .venv/ -->

<!-- External -->
