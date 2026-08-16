# Build: Final test-run gate — version_release_alignment / 0.0.4 (012)

Spec reference: `docs/SPECS/spec-012-version_release_alignment-0_0_4.md` (whole file, 57 lines) and its
companion `docs/SPECS/appx/spec-012-version_release_alignment-0_0_4-rationale.md` (434 lines)
Plan reference: `docs/builder/build-012-version_release_alignment-0_0_4.md` `## Checklist`, final row
Predecessor artifacts (both `final-accepted`, both read in full before this gate ran):
`docs/builder/bld-012-r1-rationale_and_spec_reconciliation.md`,
`docs/builder/bld-012-r2-doc_completion_archive_audit.md`
Status: final-accepted

## Plan (Worker 1)

The gate is `docs/builder/BUILD.md` `## Final test-run gate` run verbatim, plus the two obligations
the plan's `## Artifact list` folded in from the integration pass this cycle does not run (no source
landed, so there is no cross-slice DRY surface): the staged-anchor sweep, and a full read of every
closed artifact. One extra verification is folded in because it is this cycle's whole subject — a
third independent reading of the five-surface alignment the reconciled `## Scope` now asserts. No new
work is planned here; the gate measures, records, and attributes.

### Dispatched findings checklist

- [x] Full sweep — `uv run pytest --no-cov`, no `--cov*` flag anywhere in this pass.
- [x] Django consistency — `manage.py check` and `makemigrations --check --dry-run`.
- [x] Lint / format / diff, all read-only — `ruff format --check .`, `ruff check .`, `git diff --check`.
- [x] Floor verification — scope `none`, recorded with its reason; no floor venv built.
- [x] Staged-anchor sweep folded in from the integration pass.
- [x] Every closed artifact (R1, R2) read in full.
- [x] Five-surface alignment re-derived at the current `HEAD`, independently of R1 and R2.
- [x] `### Deferred work catalog` assembled from both artifacts.

---

## Final verification (Worker 1)

Baseline at gate time, **re-derived rather than quoted**: `HEAD` = `c2b8622d11de4086e36e299458683b44ac393ec9`
(the plan measured `5851bb59`; R2 already recorded the move), `git status --porcelain | wc -l` -> **108**
(93 at plan time, 102 at R1, 104 at R2 — the moving baseline the plan warns about). This cycle's own
diff is exactly one tracked path plus four untracked files:

| Path | State | Owner |
|---|---|---|
| `docs/SPECS/spec-012-version_release_alignment-0_0_4.md` | `M` | R1 |
| `docs/SPECS/appx/spec-012-version_release_alignment-0_0_4-rationale.md` | `??` (new) | R1, extended by R2 |
| `docs/builder/build-012-version_release_alignment-0_0_4.md` | `??` | Worker 0 |
| `docs/builder/bld-012-r1-…md`, `bld-012-r2-…md` | `??` | this cycle |
| `docs/builder/bld-012-final.md` | `??` (new) | this pass |

Everything else in the 108 is concurrent maintainer sessions' work: ~20 modified package sources and a
comparable number of modified tests from an in-flight `0.0.14` review cycle, `docs/GLOSSARY.md`,
`docs/SPECS/spec-009-*` and its companion, `docs/bug_hunt/`, `docs/review/**`, `scripts/bug_hunt.py`,
and the `bld-009-*` / `build-009-*` artifacts. **None was edited, reverted, staged, stashed, or
`git checkout`ed** (`AGENTS.md` rule 34, rule 22 for `docs/review/**`, `START.md` `## Concurrent
sessions`). `scripts/build_glossary_md.py` and `scripts/build_kanban_md.py` were **not** run, no DB
write of any kind was made, nothing was committed, and no branch was created or switched.

### 1. Full sweep — `uv run pytest --no-cov`

**FAIL — one row, and this cycle did not cause it. It is pre-existing at `HEAD` on stronger evidence
than the prior cycle's gate could obtain; attributed below and escalated to the maintainer.**

```
1 failed, 5776 passed, 40 skipped in 94.16s (0:01:34)
FAILED tests/rest_framework/test_inputs.py::test_dedupe_serializer_input_shape_is_sole_cache_protocol
```

The failing assertion is `assert shape_a == shape_b` at `tests/rest_framework/test_inputs.py:658`,
differing on `SerializerInputShape.serializer_class` — two distinct class objects both named
`tests.rest_framework.test_inputs._item_serializer.<locals>.ItemSer`, i.e. the dedupe cache did not
return the same shape for two builds of an equivalent serializer.

