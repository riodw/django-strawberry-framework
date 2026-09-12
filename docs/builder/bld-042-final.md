# Build: final test-run gate — spec-042 post-ship reconciliation cycle

Spec reference: `docs/SPECS/spec-042-debug_toolbar-0_0_14.md` (card `DONE-042-0.0.14`)
Build plan: `docs/builder/build-042-debug_toolbar-0_0_14.md`
Status: final-accepted

This is `BUILD.md` `## Final test-run gate`, run by Worker 1, and it closes the
cycle. Every cohort (A spec custody, B code verification, C code fix) and the
cross-cohort integration pass are closed at `final-accepted` — except Cohort B,
whose terminal `revision-needed` is correct and whose reason the build plan
records under `## Why Cohort B's box stays unticked`.

---

## Gate scoping — deliberate, argued, and stated here so it is not a silent skip

`BUILD.md` `## Final test-run gate` prescribes a full `uv run pytest --no-cov`
sweep. **Worker 0 scoped that deliberately for this cycle** and recorded the
scoping in the build plan's `## Final-gate scoping` section *before* the gate
ran. `BUILD.md` calls the gate the backstop that confirms things happened, so a
scope narrowed without saying so is indistinguishable from one nobody ran. The
reasons, both load-bearing:

1. **No worker runs the suite unless the maintainer asks.**
   `AGENTS.md` #"No pytest after edits" and `START.md` #"**No `pytest` after
   edits.**" both say so. **This dispatch did not ask**, and the maintainer has
   not authorized a full sweep at any point in this cycle.
2. **A full sweep would predominantly measure someone else's in-flight work.**
   The tree carries **67 dirty paths from a concurrent session's spec-050
   cycle** (enumerated under `### What is NOT this cycle's`, and measured at this
   pass rather than copied from an earlier reading). A full sweep would report on
   that work, not this cycle's — and any failure it surfaced would belong to
   them. `BUILD.md` `## Claims are proven mechanically` is explicit that a
   failing test in a tree dirty with another session's work is **not
   worker-verifiable at all**: reproducing it needs a clean HEAD tree, which only
   the maintainer can run. The correct response would be to escalate, never to
   diagnose — so running the sweep would buy an unusable measurement at the price
   of a misleading one.

What runs instead is the focused scope this cycle has used at every pass, plus
the whole read-only half of the gate at full tree width.

### What is deliberately NOT run, and why

- **`manage.py check` / `makemigrations --check --dry-run`.** `BUILD.md` names
  these for model / admin / URLconf drift. This cycle changed **no** model, no
  admin, and no URLconf — its entire write set is one spec, one rationale
  companion, one middleware module (comments and docstrings only), one template
  asset, one test file, and the `docs/builder/` artifacts.
- **The generator `--check` runs** (`build_kanban_md`, `build_kanban_html`,
  `build_glossary_md`, `build_tree_md`). Every input they read is fenced out of
  this cycle, and the tree is dirty with the concurrent session's regenerated
  `docs/GLOSSARY.md`, `docs/TREE.md` and `examples/fakeshop/db.sqlite3`.
  `BUILD.md` `## Pre-commit and CI gates` (via `START.md`) warns that `--check`
  measures the **WORKING TREE**, so running them here would grade their
  half-landed regenerate and report it under this cycle's name.
- **Any `--cov*` flag.** `BUILD.md` `## Coverage is the maintainer's gate, not a
  worker's tool` forbids them in every worker pass, the final gate included, with
  no carve-outs. `--no-cov` is used because `pytest.ini`'s `addopts` auto-applies
  `--cov`.
- **`scripts/check_trailing_commas.py` with no paths.** Its default is a
  **repo-wide auto-fix**, which would rewrite the concurrent session's files.
  Explicit paths only, `--check` only.

---

## Gates run

