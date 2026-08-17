# Package build plan: fieldmeta_consolidation / 0.0.6 (016) — residual-completion cycle

Spec source: `docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md` (already archived; card `DONE-016-0.0.6`)
Rationale companion: `docs/SPECS/appx/spec-016-fieldmeta_consolidation-0_0_6-rationale.md` — **does not exist**; creating it is this cycle's first obligation.
Terms companion: `docs/SPECS/appx/spec-016-fieldmeta_consolidation-0_0_6-terms.csv` (exists, 2 rows — `djangotype`, `relation-handling` — one row per anchor, importable shape; `check_spec_glossary` green: `OK: 2 terms`).
Target release: `0.0.6` (shipped; this cycle bumps no version and lands no feature).
Build rule: one round at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every round must justify shared/duplicated patterns before merging.
Ownership partition: **none; sequential rounds.** R1 and R3 both read/write spec-side Markdown and R3 audits what R1 wrote, so they could not run concurrently even if the rest were disjoint. R2 is the only round with a source file in its writable set (`optimizer/walker.py`) and still runs in sequence, because R1's reconciliation is what establishes the correct symbol vocabulary its fix must match.
Hot-path declaration: **none.** R1 and R3 write Markdown only. R2's single change is a docstring line — no executable statement changes, so no path gets slower or faster.
Floor-verification scope: **none.** No round touches a Django / Strawberry / channels integration seam. R2 edits a docstring inside `optimizer/walker.py`; the module's behavior at the floor is unchanged by construction (`docs/builder/BUILD.md` `## Floor verification` — the floor is Django 5.2.16 on Python 3.10 with strawberry-graphql 0.316.0, quoted here so no pass restates it from memory).
Pre-flight: passed on 2026-08-17 with two recorded deviations (steps 3 and 5, below); baseline: **dirty with concurrent sessions' work — 50 paths, none of them this cycle's**; cleanup: **nothing deleted or cleared** (deviation, below); memory files namespaced per cycle.

## Why this cycle exists

Card `DONE-016-0.0.6` shipped at `0.0.6`, so the code is not in question as *new* work. Three obligations, in the maintainer's framing:

1. **Nothing was skipped in the code.** Everything spec-016 promised must be present at `HEAD`, and anything promised and never delivered is a defect this cycle fixes.
2. **Later work that changed the shipped shape is legitimate — but the spec must say so.** Where a later card moved, renamed, or widened something spec-016 owns, the spec is rewritten to state the **current** contract directly. It never narrates the change (`docs/builder/BUILD.md` `## Spec rationale extraction`).
3. **The explanation goes in the rationale, not the spec.** What changed, why, which commit caused it, and what the spec may no longer claim — all of it lands in the rationale companion, keyed to the spec section it belongs to.

Spec-016 is a **card-snapshot stub**, the same shape as specs 011-013 and the opposite of spec-015: 4,558 bytes, no numbered Decisions, no slice checklist, no test plan, and an explicit self-description ("This file is intentionally lightweight… Before implementation work starts from this file, expand it into the full builder-format spec") that the shipped work overtook — the card shipped without the expansion ever happening. So its rationale companion is a **reconstruction from history**, not a `## Spec rationale extraction` move: there is no deliberative layer in the file to cut. R1 must say so in the companion's own provenance section rather than implying a move happened.

## Pre-flight record, with its two deviations

