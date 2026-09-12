# Build: Review round 1 (Cohort A) — spec-042 rationale extraction + spec reconciliation

Spec reference: `docs/SPECS/spec-042-debug_toolbar-0_0_14.md`
Build plan: `docs/builder/build-042-debug_toolbar-0_0_14.md`
Status: final-accepted

Cohort A of the spec-042 post-ship reconciliation cycle. Spec custody is the one
thing only Worker 1 may do and no source file is in this cohort's write set, so
this runs as a **combined plan + build + final-verification pass** — the
`BUILD.md` `### Procedural-closure slices` shape extended to a custodian-only
cohort. There is no Worker 2 build and no Worker 3 review for Cohort A; Cohort B
(`docs/builder/bld-042-review-2-code_verification.md`) reviews the code
concurrently under the plan's declared ownership partition.

Files written by this pass (the cohort's complete, exclusive write set):

- `docs/SPECS/spec-042-debug_toolbar-0_0_14.md`
- `docs/SPECS/appx/spec-042-debug_toolbar-0_0_14-rationale.md` (new)
- `docs/builder/bld-042-review-1-spec_reconciliation.md` (this file, new)
- `docs/builder/worker-memory/042-worker-1.md`

Nothing else was touched. `git status --short -- docs/SPECS/` shows exactly one
modified file (the spec) and one untracked file (the rationale); the other dirty
paths under `docs/builder/` are the concurrent spec-050 cycle's, left untouched
per `AGENTS.md` rule 34.

---

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable in its code sense — this cohort
  writes no `.py` and proposes no helper, shared constant, validation branch,
  coercion utility, or test helper, so there is nothing for a package-wide AST
  inventory to prevent. The prose analogue was run instead and is the load-bearing
  one here: the spec-041 and spec-040 rationale companions were read in full
  before writing, and this file's structure (`## How to read this file`,
  `## Round vocabulary`, `## Post-ship corrections` keyed by finding number,
  `## Decision entries` one per spec decision) is spec-041's, reused rather than
  reinvented.
- **Existing patterns reused.** The house rationale shape from
  `docs/SPECS/appx/spec-041-channels_router-0_0_14-rationale.md` (the immediate
  predecessor and the canonical voice reference) and
  `docs/SPECS/appx/spec-040-auth_mutations-0_0_13-rationale.md`: the
  *Claimed / HEAD / Cause* triple per post-ship correction, the per-decision
  **Change record** blocks that replace a chronology, the explicit "the claim this
  decision may no longer make" line, and the "what deliberately stayed in the spec
  even though it reads like deliberation" carve-out list. The link-definition
  block uses the same `../../../`-from-`appx/` relativisation.
- **New shared shapes justified.** One, and it is a naming convention rather than
  code: the spec's per-decision pointer line, `Alternatives rejected, and the
  record of every change this decision has undergone: [rationale][rationale-dN]`,
  is identical at all ten sites and resolves to one `[rationale-dN]` def per
  decision. Uniform wording is what makes it greppable when a later custodian
  needs to find every decision whose deliberation moved.
- **Duplication risk avoided.** The move is a **cut**, not a copy: the three
  residual-count sweeps under `### Final verification` prove each moved claim is
  at zero occurrences in the spec. The specific risk was restating a moved
  rejected-alternative inside the decision that rejected it "for readability",
  which would leave two copies to drift; none was kept.
- **Single-cohort partition.** The plan names two cohorts, but their shapes do not
  overlap: Cohort B writes no spec text and this cohort writes no source. There
  is no shared shape to assign.

### Implementation steps

1. Re-derive every finding against source before editing anything (`BUILD.md`
   `## Claims are proven mechanically, never accepted on prose`); Worker 0's
   verification is a hypothesis.
2. Write `docs/SPECS/appx/spec-042-debug_toolbar-0_0_14-rationale.md` first, so the
   destination for every cut exists before the cut is made.
3. Cut the spec's `## Revision history` block wholesale; replace with a one-line
   rationale pointer.
4. Cut each decision's `Alternatives considered (and rejected):` block; replace
   with the per-decision pointer line.
