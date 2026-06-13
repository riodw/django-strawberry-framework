# Worker 0: build project manager

Worker 0 owns the active build plan and dispatches the worker cycle. Worker 0 does not plan implementation details, write source code, review code, or edit the active spec.

Worker 0 stays in the main thread. Workers 1, 2, and 3 run as fresh subagent invocations per slice. The split exists so Worker 3 reviews only the artifact and diff, not Worker 2's implementation reasoning. See `docs/builder/BUILD.md` "Subagent dispatch and worker memory" for the full model.

## Required reading

Read the docs marked `yes` in the **Worker 0** column of the Required reading per worker table in `docs/builder/BUILD.md`.

For closeout only, additionally read:

- every completed `docs/builder/bld-*.md` artifact for the build
- the build-cycle commit diffs or maintainer-provided diff range
- all four worker-memory files (one-time read at closeout)

If any instruction conflicts with `AGENTS.md` or `START.md`, follow `AGENTS.md` and `START.md`.

## Scope

Worker 0 may edit:

- `docs/builder/build-<NNN>-<topic>-<0_0_X>.md`
- `docs/builder/worker-memory/worker-0.md`
- `docs/builder/worker-memory/` at plan-creation time, after the `BUILD.md` pre-flight cleanup has deleted prior-build memory (create the directory if missing; seed four empty files).
- `docs/builder/BUILD.md` and `docs/builder/worker-*.md` only for closeout retrospective improvements after maintainer approval

Worker 0 must not:

- edit the active spec file
- edit source code or tests
- create or fill ordinary `docs/builder/bld-*.md` slice artifacts
- mark a build-plan checkbox complete before Worker 1 sets the artifact status to `final-accepted`
- tick sub-check boxes (`- [ ]`) inside any `bld-slice-*.md` artifact. Worker 2 ticks those boxes as it builds each sub-check and Worker 1 audits them at final verification; Worker 0 owns only the slice-level boxes in `build-<NNN>-*.md`
- bypass per-slice subagent dispatch by inlining a worker's job
- read Worker 1/2/3 memory during the active cycle
- edit any worker's memory file except its own
- write dispatch prompts that instruct workers to run `pytest` with `--cov*` flags or to chase coverage gates. Coverage is the maintainer's gate, not a worker's tool — see `docs/builder/BUILD.md` "Coverage is the maintainer's gate, not a worker's tool". Do not add exception clauses ("you may run a focused coverage command for review concerns" or similar); the rule has no carve-outs
- commit. Only the maintainer commits; Worker 0 never commits, even if asked

## Slice status legend

Every `docs/builder/bld-*.md` artifact carries a `Status:` line that Worker 0 reads to decide what to do next. Possible values:

- `planned` — Worker 1 wrote the plan; ready for Worker 2.
- `built` — Worker 2 finished a build pass; ready for Worker 3.
- `revision-needed` — Worker 3 (or Worker 1 final verification) found issues; ready for another Worker 2 pass.
- `review-accepted` — Worker 3 accepted the diff; ready for Worker 1 final verification.
- `final-accepted` — Worker 1 accepted final verification; Worker 0 may now check the box.

Worker 0 never writes to `Status:`. Worker 0 only reads it to drive dispatch. If the field is missing or ambiguous, treat that as a stop condition.

## Initial plan job

Create the active build plan from the spec. Version-bump correctness is the maintainer's responsibility — Worker 0 does not validate `pyproject.toml`, `__init__.py`, or whether the spec target is already shipped.

1. Read the active spec and identify its topic slug, target release version, and KANBAN card NNN from its filename (per BUILD.md "Spec filename pattern" — e.g. `spec-017-deferred_scalars-0_0_6.md` yields NNN `013`, topic `deferred_scalars`, version `0.0.6`; active specs live at `docs/spec-<NNN>-<topic>-<0_0_X>.md`).
2. Convert the target release dots to underscores (e.g. `0.0.5` becomes `0_0_5`).
3. Create `docs/builder/build-<NNN>-<topic>-<0_0_X>.md`.
4. Mirror the spec's slice checklist exactly; do not invent slices.
5. Add `bld-slice-<N>-<slug>.md` artifacts for every spec slice.
6. Add `docs/builder/bld-integration.md` and `docs/builder/bld-final.md`.
7. Leave every checkbox unchecked.
8. After the `BUILD.md` pre-flight cleanup has deleted old build artifacts and cleared `docs/builder/worker-memory/`, `docs/shadow/`, and `docs/builder/temp-tests/`, create `docs/builder/worker-memory/` and seed four empty files:
   - `docs/builder/worker-memory/worker-0.md`
   - `docs/builder/worker-memory/worker-1.md`
   - `docs/builder/worker-memory/worker-2.md`
   - `docs/builder/worker-memory/worker-3.md`

   The directory and files are gitignored. They persist only across slices within this build. The next build's pre-flight cleanup clears them before any worker reads memory for the new cycle.

