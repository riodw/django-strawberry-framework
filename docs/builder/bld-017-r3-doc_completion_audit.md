# Build: Round R3 — documentation completion and archive audit (spec-017)

Spec reference: `docs/SPECS/spec-017-deferred_scalars-0_0_6.md`
Rationale companion: `docs/SPECS/appx/spec-017-deferred_scalars-0_0_6-rationale.md`
Build plan: `docs/builder/build-017-deferred_scalars-0_0_6.md`
Predecessor artifact: `docs/builder/bld-017-r1-rationale_and_spec_reconciliation.md` (`final-accepted`)
Shape: **procedural-closure** (`docs/builder/BUILD.md` `### Procedural-closure slices`) — one combined Plan + Final-verification block. No Worker 2 build and no Worker 3 review runs on this round.
Status: final-accepted

## Plan (Worker 1) + Final verification (Worker 1)

### Spec status-line re-verification

Read at the start of this spawn (`docs/builder/worker-1.md` `## Spec status-line re-verification`). Lines 1-9 read `Target release: 0.0.6.` / `Status: shipped in 0.0.6.` / `Owner: package maintainer.` / `Predecessors: …` / `Card line: …` plus R1's rationale pointer. Nothing this round falsifies any of them; **no edit made**.

### DRY analysis

- **Helper inventory checked.** Not applicable in its usual form: this round writes Markdown only and proposes no helper, shared constant, validation branch, coercion utility, or test helper — the package-wide AST inventory has nothing to prevent. The read-only reading this round performed is recorded per surface below.
- **Existing patterns reused.** The maintainer follow-up shape reuses the amendment precedent already present on this very card: the `BigAutoField` note bullet was previously amended in place to `"no override recourse at the time; annotation-override recourse now available via DONE-019-0.0.6"`. The replacement text below follows that pattern — state what `0.0.6` shipped, then state what superseded it — rather than deleting the historical record.
- **New helpers justified.** None.
- **Duplication risk avoided.** One real risk: `CardItem` id 715 and `CardReference` id 62 carry **byte-identical** text (the reference row mirrors the note bullet). Amending one and not the other would leave the card self-contradicting in the rendered output. The follow-up below names both rows as one atomic edit.

### Boundary count

Zero. This round adds no guard, cap, rejection path, or validation branch. No split question arises.

### Hot-path declaration

