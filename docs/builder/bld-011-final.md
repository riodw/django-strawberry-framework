# Build: Final test-run gate — stale_placeholder_cleanup / 0.0.4 (011)

Spec reference: `docs/SPECS/spec-011-stale_placeholder_cleanup-0_0_4.md` (whole file, 53 lines) and its
companion `docs/SPECS/appx/spec-011-stale_placeholder_cleanup-0_0_4-rationale.md`
Plan reference: `docs/builder/build-011-stale_placeholder_cleanup-0_0_4.md` `## Checklist`, final row
Predecessor artifacts (all `final-accepted`, all read in full before this gate ran):
`docs/builder/bld-011-r1-rationale_and_spec_reconciliation.md`,
`docs/builder/bld-011-r2-doc_completion_archive_audit.md`,
`docs/builder/bld-011-r3-kanban_card_body.md`
Status: final-accepted

## Plan (Worker 1)

The gate is `docs/builder/BUILD.md` `## Final test-run gate` run verbatim, plus the two obligations
the plan's `## Artifact list` folded in from the integration pass this cycle does not run (no source
landed, so there is no cross-slice DRY surface): the staged-anchor sweep, and a full read of every
closed artifact. No new work is planned here; the gate measures, records, and attributes.

### Dispatched findings checklist

- [x] Full sweep — `uv run pytest --no-cov`, no `--cov*` flag anywhere in this pass.
- [x] Django consistency — `manage.py check` and `makemigrations --check --dry-run`.
- [x] Lint / format / diff, all read-only — `ruff format --check .`, `ruff check .`, `git diff --check`.
- [x] Floor verification — scope `none`, recorded with its reason; no floor venv built.
- [x] Staged-anchor sweep folded in from the integration pass.
- [x] Every closed artifact (R1, R2, R3) read in full.
- [x] `### Deferred work catalog` assembled from all three artifacts.

---

## Final verification (Worker 1)

Baseline at gate time: `HEAD` = `054de9dd37a2c4181fb2a91ded57f4823a1b5220`,
`git status --porcelain | wc -l` -> **142**. This cycle's own diff is exactly four tracked paths plus
its untracked artifacts and one untracked new file:

| Path | State | Owner |
|---|---|---|
| `docs/SPECS/spec-011-stale_placeholder_cleanup-0_0_4.md` | `M` | R1 |
| `docs/SPECS/appx/spec-011-stale_placeholder_cleanup-0_0_4-rationale.md` | `??` (new) | R1 |
| `examples/fakeshop/db.sqlite3` | `M` | R3 |
| `KANBAN.md` | `M` | R3 |
| `KANBAN.html` | `M` | R3 |
| `docs/builder/bld-011-*.md`, `build-011-*.md` | `??` | this cycle |

Everything else in the 142 is two concurrent maintainer sessions' work (package sources, tests,
`docs/SPECS/spec-009*` / `spec-010*` and their companions, `docs/dry/`, `docs/shadow/`,
`docs/review/`, and the `bld-009-*` / `bld-010-*` / `build-009-*` / `build-010-*` artifacts).
**None was edited, reverted, staged, stashed, or `git checkout`ed** (`AGENTS.md` rule 34,
`START.md` `## Concurrent sessions`). Nothing was committed and no branch was created or switched.

### 1. Full sweep — `uv run pytest --no-cov`

**FAIL — one row, and this cycle did not cause it. Attributed below and escalated to the maintainer;
not fixed here, and not masked.**

```
1 failed, 5720 passed, 40 skipped in 74.19s (0:01:14)
FAILED tests/rest_framework/test_inputs.py::test_dedupe_serializer_input_shape_is_sole_cache_protocol
```

The failing assertion is `assert shape_a == shape_b` at `tests/rest_framework/test_inputs.py:658`,
differing on `SerializerInputShape.serializer_class` — two distinct class objects both named
`tests.rest_framework.test_inputs._item_serializer.<locals>.ItemSer`, i.e. the dedupe cache did not
return the same shape for two builds of an equivalent serializer.

**Attribution, with evidence rather than assertion** (`docs/builder/BUILD.md`
`## Claims are proven mechanically, never accepted on prose`):

- **The failing test does not exist at `HEAD`.**
  `git show HEAD:tests/rest_framework/test_inputs.py | grep -c "def test_dedupe_serializer_input_shape_is_sole_cache_protocol"`
  -> **0**. It is introduced by the working tree's uncommitted diff:
  `git diff -- tests/rest_framework/test_inputs.py` contains
  `+def test_dedupe_serializer_input_shape_is_sole_cache_protocol():`.
