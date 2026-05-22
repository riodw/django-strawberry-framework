# Review feedback: latest commit for `build-018-export_schema-0_0_7`

Commit reviewed: `da08746552d1cef2b4b6d3177f977ad7c9811e7d` (`update agentflow`).

## High

None.

## Medium

### Closeout commit sequencing is internally contradictory

`docs/builder/BUILD.md:585` and `docs/builder/BUILD.md:593` now correctly say the maintainer commits the build artifacts before closeout runs, and closeout depends on the maintainer-provided commit range. But `docs/builder/BUILD.md:601` still says the maintainer commits the retrospective workflow-doc updates “along with the now-completed plan and any `bld-*.md` artifacts kept for the just-finished build.”

That makes the closeout sequence ambiguous: the plan and `bld-*.md` artifacts cannot both be committed before closeout so Worker 0 can scan the commit range, and also be committed after closeout with the workflow-doc retrospective updates. This can lead a future Worker 0 to either run closeout against uncommitted artifacts or hold artifacts out of the build commit, defeating the new commit-range requirement.

Recommended fix: rewrite line 601 so the post-closeout commit contains only the retrospective workflow-doc updates (and any explicitly new closeout artifact, if one exists), while the source changes, completed build plan, and `bld-*.md` artifacts remain part of the pre-closeout maintainer build commit described at line 585.

### Worker 0 closeout precondition still starts too early

`docs/builder/worker-0.md:121` says closeout runs only after the maintainer has committed and supplied the build-cycle commit range, matching `docs/builder/BUILD.md:593`. But the operational closeout checklist begins at `docs/builder/worker-0.md:138` with “After all build-plan checkboxes are complete,” which omits the new commit/range precondition.

Because `worker-0.md` is the role file Worker 0 follows directly, this stale precondition can send Worker 0 into closeout immediately after the final checkbox, before the maintainer commit exists.

Recommended fix: change the `## Closeout job` opening to mirror `BUILD.md`, e.g. “After all build-plan checkboxes are complete, the maintainer has committed the build, and the maintainer has supplied the build-cycle commit range.”

## Low

None.

## What looks solid

- The new no-maintainer-pause rule is clear in both `docs/builder/BUILD.md` and `docs/builder/worker-0.md`: per-slice final verification is the safety net, and Worker 0 should continue through integration and the final gate without waiting for maintainer review.
- `docs/builder/build-018-export_schema-0_0_7.md` itself is already checked complete for all slices, integration, and final gate; the latest commit appropriately focuses on standing workflow docs rather than source/test churn.
