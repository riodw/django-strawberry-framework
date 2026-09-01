# Package build plan: mutations / 0.0.11 (036) — residual-reconciliation cycle

Spec source: `docs/SPECS/spec-036-mutations-0_0_11.md` (archived; shipped in `0.0.11` as card `DONE-036-0.0.11`)
Rationale companion: `docs/SPECS/appx/spec-036-mutations-0_0_11-rationale.md` (created by this cycle's Slice 0)
Target release: `0.0.11` (already shipped — this cycle lands **no** version-affecting change)
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every slice must justify shared/duplicated patterns before merging.
Ownership partition: declared per round below (R1's four cohorts are read-only and concurrent; every other pass is sequential and single-cohort).
Hot-path declaration: Slice 0, R1 and R2 land no source and declare **none**. **R3 is declared hot-path conditionally** — if the conformance audits return a SKIPPED contract whose repair lands inside `mutations/resolvers.py`, `mutations/permissions.py`, or `utils/write_transaction.py`, that pipeline runs on every generated mutation request and the repair owes a before/after number per `docs/builder/BUILD.md` `## Hot-path budget`. A repair confined to test files declares `none`.
Floor-verification scope: Slice 0, R1, R2 declare **none** (no source, no framework seam). **R3's scope is conditional on what it repairs** — a repair touching the write pipeline, the `strawberry.Schema` construction seam, or the live `/graphql/` request path re-runs its focused tests in an isolated floor venv at the versions `docs/builder/BUILD.md` `## Floor verification` states canonically, owned by **R3's builder pass**; the final gate is the backstop confirming it happened, not a second owner.
Pre-flight: run on 2026-09-01 with three recorded deviations, all deliberate; baseline: **heavily dirty with a concurrent session's work** (see below); cleanup: cycle-scoped worker memory seeded empty (4 files), `docs/builder/temp-tests/036/` created, `docs/shadow/` deliberately left populated.

> **Cycle artifacts retired.** The eight per-round `bld-036-*.md` artifacts this plan names were deleted
> when the cycle closed; only this plan and `docs/builder/bld-036-final.md` survive on disk. All nine read
> `Status: final-accepted` before deletion and every one is recoverable in full from the cycle's commit:
> `git show e184bf79:<path>`. Treat every `bld-036-*.md` path below, and in `bld-036-final.md`, as
> commit-resolvable rather than disk-resolvable -- they are retired records, not dead links. The
> cycle-scoped worker-memory files are git-ignored scratch and were not preserved.

## Cycle shape (why this is not an ordinary spec build)

`spec-036` shipped. Its five slices are `final-accepted` and its card is Done. This cycle is a **residual-reconciliation cycle** in the shape the `033`/`034` cycles established, driven by the maintainer's instruction, with three obligations:

1. **The missing rationale companion.** `spec-036` was archived with a `-terms.csv` and no `-rationale.md`. Slice 0 closed that gap.
2. **Conformance: prove nothing planned was skipped in the code.** Every contract the spec states is checked against shipped source and tests **at `HEAD`**. A contract the spec states and the code does not implement is a **code** defect and routes to R3. A contract the code implements *differently* because a later card deliberately changed it is a **spec** defect and routes to R2.
3. **Reconciliation: the spec states the current contract.** Where later work corrected or superseded what `036` shipped, the spec is rewritten to state the corrected contract **directly, without chronology**; what changed, when, and why is appended to the rationale companion as a `**Post-ship:**` bullet under the owning Decision.

**Why `036` is the highest-risk reconciliation target in the corpus so far.** `spec-036` froze the write-side foundation — the `FieldError` envelope, the generated `Input` / `PartialInput` shapes, the `<Name>Payload` wrapper, the resolver pipeline, and the `Meta.permission_classes` write-auth seam — and then **four later cards built directly on top of it**: `038` (form mutations, `0.0.12`), `039` (serializer mutations, `0.0.13`), `040` (auth mutations, `0.0.13`), and the `0.0.14` write-transaction hardening. Every one of them had licence to move shared machinery out from under `036`'s Decisions. The spec's own text pins contracts — `steps 3-6 inside one transaction.atomic()`, `no .only(...)` under the mutation operation, a three-symbol public surface — that later work is known to have changed. **The default expectation for this cycle is therefore SUPERSEDED, not CONFORMS**, and a cohort returning all-CONFORMS on the resolver or permission surface has probably graded the spec's words against itself rather than against `HEAD`.

### Known-live divergence classes this cycle exists to resolve

Slice 0 surfaced five while reading; R1 establishes the full population and R2 reconciles:

1. **`## Current state` reads present-tense and is false at `HEAD`** on at least three bullets ("No `mutations/` module", "no `Mutation` type", "sibling `0.0.11` card is unshipped"). Per `docs/builder/BUILD.md` `### `## Current state`: observations stand, predictions do not`, grade **clause by clause** — a dated observation of the pre-build repo stands; a falsified prediction is rewritten.
2. **The `0.0.14` write-transaction hardening is not in the spec.** `HEAD`'s `docs/GLOSSARY.md` (and the concurrent session's dirty copy) name `Meta.select_for_update` row locking with a retryable `conflict` `FieldError`, single-write-alias pinning, and a point-in-time authorization rule. Decisions 8, 10, and 15 carry none of it. Expect these three to diverge most.
3. **The public-symbol count.** Decision 5's surviving justification says "keeps the public symbol count at three"; the Decision body and DoD item 8 say four (`DjangoMutation`, `DjangoMutationField`, `FieldError`, `DjangoModelPermission`). One of the two is wrong at `HEAD`; `django_strawberry_framework/__init__.py.__all__` decides.
4. **The terms-CSV omits two shipped glossary headings.** `docs/GLOSSARY.md` at `HEAD` carries both `## \`DjangoMutationField\`` and `## \`DjangoModelPermission\``, while `spec-036-mutations-0_0_11-terms.csv` lists neither, and the spec's moved Risks item still argues they *cannot* be listed because they have no heading yet. The CSV is **outside this cycle's scope** (not a `.py` file, and `import_spec_terms` writes the kanban DB) — the stale *argument* is R2's to correct, the CSV itself is a maintainer call.
5. **The Decision-8 anchor defect is live in two sibling specs.** Slice 0 repaired 16 uses of a broken `#decision-8--...-optimizer-refetch` slug in `spec-036`; the same defect stands in `spec-038` (36 uses) and `spec-039` (34 uses). Out of scope here — deferred-work catalog.

## Maintainer-set scope for this cycle

- **This cycle touches spec files and `.py` source/test files only.** No `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` / `docs/TREE.md` / `TODAY.md` / `README.md` / `docs/README.md` / `GOAL.md` / `CHANGELOG.md` / `BACKLOG.md` edits, no kanban-DB writes, no doc regeneration, no card movement, no `-terms.csv` edit.
- **No closeout agentflow edits.** `docs/builder/BUILD.md`, `docs/builder/ARTIFACT.md`, and the four `docs/builder/worker-*.md` role files are not edited by this cycle.
- **Every file this cycle creates carries `036` in its name** — artifacts, and the cycle-scoped worker-memory files `worker-<N>-036.md`.
- The spec is already archived at `docs/SPECS/` with its companions at `docs/SPECS/appx/`; the archival obligation is satisfied by **verification**, not by a move. Slice 0 placed the new companion directly in `docs/SPECS/appx/`, beside the existing `-terms.csv`.

## Pre-flight

| Step | Outcome |
|---|---|
| 1. Working-tree baseline explicit | **Deviation.** Not clean — 106 dirty paths. The dirty set is a concurrent session's write-side hardening work and it covers **every module this cycle audits**. Per `AGENTS.md` rule 34 it is recorded as baseline-dirty out-of-scope rather than escalated, and no pass in this cycle edits or reverts any of it. Consequence for method: see `## The audit measures HEAD, not the working tree` below. |
| 2. `scripts/review_inspect.py` runs | Passed — smoke run on `django_strawberry_framework/mutations/sets.py --output-dir docs/shadow --stdout` produced a full overview (51 symbols, 11 control-flow hotspots, 9 repeated string literals), exit 0. |
| 3. Build artifacts reset | **Deviation.** No prior `build-036-*` / `bld-036-*` artifact existed, and every path this plan creates was verified absent. `docs/builder/bld-003-final.md` is a *different, committed* cycle's record and was **not** deleted: it is outside this cycle's maintainer-set scope and may belong to a concurrent session. Deleting a prior cycle's artifacts is the one irreversible pre-flight mistake. |
| 4. `.gitignore` lists the scratch paths | Passed — `docs/shadow/`, `docs/builder/worker-memory/`, `docs/builder/temp-tests/` all listed. |
| 5. Scratch directories cleared | **Deviation.** `docs/builder/worker-memory/` already held four files dated 2026-08-31 23:27 from a concurrent cycle; they were **not** cleared or clobbered. This cycle uses **cycle-scoped** memory files `worker-0-036.md` … `worker-3-036.md`, seeded empty, which also satisfies the maintainer's "every file this cycle creates carries `036`" rule. `docs/builder/temp-tests/` was empty; `036/` created inside it. `docs/shadow/` was left populated: its files are gitignored, regenerable, overwritten by name, and a concurrent session may be mid-review against them. Any shadow file this cycle relies on is regenerated by the pass that uses it. |
| 6. Spec-doc consistency check | Passed — `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-036-mutations-0_0_11.md` → `OK: 38 terms`, exit 0. Re-run after Slice 0's move: `OK: 38 terms`, exit 0. |
| 7. Spec rationale extracted | **Done and verified** — Slice 0 below. |

### The audit measures `HEAD`, not the working tree

The concurrent session's dirty set includes every `django_strawberry_framework/mutations/*.py`, `django_strawberry_framework/types/finalizer.py`, and `django_strawberry_framework/utils/{errors,inputs,write_transaction,write_values}.py` — `+1134 / −316` across the mutation surface alone. Auditing that tree would grade the spec against another session's uncommitted, possibly half-landed work and would record "corrections" describing behavior that has not shipped.

So this cycle grades against a **read-only `HEAD` snapshot**, per `docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose` ("a read-only HEAD reference: `git show HEAD:<path>` into a scratch path **outside** the repo"):

- Snapshot commit **`7426e7e7d8aa447e89fee75088447d6a506dec12`**, materialized outside the repo by `git archive HEAD | tar -x -C <scratch>` — no `git stash`, `git checkout`, `git restore`, or `git worktree` anywhere in this cycle.
- Every conformance grade cites the snapshot path or a `git show HEAD:<path>` read, never the live working file.
- **Before any repair is dispatched, R3 re-checks the live working tree**: if the concurrent session has already closed the gap, the finding is reported as already-closed-in-flight rather than repaired, so this cycle never writes over their work or duplicates it.
- Running tests exercises the *dirty* tree and therefore cannot verify a `HEAD` claim. A test run's result is evidence about the live tree only, and every pass says which it is measuring.

### Baseline-dirty out-of-scope files (never edit, never revert)

All 106 dirty paths, of which the ones intersecting this cycle's audit territory are the load-bearing set:

`django_strawberry_framework/mutations/{fields,inputs,permissions,resolvers,sets}.py`, `django_strawberry_framework/types/finalizer.py`, `django_strawberry_framework/utils/{__init__,canonical,connections,context,converters,errors,imports,input_values,inputs,permissions,policies,querysets,relations,sessions,typing,write_transaction,write_values}.py`, `tests/mutations/{test_fields,test_inputs,test_permissions,test_sets,test_write_transaction}.py`, `tests/types/test_finalizer.py`, `tests/utils/*.py`.

Also dirty and out of scope: `django_strawberry_framework/{_django_patches,conf,connection,consumers,exceptions,keyset,permissions,relay,resource_policy,routers,sets_mixins}.py`, `django_strawberry_framework/{auth,extensions,filters,forms,optimizer,orders,rest_framework}/*.py`, `docs/{GLOSSARY,README,TREE,feedback2}.md`, `docs/bug_hunt/bug_hunt-0_0_15.md`, `KANBAN.md`, `KANBAN.html`, `README.md`, `examples/fakeshop/apps/library/{schema,serializers}.py`, `examples/fakeshop/db.sqlite3`, `examples/fakeshop/test_query/{test_auth_api,test_library_api,test_resource_policy_api}.py`, and the remaining `tests/**` paths. Also out of scope: `docs/builder/bld-003-final.md`.

Many of these are `.py` files and this cycle's scope is "spec files and `.py` files" — **the scope grants no licence over these particular `.py` files.** They are another session's work and stay untouched.

**`git diff --check` baseline exception:** 4 trailing-whitespace lines in baseline-dirty `docs/feedback2.md` make the tree-wide check exit 2. Recorded here so the final gate does not read it as this cycle's output; scoped to this cycle's own files the check exits 0.

### Tracked binary / generated files that a concurrent writer can rewrite

`examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`, `docs/TREE.md`. All five are already dirty from the concurrent session and **no pass in this cycle writes any of them**, so any churn observed against them during this cycle is by definition not this cycle's output. Never `git checkout` one as "tool drift".

## Slice 0 — spec rationale extraction (pre-flight step 7, closed)

Performed by Worker 1 as a procedural-closure pass before this plan existed. Recorded here because the plan is where the cycle's artifact list lives.

- Created `docs/SPECS/appx/spec-036-mutations-0_0_11-rationale.md` (74,895 bytes, 428 lines), with a heading for each of the spec's 15 Decisions and `### Changes this Decision underwent` sections ready to take R2's `**Post-ship:**` bullets.
- Spec verified byte-identical to `HEAD` before the first edit, then `164,498 → 131,777` bytes / `709 → 623` lines: **−32,721 bytes**.
- Four routes carried **37,644** bytes of verbatim text out — the 5-entry revision block (14,609 B), 15 `Justification:` + 15 `Alternatives considered` pairs (17,539 B, carrying 19 justifications and 33 rejected alternatives), the `## Risks and open questions` body (7 preferred-answer/fallback items, 5,332 B), and one chronology parenthetical (98 B) — against 4,923 bytes of pointer/link framing added back. The arithmetic closes on the measured net delta.
- **Population established with four grammars**, and the finding is load-bearing: `grep -on 'Revision [0-9]'` → 6 occurrences; the shortest distinctive token `evision` → 7, the extra being the block's own preamble; a 20-word chronology sweep → 18 occurrences (14 in moved text, 2 in the deleted parenthetical, 2 false positives). Unlike `034` (4 surviving cross-reference sites) and `035` (11), **spec-036 carried no `Revision N` cross-reference outside the block**, so it lifted whole.
- **Repair A (not byte-verbatim, deliberate):** the spec carried a broken in-page slug for Decision 8 — `optimizer-refetch` where "optimizer re-fetch" slugs to `optimizer-re-fetch` — with **16 uses at `HEAD`, all resolving to nothing**. Repaired (12 in the spec, 4 in moved text). Plus 5 uses across 4 anchors naming spec sections the companion lacks, re-pointed at the spec through reference-style links.
- **Held back under the implementation-relevant carve-out:** Decision 6's rejection of a blanket "every editable field required" rule and its M2M-always-optional derivation; Decision 8's relation-decode-after-authorize paragraph; Decision 9's whole re-fetch-visibility paragraph. Each is a "why that changes how it is built" or a guarantee the contract makes.
- **Open maintainer call recorded, not acted on:** 184 review-finding tags across 34 grammars (`AR-H#` / `Major-#` / `Medium-#` / `CR-#` / `DRY-#` / `Low-1` / `P1`-`P2`) survive in the spec. A tag is a lookup key into the companion rather than a chronology, and both precedents left the shape standing (`spec-035` still carries a `Major-2`); stripping 184 parentheticals in 34 grammars is a rewrite, not a cut-and-paste.
- Gates: `check_spec_glossary` `OK: 38 terms` exit 0; `check_citations` `OK: 929 citations resolve` exit 0 (unchanged); scaffold check exit 0 on both files with all 10 group headers in `START.md` order; 0 unresolved in-page anchors and full ref/def parity on both files; every def path disk-checked; all 30 cross-file `#anchor` defs resolved against the target's real headings.
- Artifact: `docs/builder/bld-036-slice-0-rationale_extraction.md` — `Status: final-accepted`.

## Artifact list

- `docs/builder/bld-036-slice-0-rationale_extraction.md` (created, `final-accepted`)
- `docs/builder/bld-036-review-1a-inputs_envelope_payload.md`
- `docs/builder/bld-036-review-1b-base_meta_finalizer.md`
- `docs/builder/bld-036-review-1c-resolvers_fields_writeauth.md`
- `docs/builder/bld-036-review-1d-live_surface_g2_exports.md`
- `docs/builder/bld-036-review-2-spec_reconciliation.md`
- `docs/builder/bld-036-review-3-code_repair.md` — **conditional.** Created only if an R1 cohort returns a non-empty SKIPPED enumeration whose repair is inside this cycle's scope and is not already closed in the concurrent session's working tree.
- `docs/builder/bld-036-integration.md`
- `docs/builder/bld-036-final.md`

## Ownership partition

**R1 (four cohorts, concurrent).** Every R1 cohort is **read-only over source and tests** — it writes exactly one file, its own artifact — so the partition is trivially disjoint and concurrency is licensed. Each cohort's audit *territory* is declared so the findings partition the way the files would. All territory is read at the `HEAD` snapshot.

| Cohort | Writes | Audit territory (read-only, at `HEAD`) |
|---|---|---|
| R1a | `docs/builder/bld-036-review-1a-inputs_envelope_payload.md` | `django_strawberry_framework/mutations/inputs.py`, `utils/inputs.py`, `utils/errors.py`, `utils/converters.py`, `utils/write_values.py` (only as the input-decode boundary), `tests/mutations/test_inputs.py`, `tests/utils/test_inputs.py`, `tests/utils/test_errors.py`. Spec territory: **Slice 1**, Decisions 6, 7, 14, the `## User-facing API` input/payload/error shapes, `## Error shapes`, DoD item 2, and every `## Edge cases and constraints` bullet about input shape, naming, or the `UNSET`/`null` tri-state. |
| R1b | `docs/builder/bld-036-review-1b-base_meta_finalizer.md` | `django_strawberry_framework/mutations/sets.py`, `mutations/operations.py`, `types/finalizer.py`, `types/base.py` (only for `DEFERRED_META_KEYS` / `ALLOWED_META_KEYS` byte-unchanged-ness), `registry.py`, `tests/mutations/test_sets.py`, `tests/mutations/test_operations.py`, `tests/types/test_finalizer.py`. Spec territory: **Slice 2**, Decisions 3, 4, 11, 12, DoD item 3, and the finalization-ordering / no-`Meta`-key-added / two-mutations-share-input edge cases. |
| R1c | `docs/builder/bld-036-review-1c-resolvers_fields_writeauth.md` | `django_strawberry_framework/mutations/resolvers.py`, `mutations/fields.py`, `mutations/permissions.py`, `utils/write_transaction.py`, `utils/querysets.py` + `utils/permissions.py` (only as the visibility / request-decode boundary), `schema.py`, `tests/mutations/test_resolvers.py`, `tests/mutations/test_fields.py`, `tests/mutations/test_permissions.py`, `tests/mutations/test_write_transaction.py`. Spec territory: **Slice 3**, Decisions 8, 9, 10, 15, DoD item 4, and the constraint / delete-snapshot / relation-decode / M2M / unauthorized / async edge cases. **This is the cohort where SUPERSEDED is most expected** — the `0.0.14` write-transaction hardening lives here. |
| R1d | `docs/builder/bld-036-review-1d-live_surface_g2_exports.md` | `examples/fakeshop/apps/products/schema.py`, `apps/products/{models,forms,serializers,services}.py`, `examples/fakeshop/config/schema.py`, `examples/fakeshop/test_query/test_products_api.py`, `examples/fakeshop/apps/products/tests/test_schema.py`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, `django_strawberry_framework/optimizer/walker.py` + `tests/optimizer/test_walker.py` (only the G2 `only_fields` mirror). Spec territory: **Slices 4 and 5**, Decisions 1, 2, 5, 13, the `## Test plan` ownership split, DoD items 1, 5, 6, 7, 8, `## Current state` clause-by-clause, and the `## Out of scope` boundary claims. |

**R2 and R3 (two cohorts, concurrent).** Amended after R1 closed. R1 established that the divergence is almost entirely spec-side (34 SUPERSEDED / 26 STALE-DESCRIPTION / 6 RENAMED) while the code side is two SKIPPED contracts plus three weak pins closable in **test files only**. That makes the two remaining rounds' file ownership provably disjoint, so serializing them would cost wall-clock for no quality gain:

| Cohort | Writes | Reads (never writes) |
|---|---|---|
| R2 — spec reconciliation (Worker 1) | `docs/SPECS/spec-036-mutations-0_0_11.md`, `docs/SPECS/appx/spec-036-mutations-0_0_11-rationale.md`, `docs/builder/bld-036-review-2-spec_reconciliation.md`, the `Status:` line + appended `## Final verification (Worker 1)` of the four `bld-036-review-1*.md` artifacts, `worker-memory/worker-1-036.md` | all source and tests |
| R3 — code repair (Worker 2) | `tests/mutations/__init__.py`, `tests/test_permissions.py`, `tests/mutations/test_inputs.py`, `tests/mutations/test_resolvers.py`, `tests/optimizer/test_walker.py`, `examples/fakeshop/test_query/test_products_api.py`, `docs/builder/bld-036-review-3-code_repair.md`, `worker-memory/worker-2-036.md` | the spec (its read-only input contract, being edited beneath it), the four R1 artifacts |

No file appears in both columns' write sets. Each cohort was told the other's write list and told not to wait on it. R2 additionally carries the facts about R3's authorized scope it needs in order not to write spec text asserting the absence of pins R3 is landing.

R2 is single-cohort **within** its own round by construction — two custodians on one spec would guarantee the half-reconciled state `worker-1.md` forbids.

**Worker 3's review of R3, integration, final gate:** `none; sequential`, one cohort each.

## Maintainer decisions (escalated before dispatch, per `docs/builder/BUILD.md` `### Contract-level findings are escalated as maintainer decisions before dispatch`)

**Decision A — the unowned `0.0.14` write-hardening surface: CORRECT CLAIMS ONLY.** R2 rewrites every `spec-036` claim that is now false so the spec states the current contract, but does **not** expand `spec-036` into a description of machinery it never scoped; the unowned surface goes to the deferred-work catalog naming it as needing an owning spec.

- *Rejected — absorb the full surface into `spec-036`.* It would close the corpus gap now, but grows `036` substantially and attributes to it a pipeline it did not scope, making the spec a worse record of what the card actually shipped.
- *Rejected — correct claims plus a stub section naming what changed after `0.0.11`.* Rejected as a chronology inside the contract: `docs/builder/BUILD.md` `## Spec rationale extraction` forbids the spec narrating its own history, and "what changed after this card" is exactly the rationale companion's job.

**Decision B — R3's repair scope: ALL FINDINGS, INCLUDING THE DIRTY FILE.** Both SKIPPED contracts and all three weak pins are closed, which requires appending to `tests/mutations/test_inputs.py` (dirty `+16/-0` with the concurrent session's work).