| # | Gate | Command | Result |
| --- | --- | --- | --- |
| 1 | Focused suite | `uv run pytest tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py -n0 --no-cov` | **PASS** — `86 passed in 13.63s`, exit 0, **0 collection errors**. 86 collected = 86 run; 57 of them are `::test_template_port_invariants_and_robustness_divergence` rows, counted by `--collect-only` rather than asserted |
| 2 | Format | `uv run ruff format --check .` | **PASS** — `444 files already formatted`, exit 0. Read-only; never `--fix` |
| 3 | Lint | `uv run ruff check .` | **PASS** — `All checks passed!`, exit 0. Read-only; never `--fix` |
| 4 | Whitespace / conflict markers | `git diff --check` (whole tree) | **PASS** — no output, exit 0 |
| 5 | Spec glossary | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-042-debug_toolbar-0_0_14.md` | **PASS** — `OK: 24 terms - all have glossary entries and at least one spec link.`, exit 0 |
| 6 | Citations | `uv run python scripts/check_citations.py --check` | **PASS** — `OK: 992 citations resolve (823 in 441 .py files, 169 in KANBAN.md).`, exit 0 |
| 7 | Source layout | `scripts/check_trailing_commas.py --check <9 explicit cycle paths>` | **PASS** — exit 0 |
| 8 | Source layout, the asset | `scripts/check_trailing_commas.py --check <the .html asset>` | exit 0, **and the exit code means "not read"** — see below |

**Gate 7's own corpus, stated because a green is only evidence for what the
instrument reads.** The nine paths passed were the middleware module, the test
file, the spec, the rationale, the four `bld-042-*` artifacts and the build plan.
Five of those printed `excluded from the source-layout rules -- not checked`: the
`bld-042-*` artifacts and the plan are per-cycle scratch and outside the rule.
So gate 7's real corpus is **four** files — the `.py` pair and the two `.md`
contract files — and that is what its green covers.

**Gate 8 is an absence of complaint, not a reading.**
`scripts/check_trailing_commas.py` declares its suffix list as
`(".py", ".md", ".json", ".graphql", ".gql")`; `.html` is not in it, so the
shipped template asset is silently skipped and its exit 0 proves nothing about
the file. Recorded rather than reported as a pass, because "the checker exited 0"
and "the checker read the file and found it clean" are different claims and this
cycle has been caught by that difference five times (`### The cycle's instrument
failures`). The asset's only gate is the package-tier `.py` test in gate 1.

### Floor verification

**Floor-verification scope: `none`**, as declared in the build plan's preamble.
No cohort touched a Django / Strawberry / channels integration seam: Cohort A and
the integration pass wrote prose only; Cohort C's Python change is comment and
docstring bytes; its executable change is browser-side JavaScript in a template
asset.

**The floor facts, copied from `docs/builder/BUILD.md` `## Floor verification`,
the single canonical statement — never from memory:** Django **5.2.16** on Python
**3.10** with strawberry-graphql **0.316.0**. No floor venv was built and none was
owed. Cohort B independently answered the one floor question the cycle raised
(F6): the module's only Strawberry touchpoint is
`from strawberry.django.views import BaseView`, which either resolves at import
time or fails loudly, so no code behavior depends on whether the declared floor
reads `0.262.0` or `0.316.0`. F6 was therefore a spec-text correction, discharged
by Cohort A, and not a re-run.

### No live mutation is in the tree

`BUILD.md` `### Mutations are transient` — an agent dying mid-proof leaves a
deliberately broken boundary behind, and the next reader inherits it.

- No `ACTIVE-MUTATION.json` exists anywhere in the tree.
- The template asset's SHA-256 is
  `92cd040294ad2dba26158c652f92b9760cd35b64b91f848822a1fa093e17fa00`, **identical
  to the post-revert hash every Cohort C and integration-pass proof recorded**.
  The mutations from six failability entries are all reverted.
- The middleware module's AST, docstrings stripped, is **identical to HEAD** —
  re-derived at this pass rather than accepted (`### What changed, by file`).

---

## What changed, by file — the maintainer commits from this

Eleven paths, every one carrying `042` in its name or living inside the
spec-042 / debug-toolbar surface. Four are tracked and modified; seven are new
and untracked.

### Tracked, modified (4)

