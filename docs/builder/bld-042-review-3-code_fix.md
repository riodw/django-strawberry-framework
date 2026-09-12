# Build: Review round 1, Cohort C — code fix (spec-042 debug toolbar)

Spec reference: `docs/SPECS/spec-042-debug_toolbar-0_0_14.md` (`## Borrowing posture`,
Decision 5, Decision 6, `## Edge cases and constraints`, `## Test plan` Tests 13a and 16,
`## Definition of done`)
Build plan: `docs/builder/build-042-debug_toolbar-0_0_14.md` (`## Cohort returns` → Cohort B,
`## Maintainer decisions taken mid-cycle`, `## Items Cohort A routed to Worker 0`)
Review under repair: `docs/builder/bld-042-review-2-code_verification.md` (M1–M4)
Status: final-accepted

Cohort C of the spec-042 post-ship reconciliation cycle: the code-fix pass Cohort B's
`revision-needed` dispatched. Its write set, per the build plan's `## Ownership partition`:

- `django_strawberry_framework/middleware/debug_toolbar.py` (Worker 2)
- `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
  (Worker 2 — the one file the maintainer widened the fence by; build plan
  `## Maintainer decisions taken mid-cycle` item 1)
- `tests/middleware/test_debug_toolbar.py` (Worker 2)
- `docs/builder/temp-tests/042/` (Worker 2 / Worker 3 scratch; the failability manifest lives at
  `docs/builder/temp-tests/042/proofs.json` and may replace Cohort B's)
- `docs/SPECS/spec-042-debug_toolbar-0_0_14.md` and
  `docs/SPECS/appx/spec-042-debug_toolbar-0_0_14-rationale.md` (Worker 1 only)
- this artifact; `docs/builder/worker-memory/042-worker-{1,2,3}.md` (each its own)

Nothing else. Still fenced OUT: `docs/GLOSSARY.md`, `docs/README.md`, `README.md`,
`docs/TREE.md`, `KANBAN.md` / `KANBAN.html`, `TODAY.md`, `CHANGELOG.md`,
`examples/fakeshop/db.sqlite3`, `examples/fakeshop/test_query/test_debug_toolbar_api.py`,
`tests/test_ci_governance.py`, `django_strawberry_framework/utils/imports.py`, and every
closeout / agentflow doc. The 53 baseline-dirty paths are a concurrent session's; never edit,
never revert (`AGENTS.md` rule 34). All three Cohort C source/test files were byte-identical to
`git show HEAD:` when this plan was written, so Cohort C collides with nobody.

Planning-pass verification (2026-09-11): `cmp` of each in-scope file against its `git show HEAD:`
copy → identical; spec 151,018 bytes and rationale 50,563 bytes before this pass's edits;
Cohort B's manifest `docs/builder/temp-tests/042/proofs.json` and report present; no
`ACTIVE-MUTATION.json` under the scratch root.

---

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Refreshed for the whole package (`docs/shadow/helper-inventory.md`,
  2,080 lines, generated this pass from `django_strawberry_framework/` recursively). Shapes
  searched: `template`, `encod`, `hint`, `floor`, `install`, `asset`, `require_`. Relevant hits:
  `django_strawberry_framework/utils/imports.py::CHANNELS_FLOOR` / `::STRAWBERRY_FLOOR` (the
  interpolated-floor-constant shape the router's hints use, gated by
  `tests/test_ci_governance.py::test_channels_floor_constant_matches_the_pyproject_dependency_row`
  and `::test_strawberry_floor_constant_matches_the_pyproject_dependency_row`);
  `django_strawberry_framework/middleware/debug_toolbar.py::require_debug_toolbar` (the guard
  itself). No package helper touches the JavaScript asset (the package carries no JS besides it),
  so nothing in the inventory can own M3's guard. Test-side inventory (grep, not AST):
  `tests/middleware/test_debug_toolbar.py::_FakeToolbar` / `::_FakePanel` (reused as-is),
  `tests/test_routers.py` #"Path(inspect.getfile(module)).read_text()" (the one other
  read-the-source-text pin in the suite), and the two governance rows above (the regex-over-
  `pyproject.toml` idiom).
- **Existing patterns reused.**
  - `tests/test_ci_governance.py:838-871` — the exact `re.findall(r'"<name>>=([0-9][^"]*)"', text)`
    idiom over `pyproject.toml`; M4's gate row copies the idiom, comparing the row to the
    module's own hint rather than to a `utils/imports.py` constant (see "New helpers", below).
  - `tests/middleware/test_debug_toolbar.py:284-323` — the parametrize-with-`ids` shape of
    `test_encoded_response_gets_no_package_mutation`; M1 widens the same test, no new test.
  - `tests/middleware/test_debug_toolbar.py:249-263` — `_FakeToolbar`, protocol-complete for the
    stock `_postprocess`; every M1 row keeps using it.
  - The asset's own record predicate `data === null || typeof data !== "object"`
    (`debug_toolbar.html:18-19`) is the idiom M3 generalizes; see the JS helper below.
- **New helpers justified.**
  1. **`isRecord(value)` inside the template IIFE** (JavaScript): `value !== null && typeof value
     === "object"`. Single responsibility: "can keys be read from this value without a
     `TypeError`". Four call sites once M3 lands — the entry guard on `data`, the captured
     `toolbar`, `toolbar.panels`, and each `panel` inside the loop. Without it the asset would
     spell the same predicate four times, and a reviewer could not tell whether the four agree.
     The entry guard keeps its `Object.prototype.hasOwnProperty.call(data, "debugToolbar")`
     clause; only its null/typeof half moves into the helper.
  2. **A module-level table of template predicates** in `tests/middleware/test_debug_toolbar.py`
     — `_TEMPLATE_CONTRACT: tuple[tuple[str, Callable[[str], bool]], ...]` (name free; see
     discretion) — feeding ONE parametrized test with `ids=` taken from the table. Single
     responsibility: the template contract as data, one row per predicate, so the failing-row
     count tracks the number of dropped guards (M2). Ordering predicates (`text.index(a) <
     text.index(b)`) and absence predicates (`x not in text`) are rows in the same table.
  3. **No** Python constant for the toolbar floor. The DRY end-state for M4 is the router's
     shape — a `DEBUG_TOOLBAR_FLOOR` beside `CHANNELS_FLOOR` in `utils/imports.py`, interpolated
     into the hint, gated by a governance row — but `utils/imports.py` and
     `tests/test_ci_governance.py` are outside Cohort C's write set, and the hint literal is
     already single-sited in the module (D2). The gate this cohort owes (the pyproject row must
     agree with the hint) is landed in-file; the relocation of the literal is a refinement
     routed under `### Notes for Worker 1`, not a deferred fix — nothing about M4's defect
     (a false population count, an ungated pin) survives it. Condition that would justify the
     shared constant: a fourth soft dependency, or the DRF hint getting the same governance row,
     at which point three hard literals in three leaves is the duplication and `utils/imports.py`
     is its owner.
  4. **No** shared "read pyproject" test helper. Two call sites in two files today; extract into
     `tests/_soft_dependency.py` (or a sibling) the day a third soft dependency gets the row.
- **Duplication risk avoided.**
  - Do not leave the monolithic `test_template_port_invariants_and_robustness_divergence` body
    beside the new table: the table REPLACES the body. The test keeps its name (so the
    `::Symbol` citations in the rationale and both closed cohort artifacts stay valid) and
    becomes the parametrized consumer of the table.
  - Do not add a second encoded-body test: M1 is a widening of the existing one (two encodings
    × two paths, bodies changed, a positive control added per row).
  - Do not spell the record predicate more than once in the asset (helper 1).
  - Do not hand-roll the proof loop; `scripts/prove_failability.py` with one manifest.
  - Single-cohort partition at this point in the cycle (A and B are closed), so there is no
    shared shape to assign across cohorts.

### Review helper

`scripts/review_inspect.py` — **skipped with reason**: the plan adds no executable logic to any
package `.py`. The only package-Python edits are a module docstring paragraph and one comment
block in `django_strawberry_framework/middleware/debug_toolbar.py`; the executable change is in a
`.html` asset the helper cannot parse. Worker 3 may still run it on the test file if it wants the
repeated-literal signal; nothing here requires it.

### Contracts, per dispatched item

`BUILD.md`: a prescribed fix is a hypothesis, not an instruction. Each item below states the
contract that must hold, the rows that must exist and what each fails FOR, and what would make
the fix incomplete. Code shapes are sketches Worker 2 may improve on, subject to the contract.

#### M1 — the `Content-Encoding` bail must be pinned by rows that fail only because it is gone

Boundary: `django_strawberry_framework/middleware/debug_toolbar.py::DebugToolbarMiddleware._postprocess`
#"Content-Encoding" (the one occurrence of that token in the module is the guard line).

**Contract.** With the early return deleted, the HTML-append site and the JSON-re-encode site
must EACH produce failing rows at the recorded scope, and every failing row must fail because
the guard is gone and for no other reason. That means each row's body is one its mutation path
would otherwise accept — a decodable JSON **object** for the JSON path (Cohort B proved
`b"\x1f\x8bencoded-json"` never reaches injection: `_get_payload`'s decode bail returns `None`
first), plain HTML for the HTML path — and the `Content-Encoding` header is the ONLY thing
standing between the request and the rewrite. The spec's Test 13a also says "parametrized over
more than one encoding so the guard rests on the header's presence rather than one value"; the
shipped test uses `gzip` alone.

**Rows.** `tests/middleware/test_debug_toolbar.py::test_encoded_response_gets_no_package_mutation`
widened to the product of {HTML append, JSON injection} × {`gzip`, `br`} = four rows, ids of the
form `graphiql_html_append-gzip`, `operation_json_injection-br`, and so on. JSON rows use a body
such as `b'{"data": {"x": 1}}'`; HTML rows keep a plain `<html>…</html>` body. **Each row carries
its own positive control:** the same request and an identical body WITHOUT the header, driven
through `_postprocess` first, must be mutated (template marker present / `debugToolbar` key
present); only then does the row drive the header-bearing twin and assert byte-identity and no
`debugToolbar`. The control is what makes the row distinguishing by construction rather than by
argument — a row whose control cannot fail is a passing proof of nothing (`START.md`
`## Instruments that lie`). Docstring rewritten to say exactly that (the current docstring's
"reaches BOTH mutation sites" is the claim Cohort B falsified).

**What fails for what.** Guard deleted → all four rows fail (HTML rows: marker appended into an
"encoded" body; JSON rows: payload injected). Decode bail deleted → none of these rows change
(bodies are decodable), which is the point: the two guards are now measured by disjoint row sets.

**Incomplete if:** any row's body still fails `_get_payload` on its own; a single encoding;
the positive control omitted or asserted only loosely (it must assert the mutation happened, not
merely that no exception was raised); fewer than two failing rows per mutation site.

#### M2 — the template contract must be one row per predicate, so a dropped guard fails its own rows

Boundaries: every family the asset's port checklist names (spec `## Borrowing posture`) — the
five preserved invariants and the diverged forms, now seven with M3.

**Contract.** Removing any one guard family from the asset must fail at least two node ids and
must not touch the rows that belong to the other families. `BUILD.md` #"A **test row** is one
failing test node id" makes a longer assertion list inside one test worthless; parametrization is
the only shape that raises the count.

**Rows.** `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence`
keeps its name and becomes `@pytest.mark.parametrize(("name", "predicate"), _TEMPLATE_CONTRACT,
ids=[...])` over a module-level table; the body is `template = <read the asset once>; assert
predicate(template), name`. Reading the asset per row is fine (89 lines); a module-scoped fixture
is equally fine. Every assertion in the current body becomes its own row with a readable id, and
the following rows are ADDED so no family sits at one row:

- **Reviver forwarding** (2 rows already: the `function ()` signature; the
  `origParse.apply(this, arguments)` body).
- **Membership-guard safety** (3 rows already: `hasOwnProperty.call`, `typeof data !== "object"`,
  plus — after helper 1 — the `isRecord(data)` call at the entry guard replaces the raw typeof
  spelling; pin whichever spelling lands, and pin `function isRecord(value)` once).
- **Mandatory scrub ordering** — currently ONE ordering assertion (`delete` before the
  null-handle bail), which is exactly one row and therefore weakly pinned after the split. Add
  ordering rows for every early return and DOM write that follows the scrub: scrub < null-handle
  bail; scrub < payload-shape guard (M3); scrub < `Object.entries(toolbar.panels)`; scrub <
  `djDebug.setAttribute("data-request-id"`. Reverting the scrub to upstream's position (after
  the DOM work) then fails four rows, not one.
- **Best-effort per-panel DOM** (2 rows: `.forEach(` and `if (content === null) return;`; plus
  the M3 per-panel record guard rows below).
- **Shadow-DOM handle resolution** (5 rows: `getElementById("djDebugRoot")`, `shadowRoot`,
  `querySelector("#djDebug")`, the `djdt-${id}` lookup on `djDebug`, the absence of
  `document.getElementById(\`djdt-${id}\`)`).
- **Per-node null guards** (12 rows, one per `const …`/`if (… !== null)` pair as today).
- **Payload-shape guard** (M3, below).
- **Preserved invariants** (one row each: `JSON.parse = function ()`, `Response.prototype.json =
  function`, `delete data.debugToolbar`, the `setAttribute("data-request-id", toolbar.requestId)`
  write, `heading.textContent = panel.title`, `subtitle.textContent = panel.subtitle`).

**What fails for what.** See `### Failability-proof obligations`: each family gets its own
mutation and must fail ≥2 rows drawn only from its own group.

**Incomplete if:** the monolithic body survives beside the table; any family's mutation fails
one row; a row's id is an integer index rather than a name (Worker 3 and Worker 1 difference
node-id SETS, and `[3]` names nothing after the table is reordered); the scrub-ordering family
has fewer ordering rows than there are post-scrub sites.

#### M3 — `update()` must return the scrubbed data for any `debugToolbar` value it cannot read, and never throw out of the patched globals

Defect: `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
#"Object.entries(toolbar.panels).forEach". `update()` guards `data` three ways and never guards
the value under the key: a `null`, scalar, or `panels`-less `debugToolbar` throws `TypeError`
out of the globally patched `JSON.parse` / `Response.prototype.json` — after the scrub, so the key
is already gone, but the caller's parse breaks. Upstream carries the identical hole
(`~/projects/strawberry-django-main/strawberry_django/templates/strawberry_django/debug_toolbar.html`
#"Object.entries(data.debugToolbar.panels).map("), so this is the borrow's flaw the divergence
family exists to fix, not a port regression. One level down, the same hole repeats: a `panels`
entry whose value is `null` throws at `panel.title`.

**Contract (written against the ANSWER, per `BUILD.md` `### Fail-open shapes`).** The question
the DOM block asks is "can I read keys from this value". The guard answers exactly that, at every
read site, with one predicate — `isRecord(value)` = `value !== null && typeof value === "object"`
— and never enumerates spellings of bad input (`null`, string, missing `panels`, …). Concretely:

1. The scrub stays unconditional and first: `const toolbar = data.debugToolbar; delete
   data.debugToolbar;` before any return that follows the entry guard. **The `debugToolbar` key
   is deleted from the response even when the payload is malformed** — the family's stated rule,
   "payload scrubbing is mandatory, DOM updates are best-effort", is the contract this guard must
   preserve, not relax.
2. After the scrub, the DOM work proceeds only when `isRecord(toolbar) && isRecord(toolbar.panels)`;
   otherwise `return data` (the scrubbed object). Whether this check sits before or after the
   `if (djDebug === null) return data;` bail is Worker 2's (both are "return the scrubbed data"
   and neither depends on the other); the ordering rows pin scrub < both.
3. Inside the loop, a panel entry is read only when `isRecord(panel)`; otherwise that iteration
   is skipped (`return;` inside the `forEach` callback) — one panel skipped, never the request.
4. The entry guard on `data` uses the same helper for its null/typeof half, so the asset spells
   the predicate once.
5. `djDebug.setAttribute("data-request-id", toolbar.requestId)` stays as upstream wrote it.
   Considered and kept: `setAttribute` coerces a non-string value and never throws for a value,
   so a missing `requestId` degrades to a toolbar panel miss ("isn't available anymore"), which is
   the stock toolbar's own fallback and not a crash. Recorded in the rationale so it is not
   re-raised as a defect.

Sketch (a hypothesis, not a script):

```javascript
function isRecord(value) {
  return value !== null && typeof value === "object";
}
function update(data) {
  if (!isRecord(data) || !Object.prototype.hasOwnProperty.call(data, "debugToolbar")) {
    return data;
  }
  const toolbar = data.debugToolbar;
  delete data.debugToolbar;
  if (djDebug === null) return data;
  if (!isRecord(toolbar) || !isRecord(toolbar.panels)) return data;
  Object.entries(toolbar.panels).forEach(([id, panel]) => {
    if (!isRecord(panel)) return;
    ...
```

Rejected shapes, so they are not re-fought (the rationale carries them too): a `try { … } catch
{}` around the DOM block — a bare catch converts "the check blew up" into "passed" and would hide
a real toolbar-DOM bug behind a silent no-op (`BUILD.md` `### Fail-open shapes`, bare `except`);
enumerating `toolbar === null || typeof toolbar === "string" || !("panels" in toolbar)` — a guard
against input spellings, the exact insufficiency the section's worked example shows.

**Rows (text-identity; the suite has no JS runtime — see the JS-runtime item homed at close-out
in the build plan).** In the M2 table:

- `payload-shape-guard-present`: the `isRecord(toolbar) || … isRecord(toolbar.panels)` guard line
  is present (pin the exact spelling Worker 2 lands).
- `payload-shape-guard-after-scrub`: `delete data.debugToolbar` index < guard index.
- `payload-shape-guard-before-panel-loop`: guard index < `Object.entries(toolbar.panels)` index.
- `panel-record-guard-present`: `if (!isRecord(panel)) return;` (or the landed spelling) present.
- `panel-record-guard-first-in-loop`: its index is greater than the `.forEach(` index and less
  than the `if (panel.title)` index.
- `is-record-helper-defined-once`: `template.count("function isRecord(") == 1`.
- `no-post-scrub-read-of-data-debugtoolbar`: `"data.debugToolbar.panels" not in template` and
  `"data.debugToolbar.requestId" not in template` (upstream's post-scrub reads).

**What fails for what.** Deleting the toolbar/panels guard fails `…-present`, `…-after-scrub`,
`…-before-panel-loop` (3 rows; the two ordering rows raise `ValueError` from `.index`, which is a
failure). Deleting the per-panel guard fails `panel-record-guard-present` and
`panel-record-guard-first-in-loop` (2 rows). Reverting the guard to an input-spelling enumeration
fails `…-present` and `is-record-helper-defined-once`'s siblings only if Worker 2 pins the
`isRecord(` call spelling — do so.

**Incomplete if:** the guard reads `data.debugToolbar` after the scrub instead of the captured
`toolbar`; the scrub becomes conditional on the shape; the per-panel level is left unguarded
(`Object.entries({a: null})` → `panel.title` throws — same class, one door further in); a
`try/catch` lands; any of the rows above is missing; the M2 split lands without these rows in the
same table.

#### M4 — the "three places that must agree" comment must stop publishing a count nothing gates

Site: `django_strawberry_framework/middleware/debug_toolbar.py` #"three-places-that-must-agree"
(the comment block above `_DEBUG_TOOLBAR_INSTALL_HINT`) and its mirror
`tests/middleware/test_debug_toolbar.py` #"three-places-that-must-agree" (above
`_HINT_SUBSTRING`).

**The decision.** Cohort B measured `django-debug-toolbar>=7.0.0` at five live sites: the three
the comment names (`pyproject.toml` dev-group row, the hint string, the re-typed test literal)
plus `docs/GLOSSARY.md` and `docs/README.md`. Two of the five are fenced out of this cycle, so
"correct all five" is not available — and would be the wrong answer anyway: **a published count
of a population nothing gates is a self-falsifying instrument.** The comment's count was right
when written and wrong the day the docs restated the floor; "five" would rot the same way. The
fix has two halves, both in-fence:

1. **State the GATED population by mechanism, not by count.** The comment (both sites) says: the
   floor is written in the hint, re-typed as `_HINT_SUBSTRING` in the package test (the
   drift-catch), and pinned in `[dependency-groups].dev`; the test file compares all three
   (the hint-matching rows compare hint ↔ literal, the new row compares literal ↔ `pyproject.toml`
   row). Then: **anything else that restates the floor — documentation included — is ungated;
   a floor bump sweeps the tree for the `django-debug-toolbar>=` specifier rather than trusting
   this comment's enumeration.** No numeral for the population; the enumeration of what is gated
   is the claim, and it is the claim the test proves.
2. **Add the missing gate for the one ungated in-fence pair.** Today NOTHING compares the
   `pyproject.toml` row against the hint or the literal (the existing rows only match hint ↔
   literal), so `pyproject.toml` could move alone. New row
   `tests/middleware/test_debug_toolbar.py::test_install_hint_floor_matches_the_pyproject_dev_group_row`:
   read `pyproject.toml` (`Path(__file__).resolve().parents[2] / "pyproject.toml"`), assert
   `re.findall(r'"(django-debug-toolbar>=[0-9][^"]*)"', text) == [_HINT_SUBSTRING]`, and assert
   `_HINT_SUBSTRING in toolbar_leaf._DEBUG_TOOLBAR_INSTALL_HINT`. Same idiom as
   `tests/test_ci_governance.py::test_channels_floor_constant_matches_the_pyproject_dependency_row`,
   whose docstring already names this defect class ("how the router's 'three places that must
   agree' comment came to name the wrong number of places"). Docstring of the new row says what
   it gates and what it cannot see (the docs).

**Rows / what fails for what.** Mutating the hint's `>=7.0.0` → `>=7.0.1` fails the three
existing hint-matching rows AND the new row (4 rows). Mutating the `pyproject.toml` row alone
fails exactly the new row — one row, by design: it is a governance pin over a non-production
file, the same single-row shape as the two `test_ci_governance.py` precedents, and the
weakly-pinned rule attaches to production boundaries, of which the pyproject row is not one.
Record that reading in the proof entry's why line rather than adding a second pyproject row for
the number's sake.

**Incomplete if:** the comment still states a numeral for the whole population (three OR five);
either comment site is left unchanged; the new row compares only literal ↔ pyproject and not
literal ↔ hint; the spec's `## Slice checklist`, Decision 5, `## Risks` and DoD sentences still
frame the three as the WHOLE population (Worker 1's edits below).

#### The stale docstring line — the module docstring must enumerate the Python divergences by name and stop closing the world

Site: `django_strawberry_framework/middleware/debug_toolbar.py` #"No other Python behavior" (the sentence wraps onto the next source line, so the citation quotes
the half that sits on one line) — the last paragraph of the module docstring, which says "two narrow, deliberate
robustness divergences" and calls the template "the third documented divergence".

**Contract.** The paragraph enumerates the module's Python divergences BY NAME — the
`isinstance(view, type)` guard in `process_view`; `_get_payload`'s response-shape bails
(undecodable / unparseable / non-object, one family, as Cohort A narrowed F7); the
`Content-Encoding` bail in `_postprocess` — and points at the template's guard family as
documented in spec-042 `## Borrowing posture` without counting its members. The closing sentence
"No other Python behavior differs." is deleted: a closed-world claim over a population nothing
gates is the M4 shape again, and this exact sentence has already been false once. No bare
numeral for either population; the enumeration is the claim.

**Proof (docstring-only edit).** `START.md` `## Instruments that lie`: a comment/docstring-only
edit owes the INVERSE proof — AST identity with docstrings stripped. Worker 2 records, for the
`.py` file, that `ast.dump()` of the module with every docstring node removed is identical
between `git show HEAD:django_strawberry_framework/middleware/debug_toolbar.py` (written to the
scratchpad) and the working file. Comments never reach the AST, so the M4 comment edit is covered
by the same comparison. This is the proof that Cohort C changed no Python behavior — which is
also what licenses the hot-path and floor declarations below.

**Incomplete if:** a numeral replaces "two"; the closed-world closer survives in any wording;
the template count is stated in the docstring; the AST-identity record is missing.

### Implementation steps

Line numbers are pin-at-write-time hints against the HEAD-identical files; verify before editing.

1. **Template** (`debug_toolbar.html`, 89 lines): add `isRecord` inside the IIFE near
   `getDjDebug()` (lines 7-13); rewrite the entry guard (lines 17-23) onto it; insert the
   payload-shape guard after the scrub (lines 30-33); insert the per-panel record guard as the
   first statement of the `forEach` callback (line 35-36). Leave `setAttribute` (line 73) as is.
   Fix Cohort B's L1 while there (`const origJson = Response.prototype.json` lacks its semicolon,
   line 82) — one character, in the same asset, and the asset's whole test story is "no silent
   drift"; record it as a Low closed in passing.
2. **Test file — M2/M3**: replace the body of
   `test_template_port_invariants_and_robustness_divergence` (lines 469-544) with a module-level
   predicate table plus the parametrized consumer; every current assertion becomes a named row;
   add the scrub-ordering rows and the seven M3 rows listed above. Keep the function name.
   Update the module docstring's paragraph that maps the split (lines 10-17) only if the new rows
   change what it says; it lists branches, not node ids, so it likely stands.
3. **Test file — M1**: widen `test_encoded_response_gets_no_package_mutation` (lines 284-323) to
   four rows with the positive control inside each row; bodies per the M1 contract; docstring
   rewritten.
4. **Test file — M4**: rewrite the `_HINT_SUBSTRING` comment (lines 56-60); add
   `test_install_hint_floor_matches_the_pyproject_dev_group_row` next to the guard-unit tests
   (after line 224 is the natural home — it is a guard-contract row, not a coverage unit).
   `import re` joins the imports.
5. **Middleware module — M4 + docstring**: rewrite the comment block at lines 62-67; rewrite the
   docstring paragraph at lines 35-45 per the contract; touch nothing executable.
6. **Manifest**: write `docs/builder/temp-tests/042/proofs.json` (replacing Cohort B's is fine;
   its report is preserved in `bld-042-review-2-code_verification.md`) with the nine entries in
   `### Failability-proof obligations`; run `uv run python scripts/prove_failability.py
   docs/builder/temp-tests/042/proofs.json --scratch-root <outside the repo> --output
   docs/builder/temp-tests/042/proofs-report-cohort-c.md`; paste the emitted block into
   `### Failability proofs`.
7. **AST-identity proof** for the `.py` file (the docstring contract above); record command and
   result under `### Failability proofs` as its own entry.
8. `uv run ruff format <the test file>` and `uv run ruff check --fix <the test file>` — scoped,
   never `.`; then `uv run python scripts/check_trailing_commas.py --check <the .py files
   touched>` — explicit paths ALWAYS (its default is a repo-wide auto-fix over the concurrent
   session's files). `git status --short` afterwards must show only Cohort C's files changed
   beyond the baseline.
9. Tick the checklist boxes whose contract landed; append the build report; set `Status: built`.

### Test additions / updates

- `tests/middleware/test_debug_toolbar.py::test_encoded_response_gets_no_package_mutation` —
  four rows, positive control per row (M1).
- `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence`
  — parametrized over `_TEMPLATE_CONTRACT`, ~40 named rows (M2 + M3).
- `tests/middleware/test_debug_toolbar.py::test_install_hint_floor_matches_the_pyproject_dev_group_row`
  — new (M4).
- No live-tier change: `examples/fakeshop/test_query/test_debug_toolbar_api.py` is not in the
  write set and nothing here is reachable through a live request the tier does not already
  drive (an encoded `/graphql/` response and a malformed `debugToolbar` payload are both
  unreachable from fakeshop's shipped wiring — spec Test 13a and the JS-runtime item).
- Temp tests for Worker 3: Cohort B's
  `docs/builder/temp-tests/042/test_encoded_json_row_is_nondistinguishing.py` is the
  before-picture of M1; Worker 3 may re-run it against the widened rows to confirm the
  `operation_json_injection-*` bodies now return an injected payload from `_get_payload`.

### Failability-proof obligations

`scripts/prove_failability.py` is the supported way; manifest home
`docs/builder/temp-tests/042/proofs.json`; scratch root OUTSIDE the repo; every anchor asserted
to match exactly once (`--check-anchors-only` first). **Reuse Cohort B's scope verbatim** —
`-n0 tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py`
— so Worker 3 and Worker 1 can difference node-id SETS against Cohort B's record (27 passed, exit
0, 0 collection errors) rather than compare numbers; the post-split baseline will be larger, and
the tool records its own pre-mutation baseline per entry. Node ids listed, never counted;
collection/setup errors recorded separately (a valid count requires 0); revert proved by byte
comparison (the tool's `filecmp` + SHA-256). Anchors below are described by content; Worker 2
fills the exact post-edit text.

| # | Boundary | Mutation (removes the boundary; not a perturbation) | Rows expected, and from which group only |
| --- | --- | --- | --- |
| 1 | `…debug_toolbar.py::DebugToolbarMiddleware._postprocess` `Content-Encoding` bail | delete the two-line guard + `return response` | ≥4: all `test_encoded_response_gets_no_package_mutation[*]` rows |
| 2 | asset — reviver forwarding | restore upstream `JSON.parse = function (text) { return update(origParse(text)); }` | ≥2: the reviver rows |
| 3 | asset — membership-guard safety | restore upstream `if (data === null \|\| !data.hasOwnProperty("debugToolbar")) return data;` | ≥2: membership rows (`hasOwnProperty.call`, `isRecord(data)`) |
| 4 | asset — mandatory scrub ordering | move `delete data.debugToolbar` to upstream's position (after `setAttribute`) | ≥4: every scrub-ordering row |
| 5 | asset — best-effort per-panel DOM | restore upstream `.map(` with the `content === null` skip removed | ≥2: `.forEach(` row, content-null row |
| 6 | asset — shadow-DOM handle resolution | collapse `getDjDebug()` to `return document.getElementById("djDebug");` (Cohort B entry 3) | ≥3: `djDebugRoot`, `shadowRoot`, `querySelector("#djDebug")` rows |
| 7 | asset — per-node null guards | restore the chained `content.querySelector(".djDebugPanelTitle").querySelector("h3").textContent = panel.title;` (Cohort B entry 4) | ≥4: `panelTitle`/`heading` rows |
| 8 | asset — payload-shape guard (NEW, M3) | delete the `isRecord(toolbar) … isRecord(toolbar.panels)` guard line | ≥3: present + two ordering rows |
| 9 | asset — per-panel record guard (NEW, M3) | delete `if (!isRecord(panel)) return;` | ≥2: present + first-in-loop rows |

Plus, outside the tool: (10) the hint-literal mutation for M4 (`>=7.0.0` → `>=7.0.1` in
`_DEBUG_TOOLBAR_INSTALL_HINT`; expected ≥4 rows: three hint-matching rows + the new pyproject
row) — this one CAN go in the manifest too, as entry 10; and (11) the AST-identity record for the
`.py` file (not a mutation; a docstring/comment-only proof).

**Acceptance (the weakly-pinned rule).** 0 or 1 failing rows on any entry 1-10 is
`revision-needed`. Expected counts and why they exceed one: entry 1 because two paths × two
encodings each fail independently once the bodies are acceptable; entries 2-9 because each family
is pinned by ≥2 predicates of which at least one is an ordering or absence row a substring copy
cannot satisfy; entry 10 because the hint is matched by three existing rows and the new gate.
Every entry's failing node ids must lie inside the group named for it — a row from another group
failing means the mutation removed more than its boundary and the entry is re-cut. Cohort B's
entries 3 and 4 measured exactly 1 each; entries 6 and 7 above are the same mutations and are the
direct before/after evidence that M2 is discharged.

**The pyproject-row mutation** (optional demonstration, not an acceptance entry): mutating
`pyproject.toml`'s dev-group row alone fails exactly the new governance row. Record it, if run,
with the reading in M4 above (governance pin over a non-production file; the precedent rows are
single by the same construction); do not add a second row to make the number two.

### Boundary count and the split decision

New boundaries Cohort C introduces: **two** (the payload-shape guard, the per-panel record
guard). Existing boundaries whose pinning Cohort C is the deliverable for: **eight** (the
`Content-Encoding` bail, the six shipped template families, the floor pin). Ten proof loops, one
manifest, one tool invocation. Above the "roughly five" prompt, so the split question is answered
in writing: **Cohort C is one unit.** What makes it one: nine of the ten loops mutate a single
89-line asset and are measured by a single test table in a single test file — splitting them puts
`tests/middleware/test_debug_toolbar.py` in two cohorts, which `BUILD.md` serializes anyway
("one shared file is enough"), so a split would cost an artifact and a cycle and buy no
concurrency and no smaller review surface (the table IS the review surface, and it must be read
whole to see that every family has ≥2 rows). The tenth loop (M1) is the one Python-side
boundary and could stand alone, but it is a widening of one existing test in the same file. The
overload risk `BUILD.md` names (proofs written from memory, reverts asserted in prose) is closed
by the tool: all ten run from one manifest with byte-compared restores, so the per-loop cost is
an anchor and a replacement string, not a hand-run cycle.

### Hot-path declaration

**None**, and it is not the cycle-level `none` restated — Cohort C is the only cohort that edits
code, so it is answered afresh. The asset runs in the browser on each `JSON.parse` /
`Response.prototype.json` call inside the GraphiQL page — a per-parse path, but client-side
JavaScript in a dev-only IDE page, which no metric this repo captures can measure and which adds
two `typeof` checks per payload. The Python edits are a docstring and a comment (AST-identical,
proved in step 7): no per-request, per-resolver, per-row, or per-connection Python path changes.
No proxy number is owed because no measurable path moved.

### Floor-verification scope

**None.** No Django / Strawberry / channels integration seam changes: the `.py` diff is
non-executable (AST-identity proof), the asset is browser-side, and the test rows drive
`RequestFactory` + the fake toolbar exactly as the shipped units do. Floor facts, read from
`BUILD.md` `## Floor verification` this pass, never from memory: Django **5.2.16** on Python
**3.10** with strawberry-graphql **0.316.0**. Cohort B already answered the one open floor
question (`from strawberry.django.views import BaseView` either resolves or the module fails at
import; no behavior depends on `0.262.0` vs `0.316.0`), and nothing Cohort C does reopens it.

### Implementation discretion items

Assessed and decided as Worker 2's; each is a choice between equally valid shapes under a stated
constraint, not an architectural question.

- **Name and type of the predicate table** (`_TEMPLATE_CONTRACT`, `_TEMPLATE_ROWS`, …; tuple of
  pairs vs. a dict). Constraint: row ids are human-readable names carried into pytest ids; one
  predicate per row; ordering and absence predicates are ordinary rows.
- **Where the payload-shape guard sits relative to the `djDebug === null` bail.** Either order;
  constraint: both after the scrub, both before the panel loop, both pinned by ordering rows.
- **How the asset is read in the parametrized test** (per row vs. a module-scoped fixture).
  Constraint: the path is computed from `django_strawberry_framework.__file__` as today.
- **The exact second encoding token** (`br` vs `deflate`) in M1. Constraint: two distinct
  values, both realistic `Content-Encoding` tokens.
- **Exact wording** of the rewritten comment and docstring, under the contracts above (no
  numeral for the population, no closed-world closer, enumeration by name).

### Dispatched findings checklist

One box per item Cohort C is dispatched, quoting the finding as Cohort B (or the routing note)
stated it, citing the symbol-qualified path. Boxes stay `- [ ]` at planning; Worker 2 ticks only
what its diff lands; Worker 3 walks the list; Worker 1 audits every tick at final verification.

- [x] **M1** — "the `Content-Encoding` bail is weakly pinned, and its second parametrize row is
      non-distinguishing" — the `[operation_json_injection]` body `b"\x1f\x8bencoded-json"` "is
      not decodable as UTF-8, so `_get_payload`'s own decode bail … returns `None` and the
      response is left alone whether or not the encoding guard exists".
      `django_strawberry_framework/middleware/debug_toolbar.py::DebugToolbarMiddleware._postprocess`
      #"Content-Encoding";
      `tests/middleware/test_debug_toolbar.py::test_encoded_response_gets_no_package_mutation`.
- [x] **M2** — "both post-ship template boundaries rest on a single test node id … removing
      *any* template boundary scores exactly 1 row, and removing all of them still scores 1".
      `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence`;
      `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
      #"function getDjDebug()" and #"const panelTitle = content.querySelector".
- [x] **M3** — "`update()` guards the shape of `data` but not the shape of `data.debugToolbar`, so
      a malformed payload throws out of the patched global `JSON.parse`" — "`update` returns the
      scrubbed `data` for *any* `debugToolbar` value it cannot use, and never throws out of the
      patched globals". `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
      #"Object.entries(toolbar.panels).forEach".
- [x] **M4** — "the 'three places that must agree' comment names a population of three; there
      are five" — "the comment states the true population, or the package stops enumerating it
      and points at whatever compares the sites". `django_strawberry_framework/middleware/debug_toolbar.py`
      #"three-places-that-must-agree"; `tests/middleware/test_debug_toolbar.py`
      #"three-places-that-must-agree".
- [x] **Stale docstring line** (routed by Cohort A) — "`No other Python behavior differs.` still
      closes the module docstring's divergence enumeration, which the `Content-Encoding` bail
      falsifies"; the module's Python divergence count is three (isinstance guard, response-shape
      bails, `Content-Encoding` bail), not four. `django_strawberry_framework/middleware/debug_toolbar.py`
      #"No other Python behavior" (the quoted sentence wraps across two source lines).

### Spec changes made (Worker 1 only)

The maintainer asked for the plan to be incorporated into the spec. **Ordering, stated
honestly:** these edits describe a contract Worker 2 has not yet landed. Nothing is committed
until the maintainer commits the whole cycle, so spec and code reach HEAD together — but the
spec now leads the tree, and **Worker 1's final-verification pass must re-audit every sentence
below against what actually landed** (the guard's spelling, the row names, the comment's wording)
and correct the spec if the implementation settled differently. Every edit states the corrected
contract directly: no amendment block, no "previously six", no round or cohort provenance
(`AGENTS.md` rule 27; `BUILD.md` `## Spec rationale extraction`).

Census before editing (`START.md`: shortest distinctive phrase, occurrences not lines, every site
asserted to exist before any write): `six` as a word — **3** occurrences in the spec (lines 637,
1898, 2050), 0 in the rationale outside sentences that quote the retired count; `four-guard` —
0 in the spec (Cohort A retired it); `no behavioral change` — 1 (line 275, the slice-checklist
template box); `three-places-that-must-agree` — 2 (lines 231, 1075); `single-valued across three
places` — 1 (line 1985). Retirement targets after this pass: `six` as a template count → 0 in
the spec; `no behavioral change` → 0; the three-places sites reworded so none frames the three as
the whole population (the phrase itself may survive where it names the gated trio).

Spec edits (`docs/SPECS/spec-042-debug_toolbar-0_0_14.md`):

1. **`Status:` line** — the post-cut extension clause gains "and ignores a `debugToolbar` payload
   it cannot read". *M3.*
2. **`## Slice checklist`, Slice-1 template box** — "with no behavioral change" → "carrying the
   documented guard divergences"; a slice-checklist box gets no vintage licence and the sentence
   was false against six divergences before it was false against seven. *M3 sweep.*
3. **`## Slice checklist`, Slice-1 dependency-gate box** — the closing "three-places" sentence now
   names the gated trio and says everything else restating the floor is swept, not enumerated.
   *M4.*
4. **Decision 5, item 3** — same reframing of "the three-places-that-must-agree rule holds". *M4.*
5. **`## Borrowing posture`** — "six spots" → "seven spots"; a seventh bullet, **Payload-shape
   guard**, stating the contract in M3's terms (one record predicate at every read site; scrub
   unconditional; a payload the DOM update cannot read returns the scrubbed data; a panel entry
   that is not a record skips one panel). The closing "Test 16 pins …" sentence names the new
   form. *M3.*
