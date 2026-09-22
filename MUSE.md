# MUSE.md: running Worker-0 on Muse Code

How the maintainer's Claude session launches, watches, steers, pauses and relaunches Muse agents
that run Worker-0 for the three agentflows: [HUNT.md][hunt], [DRY.md][dry], [REVIEW.md][review].
Everything here was learned by doing it on the 0.0.15 hunt and DRY cycles (2026-09-17 to
2026-09-22). Read this before touching a `muse` process; do not rediscover the CLI.

The standing shape: Muse runs ONLY Worker-0. Worker-0 dispatches its own Worker 1 / Worker 2
subagents inside Muse. Claude never plays a worker role for a Muse-run flow; Claude is the
supervisor that launches, monitors, relays maintainer decisions, and reports.

## 1. Harness facts (Muse Code 1.3.0, build R3401.1)

| Thing | Where / what |
| --- | --- |
| Launcher | `~/.local/bin/muse` (shell shim) → `~/.local/bin/muse-bin-<version>` (the real binary, ~289 MB). `ps` shows the `muse-bin-*` path, not `muse`. |
| Version pin | `~/.local/bin/.muse-version`; `muse --version` prints `Muse Code 1.3.0 (1.3.0-R3401.1)`. A new binary appears beside the old one on update; pid files keep pointing at the old process. |
| User config | `~/.config/muse/settings.json` (provider `meta`, model `muse-spark-1.3-contributor`, `reasoning_effort` `max`, permissions profile `:unrestricted`), `auth.json`, `trust.json`. |
| Session store | `~/.local/share/muse/sessions/<YYYY>/<MM>/…` (durable JSONL per session), `session-index.db` (sqlite), `local-tracing/`, `model-catalog/`, `feature-config/` (server-pushed gate flags, 1 h TTL). Session names: `~/Library/Application Support/muse/session-name-authority/`. |
| Rules files | Muse loads `AGENTS.md` from the workspace root and IGNORES `CLAUDE.md` when both exist (stderr warning `rules file at …/CLAUDE.md is ignored … AGENTS.md takes precedence`). So the worktree's AGENTS.md is the whole rule set the agent sees; anything only in CLAUDE.md must go into the prompt. |
| Provider | `meta` (subscription). Quota is a weekly window; the exhaustion text is `Subscription quota exhausted. Your usage window resets at <ISO>` with `(rate_limit_error)` and an `API error 429 [request_id=…]` prefix. The High Usage upgrade lifted the block immediately on 2026-09-22 without waiting for the reset. |

### 1.1 `muse exec` flags that matter

`muse exec [OPTIONS] [PROMPT]` runs one prompt headless and exits when the run ends.

| Flag | Use |
| --- | --- |
| `--prompt-file <path>` | The Worker-0 prompt. Always a file, never inline (prompts are 5–7 KB). |
| `--workspace <path>` | Roots the policy-gated tools at the worktree. This is the ONLY location control; the agent can still `cd` elsewhere in shell, so the prompt must also forbid the main checkout. |
| `--yolo` | Disables approval prompts AND the sandbox AND trusts the workspace for this run. Required: headless approval prompts would hang, and the sandbox blocks `uv run pytest` writes. Equivalent to `--disable-approval --disable-sandbox --trust-workspace`. |
| `--model muse-spark-1.3-contributor` | "Contributor mode". Verify from the JSONL, not from the flag (see §3). |
| `--reasoning-effort max` | Scale is `none|minimal|low|medium|high|xhigh|max|ultra`; default `high`. `max` is what the maintainer asks for; `ultra` is gated by `MUSE_EXPERIMENTAL_ULTRA_REASONING_EFFORT`. |
| `--json` | JSONL events on stdout. Always on; it is the only observability. Redirect stdout to `<name>.jsonl`, stderr to `<name>.stderr`. |
| `--session-id <uuid>` | Pin the session id so the launch record, the JSONL and `muse resume`/`export` agree. Optional; without it read the id from the first `session.run.linked` event. |
| `--max-model-steps <N>` | Hard cap on model steps. Not used for Worker-0 (a hunt is thousands of steps). |
| `--context-compaction-*` | Strategy `summary-preserved-suffix/v1` (default), `prefix-extension-summary/v1`, `prefix-extension-inventory-summary/v1`; soft/hard thresholds. Left at defaults so far. |
| `--user-input-auto-resolve` | Auto-cancels `request_user_input`. Not used: Worker-0 is told to write decision requests into the ledger and stop instead. |
| `-w/--worktree existing --worktree-existing <path>` | Muse's own worktree binding. NOT used: the maintainer's t3 worktree is passed as `--workspace` and Muse is told never to create branches. |
| `--parallel-tool-calls` | Meta API parallel tool calls. Default was fine. |
| `--approval-mode`, `--approval-judge`, `--permission-profile` | Irrelevant under `--yolo`. |

