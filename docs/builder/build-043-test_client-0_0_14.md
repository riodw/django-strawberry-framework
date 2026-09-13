# Package build plan: test_client / 0.0.14 (043) — post-ship reconciliation cycle

Spec source: `docs/SPECS/spec-043-test_client-0_0_14.md` (already archived; see
`## Cycle framing` for why the path is `docs/SPECS/` rather than `docs/`)
Target release: `0.0.14` (shipped; card `DONE-043-0.0.14`)
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every slice must justify shared/duplicated patterns before merging.
Ownership partition: **declared, two concurrent cohorts** — see `## Ownership partition`.
Hot-path declaration: **none.** `django_strawberry_framework/testing/client.py` is
a consumer *test* utility: every symbol it owns runs inside a test process, never
per request, per resolver, per row, or per outbound message in a deployed
schema. `BUILD.md` `## Hot-path budget` defines a hot path by those axes, and no
axis reaches this module. Cohort B writes no source at all; if Cohort C is
dispatched, its writes stay inside the same test-only module and its test tiers.
This `none` rests on the module's runtime position, not on "no executable code
changed".
Floor-verification scope: **none.** No cohort changes a Django / Strawberry /
channels integration seam. The clients *call* `django.test.Client` and subclass
`strawberry.test.BaseGraphQLTestClient`, but this cycle's fence forbids changing
that seam's shape — Cohort A edits spec prose only, Cohort B is read-only, and a
Cohort C fix would be a guard inside the package's own owned builder. **One
caveat recorded rather than assumed:** the spec's Slice-1 checklist names a
floor-presence gate for `strawberry.test.BaseGraphQLTestClient` at a
`strawberry-graphql` floor the spec pins as `0.262.0`, while `BUILD.md`
`## Floor verification` — the single canonical statement — pins the floor at
`0.316.0`. That disagreement is finding **F6** below; discharging it is a spec
text correction, not a floor re-run.
Pre-flight: passed on 2026-09-12 with two recorded deviations (steps 3 and 5,
below); baseline: 6 files dirty from a concurrent session, **none** of them in
this cycle's scope.

## Cycle framing

This is **not** a fresh spec build. Card `DONE-043-0.0.14` shipped; the client
module, the settings key, the `testing` root re-exports, the package-tier test
file, and the live acceptance switchover are all on `main`. The maintainer's
dispatch scopes this cycle to four obligations the original build left open or
that later work falsified:

1. The spec's `-rationale.md` companion was **never created**. Every shipped
   spec from 001 through 048 except 043 and 049 carries one under
   `docs/SPECS/appx/`; spec-043 has only its `-terms.csv`. `BUILD.md`
   `## Spec rationale extraction` makes the move the first substantive action of
   a build, so this cycle owes the move retroactively.
2. The spec must be reconciled with **what actually landed** — including
   post-ship commits that corrected or extended the shipped contract, whether
   they were made for this card or to serve later work.
3. The code must be verified for **skipped or dropped spec contract** —
   anything the spec promised that never landed.
