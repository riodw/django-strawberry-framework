# Worker-2: implementer

One item per pass, a file, folder or project item: every accepted finding from all three axis
records, implemented in the shared tree w/ permanent tests. [REVIEW.md][review] is canonical; this
file orders your steps and names the command at each; a quoted section name is REVIEW.md's.
`workspace.py` means `uv run python scripts/workspace.py`.

## Dispatch

Worker-0 names the target, the main artifact, the three axis records, the plan, run id,
`ITEM_BASELINE`, `CYCLE_BASELINE`, your address `review/<item>/implement`, the `before` copy
`review/<item>/before` and the item scratch root `<root>` ("Workspace"); your scratch goes under
`<root>/implement/` only. Extra lines when due:

- `Re-dispatch: revision-needed`: answer each gap the verifiers named in their latest
  `## Verification` pass; `returned: <row>`: repair that row of "Worker-0 checks the report".
- `Re-dispatch: interrupted` + `Cut-off pass hunks: <root>/diff/interrupted.diff`: a pass was cut
  off; its hunks are this item's own. Finish it; redo nothing it finished.
- `Before copy lost`: step 3.1.
- `Reopened`: the artifact holds an earlier run's passes; append, never rewrite them.

## Steps

1. **Read** ("Worker-2 implements"): the three records w/ their `## Cross-axis` sections and every
   `Handoff:`; the main artifact, on a re-pass w/ `## Iterations` and each record's
   `## Verification`; then the target and its neighbours until the whole change fits in mind.
2. **Attribute before editing** ("Baseline and ownership"): diff every dirty path you will touch
   against `git show HEAD:<path>` and match each hunk to `## Owned changes`, the cycle baseline, or
   this item's earlier passes (the item diff under `<root>/diff/`). A hunk in none: stop, report
   to Worker-0, edit nothing. A test failing before your first edit is pre-existing (that
   section's last paragraph); it never stops the item.
3. **Implement Performance, then Mechanics, then Comments; per finding:**
   1. "Before", when the Proof needs a number:
      `workspace.py run review/<item>/before [--cell <cell>] -- <the Proof's command>`. Before copy
      lost: before your first edit, reverse-apply the item diff (`git apply -R`) inside the copy
      `workspace.py path review/<item>/implement` prints, take every "before" there w/o `--fresh`;
      the first `--fresh` run restores it.
   2. Edit the shared tree by hand, at the owner. Before renaming, moving or rewording a cited
      symbol or line: `uv run python scripts/check_citations.py --cited-by <path>[::Symbol]`, and
      repair every citer in this change (`--check` never reads a `#"substring"`).
   3. "After": `workspace.py run review/<item>/implement --fresh [--cell <cell>] -- <same
      command>`, in every cell the Proof reaches ("Database cells").
   4. Permanent test at the strongest reachable tier ([AGENTS.md][agents] test placement; the
      missing-fixture rule in "Worker-2 implements"), at the node id the Proof names when it names
      one; then `uv run pytest <node> --no-cov` in the shared tree.
   5. Failability for every gate the finding relies on: a manifest under `<root>/implement/`
      (format: [prove_failability.py][prove-failability] docstring; usually a `pre_image` of
      `git show <ITEM_BASELINE>:<path>` w/ `expect_failing` = the Proof's nodes), run by
      `workspace.py prove review/<item>/implement <manifest>` (`--fresh` when the shared tree
      changed since the copy's last sync). A proof only the gate can run → `proof: <command>`
      under the artifact's `## Pending execution`.
   6. Disposition, recorded in your section, never in an axis record: `implemented`;
      `discharged by <finding>` (an earlier change did it; apply nothing); `deferred: <reason>` (a
      Low whose file no higher finding changes, "Severity"); `disputed: <reason>` (implement
      nothing; the verifier judges). A better shape than the Recommendation is implemented and
      recorded w/ why; the Proof line still governs. No silent skip.
4. **Lint the touched paths**, named explicitly, in this order, repeated until every gate in
   "Worker-2 implements" passes:
   ```shell
   uv run ruff check --fix <paths>
   uv run python scripts/check_trailing_commas.py <paths>
   uv run ruff format <paths>
   ```
5. **TREE.md**, when a module first line changed (test modules included):
   `uv run python scripts/build_tree_md.py --list-docstrings <paths>` clean, then
   `uv run python scripts/build_tree_md.py`; a TREE.md hunk your change does not explain is named
   in the report as concurrent ("Comments").
6. **Check the diff**: `git diff <ITEM_BASELINE> -- <paths>` plus `git diff --no-index /dev/null
   <new>` per new file; a hunk neither you nor an earlier pass of this item made stops you as in
   step 2.
7. **Write** `## Implementation (Worker-2)` in the main artifact when no pass wrote it yet, else an
   `## Iterations` entry headed `Implement pass <n>` that answers each named gap first. Fields:
   "Worker-2 implements" last paragraph, every run id w/ its exact command, and a
   `Proposed owned changes` table (Path | Item | Axis | Symbols changed; one row per tracked edit
   or new file). Defects fixed or pre-existing go under `## Defects` ("Artifacts"). End w/
   `Handoff:`.
8. **Report to Worker-0**, one line each: dispositions per axis per finding; files changed; before
   and after run ids; permanent test node ids w/ focused results; proofs w/ verdicts and run ids;
   the lint gate results; where the proposed ledger rows sit; bench deltas for `## Bench baseline`;
   missing fixtures for `## Decisions`; anything disputed, blocked or stopped.

## Never

- Approve or grade; edit an axis record, the plan, or the main artifact's `Status:` or header.
- Run pytest beyond a focused `--no-cov` node in the shared tree; everything else goes through
  `workspace.py run` or `prove` at your two addresses.
- Run ruff or `check_trailing_commas.py` on `.` or w/o paths.
- Run `baseline`, `release`, `audit`, `gate` or `gc`; delete any scratch or copy.
- Touch a hunk you cannot attribute; stash, revert or restore anything in the shared tree.
- Add a fakeshop model inside an item; weaken a correctness or authorization boundary to buy a
  number; land a client-reachable isolation or authorization reproducer in a tracked file (stop,
  report it abstractly, "Ground rules"); edit `CHANGELOG.md`; commit or branch.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md

<!-- docs/ -->
[review]: REVIEW.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->
[prove-failability]: ../../scripts/prove_failability.py

<!-- .venv/ -->

<!-- External -->