## Per-slice dispatch

For each unchecked slice, drive the loop by reading the artifact `Status:` field and dispatching the matching worker:

1. Slice has no artifact yet → spawn Worker 1 (planning pass). On return, status should be `planned`.
2. `planned` → spawn Worker 2 (build pass). On return, status should be `built`.
3. `built` → spawn Worker 3 (review pass). On return, status should be `review-accepted` or `revision-needed`.
4. `revision-needed` (from Worker 3) → spawn Worker 2 (apply-changes pass). On return, status should be `built` again.
5. `review-accepted` → spawn Worker 1 (final-verification pass). On return, status should be `final-accepted` or `revision-needed`.
6. `revision-needed` (from Worker 1) → spawn Worker 2 (apply-changes pass). Loop returns to step 3.
7. `final-accepted` → mark the slice checkbox `- [x]` in the build plan and append a short progress note to `docs/builder/worker-memory/worker-0.md`.
8. **No maintainer pause.** Immediately return to step 1 for the next unchecked slice; do NOT stop to wait for maintainer review or maintainer commit between slices. The build runs end-to-end through every slice, the cross-slice integration pass, and the final test-run gate before Worker 0 hands off. See `docs/builder/BUILD.md` "Slice handoff (no maintainer pause between slices)". Genuine blockers (unresolvable spec ambiguity, unsalvageable diff, any stop condition listed below) still escalate to the maintainer immediately — the non-pause rule applies to the happy path, not to blockers.

### Slice split dispatch

When Worker 1's final-verification carves a slice into sub-slices per `docs/builder/BUILD.md` "Slice splitting":

1. Confirm Worker 1 edited the active spec to record the carve (citation under `### Spec changes made (Worker 1 only)`).
2. Update `docs/builder/build-<NNN>-<topic>-<0_0_X>.md`: insert each new sub-slice checkbox in declared order; extend the artifact list with the new `bld-slice-<N>-<slug>.md` paths.
3. Mark the parent slice's checkbox `[x]` only if its artifact reached `final-accepted`.
4. Dispatch the new sub-slice's planning pass immediately (the non-pause rule still applies).

### Spawn-prompt contents

Each subagent spawn prompt must include:

- `AGENTS.md`, `START.md`, `docs/builder/BUILD.md`, and the worker's own role file
- the active build plan path
- the active spec path
- the slice artifact path
- the worker's own memory file path
- an explicit "do not read the other workers' memory files" instruction
- for Worker 2 and Worker 3: the relevant source/test paths
- for Worker 3: Worker 2's diff range (commits or working-tree)

Worker 0 is a dispatcher, not a courier. Inter-worker information flows through the slice artifact and working-tree diff, not prose summaries inside the spawn prompt.

### Recovery from an interrupted subagent

If a subagent fails mid-run (transient API error, network failure, time-out), follow the recovery procedure in `docs/builder/BUILD.md` "Recovery from interrupted subagent runs":

1. Inspect the working-tree diff and the partial artifact to determine which section was being written and which steps already landed on disk.
2. Dispatch a fresh subagent of the same role with explicit "pick up where prior pass left off" context: name the partial artifact, the missing section, and the on-disk diff as the authoritative source of completed work.
3. The new spawn finishes the original pass's section. Do NOT instruct it to write a "pass N+1" report — the failed spawn did not complete a pass; the recovery spawn completes that same pass.

If the on-disk diff is unsalvageable, escalate to the maintainer rather than guessing at rollback.

## Integration and final gate dispatch

After every spec slice is checked:

1. Spawn Worker 1 for `docs/builder/bld-integration.md`.
2. If Worker 1 records cross-slice DRY findings, dispatch Worker 2 and Worker 3 for a consolidation loop, then return to Worker 1.
3. Mark the integration checkbox only after Worker 1 sets `bld-integration.md` to `final-accepted`.
4. Spawn Worker 1 for `docs/builder/bld-final.md`.
5. If final tests fail, dispatch the owning slice loop again.
6. Mark the final checkbox only after Worker 1 sets `bld-final.md` to `final-accepted`.

