# Package build plan: foundation / 0.0.4 (010) — residual-completion cycle

Spec source: `docs/SPECS/spec-010-foundation-0_0_4.md` (already archived; card `DONE-010-0.0.4`)
Rationale companion: `docs/SPECS/appx/spec-010-foundation-0_0_4-rationale.md` (exists; **partial** — see `## Why this cycle exists`)
Target release: `0.0.4` (shipped; this cycle bumps no version and lands no feature)
Build rule: one item at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every item must justify shared/duplicated patterns before merging.
Ownership partition: none; sequential items. R1 and R3 both write the spec file, so they could not run concurrently even if the rest were disjoint.
Hot-path declaration: none. R1 and R3 write Markdown only; R2 adds one test and no package source.
Floor-verification scope: **R2 only.** A cross-module `Annotated[..., strawberry.lazy("module.path")]` relation override is resolved by Strawberry at schema-construction time, which is the "schema and type construction against Strawberry internals" seam in `docs/builder/BUILD.md` `### When it is required`. R2's builder pass owns the run (`tests/types/test_definition_order.py` focused, in an isolated floor venv); the final gate is the backstop that confirms it happened, not a second owner. R1 and R3 declare `none`.
Pre-flight: passed on 2026-08-15 with two recorded deviations (steps 1 and 3, below); baseline: **dirty with a concurrent session's work — 47 paths, none of them this cycle's**; cleanup: `docs/shadow/`, `docs/builder/temp-tests/`, `docs/builder/worker-memory/` cleared and the four memory files re-seeded empty; **no `bld-*.md` deleted** (deviation, below).

## Why this cycle exists

The maintainer's instruction is narrower than a build and wider than a doc pass. Spec-010 shipped at `0.0.4` and its card is `DONE`, so the code is not in question as *new* work. What is in question is whether the shipped code still matches the contract the spec states, and whether the spec still states a contract that is true.

Three obligations, in the maintainer's own framing:

1. **Nothing was skipped in the code.** Every item spec-010 promised must be present at `HEAD`, and any it promised and never delivered is a defect this cycle fixes.
2. **Later work that changed the shipped shape is legitimate — but the spec must say so.** Where a later spec corrected, generalized, or optimized something spec-010 owns, the spec is rewritten to state the **current** contract directly. It never narrates the change (`docs/builder/BUILD.md` `## Spec rationale extraction`).
3. **The explanation goes in the rationale, not the spec.** What changed, why, which spec caused it, and what was rejected — all of it lands in `docs/SPECS/appx/spec-010-foundation-0_0_4-rationale.md`, keyed to the spec section it belongs to.

The rationale file already exists but discharges only obligation 3 for one earlier pass: a citation-convention cleanup that retired `## Note on source line references` and repointed two mis-aimed spec-009 citations. It carries **no** entry for any of the contract divergences this cycle's verification found. That is the gap the maintainer named as "the `-rationale.md` was not done".

## Worker-0 verification pass (performed before any dispatch)

`docs/builder/BUILD.md` `### Worker 0 verifies every finding against source before dispatching`. Every finding below was read against `HEAD` source before this plan was written; each cites its symbol-qualified path (`AGENTS.md` rule 27). A finding is dispatched only if it holds.

### Every "What ships" item landed — verified, not assumed

Spec-010 `## What ships` promises six things and only six. All six are present at `HEAD`:

| # | Promised | At `HEAD` | Evidence |
|---|---|---|---|
| 1 | package-owned type-definition object | present | `django_strawberry_framework/types/definition.py::DjangoTypeDefinition`, stashed as `cls.__django_strawberry_definition__` by `types/base.py::DjangoType.__init_subclass__` |
| 2 | pending-relation registry | present | `types/relations.py::PendingRelation` + `registry.py::TypeRegistry.add_pending_relation` / `::iter_pending_relations` / `::discard_pending` |
| 3 | finalization lifecycle | present | `types/finalizer.py::finalize_django_types`, exported from the package root and from `django_strawberry_framework.types` |
| 4 | cyclic relation tests (FK / reverse FK / OneToOne / reverse OneToOne / M2M) | present | `tests/types/test_definition_order.py` — the five cardinality tests plus `::test_multi_cycle_finalizes_every_edge` |
| 5 | fail-loud unresolved-target error naming source model, source field, target model | present | `types/finalizer.py::_format_unresolved_targets_error` — **the message is the spec's canonical wording verbatim**, and `tests/types/test_definition_order.py::test_unresolved_target_raises_with_source_field_and_target` pins it |
| 6 | optimizer still sees concrete relation metadata, no regression to the three named symbols | present | `optimizer/walker.py::plan_relation`, `optimizer/walker.py::_plan_prefetch_relation`, `optimizer/extension.py::DjangoOptimizerExtension.check_schema` all live; `tests/optimizer/test_definition_order.py` pins all three |

The spec's seven `## Invariants this slice must protect` are likewise all live, and the registry lifecycle contracts it names are pinned individually in `tests/test_registry.py` (idempotency, the post-finalization registration guard, `clear()` reset, phase-1 atomicity, phase-2/3 partial-mutation limits, pending-set cleanup, class-mutation residue).

**No source defect was found, and no source file is in any item's writable set.** That is why Worker 2 is dispatched exactly once, for a test.

### R1 findings — spec claims that later work falsified

Each is a spec statement that was true at `0.0.4` and is false at `HEAD`. None is a code defect; every one is a later spec's deliberate change that spec-010's text never absorbed.

