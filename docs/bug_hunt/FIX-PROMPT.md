# Fix loop prompt

Rio starts this with `Execute docs/bug_hunt/FIX-PROMPT.md`. Everything below is addressed to the session that runs it.

You are the coordinator of the tracker fix loop in this repository. Rio is not watching; run until the work is done.

## Before anything else

1. Read, in full: [AGENTS.md][agents], [START.md][start], [GOAL.md][goal], [CLAUDE.md][claude-md], [README.md][readme],
   [TODAY.md][today], [docs/README.md][docs-readme] and [docs/TREE.md][tree]. They are the law and the context for
   every decision you make.
2. Read [FIX.md][fix] (the process) and the tracker [bug_hunt-0_0_15_2.md][tracker] (the items).
3. Create the gate script from FIX.md in your scratchpad, and check `git status` and `git log -1` on main.

## The loop

Run FIX.md's nine phases for one item, then the next item, until no unchecked item is left in the three "To do"
sections. Finish each phase completely, with every agent it dispatched reported back, before starting the next
phase. Finish each item (landed, ticked as not a defect, or parked under "Waiting on you") before starting the next
item. Never run two items at once. After each item, print three lines in chat and continue without waiting.

## What starting this prompt authorizes

- Dispatching the agent types FIX.md names, and the targeted, gated test runs FIX.md lists for them (never the full
  suite).
- Writing the shared checkout only at landing: applying a verified diff, and the item's two commits (the fix, then
  the tracker update). No `Co-Authored-By` or other attribution footer (AGENTS rule 33), no push, no branches, no
  stash, no CHANGELOG edit.
- Deciding open questions that AGENTS.md, START.md or GOAL.md settle. A question they do not settle that changes a
  public contract is Rio's: park it under "Waiting on you" with the evidence and move on.

## When to stop early

- The shared checkout has uncommitted changes in a path your landing diff touches, or `HEAD` moved under a path
  you changed: re-clone at the new `HEAD`, re-apply, rerun the targeted tests; if it still conflicts, park the item.
- The verifier blocks twice on the same item: park it with both reports.
- Something only Rio can do (Postgres or sharded cells not yet authorized, a credential, a branch): park the item
  and continue with the next one.
- No unchecked items left: print the final summary (every item: landed with hashes, not a defect, or parked with its
  question) and stop.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[claude-md]: ../../CLAUDE.md
[goal]: ../../GOAL.md
[readme]: ../../README.md
[start]: ../../START.md
[today]: ../../TODAY.md

<!-- docs/ -->
[docs-readme]: ../README.md
[fix]: FIX.md
[tracker]: bug_hunt-0_0_15_2.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
