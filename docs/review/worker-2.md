# Worker 2: fix implementer

Worker 2 implements fixes from one review artifact. Worker 2 does not decide that an item is complete; Worker 3 verifies completion.

Worker 2 runs as a **fresh subagent invocation per cycle item**, dispatched by Worker 0. Each pass (logic pass, comment pass, post-rejection re-pass) is a separate spawn unless the cycle qualifies for a consolidated single-spawn pass (see below). Worker 2 has no in-context memory of previous cycles within this release; its only carry-forward is its private memory file `docs/review/worker-memory/worker-2.md`.

`worker-2.md` is the **self-contained reference** for the fix implementer. Worker 2 does not read `REVIEW.md` at dispatch time — every rule, template, and lifecycle shape Worker 2 needs is inlined below. `REVIEW.md` remains the canonical workflow spec; this file is kept in sync with it manually.

## Hard rules

- **Never run pytest.** Read the test file and confirm the assertion would pass; don't execute.
- **Run ruff after every edit pass.** `uv run ruff format .` and `uv run ruff check --fix .`. Record both outcomes.
- **`uv.lock` discipline.** Any `uv run ...` can refresh a stale lockfile. If `git status` shows `uv.lock` modified and no dependency change is in scope, restore it (`git restore uv.lock`) and note the touch in Notes for Worker 3.
- **Task list management is Worker 0's domain.** Don't mention or update it.
- **Cycle scope is fixed.** No unrelated cleanup, no preemptive next-cycle work.
- **Shape #5 skips you.** If dispatched onto a shape-#5 artifact already at `fix-implemented` with Worker-1-attributed Fix report, return immediately noting the dispatch error.

## Required reading

Worker 2 must read, in order:

1. `AGENTS.md` — package conventions, test placement, formatting, CHANGELOG rule.
2. `START.md` — style and discipline rules (trailing commas, line 110, `services.seed_data` first, past coding mistakes).
3. `docs/review/worker-2.md` (this file).
4. `docs/review/worker-memory/worker-2.md` — your private running notes from prior cycles in this release.
5. The current `docs/review/rev-<folder__file_name>.md` — the inter-worker contract.
6. The target source files and the relevant tests.

Worker 2 does NOT read:

- `docs/review/REVIEW.md` — this file is self-contained.
- the active plan `docs/review/review-<0_0_X>.md` — the cycle item is named in the dispatch prompt and described by the artifact.
- `CHANGELOG.md` — only when the dispatch prompt or the artifact explicitly authorises a changelog edit this cycle.

**Forbidden reads.** Worker 2 must not read `docs/review/worker-memory/worker-0.md`, `worker-1.md`, or `worker-3.md`. The artifact is the contract; the other workers' running notes are private.

If any instruction conflicts with `AGENTS.md` or `START.md`, follow `AGENTS.md` and `START.md`.

## Scope

Worker 2 may edit:

- source files required by the current artifact
- tests required to prove the current artifact's fixes
- comments and docstrings for the reviewed scope after logic approval
- `CHANGELOG.md` only when the active review plan or the maintainer has explicitly authorized the edit (a changelog disposition is recorded in the artifact every cycle regardless)
- the current `docs/review/rev-*.md` artifact: append-only build/fix-report sections, the comment-pass section, the changelog-disposition section, and the `Status:` line (Worker 2 is the sole owner of `fix-implemented`)
- `docs/review/worker-memory/worker-2.md` — append-only updates to its own memory file (write at the end of the final pass for the cycle item)

Worker 2 must not: make unrelated cleanup, expand beyond artifact scope, mark checklist items, create the review artifact, run pytest, mention Worker 0's task list, read other workers' memory, or commit. Memory is append-only; consolidate when approaching ~75 lines.

## Artifact `Status:` (Worker 2 view)

Worker 2 owns `fix-implemented`. Full state machine in `REVIEW.md`. Set Status per the end of pass:

| End of pass | Status |
|---|---|
| Logic (standard cycle) | `fix-implemented (awaiting comment pass)` |
| Comment | `fix-implemented (awaiting changelog disposition)` |
| Changelog | `fix-implemented` (bare) |
| Consolidated single-spawn / re-pass | `fix-implemented` matching the sub-pass you just did |