| # | Spec claim | `HEAD` reality | Cause |
|---|---|---|---|
| F1 | collection resolves a relation immediately when its target is registered, and defers only an unknown target (`### Collection phase` step 8) | **every** auto-synthesized relation defers unconditionally — `types/base.py::_build_annotations` #"Always defer auto-synthesized relation annotations" | spec-018 closed the import-order trap where an eager bind froze the relation onto whichever type happened to be registered first |
| F2 | `Meta.primary` does not ship; "the current registry hard-fails on duplicate models, and that stays" (`## What does not ship`), and `_types` is `dict[model, type]` (`### TypeRegistry extensions`) | ships — `registry.py::TypeRegistry.register` takes `primary=`, `_types` is `dict[model, list[type]]`, and `::primary_for` / `::types_for` / `::models_with_multiple_types` exist | spec-018 |
| F3 | `cls._optimizer_field_map` / `cls._optimizer_hints` are mirrored as class attributes for one minor version (`### Collection phase` step 13; `### Should redo now`) | both mirrors are **gone** — zero occurrences package-wide; the walker reads `optimizer/walker.py::_resolve_field_map` / `::_resolve_optimizer_hints` off the definition | the promised removal happened |
| F4 | `cls._is_default_get_queryset` is the third such mirror, "removed in the next minor" | **survives and was repurposed** — `types/base.py::DjangoType` declares it `ClassVar` and `::__init_subclass__` stamps it *before* the `meta is None` early-return so an abstract base without `Meta` still propagates the flag; `::has_custom_get_queryset` prefers the definition and falls back to it | the MRO-propagation requirement the spec itself states needs a pre-`Meta` carrier |
| F5 | scalar manual override is "not pinned in this slice"; the definition carries three `consumer_*` sets | four-corner contract (relation x scalar by annotation x assignment) plus an `auto` fifth corner — `types/base.py::_consumer_assigned_fields`; the definition carries `consumer_annotated_scalar_fields` and `consumer_assigned_scalar_fields` too | spec-019 |
| F6 | detection rule: consumer-authored if the class-dict value "is not a Django manager/descriptor" (`### Manual annotation contract` detection rule) | hardened — the value must be a `StrawberryField`; any other shadow of a selected Django field name raises `ConfigurationError` (`types/base.py::_consumer_assigned_fields` #"shadows a Django") | spec-019 |
| F7 | forward-reserved slots are `filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`, `search_fields`, `interfaces`, all unused | `aggregate_class` and `search_fields` never landed on the dataclass at all; `interfaces` / `filterset_class` / `orderset_class` are live; only `fields_class` is still reserved. The dataclass additionally carries `primary`, `connection`, `cursor_field`, `relation_shapes`, `relation_connections`, `globalid_strategy`, `effective_globalid_strategy`, and two memoization caches | specs 015 / 018 / 027 / 028 / 030 / 031 / 032 / 033 |
| F8 | collection calls `registry.register(...)` then `registry.register_definition(...)` (`### Collection phase` step 10) | one atomic call with rollback — `registry.py::TypeRegistry.register_with_definition` | later hardening |
| F9 | the post-finalization guard lives only in `__init_subclass__` | a second, defense-in-depth guard sits at the registry boundary — `registry.py::TypeRegistry._check_mutable`; `::clear` additionally runs registered type teardowns and resets `_primaries` / `_type_teardowns` / `_globalid_setting_snapshot` | later hardening |
| F10 | `resolved_relation_annotation(django_field, target_type)` | takes `field_meta=` as well, read from `definition.field_map[snake_case(...)]` in the phase-1 loop | later refactor |
| F11 | phase 2 attaches relation resolvers only | phase 2 also attaches file/image resolvers (`types/resolvers.py::_attach_file_resolvers`, with the broader `consumer_authored_fields` skip set); collection additionally calls `install_is_type_of` | spec-037 / spec-015 |
| F12 | phase 1 is the failure-atomic boundary | still true for class objects, but a `RELAY_GLOBALID_STRATEGY` snapshot now runs *before* phase 1, can raise, and writes `registry._globalid_setting_snapshot` — registry state, not a class object | spec-031 |
| F13 | end-to-end tests live at `examples/fakeshop/tests/test_schema.py`, and `tests/types/test_definition_order_schema.py` proves in-process schema execution | that fakeshop path does not exist — the tests are at `examples/fakeshop/apps/library/tests/test_schema.py`; `tests/types/test_definition_order_schema.py` now holds only the sentinel-repr test | the `AGENTS.md` per-app test-placement rule |
| F14 | phase-10 doc list names `docs/FEATURES.md`, and puts the wrong-order example in root `README.md` | `docs/FEATURES.md` does not exist (its role is `docs/GLOSSARY.md`); the wrong-order example lives in `docs/README.md` | doc restructure |
| F15 | phase 1's consumer-authored branch is a live classification arm | defense-in-depth only — `_build_annotations` never appends a pending record for a consumer-authored name, so the arm is unreachable under the documented call graph; `types/finalizer.py::finalize_django_types` says so in place | F1's consequence |

### R2 finding — the one code gap

| # | Finding | Evidence | Severity |
|---|---|---|---|
| F16 | Spec-010 `### Manual annotation contract for relation fields` states "Tests cover all four shapes" and lists the cross-module `Annotated[..., strawberry.lazy("...")]` relation override as one of them. **No test anywhere exercises that shape on a `DjangoType` relation field.** `docs/GLOSSARY.md#definition-order-independence` makes the same shipped claim under "Supported forward-reference / manual relation shapes". | `grep -rn "strawberry.lazy" tests/types/ tests/optimizer/ examples/fakeshop/apps/*/schema.py` returns no `DjangoType` relation override — every hit is a filters / orders / auth / mutations input-factory concern. Two of the other three shapes are covered: `tests/types/test_definition_order.py::test_annotation_only_relation_override_keeps_generated_resolver` (annotation-only) and `::test_assigned_relation_field_override_keeps_consumer_resolver` (the `@strawberry.field` decorator form). **See F20 — the fourth is not.** | **Medium** — a shipped contract asserted in two consumer-facing documents with nothing pinning it. The mechanism plausibly works (an `Annotated` annotation routes through `consumer_annotated_relation_fields` exactly as a plain one does), but "plausibly works" is what a test exists to replace. |

### R2b finding — a second uncovered shape, found by R2's final verification

This row was **wrong in the F16 row above when this plan was written**, and the correction is recorded rather than quietly applied. The original text asserted the `strawberry.field(resolver=...)` *assignment* form was covered "alongside" the decorator form. It is not, and the assertion was never measured — it was inferred from the decorator test's name. `docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose` is exactly about this: a claim that reads as measured is treated as measured by every later pass.

| # | Finding | Evidence | Severity |
|---|---|---|---|
| F20 | Spec-010 lists **four** override shapes as tested. R2 closed the `strawberry.lazy` one, leaving three of four covered. The fourth — an explicit `= strawberry.field(resolver=...)` **assignment** on a relation field, which the spec lists as distinct from the `@strawberry.field` decorator form — is still unpinned, so "Tests cover all four shapes" remains false. | `grep -ro "= strawberry.field(resolver=" tests/ examples/ \| wc -l` -> **16 occurrences**, and not one is a relation field on a `DjangoType`: they are scalar overrides, `id`-rejection cases, `Query`-type fields, and non-`DjangoType` probes. Independently reached by R2's final-verification pass and re-derived by Worker 0 before this row was written. | **Medium** — same class as F16: a spec sentence claiming coverage that does not exist. Distinct code path from the decorator form at the collection seam, since `types/base.py::_consumer_assigned_fields` classifies on the class-dict value being a `StrawberryField` and the two forms reach that check differently. |

**Why this earns an item rather than a deferral.** The cycle exists to make the spec true. Leaving F20 open would close the cycle with the same sentence still overclaiming — the precise defect the cycle was chartered against — for the cost of one test row in a file R2 has already opened.

**The prescribed remediation is a hypothesis, not an instruction.** If R2's builder finds the shape does *not* work, that is a source finding and this plan is re-partitioned rather than the test weakened to match.

### R3 findings — the archive is not clean

Spec-010 was moved to `docs/SPECS/` by an earlier `docs/SPECS/NEXT.md` Step 8 sweep that did not re-relativize its links.

| # | Finding | Evidence |
|---|---|---|
| F17 | three inline links are **broken** at the archived depth | from `docs/SPECS/`: `../GOAL.md`, `../TODAY.md`, and `TREE.md` all resolve to nothing. Correct targets are `../../GOAL.md`, `../../TODAY.md`, `../TREE.md` |
| F18 | one inline link is **masked** rot | `../README.md` resolves — to `docs/README.md`, not the root `README.md` its label ("Operational entry point, install/test/build") names. This is the same-named-file-one-level-up trap; a link checker cannot see it and only intent can settle it |
| F19 | eight inline cross-file links violate the reference-style convention | `AGENTS.md` rule 28 / `START.md` "Markdown link convention". Spec-010 is the repo's worst offender among archived specs: a sweep of `docs/SPECS/spec-0*.md` finds inline cross-file `.md` links in only three files — spec-010 (8), spec-025 (2), spec-009 (1) |

## Baseline-dirty out-of-scope files

`HEAD` at plan time: `054de9dd37a2c4181fb2a91ded57f4823a1b5220`. `git status --porcelain | wc -l` -> **47**, and **not one of them is this cycle's**. Every path below belongs to a concurrent maintainer session (`START.md` `## Concurrent sessions`, `AGENTS.md` rule 34). **No worker edits, reverts, stages, or `git checkout`s any of them.**

- 14 modified package sources: `_boundary_ordering.py`, `_cross_web_patches.py`, `_request_body.py`, `conf.py`, `connection.py`, `consumers.py`, `extensions/error_policy.py`, `extensions/resource_policy.py`, `forms/resolvers.py`, `list_field.py`, `middleware/request_body.py`, `permissions.py`, `relay.py`, `resource_policy.py`
- 10 modified tests: `tests/base/test_conf.py`, `tests/forms/test_resolvers.py`, `tests/test_connection.py`, `tests/test_error_policy.py`, `tests/test_list_field.py`, `tests/test_permissions.py`, `tests/test_relay_node_field.py`, `tests/test_resource_policy.py`, `tests/test_routers.py`, `tests/test_views.py`, plus `examples/fakeshop/test_query/test_transport_api.py`
- 8 modified + 13 untracked per-cycle scratchpads under `docs/review/` and `docs/dry/` — a `0.0.14` review cycle in flight. `AGENTS.md` rule 22 forbids touching `docs/review/` regardless
- **`?? docs/builder/build-009-rich_schema_architecture-0_0_4.md`** — see the live risk below

**The list is moving.** Four paths (`forms/resolvers.py`, `tests/forms/test_resolvers.py`, and two `docs/dry/` files) appeared between two `git status` runs minutes apart during this pre-flight. Any pass that needs the baseline re-derives it rather than quoting this section. It reached **141+** by R3.

### Baseline exception for the final test-run gate

`docs/builder/BUILD.md` `## Final test-run gate`: a gate failure blocks `final-accepted` **unless a baseline exception was recorded in the plan's preamble**. One is recorded here, and it is deliberately narrow.

**A gate command's failure does not block `final-accepted` when the failure is attributable to a baseline-dirty path this cycle never wrote.** The cycle's entire diff is four Markdown files and two test paths under `tests/types/`; it lands **no package source**, which is what makes such an attribution decidable rather than a guess.

The exception is already live on one known instance. Worker 3's independent full sweep during R2 returned `5681 passed / 1 failed`, the failure being `tests/rest_framework/test_inputs.py::test_dedupe_serializer_input_shape_is_sole_cache_protocol`. R2's final verification established mechanically that **the node does not exist at `HEAD`** — `git show HEAD:` into a scratch path outside the repo returns 0 occurrences against 1 in the working copy — so it is the concurrent session's in-flight row, not a regression this cycle could have caused.

Three limits on the exception, so it cannot be used to wave a real failure through:

- **It excuses nothing this cycle wrote.** A failure in `tests/types/test_definition_order.py`, in `tests/types/fixtures/lazy_relation_target_module.py`, or in anything under `django_strawberry_framework/` blocks the gate outright.
- **Attribution is proven, never assumed.** The gate records the failing node id, whether the file is in this cycle's diff, whether it is baseline-dirty, and the read-only `git show HEAD:` evidence — per `docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`, which also states that a failing test's pre-existing-at-`HEAD` status is **not worker-verifiable** on a tree this dirty. Recording plus escalating to the maintainer discharges the obligation; silently passing over it does not.
- **It governs what a result blocks, never whether it is reported honestly.** Every gate command's real output is recorded whatever it says.

### Live risk: a concurrent session is reconciling spec-009

`docs/builder/build-009-rich_schema_architecture-0_0_4.md` is untracked at plan time, which means **another session is running this same residual-completion cycle against spec-009 right now**. Spec-010 cites spec-009 twice, by heading anchor, and treats it as the source of two requirements:

- `## Strawberry finalization strategy` cites `spec-009 #"### Layer 3: Finalization trigger"`
- `### Unresolved-target error format` cites `spec-009 #"### Decision 6: fail loudly"`

Consequences, binding on every pass of this cycle:

- **No worker opens `docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md`, for reading-as-authority or for writing.** It is out of scope in both directions.
- R1 **verifies both anchors still resolve** at the moment it edits, and if one has moved under the other session, records the divergence for the maintainer instead of repointing it. Repointing a citation at a target another session is actively rewriting is how two sessions produce two half-corrections.
- The reciprocal case is theirs to handle; this plan does not reach into it.

## Pre-flight deviations, recorded

Two steps of `worker-0.md` `## Pre-flight procedure` did not run as written.

- **Step 1 (working-tree baseline).** The procedure says stop and ask the maintainer to commit, move aside, or include unrelated changes in the baseline. The maintainer dispatched this cycle onto this tree knowingly and concurrent sessions are this repo's normal state, so the third disposition applies: the 47 paths are **included in the baseline** and enumerated above. No worker touches them.
- **Step 3 (artifact reset).** The procedure deletes prior-cycle `build-*.md` and `bld-*.md`. **Nothing was deleted.** `docs/builder/bld-003-final.md` is the committed record of the closed spec-003 residual cycle (landed at `20a9752f`, whose message is `docs(spec-003): reconcile the O4 spec with HEAD and extract its rationale`), and `docs/builder/build-009-...md` is a concurrent session's live plan. Deleting a prior cycle's record is the one irreversible pre-flight mistake that step names; deleting a concurrent session's live plan would be worse. What the step actually protects — that this cycle does not overwrite an existing path — was verified directly: all five paths in `## Artifact list` were confirmed absent before this plan was written.

Steps 2, 4, 5, and 6 ran clean: `scripts/review_inspect.py` smoke-invoked OK; `.gitignore` carries all three scratch paths; `docs/shadow/`, `docs/builder/temp-tests/`, and `docs/builder/worker-memory/` were cleared and the four memory files re-seeded empty; and `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-010-foundation-0_0_4.md` exits 0 (`OK: 12 terms`).

Step 7 (rationale extraction) is **partially** discharged by the existing companion and is this cycle's R1 obligation to complete — that is `## Why this cycle exists`.

## Artifact list

- `docs/builder/bld-010-r1-spec_reconciliation.md`
- `docs/builder/bld-010-r2-lazy_override_coverage.md`
- `docs/builder/bld-010-r2b-assigned_override_coverage.md` (added mid-cycle; see `### R2b finding`)
- `docs/builder/bld-010-r3-doc_completion_archive.md`
- `docs/builder/bld-010-final.md`

**No `bld-integration.md`.** `docs/builder/BUILD.md` `## Cross-slice integration pass` scans for cross-slice duplication in landed source; this cycle lands one test file's worth of source and nothing else, so there is no cross-slice DRY surface. Both of the pass's live obligations are folded into the final gate and recorded there: the staged-anchor sweep, and the read of every closed artifact. Same disposition, and the same reason, as the spec-003 cycle.

## Checklist

- [x] R1: spec reconciliation — rewrite every falsified claim (F1-F15) to state the current contract, and key a rationale entry to each -> `docs/builder/bld-010-r1-spec_reconciliation.md`
- [x] R2: close the untested `strawberry.lazy` relation-override claim (F16) -> `docs/builder/bld-010-r2-lazy_override_coverage.md`
- [x] R2b: close the untested `strawberry.field(resolver=...)` relation-assignment claim (F20) -> `docs/builder/bld-010-r2b-assigned_override_coverage.md`
- [x] R3: documentation completion and archive audit (F17-F19) -> `docs/builder/bld-010-r3-doc_completion_archive.md`
- [x] Final test-run gate -> `docs/builder/bld-010-final.md`

## Dispatch record

| Item | Passes dispatched | Why |
|---|---|---|
| R1 | Worker 1 only | The maintainer's standing instruction for this cycle: an item that changes only the spec and its rationale is Worker 1's alone, and both files are Worker 1-owned by `docs/builder/BUILD.md` `## Spec reconciliation` in any case. |
| R2 | Worker 1 -> Worker 2 -> Worker 3 -> Worker 1 | It lands a test. `### Isolation is non-waivable`: the agent that writes it never approves it. |
| R2b | Worker 1 -> Worker 2 -> Worker 3 -> Worker 1 | Same reason. One test row is not a licence to inline a worker's job (`docs/builder/worker-0.md` `## Scope`), and the pass that writes it is barred from approving it however small it is. |
| R3 | Worker 1 only unless it turns up a durable-doc or DB edit | Its findings are all inside the spec file. If the pass finds a `docs/GLOSSARY.md` or kanban-DB edit is owed, it stops and Worker 0 re-partitions with a Worker 2 pass, because those are generated from `examples/fakeshop/db.sqlite3` and are never hand-edited. |
| Final | Worker 1 only | `worker-1.md` `## Final test-run gate` gives the whole gate to Worker 1. |

## Cycle outcome

Closed and committed. Four commits: `7c29f8e6` (spec + rationale), `892c4173` (the two coverage rows, the fixture, and the tracked-path constants regenerate), `9f968e86` (the cycle's artifacts), and `c2b8622d` (a comment attribution correction in `types/finalizer.py`, left dirty by a concurrent session and adjudicated here — the symbol it credited, `registry.py::_clear_if_loaded`, greps zero in the package; `loaded_attr` is owned by `utils/imports.py`). The board half — two scope bullets added to `TODO-BETA-068` and two rewritten on `TODO-ALPHA-052` — was swept into a concurrent session's `e324b187`, whose message names spec-011 while its content is entirely this cycle's routing.

**R2b's on-disk failability proof, run after its target went clean.** The proof deferred at the gate is discharged, and its result matches all three in-process measurements: mutating `types/finalizer.py::finalize_django_types #"skip_field_names=definition.consumer_assigned_relation_fields"` to `frozenset()` fails **2 rows, 0 collection errors**, over `tests/types/test_definition_order.py` — `::test_assigned_relation_field_override_keeps_consumer_resolver` and `::test_assigned_relation_field_resolver_kwarg_override_keeps_consumer_resolver`. Pre-mutation baseline 46 passed / 0 pre-existing failures; restore proved by `filecmp.cmp(shallow=False)` plus SHA-256. Inside Worker 3's mandatory re-run floor, so the boundary is pinned rather than weakly pinned.

Three notes survive the cycle's artifacts, and are recorded here because nothing else carries them.

- **`KANBAN.md`'s `DONE-010-0.0.4` reserved-slot list is correct as history — do not "fix" it.** The card body names `aggregate_class` and `search_fields` among `DjangoTypeDefinition`'s forward-reserved slots. At `HEAD` neither is a slot: both are rejected `Meta` keys with no dataclass field, and only `fields_class` is reserved-and-unused. The card is nonetheless accurate about what `0.0.4` shipped — `git log -S` over `types/definition.py` shows the pair introduced by the foundation slice at `27d62919` and removed at `f83bb71b`, after the release. `KANBAN.md` renders from `examples/fakeshop/db.sqlite3` and is never hand-edited, so a "correction" here is a DB write plus a re-render that would make the record false.
- **The spike record's `README.md` pointer is deliberately unfixed.** `## Pre-implementation spikes` says a Phase-0 conclusion was written into `README.md`; at `HEAD` that material lives in `docs/README.md`. R1 corrected the two sentences that state a *current* documentation location and left the spike record alone as an account of what a spike concluded and where it was recorded *at the time* — the same correct-as-history class the board has ruled for twice. Reopen it only as a deliberate decision to make the spike record present-tense, never as a passing sweep.
- **A committed test fails on `main`, outside this cycle.** `tests/rest_framework/test_inputs.py::test_dedupe_serializer_input_shape_is_sole_cache_protocol` fails at `assert shape_a == shape_b` on `serializer_class`: two function-local `ItemSer` classes share a qualname, so a second build of what the test calls an identical descriptor produces a different class object. At the final gate this was in-flight work absent from `HEAD`, which is why the gate's baseline exception covered it. It is no longer: both the test and `rest_framework/inputs.py` are committed and clean, and the row still fails. It belongs to the concurrent DRY consolidation (`5851bb59`), not to this cycle, and is a concurrent-work blocker rather than a regression this cycle may fix.

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
