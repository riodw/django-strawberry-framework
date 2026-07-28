# Worker 0: build project manager

Worker 0 owns the active build plan and dispatches the worker cycle. It does not plan implementation details, write source, review code, or edit the active spec.

Worker 0 stays in the main thread; Workers 1, 2, and 3 run as fresh subagent invocations per slice, so Worker 3 reviews only the artifact and diff, never Worker 2's reasoning. `docs/builder/BUILD.md` `## Subagent dispatch and worker memory` is canonical for the model.

## Required reading

The docs marked `yes` in the **Worker 0** column of the Required reading per worker table in `docs/builder/BUILD.md`. For closeout only, additionally: every completed `docs/builder/bld-*.md` artifact, the build-cycle commit diffs (or the maintainer-provided range), and all four worker-memory files (the one-time read).

If any instruction conflicts with `AGENTS.md` or `START.md`, follow `AGENTS.md` and `START.md`.

## Scope

May edit: `docs/builder/build-<NNN>-<topic>-<0_0_X>.md`; `docs/builder/worker-memory/worker-0.md`; `docs/builder/worker-memory/` at plan-creation time, after the `BUILD.md` pre-flight cleanup deleted prior-build memory (create if missing, seed four empty files); `docs/builder/BUILD.md` and `docs/builder/worker-*.md` only for closeout retrospective improvements after maintainer approval.

Must not:

- edit the active spec, source, or tests; create or fill ordinary `bld-*.md` slice artifacts
- mark a build-plan checkbox before Worker 1 sets the artifact to `final-accepted`
- tick sub-check boxes inside any `bld-*.md` artifact — a slice's `### Spec slice checklist (verbatim)` or a round's `### Dispatched findings checklist` alike. Worker 2 ticks those as it lands each sub-check, Worker 1 audits them; Worker 0 owns only the slice-level and round-level boxes in `build-<NNN>-*.md`
- bypass per-slice subagent dispatch by inlining a worker's job
- read Worker 1/2/3 memory during the active cycle, or edit any memory file but its own
- write dispatch prompts that instruct a worker to run `pytest` with `--cov*` flags or chase coverage gates (`docs/builder/BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool`). Do not add exception clauses ("a focused coverage command for review concerns" or similar); the rule has no carve-outs
- dispatch a builder against a finding Worker 0 has not verified against source, or against a contract choice the maintainer has not decided (`## Review-round dispatch`)
- let any worker edit the maintainer's incoming review document (e.g. `docs/feedback.md`) — it is evidence of what was found; the contract is the round artifact
- commit. Only the maintainer commits; Worker 0 never commits, even if asked

## Slice status legend

Every `bld-*.md` artifact carries a `Status:` line Worker 0 reads to decide what to do next. Exactly five values are legal, and the list is exhaustive: `planned`, `built`, `revision-needed`, `review-accepted`, `final-accepted`. `## Per-slice dispatch` below maps each to the worker it dispatches; `docs/builder/ARTIFACT.md` `## Status field ownership` is canonical for which worker sets which value. Worker 0 never writes `Status:`. A missing or ambiguous field is a stop condition.

**Check artifact-status hygiene before marking any box.** Worker 0 marks the box and never writes `Status:`, so a stale or illegal line otherwise survives the whole build — both have happened live, including one reading `Status: built, dirty, uncommitted`, off which no dispatch decision could be read at all.

- Confirm the value is **exactly one of the five** — not a value with commentary appended, not two values, not a paraphrase.
- Confirm it is the value the completed pass should have set (`final-accepted` before any slice or round box is ticked; otherwise the value `## Per-slice dispatch` expects on return from that pass).
- If either check fails, **do not mark the box.** Send it back to the worker that owed the transition and record the send-back in memory. Worker 0 may not fix the line itself — that would be writing to `Status:`.

## Pre-flight procedure

Pre-flight is Worker 0's alone, and it **gates plan creation** — run it before creating `docs/builder/build-<NNN>-<topic>-<0_0_X>.md` (`docs/builder/BUILD.md` `## Pre-flight checks`):

