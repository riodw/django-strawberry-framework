# Build: Slice 4 — Duplicated docstring fragment deletion

Spec reference: `docs/SPECS/spec-024-django_trac_37064_hardening-0_0_7.md`; companion
`docs/SPECS/appx/spec-024-django_trac_37064_hardening-0_0_7-rationale.md`.
Authorising clause: `docs/builder/bld-final-024.md` `## Deferred work catalog` item 6 — "A
pre-existing duplicated docstring fragment in a writable file… *Deferral licensed by:* nothing — it
is in scope for this cycle's `.py` surface… The fix is a one-line deletion and it needs an owner:
whichever pass next owns that docstring." This slice is that owner.
Status: final-accepted

## Plan (Worker 2, written in lieu of a Worker 1 planning pass)

The build plan's `## Dispatch deviations (deliberate, recorded)` carries exactly two bullets and
**both name Slice 1** ("Slice 1 skips its Worker 1 planning pass", "Slice 1 runs read-only"); no
deviation is recorded there for Slice 3 or for this slice. (Corrected on pass 2 — the pass-1 wording
claimed the plan licensed a Slice 3 skip, which it does not.) What licenses the shape here is the
**dispatch instruction for this slice**, and the precedent is the sibling artifact
`bld-slice-3-024-rename_rot_sweep.md:10`, whose plan is likewise builder-authored — it derives its own
licence from Slice 1's recorded deviation as "the repair cohort it licenses inherits that shape".
The plan section below is therefore authored by the builder before the build, and Worker 3 reviews it
alongside the diff.

The build plan **does** carry this slice: `## Slice 4 dispatch (post-gate, maintainer-directed)`
(line 288), the artifact at line 118 of its artifact list, and two checklist rows at lines 323-326.
That section is the maintainer-directed authority for enacting `bld-final-024.md` catalog item 6 and
states the shape explicitly — "a full Worker 2 / Worker 3 slice under the standing isolation rule,
not a Worker 1 touch-up" — and that it re-opens the final gate.

### The defect

`django_strawberry_framework/_strawberry_patches.py`, module docstring, under the heading
`Three lifecycles, and one that left` (cited symbol-qualified as
`django_strawberry_framework/_strawberry_patches.py #"Three lifecycles, and one that left"`).

At HEAD the heading is followed by its underline, a blank line, and then:

```
independent upstream *bugs* that do not retire together:
Read the retirement question per concern, because this module carries three
independent upstream *bugs* that do not retire together:
```

The first line is an orphaned copy of the second line of the complete sentence that immediately
follows it — a copy-paste artifact, not rename rot. A reader hits a dangling subordinate clause with
no subject before reaching the real sentence.

Severity: **Low** by `docs/builder/BUILD.md` `## Severity definitions` — "comments or docstrings
stale or wrong but not load-bearing". Nothing executable reads the docstring.

**Provenance — population named, instrument shown.** (Corrected on pass 2; the pass-1 wording
"recorded three times before this slice, each time as out of the recording pass's contract" was a
stated count asserted with no instrument, and it does not reproduce. See
`## Build report (Worker 2, pass 2)` for what was wrong and why.)

*Population:* passages that record this fragment, in the tracked per-cycle artifacts under
`docs/builder/`, written **before** this slice. Corpus deliberately excludes this artifact itself and
excludes `docs/builder/worker-memory/` — those files are gitignored per-worker scratch and
`worker-2.md` `## Required reading` forbids reading another worker's. It further excludes
`build-024-django_trac_37064_hardening-0_0_7.md` `## Slice 4 dispatch (post-gate,
maintainer-directed)`, which the glob does reach and whose spellings (`.py` docstring defect,
`Orphaned-docstring-fragment`) the vocabulary below cannot match: that passage **authorises** this
slice rather than recording the fragment — it states no duplication, clause, or text — and it
constitutes the "written before this slice" boundary rather than sitting inside it. The exclusion is
therefore a decision about what the population is, not a by-product of the vocabulary.

*Instrument:* match every line in that corpus against the vocabulary
`Three lifecycles | independent upstream | duplicated docstring | docstring fragment | duplicated,
truncated | dangling (truncated )?(clause|fragment) | copy-paste artifact`, then resolve each hit to
its owning `##` / `###` heading by carrying a heading stack down the file, and collapse hits sharing
a heading and sitting within 8 lines of one another into one passage. Run as a Python one-shot over
`pathlib.Path('docs/builder').glob('*.md')`; matching **lines** and distinct **passages** are
reported separately because they are different quantities.

*Measurement:* **21 matching lines, resolving to 8 distinct passages across 3 artifacts and 3 worker
roles.**

| # | Passage | Recorded there as |
|---|---|---|
| 1 | `bld-slice-3-024-rename_rot_sweep.md:362-368` — `## Build report (Worker 2)` -> `### Notes for Worker 1 (spec reconciliation)`, the **unnumbered** bolded paragraph `#"One defect found in the writable file that is deliberately NOT repaired here"` | Worker 2 declines it as unrelated cleanup |
| 2 | `bld-slice-3-024:658-661` — `## Review (Worker 3)` -> `### What looks solid` | Worker 3 confirms it at HEAD and **endorses** the decline |
| 3 | `bld-slice-3-024:703-704` — `## Review (Worker 3)` -> `### Notes for Worker 1 (spec reconciliation)` **item 4** | Worker 3 routes it for an owner |
| 4 | `bld-slice-3-024:761-763` — `## Final verification (Worker 1)` | Worker 1 upholds the decline |
| 5 | `bld-slice-2-024-spec_reconciliation.md:165` — `## Build report (Worker 1, acting as author …)` -> `### Notes for Worker 1` | Worker 1 declines it as outside a Markdown-only contract |
| 6 | `bld-slice-2-024:232` — same report -> `### Deferred work catalog` **item 6** | Worker 1 declines and routes it |
| 7 | `bld-slice-2-024:445-446` — `## Review (Worker 3)` -> `### Counts and claims re-derived independently` | Worker 3 reproduces it at HEAD |
| 8 | `bld-final-024.md:240-248` — `## Deferred work catalog` **item 6** | routed for an owner; the clause authorising this slice |

Under the narrower reading "recorded as **out of the recording pass's contract**", i.e. passages that
actually *decline* it, the population is sites 1, 4, 5 and 6 — **4**. Site 2 endorses a decline rather
than making one, sites 3 and 8 route rather than decline, and site 7 is a re-derivation. Neither
reading yields three. The two sources `bld-final-024.md` item 6 names are sites 3 and 6; pass 1 quoted
that item as its authorising clause, carried site 3 forward, and dropped site 6.

Note on the citation itself: `bld-slice-3-024-rename_rot_sweep.md` carries **two** `### Notes for
Worker 1` sections, Worker 2's and Worker 3's, and only Worker 3's is numbered. So "item 4" is
**Worker 3's** passage (site 3); Worker 2's record is the unnumbered paragraph at site 1, cited above
by content rather than by a number that belongs to the other section. `bld-final-024.md` item 6 makes
the same conflation; it is `final-accepted` and was not edited.

### The change

Delete the orphaned standalone occurrence. One line removed, nothing else. No reflow, no reword, no
re-wrap of any surviving line, no other file.

Resulting text: heading, underline, blank line, the complete two-line sentence, blank line, the
numbered list that already followed.

### DRY analysis

- No logic is added, moved, shared, or deleted. The change is one line of docstring prose.
- No duplication is introduced. The change **removes** a duplication — which is the whole slice.
- No helper is justified and none is created.

### Implementation steps

1. Re-derive the defect independently of the dispatch: measure **occurrences**, not matching lines,
   at both HEAD and the working tree; confirm 2 at each.
2. Confirm the orphan is pre-existing, using the read-only HEAD reference
   (`git show HEAD:<path>` into a scratch path outside the repo) — never `git stash` / `git checkout`
   / `git restore` / `git worktree`.
3. Delete the orphaned line only, anchoring the edit on a three-line span so no other occurrence can
   be matched.
4. Re-measure: 1 occurrence, and confirm the survivor is the in-sentence one by reading its context,
   not by trusting the count.
5. Confirm `git diff HEAD -- <path>` shows exactly two hunks — this cycle's citation repair and this
   deletion — so the concurrent slice-3 change survived untouched.
6. Run the gates and record each verbatim with its exit code.

### Test additions / updates

None, and none are owed. The slice changes no executable line, so there is no behaviour to pin.
`tests/test_strawberry_patches.py` is run below as a regression check that the docstring edit did not
break import or collection, not as new coverage. A test asserting the absence of a prose fragment
would pin the prose, not a contract.

### Implementation discretion items

- Whether the ReST section underline needs adjusting now that a line below it is gone. Checked
  rather than assumed: heading and underline are **both 35 characters**
  (`len(line.rstrip('\n'))` on lines 254 and 255), so they already match and the deletion is below
  them anyway. Nothing owed, nothing touched. (The first draft of this bullet asserted a 35-vs-34
  mismatch and was wrong; the number was re-measured rather than read back.)
- Whether to reflow the surviving two-line sentence now that the paragraph is one line shorter.
  Decided: **no** — the dispatch forbids it explicitly, and both surviving lines are already inside
  the limit.

### Dispatched findings checklist

- [x] Delete the orphaned standalone occurrence of `independent upstream *bugs* that do not retire
      together:` from the `Three lifecycles, and one that left` section of
      `django_strawberry_framework/_strawberry_patches.py`'s module docstring.
- [x] Leave the resulting text as heading, underline, blank line, complete two-line sentence, blank
      line, numbered list — nothing else changed.
- [x] Re-derive the defect rather than trusting the dispatch: occurrences not matching lines, with
      the instrument named, 2 before and 1 after, both at the working tree.
- [x] Confirm the surviving occurrence is the one inside its sentence.
- [x] Confirm the orphan is pre-existing at HEAD (`ddf8bbaf`) and not this cycle's doing.
- [x] Confirm `git diff HEAD` on the file shows exactly two hunks, this cycle's citation repair
      intact.
- [x] Run and record verbatim: `ruff format --check`, `ruff check`, the docstring-parse check,
      `pytest --no-cov tests/test_strawberry_patches.py`, and an explicit ASCII-only check.

---

## Build report (Worker 2)

### Files touched

Grounded in `git status --short`. Exactly one tracked file was changed by this pass:

