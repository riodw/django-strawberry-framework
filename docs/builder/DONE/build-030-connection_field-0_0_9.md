# Package build plan: connection_field / 0.0.9 (030)

Spec source: `docs/SPECS/spec-030-connection_field-0_0_9.md` (already archived; companions in `docs/SPECS/appx/`)
Target release: `0.0.9` (SHIPPED — this is a **residual reconciliation cycle**, not a fresh build)
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every slice must justify shared/duplicated patterns before merging.

## Cycle purpose (maintainer-set, this cycle only)

The card `DONE-030-0.0.9` shipped in `0.0.9`. Two things were never finished:

1. **The `-rationale.md` companion was never created.** Every archived spec from `001` through `029` has one in `docs/SPECS/appx/`; `spec-030` has only its `-terms.csv`. The deliberative layer is still inline in the spec.
2. **The spec was never reconciled against what actually landed** — neither against the build itself nor against the later cards (`031`/`032`/`033`/`035`/`045`/`047` and the `0.0.14` keyset work) that changed, extended, or superseded surfaces `030` contracted.

So this cycle answers exactly two questions per slice:

- **Did the code skip, drop, or silently narrow anything the spec slice contracted?** A gap is a code finding and gets fixed.
- **Did later work change what `030` landed?** If yes, the spec is rewritten to state the CURRENT contract directly — no chronology, no amendment blocks, no "as of `033`" hedges. **The explanation of what changed and why lives in the rationale file, never in the spec.**

**Scope fence (maintainer-set):** this cycle edits **spec files (`docs/SPECS/spec-030-*.md`, `docs/SPECS/appx/spec-030-*-rationale.md`) and package/test `.py` files ONLY.** No closeout agentflow edits: no `docs/GLOSSARY.md`, no `KANBAN.md` / `KANBAN.html`, no `docs/TREE.md`, no `CHANGELOG.md`, no `TODAY.md`, no `README.md`, no `db.sqlite3`, no card wrap, no `BUILD.md` / `worker-*.md` retrospective edits. Spec Slice 5 is therefore **audit-only**: its doc claims are verified and any divergence is RECORDED for the maintainer, never edited.

**Filename rule (maintainer-set):** every file this cycle creates carries `030` in its name.

## Pre-flight

Pre-flight: passed on 2026-08-25.

1. **Working-tree baseline** — dirty at start with a concurrent session's work; maintainer instruction is "ignore others concurrent work". Recorded below.
2. **`scripts/review_inspect.py`** — smoke ran green on `django_strawberry_framework/connection.py` (exit 0).
3. **Artifact reset** — no `build-030-*` / `bld-*-030*` path existed. `docs/builder/bld-003-final.md` is a **tracked** leftover of the `003` cycle; deleting it is a repo edit outside this cycle's scope fence, so it is left in place and named here so no pass mistakes it for this cycle's output. `docs/builder/DONE/` holds prior cycles' completed plans and is untouched.
4. **`.gitignore`** — lists `docs/builder/worker-memory/`, `docs/shadow/`, `docs/builder/temp-tests/`.
5. **Scratch cleared** — all three emptied; `worker-memory/worker-0..3.md` re-seeded empty.
6. **Spec-doc consistency** — `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-030-connection_field-0_0_9.md` → `OK: 50 terms`.
7. **Spec rationale extraction** — NOT yet done; it is the first dispatched pass of this cycle (checklist item 0 below). No slice is dispatched until it is `final-accepted`.

### Working-tree baseline — out-of-scope files (never edit, never revert)

A concurrent session owns all of these (`AGENTS.md` rule 34). Several are package `.py` files, so the fence matters. **This list GREW during the rationale pass** — re-read `git status --short` at the start of every pass rather than trusting this snapshot, and treat any `.py` file dirty-but-untouched-by-this-cycle as out of scope:

- `django_strawberry_framework/exceptions.py` (M) — **package .py, out of scope**
- `django_strawberry_framework/scalars.py` (M) — **package .py, out of scope**
- `django_strawberry_framework/__init__.py` (M) — **package .py, out of scope** (appeared during the rationale pass; it is also a spec Slice 4 surface, so Slice 4 AUDITS it read-only and never edits it)
- `pyproject.toml`, `uv.lock` (M) — a concurrent dynamic-version migration. It transiently broke `uv run` tree-wide mid-pass and then resolved; if `uv run` fails with `Missing 'tool.hatch.version' configuration`, that is this migration mid-write, not this cycle's doing. Fall back to `.venv/bin/python -m ...` and record it.
- `AGENTS.md` (M) — dirty; still authoritative, read it as it stands
- `scripts/bug_hunt.py`, `tests/test_bug_hunt.py`, `tests/base/test_init.py` (M)
- `tests/filters/test_base.py`, `tests/filters/test_factories.py`, `tests/filters/test_inputs.py` (M)
- `tests/test_exceptions.py`, `tests/test_resource_policy.py`, `tests/test_scalars.py`, `tests/test_schema.py`, `tests/test_sets_mixins.py` (M)
- `docs/review/**` (~37 untracked), `docs/dry/**` (untracked), `docs/bug_hunt/**` — churn under the concurrent session
- `tests/mutations/test_operations.py` (untracked)

None is a tracked binary/generated file this cycle writes. `examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md` are concurrent-writable AND fenced out of this cycle: if any shows up dirty, it is not this cycle's output and is never reverted.

## Declarations

- **Ownership partition:** `none; sequential slices`. Every slice's spec reconciliation writes `docs/SPECS/spec-030-connection_field-0_0_9.md`, which Worker 1 alone may touch, so no two slices are file-disjoint. Sequential dispatch throughout.
- **Hot-path declaration:** no code change is expected. **Conditional:** any slice that lands a change inside `django_strawberry_framework/connection.py::_pipeline_sync`, `::_resolve_from_window`, `::_finalize_queryset`, or `django_strawberry_framework/optimizer/extension.py::apply_connection_optimization` owes a before/after number per `BUILD.md` `## Hot-path budget`. A slice that lands no code change declares `none` in its artifact and says so explicitly.
- **Floor-verification scope:** `django_strawberry_framework/connection.py` sits directly on the Strawberry `relay.connection()` / `ConnectionExtension` seam. **Conditional:** any slice that lands a `.py` change under `connection.py`, `types/base.py`, `types/definition.py`, or `optimizer/extension.py` re-runs `tests/test_connection.py` (plus `tests/types/test_base.py` where `types/` changed) at the floor, owned by that slice's Worker 2 pass, recorded in `bld-final-030.md`. Floor numbers come from `BUILD.md` `## Floor verification` and nowhere else. A spec-only slice declares `none`.

## Dispatch model for this cycle (maintainer-set)

Per-slice, Worker 1 opens with an **audit pass**: it reads the spec slice's sub-checks, verifies each against HEAD source with symbol-qualified citations, and classifies every divergence as either

- **CODE GAP** — the shipped code does not deliver a contracted sub-check → full worker cycle (W1 plan → W2 build → W3 review → W1 final), or
- **SPEC DRIFT** — the code is correct and the spec text is stale (a renamed/relocated symbol, a claim a later card superseded, a bound later work changed) → Worker 1 alone reconciles the spec and closes the slice, `BUILD.md` `### Procedural-closure slices` shape, with the reasoning written to the rationale file.

Workers 2 and 3 are dispatched **only** when a CODE GAP is confirmed. `### Isolation is non-waivable` still holds: if code changes, Worker 3 reviews as a separate spawn.

## Artifact list

- `docs/builder/bld-rationale-030.md` (pre-flight step 7 — the rationale MOVE)
- `docs/builder/bld-slice-1-030-connection_base.md`
- `docs/builder/bld-slice-2-030-connection_field.md`
- `docs/builder/bld-slice-3-030-optimizer_cooperation.md`
- `docs/builder/bld-slice-4-030-live_http_export.md`
- `docs/builder/bld-slice-5-030-doc_wrap_audit.md`
- `docs/builder/bld-integration-030.md`
- `docs/builder/bld-final-030.md`

## Checklist