| Step | Outcome |
|---|---|
| 1. Working-tree baseline explicit | `git status --short` -> **50 paths**, none this cycle's; `HEAD` = `d94db99262617bd21a36a7b60cc5dd2603d0b3b5`. Recorded under `## Baseline-dirty out-of-scope files`. |
| 2. `scripts/review_inspect.py` runs | green — `uv run python scripts/review_inspect.py django_strawberry_framework/optimizer/field_meta.py --output-dir docs/shadow --stdout` printed a full overview (7 imports, 9 symbols, 0 TODO comments). |
| 3. Build artifacts reset | **DEVIATION — nothing deleted.** `docs/builder/bld-003-final.md` and `docs/builder/bld-015-final.md` are *tracked* records of two prior residual cycles, and `docs/builder/DONE/build-009-…` / `DONE/build-015-…` are a concurrent session's in-flight archive moves. This cycle's input is already-built work, so `worker-0.md` `## Pre-flight procedure` step 3's round carve-out applies: prior artifacts must survive. Verified instead that **no `build-016-*` or `bld-016-*` path exists**. |
| 4. `.gitignore` lists the scratch paths | green — `.gitignore:174` `docs/shadow/`, `:188` `docs/builder/worker-memory/`, `:192` `docs/builder/temp-tests/`. |
| 5. Scratch directories cleared | **DEVIATION — nothing cleared.** `docs/shadow/` and `docs/builder/temp-tests/` hold a concurrent session's live review-cycle output (`docs/shadow/current/`, `temp-tests/r1`, `r1c`, `r2`, `r4`). Clearing them would destroy another session's in-flight work (`AGENTS.md` rule 34, `START.md` `## Concurrent sessions`). This cycle writes no shadow file it does not create itself and no temp test at all. |
| 6. Spec-doc consistency check | green — `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md` -> `OK: 2 terms - all have glossary entries and at least one spec link.` |
| 7. Spec rationale extracted | **not yet — it is R1's contract.** No round after R1 is dispatched until the companion exists (`docs/builder/BUILD.md` `## Pre-flight checks`). |

## Worker-0 verification pass (performed before any dispatch)

`docs/builder/BUILD.md` `### Worker 0 verifies every finding against source before dispatching`. Every claim below was read against `HEAD` (`d94db992`) before this plan was written. Four of the five files spec-016 names are **clean** at baseline; `optimizer/extension.py` is **dirty with a concurrent session's work**, so every reading of it — and, for uniformity, of the others — was taken read-only through `git show HEAD:<path>` / `git grep … HEAD`. No `git stash`, `git checkout`, `git restore`, or `git worktree` was used.

### What the card actually did — recovered from history

> **Corrected by R1's own measurements (recorded here so the plan does not stay wrong).** Four facts below were re-measured during R1 and came back different: (a) the card shipped **two** commits, not one — `de35a622` (implementation) plus `2bd7cb84` two hours later (the `CHANGELOG.md` entry, the board card, the `BETTER.md` item-35 deletion), and `CHANGELOG.md` is not among `de35a622`'s paths at all; (b) `optimizer/walker.py::_resolve_optimizer_hints` was **created by `de35a622` itself**, not extracted later — so V5's "extracted into its own helper" is right about the shape and wrong about the timing, and the spec's `_walk_selections (hints read)` was stale on the day it shipped; (c) V1's rename and V2's upstream move are **one** later commit, `f83bb71b` (2026-05-20); (d) the audit method's qualified name is `optimizer/extension.py::DjangoOptimizerExtension.check_schema` — the bare `::check_schema` used in V7 and F8's neighbourhood is wrong, as it is in `CHANGELOG.md:221`. The reconciled spec and the rationale companion carry the corrected facts; V1-V11's verdicts are unaffected.

`de35a622` **"refactor(types,optimizer): consolidate metadata onto DjangoTypeDefinition"** (2026-05-15) is the card's implementation commit, and its own message enumerates three parts: thread `FieldMeta` through the three `types/` readers and add `relation_kind` / `is_many_side` properties; retire the two class-attribute mirrors so the walker and extension read `registry.get_definition(...)`; remove the **eight** `TODO(spec-fieldmeta-*)` anchors the migration closed. The commit touched 16 files: the five the spec names, plus **`django_strawberry_framework/optimizer/field_meta.py`** (the `FieldMeta` properties and the module docstring that had carried the anchors) and **six test files** the spec's file list omits — `tests/optimizer/test_definition_order.py`, `test_extension.py`, `test_field_meta.py`, `test_walker.py`, `tests/types/test_relay_interfaces.py`, `tests/types/test_resolvers.py` (+403/-178 overall).

### V1-V11: nothing was skipped in the code — verified, not assumed