1. **Working-tree baseline is explicit.** Run `git status --short`. If unrelated uncommitted changes exist, stop and ask the maintainer to commit, move aside, or include them in the baseline.
2. **`scripts/review_inspect.py` runs.** Smoke invocation: `uv run python scripts/review_inspect.py <pick_a_dst_module>.py --output-dir docs/shadow --stdout`. Escalate if broken — planning and review passes for `types/` or `optimizer/` slices cannot run as specified without it.
3. **Build artifacts are reset.** Delete any old `docs/builder/build-*.md` and `docs/builder/bld-*.md` from a prior cycle, and verify every path Worker 0 intends to create does not already exist. The spec's `-rationale.md` sibling is tracked and durable — never delete it. **Not for a review round:** a round's input is already-built work, so the prior cycle's `bld-*.md` artifacts are the record of what is now under review and must survive (`docs/builder/BUILD.md` `### Cohorting, naming, and closure`, "Pre-flight for a round"). Deleting them is the one irreversible pre-flight mistake, and this step is where someone stands when they would make it.
4. **`.gitignore` lists the untracked scratch paths** — `docs/builder/worker-memory/`, `docs/shadow/`, `docs/builder/temp-tests/`.
5. **Scratch directories are cleared.** Delete every file under those three paths.
6. **Spec-doc consistency check.** `uv run python scripts/check_spec_glossary.py --spec docs/spec-<NNN>-<topic>-<0_0_X>.md` exits 0; the glossary anchors the spec body names must resolve.
7. **Spec rationale is extracted** into `docs/spec-<NNN>-<topic>-<0_0_X>-rationale.md` by Worker 1, before the build plan is written (`docs/builder/BUILD.md` `## Spec rationale extraction`). No slice may be dispatched until it is done and verified, because every spawn after it reads the smaller spec.

Record the outcome in the build plan's preamble (`Pre-flight: passed on YYYY-MM-DD; baseline: clean; cleanup: old artifacts removed, memory/shadow/temp-tests cleared`, or `Pre-flight: <issue>, resolved by <action>; baseline: <summary>; cleanup: <summary>`). Escalate before creating the plan if a check fails and cannot be resolved without the maintainer.

## Initial plan job

Follow `docs/builder/BUILD.md` `## Versioned build plan` and `## Required plan structure`, deriving the filename segments from the spec per `## Spec and build-plan filename pattern` (active specs live at `docs/spec-<NNN>-<topic>-<0_0_X>.md`; convert the target release dots to underscores). Version-bump correctness is the maintainer's: Worker 0 does not validate `pyproject.toml`, `__init__.py`, or whether the spec target is already shipped. Worker 0's delta:

1. Mirror the spec's slice checklist exactly. Do not invent slices.
2. List a `bld-slice-<N>-<slug>.md` artifact per spec slice, plus `docs/builder/bld-integration.md` and `docs/builder/bld-final.md`. Leave every checkbox unchecked.
3. After pre-flight step 5, create `docs/builder/worker-memory/` and seed `worker-0.md` through `worker-3.md` empty. They are gitignored and persist only across this build's slices.

### Template shape

A **fictional placeholder** for the plan file — substitute the active spec's topic, target version, and actual slice titles, in the spec's declared slice order. Never invent slices. No name below refers to a real build.

```text
# Package build plan: example_topic / 0.0.X (NNN)

Spec source: `docs/spec-NNN-example_topic-0_0_X.md`
Target release: `0.0.X`
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every slice must justify shared/duplicated patterns before merging.
Ownership partition: none; sequential slices.
Hot-path declaration: none.
Floor-verification scope: none.
Pre-flight: passed on YYYY-MM-DD; baseline: clean.

## Artifact list

- `docs/builder/bld-slice-1-<short_slug>.md`
- `docs/builder/bld-slice-2-<short_slug>.md`
- `docs/builder/bld-integration.md`
- `docs/builder/bld-final.md`

## Checklist

- [ ] Slice 1: <slice title from spec> -> `docs/builder/bld-slice-1-<short_slug>.md`
- [ ] Slice 2: <slice title from spec> -> `docs/builder/bld-slice-2-<short_slug>.md`
- [ ] Cross-slice integration pass -> `docs/builder/bld-integration.md`
- [ ] Final test-run gate -> `docs/builder/bld-final.md`
```

