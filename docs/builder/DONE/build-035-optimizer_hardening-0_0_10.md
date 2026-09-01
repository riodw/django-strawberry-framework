# Package build plan: optimizer_hardening / 0.0.10 (035)

Spec source: `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` (already archived)
Target release: `0.0.10` (shipped; this is a **retrospective reconciliation cycle**, not a feature build)
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every slice must justify shared/duplicated patterns before merging.

## Cycle framing (maintainer-directed deviation from the standard build)

The `DONE-035-0.0.10` work **already shipped**. This cycle exists because the spec's
`-rationale.md` companion was never extracted (`BUILD.md` `## Spec rationale extraction`,
pre-flight step 7), and because later cycles moved code the spec cites. The maintainer's
instruction scopes the cycle to:

1. Extract `docs/SPECS/appx/spec-035-optimizer_hardening-0_0_10-rationale.md` from the spec's
   deliberative layer (a MOVE, not a copy).
2. Verify **nothing planned in the spec was dropped or skipped in the code**.
3. Where later work corrected, relocated, or extended what landed, **update the spec to the
   current contract** — stated directly, never as a chronology (`BUILD.md`
   `## Spec rationale extraction`: "the spec never narrates its own history"). The *explanation*
   of every such change goes in the rationale file, not the spec.
4. Confirm the spec is archived at `docs/SPECS/` with its companions in `docs/SPECS/appx/`.

**Scope limit (maintainer):** this cycle touches spec `.md` files and source/test `.py` files
only. No closeout / agentflow edits, no `KANBAN.md` / `docs/GLOSSARY.md` / `CHANGELOG.md` /
`README.md` regeneration, no DB writes.

**Filename rule (maintainer):** every file this cycle creates carries the issue number `035`.
That overrides `BUILD.md` `## Build artifact naming`'s `bld-slice-<N>-<slug>.md` form; artifacts
here are `bld-035-slice-<N>-<slug>.md`.

**Worker dispatch (maintainer):** dispatch Worker 2 / Worker 3 only where the **code** needs a
change. Spec-only reconciliation is Worker 1 alone.

## Pre-flight

Pre-flight: passed on 2026-08-31 with two recorded deviations; baseline: repo-wide dirty from
concurrent sessions, two dirty files inside this cycle's blast radius (below); cleanup:
`worker-memory/` re-seeded empty, `temp-tests/` already empty, `docs/shadow/` left as-is.

| Step | Outcome |
|---|---|
| 1. Working-tree baseline explicit | Repo is broadly dirty from concurrent sessions (`AGENTS.md` 34). Baseline-dirty files inside this cycle's blast radius are listed below. |
| 2. `scripts/review_inspect.py` runs | OK — smoke on `optimizer/walker.py` emitted its overview (24 imports, 37 symbols, 8 hotspots, **2 TODO comments**, 7 repeated literals). |
| 3. Build artifacts reset | **Deviation:** `docs/builder/bld-003-final.md` is a tracked leftover of a prior cycle and is NOT deleted — deleting another session's tracked artifact is the one irreversible pre-flight mistake (`worker-0.md` step 3). Every path this cycle creates is `035`-namespaced and verified absent. |
| 4. `.gitignore` lists scratch paths | OK — `docs/shadow/`, `docs/builder/worker-memory/`, `docs/builder/temp-tests/` all listed. |
| 5. Scratch directories cleared | `worker-memory/` re-seeded with four empty files; `temp-tests/` already empty. **Deviation:** `docs/shadow/current/` is a concurrent session's `bug_hunt.py` output — left untouched. |
| 6. Spec-doc consistency check | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` → `OK: 23 terms`. |
| 7. Spec rationale extracted | **Not yet — this cycle's Slice 1.** Every later dispatch reads the post-extraction spec. |

### Baseline-dirty out-of-scope files (never edit, never revert)

- `examples/fakeshop/test_query/test_library_api.py` — carries a `TODO(spec-035)` anchor this
  cycle would otherwise retarget. **Out of scope; routed to the deferred-work catalog.**
- `tests/types/test_finalizer.py` — unrelated concurrent work.
- Everything else `git status` reports dirty outside this plan's writable lists.

### Concurrent-writable tracked binary / generated files

`examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`, `docs/TREE.md`.
This cycle writes **none** of them; any churn is a concurrent writer's.

## Declarations

**Ownership partition:** none; sequential slices. Slice 2 (Worker 2) is the only pass that
writes `.py` files, and it runs after Slice 1 closes.

| Cohort | Files |
|---|---|
| Slice 1 (Worker 1) | `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md`, `docs/SPECS/appx/spec-035-optimizer_hardening-0_0_10-rationale.md`, `docs/builder/bld-035-slice-1-rationale_extraction.md` |
| Slice 2 (Workers 1/2/3) | `django_strawberry_framework/optimizer/walker.py`, `tests/optimizer/test_walker.py`, `tests/optimizer/test_extension.py`, `tests/types/test_resolvers.py`, `docs/builder/bld-035-slice-2-carry_forward_anchors.md` |
| Slice 3 (Worker 1) | `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md`, `docs/SPECS/appx/spec-035-optimizer_hardening-0_0_10-rationale.md`, `docs/builder/bld-035-slice-3-spec_reconciliation.md` |

#### Partition correction (Worker 0, mid-flight after Slice 2's first review pass)

`tests/types/test_resolvers.py` is **folded into Slice 2's cohort** (`worker-0.md`
`### Ownership partition`: a cohort needing a file it does not own re-partitions rather than
writing outside its scope). Worker 3's review surfaced a Low finding the first partition could
not cover: four shipped `.py` comments cite the spec's `## Edge cases and constraints` bullets
by **raw line number** - an `AGENTS.md` rule 27 violation, and one this cycle's own Slice 1
made definitively wrong by shrinking the spec 542 -> 498 lines. Worker 0 re-derived the
population with an anchor measurement rather than the slice's own token
(`grep -rnoE "edge case[s]? (line )?[0-9]+" --include='*.py' .`), which returns exactly four
occurrences:

Each `pre-fix` phrase in the table below is quoted as plain text, **not** in the `#"..."` pinpoint
grammar, precisely so no citation sweep reads it as a live anchor; Slice 2 replaced all four, so **none of these four anchors resolves at
`HEAD` any more and a citation sweep must not read them as live claims.** (Recorded because the
inverse mistake was made twice inside this cycle: an artifact that pinpoints the very phrase a
catalogued fix is going to rewrite defeats its own anchor - cite the stable neighbourhood, or label
the quote as pre-fix, whenever recording a defect for later repair.)

| Site (pre-fix substring) | Cites | Actual target bullet |
|---|---|---|
| `django_strawberry_framework/optimizer/walker.py::_record_relation_access`, pre-fix `edge case line 315` | line 315 | the every-projection-writer-checks-the-gate bullet |
| `tests/optimizer/test_walker.py::test_subscription_operation_gated`, pre-fix `edge case line 317` | line 317 | the subscriptions-gated-identically bullet |
| `tests/optimizer/test_walker.py::test_enable_only_defaults_enabled_without_info`, pre-fix `edge case line 320` | line 320 | the missing-`info`-defaults-to-enabled bullet |
| `tests/types/test_resolvers.py`, pre-fix `spec-035 edge case 316` | 316 | the consumer-`.only()`-defers-the-FK bullet |

All four were **already off by one or two before this cycle** (the pre-move bullets sat at 316,
318, 322, and 317 respectively), which is the standing lesson that a distance citation cannot
be stopped from regressing - only an anchor one can. `BUILD.md` `### Test staleness a focused
run cannot see` makes a regression the build introduces the build's to fix **in-loop**, so this
routes back through Slice 2 as a Worker 2 apply-changes pass rather than a follow-up.