5. Rename the three decision headings whose text is falsified or is process
   provenance, sweeping every in-page anchor in the same edit.
6. Apply the factual corrections F3-F8 and F-minor across all five contract homes.
7. Rebuild both link-definition blocks; verify every def target and anchor.
8. Run the gates and the residual sweeps.

### Test additions / updates

No test file is in this cohort's write set and none was added. The mechanical
checks this pass owns in place of tests are the gate runs and the three
residual-count sweeps recorded under `### Final verification`.

### Implementation discretion items

None delegated — there is no Worker 2 for this cohort. Two judgement calls this
pass made and is recording rather than delegating:

- **Three decision headings were renamed** (2, 7, 9). Renaming a heading strands
  every ordinal citation, so each rename swept its anchor across the spec in the
  same edit and the counts are recorded below. No document outside the spec
  carries an anchored link into spec-042 (verified:
  `grep -rn 'spec-042-debug_toolbar-0_0_14.md#' docs/ KANBAN.md` returns nothing),
  so the sweep is complete at the pair.
- **`## Current state` bullets were graded clause by clause,** not bullet by
  bullet, per `BUILD.md` `### `## Current state`: observations stand, predictions
  do not`. Two bullets there are falsified observations and stay; one carried a
  prediction in its last clause and that clause alone was rewritten.

### Dispatched findings checklist

One box per finding the plan's `## Verified finding list` dispatches to Cohort A,
quoting the finding as the plan stated it and citing the symbol-qualified path the
verification pass recorded. Every one was independently re-derived before being
acted on; the re-derivation evidence is under `### Finding re-derivation` below.

- [x] **F1** — "the `-rationale.md` companion does not exist". `docs/SPECS/appx/`
      carried `spec-042-debug_toolbar-0_0_14-terms.csv` and no `-rationale.md`.
- [x] **F2** — "the spec narrates its own history in nine inline revisions".
      `docs/SPECS/spec-042-debug_toolbar-0_0_14.md` #"Revision history (kept inline so
      the spec is self-contained)", Revisions 1-9, ≈210 lines, Revision 9 a
      supersession note.
- [x] **F3** — "`tests/middleware/debug_toolbar_urls.py` is named as a shipped
      file; it does not exist". `ls tests/middleware/` → `__init__.py`,
      `test_debug_toolbar.py` only.
- [x] **F4** — "the spec says fakeshop ships no toolbar; fakeshop wires it".
      `examples/fakeshop/config/settings.py` and
      `examples/fakeshop/config/urls.py` #"urlpatterns += debug_toolbar_urls()".
- [x] **F5** — "Decision 7's load-bearing premise 'the package ships no view
      class' is false".
      `django_strawberry_framework/views.py::DjangoGraphQLView` and
      `django_strawberry_framework/views.py::AsyncDjangoGraphQLView` ship; the
      detection still resolves.
- [x] **F6** — "the Strawberry floor the spec names is stale". `>=0.262.0` /
      `==0.262.0` at four sites against `pyproject.toml` #"strawberry-graphql>=0.316.0".
- [x] **F7** — "three post-ship Python hardenings are absent from the spec".
      `django_strawberry_framework/middleware/debug_toolbar.py::_get_payload`
      #"except (json.JSONDecodeError, LookupError, UnicodeError):" and the
      `Content-Encoding` bail in
      `django_strawberry_framework/middleware/debug_toolbar.py::DebugToolbarMiddleware._postprocess`.
- [x] **F8** — "the template carries two post-ship divergence families the spec
      does not record".
      `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
      #"function getDjDebug()" and the per-node null guards.
- [x] **F-minor (a)** — "`## Out of scope` says 'this card's tests use
      `django.test.Client` directly'"; the live tier posts through
      `django_strawberry_framework.testing::TestClient`.
- [x] **F-minor (b)** — "the spec's ship-time `Status:` line and opener describe a
      two-slice build that has since been extended by four post-ship commits".

### Finding re-derivation

Worker 0's verification was re-run rather than accepted. Commands and results:

- **F1** — `ls docs/SPECS/appx/ | grep 042` → the CSV only. Confirmed.
- **F2** — the block ran from the `Revision history` line to `## Key glossary
  references`, 18,467 characters, Revisions 1-9 present. Confirmed.