- `django_strawberry_framework/_strawberry_patches.py` — module docstring only. One line deleted:
  the orphaned `independent upstream *bugs* that do not retire together:` standing between the
  section underline's blank line and the complete sentence. Diff is 1 line deleted, 0 inserted.

Also created by this pass: this artifact, and an appended entry in the gitignored
`docs/builder/worker-memory/worker-2-024.md`.

Every other entry in `git status --short` is on the build plan's baseline-dirty list or is a
concurrent cycle's untracked artifact. Nothing else was touched and nothing was reverted; the full
listing is reproduced under `### Validation run`.

### Before/after measurement, with instruments named

**Instrument (occurrences, not matching lines):**

```shell
grep -o 'independent upstream \*bugs\* that do not retire together:' <file> | wc -l
```

`grep -o` emits one line per **occurrence**; `wc -l` counts them. The contrast instrument `grep -c`
counts **matching lines** and is recorded alongside to show the two are not interchangeable — here
they happen to agree (2 and 2) because the two occurrences sit on different lines, which is exactly
why agreeing on this file proves nothing in general and the `-o` form is the one relied on.

| Measurement | Command target | Result |
|---|---|---|
| Working tree, before edit | `django_strawberry_framework/_strawberry_patches.py` | **2** |
| Working tree, before edit, `grep -c` contrast | same | 2 (matching lines) |
| HEAD `ddf8bbafd928d634b6aeb546864e60bce8fec752`, read-only copy | scratchpad `head_sp.py` | **2** |
| Working tree, after edit | `django_strawberry_framework/_strawberry_patches.py` | **1** |

HEAD reference obtained read-only per `docs/builder/BUILD.md`
`## Claims are proven mechanically, never accepted on prose`, into a scratch path **outside** the
repo:

```shell
git show HEAD:django_strawberry_framework/_strawberry_patches.py > $S/head_sp.py
```

No `git stash`, `git checkout`, `git restore`, or `git worktree` was used at any point in this pass.

**The orphan is pre-existing.** HEAD carries 2 occurrences, identically arranged, so the duplication
predates this cycle. It is also absent from this cycle's diff before this slice: the pre-edit
`git diff HEAD -- <path>` was a single hunk at line 177 (the citation repair), and the fragment sits
at line 257.

**The survivor is the in-sentence one — read, not inferred from the count.** Post-edit context:

```
254  Three lifecycles, and one that left
255  -----------------------------------
256
257  Read the retirement question per concern, because this module carries three
258  independent upstream *bugs* that do not retire together:
259
260  1. **The ``UnicodeDecodeError`` translation** - retirable once upstream
```

Heading, underline, blank, complete two-line sentence, blank, numbered list. Exactly the shape the
contract names.

**Docstring length corroborates the size of the deletion.** `ast.get_docstring` on HEAD's copy
returns 20283 characters; on the working tree, 20226. Delta **-57**, which is the deleted line's 56
characters plus its newline, exactly. The citation repair in the other hunk contributes **0** to this
delta because both tokens are 42 characters long (see `### Notes for Worker 3`). So the docstring
lost the orphan and nothing else.

**The diff is exactly two hunks.**

```shell
git diff HEAD -- django_strawberry_framework/_strawberry_patches.py | grep -c '^@@'   # 2
```

```diff
@@ -177,7 +177,7 @@ body/multipart sites. Because the shield is a *reimplementation* rather
 than a delegating wrapper, ``_validate_upstream_shape`` pins the
 superseded upstream body source (the reimplementer's contract
 established by
-``_django_patches._UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE``) so an
+``_django_patches._AUDITED_REMOVE_DATABASES_FAILURES_SOURCES``) so an
 upstream body change fails loudly at ``apply()`` time instead of being
 silently superseded. The shield shares the envelope guard's lifecycle:
 retire both together when upstream #3398 lands.
@@ -254,7 +254,6 @@ errors at its HTTP boundary).
 Three lifecycles, and one that left
 -----------------------------------

-independent upstream *bugs* that do not retire together:
 Read the retirement question per concern, because this module carries three
 independent upstream *bugs* that do not retire together:
```

Hunk 1 is Slice 3's citation repair, byte-identical to what that slice landed (`1 insertion /
1 deletion`, unchanged by this pass). Hunk 2 is this slice: `0 insertions / 1 deletion`. No third
hunk, so no collateral reflow anywhere in the file.

### Tests added or updated

None. See `### Test additions / updates` in the plan above.

### Validation run

Every command below was run from the repository root. Output is verbatim; exit codes were captured
with `echo "exit=$?"` immediately after each command.

- `uv run ruff format --check django_strawberry_framework/_strawberry_patches.py` — **pass, exit 0**:

  ```
  warning: The following rule may cause conflicts when used with the formatter: `COM812`. To avoid unexpected behavior, we recommend disabling this rule, either by removing it from the `lint.select` or `lint.extend-select` configuration, or adding it to the `lint.ignore` configuration.
  1 file already formatted
  ```

  The `COM812` line is the repo's standing pre-existing configuration warning, not a result of this
  pass. `--check` is read-only; no write-mode `ruff format` was run, scoped or otherwise, so no file
  outside this slice could have been reformatted.

- `uv run ruff check django_strawberry_framework/_strawberry_patches.py` — **pass, exit 0**:

  ```
  All checks passed!
  ```

  Read-only; `--fix` was not passed.

- Docstring still parses — **pass, exit 0**:

  ```shell
  uv run python -c "import django_strawberry_framework._strawberry_patches as m; print(len(m.__doc__))"
  ```

  ```
  20227
  ```

  (`m.__doc__` is the raw literal at 20227; `ast.get_docstring` reports 20226 because
  `inspect.cleandoc` strips the trailing newline. Both were measured; the pair is recorded so the two
  numbers elsewhere in this artifact do not read as a contradiction.) The import succeeding is the
  load-bearing half: the module was imported, so the literal is terminated and the file compiles.

- ASCII-only (`AGENTS.md` rule 17, `.py`-only) — **three independent instruments, all pass**:

  ```shell
  LC_ALL=C grep -n '[^ -~	]' django_strawberry_framework/_strawberry_patches.py
  # (no output)  exit=1  -- grep exit 1 means no match, i.e. no byte outside printable ASCII + tab
  ```

  ```shell
  uv run python -c "
  d=open('django_strawberry_framework/_strawberry_patches.py','rb').read()
  bad=[(i,b) for i,b in enumerate(d) if b>127]
  print('non-ascii bytes:', len(bad), 'total bytes:', len(d))
  "
  # non-ascii bytes: 0 total bytes: 40943
  ```

  ```shell
  uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/_strawberry_patches.py
  # (silent)  exit=0
  ```

  The third is the repo's own `source-layout` pre-commit checker, which owns the ASCII-only rule
  (`AGENTS.md` rule 17: "ASCII-only .py source … enforced by `scripts/check_trailing_commas.py`"), so
  it is the authoritative instrument; the first two are byte-level cross-checks that do not depend on
  that script being right. Note this pass could only ever have **removed** bytes, so an ASCII
  regression was impossible by construction — the check is recorded because the dispatch asks for an
  explicit instrument, not because it was in doubt.

- `uv run pytest --no-cov tests/test_strawberry_patches.py` — **pass, exit 0**:

  ```
  ============================== 55 passed in 2.93s ==============================
  ```

  0 failures, 0 errors, 0 collection errors. The module name was resolved by listing `tests/` and
  taking the three **patch-related** modules it holds (`test_cross_web_patches.py`,
  `test_django_patches.py`, `test_strawberry_patches.py`) rather than guessed; `ls tests/*.py` returns
  **34** files in total, so those three are a named subset and not the listing's result. (Corrected on
  pass 2 — the pass-1 parenthetical read as an enumeration of the directory.) No coverage-shaped flag
  other than the mandatory `--no-cov` was used anywhere in this pass; `--cov`, `--cov-report`, and
  `--cov-config` appear nowhere.

- `git status --short` after every command above — 41 entries (42 once this artifact was written,
  `?? docs/builder/bld-slice-4-024-docstring_fragment.md`). The only slice-intended tracked entry
  is `M django_strawberry_framework/_strawberry_patches.py`. The four other dirty `.py` files
  (`django_strawberry_framework/optimizer/hints.py`, `tests/optimizer/test_hints.py`,
  `examples/fakeshop/apps/scalars/models.py`, `examples/fakeshop/test_query/test_scalars_api.py`) are
  on the dispatch's baseline-dirty list, as are `CHANGELOG.md`, `KANBAN.md`, `KANBAN.html`,
  `docs/GLOSSARY.md`, `docs/feedback.md`, `examples/fakeshop/db.sqlite3`, and the spec-021/022/025/026
  files; every `??` entry is another cycle's artifact. **Nothing was reverted and nothing needed to
  be.** This is the "stop-and-report, never a revert" obligation discharged with a null result.

### Failability proofs

`None; this pass introduced no new boundary.` The pass edits docstring text only — no guard, gate,
rejection path, or invariant is added, moved, or altered, which is the "renamed symbols, relocated
bodies, added annotations, **doc edits**" exemption in `docs/builder/BUILD.md`
`### What needs a proof, and what does not`.

The obligation that *does* apply is the stated-count rule in
`## Claims are proven mechanically, never accepted on prose`, discharged under
`### Before/after measurement, with instruments named`: every number was measured with `grep -o`
occurrence counting at the moment it was written.

Separately, the dispatch asks for a **failability proof of the change itself** — what evidence would
have shown it wrong. That is `### Failability proof` below, and it is not a mutation of production
code: two negative controls were run on **copies in a scratch path outside the repository**, so the
tree never held a mutation and no `ACTIVE-MUTATION.json` marker was ever written.

### Failability proof

Three ways this change could have been wrong, and the evidence that would have shown each. Two were
demonstrated with negative controls rather than argued.

**1. The docstring silently stops parsing, or the module stops importing.**

A deletion inside a triple-quoted literal can unbalance it or truncate the module. Evidence that
would have shown it: the import check raising instead of printing a length.

Negative control, on a scratch copy outside the repo (the working tree was never mutated): the
opening `"""` was split to `"" "`, and the same instrument was run against the copy —

```
SyntaxError: unterminated string literal (detected at line 1) (<unknown>, line 1)
```

against the real file's `docstring len: 20226`. **The instrument distinguishes the two states**, so
its clean result on the working tree is evidence rather than decoration. The scratch copy was deleted
after the control ran.