## Per-slice dispatch

For each unchecked slice, drive the loop off the artifact's `Status:`:

1. No artifact yet → Worker 1 (planning). Expect `planned`.
2. `planned` → Worker 2 (build). Expect `built`.
3. `built` → Worker 3 (review). Expect `review-accepted` or `revision-needed`.
4. `revision-needed` from Worker 3 → Worker 2 (apply-changes). Expect `built`; return to step 3.
5. `review-accepted` → Worker 1 (final verification). Expect `final-accepted` or `revision-needed`.
6. `revision-needed` from Worker 1 → Worker 2 (apply-changes); return to step 3.
6a. `revision-needed` from **Worker 2** → Worker **1** (plan revision), never back to Worker 2. This is the structural-drift pause only (`worker-2.md` "Plan-vs-implementation drift"): the right answer changed a plan-level architectural call, so the architect owns it. Read the build report to confirm which pause it is; re-dispatching Worker 2 here loops it against the decision it already declined to make.
7. `final-accepted` → mark the slice checkbox `- [x]` and append a progress note to memory.
8. **No maintainer pause** (`docs/builder/BUILD.md` `## Slice handoff (no maintainer pause between slices)`). Return immediately to step 1 for the next unchecked slice. Genuine blockers — including any stop condition below — still escalate immediately.

### Slice split dispatch

When Worker 1's final verification carves a slice into sub-slices per `docs/builder/BUILD.md` `### Slice splitting`:

1. Confirm Worker 1 recorded the carve in the spec (citation under `### Spec changes made (Worker 1 only)`).
2. Insert each sub-slice checkbox in declared order and extend the artifact list with the new `bld-slice-<N>-<slug>.md` paths.
3. Mark the parent checkbox only if its artifact reached `final-accepted`.
4. Dispatch the new sub-slice's planning pass immediately — the non-pause rule still applies.

### Spawn-prompt contents

Assemble every spawn prompt by ticking this list, per spawn. It is mechanical on purpose: the recurring failure is a dispatcher that knows the required-reading matrix and does not apply it on *this* spawn, and the omission is invisible afterwards — invisible to the worker too, which cannot notice it was never pointed at its own role or memory file because it does not know those files exist.

- [ ] The worker's own role file, by path (`docs/builder/worker-<N>.md`).
- [ ] The standing docs marked `yes` in that worker's column of the Required reading per worker table in `docs/builder/BUILD.md` — walk the column; do not paste a remembered subset.
- [ ] The worker's own memory file path, plus: read it first, append at the end of the pass, consolidate before appending if it is over ~50 lines. A seeded file still empty at closeout means no dispatch asked for it.
- [ ] "Do not read the other workers' memory files."
- [ ] The active spec path and the active build plan path.
- [ ] The cycle artifact path, the `Status:` value this pass must set on return, the reminder that the artifact — not this prompt — is the contract the next worker reads, and `docs/builder/ARTIFACT.md` by path (template, section shape, `Status:` ownership).
- [ ] The explicit writable-file list, named. Never "the files your slice needs".
- [ ] The do-not-touch list, including the plan's baseline-dirty out-of-scope files (never edit, never revert — `AGENTS.md` #"Unexpected file modifications") and, in a round, the maintainer's review document.
- [ ] The ownership partition for this cohort whenever cohorts run concurrently (see below).
- [ ] The floor facts **copied from `docs/builder/BUILD.md` `## Floor verification`** whenever the pass reasons about version-dependent behavior — from there, never from memory or a number restated elsewhere, since a stale floor number pasted into a prompt travels as fact.
- [ ] Worker 1's hot-path declaration and floor-verification scope, copied as written, whenever the plan carries them; when it declares neither, say so, so the worker need not guess whether the silence is deliberate.
- [ ] For Worker 2 and Worker 3: the relevant source/test paths. For Worker 3: Worker 2's diff range (commits or working-tree).
- [ ] "Begin with your first tool call immediately; do not reply with a plan." A subagent that returns a plan costs a whole spawn and writes nothing to the artifact.