- [x] 0. Pre-flight step 7: spec rationale extraction into `docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md` -> `docs/builder/bld-rationale-030.md`
- [x] Slice 1: `DjangoConnection[T]` base + per-target concrete connection classes + `Meta.connection` validated and stored on the definition + the `first` + `last` guard -> `docs/builder/bld-slice-1-030-connection_base.md`
- [x] Slice 2: `DjangoConnectionField` factory + synthesized-signature argument injection + composition pipeline + consumer-resolver contract + optimizer cooperation point + sync/async -> `docs/builder/bld-slice-2-030-connection_field.md`
- [x] Slice 3: verify optimizer cooperation; bound the connection-aware-planning gap -> `docs/builder/bld-slice-3-030-optimizer_cooperation.md`
- [x] Slice 4: live HTTP coverage on a Relay-Node-shaped fakeshop type + public-export promotion -> `docs/builder/bld-slice-4-030-live_http_export.md`
- [x] Slice 5: doc updates + card-completion wrap (**audit-only** under the scope fence) -> `docs/builder/bld-slice-5-030-doc_wrap_audit.md`
- [x] Cross-slice integration pass -> `docs/builder/bld-integration-030.md`
- [x] Final test-run gate -> `docs/builder/bld-final-030.md`

## Worker-0 pre-verified findings (handed into dispatch)

Verified at HEAD by Worker 0 before any dispatch, per `BUILD.md` `### Worker 0 verifies every finding against source before dispatching`. These are **starting points, not a complete list** — each slice's Worker 1 audit owns the full sweep of its own sub-checks.

Present and shipped (no gap):

- `django_strawberry_framework/connection.py` exists (2077 lines) and carries `DjangoConnection`, `_connection_type_for`, `_generate_connection_class`, `_build_total_count_connection`, `_guard_first_and_last`, `_total_count_requested`, `_attach_count_sync`, `_guard_total_count_countable`, `_guard_sidecar_input_against_non_queryset`, `_synthesized_signature`, `_pipeline_sync`, `_pipeline_async`, `_finalize_queryset`, `DjangoConnectionField`.
- `django_strawberry_framework/types/base.py::_validate_connection` exists; `ALLOWED_META_KEYS` and `_is_relay_shaped` exist; `_validate_connection` is called from `_validate_meta`.
- `django_strawberry_framework/types/definition.py::DjangoTypeDefinition` carries the `connection: dict | None` slot.
- `django_strawberry_framework/optimizer/extension.py::apply_connection_optimization` exists and is imported by `connection.py`.
- `django_strawberry_framework/__init__.py` exports `DjangoConnection` and `DjangoConnectionField` in `__all__`.
- `examples/fakeshop/apps/library/schema.py` declares `all_library_genres_connection: DjangoConnection[GenreType] = DjangoConnectionField(GenreType)` with `GenreType.Meta.connection = {"total_count": True}`, imported from the public surface.
- `tests/test_connection.py` exists (1964 lines).

Spec-drift candidates already visible (each still owed a full audit by the owning slice):

- The spec cites `_initial_queryset(target_type)` and `_apply_get_queryset_sync` / `_apply_get_queryset_async` in `types/relay.py`. At HEAD those are `initial_queryset(...)` and `apply_type_visibility_sync` / `apply_type_visibility_async` in `django_strawberry_framework/utils/querysets.py` (the spec-045 sealed-execution-queryset boundary). Every spec citation naming the old symbols is stale.
- The spec pins `_ends_in_unique_column` as a `connection.py` symbol. At HEAD the canonical implementation is `django_strawberry_framework/optimizer/plans.py::ends_in_unique_column`, re-exported into `connection.py` under the old private name.
- **Decision 11 / Slice 3 / DoD item 6 assert the derived plan is EMPTY for every connection field in `0.0.9`.** `DONE-033-0.0.9` shipped the connection-aware walker, so that claim is a bound later work deliberately removed. This is the cycle's largest reconciliation item: the spec must state the current contract, and the rationale must record that the emptiness was a `0.0.9`-cohort-internal bound `033` closed.
### Handed forward by the rationale pass (`bld-rationale-030.md`), verified by Worker 0

Line numbers are the **post-move** spec (119,551 B / 698 lines). Each is SPEC DRIFT unless the owning slice's audit proves otherwise.

