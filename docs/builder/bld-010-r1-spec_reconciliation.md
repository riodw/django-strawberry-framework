# Build: R1 — spec reconciliation (spec-010 residual-completion cycle)

Spec reference: `docs/SPECS/spec-010-foundation-0_0_4.md` (whole file; the item reconciles it against `HEAD`)
Rationale companion: `docs/SPECS/appx/spec-010-foundation-0_0_4-rationale.md` (extended, not replaced)
Build plan: `docs/builder/build-010-foundation-0_0_4.md`
Status: final-accepted

**Shape note.** This item is dispatched to **Worker 1 alone**, on the maintainer's standing instruction for this cycle: an item that changes only the spec and its rationale is Worker 1's, and both files are Worker 1-owned by `docs/builder/BUILD.md` `## Spec reconciliation` in any case. There is therefore no Worker 2 build pass and no Worker 3 review pass, and the `## Build report (Worker 2)` / `## Review (Worker 3)` sections of `docs/builder/ARTIFACT.md` are not applicable. Planning, work, and final verification all happen in this one spawn and in this one artifact, with the plan sections and the final-verification sections both present — the same single-pass shape `docs/builder/bld-003-final.md` declares for its own gate pass. The work record lives under `## Reconciliation report (Worker 1)`.

---

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable, and for a structural reason rather than a skip: `docs/builder/worker-1.md` `### Package-wide helper inventory before helper planning` gates *proposing helper-like logic*, and this item proposes none — it writes two Markdown files and touches no `.py` file. `git diff -- django_strawberry_framework/ tests/ | grep -c '^+++'` over this item's own writes is **0** by construction, since neither path is in its writable set.
- **Existing patterns reused.** The rationale file's own established structure (`## How to read this file`, `## Provenance of this record`, `## Entries keyed to the spec`, `## Standing notes`) and the appended-section precedent set by `docs/SPECS/appx/spec-003-optimizer_nested_prefetch_chains-0_0_2-rationale.md` `## Reconciliation pass — what the spec now says, and why`, whose per-entry shape (*Changed*, *Claims the spec no longer makes*, *Alternative rejected*) this pass adopts verbatim.
- **New helpers justified.** None.
- **Duplication risk avoided.** One live risk, and it is the item's central judgement call: **restating a later spec's contract inside spec-010.** Fifteen findings all point at surface later specs extended, and the pull is to describe the extension here because it is visible in the code spec-010 designed. Every one is resolved the same way — the seam is named and the owning spec is pointed at, never transplanted. A contract told twice goes stale in one of the tellings, and spec-010 is the wrong of the two to keep current.

### Implementation steps

1. Re-derive `HEAD` and `git status --porcelain`; confirm no path in the writable set is baseline-dirty.
2. Verify each of F1-F15 against `HEAD` source directly rather than accepting the plan's verification table (`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`).
3. Verify both spec-009 heading anchors still resolve, read-only, and verify the spec-008 anchor likewise. Record divergence rather than repointing.
4. Rewrite each falsified spec claim to state the current contract directly — no amendment block, no chronology.
5. Append a `## Reconciliation pass` section to the rationale, keyed to spec headings, one entry per finding, each naming the spec or card that caused the change and the alternative rejected.
6. Update the rationale's `## How to read this file` so it describes the file this pass leaves behind.
7. Re-run `scripts/check_spec_glossary.py`, `uv run ruff format .`, `uv run ruff check --fix .`; confirm every in-page anchor and link definition still resolves.
8. Set `Status:` and append a memory entry.

### Test additions / updates

None. This item lands no source and no test. A focused `pytest` run is optional per the dispatch; none was needed, because every claim this pass restates was verified by reading `HEAD` source, which is the stronger evidence for a documentation contract than a green run.

### Implementation discretion items

