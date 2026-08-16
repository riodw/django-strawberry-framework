# Build: R3 — card `TODO-BETA-054-0.1.1`'s two stale `DjangoModelField` / BACKLOG-item-38 references

Spec reference: `docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md` (context only; this item edits no spec). The
authority for the replacement text is `docs/SPECS/spec-054-fieldset-0_1_1.md` `## Risks and open questions`
#"Stale card reference" and `### Decision 11`.
Contract: `docs/builder/build-009-rich_schema_architecture-0_0_4.md` `### Maintainer decision 3` site 3, and
`### Maintainer decision 6` (which re-authorized the item after its clean-tree precondition failed).
Status: final-accepted

Chain: `W1 -> W2 -> W3 -> W1`, per the plan's per-item chain table. The deliverable is a **database edit plus a
regenerate**, which is Worker 2's work; this pass plans it and writes nothing outside this artifact and Worker 1's
namespaced memory file.

## Plan (Worker 1)

### Spec status-line re-verification

`docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md` header lines re-read this pass. R1 and R1b are
`final-accepted` and closed; nothing in R3 falsifies a status line, and R3 edits no spec. `spec-054` is read-only
here — it is a sibling spec the plan's `## Build-wide context flags` does not open, and R3 quotes it rather than
touching it. **No spec edit is planned or expected for this item.**

### The two references, re-verified against the tree before planning

Worker 0's dispatch quoted two references. Both were re-derived this pass rather than accepted, and both hold.
Line numbers below are working-tree `KANBAN.md` line numbers at the time of writing — **navigational only**,
pin-at-write-time, and NOT the edit target (the edit target is the DB).

| # | Site | Rendered at | Verified |
|---|---|---|---|
| **A** | `KANBAN.md` #"item 38 for the \`DjangoModelField\` custom Strawberry field class" | `KANBAN.md:518`, card 054 `#### Foundation-slice seam`, bullet 2 | yes — quoted below byte-exact |
| **B** | `KANBAN.md` #"See [\`BACKLOG.md\`][backlog] item 38 for the \`DjangoModelField\` direction" | `KANBAN.md:521`, same section, bullet 5 | yes — quoted below byte-exact |

**Both stale facts confirmed independently:**

- `BACKLOG.md` #"Layered manual relation override test policy" — item 38 today is a **process rule**, sitting in
  the block that opens *"Items 36, 37, and 38 were process rules, not feature cards"*. `grep -n
  "DjangoModelField" BACKLOG.md` returns **0**: there is no `DjangoModelField` entry anywhere in the file, so the
  reference is not merely mis-numbered, it has no correct target.
- `DjangoModelField` was never built (this cycle's `### Group A` D1: no `types/fields.py`, zero package-wide
  occurrences) and was declined for the third and decisive time by `spec-054` itself, which also **already
  flagged this exact card staleness** (`## Risks and open questions` #"Stale card reference").

**The population on card 054 is exactly two.** Measured, not asserted: an `awk` extraction of the card's whole
rendered region piped through `grep -n "DjangoModelField\|item 38\|BACKLOG"` returns those two lines and nothing
else. Sites A and B are the complete set for this card.

**One nearby hit that is NOT a defect, recorded so a later pass does not re-flag it:** `KANBAN.md:79` cites
"[`BACKLOG.md`][backlog] item 38" for *package-level override tests vs HTTP tests* — which **is** item 38 today.
That reference is correct and out of scope; do not touch it.

**One attribution baseline this pass established, and it is load-bearing for R3's verification** (see
`### Decision 4`): card 054's entire rendered region is **byte-identical between `HEAD` and the working tree**.
Proved read-only, without `git checkout`/`stash`:

```shell
git show HEAD:KANBAN.md > <scratch>/KANBAN.head.md
diff <(awk '/^### \[TODO-BETA-054/,/^<a id="metasearch_fields_support"/' <scratch>/KANBAN.head.md) \
     <(awk '/^### \[TODO-BETA-054/,/^<a id="metasearch_fields_support"/' KANBAN.md)   # -> no output
```

So the concurrent session's `KANBAN.md` churn (one deleted bullet at `KANBAN.md:~4479`, a different card) does
**not** intersect card 054. That gives Worker 2 a clean per-region attribution instrument even though whole-file
attribution is unavailable.

### Why this is an ORM edit plus a regenerate, and never a file edit

Recorded here in full because Workers 1-3 may not read `worker-0.md`, where the DB-backed procedure lives.

`KANBAN.md` and `KANBAN.html` are **generated** from the kanban tables in `examples/fakeshop/db.sqlite3` by
`scripts/build_kanban_md.py` and `scripts/build_kanban_html.py` (`BUILD.md` `### Generated docs are DB-backed`;
`START.md` "Rendered docs — fix the source, not the file"). They are not hand-editable source: a hand edit is
silently reverted by the next regenerate.

Four mechanics Worker 2 must honour, each verified against the scripts this pass:

1. **Write through the Django ORM**, via `uv run python examples/fakeshop/manage.py shell`. **Never raw SQL.**
   Both build scripts fetch their payload through an in-process `/graphql/` query
   (`scripts/build_kanban_html.py::fetch_dashboard_data`) whose selection requests `uuid { id }` per node, and
   the `UUIDModel` side-row is materialized by a `post_save` receiver
   (`examples/fakeshop/apps/kanban/signals.py::create_uuid_row`, registered for `CardItem` via
   `UUID_LINKED_MODELS`). A raw SQL write skips the signal and the render breaks. *Precision worth having:*
   `create_uuid_row` fires only on `created=True`, and R3 **updates** existing rows whose side-rows already
   exist — so the side-row is not the live hazard here. The ORM requirement stands regardless: raw SQL also
   bypasses `auto_now` on `updated_date` and every other receiver on the model, and `.save()` is the supported
   path the importer contract is written against.