4. Explanations of what changed and why go in the **rationale file, never the
   spec**. The spec reads as a clean current contract (`BUILD.md`
   `## Spec rationale extraction`, "The spec stays the heart, and it never
   narrates its own history").

Modelled on `BUILD.md` `## Review rounds`: the input is already-built work, the
maintainer's dispatch is the review document, and Worker 0 verified every
finding against source before dispatch (`### Worker 0 verifies every finding
against source before dispatching`). The verified findings are the
`## Verified finding list` below; each cohort's artifact carries them as its
`### Dispatched findings checklist`.

The immediate precedent is the spec-042 reconciliation cycle
(`docs/builder/DONE/build-042-debug_toolbar-0_0_14.md`), which ran the same
four obligations under the same fence. This plan follows its shape deliberately.

**Scope fence (maintainer-set, binding on every cohort):** this cycle touches
**spec files (`docs/SPECS/spec-043-*.md` + its `docs/SPECS/appx/` companions)
and package `.py` source only.** No `docs/GLOSSARY.md`, no `docs/README.md`, no
`docs/TREE.md`, no `KANBAN.md` / `KANBAN.html`, no
`examples/fakeshop/db.sqlite3`, no closeout / agentflow-doc edits.

**The spec is already archived, and stays archived.** The maintainer's dispatch
names archival as a closing step; Worker 0 verified it is already done —
`docs/SPECS/spec-043-test_client-0_0_14.md` and
`docs/SPECS/appx/spec-043-test_client-0_0_14-terms.csv` are both in place, moved
there by a later spec's `docs/SPECS/NEXT.md` Step 8 sweep. So no cohort moves
the spec; the new `-rationale.md` is **authored directly at its archived
location**, `docs/SPECS/appx/spec-043-test_client-0_0_14-rationale.md`, matching
where every other archived spec's companion lives. Recorded here because
`BUILD.md` `### Spec stays at its working location` would otherwise read as
licensing a move.

## Pre-flight deviations (both maintainer-authorized)

- **Step 3 (artifact reset) — deliberately NOT run.** `docs/builder/` carries a
  **live** cycle for spec-050 (`build-050-list_field_arguments-0_0_15.md`,
  `bld-slice-1..5`, `bld-integration.md`, `bld-final.md`). Deleting them is the
  one irreversible pre-flight mistake (`worker-0.md` step 3) and the maintainer
  directed this cycle to ignore concurrent work. **Every artifact this cycle
  creates carries `043` in its filename**, so no path collides with the live
  cycle. Verified before writing this plan: no `build-043-*` or `bld-043-*`
  path existed.
- **Step 5 (scratch clear) — deliberately NOT run,** same reason:
  `docs/builder/worker-memory/` and `docs/builder/temp-tests/` belong to the
  live spec-050 cycle (and hold the closed spec-040 / spec-042 cycles' files).
  This cycle seeds its own `043-worker-<N>.md` memory files instead of
  overwriting `worker-<N>.md`, and scopes its scratch to
  `docs/builder/temp-tests/043/`.

Steps 1, 2, 4, 6 passed as written:

- Step 1 — `git status --short`: 6 dirty paths, **zero** in this cycle's scope
  (no `spec-043`, no `testing/`, no `conf.py`, no `tests/testing/`, no
  `test_client_api.py` path is dirty). Treated as baseline-dirty out-of-scope
  per `AGENTS.md` rule 34.
- Step 2 — `uv run python scripts/review_inspect.py
  django_strawberry_framework/testing/client.py` exited 0 and wrote both
  outputs.
- Step 4 — `.gitignore` lists `docs/shadow/`, `docs/builder/worker-memory/`,
  `docs/builder/temp-tests/`.
- Step 6 — `uv run python scripts/check_spec_glossary.py --spec
  docs/SPECS/spec-043-test_client-0_0_14.md` → `OK: 22 terms - all have
  glossary entries and at least one spec link.`
- Step 7 — the rationale extraction is this cycle's Cohort A deliverable, not a
  gate it can pass beforehand.

**`review_inspect.py` output location, corrected against `AGENTS.md`.**
`BUILD.md` `### How to run` says every build-cycle invocation passes
`--output-dir docs/shadow`. `AGENTS.md` rule 23 and `START.md`'s script table
say the opposite — `docs/shadow/` has four sibling folders with one owning
script each, and `review_inspect.py` must be pointed at the session scratchpad
instead. `AGENTS.md` wins (`worker-0.md` `## Required reading`: "If any
instruction conflicts with `AGENTS.md` or `START.md`, follow `AGENTS.md` and
`START.md`"). The pre-flight smoke had already written into `docs/shadow/` before
this was reconciled; the two files it added are gitignored and additive, and
were left in place rather than deleted, because `docs/shadow/` is shared scratch
the live spec-050 cycle is also writing into. **Every cohort in this cycle passes
`--output-dir` into its own session scratchpad.**

## Baseline-dirty out-of-scope files

Six paths, all a concurrent session's work: `START.md`, `docs/GLOSSARY.md`,
`docs/TREE.md`, `docs/feedback.md`, `examples/fakeshop/apps/kanban/tests/test_mutations.py`,
`examples/fakeshop/db.sqlite3`. **Never edit, never revert.** Diff against
`git show HEAD:<path>` if a comparison is needed.

This set is a moving target, and **6 is a reading, not a constant** — the
concurrent session may add or drop paths while this cycle runs. Recorded per
`BUILD.md` `### Tracked binary / generated files: churn and concurrent-writer
handling` so no later pass mistakes that churn for this cycle's output.
`examples/fakeshop/db.sqlite3` and `docs/GLOSSARY.md` are specifically the
concurrent-writable generated pair; this cycle's fence forbids touching either
anyway. Attribute a dirty file by **diff content**, never by "files my task
touched".

## Ownership partition

Cohorts A and B have provably disjoint write sets and are dispatched
**concurrently** (`BUILD.md` `### Parallel cohorts under a declared ownership
partition`). Cohort C is conditional and runs **sequentially, after both** — it
would re-open the spec and the rationale, which Cohort A owns, so it could never
run beside A. One shared file is enough to serialize.

| Cohort | Worker | Writes (exclusively) |
| --- | --- | --- |
| **A — spec custody** | Worker 1 | `docs/SPECS/spec-043-test_client-0_0_14.md`; `docs/SPECS/appx/spec-043-test_client-0_0_14-rationale.md` (new); `docs/builder/bld-043-review-1-spec_reconciliation.md`; `docs/builder/worker-memory/043-worker-1.md` |
| **B — code verification** | Worker 3 | `docs/builder/bld-043-review-2-code_verification.md`; `docs/builder/worker-memory/043-worker-3.md`; `docs/builder/temp-tests/043/` (scratch only) |
| **C — code fix** (dispatched only on a confirmed defect) | Worker 1 plans + amends the spec; Worker 2 builds; Worker 3 reviews | `docs/builder/bld-043-review-3-code_fix.md`; `django_strawberry_framework/testing/client.py`; `django_strawberry_framework/conf.py`; `tests/testing/test_client.py`; `examples/fakeshop/test_query/test_client_api.py`; `docs/SPECS/spec-043-test_client-0_0_14.md` + its `-rationale.md` (Worker 1 only); `docs/builder/worker-memory/043-worker-{1,2,3}.md`; `docs/builder/temp-tests/043/` |

No file appears in both **A** and **B**. Cohort B is **review-only**: it reads
`django_strawberry_framework/testing/client.py`, `conf.py`,
`django_strawberry_framework/testing/__init__.py`, `tests/testing/test_client.py`
and `examples/fakeshop/test_query/test_client_api.py`, and writes no source. Its
verdict is what would dispatch Cohort C. Within Cohort C the roles keep their own
separation (`BUILD.md` `### Isolation is non-waivable`): Worker 1 plans and owns
the spec but writes no source; Worker 2 writes source and tests; Worker 3 reviews
and writes neither.

Cohort A does not consume Cohort B's surface and vice versa — but Cohort B's
verdict **can** add findings to Cohort A's spec work, which is why Cohort A's
final verification runs after Cohort B returns (`## Checklist` ordering).

## Verified finding list

Every finding below was verified against source by Worker 0 before dispatch,
with the symbol-qualified path recorded. Cohort A owns F1–F8; Cohort B owns
V1–V6.

### F1 — the `-rationale.md` companion does not exist

`docs/SPECS/appx/` carries `spec-043-test_client-0_0_14-terms.csv` and **no**
`-rationale.md`. **Verified:** `find . -name '*rationale*'` lists 47 rationale
files; specs 001–048 all carry one except **043** and **049**. Cohort A performs
the move retroactively per `BUILD.md` `## Spec rationale extraction` — a
cut-and-paste, not a copy: text that lands in the rationale **leaves** the spec.

### F2 — the spec narrates its own history in three inline revisions

`docs/SPECS/spec-043-test_client-0_0_14.md` #"Revision history (kept inline so
the spec is self-contained)" runs Revisions 1–3 (≈130 lines, spec lines
111–240). `BUILD.md` `## Spec rationale extraction` is explicit that what
changed, when, why, and what was rejected belongs in the rationale file, and
that the spec must read as a clean current contract with no chronology to apply.
Revision 3's F2 entry in particular instructs the reader to reinterpret earlier
text — precisely the shape the rule forbids.

### F3 — six post-ship code changes to `testing/client.py` are absent from the spec

Seven commits touched
`django_strawberry_framework/testing/client.py` after the card's own two
(`2db331cf` feat, `653a3841` review fixes + Slice 2/3 wrap). **Verified** by
`git diff 653a3841 HEAD -- django_strawberry_framework/testing/client.py` and by
grepping the spec for each symbol: `_finish_response`, `_safe_arg_repr`,
`_assert_file_placeholders`, `tuple`, `empty dotted`, `unreadable` each return
**0 hits** in the spec.

The six behaviour families, each with its commit:

1. **`TestClient._finish_response` extracted** (`8bac47be`, the cross-family DRY
   review's item B4). The decode → `Response` construction →
   `assert_no_errors` raise tail, previously duplicated verbatim between
   `TestClient.query` and `AsyncTestClient.query`, is now one un-colored helper
   both colors call. The spec's Decision 5 argues at length that the package
   owns `query()` in **both colors**; it never records that the shared tail was
   later factored out below that decision.
2. **Falsy consumer-supplied client is honored** (`f7fbead4`).
   `TestClient.__init__` and `AsyncTestClient.__init__` moved from
   `client or Client()` to `client if client is not None else Client()`, so a
   caller-supplied client whose `__bool__` / `__len__` reports false is no longer
   silently discarded onto a fresh client with a different session. The spec's
   Decision 5 / Decision 8 constructor text describes neither spelling.
3. **Diagnostics render through `_safe_arg_repr`** (`f7fbead4`). Every
   `AssertionError` message in `_build_body` and `_assert_file_placeholders`
   moved from `{key!r}` to `_safe_arg_repr(key)`, importing
   `django_strawberry_framework.exceptions::_safe_arg_repr`, so a hostile
   `__repr__` on a consumer-supplied path or value cannot escape the guard as a
   raw exception. This is a **new cross-module dependency** the spec's
   `## Helper-reuse obligations (DRY)` section does not list.
4. **Tuple variables are walked as arrays** (`a8f31a2d`).
   `_assert_file_placeholders` moved from `isinstance(current, list)` to
   `isinstance(current, (list, tuple))`, matching what `json.dumps` actually
   serializes as a JSON array. Decision 9's placeholder contract says "list
   index" only.
5. **The empty-dotted-segment guard and the unreadable-`__len__` guard**
   (`a8f31a2d`). A `files=` path with an empty segment (`""`, `"data."`) and a
   container whose `len()` raises are both rejected at the source with the
   guards' uniform `AssertionError` type. Neither exists in the spec.
6. **Canonical object-path index validation** (`b4d0c8ae`). The list-index check
   moved from `segment.isdigit() and int(segment) < len(current)` to a guarded
   `int()` conversion plus `index >= 0 and str(index) == segment`, because
   digit-like Unicode and very long decimal strings do not share `int()`'s
   acceptance domain, and `isdigit()` accepts superscripts `int()` rejects.
   Absent from the spec.

Cohort A folds each into the **Decision that owns it** as present-tense
contract, and records what changed and why in the rationale.

### F4 — `conf.py::testing_endpoint_setting.__test__ = False` is absent from the spec

**Verified:** `django_strawberry_framework/conf.py` #"testing_endpoint_setting.__test__ = False"
exists at HEAD and was added post-ship in `a62d6dca`. The spec names the
`__test__ = False` guard in **nine** places, all of them on the *class*
(`TestClient` / `AsyncTestClient`); none covers the **module-level accessor**,
whose name also matches pytest's default `test*` function pattern and which
returns a `str` — collected, it fails the run under
`filterwarnings = error` via `PytestReturnNotNoneWarning`. Same hazard class,
same idiom, unrecorded. Decision 7 is the owning Decision.

### F5 — Decision 9 and `## Error shapes` describe a guard the code does not have

Two disagreements, both **verified** against
`django_strawberry_framework/testing/client.py::TestClient._build_body`:

- `## Error shapes` says the guard is
  `if files is not None and variables is None: raise AssertionError(...)`.
  The shipped code is `if not files: return body` followed by
  `if not variables: raise AssertionError(...)` — **truthiness on both**. The
  observable difference is real: `files={}` posts JSON (the spec's spelling
  would build a multipart envelope with an empty map), and `variables={}`
  raises (the spec's spelling would not). The shipped truthiness is the correct
  behaviour and is documented in the code's own comments; the **spec text is
  the defect**.
- Decision 9 says `_build_body` "enforces this with an explicit
  `raise AssertionError` guard" — singular, describing only the
  `variables is None` case. The shipped contract is a **recursive path walker**,
  `TestClient._assert_file_placeholders`, with five distinct rejection branches
  (empty segment, invalid array index, unreadable array length, non-descendable
  value, non-`None` value at the resolved path) plus the reserved-envelope-key
  guard in `_build_body`. The walker existed at ship time; Decision 9 never
  described it, and Revision 3 only added the reserved-key guard beside it.

### F6 — the Strawberry floor the spec names disagrees with `BUILD.md`

**Verified:** the spec's Slice-1 checklist names
`strawberry-graphql==0.262.0` as "the package's pinned floor", while `BUILD.md`
`## Floor verification` — declared there as "the single canonical statement of
the floor versions" — pins `strawberry-graphql` at **0.316.0**, and
`pyproject.toml` is the ultimate source for the lower bound. The spec's number
is stale relative to both. Cohort A corrects the spec's text to name the source
rather than restating a number that moves (`BUILD.md`: "the role files name this
section rather than restate the numbers"). **No floor re-run is owed** — this is
a text correction, and the floor-presence question it gates
(`strawberry.test.BaseGraphQLTestClient` importable) is settled by the module
importing successfully at HEAD.

### F7 — post-ship test-tier additions are absent from the spec's Test plan

**Verified** by `git log --oneline 653a3841..HEAD -- tests/testing/test_client.py
examples/fakeshop/test_query/test_client_api.py`: four commits added rows after
the card closed — `dbe8e77e`, `b4d0c8ae`, `f7fbead4`, `1c7053ad`, `a8f31a2d` on
the package tier and `dbe8e77e`, `a9fa8c34`, `fa8af3be` on the live tier. The
spec's `## Test plan` numbers scenarios 1–14 and its coverage paragraph claims
every branch has a named owner; the branches F3 introduced (the falsy-client
selection, the tuple walk, the empty-segment guard, the unreadable-length guard,
the canonical-index rejection) have owners in the suite but **no scenario
number**. Cohort A extends the Test plan so the claim stays true. Cohort B
independently confirms each branch really is pinned (V4).

### F8 — the spec's own slice checklist and DoD are the completion claim

Per the shipped-spec convention the Slice and Definition-of-done checkboxes stay
`- [ ]` and the `Status:` line is the completion source of truth (the spec
records this itself, twice). **This is not a defect and no cohort ticks them.**
Recorded as a finding so it is not re-raised: the spec-042 cycle had the same
item, and the spec's own Revision 2 already settled it once. Cohort A's only
obligation here is to confirm the `Status:` line still reads COMPLETE and still
matches the tree after its edits.

### Cohort B verification questions (V1–V6)

Cohort B answers these against source, independently of Cohort A's spec work.
Its product is a finding list, not a fix.

- **V1 — did anything in the spec's Slice 1 checklist never land?** Walk every
  sub-check: the settings key constant + accessor, the module's every named
  symbol (`Response`, `TestClient` with `__test__ = False`, the constructor,
  `_build_body`, the file-map builder, `request(..., *, url=None)`, the owned
  `query()`, `login()`, `AsyncTestClient` + async `query()` + async `login()`,
  `GraphQLTestMixin` with `GRAPHQL_URL`, both assertion helpers,
  `GraphQLTestCase`, `GraphQLTransactionTestCase`), the six `testing` root
  re-exports, and the docstring obligation. Report each as present / absent /
  divergent with a symbol-qualified citation.
- **V2 — did anything in Slice 2 (the live-suite switchover) never land?** The
  spec requires every remaining `examples/fakeshop/test_query/` file whose
  hand-rolled POST helper the client's contract covers to switch, with the
  per-file `_graphql_data` / `_post_graphql_as_staff`-style helpers **deleted**,
  and every retained raw `client.post(...)` carrying the one-line wire-shape
  exemption comment. Measure the real population: grep the live tier for
  surviving hand-rolled post helpers and for raw `client.post(` calls, and for
  each survivor say whether it carries the exemption comment and whether the
  exemption is honest (subject IS the wire envelope) or is an unconverted file.
  State the population size; an empty grep is a grep that ran on nothing.
- **V3 — is the per-call `url=` non-persistence contract actually held?**
  Decision 7 pins that `query(..., url=...)` routes one request and never
  mutates `self.path`. Confirm by reading `TestClient.query` /
  `TestClient.request` / `AsyncTestClient.query` and by locating the test that
  pins it.
- **V4 — is every branch F3 introduced actually pinned by a test?** For each of
  the six behaviour families in F3, name the test node id(s) that would fail if
  the branch were removed. Where a family is **not** pinned, say so — that is a
  finding. Do not run coverage tooling (`BUILD.md` `## Coverage is the
  maintainer's gate, not a worker's tool`); read the diff against the contract.
- **V5 — does the mixin delegate's endpoint resolution match Decision 7's
  ladder?** `GraphQLTestMixin.query` constructs `TestClient(self.GRAPHQL_URL, ...)`.
  When `GRAPHQL_URL` is `None` the constructor falls through to the settings key
  — confirm that is what happens and that the five-rung ladder (per-call >
  constructor > class attr > settings > default) holds end to end with no rung
  short-circuited.
- **V6 — is there any fail-open shape in the module?** `BUILD.md`
  `### Fail-open shapes` — clamps, `getattr` defaults, `or` fallbacks on
  legitimately-falsy left operands, broad `except` around a check, truthiness
  where absent and empty differ. The `client or Client()` → `client is not None`
  fix (F3 item 2) was exactly this class and is already closed; verify no
  sibling survives. Note in particular the `except Exception` around `len()` in
  `_assert_file_placeholders` — decide whether it converts "the check blew up"
  into "the check passed" or into a rejection, and say which.

## Artifact list

- `docs/builder/bld-043-review-1-spec_reconciliation.md` (Cohort A)
- `docs/builder/bld-043-review-2-code_verification.md` (Cohort B)
- `docs/builder/bld-043-integration.md`
- `docs/builder/bld-043-final.md`

Plus, only if Cohort B returns `revision-needed` on a real code defect:

- `docs/builder/bld-043-review-3-code_fix.md` (Cohort C)

## Checklist

**SUPERSEDED — do not read as live.** This list predates the mid-cycle
re-partition; the authoritative checklist is
`## Checklist (superseding the list above)` further down, which carries
Cohorts C and D. Left in place rather than deleted because the cohort rows
above it record what was planned before the maintainer's three decisions
widened the cycle. Ticks belong ONLY to the later list.

- [ ] Cohort A: spec reconciliation + rationale extraction (F1–F8) -> `docs/builder/bld-043-review-1-spec_reconciliation.md`
- [ ] Cohort B: independent code verification (V1–V6) -> `docs/builder/bld-043-review-2-code_verification.md`
- [ ] Cohort C (conditional): code fix for confirmed defects -> `docs/builder/bld-043-review-3-code_fix.md`
- [ ] Cross-cohort integration pass -> `docs/builder/bld-043-integration.md`
- [ ] Final gate -> `docs/builder/bld-043-final.md`

## Final-gate scoping (recorded ahead of the gate)

`BUILD.md` `## Final test-run gate` runs the full `uv run pytest --no-cov` sweep,
the fakeshop `manage.py check` / `makemigrations --check --dry-run` pair, and
the read-only lint/format/diff gate. Recorded ahead of time so the gate's owner
does not have to re-derive it:

- If no cohort changed a `.py` file, the pytest sweep is still run — a
  concurrent session is editing this tree, so a green sweep is the only evidence
  this cycle's spec edits did not land beside a broken tree. Any failure whose
  diff belongs to the concurrent session is recorded and attributed, never
  fixed here (`BUILD.md` `## Claims are proven mechanically`, "Pre-existing at
  HEAD" — record plus escalate).
- `git diff --check` covers the whole tree including the concurrent session's
  dirty files; a whitespace error in one of those is attributed, not fixed.
- Floor verification: `none` per the preamble.

## Cohort returns

### Cohort A — `final-accepted` (2026-09-13)

`docs/builder/bld-043-review-1-spec_reconciliation.md`. The rationale companion
exists at `docs/SPECS/appx/spec-043-test_client-0_0_14-rationale.md` (51,290
bytes); the spec went 153,065 (HEAD) → 142,356 bytes. F1–F8 all closed. Gates:
`check_spec_glossary` `OK: 22 terms`, `check_citations --check` `OK: 994
citations` whole-tree, `check_trailing_commas --check` exit 0 on explicit paths.

Cohort A closed **four defects this plan's finding list did not name**, each a
consequence of the rationale move rather than of the shipped code: 15 undefined
reference links the partial pass introduced; a **failing** `check_spec_glossary`
at pickup (moving Decision 3's rejected alternatives carried off the only spec
links to two terms-CSV rows); a half-moved `## Risks` section; and an
undischarged `## Current state` prediction. Recorded because it is the general
hazard `START.md` names — **retiring text strands inbound refs** — and because
the pre-flight's green `check_spec_glossary` reading was taken *before* the
partial pass ran, so it was stale evidence by the time the recovery agent
inherited it.

### Cohort B — `revision-needed` (2026-09-13)

`docs/builder/bld-043-review-2-code_verification.md`. **No High finding, and no
production-source defect**: V1–V6 each resolve in the shipped code's favour.
Nothing from Slice 1 is absent; the Slice 2 switchover landed with no unconverted
file; the per-call `url=` non-persistence contract holds; the five-rung endpoint
ladder holds end to end; no fail-open shape survives (the `except Exception`
around `len()` converts the blow-up into a *rejection*, not a pass).

The `revision-needed` rests on test-tier defects: **M1** two live rows named for
the endpoint ladder are structurally incapable of failing (the `/alt/` probe
delegates to whatever `/graphql/` resolves to, so routed and fell-back are one
observable — measured, not argued: the wide-scope mutation added zero rows);
**M2** five weakly pinned boundaries; **M3** a test double that re-implements the
production line it tests; **M4** nine raw-post sites missing their exemption
declaration. Plus L1–L3.

## The cycle's instrument failures

Recorded because each produced a clean-looking reading that was wrong, and the
next cycle stands where this one did.

1. **Worker 0's F3 dispatch table graded prose with the code's vocabulary.** The
   recovery dispatch asserted two of F3's six behaviour families were still
   unlanded, on the strength of `grep -c 'list, tuple'` and `grep -c 'unreadable'`
   returning 0 against the spec. Both were **already landed** — the spec's prose
   read "both lists and tuples" and "an array whose length cannot be read", which
   is how a contract should be written and is exactly what those greps cannot
   see. This is `BUILD.md` `## Claims are proven mechanically`'s named failure —
   "a long grep phrase samples a claim's vocabulary rather than establishing its
   population" — committed by the dispatcher, in a table handed to a worker as
   fact. It cost nothing only because the dispatch also said to re-derive rather
   than trust the table, and Cohort A did.
2. **A pre-flight gate reading went stale inside its own cycle.** Pre-flight
   recorded `check_spec_glossary` → `OK: 22 terms` and the recovery dispatch
   repeated it. By then the partial pass had moved spec text and the gate was
   **failing**; the recovery agent found it red. A gate result is evidence for
   the tree that produced it, and a crashed pass in between invalidates it.
3. **A green `git status` is not proof a crashed proof-runner left nothing
   behind.** It happened to be true here, but the check that established it was
   the mutation-marker sweep plus three independent byte-identity instruments —
   not the dirty list.

## Maintainer escalations (contract-level, dispatched for investigation)

`BUILD.md` `### Contract-level findings are escalated as maintainer decisions
before dispatch` and `worker-0.md` `## Review-round dispatch` step 3 forbid
dispatching a builder against a contract choice the maintainer has not decided.
Three were escalated; the maintainer directed each to a fresh investigation
agent rather than deciding from the summaries. **Cohort C is blocked until all
three return** — M2's fix list includes the very guard question 1 asks about.

- `docs/builder/bld-043-escalation-1-empty_variables_guard.md` — is
  `_build_body`'s empty-`variables` guard, proven redundant with the walker,
  subject to DRY enforcement (`docs/dry/DRY.md`)?
- `docs/builder/bld-043-escalation-2-endpoint_validation.md` — should
  `conf.py::testing_endpoint_setting` reject a non-`str`, or should its docstring
  narrow its promise?
- `docs/builder/bld-043-escalation-3-exemption_declarations.md` — fix M4's nine
  undeclared raw-post sites in this cycle (requires a re-partition), or defer to
  a named owner?

## Ownership partition — correction pending

M4's five live-tier files (`test_error_policy_api.py`,
`test_products_visibility_api.py`, `test_relations_async_api.py`,
`test_resource_policy_api.py`, `test_list_field_async_api.py`) appear in **no**
cohort's write set. `BUILD.md` `### Parallel cohorts under a declared ownership
partition` requires Worker 0 to fold them into an owning cohort or re-partition,
and to record the correction here. **Deferred pending escalation 3's verdict** —
if the maintainer defers M4, no re-partition is owed.

## Maintainer decisions taken mid-cycle

Recorded with the **rejected alternatives and the reason each lost**, per
`BUILD.md` `### Contract-level findings are escalated as maintainer decisions
before dispatch`. The next reader's first instinct will be the alternative;
only the recorded reason stops the round being re-fought.

**Every one of the three escalations overturned the finding that prompted it.**
That is the cycle's central lesson and it is why none of them was decided from
Cohort B's summary. Each is reproduced below with the verification Worker 0 ran
independently before bringing it to the maintainer — a review's prescribed
remediation is a hypothesis, never an instruction (`BUILD.md` `## Review
rounds`), and here the *findings themselves* were the hypotheses.

### Decision 1 — the empty-`variables` guard is respelled, not deleted

`docs/builder/bld-043-escalation-1-empty_variables_guard.md`.

**Cohort B's premise was false.** It reported the guard fully subsumed by
`TestClient._assert_file_placeholders` for both inputs it intercepts. It is not:
for a **falsy container carrying real placeholders** — `class FalsyDict(dict):
__bool__ → False`, holding `{"file": None}` — the guard rejects and the walker
**accepts**. Worker 0 reproduced this independently before escalating: with the
guard gone the builder emits `operations` carrying **no** `variables` member
beside a `map` pointing into `variables.file`, a spec-invalid envelope Strawberry
rejects with "File(s) missing in form data".

**Decided:** respell the predicate to `if "variables" not in body:`, deriving the
guard from the envelope it protects rather than re-testing the input's
truthiness, then pin it with `match="requires variables="` rows plus a
falsy-dict-subclass row.

- **Rejected — delete it and let the walker own every rejection.** The evidence
  rules it out: the walker does not catch the falsy-container class at all.
- **Rejected — keep the current `if not variables:` spelling and only add
  rows.** Smallest diff, but it leaves a truthiness test on a value where absent
  and empty differ — `BUILD.md` `### Fail-open shapes`' named suspect — correct
  today only because the walker happens to catch the neighbouring cases.
- **Superseded — Cohort B's own recommendation** ("keep and pin", on the grounds
  that deleting a boundary is what `### Acceptance rule` forbids). The
  conclusion survives; its reasoning does not. As escalation 1 notes, the
  argument as written would forbid deleting **any** dead branch, since it
  invokes "never a weaker boundary" while simultaneously asserting the guard
  decides no verdict. The corrected premise — the guard *does* decide a verdict
  — is what actually saves it.

Further finding folded in: the walker's message for `variables=None` is
**actively misleading** ("the value there is not a dict or list" when there is no
value at any path), so the call-level wording is materially better, not
cosmetically.

### Decision 2 — no endpoint validation; the docstring and spec are restated

`docs/builder/bld-043-escalation-2-endpoint_validation.md`.

**Cohort B's premise (L2) was false.** `django.test.RequestFactory.generic`
coerces the path — `urlsplit(str(path))  # path can be lazy`, verified by Worker
0 against the installed Django — so `None`, `7`, and `["/graphql/"]` post to
`/None`, `/7`, `/['graphql/']` and produce the **identical** 404 +
`ValueError: Content-Type header is "text/html"...` a typo'd string does. There
is no gap to close. The accessor census (10 `*_KEY` constants, 9 readers: 8 thin,
1 validating, 2 toggles deliberately unvalidated) confirms Decision 7's
"validation stays at the consumer" is the module's actual practice, not an
aspiration.

**Decided:** add no validation; restate the docstring and the matching spec
sentences to describe the real mechanism.

- **Rejected — reject a non-`str` at the accessor.** It would have shipped a
  concrete regression: `TESTING_ENDPOINT = reverse_lazy(...)` is a `__proxy__`,
  not a `str`, and works today precisely because Django coerces lazily — the
  comment on that very line says so. A `str` gate breaks it.
- **Rejected — leave both as they are.** The docstring is genuinely false, just
  not for the input class anyone suspected.

Two defects this discharges, neither previously known:

1. **`TESTING_ENDPOINT = ""` is the value that does not 404** — it routes to the
   URLconf root (fakeshop: 200 HTML). The docstring's "ordinary 404" is false for
   a **string**, not for the non-strings.
2. **The spec's `## Error shapes` clause "the traceback carries the failing
   status" is false on its own date** — the status is a pytest frame-locals
   artefact, never in Django's message. Present at HEAD **and** in Cohort A's
   rewrite, so it needs a second custody touch.

### Decision 3 — M4's sites are converted, not commented; Cohort D is re-partitioned in

`docs/builder/bld-043-escalation-3-exemption_declarations.md`.

**Cohort B's premise was false in the direction that matters.** It judged all ten
flagged sites honest exemptions, leaning on the spec's "custom-view plumbing"
class (d). But that class's **only named exemplar, `test_multi_db.py`, was itself
converted** — Worker 0 verified it now carries nine `TestClient` references and
posts through `TestClient(client=client).query(...)`. The class has no surviving
exemplar, and **9 of the 10 sites meet no exemption class at all: they are
unconverted.** `AsyncTestClient` covers every async site, and
`test_resource_policy_api.py::_post` sits in a file that already routes other
calls through the client.

**Decided:** convert them under a recorded re-partition (Cohort D below); Cohort C's
Worker 1 drops the "custom-view plumbing" class from Decision 11 and the Slice-2
checklist.

- **Rejected — write the nine exemption comments.** It would assert an exemption
  class these sites do not meet. A declaration that is false is worse than a
  missing one, because it forecloses the next reader's question.
- **Rejected — defer to `TODO-ALPHA-053-0.0.15`.** Defensible (every undeclared
  file postdates 043's ship by a month or more, so this is later cards' drift
  rather than a Slice-2 miss), but naming the card needs a KANBAN DB edit this
  cycle's fence excludes, and `AGENTS.md` is explicit that an item routed forward
  without a named owner dies.

**Census corrections, both against Cohort B:** the population is 16 `.post(`
sites across **8** files, not 9 — the ninth was `graphql_client.py`, which is
outside the swept population. And a raw multipart POST spelled
`client.generic("POST", ...)` in `test_transport_api.py` is **invisible to a
`.post(` grep** — the vocabulary-not-population failure, committed inside the
census that was checking for it.

**`test_list_field_async_api.py` is excluded from Cohort D.** It appears in five
live spec-050 artifacts and its last three commits are all spec-050 work; it is
the concurrent cycle's territory (`AGENTS.md` rule 34). Its declaration also
names the `graphql_client.py` sync-only exemption — a different regime this spec
never names, which is a note for a later card, not this cycle.

## Ownership partition — correction applied

`BUILD.md` `### Parallel cohorts under a declared ownership partition` requires
Worker 0 to record a mid-flight re-partition. Cohorts C and D have provably
disjoint write sets and are dispatched **concurrently**; both run after A and B,
which are closed.

| Cohort | Worker | Writes (exclusively) |
| --- | --- | --- |
| **C — guard respell + contract text** | W1 plans + owns spec; W2 builds; W3 reviews | `docs/builder/bld-043-review-3-code_fix.md`; `django_strawberry_framework/testing/client.py`; `django_strawberry_framework/conf.py`; `tests/testing/test_client.py`; `examples/fakeshop/test_query/test_client_api.py`; `docs/SPECS/spec-043-test_client-0_0_14.md` + its `-rationale.md` (**Worker 1 only**); `docs/builder/worker-memory/043-worker-{1,2,3}.md` |
| **D — live-tier conversion** | W1 plans; W2 builds; W3 reviews | `docs/builder/bld-043-review-4-live_conversion.md`; `examples/fakeshop/test_query/test_error_policy_api.py`; `test_products_visibility_api.py`; `test_relations_async_api.py`; `test_resource_policy_api.py`; `docs/builder/worker-memory/043-worker-{1,2,3}.md` |

**The spec is Cohort C's alone.** Cohort D writes no spec text; anything it finds
routes through its artifact's `### Notes for Worker 1 (spec reconciliation)` and
Cohort C's custodian folds it in. That is what keeps the two disjoint — without
it, both cohorts' planners would want the same file and the partition would
serialize them.

`test_list_field_async_api.py` belongs to **neither** cohort (see Decision 3).

## Checklist (superseding the list above)

- [x] Cohort A: spec reconciliation + rationale extraction (F1–F8) -> `docs/builder/bld-043-review-1-spec_reconciliation.md`
- [ ] Cohort B: independent code verification (V1–V6) -> `docs/builder/bld-043-review-2-code_verification.md`
- [x] Cohort C: guard respell + contract-text fixes -> `docs/builder/bld-043-review-3-code_fix.md`
- [x] Cohort D: live-tier conversion of the 9 unconverted sites -> `docs/builder/bld-043-review-4-live_conversion.md`
- [x] Cross-cohort integration pass -> `docs/builder/bld-043-integration.md`
- [x] Final gate -> `docs/builder/bld-043-final.md`

### Why Cohort B's box stays unticked

`worker-0.md` `## Slice status legend` permits a box only over `final-accepted`,
and `bld-043-review-2-code_verification.md` reads **`revision-needed`** — the
correct terminal value for a pure verification cohort that found something real.
Its whole product was the finding list; its verdict is what dispatched C and D.
Ticking it would be a false completion claim, and sending it back for a
ceremonial final verification would manufacture a `final-accepted` that means
nothing. **Cohorts C and D are where its findings are actually discharged** —
including the three its own premises got wrong, corrected above.

## Items Cohort D routed to Worker 0

1. **The live-tier README's `Async` bullet is falsified by Cohort D's diff, and
   sits in no cohort's write set.** `examples/fakeshop/test_query/README.md` is a
   `.md`, so the maintainer's fence — **spec files and code `.py` files only** —
   puts it out of bounds for every cohort in this cycle. It cannot be fixed here
   and it must not be left unhomed (`AGENTS.md` `## Past mistakes`: an item
   routed forward without a named owner dies). Homing it needs a KANBAN DB edit,
   which the same fence excludes. **Carried to the maintainer as the cycle's one
   genuinely undischargeable item**, and recorded in `bld-043-final.md`'s
   `### Deferred work catalog` with this reasoning so the next reader inherits
   the constraint rather than the omission.
2. **Cohorts C and D share the three `worker-memory/043-worker-{1,2,3}.md`
   files.** Not a partition defect: `BUILD.md` `### Worker memory` scopes the
   notebook **per role**, not per cohort, so two concurrent Worker 1s sharing
   `043-worker-1.md` is the documented shape. Worth recording because it means
   role memory is a real cross-cohort channel while cohorts run concurrently —
   the one place information moves between them without passing through an
   artifact. Neither cohort's correctness depends on it here, and D's planner
   appended rather than consolidating at the cap, which is the right handling.

## Instrument failure, continued: a published node count that moved under its author

Cohort D's planner published a collected-node count, then caught the **concurrent
spec-050 session appending two rows to `test_products_visibility_api.py` mid-pass**
— moving the file to 10 nodes and the total from 85 to 87. The plan was corrected
to instruct Worker 2 to verify "post-edit count equals its own pre-edit baseline"
rather than match any published number.

This is `START.md`'s self-falsifying instrument in its purest form — a live count
of a population the counter is editing, in a tree a second session is also
editing — and it is the fourth instrument failure this cycle (after Worker 0's
prose-graded-with-code-vocabulary F3 table, the stale pre-flight gate reading, and
Cohort B's `.post(`-blind census that missed a `client.generic("POST", ...)`).
Escalation 3 separately found that same census counted a ninth *file* that was
outside its own stated population. **Five instrument failures, every one caught
only by a second instrument.**

## Concurrent-session files that will reach the final gate

Two live-tier paths appeared mid-cycle in **no cohort's write set**. Both were
attributed by **diff content**, not by "files my cohorts touched" (`START.md`),
and both are out of scope: never edit, never revert, never delete
(`AGENTS.md` rule 34).

1. **`examples/fakeshop/test_query/test_keyset_api.py` — modified, +37 lines.**
   A keyset visibility-window test (`PeriodicalType.issuesConnection`, embargoed
   rows, partition counts). Subject matter is the optimizer/keyset surface, which
   no cohort in this cycle touches. The concurrent spec-050 session's.
2. **`examples/fakeshop/test_query/test_zz_probe_api.py` — UNTRACKED, 26 lines.**
   A `print()`-based scratch probe (`test_probe`) comparing list-vs-connection
   item query counts under `is_private` visibility. Again optimizer territory,
   and its `zz_` prefix plus debugging `print()`s mark it as someone's working
   scratch rather than a suite member.

**The untracked probe is the one with a consequence for this cycle.** It matches
`test_*.py` and defines `test_probe`, so **the final gate's full
`uv run pytest --no-cov` sweep will collect and run it** — and `AGENTS.md` /
`START.md` both put temp files in a session scratchpad, never the repo. Recorded
here so the gate's owner reads a surprising row in the sweep as the concurrent
session's scratch rather than as this cycle's regression, and so the maintainer
sees it before a `git add -A` sweeps an untracked probe into a commit.

**Not this cycle's to remove.** Flagged to the maintainer; the no-revert rule
covers dirty and untracked files a cycle did not author, and deleting another
session's in-progress scratch is the same mistake as reverting its edits.

## Escalation pending: the async-helper extraction (Cohort D, final verification)

Cohort D's custodian **retired** its plan's "defer until a sixth async site"
trigger — the sixth site exists today (`test_list_field_async_api.py`'s
unconverted raw post), so the condition could never fire and a trigger that
cannot fire is worse than none. It kept the DRY reading and **escalated the
extraction itself**, correctly: extracting a shared async post helper reverses
`examples/fakeshop/graphql_client.py`'s stated sync-only contract and runs into
`AGENTS.md`'s async-exemption rule. That is a contract choice, not a worker's
call (`BUILD.md` `### Contract-level findings are escalated as maintainer
decisions before dispatch`).

Both options and their costs are recorded in
`docs/builder/bld-043-review-4-live_conversion.md`. **Carried to the maintainer
with the final gate**, not decided here. It blocks nothing: the sixth site is the
concurrent spec-050 cycle's file and out of bounds this cycle either way.

## Cohort D's corrections to its own artifact, and to Worker 3

Recorded because the pattern is the cycle's dominant one and the next reader
should expect it rather than rediscover it.

- Both of Worker 3's Mediums were **corrections to the plan's own measured
  claims**, fixed in place: the `variables={}` census is now an AST enumeration
  over keyword **and** positional arguments (one occurrence, consequence nil),
  and `::_post`'s caller count is 17, corrected in the census, in step D1, and in
  D1's box.
- The custodian then found a **third** wrong figure in the same paragraph Worker
  3 had not reached ("two helpers forward under `is not None`" — it is one). A
  reviewer's finding list is a sample of a paragraph's defects, not its census.
- On Low 3 it went further than the finding: Worker 3's **recommended
  replacement text was itself wrong.** `test_list_field_async_api.py` still
  drives `AsyncClient` and still declares the sync-only exemption, so rewriting
  both halves of the live-tier README bullet would have falsified the accurate
  half. `BUILD.md`'s "a prescribed fix is a hypothesis, never an instruction",
  holding at the third level down.

Its notes to Cohort C's custodian carry the same shape: the four exemption-class
sites are confirmed **plus two more a four-site sweep would strand** (the
delivery-table row and the `## Risks` fallback clause), and an explicit warning
**not** to write "no live file claims the hand-built-multipart class" —
`test_products_api.py` carries three live exemplars, and maintainer Decision 3
licenses dropping class (d) alone.