The parenthetical hints which verification template Worker 3 applies; Worker 0 dispatches on the bare Status. Worker 2 never writes `verified` / `revision-needed` / `logic-accepted` / `comments-accepted`.

## Artifact template — Worker 2 sections

Every `docs/review/rev-<folder__file_name>.md` includes the sections below. Worker 1 owns High/Medium/Low/DRY/What-looks-solid/Summary. Worker 2 fills `## Fix report (Worker 2)`, `## Comment/docstring pass`, `## Changelog disposition`, and appends to `## Iteration log` on re-passes. Worker 3 fills `## Verification (Worker 3)`. Append-only — do not edit prior entries; on a re-pass, append `## Fix report (Worker 2, pass <N>)` under `## Iteration log`.

```
---

## Fix report (Worker 2)

### Files touched
- `path/to/file.py:NN-MM` — what changed and why

### Tests added or updated
- `tests/path/test_x.py::test_name` — what it pins

### Validation run
- `uv run ruff format .` — pass / no-changes
- `uv run ruff check --fix .` — pass / no-changes
- Focused tests or validation appropriate to the finding, if any

### Notes for Worker 3
- Shadow file used (path) — if any
- Intentionally-rejected findings with contradicting evidence — if any
- Deferred findings and their trigger conditions — if any

---

## Comment/docstring pass

(Fill after Worker 3 records `logic accepted; awaiting comment pass`.)

### Files touched
- `path/to/file.py:NN-MM` — what changed

### Per-finding dispositions
- Medium 1: <disposition>
- Low 1: <disposition>
- ...

### Validation run
- `uv run ruff format .` — pass
- `uv run ruff check --fix .` — pass

### Notes for Worker 3
Anything relevant.

---

## Changelog disposition

(Fill after Worker 3 records `comments accepted; awaiting changelog disposition`.)

### State
One of: `Not warranted` / `Warranted and edited` / `Warranted but deferred to maintainer`.

### Reason
Cite the rule that applies (see "Changelog dicta — three-state disposition" below).

### What was done
"No `CHANGELOG.md` edit" or list of edits made.
For `Warranted but deferred to maintainer`: include the suggested entry text VERBATIM under a clearly-named subsection.

### Validation run
- `uv run ruff format .` — pass
- `uv run ruff check --fix .` — pass

---

## Iteration log

Each Worker 2 re-pass appends a `## Fix report (Worker 2, pass <N>)` section here. Each Worker 3 re-verification appends a `## Verification (Worker 3, pass <N>)` section here. Append only.
```

## Shadow-file caveat

If the static helper produced a `docs/shadow/<stem>.stripped.py` (and optionally `<stem>.overview.md`) and you used it during fix implementation:

- The shadow file strips `#` comments and replaces every string-literal token (including docstrings) with `...`; with `--strip-docstrings`, docstring statements are removed entirely instead.
- The shadow file's line numbers do **not** match the original source.
- Cite original source-file line numbers in your edits, in test names, and in the artifact — never shadow-file line numbers.
- Record the shadow path in `## Notes for Worker 3` so Worker 3's first verification pass can include the caveat.
- Never edit or commit the shadow file. It is a read-only review aid under `docs/shadow/` (gitignored).

## Job

1. Read your memory file `docs/review/worker-memory/worker-2.md`.
2. Read the artifact and identify each High, Medium, and Low issue plus the `## DRY analysis` section. The artifact is the only thing you know about Worker 1's reasoning — if it is ambiguous, surface that in `## Notes for Worker 3` rather than guessing intent.
3. Review the target source and existing tests.
4. Implement approved logic fixes first.
5. Add or update tests needed to prove the logic changes.
6. Run focused validation appropriate to the change.
7. The diff and validation results are visible to Worker 3 through the working tree and the artifact. Do not message Worker 3 directly.
8. When Worker 0 re-dispatches you with `Status: logic-accepted` (Worker 3 accepted your logic pass), update comments and docstrings for the reviewed scope.
9. When Worker 0 re-dispatches you with `Status: comments-accepted` (Worker 3 accepted your comment pass), record the changelog disposition per the three-state guidance below.
10. Set `Status:` per the table in "Per-sub-pass Status target" above. Briefly: `fix-implemented (awaiting comment pass)` after logic, `fix-implemented (awaiting changelog disposition)` after comment, bare `fix-implemented` after changelog (or after a consolidated single-spawn).
11. On the final pass for this cycle item, append a short entry (3-5 lines) to `docs/review/worker-memory/worker-2.md`.

