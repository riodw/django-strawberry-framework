# NEXT.md — New Spec Builder Agent Flow

You have been invoked to author a new spec file under `docs/` for the next-up Work-In-Progress card in this repository.

Spec files live at the root of `docs/` (e.g. `docs/spec-0XX-**-X_X_X.md`), NOT under `docs/SPECS/`. The older `docs/SPECS/spec-*.md` files are legacy / archived locations — read them from there for structural reference (Step 5), but new specs you create land in `docs/`.

Execute the steps below **in strict order**. Do not skip ahead. Do not read files outside the batch named in the current step. Do not start writing the new spec before Step 6. Step 3 is allowed to archive prior live specs and update the kanban DB before the new spec exists; that is queue maintenance, not new-spec authoring.

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

## Step 3 — Normalize the active spec queue

Now (and only now) read `KANBAN.md`. The file is large — use `rg -n "^## " KANBAN.md` first to scan section headers, then read the `## In progress` column in full. You do not need to read the `## To Do`, `## Blocked`, or `## Done` columns *in full* to author the spec — but you DO need a lightweight scan of the `## To Do` and `## Done` card IDs for the target's patch version (see the joint-cut note below); that scan is card-ID/version-level, not a body read.

Before selecting the next card, archive every existing live spec at the top level of `docs/`. The invariant after Step 6 is **exactly one WIP spec file at `docs/spec-*.md`**: the one this flow just authored. To keep that invariant, any `docs/spec-*.md` or companion `docs/spec-*-terms.csv` that exists at Step 3 is a prior in-flight spec and must move to `docs/SPECS/` before the new spec is written. Use the Step 8 archive procedure in **pre-write archive mode**:

