# Build: Slice 7 — correct the card-052 rationale-companion census this cycle falsified, and re-render the board

Spec reference: none. This slice implements the maintainer's post-final-gate fence amendment in
`docs/builder/build-031-globalid_encoding-0_0_9.md` `### Fence amendment (maintainer, post-final-gate)`
item 2 ("Kanban DB edits are authorized"), plan checklist line `- [ ] Slice 7`.
Build plan: `docs/builder/build-031-globalid_encoding-0_0_9.md`.
Status: final-accepted

Closed by **procedural closure** (`docs/builder/BUILD.md` `### Procedural-closure slices`): one Worker 1
pass, one combined Plan + Final-verification block, `Status: final-accepted` set directly. No Worker 2,
no Worker 3. The change is a single DB field plus the two renders that are the completion of that DB
edit (`docs/builder/BUILD.md` `### Generated docs are DB-backed: edit the DB, then regenerate`).

---

## Plan (Worker 1) + Final verification (Worker 1)

### Why this slice exists

Slice 0 of this cycle authored `docs/SPECS/appx/spec-031-globalid_encoding-0_0_9-rationale.md`, which
did not exist before. `TODO-ALPHA-052-0.0.16 - Alpha documentation-debt discharge` carries a `Scope`
bullet whose whole subject is a **measured census** of which shipped specs have a `-rationale.md`
companion. Creating `031`'s companion moved that census by one in five places. The board is rendered
from `examples/fakeshop/db.sqlite3`, so the fix is a DB edit followed by both renders.

### Fence

- **In fence:** `examples/fakeshop/db.sqlite3` (one field on one row), `KANBAN.md`, `KANBAN.html`, and
  this artifact.
- Nothing else was written. `docs/SPECS/spec-032-full_relay-0_0_9.md` (concurrent Slice 6),
  `docs/SPECS/spec-031-globalid_encoding-0_0_9.md` and its companion, every `.py` file,
  `docs/GLOSSARY.md`, `docs/TREE.md`, `CHANGELOG.md`, and the agentflow standing docs were not touched.
- No card renumber, no status change, no row added or deleted, no reset / re-migrate / re-seed /
  `git checkout` of the DB. Nothing staged, nothing committed, no branch.

### Working-tree baseline (re-read at the start of this pass)

`git status --short` at pass start — the four `M` / untracked spec-031 paths are this cycle's prior
slices, and none is in this slice's fence:

```text
 M django_strawberry_framework/types/definition.py
 M django_strawberry_framework/types/relay.py
 M docs/SPECS/spec-031-globalid_encoding-0_0_9.md
?? docs/SPECS/appx/spec-031-globalid_encoding-0_0_9-rationale.md
?? docs/builder/bld-031-final.md
?? docs/builder/bld-031-integration.md
?? docs/builder/bld-031-slice-0-rationale_extraction.md
?? docs/builder/bld-031-slice-1-meta_key_setting_precedence.md
?? docs/builder/bld-031-slice-2-encode_seam.md
?? docs/builder/bld-031-slice-3-decode_seam.md
?? docs/builder/bld-031-slice-4-live_http.md
?? docs/builder/bld-031-slice-5-docs_wrap.md
?? docs/builder/build-031-globalid_encoding-0_0_9.md
```

`examples/fakeshop/db.sqlite3`, `KANBAN.md`, and `KANBAN.html` were all **clean at pass start** — the
build plan's baseline-dirty list records the DB as concurrent-writable, but at this pass it matched
HEAD. Both renderers confirmed in sync with the DB before any edit:

```shell
uv run python scripts/build_kanban_md.py --check    # "KANBAN.md is up to date."   exit 0
uv run python scripts/build_kanban_html.py --check  # "KANBAN.html is up to date." exit 0
```

### The row

`apps.kanban.models.CardItem` **pk 1243** — `card.number` 52, section `Scope`, order 1. Read in full
before any change via the `scripts/_kanban_lib.configure_django()` bootstrap (which installs the SQLite
`busy_timeout` for concurrent writers).