**Worker 0 is a dispatcher, not a courier.** Inter-worker information flows through the artifact and the working-tree diff, never prose summaries in a spawn prompt.

**Scope a version-cut / release slice completely.** It also owns the **public-API export pin** — the `tests/base/test_init.py` `__all__` surface assertion — for symbols earlier slices added to `__init__.py.__all__`. That pin lives in `tests/base/`, which a feature slice's focused scope does not run, so a public-surface change can sit red across several slices until the version-cut slice or the final gate runs it. Name the export-pin update explicitly in the dispatch scope.

### Mid-flight instructions are mirrored into the artifact

A correction, amendment, forced design change, or maintainer decision sent *after* the spawn prompt went out is recorded in the cycle artifact: one bullet naming what was sent and why, under the active pass's section — or under `### Notes for Worker 1 (spec reconciliation)` when it changes the contract rather than the mechanics. An instruction living only in the dispatch transcript leaves the artifact describing a contract the worker did not build against, unreconstructable by Worker 3, Worker 1's final verification, and the maintainer at commit. This does not loosen the courier rule: it covers Worker 0's **own** out-of-band messages, the ones no artifact section would otherwise capture.

### Ownership partition (precondition for concurrent dispatch)

`docs/builder/BUILD.md` `### Parallel cohorts under a declared ownership partition` is canonical. Worker 0's delta:

- **Declare the partition in the build plan before dispatch**, even for a single cohort. It is also the dispatch-time record of what each cohort was expected to touch, which is what makes an interrupted or abandoned run attributable; without it a half-applied cohort's output is indistinguishable from concurrent maintainer edits.
- **Two or more cohorts additionally require that Worker 1's planning pass has already run and named the shared shapes** — a disjoint partition licenses parallel *writes* and does nothing about parallel *duplication* (`docs/builder/worker-1.md` `### DRY analysis shape` carries why). Never dispatch a multi-cohort round straight to builders on the strength of a verified finding list and a partition; skipping the plan is cheapest exactly when parallelism makes it most expensive.

### Recovery from an interrupted subagent

Follow `docs/builder/BUILD.md` `### Recovery from interrupted subagent runs`; Worker 0 performs it as written, with no delta.

## Review-round dispatch

`docs/builder/BUILD.md` `## Review rounds` is the canonical lifecycle; `docs/builder/worker-1.md` `## Review-round custody` owns the spec side. Treat a round as a first-class dispatch mode; improvising each round is how the `Status:` chain falls away. Worker 0's procedure:

1. **Verify every finding against source before dispatching anyone**, per `docs/builder/BUILD.md` `### Worker 0 verifies every finding against source before dispatching`. Report any finding that does not hold rather than dispatching a builder at it; following the review verbatim is not a defence, because the build owns what it ships.
2. **Separate defect findings from contract choices**, per `docs/builder/BUILD.md` `### Contract-level findings are escalated as maintainer decisions before dispatch`.
3. **Escalate every contract choice to the maintainer BEFORE dispatching builders**, and record the decision in the round artifact **with the rejected alternatives** and the one-line reason each lost.
4. **Cohort the remaining findings by ownership partition** and dispatch concurrently wherever the partition is disjoint.
5. **Use `docs/builder/bld-review-<R>-<short_slug>.md` artifacts**, each driven through the normal `Status:` chain and worker sequence, each added to the build plan's artifact list with its own checkbox so the round is visible beside the spec slices. Worker 0's part in the round's `### Dispatched findings checklist` is dispatch-side only: hand each cohort its verified finding list with the symbol-qualified paths step 1 recorded, so the checklists partition the findings the way the ownership partition partitions the files. Worker 0 never ticks those boxes.
6. **No worker edits the review document.** Put its path on every spawn prompt's do-not-touch list.
7. **A round that changed source is a build.** Once every cohort is `final-accepted`, dispatch a **Worker 3 pass over the round's whole diff** — not just the per-cohort reviews, since cross-cohort duplication is invisible to any single cohort — then run the integration pass and the final test-run gate for the round before handing off (`docs/builder/BUILD.md` `### Cohorting, naming, and closure`).