- **`Connection-aware optimizer planning` is `shipped (0.0.9)` in `docs/GLOSSARY.md` at HEAD**, but the spec asserts it stays `planned` in five places (`:9`, `:81`, `:111`, `:508`, DoD item 8). Owner: Slice 3 (the claim) and Slice 5 (the doc-state claim, audit-only).
- **The "derived plan is empty for every connection field" bound is live at four sites** (Decision 11 `Scope honesty`, the Slice-3 checklist, the Test plan, DoD item 6) and was closed by `DONE-033-0.0.9`. Owner: Slice 3.
- **Stale symbol citations**, by post-move line: `_initial_queryset` (`:69`, `:104`, `:354`, `:447`), `_apply_get_queryset_sync` / `_async` (`:69`, `:103`, `:104`, `:362`, `:387`, `:389`, `:557`), `_ends_in_unique_column` (`:71`, `:358`). Owner: whichever slice owns the citing text — Slice 2 for the pipeline sites, Slice 1 for the base/`Current state` sites.
- **Decision 9's `Meta.cursor_field` deferral later shipped** (`:131`, `:171`, `:379`-`:381`, `:446`, `:536`). Owner: Slice 1 (Decision 9 sits in the base-shape group) with a Slice 2 cross-check on the pipeline mention.
- **At least one review round of this spec was never recorded.** The history listed three revisions and one finding round, yet four finding labels (`P1-B`, `P3a`, `P3b`, and an "Open Question: direct relay.Node") are cited from live code. Three of those labels were already dangling at HEAD and are now homed in the rationale under Decisions 11 / 4 / 5. The unrecorded round itself is a maintainer-facing gap: record it, do not invent its contents.

- `connection.py` now also carries the keyset-cursor path (`_resolve_keyset_connection`, `_KeysetPage`, `Meta.cursor_field`), the windowed nested-connection fetch path (`_resolve_from_window`, `_consume_window`), and the synthesized relation-connection resolver (`_build_relation_connection_resolver`). None of these is `030` work — they are `032` / `033` / `0.0.14` surfaces sharing the module. Spec Decision 9 explicitly deferred `Meta.cursor_field`, so it now states a deferral that later shipped: the spec must say so without narrating the chronology.

## Mid-cycle scope amendment (Worker 0, before the integration pass)

Slice 5's audit surfaced **MF-5**: `docs/SPECS/appx/spec-030-connection_field-0_0_9-terms.csv`'s `notes` column still asserts that the glossary flips are *pending*, that `Connection-aware optimizer planning` "stays planned for `0.0.9`", that the optimizer "rides the existing root-gated flat-selection walker", and it names `WIP-032` / `WIP-033` at five sites. Every one of those now contradicts the reconciled spec sitting beside it.

Worker 0's call: the terms CSV is a **spec companion**, not a closeout agentflow artifact, so it is inside the maintainer's "spec files and code `.py` files only" fence — and a companion asserting the opposite of its own spec is precisely the drift this cycle exists to close. **The integration pass is authorized to reconcile the CSV's `notes` column**, bounded as follows:

- The `notes` column ONLY. Never a `term` or `anchor` value, never a row added or removed, never the row count or the one-row-per-anchor shape.
- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-030-connection_field-0_0_9.md` must still report `OK: 50 terms` afterward.
- `import_spec_terms --check` is RUN and its output recorded. It is not required green — a pre-existing baseline failure on an earlier done card is a known condition. **`import_spec_terms` without `--check` writes `examples/fakeshop/db.sqlite3` and is forbidden this cycle.**
- The consequence is stated for the maintainer: the CSV's `notes` cells reach the glossary DB only when the maintainer next runs the importer, so this edit changes a file, not the database.

Recorded here rather than left in the dispatch transcript, per `worker-0.md` `### Mid-flight instructions are mirrored into the artifact`.

## Rules copied for every worker