6. **`## Edge cases and constraints`** — a new bullet, **A `debugToolbar` value the bridge cannot
   read.** *M3.*
7. **`## Test plan`, Test 13a** — parametrized over two encodings AND both mutation paths, with
   bodies each path would otherwise accept and a positive control per row. *M1.*
8. **`## Test plan`, Test 16** — one row per predicate (a parametrized table with named ids), the
   seven diverged forms enumerated, ordering rows for every post-scrub site, the M3 rows named.
   *M2, M3.*
9. **`## Test plan`, guard-unit shape** — a new item 12a: the pyproject dev-group row agrees with
   the re-typed literal and the hint. *M4.*
10. **`## Risks and open questions`** — "The floor is single-valued across three places" bullet
    reframed: the three gated sites are named as gated, the doc restatements as swept. *M4.*
11. **`## Definition of done`** — "the six documented guard divergences" → "seven"; the test item
    names the parametrized template guard and the pyproject-row gate; the floor item's "the
    dev-group specifier, the hint string, and the re-typed test literal agree" sentence gains
    "gated by the package test". *M2, M3, M4.*

Rationale edits (`docs/SPECS/appx/spec-042-debug_toolbar-0_0_14-rationale.md`):

12. **`## Post-ship corrections`** — a new `### M3 — …` entry in the file's *Claimed / HEAD /
    Cause* shape (the opener's "Nine findings … all nine are spec-only" sentence corrected to
    admit the one code-side correction), keyed to `## Borrowing posture` by heading and anchor.
13. **`### Borrowing posture — the template port`** — a change record: the family grew a third
    time; why the guard is a record predicate applied at every read site (guard the answer);
    upstream carries the identical hole (cited); rejected: the `try/catch`, the input-spelling
    enumeration, guarding `requestId`; the `setAttribute` coercion kept upstream-verbatim.
14. **`### Decision 5 — Soft django-debug-toolbar dependency`** — a change record on the
    three-places rule: the trio was the gated population and was read as the whole population;
    the docs restate the floor ungated; the pyproject ↔ hint pair was itself ungated until the
    governance row; the claim the decision may no longer make.
15. **`### Decision 6`** — the change record's closing sentence extended: the docstring's "No
    other Python behavior differs" is retired in favour of enumeration by name.

`check_spec_glossary` (24 terms), `check_citations`, `check_trailing_commas --check <both
files>` and `git diff --check` results are recorded under `### Planning-pass gates` below.

### Notes for Worker 1 (spec reconciliation)

Items this planning pass surfaces for Worker 0 to route or for final verification to carry:

1. **The same false-population comment exists for DRF.**
   `django_strawberry_framework/rest_framework/__init__.py` #"three-places-that-must-agree" and
   `tests/rest_framework/test_soft_dependency.py` #"three-places-that-must-agree" name three
   places for `djangorestframework>=3.17.0`, and — unlike Channels and Strawberry — no
   `test_ci_governance.py` row gates the DRF pyproject row against its hint. Same defect class as
   M4, different spec (spec-039). Out of this cycle's single-spec scope → deferred-work catalog
   in `bld-042-final.md`, needs a named owner with that write set.
2. **The DRY end-state for the toolbar floor** is `DEBUG_TOOLBAR_FLOOR` in `utils/imports.py`
   interpolated into the hint and gated beside the Channels/Strawberry rows in
   `tests/test_ci_governance.py`. Not a deferred fix (M4's defect is closed in-file); a refinement
   whose trigger is stated under `### DRY analysis`. Catalog it with that framing so it is not
   re-raised as a duplication finding against this cohort.
3. **M4's documentation half** — `docs/GLOSSARY.md` (DB-backed; ORM edit + regenerate) and
   `docs/README.md` restate `django-debug-toolbar>=7.0.0`. Correct today; ungated forever. Fenced
   out → deferred-work catalog, as Cohort B already routed.
4. **The JS-runtime question** is homed at close-out by maintainer decision (build plan item 2);
   M2/M3's text-identity rows do not change what is proved and the plan says so above.
5. **Cohort B's L1** (the missing semicolon) is folded into step 1; **L2** (`if (panel.subtitle)`
   never clears an emptied subtitle) stays upstream-verbatim by Cohort B's own recommendation and
   is not touched.
6. **Two citation defects seen in passing, neither this cohort's to fix.** (a) The spec cites
   `utils/imports.py::require_optional_module` twice (DoD and the Slice-1 module box) with a
   package-relative path rather than the rule-27 repo-relative form; present at HEAD before this
   cycle, unread by `check_citations.py` (docs are out of its scope), Low. (b) The build plan and
   Cohort A's artifact quote `#"No other Python behavior differs."` as one substring, but the
   sentence wraps across two source lines in the docstring (`START.md`: quote text on ONE source
   line); this artifact cites the on-one-line half instead. Both closed/Worker-0 files; recorded so
   the final gate does not rediscover them.

---

## Planning-pass gates (Worker 1)

Run after the spec and rationale edits, 2026-09-11.