- **F3** — `ls tests/middleware/` → `__init__.py`, `__pycache__`,
  `test_debug_toolbar.py`. `git log --diff-filter=D -- tests/middleware/debug_toolbar_urls.py`
  → deleted in `4015442d`. Confirmed.
- **F4** — `grep -n 'debug_toolbar\|INTERNAL_IPS' examples/fakeshop/config/settings.py`
  → the app at line 70, the package middleware dotted path at line 94,
  `INTERNAL_IPS = ["127.0.0.1"]` at line 113; `config/urls.py` line 3 imports
  `debug_toolbar_urls`, line 86 appends it.
  `examples/fakeshop/test_query/test_debug_toolbar_api.py` exists and carries
  `TestToolbarPresent`. Confirmed.
- **F5** — `views.py` declares
  `class DjangoGraphQLView(_RequestBodyBoundaryMixin, GraphQLView)` and
  `class AsyncDjangoGraphQLView(_RequestBodyBoundaryMixin, AsyncGraphQLView)`,
  importing both bases from `strawberry.django.views`; the installed
  `strawberry/django/views.py` declares `class BaseView` and both `GraphQLView` /
  `AsyncGraphQLView` beneath it; `config/urls.py` mounts
  `DjangoGraphQLView.as_view(...)` under `ensure_csrf_cookie`. So
  `issubclass(view, BaseView)` resolves for the package's own view — **the
  detection works, unchanged, and that is what the spec now states.** Confirmed,
  including the part Worker 0 flagged as the substantive point.
- **F6** — `pyproject.toml` declares `requires-python = ">=3.10,<4.0"`,
  `"Django>=5.2.16"`, `"strawberry-graphql>=0.316.0"`. Cross-read against
  `BUILD.md` `## Floor verification`, which is the single canonical statement of
  the floor (Django 5.2.16 / Python 3.10 / strawberry-graphql 0.316.0) and which
  the declared dependency floor matches. Confirmed — and the fix deliberately
  states the obligation rather than a replacement number.
- **F7** — both guards read in the shipped module; the pinning tests
  (`test_encoded_response_gets_no_package_mutation`,
  `test_malformed_json_body_gets_no_package_rewrite`) are parametrized in
  `tests/middleware/test_debug_toolbar.py`. Commit attribution re-derived with
  `git log -S`: `Content-Encoding` → `9c868016`, the decode/parse bail →
  `6fa696af`. Confirmed.
- **F8** — the template's `getDjDebug()` shadow-root resolution and the
  `panelTitle` / `heading` / `scroll` / `panelContent` / `subtitle` null guards
  read in the shipped asset; `git log -S` attributes them to `312d4121` and
  `ac69acf5`. Confirmed.
- **F-minor** — `test_debug_toolbar_api.py` imports
  `from django_strawberry_framework.testing import TestClient` and posts via
  `TestClient(client=client).query(`. Confirmed.

**One correction to the finding list, and it is a widening rather than a
disagreement.** F7 names the `_get_payload` change as a "decode/parse bail"
distinct from the spec's "narrower non-object-body guard". Reading the shipped
`_get_payload` shows the three guards are **one family** — undecodable bytes,
unparseable text, non-object body — reached through a `try` and an `isinstance`
check that together answer one question. The spec now records them as one
response-shape divergence rather than two, which is also what makes the module's
divergence count three rather than four. Nothing in F7's evidence is contradicted.

---

## Build report (Worker 1, custodian pass)

### Files touched

- `docs/SPECS/appx/spec-042-debug_toolbar-0_0_14-rationale.md` (new, 50,563 bytes)
  — the deliberative layer, moved.
- `docs/SPECS/spec-042-debug_toolbar-0_0_14.md` — 179,809 → 151,018 bytes
  (−28,791). The spec lost more than the rationale gained because prose the
  current decisions had falsified was **deleted rather than moved**
  (`worker-1.md` `### Performing the rationale move`, rule 2), and because the
  round-provenance labels the moved text carried (`Rev 7`, `Rev 8`, `P2.1`-`P2.4`,
  `Revision 5`) have no home in either file.