- The archive set is every `docs/spec-*.md` and matching `*-terms.csv` currently at the top level of `docs/`.
- There is no active new spec yet, so skip Step 8 action 4 (rewriting references inside the new spec) and skip Step 8 action 6 (creating the new active card's `SpecDoc`).
- Do run the reference-definition rewrite, all moved-spec `SpecDoc.url` repoints, and the `KANBAN.md` / `KANBAN.html` regeneration.
- If no root-level `docs/spec-*.md` exists, this pre-write archive pass is a clean no-op.

Then normalize the kanban queue in the database, not by editing `KANBAN.md`. The queue has two distinct axes:

- `Card.planning_state.key == "in_progress"` controls the `## In progress` board column.
- `Card.status.key == "wip"` controls the `WIP-...` card ID and the WIP row in the `## WIP / DONE spec map`.

The flow must leave **exactly one non-Done card with `status.key == "wip"`**. Multiple cards may share `planning_state == "in_progress"` when they belong to the same active version, but only the lowest-numbered one is the WIP spec target.

Use the example project's shell to make the card-state edit:

```
uv run python examples/fakeshop/manage.py shell -c "<ORM edit>"
uv run python scripts/build_kanban_md.py
uv run python scripts/build_kanban_html.py
```

The ORM edit follows this deterministic algorithm:

1. Treat every existing non-Done `WIP` card as in-progress by setting its `planning_state` to `in_progress` before target selection. This repairs stale split-axis states.
2. Build the current in-progress pool from all non-Done cards whose `planning_state.key == "in_progress"` or whose `status.key == "wip"`, sorted by `Card.number`.
3. If the pool is non-empty, select the lowest-numbered card in that pool as the target. Set that target to `status = wip` and `planning_state = in_progress`. Set every other non-Done `wip` card back to `status = todo`; leave its planning state alone if it is part of the in-progress pool.
4. If the pool is empty, find the **next version** by taking the lowest semantic `TargetVersion.number` among non-Done `todo` cards. Move **all** non-Done `todo` cards for that version to `planning_state = in_progress`, select the lowest-numbered card among them as the target, set that target to `status = wip`, and leave the other same-version cards at `status = todo`.
5. If there is no non-Done `todo` card, stop and report that the board has no schedulable next card.
6. Re-render `KANBAN.md` and `KANBAN.html`, then verify the rendered board has exactly one `WIP-...` card and that the target card is the lowest-numbered card in the in-progress pool.

Worked ORM edit for the queue normalization (copy-paste as the `<ORM edit>` above):

```
from django.db.models import Q

from apps.kanban.models import Card, PlanningState, Status


def version_key(version):
    return tuple(int(part) for part in version.split("."))


todo = Status.objects.get(key="todo")
wip = Status.objects.get(key="wip")
in_progress = PlanningState.objects.get(key="in_progress")

scheduled = Card.objects.filter(status__key__in=("wip", "todo")).select_related(
    "status",
    "planning_state",
    "target_version",
)

# Repair stale split-axis rows first: any WIP row is active work.
for card in scheduled.filter(status=wip).exclude(planning_state=in_progress):
    card.planning_state = in_progress
    card.save(update_fields=["planning_state"])

pool = sorted(
    scheduled.filter(Q(planning_state=in_progress) | Q(status=wip)),
    key=lambda card: card.number,
)

if not pool:
    todo_cards = list(scheduled.filter(status=todo))
    if not todo_cards:
        raise SystemExit("No non-Done TODO card is available for the next spec.")
    next_version = min(
        {card.target_version.number for card in todo_cards},
        key=version_key,
    )
    pool = sorted(
        [card for card in todo_cards if card.target_version.number == next_version],
        key=lambda card: card.number,
    )
    Card.objects.filter(pk__in=[card.pk for card in pool]).update(
        planning_state=in_progress,
    )

target = pool[0]
scheduled.filter(status=wip).exclude(pk=target.pk).update(status=todo)

target.status = wip
target.planning_state = in_progress
target.save(update_fields=["status", "planning_state"])

print(f"Selected {target.card_id} - {target.title}")
```

Now determine **which other non-Done cards (WIP *and* To-Do) share the target card's patch version** — a lightweight scan of card IDs and their trailing `-X.Y.Z` across the `## In progress` and `## To Do` columns after the re-render (search the board for the patch version with `rg`; you don't need to read those cards' bodies). Checking only the WIP card is NOT enough: a card can be the sole WIP card yet still share its patch version with in-progress or unstarted To-Do cards. The ownership rule: if **any other non-Done card** shares the target's patch version, the `pyproject.toml` / `__version__` / `tests/base/test_init.py` bump is owned by the **joint cut** (the last card of that patch line to land), so the target's spec defers it; if the target is the **only non-Done card** at its patch version, its Slice 5 owns the bump. Finally, glance at the `## Done` column for a same-patch card that already **deferred its cut to your target** — that confirms your spec is the one that completes the joint cut and thus owns the bump. Record what you find so [Step 6](#step-6--write-the-spec) can pin the right Decision.

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

- For each older `spec-*.md`, run `rg -n "^##|^###" <path>` to capture its section list — do not read the body unless a specific decision shape requires it.
- Recent specs may exceed several thousand lines and can exceed a single read's token limit. If a full read fails, use `rg` to find anchors first, then read with `offset` / `limit` to grab just the sections you need.

What to internalize:

- **Filename convention**: `spec-<NNN>-<topic>-<X_Y_Z>.md`, where `<NNN>` matches the KANBAN card's NNN, `<topic>` is a short snake_case slug naming the card's subject, and `<X_Y_Z>` is the target milestone version with dots replaced by underscores — **this is not restricted to the `0.0.x` ALPHA line**; always derive it from the card's actual trailing `-X.Y.Z`. Worked examples: ALPHA card `DONE-020-0.0.7 — DjangoListField (non-Relay list)` → file `spec-020-list_field-0_0_7.md`; BETA card `TODO-BETA-046-0.1.1 — <topic>` → file `spec-046-<topic>-0_1_1.md`.
- **Section layout**: the recent specs all carry roughly the same skeleton, in this order — frontmatter with revision history, **Key glossary references**, **Slice checklist**, **Problem statement**, **Current state**, **Goals**, **Non-goals**, **Borrowing posture** (when upstreams ship a comparable primitive), **User-facing API** (when the spec adds a consumer-visible symbol), **Architectural decisions** (numbered), **Implementation plan** (with a per-slice delta table), **Edge cases and constraints**, **Test plan**, **Doc updates**, **Risks and open questions**, **Out of scope (explicitly tracked elsewhere)**, **Definition of done**. Follow the most-recent spec when in doubt.
- **Voice and depth**: these specs are detailed and decision-heavy. Every choice is pinned with rationale; every alternative considered is named and rejected with a reason.
- **Cross-references**: source files are cited as repository-relative paths using symbol-qualified `path::QualifiedName` form (e.g. `types/base.py::DjangoType.resolve_fields`), with `#"unique substring"` pinpoints for in-body lines and `path #"unique substring"` for module-level lines (per [`AGENTS.md`][agents] #"Source references in docs and code comments: use symbol-qualified paths"); KANBAN cards by their full ID; prior specs by markdown link; upstream packages by absolute local path from `docs/TREE.md`.
- **Markdown link style**: cross-file links are reference-style — inline body uses are `[text][ref-id]`; all defs live in a unified bottom block opened by `<!-- LINK DEFINITIONS -->` with the 10 canonical path-based group headers (`<!-- Root -->`, `<!-- docs/ -->`, `<!-- docs/SPECS/ -->`, `<!-- docs/builder/ -->`, `<!-- django_strawberry_framework/ -->`, `<!-- tests/ -->`, `<!-- examples/ -->`, `<!-- scripts/ -->`, `<!-- .venv/ -->`, `<!-- External -->`) always present even when empty. URLs, in-page anchors, and fenced-code-block content stay inline. Group is determined by where the target lives, not where the source file lives. Don't drift back to inline `](path)` for cross-file refs. See [`START.md`][start] "Markdown link convention" for the why and the move-cost argument.
- **Permission caveat**: the recent specs explicitly note that `AGENTS.md` prohibits `CHANGELOG.md` edits without permission and that the spec's Slice 5 grants that permission. Mirror this in your spec.

---

## Step 6 — Write the spec

Create the new file at:

```
docs/spec-<NNN>-<topic>-<X_Y_Z>.md
```

Where:

- `<NNN>` = the NNN from the WIP card you identified in Step 3.
- `<topic>` = a short snake_case slug describing the card's subject.
- `<X_Y_Z>` = the version segment from the WIP card's trailing `-X.Y.Z`, with dots replaced by underscores (e.g. `0.0.7` → `0_0_7`, `0.1.1` → `0_1_1`, `0.1.0` → `0_1_0`).

The spec must:

- Match the structure, voice, and depth of the most-recently-shipped existing spec (either `docs/spec-*.md` or `docs/SPECS/spec-*.md`, whichever is most recent).
- Carry every constraint, recommended architectural direction, and open design question from the KANBAN card body into the spec body — expanded with rationale, not merely quoted. If the card already pre-pins a "Recommended architectural direction" block (some do, some don't), preserve it as a Decision and add the alternatives-rejected language; do not re-litigate it.
- Cite source files with repository-relative paths (e.g., `django_strawberry_framework/types/base.py`). You MAY read source files during Step 6 to ground decisions — that is not a boundary violation; only file modification is.
- If the target card has a `Verified in upstream` section, read every upstream file cited there before pinning the spec's borrowing posture, public API, or implementation decisions. This is mandatory for Alpha parity cards: the spec must be grounded in the named `graphene_django` / `strawberry_django` source, then adapted to this package's DRF-first API instead of guessing from memory.
- Resolve as many of the card's open design questions as the available evidence supports; leave the remainder as entries inside the `Risks and open questions` section (not a standalone section), naming a preferred answer for the target version and a fallback.
- Pin alternatives considered and rejected with a reason — do not silently drop them.
- If **any other non-Done card** (WIP or To-Do) shares the target's patch version (per Step 3), include a Decision that explicitly defers the `pyproject.toml` / `__version__` / `tests/base/test_init.py` version bump to the joint cut, and the Slice 5 / Definition of done checklist must NOT bump the version. If the target is the **only non-Done card** at its patch version, the reverse holds — its Slice 5 owns the bump; mirror the lone-card version-bump Decision from the most recent lone-card spec (e.g. `spec-038`), and the shared-cut deferral Decision from the most recent joint-cut spec (e.g. `spec-039`).
- **Milestone (`.0`) cuts carry more than a version bump.** If the target card's version is a minor-version rollover (a trailing `-X.Y.0` — e.g. `0.1.0` completing ALPHA, or `1.0.0` completing BETA; the `## To Do - Alpha (0.1.0)` / `## To Do - Beta (1.0.0)` board headers name these release targets), it is a **milestone cut**, not a routine patch bump. Its Slice 5 doc-updates list expands beyond the usual set: lift any `alpha constraint` (or the milestone's constraint) status tags in `docs/GLOSSARY.md` that the milestone releases, advance the `## Progress to 1.0.0` board section, and flip the milestone-status prose in `README.md` / `GOAL.md` / `TODAY.md`. Treat these milestone-completion chores as first-class Slice 5 deliverables, not afterthoughts.
- The Slice 5 doc-updates list typically touches: `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `README.md`, `GOAL.md`, `TODAY.md`, `KANBAN.md`, `CHANGELOG.md`. Not every spec touches all eight; include each only when the card's surface change is reflected there.

---

## Step 7 — Anchor every project-specific term to the glossary

Author a companion `*-terms.csv` next to the new spec at:

```
docs/spec-<NNN>-<topic>-<X_Y_Z>-terms.csv
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

The instinct to "trim CSV rows that don't have GLOSSARY headings" happens AFTER the over-zealous first pass, driven by the checker's output. Do NOT pre-emptively skip a term because you are unsure it has a glossary entry. Do NOT skip a term because you already linked it in the spec body — the CSV is the audit ledger, not a duplicate of the spec body. Let the script tell you which rows to drop; do not pre-decide.

Then run the checker:

```
uv run python scripts/check_spec_glossary.py --spec docs/spec-<NNN>-<topic>-<X_Y_Z>.md
```

(`--terms` and `--glossary` default sensibly when the CSV lives next to the spec and the glossary stays at `docs/GLOSSARY.md`.)

Pass condition: the script exits 0 with `OK: N terms — all have glossary entries and at least one spec link.` That output is the proof that **everything is accounted for** — every term in the CSV resolves to a real GLOSSARY heading, and every term has at least one reference-style glossary link (`[text][glossary-...]` plus a matching bottom definition targeting `GLOSSARY.md#<anchor>`). Legacy inline `](GLOSSARY.md#<anchor>)` links still satisfy the checker, but new specs should use the reference-style convention from [`START.md`][start].

Two failure modes and their resolutions:

- **Missing glossary entries** (the term's anchor has no matching `## <heading>` in `docs/GLOSSARY.md`). Resolve this before Step 8. Either the term is misspelled in the CSV (fix the row), the term does not warrant a glossary row after inspection (delete the row), or the spec genuinely needs a new glossary entry. If a new entry is needed, stop and ask the maintainer whether to authorize the DB-backed glossary update in this flow; do not leave an unresolved CSV row and proceed, because the checker cannot exit 0 with a missing heading.
- **Missing spec links** (the spec mentions the term in prose but doesn't link it to the glossary). Add a reference-style glossary link manually, OR re-run the checker with `--auto-link` to rewrite the spec in place — it wraps the first non-code, non-link occurrence of each term as `[term][glossary-<anchor>]` (and prefers the backtick-wrapped form when the spec already says e.g. `Meta.fields` in inline code) and inserts the matching `[glossary-<anchor>]: GLOSSARY.md#<anchor>` definition under the `<!-- docs/ -->` group. The auto-link pass is idempotent.

Repeat the CSV edit / checker run cycle until the script exits 0. The CSV is the source of truth: trim it when a term does not warrant a glossary entry, extend it when a new term needs one. The CSV is committed alongside the spec so future maintainers can re-run the check whenever the GLOSSARY or the spec changes.

---

## Step 8 — Archive prior specs and update cross-references

After Step 7 exits 0, run the archive/reference sweep again as an idempotent final check. Step 3 should already have archived every pre-existing live spec before the new spec was written; this step catches any leftover root-level spec and attaches the active WIP card to the new spec. Archive every OTHER spec file that lives in `docs/` so the active working directory only contains the spec you just authored. Each prior spec moves to its legacy home under `docs/SPECS/` and every cross-reference to it gets rewritten in the same pass so no link goes stale. The active WIP card in `KANBAN.md` also gets a reference to the active spec added or updated as part of the same sweep.

The "active" spec is the one you just authored in Step 6. Every other `spec-*.md` (and its companion `*-terms.csv` if present) is a prior in-flight spec from an earlier card cycle that should now live under `docs/SPECS/` alongside the older legacy specs.

> **The most important part of this step is the cross-reference sweep — TO and FROM every moved spec.** A spec move is mechanically cheap (`git mv`) but link-fragile: when `docs/spec-XXX-…` becomes `docs/SPECS/spec-XXX-…`, three classes of link rot the instant the move lands and only one of them is obvious. **All three MUST be fixed in the same pass:**
>
> 1. **FROM other files → the moved spec** (links elsewhere that point AT the spec you just moved). The path target changes; every reference-style definition like `[spec-XXX]: spec-XXX-…`, `[spec-XXX]: docs/spec-XXX-…`, or `[spec-XXX]: ../spec-XXX-…` must be rewritten, and legacy inline links like `](spec-XXX-…)` / `](docs/spec-XXX-…)` / `](../spec-XXX-…)` must be rewritten too. This includes every doc, `KANBAN.md`, and the new active spec.
> 2. **FROM the moved spec → everywhere else** (links INSIDE the moved spec body pointing at repo files). Every relative path inside the spec body just shifted one directory deeper. In current specs those paths are usually bottom link definitions, not inline links — e.g. `[kanban]: ../KANBAN.md` from `docs/spec-XXX-…` is correct, but from `docs/SPECS/spec-XXX-…` it must become `[kanban]: ../../KANBAN.md`; `[rf-inputs]: ../django_strawberry_framework/...` must become `[rf-inputs]: ../../django_strawberry_framework/...`; `[glossary-foo]: GLOSSARY.md#foo` must become `[glossary-foo]: ../GLOSSARY.md#foo`. The file's contents did not change but the file's location did, and every relative target inside it is now wrong by one `../` level unless rewritten. **This is the failure mode that gets missed** because the visible diff is just a rename — the broken links live inside the moved file's unchanged body.
> 3. **Between specs that BOTH moved in the same sweep** (links inside one archived spec that point at another archived spec). The two specs are now siblings under `docs/SPECS/`, so a reference definition like `[spec-YYY]: SPECS/spec-YYY-…` becomes `[spec-YYY]: spec-YYY-…`, and a former sibling-under-`docs/` target like `[spec-YYY]: spec-YYY-…` stays `[spec-YYY]: spec-YYY-…` (now a sibling under `docs/SPECS/`) — same surface, different meaning. Verify every one.
>
> Bias toward over-searching. Missing references rot silently and only surface when a future reader follows the link. False positives are cheap to dismiss; false negatives are invisible until they bite.

> **`KANBAN.md` / `KANBAN.html` are GENERATED files — edit the database, not the rendered files.** `KANBAN.md` is rendered from the `apps.kanban` Django app's database (in the fakeshop example project) by `scripts/build_kanban_md.py`; `KANBAN.html` is rendered from the same DB by `scripts/build_kanban_html.py`. The committed files are exports, not sources. **Hand-edits to them decay** — they are silently overwritten the next time anyone re-renders the board. So the KANBAN parts of this sweep (actions 5 and 6 below) are made in the DB and then re-rendered, NOT by editing the generated files:
>
> - **Both the `## WIP / DONE spec map` table row AND a card's `Spec:` body line are rendered from the one `SpecDoc` model** (`apps/kanban/models.py::SpecDoc`: `card` one-to-one, unique `name`, `url`). `url` is a GitHub `…/blob/main/<repo-path>` URL; the renderer strips the `blob/main/` prefix to produce the in-repo link, so the path you want in `KANBAN.md` is whatever follows `blob/main/` in `SpecDoc.url`. There is no separate "spec map" data — one `SpecDoc` per card drives both surfaces.
> - **To repoint a moved spec's link** (action 5): update that card's `SpecDoc.url` to the new path, e.g. `…/blob/main/docs/SPECS/spec-<old_NNN>-…`.
> - **To add/fix the active card's spec reference** (action 6): `update_or_create` a `SpecDoc(card=<active card>, name="spec-<NNN>-<topic>-<X_Y_Z>", url="…/blob/main/docs/spec-<NNN>-<topic>-<X_Y_Z>.md")`. A card with no `SpecDoc` renders as `No dedicated spec`.
> - **Make the DB edits via the example project's shell**, then re-render:
>
>   ```
>   uv run python examples/fakeshop/manage.py shell -c "<ORM edit>"
>   uv run python scripts/build_kanban_md.py     # re-export KANBAN.md from the DB
>   uv run python scripts/build_kanban_html.py   # re-export KANBAN.html from the DB
>   ```
>
>   The render scripts rewrite the generated files from the DB, so confirm the resulting `git diff KANBAN.md KANBAN.html` shows ONLY your intended card-state and spec-reference changes (a clean diff also proves the committed exports were already in sync with the DB).
> - **Card-body prose that mentions a spec path inside a `CardItem.text` row** (e.g. a "Requires spec: `docs/spec-…`" line buried in a Done card's Scope/DoD prose) is historical card text, NOT a `SpecDoc`-driven link. Leave it — it is out of scope per the "no card-body content changes beyond the spec-reference line" boundary, and re-rendering will preserve it verbatim.

**Worked example (copy-paste, then fill the `<…>` blanks).** This is the entire KANBAN spec-reference side of actions 5 + 6 — one shell call that (a) creates/updates the active card's `SpecDoc` and (b) repoints each archived spec's `SpecDoc` to `docs/SPECS/`, followed by the re-render and the clean-diff check. Card-status / planning-state queue normalization already happened in Step 3. `Card.number` is the card's NNN (e.g. `30` for `WIP-ALPHA-030-0.0.9`). Run from the repo root:

```
uv run python examples/fakeshop/manage.py shell -c "
from apps.kanban.models import Card, SpecDoc
BLOB = 'https://github.com/riodw/django-strawberry-framework/blob/main'

# (action 6) active WIP card -> the spec you just authored; creates the row if absent.
SpecDoc.objects.update_or_create(
    card=Card.objects.get(number=<NNN>),
    defaults={
        'name': 'spec-<NNN>-<topic>-<X_Y_Z>',
        'url': f'{BLOB}/docs/spec-<NNN>-<topic>-<X_Y_Z>.md',
    },
)

# (action 5) every spec you moved to docs/SPECS/ this sweep -> repoint its card's SpecDoc.
# One (number, name-without-.md) tuple per archived spec; usually just the prior cycle's spec.
for number, name in [(<OLD_NNN>, 'spec-<OLD_NNN>-<old_topic>-<old_version>')]:
    sd = SpecDoc.objects.get(card__number=number)
    sd.url = f'{BLOB}/docs/SPECS/{name}.md'
    sd.full_clean(); sd.save()
"
uv run python scripts/build_kanban_md.py            # re-export KANBAN.md from the DB
uv run python scripts/build_kanban_html.py          # re-export KANBAN.html from the DB
git --no-pager diff KANBAN.md KANBAN.html           # expect ONLY intended card/spec changes
```

The modified `examples/fakeshop/db.sqlite3` is the durable artifact — `KANBAN.md` / `KANBAN.html` are just its exports, so the committed DB is what carries the change forward. Leave all three edited together for the maintainer to commit.

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
3. **Rewrite cross-references INSIDE each moved spec** (the "FROM the moved spec → everywhere else" direction — the failure mode most likely to be missed). When a spec at `docs/spec-<old_NNN>-…` becomes `docs/SPECS/spec-<old_NNN>-…`, every relative link target inside its body must be re-relativized one directory deeper. Current specs use reference-style links, so enumerate reference definitions first, then legacy inline links:

   ```
   rg -n '^\[[^][]+\]:\s+' docs/SPECS/spec-<old_NNN>-…
   rg -n '\]\([^)]+\)' docs/SPECS/spec-<old_NNN>-…
   ```

   Classify each target into one of these buckets:

   - **Repo-root files** (`KANBAN.md`, `README.md`, `GOAL.md`, `TODAY.md`, `AGENTS.md`, `CHANGELOG.md`, `pyproject.toml`, `BACKLOG.md`, …): `[kanban]: ../KANBAN.md` → `[kanban]: ../../KANBAN.md`, `](../README.md)` → `](../../README.md)`, etc.
   - **`docs/` siblings** (`GLOSSARY.md`, `TREE.md`, `README.md`, `feedback.md`, the new active spec): `[glossary]: GLOSSARY.md` → `[glossary]: ../GLOSSARY.md`, `[glossary-foo]: GLOSSARY.md#foo` → `[glossary-foo]: ../GLOSSARY.md#foo`, `[tree]: TREE.md` → `[tree]: ../TREE.md`.
   - **`NEXT.md`**: because this flow itself lives at `docs/SPECS/NEXT.md`, `[next]: SPECS/NEXT.md` from a `docs/` spec becomes `[next]: NEXT.md` after the spec moves into `docs/SPECS/`. Verify the actual file location before rewriting any nonstandard target.
   - **Specs that ALSO moved in the same sweep** — these are now `docs/SPECS/` siblings of the file being rewritten, so paths simplify: `[spec-YYY]: SPECS/spec-YYY-…` → `[spec-YYY]: spec-YYY-…`, and a former `[spec-YYY]: spec-YYY-…` sibling-under-`docs/` reference stays `[spec-YYY]: spec-YYY-…` (now a sibling under `docs/SPECS/`).
   - **The new active spec** — from a moved spec under `docs/SPECS/`, a link to the newly-authored live spec under `docs/` must use `../spec-<NNN>-<topic>-<X_Y_Z>.md`.
   - **Source / test / example / script files under repo root** (`django_strawberry_framework/...`, `tests/...`, `examples/...`, `scripts/...`, `.venv/...`): `[rf-inputs]: ../django_strawberry_framework/foo.py` → `[rf-inputs]: ../../django_strawberry_framework/foo.py`; inline `](../tests/foo.py)` → `](../../tests/foo.py)`.
   - **External sibling checkouts referenced through `..`** (`../../django-graphene-filters/...`, `../../strawberry-django-main/...` from a `docs/` spec): add one more parent after the move, e.g. `[upstream]: ../../django-graphene-filters/...` → `[upstream]: ../../../django-graphene-filters/...`.
   - **In-spec anchors** (`#decision-N`, `#some-heading`) and **absolute URLs** (`https://…`) — unchanged.
   - **Companion CSV** (the moved spec's own `*-terms.csv` — also moved): if the spec body links to it (`spec-<old_NNN>-…-terms.csv`), the link stays as-is (still a sibling).

   This is best done as a single deterministic transformation pass over the file (a short script that classifies every reference-definition target and every legacy inline-link target against the rules above) rather than ad-hoc edits, so no link is missed and no replacement-ordering hazard arises.
4. **Rewrite cross-references in the new spec** (the "FROM the active spec → moved spec" direction). Search the spec you just authored for reference definitions and legacy inline links that point at any moved spec — match targets like `spec-<old_NNN>-…`, `./spec-<old_NNN>-…`, and `docs/spec-<old_NNN>-…`. Each match becomes the new path under `docs/SPECS/` (relative-path discipline: from a spec in `docs/`, the moved sibling is now at `SPECS/spec-<old_NNN>-…`).
5. **Rewrite cross-references in every other doc, INCLUDING `KANBAN.md`** (the "FROM the rest of the repo → moved spec" direction). Enumerate every doc that references the moved spec(s):

   ```
   rg -n "spec-<old_NNN>-<old_topic>-<old_version>" docs/ README.md GOAL.md TODAY.md AGENTS.md KANBAN.md
   ```

   For each hit, rewrite the reference definition or legacy inline-link path so the link still resolves after the move. Relative-path discipline: from `docs/GLOSSARY.md` the moved file is `SPECS/spec-…`; from repo-root `README.md` / `GOAL.md` / `TODAY.md` / `AGENTS.md` it is `docs/SPECS/spec-…`; from another spec under `docs/` it is `SPECS/spec-…`; from an archived spec under `docs/SPECS/` it is `spec-…`. Apply each rewrite in place — **except `KANBAN.md` / `KANBAN.html`**: they are generated exports (see the callout above), so their spec-map row and card `Spec:` line for a moved spec are repointed by updating that card's `SpecDoc.url` in the DB (set the path after `blob/main/` to `docs/SPECS/spec-…`) and re-rendering with `uv run python scripts/build_kanban_md.py` and `uv run python scripts/build_kanban_html.py`. Do NOT hand-edit either generated file — the edit would not survive the next render.
6. **Add or update the active WIP card's reference to the new spec.** The card you targeted in Step 3 should point at the spec file you just authored — a `SpecDoc` row whose `url` resolves to `docs/spec-<NNN>-<topic>-<X_Y_Z>.md`. Because `KANBAN.md` / `KANBAN.html` are generated exports (see the callout above), this is a **DB edit + re-render**, not a file edit. Query the card's current `SpecDoc` (via `apps/kanban/models.py::SpecDoc`) and handle three cases:

   - **No `SpecDoc` present** (the spec map renders `No dedicated spec`) — create one: `SpecDoc.objects.update_or_create(card=<active card>, defaults={"name": "spec-<NNN>-<topic>-<X_Y_Z>", "url": "https://github.com/<org>/<repo>/blob/main/docs/spec-<NNN>-<topic>-<X_Y_Z>.md"})`. The renderer surfaces it as both the spec-map row and a card-body `Spec:` line automatically.
   - **`SpecDoc` present but `url` points at a different path** (e.g. a stale `docs/SPECS/spec-…` from a prior archive cycle, or a now-renamed slug) — update `SpecDoc.url` (and `name` if the slug changed) to the active path.
   - **`SpecDoc.url` already correct** — no action.

   Make the edit via `uv run python examples/fakeshop/manage.py shell -c "<ORM edit>"`, then `uv run python scripts/build_kanban_md.py` and `uv run python scripts/build_kanban_html.py`, and confirm `git diff KANBAN.md KANBAN.html` shows only the intended spec-reference change. The card's column is irrelevant — `SpecDoc` is keyed on the card, not its board column, so a card moved to `## Done` between Step 3 and Step 8 still resolves through the same `SpecDoc` and re-renders in its new column.
7. **`CHANGELOG.md` stays reserved.** `CHANGELOG.md` has its own maintainer-edited protocol and is NOT rewritten by this step even when it references a moved spec. If `rg` finds matches in `CHANGELOG.md`, surface them as a one-line report at the end of the flow ("`CHANGELOG.md` references moved spec(s) at lines …; maintainer must update") and STOP — do not silently edit.
8. **Verify every rewritten link resolves.** Before closing the step, spot-check a representative sample of the rewrites — pick 5–10 paths across the categories above (one repo-root link, one `docs/` sibling, one inter-archived-spec link, one source-file link) and confirm each target file exists at the path the rewritten link now claims. Broken links land silently; this is the only check that catches a category miss in the transformation pass.
9. **Re-run the checker** against the new spec one more time:

   ```
   uv run python scripts/check_spec_glossary.py --spec docs/spec-<NNN>-<topic>-<X_Y_Z>.md
   ```

   The archive pass may have shifted markdown link paths inside the new spec; the script's earlier exit-0 must still hold. If it now fails, fix the cross-reference rewrites until it exits 0 again.

This step is idempotent. A second pass with no other specs at `docs/` top-level and `KANBAN.md` / `KANBAN.html` already pointing at the active spec is a clean no-op.

The flow is complete when Step 8 finishes: only the active spec and its CSV live at `docs/spec-*`, every prior spec is at `docs/SPECS/spec-*`, every cross-reference resolves (including in `KANBAN.md` / `KANBAN.html`), exactly one non-Done card has `status.key == "wip"`, and the checker exits 0 against the active spec.

---

## Boundaries

- Do **not** modify `CHANGELOG.md` under any circumstance during this flow — even path-update edits triggered by Step 8 must be surfaced as a maintainer-report rather than silently applied.
- Do **not** modify `TODAY.md` except as a Step 8 path-update (rewriting a moved spec's path); content edits to `TODAY.md` outside that narrow purpose are out of scope.
- `KANBAN.md` / `KANBAN.html` card data IS in scope for this flow — Step 3 may update `Card.status` and `Card.planning_state` to select the single WIP target, and Step 8 may repoint moved-spec links and add/fix the active WIP card's spec reference — but both files are **generated exports**, so those changes are made in the `apps.kanban` DB (`examples/fakeshop/db.sqlite3`) and re-rendered with `scripts/build_kanban_md.py` / `scripts/build_kanban_html.py`, NOT by hand-editing the generated files. The only DB edits in scope are Step 3 queue normalization (`Card.status`, `Card.planning_state`) and Step 8 spec-reference repoints/creates (`SpecDoc` rows); no other DB changes (no `CardItem.text` / card-body prose edits beyond what `SpecDoc` drives).
- Do **not** modify any file other than the new spec file, its companion `*-terms.csv`, the spec files being archived under Step 8, the cross-reference updates Step 8 prescribes in `docs/`, `README.md`, `GOAL.md`, `TODAY.md`, and `AGENTS.md`, and — for kanban — the regenerated `KANBAN.md` / `KANBAN.html` plus `examples/fakeshop/db.sqlite3` carrying the `apps.kanban` rows they are rendered from.
- Do **not** commit.
- Do **not** run pytest, ruff, or any other tooling unless Step 7 or Step 8 prescribes it (the `scripts/check_spec_glossary.py` run including its `--auto-link` rewrite, the `git mv` / `rg` invocations Step 8 names, and — for kanban DB edits — the `examples/fakeshop/manage.py shell` ORM edit plus the `scripts/build_kanban_md.py` / `scripts/build_kanban_html.py` re-renders are all part of the flow) or you need to settle a question inside the spec.
- The artifacts this flow produces: the new spec file, its companion `*-terms.csv`, the moves of every prior `spec-*.md` (and companion CSV) from `docs/` to `docs/SPECS/`, path-only cross-reference updates in every doc that pointed at a moved spec, and — for the active WIP card's spec reference, any moved-spec links, and queue normalization in generated kanban — `examples/fakeshop/db.sqlite3` carrying the `apps.kanban` rows plus the regenerated `KANBAN.md` / `KANBAN.html` they export to.
- The flow is not complete until (a) `scripts/check_spec_glossary.py` exits 0 against the new spec and its CSV, (b) Step 8 has run and no `spec-*.md` other than the active one remains at `docs/` top-level, (c) exactly one non-Done card has `status.key == "wip"`, AND (d) the active WIP card in `KANBAN.md` carries a link to `docs/spec-<NNN>-<topic>-<X_Y_Z>.md`.
- If the WIP card's body conflicts with something you read in Step 1, prefer the card and call out the conflict as an entry in the spec's `Risks and open questions` section — do not silently reconcile.
- Reading source files, existing specs, or test files during Step 6 is allowed and expected. The boundary is on **writes**, not reads.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[start]: ../../START.md

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
