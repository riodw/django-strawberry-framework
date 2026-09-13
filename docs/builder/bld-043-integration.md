# Build: Cross-cohort integration pass (spec-043 post-ship reconciliation cycle)

Spec reference: `docs/SPECS/spec-043-test_client-0_0_14.md` (archived; `Status:` line 72)
Build plan: `docs/builder/build-043-test_client-0_0_14.md`
Cohorts integrated: A (spec + rationale), B (code verification), C (guard respell + contract text), D (nine live conversions)
Status: final-accepted

## Plan (Worker 1)

This is the cycle's only pass that reads the whole diff at once. Every per-cohort
review saw one slice of it; cross-cohort duplication and contradiction are
invisible to all four by construction.

### Required reading, completed

`AGENTS.md`, `START.md` (`## Instruments that lie`, `## Reconciling a spec with the
tree`), `docs/builder/BUILD.md` (`## Cross-slice integration pass`, `## Spec
reconciliation`, `## Claims are proven mechanically`, `## Severity definitions`,
`## Coverage is the maintainer's gate`, `### Fail-open shapes`),
`docs/builder/ARTIFACT.md`, `docs/builder/worker-1.md`, `GOAL.md`,
`docs/GLOSSARY.md`, `CHANGELOG.md`, the build plan in full, all seven cohort
artifacts (`bld-043-review-1..4`, `bld-043-escalation-1..3`), the spec, the
rationale, and `docs/builder/worker-memory/043-worker-1.md`. No "as needed":
every artifact was read end to end before this file was written.
`043-worker-2.md` / `043-worker-3.md` were not read.

### `BUILD.md` pre-steps, discharged literally