---

## Re-derivation of every figure — measured, not accepted

Worker 0's handed leads were treated as leads. Every figure below was measured from the filesystem and
the board DB in this pass. Population instrument, run from the repository root:

```shell
uv run python - <<'PY'
from pathlib import Path
specs = sorted(p for p in Path("docs/SPECS").glob("spec-*.md"))
appx = Path("docs/SPECS/appx")
print("spec .md files in docs/SPECS:", len(specs))
no_rat  = [p.stem for p in specs if not (appx / f"{p.stem}-rationale.md").exists()]
no_terms= [p.stem for p in specs if not (appx / f"{p.stem}-terms.csv").exists()]
print("no rationale in appx:", len(no_rat), no_rat)
print("no terms.csv in appx:", len(no_terms), no_terms)
PY
```

Output:

```text
spec .md files in docs/SPECS: 56
no rationale in appx: 20
['spec-032', 'spec-033', 'spec-034', 'spec-035', 'spec-036', 'spec-037', 'spec-038', 'spec-039',
 'spec-040', 'spec-041', 'spec-042', 'spec-043', 'spec-049', 'spec-050', 'spec-051', 'spec-053',
 'spec-054', 'spec-055', 'spec-056', 'spec-064']
no terms.csv in appx: 2 ['spec-054-graph_substrate-0_1_1', 'spec-064-structural_templates-0_1_6']
```

Shipped-vs-unshipped is **not** inferred from the filename; it was read from the board, one query per
spec-numbered card, so the "49 shipped" population is measured rather than assumed:

```shell
uv run python - <<'PY'
import sys; sys.path.insert(0, "scripts")
from _kanban_lib import configure_django; configure_django()
from apps.kanban.models import Card
for n in [*range(1, 52), 53, 54, 55, 56, 64]:
    c = Card.objects.filter(number=n).first()
    print(n, getattr(c, "status", None))
PY
```

Result: cards **1-49 are all `Done`**; **50, 51, 53, 54, 55, 56, 64 are all `To Do`** (7 cards). No card
052 spec file exists (the 2026-08-25 insert renumber left no `spec-052-*.md`), which is why 56 spec
files span numbers 001-056 plus 064.

| Figure in the bullet | Handed lead | Re-derived | Match? | How measured |
|---|---|---|---|---|
| `docs/SPECS/` holds 56 spec files | unchanged (true) | **56** | yes | `len(list(Path("docs/SPECS").glob("spec-*.md")))`; `ls -1 docs/SPECS/*.md \| wc -l` gives 57 because `NEXT.md` is not a spec |
| carry no `-rationale.md` | 21 -> **20** | **20** | yes | population instrument above |
| carry no `-terms.csv` (spec-054, spec-064, both unshipped) | unchanged (true) | **2**, exactly those two, both `To Do` | yes | population instrument + board query |
| the shipped population | unchanged (true) | **49** (cards 1-49 all `Done`) | yes | board query above |
| shipped WITH a companion | 35 -> **36** | **36** = 49 - 13 | yes | 001-031 (31) + 044-048 (5) = 36, read off the `no_rat` complement |
| shipped WITHOUT a companion | 14 (`031`-`043` + `049`) -> 13 (`032`-`043` + `049`) | **13** = `spec-032`..`spec-043` (12) + `spec-049` | yes | first 13 entries of `no_rat`, each cross-checked `Done` |
| the have-side run | `001`-`030` -> `001`-`031` | **`spec-001` to `spec-031`**, contiguous, alongside `044`-`048` | yes | `no_rat` begins at `spec-032`, so 001-031 has no hole |
| the island | 14-spec -> **13-spec** | **13** | yes | same 13 as the without-companion row; it is the same population counted once |
| the island's leading edge | `031` -> **`032`** | **`spec-032`** | yes | lowest member of `no_rat` restricted to `Done` cards |
| remaining 7 gaps are unshipped | unchanged (true) | **7** = 050, 051, 053, 054, 055, 056, 064, all `To Do` | yes | 20 - 13 = 7, each confirmed `To Do` |
| residual cycles the "every shipped spec" answer commits to | 14 -> **13** | **13** | yes | identical to the without-companion count; the sentence's subject is that population |
| `spec-048`'s companion is 29,962 bytes (preserved historical passage) | unchanged (true) | **29962** | yes | `wc -c docs/SPECS/appx/spec-048-secure_output_defaults-0_0_14-rationale.md` |

