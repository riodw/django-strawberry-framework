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

- `docs/builder/bld-035-slice-1-rationale_extraction.md`
- `docs/builder/bld-035-slice-2-carry_forward_anchors.md`
- `docs/builder/bld-035-slice-3-spec_reconciliation.md`
- `docs/builder/bld-035-integration.md`
- `docs/builder/bld-035-final.md`

## Checklist

- [x] Slice 1: Spec rationale extraction (`BUILD.md` pre-flight step 7) — Worker 1 only -> `docs/builder/bld-035-slice-1-rationale_extraction.md`
- [x] Slice 2: Carry-forward anchor retarget (comment-only `.py`) — Workers 1/2/3 -> `docs/builder/bld-035-slice-2-carry_forward_anchors.md`
- [x] Slice 3: Spec reconciliation against the shipped repo — Worker 1 only -> `docs/builder/bld-035-slice-3-spec_reconciliation.md`
- [x] Cross-slice integration pass -> `docs/builder/bld-035-integration.md`
- [x] Final test-run gate -> `docs/builder/bld-035-final.md`