- *Rejected — clean files only.* It would carry zero collision risk but would leave the cycle's headline gap open: the spec's strongest promise (`FieldError` "byte-identical") had **no gate at all**, which is why the type grew from two fields to four with nothing failing.
- *Rejected — anchors and denial rows only.* Closes the two SKIPPED contracts and defers all three weak pins; rejected for the same reason, plus it leaves the AR-M7 package tier — which exists *because* the live tier cannot pin columns — decoupled from production.
- Mitigation required of R3: additive appends only, no reflow of existing content, and the file's `git diff --numstat HEAD` figure re-checked immediately before the final edit so a concurrent write landing mid-window is detected and reported rather than silently overwritten.

## Checklist

- [x] Slice 0: spec rationale extraction (pre-flight step 7) -> `docs/builder/bld-036-slice-0-rationale_extraction.md`
- [x] R1a: conformance audit — input generation, `FieldError` envelope, payload wrapper -> `docs/builder/bld-036-review-1a-inputs_envelope_payload.md`
- [x] R1b: conformance audit — `DjangoMutation` base, `Meta` validation, finalizer binding -> `docs/builder/bld-036-review-1b-base_meta_finalizer.md`
- [x] R1c: conformance audit — resolvers, field factory, write authorization, transaction boundary -> `docs/builder/bld-036-review-1c-resolvers_fields_writeauth.md`
- [x] R1d: conformance audit — products live write surface, G2 handoff, public exports, DoD -> `docs/builder/bld-036-review-1d-live_surface_g2_exports.md`
- [x] R2: spec reconciliation — spec states the current contract; rationale takes the history -> `docs/builder/bld-036-review-2-spec_reconciliation.md`
- [x] R3: code repair — **conditional** on a SKIPPED contract surviving the live-tree re-check -> `docs/builder/bld-036-review-3-code_repair.md`
- [x] Cross-slice integration pass -> `docs/builder/bld-036-integration.md`
- [x] Final test-run gate -> `docs/builder/bld-036-final.md`