**Every handed lead matched.** No lead was refuted, and no additional stale figure was found inside the
bullet.

One arithmetic cross-check the table does not make obvious, recorded because the bullet's numbers are a
partition and a partition is re-derivable: 56 total = 36 have + 20 have-not; 20 have-not = 13 shipped +
7 unshipped; 49 shipped = 36 have + 13 have-not. All three hold.

---

## The text change

Editorial convention followed: this bullet **deliberately keeps superseded readings visible** so a
rewrite is not re-reverted. The 2026-08-25 reading is therefore named and superseded rather than
silently overwritten, in the bullet's own voice, and the load-bearing analytical point is preserved —
the **shape** did not change (one long contiguous run, plus a second run, plus a bounded island); only
the boundary moved, by one, for exactly the reason the prior reading had already named ("extended card
by card").

### Before (`CardItem.objects.get(pk=1243).text`, 2,187 bytes)

```text
Decide whether a `-rationale.md` companion in `docs/SPECS/appx/` is owed by every shipped spec or only by one whose cycle produced it, and make the directory consistent either way. Re-measured 2026-08-25 after the spec-030 residual cycle authored `030`'s companion: `docs/SPECS/` holds 56 spec files, 21 carry no `-rationale.md`, and 2 carry no `-terms.csv` either (`spec-054-graph_substrate-0_1_1` and `spec-064-structural_templates-0_1_6`, both unshipped). Restricted to the population this decision actually governs - the 49 shipped specs - 35 have a companion and 14 do not (`spec-031` through `spec-043`, plus `spec-049`); the remaining 7 gaps are unshipped specs that have had no cycle, so they are not in the population. This supersedes the 2026-08-15 reading of 13-have / 36-do-not, and what changed is the SHAPE and not only the numbers: the have-side is no longer two small cohorts but one long run plus one, contiguous from `spec-001` to `spec-030` alongside `spec-044` through `spec-048`, because that first cohort has been extended card by card since. So the gap is no longer 'everything predating the practice' but a bounded 14-spec island between two runs - and closing `030`, the last hole inside the `001`-`029` run, is precisely what made `spec-031` its leading edge and made the island visible at all. This bullet previously read that `spec-048-secure_output_defaults-0_0_14.md` was the one file missing a companion where 044 through 047 all had one; that framing was wrong twice over, and both errors are worth keeping visible so the rewrite is not re-reverted. The named file acquired its companion (29,962 bytes), and the four-of-five reading mistook a cohort boundary for a defect - it pointed at the single spec sitting on the edge of the new-practice block and made what is now a 14-file policy question look like a one-file tidy-up. What actually turns on the decision is scheduling, not consistency: answering "every shipped spec" commits the board to 14 residual cycles of the kind spec-001 through spec-008 have been receiving, so the answer belongs beside this card's rationale-template and spec/rationale-checker items rather than in a documentation sweep.
```

### After (2,669 bytes)

```text
Decide whether a `-rationale.md` companion in `docs/SPECS/appx/` is owed by every shipped spec or only by one whose cycle produced it, and make the directory consistent either way. Re-measured 2026-08-26 after the spec-031 residual cycle authored `031`'s companion: `docs/SPECS/` holds 56 spec files, 20 carry no `-rationale.md`, and 2 carry no `-terms.csv` either (`spec-054-graph_substrate-0_1_1` and `spec-064-structural_templates-0_1_6`, both unshipped). Restricted to the population this decision actually governs - the 49 shipped specs - 36 have a companion and 13 do not (`spec-032` through `spec-043`, plus `spec-049`); the remaining 7 gaps are unshipped specs that have had no cycle, so they are not in the population. This supersedes the 2026-08-25 reading of 21-carry-none / 35-have / 14-do-not, which itself superseded the 2026-08-15 reading of 13-have / 36-do-not, and the two supersessions differ in kind. The 08-15 to 08-25 one changed the SHAPE and not only the numbers: the have-side stopped being two small cohorts and became one long run plus one, contiguous from `spec-001` to `spec-030` alongside `spec-044` through `spec-048`, because that first cohort has been extended card by card since. The 08-25 to 08-26 one changed only the BOUNDARY, and by exactly one - the run now reads `spec-001` to `spec-031` alongside `spec-044` through `spec-048` - and it moved for precisely the reason the prior reading had already named: the run is extended card by card, and `031` was the next card. So the gap is no longer 'everything predating the practice' but a bounded 13-spec island between two runs, whose leading edge each residual cycle pushes forward by one: closing `030` made `spec-031` the edge and made the island visible at all, and closing `031` has now made `spec-032` the edge. This bullet previously read that `spec-048-secure_output_defaults-0_0_14.md` was the one file missing a companion where 044 through 047 all had one; that framing was wrong twice over, and both errors are worth keeping visible so the rewrite is not re-reverted. The named file acquired its companion (29,962 bytes), and the four-of-five reading mistook a cohort boundary for a defect - it pointed at the single spec sitting on the edge of the new-practice block and made what is now a 13-file policy question look like a one-file tidy-up. What actually turns on the decision is scheduling, not consistency: answering "every shipped spec" commits the board to 13 residual cycles of the kind spec-001 through spec-008 have been receiving, so the answer belongs beside this card's rationale-template and spec/rationale-checker items rather than in a documentation sweep.
```

### What changed, clause by clause

| Clause | Before | After |
|---|---|---|
| re-measure provenance | `Re-measured 2026-08-25 after the spec-030 residual cycle authored 030's companion` | `Re-measured 2026-08-26 after the spec-031 residual cycle authored 031's companion` |
| carry-no-rationale count | `21` | `20` |
| shipped split | `35 have a companion and 14 do not (spec-031 through spec-043, plus spec-049)` | `36 have a companion and 13 do not (spec-032 through spec-043, plus spec-049)` |
| supersession record | one supersession (2026-08-15) | two, named in order, with the 08-25 figures quoted (`21-carry-none / 35-have / 14-do-not`) and the two supersessions distinguished as SHAPE vs BOUNDARY |
| the run | `contiguous from spec-001 to spec-030` (kept, now attributed to the 08-25 reading) | plus `the run now reads spec-001 to spec-031`, with the move attributed to the mechanism the bullet already named |
| the island | `a bounded 14-spec island` | `a bounded 13-spec island` |
| the leading edge | `closing 030 ... is precisely what made spec-031 its leading edge` | that clause preserved as history, plus `closing 031 has now made spec-032 the edge` |
| policy-question size (inside the preserved error record) | `a 14-file policy question` | `a 13-file policy question` |
| scheduling consequence | `commits the board to 14 residual cycles` | `commits the board to 13 residual cycles` |

Untouched by design, per the slice contract: the `56 spec files` figure, the `-terms.csv` sentence, `the
49 shipped specs`, `the remaining 7 gaps are unshipped specs`, the whole `This bullet previously read
that spec-048-...` passage (a deliberately preserved record of a past error, apart from the `14`->`13`
figure inside its last clause), and the closing "what actually turns on the decision is scheduling"
argument (apart from its `14`->`13`). Character-level confirmation: the four preserved sentences are
byte-identical between the before and after texts apart from the two digit substitutions named in the
table.

### How it was written

Via the ORM with a full `save()` (never raw SQL, never `.update()`), so any `post_save` side-row wiring
runs:

```shell
uv run python - <<'PY'
import sys; sys.path.insert(0, "scripts")
from _kanban_lib import configure_django; configure_django()
from apps.kanban.models import CardItem
ci = CardItem.objects.get(pk=1243)
ci.text = NEW_TEXT
ci.save()
PY
```

The text carries no `{{card_ref:N}}` placeholder before or after, so no `CardReference` row is created,
retargeted, or orphaned by the edit.

---

## DB text-column sweep

Obligation: find any **other** row this cycle falsified — the rationale-companion census, `spec-031`'s
companion status, or the leading-edge claim. Worker 0's sweep covered three columns; this pass swept
**every** `TextField` / `CharField` on **every** model in the `kanban` app, enumerated from Django's own
model registry rather than from a hand-written list:

```shell
uv run python - <<'PY'
import re, sys; sys.path.insert(0, "scripts")
from _kanban_lib import configure_django; configure_django()
from django.apps import apps as dj_apps
from django.db import models as m
rx = re.compile(r"rationale|companion|spec-03[0-3]|leading edge|island|-terms\.csv|56 spec|"
                r"\b21 carry|\b35 have|\b14 do not|13-have|36-do-not|residual cycle|appx|shipped spec",
                re.IGNORECASE)
for model in dj_apps.get_app_config("kanban").get_models():
    fields = [f for f in model._meta.get_fields()
              if isinstance(f, (m.TextField, m.CharField)) and not f.auto_created]
    for obj in model.objects.all():
        for f in fields:
            if rx.search(getattr(obj, f.name) or ""):
                print(model.__name__, f.name, obj.pk)
PY
```

**53 columns swept, across 27 models.** The full enumeration:

`Milestone.key`, `Milestone.label`, `Milestone.version_floor`, `Milestone.version_ceiling`,
`Status.key`, `Status.label`, `Priority.key`, `Priority.label`, `RelativeSize.key`,
`RelativeSize.label`, `RelativeSize.description`, `Upstream.key`, `Upstream.label`, `Upstream.emoji`,
`ParityLevel.key`, `ParityLevel.label`, `Section.key`, `Section.label`, `CardReferenceKind.key`,
`CardReferenceKind.label`, `BoardDocKind.key`, `BoardDocKind.label`, `AttemptOutcome.key`,
`AttemptOutcome.label`, `VerificationKind.key`, `VerificationKind.label`, `Actor.key`, `Actor.label`,
`Actor.kind`, `TargetVersion.number`, `SpecDoc.name`, `SpecDoc.path`, `TrackedPath.path`,
`TrackedPath.state`, `Card.title`, `Card.planning_note`, `CardReference.raw_text`,
`CardGlossaryTerm.raw_text`, `CardPathLink.kind`, `CardItem.text`, `Label.key`, `Label.color`,
`CardTransition.note`, `WorkAttempt.summary`, `WorkAttempt.evidence`, `Decision.question`,
`Decision.choice`, `Decision.rationale`, `BoardDoc.namespace`, `BoardDoc.key`, `BoardDoc.title`,
`BoardDoc.body`, `BoardDocCardReference.raw_text`.

This is a strict superset of Worker 0's three columns and covers every column the handed prompt named as
worth enumerating (`Decision.*`, `BoardDoc.body`, `WorkAttempt.*`) plus 47 more. Nothing on
`apps/kanban/models.py` carries text outside this set — every other field is a FK, an integer, a
boolean, a date, or a UUID.

**Result: Worker 0's finding is CONFIRMED. pk 1243 is the only row this cycle falsified.**

The vocabulary sweep returned 88 raw hits; every one was read. The dispositions that are not obvious
noise (a `SpecDoc.path` naming `spec-031`, a card body using the word "companion" for something else):

- `CardItem` **pk 1278** (card 52, `Scope` order 11) — "measured 2026-08-14, 8 of the 13 files in
  `docs/SPECS/appx/` carry all three of ...". This is a census over rationale companions and it **is**
  stale, but **not falsified by this cycle**: it carries its own measurement date, and by that date's
  own arithmetic (pk 1243 records a 2026-08-15 reading of 13-have) it was already 22 companions behind
  before this cycle started. Its subject is the *template shape* question, and the sub-populations it
  names — "the companions to `spec-001` through `spec-008`" and "the five `0.0.14` companions" — are
  named sets this cycle did not touch. Out of this slice's fence and out of its mandate (a row this
  cycle falsified); **recorded, not edited**. Flagged below for the maintainer.