| # | Claim to verify | At `HEAD` | Evidence |
|---|---|---|---|
| V1 | the `types/base.py` pending-relation site reads `FieldMeta` from the canonical `field_map` | **true, at a renamed site** | the read is `types/base.py::_build_annotations #"field_meta = field_map[snake_case(field.name)]"`, feeding `PendingRelation(relation_kind=field_meta.relation_kind, nullable=field_meta.nullable)`. `_record_pending_relation` — the symbol the spec names — **no longer exists**: `git grep -n "def _record_pending_relation" HEAD` returns nothing. It was the helper `de35a622` threaded `field_meta` into, later folded into `_build_annotations` when spec-018 removed the eager-bind branch. **Drift in the spec's vocabulary, not a gap in the code.** |
| V2 | `types/converters.py::resolved_relation_annotation` reads `FieldMeta` rather than re-deriving shape | **true, and the read moved upstream** | the function signature is `(field, target_type, *, field_meta: FieldMeta \| None = None)` and its body reads only `meta.is_many_side` / `meta.nullable`. Its one production caller passes the canonical value explicitly: `types/finalizer.py::finalize_django_types #"field_meta = definition.field_map[snake_case(pending.field_name)]"` then `resolved_relation_annotation(…, field_meta=field_meta)`. The `None` default re-derives via `FieldMeta.from_django_field` and is exercised only by direct/test callers (`tests/types/test_base.py::test_resolved_relation_annotation_nullable_fk_widens_to_optional`). |
| V3 | `types/resolvers.py::_make_relation_resolver` reads `FieldMeta` from the definition | **true, via a named helper added later** | `types/resolvers.py::_field_meta_for_resolver` does `registry.get_definition(parent_type)` -> `definition.field_map.get(field.name)` and documents that production callers MUST pass `parent_type=cls`; `_make_relation_resolver` consumes `field_meta.relation_kind` / `.is_many_side`. Two documented fallbacks exist for test doubles only (`FieldMeta._from_field_shape` for descriptors lacking `is_relation`, else `FieldMeta.from_django_field`). |
| V4 | `optimizer/walker.py::_resolve_field_map` reads `registry.get_definition(...)`, not a mirror | true | `#"definition = registry.get_definition(type_cls) if type_cls is not None else None"`, with `field_map = definition.field_map` when registered and a `model._meta.get_fields()` walk when not. |
| V5 | the walker's hints read comes from the definition | **true, extracted into its own helper** | `optimizer/walker.py::_walk_selections #"hints_map = _resolve_optimizer_hints(definition)"`; `::_resolve_optimizer_hints` returns `definition.optimizer_hints or {}`. The same callable is injected into the nested-connection planner (`walker.py #"resolve_optimizer_hints=_resolve_optimizer_hints"` -> `optimizer/nested_planner.py #"hints_map = resolve_optimizer_hints(definition)"`), so spec-033's planner inherits the canonical read rather than opening a second source. |
| V6 | `optimizer/extension.py::_collect_schema_reachable_types` reads the definition | true | `#"if origin is not None and registry.get_definition(origin) is not None"` gates membership on a registered definition. |
| V7 | `optimizer/extension.py::check_schema` reads the definition | true | `#"definition = registry.get_definition(type_cls)"` -> `field_map = definition.field_map`, `hints = definition.optimizer_hints or {}`. |
| V8 | the mirrors are gone from `DjangoType.__init_subclass__` and nothing reads them | true | `grep -rn "_optimizer_field_map" --include='*.py'` over `django_strawberry_framework/`, `tests/`, `examples/`, `scripts/` returns **no match** (`_optimizer_hints` matches only unrelated `_meta_optimizer_hints` / `_validate_optimizer_hints` / `_resolve_optimizer_hints` symbol names). The two `ClassVar` declarations and the mirror writes were deleted in `de35a622`. |
| V9 | all `TODO(spec-fieldmeta-*)` anchors are removed | true | `grep -rn "spec-fieldmeta" --include='*.py' .` returns nothing; the `optimizer/field_meta.py` module docstring that carried the anchor paragraphs now ends at "eliminating per-request Django introspection overhead." |
| V10 | `FieldMeta` carries the cardinality API the readers consume | true, **and its bodies were later re-pointed at the shared helpers** | `optimizer/field_meta.py::FieldMeta.relation_kind` is now `return relation_kind(self)` and `::FieldMeta.is_many_side` is `return is_many_side_relation_kind(self.relation_kind)` — delegations to `utils/relations.py`. `de35a622` shipped both as inlined branch ladders; a later DRY pass collapsed them onto the shared classifier. Same answers, one implementation. |
| V11 | no second field-metadata store was reintroduced anywhere | true | every `field_map` producer at `HEAD` is `DjangoTypeDefinition.field_map` or the walker's documented unregistered-model fallback; `rest_framework/inputs.py`'s `_fingerprint_field_map` is DRF serializer fields, an unrelated namespace. |

