# Build: Slice 5 — doc updates + card-completion wrap

Spec reference: `docs/spec-031-globalid_encoding-0_0_9.md` (lines 105-113)
Status: final-accepted

## Plan (Worker 1)

Slice 5 has two natures, planned separately below:

- **A. Plain-markdown standing-doc edits** (hand-edited files): `docs/README.md`, `docs/TREE.md`, `README.md`, `TODAY.md`, `CHANGELOG.md`.
- **B. DB-backed generated-doc edits** (edit `examples/fakeshop/db.sqlite3` via the Django ORM, then regenerate — NEVER hand-edit the rendered markdown): `docs/GLOSSARY.md`, `KANBAN.md` (+`KANBAN.html`), plus the companion terms CSV reconciliation.

This slice touches NO package `.py` source logic. **Static inspection helper (`scripts/review_inspect.py`): SKIPPED** — Slice 5 changes only standing docs, the kanban/glossary DB rows, and the terms CSV; there is no Python source under `django_strawberry_framework/` in this slice, so none of the helper's run-triggers (`optimizer/`, `types/`, ≥30 logic lines in-package, ≥50 outside) apply. Recorded skip + reason here per `BUILD.md` "When to run the helper".

### Baseline conditions found at planning (READ-ONLY DB queries; no writes made)

1. **`docs/GLOSSARY.md` is NOT byte-clean against a DB regenerate right now.** Running `scripts/build_glossary_md.py` against the committed DB DROPS 10 lines: exactly the `<!-- TODO(spec-031-globalid_encoding-0_0_9 Slice 5) ... -->` comment block at `docs/GLOSSARY.md` lines 22-30 (the staged-slice TODO anchor, AGENTS.md #26). That block is hand-placed in the committed markdown and is not in the DB, so the renderer cannot reproduce it. **This is expected and correct for this slice:** Slice 5's job is to *resolve* that TODO (per AGENTS.md #26, a staged-slice TODO is removed in the same change that ships the slice). After Slice 5 seeds the two new glossary terms + extends the Relay body in the DB and regenerates, the committed `GLOSSARY.md` will lose the TODO block AND gain the new content — the regenerate is then byte-clean against the new committed file. **Worker 2 must NOT re-add the TODO comment after regenerate, and must NOT treat the TODO-block deletion as drift** — its removal is part of shipping the slice. The same staged-TODO removal applies to the hand-edited markdown TODO blocks in `docs/README.md` (lines 80-87), `docs/TREE.md` (lines 7-14), `README.md` (lines 52-58), `TODAY.md` (lines 9-16), and `CHANGELOG.md` (lines 21-28) — Worker 2 removes each TODO block in the same edit that lands that file's content.
2. **`manage.py import_spec_terms --check` already fails on an UNRELATED spec-030 baseline condition.** The global `--check` currently errors: `GlossarySpecMention rows for docs/SPECS/spec-030-connection_field-0_0_9.md do not match ... [] != [...]`. spec-030's `SpecDoc.url` was archived to `docs/SPECS/spec-030-...` and there ARE 50 `GlossarySpecMention` rows under a `spec-030` path, so this is the **concurrent maintainer "archive 030"** activity named in the build context (mid-archive path-mismatch state) — NOT something Slice 5 introduces or may touch (AGENTS.md #33: presumptively another dev's in-progress work; do not auto-revert). **Implication for Slice 5's verification gate:** the canonical procedure's step-8 check "`import_spec_terms --check` reports OK for all done cards" cannot pass globally while the spec-030 archive is mid-flight. Worker 2 must verify card-031's OWN reconciliation succeeded (the 031 GlossarySpecMention/CardGlossaryTerm rows match `docs/spec-031-globalid_encoding-0_0_9-terms.csv`) — e.g. by reading the `import_spec_terms` run output for the 031 spec_path specifically — and record the spec-030 `--check` failure as a pre-existing out-of-scope baseline, NOT a Slice-5 regression. If the spec-030 state blocks `import_spec_terms` from running at all (vs. just reporting a non-OK `--check`), STOP and escalate to the maintainer rather than guessing.
3. **The card's `SpecDoc` already exists and is correct.** `Card(number=31)` already has `SpecDoc(name="spec-031-globalid_encoding-0_0_9", url="https://github.com/riodw/django-strawberry-framework/blob/main/docs/spec-031-globalid_encoding-0_0_9.md")` — the procedure step 2 ("create the SpecDoc") is therefore a **confirm**, not a create. The card currently has **0** `CardGlossaryTerm` rows (procedure step 3 bootstrap still required before the done-save).

### DRY analysis

- **Existing patterns reused (cite path / line).**
  - **Canonical phrasings reused from the spec — do not re-invent prose.** The shipped-surface wording for every doc edit is derived from the spec, single-sourced:
    - The four-strategy semantics (`model` default / `type` opt-out / `type+model` transitional / callable encode-only) come from spec Decision 4 (`docs/spec-031-globalid_encoding-0_0_9.md` lines 318-329).
    - The precedence (`Meta.globalid_strategy` → `RELAY_GLOBALID_STRATEGY` → `"model"`) comes from Decision 5 (lines 342-344).
    - The `Meta.globalid_strategy` validation surface (net-new `ALLOWED_META_KEYS` key, callable arity/sync check, Relay-Node gating) comes from Decision 6 (lines 356-365).
    - The `RELAY_GLOBALID_STRATEGY` settings discipline (thin `conf.py` reader, validated at finalization, shared validator) comes from Decision 7 (lines 379-381).
    - The breaking-change posture + the **exact** `type+model`-first upgrade sequence + the not-a-rename-history-alias-map caveat come from Decision 9 (lines 436-454).
  - **One canonical breaking-change narrative, three render targets, no duplicated prose beyond what each needs.** The `type+model`-first upgrade sequence is the single load-bearing fact. It is written in full (3 ordered steps + the rename-ordering caveat) in `CHANGELOG.md` (the durable release record) and in `TODAY.md` (the products-centric playbook). `docs/GLOSSARY.md` (Relay Node integration body), `docs/README.md`, and `README.md` describe the model-anchored default + the opt-out and **link/point** to the detail rather than re-typing the full 3-step sequence — each says only what its altitude needs. Watch point for Worker 3: the sequence must read coherently in both CHANGELOG and TODAY but must not be a third near-copy elsewhere.
  - **GLOSSARY entry-body shape reused from the recent shipped-`0.0.9` precedents.** `` `Meta.connection` `` (`docs/GLOSSARY.md` lines 611-627) is the net-new-key-stored-on-definition precedent (Decision 6 cites it); `` `Meta.nullable_overrides` `` / `` `Meta.required_overrides` `` (lines 713-741, 799-807) are the companion-pair shipped-`0.0.9` precedent for two related entries that cross-reference each other. The new entries reuse this body shape (one-paragraph lead, a `python` Meta example, a `**See also:**` line) — not a new format.
  - **DB-seeding mechanics reused verbatim from `worker-0.md` "Closing out a kanban card"** (`docs/builder/worker-0.md` lines 159-187) — the GlossaryTerm/membership ORM steps, the SpecDoc/CardGlossaryTerm done-card invariant, the `import_spec_terms` CSV-anchor precondition, and the byte-clean regenerate verification. No new procedure is invented.
- **New helpers justified.** None. Slice 5 introduces no code and no shared helper. All "shared" content is the single-sourced spec phrasing above.
- **Duplication risk avoided.** The naive failure mode is (a) writing the full upgrade sequence in 4+ files (fixed: full sequence only in CHANGELOG + TODAY, summary elsewhere), and (b) hand-editing the generated `GLOSSARY.md` / `KANBAN.md` markdown directly (fixed: every generated-doc change goes through the DB ORM then regenerate, per nature B). A third risk is duplicating the strategy list between the two new glossary entries — avoided by making `RELAY_GLOBALID_STRATEGY`'s body the project-wide-knob view that cross-links `` `Meta.globalid_strategy` `` for the full strategy table (mirroring how `Meta.required_overrides` defers to `Meta.nullable_overrides` for the full validation table).

### One-vs-two GLOSSARY headings decision (PINNED)

**Two separate headings**, not one combined "Django-model-based GlobalID encoding" heading:

- `` ## `Meta.globalid_strategy` `` — backticked title, matching EVERY other `Meta.*` entry (DB title literal `` `Meta.globalid_strategy` ``; anchor `metaglobalid_strategy`).
- `## RELAY_GLOBALID_STRATEGY` — NO backticks in the title, matching the only existing code-symbol-without-`Meta.` precedent `## strawberry_config` (DB title literal `RELAY_GLOBALID_STRATEGY`; anchor `relay_globalid_strategy`).

