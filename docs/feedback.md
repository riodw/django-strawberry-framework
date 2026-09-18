# Adversarial review: spec-050 close candidate

Date: 2026-09-17

Verdict: **the row-carry implementation appears correct, but the card is not yet in a state that
can honestly be called DONE.** I found no new supported-project, wire-reachable bypass in the
production delta. I did find two release-integrity blockers, two close-out/test-contract defects,
and two non-blocking documentation issues.

I did not run pytest, per the repository rule. The existing full-suite figures are evaluated as
evidence, not re-used as evidence for this review's current tree.

## P1-1 — The recorded final gate is not for the tree that is about to be committed

**Broken contract:** spec Decision 22 step 2 and the final Definition-of-done row require the
default, sharded, floor, and structural gates to describe one identified tree, and explicitly say
that figures from another tree are not evidence. Step 4 says the record names the commit before
the card is marked DONE.

**What the record says:**

- `docs/builder/DONE/build-050-list_field_arguments-0_0_15.md` identifies HEAD `20646db2` plus
  sixteen paths.
- The older checklist in that same file still calls the final gate the working tree at
  `ab98d240`.
- The status paragraph claims the future maintainer commit of the batch will be the named tree,
  even though that commit does not yet exist.

**What exists now:**

- HEAD is `e3257e25`, one commit after `20646db2`. That commit rewrites twelve test modules. The
  full default and sharded suites required by Decision 22 necessarily include those files.
- The close candidate also contains spec-050-owned changes absent from the sixteen-path inventory:
  `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`, the board database, and the final review artifact.
  `docs/GLOSSARY.md` contains executable examples and behavior claims, so it is not disposable
  bookkeeping.
- The structural population has already changed: the current formatter sees 451 files, while the
  recorded review saw 425. The current citation count is 1108, while the gate table records 1104.
  The current structural checks are green, but that does not substitute for the default, sharded,
  and supported-floor suites on the current candidate.

There is also a design error in Decision 22 itself: a tracked record cannot contain the hash of the
same commit that contains the record. Editing the hash changes the tree and therefore changes the
commit hash. The current placeholder prose is a symptom of an impossible self-reference, not a
valid identity.

**Root fix:** make the close protocol implementable, then run it once on the real candidate.

1. Amend Decision 22 and its Definition-of-done row to use a two-commit close:
   - a candidate commit containing all production, tests, shipped docs, board/database transition,
     spec status, and generated outputs;
   - the full/default/sharded/floor gate and adversarial review run against that exact commit;
   - a record-only follow-up commit that names the gated commit and changes only the build record.
2. Run the structural checks on the record-only follow-up. Do not claim that follow-up itself was
   the full-suite tree; say plainly that its parent is the gated implementation tree and that the
   only delta is the evidence record.
3. Remove every stale tree identifier (`ab98d240`, `20646db2`, “sixteen paths”) from the live gate
   statement. Historical identifiers may remain only where explicitly labelled superseded.
4. Return card 050 to WIP until the new exact-commit gate and review are recorded. The existing
   8333/8353/3169 figures remain useful historical evidence but cannot close the current tree.

This is a release blocker even though it is not a runtime security defect: the code may be good,
but the repository currently asserts stronger verification than was performed on the candidate.

## P1-2 — The board database change is mixed with pre-existing concurrent data

**Broken contract:** the repository's concurrent-work rule says pre-existing dirty data belongs to
another session and must not be silently absorbed. The card's own close plan records that
`examples/fakeshop/db.sqlite3` was already dirty before this cycle, with library seed rows changed
while the kanban and glossary tables still matched HEAD.

The close then moved card 050 to DONE and updated glossary/board rows in that same binary database.
Git cannot commit selected SQLite tables: the current binary diff now contains both the earlier
library-data changes and this card's lifecycle changes. Calling the database out-of-scope in the
baseline does not isolate it once this cycle writes the same file.

**Root fix:** reconstruct the board database from a clean, known base and replay only the card-050
board/glossary mutations, or first let the owner of the pre-existing database change land it and
then reapply/regenerate the card transition. Do not overwrite the concurrent database blindly.
Before committing, compare the database table-by-table against both parents and record which tables
and rows card 050 owns. Regenerate `KANBAN.md`, `KANBAN.html`, and `docs/GLOSSARY.md` from that
disentangled database and rerun their consistency checks.

Until this is done, the binary file cannot safely be included in a spec-050 commit.

## P2-1 — The repository simultaneously says WIP, in flight, and DONE

**Broken contract:** Decision 22 says the card becomes DONE only at the close record, and the
standing docs describe the current checkout.

The generated board says `DONE-050-0.0.15`, but:

- `docs/spec-050-list_field_arguments-0_0_15.md` still says target
  `WIP-ALPHA-050-0.0.15` and `Status: in flight`.
- `TODAY.md` explicitly defines “Today” as the current checkout, then says the list-field card is
  still WIP in its opening note, capability table, and release-work section.
- The spec's completion checklist remains entirely unchecked, while the board copy of the shorter
  checklist is entirely checked.

The rationale's sentence that the card *was authored* as WIP is historical and may remain. The
spec header and `TODAY.md` are present-tense claims and may not.