1. **Every prior cohort artifact read in order.** Done, above.
2. **Static inspection helper confirmed for every touched `.py`.** Run by this
   pass over all nine files the cycle's own diff reaches —
   `django_strawberry_framework/testing/client.py`, `conf.py`,
   `tests/testing/test_client.py`, and the five live-tier modules plus
   `examples/fakeshop/graphql_client.py` (the helper module D's sync conversions
   route through, read as the shared shape's home). Every invocation passed
   `--output-dir <session scratchpad>/inspect`, never the bare default and never
   `docs/shadow` — `AGENTS.md` rule 23 over `BUILD.md` `### How to run`, the
   reconciliation the build plan records. All nine exited 0. No skip was taken,
   so no skip reason is owed.
3. **Repeated string literals compared across every overview.** Section below.
4. **Imports compared across every overview.** Section below.
5. **Every cohort's deferred items walked.** `### Consolidated deferred-work
   catalog` below; it is what `bld-043-final.md`'s `### Deferred work catalog`
   is built from.
6. **Staged-anchor sweep.** Section below, with a positive control.

### Attribution of the whole diff, by content

Three sources are interleaved in this tree. Attributed by **diff content**, never
by "files my cohorts touched" (`START.md`).

| Path | Owner | Basis |
| --- | --- | --- |
| `django_strawberry_framework/testing/client.py` | Cohort C | the guard respell hunk, one hunk only |
| `django_strawberry_framework/conf.py` | Cohort C | `testing_endpoint_setting` docstring, body untouched |
| `tests/testing/test_client.py` | Cohort C | +14 node ids, `_RecordingTestClient` deleted |
| `examples/fakeshop/test_query/test_client_api.py` | Cohort C | probe marker header + two assertions |
| `test_error_policy_api.py`, `test_relations_async_api.py`, `test_resource_policy_api.py` | Cohort D | conversions, `_multipart` deleted |
| `test_products_visibility_api.py` | **MIXED** — Cohort D (the four conversion hunks) + concurrent spec-050 session (the trailing ~96-line append: `_PLANNED_LIST_QUERY`, `_hide_every_item_under_the_first_parent`, `_planned_item_names`, two `test_a_planned_*` rows) | subject matter is optimizer/planner, not the client |
| `docs/SPECS/spec-043-*.md` + `appx/…-rationale.md` | Cohorts A and C, plus this pass | custody chain |
| `connection.py`, `keyset.py`, `list_field.py`, `optimizer/*`, `orders/sets.py`, `tests/optimizer/test_walker.py`, `tests/orders/test_sets.py`, `tests/test_connection.py`, `tests/test_keyset_connection.py`, `tests/test_list_field.py`, `test_keyset_api.py` | concurrent **spec-050** session | list-field/orderBy/keyset surface, named in `docs/spec-050-list_field_arguments-0_0_15.md` |
| `START.md`, `docs/GLOSSARY.md`, `docs/TREE.md`, `docs/feedback.md`, `examples/fakeshop/apps/kanban/tests/test_mutations.py`, `examples/fakeshop/db.sqlite3`, `docs/builder/bld-final.md`, `docs/builder/build-050-*`, `docs/spec-050-*` | maintainer / concurrent session | baseline-dirty, out of scope |

Nothing outside this cycle was edited, reverted, or deleted. HEAD was read with
`git show HEAD:<path>` into the session scratchpad; no `git stash`, no
`checkout --`, no `restore`, no worktree.

---

## Integration findings

### High:

None.

### Medium:

None. The four cohorts compose. No source defect is routed to any cohort and no
cohort re-loops.

### Low:

#### L-INT-1 — one guard carried five names across the spec, in four sections written by two cohorts (**fixed by this pass**)

The empty-`variables` guard is the one contract both C's respell and D's
conversions sit on top of, and it was the one thing the spec named inconsistently
after two custody passes hours apart. Enumerated before a byte was written
(`START.md` "Enumerate, never grep-count"), each site asserted present exactly
once:

| Spelling | Sites | Written by |
| --- | --- | --- |
| `empty-`variables` guard` | Decision 9, Decision 11, coverage paragraph, DoD row, Test-plan coverage list (5) | Cohort A, confirmed by C |
| ``files=`/`variables=None`` | `## Implementation plan` table row, `## Test plan` preamble (2) | pre-cycle, left by A |
| ``files=` with `variables=None`` | `## Test plan` scenario 5 (1) | pre-cycle, left by A |
| `envelope-coherence guard` | `## Test plan` scenario 15 (1) | **Cohort C**, this cycle |
| ``files=` without usable `variables`` | `### Error shapes` bullet heading (1) | the error case's name, not a guard label — left |

Three of these spell the guard by **one input it rejects**, which is narrower than
what the respelled guard does — the spec's own Decision 9 says the guard also
refuses `variables={}` and a falsy mapping carrying real placeholders. And Cohort
C, whose final verification recorded the deliberate decision that "the
`empty-`variables` guard` LABEL is kept under the respell on purpose … four spec
citers name it", then used a **fifth** name in the scenario-15 text it wrote in
the same pass. The coverage paragraph's "every branch has a named owner" claim
points at scenario 15 by content, so a reader following the claim to its owner
crossed a rename.

Not a contradiction — every one of the sentences is true — so no cohort re-loops.
It is the divergence inventory `START.md` says this pass owes
("Reconciliation slice introduces contradictions it can't see. Integration pass
owes the divergence INVENTORY"), and the fix is label-only prose in the two files
this pass is custodian of. **Converged on Cohort C's own settled label**, four
spec edits and one rationale edit, listed under `### Spec changes made (Worker 1
only)`. Post-edit: `empty-`variables`` is the sole label, 9 occurrences in the
spec; `envelope-coherence` survives at exactly two sites, both as a qualifier
naming the mechanism (spec scenario 15, rationale Decision 9 change record), 0
elsewhere in the tree outside per-cycle artifacts.

#### L-INT-2 — Cohort D's `### Notes for Worker 1` item 7 is false in its premise; its conclusion stands

Item 7 reads: "D8 is the first live row driving
`testing/client.py::TestClient._assert_file_placeholders` and reaching the
`"variables" not in body` guard's neighbourhood."

Measured by AST over both test trees — every `ast.Call` carrying a `files=`
keyword, with its `variables=` argument printed, 26 call sites swept, non-client
`files=` receivers printed too so the exclusions are visible:
`examples/fakeshop/test_query/test_uploads_api.py:483` and `:541` drive
`TestClient().query(..., files=...)`, and
`examples/fakeshop/test_query/test_client_api.py:299` drives
`AsyncTestClient().query(..., files=...)`. All three are **clean against HEAD**
(`test_uploads_api.py` is not in `git status` at all; C's only hunks in
`test_client_api.py` are the marker header and two assertions). So live rows were
already driving the walker before this cycle, in a file no cohort owns.

The item's operative conclusion — a later respell of either guard cannot be graded
on `tests/testing/test_client.py` alone — is therefore **more** true than stated,
not less. This is the one Cohort D note that Cohort C's "notes, discharged item by
item" list does not name, and the measurement is why it needed no discharge: the
spec's coverage paragraph already routes the multipart acceptance path to the live
tier and the walker's rejection branches to the package tier, which is the correct
split and is unaffected. Recorded, no action.

#### L-INT-3 — the build plan's concurrent-file warning is stale on its own date

`build-043-test_client-0_0_14.md` `## Concurrent-session files that will reach the
final gate` item 2 warns that the untracked `print()`-based scratch probe
`examples/fakeshop/test_query/test_zz_probe_api.py` will be collected by the final
gate's full sweep. **It no longer exists**: `ls` reports no such file and
`git status --short examples/fakeshop/test_query/` lists only the six `M` paths.
The concurrent spec-050 session removed its own scratch. Recorded so the final
gate's owner does not hunt for a surprising row that cannot appear, and so nobody
reads its absence as this cycle having deleted another session's file — it did
not. `test_keyset_api.py` (item 1) is still dirty and still the concurrent
session's.

---

## The cross-cohort checks `BUILD.md` prescribes

### 1. Do C's respelled guard and D's converted rows compose?

**Yes, and the answer is read off the code rather than off a green suite.**

`TestClient._build_body` emits `body["variables"]` under `if variables:`
(truthiness) and then raises under `if "variables" not in body:`. The member
exists iff `variables` is truthy, so the respelled predicate is verdict-identical
to the retired `if not variables:` — which is escalation 1's 10/10 census and
Cohort C's 12/12 re-derivation, independently re-derived here from the two lines
themselves. **A converted row can only depend on the old spelling if it passes a
falsy `variables` together with a truthy `files`.** None does:

- AST sweep of every `files=` call site in `tests/` and `examples/fakeshop/`
  (26 sites, receivers printed): every site that reaches `TestClient` /
  `AsyncTestClient` passes a non-empty `variables` — `test_client_api.py:299`,
  `test_resource_policy_api.py:920` (D8), `test_uploads_api.py:483`/`:541`. The
  `<ABSENT>` rows are Django form/`SimpleUploadedFile` kwargs and the package-tier
  guard rows that exist to raise.
- D8 specifically passes `variables={"d": {"label": "l", "attachment": None,
  "image": None}}` — truthy, so neither spelling can reject it, which is what D's
  own note 7 says and what makes the two cohorts' hunks orthogonal rather than
  merely compatible.

Focused confirmation run, by me, `-n0`, `--no-cov`, no coverage-shaped flag:

```
uv run pytest -n0 --no-cov -q tests/testing/test_client.py \
  examples/fakeshop/test_query/test_client_api.py \
  examples/fakeshop/test_query/test_resource_policy_api.py \
  examples/fakeshop/test_query/test_error_policy_api.py \
  examples/fakeshop/test_query/test_relations_async_api.py \
  examples/fakeshop/test_query/test_products_visibility_api.py
```

`collected 153 items` → **153 passed in 39.09s**. This is the seam only: C's two
test tiers plus D's four modules in one process. The full sweep is
`bld-043-final.md`'s and was not run here.

**No new row duplicates a sibling cohort's.** Measured: `def`-name sets
differenced between `git show HEAD:<path>` and the working tree for D's four
files return `+[] -[]`, `+[] -[]`, `+[] -['_multipart']`, and for
`test_products_visibility_api.py` `+['_hide_every_item_under_the_first_parent',
'_planned_item_names', 'test_a_planned_list_relation_…',
'test_a_planned_relation_connection_window_…']` — all four inside the concurrent
spec-050 append, attributed by reading that hunk. **Cohort D added zero test
functions**; Cohort C's fourteen new node ids are all in its own two files. The
two cohorts cannot have written the same row.

### 2. Duplicated helpers across cohorts

**Exactly one way to do each thing, with one named exception that is already
escalated.**

- **Sync live posts.** Cohort D routed all three sync conversions through
  `examples/fakeshop/graphql_client.py::post_graphql` rather than constructing
  private `TestClient()`s — the shared live-tier helper. Zero new sync client
  constructions. AST census of the four owned files finds **zero** raw Django
  client requests surviving (only three `client.force_login` credential calls,
  which are not requests).
- **The package-tier recording double.** Cohort C deleted
  `_RecordingTestClient` (which overrode `request()` and re-spelled the
  production line under test) in favour of `_RecordingDjangoClient` at the
  transport seam. Verified absent from the tree. `_RecordingAsyncTransport` +
  its two falsy subclasses are the async twin of that one seam, holding the
  recording body once; the subclasses declare only *how* they are falsy, which
  is the load-bearing half of a two-row parametrize. Not a near-copy.
- **The one live duplication, and it is not new to this cycle's composition.**
  D's five converted async sites are five near-identical
  `await AsyncTestClient().query(..., assert_no_errors=False, url=...)` bodies
  across four modules (D2, D4, D6, D7, D9), with a sixth unconverted raw post in
  the concurrently-owned `test_list_field_async_api.py`. The natural home is an
  async twin of `post_graphql`, which `graphql_client.py`'s own docstring
  forecloses ("sync-only by construction") and which `AGENTS.md`'s async-exemption
  rule depends on. Correctly **escalated, not deferred on a trigger** — D retired
  its own "wait for a sixth async site" condition on finding the sixth already
  existed. Carried to the maintainer; catalogued below with an owner.
- **Grep of the candidate's readers before recommending consolidation**
  (`worker-1.md` `## Integration pass`): `post_graphql` has live readers across
  the tier and `_RecordingDjangoClient` has three in-file readers, so neither
  flagged shape is dead code. The async shape has five live readers. No
  delete-and-trim case exists.

### 3. Repeated string literals / keys / tuples across the cycle's files

`scripts/review_inspect.py … --output-dir <session scratchpad>/inspect`, nine
files, **Repeated string literals** sections compared pairwise.

The only literal repeated **across** two files by this cycle's own hunks:

- **`"variables"`** — 2x in `django_strawberry_framework/testing/client.py` (the
  emission that writes the member and C's guard that reads it, eight lines apart
  in one method) and 5x in `tests/testing/test_client.py`. Cohort C measured the
  delta against a HEAD copy (3 repeated literals working tree vs 2 at HEAD) and
  kept it: renaming the emitted key without the guard makes **every** `files=`
  call raise, which four rows catch — it fails closed and loudly. Confirmed here;
  the test-tier occurrences are the wire key quoted in assertions, which is what a
  wire-shape test is for. Not a cross-slice DRY candidate.
- **`"requires variables="`** — 2x in `tests/testing/test_client.py`, the `match=`
  phrase for C's two new guard rows, sharing vocabulary with the message in
  `client.py`. A `match=` phrase deliberately quotes the message it pins; a
  constant would decouple the assertion from the string it is asserting.

Everything else is per-file and explained by construction: mount paths
(`/rp-values/` 25x, `/ep/`, `/graphql-async/`) are one-per-site by Decision 7's
per-call `url=`; query documents and fixture labels are each file's own subject.
No dictionary key or tuple shape recurs across cohorts. `conf.py`'s four repeated
literals are pre-existing `ConfigurationError` message fragments in
`_normalize_user_settings`, untouched by this cycle (C's hunk is docstring-only).

### 4. Does the spec tell one coherent story end to end?

**Yes, after L-INT-1.** Read end to end as a reader who was not here, not by
diffing the cohorts' edit lists. The load-bearing cross-section checks:

- **The guard's five homes agree** (`START.md`: "Five homes per contract …
  Cross-checking them = the one instrument no single slice runs"). `### Error
  shapes` (truthiness enters, membership raises), Decision 9 (same, plus the
  falsy-mapping class the walker alone accepts), `## Edge cases and constraints`
  (same in that section's voice), `## Test plan` scenarios 5 and 15, and the
  `## Definition of done` row. All five describe the landed predicate; none
  describes the retired one; none claims one guard covers the placeholder
  contract. After L-INT-1 all five also call it by one name.
- **The endpoint claim's four homes agree** with `conf.py`'s new docstring:
  `## Key glossary references`, `### Error shapes` (both bullets), Decision 7.
  Each states the mechanism — Django's `str()` path coercion, `reverse_lazy`
  working, `/None` as the worked case, "ordinarily a 404" with the hedge that
  `TESTING_ENDPOINT = ""` needs. The non-JSON bullet's "traceback carries the
  failing status" clause — false on its own date at HEAD — is gone, replaced by
  the three observable facts each attributed to what produces it. Escalation 2's
  five recommended edits all landed.
- **The exemption classes agree across four sites** and the class whose last
  exemplar converted (`test_multi_db.py` "custom-view plumbing") is gone from the
  Slice-2 checklist and Decision 11 alike; `[test-multi-db]`'s orphaned reference
  definition went with it (0 occurrences). Decision 9's sentence that
  `test_products_api.py`'s nested two-file shape "converts rather than staying a
  wire-shape exemption" does **not** contradict that file keeping three
  arbitrary-label envelopes: Decision 9 names a shape, Decision 11 names the
  surviving class as "an arbitrary-label `operations` / `map` envelope the
  path-keyed builder never emits", and the three survivors are that class.
- **The Slice-2 census sentences are rules, not tree censuses.** `## Test plan`
  and the DoD now say "each raw `client.post(...)` **a converted file** retains
  carries the … comment naming **which** class it claims — a call that meets no
  class converts rather than acquiring a declaration". Scoped to the switchover's
  own population, which is the only form that survives a file this cycle may not
  touch. D's four converted files retain zero raw posts, so the rule is
  vacuously and durably true of them.
- **Every `::test_…` identifier the spec and rationale cite resolves.** My own
  instrument, independent of C's: AST-collect every function/class name in
  `tests/` and `examples/fakeshop/`, then resolve every `::test_[A-Za-z0-9_]+`
  in both documents. Spec **24 cited, 0 unresolved**; rationale **3 cited, 0
  unresolved**. This is the check that caught C's scenario-8 hole (a deleted test
  double described as the current mechanism); it now returns clean, and scenario 8
  describes the landed transport-seam double.
- **No deleted symbol is described as present.** Swept both documents for
  `_RecordingTestClient`, `_multipart`, `_graphql_data`, `_post_graphql_as_staff`,
  `AsyncClient`: the surviving mentions are Decision 5 / Decision 8 / `## Current
  state` describing `django.test.AsyncClient` (which `AsyncTestClient` still
  wraps) and dated `## Current state` / `## Problem statement` observations of the
  pre-build tree, which the vintage rule keeps.
- **`Status:` re-verified** (`worker-1.md`, every spawn): line 72 reads
  **COMPLETE (card `DONE-043-0.0.14`)** and still matches the tree after this
  pass's edits. Header lines 1-20 describe the shipped surface accurately. No
  status edit owed.

### 5. Does the rationale stay keyed to the spec?

**Yes.** Fifteen entries: twelve decision entries plus `## Borrowing posture`,
`## Risks and open questions`, `## Current state`; each opens with a
`Spec: [Decision N][dN]`-shaped pointer, and every spec Decision carries a
one-line pointer back. Checked mechanically rather than by reading, with my own
auditor over both files — reference uses vs definitions, in-page `](#…)` anchors
vs real headings, cross-file definition fragments vs the target file's real
heading slugs, and disk existence of every definition path, with fenced blocks and
code spans stripped first:

| File | uses / defs | undefined | unused | broken in-page | broken def targets |
| --- | --- | --- | --- | --- | --- |
| spec | 79 / 79 | 0 | 0 | 0 | 0 |
| rationale | 26 / 26 | 0 | 0 | 0 | 0 |

Re-run after this pass's edits: identical, 0 problems.

**The three maintainer decisions each carry their rejected alternatives and why
each lost**, and each is in the rationale rather than the spec:

- **Decision 1 (guard respelled)** — rejected: delete it (the walker does not
  catch the falsy-container class at all); keep the `if not variables:` spelling
  and only add rows (leaves a truthiness test where absent and empty differ);
  superseded: Cohort B's own keep-and-pin *reasoning* (it invoked "never a weaker
  boundary" while asserting the guard decides no verdict, which would forbid
  deleting any dead branch).
- **Decision 2 (no endpoint validation)** — rejected: reject a non-`str` at the
  accessor (ships a concrete `reverse_lazy` regression and makes this the
  module's first shape gate against four sibling docstrings); leave both alone
  (the docstring is false for `""`).
- **Decision 3 (convert, don't comment)** — rejected: write the nine exemption
  comments (asserts a class the sites do not meet; a false declaration forecloses
  the next reader's question); defer to `TODO-ALPHA-053-0.0.15` (needs a board
  edit the fence excludes, and an unowned item dies).

No entry contradicts another, no entry names a decision that does not exist, and
no decision lacks an entry. Two further corrected **reasons** are recorded where
the verdict survived but its warrant did not — Decision 6 (`Response.response`'s
default is kept for shipped-public-surface reasons, not dataclass field ordering)
and Decision 8 (the async default arm is pinned; the earlier mutation was
orthogonal to it) — which is the right place for both.

### 6. Staged-anchor sweep

```
grep -rEn 'TODO\(spec-043|TODO-(ALPHA|BETA|STABLE)-043' . \
  --exclude-dir=.git --exclude-dir=.venv \
  --exclude=KANBAN.md --exclude=KANBAN.html --exclude=BACKLOG.md
```

**16 hits, zero in source.** Every one is prose: the spec's own
anchor-discipline sentence and three `TODO-ALPHA-043-0.0.14` card-id references,
`spec-042` / `spec-040` / `spec-037` / `spec-041` companions naming the card,
and this cycle's own `bld-043-*` artifacts. No `.py`, no comment, no docstring.

**Positive control, because an empty grep is a grep that ran on nothing:** the
same expression widened to `TODO\(spec-0[0-9]{2}` returns hits in
`spec-053`, `spec-044`, `spec-036` and `docs/dry/dry-0_0_12.md`. The instrument
works; the 043 population is genuinely empty. Cohort D's report of "none
survives" is confirmed on an instrument that can fail.

### 7. One-way dependency direction

**Imports** sections compared across all nine overviews.

- `django_strawberry_framework/testing/client.py` → `conf` (`testing_endpoint_setting`)
  and `exceptions` (`_safe_arg_repr`). `exceptions.py` imports **no** first-party
  module; `conf.py` imports only `exceptions`. **No cycle**, and the direction is
  leaf-ward.
- **No package runtime module imports `testing.client`.** Grep over
  `django_strawberry_framework/` returns only `conf.py` comments/docstrings naming
  it and `testing/__init__.py`'s own re-export. Helper-reuse item **D-N2**'s
  standing claim — "no package runtime module may import test utilities" — holds
  at HEAD and after this cycle.
- **The spec now records the post-ship dependency.** `## Helper-reuse obligations
  (DRY)` carries **D5** for `exceptions.py::_safe_arg_repr`, naming it a
  package-internal reuse rather than an upstream borrow, and Decision 9's closing
  paragraph cites D5 by name. The gap Cohort B's note 7 flagged is closed.
- **Cohort D's new edges are example → package** (`test_error_policy_api.py`,
  `test_products_visibility_api.py`, `test_relations_async_api.py`,
  `test_resource_policy_api.py` each now import from
  `django_strawberry_framework.testing`), which is the switchover's whole point,
  and `examples/fakeshop/graphql_client.py` → `django_strawberry_framework.testing`
  already existed. No sibling imports outside the documented boundary; no example
  module is imported by any package module.

### 8. Fail-open shapes, read off the diff

`BUILD.md` `### Fail-open shapes` catalogues clamps, `getattr` defaults, `or`
fallbacks on legitimately-falsy left operands, broad `except` around a check, and
truthiness where absent and empty differ. Read across the **whole** cycle diff,
not per cohort:

- C's respell **retires** one of them: `if not variables:` was the catalogued
  "truthiness test on a value that can be absent" and is now a membership test on
  a dict the method built one line earlier — `BUILD.md`'s own prescription
  ("guard the ANSWER, not one spelling of the incoherent input") applied to the
  suspect that section names.
- C's `conf.py` hunk is docstring-only; Worker 3 proved it by inverse with a
  docstring-stripped `ast.dump` identity against HEAD (22,457 characters) plus a
  positive control on `client.py` showing the instrument reports *not* identical.
- D's diff adds no guard, no default, no `except`, and no clamp: it is call-site
  substitution with `assert_no_errors=False` at every site that previously read
  the envelope itself. The one shape worth naming — D1 now decodes before its
  row's own `response.content` message — was graded by D's custodian and is a
  message-quality change on a path that fails **loudly** in both shapes, never a
  permit.
- No new clamp, `getattr` default, or `or` fallback appears anywhere in the
  cycle's own hunks.

---

## Consolidated deferred-work catalog

Every item every cohort routed forward, de-duplicated across artifacts, each with
a **named owner** (`AGENTS.md` `## Past mistakes`: an item routed forward without
a named owner dies). `bld-043-final.md`'s `### Deferred work catalog` is built
from this list. Cohort B's M1-M4 and L1-L3 are **not** here: all seven were
discharged by Cohorts C and D or overturned by the three escalations.

1. **The live-tier `README.md` `Async` bullet is falsified and unowned.**
   `examples/fakeshop/test_query/README.md` line 918 names `django.test.AsyncClient`
   and a helper exemption for both `test_list_field_async_api.py` and
   `test_relations_async_api.py`; after D7 the second drives `AsyncTestClient` and
   declares no exemption, and the bullet names neither `test_products_visibility_api.py`
   nor the other two files whose async rows converted. The file is a `.md`, so the
   maintainer's fence (spec files + `.py` only) put it out of every cohort's
   reach, and homing it on a card needs a KANBAN DB edit the same fence excludes.
   Corrected replacement wording is on disk in
   `bld-043-review-4-live_conversion.md` `### Notes for Worker 1` item 5 — and D's
   custodian rejected Worker 3's first recommended wording, which would have
   falsified the half of the bullet that is still accurate.
   **Owner: maintainer.** The cycle's one genuinely undischargeable item.
   Sources: D plan note 1, D build-report note 2, D review Low 3, D final item 5,
   C catalog item 1, build plan `## Items Cohort D routed to Worker 0` item 1.
2. **The async live-tier post helper — a contract decision, not a deferral on a
   trigger.** Five near-identical `await AsyncTestClient().query(...)` bodies
   across four modules, a sixth unconverted raw post in the concurrently-owned
   `test_list_field_async_api.py`. Extracting it reverses
   `examples/fakeshop/graphql_client.py`'s stated sync-only contract, the
   live-tier README's `Async` bullet, and `AGENTS.md`'s rule that async suites owe
   a stated exemption from `graphql_client.py`. Both options and their costs are
   recorded in `bld-043-review-4-live_conversion.md`
   `### The async-helper deferral`. D retired its own "wait for a sixth async
   site" trigger on finding the sixth already existed — a trigger that cannot fire
   is worse than none.
   **Owner: maintainer**, to decide and home on a card (nominee
   `TODO-ALPHA-053-0.0.15`). Blocks nothing.
3. **No gate fails a raw `.post(` / `.generic(` on a Django client in
   `test_query/` that carries no exemption declaration.** Nothing in `scripts/` or
   `.pre-commit-config.yaml` sees it; five files drifted in two months precisely
   because the rule has no gate (`START.md` "Rule w/o gate rots"). The root-cause
   fix is the gate, not the sites, and it is a `scripts/` + hook change plus a
   board edit — outside this cycle's fence in both halves.
   **Owner: maintainer**, to home on a card (escalation 3 nominates
   `TODO-ALPHA-053-0.0.15`, which already owns CI/hook changes and live-tier debt).
4. **Undeclared raw-request posture in four live files, pre-existing at HEAD.**
   `test_transport_api.py`, `test_auth_api.py`, `test_debug_toolbar_api.py`,
   `test_list_field_async_api.py` retain raw client requests whose declaration
   names a different spec, names the sync-only `graphql_client.py` exemption, or
   names nothing. Only `test_products_api.py`'s three sites carry a comment naming
   spec-043. Same population as item 3, spans files in no cohort's write set.
   Named explicitly so a future DoD sentence is not written as though it were
   discharged — which is exactly why C rewrote the DoD as a rule over the
   switchover's own population instead.
   **Owner: maintainer**, with item 3's gate.
5. **`test_list_field_async_api.py`'s conversion** — one undeclared raw async post
   survives there. Excluded from this cycle by the applied partition
   (`AGENTS.md` rule 34); the file appears in five live spec-050 artifacts and its
   last three commits are spec-050's. The spec text as now written needs no
   amendment when it lands.
   **Owner: the concurrent spec-050 cycle.**
6. **Escalation 2's package-tier endpoint row** — a `tests/base/test_conf.py` row
   asserting `testing_endpoint_setting()` returns a non-`str` verbatim, with the
   docstring reason (Django coerces; a gate would reject `reverse_lazy`). Outside
   every cohort's write set this cycle; `tests/base/` may grow rows but no files.
   Recorded in the rationale under Decision 7 as considered-and-not-taken **with
   the reason**, so a later pass knows it is absent by decision.
   **Owner: whichever card next opens `tests/base/test_conf.py`.**
7. **`docs/SPECS/appx/spec-042-debug_toolbar-0_0_14-rationale.md` carries a count
   this cycle falsified.** Its line 35 states "three sentences in `spec-043`
   citing 'spec-042 Revision 8' by name". Re-measured today: **0** in the spec and
   **1** in the spec-043 rationale. The claim's substance survives (the citations
   found their destination, which is what that sentence predicted); its arithmetic
   does not. Non-writable this cycle — the fence covers only spec-043's own
   companions.
   **Owner: maintainer.** Source: Cohort A `### Notes for Worker 1 / Worker 0`
   item 1, re-verified here rather than inherited.
8. **Two concurrent cohorts shared the three `worker-memory/043-worker-{1,2,3}.md`
   files.** Not a partition defect — `BUILD.md` `### Worker memory` scopes the
   notebook per role, not per cohort — but it made the ~50-line consolidation cap
   unsafe (consolidating would clobber a concurrent pass's entry, and did nearly
   happen: Cohort C's planning entry landed between Cohort D's planner's read and
   its write) and it makes role memory a real cross-cohort channel, the one place
   information moves between concurrent cohorts without passing through an
   artifact. Both cohorts appended rather than consolidating, which is the right
   handling.
   **Owner: Worker 0**, for the next partition's memory-stem naming.
9. **The cycle's instrument failures, for the closeout retrospective.** Nine now,
   every one caught only by a second instrument: Worker 0's F3 table grading prose
   with the code's vocabulary; a pre-flight gate reading that went stale inside its
   own cycle; Cohort B's `.post(`-blind census (missed a
   `client.generic("POST", ...)`) and its ninth *file* outside its own stated
   population; Cohort D's planner's live node count moving under its author; the
   `variables={}` census blind to a positional argument; the "15 callers" that is
   17; the "two helpers forward under `is not None`" that is one; and — this pass —
   Cohort D's item 7 premise (L-INT-2). Cohort C's enumeration built so the
   deferred pass "cannot miss one" had three holes, found only by re-deriving the
   population rather than patching the named line.
   **Owner: Worker 0's closeout job**, after the maintainer commits.

---

## Final verification (Worker 1)

- **Every cohort artifact's `Status:` walked.** A `final-accepted`,
  B `revision-needed` (the correct terminal value for a pure verification cohort
  whose whole product was the finding list; the build plan records why its box
  stays unticked and where its findings were discharged), C `final-accepted`,
  D `final-accepted`. Nothing is left at `built` or `review-accepted`.
- **Checklist boxes.** Cohorts A, C and D each report all their dispatched boxes
  `- [x]` and each re-derived them against the diff at final verification;
  spot-confirmed here for the boxes with cross-cohort consequence (C's box 14
  `_RecordingTestClient` deletion — absent from the tree; C's box 17 exemption
  class — `custom-view` returns 0 in the spec; D's D8 — `_multipart` absent,
  caller on `TestClient(..., files=...)`). Only Worker 0 marks plan checkboxes.
- **Coverage.** No coverage tooling was run in this pass. `--no-cov` on the one
  focused command; no `--cov*` flag anywhere. Gap-discovery was done by reading
  the diff against the spec, per `## Coverage is the maintainer's gate`.
- **Hot-path budget.** `Not applicable; plan declares no hot path.` Restated from
  the module's runtime position, not from "no executable code changed":
  `testing/client.py` is a consumer *test* utility whose every symbol runs inside
  a test process — never per request, per resolver, per row, per connection, or
  per outbound message in a deployed schema. Cohort D's hunks are test-file call
  sites; Cohort C's are one predicate and one docstring. No contrary finding.
- **Floor verification.** `Not applicable; plan declares floor-verification scope
  none.` No cohort changed a Django / Strawberry / channels integration seam. The
  floor facts, from `BUILD.md` `## Floor verification` (the single canonical
  statement) rather than from memory: Django **5.2.16**, Python **3.10**,
  strawberry-graphql **0.316.0**. F6's correction — the spec no longer restates a
  floor number and names `pyproject.toml` plus that section instead — is a text
  correction and owes no run. This pass installed nothing and did not touch the
  shared `.venv`.
- **Failability proofs.** `None; this pass introduced no new boundary.` No `.py`
  was written. Cohort C's seven entries were confirmed by its own custodian to
  carry all seven required fields with row counts 4/3/4/3/3/2/2 — none at 0 or 1,
  so no boundary is weakly pinned and no `why 0` is owed — and Worker 3 re-ran all
  seven independently with identical node-id **sets**. Cohort D introduced no
  boundary. Re-confirmed here that the cycle's diff adds no unproven boundary: C's
  two production hunks are one predicate respell (verdict-identical, so it retires
  no boundary either) and one docstring.
- **Public surface.** `git diff HEAD -- django_strawberry_framework/__init__.py`
  and `… testing/__init__.py` are both empty. `__all__` and the six re-exported
  testing names are unchanged.
- **Whitespace / conflict markers.** `git diff --check -- docs/SPECS/` clean.
- **Consolidation dispatch.** None needed. No DRY opportunity in this cycle's own
  hunks requires a Worker 2 pass; the one live duplication (item 2 above) is a
  contract decision the maintainer owns, not work a builder may take.

### Gates, run after this pass's edits

A pre-edit reading is no reading of the edit — this cycle's own recorded
instrument failure. Baselines taken before the first byte, shown beside the
post-edit runs.

| Gate | Before | After |
| --- | --- | --- |
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-043-test_client-0_0_14.md` | `OK: 22 terms`, exit 0 | `OK: 22 terms`, exit 0 |
| `uv run python scripts/check_citations.py --check` (whole tree) | `OK: 995 citations resolve (825 in 441 .py files, 170 in KANBAN.md)` | identical |
| `uv run python scripts/check_trailing_commas.py <the two documents> --check` | exit 0 | exit 0 |
| link / anchor / def-target auditor (mine), both files | 0 problems | 0 problems |

`check_trailing_commas.py` was run with **explicit paths only** on both readings;
its repo-wide default auto-fixes, which would rewrite the concurrent session's
files.

**Inbound-citer sweep for the retired spellings.** `envelope-coherence guard`
outside the two documents: 1 hit, in `bld-043-review-3-code_fix.md`, a per-cycle
artifact recording the state at its own close — `START.md` exempts per-cycle
scratch, and rewriting a closed cohort's artifact is forbidden.
``files=`/`variables=None`` tree-wide: **0**.

### Spec changes made (Worker 1 only)

Five edits, all label-only prose discharging **L-INT-1**. No normative statement,
no anchor, no heading, and no reference definition was touched, so no citer could
be stranded; the auditor above confirms it mechanically rather than on that
reasoning. Each site was located by content and the whole population asserted
present exactly once before a byte was written.

`docs/SPECS/spec-043-test_client-0_0_14.md`:

1. **`## Implementation plan` table, the `tests/testing/test_client.py` row** —
   "the owned builder's guards (`files=`/`variables=None`, the placeholder
   walker, …" → "(the empty-`variables` guard, the placeholder walker, …".
2. **`## Test plan` preamble** — "the guard directions the owned builder raises
   (the `files=`/`variables=None` guard, …" → "(the empty-`variables` guard, …".
3. **`## Test plan` scenario 5, the guard-direction clause** — "`files=` with
   `variables=None` raises `AssertionError` from the owned `_build_body`'s
   explicit guard" → "`files=` without usable `variables` raises `AssertionError`
   from the owned `_build_body`'s empty-`variables` guard, for every falsy
   `variables` alike". This one also widens a true-but-narrow sentence to the
   contract Decision 9 states, matching `### Error shapes`' own bullet heading.
4. **`## Test plan` scenario 15, the guard's inventory entry** — "**the
   envelope-coherence guard**" → "**the empty-`variables` guard** (the
   envelope-coherence check)". The mechanism survives as the qualifier; the label
   is now the one the coverage paragraph, Decision 9, Decision 11 and the DoD use,
   so the "every branch has a named owner" claim and its owner agree on the name.

`docs/SPECS/appx/spec-043-test_client-0_0_14-rationale.md`:

5. **Decision 9's change-record heading** — "the envelope-coherence guard is
   respelled, not deleted" → "the empty-`variables` guard is respelled to an
   envelope-coherence check, not deleted". Same convergence in the deliberation
   layer, where the mechanism's name belongs as the *description of the change*
   rather than as the thing's name.

**Not done, deliberately.** `### Error shapes`' bullet heading "**`files=`
without usable `variables`**" is left: it names the error case, not the guard, and
is the phrasing scenario 5 now borrows. No Decision, checklist box, DoD row, or
`Status:` line was touched; nothing was ticked.

### Summary

The four cohorts compose. C's respelled guard and D's converted rows are
orthogonal rather than merely compatible — the predicate is verdict-identical to
the one it replaced, and every `files=` call site in either test tree passes a
truthy `variables`, so no converted row could depend on the retired spelling;
D8's multipart conversion drives the new predicate and passes. Neither cohort
duplicated the other: D added zero test functions and routed every sync post
through the existing `graphql_client.py::post_graphql`, C deleted the double that
re-implemented the line under test, and the only live duplication — five async
near-copies — is correctly escalated to the maintainer rather than deferred on a
trigger that was already met. The spec reads as one contract end to end: the
guard's five homes agree, the endpoint claim's four homes agree with the new
`conf.py` docstring, the exemption classes lost the class whose last exemplar
converted, the Slice-2 sentences are rules over the switchover's own population
rather than tree censuses a file this cycle may not touch would falsify, and all
27 `::test_…` identifiers the two documents cite resolve against the real suites.
One divergence was found and fixed as custodian: one guard had acquired five
names across four sections, one of them introduced by the same pass that recorded
the decision to keep the old label. No staged anchor naming this spec or card
survives in source, proved on an instrument with a positive control. Nine
deferred items are catalogued, every one with a named owner.

Final status: **final-accepted**.
