# HUNT
Generate a bug-hunt checklist for `django_strawberry_framework` in
two steps, then execute it one file at a time with a hunter agent.
The generator prepares the input; the hunter does the probing. Expect
scratch files and live-code probes as part of the search; those aren't
artifacts to keep.

The per-file prompt each hunter receives is the static "how to review a
single file" block baked into `scripts/bug_hunt.py`. To tune the hunter's
behavior, edit that script — HUNT.md is just orchestration.

## Step 1: distill the current dicta
Read every `docs/review/worker-*.md` brief and distill the recurring
pitfalls, severity-calibration notes, and review-order priorities into
one markdown block specific to this package.

Frame each pitfall as a **probing question** the hunter should ask
while reading a file ("does this branch handle the None case?") rather
than a verification rule ("this branch must handle the None case").
Bias the hunter toward exploration, not checklist confirmation. Include
severity calibration as priorities, not gates — the hunter decides
what to escalate.

Save the distilled markdown to `docs/bug_hunt/dicta.md`. This file is
the input parameter for Step 2.

## Step 2: generate the checklist

Then run `scripts/bug_hunt.py`. The script:
- Resolves the current branch's HEAD commit hash first.
- Wipes `docs/shadow/` and refreshes it in-process by running
  `scripts/review_historical_package_snapshot_at_commit.py <head-sha>` (same package-dir
  default, or the `--package-dir` value you passed through). The wipe is
  recursive — any prior review/build helper output and any
  `docs/shadow/bug_hunt/{old,new,diff}/` from a previous
  `scripts/review_changed_python_diffs_against_head.py` run is discarded.

- Reads `docs/bug_hunt/dicta.md` and prepends it as the header.
- Appends a static "how to review a single file" section baked into
  the script itself.
- Enumerates every `*.stripped.py` under `docs/shadow/`,
  derives the matching original source path from each stem, and emits
  one checkbox + prompt block per file.
- Writes the result to `docs/bug_hunt/bug_hunt.<short-sha>.md`, where
  `<short-sha>` is the short hash of the same HEAD commit it refreshed
  from.

## How to use the generated checklist
Open `docs/bug_hunt/bug_hunt.<short-sha>.md` and feed the per-file
prompts into hunter agents one at a time. For a Warp subagent run,
point the agent at `docs/bug_hunt/dicta.md`, include exactly the
current item's `Prompt:` text, and tell it to work from the repo root.

Keep checklist ownership with the orchestrator, not the hunter:
- The hunter may edit the source file named by the prompt.
- Scratch probes should stay outside the repo, or be removed before
  handoff if they must be created inside the working tree.
- The hunter should not edit `docs/bug_hunt/bug_hunt.<short-sha>.md`.
- The hunter should not commit.
- If the hunter edits code, it should run the required ruff commands
  for the touched source file and report what passed.

After the hunter reports done, write a concise `Result:` line under the
matching checklist item and tick that item. "No issues" is a valid
finding, but it should still be recorded explicitly in the generated
checklist. Per-file `docs/bug_hunt/hunt-<flat-path>.md` notes are
optional handoff scratch, not the canonical completion record.
