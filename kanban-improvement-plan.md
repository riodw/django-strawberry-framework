# Kanban App Improvement Plan — AI Long-Horizon Automation Readiness

**Purpose.** The kanban DB (`examples/fakeshop/apps/kanban/` + `scripts/build_kanban_*`)
will be driven by an AI agent tracking its own long-running work: recording progress,
planning, and self-supervising across sessions. Today the board records *plans* (cards,
bullets, references) but not *work* (transitions, attempts, decisions, verification),
its write surface is convention-reliant, and its export pipeline is one-way. This plan
fixes the schema oddities the maintainer flagged, adds the missing work-tracking
dimension, and hardens the support code — decomposed into workstreams sized for
handoff to Opus 4.8 implementation agents under supervision.

Grounded in a three-agent review (data model, export scripts, support code) on
2026-07-18 against the live DB (63 cards, 1050 items, 96 references, 2595 UUID rows).

---

## Standing constraints (bind every workstream)

- READ AGENTS.md first. ASCII-only in `.py` files. `uv run ruff format .` +
  `uv run ruff check --fix .` after edits; run pre-commit checks before any commit.
- **Do NOT commit/branch/stash** unless the maintainer explicitly asks. Leave work dirty.
- **Concurrent writers**: parallel claude sessions write `db.sqlite3`. Never reset the DB;
  additive migrations only; no `git stash`; never revert files you didn't edit. Do not
  run destructive data migrations while a concurrent card-wrap is active — coordinate
  with the maintainer before applying any data migration.
- KANBAN.md / KANBAN.html / GLOSSARY.md / constants.py are **generated** — change the DB
  and/or scripts, then regenerate; never hand-edit (except the KANBAN.html Vue shell).
- New models linked into `UUIDModel` require: O2O field + `_UUID_LINK_NAMES` sync
  (models.py:678) + one-hot constraint Remove/Add migration + signal wiring + tracked-path
  constants regen. Lookup removals: the delete-data-vs-drop-column ordering depends on
  `on_delete` (migration 0003 = SET_NULL deletes rows first; 0004 = PROTECT drops the
  column first). Document and follow the right order per case.
- Coverage gate `fail_under=100` on the package; fakeshop app tests follow repo test
  idioms (live `/graphql/` tier where reachable, per `examples/fakeshop/test_query/README.md`).
- Do not run pytest after every edit; run at each workstream's verification gate.

---

## Phase 0 — Data repairs (fix what is already wrong, before schema changes)

Small, self-contained; do first so later constraints can be added cleanly.
**All data changes via Django data migrations or a management command reviewed by the
maintainer — check with the maintainer before applying to the live DB.**

- **0.1 Dedupe `CardReference` rows.** 13 duplicate `(source_card, target_card, kind)`
  groups exist (one 4x: card 14→12 "related"). Data migration: keep lowest `order`,
  delete the rest, renumber per-source contiguously.
- **0.2 Repair `Card.milestone` drift.** Card 47: `milestone=beta` but
  `target_version=0.1.0 → alpha`. Decide the truth with the maintainer (likely the
  target_version side), fix the row. (Phase 1 then removes the possibility.)
- **0.3 Resolve the stale `blocked_by` edge.** Card 32 → 30 is done→done; retype to
  `dependency` (matches established practice for shipped blockers).
- **0.4 Decide `CardItem.is_complete` semantics.** 290 of 390 `is_complete=True` rows are
  NOT `definition_of_done` items, contradicting the model comment (models.py:536).
  Recommendation: legitimize it as a general per-bullet checkbox — delete the comment,
  document it. (Alternative — constrain to DoD — requires flipping 290 rows; not
  recommended.) Maintainer decision required.
- **0.5 Audit section `other`.** 378/1050 items (36%) are in the `other` dumping-ground
  section. Propose new `Section` rows (`test_plan`, `decision`, `open_question`,
  `risk`, ...) and produce a reclassification report (card, item, proposed section) for
  maintainer sign-off before any data moves.

**Gate:** read-only verification queries showing zero duplicate reference groups, zero
milestone drift, zero done→done `blocked_by` edges.

---## Phase 1 — Schema corrections (the "weird relationships / off fields")

