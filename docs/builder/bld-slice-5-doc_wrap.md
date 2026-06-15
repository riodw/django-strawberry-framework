# Build: Slice 5 — doc updates + card-completion wrap

Spec reference: `docs/spec-034-permissions-0_0_10.md` (Slice checklist lines 75-76; Doc updates lines 472-485; Decision 2 lines 209-217; Decision 13 lines 361-367; Definition of done items 12-13 lines 543-546)
Status: final-accepted

## Plan (Worker 1)

Slice 5 is doc-only + a kanban-DB card move. It ships **no package source change and no test change**. The trickiest property of this slice is that three of its target docs — `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html` — are **GENERATED from `examples/fakeshop/db.sqlite3`** by `scripts/build_glossary_md.py` / `scripts/build_kanban_md.py` / `scripts/build_kanban_html.py`. Those files must be changed by **editing the DB via the Django ORM, then regenerating** — never hand-edited (the next regenerate silently reverts a hand-edit; a raw SQL insert skips the `post_save` UUID side-row the GraphQL render requires). See `docs/builder/BUILD.md` "Generated docs are DB-backed" and `docs/builder/worker-0.md` "Closing out a kanban card".

### Current DB / repo state confirmed this pass (read-only)

Verified against the live DB and checkout (worker-0.md: plan/spec text can be stale — confirm against the DB):

