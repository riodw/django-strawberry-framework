# Build: Final test-run gate (spec-023 multi_db)

Spec reference: `docs/SPECS/spec-023-multi_db-0_0_7.md` (whole file)
Status: final-accepted

Run by Worker 1 per `docs/builder/BUILD.md` `## Final test-run gate` and `docs/builder/worker-1.md` `## Final test-run gate`, after `docs/builder/bld-integration-023.md` closed `final-accepted`.

## What this gate is gating

This cycle's entire diff is three documents:

| Path | State | Bytes now (`wc -c`) |
|---|---|---|
| `docs/SPECS/spec-023-multi_db-0_0_7.md` | tracked, modified | 113,712 |
| `docs/SPECS/appx/spec-023-multi_db-0_0_7-rationale.md` | untracked, new | 107,160 |
| `docs/SPECS/appx/spec-023-multi_db-0_0_7-terms.csv` | tracked, modified | 2,679 |

`git diff HEAD --stat` over the two tracked paths: **129 insertions, 237 deletions across 2 files**. `git status --short` filtered to `*.py` is **empty** — no Python, no source, no test, in the whole cycle.

## Spec status-line re-verification (per-spawn obligation)

`docs/SPECS/spec-023-multi_db-0_0_7.md:1-6` re-read at the start of this pass, after the integration pass's edits. Title, `Target release`, `Status: shipped (0.0.7) … Its deliberative layer … lives in [spec-023-multi_db-0_0_7-rationale.md]`, `Owner`, `Predecessors` all describe the build's current state. **No edit required this pass.**

## Gate results

Every command as run, from the repository root, in the order `docs/builder/BUILD.md` gives.