- `CardItem` **pk 1347** (card 52, `Scope` order 26) — "**zero** files under `docs/SPECS/spec-*.md`
  carry [the boilerplate preamble]". A rationale MOVE is exactly the mechanism this bullet credits with
  the discharge, and a move can only remove text from a spec. Control re-run this pass:
  `grep -rl "expand it into the full builder-format spec" docs/SPECS/*.md | wc -l` -> **0**. Still true;
  and its "the surviving occurrences legitimately live in those companions" framing already accommodates
  a new companion. **No edit owed.**
- `CardItem` **pk 1351** (card 52, `Scope` order 28) — sizes a deferral sweep at "56 archived specs".
  Still 56 (measured above); the rationale move added no spec file. **No edit owed.**
- `CardItem` **pk 1393** (card 52, `Files likely touched`) — names `docs/SPECS/*.md` and
  `docs/SPECS/appx/*` as the cohort; carries no count. **No edit owed.**

---

## Re-render verification

`KANBAN.html`'s generator contract was read before running it rather than assumed: its module docstring
says it builds the page "from the fakeshop GraphQL endpoint" and `DATA_BLOCK_RE` in
`scripts/build_kanban_html.py` matches `<!-- KANBAN_DATA_START -->...<!-- KANBAN_DATA_END -->` — the
generator rewrites **only** that embedded data block, leaving the hand-maintained Vue shell alone. That
matches the repo's standing note; confirmed from source, not from memory.