Not available: any stdin channel. Headless `exec` leaves fd 0 on a dead unix socket. You cannot
type at a running Worker-0.

### 1.2 Other subcommands

| Command | What it does | Status for us |
| --- | --- | --- |
| `muse resume <uuid>` / `--last` | Reopens a stored session in the TUI (interactive). | Untested for Worker-0; would need a terminal. Relaunch-with-prompt has been the practice. |
| `muse export --session <uuid> --out <file>` | Full durable log as one JSON document (messages, tool calls, approvals, subagent lineage). Offline. | Use for post-mortems instead of grepping raw JSONL. |
| `muse trace inspect --session-log <jsonl> [--all-runs] [--render-mode compact]` | Renders a session log as a report. | Works on our captured `<name>.jsonl`. |
| `muse session-message list --json` / `send --target <uuid> < body` | Cross-session messaging INTO a running session. | Gated; see §4.2. Returned `external_agent_ingress_closed` for every session launched without the gate. |
| `muse skills …`, `muse plugins …`, `muse init`, `muse mcp`, `muse auth/login/logout`, `muse config`, `muse schema`, `muse serve` | Skills, plugins, scaffold, MCP OAuth, credentials, enterprise config, MSP wire schema, MSP host over stdio. | Not used. |

### 1.3 Environment gates seen in the binary

Set as `NAME=on` or `NAME=1` on the launching process. The ones that matter:

- `MUSE_EXPERIMENTAL_EXTERNAL_AGENT_INGRESS=on`: opens the local session list and message ingress
  for that process ("the local Session list is closed by the ExternalAgentIngress gate" otherwise).
- `MUSE_EXPERIMENTAL_LOCAL_SESSION_MESSAGING=1`: peer messaging between sessions.
- `MUSE_EXPERIMENTAL_MONITOR`, `MUSE_EXPERIMENTAL_WORKFLOW_TOOL`, `MUSE_EXPERIMENTAL_CODE_MODE`,
  `MUSE_EXPERIMENTAL_PREFIX_COMPACTION`, `MUSE_EXPERIMENTAL_ULTRA_REASONING_EFFORT`: present, unused.
- `MUSE_MODEL`, `MUSE_BIN`, `MUSE_SESSIONS`, `MUSE_CURRENT_SESSION_LOG`: overrides for model,
  binary path, session store, log path.

### 1.4 JSONL event vocabulary

Every line is `{"stream":{"kind":"session","id":<session uuid>}, "sequence":N, "payload_type":…,
"payload":{…}}`. Types observed across 71 runs, with what they mean to a supervisor:

| `payload_type` | Meaning |
| --- | --- |
| `session.run.linked` | First useful line; `stream.id` is the session uuid, `payload.run_stream.id` the run uuid. |
| `run.model.configured` | Confirms the model actually bound. MUST show `muse-spark-1.3-contributor`. |
| `turn.input.user` | The prompt was accepted. |
| `task.lifecycle.proposed/accepted/scheduled/started/completed/rejected/failed/cancelled` | Tool-call lifecycle. `rejected` is normal (policy filter); `failed` is normal-ish (a shell command returned non-zero). NOT a health signal. |
| `tool.result` | Tool output text; `payload.text`. Tail these to see what Worker-0 is doing. |
| `run.output.delta` | Streamed assistant text. |
| `todo.snapshot.updated` | Worker-0's own todo list. |
| `session.workspace_branch.observed` | Branch check. |
| `run.terminal.completed` | A Worker-0 TURN ended normally. Fires every time Worker-0 parks to wait for a subagent hand-back (17 of them in one DRY process); the process keeps running and the hand-back starts the next run. Only the last one, after `Status: complete` or a decision request, ends the process. Check `ps`, not this event. |
| `run.terminal.failed` | Run died. `payload.reason` carries the provider text (429, quota). Process exits. **This and `Subscription quota exhausted` are the only two failure greps that matter.** |

