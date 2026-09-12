# Package build plan: debug_toolbar / 0.0.14 (042) — post-ship reconciliation cycle

Spec source: `docs/SPECS/spec-042-debug_toolbar-0_0_14.md` (already archived; see
`## Cycle framing` for why the path is `docs/SPECS/` rather than `docs/`)
Target release: `0.0.14` (shipped; card `DONE-042-0.0.14`)
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every slice must justify shared/duplicated patterns before merging.
Ownership partition: **declared, two concurrent cohorts** — see `## Ownership partition`.
Hot-path declaration: **none** — verdict unchanged, **warrant rewritten**
mid-cycle. The original warrant read "the code cohort is review-only", which the
maintainer's own fence widening falsified the moment Cohort C was authorized to
edit production source (Worker 3 pass 3, L5-3). The honest warrant: Cohort C's
Python change is docstring- and comment-only, proved by AST identity with
docstrings stripped against HEAD, and its executable change is **browser-side
JavaScript** — a per-panel `CSS.escape` call and a record-predicate check inside
a patched `JSON.parse`, on a page that only renders when the dev-gated toolbar is
active. `BUILD.md` `## Hot-path budget` asks for a before/after **number**, and
no instrument in this repository can produce one for a browser asset: the suite
has no JS runtime at all (`### Deferred work catalog` carries that question to
the maintainer). So `none` here means *below the threshold that owes a number*,
on magnitude and on the dev-only gate — **not** "no executable code changed".
Recording the distinction because a silent `none` resting on a false reason is
indistinguishable from a considered one.
Floor-verification scope: **none.** No cohort changes a Django / Strawberry /
channels integration seam. (The spec's own ship-time floor obligation is a
finding in this cycle — F6 — but discharging it is a *spec text* correction, not
a re-run: the floor number the spec names is stale relative to
`pyproject.toml`.)
Pre-flight: passed on 2026-09-11 with two recorded deviations (steps 3 and 5,
below); baseline: 53 files dirty from a concurrent session, **none** of them in
this cycle's scope.

## Cycle framing

This is **not** a fresh spec build. Card `DONE-042-0.0.14` shipped; the
middleware, the template asset, and both test tiers are on `main`. The
maintainer's dispatch scopes this cycle to four obligations the original build
left open or that later work falsified:

1. The spec's `-rationale.md` companion was **never created**. Every other
   shipped spec from 040 onward has one under `docs/SPECS/appx/`; spec-042 has
   only its `-terms.csv`. `BUILD.md` `## Spec rationale extraction` makes the
   move the first substantive action of a build, so this cycle owes the move
   retroactively.
2. The spec must be reconciled with **what actually landed** — including
   post-ship commits that corrected or extended the shipped contract.
3. The code must be verified for **skipped or dropped spec contract** —
   anything the spec promised that never landed.
