# Fixing tracker items

How one open item in the current tracker ([bug_hunt-0_0_15_2.md][tracker]) goes from "To do" to landed.
Entry: `Execute docs/bug_hunt/FIX-PROMPT.md` ([FIX-PROMPT.md][fix-prompt]), which loops this process over every open item.

Each phase finishes completely (every agent it dispatched has reported) before the next phase starts. Each item lands
(or is parked) before the next item starts.

## Roles

| Role | Agent type | Job |
|---|---|---|
| Coordinator | the session running the loop | picks the item, writes briefs, decides, lands, commits; never implements |
| Fact finders | `sonnet-high` | reproduce, read history, read upstream; run probes and tests; report facts |
| Researcher | `opus-high` | reads the fact reports, looks upstream for a better fix, prototypes it, lists decisions |
| Implementer | `opus-medium` | builds the change from the brief in a private clone |
| Verifier | `opus-high` | attacks the change, expectation first; LAND / FIX / BLOCK |

## The phases (per item)

1. **Pick.** The first unchecked item in this order: "To do: found along the way", "To do: holes found re-checking
   the fixes", "To do: t3 robustness rows" (one area per item). Skip "Waiting on you" and everything below it.
   Check `git status` (other sessions work in this tree concurrently) and note `HEAD`.
2. **Fact finding.** Write a shared rules file (template below), then dispatch `sonnet-high` agents in parallel,
   usually three: **repro** (does it happen on main, how widely: a probe grid over every shape it can reach),
   **history** (which commit, spec, doc or test claims what; is a test pinning the current behaviour), **upstream**
   (what Django, strawberry-django, graphene-django, django-graphene-filters, DRF / django-filter do). Add a repro agent
   per sub-claim when one item bundles several. Wait for all of them.
3. **Research.** Hand every report to one `opus-high` agent: find the more elegant or more upstream-aligned fix
   nobody thought of, prototype it in its own clone, measure it against the repro grid, and list numbered
   decisions (D1, D2, ...) each with a recommendation.
4. **Rules check.** The coordinator rereads [AGENTS.md][agents], [START.md][start] and [GOAL.md][goal] and answers
   every open decision the rules settle (rule 37 / GOAL "Trust boundary" for "is it a defect", the north star and
   success criterion 7 for "which behaviour", AGENTS rule 5 for "same change or later", START for upstream audits,
   doc homes, test placement, exported surface).
   - Not a defect under rule 37: tick it in the tracker with the verdict and the evidence, no code. If it hides a
     real contract question, file that under "Waiting on you". Next item.
   - A decision only Rio can make (the rules do not settle it and the choice changes a public contract): move the
     item under "Waiting on you" with the question and the evidence. Next item.
5. **Plan.** Write the plan to the scratchpad (`<id>-plan.md`) and print it in chat: the defect, the decisions with
   their final answers and the rule behind each, what is out of scope (filed as new tracker items), the docs that
   change.
6. **Implement.** Make a fresh clone at `HEAD` and write the implementer brief (template below), starting from the
   researcher's patch. Dispatch one `opus-medium` agent with test runs authorized. A STOP from the implementer (a
   decision proves wrong against the code) comes back to the coordinator, who decides from the rules and the
   evidence and sends the ruling to the same agent (`SendMessage`), never a new one.
7. **Verify.** Dispatch one `opus-high` verifier with its own brief (template below). On FIX, rule on each finding
   and send the list to the same implementer, then send the delta back to the same verifier. Repeat until LAND.
   A docs-only last fix may be checked by the coordinator instead of a new verifier round.
8. **Land.** Apply the clone's `git diff HEAD --binary` to the shared checkout; it must apply cleanly and every
   path it touches must have been clean. Commit the fix (conventional subject, a body that states the new
   behaviour), then a tracker commit: tick the item with a one-line outcome and the fix hash, update the Progress
   counts, add out-of-scope questions under "Waiting on you", and add a "CHANGELOG entry for item N" item when
   consumers can see the change. No push, no branches, no CHANGELOG edit.