2. **The target is `CardItem.text`** (`examples/fakeshop/apps/kanban/models.py::CardItem` — *"One bullet from a
   card's section"*). Locate via `Card.objects.get(number=54)` and its `items` related manager.
   **Verify the live `text` against the DB before editing** — do not trust `KANBAN.md`'s rendering, and do not
   trust this plan's quotation. The renderer emits `- ` + `text.strip()` per bullet
   (`scripts/build_kanban_md.py::bullet_lines`, no wrapping and no re-flow), so the DB text equals the rendered
   line minus its two-character `- ` prefix — which makes an exact-equality check available and mandatory.
3. **Regenerate** from the repository root, markdown then HTML:
   `uv run python scripts/build_kanban_md.py` then `uv run python scripts/build_kanban_html.py`.
   `build_kanban_md` imports from `build_kanban_html`, so the HTML script must be importable; running from the
   repo root is what the plan requires. `build_kanban_html.py` replaces only the marked
   `<!-- KANBAN_DATA_START -->` data block (`::embed_dashboard_data`) — the Vue shell around it is hand-edited
   source and must not be touched.
4. **Nothing else moves.** Do not flip any card status, do not touch `SpecDoc` rows, do not touch glossary rows,
   and do not run `import_spec_terms` or `scripts/build_glossary_md.py`. Card 054 stays `TODO`; card 9 is already
   `Done` and correct. **This is a two-string text fix and nothing else.**

### DRY analysis

- **Helper inventory checked.** The package-wide AST helper inventory (`worker-1.md` `### Package-wide helper
  inventory before helper planning`) was **deliberately not refreshed**, and the skip is reasoned rather than
  silent: this item writes **no Python at all** — its writable set is two `CardItem.text` values plus two
  generated files — so a `django_strawberry_framework/` symbol index cannot inform it, and running it would
  write `docs/shadow/helper-inventory.md`, which is outside this pass's exhaustive writable set. The condition
  that would change the answer: if any pass concludes R3 needs a script, a management command, or any reusable
  Python, the inventory runs **before** that is planned.
- **Existing patterns reused.** The correct corpus for this item is
  `examples/fakeshop/apps/kanban/services.py`, and it was searched. It carries `append_card_item` (creates a
  bullet), `set_item_complete` (flips `is_complete`), and `verify_item` (verification metadata) — **no service
  function edits an existing bullet's text.** So there is no helper to call and none to write: a one-off
  correction of two rows is exactly the `manage.py shell` + `.save()` case, and a service function abstracting
  "change a bullet's wording" would have one caller, ever.
- **New helpers justified.** None. See above.
- **Duplication risk avoided.** One: a naive implementation writes the new text into `KANBAN.md` (and/or
  `KANBAN.html`) **as well as** the DB, producing a second, divergent source that the next regenerate silently
  reverts. The plan prevents it by making the only write an ORM write and the only file change a regenerate
  output. A second, smaller risk: pasting the replacement text into both sites. The two replacements are
  **different strings** and are quoted separately below.

### Decision 1 — Site A replacement text (quoted exactly; Worker 2 does not improvise)

**Current `CardItem.text`** (byte-exact, no leading `- `; 307 characters, pure ASCII, so 307 bytes):

```text
`Meta.fields_class` moves out of `DEFERRED_META_KEYS` only when the field-level permission / custom-resolver / computed-field machinery is applied end-to-end (see also [`BACKLOG.md`][backlog] item 38 for the `DjangoModelField` custom Strawberry field class that field-level permissions will likely require).
```

**Replacement `CardItem.text`** (byte-exact; pure ASCII):

```text
`Meta.fields_class` moves out of `DEFERRED_META_KEYS` only when the field-level permission / custom-resolver / computed-field machinery is applied end-to-end (no custom Strawberry field class is required for it; spec-054 Decision 11 pins resolver wrapping as the mechanism that carries the gate).
```

**What changed and why:** the leading sentence is preserved **verbatim** — it is not falsified and R3's scope does
not reach it. Only the parenthetical is replaced, because it is the stale reference: it promises a
`DjangoModelField` direction in a BACKLOG item that is now the test-policy entry, and it asserts that field-level
permissions "will likely require" a class this cycle proved was never built and has been declined three times.
The replacement asserts nothing new — `spec-054` `### Decision 11` states that the wrapper *"captures the original
(generated or transplanted) resolver and delegates to it as cascade step 3"*, i.e. the wrapper is what carries the
gate, and `spec-054` `## Borrowing posture` records the same shape as borrowed verbatim from upstream.

### Decision 2 — Site B replacement text, and why the "the spec must decide" clause is in scope

**Current `CardItem.text`** (byte-exact, no leading `- `; **446 characters / 448 bytes** — one non-ASCII
character, the em dash, which is 3 bytes; macOS `awk`'s `length()` counts bytes, so measure with Python):

```text
Custom Strawberry field class — django-graphene-filters' `AdvancedFieldSet` works with a custom field type that carries the `check_<field>_permission` gate at resolve time. Strawberry's `strawberry.field(...)` already supports a `permission_classes` argument; the spec must decide between mapping `check_<field>_permission` onto that machinery or carrying a parallel gate. See [`BACKLOG.md`][backlog] item 38 for the `DjangoModelField` direction.
```

**Replacement `CardItem.text`** (byte-exact; em dashes only, no other non-ASCII):

```text
Custom Strawberry field class — django-graphene-filters' `AdvancedFieldSet` works with a custom field type that carries the `check_<field>_permission` gate at resolve time. That question is settled without one: spec-054 pins **resolver wrapping** as the mechanism (Decision 11 — the wrapper captures the generated resolver and delegates to it as the cascade's step 3), upstream-parity and zero-config with zero overhead on unmanaged fields. Mapping the gate onto Strawberry's `strawberry.field(permission_classes=...)` is likewise rejected: `BasePermission.has_permission(source, info, **kwargs)` is class-per-policy with a fixed message contract, cannot host the gate-then-override cascade ordering, and would synthesize a permission class per managed field for no consumer benefit; a custom `DjangoModelField` field class is unnecessary machinery for the same reason.
```

**The first clause is preserved verbatim** — the upstream fact it states (`AdvancedFieldSet` works with a custom
field type carrying the gate at resolve time) is still true and is the reason the question was ever open.

**Why the "the spec must decide" sentence is replaced too, and why that is inside the authorized scope rather than
a widening.** `### Maintainer decision 3` site 3 authorizes "card 054's two stale references". The stale reference
at site B is not only the trailing pointer: the pointer's whole function is to anchor an **open question**, and
`spec-054` says so in the sentence that flagged this staleness: *"The open question it anchored — custom field
class vs `strawberry.field(permission_classes=...)` vs resolver wrapping — is answered by this spec without it"*,
and the answer it then gives, in the same sentence, is resolver wrapping.
Correcting the pointer while leaving "the spec must decide between..." standing would leave one `CardItem`
asserting an open decision two clauses before the answer to it, which is a worse state than the one R3 was sent to
fix. The unit of the authorized correction is the reference, and the reference is the whole open-question framing.
It is one `CardItem`, so this is not a third site.

**`DjangoModelField` deliberately survives in the replacement, as a recorded rejection.** `spec-054`'s own text
names it in exactly that role (*"a custom `DjangoModelField` field class is unnecessary machinery for the same
reason"*), and a reader who greps card 054 for the name should find the answer rather than nothing. **Consequence
for verification:** Worker 2's post-regenerate check is *not* "zero occurrences of `DjangoModelField` on card
054" — it is "zero occurrences of `item 38` on card 054, and the only surviving `DjangoModelField` mention states
its rejection". A check written the other way would fail on a correct result.

**Reference-style link check.** Both replacements drop their `[`BACKLOG.md`][backlog]` use. `[backlog]` is used
five more times elsewhere in `KANBAN.md` (`:65`, `:79`, `:3124`, `:3221`, `:5211`) against the single definition
at `:5236`, so the definition does not orphan. The definition block is DB-owned (the `link-definitions` board
doc), not derived from card bodies, so no definition edit is owed either. Worker 2 re-confirms with
`grep -c "\[backlog\]" KANBAN.md` after the regenerate (expect a count above 1) and reports rather than acts if it
does not hold.

### Decision 3 — what else on card 054 is falsified, and the scope limit

**Nothing else on card 054 is falsified by this fact set.** The measured population is the two sites above.
`### Maintainer decision 3`'s scope limit is explicit — "card 054's two stale `CardItem` references in the DB plus
the regenerate. **No other sibling spec, no other card, no source file, and no test file becomes writable.**"

Three things a reader might reach for, and why each is **out of scope** and left alone:

- **The promotion-owner ambiguity** — the card's DoD says "Promote `Meta.fields_class` ... (per
  `TODO-BETA-058-0.1.3`)" while its Foundation-slice seam says this card "populates the slot and promotes the key
  end-to-end". `spec-054` `## Risks and open questions` records this as an open conflict with a pinned preferred
  answer (Decision 8). It is a genuine card-text conflict, it is **not** the `DjangoModelField` / item-38 fact,
  and resolving it is a maintainer contract call. Not touched; recorded here.
- **`KANBAN.md:79`'s item-38 reference** — correct as written (see the verification section above).
- **Every other card citing `TODO-BETA-054-0.1.1`** (cards 053, 055, 057, 058, 059, 030, 034, and the amendment
  rows) — none of them repeats the `DjangoModelField` claim. Measured as occurrences rather than matching lines
  (`grep -o "item 38" KANBAN.md | wc -l` -> **3**; `grep -c` agrees here only because no line carries two):
  `:79` (correct, see above), `:518`, and `:521` (sites A and B). There is no fourth site anywhere on the board.
  Out of scope and clean.

### Decision 4 — the concurrency constraint, and exactly what verification is and is not available

`### Maintainer decision 6` governs and has already been taken: **R3 proceeds** even though its clean-tree
precondition failed.

**State as of this planning pass** (Worker 2 re-checks and re-records; this reading is timestamped, not
authoritative):

```
 M KANBAN.html
 M KANBAN.md
 M docs/GLOSSARY.md
 M examples/fakeshop/db.sqlite3          # HEAD 6f8bf818, 191 dirty entries tree-wide
```

`git diff --numstat` over the three text files: `KANBAN.md` `0 1`, `KANBAN.html` `1 1`, `docs/GLOSSARY.md` `1 1`.
So a concurrent session is **actively writing the same DB** — it has already made glossary and card-item edits and
regenerated. This is the ordinary state `BUILD.md` `### Tracked binary / generated files` was written for.

**The concurrent writer is identifiable, which sharpens the hand-off.** `docs/builder/bld-014-r3-card_body_scope_fix.md`
(untracked, `Status: final-accepted`) is a **spec-014 residual cycle doing the same class of operation** — a card-body
correction on `DONE-014-0.0.4` through the kanban DB plus a regenerate, uncommitted and handed to the maintainer.
That is consistent with the single deleted `KANBAN.md` bullet and the single changed `KANBAN.html` data-block line.
Two consequences: (a) name that artifact in the maintainer hand-off block so the two card-body edits can be told
apart at commit; (b) **never edit, revert, or `git checkout` anything under `bld-014*` / `build-014*`** — it belongs
to the other cycle (`AGENTS.md` rule 34), exactly as the plan's spec-010 standing instruction requires.

**Rules, in force for the whole build pass:**

- **Apply the writes on top of the concurrent state.** Never revert, never `git checkout`, never `git stash`,
  never reset the DB, never restore any of the four paths. `BUILD.md` `### Tracked binary / generated files`
  licenses applying the writes on top and requires handing the mixed diff to the maintainer to reconcile at
  commit; `AGENTS.md` rule 34 forbids the auto-revert; the `git stash` / `checkout` / `restore` / `worktree` ban
  is repo-wide in this cycle.
- **`START.md`'s caution — "don't regenerate the rendered docs while another session's feature work is
  mid-flight" — is overridden for this item by `### Maintainer decision 6`, and only for this item.** The residual
  risk it names is real and must be *handled*, not ignored: **the regenerate publishes whatever the concurrent
  session has written into the DB but not yet rendered.** If extra hunks appear in `KANBAN.md` / `KANBAN.html`
  outside card 054, they are that session's work surfacing through R3's render. **Record them exactly and never
  revert them**; name them in the build report as not-ours so the maintainer can separate them at commit.
- **Two-consecutive-regenerate byte-stability cannot distinguish this cycle's write from the concurrent
  session's while theirs is in flight.** R3 **states that limitation** rather than claiming a verification it
  cannot perform. Write it into the build report in those terms; do not present a stable second regenerate as
  proof of authorship.
- **If the DB is locked** (`OperationalError: database is locked`) the concurrent writer holds it: wait and retry
  a small number of times, never force, and **stop-and-report** if it persists. Never delete a `-wal` / `-shm`
  file.

**What verification IS available, and is therefore required:**

1. **Exact-string identity on the two rows.** Re-read both `CardItem.text` values after `.save()` and assert
   equality against the two quoted replacements. This is authorship-attributable because the strings are this
   cycle's own text.
2. **A semantic DB diff scoped to the touched rows — `iterdump()`, never the binary.** For a SQLite DB the
   comparison is schema + rows (`BUILD.md` `### Tracked binary / generated files`). Capture **read-only** so the
   capture itself cannot churn the file, before and after the write:

   ```shell
   uv run python - <<'PY'
   import sqlite3, pathlib
   con = sqlite3.connect("file:examples/fakeshop/db.sqlite3?mode=ro", uri=True)
   rows = [line for line in con.iterdump() if "kanban_carditem" in line]
   pathlib.Path("<scratch>/carditem-before.sql").write_text("\n".join(rows) + "\n")
   print(len(rows))
   PY
   ```

   Repeat after the write to `<scratch>/carditem-after.sql` and `diff` the two. **Scratch paths live outside the
   repository** (use the session scratchpad directory). Expected: exactly two changed `INSERT INTO
   "kanban_carditem"` rows, carrying the two new texts and refreshed `updated_date` values. **Any third changed
   `kanban_carditem` row is the concurrent session's and is recorded, not reverted** — and if a third row appears
   *on card 054*, that is a **stop-and-report**.
3. **Render-vs-DB consistency at that instant.** After both regenerates, `uv run python
   scripts/build_kanban_md.py --check` and `uv run python scripts/build_kanban_html.py --check` must both exit 0
   ("up to date"). This proves the rendered files match the DB *now*; it proves nothing about who wrote what, and
   the build report must say so in that sentence.
4. **Per-region attribution against `HEAD`, which IS available for this card.** Card 054's rendered region is
   byte-identical between `HEAD` and the tree at planning time (proof command in the verification section above).
   So after the write, re-running that same read-only region diff must show **exactly the two replaced bullets and
   nothing else**. This is the strongest attribution instrument R3 has, and it is the one whole-file byte
   comparison cannot give. Re-derive the `HEAD` copy at build time — `HEAD` moves several times per pass in this
   tree, so never reuse this pass's `6f8bf818`.
5. **The mixed diff, handed over with the two intended changes named exactly.** The build report ends with a
   short block the maintainer can act on: the two `CardItem` texts before and after (quoted), the paths R3 wrote
   (`examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`), and an explicit list of every other hunk in
   those paths, labelled as the concurrent session's.

### Decision 5 — hot path, floor verification, failability, boundary count

Each stated rather than omitted.

- **Hot-path declaration: `none`.** This item changes two rows of documentation text in a fixture database and
  re-renders two generated documents. It adds no executable line, no serialization point, no per-request or
  per-row work — nothing runs in production as a result. `BUILD.md` `## Hot-path budget`'s "judge by what the code
  runs inside, not by diff size" is satisfied: there is no code. Worker 2 writes `Not applicable; plan declares no
  hot path.`
- **Floor-verification scope: `none`.** `BUILD.md` `### When it is required` scopes floor runs to slices touching
  a Django / Strawberry / channels integration seam. R3 touches none; the plan preamble's blanket `none` reaches
  it (unlike R1c, which needed an explicit amendment). A floor run could not distinguish pass from fail here.
  Worker 2 writes `Not applicable; plan declares floor-verification scope none.`
- **No failability proof is owed.** `BUILD.md` `### What needs a proof, and what does not` requires one for every
  **new boundary, guard, gate, or rejection path** a pass introduces. R3 introduces none — it edits prose in a
  database. Worker 2 writes `None; this pass introduced no new boundary.` in the `### Failability proofs`
  subsection, keeping the heading.
- **Boundary count: 0. Split question answered: no split.** The whole change is two `.save()` calls on one model
  in one section of one card plus two regenerates — one indivisible unit by both of `BUILD.md`
  `### Slice splitting`'s triggers (diff shape and boundary count). Splitting it would mean regenerating twice
  against a contended DB for no review benefit.
- **Static inspection helper: skipped, with reason.** `scripts/review_inspect.py` parses `.py` files. R3 adds no
  Python and touches no `.py` file, so the helper has no target (`BUILD.md` `### When to run the helper during
  build`).
- **Public surface: untouched.** No change to `django_strawberry_framework/__init__.py` or `__all__`.

### Implementation steps

Numbered for Worker 2. All commands run from the repository root. Line numbers cited anywhere in this artifact are
pin-at-write-time navigational hints — verify against the current tree before relying on one.

1. **Re-check and record the four DB-backed paths.** `git status --porcelain -- examples/fakeshop/db.sqlite3
   KANBAN.md KANBAN.html docs/GLOSSARY.md` and `git diff --numstat --` over the same set. Paste the raw output
   into the build report. Also record the current `HEAD` (`git rev-parse --short HEAD`) — re-derived, never copied
   from this plan. **Dirty is expected and is not a blocker** (`### Maintainer decision 6`); proceed.
2. **Baseline the render-vs-DB state BEFORE writing** — `uv run python scripts/build_kanban_md.py --check` and
   `uv run python scripts/build_kanban_html.py --check`, both read-only (they render in memory and compare; they
   write nothing). This is the check that distinguishes the two concurrency cases, and it is only available
   *before* the write: **both up to date** means the rendered files already match the DB, so R3's regenerate will
   surface R3's change and nothing else; **either stale** means un-rendered concurrent DB work is queued and R3's
   regenerate **will publish it** — record that prominently in the hand-off block rather than discovering it in
   the diff afterwards. Either outcome proceeds; neither is a blocker.
3. **Capture the read-only `iterdump()` baseline** scoped to `kanban_carditem`, to a scratch path outside the
   repository (snippet in `### Decision 4`). Record the row count.
4. **Capture the `HEAD` copy of card 054's rendered region**, read-only:
   `git show HEAD:KANBAN.md > <scratch>/KANBAN.head.md`, then the `awk` region extraction from
   `### The two references, re-verified`. Confirm it still matches the working tree's region before writing (if it
   does not, the concurrent session has touched card 054 since this plan — **stop and report**, do not write).
5. **Open the ORM shell** — `uv run python examples/fakeshop/manage.py shell` — and locate the two rows without
   assuming an `order` or `section` key:

   ```python
   from apps.kanban import models
   card = models.Card.objects.get(number=54)
   hits = list(card.items.filter(text__contains="item 38").order_by("section__order", "order"))
   for item in hits:
       print(item.pk, item.section.key, item.order, repr(item.text))
   ```

   Expect **exactly two** rows, both in the Foundation-slice-seam section. A count other than two is a
   **stop-and-report**.
6. **Verify live text before editing.** Assert each row's `text` equals the corresponding "Current `CardItem`
   text" block in `### Decision 1` / `### Decision 2` **character for character** (compare with `==` in the shell,
   not by eye). If either differs, the DB is not what this plan was written against — **stop and report**; do not
   edit, and do not adapt the replacement to a text you have not had reviewed.
7. **Apply Site A.** Set the row's `text` to `### Decision 1`'s replacement and call **plain `item.save()`** — not
   `save(update_fields=[...])`. Reason: `updated_date` is `auto_now`, and an `update_fields` list that omits it
   silently skips the timestamp; a plain save writes every field, fires `post_save` with `created=False` (so no
   spurious side-row), and is the path the importer contract assumes.
8. **Apply Site B** the same way, with `### Decision 2`'s replacement.
9. **Re-read both rows from the database in a fresh query** (`models.CardItem.objects.get(pk=...)`) and assert
   each `text` equals its intended replacement exactly. Record both assertions as passing in the build report.
10. **Regenerate**, repo root, in this order:
   `uv run python scripts/build_kanban_md.py` then `uv run python scripts/build_kanban_html.py`. Record both
   commands' stdout.
11. **Freshness check:** `uv run python scripts/build_kanban_md.py --check` and
    `uv run python scripts/build_kanban_html.py --check` — both exit 0. Record the output **and** the sentence
    that it proves render-vs-DB consistency at that instant, not authorship.
12. **Capture the after `iterdump()`** and `diff` it against step 3's baseline. Record the diff. Expected: exactly
    two changed `kanban_carditem` rows. Any additional changed row is the concurrent session's — record it, do not
    revert it; an additional changed row **on card 054** is a stop-and-report.
13. **Re-run the card-054 region diff against a freshly re-derived `HEAD` copy.** Expected output: exactly the two
    replaced bullets. Paste the diff verbatim.
14. **Rendered-content checks on `KANBAN.md`:** within card 054's region, `grep -c "item 38"` is **0**; both new
    bullet texts are present verbatim; the only surviving `DjangoModelField` mention is the rejection clause; and
    `grep -c "\[backlog\]" KANBAN.md` over the whole file is greater than 1 (the definition plus surviving uses).
