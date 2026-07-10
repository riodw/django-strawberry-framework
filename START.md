# START.md

Hey, future me. You're walking into `django-strawberry-framework`. Read this once, then read [AGENTS.md][agents] — that file is law, this one is context. Then go.

This file is advice from past me to future me about how to keep Rio happy and how to actually move the package forward. Treat it as living context, not law — but don't ignore it. (There's also a [CLAUDE.md][claude-md]; its entire job is to make sure you read AGENTS.md.)

## What this repo is

DRF-shaped Django integration for Strawberry GraphQL. Alpha, single maintainer, rapid iteration. The surface has grown well past the early slices — Meta-driven types, Relay connections, filters, orders, permissions, three mutation flavors (model / form / DRF serializer), the query optimizer, and the Channels ASGI router have all shipped. `pyproject.toml` has the shipped version; [KANBAN.md][kanban] has what's in flight. See [README.md][readme] for the full positioning argument, [GOAL.md][goal] for the long-term destination, [TODAY.md][today] for the current capability snapshot, and [docs/GLOSSARY.md][glossary] for the package-wide capability catalog.

## How Rio communicates

Rio is direct and decisive. They iterate fast, they reverse course without ceremony, and they expect the same from you. Specifically:

- Short messages, often imperative. "Now do X." "Scratch that, do Y instead." Don't read tone where there isn't any. Just do the thing.
- They will reverse a decision they made one or two turns ago. This happened in the very first session around test placement — they had me put example tests inside the example app to mirror `django-graphene-filters`, then immediately had me move them all back. Both decisions were correct in their moment. Roll with the reversal; don't argue old reasoning back at them.
- They appreciate honest pushback when their question contains a hidden flaw, but only once. Surface the flaw, suggest the better path, then defer if they push past it. Don't lecture.
- They dislike preamble, sycophancy, over-explanation. They have 12 years of experience in Django and Vue.js

## Workflow rules they've set

These are the rules I most often forgot in past sessions and they had to remind me. Encode them now.

- **Do not run `pytest` after every change.** Run formatting only. They will explicitly say "run tests" or "run the full pipeline" when they want it. Coverage gating means tests will fail loud the moment they run.
- They commit themselves most of the time. Don't auto-commit unless they explicitly ask. **NEVER add a `Co-Authored-By` line (or any other author-attribution footer) to commit messages, regardless of who or what you are.** The commit message is the change description, nothing else.
- **NEVER create or switch branches without explicit authorization.** A commit request is not branch authorization — commit on whatever branch you're on and flag anything odd about it afterward. I once branched "helpfully" and misrouted Rio's concurrent commit onto my branch.
- When you make changes, run `uv run ruff format .` (and `ruff check --fix .` if there were edits) and stop there. No `pytest`. No `manage.py check`. No `uv build`.
- When you ARE asked to commit, run the pre-commit hooks first. They enforce checks the ruff pass doesn't — ASCII-only source, the .md link-def scaffold, trailing-comma layout — and passing `ruff format` is not passing the hooks.

## Concurrent sessions

Rio runs multiple Claude sessions against this same working tree — same branch, same checkout, at the same time. This is normal, not an anomaly. Consequences:

- Unexpected dirty files, untracked files, or commits you didn't make are the other session's in-flight work. Never revert or "tidy" them; never reset `examples/fakeshop/db.sqlite3` while another session may be writing it.
- Stage explicitly when committing (`git add <path>`), never `git add -A` — you'd sweep the other session's WIP into your commit. Expect the reverse too: your uncommitted edits may get swept into the other session's commit, so check `git log` before assuming your work is still unstaged.
- Don't regenerate the rendered docs below while another session's feature work is mid-flight — you'd publish half-landed surface.

## Rendered docs — fix the source, not the file

Three standing docs are generated; hand edits get clobbered on the next render:

- [docs/TREE.md][tree] — rendered by [scripts/build_tree_md.py][build-tree] from module docstrings plus the kanban DB's predicted-path rows (`--check` verifies without writing). A missing module docstring fails the render.
- [docs/GLOSSARY.md][glossary] — rendered by [scripts/build_glossary_md.py][build-glossary] from the fakeshop glossary app's database. Edit the DB, then re-render.
- [KANBAN.md][kanban] — rendered by [scripts/build_kanban_md.py][build-kanban] from the fakeshop kanban app's database. (`KANBAN.html`'s Vue shell IS hand-edited — only its data block regenerates.)

## Temp artifact conventions

Per-cycle scratchpads — they close when their cycle does:

- `docs/review/review-<X>.md`, `docs/review/rev-*.md` — REVIEW cycle.
- `docs/dry/dry-<X>.md` — DRY cycle.
- `docs/builder/bld-*.md` — BUILDER cycle.

These are exempt from AGENTS.md's symbol-qualified path rule (raw `path:NN` line refs are fine inside) and don't need stylistic cleanup — the next cycle regenerates them. Still worth *including* in repo-wide sanity checks (grep, audits) so you can flag obvious drift, but don't edit unless the cycle is in flight.

## Style they care about

- **Meta classes everywhere on consumer surfaces.** If you find yourself writing stacked Strawberry decorators on a consumer-facing class, stop. That is the strawberry-graphql-django API and the explicit reason this package exists. Strawberry is the engine; DRF is the shape.
- They prefer keeping all model text fields as `TextField`, not `CharField`, even for short strings. Personal preference; codified in the example models.

## Markdown link convention

