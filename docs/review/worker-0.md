# Worker-0: coordinator

Worker-0 is the main session. It never reviews, implements, approves, regrades or overrides a
verifier. [REVIEW.md][review] is canonical; this file orders Worker-0's steps and names the
command at each; a quoted section name is REVIEW.md's and owns the command's form.
`workspace.py` means `uv run python scripts/workspace.py`, `review_plan.py` means
`uv run python scripts/review_plan.py`.

## Start

1. Read [AGENTS.md][agents], [START.md][start], REVIEW.md, this file. Scope flags:
   `--scope <entry>` per `scope:` entry of the entry command, else `--changed`. Mode:
   `pause-after-each-item` when named, else `autonomous`. Plan: `docs/review/review-<release>.md`,
   release from `__version__`.
2. No plan → `review_plan.py plan <scope flags> --mode <mode>`. Plan exists →
   `review_plan.py resume --plan <plan> <scope flags>`, then set the header `Mode:` by hand when it
   differs. Output ends `nothing in scope` → report that to Rio and stop.
3. `review_plan.py reconcile --plan <plan>`; act on every line; re-hash every recorded fingerprint
   ("Plan"). Reopen = plan item `Status: pending`, box unticked, a `Reopened: <date> - <moved
   paths>` field; the item keeps its artifact and records, and pass numbers never restart.
4. First run of the plan: fill `CYCLE_BASELINE` and the untracked listing, once. Later runs: the
   `Drift:` line `resume` wrote stands ("Baseline and ownership").
5. `## Bench baseline` holds no figures → run its rows at `<phase>` = `baseline` before any item
   binds a copy, fill them ("Bench baseline"), then `workspace.py release review/bench`. Each row
   runs as its own literal command line: a shell variable holding the `workspace.py run` prefix
   is one word to zsh, so every row exits 127.
6. Plan `Status: in-progress`. Items carried into this run with `Status: out-of-scope` →
   `pending`. Drive the run's in-scope items in plan order by "Resume".

Every note Worker-0 adds to a plan item is a field line in the item shape ("Plan"):
`    - <Key>: <value>`. Any other line ends the item for `reconcile`.

## Resume

The plan and the artifacts are the only state; agents die with the session, some mid-write. After
a compaction inside the session, re-read Start step 1's files and continue here without `resume`;
agents dispatched before the compaction still run, so wait for their notifications before
re-dispatching their roles. A new session runs Start, then this.

- `workspace.py status review`: a `RUNNING` copy is a live command; never release or re-dispatch
  over it. A copy bound to an item not in flight is stale: `workspace.py release` that item.
  `ITEM_BASELINE` is read from the plan item's `Item baseline:` field, never from `status`.
- A pass is finished when what it wrote ends with `Handoff:`: a review pass in its axis record,
  closed `findings-recorded` or `no-findings`; an implement pass in `## Implementation (Worker-2)`
  or its `## Iterations` entry; a verify pass in its `## Verification (<Axis>)` heading
  (` pass <n>` after the first), with a verdict. Owed verify passes: every axis at pass 1; after,
  the failed axes, any axis a verifier named a gap on, and Comments whenever the re-pass diff
  touches a docstring or comment.

Each open item takes the first row that matches:

| Plan item / main artifact `Status:` | Next action |
|---|---|
| `pending` | "One item" step 1 |
| a `Returned:` field whose target has no more `Handoff:` paragraphs than it records | re-dispatch that return |
| `reviewing`, an axis record missing or unfinished | `workspace.py release review/<item> --role <axis>`; re-dispatch it, `interrupted` |
| `reviewing`, all three finished | step 4 |
| `ready-for-implementation` | step 5 |
| `implementing`, the pass finished | step 6 |
| `implementing`, the pass unfinished | "Interrupted Worker-2" |
| `ready-for-verification/<n>`, an owed pass unfinished | `workspace.py release review/<item> --role verify-<axis>-<n>`; re-dispatch it, `interrupted` |
| `ready-for-verification/<n>`, every owed verdict in | step 8 |
| `revision-needed` | step 8, re-pass |
| `verified`, box unticked | step 8: write each close field the item lacks |
| `verified` and ticked; `blocked` | skip |

- **Interrupted Worker-2:** `workspace.py release review/<item> --role implement`;
  `git diff <ITEM_BASELINE>` plus each untracked file no baseline or `Drift:` line lists →
  `<root>/diff/interrupted.diff`; a fresh Worker-2, `interrupted`. A hunk serving a finding (its
  target, owner or permanent test) is the cut-off pass's own; one in a path Worker-2 must touch
  that serves none is unattributed; the rest is concurrent work.
- **Lost `before`** (`status` lacks `review/<item>/before`, item open): item diff empty → rerun
  `workspace.py baseline`, the new `Item baseline:` beside the old; edits landed →
  `Before copy lost: <date>` on the item and in every later dispatch. No `review` flow at all →
  the run log went with it: `Evidence lost: <date>` on the run; an `audit` failure on a run id
  older than that line is not `invalid`, and the next pass re-measures what it cites.

## One item

`<item>` in an address: the target path (`optimizer/walker.py`), the folder (`optimizer`) or
`project`. `<root>`: the item scratch root ("Workspace"). A folder item runs once each file item in
it is `verified` or `blocked`, the project item once each folder item is; their dispatches name the
blocked ones ("Integration passes").