### WS-1A: Single source of truth for card-to-card edges
- Drop the `Card.dependencies` M2M (models.py:296) in favor of `CardReference` with
  `kind in {dependency, blocked_by}`; the ~150-line bidirectional signal sync
  (signals.py:448-599, 736-859) is deleted with it.
- Replace with: `Card.dependency_cards` property (queryset over `outgoing_references`),
  and a `dependencies`/`dependents` GraphQL surface backed by CardReference so existing
  queries keep working (schema.py + filters.py updates; `CardFilter.dependencies`
  RelatedFilter repointed).
- Add the missing DB constraints on CardReference:
  `UniqueConstraint(source_card, target_card, kind)` and
  `UniqueConstraint(source_card, order)` (after Phase 0.1 dedupe). Move the app-level
  order assignment (models.py:429-446) into the service layer (WS-3A) where it can be
  raced-checked; keep `save()` fallback.
- Migrate cycle-detection and lower-number-ordering validation from signals into the
  service write path; keep a thin signal *guard* (raise-only) for non-service writes.

### WS-1B: Derive, don't denormalize
- **`Card.milestone`**: remove the FK (models.py:272); derive via
  `target_version.milestone` everywhere (`card_id` property, exporters, filters —
  `CardFilter.milestone` becomes a related-path filter through target_version). Kills the
  drift class and the `prepare_card_save`/`sync_card_after_save` milestone patching
  (signals.py:602-, 714-723). UUIDModel unaffected (Milestone rows remain).
- **`TargetVersion.number`**: add structured `major/minor/patch` PositiveIntegerFields +
  a format CheckConstraint on `number`; `ordering` switches to the numeric triple
  (lexicographic ordering already mis-sorts at patch >= 10; versions are at 0.0.16).
  Backfill migration parses existing rows; `number` becomes derived-but-stored with a
  consistency constraint, or stays canonical with the triple maintained in `save()`.
  Retires `version_tuple()` string parsing in build_kanban_html.py:479-496.
- **`SpecDoc.url`**: store repo-relative `path` (or FK to TrackedPath); derive the GitHub
  URL at render time. Removes the hardcoded-prefix reverse-parse in
  build_kanban_md.py:17,76-89. Backfill migration strips the known prefix.

### WS-1C: Field-level cleanups
- `Card.priority`: make non-null + PROTECT (0/63 null today); fix the Priority docstring
  (6 levels live, not 3).
- `RelativeSize`: collapse duplicate ordering axes `order` vs `rank` (keep `order`;
  migrate `rank` weighting used by build_kanban_html.py:526-531 to read `order`).
- `TrackedPath.is_current` → explicit `state` (FK lookup or choices:
  `current | historical | planned`), disambiguating the conflated docstring semantics
  (models.py:217-220). Constants-sync service maps accordingly.
- **Per-link kind for card↔file links**: replace the bare `Card.changed_files` M2M with a
  through model `CardPathLink(card, path, kind in {predicted, changed})`. Deletes the
  DONE-status reinterpretation in build_kanban_md.py:360-380, services.py, and lets the
  two near-identical import commands merge (WS-3C). Data migration: existing links on
  done cards → `changed`, others → `predicted`.
- `Label`: add `label`/`description` for parity with other lookups (optional, low).
- `BoardDoc.namespace`: leave as-is (works), but document that it is the one deliberate
  choices-shaped slug.
- `Card.number` uniqueness: keep for now but move the renumber machinery to services
  (WS-3A); document that `number` is display ordering and `title`/`slug`/UUID are the
  identities. (Full dropping of `unique=True` is a maintainer decision — defer.)

**Migration hazards:** each M2M/FK removal touching UUID-linked models follows the
one-hot Remove/AddConstraint dance; `CardPathLink` and any new model must be added to
`_UUID_LINK_NAMES` + signals + constants regen. All migrations additive-first, data
steps separate and maintainer-gated.

**Gate:** makemigrations clean; migration plan reviewed by maintainer BEFORE applying;
full kanban app test suite + live test_kanban_api.py green; regenerate KANBAN.md/html and
diff — content-identical output expected (except intended fixes).

---

## Phase 2 — The work-tracking dimension (the core AI-automation gap)

New models (each: TimeStampedModel base, UUIDModel wiring, admin, filters/orders,
GraphQL type, factory, tests):

- **2A `CardTransition`** — `card FK, from_status FK null, to_status FK, actor, note,
  occurred_at`. Written automatically by the status-change service (WS-3A). This is the
  single highest-value addition: durable history of when work moved.
