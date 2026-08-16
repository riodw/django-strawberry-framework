# Build: Item R3 — the `DONE-011-0.0.4` card body

Spec reference: `docs/SPECS/spec-011-stale_placeholder_cleanup-0_0_4.md` `## Scope` (its closing
scalar-override paragraph) and the rationale companion's entry "`## Scope` 2 — the kept placeholder,
and a tense the spec outlived"
Plan reference: `docs/builder/build-011-stale_placeholder_cleanup-0_0_4.md` `### R3, added after R2`
Predecessor artifact: `docs/builder/bld-011-r2-doc_completion_archive_audit.md` (`final-accepted`) —
its `### Generated-doc edits reported, not made` is this item's input contract
Status: final-accepted

## Plan (Worker 1)

**Standing declarations.** Hot-path: **none** — this item writes three database rows of Markdown
prose and regenerates two rendered docs; no package source, no test, and no code path is in the
writable set. Floor-verification scope: **none** — no Django / Strawberry / channels integration seam
is touched (`docs/builder/BUILD.md` `## Floor verification` is the canonical floor statement and no
number from it is restated here; `### When it is required` names "KANBAN / glossary regeneration" as
an explicit `none` case). Failability proofs: **none owed, and none is to be invented** — this item
introduces no boundary, guard, gate, or rejection path, which is exactly the carve-out
`docs/builder/BUILD.md` `### What needs a proof, and what does not` draws ("doc edits … need none").
Write the heading with `None; this pass introduced no new boundary.` under it. Boundary count for the
`### Boundary count is a split trigger` question: **zero**, so the split question resolves to "do not
split" on both triggers — the diff is three DB rows and two generated files, and the three sub-checks
share one card and one transaction.

Never run `pytest` with a `--cov*` flag in this pass (`docs/builder/BUILD.md` `## Coverage is the
maintainer's gate, not a worker's tool`). No `pytest` run is called for at all; see
`### Test additions / updates`.

The ~123 baseline-dirty paths described in `docs/builder/build-011-stale_placeholder_cleanup-0_0_4.md`
`## Baseline-dirty out-of-scope files` are **never** edited, reverted, stashed, or `git checkout`ed
(`AGENTS.md` rule 34, `START.md` `## Concurrent sessions`). The list is moving; re-derive it, never
quote it.

### DRY analysis

- **Helper inventory checked.** Not applicable in the code sense, and the reason is recorded rather
  than left silent: this item lands no Python, no test, and no new symbol, so
  `worker-1.md` `### Package-wide helper inventory before helper planning` has no candidate surface
  to inventory. The documentary equivalent was run instead — `bld-011-r2-…md` was read in full as the
  contract it hands forward, together with the reconciled spec, its rationale companion, the kanban
  models (`examples/fakeshop/apps/kanban/models.py`), the signal layer
  (`examples/fakeshop/apps/kanban/signals.py`), the write API
  (`examples/fakeshop/apps/kanban/services.py`), and both exporters
  (`scripts/build_kanban_md.py`, `scripts/build_kanban_html.py`) — before any step below was written.
  The shapes searched for were the ones this item needs: how card-body prose is stored
  (`CardItem.text`), how a card-to-card edge stores its prose (`CardReference.raw_text`), how
  `{{card_ref:N}}` resolves, and which signals fire on a `CardItem` / `CardReference` write or delete.
- **Existing patterns reused.** The replacement sentence is not newly composed: it compresses the
  reconciled spec's own closing paragraph (`docs/SPECS/spec-011-stale_placeholder_cleanup-0_0_4.md`
  `## Scope`, final paragraph — "…is a separate concern from definition order … Card `DONE-019-0.0.6`
  owns it and ships it at `0.0.6`.") to board altitude, which is what keeps the board and the spec
  saying one thing rather than two. The card-id spelling reuses the board's own FK-backed
  `{{card_ref:0}}` placeholder idiom (`scripts/build_kanban_md.py::resolve_card_refs_for_card`) rather
  than a literal `DONE-019-0.0.6`, which would be a snapshot that drifts on the next card renumber.
  The write path reuses the sanctioned ORM shape, not raw SQL.
- **New helpers justified.** None. No script, no management command, no reusable snippet. The one-off
  ORM block in step 4 is transient and is not committed anywhere.
- **Duplication risk avoided.** The real duplication here is already in the database and is the
  subject of two of the three sub-checks: the `#### Scope` duplicate row (sub-check 2) and the
  deliberately denormalized `CardItem.text` / `CardReference.raw_text` pair (see the mechanism note
  below). The plan does not add a third copy — in particular it does **not** restate the retired
  placeholder's history on the board, because the spec and its rationale already carry it and a board
  copy would be the surface that drifts next.

#### Mechanism, verified against the models and the renderer before being asserted

The dispatch brief and `bld-011-r2-…md` `### Generated-doc edits reported, not made` both state that
"one field edit fixes both renderings" because the same `CardItem.text` re-renders under
`#### Card references`. **That is false, and the plan is built on the measurement instead.** Verified
at this working tree:

- `#### Scope` renders `CardItem.text` rows —
  `scripts/build_kanban_md.py::render_card` groups `card["items"]` by section and emits
  `resolve_card_refs_for_card(item["text"], card)`.
- `#### Card references` renders a **different column** — the same function emits
  `resolve_card_refs_for_card(reference.get("rawText", ""), card)` from `card["outgoingReferences"]`,
  i.e. `CardReference.raw_text`, then appends ` -> ` and the target card's key and title.
- The two columns hold **byte-identical copies today** because one card-spec import wrote both from a
  single source string: `examples/fakeshop/apps/kanban/services.py::create_card_from_spec` fans the
  spec dict out to `::_create_sections` (which appends the `scope` `CardItem`) and `::_create_references`
  (which appends the `related` `CardReference`). Denormalization by design, not one field read twice.
  **Corrected by Worker 1 at final verification** — this bullet originally attributed the pair to
  `services.py::add_dependency_note`, which cannot have written these rows: it resolves
  `DEPENDENCY_REFERENCE_KIND_KEY = "dependency"` and `DEPENDENCY_NOTE_SECTION_KEY = "dependencies_note"`,
  while the live rows are kind `related` and section `scope`. The conclusion the bullet supports — two
  columns, therefore two row edits — is unaffected and stands.

