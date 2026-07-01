# NEXT.md — New Spec Builder Agent Flow

You have been invoked to author a new spec file under `docs/` for the next-up Work-In-Progress card in this repository.

Spec files live at the root of `docs/` (e.g. `docs/spec-0XX-**-X_X_X.md`), NOT under `docs/SPECS/`. The older `docs/SPECS/spec-*.md` files are legacy / archived locations — read them from there for structural reference (Step 5), but new specs you create land in `docs/`.

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

Now (and only now) read `KANBAN.md`. The file is large — use `grep -n "^## " KANBAN.md` first to scan section headers, then read the `## In progress` column in full. You do not need to read the `## To Do`, `## Blocked`, or `## Done` columns *in full* to author the spec — but you DO need a lightweight scan of the `## To Do` and `## Done` card IDs for the target's patch version (see the joint-cut note below); that scan is card-ID/version-level, not a body read.

Locate the **lowest-NNN card under the `## In progress` board column** — that is, the card whose ID starts with `WIP-` and carries the smallest 3-digit sequence number among the WIP cards. That card is the spec target.

While you're on the board, also determine **which other non-Done cards (WIP *and* To-Do) share the target card's patch version** — a lightweight scan of card IDs and their trailing `-X.Y.Z` across the `## In progress` and `## To Do` columns (grep the board for the patch version; you don't need to read those cards' bodies). Checking only the WIP column is NOT enough: a card can be the sole WIP card yet still share its patch version with unstarted To-Do cards. The ownership rule: if **any other non-Done card** shares the target's patch version, the `pyproject.toml` / `__version__` / `tests/base/test_init.py` bump is owned by the **joint cut** (the last card of that patch line to land), so the target's spec defers it; if the target is the **only non-Done card** at its patch version, its Slice 5 owns the bump. Finally, glance at the `## Done` column for a same-patch card that already **deferred its cut to your target** — that confirms your spec is the one that completes the joint cut and thus owns the bump. Record what you find so [Step 6](#step-6--write-the-spec) can pin the right Decision.

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

The instinct to "trim CSV rows that don't have GLOSSARY headings" happens AFTER the over-zealous first pass, driven by the checker's output. Do NOT pre-emptively skip a term because you are unsure it has a glossary entry. Do NOT skip a term because you "already linked it inline" — the CSV is the audit ledger, not a duplicate of the spec body. Let the script tell you which rows to drop; do not pre-decide.

Then run the checker:

```
uv run python scripts/check_spec_glossary.py --spec docs/spec-<NNN>-<topic>-<X_Y_Z>.md
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

> **The most important part of this step is the cross-reference sweep — TO and FROM every moved spec.** A spec move is mechanically cheap (`git mv`) but link-fragile: when `docs/spec-XXX-…` becomes `docs/SPECS/spec-XXX-…`, three classes of link rot the instant the move lands and only one of them is obvious. **All three MUST be fixed in the same pass:**
>
> 1. **FROM other files → the moved spec** (links elsewhere that point AT the spec you just moved). The path target changes; every `](spec-XXX-…)` / `](docs/spec-XXX-…)` / `](../spec-XXX-…)` reference in every doc, in `KANBAN.md`, and in the new active spec gets rewritten so it still resolves.
> 2. **FROM the moved spec → everywhere else** (links INSIDE the moved spec body pointing at repo files). Every relative path inside the spec body just shifted one directory deeper — `](../KANBAN.md)` from `docs/spec-XXX-…` is correct, but from `docs/SPECS/spec-XXX-…` it must become `](../../KANBAN.md)`. The file's contents did not change but the file's location did, and every relative path inside it is now wrong by one `../` level. **This is the failure mode that gets missed** because the visible diff is just a rename — the broken links live inside the moved file's unchanged body.
> 3. **Between specs that BOTH moved in the same sweep** (links inside one archived spec that point at another archived spec). The two specs are now siblings under `docs/SPECS/`, so a link that was `](SPECS/spec-YYY-…)` becomes `](spec-YYY-…)`, and a link that was `](spec-YYY-…)` (sibling under `docs/`) is now also `](spec-YYY-…)` (sibling under `docs/SPECS/`) — same surface, different meaning. Verify every one.
>
> Bias toward over-grepping. Missing references rot silently and only surface when a future reader follows the link. False positives are cheap to dismiss; false negatives are invisible until they bite.

> **`KANBAN.md` is a GENERATED file — edit the database, not the file.** `KANBAN.md` is rendered from the `apps.kanban` Django app's database (in the fakeshop example project) by `scripts/build_kanban_md.py`; the committed `KANBAN.md` is an export, not a source. **Hand-edits to `KANBAN.md` decay** — they are silently overwritten the next time anyone re-renders the board. So the KANBAN parts of this sweep (actions 5 and 6 below) are made in the DB and then re-rendered, NOT by editing the file:
>
> - **Both the `## WIP / DONE spec map` table row AND a card's `Spec:` body line are rendered from the one `SpecDoc` model** (`apps/kanban/models.py::SpecDoc`: `card` one-to-one, unique `name`, `url`). `url` is a GitHub `…/blob/main/<repo-path>` URL; the renderer strips the `blob/main/` prefix to produce the in-repo link, so the path you want in `KANBAN.md` is whatever follows `blob/main/` in `SpecDoc.url`. There is no separate "spec map" data — one `SpecDoc` per card drives both surfaces.
> - **To repoint a moved spec's link** (action 5): update that card's `SpecDoc.url` to the new path, e.g. `…/blob/main/docs/SPECS/spec-<old_NNN>-…`.
> - **To add/fix the active card's spec reference** (action 6): `update_or_create` a `SpecDoc(card=<active card>, name="spec-<NNN>-<topic>-<X_Y_Z>", url="…/blob/main/docs/spec-<NNN>-<topic>-<X_Y_Z>.md")`. A card with no `SpecDoc` renders as `No dedicated spec`.
> - **Make the DB edits via the example project's shell**, then re-render:
>
>   ```
>   uv run python examples/fakeshop/manage.py shell -c "<ORM edit>"
>   uv run python scripts/build_kanban_md.py     # re-export KANBAN.md from the DB
>   ```
>
>   `build_kanban_md.py` rewrites the whole file from the DB, so confirm the resulting `git diff KANBAN.md` shows ONLY your intended spec-reference changes (a clean diff also proves the committed file was already in sync with the DB).
> - **Card-body prose that mentions a spec path inside a `CardItem.text` row** (e.g. a "Requires spec: `docs/spec-…`" line buried in a Done card's Scope/DoD prose) is historical card text, NOT a `SpecDoc`-driven link. Leave it — it is out of scope per the "no card-body content changes beyond the spec-reference line" boundary, and re-rendering will preserve it verbatim.

**Worked example (copy-paste, then fill the `<…>` blanks).** This is the entire KANBAN side of actions 5 + 6 — one shell call that (a) creates/updates the active card's `SpecDoc` and (b) repoints each archived spec's `SpecDoc` to `docs/SPECS/`, followed by the re-render and the clean-diff check. `Card.number` is the card's NNN (e.g. `30` for `WIP-ALPHA-030-0.0.9`). Run from the repo root:

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
git --no-pager diff KANBAN.md                       # expect ONLY the spec-reference changes
```

The modified `examples/fakeshop/db.sqlite3` is the durable artifact — `KANBAN.md` is just its export, so the committed DB is what carries the change forward. Leave both edited together for the maintainer to commit.

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
3. **Rewrite cross-references INSIDE each moved spec** (the "FROM the moved spec → everywhere else" direction — the failure mode most likely to be missed). When a spec at `docs/spec-<old_NNN>-…` becomes `docs/SPECS/spec-<old_NNN>-…`, every relative `](…)` target inside its body must be re-relativized one directory deeper. Enumerate every link with `grep -nE '\]\([^)]+\)' docs/SPECS/spec-<old_NNN>-…` and classify each match into one of these buckets:

   - **Repo-root files** (`KANBAN.md`, `README.md`, `GOAL.md`, `TODAY.md`, `AGENTS.md`, `CHANGELOG.md`, `pyproject.toml`, `BACKLOG.md`, …): `](../KANBAN.md)` → `](../../KANBAN.md)`, `](../README.md)` → `](../../README.md)`, etc.
   - **`docs/` siblings** (`GLOSSARY.md`, `TREE.md`, `README.md`, `feedback.md`, the new active spec, `NEXT.md` if linked): `](GLOSSARY.md)` → `](../GLOSSARY.md)`, `](README.md)` → `](../README.md)`, `](NEXT.md)` → `](../SPECS/NEXT.md)` *only if NEXT.md remains under `docs/SPECS/`* — verify location before rewriting.
   - **Specs that ALSO moved in the same sweep** — these are now `docs/SPECS/` siblings of the file being rewritten, so paths simplify: `](SPECS/spec-YYY-…)` → `](spec-YYY-…)`, and a former `](spec-YYY-…)` sibling-under-`docs/` reference stays `](spec-YYY-…)` (now a sibling under `docs/SPECS/`).
   - **Source / test / example files under repo root** (`django_strawberry_framework/...`, `tests/...`, `examples/...`, `scripts/...`, `.venv/...`): `](../django_strawberry_framework/foo.py)` → `](../../django_strawberry_framework/foo.py)`, etc.
   - **In-spec anchors** (`](#decision-N)`, `](#some-heading)`) and **absolute URLs** (`](https://…)`) — unchanged.
   - **Companion CSV** (the moved spec's own `*-terms.csv` — also moved): if the spec body links to it (`](spec-<old_NNN>-…-terms.csv)`), the link stays as-is (still a sibling).

   This is best done as a single deterministic transformation pass over the file (a short script that classifies every `](target)` against the rules above and rewrites accordingly) rather than ad-hoc edits, so no link is missed and no replacement-ordering hazard arises.
4. **Rewrite cross-references in the new spec** (the "FROM the active spec → moved spec" direction). Search the spec you just authored for markdown links that point at any moved spec — match patterns like `](spec-<old_NNN>-…)`, `](./spec-<old_NNN>-…)`, and `](docs/spec-<old_NNN>-…)`. Each match becomes the new path under `docs/SPECS/` (relative-path discipline: from a spec in `docs/`, the moved sibling is now at `SPECS/spec-<old_NNN>-…`).
5. **Rewrite cross-references in every other doc, INCLUDING `KANBAN.md`** (the "FROM the rest of the repo → moved spec" direction). Enumerate every doc that references the moved spec(s):

   ```
   grep -rln "spec-<old_NNN>-<old_topic>-<old_version>" docs/ README.md GOAL.md TODAY.md AGENTS.md KANBAN.md
   ```

   For each hit, rewrite the path so the link still resolves after the move. Relative-path discipline: from `docs/GLOSSARY.md` the moved file is `SPECS/spec-…`; from repo-root `README.md` / `GOAL.md` / `TODAY.md` / `AGENTS.md` it is `docs/SPECS/spec-…`; from another spec under `docs/` it is `SPECS/spec-…`. Apply each rewrite in place — **except `KANBAN.md`**: it is a generated export (see the callout above), so its spec-map row and card `Spec:` line for a moved spec are repointed by updating that card's `SpecDoc.url` in the DB (set the path after `blob/main/` to `docs/SPECS/spec-…`) and re-rendering with `uv run python scripts/build_kanban_md.py`. Do NOT hand-edit `KANBAN.md` — the edit would not survive the next render.
6. **Add or update the active WIP card's reference to the new spec.** The card you targeted in Step 3 should point at the spec file you just authored — a `SpecDoc` row whose `url` resolves to `docs/spec-<NNN>-<topic>-<X_Y_Z>.md`. Because `KANBAN.md` is a generated export (see the callout above), this is a **DB edit + re-render**, not a file edit. Query the card's current `SpecDoc` (via `apps/kanban/models.py::SpecDoc`) and handle three cases:

   - **No `SpecDoc` present** (the spec map renders `No dedicated spec`) — create one: `SpecDoc.objects.update_or_create(card=<active card>, defaults={"name": "spec-<NNN>-<topic>-<X_Y_Z>", "url": "https://github.com/<org>/<repo>/blob/main/docs/spec-<NNN>-<topic>-<X_Y_Z>.md"})`. The renderer surfaces it as both the spec-map row and a card-body `Spec:` line automatically.
   - **`SpecDoc` present but `url` points at a different path** (e.g. a stale `docs/SPECS/spec-…` from a prior archive cycle, or a now-renamed slug) — update `SpecDoc.url` (and `name` if the slug changed) to the active path.
   - **`SpecDoc.url` already correct** — no action.

   Make the edit via `uv run python examples/fakeshop/manage.py shell -c "<ORM edit>"`, then `uv run python scripts/build_kanban_md.py`, and confirm `git diff KANBAN.md` shows only the intended spec-reference change. The card's column is irrelevant — `SpecDoc` is keyed on the card, not its board column, so a card moved to `## Done` between Step 3 and Step 8 still resolves through the same `SpecDoc` and re-renders in its new column.
7. **`CHANGELOG.md` stays reserved.** `CHANGELOG.md` has its own maintainer-edited protocol and is NOT rewritten by this step even when it references a moved spec. If `grep` finds matches in `CHANGELOG.md`, surface them as a one-line report at the end of the flow ("`CHANGELOG.md` references moved spec(s) at lines …; maintainer must update") and STOP — do not silently edit.
8. **Verify every rewritten link resolves.** Before closing the step, spot-check a representative sample of the rewrites — pick 5–10 paths across the categories above (one repo-root link, one `docs/` sibling, one inter-archived-spec link, one source-file link) and confirm each target file exists at the path the rewritten link now claims. Broken links land silently; this is the only check that catches a category miss in the transformation pass.
9. **Re-run the checker** against the new spec one more time:

   ```
   uv run python scripts/check_spec_glossary.py --spec docs/spec-<NNN>-<topic>-<X_Y_Z>.md
   ```

   The archive pass may have shifted markdown link paths inside the new spec; the script's earlier exit-0 must still hold. If it now fails, fix the cross-reference rewrites until it exits 0 again.

This step is idempotent. A second pass with no other specs at `docs/` top-level and a `KANBAN.md` already pointing at the active spec is a clean no-op.

The flow is complete when Step 8 finishes: only the active spec and its CSV live at `docs/spec-*`, every prior spec is at `docs/SPECS/spec-*`, every cross-reference resolves (including in `KANBAN.md`), and the checker exits 0 against the active spec.

---

## Boundaries

- Do **not** modify `CHANGELOG.md` under any circumstance during this flow — even path-update edits triggered by Step 8 must be surfaced as a maintainer-report rather than silently applied.
- Do **not** modify `TODAY.md` except as a Step 8 path-update (rewriting a moved spec's path); content edits to `TODAY.md` outside that narrow purpose are out of scope.
- `KANBAN.md`'s card data IS in scope for Step 8 — repoint moved-spec links and add/fix the active WIP card's spec reference — but `KANBAN.md` is a **generated export**, so those changes are made in the `apps.kanban` DB (the `SpecDoc` rows) and re-rendered with `scripts/build_kanban_md.py`, NOT by hand-editing the file (see the Step 8 callout). The only `SpecDoc` edits in scope are spec-reference repoints/creates for the moved and active specs; no other DB changes (no column/status moves, no `CardItem.text` / card-body prose edits beyond what `SpecDoc` drives).
- Do **not** modify any file other than the new spec file, its companion `*-terms.csv`, the spec files being archived under Step 8, the cross-reference updates Step 8 prescribes in `docs/`, `README.md`, `GOAL.md`, `TODAY.md`, and `AGENTS.md`, and — for `KANBAN.md` — the regenerated file plus the `apps.kanban` `SpecDoc` rows it is rendered from.
- Do **not** commit.
- Do **not** run pytest, ruff, or any other tooling unless Step 7 or Step 8 prescribes it (the `scripts/check_spec_glossary.py` run including its `--auto-link` rewrite, the `git mv` / `grep` invocations Step 8 names, and — for the `KANBAN.md` spec-reference edits — the `examples/fakeshop/manage.py shell` ORM edit plus the `scripts/build_kanban_md.py` re-render are all part of the flow) or you need to settle a question inside the spec.
- The artifacts this flow produces: the new spec file, its companion `*-terms.csv`, the moves of every prior `spec-*.md` (and companion CSV) from `docs/` to `docs/SPECS/`, path-only cross-reference updates in every doc that pointed at a moved spec, and — for the active WIP card's spec reference and any moved-spec links in `KANBAN.md` — the `apps.kanban` `SpecDoc` rows plus the regenerated `KANBAN.md` they export to.
- The flow is not complete until (a) `scripts/check_spec_glossary.py` exits 0 against the new spec and its CSV, (b) Step 8 has run and no `spec-*.md` other than the active one remains at `docs/` top-level, AND (c) the active WIP card in `KANBAN.md` carries a link to `docs/spec-<NNN>-<topic>-<X_Y_Z>.md`.
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
