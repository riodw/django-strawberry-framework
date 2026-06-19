# Build: Slice 4 — docs + the 0.0.11 version cut + card wrap

Spec reference: `docs/spec-037-upload_file_image_mapping-0_0_11.md` (lines 388-421, the Slice 4 block of `## Slice checklist`; governed by the `## Doc updates` section lines 1468-1520 and Decision 10 lines 1275-1306)
Status: final-accepted

## Plan (Worker 1)

This is the final in-spec slice: it ships **no package logic** — only standing-doc
edits, the `0.0.11` version quintet, and the DB-backed kanban card close. Three
behaviors already shipped in Slices 1–3 (read output objects, write `Upload`
input, three root exports); Slice 4 makes the docs and the package version tell
that story, and moves `TODO-ALPHA-037-0.0.11` to `DONE-037-0.0.11`.

**Maintainer authorization recorded (read by Worker 2 and Worker 3):** the
maintainer's Slice 4 dispatch **explicitly authorized the `CHANGELOG.md` edit**.
This satisfies the `AGENTS.md` #"Do not update CHANGELOG.md unless explicitly
instructed" gate and the spec's Slice 4 requirement (spec lines 58-60, 1470-1476,
1514-1516) that the per-card `CHANGELOG.md` edit be named explicitly in the
Slice 4 maintainer prompt. The `0.0.11` CHANGELOG entry is therefore an in-scope
Slice 4 deliverable, not a gated/deferred one. Worker 3's `### CHANGELOG sanity`
check applies in full.