**None.** This round writes Markdown only. (Build plan's declaration, unchanged.)

### Floor-verification scope

**None.** This round touches no Django / Strawberry / channels integration seam. The floor, quoted from `docs/builder/BUILD.md` `## Floor verification` rather than from memory, is **Django 5.2.16 on Python 3.10 with strawberry-graphql 0.316.0**. No pass in this round needed the shared `.venv`'s own versions, so none were read or restated.

### Failability proofs

None; this round introduced no new boundary.

### Dispatched findings checklist

One box per doc surface the reconciled spec's Slice 6, `## Doc updates`, and `## Definition of done` name. Ticked when a disposition was established with a citation.

- [x] `docs/GLOSSARY.md` — `BigInt scalar` entry
- [x] `docs/GLOSSARY.md` — `Specialized scalar conversions` entry
- [x] `docs/GLOSSARY.md` — `Scalar field conversion` entry
- [x] `docs/GLOSSARY.md` — `Public exports` entry
- [x] `docs/GLOSSARY.md` — `Index` status badges for the two flipped entries
- [x] `docs/README.md` — the `**Shipped today**` line and the specialized-scalar callout placement
- [x] Root `README.md` — the package-version line
- [x] `docs/TREE.md` — `scalars.py` in both layouts
- [x] `TODAY.md` — the four new scalars in the field-conversion section
- [x] `CHANGELOG.md` — the `[0.0.6]` entry
- [x] `KANBAN.md` — the `DONE-017-0.0.6` card body
- [x] Archive audit — spec + two companions, link resolution, `check_spec_glossary`, pre-archive path sweep

---

## Obligation 1 — disposition per doc surface

Dispositions are **(a)** correct and current, **(b)** stale, **(c)** not applicable / already satisfied.

### `docs/GLOSSARY.md` — all five surfaces: **(a)**

R1 flagged the `Public exports` and `BigInt scalar` entries as *suspected* carriers of suppression wording and asked R3 to confirm rather than assume. Confirmed: **none of the five is stale.** A repo-wide `grep -n -i 'suppress\|catch_warnings\|deprecation' docs/GLOSSARY.md` returns no scalar-registration hit; every `suppress` occurrence in the file belongs to an unrelated entry (revocation frames, `.only(...)` under mutations, relation-shape suppression, Relay pk suppression).

| Entry | Disposition | Proof |
|---|---|---|
| `BigInt` scalar | (a) | `docs/GLOSSARY.md #"Consumers register `BigInt` via the [`strawberry_config`](#strawberry_config) factory"` — states the shipped registration path, no suppression claim. Status line reads `shipped (0.0.6)`. |
| Specialized scalar conversions | (a) | `docs/GLOSSARY.md #"PostgreSQL `HStoreField` → `strawberry.scalars.JSON` (soft-registered"` and `#"`PositiveBigIntegerField` → `BigInt`"` — both the Slice 6 replacement line and the `PositiveBigIntegerField` flip are in place; status `shipped (0.0.6)`. |
| Scalar field conversion | (a) | `docs/GLOSSARY.md #"`PositiveBigIntegerField` switched from `int` to `BigInt` in `0.0.6` — breaking wire-format change"`, plus the `JSONField`, `ArrayField`, and `HStoreField` bullets. |
| Public exports | (a) | `docs/GLOSSARY.md #"- [`BigInt`](#bigint-scalar) — JSON-safe scalar for 64-bit integer fields."`; the section's closing note reads `#"the registration path uses Strawberry's no-warning `strawberry.scalar(name=..., serialize=..., parse_value=...)` overload via the [`strawberry_config`](#strawberry_config) factory, so no `DeprecationWarning` is emitted"` — the **corrected** form of the Slice 6 sentence, not the suppression form. |
| `Index` status badges | (a) | `docs/GLOSSARY.md #"\| [`BigInt` scalar](#bigint-scalar) \| shipped (`0.0.6`) \|"` and `#"\| [Specialized scalar conversions](#specialized-scalar-conversions) \| shipped (`0.0.6`) \|"`. |

### `docs/README.md` — **(a)**

- Slice 6 sub-check "update the `Shipped today` line": `docs/README.md #"**Shipped today** (`0.0.14`):"`. The literal `0.0.6` target is superseded by seven later cuts; the line is current for the package's actual version (`pyproject.toml #"version = \"0.0.14\""`).
- Slice 6 sub-check "move specialized scalar conversions out of the `Coming in 0.1.0` callouts": already done. `docs/README.md #"- specialized scalar conversions (`BigIntegerField` / `PositiveBigIntegerField` → `BigInt`"` sits inside the **Shipped today** list, and no `Coming in` / `planned` callout in the file names a scalar conversion (grep of `coming in|planned` intersected with `scalar|json|array|hstore|bigint` returns only two mutation bullets that mention scalar *converters* in passing, both shipped-state).
- The file already documents the shipped registration path (`config=strawberry_config()` in eight code samples), so it makes no claim this card's contract falsifies.

**No edit made.** The surface is current about this card's contract, and `START.md`'s no-"while I'm here" rule forbids touching it for anything else.

### Root `README.md` — **(a)**

Slice 6's only obligation here is the package-version line. `README.md #", single-maintainer, alpha-quality."` reads `**`0.0.14`, single-maintainer, alpha-quality.**`, matching `pyproject.toml` and `django_strawberry_framework/__init__.py`. The file mentions no scalar conversion at all, so it carries no stale spec-017 claim. **No edit made.**

### `docs/TREE.md` — **(a)** for this card's surface; `--check` fails for a reason outside this cycle

- Both Slice 6 sub-checks are satisfied: `scalars.py` appears in the current on-disk layout **and** the target package layout, in both cases described as `# Public GraphQL scalars + the ``strawberry_config()`` schema-config factory.` — the post-`DONE-025-0.0.7` description, not a suppression-era one. The feeding docstring carries no staging language.
- `uv run python scripts/build_tree_md.py --check` → **exit 1**, `docs/TREE.md is not up to date`. Diagnosed **read-only**, without regenerating in place: `docs/TREE.md` was copied to a scratch path outside the repo and the renderer pointed at the copy via `--md`, then diffed. The entire drift is two lines, both the same entry in the two layouts:

```
<     ├── converters.py             # Fail-loud converter-dispatch skeleton shared by the form + serializer converters.
>     ├── converters.py             # Fail-loud converter-dispatch skeleton shared by write-field and filter-input converters.
```

  That is `django_strawberry_framework/utils/converters.py`'s module docstring, which is on the build plan's `## Baseline-dirty out-of-scope files` list — a concurrent session's live edit. **Not this cycle's drift, not this cycle's to fix or revert** (`AGENTS.md` rule 34). Nothing about `scalars.py` differs between the on-disk file and a fresh render. **No edit made** (the file is script-rendered; `--check` only, per the round's scope).

### `TODAY.md` — **(a)**

Slice 6's obligation was to expand "What fakeshop model fields work today" with the four new scalars. All four are present and post-`0.0.6`-accurate:

- `TODAY.md #"`BigIntegerField` / `PositiveBigIntegerField` → `BigInt`"`
- `TODAY.md #"`JSONField` → `strawberry.scalars.JSON`"`
- `TODAY.md #"PostgreSQL `ArrayField` → `list[T]`"`
- `TODAY.md #"PostgreSQL `HStoreField` → `strawberry.scalars.JSON` (soft-registered)"`

The file also shows the shipped registration path (`TODAY.md #"config=strawberry_config(),"`) and makes no suppression claim. **No edit made.**

### `CHANGELOG.md` — **(b)**, on one point only; routed, not edited

The `[0.0.6]` entry is substantively correct: `Added` carries `BigInt`, the `JSONField` and `HStoreField` mappings, and the `ArrayField` recursion; `Changed` carries the `PositiveBigIntegerField` → `BigInt` breaking wire-format change. R1's suspicion that the `Notes` line survived is **disproved** — no `### Notes` heading exists under `[0.0.6]`, and no `suppress` / `catch_warnings` token appears anywhere in the entry. `DONE-025-0.0.7` Slice 5 removed it as planned.

The one stale item is a **card identity**, not a contract:

- Says: `CHANGELOG.md #"Tracked as [013-deferred_scalar_conversions-0.0.6][card-deferred-scalar-conversions]"`.
- True at `HEAD`: the card is `DONE-017-0.0.6`. `013` is a pre-board-renumber name; today `spec-013` is the archived real-M2M stub.
- Proof: `KANBAN.md #"### [DONE-017-0.0.6 - Deferred scalar conversions]"` is the live card, and the link definition `CHANGELOG.md #"[card-deferred-scalar-conversions]: KANBAN.md#deferred_scalar_conversions"` still resolves correctly — only the visible label is wrong, exactly the shape of the recorded renumber cluster.

**Not edited.** Two independent reasons: `AGENTS.md` rule 21 (no `CHANGELOG.md` edit without being told; spec-017's Slice 6 grant was for its own `0.0.6` entry at ship time and does not license a fresh edit now), and this occurrence is one surface of the multi-surface renumber cluster `KANBAN.md #"The `[spec-013]` sibling of this cluster is documentation-only"` already cards onto `TODO-ALPHA-051-0.0.15` / `TODO-ALPHA-052-0.1.0`. Routed as maintainer follow-up **MF-2** below.

### `KANBAN.md`, the `DONE-017-0.0.6` card body — **(b)**. The round's one real staleness.

**R1's count verified independently, not restated.** Method per `docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`: grep the shortest distinctive token (`suppress`) and count **occurrences**, not matching lines, so a reword or a line wrap cannot hide one.

```shell
awk 'NR>=4235 && NR<=4326' KANBAN.md | grep -o 'suppress[a-z]*' | sort | uniq -c
#    3 suppressed
#    1 suppression
```

**Four occurrences**, which is R1's "three places plus its Test-plan block" — the two `#### Note` bullets and the `#### Card references` row are the three, the `#### Test plan` line is the fourth. Cross-checked against the DB, which is the authority the rendered file is derived from: three `kanban_carditem.text` rows and one `kanban_cardreference.raw_text` row carry the token, one occurrence each.

- Says (rendered): the Strawberry `DeprecationWarning` is **"suppressed at the definition site"**, with a "tight `warnings.catch_warnings()` filter".
- True at `HEAD`: no suppression exists. `django_strawberry_framework/scalars.py #"BigInt = NewType(\"BigInt\", int)"` is a bare `NewType`; the wire behavior is bound through `scalars.py #"_BIGINT_SCALAR_DEFINITION: ScalarDefinition = strawberry.scalar("` (Strawberry's no-warning `name=`-only overload, no `cls` argument) and registered via `scalars.py #"_PACKAGE_SCALAR_MAP: dict[object, ScalarDefinition]"`, exposed through the public `django_strawberry_framework/scalars.py::strawberry_config`. There is no `catch_warnings` and no `import warnings` in the file.
- Superseded by: `DONE-025-0.0.7`, whose spec Decision 6 is titled `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md #"Remove the `warnings.catch_warnings()` suppression block"`.

**Not edited.** `KANBAN.md` / `KANBAN.html` are generated from the kanban tables in `examples/fakeshop/db.sqlite3` (`docs/builder/BUILD.md` `### Generated docs are DB-backed`), a hand-edit is silently reverted by the next regenerate, and the build plan prohibits every round in this cycle from writing that DB or regenerating those docs while a concurrent session is active on the same tree. Routed as maintainer follow-up **MF-1** below.

---

## Obligation 2 — maintainer follow-ups (executable without rediscovery)

Neither follow-up was performed by this round. Both are DB-backed or `AGENTS.md`-gated.

### MF-1 — correct the `DONE-017-0.0.6` card's suppression claim (kanban DB, then regenerate)

Card row: `kanban.Card` `id=39`, `number=17`, `title="Deferred scalar conversions"`. Four rows to change; **rows 3 and 4 carry byte-identical text and must be changed together** or the rendered card contradicts itself.

**1. `kanban.CardItem` `id=703`** (section `note`, order `1`).

Current text, exactly:

```text
Public `BigInt` scalar (`django_strawberry_framework/scalars.py`, `NewType`-based) with the Strawberry class-direct-to-`scalar()` `DeprecationWarning` suppressed at the definition site so consumers see no warning at import time.
```

Replacement text, exactly:

```text
Public `BigInt` scalar (`django_strawberry_framework/scalars.py`, `NewType`-based). At `0.0.6` the Strawberry class-direct-to-`scalar()` `DeprecationWarning` was suppressed at the definition site so consumers saw no warning at import time; that suppression no longer exists — see the registration note below.
```

**2. `kanban.CardItem` `id=713`** (section `test_plan`, order `0`).

Current text, exactly:

```text
100% coverage via `tests/test_scalars.py` (new flat file) and `tests/types/test_converters.py` (extended). Includes a `test_package_import_does_not_emit_strawberry_deprecation_warning` guard so future regressions to the suppression are explicit.
```

Replacement text, exactly:

```text
100% coverage via `tests/test_scalars.py` (new flat file) and `tests/types/test_converters.py` (extended). Includes a `test_package_import_does_not_emit_strawberry_deprecation_warning` guard so future regressions to the warning-free import surface are explicit.
```

The test itself survives under that name; only what it guards changed.

**3. `kanban.CardItem` `id=715`** (section `note`, order `12`) **and 4. `kanban.CardReference` `id=62`** (`source_card_id=39`, `target_card_id=47`, i.e. `DONE-025-0.0.7`), field `raw_text`.

Current text of **both**, exactly (the `{{card_ref:1}}` placeholder is FK-backed — keep it verbatim):

```text
The internal Strawberry deprecation about passing a class (or `NewType`) to `strawberry.scalar(...)` is suppressed at the definition site (tight `warnings.catch_warnings()` filter). The package import surface is therefore clean. Migration to a `StrawberryConfig.scalar_map`-based design is roadmapped as `{{card_ref:1}}` — that path is a real public-API change (consumers using `BigInt` directly will merge a package-provided `StrawberryConfig` into their `strawberry.Schema(...)`), not an internal-only refactor.
```

Replacement text for **both**, exactly:

```text
The internal Strawberry deprecation about passing a class (or `NewType`) to `strawberry.scalar(...)` was suppressed at the definition site at `0.0.6` (tight `warnings.catch_warnings()` filter), keeping the package import surface clean. `{{card_ref:1}}` replaced that suppression: `BigInt` is now a bare `NewType` bound to a `ScalarDefinition` built from Strawberry's no-warning `strawberry.scalar(name=...)` overload and registered through the package scalar map that the public `strawberry_config()` factory merges into a consumer's `strawberry.Schema(...)` — the real public-API change this note anticipated, not an internal-only refactor.
```

Edit through the Django ORM against `examples/fakeshop/db.sqlite3` (never raw SQL — `post_save` writes the side rows the render needs), then regenerate both rendered surfaces:

```shell
uv run python scripts/build_kanban_md.py
uv run python scripts/build_kanban_html.py
```

Verify by re-running the occurrence count: `awk` over the `DONE-017-0.0.6` card range piped through `grep -o 'suppress[a-z]*'` must report **3 occurrences**, all in past tense inside the amended sentences, and zero occurrences of `is suppressed at the definition site`. `KANBAN.html`'s hand-edited Vue shell is untouched by the regenerate; only its data block moves.

### MF-2 — the pre-renumber card label in `CHANGELOG.md` (part of a carded cluster)

`CHANGELOG.md`'s `[0.0.6]` `Added` entry labels this card `013-deferred_scalar_conversions-0.0.6`; the card is `DONE-017-0.0.6`. The link definition resolves correctly, so this is a label-only artifact — the identical shape as the `[spec-013]` cluster in `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` and the pre-renumber filename references in `docs/SPECS/spec-018-meta_primary-0_0_6.md` and `docs/SPECS/spec-019-consumer_overrides_scalar-0_0_6.md`. `KANBAN.md`'s `TODO-ALPHA-051-0.0.15` / `TODO-ALPHA-052-0.1.0` bullet already carries the whole documentation-only cluster and states why it must land whole. **This occurrence should be folded into that same sweep, not fixed alone** — a partial fix leaves the cluster divergently rather than uniformly wrong. `AGENTS.md` rule 21 independently forbids this round from editing `CHANGELOG.md`.

---

## Obligation 3 — archive audit

**No move was performed. The archive already happened and this cycle owes none.** What follows is proof of placement, not relocation.

### Placement

| File | On disk | Bytes |
|---|---|---|
| `docs/SPECS/spec-017-deferred_scalars-0_0_6.md` | yes | 62,677 |
| `docs/SPECS/appx/spec-017-deferred_scalars-0_0_6-rationale.md` | yes | 41,325 |
| `docs/SPECS/appx/spec-017-deferred_scalars-0_0_6-terms.csv` | yes | 1,754 |

The spec sits in `docs/SPECS/`, both companions in `docs/SPECS/appx/` — exactly what `AGENTS.md` rule 26 and the spec's own `## Definition of done` archive item require. The terms CSV re-verified as importable rather than merely green: 16 data rows, 16 **distinct** anchors, columns `term,anchor,notes` — one row per anchor, the shape `import_spec_terms` requires. Not modified (do-not-touch list).

### Link and anchor resolution

Checked mechanically with fenced code blocks stripped, both files:

- **Spec:** 25 link definitions; every non-URL target resolved against the filesystem — **25 of 25 exist**. Every `[text][ref-id]` use has a definition. Every in-page `](#anchor)` resolves to a heading in the same file, with one deliberate exception: `#specialized-scalar-conversions`, which sits inside the verbatim `docs/GLOSSARY.md` entry-text drop-in in Slice 6 and is meant to resolve in `GLOSSARY.md`, not here. R1 recorded the same exception; re-derived and confirmed unchanged.
- **Rationale companion:** 11 link definitions, **11 of 11 exist**; no undefined reference; no dangling in-page anchor.
- The only apparent extra "undefined ref" either file reports under a naive scan is the token `0-9` inside the `BigInt` parser regex `^(0|-?[1-9][0-9]*)$` — a regex character class, not a link. Named here so a later sweep does not re-derive it as a defect.

### `check_spec_glossary`

```shell
uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-017-deferred_scalars-0_0_6.md
# OK: 16 terms - all have glossary entries and at least one spec link.   (exit 0)
```

### `GlossarySpecMention` rows name the archived path — no follow-up owed

Queried read-only (`file:…?mode=ro`, so no write and no lock contention with the concurrent session):

```sql
select distinct spec_path from glossary_glossaryspecmention where spec_path like '%deferred_scalars%';
-- ('docs/SPECS/spec-017-deferred_scalars-0_0_6.md',)   -- 16 rows, one path
```

All 16 rows already carry the **archived** path. Nothing to route.

### Pre-archive / mis-citation sweep

`grep -rn 'docs/spec-017\|spec-013-deferred_scalars'` across `.md` / `.py` / `.csv`, excluding this cycle's own artifacts, returns five hits and **no live mis-citation of this spec's path**:

- `docs/builder/BUILD.md:13` — `docs/spec-017-deferred_scalars-0_0_6.md` used as the *illustrative* example of the working-location naming pattern for an in-flight spec. Correct as written (working location, pre-archive, by construction); not a citation of this archived file. `docs/builder/BUILD.md` is on the do-not-touch list in any case.
- `KANBAN.md:349`, `docs/SPECS/spec-018-meta_primary-0_0_6.md`, `docs/SPECS/spec-019-consumer_overrides_scalar-0_0_6.md`, `docs/SPECS/appx/spec-013-real_m2m_coverage-0_0_4-rationale.md` — all four are the recorded pre-renumber-name cluster (MF-2), already carded and already described by `KANBAN.md` line 349 in the terms this round would use. **Re-recorded, not fixed.**

### Explicitly changed nothing

The `[spec-013]` ref-id cluster in `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` (five links whose definition `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md #"[spec-013]: spec-017-deferred_scalars-0_0_6.md"` resolves correctly, only the label being a pre-renumber artifact) was re-verified as five occurrences and left **untouched**, per the round's out-of-scope declaration and `worker-0.md` "Verify card/glossary references against the DB".

---

## Gates

- `uv run ruff format .` — pass, **no file reformatted** (this round wrote no Python; the one file written is Markdown).
- `uv run ruff check --fix .` — pass, no fixes applied.
- `uv run python scripts/check_trailing_commas.py --check docs/builder/bld-017-r3-doc_completion_audit.md` — pass (exit 0); link-def scaffold not applicable, this artifact carries no cross-file reference-style links.
- No `pytest` run; no `--cov*`-shaped flag passed in any invocation this round.
- `uv run python scripts/build_tree_md.py --check` — **exit 1**, diagnosed above as a concurrent session's `utils/converters.py` docstring edit, outside this cycle. Recorded, not fixed, not reverted.

## Files written by this round

- `docs/builder/bld-017-r3-doc_completion_audit.md` (this file)
- `docs/builder/worker-memory/spec-017-worker-1.md` (memory entry, gitignored)

**Nothing else.** `docs/README.md`, `README.md`, and `TODAY.md` were in the writable set and were audited to **(a)** on every point this card's contract reaches, so no edit was warranted; `START.md`'s no-"while I'm here" rule forbids editing them for anything else. No spec or rationale-companion edit was needed either — R1's reconciliation holds and this round found no contract error it missed.

### Spec changes made (Worker 1 only)

None. The spec and its rationale companion were read in full and re-verified against `HEAD`; no passage this round examined is false, and no deferral of a `### Dispatched findings checklist` box is owed — every box is ticked with a disposition and a citation.

### Notes for Worker 1 (spec reconciliation)

**Deferred-work catalog input for `docs/builder/bld-017-final.md`:**

- **MF-1** — the four DB rows on card 39 (`DONE-017-0.0.6`) claiming the deprecation is "suppressed at the definition site". Exact current and replacement text plus the regenerate commands are in `## Obligation 2` above. Deferral licensed by the build plan's `**No round in this cycle is authorized to write the DB or regenerate those three docs**`. Target: maintainer.
- **MF-2** — `CHANGELOG.md`'s `013-deferred_scalar_conversions-0.0.6` label, one more surface of the documentation-only pre-renumber cluster already carded onto `TODO-ALPHA-051-0.0.15` / `TODO-ALPHA-052-0.1.0`. Licensed by `AGENTS.md` rule 21 and by the whole-cluster rule. Target: that carded sweep.
- **`[spec-013]` ref-id cluster** in `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md`, five occurrences — re-recorded unchanged for the final gate, per the round's explicit out-of-scope declaration.
- **`docs/TREE.md` is out of date at `HEAD`** for a reason outside this cycle: `django_strawberry_framework/utils/converters.py`'s module docstring changed in a concurrent session's uncommitted work and the rendered doc has not been regenerated. Whoever commits that work owns the regenerate. Not a spec-017 item; recorded so the final gate does not attribute the `--check` failure to this cycle.

**Concurrent work.** The tree carried the same concurrent session's spec-016 residual cycle and review cycle throughout this pass. Nothing on the build plan's `## Baseline-dirty out-of-scope files` list was edited or reverted. `examples/fakeshop/db.sqlite3` was opened **read-only** twice (`mode=ro` URI) to verify the kanban rows and the `GlossarySpecMention` paths; it was never written, and no generated doc was regenerated in place.

### Summary

Walked every doc surface the reconciled spec's Slice 6, `## Doc updates`, and `## Definition of done` name, and established a cited disposition for each. **Ten of eleven surfaces are (a) correct and current** — including all five `docs/GLOSSARY.md` entries R1 flagged as suspects, which turned out to have been corrected already, and `docs/README.md` / `README.md` / `TODAY.md`, which needed no edit at all. **One surface is (b)**: the `KANBAN.md` `DONE-017-0.0.6` card body's suppression claim, whose four occurrences were re-counted mechanically (three `suppressed`, one `suppression`) rather than restated from R1, and traced to three `CardItem` rows and one mirrored `CardReference` row in the kanban DB — routed as maintainer follow-up MF-1 with exact current text, exact replacement text, and the regenerate commands. `CHANGELOG.md` carries one label-level staleness folded into an already-carded renumber sweep (MF-2). The archive audit passes end to end: placement correct, 36 of 36 link definitions resolve, every in-page anchor resolves, `check_spec_glossary` exits 0 on 16 terms, the `GlossarySpecMention` rows already name the archived path, and the pre-archive path sweep finds no live mis-citation. This round edited no standing doc, because none of the ones it was authorized to edit was wrong.

Final status: **`final-accepted`**.
