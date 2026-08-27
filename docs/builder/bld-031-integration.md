# Build: Cross-slice integration pass — spec-031 (globalid_encoding / 0.0.9), residual reconciliation cycle

Spec reference: `docs/SPECS/spec-031-globalid_encoding-0_0_9.md` (whole file, read end to end)
Rationale companion: `docs/SPECS/appx/spec-031-globalid_encoding-0_0_9-rationale.md` (whole file, read end to end)
Build plan: `docs/builder/build-031-globalid_encoding-0_0_9.md`
Status: final-accepted

**This artifact carries the integration pass, its consolidation cohort, and the pass's re-run.** The
findings inside the spec/companion pair are fixed under `## Spec changes made (Worker 1 only)`; the three
source-comment sites are dispatched at `### Dispatched findings checklist`, built, reviewed, and audited
at `## Final verification (Worker 1, re-run)`, which closes the cycle for `bld-031-final.md`.

---

## What this pass is, in this cycle

`docs/builder/BUILD.md` `## Cross-slice integration pass` is written for a cycle that landed source. This
one landed **none**: all five functional slices plus Slice 0 closed by procedural closure with empty CODE
GAP lists and **zero** Worker 2 dispatches. `git status --short` at the start of this pass carries only
this cycle's own eight paths (one modified spec, seven untracked), HEAD `5ebcfe9c`. So the ordinary DRY
targets have no diff to find them in, and the standard checks that read a diff or a shadow overview are
recorded not-applicable below rather than performed theatrically or dropped in silence.

What replaces them is the check no single slice could run. Five slices each rewrote their own region of one
spec; nothing had read the result end to end as one document. This spec states each contract in several
homes by design — a numbered Decision, a `## Slice checklist` sub-bullet, `## User-facing API` /
`## Error shapes`, `## Edge cases and constraints`, `## Test plan`, `## Implementation plan`,
`## Definition of done` — and the redundancy is legitimate; two homes disagreeing is not. This cycle had
already proved the failure mode twice (Slice 2's five-homes filter contract, Slice 5's case-(d) dating that
Slice 1 itself authored), and the regions edited **after** Slice 1 had still not been cross-read by anyone.

---

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable in the code sense and deliberately skipped: this pass plans
  no new helper, shared constant, validation branch, coercion utility, or test helper, and the Worker 2
  work it does plan is **comment-only** — three docstring/comment sites, zero executable change. The
  package-wide inventory `worker-1.md` `### Package-wide helper inventory before helper planning` gates is
  a gate on *helper planning*; there is none to gate. The DRY question this pass does own is claim
  duplication across the spec's regions, which is what the whole cross-home walk below is.