| # | Command | Result |
|---|---|---|
| 1 | `uv run ruff format --check .` | **PASS** — `424 files already formatted` (plus ruff's standing `COM812`-vs-formatter advisory, which is a configuration warning, not a failure; exit 0) |
| 2 | `uv run ruff check .` | **PASS** — `All checks passed!` exit 0 |
| 3 | `git diff --check` | **PASS** — no output, exit 0. No whitespace error and no conflict marker anywhere in the tree, this cycle's files or the concurrent session's. |
| 4 | `uv run python scripts/check_trailing_commas.py --check` | **FAIL as invoked repo-wide (1 violation), attributed below; PASS over every tracked file and over this cycle's diff** |
| 5 | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-023-multi_db-0_0_7.md` | **PASS** — `OK: 18 terms - all have glossary entries and at least one spec link.` exit 0 |

### Command 4, in full

The repo-wide invocation reports exactly one violation:

```
.claude/projects/-Users-riordenweber-projects-django-strawberry-framework/memory/one-spec-owns-each-feature.md:20: should carry the canonical LINK-DEFINITIONS footer scaffold (all category markers)

1 layout violation(s); run with --fix to resolve
```

**Attributed, not fixed.** The file is not this cycle's, not the concurrent session's, and not the repository's:

- **Untracked** — `git ls-files --error-unmatch <path>` -> `Did you forget to 'git add'?`.
- **Git-ignored** — `git check-ignore -v <path>` -> `.gitignore:170:.claude/`. The whole `.claude/` tree is ignored.
- **Predates this cycle** — `ls -la` gives an mtime of Aug 14 10:19; this cycle ran Aug 18.

It is an agent's local auto-memory topic file that the checker's directory walk reaches because the walk does not consult `.gitignore`. Nothing in the repository can be committed from it and nothing this cycle wrote touched it. `AGENTS.md` rule 34 forbids reverting or tidying files that are not this task's, and this one is not even a repository file.

The gate that matters is therefore re-run twice, scoped:

- **Every tracked candidate file** — `uv run python scripts/check_trailing_commas.py --check $(git ls-files '*.md' '*.py' '*.csv')`, **859 files** -> exit **0**.
- **This cycle's diff** — `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-023-multi_db-0_0_7.md docs/SPECS/appx/spec-023-multi_db-0_0_7-rationale.md docs/SPECS/appx/spec-023-multi_db-0_0_7-terms.csv` -> exit **0**.

This is the gate that actually covers this cycle: ruff is Python-only and every file this cycle touched is Markdown or CSV, so command 4 is the only lint that reads the diff at all. It passes on the diff, on every tracked file, and fails only on a git-ignored non-repository file. **Not a blocker for `final-accepted`.**

## Commands deliberately not run, and the authority for that

These are decided answers, not omissions.

### `uv run pytest --no-cov` (the full sweep)

**Not run.** `AGENTS.md` #"No pytest after edits" — "No pytest after edits; run only when explicitly asked (then `uv run pytest`)" — governs, and `docs/builder/worker-1.md` `## Required reading` says in terms: "If any instruction conflicts with `AGENTS.md` or `START.md`, follow `AGENTS.md` and `START.md`." `START.md` `## Workflow rules they've set` restates it as the rule it most often forgot. `docs/builder/BUILD.md`'s gate is the conflicting instruction and it loses.

The maintainer has not asked for a run this cycle. Independently of the precedence question, a suite run could neither confirm nor refute anything this cycle changed: **the diff contains zero Python**, so no test's behavior is reachable from it. A green sweep would be evidence about the concurrent session's tree, not about this build.

### `uv run python examples/fakeshop/manage.py check` and `… makemigrations --check --dry-run`

**Not run**, for the same two reasons. `START.md` names them in the same breath as the pytest ban ("No `pytest`. No `manage.py check`. No `uv build`."). Their purpose in the gate is to catch model / admin / url-config drift; this cycle modified no model, no admin, no URLConf, and no settings module, so there is no drift for them to catch. Running them would additionally exercise `examples/fakeshop/db.sqlite3`, which the build plan lists as concurrently written by the other session and which this cycle must not touch.

### Coverage

No `--cov*` flag was passed to anything, in this pass or either slice (`docs/builder/worker-1.md` `## Scope`; `docs/builder/BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool`).

## Floor verification

`docs/builder/build-023-multi_db-0_0_7.md` preamble declares: `Floor-verification scope: none. No slice touches a Django / Strawberry / channels integration seam; the cycle writes Markdown only.`

**Confirmed against the actual diff, not against the declaration.** `docs/builder/BUILD.md` `### When it is required` lists the seams: request/response handling, view or ASGI plumbing, upload or body parsing, session/auth surface, queryset or expression compilation, schema and type construction against Strawberry internals, consumer or middleware wiring. The diff touches none of them because it touches no executable code at all — `git status --short` filtered to `*.py` is empty, and the three changed paths are two `.md` and one `.csv`. There is no focused test scope a floor run could even be pointed at.

No floor venv was created and the shared `.venv` was not mutated, installed into, or downgraded by any pass in this cycle.

**No floor-verification scope declared.**

## Hot-path budget

The plan declares `Hot-path declaration: none. No production code is planned; nothing runs per request, per resolver, or per row.` Confirmed the same way: no production code exists in the diff. Not applicable.

## Slice checklist audit

`docs/builder/build-023-multi_db-0_0_7.md` `## Checklist` carries four boxes. Worker 0 owns the ticks; this section is Worker 1's audit of whether each contract landed.

| Box | Ticked | Contract landed? |
|---|---|---|
| Slice 1: Rationale extraction | `- [x]` | **Yes.** `docs/SPECS/appx/spec-023-multi_db-0_0_7-rationale.md` exists (107,160 bytes) carrying the five-revision history, nine Decision entries, and the moved justifications; `grep -oE 'rev[0-9]' docs/SPECS/spec-023-multi_db-0_0_7.md \| wc -l` -> 0. |
| Slice 2: Spec reconciliation | `- [x]` | **Yes.** Audited claim by claim in `docs/builder/bld-integration-023.md` `### Deferred follow-up walked`; every inherited D-finding re-derived and confirmed closed. |
| Cross-slice integration pass | `- [ ]` | **Landed this cycle** — `docs/builder/bld-integration-023.md`, `Status: final-accepted`. Worker 0 ticks it. |
| Final gate | `- [ ]` | **This artifact.** Worker 0 ticks it. |

Neither slice artifact left a `- [ ]` in its own `### Spec slice checklist (verbatim)`; both quote the plan's slice line and both are `- [x]`. No silently un-ticked, undeferred box exists.

## Failability proofs and fail-open shapes

`Not applicable; this cycle introduced no new boundary, guard, gate, or rejection path.` It added no executable code of any kind, so there is nothing whose removal could be mutated and nothing whose failure could be fail-open. The two `docs/builder/worker-1.md` `### Failability and fail-open checks` confirmations are vacuous rather than waived.

## Relocation / promotion claims

One relocation claim exists in this cycle and it is the cycle's central act: Slice 1's assertion that the deliberative layer was **moved**, not copied and not summarized. `docs/builder/worker-1.md` `### Verifying relocation / promotion claims` requires Worker 1 to run its proof rather than accept the acceptance.

Proved mechanically at the integration pass rather than on prose (`docs/builder/bld-integration-023.md` `### Cross-file duplication`): exact long-sentence overlap between spec and rationale is **0**, and the longest shared word-shingle run is **33 words**, every one read and accounted for as a link-definition tail, a quoted out-of-scope enumeration, or a short mechanism restatement the rationale needs verbatim. Text that landed in the rationale left the spec. Slice 1's own structural guarantee is consistent with the measurement — its `cut.py` captured the excised blocks to JSON and deleted them in the same run, so no block was retyped and none could survive in both files.

## Deferred work catalog

Three items. Each was **re-derived against the current tree in this pass** before being listed — a catalog is a claim, and prior cycles here have shipped catalogs with wrong populations and hazards that did not exist.

- **The shipped `docs/GLOSSARY.md` axis-3 sentence still lacks the plan-time qualifier.** Source: `docs/builder/bld-slice-2-023-spec_reconciliation.md` `### D2 — axis 3 is alias-LATE, not alias-absent` (in the rationale) and its `### Spec changes made (Worker 1 only)` row for `### Decision 3` axis 3. Licensing clause: none in the spec — the deferral is the build plan's `### Baseline-dirty out-of-scope files`, which lists `docs/GLOSSARY.md` as concurrently written and un-editable this cycle. **Re-derived:** `docs/GLOSSARY.md:1382` reads "generated `Prefetch` child querysets do NOT inherit the root alias" — 1 occurrence, no qualifier — while `CHANGELOG.md:173` already carries "at plan-construction time" and the spec now states the plan/fetch boundary at seven sites. The GLOSSARY line is not *wrong* (it describes the plan, which is what the entry describes) but it is the only one of the three shipped surfaces without the qualifier, so it is the one a reader can misread as a fetch-time promise. **Work:** add "at plan-construction time" to the glossary app's DB entry and re-render with `scripts/build_glossary_md.py` — a DB edit plus a regenerate, never a hand-edit of the rendered file (`START.md` `## Rendered docs — fix the source, not the file`).
- **`_visible_related_object`'s alias re-pin is in the spec but not in the GLOSSARY entry.** Source: same slice, `### D6 — the resolver-level alias re-pin, added without a fifth axis`. Licensing clause: same baseline exclusion; additionally, the spec's own `### Decision 3` closing paragraph pins the constraint that made it un-addable here — the re-pin is an *instance* of axis 3's alias-late principle, not a fifth axis, and "four axes" is load-bearing in both the shipped GLOSSARY entry and `CHANGELOG.md:173`. **Re-derived:** `grep -c '_visible_related_object' docs/GLOSSARY.md` -> **0**; `grep -c 'alias-late\|plan-construction' docs/GLOSSARY.md` -> **0**. **Work:** if a future card wants the behavior discoverable from the glossary, it adds a sentence to the entry's DB row as a refinement of axis 3 and regenerates. Explicitly **not** a fifth axis — a card that adds one would put three shipped surfaces out of step. This is a discoverability improvement, not a correctness gap: the behavior is contract in the spec and shipped in `types/resolvers.py::_visible_related_object`.
- **A dead `KANBAN.md` locator inside the rationale's moved Decision 9 justification.** Source: `docs/builder/bld-integration-023.md` `### F5`. Licensing clause: none — this is a Worker 1 disposition, recorded rather than patched. **Re-derived:** the cited substring `The last \`0.0.7\` card to ship owns the version bump` has **0** occurrences in the current `KANBAN.md` and **0** at HEAD (`git show HEAD:KANBAN.md | grep -c 'owns the version bump'`), so it was already dead when Slice 1 moved the block. Repair is blocked from both sides: the citation sits in moved-verbatim deliberation, which `docs/builder/worker-1.md` rule 4's append-only discipline protects from rewriting, and `KANBAN.md` is DB-rendered and on this cycle's do-not-touch list. **Work, if a future card wants it:** re-point the locator at `docs/SPECS/spec-020-list_field-0_0_7.md` Decision 10, which the same sentence already names as the policy's true source. Low value — the substance survives the dead locator, since the joint-cut policy is stated normatively in the spec's own `### Decision 9`.

Two items that look like deferrals and are **not**, checked so a later reader does not re-open them:

- `## Implementation plan`'s line-delta table (`+180 / -0`, `+160 / -0`, `+22 / -6`, "~380 lines"). Recorded in the rationale's `### Deliberately not changed` and re-read this pass: it is a planning estimate inside the plan record, not a claim about `HEAD`, and the shipped delta is not measurable as one figure. **Decided, not deferred.**
- Every `- [ ]` checkbox in the shipped spec. The `Status:` line is the source of truth for a shipped card; unticked boxes in an archived spec are the house convention. **Decided, not deferred.**

## Integration-pass fixes carried into this gate

`docs/builder/bld-integration-023.md` found six items and fixed five inside Worker 1's writable set. They are re-verified here rather than accepted from that artifact:

- Anchors / references, spec and rationale: `in-page unresolved: none`, `used-not-defined: none`, `defined-not-used: none`; 0 missing definition paths; 0 broken cross-file `#fragment`.
- Duplicate link-definition targets: **0** in both files (7 in the rationale before F4).
- `#"substring"` citations: spec **47**, 0 broken (F3 fixed the `docs/TREE.md` locator). Rationale **22**, 1 broken — F5, catalogued above.
- Staged anchors naming this build: `grep -rEn 'TODO\(spec-023|TODO-(ALPHA|BETA|STABLE)-023' .` -> **0 lines**, before any exclusion.
- `grep -oE 'rev[0-9]'`: **0** in the spec, **0** in the terms CSV.
- `grep -o 'four axes'` -> **6**; `grep -oi 'five axes\|fifth axis'` -> **0**. F6's fix did not disturb the framing the shipped GLOSSARY and CHANGELOG share.
- `grep -oE '\([a-g]\)'` in the spec -> **40** occurrences, `(g)` **0**, all resolving to the six-test a-f layout.

## Concurrent-session baseline

The tree is legitimately dirty with another session's `spec-021` / `spec-022` cycle throughout: modified `CHANGELOG.md` (went dirty during this pass), `KANBAN.html`, `KANBAN.md`, `docs/GLOSSARY.md`, `docs/SPECS/appx/spec-021-apps-0_0_7-terms.csv`, `docs/SPECS/spec-021-apps-0_0_7.md`, `docs/SPECS/spec-022-export_schema-0_0_7.md`, `docs/builder/bld-final.md`, `docs/builder/build-021-apps-0_0_7.md`, `docs/feedback.md`, `examples/fakeshop/db.sqlite3`; deleted `docs/builder/bld-integration.md`, `bld-review-1-rationale_and_spec_reconciliation.md`, `bld-review-2-db_backed_doc_reconciliation.md`, `docs/builder/build-020-list_field-0_0_7.md`; untracked `docs/SPECS/appx/spec-022-export_schema-0_0_7-rationale.md`, `docs/builder/DONE/build-020-list_field-0_0_7.md`, `docs/builder/build-022-export_schema-0_0_7.md`.

**No gate command failed in any of those files.** Commands 1, 2, 3 and 5 pass outright, and command 4's single violation is in a git-ignored `.claude/` memory file that belongs to neither session. Nothing of the other session's was edited, reverted, or read for content.

## Closeout

**Not performed, by maintainer instruction.** No edit was made to `docs/builder/BUILD.md`, `docs/builder/ARTIFACT.md`, or any `docs/builder/worker-*.md` role file. `docs/builder/build-023-multi_db-0_0_7.md` is Worker 0's and was not edited; its last two boxes stay `- [ ]` for Worker 0 to tick. No retrospective, no artifact cleanup, no KANBAN or CHANGELOG movement.

## Gate outcome

Commands 1, 2, 3 and 5 pass. Command 4 passes over every tracked file (859) and over this cycle's three-file diff, failing only on a git-ignored non-repository file that predates the cycle — attributed, not fixed, and not a blocker. Floor-verification scope is `none` and confirmed against the diff. Hot-path declaration is `none` and confirmed. No failability proof is owed. Three deferred items catalogued, each re-derived. No re-loop; no slice owns a failing behavior, because nothing failed.

Uncommitted and left dirty for the maintainer: `docs/SPECS/spec-023-multi_db-0_0_7.md`, `docs/SPECS/appx/spec-023-multi_db-0_0_7-rationale.md` (new), `docs/SPECS/appx/spec-023-multi_db-0_0_7-terms.csv`, and the four `docs/builder/*-023*.md` cycle artifacts. Worker 1 does not commit.

`Status: final-accepted`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