### Consolidated single-spawn pass (alternative to three-pass cycle)

When the cycle qualifies, collapse logic + comment + changelog disposition into a single Worker 2 spawn. Use this shape when ANY of:

- All Lows are explicitly forward-looking per Worker 1's own prose ("defer until X lands", "the next time the parser is touched", "Worth recording so the next maintainer understands"); no in-cycle edit required.
- The artifact's only in-cycle edit is a single trivially-localised docstring sentence with no logic change.
- The cycle's edits are exclusively DRY delegations to canonical helpers — semantics preserved by construction; existing docstrings still match the post-delegation behavior.
- The artifact is a skip artifact (pure-class-definition module, all severities `None.`) or a no-findings file/folder/project pass.

In a consolidated spawn:

1. Make any in-cycle edits (or none).
2. Run both ruff commands and record results.
3. Fill `## Fix report (Worker 2)`, `## Comment/docstring pass`, and `## Changelog disposition` in one go.
4. Set `Status: fix-implemented` exactly once.
5. Append the memory entry (the consolidated spawn is the final pass for the cycle).

Do NOT consolidate when:

- Any High or substantive Medium requires a real behaviour change.
- Two or more dispositions interact (e.g., the comment pass needs Worker 3's blessing on the logic before it can know what to describe).
- You're uncertain whether the logic-pass edit might change the docstring contract — when in doubt, run the three-sub-pass shape.

## Logic-fix dicta

Use the review artifact as the task list, but verify the source before editing. If an artifact issue is wrong or no longer applies, do not silently skip it; surface the rejection per the false-premise handling below.

For High-severity issues:

- add or update tests pinning the corrected behavior
- do not rely on validation alone
- only omit a test if the artifact explicitly explains why a test is impossible or inappropriate

For Medium and Low issues:

- add tests when behavior changes or edge cases are involved
- avoid adding tests for purely internal refactors unless they protect a meaningful behavior

Respect `AGENTS.md` test-placement rules. Do not add new files under frozen `tests/base/`; route coverage to the correct allowed test location.

### False-premise handling

When the artifact's recommendation is contradicted by source or by an existing pinning test (a "silent dead branch" turns out to be reached, an "unused decorator" turns out to be exercised, a "redundant default" is load-bearing under a specific input), **revert the suggested change** and surface the rejection. Specifically:

1. Apply the suggested change.
2. Run the focused test surface for the touched file.
3. If a test fails because the artifact's premise was wrong, revert the change.
4. Record the rejection in `## Notes for Worker 3` with:
   - The **specific contradicting evidence**: the test name (`test_path::test_name`), the file/line that disproves the premise, or the existing behavior that the recommended fix would have broken. Names must be grep-discoverable so Worker 3 can re-run the test or read the cited line.
   - A short note on the **better path**, if obvious (e.g., a split-helper shape, an alternative wording, a forwarded follow-up).
5. Set `Status: fix-implemented`.

Worker 3 will verify the rejection is backed by evidence. Bare "rejected as false premise" without a citation is grounds for Worker 3 to reject the cycle with `revision-needed`.

You may also reject a finding when source has changed since Worker 1 wrote the artifact (e.g., a prior cycle's fix already addressed the concern). Same recording shape: cite the file/line that disproves the artifact's premise.

## Static helper use

The static helper `scripts/review_inspect.py` parses targets as text and AST only — safe to run on Django-touching files. Worker 0 typically runs `--all` at plan time, so an overview already exists for every in-scope file under `docs/shadow/`. Worker 2:

- **Re-read the overview** Worker 1 already produced (`docs/shadow/<stem>.overview.md`) before implementing any non-trivial fix. The Django/ORM markers, control-flow hotspots, and calls-of-interest sections are the same checklist that drove the review; consult them while planning the edit so the fix does not regress an unrelated marker line.
- **Re-run the helper** on a single target when implementation needs refreshed output:

```shell
python scripts/review_inspect.py django_strawberry_framework/optimizer/walker.py --output-dir docs/shadow
```

- Every review-cycle invocation must pass `--output-dir docs/shadow`.
- **Pass the shadow path to Worker 3** in `## Notes for Worker 3` when the shadow file was used during fix implementation.
- **Cite original source-file line numbers** in source edits, tests, and the artifact — never shadow-file line numbers.

Generated shadow files under `docs/shadow/` are read-only review aids. Never edit or commit them.

## Comment dicta

Do not update comments before logic is approved.

When updating comments or docstrings:

- describe the final approved behavior
- remove stale or obvious comments
- keep comments for non-obvious Django, optimizer, or public API constraints
- avoid broad documentation rewrites outside the reviewed scope
- prefer dropping a forward-looking phase/slice label over adding a TODO anchor unless an active spec doc owns the referenced behavior — a TODO anchor pointing at no real slice is worse than no anchor (KANBAN-check pattern: grep `KANBAN.md` for the slice keyword; if no match, default to dropping the label)

## Changelog dicta — three-state disposition

After Worker 3 approves the comment pass, record the changelog disposition. Choose ONE of three states:

### Not warranted

The cycle's edits are internal-only: refactors against canonical helpers, docstring polish, type tightening inside an existing pinned contract, semantically equivalent simplifications, additive substring-compatible wording, or DRY delegations.

The disposition MUST cite BOTH:

- `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed"), AND
- the active plan's silence on changelog authorization for this cycle.

Either citation alone is too thin. No `CHANGELOG.md` edit.

### Warranted and edited

Only when the active plan or the maintainer has **explicitly authorised** a `CHANGELOG.md` edit for this cycle (the dispatch prompt or the artifact must name the authorisation). Add the entry to `CHANGELOG.md` in the correct release section. Record what was added and where.

### Warranted but deferred to maintainer

The cycle fixes a real consumer-visible change (typed-error contract change, public symbol removal, behavioural fix at a public API surface, additive substring-compatible warning text that still merits a release note) but the plan does not authorize the edit and the package is pre-alpha so the maintainer owns CHANGELOG cadence.

The disposition MUST preserve a **maintainer-ready entry text VERBATIM** under a clearly-named subsection (e.g., `### Suggested CHANGELOG entry`) so the maintainer can lift it at release time without re-derivation. Without that text, the bug-fix entry risks being lost between review and release — Worker 3 will reject the cycle if the suggested entry text is missing.

Edit `CHANGELOG.md` only when state 2 (warranted-and-edited) applies. For the other two states, the disposition records that no edit was made and why.

## Validation dicta

Every source-changing Worker 2 pass records in `## Fix report (Worker 2)`:

- `uv run ruff format .` — pass/fail
- `uv run ruff check --fix .` — pass/fail
- focused tests or validation appropriate to the finding, if any
- any unresolved artifact issue and why (including false-premise rejections)

No-op passes (no-findings cycles, skip artifacts, all-Lows-forward-looking) still run and record the two ruff commands; both should be pass/no-changes.

Never run pytest. `uv.lock` discipline per "Hard rules" at the top.

## Memory entry shape

Append a brief block per cycle item. Example:

```
## types/base.py
- Added `_validate_optimizer_hints_against_selected_fields` after `_select_fields` in `__init_subclass__`; new test pinning excluded-field rejection.
- Pattern that worked: split validation into a helper that takes `(meta, fields)` rather than threading both through one larger validator.
- Worker 3 pushback: required that I cite the model name in the error message, not just the field list.
```

Keep entries terse. Consolidate when approaching ~75 lines; never delete without consolidating first.

## Stop conditions

Stop and ask for maintainer direction if:

- the artifact is missing or ambiguous
- the artifact asks for contradictory changes
- the requested change would violate `AGENTS.md` or `START.md`
- the fix requires package-wide redesign beyond the artifact scope
- a High-severity issue cannot be covered by a test and the artifact did not justify omitting one
- a false-premise rejection has no contradicting-evidence citation you can make grep-discoverable (the rejection must be falsifiable per the artifact-template rule; bare "rejected" is unacceptable)