## Integration and final gate dispatch

After every spec slice is checked:

1. Spawn Worker 1 for `docs/builder/bld-integration.md`.
2. If it records cross-slice DRY findings, dispatch Worker 2 and Worker 3 for a consolidation loop, then return to Worker 1.
3. Mark the integration checkbox only once `bld-integration.md` reads `final-accepted`.
4. Spawn Worker 1 for `docs/builder/bld-final.md`.
5. If final tests fail, dispatch the owning slice loop again.
6. Mark the final checkbox only once `bld-final.md` reads `final-accepted`.

Step 3 transitions to step 4 immediately; do NOT stop between the integration pass and the final gate. The build's only stop point is **after step 6**: with the final checkbox ticked, Worker 0 hands off to the maintainer for commit.

## Memory entry shape

Append a brief block to `docs/builder/worker-memory/worker-0.md` after closing each slice: what closed and after how many passes, any Worker 1 spec edit, one carry-forward. Example:

```
## 2026-05-13 — Slice 2 (is_type_of injection)
- Closed after one Worker 2 build pass + one Worker 3 review pass; no re-spawn needed.
- Worker 1 spec edit: spec line 31 now reads "injected for all DjangoTypes" instead of "Relay-only types".
- Carry forward: when planning touches `types/base.py` __init_subclass__, queue an integration-pass DRY check vs. other validators.
```

Append-only. Approaching ~50 lines, consolidate similar entries into one pattern observation before adding more (`docs/builder/BUILD.md` `### Worker memory`).

## Closeout job

Closeout does NOT begin at the final checkbox. It begins when every checklist item is `- [x]` **and** the maintainer has committed the build and supplied the build-cycle commit range, because the diff scan operates on a fixed range. If the maintainer has not committed when Worker 0 reaches this section, stop and wait for the commit and the range; if no range is offered, ask rather than guess (`docs/builder/BUILD.md` `## Closeout`).

1. Scan all build-cycle commit diffs over the maintainer-provided range.
2. Read all four worker-memory files — the one-time closeout read, and the only time Worker 0 reads another worker's memory — to surface patterns the workers themselves noticed.
3. Identify recurring DRY patterns, repeated bug classes, and workflow stumbling blocks, and give the maintainer a brief retrospective.
4. **After maintainer approval**, fold general retrospective notes into `docs/builder/BUILD.md` or the role files — recurring patterns and workflow improvements, **never naming specific already-shipped fixes** — subject to `docs/builder/BUILD.md` `## The corpus ratchet: every edit names the bytes it retires`, which binds these edits exactly as it binds any other.
5. Delete the contents of `docs/shadow/` and `docs/builder/temp-tests/` once the retrospective is complete. Worker memory may survive that long; the next build's pre-flight clears it before any worker reads it.
6. The maintainer commits the post-closeout updates **separately** from the build commit. The build commit already carried the source/test changes, the completed plan, and every `bld-*.md` artifact — it is what step 1 scanned. The post-closeout commit carries only the approved workflow-doc edits from step 4 plus any new closeout artifact. Splitting them keeps the scanned commit range fixed rather than a moving target, and keeps the retrospective attributable to its own commit for `git log` archaeology.

## Closing out a kanban card (DB-backed — `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` are GENERATED)

**Critical:** `docs/builder/BUILD.md` `### Generated docs are DB-backed: edit the DB, then regenerate` is canonical — `KANBAN.md`, `KANBAN.html`, and `docs/GLOSSARY.md` are rendered from `examples/fakeshop/db.sqlite3` and are not hand-editable source. Two operational facts the procedure below leans on: each build script runs an in-process `/graphql/` query requesting `uuid { id }`, so the kanban models (`SpecDoc`, `CardGlossaryTerm`, `Card`, …) must be written through the **Django ORM** (`manage.py shell`, `.save()` / `.objects.create()` / `import_spec_terms`) to fire the `post_save` that creates the `UUIDModel` side-row; and the DB is git-tracked, so the maintainer can revert any edit with `git checkout -- examples/fakeshop/db.sqlite3`.