**This is the same node id `docs/builder/bld-011-final.md` recorded**, and its status changed between
the two gates: there it was an *uncommitted* test paired with an uncommitted rewrite of the module it
tests; here both have been committed.

**Attribution, with commands rather than assertion** (`docs/builder/BUILD.md`
`## Claims are proven mechanically, never accepted on prose`):

- **The failing test now exists at `HEAD`.**
  `git show HEAD:tests/rest_framework/test_inputs.py | grep -c "def test_dedupe_serializer_input_shape_is_sole_cache_protocol"`
  -> **1**.
- **Both the test and the module it tests are CLEAN in this working tree**, so the tree state of the
  failing pair *is* the `HEAD` state and no dirty file of any session is between them.
  `git status --porcelain -- tests/rest_framework/test_inputs.py django_strawberry_framework/rest_framework/inputs.py`
  -> **empty**; `git diff --stat` over the same two paths -> **empty**.
- **The commit that introduced it is a concurrent maintainer session's.**
  `git log --oneline -S"def test_dedupe_serializer_input_shape_is_sole_cache_protocol" -- tests/rest_framework/test_inputs.py`
  -> `5851bb59 Share the FilterSet/OrderSet permission facade and land the remaining DRY consolidations.`
  That is the commit the plan recorded as `HEAD` at plan time — the concurrent DRY work landed with
  this row already failing.
- **It is not order-dependent, so it is not an artifact of the full-sweep interleaving.**
  `uv run pytest "tests/rest_framework/test_inputs.py::test_dedupe_serializer_input_shape_is_sole_cache_protocol" --no-cov -p no:randomly`
  -> `1 failed in 1.50s`, same assertion, same attribute.
- **This cycle wrote no package source and no test at all.** Its entire diff is the five Markdown
  paths in the table above. Neither `django_strawberry_framework/rest_framework/inputs.py` nor
  `tests/rest_framework/` is in any item's writable set, and no item of this cycle can own the fix.

**Escalated to the maintainer**, who is the only party able to run a clean `HEAD` tree
(`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`, "Pre-existing at
HEAD" — a failing test is not worker-verifiable, so recording plus escalating is what discharges the
obligation). The evidence here is as close to that verification as a worker can get without a clean
checkout: the failing pair is byte-identical to `HEAD`, the failure reproduces in isolation from a
single node id, and the introducing commit is named. No re-loop is dispatched, because re-looping
routes work to an item of this cycle and both are closed, correct, and unrelated.

**Gate disposition.** `final-accepted` is set on the strength of the attribution, not in spite of the
failure: the plan's `## Baseline-dirty out-of-scope files` is the recorded pre-flight baseline
exception, this cycle's whole output is Markdown, and no output of this cycle is executed by the
suite. Masking it or "fixing" a concurrent session's committed work would violate `AGENTS.md` rule 34
and rule 5's ban on shortcuts alike.

### 2. Django consistency checks

| Command | Result |
|---|---|
| `uv run python examples/fakeshop/manage.py check` | **PASS** — `System check identified no issues (0 silenced).`, exit 0 |
| `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | **PASS** — `No changes detected`, exit 0 |

Both are green even though this cycle made no DB write and touched no model: R2's audit read the
kanban DB only through a `sqlite3 -readonly` scratchpad copy, and a clean `makemigrations --check`
confirms nothing of this cycle reached the schema.

### 3. Lint / format / diff gate — read-only, never `--fix`

| Command | Result |
|---|---|
| `uv run ruff format --check .` | **PASS** — `420 files already formatted`, exit 0 |
| `uv run ruff check .` | **PASS** — `All checks passed!`, exit 0 |
| `git diff --check` | **PASS** — no output, exit 0 |

All three are green across the **whole** tree, concurrent sessions' modified sources and tests
included, so no pre-existing lint exception needs attributing. `ruff format --check` emits a standing
`COM812` formatter-conflict warning on stderr; it is a configuration advisory, not a failure, and
exit 0 is the reading. No `--fix` was used in any form.

### 4. Floor verification

**Scope `none`, as declared, and no floor venv was built.**
`docs/builder/build-012-version_release_alignment-0_0_4.md` line 11 declares "Floor-verification
scope: **none.** No item touches a Django / Strawberry / channels integration seam — no item touches
executable code at all", and both item artifacts re-declare it (R1 `### Test additions / updates`; R2
the same, naming the plan's declaration).

