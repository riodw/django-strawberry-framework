# Package build plan: optimizer / 0.0.2 (002)

Spec source: `docs/SPECS/spec-002-optimizer-0_0_2.md` (**already archived** — the spec, its `-terms.csv`, the `SpecDoc.path` row, and every inbound cross-reference already sit at their post-archive locations; item R3 verifies rather than performs the move)
Target release: `0.0.2` (**shipped long ago** — card `DONE-002-0.0.2`, `target_version.number` `0.0.2`; the package is at `0.0.14` in `pyproject.toml`)
Date created: 2026-08-07
Build rule: one item at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every item must justify shared/duplicated patterns before merging. A fact told twice across the spec and its rationale sibling goes stale in one of them — the rationale carries the deliberation, the spec carries the contract, and neither restates the other.
Ownership partition: none; sequential residual items.
Hot-path declaration: none. No residual item changes package source, so no item runs per request, per resolver, per row, per connection, or per outbound message.
Floor-verification scope: none. No residual item touches a Django / Strawberry / channels integration seam — the cycle edits the spec, its rationale sibling, cross-references, and (only if the audit finds drift) DB-rendered docs.
Pre-flight: passed on 2026-08-07 with **three** recorded deviations (below); baseline: clean at step 1, then nine concurrent-session entries appeared while this plan was being written — see `## Baseline-dirty out-of-scope files`; cleanup: **deliberately not performed** — see Deviation 1.

## This is a residual-completion cycle, not a fresh build

Every slice spec-002 declares (O1-O6) was built and released at `0.0.2`, twelve minor versions ago. What remains is the deliverable set the shipped cycle never produced, plus the reconciliation that fifty-odd later specs made necessary. The maintainer scoped it in three sequential items: the missing `-rationale.md`, the spec-versus-HEAD reconciliation, then the documentation and archive audit.

The immediate precedent is the **spec-001 residual cycle**, committed at `cfd1f873` on 2026-08-06 (`docs/builder/build-001-django_types-0_0_1.md` and its four `bld-001-*` artifacts). This plan follows its structure deliberately: the two cycles are the same shape, and spec-001 is spec-002's own parent document.

### Already-shipped spec slices — verified delivered at HEAD (no build cycle dispatched)

Not checkboxes: Worker 0 may only tick a box after a Worker 1 final verification, and these slices predate this plan by twelve releases. They are evidence, pre-verified by Worker 0 at pre-flight so no worker re-derives them.