```shell
uv run python scripts/build_kanban_md.py
# Wrote 70 cards (excluded 1 backlog cards) and 15 board docs to .../KANBAN.md      exit 0
uv run python scripts/build_kanban_html.py
# Wrote 71 cards, 15 board docs, and 11 lookup arrays to .../KANBAN.html            exit 0

uv run python scripts/build_kanban_md.py --check
# /Users/.../KANBAN.md is up to date.        exit 0
uv run python scripts/build_kanban_html.py --check
# /Users/.../KANBAN.html is up to date.      exit 0
```

Both `--check` runs **exit 0**.

The rendered diff is the one bullet and nothing else:

```shell
git diff --stat -- KANBAN.md KANBAN.html
#  KANBAN.html | 2 +-
#  KANBAN.md   | 2 +-
```

`KANBAN.md`'s single changed line is card 52's `#### Scope` bullet 2; `KANBAN.html`'s single changed
line is the embedded JSON data block (one line by construction).

### DB semantic diff, not byte churn

`docs/builder/BUILD.md` `### Tracked binary / generated files` forbids treating a binary's size or byte
diff as evidence. The DB was clean at pass start, so a HEAD comparison is exact. Read-only HEAD copy
into a scratch path **outside** the repo (never `git stash` / `git checkout`):

