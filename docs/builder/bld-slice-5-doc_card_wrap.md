# Build: Slice 5 — doc updates + card-completion wrap

Spec reference: `docs/spec-030-connection_field-0_0_9.md` (Slice checklist lines 95-103; `## Doc updates` lines 604-617; Decision 13 lines 505-511; DoD items 1 + 8-11 lines 651-676)
Status: final-accepted

## Plan (Worker 1)

This is the FINAL functional slice: doc-only, plus the DB-backed card-completion wrap. No package `.py` logic changes. The plan separates **(A) hand-edited markdown doc surfaces** from **(B) DB-edit-then-regenerate operations** (KANBAN.md + docs/GLOSSARY.md are GENERATED artifacts — never hand-edited).

### Critical standing context confirmed at planning time

`KANBAN.md`, `KANBAN.html`, and `docs/GLOSSARY.md` are **generated** from the kanban/glossary tables in `examples/fakeshop/db.sqlite3` via `scripts/build_kanban_md.py`, `scripts/build_kanban_html.py`, `scripts/build_glossary_md.py`. Editing them means: mutate the DB via the Django ORM (`examples/fakeshop/manage.py shell` / `.save()` / `import_spec_terms`), then regenerate. Hand-editing the generated markdown creates drift the next regenerate silently reverts. The DB is git-tracked (reversible via `git checkout -- examples/fakeshop/db.sqlite3`). **Never raw SQL** — every kanban/glossary model gets a `UUIDModel` side-row via the `create_uuid_row` `post_save` signal (`examples/fakeshop/apps/kanban/signals.py`) that the GraphQL render requires, and `bulk_create` does not emit `post_save`.

**DB-state findings pinned by read-only queries during planning (these drive the whole B-section):**

1. **`Meta.connection` is NOT in the DB.** `GlossaryTerm.objects.get(anchor="metaconnection")` raises `DoesNotExist`. Commit `87f3edb` ("Add new terms… for Meta.connection") touched ONLY `docs/spec-030-…-terms.csv` (+11 lines), the spec, and `docs/feedback.md` — it did **NOT** touch `docs/GLOSSARY.md` and did **NOT** seed the DB. So the candidate term `Meta.connection` is **net-new and must be seeded** in Slice 5 (the task prompt flagged "may already exist — CHECK the DB"; it does not).
2. **The committed-HEAD `docs/GLOSSARY.md` has NO `Meta.connection` entry.** Regenerating the glossary from the current DB to a temp file reproduces HEAD's `docs/GLOSSARY.md` **byte-identical** (verified: `diff` empty). The `## Meta.connection` entry, its Index row, and its two Browse-by-category rows exist ONLY in the baseline-dirty working copy (the `+21/-2` Revision-3 hand-edit anchoring the build plan carries as baseline-dirty). The DB does not yet render them.
3. **The three target terms' current DB status is `planned`:** `djangoconnectionfield` (`status.key="planned"`, `status_text="planned for `0.0.9`"`), `djangoconnection` (same), and the fourth term `connection-aware-optimizer-planning` (also `planned` — STAYS planned, ships under `033`). `metaconnection` does not exist yet.
4. **Card 030 is `WIP-ALPHA-030-0.0.9`** (`status.key="wip"`, `number=30`, `target_version.number="0.0.9"`), already has a linked `SpecDoc` (`url=…/docs/spec-030-connection_field-0_0_9.md`), and has **0** `CardGlossaryTerm` links. Done-status keys: kanban `Status` has `done`; glossary `GlossaryStatus` has `shipped` (key) / `planned` (key).

**Consequence for the Slice-5 verification rule** (build plan + task prompt: "`git diff docs/GLOSSARY.md` must be CLEAN after regenerate"): "clean" is measured against the **maintainer's eventual commit** of the Slice-5 working tree, NOT against current HEAD (HEAD lacks `Meta.connection` entirely). The DB regenerate must reproduce the working-copy GLOSSARY with (a) `Meta.connection` PRESENT (matching the baseline-dirty hand-edited entry body, Index row, and both browse rows) AND (b) all three of `DjangoConnectionField` / `DjangoConnection` / `Meta.connection` flipped to `shipped (`0.0.9`)`. A non-empty diff after regenerate means a DB body still drifts from the working-copy anchoring — the build-plan baseline-dirty invariant requires the DB regenerate to END UP reproducing the (now-flipped) anchored entry. **This is the top Worker-2 risk** (see below).

### DRY analysis

- **Existing patterns reused (no new code/helpers — doc + DB-ORM slice).**
  - The DB WIP→DONE + glossary-flip procedure reuses the shipped tooling end-to-end: `scripts/build_glossary_md.py`, `scripts/build_kanban_md.py`, `scripts/build_kanban_html.py`, and `examples/fakeshop/apps/glossary/management/commands/import_spec_terms.py`. No new script.
  - The `metaconnection` term seed mirrors the **stored shape of the sibling Meta-key term `metainterfaces`** (inspected at planning): a `GlossaryTerm` with `title`/`title_sort`/`anchor`/`status`/`status_text`/`body`/`entry_order`/`index_order`, one `GlossaryCategoryMembership` per browse category, and `GlossaryTermLink` rows (kind `see-also`) for the "See also" block. The `body` field stores the entry text raw INCLUDING the fenced `python` code block and the `**See also:**` line (the renderer prepends `## <title>` + `**Status:** <status_text>.` and appends `body`).
  - The done-card invariant satisfaction reuses `import_spec_terms` itself: it syncs `GlossarySpecMention` rows AND `CardGlossaryTerm` links from `docs/spec-030-connection_field-0_0_9-terms.csv` for every done card. The CSV already carries all 52 rows (verified `OK: 51 terms` via `check_spec_glossary`; the CSV has 52 data rows incl. `Meta.connection`).
  - The reference-style markdown link convention (START.md / AGENTS.md) is reused for the hand-edited `docs/README.md` / `docs/TREE.md` / `TODAY.md` / `README.md` / `CHANGELOG.md` — those files already carry the `<!-- LINK DEFINITIONS -->` block with the 10 canonical group headers; any net-new cross-file ref is added as `[text][ref-id]` inline + a def under the correct group. (The generated `docs/GLOSSARY.md` / `KANBAN.md` use plain in-page `](#anchor)` / dashboard-URL links, NOT ref-style — they are machine-rendered, so the convention does not apply there; do not retrofit.)
- **New helpers justified:** none. Doc + DB-data slice; no package source touched.
- **Duplication risk avoided:** the chief risk is **hand-editing `docs/GLOSSARY.md` or `KANBAN.md` directly** (would create drift the regenerate reverts). The plan forbids it: all GLOSSARY/KANBAN changes are DB ops + regenerate. Second risk: re-seeding `metaconnection` with a `body` that diverges (even by whitespace/punctuation) from the baseline-dirty working-copy entry, which would surface as a non-clean `git diff` after regenerate. The plan pins the exact body text to copy from the working copy (`docs/GLOSSARY.md` lines 599-615) verbatim.

### Static inspection helper

**Skipped — recorded reason:** Slice 5 adds NO package `.py` logic (doc edits + DB data mutation + regeneration only). No file under `django_strawberry_framework/` is touched; the BUILD.md run-triggers (≥150-line source edit, any `optimizer/` or `types/` touch, ≥30 new logic lines under the package) are all absent. `scripts/build_*.py` and `import_spec_terms.py` are run, not modified.

### Implementation steps

Line numbers are pin-at-write-time navigational hints; verify against current source before editing.

#### (A) Hand-edited markdown doc surfaces (normal markdown edits — NOT DB)