| Spec slice | Delivered at HEAD — evidence |
|---|---|
| O1 — custom relation resolvers | `django_strawberry_framework/types/resolvers.py::_attach_relation_resolvers` + `::_make_relation_resolver`; attached from `types/finalizer.py::finalize_django_types` (see D1) |
| O2 — selection-tree walker | `django_strawberry_framework/optimizer/walker.py::plan_optimizations` (module present at the spec's declared path) |
| O3 — root-gated optimizer hook | `optimizer/extension.py::DjangoOptimizerExtension.resolve`, gate `if info.path.prev is not None: return result` |
| O4 — nested prefetch chains | shipped; `_collect_scalar_only_fields` is **absent** from the package, exactly as `spec-003` predicted its deletion |
| O5 — `only()` projection | `optimizer/plans.py::OptimizationPlan.apply` #"queryset.only(*self.only_fields)" |
| O6 — `get_queryset` + `Prefetch` downgrade | `optimizer/walker.py::_target_has_custom_get_queryset` drives the prefetch-boundary branch; `plan.cacheable` flips |

### Residual scope (this cycle's actual work)

- **R1 — spec rationale extraction.** `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` does not exist. `docs/builder/BUILD.md` `## Spec rationale extraction` makes the move the first substantive action of a build and pre-flight step 7 gates dispatch on it; the shipped cycle predates the rule. Worker 1 is the only role that may perform it. Spec-002 is a **short** spec (7,398 bytes, 113 lines) — unlike spec-001's 52KB — so the mover's judgement matters more than its stamina: the deliberative layer here is thin and interleaved rather than concentrated in one section. `## O4 extraction`, the `## Problem statement`'s account of what "pushed the optimizer story into its own subsystem", `## Architecture decision`'s justification paragraphs, and `## Open questions` are the visible candidates; the mover decides.
- **R2 — reconcile the spec with what landed and what later specs corrected.** The maintainer's framing: *make sure the spec matches what actually exists, make sure the code is correct, and where later updates corrected what landed, the spec reflects that; the explanation of each change goes in the rationale, never in the spec.* Fifteen verified drift items are tabled below. Worker 1 is the only role that may edit the spec.
- **R3 — finish the documentation and audit the archive.** Verify the durable docs (`docs/README.md`, `docs/TREE.md`, `docs/GLOSSARY.md`, `KANBAN.md`) describe the spec-002 optimizer surface as shipped, and verify the already-performed archive is complete in all three cross-reference directions, in the kanban DB, and in the terms-CSV importability chain.

**"Make sure the code is correct" is a read-only audit obligation, not a licence to change source.** If R2 or R3 finds a genuine correctness defect in shipped optimizer code, it is recorded as a finding and escalated to the maintainer — it does not become a source edit inside a documentation cycle. `AGENTS.md` rule 5 (root-cause fix, never defer) governs what the *fix* must look like when the maintainer authorizes one; it does not authorize a docs cycle to silently become a code cycle.

## Pre-flight outcome (7 steps, `docs/builder/worker-0.md` `## Pre-flight procedure`)

1. **Working-tree baseline is explicit.** `git status --short` → **empty**. The concurrent session that held `KANBAN.md` / `KANBAN.html` / `docs/SPECS/spec-048-…` / `docs/builder/bld-048-final.md` / `db.sqlite3` dirty at session start committed them at `faebd949` before this pre-flight ran. Baseline at this step is clean. It did not stay that way — see `## Baseline-dirty out-of-scope files`.
2. **`scripts/review_inspect.py` runs.** `uv run python scripts/review_inspect.py django_strawberry_framework/optimizer/walker.py --output-dir docs/shadow --stdout` emitted its overview (23 imports, 39 symbols, 9 control-flow hotspots, 2 TODO comments, 7 repeated string literals). Working.
3. **Build artifacts are reset — DEVIATION 1, see below.** Verified instead that every path this plan creates is absent: no `docs/builder/build-002*`, no `docs/builder/bld-002*`, no `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md`.
4. **`.gitignore` lists the untracked scratch paths.** `docs/shadow/` (line 174), `docs/builder/worker-memory/` (188), `docs/builder/temp-tests/` (192). Present.
5. **Scratch directories are cleared — DEVIATION 1, see below.** Deliberately not cleared.
6. **Spec-doc consistency check.** `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-002-optimizer-0_0_2.md` → `OK: 3 terms - all have glossary entries and at least one spec link.` Exit 0. Baseline for the constraint in `### The 3-anchor constraint` below.
7. **Spec rationale is extracted.** **Not done — it is item R1 of this cycle.** Ordinarily this gates dispatch. Here it cannot, because R1 *is* the dispatch: the slices whose spawns the gate protects were built and released before this plan existed, so there is no builder left to protect. R1 runs first regardless, so every later spawn in this cycle reads the smaller spec exactly as the rule intends.

Two further baselines recorded at pre-flight, both green, both re-checked by any pass that writes:

- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-002-optimizer-0_0_2.md` → exit 0 (link-definition scaffold and the 10 canonical group headers intact).
- `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+' docs/SPECS/spec-002-optimizer-0_0_2.md` → no match. The spec carries **no** raw `path:NN` reference today; `AGENTS.md` rule 27 compliance is a property to preserve, not one to establish.

### Deviation 1 — the prior cycles' artifacts, memory, shadow, and temp-tests are PRESERVED

Pre-flight steps 3 and 5 delete old `build-*.md` / `bld-*.md` and clear the three scratch paths. Not performed, deliberately:

- The 34 artifacts under `docs/builder/` belong to the spec-001 and spec-044 through spec-049 cycles and are **committed**. A blanket artifact delete would destroy the record of work now under review — including `build-001-django_types-0_0_1.md`, which this plan cites as precedent.
- `docs/builder/worker-memory/` (four files, 585 lines) and `docs/builder/temp-tests/` (eight cycle directories) are **gitignored**, so deleting them is unrecoverable, and `worker-0.md` `## Closeout job` steps 2 and 5 read exactly those files.
- The reasoning is `BUILD.md`'s own, under `### Cohorting, naming, and closure` ("Pre-flight for a round"): when the input to a cycle is already-built work, the prior artifacts are the record of that work and must survive. Every residual item here operates on already-built, already-released work.
- **Collision is avoided by naming, not by deletion.** Every artifact this plan creates is `bld-002-`-prefixed, and none of those paths exists. The maintainer's dispatch instruction required exactly this ("use file naming to not conflict with existing concurrent bld work").
- Consequence for dispatch: each worker's memory file opens with earlier cycles' entries. Dispatch prompts say so and require this cycle's entries to be appended under a `## spec-002 residual cycle` heading, so the cycles stay distinguishable at the next closeout.

### Deviation 2 — artifact filenames carry the `002` card number

`## Build artifact naming` gives `bld-slice-<N>-<short_slug>.md`; the surviving spec-046 set already occupies `bld-slice-1..5-*`, `bld-integration.md`, and `bld-final.md`, and the spec-001 set occupies `bld-001-*`. This cycle uses `bld-002-<item>-<slug>.md` and `bld-002-final.md` — still `docs/builder/bld-`-prefixed, and unambiguous about which cycle each artifact records. The items are also not spec slices (the spec's slices shipped at `0.0.2`), so an `N` mirroring a slice number would misdescribe them.

### Deviation 3 — the `built` state is skipped where the deliverable is Worker-1-exclusive

`docs/builder/ARTIFACT.md` `## Status field ownership` gives `built` to Worker 2, and `worker-0.md` `## Per-slice dispatch` maps `planned` → Worker 2. Items **R1 and R2** have no Worker 2 role that could set it:

- **R1** — `BUILD.md` `## Spec rationale extraction` makes Worker 1 the only role that performs the move, and states outright that **Worker 2 never reads the rationale file** — "that is the point of the move." Dispatching a builder at it would hand the file to the one worker the mechanism exists to keep away from it.
- **R2** — `BUILD.md` `## Spec reconciliation` and `worker-1.md` `## Scope` make Worker 1 the **only** role that may mutate the spec. R2's entire deliverable is spec edits.

So for R1 and R2 the chain is **Worker 1 (plan + perform, `planned`) → Worker 3 (audit, `review-accepted` | `revision-needed`) → Worker 1 (final verification, `final-accepted`)**, and Worker 0 reads `planned` on those artifacts as "dispatch Worker 3", not Worker 2. Declared here, before dispatch, so no pass improvises the mapping.

The Worker 3 audit is **not** skippable alongside the Worker 2 build. `BUILD.md` names Worker 3 as a reader of the rationale file during review and as the pass that checks the finished implementation against it. A rewrite performed by the author is reviewed by an agent with no memory of why a sentence was cut — the only vantage point from which an over-cut looks like an over-cut. **R3 has real Worker 2 work** (durable-doc and, if drift is found, DB edits) and runs the full unmodified chain.

## Baseline-dirty out-of-scope files

Workers neither edit nor revert these, and never `git checkout` them (`AGENTS.md` rule 34).

`git status --short` was **empty** at pre-flight step 1. It stopped being empty **before this plan was finished being written** — a concurrent session opened a cycle on the spec-042 / 043 / 044 / 050 / 051 surface and wrote the kanban DB. Recorded here rather than in a later pass's artifact, because the change is Worker 0's to attribute:

- `docs/SPECS/spec-042-debug_toolbar-0_0_14.md`
- `docs/SPECS/spec-043-test_client-0_0_14.md`
- `docs/SPECS/spec-044-debug_extension-0_0_14.md`
- `docs/SPECS/spec-050-debug_extraction-0_0_19.md`
- `docs/SPECS/spec-051-boundary_dry_squeeze-0_0_20.md`
- `examples/fakeshop/test_query/README.md`
- `examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html` — the DB write and its regenerates

That is **nine** paths (three of them the generated trio). Attribution is positive rather than inferred: pre-flight ran only read-only commands against the DB (`import_spec_terms --check`, the card / `SpecDoc` read), and this cycle's writable list contains no spec-042/043/044/050/051 path, no DB path, no KANBAN path, and no `examples/` path. **None of these files is one any residual item writes**, so every one of them stays out of scope for the whole cycle.

Two consequences that bind later passes:

- **The three generated docs are now concurrently dirty.** `## Concurrent-writable tracked binary / generated files` below said all four were clean at baseline; three of them no longer are. A `KANBAN.md` / `KANBAN.html` / `db.sqlite3` diff is now most likely the concurrent session's, so R3 **attributes semantically before concluding** — compare against a fresh regenerate and check which cards changed — and may not verify any DB-backed work of its own by "`git diff` is clean" (`BUILD.md` `### Tracked binary / generated files: churn and concurrent-writer handling`). If R3 writes the DB at all it applies its writes **on top** of the concurrent state without reverting, verifies by two-consecutive-regenerate byte-stability plus spot-checks, and hands the mixed diff to the maintainer. `docs/GLOSSARY.md` is still clean, so a diff there remains drift to investigate.
- **Baseline exception for the final test-run gate**, recorded here because `BUILD.md` `## Final test-run gate` requires it in the plan's preamble to be honoured: `uv run pytest --no-cov`, `uv run ruff format --check .`, `uv run ruff check .`, and `git diff --check` all read the whole tree, so they will see this churn. A failure attributable to a file this cycle never wrote does **not** block `final-accepted` and does **not** route back through a residual item's loop; it is reported to the maintainer. The gate still reports each command's real result — the exception governs what a result *blocks*, never whether it is recorded honestly.

If the list grows again mid-cycle, workers **report it and never revert it**, and Worker 0 appends it here rather than a worker editing the plan.

## Concurrent-writable tracked binary / generated files

Churn in these is not proof a worker caused it (`BUILD.md` `### Tracked binary / generated files: churn and concurrent-writer handling`). **Three of the four went dirty during pre-flight** — read `## Baseline-dirty out-of-scope files` above before treating any diff here as this cycle's:

- `examples/fakeshop/db.sqlite3` — **dirty from a concurrent session as of pre-flight.** **No residual item is expected to write it**: card 2 is already Done and its `SpecDoc.path` already points at the archived location (verified below). A write happens only if R3's audit finds real drift. Compare `iterdump()` semantics, never file bytes.
- `KANBAN.md`, `KANBAN.html` — **dirty from that same concurrent session.** Regenerated from that DB only if R3 writes it.
- `docs/GLOSSARY.md` — DB-rendered; **still clean at pre-flight**, and **no residual item is expected to change it.** A diff here means drift to investigate, not build output.

## Build-wide context flags

- **`0.0.2` shipped and the version quintet is at `0.0.14`.** No residual item touches `pyproject.toml`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, the GLOSSARY package-version line, or `uv.lock`.
- **No source or test file changes in this cycle.** Package source, `tests/`, and `examples/` code are read-only throughout. R3 may edit a docstring only if its audit finds a factually-false one, and that routes through Worker 2.
- **`CHANGELOG.md` is closed.** `AGENTS.md` rule 21 governs: no residual item edits it. A stale spec-002 path found there is reported to the maintainer, never edited. (Verified at pre-flight: `CHANGELOG.md` contains no `spec-002` reference at all.)
- **Sibling specs are read-only.** `spec-003`, `spec-004`, `spec-005`, and `spec-006` all reference spec-002, three of them by section title (see `### Inbound references that constrain a section retitle`). They belong to other cards. A pass that finds one made stale by an R2 edit records it as a deferred item for the maintainer / next spec author — it does not edit them.
- **The spec is already archived.** `BUILD.md` `### Spec stays at its working location` requires a move be plan-declared as a Worker-1-owned final-verification step. There is no move: `docs/SPECS/spec-002-optimizer-0_0_2.md` and `docs/SPECS/appx/spec-002-optimizer-0_0_2-terms.csv` are already at their archived paths, `SpecDoc.path` already reads `docs/SPECS/spec-002-optimizer-0_0_2.md`, and both `KANBAN.md` references already point there. **R1's new rationale file is therefore written directly to `docs/SPECS/appx/`** — the archived-companion location `AGENTS.md` rule 26 names — never to `docs/` first and moved after.
- **Only the maintainer commits.** No worker commits, and none creates or switches a branch.

## Worker-0-verified facts, passed into dispatch so no worker re-derives them

`worker-0.md` `## Closing out a kanban card` requires the live DB references be verified before a card/glossary edit is planned, because plan and spec text can carry stale ones. Read-only queries, run 2026-08-07:

- `Card.objects.get(number=2)` → `card_id` `DONE-002-0.0.2`, `status.key` `done`, `target_version.number` `0.0.2`, title `Optimizer O1-O6 foundation`. The card is **already Done**; no status flip is in scope, and the 2026-07-30 card renumber left 002 untouched (it rotated 045-068 only).
- `SpecDoc` for card 2 → name `spec-002-optimizer-0_0_2`, **`path` already `docs/SPECS/spec-002-optimizer-0_0_2.md`**. No repoint needed. (`SpecDoc.path` is the writable column; `SpecDoc.url` is a read-only `@property` deriving from it — assigning `url=` raises.)
- `card.glossary_links.count()` → 3, matching the 3 rows in the terms CSV: `djangooptimizerextension`, `djangotype`, `only-projection`.
- Sibling card 3 (`DONE-003-0.0.2`, `Optimizer O4 nested prefetch chains`) has its own `SpecDoc` at `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md`. **Card 3 and spec-003 are out of this cycle's scope** — they are a separate card with a separate closeout.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` → `OK: 49 done cards have glossary links.` Exit 0. **This is the baseline both R2 and R3 must not break.**
- Spec byte count before R1: **7,398 bytes** (`docs/SPECS/spec-002-optimizer-0_0_2.md`). Worker 1 reports the after-count in the R1 artifact.

### The 3-anchor constraint — the trap in this cycle

`docs/SPECS/appx/spec-002-optimizer-0_0_2-terms.csv` carries 3 anchors, and `check_spec_glossary.py` passes today because **each of the 3 has at least one link in the spec body**. Both R1 (which moves text out of the spec) and R2 (which rewrites text) can silently drop the last remaining link for an anchor. The failure is not cosmetic: `import_spec_terms` is what a DONE card's glossary-link set is rebuilt from, so a dropped anchor breaks the card-wrap chain for card 2.

Spec-002 is **far more fragile here than spec-001 was**. Spec-001 spread 21 anchors across 52KB; spec-002 has three anchors in 7.4KB, and each is currently carried by a *single* link:

| Anchor | Sole carrier in the spec today |
|---|---|
| `only-projection` | `## Purpose` — ``[`only()`][glossary-only-projection] projection`` |
| `djangotype` | `## Problem statement` — ``Reverse relations exposed by [`DjangoType`][glossary-djangotype]`` |
| `djangooptimizerextension` | `## Current state` — ``O3 — Root-gated optimizer hook in [`DjangoOptimizerExtension`][glossary-djangooptimizerextension]`` |

Two of the three sit in sections R1 and R2 are most likely to rewrite. **Every pass that writes the spec re-runs `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-002-optimizer-0_0_2.md` and quotes the result in its artifact.** A rewrite that drops an anchor keeps the anchor's link by re-siting it in the surviving contract prose — never by re-adding narration the item just removed, and never by editing the CSV.

### Inbound references that constrain a section retitle

`KANBAN.md:310` (card `TODO-ALPHA-052-0.1.0`, Beta release) already carries a deferral naming this exact spec:

> `docs/SPECS/spec-002-optimizer-0_0_2.md` carries four status-shaped sections: `## Current state`, `## Shipped slices`, `## Visibility status`, `## Open questions`. All four are accurate at HEAD today, so nothing is wrong now - the deferral is the standing-promise shape itself, which spec-001 retired by retitling `## Current state` to `## Prior art` on the reasoning that a section named for the present is a promise no shipped spec can keep. Nothing anywhere cites spec-002 by `#anchor`, so retitling breaks no link, but `spec-003-optimizer_nested_prefetch_chains-0_0_2.md` names those sections in prose.

That deferral is R2's inheritance, and this cycle is the natural place to discharge it. **Worker 0's verification found one constraint the card does not name**, so it is recorded here rather than left for a pass to rediscover: the "no `#anchor` citation" claim holds (verified — no `spec-002…#` fragment anywhere in the tree), but there are **two** prose-reference sites, not one:

| Site | Text | Effect of a retitle |
|---|---|---|
| `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md:333` | "Update `docs/SPECS/spec-002-optimizer-0_0_2.md` current state, visibility status, and checklist to mark O4 shipped." | A discharged "when O4 ships" instruction; goes stale in wording only |
| `docs/SPECS/spec-006-public_surface-0_0_3.md:136`, `:147` | "The optimizer-visibility decision specifically is amended into `spec-002-optimizer-0_0_2.md` **\"Visibility status\"** so the optimizer spec carries the local…" | A **live** cross-spec pointer naming the section by title |

Both files are read-only in this cycle (`## Build-wide context flags`). Whether that makes the retitle worth doing is Worker 1's call at R2; the alternatives it rejects belong in the rationale file.

### Verified spec-versus-HEAD drift — R2's input, verified by Worker 0 against source

Read at HEAD on 2026-08-07 with the symbol-qualified paths given. Each row is a claim the spec makes that HEAD complicates or falsifies. **A prescribed correction is not included: how the spec should read is Worker 1's call, and the alternatives it rejects belong in the rationale file.** Worker 1 re-verifies each row rather than trusting this table.

| # | Spec-002 claim | HEAD reality | Later spec that moved it |
|---|---|---|---|
| D1 | O1: "`DjangoType.__init_subclass__` attaches one resolver per relation field" | attachment moved to finalization **Phase 2** — `types/finalizer.py::finalize_django_types` calls `types/resolvers.py::_attach_relation_resolvers`. `__init_subclass__` still stamps the `_is_default_get_queryset` sentinel (`types/base.py::DjangoType.__init_subclass__`), so the spec's O6/coordination sentence about the sentinel is **still correct** — only the resolver attachment moved | spec-008 |
| D2 | O1: "Reverse FK / M2M resolvers return `list(manager.all())` when needed" | `types/resolvers.py` returns `list(bounded_rows(getattr(root, accessor_name).all(), info))` — the many-side list is **row-bounded by the request resource policy**, and a prefetch-cache fast path returns the cached list without the queryset clone or the `list(...)` copy | spec-047; the fast path is later optimizer work |
| D3 | `## Open questions`: "Custom resolver opt-out: consumers should eventually be able to override generated relation resolvers … The generated resolver should only fire when no consumer-declared resolver exists" | **shipped** — `_attach_relation_resolvers(..., skip_field_names=definition.consumer_assigned_relation_fields)`; the file/image twin `_attach_file_resolvers` takes the broader `consumer_authored_fields` | spec-019, spec-037 |
| D4 | O2: `plan_optimizations(selected_fields, model, info=None)` | signature adds two keyword-only parameters, `runtime_prefixes` (a tuple of runtime-path tuples) and `source_type` (the resolver's actual Strawberry return type), both defaulting to `None` | spec-003 (runtime paths), spec-033 |
| D5 | O2: "maps Django relation fields through `_optimizer_field_map`" | no `_optimizer_field_map` symbol exists in the package (the name survives only in three `tests/optimizer/test_field_meta.py` test *names*); HEAD reads `DjangoTypeDefinition.field_map: dict[str, FieldMeta]` via `optimizer/walker.py::_resolve_field_map` | spec-016 |
| D6 | O2 "produces an `OptimizationPlan`" (the family describes five bags: `select_related`, `prefetch_related`, `only_fields`, `fk_id_elisions`, `cacheable`) | `optimizer/plans.py::OptimizationPlan` additionally carries `planned_resolver_keys`, `select_path_resolver_keys`, and three `finalized_*` metadata fields, plus a `finalize()` immutability contract (directive fields become tuples, metadata frozensets) that makes post-handoff mutation raise | spec-003, spec-035 |
| D7 | O3: "root optimizer plans are stashed on context for introspection" | still true, and now a named vocabulary: `optimizer/_context.py` defines five `DST_OPTIMIZER_*` keys and `clear_optimizer_context` for the start-of-execution reset (retaining `DST_OPTIMIZER_PLANNED` across executions masks real N+1s) | spec-004 B5, later hardening |
| D8 | O3: "Non-root resolvers and non-`QuerySet` values pass through unchanged" | two further pass-throughs the spec does not state: a `Manager` is **coerced** via `utils/querysets.py::normalize_query_source` rather than passed through, and an **already-evaluated** queryset (`_result_cache is not None`) is returned unchanged so the clone cannot silently re-execute the consumer's SQL | spec-035 G1 |
| D9 | O5: "`OptimizationPlan.apply()` calls `QuerySet.only()` when the plan carries projected fields" | still true at `optimizer/plans.py::OptimizationPlan.apply`, but `.only()` is applied for **`QUERY` operations only** — a mutation / subscription queryset keeps `select_related` / `prefetch_related` and carries no column deferral | spec-035 G2 |
| D10 | O6: "the planner … emits a `Prefetch` with the target queryset instead" | the target `get_queryset` is no longer invoked directly by the planner: every framework-owned invocation runs through the sealed-execution visibility boundary (`utils/querysets.py::apply_type_visibility_sync` / `_async`), which validates and rebuilds a framework-owned queryset before the plan composes over it | spec-045 |
| D11 | `## Architecture decision`: "The optimizer runs from Strawberry's `SchemaExtension.resolve` hook" | `resolve` is no longer the only entry point into plan application: `DjangoOptimizerExtension` also defines `on_execute`, and `DjangoConnectionField`'s `apply_connection_optimization` calls the shared `apply_to` tail directly (one plan-application implementation, two callers) | spec-030 / spec-033, spec-035 Decision 11 |
| D12 | `## Shipped slices` O4: "The walker descends across queryset boundaries and emits nested `Prefetch` objects with optimized child querysets" | still true for plain relations; a nested **Relay connection** selection is delegated to `optimizer/nested_planner.py` and fetched through a pluggable `NestedConnectionStrategy` seam (`optimizer/nested_fetch.py`, `lateral_fetch.py`, `single_parent_fetch.py`) | spec-033, later |
| D13 | `## Open questions`: "`only()` opt-out per consumer field: strawberry-graphql-django ships `disable_optimization=True` … A similar flag should be considered in a future optimizer-control spec" | **answered and shipped** — `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md:128` names `Meta.optimizer_hints` as "the DRF-shaped analog of strawberry-graphql-django's `disable_optimization=True` per-field marker, but richer"; `OptimizerHint` is shipped at `0.0.3` per `docs/GLOSSARY.md` | spec-004 B4 |
| D14 | `## Current state` / `## Shipped slices` / `## Visibility status` / `## Open questions` — four status-shaped sections | accurate at HEAD, but the standing-promise **shape** is what card 052 defers; see `### Inbound references that constrain a section retitle` for the two prose sites a retitle touches | card `TODO-ALPHA-052-0.1.0` |
| D15 | `## References`: the four upstream pointers | unverified by Worker 0 — the two URLs and the two source paths (`graphene_django/converter.py::convert_django_field`, `strawberry_django/optimizer.py`) are R2's to confirm against the checkouts `AGENTS.md` line 2 names | — |

Two things the drift table deliberately does **not** say. First, that every row must change the spec: some rows are the spec being *superseded* rather than *wrong*, and the spec-003 / spec-004 family already owns much of the optimizer's later surface by spec-002's own declaration — Worker 1 decides per row whether the contract is restated, pointed elsewhere, or dropped to the rationale. Second, that the list is exhaustive; it is Worker 0's verified floor, and R2 owns the full sweep.

**The scope trap specific to this spec.** Spec-002 is the *parent* of an optimizer family: spec-003 (nested prefetch chains), spec-004 (beyond slices), spec-033 (connection optimizer), spec-035 (optimizer hardening). Reconciling it must not turn it into a summary of all four. The spec's own text already draws the line ("This parent spec only records the shipped behavior at a high level"), and D6/D10/D11/D12 are exactly the rows where the pull toward over-absorbing is strongest.

### Every reference TO spec-002 (verified by grep, 2026-08-07)

The archive already landed, so this table is R3's **verification** list, not a rewrite list. Every entry already reads correctly; R3 confirms and reports, and only edits if one is wrong.

| Location | Current text | Status |
|---|---|---|
| `KANBAN.md:145`, `:4855` (+ 6 hits in `KANBAN.html`) | `docs/SPECS/spec-002-optimizer-0_0_2.md` | **Generated** — already correct; never hand-edit |
| `KANBAN.md:310` | card 052's status-section deferral | Generated; the prose is `CardItem.text`. See `### Inbound references that constrain a section retitle` |
| `KANBAN.md:2556` | `our O3 root gate (`info.path.prev is None`, spec-002)` | Generated; accurate at HEAD |
| `docs/SPECS/spec-003-…:4`, `:27`, `:45`, `:333` | `docs/SPECS/spec-002-optimizer-0_0_2.md` + prose | Read-only sibling |
| `docs/SPECS/spec-004-…:5` | bare-filename code span | Read-only sibling |
| `docs/SPECS/spec-005-…:5`, `:27`, `:107`, `:111`, `:123` | bare-filename code spans + one `docs/SPECS/` path | Read-only sibling; `:27` names the `__init_subclass__` sentinel, which D1 confirms is still accurate |
| `docs/SPECS/spec-006-…:134`, `:136`, `:147` | bare-filename code spans; `:136`/`:147` name the "Visibility status" section | Read-only sibling; the retitle constraint |
| `docs/SPECS/spec-033-…:695`, `spec-035-…:82`, `:506` | reference-style def `[spec-002]: spec-002-optimizer-0_0_2.md` | Sibling in the same directory — correct as a bare filename |
| `docs/SPECS/spec-001-…:337`, `:414`, `:418`, `:432` | prose handing the optimizer slices to this family | Correct after the spec-001 cycle |
| `docs/SPECS/appx/spec-001-…-rationale.md` (21 hits) | the spec-001 rationale's account of the optimizer extraction | Read-only; R1 must not duplicate its content |

No hit in `CHANGELOG.md`, `README.md`, `GOAL.md`, `TODAY.md`, `AGENTS.md`, `docs/GLOSSARY.md`, `docs/TREE.md`, or `docs/README.md`. The `docs/builder/bld-001-*` and `build-001-*` hits are the prior cycle's artifacts, correctly historical. The sweep is re-run by R3, not trusted from this table.

**The direction this table cannot show** is the one inside the new file: R1's rationale lands at `docs/SPECS/appx/`, two levels below `docs/`, so its link definitions need `../../GLOSSARY.md` for a `docs/` target and `../spec-NNN-….md` for a `docs/SPECS/` sibling. The archived siblings (`docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md`) show the shape.

**Staged-anchor sweep, run at pre-flight:** `grep -rEn 'TODO\(spec-002|TODO-(ALPHA|BETA|STABLE)-002' .` → no match. `BUILD.md` `## Cross-slice integration pass` step 6 is therefore already discharged at baseline; R3 re-runs it as its backstop.

## Artifact list

- `docs/builder/bld-002-r1-rationale_move.md`
- `docs/builder/bld-002-r2-spec_reconciliation.md`
- `docs/builder/bld-002-r3-doc_completion_archive.md`
- `docs/builder/bld-002-final.md`

No `bld-integration.md`-equivalent: a cross-slice integration pass exists to find duplication across slices that landed source, and this cycle lands none. Its live obligations are folded in — the staged-anchor sweep (`BUILD.md` `## Cross-slice integration pass` step 6) runs in R3, and the cross-artifact read runs in the final gate. Naming one `bld-integration.md` would also collide with the preserved spec-046 artifact.

## Checklist

- [x] R1: Spec rationale extraction into `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` (Worker 1 performs the move; Worker 3 audits it; Worker 1 final-verifies) -> `docs/builder/bld-002-r1-rationale_move.md`
- [x] R2: Reconcile the spec with HEAD — every claim the package falsifies is restated as the contract that actually holds, or handed to the spec that now owns it; the explanation of each change lands in the rationale, never in the spec -> `docs/builder/bld-002-r2-spec_reconciliation.md`
- [x] R3: Finish the documentation and audit the archive — durable-doc audit of the spec-002 optimizer surface, the three-direction cross-reference sweep, `SpecDoc.path` / terms-CSV verification, and the `TODO(spec-002` / `TODO-ALPHA-002` staged-anchor sweep -> `docs/builder/bld-002-r3-doc_completion_archive.md`
- [x] Final test-run gate -> `docs/builder/bld-002-final.md`

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