```shell
git show HEAD:examples/fakeshop/db.sqlite3 > <scratch>/db-head.sqlite3
# sqlite3 iterdump() of each, then:
diff <scratch>/dump-head.sql <scratch>/dump-work.sql
```

Output — exactly one changed line in the whole dump:

```text
6137c6137
< INSERT INTO "kanban_carditem" VALUES(1243,'2026-08-05 19:48:14.839853','2026-08-25 20:20:24.049589','Decide whether ...
---
> INSERT INTO "kanban_carditem" VALUES(1243,'2026-08-05 19:48:14.839853','2026-08-27 00:33:40.019286','Decide whether ...
```

One row, one text column plus its `modified` timestamp. No row added, deleted, renumbered, or
re-statused; no side row created; no other table touched. This is the mechanical proof that "change only
row pk 1243" held.

---

## Final status

`git status --short` after the pass:

```text
 M KANBAN.html
 M KANBAN.md
 M django_strawberry_framework/types/definition.py
 M django_strawberry_framework/types/relay.py
 M docs/SPECS/spec-031-globalid_encoding-0_0_9.md
 M docs/SPECS/spec-032-full_relay-0_0_9.md
 M examples/fakeshop/db.sqlite3
?? docs/SPECS/appx/spec-031-globalid_encoding-0_0_9-rationale.md
?? docs/builder/bld-031-final.md
?? docs/builder/bld-031-integration.md
?? docs/builder/bld-031-slice-0-rationale_extraction.md
?? docs/builder/bld-031-slice-1-meta_key_setting_precedence.md
?? docs/builder/bld-031-slice-2-encode_seam.md
?? docs/builder/bld-031-slice-3-decode_seam.md
?? docs/builder/bld-031-slice-4-live_http.md
?? docs/builder/bld-031-slice-5-docs_wrap.md
?? docs/builder/bld-031-slice-7-card_052_companion_census.md
?? docs/builder/build-031-globalid_encoding-0_0_9.md
```