Rationale: the existing GLOSSARY is strictly one-entry-per-key; the `nullable_overrides`/`required_overrides` companion pair is the exact precedent for two related entries that cross-reference each other. Two anchors are also REQUIRED because (a) the spec's link-definition block and (b) the companion terms CSV reference each symbol independently — a single combined heading would give only one anchor and force one of the two CSV anchors to be a heading-less term the checker rejects. The spec explicitly permits either shape (lines 106 / 628); two is the cleaner fit.

### Implementation steps

Line numbers are pin-at-write-time navigational hints; verify against current source before editing.

#### A. Plain-markdown standing-doc edits (hand-edited)

1. **`docs/README.md`** — in the "Shipped today" surface list (the bullets around `docs/README.md` line 107, `Meta.interfaces = (relay.Node,)` ... `id: GlobalID!`), note that the default Relay `GlobalID` payload is now the model label (`app_label.modelname:<pk>`, e.g. `products.item:42`) and that `Meta.globalid_strategy` / `RELAY_GLOBALID_STRATEGY` provide the `type` opt-out and `type+model` transitional mode. **Resolve the `TODO(spec-031...Slice 5)` comment block at `docs/README.md` lines 80-87** (remove it in the same edit; its 4 pseudocode bullets are the content checklist). Keep the public-helper discussion OUT (sibling 032 owns testing helpers, per the TODO's last bullet + Decision 11). If a new cross-file link is introduced, use reference-style per `START.md`.
2. **`docs/TREE.md`** — **Resolve the `TODO(spec-031...Slice 5)` block at lines 7-14.** Per the TODO: (a) confirm encode/decode ownership stays under `django_strawberry_framework/types/relay.py` — update the `relay.py` annotation in the current on-disk layout (line 229, currently `# Relay Node interface wiring (resolve_* defaults, id suppression, is_type_of injection)`) to also mention the strategy-parameterized `resolve_typename` injection + `decode_global_id`; (b) update the `registry.py` annotation (line 209) to mention `TypeRegistry.definition_for_graphql_name` (the net-new `graphql_type_name` lookup). (c) **`conf.py` `RELAY_GLOBALID_STRATEGY` settings note — DISCRETION/CONDITIONAL:** the TODO says "if settings keys are enumerated." TREE.md's `conf.py` lines (179/207/269) currently read only `settings reader (DJANGO_STRAWBERRY_FRAMEWORK)` and do NOT enumerate individual settings keys (no `STRICTNESS`/`SCALAR_MAP`/etc. are listed anywhere). So the layout reference does NOT enumerate settings keys today; per the TODO's conditional ("if ... enumerates") and the spec line 108/631 ("if the layout reference enumerates settings keys"), the cleanest reading is to leave the per-key settings note OUT (do not start enumerating settings keys in a tree that lists none). Worker 2 may add a brief `RELAY_GLOBALID_STRATEGY` mention to the `conf.py` annotation if it judges the tree benefits, but this is NOT required by the spec and must not balloon into a settings-key enumeration. Do NOT add a new module entry (no new module is created — Decision 11).
3. **`README.md` (root)** — the Status paragraph (line 50) currently enumerates `DjangoConnectionField (0.0.9)` as "Newest shipped surface." Update the newest-shipped-surface line to lead with the model-anchored Relay `GlobalID` default (`0.0.9`) and mention `Meta.globalid_strategy` / `RELAY_GLOBALID_STRATEGY`. **Resolve the `TODO(spec-031...Slice 5)` block at lines 52-58.** Per the TODO + Decision 12: do NOT bump `0.0.8` and do NOT promote a release heading (the joint `0.0.9` cut owns version files). The status badge stays `0.0.8`.
4. **`TODAY.md`** — **Slice 5 is the SOLE editor of the `GlobalID`-filtering examples** (per the Slice-4 reconciliation recorded in the spec at line 102 and worker-1 memory; the source TODO at `TODAY.md` lines 9-16 is Slice-5-anchored). Three edits, keeping the file products-centric:
   - Update the `GlobalID`-filtering example at `TODAY.md` lines 192-214 (the `filter: { category: { id: { exact: "<CategoryType GlobalID>" } } }` block) so the placeholder reflects the model-label payload (`products.category:<pk>` — base64-encoded GlobalID of `products.category:<pk>`), and update the surrounding `Relay nodes` prose (line 23, `own-PK GlobalID filtering`) to note the model-anchored default.
   - Add the breaking-wire-format-change note **including the full `type+model`-first upgrade sequence** (Decision 9 lines 446-452: 1. deploy `RELAY_GLOBALID_STRATEGY = "type+model"` while old GraphQL type names still exist → 2. let clients age out old type-name IDs → 3. only then rename GraphQL types / flip to `model`; PLUS the caveat that `type+model` decodes an old type-anchored ID only while its old GraphQL type name still resolves — it is NOT a rename-history alias map, BACKLOG item 39). Frame it parallel to the existing `PositiveBigIntegerField → BigInt` `0.0.6` breaking-wire-format note (TODAY.md line 125 already states that precedent).
   - **Resolve the `TODO(spec-031...Slice 5)` comment at `TODAY.md` lines 9-16.**
   - Keep every example products-only (the file's scope rule at lines 5); do not broaden to library/scalars.
5. **`CHANGELOG.md` — THE PER-CARD PERMISSION GRANT (named explicitly here so Worker 2 does not infer permission from a standing doc).** `AGENTS.md` #"Do not update CHANGELOG.md unless explicitly instructed" withholds CHANGELOG edits by default; **the spec's Slice 5 (lines 111 / 634 / Doc-updates 625 / DoD item 7) grants this exact edit, and this plan names it: Worker 2 IS authorized to edit `CHANGELOG.md` for this slice, and ONLY for the two bullets below.** Under the existing `## [Unreleased]` block:
   - Add a `### Changed` (breaking) bullet for the model-anchored Relay `GlobalID` default flip. It MUST prescribe the `type+model`-first upgrade sequence (set `RELAY_GLOBALID_STRATEGY = "type+model"` while old clients exist → age out old IDs → THEN flip to `model` / rename GraphQL types), WITH the caveat that `type+model` is a strategy bridge, NOT a rename-history alias map (renaming a type/`Meta.name` mid-window still orphans cached old-type-name IDs). Frame it as the breaking-wire-format precedent parallel to the `0.0.6` `PositiveBigIntegerField → BigInt` `### Changed` bullet already in the file (CHANGELOG lines 109-117). State the breakage is *latent* in `0.0.9` (nothing decodes until WIP-ALPHA-032 ships root `node(id:)`).
   - Add an `### Added` bullet for `Meta.globalid_strategy` (net-new `Meta` key, four strategies, Relay-Node-gated, callable arity/sync validated at type creation) and `RELAY_GLOBALID_STRATEGY` (schema-wide default setting; `Meta` → setting → `model` precedence).
   - **Resolve the `TODO(spec-031...Slice 5)` comment block at CHANGELOG lines 21-28.**
   - **NO version-heading promotion** — both bullets stay under `[Unreleased]`; do NOT create a `## [0.0.9]` heading (Decision 12; the joint cut owns the bump). Verify wording does not overstate (it is NOT yet decode-reachable in `0.0.9`) or understate (it IS a breaking default flip for every emitted GlobalID). Use reference-style links for any new cross-file refs and add link defs under the right group header at the bottom block.

#### B. DB-backed generated-doc edits (edit DB via ORM, then regenerate — per `worker-0.md` "Closing out a kanban card")

Run all DB edits via `uv run python examples/fakeshop/manage.py shell`; regenerate from the repo root. **Use the Django ORM only — never raw SQL** (the `post_save` UUID side-row the GraphQL render needs is skipped by a raw INSERT). **Ordering is load-bearing:** seed glossary terms → regenerate GLOSSARY → add the two anchors to the terms CSV → bootstrap+move the card → `import_spec_terms` → fix card body + tick DoD → regenerate all three docs → verify.

6. **Seed the two net-new `GlossaryTerm` rows** (procedure step 1). The committed `GLOSSARY.md` bodies (nature-A authoring decides exact prose, derived from the spec Decisions; see DRY analysis) are the source for `body`. Create with the Django ORM:
   - **`` `Meta.globalid_strategy` ``:**
     - `title = "` + "`" + `Meta.globalid_strategy` + "`" + `"` (literal backticked `` `Meta.globalid_strategy` ``)
     - `anchor = "metaglobalid_strategy"`
     - `title_sort = title.replace("` + "`" + `", "").lower()` → `"meta.globalid_strategy"`
     - `status = GlossaryStatus.objects.get(key="shipped")`
     - `status_text = "shipped (` + "`" + `0.0.9` + "`" + `)"` (literal `shipped (\`0.0.9\`)`)
     - `body =` the committed Relay-strategy-key body (one lead paragraph: net-new Relay-Node-gated `Meta` key declaring the per-type encode strategy; the four strategies `model`/`type`/`type+model`/callable; precedence note pointing at `RELAY_GLOBALID_STRATEGY`; a `python` Meta example; `**See also:**` cross-links to `RELAY_GLOBALID_STRATEGY`, `Relay Node integration`, `Meta.interfaces`, `Meta.name`, `ConfigurationError`).
     - **Ordering (slot right AFTER `` `Meta.filterset_class` ``):** `entry_order = 43`, `index_order = 39` (the preceding alphabetical neighbor `` `Meta.filterset_class` ``'s values — verified in DB: eo=43/io=39, ts=`meta.filterset_class`; the following `` `Meta.interfaces` `` is eo=44/io=40). The tie at (43, `meta.globalid_strategy`) sorts after `meta.filterset_class` and before `meta.interfaces` with no renumbering of any other row.
   - **`RELAY_GLOBALID_STRATEGY`:**
     - `title = "RELAY_GLOBALID_STRATEGY"` (no backticks — matches `strawberry_config`)
     - `anchor = "relay_globalid_strategy"`
     - `title_sort = "relay_globalid_strategy"` (`.lower()`; no backticks to strip)
     - `status = shipped`, `status_text = "shipped (` + "`" + `0.0.9` + "`" + `)"`
     - `body =` the committed settings-key body (the schema-wide default knob on `DJANGO_STRAWBERRY_FRAMEWORK`; `Meta.globalid_strategy` → setting → `"model"` precedence; thin-`conf.py`-reader / validated-at-finalization note; cross-link to `` `Meta.globalid_strategy` `` for the full strategy table; `**See also:**`).
     - **Ordering (slot right AFTER `Relay Node integration`):** `entry_order = 64`, `index_order = 60` (the preceding alphabetical neighbor `Relay Node integration`'s values — verified in DB: eo=64/io=60, ts=`relay node integration`; the following `Response-extensions debug middleware` is eo=65/io=61). Note `"relay node integration"` < `"relay_globalid_strategy"` (space 0x20 < underscore 0x5F), so the tie at (64, `relay_globalid_strategy`) sorts after `Relay Node integration` and before `Response-extensions...`. No renumbering.
   - **`GlossaryCategoryMembership` rows** for the Browse-by-category buckets (procedure step 1; memberships sort by `order` alone within a category, with a `(category, order)` unique constraint AND a `(category, term)` unique constraint):
     - `` `Meta.globalid_strategy` `` → **Type generation** (`key="type-generation"`) AND **Relay** (`key="relay"`).
     - `RELAY_GLOBALID_STRATEGY` → **Relay** (`key="relay"`). (Type generation is the `Meta`-key bucket; the settings symbol belongs to Relay.)
     - To avoid the `(category, order)` collision when inserting into a category mid-list: per the procedure, bump the target category's existing members into a temp band (`order += 1000`) then reassign the full desired `0..N-1` order with the new member placed at its intended position (Type generation: after `Meta.connection` / among the `Meta.*` cluster; Relay: a sensible position, e.g. after `Relay Node integration`). Worker 2 picks the exact in-bucket index (DISCRETION — both new symbols are additive; the bucket order is reader-facing browse order, not a contract).
   - **Reconcile any EXISTING hand-edited body drift (procedure step 1, second clause):** the GLOSSARY regenerate at planning dropped ONLY the TODO comment block (baseline finding 1), which is intentional removal — there is no existing-term *body* drift to sync. Confirm `git diff docs/GLOSSARY.md` after the step-12 regenerate shows ONLY the TODO-block removal + the two new entries + the extended Relay body (no stray reverts of other entries' bodies). If any other entry body reverts, a hand-edit drifted from the DB — sync it from the committed file before proceeding (procedure step 1).
7. **Extend the `Relay Node integration` term body** (DB edit, then regenerate) to describe the model-anchored default + the four strategies + the precedence (spec line 106/628: "extend the Relay Node integration body"). Edit `GlossaryTerm.objects.get(anchor="relay-node-integration").body` to add a paragraph: the `0.0.9` default `GlobalID` payload is the Django model label (`app_label.modelname:<pk>`); `Meta.globalid_strategy` / `RELAY_GLOBALID_STRATEGY` select `model` (default) / `type` (legacy opt-out, byte-identical pre-`0.0.9` payload) / `type+model` (transitional) / callable; precedence `Meta` → setting → `model`. Add `**See also:**` cross-links to the two new anchors. (This body change must be made in the DB so the regenerate reproduces it — NOT hand-edited into the markdown.)
8. **Add the two net-new anchors to `docs/spec-031-globalid_encoding-0_0_9-terms.csv`** (now that they HAVE glossary headings — the spec's Risks item + DoD item 1 say they were intentionally absent until the headings exist). Append two rows in the existing `term,anchor,notes` CSV format:
   - `Meta.globalid_strategy,metaglobalid_strategy,<one-line note: net-new Meta key; the per-type encode strategy (model/type/type+model/callable)>`
   - `RELAY_GLOBALID_STRATEGY,relay_globalid_strategy,<one-line note: schema-wide default setting; Meta→setting→model precedence>`
   This must happen AFTER step 6-7's GLOSSARY regenerate (so every CSV anchor already resolves to a `GlossaryTerm` heading — the `import_spec_terms` precondition) and BEFORE step 11's `import_spec_terms` run (so the 031 GlossarySpecMention reconciliation picks up the two new anchors).
9. **Confirm the `SpecDoc`** (procedure step 2 — already satisfied; baseline finding 3). `Card(number=31)` already has `SpecDoc(name="spec-031-globalid_encoding-0_0_9", url=".../docs/spec-031-globalid_encoding-0_0_9.md")`. Worker 2 confirms it exists and the `url` contains the `docs/spec-031-globalid_encoding-0_0_9.md` path the build/`import_spec_terms` parse; does NOT create a duplicate.
10. **Bootstrap ≥1 `CardGlossaryTerm` then flip status to done** (procedure steps 3-4). The card currently has 0 glossary links (baseline finding 3); the DONE-card invariant (`apps/kanban/signals.py`) requires ≥1 `CardGlossaryTerm` + a linked `SpecDoc` before a `status.key=="done"` save. Create one `CardGlossaryTerm` for `Card(number=31)` pointing at a term in the 031 CSV (e.g. the first CSV term `relay-node-integration`), then `card.status = Status.objects.get(key="done"); card.save()` (ORM `.save()` fires the pre_save validation + sets `milestone_id`). **The rendered id auto-becomes `DONE-031-0.0.9`** (verified: `format_card_id` drops the milestone prefix for done cards and uses the card's own `number=31`; the "next `DONE-NNN`" is therefore **DONE-031-0.0.9**, NOT a re-sequenced number).
11. **Sync the full glossary-link set** (procedure step 5): `uv run python examples/fakeshop/manage.py import_spec_terms`. This processes every done card and creates `CardGlossaryTerm` + `GlossarySpecMention` rows from each card's CSV, including the now-extended 031 CSV. **See baseline finding 2:** the spec-030 archive state may surface a non-OK `--check` later; the bare `import_spec_terms` run (no `--check`) should still process 031. If `import_spec_terms` itself errors out (vs. `--check` reporting non-OK), STOP and escalate.
12. **Fix card-body content + tick DoD** (procedure step 6): the 031 card body has NO stale `docs/spec-0NN` filename ref to correct (verified; the SpecDoc holds the canonical link, and the one `files_touched` item says "the active Relay spec" generically). Mark all SIX `definition_of_done` `CardItem.is_complete = True` (verified there are 6 DoD items, all currently `is_complete=False`) — the done-card convention. Keep edits to what the spec wrap authorizes; leave unrelated card-body prose alone.
13. **Regenerate all three docs** from the repo root (procedure step 7): `uv run python scripts/build_kanban_md.py`, `uv run python scripts/build_kanban_html.py`, `uv run python scripts/build_glossary_md.py`. This is what materializes the DB changes into `KANBAN.md`, `KANBAN.html`, and `docs/GLOSSARY.md`. (Regenerating GLOSSARY here is also what removes the TODO comment block — baseline finding 1 — which is correct.)
14. **Verify** (procedure step 8 — the verification gates, see "Test additions / updates"):
    - `git diff docs/GLOSSARY.md` shows ONLY: the TODO-block removal (lines 22-30), the two new `## ` entries (in their pinned ordering slots), the two new Index rows, the two new Browse-by-category links (Type generation + Relay / Relay), and the extended Relay Node integration body. No unintended reverts.
    - card-031's own `import_spec_terms` reconciliation succeeded (031 GlossarySpecMention rows match the 031 CSV); the global `--check` spec-030 failure is recorded as the out-of-scope baseline.
    - `KANBAN.md` shows `DONE-031-0.0.9` in the Done section (and removed from the WIP/Alpha section) with its DoD items ticked.
    - `uv run python examples/fakeshop/manage.py check` passes.
    - `uv run python scripts/check_spec_glossary.py --spec docs/spec-031-globalid_encoding-0_0_9.md` reports `OK: 31 terms` (was 29; +2 net-new anchors).

Workers never commit — hand the regenerated `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` + `examples/fakeshop/db.sqlite3` + the standing-doc edits + the terms CSV to the maintainer for review.

### Test additions / updates

- **No package test additions/updates.** Slice 5 ships docs + DB rows + the terms CSV; it touches no `django_strawberry_framework/` source and no `tests/` tree. (The functional contract was tested in Slices 1-4.)
- **Verification gates stand in for tests** (these are the Worker-3 / final-verification gates, NOT pytest):
  - `uv run python scripts/check_spec_glossary.py --spec docs/spec-031-globalid_encoding-0_0_9.md` → `OK: 31 terms` (the spec-doc consistency check; every CSV anchor must resolve to a `GlossaryTerm` heading).
  - `uv run python examples/fakeshop/manage.py import_spec_terms` runs clean for card 031, and the 031 reconciliation matches the 031 CSV (card-scoped; the spec-030 `--check` failure is a recorded out-of-scope baseline — finding 2).
  - `git diff docs/GLOSSARY.md` clean against a fresh `build_glossary_md.py` regenerate (proves the DB regenerates the committed glossary identically — the byte-clean invariant).
  - `KANBAN.md` shows `DONE-031-0.0.9` with DoD ticked; `KANBAN.html` regenerated from the same DB.
  - `uv run python examples/fakeshop/manage.py check` passes (model/admin/url consistency).
- Worker 3 should additionally run the BUILD.md `### Documentation / release sanity` and `### CHANGELOG sanity` checks (this slice touches docs + CHANGELOG + KANBAN): confirm the moved card is removed from WIP and appears once in Done; confirm CHANGELOG bullets stay under `[Unreleased]` with no version-heading promotion and no `0.0.8`→`0.0.9` bump; confirm the `type+model` upgrade sequence reads coherently and matches Decision 9; confirm any verbatim GLOSSARY/CHANGELOG text against the spec source.

### Implementation discretion items

Items Worker 1 has assessed and decided belong to Worker 2 (equivalent-shape / additive-ordering choices, not architecture):

- **Exact in-bucket position** of each new `GlossaryCategoryMembership` within its Browse-by-category bucket (Type generation / Relay). The bucket order is reader-facing browse order, not a contract; both symbols are additive. Use the `order += 1000` temp-band → reassign `0..N-1` mechanism (procedure step 1) to dodge the `(category, order)` unique collision; the precise index is Worker 2's call.
- **The exact prose** of the two new GLOSSARY entry bodies and the extended Relay Node integration paragraph, and the exact prose of each standing-doc edit — within the spec-derived content constraints listed in DRY analysis + steps 1-7. The facts are pinned (default = model label; four strategies; precedence; upgrade sequence); the sentence-level wording is Worker 2's, held to the spec's canonical phrasings.
- **Whether to add a brief `RELAY_GLOBALID_STRATEGY` mention to TREE.md's `conf.py` annotation** (step 2c) — the spec makes this conditional on the tree enumerating settings keys, which it does not today, so the default is to omit; Worker 2 may add a one-clause mention if it judges the tree benefits, but must NOT begin enumerating settings keys.

Genuine ambiguities are NOT delegated here; they are surfaced as baseline findings (the spec-030 `import_spec_terms --check` state) with an explicit STOP-and-escalate condition if `import_spec_terms` itself cannot run.

### Spec slice checklist (verbatim)

Copied verbatim from `docs/spec-031-globalid_encoding-0_0_9.md` `## Slice checklist` (lines 105-113). Worker 2 ticks each box as the sub-check lands; Worker 1 audits at final verification.

- [x] Slice 5: doc updates + card-completion wrap (grants the per-card [`CHANGELOG.md`][changelog] edit permission)
  - [x] [`docs/GLOSSARY.md`][glossary]: add a `## Meta.globalid_strategy` entry and a `## RELAY_GLOBALID_STRATEGY` (or a single "Django-model-based GlobalID encoding") entry as `shipped (0.0.9)`, add their Index rows, and add them to the "Relay" / "Type generation" [Browse by category][glossary] rows; extend the [Relay Node integration][glossary-relay-node-integration] body to describe the model-anchored default and the strategy override. **These glossary entries do not exist at spec-authoring time and creating them is out of scope for the [`docs/SPECS/NEXT.md`][next] flow** (see [Risks and open questions](#risks-and-open-questions)) — Slice 5 of the build creates them.
  - [x] [`docs/README.md`][docs-readme]: note the model-anchored `GlobalID` default and the `Meta.globalid_strategy` / `RELAY_GLOBALID_STRATEGY` opt-out in the shipped-surface list.
  - [x] [`docs/TREE.md`][tree]: no new module (encode / decode live in the existing [`types/relay.py`][relay]); add the [`conf.py`][conf] `RELAY_GLOBALID_STRATEGY` settings note if the layout reference enumerates settings keys.
  - [x] [`TODAY.md`][today]: update the products `GlobalID`-filtering examples to the model-label payload and add the breaking-wire-format-change note **including the `type+model`-first upgrade sequence** ([Decision 9](#decision-9--changing-the-default-to-model-is-a-breaking-wire-format-change-acceptable-pre-100); parallel to the `PositiveBigIntegerField → BigInt` `0.0.6` precedent); keep the file products-centric.
  - [x] [`README.md`][readme]: update the status paragraph's newest-shipped-surface line if it enumerates the GlobalID encoding.
  - [x] [`CHANGELOG.md`][changelog]: a `### Changed` (breaking) bullet for the model-anchored `GlobalID` default — which **must prescribe the `type+model`-first upgrade sequence** (set `RELAY_GLOBALID_STRATEGY = "type+model"` while old clients exist, age out old IDs, **then** flip to `model` / rename GraphQL types, with the rename-ordering caveat that `type+model` is not a rename-history alias map — [Decision 9](#decision-9--changing-the-default-to-model-is-a-breaking-wire-format-change-acceptable-pre-100)) — plus an `### Added` bullet for `Meta.globalid_strategy` / `RELAY_GLOBALID_STRATEGY`, both under `[Unreleased]`. **This is the per-card CHANGELOG-edit permission grant** ([`AGENTS.md`][agents] withholds it by default); the Slice 5 maintainer prompt must name this edit explicitly. No version-heading promotion (per [Decision 12](#decision-12--version-bumps-are-owned-by-the-joint-009-cut)).
  - [x] [`KANBAN.md`][kanban]: move [`WIP-ALPHA-031-0.0.9`][kanban] to the Done column with the next `DONE-NNN-0.0.9` id; add / confirm the card body's spec reference points at [`docs/spec-031-globalid_encoding-0_0_9.md`][spec-031] (this document).
  - [x] **No version-file edits in this card.** Leave `pyproject.toml`, [`__version__`][package-init], [`tests/base/test_init.py::test_version`][test-base-init], and `uv.lock` to the joint `0.0.9` cut per [Decision 12](#decision-12--version-bumps-are-owned-by-the-joint-009-cut).

---

## Build report (Worker 2)

Slice 5 split exactly as the plan directed: plain-markdown standing-doc edits first (nature A), then the DB-backed generated-doc work via the Django ORM (nature B), then regenerate all three docs. No package `.py` source touched (helper run correctly skipped per the plan). All seven verbatim sub-checks landed in this diff and are ticked.

### Files touched

**A. Plain-markdown standing-doc edits (hand-edited):**

- `docs/README.md` — resolved the `TODO(spec-031…Slice 5)` block (lines 80-87); added a paragraph after the Relay-Node subsection stating the `0.0.9` model-label default (`app_label.modelname:<pk>`) and the `Meta.globalid_strategy` / `RELAY_GLOBALID_STRATEGY` strategies; kept the public-helper discussion out (032 owns testing helpers). Added reference-style def `[glossary-metaglobalid_strategy]: GLOSSARY.md#metaglobalid_strategy` in the `<!-- docs/ -->` group (alphabetical).
- `docs/TREE.md` — resolved the `TODO` block (lines 7-14); updated the current-on-disk-layout `relay.py` annotation (strategy-parameterized `resolve_typename` injection + `decode_global_id`) and `registry.py` annotation (`definition_for_graphql_name` Relay-Node graphql-type-name lookup). No new module entry (Decision 11). Per step 2c discretion: did NOT add a `conf.py` settings-key note — the tree enumerates no settings keys today, so the spec's conditional ("if the layout reference enumerates settings keys") resolves to omit.
- `README.md` (root) — resolved the `TODO` block (lines 52-58); rewrote the "Newest shipped surface" line to lead with the model-anchored Relay `GlobalID` default (`0.0.9`) + `Meta.globalid_strategy` / `RELAY_GLOBALID_STRATEGY`, demoting `DjangoConnectionField` to "lands alongside". Status badge stays `0.0.8` (no version bump, Decision 12).
- `TODAY.md` — resolved the `TODO` block (lines 9-16); updated the `Relay nodes` bullet to note the model-anchored default; changed the `GlobalID`-filtering example placeholder to the model-label form (`<GlobalID: base64 of products.category:<pk>>`); added a blockquote breaking-wire-format note with the full 3-step `type+model`-first upgrade sequence + the rename-ordering caveat (NOT a rename-history alias map), framed parallel to the `0.0.6` `PositiveBigIntegerField → BigInt` precedent. Kept products-only.
- `CHANGELOG.md` — **per the explicit per-card permission grant, ONLY these two `[Unreleased]` bullets:** a `### Changed` (breaking) bullet for the model-anchored default flip with the full `type+model`-first upgrade sequence + rename caveat + latent-breakage note; an `### Added` bullet for `Meta.globalid_strategy` / `RELAY_GLOBALID_STRATEGY`. Resolved the `TODO` block (lines 21-28). **No version-heading promotion** — both bullets stay under `[Unreleased]`; no `## [0.0.9]` heading created. Added reference-style defs `[glossary-metaglobalid_strategy]`, `[glossary-relay-globalid-strategy]`, `[glossary-metaname]` in the `<!-- docs/ -->` group (alphabetical). Did NOT touch `pyproject.toml` / `__version__` / `test_init.py` / `uv.lock`.

**B. DB-backed generated-doc work (`examples/fakeshop/db.sqlite3` via Django ORM, then regenerate):**

- `examples/fakeshop/db.sqlite3` (binary) — ORM rows created/changed:
  - **2 net-new `GlossaryTerm` rows:** `` `Meta.globalid_strategy` `` (anchor `metaglobalid_strategy`, `entry_order=43`, `index_order=39`, `title_sort="meta.globalid_strategy"`, status `shipped`, `status_text="shipped (\`0.0.9\`)"`, full body w/ 4 strategies + precedence + python example + See-also); `RELAY_GLOBALID_STRATEGY` (anchor `relay_globalid_strategy`, no-backtick title, `entry_order=64`, `index_order=60`, `title_sort="relay_globalid_strategy"`, status `shipped`, body w/ schema-wide-knob view cross-linking the per-type key for the full strategy table). Both slot into their pinned ordering with no renumbering of other terms.
  - **3 net-new `GlossaryCategoryMembership` rows:** `Meta.globalid_strategy` → Type generation (after `metaconnection`, new index 9) AND Relay; `RELAY_GLOBALID_STRATEGY` → Relay (after `relay-node-integration`, new index 1). Both buckets reassigned `0..N-1` via a large-constant shift to dodge the `(category, order)` unique collision.
  - **`Relay Node integration` `GlossaryTerm.body` extended** (DB edit, not hand-edit): added the model-anchored-default paragraph (4 strategies + precedence + "only the type-name slot moved") and extended the `**See also:**` line with the two new anchors.
  - **Card 31 moved to done:** confirmed the existing `SpecDoc(spec-031-globalid_encoding-0_0_9)` (not re-created); bootstrapped 1 `CardGlossaryTerm` (`relay-node-integration`); flipped `card.status` to `done` via `.save()` → renders `DONE-031-0.0.9`; marked all 6 `definition_of_done` `CardItem.is_complete = True`.
  - **`import_spec_terms` (bare run) reconciled all 31 done cards' `CardGlossaryTerm` + `GlossarySpecMention` rows from their CSVs**, including the now-extended 031 CSV (31 anchors, both new anchors present; card-031 mentions AND links match the CSV exactly).
- `docs/spec-031-globalid_encoding-0_0_9-terms.csv` — appended 2 rows (`Meta.globalid_strategy,metaglobalid_strategy,…` and `RELAY_GLOBALID_STRATEGY,relay_globalid_strategy,…`), comma-free notes, AFTER the GlossaryTerm rows existed so `import_spec_terms` / `check_spec_glossary` reconcile.
- `docs/GLOSSARY.md` — regenerated from DB (`scripts/build_glossary_md.py`).
- `KANBAN.md`, `KANBAN.html` — regenerated from DB (`scripts/build_kanban_md.py`, `scripts/build_kanban_html.py`).

### Tests added or updated

- None. Slice 5 ships docs + DB rows + the terms CSV; it touches no `django_strawberry_framework/` source and no `tests/` tree (the functional contract was tested in Slices 1-4). Per the plan, verification gates stand in for tests.

### Validation run

- `uv run ruff format .` — pass (235 files unchanged; only the pre-existing COM812-vs-formatter config warning, AGENTS.md-known). My edits are docs/CSV/DB, so no `.py` churn.
- `uv run ruff check --fix .` — pass ("All checks passed!"). No churn.
- `git status --short` after both ruff invocations — classified:
  - **Slice-5-intended (stay in diff, in Files touched):** `CHANGELOG.md`, `README.md`, `TODAY.md`, `docs/README.md`, `docs/TREE.md`, `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`, `docs/spec-031-globalid_encoding-0_0_9-terms.csv`, `examples/fakeshop/db.sqlite3`.
  - **Cumulative Slice 1-4 accepted diff + Worker 1's spec edit (EXPECTED, NOT churn, NOT reverted):** the seven `django_strawberry_framework/**.py` files, the three `examples/fakeshop/test_query/test_*_api.py` files, the four `tests/**` files, and `docs/spec-031-globalid_encoding-0_0_9.md`.
  - **Concurrent out-of-scope activity (NOT reverted, AGENTS.md #33):** `docs/dry/dry-0_0_9.md` — a DRY-cycle scratchpad (`docs/dry/dry-<X>.md`) modified by the concurrent DRY cycle, not by me. Left untouched.
  - **Untracked build-cycle artifacts (expected):** `docs/builder/bld-slice-*.md`, `docs/builder/build-031-globalid_encoding-0_0_9.md`.
  - No unrelated tool churn to revert. The one-shot ORM seeding scripts were written to the gitignored `docs/builder/temp-tests/` and removed after use.

### Verification gates (run and reported)

- `scripts/check_spec_glossary.py --spec docs/spec-031-globalid_encoding-0_0_9.md` → **exit 1, FAILS:** both GLOSSARY anchors now resolve to headings (check #1 passes), but the **spec body carries no link to `#metaglobalid_strategy` / `#relay_globalid_strategy`** (check #2). The terms exist in `docs/GLOSSARY.md` and in the CSV, but the spec markdown never linked these net-new symbols (they had no anchor at spec-authoring time). Adding a spec body link + link def is a **spec edit, which only Worker 1 may make** — surfaced under `### Notes for Worker 1 (spec reconciliation)` below. The plan's step-14 "`OK: 31 terms`" expectation did not account for this consequence of the (plan-required) CSV addition.
- `manage.py import_spec_terms` (bare) → ran clean: "Imported glossary terms for 31 done card(s)." Card-031's own reconciliation verified: 031 `GlossarySpecMention` rows (31) AND `CardGlossaryTerm` links (31) match the 031 CSV exactly, both new anchors present.
- `manage.py import_spec_terms --check` → **`OK: 31 done cards have glossary links.`** Finding 2 noted a pre-existing spec-030 `--check` failure (`GlossarySpecMention rows for docs/SPECS/spec-030-… [] != […]`). The **bare** `import_spec_terms` run — a required Slice 5 step that processes every done card — incidentally re-synced card-030's `GlossarySpecMention` rows to the archived `docs/SPECS/spec-030-…` path (`_resolve_spec_path` resolves the archived basename), so the global `--check` now passes. I did NOT touch card-030 directly; the canonical command reconciled it by design. (Reported transparently per finding 2.)
- `git diff docs/GLOSSARY.md` → shows EXACTLY the intended changes (finding 1): the TODO block removed (lines 22-30, intended); two new Index rows in their alphabetical slots; two new Browse-by-category links (Type generation gets `Meta.globalid_strategy`, Relay gets `RELAY_GLOBALID_STRATEGY`); the two new `## ` entries in their pinned ordering slots; the extended `Relay Node integration` body + See-also. No spurious reordering/drift of unrelated entries. TODO block NOT re-added.
- `KANBAN.md` → `DONE-031-0.0.9` appears in the Done section with all 6 `definition_of_done` items rendered `- [x]`; `WIP-ALPHA-031-0.0.9` no longer appears as a live card. `KANBAN.html` regenerated from the same DB.
- `manage.py check` → "System check identified no issues (0 silenced)."

### Implementation notes

- **Category-membership reassignment mechanism.** The plan's `order += 1000` temp-band hint collides when the target band overlaps live values during per-row SQLite unique-constraint checks. Used a collision-proof variant instead: park each NEW row in a far-empty band, then shift EVERY membership by a large constant `+1_000_000` (injective, all targets above the current max), then assign final `0..N-1` (all far below the shifted band). Equivalent outcome, no `(category, order)` collision. Verified final orders are contiguous `0..N-1` with no temp-band leftovers.
- **DoD ticking via per-instance `.save()`** rather than a bulk `.update()`, so any `post_save` side-row stays coherent (the rows already existed; only `is_complete` flipped).
- **`status_text` stored as `shipped (\`0.0.9\`)`** (no trailing period) — the renderer appends `**Status:** {statusText}.`, matching every existing `shipped (\`0.0.X\`)` entry.
- **`**See also:**` lines live in `GlossaryTerm.body`**, not in `outgoingLinks` — `render_term` emits only `## title` / `**Status:**` / `body`; the `outgoingLinks` GraphQL field is queried but unused by the renderer. Matched the existing `Meta.connection` body shape.
- **GLOSSARY entry bodies use in-page `](#anchor)` links** (the file's internal convention), NOT cross-file reference-style — consistent with every existing entry.

### Notes for Worker 3

- Verbatim-text checks: the two new GLOSSARY entry bodies and the extended Relay body are Worker-2-authored prose (DISCRETION per the plan), held to the spec's canonical phrasings (Decisions 4/5/9) — not verbatim copies from the spec, so a character-for-character `diff` against the spec does not apply to them. The CHANGELOG/TODAY `type+model`-first sequence IS the load-bearing Decision-9 fact and should read coherently in both (the full 3-step sequence appears in CHANGELOG + TODAY; docs/README, root README, and the GLOSSARY entries summarize-and-point rather than re-type it — the intended single-source shape).
- Public-surface check: `git diff -- django_strawberry_framework/__init__.py` is empty (this slice adds no export); the `__init__.py` modification you may see is not present — Slice 5 touched no package source.
- The `docs/dry/dry-0_0_9.md` modification in `git status` is the concurrent DRY cycle's scratchpad, out of scope, left untouched (AGENTS.md #33).

### Notes for Worker 1 (spec reconciliation)

- **`check_spec_glossary.py --spec docs/spec-031-globalid_encoding-0_0_9.md` exits 1** because the spec body has no link to the two net-new GLOSSARY anchors `#metaglobalid_strategy` / `#relay_globalid_strategy`. This is the direct, expected consequence of the plan-required CSV additions (step 8): the checker requires every CSV term to (1) have a GLOSSARY heading — now satisfied — AND (2) be linked from the spec body. The symbols were intentionally absent from the GLOSSARY/CSV at spec-authoring time, so the spec never linked them. **Resolution is a spec edit only Worker 1 may make:** add one reference-style body link each (e.g. `[\`Meta.globalid_strategy\`][glossary-metaglobalid_strategy]` and `[\`RELAY_GLOBALID_STRATEGY\`][glossary-relay-globalid-strategy]`) plus the two matching defs under the spec's existing `<!-- docs/ -->` link-def group — or run `scripts/check_spec_glossary.py --spec … --auto-link` (the spec already carries a `<!-- docs/ -->` group, so `--auto-link` will work). After that the check should report `OK: 31 terms`. The plan's step-14 "`OK: 31 terms`" expectation assumed the spec already linked these; it did not.
- The `import_spec_terms --check` global pass now succeeds (see Verification gates) — the bare run reconciled the mid-flight spec-030 archive mentions as a side effect of processing every done card. No action needed; flagging so Worker 1 / the maintainer is aware the spec-030 `--check` baseline state described in finding 2 is now resolved (not by editing card-030, but by the canonical command's normal reconciliation).

---

## Review (Worker 3)

Scope: Slice 5 only (docs + release metadata + KANBAN + GLOSSARY + terms CSV + DB). Reviewed via `git diff -- docs/GLOSSARY.md KANBAN.md KANBAN.html CHANGELOG.md docs/README.md docs/TREE.md README.md TODAY.md docs/spec-031-globalid_encoding-0_0_9-terms.csv` plus the `examples/fakeshop/db.sqlite3` ORM rows (reviewed via the rendered-doc output they produced). Cumulative Slice 1-4 `.py`/test diffs, the line-102 TODAY/spec reconciliation (Worker-1 Slice-4 edit), `docs/dry/dry-0_0_9.md`, and the maintainer "archive 030" activity are out-of-scope per the dispatch and were not weighed.

**Static inspection helper: SKIPPED (correct).** Slice 5 touches no package `.py` source — none of the helper's run-triggers (`optimizer/`, `types/`, ≥30 in-package logic lines, ≥50 outside) apply. Skip recorded per BUILD.md "When to run the helper".

### High:

None.

### Medium:

None. (The `check_spec_glossary` exit-1 spec-body-link gap is a Worker-1-only spec edit, escalated below under `### Notes for Worker 1` with an `Escalated:` prefix — it is the in-design consequence of the plan-required CSV addition, NOT a Slice-5 build defect, and re-spawning Worker 2 cannot resolve a spec edit.)

### Low:

None.

### DRY findings

- None. Slice 5 introduces no code and no shared helper. The single load-bearing fact (the `type+model`-first upgrade sequence) is written in full in exactly two render targets — `CHANGELOG.md` (durable release record) and `TODAY.md` (products playbook) — and `docs/README.md`, root `README.md`, and the GLOSSARY entries summarize-and-point rather than re-type it. Verified there is no third near-copy of the full 3-step sequence: the only files carrying all three ordered steps + the rename caveat are CHANGELOG and TODAY; the others carry the one-line `model`/`type`/`type+model`/callable summary only. The two new GLOSSARY entries split cleanly — `Meta.globalid_strategy` carries the full strategy table and `RELAY_GLOBALID_STRATEGY` cross-links to it for the table (mirroring the `nullable_overrides`/`required_overrides` companion precedent), so the strategy list is not duplicated.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty** — Slice 5 made no change to `__all__` or the re-export list. Confirmed; matches the DoD "no new public exports" posture (the public `testing/relay` helpers are sibling-032 scope).

### CHANGELOG sanity

Full check performed (slice touches `CHANGELOG.md`):

- **Only the two granted bullets, both under `[Unreleased]`.** A `### Changed` (breaking) bullet (CHANGELOG.md line 22) for the model-anchored default flip, and an `### Added` bullet (line 26) for `Meta.globalid_strategy` / `RELAY_GLOBALID_STRATEGY`. The TODO comment block (old lines 21-28) was removed (intended). No other CHANGELOG content changed (the existing optimizer-singleton `### Changed` bullet and the `### Added` `inspect_django_type` / overrides / connection bullets are pre-existing Slice-1-4-and-prior content, untouched).
- **No version-heading promotion.** Both bullets stay under `## [Unreleased]` (line 19); the next heading is `## [0.0.8] - 2026-06-03` (line 35) — NO `## [0.0.9]` heading created. Decision 12 satisfied.
- **Version files untouched (Decision 12).** `git status` confirms `pyproject.toml` (`version = "0.0.8"`), `django_strawberry_framework/__init__.py` (`__version__ = "0.0.8"`), `tests/base/test_init.py`, and `uv.lock` are all absent from the working-tree changes.
- **Wording neither overstates nor understates.** The `### Changed` bullet states the break is *latent* in `0.0.9` (nothing decodes until root `node(id:)` ships in 032) — does not overstate — AND that it changes *every* emitted `GlobalID` for a non-opted-out Relay-Node type — does not understate. It prescribes the full `type+model`-first upgrade sequence (3 ordered steps), the step-3-ordering load-bearing caveat, and the not-a-rename-history-alias-map caveat (BACKLOG item 39) — matching Decision 9 character-for-fact. The headings used (`### Changed`, `### Added`) are exactly the ones the spec authorizes (Slice 5 / DoD item 7).
- **Link defs resolve.** New reference-style defs `[glossary-metaglobalid_strategy]`, `[glossary-relay-globalid-strategy]`, `[glossary-metaname]` added in the `<!-- docs/ -->` group (alphabetical); `[backlog]` / `[today]` / `[glossary-djangotype]` / `[glossary-configurationerror]` pre-exist. All used refs have matching defs.

CHANGELOG sanity verdict: **clean.**

### Documentation / release sanity

Full check performed (slice touches docs/KANBAN/GLOSSARY/CSV):

- **`KANBAN.md` + `KANBAN.html`: card move correct.** `WIP-ALPHA-031` appears **0** times in both files; `DONE-031-0.0.9` appears in KANBAN.md exactly in the cohort-summary line, the spec-index table, and once as the card heading under `## Done` (line 1513) — removed from `## In progress`. In KANBAN.html the card renders once with `"status":{"key":"done"}` and `"number":31`. The card body's `Spec:` reference points at `docs/spec-031-globalid_encoding-0_0_9.md` (the live working location, NOT `docs/SPECS/`) — correct per BUILD.md "spec stays at its working location". All 6 `definition_of_done` items render `- [x]`. The "Status: Needs spec" line is the `planning_state` render field (consistent with sibling DONE-030), not a status contradiction. The `DONE-031` id is correct: `format_card_id` drops the milestone prefix for done cards and uses the card's own `number=31`.
- **`docs/GLOSSARY.md`: diff is only the intended changes.** Verified `git diff docs/GLOSSARY.md` shows ONLY: the spec-031 TODO comment block removed (intended per AGENTS.md #26 — NOT flagged as drift); two new Index rows (`Meta.globalid_strategy` alphabetically after `Meta.filterset_class`, `RELAY_GLOBALID_STRATEGY` after `Relay Node integration`); two Browse-by-category additions (Type generation gets `Meta.globalid_strategy`; Relay gets `RELAY_GLOBALID_STRATEGY`); the two new `## ` entries in their pinned slots; the extended `Relay Node integration` body + See-also. No spurious reordering of unrelated entries. **Idempotency confirmed read-only:** ran `scripts/build_glossary_md.py` against the unchanged DB — `md5 docs/GLOSSARY.md` is byte-identical before and after (`51f5612a5a1ca2f1e34ec8f4817516d9`), so the committed file regenerates exactly (the regenerate did not re-add the TODO block and produced no further diff).
- **`docs/spec-031-...-terms.csv`: two new anchor rows added, file otherwise unchanged.** Diff shows exactly the two appended rows (`Meta.globalid_strategy,metaglobalid_strategy,…` and `RELAY_GLOBALID_STRATEGY,relay_globalid_strategy,…`), comma-free notes, in the existing `term,anchor,notes` format. No other CSV lines touched.
- **`docs/README.md` / `docs/TREE.md` / `README.md` / `TODAY.md`: shipped-surface + breaking-format notes landed; all embedded `TODO(spec-031...Slice 5)` blocks resolved (removed), none left dangling.** docs/README.md notes the model-anchored default + the strategies and adds the `[glossary-metaglobalid_strategy]` ref def. docs/TREE.md updates the `relay.py` annotation (strategy-parameterized `resolve_typename` + `decode_global_id`) and the `registry.py` annotation (`definition_for_graphql_name`); correctly omits a settings-key note (the tree enumerates no settings keys — the spec's conditional resolves to omit); adds no new module entry (Decision 11). root README.md leads the newest-shipped-surface line with the model-anchored default, demotes `DjangoConnectionField` to "lands alongside", keeps the badge `0.0.8`. TODAY.md updates the `Relay nodes` bullet + the filter-example placeholder to the model-label form and adds the full 3-step `type+model`-first blockquote framed parallel to the `0.0.6` `PositiveBigIntegerField → BigInt` precedent; products-only scope preserved; the `BACKLOG.md item 39` mention is inline code (no broken ref-link). No obsolete "coming soon"/"planned"/old-version wording remains in the updated lines.
- **New/moved Markdown links resolve.** The two new GLOSSARY anchors (`#metaglobalid_strategy`, `#relay_globalid_strategy`) exist as headings (GLOSSARY.md lines 668, 1047); all new ref defs point at existing files/anchors. GLOSSARY entry bodies use in-page `](#anchor)` links (the file's internal convention) — consistent with every existing entry.
- **Verbatim-text check.** The two new GLOSSARY entry bodies and the extended Relay body are Worker-2-authored prose held to the spec's canonical phrasings (Decisions 4/5/9) — NOT verbatim copies from the spec, so a character-for-character `diff` does not apply (confirmed against the build report's Implementation notes and by reading both against the spec Decisions: facts match — default `model`; four strategies; `Meta` → setting → `model` precedence; Relay-Node gating; callable arity/sync). The load-bearing `type+model`-first sequence (the one fact that must read coherently) was read in full in both CHANGELOG (line 22) and TODAY (lines 209-217) and matches Decision 9's ordering and caveats. No four-backtick-fence concern (no fenced-code drop-ins with matching inner fences in this slice).

Documentation / release sanity verdict: **clean.**

### Spec slice checklist (verbatim) walk

Worker 2 ticked 9 boxes (the slice header + 8 sub-checks). Verified each landed in the diff:

- [x] Slice 5 header — all sub-checks below landed. ✓
- [x] GLOSSARY: two new entries `shipped (0.0.9)` + Index rows + Browse-by-category (Type generation / Relay) + extended Relay body. ✓ (verified in `git diff docs/GLOSSARY.md`)
- [x] docs/README.md: model-anchored default + `Meta.globalid_strategy` / `RELAY_GLOBALID_STRATEGY` opt-out in shipped surface. ✓
- [x] docs/TREE.md: no new module; settings-key note conditionally omitted (tree enumerates none). ✓
- [x] TODAY.md: model-label filter examples + breaking note incl. `type+model`-first sequence; products-centric. ✓
- [x] README.md: status paragraph newest-shipped-surface line updated. ✓
- [x] CHANGELOG.md: `### Changed` (breaking, with upgrade sequence) + `### Added`, both `[Unreleased]`, no version promotion. ✓
- [x] KANBAN.md: `WIP-ALPHA-031` → `DONE-031-0.0.9`, spec ref at live location. ✓
- [x] No version-file edits. ✓ (`git status` confirms pyproject / `__version__` / test_init / uv.lock untouched)

No box was ticked without matching implementation; no sub-check is silently un-addressed.

### Verification gates (re-run by Worker 3)

- `uv run python examples/fakeshop/manage.py check` → "System check identified no issues (0 silenced)." PASS.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` → "OK: 31 done cards have glossary links." PASS. (Card-031 reconciles; the prior spec-030 `--check` baseline failure was incidentally re-synced by the bare `import_spec_terms` run processing every done card — a side effect, not a Slice-5 edit to card-030. Confirmed as Worker 2 reported.)
- `scripts/build_glossary_md.py` read-only regenerate → byte-identical MD5, no further diff (idempotency PASS).
- `scripts/check_spec_glossary.py --spec docs/spec-031-globalid_encoding-0_0_9.md` → exit 1, two net-new anchors missing a spec-BODY link (anchors-as-headings + CSV both satisfied). This is the escalated Worker-1 item below, NOT a Slice-5 build defect.
- Did NOT run pytest; did NOT use any `--cov*` flag (per BUILD.md / role rules). Did NOT run any regenerate in WRITE mode that would change the DB — `build_glossary_md.py` only rewrites the .md from the unchanged DB and produced no diff.

### What looks solid

- The generated-docs-are-DB-backed discipline held end-to-end: GLOSSARY/KANBAN/KANBAN.html all regenerate from the DB, the GLOSSARY regenerate is byte-clean (idempotent), and the TODO-block removals are part of shipping the slice (AGENTS.md #26) — not drift.
- The card move is textbook: removed from WIP, present once in Done, correct `DONE-031` id, spec ref at the live working location, all 6 DoD ticked, plus the auto-rendered Glossary-terms table (the 031 CSR/`CardGlossaryTerm` reconciliation).
- The breaking-change documentation is honest and complete: latent-break framing + the full prescriptive `type+model`-first sequence + the not-an-alias-map caveat, single-sourced into CHANGELOG + TODAY with summarize-and-point everywhere else (clean DRY shape, no third near-copy).
- Decision 12 fully respected: no version-heading promotion, no version-file edits.

### Temp test verification

None. Slice 5 ships no code; no temp tests were needed or created under `docs/builder/temp-tests/`. All verification was via `git diff` reading, read-only regenerate idempotency, and the management-command gates above.

### Notes for Worker 1 (spec reconciliation)

- **Escalated: `check_spec_glossary.py --spec docs/spec-031-globalid_encoding-0_0_9.md` exits 1** — the two net-new anchors `metaglobalid_strategy` / `relay_globalid_strategy` now exist as GLOSSARY headings AND are listed in `docs/spec-031-globalid_encoding-0_0_9-terms.csv`, but the spec BODY does not yet link them, so the checker's link requirement fails. This is the expected, in-design consequence of the plan-required CSV addition (Slice 5 step 8) — Worker 2 correctly did NOT touch the spec (only Worker 1 may). It is **NOT a Slice-5 build defect** and does not by itself force `revision-needed` (re-spawning Worker 2 cannot resolve a spec edit). **Resolution paths for Worker 1's final verification:** (a) add one reference-style body link each (`[\`Meta.globalid_strategy\`][glossary-metaglobalid_strategy]`, `[\`RELAY_GLOBALID_STRATEGY\`][glossary-relay-globalid-strategy]`) plus the two matching defs under the spec's existing `<!-- docs/ -->` link-def group (the group already exists at spec lines 702-737); or (b) run `scripts/check_spec_glossary.py --spec docs/spec-031-globalid_encoding-0_0_9.md --auto-link`. After either, the check should report `OK: 31 terms`. The plan's step-14 `OK: 31 terms` expectation assumed the spec already linked these; it did not at spec-authoring time (the symbols had no anchor then).
- The `import_spec_terms --check` global pass now succeeds (the bare run reconciled the mid-flight spec-030 archive mentions as a normal side effect of processing every done card) — no action needed; flagging that the spec-030 `--check` baseline state from planning finding 2 is now resolved without any direct card-030 edit.

### Review outcome

`review-accepted`. The Slice-5 BUILD work is independently correct and complete: CHANGELOG carries only the two granted `[Unreleased]` bullets with no version promotion (Decision 12 held), the GLOSSARY diff is only the intended changes and regenerates byte-clean, the KANBAN card moved to `DONE-031-0.0.9` exactly once with all 6 DoD ticked and the spec ref at its live location, the terms CSV gained exactly the two anchor rows, and every embedded Slice-5 TODO block was resolved. No High/Medium/Low findings and no DRY findings. The one Medium-tier item (the `check_spec_glossary` spec-body-link gap) is transparently escalated to Worker 1 above with an `Escalated:` prefix and resolution paths — it requires a spec edit only Worker 1 may make, so per BUILD.md `review-accepted` may be set with it escalated rather than blocking the slice.

---

## Final verification (Worker 1)

Outcome: **final-accepted**. The Slice-5 build is independently correct and complete, and the one escalated item (the `check_spec_glossary` spec-body-link gap) was a Worker-1-only spec edit, now made — the check is green. No Slice-5 build defect exists.

### Required spec-custodian edit (the escalated item) — DONE

`scripts/check_spec_glossary.py --spec docs/spec-031-globalid_encoding-0_0_9.md` failed (exit 1) before this pass: the two net-new anchors `metaglobalid_strategy` / `relay_globalid_strategy` had GLOSSARY headings and terms-CSV rows (added by the Slice-5 build) but no spec-body link. Fixed with the minimal natural edit + matching link-defs (recorded under `### Spec changes made (Worker 1 only)` below). Re-run result:

- `uv run python scripts/check_spec_glossary.py --spec docs/spec-031-globalid_encoding-0_0_9.md` → **`OK: 31 terms — all have glossary entries and at least one spec link.`** (exit 0). Was exit 1.

### Spec slice checklist audit (Worker 2 ticked 9 boxes)

Audited every `- [x]` in `### Spec slice checklist (verbatim)` against the actual working-tree diff. **All 9 boxes (slice header + 8 sub-checks) truly landed** — no over-tick, no silently un-ticked box, no remaining `- [ ]`, no deferral needed:

- Slice 5 header — all sub-checks landed. ✓
- GLOSSARY: two new entries as `shipped (0.0.9)` — `` ## `Meta.globalid_strategy` `` (GLOSSARY.md:668) + `## RELAY_GLOBALID_STRATEGY` (GLOSSARY.md:1047); Index rows (lines 89, 113) `shipped (\`0.0.9\`)`; Browse-by-category rows (Type generation gets `Meta.globalid_strategy`; Relay gets `RELAY_GLOBALID_STRATEGY` — lines 135, 144); extended Relay Node integration body (line 1043 + See-also 1045). ✓
- docs/README.md: model-anchored default + `Meta.globalid_strategy` / `RELAY_GLOBALID_STRATEGY` opt-out in shipped-surface list (line 80) + ref def. ✓
- docs/TREE.md: no new module (Decision 11); `relay.py` + `registry.py` annotations updated; settings-key note conditionally omitted (tree enumerates no settings keys). ✓
- TODAY.md: model-label filter example + breaking-wire-format note with the full 3-step `type+model`-first upgrade sequence + rename caveat; products-centric. ✓
- README.md: newest-shipped-surface line leads with the model-anchored default; status badge stays `0.0.8`. ✓
- CHANGELOG.md: exactly two `[Unreleased]` bullets — `### Changed` (breaking, with upgrade sequence + not-a-rename-history-alias-map caveat + latent-break framing) and `### Added` (`Meta.globalid_strategy` / `RELAY_GLOBALID_STRATEGY`); no `## [0.0.9]` heading promotion (next heading is `## [0.0.8]`). ✓
- KANBAN.md: `WIP-ALPHA-031` appears 0 times in KANBAN.md/KANBAN.html; `DONE-031-0.0.9` present (card heading KANBAN.md:1516, all 6 DoD ticked `- [x]`, spec ref at the live working location `docs/spec-031-globalid_encoding-0_0_9.md`). ✓
- No version-file edits: `git status` confirms `pyproject.toml` (`version = "0.0.8"`), `django_strawberry_framework/__init__.py` (`__version__ = "0.0.8"`), `tests/base/test_init.py`, and `uv.lock` are all absent from the working-tree changes. ✓

### DB-backed integrity

- **`git diff docs/GLOSSARY.md` is only intended changes** — the spec-031 TODO block removal (AGENTS.md #26, part of shipping the slice), the two new `## ` entries in their pinned ordering slots, two Index rows, two Browse-by-category links, the extended Relay body + See-also. No spurious reordering/drift of unrelated entries (matches Worker 3's verified review).
- **GLOSSARY regenerate is idempotent (byte-clean).** Read-only re-run of `scripts/build_glossary_md.py` against the unchanged DB left `docs/GLOSSARY.md` byte-identical: MD5 `51f5612a5a1ca2f1e34ec8f4817516d9` before and after, no further diff. The DB reproduces the committed glossary exactly.
- **`import_spec_terms --check`** → `OK: 31 done cards have glossary links.` (exit 0). Card-031 reconciles against the 031 terms CSV (both new anchors present). The prior spec-030 mid-archive `--check` baseline failure (planning finding 2) was incidentally resolved during the build by the bare `import_spec_terms` run reconciling every done card's mentions — confirmed still green this pass; not a Slice-5 edit to card-030.
- **`manage.py check`** → `System check identified no issues (0 silenced).`

### DRY across the build

Clean. The single load-bearing fact (the `type+model`-first upgrade sequence) is written in full in exactly two render targets — `CHANGELOG.md` and `TODAY.md` — and `docs/README.md`, root `README.md`, and the GLOSSARY entries summarize-and-point rather than re-type it. The two new GLOSSARY entries split cleanly: `Meta.globalid_strategy` carries the full strategy table, `RELAY_GLOBALID_STRATEGY` cross-links to it (mirroring the `nullable_overrides`/`required_overrides` companion precedent). No third near-copy. Canonical phrasings reused from the spec Decisions 4/5/9 throughout.

### No focused pytest

Per the dispatch and BUILD.md: Slice 5 touches docs + DB rows + the terms CSV, no package logic or tests, so no focused pytest was run (and never with `--cov*`). The integration pass + final gate run the suite later.

### Summary

Slice 5 shipped the doc + card-completion wrap for the model-based GlobalID encoding card: two net-new `shipped (0.0.9)` GLOSSARY entries (`` `Meta.globalid_strategy` `` + `RELAY_GLOBALID_STRATEGY`) plus Index/Browse rows and an extended Relay Node integration body (all DB-backed, regenerated byte-clean); the model-anchored-default + opt-out notes in docs/README, docs/TREE, root README, and TODAY (with the full prescriptive `type+model`-first breaking-change upgrade sequence in TODAY + CHANGELOG); the two granted `[Unreleased]` CHANGELOG bullets with no version-heading promotion; and the KANBAN move of the card to `DONE-031-0.0.9` with all 6 DoD ticked and the spec ref at its live location. No version files were touched (Decision 12). The build was correct; the only Worker-1 action was the required spec-body-link edit that makes `check_spec_glossary` green.

### Spec changes made (Worker 1 only)

- `docs/spec-031-globalid_encoding-0_0_9.md` line 46 (`## Key glossary references`, the `DjangoType` bullet): repointed the existing `[\`Meta.globalid_strategy\`]` mention from `[glossary-djangotype]` to the new dedicated `[glossary-metaglobalid_strategy]` anchor, and added a `[\`RELAY_GLOBALID_STRATEGY\`][glossary-relay-globalid-strategy]` inline use in the same bullet. **Reason:** the two net-new symbols now have GLOSSARY headings + terms-CSV rows (added by the Slice-5 build), so the spec body must link them for `check_spec_glossary` to pass (DoD item 1). Minimal, natural edit — no prose rewrite.
- `docs/spec-031-globalid_encoding-0_0_9.md` link-definitions block, `<!-- docs/ -->` group (~lines 722, 730): added `[glossary-metaglobalid_strategy]: GLOSSARY.md#metaglobalid_strategy` (alphabetical, after `metafields_class`) and `[glossary-relay-globalid-strategy]: GLOSSARY.md#relay_globalid_strategy` (alphabetical, before `relay-node-integration`). **Reason:** matching reference-style defs for the two new body uses; ref-ids match the form already established in `CHANGELOG.md` / `docs/README.md` so the repo is consistent. Targets resolve to the real GLOSSARY anchors (verified: `check_spec_glossary` → `OK: 31 terms`).