- **2B `WorkAttempt`** — `card FK, started_at, ended_at null, outcome FK lookup
  (succeeded | failed | abandoned | blocked), summary, evidence`. Lets an agent record
  tries/failures/retries across sessions.
- **2C `Decision`** — `card FK null, question, choice, rationale, decided_at,
  supersedes FK self null`. Today decisions rot in `planning_note` and `other` bullets.
- **2D `Actor` provenance** — `Actor` lookup (human maintainer, agent session ids) +
  `actor FK` on CardTransition/WorkAttempt/Decision. Essential given confirmed parallel
  agent sessions writing the same DB.
- **2E Verification on CardItem** — `verified_at null, verified_by text,
  verification_kind FK null (test_run | coverage_gate | manual | live_query)`. Upgrades
  the bare `is_complete` bool into auditable DoD state.
- **2F Status state machine** — allowed-transition validation in the service layer
  (`backlog→todo→wip→done`, explicit reopen path that re-checks done-guards), enforced
  in `services.set_card_status`; signal guard raises on non-service status writes.
- **2G Dependency semantics formalization** — documented: `blocked_by` gates
  `is_blocked`; `dependency` is informational. Auto-downgrade `blocked_by`→`dependency`
  when the target flips done (service hook), with a CardTransition-style note. Add
  `resolved_at` to CardReference.
- **2H "What next" query** — `readyCards` root field / `isReady` derived field:
  status=todo, not blocked, dependencies done, ordered by priority.order then number.
  Fix the `is_blocked` N+1 with a resolver-level `Exists` annotation while here.

**Gate:** package + fakeshop suites green; live-tier tests for every new GraphQL surface;
KANBAN regen unaffected (new tables don't render yet — rendering them is a later,
separate slice).

---

## Phase 3 — Support-code hardening

### WS-3A: Services as the sanctioned write API (signals demoted to guards)
- New/completed services: `set_card_status` (writes CardTransition, enforces 2F),
  `move_card_number` (absorbs the renumbering engine, signals.py:178-445; per-row
  `.update()` instead of full `save()` to stop `updated_date` churn on neighbors),
  `add_dependency`/`remove_dependency` (absorbs cycle + ordering validation),
  `set_item_complete`/`verify_item`, `record_attempt`, `record_decision`,
  `append_card_item` / `append_card_reference` / `create_card_from_spec` (already built
  and orphaned — finally get callers).
- Signals shrink to: UUID side-row creation, done-card invariant guards (raise-only),
  and raise-on-bypass guards for status/number writes outside services.
- Normalize errors: everything surfaces `KanbanServiceError` with a stable `code`
  attribute; commands catch `ValidationError` too (fixes the raw-traceback leak in
  import_card_changed_files.py:102-103).
- Kill duplication: `_card_identifier` (signals.py:128) → `card.card_id`; shared
  `_manager`/`DONE_STATUS_KEY` into one module; defensive `.get()` at signals.py:829.

### WS-3B: GraphQL mutation surface
Wire the WS-3A services as framework mutations (dogfooding
`django_strawberry_framework/mutations/`): `createCardFromSpec`, `setCardStatus`,
`moveCardNumber`, `setCardItemComplete`, `verifyCardItem`, `addDependency`,
`removeDependency`, `recordWorkAttempt`, `recordDecision`, `setCardFiles(kind)`.
Also: add missing `labels` + `dependents` RelatedFilters to CardFilter (filters.py:175);
accept UUID/slug in `resolve_card` (services.py:214) and make ambiguous-title an error
(`.get()` + explicit MultipleObjectsReturned message).

### WS-3C: Importer/command consolidation
- Merge `import_card_changed_files` / `import_card_predicted_files` (95% identical) into
  one command with `--kind {changed,predicted}` over `CardPathLink`.
