# Feedback: Review workflow vs Build workflow comparison

## Structural strengths of Build over Review

### 1. Explicit artifact status state machine

Build's `bld-*.md` artifacts carry a `Status:` line (planned / built / revision-needed / review-accepted / final-accepted) that Worker 0 reads to drive dispatch. Review has no equivalent — the only signal that a cycle item is ready for the next worker is an implicit "artifact exists" or "diff exists" check. This makes Review's dispatch logic harder to automate or audit. Consider adding a `Status:` field to `rev-*.md` artifacts and to the review plan.

### 2. Worker 0 memory file

Build gives Worker 0 its own memory file (`docs/build/worker-memory/worker-0.md`) for progress notes per slice. Review gives Worker 0 no memory file — it only reads the other workers' memory at closeout. A coordination notebook would help Worker 0 track which cycles needed re-spawns, which files produced skip artifacts, and which blockers were raised.

### 3. Final test-run gate

Build closes with `bld-final.md` and a single `uv run pytest` gate to confirm existing tests still pass. Review has no equivalent final gate — it relies on per-cycle validation and the maintainer to catch regressions. A final gate would catch cross-cycle test breakage before closeout.

### 4. Temp test capability for Worker 3

Build lets Worker 3 create gitignored temp tests under `docs/build/temp-tests/<slice>/` during review, with a path-to-promotion workflow (Medium finding → Worker 2 promotes to permanent). Review gives Worker 3 no such tool — verification is limited to diff inspection and running standing tests. This is a meaningful gap for complex fixes.

### 5. DRY-first language and structured analysis

Build places DRY as the first and loudest rule: a prominent `!!IMPORTANT — DRY FIRST!!` block and a mandatory `DRY analysis` section in every plan answering three explicit questions (existing patterns reused, new helpers justified, duplication risk avoided) with file:line citations. Review mentions DRY opportunities throughout but without the same structural requirement. The folder-level repeated-literal check in Review is good but reactive; adding a proactive DRY analysis per artifact would catch duplication before fixes are implemented.

### 6. Namespaced helper output directory

Build requires `--output-dir docs/build/shadow` for every `scripts/review_inspect.py` invocation, keeping build and review shadow artifacts separate. Review uses the default output path (`docs/review/shadow/`), which is fine but means there's no parallel discipline enforced in the docs. Worth explicitly documenting the default behaviour.

## Structural strengths of Review over Build

### 1. More precise static helper trigger rules

Review defines mandatory and skip conditions with concrete thresholds (≥150 lines, any file under `optimizer/` or `types/`, pure-class-definition module skip). Build's rules are looser (e.g. "adds more than ~50 lines of new logic" without the pure-class skip). Consider bringing the threshold precision and skip rules from Review into Build.

### 2. Folder-level repeated-literal check procedure

Review's folder-pass section has a concrete procedure: confirm every overview exists, compare repeated literals across siblings, compare imports for boundary leaks. Build's integration pass lists similar goals but lacks the step-by-step overview-driven procedure. Consider adding a parallel procedure to Build's integration-pass instructions.

### 3. Maintainer checkpoint is more explicit

Review has a numbered maintainer checkpoint (review result → inform Worker 1 → Worker 1 checks full diff → maintainer commits with artifact and plan). Build's maintainer checkpoint is a shorter three-step block. Review's version is stronger for ensuring the reviewer (Worker 1) confirms the fix before the maintainer commits.

## Specific gaps and inconsistencies

### Review gaps (things Review should adopt)

- **No Worker 0 memory file.** Add `docs/review/worker-memory/worker-0.md` seeded at plan time by Worker 0. Contents: per-item progress, re-spawn counts, blockers raised.
- **No final test-run gate.** Add a final pass to the review plan that runs `uv run pytest` once after all checklist items are done, before closeout.
- **No worker status legend.** Add a status legend parallel to `docs/build/worker-0.md` Slice status legend for the review plan. Even if the statuses differ (review has no planning phase), having explicit states clarifies dispatch.
- **Artifact naming collision risk.** Review and Build artifact prefixes (`rev-` and `bld-`) are distinct, but both live under `docs/` subdirectories. If a future workflow adds artifacts under `docs/`, ensure no further prefix collisions.

### Build gaps (things Build should adopt)

- **No pure-class-definition skip rule for the helper.** Review explicitly exempts `exceptions.py`-style modules. Build's helper rules don't include this exemption, which means Worker 3 might run the helper unnecessarily on low-surface new files.
- **No explicit "folder pass reads sibling artifacts first" check.** Review requires Worker 1 to read every sibling `rev-*.md` before the folder pass. Build's integration pass should have a parallel rule but currently says "read all prior `bld-*.md` artifacts needed to understand cross-slice patterns" — less strict and gated by "needed to understand."

### Cross-workflow inconsistencies

- **Worker memory file count.** Build has four (worker-0 through worker-3); Review has three (worker-1 through worker-3). If Worker 0 memory is valuable for Build, it should be present in Review too, or Build should document why Review doesn't need it.
- **BUILD.md says files are "tracked"; REVIEW.md doesn't make this explicit.** REVIEW.md says artifacts "are committed" and the plan "is kept in git" but doesn't have the explicit "Permanent workflow files … are tracked" sentence that BUILD.md has. This is minor but inconsistent.
- **Workers 2 and 3 can be combined in Review but not Build.** REVIEW.md: "When a review artifact has no High-severity issues, Worker 2 and Worker 3 may be the same agent invocation if the maintainer explicitly chooses." BUILD.md has no equivalent provision. If the isolation guarantee is load-bearing, both workflows should be consistent on when it can be waived.

## Summary

The Build workflow is a more mature evolution of the review pattern. It adds explicit state management, structured DRY analysis, a final test gate, and temp-test capability. The Review workflow has stronger per-fold helper trigger rules and a more detailed maintainer checkpoint. Most gaps run one direction: Review should adopt several Build improvements (status fields, Worker 0 memory, final gate, temp tests for Worker 3). Build should backport Review's helper skip rules and more explicit folder/integration-pass prerequisites.