None reserved. There is no downstream worker on this item, so nothing is delegable. The two judgement calls the dispatch names (absorption scope, and F4's asymmetry) are decided in `### The absorption line` and `### F4 — the mirror that survived` below, not delegated.

### Dispatched findings checklist

Spec-010 has no `## Slice checklist`, so per `docs/builder/BUILD.md` `### Dispatched findings checklist` the boxes below are the fifteen findings the build plan's `## Worker-0 verification pass` dispatched to this item, plus the three procedural obligations the dispatch adds. Worker 1 both ticks and audits them; each box cites the evidence in this artifact that discharges it.

- [x] **F1** — collection resolves a relation immediately when its target is registered (`### Collection phase` step 8). `HEAD`: `django_strawberry_framework/types/base.py::_build_annotations #"Always defer auto-synthesized relation annotations"`.
- [x] **F2** — `Meta.primary` does not ship and `_types` is `dict[model, type]` (`## What does not ship in this slice`, `### TypeRegistry extensions`, `### Stays deferred`). `HEAD`: `django_strawberry_framework/registry.py::TypeRegistry.__init__ #"self._types: dict[type[models.Model], list[type]]"`.
- [x] **F3** — `cls._optimizer_field_map` / `cls._optimizer_hints` are mirrored for one minor version (`### Collection phase` step 13, `### Should redo now`). `HEAD`: zero occurrences package-wide.
- [x] **F4** — `cls._is_default_get_queryset` is a third such mirror, removed in the next minor. `HEAD`: `django_strawberry_framework/types/base.py::DjangoType #"_is_default_get_queryset: ClassVar[bool] = True"`, survives and is load-bearing.
- [x] **F5** — scalar manual override "not pinned in this slice"; three `consumer_*` sets. `HEAD`: four sets plus the union, and an `auto` fifth corner.
- [x] **F6** — detection rule keyed on "not a Django manager/descriptor". `HEAD`: `django_strawberry_framework/types/base.py::_consumer_assigned_fields #"shadows a Django"`.
- [x] **F7** — forward-reserved slots are six names, all unused. `HEAD`: only `fields_class` is still reserved-and-unused on the dataclass.
- [x] **F8** — collection calls `register` then `register_definition` (`### Collection phase` step 10). `HEAD`: `django_strawberry_framework/registry.py::TypeRegistry.register_with_definition`.
- [x] **F9** — the post-finalization guard lives only in `__init_subclass__`. `HEAD`: `django_strawberry_framework/registry.py::TypeRegistry._check_mutable` is a second guard; `::clear` resets more than the spec lists.
- [x] **F10** — `resolved_relation_annotation(django_field, target_type)`. `HEAD`: takes `field_meta=` as a third, keyword-only argument.
- [x] **F11** — phase 2 attaches relation resolvers only. `HEAD`: also file/image resolvers; collection additionally calls `install_is_type_of`.
- [x] **F12** — phase 1 is the failure-atomic boundary, full stop. `HEAD`: a `RELAY_GLOBALID_STRATEGY` snapshot writes registry state before phase 1.
- [x] **F13** — end-to-end tests live at `examples/fakeshop/tests/test_schema.py`. `HEAD`: that path does not exist; the tests are per-app.
- [x] **F14** — phase-10 doc list names `docs/FEATURES.md` and puts the wrong-order example in root `README.md`. `HEAD`: neither holds.
- [x] **F15** — phase 1's consumer-authored branch is a live classification arm. `HEAD`: unreachable under the documented call graph; defense-in-depth only.
- [x] Every rewritten claim states the current contract **directly** — no amendment block, no retraction paragraph, no "as of spec-NNN", no chronology a reader must apply.
- [x] Every rewritten claim has a rationale entry keyed to the spec section by its own heading, naming the causing spec or card and the rejected alternative.
- [x] Both spec-009 anchors and the spec-008 anchor verified read-only; neither spec opened for writing; no citation repointed.

---

## Reconciliation report (Worker 1)

### Working tree, re-derived

`HEAD` re-derived rather than taken from the build plan, which warns its own baseline was already moving:

```text
git rev-parse HEAD             -> 054de9dd37a2c4181fb2a91ded57f4823a1b5220   (unmoved from plan time)
git status --porcelain | wc -l -> 58   at the start of this pass (the plan recorded 47)
git status --porcelain | wc -l -> 70   at the end of it, of which 3 are this item's
```

**The plan's warning was correct, twice.** Eleven paths appeared between the plan's measurement and the start of this pass — `optimizer/join_taxonomy.py`, `optimizer/walker.py`, `utils/connections.py`, three `tests/optimizer/` files, and five `docs/dry/` scratchpads — and nine more appeared while this pass was writing, three of them fresh `docs/dry/` files (`dry-file-testing__client.md`, `dry-file-testing__relay.md`, `dry-folder-testing.md`). All belong to the concurrent `0.0.14` review / DRY cycle. **None was edited, reverted, staged, or `git checkout`-ed** (`AGENTS.md` rule 34), and none is in this item's writable set.

The intersection was empty **before** this pass wrote anything, which is the measurement that matters and is not re-derivable afterwards:

```text
git status --porcelain | grep -c 'spec-010'   -> 0   (measured before the first edit)
git status --porcelain | grep -c 'spec-010'   -> 2   (after; both are this pass's own writes)
```

Neither `docs/SPECS/spec-009-…md` nor `docs/SPECS/spec-008-…md` is dirty at either reading. This item's own writes are exactly four paths: the spec, the rationale, this artifact, and `docs/builder/worker-memory/worker-1.md`.

### The absorption line — the first judgement call, decided

Spec-010 owns the foundation layer: the definition object, pending relations, the finalization lifecycle, the consumer-override contract for relation fields, and the registry extensions. It does not own filters, orders, relay, connections, mutations, GlobalID encoding, or file/image output mapping.

Its `### Finalization phase` already had the right instinct — it calls the three-phase lifecycle "a skeleton later slices insert into rather than a closed list" and pushes the inserted phases' contents to the specs that shipped them. **The decision is to extend that discipline to every other section rather than to import another spec's contract into this one.** Concretely, that produced three shapes, applied consistently:

1. **Where the foundation's own structure changed, the structure is restated.** `_types` is many-valued, `register_with_definition` is one atomic call, `_check_mutable` exists, `clear()` resets more maps. These are the registry spec-010 designed, and a reader of spec-010 who cannot see the current registry shape is reading a false document.
2. **Where a slot or a phase exists but its behavior belongs elsewhere, the seam is named and the owner pointed at.** `Meta.primary`'s selection semantics, the interface / connection / GlobalID phase inserts, the file/image resolver pass, the scalar half of the override contract, the seven later dataclass slots — each gets one clause naming the owning spec and no description of what it does.
3. **Where the spec promised something that simply happened, the promise is deleted and the outcome stated.** The two optimizer mirrors are the case: "mirrored for one minor version, removed in the next minor" becomes "the definition is the only store", with no trace of the staging.

The pull the other way was strongest at `### DjangoTypeDefinition`, where enumerating all twenty-odd live slots is one edit away and reads as thoroughness. It loses for the reason the spec-003 reconciliation recorded for the same shape: an inventory of a dataclass is a symbol map, it is a second copy of seven other specs' contracts, and it goes stale on every one of their next edits. What spec-010 owes its reader is the **partition** — which slots are the foundation's, which are later, and who to ask — and that is what the block now carries.

### F4 — the mirror that survived, and why the asymmetry is not an oversight

`cls._is_default_get_queryset` is the one legacy class-attribute mirror still standing, and it stands because **the spec's own requirement cannot be met without it**.

The requirement is spec-010's, stated twice in its own text: an abstract intermediate base that overrides `get_queryset` but declares no `Meta` must still propagate the signal to concrete subclasses. Trace it against `HEAD`:

- `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__` stamps the sentinel **before** reading `Meta` (`#"cls._is_default_get_queryset = not has_custom_get_queryset"`, above `meta = cls.__dict__.get("Meta")`).
- Two lines later, `if meta is None: return`. An abstract base without `Meta` exits **there** — before any definition is constructed, before `register_with_definition`, before `cls.__django_strawberry_definition__` is set.
- So a definition-only carrier structurally cannot hold this flag for such a base: on the one class that most needs to carry it, no definition object exists.

That is the whole asymmetry. Its two siblings, `_optimizer_field_map` and `_optimizer_hints`, are read only for **registered** types, which by construction have a definition — so the definition could absorb them, and did. `has_custom_get_queryset()` reflects the split exactly: it prefers `__django_strawberry_definition__.has_custom_get_queryset` and falls back to the sentinel precisely for the definition-less case.

The spec now states this as a contract (a `ClassVar` stamped ahead of the `Meta` opt-out, with the reason) rather than as a compat shim with an expiry date. The rationale entry carries why the promise to remove it was withdrawn and what removing it would have cost.

### Spec-009 and spec-008 anchors — verified, not repointed

The build plan flags a live concurrent session reconciling spec-009 (`docs/builder/build-009-rich_schema_architecture-0_0_4.md` is untracked). Spec-010 cites spec-009 twice and spec-008 twice, all by heading anchor. All four were checked **read-only**, for the single purpose of confirming they resolve. Neither file was opened for writing and no citation was touched.

```text
grep -n '^### Layer 3: Finalization trigger$'  docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md   -> 672
grep -n '^### Decision 6: fail loudly$'        docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md   -> 1066
grep -n '^### The shape that shipped$'         docs/SPECS/spec-008-definition_order_independence-0_0_4.md -> 182
grep -n '^### The finalization trigger$'       docs/SPECS/spec-008-definition_order_independence-0_0_4.md -> 172
```

**All four resolve. No divergence to report**, so nothing is recorded for the maintainer under this head beyond the fact that the check ran at the moment of editing. `git status --porcelain | grep -c 'spec-009\|spec-008'` is `0` — neither spec is dirty, so the other session has not yet written to spec-009's body.

### Every count in this artifact, with the command that produced it

`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose` — counted as **occurrences**, and measured at the moment each number was written.

| Figure | Command | Result |
|---|---|---|
| working-tree paths (plan time) | recorded in the build plan | 47 |
| working-tree paths (pass start) | `git status --porcelain \| wc -l` | 58 |
| working-tree paths (pass end) | same command, re-run | 70 |
| this item's paths already dirty, before any edit | `git status --porcelain \| grep -c 'spec-010'` | 0 |
| spec bytes, before | `wc -c docs/SPECS/spec-010-foundation-0_0_4.md` | 61242 |
| spec bytes, after | same command, re-run | 70504 |
| rationale bytes, before | `wc -c docs/SPECS/appx/spec-010-…-rationale.md` | 10373 |
| rationale bytes, after | same command, re-run | 43044 |
| `_optimizer_field_map` occurrences, package | `grep -ro '_optimizer_field_map' django_strawberry_framework/ \| wc -l` | 0 |
| `_optimizer_hints` occurrences, package (the mirror) | `grep -ro 'cls\._optimizer_hints' django_strawberry_framework/ \| wc -l` | 0 |
| `_is_default_get_queryset` occurrences, package | `grep -ro '_is_default_get_queryset' django_strawberry_framework/ \| wc -l` | 5 |
| `DEFERRED_META_KEYS` members | `django_strawberry_framework/types/base.py #"DEFERRED_META_KEYS"` | 3 (`aggregate_class`, `fields_class`, `search_fields`) |
| glossary anchors used in the spec body | `grep -o '\[glossary-[a-z-]*\]' … \| sort -u \| wc -l` (body only) | 12, unchanged |
| `check_spec_glossary` result | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-010-foundation-0_0_4.md` | `OK: 12 terms`, exit 0 |
| rationale entries appended | `grep -c '^### ' …-rationale.md`, from `## Reconciliation pass` onward | 16 |

**The spec grew by 9,262 bytes and the rationale by 32,671.** That direction is worth stating rather than passing over, because the rationale move's usual direction is the opposite. The spec's growth is entirely (a) the seam table and the one-clause owner pointers that replace six now-false enumerations, and (b) implementation-relevant rationale, which `docs/builder/worker-1.md` `### Performing the rationale move` keeps in the spec by name: the reason step 8's deferral must stay unconditional, the reason the post-finalization guard is stated twice, the reason the detection rule is positive rather than exclusionary, and the reason `_is_default_get_queryset` cannot move onto the definition. Each is a "why that changes HOW a thing is built" — a builder who never reads them re-adds the eager bind, deletes the second guard as redundant, loosens the detection rule, or finishes the migration that must not be finished. The corpus ratchet governs `docs/builder/`'s six workflow files and does not reach a spec or its rationale, so no bytes were owed elsewhere for this growth.

Note the third-from-last-group row deliberately measures `cls._optimizer_hints`, not `_optimizer_hints`: the bare token still occurs as `DjangoTypeDefinition.optimizer_hints` and as local variables, so a bare grep would sample the wrong population and report the mirror as surviving. This is the "long grep phrase samples a claim's vocabulary rather than establishing its population" trap, inverted — here the *short* token over-collects.

### Spec status-line re-verification (owed by every Worker 1 spawn)

Read `docs/SPECS/spec-010-foundation-0_0_4.md` lines 1-10. The spec carries **no `Status:` / owner / target-release / predecessor header block**: its opening is the title, the rationale-companion pointer, then `## Purpose`. The one forward-looking line in that region is the companion pointer's list of what the rationale holds, which this pass extends — and it was updated in the same edit so the pointer describes the file that now exists. Nothing else in lines 1-10 is falsified.

### Validation run

- `uv run ruff format .` — pass (no-op; Markdown only).
- `uv run ruff check --fix .` — pass (no-op; Markdown only).
- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-010-foundation-0_0_4.md` — `OK: 12 terms`, exit 0.
- `git status --short` after both ruff invocations — the only paths added versus the pre-pass reading are this item's four. No unexpected churn; nothing reverted.
- No `pytest` run. The dispatch makes it optional for an item landing no code, and no claim in this pass rests on runtime behavior.

### Failability proofs

None; this item introduced no boundary, guard, gate, or rejection path. Confirmed mechanically rather than accepted from the plan: this item writes no executable code at all, so there is no expression for a **fail-open shape** to inhabit either. Both confirmations are vacuous in the strict sense — and stated, because `worker-1.md` `### Failability and fail-open checks` asks for the confirmation, not for the absence of the subsection.

### Hot-path budget

Not applicable; the plan declares `Hot-path declaration: none. R1 and R3 write Markdown only`. Confirmed against this item's diff rather than accepted from the declaration.

### Floor verification

The plan scopes floor verification to **R2 alone** and declares `none` for R1. Confirmed correct against this item's diff: `docs/builder/BUILD.md` `### When it is required` scopes the obligation to request/response handling, ASGI plumbing, body parsing, session/auth, queryset or expression compilation, schema construction against Strawberry internals, and consumer or middleware wiring. This item touches none of them — it touches no `.py` file. **No floor venv was built and the shared `.venv` was not mutated.**

### Notes for Worker 1 (spec reconciliation)

Three items for the maintainer and for the cycle's final gate. **None is a source defect** — the build plan's verification pass found none, and this pass found none either; every one below is a documentation-surface observation outside this item's writable set.

1. **`docs/GLOSSARY.md#definition-order-independence` carries the same untested `strawberry.lazy` claim R2 is closing.** The build plan's F16 already names it. Recorded here so the final gate sees it from both sides: if R2 proves the shape works, the glossary's claim is correct-but-was-unpinned and needs no edit; if R2 finds it does not work, the glossary is a second surface carrying a false shipped claim, and it is DB-backed (`examples/fakeshop/db.sqlite3` -> `scripts/build_glossary_md.py`), so it is never hand-edited and Worker 0 must re-partition with a Worker 2 pass.
2. **Spec-010's `## Pre-implementation spikes` section says the Phase-0 conclusions were "written into `README.md`".** At `HEAD` the schema-setup boundary, the correct/wrong-order pair, and the import-boundary note all live in `docs/README.md`; the root `README.md` carries only the correct snippet. This pass fixed the two sentences that state a **current** documentation location (`## Strawberry finalization strategy` and phase-10) and deliberately left the Phase-0 spike record alone: it is a historical account of what a spike concluded and where it was recorded at the time, in the same class the rationale's existing entry rules on for `convert_relation` / `lazy_ref` — a present-tense survival in a shipped spec that is correct as history. Flagged rather than fixed, because the boundary is a judgement the maintainer may draw elsewhere.
3. **The `### Manual annotation contract for relation fields` heading lost its `(0.0.4)` suffix.** No in-page anchor, no reference-style link definition, and no other document targeted it — verified by `grep -rn 'manual-annotation-contract' .` returning nothing outside this artifact. Recorded because a heading rename is the one edit class that can silently break an anchor, and the check is cheap to state and expensive to re-derive later.

### Spec changes made (Worker 1 only)

Every edit below is keyed to the finding that triggered it, cites the spec section by its own heading, and carries a one-line reason. Line numbers are the **post-edit** file's, given for navigation only; the heading is the durable address (`AGENTS.md` rule 27 permits raw `path:NN` inside a per-cycle artifact and nowhere else).

| # | Spec section | Edit | Reason |
|---|---|---|---|
| F1 | `### Collection phase: DjangoType.__init_subclass__` (step 8, spec:~250) | The relation branch always records a `PendingRelation` and sets the sentinel annotation; the eager "resolve immediately if registered" arm is gone from both the comment and the code | An eager bind froze the relation onto whichever type was registered first; the deferral is what makes the primary-selection layer sound |
| F2 | `## What does not ship in this slice`, `### TypeRegistry extensions`, `### Stays deferred` | `_types` is `dict[model, list[type]]` beside `_primaries`; the multi-type surface is stated as the registry's shape and the selection **rule** is pointed at `spec-018`; the "hard-fails on duplicate models, and that stays" claim is deleted | The registry is the foundation's to describe; what `primary` *means* is not |
| F3 | `### Collection phase` (step 13, deleted), `### Should redo now` (spec:~455) | The two optimizer mirrors are gone from both sites; the definition is stated as the only store, read by the walker's resolvers and the schema audit | The promised removal happened; a spec that still promises it is a false forward-looking claim |
| F4 | `### Collection phase` (step 1), `### Should redo now` (spec:~458) | `_is_default_get_queryset` is stated as a surviving `ClassVar` stamped **before** the `Meta` early-return, with the structural reason; "removed in the next minor" deleted | A definition-only carrier cannot serve an abstract base that returns before any definition exists |
| F5 | `## What does not ship in this slice`, `### Manual annotation contract…`, `### DjangoTypeDefinition`, `### Stays deferred` | Four `consumer_*` split sets plus the union; the relation half stated here, the scalar half pointed at `spec-019`, the `auto` corner named as a seam | The contract generalized; spec-010 keeps only its own half |
| F6 | `### Manual annotation contract…` (detection rule) | Assignment detection requires a `StrawberryField`; any other shadow of a selected Django field name raises `ConfigurationError` | "not a Django manager/descriptor" admitted arbitrary values and failed late |
| F7 | `### DjangoTypeDefinition` (reserved slots), `### Stays deferred` (`DEFERRED_META_KEYS`) | Only `fields_class` is reserved-and-unused; `aggregate_class` / `search_fields` are rejected `Meta` keys with no slot; the live slots are listed as a seam table naming owners | Six-name lists in two places were both false, in different directions |
| F8 | `### TypeRegistry extensions`, `### Collection phase` (step 10) | One atomic `register_with_definition(...)` with snapshot rollback; `discard_pending` added to the API list it was missing from | A two-call sequence could leave a registration without its definition |
| F9 | `### TypeRegistry extensions`, `## Idempotency and lifecycle contract` | `_check_mutable` stated as a second guard at the registry boundary; `clear()`'s reset list corrected and its teardown pass named | The spec described one guard and an out-of-date reset list |
| F10 | `### Finalization phase` (phase 1 loop) | `resolved_relation_annotation(..., field_meta=...)`, read from `definition.field_map[snake_case(...)]` | The signature changed; the pseudocode is the spec's normative call shape |
| F11 | `### Finalization phase` (intro + phase 2), `### Collection phase` (tail) | Phase 2 attaches relation **and** file/image resolvers, the latter over the broader skip set and pointed at `spec-037`; collection ends with `install_is_type_of` | Two live steps the lifecycle description omitted |
| F12 | `### Finalization phase` (docstring), `## Idempotency and lifecycle contract` | The atomicity claim is scoped to **class objects**, with the pre-phase-1 `RELAY_GLOBALID_STRATEGY` snapshot named as the one registry write that precedes it | An unqualified "nothing has happened yet" was false in one measurable respect |
| F13 | `### End-to-end schema and HTTP tests` | `examples/fakeshop/apps/library/tests/test_schema.py`; `tests/types/test_definition_order_schema.py` described as the sentinel-repr pin it now is | The named path does not exist; per-app placement is `AGENTS.md` rule 7 |
| F14 | `## Strawberry finalization strategy`, `## Phased implementation order` (step 10) | `docs/GLOSSARY.md` replaces `docs/FEATURES.md`; the wrong-order example and the import-boundary note are located in `docs/README.md` | `docs/FEATURES.md` does not exist and the example is not in the root README |
| F15 | `### Finalization phase` (phase 1 loop) | The consumer-authored arm is stated as defense-in-depth, unreachable under the documented call graph, with the reason it is kept | F1's consequence; the spec presented an unreachable arm as live classification |
| — | `# Foundation slice…` (companion pointer, spec:3) | The pointer's list of what the rationale holds now describes the reconciliation record too | Owed by the per-spawn status-line re-verification; the old list is now incomplete |

No other spec was edited. `docs/SPECS/appx/spec-010-foundation-0_0_4-terms.csv` was **not** edited and needs no edit: the twelve glossary anchors the body names are unchanged, and `check_spec_glossary` exits 0. `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`, `examples/fakeshop/db.sqlite3`, and `CHANGELOG.md` were not touched.

---

## Final verification (Worker 1)

- **Dispatched findings checklist:** all eighteen boxes `- [x]`, each discharged by evidence in this artifact. No deferral reason is owed.
- **Every rewritten claim states a contract, not a chronology.** Audited by reading the post-edit spec end to end: it carries no amendment block, no retraction paragraph, no "as of spec-NNN", and no sentence a reader must date to interpret. Where a later spec is named it is named as the **owner of a seam**, in the present tense, which is a contract statement and not a history.
- **Every finding has a keyed rationale entry.** Sixteen `###` entries under `## Reconciliation pass`, one per finding plus a closing entry recording what the pass deliberately did not change. Each names its spec section by that section's own heading, states what the spec used to claim, what is true now, the causing spec or card, and the alternative rejected.
- **The rationale was extended, not rewritten.** `git diff -U0` over it shows **seven** deleted lines in total: the two `## How to read this file` bullets whose framing this pass falsifies (the dispatch asks for exactly that — "little deliberation to cut" and "a change record, not a full rationale extraction" stop being true the moment the appended section lands), and the closing line of `## Standing notes`, extended by one sentence pointing at the new block. **`## Entries keyed to the spec` is byte-unchanged**, all four of its entries intact.
- **DRY:** no new duplication. The single risk — importing a later spec's contract into spec-010 — was decided against in `### The absorption line` and applied uniformly across all fifteen findings.
- **Scope:** no package source, no test, no other spec, no terms CSV, no DB-backed doc. No commit, no branch, no `git stash` / `checkout` / `restore` / `worktree`.
- **Concurrent work:** eleven paths went dirty between the plan's baseline and this pass. Reported above, not reverted, not in scope.

### Summary

Spec-010 now states the contract that holds at `HEAD`. Fifteen claims that later work falsified were rewritten in place — the unconditional relation deferral, the many-valued registry and its atomic register-with-definition, the two retired optimizer mirrors and the one that survived, the four-corner override contract, the reserved-slot inventory, the second registry-boundary guard, the corrected `clear()` reset, the phase-2 file/image pass, the `install_is_type_of` tail, the scoped atomicity claim, the moved test and doc paths, and the defense-in-depth pending arm. None of them narrates the change: the spec reads as a current contract, and the chronology lives in the companion.

The absorption line held, which was the hard part. Fifteen findings all sit on surface that seven later specs extended, and every one was resolved by naming the seam and pointing at the owner rather than transplanting a paragraph — so spec-010 gained one clause per seam and no second copy of anyone else's contract.

`Status: final-accepted`. Worker 0 marks the plan's R1 checkbox.

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