**2. The wrong occurrence survives — the count reads 1 and the text is still broken.**

This is the failure mode a bare count cannot see, and it is why the contract says "confirm the
surviving occurrence is the one inside its sentence".

Negative control: on a second scratch copy of HEAD, the **in-sentence** occurrence was deleted
instead of the orphan. The occurrence instrument returns **1** — identical to the correct edit's
result — while the text reads:

```
Three lifecycles, and one that left
-----------------------------------

independent upstream *bugs* that do not retire together:
Read the retirement question per concern, because this module carries three

1. **The ``UnicodeDecodeError`` translation** - retirable once upstream
```

A dangling clause followed by a sentence with no predicate: strictly worse than the defect, and
**invisible to every count in this artifact**. What separates the two outcomes is the context read
recorded under `### Before/after measurement`, not the number. The copy was deleted after the control
ran.

**3. A collateral reflow, or an edit to a line the dispatch forbids touching.**

Evidence that would have shown it: a third hunk in `git diff HEAD -- <path>`, or hunk 2 carrying any
`+` line, or hunk 1 disappearing/changing (which would mean this pass clobbered the concurrent
slice-3 citation repair). Measured: `grep -c '^@@'` returns **2**; hunk 2 is `0 insertions /
1 deletion` so no line was rewritten, only removed; hunk 1 is byte-identical to what Slice 3 landed.
Independently corroborated by the docstring-length delta of exactly **-57** — the deleted line plus
its newline, with nothing left over for a reflow to hide in.

A fourth check exists for free: `ruff format --check` returns `1 file already formatted`, so the file
is at the formatter's fixed point and no later formatting run will produce churn attributable to this
pass.

### Hot-path budget

`Not applicable; plan declares no hot path.` The build plan's declarations set the hot-path
declaration to `none` for the whole cycle, and a docstring carries no runtime cost in any case.

### Floor verification

`Not applicable; plan declares floor-verification scope none for this slice.` The plan assigns the
cycle's single floor run to Slice 1b, which ran it. A docstring change has no runtime behaviour to
verify at the floor, so a floor run here would measure nothing this slice changed.

### Implementation notes

- **A three-line anchor, not a one-line one.** The deleted text is a byte-for-byte duplicate of a
  line 2 lines below it, so an edit anchored on the orphan alone is ambiguous by construction and
  could have matched either. The edit was anchored on the whole three-line span (orphan + both lines
  of the complete sentence) and replaced it with the two-line sentence, which can match exactly one
  place in the file. This is the mechanical reason the wrong-occurrence failure in
  `### Failability proof` case 2 could not have happened here.
- **Deletion, not replacement.** The blank line above the orphan and the blank line below the
  sentence were both already present and were left alone; only the orphan line and its newline are
  gone. That is why the delta is exactly -57 and not -58 or -56.
- **`scripts/review_inspect.py` was not run**, and the skip is recorded per `docs/builder/BUILD.md`
  `### When to run the helper during build`: the pass adds zero lines of logic, adds no new `.py`
  file, and touches nothing under `optimizer/` or `types/`, so none of the Worker 2 or Worker 3
  triggers fires and the AST overview would be identical before and after.

### Notes for Worker 3

- **The whole diff is one deleted docstring line.** The cheapest independent re-derivation is the
  three commands under `### Before/after measurement`: the `grep -o … | wc -l` occurrence count at
  HEAD (2) and at the working tree (1), plus reading lines 254-260 to confirm which one survived.
  Do not accept the count alone — negative control 2 shows a count of 1 is also what the *wrong*
  edit produces.
- **Scratch paths used, all outside the repository:**
  `…/scratchpad/head_sp.py` (read-only HEAD copy, retained),
  `…/scratchpad/wrong_delete.py` and `…/scratchpad/broken_docstring.py` (the two negative controls,
  both deleted after use). Nothing was written under `docs/builder/temp-tests/`, and no file inside
  the repo was ever mutated for a control.
- **The section underline was checked and is correct** — heading and underline are both 35
  characters, so a reviewer diffing the section owes it no attention. Recorded because a
  docstring-section edit is exactly where an underline mismatch would be introduced, and "I did not
  break it" is worth a measurement rather than a silence.
- **One measured correction to a `final-accepted` sibling artifact, recorded not fixed.**
  `bld-slice-3-024-rename_rot_sweep.md` `### Implementation notes` states "The replacement is 43
  characters against the old 42, so the docstring line grows by one character." Both tokens are
  **42** characters (`_UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE` and
  `_AUDITED_REMOVE_DATABASES_FAILURES_SOURCES`; verified by
  `python -c "print(len('…'), len('…'))"` and corroborated by this slice's docstring-length delta of
  exactly -57, which leaves no room for a +1 from the other hunk). The slice-3 conclusion it supports
  — no reflow needed, line stays inside the limit — is unaffected; only the arithmetic is off by one.
  That artifact is `final-accepted` and belongs to a closed slice, so it is **not** edited here.

### Notes for Worker 1 (spec reconciliation)

1. **This slice closes `bld-final-024.md` `## Deferred work catalog` item 6.** The item's own text
   says the deferral was licensed by "nothing" and that the fix "needs an owner: whichever pass next
   owns that docstring." That owner is this pass, and the fix has landed. Worker 1 should record the
   closure wherever the catalog's open items are tracked at cycle close; this artifact is the
   evidence. **No spec amendment is owed** — the deleted text was a copy-paste duplicate carrying no
   claim, so no contract the spec states changes.

2. **A standing observation, not a spec matter, worth one line in the rationale companion if it fits
   an existing entry — do not open a new decision for it.** The fragment survived from its
   introduction through every gate this process has: tests green, ruff clean, `ruff format` at its
   fixed point, and a Worker 3 review pass that *read the section and correctly identified the
   defect* while (rightly) declining to fix it out of contract. Prose duplication inside a docstring
   is invisible to every mechanical gate the repo runs, in the same way
   `bld-slice-3-024-*.md` `### Notes for Worker 1` item 3 observes that **no gate in this process
   resolves a citation**. It is the same shape of gap and the same maintainer decision is already
   escalated there (a `scripts/`-resident checker); this is a second piece of evidence for it, not a
   new escalation.

3. **The slice-3 artifact's "43 characters against the old 42" is off by one** (see
   `### Notes for Worker 3`). Both tokens are 42. That artifact is `final-accepted` and was not
   edited. Recorded so a later reader who re-derives the docstring-length arithmetic does not
   conclude this slice's -57 delta is wrong.

---

## Review (Worker 3)

Scope of this pass: the working-tree diff in `django_strawberry_framework/_strawberry_patches.py`,
the plan and build report above, and every count either states. `bld-slice-1a`/`1b` were not read —
they are a closed slice of this cycle and nothing in this diff touches them. Prior-artifact content
was read where this artifact cites it, because a provenance citation is a claim like any other.

Read-only HEAD reference used throughout, per `docs/builder/BUILD.md`
`## Claims are proven mechanically, never accepted on prose`, into a scratch path **outside** the
repo. No `git stash` / `git checkout` / `git restore` / `git worktree` at any point, and no
`--cov*` flag other than the mandatory `--no-cov`.

```shell
S=/private/tmp/claude-501/.../scratchpad
git show HEAD:django_strawberry_framework/_strawberry_patches.py > $S/w3_head_sp.py
```

`git log --oneline -1` -> `ddf8bbaf finish 23`, so HEAD is the commit the dispatch names.

### High:

None.

### Medium:

#### The provenance count "recorded three times before this slice" does not reproduce

`### The defect` states: "Provenance: recorded three times before this slice, each time as out of the
recording pass's contract" and enumerates three sites. The enumeration is a **stated count**, one of
the three claim shapes `docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on
prose` names, and it is asserted with no instrument. Re-derived by reading every prior artifact that
mentions the fragment (instrument: `grep -rn 'independent upstream' --include='*.md' .` plus
`grep -rn 'Three lifecycles' …`, then resolving each hit to its owning `###` heading with
`grep -n '^## \|^### '`), the population is **seven passages across three artifacts and four
distinct workers**:

| # | Site | Disposition recorded there |
|---|---|---|
| 1 | `bld-slice-3-024-rename_rot_sweep.md:361-368` — Worker 2's `### Notes for Worker 1`, **unnumbered** | declined as out of contract |
| 2 | `bld-slice-3-024-rename_rot_sweep.md:657-664` — Worker 3's `### What looks solid` | decline **endorsed**, HEAD presence confirmed |
| 3 | `bld-slice-3-024-rename_rot_sweep.md:703-707` — Worker 3's `### Notes for Worker 1` **item 4** | declined, routed for an owner |
| 4 | `bld-slice-3-024-rename_rot_sweep.md:761-766` — Worker 1's `## Final verification` | decline upheld |
| 5 | `bld-slice-2-024-spec_reconciliation.md:232` — catalog item 6 | declined as outside a Markdown-only contract |
| 6 | `bld-slice-2-024-spec_reconciliation.md:445-448` — `### Counts and claims re-derived independently` | reproduced at HEAD |
| 7 | `bld-final-024.md:240-250` — `### Deferred work catalog` item 6 | routed for an owner |

The count is wrong under **both** readings of its own qualifier. Read broadly ("recorded"), the
population is 7, not 3. Read narrowly ("each time as out of the recording pass's contract",
i.e. sites that *declined* it), the population is 1/3/4/5 = **4**, and the artifact's own list
includes site 2, which endorses a decline rather than making one, while omitting site 5.

What makes this Medium rather than cosmetic: site 5 is named **in the very sentence this artifact
quotes as its authorising clause**. `bld-final-024.md` item 6 reads "*Source:* `bld-slice-3`
`### Notes for Worker 1` item 4 **and** `bld-slice-2` catalog item 6". The artifact quoted that item,
carried one of its two named sources forward, and dropped the other. That is the derived-description
failure this cycle exists to catch, reproduced inside the artifact that catches it elsewhere.

Recommended change: state the population with the instrument named, or drop the number and cite the
sites. Nothing in the diff changes; the correction is two sentences in `### The defect`.

### Low:

#### The `### Notes for Worker 1` "item 4" citation and its parenthetical name different passages