- **Existing patterns reused.** The `**Post-ship:**` bullet convention Slices 1-5 established in the
  rationale companion, keyed to a spec Decision by heading and anchor; five bullets appended, no new
  section and no new shape. For the Worker 2 plan, the shipped comment style of the three target
  docstrings (spec-Decision provenance pointers kept, per `AGENTS.md` rule 27's KEEP list).
- **New helpers justified.** None.
- **Duplication risk avoided.** Two. (a) The naive fix for the Implementation-plan count divergence is to
  re-type the Test plan's enumeration into the table cell; instead the corrected cells state the measured
  totals and point at the [Test plan](#test-plan) for the enumeration, so one home owns the names.
  (b) The Worker 2 comment fixes must not restate the spec: each corrected clause states the invariant and
  keeps its existing `spec-031 Decision N` pointer, rather than pasting the Decision's prose into source.
- **Consolidation candidates: none, and the readers were checked before saying so** (`worker-1.md`
  `## Integration pass` delta). The only shapes this cycle touched that could look like duplication are
  the strategy frozensets and the two error formatters, and all of them are **live single-sitings with
  multiple readers**, not dead pairs: `types/relay.py::MODEL_LABEL_STRATEGIES` / `::TYPE_NAME_STRATEGIES`
  are read by `::encode_typename`, `::_accepts_model_label_decode` / `::_accepts_type_name_decode`,
  `types/finalizer.py::_emits_model_label`, and `filters/base.py` (which **derives**
  `FRAMEWORK_GLOBALID_STRATEGIES` from their union rather than re-typing it);
  `filters/base.py::resolve_globalid_target_definition` has two readers by construction (the build-time
  audit and the runtime backstop) and that is the point of it. Nothing here is delete-and-trim material.

### Implementation steps

Executed in this pass, in order.

1. Read `AGENTS.md`, `START.md`, `docs/builder/BUILD.md`, `docs/builder/ARTIFACT.md`,
   `docs/builder/worker-1.md`, the build plan, the spec, the rationale companion, and **all six** prior
   `bld-031-*.md` artifacts in slice order (integration-pass step 1; no "as needed").
2. Re-read `git status --short` and confirm the plan preamble's baseline-dirty list is stale (below).
3. Re-run the mechanical gates myself rather than inheriting them: the staged-anchor sweep,
   `check_spec_glossary.py`, `check_citations.py`, the markdown scaffold check, and a full anchor /
   link-definition / cross-file-fragment resolution pass over both files.
4. Walk every contract through all of its homes (`### Cross-home contract walk`), prioritizing the ones
   this cycle's slices edited, and re-derive every stated count.
5. Check the spec/companion pairing as a pair (`### Spec / companion pairing`).
6. Walk every accepted slice artifact's deferral sections for an item still drifting without a named owner
   (`### Step 5 — deferred follow-up walk`).
7. Fix every in-fence finding, append the reasoning to the companion, and re-run the gates.
8. Re-open the batched source-comment judgement and write the Worker 2 plan.

### Test additions / updates

None from this pass. The Worker 2 pass owes **no** test change: its diff is comment-only and its obligation
is the inverse proof that executable bytes are unchanged, spelled out in
`### Dispatched findings checklist` below. Adding a test to a comment-only diff would be the wrong shape.

### Implementation discretion items

- The exact wording of the three corrected comments, within the contract each must state. Assessed and
  delegated: the contracts are pinned below sentence by sentence; the phrasing is Worker 2's.

### Dispatched findings checklist

Three source sites, one cohort, comment-only. Boxes stay `- [ ]` at planning; Worker 2 ticks a box only
when the fix lands in its diff; Worker 1 audits the ticks at the re-run of this pass.

- [x] **F-1 — `django_strawberry_framework/types/definition.py::DjangoTypeDefinition`
      #"the filter falls back to node-id-only validation"** (raised by Slice 1, batched by Slice 2). The
      invariants docstring, describing the `effective_globalid_strategy` slot, says a `None` recorded
      strategy means the filter "falls back to node-id-only validation (spec-031 Decision 13)". **False
      since the `0.0.14` hardening.** Shipped `filters/base.py::_decode_and_validate_global_id` fails
      **closed** on a known `None` — the guard is spelled `if strategy not in FRAMEWORK_GLOBALID_STRATEGIES`
      and raises a `GraphQLError` carrying `extensions={"code": "GLOBALID_UNVALIDATABLE"}` — before
      `::_accepted_globalid_type_names` is consulted at all, and that helper's own docstring in the same
      package says so. The clause to state instead: a known `None` recorded strategy is rejected at request
      time by the runtime backstop; the **only** surviving node-id-only path is the unbound-owner /
      unresolvable-target case, where no definition and therefore no strategy exists. Keep the
      `spec-031 Decision 13` pointer.
- [x] **F-2 — `django_strawberry_framework/types/relay.py::encode_typename`
      #"so this branch is the live implementation for exactly that shape"** (raised by Slice 2). The
      `type`-branch docstring bullet carries the exclusivity framing `DONE-032-0.0.9` falsified: shipped
      `testing/relay.py::global_id_for` calls `encode_typename` directly with a type's recorded strategy
      and reaches that branch with no installed closure. The clause to state instead is the membership half
      the spec's Decision 10 now carries: the shadow-install is the only way a `type`-strategy type carries
      a framework closure, hence the only route into this branch **during `id` resolution**;
      `testing/relay.py::global_id_for` reaches it directly.
- [x] **F-3 — `django_strawberry_framework/types/relay.py::decode_global_id`
      #"WIP-ALPHA-032-0.0.9"** (raised by Slice 3). The docstring reads "It is the forward-looking piece
      root ``node(id:)`` / ``nodes(ids:)`` (``WIP-ALPHA-032-0.0.9``) will consume - no shipped ``0.0.9``
      path calls it yet". **Both clauses are false**, and the card id is a stale `WIP-ALPHA-` spelling
      `AGENTS.md` rule 26 says is retired by the change that ships the slice. The card is `DONE-032-0.0.9`
      and the helper has three live callers: `relay.py::_decode_or_graphql_error` (root node fields, which
      converts the uniform `ConfigurationError` into a `GLOBALID_INVALID` `GraphQLError`),
      `relay.py::decode_model_global_id` (the write-side typed-id primitive the mutation flavors and the
      relation `<field>_id` decode share), and the `testing/relay.py` re-export. State the current
      consumption and drop the "no shipped path calls it yet" clause.

**Explicitly NOT in scope, and Worker 2 must not "fix" it.** Slices 2, 3, and 5 recorded this batch as
**four** clauses in three files, the fourth being
`django_strawberry_framework/types/relay.py::_install_typename_closure`'s docstring, said to carry "the same
falsified `type`-branch exclusivity claim". Re-derived at HEAD: it does not. That docstring says "``model``
/ ``type+model`` / ``callable`` always reach here; ``type`` reaches here only when shadowing a framework
closure inherited from a concrete Relay parent (otherwise ``type`` keeps Strawberry's default)" — a **true
membership claim about the install site**, which is precisely the half Slice 2's spec fix (S2) preserved.
The batch is three sites, not four. Leave that docstring alone.

Worker 2's obligations for this cohort, in full:

- **The inverse proof that executable bytes are unchanged** is mandatory and is the pass's central record
  (`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`, the
  relocated/carried-over-unchanged shape). Method, per touched file: `git show HEAD:<path>` into a scratch
  path **outside** the repo, then compare a docstring-stripped AST unparse of both revisions and confirm
  they are identical. Comments never reach the AST; docstrings do, so they must be stripped explicitly —
  a bare `ast.dump` comparison would show a difference and prove nothing. Quote the command and its output.
  Never `git stash` / `git checkout` / `git restore` / `git worktree`.
- **No failability proof is owed** — the pass introduces no boundary, guard, gate, or rejection path
  (`### What needs a proof, and what does not`). Record `None; this pass introduced no new boundary.`
- **`AGENTS.md` rule 17**: ASCII-only `.py` source. The three target docstrings currently use `-`, not an
  em dash; keep it that way. Line length 99, E501 graced to 110.
- **`AGENTS.md` rule 27 and the wrapped-citation hazard**: source refs stay symbol-qualified
  (`path::QualifiedName`, `path::QualifiedName #"unique substring"`), never `path:NN`. Do not reflow an
  existing citation across two lines — `scripts/check_citations.py` cannot see a wrapped one, so a reflow
  silently retires the gate. Run it after editing (`uv run python scripts/check_citations.py`).
- **No process provenance in comments.** State the invariant, never that a reconciliation cycle corrected
  it. The `spec-031 Decision N` pointers are on the KEEP list and stay.
- `uv run ruff format <the two files>` and `uv run ruff check --fix <the same two files>`, scoped — never
  `.` — then `git status --short`, and stop-and-report anything unexpected rather than reverting it.

### Plan declarations

- **Hot-path declaration:** `none`. Carried from the build plan and confirmed rather than inherited: the
  Worker 2 diff is comment-only, so no executable line on any path — hot or cold — changes, and the inverse
  proof above is what establishes that. The seams involved **are** hot (`types/relay.py`'s installed
  `resolve_typename` closure runs per emitted node `id`; `decode_global_id` runs per root `node(id:)` and
  per write-side typed id; `filters/base.py::_decode_and_validate_global_id` runs per filter value), so a
  *future* pass landing executable change in any of them owes a before/after number. Deliberate, not
  silence.
- **Floor-verification scope:** `none`. Same reason: no executable change reaches a Django / Strawberry /
  channels seam, and the inverse proof is the evidence. Had this cohort touched behavior in `types/` or
  `filters/`, the scope would have been focused `tests/types/` + `tests/filters/` at the floor in an
  isolated venv outside the repo, owned by that pass. Deliberate, not silence. The shared `.venv`'s own
  versions are not stated: this pass had no reason to read them and `## Floor verification` forbids
  stating them from memory.
- **Ownership partition:** `none; sequential slices`. One cohort, two files, no concurrency.
- **Boundary count (split trigger):** **0**. No guard, cap, rejection path, or validation branch is added.
  The split question is answered and the answer is no: the three sites are one unit because they are one
  edit shape (a false or over-claiming sentence in a docstring), share one proof obligation, and two of
  them are in the same file.

---

## Required integration-pass steps

### Step 1 — every prior artifact read, in slice order

All six read end to end, not sampled: `bld-031-slice-0-rationale_extraction.md`,
`bld-031-slice-1-meta_key_setting_precedence.md`, `bld-031-slice-2-encode_seam.md`,
`bld-031-slice-3-decode_seam.md`, `bld-031-slice-4-live_http.md`, `bld-031-slice-5-docs_wrap.md`. Their
carried-forward items are walked at `### Step 5 — deferred follow-up walk`.

### Step 2 — the static inspection helper

**Not applicable, with the reason recorded.** `scripts/review_inspect.py` must have run or been explicitly
skipped for every Python file with review-worthy logic **the build touched**. This build touched **no**
Python file: all six passes were `.md`-only, every CODE GAP list was empty, and no Worker 2 ran. There is
therefore no file in the population the step ranges over. Each slice recorded the same skip with the same
reason (Slices 1-5, `### Static inspection helper` / `### scripts/review_inspect.py`), and Worker 0's
pre-flight step 2 exercised the helper once against `types/relay.py` (exit 0) purely as a smoke check.

Forward-looking, because the dispatch above changes the population: the Worker 2 cohort touches
`types/definition.py` and `types/relay.py`, both under `types/`, which is a `### When to run the helper
during build` trigger for Worker 3. It is **not** a trigger for this planning pass — the rule fires when
"the plan **adds logic**" to such a file, and this plan adds none — and Worker 3 may record the same skip
against the same reason once the inverse proof shows the executable surface unchanged. Recording that here
so the next pass does not have to re-derive whether it owes a run.

### Steps 3 and 4 — the shadow-overview comparisons

**Both not applicable, with the reason recorded.** Step 3 compares the **Repeated string literals**
sections across every shadow overview to find cross-file literal duplication; step 4 compares the
**Imports** sections to confirm one-way dependency direction. Both read shadow overviews produced by slices
that wrote code. No slice in this cycle wrote code, so `docs/shadow/` holds only Worker 0's single
pre-flight smoke output plus Slice 1's package-wide helper inventory — one file's overview and an index,
which is not a cross-slice comparison set. There is nothing to compare across, and generating overviews now
would compare the shipped `0.0.14` tree against itself, which answers a question this cycle did not ask.

The cross-file literal and import questions were nonetheless answered, by the route available to a cycle
with no diff: Slices 1-4 each grepped the whole package for their slice's shapes and recorded the result in
`### DRY analysis`, and this pass's own reader-check (above) walked the strategy frozensets, the derived
`FRAMEWORK_GLOBALID_STRATEGIES`, and the shared target resolver across `types/` and `filters/`, confirming
the `filters -> types` import direction is one-way and acyclic and that every literal is typed once.

### Step 5 — deferred follow-up walk

Every accepted artifact's `What looks solid` / `### Notes for Worker 1 (spec reconciliation)` /
`### Handed forward` / `### Deferred to ...` section, walked for an item that should land here rather than
in the catalog. Two long-orphaned items reached Slice 5 only because they were explicitly routed; the check
is that nothing else is drifting the same way.

| Item | Raised by | Disposition |
|---|---|---|
| `install_globalid_typename_resolver` arity contradiction | Slice 0 (note 1) | Discharged by Slice 2 (S1). Re-verified: one spelling at 2 sites, both three-arg. |
| DoD item 1's stale terms-CSV claim | Slice 0 (note 2) | Discharged by Slice 5 (edit 5) across four homes. Re-verified. |
| Decision 1's pre-archival `docs/spec-031-…` path | Slice 0 (note 3) | Discharged by Slice 5 (edits 2/3/4/5/7). Re-verified: `grep -n 'docs/spec-031' <spec>` → zero. |
| `types/definition.py` node-id-only docstring | Slice 1 | **Was drifting: routed to "a future pass" with no named owner.** Taken here as F-1. |
| `types/finalizer.py::_warn_model_label_secondary_collapse` unowned | Slice 1 | Discharged by Slice 2 (S7) across four homes. Re-verified: 5 homes now name it, all consistent on "warns (never raises)". |
| `encode_typename` / `_install_typename_closure` exclusivity docstrings | Slice 2 | **Was drifting, unowned.** Re-derived: one real site, not two. Taken here as F-2; the `_install_typename_closure` half withdrawn as a mis-attribution. |
| `_first_model_label_emitter` / `_audit_model_label_routing` no-definition raises | Slice 2 | **Judgement confirmed, closed** — see `### Known-open item 2` below. |
| `decode_global_id` `WIP-ALPHA-032-0.0.9` docstring | Slice 3 | **Was drifting, unowned.** Taken here as F-3. |
| `TODAY.md:14` phrasing | Slice 4 → Slice 5 | Closed by Slice 5's audit: accurate on its own terms, no doc obligation implied. No owner needed. |
| G4 Browse-by-category slash ambiguity | Slice 5 | Not a defect (the glossary satisfies the better reading) and out of fence. Catalog item, owner **maintainer**. |
| `spec-032` cross-references into moved text | Slice 0 (note 4) | Out of fence for the whole cycle. Catalog item, owner **maintainer**; population re-derived below. |

Nothing else was drifting. Every item now has a named owner or is closed.

### Step 6 — staged-anchor sweep

Re-run here rather than inherited from Slice 5, because it is a stated finding like any other:

```shell
grep -rEn 'TODO\(spec-031|TODO-(ALPHA|BETA|STABLE)-031' . \
  | grep -v '^\./\.git/' | grep -v 'KANBAN.md\|KANBAN.html\|BACKLOG.md'
```

**Clean: no surviving anchor in any shipped source, test, or comment.** **Eight** hits, every one prose
*describing* an anchor rather than being one:

- `docs/SPECS/spec-031-…md:76` and `:419` — the Slice-4 checklist and plan row recording that the anchor
  "is removed by this slice";
- `docs/SPECS/appx/spec-031-…-rationale.md:413` — Slice 4's post-ship bullet recording the same deletion;
- `docs/builder/bld-031-slice-0-…md:233`, `bld-031-slice-4-…md:80`, and `bld-031-slice-5-…md:141` and
  `:339` — prior artifacts' own sweep records;
- `docs/SPECS/appx/spec-022-export_schema-0_0_7-rationale.md:350` — a **card-renumber history row**
  (`| Debug-toolbar middleware | TODO-ALPHA-031 for 0.0.12 | DONE-042-0.0.14 |`), naming a *different* card
  that once held the number 031, in a table whose purpose is to record the renumber. Not a staged anchor,
  and out of fence.

Slice 5 reported **six**; the delta is exactly the two hits in Slice 5's own artifact, written after its
sweep ran. Re-measuring rather than inheriting is what makes that attributable instead of alarming. The
excluded board files carry no `031` anchor either. Nothing routes back to a slice.

---

## Cross-home contract walk

Every contract this cycle's slices edited, walked through all of its homes. Five disagreements found; all
five are inside the spec/companion pair and all five are fixed in this pass.

### Mechanical sweeps that came back clean

| Sweep | Method | Result |
|---|---|---|
| Signature spellings across every home | `grep -on '<symbol>([^)]*)' <spec> \| sort -u`, per symbol | One spelling each. `install_globalid_typename_resolver(type_cls, definition, globalid_setting)` ×2; `_resolve_globalid_strategy(definition, globalid_setting)` ×6; `_validate_globalid_strategy` in its two licensed forms (the `(meta, value, relay_shaped, *, source="meta")` definition and the `source="setting"` call) ×4; `encode_typename(definition, strategy, type_cls, root)`; `decode_global_id(gid: relay.GlobalID \| str)`. Companion agrees with the spec at every site. |
| Callable-encoder arity across every home | same, on `(type_cls, model[^)]*)` | `(type_cls, model, root)` everywhere in the spec except Decision 6's deliberate rejection example, which names the superseded four-arg shape and (after Slice 5's S5-3) asserts no date. The companion's `(type_cls, model, node_id, info)` / `(type_cls, model, root, info)` spellings sit only inside Revision-history and claim-retired bullets, which is where a superseded signature belongs. |
| The fail-closed filter contract, the five-homes case | line-set comparison across `GLOBALID_UNVALIDATABLE`, `_audit_globalid_filter_strategies`, "known `None`", "unbound-owner" | Consistent across all seven homes (checklist box 5, both `## Error shapes` bullets, Decision 13, plan row 2, `## Edge cases`, DoD 4, and the filter/finalizer test lists): build-time audit keys on the two encode-only names, the runtime backstop additionally rejects a known `None`, only the unbound-owner case keeps node-id-only. Slice 2's S3 holding. |
| Census claims (`the only` / `the one` / bare singulars) | grep the quantifier **and** the subject (`caller`, `path`, `branch`) | One survivor, Decision 10's shadow-install sentence, correctly scoped to "during `id` resolution" with the `testing/relay.py::global_id_for` carve-out in the same sentence. Slices 2 and 3 holding. |
| Chronology residue after the Slice-0 move | `grep -nE 'Revision [0-9]\|review finding\|Rev [0-9]\|\(P[0-9]'` over the spec | Zero. The spec narrates none of its own history. |
| Pre-archival spec paths | `grep -n 'docs/spec-031'` over the spec | Zero. Slice 5's S5-1 holding. |
| `_warn_model_label_secondary_collapse` | all 5 homes read | All say "warns (never raises)"; all scope the audit to multi-type models. |
| Rejected-alternative counts, spec pointers vs companion | count the bullets under each of the 13 `### Alternatives considered (and rejected)` sections; compare to the per-Decision `Rationale companion — … its <N> rejected alternatives` pointer | **All 13 match** (2, 1, 3, 3, 2, 3, 2, 6, 2, 3, 2, 1, 3), summing to the companion's stated **33**; the 13 `### Justification` sections carry **29** items, the companion's stated figure. The provenance block's "26 label lines became `###` headings" re-derives as 13 + 13. |
| `OK: 31 terms` | `check_spec_glossary.py`, and the claim's home count | Asserted in exactly one home (DoD item 1); the checker agrees. |
| Every `::test_*` citation in the pair | 93 distinct names extracted from both files and matched against every `def test_` in `tests/` and `examples/fakeshop/` | 92 resolve. One does not — finding **X-1** below. |
| The provenance block's "fourteen prose removals" | count the enumerated clauses; reconcile against Slice 0's own `What was DELETED, not moved` list | **Holds.** The sentence enumerates 15 clauses, of which Decision 4's `(breaking, pre-`1.0`)` tag is classified a *deletion* rather than a move in `bld-031-slice-0`'s separate list — 15 − 1 = 14. Recorded so the next pass does not re-open it; the enumeration reads as one clause over its own count until that reconciliation is stated. |
| Byte arithmetic in the provenance block | re-added | Internally exact: 24,609 + 16,870 + 4,453 = 45,932; + 2,235 = 48,167; − 5,732 = 42,435; 190,961 − 42,435 = 148,526. The *tense* around it was wrong — finding **X-2**. |

### X-1 — the companion cites a test name no file in the tree carries

**Home:** `docs/SPECS/appx/…-rationale.md`, Decision 7's Slice-1 `**Post-ship:**` bullet.

The bullet closed by naming the test that pins the constant coupling:
`tests/types/test_relay_interfaces.py::test_setting_error_subject_is_the_conf_key`. **No file in the
repository defines that name.** The shipped test is
`tests/types/test_relay_interfaces.py::test_setting_error_framing_tracks_the_conf_key_constant`
(`tests/types/test_relay_interfaces.py:2391`), and it asserts exactly what the bullet describes — the
`match=` argument **is** `conf.RELAY_GLOBALID_STRATEGY_KEY`, not a matching string literal. Only the
citation was invented; the claim it supports is true and the spec's Decision 7 is unaffected, because
Decision 7 names the constant rather than the test.

Found by sweeping the **whole population** rather than spot-checking: all 93 distinct `::test_*` names
across the spec and the companion, matched against every `def test_` under `tests/` and
`examples/fakeshop/`. Four apparent misses were the sweep's own false positives (`test_products_api`,
`test_library_api`, `test_kanban_api` are file stems; `test_model_label_routing_audit_` is a glob). This was
the one real miss, and no sampling method would reliably have found it: a test name invented from the
behavior it pins reads exactly like a measured one.

**Fixed** in the companion. Recorded there as a Decision 7 `**Post-ship:**` bullet.

### X-2 — the companion's own provenance measurement is present-tense, and this cycle falsified it

**Home:** `docs/SPECS/appx/…-rationale.md`, `## Provenance of this record`.

The block read "The spec on disk **now** measures **148,526** bytes over 670 lines". True when Slice 0 wrote
it; false by the end of the same cycle — Slices 1-5 added roughly 28KB of reconciliation and the spec
measures **178,300** bytes over 706 lines at the close of this pass. The figure is worth keeping (it is the
move's own accounting, and the byte reconciliation around it only reads if the post-move size is stated),
so the fix is tense, not deletion: it now says "immediately after the move" and states outright that it is
not a claim about the file's current size.

This is the inner-ring case Slice 5 named one level up: a dated claim written *during* reconciliation,
graded by nobody, because each slice checks what it inherits and not what it writes. Slice 0 could not have
caught it — the falsifying edits had not happened yet — and Slices 1-5 had no reason to re-read the
companion's provenance header. **Fixed.**

### X-3 — the `## User-facing API` example cannot finalize

**Home:** `docs/SPECS/spec-031-globalid_encoding-0_0_9.md`, `## User-facing API` → "Declaring a per-type
strategy" (a fenced `python` block), plus the sentence beneath it.

The example declares two Relay-Node `DjangoType`s over `models.Item` — `ItemType` with no `Meta.primary`
flag and `LegacyItemType` with `primary = False` — and closes by calling `finalize_django_types()`.
`registry.py::TypeRegistry.primary_for` returns `_primaries.get(model)`, and `_primaries` is populated only
by an explicit `primary=True` at registration, so `models.Item` is a multi-type model with **no declared
primary** and `types/finalizer.py::_audit_primary_ambiguity` collects it as an offender and raises
`ConfigurationError` on the example's own last line. The sentence beneath, asserting what each type's `id`
decodes to, therefore describes a schema that never builds. `primary = False` reads as "declares the other
one primary" and is indistinguishable from omitting the key.

Present at the spec's authoring commit and untouched by Slices 0-5, because **no functional slice owns
`## User-facing API`** — and invisible to every sweep the reconciliation ran, because the claim lives inside
a fenced code block. The spec's own contract sections state the primary rule correctly throughout
(`## Key glossary references`'s `Meta.primary` entry, Decision 8's invariant, `## Edge cases`); only the
executable example disagreed with them.

**Fixed:** `primary = True` on `ItemType.Meta`, with a comment saying why, and the sentence beneath now
states which side of the model-label-routing invariant the arrangement falls on (the only model-label
emitter is the primary, which accepts model-label decode, so the audit passes and
`_warn_model_label_secondary_collapse` stays silent).

### X-4 — the Implementation-plan table: half-measured rows, and a total its own rows falsify

**Homes:** `## Implementation plan` (the table's New-tests column and the closing total) against
`## Test plan` (which enumerates the same tests by name) and the shipped test files.

Two defects, one cause.

*(a) Two rows measured, two left as guesses.* Slice 3 replaced its `~14` with a measured **26** (21 + 5) and
Slice 4 replaced its `~6` with a measured **3 net-new + 16 migrated**. Rows 1 and 2 still read `~11` and
`~20`. Both are re-derivable from the spec's own Test plan, and both are low:

- **Slice 1 → 19**, not ~11: **15** in `tests/types/test_base.py` (the Test plan names 15; the shipped file
  carries exactly 15 `globalid`-strategy tests — 13 under the `# Meta.globalid_strategy + …` banner at
  `tests/types/test_base.py:978` plus the two un-inspectable-callable rows at `:329` and `:349`) **plus 4**
  finalization-scoped in `tests/types/test_relay_interfaces.py`, all four named by the Test plan's closing
  paragraph and all four present.
- **Slice 2 → 37**, not ~20: **23** in `tests/types/test_relay_interfaces.py` + **11** in
  `tests/filters/test_base.py` + **3** in `tests/filters/test_finalizer.py`. Every one of the 37 was
  confirmed to exist; the 11 filter rows were checked individually, since four of them
  (`test_filter_type_plus_model_accepts_both`, `::test_multi_value_filter_encode_only_reject_names_index`,
  `::test_filter_unbound_owner_node_id_only`, `::test_filter_wrong_model_rejected`) carry no `globalid` /
  `strategy` token and are invisible to the obvious grep — the "a finding's grep vocabulary is not its
  population" shape.

*(b) The total agrees with nothing.* "Total expected delta: ~750 lines" summarises five row estimates that
come to `+930 / -97`. Measured against what the card actually landed
(`git show --numstat 7d892d6f`, the card's single shipping commit): `+2,140 / -375` outside the build's own
`docs/builder/` artifacts — `+734 / -119` under `django_strawberry_framework/`, `+1,227 / -114` across the
three test trees plus the staged-anchor deletion in `examples/fakeshop/apps/products/schema.py`, and
`+179 / -142` across the standing docs, the terms CSV, and the spec itself. Cross-checked against git's own
summary: 2,140 + 5,267 (the eight `docs/builder/` files) = 7,407 insertions, and 375 deletions — both
matching `35 files changed, 7407 insertions(+), 375 deletions(-)` exactly.

**Fixed:** both cells now carry the measured count with its per-file split and point at the Test plan for
the enumeration; the section opener says which numbers are estimates and which are re-derived; the closing
sentence states the estimate sum and the measured delta side by side.

The cross-slice cause is worth naming: **a slice measures its own row and cannot see that its siblings were
left as guesses, and a total is a number no row owns.** Both are structurally invisible below this pass.

### X-5 — a Step-2 enumeration lost its newest member in one home

**Homes:** the Slice-3 `## Slice checklist` sub-bullet against Decision 8, `## Error shapes`, DoD item 5,
and the Slice-3 coverage sub-bullet.

Revision 4 (P1) added the **absent (`None`) recorded strategy** as a Step-2 rejection, and Decision 8, the
error-shapes list, DoD item 5, and the Slice-3 coverage bullet all carry it. The Slice-3 checklist's own
Step-2 parenthetical enumerated four states — `model`, `type`, `type+model`, `callable`/`custom` — and not
five, dropping exactly the member Revision 4 added, which is the member most likely to be missing because
it is the newest. Slice 3 edited this very bullet (its S7 appended the containment clause and the shared
frozensets) and did not notice, which is the ordinary outcome: **an enumeration is a count claim with no
number in it**, so nothing mechanical in the spec can see a member go missing. Only reading the five homes
against each other could.

**Fixed:** the member is restored to the checklist's Step-2 enumeration.

### Checked and deliberately left

- **Decision 11's heading still reads "no public export in `0.0.9`" while its body reads "No public export
  from this card".** Slice 3 assessed this (its divergence 4) and chose to reconcile the body and leave the
  heading, because renaming it changes the slug and breaks the `[spec-031-d11]` / `[rationale-d11]` anchor
  pair for no gain in accuracy. Confirmed rather than re-opened: the body's **first bold sentence** is the
  disambiguation, the `## Non-goals` entry is card-scoped, and the same paragraph names the same-release
  sibling export explicitly, so no reader reaches the ambiguous heading without immediately reading the
  correction. Re-opening an accepted slice's reasoned call with no new evidence is churn.
- **The companion's Risks item-1 preamble still says DoD item 1 "still says … intentionally absent from the
  CSV".** Present tense, and false since Slice 5's edit 5. Left, because the `**Post-ship:** … closed`
  bullet that supersedes it sits immediately beneath it — the file's documented shape for a superseded
  claim (the same shape the six `**Claim(s) retired.**` bullets use), and the companion is the one file in
  the pair that is *allowed* to carry chronology. Recorded so the next pass does not re-flag it.
- **`## Current state`'s two dated observations** (`_expected_global_id_type_name` as the live filter
  helper; no shipped `0.0.9` path reaching native `resolve_type`). Both were verified against the authoring
  commit `b1f82f0e` by Slices 2 and 3 and are licensed dated observations. Not re-derived here — a verified
  claim with its evidence recorded is done.

---

## Spec / companion pairing

The second cross-slice instrument, equally invisible per-slice: the two files are now a pair, and Slice 0
moved headings while Slices 1-5 edited them.

| Check | Result |
|---|---|
| Every `## Decision N` in the companion names its spec Decision by heading **and** anchor | **13 / 13.** Each opens with `Spec: [Decision N — <title>][spec-031-dN].`, and all 13 `[spec-031-dN]` definitions resolve to a real heading slug in the spec (fragment-checked, not just path-checked). |
| Every spec Decision carries its `Rationale companion —` pointer | **13 / 13**, and all 13 `[rationale-dN]` definitions resolve to a real heading slug in the companion. Plus `[rationale-risks]` → `#risks-and-open-questions`, which exists. |
| Every `**Post-ship:**` entry names a decision that exists | **34 entries** (36 occurrences of the marker, two of which are the file's own prose describing the convention). 24 sit under a `## Decision N` → `### Changes this Decision underwent`, spread over all 13 Decisions; 9 under `## Non-Decision deliberation`, the file's documented home for a finding belonging to no single Decision, each naming the spec sections it corrected (Test plan, Slice-N checklist, plan row, DoD item, `## Current state`, the `Status:` line); 1 under `## Risks and open questions`, against the risk item it closes. None is unlookuppable. Re-derived at the re-run: the pre-append figure was 29, and the five bullets this pass appended take it to 34. |
| No spec pointer names a companion section that is not there | Confirmed. All 15 spec→companion definitions resolve, fragments included. |
| No companion entry contradicts the spec's current text | **Two did** — X-1 (a test name the tree does not carry) and X-2 (a present-tense byte count this cycle falsified). Both fixed. Everything else was read against the spec's current wording and agrees. |
| Anchors, link definitions, cross-file fragments, both files | **0 dangling in-page anchors, 0 undefined ref-ids, 0 unused definitions, 0 broken definition paths, 0 dangling cross-file fragments** — spec 87 defs / 87 uses / 147 in-page anchors; companion 60 / 60 / 60. Includes every `GLOSSARY.md#…` fragment. Verified before and after this pass's edits. |

---

## Known-open items entering this pass

### Known-open item 1 — the batched stale `.py` comment clauses

**Judgement re-opened, and a Worker 2 pass is warranted.** Recorded as F-1 / F-2 / F-3 in
`### Dispatched findings checklist`.

Two things changed on re-derivation. First, the batch is **three** sites, not four: Slice 2's clause (c),
`types/relay.py::_install_typename_closure`'s docstring, does not carry the falsified exclusivity claim it
was said to — it states a true membership claim about the install site, which is the half Slice 2's own
spec fix preserved. So the count argument the maintainer offered ("four clauses is more than two") is
weaker than it looked, and it is not what decides this.

What decides it is the content of the two that are flatly false. F-1 is a **false statement about a
fail-closed boundary**, sitting in the invariants docstring of the definition module and contradicted by a
sibling docstring in the same package — the shape a maintainer reads to learn what `None` means and comes
away with the pre-`0.0.14` answer. F-3 carries a stale `WIP-ALPHA-032-0.0.9` card id, which `AGENTS.md`
rule 26 says is retired by the change that ships the slice; the card's own wrap missed it and no later card
owns `types/relay.py`'s docstrings, so there is no future pass this lands in by itself. `AGENTS.md` rule 5
forbids exactly that sequencing — "never offer defer-the-real-fix sequencing … shortcuts are never viable
even with a follow-up card." Routing these to the catalog with the maintainer as owner *is* the follow-up
card.

`### Isolation is non-waivable` holds even for a comment-only diff: Worker 0 dispatches Worker 2, then
Worker 3 as a separate spawn, then re-runs this pass. The two-spawn cost is real and is why Slices 2 and 3
each declined — correctly, from where they stood, each seeing one clause. Three sites in two files, one
proof obligation, and a false security-adjacent statement between them is a different trade.

### Known-open item 2 — the two unowned internal-consistency raises

**Judgement confirmed; not contracted; closed, no owner needed.**

`types/finalizer.py::_audit_model_label_routing` (`:412`) and `::_first_model_label_emitter` (`:436`) each
raise `ConfigurationError` when a registered type carries no `DjangoTypeDefinition`. Both were re-derived at
HEAD and both exist as Slice 2 described. They stay uncontracted, for the reason Slice 2 gave and this pass
re-checked: they assert an internal registry invariant that Phase-1 `_audit_primary_ambiguity` and the
registration path already guarantee, so a spec sentence would present an impossible state as a supported
consumer contract — the opposite of what a contract section is for. They are not untested: at least the
`_audit_model_label_routing` arm is pinned by
`tests/types/test_finalizer.py::test_model_label_routing_audit_rejects_a_missing_primary_definition`, which
monkeypatches the registry into the impossible state deliberately, and the package's `fail_under = 100`
gate covers the rest. Uncontracted is not unpinned. Recorded here so the next reader does not re-open it.

### Known-open item 3 — the `spec-032` cross-references into text that left `spec-031`

**Out of fence; maintainer-owned catalog item. Line numbers re-derived, and the population is larger than
the handoff said.** Slice 0 named three sites (13, 281, 452). `spec-032` has not been edited since, so those
numbers still hold — but they are three of **eight**, in four claim families. Stating each precisely so the
maintainer does not have to re-find them:

| `spec-032` line(s) | What it cites | What it now dangles on |
|---|---|---|
| `:13` | "recorded in full in [`spec-031`][spec-031] **Revision 7**" | `spec-031` has no `Revision 7` and no `## Revision history` at all. The entry is at `docs/SPECS/appx/spec-031-globalid_encoding-0_0_9-rationale.md` `## Revision history` → the **Revision 7** bullet; the specific delta `spec-032` is riding on is its **Delta (b)** sub-bullet (the callable encoder's `info` drop). |
| `:513` | "the precedent [`spec-031`][spec-031]'s build followed (its **Revision 6** swept the stale shipped-slice anchors)" | Same: no `Revision 6` in `spec-031`. Companion `## Revision history` → **Revision 6** → its `Hygiene` bullet. **Not in Slice 0's handoff.** |
| `:281` | "[`spec-031`][spec-031] **Decision 1** set the precedent of preferring the convention and recording the card's older name" | `spec-031`'s Decision 1 body now carries only the naming contract; its justification and both rejected alternatives moved to the companion's `## Decision 1` → `### Justification (moved from the spec)` / `### Alternatives considered (and rejected)`. Worth flagging while the maintainer is there: `spec-031`'s Decision 1 never recorded "the card's older name" in any revision — its two rejected alternatives were amending `spec-015` and two other topic slugs — so the characterisation was already loose before the move. |
| `:312` | "the same reasoning that rejected the global `resolve_typename` patch in [`spec-031`][spec-031] **Decision 3**" | The "Monkeypatch `strawberry.relay.GlobalID` / `Node.resolve_typename` globally" rejection moved to the companion's `## Decision 3` → `### Alternatives considered (and rejected)`. `grep -c 'Monkeypatch' <spec>` → 0. **Not in Slice 0's handoff.** |
| `:9`, `:143`, `:452`, `:464` | Four sites asserting that `spec-031` **Decision 11** "explicitly deferred the top-level `relay.py` module", "explicitly reserved" that home, or withheld the export "because 'no shipped `0.0.9` consumer'" existed | `spec-031`'s Decision 11 at HEAD names only `types/relay.py` and `testing/relay.py`; both the top-level-`relay.py` deferral and the quoted phrase were rejected-alternative / justification text and now live in the companion's `## Decision 11` → `### Alternatives considered (and rejected)` and `### Justification (moved from the spec)`. `grep -c 'no shipped `0.0.9` consumer' <spec>` → 0. Slice 0 named `:452`; `:9`, `:143`, and `:464` are new. |

Five `spec-032` citations that still resolve were checked and are fine and need no maintainer attention:
`:9`'s Decision 8 / 11 / 12 references (the Decisions exist), `:97` and `:385` (the Decision 6 net-new-key
rule, which stayed in the spec), `:304` ("the forward-looking helper `032` dispatches through" — the phrase
survives in `## Current state`), `:493` (Decision 12), and `:479` / `:634` (the "Slice-4 precedent", which
the checklist still carries). The distinction matters: the moved text is what dangles, not the pointer.

---

## Spec changes made (Worker 1 only)

Five edits, all triggered by this pass's cross-home walk. Line numbers are post-edit. The spec never
narrates its own history: each edit states the current contract directly and the reasoning is appended to
the rationale companion.

| # | File and site | Change | Finding |
|---|---|---|---|
| I1 | spec `:176` (`## User-facing API`, the fenced example) | `primary = True` added to `ItemType.Meta`, with a comment stating why (two `DjangoType`s share the model, so one must declare it) | X-3 |
| I2 | spec `:192` (the sentence beneath the example) | States that the arrangement satisfies the model-label-routing invariant and raises no secondary-collapse warning, with an in-page link to Decision 8 | X-3 |
| I3 | spec `:70` (Slice-3 checklist, decode sub-bullet) | The Step-2 enumeration regains its first member: **absent (`None`) → reject**, the candidate is not a framework-decodable Relay-Node type | X-5 |
| I4 | spec `:413`, `:417`, `:418`, `:423` (`## Implementation plan` opener, rows 1 and 2, closing total) | Opener now says which numbers are estimates and which are re-derived; row 1's `~11` → the measured **19** (15 + 4) with its per-file split; row 2's `~20` → the measured **37** (23 + 11 + 3); the closing "Total expected delta: ~750 lines" → the estimate sum `+930 / -97` beside the measured `+2,140 / -375`, split source / tests / docs | X-4 |
| I5 | companion `:20` (`## Provenance of this record`) | "The spec on disk **now** measures 148,526 bytes over 670 lines" → "**Immediately after the move** the spec measured …", plus an explicit sentence that the figure measures the move and is not a claim about the file's current size | X-2 |
| I6 | companion `:228` (Decision 7's Slice-1 `**Post-ship:**` bullet) | `::test_setting_error_subject_is_the_conf_key` → the shipped `::test_setting_error_framing_tracks_the_conf_key_constant` | X-1 |

### Rationale companion entries appended

Five `**Post-ship:**` bullets, append-only, in the convention Slices 1-5 established, each keyed to the
Decision or section it belongs to by heading and anchor:

- **`## Decision 7` → `### Changes this Decision underwent`** — the pinning test was cited under a name no
  file carries; the corrected name; why the spec's Decision 7 was unaffected; and the general shape,
  *a symbol-qualified citation is a claim like any other, and a test name invented from the behavior it
  pins reads exactly like a measured one*, with the population sweep (93 names, 92 resolving) recorded so
  the next pass knows it was a population and not a sample.
- **`## Decision 8` → `### Changes this Decision underwent`**, two bullets: (a) the `## User-facing API`
  example could not finalize — the `primary_for` / `_audit_primary_ambiguity` mechanism, why
  `primary = False` is indistinguishable from omitting the key, and *an example is executable prose, and a
  claim inside a fenced block is invisible to every sweep the reconciliation ran*; (b) Step 2's enumeration
  lost the member Revision 4 added, and *an enumeration is a count claim with no number in it*.
- **`## Non-Decision deliberation`**, two bullets: (a) the half-measured table and the total its own rows
  falsify, with both re-derivations and the cross-slice cause — *a slice measures its own row and cannot
  see that its siblings were left as guesses, and a total is a number no row owns*; (b) this file's own
  provenance measurement written in the present tense, and *a measurement of a change is not a measurement
  of the file*.

One link definition was added to the companion, `[spec-031-implementation-plan]`, in alphabetical position
under `<!-- docs/SPECS/ -->`.

---

## Verification checks run

| Check | Command | Result |
|---|---|---|
| Spec/glossary gate | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-031-globalid_encoding-0_0_9.md` | **`OK: 31 terms`** — before **and** after the edits. I4 and I2 add links rather than removing any, so no CSV term was orphaned. |
| Citation gate | `uv run python scripts/check_citations.py` | **`OK: 807 citations resolve`** (726 in 431 `.py` files, 81 in `KANBAN.md`). No citation was reflowed by this pass. |
| In-page anchors, both files | GitHub-slug comparison over every non-fenced heading vs every `](#…)` use | **0 dangling**, before and after. |
| Reference-style link definitions, both files | undefined ref-ids / unused defs / defs whose target file is missing | **0 / 0 / 0**, before and after. |
| Cross-file link **fragments** | every `path#fragment` definition resolved against the target file's real headings | **0 dangling**, before and after — the 13 `[rationale-dN]` pairs, the 13 `[spec-031-dN]` pairs back, and every `GLOSSARY.md#…` anchor. |
| Markdown scaffold / layout | `uv run python scripts/check_trailing_commas.py --check <both files>` | exit 0. |
| Staged anchors | the step-6 sweep above | Clean; 8 prose-only hits. |
| Working tree | `git status --short` | Only this cycle's own paths. Nothing outside the fence touched, nothing reverted. |

`pytest` was **not** run: this pass changes no `.py` file, so there is no focused scope whose result could
be attributed to it. No `--cov*` flag was used anywhere. `uv run ruff format .` / `ruff check --fix .` were
deliberately not run — this pass edited only `.md` files, which ruff neither formats nor lints, and running
them repo-wide would churn files owned by other work. No `git stash` / `git checkout` / `git restore` /
`git worktree` was used; the one HEAD-history read (`git show HEAD:<spec>`) wrote to a scratch path outside
the repo, and `git show --numstat 7d892d6f` is read-only.

### Working-tree baseline (re-read at the start of this pass)

HEAD `5ebcfe9c`. The build plan's `### Concurrent work` list is **stale**, as the plan preamble warns: the
concurrent session committed `consumers.py`, `utils/sessions.py`, `tests/test_consumers.py`, and
`examples/fakeshop/db.sqlite3` mid-cycle (`bc4ed00a` → `0e5044da` → `5ebcfe9c`). Nothing outside this
cycle's own eight paths is dirty, so this pass had no `AGENTS.md` rule-34 exclusions to respect beyond
leaving the committed work alone. `examples/fakeshop/db.sqlite3` was neither written nor reset.

---

## Worker 2 dispatch

**Owed.** One cohort, three sites, two files, comment-only:
`django_strawberry_framework/types/definition.py` and `django_strawberry_framework/types/relay.py`. The
contracts, the exclusion, and the full obligation list (the inverse proof method above all) are in
`### Dispatched findings checklist`. Worker 0 dispatches Worker 2, then Worker 3 as a separate spawn
(`### Isolation is non-waivable`), then re-runs this integration pass.

Everything else this pass found was inside the spec/companion pair and is already fixed; the catalog below
is what `bld-031-final.md` inherits.

---

## For `bld-031-final.md` — `### Deferred work catalog` handoff

Every item with a named owner, as the last pass before the gate requires.

| Item | Source | Owner |
|---|---|---|
| **`spec-032`'s eight dangling citations into text that left `spec-031`**, in four claim families — the two `Revision 6` / `Revision 7` references (`:13`, `:513`), Decision 1's moved justification (`:281`), Decision 3's moved rejected alternative (`:312`), and Decision 11's moved deferral / "no shipped `0.0.9` consumer" quote (`:9`, `:143`, `:452`, `:464`). Each row above states where the cited text now lives. `spec-032` is out of this cycle's fence entirely. | `bld-031-slice-0` note 4, population re-derived by this pass (3 sites → 8) | **maintainer**, or a future `032` cycle |
| **The `"Relay"` / `"Type generation"` Browse-by-category slash** in the Slice-5 GLOSSARY checklist bullet and `## Doc updates` admits two readings; `docs/GLOSSARY.md` satisfies the better one (each symbol filed under the row it belongs in). Not a defect and out of fence; worth one sentence only if the slash is to be disambiguated in a future spec's template. | `bld-031-slice-5` | **maintainer** |
| **`docs/builder/bld-003-final.md`** survives from the `spec-003` cycle and was deliberately left in place at pre-flight (tracked, committed, out of the maintainer's fence, cannot collide with this cycle's `031`-named artifacts). Recorded as a pre-flight deviation, not a defect. | build plan, pre-flight step 3 | **maintainer** |

Closed, and listed only so the gate can see they were not dropped:

- The four-clause stale-`.py`-comment batch — **re-derived to three sites and dispatched to Worker 2**, not
  deferred. No longer a catalog item.
- `_first_model_label_emitter` / `_audit_model_label_routing`'s no-definition raises — judgement confirmed,
  deliberately uncontracted, pinned by `tests/types/test_finalizer.py`. No owner needed.
- `TODAY.md:14` — Slice 5's audit closed it; accurate on its own terms, no doc obligation implied.
- Slice 0's notes 1-3 (the resolver arity, DoD item 1's CSV claim, the pre-archival spec path) — discharged
  by Slices 2 and 5, each re-verified by this pass.

---

## Final verification (Worker 1)

- **Cross-home walk:** every contract this cycle's slices edited walked through all of its homes. Five
  disagreements found, all five inside the fence, all five fixed. Eleven mechanical sweeps came back clean
  and are recorded above rather than left implied.
- **Spec / companion pairing:** 13/13 Decisions paired in both directions with resolving anchors; 29
  `**Post-ship:**` entries all lookuppable; two companion entries contradicted the repository and both are
  fixed; zero dangling anchors, definitions, or fragments in either file.
- **Standard checks not applicable:** step 2 (no Python file touched by the build), steps 3 and 4 (no
  shadow overviews, because no slice wrote code). Each recorded with its reason and with what answered the
  underlying question instead.
- **Staged-anchor sweep:** clean, re-measured rather than inherited.
- **Step 5:** every deferred item now has a named owner or is closed. Three that were drifting without one
  are dispatched to Worker 2.
- **DRY check across slices:** no duplication introduced; no consolidation candidate survives the
  reader-check, which found live single-sitings rather than dead pairs.
- **Fail-open shapes:** none introduced — no code changed by this pass, and the Worker 2 diff is
  comment-only with an inverse proof to establish it.
- **Failability proofs:** not applicable; zero new boundaries.
- **Relocation / promotion claims:** none made by this pass. The one owed by the Worker 2 pass is specified
  in `### Dispatched findings checklist`.
- **Final status:** `planned`. A Worker 2 pass is owed; Worker 0 dispatches Worker 2, then Worker 3, then
  re-runs this pass.

### Summary

Nothing had read `spec-031` end to end as one document since five slices each rewrote their own region of
it. Reading it that way found five cross-home disagreements no per-slice pass could have seen: a test name
the companion invented, a present-tense byte count the same cycle falsified, a `## User-facing API` example
that raises `ConfigurationError` on its own last line because two Relay types share a model with no
declared primary, an Implementation-plan table half measured and half guessed with a total its own rows
contradict, and a Step-2 enumeration missing the member Revision 4 added. All five are in Worker 1's fence
and all five are fixed, with five `**Post-ship:**` bullets recording why. The spec/companion pair holds in
both directions — 13/13 Decisions cross-linked with resolving anchors, 29 lookuppable `**Post-ship:**`
entries, zero dangling links in either file — and eleven other cross-home sweeps, the 33 rejected
alternatives and the 93 test citations among them, came back clean.

The batched source-comment judgement is re-opened and reversed. Re-derivation shrank the batch from four
clauses to three (`_install_typename_closure`'s docstring was a mis-attribution and is correct as written),
but two of the three are flatly false — one of them about a fail-closed boundary, in the invariants
docstring a maintainer reads to learn what `None` means, contradicted by a sibling docstring in the same
package; the other carrying a stale `WIP-ALPHA-` card id no future card owns. `AGENTS.md` rule 5 does not
permit routing those to a follow-up. `Status: planned`; Worker 2, then Worker 3, then this pass again.

---

## Build report (Worker 2)

Comment-only cohort, three sites, two files. All three `### Dispatched findings checklist` boxes are
ticked: each fix landed in this pass's diff. Nothing was deferred.

### Files touched

Grounded in `git status --short` (below), not memory. Two source files, both docstring-only.

- `django_strawberry_framework/types/definition.py` — **F-1**. The `DjangoTypeDefinition` invariants
  docstring's `effective_globalid_strategy` bullet said a known `None` recorded strategy makes "the filter
  fall back to node-id-only validation". False since the `0.0.14` hardening. The bullet now states that the
  strategy-aware `GlobalID` filter **fails closed** on a known `None` — a coded `GLOBALID_UNVALIDATABLE`
  error raised at request time by `filters/base.py::_decode_and_validate_global_id`, the runtime backstop
  behind the build-time audit — and that the only surviving node-id-only path is the unbound-owner /
  unresolvable-target case, where no definition and therefore no strategy exists at all. The
  `spec-031 Decision 8` and `spec-031 Decision 13` pointers are both kept, Decision 13 now sitting on the
  sentence it actually licenses.
- `django_strawberry_framework/types/relay.py` — **F-2** and **F-3**.
  - **F-2**, `::encode_typename`, the `type` bullet. The exclusivity framing ("so this branch is the live
    implementation for exactly that shape") is replaced by the membership claim Decision 10 now carries:
    the shadow-install is the only route into this branch **during `id` resolution**, and
    `testing/relay.py::global_id_for` calls the helper directly with a type's recorded strategy and reaches
    the branch with no installed closure.
  - **F-3**, `::decode_global_id`. The stale `WIP-ALPHA-032-0.0.9` card id and the "no shipped `0.0.9` path
    calls it yet" clause are gone. The docstring now states the current consumption as a three-item list:
    the root `node(id:)` / `nodes(ids:)` fields through
    `django_strawberry_framework/relay.py::_decode_or_graphql_error` (which converts the uniform
    `ConfigurationError` into a `GLOBALID_INVALID` `GraphQLError`); the write-side typed-id primitive
    `django_strawberry_framework/relay.py::decode_model_global_id` (shared by the mutation flavors and the
    relation `<field>_id` decode); and the public re-export `testing/relay.py::decode_global_id`.

    One further clause in the **same docstring** carried the same falsified premise and had to move with
    it: the paragraph immediately beneath opened "Because its **eventual** caller feeds it arbitrary
    client-controlled input". With the three call paths now named three lines above, "eventual caller"
    contradicts them outright — the callers exist. It now reads "Because **those** callers feed it arbitrary
    client-controlled input", which is the same sentence pointed at the list. This is inside F-3's site and
    F-3's contract (the plan's instruction is to "state the current consumption and drop the 'no shipped
    path calls it yet' clause"), not a broadening: it is one tense fix in the clause the F-3 rewrite would
    otherwise have left self-contradicting. Recorded rather than done silently.
- `docs/builder/bld-031-integration.md` — this build report, the three checklist ticks, and the `Status:`
  line. Worker 1's plan prose is untouched apart from the three `- [ ]` → `- [x]` markers.

**Explicitly not touched, per the plan's exclusion:**
`django_strawberry_framework/types/relay.py::_install_typename_closure`'s docstring. Re-read at HEAD before
editing the sibling three lines above it: it states `` `model` / `type+model` / `callable` always reach
here; `type` reaches here only when shadowing a framework closure inherited from a concrete Relay parent ``
— a true membership claim about the **install site**, not the falsified exclusivity claim. Left byte-for-byte
alone.

### Tests added or updated

None, and none is owed. The diff changes no executable byte (proved below), so there is no behavior for a
new assertion to pin; adding one would be a test of prose. The claims the three docstrings now make were
each verified against shipped source before being written:

| Clause written | Verified against |
|---|---|
| the filter fails closed on a known `None` | `django_strawberry_framework/filters/base.py::_decode_and_validate_global_id` — the guard reads `if strategy not in FRAMEWORK_GLOBALID_STRATEGIES:` and raises with `extensions={"code": "GLOBALID_UNVALIDATABLE"}` **before** `::_accepted_globalid_type_names` is called |
| node-id-only survives only for the unbound owner | `::_accepted_globalid_type_names` returns `None` on `definition is None` and only there; the mismatch guard is skipped when `accepted is None` |
| `global_id_for` reaches the `type` branch directly | `django_strawberry_framework/testing/relay.py::global_id_for` calls `encode_typename(definition, strategy, type_cls, None)` after gating on `strategy in STRING_GLOBALID_STRATEGIES`, which contains `type`; no closure is installed on that path |
| `decode_global_id`'s three call paths | `grep -rn "decode_global_id" --include="*.py" django_strawberry_framework/` — `relay.py:115` inside `::_decode_or_graphql_error`, `relay.py:311` inside `::decode_model_global_id`, and the `testing/relay.py:47` import / `:49` `__all__` re-export. No fourth in-package call site |

### Validation run

```shell
uv run ruff format django_strawberry_framework/types/definition.py django_strawberry_framework/types/relay.py
# -> 2 files left unchanged
uv run ruff check --fix django_strawberry_framework/types/definition.py django_strawberry_framework/types/relay.py
# -> All checks passed!
uv run python scripts/check_trailing_commas.py --check \
  django_strawberry_framework/types/definition.py django_strawberry_framework/types/relay.py
# -> exit 0 (ASCII-only, line length, trailing-comma layout)
uv run python scripts/check_citations.py
# -> OK: 812 citations resolve (731 in 431 .py files, 81 in KANBAN.md)
```

Both ruff invocations were **scoped to the two files**, never `.`. Ruff reformatted nothing, which is the
expected result for a docstring rewrite kept inside the existing wrap.

**Citation gate, and the wrapped-citation hazard specifically.** The count moved `807` → `812`: five
citations were **added** by this diff, none removed, none reflowed. The five are
`filters/base.py::_decode_and_validate_global_id` (F-1), `testing/relay.py::global_id_for` (F-2), and
`django_strawberry_framework/relay.py::_decode_or_graphql_error` /
`django_strawberry_framework/relay.py::decode_model_global_id` / `testing/relay.py::decode_global_id`
(F-3). Every one is written on a single line. The two root-module refs are spelled with the **full**
`django_strawberry_framework/` prefix rather than a bare `relay.py::…`: the citing file is itself named
`relay.py`, and `scripts/check_citations.py::candidate_paths` resolves a citation against the citing file's
own directory first, so a bare spelling would read as self-referential to a human even though the gate
resolves it. Independently swept for a wrapped citation, which the gate cannot see:

```shell
grep -nE '\.py$|::$' django_strawberry_framework/types/definition.py django_strawberry_framework/types/relay.py
# -> no output (exit 1): no line in either file ends in `.py` or `::`, so no citation is split across two lines
```

```shell
git status --short
 M django_strawberry_framework/types/definition.py
 M django_strawberry_framework/types/relay.py
 M docs/SPECS/spec-031-globalid_encoding-0_0_9.md
?? docs/SPECS/appx/spec-031-globalid_encoding-0_0_9-rationale.md
?? docs/builder/bld-031-integration.md
?? docs/builder/bld-031-slice-0-rationale_extraction.md
?? docs/builder/bld-031-slice-1-meta_key_setting_precedence.md
?? docs/builder/bld-031-slice-2-encode_seam.md
?? docs/builder/bld-031-slice-3-decode_seam.md
?? docs/builder/bld-031-slice-4-live_http.md
?? docs/builder/bld-031-slice-5-docs_wrap.md
?? docs/builder/build-031-globalid_encoding-0_0_9.md
```

Every modified path is slice-intended: the two source files are this cohort's, the nine `031` paths are the
cycle's own. Nothing outside the fence is dirty, so there was nothing to stop-and-report and nothing was
reverted. The build plan's `### Concurrent work` list is stale in the way the integration plan already
recorded — the concurrent session committed `consumers.py`, `utils/sessions.py`, `tests/test_consumers.py`,
and `examples/fakeshop/db.sqlite3` mid-cycle (HEAD `bc4ed00a` → `5ebcfe9c`), so none of the four is dirty
any more. `examples/fakeshop/db.sqlite3` was neither written nor reset by this pass.

**Focused test run** (no `--cov*` flag; `--no-cov` only), to confirm a docstring rewrite broke no import or
collection in the two modules and their readers:

```shell
uv run pytest tests/types/test_relay_interfaces.py tests/filters/test_base.py tests/testing/test_relay.py --no-cov -q
# -> 262 passed in 9.48s (8 workers, 0 collection errors)
```

### Inverse proof — executable bytes unchanged

The pass's central record, per `### Dispatched findings checklist` and `docs/builder/BUILD.md`
`## Claims are proven mechanically, never accepted on prose` (the *carried-over-unchanged* shape).
Comments never reach the AST but **docstrings do**, so a bare `ast.dump` / `ast.unparse` comparison would
show a difference and prove nothing; the docstrings are stripped explicitly and the remaining executable
content compared. No `git stash` / `git checkout` / `git restore` / `git worktree` anywhere — the only git
read is `git show HEAD:<path>`, which is read-only, and it writes to a scratch path **outside** the repo.

Scratch root (outside the working tree):
`/private/tmp/claude-501/-Users-riordenweber-projects-django-strawberry-framework/bcce4eff-a8a2-41e3-a692-e4808b71a430/scratchpad`, referred to as `$SP` below.

The stripper, `$SP/strip_docstrings.py`, walks the parsed tree and drops the leading string-constant
`Expr` from every `Module` / `FunctionDef` / `AsyncFunctionDef` / `ClassDef` body (substituting `pass` when
the docstring was the whole body), then `ast.unparse`s the result.

**Step 1 — take the HEAD reference read-only, and establish the pre-edit baseline.** Run before any edit,
so the comparison is anchored on a revision that is known-unmutated:

```shell
git show HEAD:django_strawberry_framework/types/definition.py > $SP/definition.HEAD.py
git show HEAD:django_strawberry_framework/types/relay.py      > $SP/relay.HEAD.py
uv run python $SP/strip_docstrings.py $SP/definition.HEAD.py > $SP/definition.HEAD.stripped
uv run python $SP/strip_docstrings.py $SP/relay.HEAD.py      > $SP/relay.HEAD.stripped
wc -c $SP/definition.HEAD.stripped $SP/relay.HEAD.stripped
#  7558 .../definition.HEAD.stripped
# 14589 .../relay.HEAD.stripped
uv run python $SP/strip_docstrings.py django_strawberry_framework/types/definition.py | cmp - $SP/definition.HEAD.stripped
# -> definition: identical
uv run python $SP/strip_docstrings.py django_strawberry_framework/types/relay.py | cmp - $SP/relay.HEAD.stripped
# -> relay: identical
```

Both files' executable content matched HEAD **before** this pass edited anything, so neither carried a
concurrent session's executable change that a post-edit comparison could have absorbed silently.

**Step 2 — compare after the edits.**

```shell
uv run python $SP/strip_docstrings.py django_strawberry_framework/types/definition.py > $SP/definition.WT.stripped
cmp $SP/definition.HEAD.stripped $SP/definition.WT.stripped
# -> exit 0 (no output): executable content identical
uv run python $SP/strip_docstrings.py django_strawberry_framework/types/relay.py > $SP/relay.WT.stripped
cmp $SP/relay.HEAD.stripped $SP/relay.WT.stripped
# -> exit 0 (no output): executable content identical
```

**Step 3 — the control, so the proof is not vacuous.** A comparison that would pass no matter what is not a
proof. The *unstripped* unparse of the same two revisions must **differ**, since the docstrings did change;
if it did not, the stripper (or the comparison) would be reading the wrong thing:

```shell
uv run python -c "
import ast
a = ast.unparse(ast.parse(open('$SP/relay.HEAD.py').read()))
b = ast.unparse(ast.parse(open('django_strawberry_framework/types/relay.py').read()))
print('unstripped identical:', a == b)
"
# -> unstripped identical: False
```

So the docstring text demonstrably moved, and the executable content demonstrably did not. Ruff also
reported `2 files left unchanged`, an independent read on the same fact from a different parser.

### Failability proofs

**None; this pass introduced no new boundary.** Stated explicitly rather than left blank, per the plan.
`docs/builder/BUILD.md` `### What needs a proof, and what does not` scopes the obligation to a new boundary,
guard, gate, or rejection path a slice **introduces**; this diff introduces none. It corrects prose *about*
two existing ones — `filters/base.py::_decode_and_validate_global_id`'s `GLOBALID_UNVALIDATABLE` fail-closed
guard (F-1) and `types/relay.py::decode_global_id`'s Step-2 enforcement (F-3) — both of which shipped, and
were pinned, long before this cycle. The proof this pass **does** owe is the inverse one above, and it is
the stronger claim: not that a boundary can fail, but that no executable byte moved at all.

### Hot-path budget

**Not applicable; the plan declares no hot path, and a docstring change adds no runtime cost.** Stated
explicitly rather than omitted, per the plan. The seams involved genuinely are hot — the installed
`resolve_typename` closure runs per emitted node `id`, `decode_global_id` per root `node(id:)` and per
write-side typed id, `filters/base.py::_decode_and_validate_global_id` per filter value — so a future pass
landing executable change in any of them owes a before/after number. This pass lands none, and the inverse
proof above is what establishes that rather than an assertion.

### Floor verification

**Not applicable; plan declares floor-verification scope `none`.** Same evidence: no executable change
reaches a Django / Strawberry / channels seam. The shared `.venv` was neither read nor mutated, and its
versions are deliberately not stated here — `docs/builder/BUILD.md` `## Floor verification` forbids stating
them from memory and this pass had no reason to read them.

### Implementation notes

- **F-1's Decision pointers were re-homed, not just kept.** The plan says to keep the `spec-031 Decision 13`
  pointer, and the false clause was the one carrying it. Deleting the clause would have orphaned the
  pointer, so Decision 13 now sits on the replacement sentence — the fail-closed reject plus the
  unbound-owner carve-out — which is precisely what Decision 13 contracts. Decision 8 stays on the decode
  half of the same sentence, unmoved.
- **F-3 became a list rather than a sentence.** Three call paths, each needing its own qualifier (what the
  root path converts the error into; what the write-side primitive is shared by; that the third is a
  re-export rather than a distinct consumer), do not fit one readable sentence, and the module's other
  docstrings already use bulleted call-path lists (`::decode_global_id`'s own Steps list, `::encode_typename`'s
  per-strategy list). Same convention, no new shape.
- **The two root-module citations carry the full `django_strawberry_framework/` prefix.** Reasoning under
  `### Validation run`; the short form resolves for the gate but reads as self-referential inside a file
  itself named `relay.py`.
- **ASCII kept.** All three docstrings used `-` rather than an em dash and still do; no non-ASCII character
  was introduced (`scripts/check_trailing_commas.py --check` is the mechanical confirmation).
- **No process provenance.** None of the three replacements says a cycle corrected it, that it was
  previously wrong, or names a review round. Each states only the current invariant plus its spec-Decision
  pointer, which is on the `AGENTS.md` rule 27 KEEP list.

### Notes for Worker 3

- The whole diff is docstring text. The single question worth spending review time on is whether the three
  new clauses are **true at HEAD**, not whether the code is right — the code is byte-identical, and
  `### Inverse proof` is the mechanical record of that. Re-deriving the four rows of the
  `### Tests added or updated` table against shipped source is the highest-value independent check.
- `scripts/review_inspect.py` was **not** run, and the reason is the one the integration pass forecast at
  its `### Step 2 — the static inspection helper`. The trigger for Worker 3 is "touches an existing `.py`
  file under `optimizer/` or `types/`", which this diff does — but the helper's output is an AST overview
  (imports, symbols, repeated literals, control-flow hotspots), every section of which is a function of the
  executable surface, and the inverse proof establishes that surface is unchanged from HEAD. A run would
  reproduce the pre-existing overview by construction. The integration plan recorded in advance that Worker 3
  may take the same skip against the same reason once the inverse proof holds; it holds.
- The plan's exclusion is real and easy to trip over on a fresh read: `::_install_typename_closure`'s
  docstring sits ~15 lines below the F-2 edit and makes a superficially similar `type`-branch statement. It
  is **true** (a membership claim about the install site) and is deliberately untouched. Two earlier slices
  attributed the F-2 defect to both sites; the integration pass re-derived it to one.
- No temp test was needed or written; `docs/builder/temp-tests/` is untouched.

### Notes for Worker 1 (spec reconciliation)

**None.** No spec gap, conflict, or unstated assumption surfaced. Each of the three replacement clauses was
written to state what the spec already contracts, and each was read against the spec's current text before
being written:

- F-1 against `## Decision 13`, whose closing sentences already say the known-`None` case "is rejected by
  that **runtime** backstop and only there" and that "the **only** node-id-only fallback that survives is
  the pre-existing no-resolvable-definition case". The docstring now agrees with the spec instead of
  contradicting it; no spec edit is needed in either direction.
- F-2 against `## Decision 10` step 2, whose shadow-install sentence already carries both halves — "the only
  path reaching `encode_typename`'s `type` branch … **during `id` resolution**" and the explicit
  `testing/relay.py::global_id_for` carve-out. The docstring is now the same claim in source.
- F-3 against `## Decision 8`. The spec's `## Current state` observation that "in `0.0.9` no shipped path
  hits native `resolve_type` … the package's own `decode_global_id` is the forward-looking helper
  `DONE-032-0.0.9` dispatches through" is about **Strawberry's native** `resolve_type` and is a licensed
  dated observation the integration pass already verified against the authoring commit. It is **not** the
  claim F-3 retired — the docstring's false clause was about `decode_global_id` itself having no shipped
  caller, which is a different sentence about a different symbol. Flagged here only so a future reader does
  not mistake the surviving spec sentence for missed residue of F-3.

No plan-vs-implementation drift of either kind: the three contracts were pinned sentence by sentence and the
implementation stayed inside them, with only the wording delegated (the plan's single
`### Implementation discretion item`).

---

## Review (Worker 3)

Comment-only cohort, two files, three dispatched findings. Everything below was re-derived from shipped
source and re-run rather than read off the build report. The two questions this pass turns on are (1) does
the inverse proof hold under an independently-written instrument, and (2) is each replacement clause TRUE.
Both answers are yes.

### High:

None.

### Medium:

None.

### Low:

#### F-1's parenthetical could be read as attributing the `None` reject to the build-time audit

`django_strawberry_framework/types/definition.py:130-134`. The new clause reads "a known ``None`` on a
resolved definition raises the coded ``GLOBALID_UNVALIDATABLE`` error at request time
(``filters/base.py::_decode_and_validate_global_id``, the runtime backstop behind the build-time audit)".
Re-derived: `types/finalizer.py::_audit_globalid_filter_strategies` keys **only** on
`strategy in ENCODE_ONLY_GLOBALID_STRATEGIES` and does **not** reject a `None` strategy, so the runtime
backstop is the sole rejecter of the `None` case. A reader could take the trailing appositive as saying the
audit covers `None` too.

**Raised and intentionally rejected, reason recorded.** The appositive attaches to the cited *function* and
describes that function's standing role, which is accurate; it makes no claim about what the audit keys on.
It is also verbatim the phrasing the shipped sibling already uses -
`filters/base.py::_decode_and_validate_global_id`'s own docstring says "the runtime backstop behind the
build-time audit (`finalizer._audit_globalid_filter_strategies`) for hand-built filtersets constructed
outside finalization" - so tightening only this one site would put the two docstrings out of step for no
gain in accuracy. The precise split (audit keys on the two encode-only names; the backstop *additionally*
rejects a known `None`) is stated in both Decision 13 and that sibling docstring. Not a re-loop.

#### A test docstring outside the fence carries the F-2 exclusivity framing

`tests/types/test_relay_interfaces.py:2151`, inside
`::test_type_strategy_child_shadows_inherited_framework_closure`: "(``encode_typename``'s ``type`` branch
goes live for exactly this shape)". This is the same unscoped exclusivity framing F-2 corrected in source.

**Raised and intentionally rejected, reason recorded.** It is out of this cohort's two-file fence, Worker 3
does not edit permanent tests, and it is defensible as written: the sentence sits inside a test whose whole
subject is `id` resolution, which is exactly the scope Decision 10 and the corrected F-2 clause use. Flagged
for Worker 1 below so the decision is visible rather than silent, not as a blocker.

### DRY findings

None. The diff adds no helper, constant, branch, or literal - it changes docstring text only, which the
inverse proof below establishes mechanically. The one DRY-adjacent judgement in range is the plan's
exclusion of `::_install_typename_closure`, audited under `### The exclusion, independently re-derived`.

### The inverse proof, independently re-run

Worker 2's instrument drops the leading string `Expr` and compares `ast.unparse` output. I did **not** reuse
it. I wrote `$SP/w3_strip.py`, which differs on both axes deliberately: it *substitutes a fixed sentinel*
into every docstring slot rather than deleting the node (so the comparison also pins that no docstring slot
was added, removed, or moved), and it emits `ast.dump(..., include_attributes=False)` rather than an
unparse (so the comparison is on tree structure, not on re-rendered text that a normalising unparser could
launder). HEAD reference taken read-only with `git show HEAD:<path>` into a scratch path outside the repo;
no `git stash` / `git checkout` / `git restore` / `git worktree` anywhere in this pass.

```shell
git show HEAD:django_strawberry_framework/types/definition.py > $SP/w3_definition.HEAD.py
git show HEAD:django_strawberry_framework/types/relay.py      > $SP/w3_relay.HEAD.py
uv run python $SP/w3_strip.py $SP/w3_<f>.HEAD.py                      > $SP/w3_<f>.HEAD.dump
uv run python $SP/w3_strip.py django_strawberry_framework/types/<f>.py > $SP/w3_<f>.WT.dump
cmp $SP/w3_<f>.HEAD.dump $SP/w3_<f>.WT.dump
# -> definition: STRUCTURAL AST IDENTICAL
# -> relay:      STRUCTURAL AST IDENTICAL
```

`wc -c` on the references: 25,153 (definition) and 47,968 (relay) bytes of dumped tree.

**Four controls, because an instrument that passes everything proves nothing.** Worker 2 ran one (the
unstripped unparse must differ). I ran that plus three more, all against scratch copies only - no repo file
was mutated at any point, so the `worker-3.md` source carve-out was not exercised and nothing needed
reverting:

| Control | What it rules out | Result |
|---|---|---|
| A - unstripped `ast.dump` of HEAD vs working tree must **differ** | the comparison is reading a revision that did not change | `definition: False`, `relay: False` (i.e. not identical) - correct |
| B - rename an executable binding in a scratch HEAD copy (`MODEL_LABEL_STRATEGIES` -> `..._XX`) | the sentinel substitution flattens the whole tree | detected - correct |
| C - change an executable string literal in a scratch HEAD copy (`"model"` inside the `MODEL_LABEL_STRATEGIES` frozenset) | the stripper wipes *all* string constants, not just docstring slots | detected - correct |
| D - replace the module docstring wholesale in a scratch HEAD copy | the sentinel does not actually cover docstring slots | invisible - correct |

C is the control worth naming: my first attempt at it targeted the *first* occurrence of `"type+model"` in
the file, which lives inside the module docstring, and the stripper correctly reported no difference. Read
naively that is a "VACUOUS (bad)" result; it was the control being aimed at the wrong token. Re-aimed at the
`frozenset({...})` on `types/relay.py:433` it detects immediately. Recording the misfire because a control
that quietly measured the wrong thing is the exact failure mode this table exists to prevent.

**Verdict: the executable surface is byte-equivalent to HEAD.** The hot-path declaration (`none`) and the
floor-verification scope (`none`) both follow from that and are correct - there is no executable line on any
path, hot or cold, for a budget number to attach to.

### Per-finding TRUE/FALSE verdicts

Each replacement clause checked against shipped source, not against the plan's description of it.

#### F-1 - `types/definition.py::DjangoTypeDefinition` - **TRUE**, both halves

- *Fails closed on a known `None`.* `filters/base.py::_decode_and_validate_global_id` reaches
  `if definition is not None: strategy = definition.effective_globalid_strategy;
  if strategy not in FRAMEWORK_GLOBALID_STRATEGIES:` and raises with
  `extensions={"code": "GLOBALID_UNVALIDATABLE"}`. `FRAMEWORK_GLOBALID_STRATEGIES` is
  `MODEL_LABEL_STRATEGIES | TYPE_NAME_STRATEGIES` = `{"model", "type", "type+model"}`, so `None` fails the
  membership; `None` is not in `ENCODE_ONLY_GLOBALID_STRATEGIES` either, so control lands in the `else` arm
  whose message is the no-recorded-strategy one. The raise precedes the
  `accepted = _accepted_globalid_type_names(definition)` call, as the clause implies. Confirmed.
- *The only surviving node-id-only path is the unbound-owner / unresolvable-target case.*
  `_accepted_globalid_type_names` returns `None` **only** on `definition is None` (its `accepted or None`
  tail is unreachable given the fail-closed guard above, and its own docstring says so), and the `type_name`
  guard is skipped exactly when `accepted is None`. The PK-coercion guard is likewise skipped for
  `definition is None`, since `target_model` is then `None`. So `definition is None` is the whole of the
  surviving node-id-only path. Confirmed.
- *Decision pointers.* `spec-031 Decision 8` stays on the decode half; `spec-031 Decision 13` moved onto the
  replacement sentence rather than being orphaned with the deleted clause. Decision 13 is what contracts the
  strategy-aware filter, so it is now on the sentence it licenses. Correct re-homing, not a drift.

#### F-2 - `types/relay.py::encode_typename` - **TRUE**, both halves, and the population is complete

- *Shadow-install is the only route into the branch during `id` resolution.*
  `install_globalid_typename_resolver` gates the install on
  `if classification != "type" or _inherits_framework_closure(type_cls):`, so a `type`-strategy type
  installs a closure **only** when it inherits a framework closure - the shadow case. With no closure
  installed, Strawberry's default `resolve_typename` runs and never enters `encode_typename` at all. The
  final `return definition.graphql_type_name` is reached only for `strategy == "type"` exactly, since
  `"type+model"` is a member of `MODEL_LABEL_STRATEGIES` and takes the earlier return. Confirmed.
- *`testing/relay.py::global_id_for` reaches it directly with no installed closure.* It calls
  `encode_typename(definition, strategy, type_cls, None)` after gating on
  `strategy in STRING_GLOBALID_STRATEGIES`, and `types/base.py:135` defines that set as
  `frozenset({"model", "type", "type+model"})` - `"type"` is a member. No closure is installed on that path.
  Confirmed.
- *Population.* `grep -rn "encode_typename" --include="*.py" .` returns exactly two shipped call sites -
  the closure body in `::_install_typename_closure` and `testing/relay.py::global_id_for` - plus one package
  test. So the corrected clause enumerates the complete set of routes, not a sample. The helper is not in
  `django_strawberry_framework/__init__.py`, so there is no public third route.

One compression worth naming and not faulting: "reaches the branch with no installed closure" is true of
`global_id_for` *for a `type`-strategy type*; `global_id_for` also reaches `encode_typename`'s other
branches for the other string strategies. The bullet's entire scope is the `type` strategy, so the reading
is unambiguous in place.

#### F-3 - `types/relay.py::decode_global_id` - **TRUE**, and three is the population, not a sample

Enumerated the whole population rather than confirming the three named:
`grep -rn "decode_global_id" django_strawberry_framework/ --include="*.py"` yields exactly three
**invocation** sites (every other hit is the definition, an error-message f-string, or a prose reference):

| Named path | Site | Verified |
|---|---|---|
| root `node(id:)` / `nodes(ids:)` via `::_decode_or_graphql_error` | `relay.py:115`, called from `relay.py:470` (the `node(id:)` resolver) and `relay.py:554` (the `nodes(ids:)` batch decode) | the wrapper catches `ConfigurationError` and re-raises `GraphQLError(..., extensions={"code": "GLOBALID_INVALID"})` - exactly as the clause says |
| write-side typed-id primitive `::decode_model_global_id` | `relay.py:311` | its own docstring names `coerce_lookup_id` (mutation root `id:`) and `_decode_relation_id_set` (relation `<field>_id`) as its consumers; readers confirmed in `mutations/resolvers.py:1218`, `utils/write_values.py:151`, plus `forms/resolvers.py` and `rest_framework/resolvers.py` - "the mutation flavors and the relation `<field>_id` decode" is accurate |
| public re-export `testing/relay.py::decode_global_id` | `testing/relay.py:47` import, `:49` `__all__` | confirmed |

No fourth in-package invocation exists. The stale `WIP-ALPHA-032-0.0.9` id and the "no shipped `0.0.9` path
calls it yet" clause are both gone from the file.

**The unrequested tense fix ("its eventual caller" -> "those callers") was warranted and in scope.** With
three live call paths named three lines above, "eventual caller" is not merely stale, it directly
contradicts the list the same docstring just gave - the F-3 rewrite would have left the paragraph
self-contradicting had it been left alone. It is one word inside F-3's own site, changes no other claim in
the sentence, and Worker 2 recorded it rather than doing it silently. Correct call on both counts.

### The exclusion, independently re-derived

The plan excluded `types/relay.py::_install_typename_closure`'s docstring and told Worker 2 not to "fix" it.
Both halves audited:

- **The exclusion was correct.** That docstring claims "``model`` / ``type+model`` / ``callable`` always
  reach here; ``type`` reaches here only when shadowing a framework closure inherited from a concrete Relay
  parent (otherwise ``type`` keeps Strawberry's default)". Read against
  `if classification != "type" or _inherits_framework_closure(type_cls):` this is exactly the guard, stated
  as a membership claim about the **install site** - a different claim from the one F-2 retired, and true.
  Re-derived from the source, not accepted from the artifact's account of the re-derivation.
- **Worker 2 honored it.** `git diff HEAD` shows the file's only two hunks at `::encode_typename` and
  `::decode_global_id`; the `::_install_typename_closure` body and docstring are byte-identical to HEAD, and
  the structural AST comparison above independently pins that nothing in the file moved.

I am not re-opening it.

### Dispatched findings checklist audit

Three boxes, all ticked by Worker 2, all three audited against the diff:

| Box | Ticked | Matching fix in the diff | Verdict |
|---|---|---|---|
| F-1 `types/definition.py::DjangoTypeDefinition` | `- [x]` | hunk at `definition.py:124-138`, replaces the node-id-only fallback clause | tick justified |
| F-2 `types/relay.py::encode_typename` | `- [x]` | hunk at `relay.py:484-497`, replaces the exclusivity framing | tick justified |
| F-3 `types/relay.py::decode_global_id` | `- [x]` | hunk at `relay.py:678-696`, replaces the `WIP-ALPHA-` clause with the three call paths | tick justified |

No box is ticked without a matching fix, and no box the diff leaves unaddressed. Nothing was deferred, and
nothing needed to be.

### Failability proofs and the re-run floor

**Empty re-run set, and it is legal here.** `worker-3.md` "Reading is necessary, not sufficient" permits an
empty subset only when the diff introduces no boundary meeting the floor. This diff introduces no boundary
at all - not a guard, gate, cap, rejection path, or validation branch - and that is not accepted on Worker
2's word: the inverse proof above establishes the executable surface is identical to HEAD, which is a
strictly stronger statement than "no new boundary". Worker 2's `None; this pass introduced no new boundary.`
is therefore correct, and correctly stated rather than left blank.

The two boundaries the corrected prose *describes* - `filters/base.py::_decode_and_validate_global_id`'s
`GLOBALID_UNVALIDATABLE` guard and `types/relay.py::decode_global_id`'s Step-2 enforcement - shipped and
were pinned before this cycle; neither is introduced here, so neither is in scope for a proof.

### Fail-open shape hunting

Not applicable and checked rather than assumed: a fail-open shape is a syntactic form in executable code,
and this diff contains no executable code. I re-read the two guards the new prose describes for the shapes
anyway, since F-1's whole subject is a fail-closed decision: `_decode_and_validate_global_id` uses a
positive-membership test (`strategy not in FRAMEWORK_GLOBALID_STRATEGIES` -> raise) rather than a
denylist, so an unrecognised or absent strategy lands on the reject side. That is the answer-guarding shape,
not the input-spelling-guarding one. No finding.

### Static inspection helper

**Run, not skipped.** `docs/builder/BUILD.md` `### When to run the helper during build` fires for Worker 3
on any slice that "touches an existing `.py` file under `optimizer/` or `types/`", which this one does
twice. Worker 2's `### Notes for Worker 3` forecast that I could take the same skip the integration plan
pre-authorized, on the reasoning that the overview is a function of an unchanged executable surface. The
reasoning is sound, but the rule says *must run* and the run is cheap, so I ran it rather than argue the
trigger away:

```shell
uv run python scripts/review_inspect.py django_strawberry_framework/types/definition.py --output-dir docs/shadow
# -> exit 0; wrote docs/shadow/django_strawberry_framework__types__definition.{overview.md,stripped.py}
uv run python scripts/review_inspect.py django_strawberry_framework/types/relay.py --output-dir docs/shadow
# -> exit 0; wrote docs/shadow/django_strawberry_framework__types__relay.{overview.md,stripped.py}
```

Outcome as forecast: every section is pre-existing shipped surface. `types/relay.py` reports 6 repeated
string literals, 6 control-flow hotspots (`::decode_global_id` the largest at 139 lines / 19 branch nodes),
11 executable marker lines, 30 calls of interest, 0 TODO comments; the Imports section shows the documented
one-way `types -> exceptions / registry / utils` direction with no new cross-folder edge. Nothing in either
overview is attributable to this diff, which is the expected consequence of the inverse proof rather than
evidence independent of it. Recorded so the next pass does not have to re-derive whether it owes a run.

### Gate results, all re-run independently

| Gate | Command | Result |
|---|---|---|
| Citations | `uv run python scripts/check_citations.py` | `OK: 812 citations resolve (731 in 431 .py files, 81 in KANBAN.md)`, exit 0 |
| Layout / ASCII / line length | `uv run python scripts/check_trailing_commas.py --check <both files>` | exit 0 |
| Lint | `uv run ruff check <both files>` | `All checks passed!` |
| Format | `uv run ruff format --check <both files>` | `2 files already formatted` |
| Focused tests | `uv run pytest tests/types/test_relay_interfaces.py tests/filters/test_base.py tests/testing/test_relay.py tests/types/test_finalizer.py --no-cov -q` | `278 passed in 10.00s`, 0 collection errors |

Neither ruff invocation used `--fix`; both were scoped to the two files, never `.`. No `--cov*` flag was
used anywhere in this pass.

**The wrapped-citation hazard, checked directly rather than inferred from the green gate.** A passing
`check_citations.py` is not evidence on this specific hazard, and Worker 2's own sweep
(`grep -nE '\.py$|::$'`) only catches a break at two particular characters. I ran a stronger check: extract
every rule-27 citation shape from the **HEAD** revision of each file and from the working tree, then
difference the sets. A citation reflowed across two lines disappears from the working-tree set while the
gate stays green, so a non-empty "lost" set is the signature.

```
--- types/definition.py ---   lost from HEAD: none
                              added: filters/base.py::_decode_and_validate_global_id
--- types/relay.py ---        lost from HEAD: none
                              added: django_strawberry_framework/relay.py::_decode_or_graphql_error,
                                     django_strawberry_framework/relay.py::decode_model_global_id,
                                     testing/relay.py::decode_global_id,
                                     testing/relay.py::global_id_for
```

Zero lost, five added - reconciling exactly with the gate's `807` -> `812` and with Worker 2's list, and
re-derived from the files rather than read off the report. Six lines in the two files end in a path-shaped
token, and all six are *complete* citations that merely happen to end a line (`types/base.py:82`, `:237`;
`types/relay.py:81`, `:256`, `:728`, `:1012`); none sits in a hunk this diff touched. No citation is split.

### Standing-rule checks on the added lines

`AGENTS.md` rule 4 (no `feedback*.md` mention): none. Rule 27 (no `path:NN` in code comments): none - every
new reference is `path::QualifiedName`. ASCII-only: no non-ASCII byte added, `-` kept rather than an em
dash. Longest added line: 83 characters, inside the 99 limit with no E501 grace needed. No process
provenance: no added line says a cycle corrected anything, names a review round, or narrates a prior wrong
state; the three `spec-031 Decision N` pointers are the `AGENTS.md` rule 27 KEEP list and are preserved.

### Test staleness sweep

Run independently rather than against the slice's file list, per `worker-3.md`. Neither staleness class can
apply: the diff adds, removes, and renames no model field or column, and converts no wire shape - it
changes no executable token at all, which the inverse proof establishes mechanically. No test tree is
stranded. No `__doc__` assertion exists anywhere under `tests/` or `examples/` that a docstring rewrite
could break, and the focused run above confirms no import or collection regression.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` returns empty: `__all__` and the re-export list
are unchanged. Confirmed additionally that neither `encode_typename` nor `decode_global_id` is named in that
module, so the two docstrings this pass edited describe internal seams whose public exposure is unchanged.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. The only non-source file in the
diff is this artifact, which Worker 2 owns for its build report and the three checklist ticks.

### What looks solid

- **The inverse proof was built to be falsifiable, not to pass.** Worker 2 ran a control showing the
  unstripped unparse differs, which is the control most builders skip. It is the difference between a proof
  and an assertion, and it is why my re-run could be a genuine second instrument rather than a re-execution
  of the first.
- **The F-1 Decision-pointer re-homing.** Deleting the false clause would have orphaned the
  `spec-031 Decision 13` pointer it carried. Moving it onto the replacement sentence - which is precisely
  what Decision 13 contracts - is the right handling of a pointer whose host sentence dies, and Worker 2
  recorded the reasoning rather than leaving it to be reverse-engineered.
- **The exclusion held under pressure.** `::_install_typename_closure`'s docstring sits about fifteen lines
  below the F-2 edit and makes a superficially identical `type`-branch statement; two earlier slices
  mis-attributed the defect to it. Editing it would have been the natural mistake and would have replaced a
  true claim with a differently-scoped one.
- **F-3's population was enumerated, not sampled.** The three call paths are the complete set, which I
  confirmed by grepping the package rather than by checking the three named. An enumeration presented as
  complete and actually being complete are different properties, and this one is both.
- **Both root-module citations carry the full `django_strawberry_framework/` prefix.** The short form
  resolves for the gate, but inside a file itself named `relay.py` a bare `relay.py::...` reads as
  self-referential. The gate could not have caught that; a human reader would have tripped on it.

### Temp test verification

None written and none needed. `docs/builder/temp-tests/` is untouched. The four controls on the inverse
proof ran entirely against scratch copies under the session scratchpad, outside the repository; no
repository file was mutated at any point in this pass, so the `worker-3.md` source carve-out was not
exercised and there is no revert to prove.

### Notes for Worker 1 (spec reconciliation)

No spec gap or conflict surfaced, and I confirm Worker 2's reading on each of the three: F-1 now agrees with
Decision 13's closing sentences, F-2 with Decision 10 step 2's scoped shadow-install sentence, and F-3 with
Decision 8. No spec edit is owed in either direction.

Two items for your judgement at final verification, neither blocking:

- **The out-of-fence test docstring** at `tests/types/test_relay_interfaces.py:2151`
  (`::test_type_strategy_child_shadows_inherited_framework_closure`) carries the same unscoped "goes live
  for exactly this shape" framing F-2 retired from source. Recorded as a Low above with the rejection
  reason. Resolution paths: (a) leave it - it is defensible under the same `id`-resolution scoping Decision
  10 uses, and it is a test docstring rather than a contract surface; (b) route it to a future pass that
  already owns that test file, since Worker 3 does not edit permanent tests and this cohort's fence is two
  source files. My recommendation is (a), recorded so the call is visible rather than silent.
- **The build-time audit does not key on a `None` strategy** - `_audit_globalid_filter_strategies` filters
  on `ENCODE_ONLY_GLOBALID_STRATEGIES` only, so the `None` case is caught exclusively by the runtime
  backstop. The spec's Decision 13 and `filters/base.py`'s own docstrings both state this split correctly
  and F-1 does not contradict it; I note it only because F-1's parenthetical is the one place in the new
  prose where a hurried reader could merge the two. No action needed.

### Review outcome

`review-accepted`.

Every dispatched finding landed, every replacement clause is TRUE against shipped source with its population
enumerated rather than sampled, the inverse proof holds under an independently written instrument with four
controls, the plan's exclusion was correct and was honored, and every gate re-runs green including the
wrapped-citation hazard the gate itself cannot see. Two Low findings are recorded with their rejection
reasons; neither is a defect in this diff. No High or Medium finding.

---

## Final verification (Worker 1, re-run)

Both halves of one pass: final verification of the consolidation cohort, and the re-run of the integration
pass the consolidation obliged (`worker-1.md` `## Integration pass`). Every number below was re-derived
here; nothing is inherited from the Worker 2 or Worker 3 sections, including the numbers those sections
already proved.

### Working-tree baseline, re-read

HEAD `5ebcfe9c`, unmoved since the Worker 2 pass. `git status --short` carries the same eleven paths: the
two cohort source files, the modified spec, and the eight untracked `031` cycle files. Nothing outside the
fence is dirty, so there is no `AGENTS.md` rule-34 exclusion to respect beyond leaving the concurrent
session's committed work alone. `examples/fakeshop/db.sqlite3` was neither written nor reset.

### The inverse proof, run a third time on a third axis

`worker-1.md` `### Verifying relocation / promotion claims` does not exempt Worker 1 because two agents
already proved the claim, and "carried over unchanged / executable bytes identical" is one of the three
shapes `docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose` requires
re-derivation for. Neither prior instrument was reused.

Worker 2 compared `ast.unparse` text of a docstring-**deleted** tree; Worker 3 compared `ast.dump` structure
of a docstring-**sentinel** tree. Both build an AST. `$SP/w1_bytecode.py` builds none: it hands raw source
to CPython's compiler and walks the resulting code-object graph — `co_code` bytes, `co_names`,
`co_varnames`, free/cell vars, flags, argcounts, and **every** constant, verbatim, recursing into nested
code objects. `$SP` is the session scratchpad outside the repository; the only git read is
`git show HEAD:<path>`, and no `git stash` / `git checkout` / `git restore` / `git worktree` was used.

Docstring neutralisation is CPython's own rather than hand-rolled: the source is compiled at
`optimize=2` (the `-OO` setting), which strips docstrings during compilation. Nothing guesses which const
slot holds a docstring, and because *only* docstrings are removed, an executable string literal stays fully
visible to the comparison.

```shell
git show HEAD:django_strawberry_framework/types/definition.py > $SP/w1_definition.HEAD.py
git show HEAD:django_strawberry_framework/types/relay.py      > $SP/w1_relay.HEAD.py
uv run python $SP/w1_bytecode.py $SP/w1_<f>.HEAD.py                      > $SP/w1_<f>.HEAD.bc
uv run python $SP/w1_bytecode.py django_strawberry_framework/types/<f>.py > $SP/w1_<f>.WT.bc
cmp $SP/w1_<f>.HEAD.bc $SP/w1_<f>.WT.bc
# -> definition: BYTECODE IDENTICAL
# -> relay:      BYTECODE IDENTICAL
```

Reference dumps: 19,309 bytes (`definition`) and 45,480 bytes (`relay`). The interpreter was the shared
`.venv`'s, read at runtime as CPython `3.14.2`; that is a statement about the instrument, not a floor claim
(floor-verification scope is `none` and no version was stated from memory).

#### The first instrument was wrong, and said so loudly

Worth recording, because it is the mirror image of the trap Worker 3 named. The first version of
`w1_bytecode.py` neutralised docstrings with a hand-rolled rule — "`co_consts[0]`, if it is a `str`". Under
CPython 3.14 a **class** body stores its docstring at a different const slot, so the run reported
`definition: DIFFERS`, with the whole `DjangoTypeDefinition` docstring in the diff. A false positive from a
wrong instrument reads exactly like a real finding, the way Worker 3's misaimed control read exactly like a
vacuous one. Delegating the strip to `optimize=2` removed the rule, and with it the class of error.

#### Six controls, and how each was made able to fail

An instrument that cannot report a difference proves nothing, so every control carries two guards. First,
the mutated scratch copy is `cmp`-ed against its base *before* the instrument runs; a control that failed
to mutate reports itself invalid instead of passing. Second — the direct answer to Worker 3's misfire — the
mutation target is **proved executable before being aimed at**, by grepping the docstring-stripped
(`optimize=2`) reference dump for the token: a token that survives docstring stripping is executable by
construction, so it cannot be a string that only lives inside a docstring. `'type+model'` occurs once in
`relay`'s stripped dump; the `_GRAPHQL_NAME_RE` pattern occurs once in `definition`'s.

| Control | Mutation | What it rules out | Expected | Result |
|---|---|---|---|---|
| A | none — recompile both revisions at `optimize=0` (docstrings kept) | the comparison is reading a revision that did not change | DIFFERENT | `definition`: DIFFERENT; `relay`: DIFFERENT |
| B | executable string literal in the frozenset at `types/relay.py:433` (`"type+model"` → `"type+MODEL"`) | `optimize=2` wipes *all* string constants, not just docstrings | DIFFERENT | detected |
| C | operator flip at `types/relay.py:146` (`iface not in type_cls.__mro__` → `iface in …`) | the dump ignores `co_code`, so a semantic change with identical constants slips through | DIFFERENT | detected |
| D | rename an executable binding (`MODEL_LABEL_STRATEGIES` → `..._XX`, all sites) | the dump ignores names / varnames | DIFFERENT | detected |
| E | executable regex literal at `types/definition.py:16` (`^[_A-Za-z]` → `^[_A-Za-Z]`) | control B's result is specific to one file | DIFFERENT | detected |
| F | docstring text only (`::decode_global_id`'s opening sentence, replaced wholesale) | the neutralisation does not actually cover docstring slots | IDENTICAL | invisible |

B through E establish the instrument is not blind; F establishes the neutralisation is what makes the main
comparison pass. A alone would not have been enough, and neither would F alone.

**Verdict: the executable surface of both files is byte-equivalent to HEAD**, independently of the two
prior proofs. The `none` hot-path declaration and the `none` floor-verification scope both follow from that
rather than from assertion — there is no executable line, on any path, for a budget number or a floor run
to attach to.

### The exclusion, and the standing-rule checks, re-derived rather than read

The plan excluded `types/relay.py::_install_typename_closure`'s docstring. Byte-compared directly, HEAD
against the working tree, by extracting that one docstring from each revision: **identical, 801 bytes**.
The exclusion was honored, and the bytecode proof independently pins that nothing executable in the file
moved either.

On the added lines: no process provenance (a case-insensitive scan of every `+` line for `cycle`, `round`,
`review`, `reconcil`, `previously`, `used to`, `was wrong`, `corrected`, `integration`, `worker` returns
nothing); no non-ASCII byte; longest added line 83 characters, inside the 99 limit with no E501 grace
needed; every new source reference is `path::QualifiedName`, none is `path:NN`. The three
`spec-031 Decision N` pointers are on the `AGENTS.md` rule 27 KEEP list and are preserved, with Decision 13
re-homed onto the sentence it licenses rather than orphaned with the clause that died.

### Failability records, and the fail-open read

**Worker 2's `None; this pass introduced no new boundary.` is confirmed CORRECT, not merely present.**
`docs/builder/BUILD.md` `### What needs a proof, and what does not` scopes the obligation to a boundary,
guard, gate, or rejection path a slice **introduces**, and explicitly exempts doc edits. This diff
introduces zero executable tokens, so it introduces zero boundaries — a strictly stronger statement than
"no new boundary", and the inverse proof is what supplies it. The two guards the corrected prose *describes*
shipped and were pinned long before this cycle.

**Fail-open shapes: none, and the diff was read for them rather than skipped.** A fail-open shape is a
syntactic form in executable code — a clamp, a `getattr` default, an `or` fallback, a bare `except`, a
truthiness test on a value that can be absent. The diff contains no executable code at all, which is what
licenses the conclusion; on a comment-only diff that is trivially satisfied, and saying so is the point.
Read separately for the same shapes: `filters/base.py::_decode_and_validate_global_id`, whose fail-closed
decision F-1 now describes, guards the **answer** (`strategy not in FRAMEWORK_GLOBALID_STRATEGIES` → raise)
rather than one spelling of an incoherent input, so an unrecognised or absent strategy lands on the reject
side. No finding.

### Dispatched findings checklist audit

Three boxes, all `- [x]`, each audited against `git diff HEAD` rather than against the build report's
account of it. No box is over-ticked and no landed contract was left open, so no box is un-ticked here and
no deferral reason is owed.

| Box | Contract the plan pinned | Landed in the diff | Verdict |
|---|---|---|---|
| F-1 `types/definition.py::DjangoTypeDefinition` | known `None` is rejected at request time by the runtime backstop; the only surviving node-id-only path is the unbound-owner / unresolvable-target case; keep the Decision 13 pointer | one hunk in the `effective_globalid_strategy` invariants bullet, stating both clauses, with Decision 8 on the decode half and Decision 13 on the replacement sentence | tick justified |
| F-2 `types/relay.py::encode_typename` | replace the exclusivity framing with Decision 10's membership half, scoped to `id` resolution, plus the `global_id_for` carve-out | one hunk in the `type` bullet, carrying both halves | tick justified |
| F-3 `types/relay.py::decode_global_id` | drop the stale card id and the "no shipped path calls it yet" clause; state the current consumption | one hunk replacing both with the three named call paths | tick justified |

**The unrequested change inside F-3 is in scope.** Worker 2 also changed "Because its **eventual** caller
feeds it arbitrary client-controlled input" to "Because **those** callers …". It sits inside F-3's own
docstring, changes no claim other than the tense the F-3 rewrite falsified three lines above it, and was
recorded rather than done silently. Leaving it would have shipped a self-contradicting paragraph. Confirmed
in scope; not a broadening.

### Planned steps: implemented, or rejected with a reason

Every obligation the plan placed on the cohort discharged: the inverse proof (mandatory, and now proved
three times on three axes); the explicit no-failability-proof record (present and correct); ASCII-only and
line length (gate exit 0); rule-27 symbol-qualified references with no reflowed citation (`812` resolving,
zero lost from HEAD); no process provenance (scanned above); scoped ruff and a `git status --short` read.
The plan's single `### Implementation discretion item` — the exact wording, within pinned contracts — was
exercised and stayed inside those contracts. Nothing was deferred and nothing was rejected.

### DRY across slices

**Not applicable, and this is the honest answer rather than a skip.** New duplication, repeated literals,
and inconsistent helper shape are all properties of executable code; the diff contains none, which the
inverse proof establishes mechanically rather than by inspection. The integration pass's own reader-check
of the candidates this cycle touched — the two strategy frozensets, the derived
`FRAMEWORK_GLOBALID_STRATEGIES`, and the shared target resolver — found live single-sitings with multiple
readers rather than dead pairs, and nothing in the cohort changed that. No DRY opportunity remains open, so
`worker-1.md`'s "if DRY opportunities remain, do not accept the slice" is not triggered.

### Focused tests

```shell
uv run pytest tests/types/test_relay_interfaces.py tests/filters/test_base.py tests/testing/test_relay.py \
  tests/types/test_finalizer.py tests/test_registry.py --no-cov -q
# -> 358 passed in 10.56s, 0 collection errors
```

They run. No `--cov*` flag was used in this pass; `tests/test_registry.py` was added to the scope Worker 2
and Worker 3 used because Slice 3's decode seam is pinned there.

### Staged-anchor sweep, and the count reconciled rather than inherited

Re-run with the exact command, excluding the three board files. **Clean: no surviving anchor in any shipped
source, test, or comment**, and the two cohort files add none. **Nine** hits, every one prose describing an
anchor: the spec's Slice-4 checklist and plan row, the companion's Slice-4 post-ship bullet, the
`spec-022` companion's card-renumber history row for a *different* card that once held the number, and five
prior-artifact sweep records.

The three measurements now on record are 6 (Slice 5), 8 (integration pass), 9 (here), and the deltas are
fully attributable: **each pass's own artifact rows are written after its own sweep has run**, so a sweep
can never see the record it is about to create. Slice 5's +2 were its own two rows; the +1 here is the
integration pass's row quoting the `spec-022` renumber table verbatim. Re-measuring rather than inheriting
is what makes that arithmetic instead of alarm.

Worth naming, because it is what stops the regress: **the sweep's population includes the sweep's own
record.** Quoting the *command* costs nothing — its regex metacharacters do not match the literal card-id
form — but quoting a bare card id verbatim adds a hit. This section quotes none, so the next pass measures
nine and not ten.

### Integration re-run — the cross-home questions, re-asked against the current tree

#### The three corrected docstrings against the spec contracts they overlap

The risk this pass exists to catch is a docstring corrected into disagreement with the spec — a cross-home
contradiction this cycle would have *created*. Each was read against the spec's current text.

| Docstring | Spec home | Agreement |
|---|---|---|
| F-1 | Decision 13's closing sentences | **Agrees.** The spec: a known-`None` target "is rejected by that **runtime** backstop and only there: the build-time audit keys on the two encode-only names", and "the **only** node-id-only fallback that survives is the pre-existing no-resolvable-definition case (an unbound owner / unresolvable target, where no definition — and thus no strategy — is available at all)". The docstring states the same two clauses, in the same order, with the same carve-out. |
| F-2 | Decision 10, step 2 | **Agrees.** The spec: "The shadow-install is the only way a `type`-strategy type carries a framework `resolve_typename` closure, so it is the only path reaching `encode_typename`'s `type` branch … during `id` resolution; the public `testing/relay.py::global_id_for` helper calls `encode_typename` directly with the recorded strategy and reaches that branch without an installed closure." The docstring is that sentence in source. |
| F-3 | Decision 8's closing paragraph | **Agrees.** The spec names the same three consumers in the same order with the same qualifiers — root `node(id:)` / `nodes(ids:)` via `_decode_or_graphql_error` converting to `GLOBALID_INVALID`; `decode_model_global_id` shared by the mutation flavors and the relation `<field>_id` decode; the `testing/relay.py` re-export. |

No spec edit is owed in either direction, and no new cross-home contradiction was created by this cycle.

Worker 3's Low on F-1's appositive is **confirmed rejected on its recorded reason**, re-derived rather than
accepted: `types/finalizer.py::_audit_globalid_filter_strategies` keys on `ENCODE_ONLY_GLOBALID_STRATEGIES`
only, so the runtime backstop is indeed the sole rejecter of the `None` case — and the appositive claims
nothing else, describing the cited function's standing role in wording the shipped sibling docstring and
Decision 13 both already use. Tightening one of three sites would put them out of step for no accuracy
gain.

#### Spec / companion pairing, re-derived after every edit

| Check | Result |
|---|---|
| Companion `## Decision N` → spec, by heading and anchor | **13 / 13.** Every companion Decision opens `Spec: [Decision N — …][spec-031-dN]`, and all 13 definitions resolve to a real heading slug in the spec. |
| Spec Decision → companion pointer | **13 / 13** `Rationale companion —` pointers, 13 distinct `[rationale-dN]` uses, all resolving to real companion heading slugs. |
| Every `**Post-ship:**` entry names a lookuppable home | **34 entries** (36 marker occurrences, two of them the file's own prose describing the convention): 24 under a `## Decision N`, 9 under `## Non-Decision deliberation`, 1 under `## Risks and open questions`. None is unlookuppable. The integration pass's `29` was a pre-append measurement; the five bullets it appended take it to 34, and the table row above now carries the re-derived figure. |
| Anchors, link definitions, cross-file fragments, both files | **0 dangling in-page anchors, 0 undefined ref-ids, 0 unused definitions, 0 broken definition paths, 0 dangling cross-file fragments.** Spec: 87 defs / 87 uses / 20 distinct in-page anchor targets. Companion: 60 / 60 / 15 distinct targets. |

The anchor figures need one note so the next pass does not read a regression into them. The integration
pass recorded 147 and 60; those are **occurrences**, this pass's 20 and 15 are **distinct targets**. Both
were re-measured here — 147 and 60 occurrences, unchanged — so the two rows describe different subjects and
neither falsifies the other.

#### The integration pass's own measured claims, re-derived

`docs/builder/BUILD.md` treats "a stated count" as a claim shape needing re-derivation, so the cycle's own
numbers were re-measured rather than carried:

- **X-4's shipped-commit delta.** `git show --numstat 7d892d6f`, partitioned: `docs/builder/` (8 files)
  `+5,267 / -0`; package `+734 / -119`; the three test trees plus the example schema `+1,227 / -114`;
  standing docs, terms CSV and the spec `+179 / -142`. Non-builder total `+2,140 / -375`, grand total
  `+7,407 / -375`, matching git's own `35 files changed, 7407 insertions(+), 375 deletions(-)` exactly.
  Every figure in the spec's closing sentence re-derives.
- **X-4's row-1 sub-count.** 15 in `tests/types/test_base.py`. The obvious grep returns **16**; the extra is
  `::test_interfaces_rejects_relay_globalid_named`, which is about `Meta.interfaces` rejecting a
  `relay.Node`-named entry and not about the strategy key at all. The population is 15, and the grep's
  vocabulary is again not the population.
- **X-4's row-2 sub-count.** 3 in `tests/filters/test_finalizer.py`, confirmed exactly.
- **X-1, X-2, X-3, X-5 all landed.** The invented test name is gone from both files and the shipped
  `::test_setting_error_framing_tracks_the_conf_key_constant` exists at `tests/types/test_relay_interfaces.py:2391`;
  the provenance block now reads "**Immediately after the move** the spec measured 148,526 bytes";
  `primary = True` sits on `ItemType.Meta` with the sentence beneath naming the model-label-routing
  invariant; and the Slice-3 checklist's Step-2 enumeration carries **absent (`None`) → reject** again.

#### Gates

| Check | Command | Result |
|---|---|---|
| Spec/glossary gate | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-031-globalid_encoding-0_0_9.md` | `OK: 31 terms` |
| Citation gate | `uv run python scripts/check_citations.py` | `OK: 812 citations resolve (731 in 431 .py files, 81 in KANBAN.md)` |
| Layout / ASCII / line length, the two source files | `uv run python scripts/check_trailing_commas.py --check <both>` | exit 0 |
| Anchors and link definitions, spec + companion | independent validator, both files | 0 / 0 / 0 / 0 / 0 |
| Staged anchors | the sweep above | clean; 9 prose-only hits |
| Spec status lines | read at the start of this spawn, per `worker-1.md` `## Spec status-line re-verification` | still accurate; `Status: **SHIPPED (0.0.9)**` and the header's five lines describe the current state, no edit owed |

#### Worker 3's two flagged items

- **`tests/types/test_relay_interfaces.py:2151`** carries "``encode_typename``'s ``type`` branch goes live
  for exactly this shape" inside `::test_type_strategy_child_shadows_inherited_framework_closure`. **No
  change owed, and it goes to the catalog as a recorded verdict rather than as work.** Re-derived: it is
  the only site in `tests/`, `examples/`, or the package carrying that framing, and it is a *narrower*
  claim than the one F-2 retired. F-2's clause said the branch was "the live implementation for exactly
  that shape" — a claim about the branch's whole population, which `testing/relay.py::global_id_for`
  falsifies. This one says the branch "goes live", i.e. is *installed*, for exactly that shape, inside a
  test whose entire subject is closure installation — and installation happens for exactly the shadow case.
  Worker 3's recommendation (a) is the right call. It enters the catalog only so the next reader who greps
  the retired phrasing finds the verdict instead of re-opening it.
- **The build-time audit does not key on a `None` strategy.** Confirmed above; no action needed, and F-1
  does not contradict it.

### Spec changes made (Worker 1 only)

**None to the spec or the companion.** This pass found no gap, conflict, or falsified sentence in either
file: the three docstrings agree with the contracts they overlap, and the five edits the integration pass
made re-derive as correct. Two corrections were made to this artifact's own earlier Worker 1 prose, both
recorded rather than silent:

| # | Site | Change | Reason |
|---|---|---|---|
| A1 | artifact line 8 preamble | "**A Worker 2 pass is owed.**" replaced by a statement of what the artifact now carries | The sentence was true when the plan was written and is not now. Per `docs/builder/BUILD.md` `## Spec rationale extraction`'s standing principle, the replacement states the current situation directly instead of narrating that it changed. |
| A2 | `## Spec / companion pairing`, the `**Post-ship:**` row | `29 entries (31 occurrences)` → the re-derived `34 entries (36 occurrences)` with its three-way split | The figure was measured before the same pass appended five bullets and reported as current — the inner-ring case (d) this cycle keeps producing, this time in the integration pass's own output. |

### For `bld-031-final.md` — `### Deferred work catalog` handoff

The final list, every item with a named owner. Items 1-3 carry forward from the integration pass; item 4 is
this pass's addition.

| # | Item | Source | Owner |
|---|---|---|---|
| 1 | **`spec-032`'s eight dangling citations into text that left `spec-031`**, in four claim families — the `Revision 6` / `Revision 7` references (`:13`, `:513`), Decision 1's moved justification (`:281`), Decision 3's moved rejected alternative (`:312`), and Decision 11's moved deferral plus the "no shipped `0.0.9` consumer" quote (`:9`, `:143`, `:452`, `:464`). `## Known-open item 3` states where each cited passage now lives. `spec-032` is out of this cycle's fence entirely. | `bld-031-slice-0` note 4; population re-derived by the integration pass from 3 sites to 8 | **maintainer**, or a future `032` cycle |
| 2 | **The `"Relay"` / `"Type generation"` Browse-by-category slash** in the Slice-5 GLOSSARY checklist bullet and `## Doc updates` admits two readings; `docs/GLOSSARY.md` satisfies the better one. Not a defect and out of fence; worth one sentence only if a future spec's template disambiguates the slash. | `bld-031-slice-5` | **maintainer** |
| 3 | **`docs/builder/bld-003-final.md`** survives from the `spec-003` cycle and was deliberately left in place at pre-flight (tracked, committed, out of the maintainer's fence, cannot collide with this cycle's `031`-named artifacts). A pre-flight deviation, not a defect. | build plan, pre-flight step 3 | **maintainer** |
| 4 | **`tests/types/test_relay_interfaces.py:2151`'s "goes live for exactly this shape" docstring.** Verdict recorded, **no change owed**: it is an installation claim inside a test about closure installation, which is narrower than and different from the population claim F-2 retired from source. Listed so a future grep for the retired phrasing finds the verdict rather than re-opening it; act only if that test file is being rewritten for another reason. | `bld-031-integration` Worker 3 Low, adjudicated at this re-run | **maintainer**, or whichever future pass owns that test file |

Closed, and listed only so the gate can see they were not dropped:

- The stale-`.py`-comment batch — re-derived from four clauses to three, dispatched, built, reviewed, and
  audited here. No longer a catalog item.
- `_first_model_label_emitter` / `_audit_model_label_routing`'s no-definition raises — judgement confirmed,
  deliberately uncontracted, pinned by `tests/types/test_finalizer.py`. No owner needed.
- `TODAY.md:14` — closed by Slice 5's audit.
- Slice 0's notes 1-3 (the resolver arity, DoD item 1's CSV claim, the pre-archival spec path) — discharged
  by Slices 2 and 5, each re-verified by the integration pass.

### Final status

`final-accepted`.

### Summary

The consolidation holds and the integration questions are clean. The three docstrings say what the shipped
code does and agree with the spec contracts they overlap — Decision 13's fail-closed split, Decision 10's
scoped shadow-install, Decision 8's three consumers — so this cycle created no cross-home contradiction
while correcting three. All three checklist boxes are justified against the diff; the plan's exclusion was
honored byte-for-byte; nothing was deferred and no box was over-ticked.

The inverse proof was re-run on a third axis. Compiled bytecode, docstrings stripped by CPython's own
`optimize=2` rather than a hand-rolled rule, reports both files byte-equivalent to HEAD, with six controls
proving the instrument can fail: four executable mutations detected, a docstring-only mutation invisible,
and the unstripped recompile differing. The two guards that make those controls real are that a control
which failed to mutate reports itself invalid, and that a mutation target is proved executable — by
surviving docstring stripping — *before* being aimed at, which is the mechanical answer to the misfire
Worker 3 recorded. The pass's own first instrument carried a wrong docstring rule and produced a false
positive that read exactly like a finding; recorded because it is that misfire's mirror image.

The staged-anchor count reconciles at nine, and the reason the three measurements differ is structural
rather than alarming: a sweep cannot see the record it is about to write. Four items go to
`bld-031-final.md`, each with a named owner; three carry forward and the fourth is a verdict recorded so it
is not re-opened.