- **It is paired with an uncommitted rewrite of the production module it tests.**
  `git diff --stat` -> `django_strawberry_framework/rest_framework/inputs.py` **+44 / -12** and
  `tests/rest_framework/test_inputs.py` **+27**. Both files carry today's `17:55` mtime, inside the
  concurrent sessions' window, and both are on the plan's baseline-dirty out-of-scope list.
- **It is not order-dependent, so it is not an artifact of the full-sweep interleaving.** Re-run
  focused: `uv run pytest tests/rest_framework/test_inputs.py::test_dedupe_serializer_input_shape_is_sole_cache_protocol --no-cov`
  -> `1 failed in 1.96s`, same assertion.
- **This cycle wrote no package source and no test at all.** Its entire diff is the five paths in the
  table above. Neither `rest_framework/inputs.py` nor `tests/rest_framework/` is in any item's
  writable set, and no item of this cycle can own the fix.

**Escalated to the maintainer**, who is the only party able to run a clean `HEAD` tree
(`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`, "Pre-existing at
HEAD"). This is the strictly stronger case than a pre-existing-at-HEAD claim: the failing row is not
at `HEAD` in any form, so the concurrent session's in-flight serializer-input dedupe work is the
whole population of the failure. No re-loop is dispatched, because re-looping routes work to an item
of this cycle and every one of them is closed, correct, and unrelated.

**Gate disposition.** `final-accepted` is set on the strength of the attribution, not in spite of the
failure: the plan's `## Baseline-dirty out-of-scope files` is the recorded pre-flight baseline
exception, this cycle's four tracked paths are all Markdown, generated documents, and the kanban
database, and no output of this cycle is executed by the suite. Recording plus escalating is what
discharges the obligation; masking it or "fixing" another session's uncommitted work would violate
`AGENTS.md` rule 34.

### 2. Django consistency checks

| Command | Result |
|---|---|
| `uv run python examples/fakeshop/manage.py check` | **PASS** — `System check identified no issues (0 silenced).`, exit 0 |
| `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | **PASS** — `No changes detected`, exit 0 |

The second is the one that matters most for this cycle: R3 wrote three kanban rows through the ORM,
and a clean `makemigrations --check` confirms the write introduced no model drift.

### 3. Lint / format / diff gate — read-only, never `--fix`

| Command | Result |
|---|---|
| `uv run ruff format --check .` | **PASS** — `419 files already formatted`, exit 0 |
| `uv run ruff check .` | **PASS** — `All checks passed!` |
| `git diff --check` | **PASS** — no output, exit 0 |

All three are green across the **whole** tree, concurrent sessions' files included, so no pre-existing
lint exception needs attributing. `ruff format --check` emits a standing `COM812` conflict warning on
stderr; it is a configuration advisory, not a failure, and exit 0 is the reading.

### 4. Floor verification

**Scope `none`, as declared, and no floor venv was built.**
`docs/builder/build-011-stale_placeholder_cleanup-0_0_4.md` preamble declares
"Floor-verification scope: **none.** No item touches a Django / Strawberry / channels integration seam
— no item touches executable code at all", and each item's artifact re-declares it (R1 and R2:
Markdown only; R3: `Not applicable; plan declares floor-verification scope none.`).

The declaration re-derives at this working tree: the cycle's four tracked paths are two Markdown
files, two generated documents, and a SQLite database. No request/response handling, ASGI plumbing,
body parsing, session/auth surface, queryset or expression compilation, schema construction, or
consumer/middleware wiring is touched, and `docs/builder/BUILD.md` `### When it is required` names
"KANBAN / glossary regeneration" as an explicit `none` case. A floor venv would have nothing
version-sensitive to execute. The shared `.venv` was not mutated by any pass of this cycle.

### 5. Staged-anchor sweep (folded in from the integration pass)

```shell
grep -rEn 'TODO\(spec-011|TODO-(ALPHA|BETA|STABLE)-011' . \
  --exclude=KANBAN.md --exclude=KANBAN.html --exclude=BACKLOG.md
```

**Two hits, both false positives, zero surviving anchors.** Both are in
`docs/builder/bld-011-r2-doc_completion_archive_audit.md` (lines 196 and 350), where R2 quotes the
sweep command `` `TODO(spec-011` `` inside its own verification record. Neither is an anchor: no
package source, test, comment, or standing doc carries one. This corroborates R2's independently-run
`grep -rn 'TODO(spec-011'` -> **0**. Card `DONE-011-0.0.4` shipped at `0.0.4` and its staged anchors
were deleted in `118f71a1`, the commit that shipped it. No finding, so nothing is routed to an item.

### 6. Every closed artifact read

R1, R2, and R3 were each read end to end before this gate was written, per
`docs/builder/BUILD.md` `## Cross-slice integration pass` step 1 (the one integration obligation that
survives when a cycle lands no source). The read is what the `### Deferred work catalog` below is
assembled from, and it is also what surfaced R3's Low finding for pass-A correction.

**No `bld-integration.md` exists, deliberately.** The plan's `## Artifact list` records the
disposition and the reason: the integration pass scans landed source for cross-slice duplication and
this cycle lands none, so its shadow-overview comparisons (steps 2-4) have no input. Its two live
obligations are discharged in sections 5 and 6 above. Same disposition, and the same reason, as the
spec-003 and spec-010 cycles.

### Deferred work catalog

The next spec author's reading list. Every entry is one an artifact of this cycle actually recorded;
nothing is invented, and nothing recorded is dropped.

- **F11 — the `[spec-011]` ref-id ambiguity, and it reaches package source.**
  Source: `bld-011-r2-doc_completion_archive_audit.md` `### 4. F11 — the `[spec-011]` ref-id cluster,
  measured`, corroborated in `bld-011-r1-…md` `### Notes for the deferred-work catalog`.
  Licensing spec line: none — this is repo-wide reference hygiene, outside
  `docs/SPECS/spec-011-stale_placeholder_cleanup-0_0_4.md` `## Scope`.
  The token `spec-011` occurs **99 times in 17 files**; excluding this cycle's own files the standing
  population is **43 occurrences across 13 files**. Most mean the *pre-renumber* `spec-011`, which is
  today `docs/SPECS/spec-015-relay_interfaces-0_0_5.md` — including six occurrences in **package
  source and tests** (`django_strawberry_framework/types/base.py` x5,
  `django_strawberry_framework/types/resolvers.py`, plus `tests/types/test_base.py` and
  `tests/filters/test_sets.py`), whose quoted substrings provably resolve to spec-015 Decisions 4, 7,
  and 9. Two files define `[spec-011]` pointing at **this** card while their prose means the relay
  spec: `docs/SPECS/spec-032-full_relay-0_0_9.md` and
  `docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md`. Not partial-fixed, because
  correcting only the file this cycle owns leaves the cluster divergently rather than uniformly wrong.
  It is the only catalog entry that reaches package source.

- **F8 widened — unused `[backlog]` link definitions, and the 71-definition pattern they belong to.**
  Source: `bld-011-r1-…md` `### Spec changes made (Worker 1 only)` (the `[backlog]` kept-deliberately
  bullet) and `bld-011-r2-…md` `#### F8 widened — unused link definitions`.
  Licensing spec line: none; `worker-0.md` `## Closing out a kanban card` is the authority for not
  partial-fixing a cross-surface pattern.
  **Eight** archived specs carry an unused `[backlog]` definition — `spec-011`, `spec-012`, `spec-013`,
  `spec-016`, `spec-024`, `spec-026`, `spec-036`, `spec-054` — and that is one ref-id of a wider
  pattern: **23 files carry 71 link definitions no body reference uses** (largest: `KANBAN.md` 28,
  DB-generated; `spec-051` 6; `spec-050` and `spec-054` 5 each; `CHANGELOG.md` 5). Invisible to both
  checkers — `check_trailing_commas.py` enforces only the header scaffold and `check_spec_glossary.py`
  only glossary terms — so a sweep needs a new check or a one-off script, which is itself the argument
  for doing it once. This cycle's own rationale companion contributes two (`[backlog]`, `[kanban]`),
  left in place so it is not the single exception in a 23-file pattern; if the maintainer prefers the
  opposite call, deleting two lines from the companion is the whole change.

- **Five archived stubs still carrying the boilerplate preamble.**
  Source: `bld-011-r1-…md` `### Notes for the deferred-work catalog`, re-measured in `bld-011-r2-…md`
  `#### Archived stubs still carrying the boilerplate preamble`.
  Licensing spec line: none — each awaits its own residual cycle.
  `spec-012`, `spec-013`, `spec-016`, `spec-024`, `spec-026` still open with the "This file is
  intentionally lightweight … expand it into the full builder-format spec" paragraph, whose
  instruction the release falsified. Five of the seven spec-007 measured; spec-007 and spec-011 are
  the two whose residual cycles have run. Named so the next author does not have to grep.

- **Two figures in the build plan that did not reproduce — do not re-copy them.**
  Source: `bld-011-r1-…md` `### Evidence re-derived at this working tree`, carried in
  `bld-011-r2-…md` `#### The plan's two corrected figures`; both are already corrected in
  `docs/builder/build-011-stale_placeholder_cleanup-0_0_4.md` `## Corrections to this plan, recorded`.
  Licensing spec line: none.
  (a) F8's "fifteen archived stubs" is **eight**. (b) `a357c68c`'s replacement siblings are **18**
  added `def test_` lines in `tests/types/test_definition_order.py`, not "six". Both were cheap to
  measure and both were wrong, which is the reason they are catalogued rather than quietly fixed.

- **R3's declined optional sub-check — `#### Files likely touched` names three of five files.**
  Source: `bld-011-r3-kanban_card_body.md` `#### Sub-check 3 — decided: **not** planned in, and why`,
  raised as "minor and optional" in `bld-011-r2-…md` `### Generated-doc edits reported, not made`.
  Licensing spec line: `docs/SPECS/spec-011-stale_placeholder_cleanup-0_0_4.md` `## Scope`, which
  names all five files by `path::QualifiedName` and is where the fact is already checkable.
  The board's `#### Files likely touched` lists only the three replacement modules and never
  `tests/types/test_base.py` or `tests/optimizer/test_extension.py`, the two files the placeholders
  were removed **from**. Declined because "likely touched" is a planning-time prediction field and
  back-filling it with post-hoc knowledge makes the board assert a prediction nobody made — the
  duplicate-row defect running in reverse. **Reversal recipe, if the maintainer prefers board
  fidelity:** append two `append_card_item`-shaped rows at `order` 3 and 4 in section
  `files_touched` for card 11 through the Django ORM, then regenerate `KANBAN.md` and `KANBAN.html`
  — nothing else changes.

- **The concurrent session's failing row, for the commit reviewer.**
  Source: section 1 above.
  Licensing spec line: none; it is not this cycle's work at all.
  `tests/rest_framework/test_inputs.py::test_dedupe_serializer_input_shape_is_sole_cache_protocol`
  fails at this tree and does not exist at `HEAD`; it belongs with the uncommitted
  `django_strawberry_framework/rest_framework/inputs.py` change it was written against. Catalogued so
  it is not re-discovered as a mystery by whoever runs the suite next.

Also handed forward, from `bld-011-r3-…md` `### Notes for Worker 1 (spec reconciliation)`: the
semantic delta of `examples/fakeshop/db.sqlite3` is a **12-line `.dump` diff**, not the opaque binary
`git diff`, and that dump is what a reviewer of the eventual commit should be handed.

### Summary

The gate closes the spec-011 residual-completion cycle. Three items shipped: R1 created the missing
rationale companion and rewrote the card-snapshot stub into a contract that names all three retired
placeholders and the tests pinning their subjects; R2 audited the archive, the terms CSV, and the
durable docs, and reported — correctly, rather than hand-editing — two DB-backed defects in the board
card; R3 fixed those in the kanban database through the ORM and regenerated both rendered documents.
No package source and no test was written by any item, which is why floor verification is `none` and
why no integration pass ran.

Every gate command passes except one full-sweep row, which is a concurrent maintainer session's
in-flight work: the failing test does not exist at `HEAD`, arrives with an uncommitted rewrite of the
module it tests, and fails identically in isolation. It is recorded, attributed with commands and
output, and escalated to the maintainer rather than fixed or masked.

### Spec changes made (Worker 1 only)

**None.** The spec's status/header lines were re-verified at this spawn per `worker-1.md`
`## Spec status-line re-verification (every Worker 1 spawn)` — title, target release `0.0.4` per card
`DONE-011-0.0.4`, `Status: shipped`, owner, and the rationale-companion pointer all still describe the
cycle's current state — and nothing the gate measured falsified a sentence in either file. No
checklist box in any of the three item artifacts is left `- [ ]`, so no deferral reason is owed here;
the one decided disposition (R3's sub-check 3) is in the catalog above with its reversal recipe.

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
