# NEXT.md — New Spec Builder Agent Flow

You have been invoked to author a new spec file under `docs/` for the next-up Work-In-Progress card in this repository.

Spec files live at the root of `docs/` (e.g. `docs/spec-018-export_schema-0_0_7.md`), NOT under `docs/SPECS/`. The older `docs/SPECS/spec-*.md` files are legacy / archived locations — read them from there for structural reference (Step 5), but new specs you create land in `docs/`.

Execute the steps below **in strict order**. Do not skip ahead. Do not read files outside the batch named in the current step. Do not start writing the spec before Step 6.

---

## Step 1 — Familiarize yourself with the repo

Read the following files (you may read them in parallel):

- `README.md`
- `START.md`
- `GOAL.md`
- `docs/README.md`
- `docs/TREE.md`
- `docs/GLOSSARY.md`
- `TODAY.md`

**Do NOT read `KANBAN.md` in this step.** You will read it in Step 3. Reading it now would bias your overview before you've built one from first principles.

`docs/GLOSSARY.md` is large but load-bearing — read it in full. Status tags (`shipped`, `planned for X.Y.Z`, `deferred`, `alpha constraint`) on each entry are the canonical source of truth for what the spec may rely on as a dependency.

`TODAY.md`'s "wait for" list is the canonical pre-state for what's NOT shipped. The spec's `Current state` and `Out of scope` sections will reuse this framing.

---

## Step 2 — Summarize the package

After finishing Step 1, output **a single paragraph** describing:

- What `django-strawberry-framework` is.
- What surfaces it ships today.
- How it positions itself relative to its upstream peers (`graphene-django` and `strawberry-graphql-django`).

Keep it tight. No headers, no bullet lists, no follow-up commentary. One paragraph, then stop and move to Step 3.

---

## Step 3 — Read the KANBAN

Now (and only now) read `KANBAN.md`. The file is large — use `grep -n "^## " KANBAN.md` first to scan section headers, then read the `## In progress` column in full. You do not need to read the `## To Do`, `## Blocked`, or `## Done` columns to author the spec.

Locate the **lowest-NNN card under the `## In progress` board column** — that is, the card whose ID starts with `WIP-` and carries the smallest 3-digit sequence number among the WIP cards. That card is the spec target.