### 1.5 Plan, pricing and budget (why we do not send prompts casually)

**Plan on this account** (`riodweber@gmail.com`, Meta OAuth via device code, provider `meta`,
`api.meta.ai/v1`): **Muse Code "High Usage"**, upgraded 2026-09-22 ~13:40Z from "Everyday Usage".
Maintainer's words: "3x the price but 5x the usage". Model bound: `muse-spark-1.3-contributor`
(the catalog default; its description: "Your content, including inter-session messages, may be
used for product improvement", 1,007,997-token context, 128,000 output).

**Muse Code subscription tiers** (Meta's [subscriptions page][muse-subs]; prices from press and
third-party pages since Meta's page omits them; the multipliers on Meta's own page are 5x/20x, a
fan site says 3x/10x):

| Tier | Price | Allowance (Meta's wording) |
| --- | --- | --- |
| Everyday Usage | $5/mo | "Send 10-50 prompts every 5 hours" |
| High Usage (**ours**) | $15/mo | "5x more usage than the Everyday Usage plan" |
| Power Usage | $50/mo | "20x more usage than the Everyday Usage plan" + early features |

Metering facts we established, not from docs but from six 429 deaths:
- Two windows exist: a rolling **5-hour** window (429 text `resets at 2026-09-22T00:32:39Z`,
  `…T07:40:45Z`) and a calendar **weekly** window resetting **Monday 00:00Z** (`resets at
  2026-09-28T00:00:00Z`). Neither the weekly size nor the 5-hour size is published; there is no
  `muse usage` command; third-party tools read a `subscription_usage` SSE event.
- The unit is the **prompt**, i.e. `turn.input.user` events: the launch prompt plus each
  subagent hand-back into Worker-0. The maintainer's reading (2026-09-22): internal tool round-
  trips and W1/W2 fan-out do NOT count; user prompts do. Our own turn counts fit the "10-50 per
  5 h" range (13-20 per window) yet still tripped the 5-hour wall three times, so a long
  Worker-0 turn weighs more than a chat question; treat the allowance as a budget, not a count.
- Burn history on Everyday: 48 prompt turns over ~6 h of agent runtime (two Worker-0s at
  `max`) exhausted the WEEK by 05:11Z on day two. On High Usage the same two agents have run
  ~3 h continuously without a 429 (2026-09-22 14:10Z onward).
- The exhaustion text is always `API error 429 [request_id=…]: Subscription quota exhausted.
  Your usage window resets at <ISO>. (rate_limit_error)` in `run.terminal.failed.payload.reason`.
  The process exits; nothing resumes on its own. A 5-hour reset lets you relaunch the same day;
  a Monday reset means the week is gone unless the plan is upgraded (the upgrade took effect
  immediately).

What this means for the supervisor:
- **Every launch, relaunch and `session-message send` is a metered prompt.** Do not relaunch to
  "nudge", do not send status pings, do not message a running Worker-0 unless the maintainer
  asked for that instruction. Monitoring reads local files only (§3) and costs nothing.
- Batch instructions into one prompt file per launch. A relaunch also re-reads the ~1,600-line
  ledgers and AGENTS/START, so each death costs a large turn before any work resumes; this is
  why §2 arms the failure grep on every tick and §4.3 lists everything a fresh prompt must carry.
- Prefer SIGSTOP/SIGCONT (§4.1) over kill+relaunch for pauses: a resume is not a prompt.
- Running three Worker-0s (hunt + DRY + review) roughly multiplies prompt turns by 1.5x over
  today's two; on High Usage that is untested. Watch the first 5-hour window after launch.

**Pay-as-you-go alternative** (Meta Model API, no windows; [pricing page][muse-pricing]):
`muse-spark-1.3-contributor` $0.10 input / $0.002 cached input / $0.20 output per million tokens,
100 requests/min and 3M tokens/min; `muse-spark-1.3` standard $1.25 / $0.15 / $4.25 per million,
3,000 requests/min and 4M tokens/min. Contributor's discount is "in exchange for permission to use
your prompts and completions to train future Meta models". Our ~6 h Everyday burn was estimated at
$3-15 at contributor rates (hidden `max` reasoning is billed as output and is invisible in the
logs), so the API is the fit if multi-day unattended runs outgrow High Usage. Switching means
`muse auth` with an API key and `--api-key-stdin`; not done yet.

Do not confuse these with the muse.ai personal-agent plans (Power $20/mo 500M tokens per week,
Maximum $100/mo 3B tokens per week): different product, different quota.

## 2. Launch recipe

Preconditions: the maintainer said "restart"/"launch" AND named the flow(s), the model mode
(`contributor`) and the effort (`max`). Never launch on inference. Rule 33: no branch work, so the
target is always the existing worktree.

```bash
WT=/Users/riordenweber/.t3/worktrees/django-strawberry-framework/t3code-1cc21548
S=$SCRATCHPAD/muse            # session scratchpad, never the repo
mkdir -p "$S"
# one line per flow; rotate old logs first (mv hunt.jsonl hunt-runN.jsonl)
MUSE_EXPERIMENTAL_EXTERNAL_AGENT_INGRESS=on MUSE_EXPERIMENTAL_LOCAL_SESSION_MESSAGING=1 \
nohup muse exec --yolo --workspace "$WT" \
  --model muse-spark-1.3-contributor --reasoning-effort max --json \
  --prompt-file "$S/hunt-prompt-N.md" > "$S/hunt.jsonl" 2> "$S/hunt.stderr" &
echo $! > "$S/hunt.pid"
```

Same for `dry` and `review` with their own prompt, jsonl, stderr, pid. Then, within a minute:

```bash
grep -m1 -o '"run.model.configured".\{0,400\}' "$S/hunt.jsonl" | grep -o 'muse-spark[^"]*'
grep -m1 -o '"stream":{"kind":"session","id":"[^"]*"' "$S/hunt.jsonl"   # session uuid, record it
cat "$S/hunt.stderr"   # expect: workspace root (explicit), trust source=run-flag, the CLAUDE.md-ignored warning
```

Then ALWAYS arm the check-in loop (§3). A launch without the loop is a launch nobody watches.

Notes:
- The two env gates are new as of 2026-09-22 and untested end to end; they cost nothing and are
  the only known route to `muse session-message send` working later (§4.2). Verify right after
  launch with `muse session-message list --json`; if it still says ingress closed, note it and
  fall back to §4.1. Observed 2026-09-22 after the gated relaunch: `list` (run with the same two
  env vars) returned `{"schema_version":1,"sessions":[]}` instead of `external_agent_ingress_closed`,
  i.e. the gate opened but the running exec sessions are not listed. `send` stays untested
  (each send is a metered prompt); try it only when the maintainer actually wants a message sent.
- Stop at a boundary without messaging: a background poller on the ledger that SIGSTOPs the
  pid the moment the item's verdict line lands (DRY: `Outcome:` + row ticked; HUNT: the next
  `Fold … UTC` paragraph ending `In flight now: …`), then TERM+CONT and relaunch. HUNT always has
  a second dispatch in flight, so one worker is lost; DRY loses at most a seconds-old dispatch.
- `timeout(1)` is not installed on this Mac ([START.md][start] says so too). Use the Bash tool's own timeout.
- Two Worker-0s (hunt + DRY) share one worktree fine IF each prompt names the other's ownership
  (§5). Three (with review) has not been tried; review edits production files, so expect more
  MIXED files and say so in all three prompts.

## 3. Monitoring: the check-in loop

Maintainer's standing cadence: every 15 min (`ScheduleWakeup` 900 s; was 295 s until 2026-09-22 16:02), reply in ONE paragraph,
2–3 sentences, naming what each agent is on right now. Stop the loop only if a process died on a
provider error; never relaunch without the maintainer.

Per tick, one Bash call:

```bash
for a in dry hunt; do p=$(cat $S/$a.pid); ps -p $p -o pid,stat,etime | tail -1
  echo "failed=$(grep -c run.terminal.failed $S/$a.jsonl) quota=$(grep -c 'Subscription quota exhausted' $S/$a.jsonl)"; done
df -h / | tail -1
tail -c 1500 $WT/docs/dry/dry-0_0_15.md          # newest run-section paragraph
tail -c 1800 $WT/docs/bug_hunt/bug_hunt-0_0_15.md # newest Fold paragraph
```

What to read:
- `ps` `stat` `S`/`R` = running, `T` = SIGSTOPped (§4.1), missing = exited: then grep the last
  `run.terminal.*` line for why.
- DRY progress lives in the last `### Dispatch …` / `W1 submitted` / `W2 verified` paragraph of the
  current `## Run …` section. Ledger rows are `- [x]`/`- [ ] File|Family|Folder integration`.
- HUNT progress lives in the newest `Fold <UTC> (Worker 0):` paragraph and `## Current status`;
  its last sentence is always `In flight now: …`. Item statuses `verified/stale/pending/hunting`.
- Disk: the hunt's `hunt-ws/` copies are the consumer (1.5 GB steady, once recursed
  `hunt-ws/*/hunt-ws/` four deep). Free space went 24 → 17 GB over one day. Warn below 10 GB; the
  prompts tell Worker-0 to stop dispatching below 6 GB.