- **Card 34** is `WIP-ALPHA-034-0.0.10` (`Card.objects.get(number=34)`: `status.key == "wip"`, `milestone_id == 1`, title "Permissions subsystem"). The dispatch framing said "move WIP→DONE" and that matches: the concurrent kanban sweep (build plan "Concurrent-sweep update") already moved it To Do→WIP. **Not** at TODO state.
- **A `SpecDoc` already exists** for card 34: `name="spec-034-permissions-0_0_10"`, `url="https://github.com/riodw/django-strawberry-framework/blob/main/docs/spec-034-permissions-0_0_10.md"` — the url's `docs/...` path is correct and points at the live spec (no `docs/SPECS/` subdir, unlike card 33). **Do NOT re-create it** (the procedure's step 2 `SpecDoc.objects.create` is already satisfied; `name` is unique so a re-create would raise). The done-save invariant #1 (linked SpecDoc) is already met.
- **`card.glossary_links.count() == 0`** — the done-save invariant #2 (≥1 `CardGlossaryTerm`) is NOT yet met. This must be bootstrapped before the done-save (procedure step 3), then fully synced by `import_spec_terms` (step 5).
- **Card 34 DoD CardItems:** 11 items (orders 0-10), all `is_complete=False`. Done-card convention flips every DoD item to `True` (procedure step 6).
- **Stale card-body ref:** DoD item order=0 reads `Add \`docs/spec-permissions.md\`.` — the pre-convention filename (Decision 1 renamed it to `docs/spec-034-permissions-0_0_10.md`). Fix the `CardItem.text` (procedure step 6 names "stale spec filename refs").
- **Glossary terms (both exist, both `planned`):**
  - `apply_cascade_permissions` (anchor `apply_cascade_permissions`): `status=planned`, `status_text="planned for \`0.0.10\`"`, `entry_order=6`, `index_order=2`, `title_sort="apply_cascade_permissions"`. Body carries the **"FK / M2M" scope error** to correct and the consumer-example `apply_cascade_permissions(cls, queryset.filter(is_private=False), info)` (no `info.context.user` line in this entry's example — the broken-user-form fix is a GOAL.md concern, see below).
  - `per-field-permission-hooks` (title "Per-field permission hooks"): `status=planned`, `status_text="planned for \`0.0.10\`"`. Body describes `check_<field>_permission` on `FieldSet` with redaction/denial modes.
- **Public exports list is DB-backed**, NOT a static markdown block: it is the `BoardDoc` row `namespace="glossary"`, `key="public-exports"`. Adding the two new symbols means editing that `BoardDoc.body` via ORM, then regenerating GLOSSARY.
- **`check_spec_glossary.py --spec docs/spec-034-permissions-0_0_10.md`** → `OK: 43 terms`, exit 0 (clean now; re-confirm after any CSV edit).
- **`manage.py check`** → "no issues" (clean now).
- **Committed `KANBAN.md`** shows `WIP-ALPHA-034-0.0.10` (lines 100/141/149 etc.); committed `db.sqlite3` matches WIP. The DB/KANBAN/GLOSSARY are NOT in the current `git status` working-tree diff — the concurrent sweep's DB+KANBAN change was committed (commit `d281d34e`), so the baseline for Slice 5's DB edit is the committed WIP state.

### ⛔ Critical blocker found this pass — the terms-CSV duplicate-anchor / `import_spec_terms` collision (READ FIRST)

`docs/spec-034-permissions-0_0_10-terms.csv` contains **two rows that share the anchor `apply_cascade_permissions`**:

```
apply_cascade_permissions,apply_cascade_permissions,the card's deliverable; ...
aapply_cascade_permissions,apply_cascade_permissions,async twin; shares the apply_cascade_permissions entry ... - no own heading by design
```

This is intentional at the doc-design level (spec line 477 / Decision 2: "Net-new entries: none — `aapply_cascade_permissions` is documented inside the existing `apply_cascade_permissions` entry"; CSV note "no own heading by design"). And `scripts/check_spec_glossary.py` **tolerates** it (it validates each row independently — heading exists + spec links the anchor — and never deduplicates; this is exactly the Risks-ledger note at spec line 498b: "the checker has no dedup/collision warning").

**BUT** the canonical card-close tool `manage.py import_spec_terms` (`examples/fakeshop/apps/glossary/management/commands/import_spec_terms.py::Command._load_rows`, lines 110-111) raises `CommandError("Duplicate glossary anchor 'apply_cascade_permissions' in <csv>")` on the second row. The card-completion procedure (worker-0.md step 5) runs `import_spec_terms` over **every** done card and resyncs each from its CSV — so **the duplicate row will hard-fail the card-34 close**. The spec's Risks ledger noted the checker tolerates the dual rows but did NOT anticipate that `import_spec_terms` rejects them.

**Resolution (planned, minimal):** delete the second CSV row (`aapply_cascade_permissions,apply_cascade_permissions,...`) so the CSV carries **one** row for the shared anchor. Rationale:
- A done card can hold only ONE `CardGlossaryTerm` per `(card, term)` and one `GlossarySpecMention` per `(spec_path, term)` (both keyed on the resolved `GlossaryTerm`, and both rows resolve to the *same* `GlossaryTerm` via `anchor`). The two CSV rows therefore cannot produce two distinct DB rows anyway — the second is redundant by construction.
- The async twin "documents inside the existing entry … no own heading by design" (spec line 477) — a single CSV row for the shared anchor is the faithful representation of "one concept, two execution contexts, one heading."
- After deletion `check_spec_glossary.py` still passes (it counts rows, so it will report `OK: 42 terms` instead of 43 — the count drop is expected and correct, since the duplicate was double-counting one anchor).
- The terms CSV is a **hand-edited** file (not DB-backed), so this is a plain-text edit (procedure-wise it belongs to the Slice-5 build pass before `import_spec_terms` runs).

This is also a **spec-reconciliation** item (the Risks ledger should record that the dedup collision is resolved by collapsing the CSV to one row, not merely "eye-checked") — see `### Notes for Worker 1 (spec reconciliation)`.

### DRY analysis

- **Existing patterns reused.**
  - The entire DB-backed card-close procedure is reused verbatim from `docs/builder/worker-0.md` "Closing out a kanban card" → "Procedure" steps 1-8 (no new mechanism invented). The three regenerate scripts (`scripts/build_glossary_md.py`, `scripts/build_kanban_md.py`, `scripts/build_kanban_html.py`) are the single source of truth for the generated docs — there is no parallel hand-edit path.
  - The glossary status flip reuses the shipped status vocabulary: `GlossaryStatus` key `shipped` already exists (alongside `planned`); the renderer (`scripts/build_glossary_md.py:156,199`) reads `term['statusText']` for BOTH the Index row and the entry's `**Status:**` line, so flipping ONE `GlossaryTerm.status` + `status_text` pair updates both rendered surfaces — no duplicate edit. Status-text phrasing mirrors the shipped convention seen on neighbors (e.g. `shipped (\`0.0.9\`)` → use `shipped (\`0.0.10\`)`).
  - The done-card DoD-tick + SpecDoc + glossary-link invariants reuse the exact shapes the existing DONE cards already satisfy (verified card 33 = `DONE-033-0.0.9`, SpecDoc + 38 glossary_links + done status).
  - CHANGELOG `### Added` bullet phrasing mirrors the canonical entries already in `CHANGELOG.md` `## [0.0.9]` (one bold-lead bullet per shipped symbol with glossary cross-links).
- **New helpers justified.** None. Slice 5 adds no code, no script, no helper. All edits are data (DB rows) or prose (hand-edited markdown).
- **Duplication risk avoided.**
  - The naive failure mode is **hand-editing the generated `docs/GLOSSARY.md` / `KANBAN.md` / `KANBAN.html`** — which creates drift the next regenerate reverts. The plan forbids it explicitly: every generated-doc change is a DB edit + regenerate.
  - The second naive failure is editing the GLOSSARY body in the committed file but not in the DB (or vice-versa). The verification step (`git diff docs/GLOSSARY.md` must reflect ONLY intended changes after regenerate) catches any DB-vs-file body divergence — a non-empty *unexpected* diff means the DB still drifts from intended content.
  - Net-new glossary entries: NONE (`aapply_cascade_permissions` documents inside the existing `apply_cascade_permissions` entry — spec line 477). No new `GlossaryTerm` row, no `GlossaryCategoryMembership` reshuffle (the Permissions browse-bucket already lists both terms), no `entry_order`/`index_order` renumbering (a pure in-place status flip + body rewrite).

### Implementation steps

Line numbers are pin-at-write-time navigational hints; verify against current source before editing.

All DB edits run via `uv run python examples/fakeshop/manage.py shell` (ORM only — never raw SQL); regenerate scripts run from the repo root.

#### A. DB-backed: GLOSSARY (edit DB via ORM, then regenerate)

1. **Flip `apply_cascade_permissions` to shipped + rewrite body.** `t = GlossaryTerm.objects.get(anchor="apply_cascade_permissions")`. Set:
   - `t.status = GlossaryStatus.objects.get(key="shipped")`
   - `t.status_text = "shipped (\`0.0.10\`)"`  (matches the neighbor convention, e.g. `shipped (\`0.0.9\`)`)
   - `t.body = <rewritten body>` — rewrite per spec Doc-updates line 477. The body MUST:
     - **Correct the "FK / M2M" scope to forward-FK / OneToOne only** (the current body says "reaching through FK / M2M"; M2M is out of scope per Non-goals line 114). Pin the scope as single-column forward FK / OneToOne (exclude M2M, reverse relations, `GenericForeignKey`/`GenericRelation`, the MTI `<parent>_ptr` parent-link edge).
     - Describe the **walk mechanism** (call-time walk of the model's single-column forward relations, registry primary-type lookup, skip targets without a custom `get_queryset`, intersect `Q(<fk>__in=<visible>) | Q(<fk>__isnull=True)`, target subquery pinned to the caller's resolved DB alias).
     - Name the **four invariants** (ContextVar cycle guard with partial-narrow on cycle break; single-column forward scope; nullable-FK preservation; caller-alias pinning).
     - Name **`fields=` loud validation** (`ConfigurationError` on unknown / non-cascadable names + the bare-string guard).
     - Name the **sync/async pair**: the sync helper raises `SyncMisuseError` for an async target hook (coroutine closed); `aapply_cascade_permissions` wraps the sync walk in `sync_to_async(thread_sensitive=True)`. Document `aapply_cascade_permissions` INSIDE this entry (one concept, two execution contexts — no own heading).
     - Name the **composition rule** (cascade narrows rows first, then the shipped `check_<field>_permission` filter/order gates judge input; composes with connections / node refetch / list fields / nested filter branches through their existing `get_queryset` seams via the optimizer `Prefetch` downgrade).
     - **Correct the consumer example's user read** to the canonical `getattr(getattr(info.context, "request", None), "user", None)` form (the stock `StrawberryDjangoContext` exposes no `.user`; reading `info.context.user` binds `None` and collapses staff/perm branches — spec User-facing API line 169 + this build's Slice-4 central reconciliation). If the rewritten example shows a staff bypass + cascade call, use `info.context.request.user`, NOT `info.context.user`. (The committed entry's current example has no user line, so this is part of authoring the expanded body, not a separate fix — but if Worker 2 adds a staff-branch example, it MUST use the `request.user` form.)
   - `t.save()`.
2. **Re-status `Per-field permission hooks` to `planned for 0.1.1` + Decision-2 note.** `t2 = GlossaryTerm.objects.get(anchor="per-field-permission-hooks")`. Set:
   - `t2.status_text = "planned for \`0.1.1\`"` (keep `t2.status` = `planned` — only the version moves from `0.0.10` to `0.1.1`; the Index row + entry status both re-render from `status_text`).
   - `t2.body = <body + Decision-2 contract note>` — append/weave a note recording the Decision-2 contract: **host** = `FieldSet` (wired via `Meta.fields_class`, the `0.1.1` deliverable); **signature** = `check_<field>_permission(self, info)` (info-shaped read gate, vs the `(self, request)` input gates); **failure modes** = denial (`GraphQLError`) and redaction (safe-value fallback); **composition rule** = a field gate does NOT short-circuit the cascade — the cascade narrows the queryset first, field gates run on surviving rows, so a field denial never leaks the existence of a cascade-hidden row. Preserve the existing redaction/denial description.
   - `t2.save()`.
3. **Cross-reference the cascade from the `get_queryset` visibility hook entry.** `t3 = GlossaryTerm.objects.get(anchor="get_queryset-visibility-hook")`. The entry's "See also" already links `apply_cascade_permissions`; spec line 477 asks to "cross-reference the cascade from the `get_queryset` visibility hook entry." Add a one-sentence body note (Worker 2 discretion on exact wording) that a type's `get_queryset` is the seam `apply_cascade_permissions` composes — it is *called from inside* the hook to reach the type's FK/OneToOne targets' own hooks. Keep the optimizer-cooperation paragraph intact. (If Worker 2 judges the existing "See also" link sufficient, record that judgment in the build report — but the spec explicitly names a cross-reference, so prefer adding the sentence.)
4. **Update the Public-exports list (DB-backed `BoardDoc`).** `d = BoardDoc.objects.get(namespace="glossary", key="public-exports")`. Insert two bullets into `d.body` in the existing alphabetical-ish symbol order (the list runs `BigInt`, `Django*`, `OptimizerHint`, `SyncMisuseError`, `finalize_django_types`, `strawberry_config`, `auto`, `__version__`):
   - `- [\`apply_cascade_permissions\`](#apply_cascade_permissions) — cascade a type's \`get_queryset\` visibility through its single-column forward FK / OneToOne edges (sync).`
   - `- [\`aapply_cascade_permissions\`](#apply_cascade_permissions) — async twin of \`apply_cascade_permissions\` (\`sync_to_async\` wrap); shares the entry.`
   Both anchor at `#apply_cascade_permissions` (shared entry). Placement (top of the re-exports list, before `BigInt`, since `a` sorts first among the symbol names) is Worker 2 discretion — match whatever ordering convention the existing list follows. `d.save()`.
5. **Regenerate GLOSSARY:** `uv run python scripts/build_glossary_md.py`. The Index row for `apply_cascade_permissions` flips to `shipped (\`0.0.10\`)`, the `Per-field permission hooks` row flips to `planned for \`0.1.1\``, the entry bodies + Public-exports list re-render from the DB.

#### B. DB-backed: KANBAN card move (worker-0.md "Closing out a kanban card" procedure)

Run the procedure, ADAPTED to the confirmed DB state (SpecDoc already exists; glossary_links == 0):

6. **Seed net-new glossary terms / reconcile drifted bodies (procedure step 1).** Net-new glossary symbols: NONE (both terms already exist; `aapply_cascade_permissions` shares the existing anchor). The "reconcile existing term whose body the build hand-edited" clause is already handled by steps 1-2 above (the GLOSSARY body edits live in the DB, so step 5's GLOSSARY regenerate will NOT revert them — that is the verification fence in step 12). No additional term seeding.
7. **Fix the terms CSV duplicate-anchor blocker (see the Critical-blocker section).** Before any `import_spec_terms` run: delete the `aapply_cascade_permissions,apply_cascade_permissions,...` row from `docs/spec-034-permissions-0_0_10-terms.csv` (hand edit; the CSV is not DB-backed). Re-run `uv run python scripts/check_spec_glossary.py --spec docs/spec-034-permissions-0_0_10.md` — expect `OK: 42 terms` (count drops by one; that is correct, the duplicate was double-counting one anchor).
8. **SpecDoc (procedure step 2): ALREADY EXISTS — skip the create.** Confirm `SpecDoc.objects.get(card=Card.objects.get(number=34))` resolves and `url` contains `docs/spec-034-permissions-0_0_10.md` (verified this pass). Do NOT `SpecDoc.objects.create` (name is unique — would raise).
9. **Bootstrap ≥1 `CardGlossaryTerm` (procedure step 3)** so the done-save passes invariant #2: create one link for a term in the card's CSV, e.g. `CardGlossaryTerm.objects.create(card=card, term=GlossaryTerm.objects.get(anchor="apply_cascade_permissions"), raw_text="apply_cascade_permissions", order=0)`. `import_spec_terms` reconciles the full set next.
10. **Flip status to done (procedure step 4):** `card.status = Status.objects.get(key="done"); card.save()` — the ORM `.save()` fires the pre_save done-invariant validation (now satisfied: SpecDoc + ≥1 link) and sets `milestone_id`. The rendered id becomes `DONE-034-0.0.10` (done cards drop the milestone prefix).
11. **Sync the full glossary-link set (procedure step 5):** `uv run python examples/fakeshop/manage.py import_spec_terms`. This processes EVERY done card and resyncs `CardGlossaryTerm` + `GlossarySpecMention` from each CSV. **Side-effect to expect (not a defect):** it will also resync card 33's `GlossarySpecMention` rows, which are currently empty (`[]`) per the concurrent-sweep drift — this is the canonical tool *reconciling* committed-but-half-synced data, NOT a worker reverting concurrent work, so it is allowed and correct (worker-0.md step 5 explicitly processes all done cards). The resulting `git diff examples/fakeshop/db.sqlite3` will therefore include card-33 mention rows in addition to card-34's — call this out in the build report so the maintainer is not surprised.
12. **Fix card-body content + tick DoD (procedure step 6):**
    - Edit the stale DoD `CardItem.text` (order=0, section "Definition of done"): `Add \`docs/spec-permissions.md\`.` → `Add \`docs/spec-034-permissions-0_0_10.md\`.` (Decision 1 canonical filename). Scope: only this stale-filename fix; leave all other card-body prose alone.
    - Set `is_complete = True` on every DoD `CardItem` for card 34 (all 11, orders 0-10) — the done-card convention. No `## [0.0.X]` → `[Unreleased]` card-body edit is needed (no DoD item carries a `## [0.0.X]` release-heading ref; the stale-ref scan found only the spec filename + the FieldSet `044`→`046` open-question text, which is a separate pre-existing cross-surface cluster — see Notes).
13. **Regenerate KANBAN (procedure step 7):** `uv run python scripts/build_kanban_md.py` then `uv run python scripts/build_kanban_html.py`. (`build_glossary_md.py` already ran in step 5; re-run it AFTER the DB card move only if any glossary-affecting DB write happened in steps 9-12 — none should, so one GLOSSARY regenerate in step 5 suffices; if in doubt, re-run it — it is idempotent.)

#### C. Hand-edited plain-markdown docs (NOT DB-backed — edit the files directly)

14. **`docs/README.md`** (spec line 479):
    - In the "Shipped today" list (currently ends at the `inspect_django_type` bullet ~line 121), add a permissions bullet for the cascade subsystem (`apply_cascade_permissions` / `aapply_cascade_permissions`, the four invariants, sync/async pair, composition). Mirror the existing bullet style (bold lead + glossary cross-link).
    - In "Coming next — remaining alpha" the `0.0.10` line (line 124 `- \`0.0.10\` — permissions / cascade-permissions subsystem`) shrinks to the `035` remainder (optimizer robustness hardening) — permissions has shipped, so it leaves the Coming-next `0.0.10` line. Worker 2 reshapes that line to describe the `035` remainder only.
15. **`docs/TREE.md`** (spec line 480):
    - Line 262 `permissions.py # planned by TODO-ALPHA-034-0.0.10 - Permissions subsystem` → a real one-line description (e.g. `permissions.py # \`apply_cascade_permissions\` / \`aapply_cascade_permissions\` - cascade a type's get_queryset visibility through single-column forward FK / OneToOne edges.`). NOTE: there are MULTIPLE `permissions.py` lines in TREE.md (151, 184, 262, and the filters/-substrate one at 241/315 which is a DIFFERENT file — the active-input permission substrate, leave it). The package-top-level one carrying the `planned by TODO-ALPHA-034-0.0.10` marker is line 262; lines 151/184 are in other tree views — verify each and update the package-top-level entries consistently (do not touch the `filters/permissions.py` substrate line).
    - Add `tests/test_permissions.py` to the test tree (spec: "`tests/test_permissions.py` joins the test tree"). Locate the `tests/` block and add it in path order.
16. **`TODAY.md`** (spec line 481):
    - "What products is still waiting for" list (line 277): the permissions bullet `- permissions / \`apply_cascade_permissions\` (\`0.0.10\`: \`TODO-ALPHA-033-0.0.10\`) — activates the commented cascade ...` — DROP permissions from the waiting-for list (it has shipped/activated). The stale `TODO-ALPHA-033-0.0.10` id (should be `034`) goes away with the bullet (spec Risks line 497: "Slice 5 corrects `TODAY.md`"). If any other line still cites `TODO-ALPHA-033-0.0.10` for *this* card, fix to `034` / DONE form.
    - Visibility section (line 271): the caveat "(The `products/schema.py` types carry commented cascade-permission `get_queryset` hooks that activate once the permissions card ships — see below.)" rewrites to the LIVE shape — the hooks are now active; describe the cascade as shipped/wired (per Slice 4). The `get_queryset` example at lines 263-268 currently reads `getattr(info.context, "user", None)` — if Worker 2 live-shapes the visibility example to show the cascade, use the canonical `info.context.request.user` form; if it leaves the non-cascade `ItemType` example as-is (it predates this card and is a generic visibility demo, not a cascade demo), that broken-form line is pre-existing TODAY.md content outside this card's named scope — Worker 2 discretion, but flag any left-as-is broken form in the build report. The spec names "the products demonstration sections gain the activated cascade hooks" + "the commented-hook caveat ... rewrites to the live shape" — those two are the in-scope edits.
17. **`README.md`** (spec line 482):
    - The status paragraph's "Newest shipped surface" line (line 50, currently "connection-aware optimizer planning (`0.0.9`)") gains the permissions subsystem as the newest shipped surface (or adds a permissions clause). Worker 2 discretion on phrasing; keep it one coherent sentence consistent with the existing dense status paragraph.
    - The "Coming next" / roadmap `0.0.10` mention — README's roadmap reference (line 46 mentions mutations `0.0.11`; there is no explicit `0.0.10` "Coming next" line in README like docs/README has). If README carries a `0.0.10` roadmap line, update it to the `035` remainder; if it does not, the only README edit is the status-paragraph shipped-surface line. Worker 2 verifies and records which applied.
18. **`CHANGELOG.md`** (spec line 483; Decision 13; build-plan "CHANGELOG-edit permission is Slice-5-only"):
    - There is currently **NO `[Unreleased]` section** — the top released section is `## [0.0.9] - 2026-06-13`. **Add a new `## [Unreleased]` section ABOVE `## [0.0.9]`** with an `### Added` subsection.
    - `### Added` bullets (mirror the `## [0.0.9]` bullet style — bold lead + glossary cross-links):
      - `apply_cascade_permissions` / `aapply_cascade_permissions` — the cascade visibility helper pair (sync + `sync_to_async` async twin), four invariants, `fields=` loud validation, `SyncMisuseError` on async target hooks, composition with the shipped gates / connections / node refetch / list fields via the optimizer `Prefetch` downgrade; exported from the package root.
      - The products cascade activation — the four `examples/fakeshop/apps/products/schema.py` `get_queryset` hooks now cascade across the `Entry → Item → Category` chain, exercised live by `create_users(1)`.
    - **NO version-heading promotion** (Decision 13): do NOT add `## [0.0.10]`. The bullets stay under `[Unreleased]`. Do NOT touch `pyproject.toml`, `__version__`, `tests/base/test_init.py::test_version`, `uv.lock`.

#### D. Verification (after all edits + regenerates)

19. `git diff docs/GLOSSARY.md` reflects ONLY the intended changes (apply_cascade status→shipped + body rewrite; per-field-hooks status→0.1.1 + Decision-2 note; get_queryset cross-ref sentence; Public-exports two new bullets). Any *unexpected* hunk means a DB body still drifts from intended — fix in the DB and regenerate (do NOT hand-edit GLOSSARY.md).
20. `uv run python examples/fakeshop/manage.py import_spec_terms --check` reports OK for all done cards (this is the post-resync state — it should now pass for card 34 AND card 33, since step 11's real run reconciled both). If card 33 still fails `--check` after the real `import_spec_terms` run, that is a deeper pre-existing concurrent-sweep issue (the CSV path / mention rows) — flag to the maintainer, do NOT attempt to fix card 33's data beyond what the canonical tool reconciles.
21. `uv run python examples/fakeshop/manage.py check` passes (0 issues).
22. `KANBAN.md` shows `DONE-034-0.0.10` in the Done section with its DoD ticked; the card's spec reference points at `docs/spec-034-permissions-0_0_10.md`. `KANBAN.html` regenerated byte-consistently.
23. Byte-clean regenerate sanity: re-running all three build scripts a second time produces no further diff (proves the DB is the stable source).

### Test additions / updates

None; doc/DB work. Slice 5 ships no package source change and no test change (spec Implementation-plan table line 379: "New tests: 0 (doc-only)"). The final test-run gate (`bld-final.md`) runs the full `pytest --no-cov` sweep once at the end of the build; Slice 5 introduces no test surface to pin.

### Implementation discretion items

These are assessed and delegated to Worker 2 (style / equivalent-shape, not architecture):

- **Exact prose of the rewritten `apply_cascade_permissions` glossary body** and the `Per-field permission hooks` Decision-2 note — Worker 2 writes the prose; the plan fixes the *required content* (scope correction, four invariants, sync/async pair, composition rule, Decision-2 contract). Constraint: the scope MUST read forward-FK / OneToOne (never "M2M"); any user-read example MUST use `info.context.request.user`.
- **Whether to add a sentence vs. rely on the existing "See also" link** in the `get_queryset` visibility hook entry — prefer adding the sentence (spec names a cross-reference); if Worker 2 judges the existing link sufficient, record the judgment in the build report.
- **Placement of the two new Public-exports bullets** within the re-exports list (top vs. alphabetical-by-symbol) — match the list's existing ordering convention.
- **Exact CHANGELOG bullet wording** and `docs/README.md` / `README.md` / `TREE.md` / `TODAY.md` phrasing — match each file's existing voice; the plan fixes which lines change and the required facts.
- **The bootstrap `CardGlossaryTerm` term choice** (procedure step 9) — any term in the card's CSV; `apply_cascade_permissions` is the natural first.

### Spec slice checklist (verbatim)

The spec's Slice 5 sub-bullets from `## Slice checklist` (lines 75-76), copied verbatim:

- [x] Slice 5: doc updates + card-completion wrap (per [Doc updates](#doc-updates))
  - [x] [`docs/GLOSSARY.md`][glossary], [`docs/README.md`][docs-readme], [`docs/TREE.md`][tree], [`TODAY.md`][today], [`README.md`][readme], [`CHANGELOG.md`][changelog] (the explicit permission grant), [`KANBAN.md`][kanban] (card → Done via the kanban DB + re-render). No version-file edits ([Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-0010-cut)).

### Notes for Worker 1 (spec reconciliation)

Items to weigh at Slice-5 final-verification (Worker 1 owns spec edits; this planning pass made none):

1. **Stale spec status line (line 5).** Reads "Slices 1-3 … shipped; Slices 4-5 remain" but Slice 4 is `final-accepted`. Per Worker 1's per-spawn status-line duty, correct to "Slices 1-4 … shipped; Slice 5 remains" (or, once Slice 5 lands, "all five slices shipped") at final verification. Planning pass leaves it (no spec edit this pass).
2. **Terms-CSV duplicate-anchor / `import_spec_terms` collision (the Critical blocker above).** The Risks ledger (spec line 498b) says the dual-row share is "eye-checked, not tool-enforced" but did NOT anticipate that `import_spec_terms::_load_rows` HARD-REJECTS the duplicate anchor (it is not merely un-warned — it raises and blocks the card close). Slice 5's resolution collapses the CSV to one row. At final verification, **update the Risks line 498b** to record this: the dedup collision is resolved by carrying ONE CSV row for the shared anchor (the second row was unrepresentable as a distinct DB row anyway), and note `check_spec_glossary` reports `OK: 42 terms` after the collapse. This is a genuine spec-vs-tooling reconciliation, not just prose.
3. **GOAL.md `info.context.user` follow-up — DECISION RECOMMENDED (carry-forward from Slice 4).** GOAL.md is NOT in the spec's Slice-5 doc list (spec line 479 names docs/README, docs/TREE, TODAY, README — not GOAL.md). The broken `getattr(info.context, "user", None)` form appears in GOAL.md at the cascade showcase bodies (lines 116, 138) and the shared `_user(info)` helper (line 327, used at 339-397). Slice 4's central reconciliation established the canonical form is `info.context.request.user` and corrected the spec's User-facing API to match — so GOAL.md's astronomy showcase is now **factually wrong** (its cascade hooks would bind `None` for every request, collapsing the staff/perm branches).
   - **Recommendation: option (a) — plan it as an authorized Slice-5 doc-accuracy addition, recorded as a spec reconciliation Worker 1 makes at final verification.** Rationale: (i) the GLOSSARY `info.context.user`-shape fix is already IN scope (spec line 477 / step 1 above), so fixing the same broken form in the sibling showcase doc is the consistent, same-cycle move — leaving GOAL.md wrong while GLOSSARY is corrected would itself be cross-surface inconsistency (the exact anti-pattern worker-0.md warns against); (ii) it is a pure doc-accuracy fix (no contract change); (iii) GOAL.md is the project's pitch/showcase — shipping a permissions card while its flagship permissions showcase is silently broken undercuts the card. The fix is mechanical: `info.context.user` → `getattr(getattr(info.context, "request", None), "user", None)` in the two showcase bodies and the `_user(info)` helper (changing the helper fixes all its call sites at once — DRY). **Because GOAL.md is outside the spec's named Slice-5 doc list, this is a Worker-1 spec-reconciliation act:** add GOAL.md to the Doc-updates list (spec line 479) as an authorized Slice-5 doc-accuracy edit at final verification, OR (option b) surface it to the maintainer as deferred. I recommend (a) but flag it here so Worker 1 at final-verification makes the call explicitly and records the spec edit. If (a): Worker 2 does the GOAL.md edit in the build pass once Worker 1 authorizes it via the spec list; if Worker 1 prefers to keep the build pass strictly to the spec's named list, the GOAL.md fix can be the Worker-1 final-verification spec-reconciliation action's companion — but a doc *content* edit is Worker 2's domain, so the cleaner path is to authorize it into scope BEFORE the build pass. **Concretely: recommend Worker 0 widen the Slice-5 build dispatch to include GOAL.md's `info.context.user` → `request.user` fix, with Worker 1 recording the spec-line-479 addition at final verification.**
4. **Card-33 concurrent-sweep drift (out-of-scope, flag-only).** Card 33 (`DONE-033-0.0.9`) currently fails `import_spec_terms --check` (its `GlossarySpecMention` rows are empty `[]` vs its CSV). This is pre-existing concurrent-sweep drift (build plan "Concurrent-sweep update"), NOT card-34 work. Slice 5's `import_spec_terms` real run will resync it as a documented side-effect (step 11). Do NOT separately edit card-33 data; if the real run does not fully reconcile it, flag to the maintainer. STANDING GUARD: never git-checkout/restore the DB.
5. **FieldSet card-number `044` vs `046` cross-surface cluster (flag-only, NOT a Slice-5 fix).** The card-34 body's open-question text still quotes the older FieldSet card `044` while the live card is `TODO-BETA-046-0.1.1` (spec Revision-2 L1 noted this). This is a multi-surface stale reference (card body + possibly spec prose); per worker-0.md, do NOT partial-fix one surface — record as a maintainer / next-spec-author follow-up in the deferred-work catalog (`bld-final.md`). Slice 5 does not touch it.

---

## Build report (Worker 2)

Slice 5 landed end-to-end: CSV-dedup blocker fixed, GLOSSARY flipped + body-rewritten via the DB, card 34 moved WIP→DONE, the five hand-edited plain-markdown docs + GOAL.md updated, and all three generated docs re-rendered byte-clean. No version-file touched. The trickiest part was an unanticipated pre-existing DB-vs-committed-GLOSSARY divergence (see Implementation notes / Notes for Worker 1).

### Files touched

**DB-backed (edited via the Django ORM, then regenerated — never hand-edited):**
- `examples/fakeshop/db.sqlite3` — all glossary + kanban edits via `manage.py shell` (ORM only, no raw SQL) + the `import_spec_terms` real run. Mention-row diff scope (HEAD → now): `docs/spec-034-permissions-0_0_10.md` 0 → 42 (card-34's deduped CSV) and `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` 0 → 38 (card-33's previously-empty mentions resynced by the canonical tool — the documented side-effect, NOT a worker revert). Glossary-term body edits: 4 intended (`apply_cascade_permissions`, `per-field-permission-hooks`, `get_queryset-visibility-hook`, public-exports `BoardDoc`) + 8 pre-existing-drift reconciliations (see notes).
- `docs/GLOSSARY.md` — regenerated by `scripts/build_glossary_md.py`. Diff = exactly 6 intended hunks: public-exports +2 bullets (`apply_cascade_permissions` / `aapply_cascade_permissions`, both anchored `#apply_cascade_permissions`, placed in the lowercase-function group before `finalize_django_types`); Index rows for `apply_cascade_permissions` (→ `shipped (0.0.10)`) and `Per-field permission hooks` (→ `planned for 0.1.1`); the `apply_cascade_permissions` entry body (status flip + full rewrite: walk mechanism, four invariants, `fields=` loud validation, sync/async pair, composition rule — scope corrected to forward-FK / OneToOne only, **no M2M**; consumer example uses the canonical `getattr(getattr(info.context, "request", None), "user", None)` form); the `Per-field permission hooks` entry body (Decision-2 note: host=FieldSet, signature `check_<field>_permission(self, info)`, failure modes, cascade-composition rule); the `get_queryset` visibility hook entry's one-sentence cascade cross-reference.
- `KANBAN.md` / `KANBAN.html` — regenerated by `scripts/build_kanban_md.py` / `build_kanban_html.py`. Card 34 moves WIP-ALPHA-034 → `DONE-034-0.0.10` (Done section, spec ref `docs/spec-034-permissions-0_0_10.md`, every DoD item `- [x]`, dependency cross-refs re-rendered).

**CSV (hand-edited, NOT DB-backed):**
- `docs/spec-034-permissions-0_0_10-terms.csv` — deleted the redundant `aapply_cascade_permissions,apply_cascade_permissions,...` row (folded its "no own heading by design" note into the surviving `apply_cascade_permissions` row's notes). `check_spec_glossary.py` → `OK: 42 terms` (was 43; the −1 is the de-double-counted shared anchor, correct).

**Hand-edited plain markdown (NOT generated):**
- `docs/README.md` — added the cascade-permissions bullet to "Shipped today" (after `inspect_django_type`); reshaped the "Coming next" `0.0.10` line to the `035` optimizer-robustness remainder; added the `[glossary-apply-cascade-permissions]` link-def.
- `docs/TREE.md` — package-top `permissions.py` line gets a real description in BOTH tree views (current on-disk layout, which lacked the entry, and the target layout, whose `planned by TODO-ALPHA-034-0.0.10` marker became the description); `tests/test_permissions.py` added to both test trees. The `filters/permissions.py` and `utils/permissions.py` substrate lines (different files) left untouched.
- `TODAY.md` — dropped the permissions bullet (with its stale `TODO-ALPHA-033-0.0.10` id) from "What products is still waiting for"; rewrote the commented-hook caveat in the visibility section to the live activated-cascade shape; added the `[glossary-apply-cascade-permissions]` link-def.
- `README.md` — status paragraph's "Newest shipped surface" lead now leads with the cascade-permissions subsystem (`0.0.10`); README has no explicit `0.0.10` "Coming next" roadmap line (only `0.0.11`), so no roadmap-line edit applied (verified).
- `CHANGELOG.md` — added a `## [Unreleased]` section above `## [0.0.9]` with two `### Added` bullets (the helper pair + the products cascade activation), bold-lead + glossary-cross-link style; added the `[permissions]` source link-def. No `## [0.0.10]` heading (Decision 13).

**GOAL.md doc-accuracy fix (authorized Slice-5 addition):**
- `GOAL.md` — the broken `getattr(info.context, "user", None)` (binds `None` against the live `StrawberryDjangoContext`) → canonical `getattr(getattr(info.context, "request", None), "user", None)` in the two cascade-showcase `get_queryset` bodies (Galaxy/CelestialBody) and the shared `_user(info)` helper (fixing the helper corrects all its call sites at once — DRY). 0 broken forms remain.

**NO version-file touched (Decision 13):** `pyproject.toml`, `django_strawberry_framework/__init__.py __version__`, `tests/base/test_init.py`, `uv.lock` — all untouched (confirmed via `git status`; the dirty `__init__.py`/`permissions.py`/`schema.py`/test files/`spec-034…md` are prior-slices' uncommitted work, left alone).

### Tests added or updated

None — doc/DB slice. Slice 5 ships no package source change and no test change (spec Implementation-plan "New tests: 0 (doc-only)").

### Validation run

- `uv run ruff format .` — pass (267 files unchanged, zero drift). The `COM812`-vs-formatter warning is pre-existing config, not from this slice.
- `uv run ruff check --fix .` — pass ("All checks passed!").
- `uv run python scripts/check_spec_glossary.py --spec docs/spec-034-permissions-0_0_10.md` — `OK: 42 terms` (post-CSV-dedup; was 43).
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` — `OK: 34 done cards have glossary links.` (exit 0 — both card 34 AND card 33 now pass; card 33 failed `--check` before the real run, reconciled by it).
- `uv run python examples/fakeshop/manage.py check` — `System check identified no issues (0 silenced).`
- Byte-clean regenerate: re-running all three generators a second time produces no further diff (`GLOSSARY` / `KANBAN.md` / `KANBAN.html` all byte-identical). `git diff docs/GLOSSARY.md` = exactly 6 intended hunks after regeneration.
- `git status --short` after both ruff invocations: only the Slice-5 files above are mine; no tool churn introduced (ruff reformatted nothing). Did NOT run the committed pytest suite (per dispatch); did NOT commit.

### Implementation notes

- **All DB edits ran via `manage.py shell` piping a temporary script from the gitignored `docs/builder/temp-tests/` dir (ORM only, never raw SQL), deleted after.** Three scripts: glossary edits, drift reconciliation, card move.
- **Public-exports bullet placement:** put both new symbols in the lowercase-function group (before `finalize_django_types`) rather than at the top, matching the list's existing uppercase-classes-then-lowercase-functions grouping; both anchor `#apply_cascade_permissions` (shared entry).
- **`get_queryset` cross-reference:** added the one sentence (spec explicitly names a cross-reference) rather than relying on the existing "See also" link; inserted it before the "Inheritance through an abstract base…" sentence, optimizer-cooperation paragraph left intact.
- **Bootstrap `CardGlossaryTerm` term choice:** `apply_cascade_permissions` (order=0), per plan discretion — `import_spec_terms` then synced the full 42-row set.
- **CSV-dedup representation:** folded the deleted row's "async twin … no own heading by design" note into the surviving row's notes column rather than dropping it outright, so the design intent stays documented in the CSV.
- **DoD ticks:** ticked all 11 `definition_of_done` CardItems (orders 0-10); left the `scope` / `foundation_seam` / `verified_upstream` / `dependencies_note` / `other` sections' items alone (the done-card convention ticks DoD only).

### Notes for Worker 3

- **Three generated docs are DB-backed** (`docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`). Spot-check by re-running `scripts/build_glossary_md.py` / `build_kanban_md.py` / `build_kanban_html.py` and confirming no diff (byte-clean — verified). Do NOT hand-edit them; the source of truth is `examples/fakeshop/db.sqlite3`.
- **`db.sqlite3` diff is larger than card-34 alone:** it includes card-33's `GlossarySpecMention` resync (0 → 38 rows) — that is `import_spec_terms` reconciling pre-existing concurrent-sweep drift across ALL done cards, expected and correct (worker-0.md step 5 processes every done card). It is NOT a worker reverting concurrent work.
- **Pre-existing GLOSSARY-body drift reconciled into the DB (see Notes for Worker 1 item A):** 8 shipped entries (`DjangoConnection`, `OrderSet`, `Meta.orderset_class`, `RelatedFilter`, `RelatedOrder`, `SyncMisuseError`, `Relay Node integration`, `Schema introspection management command`) + the public-exports `testing.relay` line were synced FROM the committed `docs/GLOSSARY.md` INTO the DB so the regenerate reproduces committed shipped content. Without this, regenerating would have reverted those shipped bodies. Verify the final `git diff docs/GLOSSARY.md` is exactly the 6 intended hunks (it is).
- **Two known broken-form `getattr(info.context, "user", None)` lines left intentionally out of scope:** the `get_queryset` visibility hook GLOSSARY entry's own generic example (DB-backed, line ~584 of rendered GLOSSARY) and the `ItemType` generic visibility demo in `TODAY.md` (lines ~264-265). Both are pre-existing generic `get_queryset` teaching examples (NOT cascade demos, NOT products-schema hooks) outside this slice's named scope — see Notes for Worker 1 item C.

### Notes for Worker 1 (spec reconciliation)

A. **Pre-existing DB-vs-committed-GLOSSARY divergence (root-caused, reconciled — the big one).** The committed `examples/fakeshop/db.sqlite3` (last refreshed by concurrent-sweep commit `d281d34e`) was BEHIND the committed `docs/GLOSSARY.md` (last regenerated at `e30d77ab`, an EARLIER commit) for 8 shipped glossary entries + the public-exports `testing.relay` line — verified independent of any Slice-5 edit by regenerating from HEAD's extracted `db.sqlite3` (HEAD-DB had the OLD `djangoconnection` body while HEAD-GLOSSARY had the new one). Regenerating GLOSSARY would have reverted that committed shipped doc content. Per worker-0.md step 1 (2nd bullet) I synced those 8 bodies + the relay line FROM the committed file INTO the DB (no committed-file content changed — the DB was brought UP to match), so the regenerate is byte-clean and the diff is exactly the 6 intended hunks. **Recommend Worker 1 confirm this reconciliation and consider whether the maintainer should be told the committed DB/GLOSSARY pair was out of sync before this build** (a concurrent-sweep artifact, not introduced here). This was NOT anticipated by the plan's "baseline is the committed WIP state" assumption.
B. **CSV-dedup → spec Risks reconciliation (plan item 2).** Resolved exactly as planned: deleted the redundant `aapply_cascade_permissions` CSV row; `import_spec_terms` no longer hard-rejects the duplicate anchor; `check_spec_glossary` reports `OK: 42 terms`. Update spec Risks line 498b to record that the dedup collision is resolved by ONE CSV row for the shared anchor (the second row was unrepresentable as a distinct DB row anyway).
C. **GOAL.md ratification + two left-as-is broken forms.** GOAL.md's `info.context.user` → `request.user` fix landed (3 sites: two showcase bodies + the `_user` helper). GOAL.md is not yet in the spec's Slice-5 doc list (spec line 479) — Worker 1 should ratify the addition at final verification (plan Notes-for-Worker-1 item 3, option a). Separately, two pre-existing broken `getattr(info.context, "user", None)` forms were left untouched as out-of-named-scope generic `get_queryset` teaching examples: the GLOSSARY `get_queryset` visibility hook entry's own example (DB-backed) and `TODAY.md`'s `ItemType` demo. Both predate this card and are not cascade demos. Worker 1 may decide whether to fold them in (the same canonical-form fix) — flagged per the dispatch.
D. **Stale spec status line (plan item 1).** Spec line 5 still reads "Slices 1-3 … shipped; Slices 4-5 remain" — correct to reflect Slice 4 final-accepted and Slice 5 landed at final verification (Worker 1 owns spec edits).
E. **TODAY.md / KANBAN card-body residual `docs/spec-permissions.md` refs (multi-surface, flag-only).** The card-34 DoD order=0 stale ref was fixed (`docs/spec-permissions.md` → `docs/spec-034-permissions-0_0_10.md`) per the plan. But other card-body prose still cites `docs/spec-permissions.md` — DoD item order=8's inner clause ("Decision recorded in `docs/spec-permissions.md`") and two `scope`/`other`-section bullets. Per worker-0.md's "do not partial-fix multi-surface stale refs" rule and the plan's "leave all other card-body prose alone" scope, I left these. Record as a maintainer/next-author follow-up in `bld-final.md`'s deferred catalog.
F. **TODAY.md / GLOSSARY `get_queryset` entry are themselves NOT generated by the kanban/glossary build, but `docs/TREE.md`'s `django_strawberry_framework` + Test-layout sections ARE generated** by `scripts/build_tree_md.py` (from module docstrings + kanban card predictions). I made targeted hand-edits to TREE.md per the dispatch (which framed it as hand-edited) rather than a full `build_tree_md.py` regenerate, because regenerating swept in unrelated pre-existing drift (docstring rewordings across connection/optimizer/utils files, a net-new `utils/input_values.py`, `tests/conftest.py`, `tests/optimizer/test_selections.py`, several `tests/utils/test_*.py`) from earlier specs that never got regenerated into TREE.md — out of this slice's scope. **Recommend Worker 1 flag the TREE.md staleness (run `scripts/build_tree_md.py --check` → reports not-up-to-date) to the maintainer as a separate doc-regeneration follow-up.** My TREE.md diff is exactly the 4 permissions-relevant edits.
G. **Card-33 drift fully reconciled (plan item 4).** Card 33 failed `import_spec_terms --check` before the real run (empty `GlossarySpecMention` rows); the real run reconciled it (now passes `--check`). No separate card-33 edit was made. STANDING GUARD honored throughout — no `git checkout`/`restore`/`stash`/`reset` of any tracked file (TREE.md was reconstructed from HEAD's blob via `git show HEAD:… > file` to undo an over-broad regenerate, which is a content-write, not a checkout, and TREE.md carried no prior accepted Slice work).

---

## Review (Worker 3)

Doc/DB slice. No package source logic, no test surface. Reviewed read-only against the spec (Doc-updates 472-485, Decision 2, Decision 13, DoD 12-13) and the Plan's `### Spec slice checklist (verbatim)` (lines 154-155). STANDING GUARD honored: every inspection was `git diff`/`grep`/`Read`; the only DB-touching commands were the three sanctioned regenerate scripts (read the DB, rewrite the rendered files) + two read-only `manage.py` checks + a read-only `build_tree_md.py --check`. No `git checkout`/`restore`/`stash`/`reset`, no tracked-file edit outside this artifact and worker-3 memory.

### High

None.

### Medium

None.

### Low

None.

### DRY findings

None. Slice 5 ships no code. The one DRY-relevant authoring choice — GOAL.md's `info.context.user` fix routed through the single `_user(info)` helper (line 327), which corrects all 7 call sites (lines 339-397) at once plus the two inline showcase bodies (galaxy/celestialbody) — is the correct readable-reuse shape (verified: `grep` shows 0 remaining broken `getattr(info.context, "user"` forms in GOAL.md). The two new GLOSSARY public-exports bullets both anchor `#apply_cascade_permissions` (shared entry, per spec line 477 "no own heading by design") rather than minting a duplicate `aapply` heading — correct anti-duplication.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` shows the Slice-1 export work (the `permissions` import + `aapply_cascade_permissions` / `apply_cascade_permissions` added to `__all__`, ERA001-staged-seam comment block removed). This is **prior-accepted Slice-1 content, not a Slice-5 edit** — Slice 5 adds NO new export. `__all__` already carries the two cascade symbols from Slice 1. Authorized by spec Decision 4 (package-root export) + Decision 13 ("the exports pin *does* grow in Slice 1 … exports are card-owned surface; the version constant is cut-owned"). Confirmed `__version__` is still `0.0.9`. **Result: public surface unchanged by this slice; the carried Slice-1 export delta is spec-authorized.**

### CHANGELOG sanity

Slice modifies `CHANGELOG.md`. Read the new entry end-to-end:
- **Heading placement (Decision 13):** new section is `## [Unreleased]` inserted ABOVE `## [0.0.9] - 2026-06-13`. NO `## [0.0.10]` release-heading promotion. Correct — Decision 13 / spec line 483.
- **Subsection heading:** `### Added` (matches what the spec authorizes — net-new public symbols + activation; no Changed/Fixed/Removed).
- **Version-line vs `pyproject.toml`/`__init__.py`:** N/A by design — `[Unreleased]` carries no version line, and `__version__`/`pyproject.toml` are frozen at `0.0.9` (the joint-cut owns the bump). Consistent.
- **Wording vs shipped behavior:** two bullets. Bullet 1 (`apply_cascade_permissions` / `aapply_cascade_permissions`) faithfully states the walk, four invariants (scope correctly reads forward-FK/OneToOne with M2M/reverse/GFK/GenericRelation/MTI-`<parent>_ptr` excluded), loud `fields=` validation, `SyncMisuseError`, the `sync_to_async` async twin, composition + `Prefetch` downgrade + zero round-trips, package-root export. Bullet 2 (products cascade activation) matches the Slice-4 four-hook `Entry → Item/Property → Category` activation exercised by `create_users(1)`. Nothing over/understated.
- **Link-def:** `[permissions]` → `django_strawberry_framework/permissions.py` (file EXISTS).

**Result: CHANGELOG sanity PASS.**

### Documentation / release sanity

- **GLOSSARY (DB-backed):** `apply_cascade_permissions` flipped to `shipped (0.0.10)` (Index row + entry status both re-render from one `status_text`); body rewritten with the walk mechanism, four invariants, `fields=` loud validation, sync/async pair, composition rule. **Scope corrected to "single-column forward FK / OneToOne edges" with M2M / reverse / `GenericForeignKey` / `GenericRelation` / MTI `<parent>_ptr` explicitly out of scope** — the spec-line-477 "FK / M2M"→forward-FK correction landed. Consumer example uses `getattr(getattr(info.context, "request", None), "user", None)` (canonical form). `Per-field permission hooks` re-statused to `planned for 0.1.1` with the Decision-2 note (host=`FieldSet`, signature `check_<field>_permission(self, info)`, denial/redaction, cascade-composition rule). `get_queryset` visibility-hook entry gained the one-sentence cascade cross-reference. Both new symbols in the public-exports list, both anchored `#apply_cascade_permissions`. **Byte-clean regenerate: `build_glossary_md.py` re-run → `docs/GLOSSARY.md` SHA unchanged (`7636a0fd…`); `git diff` is exactly the 6 intended hunks, no entry-header add/remove (no renumbering), no reconciled-shipped-entry body content in the diff.** PASS.
- **KANBAN (DB-backed):** `DONE-034-0.0.10` appears in the Done section (7 refs: card body + column table + dependency cross-refs); `WIP-ALPHA-034` count = 0 (removed from WIP cleanly). DoD all `- [x]` (11 items); DoD order=0 reads the corrected `Add docs/spec-034-permissions-0_0_10.md.`; spec ref → `docs/spec-034-permissions-0_0_10.md`; Glossary-terms table shows `apply_cascade_permissions` shipped (0.0.10) + `Per-field permission hooks` planned 0.1.1. **Byte-clean: `build_kanban_md.py` + `build_kanban_html.py` re-run → both SHAs unchanged (`78ca00ce…` / `be77b8f8…`).** `import_spec_terms --check` → `OK: 34 done cards have glossary links.` (exit 0). `manage.py check` → `no issues (0 silenced)` (exit 0). `check_spec_glossary --spec …034….md` → `OK: 42 terms` (exit 0, confirms the CSV-dedup −1 count). PASS.
  - *Informational (not a finding):* the Done card body still renders `Status: In progress` (line 1487). Verified this is a free-text DB field independent of the kanban-column FK that drives Done placement — DONE-033 renders `Status: Planned`, and 0 DONE cards render `Status: Done`. Pre-existing generator behavior across all DONE cards, not a Slice-5 defect; the `DONE-034-0.0.10` id + Done-section placement are the load-bearing closure facts and both are correct.
- **Hand-edited docs:** `docs/README.md` (shipped-today bullet added; Coming-next `0.0.10` reshaped to the `035` optimizer-robustness remainder; link-def added), `docs/TREE.md` (4 targeted permissions edits, no regenerate churn), `TODAY.md` (permissions bullet + stale `TODO-ALPHA-033-0.0.10` id dropped; commented-hook caveat rewritten to live activated shape; link-def added), `README.md` (status-para newest-shipped-surface now leads with the cascade-permissions subsystem `0.0.10`), `GOAL.md` (`info.context.user` → `request.user` complete: 0 broken forms remain). No residual "planned for 0.0.10" in any touched doc. All introduced/moved markdown links resolve (`[permissions]`, `[glossary-apply-cascade-permissions]` × 2 → existing file + existing GLOSSARY anchor). PASS.

**Result: Documentation / release sanity PASS.**

### Verbatim-copy check

Spot-confirmed faithfulness where the slice copies spec text: the GLOSSARY scope sentence matches Doc-updates 477 + Non-goals 114 (M2M out of scope); the Decision-2 note matches Decision 2 (lines 213-216) field-for-field (host / signature / failure modes / composition rule); the CHANGELOG bullets match Doc-updates 483 + the shipped Slice 1-4 behavior; the consumer example matches the User-facing API canonical form (spec lines 152-167). No drift.

### Adjudication of Worker 2's two findings

- **(a) Pre-existing DB-vs-GLOSSARY divergence reconciled by syncing 8 shipped entry bodies + the `testing.relay` public-exports line FROM the committed file INTO the DB — RIGHT CALL, CONFIRMED.** worker-0.md step 1 (2nd bullet) sanctions bringing a lagging DB up to the committed rendered file. Verified it did NOT alter unrelated shipped content: the byte-clean GLOSSARY regenerate produced zero net change, and the `git diff` contains no body changes to any of the 8 reconciled entries (`DjangoConnection`/`OrderSet`/`Meta.orderset_class`/`RelatedFilter`/`RelatedOrder`/`SyncMisuseError`/`Relay Node integration`/introspection-cmd) — the only diff line mentioning `OrderSet`/connections is the *new* `apply_cascade_permissions` Composition paragraph's cross-links, an intended hunk. Concur this was correct; concur with the recommendation that Worker 1 surface to the maintainer that the committed DB/GLOSSARY pair was out of sync pre-build (a concurrent-sweep artifact, not introduced here).
- **(b) `docs/TREE.md` is generated; Worker 2 targeted-hand-edited rather than full-regenerate — RIGHT CALL, CONFIRMED.** Independently ran `build_tree_md.py --check` (read-only, does not write) → "is not up to date" *with Worker 2's edits in place*, proving TREE.md carries pre-existing drift (earlier-spec docstring rewordings + net-new files) a full regenerate would sweep in, out of Slice-5 scope. The TREE.md diff is exactly the 4 permissions-relevant edits (5 content lines, one being an add+remove). The maintainer-regenerate recommendation is sound — concur it should be a separate doc-regeneration follow-up Worker 1 flags.

### Static helper

N/A — skip recorded. Slice 5 adds no `.py` source logic and touches no file under `optimizer/`/`types/`; the only `.py` diff (`__init__.py`) is prior-accepted Slice-1 export work, not Slice-5 content. `scripts/review_inspect.py` not run.

### What looks solid

The DB-backed-doc discipline is airtight: all three generated docs regenerate byte-identically from the committed DB (no drift), the card closed through the canonical ORM procedure (SpecDoc reused, DoD ticked, spec ref correct, `DONE-034-0.0.10` placed once), the CSV-dedup blocker resolved cleanly (`OK: 42 terms`), and the version freeze is intact (no `pyproject.toml`/`__version__`/`uv.lock`/`test_init.py` change). The GOAL.md `request.user` fix is complete and DRY (single-helper hinge). The two left-as-is broken `info.context.user` forms (GLOSSARY line 584, TODAY.md line 265) are correctly scoped out — verified both are generic `is_private=False` `get_queryset` teaching examples, NOT cascade/products-schema hooks, so leaving them (and escalating to Worker 1) avoids the partial-multi-surface-fix anti-pattern.

### Temp test verification

None created. Doc/DB slice — no behavioral suspicion to probe; verification was regenerate-byte-clean + the three management/checker commands + targeted greps. No temp tests under `docs/builder/temp-tests/` to clean up.

### Spec slice checklist (verbatim) walk

Both `- [ ]` sub-boxes (Plan lines 154-155) are reflected in the diff: `docs/GLOSSARY.md` ✓, `docs/README.md` ✓, `docs/TREE.md` ✓, `TODAY.md` ✓, `README.md` ✓, `CHANGELOG.md` ✓ (the explicit permission grant), `KANBAN.md` card→Done via the kanban DB + re-render ✓; "No version-file edits (Decision 13)" ✓ confirmed. Worker 1 ticks the boxes at final verification.

### Notes for Worker 1 (spec reconciliation)

Carrying forward Worker 2's items A-G unchanged — I independently confirmed each material claim:
- **Item A (DB-vs-GLOSSARY divergence):** confirmed reconciliation altered no unrelated shipped content (byte-clean + diff scope). Worker 1 should surface the pre-build DB/GLOSSARY out-of-sync (concurrent-sweep artifact) to the maintainer.
- **Item B (CSV-dedup → spec Risks 498b):** confirmed `OK: 42 terms`. Update spec Risks line 498b to record the dedup collision is resolved by ONE CSV row for the shared anchor (the second row was unrepresentable as a distinct DB row).
- **Item C (GOAL.md ratification + 2 left-as-is broken forms):** GOAL.md fix complete (0 broken forms). GOAL.md is not yet in spec Slice-5 doc-list line 479 — Worker 1 should ratify the addition. The two pre-existing generic-teaching broken forms (GLOSSARY line 584, TODAY.md line 265) are correctly out-of-named-scope; Worker 1 may decide whether to fold them in.
- **Item D (stale spec status line 5):** still reads "Slices 1-3 … shipped; Slices 4-5 remain" — correct to "Slices 1-4 shipped; Slice 5 landed" (or all five) at final verification.
- **Item E (card-body residual `docs/spec-permissions.md` refs):** confirmed DoD order=0 fixed; DoD order=8's inner clause + two scope/other bullets still cite the old name. Correctly left per the no-partial-multi-surface-fix rule — record in `bld-final.md` deferred catalog.
- **Item F (TREE.md generated/stale):** confirmed `build_tree_md.py --check` reports not-up-to-date; targeted hand-edit was right; recommend the maintainer-regenerate follow-up.
- **Item G (card-33 drift):** confirmed reconciled by the canonical `import_spec_terms` run (now passes `--check`); no separate card-33 edit.
- **Escalated (informational, not a blocker):** the KANBAN Done card-body `Status: In progress` free-text field is a pre-existing generator artifact (every DONE card renders a non-"Done" free-text status). If the maintainer wants DONE cards to render `Status: Done`, that is a generator/DB-convention change spanning all DONE cards — out of Slice-5 scope.

### Review outcome

**review-accepted.** 0 High / 0 Medium / 0 Low. All spec-required Slice-5 doc/DB behaviors are reflected in the diff; both checklist sub-boxes addressed; all three generated docs regenerate byte-clean from the DB; `import_spec_terms --check` + `manage.py check` + `check_spec_glossary` all pass (exit 0); version freeze intact (Decision 13); CHANGELOG under `[Unreleased]` with no `## [0.0.10]` promotion; both of Worker 2's findings adjudicated as correct calls; the carried spec-reconciliation items (A-G) belong to Worker 1's final verification, not slice blockers.

---

## Final verification (Worker 1)

Final-verification pass for Slice 5 (the LAST spec slice). Worker 3 set `review-accepted` (0/0/0). I re-ran every doc/DB integrity check independently, audited both verbatim-checklist boxes against the diff, and resolved all carried-forward spec-reconciliation items (I own spec edits; I made no source/test/doc/DB edit — only the spec + this artifact + my memory). STANDING GUARD honored: every command was a read-only check or a sanctioned regenerate (read DB → rewrite md); no `git checkout`/`restore`/`stash`/`reset`.

### 1. Spec slice checklist audit — PASS (both boxes truly landed)

Both `- [x]` boxes in the Plan's `### Spec slice checklist (verbatim)` (lines 154-155) are backed by real implementation in the working tree:

- `docs/GLOSSARY.md` — `apply_cascade_permissions` Index row → `shipped (\`0.0.10\`)` (line 57); entry status line 173 → `shipped (\`0.0.10\`)`; body rewritten with the walk, four invariants, `fields=` loud validation, sync/async pair, composition; scope correctly reads **single-column forward FK / OneToOne** with M2M / reverse / GFK / `GenericRelation` / MTI `<parent>_ptr` explicitly out of scope (no "M2M" claim); consumer example uses the canonical `getattr(getattr(info.context, "request", None), "user", None)` form (verified line 181). Two public-exports bullets (lines 36-37), both anchored `#apply_cascade_permissions`. `Per-field permission hooks` re-statused to `planned for \`0.1.1\`` with the Decision-2 note. `get_queryset` visibility-hook entry carries the one-sentence cascade cross-reference.
- `docs/README.md` ✓ (3 ins/1 del), `docs/TREE.md` ✓ (4 ins/1 del), `TODAY.md` ✓ (2/2), `README.md` ✓ (1/1), `CHANGELOG.md` ✓ (`## [Unreleased]` at line 19 ABOVE `## [0.0.9]` at line 25; no `## [0.0.10]`; the explicit per-card permission grant exercised). `docs/spec-034-permissions-0_0_10-terms.csv` ✓ (CSV-dedup, 1 ins/2 del).
- `KANBAN.md` card→Done ✓ — `DONE-034-0.0.10` present (7 refs), `WIP-ALPHA-034` count = 0 (clean move); `KANBAN.html` regenerated.
- **No version-file edits (Decision 13)** ✓ — `git diff --stat -- pyproject.toml uv.lock` empty; `tests/base/test_init.py` empty; `django_strawberry_framework/__init__.py` diff is exactly the prior-accepted **Slice-1** export work (ERA001 seam-comment removed + `permissions` import uncommented + two symbols added to `__all__`), and `__version__` is unchanged at `"0.0.9"` in both HEAD and the working tree. Slice 5 added NO export and no version change.

No box was ticked without matching implementation. No un-tick / `revision-needed` warranted.

### 2. DRY check — PASS

Doc/DB slice; no code. The one DRY-relevant authoring choice (GOAL.md's broken-form fix routed through the single `_user(info)` helper, correcting all call sites + the two inline showcase bodies at once; the two public-exports bullets sharing `#apply_cascade_permissions` rather than minting a duplicate `aapply` heading) is the correct readable-reuse shape — concur with Worker 3. The cross-file test-fixture consolidation (the cascading-schema scaffold re-declared across `test_permissions.py` / `test_connection.py` / `test_relay_node_field.py` / `test_list_field.py`) remains an **integration-pass** item, NOT Slice 5 — correctly out of scope here.

### 3. Doc/DB integrity checks — PASS (all re-run independently)

- `uv run python examples/fakeshop/manage.py check` → `System check identified no issues (0 silenced).` (exit 0).
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` → `OK: 34 done cards have glossary links.` (exit 0 — card 34 AND the previously-failing card 33 both pass; the canonical tool reconciled card-33's concurrent-sweep drift).
- `uv run python scripts/check_spec_glossary.py --spec docs/spec-034-permissions-0_0_10.md` → `OK: 42 terms` (exit 0; confirms the CSV-dedup −1 from 43). Re-confirmed `OK: 42 terms` AFTER my spec edits below.
- **Generated docs byte-clean:** captured SHA-256 of `docs/GLOSSARY.md` / `KANBAN.md` / `KANBAN.html`, re-ran `build_glossary_md.py` + `build_kanban_md.py` + `build_kanban_html.py`, re-captured — all three SHAs **identical** (DB is the stable source; no hand-edit drift).
- **No version-file change:** confirmed (see checklist audit item 1) — `pyproject.toml` / `uv.lock` / `test_init.py` clean; `__version__` still `0.0.9`.

### 4. Spec reconciliation — resolved (see `### Spec changes made (Worker 1 only)` below)

- **GOAL.md ratified** into the Doc-updates list (spec ~line 484) as an authorized Slice-5 doc-accuracy fix, with rationale recorded — done.
- **CSV-dedup** Risks-ledger note (b) updated to record that `import_spec_terms` HARD-REJECTS the duplicate anchor (not merely un-warned), the redundant `aapply_` row was removed, and `check_spec_glossary` reports `OK: 42 terms` — done.
- **Stale status line 5** updated to "build complete — all five slices shipped … pending integration + final gate" — done.
- **Two left-as-is `info.context.user` teaching examples — JUDGED GENERIC, left as-is (decision recorded):** GLOSSARY line 584 lives in the `get_queryset` visibility hook entry (status **shipped `0.0.1`**) — a generic single-type hook teaching example that predates this card entirely; it is NOT a cascade or contract example, and that entry's only spec-named Slice-5 edit (the cascade cross-reference) DID land in the adjacent paragraph. TODAY.md line 265 is the generic `ItemType` single-type visibility demo, distinct from the live cascade-activation paragraph directly below it (which correctly describes the shipped `apply_cascade_permissions` cascade as of `0.0.10`). Both are genuinely generic teaching examples, not contract examples — Worker 3's assessment confirmed. I did NOT change them: (i) they are out of the spec's named Slice-5 scope; (ii) GLOSSARY is DB-backed (a fix is a Worker-2 DB edit, not a Worker-1 spec edit); (iii) a generic-teaching-example cleanup is a consistent multi-surface sweep better done holistically — recorded as a maintainer/integration follow-up rather than partial-fixed. No `revision-needed`: leaving genuinely-generic examples is correct, not a defect.
- **FieldSet 044→046 cross-surface cluster — recorded for the maintainer, NOT partial-fixed:** the card-34 body's open-question prose still quotes the older FieldSet card `044` while the live card is `TODO-BETA-046-0.1.1`. Per worker-0.md's "do not partial-fix multi-surface stale refs" rule, I did NOT diverge one surface. This belongs in the deferred-work catalog the integration/final pass (`bld-final.md`) will own — that artifact does not exist yet, so it is recorded here + in my memory for the integration author to catalog (Worker 1 does not create speculative downstream files).
- **Companion deferred items also carried for the integration/final author:** (i) the **pre-build committed-DB-vs-committed-GLOSSARY divergence** (8 shipped entry bodies + the `testing.relay` public-exports line; a concurrent-sweep artifact reconciled INTO the DB by Worker 2, byte-clean — surface to the maintainer that the committed pair was out of sync before this build); (ii) **`docs/TREE.md` generator staleness** (`build_tree_md.py --check` reports not-up-to-date because of earlier-spec docstring/file drift a full regenerate would sweep in — Worker 2's targeted hand-edit was the right call; recommend a separate maintainer doc-regeneration follow-up); (iii) residual card-body `docs/spec-permissions.md` refs (DoD order=8 inner clause + two scope/other bullets) left per the no-partial-multi-surface-fix rule.

### Spec changes made (Worker 1 only)

Three edits to `docs/spec-034-permissions-0_0_10.md`; `check_spec_glossary` re-run after → `OK: 42 terms` (exit 0):

1. **Status line 5** — `in progress — Slices 1-3 … shipped; Slices 4-5 remain` → `build complete — all five slices shipped (… ; doc updates + card-completion wrap); pending the cross-slice integration pass and the joint-\`0.0.10\` final gate`.
2. **Doc-updates list (Slice 5 — package docs group, after the `CHANGELOG.md` bullet, ~line 484)** — added a `GOAL.md` bullet marked *(ratified at Slice-5 final verification — Worker 1)* authorizing the `getattr(info.context, "user", None)` → `getattr(getattr(info.context, "request", None), "user", None)` showcase correction (three sites: two showcase `get_queryset` bodies + the shared `_user(info)` helper), with the cross-surface-consistency rationale (GOAL.md was outside the originally-named list, but the identical broken form was already in-scope for the GLOSSARY rewrite; leaving the flagship showcase wrong while fixing GLOSSARY would be the cross-surface inconsistency the discipline forbids; pure doc-accuracy, no contract change). Used the existing `[goal]` link-def; wrote `StrawberryDjangoContext` as inline code (no `[glossary-strawberrydjangocontext]` link-def exists — avoided minting a dangling reference).
3. **Risks ledger item (b) (line ~498)** — rewrote the CSV-dedup note: was "the checker has no dedup/collision warning, so the CSV note's accuracy is eye-checked, not tool-enforced"; now records that `manage.py import_spec_terms` `_load_rows` HARD-REJECTS the duplicate anchor (`CommandError: Duplicate glossary anchor`) — sharper than the authoring-time framing (which only anticipated the *checker* tolerating it) — that the second row was unrepresentable as a distinct DB row anyway (both resolve to the same `GlossaryTerm`), that Slice 5 deleted the redundant `aapply_cascade_permissions` row (folding its "no own heading by design" note into the surviving row), and that `check_spec_glossary` reports `OK: 42 terms` after (the −1 is the de-double-counted shared anchor, correct).

### Summary

Slice 5 (doc updates + card-completion wrap — the LAST spec slice) is **final-accepted**. All doc/DB integrity checks pass (exit 0): `manage.py check` (no issues), `import_spec_terms --check` (34 done cards, both card 34 and the reconciled card 33), `check_spec_glossary` (`OK: 42 terms`, re-confirmed after my spec edits). All three DB-backed generated docs (`docs/GLOSSARY.md` / `KANBAN.md` / `KANBAN.html`) regenerate byte-identically (SHA-stable). Version freeze intact (Decision 13): `pyproject.toml` / `uv.lock` / `test_init.py` clean, `__version__` still `0.0.9`, the only `__init__.py` diff is prior-accepted Slice-1 export work. Both verbatim-checklist boxes are backed by real implementation — nothing over/under-ticked. I made three spec edits (status-line refresh, GOAL.md ratification, CSV-dedup Risks reconciliation) and resolved every carried-forward item; the FieldSet 044→046 cluster, two genuinely-generic teaching examples, the pre-build DB/GLOSSARY divergence, and the TREE.md generator staleness are recorded as maintainer/integration follow-ups (not partial-fixed). The build is complete pending the cross-slice integration pass + the joint-`0.0.10` final gate.