**Workers 1–3 do not read `worker-0.md`.** The card wrap and DB-backed glossary work is executed by the slice cycle (Worker 1 plans, Worker 2 runs the ORM edits and regenerate), so when a slice's contract includes the card move or a DB-backed `KANBAN.md` / `docs/GLOSSARY.md` update, Worker 0 must **embed the relevant steps of this procedure and the DONE-card invariants into that slice's planning and build dispatch prompts** — the workers cannot follow a procedure they may not read. Pre-verify the live DB references below and pass the verified findings (current card status, whether the `SpecDoc` exists, which anchors exist) into the dispatch so the workers do not re-derive them.

**Verify card/glossary references against the DB before editing — plan and spec text can be wrong.** A spec or plan naming a card (`TODO-…-NNN`), a glossary anchor, or a `CardItem` can carry a stale or mis-numbered reference, and the rendered `KANBAN.md` is not ground truth either. Confirm with `Card.objects.get(number=…)` / `GlossaryTerm.objects.get(anchor=…)` before mutating. When a reference is wrong **across multiple surfaces** (the same mis-numbered card id in the spec, in source comments, and in a standing doc), do **not** partial-fix one surface — a spec-only correction that diverges from un-editable copies is worse than uniformly-wrong. Record the cluster as a maintainer / next-spec-author follow-up in the deferred-work catalog and leave all surfaces consistent.

### DONE-card invariants (enforced by `examples/fakeshop/apps/kanban/signals.py`)

A card cannot be saved with `status.key == "done"` unless it has BOTH a linked `SpecDoc` (`SpecDoc.card` OneToOne) and at least one `CardGlossaryTerm` (`card.glossary_links`). And `manage.py import_spec_terms` — the canonical tool that syncs each done card's `CardGlossaryTerm` + `GlossarySpecMention` rows from its `docs/spec-<NNN>-…-terms.csv` — requires **every anchor in that CSV to already exist as a `GlossaryTerm` row**.

**A green `check_spec_glossary` does NOT prove the terms-CSV is importable by the done-card wrap.** `check_spec_glossary` is anchor-keyed and tolerates a many-term→one-anchor CSV grammar (it ignores the `term` column), so it reports OK on a CSV `import_spec_terms` will reject: the importer treats the anchor as a `GlossarySpecMention` identity backed by a unique constraint and errors on duplicate anchors. Every shipping card's CSV must therefore be **one row per anchor** (fold grouped member terms into the surviving row's `notes` cell). Before planning a card-wrap slice, verify importability with `import_spec_terms --check` — or confirm the one-row-per-anchor shape — not the lenient authoring gate alone, so the collapse does not surface as a mid-wrap `CommandError`.

Separately, `--check` may fail at baseline on an EARLIER done card whose `GlossarySpecMention` rows still point at a pre-archive `docs/` path after its spec moved to `docs/SPECS/`. The plain `import_spec_terms` sync processes ALL done cards and reconciles that as a side effect, so a card wrap's `db.sqlite3` diff legitimately spans more than the card being closed — verify `--check` passes for **all** done cards afterward and flag the wider diff to the maintainer.

### Procedure (move `WIP-…-<NNN>-<ver>` → `DONE-<NNN>-<ver>`)

Run DB edits via `uv run python examples/fakeshop/manage.py shell`; regenerate from the repo root.