Read from a `sqlite3 -readonly` query against a **scratchpad copy** of `examples/fakeshop/db.sqlite3`
(no write, no `manage.py` invocation, per `bld-011-r2-…md`'s method):

| Row | Location | Current text |
|---|---|---|
| `kanban_carditem` id **614** | card 11, section `scope`, `order` **0** | ``Replaced stale M2M and forward-reference skips with definition-order tests.`` |
| `kanban_carditem` id **615** | card 11, section `scope`, `order` **1** | ``Kept the remaining scalar override skip documented as a separate scalar-field concern under `{{card_ref:0}}`.`` |
| `kanban_carditem` id **613** | card 11, section `scope`, `order` **2** | ``replace stale M2M / forward-reference skips with definition-order tests.`` |
| `kanban_cardreference` id **17** | source card 11 -> target card 19, kind `related`, `order` 0 | ``Kept the remaining scalar override skip documented as a separate scalar-field concern under `{{card_ref:0}}`.`` |

So sub-check 1 is **two** row edits, not one. Ids are given for orientation; every step below selects
by `(card number, section key, order)` and by edge FK, and asserts the current text before writing, so
a stale id cannot cause a wrong-row write.

#### Which row is which, for sub-check 2

Bullet 1 is `CardItem` id **614**, `order` **0** — the capitalized, past-tense, complete sentence.
Bullet 3 is `CardItem` id **613**, `order` **2** — the lowercase, imperative-mood restatement
(`"replace stale M2M / forward-reference skips with definition-order tests."`). **Delete `order` 2;
keep `order` 0.** Note that the lower row id (613) belongs to the *later*-rendered bullet: id order and
`order` order disagree here, which is precisely why the builder must select on `order` and assert on
text rather than trust the id. Rationale for the direction of the deletion: the rationale companion's
`### `## Other` — a heading that names a card section the board has retired` already dispositioned
this string as "a restatement of `## Scope` bullet 1" with no successor, and `order` 0 is the row the
reconciled spec's `## Scope` bullet 1 corresponds to.

**Delete rather than fold.** Folding would mean merging two sentences that say the same thing, which
produces a third wording nobody wrote; there is no content in `order` 2 that `order` 0 lacks. Deletion
is also constraint-safe: `CardItem`'s only relevant constraint is
`unique_item_position_per_card` on `(card, section, order)`
(`examples/fakeshop/apps/kanban/models.py::CardItem.Meta`), so removing `order` 2 leaves `0, 1`
contiguous and needs **no** re-ordering write on the survivors. No `pre_delete` / `post_delete`
receiver is registered for `CardItem`
(`examples/fakeshop/apps/kanban/signals.py` registers `pre_delete` only for `SpecDoc` and
`CardGlossaryTerm`, and `post_delete` only for `Card`), so the done-card protections cannot fire on
this delete, and the row's `UUIDModel` side row is removed by its own `on_delete=CASCADE` O2O link
rather than orphaned.

#### Sub-check 3 — decided: **not** planned in, and why

`#### Files likely touched` keeps its three rows. `tests/types/test_base.py` and
`tests/optimizer/test_extension.py` are **not** added. Recorded as a decided disposition, not an
oversight:

1. **R3's authorization is a falsified claim and a duplicate row.** An incomplete planning-time
   prediction is neither. `bld-011-r2-…md` graded it itself: "a board-fidelity question, not a
   correctness one, since 'likely touched' is a planning-time field."
2. **Back-filling a prediction field with post-hoc knowledge makes the board assert a prediction
   nobody made.** That is the same class of defect as the duplicate row — import residue presented as
   board fact — only running in the opposite direction, and this item exists to remove that class, not
   to add to it.
3. **The five-file set is already stated where it is checkable.** The reconciled spec's `## Scope`
   names all five by `path::QualifiedName`, and the card's `Spec:` row links straight to it. A board
   copy would be a second source for one fact, which is the shape that drifts next — the same argument
   the rationale companion used to delete `## Card snapshot`'s label list rather than patch it.
4. **Writes to a concurrently-written database are not free.** Two unnecessary `CardItem` rows on a
   shared `examples/fakeshop/db.sqlite3` is a cost with no correctness return.

If the maintainer prefers the opposite call, it is two `append_card_item`-shaped rows at `order` 3 and
4 in section `files_touched`, and nothing else changes.

### Implementation steps

Line numbers and row ids in this plan are pin-at-write-time navigational hints. Verify against the
current source and the current database before editing.

**Step 0 — concurrency gate, before anything else.** Worker 0 verified before dispatch that
`examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, and `docs/GLOSSARY.md` are all **clean at
`HEAD`**; this plan re-verified the same four at plan time and they were clean. Re-run it:

```shell
git status --porcelain -- examples/fakeshop/db.sqlite3 KANBAN.md KANBAN.html docs/GLOSSARY.md
```

Empty output is the only permitted result. **Any of the four dirty is a concurrent writer and a stop
condition**: report and stop. Do **not** revert, reset, stash, or `git checkout` the database or the
rendered docs under any circumstance (`START.md` `## Concurrent sessions`, `AGENTS.md` rule 34) — a
regenerate on top of another session's unlanded card edit publishes their half-landed surface, and a
DB reset destroys it outright.

**Step 1 — baseline regenerate-to-temp, before any DB edit.** This is what separates pre-existing
file drift from this item's own output; `git diff` alone cannot, because it shows the cumulative
difference from `HEAD` rather than what a regenerate would newly produce.

```shell
SCRATCH="$(mktemp -d)"
uv run python scripts/build_kanban_md.py --md "$SCRATCH/kanban-baseline.md"
diff KANBAN.md "$SCRATCH/kanban-baseline.md"
cp KANBAN.html "$SCRATCH/kanban-baseline.html"
uv run python scripts/build_kanban_html.py --html "$SCRATCH/kanban-baseline.html"
diff KANBAN.html "$SCRATCH/kanban-baseline.html"
```

Both diffs must be **empty**. A non-empty baseline diff means the committed DB already carries state
the rendered docs do not show — a regenerate would publish it along with this item's edit — and is a
**stop condition**: record the diff in the build report and stop. (`build_kanban_md.py --check` and
`build_kanban_html.py --check` are the boolean equivalents and may be run as corroboration; the
temp-diff is what the report records, because it also characterizes any drift found.)

**Step 2 — record the pre-edit hashes.** `shasum -a 256 KANBAN.md KANBAN.html`. Keep the two digests
for the step-6 comparison.

**Step 3 — read the three target rows from a read-only copy.** Never query the live file with a
writing tool:

```shell
cp examples/fakeshop/db.sqlite3 "$SCRATCH/db-r3.sqlite3"
sqlite3 -readonly "$SCRATCH/db-r3.sqlite3" \
  'select i.id, s.key, i."order", i.text from kanban_carditem i
     join kanban_section s on s.id = i.section_id
     join kanban_card c on c.id = i.card_id
    where c.number = 11 order by s."order", i."order";'
sqlite3 -readonly "$SCRATCH/db-r3.sqlite3" \
  'select r.id, r."order", r.raw_text from kanban_cardreference r
     join kanban_card c on c.id = r.source_card_id where c.number = 11;'
```

Confirm the four rows in the mechanism table above still read as stated. A mismatch is a stop
condition, not a cue to adapt the strings.

**Step 4 — the ORM write.** One `transaction.atomic` block through the Django ORM, from the repository
root. Never raw SQL: a raw write skips the `post_save` receiver that materializes the row's
`UUIDModel` side row (`examples/fakeshop/apps/kanban/signals.py`, `UUID_LINKED_MODELS` — `CardItem`
and `CardReference` are both in it), and the exporters fetch `uuid { id }` for both through the real
`/graphql/` route (`scripts/build_kanban_html.py::STATIC_KANBAN_QUERY`), so a missing side row breaks
the render. Plain `.save()` — not `update_fields` — so every pre_save/post_save receiver sees a
complete instance.

```shell
uv run python examples/fakeshop/manage.py shell <<'PY'
from django.db import transaction

from apps.kanban import models

OLD = (
    "Kept the remaining scalar override skip documented as a separate "
    "scalar-field concern under `{{card_ref:0}}`."
)
NEW_ITEM = (
    "Scalar field override semantics is a separate concern from definition order "
    "and is owned by `{{card_ref:0}}`, which ships it at `0.0.6`."
)
NEW_REF = (
    "Scalar field override semantics is a separate concern from definition order "
    "and ships at `0.0.6`."
)
DUPLICATE = "replace stale M2M / forward-reference skips with definition-order tests."

card = models.Card.objects.get(number=11)
item = models.CardItem.objects.get(card=card, section__key="scope", order=1)
duplicate = models.CardItem.objects.get(card=card, section__key="scope", order=2)
reference = models.CardReference.objects.get(
    source_card=card,
    target_card__number=19,
    kind__key="related",
)

assert item.text == OLD, repr(item.text)
assert reference.raw_text == OLD, repr(reference.raw_text)
assert duplicate.text == DUPLICATE, repr(duplicate.text)

with transaction.atomic():
    item.text = NEW_ITEM
    item.save()
    reference.raw_text = NEW_REF
    reference.save()
    duplicate.delete()

print("ok")
PY
```

Three assertions, then three writes. If any assertion raises, **nothing is written** (it raises before
the atomic block) — re-read step 3 and stop rather than loosening the assertion.

Why the two new strings differ. The `CardItem` text carries `{{card_ref:0}}` because `#### Scope`
renders standalone prose that must name its owner. The `CardReference` `raw_text` does not, because
`render_card` already appends `` -> `DONE-019-0.0.6` - Consumer override semantics (scalar fields) ``
to it; repeating the id inside the sentence would render the card key twice on one line. Dropping the
placeholder from `raw_text` is safe: `resolve_card_refs_for_card` indexes
`card["outgoingReferences"]` by `order`, the reference row itself is **kept** (only its prose
changes), and `{{card_ref:0}}` is still used by `CardItem` 615 and by the `#### Note` row, both of
which continue to resolve.

**Step 5 — regenerate both docs, from the repository root.**

```shell
uv run python scripts/build_kanban_md.py
uv run python scripts/build_kanban_html.py
```

**Step 6 — prove byte-stability with two consecutive regenerates.** A `git diff` shows the cumulative
difference from `HEAD`, never whether a second regenerate is stable, so hash across a repeat:

```shell
shasum -a 256 KANBAN.md KANBAN.html
uv run python scripts/build_kanban_md.py
uv run python scripts/build_kanban_html.py
shasum -a 256 KANBAN.md KANBAN.html
```

The two digest pairs must be **identical**. Record all four digests (plus step 2's pre-edit pair) in
the build report. A digest that moves between consecutive regenerates is a stop condition.

**Step 7 — leave `docs/GLOSSARY.md` alone and prove it.** This item owes that file nothing: R2 verified
both anchors carry the right shipped versions (`#definition-order-independence` shipped `0.0.4`,
`#scalar-field-override-semantics` shipped `0.0.6`, `docs/GLOSSARY.md:490` and `:1785`), and
`scripts/build_glossary_md.py` is **not** run in this pass. `git diff docs/GLOSSARY.md` must be
**empty**. A non-empty diff means DB body drift reached the glossary tables and is a **stop
condition** — report, do not revert.

**Step 8 — the writable set is exactly four paths.** `examples/fakeshop/db.sqlite3`, `KANBAN.md`,
`KANBAN.html`, and this artifact. Run `git status --short` after step 6 and confirm no fifth path
changed under your hand. Anything unexpected is a **stop-and-report**, never a revert — this tree
carries concurrent sessions' uncommitted work. Do not commit; do not stage; do not create or switch a
branch (`AGENTS.md` rules 32-34).

### Test additions / updates

**None, and none is possible.** This item lands no Python and no test; the change is three rows of
board prose and the two documents rendered from them. No `pytest` invocation is called for, and none
may carry a `--cov*` flag if one is run for another reason.

The verification this item owes is the command set below, run and recorded verbatim in the build
report. It is verification of a generated artifact, not test coverage, and must not be written up as
coverage.

- `git status --porcelain -- examples/fakeshop/db.sqlite3 KANBAN.md KANBAN.html docs/GLOSSARY.md`
  before the edit -> empty (step 0).
- Baseline regenerate-to-temp diffs for both docs -> both empty (step 1).
- Pre-edit and two post-edit `shasum -a 256 KANBAN.md KANBAN.html` readings; the two post-edit pairs
  identical (steps 2 and 6).
- `git diff docs/GLOSSARY.md` -> empty (step 7).
- `uv run python examples/fakeshop/manage.py check` -> passes (run it after step 5; it is the cheap
  proof the ORM write left no model/signal state the app cannot load).
- `uv run python scripts/check_trailing_commas.py --check KANBAN.md` -> exit 0. `KANBAN.md` is a
  tracked `.md` under the link-scaffold hook; the edit adds no link definition, so this should be a
  no-op, and a failure here means the render moved something the edit did not intend.
- **Read the rendered card end to end.** `grep -n 'stale_placeholder_cleanup' KANBAN.md`, then read
  the ~40 lines from the `<a id="stale_placeholder_cleanup"></a>` anchor to the next `<a id=`.
  Confirm `#### Scope` now carries exactly two bullets, that bullet 2 reads
  ``- Scalar field override semantics is a separate concern from definition order and is owned by `DONE-019-0.0.6`, which ships it at `0.0.6`.``,
  that the lowercase duplicate is gone, that `#### Files likely touched` still lists its three
  original paths, and that `#### Card references` reads
  ``- Related: Scalar field override semantics is a separate concern from definition order and ships at `0.0.6`. -> `DONE-019-0.0.6` - Consumer override semantics (scalar fields)``.
- **Confirm no other card's rendering moved.** `git diff -- KANBAN.md` must contain exactly one hunk,
  inside the `DONE-011-0.0.4` card block, net **-3 / +2** lines: bullet 2 replaced, bullet 3 deleted,
  the `#### Card references` line replaced. In particular the board's `{{last_refreshed}}` token must
  **not** move — `scripts/build_kanban_md.py::compute_tokens` derives it from `Card.updatedDate` and
  `BoardDoc.updatedDate` only, and this item saves neither a `Card` nor a `BoardDoc`, so a changed
  "last refreshed" line means something outside this edit's scope was written and is a stop condition.

**Two `KANBAN.html` diff expectations that are correct and must not be reported as drift.** The HTML
data block is the serialized GraphQL payload, which is wider than the Markdown render:

- **Timestamps move.** `STATIC_KANBAN_QUERY` selects `updatedDate` on both `items` and the outgoing/
  incoming reference fragments, and both models inherit `TimeStampedModel`'s `auto_now` `updated_date`
  (`examples/fakeshop/apps/kanban/models.py:118-122`). The edited item's and the edited reference's
  `updatedDate` therefore advance, and the deleted item's entry disappears. Expected. They are stored
  values, not `now()` at render time, so step 6's byte-stability still holds.
- **Card 19 changes too, legitimately.** `CardReference` id 17 is card 11's *outgoing* reference and
  card 19's *incoming* one, and the query selects `incomingReferences` as well. So
  `DONE-019-0.0.6`'s payload carries the same new `rawText`. This does **not** contradict "no other
  card's rendering moved": `render_card` renders only `outgoingReferences`, so `KANBAN.md`'s
  `DONE-019-0.0.6` card is untouched, and the HTML change is one denormalized copy of the sentence
  this item deliberately rewrote.
- Confirm every `git diff -- KANBAN.html` hunk falls **between** the `<!-- KANBAN_DATA_START -->` and
  `<!-- KANBAN_DATA_END -->` markers. The Vue shell outside them is hand-edited source
  (`START.md` `## Rendered docs`) and `embed_dashboard_data` replaces only the marked block; a hunk
  outside the markers is a stop condition.

### Implementation discretion items

Genuinely Worker 2's, having been assessed:

- The shell mechanics of step 4 — heredoc into `manage.py shell` versus `shell -c` versus a
  scratchpad `.py` run through `manage.py shell <` — provided it goes through the Django ORM, runs
  inside one `transaction.atomic`, and keeps all three pre-write assertions. The **strings** are not
  discretionary and are pinned verbatim above.
- Whether the scratchpad directory is `mktemp -d` or the session scratchpad path. Either, so long as
  it is outside the repository working tree.
- The order of the two regenerate commands within a step (they are independent).

Not discretionary, and stated so the builder does not treat them as open: the two replacement strings;
which `#### Scope` row is deleted; that `#### Files likely touched` is left alone; that
`docs/GLOSSARY.md` is not regenerated; that no row other than the three named is written.

### Dispatched findings checklist

Boxes stay `- [ ]` at planning. Worker 2 ticks only a box whose fix actually landed in its diff this
pass and states any deferral in the build report; Worker 1 audits every tick at final verification.

- [x] **R3-1a** — `#### Scope` bullet 2 states a claim R1 removed from the spec: "Kept the remaining
      scalar override skip documented as a separate scalar-field concern under `DONE-019-0.0.6`" (the
      placeholder `tests/types/test_base.py::test_consumer_annotation_overrides_synthesized` was
      retired at `0.0.6` by `a357c68c`). `kanban_carditem` card 11 / section `scope` / `order` 1 now
      reads the pinned `NEW_ITEM` string and states what is true now.
- [x] **R3-1b** — the same falsified sentence re-renders under `#### Card references` from a
      **separate** column, `kanban_cardreference.raw_text` (source card 11 -> target card 19, kind
      `related`), not from `CardItem.text`. That row now reads the pinned `NEW_REF` string, and the
      reference row itself is kept so every `{{card_ref:0}}` placeholder still resolves.
- [x] **R3-2** — `#### Scope`'s duplicate row is removed: `kanban_carditem` card 11 / section `scope`
      / `order` **2** ("replace stale M2M / forward-reference skips with definition-order tests.") is
      **deleted**; `order` **0** ("Replaced stale M2M and forward-reference skips with
      definition-order tests.") is **kept** unchanged. No re-ordering write on the survivors.
- [x] **R3-3** — `#### Files likely touched` is left at its three existing rows;
      `tests/types/test_base.py` and `tests/optimizer/test_extension.py` are **not** added. Planned out
      for the four reasons under `#### Sub-check 3`; tick this box by confirming the section is
      byte-unchanged in the rendered diff.
- [x] **R3-V** — the verification set in `### Test additions / updates` ran and is recorded in the
      build report: the step-0 concurrency gate, the step-1 baseline regenerate-to-temp diffs (both
      empty), the pre-edit and two post-edit `shasum` pairs (the two post-edit pairs identical), the
      empty `git diff docs/GLOSSARY.md`, a passing `manage.py check`, the end-to-end read of the
      rendered `DONE-011-0.0.4` card, and the confirmation that no other card's `KANBAN.md` rendering
      moved.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

---

## Build report (Worker 2)

### Files touched

Grounded in `git status --short` (the tree carries ~140 concurrently-dirty paths; the three below are
this pass's, and no fourth tracked path was written by this pass):

- `examples/fakeshop/db.sqlite3` — three kanban rows written through the Django ORM inside one
  `transaction.atomic`: `CardItem` (card 11 / section `scope` / `order` 1) re-texted to the pinned
  `NEW_ITEM` string; `CardReference` (source card 11 -> target card 19, kind `related`) `raw_text`
  re-texted to the pinned `NEW_REF` string; `CardItem` (card 11 / section `scope` / `order` 2), the
  lowercase duplicate, deleted. No other row was touched.
- `KANBAN.md` — regenerated by `scripts/build_kanban_md.py`. Not hand-edited.
- `KANBAN.html` — regenerated by `scripts/build_kanban_html.py`. Not hand-edited.
- `docs/builder/bld-011-r3-kanban_card_body.md` — this build report, the five ticked checklist boxes,
  and `Status: built`.

`docs/GLOSSARY.md`, `docs/TREE.md`, `CHANGELOG.md`, `README.md`, all package source and all tests:
untouched, confirmed by `git status --porcelain -- <paths>` returning nothing for the doc surfaces and
by this pass issuing no write to any of them.

### Tests added or updated

None, and none was possible — the plan's `### Test additions / updates` states this item lands no
Python and no test. No `pytest` was run in this pass, so no `--cov*` flag was used.

### Validation run

No `ruff` invocation: this pass touched no `.py` file. Every command below was run from the repository
root.

- **Step 0, concurrency gate** — `git status --porcelain -- examples/fakeshop/db.sqlite3 KANBAN.md KANBAN.html docs/GLOSSARY.md`
  -> **empty output**, re-run at the start of this pass. All four clean at `HEAD` (`054de9dd`), so no
  concurrent writer held an unlanded card edit that this regenerate would have published.
- **Step 1, baseline regenerate-to-temp** — both diffs **empty**, so the committed DB carried no state
  the rendered docs did not already show and the regenerate published nothing but this item's edit:
  - `uv run python scripts/build_kanban_md.py --md "$SCRATCH/kanban-baseline.md"` ("Wrote 69 cards
    (excluded 1 backlog cards) and 15 board docs"), then `diff KANBAN.md "$SCRATCH/kanban-baseline.md"`
    -> no output, exit 0.
  - `cp KANBAN.html "$SCRATCH/kanban-baseline.html"`,
    `uv run python scripts/build_kanban_html.py --html "$SCRATCH/kanban-baseline.html"` ("Wrote 70
    cards, 15 board docs, and 11 lookup arrays"), then `diff KANBAN.html "$SCRATCH/kanban-baseline.html"`
    -> no output, exit 0.
- **Step 2, pre-edit hashes** — `shasum -a 256 KANBAN.md KANBAN.html`:
  - `39faf35529975d18db9887e364c7bace4805600fdf0a062c5fb0bf1860c5e8d0  KANBAN.md`
  - `cf928b80d474ef716714c7d6ca7ec73e11f91f4efe2fa9a3ea013b4127dbb941  KANBAN.html`
- **Step 3, read-only row read** — `cp examples/fakeshop/db.sqlite3 "$SCRATCH/db-r3.sqlite3"` then two
  `sqlite3 -readonly` selects against the copy (never the live file). All four rows in the plan's
  mechanism table read **exactly** as stated, ids included (614 / 615 / 613 `CardItem`, 17
  `CardReference`), and the full card-11 item set was `scope` 0/1/2, `files_touched` 0/1/2,
  `why_it_matters` 0, `note` 0.
- **Step 4, the ORM write** — heredoc into `uv run python examples/fakeshop/manage.py shell`, verbatim
  from the plan (strings unmodified). All three pre-write assertions passed; the three writes ran
  inside one `transaction.atomic` with plain `.save()` (no `update_fields`), so every pre_save /
  post_save receiver saw a complete instance. Output: `ok`.
- **Step 5, regenerate** — `uv run python scripts/build_kanban_md.py` and
  `uv run python scripts/build_kanban_html.py`, both from the repository root, both reporting the same
  card / board-doc counts as the baseline run (69 md / 70 html cards, 15 board docs).
- **Step 6, two-consecutive-regenerate byte stability** — the two post-edit digest pairs are
  **identical**:
  - pass 1: `57d4404454e57190a8ee6431f22ee26c91e19fe9b40456ac8f3f9bb2b669a66b  KANBAN.md`,
    `d9ada4cfba16127170ce0119a13e013f4df023d6da48a0c5e048671197ca6cb9  KANBAN.html`
  - pass 2: `57d4404454e57190a8ee6431f22ee26c91e19fe9b40456ac8f3f9bb2b669a66b  KANBAN.md`,
    `d9ada4cfba16127170ce0119a13e013f4df023d6da48a0c5e048671197ca6cb9  KANBAN.html`
- **Step 7, glossary untouched** — `git diff docs/GLOSSARY.md` -> **empty**, and
  `git diff --stat docs/GLOSSARY.md` -> empty. `scripts/build_glossary_md.py` was not run.
- **Step 8, writable set** — `git status --porcelain -- KANBAN.md KANBAN.html examples/fakeshop/db.sqlite3 docs/GLOSSARY.md docs/TREE.md CHANGELOG.md README.md`
  reports exactly `M KANBAN.html`, `M KANBAN.md`, `M examples/fakeshop/db.sqlite3` and nothing else.
  The repo-wide `git status --porcelain | wc -l` is **140**, up from the plan's ~123 — the surplus is
  two concurrent sessions' package sources, tests, `docs/dry/`, `docs/shadow/` and `docs/SPECS/spec-009…`,
  confirmed by an `mmin -25` sweep. **None was edited, reverted, staged, stashed, or `git checkout`ed.**
  Nothing was committed, staged, or branched.
- `uv run python examples/fakeshop/manage.py check` -> `System check identified no issues (0 silenced).`,
  exit 0.
- `uv run python scripts/check_trailing_commas.py --check KANBAN.md` -> exit 0, no output (the edit
  adds no link definition, so the scaffold hook is a no-op as predicted).

### Rendered-result verification

- **The rendered card, read end to end.** `grep -n 'stale_placeholder_cleanup' KANBAN.md` -> the board
  index row at `:136` and the card anchor at `:4558`; the card block `KANBAN.md:4558-4595` was read in
  full. `#### Scope` now carries **exactly two** bullets; bullet 2 reads verbatim
  ``- Scalar field override semantics is a separate concern from definition order and is owned by `DONE-019-0.0.6`, which ships it at `0.0.6`.``;
  the lowercase duplicate is gone; `#### Files likely touched` still lists its three original paths in
  order; `#### Note` still renders `` `DONE-019-0.0.6` `` (so the surviving `{{card_ref:0}}`
  placeholders still resolve); `#### Card references` reads verbatim
  ``- Related: Scalar field override semantics is a separate concern from definition order and ships at `0.0.6`. -> `DONE-019-0.0.6` - Consumer override semantics (scalar fields)``.
  The `#### Glossary terms` table still shows `shipped (0.0.4)` / `shipped (0.0.6)`.
- **No other card's rendering moved.** `git diff -- KANBAN.md` is confined to the `DONE-011-0.0.4` card
  block at net **-3 / +2** lines, exactly the predicted content. The `{{last_refreshed}}` line does not
  appear in the diff, confirming no `Card` and no `BoardDoc` was saved.
- **Shape deviation from the plan's prediction, recorded.** The plan predicted "exactly one hunk"; git
  emits **two** hunks (`@@ -4574,8 +4574,7 @@` for `#### Scope` and `@@ -4593,7 +4592,7 @@` for
  `#### Card references`). This is a hunk-grouping artifact only — the two edited regions sit ~17 lines
  apart, beyond the default 3-line context, so they cannot coalesce. Both hunks are inside the
  `DONE-011-0.0.4` block and the net line delta is the predicted -3 / +2. No content differs from the
  prediction.
- **`KANBAN.html` diff, against the plan's two stated expectations.** `git diff -U0 -- KANBAN.html`
  yields a single hunk, `@@ -97 +97 @@` — the `window.KANBAN_DATA` line. `grep -n` places
  `<!-- KANBAN_DATA_START -->` at line 95 and `<!-- KANBAN_DATA_END -->` at line 100, so the hunk falls
  strictly **between** the markers and the hand-edited Vue shell is untouched. String census of the new
  payload: the falsified sentence `Kept the remaining scalar override skip` -> **0** occurrences in both
  `KANBAN.md` and `KANBAN.html`; the deleted duplicate `replace stale M2M / forward-reference skips`
  -> **0**; `NEW_ITEM`'s distinctive prefix -> **1** (the `CardItem`); `NEW_REF`'s distinctive prefix ->
  **2** — card 11's `outgoingReferences` and card 19's `incomingReferences`, which is exactly the
  legitimate denormalized second copy the plan predicted, not drift. The `updatedDate` movement on the
  edited item and reference is likewise expected and is a stored value, which is why step 6's
  byte-stability still holds.

### Failability proofs

None; this pass introduced no new boundary.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- **Scratchpad location** — the session scratchpad
  (`/private/tmp/claude-501/…/scratchpad`) was used rather than `mktemp -d`, one of the plan's two
  explicitly discretionary choices. It is outside the working tree, which is the property that matters.
  It holds `kanban-baseline.md`, `kanban-baseline.html`, and `db-r3.sqlite3`; none is in the repo.
- **Shell mechanics** — a heredoc piped into `manage.py shell`, the plan's first named option. The
  block is transient and is committed nowhere. The strings were used verbatim; nothing about them was
  re-derived or re-wrapped.
- **Both regenerate scripts write to the repository-root default** when given no flag, so step 5 used
  the bare invocations and only the step-1 baseline runs carried `--md` / `--html` redirects to the
  scratchpad. `build_kanban_html.py` embeds into an existing file rather than writing one from scratch,
  which is why the baseline run needed the `cp` first — as the plan wrote it.

### Notes for Worker 3

- The plan's `#### Mechanism` section is correct and was re-verified against the live database before
  any write: `#### Scope` and `#### Card references` render **different columns**
  (`CardItem.text` vs `CardReference.raw_text`), so sub-check 1 genuinely required two row edits.
- The two replacement strings deliberately differ (the `CardItem` carries `{{card_ref:0}}`, the
  `CardReference` does not) because `render_card` already appends the target card key to a reference
  line. Confirmed in the rendered output above: the card id appears once per line in both places.
- The `KANBAN.md` two-hunk shape is the only deviation from any prediction in the plan, and it is
  cosmetic (git context grouping). Recorded above rather than passed silently.
- The tree is dirty with ~140 concurrent-session paths. `git diff` for anything outside
  `KANBAN.md` / `KANBAN.html` / `examples/fakeshop/db.sqlite3` is not this pass's work.
- Nothing was deferred. All three sub-checks and the verification set landed, so all five checklist
  boxes are ticked, including `R3-3` — which the plan defines as ticked by *confirming* the
  `#### Files likely touched` section is byte-unchanged, and it is (absent from the diff, still its
  three original rows in the rendered card).

### Notes for Worker 1 (spec reconciliation)

No spec gap surfaced. The board's `#### Scope` bullet 2 and `#### Card references` line now compress
`docs/SPECS/spec-011-stale_placeholder_cleanup-0_0_4.md` `## Scope`'s closing paragraph, so the spec
and the board state one thing. No amendment is recommended and none is owed.

---

## Review (Worker 3)

Reviewed the three paths this item owns (`examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`)
against the reconciled spec, its rationale companion, the plan's `### Dispatched findings checklist`,
and the kanban app's own models / signals / services / exporters. The tree carries ~140
concurrently-dirty paths from two maintainer sessions; every one outside the three above was
attributed as not this item's and was neither read as authority nor touched. Nothing was staged,
reverted, stashed, `git checkout`ed, or committed, and no file outside the writable set was written.

Every claim below was re-derived, not accepted from the build report. `git diff` on the database is a
binary diff and proves nothing semantic, so the DB delta was measured by dumping `git show
HEAD:examples/fakeshop/db.sqlite3` and the live file into read-only scratch copies **outside the
repository** and diffing the two `.dump` outputs.

### High:

None.

### Medium:

None.

### Low:

#### The plan's provenance claim for the denormalized pair names the wrong writer

`docs/builder/bld-011-r3-kanban_card_body.md` `#### Mechanism, verified against the models and the
renderer before being asserted` (third bullet) explains the byte-identical `CardItem.text` /
`CardReference.raw_text` pair as written by
`examples/fakeshop/apps/kanban/services.py::add_dependency_note`. That helper cannot have created
these rows: it resolves `DEPENDENCY_REFERENCE_KIND_KEY = "dependency"` and
`DEPENDENCY_NOTE_SECTION_KEY = "dependencies_note"` (`services.py:38-39`), while the actual rows are
`kanban_cardreference.kind_id = 3` (`related`) and `kanban_carditem.section_id = 1` (`scope`) — read
from the scratch DB copy. The pair came from the spec importer path
(`services.py::create_card_from_spec` -> `_create_sections` / `_create_references`, one `spec` dict
feeding both), not from the dependency-note helper.

Severity Low and **no revision is owed**: this is prose about how the duplication arose, and nothing
in the build depends on it. The operative conclusion the section was written to establish — that
`#### Scope` and `#### Card references` render **different columns**, so sub-check 1 is two row edits
and not one — is independently correct: `scripts/build_kanban_md.py::render_card` emits
`resolve_card_refs_for_card(item["text"], card)` at `build_kanban_md.py:463`/`:470` and
`resolve_card_refs_for_card(reference.get("rawText", "").strip(), card)` at `:485-486`. Recorded so
Worker 1's final verification does not carry the mis-attribution forward into the cycle record.

### DRY findings

None. This item adds no helper, no script, no constant, and no reusable snippet; the ORM block is
transient and committed nowhere. The one duplication in play is the pre-existing denormalized
`CardItem.text` / `CardReference.raw_text` pair, which the item correctly kept in step with the change
rather than adding a third copy of the sentence. No existence challenge is raised: nothing was created
whose existence could be challenged.

Checked, and deliberately **not** flagged: the two replacement strings now differ (`NEW_ITEM` carries
`{{card_ref:0}}`, `NEW_REF` does not), so a pair that was byte-identical is no longer. Nothing joins
the two columns — `render_card` renders them from different keys, and the importer's reconcile step
matches items on `(card, section, order)` (`examples/fakeshop/apps/kanban/models.py:862-871`), never
on text — so the divergence is safe, and it is what stops `DONE-019-0.0.6` rendering twice on the
`#### Card references` line. Confirmed in the rendered output.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` -> **empty**. `__all__` and the re-export list
are unchanged. No package source is in this item's writable set at all.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md. Verified independently:
`git status --porcelain -- CHANGELOG.md` returns nothing.

### Documentation / release sanity

The slice touches `KANBAN.md` / `KANBAN.html`, so this section applies and was run end to end.

- **The landed card text is true at `HEAD`.** The rendered `DONE-011-0.0.4` card (`KANBAN.md:4558-4595`,
  read in full) now says
  ``- Scalar field override semantics is a separate concern from definition order and is owned by `DONE-019-0.0.6`, which ships it at `0.0.6`.``
  The retired claim is gone, and the sentence is checkable in both directions:
  `grep -rn "test_consumer_annotation_overrides_synthesized" tests/` returns **zero** hits, so no such
  placeholder is "kept" anywhere, and `git show --stat a357c68c` is
  `Finish docs/spec-015-consumer_overrides_scalar-0_0_6.md` (2026-05-19), the `0.0.6` commit that
  retired it. The new wording matches `docs/SPECS/spec-011-stale_placeholder_cleanup-0_0_4.md`
  `## Scope`'s closing paragraph ("…is a separate concern from definition order … Card `DONE-019-0.0.6`
  owns it and ships it at `0.0.6`") compressed to board altitude, and asserts nothing on the rationale
  companion's *Claims the spec no longer makes* list (`…-rationale.md:215-217`: that a placeholder is
  kept/skipped/pending, or that `DONE-019-0.0.6` is where it is *documented*). Both are avoided.
- **Card ids and versions match.** `#### Glossary terms` still renders `shipped (0.0.4)` /
  `shipped (0.0.6)`; the `Spec:` link resolves to the archived spec; `{{card_ref:0}}` still resolves to
  `DONE-019-0.0.6` in both the `#### Scope` bullet and the surviving `#### Note` row, because the
  `CardReference` row was kept at `order` 0 (confirmed in the DB dump).
- **No stale "planned"/"coming soon" wording**, and no version string moved. `{{last_refreshed}}` does
  not appear in the diff, corroborating that no `Card` and no `BoardDoc` row was saved.
- **No card moved section**, and no docstring-fed generated doc is involved (`docs/TREE.md` clean).
- **`docs/GLOSSARY.md` is untouched**: `git status --porcelain -- docs/GLOSSARY.md` and
  `git diff --stat -- docs/GLOSSARY.md` both return **empty**.

#### No hand-edit of a generated doc — proven independently, not accepted on the report's hashes

Per `docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`, both
documents were regenerated to a scratch directory outside the repository and compared, rather than
reading the recorded digests:

```
uv run python scripts/build_kanban_md.py --md "$S/regen.md"      -> "Wrote 69 cards ... 15 board docs"
diff KANBAN.md   "$S/regen.md"    -> no output, exit 0   (MD-IDENTICAL)
cp KANBAN.html "$S/regen.html"
uv run python scripts/build_kanban_html.py --html "$S/regen.html" -> "Wrote 70 cards, 15 board docs, 11 lookup arrays"
diff KANBAN.html "$S/regen.html"  -> no output, exit 0   (HTML-IDENTICAL)
```

Both tracked files are therefore exactly what the current DB renders — no hand-edit survives in
either. Corroborated by the boolean form: `build_kanban_md.py --check` and
`build_kanban_html.py --check` both exit **0**. `scripts/check_trailing_commas.py --check KANBAN.md`
exits **0**.

**The `KANBAN.html` Vue shell did not move.** Splitting both the `HEAD` blob and the working file at
`<!-- KANBAN_DATA_START -->` / `<!-- KANBAN_DATA_END -->` (lines 95 / 100) and comparing the two
outside segments: pre-marker segment **identical**, post-marker segment **identical**. The entire
change is inside the marked data block, which is the only part `embed_dashboard_data` writes.

#### Blast radius — measured on the DB, not inferred from the render

`.dump` diff of the `HEAD` copy vs the live copy is **12 lines**, and is the complete write set:

| Row | Change |
|---|---|
| `kanban_carditem` 615 (card 33 / section 1 `scope` / `order` 1) | `text` -> the `NEW_ITEM` string; `updated_date` advanced |
| `kanban_carditem` 613 (`order` 2, the lowercase duplicate) | **deleted** |
| `kanban_uuidmodel` for item 613 | removed by its own `on_delete=CASCADE` O2O link, not orphaned |
| `kanban_cardreference` 17 (source card 33 -> target 41, kind 3 `related`, `order` 0) | `raw_text` -> the `NEW_REF` string; `updated_date` advanced |

No `kanban_card` row appears in the dump diff, so **no `Card` was saved**; no `CardItem` or
`CardReference` row outside the three named was written or deleted; no other table changed at all.
`KANBAN.md`'s diff is two hunks, net **-3 / +2**, entirely inside the `DONE-011-0.0.4` block
(`@@ -4574,8 +4574,7 @@` and `@@ -4593,7 +4592,7 @@`), so no other card's Markdown rendering moved.
The two-hunk shape (the plan predicted one) is a git context-grouping artifact, correctly recorded by
Worker 2 rather than passed silently; the two edited regions sit ~17 lines apart.

For `KANBAN.html` the payload was parsed as JSON from both versions and diffed key-sorted rather than
eyeballed: **34 changed lines**, all of them the item-615 text, the item-613 object's removal, the
reference-17 `rawText` in **two** places — card 11's `outgoingReferences` and card 19's
`incomingReferences` — and the three `updatedDate` values. Card 19's copy is exactly the legitimate
denormalized incoming-edge copy the plan predicted, and it does not reach `KANBAN.md` because
`render_card` renders only `outgoingReferences` (`scripts/build_kanban_md.py:476`).

#### Constraint safety of the deletion — verified against the invariants, not against "it did not raise"

`CardItem.Meta.constraints` holds exactly one constraint, `unique_item_position_per_card` on
`(card, section, order)` (`examples/fakeshop/apps/kanban/models.py:861-872`). There is **no**
contiguity or count invariant anywhere on `CardItem`: `Meta.ordering` is
`["card", "section", "order"]`, a sort key, not a density requirement. Surviving `order` values are
`0, 1` — unique, so the constraint holds, and no re-ordering write on the survivors was owed.

`examples/fakeshop/apps/kanban/signals.py` registers `pre_delete` only for `SpecDoc`
(`protect_done_card_spec`) and `CardGlossaryTerm` (`protect_done_card_glossary_link`), and
`post_delete` only for `Card` (`compact_card_order_after_delete`, which compacts `Card.number` and has
nothing to do with item order). **No receiver of any kind is registered for `CardItem` deletion**, so
the done-card protections were not silently bypassed — they never apply to this model, and the
compaction the board does perform is deliberately scoped to cards. The next append is also safe:
`services.py::_next_card_item_order` is `Max("order") + 1`, not `count()`, so it returns `2` rather
than colliding with a survivor.

The `CardReference` save did run its `pre_save` receiver (`prepare_card_reference`,
`signals.py:491`), because the write used plain `.save()` rather than raw SQL or `update_fields` —
confirmed by the surviving `order` 0 and by the `uuid` side rows still present for both surviving
rows in the regenerated payload.

#### Every checklist tick is real

| Box | Verified against | Verdict |
|---|---|---|
| R3-1a | `kanban_carditem` 615 `text` in the dump diff; rendered bullet 2 | real |
| R3-1b | `kanban_cardreference` 17 `raw_text` in the dump diff; rendered `#### Card references` line; reference row kept at `order` 0 so `{{card_ref:0}}` still resolves (`#### Note` still renders `DONE-019-0.0.6`) | real |
| R3-2 | `kanban_carditem` 613 absent from the live dump, `order` 0 row byte-unchanged, no survivor re-ordered | real |
| R3-3 | `#### Files likely touched` absent from the `KANBAN.md` diff and still its three original rows in the rendered card; no `files_touched` row in the dump diff. The box's own definition is "tick by confirming the section is byte-unchanged", so the tick is what the box asks for, not a claim of work not done | real |
| R3-V | every command in the verification set re-run or independently re-derived here (regenerate-to-scratch, `--check` pair, glossary diff, `manage.py check` shape, scaffold check, end-to-end card read, no-other-card confirmation) | real |

No box is ticked without a matching change, and no change in the diff lacks a box.

### What looks solid

- The read-only method throughout: the DB was read from a scratch copy and written only through the
  ORM inside one `transaction.atomic`, with three pre-write assertions on the exact current strings, so
  a stale row id could not have caused a wrong-row write. Selecting on `(card, section, order)` while
  asserting on text is the right shape given that id order and `order` order disagree here.
- Recording the two-hunk deviation from the plan's "exactly one hunk" prediction instead of quietly
  matching the prose to the output.
- Deleting the duplicate rather than folding it: there was no content in `order` 2 that `order` 0
  lacked, and folding would have produced a third wording nobody wrote.
- The decided disposition of sub-check 3 is argued, not skipped, and its reasoning is the same one the
  rationale companion used elsewhere — a board copy of a fact the spec already states checkably is the
  surface that drifts next.

### Temp test verification

None. No temp test was created and none was warranted: this item lands no Python, and
`docs/builder/temp-tests/r3/` was not used. No `pytest` was run in this review, so no `--cov*` flag was
used. No failability proof is owed or was invented — the diff introduces no boundary, guard, gate, or
rejection path, which is the `docs/builder/BUILD.md` `### What needs a proof, and what does not`
carve-out. Re-run set is therefore legally **empty**: no boundary meets the mandatory floor because
there is no boundary. Hot-path budget: none owed, plan declares no hot path. Floor verification: none
owed, plan declares scope none. `scripts/review_inspect.py` was **not** run, and the skip is recorded
here with its reason: it inspects Python source, and this item's entire diff is one binary database
file and two generated documents.

### Notes for Worker 1 (spec reconciliation)

- No spec gap surfaced, and no amendment is owed. The board and
  `docs/SPECS/spec-011-stale_placeholder_cleanup-0_0_4.md` `## Scope` now state one thing, and the
  rationale companion's *Claims the spec no longer makes* list is respected by the landed text.
- Carry the Low finding into the cycle record: the plan's `add_dependency_note` provenance claim is
  wrong (kind `related` / section `scope` cannot come from that helper, which writes kind `dependency`
  / section `dependencies_note`). Nothing built on it, but the plan text should not be quoted forward
  as if it were measured.
- For the final gate: `examples/fakeshop/db.sqlite3`, `KANBAN.md`, and `KANBAN.html` are the three
  paths this cycle owns in the working tree, and the DB is a binary blob in `git diff` — the semantic
  delta is the 12-line `.dump` diff recorded above, which is what a reviewer of the eventual commit
  should be handed.

### Review outcome

`review-accepted`. One Low finding, recorded above with its reason for not requiring a revision; no
High or Medium finding. All five checklist boxes carry a matching landed change; the card text is true
at `HEAD`; both generated documents are pure regenerate output, proven by independent regeneration to
a scratch path outside the repository; the `KANBAN.html` Vue shell is byte-identical outside the data
markers; the blast radius is exactly the three named rows plus one cascade side row and the one
predicted denormalized incoming-edge copy; `docs/GLOSSARY.md` is untouched with an empty diff; and the
deletion is constraint-safe by the model's own single `(card, section, order)` uniqueness constraint
and the absence of any `CardItem` delete receiver.

---

## Final verification (Worker 1)

Every claim below was re-derived at this working tree rather than accepted from the build report or
the review (`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`).
The database was read from a **copy** in the session scratchpad with `sqlite3 -readonly`; the live
`examples/fakeshop/db.sqlite3` was never opened for writing, no regenerate script was run in write
mode, and no path outside `docs/builder/bld-011-r3-kanban_card_body.md` was modified by this pass.

### 1. Worker 3's routed Low finding — confirmed, and the prose corrected

The finding holds. `examples/fakeshop/apps/kanban/services.py::add_dependency_note` resolves
`DEPENDENCY_REFERENCE_KIND_KEY = "dependency"` and `DEPENDENCY_NOTE_SECTION_KEY = "dependencies_note"`
(`services.py` #"DEPENDENCY_NOTE_SECTION_KEY = " / #"DEPENDENCY_REFERENCE_KIND_KEY = ") and passes both
into `append_card_reference` / `append_card_item`. The live rows are neither: read from the scratch
copy, card 11's reference row 17 joins `kanban_cardreferencekind.key = 'related'` and its prose row
joins `kanban_section.key = 'scope'`. So that helper cannot have written this pair.

The writer is the card-spec import path: `services.py::create_card_from_spec` fans one spec dict out
to `::_create_sections` (appends the `scope` `CardItem` from a `sections` bullet) and
`::_create_references` (appends the `CardReference` from a `references` entry, defaulting
`kind` to `"related"`). Two independent appends from one source document — which is why the strings
were byte-identical without any single call writing both.

**Corrected in place** in `#### Mechanism, verified against the models and the renderer before being
asserted`, third bullet, with the correction marked as Worker 1's so the artifact reads as a record
rather than a silent rewrite. The conclusion that bullet exists to establish — `#### Scope` renders
`CardItem.text` and `#### Card references` renders `CardReference.raw_text`, therefore sub-check 1 is
**two** row edits — is untouched and independently correct (`scripts/build_kanban_md.py::render_card`
emits `resolve_card_refs_for_card(item["text"], card)` for items and
`resolve_card_refs_for_card(reference.get("rawText", "").strip(), card)` for outgoing references).
No further finding follows from it: nothing in the plan's steps, the write, or the verification set
depended on the provenance sentence.

### 2. Dispatched findings checklist audit — all five ticks are real, none over-ticked

Audited against the live database and the rendered documents, not against the build report.

| Box | Evidence re-derived here | Verdict |
|---|---|---|
| R3-1a | `kanban_carditem` card 11 / `scope` / `order` 1 reads ``Scalar field override semantics is a separate concern from definition order and is owned by `{{card_ref:0}}`, which ships it at `0.0.6`.``; renders as `KANBAN.md` `#### Scope` bullet 2 with the placeholder resolved to `DONE-019-0.0.6` | `- [x]` stands |
| R3-1b | `kanban_cardreference` id 17, kind `related`, `order` 0, `raw_text` = ``Scalar field override semantics is a separate concern from definition order and ships at `0.0.6`.``; the row is **kept**, so `#### Note`'s `{{card_ref:0}}` still resolves (it renders `DONE-019-0.0.6`) | `- [x]` stands |
| R3-2 | card 11's `scope` section now holds exactly two rows, `order` 0 and 1; the lowercase duplicate (`order` 2) is absent, and `order` 0 is byte-unchanged (`Replaced stale M2M and forward-reference skips with definition-order tests.`) | `- [x]` stands |
| R3-3 | `files_touched` still holds exactly its three original rows (`order` 0/1/2, the three definition-order modules) and the rendered `#### Files likely touched` lists the same three. The box's own contract is "tick by confirming the section is byte-unchanged", which is what the evidence shows | `- [x]` stands |
| R3-V | the verification set's load-bearing outputs re-derived: `build_kanban_md.py --check` -> `KANBAN.md is up to date.` exit 0; `build_kanban_html.py --check` -> `KANBAN.html is up to date.` exit 0; `git status --porcelain -- KANBAN.md KANBAN.html examples/fakeshop/db.sqlite3 docs/GLOSSARY.md docs/TREE.md CHANGELOG.md` -> exactly the three owned paths modified, the other three clean | `- [x]` stands |

No box is un-ticked, so no `revision-needed` follows from the audit and no box needs a deferral
reason. **One decided disposition is carried to the catalog rather than deferred silently:** the
optional third sub-check R2 raised (`#### Files likely touched` does not name the two donor files the
placeholders were removed from) was planned **out** with four recorded reasons, and R3-3 ticks that
decision rather than work left undone. It is in `bld-011-final.md`'s `### Deferred work catalog` with
its one-sentence reversal recipe, since the reversal is a maintainer preference call, not a defect.

### 3. The landed card text matches the reconciled spec

The rendered `#### Scope` bullet 2 compresses
`docs/SPECS/spec-011-stale_placeholder_cleanup-0_0_4.md` `## Scope`'s closing paragraph ("Scalar field
override semantics is a separate concern from definition order … Card `DONE-019-0.0.6` owns it and
ships it at `0.0.6`.") to board altitude and asserts nothing the rationale companion lists under
*Claims the spec no longer makes* — in particular it does not say a placeholder is kept, skipped, or
pending. The card's `#### Glossary terms` rows (`shipped (0.0.4)` / `shipped (0.0.6)`) and its `Spec:`
link to the archived path are unchanged and correct. Board and spec now state one thing.

### 4. Spec reconciliation

**No spec edit is owed, and none was made.** Re-verified per `worker-1.md`
`## Spec status-line re-verification (every Worker 1 spawn)`: the spec's header lines (title, target
release `0.0.4` per card `DONE-011-0.0.4`, `Status: shipped`, owner, and the rationale-companion
pointer) all still describe the cycle's current state, and R3 changed nothing the spec claims. R3
landed no source, no test, and no new contract; it brought a generated board rendering into agreement
with a spec this cycle had already reconciled in R1. Worker 2 and Worker 3 both recorded "no spec gap
surfaced", and this pass found none either.

### Summary

R3 corrected the `DONE-011-0.0.4` card body in the kanban database and regenerated both rendered
documents. Three rows changed: the `scope` `CardItem` at `order` 1 re-texted off the falsified
kept-skip tense, the `related` `CardReference`'s `raw_text` re-texted the same way, and the duplicate
`scope` row at `order` 2 deleted. Both generated documents are pure regenerate output, confirmed here
by both exporters' `--check` mode. The one Low finding routed to this pass was confirmed against
source and the artifact's prose corrected so the mis-attribution is not quoted forward; the analysis
it supported was independently correct and stands.

### Spec changes made (Worker 1 only)

**None.** The spec and its rationale companion were read and re-verified (section 4) and neither was
opened for writing. No checklist box is left `- [ ]`, so no deferral reason is owed under this
heading; the one decided disposition (sub-check 3) is recorded in section 2 and carried to
`docs/builder/bld-011-final.md`'s `### Deferred work catalog`.

### Final status

`final-accepted`.