- Importers accept `uuid`/`slug` identifiers (the stable ids the exports publish).
- `import_kanban_package_file_links.py`: error (don't skip) on malformed `## DONE-...`
  headings; longer-term, retire the markdown attribution ledger for the JSON shape the
  command already accepts.
- Print a summary when `sync_tracked_paths_from_constants` flips `is_current`/`state`
  rows inside an import transaction (large silent side effect today).

### WS-3D: Test-gap closure (signals/services are the riskiest code)
Add tests for: m2m clear/remove/reverse dependency-sync paths (pre-WS-1A) or their
service equivalents (post), reference retarget/kind-change, delete-compaction
renumbering, done-card spec REASSIGN guard, `_restore_dependency_if_references_remain`,
`OneHotLinkCount.deconstruct()` + zero-field ValueError, `resolve_card` by-int/by-uuid,
`create_card_from_spec` rejection branches, `sync_tracked_paths_from_constants`
flip-back, and live assertions for `isBlocked`/`cardId`/`slug`/`readyCards`.

**Gate:** full suite green; every new mutation exercised in the live `/graphql/` tier.

---

## Phase 4 — Export pipeline for machines

- **4A `KANBAN.json`** — first-class canonical JSON export (`build_kanban_html.py`
  already holds the full payload dict at ~712); md + html renderers consume it; embed an
  as-of snapshot timestamp. This is the agent's diffable board snapshot.
- **4B Uniform CLI contract** — `--check` and `--json` result output + int exit codes on
  ALL `build_*` scripts (html and glossary lack `--check` today, so hooks can't gate
  their freshness); extract `scripts/_kanban_lib.py` (shared `configure_django`,
  `run_git`, dry-run helper, GraphQL fetch) replacing the import-from-build_kanban_html
  coupling.
- **4C Move script-frozen facts into the DB** — `COLUMN_DOC_KEYS` / column routing
  (build_kanban_md.py:21-26, 156-181) → a `BoardColumn` model or BoardDoc metadata;
  `_RELEASE_VERSION` + rank-weighting (build_kanban_html.py:471, 526-531) → Milestone
  fields; `PLANNED_PATH_DESCRIPTIONS`/`TARGET_PATH_REPLACEMENTS`
  (build_tree_md.py:471-487) → TrackedPath/card rows; the synthetic fractional-order
  "Progress to 1.0.0" doc (order + 0.5, silent None if no snapshot doc) → a real
  computed BoardDoc kind, loud on missing anchor.
- **4D SQLite concurrency** — `PRAGMA busy_timeout` (or retry-on-locked wrapper) in the
  script-side connection setup; documented, given the parallel-writer workflow.
- **4E Renderer hygiene** — deterministic ordering for the HTML data block (re-sort the
  payload, not resolver order); loud error naming the doc/card on unresolved
  `{{card_ref:N}}` instead of only the leftover sweep; drop dead `specMentions`/
  `outgoingLinks` payload in build_glossary_md.py or render it.

**Gate:** regen all artifacts; `--check` passes for every renderer; KANBAN.json
round-trips (a card addressed by its exported uuid can be mutated via WS-3B).

---

## Sequencing, sizing, and supervision

| Order | Workstream | Size | Parallelizable? |
|---|---|---|---|
| 1 | Phase 0 data repairs | S | after maintainer sign-off |
| 2 | WS-1B, WS-1C | M | 1B ∥ 1C |
| 3 | WS-1A (edges) | M | after 0.1 |
| 4 | Phase 2 models (2A-2E) | L | one agent per model, shared plan for UUIDModel wiring (serialize the migration numbering!) |
| 5 | WS-3A services + 2F/2G/2H | L | after Phase 2 |
| 6 | WS-3B mutations + WS-3C importers | M | 3B ∥ 3C |
| 7 | WS-3D tests | M | ∥ with 6 |
| 8 | Phase 4 exports | M | 4A first, rest ∥ |

Supervision protocol per workstream: (1) supervisor briefs an Opus 4.8 agent with the
workstream section + standing constraints; (2) agent implements, leaves tree dirty;
(3) supervisor runs an independent adversarial-review agent over the diff; (4) supervisor
verifies the gate (targeted tests, regen diffs); (5) maintainer decides commit points.
Migrations are the serialization hazard — only one workstream may hold "next migration
number" at a time; supervisor allocates.

Open maintainer decisions needed before Phase 0/1 start:
1. `is_complete` semantics (0.4): legitimize (recommended) or constrain?
2. `Card.milestone` removal (1B) vs keep-with-DB-consistency-constraint?
3. Drop `Card.number` uniqueness eventually, or keep the renumber engine?
4. Retire the markdown attribution ledger (3C)?
5. Timing of data migrations relative to concurrent sessions.

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
