# START.md

Hey, future me. You're in `django-strawberry-framework`. Read this once, then [AGENTS.md][agents] — that file is law, this one is context. Then go.

Advice from past me on keeping Rio happy and moving the package forward. ([CLAUDE.md][claude-md]'s whole job is to make sure you read AGENTS.md.)

## What this repo is

DRF-shaped Django integration for Strawberry GraphQL. Alpha, single maintainer, rapid iteration. Shipped: Meta-driven types, Relay connections, filters, orders, permissions, three mutation flavors (model / form / DRF serializer), the query optimizer, the Channels ASGI router. `pyproject.toml` = shipped version; [KANBAN.md][kanban] = in flight; [README.md][readme] = positioning; [GOAL.md][goal] = destination; [TODAY.md][today] = current capability snapshot; [docs/GLOSSARY.md][glossary] = capability catalog.

## How Rio communicates

Direct and decisive. Iterates fast, reverses course without ceremony, expects the same from you.

- Short imperative messages. "Now do X." "Scratch that, do Y." No hidden tone. Just DO the thing.
- They reverse decisions from a turn or two ago (session one: moved example tests in, then straight back out; both right at the time). Roll with it; don't argue old reasoning back.
- Pushback when a question has a hidden flaw is welcome — once. Surface it, suggest better, then defer. No lectures.
- No preamble, sycophancy, or over-explanation. 12 years of Django and Vue.js.

## Workflow rules they've set

The rules I most often forgot:

- **No `pytest` after edits.** Format only. They'll say "run tests" or "run the full pipeline" when they want it. Coverage gating means tests fail loud the moment they run.
- They commit themselves. Never auto-commit unless explicitly asked. **NEVER add `Co-Authored-By` or any author-attribution footer.** The commit message is the change description, nothing else.
- **NEVER create or switch branches without explicit authorization.** A commit request is not branch authorization — commit on the current branch and flag anything odd afterward. I once branched "helpfully" and misrouted Rio's concurrent commit onto my branch.
- After edits: `uv run ruff format .` (plus `ruff check --fix .` if there were edits), then stop. No `pytest`. No `manage.py check`. No `uv build`.
- When asked to commit, run the pre-commit hooks first. They check things ruff doesn't — ASCII-only source, .md link-def scaffold, trailing-comma layout — and passing `ruff format` is not passing the hooks.

## Concurrent sessions

Rio runs multiple sessions on this working tree — same branch, same checkout, same time. Normal. So:

- Unexpected dirty files, untracked files, or commits you didn't make are the other session's work. Never revert or "tidy" them; never reset `examples/fakeshop/db.sqlite3` while another session may be writing it.
- Stage explicitly (`git add <path>`), never `git add -A` — you'd sweep the other session's WIP into your commit. The reverse happens too: your uncommitted edits may land in their commit, so check `git log` before assuming your work is still unstaged.
- Don't regenerate the rendered docs below while another session's feature work is mid-flight — you'd publish half-landed surface.

## Rendered docs — fix the source, not the file

Three standing docs are generated; hand edits get clobbered on the next render:

- [docs/TREE.md][tree] — [scripts/build_tree_md.py][build-tree] renders from module docstrings plus the kanban DB's predicted-path rows (`--check` verifies without writing). A missing module docstring fails the render.
- [docs/GLOSSARY.md][glossary] — [scripts/build_glossary_md.py][build-glossary] renders from the fakeshop glossary app's DB. Edit the DB, re-render.
- [KANBAN.md][kanban] — [scripts/build_kanban_md.py][build-kanban] renders from the fakeshop kanban app's DB. (`KANBAN.html`'s Vue shell IS hand-edited — only its data block regenerates.)

## Temp artifact conventions

Per-cycle scratchpads — they close with their cycle:

- `docs/review/review-<X>.md`, `docs/review/rev-*.md` — REVIEW cycle.
- `docs/dry/dry-<X>.md` — DRY cycle.
- `docs/builder/bld-*.md` — BUILDER cycle.

Exempt from AGENTS.md's symbol-qualified path rule (raw `path:NN` refs are fine inside) and need no stylistic cleanup — the next cycle regenerates them. Still include them in repo-wide sanity checks (grep, audits) to flag drift, but don't edit unless the cycle is in flight.

## Style they care about

- **Meta classes everywhere on consumer surfaces.** Stacked Strawberry decorators on a consumer-facing class = the strawberry-graphql-django API, the explicit reason this package exists. Strawberry is the engine; DRF is the shape.
- All model text fields are `TextField`, not `CharField`, even for short strings. Personal preference; codified in the example models.

## Markdown link convention