4. Explanations of what changed and why go in the **rationale file, never the
   spec**. The spec reads as a clean current contract
   (`BUILD.md` `## Spec rationale extraction`, "The spec stays the heart, and it
   never narrates its own history").

Modelled on `BUILD.md` `## Review rounds`: the input is already-built work, the
maintainer's dispatch is the review document, and Worker 0 verified every
finding against source before dispatch (`### Worker 0 verifies every finding
against source before dispatching`). The verified findings are the
`## Verified finding list` below; each cohort's artifact carries them as its
`### Dispatched findings checklist`.

**Scope fence (maintainer-set, binding on every cohort):** this cycle touches
**spec files (`docs/SPECS/spec-042-*.md` + its `docs/SPECS/appx/` companions)
and package source only.** No `docs/GLOSSARY.md`, no `docs/README.md`, no
`docs/TREE.md`, no `KANBAN.md` / `KANBAN.html`, no
`examples/fakeshop/db.sqlite3`, no closeout / agentflow-doc edits.

**Amended mid-cycle (see `## Maintainer decisions taken mid-cycle` item 1):**
"package source" was originally written "package `.py` source". The maintainer
widened it by exactly one file — the shipped bridge asset
`django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
— after a research pass established that no board card owns the defect found in
it and that the repo's own tracked-path constants count the asset as package
source. Nothing else moved.

## Pre-flight deviations (both maintainer-authorized)

- **Step 3 (artifact reset) — deliberately NOT run.** `docs/builder/` carries a
  **live** cycle for spec-050 (`build-050-list_field_arguments-0_0_15.md`,
  `bld-slice-1..5`, `bld-integration.md`, `bld-final.md`). Deleting them is the
  one irreversible pre-flight mistake (`worker-0.md` step 3) and the maintainer
  directed this cycle to ignore concurrent work. **Every artifact this cycle
  creates carries `042` in its filename**, so no path collides with the live
  cycle. Verified: no `build-042-*` or `bld-042-*` path existed before this plan.
- **Step 5 (scratch clear) — deliberately NOT run,** same reason:
  `docs/builder/worker-memory/` and `docs/builder/temp-tests/` belong to the
  live spec-050 cycle. This cycle seeds its own `042-worker-<N>.md` memory
  files instead of overwriting `worker-<N>.md`.

Steps 1, 2, 4, 6 passed as written:

- Step 1 — `git status --short`: 53 dirty paths, **zero** in this cycle's scope
  (no `spec-042`, no `middleware/`, no `debug_toolbar` path is dirty). Treated
  as baseline-dirty out-of-scope per `AGENTS.md` rule 34.
- Step 2 — `uv run python scripts/review_inspect.py
  django_strawberry_framework/middleware/debug_toolbar.py --output-dir
  docs/shadow` exited 0 and wrote both outputs.
- Step 4 — `.gitignore` lists `docs/shadow/`, `docs/builder/worker-memory/`,
  `docs/builder/temp-tests/`.
- Step 6 — `uv run python scripts/check_spec_glossary.py --spec
  docs/SPECS/spec-042-debug_toolbar-0_0_14.md` → `OK: 24 terms`.
- Step 7 — the rationale extraction is this cycle's Cohort A deliverable, not a
  gate it can pass beforehand.

## Baseline-dirty out-of-scope files

The dirty paths are a concurrent session's spec-050 work (`connection.py`,
`list_field.py`, `orders/sets.py`, `utils/querysets.py`, the `docs/builder/bld-*`
artifacts, the fakeshop live-tier test files, `examples/fakeshop/db.sqlite3`,
`docs/GLOSSARY.md`, `docs/TREE.md`, and the test trees). **Never edit, never
revert.** Diff against `git show HEAD:<path>` if a comparison is needed.

**This set is a moving target, and the figure below is a reading, not a
constant.** At pre-flight it was **53 paths**; Worker 2 flagged mid-build that it
had grown, and at the Cohort C review dispatch it measures **73** — the
concurrent session added `keyset.py`, `resource_policy.py`,
`types/finalizer.py`, `docs/GLOSSARY.md`, `docs/TREE.md` and several live-tier
test files while this cycle ran. Recorded per `BUILD.md` `### Tracked binary /
generated files: churn and concurrent-writer handling` so no later pass mistakes
that churn for this build's output. The rule this figure exists to serve is
unchanged whatever it reads: **attribute a dirty file by DIFF CONTENT, not by a
count** (`START.md` #"Attribute dirty files by DIFF CONTENT"). Cohort C's three
code files are the only paths in this cycle's write set that are dirty as
package source, and all three were byte-clean at HEAD when Worker 2 began.

## Ownership partition

Cohorts A and B have provably disjoint write sets and were dispatched
**concurrently** (`BUILD.md` `### Parallel cohorts under a declared ownership
partition`). Cohort C was added mid-cycle and runs **sequentially, after both** —
it re-opens the spec and the rationale, which Cohort A owned, so it could never
have run beside A. One shared file is enough to serialize (`BUILD.md`: "Any file
owned by two cohorts serializes them"), and here the overlap is deliberate: C's
planner is the same role that wrote A's spec text and is amending its own work.

| Cohort | Worker | Writes (exclusively) |
| --- | --- | --- |
| **A — spec custody** | Worker 1 | `docs/SPECS/spec-042-debug_toolbar-0_0_14.md`; `docs/SPECS/appx/spec-042-debug_toolbar-0_0_14-rationale.md` (new); `docs/builder/bld-042-review-1-spec_reconciliation.md`; `docs/builder/worker-memory/042-worker-1.md` |
| **B — code verification** | Worker 3 | `docs/builder/bld-042-review-2-code_verification.md`; `docs/builder/worker-memory/042-worker-3.md`; `docs/builder/temp-tests/042/` (scratch only) |
| **C — code fix** (dispatched after B's `revision-needed`) | Worker 1 plans + amends the spec; Worker 2 builds; Worker 3 reviews | `docs/builder/bld-042-review-3-code_fix.md`; `django_strawberry_framework/middleware/debug_toolbar.py`; `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`; `tests/middleware/test_debug_toolbar.py`; `docs/SPECS/spec-042-debug_toolbar-0_0_14.md` + its `-rationale.md` (Worker 1 only); `docs/builder/worker-memory/042-worker-{1,2,3}.md`; `docs/builder/temp-tests/042/` |

No file appears in both **A** and **B**. Cohort B is **review-only**: it reads
`django_strawberry_framework/middleware/debug_toolbar.py`, the template asset,
and both test tiers, and writes no source. Its verdict is what dispatched
Cohort C. Within Cohort C the roles keep their own separation —
`### Isolation is non-waivable`: Worker 1 plans and owns the spec but writes no
source; Worker 2 writes the source and tests; Worker 3 reviews and writes
neither.

Cohort A does not consume Cohort B's surface *and vice versa* — but Cohort B's
verdict **can** add findings to Cohort A's spec work, which is why Cohort A's
final verification runs after Cohort B returns (`## Checklist` ordering).

## Verified finding list

Every finding below was verified against source by Worker 0 before dispatch,
with the symbol-qualified path recorded. Cohort A owns F1–F8; Cohort B owns V1–V4.

### F1 — the `-rationale.md` companion does not exist

`docs/SPECS/appx/` carries `spec-042-debug_toolbar-0_0_14-terms.csv` and **no**
`-rationale.md`. Specs 040, 041, 044–048 all carry both. **Verified:** `ls
docs/SPECS/appx/ | grep 042` returns the CSV only.

### F2 — the spec narrates its own history in nine inline revisions

`docs/SPECS/spec-042-debug_toolbar-0_0_14.md` #"Revision history (kept inline so
the spec is self-contained)" runs Revisions 1–9 (≈210 lines). `BUILD.md`
`## Spec rationale extraction` is explicit that the deliberative layer — what
changed, when, why, and what was rejected — belongs in the rationale file, and
that the spec must read as a clean current contract with no chronology to apply.
Revision 9 in particular is a *supersession note* instructing the reader to
reinterpret text the spec still carries uncorrected; that is precisely the shape
the rule forbids.