| Gate | Command | Result |
| --- | --- | --- |
| Spec glossary | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-042-debug_toolbar-0_0_14.md` | `OK: 24 terms - all have glossary entries and at least one spec link.` |
| Citations | `uv run python scripts/check_citations.py --check` | `OK: 991 citations resolve (822 in 441 .py files, 169 in KANBAN.md).` — reads `.py` + `KANBAN.md` only; says nothing about the three files this pass wrote |
| Source layout | `uv run python scripts/check_trailing_commas.py --check <spec> <rationale> <this artifact>` | exit 0 (the artifact is reported "excluded from the source-layout rules"; both standing files pass) |
| Whitespace | `git diff --check -- docs/SPECS/spec-042-debug_toolbar-0_0_14.md` | clean; the rationale and this artifact are untracked, so a trailing-whitespace grep stood in (0 hits) |
| Rule-27 citations (own verifier, both forms, against the tree) | scratchpad script over spec + rationale + artifact | spec: 0 problems in this pass's additions (2 pre-existing `utils/imports.py::…` package-relative cites, see Notes 6); rationale: 0 problems, every `path::Symbol` and `path #"substring"` resolves, 0 nested-quote substrings, 0 `path:NN`, 0 wrapped citations; artifact: 1 planned-not-landed symbol (`::test_install_hint_floor_matches_the_pyproject_dev_group_row`, expected until Worker 2 lands it) |
| Link convention (own verifier) | scratchpad script | spec 73 uses / 73 defs, rationale 26 / 26 (the new `[edge-cases]` def resolves to `#edge-cases-and-constraints`), 0 broken in-page anchors, 0 orphan / undefined refs, ten group headers in order, groups sorted, in all three files |
| Retirement census | `grep -o -w` occurrences, not lines | spec: `six` as a word 3 → **0**; `no behavioral change` 1 → **0**; `single-valued across three places` 1 → **0**; `three-places-that-must-agree` 2 → 2, both sites now naming the gated trio rather than the population; `seven` 0 → 3 (Borrowing posture, Test 16, DoD); round / cohort / "previously" provenance in the spec → **0**. Rationale: `six` survives at three sites, each inside a sentence recording the retired count (F8's HEAD line, M3's *Claimed* line, M3's "first six forms") |

Byte counts: spec 151,018 → 156,997; rationale 50,563 → 57,951. Every in-scope source / test
file is still byte-identical to `git show HEAD:` — this pass wrote no source and no tests.

`Status: planned`. Next: Worker 0 dispatches Worker 2 against `## Plan (Worker 1)`.

---

## Build report (Worker 2)

Built against `## Plan (Worker 1)`. All five dispatched items landed; nothing deferred. Every
in-scope file was byte-identical to `git show HEAD:` when this pass started (re-verified with
`cmp` against scratchpad copies before the first edit), so nothing here collided with the
concurrent spec-050 session.

### Files touched

From `git status --short`, restricted to this cohort's write set. Every other modified path in
that output is the concurrent session's baseline-dirty work — neither edited nor reverted
(`AGENTS.md` rule 34); that set has GROWN since the plan's snapshot and now also carries
`django_strawberry_framework/keyset.py`, `resource_policy.py`, `types/finalizer.py` and several
more `tests/` files.

- `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html` —
  **M3**, the one executable change in the pass. Adds `isRecord(value)` inside the IIFE
  (`value !== null && typeof value === "object"`), rewrites the entry guard's null/typeof half
  onto it, inserts `if (!isRecord(toolbar) || !isRecord(toolbar.panels)) return data;` after the
  scrub and before the panel loop, and makes `if (!isRecord(panel)) return;` the first statement
  of the `forEach` callback. The scrub stays unconditional and first;
  `djDebug.setAttribute("data-request-id", toolbar.requestId)` stays upstream-verbatim with a
  comment recording why (`setAttribute` coerces a non-string value and never throws for one).
  Cohort B's **L1** closed in passing: `const origJson = Response.prototype.json` gained its
  missing semicolon.
- `django_strawberry_framework/middleware/debug_toolbar.py` — **M4 + the stale docstring line.**
  Non-executable only. The module docstring's last paragraph now enumerates the Python
  divergences BY NAME (the `isinstance(view, type)` guard, `_get_payload`'s response-shape bail
  family, the `Content-Encoding` bail) and points at the template's guard family as enumerated in
  spec-042 `## Borrowing posture` without counting its members; `No other Python behavior
  differs.` is deleted and no numeral replaced `two`. The `_DEBUG_TOOLBAR_INSTALL_HINT` comment
  now names the three GATED sites and what compares them, then states that anything else
  restating the floor — documentation included — is gated by nothing, so a bump sweeps the tree
  for the `django-debug-toolbar>=` specifier instead of trusting the enumeration. Proved
  AST-identical to HEAD with docstrings stripped (`### Failability proofs`, entry 11).
- `tests/middleware/test_debug_toolbar.py` — **M1, M2, M3, M4.** `import re`; the
  `_HINT_SUBSTRING` comment reframed the same way as the module's; the encoded-response test
  widened to four rows with a per-row positive control; the monolithic template test replaced by
  a module-level `_TEMPLATE_CONTRACT` table of 41 named predicates feeding one parametrized
  consumer that keeps the old function name; one new governance row for the `pyproject.toml`
  dev-group specifier.
- `docs/builder/temp-tests/042/proofs.json` — the ten-entry manifest (replaces Cohort B's; its
  report survives at `proofs-report.md` and inside `bld-042-review-2-code_verification.md`).
  Emitted report: `docs/builder/temp-tests/042/proofs-report-cohort-c.md`. Both gitignored
  scratch.
- This artifact; `docs/builder/worker-memory/042-worker-2.md`.

The module docstring's **first** line is unchanged, so the `docs/TREE.md` row it renders is
unchanged and no regenerate is owed — which matters, because `docs/TREE.md` is fenced out of this
cycle and is itself baseline-dirty. Same for the test module's first docstring line.

### Tests added or updated

- `tests/middleware/test_debug_toolbar.py::test_encoded_response_gets_no_package_mutation`
  (**M1**) — `{graphiql_html_append, operation_json_injection}` x `{gzip, br}` = four rows.
  Bodies are ones each mutation path would otherwise accept: `b"<html><body>ide</body></html>"`
  for the append, `b'{"data": {"x": 1}}'` for the re-encode (Cohort B proved
  `b"\x1f\x8bencoded-json"` never reaches injection — `_get_payload`'s decode bail returns `None`
  first). **Each row drives its own positive control first**: the same request and body with no
  `Content-Encoding` header, asserting the mutation actually happened (`was_mutated` is
  `_html_was_appended` / `_payload_was_injected` per row); only then the header-bearing twin,
  asserting `result is response`, byte-identity, `not was_mutated(...)`, and no `debugToolbar`
  key. Docstring rewritten to state that contract; the falsified "reaches BOTH mutation sites"
  claim is gone.
- `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence`
  (**M2 + M3**) — same name, now
  `@pytest.mark.parametrize(("name", "predicate"), _TEMPLATE_CONTRACT, ids=[...])` over a
  module-level table; body is `assert predicate(_template_text()), name`. 41 rows, every id a
  readable name. Rows per family: preserved invariants 7; membership guard 2; null-handle-bail
  presence 1 plus mandatory-scrub ordering 4; best-effort per-panel loop 2; shadow-DOM handle 5;
  per-node null guards 12; payload-shape / `isRecord` family 8. Predicate helpers `_present`,
  `_absent`, `_defined_once`, `_ordered` — the last variadic, and **returning `False` rather than
  raising** when a needle is missing, so a row that a dropped guard makes unanswerable fails under
  its own name instead of erroring out of the parametrized body.
- `tests/middleware/test_debug_toolbar.py::test_install_hint_floor_matches_the_pyproject_dev_group_row`
  (**M4**, new) — reads `pyproject.toml` via `Path(__file__).resolve().parents[2]`, asserts
  `re.findall(r'"(django-debug-toolbar>=[0-9][^"]*)"', text) == [_HINT_SUBSTRING]` and
  `_HINT_SUBSTRING in toolbar_leaf._DEBUG_TOOLBAR_INSTALL_HINT`. Same
  regex-over-`pyproject.toml` idiom as
  `tests/test_ci_governance.py::test_channels_floor_constant_matches_the_pyproject_dependency_row`.
  Its docstring says what it gates and what it cannot see.
- **No live-tier change.** `examples/fakeshop/test_query/test_debug_toolbar_api.py` is not in the
  write set and nothing here is reachable through a live request the tier does not already drive.

Node-id arithmetic at the recorded scope, so the difference against Cohort B's record is
re-derivable rather than asserted: Cohort B measured **27 passed, exit 0, 0 collection errors**;
this pass measures **70 passed, exit 0, 0 collection errors** at the identical scope.
`27 + 40` (template test 1 row -> 41) `+ 2` (encoded test 2 rows -> 4) `+ 1` (the new governance
row) `= 70`. No row was removed and none renamed away.

### Validation run

- `uv run ruff format django_strawberry_framework/middleware/debug_toolbar.py tests/middleware/test_debug_toolbar.py` — pass (scoped to this pass's files, never `.`).
- `uv run ruff check --fix <the same two files>` — `All checks passed!`.
- `uv run python scripts/check_trailing_commas.py --fix <the same two files>` — `Fixed 1 file(s).`
  (exploded the 4-element parametrize name tuple; collapsed one over-exploded 2-element row).
  Explicit paths always, never the repo-wide auto-fix default.
- Re-verified read-only afterwards: `ruff format --check` (`2 files already formatted`);
  `ruff check` (`All checks passed!`);
  `check_trailing_commas.py --check <both .py files + the .html>` exit 0;
  `git diff --check -- <the three files>` exit 0.
- `uv run python scripts/check_citations.py --check` —
  `OK: 991 citations resolve (822 in 441 .py files, 169 in KANBAN.md)`. The planning pass's one
  known-unresolved citation (`::test_install_hint_floor_matches_the_pyproject_dev_group_row`) now
  resolves.
- `uv run pytest -n0 tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py --no-cov` — **70 passed**, exit 0, 0 collection errors. No `--cov*` flag was used anywhere in this pass.
- `git status --short` after both ruff invocations: exactly the three tracked files of this
  cohort's write set are modified, plus the four untracked `docs/builder/{build,bld}-042-*` files
  this cycle created. Everything else modified is the concurrent session's — recorded, not
  touched. Nothing unexpected to stop-and-report.

### Failability proofs

Procedure, mechanized by `scripts/prove_failability.py`: the target is copied to a scratch path OUTSIDE the repo before any mutation; the mutation site is located by an exact anchor asserted to match exactly once (any other count aborts the entry without writing); the same focused scope is run unmutated first, so rows already failing before the mutation are differenced out of the count; both runs' pytest exit codes are read, because a run that collected nothing or blew up emits no `FAILED` lines and would otherwise be recorded as a measured zero; both runs use `--no-cov`; the file is restored from the pre-mutation copy in a `finally` and the restore is proved by `filecmp.cmp(shallow=False)` plus a SHA-256 comparison. One boundary at a time, restored before the next. `git` is never invoked - the tree is legitimately dirty, so an empty `git diff` is unachievable and forcing one would destroy the build's own work.

| # | Boundary | File mutated | Mutation applied | Rows failed | Errors | Scope as run | Restore proof |
|---|---|---|---|---|---|---|---|
| 1 | `django_strawberry_framework/middleware/debug_toolbar.py::DebugToolbarMiddleware._postprocess (Content-Encoding bail)` | `django_strawberry_framework/middleware/debug_toolbar.py` | deleted: `if response.get("Content-Encoding", ""): return response` - builder's description (unverified prose): the Content-Encoding early-return deleted, so an already-encoded body reaches both mutation sites | **4** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE -n0 tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py` | filecmp.cmp(shallow=False) True; sha256 5c189885117946d2... == 5c189885117946d2... (vs pre-mutation copy) |
| 2 | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"JSON.parse = function ()" (reviver forwarding)` | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html` | `const origParse = JSON.parse; JSON.parse = function () { return update(origParse.apply(this, arguments)); };` -> `const origParse = JSON.parse; JSON.parse = function (text) { return update(origParse(text)); };` - builder's description (unverified prose): the argument-forwarding wrapper reverted to upstream's verbatim single-argument form, which drops a page-wide JSON.parse(text, reviver)'s reviver | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE -n0 tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py` | filecmp.cmp(shallow=False) True; sha256 a1431798b18787cf... == a1431798b18787cf... (vs pre-mutation copy) |
| 3 | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"!Object.prototype.hasOwnProperty.call(data" (membership-guard safety)` | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html` | `if ( !isRecord(data) || !Object.prototype.hasOwnProperty.call(data, "debugToolbar") ) { return data; }` -> `if (data === null || !data.hasOwnProperty("debugToolbar")) { return data; }` - builder's description (unverified prose): the entry guard reverted to upstream's verbatim form, which throws for a null-prototype object or one shadowing hasOwnProperty | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE -n0 tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py` | filecmp.cmp(shallow=False) True; sha256 a1431798b18787cf... == a1431798b18787cf... (vs pre-mutation copy) |
| 4 | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"delete data.debugToolbar" (mandatory scrub, before every post-scrub site)` | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html` | deleted: `delete data.debugToolbar;` - builder's description (unverified prose): the unconditional scrub deleted, so the server-only debugToolbar key survives every early return and every DOM write and leaks back to GraphiQL | **5** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE -n0 tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py` | filecmp.cmp(shallow=False) True; sha256 a1431798b18787cf... == a1431798b18787cf... (vs pre-mutation copy) |
| 5 | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"if (content === null) return;" (best-effort per-panel DOM)` | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html` | `Object.entries(toolbar.panels).forEach(([id, panel]) => { if (!isRecord(panel)) return; if (panel.title) { const cont...` -> `Object.entries(toolbar.panels).map(([id, panel]) => { if (!isRecord(panel)) return; if (panel.title) { const content ...` - builder's description (unverified prose): the skip-on-absent-content-node removed and the side-effect loop reverted to upstream's .map, so a payload panel missing from the toolbar DOM throws inside the patched JSON.parse | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE -n0 tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py` | filecmp.cmp(shallow=False) True; sha256 a1431798b18787cf... == a1431798b18787cf... (vs pre-mutation copy) |
| 6 | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"function getDjDebug()" (shadow-DOM handle resolution)` | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html` | `function getDjDebug() { const rootEl = document.getElementById("djDebugRoot"); if (rootEl !== null && rootEl.shadowRo...` -> `function getDjDebug() { return document.getElementById("djDebug"); }` - builder's description (unverified prose): the shadow-root lookup removed, reverting to light-DOM-only resolution that returns null on a default USE_SHADOW_DOM=True toolbar | **3** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE -n0 tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py` | filecmp.cmp(shallow=False) True; sha256 a1431798b18787cf... == a1431798b18787cf... (vs pre-mutation copy) |
| 7 | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"const panelTitle = content.querySelector" (per-node null guards)` | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html` | `const panelTitle = content.querySelector(".djDebugPanelTitle"); if (panelTitle !== null) { const heading = panelTitle...` -> `content .querySelector(".djDebugPanelTitle") .querySelector("h3").textContent = panel.title;` - builder's description (unverified prose): the panelTitle/heading null guards removed, restoring the chained assignment that throws a TypeError inside the patched JSON.parse when one node is absent | **4** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE -n0 tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py` | filecmp.cmp(shallow=False) True; sha256 a1431798b18787cf... == a1431798b18787cf... (vs pre-mutation copy) |
| 8 | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"!isRecord(toolbar) || !isRecord(toolbar.panels)" (payload-shape guard)` | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html` | deleted: `if (!isRecord(toolbar) || !isRecord(toolbar.panels)) return data;` - builder's description (unverified prose): the payload-shape guard deleted, so a null / scalar / panels-less debugToolbar value reaches Object.entries and throws out of the patched globals | **3** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE -n0 tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py` | filecmp.cmp(shallow=False) True; sha256 a1431798b18787cf... == a1431798b18787cf... (vs pre-mutation copy) |
| 9 | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"if (!isRecord(panel)) return;" (per-panel record guard)` | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html` | deleted: `if (!isRecord(panel)) return;` - builder's description (unverified prose): the per-panel record guard deleted, so a panels entry whose value is null or a scalar throws at panel.title inside the patched globals | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE -n0 tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py` | filecmp.cmp(shallow=False) True; sha256 a1431798b18787cf... == a1431798b18787cf... (vs pre-mutation copy) |
| 10 | `django_strawberry_framework/middleware/debug_toolbar.py #"pip install 'django-debug-toolbar>=7.0.0'" (the floor's gated trio)` | `django_strawberry_framework/middleware/debug_toolbar.py` | `"with `pip install 'django-debug-toolbar>=7.0.0'` (the package's verified debug-toolbar "` -> `"with `pip install 'django-debug-toolbar>=7.0.1'` (the package's verified debug-toolbar "` - builder's description (unverified prose): the floor in the install hint moved alone to >=7.0.1, leaving the re-typed test literal and the pyproject.toml dev-group row behind | **4** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE -n0 tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py` | filecmp.cmp(shallow=False) True; sha256 5c189885117946d2... == 5c189885117946d2... (vs pre-mutation copy) |

Verdicts:

1. `django_strawberry_framework/middleware/debug_toolbar.py::DebugToolbarMiddleware._postprocess (Content-Encoding bail)` - pinned
2. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"JSON.parse = function ()" (reviver forwarding)` - inside Worker 3's mandatory re-run floor (<= 3 rows)
3. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"!Object.prototype.hasOwnProperty.call(data" (membership-guard safety)` - inside Worker 3's mandatory re-run floor (<= 3 rows)
4. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"delete data.debugToolbar" (mandatory scrub, before every post-scrub site)` - pinned
5. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"if (content === null) return;" (best-effort per-panel DOM)` - inside Worker 3's mandatory re-run floor (<= 3 rows)
6. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"function getDjDebug()" (shadow-DOM handle resolution)` - inside Worker 3's mandatory re-run floor (<= 3 rows)
7. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"const panelTitle = content.querySelector" (per-node null guards)` - pinned
8. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"!isRecord(toolbar) || !isRecord(toolbar.panels)" (payload-shape guard)` - inside Worker 3's mandatory re-run floor (<= 3 rows)
9. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"if (!isRecord(panel)) return;" (per-panel record guard)` - inside Worker 3's mandatory re-run floor (<= 3 rows)
10. `django_strawberry_framework/middleware/debug_toolbar.py #"pip install 'django-debug-toolbar>=7.0.0'" (the floor's gated trio)` - pinned

Failing node ids, per boundary (the count above is `len()` of this list):

1. `django_strawberry_framework/middleware/debug_toolbar.py::DebugToolbarMiddleware._postprocess (Content-Encoding bail)`
   - file mutated: `django_strawberry_framework/middleware/debug_toolbar.py`
   - pytest summary: `======================== 4 failed, 66 passed in 29.70s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `======================== 70 passed in 85.92s (0:01:25) =========================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/middleware/test_debug_toolbar.py::test_encoded_response_gets_no_package_mutation[graphiql_html_append-gzip]`
   - `tests/middleware/test_debug_toolbar.py::test_encoded_response_gets_no_package_mutation[graphiql_html_append-br]`
   - `tests/middleware/test_debug_toolbar.py::test_encoded_response_gets_no_package_mutation[operation_json_injection-gzip]`
   - `tests/middleware/test_debug_toolbar.py::test_encoded_response_gets_no_package_mutation[operation_json_injection-br]`
2. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"JSON.parse = function ()" (reviver forwarding)`
   - file mutated: `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
   - pytest summary: `======================== 2 failed, 68 passed in 26.39s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 70 passed in 27.76s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[json-parse-wrapper-signature]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[reviver-forwarded-via-apply]`
3. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"!Object.prototype.hasOwnProperty.call(data" (membership-guard safety)`
   - file mutated: `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
   - pytest summary: `======================== 2 failed, 68 passed in 24.62s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 70 passed in 25.48s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[entry-guard-uses-record-predicate]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[membership-guard-uses-hasownproperty-call]`
4. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"delete data.debugToolbar" (mandatory scrub, before every post-scrub site)`
   - file mutated: `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
   - pytest summary: `======================== 5 failed, 65 passed in 24.43s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 70 passed in 24.45s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[scrub-key-deleted]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[scrub-before-null-handle-bail]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[scrub-before-payload-shape-guard]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[scrub-before-panel-loop]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[scrub-before-request-id-write]`
5. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"if (content === null) return;" (best-effort per-panel DOM)`
   - file mutated: `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
   - pytest summary: `======================== 2 failed, 68 passed in 24.32s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 70 passed in 24.65s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[panel-loop-is-foreach]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[panel-loop-skips-absent-content-node]`
6. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"function getDjDebug()" (shadow-DOM handle resolution)`
   - file mutated: `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
   - pytest summary: `======================== 3 failed, 67 passed in 24.48s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 70 passed in 28.27s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[shadow-dom-root-lookup]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[shadow-dom-shadow-root-branch]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[shadow-dom-inner-query]`
7. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"const panelTitle = content.querySelector" (per-node null guards)`
   - file mutated: `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
   - pytest summary: `======================== 4 failed, 66 passed in 24.47s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 70 passed in 24.42s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[panel-title-node-lookup]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[panel-title-node-guarded]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[heading-node-lookup]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[heading-node-guarded]`
8. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"!isRecord(toolbar) || !isRecord(toolbar.panels)" (payload-shape guard)`
   - file mutated: `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
   - pytest summary: `======================== 3 failed, 67 passed in 24.38s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 70 passed in 24.43s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[scrub-before-payload-shape-guard]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[payload-shape-guard-present]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[payload-shape-guard-before-panel-loop]`
9. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"if (!isRecord(panel)) return;" (per-panel record guard)`
   - file mutated: `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
   - pytest summary: `======================== 2 failed, 68 passed in 24.84s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 70 passed in 27.15s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[panel-record-guard-present]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[panel-record-guard-first-in-loop]`
10. `django_strawberry_framework/middleware/debug_toolbar.py #"pip install 'django-debug-toolbar>=7.0.0'" (the floor's gated trio)`
   - file mutated: `django_strawberry_framework/middleware/debug_toolbar.py`
   - pytest summary: `======================== 4 failed, 66 passed in 24.35s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 70 passed in 24.40s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/middleware/test_debug_toolbar.py::test_leaf_import_raises_install_hint_when_toolbar_absent`
   - `tests/middleware/test_debug_toolbar.py::test_leaf_reimports_after_restore`
   - `tests/middleware/test_debug_toolbar.py::test_require_debug_toolbar_guard_unit`
   - `tests/middleware/test_debug_toolbar.py::test_install_hint_floor_matches_the_pyproject_dev_group_row`

A boundary whose removal fails 0 or 1 rows is **weakly pinned** and is `revision-needed` per `docs/builder/BUILD.md` - the fix is more or better-targeted rows, never a weaker boundary. A boundary at 3 rows or fewer is inside Worker 3's mandatory independent re-run floor. A proof carrying collection or setup errors, or whose pytest run exited anything but 0 or 1 (nothing collected, interrupted, internal error, usage error), is not a valid count at all - and a 0 from such a run is not a zero-row result: resolve it and re-run.

Every `<fill in ...>` above is a judgement no tool can make and MUST be replaced by hand before this subsection is submitted: weakly pinned and harness-impossible are the two possible readings of a zero-row result and they prescribe opposite responses (more rows, versus a production-call-site invariant assertion plus a recorded harness limitation), so a record that does not name one reads as self-contradictory.

**Entry 11 — the docstring/comment-only proof (not a mutation).** `START.md`
`## Instruments that lie` owes a comment/docstring-only edit the INVERSE proof, so:
`git show HEAD:django_strawberry_framework/middleware/debug_toolbar.py` was written to the
scratchpad (outside the repo) and both files parsed with `ast.parse`, every `Module` / `ClassDef`
/ `FunctionDef` / `AsyncFunctionDef` docstring node removed, then `ast.dump()` compared:

```
AST-identical (docstrings stripped): True
len(dump) a/b: 12387 12387
```

A whole-module `ast.unparse` diff of the two shows exactly one hunk, the docstring text itself
(comments never reach the AST, so the M4 comment rewrite is covered by the same comparison).
**This is the proof that Cohort C changed no Python behavior**, which is what licenses the
hot-path and floor-verification declarations below.

**Reading of the results.**

- No entry returned 0 or 1 rows, so nothing is weakly pinned and there is no **why 0** judgement
  to make — the emitted block carries no `<fill in …>` placeholder. Every pre-mutation baseline
  was `70 passed`, exit 0, 0 collection/setup errors, so every count is a valid count and no
  pre-existing failing row was differenced out.
- **M1 discharged:** the `Content-Encoding` bail went from Cohort B's 1 row to **4**, and every
  one of them is now distinguishing — both mutation sites fail, at both encodings, because each
  row's body is one its own path accepts and each row's positive control fired first.
- **M2 discharged:** Cohort B's entries 3 and 4 (the same two mutations as entries 6 and 7 here)
  measured **1 row each**. They now measure **3** and **4**, and every other template family is
  at 2 or more. The before/after is direct, at the same scope, on the same mutations.
- **M3 pinned:** the two new boundaries measure 3 (payload-shape guard) and 2 (per-panel record
  guard).
- **M4:** moving the hint's floor alone fails 4 rows — the three hint-matching rows plus the new
  governance row. The plan's optional demonstration (mutating the `pyproject.toml` row alone,
  expected to fail exactly the new row) was **not run**: `pyproject.toml` is outside this
  cohort's write set, and the entry-10 mutation already proves the pair is compared in both
  directions from inside the fence.
- **One deliberate cross-entry overlap:** `…[scrub-before-payload-shape-guard]` fails under both
  entry 4 and entry 8. That is the row's construction, not a mutation reaching past its boundary
  — the predicate names the scrub AND the guard, so removing either makes it unanswerable. No
  other entry's failing set contains a row from another family.
- Restores: `filecmp.cmp(shallow=False)` True plus a SHA-256 match against the pre-mutation copy
  on all ten. Independently re-confirmed after the run — the scratch root holds only `pristine/`
  and **no** `ACTIVE-MUTATION.json`, the hint reads `>=7.0.0` again, and the focused scope is
  back to 70 passed. **No mutated tree is handed to Worker 3.**

### Hot-path budget

**Not applicable; the plan declares no hot path**, and entry 11 is the evidence rather than an
assertion: the Python diff is AST-identical with docstrings stripped, so no per-request,
per-resolver, per-row or per-connection Python path moved. The asset's added cost is two `typeof`
checks per parsed payload in a dev-only browser page, which no instrument in this repo measures.

### Floor verification

**Not applicable; plan declares floor-verification scope `none`.** No Django / Strawberry /
channels integration seam changed (the `.py` diff is non-executable, the asset is browser-side,
and the new test rows drive `RequestFactory` plus the existing fake toolbar). Floor facts read
from `docs/builder/BUILD.md` `## Floor verification` this pass, never from memory: Django
**5.2.16** on Python **3.10** with strawberry-graphql **0.316.0**. Nothing here reopens Cohort
B's answered floor question.

### Implementation notes

- **`isRecord` placement.** Defined beside `getDjDebug()` at IIFE scope rather than inside
  `update`, so the four call sites share one definition and `is-record-helper-defined-once` can
  pin `template.count("function isRecord(") == 1`. The entry guard keeps its multi-line
  `if ( … || … )` shape (only the null/typeof half moved into the helper), which keeps the diff
  legible and the `Object.prototype.hasOwnProperty.call` clause on its own line for the row that
  pins it.
- **Guard ordering.** `if (djDebug === null) return data;` stays first and the payload-shape guard
  follows it — the plan left the order to discretion, requiring only that both sit after the
  scrub and before the loop. Both orderings are pinned by rows either way.
- **The second encoding is `br`** (plan discretion: `br` or `deflate`). Both are realistic
  `Content-Encoding` tokens; `br` is the one a real dev server is likelier to emit.
- **Stacked `parametrize` for M1** rather than a hand-written four-entry list, so the four ids
  read `[<path>-<encoding>]` and the path bodies stay written once.
- **`was_mutated` is a per-row callable**, not a marker string, because the two paths prove
  different mutations (template marker appended vs. `debugToolbar` key injected) and a single
  shared marker would make one row's control non-distinguishing.
- **`_ordered` is variadic and total.** Three-needle orderings (the per-panel record guard's
  position inside the loop) fall out of the same helper, and a missing needle yields `False`
  rather than a `ValueError`, so a row reports its own name.
- **Table rows are named, never indexed** — `BUILD.md` compares node-id SETS across passes, and
  `[3]` names nothing once the table is reordered.

### Notes for Worker 3

- The manifest is `docs/builder/temp-tests/042/proofs.json`; the emitted record is
  `proofs-report-cohort-c.md` beside it. Cohort B's `proofs.json` was replaced but its report
  (`proofs-report.md`) is untouched, so the before/after for M2 is readable without `git`.
  Re-run at the **recorded scope** — `-n0 tests/middleware/test_debug_toolbar.py
  examples/fakeshop/test_query/test_debug_toolbar_api.py` — and difference node-id sets; the
  baseline is 70, not Cohort B's 27, and the arithmetic for the delta is in
  `### Tests added or updated` above.
- Cohort B's temp probe `docs/builder/temp-tests/042/test_encoded_json_row_is_nondistinguishing.py`
  is the before-picture of M1 and still runs. Its
  `test_a_decodable_encoded_body_would_have_been_rewritten` is exactly the body shape the widened
  `operation_json_injection-*` rows now use.
- **Unusual control flow worth knowing:** entry 4's mutation **deletes** the scrub line rather
  than relocating it (see `### Notes for Worker 1`, item 1). If you re-run it, expect 5 rows, not
  the plan's predicted 4.
- The asset is still text-identity-tested only; no JS runtime was added (the plan and the build
  plan both home that question at close-out). Nothing in M3 is proved to *execute* correctly —
  only that the guard text is present, single-sited, and correctly ordered. Say so if you review
  it; do not read the 41 green rows as behavioural evidence.
- `_TEMPLATE_MARKER` does double duty: it is the M1 HTML-append control's marker AND is pinned as
  the `response-json-wrapper` row's needle. Deliberate (one distinctive substring of the asset),
  but it does couple the two tests to one string.

### Notes for Worker 1 (spec reconciliation)

1. **Small drift, plan `### Failability-proof obligations` row 4 — the mandatory-scrub mutation
   is a deletion, not a relocation.** The plan specified "move `delete data.debugToolbar` to
   upstream's position (after `setAttribute`)". `scripts/prove_failability.py` takes ONE
   contiguous anchor per entry, and in the shipped asset the scrub line and the `setAttribute`
   line are ~40 lines apart with the whole panel loop between them, so the relocation is two
   edits and cannot be one entry. Anchoring the whole span would mutate far more than the
   boundary. The mutation applied instead deletes the scrub line outright — a strictly stronger
   removal of the same boundary ("the scrub is unconditional and precedes every post-scrub
   site") — and it failed **5** rows, not the predicted 4, because the presence row goes with the
   four ordering rows. Recommended plan/spec wording, if either is restated: *"the mandatory
   scrub is proved by deleting it, which fails its presence row and every ordering row that names
   it."* No spec sentence currently states the mutation, so this may need no spec edit at all.
2. **Row naming, `## Test plan` Test 16 and the plan's M3 row list.** The plan named a row
   `payload-shape-guard-after-scrub` under M3 and a row `scrub < payload-shape guard` under the
   scrub-ordering family. Those are the same predicate over the same two needles, so it is landed
   **once**, as `scrub-before-payload-shape-guard`, and it fails under both boundaries' mutations.
   Not a dropped row. Test 16's own wording ("one row per early return and DOM write that follows
   the scrub … the payload-shape guard, its position after the scrub and before the panel loop")
   is already consistent with the single naming; no edit needed unless you want the id spelled.
3. **Two rows are anchored away from the obvious needle, deliberately, to keep the failing sets
   inside one family.** `panel-record-guard-first-in-loop` orders against
   `"Object.entries(toolbar.panels)"` rather than `".forEach("`, and `panel-title-write` /
   `panel-subtitle-write` pin `"textContent = panel.title"` / `"= panel.subtitle"` rather than
   `"heading.textContent = …"` / `"subtitle.textContent = …"`. Without this the
   best-effort-per-panel mutation (`forEach` -> `map`) and the per-node-guard mutation (the
   chained assignment, which still writes the title) would each fail a row belonging to another
   family, and `BUILD.md`'s acceptance reading would call the entry mis-cut. Nothing in the spec
   states a needle, so this is a note for your audit rather than an amendment.
4. **Spec sentences to re-audit against what landed** (the plan says final verification owes
   this, so here is the landed side):
   - `## Borrowing posture`, payload-shape bullet — landed verbatim as described: one record
     predicate `value !== null && typeof value === "object"`, **defined once as `isRecord`**,
     applied at the captured `toolbar`, its `panels`, and each `panel`; scrub unconditional and
     first; a malformed payload returns the already-scrubbed data; an unreadable panel entry
     skips one panel; `setAttribute` kept upstream-verbatim; no `try`/`catch`.
   - `## Borrowing posture`, "**seven** spots" — seven families are present in the asset and each
     is pinned by >= 2 rows, at least one of them an ordering or absence predicate.
   - `## Test plan` Test 13a — landed as two encodings x both mutation paths, bodies each path
     accepts, positive control inside each row.
   - `## Test plan` Test 16 — landed as one parametrized row per predicate with named ids.
   - `## Test plan` Test 12a and the DoD's "the package test compares all three" — landed as
     `::test_install_hint_floor_matches_the_pyproject_dev_group_row`, comparing the dev-group row
     to the re-typed literal AND the literal to the hint.
   - `## Edge cases and constraints`, "A `debugToolbar` value the bridge cannot read" — matches
     the landed behaviour exactly.
5. **Nothing this pass found changes the plan's own `### Notes for Worker 1` items 1–6.** The DRF
   false-population comment (`rest_framework/__init__.py`), the `DEBUG_TOOLBAR_FLOOR` refinement
   in `utils/imports.py`, and M4's documentation half (`docs/GLOSSARY.md` / `docs/README.md`) are
   all still out-of-fence and still owed a named owner in `bld-042-final.md`'s deferred-work
   catalog. The DRF one is now the **only** remaining "three places that must agree" comment in
   the package that states a closed population with no gate behind the `pyproject.toml` side —
   the toolbar's is closed by this pass.
6. **The baseline-dirty population has grown since the plan recorded 53 paths.** At the end of
   this pass `git status --short` shows additional concurrent-session files not in the plan's
   list (`django_strawberry_framework/keyset.py`, `resource_policy.py`, `types/finalizer.py`,
   `tests/test_keyset*.py`, `tests/optimizer/test_single_parent_fetch.py`,
   `tests/test_resource_policy.py`, `tests/utils/test_errors.py`, and more). None is in this
   cohort's write set and none was touched. Worth restating in the final gate rather than
   comparing against the plan's frozen count — a stale count is the instrument that would make
   an unexpected file look like this cohort's churn.

`Status: built`. Next: Worker 0 dispatches Worker 3 against this diff.

---

## Review (Worker 3)

Diff under review: `git diff HEAD --` restricted to Cohort C's three writable files —
`django_strawberry_framework/middleware/debug_toolbar.py` (40 lines changed, none executable),
`django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html` (28), and
`tests/middleware/test_debug_toolbar.py` (353). Nothing else in the working tree was read as
build output: the concurrent session's baseline-dirty set has grown past the plan's 53 paths and
now carries `keyset.py`, `resource_policy.py`, `types/finalizer.py`, `docs/GLOSSARY.md`,
`docs/TREE.md` and several live-tier test files; none was edited, reverted or reviewed
(`AGENTS.md` rule 34).

### Mutations recorded BEFORE they were made

`worker-3.md` "Scope" requires the carve-out's mutations to be recorded before they are applied.
Nine independent re-runs, listed here before the first was applied. Eight re-use Worker 2's
manifest entries verbatim so the node-id SETS are differenceable; the ninth is this pass's own.

**The mandatory floor** (`worker-3.md` "Reading is necessary, not sufficient": every boundary
recorded at 3 rows or fewer) is Worker 2's entries **2, 3, 5, 6, 8, 9**. Three more are re-run on
grounds rather than arithmetic: **entry 1** (M1's whole claim is that these four rows are now
distinguishing — the exact property Cohort B falsified for the old row), **entry 4** (the
disclosed deletion-instead-of-relocation deviation), and **entry 4b**, this pass's own mutation,
which performs the relocation Worker 2 could not express as one anchor.

| # | Boundary | Mutation to be applied | Source |
| --- | --- | --- | --- |
| 1 | `…debug_toolbar.py::DebugToolbarMiddleware._postprocess` #"Content-Encoding" | the two-line guard + `return response` deleted | Worker 2 entry 1, verbatim |
| 2 | `…/debug_toolbar.html` #"JSON.parse = function ()" | reviver forwarding reverted to upstream's `function (text) { return update(origParse(text)); }` | Worker 2 entry 2, verbatim |
| 3 | `…/debug_toolbar.html` #"!Object.prototype.hasOwnProperty.call(data" | entry guard reverted to upstream's `data === null \|\| !data.hasOwnProperty("debugToolbar")` | Worker 2 entry 3, verbatim |
| 4 | `…/debug_toolbar.html` #"delete data.debugToolbar" | the scrub line **deleted** | Worker 2 entry 4, verbatim |
| 4b | `…/debug_toolbar.html` #"delete data.debugToolbar" | the scrub line **relocated** to upstream's position, immediately after `djDebug.setAttribute("data-request-id", toolbar.requestId);`. Anchor is the 48-line span from the scrub to the `setAttribute` write; the replacement reproduces that span verbatim with the one line moved to its end, so the only thing removed is the ORDERING | **this pass** |
| 5 | `…/debug_toolbar.html` #"if (content === null) return;" | `.forEach(` → `.map(` and the content-null skip removed | Worker 2 entry 5, verbatim |
| 6 | `…/debug_toolbar.html` #"function getDjDebug()" | body collapsed to `return document.getElementById("djDebug");` | Worker 2 entry 6, verbatim |
| 8 | `…/debug_toolbar.html` #"!isRecord(toolbar) \|\| !isRecord(toolbar.panels)" | the payload-shape guard line deleted | Worker 2 entry 8, verbatim |
| 9 | `…/debug_toolbar.html` #"if (!isRecord(panel)) return;" | the per-panel record guard deleted | Worker 2 entry 9, verbatim |

Accepted on Worker 2's record without a re-run, and why: **entry 7** (per-node null guards, 4
rows — Cohort B independently measured the same mutation at 1 row against the pre-split test, so
the before/after is already two measurements, and the four recorded ids are all `panel-title-*` /
`heading-*` rows, which is the family the mutation touches) and **entry 10** (the floor's gated
trio, 4 rows — three of the four are pre-existing hint-matching rows that Cohort B already ran
green, and the fourth is the row this pass reads below in full). Both sit above the floor and
neither is a security or data-isolation decision.

Manifest: `docs/builder/temp-tests/042/proofs-worker3.json` (Worker 2's is preserved unchanged
beside it). Scratch root **outside** the repository. Anchors asserted to match exactly once
before any mutation — which is also what proves the tree was not already carrying a foreign live
mutation.

### Failability proofs (Worker 3 independent re-run)

Scope, identical for all nine and identical to Worker 2's record:
`uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE -n0
tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py`.
Pre-mutation state, measured fresh before every entry: **70 passed, exit 0, 0 collection/setup
errors** — nine times, so no pre-existing failing row inflates any count and the post-split
baseline Worker 2 recorded is confirmed independently. Emitted record:
`docs/builder/temp-tests/042/proofs-report-worker3.md`; tool exit **0**.

| # | Boundary | Rows | Failing node ids (all under `tests/middleware/test_debug_toolbar.py`) | vs Worker 2 |
| --- | --- | --- | --- | --- |
| 1 | `…debug_toolbar.py::DebugToolbarMiddleware._postprocess` (Content-Encoding bail) | **4** | `::test_encoded_response_gets_no_package_mutation[graphiql_html_append-gzip]`, `[graphiql_html_append-br]`, `[operation_json_injection-gzip]`, `[operation_json_injection-br]` | identical set |
| 2 | asset — reviver forwarding | **2** | `…divergence[json-parse-wrapper-signature]`, `[reviver-forwarded-via-apply]` | identical set |
| 3 | asset — membership-guard safety | **2** | `[entry-guard-uses-record-predicate]`, `[membership-guard-uses-hasownproperty-call]` | identical set |
| 4 | asset — mandatory scrub, **deleted** | **5** | `[scrub-key-deleted]`, `[scrub-before-null-handle-bail]`, `[scrub-before-payload-shape-guard]`, `[scrub-before-panel-loop]`, `[scrub-before-request-id-write]` | identical set |
| 4b | asset — mandatory scrub, **relocated** (this pass's own mutation) | **4** | `[scrub-before-null-handle-bail]`, `[scrub-before-payload-shape-guard]`, `[scrub-before-panel-loop]`, `[scrub-before-request-id-write]` | no counterpart; see `#### Deviation 1` |
| 5 | asset — best-effort per-panel DOM | **2** | `[panel-loop-is-foreach]`, `[panel-loop-skips-absent-content-node]` | identical set |
| 6 | asset — shadow-DOM handle resolution | **3** | `[shadow-dom-root-lookup]`, `[shadow-dom-shadow-root-branch]`, `[shadow-dom-inner-query]` | identical set |
| 8 | asset — payload-shape guard (M3, new) | **3** | `[scrub-before-payload-shape-guard]`, `[payload-shape-guard-present]`, `[payload-shape-guard-before-panel-loop]` | identical set |
| 9 | asset — per-panel record guard (M3, new) | **2** | `[panel-record-guard-present]`, `[panel-record-guard-first-in-loop]` | identical set |

Every restore proved inside the run by `filecmp.cmp(shallow=False) True` plus SHA-256 equality
against the pre-mutation copy (nine of nine). Post-run tree state, checked independently of the
tool: the scratch root holds `pristine/` and **no** `ACTIVE-MUTATION.json`, and the two mutated
files hash to `a1431798b18787cf…` (asset) and `5c189885117946d2…` (module) — **the same digests
Worker 2 recorded**, which is also what proves this review read the same bytes Worker 2 proved.
No mutation is live.

**Boundaries accepted on Worker 2's record, and why:** entry **7** (per-node null guards, 4 rows)
and entry **10** (the floor's gated trio, 4 rows). Both sit above the mandatory floor and neither
is a security or data-isolation decision. Neither was accepted on prose alone, though: entry 7's
recorded row set was reproduced by the second instrument below, and entry 10's four rows are
exactly the four `_HINT_SUBSTRING` positive comparisons in the file
(`tests/middleware/test_debug_toolbar.py` #"match=_HINT_SUBSTRING" three times, plus the new
governance row) — the fifth `_HINT_SUBSTRING` site is the broken-install row's *negative*
assertion, which correctly does not move when the hint's floor does.

**A second instrument, run on all eight template mutations.** `prove_failability.py` and the
predicate table are one instrument measured twice, so the row sets were also derived statically,
without pytest and without touching the tree: the landed `_TEMPLATE_CONTRACT` and its four
predicate helpers were extracted verbatim by `ast` and evaluated against in-memory mutated copies
of the asset (`docs/builder/temp-tests/042/worker3_replay_probe.py`,
`worker3_contract_table_probe.py`). It reproduces **all eight** template entries' node-id sets
exactly, entry 7 included. Zero rows fail on the unmutated asset.

**Entry 11, the docstring-only inverse proof, re-run rather than read.**
`git show HEAD:django_strawberry_framework/middleware/debug_toolbar.py` into the scratchpad
(outside the repo), both files `ast.parse`d, every `Module`/`ClassDef`/`FunctionDef`/
`AsyncFunctionDef` docstring node removed, `ast.dump()` compared: **identical, 12387 == 12387
characters**. Worker 2's figure reproduces exactly. This is the whole warrant for the hot-path
declaration and it holds: no Python behaviour moved, so `none` is correct for both the hot-path
and the floor-verification declarations, and the asset is browser-side.

#### Deviation 1 — the scrub mutation is a deletion, not the plan's relocation: audited, holds

The question is not whether deleting the scrub is *bigger* than relocating it. It is whether the
rows that failed are the rows that pin the boundary **Revision 8 exists to hold**, which is
`scrub BEFORE the bail`, not `scrub happens`. Under a deletion those are different claims: the
four ordering rows fail because `_ordered` returns `False` for a missing needle, i.e. because the
scrub is *absent*, not because it is *misordered*. A deletion therefore cannot by itself show
that the ordering predicates detect a reordering — which is exactly the "a wider mutation
re-proves a neighbouring guard" shape Cohort B's M1 was about.

So this pass ran the relocation Worker 2 could not express as one anchor (entry 4b above): the
48-line span from the scrub to the `setAttribute` write, replaced by itself with that one line
moved to upstream's position. **4 rows fail, all four of them ordering rows, and the presence row
`[scrub-key-deleted]` does not** — the ordering boundary is independently pinned at 4, above the
weakly-pinned threshold on its own. Worker 2's deletion is then a strict superset (the same four
plus the presence row), and its "strictly stronger removal" reading is correct as measured, not
just as argued. The static probe agrees: `relocated scrub -> 4 ordering rows`,
`deleted scrub -> those 4 plus scrub-key-deleted`.

The deviation is accepted, with one correction to the record for Worker 1: Worker 2's own
justification ("a strictly stronger removal of the same boundary") is true but was not
demonstrated by the entry it justifies. What demonstrates it is entry 4b.

#### Deviation 2 — two rows anchored away from the obvious needle: audited, each still pins its own claim

- **`panel-record-guard-first-in-loop`** orders `"Object.entries(toolbar.panels)"` →
  `"if (!isRecord(panel)) return;"` → `"if (panel.title)"` instead of anchoring on `".forEach("`.
  `"Object.entries(toolbar.panels)"` occurs exactly once in the asset (the `isRecord` guard spells
  `isRecord(toolbar.panels)`, which does not contain it), so the row still pins precisely what its
  name claims: the guard sits inside the loop and ahead of the first panel-key read. Anchoring on
  `".forEach("` would have made this row fail under the *per-panel-loop* mutation
  (`forEach` → `map`), putting a foreign row in that entry's failing set. Verified by the static
  replay: entry 5's failing set contains no `panel-record-*` row.
- **`panel-title-write` / `panel-subtitle-write`** pin `"textContent = panel.title"` /
  `"= panel.subtitle"` rather than the `heading.` / `subtitle.` receivers. Same reasoning: the
  per-node-guard mutation restores the chained upstream assignment, which still *writes the
  title*, so a receiver-anchored row would fail inside entry 7's set while belonging to the
  preserved-invariant family. What the row claims — the per-panel title write survives the port —
  is exactly what the needle pins; the receiver is pinned separately by `heading-node-lookup` and
  `heading-node-guarded`. Measured: dropping `heading.textContent = panel.title;` fails
  `panel-title-write` and nothing else.

Both anchorings are deliberate row hygiene, and both are correct.

#### M1: do the four rows fail for their own reason?

Cohort B's defect was a row refused earlier by a different guard. Re-checked directly against
`…debug_toolbar.py::DebugToolbarMiddleware._postprocess`, in source order: the `Content-Encoding`
bail sits ahead of the content-type sniff, so both rewrite sites are behind it, and each row's
body is one its own path accepts — `b"<html><body>ide</body></html>"` reaches the append
(`is_html and is_graphiql and status 200`), `b'{"data": {"x": 1}}'` decodes, parses and is a
`dict`, so `_get_payload` returns a payload rather than `None`. Neither body can be refused by the
decode bail. The **positive control inside each row** is what makes this structural rather than
argued: it drives the identical body with no header first and asserts the mutation actually
happened (`_html_was_appended` / `_payload_was_injected`), so a row whose body stopped being
acceptable fails loudly on its control instead of passing vacuously — `START.md`'s "control that
cannot fail ≡ passing proof", closed by construction. Measured: all four rows fail with the guard
gone, HTML and JSON alike.

On the `br` rows specifically: `br` does not reach a different branch — `if response.get(
"Content-Encoding", "")` is a truthiness test, so `br` and `gzip` take the same arm. What the
second value proves is that the guard rests on the header's *presence* and not on the literal
`"gzip"`, which is what the spec's Test 13a asks for; it does not add a second boundary, and this
review does not read it as one. The two *sites* (append, re-encode) are the independent halves,
and each contributes two rows.

### High:

None.

### Medium:

#### M3-1 — the table's own comment, and the spec sentence it mirrors, claim a property the table does not have

`tests/middleware/test_debug_toolbar.py` #"at least two rows, at least one of them an ordering"
(the block comment above `_TEMPLATE_CONTRACT`), mirrored in
`docs/SPECS/spec-042-debug_toolbar-0_0_14.md` `## Test plan` Test 16 #"Every form is pinned by at
least two rows".

Measured over the landed table (`ast` over the 41 rows, predicate constructor per row): **35 of
41 rows are plain `_present` substring checks.** The six that are not are four `_ordered` rows
(all in the scrub family), two `_absent` rows plus one more in the payload-shape family, and one
`_defined_once`. Per diverged form:

| Diverged form | Rows | Ordering / absence row? |
| --- | --- | --- |
| Reviver forwarding | 2 | **none** |
| Membership-guard safety | 2 | **none** |
| Mandatory scrub ordering | 5 | 4 `_ordered` |
| Best-effort per-panel DOM | 2 | **none** |
| Shadow-DOM handle resolution | 5 | 1 `_absent` |
| Per-node null guards | 12 | **none** |
| Payload-shape guard (M3) | 9 | 2 `_ordered`, 2 `_absent`, 1 `_defined_once` |

Four of the seven forms have no ordering or absence row at all, so the clause "at least one of
them an ordering or absence predicate that a stray substring elsewhere in the asset cannot
satisfy" is false for a majority of the families it is written over. The `>= 2 rows` half also
fails for three of the five **preserved invariants** if the sentence is read to cover them
(`response-json-wrapper`, `panel-title-write`, `panel-subtitle-write` are one row each — measured
by replaying each removal through the landed table: dropping the whole
`Response.prototype.json` wrapper block fails exactly `[response-json-wrapper]`, and dropping
`heading.textContent = panel.title;` fails exactly `[panel-title-write]`).

**Why this is Medium and not a nit.** This is the defect class the cohort exists to retire. M4 and
the docstring closer are both "a published claim nothing gates", and the pass that retires them
publishes a new one in the same file — a comment that tells the next editor the table resists a
stray substring when, for four of seven families, it does not. `START.md` #"Rule w/o gate rots"
and the repo's standing self-falsifying-instrument lesson apply unchanged, and a false claim is
worse than no claim because it reads as evidence the question was examined.

**Contract that must hold** (not a prescription of lines): every claim the table and Test 16 make
about the table is true of the landed table. Two ways to get there, and the first is worth more
than the correction:

1. **Add the missing rows, which are the silent-revert detectors this family exists for.** Every
   one of Worker 2's own template mutations restores *upstream's* spelling, and the table catches
   each only because the port's spelling vanished — nothing asserts upstream's form is absent. An
   `_absent` row per reverted form closes that and makes the comment true:
   `_absent('data.hasOwnProperty("debugToolbar")')` (membership), `_absent("update(origParse(text))")`
   (reviver), `_absent("Object.entries(toolbar.panels).map(")` (per-panel loop),
   `_absent('.querySelector(".djDebugPanelTitle").querySelector("h3")')` (per-node guards). Each is
   a needle upstream has and the port must not; each raises its family's failing-row count by one.
   A second row for the `Response.prototype.json` wrapper falls out of the same move
   (`_present("origJson.apply(this, arguments)")` pins that the wrapper forwards and calls
   `update`, which the presence row does not).
2. Or correct both sentences to state what the table actually does.

**Incomplete if:** the comment is edited and Test 16 is not, or the reverse; or a row is added
that repeats a needle an existing row already pins (the count must track guards, which is M2's
whole point).

### Low:

#### L3-1 — nothing pins that the scrub is *unconditional*, only that it is first

`django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
#"delete data.debugToolbar", against `docs/SPECS/spec-042-debug_toolbar-0_0_14.md`
`## Borrowing posture` #"The scrub stays unconditional and precedes this guard".

Measured, not argued: replacing the scrub with `if (isRecord(toolbar)) delete data.debugToolbar;`
— the exact weakening the plan's M3 "Incomplete if" list names, and the one that would re-open
Revision 8's leak for a malformed payload — fails **0 of 41 rows**. The ordering rows compare
indices, so a guarded scrub still precedes everything; the presence row still matches. The
shipped code is correct and this is not a defect in it: Test 16's contract asks for ordering rows
and the diff delivers them. It is a gap in what the contract asks for, which is why it is Low and
routed rather than held. One row closes it — an adjacency predicate over
`"const toolbar = data.debugToolbar;"` immediately followed by `"delete data.debugToolbar;"`,
which is the property the spec sentence actually states.

#### L3-2 — the record predicate does not cover the panel id's trip through `querySelector`

`django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
#"const content = djDebug.querySelector(`#${id}`);".

The payload-shape family now answers "can keys be read from this value" at every read site. The
loop then interpolates the *key itself* into a selector: for a `debugToolbar` payload whose
`panels` object carries a key that is not a valid CSS identifier (`{"a b": {"title": "x"}}`),
`querySelector("#a b")` throws a `DOMException` out of the patched `JSON.parse` /
`Response.prototype.json` — the same door M3 closed, one step further in, reached only by a
foreign payload that has already passed three record checks. Upstream carries it identically, and
neither the spec's `## Edge cases and constraints` bullet nor the `## Borrowing posture` entry
claims more than it delivers (both are scoped to values and panel entries, not to ids), so
**nothing shipped is falsified** and this is not a re-raise of anything the rationale rejected
(the rejected list covers `try`/`catch`, input-spelling enumeration and `requestId`, not the
selector). Recorded so the next reader does not rediscover it as a defect, and escalated below
because "does this asset take on `CSS.escape`" is a contract question, not a worker's. **No change
recommended inside this cohort.**

### DRY findings

- **Needle literals repeat inside `_TEMPLATE_CONTRACT`** (`tests/middleware/test_debug_toolbar.py`;
  helper output, not eyeballed): `delete data.debugToolbar` 5x, the payload-shape guard line 3x,
  `Object.entries(toolbar.panels)` 3x, `if (djDebug === null) return data;` 2x,
  `if (!isRecord(panel)) return;` 2x. **Not flagged for consolidation**, and the reason is worth
  recording so it is not re-derived: the duplication is *self-detecting* — reword the asset's
  scrub line and five rows fail loudly in one run, which is the opposite of the silent rot the DRY
  rule exists to prevent — and each row currently reads as a standalone statement of the contract
  text it pins. Naming the five multiply-used needles as module constants would be a small
  improvement (one edit site instead of five) and is recommended if Worker 2 re-opens the file for
  M3-1 anyway; it is not required.
- **The regex-over-`pyproject.toml` governance idiom now has three sites in two files** —
  `tests/test_ci_governance.py::test_channels_floor_constant_matches_the_pyproject_dependency_row`,
  `::test_strawberry_floor_constant_matches_the_pyproject_dependency_row`, and this pass's
  `tests/middleware/test_debug_toolbar.py::test_install_hint_floor_matches_the_pyproject_dev_group_row`.
  The plan's `### DRY analysis` item 4 declined the extraction with an explicit trigger — "extract
  … the day a third soft dependency gets the row" — and **this pass is that day**. The extraction
  cannot land here (`tests/test_ci_governance.py` and `tests/_soft_dependency.py` are outside the
  cohort's write set), so this is a routed refinement, not a finding against the diff; the landed
  row copies the idiom faithfully, which is the right call given the fence. Routed below.
- **`isRecord` — existence challenge considered, not raised.** Four real call sites (`data`, the
  captured `toolbar`, `toolbar.panels`, each `panel`), and the alternative is the asset spelling
  `value !== null && typeof value === "object"` four times, where a reviewer could no longer tell
  whether the four agree. Deleting it and inlining would add three duplicate predicates, not
  remove an indirection. Not a challenge.
- **`_TEMPLATE_CONTRACT` — existence challenge considered, not raised, and this is the one worth
  saying out loud.** The largest DRY win in this repo's history was a deletion, so the question is
  live: should a 41-row table of substring predicates exist at all? The measured answer is yes,
  and the measurement is Cohort B's: the monolithic predecessor scored **1** failing row for the
  removal of any template guard and **1** for the removal of all of them, so deleting the table
  would return the asset to a state where the suite cannot distinguish one dropped guard from
  seven. The table is not an abstraction over duplication; it is the only instrument in the file
  whose output tracks the thing it measures. Its cost — 35 substring predicates over an 89-line
  asset — is the price of having no JS runtime, which is the question already escalated and
  parked.
- **`_present` / `_absent` / `_defined_once` / `_ordered`** are four one-line closures with 41 call
  sites between them. No duplication, no premature abstraction; `_ordered`'s decision to return
  `False` rather than raise for a missing needle is the right one (a row reports under its own
  name instead of erroring out of the parametrized body) and is the reason the deletion-mutation
  entry counts ordering rows at all.
- Repeated literals in `django_strawberry_framework/middleware/debug_toolbar.py` are unchanged
  from Cohort B's reading (`Content-Length` 4x, `debugToolbar` 3x, `debug_toolbar` 2x), both
  already considered and recorded as no-action there; this pass added no executable line, so
  nothing re-opens them.

### What the 41 rows do and do not prove

Stated plainly so nobody later reads a green run as behavioural coverage, per the dispatch and
Worker 2's own `### Notes for Worker 3`:

**Every one of the 41 rows is a text predicate over the asset file.** `_present`, `_absent`,
`_defined_once` and `_ordered` all operate on `template.read_text()`. The asset is never parsed as
JavaScript, never loaded into a DOM, never executed. So the table proves: the guard text is
present, single-sited where that matters, ordered correctly relative to the scrub, and free of the
upstream reads it replaced. It proves **nothing** about whether `isRecord` returns what it should,
whether the payload-shape guard actually prevents the `TypeError` it was written to prevent,
whether the shadow-root lookup resolves, or whether `update` returns a scrubbed object. Three of
the seven diverged forms exist specifically to survive *runtime* inputs (a null-prototype object,
an absent DOM node, a shadow root) and no row can reach any of them. M3's guard is in exactly that
position: correct by reading, unexecuted by the suite. Whether this repo takes on a JS runtime is
already escalated and homed at close-out (build plan `## Maintainer decisions taken mid-cycle`
item 2); this section is not a re-raise, it is the label the table needs so its 41 green rows are
never mistaken for behavioural evidence.

### Dispatched findings checklist — walked

All five boxes are `- [x]`; each has a matching fix in the diff, and no box is ticked without one.

- **M1** ✓ `tests/middleware/test_debug_toolbar.py::test_encoded_response_gets_no_package_mutation`
  is four rows (`{append, injection} × {gzip, br}`) with a per-row positive control and bodies each
  path accepts; the falsified "reaches BOTH mutation sites" docstring is gone. Re-measured at 4
  rows, both sites represented. **Closed.**
- **M2** ✓ the monolithic test is replaced by the 41-row table under the same function name (no
  stranded `::Symbol` citation — the two test names are cited in the rationale and in both closed
  cohort artifacts and both still resolve; `check_citations.py --check` reads `.py` and `KANBAN.md`
  and passes). Cohort B's two 1-row template entries now measure **3** and **4** at the same scope
  on the same mutations, and every one of the seven families measures ≥ 2. **Closed** — with M3-1
  open against a claim the fix makes about itself, not against the fix.
- **M3** ✓ `isRecord` defined once at IIFE scope, applied at the entry guard, the captured
  `toolbar`, `toolbar.panels` and each `panel`; scrub unconditional and first; no `try`/`catch`;
  no input-spelling enumeration; `setAttribute` left upstream-verbatim with the coercion reason
  recorded. Two new boundaries, measured at 3 and 2 rows. Matches the rationale's `### M3` entry
  and the `### Borrowing posture` change record clause for clause, including every rejected
  alternative. **Closed.**
- **M4** ✓ both comment sites reframed to name the gated trio by mechanism with no population
  numeral, plus the sweep instruction; the new governance row compares the `pyproject.toml` row to
  the re-typed literal **and** the literal to the hint. Independently re-measured: the specifier
  `django-debug-toolbar>=7.0.0` still occurs at five live sites (`pyproject.toml`, the hint, the
  test literal, `docs/GLOSSARY.md`, `docs/README.md`), and the comment no longer makes a claim
  about that population. **Closed.**
- **Stale docstring line** ✓ `No other Python behavior differs.` is gone, no numeral replaced
  `two`, the three Python divergences are enumerated by name, and the template family is pointed
  at without being counted. AST-identity with docstrings stripped re-run independently: identical.
  **Closed.**

Cohort B's **L1** (the missing semicolon on `const origJson = Response.prototype.json`) is closed
in passing, as the plan's step 1 directed. **L2** (`if (panel.subtitle)` never clearing an emptied
subtitle) is untouched, as Cohort B recommended.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` — **empty**. `__all__` and the re-export
list are unchanged, and no new public name enters the package: `isRecord` is a JavaScript
IIFE-local, and the table plus its four predicate helpers are module-private in the test file. The
spec's soft-dependency DoD item requires exactly that.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; this cohort's diff modifies no docs, release-metadata, KANBAN or archive surface —
its three files are the middleware module, the asset, and the package-tier test. The spec and
rationale edits recorded in `### Spec changes made (Worker 1 only)` are Worker 1's planning-pass
work, read here as review context (they are the reasoning the implementation is checked against)
and never edited; what they need is under `### Notes for Worker 1` below.

### What looks solid

- **The guard is written against the answer, at every site, and the sites are complete for the
  question it asks.** Read end to end with the diff open: after `isRecord(toolbar) &&
  isRecord(toolbar.panels)` and `isRecord(panel)`, every remaining read in the DOM block is either
  behind a null check (`content`, `panelTitle`, `heading`, `scroll`, `loader`, `panelContent`,
  `nav`, `subtitle`) or on a value already proved a record (`panel.title`, `panel.subtitle`,
  `toolbar.requestId`). `isRecord` is also correct for the hostile shapes the family already
  hardened against: `Object.create(null)` passes (it is an object), a function fails (`typeof` is
  `"function"`), an array passes and degrades harmlessly (`Object.entries([])` is legal;
  `panel.title` on an array is `undefined`, which the truthiness test skips).
- **The scrub really is unconditional and really is first**, and both halves are pinned in the
  direction that matters: `const toolbar = data.debugToolbar; delete data.debugToolbar;` precede
  the null-handle bail, the new payload-shape guard, the panel loop and the `setAttribute` write,
  and the relocation mutation fails four ordering rows rather than passing.
- **The failability record is honest where it was easiest not to be.** Worker 2 disclosed the
  deletion-for-relocation substitution in `### Notes for Worker 1` rather than letting a 5-row
  count stand unexplained, disclosed both anchor choices, disclosed the deliberate cross-entry row
  overlap, and pre-warned this reviewer that re-running entry 4 yields 5 rows and not the plan's
  predicted 4. Every one of those disclosures checked out.
- **The node-id arithmetic is re-derivable and correct.** `27 + 40 + 2 + 1 = 70`, and the scope
  collects exactly 70 (`--collect-only -q` → `70 tests collected`), with all nine of this pass's
  independent baselines reading `70 passed, exit 0`.
- **The new governance row fails closed.** `re.findall(...) == [_HINT_SUBSTRING]` refuses a
  deleted row (`[] != [...]`), a moved row, and a second `django-debug-toolbar>=` specifier
  appearing anywhere in `pyproject.toml` — not merely a changed one. It copies the two
  `test_ci_governance.py` precedents' idiom exactly, capturing the whole specifier rather than the
  version because `_HINT_SUBSTRING` is the whole specifier.
- **The docstring rewrite states a contract rather than a chronology.** No round or cohort
  provenance, no "previously", no numeral, and the three divergences are the three that exist in
  the shipped module (`isinstance(view, type)` in `process_view`, `_get_payload`'s response-shape
  bail family, the `Content-Encoding` bail in `_postprocess`) — checked against the source, not
  against the spec's account of it.

### Temp test verification

- `docs/builder/temp-tests/042/proofs-worker3.json` — this pass's nine-entry manifest; Worker 2's
  `proofs.json` is preserved unchanged beside it.
- `docs/builder/temp-tests/042/proofs-report-worker3.md` — the emitted record, tool exit 0.
- `docs/builder/temp-tests/042/worker3_contract_table_probe.py` — the landed `_TEMPLATE_CONTRACT`
  and its four predicate helpers, extracted verbatim by `ast` from the test file.
- `docs/builder/temp-tests/042/worker3_replay_probe.py` — evaluates that table against in-memory
  mutated assets; the second instrument behind the eight template row-set confirmations, the
  relocation/deletion comparison, and the conditional-scrub measurement in L3-1. Deliberately not
  a `test_` module: it is a review probe, not a suite member.
- **Disposition:** all four stay under `temp-tests/`. None caught a production bug (M3-1 and L3-1
  are findings about the pinning, and L3-2 was found by reading), so nothing is promoted. The
  probe's *content* should not be promoted either — if M3-1 is closed by adding rows, the landed
  table is the permanent instrument and the probe is scaffolding.

### Notes for Worker 1 (spec reconciliation)

1. **Test 16's "every form … at least one ordering or absence predicate" sentence is false against
   the landed table** (M3-1 above, with the per-form measurement). Whichever resolution Worker 2
   takes, the spec sentence and the test-file comment must end up saying the same true thing. If
   rows are added, Test 16's enumeration should name the upstream-form absence rows explicitly —
   they are the silent-revert detectors and deserve to be contract, not implementation detail.
2. **`## Borrowing posture`, the membership-guard bullet, now describes a spelling that moved.** It
   says the port's `update` "bails on `data === null`, `typeof data !== "object"`, and
   `!Object.prototype.hasOwnProperty.call(...)`". Behaviourally still exact; as a description of
   the asset it is now one clause stale, since the first two are spelled `!isRecord(data)`. Low,
   and Worker 1's call whether a behavioural description should track a spelling at all.
3. **Escalated (contract-level): L3-2, the panel id's trip through `querySelector`.** A `panels`
   key that is not a valid CSS identifier still throws out of the patched globals. Resolution
   paths: (a) accept it — the payload is dev-only and already three record checks deep, and record
   the scope line in the rationale's Borrowing-posture entry beside the other rejected shapes so it
   is not re-raised; (b) `djDebug.querySelector("#" + CSS.escape(id))`, one call, which upstream
   does not do; (c) narrow the asset so the id never reaches a selector. **Not held at
   `revision-needed`** — nothing shipped is falsified by it and M3-1 is what sets the status.
4. **L3-1's one missing row** (the scrub's unconditionality) is worth folding into Test 16's
   contract if Worker 2 re-opens the table.
5. **The deferred-work catalog gains two measured items, replacing two "plausible carrier"
   hypotheses.** (a) `docs/GLOSSARY.md`'s Debug-toolbar middleware entry was recorded by Cohort A
   and Worker 0 as a *plausible* carrier of this cycle's staleness; it is an actual one — the body
   reads "Two deliberate robustness divergences from the verbatim upstream borrow" and enumerates
   only `process_view`'s `isinstance` guard and `_get_payload`'s bail, which is the exact
   closed-count claim the module docstring just retired, and it names the `>=7.0.0` floor besides.
   Fenced out and DB-backed (ORM edit + regenerate), so it stays routed — but it should be
   catalogued as measured, not as suspected. (b) The `DEBUG_TOOLBAR_FLOOR` refinement in
   `utils/imports.py` now has a *fired* trigger rather than a hypothetical one: three
   regex-over-`pyproject.toml` governance rows exist across two files as of this pass, which is the
   condition the plan's own `### DRY analysis` item 4 named.
6. **The DRF twin is now the package's only remaining false-population comment**, as Worker 2
   recorded — `django_strawberry_framework/rest_framework/__init__.py` #"three-places-that-must-agree"
   with no gate over the `pyproject.toml` side. Confirmed by re-reading both sites; still out of
   this cycle's single-spec scope and still owed a named owner.
7. **The concurrent session is queuing work in this cohort's test file.** The (dirty, uncommitted)
   `examples/fakeshop/test_query/README.md` live-promotion backlog names
   `tests/middleware/test_debug_toolbar.py::test_get_payload_panel_title_only_when_has_content` for
   live promotion and "`tests/middleware/test_debug_toolbar.py` two `Content-Length` refresh rows"
   for deletion after a live twin lands. Nothing collides today — that work is unstarted and
   Cohort C touched neither row — but whoever executes that sweep will meet a file that now carries
   a 41-row table and four predicate helpers. Worth one line in `bld-042-final.md` so it is not a
   surprise.
8. **Baseline-dirty population: 74 paths at the end of this pass**, up from the plan's 53 and the
   dispatch's 73. Only the three Cohort C files are this cycle's; nothing else was read as build
   output, edited or reverted. Recorded as a reading, not a constant.

### Review outcome

`revision-needed`.

One Medium (M3-1) and two Lows (L3-1, L3-2), none of them against the behaviour that landed. The
code is right: `isRecord` is applied at every read site and written against the answer rather than
an input spelling, the scrub stays unconditional and first, the Python diff is provably
non-executable, the floor's gated trio is now actually gated in both directions, and every
boundary this cohort was dispatched to pin is independently re-measured above the weakly-pinned
threshold — the two Cohort B entries that scored 1 row now score 3 and 4 on the same mutations at
the same scope, and the node-id sets match Worker 2's record exactly, boundary for boundary, under
two independent instruments.

What sends it back is a single sentence, in two places, that claims the new table resists a stray
substring when four of its seven families are pinned by presence checks alone. That is the same
defect class as M4 and as the docstring closer this very pass retired, published by the pass that
retired them, in the file that retired them. The cheap fix is not the correction but the four
absence rows it implies — the ones that would catch a silent revert to upstream's form, which is
the failure mode the whole divergence family exists to prevent and the one every mutation in this
record simulates.

---

## Build report (Worker 2, pass 2)

Built against `## Review (Worker 3)`. One Medium (M3-1) and one Low (L3-1) closed in the
diff; the second Low (L3-2) is decided in writing below and deliberately not fixed. Nothing
from the prior pass is reopened: `django_strawberry_framework/middleware/debug_toolbar.py` and
`django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html` are
**byte-unchanged by this pass** - `shasum -a 256` reads `5c189885117946d2...` and
`a1431798b18787cf...`, the same two digests Worker 2's first pass recorded and Worker 3
independently re-confirmed after its nine re-runs. This pass edits one tracked file.

### Files touched

From `git status --short`. Everything else modified in that output is the concurrent session's
baseline-dirty work - neither edited nor reverted (`AGENTS.md` rule 34); it now also carries
`docs/builder/bld-final.md`, `bld-integration.md`, `bld-slice-3-sql_and_unit_contracts.md` and
`build-050-list_field_arguments-0_0_15.md`, none of them this cycle's.

- `tests/middleware/test_debug_toolbar.py` - **M3-1 + L3-1.** Three new predicate helpers
  (`_adjacent`, `_own_statement_line`, `_unnested_within`); the `_TEMPLATE_CONTRACT` block
  comment rewritten to state the discipline by mechanism; seven rows added; one existing
  absence row's needle tightened; the reviver rows regrouped out of the preserved-invariant
  block into their own family; the parametrized test's docstring corrected.
- `docs/builder/temp-tests/042/proofs-cohort-c-pass2.json` - this pass's eight-entry manifest.
  Worker 2's `proofs.json` and Worker 3's `proofs-worker3.json` are both preserved unchanged
  beside it, as are their reports. Emitted record:
  `docs/builder/temp-tests/042/proofs-report-cohort-c-pass2.md`. Gitignored scratch.
- This artifact; `docs/builder/worker-memory/042-worker-2.md`.

No `.py` under `django_strawberry_framework/` and no `.html` asset changed, so the prior pass's
AST-identity record and both `none` declarations stand untouched rather than re-derived.

### Worker 3 findings - disposition

#### M3-1 (Medium) - **closed by adding the silent-revert detectors, not by correcting the prose**

The population was re-derived from the landed table rather than taken from either recorded
split (Worker 3's and Worker 0's disagreed, and neither is authoritative): `ast` over the
`_TEMPLATE_CONTRACT` elements, reading each row's predicate **constructor name**, then each
family's rows read off the table's own comment blocks. The re-derivation confirmed the finding's
substance - several diverged forms carried presence checks only - without adopting either count.

The remedy is the one Worker 3 named as worth more than the correction. Every **diverged** form
now carries both halves of its divergence: the port's spelling, and a row asserting the upstream
spelling it replaced is **absent**. Those are the silent-revert detectors: every mutation in this
cycle's proof record restores upstream's form, and a presence row cannot catch a revert that
restores upstream's shape alongside the port's.

- `no-upstream-single-argument-parse` - `_absent("update(origParse(text))")` (reviver)
- `no-upstream-own-hasownproperty-call` - `_absent('data.hasOwnProperty("debugToolbar")')`
  (membership guard)
- `no-upstream-value-returning-panel-map` - `_absent(".map(([id, panel])")` (per-panel loop;
  anchored on the destructured callback rather than on a receiver, so it names upstream's
  construct whichever object the `.map` is taken over)
- `no-upstream-chained-panel-title-write` - `_absent('.querySelector("h3").textContent')`
  (per-node null guards)
- `no-document-level-nav-lookup` - **existing row, needle tightened** from
  `document.getElementById(\`djdt-${id}\`)` to `.getElementById(\`djdt-${id}\`)`. Measured, not
  assumed: the old needle occurs **zero** times in upstream's asset, because upstream wraps that
  call across three lines - the row could not have caught the verbatim paste it was written to
  catch. The tightened needle occurs once upstream and zero times in the port.

The block comment and the test docstring now state the discipline **by mechanism and carry no
numeral for any population**: what each kind of row is for, and what falsifies the claim (a
diverged form whose rows are all presence checks, or a post-scrub site no ordering row names).
A count there would be the same self-falsifying instrument in a third incarnation - it is a live
count of a population the next editor of this table is editing.

Not taken: Worker 3's optional `_present("origJson.apply(this, arguments)")` second row for the
`Response.prototype.json` wrapper. That block is upstream-**verbatim**, so it has no revert to
detect, and the only mutation that removes what such a row pins is deleting the wrapper - which
also deletes `_TEMPLATE_MARKER`'s needle and fails the M1 positive controls and the HTML
`Content-Length` row, i.e. a mutation reaching well past its boundary. Narrowing it to a
non-forwarding call instead yields exactly one row, which is weakly pinned. The claim the comment
now makes about preserved invariants is true without it.

#### L3-1 (Low) - **closed; the conditional scrub now fails rows in both of its spellings**

The hole was real and fail-open: a guard that cannot see its own absence. Ordering rows compare
indices, so `if (isRecord(toolbar)) delete data.debugToolbar;` still precedes everything it
preceded. Three rows answer "does the scrub run on every path that reaches it", each by a
different mechanism, because the weakening has two natural spellings and one row catches only one
of them:

- `scrub-immediately-follows-capture` - only whitespace between
  `const toolbar = data.debugToolbar;` and `delete data.debugToolbar;` (catches both spellings)
- `scrub-is-its-own-statement` - some line's content is exactly `delete data.debugToolbar;`
  (catches the inline spelling)
- `scrub-not-nested-inside-update` - braces balance between `function update(data) {` and the
  scrub (catches the braced spelling)

Both spellings were mutated and measured (entries 1 and 2 below): **2 rows each**, from the scrub
family only. Worker 3 measured the inline spelling at 0 of 41 rows before this pass.

#### L3-2 (Low, escalated) - **decided: not fixed in this cohort, and here is why**

A `panels` key that is not a valid CSS identifier still throws a `DOMException` out of
`djDebug.querySelector(\`#${id}\`)` and therefore out of the patched globals. Read against M3's
own contract this is arguably the same class - a payload-shaped input crashing the global
`JSON.parse` patch, against a family whose rule is "payload scrubbing is mandatory, DOM updates
are best-effort". It is not fixed here, for reasons that are about ownership, not about risk:

1. **The fix is an eighth divergence from the borrow, and the spec fixes the family at seven.**
   `## Borrowing posture` enumerates the diverged forms and scopes the payload-shape guard to
   *values and panel entries*; `## Edge cases and constraints` does the same. Adding
   `CSS.escape(id)` - or any id-validity predicate - adds a form to that enumeration and changes
   what the asset promises about the payload. Worker 2 may not edit the spec, and landing an
   eighth divergence the spec does not carry would falsify it: the exact defect class this cycle
   exists to retire, committed in the direction nobody would look.
2. **Nothing shipped is falsified by leaving it.** Worker 3 checked this and this pass re-read
   both sections to confirm: neither claims id safety, so the code matches its contract. A fix is
   an extension of the contract, which is Worker 1's call and the maintainer's, not a builder's.
3. **It is not a defect the guard was written to catch and missed.** `isRecord` answers "can keys
   be read from this value". "Is this key a usable CSS identifier" is a different question whose
   answer needs a different instrument; the guard is not fail-open with respect to the question
   it asks.
4. **The cheap-looking fix has a cost worth stating before anyone takes it.** `CSS.escape` would
   be the only DOM API in the asset that upstream does not use, on a page the package does not
   control; and the `try`/`catch` spelling is already a recorded rejected alternative
   (`BUILD.md` `### Fail-open shapes`, bare `except`).

Routed to Worker 1 under `### Notes for Worker 1 (spec reconciliation)` with the amendment shape
each resolution path would need. Not left silent, and not closed by a worker.

### Tests added or updated

- `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence`
  - same name, same shape, seven new rows. Node-id arithmetic at the recorded scope, so the
  difference against the two existing records is re-derivable rather than asserted: Cohort B
  measured **27 passed**, Worker 2's first pass **70 passed**, this pass measures **77 passed**,
  exit 0, 0 collection errors, at the identical scope. `70 + 7 = 77`; the seven are the five
  absence/revert rows minus the one that already existed (`no-document-level-nav-lookup` was
  re-needled, not added) plus the three scrub-unconditionality rows. No row was removed and none
  renamed; the tightened needle keeps its id, so every node-id set in the two prior records still
  resolves.
- No other test changed. No live-tier change:
  `examples/fakeshop/test_query/test_debug_toolbar_api.py` is not in the write set and nothing
  here is reachable through a live request.

### Validation run

- `uv run ruff format tests/middleware/test_debug_toolbar.py` - pass (scoped to this pass's one
  file, never `.`).
- `uv run ruff check --fix tests/middleware/test_debug_toolbar.py` - `All checks passed!`.
- `uv run python scripts/check_trailing_commas.py --fix tests/middleware/test_debug_toolbar.py`
  - `Fixed 0 file(s).` Explicit paths always, never the repo-wide auto-fix default.
- Re-verified read-only afterwards: `ruff format --check` (`1 file already formatted`);
  `ruff check` (`All checks passed!`);
  `check_trailing_commas.py --check <the test file + both prior-pass source files>` exit 0;
  `git diff --check -- tests/middleware/test_debug_toolbar.py` exit 0.
- `uv run python scripts/check_citations.py --check` -
  `OK: 992 citations resolve (823 in 441 .py files, 169 in KANBAN.md).`
- `uv run pytest -n0 tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py --no-cov` - **77 passed**, exit 0, 0 collection errors. No `--cov*` flag anywhere in this pass.
- `git status --short` after both ruff invocations: exactly one tracked file of this cohort's
  write set is newly modified beyond the prior pass's two, plus this cycle's four untracked
  `docs/builder/{build,bld}-042-*` files. Nothing unexpected to stop-and-report.

### Failability proofs

Procedure, mechanized by `scripts/prove_failability.py`: the target is copied to a scratch path OUTSIDE the repo before any mutation; the mutation site is located by an exact anchor asserted to match exactly once (any other count aborts the entry without writing); the same focused scope is run unmutated first, so rows already failing before the mutation are differenced out of the count; both runs' pytest exit codes are read, because a run that collected nothing or blew up emits no `FAILED` lines and would otherwise be recorded as a measured zero; both runs use `--no-cov`; the file is restored from the pre-mutation copy in a `finally` and the restore is proved by `filecmp.cmp(shallow=False)` plus a SHA-256 comparison. One boundary at a time, restored before the next. `git` is never invoked - the tree is legitimately dirty, so an empty `git diff` is unachievable and forcing one would destroy the build's own work.

| # | Boundary | File mutated | Mutation applied | Rows failed | Errors | Scope as run | Restore proof |
|---|---|---|---|---|---|---|---|
| 1 | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"delete data.debugToolbar;" (the scrub is unconditional - inline condition)` | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html` | `delete data.debugToolbar;` -> `if (isRecord(toolbar)) delete data.debugToolbar;` - builder's description (unverified prose): the unconditional scrub made conditional on the payload shape without moving it, so a malformed debugToolbar value leaks the server-only key back to GraphiQL while every index-ordering row still matches | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE -n0 tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py` | filecmp.cmp(shallow=False) True; sha256 a1431798b18787cf... == a1431798b18787cf... (vs pre-mutation copy) |
| 2 | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"delete data.debugToolbar;" (the scrub is unconditional - block condition)` | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html` | `delete data.debugToolbar;` -> `if (isRecord(toolbar)) { delete data.debugToolbar; }` - builder's description (unverified prose): the same weakening in its braced spelling: the scrub nested inside a block of its own, which leaves its line untouched | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE -n0 tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py` | filecmp.cmp(shallow=False) True; sha256 a1431798b18787cf... == a1431798b18787cf... (vs pre-mutation copy) |
| 3 | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"update(origParse(text))" (reviver forwarding - upstream form absent)` | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html` | `const origParse = JSON.parse; JSON.parse = function () { return update(origParse.apply(this, arguments)); };` -> `const origParse = JSON.parse; JSON.parse = function (text) { return update(origParse(text)); };` - builder's description (unverified prose): the argument-forwarding wrapper reverted to upstream's verbatim single-argument form, which drops a page-wide JSON.parse(text, reviver)'s reviver | **3** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE -n0 tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py` | filecmp.cmp(shallow=False) True; sha256 a1431798b18787cf... == a1431798b18787cf... (vs pre-mutation copy) |
| 4 | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"data.hasOwnProperty(\"debugToolbar\")" (membership-guard safety - upstream form absent)` | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html` | `if ( !isRecord(data) || !Object.prototype.hasOwnProperty.call(data, "debugToolbar") ) { return data; }` -> `if (data === null || !data.hasOwnProperty("debugToolbar")) { return data; }` - builder's description (unverified prose): the entry guard reverted to upstream's verbatim form, which throws for a null-prototype object or one shadowing hasOwnProperty | **3** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE -n0 tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py` | filecmp.cmp(shallow=False) True; sha256 a1431798b18787cf... == a1431798b18787cf... (vs pre-mutation copy) |
| 5 | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #".map(([id, panel])" (best-effort per-panel DOM - upstream form absent)` | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html` | `Object.entries(toolbar.panels).forEach(([id, panel]) => { if (!isRecord(panel)) return; if (panel.title) { const cont...` -> `Object.entries(toolbar.panels).map(([id, panel]) => { if (!isRecord(panel)) return; if (panel.title) { const content ...` - builder's description (unverified prose): the skip-on-absent-content-node removed and the side-effect loop reverted to upstream's value-returning .map, so a payload panel missing from the toolbar DOM throws inside the patched JSON.parse | **3** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE -n0 tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py` | filecmp.cmp(shallow=False) True; sha256 a1431798b18787cf... == a1431798b18787cf... (vs pre-mutation copy) |
| 6 | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #".querySelector(\"h3\").textContent" (per-node null guards - upstream form absent)` | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html` | `const panelTitle = content.querySelector(".djDebugPanelTitle"); if (panelTitle !== null) { const heading = panelTitle...` -> `content .querySelector(".djDebugPanelTitle") .querySelector("h3").textContent = panel.title;` - builder's description (unverified prose): the panelTitle/heading null guards removed, restoring upstream's chained assignment that throws a TypeError inside the patched JSON.parse when one node is absent | **5** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE -n0 tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py` | filecmp.cmp(shallow=False) True; sha256 a1431798b18787cf... == a1431798b18787cf... (vs pre-mutation copy) |
| 7 | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #".getElementById(`djdt-${id}`)" (nav lookup scoped to the handle - upstream form absent)` | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html` | `const nav = djDebug.querySelector(`#djdt-${id}`);` -> `const nav = document.getElementById(`djdt-${id}`);` - builder's description (unverified prose): the nav lookup re-pointed at the document, upstream's spelling, which resolves to null under the default USE_SHADOW_DOM=True toolbar because the nav nodes live in the shadow tree | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE -n0 tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py` | filecmp.cmp(shallow=False) True; sha256 a1431798b18787cf... == a1431798b18787cf... (vs pre-mutation copy) |
| 8 | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"delete data.debugToolbar" (mandatory scrub, deleted)` | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html` | deleted: `delete data.debugToolbar;` - builder's description (unverified prose): the unconditional scrub deleted, so the server-only debugToolbar key survives every early return and every DOM write and leaks back to GraphiQL | **8** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE -n0 tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py` | filecmp.cmp(shallow=False) True; sha256 a1431798b18787cf... == a1431798b18787cf... (vs pre-mutation copy) |

Verdicts:

1. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"delete data.debugToolbar;" (the scrub is unconditional - inline condition)` - inside Worker 3's mandatory re-run floor (<= 3 rows)
2. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"delete data.debugToolbar;" (the scrub is unconditional - block condition)` - inside Worker 3's mandatory re-run floor (<= 3 rows)
3. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"update(origParse(text))" (reviver forwarding - upstream form absent)` - inside Worker 3's mandatory re-run floor (<= 3 rows)
4. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"data.hasOwnProperty(\"debugToolbar\")" (membership-guard safety - upstream form absent)` - inside Worker 3's mandatory re-run floor (<= 3 rows)
5. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #".map(([id, panel])" (best-effort per-panel DOM - upstream form absent)` - inside Worker 3's mandatory re-run floor (<= 3 rows)
6. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #".querySelector(\"h3\").textContent" (per-node null guards - upstream form absent)` - pinned
7. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #".getElementById(`djdt-${id}`)" (nav lookup scoped to the handle - upstream form absent)` - inside Worker 3's mandatory re-run floor (<= 3 rows)
8. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"delete data.debugToolbar" (mandatory scrub, deleted)` - pinned

Failing node ids, per boundary (the count above is `len()` of this list):

1. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"delete data.debugToolbar;" (the scrub is unconditional - inline condition)`
   - file mutated: `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
   - pytest summary: `======================== 2 failed, 75 passed in 14.44s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 77 passed in 14.50s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[scrub-immediately-follows-capture]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[scrub-is-its-own-statement]`
2. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"delete data.debugToolbar;" (the scrub is unconditional - block condition)`
   - file mutated: `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
   - pytest summary: `======================== 2 failed, 75 passed in 14.46s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 77 passed in 14.52s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[scrub-immediately-follows-capture]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[scrub-not-nested-inside-update]`
3. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"update(origParse(text))" (reviver forwarding - upstream form absent)`
   - file mutated: `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
   - pytest summary: `======================== 3 failed, 74 passed in 14.42s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 77 passed in 14.37s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[json-parse-wrapper-signature]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[reviver-forwarded-via-apply]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[no-upstream-single-argument-parse]`
4. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"data.hasOwnProperty(\"debugToolbar\")" (membership-guard safety - upstream form absent)`
   - file mutated: `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
   - pytest summary: `======================== 3 failed, 74 passed in 14.18s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 77 passed in 14.35s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[entry-guard-uses-record-predicate]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[membership-guard-uses-hasownproperty-call]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[no-upstream-own-hasownproperty-call]`
5. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #".map(([id, panel])" (best-effort per-panel DOM - upstream form absent)`
   - file mutated: `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
   - pytest summary: `======================== 3 failed, 74 passed in 14.10s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 77 passed in 14.14s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[panel-loop-is-foreach]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[panel-loop-skips-absent-content-node]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[no-upstream-value-returning-panel-map]`
6. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #".querySelector(\"h3\").textContent" (per-node null guards - upstream form absent)`
   - file mutated: `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
   - pytest summary: `======================== 5 failed, 72 passed in 14.15s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 77 passed in 14.15s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[panel-title-node-lookup]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[panel-title-node-guarded]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[heading-node-lookup]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[heading-node-guarded]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[no-upstream-chained-panel-title-write]`
7. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #".getElementById(`djdt-${id}`)" (nav lookup scoped to the handle - upstream form absent)`
   - file mutated: `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
   - pytest summary: `======================== 2 failed, 75 passed in 14.10s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 77 passed in 14.07s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[nav-lookup-scoped-to-handle]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[no-document-level-nav-lookup]`
8. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"delete data.debugToolbar" (mandatory scrub, deleted)`
   - file mutated: `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
   - pytest summary: `======================== 8 failed, 69 passed in 14.10s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 77 passed in 14.09s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[scrub-key-deleted]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[scrub-immediately-follows-capture]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[scrub-is-its-own-statement]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[scrub-not-nested-inside-update]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[scrub-before-null-handle-bail]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[scrub-before-payload-shape-guard]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[scrub-before-panel-loop]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[scrub-before-request-id-write]`

A boundary whose removal fails 0 or 1 rows is **weakly pinned** and is `revision-needed` per `docs/builder/BUILD.md` - the fix is more or better-targeted rows, never a weaker boundary. A boundary at 3 rows or fewer is inside Worker 3's mandatory independent re-run floor. A proof carrying collection or setup errors, or whose pytest run exited anything but 0 or 1 (nothing collected, interrupted, internal error, usage error), is not a valid count at all - and a 0 from such a run is not a zero-row result: resolve it and re-run.

Every `<fill in ...>` above is a judgement no tool can make and MUST be replaced by hand before this subsection is submitted: weakly pinned and harness-impossible are the two possible readings of a zero-row result and they prescribe opposite responses (more rows, versus a production-call-site invariant assertion plus a recorded harness limitation), so a record that does not name one reads as self-contradictory.

**Reading of the results.**

- No entry returned 0 or 1 rows, so nothing is weakly pinned and there is no **why 0** judgement
  to make - the emitted block carries no `<fill in ...>` placeholder. Every pre-mutation baseline
  was `77 passed`, exit 0, 0 collection/setup errors, eight times, so every count is a valid count
  and no pre-existing failing row was differenced out. Tool exit **0**.
- **L3-1 discharged.** The inline weakening Worker 3 measured at **0 of 41 rows** now fails 2, and
  its braced twin fails 2. Neither failing set contains a row from another family.
- **M3-1 discharged, measured per family.** Each upstream-revert mutation now fails its family's
  presence rows **and** the row asserting upstream's spelling is gone: reviver 2 -> **3**,
  membership 2 -> **3**, per-panel loop 2 -> **3**, per-node guards 4 -> **5**. The nav lookup's
  revert - not previously a manifest entry - fails **2**, which is what proves the tightened
  `no-document-level-nav-lookup` needle actually detects upstream's spelling.
- **Every entry's failing node ids lie inside the family the entry names.** Worker 2's two
  deliberate anchorings still hold under the wider table: entry 6 (per-node guards) fails
  `no-upstream-chained-panel-title-write` and **not** `panel-title-write`, which stays in the
  preserved-invariant family exactly as the first pass designed.
- The scrub-deletion entry is carried forward from Worker 2's manifest unchanged, so its set is
  directly differenceable: **5 rows -> 8**, the three added being this pass's unconditionality
  rows. Same mutation, same scope, no renames.
- Restores: `filecmp.cmp(shallow=False)` True plus a SHA-256 match against the pre-mutation copy
  on all eight. Independently re-confirmed after the run - the scratch root holds only
  `pristine/` and **no** `ACTIVE-MUTATION.json`, and the asset hashes to
  `a1431798b18787cfe303078af4e7579b29f8d7121ede20a7f05086aaa673c6a0`, the digest Worker 2 and
  Worker 3 both recorded. **No mutated tree is handed to Worker 3.**

### Hot-path budget

**Not applicable; the plan declares no hot path**, and this pass strengthens the warrant rather
than restating it: this pass changed no production file at all. Both source digests are unmoved
from the first pass, so the first pass's AST-identity proof (docstrings stripped, `12387 ==
12387`) is still the live evidence and needed no re-run - re-running it would prove a file that
did not change.

### Floor verification

**Not applicable; plan declares floor-verification scope `none`.** No Django / Strawberry /
channels integration seam changed; this pass touched one package-tier test file whose new rows
are pure text predicates over an asset on disk. Floor facts read from `docs/builder/BUILD.md`
`## Floor verification` this pass, never from memory: Django **5.2.16** on Python **3.10** with
strawberry-graphql **0.316.0**.

### Implementation notes

- **Three predicates for one property, deliberately.** "The scrub is unconditional" has two
  natural spellings and no single text predicate catches both: an inline `if (...) delete ...;`
  leaves brace depth untouched, and a braced `if (...) { delete ...; }` leaves the scrub's own
  line untouched. Adjacency catches both; the other two each catch the one adjacency alone would
  leave at a single row, which the weakly-pinned rule forbids. Each is a statement about the
  answer ("does this run on every path that reaches it"), not about a spelling of the weakening.
- **`_adjacent`, `_own_statement_line` and `_unnested_within` are total**, like `_ordered`: a
  missing needle returns `False` rather than raising, so a row a dropped guard makes unanswerable
  fails under its own name instead of erroring out of the parametrized body. That is why the
  scrub-deletion entry counts eight rows rather than erroring three of them.
- **`_unnested_within` counts braces over the span between the opener and the needle.** The span
  in the shipped asset holds only the entry guard (balanced) and comments, no template literals,
  so brace counting is exact here - it is not a general JavaScript parser and is not written as
  one.
- **The reviver rows were regrouped, not renamed.** `json-parse-wrapper-signature` and
  `reviver-forwarded-via-apply` sat under the "Preserved upstream invariants" comment while
  pinning a **diverged** form (upstream's signature is `function (text)`). With the comment now
  making a per-kind claim, a reader had to be able to tell which block is which. Ids are
  unchanged and the table is a `parametrize` argument, so node-id sets are order-independent and
  every recorded set in the two prior records still resolves.
- **The tightened nav needle was measured against both assets before the edit**, not reasoned:
  the old needle is absent from upstream (which wraps `document` / `.getElementById(...)` /
  `.querySelector(...)` across three lines), the new one occurs once there and never in the port.
- Repeated needle literals inside the table are unchanged in kind from Worker 3's DRY reading and
  were left as they are for the reason recorded there (the duplication is self-detecting). The
  new rows introduce no needle an existing row already pins: `delete data.debugToolbar;` carries
  the trailing semicolon the ordering rows' needle does not, and pins adjacency and nesting
  rather than order.

### Notes for Worker 3

- The manifest is `docs/builder/temp-tests/042/proofs-cohort-c-pass2.json`; the emitted record is
  `proofs-report-cohort-c-pass2.md` beside it. **Both prior manifests and both prior reports are
  untouched** (`proofs.json`, `proofs-report-cohort-c.md`, `proofs-worker3.json`,
  `proofs-report-worker3.md`), so the three-way before/after is readable without `git`.
- Re-run at the **recorded scope** - `-n0 tests/middleware/test_debug_toolbar.py
  examples/fakeshop/test_query/test_debug_toolbar_api.py` - and difference node-id sets; the
  baseline is **77**, not 70 and not 27, and the arithmetic is above.
- Entries 3, 4, 5 and 6 are Worker 2's first-pass entries 2, 3, 5 and 7 **verbatim**, so their
  sets are directly differenceable against both prior records; entry 8 is the first pass's entry
  4 verbatim. Entries 1, 2 and 7 are new.
- Worker 3's own replay probe (`worker3_replay_probe.py` / `worker3_contract_table_probe.py`)
  extracts the table and its helpers by `ast`. It will need the three new helper names added to
  whatever it extracts before it can replay this table - the probe is a second instrument worth
  keeping, and it is currently one instrument behind.
- **What the rows prove is unchanged in kind.** Every row, new ones included, is a text predicate
  over the asset file; nothing is parsed as JavaScript or executed. The new absence rows prove
  upstream's spelling is not in the file - not that the port's behaviour is correct. Worker 3's
  `### What the 41 rows do and do not prove` section applies verbatim to the wider table.
- L3-2 is **not** fixed. The reasoning is above under its own heading and the routing is below;
  read it as a decision rather than an omission.

### Notes for Worker 1 (spec reconciliation)

1. **`## Test plan`, Test 16 - the required correction, ready to apply verbatim.** Worker 2 may
   not edit the spec, so it is written out here in full.

   - **Where:** `## Test plan`, item 16 (the `**Template-port guard**` group), final claim
     sentence of the item.
   - **Current wording:** "Every form is pinned by at least two rows, at least one of them an
     ordering or absence predicate a stray substring cannot satisfy."
   - **Recommended replacement:** "Every diverged form carries both halves of its divergence: a
     row pinning the port's spelling, and a row pinning that the upstream spelling it replaced is
     absent - the silent-revert detector a presence check cannot supply, naming upstream's own
     forms (its single-argument `JSON.parse` wrapper, its `data.hasOwnProperty(\"debugToolbar\")`
     guard, its value-returning `.map` over panel entries, its `document`-level nav lookup, and
     its chained `.querySelector(\"h3\").textContent` write). Where the contract is a position
     rather than a spelling, the rows compare indices, adjacency and nesting instead, so a
     reordering - or a condition wrapped around the scrub - fails them while every substring
     still matches. A preserved invariant carries the row pinning the upstream write the port
     keeps."

2. **`## Test plan`, Test 16 - the mandatory-scrub clause, same item.**

   - **Current wording:** "the mandatory scrub **ordering** (one row per early return and DOM
     write that follows the scrub: the null-handle bail, the payload-shape guard, the panel loop,
     the `data-request-id` write)"
   - **Recommended replacement:** "the mandatory scrub **ordering and unconditionality** (one row
     per early return and DOM write that follows the scrub: the null-handle bail, the
     payload-shape guard, the panel loop, the `data-request-id` write - plus the rows that pin it
     unconditional, which an index comparison cannot: nothing but whitespace between the capture
     and the scrub, the scrub alone on its own line, and the scrub not nested inside a block of
     its own)"

   Warrant, in case it is questioned at final verification: `## Borrowing posture` already states
   "The scrub stays unconditional and precedes this guard", and until this pass nothing gated the
   first half - Worker 3 measured a guarded scrub at 0 failing rows. The sentence is now a gate.

3. **Escalated (contract-level), L3-2 - a `panels` key that is not a valid CSS identifier.**
   Worker 3 escalated it; this pass decided **not** to fix it inside the cohort and recorded why
   under `#### L3-2` above. The decision that remains is yours and the maintainer's, and each
   path needs a different spec edit:
   - **(a) Accept.** No code change. `## Borrowing posture`'s payload-shape bullet gains one
     clause scoping the guard - e.g. "The guard answers whether keys can be read from a value; a
     panel key that is not a valid CSS selector is out of its scope and still throws, which is
     upstream's behaviour and is recorded as accepted" - and the rationale's
     `### Borrowing posture` change record gains it beside the other rejected shapes so it is not
     re-raised a third time.
   - **(b) `djDebug.querySelector("#" + CSS.escape(id))`.** This is an **eighth** diverged form:
     `## Borrowing posture`'s "seven spots" becomes eight, a new bullet states the contract, the
     DoD's "seven documented guard divergences" moves with it, and Test 16 gains its rows. It
     owes a failability proof like any boundary, so it is a Worker 2 re-pass, not a spec-only
     edit.
   - **(c) Narrow the asset so the id never reaches a selector.** Same spec surface as (b) plus a
     behavioural change to which panels update.

4. **Small drift: one existing row's needle was tightened, not only added to.**
   `no-document-level-nav-lookup` kept its id and changed its needle from
   `document.getElementById(\`djdt-${id}\`)` to `.getElementById(\`djdt-${id}\`)`, because the old
   spelling occurs **zero** times in upstream's asset - upstream wraps the call across three
   lines, so the row could not catch the verbatim paste it names. Nothing in the spec states a
   needle, so this is for your audit rather than an amendment; it changes no recorded node-id set
   (the row's id is unchanged and it passes on the unmutated asset before and after).

5. **Worker 3's `## Borrowing posture` membership-guard note (its item 2) is untouched by this
   pass** and still stands: the bullet describes the port's bail as `data === null`,
   `typeof data !== "object"`, `!Object.prototype.hasOwnProperty.call(...)`, and the first two are
   now spelled `!isRecord(data)`. Behaviourally exact, one clause stale as a description. Your
   call whether a behavioural description should track a spelling; this pass added a row naming
   upstream's spelling rather than the port's, which does not touch the question.

6. **Nothing this pass found changes the deferred-work items** already routed by the plan, the
   first build report and Worker 3: the DRF false-population comment in
   `django_strawberry_framework/rest_framework/__init__.py`, the `DEBUG_TOOLBAR_FLOOR` refinement
   in `utils/imports.py` (trigger fired), M4's documentation half (`docs/GLOSSARY.md` measured as
   an actual carrier, `docs/README.md`), the JS-runtime question homed at close-out, and the
   concurrent session's queued live-promotion sweep over this test file. All still owed a named
   owner in `bld-042-final.md`.

7. **Baseline-dirty population, as a reading rather than a constant:** `git status --short` at the
   end of this pass shows the concurrent session's set has grown again and now includes
   `docs/builder/bld-final.md`, `bld-integration.md`, `bld-slice-3-sql_and_unit_contracts.md` and
   `build-050-list_field_arguments-0_0_15.md` alongside the package and test files Worker 3
   listed. None is this cycle's; none was edited or reverted. Compare against a fresh reading at
   the final gate, never against any of the three counts now recorded in this artifact.

`Status: built`. Next: Worker 0 dispatches Worker 3 against this diff.


---

## Review (Worker 3, pass 2)

Diff under review: `git diff HEAD -- tests/middleware/test_debug_toolbar.py`. The two source
files this cohort owns are byte-unchanged by this pass, re-measured here rather than accepted:
`shasum -a 256` reads
`5c189885117946d2122c4dd03f9153ddfab4a13c4697d669557958387af4201b` for
`django_strawberry_framework/middleware/debug_toolbar.py` and
`a1431798b18787cfe303078af4e7579b29f8d7121ede20a7f05086aaa673c6a0` for
`django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html` — the same
two digests the first build pass recorded and the first review pass re-confirmed. So the
docstring-only AST-identity warrant behind the `none` hot-path and `none` floor-verification
declarations is untouched and needed no re-derivation. Everything else dirty in the tree is the
concurrent spec-050 session's; none of it was edited, reverted or read as build output
(`AGENTS.md` rule 34).

### Mutations recorded BEFORE they were made

`worker-3.md` "Scope" requires the carve-out's mutations to be recorded before they are applied.
Seven independent re-runs, listed here before the first was applied. Six re-use Worker 2's
pass-2 manifest entries verbatim so the node-id SETS are differenceable; the seventh is this
pass's own.

**The mandatory floor** (`worker-3.md` "Reading is necessary, not sufficient": every boundary
recorded at 3 rows or fewer) is Worker 2's pass-2 entries **1, 2, 3, 4, 5, 7**. Entry 6 (5 rows)
and entry 8 (8 rows) sit above it; neither is a security or data-isolation decision. Both are
nonetheless re-measured by the second instrument below rather than accepted on prose, and entry 8
is additionally differenced against the same mutation's two prior records.

| # | Boundary | Mutation to be applied | Source |
| --- | --- | --- | --- |
| 1 | `…/debug_toolbar.html` #"delete data.debugToolbar;" | scrub made conditional, **inline**: `if (isRecord(toolbar)) delete data.debugToolbar;` | Worker 2 pass-2 entry 1, verbatim |
| 2 | `…/debug_toolbar.html` #"delete data.debugToolbar;" | scrub made conditional, **braced**: `if (isRecord(toolbar)) { delete data.debugToolbar; }` | Worker 2 pass-2 entry 2, verbatim |
| 3 | `…/debug_toolbar.html` #"update(origParse(text))" | reviver forwarding reverted to upstream's `function (text) { return update(origParse(text)); }` | Worker 2 pass-2 entry 3, verbatim |
| 4 | `…/debug_toolbar.html` #"data.hasOwnProperty(\"debugToolbar\")" | entry guard reverted to upstream's `data === null \|\| !data.hasOwnProperty("debugToolbar")` | Worker 2 pass-2 entry 4, verbatim |
| 5 | `…/debug_toolbar.html` #".map(([id, panel])" | per-panel loop reverted to upstream's value-returning `.map`, content-null skip removed | Worker 2 pass-2 entry 5, verbatim |
| 7 | `…/debug_toolbar.html` #".getElementById(\`djdt-${id}\`)" | nav lookup re-pointed at `document`, upstream's spelling | Worker 2 pass-2 entry 7, verbatim |
| 3b | `…/debug_toolbar.html` #"origJson.apply(this, arguments)" | **this pass's own**: the `Response.prototype.json` wrapper narrowed to a non-forwarding `origJson.call(this)`, leaving `Response.prototype.json = function` intact — the mutation the declined optional row would have pinned, run to test the decline rather than accept it | **this pass** |

Manifest: `docs/builder/temp-tests/042/proofs-worker3-pass2.json` (all four prior manifests and
all four prior reports preserved unchanged beside it). Scratch root **outside** the repository.
Anchors asserted to match exactly once before any mutation — which is also what proves the tree
was not already carrying a foreign live mutation.

### Failability proofs (Worker 3 independent re-run, pass 2)

Scope, identical for all seven and identical to Worker 2's pass-2 record:
`uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE -n0
tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py`.
Pre-mutation state, measured fresh before every entry: **77 passed, exit 0, 0 collection/setup
errors** — seven times, so no pre-existing failing row inflates any count and the post-addition
baseline Worker 2 recorded is confirmed independently. Emitted record:
`docs/builder/temp-tests/042/proofs-report-worker3-pass2.md`; tool exit **0**.

| # | Boundary | Rows | Failing node ids (all `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[…]`) | vs Worker 2 |
| --- | --- | --- | --- | --- |
| 1 | scrub unconditional — **inline** condition | **2** | `[scrub-immediately-follows-capture]`, `[scrub-is-its-own-statement]` | identical set |
| 2 | scrub unconditional — **braced** condition | **2** | `[scrub-immediately-follows-capture]`, `[scrub-not-nested-inside-update]` | identical set |
| 3 | reviver forwarding — upstream form absent | **3** | `[json-parse-wrapper-signature]`, `[reviver-forwarded-via-apply]`, `[no-upstream-single-argument-parse]` | identical set |
| 4 | membership guard — upstream form absent | **3** | `[entry-guard-uses-record-predicate]`, `[membership-guard-uses-hasownproperty-call]`, `[no-upstream-own-hasownproperty-call]` | identical set |
| 5 | per-panel loop — upstream form absent | **3** | `[panel-loop-is-foreach]`, `[panel-loop-skips-absent-content-node]`, `[no-upstream-value-returning-panel-map]` | identical set |
| 7 | nav lookup — upstream form absent | **2** | `[nav-lookup-scoped-to-handle]`, `[no-document-level-nav-lookup]` | identical set |
| 3b | `Response.prototype.json` wrapper stops forwarding (**this pass's own**) | **0** | — | no counterpart; see `#### The declined optional row` |

Every restore proved inside the run by `filecmp.cmp(shallow=False) True` plus SHA-256 equality
against the pre-mutation copy (seven of seven). Post-run tree state, checked independently of the
tool: the scratch root holds `pristine/` and **no** `ACTIVE-MUTATION.json`, and the two source
files hash to `a1431798b18787cf…` (asset) and `5c189885117946d2…` (module) — the digests recorded
before the first mutation. No mutation is live.

**Boundaries accepted on Worker 2's record, and why:** entry **6** (per-node null guards, 5 rows)
and entry **8** (mandatory scrub deleted, 8 rows). Both sit above the mandatory re-run floor and
neither is a security or data-isolation decision. Neither was accepted on prose: both row sets
were reproduced exactly by the second instrument below, and entry 8 is the same mutation the two
prior records carry, so its set is directly differenceable (**5 → 8 rows**, the three added being
this pass's unconditionality rows, no rename, same scope).

**A second instrument, run on all eight entries plus three controls.**
`prove_failability.py` and the predicate table are one instrument measured twice, so the row sets
were also derived statically, without pytest and without touching the tree:
`docs/builder/temp-tests/042/worker3_pass2_replay_probe.py` extracts the landed
`_TEMPLATE_CONTRACT` and all **seven** predicate helpers verbatim by `ast` and evaluates them
against in-memory mutated copies of the asset. It reproduces **all eight** of Worker 2's pass-2
node-id sets exactly, entries 6 and 8 included, and **0 rows fail on the unmutated asset**. (The
prior pass's probe is one instrument behind, as Worker 2 warned; this is its successor, not an
edit of it — both are kept.)

#### The four new absence needles, checked against upstream's actual asset

This is the check the disclosed nav-lookup drift demands be applied to every new row of the same
kind: an absence row whose needle never occurs in the thing it guards against can never fail and
reads exactly like a working one. Occurrences — not matching lines — in
`~/projects/strawberry-django-main/strawberry_django/templates/strawberry_django/debug_toolbar.html`
and in the port:

| Row | Needle | upstream | port |
| --- | --- | --- | --- |
| `no-upstream-single-argument-parse` | `update(origParse(text))` | **1** | 0 |
| `no-upstream-own-hasownproperty-call` | `data.hasOwnProperty("debugToolbar")` | **1** | 0 |
| `no-upstream-value-returning-panel-map` | `.map(([id, panel])` | **1** | 0 |
| `no-upstream-chained-panel-title-write` | `.querySelector("h3").textContent` | **1** | 0 |
| `no-document-level-nav-lookup` (tightened) | `.getElementById(\`djdt-${id}\`)` | **1** | 0 |
| `no-document-level-nav-lookup` (**old** needle) | `document.getElementById(\`djdt-${id}\`)` | **0** | 0 |
| `no-post-scrub-read-of-panels` (pre-existing) | `data.debugToolbar.panels` | **1** | 0 |
| `no-post-scrub-read-of-request-id` (pre-existing) | `data.debugToolbar.requestId` | **1** | 0 |

Every absence row in the landed table — the four new ones, the tightened one, and the two that
predate this pass — names a spelling upstream actually carries. None is inert. The disclosed
drift is confirmed in both directions: the old needle was `0` upstream (upstream wraps
`document` / `.getElementById(…)` / `.querySelector("small")` across three lines, so the row it
replaced could not have caught the verbatim paste it named), and the tightened one is `1`.
Worker 2's "measured, not assumed" claim about that edit is itself measured here.

#### The declined optional row: the reasoning holds, and the number is the reason

Worker 3's pass-1 suggestion of `_present("origJson.apply(this, arguments)")` was declined on two
grounds; both check out.

- *No revert to detect.* Upstream's `Response.prototype.json` block is
  `return origJson.apply(this, arguments).then((data) => update(data));` — byte-identical to the
  port's. Read in upstream's asset directly: there is no upstream spelling for an absence row to
  name, so this is a preserved invariant, not a divergence, and the comment's per-kind claim
  ("a preserved invariant carries the row pinning the upstream write the port keeps") is
  satisfied by `response-json-wrapper` without it.
- *The narrow mutation yields one row.* Measured rather than argued: entry **3b** replaced
  `origJson.apply(this, arguments)` with `origJson.call(this)` — the narrowest removal of what
  such a row would pin, leaving `Response.prototype.json = function` and therefore
  `_TEMPLATE_MARKER`'s needle intact — and **0 of 77 rows fail**. Adding the row would make that
  set exactly `{origJson-forwarding}`: one row, weakly pinned, which is the shape the rule
  forbids. The wide alternative is worse and Worker 2 named it correctly: deleting the whole
  wrapper block also deletes `_TEMPLATE_MARKER`'s needle — confirmed by the probe's control `Y`,
  where the block's removal fails `[response-json-wrapper]` inside the table and would additionally
  break the M1 positive controls and the HTML `Content-Length` row, i.e. a mutation reaching well
  past its boundary. Decline accepted.

#### Preserved-invariant controls, measured

Two controls the probe ran to keep this review's own claims honest: dropping
`heading.textContent = panel.title;` still fails exactly `[panel-title-write]` (**1 row**), and
deleting the `Response.prototype.json` block fails exactly `[response-json-wrapper]` inside the
table (**1 row**). The preserved invariants are therefore still one row each — which is the
residual behind the spec sentence in `### Notes for Worker 1` item 1, and the reason that sentence
cannot be left as written.

### High:

None.

### Medium:

None. M3-1 is closed, and the check that would have caught a defect had one been there is the
absence-needle table above plus the seven independent re-runs, not the builder's prose.

### Low:

#### L4-1 — the conditional-scrub rows are written against two spellings of the weakening, and a third spelling still fails 0 of 48 rows

`tests/middleware/test_debug_toolbar.py` #"scrub-immediately-follows-capture", against
`django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
#"const toolbar = data.debugToolbar;".

Measured, not argued (`worker3_pass2_replay_probe.py`, the same instrument that reproduced all
eight entries). Insert an early bail **above** the capture instead of wrapping the scrub:

```javascript
      if (!isRecord(data.debugToolbar)) return data;   // or its braced twin
      const toolbar = data.debugToolbar;
      delete data.debugToolbar;
```

The scrub is now conditional — a malformed `debugToolbar` value returns with the server-only key
intact, which is exactly the leak Revision 8 closed — and **0 of 48 rows fail**, in both the
inline and the braced spelling. Adjacency holds (nothing sits between the capture and the scrub),
the scrub is still alone on its line, and the braces still balance. The two-row and two-row
results this pass records for the wrapped-condition spellings are real; they just do not cover
this one.

**This is my own prescription coming back.** Pass 1's L3-1 named the mutation
`if (isRecord(toolbar)) delete data.debugToolbar;` and prescribed "an adjacency predicate over
`const toolbar = data.debugToolbar;` immediately followed by `delete data.debugToolbar;`". Worker 2
implemented that faithfully and added two more rows on top. The gap is in the finding, not the
fix: it was written against an input spelling, and `BUILD.md` `### Fail-open shapes` says a guard
written that way leaves the next spelling flowing through — the reviewer's own first prescribed
guard being insufficient is the worked example that section carries.

**The answer to pin, if this is closed:** *nothing returns between the entry guard and the scrub*
— one row, e.g. no `return` occurring between the entry guard's own `return data;` and
`delete data.debugToolbar;`. That is the property stated as the answer rather than as a list of
ways to break it, and it subsumes all three spellings measured so far.

**Recorded reason for closing it here rather than looping a third builder pass.** The shipped
asset is correct; this is a pinning gap, not a defect. The boundary is not weakly pinned by any
recorded measurement — its deletion fails 8 rows and each wrapped-condition spelling fails 2 —
and the table comment's enumeration of what the three rows check ("nothing between the capture and
the scrub, the scrub alone on its line, the scrub not nested inside a block of its own") is
accurate clause for clause; only the framing half-sentence above it reads wider than the rows
deliver. Worker 1 owes a `## Test plan` Test 16 amendment for this cohort in any case (item 1
below), so the decision of whether one more row joins that amendment sits with the pass that is
already editing the contract, with this measurement in hand. Routed, not held.

#### L4-2 — `_adjacent` forbids a comment between the capture and the scrub

`tests/middleware/test_debug_toolbar.py` #"def _adjacent(first, second):".

`rest[: rest.index(second)].strip() == ""` means any comment inserted between
`const toolbar = data.debugToolbar;` and `delete data.debugToolbar;` fails the row, though the
scrub would still be unconditional. Fails **closed** and loudly, with the row's own name, and the
asset's explanatory comment for this block sits above the capture rather than between the two, so
nothing fires today. **Closed with that reason**; noted only so a future editor who meets a red
`[scrub-immediately-follows-capture]` after adding a comment knows the row is doing what it says
and the one-line fix is to allow comment lines in the span, never to delete the row.

### DRY findings

- **`_adjacent` / `_own_statement_line` / `_unnested_within` — existence challenge considered,
  not raised.** Three helpers, one call site each, which is the "helper extracted too early"
  shape. Against deletion: the table's row form is `(name, callable)`, so each predicate must be a
  callable either way, and the three join four established constructors (`_present`, `_absent`,
  `_defined_once`, `_ordered`) whose idiom they follow exactly; inlining a brace-count or an
  adjacency scan as a lambda inside the table would hide the one thing a reader of this table
  needs to see, which is what each row claims. Deleting them removes no indirection and costs
  legibility. Not a challenge.
- **`_unnested_within` is a brace counter, not a JavaScript parser**, and its docstring says so.
  Checked for the fail-open direction: a missing opener or needle returns `False`, a wrapped block
  leaves one unclosed brace, and a stray `{` in a future string or comment inside the span would
  fail the row rather than pass it. The one shape that could make it pass while nested — an
  unbalanced `}` appearing in a comment in the same span — is not reachable without deliberately
  writing it, and adjacency catches the same weakening independently. Sound.
- **Needle literals repeat, now across two spellings of one line.** `delete data.debugToolbar`
  (5 rows) and `delete data.debugToolbar;` (3 new rows) — eight sites for one asset statement,
  differing only by a semicolon. The prior pass recorded the reason this duplication is left
  alone (it is self-detecting: reword the asset line and eight rows fail loudly in one run, which
  is the opposite of the silent rot the DRY rule exists to prevent) and that reason still holds.
  What is new is the **two spellings**: they are not load-bearingly different — the semicolon-less
  needle is simply looser and both match the shipped line — so if the file is re-opened for
  anything, collapse them to one module constant used by all eight rows. Recommended, not
  required; not a finding against this diff.
- **No new row repeats a needle an existing row already pins.** Pass 1's "incomplete if" condition
  on M3-1, checked by `ast` over the landed table: the four new absence rows carry needles no
  other row uses, and the three scrub rows share one needle but each answers a different
  falsifiable question and each fails for a different weakening (measured: inline → adjacency +
  own-statement; braced → adjacency + nesting). The row count still tracks guards.
- **The regex-over-`pyproject.toml` governance idiom** remains at three sites in two files, as the
  prior pass routed. This pass did not touch it and nothing re-opens it.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` — **empty**. `__all__` and the re-export
list are unchanged; this pass added three module-private test helpers and seven table rows, and no
package file at all.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; this pass's diff is one package-tier test file. It modifies no docs, release
metadata, KANBAN or archive surface. The spec and rationale edits recorded under
`### Spec changes made (Worker 1 only)` are the planning pass's and were read as review context
only, never edited.

### What the 48 rows do and do not prove

The pass-1 section of this name applies verbatim to the wider table, and this pass changes nothing
about it in kind. Restated because the table grew and a bigger green run is a bigger temptation:
**every one of the 48 rows is a text predicate over the asset file.** `_present`, `_absent`,
`_defined_once`, `_ordered` and now `_adjacent`, `_own_statement_line` and `_unnested_within` all
operate on `template.read_text()`. The asset is never parsed as JavaScript, never loaded into a
DOM, never executed.

The seven new rows prove: upstream's five named spellings are **not in the file**, and the scrub
sits adjacent to the capture, alone on its line, and at `update`'s own block level. They prove
**nothing** about whether a silent revert would actually break anything at runtime, whether
`isRecord` returns what it should, or whether the scrub runs on any real payload. The absence rows
in particular are worth naming precisely: they detect a *paste of upstream's text*, which is the
failure mode the divergence family exists to prevent, and they detect nothing else — a rewrite of
the same hole in different words passes all seven. Whether this repo takes on a JS runtime is
already escalated and homed at close-out; this is the label the table needs, not a re-raise.

### Dispatched findings checklist — walked

This pass added no boxes; all five remain `- [x]` from pass 1 and each still has its matching fix
in the diff. Re-walked against the current tree rather than against the pass-1 review:

- **M1** ✓ four rows with per-row positive controls; re-measured at 4 rows in the pass-1 re-run and
  untouched since (`tests/middleware/test_debug_toolbar.py` is the only file this pass edited and
  the encoded-response test is not in its diff).
- **M2** ✓ the table is now 48 rows under the same function name; every one of the seven diverged
  families fails ≥ 2 rows on its own mutation, measured twice.
- **M3** ✓ both source files byte-unchanged; digests re-measured above.
- **M4** ✓ unchanged; the gated trio is still gated in both directions and the comments still carry
  no population numeral (scanned mechanically: every numeral in a comment or docstring of either
  file names the **gated** trio, a per-row rule, or upstream's line wrapping — none is a live count
  of a population this cohort edits).
- **Stale docstring line** ✓ unchanged; the AST-identity warrant stands on the unmoved digest.

### Worker 2's pass-2 claims, verified

Each was treated as a hypothesis. What was re-derived, and how:

- *"Both source files are byte-unchanged."* `shasum -a 256` on both — matches the two digests in
  the pass-1 record. So the `none` hot-path and `none` floor declarations need no re-derivation,
  and re-running the AST-identity proof would have measured a file that did not move.
- *"No numeral for any population appears anywhere in the diff."* Checked literally and wider than
  the diff: `tokenize` over every comment and `ast` over every docstring in both `.py` files, for
  digits and number-words. The table's block comment and the parametrized test's docstring carry
  none; the surviving "three" is M4's **gated** trio, which is the enumeration M4's fix
  deliberately kept. The routed Test 16 replacement wording in `### Notes for Worker 1` also
  carries none (regex-scanned).
- *"No row removed or renamed, so every node-id set in the two prior records still resolves."* The
  load-bearing claim, checked mechanically rather than read: every `test_…[…]` id appearing in
  `proofs-report-cohort-c.md` and `proofs-report-worker3.md` was differenced against
  `pytest --collect-only` at the recorded scope — **all resolve**. Two ids do not, and both come
  only from Cohort B's pre-split `proofs-report.md`
  (`test_encoded_response_gets_no_package_mutation[graphiql_html_append]` and the un-parametrized
  `test_template_port_invariants_and_robustness_divergence`); both were retired by pass 1 with its
  arithmetic recorded, not by this pass.
- *"41 → 48 rows, seven added, one needle tightened."* `ast` diff of the landed table against the
  pass-1 table (preserved verbatim in `worker3_contract_table_probe.py`): 0 rows removed, 0
  renamed, exactly 7 added, exactly 1 predicate argument changed — `no-document-level-nav-lookup`,
  the disclosed one. Nothing undisclosed moved.
- *"27 → 70 → 77, `70 + 7`."* `pytest --collect-only` at the recorded scope collects **77**, and
  the seven independent pre-mutation baselines all read `77 passed, exit 0`.
- *"The reviver rows were regrouped, not renamed."* Confirmed by the same `ast` diff: both ids are
  unchanged and the table is a `parametrize` argument, so order does not enter a node id.
- *L3-2's premise, "nothing shipped is falsified".* Re-read both spec sections rather than taking
  it: `## Borrowing posture`'s payload-shape bullet scopes the predicate to "the captured
  `toolbar`, its `panels`, and each `panel` inside the loop", and `## Edge cases and constraints`
  scopes its bullet to a value "not an object with an object `panels` — or whose panel entries are
  not objects". Neither claims id safety. The premise holds.

### L3-2: judging the reasoning, not just noting it

Asked directly: is "the spec says seven" a legitimate reason to leave a reachable throw in a
patched global, or is it the tail wagging the dog?

**As a routing answer it is legitimate; as a disposition it would not be**, and the pass wrote it
as the former. A builder may not edit the spec (`BUILD.md` `## Spec reconciliation`), and landing
a guard the `## Borrowing posture` enumeration does not carry would falsify the contract in the
direction nobody audits — which is the defect class this whole cycle exists to retire. Refusing to
falsify a contract you are forbidden to amend is not deference; the test is whether the question
was *routed* or *buried*, and it was routed, with three resolution paths and the spec surface each
one needs. `BUILD.md` `### Contract-level findings are escalated as maintainer decisions` is the
rule that puts this call above a worker, and `worker-3.md` says the same for the existence
question. I escalated rather than held it last pass and I hold to that.

Two things sharpen it for whoever decides, neither of which the record carries yet:

1. **Reachability, measured.** The loop's `id` is a `panels` key, and the middleware writes those
   keys as `panel.panel_id` (`django_strawberry_framework/middleware/debug_toolbar.py::_get_payload`), i.e. debug-toolbar's own
   class-derived identifiers, which are always valid CSS identifiers. No payload this package
   produces can reach the throw. It needs a *foreign* `debugToolbar` key in some other JSON the
   GraphiQL page parses — the same reachability class as M3, which was graded Medium and fixed, but
   one door further in and behind three record checks.
2. **The amendment may be smaller than an eighth form.** Worker 2 frames the fix as a new
   divergence, which makes "seven spots" become eight across the spec, the DoD and Test 16. It can
   equally be read as completing the **existing** best-effort-per-panel form, whose own bullet
   already promises that "a panel present in the payload but missing from the current toolbar DOM
   cannot throw inside the patched `JSON.parse`" — an id that cannot be *resolved* is the same
   promise as a node that cannot be *found*. Under that reading the amendment is one clause in an
   existing bullet plus one row, and the family stays at seven. Worker 1 should pick the framing
   before the wording; they lead to different spec surfaces and only one of them touches the DoD.

Either way it is not this cohort's to land, and nothing it ships is falsified by leaving it.

### What looks solid

- **The remedy chosen is the one that catches the failure mode.** Every mutation in this cycle's
  three proof records restores upstream's text, and until this pass the table caught them only
  because the port's spelling vanished — nothing asserted upstream's form was absent. Now every
  diverged form carries both halves, and the needles are the real ones: seven of seven occur in
  upstream's asset and none in the port, counted as occurrences.
- **The disclosed drift was disclosed in the direction that costs the builder something.** The
  tightened nav needle means the pass shipped the admission that a row already in the tree had been
  inert since it was written. That is the harder half to say, and it was measured before it was
  said — reproduced here in both directions.
- **The scrub's unconditionality is pinned by mechanism, not by one predicate.** Adjacency alone
  catches both wrapped spellings; the other two each clear the weakly-pinned floor for the one
  spelling adjacency would otherwise hold at a single row. Each is a statement about the answer,
  and the three fail in the disjoint pairs the record claims.
- **The count discipline held under pressure.** The pass that was sent back for publishing a count
  nothing gates re-derived the population by `ast` rather than adopting either circulating figure,
  and published **no** numeral for it — verified by scanning every comment and docstring in both
  `.py` files, not by reading the diff.
- **Every entry's failing set stays inside its own family.** The two deliberate anchorings from
  pass 1 still hold under the wider table: the per-node-guard mutation fails
  `no-upstream-chained-panel-title-write` and **not** `panel-title-write`, and the per-panel-loop
  mutation touches no `panel-record-*` row. Confirmed by both instruments.

### Temp test verification

- `docs/builder/temp-tests/042/proofs-worker3-pass2.json` — this pass's seven-entry manifest. All
  four prior manifests and all four prior reports are preserved unchanged beside it.
- `docs/builder/temp-tests/042/proofs-report-worker3-pass2.md` — the emitted record, tool exit 0.
- `docs/builder/temp-tests/042/worker3_pass2_replay_probe.py` — the second instrument: the landed
  table and all seven helpers extracted verbatim by `ast`, evaluated against in-memory mutated
  assets, plus the upstream/port occurrence counts for every absence needle and the two
  preserved-invariant controls. Deliberately not a `test_` module: it is a review probe. It
  supersedes the pass-1 probe (which is one instrument behind, as Worker 2 noted); both are kept so
  the three-way comparison stays readable.
- **Disposition:** all stay under `temp-tests/`. None caught a production bug — L4-1 and L4-2 are
  findings about the pinning, and L3-2's disposition is a contract question — so nothing is
  promoted. The probe's content should not be promoted either: the landed table is the permanent
  instrument and the probe is scaffolding for reviewing it.

### Notes for Worker 1 (spec reconciliation)

1. **`## Test plan` Test 16 still says something false, and the correction is Worker 2's routed
   text plus one thing it misses.** The sentence "Every form is pinned by at least two rows, at
   least one of them an ordering or absence predicate a stray substring cannot satisfy" is now true
   of all seven **diverged** forms (measured above) and still false of the **preserved
   invariants**, which Test 16's own enumeration puts inside "every form": dropping
   `heading.textContent = panel.title;` fails exactly one row and deleting the
   `Response.prototype.json` block fails exactly one row inside the table. Worker 2's replacement
   wording under its `### Notes for Worker 1` item 1 fixes this correctly by making the claim
   per-kind, and it carries no numeral. Two amendments to it before it lands:
   - its parenthetical names **five** upstream forms, but the table carries **seven** absence rows
     — `no-post-scrub-read-of-panels` and `no-post-scrub-read-of-request-id` also name upstream
     spellings (`data.debugToolbar.panels`, `data.debugToolbar.requestId`, one occurrence each
     upstream). Either name all seven or name none; a short enumeration presented as the population
     is the shape this cycle is retiring.
   - **sweep the rationale in the same pass.**
     `docs/SPECS/appx/spec-042-debug_toolbar-0_0_14-rationale.md`
     `### Borrowing posture — the template port` #"each form, this one included, fails at least two
     node ids when removed" is the same claim in the companion file, and Worker 2's routing names
     only the spec. `START.md` "Sweep both files of a pair" — fixing one leaves the other
     falsified.
2. **L4-1, above: one more row would close the conditional-scrub family against every spelling
   measured.** You are amending Test 16 anyway; the answer to state is *nothing returns between the
   entry guard and the scrub*. Your call whether it joins the amendment (which re-loops Worker 2
   for one row and one proof entry) or is recorded as accepted with the measurement. Recorded here
   either way so nobody re-derives it: the early-bail-above-the-capture spelling fails **0 of 48**
   rows today, in both its inline and braced forms.
3. **L3-2 is escalated unchanged, with the framing question added** (`### L3-2: judging the
   reasoning` above): decide whether `CSS.escape` is an **eighth** divergence or a clause completing
   the existing best-effort-per-panel form, because the two need different spec surfaces and only
   the first moves "seven spots", the DoD and Test 16's form count. Reachability is now measured
   rather than assumed: the middleware keys `panels` by `panel.panel_id`, so no payload this
   package produces can reach the throw.
4. **`## Borrowing posture`, the membership-guard bullet** still describes the port's bail as
   `data === null`, `typeof data !== "object"`, `!Object.prototype.hasOwnProperty.call(...)` while
   the first two are spelled `!isRecord(data)`. Unchanged by this pass; behaviourally exact, one
   clause stale as a description. Your call whether a behavioural description should track a
   spelling.
5. **Worker 2's disclosed needle tightening needs no spec edit** (nothing in the spec states a
   needle) but it does belong in the rationale's Borrowing-posture change record as a measured
   fact: the row that was supposed to catch a `document`-level nav lookup had been inert since it
   was written, because upstream wraps that call across three lines. That is a reusable lesson
   about absence rows, and it is currently recorded only in a per-cycle artifact that closes with
   the cycle.
6. **Nothing this pass found changes any routed deferred item**: the DRF false-population comment
   (`django_strawberry_framework/rest_framework/__init__.py` #"three-places-that-must-agree" — re-
   confirmed as the package's last one, four sites total across the two pairs), the
   `DEBUG_TOOLBAR_FLOOR` refinement in `utils/imports.py` (trigger fired), M4's documentation half
   (`docs/README.md` #"django-debug-toolbar>=7.0.0" and the DB-backed `docs/GLOSSARY.md` entry), the
   JS-runtime question homed at close-out, and the concurrent session's queued live-promotion sweep
   over this test file. All still owed a named owner in `bld-042-final.md`.
7. **Baseline-dirty population is a reading, not a constant.** Re-read at the end of this pass;
   only `tests/middleware/test_debug_toolbar.py` plus the two byte-unchanged source files belong to
   this cohort. Compare against a fresh reading at the final gate, never against any count recorded
   in this artifact.

### Review outcome

`review-accepted`.

No High, no Medium. Two Lows (L4-1, L4-2), each recorded with the reason it closes here rather
than looping a third builder pass, and L3-2 escalated unchanged with its framing question
sharpened. The Medium that sent the cohort back is discharged in the way that was worth more than
the correction: every diverged form now carries the row that catches a silent revert to upstream's
text, and — the check that would have caught a defect had there been one — **every one of those
needles occurs in upstream's actual asset and none in the port**, counted as occurrences in both
files. The one needle that did not, the pre-existing nav row, is the drift Worker 2 disclosed and
tightened; it was inert, and it now fires.

The seven independent re-runs reproduce Worker 2's node-id sets **exactly, set for set**, at the
recorded scope, with a `77 passed / exit 0 / 0 errors` baseline measured fresh before each; a
second instrument built from the landed table reproduces all eight entries including the two
accepted on record; no row was removed or renamed, so every node-id set in this cycle's earlier
records still resolves; both source files are byte-identical to the first pass, so the AST-identity
warrant behind both `none` declarations is untouched; and no mutation is live.

What the table proves is text identity against an upstream paste. It is not behavioural coverage,
the asset still has no executing test, and nothing here should be read as saying otherwise.


---

## Final verification (Worker 1)

Ran against the tree as it stands, not against the reports. Everything below that reads as a
measurement was re-derived in this pass; where a prior pass's figure is quoted it is named as a
quotation and differenced against my own reading.

### Dispatched findings checklist — audited against the diff

All five boxes are `- [x]`. Each was checked against `git diff HEAD -- <file>` rather than
against the build reports; none is over-ticked, none is under-ticked, and nothing is left `- [ ]`,
so no deferral reason is owed.

- **M1** — the widened test is in the diff: `{graphiql_html_append, operation_json_injection}` x
  `{gzip, br}`, each row driving its body through `_postprocess` **twice** (the header-free
  positive control first, asserting `was_mutated`, then the header-bearing twin asserting
  `result is response`, byte-identity and no `debugToolbar` key). Read in the landed source, not
  summarised from the report. The falsified "reaches BOTH mutation sites" docstring is gone.
- **M2** — the monolithic body is replaced by `_TEMPLATE_CONTRACT` under the same function name.
  Counted mechanically by `ast` over the landed table rather than read off the reports:
  **48 rows**, predicate constructors `_present` 31, `_absent` 7, `_ordered` 6, `_adjacent` 1,
  `_own_statement_line` 1, `_unnested_within` 1, `_defined_once` 1. Every row id is a name.
- **M3** — the asset diff carries `isRecord` defined once at IIFE scope, the entry guard's
  null/typeof half rewritten onto it, `if (!isRecord(toolbar) || !isRecord(toolbar.panels))
  return data;` after the scrub and before the loop, and `if (!isRecord(panel)) return;` as the
  loop body's first statement. The scrub is unconditional and first. No `try`/`catch`, no
  input-spelling enumeration, `setAttribute` upstream-verbatim with the coercion reason in a
  comment. Cohort B's L1 (the missing semicolon) is closed in the same diff.
- **M4** — the module's comment block and the test file's mirror both name the gated trio and
  what compares them, then say anything else restating the floor is gated by nothing and a bump
  sweeps the tree for the specifier. No population numeral survives at either site. The new
  governance row is in the diff and compares the `pyproject.toml` row to the re-typed literal
  **and** the literal to the hint.
- **Stale docstring line** — `No other Python behavior differs.` is gone from the module
  docstring; the three Python divergences are enumerated by name (the `isinstance(view, type)`
  guard, `_get_payload`'s response-shape bail family, the `Content-Encoding` bail) and the
  template family is pointed at without being counted. No numeral replaced `two`.

Both production files are byte-unchanged since the first build pass, re-measured here:
`shasum -a 256` reads `5c189885117946d2122c4dd03f9153ddfab4a13c4697d669557958387af4201b`
(module) and `a1431798b18787cfe303078af4e7579b29f8d7121ede20a7f05086aaa673c6a0` (asset) — the
digests both prior passes recorded. `docs/builder/temp-tests/042/` holds no
`ACTIVE-MUTATION.json`; no mutation is live.

### Slice-local checks

| Gate | Command | Result |
| --- | --- | --- |
| Spec glossary | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-042-debug_toolbar-0_0_14.md` | `OK: 24 terms - all have glossary entries and at least one spec link.` |
| Citations | `uv run python scripts/check_citations.py --check` | `OK: 992 citations resolve (823 in 441 .py files, 169 in KANBAN.md).` — reads `.py` + `KANBAN.md` only, so it says nothing about the two files this pass wrote |
| Whitespace | `git diff --check` (whole tree) | exit 0 |
| Format | `uv run ruff format --check .` | `444 files already formatted` |
| Lint | `uv run ruff check .` | `All checks passed!` (never `--fix`) |
| Source layout | `uv run python scripts/check_trailing_commas.py --check <the two `.py` files, the asset, the spec, the rationale>` | exit 0 (explicit paths only — its default is a repo-wide auto-fix over the concurrent session's files) |
| Focused suite | `uv run pytest tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py -n0 --no-cov` | **77 passed**, exit 0, 0 collection errors. No `--cov*` flag anywhere in this pass; no full sweep run (not authorised, and the tree carries another cycle's work) |
| Rule-27 citations + link convention (own verifier, both files) | scratchpad script, positive-controlled | spec: 73 defs / 73 used refs, 0 broken in-page anchors, 0 undefined refs, 0 orphan defs, 0 broken cross-file anchors, 0 `path:NN`; **2** package-relative `utils/imports.py::require_optional_module` citations, both present at HEAD (`git show HEAD:<spec> \| grep -c` → 2) and unchanged by this pass. Rationale: 26 / 26, 0 problems |

The verifier was positive-controlled before its green was accepted: a scratch copy with one
invented `[nope]` reference and one `#no-such-heading` anchor appended reports both. Its first
run also reported 73 false "broken anchor" problems because its own slug function was stripping
code spans out of headings — the instrument was wrong, not the file, which is exactly why a
control ran before the clean reading was believed.

### Spec changes made (Worker 1 only)

Every edit states the corrected contract directly: no amendment block, no round or cohort
provenance, no "previously". Census taken before writing, occurrences rather than lines, both
files: `at least two` — spec 1, rationale 1; `fails at least` — 0 / 1; `stray substring` —
spec 1, rationale 0. Two polarities were swept, not one (the positive claim vocabulary
`at least two` / `each form` / `every form` / `one row per predicate`, and the second-polarity
vocabulary `stray substring` / `silently regress` / `ordering or absence predicate` /
`weakly pinned` / `node id`); both instruments return the same population, and a repo-wide grep
confirms no third file outside this pair carries the claim. **Retirement after this pass:** spec
0 / 0 / 0; rationale 1 occurrence of `at least two`, inside the sentence that records the claim
as retired — the same convention the file already uses for the stale `0.262.0` sites.

Spec (`docs/SPECS/spec-042-debug_toolbar-0_0_14.md`):

1. **`## Test plan` Test 16, the claim sentence** — the retired wording, quoted on one line as it
   stood ("Every form is pinned by at least two rows, at least one of them an ordering"),
   replaced by a **per-kind** statement with no count: a diverged form carries both halves of its
   divergence (the port's spelling, and the absence of the upstream spelling it replaced); a form
   whose contract is a position is pinned by index, adjacency and nesting rows; a preserved
   invariant carries the row for the upstream write the port keeps — plus what falsifies the
   claim, including *an absence row whose needle upstream does not actually carry*. Reason: the
   sentence was false of the landed table, and the correction routed to this pass carried a
   parenthetical naming **five** upstream forms where the landed table carries **seven** absence
   rows (re-derived by `ast` over `_TEMPLATE_CONTRACT` in this pass, not taken from either
   report: `no-upstream-single-argument-parse`, `no-upstream-own-hasownproperty-call`,
   `no-upstream-value-returning-panel-map`, `no-document-level-nav-lookup`,
   `no-upstream-chained-panel-title-write`, `no-post-scrub-read-of-panels`,
   `no-post-scrub-read-of-request-id`). **The sentence needs no number at all**: this cycle has
   already retired two counts of populations nothing gates, and a third — "seven" today, wrong
   the day an eighth absence row lands, which the re-pass below will land — would be the same
   instrument in a new place. Stated by mechanism instead. *Triggered by the Medium the review
   raised against the table's own comment, and by the correction to its routed replacement.*
2. **`## Test plan` Test 16, the mandatory-scrub clause** — now "ordering **and
   unconditionality**", naming the rows an index comparison cannot supply: that **nothing returns
   between the entry guard and the scrub**, that nothing but whitespace separates the capture
   from it, that it stands alone on its own line, and that it is not nested inside a block of its
   own. Reason: `## Borrowing posture` already states "The scrub stays unconditional and precedes
   this guard", and until the last build pass nothing gated the first half. The first clause is
   the answer-shaped one and is **not yet landed** — see `### L4-1` below. *Triggered by the Low
   on the conditional scrub and by its successor.*
3. **`## Borrowing posture`, the membership-guard bullet** — the port's bail was described as
   `data === null`, `typeof data !== "object"`, `!Object.prototype.hasOwnProperty.call(...)`;
   the asset now spells the first two as `!isRecord(data)`. Rewritten to describe the bail by the
   record predicate plus the `hasOwnProperty.call` clause. Reason: a spec describing a spelling
   the file does not carry is stale as a description, and the landed row that pins it is named
   `entry-guard-uses-record-predicate`. *Triggered by the review's routed item; this is the
   five-homes re-audit finding it as well.*
4. **`## Borrowing posture`, the payload-shape bullet's read-site list** — `data` itself at the
   entry guard added to "the captured `toolbar`, its `panels`, and each `panel`". Reason: the
   asset applies `isRecord` at four sites and the rationale already said four; the spec listed
   three, so the pair disagreed. *Five-homes re-audit.*
5. **`## Borrowing posture`, the best-effort per-panel bullet** — gains the panel **key**: the
   key reaches `querySelector` only through a form the selector parser always accepts, so a key
   that cannot name a node skips that one panel exactly as an absent node does, instead of
   raising a `DOMException` out of the patched globals; and the sentence saying why this is that
   form rather than a new one. *L3-2, framing decided below.* The family stays at seven and the
   DoD is untouched.
6. **`## Edge cases and constraints`, "A `debugToolbar` value the bridge cannot read"** — gains
   the panel-key half of the same contract and records that a real middleware payload keys its
   panels by the toolbar's own class-derived panel ids. *L3-2.*
7. **`## Test plan` Test 16, the diverged-form enumeration** — "the skip-on-absent-content-node
   panel loop" is now "… with its selector-safe panel key". *L3-2.*
8. **`## Definition of done`, the test item** — the template-port guard clause now states that
   each diverged form carries both the row pinning the port's spelling and the row pinning
   upstream's replaced spelling absent. Reason: the DoD is one of the five contract homes and was
   the only one that still described the table in terms the corrected Test 16 no longer uses.

Rationale (`docs/SPECS/appx/spec-042-debug_toolbar-0_0_14-rationale.md`):

9. **`### Borrowing posture — the template port`** — its closing sentence carried the same false
   claim in the companion file (retired wording, quoted on one line as it stood:
   "fails at least two node ids when removed"), and the
   routing that reached this pass named only the spec. Rewritten: the split's value is stated as
   distinguishability (one node id for any form and one for all of them, before), and a new
   change record says what the table is allowed to claim about itself, why the remedy was the
   missing rows rather than a corrected sentence, and carries two measured lessons — **an absence
   row whose needle the borrow never spells is inert and reads exactly like a working row** (the
   nav-lookup needle, zero occurrences upstream until it was tightened), and **"unconditional" is
   a property of the answer, not of a spelling** (the early-bail-above-the-capture case). This is
   `START.md` #"Sweep both files of a pair": the named set was a sample of the claim's
   vocabulary, and the sweep above establishes the population.
10. **`### Borrowing posture — the template port`, new change record** — the panel key's trip
    through the selector: why it is the best-effort per-panel form rather than an eighth
    divergence, that no payload this package produces can reach it, and the rejected
    alternatives — leaving it as documented behaviour, recording it as an eighth form, a
    `try`/`catch`, and an enumeration of invalid-identifier spellings. *L3-2.*
11. **`### Decision 5`, the three-places change record** — it published "five live sites" as a
    measured population. Re-measured in this pass with a looser needle:
    `CHANGELOG.md` #"Soft-dependency feature floors" restates the floor as
    `django-debug-toolbar \`>=7.0.0\``, which
    the tight needle misses because of the backtick between the name and the specifier. Rewritten
    to record the sweep, the miss, and the lesson that **any replacement count is bounded by the
    spelling of the needle that produced it**; the rejected "correct the comment to five" is now
    "correct it to the measured number". Reason: a published count of an ungated population
    inside the file that argues against publishing them is the same defect one level up.
12. **`## Post-ship corrections`, the opener** — "Nine findings … plus one … The tenth is the one
    correction that moved the shipped asset" restated without the counts, and it now names the
    panel-key correction beside the payload-shape guard. Reason: the count was about to become
    false, and it is a count of a population this very pass edits.

### `### L4-1` — the conditional-scrub gap: re-loops, and why

**Measured independently before deciding.** The landed `_TEMPLATE_CONTRACT` and its seven
predicate helpers were extracted from the test file by source slice and evaluated in-process
against in-memory mutations of the asset (no file in the tree was touched, no `git` invoked).
Unmutated: **0 of 48** rows fail. The two wrapped-condition spellings fail 2 and 3 rows
respectively (`scrub-immediately-follows-capture` + `scrub-is-its-own-statement`; and the braced
form additionally `scrub-not-nested-inside-update` — one row more than the build pass recorded,
because my braced spelling puts the scrub inline inside the block; the difference is in the
mutation, not in the table). **The early bail placed above the capture fails 0 of 48, in both its
inline and its braced spelling** — the review's figure reproduces exactly.

**Decision: `revision-needed`, one row, routed back through Worker 0.** The reasoning, weighed
honestly:

- The shipped asset is correct and the boundary is not weakly pinned by any recorded
  measurement — deleting the scrub fails 8 rows. What is unpinned is one **half** of the
  contract: that the scrub is unconditional, for a whole class of weakening.
- The three landed rows are three *spellings* of the weakening. `BUILD.md` `### Fail-open shapes`
  is explicit that a guard written against input spellings leaves the next spelling flowing
  through, and that the reviewer's own first prescribed guard being insufficient is that
  section's worked example. The same lesson has now arrived twice in this cycle — once in the
  asset (the payload-shape guard) and once in the table.
- The half that is unpinned is the one Revision 8 exists to hold, and the leak it guards is a
  server-only key flowing back into the GraphiQL response. That is the class this repo is least
  tolerant of, and `AGENTS.md` rule 5 forbids the defer-the-real-fix shape even with a follow-up
  card.
- The cost is one row and one proof entry in a file the re-pass is opening anyway for L3-2.
  Accepting it instead would mean publishing a Test 16 clause that says the rows pin the scrub
  unconditional while a measured spelling class passes — a fourth self-falsifying instrument, in
  the cycle whose subject is that defect.

**What the re-pass must land:** one row pinning the **answer** — *nothing returns between the
entry guard and the scrub* — not a fourth spelling; e.g. no `return` occurring between the entry
guard's own `return data;` and `delete data.debugToolbar;`. It owes a failability entry measured
against all three weakenings (the two wrapped spellings and the early bail, inline and braced),
each failing set staying inside the scrub family. The spec clause it implements is already
written (spec change 2).

### `### L3-2` — the framing decided, before anyone words it

Two selector sites interpolate the panel key: `djDebug.querySelector(\`#${id}\`)` behind
`if (panel.title)` and `djDebug.querySelector(\`#djdt-${id}\`)` behind `if (panel.subtitle)`.
Both raise a `DOMException` for a key that is not a valid CSS identifier, out of the patched
globals. Re-derived rather than accepted: the reachability claim holds — `_get_payload` keys
`panels` by `panel.panel_id`, so no payload this package produces can reach it, and it needs a
foreign `debugToolbar` key in some other JSON the page parses. That is the **same reachability
class as the payload-shape hole**, which was graded Medium and fixed under the no-defer rule.

**Decision: the guard lands, and it completes the existing best-effort per-panel form rather
than adding an eighth.** Reasons, and the rejected alternative each answers:

- *Not documented behaviour.* Scoping the contract to "a payload key we cannot parse crashes the
  caller's parse" documents a defect as a promise, in a family whose stated rule already promises
  the opposite for a panel whose node is absent. The rationale's own M3 entry records that
  deferring that hole was rejected under `AGENTS.md` rule 5; this is the same hole one door in.
- *Not an eighth divergence.* An id that cannot be **resolved** and a node that cannot be
  **found** are one promise. The best-effort per-panel bullet already carries that promise, so
  the clause belongs inside it: `## Borrowing posture` stays at seven spots, the DoD's "seven
  documented guard divergences" does not move, and Test 16's form count is unchanged. A form
  count that grows for a clause inside an existing rule stops describing anything.
- *Not a `try`/`catch`, and not an enumeration of invalid-identifier spellings* — both already
  rejected in the rationale for this family, and re-rejected here for the same reasons.
- The contract is stated as an answer: **the key reaches `querySelector` only through a form the
  selector parser always accepts.** How that is spelled in the asset is the builder's, subject to
  the contract; the obvious spelling makes the lookup total so the existing `content === null` /
  `nav !== null` skips do the rest, which is why this adds no new failure path.

Worker 1 writes no source, so this is `revision-needed` routed through Worker 0 to a builder:
the asset change at **both** selector sites, the Test 16 rows for it, and a failability entry.

### The five contract homes, re-audited against what landed

The spec's amendments were written before the code existed; this is the pass that checks them
against the tree. Walked home by home, each against the landed diff rather than against the
reports:

| Home | Reading |
| --- | --- |
| Decision (`## Borrowing posture`, Decisions 5 / 6) | The template family's seven forms are each present in the asset and each pinned; the Python ledger's three divergences are the three in the shipped module. **Two disagreements found and fixed** (spec changes 3 and 4): the membership bullet described a spelling the asset no longer carries, and the payload-shape bullet's read-site list omitted the entry guard while the rationale's named it. Decision 5 item 3 and Decision 6 agree with the module as landed. |
| `## Slice checklist` | The Slice-1 dependency box names the gated trio and the sweep, matching the module comment and the test mirror word for word in substance. No stale count. |
| `## Edge cases and constraints` | "A `debugToolbar` value the bridge cannot read" matched the landed behaviour exactly; extended for the panel key (spec change 6). The encoded-body bullet matches the widened test. |
| `## Test plan` | Test 13a matches the landed four rows with a positive control inside each. Test 12a matches the landed governance row in both directions. Test 16's claim sentence was false and its scrub clause incomplete — both amended. Test 8's text was already corrected by the custody cohort and matches the landed `RequestFactory` unit, so the routed note about it is discharged with no further edit. |
| `## Definition of done` | "the seven documented guard divergences" agrees with `## Borrowing posture` and with the asset; the floor item's "compares all three (Test 12a)" agrees with the landed row; the test item amended (spec change 8) so it describes the table the way Test 16 now does. |

No home now disagrees with another or with the tree, **except where the tree is behind the spec
by design**: spec changes 2, 5, 6 and 7 state contracts the re-pass must land. That is the same
lead-the-tree ordering the planning pass recorded and it is stated here rather than left to be
discovered.

### Failability and fail-open confirmations

- **Every boundary carries a record.** Ten entries in the first build pass, eight in the second,
  each with the mutation, the scope as run, the pre-mutation baseline, the failing node ids
  listed, `0` collection/setup errors, and a byte-compared restore. No entry measured 0 or 1
  rows, so nothing is weakly pinned and no **why 0** judgement is owed. The review's independent
  re-runs reproduce every node-id set; I differenced the two records myself for the one mutation
  they share (the scrub deletion, 5 rows → 8 after the unconditionality rows landed) and the
  arithmetic holds.
- **No fail-open shape landed.** Read the diff for the catalogued shapes rather than trusting the
  green: the asset adds no clamp, no `or` fallback, no `try`/`catch`, and `isRecord` is a
  two-clause test whose false branch exits the permit path (`return data`) rather than coercing
  into it. The `.py` diff is non-executable — the AST-identity record (docstrings stripped,
  `12387 == 12387`) is the warrant for that, and both source digests are unmoved since it was
  taken, so it still applies.
- **One fail-open shape did land in the *test* table's contract**, which is L4-1: three rows
  written against spellings of a weakening rather than against the answer. It is routed above.

### Hot-path and floor declarations

**Hot-path: `none`** and **floor-verification scope: `none`**, both confirmed rather than
restated: the Python diff is AST-identical with docstrings stripped, so no per-request,
per-resolver, per-row or per-connection path moved, and no Django / Strawberry / channels
integration seam changed. Floor facts, copied from `docs/builder/BUILD.md` `## Floor
verification` this pass and never from memory: Django **5.2.16** on Python **3.10** with
strawberry-graphql **0.316.0**. The re-pass routed above touches the browser-side asset and one
test file, so neither declaration changes for it.

### Concurrent-session baseline

A reading, not a constant: `git status --short` at the end of this pass returns **76** paths.
This cycle's are exactly `django_strawberry_framework/middleware/debug_toolbar.py`,
`django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`,
`tests/middleware/test_debug_toolbar.py`, the spec, the untracked rationale, and the cycle's
`042` artifacts. Nothing else was read as build output, edited or reverted (`AGENTS.md` rule 34).
Compare against a fresh reading at the final gate, never against any count in this artifact.

### Notes for Worker 1 (spec reconciliation)

Items for the deferred-work catalog in `docs/builder/bld-042-final.md`. Each needs a **named
owner** with the write set it requires; an item routed forward without one dies.

1. **The floor is restated in the changelog too, and the first sweep could not see it.**
   `CHANGELOG.md` #"Soft-dependency feature floors" carries `django-debug-toolbar \`>=7.0.0\``
   with a backtick between the name and the specifier, so the needle this cycle used
   (`django-debug-toolbar>=`) misses it. Ungated, correct today, fenced out. Catalogue it with
   the two doc sites below **and with the lesson**: the sweep a floor bump owes is more than one
   spelling of the needle.
2. **M4's documentation half.** `docs/README.md` #"django-debug-toolbar>=7.0.0" and the DB-backed
   `docs/GLOSSARY.md` entry restate the floor ungated. DB-backed means ORM edit plus regenerate,
   never a hand-edit.
3. **`docs/GLOSSARY.md`'s Debug-toolbar middleware entry is a measured carrier, not a suspected
   one.** Re-read in this pass: its body says "Two deliberate robustness divergences from the
   verbatim upstream borrow" and enumerates only the `isinstance` guard and `_get_payload`'s
   bail — the exact closed-count claim the module docstring retired this cycle — and it names the
   floor besides. Fenced out and DB-backed.
4. **The DRF twin is the package's last false-population comment.**
   `django_strawberry_framework/rest_framework/__init__.py` #"three-places-that-must-agree" and
   `tests/rest_framework/test_soft_dependency.py` #"three-places-that-must-agree", with no
   governance row over the `pyproject.toml` side. Same defect class as M4, different spec.
5. **The `DEBUG_TOOLBAR_FLOOR` refinement** in `utils/imports.py`, interpolated into the hint and
   gated beside the Channels / Strawberry rows. Its stated trigger has fired: the
   regex-over-`pyproject.toml` idiom now has three sites in two files. A refinement, not a
   deferred fix — catalogue it so it is not re-raised as a duplication finding against this
   cohort.
6. **The JS-runtime question**, homed at close-out by maintainer decision. Everything the table
   proves is text identity over the asset; nothing in it executes. The absence rows sharpen what
   that means: they detect a **paste of upstream's text** and nothing else — a rewrite of the same
   hole in different words passes all of them.
7. **Decision 1's "This spec lives at `docs/spec-…`" template sentence** plausibly sits in every
   archived spec under `docs/SPECS/`; the custody cohort fixed this one and could not sweep the
   rest.
8. **Two package-relative citations in the spec** (`utils/imports.py::require_optional_module`,
   twice) use a package-relative path rather than the repo-relative rule-27 form. Present at HEAD
   before this cycle, measured again in this pass, unread by any gate (`check_citations.py` does
   not read `docs/`). Low; left alone deliberately rather than widened into a spec-wide citation
   sweep.
9. **`## Implementation plan` opens "The file-level delta map for the Worker 0 build handoff".**
   Pre-existing at HEAD. It names an audience rather than attributing a change, so it is not read
   as the provenance `AGENTS.md` rule 27 bans — recorded so the next reader does not have to
   re-decide it.
10. **The concurrent session has queued work in this cohort's test file.** Its (dirty)
    `examples/fakeshop/test_query/README.md` backlog names
    `tests/middleware/test_debug_toolbar.py::test_get_payload_panel_title_only_when_has_content`
    for live promotion and two `Content-Length` refresh rows for deletion afterwards. Nothing
    collides today; whoever executes that sweep meets a file that now carries a 48-row table and
    seven predicate helpers.

### Final status

`revision-needed`.

Nothing that landed is wrong, and nothing dispatched to this cohort is unfinished: all five boxes
are ticked and audited against the diff, every boundary is pinned above the weakly-pinned
threshold under two instruments, both production files are byte-stable, and the focused scope is
77 green. What sends it back is two contracts the spec now states and the tree does not yet
carry, each a routed Low that the amendments turned into a gate:

- **L4-1** — the scrub's unconditionality is pinned by three spellings of the weakening, and a
  fourth (an early bail above the capture) fails 0 of 48 rows, re-measured here. One row pinning
  the answer — nothing returns between the entry guard and the scrub — closes it.
- **L3-2** — the panel key's trip through `querySelector`. Framing decided: it completes the
  best-effort per-panel form, so the family stays at seven and the DoD does not move; the asset
  guards both selector sites, Test 16 gains its rows, and the boundary owes a failability entry.

Both are builder work. Worker 1 writes no source, and
`docs/builder/BUILD.md` `### Isolation is non-waivable` does not bend for a small diff.

### Summary

The cohort's dispatched work is complete and correct: the `Content-Encoding` bail is pinned by
four distinguishing rows with a positive control inside each, the template contract is 48 named
rows where it was one, the bridge ignores a `debugToolbar` payload it cannot read, the floor's
gated trio is gated in both directions, and neither the module nor the test file publishes a
count of a population nothing gates. The spec and the rationale now say the same true thing about
the table in both files, describe the asset by the spelling it actually carries, and state the
two contracts the re-pass must land.

---

## Build report (Worker 2, pass 3)

Built against `## Final verification (Worker 1)`. Exactly the two items it routed back land here
and nothing else is reopened: **L4-1**, the answer-shaped rows for the scrub's unconditionality,
and **L3-2**, the selector-safe panel key at both selector sites. The module
`django_strawberry_framework/middleware/debug_toolbar.py` is **byte-unchanged by this pass** -
`shasum -a 256` reads `5c189885117946d2122c4dd03f9153ddfab4a13c4697d669557958387af4201b`, the
digest both prior passes and the final verification recorded - so the first pass's AST-identity
record still stands as the live warrant for the Python side. The asset moves for the first time
since pass 1: `a1431798b18787cf...` ->
`92cd040294ad2dba26158c652f92b9760cd35b64b91f848822a1fa093e17fa00`.

The five `### Dispatched findings checklist` boxes are all `- [x]` and were audited against the
diff at final verification; L4-1 and L3-2 are not boxes in that list, so this pass ticks nothing.
Its work is the two contracts the spec already states and the tree did not yet carry.

### Files touched

From `git status --short`, which reads **76** paths. Everything in it other than the paths below
plus this cycle's `042` artifacts is the concurrent session's baseline-dirty work - neither
edited nor reverted (`AGENTS.md` rule 34). Its two `D` entries under
`examples/fakeshop/apps/products/tests/` are theirs and were left exactly as found.

- `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html` -
  **L3-2.** The panel loop destructures the payload key as `panelId` and binds `id` to
  `CSS.escape(panelId)`; a key whose escape is the empty identifier skips that panel before
  either lookup. Both selector expressions - ``djDebug.querySelector(`#${id}`)`` and
  ``djDebug.querySelector(`#djdt-${id}`)`` - are textually unchanged, so both selector sites are
  covered by one escape at the key's entry rather than by two wrappers.
- `tests/middleware/test_debug_toolbar.py` - **L4-1 + L3-2.** One new predicate constructor
  (`_return_count_between`); two rows for the scrub's unconditionality; seven rows for the
  selector-safe key; the `_TEMPLATE_CONTRACT` block comment extended to name the return-count
  instrument and what falsifies a spelling-shaped guard row. **No existing row was removed,
  renamed or re-needled** - every node id in all three prior proof records still resolves.
- `docs/builder/temp-tests/042/proofs-cohort-c-pass3.json` - this pass's six-entry manifest, and
  `proofs-report-cohort-c-pass3.md` the record it emitted. `proofs.json`, `proofs-worker3.json`,
  `proofs-cohort-c-pass2.json`, their three reports and Worker 3's probe scripts are all
  preserved unchanged beside them. Gitignored scratch.
- This artifact; `docs/builder/worker-memory/042-worker-2.md`.

### Worker 1 final-verification items - disposition

#### L4-1 - closed by pinning the answer, not by adding a fourth spelling

Worker 1's measurement reproduces here: against the pass-2 table an early bail placed **above**
the capture fails **0 of 48** rows in both its inline and its braced spelling, because nothing
was wrapped around the scrub - index, adjacency, own-line and nesting all still match. The three
landed rows pin three *spellings* of a weakening; `BUILD.md` `### Fail-open shapes` is explicit
that this is a guess where the answer itself can be measured.

The answer the spec now states (`## Test plan` Test 16, the mandatory-scrub clause) is **nothing
returns between the entry guard and the scrub**. Two rows measure it, both through one new
constructor `_return_count_between(first, second, expected)`, which counts `return` occurrences
in the span between two needles:

- `no-return-between-entry-guard-and-scrub` - zero returns between the asset's **first**
  `return data;` and `delete data.debugToolbar;`. That first occurrence is the entry guard's own
  return, the one return that may legitimately precede the scrub, because it fires only when the
  payload carries no `debugToolbar` key at all and so can leak nothing.
- `entry-guard-return-is-the-only-one-before-the-scrub` - exactly one return between
  `function update(data) {` and the scrub. Anchored at the function rather than at a return, so
  it also sees a bail inserted **above** the entry guard returning something other than `data`,
  where the first row's span would slide down with the insertion and read clean.

Neither row names a condition, a bail, or any other form of the weakening, so neither is a fourth
spelling. Measured, not asserted: proof entries 1 and 2 apply the early bail in both spellings
and each fails exactly these two rows, where the same mutation against the pass-2 table failed
none.

#### L3-2 - the guard lands at both selector sites, inside the existing per-panel form

Worker 1 decided the framing and it is followed as written: an id that cannot be *resolved* and a
node that cannot be *found* are one promise, so this completes the best-effort per-panel form.
Verified rather than assumed: `## Borrowing posture` still reads "diverges from the borrow in
**seven** spots", `## Test plan` Test 16 still reads "each of the **seven** diverged forms", and
`## Definition of done` still reads "the **seven** documented guard divergences" - three
occurrences of `seven` in the spec, the same three as before this pass, and the DoD is untouched.
The spec is not in this pass's write set and was never opened for writing.

The contract is answer-shaped: **the key reaches `querySelector` only through a form the parser
always accepts.** The implementation applies `CSS.escape` once, where the key enters the loop
body, and both interpolation sites use the escaped value:

```
      Object.entries(toolbar.panels).forEach(([panelId, panel]) => {
        if (!isRecord(panel)) return;
        ...
        const id = CSS.escape(panelId);
        if (id === "") return;
```

`CSS.escape` is total over every **non-empty** string: its output is a valid CSS identifier for
any input, so `#<escaped>` is a selector the parser accepts and it names the element whose id is
exactly the key (`#\35 x` names the element with id `5x`, and `#djdt-\35 x` the element with id
`djdt-5x`, so the escape changes no lookup that resolves today). The one input it cannot turn
into an identifier is the empty string, whose escape is the empty identifier - which can name no
node, so that panel is skipped. That is the spec's own "resolves to nothing and skips that one
panel exactly as an absent node does", and it is a closed answer rather than an enumeration: the
escape covers every key but one and the skip covers that one.

No `try` / `catch`, no list of invalid-identifier spellings, and no new failure path - for every
key that names a real panel the escaped selector means exactly what the raw one meant, so the
existing `content === null` / `nav !== null` skips still do all the work.

### Tests added or updated

All in
`tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence`,
a table-driven parametrize where a row is a node id. Nine rows added, none removed.

Scrub family (L4-1):

- `[no-return-between-entry-guard-and-scrub]` - no `return` between the entry guard's own
  `return data;` and `delete data.debugToolbar;`.
- `[entry-guard-return-is-the-only-one-before-the-scrub]` - exactly one `return` between
  `function update(data) {` and the scrub.

Best-effort per-panel family (L3-2):

- `[panel-key-escaped-for-selector]` - `const id = CSS.escape(panelId);` is present.
- `[panel-key-escape-is-single-sited]` - `CSS.escape(` occurs exactly once, so the key is escaped
  at its entry rather than at each use (the `is-record-helper-defined-once` shape).
- `[unusable-panel-key-skips-panel]` - `if (id === "") return;` is present.
- `[unusable-panel-key-skipped-before-any-lookup]` - the escape, then the skip, then
  `if (panel.title)`: the skip precedes the first use rather than merely existing.
- `[panel-key-escaped-before-content-lookup]` - the escape precedes
  ``const content = djDebug.querySelector(`#${id}`);``.
- `[panel-key-escaped-before-nav-lookup]` - the escape precedes
  ``djDebug.querySelector(`#djdt-${id}`)``. Both selector sites carry their own row, as the
  routing required.
- `[no-upstream-raw-panel-key-binding]` - `([id, panel])` is **absent**. That is upstream's own
  spelling (`Object.entries(data.debugToolbar.panels).map(([id, panel]) => {`), measured in
  `~/projects/strawberry-django-main/strawberry_django/templates/strawberry_django/debug_toolbar.html`
  before the row was written: one occurrence there, zero in the port. So a paste of upstream's
  loop restores it and fails this row - the absence half a presence check cannot supply, with a
  needle the borrow actually spells, which is the inert-needle failure pass 2 recorded and this
  row does not repeat.

### Validation run

- `uv run ruff format tests/middleware/test_debug_toolbar.py` - pass (`1 file left unchanged`).
- `uv run ruff check --fix tests/middleware/test_debug_toolbar.py` - pass (`All checks passed!`).
- `uv run python scripts/check_trailing_commas.py tests/middleware/test_debug_toolbar.py django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
  - pass (`Fixed 0 file(s).`). Explicit paths only; its default is a repo-wide auto-fix that
  would rewrite the concurrent session's files. `ruff format` re-run after it; no rewrite either
  way.
- `git status --short` after both ruff invocations - **76** paths, the same reading and the same
  set Worker 1 recorded at the end of its pass: this cycle's code/spec paths plus the untracked
  rationale and `042` artifacts, everything else the concurrent session's. Nothing outside
  `### Files touched` moved; nothing was reverted.
- `uv run pytest tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py -n0 --no-cov`
  - **86 passed**, exit 0, 0 collection errors. The cycle's standing scope, so it differences
  directly against the recorded baseline: 77 + 9 new rows = 86, and the nine new node ids are the
  nine listed above. No `--cov*` flag anywhere in this pass; no full sweep (not authorised, and
  this pass changes no model field set and no wire shape, so `### Test staleness a focused run
  cannot see` owes none).

### Failability proofs

Procedure, mechanized by `scripts/prove_failability.py`: the target is copied to a scratch path OUTSIDE the repo before any mutation; the mutation site is located by an exact anchor asserted to match exactly once (any other count aborts the entry without writing); the same focused scope is run unmutated first, so rows already failing before the mutation are differenced out of the count; both runs' pytest exit codes are read, because a run that collected nothing or blew up emits no `FAILED` lines and would otherwise be recorded as a measured zero; both runs use `--no-cov`; the file is restored from the pre-mutation copy in a `finally` and the restore is proved by `filecmp.cmp(shallow=False)` plus a SHA-256 comparison. One boundary at a time, restored before the next. `git` is never invoked - the tree is legitimately dirty, so an empty `git diff` is unachievable and forcing one would destroy the build's own work.

| # | Boundary | File mutated | Mutation applied | Rows failed | Errors | Scope as run | Restore proof |
|---|---|---|---|---|---|---|---|
| 1 | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"delete data.debugToolbar;" (the scrub is unconditional - early bail above the capture, inline)` | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html` | `const toolbar = data.debugToolbar;` -> `if (!djDebug) return data; const toolbar = data.debugToolbar;` - builder's description (unverified prose): an early bail on the toolbar handle hoisted ABOVE the capture, so a page whose toolbar DOM did not render returns with the server-only debugToolbar key intact - the weakening that leaves the index, adjacency, own-line and nesting rows all matching because nothing was wrapped around the scrub | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE -n0 tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py` | filecmp.cmp(shallow=False) True; sha256 92cd040294ad2dba... == 92cd040294ad2dba... (vs pre-mutation copy) |
| 2 | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"delete data.debugToolbar;" (the scrub is unconditional - early bail above the capture, braced)` | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html` | `const toolbar = data.debugToolbar;` -> `if (!djDebug) { return data; } const toolbar = data.debugToolbar;` - builder's description (unverified prose): the same weakening in its braced spelling: the hoisted bail's return sits on its own line inside a block, so no line-shape predicate over the scrub can see it | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE -n0 tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py` | filecmp.cmp(shallow=False) True; sha256 92cd040294ad2dba... == 92cd040294ad2dba... (vs pre-mutation copy) |
| 3 | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"delete data.debugToolbar;" (the scrub is unconditional - inline condition)` | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html` | `delete data.debugToolbar;` -> `if (isRecord(toolbar)) delete data.debugToolbar;` - builder's description (unverified prose): the unconditional scrub made conditional on the payload shape without moving it, so a malformed debugToolbar value leaks the server-only key back to GraphiQL while every index-ordering row still matches | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE -n0 tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py` | filecmp.cmp(shallow=False) True; sha256 92cd040294ad2dba... == 92cd040294ad2dba... (vs pre-mutation copy) |
| 4 | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"delete data.debugToolbar;" (the scrub is unconditional - block condition)` | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html` | `delete data.debugToolbar;` -> `if (isRecord(toolbar)) { delete data.debugToolbar; }` - builder's description (unverified prose): the same weakening in its braced spelling: the scrub nested inside a block of its own, which leaves its line untouched | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE -n0 tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py` | filecmp.cmp(shallow=False) True; sha256 92cd040294ad2dba... == 92cd040294ad2dba... (vs pre-mutation copy) |
| 5 | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"const id = CSS.escape(panelId);" (selector-safe panel key removed, upstream's raw binding restored)` | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html` | `Object.entries(toolbar.panels).forEach(([panelId, panel]) => { if (!isRecord(panel)) return; // A panel key is arbitr...` -> `Object.entries(toolbar.panels).forEach(([id, panel]) => { if (!isRecord(panel)) return;` - builder's description (unverified prose): the payload key bound straight to id and interpolated into both selectors unescaped - upstream's own spelling - so a debugToolbar key that is not a valid CSS identifier raises a SyntaxError out of the globally patched JSON.parse / Response.prototype.json instead of skipping that one panel | **7** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE -n0 tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py` | filecmp.cmp(shallow=False) True; sha256 92cd040294ad2dba... == 92cd040294ad2dba... (vs pre-mutation copy) |
| 6 | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"if (id === \"\") return;" (the one key CSS.escape cannot make nameable)` | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html` | `const id = CSS.escape(panelId); if (id === "") return;` -> `const id = CSS.escape(panelId);` - builder's description (unverified prose): the empty-escape skip removed while the escape stays, leaving the single key the escape cannot turn into an identifier - the empty one - to reach querySelector as a bare "#" and throw | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE -n0 tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py` | filecmp.cmp(shallow=False) True; sha256 92cd040294ad2dba... == 92cd040294ad2dba... (vs pre-mutation copy) |

Verdicts:

1. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"delete data.debugToolbar;" (the scrub is unconditional - early bail above the capture, inline)` - inside Worker 3's mandatory re-run floor (<= 3 rows)
2. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"delete data.debugToolbar;" (the scrub is unconditional - early bail above the capture, braced)` - inside Worker 3's mandatory re-run floor (<= 3 rows)
3. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"delete data.debugToolbar;" (the scrub is unconditional - inline condition)` - inside Worker 3's mandatory re-run floor (<= 3 rows)
4. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"delete data.debugToolbar;" (the scrub is unconditional - block condition)` - inside Worker 3's mandatory re-run floor (<= 3 rows)
5. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"const id = CSS.escape(panelId);" (selector-safe panel key removed, upstream's raw binding restored)` - pinned
6. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"if (id === \"\") return;" (the one key CSS.escape cannot make nameable)` - inside Worker 3's mandatory re-run floor (<= 3 rows)

Failing node ids, per boundary (the count above is `len()` of this list):

1. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"delete data.debugToolbar;" (the scrub is unconditional - early bail above the capture, inline)`
   - file mutated: `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
   - pytest summary: `======================== 2 failed, 84 passed in 14.19s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 86 passed in 14.22s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[no-return-between-entry-guard-and-scrub]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[entry-guard-return-is-the-only-one-before-the-scrub]`
2. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"delete data.debugToolbar;" (the scrub is unconditional - early bail above the capture, braced)`
   - file mutated: `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
   - pytest summary: `======================== 2 failed, 84 passed in 14.28s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 86 passed in 14.26s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[no-return-between-entry-guard-and-scrub]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[entry-guard-return-is-the-only-one-before-the-scrub]`
3. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"delete data.debugToolbar;" (the scrub is unconditional - inline condition)`
   - file mutated: `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
   - pytest summary: `======================== 2 failed, 84 passed in 14.21s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 86 passed in 14.25s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[scrub-immediately-follows-capture]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[scrub-is-its-own-statement]`
4. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"delete data.debugToolbar;" (the scrub is unconditional - block condition)`
   - file mutated: `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
   - pytest summary: `======================== 2 failed, 84 passed in 14.15s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 86 passed in 14.13s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[scrub-immediately-follows-capture]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[scrub-not-nested-inside-update]`
5. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"const id = CSS.escape(panelId);" (selector-safe panel key removed, upstream's raw binding restored)`
   - file mutated: `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
   - pytest summary: `======================== 7 failed, 79 passed in 14.13s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 86 passed in 14.12s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[panel-key-escaped-for-selector]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[panel-key-escape-is-single-sited]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[unusable-panel-key-skips-panel]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[unusable-panel-key-skipped-before-any-lookup]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[panel-key-escaped-before-content-lookup]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[panel-key-escaped-before-nav-lookup]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[no-upstream-raw-panel-key-binding]`
6. `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"if (id === \"\") return;" (the one key CSS.escape cannot make nameable)`
   - file mutated: `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
   - pytest summary: `======================== 2 failed, 84 passed in 14.18s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 86 passed in 14.14s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[unusable-panel-key-skips-panel]`
   - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[unusable-panel-key-skipped-before-any-lookup]`

A boundary whose removal fails 0 or 1 rows is **weakly pinned** and is `revision-needed` per `docs/builder/BUILD.md` - the fix is more or better-targeted rows, never a weaker boundary. A boundary at 3 rows or fewer is inside Worker 3's mandatory independent re-run floor. A proof carrying collection or setup errors, or whose pytest run exited anything but 0 or 1 (nothing collected, interrupted, internal error, usage error), is not a valid count at all - and a 0 from such a run is not a zero-row result: resolve it and re-run.

Every `<fill in ...>` above is a judgement no tool can make and MUST be replaced by hand before this subsection is submitted: weakly pinned and harness-impossible are the two possible readings of a zero-row result and they prescribe opposite responses (more rows, versus a production-call-site invariant assertion plus a recorded harness limitation), so a record that does not name one reads as self-contradictory.

Read against the acceptance rule: **no entry is weakly pinned** - the six read 2, 2, 2, 2, 7, 2,
so none is 0 or 1 - and **no entry is a zero-row result**, so no `why 0` judgement is owed by
this pass and none is written. Every entry carries 0 collection/setup errors, a pre-mutation
baseline of `86 passed` (exit 0) at the same scope, and a byte-compared restore; the run's exit
code was `0`. `docs/builder/temp-tests/042/` holds no `ACTIVE-MUTATION.json` and the asset's
digest after the run equals the digest recorded above, so no mutation is live and the tree handed
to Worker 3 is unmutated.

What the six entries are for, and how they difference against the prior records:

- **1 and 2 are the L4-1 boundary**, the class that had nothing pinning it: the early bail
  hoisted above the capture, inline and braced. Against the pass-2 table both fail **0 of 48**
  (Worker 1 re-measured that independently); against this table both fail **2 of 57**, and the
  two are the two new rows. That difference is the whole of L4-1.
- **3 and 4 are pass-2's entries 1 and 2 verbatim**, re-run here so the two wrapped-condition
  spellings are measured against the widened table rather than assumed unchanged. Both still
  fail 2, and the node-id sets are identical to pass 2's - the new rows do not absorb them, which
  is what keeps each weakening's failures inside its own family.
- **5 is the L3-2 boundary**: the escape removed and upstream's raw binding restored. Seven rows,
  the six presence/order rows plus the absence row. The four weakenings above and this one share
  no failing node id.
- **6 is 5's inseparable half measured alone**: the empty-escape skip removed while the escape
  stays. Two rows. Recorded because "the key reaches querySelector only through a form the parser
  always accepts" is one contract at one site and is proved as one boundary (`BUILD.md`
  `### Slice splitting`: boundaries one guard site and one contract make single are one unit) -
  the second entry exists to show the half that covers the single key the escape cannot help is
  itself pinned above the threshold, not to split the boundary in two.

### Hot-path budget

**The plan declares `none`, and this pass re-examined that rather than restating it**, because
unlike pass 2 it does change executable production JavaScript. The judgement and the reason a
number cannot be produced here at all are recorded under
`### Notes for Worker 1 (spec reconciliation)` below, which is where `BUILD.md` `## Hot-path
budget` routes a builder that finds otherwise - it is not Worker 2's call. The Python side is
untouched (digest unmoved), so no per-request, per-resolver, per-row or per-connection Python
path moved.

### Floor verification

**Not applicable; plan declares floor-verification scope `none`.** No Django / Strawberry /
channels integration seam changed: one browser-side asset and one package-tier test file whose
new rows are text predicates over that asset on disk. Floor facts read from
`docs/builder/BUILD.md` `## Floor verification` this pass, never from memory: Django **5.2.16**
on Python **3.10** with strawberry-graphql **0.316.0**.

### Implementation notes

- **One escape at the key's entry, not one wrapper per selector.** The routing named both
  selector sites; escaping where the key enters the loop body covers both with a single call and
  leaves both selector expressions byte-identical to what they were. That matters beyond taste:
  ``djDebug.querySelector(`#djdt-${id}`)`` is the needle of the landed
  `nav-lookup-scoped-to-handle` row and ``djDebug.querySelector(`#${id}`)`` is upstream's own
  write. A per-site wrapper would have re-needled an existing row - the one thing the routing
  forbade, because Worker 3 verified every node id in three proof records still resolves.
- **`panelId` / `id`, and why the escaped value keeps the shorter name.** `id` is what both
  selector expressions interpolate, so it is the name that must stay; `panelId` names the raw
  payload key. Reading the loop top-down, the raw key is bound, escaped, and never used again -
  which is the property the `panel-key-escape-is-single-sited` row exists to hold.
- **`if (id === "") return;` is a closed answer, not an enumeration.** CSS.escape's
  serialization is defined for every code point and yields a valid identifier for every non-empty
  input; the empty input is the single case where it returns something `#` cannot complete. So
  the pair covers the whole domain, which is what `BUILD.md` `### Fail-open shapes` asks for and
  what an "is this id valid" spelling check could not give.
- **No new browser requirement.** `CSS.escape` ships in the same generation as the APIs the asset
  already depends on - `Element.prepend`, `Object.entries`, `ShadowRoot`, template literals - so
  the port's effective floor does not move. Stated here rather than guarded, because a
  `typeof CSS.escape === "function"` fallback to raw interpolation would be exactly the fail-open
  shape this family exists to avoid.
- **`_return_count_between` is total like its siblings**: a missing needle returns `False` rather
  than raising, so a row a dropped guard makes unanswerable fails under its own id instead of
  erroring out of the parametrized body.
- **Why two rows rather than Worker 1's one.** The routing said one answer-shaped row closes
  L4-1, and one row would have taken the class from 0 to 1 - still weakly pinned under
  `### Acceptance rule`, which the same routing message named as the bar. The second row is not a
  second spelling: it re-anchors the same count at the function opener, which is the one position
  from which a return inserted *above* the entry guard is visible. Recorded here rather than
  silently: a builder adding a row the plan did not name is drift, even when the acceptance rule
  compels it.
- **Needle overlap with `no-upstream-value-returning-panel-map` is deliberate.** That row's
  needle is `.map(([id, panel])` and the new one's is `([id, panel])`; the new one subsumes it
  textually, but they pin different divergences (a value-returning loop; a raw key binding) and a
  future edit can restore either without the other. Collapsing them would leave one divergence
  with no absence half.

### Notes for Worker 3

- The manifest is `docs/builder/temp-tests/042/proofs-cohort-c-pass3.json`, the emitted record
  `proofs-report-cohort-c-pass3.md` beside it. **All three prior manifests and all four prior
  reports are untouched**, as are `worker3_replay_probe.py`,
  `worker3_contract_table_probe.py`, `worker3_pass2_replay_probe.py` and
  `test_encoded_json_row_is_nondistinguishing.py`, so the four-way before/after is readable
  without `git`.
- Re-run at the **recorded scope** - `-n0 tests/middleware/test_debug_toolbar.py
  examples/fakeshop/test_query/test_debug_toolbar_api.py` - and difference node-id sets. The
  unmutated baseline is now **86**, was 77 before this pass, and the delta is exactly the nine
  new row ids.
- **Entries 3 and 4 are pass-2's entries 1 and 2 verbatim**, so their sets are directly
  differenceable against that record; entries 1, 2, 5 and 6 are new. The single mutation both
  records share beyond those is not re-run here - pass 2's scrub-deletion entry (8 rows) is
  unchanged by this pass's rows except that it would now also fail the two new scrub rows, which
  is worth measuring if you want the arithmetic closed.
- Your pass-2 probe scripts extract the table and its helpers by `ast`; they now need the helper
  name `_return_count_between` added to whatever they extract before they can replay this table.
  The probe is one instrument behind again, and that is the second time - it may be worth
  extracting the helper names rather than listing them.
- **What the rows prove is unchanged in kind.** Every row, the nine new ones included, is a text
  predicate over the asset file; nothing is parsed as JavaScript or executed. `CSS.escape`'s
  totality argument above is *reasoning about the JavaScript*, not something any row measures -
  the rows prove the call is there, single-sited and ahead of both lookups, and nothing about
  what it returns. Your `### What the 48 rows do and do not prove` applies verbatim to the wider
  table, and the JS-runtime question stays homed at close-out.

### Notes for Worker 1 (spec reconciliation)

1. **Hot-path: the declaration is `none` and I did not change it, but it now covers executable
   production JavaScript and the honest answer is "unmeasurable here", not "not hot".** The
   guard runs once per panel per patched-JSON call on a `DEBUG`-gated GraphiQL page: one
   `CSS.escape` call and one string comparison per panel, against a panel list the toolbar keeps
   in single digits, inside a function that already performs several `querySelector` calls per
   panel. By the `BUILD.md` `## Hot-path budget` definition ("per request, per resolver, per row,
   per connection, or per outbound message") the per-panel loop is row-shaped, so the
   declaration is at least arguable. What makes it undecidable rather than merely small is that
   **this repo has no instrument that can measure it**: the suite has no JS runtime, the asset is
   never executed by any test, and every number the hot-path section names (query count,
   wall-clock over an iteration count, added-`await` count) is a Python-side measurement. A
   builder cannot produce a reproducible before/after for a browser-side asset here, so recording
   it as `none` with no number and recording it as hot-path with no number are the same artifact.
   - **Where:** `docs/builder/build-042-debug_toolbar-0_0_14.md`, the hot-path declaration; and
     `## Risks and open questions` in the spec, where the JS-runtime gap already lives.
   - **Current wording:** the plan declares hot-path `none` for Cohort C with no qualifier.
   - **Recommended replacement:** keep `none`, and add the qualifier that makes it checkable -
     "`none`; the asset's per-panel DOM work is browser-side and this repo executes no
     JavaScript, so a hot-path number cannot be captured for it by any pass. Cost changes to the
     asset are reasoned about in the artifact and reach the maintainer that way." That ties the
     declaration to the close-out JS-runtime item instead of leaving a silent `none` behind a
     path that did change.
2. **Test 16's mandatory-scrub clause is landed, with one row more than it describes.** The
   clause names four things the rows must pin, the first being "that nothing returns between the
   entry guard and the scrub". Two rows landed for that first clause, not one, because one row
   would have left the class weakly pinned at exactly 1 failing row.
   - **Where:** `## Test plan`, Test 16, the mandatory-scrub parenthetical.
   - **Current wording:** "plus the rows that pin the scrub unconditional, which an index
     comparison cannot see: that nothing returns between the entry guard and the scrub, that
     nothing but whitespace separates the capture from it, that it stands alone on its own line,
     and that it is not nested inside a block of its own".
   - **Recommended replacement:** "... that nothing returns between the entry guard and the
     scrub - counted both from the entry guard's own return and from the function opener, so a
     bail inserted above that guard is visible too - that nothing but whitespace separates the
     capture from it, ...". No count, and it states why the answer is measured twice.
3. **The DoD's seven-divergence item and `## Borrowing posture`'s "seven spots" both still read
   true after L3-2**, verified in this pass against the landed asset rather than assumed: the
   panel key's guard sits inside the best-effort per-panel bullet, which is one of the seven.
   No edit recommended; recorded so the next reader does not re-derive it.
4. **The rationale's L3-2 change record predicts a spelling, and the landed one differs in one
   respect worth a line.** It records "the obvious spelling makes the lookup total so the
   existing `content === null` / `nav !== null` skips do the rest". That is true for every key
   but the empty one: the empty key's escape is the empty identifier, which cannot be completed
   into a selector at all, so the port skips it explicitly rather than letting the lookup answer
   `null`. The distinction is the difference between a total lookup and a total *answer*, and it
   is the one place the implementation is not simply "escape it".
   - **Where:** `docs/SPECS/appx/spec-042-debug_toolbar-0_0_14-rationale.md`,
     `### Borrowing posture - the template port`, the panel-key change record.
   - **Current wording:** "the obvious spelling makes the lookup total so the existing
     `content === null` / `nav !== null` skips do the rest, which is why this adds no new failure
     path".
   - **Recommended replacement:** "... the escape makes the selector parseable for every key but
     the empty one, whose escape names no identifier and is skipped outright, so the existing
     `content === null` / `nav !== null` skips do the rest and this adds no new failure path".
5. **Nothing else moved.** The five contract homes were re-read in this pass for the two landed
   items only; no other disagreement between spec and tree surfaced, and the spec was not opened
   for writing.
---

## Review (Worker 3, pass 3)

Fresh invocation, no memory of passes 1 and 2 beyond
`docs/builder/worker-memory/042-worker-3.md`. Under review: **Build report (Worker 2, pass 3)**
— the two items Worker 1's final verification routed back, **L4-1** (the scrub's
unconditionality) and **L3-2** (the selector-safe panel key). Everything earlier in this artifact
is read as evidence, not as settled fact.

Scope read before acting: `AGENTS.md`, `START.md`, `docs/builder/BUILD.md`,
`docs/builder/ARTIFACT.md`, `docs/builder/worker-3.md`, `docs/README.md`,
`examples/fakeshop/test_query/README.md`, `docs/SPECS/spec-042-debug_toolbar-0_0_14.md`
(`## Borrowing posture`, `## Edge cases and constraints`, `## Test plan` Test 16,
`## Definition of done`), `docs/SPECS/appx/spec-042-debug_toolbar-0_0_14-rationale.md`,
`docs/builder/build-042-debug_toolbar-0_0_14.md`, this artifact in order, and my own memory file.
No other worker's memory file was opened.

### Mutations recorded BEFORE they were made

`worker-3.md` requires the record to precede the mutation. Six transient mutations, one boundary
at a time, mechanized by `scripts/prove_failability.py` from a manifest of my own —
`docs/builder/temp-tests/042/proofs-worker3-pass3.json`, scratch root **outside** the repository,
emitted record `proofs-report-worker3-pass3.md`. Every prior manifest, report and probe script
under `docs/builder/temp-tests/042/` is left untouched. The six are Worker 2's six entries
re-applied verbatim at the scope it recorded:

1. `debug_toolbar.html #"delete data.debugToolbar;"` — `const toolbar = data.debugToolbar;`
   gains `if (!djDebug) return data;` **above** it (inline).
2. the same, braced (`if (!djDebug) {` / `return data;` / `}`).
3. `delete data.debugToolbar;` → `if (isRecord(toolbar)) delete data.debugToolbar;`.
4. the same, block-form.
5. `Object.entries(toolbar.panels).forEach(([panelId, panel]) => {` … `if (id === "") return;`
   → `Object.entries(toolbar.panels).forEach(([id, panel]) => { if (!isRecord(panel)) return;` —
   the escape, the empty-key skip and their comment removed, upstream's raw key binding restored.
6. `const id = CSS.escape(panelId);` / `if (id === "") return;` → the escape alone, the
   empty-escape skip removed.

Every entry is restored in the same pass and the restore is proved by
`filecmp.cmp(shallow=False)` plus a SHA-256 comparison against the pre-mutation copy. No source
edit outside this carve-out; `git stash` / `checkout` / `restore` were never invoked.

Two **supplementary** mutations beyond Worker 2's six, recorded here before they were made,
because both close arithmetic this pass left open rather than asserted:

7. `delete data.debugToolbar;` **deleted** — pass 2's scrub-deletion entry (8 rows then),
   re-run against the widened table. If any pre-existing scrub row had been silently re-needled,
   its set would not be pass 2's eight plus the two new ones.
8. `Object.entries(toolbar.panels).forEach(([panelId, panel]) => {` →
   `Object.entries(toolbar.panels).map(([panelId, panel]) => {` — pass 2's value-returning-`map`
   revert, re-spelled against the landed binding, to measure the deliberate needle overlap
   between `no-upstream-value-returning-panel-map` (`.map(([id, panel])`) and the new
   `no-upstream-raw-panel-key-binding` (`([id, panel])`): with `panelId` still bound, `.map` alone
   must fail the loop rows and **not** the new absence row.

### Failability proofs (Worker 3 independent re-run, pass 3)

Re-run at the scope Worker 2 recorded — `-n0 tests/middleware/test_debug_toolbar.py
examples/fakeshop/test_query/test_debug_toolbar_api.py` — and compared as **node-id sets**, not
totals. Record: `docs/builder/temp-tests/042/proofs-report-worker3-pass3.md`.

| # | Boundary | W2 rows | W3 rows | Node-id sets |
|---|---|---|---|---|
| 1 | early bail above the capture, inline | 2 | **2** | identical |
| 2 | early bail above the capture, braced | 2 | **2** | identical |
| 3 | conditional scrub, inline (pass 2's entry 1 verbatim) | 2 | **2** | identical, and identical to pass 2's record |
| 4 | conditional scrub, block (pass 2's entry 2 verbatim) | 2 | **2** | identical, and identical to pass 2's record |
| 5 | `CSS.escape` removed, upstream's raw binding restored | 7 | **7** | identical |
| 6 | the empty-escape skip removed alone | 2 | **2** | identical |

Every entry: pre-mutation baseline `86 passed` (exit 0) at the same scope, **0** collection/setup
errors, restore proved by `filecmp.cmp(shallow=False)` + SHA-256 against the pre-mutation copy.
After the run the asset reads `92cd040294ad2dba26158c652f92b9760cd35b64b91f848822a1fa093e17fa00`
— the digest Worker 2 recorded — the module reads `5c189885117946d2122c4dd03f9153ddfab4a13c4697d669557958387af4201b`,
and no `ACTIVE-MUTATION.json` exists under the scratch root or `docs/builder/temp-tests/042/`.
**No entry is 0 or 1 rows; nothing is weakly pinned; no entry is a zero-row result, so no `why 0`
is owed.** Six of six re-run: the floor (≤ 3 rows) required 1, 2, 3, 4 and 6; entry 5 was re-run
anyway because it is the only boundary L3-2 introduced and accepting it on the record would have
left the pass's headline change resting on prose.

**Two supplementary entries, beyond Worker 2's six** (recorded above before they were made;
record: `proofs-report-worker3-pass3-supplementary.md`):

- **The scrub deleted, re-measured against the 57-row table: 10 rows**, and the ten are pass 2's
  eight plus exactly `no-return-between-entry-guard-and-scrub` and
  `entry-guard-return-is-the-only-one-before-the-scrub`. This is the arithmetic Worker 2 left
  open, and it is the check that would have caught a pre-existing row silently removed or
  re-needled in the scrub family: any such edit shows up here as a missing or unexpected id, not
  as a count.
- **`forEach` → `.map` with the landed `panelId` binding kept: 1 row.** Nobody claimed this
  number; it is the finding at `### Low:` L5-2 below.

**Second instrument.** `docs/builder/temp-tests/042/worker3_pass3_return_span_probe.py` extracts
`_TEMPLATE_CONTRACT` and all eight predicate constructors from the test file by `ast` source
slice and evaluates every row against **in-memory** mutations of the asset text — no file
written, no pytest, no `git`. It reproduces all six manifest verdicts row for row, confirms
57 rows / 57 unique ids / 0 failing unmutated, and confirms the asset was byte-unchanged by the
probe. Two instruments, agreeing; a table extracted by `ast` and a table run by pytest are not
the same instrument measured twice.

#### The two-rows-not-one deviation: measured, and the second row is a real second anchor

The routing asked for "one answer-shaped row"; two landed. Worker 2's argument is that one row
takes the class from 0 failing rows to 1, which `### Acceptance rule` still rejects. That is
correct but it is an argument about arithmetic, not about whether the second row sees anything
the first cannot. Measured, with a mutation **no manifest carries** (probe `P1`):

```
bail inserted ABOVE the entry guard, returning something other than `data`
  -> `if (!djDebug) return null;` between `function update(data) {` and the entry guard
  -> fails EXACTLY ['entry-guard-return-is-the-only-one-before-the-scrub']
```

Row 1's span opens at the asset's **first** `return data;`. The inserted bail is not spelled
`return data;`, so the span still opens at the entry guard's own return and reads clean — row 1
passes. Row 2, anchored at the function opener, counts two returns where one is contracted and
fails. So the second row is a second anchor from a position the first cannot see past, not a
restatement; the deviation is justified on its own terms and not only on the acceptance rule.
Checked in the other direction too (probe `P2`): a bail above the entry guard spelled
`return data;` fails **both**, so neither row is redundant with the other.

#### Absence-needle inertness: every needle this pass added, counted in both artefacts

The recurring defect of this cohort is an absence row whose needle never occurs in what it guards
against. Counted with `str.count` over both whole files, not grepped for matching lines:

| Needle | upstream asset | port |
|---|---|---|
| `([id, panel])` (**new this pass**) | **1** | 0 |
| `.map(([id, panel])` | 1 | 0 |
| `update(origParse(text))` | 1 | 0 |
| `data.hasOwnProperty("debugToolbar")` | 1 | 0 |
| `` .getElementById(`djdt-${id}`) `` | 1 | 0 |
| `.querySelector("h3").textContent` | 1 | 0 |
| `data.debugToolbar.panels` | 1 | 0 |
| `data.debugToolbar.requestId` | 1 | 0 |

Upstream:
`~/projects/strawberry-django-main/strawberry_django/templates/strawberry_django/debug_toolbar.html`
(1,449 bytes, 46 lines). The new `no-upstream-raw-panel-key-binding` row is **not inert**: its
needle is a spelling the borrow actually carries, and a verbatim paste of upstream's loop restores
it. Every other absence row in the table clears the same bar; the pass-2 class is closed across
the whole table, not only for the row this pass added.

The presence and ordering needles this pass added need no such check — they are satisfied by the
shipped asset, so each is proved live by its own passing row — but each was also confirmed to be
falsifiable by a mutation that removes what it names (entries 5 and 6, plus probes `F1`, `F2`,
`F3`, `F6` below).

#### The evidence chain: no row removed, renamed, or re-needled

- Table: **57** rows, **57** unique ids, 0 duplicates (`ast` over the landed table).
- Every node id cited anywhere in this artifact's three prior proof records — **32 distinct ids**
  — resolves in the current table. Nothing was renamed out from under a closed record.
- Focused scope: **86** collected, was **77**; delta **+9**, and the nine are exactly the nine
  the build report names. 57 − 9 = 48, the pass-2 table.
- Entries 3 and 4 reproduce pass 2's node-id sets exactly, and the supplementary scrub-deletion
  entry returns pass 2's eight ids plus the two new ones. A re-needle in the scrub family would
  have shown as a set difference in one of those three.
- Both selector expressions are byte-identical: neither `` const content = djDebug.querySelector(`#${id}`); ``
  nor `` djDebug.querySelector(`#djdt-${id}`) `` appears as a changed line in
  `git diff HEAD -- …/debug_toolbar.html`, and `nav-lookup-scoped-to-handle` — whose needle is the
  second of those — still passes. Escaping at the key's entry rather than per use is what bought
  that, and it is the right call for exactly the reason Worker 2 gives.

#### `CSS.escape`: total over the answer, checked against CSSOM rather than accepted

`CSS.escape(ident)` returns the result of CSSOM's **serialize an identifier**. Walked branch by
branch against the shipped algorithm rather than against the build report's summary of it:
U+0000 becomes U+FFFD; U+0001–U+001F and U+007F become `\<hex> `; a leading digit, and a digit
second after a leading `-`, become `\<hex> `; a lone `-` becomes `\-`; code points ≥ U+0080, `-`,
`_`, and `[0-9A-Za-z]` pass through; **everything else is backslash-escaped**. Every branch
appends and **no branch throws** — the NULL case in current CSSOM replaces rather than raises.
So the output is a valid `<ident-token>` by construction for every non-empty input, and
`"#" + CSS.escape(k)` is a selector `querySelector` parses. **No non-empty input can still produce
a selector `querySelector` rejects**; the builder's totality claim holds as stated.

The empty string is the single non-total input — `""` escapes to `""`, and `"#"` alone is not a
selector — and it is exactly what `if (id === "") return;` refuses. The domain is closed by an
answer, not by an enumeration: escape covers every key but one, the skip covers that one. This is
the shape `BUILD.md` `### Fail-open shapes` asks for, and it is why the empty-key case must be a
**skip** rather than a `try`/`catch` or a validity spelling-check.

One clause in the build report is slightly overstated and worth stating exactly rather than
carrying forward: "the escape changes no lookup that resolves today". Meaning is preserved for
id lookup — `#\35 x` does name the element whose id is `5x` — but for a raw key containing a
CSS-significant character that nevertheless *parsed*, the escape changes the result: `"a.b"`
previously selected `#a.b` (the element with id `a` **and class `b`**) and now selects `#a\.b`
(the element with id `a.b`). That is the corrected semantics, not a regression, and no payload
this package produces can carry such a key —
`django_strawberry_framework/middleware/debug_toolbar.py` #"payload[\"debugToolbar\"][\"panels\"][panel.panel_id]"
keys `panels` by the panel's class-derived `panel_id`. Nothing shipped moves; the sentence is
just wider than the fact.

#### The new global dependency: judged, and the judgement is "no guard"

This is the one genuinely new risk the pass introduces, so it is recorded either way rather than
left implicit. `CSS.escape` is a browser API called inside the globally patched `JSON.parse` /
`Response.prototype.json`; if it were absent or shadowed the call would throw, one level up from
the class M3 and L3-2 exist to close. **Verdict: no guard, no fallback, and no capture.** Four
grounds, each checked rather than assumed:

1. **It cannot be absent on a page that runs the toolbar.** `CSS.escape` ships in Chrome 46,
   Firefox 31, Safari 10, Edge 79. The asset already requires `Object.entries`,
   `Element.prepend`, `ShadowRoot`, template literals and arrow functions; and the toolbar the
   asset exists to update requires more still — measured in the installed
   `django-debug-toolbar` **7.1.1**: `static/debug_toolbar/js/toolbar.js` uses `globalThis`
   (10 occurrences, Chrome 71 / Firefox 65 / Safari 12.1) and `static/debug_toolbar/js/utils.js`
   reads `root.shadowRoot`. Every one of those is **newer** than `CSS.escape`. A browser lacking
   it cannot render the DOM this function updates, so the port's effective floor does not move.
2. **Shadowing is the same exposure the asset already accepts for `document`.** `CSS` is read
   from the global scope at call time, exactly as `document.getElementById` and
   `document.createElement` already are. The IIFE's `(JSON, Response)` capture exists because
   those are the two globals the asset *patches* and it needs the originals — it is not
   shadow-protection, so adding a `CSS` parameter would introduce a new idiom rather than follow
   the existing one.
3. **The failure mode is a different risk class.** M3 and L3-2 are input-triggered: a hostile or
   unusual *payload* reaches a throw while every other payload is fine, which is what makes them
   latent. A missing or shadowed `CSS` breaks the first panel of the first update on every page,
   deterministically, in a `DEBUG`-gated developer tool. Latent-versus-immediate is the whole
   reason the first class earns a guard.
4. **The guard itself would be the fail-open shape.** A `typeof CSS !== "undefined" ?
   CSS.escape(panelId) : panelId` fallback converts "cannot determine whether the escape is
   available" into "let the raw key through", reopening precisely the hole L3-2 closes —
   `BUILD.md` `### Fail-open shapes`, applied to the guard rather than to the input. **Measured,
   not argued:** probe `F7` applies that exact shape and it fails **4** rows of the landed table
   (`panel-key-escaped-for-selector`, `unusable-panel-key-skipped-before-any-lookup`,
   `panel-key-escaped-before-content-lookup`, `panel-key-escaped-before-nav-lookup`). The table
   already forbids it. A fallback that *skipped* the panel instead would not be fail-open, but it
   guards an input the audited browser range cannot supply, which is the speculative-feature shape
   the spec's divergence ledger refuses. Worker 2's `### Implementation notes` reaches the same
   conclusion in one sentence; this is the evidence under it.

#### Fail-open shape hunt over what landed

Read for the catalogued shapes rather than inferred from the green run. The asset adds no clamp,
no `or` fallback, no `getattr`-style default, no bare `catch`, and no truthiness test standing in
for an absence test. `const id = CSS.escape(panelId); if (id === "") return;` is a total function
followed by an equality test on its single non-total output, and the false branch **exits** the
per-panel path rather than coercing into it. The guard is written against the answer ("can this
key name a node") and not against an enumeration of key spellings — which is the distinction
L4-1 was routed back for, arriving correctly on the asset side too.

Probed for weakenings that might slip through the new rows (in-memory, no writes):

| Probe | Weakening | Rows failed |
|---|---|---|
| `F1` | escape kept, raw key interpolated at the content lookup | 1 — `panel-key-escaped-before-content-lookup` |
| `F2` | escape kept, raw key interpolated at the nav lookup | 2 — incl. `nav-lookup-scoped-to-handle` |
| `F3` | the empty-key skip moved after the content lookup | 1 — `unusable-panel-key-skipped-before-any-lookup` |
| `F6` | `CSS.escape` replaced by an identity `String()` | 5 |
| `F7` | the guarded raw-interpolation fallback | 4 |
| `F4` | a `throw` above the capture instead of a `return` | **0** |

`F4` is the one gap and it is not a leak: `_return_count_between`'s docstring says the property is
"does every path reaching the span's start also reach its end", and a `throw` falsifies that
literally — but a `throw` raises out of the patched globals rather than **returning** the payload,
so the server-only key cannot reach GraphiQL by that route. Every path that can *return* a value
to the caller is a `return`, so counting returns in the span is **complete for the leak class
Revision 8 guards**, which is the property that matters. Recorded so the next reader does not
re-derive it, and so the docstring's wider phrasing is not mistaken for a wider guarantee.

### High:

None.

### Medium:

None.

### Low:

#### L5-1 — the routed rationale correction quotes a sentence the rationale does not contain

`docs/builder/bld-042-review-3-code_fix.md`, `## Build report (Worker 2, pass 3)` →
`### Notes for Worker 1 (spec reconciliation)` item 4.

The item routes a real distinction (a total *lookup* versus a total *answer*) to the right file
and the right section, then quotes as the rationale's **"Current wording"**:

> the obvious spelling makes the lookup total so the existing `content === null` /
> `nav !== null` skips do the rest, which is why this adds no new failure path

That string occurs **0 times** in
`docs/SPECS/appx/spec-042-debug_toolbar-0_0_14-rationale.md` and **3 times in this artifact** — it
is Worker 1's own framing sentence from `### L3-2 — the framing decided, before anyone words it`,
not the rationale's text. The custodian would search the rationale for it and find nothing. The
rationale's actual sentence, in `**Change record — the panel key reaches a selector…**`, is:

> the contract is stated as an answer — the key reaches `querySelector` only through a form the
> selector parser always accepts — so an unusable key resolves to nothing and the existing
> absent-node skip does the rest.

(measured: 1 occurrence of `resolves to nothing and the existing`). **Corrected here rather than
re-looped** — the target and a replacement are given under `### Notes for Worker 1` below, so
nothing is lost and the cohort does not reopen for a citation. Why it matters beyond tidiness: a
derived description published as a quotation is the defect class this cycle exists to close, and
it reached the routing note in the same pass that closed two instances of it in the code.

#### L5-2 — this pass narrowed `no-upstream-value-returning-panel-map`'s reach, and nothing says so

`tests/middleware/test_debug_toolbar.py` #"no-upstream-value-returning-panel-map".

Needle: `.map(([id, panel])`. Before this pass the port bound `([id, panel])`, so a revert of the
side-effect loop to upstream's value-returning `.map` matched it — pass 2 measured that mutation
at **3** rows, the absence half included. The rename to `panelId` moved the needle out of reach of
a *partial* revert. Measured, supplementary entry 2:

```
Object.entries(toolbar.panels).forEach(([panelId, panel]) => {
  -> Object.entries(toolbar.panels).map(([panelId, panel]) => {
  -> fails EXACTLY ['panel-loop-is-foreach']   (1 row, and it is a presence row)
```

So that divergence's silent-revert detector now fires only for a revert that also restores the raw
key binding. Test 16's own falsifier list names "a diverged form whose rows are all presence
checks", and for the partial-revert case this form is now one.

**Intentionally accepted, with the reason recorded, rather than re-looped.** Three grounds:
the row is **not inert** by the criterion Test 16 actually states — its needle occurs once in
upstream's asset (measured above), so it still detects the verbatim paste it was written to
detect; the divergence is still detected, by `panel-loop-is-foreach`; and no boundary this pass
introduced is weakly pinned (all six read 2, 2, 2, 2, 7, 2). Holding a third builder pass open for
it would be polish. Routed to Worker 1 for the deferred-work catalog with the fix already derived:
re-needle the row to `` `.panels).map(` `` — **1** occurrence in upstream's asset, **0** in the
port, and binding-agnostic, so a partial revert fails it. Note the trap that fix avoids:
`Object.entries(toolbar.panels).map(` is the obvious binding-agnostic needle and is **inert** —
upstream writes `Object.entries(data.debugToolbar.panels).map(`, so it occurs 0 times there.

#### L5-3 — the build plan's hot-path declaration rests on a warrant the maintainer's mid-cycle decision falsified

`docs/builder/build-042-debug_toolbar-0_0_14.md`, the hot-path declaration (Worker 0's file; not
in this cohort's write set).

It reads `**none.** … the reconciliation is documentation-side, and the code cohort is
review-only`. The second clause is no longer true: `## Maintainer decisions taken mid-cycle`
item 1 widened the fence by exactly one file — the shipped bridge asset — and Cohort C has since
landed executable production JavaScript in it across three passes. The declaration's **verdict**
may well still be right; its **stated reason** is falsified, and a reason is what a later reader
re-derives from.

Worker 2 routed the wording (item 1 of its notes) as a missing qualifier. It is more than that,
and the difference is the point: a qualifier appended to a false warrant leaves the false warrant.
Endorsed and sharpened under `### Notes for Worker 1` below. **Not grounds to hold the cohort** —
the file is Worker 0's, no worker in this cohort may edit it, and the verdict is separately
defensible (see the next paragraph).

**On the verdict itself, since the dispatch asks whether `none` is still honest.** Measured by
reading: the added per-panel cost is one `CSS.escape` call and one string comparison, inside a
loop body that already issues up to eight `querySelector` calls per panel, over a panel list the
toolbar keeps in single digits, on a `DEBUG`-gated GraphiQL page. `none` is defensible on
magnitude. What is **not** honest is a bare `none`, because no pass could have produced a number
even if the cost were large: this repo executes no JavaScript, the asset is never run by any test,
and every metric `BUILD.md` `## Hot-path budget` names is a Python-side measurement. Recording
`none` with no number and recording `hot-path` with no number produce the identical artifact, and
the obligation the section actually carries — that a cost never reaches the maintainer silently —
is discharged by saying that, not by picking one of two indistinguishable labels.

### Findings raised earlier and deliberately not re-raised

- **`_return_count_between` shares `_adjacent`'s comment-brittleness, over a wider span.** Pass 2's
  `### L4-2` closed exactly this class with a recorded reason (fails **closed**, loudly, under the
  row's own name). Measured here for the new predicate (probe `P4`): a comment carrying the word
  `return` inserted anywhere between `function update(data) {` and the scrub fails **both** new
  rows, because the helper counts the substring `return`, not the token. The span is wider than
  `_adjacent`'s and it already contains a six-line comment block, so the trip hazard is closer
  than L4-2's was — but the disposition is identical and re-raising a closed finding under a new
  name is not a new finding. Same one-line fix if it ever fires: strip `//` comment lines before
  counting, never delete the row.
- **`P5`: a correct refactor of the empty-key skip to `id.length === 0` fails 2 rows.** Every row
  in this table is a text predicate; spelling-sensitivity is the instrument, not a defect in it,
  and it fails closed. Not a finding.
- **The JS-runtime question.** Escalated and parked for the maintainer at close-out; not re-raised.
  See `### What the 57 rows do and do not prove` below for what this pass changes about it.

### DRY findings

- **`_return_count_between` — existence challenge raised and answered: it should exist.** Grounds
  to raise it: a new helper with two call sites, both landed in the same pass, which is the
  "helper extracted too early" shape. Against deletion: none of the seven established constructors
  can express it — `_present` / `_absent` / `_defined_once` are single-needle, `_ordered` compares
  indices, `_adjacent` tests a whitespace span, `_own_statement_line` reads one line,
  `_unnested_within` counts braces; **counting a token across a span is a question none of them
  asks**, which the measurements confirm (entries 1 and 2 fail only the return rows; entries 3 and
  4 fail only the adjacency / own-line / nesting rows — the two families share no failing node id,
  so neither subsumes the other). Inlining would mean a lambda inside the table, hiding the one
  thing a reader of this table needs to see, and it would lose the docstring that carries the
  "property of the answer, not of a spelling" reasoning. It follows the seven siblings' idiom
  exactly and is total like them (a missing needle returns `False` rather than raising — verified
  by reading the body, and exercised by the supplementary scrub-deletion entry, where the second
  needle is gone and both rows fail under their own ids instead of erroring).
- **Needle literals repeat, as the table intends.** `const id = CSS.escape(panelId);` now appears
  4× and `if (id === "") return;` 2× (`scripts/review_inspect.py` over the test file,
  `docs/shadow/tests__middleware__test_debug_toolbar.overview.md`, "Repeated string literals").
  This follows the pre-existing 5× / 3× pattern for the scrub line that both prior passes
  accepted, and the reason still holds and is stronger here: hoisting a needle into a shared
  constant would let **one** edit silently re-needle four rows at once, which is precisely the
  failure this cohort's evidence chain is built to detect. Not a finding. Pass 2's standing
  recommendation — collapse the two `delete data.debugToolbar` spellings to one constant if the
  file is reopened for other reasons — is unaffected by this pass and not re-raised against it.
- **No new row duplicates an existing row's question.** Checked by `ast` over the landed table:
  the nine new rows carry needles no other row uses, except the deliberate `([id, panel])` /
  `.map(([id, panel])` overlap Worker 2 documented. That overlap is where L5-2 lives — the
  documentation of it is right about the direction it checked and silent about the other.
- **The `isRecord` helper, the `CSS.escape` single-siting, and the escape-at-entry placement are
  the DRY-correct shapes.** One escape call covering two selector sites beats two wrappers on
  every axis here: fewer calls, both selector expressions left byte-identical, and no existing row
  re-needled.

### Static helper use

`uv run python scripts/review_inspect.py tests/middleware/test_debug_toolbar.py --output-dir
docs/shadow` — run, and its repeated-string-literal section is the evidence under the DRY finding
above. **Skipped with reason for the package `.py`:** the module is byte-unchanged this pass
(digest `5c189885…`, verified). **Not applicable to the asset:** it is an AST tool over Python and
cannot parse `.html` / JavaScript — which is also why no instrument in this repo can review the
executable half of this diff mechanically.

### Test staleness — swept independently, not from the diff's file list

`worker-3.md` requires this sweep be derived rather than read off the slice's enumeration.
Derived: the pass touches one `.html` asset and one package-tier test file; it adds, removes and
renames **no** model field, no column, no `fields=` / `exclude=` list and no wire shape, so
neither shape `BUILD.md` `### Test staleness a focused run cannot see` names is in play and no
full-tree sweep is owed. Confirmed by searching for stranded readers rather than assuming:
`debug_toolbar.html` is named in three places outside the asset — the test file's
`_template_text()`, the middleware's `render_to_string(...)`, and
`examples/fakeshop/apps/kanban/constants.py` (the generated tracked-path list) — and the **path**
is unchanged in all three; `panelId` and `CSS.escape` occur nowhere outside the two cohort files.
Citation sweep as postcondition (`START.md`, and `check_citations.py` cannot see `#"substring"`
forms): no `debug_toolbar.html #"…"` citation exists anywhere in `docs/`, `KANBAN.md`,
`CHANGELOG.md`, `README.md` or `TODAY.md` outside this cycle's own scratch, and no standing doc
quotes the old `([id, panel])` binding. The `### Dispatched findings checklist`'s M3 citation
#"Object.entries(toolbar.panels).forEach" still resolves in the landed asset.

### Dispatched findings checklist — walked

All five boxes (`M1`, `M2`, `M3`, `M4`, the stale docstring line) are `- [x]` and were audited
against the diff by Worker 1 at final verification. This pass ticks nothing and reopens nothing;
its two items, **L4-1** and **L3-2**, are routed Lows the spec amendments turned into gates, not
boxes in that list. Re-confirmed rather than assumed: the diff still carries each box's contract
(the four-row `Content-Encoding` family, the 57-row table where there was one node id, the
`isRecord` payload-shape guard at all four read sites, the governance row over the floor's gated
trio, and the module docstring's named divergences), and the module's digest is unmoved since
Worker 1 audited them.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` — **empty** (0 lines). `__all__` and
the re-export list are unchanged. This pass added one module-private test helper, nine table rows
and one asset guard, and no public symbol.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify `CHANGELOG.md`.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. The spec and the
rationale were **not opened for writing** by this pass — verified independently of the claim:
their mtimes (21:33:57 and 21:36:26) precede this pass's test file (21:51:49) and asset
(21:56:38), `seven` still occurs exactly 3 times in the spec (`## Borrowing posture`,
`## Test plan` Test 16, `## Definition of done`), and the `## Borrowing posture` divergence list
still enumerates exactly seven bullets with the panel-key clause sitting inside the existing
best-effort per-panel bullet — the framing Worker 1 decided, followed as written.

### What the 57 rows do and do not prove

Worker 3's `### What the 48 rows do and do not prove` applies verbatim to the widened table; the
nine new rows change its scope, not its kind. Stated plainly because this pass is the first to add
**executable production JavaScript** whose only tests are text-identity rows:

- **What they prove.** That the asset on disk contains `const id = CSS.escape(panelId);` exactly
  once; that it is followed by `if (id === "") return;` and that both precede `if (panel.title)`
  and both `querySelector` interpolations; that upstream's raw `([id, panel])` binding is absent;
  that no `return` sits between the entry guard and the scrub, counted from two anchors. A future
  edit that drops, reorders or reverts any of those fails named rows — measured, six boundaries,
  every set reproduced independently.
- **What they do not prove.** That `CSS.escape` behaves as the totality argument above says; that
  `querySelector` accepts what it returns; that the skip actually prevents a `DOMException`; that
  the loop runs at all. Nothing in this suite parses the asset as JavaScript or executes it, and
  this machine's only JS runtime (`node`) has no `CSS` global at all — so even an ad-hoc check is
  unavailable without a DOM implementation this repo does not depend on. The totality argument in
  this review is **reasoning against the CSSOM specification**, and it is the warrant for the
  guard's correctness; the rows are the warrant that the guard is still there.
- **And what the absence rows specifically detect** is a *paste of upstream's text*. A rewrite of
  the same hole in different words passes all of them. That was already routed to close-out; the
  only thing this pass changes is that the gap now sits under executable code rather than under a
  comment.

### What looks solid

- **The L4-1 fix pins the answer, and the measurement proves it is not a fourth spelling.** Neither
  row names a condition, a bail, or a handle; both count returns in a span. Against the pass-2
  table the early bail failed 0 of 48 in both spellings (independently re-derived here: the
  mutation fails exactly the two new rows out of 57, so all 48 pre-existing rows pass). Against
  this table it fails 2. That delta is the whole of L4-1 and it is measured, not asserted.
- **The L3-2 fix is placed where it costs nothing.** One escape at the key's entry covers both
  selector sites, leaves both selector expressions byte-identical, re-needles no landed row, and
  keeps the divergence ledger at seven because the clause lives inside a rule that already
  promises it. A per-site wrapper would have broken `nav-lookup-scoped-to-handle`'s needle — the
  one thing the routing forbade.
- **The build report's numbers are all re-derivable and all re-derived correctly here**: six
  node-id sets, the 77 → 86 baseline, 48 → 57 rows, the nine new ids, both source digests, the
  upstream needle count, 0 collection errors throughout, and every restore.
- **Worker 2 recorded its own deviation from the routing (two rows, not one) rather than letting
  it read as the plan.** That is the behaviour that makes a build report usable as evidence.
- **The manifests and reports of all three prior passes, and all four Worker 3 probe scripts, are
  preserved unmodified** — verified by listing the directory, not by trusting the claim. The
  four-way before/after is readable without `git`.

### Temp test verification

- `docs/builder/temp-tests/042/proofs-worker3-pass3.json` — my copy of Worker 2's six entries with
  a scratch root **outside** the repository; emitted record `proofs-report-worker3-pass3.md`.
- `docs/builder/temp-tests/042/proofs-worker3-pass3-supplementary.json` — the two supplementary
  entries; record `proofs-report-worker3-pass3-supplementary.md`.
- `docs/builder/temp-tests/042/worker3_pass3_return_span_probe.py` — the read-only `ast` +
  in-memory-mutation probe (second instrument; source of `P1`–`P5` and `F1`–`F7`).

Disposition: **all kept as this cycle's evidence, none promoted.** None catches a behaviour bug
requiring a permanent test — the one finding a probe produced (L5-2) is a finding about an
existing row's reach, and its fix is a re-needle, not a new test. Nothing under
`docs/builder/temp-tests/042/` that predates this pass was overwritten or deleted; the pass-2
probe scripts' inability to replay the widened table (Worker 2's note 3 to Worker 3) is why this
pass has its own probe rather than an edit to theirs.

### Notes for Worker 1 (spec reconciliation)

1. **Worker 2's routed item 4 is right about the substance and wrong about the target — use this
   citation instead.** The rationale sentence to amend is in
   `docs/SPECS/appx/spec-042-debug_toolbar-0_0_14-rationale.md`,
   `**Change record — the panel key reaches a selector, and that is the best-effort per-panel
   form, not an eighth.**`, its closing clause: *"so an unusable key resolves to nothing and the
   existing absent-node skip does the rest."* (1 occurrence of `resolves to nothing and the
   existing`). The wording Worker 2 quoted as the rationale's is this artifact's own
   `### L3-2 — the framing decided` text and occurs 0 times in the rationale. Suggested
   replacement, preserving the distinction Worker 2 identified: *"so the escape makes the selector
   parseable for every key but the empty one, whose escape names no identifier and is skipped
   outright, and the existing absent-node skip does the rest."* See `### Low:` L5-1.
2. **Worker 2's routed item 1 (hot-path wording) is endorsed and needs to go one step further.**
   The problem in `docs/builder/build-042-debug_toolbar-0_0_14.md` is not only a missing qualifier
   on `none` — the declaration's **stated warrant**, "the code cohort is review-only", was
   falsified by the maintainer's own mid-cycle fence widening (`## Maintainer decisions taken
   mid-cycle` item 1). A qualifier appended to a false warrant leaves the false warrant standing.
   Recommend the reason be replaced, not extended: the code cohort ships one file of executable
   browser-side JavaScript; `none` stands on magnitude (one `CSS.escape` call and one string
   comparison per panel, inside a loop already issuing up to eight `querySelector` calls per
   panel, single-digit panel counts, `DEBUG`-gated page); and no pass could produce a number
   regardless, because this repo executes no JavaScript. That last clause is the one that ties the
   declaration to the close-out JS-runtime item. Worker 0 owns the file. See `### Low:` L5-3.
3. **Deferred-work catalog item, with the fix already derived:** re-needle
   `tests/middleware/test_debug_toolbar.py` #"no-upstream-value-returning-panel-map" from
   `.map(([id, panel])` to `` `.panels).map(` `` (1 occurrence in upstream's asset, 0 in the port,
   binding-agnostic), so a `forEach` → `.map` revert that keeps the `panelId` binding fails the
   absence half instead of one presence row. Do **not** use
   `Object.entries(toolbar.panels).map(` — it occurs 0 times upstream and would be inert, which is
   the defect this cohort has now caught three times. Owner: whoever next opens
   `tests/middleware/test_debug_toolbar.py` — the concurrent session's own queued promotion of
   `::test_get_payload_panel_title_only_when_has_content` (noted at item 10 of Worker 1's final
   verification) is the obvious carrier. See `### Low:` L5-2.
4. **Test 16's mandatory-scrub clause reads true as landed; Worker 2's routed item 2 is optional
   polish, not a defect.** The clause says the rows pin "that nothing returns between the entry
   guard and the scrub"; two rows pin exactly that, and the spec names no count. The proposed
   rewording (naming both anchors) is an improvement because it records *why* the answer is
   measured twice, which probe `P1` above shows is load-bearing — but the spec is not currently
   false, so this is a custodian's call rather than a gate.
5. **Worker 2's routed item 3 is confirmed independently.** `seven` occurs exactly 3 times in the
   spec, the `## Borrowing posture` list still enumerates seven bullets, the panel-key clause sits
   inside the best-effort per-panel bullet, and `## Definition of done` is untouched.
6. **Nothing else moved.** No new disagreement between the spec, the rationale and the tree
   surfaced in this pass.

### Review outcome

`review-accepted`.

Both routed items landed and both are measured rather than argued. L4-1 closed the gap it was
routed for: the early bail above the capture failed 0 of 48 rows before and fails exactly the two
new rows now, and the second row is a genuine second anchor rather than a restatement — probe `P1`
shows a bail above the entry guard returning something other than `data` fails **only** the second
row. L3-2 landed at both selector sites through one escape at the key's entry, with the CSSOM
totality argument checked against the specification's own algorithm and holding, and the new
global dependency judged and recorded with the browser evidence under it. Six of six failability
entries independently re-run at the recorded scope with identical node-id sets, two supplementary
entries beyond them, a second instrument agreeing row for row, every prior node id still
resolving, and no mutation left live.

Three **Low** findings, each with its disposition recorded: L5-1 corrected in place (the correct
rationale citation and replacement are in `### Notes for Worker 1` above, so nothing is stranded);
L5-2 intentionally accepted with its reason and routed with a derived fix; L5-3 routed to the file's
owner. No High and no Medium. Per `BUILD.md` `### Spawn-per-cycle dispatch` step 4 the loop closes:
no unresolved finding remains, and the cohort does not reopen for polish after three builder passes.

**The evidence that would have caught a defect had one been there**, stated so the acceptance is
checkable rather than asserted: the supplementary scrub-deletion re-run returned pass 2's eight
ids **plus** the two new ones — a removed or re-needled pre-existing row would have shown there as
a set difference, and it is the only check in this pass that could have; counting `([id, panel])`
in upstream's asset (1) and the port (0) is what would have caught a fourth inert absence needle,
the defect two prior passes each found; probe `F7` fails 4 rows on the guarded-fallback shape, so
had Worker 2 written the `typeof CSS` fallback the table would have rejected it; probe `P1` is
what would have shown the second scrub row to be a restatement had it been one; and the `ast`
probe reproducing all six verdicts without pytest is what would have caught the manifest and the
table being one instrument measured twice. Each of those ran and each came back clean; the one
that came back dirty — the `.map`-with-`panelId` revert at 1 row — is L5-2, and it is a finding
nobody claimed rather than a claim I accepted.

---

## Final verification (Worker 1, pass 2)

Ran against the tree, not against the reports. Every figure below was re-derived in this pass;
where a prior pass's figure is quoted it is named as a quotation and differenced against my own
reading. This is the third named citation in this cycle to have named the wrong site, so no
routed citation was applied before being re-derived.

### The three routed Lows

#### L5-1 — the routed rationale correction quoted a sentence that is not in the rationale

**Re-derived before applying, not after.** Counted as occurrences over whole files (`str.count`,
normalized for line wrapping), never as matching lines:

| String | rationale | this artifact | spec |
|---|---|---|---|
| `the obvious spelling makes the lookup total` | **0** | 4 | 0 |
| `resolves to nothing and the existing` | **1** | 4 | 0 |

So the review's correction holds in both halves: the wording Worker 2 published as the
rationale's "Current wording" is this artifact's own `### L3-2 — the framing decided` text and
occurs nowhere in the file it names, and the sentence actually in the rationale is the one the
review cites. The corrected target is
`docs/SPECS/appx/spec-042-debug_toolbar-0_0_14-rationale.md`, `### Borrowing posture — the
template port`, the panel-key change record's closing clause.

**Applied, and the substance re-derived independently of both routings.** The distinction Worker 2
found is real and is a property of the landed code, not of anyone's prose: `CSS.escape` is defined
for every code point and returns a valid identifier for every **non-empty** input, and its single
non-total case is the empty string, whose escape is the empty identifier — a `#` with nothing
after it, which is not a selector at all rather than a selector that matches nothing. The asset
therefore does not make the *lookup* total; it makes the *answer* total, by escaping every key and
skipping the one key the escape cannot help
(`django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
#"if (id === \"\") return;"). Rationale edit 1 below.

#### L5-2 — `no-upstream-value-returning-panel-map`'s reach, narrowed by the `panelId` rename

**Closes as a recorded Low. It does not re-loop.** Measured myself first, with my own replay of
the landed `_TEMPLATE_CONTRACT` (extracted by `ast` source slice from the test file and evaluated
against in-memory mutations of the asset text — no file written, no pytest, no `git`; the asset
was byte-compared unchanged afterwards). Unmutated: **0 of 57** rows fail, 57 rows / 57 unique ids.

| Mutation | Rows | Ids |
|---|---|---|
| `forEach` → `.map`, landed `panelId` binding kept | **1** | `panel-loop-is-foreach` |
| `forEach` → `.map` **and** the binding reverted (upstream's verbatim loop head) | **3** | `panel-loop-is-foreach`, `no-upstream-value-returning-panel-map`, `no-upstream-raw-panel-key-binding` |

The review's figure reproduces exactly. Why it closes rather than re-loops, graded against the
contract rather than against how it feels:

- **Nothing the spec claims is falsified.** `## Test plan` Test 16 states the falsifier as *an
  absence row whose needle upstream does not actually carry*. Re-measured over both whole files:
  `.map(([id, panel])` occurs **1×** in
  `~/projects/strawberry-django-main/strawberry_django/templates/strawberry_django/debug_toolbar.html`
  and **0×** in the port. The row is not inert, and the failure mode Test 16 names — a paste of
  upstream's text — still fails it, at 3 rows. What narrowed is the row's reach over a *hand edit*
  that reverts half the form, which no home ever promised.
- **Nothing is weakly pinned.** The best-effort per-panel form is at 2 presence rows plus 2
  absence rows; the boundary this cycle introduced there measures 7 (below).
- **The remedy is a needle change in a test file, and Worker 1 writes no tests.** Re-looping a
  fourth builder pass to re-needle one row, after three passes and with no contract falsified, is
  the polish `### Spawn-per-cycle dispatch` step 4 closes the loop against.

**The derived fix, re-measured rather than trusted, before it goes in the catalog.** Applying
`_absent("`.panels).map(`")` to that row in my replay: unmutated still 0 rows; the partial revert
fails **2** — `panel-loop-is-foreach` and `no-upstream-value-returning-panel-map`. Its needle
occurs **1×** upstream and **0×** in the port. And the trap the review flags is real and measured
here: `Object.entries(toolbar.panels).map(` occurs **0×** upstream (upstream writes
`Object.entries(data.debugToolbar.panels).map(`), so the obvious binding-agnostic needle would be
inert — the third time this cycle has met that shape. Catalogued with both halves.

#### L5-3 — the build plan's hot-path warrant

Confirmed as fixed, read in Worker 0's file rather than taken from the routing.
`docs/builder/build-042-debug_toolbar-0_0_14.md` now reads `**none** — verdict unchanged,
**warrant rewritten**`, names the falsified reason ("the code cohort is review-only") as
falsified by the maintainer's own fence widening, and replaces it: the Python change is
docstring- and comment-only under an AST-identity proof, the executable change is browser-side
JavaScript, `none` means *below the threshold that owes a number* on magnitude and the dev-only
gate, and no instrument in this repository could produce a number for a browser asset either way.
The reason is replaced, not extended, which is what the finding asked for. No further action; the
file is not in this cohort's write set and nothing about it is owed here.

### Re-audit of the spec against what actually landed

The amendments for L4-1 and L3-2 were written **before** the builder implemented them, and both
implementations differ in shape from what the clauses predicted. This is the pass that checks the
clauses against the tree. Walked home by home, against the landed diff:

| Home | Reading |
|---|---|
| Decision (`## Borrowing posture`, Decisions 5 / 6) | Seven diverged forms enumerated and seven present in the asset; the panel-key clause sits inside the best-effort per-panel bullet, so the ledger did not grow. **One disagreement found and fixed** (spec edit 2): the bullet described the guard as making the *lookup* total, which is not what landed. Decisions 5 and 6 are untouched by both items and still agree with the module (digest unmoved). |
| `## Slice checklist` | The Slice-1 template box carries "the documented guard divergences" with no count; the dependency box names the gated trio and the sweep. Neither is touched by L4-1 or L3-2 and neither is stale. |
| `## Edge cases and constraints` | "A `debugToolbar` value the bridge cannot read" already states the panel-key half as an **answer** ("a key that cannot name a DOM node skips that one panel"), which is true of both branches of what landed. No edit. |
| `## Test plan` | Test 13a and Test 12a unchanged and still matched by their rows. Test 16's mandatory-scrub clause reads true as landed but named one anchor where two rows landed — amended (spec edit 3). Test 16's per-kind claim carried a real defect — below. |
| `## Definition of done` | "the seven documented guard divergences" still true (checked below). The test item was **false** — below. |

**The disagreement worth the pass.** `## Definition of done` claimed "each diverged form carrying
both the row that pins the port's spelling and the row that pins upstream's replaced spelling
absent." Counted by `ast` over the landed table: **8 absence rows covering 6 of the 7 diverged
forms.** The mandatory-scrub form carries none and cannot — upstream spells the identical
statement `delete data.debugToolbar;`, just after the DOM work
(`~/projects/strawberry-django-main/strawberry_django/templates/strawberry_django/debug_toolbar.html`,
read in full this pass), so that form diverges by **position** and there is no replaced spelling to
assert absent. `## Test plan` Test 16 already carried the positional carve-out and the test file's
own block comment names the scrub as that case explicitly; the DoD did not, so one of five homes
stated the opposite of the other two. Fixed in both directions (spec edits 4 and 5): the DoD gains
the kind split, and Test 16's leading sentence is narrowed from "A **diverged** form" to "A form
that diverges **by spelling**" so its next sentence reads as the carve-out it is rather than as a
parallel claim.

**`## Borrowing posture`'s "seven" and the Definition of done, confirmed specifically**, because
the framing was mine and this is where it gets checked against the code that landed:

- `## Borrowing posture` opens "diverges from the borrow in seven spots" and the list under it
  carries exactly **7** top-level bullets (counted mechanically over the section's line range).
- `seven` occurs exactly **3** times in the spec — `## Borrowing posture`, Test 16, the DoD — the
  same three as before this pass.
- The panel-key clause is **inside** the best-effort per-panel bullet, not a bullet of its own,
  and the asset matches that framing: one guard, at the key's entry, serving both selector sites,
  under the rule that already promises a panel whose node is absent cannot throw.
- The DoD's "the seven documented guard divergences" therefore still reads true and was not moved.

### Failability and fail-open confirmations

**Re-measured, not read.** My own replay of the landed table over in-memory mutations, at
57 rows / 57 unique ids / 0 failing unmutated:

| Weakening | Rows | Where they fall |
|---|---|---|
| early bail above the capture, inline | **2** | both new return-count rows |
| early bail above the capture, braced | **2** | both new return-count rows |
| bail above the **entry guard** returning something other than `data` | **1** | `entry-guard-return-is-the-only-one-before-the-scrub` only |
| conditional scrub, inline | **2** | adjacency + own-statement |
| conditional scrub, braced | **2** | adjacency + nesting |
| the empty-escape skip removed alone | **2** | both `unusable-panel-key-*` rows |
| `CSS.escape` removed, upstream's raw binding restored | **7** | the six presence/order rows + the absence row |
| the scrub deleted outright | **10** | pass 2's eight **plus** exactly the two new ones |

Every scrub weakening's failing set stays inside the scrub family; no entry is 0 or 1 rows, so
nothing Cohort C introduced is weakly pinned. The third row above is the one that settles Worker
2's disclosed deviation from my routing — I asked for one answer-shaped row and two landed, and
the second is a second **anchor**, not a second spelling: a bail above the entry guard that does
not spell `return data;` slides the first row's span down with it and reads clean, and only the
function-anchored row sees it. The routing's arithmetic argument (one row leaves the class at 1,
which `### Acceptance rule` rejects) was correct but was not what justified the second row; this
measurement is. The scrub-deletion re-run is the check that would have caught a pre-existing row
silently removed or re-needled, and it returns the earlier record's ids plus the two new ones.

**No fail-open shape landed.** Read the diff for the catalogued shapes rather than trusting the
green: no clamp, no `or` fallback, no `getattr`-style default, no bare `catch`, no truthiness test
standing in for an absence test. `const id = CSS.escape(panelId); if (id === "") return;` is a
total function followed by an equality test on its one non-total output, and the false branch
**exits** the per-panel path instead of coercing into it. The one shape worth naming as rejected
rather than absent is the guard on the guard — a `typeof CSS !== "undefined" ? CSS.escape(k) : k`
fallback would convert "cannot tell whether the escape is available" into "let the raw key
through", reopening the hole; it is recorded in the rationale (edit 2) so it is not proposed as an
improvement later. The Python module is byte-unchanged from the first build pass
(`5c189885117946d2…`), so the AST-identity record (docstrings stripped, `12387 == 12387`) is still
the live warrant that no Python behavior moved.

**The gap that is not a defect, stated so the green is not over-read.** Every one of the 57 rows
is a text predicate over the asset on disk. The totality argument above is reasoning against the
CSSOM identifier-serialization rules, not a measurement, and no test in this repository executes
the asset. That is now a live risk rather than an aside, because this cycle put executable
production JavaScript behind it — recorded as a `## Risks and open questions` bullet with the
close-out JS-runtime decision as its named owner (spec edit 6), rather than left in a per-cycle
artifact that closes with the cycle.

### Dispatched findings checklist — re-audited

All five boxes (`M1`, `M2`, `M3`, `M4`, the stale docstring line) remain `- [x]`. Re-checked
against `git diff HEAD --` on the three files rather than against any report: the four-row
`Content-Encoding` family with a positive control inside each row, the 57-row named table where
there was one node id, `isRecord` defined once and applied at all four read sites, the governance
row comparing the `pyproject.toml` row to the literal and the literal to the hint, and the module
docstring's three named divergences with no closed-world closer. None is over-ticked, none
under-ticked, nothing is left `- [ ]`, so no deferral reason is owed. L4-1 and L3-2 are not boxes
in that list; they were routed Lows that the spec amendments turned into gates, and both have now
landed.

### DRY check across this cohort and the prior passes

No new duplication. `_return_count_between` is the eighth predicate constructor and asks a
question none of the other seven can express — the measurements above are the evidence: the
return-count rows and the adjacency/own-line/nesting rows fail for **disjoint** weakenings, so
neither family subsumes the other. One escape at the key's entry rather than a wrapper per
selector is the DRY-correct placement and is also what left both selector expressions
byte-identical, so no landed row was silently re-needled. The repeated needle literals in the
table remain deliberate for the reason both prior passes recorded and which this pass's evidence
chain depends on: hoisting a needle into a shared constant would let one edit re-needle several
rows at once, which is exactly the drift the chain exists to detect.

### Slice-local checks

| Gate | Command | Result |
| --- | --- | --- |
| Spec glossary | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-042-debug_toolbar-0_0_14.md` | `OK: 24 terms - all have glossary entries and at least one spec link.` |
| Citations | `uv run python scripts/check_citations.py --check` | `OK: 992 citations resolve (823 in 441 .py files, 169 in KANBAN.md).` — reads `.py` + `KANBAN.md` only, so it says nothing about either file this pass wrote |
| Whitespace | `git diff --check` (whole tree) | exit 0 |
| Format | `uv run ruff format --check .` | `444 files already formatted` |
| Lint | `uv run ruff check .` | `All checks passed!` (never `--fix`) |
| Source layout | `uv run python scripts/check_trailing_commas.py --check` over the spec, the rationale, both `.py` files and the asset | exit 0 (explicit paths only — its default is a repo-wide auto-fix over the concurrent session's files) |
| Focused suite | `uv run pytest tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py -n0 --no-cov` | **86 passed**, exit 0, 0 collection errors. No `--cov*` flag anywhere in this pass; no full sweep |
| Rule-27 citations + link convention (own verifier, positive-controlled) | scratchpad script over both files | spec 73 defs / 73 used refs, 0 undefined, 0 orphan, 0 broken in-page anchors, 0 broken cross-file anchors, 0 `path:NN`, 0 wrapped `#"substring"` citations; rationale 26 / 26, 0 problems. The 2 package-relative `utils/imports.py::require_optional_module` citations are pre-existing at HEAD and catalogued |

**The verifier's first reading was wrong and the file was right**, recorded because the whole
point of a positive control is that it catches this: its first pass reported 39 "problems" in the
spec — every cross-file link definition carrying a `#fragment`, because it stat-ed the whole
`path#anchor` string as a filename, plus two "orphan" definitions whose `[text][ref]` link text
wraps across a source line, which its single-line regex could not see. Both are the instrument, not
the file: the same two refs wrap identically at HEAD. Fixed, re-run, and the control (an invented
reference plus an invented anchor appended to a scratch copy) reports both before the clean reading
was believed.

### Hot-path and floor declarations

**Hot-path: `none`**, and this is the declaration the cycle's own L5-3 was about, so it is stated
rather than restated: Cohort C ships one file of executable browser-side JavaScript, `none` rests
on magnitude and the dev-only gate, and no pass could have produced a number for a browser asset
in a repository that executes no JavaScript — recording `none` with no number and recording
`hot-path` with no number produce the identical artifact, so the obligation is discharged by
saying that, which Worker 0's rewritten warrant now does. The Python module is byte-unchanged, so
no per-request, per-resolver, per-row or per-connection Python path moved.

**Floor-verification scope: `none`.** No Django / Strawberry / channels integration seam changed:
one browser-side asset, one package-tier test file of text predicates over it, and two Markdown
files. Floor facts, copied from `docs/builder/BUILD.md` `## Floor verification` this pass and
never from memory: Django **5.2.16** on Python **3.10** with strawberry-graphql **0.316.0**.

### Concurrent-session baseline

A reading, not a constant: `git status --short` returns **76** paths at the end of this pass.
This cycle's are `django_strawberry_framework/middleware/debug_toolbar.py`,
`django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`,
`tests/middleware/test_debug_toolbar.py`, the spec, the untracked rationale, and the four
untracked `042` artifacts. Nothing else was read as build output, edited or reverted
(`AGENTS.md` rule 34). Compare against a fresh reading at the final gate, never against this
number.

### Deferred work catalog (assembled here for `docs/builder/bld-042-final.md`)

The next spec author's reading list, and the input the final gate copies into `bld-042-final.md`'s
`### Deferred work catalog`. Per `BUILD.md` `## Final test-run gate` each item carries **the
source artifact section**, **the spec line licensing the deferral** (or `none`), and **a one-line
description**; per `AGENTS.md` "Item routed forward w/o NAMED owner dies" each also carries a
named owner. Where the owner is a card that does not exist yet, that is said plainly — homing it
on the board needs a write set this cycle is fenced out of, and it is the maintainer's to place.

1. **The floor's ungated restatements, and the needle that cannot see them all.**
   *Source:* `## Review (Worker 3)` → `### Notes for Worker 1` item 5; `## Final verification
   (Worker 1)` item 1; re-measured this pass. *Spec licence:* `## Risks and open questions`, the
   "single-valued across its three gated sites, and restated elsewhere ungated" bullet.
   *Description:* `django-debug-toolbar>=7.0.0` is restated, correct today and gated by nothing,
   at `docs/GLOSSARY.md` (DB-backed: ORM edit plus regenerate, never a hand-edit),
   `docs/README.md`, `CHANGELOG.md` #"Soft-dependency feature floors", and the spec's own
   `docs/SPECS/appx/spec-042-debug_toolbar-0_0_14-terms.csv` soft-dependency row — and **the
   census instrument is part of the item**: the tight needle `django-debug-toolbar>=` finds 24
   occurrences across the tree and misses the changelog's, which writes a backtick between the
   name and the specifier; the loose needle finds 25. A floor bump owes both spellings.
   *Owner:* the card that next raises the `[dependency-groups].dev` specifier — it already owns
   the gated trio and is the only work that makes these sites wrong.
2. **`docs/GLOSSARY.md`'s Debug-toolbar middleware entry is a measured stale carrier, not a
   suspected one.** *Source:* `## Review (Worker 3)` → `### Notes for Worker 1` item 5(a);
   re-read this pass. *Spec licence:* none — the entry is outside the spec's contract surface.
   *Description:* its body says "Two deliberate robustness divergences from the verbatim upstream
   borrow" and enumerates only `process_view`'s `isinstance` guard and `_get_payload`'s bail —
   the exact closed-count claim the module docstring retired this cycle, now three behind the
   module's three — and it restates the floor besides. DB-backed and fenced out.
   *Owner:* needs a KANBAN card; recommended carrier is the Slice-2 glossary status flip the spec
   already defers to the joint cut, which is the next work that opens this entry.
3. **The DRF twin is the package's last false-population comment.** *Source:* `## Plan (Worker 1)`
   → `### Notes for Worker 1` item 1, re-confirmed by every later pass. *Spec licence:* none —
   different spec (spec-039). *Description:*
   `django_strawberry_framework/rest_framework/__init__.py` #"three-places-that-must-agree" and
   `tests/rest_framework/test_soft_dependency.py` #"three-places-that-must-agree" name three
   places for `djangorestframework>=3.17.0`, and — unlike Channels and Strawberry — no
   `tests/test_ci_governance.py` row gates the `pyproject.toml` side. Same defect class as M4.
   *Owner:* needs a card with that write set; single-spec scope keeps it out of this cycle.
4. **The `DEBUG_TOOLBAR_FLOOR` refinement, trigger fired.** *Source:* `## Plan (Worker 1)` →
   `### DRY analysis` item 3 (which named the trigger) and `### Notes for Worker 1` item 2.
   *Spec licence:* none — a refinement, not a deferred fix; M4's defect is closed in-file.
   *Description:* hoist the toolbar floor beside `CHANNELS_FLOOR` / `STRAWBERRY_FLOOR` in
   `django_strawberry_framework/utils/imports.py`, interpolate it into the hint, and gate it
   beside the two existing rows in `tests/test_ci_governance.py`. Its stated trigger — a third
   regex-over-`pyproject.toml` governance row — fired in this cycle's first build pass.
   *Owner:* the same card as item 3 (both need `utils/imports.py` + `tests/test_ci_governance.py`);
   catalogue it with this framing so it is not re-raised as a duplication finding against Cohort C.
5. **Re-needle `no-upstream-value-returning-panel-map`.** *Source:* `## Review (Worker 3, pass 3)`
   → `### Low:` L5-2 and `### Notes for Worker 1` item 3; re-measured this pass. *Spec licence:*
   `## Test plan` Test 16 — the row satisfies the falsifier Test 16 states, so this is an
   improvement rather than a defect, which is why it is catalogued rather than re-looped.
   *Description:* change the row's needle from `.map(([id, panel])` to `` `.panels).map(` `` so a
   `forEach` → `.map` revert that keeps the port's `panelId` binding fails the absence half
   instead of one presence row (measured: 1 row → 2). **Do not** use
   `Object.entries(toolbar.panels).map(` — 0 occurrences upstream, therefore inert, which is the
   trap this cycle has now met three times.
   *Owner:* whoever next opens `tests/middleware/test_debug_toolbar.py`; the concurrent session's
   own queued live-promotion of `::test_get_payload_panel_title_only_when_has_content` (item 10)
   is the obvious carrier.
6. **The JS-runtime question**, parked for the maintainer at close-out. *Source:* build plan
   `## Maintainer decisions taken mid-cycle` item 2; `### What the 57 rows do and do not prove`.
   *Spec licence:* `## Risks and open questions`, the "pinned by text, never by execution" bullet
   added this pass, which names this decision as the risk's owner. *Description:* the asset now
   carries executable guards whose correctness is established by reasoning against the language
   and the CSSOM rules and by no test; the absence rows detect a paste of upstream's text and
   nothing else, so a rewrite of the same hole in different words passes all of them. It is also
   the reason the hot-path declaration can carry no number.
   *Owner:* the maintainer, at close-out.
7. **Decision 1's "This spec lives at `docs/spec-…`" template sentence** plausibly sits in every
   archived spec under `docs/SPECS/`. *Source:* `## Final verification (Worker 1)` item 7.
   *Spec licence:* none. *Description:* the custody cohort corrected spec-042's copy and could not
   sweep the rest; the population is a grep away and the fix is mechanical.
   *Owner:* the next `docs/SPECS/NEXT.md` Step 8 archival sweep, which already rewrites every
   cross-reference in one pass and is the only work that opens every archived spec.
8. **Two package-relative citations in the spec.** *Source:* `## Plan (Worker 1)` →
   `### Notes for Worker 1` item 6(a); re-measured this pass by my own verifier. *Spec licence:*
   none. *Description:* `utils/imports.py::require_optional_module` appears twice with a
   package-relative path where `AGENTS.md` rule 27 wants the repo-relative form; present at HEAD
   before this cycle and unread by any gate (`check_citations.py` does not read `docs/`). Low, and
   deliberately not widened into a spec-wide citation sweep by this cycle.
   *Owner:* the same archival sweep as item 7.
9. **`## Implementation plan` opens "The file-level delta map for the Worker 0 build handoff".**
   *Source:* `## Final verification (Worker 1)` item 9. *Spec licence:* none.
   *Description:* pre-existing at HEAD; it names an audience rather than attributing a change, so
   it is **not** the process provenance `AGENTS.md` rule 27 bans. Catalogued so the next reader
   does not re-decide it, not as work.
   *Owner:* nobody — recorded as decided.
10. **The concurrent session has queued work in this cohort's test file.** *Source:*
    `## Review (Worker 3)` → `### Notes for Worker 1` item 7; `## Final verification (Worker 1)`
    item 10. *Spec licence:* none. *Description:* its (dirty, uncommitted)
    `examples/fakeshop/test_query/README.md` backlog names
    `tests/middleware/test_debug_toolbar.py::test_get_payload_panel_title_only_when_has_content`
    for live promotion and two `Content-Length` refresh rows for deletion afterwards. Nothing
    collides today; whoever executes that sweep meets a file that now carries a 57-row table and
    eight predicate helpers.
    *Owner:* the concurrent session's own live-promotion card.
11. **Worker 2's routed Test 16 rewording (build report pass 3, item 2) is discharged, not
    deferred** — recorded here so the final gate does not carry it forward as open. The clause was
    not false as landed; it named one anchor where two rows landed, and spec edit 3 below states
    both. *Owner:* none; closed in this pass.

### Spec changes made (Worker 1 only)

Every edit states the corrected contract directly: no amendment block, no round or cohort
provenance, no "previously". Census before writing, occurrences rather than lines, both files:
`seven` — spec 3, and 3 after this pass, the same three sites; `diverged form` as a phrase — spec
2 before; `resolves to nothing` — spec 1, rationale 1. Retirement after this pass: the spec's
description of the panel-key guard as making the *lookup* total → **0**; the DoD's unconditional
"each diverged form … upstream's replaced spelling absent" → **0**; no numeral was added anywhere.

Spec (`docs/SPECS/spec-042-debug_toolbar-0_0_14.md`):

1. **`Status:` line** — the post-cut extension clause gains "and skips a panel whose key cannot
   name a node rather than raising out of the patched globals". Reason: the line enumerates what
   the shipped contract gained after the cut and was one clause behind the tree. *Per-spawn status
   re-verification; L3-2's landed code.*
2. **`## Borrowing posture`, the best-effort per-panel bullet** — the clause "so a key that cannot
   name a node resolves to nothing and skips that one panel exactly as an absent node does" is
   replaced by the three cases the asset actually has: every key either names a node, resolves to
   nothing and is skipped as an absent node is, or — the one key that cannot be put into a form
   the parser accepts — is skipped before either lookup; and the sentence naming what is total,
   "the **answer** the loop needs, not the lookup itself". Reason: the spec described a mechanism
   the implementation does not have, and the difference is the whole of the empty-key case.
   *Five-homes re-audit; the builder's routed item 4.*
3. **`## Test plan` Test 16, the mandatory-scrub clause** — "that nothing returns between the
   entry guard and the scrub" gains "counted from the function opener as well as from that guard's
   own return so that a bail hoisted *above* the guard is visible too". Reason: my routing asked
   for one answer-shaped row and two landed; the second is a second anchor, measured this pass,
   and a test plan that names one anchor reads as though the second row were a restatement. No
   count. *L4-1 as landed.*
4. **`## Test plan` Test 16, the per-kind claim** — "A **diverged** form carries both halves" is
   narrowed to "A form that diverges **by spelling** carries both halves", and the next sentence
   is restated as the other case: a form that diverges **by position** — the borrow carries the
   same statement, elsewhere — has no replaced spelling to assert absent and is pinned by index,
   adjacency, nesting and return-count rows. The falsifier follows it ("a spelling-diverged form
   whose rows are all presence checks"). Reason: read universally the first sentence is false of
   the mandatory-scrub form, which is one of the seven. *Five-homes re-audit.*
5. **`## Definition of done`, the test item** — the same kind split, replacing "each diverged form
   carrying both the row that pins the port's spelling and the row that pins upstream's replaced
   spelling absent". Reason: this was the home that was actually **false** — measured by `ast`
   over the landed table, 8 absence rows cover 6 of the 7 diverged forms, and the seventh's
   divergence is positional. Test 16 and the test file's own comment both carried the carve-out;
   the DoD did not, so two homes said the opposite of a third. *Five-homes re-audit.*
6. **`## Risks and open questions`, a new bullet** — "The bridge asset's guards are pinned by
   text, never by execution": what Test 16's rows prove and do not, that the totality arguments
   are reasoning rather than measurement, that the absence rows detect only a paste of upstream's
   text, and that the JS-runtime decision is the risk's named owner. Reason: the section's opener
   says every constraint below is live, and this cycle put executable production JavaScript behind
   a text-only guard — a constraint that until now lived only in per-cycle artifacts that close
   with the cycle. *L3-2 as landed; the deferred-work catalog's item 6 needed a licence in the
   spec.*

Rationale (`docs/SPECS/appx/spec-042-debug_toolbar-0_0_14-rationale.md`):

7. **`### Borrowing posture — the template port`, the panel-key change record's closing clause** —
   "so an unusable key resolves to nothing and the existing absent-node skip does the rest" becomes
   "so the escape makes the selector parseable for every key but the empty one, whose escape names
   no identifier and is therefore skipped outright, and the existing absent-node skip does the
   rest", followed by a paragraph naming the distinction as a reusable one: the contract was
   written expecting a total **lookup** and what the domain admits is a total **answer**, and only
   the second is what `### Fail-open shapes` asks for. This is L5-1's substance, applied to the
   site L5-1 corrected. *L5-1, re-derived.*
8. **Same change record, two additions** — the landed placement (one escape where the key enters
   the loop body rather than a wrapper per selector, and why: both selector expressions stay
   byte-identical, so no row already in the table is silently re-needled), and a new **rejected**
   alternative, guarding the escape itself, with the three grounds it loses on — it cannot be
   absent on a page that runs the toolbar, its failure mode is deterministic rather than latent,
   and a `typeof` fallback to the raw key would be the fail-open shape this change closes. Reason:
   the asset calls a global the borrow does not, which is the obvious next finding, and the
   rationale is where a settled alternative goes so it is not re-fought.
9. **`### Borrowing posture — the template port`, the table's self-claim change record** — its
   per-kind summary is swept to match spec edits 4 and 5 (a form diverging by spelling carries
   both halves; a form diverging by position carries the positional rows, because the borrow
   spells the same statement and there is no replaced spelling to assert absent), with the
   mandatory scrub named as that case. `START.md` "Sweep both files of a pair": the same sentence
   lived in both files and correcting only the spec would leave the companion falsified.
10. **Same record, a third measured lesson** — a rename in the guarded file can narrow an absence
    needle's reach without making it inert, and the row still reads green: an absence needle is
    coupled to the port's own spelling wherever it quotes more of the line than the divergence
    itself, so a rename owes a re-count of every absence needle spanning it, and the narrower
    needle is the one that survives. Reason: it sits beside the two lessons already recorded
    there, it is the generalization of the catalog's item 5, and a lesson left only in a
    per-cycle artifact dies with the cycle. *L5-2.*

Byte counts: spec 159,492 → 161,287; rationale 62,946 → 67,234. This pass wrote no source and no
tests; all three code/test digests are unchanged from the build pass that set them.

### Final status

`final-accepted`.

Both contracts my prior pass routed back have landed and both are measured rather than argued, by
my own instrument and not by either report's: the early bail above the capture failed 0 of 48 rows
before and fails exactly the two new rows now, and the selector-safe panel key's boundary measures
7 with its inseparable half at 2. Nothing Cohort C introduced is weakly pinned, every weakening's
failing set stays inside its own family, the scrub-deletion re-run returns the earlier record's
ids plus exactly the two new ones, and no mutation is live.

The three routed Lows are discharged: L5-1 applied to the site it actually names, after the
citation was re-derived rather than trusted; L5-2 closed as a recorded Low with its measurement
and its derived fix — including the inert alternative that fix must avoid — carried into the
catalog under a named owner; L5-3 confirmed fixed in Worker 0's file, with the false warrant
replaced rather than qualified.

The re-audit earned its place. Two of the five homes disagreed with the tree and one disagreed
with two other homes: `## Borrowing posture` described the panel-key guard as making the lookup
total when what landed makes the answer total, and the `## Definition of done` claimed every
diverged form carries an absence row when the mandatory scrub's divergence is positional and
cannot. Both are fixed, in both files of the pair, and `## Borrowing posture`'s "seven" and the
DoD's seven-divergence item are confirmed against the landed asset rather than assumed: seven
bullets, three occurrences, and the panel-key clause inside the best-effort per-panel bullet where
the framing put it.

### Summary

Cohort C closes with the bridge asset hardened against both the payload it cannot read and the
panel key it cannot turn into a selector, the scrub's unconditionality pinned by the answer rather
than by three spellings of the weakening, and a 57-row named contract table where the port once
had one node id. The spec and the rationale now describe what landed rather than what was
predicted — including the one place the implementation is not simply "escape it" — and the five
contract homes agree with each other and with the tree. The cycle's deferred work is catalogued
with a source, a licence and a named owner for each item, ready for `docs/builder/bld-042-final.md`.

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