- `docs/builder/bld-042-review-1-spec_reconciliation.md` (this file, new).
- `docs/builder/worker-memory/042-worker-1.md` — one appended entry.

### The rationale move, as performed

A cut-and-paste. What moved, by block:

- **`Revision history` (Revisions 1-9, 18,467 characters)** — restructured, not
  transcribed. `## Round vocabulary` names the nine once, distinguishing the eight
  pre-implementation review passes from Revision 9, which was a **post-ship
  maintainer change** rather than a review round. The per-revision content was
  redistributed into the `Change record` block of the decision it changed.
  Revision 9's supersession note is discharged outright: its instruction to
  reinterpret text the spec still carried is exactly the shape `BUILD.md` forbids,
  so its content became spec corrections (F3, F4) and its record became two
  post-ship-correction entries.
- **Ten `Alternatives considered (and rejected):` blocks (~11,524 characters)** —
  every rejected alternative and its reason, under the decision it belongs to.
  Each decision keeps a one-line pointer, so a reviewer can see that deliberation
  exists (`worker-1.md` rule 1).
- **Four `Justification:` / derivation paragraphs** — Decision 2's card-body
  appeal, Decision 3's spec-041 identity-mechanics contrast, Decision 5's PyPI
  floor derivation, Decision 8's name-based-vs-content-based argument, Decision
  10's NEXT.md appeal.
- **The `## Risks and open questions` preferred-answer / fallback weighing** —
  every risk's two-branch deliberation. The constraints themselves stayed; the
  section now opens with a pointer and six live constraints stated flatly.
- **The `## Borrowing posture` template-port chronology** — the Revision 7/8
  narrative of how the guard family grew. The checklist and the six diverged forms
  stayed: Test 16 pins them, so they are a live contract and were graded clause by
  clause rather than moved as a block.

What **stayed** despite reading like deliberation, and why (the carve-out
`worker-1.md` calls the one place this move can itself cause a defect): Decision
5's guard-before-imports ordering, Decision 6's `super()._postprocess(...)`-first
ordering with its account of what the stock method does in that order, Decision
9's `DEBUG=True` and URL-reload ordering, the `Content-Length`-only-when-present
reasoning, and the Test-plan note that a non-null `operationName` needs a *named*
operation document. Each is an instruction whose absence makes a builder write the
wrong thing. The rationale's `## How to read this file` names them, so the next
custodian does not "finish the job" by moving them.

Every rationale entry names the spec decision it belongs to by heading and anchor,
including the two non-decision sections, which get their own entries under
`## Non-decision entries` rather than being filed nowhere.

### Spec changes made (Worker 1 only)

Each entry cites the spec text, the reason, and the finding that triggered it.
Every correction states the **corrected contract directly** — no amendment block,
no "previously", no "as of Revision N" (`AGENTS.md` rule 27).

1. **`Status:` line** — was "both slices built and the card-wrap landed"; now
   states the current truth including the post-card extension (the example's
   toolbar wiring and live-tier tests, the middleware's `Content-Encoding` and
   response-shape bails, the template's shadow-DOM resolution and per-node
   guards). *F-minor (b).* Checkboxes left unticked by convention.
2. **`Revision history` block → one-line rationale pointer.** *F1, F2.*
3. **Ten `Alternatives considered (and rejected):` blocks → one pointer line
   each,** `[rationale-d1]`…`[rationale-d10]`. *F1.*
4. **Decision 1** — "This spec lives at `docs/spec-042-…`" was false about the
   archived location; now names the stem and the archived paths of all three
   files. *Not in the finding list — see `### Notes`.*
5. **Decision 2** — heading rewritten (the "fakeshop settings opt-in" clause
   dropped), "Four adjacent-looking pieces" → "Three", the whole
   fakeshop-opt-in bullet deleted, the tested-contract clause reworded off
   "fakeshop's `GraphQLView`", the `Justification:` paragraph moved. *F4, F5.*
   Anchor swept at **5** sites.
6. **Decision 3** — the spec-041 identity-mechanics contrast moved; the decision
   now states the naming rule directly. *F1.*