`bld-slice-3-024-rename_rot_sweep.md` carries **two** `### Notes for Worker 1 (spec reconciliation)`
sections — Worker 2's at line 289 and Worker 3's at line 677 (`grep -n '^### '` on that file). Only
Worker 3's is numbered to 4; item 4 is at line 703. Worker 2's record of the fragment is the
**unnumbered** bolded paragraph at 361-368. So "`### Notes for Worker 1` item 4 (builder declined it
as unrelated cleanup)" resolves to Worker 3's item and attributes it to Worker 2. Both passages
exist and both are declines, so nothing downstream is misled about the facts — only about who said
what. `bld-final-024.md` item 6 makes the same conflation, so this is inherited rather than
originated here. Recommended: cite Worker 2's passage by content (`#"One defect found in the writable
file that is deliberately NOT repaired here"`) rather than by a number that belongs to the other
section.

#### "by the build plan's recorded dispatch deviation" is false for Slice 3

`## Plan (Worker 2, written in lieu of a Worker 1 planning pass)` claims "Slices 1 and 3 of this
cycle skipped their planning passes by the build plan's recorded dispatch deviation".
`docs/builder/build-024-django_trac_37064_hardening-0_0_7.md` `## Dispatch deviations (deliberate,
recorded)` (line 275) carries exactly **two** bullets and **both name Slice 1** — "Slice 1 skips its
Worker 1 planning pass" and "Slice 1 runs read-only". No Slice-3 deviation is recorded there.
Slice 3 did in fact run a builder-authored plan (`bld-slice-3-024-rename_rot_sweep.md:10`), so the
event is real; the **licensing authority** cited for it is not. The same is true of this slice, whose
plan-in-lieu is likewise unrecorded in the build plan. Recommended: attribute the shape to the
sibling artifact and the dispatch instruction rather than to a plan section that does not carry it.

#### The `tests/` listing parenthetical reads as an enumeration of the directory

`### Validation run` says the module name "was resolved by listing `tests/`
(`test_cross_web_patches.py`, `test_django_patches.py`, `test_strawberry_patches.py`)". `ls tests/*.py`
returns **34** files. The three named are the patch-related subset, which is almost certainly what
was meant, but as written the parenthetical reads as the listing's result. Recommended: say
"the three patch-related modules in `tests/`". No consequence — the module chosen is the right one.

### DRY findings

None owed by the diff. The pass adds, moves, and shares no logic; it deletes one line of docstring
prose, which is itself a de-duplication. The existence challenge does not apply — nothing is
abstracted, created, or indirected.