1. **`docs/README.md`** — move `DjangoConnectionField` from the "coming next" line to the shipped surface.
   - Line ~114-115 currently reads `**Coming next — remaining alpha (`0.0.9` → `0.0.12`):**` then `- `0.0.9` *(in progress)* — `DjangoConnectionField` (Relay connection), the full Relay story …`. Edit the `0.0.9` bullet so `DjangoConnectionField` is no longer listed as coming-next: drop it from that bullet (leaving the full Relay story / connection-aware optimizer planning / DX cleanup as the remaining `0.0.9` items, since those are still WIP under `031`/`032`/`033`), and add `DjangoConnectionField` to the shipped-surface enumeration earlier in the "Today and coming next" section (the shipped block ~lines 107-111, alongside the ordering subsystem). Note the **sidecar-derived `filter:` / `orderBy:` arguments and the opt-in `totalCount`**.
   - Worker-2 discretion: exact placement/wording within the shipped block, as long as it (a) names `DjangoConnectionField`, (b) notes the sidecar-derived `filter:`/`orderBy:` arguments, (c) notes the opt-in `totalCount`, and (d) removes the stale "coming next / in progress" framing for the connection field specifically. Preserve the reference-style link convention if any cross-file ref is introduced.

2. **`docs/TREE.md`** — list `connection.py` under the **current on-disk** package layout and the mirrored test.
   - The current-on-disk block is `## django_strawberry_framework (current on-disk layout)` (line ~188, tree starts line 194). Add a `connection.py` line after `list_field.py` (line 202), e.g. `├── connection.py            # DjangoConnectionField / DjangoConnection (Relay connection factory; shipped in 0.0.9)`. Do NOT add an `[alpha]` tag here — the `[alpha]` tag lives on the **target** layout block (line 266: `├── connection.py            # [alpha] DjangoConnectionField (Relay)`); per the spec, "drop its `[alpha]` planned tag" means: it appears in the **current on-disk** layout WITHOUT `[alpha]` (it is now shipped). Leave the target-layout `[alpha]` line as-is OR remove it — Worker-2 discretion, but the spec's intent is that connection.py is reflected as on-disk/shipped. Recommended: add to current-on-disk (no `[alpha]`); the target-layout duplicate may stay (it documents the aspirational tree).
   - Add the mirrored test file under the test "current shape (on disk today)" tree (line ~338-348): a `test_connection.py` line near `test_list_field.py` (line 348), e.g. `├── test_connection.py       # DjangoConnectionField / DjangoConnection (single-file Layer-3 module)`.
   - Preserve reference-style links / the bottom `<!-- LINK DEFINITIONS -->` block if any def needs adding.

3. **`TODAY.md`** — update the products "still waiting for" list (keep products-centric).
   - Line ~239 reads `- `DjangoConnectionField` — Relay connections (`0.0.9`, in progress: `WIP-ALPHA-030-0.0.9`)`. Per the spec, `DjangoConnectionField` moves OFF the "still waiting for" list (it shipped). Worker-2 discretion on the exact treatment: either (a) remove the bullet (it shipped, like filtering/ordering which the section explicitly excludes — line 237: "Filtering and ordering are not on this list — they shipped in 0.0.8"), OR (b) note its products-side activation tracking (lit up at fakeshop activation per `TODO-BETA-051-0.1.5`). Recommended: remove from the waiting list and, if it reads naturally, add a short shipped/activation note consistent with how the filter/order shipped surfaces are framed. Keep the file products-centric (no library-app specifics).

4. **`README.md`** — update the status paragraph's newest-shipped-surface line **only if it enumerates the connection field**.
   - Line ~50 currently reads `Newest shipped surface: the ordering subsystem (`0.0.8`) — …`. It does **not** currently enumerate the connection field. The spec wording is conditional ("update … only if it enumerates the connection field"). Because the connection field is now genuinely the newest-shipped surface and this line's explicit job is to name the newest-shipped surface, **update it** to lead with `DjangoConnectionField` (the Relay connection field with sidecar-derived `filter:`/`orderBy:` arguments and opt-in `totalCount`) as the newest shipped surface, keeping the ordering/filter recap as prior context. The `**`0.0.8`…**` version-token at the line start is the on-disk version (Decision 13 keeps it `0.0.8`) — do NOT change the version token; only the prose "Newest shipped surface" clause changes.
   - This is the one (A)-step the spec phrases conditionally; Worker-2 records the decision in its build report. If on inspection the maintainer's baseline already changed line 50, treat the existing text as authoritative (AGENTS.md unexpected-modification rule) and only ensure the connection field is named as newest-shipped.

5. **`CHANGELOG.md`** — add a `### Added` bullet under `[Unreleased]` (the per-card permission grant; NO version-heading promotion, Decision 13).
   - The `[Unreleased]` section (line ~21) already has a `### Changed` block and a `### Added` block (lines ~25-27). Append a new bullet to the EXISTING `[Unreleased]` `### Added` list (do not create a new heading, do not promote a `[0.0.9]` release heading).
   - **Exact `### Added` wording to add (pin verbatim):**

     ```
     - **`DjangoConnectionField` (Relay connection field).** [`DjangoConnectionField`][glossary-djangoconnectionfield] and the generic [`DjangoConnection`][glossary-djangoconnection]`[T]` return alias now ship under [`django_strawberry_framework/connection.py`][connection]. The factory wraps a Relay-Node-shaped [`DjangoType`][glossary-djangotype], emits `edges` / `node` / `pageInfo` cursor pagination on Strawberry's native `relay.connection()` / `ListConnection`, and injects `filter:` / `orderBy:` arguments derived from the wrapped type's `Meta.filterset_class` / `Meta.orderset_class` sidecars via a synthesized resolver signature — no hand-written list resolver, no parallel argument declarations. The composition pipeline runs `get_queryset` visibility → `filter` → `orderBy` → default deterministic pk-ordering → optimizer-plan → cursor slice, and the field owns its own optimizer cooperation point (the plan-application logic extracted from `DjangoOptimizerExtension._optimize`) because Strawberry's connection slicing hides the pre-slice queryset from the schema middleware. A package-owned guard rejects `first` + `last` together with a `GraphQLError`.
     - **`Meta.connection` opt-in `totalCount`.** The net-new type-level [`Meta.connection`][glossary-metaconnection] key (`{"total_count": bool}`, valid only when [`Meta.interfaces`][glossary-metainterfaces] includes `relay.Node`) is validated at type-creation time and stored on the `DjangoType` definition. When `total_count` is enabled, the connection resolves through a generated per-target `<TypeName>Connection` class exposing `totalCount: Int!` — counted on the post-filter pre-slice queryset, selection-gated (no count query runs unless `totalCount` is selected), and carried per connection instance so two aliases with different `filter:` values report independent counts.
     ```
   - Worker-2 discretion: whether this lands as one combined bullet or the two bullets shown (recommended: two bullets — one for the field, one for `Meta.connection`, matching the existing `[Unreleased]` `Meta.nullable_overrides` bullet granularity). The reference-style refs `[glossary-djangoconnectionfield]`, `[glossary-djangoconnection]`, `[glossary-metaconnection]`, `[glossary-metainterfaces]`, `[glossary-djangotype]`, `[connection]` must resolve in CHANGELOG.md's bottom `<!-- LINK DEFINITIONS -->` block — verify each def exists (most do, from prior changelog entries); add any missing def to the correct group (`[connection]: django_strawberry_framework/connection.py` under `<!-- django_strawberry_framework/ -->`; `[glossary-metaconnection]: docs/GLOSSARY.md#metaconnection` under `<!-- docs/ -->`). If a ref-id used here is not already defined in CHANGELOG.md, either add the def or fall back to the inline-code form already used elsewhere in the file — Worker-2 confirms the existing CHANGELOG link inventory before choosing.

#### (B) DB-edit-then-regenerate operations (Django ORM, then regenerate)

All ORM work runs through `uv run python examples/fakeshop/manage.py shell` (or a one-off script piped to `shell`); **never raw SQL**; use `.save()` / `.objects.create()` / `update_or_create()` so the `create_uuid_row` `post_save` signal fires. Wrap the multi-step mutation so a mid-way failure does not leave a half-done card (a done-card invariant violation mid-sequence will raise `ValidationError`).