9. **Close.** Ask the implementer for `<id>-impl-feedback.md` (helpful / misleading / missing about the brief and the
   standing docs). Delete the item's clones, grids and patches; keep the reports, briefs and feedback. Print three
   lines: what landed, what got filed, what is next.

## Standing rules for every agent

- Read AGENTS.md, START.md and GOAL.md first.
- Work only in a private clone under the coordinator's scratchpad (`S/<id>-<role>`, made with
  `git clone -q --no-local <repo> S/<id>-<role>` then `uv sync -q`; assert `django_strawberry_framework.__file__`
  lies inside it). The shared checkout is read-only to every agent; only the coordinator writes it, at landing.
- Never touch `~/.t3/` (read-only), any `hunt-ws/`, or `~/dst-handoff/`. Never mention feedback.md / feedback2.md.
- Resource gate before every pytest run (35% free) and every basedpyright / `check_public_types` run (50% free); one
  heavy run at a time machine-wide. Pytest only `uv run pytest -q -p no:randomly --no-cov -n 2 <one file or node
  ids>`, never the full suite. Gate script (`S/gate.sh <percent>`):

  ```bash
  #!/bin/bash
  while true; do
    busy=$(ps -axo comm=,args= | awk '$1 !~ /(^|\/)(zsh|bash|sh|rg|grep|ugrep|awk|ps)$/ && /[p]ytest|[b]asedpyright/' | wc -l | tr -d ' ')
    free=$(memory_pressure | tail -1 | tr -dc '0-9')
    if [ "$busy" = "0" ] && [ "${free:-0}" -ge "$1" ]; then echo "gate open (free=${free}%)"; exit 0; fi
    echo "gate wait busy=$busy free=${free}%"; sleep 60
  done
  ```

- Downloads only PyPI wheels into a fresh empty dir; read them, never run them; Python reading them runs with `-I`.
- No commits, branches or stash in any clone. Delete only files you created.
- Reports are text in the final message: numbered FACTS with `path::Symbol` or command evidence and counts, then
  OPINIONS. The coordinator saves each report to `S/<id>-report-<role>.md`.

## Brief contents

- **Fact-finding rules file:** the item text verbatim, where its evidence may live (the t3 worktree, read-only),
  the doc and code paths to start from, why it matters under rule 37, "fact finding only, do not fix", the
  standing rules, the report format.
- **Implementer brief:** the clone path; the defects as facts with `path::Symbol`; the starting patch and what it
  is (unreviewed); the decisions as FINAL with their reasons; the STOP rule ("a decision proves wrong against the
  code, a pin moves, or a result that was correct at HEAD changes: stop that part and report with evidence");
  tests (live first, parametrized, exact query counts, package rows only for lines no live query reaches, real
  consumer shapes over monkeypatches); docs in the same change (README, GLOSSARY through the DB, specs, docstrings,
  test READMEs), no CHANGELOG; verification steps (ruff, trailing commas, citations, generators, pre-commit,
  each targeted test file alone, coverage of changed modules at 100%, the repro grid, `scripts/prove_failability.py`
  per fix, basedpyright main + floor, `check_public_types`, the Python 3.10 floor run last); the report format.
- **Verifier brief:** the clone is read-only (mutate a copy); write expectations from the implementer brief BEFORE
  reading the diff or the report; check every decision, try shapes the tests miss, rerun the grid, reproduce two
  mutations, judge every moved expectation, docs vs code, simplicity; verdict LAND / FIX / BLOCK with
  severity-ranked findings and minimal fixes.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[goal]: ../../GOAL.md
[start]: ../../START.md

<!-- docs/ -->
[fix-prompt]: FIX-PROMPT.md
[tracker]: bug_hunt-0_0_15_2.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
