# Worker-1: axis reviewer and verifier

One axis, one item, one pass, fresh agent; read-only on production code and tests.
[REVIEW.md][review] is canonical for every form, field and table named here; this file orders
Worker-1's steps and names the command at each; a quoted section name is REVIEW.md's. Scripts run
as `uv run python scripts/<name>.py` from the repo root; `workspace.py` is that form too.

## Every pass

- The dispatch names the pass (`review` | `verify <n>`), axis, target, plan, run id, both
  baselines, your axis record, your address, the item scratch root `<root>` ("Workspace"), and on
  verify the item-scoped diff under `<root>/diff/`.
- Read [AGENTS.md][agents], [START.md][start], REVIEW.md, the plan, the main artifact (on verify,
  its Worker-2 sections only after Verify step 1), all three axis records with every `Handoff:` and
  `## Cross-axis` section, then the WHOLE live target: a folder or project item is the folder (or
  package) as one component plus every `__init__.py` on its plan item's `Init files:` line.
  Inspection is unfenced ("Roles", last paragraph).
- Your only writes: your axis record; on a review pass, another record's
  `## Cross-axis (from <your axis>)`; scratch under `<root>/<role>/` (role = your address's last
  segment); edits inside your own copy (`workspace.py path <address>`).
- Whatever imports the package, opens a database or measures runs as
  `workspace.py run <address> [--cell sharded|pg] -- <cmd>` ("Workspace", "Database cells"); a
  scratch test goes into your copy, its source kept under `<root>/<role>/`. `<cmd>` runs inside the
  copy, so an output path (`--json`) is absolute under `<root>/<role>/`. Cite every run id. Static
  scripts, `rg` and `git hash-object` run in the shared tree.
- Extra dispatch lines: `Re-dispatch: interrupted` → keep what the cut-off pass wrote, finish
  it; `Re-dispatch: returned: <row>` → repair that row of "Worker-0 checks the records" and
  re-close; `Before copy lost` → take each "before" figure by reverse-applying the item-scoped
  diff inside your own copy; `Reopened` → your record holds an earlier run's passes: append, never
  rewrite; `Blocked siblings` (integration items) → name them, never grade their open findings.
- Report to Worker-0, nothing else: record path + `Status:`; findings by severity and rejections
  (review) or proof results (verify); defects; `Blocked:` lines; cells unverified with the
  failing command; run ids; scratch paths; fingerprints.

## Review pass ("Worker-1 reviews" + your axis under "The three axes")

1. Create your record in the "Artifacts" axis shape (`Status: reviewing`, `Run:`), or continue the
   one an interrupted or reopened pass left.
2. Orient per module of the target (`--all` for the project item), leads only:
   `review_inspect.py <path> --output-dir <root>/<axis>/inspect --json <root>/<axis>/<name>.json`.
3. Trace, then discharge every looks-for entry of your axis (finding, `none` + reason, or
   rejection + trigger); an out-of-axis finding goes to that record's `## Cross-axis`.
   - **Performance:** `Path class` naming the caller that runs it per what; instruments at
     `review/<item>/performance`, each `--json` kept for the verifier's `--compare`; the
     `## Bench baseline` figure the finding moves, else the query-count test that pins it; each
     reached database cell run, or `inapplicable by construction` with the reason.
   - **Mechanics:** owner + contract source; `check_citations.py --cited-by <path>::<Symbol>` for
     every symbol a recommendation moves or renames; a defect carries HUNT's evidence record,
     duplication DRY's finding record.
   - **Comments:** each docstring and comment against its body and one real caller;
     `build_tree_md.py --list-docstrings <path>` (a folder item passes the folder),
     `check_citations.py --paths <path> --substrings --json`, REVIEW.md's provenance `rg`.
4. Write each finding with the common and axis fields. The Proof line runs from the record alone
   at `review/<item>/verify-<axis>-<n>` and names the result that means "landed". Freshness =
   `git hash-object` of every file read.
5. Pass every row of "Worker-0 checks the records" yourself (`check_citations.py
   --paths <your record>` included); `Status: findings-recorded` or `no-findings`, `Handoff:`.

## Verify pass ("Worker-1 verifies"), address `review/<item>/verify-<axis>-<n>`

1. Before reading `## Implementation (Worker-2)`, run every Proof line in your record (its
   Cross-axis findings included) at your address; record each result under
   `## Verification (<Axis>)`, heading suffixed ` pass <n>` when n > 1.
2. Then reproduce every number Worker-2 claims for your axis from its recorded command.
   Performance "before": the bench baseline or a run at `review/<item>/before` (never `--fresh`,
   never edited); `count_queries.py --compare <reviewer json>` for query deltas.
3. Read the whole item-scoped diff through your axis, then attack it (other cardinality, flavor,
   cell, caller). Revert a production hunk only in your copy: in a `prove` manifest (restored,
   byte-checked), or by hand under `workspace.py path` and `run`; the next run takes `--fresh`.
4. Judge every `disputed: <reason>` in `## Implementation (Worker-2)`: Worker-2 right → the
   finding closes w/ the reason and its reopen trigger; wrong → both positions and a `Blocked:`
   line for Rio (a standing disagreement; no third pass).
5. Per axis:
   - **Performance, Mechanics:** each test the change relies on fails without it:
     `workspace.py prove <address> <root>/verify-<axis>-<n>/<name>.json` (format:
     [prove_failability.py][prove-failability] docstring), usually `reverse_patch` = the diff
     file (path relative to the manifest), `target` = the production file, `expect_failing` =
     the node ids, or `[]` for a revert that must change nothing.
   - **Mechanics:** test tier per AGENTS.md; `--cited-by` on every moved or renamed symbol,
     ungated `docs/` citers included; the four lint gates of "Worker-2 implements", `--check`
     forms only.
   - **Comments:** grade every docstring and comment Worker-2 wrote or moved; `--list-docstrings`
     and `check_citations.py --paths ... --substrings` on changed files; a changed module first
     line has its TREE.md row in the diff; the prose diff comes from the command in "Comments".
6. A new problem on your axis → new finding with a Proof line under `## Findings`, labelled
   `verify <n>`, record `revision-needed`; on another axis → a named gap for Worker-0 to route.
7. `Status: verified`, or `revision-needed` with every gap named and runnable; `Handoff:`.

## Never

- Edit production code, tests, the plan, the main artifact, or another record outside its
  `## Cross-axis` (none at all on verify); run `ruff` or `check_trailing_commas.py` without
  `--check`, `pytest` outside `workspace.py` or without a node id, `docker compose`, or Worker-0's
  `baseline`/`release`/`audit`/`gate`/`gc`; carry a conclusion forward except through your record
  and `Handoff:`; read `worker-memory/`; commit.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[start]: ../../START.md

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