| Path | Diff | What changed |
| --- | --- | --- |
| `docs/SPECS/spec-042-debug_toolbar-0_0_14.md` | 1814 lines changed | Cohort A's reconciliation plus Cohort C's and the integration pass's amendments. The nine-revision inline chronology moved out to the rationale companion; the nine false `tests/middleware/debug_toolbar_urls.py` naming sites, the four stale `0.262.0` floor sites, the "ships no view class" premise and the "two narrow divergences" ledger all corrected; the `Status:` line now states the post-cut extended contract; `## Risks and open questions` gained the two bullets that license deferred items 1 and 6 |
| `docs/SPECS/appx/…-rationale.md` → see new files | — | (the companion is new; listed below) |
| `django_strawberry_framework/middleware/debug_toolbar.py` | 42 lines changed, **14556 → 15503 bytes** | **Comment and docstring bytes only.** The module docstring's divergence enumeration now names the three Python divergences by mechanism instead of closing on a false "two … No other Python behavior differs"; the `_DEBUG_TOOLBAR_INSTALL_HINT` comment block replaces the false three-places population claim with the gated trio named by mechanism plus an honest sweep instruction (sweep the package **name**, read each hit — never the `>=` specifier). **AST-identical to HEAD with docstrings stripped, re-derived at this gate: both dumps are 12387 characters and compare equal.** No executable Python moved |
| `django_strawberry_framework/templates/…/debug_toolbar.html` | 40 lines changed | The cycle's only executable change, and it is browser-side JavaScript. Adds `isRecord()` defined once and applied at every read site; guards `data.debugToolbar` and `.panels` before the panel loop (M3, the residual hole in the very guard family the post-ship commits were extending — upstream carries the identical hole); guards each panel entry; routes the arbitrary panel key through `CSS.escape` with an empty-escape skip; documents the `setAttribute` coercion as upstream's write, kept; and terminates a missing statement semicolon |
| `tests/middleware/test_debug_toolbar.py` | 512 lines changed | Adds `::test_install_hint_floor_matches_the_pyproject_dev_group_row` (the governance row gating hint ↔ literal ↔ `pyproject.toml`); parametrizes the encoded-response row and gives each row a **positive control** drive so it can no longer pass by re-proving a different guard (M1); converts the single-node-id template test into a **57-row parametrized contract table** with eight predicate constructors (M2), so removing any one template guard now fails its own row; introduces `_SCRUB` / `_SCRUB_STATEMENT` to collapse ten typed copies of the scrub needle; re-needles the `no-upstream-value-returning-panel-map` row to `` `.panels).map(` `` (I4) |

### New, untracked (7)

| Path | Size | What it is |
| --- | --- | --- |
| `docs/SPECS/appx/spec-042-debug_toolbar-0_0_14-rationale.md` | 965 lines / 69,959 B | The companion that never existed (F1). Tracked and committed alongside the spec — a durable record, not scratch (`worker-1.md` `### Performing the rationale move` rule 5) |
| `docs/builder/build-042-debug_toolbar-0_0_14.md` | 510 lines | Worker 0's build plan |
| `docs/builder/bld-042-review-1-spec_reconciliation.md` | 604 lines | Cohort A — `final-accepted` |
| `docs/builder/bld-042-review-2-code_verification.md` | 602 lines | Cohort B — `revision-needed` (correct terminal value; see the plan) |
| `docs/builder/bld-042-review-3-code_fix.md` | 4424 lines | Cohort C — `final-accepted` |
| `docs/builder/bld-042-integration.md` | 1935 lines | Integration pass — `final-accepted` |
| `docs/builder/bld-042-final.md` | this file | The final gate |

**Retired 2026-09-12.** The cycle's four per-pass artifacts —
`docs/builder/bld-042-review-1-spec_reconciliation.md`,
`docs/builder/bld-042-review-2-code_verification.md`,
`docs/builder/bld-042-review-3-code_fix.md` and
`docs/builder/bld-042-integration.md` — were deleted once the cycle closed; this
plan and `docs/builder/bld-042-final.md` survive it. All four were introduced in
`50b7d489` and die together, so one retrieval pointer serves them all:
`git show 50b7d489:docs/builder/<name>`. Every remaining `bld-042-review-*` or
`bld-042-integration` filename in this file is therefore a **retrieval key, not a
live path** — nothing below is broken by their absence.

Untracked and gitignored, so they are **not** part of the commit:
`docs/builder/worker-memory/042-worker-{1,2,3}.md` and
`docs/builder/temp-tests/042/` (manifests, reports, probe scripts).

