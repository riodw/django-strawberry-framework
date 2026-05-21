# NEW.md — New Spec Builder Agent Flow

You have been invoked to author a new spec file under `docs/SPECS/` for the next-up Work-In-Progress card in this repository.

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

Read **the most-recently-shipped existing `docs/SPECS/spec-*.md` file in full** — it is the canonical template for voice, depth, and section layout. For the rest, you only need to internalize structure:

- For each older `spec-*.md`, run `grep -n "^##\|^###" <path>` to capture its section list — do not read the body unless a specific decision shape requires it.
- The recent specs run 500–800 lines and may exceed the Read tool's 25k-token limit. If a full read fails, use `grep` to find anchors first, then read with `offset` / `limit` to grab just the sections you need.

What to internalize:

- **Filename convention**: `spec-<NNN>-<topic>-<0_0_X>.md`, where `<NNN>` matches the KANBAN card's NNN, `<topic>` is a short snake_case slug naming the card's subject, and `<0_0_X>` is the target milestone version with dots replaced by underscores. Worked example: card `WIP-ALPHA-016-0.0.7 — DjangoListField (non-Relay list)` → file `spec-016-list_field-0_0_7.md`.
- **Section layout**: the recent specs all carry roughly the same skeleton, in this order — frontmatter with revision history, **Key glossary references**, **Slice checklist**, **Problem statement**, **Current state**, **Goals**, **Non-goals**, **Borrowing posture** (when upstreams ship a comparable primitive), **User-facing API** (when the spec adds a consumer-visible symbol), **Architectural decisions** (numbered), **Implementation plan** (with a per-slice delta table), **Edge cases and constraints**, **Test plan**, **Doc updates**, **Risks and open questions**, **Out of scope (explicitly tracked elsewhere)**, **Definition of done**. Follow the most-recent spec when in doubt.
- **Voice and depth**: these specs are detailed and decision-heavy. Every choice is pinned with rationale; every alternative considered is named and rejected with a reason.
- **Cross-references**: source files are cited as repository-relative paths (often with line numbers, e.g. `types/base.py:651-657`); KANBAN cards by their full ID; prior specs by markdown link; upstream packages by absolute local path from `docs/TREE.md`.
- **Permission caveat**: the recent specs explicitly note that `AGENTS.md` prohibits `CHANGELOG.md` edits without permission and that the spec's Slice 5 grants that permission. Mirror this in your spec.

---

## Step 6 — Write the spec

Create the new file at:

```
docs/SPECS/spec-<NNN>-<topic>-<0_0_X>.md
```

Where:

- `<NNN>` = the NNN from the WIP card you identified in Step 3.
- `<topic>` = a short snake_case slug describing the card's subject.
- `<0_0_X>` = the version segment from the WIP card's trailing `-X.Y.Z`, with dots replaced by underscores (e.g. `0.0.7` → `0_0_7`).

The spec must:

- Match the structure, voice, and depth of the most-recently-shipped existing spec under `docs/SPECS/`.
- Carry every constraint, recommended architectural direction, and open design question from the KANBAN card body into the spec body — expanded with rationale, not merely quoted. If the card already pre-pins a "Recommended architectural direction" block (some do, some don't), preserve it as a Decision and add the alternatives-rejected language; do not re-litigate it.
- Cite source files with repository-relative paths (e.g., `django_strawberry_framework/types/base.py`). You MAY read source files during Step 6 to ground decisions — that is not a boundary violation; only file modification is.
- Resolve as many of the card's open design questions as the available evidence supports; leave the remainder as entries inside the `Risks and open questions` section (not a standalone section), naming a preferred answer for the target version and a fallback.
- Pin alternatives considered and rejected with a reason — do not silently drop them.
- If multiple WIP cards share the target patch version (per Step 3), include a Decision that explicitly defers the `pyproject.toml` / `__version__` / `tests/base/test_init.py` version bump to the joint cut card. The Slice 5 / Definition of done checklist must NOT bump the version.
- The Slice 5 doc-updates list typically touches: `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `README.md`, `GOAL.md`, `TODAY.md`, `KANBAN.md`, `CHANGELOG.md`. Not every spec touches all eight; include each only when the card's surface change is reflected there.

---

## Boundaries

- Do **not** modify `KANBAN.md`, `CHANGELOG.md`, `TODAY.md`, or any file other than the new spec file.
- Do **not** commit.
- Do **not** run pytest, ruff, or any other tooling unless answering a question you need to settle inside the spec.
- The new spec file is the only artifact this flow produces.
- If the WIP card's body conflicts with something you read in Step 1, prefer the card and call out the conflict as an entry in the spec's `Risks and open questions` section — do not silently reconcile.
- Reading source files, existing specs, or test files during Step 6 is allowed and expected. The boundary is on **writes**, not reads.