15. **`KANBAN.html` check:** the data block carries both new strings. The block is JSON with
    `ensure_ascii=True` (`scripts/build_kanban_html.py::render_data_block`), so the em dashes appear escaped as
    the six-character sequence `\u2014` rather than literally — search for an ASCII-only fragment of each
    replacement (e.g. `pins resolver wrapping as the mechanism`) rather than the whole string.
16. **`uv run python examples/fakeshop/manage.py check`** — must pass. Record the output.
17. **`git status --short`** afterwards. Only `examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html` should be
    newly affected by this pass, on top of the recorded baseline. Anything unexpected is a **stop-and-report,
    never a revert** — this tree carries several concurrent sessions' uncommitted work, so `git checkout -- path`
    would destroy someone else's change.
18. **Write the maintainer hand-off block** described in `### Decision 4` item 5, and the explicit
    byte-stability-limitation statement. Then set `Status: built`.

### Test additions / updates

**None, and the reason is structural rather than an omission.** R3 writes no package source and no package
behavior; the changed content is documentation prose in a fixture database. `AGENTS.md` rule 10 ("test through
real usage") has no surface to attach to here — there is no line of `django_strawberry_framework/` reachable by a
GraphQL query that this item changes, and the coverage gate is scoped to `django_strawberry_framework` only
(rule 11), which this item does not touch.

The equivalent obligation is discharged by the verification steps above, which are executable and recorded rather
than asserted: the exact-string identity assertions (steps 6, 9), the semantic `iterdump()` diff (steps 3, 12),
the `HEAD`-region diff (steps 4, 13), the `--check` runs before and after (steps 2, 11), and `manage.py check`
(step 16).

**No `pytest` run is required or planned for this item**, and if any pass runs one it must carry **no `--cov*`
flags** (`BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool`). Do not run
`scripts/build_glossary_md.py`, `import_spec_terms`, or any migration.

### Implementation discretion items

Assessed and delegated — each is a genuine either/or with no correctness consequence:

- **Whether to do the edit in one `manage.py shell` session or via a here-doc piped into it.** Either is fine as
  long as it is the ORM and the commands and their output are recorded in the build report.
- **The exact scratch filenames** under the session scratchpad, provided they are outside the repository.
- **How the two rows are addressed** — by `pk` captured in step 4, or by re-filtering on a distinctive substring.
  Either is fine; the exact-equality check in step 5 is what makes it safe.
- **Whether the `iterdump()` capture filters on `kanban_carditem` or on the two `pk` values.** Narrower is
  cleaner; both satisfy "scoped to the rows it touched" as long as the diff is recorded.

Everything about *what the text says*, *what is in scope*, and *what may not be reverted* is decided in this plan
and is not discretionary.

### Dispatched findings checklist

One box per contract Worker 2 must land. Worker 2 ticks `- [x]` only where the contract actually landed in this
pass and states any deferral in the build report; Worker 3 walks the list during review; Worker 1 audits every
tick at final verification.

- [x] All four DB-backed paths (`examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`)
      re-checked immediately before writing, with their raw `git status --porcelain` / `--numstat` state and the
      freshly re-derived `HEAD` recorded in the build report.
- [x] Both build scripts' `--check` run **before** the write and their result recorded, so the build report can
      say whether un-rendered concurrent DB work was queued at that moment (either outcome proceeds).
- [x] Read-only `iterdump()` baseline captured to a scratch path **outside the repository**, scoped to the rows
      R3 touches.
- [x] Both target `CardItem` rows located through the ORM from `Card.objects.get(number=54)`, and their **live
      `text` verified character-for-character against `### Decision 1` / `### Decision 2`'s "current" blocks
      before any edit** (mismatch = stop-and-report, not an adapted edit).
- [x] Site A's `CardItem.text` replaced with `### Decision 1`'s replacement text exactly, written through the
      Django ORM with a plain `.save()` — never raw SQL, never `update_fields`.
- [x] Site B's `CardItem.text` replaced with `### Decision 2`'s replacement text exactly, same mechanism.
- [x] Both rows re-read from the database in a fresh query and asserted equal to their intended replacements.
- [x] `KANBAN.md` regenerated from the repository root with `uv run python scripts/build_kanban_md.py`.
- [x] `KANBAN.html` regenerated from the repository root with `uv run python scripts/build_kanban_html.py`.
- [x] After-`iterdump()` captured and diffed against the baseline; the diff recorded, and any row beyond the two
      intended ones recorded as the concurrent session's rather than reverted.
- [x] Card 054's rendered region diffed against a freshly re-derived `HEAD` copy, showing **exactly the two
      replaced bullets and nothing else on that card**; the diff pasted verbatim.
- [x] Rendered-content checks recorded: `item 38` count 0 within card 054; both replacement strings present in
      `KANBAN.md`; the only surviving `DjangoModelField` mention is the rejection clause; `[backlog]` still used
      elsewhere; both new strings present in `KANBAN.html`'s data block.
- [x] `uv run python examples/fakeshop/manage.py check` passes, and `git status --short` afterwards shows only
      expected paths — anything unexpected reported, never reverted.
- [x] The build report **states explicitly** that two-consecutive-regenerate byte-stability cannot distinguish
      this cycle's write from the concurrent session's while theirs is in flight, and records what was verified
      instead (exact-string identity, scoped semantic DB diff, per-card `HEAD`-region diff, `--check` freshness).
- [x] The maintainer hand-off block written: the two intended `CardItem` changes named exactly (before/after), the
      three paths R3 wrote, and every other hunk in those paths labelled as the concurrent session's.

### Standing constraints inherited by the builder

- **Never edit, revert, or `git checkout` any concurrent file.** `git stash`, `git checkout`, `git restore`, and
  `git worktree` are banned repo-wide for this cycle. Diff against `git show HEAD:<path>` into a scratch path
  outside the repo instead.
- **Only the maintainer commits.** Never commit, never create or switch a branch, never amend or force-push.
- **Do not touch any spec, any source file, any test file, `docs/GLOSSARY.md`, `docs/TREE.md`, `CHANGELOG.md`,
  `BACKLOG.md`, or any other card.** R3's writable set is: `examples/fakeshop/db.sqlite3` (two `CardItem.text`
  values only), the two generated files as **regenerate output only**, this artifact, and Worker 2's own
  namespaced memory file `docs/builder/worker-memory/spec-009-worker-2.md`.
- **Do not read another worker's memory file**, the un-namespaced `worker-<N>.md` files, or another cycle's
  namespace.
- **No card status flips, no `SpecDoc` rows, no glossary rows, no `import_spec_terms`.** Card 054 stays `TODO`.
- **Never hand-edit `KANBAN.md` or `KANBAN.html`** — the next regenerate silently reverts it, and a hand edit that
  survives into a commit desynchronizes the board from its source of truth.

---

## Build report (Worker 2)

Steps 1-18 of `### Implementation steps` ran in order, from the repository root. No step was skipped and no
stop-and-report condition fired. The scratch root used throughout is the session scratchpad, **outside the
repository**: `/private/tmp/claude-501/-Users-riordenweber-projects-django-strawberry-framework/fc7d0b3d-4cfd-4ed0-a153-22f1402f6dfd/scratchpad`.

### Files touched

Grounded in `git status --short`, not memory.

- `examples/fakeshop/db.sqlite3` — **two `CardItem.text` values on card 054, and nothing else.** `kanban_carditem`
  `pk=316` (section `foundation_seam`, `order=1`) and `pk=839` (section `foundation_seam`, `order=4`). Written
  through the Django ORM with a plain `.save()`. This file was already dirty at pass start under a concurrent
  writer; R3's two rows are applied **on top** of that state, never reverting it.
- `KANBAN.md` — **regenerate output only** (`uv run python scripts/build_kanban_md.py`). Never hand-edited. The
  regenerate published R3's two bullets and nothing else; the file was already dirty with one concurrent-session
  deletion (see `### Notes for Worker 3`, "the mixed diff").
- `KANBAN.html` — **regenerate output only** (`uv run python scripts/build_kanban_html.py`). Never hand-edited.
  The Vue shell was not touched; only the marked data block changed.
- `docs/builder/bld-009-r3-card054_db_references.md` — this build report appended, the 15
  `### Dispatched findings checklist` boxes ticked, top-level `Status:` set to `built`. The `## Plan (Worker 1)`
  section was not edited.
- `docs/builder/worker-memory/spec-009-worker-2.md` — one appended entry (untracked).

**Not touched, and confirmed so:** `docs/GLOSSARY.md` (dirty at pass start and at pass end with an identical
`1 1` numstat — the diff is entirely a concurrent session's auth-glossary rewrite); every spec; every source and
test file; `BACKLOG.md`; `docs/TREE.md`; `CHANGELOG.md`; every other card; every `SpecDoc` and glossary row. No
card status was flipped — card 054 remains `TODO`. `import_spec_terms`, `scripts/build_glossary_md.py`, and every
migration command were not run.

### Tests added or updated

**None**, per the plan's `### Test additions / updates`, and the reason is structural rather than an omission:
this item writes no package source and changes no package behavior. The changed content is documentation prose in
a fixture database, so there is no line of `django_strawberry_framework/` for a test to reach and nothing enters
the coverage gate's scope (`AGENTS.md` rules 10 and 11). The equivalent obligation is discharged by the executable,
recorded verification below rather than by asserted prose.

No `pytest` run was required, planned, or performed. No `--cov*` flag was used anywhere in this pass.

### Validation run

**Ruff: not applicable — this pass touched no `.py` file inside the repository.** The two ORM scripts it executed
(`r3_verify.py`, `r3_apply.py`) live in the out-of-repo session scratchpad and are not repository files, so a
`ruff format` / `ruff check --fix` invocation would have had no in-repo target. Running either on `.` is forbidden
by `worker-2.md` step 5 and would have reformatted several concurrent sessions' uncommitted work.

**Step 1 — the four DB-backed paths, re-checked immediately before writing** (raw output, and the `HEAD` freshly
re-derived rather than copied from the plan):

```
$ git rev-parse --short HEAD
6f8bf818

$ git status --porcelain -- examples/fakeshop/db.sqlite3 KANBAN.md KANBAN.html docs/GLOSSARY.md
 M KANBAN.html
 M KANBAN.md
 M docs/GLOSSARY.md
 M examples/fakeshop/db.sqlite3

$ git diff --numstat -- examples/fakeshop/db.sqlite3 KANBAN.md KANBAN.html docs/GLOSSARY.md
1	1	KANBAN.html
0	1	KANBAN.md
1	1	docs/GLOSSARY.md
-	-	examples/fakeshop/db.sqlite3

$ git status --porcelain | wc -l
     192
```

All four dirty, exactly as `### Maintainer decision 6` anticipated. **Dirty is not a blocker for this item**; the
pass proceeded and applied its writes on top. The state matches the plan's timestamped reading in `### Decision 4`
row for row, so no concurrent writer changed the picture between planning and building.

**Step 2 — the pre-write `--check` baseline. This is the load-bearing concurrency measurement and it came back
clean:**

```
$ uv run python scripts/build_kanban_md.py --check
/Users/riordenweber/projects/django-strawberry-framework/KANBAN.md is up to date.      # exit 0
$ uv run python scripts/build_kanban_html.py --check
/Users/riordenweber/projects/django-strawberry-framework/KANBAN.html is up to date.    # exit 0
```

**Both up to date before the write, which is the favourable branch of the plan's two cases: the rendered files
already matched the DB, so no un-rendered concurrent DB work was queued and R3's regenerate could only surface
R3's own change.** Had either been stale, the regenerate would have published another session's un-rendered work
and this report would be saying so loudly instead. The post-write diff confirms the prediction: `KANBAN.md`'s
numstat moved `0 1` -> `2 3`, i.e. exactly R3's two replaced lines were added to the pre-existing single
concurrent deletion, and no third hunk appeared.

**Step 3 — read-only `iterdump()` baseline**, captured through a `mode=ro` URI so the capture itself cannot churn
the DB, scoped to `kanban_carditem`, written outside the repository: **1280 rows**.

**Step 4 — `HEAD` copy of card 054's rendered region, re-derived read-only** (`git show HEAD:KANBAN.md` into
scratch; no `git checkout` / `stash` / `restore` / `worktree` anywhere in this pass):

```
$ diff <(awk '/^### \[TODO-BETA-054/,/^<a id="metasearch_fields_support"/' <scratch>/KANBAN.head.md) \
       <(awk '/^### \[TODO-BETA-054/,/^<a id="metasearch_fields_support"/' KANBAN.md)
                       # no output — region still byte-identical to HEAD; safe to write
```

**Steps 5-6 — the two rows located through the ORM and their live text verified before any edit.**
`Card.objects.get(number=54)` -> `pk=16`, title `` `FieldSet` ``.
`card.items.filter(text__contains="item 38").order_by("section__order", "order")` -> **exactly 2** rows:

| pk | section | order | live `len(text)` | equals the plan's "current" block? |
|---|---|---|---|---|
| 316 | `foundation_seam` | 1 | 307 | **True** (`==`, not by eye) |
| 839 | `foundation_seam` | 4 | 446 | **True** |