---

## What is NOT this cycle's

`git status --porcelain` returns **77** paths at this pass — a reading taken here,
never copied from the plan's 53 or the integration pass's 76/77. **10 are this
cycle's** (the four modified tracked files and six of the seven new files; this
artifact is the eleventh and does not yet appear). **67 are the concurrent
session's spec-050 cycle** and are baseline-dirty out-of-scope under `AGENTS.md`
rule 34: never edited, never reverted, never `git stash`ed, never
`git checkout`ed. Comparisons used `git show HEAD:<path>`.

`START.md` #"Attribute dirty files by DIFF CONTENT, not \"files my task touched\""
is the rule this list serves — and the attribution here is by content, not by a
filename convention: the 67 carry `list_field` / `orders` / `keyset` /
`resource_policy` argument work, the spec-050 doc set, and the regenerated
board/glossary/DB that work produced.

**A `git add -A` would sweep all 67 into this commit.** `git add` the eleven paths
below by name.

### This cycle's eleven paths — the complete `git add` list

```
django_strawberry_framework/middleware/debug_toolbar.py
django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html
docs/SPECS/spec-042-debug_toolbar-0_0_14.md
tests/middleware/test_debug_toolbar.py
docs/SPECS/appx/spec-042-debug_toolbar-0_0_14-rationale.md
docs/builder/build-042-debug_toolbar-0_0_14.md
docs/builder/bld-042-review-1-spec_reconciliation.md
docs/builder/bld-042-review-2-code_verification.md
docs/builder/bld-042-review-3-code_fix.md
docs/builder/bld-042-integration.md
docs/builder/bld-042-final.md
```

### The 67 that are not (do not stage, do not revert)

`CONTRIBUTING.md`, `START.md`, `django_strawberry_framework/connection.py`,
`…/keyset.py`, `…/list_field.py`, `…/orders/sets.py`, `…/resource_policy.py`,
`…/types/finalizer.py`, `…/utils/querysets.py`, `docs/GLOSSARY.md`,
`docs/TREE.md`, `docs/builder/bld-final.md`, `docs/builder/bld-integration.md`,
`docs/builder/bld-slice-3-sql_and_unit_contracts.md`,
`docs/builder/build-050-list_field_arguments-0_0_15.md`, `docs/feedback.md`,
`docs/feedback2.md`, `docs/spec-050-list_field_arguments-0_0_15.md`,
`examples/fakeshop/README.md`,
`examples/fakeshop/apps/library/tests/test_schema.py`,
`examples/fakeshop/apps/products/tests/conftest.py` (**deleted**),
`examples/fakeshop/apps/products/tests/test_schema.py` (**deleted**),
`examples/fakeshop/db.sqlite3`, `examples/fakeshop/test_query/README.md`,
14 further `examples/fakeshop/test_query/test_*_api.py` files, 26 further
`tests/**/test_*.py` files, plus two untracked:
`docs/review/rev-050-implementation-review.md` and
`examples/fakeshop/test_query/test_schema_composition_api.py`.

**Three of those deserve a second look before any staging command runs:**

- **`docs/builder/bld-final.md` and `docs/builder/bld-integration.md` are the
  spec-050 cycle's artifacts, not this one's.** This cycle's are
  `bld-042-final.md` and `bld-042-integration.md`. The names differ by five
  characters and a careless `git add docs/builder/` takes both sets.
- **Two `examples/fakeshop/apps/products/tests/` files are `D`, not `M`.** A
  broad `git add` stages their deletion.
- **`START.md` is dirty**, so the required reading for this pass was of a
  modified file. The one line this artifact cites from it —
  #"Item routed forward w/o NAMED owner dies" — was checked against
  `git show HEAD:START.md` and is identical in both (line 334 at HEAD, 337 in
  the tree); the concurrent session's five-line delta does not touch it.

---

## The JS-runtime question — a maintainer decision, parked for close-out

Recorded here at the maintainer's explicit instruction (build plan
`## Maintainer decisions taken mid-cycle` item 2), with **the escalation's own
reasoning rather than a paraphrase**, because it is a contract-level call and not
a worker's (`BUILD.md` `### Contract-level findings are escalated as maintainer
decisions before dispatch`).

Cohort B's escalation, in its own words
(`bld-042-review-2-code_verification.md` `### Notes for Worker 1`):

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