1. New drift → a `Drift:` line. `workspace.py baseline review/<item>`; `Item baseline: <sha>` and
   the untracked listing on the item ("Baseline and ownership").
2. Skeleton artifact ("Worker-0 dispatches"; a reopened item keeps its own), `Status: reviewing`.
   Every status from here is set on the artifact and the plan item alike.
3. Dispatch the three reviewers at once.
4. Each record as it lands: `workspace.py audit <record>`,
   `uv run python scripts/check_citations.py --paths <record>`, "Worker-0 checks the records". All
   three pass → `Path class:` into the item and the artifact header, `ready-for-implementation`,
   `workspace.py release review/<item> --keep before`.
5. `implementing`; dispatch Worker-2.
6. "Worker-0 checks the report", with `workspace.py audit <artifact>`. Item diff:
   `git diff <ITEM_BASELINE> -- <paths the report lists>` plus `git diff --no-index /dev/null
   <file>` per new file → `<root>/diff/pass-<n>.diff`. Pass → missing fixtures it names into
   `## Decisions`, `ready-for-verification/<n>`, `workspace.py release review/<item> --keep
   before`.
7. Dispatch the owed Performance and Mechanics verifiers at once; Comments after both report.
8. Close ("Worker-0 closes the item"). A verifier report carrying `Blocked:` → `blocked`. Every
   owed verdict `verified` → Worker-2's proposed rows, checked against the item diff, into
   `## Owned changes`; its bench deltas into `## Bench baseline`; `Result:`, `Verification:`,
   `Cleanup:` on the item; `verified`; tick; `rm -r docs/review/temp-tests/<stem>`;
   `workspace.py release review/<item>`; advance, or report and wait. Any `revision-needed` →
   `revision-needed`, then a fresh Worker-2 re-pass from step 5, verification at `<n+1>`.

- A step 4 or 6 row fails → back to that role with the row named, and
  `Returned: <axis | Worker-2> - <row>; handoffs <count in the file it writes>` on the item. The
  same row failing twice, or a second failed re-pass → `blocked`.
- An unattributed hunk stops the item until Rio reconciles it; `autonomous` records it `blocked`
  and advances. A pre-existing failure goes into `## Decisions` (Worker-2 also records one it
  reports under the artifact's `## Defects`); it blocks the gate row, never the item.
- A reviewer's `Routed:` lead for another item → a `Routed:` line in that item's dispatch, or
  `## Decisions` w/ its owner when the item is out of this run's scope.
- A verifier's named gap on another axis → that axis owes a verify pass, dispatched w/ a
  `Routed gap:` line; a gap the receiving verifier puts outside the item's reach →
  `## Decisions` w/ its named owner.
- A sensitive finding ("Ground rules") is `blocked` at once and its scratch root stays until Rio
  clears it. `blocked` → `Blocked:` on the item, the decision into `## Decisions`,
  `workspace.py release review/<item>`, advance.

## Dispatch

Subagent `review-worker-1` or `review-worker-2` by name, in the background ("Roles", **Effort**).
Pointers only, never a pasted ledger, record or diff. While agents run, wait for their
notifications: no sleep polling, no other item's work. One prompt per agent:

```text
<Review pass, <axis> axis | Implement pass <n> | Verify pass <n>, <axis> axis>.
Target: <item label> (<path>). Plan: <plan>, run <run id>; ledger: its ## Owned changes.
CYCLE_BASELINE=<sha> ITEM_BASELINE=<sha>
Address: review/<item>/<role>. Scratch root: <root>; yours: <root>/<role>/.
Review:    record docs/review/rev-<stem>.<axis>.md.
Implement: artifact docs/review/rev-<stem>.md, records
           rev-<stem>.{performance,mechanics,comments}.md, before copy review/<item>/before.
Verify:    record docs/review/rev-<stem>.<axis>.md, item diff <root>/diff/pass-<n>.diff.
```

Add a line only when due: `Blocked siblings: <items>`; `Reopened: <moved paths>`;
`Routed gap: <gap> (from <axis> verify <n>)`;
`Re-dispatch: interrupted | returned: <row> | revision-needed, gaps in pass <n-1>`;
`Cut-off pass hunks: <root>/diff/interrupted.diff`; `Before copy lost: take "before" figures in
your own copy after reverse-applying <latest item diff>`.

## Closeout

1. Every in-scope item but the gate `verified` or `blocked` → Start step 3 again, reopened items
   first; then `workspace.py gate review`, every `## Pending execution` command as listed, the
   `## Bench baseline` rows at `<phase>` = `gate` ("Final gate and closeout"). A failure routed to
   an item makes it `revision-needed`; the gate reruns after it closes.
2. `## Outcomes` before deleting anything; tick the gate. Plan `Status: blocked` with the decisions
   Rio owes when any item or the gate row is blocked, else `complete` or `partial (<scope>)`.
3. Remove this run's `docs/review/temp-tests/<stem>/` dirs bar a sensitive blocked item's, and the
   `docs/review/worker-memory/` contents, each by explicit path; `workspace.py gc review`.
4. Report to Rio in five lines or fewer: result, blocked items with the decision owed, what is
   uncommitted. Never commit.

Beside a HUNT or DRY Worker-0 under [MUSE.md][muse]: REVIEW.md's last paragraph.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[muse]: ../../MUSE.md
[start]: ../../START.md

<!-- docs/ -->
[review]: REVIEW.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