### F3 — `tests/middleware/debug_toolbar_urls.py` is named as a shipped file; it does not exist

**Verified:** `ls tests/middleware/` → `__init__.py`, `test_debug_toolbar.py`
only. Revision 9 records the deletion, but the spec body still names the module
as shipped in **nine** places: the Slice-1 checklist, the
`## Implementation plan` file table (its own row), Decision 9's fixture contract
(two spots), the `## Test plan` fixture paragraph, Test 8, and the
`## Definition of done`. The contract halves therefore disagree with each other
and with the tree.

### F4 — the spec says fakeshop ships no toolbar; fakeshop wires it

**Verified in `examples/fakeshop/config/settings.py`:** `"debug_toolbar"` in
`INSTALLED_APPS`,
`"django_strawberry_framework.middleware.debug_toolbar.DebugToolbarMiddleware"`
in `MIDDLEWARE`, `INTERNAL_IPS = ["127.0.0.1"]`; and in
`examples/fakeshop/config/urls.py`, `urlpatterns += debug_toolbar_urls()`.
Decision 2 scopes this OUT, `## Current state` asserts it, and Decision 9's
whole placement argument rests on it. Consequence: the toolbar-present tests
live at `examples/fakeshop/test_query/test_debug_toolbar_api.py` (live tier),
not in `tests/middleware/test_debug_toolbar.py` as the `## Test plan` header
states.

### F5 — Decision 7's load-bearing premise "the package ships no view class" is false

**Verified:** `django_strawberry_framework/views.py::DjangoGraphQLView` and
`::AsyncDjangoGraphQLView` ship (spec-046), and
`examples/fakeshop/config/urls.py` mounts `DjangoGraphQLView`. The spec asserts
the opposite at four sites (the opener, `## Current state`, `## Non-goals`,
Decision 7 itself) and rejects "Ship a package `DjangoGraphQLView` and detect
that" as an alternative.

**The detection still works, and that is the point worth stating:**
`DjangoGraphQLView(_RequestBodyBoundaryMixin, GraphQLView)` and
`strawberry/django/views.py::GraphQLView` subclasses `BaseView`, so
`issubclass(view, BaseView)` resolves for the package's own view. The
`## Risks and open questions` bullet that hedged "if a future card ships a
package view class, the one `issubclass` line is that card's to update"
**resolved to no update needed** — a fact the spec should state, not a change it
should hide.

### F6 — the Strawberry floor the spec names is stale

The spec names `strawberry-graphql>=0.262.0` / `==0.262.0` at **four** sites
(Slice-1 view-class gate, Decision 7, the Risks bullet, the DoD).
**Verified:** `pyproject.toml` now declares `"strawberry-graphql>=0.316.0"`.
The DoD item demanding a `0.262.0` throwaway-venv run is unsatisfiable against
the current floor and, per `BUILD.md` `## Floor verification`, the canonical
floor lives in `BUILD.md` / `pyproject.toml`, never restated from memory in a
spec.

### F7 — three post-ship Python hardenings are absent from the spec

All three are in the shipped module and pinned by tests; none appears in the
spec's divergence ledger (which still says "two narrow divergences" and "No
other Python behavior differs"):

- **`Content-Encoding` bail** —
  `django_strawberry_framework/middleware/debug_toolbar.py::DebugToolbarMiddleware._postprocess`
  #"if response.get("Content-Encoding", "")". Landed in `9c868016`. Pinned by
  `tests/middleware/test_debug_toolbar.py::test_encoded_response_gets_no_package_mutation`
  (parametrized).
- **`_get_payload` decode/parse bail** —
  `django_strawberry_framework/middleware/debug_toolbar.py::_get_payload`
  #"except (json.JSONDecodeError, LookupError, UnicodeError):". Landed in
  `6fa696af`; the spec only carries the narrower non-object-body guard. Pinned by
  `::test_malformed_json_body_gets_no_package_rewrite` (parametrized over
  `b"not json"` and `b"\xff"`).
- The module docstring already states both correctly; only the **spec** is behind.

### F8 — the template carries two post-ship divergence families the spec does not record

The spec's `## Borrowing posture` template-port checklist and Revision 7/8
record a "four-guard family". The shipped asset carries two more:

- **Shadow-DOM handle resolution** (`312d4121`) —
  `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
  #"function getDjDebug()". debug-toolbar ≥7 defaults `USE_SHADOW_DOM=True`, so
  the bare `document.getElementById("djDebug")` the port inherited returned
  `null` and every DOM update silently stopped. Nav lookups moved to
  `djDebug.querySelector(\`#djdt-${id}\`)`.
- **Per-node null guards on the panel render** (`ac69acf5`) — every nested
  `querySelector` result (`panelTitle`, `heading`, `scroll`, `panelContent`,
  `subtitle`) is null-checked before assignment; the previous chained form threw
  a `TypeError` inside the patched `JSON.parse` and blanked the toolbar.

Both are pinned by
`tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence`
(assertions 5a and 9).

### F-minor — two smaller spec/tree disagreements, verified

- `## Out of scope` says "this card's tests use `django.test.Client` directly";
  the live tier now posts through the package's own
  `django_strawberry_framework.testing::TestClient` (spec-043).
  **Verified:** `examples/fakeshop/test_query/test_debug_toolbar_api.py`
  #"TestClient(client=client).query(".
- The spec's ship-time `Status:` line and opener describe a two-slice build that
  has since been extended by four post-ship commits. The `Status:` line is the
  completion source of truth (`BUILD.md`) and must state the current truth.

### Cohort B verification questions (V1–V4)

Worker 3 answers these adversarially against source, independent of Worker 0's
reading. A "no defect" answer is a finding too — record the evidence.

- **V1 — nothing in the spec's contract was skipped.** Walk the
  `## Definition of done`, the `## Slice checklist`, the `## Test plan`
  (Tests 1–16 incl. 11a, 11b, 14a) and the `## Helper-reuse obligations (DRY)`
  ledger (D1–D4, D-N1–D-N3) against the shipped tree, and report every item with
  no landed counterpart. Worker 0's pre-read found none, which is exactly the
  claim that needs an independent reader.
- **V2 — the three post-ship Python/template hardenings (F7, F8) are correct and
  pinned.** Are the guards written against the *answer* rather than one spelling
  of the bad input (`BUILD.md` `### Fail-open shapes`)? Is each pinned by more
  than one test row (`### Acceptance rule: weakly pinned is revision-needed`)?
- **V3 — fail-open shapes in the shipped module.** The
  `except Exception` around `json.loads(request.body)` in `_postprocess` is
  upstream-verbatim and spec-sanctioned as deliberate degradation; confirm that
  reading and check every other clamp / `getattr` default / `or` fallback /
  truthiness test in the module.
- **V4 — the live/package test split holds the coverage contract.** Every branch
  named in the spec's coverage paragraph has a landed owner in one tier or the
  other, and no branch lost its owner when Revision 9 moved the present-path
  tests live.

## Artifact list

- `docs/builder/bld-042-review-1-spec_reconciliation.md` (Cohort A)
- `docs/builder/bld-042-review-2-code_verification.md` (Cohort B)
- `docs/builder/bld-042-integration.md`
- `docs/builder/bld-042-final.md`

Plus, if Cohort B returns `revision-needed` on a real code defect:

- `docs/builder/bld-042-review-3-code_fix.md` (Cohort C — dispatched only then)

**Retired 2026-09-12.** All five per-cycle artifacts —
`docs/builder/bld-042-review-1-spec_reconciliation.md`,
`docs/builder/bld-042-review-2-code_verification.md`,
`docs/builder/bld-042-review-3-code_fix.md`,
`docs/builder/bld-042-integration.md` and `docs/builder/bld-042-final.md` — were
deleted once the cycle closed, and this plan is the only survivor. All five were
introduced in `50b7d489` and die together, so one retrieval pointer serves them
all: `git show 50b7d489:docs/builder/<name>`. Every remaining `bld-042-*`
filename in this file is therefore a **retrieval key, not a live path** — nothing
below is broken by their absence. What the final gate held that nothing else
recorded was moved into this plan before it was deleted: `## The cycle's
instrument failures`, `## The owner rule's provenance, corrected`,
`## The JS-runtime question` and `## Decided — do not re-raise`.

## Checklist

- [x] Cohort A: spec reconciliation + rationale extraction (F1–F8, F-minor) -> `docs/builder/bld-042-review-1-spec_reconciliation.md`
- [ ] Cohort B: independent code verification (V1–V4) -> `docs/builder/bld-042-review-2-code_verification.md`
- [x] Cohort C: code fix for the confirmed defects -> `docs/builder/bld-042-review-3-code_fix.md`
- [x] Cross-cohort integration pass -> `docs/builder/bld-042-integration.md`
- [x] Final gate -> `docs/builder/bld-042-final.md`

## Why Cohort B's box stays unticked

`worker-0.md` `## Slice status legend` permits a box only over `final-accepted`,
and `bld-042-review-2-code_verification.md` reads **`revision-needed`** — the
correct terminal value for it. Cohort B was a pure verification cohort: its whole
product was the finding list M1–M4, its verdict is what dispatched Cohort C, and
it never had a build to final-verify. Its `revision-needed` is a true statement
that the code needed revision, and the revision happened in Cohort C.

Ticking it would be a false completion claim; sending it back for a ceremonial
final-verification pass would manufacture a `final-accepted` that means nothing.
So the box stays open with this as its recorded reason, and **Cohort C's
`final-accepted` is where B's findings are actually discharged** — M1, M2, M3 and
M4 each closed and independently re-measured there.

## Cohort returns

### Cohort A — `final-accepted` (2026-09-11)

Status line verified as exactly one of the five legal values before the box was
ticked (`worker-0.md` `## Slice status legend`). Write set verified against the
declared partition: `git status --short` shows the spec modified and the
rationale, both `bld-042-*` artifacts, and this plan untracked — **no `.py`, no
`docs/GLOSSARY.md`, no `docs/TREE.md`, no `README`, no DB.** The fence held.

Worker 0 re-derived rather than accepted (`BUILD.md` `## Claims are proven
mechanically`): `check_spec_glossary` → `OK: 24 terms`; `check_citations` →
`OK: 991 citations resolve`; `git diff --check` clean; residual sweeps for the
retired claims measure 0 in the spec (`debug_toolbar_urls.py`,
`tests.middleware.debug_toolbar_urls`, `0.262.0`, `no view class of its own`,
`## Revision history`).

One sweep hit needing a second instrument, recorded because the blunt reading
would have been wrong: `ships no view class` still matches **once**, at
`docs/SPECS/spec-042-debug_toolbar-0_0_14.md` #"**The package ships no view
class.**". Reading the context shows it sits inside `## Current state`, whose
opener vintages it ("A true description of the repo as this spec is authored"),
and the bullet now closes "and it is why the package's later own views are
covered by the same check." That is `BUILD.md` `### `## Current state`:
observations stand, predictions do not` applied correctly — a falsified
observation stays because the header dates it. **F5 is discharged; the grep was
the defective instrument, not the spec.**

### Cohort B — `revision-needed` (2026-09-11)

Four Medium findings, no High. Worker 0 verified all four against source before
any dispatch decision (`BUILD.md` `### Worker 0 verifies every finding against
source before dispatching`); all four hold:

- **M1** — the `Content-Encoding` bail is pinned by 1 row (weakly pinned). Its
  `operation_json_injection` parametrize id is **non-distinguishing**: the body
  `b"\x1f\x8bencoded-json"` fails the UTF-8 decode inside
  `middleware/debug_toolbar.py::_get_payload` #"except (json.JSONDecodeError,
  LookupError, UnicodeError):" and returns `None`, so the row passes with the
  `Content-Encoding` guard removed and re-proves a different guard. Verified by
  reading both guards against
  `tests/middleware/test_debug_toolbar.py::test_encoded_response_gets_no_package_mutation`.
- **M2** — the whole template contract lives in one node id
  (`::test_template_port_invariants_and_robustness_divergence`), so removing any
  one template guard scores exactly 1 and removing all of them still scores 1.
  `BUILD.md` #"A **test row** is one failing test node id" makes assert count
  irrelevant.
- **M3** — production defect in
  `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
  #"Object.entries(toolbar.panels).forEach": `update()` guards `data` three ways
  but never `data.debugToolbar`, so a `null` / scalar / `panels`-less payload
  throws `TypeError` out of the **globally patched** `JSON.parse`. Same class as
  the divergence family whose stated rule is "payload scrubbing is mandatory,
  DOM updates are best-effort".
- **M4** — `middleware/debug_toolbar.py` #"three-places-that-must-agree" states a
  closed population of three; `django-debug-toolbar>=7.0.0` is live at **five**
  sites: `pyproject.toml:70`, `tests/middleware/test_debug_toolbar.py:60`, the
  hint string itself, plus `docs/GLOSSARY.md` and `docs/README.md`. Verified by
  sweep. A published count of a population nothing gates is a self-falsifying
  instrument.

M1, M2 and M4's comment correction are `.py`-side and inside the fence. **M3 is
not** — its fix edits the `.html` asset. Escalated (below).

## Maintainer decisions taken mid-cycle

Recorded here per `worker-0.md` `### Mid-flight instructions are mirrored into
the artifact`, because an instruction living only in the dispatch transcript
leaves the artifact describing a contract no worker built against.

1. **M3's scope — DECIDED: the fence is widened by exactly one file, the `.html`
   asset.** M3's fix fell outside the original "spec files and code `.py` files
   ONLY" fence. The maintainer directed a research pass (reading `AGENTS.md`,
   `START.md`, `docs/README.md`, and the `TODO-ALPHA-052-0.0.15` card in
   `KANBAN.md`) before deciding. Findings, each verified by Worker 0 against
   source rather than accepted:

   - **`TODO-ALPHA-052-0.0.15` does not own it.** The card is "Extract
     DjangoDebugExtension into the standalone django-strawberry-debug package"
     (`KANBAN.md` #"Extract DjangoDebugExtension into the standalone"), and its
     files line names only `django_strawberry_framework/extensions/{__init__,debug}.py`,
     `tests/extensions/test_debug.py`, `tests/_soft_dependency.py`, the live
     debug-extension test, `pyproject.toml` and `uv.lock` — nothing under
     `middleware/` or `templates/`. The shared word "debug" is the only link;
     `spec-042 ## Out of scope` and the glossary both mark the two subsystems
     distinct. Routing M3 there would be `START.md` #"Item routed forward w/o
     NAMED owner dies" dressed up as a homing.
   - **No other card owns it.** The only other card opening
     `middleware/debug_toolbar.py` is 053 WP-A (the `debug-toolbar` extra and a
     possible shared view recognizer) — boundary/DRY work, not a JS guard.
   - **The asset is package source by the repo's own accounting.**
     `examples/fakeshop/apps/kanban/constants.py` #"templates/django_strawberry_framework/debug_toolbar.html"
     lists it among tracked package paths; hatchling packages the directory
     wholesale; `docs/TREE.md` renders it inside the package tree; and its only
     gate is a package-tier `.py` test that was in-fence all along. Read against
     its own listed exclusions — all rendered/board/closeout surfaces — the
     fence meant "package source, no doc/board churn", not a carve-out of an
     85-line asset.
   - **The decisive cost of deferring:** Cohort A's reconciled spec now states
     the port "diverges from the borrow in **six** spots, every one of them
     serving that rule" and the DoD names "the **six** documented guard
     divergences". Closing without M3 ships a spec asserting a complete family
     with a known seventh hole — manufacturing a third instance of exactly the
     F8 defect (post-ship template hardenings the spec never absorbed) this
     cycle exists to clear.
   - **Upstream carries the identical hole**
     (`~/projects/strawberry-django-main/strawberry_django/templates/strawberry_django/debug_toolbar.html`
     #"Object.entries(data.debugToolbar.panels).map("), so M3 is the borrow's
     flaw the divergence family was created to fix, not a port regression.

   `AGENTS.md` rule 5 — #"never offer defer-the-real-fix sequencing" …
   "shortcuts are never viable even with a follow-up card" — is the rule that
   settles it. The maintainer's words: "it sounds like this should have landed in
   the original BUILD but didn't, that is okay we will do it now."

   **Rejected alternatives, recorded so the round is not re-fought:** (a) defer
   to a new card — lost on cost (four surfaces reopened later, including an
   archived spec, to avoid one `.html` edit now) and on rule 5; (b) fold into
   card 053 — lost because 053 is boundary/DRY work and the fit is nominal, the
   file overlap alone.

   Still fenced OUT and unchanged: `docs/GLOSSARY.md`, `docs/README.md`,
   `README.md`, `docs/TREE.md`, `KANBAN.md` / `KANBAN.html`, `TODAY.md`,
   `CHANGELOG.md`, `examples/fakeshop/db.sqlite3`, and every closeout /
   agentflow-doc edit.

1a. **Cohort C's dispatch shape, maintainer-directed.** Write a dedicated
   `bld-042-review-3-code_fix.md` planning the work to completion, incorporate
   that plan into the spec and this build plan, then execute it through the
   `BUILD.md` cycle. Worker 1's planning pass is dispatched first and owns both
   the artifact and the spec amendments; Worker 2 then builds, Worker 3 reviews,
   Worker 1 final-verifies. `### Isolation is non-waivable` holds: the planner
   writes no source.
2. **The JS-runtime question — DEFERRED TO CLOSE-OUT, homed.** Cohort B escalated
   (correctly, rather than holding it at `revision-needed`) that the template
   asset has **no executing test of any kind** — every assertion in the port
   guard is text-identity on the file, so a green template test proves the text
   is present and nothing about whether the script runs. Whether this repo takes
   on a JS runtime is a contract-level call. **Maintainer decision: carry it into
   `docs/builder/bld-042-final.md` for discussion at close-out.** Worker 1 must
   surface it there under `### Deferred work catalog` with the escalation's own
   reasoning, not a paraphrase — it is a named item with a named owner
   (`AGENTS.md`: an item routed forward without a named owner dies).

## Items Cohort A routed to Worker 0

1. **A finding the plan's list missed, in scope.**
   `django_strawberry_framework/middleware/debug_toolbar.py` #"No other Python
   behavior differs." still closes the module docstring's divergence
   enumeration, which the `Content-Encoding` bail falsifies. `.py`-side and
   inside the fence → **folded into Cohort C's scope** alongside M1/M2/M4.
   (Cohort A also narrowed F7: the decode/parse bail and the non-object guard
   are one response-shape family in the shipped `_get_payload`, so the module's
   Python divergence count is **three**, not four.)
2. **Decision 1's "This spec lives at `docs/spec-042-…`" was false since
   archival** (fixed in-spec by Cohort A). The same template sentence plausibly
   sits in every archived spec under `docs/SPECS/`. Out of this cycle's
   single-spec scope → **deferred-work catalog**, needs an owner with that write
   set.
3. **`docs/GLOSSARY.md`'s `Debug-toolbar middleware` body** is a plausible
   carrier of the same staleness this cycle corrected in the spec (it is
   DB-backed, so the fix is an ORM edit plus a regenerate). Explicitly fenced out
   → **deferred-work catalog**.

## Final-gate scoping (recorded ahead of the gate, per `BUILD.md`)

`AGENTS.md` #"No pytest after edits" and `START.md` both forbid a worker running
the suite unless the maintainer asks; this dispatch did not ask. The tree is
also 53 files dirty with a concurrent cycle's in-flight work, so a full
`uv run pytest --no-cov` sweep would measure that work rather than this cycle's.
The gate therefore runs the read-only half in full —
`uv run ruff format --check .`, `uv run ruff check .`, `git diff --check`,
`uv run python scripts/check_spec_glossary.py --spec <spec>`,
`uv run python scripts/check_citations.py` — and runs a **focused** pytest scope
only if Cohort C lands a source change. Worker 0 surfaces the scoping to the
maintainer at hand-off rather than recording it as a silent skip.

## The cycle's instrument failures

The most transferable output of this cycle. The maintainer asked for no closeout
doc edits — `docs/builder/BUILD.md`, `ARTIFACT.md` and the `worker-*.md` role
files were explicitly fenced out — so this plan is their home; they were written
in the final gate and moved here when it was retired. Each
is an occasion where a **first measurement was wrong and only a second instrument
caught it**; in every case the first read exactly like a clean result.

1. **A `grep -v` content filter used as a path filter deletes exactly the rows
   whose text mentions the excluded path.** The floor-restatement census dropped
   `docs/SPECS/appx/spec-042-debug_toolbar-0_0_14-terms.csv` silently, because the
   filter intended to drop hits *in* a path also dropped every line that merely
   *names* it. The sweep read as complete. Carried with deferred item 1, whose owner is
   `TODO-ALPHA-053-0.0.15`, since the next floor bump runs that same census.

2. **A line-anchored grep found 2 of 3 wrapped sites.** The I3 sweep for the
   published sweep-instruction clause returned two hits, because the middleware's
   copy and one other wrap the clause across a line. Only a
   whitespace-normalizing sweep over a **stated** corpus — every tracked file,
   every untracked non-ignored file, plus the untracked rationale, **744 files** —
   found all three. Normalize whitespace before matching any clause prose can
   wrap, and state the corpus with the number.

3. **A link verifier's positive control did not fire, and a control that cannot
   fail is a passing proof.** The injected `[no-such-ref]` and `#no-such-heading`
   were appended to a scratch copy *after* the `<!-- LINK DEFINITIONS -->` marker
   the verifier partitions on, so they were never in the body the verifier reads;
   neither was reported and the control read as green. Re-run with the injection
   placed **before** the marker, both were reported, and only then was the real
   files' green believed. Place a control where the instrument actually looks, and
   watch it fail before trusting a pass. That verifier was the thing at fault
   three separate times in this cycle, and the file was right all three.

4. **An absence needle was inert from the day it was written, because upstream
   wraps the expression across three lines.** The row meant to catch a
   `document`-level nav lookup named a spelling that occurs **0** times in
   upstream's asset — upstream splits `document` / `.getElementById(…)` /
   `.querySelector("small")` across three lines — so the row could never have
   caught the verbatim paste it existed to catch, while reading green forever. The
   tightened needle occurs 1 upstream and 0 in the port. **An absence row's needle
   must be measured in the borrow before the row is believed**; that rule is now
   in the table's own comment and in the spec's Test 16, stated by mechanism and
   with no numeral (the table is a population the next editor extends).
   Inertness, subsumption and derivation are three ways an absence row cannot
   fail — one symptom, three different instruments.

5. **Five separate named citations in this cycle named the wrong site.** The last
   was the integration dispatch's own: it stated the falsified
   `` `.map(([id, panel])` `` spelling "occurs at exactly two standing-doc sites,
   both routed"; measured over the 744-file corpus, **it occurs at one**. Two
   *bullets* were routed, in one file, carrying different falsified content. The
   work was right every time and the population description was not — and a
   sweeper trusting the description looks for a hit that does not exist, then
   either invents one or concludes the population is already closed.
   **Re-derive every routed citation, count and population before acting on it.**

The generalization the five share, and the one worth carrying out of this cycle:
**a published count of a population nothing gates is a self-falsifying
instrument** — and so is the instrument that replaces it, unless its own needle is
audited against the population it points at. M4's fix replaced a false count with
a sweep instruction, and the instruction's needle could not see the population it
named. State the corpus or state no number; publish the reproducible delta, not
the absolute total; and drop the numeral from any list later work extends.

## The owner rule's provenance, corrected

Stated here so the mistake stops propagating: it is `START.md`
#"Item routed forward w/o NAMED owner dies", under `## Past mistakes`. It is
**not** in `AGENTS.md` — measured, not recalled: `grep -c 'NAMED owner' AGENTS.md`
returns **0** both in the working tree and at `git show HEAD:AGENTS.md`. Worker 0's
dispatches, Cohort C's catalog and the final gate's own dispatch all named
`AGENTS.md`; the integration pass corrected it, and this is the correction's home.

## The JS-runtime question — a maintainer decision, parked for close-out

Recorded here at the maintainer's explicit instruction (build plan
`## Maintainer decisions taken mid-cycle` item 2), with **the escalation's own
reasoning rather than a paraphrase**, because it is a contract-level call and not
a worker's (`BUILD.md` `### Contract-level findings are escalated as maintainer
decisions before dispatch`).

Cohort B's escalation, in its own words (`bld-042-review-2-code_verification.md`
`### Notes for Worker 1`, retired — `git show 50b7d489:docs/builder/<name>`):

> **Escalated (contract-level): the asset has no executing test of any kind.**
> Every template assertion is a substring check over the file's text, so the
> suite can prove the guards are *written* and can never prove they *work* — and
> three of the four documented divergence families exist specifically to survive
> runtime inputs (null-prototype objects, absent DOM nodes, a shadow root). M2's
> parametrized split raises the failability count and is the in-scope fix, but it
> does not change what is being proved. Whether this package should carry a
> JavaScript runtime for one 89-line asset is a contract-level call, not a
> worker's. Resolution paths: (a) accept text-identity pinning permanently and
> say so in the spec, so the next reviewer does not re-raise it; (b) add a
> minimal DOM harness for this asset alone; (c) narrow the asset so less of it
> needs guarding.

**What is true after the cycle, and what is not.** M2 is closed: the single node
id became **57 parametrized rows**, so removing any one template guard now fails
its own row. That raised failability and changed nothing about what is proved.
All 57 rows are text-identity predicates over the file on disk. **A green table
proves the guard's text is present, single-sited and correctly ordered, and says
nothing about whether the JavaScript runs.** The integration pass narrowed the
gap in one direction only, and measured rather than argued it: all eight absence
needles occur exactly once in upstream's asset and never in the port, so the rows
**do** detect a verbatim paste of upstream's text — and a rewrite of the same hole
in different words passes every one of them.

**Homed 2026-09-12 on `TODO-BETA-072-0.1.8`** (adversarial non-live test suite),
so the question carries a named owner now that this plan is archived.
Path (a) has already been half-taken: the spec now carries
`## Risks and open questions` #"The bridge asset's guards are pinned by text,
never by execution.", which states the limit and names the maintainer as the
risk's owner. What remains is the decision itself.

**What the machine actually has, measured at this gate rather than assumed:**

```shell
$ node --version
v24.10.0
$ node -e 'console.log("typeof CSS =", typeof CSS); console.log("typeof document =", typeof document)'
typeof CSS = undefined
typeof document = undefined
```

`node` is installed, so path (b) is not blocked on a missing runtime — but a bare
`node` carries **no `CSS` global at all** and no `document`. That matters for
scoping the decision: even the one guard that is otherwise pure language,
`CSS.escape(panelId)` with its empty-identifier skip, cannot be exercised under
`node` as it stands. Path (b) is not "run the file under node"; it is a DOM/CSSOM
emulator (jsdom or equivalent) as a new dev dependency, for one 89-line asset.
That cost is the substance of the decision, and it is the maintainer's.

It is also the reason the cycle's hot-path declaration can carry no number: the
build plan's `Hot-path declaration: none` rests on magnitude and the dev-only
gate, **not** on "no executable code changed", and no instrument in this
repository can produce a before/after number for a browser asset.

## Decided — do not re-raise

Four rulings the cycle made and nothing else records. Each was re-verified against
source on 2026-09-12 before this plan was archived.

1. **The spec's `## Implementation plan` opener is not banned process
   provenance.** `docs/SPECS/spec-042-debug_toolbar-0_0_14.md` #"for the Worker 0
   build handoff" names an audience rather than attributing a change, so
   `AGENTS.md` rule 27's ban does not reach it. Pre-existing at `HEAD`; catalogued
   so the next reader does not re-decide it.
2. **A prior cycle's closed artifact carries a warrant this cycle falsified, and
   its conclusion still stands.** `docs/builder/DONE/build-040-auth_mutations-0_0_13.md`
   #"Deferred entries 3 and 5 were correctly NOT homed" defers five
   `spec-042 Revision N` citations on the ground that the spec still carries the
   revision names and has no rationale companion. **Both premises are now false** —
   the block moved to the companion and the companion exists — while the
   conclusion holds, because the rationale preserved the names under
   `## Round vocabulary` and the spec carries the signpost. That artifact is
   closed and was not edited; this note exists so a later reader does not
   re-derive the wrong conclusion from a dead warrant.
3. **Presence rows that cannot fail alone were measured and deliberately left.**
   Several `_present` rows in the template contract are subsumed by a sibling
   pinning the same needle more strictly, so a containment check run table-wide
   meets them. The disposition now lives where it is needed, in
   `tests/middleware/test_debug_toolbar.py`'s own table comment, stated by
   mechanism and without a count (the table is a population later work extends).
4. **`scripts/prove_failability.py`'s verdict arithmetic has no row-isolation
   case.** It labels a one-row result `WEAKLY PINNED - revision-needed` because the
   arithmetic is written for boundary proofs, where one row means one assertion
   holds a guard. A **row-isolation** proof — "does this row produce a failing id
   no other row produces" — seeks exactly one row, and a second would falsify it,
   so the tool's line reads as a finding against a proof that succeeded. Twice in
   this cycle a pass had to write a paragraph explaining the verdict does not
   apply. **Homed 2026-09-12 on `TODO-BETA-072-0.1.8`**, beside that card's
   existing failability-manifest item.