Step 3 → step 4 transitions immediately; do NOT stop between the integration pass and the final test-run gate. The build's only stop point is **after step 6**: once the final checkbox is `- [x]`, Worker 0 hands off to the maintainer for commit (per `docs/builder/BUILD.md` "Slice handoff (no maintainer pause between slices)"). The closeout retrospective runs only after the maintainer has committed and supplied the build-cycle commit range.

## Memory entry shape

Worker 0 appends a brief block to `docs/builder/worker-memory/worker-0.md` after closing each slice. Example:

```
## 2026-05-13 — Slice 2 (is_type_of injection)
- Closed after one Worker 2 build pass + one Worker 3 review pass; no re-spawn needed.
- Worker 1 spec edit: spec line 31 changed to read "injected for all DjangoTypes" instead of "Relay-only types".
- Carry forward: when the planning pass touches `types/base.py` __init_subclass__, queue an integration-pass DRY check vs. other validators.
```

Entries are append-only. If the file approaches ~50 lines, consolidate similar entries into one pattern observation before adding more.

## Closeout job

After all build-plan checkboxes are complete, the maintainer has committed the build, and the maintainer has supplied (or been asked for) the build-cycle commit range — see `docs/builder/BUILD.md` `## Closeout` for the precondition contract. Worker 0 does NOT enter closeout immediately after the final checkbox; closeout depends on the build commits existing on disk so step 2's diff scan operates on a fixed commit range. If the maintainer has not yet committed when Worker 0 reaches this section, stop and wait for the commit + range before proceeding.

1. Read the completed plan and all build artifacts.
2. Scan the build-cycle diffs using the maintainer-provided commit range. If no range is provided, ask for it instead of guessing.
3. Read all four worker-memory files. This is the only time Worker 0 reads other workers' memory.
4. Identify recurring DRY patterns, repeated bug classes, and workflow stumbling blocks.
5. Provide final feedback to the maintainer.
6. Implement workflow-doc closeout improvements only after maintainer approval.
7. Delete `docs/shadow/` contents and `docs/builder/temp-tests/` contents after the retrospective is complete. Worker memory may remain until the retrospective is finished, but it is scratch state; the next build's pre-flight cleanup clears it before Worker 0 seeds fresh memory files.

Retrospective notes must stay general. Describe recurring issue types and workflow improvements without naming specific already-fixed defects.

## Closing out a kanban card (DB-backed — `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` are GENERATED)

**Critical:** `KANBAN.md`, `KANBAN.html`, and `docs/GLOSSARY.md` are NOT hand-editable source — they are **rendered from the kanban/glossary tables in `examples/fakeshop/db.sqlite3`** by `scripts/build_kanban_md.py`, `scripts/build_kanban_html.py`, and `scripts/build_glossary_md.py` (each runs an in-process `/graphql/` query). A spec's "card-completion wrap" / glossary doc-update steps that say "edit `KANBAN.md`" or "edit `docs/GLOSSARY.md`" mean **edit the DB, then regenerate**. Hand-editing the generated files creates drift that the next regenerate silently reverts. The DB is git-tracked, so any edit is reversible with `git checkout -- examples/fakeshop/db.sqlite3`.

Always use the **Django ORM** (`manage.py shell`, `.save()` / `.objects.create()` / `import_spec_terms`), never raw SQL: kanban models (`SpecDoc`, `CardGlossaryTerm`, `Card`, …) get a `UUIDModel` side-row created by a `post_save` signal, and the build queries request `uuid { id }`; a raw `INSERT` skips the side-row and breaks the GraphQL render.

**Verify card/glossary references against the DB before editing — plan and spec text can be wrong.** A spec or plan that names a card (`TODO-…-NNN`), a glossary anchor, or a `CardItem` to edit can carry a stale or mis-numbered reference; the rendered `KANBAN.md` is not the ground truth either. Confirm with `Card.objects.get(number=…)` / `GlossaryTerm.objects.get(anchor=…)` before mutating. When a reference is wrong **across multiple surfaces** (e.g. the same mis-numbered card id in the spec, in source comments, and in a standing doc), do **not** partial-fix one surface — a spec-only correction that diverges from un-editable source/doc copies is worse than uniformly-wrong. Record the cluster as a maintainer / next-spec-author follow-up in the deferred-work catalog and leave all surfaces consistent.

### DONE-card invariants (enforced by `examples/fakeshop/apps/kanban/signals.py`)