7. **Decision 4** — the test-locations paragraph now describes the two-tree split
   and names the live-tier file. *F3, F4.*
8. **Decision 5** — item 2's spec-041 quotation condensed to the normative
   decision rule; item 3's PyPI floor derivation moved, the single-floor
   obligation kept. *F1.*
9. **Decision 6** — the divergence count is now **three**; a new `_postprocess`
   step records the `Content-Encoding` early-out with its ordering consequence;
   `_get_payload`'s bail is stated as the response-shape family (undecodable /
   unparseable / non-object) with the guard-the-answer reasoning that makes it one
   guard rather than three special cases. *F7.*
10. **Decision 7** — heading rewritten (the `DjangoGraphQLView`-hedge clause
    dropped); the "the package ships no view class" opener replaced by the
    engine-owned-target contract plus a new paragraph stating that the package's
    own `views.py` views are covered by the same one line, because they subclass
    Strawberry's views; the `0.262.0` floor replaced by the read-at-gate-time
    obligation; the divergence list updated. *F5, F6, F7, F8.* Anchor swept at
    **10** sites.
11. **Decision 8** — the name-based-vs-content-based deliberation moved; the
    contract statement kept. *F1.*
12. **Decision 9** — heading rewritten and the body rewritten end to end (11,854
    → 9,090 characters): the two-tier split stated directly, the `DEBUG=True` +
    `config.urls`-reload fixture contract replacing the four-override fixture and
    the deleted test URLconf, the cache-hygiene contract kept verbatim as a live
    obligation, the schema-reload obligation restated as inherited from the live
    suites, and the package-tier leaf-import ordering obligation added. *F3, F4.*
    Anchor swept at **10** sites.
13. **Decision 10** — the NEXT.md `Justification:` paragraph moved. *F1.*
14. **`## Key glossary references`** — the Live-first, Schema-reload and
    `TestClient` bullets rewritten; the `Revision 5` label dropped from the
    Eviction bullet. *F3, F4, F-minor (a).*
15. **`## Slice checklist`** — the view-class-gate box now names the
    read-at-gate-time floor obligation; the test box now describes both tiers and
    the current fixture. *F3, F4, F6.*
16. **`## Current state`** — the fakeshop bullet's **prediction** clause ("and
    this card deliberately keeps it that way") rewritten; its **observation**
    clause kept and dated. The "package ships no view class" bullet **stays** as a
    dated observation, with its trailing pointer reworded so it no longer implies
    the package will never ship one. *F4, F5, graded per `BUILD.md`.*
17. **`## Goals` Goal 4** — the live tier's vehicle corrected to `TestClient`.
    *F-minor (a).*
18. **`## Non-goals`** — the "Wiring the toolbar into fakeshop's shipped settings"
    bullet deleted (it is no longer a non-goal); the "A package view class" bullet
    rewritten to the claim that survives: no view is shipped **for detection's
    sake**, and the package's own views are covered for free. *F4, F5.*
19. **`## Borrowing posture`** — `_get_payload`'s description widened to the
    response-shape family; the deltas sentence now says three Python divergences;
    the template family grown from four to **six** with the shadow-DOM resolution
    and the per-node guards written as the same rule, and the `(Rev 7)` / `(Rev 8)`
    labels dropped. *F7, F8.*
20. **`## Implementation plan` file table** — the `debug_toolbar_urls.py` row
    deleted; the tests row split into package-tier and live-tier rows; a new row
    for the example's own toolbar wiring. *F3, F4.*
21. **`## Helper-reuse obligations` D3** — the `Revision 5` label dropped. *F2.*
22. **`## Edge cases and constraints`** — two new bullets (the encoded-body skip
    with its middleware-ordering consequence; the unreadable declared-JSON
    response); the show-toolbar-gating bullet now records that the example's
    shipped wiring is inert under `DEBUG=False`; the `loadscope` bullet rewritten
    off the `INSTALLED_APPS` override onto the toolbar's process caches and the
    reloaded URLconf. *F4, F7.*