The comparison was made in Python with `==` against constants, and the constants themselves were then verified
mechanically rather than transcribed by eye: a script parsed the four ```` ```text ```` fences out of this
artifact and compared each against the constant the apply script would use —

```
fenced text blocks: 4
block[0] == CURRENT_A: True  (len art=307 mine=307)
block[1] == REPLACEMENT_A: True  (len art=296 mine=296)
block[2] == CURRENT_B: True  (len art=446 mine=446)
block[3] == REPLACEMENT_B: True  (len art=869 mine=869)
```

So both the *current* text (DB vs plan) and the *replacement* text (plan vs what was written) are byte-exact by
measurement. Nothing in this pass was improvised.

**Steps 7-9 — the two writes and the fresh re-read** (`uv run python examples/fakeshop/manage.py shell` fed the
apply script; plain `item.save()`, never `update_fields`, never raw SQL):

```
saved A pk= 316
saved B pk= 839
A re-read equals REPLACEMENT_A: True
B re-read equals REPLACEMENT_B: True
A len: 296 B len: 869
```

The re-read is a fresh `models.CardItem.objects.get(pk=...)` query, not the in-memory instance.

**Step 10 — regenerate**, repo root, markdown then HTML:

```
$ uv run python scripts/build_kanban_md.py
Wrote 69 cards (excluded 1 backlog cards) and 15 board docs to .../KANBAN.md          # exit 0
$ uv run python scripts/build_kanban_html.py
Wrote 70 cards, 15 board docs, and 11 lookup arrays to .../KANBAN.html                # exit 0
```

**Step 11 — post-write freshness**, both exit 0 (`KANBAN.md is up to date.`, `KANBAN.html is up to date.`).
**This proves render-vs-DB consistency at that instant. It proves nothing about authorship** — it says the two
rendered files match the database as it stands now, not who wrote which row of it.

**Step 12 — after-`iterdump()` diffed against the step-3 baseline.** Row count unchanged (1280 -> 1280). The diff
is **exactly two changed rows, both R3's**, each carrying its new text and a refreshed `updated_date`
(`2026-08-16 11:26:32`), with `created_date` untouched:

```
261c261
< INSERT INTO "kanban_carditem" VALUES(316,...,'2026-05-30 16:27:12.544593','...(see also [`BACKLOG.md`][backlog] item 38 for the `DjangoModelField` custom Strawberry field class...',1,0,16,3,NULL,NULL,NULL);
---
> INSERT INTO "kanban_carditem" VALUES(316,...,'2026-08-16 11:26:32.455196','...(no custom Strawberry field class is required for it; spec-054 Decision 11 pins resolver wrapping as the mechanism that carries the gate).',1,0,16,3,NULL,NULL,NULL);
768c768
< INSERT INTO "kanban_carditem" VALUES(839,...,'2026-07-20 21:35:17.956971','Custom Strawberry field class ... See [`BACKLOG.md`][backlog] item 38 for the `DjangoModelField` direction.',4,0,16,3,NULL,NULL,NULL);
---
> INSERT INTO "kanban_carditem" VALUES(839,...,'2026-08-16 11:26:32.456414','Custom Strawberry field class ... a custom `DjangoModelField` field class is unnecessary machinery for the same reason.',4,0,16,3,NULL,NULL,NULL);
```

**No third changed `kanban_carditem` row appeared**, on card 054 or anywhere else — so no concurrent write landed
in that table during this pass's window. (The full untruncated diff was read in the terminal; the middles are
elided here only for width.)

**Step 13 — card-054 region diff against a freshly re-derived `HEAD` copy** (`HEAD` re-read as `6f8bf818` at this
point, not reused from the plan). **Exactly the two replaced bullets and nothing else on that card** — this is the
strongest attribution instrument available for this item, and it is clean:

```
44c44
< - `Meta.fields_class` moves out of `DEFERRED_META_KEYS` only when the field-level permission / custom-resolver / computed-field machinery is applied end-to-end (see also [`BACKLOG.md`][backlog] item 38 for the `DjangoModelField` custom Strawberry field class that field-level permissions will likely require).
---
> - `Meta.fields_class` moves out of `DEFERRED_META_KEYS` only when the field-level permission / custom-resolver / computed-field machinery is applied end-to-end (no custom Strawberry field class is required for it; spec-054 Decision 11 pins resolver wrapping as the mechanism that carries the gate).
47c47
< - Custom Strawberry field class — django-graphene-filters' `AdvancedFieldSet` works with a custom field type that carries the `check_<field>_permission` gate at resolve time. Strawberry's `strawberry.field(...)` already supports a `permission_classes` argument; the spec must decide between mapping `check_<field>_permission` onto that machinery or carrying a parallel gate. See [`BACKLOG.md`][backlog] item 38 for the `DjangoModelField` direction.
---
> - Custom Strawberry field class — django-graphene-filters' `AdvancedFieldSet` works with a custom field type that carries the `check_<field>_permission` gate at resolve time. That question is settled without one: spec-054 pins **resolver wrapping** as the mechanism (Decision 11 — the wrapper captures the generated resolver and delegates to it as the cascade's step 3), upstream-parity and zero-config with zero overhead on unmanaged fields. Mapping the gate onto Strawberry's `strawberry.field(permission_classes=...)` is likewise rejected: `BasePermission.has_permission(source, info, **kwargs)` is class-per-policy with a fixed message contract, cannot host the gate-then-override cascade ordering, and would synthesize a permission class per managed field for no consumer benefit; a custom `DjangoModelField` field class is unnecessary machinery for the same reason.
```

**Step 14 — rendered-content checks on `KANBAN.md`.** Counted as occurrences (`grep -o | wc -l`), never as
matching lines:

| Check | Result |
|---|---|
| `item 38` **within card 054's region** | **0** |
| `DjangoModelField` within card 054's region | **1**, and it is the rejection clause: *"a custom `DjangoModelField` field class is unnecessary machinery for the same reason"* |
| `item 38` **whole file** | **1** — `KANBAN.md:79` only, the correct test-policy reference the plan ruled out of scope (was 3 before this pass) |
| Replacement A present verbatim | yes (1) |
| Replacement B present verbatim | yes (1) |
| `[backlog]` whole file | **8** occurrences over 7 lines (`:65`, `:79`, `:340` x2, `:3124`, `:3221`, `:5211`, plus the definition at `:5236`) — well above 1, so the definition does not orphan |

**The predicate deliberately used is "zero `item 38` on card 054", never "zero `DjangoModelField`"** — the plan's
`### Decision 2` keeps `DjangoModelField` in the replacement as a recorded rejection, so the latter check would
have failed on a correct result.

**Step 15 — `KANBAN.html` data block.** Searched on ASCII-only fragments, because the block is JSON with
`ensure_ascii=True` and the em dashes render as the six-character escape sequence rather than literally:
`pins resolver wrapping as the mechanism` -> 1,
`unnecessary machinery for the same reason` -> 1, and the old `item 38 for the ` string -> **0**. The Vue shell
outside `<!-- KANBAN_DATA_START -->` was not touched (the file's whole diff is one changed line, which is the
single-line data block).

**Step 16 — `uv run python examples/fakeshop/manage.py check`:**

```
System check identified no issues (0 silenced).      # exit 0
```

**Step 17 — `git status --short` afterwards.** The four DB-backed paths, and the tree-wide dirty count, are
**unchanged in membership** from the step-1 baseline — no path became newly dirty as a result of this pass:

```
$ git status --porcelain -- examples/fakeshop/db.sqlite3 KANBAN.md KANBAN.html docs/GLOSSARY.md
 M KANBAN.html
 M KANBAN.md
 M docs/GLOSSARY.md
 M examples/fakeshop/db.sqlite3

$ git diff --numstat -- examples/fakeshop/db.sqlite3 KANBAN.md KANBAN.html docs/GLOSSARY.md
1	1	KANBAN.html
2	3	KANBAN.md        # was 0 1 — the delta is exactly R3's two replaced lines
1	1	docs/GLOSSARY.md # unchanged: R3 never touched it
-	-	examples/fakeshop/db.sqlite3

$ git status --porcelain | wc -l
     192              # unchanged from the step-1 baseline
```

**Nothing unexpected appeared, so no stop-and-report was owed and nothing was reverted.** Had anything unexpected
appeared it would be recorded here, never `git checkout`-ed away — this tree carries several concurrent sessions'
uncommitted work.

### Failability proofs

None; this pass introduced no new boundary.

R3 edits two prose strings in a fixture database and re-renders two generated documents. It adds no guard, gate,
rejection path, or invariant — nothing that can say "no" — so `BUILD.md` `### What needs a proof, and what does
not` scopes it out. Boundary count: 0, as the plan's `### Decision 5` declared.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- **The verification-then-apply split was run as two separate ORM shell invocations, not one.** The plan left the
  shape to discretion. Two invocations means the character-for-character check against the plan's "current" blocks
  completed and was *read* before any `.save()` existed in the process — a single script would have made the check
  and the write one atomic unit whose stop-and-report branch nobody had eyes on. The apply script re-asserts both
  current-text equalities anyway (as `assert` statements before the first `.save()`), so the guard is present in
  both places.
- **The four replacement/current constants were verified against this artifact's fenced blocks by a parser, not by
  reading.** Transcription is exactly where a byte-exact contract fails silently, and the plan's own instruction is
  that Worker 2 does not improvise the text. The check cost one command and is quoted above.
- **Rows were addressed by `pk` captured from the verification pass** (316, 839) and re-filtered by the same
  distinctive-substring query in the apply pass, with the count re-asserted as 2. Discretion item; belt and braces
  because a concurrent writer could in principle have changed the population between the two invocations.
- **The `iterdump()` capture filters on the `kanban_carditem` table rather than the two `pk` values.** Discretion
  item, and the wider scope is the deliberate choice: it is what makes "no third `kanban_carditem` row changed"
  a measured statement rather than an untested assumption, which is precisely the concurrency question this item
  needs answered.
- **The two board-doc counts in the regenerate output differ between the scripts** (`69 cards (excluded 1 backlog
  cards)` for markdown, `70 cards` for HTML). That is the scripts' own pre-existing behavior — the markdown render
  excludes backlog cards and the HTML dashboard includes them — not an artifact of this pass, and both `--check`
  runs pass afterwards.

### Notes for Worker 3

- **The regenerate could not have published concurrent work, and that is measured rather than assumed.** Both
  `--check` runs were clean *before* the write (step 2 above), which is the only moment that distinguishes "the
  render already matches the DB" from "un-rendered concurrent work is queued". They were clean, so the regenerate
  had nothing of anyone else's to publish. The `0 1` -> `2 3` numstat move on `KANBAN.md` independently confirms it.
- **Two-consecutive-regenerate byte-stability cannot distinguish this cycle's write from the concurrent session's
  while theirs is in flight, and this report does not claim it does.** The usual DB-backed verification instrument
  is unavailable here, so no stable second regenerate is presented as proof of authorship anywhere above. What was
  verified instead, and each is authorship-attributable or scoped: (1) **exact-string identity** on both rows
  against this cycle's own text, asserted on a fresh re-read query; (2) a **semantic `iterdump()` diff scoped to
  `kanban_carditem`**, showing exactly two changed rows and no third; (3) a **per-card region diff against a
  freshly re-derived `HEAD`**, showing exactly the two replaced bullets and nothing else on card 054; (4) the
  **`--check` freshness runs**, which prove render-vs-DB consistency at an instant and nothing about who wrote
  what.
- **The mixed diff, and which hunks are not R3's.** `KANBAN.md` carries one deletion R3 did not make and must not
  revert — a bullet at `KANBAN.md:~4479` on a *different* card, opening "remove the tests.fixtures.apps fixture
  app + unmanaged cardinality fixtures". It was already absent at pass
  start and is the concurrent **`spec-014` residual cycle**'s work (`docs/builder/bld-014-r3-card_body_scope_fix.md`,
  untracked, `Status: final-accepted`). `docs/GLOSSARY.md`'s entire diff — an auth-entry rewrite about
  `SessionMiddleware` requirements — is likewise another session's and R3 never opened the file. `KANBAN.html`'s
  single changed line is the data block, which necessarily carries both cycles' card text at once because it is
  one line. **None of it was touched, reverted, or `git checkout`-ed.**
- **Scope discipline worth re-checking against the diff:** the plan's `### Decision 3` names three things
  deliberately left alone — the card's promotion-owner ambiguity between its DoD and its Foundation-slice seam
  (a maintainer contract call, `spec-054` Decision 8), `KANBAN.md:79`'s item-38 reference (correct as written), and
  every other card citing `TODO-BETA-054-0.1.1`. The region diff above shows none of them moved.
- **No `git stash` / `checkout` / `restore` / `worktree` was run at any point.** Every HEAD reference in this pass
  is `git show HEAD:<path>` into an out-of-repo scratch path, and every DB read is through a `mode=ro` URI.

### Notes for Worker 1 (spec reconciliation)

**No spec amendment is owed by this pass, and no plan-vs-implementation drift occurred.** The plan was correct in
every structural particular that was testable: both rows existed, both lived in `foundation_seam`, both live texts
matched the quoted "current" blocks character-for-character, the population was exactly two, the card's rendered
region was still byte-identical to `HEAD` at write time, and the ORM-plus-regenerate mechanics behaved as
described. Nothing required a decision the plan had not already made.

Two observations for final verification, neither an amendment:

- **The plan's favourable concurrency branch is the one that occurred.** `### Decision 4` and `### Maintainer
  decision 6` were written to survive either case; the pre-write `--check` came back clean, so the weaker
  "R3's regenerate will publish someone else's queued work" contingency never fired and no hand-off caveat about
  it is needed. If Worker 1 re-runs anything to confirm, the re-derivable check is the `0 1` -> `2 3` numstat move
  on `KANBAN.md` plus the card-054 region diff.
- **The `spec-014` residual cycle's artifact is `final-accepted` and uncommitted in this same tree**, editing a
  different card's body through the same DB and the same two generated files. It is named in the hand-off block
  below so the maintainer can separate the two card-body edits at commit. It is out of scope for this cycle in
  both directions: R3 did not touch it, and it must not be reverted to tidy R3's diff.

### Maintainer hand-off

**R3 wrote exactly three paths:** `examples/fakeshop/db.sqlite3` (two `CardItem.text` values), `KANBAN.md`
(regenerate output), `KANBAN.html` (regenerate output). Plus this artifact and Worker 2's memory file.

**The two intended `CardItem` changes, named exactly.** Both on card `TODO-BETA-054-0.1.1` (`Card` `pk=16`,
`number=54`), section `foundation_seam`:

**`CardItem` `pk=316`** (`order=1`) — before (307 chars):

```text
`Meta.fields_class` moves out of `DEFERRED_META_KEYS` only when the field-level permission / custom-resolver / computed-field machinery is applied end-to-end (see also [`BACKLOG.md`][backlog] item 38 for the `DjangoModelField` custom Strawberry field class that field-level permissions will likely require).
```

after (296 chars):

```text
`Meta.fields_class` moves out of `DEFERRED_META_KEYS` only when the field-level permission / custom-resolver / computed-field machinery is applied end-to-end (no custom Strawberry field class is required for it; spec-054 Decision 11 pins resolver wrapping as the mechanism that carries the gate).
```

**`CardItem` `pk=839`** (`order=4`) — before (446 chars):

```text
Custom Strawberry field class — django-graphene-filters' `AdvancedFieldSet` works with a custom field type that carries the `check_<field>_permission` gate at resolve time. Strawberry's `strawberry.field(...)` already supports a `permission_classes` argument; the spec must decide between mapping `check_<field>_permission` onto that machinery or carrying a parallel gate. See [`BACKLOG.md`][backlog] item 38 for the `DjangoModelField` direction.
```

after (869 chars):

```text
Custom Strawberry field class — django-graphene-filters' `AdvancedFieldSet` works with a custom field type that carries the `check_<field>_permission` gate at resolve time. That question is settled without one: spec-054 pins **resolver wrapping** as the mechanism (Decision 11 — the wrapper captures the generated resolver and delegates to it as the cascade's step 3), upstream-parity and zero-config with zero overhead on unmanaged fields. Mapping the gate onto Strawberry's `strawberry.field(permission_classes=...)` is likewise rejected: `BasePermission.has_permission(source, info, **kwargs)` is class-per-policy with a fixed message contract, cannot host the gate-then-override cascade ordering, and would synthesize a permission class per managed field for no consumer benefit; a custom `DjangoModelField` field class is unnecessary machinery for the same reason.
```

Nothing else on card 054 changed, and no other card, status, `SpecDoc` row, or glossary row was touched.

**Every other hunk in those paths is a concurrent session's and was deliberately left alone:**

| Path | Hunk | Owner |
|---|---|---|
| `KANBAN.md` | the deleted bullet at `:~4479`, opening "remove the tests.fixtures.apps fixture app + unmanaged cardinality fixtures", on a **different card** | the concurrent **`spec-014`** residual cycle — `docs/builder/bld-014-r3-card_body_scope_fix.md`, `Status: final-accepted`, uncommitted |
| `KANBAN.html` | the single data-block line necessarily carries **both** cycles' card text, since it is one line | shared: R3's two strings + `spec-014`'s deletion |
| `docs/GLOSSARY.md` | the whole diff (auth entry, `SessionMiddleware` wording) | another concurrent session; **R3 never opened this file** |
| `examples/fakeshop/db.sqlite3` | binary; R3's semantic contribution is the two `kanban_carditem` rows above and **nothing else in that table** (measured by scoped `iterdump()` diff). Other tables were not inspected and may carry concurrent work | mixed |

**The verification limitation, stated plainly:** two-consecutive-regenerate byte-stability cannot distinguish this
cycle's write from the concurrent session's while theirs is in flight, so it is not offered as evidence anywhere
above. The substitutes actually run are exact-string identity on both rows, a scoped semantic DB diff, a per-card
`HEAD`-region diff, and the `--check` freshness runs — the first three of which are authorship-attributable, and
the last of which is explicitly not.

---

## Review (Worker 3)

Every claim below was re-derived read-only against the working tree. No `git stash` / `checkout` / `restore` /
`worktree` was run; every `HEAD` reference is `git show HEAD:<path>` into an out-of-repo scratch path, and every
database read is through a `mode=ro` URI. `HEAD` is still `6f8bf818` and the tree-wide dirty count is still 192,
so the tree has not moved since the build pass.

**Two verification instruments this pass had that the build report did not, and both were used.** Worker 2 could
only difference its own window (baseline captured *after* the concurrent session's write had already landed). This
review differences **`HEAD` to now** instead, which spans both cycles, and it differences the **whole database**
rather than one table. That converts several of Worker 2's scoped statements into stronger ones.

### High:

None.

### Medium:

#### `spec-054`'s "Stale card reference" bullet is falsified by this pass, and the build report states the opposite

`docs/SPECS/spec-054-fieldset-0_1_1.md` `## Risks and open questions` #"Stale card reference" opens, in the present
tense: *"The card's Foundation-slice seam cites \"BACKLOG.md item 38 for the `DjangoModelField` custom Strawberry
field class\", but item 38 in today's `BACKLOG.md` is the layered manual-relation-override *test policy*"*. As of
this pass that sentence describes a card that no longer exists. Measured, board-wide, over `CardItem.text`:

| Population | at `HEAD` | now |
|---|---|---|
| `item 38` in any `CardItem` | 2 (both card 54: `pk` 316, 839) | **0** |
| `DjangoModelField` in any `CardItem` | 2 (both card 54) | 1 (card 54 `pk` 839, the rejection clause) |

So `spec-054` is now the **only** document in the repository asserting that the card carries the stale citation —
the inbound reference this pass retired, unretired at its source. `grep -rn --include='*.md' "item 38"` returns
five sites; `BACKLOG.md:1914`, `docs/GLOSSARY.md:2116` and `KANBAN.md:79` are the correct test-policy references,
`docs/builder/build-009-…md:130` is this cycle's own dispatch record (a per-cycle artifact quoting before-text,
correct as a record), and `docs/SPECS/spec-054-fieldset-0_1_1.md:800-803` is the falsified one.

**Why it matters, specifically.** `### Maintainer decision 3` exists on the standing instruction *"since we did
not fix every inbound reference in the same change last time, do that now"*. This pass fixed site 3 and created a
new inbound reference of exactly the class the instruction names. `spec-054` is a live design document for
unbuilt work (`TODO-BETA-054-0.1.1`), so the next reader of that bullet will go looking for a card citation that
was removed.

**What was in Worker 2's power and was not done.** `### Notes for Worker 1 (spec reconciliation)` states **"No
spec amendment is owed by this pass"**. That sentence is falsified by the same fact. Worker 2 correctly did not
*edit* `spec-054` — `### Maintainer decision 3`'s scope limit is explicit that no other sibling spec becomes
writable, and the plan's `### Spec status-line re-verification` re-pins it — but recording the consequence is not
an edit, and its absence is why this had to be found in review rather than read in the report.

**Recommended change:** none inside this item's writable set. Escalated to Worker 1 with resolution paths under
`### Notes for Worker 1 (spec reconciliation)` below. **This finding does not hold the pass** (`worker-3.md`
`### Acceptance gate`, the escalation carve-out): closing it requires widening `### Maintainer decision 3`'s scope
limit, which is a maintainer call, not Worker 2's.

### Low:

#### "no concurrent writer changed the picture" is scoped wider than its evidence

`### Validation run` step 1 concludes: *"The state matches the plan's timestamped reading in `### Decision 4` row
for row, so no concurrent writer changed the picture between planning and building."* The four-path rows do match
row for row. The tree-wide count in the two readings does not: the plan's `### Decision 4` records **191 dirty
entries tree-wide**, the build report's step 1 records **192**. So one path elsewhere in the tree did go dirty
between planning and building, and "the picture" as written reaches it.

Harmless to the item's correctness — the four DB-backed paths are the only ones R3's protocol depends on, and
they are unchanged — but it is a negative-population claim one clause wider than the measurement beneath it,
which is the defect class this cycle has closed seventeen-plus times. **Recommended change:** scope the sentence
to the four DB-backed paths and state the `191 -> 192` tree-wide move alongside it.

**Disposition: recorded, not held.** The correction is one clause in a per-cycle artifact that closes with the
cycle, the underlying measurement is already present and correct in both passes, and no shipped surface is
affected. Routed to Worker 1 to apply or dismiss at final verification (`worker-3.md`: file the Low, record its
disposition, do not hold the pass).

### DRY findings

- **No code duplication is possible in this diff** — the pass wrote no Python. `scripts/review_inspect.py` was
  **skipped** for the same reason (it parses `.py` files and this diff contains none); the skip matches the plan's
  `### Decision 5` and is recorded here per `worker-3.md` `## Static helper use`.
- **One real duplication, deliberate, raised rather than held: the 869-character replacement is a near-copy of
  `spec-054`'s own rejection rationale.** Clause-for-clause, replacement B restates
  `## Risks and open questions` #"Stale card reference" (the `permission_classes` rejection, the
  `BasePermission.has_permission` shape, the "class-per-policy with a fixed message contract" phrase, the
  "unnecessary machinery for the same reason" clause — that last one verbatim) plus one detail lifted from
  `### Decision 11`. The rejection rationale now lives at **three** sites: the spec's risks bullet, the spec's
  Decision 11 / `## Borrowing posture` pair, and this card item.
  - **Existence challenge, answered rather than escalated.** The alternative shape — a bare pointer
    ("resolved by `spec-054` `## Risks and open questions`") — was weighed and loses. The board renders to
    `KANBAN.html` for a reader who is not holding the spec open, the adjacent bullet in the same section already
    carries its own inline rationale (`"(spec-034 Decision 2 — the structural mirror of the shipped
    filterset_class / orderset_class slots)"`), and the plan's `### Decision 2` reasoned the call explicitly. The
    abstraction earns its place; no maintainer decision is needed.
  - **But the coupling is exactly what produced the Medium above.** Three copies of one rationale, with no
    back-pointer from the spec to the card, is why fixing the card silently staled the spec. Worth Worker 1
    weighing whether the spec bullet should become a pointer at the card rather than a restatement of it.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty** (0 bytes of diff). `__all__` and the re-export
list are unchanged. No public export was added, removed, or renamed — consistent with the plan's
`### Decision 5` ("Public surface: untouched") and with a pass that wrote no Python.

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md`. Verified mechanically: `git diff -- CHANGELOG.md` is 0 bytes.

### Documentation / release sanity

**Applies** — this is a KANBAN board diff. Read end-to-end and confirmed:

- **Card IDs and statuses.** Card `TODO-BETA-054-0.1.1` (`kanban_card` `pk=16`, `number=54`) is **byte-identical
  to `HEAD`**, including `status_id` and `updated_date` (`2026-07-20`, i.e. `auto_now` never fired on the `Card`
  row). No card moved column or section: the `KANBAN.html` data block's per-card non-item fields are identical for
  all 70 cards, and `boardDocs` / `lookups` compare equal. Card 054 still carries 27 items at `HEAD` and now.
- **No card moved sections, and nothing appears twice.** Both edited items stayed in `section_id=3`
  (`foundation_seam`) at `order` 1 and 4 — unchanged from `HEAD`.
- **Markdown links.** Both replacements *remove* their only link and introduce none, so there is no new link to
  resolve. The `[backlog]` definition does not orphan: 8 occurrences over 7 lines (`:65`, `:79`, `:340` x2,
  `:3124`, `:3221`, `:5211`, definition `:5236`) — six live uses remain. `uv run python
  scripts/check_trailing_commas.py --check KANBAN.md` exits **0**, so the link-definition scaffold and layout
  rules survive the regenerate (and the file's numstat was unchanged by that run, confirming it was read-only).
- **Spec-citation convention.** The replacements cite `spec-054` bare rather than reference-style. That is the
  board's dominant form (hundreds of bare `spec-NNN` mentions against ten reference-style ones) and it matches the
  *immediately adjacent* bullet in the same section, `"(spec-034 Decision 2 — …)"`. Convention-consistent, not
  drift.
- **Verbatim-copy check.** ARTIFACT.md's char-for-char `diff`-against-spec item does not apply as written: this
  text is a deliberate paraphrase, not a drop-in. Discharged the equivalent obligation instead — a clause-by-clause
  read of both replacements against `spec-054`, recorded under `### What looks solid`. No fenced code is involved,
  so the four-backtick outer-fence case does not arise.
- **No staging language introduced.** Neither replacement contains `planned`, `Slice N`, `TODO(`, `coming soon`,
  or the retired `will likely require`. The card's remaining forward-looking wording ("moves out of
  `DEFERRED_META_KEYS` only when…") is correct: the card is `TODO` and the key is still deferred.
- **Version strings and release metadata.** None touched — no `pyproject.toml`, no `__version__`, no
  `CHANGELOG.md`, no `docs/TREE.md`.
- **Script-rendered doc discipline.** `KANBAN.md` / `KANBAN.html` were regenerated from the DB, never hand-edited
  — proved below, not accepted on prose.

### What looks solid

- **The replacement text says what `spec-054` actually settled, checked against the spec rather than the plan's
  paraphrase.** Clause by clause: *"captures the generated resolver and delegates to it as the cascade's step 3"*
  against `### Decision 11` #"delegates to it as cascade step 3" and `## Borrowing posture` #"captures and
  delegates to the prior resolver as the cascade's step 3"; *"upstream-parity and zero-config with zero overhead
  on unmanaged fields"* against the risks bullet's "(upstream-parity, zero-config, zero-overhead on unmanaged
  fields)" and `## Borrowing posture` #"only managed fields get wrapped"; the whole `permission_classes` rejection
  against the risks bullet, near-verbatim. **Nothing is invented and no direction is asserted that the spec does
  not hold.** The one narrowing — Decision 11's "original (generated or transplanted) resolver" rendered as
  "generated resolver" — is a narrowing, not a falsification.