**No skipped feature, and no correctness defect.** One source-level defect was found (F5 below) and it is a docstring source-reference error, not behavior — so **exactly one round in this cycle dispatches Worker 2**, per the maintainer's dispatch instruction that workers beyond Worker 1 are spawned only when the code needs updating.

### R1 findings — the spec's own text

Each is a claim the shipped code or later work falsified, or a deliberative layer that never got a home. None is a code defect.

| # | Finding | Evidence |
|---|---|---|
| F1 | **No rationale companion exists, and there is no deliberative layer in the spec to move.** The file is a card snapshot: `## Card snapshot`, a one-word `## Planning note` ("shipped"), `## Scope`, `## Why it matters`, and an eleven-bullet `## Other` dumping ground. R1 therefore **reconstructs** the deliberation from `de35a622`, the `BACKLOG.md` item-35 history, the retired `TODO(spec-fieldmeta-*)` anchor text (recoverable from the pre-commit `field_meta.py` docstring), and the later commits that reshaped the shipped sites — and says in the companion's provenance section that this is a reconstruction, not a move. | `ls docs/SPECS/appx/spec-016-*` returns only the terms CSV; spec `#"This file is intentionally lightweight"` |
| F2 | **Every source reference in the spec uses the forbidden `path:symbol` colon form** — seven of them, plus `KANBAN.md`-style bare paths. `AGENTS.md` rule 27 requires `path::QualifiedName`, and raw `path:NN` / `path:name` is licensed only in per-cycle scratchpads, which an archived spec is not. | spec `## Scope` bullets, e.g. `#"django_strawberry_framework/types/base.py:_record_pending_relation"` |
| F3 | **Three of the seven named reader sites no longer exist under those names**, so the spec cannot be read against `HEAD` as written: `_record_pending_relation` is gone (V1), the `resolved_relation_annotation` canonical read now happens in `types/finalizer.py` (V2), and the `_walk_selections` hints read is now `_resolve_optimizer_hints` (V5). The reconciliation states the current sites; the renames and their causes go to the companion. | V1, V2, V5 |
| F4 | **The spec's "single source of truth" claim is stated without the two bounded exceptions the shipped code documents**, and a reader checking the code against the spec finds them and cannot tell whether they are drift or design: the walker's **dual contract** (`FieldMeta` for a registered model, raw Django field objects on the unregistered-model fallback, safe only because every downstream read is `getattr(…, default)`) and the **test-double fallbacks** in `_field_meta_for_resolver` / `resolved_relation_annotation(field_meta=None)`. Both are deliberate and both are load-bearing; the spec owes them a sentence. | `optimizer/walker.py::_resolve_field_map #"DUAL CONTRACT (read before consuming the returned map)"`; `types/resolvers.py::_field_meta_for_resolver` |
| F5 | **The spec's file list is incomplete against its own commit**: `optimizer/field_meta.py` — where the `FieldMeta` properties the whole consolidation consumes were added and where the retired anchors lived — is absent, as are the six test files `de35a622` updated. The spec claims "Existing tests pass without modification", which its own commit falsifies (+120 lines in `tests/optimizer/test_walker.py` alone, +72 in `tests/types/test_resolvers.py`). | `git show --stat de35a62` |
| F6 | **The `~7 sites of duplicated relation-shape logic` claim needs the current population, not a tilde.** At `HEAD` the free classifiers `relation_kind(field)` / `is_many_side_relation_kind(...)` are still called on raw Django descriptors at several sites by design (`connection.py`, `filters/sets.py`, `join_taxonomy.py`, `walker.py`, `utils/relations.py` itself) — those are not the duplication this card retired, and a reader who greps the classifier and finds them concludes the consolidation was undone. The reconciled text distinguishes "reads shape from a `FieldMeta`" (this card's contract) from "calls the shared classifier on a raw field" (never in scope). | `git grep -n "relation_kind(\|is_many_side_relation_kind" HEAD -- django_strawberry_framework` |
| F7 | The `Status:` line and `## Planning note` still address a *future* implementation ("Before implementation work starts from this file, expand it into the full builder-format spec…"; `## Planning note` = "shipped"). The work shipped nineteen cards ago; the instruction cannot be followed and the note is not a sentence. | spec preamble |

### R2 finding — the one source-level defect

| # | Finding | Evidence |
|---|---|---|
| F8 | **`optimizer/walker.py::_resolve_field_map`'s docstring points its dual-contract cross-reference at a module that does not exist.** It reads "The same divergence (and the same `getattr`-defensive fallback) lives in `optimizer/resolvers.py::_field_meta_for_resolver`; keep the two in sync." There is no `django_strawberry_framework/optimizer/resolvers.py`; the symbol is `django_strawberry_framework/types/resolvers.py::_field_meta_for_resolver` (V3). This is the *one* cross-reference tying the two halves of this card's SSoT surface together, and it sends a reader looking for a file that was never there. Verified by grep: `git grep -n "optimizer/resolvers" HEAD -- django_strawberry_framework tests examples docs` returns exactly **one** line, this one. | `HEAD:django_strawberry_framework/optimizer/walker.py:313` |

`optimizer/walker.py` is **clean** at baseline (`git status --short` does not list it), so R2 edits it without colliding with the concurrent sessions. Scope is one docstring line; `AGENTS.md` rule 27's "renaming a symbol means grep-sweep `::OldName` in the same change" is the standing authority, and the grep above is the sweep. Not a boundary, so it owes no failability proof (`docs/builder/BUILD.md` `### What needs a proof, and what does not`).

### R3 findings — documentation completion and archive audit

| # | Finding | Evidence |
|---|---|---|
| F9 | **The archive move is already done.** The spec is at `docs/SPECS/`, its terms CSV at `docs/SPECS/appx/`, the DB agrees (`SpecDoc(name='spec-016-fieldmeta_consolidation-0_0_6', path='docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md')`), and `KANBAN.md:131` renders the link at the archived path. What R3 owes is an audit — including the **new** companion's own link hygiene and the depth-rot traps a `docs/SPECS/appx/` file inherits — not a move. | DB read via `manage.py shell`; `KANBAN.md:131` |
| F10 | **The DONE-card invariants already hold and no DB edit is owed for them.** Card 16 is `status.key == "done"`, carries the `SpecDoc`, and carries both `CardGlossaryTerm` links (`djangotype`, `relation-handling`) matching the two-row CSV exactly. Every `Scope` / `Why it matters` / `Note` / `Files likely touched` `CardItem` is `is_complete=True`. | DB read |
| F11 | The card's `CardItem` bodies are a **verbatim copy of the spec's pre-reconciliation text**, colon-form source references and the retired `_record_pending_relation` name included. R3 decides whether re-stating them is owed and records the answer either way; it does **not** perform DB writes (`worker-0.md` reserves ORM edits + regenerate for a Worker 2 pass, which this cycle dispatches only if R3 finds the edit owed). The default answer is "not owed": a card body is the board's record of the card, `KANBAN.md`/`KANBAN.html`/`docs/GLOSSARY.md` are generated, and gratuitous `db.sqlite3` churn is the expensive mistake here. | DB read; `docs/builder/BUILD.md` `### Generated docs are DB-backed` |
| F12 | **`CHANGELOG.md:221` names this card by its pre-renumber id** — `[012-fieldmeta_single_source_of_truth_consolidation_and_mirror_retirement-0.0.6]` — and the card is now `016`. It is the same stale-KANBAN-id class spec-015's cycle catalogued rather than partial-fixed, and `AGENTS.md` rule 21 forbids CHANGELOG edits unless told. R3 records it in the deferred catalog; **no round edits `CHANGELOG.md`.** | `git grep -n "_optimizer_field_map" HEAD -- CHANGELOG.md` |
| F13 | The durable docs are complete for this card's work: it is an internal refactor with no consumer-visible surface, so `docs/README.md` owes it nothing; `docs/GLOSSARY.md` carries both linked anchors; `docs/TREE.md` renders `optimizer/field_meta.py` with its shipped docstring. **No durable-doc edit is owed** — R3 re-verifies rather than assumes. | read at `HEAD` |

## Baseline-dirty out-of-scope files

`HEAD` at plan time: `d94db99262617bd21a36a7b60cc5dd2603d0b3b5`; `git status --short | wc -l` -> **50**, and **not one of them is this cycle's**. Every path belongs to a concurrent maintainer session (`START.md` `## Concurrent sessions`, `AGENTS.md` rule 34). **No worker edits, reverts, stages, or `git checkout`s any of them.** In particular:

- **Package source, modified:** `mutations/resolvers.py`, `optimizer/extension.py`, `optimizer/nested_planner.py`, `optimizer/plans.py`, `optimizer/selections.py`, `orders/inputs.py`, `orders/sets.py`, `relay.py`, `templates/django_strawberry_framework/debug_toolbar.html`. **`optimizer/extension.py` is one of the five files spec-016 names** — hence the read-only `git show HEAD:` discipline for V6/V7 and the rule that no round in this cycle opens it.
- **Tests, modified:** `tests/middleware/test_debug_toolbar.py`, `tests/mutations/test_resolvers.py`, `tests/optimizer/test_extension.py`, `test_plans.py`, `test_selections.py`, `tests/orders/test_inputs.py`, `test_sets.py`, `tests/test_relay_connection.py`, `examples/fakeshop/test_query/test_multi_db.py`, `test_optimizer_auto_api.py`.
- **Another session's review cycle, untracked:** ~29 `docs/review/rev-*.md` files plus a modified `docs/review/review-0_0_14.md`. `AGENTS.md` rule 22 forbids bulk-deleting or overwriting anything under `docs/review/`.
- **Another session's archive moves, uncommitted:** `D docs/builder/build-009-…` / `D docs/builder/build-015-…` against `?? docs/builder/DONE/build-009-…` / `?? docs/builder/DONE/build-015-…`. This cycle's own plan file stays at `docs/builder/`; moving it is the maintainer's call, not a worker's (`AGENTS.md` #"Commit authorization does not carry forward").
- **`examples/fakeshop/db.sqlite3` is clean right now**, which is the evidence that no concurrent card-wrap is mid-flight. Any round that would write the DB re-checks that before touching it; this cycle plans no DB write.

## Concurrent-writable tracked binary / generated files

Per `docs/builder/BUILD.md` `### Tracked binary / generated files: churn and concurrent-writer handling`: `examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`. None is in any round's writable set. If one of them turns dirty during this cycle it is a concurrent writer's, **not** this build's output, and no round reverts it.

## Artifact list

- `docs/builder/bld-016-r1-rationale_and_spec_reconciliation.md` — Worker 1 (procedural-closure shape: plan + final verification in one artifact)
- `docs/builder/bld-016-r2-walker_source_reference_fix.md` — full cycle: Worker 1 plan -> Worker 2 build -> Worker 3 review -> Worker 1 final verification
- `docs/builder/bld-016-r3-doc_completion_archive_audit.md` — Worker 1 (procedural-closure shape)
- `docs/builder/bld-016-final.md` — Worker 1, the final test-run gate

**No `bld-integration.md` for this cycle.** R2 lands one docstring line and R1/R3 land Markdown, so there is no cross-round DRY surface for a consolidation pass to find. The integration pass's two live obligations — `docs/builder/BUILD.md` `## Cross-slice integration pass` step 1 (read every closed artifact in full) and step 6 (the staged-anchor sweep for `TODO(spec-016` / `TODO-(ALPHA|BETA|STABLE)-016`) — are folded into the final gate, which records them explicitly.

## Checklist

- [x] R1: rationale companion (reconstruction) + spec reconciliation -> `docs/builder/bld-016-r1-rationale_and_spec_reconciliation.md`
- [x] R2: correct the `_resolve_field_map` dual-contract cross-reference (F8) -> `docs/builder/bld-016-r2-walker_source_reference_fix.md`
- [x] R3: documentation completion + archive audit -> `docs/builder/bld-016-r3-doc_completion_archive_audit.md`
- [x] Final test-run gate -> `docs/builder/bld-016-final.md`

## Worker memory

Namespaced per cycle so a concurrent session's build cannot read or clobber them: `docs/builder/worker-memory/spec-016-worker-0.md` … `spec-016-worker-3.md`, seeded empty at plan time. Gitignored (`.gitignore:188`). The four un-namespaced `worker-N.md` files in that directory are left untouched.

## Post-gate note (Worker 0)

Every checklist box is `- [x]`; `docs/builder/bld-016-final.md` reads `final-accepted`. Worker 0 stops
driving here and hands off to the maintainer (`docs/builder/BUILD.md` `## Slice handoff`). Closeout —
the retrospective, the memory read, and the `docs/shadow/` / `docs/builder/temp-tests/` cleanup — runs
only **after** the maintainer commits and supplies the build-cycle commit range, and this cycle must
not clear those scratch paths in any case while a concurrent session's live output is in them.

Two post-gate re-checks Worker 0 ran, because concurrent sessions dirtied two of this card's reader
sites (`types/base.py`, `types/finalizer.py`) during the gate:

- All nine symbols the reconciled spec cites still resolve to exactly one `def` in the **worktree**,
  not only at `HEAD`.
- All four `#"unique substring"` citations the spec carries into `types/base.py`,
  `types/finalizer.py`, `optimizer/walker.py`, and `optimizer/nested_planner.py` still match exactly
  once each in the worktree (`grep -cF` -> `1`, `1`, `1`, `1`).

So the reconciled spec describes the tree as it stands now, not merely as it stood at plan time.

## Deferred-work homing (Worker 0, post-gate)

Eight of the eighteen `## Deferred work catalog` items were homed onto the board on 2026-08-17 as four
`CardItem` Scope rows, so nothing in the catalog depends on this cycle's artifacts surviving their own
retirement. Prior cycles' final artifacts are deleted at close while cards keep citing them by name
(`bld-009-final.md`, `bld-011-final.md` and `bld-013-final.md` are all already gone and all still
cited), which is why each bullet enumerates its population inline rather than pointing at a file.

- `TODO-ALPHA-051-0.0.15` gained three rows: catalog item 9 as a constraint on WP-D's own
  `_resolve_field_map` dual-contract retirement (**delete** the paragraph, its cross-reference and the
  spec's first bounded exception -- never re-point them); catalog items 1, 5 and 6 as one rule-27
  fold-in row over `optimizer/walker.py`, `optimizer/field_meta.py` and `tests/test_registry.py`; and
  catalog item 7 as the corrected bare-basename census.
- `TODO-ALPHA-052-0.1.0` gained one row: catalog items 3 and 4, whose two files no `051` WP batch
  opens, folded into that card's existing repo-wide rule-27 sweep.

Item 2 stays with the maintainer (`AGENTS.md` rule 21 bars the `CHANGELOG.md` edit) and items 8 and
10-18 are decided rulings or standing method notes that own no work, so they were not carded.

**Two catalog figures were re-derived at homing time and came back different, both understated.**
Recording the mechanism, because in each case the instrument -- not the tree -- was the cause:

- Catalog item 7's ambiguous class is **13** cross-folder occurrences at `HEAD` `fa248bdf`, not 12. The
  census pattern that produced 12 matched only the double-backtick RST spelling, so the two
  single-backtick occurrences in `filters/base.py` were invisible to it; both landed 2026-07-13 and
  2026-07-15, so neither is new. A 14th occurrence exists in the worktree only, from a concurrent
  session's uncommitted `mutations/resolvers.py` edit. The acquitted classes re-measured at 97
  same-folder and 61 unique-basename cross-folder (recorded as 98 and 56); `HEAD` has moved several
  commits since the gate, so those two deltas are not attributed to the instrument.
- Catalog item 3 is **two** dotted references, not one: `registry.py`'s module docstring lists
  `types.converters.resolved_relation_annotation` and `types.converters.convert_choices_to_enum` in the
  same reader list. Fixing one of two entries in one list would leave it divergently rather than
  uniformly spelled, so the card row moves them as a pair.

This is the sixth and seventh instance in this cycle of one failure shape: **a population measured
through an instrument inherits that instrument's blind spot, and the number outlives the measurement.**
Both standing rules already in the record cover it -- count occurrences rather than matching lines, and
state the corpus and the pattern as explicit parameters of any figure.