**Root fix:** after the exact-commit gate succeeds, update the spec target/status to the shipped
card id and completion state, reconcile the spec checklist according to the repository's shipped-
spec convention, and update all three current-checkout statements in `TODAY.md`. Remove the old
instruction that `TODAY.md` must not change at close; it became false when the card lifecycle
changed.

## P2-2 — The live `Manager.from_queryset` proof mounts the manager through private model state

**Broken contract row:** the Definition of done says a relation whose manager is a
`Manager.from_queryset` class with no overrides is proven live under a prefetching plan at two
parent cardinalities and on the async transport. The repository test rule requires real supported
usage where the live endpoint can reach it.

**Supported project shape:** a normal Django model declaration using
`objects = LoanQuerySet.as_manager()` or `Manager.from_queryset(LoanQuerySet)()`.

**Wire input:** the live `patrons { loans { note } }` request already used by the new tests.

The production behavior works for that shape, but the checked-in live proof does not construct it
that way. `_project_relation_manager` rewrites `Loan._meta.local_managers`, manually assigns
manager internals, and calls the private `_expire_cache()` hook for the duration of a request. The
package-tier proof likewise calls the private related-manager `_apply_rel_filters` method directly.
Those are useful mechanism probes, but neither is the public project declaration named by the
contract.

I independently exercised the actual public declaration: a model with a no-override queryset from
`Manager.from_queryset`, a real reverse relation, and a warmed `Prefetch`. The cached relation was
a project queryset with a pending deferred predicate and an exact-list result cache; normalization
returned a plain `QuerySet`, retained the same Django cache, bounded it to two rows, and executed
zero additional queries. That supports the implementation, but it does not repair the repository's
acceptance-test fidelity.

**Root fix:** dogfood the no-op project queryset as the real default manager of the fakeshop `Loan`
model (a custom manager with `use_in_migrations=False` should not require schema state, which
`makemigrations --check --dry-run` must confirm). Then run the existing HTTP document against that
ordinary declaration and retain the absolute two-query assertions at two parent cardinalities plus
the async payload row. Once the absolute count is pinned, the temporary manager mount and its
parallel control schemas can be deleted. This both proves the supported shape and makes the test
substantially simpler.

## P3-1 — The sealed-queryset glossary overclaims row provenance

`docs/GLOSSARY.md` now correctly says that the raw-list policy alone carries `_result_cache`, but
the same paragraph still concludes that “no synthetic row ... can cross the boundary.” The carry
validates the cache container as an exact list; it does not and should not validate the provenance
of each row. Under Decision 20 application Python is trusted, and the raw-list seam guarantees a
row ceiling, not that application-produced cached rows came from a particular SQL execution.

**Fix:** split the guarantees explicitly. Visibility/order seals drop cached rows and preserve
query provenance; the final raw-list seal may carry already-fetched rows and guarantees only that
the package-owned slice cannot exceed the accepted window. Do not describe the latter as a
synthetic-row exclusion boundary.

This is documentation accuracy, not a newly admitted security defect.

## P3-2 — Retired deferred-filter wording still appears in first-party errors

The new implementation admits a well-formed pending deferred filter on any queryset class and
rejects malformed deferred-filter state. Several first-party messages still tell consumers that an
“unresolved deferred filter” cannot be rebuilt, even though unresolved is now the supported case:

- `django_strawberry_framework/permissions.py::_root_error_renderer`
- `django_strawberry_framework/permissions.py::_edge_error_renderer`
- `django_strawberry_framework/utils/querysets.py::_visibility_result_error`
- the module-level querysets boundary description

The current build record already classifies this as deferred wording work, so it does not reopen
spec-050 under Decision 20. The correction is nevertheless mechanical: replace the cause with
“malformed deferred-filter state” at every live message/docstring site and keep the archived-spec
quotations historical.

## What passed this review

- The new `carry_result_cache` policy is confined to `_RAW_LIST_SOURCE_POLICY`; visibility and
  post-OrderSet seals do not inherit it.
- The cache carry refuses every populated cache that is not an exact built-in list before the
  package-owned queryset slice can consult it.
- The pending reverse-relation predicate is baked onto a detached cloned query for exact and
  project queryset classes, with `negate` pinned to an exact bool before its truth test.
- An actual public `Manager.from_queryset` reverse relation, including the warmed-prefetch shape
  that simultaneously has a pending predicate and populated cache, retained the correct rows and
  incurred zero additional queries in a direct probe.
- The current tree passes formatter check, Ruff, the trailing-comma/source-layout check, the
  spec-glossary check (43 terms), citation resolution (1108), tracked-path generation, and
  `git diff --check`.
- The extension documentation now distinguishes enforcement configuration, upstream ordinary
  extension spellings, and package-owned per-operation isolation without claiming to isolate
  third-party extension state.

## Required disposition before commit

1. Fix the impossible/stale close protocol and return the card to WIP.
2. Disentangle the binary board database from the concurrent library-data change.
3. Put every intended spec-050 path into one candidate commit and rerun default, sharded, full
   declared floor, and structural gates on that exact commit.
4. Run the final adversarial review against that commit.
5. Write the evidence-only follow-up record naming the gated commit, then mark the close complete.
6. Reconcile the spec and `TODAY.md` present-tense status claims.
7. Replace the private manager mount with a real fakeshop model manager declaration before treating
   the live Manager.from_queryset row as satisfied.

The implementation itself should be preserved. The required work is to make the acceptance proof
and repository state as trustworthy as the code now appears to be.
