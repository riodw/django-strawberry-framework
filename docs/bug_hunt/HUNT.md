# HUNT
Generate a bug-hunt checklist for `django_strawberry_framework` in
two steps. The checklist is fed to Gemini 3.1 Pro (via Antigravity),
which acts as the bug hunter — Claude prepares the input; Gemini does
the hunting. Expect scratch files and live-code probes as part of
the search; those aren't artifacts to keep.

The per-file prompt Gemini receives is the static "how to review a
single file" block baked into `scripts/bug_hunt.py`. To tune Gemini's
behavior, edit that script — HUNT.md is just orchestration.

## Step 1: distill the current dicta
Read every `docs/review/worker-*.md` brief and distill the recurring
pitfalls, severity-calibration notes, and review-order priorities into
one markdown block specific to this package.

Frame each pitfall as a **probing question** the hunter should ask
while reading a file ("does this branch handle the None case?") rather
than a verification rule ("this branch must handle the None case").
Bias Gemini toward exploration, not checklist confirmation. Include
severity calibration as priorities, not gates — the hunter decides
what to escalate.

Save the distilled markdown to `docs/bug_hunt/dicta.md`. This file is
the input parameter for Step 2.

## Step 2: generate the checklist

Then run `scripts/bug_hunt.py`. The script:
- Resolves the current branch's HEAD commit hash first.
- Wipes `docs/shadow/` and refreshes it in-process by running
  `scripts/review_current_from_commit.py <head-sha>` (same package-dir
  default, or the `--package-dir` value you passed through). The wipe is
  recursive — any prior review/build helper output and any
  `docs/shadow/bug_hunt/{old,new,diff}/` from a previous
  `scripts/review_diff_from_commit.py` run is discarded.

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
prompts into Gemini one at a time. Gemini writes its findings to
`docs/bug_hunt/hunt-<flat-path>.md`, mirroring the review workflow's
`rev-<flat-path>.md` convention (`/` in the source path becomes `__`
in the file name; e.g.
`django_strawberry_framework/optimizer/walker.py` →
`docs/bug_hunt/hunt-optimizer__walker.md`). Every per-file pass
writes a hunt note, even when nothing is found — "no issues" is a
valid finding. Tick the checkbox after the note lands on disk.