23. **`## Test plan`** — header rewritten for the two tiers; Test 2 recast as the
    inert-under-shipped-settings baseline; Test 6's routes attributed to
    fakeshop's own `config.urls`; Test 7's positive-direction note now records
    that the mount is the package's own view; Test 8 recast as the package-tier
    `RequestFactory` unit with the reason it cannot be live; two new units (13a
    encoded-body early-out, 14b undecodable/unparseable body); Test 11b gains the
    inverse first-import obligation; Test 16 extended to the six diverged forms;
    the coverage paragraph re-owned per tier. *F3, F4, F7, F8.*
24. **`## Doc updates`** — the TREE row now names both tiers. *F4.*
25. **`## Risks and open questions`** — rewritten to six live constraints with the
    preferred/fallback weighing moved; the floor bullet replaced by the
    read-never-restate obligation; the closed view-detection hedge removed from
    the live list. *F5, F6.*
26. **`## Out of scope`** — the `TestClient` bullet corrected (this card consumes
    it, does not build it); the fakeshop-dogfooding bullet deleted, its subject
    having landed. *F4, F-minor (a).*
27. **`## Definition of done`** — the URLconf item rewritten to the example's own
    wiring plus the `DEBUG`-only override; the Strawberry-gate item's `0.262.0`
    replaced by the read-at-gate-time obligation; the test item split per tier and
    extended with the new units; the template item now names the six guard
    divergences. *F3, F4, F6, F7, F8.*
28. **Link-definition block** — added `[rationale]`, `[rationale-d1..d10]`,
    `[rationale-risks]`, `[build]`, `[views]`, `[spec-043]`; removed three defs
    left with no use (`[debug-toolbar-pypi]` and `[tests-conftest]`, whose uses
    moved to the rationale; `[test-routers]`, which was already orphaned at HEAD);
    sorted the `<!-- External -->` group, which was unsorted at HEAD.

### Deferral reasons

None. Every dispatched box landed; there is nothing left `- [ ]`.

### Failability proofs

Not applicable; this pass introduced no boundary, guard, gate, or rejection path —
it writes no executable code. The mechanical equivalents this pass does owe (gate
runs, residual sweeps, anchor and link verification) are recorded under
`### Final verification`.

### Hot-path budget

Not applicable; the plan declares no hot path, and this cohort changes no
per-request / per-resolver / per-row path.

### Floor verification

Not applicable; the plan declares floor-verification scope `none`, and this cohort
changes no Django / Strawberry / channels integration seam. **F6 is not an
exception to that declaration:** discharging it is a spec-text correction that
*removes* a version number from the spec, so there is nothing to re-run at a
floor. The floor facts this pass needed were read from `BUILD.md`
`## Floor verification` and `pyproject.toml`, never from memory.

---

## Final verification (Worker 1)

### Gates

| Gate | Command | Result |
| --- | --- | --- |
| Spec glossary | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-042-debug_toolbar-0_0_14.md` | `OK: 24 terms - all have glossary entries and at least one spec link.` |
| Citations | `uv run python scripts/check_citations.py` | `OK: 991 citations resolve (822 in 441 .py files, 169 in KANBAN.md).` |
| Source layout | `uv run python scripts/check_trailing_commas.py --check <the two files>` | exit 0 |
| Whitespace | `git diff --check -- docs/SPECS/spec-042-debug_toolbar-0_0_14.md` | clean |

The glossary gate still reads 24 terms after an edit that removed ~29KB of spec
prose, which is the one thing it can prove here: no term lost its last inline
mention. Its input is term + anchor only, so it says nothing about the surrounding
notes — the reason the `## Key glossary references` bullets were re-read by hand
rather than trusted to the green.

`check_citations.py` is `path::Symbol`-only and scopes itself to first-party `.py`
files and `KANBAN.md`, so **it reads neither file this pass wrote.** Its green is
evidence that nothing this pass did rotted a citation elsewhere, not that the new
citations resolve. Those were verified by a separate script that parses both files
for the `AGENTS.md` rule-27 forms and checks each against the tree: **10
`path::Symbol` citations and 4 `path #"substring"` citations, all resolving; 0
`path:NN` forms; 0 citations wrapped across lines; 0 `#"…"` substrings containing
an inner double quote** (the last check caught a real defect — a
`#"if response.get("Content-Encoding", ""):"` citation whose nested quotes make it
unparseable — which was rewritten as a symbol-only citation).