- **The third-party claim the card now makes as fact checks out.** `BasePermission.has_permission` really is
  `(self, source, info, **kwargs) -> bool | Awaitable[bool]` in the installed Strawberry, and `BasePermission`
  really does carry a class-level `message` attribute — so "class-per-policy with a fixed message contract" is
  true of the library, not just repeated from the spec.
- **Site A's decision attribution holds, and it is the sentence most at risk in this diff.** *"spec-054 Decision
  11 pins resolver wrapping as the mechanism that carries the gate"* — `### Decision 11`'s body does state that
  the wrapper runs "the gate -> override -> default cascade", so the gate is carried there. Worth noting for the
  record that the *choice* of wrapping over the two alternatives is pinned in `## Risks and open questions` (and
  `### Decision 4` names "resolver wrapping" as a bind subpass), which is why site B's split attribution
  ("spec-054 pins … (Decision 11 — <shape detail>)") is the more precise of the two. Both are true as written.
- **The verification predicate is the correct one.** Worker 2 used "zero `item 38` on card 054", never "zero
  `DjangoModelField`", and said so explicitly. Re-derived: `item 38` on card 054 = **0**, `DjangoModelField` = **1**
  and it is the rejection clause. The inverted predicate would indeed have failed on this correct result.
- **Scope held, and this is now measured over the whole database rather than one table.** A `mode=ro`
  `iterdump()` of **every** table at `HEAD` versus now (9,883 -> 9,881 statements) differs in exactly two tables:
  `kanban_carditem` (3 `HEAD`-only / 2 now-only) and `kanban_uuidmodel` (1 `HEAD`-only, the side row of the
  concurrently-deleted item). **No `kanban_card` row, no `kanban_specdoc` row, and none of the ten `glossary_*`
  tables changed at all** — so "no card status flipped, no `SpecDoc` row touched, no glossary row touched,
  `import_spec_terms` not run" is proved, not asserted, and proved across the whole `HEAD`-to-now range rather
  than one pass's window.