One standing observation, endorsing rather than duplicating the builder's `### Notes for Worker 1`
item 2: prose duplication inside a docstring passes every mechanical gate this repo runs — `ruff
format --check` reports the file at its fixed point, `ruff check` is clean, `check_trailing_commas
--check` is silent, all 55 rows of `tests/test_strawberry_patches.py` pass, and the module imports.
I ran every one of those against the **defective** HEAD text as well as the fixed text; each returns
the same result on both. That is a fact about the gates, not a new escalation — it is the same
contract-level question already routed in `bld-slice-3` `### Notes for Worker 1` item 3, and the
slice is not held on it.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` — **empty**. `__all__` and the re-export
list are unchanged. The diff does not reach a public surface: it is docstring text inside a private
module (`_strawberry_patches`), and `m.__doc__` is read by nothing executable
(`grep -rln '__doc__\|get_docstring' tests/ examples/` returns **zero** files; the only readers in
the repo are under `scripts/`).

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md. Confirmed against `git status --short`:
`CHANGELOG.md` is dirty, but it is on the dispatch's baseline-dirty list and is not in this slice's
diff.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. Checked anyway, because
`docs/TREE.md` is **rendered from module docstrings** (`scripts/build_tree_md.py`) and a docstring
edit is exactly the shape that can strand it:

- `grep -n '_strawberry_patches' docs/TREE.md` -> lines 198, 319 (module) and 477, 700 (test module),
  all rendering the summary line `Defensive patches for upstream Strawberry bugs, applied at app
  load.`
- `m.__doc__.split('\n')[0]` on the working tree -> `Defensive patches for upstream Strawberry bugs,
  applied at app load.` — byte-identical, unchanged by the deletion, which sits at line 257 of the
  file and 254+ of the docstring.
- `grep -rn 'independent upstream' --include='*.md' .` finds the fragment in **no** standing doc —
  only in this cycle's `bld-*` scratchpads.

So no regenerate is owed and none was skipped. `docs/SPECS/spec-024-…md` line 22 also enumerates the
six TREE-feeding surface modules for this card and `_strawberry_patches.py` is **not** among them.

### Claim verification (re-derived vs. accepted)

**Re-derived independently — my measurements, not the report's:**

1. **The defect is real and pre-existing at HEAD.** Instrument: occurrences, not matching lines.

   ```shell
   grep -o 'independent upstream \*bugs\* that do not retire together:' $S/w3_head_sp.py | wc -l   # 2
   grep -c 'independent upstream \*bugs\* that do not retire together:' $S/w3_head_sp.py           # 2 (lines)
   grep -o '…same pattern…' django_strawberry_framework/_strawberry_patches.py | wc -l             # 1
   ```

   Reproduces the report's 2 / 2 / 1 exactly. The `-o` form is the one relied on; the `grep -c`
   contrast is recorded for the same reason the report records it.

2. **The RIGHT occurrence was deleted — read, not counted.** A count of 1 is produced by either
   deletion, so the count is not the evidence. `sed -n '248,268p'` on the working tree against the
   same range of the HEAD copy:

   ```
   Three lifecycles, and one that left
   -----------------------------------

   Read the retirement question per concern, because this module carries three
   independent upstream *bugs* that do not retire together:

   1. **The ``UnicodeDecodeError`` translation** - retirable once upstream
   ```

   The survivor is the second line of a complete sentence with subject, verb, and its colon leading
   into the numbered list. The orphan — a subordinate clause with no subject, above the sentence that
   contains it — is gone. This is the contract's shape and the correct half of the pair.

3. **Nothing else changed.** `git diff HEAD -- <path>` piped to `grep -c '^@@'` -> **2**.
   `git diff HEAD --numstat` -> `1  2  django_strawberry_framework/_strawberry_patches.py`, i.e. one
   insertion (hunk 1's citation repair) and two deletions (hunk 1's replaced line + hunk 2's orphan).
   Hunk 2 carries **zero** `+` lines, so no line was rewritten, only removed; no third hunk, so no
   reflow. Hunk 1 is Slice 3's `_UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE` ->
   `_AUDITED_REMOVE_DATABASES_FAILURES_SOURCES` repair, intact. `git diff --check` -> exit 0.

4. **The docstring-length arithmetic.** Measured with `ast.get_docstring` on both files in one
   process:

   | Quantity | HEAD | working tree | delta |
   |---|---|---|---|
   | `ast.get_docstring` | 20283 | 20226 | **-57** |
   | raw literal `.value` | 20284 | 20227 | **-57** |

   `len('independent upstream *bugs* that do not retire together:')` -> **56**; +1 newline -> 57.
   Both of the report's figures reproduce, including the `20227` vs `20226` pair it flagged as
   non-contradictory (the raw literal keeps the trailing newline `inspect.cleandoc` strips).

5. **Both tokens are 42 characters** — `len('_UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE')` = 42,
   `len('_AUDITED_REMOVE_DATABASES_FAILURES_SOURCES')` = 42. So the report's correction of
   `bld-slice-3-024-rename_rot_sweep.md:266` ("43 characters against the old 42") is **right**: that
   figure is off by one, and slice 3's conclusion drawn from it (no reflow owed) is unaffected. This
   is also what licenses the -57 delta to be attributed wholly to hunk 2.

6. **Heading and underline are both 35 characters** — `len(lines[253])` = 35, `len(lines[254])` = 35
   at working-tree lines 254/255. The report's self-correction (its first draft said 35 vs 34)
   **reproduces**: 35 vs 35, no underline adjustment owed. Both self-reported corrections in the
   dispatch therefore check out.

7. **File-level byte facts.** `len(read_bytes())` -> **40943**, matching the report; non-ASCII byte
   count -> **0**; `LC_ALL=C grep -n '[^ -~\t]'` -> no match, exit 1;
   `uv run python scripts/check_trailing_commas.py --check <file>` -> silent, exit 0. ASCII-only rule
   (`AGENTS.md` rule 17, `.py`-only) satisfied on three independent instruments.

8. **Working-tree census.** `git status --short | wc -l` -> **42** (the artifact now exists), and the
   dirty `.py` set is exactly five: the slice's target plus
   `django_strawberry_framework/optimizer/hints.py`, `tests/optimizer/test_hints.py`,
   `examples/fakeshop/apps/scalars/models.py`, `examples/fakeshop/test_query/test_scalars_api.py` —
   all four on the dispatch's baseline-dirty list. The report's "41 before this artifact, 42 after"
   reproduces. No `ACTIVE-MUTATION.json` anywhere in the tree.

**Accepted on the report's record, not re-derived:** the two scratch-path negative controls (the
split-`"""` parse control and the wrong-occurrence control). Both ran on copies outside the
repository and were deleted, so there is nothing left to re-measure; the tree carries no evidence of
either, which is itself consistent with the claim. Their conclusions are independently corroborated
by items 2 and 3 above, which is why re-running them buys nothing.

### Gates re-run by this pass (not accepted from the report's transcript)

| Command | Result |
|---|---|
| `uv run ruff format --check .` (repo-wide) | **exit 0** — `424 files already formatted` (plus the standing `COM812` config warning) |
| `uv run ruff check .` (repo-wide) | **exit 0** — `All checks passed!` |
| `uv run pytest --no-cov tests/test_strawberry_patches.py` | **55 passed**, 0 failures, 0 collection errors |
| `uv run pytest --no-cov tests/test_strawberry_patches.py tests/test_apps.py tests/test_views.py` | **285 passed** — the wider scope of every package test module that references `_strawberry_patches` |
| `uv run python -c "import django_strawberry_framework._strawberry_patches as m; print(len(m.__doc__))"` | **exit 0**, `20227` — module imports, literal terminated, file compiles |
| `LC_ALL=C grep -n '[^ -~\t]' <file>` | no output, exit 1 — no non-ASCII byte |
| `uv run python scripts/check_trailing_commas.py --check <file>` | silent, **exit 0** |
| `git diff --check` | **exit 0** |

The scope was widened past the report's single module deliberately:
`grep -rln '_strawberry_patches' tests/ examples/` names **four** test modules
(`tests/test_strawberry_patches.py`, `tests/test_apps.py`, `tests/test_views.py`,
`examples/fakeshop/test_query/test_transport_api.py`), not one. The three package-tier modules were
run together and all pass. The live tier was not run — no test in it reads a docstring, and the
report's scope choice is not a finding, only a narrower one than the file's dependents warrant.

### Failability proofs — audit and independent re-run set

**Re-run set: empty, and legal.** `docs/builder/BUILD.md` `### What needs a proof, and what does not`
exempts "renamed symbols, relocated bodies, added annotations, **doc edits**". The diff introduces no
boundary, guard, gate, or rejection path — it deletes prose — so nothing meets `worker-3.md`'s
mandatory floor (recorded row count of 3 or fewer; security or data-isolation decision) and there is
nothing to re-run. The report's `None; this pass introduced no new boundary.` is correct and is
**accepted as recorded**.

The source carve-out was **not** exercised: no production file was mutated by this review. No
`ACTIVE-MUTATION.json` marker exists and the tree's only dirty `.py` files are the slice's target and
four baseline-dirty concurrent files.

The report's `### Failability proof` (the change-level one, distinct from the boundary proofs) is
sound as far as it goes, and its case 2 is the right instinct — a count of 1 is exactly what the
destructive edit produces. I did not accept it on that argument: item 2 of
`### Claim verification` is my own read of the surviving text.

### Hot-path budget

Verified not owed. `build-024-…md`'s declarations set the hot-path declaration to `none` for the
cycle, and a docstring carries no runtime cost. `Not applicable` is correct.

### Floor verification

Verified not owed. The plan assigns the cycle's single floor run to Slice 1b. The diff has no runtime
behaviour, no Django / Strawberry / channels seam is touched, and a floor run here would measure
nothing this slice changed. `Not applicable` is correct.

### Dispatched findings checklist — walked

All seven boxes are ticked and all seven land:

1. Orphan deleted — hunk 2, verified.
2. Resulting shape is heading / underline / blank / two-line sentence / blank / list — verified by
   reading lines 254-260.
3. Defect re-derived with the instrument named, occurrences not lines, 2 -> 1 — verified; the
   report's HEAD figure is also correct at 2.
4. Survivor confirmed in-sentence — verified by reading, and this is the box a count could not close.
5. Orphan confirmed pre-existing at `ddf8bbaf` — verified from an independent read-only HEAD copy.
6. Exactly two hunks — verified, plus `--numstat` corroboration.
7. Gates run and recorded verbatim — verified, and all re-run above.

No box is over-ticked and none is silently unaddressed.

### What looks solid

- **The edit itself is exactly right and minimally scoped.** One line removed, zero inserted in that
  hunk, no reflow, no reword, no second file. The three-line anchoring described in
  `### Implementation notes` is the correct technique for a duplicate-line deletion and is why the
  destructive alternative could not have happened mechanically rather than only by luck.
- **The report distinguishes the count from the judgement.** Its negative control 2 states outright
  that a count of 1 is also the wrong edit's result and that the context read, not the number, is the
  discriminator. That is the specific trap this dispatch names, identified by the builder before
  review rather than by review.
- **Both self-reported corrections reproduce.** The 43-vs-42 correction against slice 3 is right, and
  the 35-vs-34 self-correction in its own draft is right. Neither number was read back; both were
  re-measured, and both survive an independent re-measurement here.
- **The `-57` arithmetic is a genuine independent check on the diff**, not decoration: it closes the
  gap a hunk count leaves, since two hunks with a hidden reflow inside one of them would still count
  two. Combined with hunk 2 carrying no `+` line, the file is pinned from two directions.
- **`review_inspect.py` skip is correct and correctly recorded** on both sides: zero lines of logic
  added, no new `.py` file, nothing under `optimizer/` or `types/`, so no Worker 2 or Worker 3 trigger
  in `BUILD.md` `### When to run the helper during build` fires. Skipped here for the same reason,
  recorded per `worker-3.md` `## Static helper use`.
- **The baseline-dirty discipline held.** Nothing was reverted, nothing outside the slice was
  touched, and the four concurrent `.py` files are untouched at the byte level in this diff.

### Temp test verification

None created. `docs/builder/temp-tests/` carries only prior cycles' `024-final` and `024-fix2`
directories (gitignored, untracked, not this pass's). Nothing to promote: the slice changes no
executable line, and a test asserting the absence of a prose fragment would pin prose, not a
contract. The report's reasoning on this is endorsed.

### Notes for Worker 1 (spec reconciliation)

1. **No spec amendment is owed, and I re-derived that rather than accepting it.** The deleted text is
   a copy-paste duplicate carrying no claim.
   `grep -n 'Three lifecycles\|independent upstream' docs/SPECS/spec-024-…md docs/SPECS/appx/spec-024-…-rationale.md`
   returns **zero** hits for either phrase; neither file states any contract about this docstring
   section, and `_strawberry_patches.py` is not among the six TREE-feeding surface modules the spec
   enumerates at line 22. Nothing in the spec or its companion goes stale.

2. **`bld-final-024.md` `### Deferred work catalog` item 6 is closed by this diff** — the fix landed
   and is verified above. Worker 1 owns recording the closure wherever the catalog's open items are
   tracked at cycle close.

3. **The build plan lists no Slice 4.**
   `docs/builder/build-024-django_trac_37064_hardening-0_0_7.md` `## Checklist` (line 288) carries
   six rows ending at the final gate, and its artifact list (lines 114-119) names six artifacts;
   neither includes `docs/builder/bld-slice-4-024-docstring_fragment.md`. `BUILD.md`
   `## Required plan structure` wants every artifact listed and every slice carrying a checkbox.
   Worker 0/1 own the plan — I have not touched it. Flagging rather than actioning also because this
   cycle's maintainer-set scope is spec files and code `.py` files only, so a plan edit may itself be
   out of scope; if so, record it as deferred rather than skipped.

4. **`Escalated:` — nothing new.** The "no mechanical gate sees prose duplication in a docstring"
   observation in the report's `### Notes for Worker 1` item 2 is corroborated by this review (every
   gate returns an identical result on the defective and the fixed text), but it is the same
   contract-level question already escalated as `bld-slice-3` `### Notes for Worker 1` item 3. It is
   a second data point for that decision, not a second decision, and the slice is not held on it.

### Review outcome

`revision-needed`.

The **code change is correct and I would accept it as it stands**: the defect is real and
pre-existing at `ddf8bbaf` (2 occurrences, measured on an independent read-only HEAD copy), the
correct occurrence was deleted (established by reading the surviving prose, not by the count that
cannot tell the two edits apart), the diff is exactly the two expected hunks with Slice 3's citation
repair intact and no third hunk, and every gate passes on a re-run at a scope wider than the report's.
Every count in the report reproduced — including both self-reported corrections, which the dispatch
asked me to check and which are both right.

What holds it is the one Medium: `### The defect`'s "recorded three times before this slice" is a
stated count asserted without an instrument, and it does not reproduce under either reading of its own
qualifier — the population is seven passages, or four declines, and the artifact's own enumeration
drops `bld-slice-2` catalog item 6, a source named in the same `bld-final-024.md` sentence this
artifact quotes as its authorising clause. `BUILD.md` `## Claims are proven mechanically, never
accepted on prose` grades an unverified claim of that shape Medium, and `worker-3.md`'s
`### Acceptance gate` permits `review-accepted` with a Medium only when resolution needs spec context
Worker 2 cannot supply. It does not here: the fix is two sentences in a section Worker 2 owns, in an
artifact that is still open. Holding it costs one cheap re-pass; waving it through would put a fourth
wrong provenance description into a cycle whose subject is that derived descriptions outlive their
sources — and this one was inherited from `bld-final-024.md`, which is how the class propagates.

The three Low findings are in the same two sections and are cheap to fold into the same re-pass. No
finding asks for a change to `django_strawberry_framework/_strawberry_patches.py`; **Worker 2 should
not touch the source file on the re-pass.** No boundary in the diff meets the mandatory re-run floor,
so the empty re-run set is legal; the source carve-out was not exercised and the tree carries no
mutation.

---

## Build report (Worker 2, pass 2)

Revision pass answering `## Review (Worker 3)`. **No source file was touched.** The reviewer accepted
the diff outright ("the code change is correct and I would accept it as it stands") and every finding
is against this artifact's own prose, so `django_strawberry_framework/_strawberry_patches.py` is
byte-identical to the state pass 1 left it in.

### Files touched

Grounded in `git status --short`. Exactly one file changed by this pass:

- `docs/builder/bld-slice-4-024-docstring_fragment.md` — this artifact: the `### The defect`
  provenance paragraph rewritten, the plan preamble's licensing sentence corrected, the
  `### Validation run` `tests/` parenthetical clarified, and this report appended.

Also appended: an entry in the gitignored `docs/builder/worker-memory/worker-2-024.md`.

`django_strawberry_framework/_strawberry_patches.py` is **not** in this pass's changes.
`git diff HEAD -- django_strawberry_framework/_strawberry_patches.py` still shows the same two hunks
and `grep -c '^@@'` still returns **2**.

**Prior sections were corrected in place rather than only superseded here**, on the reviewer's
explicit recommendation ("the correction is two sentences in `### The defect`"). Leaving a
known-false count standing upstream while correcting it downstream is the partial-claim-fix failure
this cycle exists to catch. Every in-place correction carries a bracketed "corrected on pass 2"
marker naming what the pass-1 wording said, so the record stays auditable rather than silently
rewritten; nothing in the pass-1 `## Build report (Worker 2)` measurements was altered.

### Findings addressed

**Medium — "recorded three times before this slice" does not reproduce. Accepted and fixed.**

Re-derived from scratch rather than adopting either of the reviewer's figures. Corpus, vocabulary,
resolution method, and both quantities are now stated in `### The defect`; the numbers there are
mine, measured while writing them.

- **Corpus** stated as an explicit parameter: tracked per-cycle artifacts under `docs/builder/`,
  excluding this artifact and excluding `docs/builder/worker-memory/`. The memory exclusion is not
  bookkeeping — `worker-2.md` `## Required reading` forbids reading another worker's memory file, and
  an unscoped `grep -r` over `docs/builder/` reaches two of them.
- **Vocabulary broadened past the phrases the fragment quotes.** The reviewer's instrument
  (`Three lifecycles` / `independent upstream`) returns **11** matching lines in that corpus; the
  broadened one returns **21**. The difference matters: `bld-slice-2-024:165` records the fragment as
  "the duplicated docstring fragment in `_strawberry_patches.py`" and contains **neither** phrase, so
  it is invisible to the narrow vocabulary. That passage is site 5 in the corrected table and is a
  **decline**, so it belongs to the narrow reading's population too.
- **Result: 8 passages across 3 artifacts and 3 worker roles**, or **4** under the narrow "declined
  as out of contract" reading. Pass 1's "three" is wrong under both, and its enumeration dropped
  `bld-slice-2` catalog item 6 — one of the two sources named inside the `bld-final-024.md` sentence
  pass 1 quoted as its own authorising clause.

**Low — the `bld-slice-3` "item 4" citation conflates two sections. Accepted and fixed.**
Confirmed independently: that file carries two `### Notes for Worker 1` sections, Worker 2's
(unnumbered, at the passage `#"One defect found in the writable file that is deliberately NOT
repaired here"`) and Worker 3's (numbered, item 4). Worker 2's record is now cited by content and
Worker 3's item 4 is attributed to Worker 3. The same conflation in `bld-final-024.md` item 6 is
recorded, not fixed — that artifact is `final-accepted`.

**Low — "by the build plan's recorded dispatch deviation" is false for Slice 3. Accepted and fixed.**
Re-read the plan section rather than taking the finding on its word: `## Dispatch deviations
(deliberate, recorded)` carries exactly two bullets, "Slice 1 skips its Worker 1 planning pass" and
"Slice 1 runs read-only". Neither names Slice 3 and neither names this slice. The preamble now
attributes the shape to this slice's dispatch instruction and to the sibling artifact's precedent,
and quotes `bld-slice-3-024-rename_rot_sweep.md:10` — which is itself precise ("Slice 1 skipped its
planning pass … and the repair cohort it licenses inherits that shape"); the false generalisation was
pass 1's, not slice 3's.

**Low — the `tests/` listing parenthetical reads as an enumeration of the directory. Accepted and
fixed.** Re-measured: `ls tests/*.py | wc -l` -> **34**, and `ls tests/*patch*.py` -> exactly the
three named. The sentence now says the three patch-related modules and states the 34.

### Figures of the reviewer's that did not reproduce

Both are in the Medium finding's own table, and neither changes its verdict — the finding is right
and pass 1's "three" is wrong either way.

- **"seven passages" -> I measure 8.** The extra is `bld-slice-2-024:165`, Worker 1's
  `### Notes for Worker 1` decline, which the reviewer's two-phrase vocabulary cannot see. This is
  the standing trap in its purest form: **a finding's grep vocabulary is not its population**, and
  the finding whose subject is an under-measured population was itself measured with an
  under-inclusive instrument.
- **"four distinct workers" -> I measure 3 worker roles.** Resolving each passage to its owning
  `##` heading gives Worker 2 (site 1), Worker 3 (sites 2, 3, 7), and Worker 1 (sites 4, 5, 6, and
  `bld-final-024.md`, the Worker-1-owned final gate). No fourth role appears. If the intent was to
  count Worker 1's custodian pass and its final-verification pass separately, that is a count of
  passes, not of workers.

Everything else in the review reproduced or was already my own measurement: the 2 -> 1 occurrence
counts, the two-hunk / `--numstat 1 2` shape, the -57 docstring delta, the 42/42 token lengths, the
35/35 heading and underline, the 40943 bytes, and the 42-entry working-tree census.

### Flagged by the reviewer, acknowledged, and deliberately not actioned

- **`bld-slice-3-024-rename_rot_sweep.md`'s "43 characters against the old 42".** Confirmed wrong by
  both of us (both tokens are 42). That artifact is `final-accepted` and belongs to a closed slice,
  so it is **not** edited. The correction lives here and in the reviewer's section; slice 3's
  conclusion drawn from the figure (no reflow owed) is unaffected either way.
- **The build plan's Slice 4 rows.** The reviewer recorded that the plan "lists no Slice 4". Re-read
  at this pass and the claim no longer holds: the plan carries `## Slice 4 dispatch (post-gate,
  maintainer-directed)` at line 288, `docs/builder/bld-slice-4-024-docstring_fragment.md` at line 118
  of its artifact list, and two checklist rows at lines 323-326. Either the rows landed after the
  review was written or the measurement was taken before them. Recorded rather than actioned in any
  case: the plan is Worker 0's, and there is now nothing to add to it. (Re-grepping a cited file
  before recording a correction against it is the point — this is the second time in this cycle a
  finding about an un-editable file went stale between being written and being read.)

### Tests added or updated

None, unchanged from pass 1. This pass changed no executable line and no `.py` file at all.

### Validation run

Scoped to what this pass's edits could plausibly invalidate. The reviewer re-ran the full gate set
after pass 1 and it passed; nothing here touches source, so re-running it would measure nothing this
pass changed.

- `uv run python scripts/check_trailing_commas.py --check docs/builder/bld-slice-4-024-docstring_fragment.md`
  — **pass, exit 0**, silent. This is the checker that owns the `.md` link-def scaffold rule; the
  artifact uses only backticked paths and no cross-file markdown links, so no `<!-- LINK DEFINITIONS -->`
  block is owed, matching the sibling `bld-*.md` artifacts.
- Source untouched, re-confirmed: `git diff HEAD -- django_strawberry_framework/_strawberry_patches.py | grep -c '^@@'`
  -> **2**, and the occurrence instrument
  `grep -o 'independent upstream \*bugs\* that do not retire together:' <file> | wc -l` -> **1**.
- `git status --short` — the only tracked-file change attributable to this pass is this artifact
  (untracked, `?? docs/builder/bld-slice-4-024-docstring_fragment.md`). No new dirty file appeared;
  the baseline-dirty set is unchanged and nothing was reverted.
- No `pytest`, `ruff format`, or `ruff check` re-run: no `.py` file changed on this pass, so their
  pass-1 and reviewer-re-run results stand unaltered. No `--cov*` flag was used anywhere.

### Failability proofs

`None; this pass introduced no new boundary.` Unchanged from pass 1 and doubly true here — this pass
changed no executable line and no `.py` file. The change-level failability argument in
`### Failability proof` is untouched and still stands; the reviewer's item 2 of
`### Claim verification` independently corroborates its conclusion by reading the surviving prose.

### Hot-path budget

`Not applicable; plan declares no hot path.` Unchanged.

### Floor verification

`Not applicable; plan declares floor-verification scope none for this slice.` Unchanged.

### Implementation notes

- **The corpus was made an explicit parameter of the count, not an implicit one.** Pass 1's failure
  was not arithmetic — it was that "recorded three times" never said *recorded where*, so no reader
  could re-derive it and no instrument could contradict it. The corrected passage states the corpus,
  its two exclusions and the reason for each, the vocabulary, the resolution method, and reports
  matching lines and passages as separate quantities.
- **Both readings are reported rather than one chosen.** "Recorded" and "recorded as out of the
  recording pass's contract" are different populations (8 and 4), and pass 1's qualifier claimed the
  second while its list sampled the first. Stating both with their subjects named is what stops the
  next reader inheriting the ambiguity.

### Notes for Worker 3

- Nothing in `django_strawberry_framework/_strawberry_patches.py` changed on this pass; the pass-1
  diff verification stands as re-run in your own section.
- The one number worth re-deriving is the provenance population. The instrument is described in full
  in `### The defect` and is a ~15-line Python one-shot; the cheap partial check is that
  `grep -rn 'duplicated docstring fragment' --include='*.md' docs/builder/` reaches
  `bld-slice-2-024-spec_reconciliation.md:165` while
  `grep -rn 'Three lifecycles\|independent upstream'` does not.
- The two "not mine to fix" items are acknowledged above with their evidence; the build-plan one
  changed state between your pass and this one, so it needs no action from anybody.

### Notes for Worker 1 (spec reconciliation)

Both pass-1 items stand unchanged: this slice closes `bld-final-024.md` `## Deferred work catalog`
item 6, and **no spec amendment is owed** — independently confirmed by the reviewer, whose
`grep -n 'Three lifecycles\|independent upstream'` over the spec and its rationale companion returns
zero hits in either.

One addition from this pass, for whoever records the closure: `bld-final-024.md` item 6 names two
sources and this cycle's derived descriptions of it have now dropped one of them twice — once in that
item's own "item 4" attribution (which resolves to Worker 3's section while the prose credits the
builder) and once in this artifact's pass-1 provenance sentence. The item itself is `final-accepted`
and was not edited. If the catalog's closure is recorded anywhere durable, recording it **by content**
(`#"One defect found in the writable file that is deliberately NOT repaired here"` for Worker 2's
decline, `### Notes for Worker 1` item 4 for Worker 3's routing) rather than by section-plus-number is
what stops the conflation propagating a third time.

---

## Review (Worker 3, pass 2)

Scope: this artifact's prose only. The source file was re-verified as untouched and is not
re-litigated — `git diff HEAD --numstat -- django_strawberry_framework/_strawberry_patches.py` ->
`1  2`, `grep -c '^@@'` -> **2**, occurrence instrument -> **1**. Pass 1's acceptance of the code
change stands unchanged. The full gate set was **not** re-run: no `.py` file changed on pass 2, so a
re-run would measure nothing this pass touched, and Worker 0 owns the gate re-run over the source
change.

**I lost the Medium on the evidence.** Both of the figures I put in it were wrong, and the builder's
counter-measurement is right on both. The findings below record the ruling, the evidence, and the one
new Low that survives.

### High:

None.

### Medium:

None. The pass-1 Medium is **closed** — see `### Adjudication of the disputed figures`. The underlying
finding was correct (pass 1's "recorded three times" was a stated count with no instrument and does
not reproduce) and it is fixed; the two quantities I offered in its place were themselves wrong.

### Low:

#### The stated corpus reaches a passage the stated vocabulary cannot see

The corrected `### The defect` declares its corpus as "the tracked per-cycle artifacts under
`docs/builder/`", with two named exclusions (this artifact, `worker-memory/`), and its instrument as a
glob over `pathlib.Path('docs/builder').glob('*.md')`. That glob returns **24** files and includes
`build-024-django_trac_37064_hardening-0_0_7.md`, which is a tracked per-cycle artifact of this cycle
and is not excluded. It carries a passage about this defect that the stated vocabulary does not match:

```docs/builder/build-024-django_trac_37064_hardening-0_0_7.md:292
item 6 is the only one whose `*Deferral licensed by:*` clause reads
**nothing** — it is a `.py` docstring defect …
```

```docs/builder/build-024-django_trac_37064_hardening-0_0_7.md:323
- [ ] Slice 4: Orphaned-docstring-fragment repair — `bld-final-024.md` deferred-catalog item 6,
```

`Orphaned-docstring-fragment` is **hyphenated**, so it matches neither `docstring fragment` nor
`dangling (truncated )?(clause|fragment)`; "`.py` docstring defect" matches nothing in the list. Same
class as the defect this pass just corrected in my own instrument, one level up.

**Ruled non-blocking, and the population stands at 8.** Three reasons, in decreasing weight:

1. The passage **authorises rather than records.** It never states what the fragment is — no
   duplication, no clause, no text. The population is "passages that record this fragment"; a
   checklist row naming the repair is not a recording of the defect.
2. The population is explicitly scoped "written **before** this slice", and
   `## Slice 4 dispatch (post-gate, maintainer-directed)` is the section that *constitutes* this
   slice's dispatch. It is the boundary of the population, not a member of it.
3. It is Worker 0's, and Worker 0 is not one of the three roles that recorded the defect — so
   admitting it would change the role count as well, on a passage that records nothing.

Recommended change: one clause in the *Population:* sentence stating that the build plan's Slice 4
dispatch is excluded as this slice's own authorisation rather than a prior recording. That makes the
boundary a decision rather than an artifact of the vocabulary. Not held on it: the figure is right,
its subject is named, and the correction adds no number.

### Adjudication of the disputed figures

I re-derived with an instrument built to see **both** candidate populations before reading the
builder's, then implemented the builder's stated instrument literally to check it reproduces from its
own description. Both runs are below.

**Ruling 1 — "seven passages" vs "8": the builder is right; my figure was wrong.**

The disputed passage is `bld-slice-2-024-spec_reconciliation.md:165`. Read directly:

```docs/builder/bld-slice-2-024-spec_reconciliation.md:165
The one source-shaped item found — the duplicated docstring fragment in `_strawberry_patches.py` —
is pre-existing at HEAD, is not rename rot, and is routed to the deferred-work catalog rather than
repaired, since repairing it here would broaden this slice past a Markdown-only contract.
```

It is a real recording and a real **decline**, and it contains neither `Three lifecycles` nor
`independent upstream` — confirmed, not assumed:

```shell
grep -n 'Three lifecycles\|independent upstream' docs/builder/bld-slice-2-024-spec_reconciliation.md
# 232, 446 only — line 165 does not appear
grep -n 'duplicated docstring fragment' docs/builder/bld-slice-2-024-spec_reconciliation.md
# 165
```

Its owning heading is `## Build report (Worker 1, acting as author under the cycle's recorded dispatch
deviation)` -> `### Notes for Worker 1`, so it is Worker 1's decline in the custodian slice. My pass-1
instrument was the two phrases the fragment itself quotes, which is a sample of the *defect's*
vocabulary rather than of the *corpus's*. **A finding's grep vocabulary is not its population** — and
the finding whose subject was an under-measured population was measured with an under-inclusive
instrument. The correction is mine to wear.

I did not adopt the 8 on the builder's say-so. Two independent runs:

- **My own broader instrument**, deliberately over-inclusive (`Three lifecycles | independent upstream
  | docstring fragment | duplicated docstring | dangling | truncated | copy-paste artifact | catalog
  item 6 | item 6 | orphan`, plus any line pairing `_strawberry_patches` with
  `docstring|fragment|clause`), over every `docs/builder/*.md`: **81 candidate lines**, which I then
  read and filtered. Everything it added over the builder's set was a false positive of a different
  subject — orphan *commits* in `bld-slice-1a`/`1b`, dangling *link definitions* in the 025/026
  artifacts, `item 6` of `bld-003-final.md` and of `bld-slice-1b`'s `**Facts for the spec**`, and
  `bld-final-024.md:272`, which is the *citation* repair (`bld-slice-1a` item 19), not this fragment.
  No ninth recording exists inside the corpus except the build-plan passage ruled on above.
- **The builder's stated instrument, implemented literally** from the description in
  `### The defect` — same vocabulary, same glob, same heading-stack resolution, same 8-line collapse:

  ```
  corpus files in glob: 24
  MATCHING LINES: 21
  PASSAGES: 8
  ```

  All eight passages reproduce with the **same line ranges and the same heading attributions** as the
  artifact's table: `bld-slice-3:362-368`, `658-661`, `703-704`, `761-763`; `bld-slice-2:165`, `232`,
  `445-446`; `bld-final-024:240-248`. That is the property pass 1's "three" lacked — a stated figure a
  reader can re-derive from the artifact's own description without asking the author what was counted.

**Ruling 2 — "four distinct workers" vs "3 worker roles": the builder is right; my figure was wrong
under both readings.**

Resolving each of the 8 passages to the `##` heading that owns it:

| Passages | Owning `##` heading | Role |
|---|---|---|
| 1 | `bld-slice-3` `## Build report (Worker 2)` | Worker 2 |
| 2, 3 | `bld-slice-3` `## Review (Worker 3)` | Worker 3 |
| 4 | `bld-slice-3` `## Final verification (Worker 1)` | Worker 1 |
| 5, 6 | `bld-slice-2` `## Build report (Worker 1, acting as author under the cycle's recorded dispatch deviation)` | Worker 1 |
| 7 | `bld-slice-2` `## Review (Worker 3)` | Worker 3 |
| 8 | `bld-final-024.md` — Worker 1's gate report (`BUILD.md` `## Final test-run gate`: "Worker 1 runs the final test-run gate and produces `docs/builder/bld-final.md`") | Worker 1 |

The set is `{Worker 1, Worker 2, Worker 3}` — **3**. There is no fourth role. My "four" came from
reading `bld-slice-2`'s build report as a builder's; its heading says otherwise, and I did not resolve
it before writing the number. That is this card's standing failure exactly: **the digits were checked
and the subject was not.**

The builder's diagnosis ("if the intent was to count Worker 1's custodian pass and its
final-verification pass separately, that is a count of passes, not of workers") is the right reading of
where my number came from, but it does not rescue it either — counted as **passes** the population is
**6**: slice-3's builder pass, slice-3's review pass, slice-3's final-verification pass, slice-2's
custodian pass, slice-2's review pass, and the gate. Four is not the answer to any question here.

**Which population the artifact should state:** roles, as it does. Passes would need each pass named to
be re-derivable, and the passage table already carries that information positionally. `3 worker roles`
names its subject unambiguously in the same clause as the number, which is the whole requirement.

### Method claim: corrected in place, with markers, no pass-1 measurement altered — confirmed

The pass-2 report claims three in-place corrections, each carrying a bracketed "corrected on pass 2"
marker naming the pass-1 wording, with no pass-1 measurement touched. All three hold:

| Correction | Marker | Names the pass-1 wording? |
|---|---|---|
| Plan preamble licensing sentence (`:13-21`) | `:15` | yes — "the pass-1 wording claimed the plan licensed a Slice 3 skip, which it does not" |
| `### The defect` provenance (`:50-92`) | `:50-53` | yes — quotes the pass-1 sentence verbatim |
| `### Validation run` `tests/` parenthetical (`:338-344`) | `:341-342` | yes — "the pass-1 parenthetical read as an enumeration of the directory" |

**A note against my own instrument, for the third time this review.** `grep -n -i 'corrected on pass 2'`
returns only lines 15, 50 and 913 — it misses the third marker entirely, because that marker **wraps
across a line break** (`(Corrected on` / `pass 2 — …`) and a line-based grep cannot see a phrase split
over two lines. I nearly filed "the third correction carries no marker" on that output. This is the
repo's standing reflow trap in a new place: it breaks a `grep` as readily as a `#"substring"` citation.
The marker is there; the instrument was wrong.

**No pass-1 measurement was altered.** Checked by reading `## Build report (Worker 2)` end to end
against my pass-1 read of the same sections: the `### Before/after measurement` instrument block and
its four-row table (2 / 2 / 2 / 1) are unchanged word for word; `20283` / `20226` / `-57` / `20227`,
`55 passed in 2.93s`, `non-ascii bytes: 0 total bytes: 40943`, the `41 entries (42 once this artifact
was written)` census, the `### Implementation discretion items` 35-character underline bullet with its
own 35-vs-34 self-correction, and `### Notes for Worker 1` item 3's 42/42 correction against slice 3 all
survive intact. The only prose that moved is the three passages above, each marked.

**My own `## Review (Worker 3)` section was not edited.** Verified by reading it back: scope paragraph,
the Medium finding with its seven-row table and "four distinct workers" wording, the three Lows, the
claim-verification items, the gate table, and the `### Review outcome` reasoning are all as I wrote
them — including the two figures now ruled wrong, which is correct: a superseded measurement stays on
the record rather than being quietly repaired.

### The three Low findings — landed and now true

- **`bld-slice-3` "item 4" conflation.** Fixed. Site 1 is now cited by content
  (`#"One defect found in the writable file that is deliberately NOT repaired here"`) and attributed to
  Worker 2; site 3 is `### Notes for Worker 1` **item 4** attributed to Worker 3. The note at
  `:88-92` states the two-section trap outright. Re-verified: `grep -n '^### '` on that file gives
  Worker 2's section at 289 and Worker 3's at 677, and item 4 is at 703. The same conflation in
  `bld-final-024.md` item 6 is recorded and not edited — correct, that artifact is `final-accepted`.
- **The dispatch-deviation licensing claim.** Fixed, and the attribution of the error is right. The
  plan's `## Dispatch deviations (deliberate, recorded)` still carries exactly two bullets, both
  naming Slice 1. `bld-slice-3-024-rename_rot_sweep.md:12-14` reads "Slice 1 skipped its planning pass
  by the plan's recorded dispatch deviation, and the repair cohort it licenses inherits that shape" —
  precise about Slice 1, with the inheritance stated as its own reasoning. So the false generalisation
  *was* pass 1's, not slice 3's, exactly as the report says.
- **The `tests/` parenthetical.** Fixed and re-measured independently: `ls tests/*.py | wc -l` -> **34**,
  `ls tests/*patch*.py` -> exactly `test_cross_web_patches.py`, `test_django_patches.py`,
  `test_strawberry_patches.py`. The sentence now states the 34 and calls the three a named subset.

### Retracted from pass 1

**"The build plan lists no Slice 4" — withdrawn.** Re-derived at this pass: the plan carries
`## Slice 4 dispatch (post-gate, maintainer-directed)` at line 288, the artifact row at line 118, and
two checklist rows at 323-326 (the Slice 4 box and the gate re-run box). The rows landed after my pass
was written. Nothing is owed to anyone; the note in my pass-1 `### Notes for Worker 1` item 3 should be
read as superseded by this paragraph.

### DRY findings

None owed. No `.py` file changed on this pass and no logic exists to duplicate. The existence challenge
does not apply.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` — **empty**, unchanged from pass 1. No source
file changed on this pass at all.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. The one adjacent surface
checked at pass 1 (`docs/TREE.md`, rendered from module docstrings) is unaffected and unchanged — the
rendered summary line is the docstring's first line and no `.py` file moved on this pass.

### Failability proofs — audit and independent re-run set

**Re-run set: empty, and legal**, unchanged from pass 1 and doubly so — this pass changed no executable
line and no `.py` file. `None; this pass introduced no new boundary.` is correct and accepted as
recorded. The source carve-out was not exercised by either party; no `ACTIVE-MUTATION.json` exists and
the tree's dirty `.py` set is unchanged from pass 1 (the slice's target plus the four baseline-dirty
concurrent files).

### Hot-path budget

`Not applicable` — verified unchanged and still correct.

### Floor verification

`Not applicable` — verified unchanged and still correct.

### What looks solid

- **The builder re-derived rather than adopting either of my figures**, and said so explicitly. It was
  right to: one of them was wrong in its instrument and the other in its subject. A pass that had taken
  the reviewer's numbers on seniority would have shipped both errors into the record.
- **The corrected passage states the corpus as an explicit parameter**, with both exclusions and the
  reason for each — and the `worker-memory/` exclusion is a real rule (`worker-2.md` forbids reading
  another worker's memory), not tidying. That is what makes the figure re-derivable, and it is why my
  literal re-implementation of the description lands on the same 8 passages with the same line ranges.
- **Both readings are reported with their subjects named** (8 recordings, 4 declines) instead of one
  being chosen silently. Pass 1's sentence claimed the narrow reading while sampling the broad one;
  reporting both is what stops the next reader inheriting that ambiguity.
- **Matching lines and passages are reported as separate quantities** (21 and 8). Conflating them is
  the `grep -c`-versus-`grep -o` error one level up, and this artifact has now avoided it twice.
- **The corrections were made in place with markers rather than only superseded downstream.** The
  partial claim fix — a known-false count left standing upstream while a later section quietly corrects
  it — is a failure mode this card has hit before, and this pass closed it without rewriting history.
- **Two "not mine to fix" items were re-checked before being restated**, and one of them (the build
  plan) had changed state since my review. Re-grepping a cited file before recording a correction
  against it is what caught that.

### Temp test verification

None created on either pass. `docs/builder/temp-tests/` holds only prior cycles' `024-final` and
`024-fix2` directories, untouched. Nothing to promote.

### Notes for Worker 1 (spec reconciliation)

1. **No spec amendment is owed** — unchanged from pass 1 and independently re-confirmed there
   (`grep -n 'Three lifecycles\|independent upstream'` over `spec-024` and its rationale companion
   returns zero hits in either; `_strawberry_patches.py` is not among the six TREE-feeding surface
   modules the spec enumerates at line 22).
2. **`bld-final-024.md` `### Deferred work catalog` item 6 is closed by this slice.** The builder's
   recommendation for how to record the closure is endorsed: cite the two sources **by content** rather
   than by section-plus-number, because `bld-final-024.md` item 6's own "item 4" attribution resolves
   to Worker 3's section while its prose credits the builder, and that conflation has now propagated
   twice within this cycle.
3. **The one open Low is a one-clause edit to `### The defect`'s *Population:* sentence** (exclude the
   build plan's Slice 4 dispatch as this slice's own authorisation). It is recorded here, on disk,
   where final verification reads it. It changes no number and is not worth a fourth pass on its own;
   fold it if the artifact is touched again for any other reason.
4. **My pass-1 `### Notes for Worker 1` item 3 is withdrawn** — see `### Retracted from pass 1`. The
   build plan carries Slice 4 and owes nothing.

### Review outcome

`review-accepted`.

The pass-1 Medium is closed and it was closed the right way — re-derived from a stated corpus with a
stated vocabulary and a stated resolution method, reproducing exactly (21 matching lines, 8 passages,
every line range and heading attribution matching) when I implemented the artifact's own description
independently. Both figures I offered in that finding were wrong: `bld-slice-2-024:165` is a real
eighth passage my two-phrase vocabulary could not see, and there is no fourth worker role under any
reading — the set is `{W1, W2, W3}`, and counting passes instead gives 6, not 4. The underlying
finding was right and the numbers I replaced it with were not; both facts belong on the record.

All three Low findings landed and are true as re-derived. The method claim holds: three in-place
corrections, three markers, each naming the pass-1 wording, and no pass-1 measurement altered — my own
review section included, which is correct, since a superseded measurement should stay visible rather
than be quietly repaired. One new Low survives (the stated corpus reaches the build plan while the
stated vocabulary cannot see it) and is explicitly ruled non-blocking with its reasons and its
one-clause remedy recorded for Worker 1: the passage authorises rather than records, sits outside the
"before this slice" scope, and belongs to a fourth role that recorded nothing.

The source change was accepted at pass 1 and is unchanged and re-verified here. No boundary meets the
mandatory re-run floor, the empty re-run set is legal, the carve-out was not exercised, and the tree
carries no mutation.

---

## Final verification (Worker 1)

Scope: the slice's source change, the one open Low from `## Review (Worker 3, pass 2)`, the spec /
rationale custody question, and the final gate re-run this slice re-opened. HEAD read read-only into a
scratch path outside the repo; no `git stash`, `git checkout`, `git restore`, or `git worktree` at any
point, and no coverage-shaped flag other than the mandatory `--no-cov`.

`git log --oneline -1` -> `ddf8bbaf finish 23`, the commit the dispatch names, at pass start and close.

### Source change — re-derived, not accepted

Every item below is my own measurement, not a reading of the sections above.

- **Real and pre-existing at `ddf8bbaf`.** Occurrences, not matching lines:
  `grep -o 'independent upstream \*bugs\* that do not retire together:' <HEAD copy> | wc -l` -> **2**;
  same instrument on the working tree -> **1**.
- **The correct occurrence was deleted**, judged by reading the surviving prose rather than by the
  count — a count of 1 is equally what deleting the in-sentence half produces. At HEAD the section is
  heading / underline / blank / a subordinate clause with no subject / the complete two-line sentence /
  blank / numbered list; in the working tree it is heading / underline / blank / the complete sentence /
  blank / numbered list. The survivor is the sentence's second line, and its "three" agrees with the
  three-item list it introduces. The orphan is gone.
- **Exactly two hunks, no reflow, no other file.** `grep -c '^@@'` on the file's diff -> **2**;
  `--numstat` -> `1  2`; hunk 2 carries zero `+` lines; hunk 1 is Slice 3's
  `_UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE` -> `_AUDITED_REMOVE_DATABASES_FAILURES_SOURCES` repair,
  intact. `ast.get_docstring` delta -57 = the deleted line's 56 characters plus its newline, leaving no
  room for a hidden reflow. The dirty `.py` set is five files and only this one is in the cycle's diff.

**Accepted.** The change is right, complete, and minimally scoped.

### The one open Low — discharged

`## Review (Worker 3, pass 2)` `### Notes for Worker 1` item 3 asked for one clause in
`### The defect`'s *Population:* sentence excluding the build plan's `## Slice 4 dispatch (post-gate,
maintainer-directed)`. Added. It names the two spellings the vocabulary cannot match, states the
exclusion's grounds (the passage authorises rather than records; it constitutes the "written before
this slice" boundary), and adds no number — the figure of 8 passages was already correct and is
unchanged, as the reviewer ruled.

### Spec reconciliation — nothing owed

Re-derived rather than accepted from the review. Neither the fragment's phrasing nor its section
appears in `spec-024` or its rationale companion; `_strawberry_patches.py` is named nowhere in the spec
and is not among the six TREE-feeding surface modules it enumerates; the rationale's only mention under
Decision 5 `### Changes this Decision underwent` is scoped to the **citation** repair, which this
deletion neither falsifies nor extends, since the fragment is a copy-paste duplicate rather than rename
rot. The deleted text carried no claim, so no Decision's contract, rejected alternative, change record,
or retired claim moves — and there is no decision it could be keyed to, which
`docs/builder/BUILD.md` `## Spec rationale extraction` requires of any rationale entry. The spec's
status/header lines were re-read per `worker-1.md` `## Spec status-line re-verification` and still
describe the build's state. **No spec edit and no rationale edit were made.**

### Final gate

Re-run in full and **appended** to `docs/builder/bld-final-024.md` as
`## Final test-run gate, re-run after Slice 4`; that file's existing record was not altered and its
`Status:` stays `final-accepted`. All seven executed commands exit 0 (both full sweeps, the two
`manage.py` checks, both ruff gates, `git diff --check`). Floor verification was deliberately not
re-run — it is owned and recorded by Slice 1b, was independently re-executed by that slice's review,
and a docstring deletion cannot change which audited upstream body validates; the reasoning is stated
in the appended section rather than the omission left silent. No failure appeared anywhere, so nothing
was escalated.

### Deferred work

None. `docs/builder/bld-final-024.md` `## Deferred work catalog` item 6 is closed by this slice; the
closure is recorded in the appended gate section, cited by content rather than by section-plus-number
per the standing correction above.

### Summary

One line deleted from `django_strawberry_framework/_strawberry_patches.py`'s module docstring: an
orphaned standalone `independent upstream *bugs* that do not retire together:` that duplicated a clause
of the sentence immediately below it. No executable line changed, no boundary was added, no test was
owed, and `docs/TREE.md` owes no regenerate because the rendered summary line — the docstring's first
line — is byte-unchanged.

### Spec changes made (Worker 1 only)

None. See `### Spec reconciliation — nothing owed` above for the re-derivation.

Final status: `final-accepted`.