While you're in the `## In progress` column, also note **which other WIP cards share the same patch version** as the target card (e.g., five WIP cards all tagged `-0.0.7`). When multiple cards target the same patch, the version bump is owned by the joint cut, not by any individual card's spec; record this so [Step 6](#step-6--write-the-spec) can pin the right Decision.

---

## Step 4 — Summarize the spec on deck

Output **one short paragraph** stating:

- The card ID and title.
- Why the card matters (one sentence pulled from the card's "Why it matters" body).
- The scope of the spec you are about to write.

No headers, no bullet lists. One paragraph, then move to Step 5.

---

## Step 5 — Study the existing spec format

Existing specs may live in either `docs/spec-*.md` (the canonical new location) or `docs/SPECS/spec-*.md` (the legacy location for specs authored before the path change). Check both directories. Read **the most-recently-shipped spec file in full** — it is the canonical template for voice, depth, and section layout. For the rest, you only need to internalize structure:

- For each older `spec-*.md`, run `grep -n "^##\|^###" <path>` to capture its section list — do not read the body unless a specific decision shape requires it.
- The recent specs run 500–800 lines and may exceed the Read tool's 25k-token limit. If a full read fails, use `grep` to find anchors first, then read with `offset` / `limit` to grab just the sections you need.

What to internalize:

- **Filename convention**: `spec-<NNN>-<topic>-<0_0_X>.md`, where `<NNN>` matches the KANBAN card's NNN, `<topic>` is a short snake_case slug naming the card's subject, and `<0_0_X>` is the target milestone version with dots replaced by underscores. Worked example: card `DONE-016-0.0.7 — DjangoListField (non-Relay list)` → file `spec-016-list_field-0_0_7.md`.
- **Section layout**: the recent specs all carry roughly the same skeleton, in this order — frontmatter with revision history, **Key glossary references**, **Slice checklist**, **Problem statement**, **Current state**, **Goals**, **Non-goals**, **Borrowing posture** (when upstreams ship a comparable primitive), **User-facing API** (when the spec adds a consumer-visible symbol), **Architectural decisions** (numbered), **Implementation plan** (with a per-slice delta table), **Edge cases and constraints**, **Test plan**, **Doc updates**, **Risks and open questions**, **Out of scope (explicitly tracked elsewhere)**, **Definition of done**. Follow the most-recent spec when in doubt.
- **Voice and depth**: these specs are detailed and decision-heavy. Every choice is pinned with rationale; every alternative considered is named and rejected with a reason.
- **Cross-references**: source files are cited as repository-relative paths (often with line numbers, e.g. `types/base.py:651-657`); KANBAN cards by their full ID; prior specs by markdown link; upstream packages by absolute local path from `docs/TREE.md`.
- **Permission caveat**: the recent specs explicitly note that `AGENTS.md` prohibits `CHANGELOG.md` edits without permission and that the spec's Slice 5 grants that permission. Mirror this in your spec.

---

## Step 6 — Write the spec

Create the new file at:

```
docs/spec-<NNN>-<topic>-<0_0_X>.md
```

Where:

- `<NNN>` = the NNN from the WIP card you identified in Step 3.
- `<topic>` = a short snake_case slug describing the card's subject.
- `<0_0_X>` = the version segment from the WIP card's trailing `-X.Y.Z`, with dots replaced by underscores (e.g. `0.0.7` → `0_0_7`).

The spec must:

- Match the structure, voice, and depth of the most-recently-shipped existing spec (either `docs/spec-*.md` or `docs/SPECS/spec-*.md`, whichever is most recent).
- Carry every constraint, recommended architectural direction, and open design question from the KANBAN card body into the spec body — expanded with rationale, not merely quoted. If the card already pre-pins a "Recommended architectural direction" block (some do, some don't), preserve it as a Decision and add the alternatives-rejected language; do not re-litigate it.
- Cite source files with repository-relative paths (e.g., `django_strawberry_framework/types/base.py`). You MAY read source files during Step 6 to ground decisions — that is not a boundary violation; only file modification is.
- Resolve as many of the card's open design questions as the available evidence supports; leave the remainder as entries inside the `Risks and open questions` section (not a standalone section), naming a preferred answer for the target version and a fallback.
- Pin alternatives considered and rejected with a reason — do not silently drop them.
- If multiple WIP cards share the target patch version (per Step 3), include a Decision that explicitly defers the `pyproject.toml` / `__version__` / `tests/base/test_init.py` version bump to the joint cut card. The Slice 5 / Definition of done checklist must NOT bump the version.
- The Slice 5 doc-updates list typically touches: `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `README.md`, `GOAL.md`, `TODAY.md`, `KANBAN.md`, `CHANGELOG.md`. Not every spec touches all eight; include each only when the card's surface change is reflected there.

---

## Step 7 — Anchor every project-specific term to the glossary

Author a companion `*-terms.csv` next to the new spec at:

```
docs/spec-<NNN>-<topic>-<0_0_X>-terms.csv
```

CSV columns: `term,anchor,notes` (header row required). One row per project-specific symbol or concept the spec references — every `DjangoType`, `Meta.*` key, named subsystem (`FilterSet`, `OrderSet`, `AggregateSet`, …), helper symbol (`apply_cascade_permissions`, `OptimizerHint`, …), and shipped/planned capability that has (or should have) a `## <heading>` in `docs/GLOSSARY.md`. The `term` column is the surface form the consumer writes (e.g., `Meta.primary`, `DjangoConnectionField`); the `anchor` column is the GitHub auto-anchor for the matching `## <heading>` (lowercased, backticks dropped, non-word characters except whitespace/hyphens stripped, whitespace runs collapsed to single hyphens — so `## \`Meta.primary\`` → `metaprimary` and `## Relation handling` → `relation-handling`); the `notes` column is free-form (use it to record why a term was included, ambiguity callouts, or status hints like `planned for 0.0.9`).

**Populate the CSV OVER-ZEALOUSLY on the first pass.** Under-population is the common failure mode and the checker cannot catch it — a term that appears in the spec body but is missing from the CSV is silently unanchored and ships that way. Over-population, by contrast, surfaces loudly: the checker flags every CSV term whose anchor has no matching GLOSSARY heading, and you delete the row in one edit. **The asymmetry is the whole point — false positives are cheap, false negatives are invisible. Bias every judgement call toward inclusion.**

Concrete enumeration discipline (do NOT short-circuit this list — under-population happens precisely when an agent skips the fresh-pass discipline and works from memory of writing the spec):

- After writing the spec body, do a **separate fresh pass front-to-back** with the explicit goal of enumerating terms. Do not rely on memory from the writing pass; open the file again and read every section.
- Scan **every section**, not just `Key glossary references` at the top — glossary terms hide in `Decision` bodies, `Risks and open questions`, `Edge cases and constraints`, `Doc updates`, `Out of scope`, even `Definition of done` as often as they appear in the obvious top-of-spec lookup section.
- Every backticked symbol that names a package surface gets a row (`DjangoType`, `DjangoListField`, `DjangoConnectionField`, `OptimizerHint`, `BigInt`, `finalize_django_types`, `auto`, `ConfigurationError`, …).
- Every `Meta.*` key the spec mentions gets its own row, one per key (`Meta.model`, `Meta.fields`, `Meta.exclude`, `Meta.name`, `Meta.description`, `Meta.interfaces`, `Meta.primary`, `Meta.optimizer_hints`, `Meta.filterset_class`, `Meta.orderset_class`, `Meta.aggregate_class`, `Meta.fields_class`, `Meta.search_fields`, `Meta.choice_enum_names`, …) — even when the spec only mentions one of them in passing.
- Every named subsystem or capability gets a row (Relay Node integration, FK-id elision, Plan cache, Strictness mode, Choice enum generation, Relation handling, Specialized scalar conversions, Definition-order independence, Schema audit, Queryset diffing, `only()` projection, Multi-database cooperation, Connection-aware optimizer planning, …).
- Every helper symbol cited in body or decision rationales gets a row (`apply_cascade_permissions`, `get_queryset` visibility hook, `RelatedFilter`, `RelatedOrder`, `RelatedAggregate`, `get_child_queryset`, Per-field permission hooks, `FieldError` envelope, `Upload` scalar, `DjangoFileType`, `DjangoImageType`, …).
- Every shipped-status or planned-status callout that names a term — if the spec writes "planned for `0.0.9`" against a symbol name, that symbol gets a row even if the spec only references it as an Out-of-scope pointer.
- Every cross-referenced spec section, GLOSSARY entry name, or external symbol cited via markdown link gets evaluated for a row — when in doubt, include.
- Backtick-wrapped, non-backticked, qualified (`relay.Node`), and unqualified (`Node`) forms of the same symbol all map to the same anchor — pick the most common surface form for the `term` column and let one row cover every mention.

The instinct to "trim CSV rows that don't have GLOSSARY headings" happens AFTER the over-zealous first pass, driven by the checker's output. Do NOT pre-emptively skip a term because you are unsure it has a glossary entry. Do NOT skip a term because you "already linked it inline" — the CSV is the audit ledger, not a duplicate of the spec body. Let the script tell you which rows to drop; do not pre-decide.

Then run the checker:

```
uv run python scripts/check_spec_glossary.py --spec docs/spec-<NNN>-<topic>-<0_0_X>.md
```

(`--terms` and `--glossary` default sensibly when the CSV lives next to the spec and the glossary stays at `docs/GLOSSARY.md`.)

Pass condition: the script exits 0 with `OK: N terms — all have glossary entries and at least one spec link.` That output is the proof that **everything is accounted for** — every term in the CSV resolves to a real GLOSSARY heading, and every term has at least one inline `](GLOSSARY.md#<anchor>)` reference somewhere in the spec body.

Two failure modes and their resolutions:

- **Missing glossary entries** (the term's anchor has no matching `## <heading>` in `docs/GLOSSARY.md`). Either the term is mis-spelled in the CSV (fix the row), the GLOSSARY needs a new entry (out of scope for this flow — leave the term in the CSV and call out the missing entry as an `Open questions` item in the spec), or the term shouldn't be in the CSV at all (delete the row).
- **Missing spec links** (the spec mentions the term in prose but doesn't link it to the glossary). Add a `](GLOSSARY.md#<anchor>)` reference manually, OR re-run the checker with `--auto-link` to rewrite the spec in place — it wraps the first non-code, non-link occurrence of each term as `[term](GLOSSARY.md#<anchor>)` (and prefers the backtick-wrapped form when the spec already says e.g. `Meta.fields` in inline code). The auto-link pass is idempotent.

Repeat the CSV edit / checker run cycle until the script exits 0. The CSV is the source of truth: trim it when a term does not warrant a glossary entry, extend it when a new term needs one. The CSV is committed alongside the spec so future maintainers can re-run the check whenever the GLOSSARY or the spec changes.

---

## Step 8 — Archive prior specs and update cross-references

After Step 7 exits 0, archive every OTHER spec file that lives in `docs/` so the active working directory only contains the spec you just authored. Each prior spec moves to its legacy home under `docs/SPECS/` and every cross-reference to it gets rewritten in the same pass so no link goes stale. The active WIP card in `KANBAN.md` also gets a reference to the active spec added or updated as part of the same sweep.

The "active" spec is the one you just authored in Step 6. Every other `spec-*.md` (and its companion `*-terms.csv` if present) is a prior in-flight spec from an earlier card cycle that should now live under `docs/SPECS/` alongside the older legacy specs.

Concrete sequence:

1. **List candidates.** Enumerate every `spec-*.md` file at the top level of `docs/` (do NOT recurse into `docs/SPECS/`, which is the destination):

   ```
   ls docs/spec-*.md
   ```

   Subtract the new spec you just authored. The remainder is the archive set.
2. **Move each candidate** (and its companion CSV when present) into `docs/SPECS/`, preserving filename:

   ```
   git mv docs/spec-<old_NNN>-<old_topic>-<old_version>.md docs/SPECS/
   git mv docs/spec-<old_NNN>-<old_topic>-<old_version>-terms.csv docs/SPECS/
   ```

   Use `git mv` rather than `mv` so the rename is tracked. If the file is not yet tracked by git, fall back to `mv`.
3. **Rewrite cross-references in the new spec.** Search the spec you just authored for markdown links that point at any moved spec — match patterns like `](spec-<old_NNN>-…)`, `](./spec-<old_NNN>-…)`, and `](docs/spec-<old_NNN>-…)`. Each match becomes the new path under `docs/SPECS/` (relative-path discipline: from a spec in `docs/`, the moved sibling is now at `SPECS/spec-<old_NNN>-…`).
4. **Rewrite cross-references in every other doc, INCLUDING `KANBAN.md`.** Enumerate every doc that references the moved spec(s):

   ```
   grep -rln "spec-<old_NNN>-<old_topic>-<old_version>" docs/ README.md GOAL.md TODAY.md AGENTS.md KANBAN.md
   ```

   For each hit, rewrite the path so the link still resolves after the move. Relative-path discipline: from `docs/GLOSSARY.md` the moved file is `SPECS/spec-…`; from repo-root `README.md` / `KANBAN.md` / `GOAL.md` / `TODAY.md` / `AGENTS.md` it is `docs/SPECS/spec-…`; from another spec under `docs/` it is `SPECS/spec-…`. Apply every rewrite in place — `KANBAN.md` is part of this sweep, not exempt from it.
5. **Add or update the active WIP card's reference to the new spec.** The card you targeted in Step 3 should point at the spec file you just authored. Open `KANBAN.md` at the active WIP card body and verify it contains a link to `docs/spec-<NNN>-<topic>-<0_0_X>.md`. Three cases:

   - **No reference present** — add one. Typical placement: a `Spec:` or `Active spec:` line at the top of the card body (or under the card's existing "Files likely touched" section if the card uses that convention), with a markdown link to the new spec at its `docs/spec-<NNN>-…` path.
   - **Reference present but pointing at a different path** (e.g., a stale `docs/SPECS/spec-…` from a prior archive cycle, or a now-renamed slug) — rewrite to point at the active path.
   - **Reference present at the correct path** — no action.

   When the active card lives in a column other than `## In progress` by the time you reach this step (e.g., the maintainer moved it to `## Done` between Step 3 and Step 8), follow the reference to the new column and update in place there. The reference belongs with the card, not with the column.
6. **`CHANGELOG.md` stays reserved.** `CHANGELOG.md` has its own maintainer-edited protocol and is NOT rewritten by this step even when it references a moved spec. If `grep` finds matches in `CHANGELOG.md`, surface them as a one-line report at the end of the flow ("`CHANGELOG.md` references moved spec(s) at lines …; maintainer must update") and STOP — do not silently edit.
7. **Re-run the checker** against the new spec one more time:

   ```
   uv run python scripts/check_spec_glossary.py --spec docs/spec-<NNN>-<topic>-<0_0_X>.md
   ```

   The archive pass may have shifted markdown link paths inside the new spec; the script's earlier exit-0 must still hold. If it now fails, fix the cross-reference rewrites until it exits 0 again.

This step is idempotent. A second pass with no other specs at `docs/` top-level and a `KANBAN.md` already pointing at the active spec is a clean no-op.

The flow is complete when Step 8 finishes: only the active spec and its CSV live at `docs/spec-*`, every prior spec is at `docs/SPECS/spec-*`, every cross-reference resolves (including in `KANBAN.md`), and the checker exits 0 against the active spec.

---

## Boundaries

- Do **not** modify `CHANGELOG.md` under any circumstance during this flow — even path-update edits triggered by Step 8 must be surfaced as a maintainer-report rather than silently applied.
- Do **not** modify `TODAY.md` except as a Step 8 path-update (rewriting a moved spec's path); content edits to `TODAY.md` outside that narrow purpose are out of scope.
- `KANBAN.md` IS in scope for Step 8 — apply path-updates for moved specs in place, AND add or rewrite the active WIP card's spec reference per Step 8 action 5. No other edits to `KANBAN.md` (no column moves, no card-body content changes beyond the spec-reference line).
- Do **not** modify any file other than the new spec file, its companion `*-terms.csv`, the spec files being archived under Step 8, and the cross-reference updates Step 8 prescribes in `docs/`, `README.md`, `GOAL.md`, `TODAY.md`, `AGENTS.md`, and `KANBAN.md`.
- Do **not** commit.
- Do **not** run pytest, ruff, or any other tooling unless Step 7 or Step 8 prescribes it (the `scripts/check_spec_glossary.py` run including its `--auto-link` rewrite, and the `git mv` / `grep` invocations Step 8 names, are all part of the flow) or you need to settle a question inside the spec.
- The artifacts this flow produces: the new spec file, its companion `*-terms.csv`, the moves of every prior `spec-*.md` (and companion CSV) from `docs/` to `docs/SPECS/`, path-only cross-reference updates in every doc that pointed at a moved spec, and the active WIP card's spec-reference line in `KANBAN.md`.
- The flow is not complete until (a) `scripts/check_spec_glossary.py` exits 0 against the new spec and its CSV, (b) Step 8 has run and no `spec-*.md` other than the active one remains at `docs/` top-level, AND (c) the active WIP card in `KANBAN.md` carries a link to `docs/spec-<NNN>-<topic>-<0_0_X>.md`.
- If the WIP card's body conflicts with something you read in Step 1, prefer the card and call out the conflict as an entry in the spec's `Risks and open questions` section — do not silently reconcile.
- Reading source files, existing specs, or test files during Step 6 is allowed and expected. The boundary is on **writes**, not reads.