**Correction (Worker 0, after Slice 2's re-review): the population above was FOUR, not the
whole set - the instrument was fail-open.** `grep -rnoE "edge case[s]? (line )?[0-9]+"` is
**line-oriented**, and a citation wrapped across two source lines does not match it. Worker 3's
whitespace-normalized re-derivation found a **fifth** in-scope site,
`tests/optimizer/test_walker.py::test_mutation_scalar_only_connection_window_no_only
#"spec-035 Decision 4 / edge case"`, whose `line 315` wraps onto the next line. It is already in
the cohort, so no further re-partition is needed. Worker 0 re-derived the finding independently
with a `re.sub(r"\s+", " ", text)` flatten before matching; that is the instrument this cycle
should have used from the start, and the stated "population is zero" in the first apply-changes
report was a false count of exactly the shape `BUILD.md` `## Claims are proven mechanically,
never accepted on prose` grades Medium.

**Out of scope, cataloged not fixed** (re-derived wrap-aware: **seven** occurrences, not six): `tests/optimizer/test_extension.py #"Decision 7 line 346"`
(x2) and `#"Decision 7 line 347"`, three in `tests/mutations/test_sets.py`, and
`tests/optimizer/test_extension.py #"spec line"` (which wraps AND names no spec at all, so it is
invisible to both a line-oriented sweep and a spec-named one) cite *other* specs by line number.
Same defect class, different card; this cycle is spec-035's.

**Hot-path declaration:** none. No slice changes runtime behavior — Slice 2 is comment-text
only (verified by an AST-with-comments-stripped comparison), and Slices 1 and 3 are `.md`.

**Floor-verification scope:** none. No slice touches a Django / Strawberry / channels
integration seam; no runtime line changes.

## Verified code state (Worker 0, before dispatch)

`BUILD.md` `### Worker 0 verifies every finding against source before dispatching`. Every claim
below was re-derived from HEAD-plus-working-tree, not read out of the spec.

**Everything the spec says shipped, shipped. Nothing was dropped.**

| Spec contract | Live site | Verdict |
|---|---|---|
| G1 `_result_cache` early-return, after `normalize_query_source`, before `apply_to` | `optimizer/extension.py::DjangoOptimizerExtension._optimize #"getattr(result, \"_result_cache\", None) is not None"` | **holds** |
| G2 gate derived once at the walker entry | `optimizer/walker.py::_enable_only_for_operation`, called from `optimizer/walker.py::plan_optimizations` | **holds** |
| G2 writer 1 — scalar + Relay-pk appends | `optimizer/walker.py::_walk_selections #"if db_field is not None and enable_only"` and `#"if enable_only:"` | **holds** |
| G2 writer 2 — FK connector columns | `optimizer/walker.py::_record_relation_access #"if enable_only and attname is not None"` | **holds** |
| G2 writer 3 — prefetch connector columns | `optimizer/walker.py::_ensure_connector_only_fields #"if not enable_only:"` | **holds** |
| G2 writer 4 — scalar-only window `.only(...)` | **RELOCATED** → `optimizer/nested_planner.py::_project_scalar_only_window #"if not enable_only:"` | **holds, spec cite stale** |
| Decision 5 elision loaded-check + loud fallback | `types/resolvers.py::_build_fk_id_stub`, `types/resolvers.py::_fk_attname_is_deferred`, `types/resolvers.py #"_FK_ELISION_UNSAFE"`, `types/resolvers.py::forward_resolver #"elision_unsafe = True"` | **holds, mechanism richer than the spec states** |
| All 15 spec-named tests | 4 in `tests/optimizer/test_extension.py`, 9 in `tests/optimizer/test_walker.py`, 2 in `tests/types/test_resolvers.py` | **all present** |
| G3 ships no runtime code | no `type_condition` match against a planning type anywhere | **holds** |

### Deviations later work introduced (spec is stale; code is correct)

1. **`_project_scalar_only_window` moved out of `walker.py`.** Commit `991d5120`
   (2026-07-13, "fix(optimizer): isolate nested planning") relocated it to
   `optimizer/nested_planner.py`. The G2 gate travelled with it intact, and
   `walker.py::_plan_connection_relation` forwards `enable_only` through
   `nested_planner._plan_nested_connection_relation` to the relocated writer. The spec cites
   `walker.py::_project_scalar_only_window` in eight places.
2. **Decision 5 needed a `force_unplanned` strictness bypass the spec does not name.** The
   spec says the stub "falls back loudly … so strictness sees the access". It cannot, on the
   spec's text alone: the relation IS in `planned` (the elision branch recorded it), so
   `_check_n1` short-circuits on the planned key and stays silent. The implementation added a
   keyword-only `force_unplanned` on `types/resolvers.py::_check_n1` that bypasses that
   short-circuit, plus the `_FK_ELISION_UNSAFE` sentinel and the `_fk_attname_is_deferred`
   probe. The contract the spec states is only reachable through that addition.
3. **The G1 live-coverage waiver was reversed.** The spec's Slice 1 test plan declines a live
   test ("adding a permanent fakeshop resolver that models it would put an anti-pattern on the
   example surface purely to host a test"). Later work added exactly that resolver —
   `examples/fakeshop/apps/library/schema.py::Query.all_library_branches_eager_eval` — and the
   live pin `examples/fakeshop/test_query/test_library_api.py::test_library_evaluated_queryset_not_re_executed_over_http`.
   The waiver is now a false statement about the repo.
4. **The G2 live-test handoff was discharged.** The spec records it as an obligation on "the
   first card that adds such a mutation". The `0.0.11` mutations cohort discharged it in
   `examples/fakeshop/test_query/test_products_api.py` (the model flavor and the serializer
   flavor), and `mutations/resolvers.py`, `forms/resolvers.py`, `rest_framework/resolvers.py`
   each cite the G2 gate in their pipeline docstrings.
5. **The carry-forward anchor retarget landed at one of five sites.** After the G3 deferral,
   `optimizer/selections.py` was retargeted to
   `TODO(BACKLOG polymorphic_interface_connections - the abstract-return optimizer entry card)`
   by commit `dd8dc0b3`. The other four sites were missed, and commit `471d4c6b`
   ("drop build-process vocabulary from code comments") then stripped ` Slice 3` from the two
   `walker.py` anchors — which the standing no-process-provenance rule explicitly exempts,
   since `AGENTS.md` L26 requires a staged anchor to name its doc **and slice**. Current state:

   | Site | Anchor today | Correct form |
   |---|---|---|
   | `optimizer/selections.py::included_field_selections` | `TODO(BACKLOG polymorphic_interface_connections …)` | already correct |
   | `optimizer/walker.py::_walk_selections` | `TODO(spec-035)` | retarget to the follow-up card |
   | `optimizer/walker.py::_selected_scalar_names` | `TODO(spec-035)` | retarget to the follow-up card |
   | `tests/optimizer/test_walker.py` | `TODO(spec-035 Slice 3)` | retarget to the follow-up card |
   | `tests/optimizer/test_extension.py` | `TODO(spec-035 Slice 3)` | retarget to the follow-up card |
   | `examples/fakeshop/test_query/test_library_api.py` | `TODO(spec-035)` | **baseline-dirty — out of scope** |

   This is Slice 2's whole content. The spec's own claim of "three `TODO(spec-035 Slice 3)`
   comments … at the inliner, the planning seam, and the second-consumer site" is stale on both
   the count and the form.
6. **Loose citation, unchanged since `0.0.10`.** The spec's Current-state bullet attributes
   `apply_connection_optimization` to `DjangoConnectionField`; it is and always was a
   module-level function in `optimizer/extension.py`, re-exported and called from
   `connection.py`. Not a later drift — a spec imprecision to correct in place.

**No contract-level finding requires a maintainer decision.** Every item above is either a
spec statement falsified by the repo (Worker 1 fixes) or an anchor retarget the deferral
already decided (Worker 2 fixes).

## Artifact list

> **The four per-slice artifacts below were deleted at the maintainer's instruction once the cycle
> closed**, and `bld-035-final.md` was deleted after it too, leaving this plan as the cycle's only
> retained artifact. Every one of them, and every `Sources:` pointer into them elsewhere, is
> recoverable at commit `8c05f7fc` - `git show 8c05f7fc:docs/builder/<name>.md`. They are listed here
> as the cycle's real artifact set, not as live paths. **Everything the final gate's deferred-work
> catalog left open now lives on a card or in `BACKLOG.md`**: `TODO-ALPHA-053-0.0.15` carries the
> unretargeted fifth anchor, `TODO-ALPHA-056-0.0.17` carries the citation-hygiene items (raw
> line-number sites with their addresses inlined, the live-source self-citations, the
> `path::Symbol` qualification register, and the anchor-uniqueness warning case), and `BACKLOG.md`
> `polymorphic_interface_connections` carries R4 plus the live-coverage note.

- `docs/builder/bld-035-slice-1-rationale_extraction.md`
- `docs/builder/bld-035-slice-2-carry_forward_anchors.md`
- `docs/builder/bld-035-slice-3-spec_reconciliation.md`
- `docs/builder/bld-035-integration.md`
- `docs/builder/bld-035-final.md` (deleted after the cycle closed; `git show 8c05f7fc:` recovers it)

## Final report (folded in from `bld-035-final.md`, which was then deleted)

`bld-035-final.md` and the four per-slice artifacts were deleted once the cycle closed, leaving this
file as the cycle's only retained artifact. What follows is everything from the final gate that is
still true and still useful; the process narration is not reproduced. Any of the five is recoverable
verbatim with `git show 8c05f7fc:docs/builder/<name>.md`.

### Outcome

G1, G2 and Decision 5 are verified present and correct in shipped code; **nothing planned in the spec
was dropped**. G3 correctly ships no runtime code -- it was deferred whole, with its design carried
forward. The cycle produced the missing `-rationale.md` companion, reconciled the spec over ten
verified post-ship divergences, retargeted five carry-forward anchors, and changed **zero executable
lines**: every touched `.py` is docstring-blanked-`ast.dump`-identical to its pre-cycle state.

### Gate report

| # | Command | Result |
|---|---|---|
| 1 | `uv run pytest --no-cov` | **PASS** -- `7069 passed, 42 skipped`, exit 0. No `--cov*` flag in any form. |
| 2 | `manage.py check` | **PASS** -- `System check identified no issues (0 silenced).` |
| 3 | `manage.py makemigrations --check --dry-run` | **PASS** -- `No changes detected`. |
| 4 | `ruff format --check .` | **PASS** -- `435 files already formatted`. Read-only, never `--fix`. |
| 5 | `ruff check .` | **PASS** -- `All checks passed!`. Read-only, never `--fix`. |
| 6 | `git diff --check` | **FAIL**, exit 2 -- attributed below, not this cycle's, not blocking. |
| 7 | `check_spec_glossary.py --spec docs/SPECS/spec-035-…md` | **PASS** -- `OK: 23 terms`. Also the spec's own Definition-of-done invocation. |
| 8 | `check_trailing_commas.py --check` over the 2 spec `.md` + 4 cohort `.py` | **PASS**. |
| 9 | The five shipped-`.py` `#"substring"` spec anchors | **PASS** -- all five resolve **exactly once**. |
| 10 | Wrap-aware staged-anchor sweep | **PASS with one expected survivor** -- the baseline-dirty `test_library_api.py` site, carried by `TODO-ALPHA-053-0.0.15`. |

**The one failure, attributed.** `git diff --check` exits 2 on trailing whitespace in added lines of
`docs/feedback.md` (and, at the 2026-09-01 pass, `docs/feedback2.md` as well -- 18 lines between
them). Derived rather than assumed: the file is in no writable list in this plan, no `bld-035-*`
artifact records an edit to it, its added lines are a concurrent session's `spec-050` review dated
2026-08-31, and `git show HEAD:docs/feedback.md` read into a scratch path outside the repo returns a
**0-line** file -- so every flagged line is uncommitted concurrent work. Recorded and escalated, not
fixed and not reverted, per `AGENTS.md` 34. Scoped re-run over the cycle's own surfaces
(`docs/SPECS/`, `django_strawberry_framework/`, `tests/`, `docs/builder/`) is clean.

### Deferred work: final disposition

Twelve catalogued items. Every one is closed in the tree, carried by a card, carried by `BACKLOG.md`,
or recorded below -- nothing is left pointing at a deleted file.

| # | Item | Disposition |
|---|---|---|
| D1 | The fifth carry-forward anchor at `examples/fakeshop/test_query/test_library_api.py:3680` is still `TODO(spec-035)` | **`TODO-ALPHA-053-0.0.15`** -- the only card whose sweep opens that file |
| D2 | The two package test-tree anchors are deletable only once this cycle's successor spec records their file placement | **`BACKLOG.md` `polymorphic_interface_connections` R4**, with both measured legs |
| D3 | `selections.py`'s anchor cited `(R1)` without naming the defining document | **CLOSED** in the tree, 2026-09-01 |
| D4 | Nine raw-line-number citations owned by *other* specs | **`TODO-ALPHA-056-0.0.17`**, with all nine addresses inlined into that item |
| D5 | Twelve live-source `(line NNN)` self-citations + 2 `cookbook line(s)` | **`TODO-ALPHA-056-0.0.17`** as its own item; it had no owner before |
| D6 | The `## Implementation plan` delta-table preamble carries chronology | **Judged, deliberately left** -- see below |
| D7 | The companion's `## Post-ship divergences` mixes two list forms | **Judged, deliberately left** -- see below |
| D8 | `#"defaults to enabled"` is the least distinctive of the five anchors | **`TODO-ALPHA-056-0.0.17`**, as the fourth instance on its anchor-uniqueness item |
| D9 | A companion citation pointed at the `_project_scalar_only_window` alias site | **CLOSED** inside the cycle |
| D10 | `path::Symbol` under-qualification is a repo-wide convention register | **`TODO-ALPHA-056-0.0.17`**, figures re-derived across three citation grammars |
| D11 | Derived counts drifted four times in this cycle | **Recorded below** as a standing rule |
| D12 | A `#"substring"` anchor in `tests/types/test_resolvers.py` did not resolve | **CLOSED** in the tree, 2026-09-01; the class is carried by card 056 |

**D6, kept as a decision rather than a defect.** The spec at `:260` reads "Line deltas were planning
estimates; G1 and G2 have since shipped (Slice 1's are the realized `d1dea2fd` deltas)." That is
chronology by the letter of `BUILD.md` `## Spec rationale extraction`, but it is **not false** and it
does real work: it tells a reader the delta table's last column mixes an estimate with a realized
figure. Left on purpose so a later custodian judges it rather than inherits it. Note the citation is
by line number and the line is long -- a `grep … | cut -c1-220` hides the match past the cut and
makes a present sentence read as absent, which happened once while verifying this very item.

**D7, likewise.** In the rationale companion, `## Post-ship divergences (spec vs. HEAD)` entries 1-7
are numbered list items while 8 and 9 are `### Divergence 8` / `### Divergence 9` subheadings,
because those two carry rejected alternatives and needed the structure. The section preamble says so,
so it is navigable. A tenth entry should either follow the subheading form or normalise all of them.

**D11, the standing rule.** Four derived counts drifted inside this one cycle: a `[nested-planner]`
citation population reported as seven and measured as six; a deferred inventory reported as six and
measured as nine; a raw-line-number population that went zero, six/seven, eight, then nine as the
instrument improved; and a `path::Symbol` figure reported as 17/5 and measured as 15/6. **A count in
an artifact is a claim. Re-measure it, quote the command that produced it, print the population size
the command scanned, and prefer an occurrence list whose entries the next reader can re-derive over a
bare total.** Two instrument shapes caused most of it: a line-oriented grep cannot see a citation
that wraps, and a positively-spelled census is invisible to a negative-vocabulary sweep.

### Two defect shapes worth carrying forward

- **An anchor that quotes the phrase its own catalogued fix will rewrite defeats itself.** Closing D3
  broke a `#"contract (R1). Pseudocode:"` citation in a sibling artifact, and the Slice 2 citation
  fix had already broken `#"spec-035 edge case 316"` in two more places plus a four-row inventory
  table whose every cell was pre-fix text. Four self-inflicted breaks, none visible to
  `scripts/check_citations.py` (it is `path::Symbol`-only and excludes `docs/`). When recording a
  defect for later repair, cite the **stable neighbourhood**, or take the quote out of the `#"..."`
  grammar entirely and label it pre-fix. New anchors must quote text that sits on a **single** source
  line -- a phrase that reads correctly flattened can straddle a comment wrap and resolve zero times.
- **Attribute a failure in a concurrently-dirty tree by AST, not by file list.** `ast.dump` your
  edited file against `HEAD`: identical proves behaviour-neutral by construction, which pins any test
  failure on whichever files are AST-changed and not yours. Compare against the **pre-edit** state,
  not `HEAD`, when the cycle already touched that file, or you mis-attribute your own earlier edit.

### Board state at hand-off

The board DB carries card-053 and card-056 edits that neither `KANBAN.md` nor `KANBAN.html` renders.
They were deliberately not regenerated: both render files held a concurrent session's uncommitted
edits, and regenerating would overwrite that session's in-flight work. **The render is owed to
whoever next wraps the board** -- `scripts/build_kanban_md.py` and `scripts/build_kanban_html.py`,
never a hand-edit.

## Checklist

- [x] Slice 1: Spec rationale extraction (`BUILD.md` pre-flight step 7) — Worker 1 only -> `docs/builder/bld-035-slice-1-rationale_extraction.md`
- [x] Slice 2: Carry-forward anchor retarget (comment-only `.py`) — Workers 1/2/3 -> `docs/builder/bld-035-slice-2-carry_forward_anchors.md`
- [x] Slice 3: Spec reconciliation against the shipped repo — Worker 1 only -> `docs/builder/bld-035-slice-3-spec_reconciliation.md`
- [x] Cross-slice integration pass -> `docs/builder/bld-035-integration.md`
- [x] Final test-run gate -> `docs/builder/bld-035-final.md` (deleted; recover with `git show 8c05f7fc:`)