**B1. Seed the net-new `Meta.connection` glossary term** (it is MISSING from the DB — confirmed). Create a `GlossaryTerm` reproducing the baseline-dirty working-copy entry (`docs/GLOSSARY.md` lines 599-615) so the regenerate renders it byte-identical:
   - `anchor="metaconnection"`, `title="`Meta.connection`"`, `title_sort="meta.connection"`.
   - `status = GlossaryStatus.objects.get(key="shipped")`, `status_text="shipped (`0.0.9`)"` — seed it **directly as shipped** (the working copy will be flipped to shipped this slice anyway; seeding planned-then-flipping is two steps for the same end state, but Worker-2 may seed `planned` first then flip in B2 for symmetry with the existing terms — discretion).
   - `body` = the working-copy entry body VERBATIM from `docs/GLOSSARY.md` (the two prose paragraphs + the fenced ` ```python … ``` ` block + the `**See also:** …` line), i.e. everything AFTER the `**Status:** …` line through the See-also line. Pin (copy exactly):

     ```
     Relay-connection options for a `DjangoType`. In `0.0.9`, the accepted shape is `{"total_count": bool}` and the key is valid only when [`Meta.interfaces`](#metainterfaces) includes `strawberry.relay.Node`.

     When `total_count` is true, [`DjangoConnectionField`](#djangoconnectionfield) resolves the type through a concrete per-target connection class exposing `totalCount`; otherwise it uses [`DjangoConnection`](#djangoconnection)`[T]` without that field. The option is type-level, not per field, so a node type has one stable connection shape.

     ```python
     class GenreType(DjangoType):
         class Meta:
             model = Genre
             interfaces = (relay.Node,)
             connection = {"total_count": True}
     ```

     **See also:** [`DjangoConnectionField`](#djangoconnectionfield) · [`DjangoConnection`](#djangoconnection) · [Relay Node integration](#relay-node-integration) · [`Meta.interfaces`](#metainterfaces).
     ```
     (Worker-2: confirm whether the renderer stores the `**See also:**` line in `body` or assembles it from `GlossaryTermLink` rows. The sibling `metainterfaces` term inspected at planning stores the `**See also:** …` line INSIDE `body` AND has `see-also` `GlossaryTermLink` rows — check the renderer to see which the markdown comes from, and match the metainterfaces pattern exactly. If the See-also line is rendered from links, create the four `GlossaryTermLink` rows (kind `see-also`, ordered 0-3: `djangoconnectionfield`, `djangoconnection`, `relay-node-integration`, `metainterfaces`) and store body WITHOUT the See-also line; if from `body`, store it in `body` as shown. The metainterfaces precedent stores it in body AND has link rows — replicate whichever produces the byte-identical regenerate.)
   - `entry_order` / `index_order`: pick values that place the entry where the working copy has it (alphabetically among the `Meta.*` entries — between `## DjangoFileType`-region ordering; the working-copy `## Meta.connection` sits at line 599, after `Meta.aggregate_class`-region entries). Worker-2 derives the exact `entry_order`/`index_order` by reading the neighboring `Meta.*` terms' orders and inserting consistently; the renderer sorts entries by `entry_order, title_sort` and the Index by `index_order`. The Index row position in the working copy is line 83 (between `Meta.aggregate_class`/`Meta.description`-region rows — Worker-2 confirms the exact alphabetical Index neighbors).

**B2. Seed the `Meta.connection` category memberships** (so the Browse-by-category rows render in the working-copy positions). Two `GlossaryCategoryMembership` rows:
   - **Type generation** (`GlossaryCategory key="type-generation"`): the working copy lists `Meta.connection` between `Meta.interfaces` and `Meta.nullable_overrides`. Current members (order): …7=`metainterfaces`, 8=`metanullable_overrides`, 9=`metarequired_overrides`, 10=`definition-order-independence`, 11=`finalize_django_types`, 12=`configurationerror`. The `(category, order)` UNIQUE constraint means inserting at order 8 requires **shifting members 8-12 up by one** (work from highest order downward to avoid transient collisions), then create `metaconnection` at order 8.
   - **Relay** (`GlossaryCategory key="relay"`): the working copy lists `Meta.connection` between `DjangoConnection` and `Connection-aware optimizer planning`. Current members (order): 0=`relay-node-integration`, 1=`djangonodefield`, 2=`djangoconnectionfield`, 3=`djangoconnection`, 4=`connection-aware-optimizer-planning`, 5=`syncmisuseerror`. Insert at order 4 → shift members 4-5 up by one (descending), then create `metaconnection` at order 4.
   - Worker-2: the shift must be done with `.save()` per row (the `(category, order)` UNIQUE constraint + the per-row signal); descending iteration avoids transient unique-collisions. Confirm the working-copy browse-row order against the regenerate.