## Conformance grading vocabulary (used by every R1 cohort)

One grade per contract row, so R2 knows where each row routes. A row may carry more than one grade; the artifact re-derives the count rather than asserting it.

- **CONFORMS** — the spec states it and `HEAD` implements it. No action.
- **SUPERSEDED** — `HEAD` implements something *different* on purpose, because later work changed it. **Routes to R2** (spec edit + `**Post-ship:**` bullet). Name the card or spec that changed it, or say the attribution could not be established.
- **STALE-DESCRIPTION** — the contract holds but the spec describes it wrongly (a wrong symbol path, a renamed helper, a false count, a falsified prediction). **Routes to R2.**
- **RENAMED** — the behavior is at a different symbol or path than the spec cites. **Routes to R2.**
- **SKIPPED** — the spec states it, nothing superseded it, and `HEAD` does not implement it. **This is the cycle's answer to "was anything skipped in the code" and routes to R3.** A SKIPPED grade owes a failability-style demonstration that the gap is real, not merely unfound: name the test that would have to exist, and where you looked.

**A SKIPPED grade is checked against the live working tree before it becomes work.** The concurrent session may already have closed it; R3 records that and repairs nothing.

## R1 outcome (all four cohorts `review-accepted`)

| Cohort | Rows | CONFORMS | SUPERSEDED | STALE-DESCRIPTION | RENAMED | **SKIPPED** | Not verifiable |
|---|---|---|---|---|---|---|---|
| R1a — inputs / envelope / payload | 85 | 69 | 7 | 5 | 3 | **1** | — |
| R1b — base / `Meta` / finalizer | 64 | 52 | 3 | 7 | 2 | **0** | — |
| R1c — resolvers / fields / write-auth | 72 | 47 | 20 | 4 | 1 | **0** | — |
| R1d — live surface / G2 / exports | 70 | 54 | 4 | 10 | 0 | **1** | 1 |
| **Total** | **291** | **222** | **34** | **26** | **6** | **2** | **1** |