**Slice NOT split — single coherent slice, strictly ordered.** I assessed
splitting into `4a` (prose + version quintet) / `4b` (DB card-close) per BUILD.md
"Slice splitting". I am **not** splitting it. The DB body-sync step (step F1
below) reads its `GlossaryTerm.body` content **from the just-edited committed
`docs/GLOSSARY.md`** (worker-0.md procedure step 1 / step 1's "reconcile any
existing term whose body the build hand-edited"), so the prose-GLOSSARY edit and
the DB edit are tightly data-coupled — the DB sync is meaningless until the
GLOSSARY prose is final, and splitting would leave an awkward intermediate state
where the committed GLOSSARY claims `shipped (0.0.11)` while the DB still renders
`planned`. The doc-prose and DB-close halves are also reviewed against the same
spec section (`## Doc updates`). The slice is large but its steps are mechanical
and independently verifiable; the byte-clean-regenerate verification (step G) is
the single integration gate. Keeping it one slice preserves a single reviewable
"the `0.0.11` story is now consistent everywhere" diff. If Worker 2 finds the DB
card-close genuinely cannot land in the same pass (e.g. an unforeseen signal-model
blocker), it should surface that under `### Notes for Worker 1 (spec
reconciliation)` and Worker 1 will split at that point — but the plan is one slice.

### Ground truth established at planning (read-only DB + baseline regenerate)

I ran the worker-0.md "baseline regenerate-to-temp diff BEFORE any DB edit" and
read-only ORM inspections. The findings below are load-bearing for the plan —
Worker 2 must not be surprised by them:

- **Card 037 is `status=todo`, NOT `wip`.** `Card.objects.get(number=37)` has
  `status.key == "todo"`, no `SpecDoc`, zero `glossary_links`. The spec/dispatch
  framing "`WIP-…` → `DONE`" is loose; the actual move is `todo → done`. The
  rendered id flips to `DONE-037-0.0.11` automatically on the done-save (done
  cards drop the milestone prefix). Status keys available: `backlog`, `todo`,
  `wip`, `done`.
- **All three new glossary terms ALREADY exist as `GlossaryTerm` rows**, each with
  `status.key == "planned"`: `upload-scalar` (entry_order=78, index_order=74),
  `djangofiletype` (17/13), `djangoimagetype` (20/16). **No net-new term seeding
  is required** (worker-0.md procedure step 1's "seed any net-new term" is a
  no-op here). What IS required: flip each from `planned` → `shipped` (FK to
  `GlossaryStatus.objects.get(key="shipped")`) AND sync each `.body` to the
  rewritten committed `docs/GLOSSARY.md` entry (step F1), because step E rewrites
  those three bodies. `GlossaryStatus` has exactly two keys: `shipped`, `planned`.
- **Every term in the spec's `-terms.csv` already exists as a `GlossaryTerm`**
  (`check_spec_glossary.py --spec …` reports `OK: 20 terms`; I confirmed
  `scalar-field-conversion`, `specialized-scalar-conversions`, `strawberry_config`,
  `filterset`, `djangotype` all present). So `import_spec_terms` (step F2) will
  not hit the "anchor missing from `GlossaryTerm`" failure.
- **PRE-EXISTING DB DRIFT CLUSTER #1 — `036` SpecDoc.url is stale (non-`SPECS`).**
  The committed `KANBAN.md` (lines 100, 1339) renders the `036` spec link as
  `docs/SPECS/spec-036-mutations-0_0_11.md` — which is **correct** (spec-035 and
  spec-036 are already archived in `docs/SPECS/` on disk; I verified
  `docs/SPECS/spec-036-mutations-0_0_11.md` EXISTS and `docs/spec-036-…` does
  NOT). But the **DB** `SpecDoc` for card 36 stores
  `url=…/blob/main/docs/spec-036-mutations-0_0_11.md` (NON-`SPECS`). So the
  baseline regenerate-to-temp diff (run before any edit) **already** rewrites
  KANBAN lines 100/1339 from the correct `docs/SPECS/spec-036` to the broken
  `docs/spec-036` path. **This means Slice 4's mandatory KANBAN regenerate (step F3)
  will introduce two broken `036` spec links unless the DB is reconciled first.**
  See `### Implementation steps` step C for the resolution (reconcile the `036`
  SpecDoc.url to the `docs/SPECS/` path in the same DB pass — it is the durable
  fix, not a partial one, because the on-disk reality and the committed KANBAN
  both already use `docs/SPECS/`; only the DB lags).
- **PRE-EXISTING DB DRIFT CLUSTER #2 — `djangomodelpermission` body lags the
  committed file.** The committed `docs/GLOSSARY.md` `DjangoModelPermission`
  entry carries an extra trailing paragraph (the `check_permission` sync
  requirement, the empty-`Meta.permission_classes = []` AllowAny opt-out, the
  `SyncMisuseError`-on-async-hook detail) that the **DB body lacks**. The baseline
  regenerate-to-temp diff already strips that paragraph from the committed file.
  This is a `036`-era hand-edit-to-committed-GLOSSARY that was never synced to the
  DB. **Step F1 must reconcile this existing body too** (worker-0.md procedure
  step 1 "Also reconcile any existing term whose body the build hand-edited in the
  committed `docs/GLOSSARY.md` but not in the DB"), or step G's
  `git diff docs/GLOSSARY.md` cannot be clean.
- **PRE-EXISTING STALE-REF CLUSTER #3 — `034` and `028` in the 037 card body.**
  The 037 `CardItem` rows carry stale references the spec's Risks section already
  flagged: the **Definition of done** item order=1 says "Mutation input-type
  generation (`TODO-ALPHA-034-0.0.11`)" and the **Other** section says "pairs with
  `TODO-ALPHA-034-0.0.11`" and "Pairs with 028". The mutations card is `036` (not
  `034` = permissions); `028` = ordering subsystem (unrelated). The spec
  (Risks, lines 1593-1599 and 1606-1612) carries the "Pairs with 028" and the
  `scalars.py` `035` items as conflicts with preferred readings, NOT silent
  reconciliations. See step D for the disposition (fix the card-body `034`→`036`
  / "Pairs with 028"→"pairs with 036" because the spec authorizes fixing card-body
  content the wrap names AND these are single-surface `CardItem.text` values with
  no un-editable mirror; record as a deferred-catalog note for the integration
  pass either way).
- **Baseline regenerate-to-temp diff content (the file-only staged anchors that
  auto-clear, separated from real DB drift):** regenerating from the *current* DB
  changes `KANBAN.md` (5 lines) and `docs/GLOSSARY.md` (16 lines). The GLOSSARY
  16-line delta is: the `<!-- TODO(spec-037 Slice 4) -->` HTML-comment block
  (file-only staged anchor — auto-clears, expected, fine) PLUS the
  `DjangoModelPermission` body paragraph (real DB drift, cluster #2). The KANBAN
  5-line delta is: the two `036` spec-path reversions (cluster #1) and the
  removal of the 037 card's `- Spec:` line (file-only — the DB has no `037`
  SpecDoc yet, which step B fixes). This baseline is the reference for step G:
  after Slice 4's DB edits, the `git diff docs/GLOSSARY.md` must be clean *given
  the step-E prose edits land in the DB too*; the only "expected" auto-clear is
  the staged HTML-comment anchor.

### DRY analysis

- **Existing patterns reused.**
  - **The version quintet is the established multi-file version-cut shape.** Five
    coordinated sites carry the SAME `0.0.11` literal, exactly as prior cuts did
    (the `0.0.8` cut moved `__init__.py` `__version__`, `pyproject.toml`,
    `test_init.py::test_version`, and the GLOSSARY version line together — see
    `CHANGELOG.md` `[0.0.8]` "`django_strawberry_framework.__version__` is now
    `0.0.8`"). The five sites, each carrying a pre-placed `TODO(spec-037 Slice 4)`
    anchor naming the others: `pyproject.toml:4-6`, `__init__.py:36-38`,
    `tests/base/test_init.py:3-4,22`, `docs/GLOSSARY.md:20-34` (version line +
    staged HTML-comment), `uv.lock:218-220`. **One canonical literal: `0.0.11`** —
    DRY rule (a): every site uses the identical string; Worker 2 must not invent a
    divergent form (`0.0.11.dev`, `v0.0.11`, etc.).
  - **The GLOSSARY status flip is the established `planned for X.Y.Z` →
    `shipped (X.Y.Z)` shape.** Every prior card promoted its entries this way
    (e.g. `DjangoMutation` reads `**Status:** shipped (\`0.0.11\`).` today). The
    three 037 entries (`Upload` scalar, `DjangoFileType`, `DjangoImageType`) flip
    `**Status:** planned for \`0.0.11\`.` → `**Status:** shipped (\`0.0.11\`).` —
    same literal shape as the already-shipped `DjangoMutation` /
    `DjangoModelPermission` / `Input type generation` siblings on `0.0.11`. The
    Index-table rows flip `planned for \`0.0.11\`` → `shipped (\`0.0.11\`)`
    identically.
  - **The "breaking wire-format change" precedent text is reusable verbatim.**
    `Scalar field conversion` already documents `PositiveBigIntegerField switched
    from \`int\` to \`BigInt\` in \`0.0.6\` — breaking wire-format change`, and
    `TODAY.md` line 105 + the `0.0.9` model-anchored-`GlobalID` precedent use the
    same "breaking wire-format change … acceptable pre-`1.0.0`" framing. The new
    `Specialized scalar conversions` file/image row and the GLOSSARY breaking-change
    note reuse that exact phrasing (Slice 1 final-verification and the spec lines
    932-941 both anchor the file/image read break to the
    `PositiveBigIntegerField → BigInt` precedent). DRY: do not coin new
    breaking-change vocabulary; mirror the `BigInt` row.
  - **The DB-backed card-close procedure is fully specified** in
    `docs/builder/worker-0.md` "Closing out a kanban card (DB-backed …)" steps
    1-8, including the `manage.py shell` ORM-only rule (never raw SQL — the
    `post_save` `UUIDModel` side-row is required), the `import_spec_terms`
    full-set sync, the three `scripts/build_*.py` regenerate, and the
    byte-clean-regenerate verification. Step B-G below mirror that procedure
    one-for-one; no new close mechanism is invented.
  - **The READMEs already carry the "shipped" mutation bullets** (`README.md`
    line 57 "Mutations ship today too", `docs/README.md` line 131 "mutations +
    auto-generated `Input` types (new in `0.0.11`)"). Slice 4 only MOVES the
    `Upload`/file-image item from the "Coming next" list into the shipped list and
    bumps the Status/`Shipped today` version label — it reuses the existing
    sentence shape, not a new section.

- **New helpers justified.** **None.** This is a docs + version + DB-edit slice
  with zero new source symbols, zero new test helpers, zero new modules. The
  canonical-phrasing one-source-of-truth is the prose itself (see the canonical
  wordings pinned in `### Implementation steps`), not a code helper.

- **Duplication risk avoided.**
  - **Divergent `0.0.11` phrasings across pyproject / `__init__` / test /
    GLOSSARY / CHANGELOG.** Risk: five+ sites each spelling the version or the
    "shipped" wording slightly differently. Avoided by pinning ONE canonical
    literal (`0.0.11`) and ONE canonical "shipped" sentence shape per surface, and
    by reusing the existing `0.0.8`-cut and `DjangoMutation`-promotion shapes
    rather than inventing new ones. The plan flags (below) every place the spec's
    described wording already exists verbatim so Worker 2 copies it
    character-for-character.
  - **Hand-editing the generated `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md`
    instead of editing the DB.** Risk: the highest-frequency mistake for this
    slice — these three files are GENERATED (worker-0.md, BUILD.md "Generated docs
    are DB-backed"). A hand-edit is silently reverted by the next regenerate.
    Avoided: step E edits the **prose** `docs/GLOSSARY.md` body sections by hand
    (those are the *source-of-truth* the DB syncs FROM, per procedure step 1), but
    the **version line, status flips, Public-exports list, Index rows, Browse-by-
    category row, and Specialized-scalar row** are all DB-backed and land via the
    ORM (step F) then regenerate (step F3) — and step G proves the committed file
    regenerates byte-identically. The plan is explicit per-edit about which path
    (hand-edit-prose-body vs DB-field) each GLOSSARY change takes (see step E/F
    split). `README.md` / `docs/README.md` / `GOAL.md` / `TODAY.md` /
    `CHANGELOG.md` are NOT generated — those are hand-edited directly.
  - **Two copies of the breaking-wire-format note drifting.** Risk: the GLOSSARY
    `Specialized scalar conversions` row, the GLOSSARY `DjangoFileType` body, and
    `TODAY.md` each describing the read break differently. Avoided: anchor all
    three to the same `PositiveBigIntegerField → BigInt` `0.0.6` precedent phrasing
    already in the file, and keep the canonical sentence (pinned below) consistent.
  - **Re-deriving the term bodies for the DB sync instead of copying the committed
    file.** Risk: step F1 paraphrasing the GLOSSARY body when setting
    `GlossaryTerm.body`. Avoided: procedure step 1 is explicit — `body` = the text
    between the `**Status:** …` line and the next `## ` heading of the COMMITTED
    file, stripped. Worker 2 copies, does not paraphrase, so the regenerate is
    byte-identical (step G).

### Canonical phrasings (pin once — copy character-for-character)

These are the DRY single-source wordings. Where the spec's described text already
exists verbatim in the repo, the source site is named so Worker 2 copies it, not
re-authors it.

- **Version literal:** `0.0.11` (bare, no prefix). Five sites (step A).
- **GLOSSARY status flip:** exact replacement `**Status:** planned for \`0.0.11\`.`
  → `**Status:** shipped (\`0.0.11\`).` — matches the already-shipped
  `DjangoMutation` entry's status line verbatim (GLOSSARY `## DjangoMutation`).
- **GLOSSARY version line (line 20):** replace `Current package version:
  \`0.0.10\`.` → `Current package version: \`0.0.11\`.` (rest of the sentence
  unchanged). DB-backed via the kanban/glossary render — confirm whether this line
  is rendered from a DB field or is static prose at the top of the generated file
  (see step E note: the version line sits ABOVE `## Public exports`, in the
  generated header; Worker 2 must verify whether `build_glossary_md.py` emits it
  from a DB value or a literal — if literal-in-script, the version bump is a
  one-line edit to `scripts/build_glossary_md.py`, NOT a hand-edit of the rendered
  file; if DB-sourced, edit the DB field. RESOLVE at build time — see step E1).
- **Breaking-wire-format precedent phrasing (reuse verbatim shape):**
  `PositiveBigIntegerField switched from \`int\` to \`BigInt\` in \`0.0.6\` —
  breaking wire-format change` (GLOSSARY `Scalar field conversion`,
  `TODAY.md:105`). The file/image read break mirrors this: "file/image read
  output changed from `str` to `DjangoFileType` / `DjangoImageType` in `0.0.11` —
  breaking wire-format change", with the consumer-annotation override
  (`attachment: str`) as the documented opt-out.
- **The read=object / filter-input=str / mutation-input=Upload split sentence**
  (the spec's core "three-way split", spec lines 159-170, 1488-1502): the
  canonical statement is "On **read**, a `FileField` / `ImageField` column
  converts to a structured `DjangoFileType` / `DjangoImageType` output object (via
  the new `FIELD_OUTPUT_TYPE_MAP`); the **filter / scalar-input** value stays
  `str` (the `SCALAR_MAP` rows are unchanged); the **mutation input** is the
  `Upload` scalar." Use this one phrasing in the GLOSSARY `Scalar field
  conversion` file/image line, and reference it (not re-spell it) elsewhere.
- **README "shipped scalar + generated mutation-field typing, NOT multipart HTTP
  ergonomics" caveat** (spec lines 1503-1508, 1716-1718): the canonical caveat is
  "the `Upload` scalar and generated file/image mutation-input field typing ship
  in `0.0.11`; full multipart HTTP upload ergonomics await the `0.0.14`
  `TestClient` card." Worker 2 must include this caveat wherever it moves the
  `Upload` item to "shipped" (README + docs/README) so no reader infers a working
  multipart test client.
- **CHANGELOG version line:** `## [0.0.11] - <DATE>` — the date is the
  maintainer's commit date; Worker 2 uses today's date (`2026-06-19`) as the
  placeholder, matching the prior `## [0.0.9] - 2026-06-13` shape, and notes that
  the maintainer may adjust it at commit. The version in the `[0.0.11]` heading
  MUST equal `pyproject`/`__init__` `0.0.11` (Worker 3 `### CHANGELOG sanity`
  pins this).

### Implementation steps

Line numbers are pin-at-write-time navigational hints; verify against current
source before editing (a prior pass may have shifted the file). Steps are
**strictly ordered**: A (version quintet) and B-G (docs + DB close) can interleave,
but **step E (prose GLOSSARY body edits) MUST precede step F1 (DB body sync)**, and
**step F (all DB edits) MUST precede step F3/G (regenerate + verify)**. Do the
non-generated hand-edited docs (steps A, D-prose-only-where-applicable, H README,
I GOAL, J TODAY, K CHANGELOG) first, then the DB pass (B, C, D-DB, F), then
regenerate (F3) and verify (G).

#### Step A — Version quintet → `0.0.11` (Decision 10, spec lines 1275-1306, 391-396)

Move all five sites to the single literal `0.0.11`, and clear/trim the four
pre-placed `TODO(spec-037 Slice 4)` anchors:

1. `pyproject.toml:6` — `version = "0.0.10"` → `version = "0.0.11"`. Remove the
   `# TODO(spec-037 Slice 4): …` anchor at `pyproject.toml:4-5`. **Do NOT touch
   the Pillow dev dependency** (`pyproject.toml:45` `"pillow>=10.0.0"` — added in
   Slice 1, must stay) or any other `[dependency-groups] dev` line.
2. `django_strawberry_framework/__init__.py:38` — `__version__ = "0.0.10"` →
   `__version__ = "0.0.11"`. Remove the `# TODO(spec-037 Slice 4): bump
   __version__ …` anchor at `__init__.py:36-37`. **Do NOT touch the import block
   or `__all__`** (Slice 3 already landed the three exports — re-confirm
   `DjangoFileType`/`DjangoImageType`/`Upload` are present in `__all__` and
   unchanged).
3. `tests/base/test_init.py:22` — `assert __version__ == "0.0.10"` →
   `assert __version__ == "0.0.11"`. Remove the file-top `# TODO(spec-037 Slice
   4): update test_version …` anchor at `test_init.py:3-4`. **This is the ONLY
   test change in the entire slice** (spec: no new behavior tests — the behavior
   shipped in Slices 1-3). Do NOT add, remove, or modify any other test.
4. `uv.lock:220` — the `django-strawberry-framework` package entry `version =
   "0.0.10"` → `version = "0.0.11"`. Remove the `# TODO(spec-037 Slice 4):
   regenerate this lock entry …` anchor at `uv.lock:218-219`. **Preferred
   mechanism: run `uv lock` from the repo root** so the lock regenerates
   consistently from the bumped `pyproject.toml` (do step A1 first); then confirm
   the package `version` line reads `0.0.11` and the diff is otherwise
   Pillow-undisturbed (Slice 1's W2 noted `uv add`/`uv lock` can strip the inline
   TODO comment — that is fine here since we are removing it anyway). If `uv lock`
   touches unrelated entries, Worker 2 may instead hand-edit only the
   `version = "0.0.10"` → `"0.0.11"` line on `uv.lock:220` plus the anchor removal
   (the version field is a plain literal in the lock). **Discretion item** — see
   below; either keeps the lock's package version aligned with pyproject/`__init__`
   (AGENTS.md: pyproject `version` and `__init__` `__version__` must match; the
   lock should follow).
5. `docs/GLOSSARY.md:20` version line — handled in **step E1** (it is part of the
   generated GLOSSARY; resolve the DB-vs-script source there).

Per AGENTS.md, `pyproject` `version` and `__init__` `__version__` must match —
all five sites land in this one slice (the bump that `036` deferred to this joint
cut; Decision 10).

#### Step B — Create the `037` SpecDoc (worker-0.md procedure step 2)

Card 037 has NO `SpecDoc` (verified). spec-037 is at its WORKING location
`docs/spec-037-upload_file_image_mapping-0_0_11.md` (NOT archived to `docs/SPECS/`
— per AGENTS.md the archive move is the *next* spec author's Step 8 batched sweep,
never per-card). So the `037` SpecDoc.url uses the **non-`SPECS` `docs/` path**:

```python
from apps.kanban.models import Card, SpecDoc
card = Card.objects.get(number=37)
SpecDoc.objects.create(
    card=card,
    name="spec-037-upload_file_image_mapping-0_0_11",
    url="https://github.com/riodw/django-strawberry-framework/blob/main/docs/spec-037-upload_file_image_mapping-0_0_11.md",
)
```

(`name` is unique; no existing `037` SpecDoc, so `.create()` is correct — not
`.update()`.) The `url` must contain the `docs/…` path the build / `import_spec_terms`
parse.

#### Step C — Reconcile the STALE `036` SpecDoc.url (drift cluster #1 — REQUIRED before regenerate)

The `036` SpecDoc.url in the DB is the stale NON-`SPECS` path; the spec-036 file
is on disk at `docs/SPECS/spec-036-mutations-0_0_11.md` (archived) and the
committed KANBAN already renders the correct `docs/SPECS/` link. Without this
fix, step F3's KANBAN regenerate introduces two broken `036` links (KANBAN lines
100, 1339). Fix the DB to match on-disk + committed reality:

```python
sd36 = SpecDoc.objects.get(card=Card.objects.get(number=36))
sd36.url = "https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-036-mutations-0_0_11.md"
sd36.save()
```

This is the **durable, non-partial** fix: on-disk location, committed KANBAN, and
(after this) the DB all agree on `docs/SPECS/spec-036`. It is in-scope because
Slice 4's mandatory regenerate would otherwise regress a shipped doc. Record it
under `### Spec changes made / Notes` as a reconciled pre-existing-drift cluster
(it is a DB edit, not a spec-file edit, so it belongs in the build report and the
deferred-work/notes, not under "Spec changes made (Worker 1 only)"). **Worker 2:
re-verify the spec-035 SpecDoc.url too** — if `035` shows the same `docs/spec-035`
(non-`SPECS`) drift in the DB while disk + committed KANBAN use `docs/SPECS/`, it
will likewise regress on regenerate; reconcile it the same way and note it. (Only
035/036 are at risk — they are the archived siblings; do NOT touch any card whose
spec genuinely lives at `docs/` working location, including 037.)

#### Step D — Fix the `037` card-body stale refs (drift cluster #3) + mark shipped DoD

Per worker-0.md procedure step 6 (fix card-body content the spec wrap names; mark
shipped `definition_of_done` items complete). The 037 `CardItem` rows
(section `Definition of done` and `Other`) carry stale `034` / `028` refs. The
spec's predecessor analysis + Decision 6 establish the mutations card is `036`;
`034` is permissions, `028` is ordering. These are single-surface `CardItem.text`
values (no un-editable source-comment mirror — the spec/source already name `036`
/ `037` correctly), so fixing them is a coherent same-surface correction, not a
partial-fix-that-diverges. Edit via the ORM:

1. **`Definition of done` items** (4 rows, `section` = "Definition of done"):
   - order=1 text "Mutation input-type generation (`TODO-ALPHA-034-0.0.11`) maps
     the same fields to Strawberry's `Upload` scalar." → change
     `TODO-ALPHA-034-0.0.11` to `DONE-036-0.0.11` (the mutations card, now done).
   - **Mark every shipped DoD item `is_complete = True`** — all four DoD items
     shipped (read converter = Slice 1; write input mapping = Slice 2;
     synthetic-model tests = Slices 1-3; `docs/GLOSSARY.md` conversion-table
     change = this slice's step E). No DoD item is deferred, so all four flip to
     complete (done-card convention).
2. **`Other` section items:**
   - order=1 "pairs with `TODO-ALPHA-034-0.0.11` for the write side." → "pairs
     with `DONE-036-0.0.11` for the write side." (the genuine pairing; spec Risks
     "Pairs with 028" cluster — but here the `Other` order=1 says `034`, and
     order=2 says "Pairs with 028"; both are the stale-pairing cluster).
   - order=2 "… Pairs with 028." → "… Pairs with `DONE-036-0.0.11`." (spec Risks
     lines 1593-1599: preferred reading = the genuine pairing is the mutations
     card `036`, not ordering `028`).
   Keep the rest of each item's prose byte-identical; change only the stale id.
3. **`Definition of done` order=1 also still references the right scalar** — leave
   `Upload` / the field-mapping prose unchanged; only the card-id token moves.

**DISCRETION / ESCALATION NOTE:** the spec's Risks section (lines 1593-1599)
recorded "Pairs with 028" as a conflict with a *preferred reading*, explicitly
NOT silently reconciled at spec-authoring time, "recorded per the NEXT.md 'prefer
the card, surface the conflict' rule." Slice 4 is the card wrap that the spec's
`## Doc updates` authorizes to "fix card-body content the spec wrap names." I
judge the `034`→`036` and `028`→`036` card-body fixes IN SCOPE for the wrap (they
are the genuine pairings the spec's own predecessor/Decision-6 analysis
establishes, and they live only in `CardItem.text` with no divergent mirror). If
Worker 2 or Worker 3 reads the spec's "surface, don't reconcile" framing as
forbidding the card-body fix, leave the stale ids AS-IS and instead record the
`034`/`028` cluster in the build report's `### Notes for Worker 1` for the
deferred-work catalog — DO NOT partial-fix (e.g. fix `034` but leave `028`).
Worker 1 will rule at final verification. The plan's recommendation is: fix both
in the card body (same surface, genuine pairing) AND record the cluster in the
deferred catalog so the integration pass sees it.

#### Step E — `docs/GLOSSARY.md` PROSE body edits (hand-edited source-of-truth; MUST precede step F1)

These are the entry-BODY rewrites — the text the DB `GlossaryTerm.body` is synced
FROM (procedure step 1). Edit the committed file by hand here; step F1 copies
these bodies into the DB so the regenerate is byte-identical.

1. **Version line (`docs/GLOSSARY.md:20`).** `Current package version: \`0.0.10\`.`
   → `Current package version: \`0.0.11\`.`. **RESOLVE the source at build time:**
   determine whether `scripts/build_glossary_md.py` emits this header line from a
   DB value or as a script literal. If script-literal, the bump is a one-line edit
   to `scripts/build_glossary_md.py` (then regenerate); if DB-sourced, edit the DB
   field in step F. Worker 2 records which. (The line sits in the generated header
   above `## Public exports`, so it is part of the generated output — a raw
   hand-edit of the rendered file alone would be reverted by step F3.)
2. **Remove the staged HTML-comment anchor** at `docs/GLOSSARY.md:22-34`
   (`<!-- TODO(spec-037 Slice 4): promote the file/upload glossary surface … -->`).
   This is the file-only staged anchor the baseline diff showed auto-clears on
   regenerate; remove it so the source is clean (regenerate will not re-emit it).
3. **`## DjangoFileType` body (`docs/GLOSSARY.md:341-347`).** Flip status
   `planned for \`0.0.11\`` → `shipped (\`0.0.11\`)` and rewrite the body to the
   shipped contract: resolver-backed output object with `name` (non-null) and
   `path` / `size` / `url` (nullable, storage-safe — degrade to `null` via the
   narrow `_safe_file_attr` catch on `ValueError` / `OSError` / storage
   `NotImplementedError`); an empty / absent file resolves the **whole object** to
   `null`; mapped on **read** via the new `FIELD_OUTPUT_TYPE_MAP` (kept OFF the
   shared `SCALAR_MAP` / filter-input path); consumer `attachment: str` annotation
   override bypasses it. Note `SuspiciousFileOperation` is deliberately NOT
   swallowed (propagates as a security signal). Keep the `**See also:**` line.
4. **`## DjangoImageType` body (`docs/GLOSSARY.md:363-369`).** Same status flip;
   rewrite to: subclasses `DjangoFileType`, adds nullable `width` / `height`
   (degrade to `null` via the same guard when the image is missing/corrupt or the
   backend cannot read dimensions); `ImageField` resolves here (not
   `DjangoFileType`) via the `FIELD_OUTPUT_TYPE_MAP` MRO precedence (`ImageField`
   row precedes `FileField`). Drop the "where Pillow is available" hedge — keep it
   accurate: a consumer `ImageField` already requires Pillow (Django requires it
   for the field); the dimensions degrade to `null` on read failure.
5. **`## \`Upload\` scalar` body (`docs/GLOSSARY.md:1367-1373`).** Status flip;
   rewrite to: Strawberry's built-in `Upload` scalar (`NewType("Upload", bytes)`),
   **re-exported** from the package root (`from django_strawberry_framework import
   Upload`) — needs NO `_PACKAGE_SCALAR_MAP` entry because it already resolves via
   Strawberry's built-in `DEFAULT_SCALAR_REGISTRY` (the deliberate contrast with
   the package-custom `BigInt`). Generated `DjangoMutation` `Input` /
   `PartialInput` types map a `FileField` / `ImageField` editable column to
   `Upload` (required per the shipped per-field rule, `Upload | None` on `blank` /
   `null`). Keep the `**See also:**` line.
6. **`## Scalar field conversion` file/image line (`docs/GLOSSARY.md:1196`).**
   Replace `- file and image fields → string path / URL values` with the
   canonical three-way-split line (pinned above): **read** → structured
   `DjangoFileType` / `DjangoImageType` output objects via `FIELD_OUTPUT_TYPE_MAP`;
   **filter / scalar-input** → `str` (the `SCALAR_MAP` `FileField` / `ImageField`
   rows are unchanged); **mutation input** → `Upload` scalar. Cross-link the three
   entries. (This is the `036`-style "documents the conversion table change" DoD
   item.)
7. **`## Specialized scalar conversions` (`docs/GLOSSARY.md:1261-1273`).** ADD a
   file/image row (this section has none today) recording the **read-side breaking
   wire-format change**, anchored to the `PositiveBigIntegerField → BigInt` `0.0.6`
   precedent: e.g. `- \`FileField\` / \`ImageField\` read output → structured
   \`DjangoFileType\` / \`DjangoImageType\` objects (changed from \`str\` in
   \`0.0.11\` — breaking wire-format change, parallel to the
   \`PositiveBigIntegerField → BigInt\` \`0.0.6\` precedent; opt out per field with
   a \`attachment: str\` annotation override). The filter / scalar-input value
   stays \`str\`; the mutation input is the \`Upload\` scalar.` Keep the existing
   `**See also:**` line.
8. **`## strawberry_config` body (`docs/GLOSSARY.md:1279`).** Remove the stray
   "next: `Upload`" mention: `… bind package-defined scalars (today:
   [\`BigInt\`](#bigint-scalar); next: [\`Upload\`](#upload-scalar) in \`0.0.11\`)
   into …` → `… bind package-defined scalars (today: [\`BigInt\`](#bigint-scalar))
   into …`. `Upload` is a built-in and is NOT a `_PACKAGE_SCALAR_MAP` key, so it
   never rode through `strawberry_config` — the "next: Upload" wording was always
   inaccurate (Decision 5). Leave only `BigInt`.
9. **Reconcile drift cluster #2 — `## DjangoModelPermission` body
   (`docs/GLOSSARY.md` ~389).** Leave the committed file's `DjangoModelPermission`
   body **as-is** (it is the correct, fuller text). It is handled in step F1 by
   syncing the DB body UP to the committed file — NOT by trimming the committed
   file down. Do not edit this entry's prose.

**These prose edits to `docs/GLOSSARY.md` are the one authorized hand-edit of the
generated file's BODY content** — because the body is the source-of-truth the DB
syncs from (procedure step 1). The version line / status-FK / Public-exports
list / Index rows / Browse-by-category row are DB-FIELD-backed and handled in
step F (do NOT hand-edit those in the rendered file; the regenerate would revert
them).

#### Step F — DB pass: glossary terms + card close (worker-0.md procedure steps 1, 3-6)

Run via `uv run python examples/fakeshop/manage.py shell`. ORM only — never raw
SQL (the `post_save` `UUIDModel` side-row is required by the GraphQL render).

**F1 — Sync glossary `GlossaryTerm` rows (procedure step 1):**
- For `upload-scalar`, `djangofiletype`, `djangoimagetype`: set
  `status = GlossaryStatus.objects.get(key="shipped")` AND set `.body` to the
  text between the `**Status:** …` line and the next `## ` heading of the
  **committed (step-E-edited)** `docs/GLOSSARY.md` entry, stripped. `.save()`.
  (entry_order / index_order are unchanged — the entries already exist in their
  alphabetical slots; only status + body move.)
- **Reconcile drift cluster #2:** set `djangomodelpermission`'s `GlossaryTerm.body`
  to the committed file's fuller body (the `check_permission` sync /
  empty-list-AllowAny / `SyncMisuseError` paragraph) so step G's GLOSSARY diff is
  clean. (Status stays `shipped`.)
- Worker 2 should also spot-check (via a pre-edit `git diff` of the baseline
  regenerate, already captured at planning) whether any OTHER existing term body
  drifts; if so, reconcile it the same way. The planning baseline diff showed ONLY
  `djangomodelpermission` as real body drift, but re-verify after the step-E edits.

**F2 — Index rows / Public exports / Browse-by-category (DB-field-backed):**
The Index-table status column, the Public-exports list, and the Browse-by-category
row are all rendered by `build_glossary_md.py` from the glossary DB. After F1's
status flip to `shipped`, the three Index rows (`DjangoFileType`,
`DjangoImageType`, `Upload` scalar) will render `shipped (\`0.0.11\`)`
automatically. Worker 2 must VERIFY whether the **Public exports** list and the
**Browse-by-category** "File / image uploads" row are DB-sourced (they likely are
— the whole GLOSSARY is generated) or partly script-literal; the spec (lines
1499-1502) wants the three symbols in **Public exports** + the **Index** + the
**Browse-by-category** row. They are already PRESENT in the committed file (Public
exports does NOT currently list the three — verify; Browse-by-category line 177
DOES list all three). RESOLVE at build time: if Public-exports is DB/script-driven,
ensure the three appear after regenerate; if the three are missing from the
generated Public-exports, that is a render-input gap to fix in the DB/script, not
a hand-edit. **Worker 2 records the source-of-truth for each of these three
sub-surfaces** (Index = DB status, Public exports = ?, Browse = ?).

**F3 — Card close (procedure steps 2-6, already partly done in B/C/D):**
1. (Step B done) SpecDoc created for 037.
2. (Step D done) card-body stale refs fixed; shipped DoD items `is_complete=True`.
3. **Bootstrap ≥1 `CardGlossaryTerm`** so the done-save passes the signal
   invariant (a card cannot save `status=done` without ≥1 glossary link AND a
   SpecDoc): create one `CardGlossaryTerm` linking card 37 to a term in the
   037 CSV (e.g. `upload-scalar`). `import_spec_terms` reconciles the full set
   next.
4. **Flip status:** `card.status = Status.objects.get(key="done"); card.save()`
   (ORM `.save()` fires the pre_save validation + sets `milestone_id`; the
   rendered id auto-becomes `DONE-037-0.0.11`).
5. **Sync the full glossary-link set:** `uv run python
   examples/fakeshop/manage.py import_spec_terms` (creates `CardGlossaryTerm` +
   `GlossarySpecMention` rows from the 037 CSV — all 20 anchors already exist as
   `GlossaryTerm` rows, so no "missing anchor" failure).

**F3-regenerate — Regenerate all three docs (procedure step 7), from the repo root:**
- `uv run python scripts/build_kanban_md.py`
- `uv run python scripts/build_kanban_html.py`
- `uv run python scripts/build_glossary_md.py`

#### Step G — Byte-clean-regenerate verification (procedure step 8)

- `uv run python examples/fakeshop/manage.py import_spec_terms --check` reports OK
  for all done cards (including the new 037).
- `git diff docs/GLOSSARY.md` shows ONLY the intended Slice-4 changes (status
  flips, the three rewritten bodies, the version line, the new
  Specialized-scalar row, the `strawberry_config` "next: Upload" removal, the
  `DjangoModelPermission` body now matching) and **no spurious revert** of any
  prior-card content — i.e. the DB regenerates the committed glossary identically
  apart from this card's edits. Prove stability by regenerating a SECOND time and
  confirming the file is byte-identical across the two consecutive regenerates
  (a single `git diff` shows only the cumulative HEAD diff, not second-regenerate
  stability).
- `git diff KANBAN.md` shows the 037 card moved to the Done section as
  `DONE-037-0.0.11` with its DoD ticked, the `037` `- Spec:` line present and
  pointing at `docs/spec-037-…` (working location), the `036`/`035` spec links
  STILL `docs/SPECS/…` (cluster #1 reconciled — NOT regressed to the broken
  non-SPECS path), and the card-body `034`/`028` stale refs fixed to `036`.
- `uv run python examples/fakeshop/manage.py check` passes.
- `KANBAN.html` regenerated (verify it changed consistently with `KANBAN.md`).

#### Step H — `README.md` + `docs/README.md` (hand-edited, NOT generated; spec lines 1503-1508)

- **`README.md` Status block (`README.md:59-71`).** Remove the `<!-- TODO(spec-037
  Slice 4) … -->` anchor at `README.md:61-67`. Change `**\`0.0.10\`,
  single-maintainer, alpha-quality.**` → `**\`0.0.11\`, single-maintainer,
  alpha-quality.**`. Update "Newest shipped surface:" to name the `Upload` scalar
  + generated file/image mutation-field typing as the `0.0.11` newest surface
  (with the canonical "NOT multipart HTTP ergonomics — those await the `0.0.14`
  `TestClient`" caveat), keeping the existing cascade-permissions / Relay prose as
  the prior-surface context. Worker 2 weaves the new sentence in without bloating
  the (already long) paragraph — a concise "and the `0.0.11` `Upload` scalar +
  generated `FileField` / `ImageField` mutation-input typing and the structured
  `DjangoFileType` / `DjangoImageType` read output" clause.
- **`README.md` line 57** ("Coming from DRF" paragraph) already says "Mutations
  ship today too … lands in `0.0.11`". Verify it does not separately claim the
  `Upload` part is future; if it implies uploads are not yet shipped, tighten to
  note `Upload` ships in the same `0.0.11`. (Likely no change needed — it speaks
  to mutations generally.)
- **`docs/README.md` "Shipped today" (`docs/README.md:97-105`).** Remove the
  `<!-- TODO(spec-037 Slice 4) … -->` anchor at lines 98-105. Change
  `**Shipped today** (\`0.0.10\`):` → `**Shipped today** (\`0.0.11\`):`. The
  scalar-conversion bullet (line 107) already says "file/image" — update its
  parenthetical so file/image reads as the structured output objects, not "file"
  generically (keep it terse).
- **`docs/README.md` "Coming next" (`docs/README.md:133-134`).** MOVE the
  `0.0.11` Upload item OUT of "Coming next": delete line 134
  (`- \`0.0.11\` — the \`Upload\` scalar + file/image field mapping (the sibling
  write-side card; …)`) and ADD a shipped bullet (or extend the existing
  mutations shipped bullet at line 131) naming the `Upload` scalar + generated
  file/image mutation-input typing + the structured `DjangoFileType` /
  `DjangoImageType` read output as shipped in `0.0.11`, WITH the canonical
  multipart-caveat. Worker 2's discretion whether to add a dedicated shipped
  bullet or fold into line 131; the load-bearing requirement is the `0.0.11`
  Upload item no longer appears under "Coming next" and the multipart caveat is
  present. Keep the `0.0.12` / `0.0.13` / `0.0.14` "Coming next" items intact.

#### Step I — `GOAL.md` criterion 6 (hand-edited; spec lines 1508-1511, 413-415)

- Remove the `<!-- TODO(spec-037 Slice 4) … -->` block at `GOAL.md:511-517`.
- Update criterion 6 (`GOAL.md:518`) to note that the `Upload` / `FileField` /
  `ImageField` part ships for **generated `DjangoMutation` inputs** in `0.0.11`,
  while the `ModelForm` / `ModelSerializer` mutation flavors in that same
  criterion still land later (`0.0.12` / `0.0.13`). Do NOT imply multipart
  `TestClient` ergonomics are part of this card. Suggested shape: keep the
  criterion's existing structure ("Write mutations declaratively from `ModelForm`,
  `ModelSerializer`, or auto-generated `Input` types — one shared `errors:
  list[FieldError]` envelope … plus `Upload` scalar for `FileField` /
  `ImageField`") and append a parenthetical or short clause clarifying the
  `Upload` + auto-generated-`Input` part ships in `0.0.11` while the form /
  serializer flavors are later. Worker 2 picks the minimal edit that satisfies
  the spec's constraint.

#### Step J — `TODAY.md` scalar-conversion table (hand-edited; spec lines 1511-1514, 416-417)

- Remove the `<!-- TODO(spec-037 Slice 4) … -->` block at `TODAY.md:110-117`.
- Rewrite the `- \`FileField\` / \`ImageField\` → \`str\`` row (`TODAY.md:118`) to
  the structured output objects: read output → `DjangoFileType` / `DjangoImageType`
  (with the canonical three-way-split note that filter/scalar input stays `str`
  and the generated mutation input is `Upload`).
- Note (per spec line 1513-1514) that **upload mutation inputs are a package
  capability NOT exercised by fakeshop products** — add a one-line entry to the
  "Shipped package capabilities not exercised by products" section
  (`TODAY.md:323-332`) for the `Upload` scalar + file/image output objects /
  generated upload mutation inputs (products has no file/image column;
  synthetic-model tests cover it; live fakeshop upload surface deferred to
  `TODO-BETA-051-0.1.5`). Keep `TODAY.md` products-centric and capability-focused
  (its scope rule, lines 5-7) — do NOT add a new fakeshop file model narrative.

#### Step K — `CHANGELOG.md` `0.0.11` entry (AUTHORIZED — spec lines 1514-1516; maintainer-authorized per the preamble)

The `[Unreleased]` section (`CHANGELOG.md:19-34`) currently holds the `036`
mutation bullets under `### Added` / `### Changed` / `### Fixed`. Convert
`## [Unreleased]` → `## [0.0.11] - 2026-06-19` (the version MUST equal
`pyproject`/`__init__` `0.0.11`; the date is a placeholder the maintainer may
adjust). ADD the `037` bullets to the appropriate headings:

- **`### Added`** — three bullets (or one combined, Worker 2's call) covering:
  (1) the structured **read output objects** `DjangoFileType` (`name` non-null;
  `path` / `size` / `url` nullable, storage-safe) / `DjangoImageType` (+ nullable
  `width` / `height`), mapped via the new `FIELD_OUTPUT_TYPE_MAP` (kept off the
  shared `SCALAR_MAP` / filter-input path), with an empty file resolving the
  whole object to `null` and per-subfield storage-failure degradation; (2) the
  **`Upload` scalar re-export** from the package root (a Strawberry built-in via
  `DEFAULT_SCALAR_REGISTRY` — no `_PACKAGE_SCALAR_MAP` entry, the contrast with
  `BigInt`) and the **generated `DjangoMutation` mutation-input mapping** of
  `FileField` / `ImageField` → `Upload` (required per the shipped per-field rule,
  `Upload | None` on `blank` / `null`); (3) the **three new public exports**
  `Upload` / `DjangoFileType` / `DjangoImageType` (re-exported from the package
  root, added to `__all__`).
- **`### Changed`** — the **read-side breaking wire-format change**: `FileField` /
  `ImageField` read output changed from `str` to the structured `DjangoFileType` /
  `DjangoImageType` objects (acceptable pre-`1.0.0`, parallel to the
  `PositiveBigIntegerField → BigInt` `0.0.6` and model-anchored `GlobalID` `0.0.9`
  precedents; opt out per field with an `attachment: str` annotation override).
  The filter / scalar-input shape is unchanged (still `str`).
- Add the standard "`django_strawberry_framework.__version__` is now `0.0.11`"
  bullet under `### Changed` (matching every prior cut's version-bump bullet,
  e.g. `[0.0.8]` "`__version__` is now `0.0.8`").
- Use ONLY `### Added` / `### Changed` headings the spec authorizes (spec lines
  1513-1516 name `### Added` / `### Changed`); do NOT invent `### Fixed` /
  `### Removed` for this card (there is no fix/removal). Keep the existing `036`
  bullets in their sections (they ship in the same `0.0.11` release).
- Match the canonical phrasings (the three-way split, the breaking-change
  precedent, the no-`_PACKAGE_SCALAR_MAP` `Upload` contrast) so Worker 3's
  `### CHANGELOG sanity` finds no overstate/understate. Worker 3 verifies the
  version line equals `pyproject`/`__init__`, the headings are spec-authorized,
  and nothing overstates (e.g. does NOT claim multipart transport ships).

### Test additions / updates

- **Only one test change in the entire slice:** `tests/base/test_init.py::test_version`
  assertion `0.0.10` → `0.0.11` (step A3). No new behavior tests — the read /
  write / export behaviors shipped and were tested in Slices 1-3. No `--cov*`
  invocation, ever.
- Worker 2 should run the focused gate `uv run pytest tests/base/test_init.py
  --no-cov` to confirm `test_version` now passes at `0.0.11` (and the public-API
  surface test still passes — Slice 3 pinned the three exports, unchanged here).
  No other focused test is required by this slice.

### Implementation discretion items

These are stylistic / equivalent-shape choices I have assessed and decided belong
to Worker 2 — not architectural escape hatches.

- **`uv.lock` bump mechanism** (step A4): `uv lock` (regenerate from the bumped
  `pyproject.toml`) vs. a targeted hand-edit of the single `version = "0.0.10"` →
  `"0.0.11"` line on the package entry + anchor removal. Both align the lock's
  package version with `pyproject`/`__init__`. Prefer `uv lock` if it leaves
  unrelated entries (incl. Pillow) undisturbed; fall back to the hand-edit if
  `uv lock` churns the lock. Worker 2 records which and confirms the diff is
  version-only + anchor-only.
- **GLOSSARY version line + Public-exports + Browse-by-category source-of-truth**
  (steps E1, F2): whether each is DB-field-sourced or script-literal in
  `build_glossary_md.py` is a RESOLVE-at-build-time investigation, not a free
  choice — Worker 2 determines the actual source for each and edits THAT source
  (DB field or script), never the rendered file alone. The requirement is fixed
  (version line reads `0.0.11`; the three symbols appear in Public exports + Index
  shipped + Browse-by-category); the *mechanism* per sub-surface is what Worker 2
  resolves and records.
- **CHANGELOG `037` bullets: three separate `### Added` bullets vs. one combined**
  (step K): either is acceptable as long as all three Added facts (read objects,
  `Upload` re-export + mutation-input mapping, three exports) and the one Changed
  fact (read breaking-wire-format) are present and the version-bump bullet is
  added. Worker 2 picks the shape that reads cleanest against the existing `036`
  bullets.
- **`docs/README.md` shipped-Upload placement** (step H): dedicated new shipped
  bullet vs. extending the existing line-131 mutations bullet. Either satisfies
  "moved out of Coming next, multipart caveat present."
- **`GOAL.md` criterion 6 minimal-edit shape** (step I): parenthetical vs. short
  trailing clause — Worker 2 picks the minimal edit satisfying "Upload + generated
  Input ships `0.0.11`; ModelForm/ModelSerializer later; no multipart-TestClient
  implication."
- **Card-body `034`/`028` fix vs. defer-and-record** (step D): the plan
  RECOMMENDS fixing both in the card body (same surface, genuine pairing the
  spec's own analysis establishes) AND recording the cluster in the deferred
  catalog. If Worker 2 reads the spec's Risks "surface, don't reconcile" framing
  as forbidding the card-body fix, it may leave the stale ids and record-only —
  but must NOT partial-fix (both or neither). Worker 1 rules at final verification.

### Spec slice checklist (verbatim)

The spec's nested sub-bullets for Slice 4 from `## Slice checklist` (spec lines
388-421), copied verbatim:

- [x] Slice 4: docs + the `0.0.11` version cut + card wrap (per
  [Doc updates](#doc-updates) /
  [Decision 10](#decision-10--this-card-owns-the-final-0011-version-bump))
  - [x] **Version files to `0.0.11`**
    ([Decision 10](#decision-10--this-card-owns-the-final-0011-version-bump)):
    [`pyproject.toml`][pyproject], `__version__` in [`__init__.py`][init],
    [`tests/base/test_init.py::test_version`][test-base-init], the
    [`docs/GLOSSARY.md`][glossary] package-version line, and `uv.lock` if it
    carries the package version.
  - [x] [`docs/GLOSSARY.md`][glossary] (promote
    [`Upload` scalar][glossary-upload-scalar] /
    [`DjangoFileType`][glossary-djangofiletype] /
    [`DjangoImageType`][glossary-djangoimagetype] to `shipped (0.0.11)`; rewrite
    the [Scalar field conversion][glossary-scalar-field-conversion] file/image
    row and **add** a file/image row to
    [Specialized scalar conversions][glossary-specialized-scalar-conversions]
    (which has none today); add the three to **Public exports** + the **Index** +
    the **File / image uploads** browse-by-category row; record the read-side
    breaking-wire-format change; remove the
    [`strawberry_config`][glossary-strawberry-config] entry's stray "next:
    `Upload`" mention), [`docs/README.md`][docs-readme] /
    [`README.md`][readme] (move the `Upload` scalar + generated file/image field
    typing from "Coming next (`0.0.11`)" to "Shipped today" — wording the
    *scalar and generated mutation-field typing*, **not** full multipart HTTP
    upload ergonomics, which await the `0.0.14` [`TestClient`][glossary-testclient]
    — and the README **Status** line from `0.0.10` to `0.0.11`), [`GOAL.md`][goal]
    (note that criterion 6's `Upload` / `FileField` / `ImageField` part ships for
    generated `DjangoMutation` inputs — the `ModelForm` / `ModelSerializer`
    flavors in that same criterion still land later), [`TODAY.md`][today] (rewrite the
    scalar-conversion table's `FileField` / `ImageField` → `str` row to the
    structured output objects and note upload mutation inputs as a package
    capability not exercised by products), [`CHANGELOG.md`][changelog] (only if
    the Slice 4 maintainer prompt explicitly requests it), [`KANBAN.md`][kanban]
    (card → Done via the kanban DB + re-render).

---

## Build report (Worker 2)

### Files touched

Slice-4-intended (my diff):

- `pyproject.toml` — `[project].version` `0.0.10` → `0.0.11`; removed the 2-line `TODO(spec-037 Slice 4)` anchor (step A1). Pillow dev-dep untouched (it appears in the cumulative-vs-HEAD diff because Slice 1 added it; not my edit).
- `django_strawberry_framework/__init__.py` — `__version__` `0.0.10` → `0.0.11`; removed the version-bump `TODO` anchor (step A2). The Upload/DjangoFileType/DjangoImageType imports + `__all__` entries in the cumulative diff are Slice 3's, not mine — re-confirmed present and unchanged by me.
- `tests/base/test_init.py` — `test_version` assertion `0.0.10` → `0.0.11`; removed the file-top `TODO` anchor; updated the now-stale "`test_version` is untouched" clause in `test_public_api_surface_is_pinned`'s comment to "owns `test_version`, asserted at `0.0.11` above" (the only non-mechanical text touch, tightly coupled to the version assertion) (step A3).
- `uv.lock` — package entry `version` `0.0.10` → `0.0.11` via `uv lock` (regenerated from the bumped pyproject); the TODO anchor was stripped by the regenerate. Verified `diff` of the pre-`uv lock` working tree vs post shows ONLY the version line + anchor changed — Pillow block + all other entries undisturbed (step A4, discretion item resolved to `uv lock`).
- `docs/GLOSSARY.md` — REGENERATED from the edited DB (`scripts/build_glossary_md.py`). Contains: version line `0.0.11` (status-legend BoardDoc), staged HTML-comment anchor removed, 3 Index rows + 3 entry status flips to `shipped (0.0.11)`, 3 entry-body rewrites (`DjangoFileType` / `DjangoImageType` / `Upload` scalar), Public-exports list + 3 symbols, `Scalar field conversion` file/image line rewritten, new `Specialized scalar conversions` file/image row, `strawberry_config` "next: Upload" removed. NO spurious revert of prior content (cluster #2 `DjangoModelPermission` body synced UP).
- `KANBAN.md` / `KANBAN.html` — REGENERATED. Card 037 moved to Done as `DONE-037-0.0.11` (working-location spec link), 036 spec link kept at `docs/SPECS/` (cluster #1 reconciled, NOT regressed), card-body `034`→`036` + "Pairs with 028"→"`DONE-036-0.0.11`" fixed, DoD all `- [x]`, progress stats updated, cross-card `TODO-ALPHA-037`→`DONE-037` refs updated.
- `examples/fakeshop/db.sqlite3` — DB card-close + glossary edits via the Django ORM only (steps B–F). No raw SQL.
- `README.md` — Status block: `0.0.10`→`0.0.11`, TODO anchor removed, "Newest shipped surface" now names the `0.0.11` Upload scalar + generated file/image mutation-field typing + structured read output, with the canonical multipart caveat (step H).
- `docs/README.md` — "Shipped today" `0.0.10`→`0.0.11`, TODO anchor removed, scalar-conversion bullet's file/image parenthetical rewritten; new shipped bullet for the Upload scalar + file/image mapping with the multipart caveat; the `0.0.11` item removed from "Coming next" (header retitled `0.0.12 → 0.0.14`). Added `[glossary-upload-scalar]` link def (step H).
- `GOAL.md` — criterion 6: TODO block removed; appended a clause noting the `Upload` + auto-generated-`Input` flavor ships `0.0.11` while the `ModelForm` (`0.0.12`) / `ModelSerializer` (`0.0.13`) flavors land later; no multipart-TestClient implication (step I).
- `TODAY.md` — scalar-conversion table file/image row rewritten to the structured output objects (+ filter-input=`str`, mutation-input=`Upload`, breaking-change note); new entry in "Shipped package capabilities not exercised by products" for the Upload scalar + file/image mapping (products has no file column; synthetic-model tests cover it; live surface deferred to `TODO-BETA-051-0.1.5`). Added `[glossary-djangofiletype]` / `[glossary-djangoimagetype]` / `[glossary-upload-scalar]` link defs (step J).
- `CHANGELOG.md` (MAINTAINER-AUTHORIZED) — `## [Unreleased]` → `## [0.0.11] - 2026-06-19`; 3 new `### Added` bullets (read output objects; Upload re-export + mutation-input mapping; three new public exports); 2 new `### Changed` bullets (read-side breaking wire-format change; `__version__` is now `0.0.11`). Existing 036 Added/Changed/Fixed bullets kept in their sections (same `0.0.11` release). Only `### Added` / `### Changed` headings used (spec-authorized). Added `[glossary-djangofiletype]` / `[glossary-djangoimagetype]` / `[glossary-scalar-field-conversion]` / `[glossary-upload-scalar]` link defs (step K).

NOT my churn (accepted Slices 1–3 baseline, present at task start, left untouched): `django_strawberry_framework/mutations/inputs.py`, `mutations/resolvers.py`, `scalars.py`, `types/base.py`, `types/converters.py`, `types/finalizer.py`, `types/resolvers.py`; `tests/mutations/test_inputs.py`, `test_resolvers.py`, `tests/test_scalars.py`, `tests/types/test_base.py`, `test_converters.py`, `test_resolvers.py`; `docs/spec-037-…md` (Worker 1's prior-slice edits); the `bld-*.md` / `build-*.md` artifacts.

### Tests added or updated

- `tests/base/test_init.py::test_version` — assertion `0.0.10` → `0.0.11` (the ONLY test change in the slice; no new behavior tests — read/write/export behavior shipped + tested in Slices 1–3).

### Validation run

- `uv run ruff format .` — pass (287 files left unchanged; the standing COM812-vs-formatter warning is pre-existing config noise, not a new finding).
- `uv run ruff check --fix .` — pass ("All checks passed!"; zero fixes applied).
- `git status --short` after both ruff invocations — every modified file classified above. ZERO tool churn introduced (ruff changed nothing), so nothing to revert. The 13 Slices-1–3 source/test files + the spec + the `??` artifacts are accepted baseline, not my churn.
- `uv run pytest tests/base/test_init.py --no-cov` — 5 passed (incl. `test_version` at `0.0.11`, `test_public_api_surface_is_pinned`, `test_file_upload_exports_resolve_to_their_source_definitions`). No `--cov*` flag used.
- **DB card-close + regenerate verification (the load-bearing checks):**
  - Baseline regenerate-to-temp diff run BEFORE any DB edit (confirmed the plan's ground truth: KANBAN 5-line / GLOSSARY 16-line deltas = staged HTML-comment auto-clear + cluster #1 (036 spec-path) + cluster #2 (`DjangoModelPermission` body) + the missing-037-SpecDoc `- Spec:` line). Restored committed files + worked from committed state.
  - `git diff docs/GLOSSARY.md` shows ONLY intended Slice-4 changes; NO spurious revert of prior content (cluster #2 reconciled by syncing the DB body UP).
  - **Byte-clean stability proven by regenerating TWICE: the second regenerate is byte-identical to the first** (md5 of GLOSSARY + KANBAN.md + KANBAN.html identical across two consecutive runs). Re-verified idempotent after ALL edits.
  - `uv run python examples/fakeshop/manage.py import_spec_terms --check` — `OK: 37 done cards have glossary links.`
  - `uv run python examples/fakeshop/manage.py check` — `System check identified no issues (0 silenced).`
  - `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` — `No changes detected` (DB data edits caused no model drift).
  - `uv run python scripts/check_spec_glossary.py --spec docs/spec-037-…md` — `OK: 20 terms`.

### Implementation notes

- **GLOSSARY DB-source resolution (step E1/F2 RESOLVE items):** the version line is the `kanban.BoardDoc` `key="status-legend"` body (DB-sourced — edited the DB field, NOT the script or rendered file). Public-exports is the `kanban.BoardDoc` `key="public-exports"` body, rendered verbatim (DB-sourced — added the 3 symbols to the BoardDoc body). Index status column renders from `GlossaryTerm.status` (auto-flips on the F1 status change). Browse-by-category "File / image uploads" already listed all three (no edit needed). Recorded per the plan's "Worker 2 records the source-of-truth for each sub-surface."
- **Term-body sync is broader than the plan's F1 list.** Steps E6/E7/E8 (`Scalar field conversion`, `Specialized scalar conversions`, `strawberry_config`) are ALSO DB-backed `GlossaryTerm.body` rows. My first regenerate REVERTED my hand-edits to those three (they were not in the F1 sync list). Caught it via the post-regenerate diff scan, re-applied the prose, and synced `scalar-field-conversion` / `specialized-scalar-conversions` / `strawberry_config` bodies to the DB (anchors verified), then regenerated → byte-clean. This is the exact "hand-edit reverted by regenerate" trap; it is now resolved. Flagging it for Worker 1 awareness below.
- **`upload-scalar` term body keeps a trailing `---`.** The `Upload` scalar entry is the last `GlossaryTerm` alphabetically, and its stored `GlossaryTerm.body` includes the trailing `\n\n---` section separator (verified against the pre-edit DB body). The other two output-type bodies do NOT. Copied the bodies verbatim from the committed file (procedure step 1) rather than paraphrasing, so the regenerate is byte-identical.
- **`uv.lock` bump = `uv lock` (discretion item).** Chose `uv lock` over hand-edit; it regenerated only the version line + stripped the anchor, leaving Pillow + all other entries undisturbed (verified by diffing pre/post snapshots).
- **`CardItem.section` is an FK to `Section`, not a CharField.** Filtered the 037 card-body edits by `section__key` (`definition_of_done` / `other`), not by the display label.
- **Card-body stale-ref disposition (step D / drift cluster #3):** applied the plan's RECOMMENDED path — fixed BOTH `034`→`DONE-036-0.0.11` (DoD order=1 + Other order=1) AND "Pairs with 028"→"Pairs with `DONE-036-0.0.11`" (Other order=2), since these are single-surface `CardItem.text` values with no divergent un-editable mirror and the spec's own predecessor/Decision-6 analysis establishes 036 as the genuine pairing. All 4 DoD items marked `is_complete=True` (all shipped). Recorded in the deferred-work note below for the integration pass per the plan.
- **Drift cluster #1 (036 SpecDoc.url) reconciled:** DB `036` SpecDoc.url was the stale non-`SPECS` path while disk + committed KANBAN use `docs/SPECS/`; fixed the DB to `docs/SPECS/spec-036-…`. Verified `035` was already correct (`docs/SPECS/`) — no edit. 037's own SpecDoc created at the `docs/` working location (spec not archived; per AGENTS.md the archive sweep is the next spec author's Step 8).
- **Drift cluster #2 (`DjangoModelPermission` body) reconciled:** synced the DB `djangomodelpermission` `GlossaryTerm.body` UP to the fuller committed-file text (did NOT trim the committed file down), so the regenerate preserves the shipped 036-era paragraph.

### Notes for Worker 3

- The single load-bearing review surface is the three generated docs (`docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`) + the DB (`db.sqlite3`) + the 6 hand-edited standing docs + the version quintet. NO package source/test logic changed except `test_version`'s one-line assertion.
- `### CHANGELOG sanity` applies in full (maintainer-authorized). The `[0.0.11]` version line equals `pyproject`/`__init__` `0.0.11`; only `### Added` / `### Changed` headings used (the spec authorizes exactly those for 037); existing 036 bullets retained in-section. The breaking-change bullet does NOT claim multipart transport ships (caveat present in README/docs/README).
- `### Documentation / release sanity` applies. Byte-clean regenerate proven by two consecutive byte-identical regenerates (md5). The card appears exactly once in Done; the spec links resolve (036 at `docs/SPECS/`, 037 at `docs/` working location — both files verified on disk). All new in-page GLOSSARY anchor links and the new reference-style `[glossary-*]` link defs in README/docs/README/TODAY/CHANGELOG resolve to existing headings.
- To re-verify byte-clean stability: regenerate the three docs twice and `diff` the md5s; confirm `git diff docs/GLOSSARY.md` carries only the intended status flips / body rewrites / version line / new rows / "next: Upload" removal and no prior-content revert.
- Pre-existing `Last refreshed:` date in `KANBAN.md` moved `2026-06-17` → `2026-06-19` automatically by the regenerate (BoardDoc/render-driven, not a hand-edit) — expected.

### Notes for Worker 1 (spec reconciliation)

- **DB drift-cluster reconciliations applied (NOT spec-file edits — recorded here for the deferred-work catalog, per the plan's step C/D and worker-0.md procedure):**
  - Cluster #1: `036` SpecDoc.url `docs/spec-036` → `docs/SPECS/spec-036` (durable fix; on-disk + committed KANBAN + DB now all agree). `035` already correct.
  - Cluster #2: `djangomodelpermission` `GlossaryTerm.body` synced UP to the fuller committed-file text.
  - Cluster #3: `037` card-body stale refs fixed in `CardItem.text` — `TODO-ALPHA-034-0.0.11`→`DONE-036-0.0.11` (DoD order=1 + Other order=1) and "Pairs with 028"→"Pairs with `DONE-036-0.0.11`" (Other order=2). Applied the plan's RECOMMENDED both-or-neither path (fixed both). The spec's Risks section (lines 1593-1599, 1606-1612) recorded the "Pairs with 028" / stale-`034` conflicts with a *preferred reading* under the NEXT.md "prefer the card, surface the conflict" rule, explicitly NOT silently reconciled at authoring time; Slice 4's `## Doc updates` card-wrap authorizes fixing card-body content the wrap names, and these are single-surface `CardItem.text` values. If Worker 1 reads the Risks framing as forbidding the card-body fix, the fallback is to revert these three `CardItem.text` edits and record-only — but that is a DB edit, not a spec-file edit.
- **Plan-vs-reality delta (term-body sync scope):** the plan's step F1 named only `upload-scalar` / `djangofiletype` / `djangoimagetype` + the `djangomodelpermission` cluster for DB body sync, but steps E6/E7/E8 also edit DB-backed `GlossaryTerm.body` rows (`scalar-field-conversion`, `specialized-scalar-conversions`, `strawberry_config`). I synced all three additional bodies to the DB so the regenerate is byte-clean. No spec change needed; flagging so final verification expects these three extra DB body edits in the diff.
- **`Card.planning_state` ("Status:" card-body line) left as `In progress` on the DONE-037 card.** The rendered `- Status:` line comes from `card.planningState.label`, a free-text field SEPARATE from the kanban workflow `status` FK. The immediately-prior `DONE-036-0.0.11` card (closed by the prior build cycle) ALSO renders `Status: In progress`, so I followed that established precedent and the plan/worker-0 "leave unrelated card-body prose alone" rule rather than unilaterally flipping it to "Shipped" (which `DONE-035` shows). If the maintainer/Worker 1 wants freshly-closed cards to read "Shipped", that is a separate `planningState` edit that should also re-touch DONE-036 for consistency — flagging, not fixing.

---

## Review (Worker 3)

Reviewed the Slice-4-owned files (`CHANGELOG.md`, `GOAL.md`, `README.md`, `docs/README.md`, `TODAY.md`, `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`, `examples/fakeshop/db.sqlite3`) and the Slice-4 increments on prior-slice files (`__init__.py` `__version__` + anchor, `tests/base/test_init.py::test_version`, `pyproject.toml` `[project].version`, `uv.lock` package version). Slice 1–3 source/test work and the spec's Slice 1–3 prose edits are accepted baseline, NOT under review. Used `### Files touched` as the cumulative-diff navigational filter.

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

- No new code/symbols this slice (docs + version + DB only), so no logic duplication to flag. The version literal is the single canonical `0.0.11` across all five quintet sites (verified identical strings — no `v0.0.11` / `.dev` drift). The breaking-wire-format note reuses the established `PositiveBigIntegerField → BigInt` `0.0.6` precedent phrasing verbatim in both the GLOSSARY `Specialized scalar conversions` new row and `TODAY.md`, rather than coining new vocabulary — exactly the DRY shape the plan pinned. The three-way-split sentence (read=object / filter-input=`str` / mutation-input=`Upload`) is stated once in the GLOSSARY `Scalar field conversion` line and referenced (not re-spelled) elsewhere. No drift between the GLOSSARY breaking-change row, the `DjangoFileType`/`DjangoImageType` bodies, the CHANGELOG `### Changed` bullet, and `TODAY.md` — all anchor to the same precedent and the same opt-out (`attachment: str`).

### Public-surface check

The Slice-4 hunk to `django_strawberry_framework/__init__.py` changes ONLY `__version__` (`0.0.10` → `0.0.11`) and removes the `# TODO(spec-037 Slice 3/4)` anchor block. The `Upload` / `DjangoFileType` / `DjangoImageType` import lines and their `__all__` entries present in the cumulative working-tree diff are Slice 3's accepted work (confirmed against the Slice 3 acceptance recorded in worker-3 memory: "three root re-exports … `__all__` in true `sorted()` order; VERSION GUARD held (`0.0.10` byte-unchanged)"), NOT a Slice-4 change. `__all__` is unchanged by Slice 4. `tests/base/test_init.py::test_public_api_surface_is_pinned` passes (`uv run pytest tests/base/test_init.py --no-cov` → 5 passed), confirming `__all__` matches the pinned tuple. The one `test_init.py` comment edit in `test_public_api_surface_is_pinned` (rewording the stale "`test_version` is untouched" sentence to "asserted at `0.0.11` above") is a tightly-coupled, correct follow-on to the version bump that Slice 4 owns — in-scope, not a public-surface change.

### CHANGELOG sanity

Maintainer-authorized edit (recorded in the Plan preamble); full gate applied.

- **Version line matches:** `## [0.0.11] - 2026-06-19` equals `pyproject.toml` `version = "0.0.11"` and `__init__.py` `__version__ = "0.0.11"` (and `uv.lock` + the GLOSSARY package-version line). The `[Unreleased]` heading is fully consumed into `[0.0.11]` (zero `Unreleased` occurrences remain); `## [0.0.11]` appears exactly once and sorts above `## [0.0.9]` (there is no separate `[0.0.10]` release heading — consistent with the spec narrative that `0.0.10`/`0.0.11` were not cut separately and `036`'s work sat under `[Unreleased]`).
- **Headings spec-authorized:** only `### Added` and `### Changed` are used for the `037` bullets (spec lines 1513-1516 authorize exactly those for this card). No `### Fixed` / `### Removed` was invented for `037`; the existing `### Fixed` content is `036`'s, correctly retained in-section (same `0.0.11` release).
- **Wording matches shipped behavior / canonical phrasings:** three `### Added` bullets (read output objects via `FIELD_OUTPUT_TYPE_MAP` kept off `SCALAR_MAP`; `Upload` re-export with the no-`_PACKAGE_SCALAR_MAP` `BigInt` contrast + the mutation-input mapping; three new public exports) and two `### Changed` bullets (the read-side breaking wire-format change anchored to the `0.0.6`/`0.0.9` precedents with the `attachment: str` opt-out; the standard `__version__` is now `0.0.11` bullet). Nothing overstates: the breaking-change bullet explicitly keeps the filter/scalar-input shape `str` and does NOT claim multipart transport ships. The four new reference-style link defs (`glossary-djangofiletype`, `glossary-djangoimagetype`, `glossary-scalar-field-conversion`, `glossary-upload-scalar`) all resolve to existing `docs/GLOSSARY.md` headings.

### Documentation / release sanity

Full gate applied; all checks pass.

- **DB-backed byte-clean regenerate (the load-bearing check) — PASS.** Re-ran `uv run python scripts/build_kanban_md.py`, `build_kanban_html.py`, `build_glossary_md.py` from the repo root. The md5 of `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` is byte-identical to Worker 2's committed-working-tree snapshot taken before I regenerated, and a SECOND consecutive regenerate produced the identical md5 again — proving the rendered files match the DB and a regenerate is a no-op (no hand-edited drift, no un-synced DB body). `git diff --stat` of the three files was unchanged across the regenerate. `uv run python examples/fakeshop/manage.py import_spec_terms --check` → `OK: 37 done cards have glossary links.` `uv run python examples/fakeshop/manage.py check` → `System check identified no issues (0 silenced).` I left the working tree byte-identical to Worker 2's state (md5 confirmed; no temp files, no accidental drift).
- **Version strings / shipped statuses / card IDs.** All five version-quintet sites read `0.0.11` and agree; all four `TODO(spec-037 Slice 4)` source anchors cleared (`pyproject.toml`, `__init__.py`, `tests/base/test_init.py`, `uv.lock`); the Pillow dev-dep (Slice 1) is undisturbed in both `pyproject.toml` and `uv.lock`. The GLOSSARY package-version line, the three GLOSSARY entry statuses, the two Index rows, and the browse-by-category row all read `shipped (0.0.11)`.
- **KANBAN card move.** `TODO-ALPHA-037-0.0.11` is removed from `## In progress` and appears as `### [DONE-037-0.0.11 …]` in the Done section exactly once (`grep -c` = 1); zero `TODO-ALPHA-037` references remain in `KANBAN.md` or `KANBAN.html` (the `0.0.14` `TestClient` card's dependency/related refs all flipped to `DONE-037`). All four DoD items are `- [x]`. The `036`/`035` spec links stay at `docs/SPECS/…` (drift cluster #1 reconciled, NOT regressed to the broken non-`SPECS` path). The `037` card's `- Spec:` link points at the working-location `docs/spec-037-…md` (verified on disk; `036`/`035` verified archived at `docs/SPECS/`).
- **Glossary three terms + cross-surfaces.** `Upload` / `DjangoFileType` / `DjangoImageType` are `shipped (0.0.11)` in the entry bodies, the Index, the Public-exports list, and the "File / image uploads" browse-by-category row. The `Scalar field conversion` file/image row reflects read=object / filter-input=`str` / mutation-input=`Upload`; a file/image row was ADDED to `Specialized scalar conversions` (which had none) recording the breaking wire-format change. The `strawberry_config` "next: `Upload`" stray mention is removed (leaving only `BigInt`). All nine in-page anchors referenced by the new GLOSSARY prose resolve to existing headings.
- **README scope wording — correct.** Both `README.md` (Status line `0.0.10` → `0.0.11`) and `docs/README.md` ("Shipped today" `0.0.11`) describe the *scalar and generated mutation-field typing* as shipped and carry the canonical caveat "not full multipart HTTP upload ergonomics, which await the `0.0.14` `TestClient`". The `0.0.11` Upload item is removed from `docs/README.md`'s "Coming next" (retitled `0.0.12 → 0.0.14`); the `0.0.12`/`0.0.13`/`0.0.14` items are intact. `GOAL.md` criterion 6 notes the `Upload` + auto-generated-`Input` flavor ships `0.0.11` while `ModelForm`(`0.0.12`)/`ModelSerializer`(`0.0.13`) land later, with no multipart-TestClient implication. `TODAY.md`'s scalar-conversion file/image row is rewritten to the structured output objects with the three-way split, and a "not exercised by products" capability entry is added (deferred to `TODO-BETA-051-0.1.5`).
- **Markdown links.** Every reference-style link def introduced or moved (`CHANGELOG.md`, `docs/README.md`, `TODAY.md`) points at an existing GLOSSARY heading and lands under the correct `docs/` group header in the bottom block, alphabetical within the group. `uv run python scripts/check_spec_glossary.py --spec docs/spec-037-…md` → `OK: 20 terms`.
- **No obsolete wording** ("coming soon" / "planned" / old-version) remains in the deliberately-updated files: the three GLOSSARY entries flipped off `planned for 0.0.11`, the `strawberry_config` "next: Upload" is gone, and the README/docs-README/GOAL/TODAY version labels all read `0.0.11`.
- **Verbatim-copy spot-check.** GLOSSARY entry bodies are DB-`GlossaryTerm.body`-sourced and regenerate byte-identically from the committed file (proven by the two-pass byte-clean regenerate), so the committed prose and the DB are character-for-character in sync. No fenced-code-block drop-ins with conflicting backtick counts were introduced this slice.

### What looks solid

- The byte-clean regenerate is genuinely clean and stable across two passes — the highest-risk failure mode for a DB-backed doc slice (hand-edited drift / un-synced DB body) is absent. Worker 2's discovery that steps E6/E7/E8 (`scalar-field-conversion`, `specialized-scalar-conversions`, `strawberry_config`) are ALSO DB-backed `GlossaryTerm.body` rows — and the subsequent re-sync of all three after the first regenerate reverted the hand-edits — is exactly the trap the plan warned about, caught and resolved correctly.
- The three drift clusters (036 SpecDoc.url, `DjangoModelPermission` body, 037 card-body stale refs) were each reconciled UP toward the on-disk/committed reality rather than regressed — the durable fix, not a partial one.
- The version quintet is internally consistent and the Pillow dev-dep is untouched; the `uv lock` regenerate left every other lock entry undisturbed.
- The CHANGELOG, README, GOAL, and TODAY edits hold the read=object / filter-input=`str` / mutation-input=`Upload` split and the multipart caveat consistently, with no overstatement of multipart transport.

### Temp test verification

- No temp tests created. This slice ships no package logic (only the `test_version` literal bump), so behavior verification reduces to the focused `tests/base/test_init.py` run (5 passed) and the DB regenerate/management-command gate, both run above. Disposition: none needed.

### Notes for Worker 1 (spec reconciliation)

Worker 2 escalated three flags; my assessment of each:

- **Escalated (judgment call, not a defect) — drift cluster #3, the 037 card-body `034`→`036` / "Pairs with 028"→`036` fix vs the spec's Risks "surface, don't reconcile" framing.** The spec's Risks (lines 1593-1599, 1606-1612) recorded "Pairs with 028" and the stale-`034` as conflicts with a *preferred reading*, explicitly NOT reconciled at spec-authoring time, per the NEXT.md "prefer the card, surface the conflict" rule. Worker 2 fixed both in `CardItem.text` per the plan's RECOMMENDED both-or-neither path. My read: this is **acceptable** and Worker 1 should ratify it. The edits are DB `CardItem.text` values (not spec-file edits), single-surface with no divergent un-editable mirror, and the genuine pairing (`036`) is established by the spec's own predecessor analysis + Decision 6; Slice 4's `## Doc updates` card-wrap (worker-0.md procedure step 6) authorizes fixing card-body content the wrap names. The "surface, don't reconcile" framing governs spec-authoring time, not the card-close wrap. If Worker 1 instead reads the Risks framing as binding at wrap time, the recorded fallback (revert all three `CardItem.text` edits, record-only) is a clean DB-only reversal that would require a regenerate. Either resolution keeps the slice acceptable; flagging for the final-verification decision.
- **Escalated (acceptable, mirrors precedent) — DONE-037 card-body `- Status:` renders "In progress".** Confirmed independently: `DONE-037` and `DONE-036` both render `Status: In progress` (`Card.planningState.label`), while `DONE-035` / `DONE-034` render `Status: Shipped`. This is a free-text field distinct from the workflow `status` FK (which correctly flipped to `done`, yielding the `DONE-037-0.0.11` id). Worker 2 followed the immediately-prior `DONE-036` precedent and the "leave unrelated card-body prose alone" rule. My read: **acceptable as-is** — flipping it unilaterally would diverge from the just-closed `DONE-036` and is not named by the spec's Slice 4 contract. If the maintainer wants freshly-closed cards to read "Shipped", that is a separate `planningState` pass that should also re-touch `DONE-036` for consistency. Not a blocker.
- **Acknowledged (no action) — term-body sync broader than the plan's F1 list.** Worker 2 synced three extra DB-backed bodies (`scalar-field-conversion`, `specialized-scalar-conversions`, `strawberry_config`) beyond the plan's named F1 set because steps E6/E7/E8 edit those same DB rows. This is plan-vs-reality completeness, not a spec gap; the byte-clean two-pass regenerate proves the sync is correct and complete. Worker 1 should expect these three extra `GlossaryTerm.body` edits in the `db.sqlite3` diff at final verification. No spec change needed.

### Review outcome

`review-accepted`. No High / Medium / Low findings. The two Medium-adjacent judgment calls (cluster #3 card-body fix; the `planningState` "In progress" render) are transparently escalated to Worker 1 for the final-verification ruling per the acceptance gate — neither blocks acceptance, and both have clean recorded resolution paths. Byte-clean two-pass regenerate verified; working tree left byte-identical to Worker 2's state. No re-pass needed.

---

## Final verification (Worker 1)

Status set to **`revision-needed`**. One silently-unaddressed Slice-4 deliverable
blocks `final-accepted`: the pre-placed `TODO(spec-037 Slice 4)` summary anchor in
`docs/TREE.md` was never discharged. Everything else verified clean — the version
quintet, the byte-clean DB regenerate, the three glossary promotions, the README /
docs/README / GOAL / TODAY / CHANGELOG edits, and the three drift-cluster
reconciliations all hold. The single fix is a `docs/TREE.md` summary update + anchor
removal (a doc edit Worker 1 cannot make — routed to Worker 2).

### 1. Spec slice checklist audit (verbatim boxes)

The Plan's `### Spec slice checklist (verbatim)` carries two `- [x]` boxes (the
Slice 4 parent + its two sub-bullets — "Version files to `0.0.11`" and the combined
GLOSSARY/README/docs-README/GOAL/TODAY/CHANGELOG/KANBAN doc bullet). Audited each
against the diff:

- **`- [x]` Version files to `0.0.11`** — LANDED, box stays ticked. Verified all five
  quintet sites read the single canonical literal `0.0.11` and agree: `pyproject.toml:4`
  `version = "0.0.11"`, `django_strawberry_framework/__init__.py:36` `__version__ = "0.0.11"`,
  `tests/base/test_init.py:19` `assert __version__ == "0.0.11"`, `docs/GLOSSARY.md:20`
  `Current package version: \`0.0.11\``, `uv.lock:218` `version = "0.0.11"` (the
  `django-strawberry-framework` package entry). Pillow dev-dep undisturbed
  (`pyproject.toml:43` `"pillow>=10.0.0"` present; `uv.lock` Pillow block intact).
  All four source-site `TODO(spec-037 Slice 4)` anchors on these files cleared.
  Focused gate `tests/base/test_init.py --no-cov` = 5 passed.
- **`- [x]` GLOSSARY + READMEs + GOAL + TODAY + CHANGELOG + KANBAN doc bullet** —
  LANDED for every surface the **verbatim box names**, box stays ticked. The box's
  text enumerates GLOSSARY (3 promotions, Scalar-field-conversion rewrite, new
  Specialized-scalar row, Public exports + Index + Browse-by-category, breaking-wire
  note, `strawberry_config` "next: Upload" removal), `docs/README.md` / `README.md`
  (Coming-next → Shipped, Status `0.0.10`→`0.0.11`, multipart caveat), `GOAL.md`
  (criterion 6), `TODAY.md` (file/image row), `CHANGELOG.md` (maintainer-authorized),
  and `KANBAN.md` (card → Done via DB). Each verified present and accurate (see §4).
  **`docs/TREE.md` is NOT named in this verbatim box** (nor anywhere in the spec's
  `## Doc updates` list as authored), so the missed TREE work does not falsify this
  tick — it is a separate spec-vs-build gap recorded in §6 and routed via the spec
  edit + `revision-needed`.

No box was over-ticked (every ticked contract landed) and no box was silently left
un-ticked. The `revision-needed` is driven by the TREE.md anchor (§6), not by a
verbatim-checklist box.

### 2. Version-cut consistency (Decision 10)

CONFIRMED. `pyproject` version, `__init__` `__version__`, `test_version`, the GLOSSARY
package-version line, the `uv.lock` package-version, and (bonus surface) the CHANGELOG
`## [0.0.11] - 2026-06-19` heading all read `0.0.11` and agree. Zero `Unreleased`
remains in CHANGELOG. All four source-site `TODO(spec-037 Slice 4)` anchors on the
quintet files cleared (`grep` over `pyproject.toml` / `__init__.py` / `test_init.py` /
`uv.lock` returns nothing). Pillow dev-dep undisturbed in both `pyproject.toml` and
`uv.lock`. **NOTE — a fifth `TODO(spec-037 Slice 4)` anchor survives in `docs/TREE.md`
(NOT a version-quintet file)** — see §6.

### 3. DB-backed byte-clean re-verify

PASS, working tree left byte-identical to its current state.

- Snapshotted md5 of `docs/GLOSSARY.md` / `KANBAN.md` / `KANBAN.html`, then ran the
  three `scripts/build_*.py` regenerates TWICE. Both regenerate passes produced
  **byte-identical** md5s to the pre-regenerate snapshot (`bda14dd3…` / `4e9c00f8…` /
  `d5974578…` unchanged across all three states) — a second regenerate is a no-op, so
  the rendered docs match the DB (no hand-edited drift, no un-synced DB body).
- `git diff --stat` of the three generated files after regenerate equals the cumulative
  HEAD diff (the Slice-4 changes vs the committed-at-HEAD baseline) and did **not move**
  from the current working-tree state.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` → `OK: 37 done
  cards have glossary links.`
- `uv run python examples/fakeshop/manage.py check` → `System check identified no
  issues (0 silenced).`
- Confirmed `spec-035` / `spec-036` are archived on disk at `docs/SPECS/` (NOT at
  `docs/` working location), so cluster #1's DB reconciliation to the `docs/SPECS/`
  path renders correctly; `spec-037` is at its `docs/` working location and its KANBAN
  `- Spec:` link points there (correct — archive sweep is the next author's job).

### 4. DRY / consistency across the build

CONFIRMED. The canonical `0.0.11` literal is identical across all six sites (no
`v0.0.11` / `.dev` drift). The read=object / filter-input=`str` / mutation-input=`Upload`
three-way-split sentence and the `PositiveBigIntegerField → BigInt` `0.0.6`
breaking-change precedent phrasing are reused consistently (GLOSSARY `Scalar field
conversion` line, GLOSSARY `Specialized scalar conversions` new row, GLOSSARY
`DjangoFileType` / `DjangoImageType` bodies, CHANGELOG `### Changed`, `TODAY.md` row),
each anchored to the same opt-out (`attachment: str`). CHANGELOG uses only the
spec-authorized `### Added` / `### Changed` headings for the `037` bullets; the `036`
bullets stay in-section (same `0.0.11` release); the breaking-change bullet does not
overstate (it keeps filter/scalar-input `str` and does not claim multipart transport).
Verbatim glossary bodies are DB-`GlossaryTerm.body`-sourced and regenerate
byte-identically, so the committed prose and the DB are character-for-character in sync.

### 5. Escalated-item resolutions

- **Worker 2 flag (1) — term-body sync broader than the plan's F1 list (3 extra
  conversion-section bodies: `scalar-field-conversion`, `specialized-scalar-conversions`,
  `strawberry_config`).** ACCEPTED. These three are DB-backed `GlossaryTerm.body` rows
  that steps E6/E7/E8 edit; syncing them to the DB is the correct completeness move and
  is proven by the two-pass byte-clean regenerate (a missed sync would surface as a
  non-empty second-regenerate diff, which did not occur). Not a spec gap; no spec edit.
- **Worker 2 flag (2) / Worker 3 call (2) — DONE-037 card body renders
  `Status: In progress` (`Card.planningState`, free-text, distinct from the workflow
  `status` FK which correctly flipped to `done`).** ACCEPTED as precedent-consistent;
  NOT a defect. Independently confirmed via the rendered KANBAN: `DONE-037` and
  `DONE-036` (the immediately-prior closed card) both render `Status: In progress`;
  `DONE-035` / `DONE-034` render `Status: Shipped`. The two most-recently-closed cards
  share the "In progress" `planningState`; flipping 037 alone would diverge from the
  just-closed 036, and `planningState` is not named by the spec's Slice 4 contract or
  the worker-0 close procedure (the procedure flips the workflow `status` FK, which is
  correct here, and says "leave unrelated card-body prose alone"). `planningState`
  accuracy for a freshly-shipped card is a real-but-minor inconsistency, not a card-close
  defect — if the maintainer wants freshly-closed cards to read "Shipped", that is a
  separate `planningState` pass that should also re-touch `DONE-036` for consistency.
  Recorded as a maintainer follow-up; does **not** trigger `revision-needed`.
- **Worker 2 flag (3) / Worker 3 call (1) — the `037` card-body `034`→`036` and
  "Pairs with 028"→`036` reconciliation vs the spec Risks "surface, don't reconcile"
  framing.** ACCEPTED — the applied both-or-neither fix is correct for the card-close
  wrap; ratified, NOT reverted. Reasoning: (a) the spec's Risks "surface, don't
  reconcile" framing governs **spec-authoring time** (the NEXT.md "prefer the card,
  surface the conflict" rule applied when the spec was drafted), not the card-close
  wrap; (b) Slice 4's `## Doc updates` "card wrap" plus worker-0.md procedure step 6
  explicitly authorize fixing card-body content the wrap names; (c) these are
  single-surface `CardItem.text` values with no un-editable divergent mirror (the spec
  and source already name `036`/`037` correctly), so the worker-0.md "do not partial-fix
  a multi-surface reference" rule is satisfied by fixing them uniformly — leaving them
  stale would be the divergence; (d) the genuine pairing (`036`, the mutations card
  whose seam this card fills) is established by the spec's own predecessor analysis +
  Decision 6; `034` = permissions and `028` = ordering are unrelated. Verified the
  rendered KANBAN now carries zero `TODO-ALPHA-034` / "Pairs with 028" tokens in the 037
  body and DoD order=1 reads `DONE-036-0.0.11`. The both-or-neither discipline held
  (both fixed). No spec edit needed for this item.

### 6. Spec reconciliation + the blocking finding

**BLOCKING (silently-unaddressed Slice-4 deliverable) — `docs/TREE.md` `TODO(spec-037
Slice 4)` summary anchor undischarged.** `docs/TREE.md:205-211` carries a pre-placed
`<!-- TODO(spec-037 Slice 4): update tree summaries after Upload/file-image mapping
lands. … -->` anchor with a concrete pseudo-code work list (update the `scalars.py`
summary for the Upload re-export, the `types/converters.py` summary for `DjangoFileType`
/ `DjangoImageType` / `FIELD_OUTPUT_TYPE_MAP`, the `types/resolvers.py` summary for
file-column parent resolvers, and the matching test summaries). The anchor was committed
by `0273c869 "037 - Add TODO comments"` — the same commit that pre-placed **every other**
`TODO(spec-037 Slice 4)` anchor across the version quintet and the standing docs. Worker 2
discharged all the others but **`docs/TREE.md` is unmodified vs HEAD** (the anchor is
still present and the summary lines still read the pre-upload text), and the slice
artifact / build report / review never mention TREE.md. `AGENTS.md` #"Design docs and
TODO anchors" mandates that shipped behavior "folds into docs/GLOSSARY.md / docs/TREE.md
/ KANBAN.md" and that the staged source-site anchor naming the slice is "removed in the
same change that ships the slice." This is an undischarged, Slice-4-named obligation; it
blocks `final-accepted`. The fix is a `docs/TREE.md` summary update + anchor removal,
which is a standing-doc edit Worker 1 may not make — so this routes to Worker 2 via
`revision-needed`. (`docs/TREE.md` is a flat hand-edited standing doc, NOT DB-generated,
so no regenerate is involved — Worker 2 edits the four summary lines and deletes the
seven-line anchor block.)

Root cause: the spec's `## Doc updates` list and the verbatim Slice 4 checklist box
**omitted `docs/TREE.md`** even though the build pre-placed a Slice-4 anchor for it. This
is a spec authoring gap, reconciled below.

**Spec edits made — see `### Spec changes made (Worker 1 only)`.**

### Final status: `revision-needed`

Re-loop scope is narrow and mechanical: Worker 0 dispatches Worker 2 to (1) rewrite the
`docs/TREE.md` `scalars.py` / `types/converters.py` / `types/resolvers.py` summary lines
(both the current-tree and the planned-tree occurrences if the planned-tree section also
carries them — Worker 2 confirms) plus the `test_scalars.py` / `test_converters.py` /
`test_resolvers.py` summaries, per the anchor's own pseudo-code list, and (2) delete the
`docs/TREE.md:205-211` `TODO(spec-037 Slice 4)` anchor block in the same change. No DB
edit, no regenerate, no version change, no test change. Then Worker 3 re-reviews the
TREE.md hunk and Worker 1 re-runs final verification. Everything else in this slice is
verified clean and need not be re-touched.

### Summary

Slice 4 ships the final-in-spec `0.0.11` close: it aligns the version quintet
(`pyproject` / `__init__` `__version__` / `test_version` / GLOSSARY package-version line
/ `uv.lock`) on `0.0.11`; promotes `Upload` scalar / `DjangoFileType` / `DjangoImageType`
to `shipped (0.0.11)` in the GLOSSARY (Index + Public exports + Browse-by-category +
entry bodies), rewrites the `Scalar field conversion` file/image line to the read=object
/ filter-input=`str` / mutation-input=`Upload` three-way split, adds a `Specialized
scalar conversions` row recording the read-side breaking wire-format change, and removes
the `strawberry_config` "next: Upload" mention; moves the `Upload` + generated
file/image mutation-field typing from "Coming next" to "Shipped today" in `README.md` /
`docs/README.md` (with the "not full multipart HTTP ergonomics — those await `0.0.14`
`TestClient`" caveat) and bumps the README Status line; updates `GOAL.md` criterion 6 and
the `TODAY.md` scalar-conversion table; adds the maintainer-authorized `[0.0.11]`
CHANGELOG section; and DB-closes the kanban card `todo → done` (rendered
`DONE-037-0.0.11`, DoD all ticked, SpecDoc created at the `docs/` working location,
full glossary-link set synced via `import_spec_terms`). Three pre-existing DB drift
clusters were reconciled UP toward on-disk/committed reality (036 SpecDoc.url →
`docs/SPECS/`; `djangomodelpermission` body synced up; 037 card-body `034`/`028` stale
refs → `036`). The byte-clean two-pass regenerate, `import_spec_terms --check`, and
`manage.py check` all pass. **One deliverable was missed: the `docs/TREE.md` Slice-4
summary anchor is undischarged — the slice is `revision-needed` until Worker 2 updates the
TREE summaries and removes the anchor.**

### Spec changes made (Worker 1 only)

- `docs/spec-037-upload_file_image_mapping-0_0_11.md` line ~38-40 (status header):
  reflected reality per the per-spawn status-line rule — "Slices 1–3 final-accepted,
  Slice 4 pending" → "Slices 1–3 final-accepted, Slice 4 under review —
  `revision-needed`: the pre-placed `docs/TREE.md` `TODO(spec-037 Slice 4)` summary
  anchor is still undischarged; see the Slice 4 build artifact." Reason: the prior header
  described Slice 4 as merely "pending"; final verification found it under review and
  blocked on the TREE.md anchor.
- `docs/spec-037-upload_file_image_mapping-0_0_11.md` `## Doc updates` Slice 4 "package
  docs" bullet (~line 1511-1516): added `docs/TREE.md` to the authoritative Slice 4
  doc-update list, naming the `scalars.py` / `types/converters.py` / `types/resolvers.py`
  (+ matching test) summary updates and the discharge of the pre-placed
  `TODO(spec-037 Slice 4)` source-site anchor, citing the `AGENTS.md` "folds shipped
  behavior into docs/TREE.md" rule. Reason: the spec's authored `## Doc updates` list and
  verbatim Slice 4 checklist omitted `docs/TREE.md` even though the build pre-placed a
  Slice-4 anchor for it — the omission is the root cause of the missed deliverable; this
  edit closes the spec-vs-build gap so the re-loop dispatch and Worker 2 see the
  obligation explicitly.
- `scripts/check_spec_glossary.py --spec docs/spec-037-upload_file_image_mapping-0_0_11.md`
  re-run after both edits → exit 0 ("OK: 20 terms").

## Build report (Worker 2, pass 2)

Apply-changes pass discharging the one undischarged Slice-4 deliverable Worker 1's
final verification (§6) flagged: the pre-placed `docs/TREE.md` `TODO(spec-037 Slice 4)`
summary anchor. Updated the affected module/test summary lines per the anchor's own
pseudo-code work list and deleted the anchor block in the same change. No source, no
DB, no regenerate, no version/test change.

### Files touched
- `docs/TREE.md` — updated summary lines for the modules this card changed and
  deleted the staged `TODO(spec-037 Slice 4)` anchor block (lines 205-211):
  - `scalars.py` (current-tree) — now notes it also re-exports Strawberry's built-in
    `Upload`, with `strawberry_config()` staying `BigInt`-only (`Upload` needs no
    `_PACKAGE_SCALAR_MAP` entry).
  - `types/converters.py` (current-tree + target-tree, 2 occurrences) — now names the
    `DjangoFileType` / `DjangoImageType` read-output objects, the `_safe_file_attr`
    guard, the `FIELD_OUTPUT_TYPE_MAP` read-output map, and `convert_field_output`
    (filter-input `SCALAR_MAP` stays `str`).
  - `types/resolvers.py` (current-tree + target-tree, 2 occurrences) — now notes the
    file-column resolvers (`_attach_file_resolvers`) for columns resolving via
    `FIELD_OUTPUT_TYPE_MAP`.
  - `tests/test_scalars.py` (current-tree + target-tree, 2 occurrences) — now names the
    re-exported `Upload` scalar coverage.
  - `tests/types/test_converters.py` (current-tree + target-tree, 2 occurrences) — now
    names the file/image read-output conversion coverage.
  - `tests/types/test_resolvers.py` (current-tree + target-tree, 2 occurrences) — now
    names the file/image output-resolver coverage.

  No new cross-file links were added (summary-text edits only), so the `<!-- LINK
  DEFINITIONS -->` block is unchanged. `docs/TREE.md` is a flat hand-edited standing
  doc, NOT DB-generated — no regenerate involved.

### Validation run
- `uv run ruff format .` → 287 files left unchanged (the COM812-vs-formatter warning is
  the pre-existing repo config, not a change). `uv run ruff check --fix .` → All checks
  passed. (Neither touches `.md`; run per AGENTS.md protocol.)
- `git status --short`: the only file this pass changed is `docs/TREE.md` (` M`). All
  other dirty entries (version files, `CHANGELOG.md` / `GOAL.md` / `TODAY.md` /
  `README.md` / `docs/README.md`, the generated `KANBAN.*` / `docs/GLOSSARY.md`,
  `examples/fakeshop/db.sqlite3`, the spec, source, and tests) are accepted prior-pass
  work, untouched here.
- Protected-file byte-stability confirmed: `md5` of `docs/GLOSSARY.md` = `bda14dd3…`,
  `KANBAN.md` = `4e9c00f8…`, `KANBAN.html` = `d597457880…` — all match Worker 1's §3
  recorded md5 prefixes exactly, so they are byte-unchanged by this pass.
  `examples/fakeshop/db.sqlite3` size unchanged (3391488 → 3391488); no DB/regenerate
  command was run.

### Checklist ticks
None added; none removed. Worker 1's §1 audit ruled `docs/TREE.md` is NOT named by
either `### Spec slice checklist (verbatim)` box (both already correctly `- [x]`; the
`revision-needed` was driven by the §6 anchor finding, not a verbatim box). The TREE.md
obligation lives only in the spec's `## Doc updates` list (which Worker 1 amended), not
in a verbatim sub-check box — so there is no box to tick for this pass. Existing ticks
left as-is.

### Implementation notes
Summary phrasing follows the file's existing sibling-entry style (semicolon-extended
descriptions, double-backtick symbol quoting, `#`-comment column preserved) rather than
adding a new `mutations/inputs.py` line — `mutations/` appears in TREE.md only as a bare
`planned by TODO-ALPHA-036-0.0.11` directory entry with no per-file summary to update,
and the anchor's pseudo-code list does not name it; the `Upload` write-side mapping is
captured via the `scalars.py` re-export summary.

## Review (Worker 3, pass 2)

Narrow re-review of the single file Worker 2's pass-2 change touched: `docs/TREE.md`.
Did NOT re-litigate already-accepted Slice-4 content (version cut, DB card-close,
GLOSSARY/README/GOAL/TODAY/CHANGELOG). Verified the TREE.md fix landed cleanly and
introduced no regression or collateral drift. `git diff -- docs/TREE.md` reviewed in full.

### High:

None.

### Medium:

None.

### Low:

None.

### Documentation / release sanity

The relevant gate for this TREE.md doc edit. All checks pass.

- **Anchor gone — PASS.** `grep "spec-037 Slice 4" docs/TREE.md` returns nothing; the
  seven-line `<!-- TODO(spec-037 Slice 4) … -->` block at the old `docs/TREE.md:205-211`
  is deleted (confirmed against `git show HEAD:docs/TREE.md`, which still carried it).
  The only `TODO` tokens left in TREE.md are the legitimate `planned by TODO-ALPHA-…` /
  `TODO-BETA-…` target-layout directory annotations (unrelated to the discharged anchor).
- **Summaries accurate to what shipped (Slices 1–3), no overstatement — PASS.** Traced
  every named symbol to source: `scalars.py` re-exports Strawberry's built-in `Upload`
  (`from strawberry.file_uploads.scalars import Upload`, `__all__` includes `Upload`) and
  `strawberry_config()` stays `BigInt`-only (`Upload` is NOT in `_PACKAGE_SCALAR_MAP`) —
  matches the summary verbatim. `types/converters.py` defines `class DjangoFileType`
  (line 101), `class DjangoImageType(DjangoFileType)` (142), `def _safe_file_attr` (75),
  `FIELD_OUTPUT_TYPE_MAP` (206), `def convert_field_output` (412) — all present;
  filter-input `SCALAR_MAP` parenthetical is correct. `types/resolvers.py` defines
  `def _attach_file_resolvers` (461) keyed on `FIELD_OUTPUT_TYPE_MAP` (473) — accurate.
  Test summaries verified against the files: `test_scalars.py` has the `Upload`
  re-export / default-registry tests (440-453); `test_converters.py` imports and exercises
  `convert_field_output` / `FIELD_OUTPUT_TYPE_MAP` / `DjangoFileType` / `DjangoImageType`
  (1683-1699); `test_resolvers.py` has the populated `name/path/size/url + width/height`
  read (1072) and `test_empty_file_resolves_parent_object_to_null` parent guard (1105) —
  the "subfield reads and the empty-file parent-null guard" phrasing is exact.
  **No overstatement:** the write side is described only as the `Upload` re-export +
  `strawberry_config` `BigInt`-only contrast; nothing in TREE.md claims multipart HTTP
  upload ergonomics (the `0.0.14` `TestClient`). No stale / "planned" / old-version
  wording was introduced.
- **Format / style match — PASS.** The four updated module summaries and six test
  summaries follow the existing sibling-entry conventions: semicolon-extended descriptions,
  double-backtick symbol quoting (` ``Upload`` `), and the aligned `#`-comment column
  preserved. The current-tree and target-tree occurrences (and the test-shape mirror) are
  updated consistently (the same edit applied to all parallel occurrences), so the two
  rendered trees stay in lockstep. No invented new format.
- **Links resolve — PASS.** These are summary-text-only edits; no new cross-file
  reference-style link was added, so the `<!-- LINK DEFINITIONS -->` bottom block is
  byte-unchanged (`git diff` shows no `+[…]:` line). No new link to validate; the
  pre-existing `[agents]` / `[readme]` defs are untouched. (The spec's `## Doc updates`
  Slice-4 bullet now names `docs/TREE.md` via the `[tree]: TREE.md` ref def at spec line
  1785 — Worker 1's reconciliation, not part of this TREE.md pass.)

### What looks solid

- The discharge is exactly the §6 directive: the four module/test summary lines updated
  per the anchor's own pseudo-code list and the anchor block deleted in the same change,
  with no scope creep. The `mutations/inputs.py` non-edit is correctly reasoned — TREE.md
  carries `mutations/` only as a bare `planned by TODO-ALPHA-036` directory with no
  per-file summary, and the write-side mapping is surfaced via the `scalars.py` summary.
- The summary symbols are character-for-character faithful to source (no paraphrase that
  drifts), and the `(filter-input ``SCALAR_MAP`` stays ``str``)` / `BigInt`-only
  parentheticals correctly preserve the read-output-vs-filter-input split this card's
  whole design rests on.

### Temp test verification

None needed. This is a flat hand-edited standing-doc summary edit (no package logic, no
test, no DB, no regenerate); behavior verification reduces to tracing the named symbols to
source, done above.

### Notes for Worker 1 (spec reconciliation)

None new. The TREE.md obligation Worker 1 reconciled in §6 / the spec's `## Doc updates`
list is now discharged. No further spec edit is implied by this pass. The two prior
escalated judgment calls (037 card-body `034`/`028` → `036` fix; DONE-037 `planningState`
"In progress" render) were already RATIFIED in Worker 1's §5 final verification and are
untouched by this TREE.md-only pass — no re-escalation.

### No-collateral-drift confirmation

This pass touched ONLY `docs/TREE.md`. Re-confirmed the protected files are byte-unchanged
from the prior-accept state: `md5 docs/GLOSSARY.md` = `bda14dd3…`, `KANBAN.md` =
`4e9c00f8…`, `KANBAN.html` = `d5974578…` — all match Worker 1's §3 / Worker 2's pass-2
recorded prefixes exactly. `examples/fakeshop/db.sqlite3` size unchanged (3391488) and no
DB / regenerate command was run. The version-quintet files (`pyproject.toml`,
`__init__.py`, `tests/base/test_init.py`, `uv.lock`) are unchanged by this pass. `git
status` shows `docs/TREE.md` as the sole file modified beyond the accepted prior-pass set.

### Review outcome

`review-accepted`. The undischarged `docs/TREE.md` anchor is gone, the four module + six
test summaries are accurate to what shipped (Slices 1–3) with no overstatement of the
write side, the phrasing matches sibling-entry style, no new link was introduced, and no
collateral file drifted (GLOSSARY / KANBAN.* / db.sqlite3 / version files all byte-unchanged).
No High / Medium / Low findings. No re-pass needed; routes to Worker 1 for final re-verification.

## Final verification (Worker 1, pass 2)

Status set to **`final-accepted`**. The single `revision-needed` directive from my
prior `## Final verification (Worker 1)` §6 — discharge the undischarged
`docs/TREE.md` `TODO(spec-037 Slice 4)` summary anchor — was applied exactly by
Worker 2 (pass 2) and re-accepted by Worker 3 (pass 2). I re-confirmed the fix, the
full Slice 4 contract, the DB-backed byte-clean state, and reconciled the spec
header. Slice 4 — the LAST in-spec slice — is closed; **all four slices are
final-accepted**. The cross-slice integration pass + final gate (Worker 1) still
follow.

### 1. Directive applied exactly — CONFIRMED

`git diff -- docs/TREE.md` is the ONLY working-tree change since my prior pass
(verified by `git status --short`: `docs/TREE.md` is the sole file modified beyond
the accepted prior-pass set; the version-quintet files, generated docs, source,
tests, and `db.sqlite3` are untouched this pass).

- **Anchor gone.** `grep "spec-037 Slice 4" docs/TREE.md` returns nothing (exit 1).
  The seven-line `<!-- TODO(spec-037 Slice 4): update tree summaries … -->` block at
  the old `docs/TREE.md:205-211` is deleted (the diff shows the seven `-` lines
  removed, replaced by a single updated `scalars.py` summary). The only `TODO`
  tokens remaining in `docs/TREE.md` are the legitimate `planned by TODO-ALPHA-…` /
  `TODO-BETA-…` target-layout directory annotations — unrelated to the discharged
  anchor.
- **Summaries accurate to what shipped (Slices 1–3), no overstatement.** The diff
  updates exactly the lines the anchor's pseudo-code named, in both the current-tree
  and target-tree occurrences (kept in lockstep): `scalars.py` (re-exports
  Strawberry's built-in `Upload`; `strawberry_config()` stays `BigInt`-only —
  `Upload` needs no `_PACKAGE_SCALAR_MAP` entry); `types/converters.py` (names
  `DjangoFileType` / `DjangoImageType`, `_safe_file_attr`, `FIELD_OUTPUT_TYPE_MAP`,
  `convert_field_output`, with the `filter-input SCALAR_MAP stays str` parenthetical
  preserving the read-output-vs-filter-input split); `types/resolvers.py` (notes the
  file-column `_attach_file_resolvers` keyed on `FIELD_OUTPUT_TYPE_MAP`); and the
  three test summaries (`test_scalars.py` Upload re-export coverage,
  `test_converters.py` file/image read-output conversion, `test_resolvers.py`
  file/image output resolvers + empty-file parent-null guard). **No overstatement:**
  the write side is described only as the `Upload` re-export + `strawberry_config`
  `BigInt`-only contrast — nothing claims full multipart HTTP upload ergonomics (the
  `0.0.14` `TestClient`); no stale / "planned" / old-version wording was introduced.
  The `mutations/inputs.py` non-edit is correctly reasoned (TREE.md carries
  `mutations/` only as a bare `planned by TODO-ALPHA-036` directory with no per-file
  summary; the write-side mapping is surfaced via the `scalars.py` summary).
- **Format matches the file's existing style** (semicolon-extended descriptions,
  double-backtick symbol quoting, aligned `#`-comment column). Summary-text-only
  edits — no new cross-file reference-style link added, so the `<!-- LINK
  DEFINITIONS -->` block is byte-unchanged. **No other file changed in this pass.**

### 2. Full Slice 4 contract re-confirmed — HOLDS

- **Verbatim sub-checks.** Both `### Spec slice checklist (verbatim)` `- [x]` boxes
  ("Version files to `0.0.11`" + the combined GLOSSARY/README/docs-README/GOAL/TODAY/
  CHANGELOG/KANBAN doc bullet) remain ticked and landed (re-audited in pass 1 §1; no
  box was added, removed, or re-litigated in pass 2 — `docs/TREE.md` lives in the
  spec's `## Doc updates` list, not a verbatim box, so there is no box to tick for
  the fix).
- **Version quintet — all `0.0.11`, agree.** `pyproject.toml:4` `version = "0.0.11"`,
  `django_strawberry_framework/__init__.py:36` `__version__ = "0.0.11"`,
  `tests/base/test_init.py:19` `assert __version__ == "0.0.11"`,
  `docs/GLOSSARY.md:20` `Current package version: \`0.0.11\``, `uv.lock:218`
  `version = "0.0.11"` (the `django-strawberry-framework` package entry). Pillow
  undisturbed (`pyproject.toml:43` `"pillow>=10.0.0"`; `uv.lock` Pillow block intact,
  `pillow 12.2.0`). No `TODO(spec-037 Slice 4)` anchor survives anywhere outside the
  builder artifacts and the spec's own descriptive prose (the spec header reference +
  the `## Doc updates` "discharging the pre-placed … anchor" mention — both correct
  prose, not undischarged anchors).
- **`## Doc updates` Slice 4 surfaces all present:** GLOSSARY — `Upload` scalar /
  `DjangoFileType` / `DjangoImageType` bodies all `**Status:** shipped (\`0.0.11\`)`,
  Index rows all `shipped (\`0.0.11\`)`, Public-exports list carries all three
  symbols, Browse-by-category "File / image uploads" row lists all three,
  Specialized-scalar-conversions file/image breaking-wire-format row present
  (anchored to the `PositiveBigIntegerField → BigInt` `0.0.6` precedent, filter/
  scalar-input stays `str`, mutation input is `Upload`), `strawberry_config` "next:
  `Upload`" mention removed. README — Status line `0.0.11`, "Newest shipped surface"
  names the `Upload` scalar + generated file/image mutation-input typing + structured
  read output WITH the "not full multipart HTTP upload ergonomics, which await the
  `0.0.14` `TestClient`" caveat. docs/README — "Shipped today (`0.0.11`)" present.
  GOAL criterion 6 — the `Upload` / file/image part scoped to generated
  `DjangoMutation` inputs in `0.0.11`, ModelForm (`0.0.12`) / ModelSerializer
  (`0.0.13`) flavors later. TODAY — scalar-conversion row rewritten to the structured
  output objects + the not-exercised-by-products note. CHANGELOG — `## [0.0.11] -
  2026-06-19` present, no `Unreleased`. KANBAN — `DONE-037-0.0.11` in the Done
  section. And `docs/TREE.md` (this pass's fix) — discharged.

### 3. DB-backed byte-clean re-verify (final) — PASS, tree left byte-identical

- Snapshotted md5 of the three generated files, ran the three `scripts/build_*.py`
  TWICE. Byte-identical across all three states (pre-regenerate, pass 1, pass 2):
  `docs/GLOSSARY.md` = `bda14dd38234e25641575043b67d43dd`, `KANBAN.md` =
  `4e9c00f81f1a7ad89647cd5d5f6e9f78`, `KANBAN.html` = `d597457880b048e257f3d97057871a4c`
  — matching my prior §3 recorded prefixes and Worker 2/3 pass-2 prefixes exactly. A
  second regenerate is a no-op → the rendered docs match the DB (no hand-edit drift,
  no un-synced body). `git diff --stat` of the three files after regenerate equals the
  cumulative HEAD diff and did **not move** from the current working-tree state.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` → `OK: 37 done
  cards have glossary links.`
- `uv run python examples/fakeshop/manage.py check` → `System check identified no
  issues (0 silenced).`
- `examples/fakeshop/db.sqlite3` size unchanged (3391488 → 3391488); no DB / regenerate
  command mutated the DB. `docs/TREE.md` anchor still gone after the regenerate
  (TREE.md is not DB-generated; regenerate does not touch it). The tree is byte-identical
  to its pre-verification working state.

### 4. Escalated items — no change

The three judgment calls ruled in pass 1 §5 (the three extra `GlossaryTerm.body`
syncs ACCEPTED; the `DONE-037` `planningState` "In progress" render ACCEPTED as
precedent-consistent / maintainer follow-up; the `037` card-body `034`→`036` /
"Pairs 028"→`036` reconciliation RATIFIED) are untouched by this TREE.md-only pass and
stand. Worker 3 (pass 2) re-confirmed no re-escalation. Nothing new surfaced.

### Final status: `final-accepted`

The directive landed exactly, the full Slice 4 contract holds, and the DB-backed
byte-clean state is preserved. The artifact top-level `Status:` is set to
`final-accepted`. **Slice 4 is closed; all four in-spec slices are final-accepted.**
The cross-slice integration pass + final gate (Worker 1) follow.

### Summary

Slice 4 — the final in-spec slice — ships the `0.0.11` close with no package logic:
it aligns the version quintet (`pyproject` / `__init__` `__version__` / `test_version`
/ GLOSSARY package-version line / `uv.lock`) on `0.0.11`; promotes `Upload` scalar /
`DjangoFileType` / `DjangoImageType` to `shipped (0.0.11)` across the GLOSSARY (entry
bodies + Index + Public exports + Browse-by-category), rewrites the `Scalar field
conversion` file/image line to the read=object / filter-input=`str` /
mutation-input=`Upload` three-way split, adds a `Specialized scalar conversions` row
recording the read-side breaking wire-format change, and removes the
`strawberry_config` "next: Upload" mention; moves `Upload` + generated file/image
mutation-field typing from "Coming next" to "Shipped today" in `README.md` /
`docs/README.md` (with the "not full multipart HTTP ergonomics — those await the
`0.0.14` `TestClient`" caveat) and bumps the README Status line; updates `GOAL.md`
criterion 6 and the `TODAY.md` scalar-conversion table; adds the maintainer-authorized
`[0.0.11]` CHANGELOG section; DB-closes the kanban card `todo → done` (rendered
`DONE-037-0.0.11`, DoD ticked, SpecDoc at the `docs/` working location, full
glossary-link set synced); and — the pass-2 fix — discharges the `docs/TREE.md`
Slice-4 summary anchor (four module summaries + six test summaries updated to shipped
behavior, anchor block deleted). Three pre-existing DB drift clusters were reconciled
UP toward on-disk/committed reality (036 SpecDoc.url → `docs/SPECS/`;
`djangomodelpermission` body synced up; 037 card-body `034`/`028` → `036`). The pass-1
`revision-needed` (the undischarged `docs/TREE.md` anchor) is resolved: Worker 2
discharged it, Worker 3 re-accepted, and this pass-2 final verification confirms the
fix landed exactly, the full contract holds, and the byte-clean two-pass regenerate /
`import_spec_terms --check` / `manage.py check` all pass with the tree left
byte-identical. **Final status: `final-accepted`. All four slices complete.**

### Spec changes made (Worker 1 only)

- `docs/spec-037-upload_file_image_mapping-0_0_11.md` lines 38-42 (status header):
  per the per-spawn status-line rule, replaced "Slices 1–3 final-accepted, Slice 4
  under review — `revision-needed`: the pre-placed `docs/TREE.md` `TODO(spec-037 Slice
  4)` summary anchor is still undischarged" with "**all four slices final-accepted**
  (the in-spec build is complete; the cross-slice integration pass + final gate still
  follow). The `docs/TREE.md` summary anchor that blocked Slice 4 was discharged
  (summaries updated, anchor removed); see the Slice 4 build artifact." Reason: the
  prior header recorded Slice 4 as blocked on the TREE.md anchor; this pass confirms
  the anchor is discharged and the in-spec build is complete, so the header now
  reflects all-four-slices-accepted reality. (The overall `Status: **IN PROGRESS**`
  prefix is intentionally retained — the cross-slice integration pass + final gate are
  not yet run, so the spec is not yet at its terminal state.)
- `scripts/check_spec_glossary.py --spec docs/spec-037-upload_file_image_mapping-0_0_11.md`
  re-run after the edit → exit 0 ("OK: 20 terms - all have glossary entries and at
  least one spec link.").