- Coverage-gate regressions are NOT loop material unless the maintainer asked; the hunt's
  guards + tests land uncommitted and are its business.

Progress table on request (maintainer asks "table and nothing else"): count `- [x]` vs `- [ ]`
per row kind in the DRY ledger; count statuses in the HUNT `## Current status`.

Helper scripts kept in the scratchpad (`summ.py`, `tail.py`): payload_type census and a tail of
`tool.result` texts. Rewrite in place if the scratchpad is gone; they are ten lines each.

## 4. Steering, pausing, stopping

### 4.1 Signals (always available)

- `kill -STOP <pid>` (and its children: `pgrep -P <pid> | xargs kill -STOP`) freezes Worker-0
  instantly mid-instruction. Nothing is lost; `kill -CONT` resumes at the same point with the
  cache warm. `ps` shows `T`. In-flight Worker 1/2 subagents are frozen too; they did NOT finish.
- Use STOP/CONT for "hold everything now" (maintainer wants a quiet tree for an investigation).
- "Finish current workers, dispatch nothing new" is NOT expressible by signal. Options: (a) poll
  the ledger every ~30 s and STOP each agent the moment its open dispatches are ticked/verified,
  accepting the cut may land a few seconds into the next dispatch line; (b) message it (§4.2).
- `kill -TERM <pid>` ends the run; the ledger keeps whatever Worker-0 last wrote; workspaces under
  `hunt-ws/` and `docs/dry/temp-tests/` stay for the next launch to clean.