Paths this slice dirtied: `examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, and this artifact.
The remaining entries are this cycle's earlier slices, present and unchanged since pass start, with one
exception that appeared **during** this pass and is not this slice's:
`docs/SPECS/spec-032-full_relay-0_0_9.md` went `M` mid-pass — that is the concurrent Slice 6, which owns
that file. It was clean in this pass's opening baseline and was never opened here. Nothing staged,
nothing committed, no branch created or switched.

### Not fixable inside the fence

- `CardItem` pk 1278 (card 52, `Scope` order 11) states "8 of the 13 files in `docs/SPECS/appx/`",
  measured 2026-08-14. There are now 36 rationale companions in `docs/SPECS/appx/`. The staleness
  predates this cycle by roughly 22 companions and the bullet carries its own measurement date, so it is
  neither this cycle's damage nor within "change only row pk 1243 unless the sweep finds another
  **falsified-by-this-cycle** row". Left untouched; the maintainer may want it re-measured by whichever
  pass next owns card 52's rationale-template bullet — and re-measuring it means re-running the
  three-section shape check across all 36 companions, not just re-counting files.

### Summary

Corrected the rationale-companion census in `CardItem` pk 1243 (card 52, `Scope` bullet 1) that this
cycle falsified by authoring `spec-031`'s rationale companion: 21 -> 20 carry none, 35/14 -> 36/13 on
the 49-shipped population, the island 14 -> 13 specs, the have-side run extended to `spec-031`, the
leading edge moved to `spec-032`, and the scheduling consequence 14 -> 13 residual cycles. The
2026-08-25 reading is recorded as superseded with its figures named, in the bullet's existing voice, and
the shape argument is preserved and extended rather than replaced. Every figure was re-derived from the
filesystem and the board DB in this pass; all matched the handed leads. A 53-column sweep across all 27
kanban models confirms pk 1243 was the only row this cycle falsified. Both renderers regenerated and
`--check` exit 0.

### Spec changes made (Worker 1 only)

None. This slice edits no spec file. `docs/SPECS/spec-031-globalid_encoding-0_0_9.md` and its rationale
companion were read-only for this pass, and `docs/SPECS/spec-032-full_relay-0_0_9.md` is owned by the
concurrent Slice 6.

<!-- LINK DEFINITIONS -->

<!-- Root -->

[kanban]: ../../KANBAN.md
[kanban-html]: ../../KANBAN.html

<!-- docs/ -->

<!-- docs/SPECS/ -->

[spec-031]: ../SPECS/spec-031-globalid_encoding-0_0_9.md

<!-- docs/builder/ -->

[build-031]: build-031-globalid_encoding-0_0_9.md
[build-md]: BUILD.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

[fakeshop-db]: ../../examples/fakeshop/db.sqlite3

<!-- scripts/ -->

[build-kanban-html]: ../../scripts/build_kanban_html.py
[build-kanban-md]: ../../scripts/build_kanban_md.py

<!-- .venv/ -->

<!-- External -->