---

## The cycle's instrument failures

The most transferable output of this cycle, and the maintainer asked for no
closeout doc edits — `docs/builder/BUILD.md`, `ARTIFACT.md` and the `worker-*.md`
role files are explicitly fenced out — so this artifact is where they live. Each
is an occasion where a **first measurement was wrong and only a second instrument
caught it**; in every case the first read exactly like a clean result.

1. **A `grep -v` content filter used as a path filter deletes exactly the rows
   whose text mentions the excluded path.** The floor-restatement census dropped
   `docs/SPECS/appx/spec-042-debug_toolbar-0_0_14-terms.csv` silently, because the
   filter intended to drop hits *in* a path also dropped every line that merely
   *names* it. The sweep read as complete. Carried with deferred item 1, since the
   next floor bump runs that same census.

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

---

## Deferred work catalog

The next spec author's reading list (`BUILD.md` `## Final test-run gate`). This
is the **merged 16-item set** the integration pass assembled, which **supersedes**
Cohort C's 11 — four of those corrected, one discharged, plus five added by the
integration pass and the consolidation's review. Items 1–11 keep their Cohort C
numbers so a reader arriving from `bld-042-review-3-code_fix.md` lands on the same
item.

Each bullet carries **the source artifact section**, **the spec line licensing the
deferral (or `none`)**, **a one-line description**, and **a named owner**.

**The owner rule's provenance, stated correctly here so the mistake stops
propagating:** it is `START.md` #"Item routed forward w/o NAMED owner dies", under
`## Past mistakes`. It is **not** in `AGENTS.md` — measured, not recalled:
`grep -c 'NAMED owner' AGENTS.md` returns **0** both in the working tree and at
`git show HEAD:AGENTS.md`. Worker 0's dispatches, Cohort C's catalog and this
gate's own dispatch all named `AGENTS.md`; the integration pass corrected it, and
this is the correction's home.

### Items needing a KANBAN card the maintainer must place

The board write set (`KANBAN.md` / `KANBAN.html` / `examples/fakeshop/db.sqlite3`)
is fenced out of this cycle, so **no worker can home these**. Grouped so the
maintainer acts on two decisions rather than five:

- **One card for items 3 + 4** — both need `django_strawberry_framework/utils/imports.py`
  and `tests/test_ci_governance.py`.
- **One card for items 1 / 12 / 14 / 15** — all four name *"the card that next
  raises the `[dependency-groups].dev` specifier"*, and **no such card exists**.
  Until it is placed, four catalogued items point at an owner that is not on the
  board, which is the exact shape `START.md` warns kills a routed item.
- **One card for item 2** — the DB-backed `docs/GLOSSARY.md` entry; recommended
  carrier is the Slice-2 glossary status flip the spec already defers to the joint
  cut.

Items 6, 7, 8 and 10 have live owners already. Items 5, 9, 11, 13 and 16 need no
card: they are recorded as decided or discharged.

### The sixteen