### Link convention

A verifier parsed both files (fenced blocks and code spans stripped first) and
checked: in-page anchors against slugs computed from the files' own headings;
every `][label]` against a def; every def against a use; every def target against
disk, including the fragment against the target file's headings; and alphabetical
order within each group.

| Check | Spec | Rationale |
| --- | --- | --- |
| Broken in-page anchors | none | none |
| Undefined refs | none | none |
| Orphan defs | none | none |
| Missing def targets | none | none |
| Broken cross-file anchors | none | none |
| Unsorted groups | none | none |
| Ten canonical group headers present | yes | yes |

Both files carry all ten headers in order, empty ones included. The
disk-exists check alone is fail-open on depth rot (`START.md`: a same-named file
one level up masks it), so each def's **group header and label** were read against
its intended target as well — this is what the cross-file-anchor column adds:
every `[rationale-dN]` fragment was resolved against the rationale's actual
headings rather than assumed from the heading text.

### Residual-claim sweeps

`START.md` "Partial claim fix = dominant residual defect": the shortest
**distinctive** phrase, counting occurrences rather than lines, proving retirement
is zero.

| Claim | Instrument | Spec | Rationale |
| --- | --- | --- | --- |
| the deleted test URLconf | `debug_toolbar_urls\.py` | **0** | 1 (recorded as retired) |
| " | `middleware\.debug_toolbar_urls` | **0** | 0 |
| " | `middleware/debug_toolbar_urls` | **0** | 0 |
| " | `test URLconf` | **0** | — |
| the stale Strawberry floor | `0\.262\.0` | **0** | 4 (recorded as stale) |
| the four-guard template family | `four-guard` / `in four spots` | **0** | — |
| the two-divergence ledger | `No other Python behavior differs` | **0** | quoted once as retired |
| the live tier's old vehicle | `use .django\.test\.Client. directly` | **0** | — |
| revision narration | `Revision [0-9]` / `(Rev [0-9]` | **0** | the round vocabulary only |
| round-label provenance | `P2\.[0-9]` / `P1 ` / `P3 ` | **0** | — |
| the old Decision 9 anchor | `decision-9--test-strategy-package-tests` | **0** | — |

Three instruments were used for the test-URLconf population rather than one,
because `debug_toolbar_urls` is a **live** function name in this spec as well as
the dead module's stem — a single grep on the shared token would have counted the
legitimate `debug_toolbar_urls()` calls and read as a failed retirement. The
dotted form, the path form and the `.py` form together isolate the module.

The rationale's four `0.262.0` occurrences and its one `debug_toolbar_urls.py` are
**intended**: each sits inside a sentence declaring the claim stale, which is the
file's whole job. A later custodian sweeping this population should expect them.

### Anchor-rename sweeps

Three headings were renamed; each rename's in-page anchor was swept in the same
edit, with the pre-edit occurrence count asserted before replacement:

| Decision | Heading occurrences | Anchor references swept |
| --- | --- | --- |
| 2 | 1 | 5 |
| 7 | 1 | 10 |
| 9 | 1 | 10 |

No document outside the spec carries an anchored link into spec-042
(`grep -rn 'spec-042-debug_toolbar-0_0_14.md#' docs/ KANBAN.md` → no matches), so
the rename population is closed at this pair. **Prose** citations of spec-042 do
exist in siblings — `spec-043` cites "spec-042 Revision 8" three times for the
shipped-spec closeout convention it settled — which is why `## Round vocabulary`
preserves the Revision 1-9 names in the rationale rather than discarding them;
those three citations still resolve, to the rationale.

### Archive state

All three files are present at their canonical paths:

- `docs/SPECS/spec-042-debug_toolbar-0_0_14.md` — 151,018 bytes
- `docs/SPECS/appx/spec-042-debug_toolbar-0_0_14-terms.csv` — 6,987 bytes,
  untouched by this pass (out of scope; the glossary gate passes against it)