- The check-in loop: `ScheduleWakeup stop` when pausing, re-arm on resume.

### 4.2 Messages (only if launched with the gates)

`muse session-message send --target <session-uuid> --json < body` delivers a maintainer
instruction into the running session, e.g. "PAUSE HERE: let every dispatched worker finish and
record normally; dispatch nothing new; when nothing is in flight write a `Paused <date> by
maintainer` line under the current run section and end the run." Both sessions launched
2026-09-22 without the gates answered `external_agent_ingress_closed`; the gate must be on the
`muse exec` process at launch, it cannot be added later. Hence §2's env prefix. Each send is a metered prompt (§1.5).

### 4.3 Relaunch after a death or pause

1. Confirm the death: last `run.terminal.failed` reason, request_id, `ps` gone. Record it.
2. `git -C $WT rev-parse --short HEAD` and compare with the HEAD the ledger last recorded; a move
   means the prompt must ask for a Drift/freshness line.
3. Inventory what died mid-flight from the ledger's last paragraph: every dispatch is dead, every
   partial expectation file is poison (the record says W2 must be expectation-first; a half-written
   expectation from a dead W2 must never be opened by the fresh one). List them in the prompt.
4. Rotate logs (`mv hunt.jsonl hunt-runN.jsonl`), write `hunt-prompt-N+1.md`, launch (§2),
   verify model, arm loop.
5. Never `muse resume` into a dead Worker-0's context; the flows say fresh context per item and
   the prompts say "you never inherit a dead worker's context".

## 5. Prompt design: what produced good Worker-0 runs

The prompt is the ONLY channel for anything not in the worktree's AGENTS.md (CLAUDE.md is ignored,
§1). Shape that worked (hunt-prompt-5, dry-prompt-4, both ~6 KB), in this order:

```
Execute docs/<flow>/<FLOW>.md (You are Worker-0)

You are Worker-0: the orchestrator. You dispatch <W1 role> and <W2 role> subagents, run the
mechanical checks, and write the <record|plan>. You never inherit a dead worker's context;
every dispatch is fresh.

Context you must absorb before your first action:
1. Fresh session, NOT a fresh cycle. Name the live ledger file, its Status, the exact heading
   to resume under (DRY: a NEW `## Run <release> <date>-N`; HUNT: append Folds, `## Current
   status` authoritative), "do not regenerate", which sections are frozen (`## Cycle baseline`).
   Name the prior death: date, time, request_id, "nothing it dispatched is still running".