1. **The floor's ungated restatements, and an instrument that can see them.**
   *Source:* Cohort C `### Deferred work catalog` item 1, corrected by the
   integration pass's `### 3.` and `### Carried forward` item 1. *Spec licence:*
   `## Risks and open questions`, the "single-valued across its three gated sites,
   and restated elsewhere ungated" bullet. *Description:*
   `django-debug-toolbar>=7.0.0` is restated — correct today, gated by nothing —
   at `docs/GLOSSARY.md` (DB-backed: an ORM edit plus a regenerate, never a
   hand-edit), `docs/README.md`, `CHANGELOG.md` #"Soft-dependency feature floors",
   the `…-terms.csv` soft-dependency row, **and the spec's own seven value-bearing
   restatements**, which Cohort C's enumeration omitted. The terms.csv site is a
   **pair**: `import_spec_terms` loaded the same `notes` cell into
   `glossary_glossaryspecmention.notes` in `examples/fakeshop/db.sqlite3`, so
   fixing the CSV alone leaves the DB copy live. Cohort C's "24 / 25" is
   **withdrawn** — the absolute count is a function of an unstated corpus and moves
   by more than twenty depending on whether `__pycache__`, the tracked DB and
   `temp-tests/` are read; the reproducible half is the delta, that the loose
   needle finds exactly one restatement the tight one misses (`CHANGELOG.md:61`).
   The sweep a bump owes is over the package **NAME**, each hit read. Carry the
   census failure with the item (`### The cycle's instrument failures` #1).
   *Owner:* the card that next raises the `[dependency-groups].dev` specifier —
   **needs a KANBAN card; the maintainer places it.**

2. **`docs/GLOSSARY.md`'s Debug-toolbar middleware entry is a measured stale
   carrier.** *Source:* Cohort C item 2. *Spec licence:* none — the entry is
   outside the spec's contract surface. *Description:* its body says "Two
   deliberate robustness divergences" and enumerates two where the module now
   names three, and it restates the floor besides. DB-backed and fenced out of
   this cycle: an ORM edit plus a regenerate. *Owner:* **needs a KANBAN card**;
   recommended carrier is the Slice-2 glossary status flip the spec already defers
   to the joint cut.

3. **The DRF twin is the package's last false-population comment.** *Source:*
   Cohort C item 3. *Spec licence:* none — different spec (spec-039).
   *Description:* `django_strawberry_framework/rest_framework/__init__.py`
   #"three-places-that-must-agree" and
   `tests/rest_framework/test_soft_dependency.py` #"three-places-that-must-agree"
   name three places for `djangorestframework>=3.17.0`, and — unlike Channels and
   Strawberry — no `tests/test_ci_governance.py` row gates the `pyproject.toml`
   side. Same defect class as M4. *Owner:* **needs a KANBAN card** with that write
   set (shared with item 4).

4. **The `DEBUG_TOOLBAR_FLOOR` refinement, trigger fired.** *Source:* Cohort C
   item 4. *Spec licence:* none — a refinement, not a deferred fix.
   *Description:* hoist the toolbar floor beside `CHANNELS_FLOOR` /
   `STRAWBERRY_FLOOR` in `django_strawberry_framework/utils/imports.py`,
   interpolate it into the hint, and gate it beside the two existing rows in
   `tests/test_ci_governance.py`; its stated trigger — a third
   regex-over-`pyproject.toml` governance row — fired in this cycle. Catalogue it
   with this framing so it is not re-raised as a duplication finding against
   Cohort C. *Owner:* **the same card as item 3.**

5. **~~Re-needle `no-upstream-value-returning-panel-map`~~ — DISCHARGED, not
   deferred.** *Source:* Cohort C item 5, superseded by the integration pass's
   `### I4` and closed by the consolidation pass. *Spec licence:* n/a.
   *Description:* the row now carries `` `.panels).map(` ``; 0
   absence-over-absence containment pairs survive, and Worker 3's re-run shows the
   row failing alone. **Recorded so this gate does not carry it forward as open**,
   which a straight copy of Cohort C's list would have done. *Owner:* none; closed
   in this cycle.

6. **The JS-runtime question**, parked for the maintainer. *Source:* Cohort C
   item 6, with one sentence of evidence added by the integration pass's `### I5`;
   build plan `## Maintainer decisions taken mid-cycle` item 2. *Spec licence:*
   `## Risks and open questions`, the "pinned by text, never by execution" bullet.
   *Description:* the asset's guards are established by reasoning against the
   language and the CSSOM rules and by no test; the absence rows detect a paste of
   upstream's text and nothing else. That last clause is now **measured in both
   assets** rather than reasoned — all eight needles occur once upstream and never
   in the port — so the risk is bounded rather than suspected. Full escalation
   text, resolution paths and the `node`/`CSS` measurement are in
   `## The JS-runtime question` above. *Owner:* **the maintainer, at close-out.**

7. **Decision 1's "This spec lives at `docs/spec-…`" template sentence** in the
   archived specs. *Source:* Cohort C item 7; build plan
   `## Items Cohort A routed to Worker 0` item 2. *Spec licence:* none.
   *Description:* the custody cohort corrected spec-042's copy and could not sweep
   the rest; the population is a grep away and the fix is mechanical. *Owner:* the
   next `docs/SPECS/NEXT.md` Step 8 archival sweep, which already rewrites every
   cross-reference in one pass.

8. **Package-relative citations of `utils/imports.py::require_optional_module` —
   the population is THREE, not two.** *Source:* Cohort C item 8, corrected by the
   integration pass's `### I6`. *Spec licence:* none. *Description:* two in
   `docs/SPECS/spec-042-debug_toolbar-0_0_14.md` and **one in
   `docs/SPECS/spec-041-channels_router-0_0_14.md`**, same spelling; `AGENTS.md`
   rule 27 wants the repo-relative form, and no gate reads either
   (`check_citations.py` does not read `docs/`). Fixing only the two named would
   leave the sibling live while the population read as closed. *Owner:* the same
   archival sweep as item 7.

9. **`## Implementation plan`'s "for the Worker 0 build handoff" opener.**
   *Source:* Cohort C item 9. *Spec licence:* none. *Description:* pre-existing at
   HEAD; it names an audience rather than attributing a change, so it is **not**
   the process provenance `AGENTS.md` rule 27 bans. Catalogued so the next reader
   does not re-decide it. *Owner:* nobody — recorded as decided.

10. **The concurrent session has queued work in this cycle's test file.**
    *Source:* Cohort C item 10, one fact added by the integration pass. *Spec
    licence:* none. *Description:* its dirty
    `examples/fakeshop/test_query/README.md` backlog names
    `tests/middleware/test_debug_toolbar.py::test_get_payload_panel_title_only_when_has_content`
    for live promotion and two `Content-Length` refresh rows for deletion
    afterwards. Nothing collides today; whoever executes it now meets a file
    carrying a 57-row table, eight predicate constructors and the `_SCRUB`
    constants. *Owner:* the concurrent session's own live-promotion card.

11. **Worker 2's routed Test 16 rewording is discharged, not deferred.** *Source:*
    Cohort C item 11. *Spec licence:* n/a. *Description:* the clause was not false
    as landed; it named one anchor where two rows landed, and Cohort C's spec edit
    3 states both. *Owner:* none; closed in Cohort C.

12. **A prior cycle's closed artifact carries a warrant this cycle falsified.**
    *Source:* integration pass `### I2` and `### Carried forward` item 4. *Spec
    licence:* none. *Description:*
    `docs/builder/DONE/build-040-auth_mutations-0_0_13.md` #"Deferred entries 3
    and 5 were correctly NOT homed" defers the five `spec-042 Revision N`
    citations on the ground that the spec still carries the revision names and has
    no rationale companion. **Both halves are now false** — the block moved, the
    companion exists — while the **conclusion** stays correct, because Cohort A
    preserved the names and the spec now carries the signpost. Catalogued so a
    later reader does not re-derive the wrong conclusion from a dead warrant; that
    artifact is closed and was not edited. *Owner:* nobody — recorded as decided.
    (Its practical successor is item 1's card, which is the next pass likely to
    open that neighbourhood.)

13. **Seven `_present` rows cannot fail alone; measured, and deliberately left.**
    *Source:* integration pass `## Review (Worker 3)` `### Low:` L1 and the
    independent re-derivation in `### The three Lows, decided`. *Spec licence:*
    `## Test plan` Test 16, whose falsifier list is about **absence** rows — the
    clause added by the integration pass's spec edit 1 deliberately does not reach
    these. *Description:* each is subsumed by a sibling pinning the **same** needle
    more strictly, so nothing is advertised that is not held and the table's
    detection power is identical with or without them; the only available fix is
    deleting the plain statement of each invariant. Recorded because a later reader
    running the containment check table-wide will meet all seven and needs to know
    they were measured and dispositioned rather than missed. *Owner:* nobody —
    recorded as decided.

14. **A symbol name wrapped across two backtick spans, ungreppable and ungated.**
    *Source:* integration pass `## Review (Worker 3)` `### Low:` L3, decided in
    `### The three Lows, decided`. *Spec licence:* none. *Description:*
    `tests/middleware/test_debug_toolbar.py` #"rows below against the literal,"
    splits `test_install_hint_floor_matches_the_pyproject_dev_group_row` across two
    code spans to fit the line, so a rename of that test strands the reference with
    nothing to catch it (`check_citations.py` is `path::Symbol`-only and this is
    neither form). The fix is to shorten the surrounding clause so the name sits on
    one line; it changes no behavior, no row and no node id. *Owner:* **item 1's
    owner — the card that next raises the `[dependency-groups].dev` specifier**,
    because the wrapped name sits inside the `_HINT_SUBSTRING` comment block that
    card rewrites. **Needs the same KANBAN card as item 1.**

15. **The table comment's falsifier list mirrors two of the contract's three
    absence-row shapes; sync it when the file is next opened.** *Source:*
    integration pass `## Review (Worker 3)` `### Low:` L2, discharged into the spec
    by that pass's spec edit 1. *Spec licence:* `## Test plan` Test 16 as amended,
    which now names all three. *Description:*
    `tests/middleware/test_debug_toolbar.py` #"An absence needle must occur in the
    borrow" states inertness and subsumption; the third shape — an absence needle
    **derived from `_SCRUB` / `_SCRUB_STATEMENT`** rather than typed literally, the
    one derivation under which a drifting constant is silent instead of red — is
    now in the contract and not yet in the mirror. No instance exists in the table
    today; this is a one-clause addition to a comment, not a fix. *Owner:* **item
    1's / item 14's card**, whichever pass next opens the file; item 10's
    live-promotion card is an equally valid carrier and would meet the comment
    anyway.

16. **`prove_failability.py`'s verdict arithmetic has no row-isolation case.**
    *Source:* integration pass `## Review (Worker 3)` `### The four proofs, run`,
    and that pass's audit of it. *Spec licence:* none — a tooling observation, not
    spec work. *Description:* the tool labels a one-row result `WEAKLY PINNED -
    revision-needed` because its arithmetic is written for boundary proofs, where
    one row means one assertion holds a guard. A **row-isolation** proof — "does
    this row produce a failing id no other row produces" — seeks exactly one row,
    and a second would falsify it, so the tool's line reads as a finding against a
    proof that succeeded. Twice now a pass has had to write a paragraph explaining
    that the verdict does not apply. Catalogued as a decided observation, not as
    work: `scripts/` is outside this cycle's write set and the judgement may be
    better left to the reader than encoded. *Owner:* nobody — recorded as decided;
    raise it at close-out if the shape recurs.

---

## Spec changes made (Worker 1 only)

**None at this pass.** Per `worker-1.md` `## Spec status-line re-verification
(every Worker 1 spawn)` the spec's header and `Status:` lines were re-read at the
start of this gate: the opener, the version-boundary paragraph and the `Status:`
line all describe the current tree — the `Status:` line already names the
post-cut extension "skips a panel whose key cannot name a node rather than
raising out of the patched globals", which is Cohort C's landed code. Nothing the
gate found falsifies a spec sentence, so no edit was owed and none was made. The
rationale companion likewise needed no append: the gate introduced no decision.

---

## Final status

`final-accepted`.

Every gate in the scoped set is green, and each one's corpus is stated rather
than implied: 86/86 focused rows with 0 collection errors, `ruff format --check`
and `ruff check` clean across 444 files, `git diff --check` clean tree-wide, 24
spec glossary terms resolved, 992 citations resolved, and the source-layout
check clean over its real four-file corpus (with gate 8 recorded as "not read"
rather than as a pass). No floor verification was owed and none was skipped. No
live mutation is in the tree: the asset's SHA-256 matches every recorded
post-revert hash, no `ACTIVE-MUTATION.json` exists, and the middleware's
docstring-stripped AST is byte-for-byte HEAD's at 12,387 characters, re-derived
here rather than accepted from the artifact that first claimed it.

The 16-item deferred catalog is carried, superseding Cohort C's 11, with the
discharged items marked as discharged so nothing closed reads as open, with the
owner rule cited to `START.md` rather than `AGENTS.md`, and with the five items
that have no board home grouped into three maintainer decisions.

**The cycle is ready to hand to the maintainer for commit.** Eleven paths,
enumerated above; the other 67 dirty paths are a concurrent session's and must
not be staged or reverted. Worker 0 may mark the final checkbox.

**Worker 1 does not commit. Only the maintainer commits.**

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