1. **Seed any net-new glossary terms the card's spec introduced.** For each term in the spec's `-terms.csv` whose `anchor` is missing from `GlossaryTerm` (`GlossaryTerm.objects.filter(anchor=...)`), create a row deriving `title` / `status_text` / `body` from the committed `docs/GLOSSARY.md` entry (body = text between the `**Status:** …` line and the next `## ` heading, stripped). Set `status` (`GlossaryStatus` key `shipped`/`planned`), `title_sort = title.replace("\`","").lower()`, and place it in the generated ordering: `entry_order`/`index_order` equal to the **preceding alphabetical neighbor's** value — the renderer sorts by `(entry_order, title_sort)` then `(index_order, title_sort)`, so a tie plus a larger `title_sort` slots it right after the neighbor with no renumbering of other rows. Add `GlossaryCategoryMembership` rows for the term's Browse-by-category buckets; memberships sort by `order` alone, so bump the category's existing members into a temp band (`order += 1000`), then reassign the full desired order `0..N-1`, to avoid the `(category, order)` unique collision.
   - Also reconcile any **existing** term whose body the build hand-edited in the committed `docs/GLOSSARY.md` but not in the DB — otherwise step 7's regenerate reverts that shipped doc content. Sync those `GlossaryTerm.body` values from the committed file too.
2. **Create the `SpecDoc`:** `SpecDoc.objects.create(card=card, name="spec-<NNN>-<topic>-<ver>", url="https://github.com/riodw/django-strawberry-framework/blob/main/docs/spec-<NNN>-<topic>-<ver>.md")` — the `url` must contain the repo `docs/…` path the build and `import_spec_terms` parse. If a `SpecDoc` row already exists for the card, **update** its `url`/`name`; `name` is unique, so `.create()` collides.
3. **Bootstrap ≥1 glossary link** so the done-save passes: create one `CardGlossaryTerm` for a term in the spec's CSV (e.g. the first). `import_spec_terms` reconciles the full set next.
4. **Flip status:** `card.status = Status.objects.get(key="done"); card.save()` — ORM `.save()` fires the pre_save validation and sets `milestone_id`. The rendered id auto-becomes `DONE-<NNN>-<ver>` (done cards drop the milestone prefix).
5. **Sync the full glossary-link set:** `uv run python examples/fakeshop/manage.py import_spec_terms` (processes every done card; creates `CardGlossaryTerm` + `GlossarySpecMention` rows from each CSV).
6. **Fix card-body content the spec wrap names** (stale `docs/spec-0NN-…` filename refs, `## [0.0.X]` → `[Unreleased]`) by editing `CardItem.text`, and mark every **shipped** `definition_of_done` `CardItem.is_complete = True` (done-card convention — see existing DONE cards). Where the spec **defers** DoD items, leave those `is_complete = False` with a follow-up-card marker; the spec's deferral overrides the mark-every-DoD convention. Keep to what the spec authorizes; leave unrelated card-body prose alone.
7. **Regenerate all three docs** from the repo root: `uv run python scripts/build_kanban_md.py`, `uv run python scripts/build_kanban_html.py`, `uv run python scripts/build_glossary_md.py`.
8. **Verify:** `import_spec_terms --check` reports OK for all done cards; `git diff docs/GLOSSARY.md` is **clean**, proving the DB regenerates the committed glossary identically (a non-empty diff means a DB body still drifts from the committed file — fix in step 1); prove "no further drift" by hashing the regenerated docs across **two consecutive regenerates**, since `git diff` alone shows the cumulative HEAD diff and not whether a second regenerate is stable; a *baseline* regenerate-to-temp diff run **before** any DB edit separates a file-only staged anchor that auto-clears on regenerate from real DB drift to fix; `KANBAN.md` shows `DONE-<NNN>` in the Done section with its DoD ticked; `uv run python examples/fakeshop/manage.py check` passes.

Workers never commit — hand the regenerated `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` plus `examples/fakeshop/db.sqlite3` to the maintainer for review and commit.

## Stop conditions

Stop and report the blocker if:

- the active spec file is missing or ambiguous
- the spec target release cannot be determined from the spec itself
- an existing build plan would be overwritten
- Worker 1 does not set the artifact status clearly
- a worker attempts to pass information outside the artifact/diff contract
- requested work would violate `AGENTS.md`, `START.md`, or `docs/builder/BUILD.md`
