# HUNT
Generate a bug-hunt checklist for `django_strawberry_framework`
in two steps.

## Step 1: distill the current dicta
Read every `docs/review/worker-*.md` brief and distill the recurring
pitfalls, severity-calibration notes, and review-order priorities into
one markdown block specific to this package.

Save the distilled markdown to `docs/bug_hunt/dicta.md`. This file is
the input parameter for Step 2.

## Step 2: generate the checklist

Then run `scripts/bug_hunt.py`. The script:
- Resolves the current branch's HEAD commit hash first.
- Wipes `docs/shadow/bug_hunt/current/` and refreshes it in-process by running
  `scripts/review_current_from_commit.py <head-sha>` (same package-dir
  default, or the `--package-dir` value you passed through).

- Reads `docs/bug_hunt/dicta.md` and prepends it as the header.
- Appends a static "how to review a single file" section baked into
  the script itself.
- Enumerates every `*.stripped.py` under `docs/shadow/bug_hunt/current/`,
  derives the matching original source path from each stem, and emits
  one checkbox + prompt block per file.
- Writes the result to `docs/bug_hunt/bug_hunt.<short-sha>.md`, where
  `<short-sha>` is the short hash of the same HEAD commit it refreshed
  from.

## How to use the generated checklist
Open `docs/bug_hunt/bug_hunt.<short-sha>.md` and feed the per-file
prompts into the model one at a time. Tick the checkbox for each file
as you finish its pass.