Every .md file with cross-file links uses **reference-style** markdown — body uses `[text][ref-id]`; all defs live in one block at the bottom. [AGENTS.md][agents] and [CLAUDE.md][claude-md] are the only exempt files (agent-instruction prose, not standing docs). The exemption is real code: `EXEMPT_MD_SCAFFOLD_NAMES` in [scripts/check_trailing_commas.py][check-commas], whose `source-layout` pre-commit hook enforces the scaffold on every other .md file and auto-appends missing markers — don't hand-fight it. Specs get one more layer: [scripts/check_spec_glossary.py][check-spec-glossary] validates that a spec's project-specific terms link to real `GLOSSARY.md` anchors, in both inline and reference-style forms.

The block opens with the single-line delimiter `<!-- LINK DEFINITIONS -->` and carries all 10 canonical path-based group headers, in this exact order, present even when empty:

`<!-- Root -->`, `<!-- docs/ -->`, `<!-- docs/SPECS/ -->`, `<!-- docs/builder/ -->`, `<!-- django_strawberry_framework/ -->`, `<!-- tests/ -->`, `<!-- examples/ -->`, `<!-- scripts/ -->`, `<!-- .venv/ -->`, `<!-- External -->`.

Defs are alphabetical within each group: `[ref-id]: path/from/this/file/to/target`.

Why: when a file moves — archiving a spec to `docs/SPECS/`, restructuring `examples/`, any relocation — every inline `[text][ref-id]` use survives untouched; only the def paths at the bottom need re-relativizing. Move cost drops ~75% vs scattered inline `](path)` links.

Group = where the **target** lives, NOT the source. A README at `examples/fakeshop/` linking to `docs/GLOSSARY.md` puts the def under `<!-- docs/ -->`. Empty groups stay so a reader can confirm "this file links to nothing in `tests/`" in one scan.

The ten headers are a closed list (`LINK_DEF_CATEGORIES` in [scripts/check_trailing_commas.py][check-commas]), so a subdirectory shares its parent's group rather than earning an eleventh: an archived spec's companions live at `docs/SPECS/appx/` and their defs sit under `<!-- docs/SPECS/ -->`.

Stays inline (NOT converted):

- URLs (`https://...`, `http://...`).
- In-page anchors (`](#decision-N)`, `](#some-heading)`).
- Anything inside fenced code blocks — renders verbatim as example content.

New cross-file link: write `[text][ref-id]` inline; add `[ref-id]: path` to the correct group (alphabetical, path resolved from the source file's directory). Don't drift back to inline `](path)`.

Moving a .md file: only the bottom block's paths change; inline uses stay. Disk-exists-check each rewritten path before calling the move done — the convention makes link rot visible, not impossible.

## AGENTS.md

If updating that file keep it dense — no blank lines, no periods, no code blocks.

## Past mistakes to not repeat

- **Don't preemptively populate `conf.py` with future-feature settings.** Rio aggressively trimmed it. Add a settings key only when the feature that needs it lands.
- **Don't restore deleted files because you assume they belong.** Ask first. I once restored a `schema.py` and `test_schema_smoke.py` Rio had intentionally removed.
- **Don't add example-app coverage to the gate.** Rolled back once already. The package gets 100%; the example exercises the package via real flows, it doesn't gate the build.
- **Don't second-guess `field_name` patterns** in files mechanically translated from `django-graphene-filters`. I burned time deducing intent in the then-aspirational `filters.py`/`orders.py` (both since shipped; aggregates still ahead, on the beta line). When in doubt, mirror the old shape.
- **Don't over-harden a rule after context loss.** The commit rule is *no auto-commit*, not *never commit* — I once refused an explicit commit request because a compaction summary had hardened the rule. When a rule seems to forbid what Rio is explicitly asking, re-read the actual rule in AGENTS.md.

## Strategic advice

- The package rebuilds the overlap between `graphene-django` and `strawberry-graphql-django`, DRF-shaped. Unsure a feature belongs? Both libraries provide it = foundational, we need it. Only one = optional, probably a later spec.
- Behaviorally copy `strawberry-graphql-django`'s good ideas (especially the optimizer's downgrade-to-`Prefetch` rule when the target type has a custom `get_queryset`). Surface-wise copy `django-graphene-filters` (Meta-class API). Be honest about which side of the line a decision falls on.
- Build in slices; fork a subsystem into its own spec mid-stream when a slice grows past ~one module. Spec/card mechanics: [docs/builder/BUILD.md][build].
- Resist scope creep. This file once deferred filters, orders, aggregates, permissions, and the full connection field — all but aggregates have since shipped, each in its own deliberate slice, which is the point. The beta line (`0.1.x`) still defers `FieldSet`, full-text search, and aggregates. No "while I'm here" extras.
- Coverage is a feature, not a chore. A line that can't be covered by exercising the example is a smell — usually too-clever code or the wrong abstraction.

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
