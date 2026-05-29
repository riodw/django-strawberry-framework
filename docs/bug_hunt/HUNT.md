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
- Refreshes `docs/shadow/current/` in-process by running
  `scripts/review_historical_package_snapshot_at_commit.py <head-sha>` (same package-dir
  default, or the `--package-dir` value you passed through). Only that one
  folder is cleared and rewritten — the diff helper's sibling
  `docs/shadow/{old,new,diff}/` from a previous
  `scripts/review_changed_python_diffs_against_head.py` run is left
  untouched (each script owns and clears only its own folder under
  `docs/shadow/`).

- Reads `docs/bug_hunt/dicta.md` and prepends it as the header.
- Appends a static "how to review a single file" section baked into
  the script itself.
- Enumerates every `*.stripped.py` under `docs/shadow/current/`,
  derives the matching original source path from each stem, and emits
  one checkbox + prompt block per file.
- Writes the result to `docs/bug_hunt/bug_hunt.<short-sha>.md`, where
  `<short-sha>` is the short hash of the same HEAD commit it refreshed
  from.

Once `docs/bug_hunt/bug_hunt.<short-sha>.md` exists for an in-progress
hunt, keep using that same file as the canonical record unless the
maintainer explicitly asks to regenerate or restart the hunt. Do not
regenerate it just because later commits or working-tree changes appear
while the hunt is in progress.

## Step 3: run the next hunter
Open `docs/bug_hunt/bug_hunt.<short-sha>.md` and find the first
unchecked `- [ ]` source-file item. That item is the next unit of work.
Do not batch several file prompts together unless the maintainer
explicitly changes the hunt mode; the default hunt is one fresh hunter
for one file.

Git is off limits to agents in this workflow. Worker 0 and hunters do
not run `git` commands of any kind while executing Steps 3 and 4. The
only allowed git interaction is whatever `scripts/bug_hunt.py` performs
internally during Step 2.

Worker 0 owns the generated checklist. The hunter owns only the source
file named by the current prompt:
- Worker 0 copies exactly that item's `Prompt:` text into the hunter
  dispatch.
- Worker 0 points the hunter at `docs/bug_hunt/dicta.md` and tells it
  to work from the repo root.
- Worker 0 tells the hunter not to edit
  `docs/bug_hunt/bug_hunt.<short-sha>.md`, not to edit
  `docs/bug_hunt/dicta.md`, and not to run any git commands whatsoever.
  `git status`, `git diff`, `git log`, branch creation, branch
  switching, checkout, commit, push, stash, merge, rebase, and similar
  VCS commands are all off limits.
- The hunter may edit only the source file named by the prompt. For a
  confirmed High-severity defect, the hunter may also add or update the
  permanent test that pins the corrected behavior.
- If the fix needs sibling source changes, public API changes, or spec
  reconciliation, the hunter reports that as a blocker/question instead
  of widening the diff unilaterally.
- Scratch probes should stay outside the repo, or be removed before
  handoff if they must be created inside the working tree.
- If the hunter edits code, it runs `uv run ruff format <file>` and
  `uv run ruff check <file>` for each touched source file and reports
  both outcomes.

The hunter's completion report must include:
- Target source file.
- Result: `No issues`, `Fixed <severity>`, or `Blocked`.
- Confirmed defect summary and severity, if any.
- Files changed.
- Validation commands and outcomes.
- Confirmation that no git commands were run, and that no branch
  switch, branch creation, commit, or push occurred.
- Any scratch files created and removed.

## Step 4: record the result, then advance
After the hunter reports done, Worker 0 reviews the report and the
contents of any touched source/test files for scope. Worker 0 does not
run git commands while reviewing; if unrelated workspace movement or
other VCS activity is suspected, Worker 0 stops and asks the maintainer
instead of investigating with git. Then Worker 0 updates only the matching
checklist item in `docs/bug_hunt/bug_hunt.<short-sha>.md`:
- If the hunter completed the file, change the checkbox to `- [x]`.
- Add a concise nested `Result:` line under the item. `No issues` is a
  valid result and must still be recorded explicitly.
- Use a stable format: `Result: <outcome>. Files changed: <...>;
  validation: <...>.`
- For a fix, include severity, changed files, and validation in the
  `Result:` line.
- For a blocker, leave the checkbox unchecked, add a nested `Blocked:`
  line, and stop or ask the maintainer before retrying that item.

Example result lines:
- `Result: No issues. Files changed: none; validation: <commands/results>.`
- `Result: Fixed Medium. Files changed: django_strawberry_framework/filters/sets.py;
  validation: uv run ruff format ... pass, uv run ruff check ... pass.`
- `Blocked: Fix requires sibling changes outside the prompted file.`

Then repeat Step 3 for the next unchecked source-file item. The
generated checklist is the canonical completion record for the hunt.
Per-file `docs/bug_hunt/hunt-<flat-path>.md` notes are optional
handoff scratch only; they do not replace the `Result:` line.

When no unchecked items remain, Worker 0 gives the maintainer a short
closeout summary of fixes, blockers, and files left dirty. Worker 0 does
not commit.