- **One slice at a time.** Do not start the next slice until the current one's cycle is complete.
- **DRY first.** Every pass answers "is this the maximally DRY shape that stays readable?" before anything else.
- **No `pytest --cov*`.** `--no-cov` is the only coverage-shaped flag permitted (`AGENTS.md`; `BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool`).
- **Never commit.** Only the maintainer commits.
- **Never branch or switch branches.**
- **Source refs are symbol-qualified** (`path::QualifiedName`, `path::QualifiedName #"substring"`, `path #"substring"`) everywhere except these per-cycle `docs/builder/bld-*` scratchpads, where raw `path:NN` is allowed.

## Final gate record (folded in from `bld-final-030.md` before its deletion)

The seven per-slice / rationale / integration artifacts were deleted at close on the maintainer's
instruction, and `bld-final-030.md` after them; **this plan is the only surviving artifact of the
cycle.** Each reached `Status: final-accepted` first. Every `Slice N` / `integration pass` /
`final gate` attribution elsewhere in this file names a source that no longer exists on disk — the
claims they supported are restated here rather than left as pointers. All eight are recoverable
from commit `6b3e1c82`, which added them; `aa23d44d` removed them.

Gate commands, in `BUILD.md` order, all PASS at the final gate: `pytest --no-cov`
(**6570 passed, 42 skipped**; a confirming `-rs` re-run 20 minutes later gave `6571 passed,
42 skipped` — one row a concurrent session added mid-pass, which is `BUILD.md`'s "a bare count
rots" hazard observed live); `manage.py check` (`no issues (0 silenced)`);
`makemigrations --check --dry-run` (no changes); `ruff format --check .` (`429 files already
formatted`); `ruff check .` (`All checks passed!`); `git diff --check` (silent);
`check_spec_glossary.py` (`OK: 50 terms`, unchanged across the whole cycle);
`check_trailing_commas.py --check` over the three `docs/SPECS/` files this cycle wrote — which is
also the untracked-file gate `git diff --check` structurally cannot be; and
`import_spec_terms --check` (`OK: 49 done cards have glossary links`, the importer never run
without `--check`). No `--cov*` flag was used and no coverage figure was read.

**The skip census corrected Worker 1's own first assumption and is recorded that way**: the
`FAKESHOP_SHARDED` gate was expected, and two sampled rows fit it, but the real breakdown is 37
Postgres-tier, 2 missing-`psycopg2`, 2 sharded, 1 multi-DB alias — two conforming samples read
exactly like a measured population.

**Floor verification resolves to `none`, proved inversely rather than asserted**: scope was
conditional on a slice landing a `.py` change under `connection.py` / `types/base.py` /
`types/definition.py` / `optimizer/extension.py`, and the cycle's footprint contains **0** `.py`
files across all eleven paths. No floor venv was built and the shared `.venv` was not mutated.
Hot-path: none. Boundary count: 0. **CODE GAP list: empty**, for the seventh consecutive pass.

Two facts a green gate would otherwise hide are stated rather than omitted: the sweep is green over
a tree carrying 27 concurrent-owned dirty `.py` files, and `types/base.py` — a named
floor-verification trigger file — went dirty mid-pass from that same session, touching zero
`030`-audited symbols. It was not reverted, edited, or tidied.

Post-gate the cycle was committed as `6b3e1c82` (12 files), its deferred work homed on the board,
and its artifacts retired by `aa23d44d`.

## Deferred-work homing (Worker 0, post-gate, maintainer-requested)

The next spec author's reading list, carried over in substance from the final gate's
`### Deferred work catalog` (14 items, every one re-measured rather than inherited). Before the
artifacts were dropped the catalog was re-derived against the seven files it claimed to have walked,
rather than trusted: the integration pass's `### Carried items 1-9` dispositions every one, the
final catalog is a strict superset of the ten items handed to it, and every slice's deferral
section records `None`.

### Closed — do NOT read these as deferred

- **The terms-CSV `notes` content half.** 12 drifted cells reconciled by the integration pass, and
  the parser bug behind them fixed: `csv.DictReader` — used by both `check_spec_glossary.py` and
  the fakeshop `import_spec_terms` command — was silently truncating 8 of 50 `notes` cells at the
  first unquoted comma. Post-fix 0 of 50 truncate. The **gate** half stays open below.
- **The `DONE-032-0.0.9` parity row**, the `finalize_django_types()` auto-trigger deferral, and the
  unused `[goal]` link definition — all resolved in the integration pass against four independent
  sources apiece.
- **`test_anonymous_inline_fragment_under_connection_field_resolves` must stay absent from the
  spec.** Its subject is an optimizer selection-walker behaviour, not a `030` contract, and it only
  looks like one because it lives in this card's live block. The boundary is now recorded in
  `docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md`, deliberately not in the spec —
  naming it in the spec is the very thing the boundary forbids.
- **The `[alpha]` / `docs/TREE.md` instructions are landed work, not drift.** Already stated in the
  rationale companion, and more precisely than the artifact had it: two of the three `[alpha]`
  mentions are instruction sites describing completed work, the third is a licensed
  `## Current state` observation, and a sweep on the tag alone cannot tell the three apart.

### Open — homed on `TODO-ALPHA-052-0.0.16` as scope bullets

- **MF-1** — the three `030` glossary entries never say `totalCount` gating is directive-resolved
  (`optimizer/selections.py::should_include`). DB-backed regenerate.
- **MF-2 + MF-3 + MF-7 are ONE maintainer decision, not three** — the keyset / `Meta.cursor_field`
  feature is missing all three of its documentation homes: no owning spec, no glossary heading, no
  CHANGELOG entry. The surface is real (`ALLOWED_META_KEYS`, two-stage validation, 31 occurrences
  in `keyset.py`, four `GraphQLError` raise sites in `connection.py`).
- **MF-4** — the already-sliced-`QuerySet` `GraphQLError` is undocumented in both `CHANGELOG.md` and
  `docs/GLOSSARY.md`, under five tested spellings.
- **MF-5's gate half** — `check_spec_glossary.py` validates only `term,anchor` and never reads
  `notes`, so that column can assert arbitrary statuses indefinitely. One decision: either `notes`
  is contract text and needs a gate, or it is scratch and must stop asserting statuses.
- **MF-6** — stale `docs/spec-…` paths inside kanban card **bodies**, re-derived materially wider
  than recorded: 8 archived specs at 11 occurrences across 8 cards, against 154 correct
  `docs/SPECS/` occurrences. **The fix needs a three-way classification, never a global replace** —
  six further tokens must NOT be swept, three naming specs that do not exist yet (correct-in-advance
  under `AGENTS.md` rule 26) and three pre-canonical historical names.
- **The archive-wide inline-link-TEXT rot**, which a resolution-based checker structurally cannot
  find: the definitions resolve while the visible text names the pre-archival path. The same
  archival sweep produced every archived spec.
- **The rationale-companion coverage gap** — closing `030`'s hole makes `031` the leading edge of a
  21-spec gap (`031`-`043`, `049`-`055`, `063`); two specs carry no terms CSV either.

### Open — method notes, preserved outside the board

- **Card-less commits are this repo's ordinary mode**, not an anomaly — 11 in a bounded
  `git log -S` sweep over ten symbols, none adding uncontracted surface. The hazard is sharper than
  "the commit named no card": `6912ca92`, a card-less DRY pass, authored the single-call-site
  invariant Slice 1's whole guard-reachability audit rests on. And a card-less commit's **doc** debt
  is invisible to every provenance sweep — MF-3 and MF-4 are exactly that consequence.
- **`START.md` contains the literal `<!-- LINK DEFINITIONS -->` twice**, so any checker splitting
  body from definitions at the FIRST occurrence swallows 40 lines of live prose and reports a false
  unused-definition. Count the delimiter, then split on the LAST. The population is "any file that
  documents the convention" — which includes this one.
- **This spec's revision history is not the complete record of what reshaped it.** It lists three
  revisions and one finding round, yet four finding labels are cited from live code and tests, and
  two shipped contracts arrived through rounds it does not record. A provenance gap only: the
  round's contents were never recorded and **must not be reconstructed**.
- **Decision 13's no-version-bump rule survives only because four spec sites cite
  `tests/base/test_init.py::test_version` rather than the bare file** — the doc-wrap commit does
  touch that file. A tidy-up shortening those citations to the filename would falsify four spec
  sentences at once, and no gate in this repo would see it.