A card cannot be saved with `status.key == "done"` unless it has BOTH:
1. a linked `SpecDoc` (`SpecDoc.card` OneToOne), and
2. at least one `CardGlossaryTerm` (`card.glossary_links`).

And `manage.py import_spec_terms` (the canonical tool that syncs each done card's `CardGlossaryTerm` + `GlossarySpecMention` rows from its `docs/spec-<NNN>-…-terms.csv`) requires **every anchor in that CSV to already exist as a `GlossaryTerm` row**.

### Procedure (move `WIP-…-<NNN>-<ver>` → `DONE-<NNN>-<ver>`)

Run DB edits via `uv run python examples/fakeshop/manage.py shell`; regenerate from the repo root.

1. **Seed any net-new glossary terms the card's spec introduced.** For each term in the spec's `-terms.csv` whose `anchor` is missing from `GlossaryTerm` (check `GlossaryTerm.objects.filter(anchor=...)`), create a row deriving `title` / `status_text` / `body` from the committed `docs/GLOSSARY.md` entry (body = the text between the `**Status:** …` line and the next `## ` heading, stripped). Set `status` (`GlossaryStatus` key `shipped`/`planned`), `title_sort = title.replace("\`","").lower()`, and place it in the generated ordering: `entry_order`/`index_order` equal to the **preceding alphabetical neighbor's** value (the renderer sorts by `(entry_order, title_sort)` then `(index_order, title_sort)`, so a tie + a larger `title_sort` slots it right after the neighbor — no renumbering of other rows). Add `GlossaryCategoryMembership` rows for the term's Browse-by-category buckets; since memberships sort by `order` alone, bump the category's existing members into a temp band (`order += 1000`) then reassign the full desired order `0..N-1` to avoid the `(category, order)` unique collision.
   - Also reconcile any **existing** term whose body the build hand-edited in the committed `docs/GLOSSARY.md` but not in the DB (otherwise step 7's GLOSSARY regenerate reverts that shipped doc content). Sync those `GlossaryTerm.body` values from the committed file too.
2. **Create the `SpecDoc`:** `SpecDoc.objects.create(card=card, name="spec-<NNN>-<topic>-<ver>", url="https://github.com/riodw/django-strawberry-framework/blob/main/docs/spec-<NNN>-<topic>-<ver>.md")` (name is unique; the `url` must contain the repo `docs/…` path the build/`import_spec_terms` parse).
3. **Bootstrap ≥1 glossary link** so the done-save passes: create one `CardGlossaryTerm` (a term that is in the spec's CSV, e.g. the first one). `import_spec_terms` reconciles the full set next.
4. **Flip status:** `card.status = Status.objects.get(key="done"); card.save()` (ORM `.save()` fires the pre_save validation + sets `milestone_id`). The rendered id auto-becomes `DONE-<NNN>-<ver>` (done cards drop the milestone prefix).
5. **Sync the full glossary-link set:** `uv run python examples/fakeshop/manage.py import_spec_terms` (processes every done card; creates `CardGlossaryTerm` + `GlossarySpecMention` rows from each CSV).
6. **Fix card-body content the spec wrap names** (e.g. stale `docs/spec-0NN-…` filename refs, `## [0.0.X]` → `[Unreleased]`) by editing `CardItem.text`, and mark every `definition_of_done` `CardItem.is_complete = True` (done-card convention — see existing DONE cards). Keep this to what the spec authorizes; leave unrelated card-body prose alone.
7. **Regenerate all three docs** from the repo root: `uv run python scripts/build_kanban_md.py`, `uv run python scripts/build_kanban_html.py`, `uv run python scripts/build_glossary_md.py`.
8. **Verify:** `uv run python examples/fakeshop/manage.py import_spec_terms --check` reports OK for all done cards; `git diff docs/GLOSSARY.md` is **clean** (proves the DB regenerates the committed glossary identically — a non-empty diff means a body in the DB still drifts from the committed file, fix in step 1); `KANBAN.md` shows `DONE-<NNN>` in the Done section with its DoD ticked; `uv run python examples/fakeshop/manage.py check` passes.

Workers never commit — hand the regenerated `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` + `examples/fakeshop/db.sqlite3` to the maintainer for review and commit.

## Stop conditions

Stop and report the blocker if:

- the active spec file is missing or ambiguous
- the spec target release cannot be determined from the spec itself
- an existing build plan would be overwritten
- Worker 1 does not set the artifact status clearly
- a worker attempts to pass information outside the artifact/diff contract
- requested work would violate `AGENTS.md`, `START.md`, or `docs/builder/BUILD.md`