2. Any maintainer ruling section to READ FIRST and what it supersedes. Ticked rows are verified;
   do not re-trace/re-adjudicate them. Name dropped queue items explicitly.
3. Order of work as a lettered list, with counts, and how to tell "un-artifacted" (check the
   directory, not memory).
4. Location: the worktree path + branch; the main checkout is OFF LIMITS (never read, write,
   run, or cd). HEAD short sha; "confirm with git rev-parse and say so"; whether a Drift line
   is owed; whether the last ITEM_BASELINE may be reused (tree hash + target digests match).
5. Dead dispatches to redo FRESH, one bullet each, W1-vs-W2-only spelled out, dead workspace
   names, "partial expectation files are never to be opened"; on-disk things to KEEP.
6. Counts at last write (items/checked/unchecked; verified/stale/pending/hunting) and the full
   stale list, so the agent's first census has an oracle.
7. Disk: current free GB, the workspace-copy recursion hazard (exclude `hunt-ws` from every
   copy), delete per-item scratch at item close, keep expectation files, stop dispatching below
   6 GB and write a decision request, "delete nothing outside <your scratch>".
8. Concurrent work in the same tree that is NOT yours and NOT to be reverted: the other flow's
   directories and files, the MIXED files with which hunks belong to whom, "attribute every
   hunk by DIFF CONTENT against `git show HEAD:<path>`, never by filename", "record blocked-on-
   <other> with the exact hunk, do not edit around it, do not wait, move on", "coordinate
   through the ledger only".
9. Test hygiene: banned provenance words in tests (plan, audit, sweep, restored, hardening,
   previously, worker, grader, feedback); docstring-only production edits remove no duplication.
10. Open maintainer decisions carried unchanged: list them; "do not resolve them yourself; the
    final gate stays blocked on X".
11. Standing rules: no commit, no branch create/switch, no `git stash`/`git checkout --`/
    `git restore`, `git add <path>` only if the flow calls for staging; after every edit
    `uv run ruff check --fix --exclude hunt-ws .` then `uv run ruff format --exclude hunt-ws .`;
    no `pragma: no cover`; scratch under `hunt-ws/`, `docs/<flow>/temp-tests/` or the OS temp
    dir, never the repo root; run to `Status: complete` or a genuine maintainer decision; when
    blocked, write the decision request into the ledger and stop.
```

Things that measurably helped:
- Naming the death and its request_id up front: the agent stops trying to "find" the previous
  Worker-0 and starts a clean run section.
- The full stale list + counts: the agent's census matched on the first try and it corrected
  its own earlier count slips against them.
- "Attribute by DIFF CONTENT": both agents shared ~40 dirty production files for two days without
  one revert.
- Naming the recursion hazard: after the prompt said "exclude hunt-ws from every workspace copy"
  the disk stopped falling in steps.
- Telling Worker-0 that a maintainer decision is open and NOT its to resolve kept the RED
  `test_djangolistfield_unregistered_guard_survives_a_hostile_metaclass_name` from being "fixed".
- Telling it which probe-pin hash to use: it once "found" digest drift because it used
  `git hash-object` where its workers used `sha256sum`; it corrected itself, but the prompt should
  say `sha256sum` for scratch probes, `git hash-object` for tracked blobs.

Things that hurt:
- Dying on 429 four times before anyone noticed the weekly window (one death per ~6 h of `max`).
  The loop's failure grep exists because of this.
- A prompt that told the agent to re-verify already-ticked rows: it spent a run re-adjudicating.
  Say "ticked = verified this cycle" when that is the ruling.
- A Worker-0 that inherited a half-written expectation file from a dead W2 verified against it.
  Hence "never to be opened".

### 5.1 Per-flow specifics

**HUNT** ([HUNT.md][hunt], roles in `docs/bug_hunt/worker-{0,1,2}.md`): ledger
`docs/bug_hunt/bug_hunt-<release>.md` (+ `-historical.md`), regenerable, `dicta.md` is
maintainer-edited. W1 = attack (workspace `hunt-ws/<item>-r<N>`), W2 = verify expectation-first
(`hunt-ws/<item>-verify`, retained `hunt-ws/w2-<item>-expectation.txt`). Shared testbed
`hunt-ws/floor-310/` is kept. Statuses verified/stale/pending/hunting; a `Stale` note reopens an
item for a narrow re-pass with a scope sentence. Worker-0 runs the mechanical checks (item diff,
digests, collection count, no nested hunt-ws, ruff + trailing-commas + banned-word + pragma scans)
and never overrides a W2 rejection. Fixes land uncommitted with paired tests; the final gate is
full suite + package coverage 100 %.

**DRY** ([DRY.md][dry]): plan `docs/dry/dry-<release>.md` with `## Cycle baseline` (frozen),
`## Run …` sections (one per Worker-0 lifetime), ledger rows `- [ ] File|Family|Folder
integration`, per-item artifacts `dry-file-*.md` / `dry-rule-*.md`. W1 = trace, W2 = verify;
`ITEM_BASELINE` is a tree hash; blob fingerprints via `git hash-object` vs
`git rev-parse <HEAD>:<path>`. `--mode pause-after-each-item` exists in the flow: name it in the
entry command when the maintainer wants a go/no-go per item; otherwise the run is autonomous.
Family rows are consolidations and may be `UNAPPLIED` when the target is hunt-dirty: record, do not
apply without a maintainer word.