- `docs/SPECS/appx/spec-042-debug_toolbar-0_0_14-rationale.md` — 50,563 bytes, new

The rationale landing beside the CSV under `docs/SPECS/appx/` is what completes
the archive; the spec's link-definition block still resolves from `docs/SPECS/`
(every `[ref]: path` target exists on disk, with its group header and label
checked against the intended target, per the table above).

### Spec slice checklist audit

Not applicable — a review round has no spec `## Slice checklist` to audit
(`BUILD.md` `### Dispatched findings checklist` replaces it, audited above). The
spec's own slice checklist and Definition-of-done boxes stay **unticked**: the
`Status:` line is the completion source of truth and this repo's shipped-card
closeout convention leaves the boxes alone. Their **text** was corrected where it
made a false completion claim, which is a different thing and is what a checklist
box gets no vintage licence for.

### Final status

`final-accepted`. Every dispatched finding is discharged, every gate is green, and
no residual claim survives.

### Summary

spec-042's deliberative layer now lives in
`docs/SPECS/appx/spec-042-debug_toolbar-0_0_14-rationale.md` — nine revisions
restructured into per-decision change records, ten blocks of rejected
alternatives, four derivation paragraphs, and the risks' preferred/fallback
weighing — and the spec reads as a clean current contract 28,791 bytes lighter,
with every falsified statement rewritten to state the corrected contract directly
across all five homes. The card's archive is complete for the first time.

---

## Notes for Worker 1 (spec reconciliation)

Items for Worker 0 to route. Nothing here blocks this cohort's `final-accepted`.

1. **The module docstring understates the divergence ledger the same way the spec
   did — and this cohort cannot fix it.**
   `django_strawberry_framework/middleware/debug_toolbar.py` enumerates the
   `process_view` guard and the `_get_payload` bails as "two narrow, deliberate
   robustness divergences" and closes "No other Python behavior differs", which
   the `Content-Encoding` bail (commit `9c868016`) falsifies. The spec now says
   three; the docstring still says two. It is a `.py` file, so it is Cohort B's
   surface or a Cohort C fix, not Cohort A's. **This is the finding the plan's
   list missed:** F7 treated the docstring as already correct ("The module
   docstring already states both correctly; only the **spec** is behind"), and it
   is correct only about the two it enumerates.
2. **Decision 1 carried a location claim outside the finding list.** It read "This
   spec lives at `docs/spec-042-debug_toolbar-0_0_14.md`" — true when authored,
   false since the spec was archived. Corrected in this pass to name the stem plus
   the archived paths of all three companion files. Flagged because every archived
   spec whose Decision 1 uses this template carries the same sentence, so the
   population is larger than this card: a custodian closing the next cycle should
   sweep `docs/SPECS/` for `This spec lives at \`docs/spec-` before assuming it is
   a one-off. This pass did not sweep it — those files are outside this cohort's
   write set.
3. **`docs/GLOSSARY.md`'s `Debug-toolbar middleware` entry was not read against
   the corrections.** The maintainer fenced this cycle to spec files and package
   `.py` files, and the glossary is DB-backed in any case (a hand-edit is reverted
   by the next render). The entry body carries the same contract this spec states
   — the fakeshop wiring, the test placement, the divergence ledger — so it is a
   plausible carrier of the same staleness. Routing rather than touching it.
4. **The spec's `<!-- External -->` link group was unsorted at HEAD.** Sorted in
   this pass since the file is in this cohort's write set. Recorded so it is not
   read as an unexplained diff hunk.
5. **Cohort B's artifact exists on disk and was deliberately not read.**
   `docs/builder/bld-042-review-2-code_verification.md` is untracked in the tree.
   The plan routes Cohort B's verdict to Cohort A through Worker 0, and the
   cohorts run concurrently, so reading a possibly mid-pass artifact would be
   exactly the cross-cohort chatter the partition exists to prevent. **If Cohort B
   raises a finding that needs spec text, this cohort has not seen it** and a
   further custodian pass is owed.
6. **Nothing is deferred from the dispatched list.** F1-F8 and both F-minor halves
   are discharged in full.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