Every .md file with any cross-file links uses **reference-style** markdown — inline uses in the body read `[text][ref-id]`; all defs live in a unified block at the bottom. [AGENTS.md][agents] and [CLAUDE.md][claude-md] are the only files exempt (agent-instruction prose, not standing docs). The exemption is real code, not habit: `EXEMPT_MD_SCAFFOLD_NAMES` in [scripts/check_trailing_commas.py][check-commas], whose `source-layout` pre-commit hook enforces the scaffold on every other .md file and auto-appends missing markers — don't hand-fight it. Specs get one more layer: [scripts/check_spec_glossary.py][check-spec-glossary] validates that a spec's project-specific terms link to real `GLOSSARY.md` anchors, and it understands both the inline and reference-style link forms.

The block opens with the single-line delimiter `<!-- LINK DEFINITIONS -->` and carries all 10 canonical path-based group headers, always present in this exact order even when a group is empty:

`<!-- Root -->`, `<!-- docs/ -->`, `<!-- docs/SPECS/ -->`, `<!-- docs/builder/ -->`, `<!-- django_strawberry_framework/ -->`, `<!-- tests/ -->`, `<!-- examples/ -->`, `<!-- scripts/ -->`, `<!-- .venv/ -->`, `<!-- External -->`.

Defs are alphabetical within each group: `[ref-id]: path/from/this/file/to/target`.

Why this matters: when a file moves — archiving a spec from `docs/` to `docs/SPECS/`, restructuring `examples/`, any future relocation — every inline `[text][ref-id]` use in the body survives the move untouched. Only the paths on the right side of each def at the bottom need re-relativizing. Move cost drops ~75% vs. scattered inline `](path)` links.

Group is determined by where the **target** lives in the repo, NOT where the source file lives. A README at `examples/fakeshop/` linking to `docs/GLOSSARY.md` puts the def under `<!-- docs/ -->`. Empty groups stay present so a reader can confirm "this file does not link to anything in `tests/`" in one scan instead of grepping.

What stays inline (NOT converted to ref-style):

- URLs (`https://...`, `http://...`).
- In-page anchors (`](#decision-N)`, `](#some-heading)`).
- Anything inside fenced code blocks — renders verbatim as example content.

When adding a new cross-file link: write `[text][ref-id]` inline; add `[ref-id]: path` to the correct group at the bottom (alphabetical within the group, path resolved from the source file's directory). Don't drift back to inline `](path)` for cross-file refs — the convention is in force across every .md file except AGENTS.md and CLAUDE.md.

When moving a .md file: only the bottom block's paths need updating. The inline `[text][ref-id]` uses stay as-is. Run a disk-exists check on each rewritten path before considering the move done; the convention makes link rot visible but doesn't prevent it.

## AGENTS.md

If updating this file Keep this document as dense as possible, don't even use blank lines or periods. No code blocks.

## Past mistakes to not repeat

These are real mistakes I made in past sessions. Don't repeat them.

- **Don't preemptively populate `conf.py` with future-feature settings.** I did that on the first pass and Rio aggressively trimmed it. The rule: add a settings key only when the feature that needs it lands.
- **Don't restore deleted files because you assume they belong.** When a file disappears, ask first. I once restored a `schema.py` and `test_schema_smoke.py` that Rio had intentionally removed.
- **Don't add coverage of the example app to the gate.** I expanded the coverage source once and Rio rolled it back. The package gets 100%; the example exists to exercise the package via real flows, not to gate the build.
- **Don't second-guess `field_name` patterns** in files mechanically translated from `django-graphene-filters`. I spent too long trying to deduce the original author's intent in the then-aspirational `filters.py`/`orders.py` (both have since shipped as real subsystems; aggregates is still ahead, on the beta line). When in doubt, mirror the old shape.
- **Don't over-harden a rule after context loss.** The commit rule is *no auto-commit*, not *never commit* — I once refused an explicit commit request because a compaction summary had hardened the rule in my head. When a rule seems to forbid something Rio is explicitly asking for, re-read the actual rule in AGENTS.md.

## Strategic advice

- The package is rebuilding the overlap between `graphene-django` and `strawberry-graphql-django`, DRF-shaped. When in doubt about whether a feature belongs, ask: do both libraries provide it? If yes, it's foundational and we need it. If only one does, it's optional and probably belongs in a later spec.
- Behaviorally we copy `strawberry-graphql-django`'s good ideas (especially the optimizer's downgrade-to-`Prefetch` rule when the target type has a custom `get_queryset`). Surface-wise we copy `django-graphene-filters` (Meta-class API). Be honest about which side of that line a decision falls on.
- Build in slices; don't be afraid to fork a subsystem into its own spec mid-stream when a slice grows past ~one module. The spec/card mechanics live in [docs/builder/BUILD.md][build].
- Resist scope creep. When this file was first written the package deferred filters, orders, aggregates, permissions, and the full connection field — all but aggregates have since shipped, each in its own deliberate slice, which is exactly the point. The beta line (`0.1.x`) still defers `FieldSet`, full-text search, and aggregates. Don't quietly mix in "while I'm here" extras that bloat the slice and complicate review.
- Coverage is a feature, not a chore. If a line can't be covered by exercising the example, that's a smell — it usually means the code is too clever or the wrong abstraction.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: AGENTS.md
[claude-md]: CLAUDE.md
[goal]: GOAL.md
[kanban]: KANBAN.md
[readme]: README.md
[today]: TODAY.md

<!-- docs/ -->
[glossary]: docs/GLOSSARY.md
[tree]: docs/TREE.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[build]: docs/builder/BUILD.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->
[build-glossary]: scripts/build_glossary_md.py
[build-kanban]: scripts/build_kanban_md.py
[build-tree]: scripts/build_tree_md.py
[check-commas]: scripts/check_trailing_commas.py
[check-spec-glossary]: scripts/check_spec_glossary.py

<!-- .venv/ -->

<!-- External -->