**REVIEW** ([REVIEW.md][review]): Worker-0 creates `docs/review/review-<release>.md` from the
version list, coordinates but never reviews/implements/approves, captures the cycle baseline that
worker diffs use, and at the end removes only generated scratch under `docs/shadow/`. `docs/review/`
is committed source of truth: never bulk-delete or overwrite `rev-*.md`, `REVIEW.md`,
`review-*.md`, `worker-*.md` (AGENTS.md rule 22). Not yet run under Muse; when it is, the prompt
must add its ownership (production files it may edit) to the hunt and DRY prompts and vice versa.

## 6. Concurrency contract between the flows

- All Muse agents run in the t3 worktree; the main checkout
  `/Users/riordenweber/projects/django-strawberry-framework` is theirs to never touch. Claude's own
  edits for the maintainer happen in whichever tree the maintainer names (guard deletions on
  2026-09-22 were in the worktree, uncommitted).
- Nobody reverts. Dirty files at task start are concurrent work (AGENTS.md rule 34). A finding
  about another flow's hunk is recorded `blocked-on-<flow>` with the exact hunk.
- MIXED files exist (e.g. `tests/utils/test_errors.py`: DRY census + hunt hostile-class tests);
  attribution is by hunk content vs `git show HEAD:<path>`.
- Only the maintainer commits (rule 32). Worker-0s never `git commit`, never branch (rule 33).
- The 08:45-style "freshness reconciliation" (HEAD moved under a running agent) is Worker-0's
  own job per its flow; the supervisor only tells it the new HEAD in the next prompt.

## 7. Supervisor rules of engagement

- Launch, pause, resume, relaunch only on an explicit maintainer instruction naming the flow.
- Every launch: verify `run.model.configured`, record the session uuid, arm the check-in loop (§3).
- Report in the maintainer's format: one paragraph, what each agent is on, disk if it moved.
- Do not act on the agents' findings in production code unless the maintainer hands you the
  item (as with the `except BaseException` guard resolution); then report per item, not per file, under the [GOAL.md][goal] trust boundary and rule 35.
- Do not fold the agents' self-written closing audits into evidence (memory: "a hunt record's
  self-written closing audit is not evidence"); the maintainer re-inventories before commit.
- `pytest` only when the maintainer authorizes it; `FAKESHOP_SHARDED=1` was authorized
  2026-09-22 for the querysets D1 proof. Fingerprint `examples/fakeshop/db.sqlite3` and
  `db_shard_b.sqlite3` (both TRACKED) before and after any live or sharded run.

<!-- LINK DEFINITIONS -->
<!-- Root -->
[agents]: AGENTS.md
[goal]: GOAL.md
[start]: START.md
<!-- docs/ -->
[dry]: docs/dry/DRY.md
[hunt]: docs/bug_hunt/HUNT.md
[review]: docs/review/REVIEW.md
<!-- docs/SPECS/ -->
<!-- docs/builder/ -->
<!-- django_strawberry_framework/ -->
<!-- tests/ -->
<!-- examples/ -->
<!-- scripts/ -->
<!-- .venv/ -->
<!-- External -->
[muse-pricing]: https://dev.meta.ai/docs/pricing-rate-limits
[muse-subs]: https://dev.meta.ai/docs/muse-code/subscriptions