- **The two-row claim is confirmed and sharpened.** Worker 2 reported 1280 `kanban_carditem` rows before and
  after with exactly two changed. Re-derived from `HEAD`: **1281 -> 1280**, three deltas — `pk=316` changed
  (R3), `pk=839` changed (R3), `pk=638` **deleted** (`card_id=36`, a *different* card, the `spec-014` cycle's).
  Worker 2's 1280-before is consistent because its baseline was captured after that deletion had landed. No
  third `kanban_carditem` row moved, on card 054 or anywhere.
- **The population was exactly two, verified by an unfiltered control rather than the plan's filter.** Querying
  the `HEAD` database directly for card-054 items containing `DjangoModelField`, `item 38`, `BACKLOG`, `backlog`,
  or the bare token `38` returns the **same two ids** for every token — and board-wide, `DjangoModelField`
  appeared in exactly those two `CardItem`s and nowhere else. There was no third site the plan's
  `text__contains="item 38"` filter could have missed.
- **Byte-exact text, re-derived independently in both directions.** A parser pulled the eight fenced `text`
  blocks out of this artifact and compared them against the live and `HEAD` databases: `HEAD` `pk=316` ==
  "current A", `HEAD` `pk=839` == "current B", live `pk=316` == "replacement A", live `pk=839` ==
  "replacement B" — all `True`, at 307 / 446 / 296 / 869 characters. The hand-off block's four quotations are
  also byte-identical to the plan's four, so the maintainer-facing before/after has not drifted from the
  reviewed text. Replacement A is pure ASCII (296 bytes); replacement B carries two em dashes and nothing else
  non-ASCII (869 chars / 873 bytes).
- **Per-region attribution re-derived against a freshly re-derived `HEAD`.** `git show HEAD:KANBAN.md` into
  scratch, `awk` region extraction, `diff`: **exactly two changed lines** (region-relative 44 and 47) in a
  77-line region, and nothing else on the card.
- **The rendered markdown is intact.** The `#### Foundation-slice seam` section renders as five well-formed
  single-line `- ` bullets; the 869-character replacement did not break the list, the inline `**resolver
  wrapping**` emphasis and the backticked `strawberry.field(permission_classes=...)` /
  `BasePermission.has_permission(source, info, **kwargs)` spans render as intended, and the section boundaries
  either side (`#### Definition of done` above, `#### Architectural posture` below) are untouched.
- **`KANBAN.html`'s data block carries the same text, and carries nothing else.** The block was parsed as JSON
  at `HEAD` and now and compared **by item identity** rather than by position — which is what the single-line
  diff cannot show. Result: 70 cards both sides with identical card numbers, `boardDocs` equal, `lookups` equal,
  `blockingReferenceKindKeys` equal, **zero cards with changed non-item fields**, one item removed (638, card 14,
  the `spec-014` cycle's), zero items added, and **exactly two items with changed text: 316 and 839, both card
  54.** The ASCII-fragment counts hold too (`pins resolver wrapping as the mechanism` -> 1,
  `unnecessary machinery for the same reason` -> 1, `item 38 for the ` -> 0).
- **`manage.py check` re-run: `System check identified no issues (0 silenced).`**, exit 0. Both `--check`
  freshness runs re-run and both exit 0 (`KANBAN.md is up to date.`, `KANBAN.html is up to date.`). Confirmed
  read-only two ways: `main()` in both build scripts returns from the `args.check` branch before any
  `write_text` / `embed_dashboard_data`, and the four paths' `--numstat` and the tree-wide dirty count were
  identical before and after these runs.
- **Neither generated file was hand-edited.** Both `--check` runs passing after the fact is the mechanical proof:
  a hand edit would make the on-disk file differ from the in-memory render of the DB.

### Temp test verification

- **No temp tests were created under `docs/builder/temp-tests/r3/`**, and the directory was not used. Nothing in
  this item is a testable code behavior — the correct instruments are database and file differencing, not
  `pytest` — and `### Test additions / updates`'s structural reason for adding no permanent test holds on review:
  the pass changes no line of `django_strawberry_framework/`, so nothing enters the `fail_under = 100` scope
  (`AGENTS.md` rules 10 and 11).
- Verification ran as `uv run python` here-docs writing only to the out-of-repo session scratchpad
  (`…/scratchpad/w3r3/`: `db.head.sqlite3`, `KANBAN.head.md`, `KANBAN.head.html`, `carditem-head.sql`,
  `carditem-now.sql`). Nothing was written inside the repository by this review except this section and
  `docs/builder/worker-memory/spec-009-worker-3.md`.
- **No `pytest` was run, and no `--cov*` flag was used anywhere in this review.**

### Notes for Worker 1 (spec reconciliation)

- **Escalated (Medium): `docs/SPECS/spec-054-fieldset-0_1_1.md:800-803` now describes a card state this pass
  removed.** Resolution paths, for the maintainer to pick between:
  1. **Widen `### Maintainer decision 3`'s scope limit by one bullet** and let Worker 1 rewrite the spec's
     "Stale card reference" bullet into the past tense (*"the card's Foundation-slice seam cited … ; corrected in
     the spec-009 residual cycle"*), keeping the rejection rationale that follows it, which is still live and is
     what the card now quotes. Cheapest, and it is what the standing instruction behind decision 3 asks for.
  2. **Record it as a follow-up** on card 054 or in the cycle's `R4` documentation-obligations sweep, accepting
     one stale sentence in an unshipped spec until then.
  3. **Leave it**, on the reading that the bullet is a historical record of a conflict ("Recorded here per the
     conflict rule rather than silently reconciled") rather than a present-tense claim. I do not recommend this:
     the sentence is present-tense as written, and the card it points at is the one thing a reader will check.
  Whichever path is taken, `### Notes for Worker 1 (spec reconciliation)`'s sentence **"No spec amendment is owed
  by this pass"** should be read as scoped to `spec-009` — it is not true of `spec-054`.
- **Low, routed for disposition:** the `191 -> 192` tree-wide scope slip in `### Validation run` step 1, above.
  One clause; apply or dismiss at final verification.
- **Observation, not a finding, and not R3's: `docs/GLOSSARY.md` is dirty with *no* backing change in the
  database.** The whole-DB `HEAD`-to-now comparison shows all ten `glossary_*` tables byte-identical, yet
  `docs/GLOSSARY.md` carries a one-line auth-entry diff. `docs/GLOSSARY.md` is rendered from those tables
  (`scripts/build_glossary_md.py` reads `allGlossaryTerms`), so the concurrent session's change is either a hand
  edit of a generated file or a DB write that was subsequently rolled back. This **refines** the hand-off table's
  `docs/GLOSSARY.md` row — Worker 2's ownership call ("another concurrent session; R3 never opened this file") is
  correct and is independently confirmed by the DB evidence, but the row is worth flagging to the maintainer as
  *unbacked* at commit time. R3 correctly did not touch it, and neither did this review.
- **Observation, out of scope, recorded so a later pass does not treat it as new:** card 054's
  `#### Definition of done` opens *"Add `docs/spec-054-fieldset-0_1_1.md`"*, but the spec lives at
  `docs/SPECS/spec-054-fieldset-0_1_1.md`. Pre-existing at `HEAD`, unaffected by this pass, and outside
  `### Maintainer decision 3`'s scope limit. The plan's `### Decision 3` claim that "nothing else on card 054 is
  falsified **by this fact set**" remains true as written — this is a different fact set.

### Review outcome

**`review-accepted`**, with one Medium transparently escalated to Worker 1 above (`worker-3.md`
`### Acceptance gate`: escalation is the right instrument when resolution requires spec-scope context Worker 2
could not supply — closing it means widening a maintainer scope limit) and one Low recorded with its disposition.

Walking the acceptance gate explicitly:

- **All 15 `### Dispatched findings checklist` boxes are ticked and every tick was audited against evidence.**
  Each one landed: the four paths re-checked and recorded raw; both pre-write `--check` runs recorded; the
  read-only `iterdump()` baseline captured outside the repo; both rows located through the ORM from
  `Card.objects.get(number=54)` with live text verified character-for-character; both replacements written by
  plain `.save()` (confirmed by the refreshed `updated_date` on both rows and untouched `created_date` — an
  `update_fields` list omitting the timestamp, or raw SQL, would have left `updated_date` at its old value);
  fresh re-read asserted; both regenerates run; the after-diff captured; the region diff pasted; the
  rendered-content checks recorded; `manage.py check` passing; the byte-stability limitation stated; the hand-off
  block written. No box is ticked without a matching fix, and none is silently unaddressed.
- **`### Failability proofs` — `None; this pass introduced no new boundary.` is correct, not a skipped
  obligation.** Audited rather than accepted: the diff's entire semantic content is two `TextField` values and
  two regenerate outputs. There is no guard, gate, limit, comparison, permission decision, or rejection path
  anywhere in it — nothing that can say "no", so there is nothing a mutation could remove and nothing a row could
  fail on. `BUILD.md` `### What needs a proof, and what does not` scopes it out. **The re-run floor is
  arithmetic and it computes to an empty set here, legally:** an empty re-run set is permitted exactly when the
  diff introduces no boundary meeting the floor, and boundary count is 0. Recorded per `worker-3.md`: **boundaries
  re-run — none; boundaries accepted on Worker 2's record — none, because there are none.** The fail-open-shape
  hunt has no target for the same reason (no computed input to a limit, size, or permission decision exists in
  this diff).
- **Hot-path budget and floor verification** are `Not applicable` per the plan's `### Decision 5`, and both are
  right: no executable line ships, and no Django / Strawberry / channels integration seam is touched, so a floor
  run could not distinguish pass from fail.
- **The recorded limitation is honest and its substitutes genuinely cover the gap.** Two-consecutive-regenerate
  byte-stability would answer *"is the rendered file a faithful function of the DB, and is that stable?"*. Its
  four substitutes cover strictly more: `--check` (re-run here, both exit 0) answers the faithfulness half
  directly; exact-string identity, the scoped semantic DB diff, and the per-card `HEAD`-region diff each answer
  the **authorship** half, which byte-stability never could — and this review's whole-DB and identity-keyed
  `KANBAN.html` comparisons close the two seams the four substitutes left open (other tables; the single-line
  HTML data block). The report correctly refuses to present `--check` as authorship evidence and says so in the
  same sentence, twice.
- **The `### Maintainer hand-off` block is precise enough to separate the two cycles at commit.** It names the
  three paths written, quotes both `CardItem` texts before and after (byte-identical to the plan's, verified),
  identifies the concurrent hunk by card, by opening words, and by owning artifact
  (`docs/builder/bld-014-r3-card_body_scope_fix.md`), and states plainly that the `KANBAN.html` data-block line
  is shared between both cycles. All of it re-derived and correct. The one caveat it draws honestly — *"Other
  tables were not inspected and may carry concurrent work"* — this review has now closed: **no other table
  carries any change at all** between `HEAD` and now.
- Public-surface check performed; CHANGELOG sanity not applicable and verified so; documentation / release
  sanity performed in full.

**On the load-bearing concurrency claim, stated plainly rather than accepted.** Worker 2's pre-write `--check`
transcript is **not re-derivable after the fact** — that state is gone, and no instrument available now can
reconstruct it. What is re-derivable is the *outcome* it was invoked to guarantee, and it is verified exhaustively:
between `HEAD` and now, `KANBAN.md`'s complete diff is two hunks (R3's two bullets; the `spec-014` deletion) with
no third; `KANBAN.html`'s data block differs by exactly those same three item-level facts and nothing else, by
identity-keyed comparison; and the database differs in two tables, both accounted for. **The regenerate published
no un-rendered third-party work, because there is no third-party content in the published files to be found.**
The numstat chain corroborates the mechanism: `0 1` recorded independently by Worker 1 at planning and by
Worker 2 at build, `2 3` now, the delta being exactly R3's two replaced lines. So the favourable branch is
confirmed by its consequences and by two independently-timed records of the pre-state, though not by replaying
the check itself — and the sole concurrent item that *is* published was already present at pass start, is named
in the hand-off block by card, text, and owner, and was correctly left alone.

---

## Final verification (Worker 1)

Every claim below was **re-derived**, never accepted from a prior section. Read-only throughout: no `git stash` /
`checkout` / `restore` / `worktree`, every `HEAD` reference is `git show HEAD:<path>` into the out-of-repo session
scratchpad (`.../scratchpad/w1r3/`), every database read is through a `mode=ro` URI, and no write of any kind
landed in `examples/fakeshop/db.sqlite3`, `KANBAN.md`, or `KANBAN.html`. This pass wrote exactly two files: this
section (plus the top-level `Status:` line) and `docs/builder/worker-memory/spec-009-worker-1.md`.

**Tree state at verification, re-derived rather than carried:** `HEAD` `6f8bf818`, tree-wide dirty count **192**,
and the four DB-backed paths `M KANBAN.html` / `M KANBAN.md` / `M docs/GLOSSARY.md` / `M
examples/fakeshop/db.sqlite3` at `--numstat` `1 1` / `2 3` / `1 1` / `- -`. Identical to the review pass, so the
tree did not move between review and final verification and every re-derivation below is against the same state
Worker 3 measured.

### Spec status-line re-verification

`docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md`'s header lines re-read this pass. Nothing in R3 falsifies
one: R3 edits no spec, and R1 / R1b / R1c / R2 are `final-accepted` and closed. **No spec edit was made by this
pass** — see `### Spec changes made (Worker 1 only)`.

### Scope, re-derived over the WHOLE database

Worker 3's whole-DB differencing reproduced independently, `HEAD` versus now, as a multiset comparison of
`iterdump()` statements:

| Measure | Result |
|---|---|
| Total statements, `HEAD` -> now | **9,883 -> 9,881** |
| Tables carrying any difference | **exactly two**: `kanban_carditem`, `kanban_uuidmodel` |
| `kanban_carditem` deltas | `pk=316` changed (R3), `pk=839` changed (R3), `pk=638` **deleted** |
| `kanban_uuidmodel` deltas | one `HEAD`-only row, `object_id=638` — the deleted item's side row |
| `kanban_card`, `kanban_specdoc`, all ten `glossary_*` tables | **zero differing statements** |

So "no card status flipped, no `SpecDoc` row touched, no glossary row touched, `import_spec_terms` not run" is
**proved**, not asserted, across the whole `HEAD`-to-now range rather than one pass's window. `pk=638` is
attributable to the concurrent `spec-014` cycle by evidence rather than by assumption: it belongs to `card_id=36`
(**card number 14**, *"Move test fixture out of example settings"*), a different card entirely, and its text opens
*"remove the `tests.fixtures.apps` fixture app + unmanaged cardinality fixtures"* — the bullet named in the
hand-off table.

**Row-level scope on card 054, also re-derived:** card `pk=16` (`number=54`) is **byte-identical** between `HEAD`
and now, `updated_date` included, so `auto_now` never fired on the `Card` row; the card carries **27** items on
both sides; both edited items kept `section_id=3` / `order` 1 and 4 / `is_complete=0` / `card_id=16`. Board-wide,
`item 38` appeared in exactly two `CardItem`s at `HEAD` (316, 839, both card 54) and in **zero** now;
`DjangoModelField` appeared in the same two and in **one** now (839, the rejection clause).

**Plain `.save()` is evidenced, not assumed:** both rows carry a refreshed `updated_date`
(`2026-08-16 11:26:32.455196` / `...456414`) against an untouched `created_date` (`2026-05-30 16:27:12.544589` /
`2026-06-02 00:09:05.108772`). Raw SQL or an `update_fields` list omitting the timestamp would have left
`updated_date` at its `HEAD` values (`2026-05-30 16:27:12.544593` / `2026-07-20 21:35:17.956971`).

### Byte-exact text, verified in both directions

A parser pulled the eight fenced ```` ```text ```` blocks out of this artifact and compared each against the
`HEAD` and live databases. All four identities hold, and the hand-off block's four quotations are byte-identical
to the plan's four (blocks 4-7 equal blocks 0-3), so the maintainer-facing before/after has not drifted from the
reviewed text:

```
block[0] (307) == HEAD pk=316   True      block[4] == block[0]  True
block[1] (296) == live pk=316   True      block[5] == block[1]  True
block[2] (446) == HEAD pk=839   True      block[6] == block[2]  True
block[3] (869) == live pk=839   True      block[7] == block[3]  True
```

### The load-bearing concurrency claim — verification-by-consequence IS sufficient here, and this is why

Worker 3 states plainly that Worker 2's pre-write `--check` transcript is **not re-derivable** and verifies the
outcome instead. **Judged explicitly, as this pass's own conclusion: the substitution is sound, and the closure
argument is stronger than either prior section states.** It rests on three re-derived facts, not on the transcript:

1. **The `HEAD`-to-now database delta is a closed set of three rows** (316, 839, 638) — measured over every table,
   above. Nothing else in the database differs from `HEAD` at all.
2. **Both `--check` runs pass right now** (re-run below), so the two rendered files are a faithful function of the
   database *as it currently stands*. Combined with (1), every byte of published content in `KANBAN.md` /
   `KANBAN.html` that differs from `HEAD` must derive from one of those three rows — the space of "un-accounted
   third-party content R3's regenerate might have published" is provably **empty**, not merely unobserved.
3. **The one third-party row that IS published was already published before R3 rendered anything.** `KANBAN.md`'s
   `--numstat` stood at `0 1` in two independently-timed records (Worker 1 at planning, Worker 2 at build step 1)
   and stands at `2 3` now; the delta is exactly R3's two replaced lines, and the deletion was already on disk in
   the tracked file at pass start. `docs/builder/bld-014-r3-card_body_scope_fix.md` is `final-accepted`, i.e. that
   cycle had already run its own regenerate.

The one scenario the outcome test could in principle miss — a concurrent write that landed after R3's baseline,
was published by R3's regenerate, and was then rolled back in the database without a re-render — is **excluded by
fact (2)**: such a rollback would leave the rendered file ahead of the database and `--check` would report stale.
It does not. (That failure mode is not hypothetical in this tree — `docs/GLOSSARY.md` is dirty with **no** backing
database change, which is exactly the unbacked-render shape. It is a different file, rendered by a different
script, and R3 never opened it; Worker 3's flagging of it for the maintainer is correct and is carried into the
summary below.)

Re-derived corroboration of the published surface:

- `KANBAN.md`, complete `HEAD`-to-now diff: **two hunks** at default context (`@@ -515,10 +515,10 @@` carrying
  R3's two bullets, `@@ -4477,7 +4477,6 @@` carrying the `spec-014` deletion), **three** changed content lines and
  no fourth. At `-U0` the first hunk resolves into `:518` and `:521` — the same two bullets, not a third change.
- `KANBAN.html` data block, parsed as JSON at `HEAD` and now and compared **by item identity** rather than by
  position: `boardDocs`, `lookups`, `blockingReferenceKindKeys` all equal; 70 cards both sides with identical
  numbers; **zero** cards with changed non-item fields; one item removed (`638`, card 14); zero items added; and
  **exactly two items with changed text — 316 and 839, both card 54** (changed keys `text` and `updatedDate`, and
  nothing else).
- Card 054's rendered region against a freshly re-derived `HEAD` copy: **exactly two changed lines** (region-
  relative 44 and 47) in a 77-line region.

### Substance — the replacements state what `spec-054` settled, and invent nothing

Re-checked against the spec rather than against the plan's paraphrase:
`### Decision 11` #"delegates to it as cascade step 3" and `## Borrowing posture` #"captures and delegates to the
prior resolver as the cascade's step 3" carry replacement B's wrapper clause; `## Borrowing posture`'s
"zero-overhead posture (only managed fields get wrapped — unmanaged fields keep their untouched resolvers)"
carries its zero-overhead clause; and `## Risks and open questions` #"Stale card reference" carries the whole
`permission_classes` rejection near-verbatim, the "unnecessary machinery for the same reason" clause included.
Site A's narrower attribution ("Decision 11 pins resolver wrapping as the mechanism that carries the gate") is
true as written — Decision 11's body runs the gate -> override -> default cascade through the wrapper — and
Worker 3's note that the *choice* between the three alternatives is pinned in `## Risks and open questions` is
recorded rather than treated as a defect.

**The deliberate-survival design is confirmed and the predicate is the correct one.** `DjangoModelField` survives
on card 054 exactly once, as the recorded rejection, so the verification predicate is *"zero `item 38` on card
054"* (re-derived: **0**) and never *"zero `DjangoModelField`"* (re-derived: **1**, correctly). The inverted
predicate would have failed on this correct result.

### Rendered output, re-run read-only

| Check | Result |
|---|---|
| `uv run python scripts/build_kanban_md.py --check` | `KANBAN.md is up to date.` exit **0** |
| `uv run python scripts/build_kanban_html.py --check` | `KANBAN.html is up to date.` exit **0** |
| `uv run python examples/fakeshop/manage.py check` | `System check identified no issues (0 silenced).` exit **0** |
| `uv run python scripts/check_trailing_commas.py --check KANBAN.md` | exit **0** |
| `item 38`, whole `KANBAN.md` | **1** — `:79` only, the correct test-policy reference the plan ruled out of scope |
| `item 38` / `DjangoModelField` within card 054's region | **0** / **1** (the rejection clause) |
| Both replacement strings present verbatim in `KANBAN.md` | yes, 1 each |
| `KANBAN.html` ASCII fragments | `pins resolver wrapping as the mechanism` 1, `unnecessary machinery for the same reason` 1, `item 38 for the ` **0** |
| `[backlog]` in `KANBAN.md` | **8 occurrences over 7 lines** (`:65`, `:79`, `:340` x2, `:3124`, `:3221`, `:5211`, definition `:5236`) — the definition does not orphan |

Both `--check` branches were confirmed read-only by source (`scripts/build_kanban_md.py` #"if args.check" and
`scripts/build_kanban_html.py` #"if args.check" both return before any `write_text` / `embed_dashboard_data`), and
by consequence: the tree-wide dirty count and all four `--numstat` rows are identical before and after every
command in this pass.

**Card-region coherence, read directly.** The `#### Foundation-slice seam` section renders as **six** well-formed
single-line `- ` bullets (`CardItem` `order` 0-5), the two replacements sitting at bullets 2 and 5. The
869-character replacement did not break the list, wrap, or re-flow — the renderer emits `- ` + `text.strip()` with
no wrapping, which the two-line region diff independently confirms. Section boundaries either side
(`#### Definition of done` above, `#### Architectural posture` below) are untouched.

### Dispatched findings checklist audit — 15 of 15 ticks confirmed against evidence

Every box audited against the diff and the re-derivations above, not against the build report's prose. **No box is
over-ticked and none is silently un-ticked; no deferral is owed.**

| # | Contract | Evidence this pass re-derived |
|---|---|---|
| 1 | Four paths re-checked, raw state + fresh `HEAD` recorded | Recorded raw in `### Validation run`; the state is unchanged now and reproduces row for row |
| 2 | Both `--check` run **before** the write and recorded | Recorded; transcript not re-derivable, outcome verified above and judged sufficient |
| 3 | Read-only `iterdump()` baseline outside the repository | Recorded (`mode=ro` URI, scratch path outside repo); its scope reproduced here |
| 4 | Rows located via `Card.objects.get(number=54)`, live text verified character-for-character | `HEAD` `pk=316`/`pk=839` == fenced blocks 0/2, `True` |
| 5 | Site A replaced exactly, ORM, plain `.save()` | live `pk=316` == block 1; `updated_date` refreshed, `created_date` untouched |
| 6 | Site B replaced exactly, same mechanism | live `pk=839` == block 3; same timestamp evidence |
| 7 | Both rows re-read in a fresh query and asserted equal | Recorded; the live-DB identities above are the same assertion re-run |
| 8 | `KANBAN.md` regenerated from the repository root | `--check` exit 0 + region diff shows exactly the two bullets |
| 9 | `KANBAN.html` regenerated from the repository root | `--check` exit 0 + identity-keyed JSON comparison |
| 10 | After-`iterdump()` diffed; any extra row recorded, not reverted | Whole-DB re-derivation: 316/839 R3's, 638 recorded as `spec-014`'s and still present as a deletion |
| 11 | Card-054 region diff against a fresh `HEAD`, pasted verbatim | Re-run: exactly lines 44 and 47 of 77 |
| 12 | Rendered-content checks recorded | Every row of the table above re-derived independently |
| 13 | `manage.py check` passes; `git status --short` shows only expected paths | Re-run, exit 0; four paths and dirty count unchanged |
| 14 | Byte-stability limitation stated, substitutes recorded | Stated twice (`### Notes for Worker 3`, `### Maintainer hand-off`); judged sufficient above |
| 15 | Maintainer hand-off block written | Present; its four quotations are byte-identical to the plan's, verified by parser |

**Required-amendment list (review-round custody):** Worker 3 recorded no on-disk required amendment for Worker 2 —
the Medium was escalated to Worker 1 by design and the Low was routed for disposition. Both are dispositioned
below, so nothing is recorded-and-not-implemented.

### Planned steps: all 18 landed, none rejected

`### Implementation steps` 1-18 each have a matching recorded outcome, and steps 2-4, 9, 11-17 were re-derived or
re-run above. No step was skipped, reinterpreted, or intentionally rejected, so no deferral reason is owed.
The plan's declared `none` results — hot path, floor verification, failability proofs, static inspection helper,
public surface — are each **correct rather than skipped obligations**: the diff's entire semantic content is two
`TextField` values and two regenerate outputs, so boundary count is 0 (nothing in it can say "no"), no executable
line ships, no Django / Strawberry / channels seam is touched, and `scripts/review_inspect.py` parses `.py` files
of which this diff contains none. `git diff -- django_strawberry_framework/__init__.py` and
`git diff -- CHANGELOG.md` are both 0 bytes.

### Shape consistency across R3's three passes

Checked, and it holds. All three passes use the same instruments in the same spellings — occurrence counts via
`grep -o | wc -l` rather than `grep -c`, `mode=ro` URIs for every database read, `git show HEAD:<path>` into an
out-of-repo scratch path for every `HEAD` reference, and the same `awk` region extraction. The plan's five
"what verification IS available" items map one-to-one onto the build report's evidence and onto the review's
re-derivations, and the review's two added instruments (whole-database differencing, identity-keyed
`KANBAN.html` comparison) are widenings of the plan's, not substitutes for them. No pass invented a section shape
outside `docs/builder/ARTIFACT.md`.

### No tests are owed — stated explicitly

**None, and structurally so rather than by omission.** This item writes no package source and changes no package
behavior; the changed content is documentation prose in a fixture database, so there is no line of
`django_strawberry_framework/` for a test to reach and nothing enters the `fail_under = 100` scope (`AGENTS.md`
rules 10 and 11). No `pytest` was run in this pass and no `--cov*` flag was used anywhere in the item.

**The staged-anchor sweep is not owed here either.** `worker-1.md` `## Final verification job` step 6 scopes it to
a doc-wrap or final in-spec slice; R3 is neither, and the cycle's `grep -rn 'TODO(spec-009' .` sweep is **R4's
declared contract** (build plan `## Checklist`, R4). Not run, deliberately, so R4's audit owns it undivided.

### Disposition of the escalated Medium — routed to R4, confirmed, with one correction to the routing

**The finding is real and was re-derived here.** `docs/SPECS/spec-054-fieldset-0_1_1.md:800-803` states in the
present tense that card 054's Foundation-slice seam *"cites 'BACKLOG.md item 38 for the `DjangoModelField` custom
Strawberry field class'"*. Measured board-wide: `item 38` in any `CardItem` was 2 at `HEAD` and is **0** now, so
the sentence describes a card state that no longer exists, and `spec-054` is the **only** document in the
repository still asserting it. This is precisely the class `### Maintainer decision 3` exists to prevent —
*"since we did not fix every inbound reference in the same change last time, do that now"* — re-created at the
other end by the fix itself.

**Worker 2's `### Notes for Worker 1 (spec reconciliation)` sentence "No spec amendment is owed by this pass" is
falsified by the same fact and must be read as scoped to `spec-009`.** Worker 2 was right not to edit `spec-054`
(the scope limit is explicit that no other sibling spec becomes writable) but recording the consequence was within
its power; that is why this surfaced in review rather than in the report. Recorded here as the correction, not as
a hold — it is one sentence in a per-cycle artifact that closes with the cycle, and the fact it misses is now
carried in three places (the review, this section, and the summary below).

**Worker 0's routing to R4 is CONFIRMED**, on three grounds:

1. **R4's contract is exactly this.** R4 is the cross-reference audit, and `## R4 inherits` already carries one
   clause of the identical class (the spec-009 rationale's stale `spec-028 ### Decision 12` claim, likewise
   falsified by this cycle's own work). Two instances of one class belong in one pass, audited together.
2. **R3 cannot close it, and must not.** `### Maintainer decision 3`'s scope limit is enumerated, `spec-054` is
   not in it, and self-fixing at acceptance would ship an unreviewed change through the one pass that has no
   reviewer after it. Re-opening R3 with a widened scope is worse still: its contract is discharged and its
   artifact is closing.
3. **The alternatives lose.** *Card it* — rejected on the same ground `### Maintainer decision 5` rejected it: the
   cycle can finish it, and the DB is contended. *Leave it as a historical record* — rejected because the sentence
   is present-tense as written and the card it points at is the first thing a reader will check.

**The one correction to the routing, and it matters at dispatch time: R4 inherits the item, but R4 cannot close it
on its own authority either.** `spec-054` is a sibling spec excluded by the same enumerated scope limit that binds
R3, and R4's own chain row says it *"writes only its artifact unless it finds a defect, which it escalates"*. The
`## R4 inherits` precedent does not transfer: that clause lives in
`docs/SPECS/appx/spec-009-…-rationale.md`, a file **this cycle already owns**. So R4 must carry this as a
maintainer scope question — Worker 3's resolution path 1, *widen `### Maintainer decision 3`'s scope limit by one
bullet* — on the `### Maintainer decision 7` precedent, where Worker 0 decided on the maintainer's standing
instruction and flagged it in the same turn. The standing instruction points squarely at path 1.

**Recommended shape for R4, so the fix is not re-litigated:** rewrite the `## Risks and open questions` "Stale
card reference" bullet into the past tense (*"the card's Foundation-slice seam cited … ; corrected in the spec-009
residual cycle"*) and **keep the rejection rationale that follows it** — that rationale is live, and is what the
card now quotes. Do **not** attempt to de-duplicate the rationale down to a single site: Worker 3's DRY note
correctly weighs and rejects a bare pointer on the card, because `KANBAN.html` renders for a reader who is not
holding the spec open, and the adjacent bullet in the same section already carries its own inline rationale. The
coupling worth adding instead is a **back-pointer from the spec bullet to card 054**, which is the thing whose
absence let a card fix silently stale the spec.

**Recorded, not written into the build plan.** `docs/builder/build-009-…md` is not in this pass's exhaustive
writable set, so `## R4 inherits` is unchanged and this section is the record Worker 0 and the maintainer act on.

### Disposition of the Low — corrected in the record, not held

`### Validation run` step 1's *"no concurrent writer changed the picture between planning and building"* is one
clause wider than its evidence. Re-derived: the four DB-backed paths do match the plan's reading row for row, but
the tree-wide dirty count moved **191 -> 192** between the two readings, so one path elsewhere in the tree did go
dirty. **The correction, for the record:** the claim holds for the four DB-backed paths R3's protocol depends on,
and the tree-wide count moved 191 -> 192 over the same interval. (It is still 192 now.)

**Not held, and not fixed in place.** Prior sections are not editable by this pass, the underlying measurements
are already present and correct in both passes, no shipped surface is affected, and `revision-needed` is for a
contract that did not land rather than for a wording slip in a per-cycle scratchpad that closes with the cycle.

### Three artifact-only imprecisions found by this pass, recorded and not fixed

Same disposition and same reason as the Low: prior sections are not editable here, none affects a shipped surface
or the item's conclusions, and all three are stated correctly in this section.

- **"1280 rows" / "1281 -> 1280 rows" are `iterdump()` *statement* counts, not row counts.** Both passes filtered
  `iterdump()` on lines *containing* `kanban_carditem`, which also matches the table's `CREATE TABLE`, its four
  `CREATE INDEX` statements, `kanban_uuidmodel`'s `CREATE TABLE`, and the `sqlite_sequence` insert — seven
  non-`INSERT` statements. Re-derived: matching statements **1281 -> 1280**, actual `kanban_carditem` rows
  **1274 -> 1273**. The delta reasoning both passes drew from it (one deleted row, two changed) is unaffected and
  correct.
- **`### Documentation / release sanity` says the `#### Foundation-slice seam` section renders as "five" bullets;
  it renders as six** (`order` 0-5), with the replacements at bullets 2 and 5 — which is what the plan's own site
  table said. The substantive claim (well-formed, single-line, list unbroken) re-derived as true.
- **The plan's `### Decision 2` reference-style link check under-counts `[backlog]`** as "five more times
  elsewhere (`:65`, `:79`, `:3124`, `:3221`, `:5211`)". The measured population is 8 occurrences over 7 lines —
  `:340` carries two uses neither the plan nor the build report's line list names. The check's predicate (a count
  above 1, so the definition does not orphan) is satisfied with room to spare, and the build report's measured
  count is the correct one.

### DRY across R3 and prior accepted items

No new duplication. R3 wrote no Python, so no code shape can repeat, and `scripts/review_inspect.py` was correctly
skipped for want of a target. The one real duplication — replacement B restating `spec-054`'s rejection rationale
at a third site — was raised by Worker 3, weighed against the bare-pointer alternative, and decided in the plan's
`### Decision 2` on grounds this pass re-checked and accepts (the board renders standalone; the adjacent bullet
carries inline rationale of the same shape). It is the *cause* of the escalated Medium, which is why the R4
recommendation above adds a back-pointer rather than a fourth copy or a de-duplication.

### Final status

`final-accepted`. Every contract in the `### Dispatched findings checklist` landed and was audited against
re-derived evidence; the scope proof, the substance check, and the concurrency judgement each hold; the Medium is
dispositioned to R4 with its routing confirmed and one correction; the Low and three artifact-only imprecisions
are corrected in this record.

### Summary

**What R3 shipped.** Two `CardItem.text` values on card `TODO-BETA-054-0.1.1` (`Card` `pk=16`, `number=54`,
section `foundation_seam`), written through the Django ORM with a plain `.save()`, plus the two regenerates that
publish them. Card 054 stays `TODO`; no card status, `SpecDoc` row, or glossary row moved, proved over the whole
database.

- **`CardItem` `pk=316`** (`order=1`, 307 -> 296 chars). Before: the `Meta.fields_class` bullet ended *"(see also
  [`BACKLOG.md`][backlog] item 38 for the `DjangoModelField` custom Strawberry field class that field-level
  permissions will likely require)"*. After: *"(no custom Strawberry field class is required for it; spec-054
  Decision 11 pins resolver wrapping as the mechanism that carries the gate)"*. The leading sentence is unchanged.
- **`CardItem` `pk=839`** (`order=4`, 446 -> 869 chars). Before: the "Custom Strawberry field class" bullet posed
  the choice as open (*"the spec must decide between …"*) and ended *"See [`BACKLOG.md`][backlog] item 38 for the
  `DjangoModelField` direction."*. After: the same opening clause verbatim, then the settled answer — resolver
  wrapping per `spec-054` Decision 11, with the `strawberry.field(permission_classes=...)` mapping and the custom
  `DjangoModelField` class both recorded as rejected and why. **`DjangoModelField` deliberately survives once, as
  a recorded rejection**, which is why the verification predicate is "zero `item 38` on card 054" (0) and not
  "zero `DjangoModelField`" (1, correctly).

Board-wide, `item 38` went from two `CardItem`s to none; the one surviving `KANBAN.md` mention (`:79`) is the
correct test-policy reference and was deliberately left alone.

**The favourable concurrency branch occurred, and how it was corroborated.** Both build scripts' `--check` came
back *up to date* **before** the write, so R3's regenerate could only publish R3's own change. That transcript is
not re-derivable after the fact; the outcome it guarantees is, and it was verified three ways here: the whole
`HEAD`-to-now database delta is a closed set of three rows; both `--check` runs still pass, so the rendered files
are a faithful function of that database; and `KANBAN.md`'s `--numstat` chain (`0 1` recorded independently at
planning and at build, `2 3` now) shows the single concurrent hunk was already on disk before R3 rendered.
**Nothing of another session's was published by this cycle.**

**Scope proof.** `iterdump()` `HEAD` -> now, whole database: 9,883 -> 9,881 statements differing in exactly two
tables — `kanban_carditem` (316 and 839 changed by R3; 638 deleted by the concurrent `spec-014` cycle) and
`kanban_uuidmodel` (638's side row). `kanban_card`, `kanban_specdoc`, and all ten `glossary_*` tables are
untouched. `manage.py check` passes; both `--check` runs pass; `check_trailing_commas.py --check KANBAN.md`
passes.

**For the maintainer at commit time — read `### Maintainer hand-off` above; this cycle's write is NOT the only one
in these files.** `examples/fakeshop/db.sqlite3`, `KANBAN.md`, and `KANBAN.html` carry a **concurrent `spec-014`
residual cycle's card-body edit** as well as R3's: the deleted bullet at `KANBAN.md:~4479` on **card 14**
(*"remove the `tests.fixtures.apps` fixture app + unmanaged cardinality fixtures"*, `CardItem` `pk=638`), owned by
`docs/builder/bld-014-r3-card_body_scope_fix.md` (untracked, `Status: final-accepted`). `KANBAN.html`'s
single-line data block necessarily carries **both** cycles' text at once. The hand-off block names each hunk and
its owner exactly. Two further notes for that moment: `docs/GLOSSARY.md` is dirty with **no backing change in the
database** (all ten `glossary_*` tables are byte-identical to `HEAD`), so that diff is either a hand edit of a
generated file or a rolled-back write by another session — R3 never opened it; and nothing in these three paths
may be reverted to tidy either cycle's diff.

**Open and routed, not fixed here:** `docs/SPECS/spec-054-fieldset-0_1_1.md:800-803` now describes a card state
this pass removed. Routed to **R4** with the routing confirmed, plus the correction that R4 needs a one-bullet
widening of `### Maintainer decision 3`'s scope limit to close it, since `spec-054` is a sibling spec excluded by
the same enumerated limit that bound R3.

### Spec changes made (Worker 1 only)

**None.** R3 edits no spec by contract, and `spec-009`'s status lines are unfalsified by this item. The one spec
sentence this item's work *does* falsify — `docs/SPECS/spec-054-fieldset-0_1_1.md:800-803` — is outside
`### Maintainer decision 3`'s enumerated scope limit and is routed to R4 with a maintainer scope question, as
recorded above. No checklist box is left `- [ ]`, so no deferral reason is owed under this heading.