Each cohort's grades sum to its own row count and the column totals sum to 291; every figure was re-derived by its cohort off the rendered table rather than asserted, and re-derived again here.

**The prediction held.** The plan predicted SUPERSEDED, not CONFORMS, as the default on the resolver and permission surface, and warned that an all-CONFORMS return from R1c would mean the spec had been graded against itself. R1c returned **20 SUPERSEDED against 47 CONFORMS** — by far the highest divergence rate of the four cohorts — and 0 SKIPPED. The write pipeline is not under-built; it is under-described.

### The two SKIPPED contracts

1. **R1a — an undischarged staged anchor.** `tests/mutations/__init__.py #"TODO(spec-036 Slice 1)"` survives at `HEAD` for a slice that shipped in `0.0.11`. The spec's own `## Implementation plan` says such an anchor is `#"removed in the change that ships the slice"`, and `AGENTS.md` rule 26 plus `docs/builder/BUILD.md`'s integration-pass step 6 make discharging it the shipping slice's contract. **Why it rotted for four release lines: no gate greps for it.** Verified by Worker 0 — `grep -rn 'TODO(spec-'` over `scripts/`, `.pre-commit-config.yaml`, and `.github/workflows/` returns nothing. Tree-wide, 26 staged spec anchors survive across `*.py`, one of them naming `spec-035`, which also shipped.
2. **R1d — the live write-authorization denial matrix is pinned for `create` only.** The `## Test plan` live tier and DoD item 5 both demand that "a caller lacking the `add` / `change` / `delete` model perm is denied"; `updateItem` / `deleteItem` have no denial row in any live flavor. Population established from the single denial message string: `grep -rc 'Not authorized'` over the live tier → 9 hits in `test_products_api.py` attributing to 8 tests, **every one a create**. The behavior itself ships — the per-operation matrix is pinned at package tier by `tests/mutations/test_permissions.py::test_create_perm_does_not_authorize_update_or_delete` and `::test_change_and_delete_perms_authorize_their_operations` — so what is missing is the **tier the spec assigns it to**, not the guarantee.

**A third staged anchor is RENAMED, not SKIPPED.** `tests/test_permissions.py #"TODO(spec-036 Slice 3)"` stages a lookup-scoping pin that **did land**, in two other files — Worker 0 confirmed `tests/mutations/test_resolvers.py::test_hidden_row_update_is_not_found_no_existence_leak` and `tests/mutations/test_permissions.py::test_hidden_row_is_not_found_before_auth_signal_no_existence_leak` both exist at `HEAD`. R1a graded it SKIPPED and R1b graded it RENAMED; **R1b is correct**, so its repair is anchor removal, not test authoring. Recorded because the two cohorts disagreeing on one row is exactly what the partition is supposed to surface.

### The four High findings, all verified by Worker 0 against source before any dispatch

Per `docs/builder/BUILD.md` `### Worker 0 verifies every finding against source before dispatching`:

1. **The spec instructs a construction that now fails loudly (R1c H1, R1d).** `grep -o 'DjangoSchema'` on the spec → **0**; `strawberry.Schema` → **6**. Slice 4 says to wire `mutation=Mutation` into `strawberry.Schema(...)`, while `HEAD`'s `utils/write_transaction.py::require_managed_write` raises `ConfigurationError` **before any DB work** for a generated mutation reached through a plain `strawberry.Schema` — and `examples/fakeshop/config/schema.py` at `HEAD` builds `DjangoSchema(...)`. A consumer following the spec literally gets a non-functional write surface. **The most consumer-damaging defect in the cycle**; all six sites must be fixed in one R2 pass, and two of them sit in R1b's and R1d's spec territory.
2. **Decision 8's transaction boundary is wrong in extent, owner, and failure surface (R1c H2).** Three spec sites say "steps 3-6 inside one `transaction.atomic()`". At `HEAD` the `atomic()` opens before the *locate* (the row lock requires it), is nested inside `schema.py::DjangoMutationExecutionContext`'s completion-spanning transaction, and every error-envelope return calls `set_rollback` first.
3. **Decision 8 step 5 contradicts the spec's own no-visibility-leak guarantee (R1c H3).** The spec says M2M related objects "resolve through the target model's **default manager**" at four sites; `HEAD`'s `utils/write_values.py::decode_visible_relation_ids` type-checks every id and then confirms the whole set in one **visibility** query through the related primary's `get_queryset`. The spec asserts both contracts and they are incompatible; `HEAD` implements the safe one.
4. **`FieldError`'s freeze claim is false and was pinned by zero test rows (R1a, R1d).** Decision 2 / Decision 7 promise `038` / `039` "reuse the byte-identical type". `spec-039` (commit `951945b7`) added `codes` and `path`, so the type has **four** fields at `HEAD`, not two — and its shipped docstring still says "Defined and frozen here (spec-036 Decision 7)" immediately above the two additive fields it documents. Nothing failed when the shape changed because exactly one site tree-wide inspects the type and it builds a name→field dict then asserts two entries, with no `len` and no set equality anywhere. **The spec's strongest promise had no gate.**

### Contract-level findings escalated to the maintainer, not dispatched

Per `docs/builder/BUILD.md` `### Contract-level findings are escalated as maintainer decisions before dispatch`:

- **The `0.0.14` write hardening has no owning spec (R1c, structural).** Nine specs carry the `0_0_14` version segment and none of them scopes it; Worker 0 confirmed by grepping the whole `docs/SPECS/` corpus for `select_for_update` / `write_transaction` / `DjangoMutationExecutionContext` — the top hit is `spec-039` (10), the serializer card at `0.0.13`. So `spec-036` is the corpus's only spec-level description of a pipeline it did not scope, and 13 of R1c's rows have nowhere to be homed. The board already knows the surface is undocumented (`KANBAN.md` records the shipped always-on `atomic()` baseline as "given, commit `1b06c39e`", and a separate card item notes the atomicity guarantee "is stated nowhere") but no spec owns it. **This is the recurrence of a known class** — a surface with no owning spec silently inverts the specs describing it, previously homed on cards `051` / `052` / `064` by the `033` cycle.
- **Two DRY ownership findings, both cross-flavor and both refactors of concurrent-dirty files.** R1a N6: the neutral `utils/` layer three write flavors share depends **upward** on `mutations/inputs.py` for `FieldError`, paid for with two function-local imports whose stated purpose is dodging an import cycle. R1b DRY-1: `mutations/sets.py` (1,606 lines) has become the cross-flavor write substrate — 25 distinct symbols imported out by `forms/sets.py`, `rest_framework/sets.py`, and `auth/mutations.py`, **4 private-by-name** and **6 helpers with zero caller inside `mutations/`** — with `sets_mixins.py` the exact precedent and the home Decision 4 predicted. Each cohort recorded three resolution paths and neither held at `revision-needed`.
- **184 review-finding tags across 34 grammars survive in the spec** (`AR-H#` / `Major-#` / `Medium-#` / `CR-#` / `DRY-#` / `Low-1` / `P1`-`P2`), recorded by Slice 0. A tag is a lookup key into the companion rather than a chronology, and both precedents left the shape standing.

**Stated positively so a later pass does not undo it (R1c):** four write flavors ride one `run_write_pipeline_sync` skeleton and three share `make_resolver_entries`, with **zero** cross-flavor near-copies. The DRY risk here is un-sharing, not duplication.

### Process defect in Worker 0's own dispatch, recorded

Three concurrent cohorts were pointed at one shared memory file, `docs/builder/worker-memory/worker-3-036.md`, and R1c reported it was being **clobbered rather than appended** — R1a's entry had already been replaced by R1b's. Cycle-scoped-per-role was the wrong granularity for concurrent same-role cohorts; per-cohort files would have been correct. No content was lost, because every cohort's findings live in its own artifact, which is exactly why `docs/builder/BUILD.md` makes the artifact the contract and memory a private notebook.

## Final gate outcome (`final-accepted`)

**Gate commands, in `docs/builder/BUILD.md` `## Final test-run gate` order.**

| Command | Result |
|---|---|
| `uv run pytest --no-cov -q` | 4 failed, **7119 passed**, 42 skipped — all 4 pre-existing, see below |
| `uv run python examples/fakeshop/manage.py check` | PASS, exit 0 |
| `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | PASS, exit 0 |
| `uv run ruff format --check .` | PASS, exit 0 |
| `uv run ruff check .` | PASS, exit 0 |
| `git diff --check` | exit 2 tree-wide / **exit 0 scoped to this cycle's files** — the plan's recorded 4-line `docs/feedback2.md` baseline exception |

**The four failures are the concurrent session's, attributed at occurrence level and escalated rather than graded against this cycle.** Per `docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`, a failing test is **not worker-verifiable at `HEAD`** — reproducing it needs a clean tree, which only the maintainer can run — so the obligation is discharged by recording plus escalating:

- `tests/optimizer/test_walker.py::test_divergent_key_windows_shared_payload_uses_none_key` — `ConnectionWindowBounds` occurs **0** times in `optimizer/nested_planner.py` at `HEAD` and **5** times live (dirty `31/32`); the class exists at `HEAD` only in `utils/connections.py`. The failing row sits at line 3568 while R3's hunks in that file are at line 28 and lines 4775-4848.
- Three rows on `ActiveInputPermissionAttrs.__init__() got an unexpected keyword argument 'unset_sentinel'` — the keyword is **declared** at `HEAD` and **removed** live in `sets_mixins.py` (dirty `41/39`), while `tests/orders/test_inputs.py` is **clean at `HEAD`**. A clean test file failing against a dirty production file is sharper evidence of attribution than diff locality.

**Nothing in R3's diff fails.** R3 deliberately left the walker row un-re-pinned because that contract is mid-flight in another session, which `AGENTS.md` rule 34 and this cycle's scope both require.

**Floor verification.** One scope for the whole cycle, owned by R3's builder pass and discharged there; the gate corroborated it read-only rather than re-running it, per `docs/builder/BUILD.md` `## Floor verification` ("the backstop confirming it happened, not a second owner"). Scratch venv outside the repo, every install carrying an explicit `--python`, shared `.venv` never written to. Resolved: Python **3.10.19**, django **5.2.16**, strawberry-graphql **0.316.0**. New live rows → `3 passed`; whole `test_products_api.py` → `132 passed`.

**Round-status chain.** Every `bld-036-*.md` artifact's `Status:` line was read on disk before the final checkbox was ticked; all nine read `final-accepted`, with none left `built`, `review-accepted`, or `revision-needed`.

**Tree state at hand-off.** `grep -rn --include='*.py' 'TODO(spec-036' .` → nothing; no `ACTIVE-MUTATION.json`; every failability-proof target's `git diff --numstat HEAD` at its recorded pass-start figure, so no mutation was left live and no concurrent write was overwritten.

### What the cycle answered

**"Was anything skipped in the code?" — two contracts, both now closed.** Against 291 graded contract rows, exactly two were SKIPPED: an undischarged staged `TODO(spec-036 Slice 1)` anchor, and the live write-authorization denial matrix being pinned for `create` only. Everything else the spec promised is built. **The write pipeline was not under-built; it was under-described** — R1c returned 20 SUPERSEDED against 47 CONFORMS.

**The most consumer-damaging defect was in the spec, not the code.** The spec instructed `strawberry.Schema(...)` at six sites and named `DjangoSchema` zero times, while `utils/write_transaction.py::require_managed_write` refuses the write with a `ConfigurationError` before any database work. A consumer following the spec literally got a dead write surface. Fixed at every site.

**The cycle's headline quality finding:** `FieldError` grew from two fields to four (`spec-039`, commit `951945b7`) and **nothing failed**, because the single site inspecting the type built a name→field dict and asserted two entries with no `len` and no set equality. The spec's strongest promise — "reuse the byte-identical type" — had no gate at all. Now it has one, and removing a member fails 2 named rows.

## Deferred-work disposition

`docs/builder/bld-036-final.md` `### Deferred work catalog` carries **21 items**, plus a deliberate second list of **6 items the artifacts route forward that this cycle actually closed**, struck so the next author does not go fix what is already fixed.

The load-bearing five:

1. **The `0.0.14` write hardening has no owning spec.** Nine specs carry the `0_0_14` version segment and none scopes it; the corpus-wide grep's top hit is `spec-039` (10 occurrences), the serializer card at `0.0.13`. Maintainer Decision A deferred **10 of R1c's rows** on these grounds (`X3`-`X12`; `X13` partially discharged). `spec-036` is **not** that spec. A recurrence of a known class — a surface with no owning spec silently inverts the specs describing it — previously homed on cards `051` / `052` / `064`.
2. **The broken Decision-8 heading-slug defect is live in two sibling specs**: `spec-038` (36 dead uses) and `spec-039` (34), the same defect Slice 0 repaired here where it had 16.
3. **`mutations/inputs.py::FieldError`'s docstring still claims the type is "frozen … byte-identical"** three lines above the two additive fields it documents. The file is baseline-dirty (`31/38`) with the concurrent session's work, so this cycle could not touch it.
4. **No automated gate greps for staged `TODO(spec-<NNN>)` anchors anywhere** — verified absent from `scripts/`, `.pre-commit-config.yaml`, and `.github/workflows/`. That absence is why this card's two anchors rotted for four release lines. 24 anchors naming other specs survive, one of them (`spec-035`) shipped.
5. **`examples/fakeshop/apps/products/services.py::create_users`' docstring calls `staff_<n>` a superuser** while the code sets `is_staff=True` only. It matters because `delete_users` never deletes superusers, so a reader trusting the docstring expects `staff_<n>` to survive `delete_users all`. The file is clean at `HEAD` and so is technically inside this cycle's file-type scope, but it is unrelated to any `spec-036` contract — deferred rather than widening the cycle. A ready-to-fix one-liner.

## Hand-off

Every checklist item is `- [x]` and every artifact reads `final-accepted`. Per `docs/builder/BUILD.md` `## Slice handoff`, Worker 0 stops driving here: the maintainer reviews the whole cycle and commits at their discretion.

**Closeout is NOT run.** It requires the maintainer's commit and a commit range, and this cycle's maintainer-set scope excludes closeout agentflow edits — `docs/builder/BUILD.md`, `docs/builder/ARTIFACT.md`, and the four role files are untouched.