The declaration re-derives at this working tree rather than being accepted: this cycle's five paths
are Markdown, one of them modified and four untracked, and nothing in the diff is imported, executed,
or collected by the suite. None of `docs/builder/BUILD.md` `### When it is required`'s seams —
request/response handling, view or ASGI plumbing, upload or body parsing, the session/auth surface,
queryset or expression compilation, schema and type construction against Strawberry internals,
consumer or middleware wiring — is touched, and that section names docs work as an explicit `none`
case. A floor venv would have nothing version-sensitive to execute. **The shared `.venv` was not
mutated by any pass of this cycle**, and no `uv pip install` was run.

### 5. Staged-anchor sweep (folded in from the integration pass)

```shell
grep -rEn 'TODO\(spec-012|TODO-(ALPHA|BETA|STABLE)-012' . \
  --exclude=KANBAN.md --exclude=KANBAN.html --exclude=BACKLOG.md
```

**One hit, a false positive; zero surviving anchors.** The hit is
`docs/builder/bld-012-r2-doc_completion_archive_audit.md:411`, where R2 quotes the sweep command
`` `grep -rn 'TODO(spec-012' .` `` inside its own verification record. It is a quoted command, not an
anchor. The unfiltered sweep (no `--exclude`) returns the same **1** occurrence, so the three excluded
board files carry no `TODO-<MILESTONE>-012` row either — consistent with card `DONE-012-0.0.4` being
shipped and Done. No package source, test, comment, or standing doc carries an anchor naming this
spec or card. This re-derives R2's independently measured `grep -rn 'TODO(spec-012' .` -> **0** rather
than accepting it. No finding, so nothing is routed to an item.

(This artifact itself now contains the pattern in the fenced command above; a later sweep will see two
false positives for the same reason, both quotations inside per-cycle `bld-*.md` scratchpads.)

### 6. Every closed artifact read

`bld-012-r1-rationale_and_spec_reconciliation.md` and `bld-012-r2-doc_completion_archive_audit.md`
were each read end to end before this gate was written, per `docs/builder/BUILD.md` `## Cross-slice
integration pass` step 1 and step 5 — the two integration obligations that survive when a cycle lands
no source. Their `### Notes for Worker 0`, `### Items for the final gate's ### Deferred work catalog`,
`### 8. Deferred-work items for bld-012-final.md`, and `### Spec changes made (Worker 1 only)`
sections are what the catalog below is assembled from. **Nothing either artifact deferred is dropped,
and nothing is invented.**

Both artifacts' `### Dispatched findings checklist` blocks were audited against their diffs: R1's
eight boxes (F1-F8) and R2's five (F9-F12 plus F8 carried) are all `- [x]`, each with a landed
contract or an explicitly recorded "recorded, not fixed" disposition (F8). **No box in either artifact
is left `- [ ]`, so no deferral reason is owed under `## Final verification job` step 3.**

**No `bld-integration.md` exists, deliberately.** The plan's `## Artifact list` records the
disposition and the reason: the integration pass scans landed source for cross-slice duplication and
this cycle lands none, so its shadow-overview comparisons (steps 2-4) have no input. Its two live
obligations are discharged in sections 5 and 6. Same disposition, and the same reason, as the
spec-003, spec-010, and spec-011 cycles.

### 7. The five-surface alignment, re-derived at `c2b8622d`

The reconciled `## Scope` asserts that a release cut aligns **five** surfaces on one version string,
and that alignment is a **per-release obligation, not a standing property of these five files**. That
is the one claim in this spec a third reading can cheaply confirm, and it is exactly what this cycle
is about, so it was re-derived here independently of R1's and R2's measurements.

| Surface | Reading at `HEAD` = `c2b8622d` | Command |
|---|---|---|
| `pyproject.toml` `#"version = "` | `0.0.14` (line 4) | `grep -n '^version' pyproject.toml` |
| `django_strawberry_framework/__init__.py` `#"__version__ = "` | `0.0.14` (line 58) | `grep -n '__version__' …/__init__.py` |
| `uv.lock`, `django-strawberry-framework` root entry | `0.0.14` (line 544, under `name =` at 543) | `grep -n -A2 'name = "django-strawberry-framework"' uv.lock` |
| `tests/base/test_init.py::test_version` | `assert __version__ == "0.0.14"` | file read |
| `CHANGELOG.md`, newest release heading | `## [0.0.14] - 2026-07-20` (line 19) | `grep -n '^## \[' CHANGELOG.md` |

**All five agree, on `0.0.14`.** The spec's contract therefore holds in exactly the shape it now
states it: the invariant is intact and its *value* has moved ten patches past `0.0.4`, which is the
reading F6's remedy was written to make possible without applying a chronology. R1 and R2 both
measured `0.0.14` at `5851bb59`; this third reading at the moved `HEAD` reproduces it line for line
(`__init__.py:58`, `uv.lock:544`, `CHANGELOG.md:19` are the same lines R1 recorded).

**V5 re-derives too, and is a limit rather than a defect.** `tests/base/test_init.py::test_version`
asserts the literal and nothing in it reads `pyproject.toml`; the file's other three tests pin the
logger name, the optimizer re-export identity, and `__all__`. The spec says precisely that — rule 31
as prose policy, `::test_version` pinning the runtime literal alone — so no sentence of the spec is
falsified by the gap. It is catalogued below.

### Deferred work catalog

The next spec author's reading list. Every entry is one an artifact of this cycle actually recorded;
nothing recorded is dropped, and where an item is judged not to be genuine deferred work that is said
with its reason rather than resolved by omission.

- **V5 — `AGENTS.md` rule 31's `pyproject.toml` <-> `__init__.py` pairing has no executable pin.**
  Source: `bld-012-r1-…md` `### Re-derivation of the plan's measurements` (V5) and `### Items for the
  final gate's ### Deferred work catalog`; re-stated in `bld-012-r2-…md` `### 8`.
  Licensing spec line: none, and deliberately so — `docs/SPECS/spec-012-version_release_alignment-0_0_4.md`
  `## Scope`'s closing sentence states the honest limit ("`AGENTS.md` rule 31 carries the … pairing as
  standing **prose** policy; `::test_version` pins the runtime literal alone and no test compares the
  two files") instead of claiming an enforcement the tree lacks.
  Re-derived at this gate (section 7): a bump that edits one file and not the other is caught only if
  the literal in `tests/base/test_init.py::test_version` is edited too. Not a spec-012 defect — the
  card promised agreement at one release and delivered it, verified surface by surface — so writing
  the check into the spec would be this cycle widening a shipped card. **Genuine deferred work**, and
  this card is the closest thing the board has to an owner for it; the smallest honest fix is a test
  that reads `pyproject.toml`'s `[project].version` and compares it to `__version__`.

- **F8 — the unused `[backlog]` link definition, left in place.**
  Source: `bld-012-r1-…md` finding F8 and its `### Spec changes made (Worker 1 only)` row for spec
  line 40; `bld-012-r2-…md` `### 6. F8 confirmed`; the rationale's `### The `[backlog]` link
  definition — recorded, not fixed`.
  Licensing spec line: none; `worker-0.md` `## Closing out a kanban card` is the authority for not
  partial-fixing a pattern that spans surfaces.
  Three definitions of this cycle's making or keeping — `[backlog]` in the spec, plus `[backlog]` and
  `[kanban]` in the rationale companion, both inherited from the shared rationale template — inside
  the board's catalogued population of **71 unused definitions across 23 files**, which
  `KANBAN.md` already assigns to the checker card as a single sweep. Removing only this cycle's three
  would make these two files the exception in a 23-file pattern. **Genuine deferred work**, owned
  elsewhere; if the maintainer prefers the opposite call, deleting three definition lines is the whole
  change.

- **F9's onward reader problem — `CHANGELOG.md`'s `## Versioning` does not say from which release the
  milestone cadence applies.**
  Source: `bld-012-r2-…md` `### 1. F9` and `### 8`; the rationale's `### `## Scope` — the release
  policy `0.0.4` was cut under was rewritten a week later`.
  Licensing spec line: none — the spec deliberately states no policy claim, and the rationale records
  the frame's movement instead (four rejected alternatives, including annotating the `0.0.4` entry).
  `0.0.4` was cut under a header asserting Semantic Versioning adherence; `27ed0b30` (2026-05-15)
  deleted that clause seven days later and added the milestone cadence whose `0.0.x` row says strict
  SemVer does **not** apply — retroactively, and without touching the `0.0.4` entry, which stays
  byte-identical. Nothing in the file marks where the policy changed, so every pre-`27ed0b30` entry
  reads under a policy the file no longer states. `AGENTS.md` rule 21 closes `CHANGELOG.md` to a build
  cycle, and card `TODO-ALPHA-052-0.1.0` already owns the CHANGELOG promotion question. **Genuine
  deferred work**, and already homed on that card.

- **F12's plan wording drift — recorded, and NOT deferred work.**
  Source: `bld-012-r2-…md` `### 4. F12` and `### Notes for Worker 0`; already written into
  `docs/builder/build-012-version_release_alignment-0_0_4.md` `## Corrections to this plan, recorded`.
  Licensing spec line: none.
  The plan's F12 said "no file defines a `[spec-012]` ref-id at all"; four now do
  (`[spec-012-rationale]` in the spec, `[spec-012]` / `[spec-012-card-snapshot]` / `[spec-012-scope]`
  in the companion), **all written by R1 within this cycle**, all resolving to this card. The
  finding's substance is unaffected and is now provable rather than merely observed —
  `git log --all --diff-filter=A -- '*spec-012*'` shows the number never named any other file, so no
  `[spec-011]`-shaped ambiguity cluster exists. **Listed because both artifacts surfaced it, and
  listed as not genuinely deferred: the correction is already in the plan, no file is wrong, and no
  future author owes work on it.** It is carried here only so the sentence is not re-copied from an
  older draft of the plan.

- **The concurrent session's failing row, for the commit reviewer.**
  Source: section 1 above; the same node id `docs/builder/bld-011-final.md` catalogued one cycle ago.
  Licensing spec line: none; it is not this cycle's work at all.
  `tests/rest_framework/test_inputs.py::test_dedupe_serializer_input_shape_is_sole_cache_protocol`
  fails at this tree, and unlike at the prior gate it is now **committed** — introduced by `5851bb59`
  together with the `rest_framework/inputs.py` dedupe-cache work it was written against, with both
  paths clean in the working tree. Catalogued so it is not re-discovered as a mystery, and because its
  status changed between the two gates: it is no longer "uncommitted concurrent work" but a failing
  row on `main`.

Also handed forward, from `bld-012-r2-…md` `### 5. The card body`: **no `KANBAN.md` card-body edit and
no kanban-DB edit is owed for card 12**, verified independently of R1. The card's present-tense
`#### Scope` bullet is the board's normal register for a Done card (23 such bullets), the board states
in its own text that such a row is "correct history on a Done card and is NOT to be edited", and the
card is version-stamped in its id, title, and `Spec:` row. Recorded so a later pass does not re-open
it as an unfixed defect.

### Summary

The gate closes the spec-012 residual-completion cycle. Two items shipped, both Worker 1-only and both
Markdown-only: R1 created the missing rationale companion and reconciled the card-snapshot stub —
cutting the counterfactual boilerplate preamble and `## Planning note` into the rationale, deleting the
drifted board-metadata bullets and the seven-row `## Other` dump outright, and rewriting `## Scope`
into a five-surface enumeration that states alignment as a per-release obligation rather than a
present-tense property. R2 audited the archive, the link scaffold at both depths, the terms CSV against
`import_spec_terms`'s enforced constraints, and the board card, found no defect, and wrote F9 — the
release policy rewritten a week after the cut — into the rationale as a `## Scope`-keyed entry. No
package source and no test was written by either item, which is why floor verification is `none` and
why no integration pass ran.

Every gate command passes except one full-sweep row, which is a concurrent maintainer session's work
and is now **committed at `HEAD`**: the failing test and the module it tests are both clean in this
tree, both arrived in `5851bb59`, and the failure reproduces from a single node id in isolation. It is
recorded, attributed with commands and output, and escalated to the maintainer rather than fixed or
masked.

The cycle's own subject was verified a third time at a moved `HEAD`: all five version surfaces agree,
on `0.0.14`. The spec's invariant holds and its value has moved, which is precisely the reading the
reconciliation was written to make possible.

### Spec changes made (Worker 1 only)

**None.** The spec's status/header lines were re-verified at this spawn per `worker-1.md`
`## Spec status-line re-verification (every Worker 1 spawn)` — the title, `Target release: 0.0.4` per
card `DONE-012-0.0.4`, `Status: shipped — canonical spec stub created to keep the Kanban DB
one-to-one spec invariant intact.`, `Owner: package maintainer.`, and the pointer paragraph naming the
rationale companion all still describe the cycle's current state, and the companion the pointer names
exists on disk. Nothing the gate measured falsified a sentence in either file — section 7 confirms the
`## Scope` contract holds at the current `HEAD`, and section 4 confirms the plan's floor declaration.
No checklist box in either item artifact is left `- [ ]`, so no deferral reason is owed here; the
dispositions decided rather than deferred (F8's "recorded, not fixed", F12's correction, the card
body) are in the catalog above with their reasons.

### Final status

`final-accepted`.

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