**B3. Flip the three term statuses `planned` → `shipped`.** For each of `djangoconnectionfield`, `djangoconnection` (and `metaconnection` if seeded as planned in B1):
   - `t.status = GlossaryStatus.objects.get(key="shipped")`; `t.status_text = "shipped (`0.0.9`)"`; `t.save()`.
   - **Leave `connection-aware-optimizer-planning` `planned`** (ships under `033`) — do NOT touch it.
   - Also reconcile the two existing terms' BODIES to match the baseline-dirty working copy if the build hand-edited the body there: the working-copy `DjangoConnection` (lines 274-280) and `DjangoConnectionField` (lines 282-288) bodies are IDENTICAL to HEAD's DB-rendered bodies (verified: the only working-copy GLOSSARY diff vs regenerate is the three `Meta.connection` anchoring lines + entry — the two existing entry bodies are unchanged). **So no body reconcile is needed for `DjangoConnection`/`DjangoConnectionField` beyond the status flip.** (Note: the spec's `## Doc updates` GLOSSARY bullet asks to "add the sidecar-derived-argument / composition-order / opt-in-`totalCount` / per-shape-connection-class detail and the flat-walker cooperation-point alpha-constraint note to the `DjangoConnectionField` body." The current working-copy/DB `DjangoConnectionField` body (line 286) already describes `edges`/`node`/`pageInfo`/`totalCount`, the sidecar `filter`/`orderBy`/`search` flow, and optimizer composition — but says "Composes with the optimizer for nested-selection planning" and "Works at root fields and at nested relation fields," which OVERSTATES the 0.0.9 alpha reality (Slice 3 re-scope: the plan is EMPTY in 0.0.9; nested `edges{node}` planning is `033`). **Worker-2 SHOULD update the `DjangoConnectionField` body via the DB** to (a) drop/qualify the `search` argument mention (search is 0.1.2, not shipped — the field reserves the seam but generates no `search:` arg in 0.0.9), and (b) replace the optimistic optimizer/nesting prose with the honest alpha-constraint note: the field owns its optimizer cooperation point but the derived plan is empty in 0.0.9 (flat-walker connection-unawareness), and nested `edges { node }` planning is the sibling `Connection-aware optimizer planning` card (`033`). This is a `body` edit on the `djangoconnectionfield` `GlossaryTerm`, done in the DB, then regenerated. **Because this body edit diverges from the baseline-dirty working copy, it CHANGES what "clean diff" means** — see the verification note: after this edit the regenerate will differ from the baseline-dirty working copy in the `DjangoConnectionField` body, which is INTENDED; the maintainer's commit captures the new body. Worker-2 records the exact new body in its build report so Worker-1 final-verification and Worker-3 can confirm it against the spec's `## Doc updates` requirement.)

**B4. Satisfy the DONE-card invariants, then flip the card to done.** The `prepare_card_save` `pre_save` signal blocks saving `status.key=="done"` unless the card has BOTH a linked `SpecDoc` AND ≥1 `CardGlossaryTerm`. Card 030 already has the `SpecDoc` (verified) but **0** glossary links.
   - **Bootstrap ≥1 `CardGlossaryTerm`** BEFORE the done-flip: `CardGlossaryTerm.objects.create(card=card_030, term=<any seeded GlossaryTerm, e.g. djangoconnectionfield>, raw_text="`DjangoConnectionField`", order=0)`. (This is the bootstrap link; `import_spec_terms` in B5 then reconciles the FULL link set from the CSV.)
   - **Flip status:** `card = Card.objects.get(number=30)`; `card.status = Status.objects.get(key="done")`; `card.save()`. The `_card_identifier` / `card_id` render drops the milestone prefix for done cards → the rendered id becomes `DONE-030-0.0.9` (number stays 30). Confirm no card-number reshuffle is triggered (status change is not a number change; `prepare_card_save` only reorders when `number` changes).

**B5. Sync the full glossary-link set from the CSV.** Run `uv run python examples/fakeshop/manage.py import_spec_terms`. This:
   - For every done card (now including 030), loads its `*-terms.csv`, requires **every anchor to already exist as a `GlossaryTerm`** (B1 ensured `metaconnection` exists — without B1 this command FAILS with "Missing GlossaryTerm anchor 'metaconnection'"), syncs `GlossarySpecMention` rows for `spec_path=docs/spec-030-connection_field-0_0_9.md`, and reconciles `card.glossary_links` (`CardGlossaryTerm`) to exactly match the CSV's 52 anchors in CSV order. The bootstrap link from B4 is absorbed/reordered by this sync.

**B6. Fix card-body content the spec wrap names.** Per spec `## Doc updates` (line 617) and Decision 1: the card body's DoD currently references an unnumbered `docs/spec-connection.md` — rewrite it to the canonical `docs/spec-030-connection_field-0_0_9.md`. Also confirm/set the card body's spec reference (DB `SpecDoc.url` already points at the canonical path — verified — so the linked-spec is correct; the in-body prose reference is what needs the rewrite). The card body lives in the DB (`Card.body` / `CardItem` rows — Worker-2 confirms which field holds the rendered body and whether the DoD items are `CardItem` rows). Mark the card's `definition_of_done` items complete if they are tracked as DB rows (`CardItem` with a done flag) — Worker-2 reads the `Card`/`CardItem` model to determine the mechanism; if the DoD is free-text in `Card.body`, edit that text. Worker-2 records the exact card-body field(s) edited.
   - **`[0.0.X]` → `[Unreleased]`:** the task prompt names a "stale `## [0.0.X]` → `[Unreleased]`" fix. Scan the card body for any `[0.0.9]`/`[0.0.X]` release-heading reference that should read `[Unreleased]` (consistent with Decision 13 — no version heading promoted). Worker-2 greps the card body and the rendered `KANBAN.md` card for this and corrects in the DB if present; if absent, records "no stale version-heading ref in card body."

**B7. Regenerate all three artifacts** (after ALL DB mutations B1-B6 land):
   - `uv run python scripts/build_kanban_md.py`
   - `uv run python scripts/build_kanban_html.py`
   - `uv run python scripts/build_glossary_md.py`
   (Order: any order works; each reads the DB and writes its own file. Run all three so `KANBAN.md`, `KANBAN.html`, and `docs/GLOSSARY.md` are all consistent with the DB.)

**B8. Verify** (read-only checks; record results in the build report):
   - `uv run python examples/fakeshop/manage.py import_spec_terms --check` → expect `OK: <N> done cards have glossary links.` (030 now included; its links == the CSV).
   - `uv run python scripts/check_spec_glossary.py --spec docs/spec-030-connection_field-0_0_9.md` → expect `OK: <N> terms` (still resolves; `metaconnection` now in GLOSSARY).
   - `git diff docs/GLOSSARY.md`: must reflect ONLY the intended Slice-5 changes (the three status flips, the `Meta.connection` entry/Index/browse rows now matching the working-copy anchoring, and the `DjangoConnectionField` body honesty edit from B3). The build-plan invariant: the DB regenerate must REPRODUCE the (flipped + body-corrected) anchored entry — i.e. no UNINTENDED drift. A diff that shows the `Meta.connection` entry DISAPPEARING, or whitespace/punctuation churn vs the working-copy entry, means the B1/B2 seed diverged — fix the seed, do not hand-edit the markdown.
   - `git diff KANBAN.md`: shows `WIP-ALPHA-030-0.0.9` → `DONE-030-0.0.9` moved to the Done column, spec ref canonical, DoD items rendered complete.
   - `uv run python examples/fakeshop/manage.py check` → passes (system-check framework).
   - `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` → no new migrations (DB DATA changed, not schema).
   - **Guard the no-version-bump invariant** (Decision 13): `git diff` shows `pyproject.toml`, `django_strawberry_framework/__init__.py` (`__version__` stays `"0.0.8"`), `tests/base/test_init.py`, and `uv.lock` ALL UNCHANGED. CHANGELOG has NO new `[0.0.9]` release heading (only the `[Unreleased]` `### Added` bullets).

### Test additions / updates

- **Package tests (`tests/`):** NONE. Slice 5 adds no `django_strawberry_framework/` logic; the connection field's behavior is fully covered by Slices 1-4 (`tests/test_connection.py`, `tests/types/test_base.py`, `tests/optimizer/`, and the live `examples/fakeshop/test_query/test_library_api.py`).
- **DB-generated example tests (`test_kanban_api.py` / `test_glossary_api.py`):** assess but do NOT pre-emptively change. These live-HTTP suites query the kanban/glossary GraphQL API against the DB. Slice 5's DB mutations (one new `GlossaryTerm`, two memberships, three status flips, a card status flip, glossary-link sync) change the DATA the API returns. **Worker-2 must check** whether either suite asserts a fixed term-count, a fixed done-card count, a fixed status distribution, or snapshots a card's exact status/column — if so, those assertions must be updated to the post-Slice-5 reality (e.g. one more `shipped` term, `metaconnection` present, card 030 in Done). If the suites assert structural/shape invariants (not exact counts/snapshots of the mutated rows), no change is needed. Worker-2 greps both suites for term-count / card-count / status assertions and records the finding; any required test edit is a Worker-2 change in the same diff (AGENTS.md "add tests in the same change"). This is the one place Slice 5 might touch a test file — flagged for Worker-3 to walk.
- **Temp/scratch tests:** none needed; the verification is via the management commands + `git diff`, not pytest.

### Implementation discretion items

Worker-1 has assessed these and delegates them to Worker-2:

- **`metaconnection` body — See-also storage location** (in `body` vs assembled from `GlossaryTermLink` rows): replicate the `metainterfaces` precedent exactly so the regenerate is byte-identical. Either mechanism is acceptable as long as the rendered output matches the baseline-dirty working-copy entry.
- **Seed `metaconnection` as `shipped` directly (B1) vs seed `planned` then flip (B3):** both reach the same end state; pick whichever reads cleaner in the shell script.
- **`CHANGELOG.md` one combined bullet vs two bullets:** recommended two (field + `Meta.connection`); Worker-2 picks the granularity that matches the existing `[Unreleased]` bullets.
- **`docs/TREE.md` target-layout `[alpha]` line (266) — keep or remove:** keep is acceptable (it documents the aspirational tree); the load-bearing requirement is the current-on-disk entry without `[alpha]`.
- **`TODAY.md` — remove the waiting bullet vs convert to an activation note:** either, kept products-centric.
- **Exact `entry_order` / `index_order` / browse-membership shift values:** derived by Worker-2 from the neighboring rows to reproduce the working-copy positions.

NOT delegated (architectural / must follow the plan): the (A)/(B) split (GLOSSARY/KANBAN are DB-only, never hand-edited); the no-version-bump invariant (Decision 13); seeding `metaconnection` BEFORE running `import_spec_terms` (the command hard-fails otherwise); the `DjangoConnectionField` body honesty edit (B3) reflecting the Slice-3 re-scope (empty plan in 0.0.9, nested planning is `033`).

### Spec slice checklist (verbatim)

- [x] [`docs/GLOSSARY.md`][glossary]: flip [`DjangoConnectionField`][glossary-djangoconnectionfield], [`DjangoConnection`][glossary-djangoconnection], and [`Meta.connection`][glossary-metaconnection] from `planned for 0.0.9` to `shipped (0.0.9)` in the [Index][glossary-index] table and entry bodies; confirm `Meta.connection` describes the `{"total_count": bool}` shape and the Relay-Node requirement and remains present in the Index plus the "Relay" / "Type generation" [Browse by category][glossary] rows. Leave [Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning] `planned for 0.0.9` (ships under [`WIP-ALPHA-033-0.0.9`][kanban]).
- [x] [`docs/README.md`][docs-readme]: move `DjangoConnectionField` from the "coming next" `0.0.9` line to the shipped surface list; note the sidecar-derived `filter:` / `orderBy:` arguments and opt-in `totalCount`.
- [x] [`docs/TREE.md`][tree]: list [`connection.py`][connection] under the current on-disk package layout (drop its `[alpha]` planned tag) and the mirrored [`tests/test_connection.py`][test-connection].
- [x] [`TODAY.md`][today]: update the products "still waiting for" list — `DjangoConnectionField` moves from waiting to shipped (or note products' Relay-connection activation tracking, lit up at fakeshop activation per [`TODO-BETA-051-0.1.5`][kanban]); keep the file products-centric.
- [x] [`README.md`][readme]: update the status paragraph's newest-shipped-surface line if it enumerates the connection field (include only if reflected there).
- [x] [`CHANGELOG.md`][changelog]: `### Added` bullet under `[Unreleased]` for `DjangoConnectionField` / `DjangoConnection` / `Meta.connection`. **This is the per-card CHANGELOG-edit permission grant** ([`AGENTS.md`][agents] withholds it by default); the Slice 5 maintainer prompt must name this edit explicitly. No version-heading promotion (per [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-009-cut)).
- [x] [`KANBAN.md`][kanban]: move [`WIP-ALPHA-030-0.0.9`][kanban] to the Done column with the next `DONE-NNN-0.0.9` id; add / confirm the card body's spec reference points at [`docs/spec-030-connection_field-0_0_9.md`][spec-030] (this document).
- [x] **No version-file edits in this card.** Leave `pyproject.toml`, [`__version__`][package-init], [`tests/base/test_init.py::test_version`][test-base-init], and `uv.lock` to the joint `0.0.9` cut per [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-009-cut).

---

## Build report (Worker 2)

### Files touched

**(A) Hand-edited markdown (Worker 2 edits):**

- `docs/README.md` — added a `DjangoConnectionField` shipped-surface bullet (after the ordering subsystem) naming `edges`/`node`/`pageInfo`, the sidecar-derived `filter:`/`orderBy:` args, and the opt-in `totalCount`; removed `DjangoConnectionField` from the "coming next `0.0.9`" bullet; added the `[glossary-djangoconnectionfield]` ref-def under `<!-- docs/ -->`.
- `docs/TREE.md` — added `connection.py` under the **current on-disk** package layout (no `[alpha]` tag) and `test_connection.py` under the current-state test tree. Left the target-layout `[alpha]` line (line ~267) as-is per the plan's discretion (documents the aspirational tree).
- `TODAY.md` — removed the `DjangoConnectionField` "still waiting for" bullet; extended the section's exclusion sentence (alongside filtering/ordering) noting it shipped in `0.0.9` and lights up at fakeshop activation (`TODO-BETA-051-0.1.5`). Kept products-centric.
- `README.md` — updated the Status paragraph's "Newest shipped surface" clause to lead with `DjangoConnectionField` (`0.0.9`) + `Meta.connection` + the `DjangoConnection[T]` alias, keeping the ordering/filter recap as prior context. The `**`0.0.8`...**` on-disk-version token was NOT changed (Decision 13).
- `CHANGELOG.md` — added two `### Added` bullets under `[Unreleased]` (field + `Meta.connection`) with the plan's pinned verbatim wording; added the missing ref-defs `[glossary-djangoconnection]`, `[glossary-djangoconnectionfield]`, `[glossary-metaconnection]`, `[glossary-metainterfaces]` (under `<!-- docs/ -->`) and `[connection]` (under `<!-- django_strawberry_framework/ -->`). No version-heading promotion.

**(B) DB-edit-then-regenerate (Django ORM on `examples/fakeshop/db.sqlite3`, then regenerate):**

- `examples/fakeshop/db.sqlite3` — see Implementation notes for the exact ORM sequence (B3 status flips + `DjangoConnectionField` body honesty edit; B4 bootstrap `CardGlossaryTerm` + card→done; B6 card-body spec-ref rewrite + DoD `is_complete`; B5 `import_spec_terms` full sync).
- `docs/GLOSSARY.md` — REGENERATED. Diff = three Index status flips + three entry `**Status:**` flips to `shipped (`0.0.9`)`, the `DjangoConnectionField` body honesty edit, the now-present `## Meta.connection` entry + its Index row + "Type generation"/"Relay" browse rows. No stray drift.
- `KANBAN.md` / `KANBAN.html` — REGENERATED. `WIP-ALPHA-030-0.0.9` → `DONE-030-0.0.9`, moved from the In-progress section to `## Done`; all 10 DoD items render `- [x]`; card spec ref canonical.
- `docs/spec-030-connection_field-0_0_9-terms.csv` — removed the spurious `Public exports,public-exports,...` row (a document-section anchor, not a `GlossaryTerm`) that hard-blocked `import_spec_terms`. **This is plan-vs-implementation drift — flagged for Worker 1 below.**

**NOT touched (prior-slice or Worker-1 work, left in tree):** `django_strawberry_framework/__init__.py` (Slice 4 export), `optimizer/extension.py`, `types/base.py`, `types/definition.py`, `connection.py`, `examples/fakeshop/apps/library/schema.py`, `test_library_api.py`, `tests/optimizer/test_extension.py`, `tests/types/test_base.py`, `tests/test_connection.py`, `docs/spec-030-connection_field-0_0_9.md` (Worker-1 spec edits), and the `bld-*`/`build-*` artifacts.

### Tests added or updated

- **None.** Slice 5 adds no package `.py` logic.
- **Count-assertion fixes: NONE needed.** `test_kanban_api.py` / `test_glossary_api.py` are `@pytest.mark.django_db` suites that build their own isolated fixtures (`_seed_glossary` / per-test `create()`) on a fresh transactional DB. They depend on the models/schema, NOT on the committed `db.sqlite3` row data, and assert no global term/card counts or status distributions. The Slice-5 DB mutations to `db.sqlite3` (used only by the `build_*.py` generators) do not reach them. Verified by reading both suites' setup/assertions.

### Validation run

- `uv run ruff format .` — pass (233 files unchanged; no `.py` churn).
- `uv run ruff check --fix .` — pass (All checks passed).
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` — `OK: 30 done cards have glossary links.` (card 030 now included).
- `uv run python scripts/check_spec_glossary.py --spec docs/spec-030-connection_field-0_0_9.md` — `OK: 50 terms` (was 51; the removed `public-exports` row dropped the count by one — see drift note).
- `uv run python examples/fakeshop/manage.py check` — `System check identified no issues (0 silenced)`.
- `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` — `No changes detected` (DB **data** changed, not schema).
- `git diff docs/GLOSSARY.md` — reflects ONLY the intended shipped state (3 status flips + body honesty edit + `Meta.connection` entry/Index/browse rows present). No stray drift.
- `git diff KANBAN.md` — `DONE-030-0.0.9` in `## Done` with DoD ticked, spec ref canonical.
- **No-version-bump invariant (Decision 13):** `pyproject.toml` / `tests/base/test_init.py` / `uv.lock` UNCHANGED (not in `git status`). `django_strawberry_framework/__init__.py` is modified but that is the Slice-4 export promotion (`from .connection import ...`), NOT a version bump — `__version__` stays `"0.0.8"`. No `## [0.0.9]` release heading in CHANGELOG (verified absent).
- `git status --short` classification: all listed `M`/`??` files are either Slice-5-intended (the A-markdown + db.sqlite3 + regenerated KANBAN/GLOSSARY/HTML + the terms CSV) or carried-in prior-slice/Worker-1 work (the package `.py`, the spec `.md`, the library schema/tests, the bld-/build- artifacts). No unrelated tool churn.

### Implementation notes

- **B1/B2 were already done in the DB.** Contrary to Worker 1's planning-time finding ("`Meta.connection` is NOT in the DB"), the `metaconnection` `GlossaryTerm` already existed in `db.sqlite3` (status `planned`, body verbatim, both `GlossaryCategoryMembership` rows at type-generation order=8 / relay order=4, See-also stored IN `body` with NO `GlossaryTermLink` rows). The DB had moved on since planning. So I did NOT re-seed; I only flipped its status in B3. The committed HEAD `docs/GLOSSARY.md` lacked the entry (the markdown was stale vs. the DB), so the regenerate correctly ADDS the `Meta.connection` entry — that is the intended shipped state, not drift.
- **B3 status flips** ran via `GlossaryStatus.objects.get(key="shipped")` + `status_text="shipped (`0.0.9`)"` + `.save()` per term (so the `post_save` UUID side-row signal fires). Flipped `djangoconnectionfield`, `djangoconnection`, `metaconnection`. Left `connection-aware-optimizer-planning` `planned` (confirmed untouched post-op).
- **B3 `DjangoConnectionField` body honesty edit** (per the plan's not-delegated requirement): the new `body` (a) qualifies the `search:` arg — "reserved for `Meta.search_fields` (`0.1.2`) and is not generated in `0.0.9`"; (b) replaces the optimistic "Composes with the optimizer for nested-selection planning / Works at root and nested relation fields" prose with the honest alpha-constraint note — the field owns its cooperation point but the derived plan is **empty** in `0.0.9` (flat walker connection-unawareness), nested `edges{node}` planning is `WIP-ALPHA-033-0.0.9`, and a Strictness `"raise"` run surfaces the unplanned nested access (no silent cap). The exact new body text is the `+` lines in `git diff docs/GLOSSARY.md` for the `## DjangoConnectionField` entry.
- **B4 ordering** honored the done-card invariant: bootstrap `CardGlossaryTerm` (term=`djangoconnectionfield`, order=0) created BEFORE flipping `card.status` to `done` (the `prepare_card_save` `pre_save` signal requires SpecDoc — already present — AND ≥1 `CardGlossaryTerm`). `card.card_id` then renders `DONE-030-0.0.9` (milestone prefix dropped for done; number unchanged → no reshuffle).
- **B6 card body:** rewrote `docs/spec-connection.md` → `docs/spec-030-connection_field-0_0_9.md` in TWO `CardItem.text` rows (DoD order=0 and `[other]` order=3 prose). Set `is_complete=True` on all 10 `definition_of_done` `CardItem` rows (the DoD ticks render from this flag). No stale `[0.0.X]`/`[0.0.9]` release-heading reference exists in the card body (grep over all items returned 0) — recorded per plan B6.
- **B5** `import_spec_terms` (no flags) reconciled all 30 done cards' `GlossarySpecMention` + `CardGlossaryTerm` link sets from their CSVs; the B4 bootstrap link was absorbed/reordered into the CSV's 51-row set for card 030.
- All ORM mutations ran inside a single `transaction.atomic()` block via `manage.py shell` (no raw SQL); regeneration via the three `scripts/build_*.py`.

### Notes for Worker 3

- **KANBAN.md / KANBAN.html / docs/GLOSSARY.md are GENERATED from `examples/fakeshop/db.sqlite3`.** Do NOT review them as hand-authored source. To verify, read the DB rows (or re-run `scripts/build_*.py` and diff) — the markdown is an export. The Slice-5 changes to these three files are entirely DB-derived.
- The terms-CSV row removal (`public-exports`) is the one spec-companion edit; see the spec-reconciliation note below.
- No static inspection helper (`scripts/review_inspect.py`) was run — Slice 5 touches no package `.py` (doc + DB-data slice).

### Notes for Worker 1 (spec reconciliation)

**DRIFT — `docs/spec-030-connection_field-0_0_9-terms.csv` `public-exports` row removed (verified fix; needs Worker-1 ratification).**

- **Blocker found:** with card 030 flipped to `done`, `import_spec_terms` processes its terms CSV and hard-fails: `Missing GlossaryTerm anchor 'public-exports'`. The CSV row `Public exports,public-exports,...` points at the GLOSSARY's `## Public exports` **document section** (rendered from a kanban `BoardDocument`), which is NOT a `GlossaryTerm`. `import_spec_terms._load_rows` requires every CSV anchor to resolve to a `GlossaryTerm`; `scripts/check_spec_glossary.py` only requires an `## H2` heading (so it passed `public-exports` at pre-flight). The two tools disagree on the anchor universe.
- **Audit:** across ALL `docs/**/*-terms.csv`, `public-exports` is the ONLY anchor that is not a `GlossaryTerm` (every other CSV row maps to a term). So the row is anomalous, not a systemic pattern.
- **Fix applied (minimal, root-cause):** removed the single `Public exports,public-exports,...` row from the spec-030 terms CSV. Post-fix: `import_spec_terms` and `--check` pass, `check_spec_glossary` reports `OK: 50 terms` (was 51). The spec body's `[Public exports][glossary-public-exports]` inline ref (spec line ~50) + its ref-def (line ~736) still resolve to the live `## Public exports` GLOSSARY heading — unaffected — so no spec-body edit is needed.
- **Why this is drift, not a unilateral call I'm comfortable owning:** the terms CSV is a spec-companion artifact, and DoD item 1's wording ("every project-specific term that **has** a docs/GLOSSARY.md heading") arguably licenses the `public-exports` row for `check_spec_glossary`'s purposes. The real tension is that `import_spec_terms` is stricter than `check_spec_glossary`. Worker 1 should decide the canonical resolution: (a) keep the CSV row removed (my fix — section anchors don't belong in a terms list `import_spec_terms` treats as terms), or (b) relax `import_spec_terms` to skip/tolerate section-only anchors, or (c) seed `Public exports` as a `GlossaryTerm` (NOT recommended — it is deliberately a shared `BoardDocument` section, and converting it would restructure the GLOSSARY render). I applied (a) to keep the build green and the done-card verifiable; reverse if Worker 1 prefers (b)/(c).

**Confirmation of Worker-1's flagged DB-state risk:** the planning-time claim that `Meta.connection` was missing from the DB is now stale — the term was already seeded (planned) with both memberships and a verbatim body. I flipped it rather than seeding. The regenerate adds the `Meta.connection` entry to `docs/GLOSSARY.md` (absent at HEAD), which is the intended shipped state. No baseline-dirty `docs/GLOSSARY.md` exists at session start (its diff vs HEAD was empty); the build-plan's baseline-dirty note for `docs/GLOSSARY.md` is stale (that anchoring was committed/regenerated away before this slice).

---

## Review (Worker 3)

Slice 5 is doc-only + DB-edit-then-regenerate. No package `.py` logic touched, so the static-inspection helper was correctly skipped (recorded by W2; re-confirmed: `git status` shows no Slice-5 edit to any `django_strawberry_framework/` file). Review focused entirely on doc/release/CHANGELOG sanity, the DB-regenerate-clean invariant, the public-surface/version invariant, and the terms-CSV row removal.

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

The five hand-edited markdown surfaces tell one coherent story: each frames `DjangoConnectionField` as the newest **shipped (`0.0.9`)** Relay connection field, consistently naming the same three load-bearing facts — sidecar-derived `filter:` / `orderBy:` arguments (from `Meta.filterset_class` / `Meta.orderset_class`), the opt-in `totalCount` via `Meta.connection = {"total_count": True}`, and the `DjangoConnection[T]` return alias. README.md ("Newest shipped surface"), docs/README.md (shipped-surface bullet), TODAY.md (off the waiting list, products-centric activation note), docs/TREE.md (current on-disk `connection.py`/`test_connection.py`), CHANGELOG.md (`[Unreleased]` `### Added`), and the GLOSSARY entries all agree on the same wording skeleton with no contradictions and no near-duplicate boilerplate that should be consolidated (each surface is appropriately scoped to its file's audience). No new helper/constant duplication is possible in a doc/DB-data slice. No DRY findings.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` shows ONLY the Slice-4 export promotion (`from .connection import DjangoConnection, DjangoConnectionField` + `DjangoConnection` / `DjangoConnectionField` added to `__all__`, alphabetical). Slice 5 introduces **no** `__init__.py` change. `__version__` stays `"0.0.8"`; `pyproject.toml` (`version = "0.0.8"`), `uv.lock`, and `tests/base/test_init.py` are all UNCHANGED (verified `git diff --quiet` each). `makemigrations --check --dry-run` → `No changes detected` (DB **data** changed, not schema). Decision 13 (no version bump) is honored.

### CHANGELOG sanity

- **No version-heading promotion (Decision 13):** confirmed no `## [0.0.9]` release heading exists; the new bullets land under the existing `## [Unreleased]` → `### Added` block. Headings under `[Unreleased]` are `### Changed` + `### Added` only — `### Added` is the heading the spec authorizes.
- **Verbatim text:** the two shipped CHANGELOG bullets (`DjangoConnectionField (Relay connection field)` + `Meta.connection opt-in totalCount`) match the plan's pinned text **character-for-character** (verified via a Python `==` diff against the artifact's pinned fenced block — EXACT MATCH).
- **Ref-defs resolve:** all six refs used by the bullets (`[glossary-djangoconnectionfield]`, `[glossary-djangoconnection]`, `[glossary-metaconnection]`, `[glossary-metainterfaces]`, `[glossary-djangotype]`, `[connection]`) have defs in CHANGELOG.md's bottom block; each target exists on disk (`connection.py`) or as a live GLOSSARY anchor (`## DjangoConnectionField` / `## DjangoConnection` / `## Meta.connection` / `## Meta.interfaces` / `## DjangoType` all present).
- **No over/understatement:** the bullets accurately describe the shipped behavior (synthesized-signature arg injection, composition pipeline, the extracted-from-`_optimize` cooperation point, the `first`+`last` guard, selection-gated per-instance `totalCount`). Nothing claims nested-`edges{node}` planning (correctly absent — that is `033`).

### Documentation / release sanity

- **Version strings / statuses / card IDs:** on-disk version held at `0.0.8` everywhere (README.md `**0.0.8**` token preserved; only the prose "Newest shipped surface" clause changed). All connection-field surfaces tagged `0.0.9` consistent with the spec.
- **KANBAN card move:** `WIP-ALPHA-030` has **0** occurrences in both KANBAN.md and KANBAN.html. The card heading `### [DONE-030-0.0.9 — DjangoConnectionField]` appears **exactly once**, under `## Done`. (The other `DONE-030-0.0.9` mentions in KANBAN.md are legitimate cross-references from sibling cards' dependency/related lines.) All 10 Definition-of-done items render `- [x]`. The card's `- Status: Planned` metadata field is a board-wide convention shared by other DONE cards (e.g. DONE-029) — column placement, not the status property, marks completion; not a Slice-5 regression. The card's `Spec:` ref is the canonical `docs/spec-030-connection_field-0_0_9.md`; the card-body DoD's prior unnumbered `docs/spec-connection.md` reference was rewritten (B6) — no stale `docs/spec-connection.md` remains in the 030 card body. (Remaining repo hits for that string are the 033 card's hypothetical future-spec mention and the spec-030 body's own deliberate rename-decision text — both correct.) No stale `[0.0.9]`/`[0.0.X]` release-heading reference in the card body.
- **Markdown links:** new ref-defs disk-checked. docs/README.md `[glossary-djangoconnectionfield]: GLOSSARY.md#djangoconnectionfield` added alphabetically under `<!-- docs/ -->`; CHANGELOG `[connection]: django_strawberry_framework/connection.py` (file exists) + the five glossary anchors (all live H2 entries). docs/TREE.md uses plain code-fence text (no ref-style needed for fenced tree content); TODAY.md's `TODO-BETA-051-0.1.5` is inline code (not a cross-file link).
- **GLOSSARY flips:** Index table (lines 59/60/83) shows `DjangoConnection` / `DjangoConnectionField` / `Meta.connection` all `shipped (0.0.9)`; entry-body `**Status:**` lines all flipped to `shipped (0.0.9).`; `Connection-aware optimizer planning` stays `planned for 0.0.9` (Index line 55). Browse-by-category: `Meta.connection` present in **Type generation** (between `Meta.interfaces` / `Meta.nullable_overrides`) and **Relay** (between `DjangoConnection` / `Connection-aware optimizer planning`). The `Meta.connection` body describes the `{"total_count": bool}` shape and the `strawberry.relay.Node` requirement. The `DjangoConnectionField` body honesty edit (B3) landed: sidecar-arg / composition-order / opt-in-`totalCount` / per-shape-connection-class detail added; `search:` qualified as reserved for `Meta.search_fields` (`0.1.2`), not generated in `0.0.9`; the flat-walker cooperation-point alpha-constraint note (empty plan in `0.0.9`, nested planning is `033`, strictness-`"raise"` surfaces the N+1) present — satisfies the spec `## Doc updates` GLOSSARY bullet.
- **DB-regenerate clean (the canonical proof):** re-ran all three generators (`build_kanban_md.py`, `build_kanban_html.py`, `build_glossary_md.py`); **shasums of KANBAN.md / KANBAN.html / docs/GLOSSARY.md are byte-identical before and after regenerate** → the committed working-tree docs exactly match the DB. My regenerate did not dirty the tree beyond Worker 2's state. `import_spec_terms --check` → `OK: 30 done cards have glossary links.` `check_spec_glossary --spec spec-030` → `OK: 50 terms`. `manage.py check` → `System check identified no issues (0 silenced)`.
- **No obsolete wording:** scanned all five updated markdown files for stale "in progress" / "coming next" / "planned" / "waiting" / `WIP-ALPHA-030` framing of the connection field — none. (The one docs/README.md `*(in progress)*` line correctly scopes to the *remaining* 0.0.9 cohort — full Relay story / connection-aware planning / DX cleanup, all genuinely WIP — and explicitly notes "(`DjangoConnectionField` shipped above)".)

### What looks solid

- The (A) hand-edited markdown / (B) DB-edit-then-regenerate split was honored exactly — no hand-edits to the generated KANBAN/GLOSSARY markdown (proven by the byte-identical regenerate).
- Verbatim CHANGELOG match to the plan's pinned text; clean ref-def hygiene across all updated files.
- The card-completion wrap satisfied the done-card invariants correctly (bootstrap `CardGlossaryTerm` before the done-flip, then `import_spec_terms` reconciled the full link set; spec ref + DoD ticks landed).
- Decision 13 fully respected: no version-file edits, no release-heading promotion.
- The `DjangoConnectionField` body honesty edit is the right call — it removes the overstated "composes with the optimizer for nested-selection planning / works at nested relation fields" prose that would have misrepresented the `0.0.9` alpha reality (empty plan; nested planning is `033`).

### Temp test verification

No temp tests created. Verification was via the management commands, the three generators (shasum-diff), `git diff`, and targeted reads — no `docs/builder/temp-tests/slice-5/` artifacts. Independently confirmed Worker 2's "no test edits needed" claim by reading `examples/fakeshop/test_query/test_kanban_api.py` and `test_glossary_api.py`: both are `@pytest.mark.django_db` suites with self-contained `_seed_board()` / `_seed_glossary()` fixtures on a fresh transactional DB; neither reads the committed `db.sqlite3` row data nor asserts global term/card counts, so the Slice-5 DB-data mutations (which only feed the `build_*.py` generators) do not reach them.

### Notes for Worker 1 (spec reconciliation)

**Terms-CSV `public-exports` row removal — ratify Worker 2's fix (verified correct; spec-companion custody is yours).**

Worker 2 removed the row `Public exports,public-exports,...` from `docs/spec-030-connection_field-0_0_9-terms.csv`. I independently verified the root cause and the fix:

- `public-exports` is **not** a `GlossaryTerm` (DB query: `GlossaryTerm.objects.filter(anchor='public-exports').exists()` → `False`). The `## Public exports` GLOSSARY H2 is a board-document/section heading, not a term.
- The two tools genuinely disagree on the anchor universe: `scripts/check_spec_glossary.py` (`_load_rows` / `glossary_anchors`) only requires a matching `## <heading>` GitHub auto-anchor, so it accepted `public-exports` at pre-flight (`OK: 51 terms`). `import_spec_terms.py` line 114-117 does `GlossaryTerm.objects.get(anchor=...)` and raises `Missing GlossaryTerm anchor 'public-exports'` — which hard-blocked `import_spec_terms` once card 030 flipped to done.
- **Audit:** across ALL `docs/**/*-terms.csv`, after removal `public-exports` was the **only** non-GlossaryTerm anchor — the row was anomalous, not systemic.
- The spec body's `[Public exports][glossary-public-exports]` inline ref (spec line 50) + its ref-def (line 736) still resolve to the live `## Public exports` GLOSSARY heading — unaffected by the CSV row removal, so no spec-body edit is needed.

Worker 2 applied fix (a) — remove the row. I concur this is the correct minimal root-cause fix and recommend Worker 1 ratify it: a section anchor does not belong in a terms list that `import_spec_terms` treats as `GlossaryTerm`s, and DoD item 1's wording ("every project-specific term that **has** a docs/GLOSSARY.md heading") is satisfied for genuine terms without it. Alternatives (b) relax `import_spec_terms` to tolerate section-only anchors, or (c) seed `Public exports` as a real `GlossaryTerm`, are both heavier and (c) would restructure the GLOSSARY render of a deliberately-shared section — not recommended. The deeper tooling tension (two tools, two anchor-universe definitions) is a possible future-spec cleanup candidate but is out of scope for this card; flagging it for the catalog.

**Spec checklist tick audit:** all 8 verbatim sub-checks are `- [x]` and each is reflected in the diff (GLOSSARY flips + Meta.connection shape/Relay-Node/browse rows; docs/README move; TREE current-on-disk `connection.py` no-`[alpha]` + `test_connection.py`; TODAY off-the-waiting-list products-centric; README newest-shipped line; CHANGELOG `[Unreleased]` `### Added` no-heading-promotion; KANBAN WIP→DONE canonical spec ref; no version-file edits). No over-ticks, no silently-unaddressed boxes.

**Planning-time DB-state drift (informational):** the plan's B1/B2 (seed `metaconnection`) were already satisfied in the DB at build time — Worker 2 found the term pre-seeded (planned, body verbatim, both memberships) and only flipped its status (B3) rather than re-seeding. Net end state is identical and verified correct (regenerate byte-clean). No action needed; noted so final-verification doesn't expect a fresh seed in the diff.

### Review outcome

`review-accepted`. Zero High / Medium / Low findings. DB-regenerate is byte-clean; public-surface and version invariants hold (no `__init__.py` Slice-5 change, `__version__` 0.0.8, no version-file edits, no `[0.0.9]` heading); CHANGELOG verbatim-matches the plan with correct heading and resolving refs; KANBAN card moved to Done exactly once with DoD ticked and canonical spec ref; GLOSSARY flips and `Meta.connection` body/browse rows correct. The one spec-companion edit (terms-CSV `public-exports` row removal) is verified-correct and escalated to Worker 1 for ratification (custody), not a blocker.

---

## Final verification (Worker 1)

### Summary

`final-accepted`. Slice 5 — the final functional slice — is verified clean. This is a doc + DB-edit-then-regenerate slice with ZERO package `.py` logic; the only `__init__.py` modification in the tree is the carried-in Slice-4 export, not a Slice-5 change.

**Spec slice checklist audit (8/8 `- [x]`, no over-tick, no remaining `- [ ]`):**

1. **GLOSSARY flips** — `docs/GLOSSARY.md` Index rows: `DjangoConnection` (L59), `DjangoConnectionField` (L60), `Meta.connection` (L83) all `shipped (`0.0.9`)`; entry-body `**Status:**` lines flipped (L276/284/603); `Connection-aware optimizer planning` stays `planned for `0.0.9`` (Index L55). `Meta.connection` present in Index + "Type generation"/"Relay" browse rows; body describes `{"total_count": bool}` + `relay.Node` requirement. `DjangoConnectionField` body carries the Slice-3 honesty edit (empty plan in `0.0.9`, nested planning is `033`, strictness-`"raise"` surfaces the N+1). LANDED.
2. **`docs/README.md`** — connection field moved to shipped surface; sidecar args + opt-in `totalCount` noted. LANDED.
3. **`docs/TREE.md`** — `connection.py` on current on-disk layout (no `[alpha]`) + `test_connection.py` on the test tree. LANDED.
4. **`TODAY.md`** — `DjangoConnectionField` off the waiting list, products-centric activation note. LANDED.
5. **`README.md`** — "Newest shipped surface" clause leads with the connection field; on-disk `**`0.0.8`**` version token preserved (Decision 13). LANDED.
6. **`CHANGELOG.md`** — two `### Added` bullets under `## [Unreleased]` (L27 + the `Meta.connection` bullet); NO `## [0.0.9]` release heading. LANDED (per-card permission grant honored).
7. **`KANBAN.md`** — `WIP-ALPHA-030` = 0 occurrences in both KANBAN.md/KANBAN.html; `### [DONE-030-0.0.9 — DjangoConnectionField]` once under `## Done` (KANBAN.md L1532); all 10 DoD items render `- [x]`; card `Spec:` ref canonical (`docs/spec-030-connection_field-0_0_9.md`, L1539). LANDED.
8. **No version-file edits** — `pyproject.toml` / `__version__` / `tests/base/test_init.py` / `uv.lock` unchanged; `__version__ = "0.0.8"`. LANDED (Decision 13).

**DB-regenerate clean:** re-ran `scripts/build_kanban_md.py`, `scripts/build_kanban_html.py`, `scripts/build_glossary_md.py`; `shasum -c` of KANBAN.md / KANBAN.html / docs/GLOSSARY.md is byte-identical before vs after regenerate (the committed working-tree docs exactly match the DB — the `git diff` vs HEAD is the intended Slice-5 change, not post-regenerate drift). `import_spec_terms --check` → `OK: 30 done cards have glossary links.` `manage.py check` → `System check identified no issues (0 silenced)`. `check_spec_glossary --spec spec-030` → `OK: 50 terms`.

**Guards:** `pyproject.toml` / `tests/base/test_init.py` / `uv.lock` show no diff; `__init__.py` diff is ONLY the Slice-4 `from .connection import DjangoConnection, DjangoConnectionField` + two alphabetical `__all__` entries (no version change). No `[0.0.9]` release heading. Decision 13 fully honored.

**DoD 8-11 cross-check:** item 8 (GLOSSARY flips + 4 doc surfaces + CHANGELOG `[Unreleased]` `### Added`) ✓; item 9 (KANBAN `DONE-030-0.0.9` from WIP, canonical card spec ref) ✓; item 10 (no version bump, no release-heading promotion) ✓; item 11 (coverage is CI's gate; no worker pytest run — N/A this pass) ✓.

**Terms-CSV `public-exports` removal — RATIFIED.** See Spec changes below; the removal is the correct root-cause fix, the spec body ref still resolves, and `check_spec_glossary` is OK.

### Spec changes made (Worker 1 only)

1. **Ratify the terms-CSV `public-exports` row removal** — `docs/spec-030-connection_field-0_0_9-terms.csv` (1 deletion: the `Public exports,public-exports,…` row), triggered by Slice 5 (the card-done flip made `import_spec_terms` process the CSV, which hard-fails on a non-`GlossaryTerm` anchor). Ratified Worker 2's fix (option a) as spec custodian: `public-exports` resolves to the GLOSSARY `## Public exports` board-document **section heading**, not a `GlossaryTerm`, so it does not belong in a terms list `import_spec_terms` treats as terms (`GlossaryTerm.objects.get(anchor=...)`). `check_spec_glossary` only needs an `## H2` GitHub-anchor, so it passed pre-flight (`OK: 51`→`OK: 50` after removal — one fewer term, expected). Verified: the spec body's `[Public exports][glossary-public-exports]` inline ref (L50) + its ref-def `GLOSSARY.md#public-exports` (L736) still resolve to the live `## Public exports` heading (GLOSSARY L22) — unaffected by the CSV row removal, so NO spec-body edit needed. Audit confirmed `public-exports` was the only non-`GlossaryTerm` anchor across all `docs/**/*-terms.csv` — anomalous, not systemic. The deeper tooling tension (`import_spec_terms` stricter than `check_spec_glossary` on the anchor universe) is logged as a future-spec cleanup candidate for the deferred-work catalog, out of scope for this card. I own this removal.
2. **Advance the spec status line** — `docs/spec-030-connection_field-0_0_9.md` line 5, triggered by Slice 5 being the last functional slice: `in build — Slice 4 accepted` → `in build — Slices 1-5 accepted; integration + final-gate pending`. `check_spec_glossary` OK: 50 terms after the edit.
