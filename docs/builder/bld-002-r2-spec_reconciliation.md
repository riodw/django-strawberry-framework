# Build: R2 — Reconcile spec-002 with what shipped

Spec reference: `docs/SPECS/spec-002-optimizer-0_0_2.md` (whole file; 7,006 bytes / 110 lines at pass start, post-R1)
Build plan: `docs/builder/build-002-optimizer-0_0_2.md` (residual item R2)
Status: final-accepted

**Deviation 3 of the build plan governs this artifact.** R2 has no Worker 2 pass — `BUILD.md`
`## Spec reconciliation` and `worker-1.md` `## Scope` make Worker 1 the only role that may mutate the
spec, and R2's entire deliverable is spec edits. So this single Worker 1 pass **wrote the plan below
AND performed the reconciliation**, and `Status: planned` here means "dispatch Worker 3 for the
audit", not "dispatch a builder". The `## Reconciliation performed` section stands in for the Worker
2 build report and keeps its subsection names so Worker 3 reads a familiar shape.

## Plan (Worker 1)

### Spec status-line re-verification

`spec-002-optimizer-0_0_2.md` has **no status/header block** — no target-release, status, owner, or
predecessor line adjacent to the title. Line 1 is `# Spec: Optimizer & Reverse-Relation Resolution`,
line 2 blank, line 3 `## Purpose`. Nothing to re-verify or falsify. Re-confirmed rather than
inherited from R1's identical finding: the file has changed since R1 read it (R1 changed it).

The spec's stale-by-tense *body* claims are this item's whole axis, and are handled per drift row
below.

### The two rulings the maintainer's framing forces, stated once

Everything below is applied to every row rather than re-decided per row.

1. **The spec states the corrected contract directly.** No amendment block, no retraction paragraph,
   no "as of round N" hedge, no "originally" clause (`BUILD.md` `## Spec rationale extraction`). A
   reader must never reconstruct what is currently true by applying a chronology. Where a claim is
   false at HEAD the sentence is **rewritten to what holds**, and the fact that it once read
   otherwise appears only in the rationale.
2. **Rule 2 versus the reader rule, resolved by R1's precedent and reused unchanged** (R1 hand-off
   item 6): *move and tense-mark when the claim is deliberation a later spec answered; delete when it
   is a false assertion about the package.* R2 adds the third case its own axis creates:
   **restate when the corrected behavior is this spec's own contract.** Which of the three applies is
   recorded per row in `### Drift-row dispositions`.

### The scope rule, and why it is written INTO the spec rather than only obeyed

The build plan's scope trap is real and D6 / D10 / D11 / D12 are where it bites. R1 preserved the
sentence that governs it (`## Purpose`: "It records that behavior at a high level only"), but that
sentence names only `spec-003`. Four later specs now own optimizer surface, and each of D10 / D11 /
D12 is a case where the *correct* fix is a pointer rather than a restatement — a disposition the
spec's own text does not currently license.

So the plan **extends the `## Purpose` scope paragraph to the family**, in one sentence, and makes
the licence explicit: where a later spec changed how an O-slice behaves, this spec states the
behavior that holds and names the owning spec, and does not restate that spec's rules. This is the
cheapest possible durable defence against the next pass rewriting this parent into a summary of its
four children — and it is a contract sentence, not narration, so it belongs in the spec.

### The un-rowed finding that reshapes D14: `## Current state` says almost nothing new

Worker 0's table is organized by CLAIM, so a SECTION that is wrong as a *structure* appears in it
only as D14's "standing-promise shape" note. Read end to end, `## Current state` carries five facts,
and **the only one stated nowhere else in the same 110-line document is O2's module path** — one
more is a lower-precision copy, two are exact copies, and the fifth is not a contract at all:

| `## Current state` carries | Also stated at |
|---|---|
| the O1-O6 roster (six one-liners) | `## Shipped slices`' six `###` headings, and `## Implementation checklist`'s six boxes |
| O2's module path `optimizer/walker.py` | nowhere — **unique** |
| `DjangoOptimizerExtension` exported from `__init__` | `## Visibility status` ("public via `DjangoOptimizerExtension`"), minus the path — **near-duplicate** |
| "root optimizer plans are stashed on context for introspection" | `### O3` ("stashes the plan on context") |
| "the extension is covered by the optimizer test suite" | nowhere — and it is a repo-status claim, not a contract |

That makes D14 answerable without inventing a heading. spec-001's cycle retitled its own
`## Current state` to `## Prior art` because that section *contained* a prior-art survey; spec-002's
contains a shipped-slice roster, so the same retitle would be a lie. **The disposition is to remove
the heading, re-site the module path and the export path where each is normative, and drop the
test-suite claim**, which discharges the standing-promise half of card 052's deferral *and* removes
a three-way duplication of the slice roster in one edit. The alternatives considered and rejected go
in the rationale.

**This is where the 3-anchor constraint bites.** `djangooptimizerextension`'s sole spec-body link is
inside `## Current state`'s O3 line. The plan re-sites it into `### O3 — Root-gated optimizer hook`,
which is the surviving **contract** prose for the same mechanism, and adds a second link in
`## Visibility status`'s public-surface sentence, where the concept is also normative. That takes the
anchor map from 1/1/1 to 1/1/2 — a deliberate change, reported as such, and the first spare link this
spec has ever carried.

### Drift-row dispositions

Each row was **re-verified against source at HEAD before being ruled on**, not trusted from the
table; the evidence is in `### Drift-row re-verification`. `restate` = the corrected behavior is
spec-002's own contract and the sentence is rewritten. `point` = real HEAD behavior a later spec
owns; one clause names it and the owner. `rationale` = no spec-side contract, recorded in the
companion's change record. `none` = the claim is true at HEAD and at the right altitude.

| Row | Disposition | One-line reason |
|---|---|---|
| D1 | **restate** | O1's attachment site is spec-002's own contract and it is flatly false at HEAD. |
| D2 | **restate + point** | The many-side shape is O1's; the row bound is `spec-047`'s and is named, not re-specified. |
| D3 | **restate + rationale** | The opt-out shipped and lands *inside O1* (a skip set), so it becomes contract here; that it was an open question this spec left is the rationale's. |
| D4 | **restate** | O2's signature is spec-002's own contract and is stated wrong. |
| D5 | **restate** | `_optimizer_field_map` does not exist; a spec naming a symbol the package lacks is the worst failure mode available. |
| D6 | **none** | "produces an `OptimizationPlan`" is true; enumerating the plan's eleven fields IS the scope trap. |
| D7 | **restate (narrow)** | The stash is true; "for introspection" narrows a load-bearing hand-off to a diagnostic. Two words, no new surface. |
| D8 | **restate + point** | A `Manager` is a non-`QuerySet` value that does NOT pass through — the architecture sentence is false as written. G1 is named and pointed at `spec-035`. |
| D9 | **restate + point** | Unqualified, O5's sentence is false for mutations; the gate is `spec-035`'s and is named, not re-specified. |
| D10 | **point** | O6's downgrade is spec-002's, but how the target queryset is obtained is `spec-045`'s sealed boundary. One clause. |
| D11 | **restate + point** | "runs from the `resolve` hook" reads as exclusive and is not; the second caller is named and pointed at `spec-033`. |
| D12 | **point** | O4's plain-relation statement stays true; the nested-connection delegation is `spec-033`'s. One clause. |
| D13 | **rationale** | The answer (`Meta.optimizer_hints`) is `spec-004` B4's contract, not spec-002's. Nothing to restate here. |
| D14 | **restate (structural)** | `## Current state` removed and its two unique facts re-sited; `## Visibility status` kept by title (a read-only sibling cites it). |
| D15 | **none** | All four upstream pointers re-verified present. No edit. |

**Why D13 and D3 diverge although both were `## Open questions` rows** (R1 hand-off item 2 asked for
this routing to be stated once). Both questions were answered by shipped work, and neither has a
spec-side target left. The test is not "did it ship" but **whose contract the answer is**: D3's
answer lives inside O1's own resolver-attachment pass, so it is spec-002 contract and must be stated
here; D13's answer is a `Meta` option `spec-004` specifies and `docs/GLOSSARY.md` catalogues, so
restating it here would be the scope trap wearing an "it shipped!" badge. Both get a rationale
change-record entry either way, because both are claims the spec once carried.

### DRY analysis

**Helper inventory checked.** Not applicable in the form `worker-1.md`
`### Package-wide helper inventory before helper planning` defines it: that step prevents duplicated
*code* helpers, and this item writes no `.py` file and plans none. The DRY question R2 does ask is
the build plan's preamble rule — the rationale carries the deliberation, the spec carries the
contract, neither restates the other — plus the un-rowed within-spec duplication above.

- **Existing patterns reused.** The rationale file's entry shape, created by R1 and unchanged here:
  `### <heading> — <subject>`, a `Spec: [heading][ref]` lead, italic `*Moved …*` /
  `*Alternative rejected …*` / (new here) `*Changed …*` leads, and a
  `**Claims the spec no longer makes.**` line per entry. R2 appends entries in that shape rather than
  inventing a change-log format; `worker-1.md` rule 4 makes the file append-only during a build.
  Symbol references use `path::QualifiedName` (`AGENTS.md` rule 27), which is the pointer mechanism
  every "point elsewhere" disposition rests on.
- **New helpers justified.** None. No source, no test, no script.
- **Duplication risk avoided.** Four, all live here:
  1. **The same fact in both files.** Every rewritten claim's *explanation* goes only to the
     rationale; every *contract* stays only in the spec. Measured in
     `### Spec-versus-rationale overlap`.
  2. **The within-spec three-way roster duplication** (`## Current state` / `## Shipped slices` /
     `## Implementation checklist`), addressed by the D14 disposition above.
  3. **Absorbing four sibling specs.** Prevented structurally by the `## Purpose` scope sentence and
     by the per-row `point` disposition, and audited in `### Scope-trap audit` by counting what each
     pointer clause actually asserts.
  4. **Re-specifying `docs/GLOSSARY.md`.** The glossary's `DjangoOptimizerExtension` entry already
     carries a fourteen-bullet shipped-behavior list including G1 and G2. The spec must not become a
     second copy of it; where the two would overlap, the spec states only what its own O-slice
     promises.

### Implementation steps

Pin-at-write-time line numbers are from the 110-line post-R1 spec.

1. `## Purpose` (6): extend the scope paragraph to the optimizer family and state the
   state-the-behavior-name-the-owner licence. **Do not touch sentence 1** — it is the sole carrier of
   the `only-projection` anchor.
2. `## Architecture decision` (33-37): restate the root-gate paragraph for D8 and D11 — normalization
   and `Manager` coercion, the evaluated-queryset pass-through, and the connection field as the
   second caller of the shared plan-application tail.
3. **Add every `djangooptimizerextension` destination BEFORE removing its source** (the one ordering
   rule that makes an anchor drop impossible): link it in `### O3` and in `## Visibility status`
   first, verify, only then remove `## Current state`.
4. `### O1` (40-41): restate the attachment site (D1), the consumer-resolver skip (D3), the forward-FK
   elision qualifier (un-rowed), and the many-side bound (D2).
5. `### O2` (43-44): restate the signature (D4) and the field-map symbol (D5); name the module (the
   fact rescued from `## Current state`).
6. `### O3` (46-47): restate the stash sentence (D7) and carry the re-sited anchor. Fix the missing
   blank line before `### O4` (R1 hand-off item 7a).
7. `### O4` (48-49): append the nested-connection pointer (D12).
8. `### O5` (51-52): append the `QUERY`-only projection gate (D9).
9. `### O6` (54-55): append the visibility-boundary clause (D10).
10. Remove `## Current state` (20-30) entire, after step 3 has verified both destinations.
11. `## Visibility status` (64-65): carry the export path rescued from `## Current state`.
12. **Leave untouched:** `## Problem statement` (sole carrier of `djangotype`),
    `## Coordination with spec-001…`, `## References` (D15 verified), `## Implementation checklist`,
    and the link-definition block except for what steps 1-11 require.
13. Append four entries plus a provenance update to
    `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md`.
14. Run every verification command, quote it exactly, and prove the anchor map mechanically.

**Sections deliberately not opened:** listed at step 12, with reasons in
`### What deliberately STAYED, and why`.

### Test additions / updates

None, and none possible: this item writes no `.py` file and no test. `AGENTS.md` rule 15 forbids a
`pytest` run after edits and none is owed — no source and no test is in this diff. The executable
checks that stand in for tests are the commands in `### Validation run` plus the throwaway script in
`### Temp tests used`; each has a recorded pre-edit baseline.

### Implementation discretion items

None delegated — there is no Worker 2 pass to delegate to. Every judgement call is decided in
`### Implementation notes`.

### Dispatched findings checklist

R2 is neither a spec slice (spec-002's slices O1-O6 shipped at `0.0.2`) nor a review round, so there
is no `## Slice checklist` to copy verbatim; per `BUILD.md` `## Review rounds`,
`### Dispatched findings checklist` is the named substitute in this position. The boxes are R2's
obligations as the build plan's checklist line, the maintainer's framing, and R1's consolidated
hand-off state them. **Ticked by Worker 1 in this pass** because Deviation 3 gives it the performer's
role; Worker 3 audits the ticks, Worker 1 re-audits at final verification.

- [x] Every one of the fifteen drift rows D1-D15 is **re-verified against source at HEAD** and given
      an explicit disposition with a reason (`### Drift-row re-verification`,
      `### Drift-row dispositions`).
- [x] Every claim the package falsifies is **restated as the contract that holds**, or handed to the
      spec that now owns it. No claim known-false at HEAD survives in the spec.
- [x] **No explanation landed in the spec.** No amendment block, no retraction paragraph, no
      "originally" / "as of" / "used to" chronology — those three return zero hits over the whole
      file. The wide chronology sweep returns exactly one hit, line 8's `no longer` inside R1's
      `final-accepted` rationale pointer, which is the sanctioned shape. (Headline tightened at final
      verification: "returns zero hits" was true of the narrow regex and false of the wide one the
      review ran, and naming which is what makes the box re-derivable.)
- [x] Every change carries a rationale entry **naming the spec section by heading and anchor**, and
      each records the alternatives rejected and the claims the spec may no longer make.
- [x] The **scope trap** is answered per row: D6 / D10 / D11 / D12 are each ruled and reasoned, and
      the spec gained a durable scope sentence rather than four ad-hoc judgements.
- [x] The **3-anchor constraint** holds: `check_spec_glossary.py` exits 0 with `OK: 3 terms …`, and
      the anchor map is measured before and after. The terms CSV was not touched.
- [x] `import_spec_terms --check` exits 0 with `OK: 49 done cards have glossary links.`
- [x] `check_trailing_commas.py --check` exits 0 on the spec, the rationale, and this artifact;
      neither standing doc gains a raw `path:NN` reference (`AGENTS.md` rule 27).
- [x] Spec byte count reported before and after, by two independent measurements that agree.
- [x] Package source, tests, `examples/`, `CHANGELOG.md`, the sibling specs, the terms CSV, the
      kanban DB and its rendered docs were **not** edited. Every correctness finding in shipped source
      is recorded and escalated, not fixed (`### Source-correctness audit`).
- [x] The `KANBAN.md:310` decision is written out in executable form for R3, and every hand-over
      carries a named owner (`### Notes for Worker 1 / Worker 3`).

---

## Reconciliation performed (Worker 1, in place of the Worker 2 build pass)

### Files touched

- `docs/SPECS/spec-002-optimizer-0_0_2.md` — the eleven edits of the implementation steps.
- `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` — four appended entries and a provenance
  update.
- `docs/builder/bld-002-r2-spec_reconciliation.md` — this artifact.
- `docs/builder/worker-memory/worker-1.md` — one appended entry under the existing
  `## spec-002 residual cycle` heading (gitignored; not part of the diff).
- `docs/builder/temp-tests/r2-spec002/` — one throwaway verification script (gitignored).

Nothing else. `docs/SPECS/appx/spec-002-optimizer-0_0_2-terms.csv` is byte-untouched.

### Byte counts

Measured at close, after the last edit to each file.

| File | Before (post-R1) | After | Delta |
|---|---|---|---|
| `docs/SPECS/spec-002-optimizer-0_0_2.md` | 7,006 / 110 lines | **9,844 / 103 lines** | **+2,838 (+40.5%), -7 lines** |
| `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` | 14,296 / 224 lines | **33,555 / 486 lines** | **+19,259** |

**Two independent measurements of the spec delta agree.** `wc -c` against the working tree minus the
R1 artifact's recorded 7,006. And, independently, via HEAD: the read-only HEAD copy measures 7,398
(`git show HEAD:… > <scratch outside the repo>`), the working tree measures 9,844, so the whole-cycle
delta is +2,446; R1's recorded delta was -392, leaving R2 at 2,446 + 392 = **+2,838**. The two routes
use different baselines and agree exactly.

**A reconciliation grows a spec; that is the correct sign, and 40% is the honest number.** R1 removed
narration and shrank the file 5.3%. R2's job is the opposite: nine of the fifteen drift rows are the
spec saying something less specific than the package does (a three-parameter signature for a
five-parameter function, an unqualified pass-through rule with two exceptions, a projection with no
operation gate), and the only way to state a corrected contract is more words than the wrong one
took. The counterweight is the -7 lines: `## Current state` left. Of the +2,838, roughly 950 bytes
are the six pointer clauses (spec lines 23, 25, 33, 42, 45, 48) plus the `## Purpose` scope
paragraph, which together keep four sibling specs *out* of this document — the scope trap's price,
paid in bytes rather than in scope. (`seven` at build time, which counted the scope paragraph as a
seventh clause; corrected at final verification.)

### Drift-row re-verification

Every row re-read at HEAD against the symbol the row names, not against the row's claim. Where the
re-verification found more than the row said, the extra is in `### Beyond the drift table`.

| Row | Re-verified at | Verdict |
|---|---|---|
| D1 | `types/finalizer.py::finalize_django_types` (calls `_attach_relation_resolvers` in its Phase 2 loop); `types/base.py::DjangoType.__init_subclass__` (stamps `_is_default_get_queryset`, no resolver attachment) | confirmed; the sentinel half is still accurate |
| D2 | `types/resolvers.py::_make_relation_resolver` — many-side returns `list(bounded_rows(getattr(root, accessor_name).all(), info))`, with a `_prefetched_objects_cache` fast path returning `bounded_rows(...)` over the cached rows | confirmed |
| D3 | `types/finalizer.py` #"skip_field_names=definition.consumer_assigned_relation_fields"; `types/resolvers.py::_attach_relation_resolvers` skips those names; `types/definition.py` #"consumer_assigned_relation_fields: frozenset[str]" | confirmed shipped |
| D4 | `optimizer/walker.py::plan_optimizations` — `(selected_fields, model, info=None, *, runtime_prefixes=None, source_type=None)` | confirmed, exact |
| D5 | no `_optimizer_field_map` anywhere in `django_strawberry_framework/`; three hits, all **test function names**, in `tests/optimizer/test_field_meta.py`. HEAD reads `optimizer/walker.py::_resolve_field_map` | confirmed; see `### Source-correctness audit` |
| D6 | `optimizer/plans.py::OptimizationPlan` — **eleven** dataclass fields, plus `finalize()` and `_assert_under_construction` | confirmed, and the row **undercounts**: it names five additions, there are six (it omits `prefetch_path_resolver_keys`) — corrected at final verification, see `### Spec changes made (Worker 1 only)` |
| D7 | `optimizer/_context.py` — five `DST_OPTIMIZER_*` keys, `DST_OPTIMIZER_KEYS`, `clear_optimizer_context`, called from `optimizer/extension.py::DjangoOptimizerExtension.on_execute` | confirmed |
| D8 | `optimizer/extension.py::DjangoOptimizerExtension._optimize` — `normalize_query_source` coercion, then `if getattr(result, "_result_cache", None) is not None` | confirmed |
| D9 | `optimizer/walker.py::_enable_only_for_operation` returns `operation is None or operation is OperationType.QUERY`, threaded through the whole walk as `enable_only` | confirmed **with a correction**: the gate is in the **walker**, not in `apply()`. `OptimizationPlan.apply()` is unchanged and still calls `.only()` whenever `only_fields` is non-empty; under a non-`QUERY` operation `only_fields` is simply never populated |
| D10 | `optimizer/walker.py` #"apply_type_visibility_sync(target_type, queryset, info, allow_sliced=True)" in the child-queryset build; `utils/querysets.py::apply_type_visibility_sync` | confirmed |
| D11 | `optimizer/extension.py::DjangoOptimizerExtension.on_execute` and `::apply_to`; `connection.py` calls `apply_connection_optimization` twice, which reaches the same `apply_to` | confirmed |
| D12 | `optimizer/nested_planner.py`; `optimizer/nested_fetch.py::NestedConnectionStrategy` (a `Protocol`), with `lateral_fetch.py` / `single_parent_fetch.py` implementations | confirmed |
| D13 | `optimizer/hints.py` (`OptimizerHint`, `Meta.optimizer_hints`); `spec-004` B4 #"the DRF-shaped analog of strawberry-graphql-django's `disable_optimization=True`"; `docs/GLOSSARY.md` `## OptimizerHint` **Status:** shipped (`0.0.3`) | confirmed answered |
| D14 | the four headings, plus the two prose citation sites | confirmed, and **reshaped** — see `### The un-rowed finding that reshapes D14` |
| D15 | `graphene_django/converter.py` in the checkout `AGENTS.md` line 2 names: `convert_django_field` at `:182`, `convert_onetoone_field_to_djangomodel` at `:274`, `convert_field_to_list_or_connection` at `:342`, `convert_field_to_djangomodel` at `:381`. `~/projects/strawberry-django-main/strawberry_django/optimizer.py` and `fields/field.py` both exist | **all four locators verified present; no edit** |

D15's two URLs (`github.com/tfoxy/graphene-django-optimizer`,
`strawberry.rocks/docs/django/guide/optimizer`) were **not** fetched — no worker in this cycle has
network access as part of its contract, and a URL is not verifiable read-only from the tree. Both are
stable upstream landing pages named by `AGENTS.md` line 2's own reading list; recorded as unverified
rather than claimed as verified.

### Beyond the drift table

The table is organized by CLAIM, so it cannot see a claim the spec never made or a defect in a
SECTION's structure. Five findings the sweep added:

1. **`## Current state` is a three-way duplicate, not just a badly-named section.** The finding that
   reshaped D14; full argument in the plan above and in the rationale entry.
2. **The forward-FK resolver has a second return shape the spec never mentioned.** Under B2 FK-id
   elision `types/resolvers.py`'s forward resolver returns a stub carrying only the target's
   identifier, not the related attribute. D2 covers only the many-side. Restated in O1.
3. **D6 undercounts.** `OptimizationPlan` carries `prefetch_path_resolver_keys` as well, which the
   row omits. It changes nothing about the row's disposition (`none`) — recorded because a stated
   count is a claim, and this one is re-derivable: eleven dataclass fields by `ast`, six beyond the
   five bags the row's own parenthesis names. (`seven` at build time; corrected at final
   verification.)
4. **D9's mechanism is in the walker, not in `apply()`.** Recorded above. It matters for the fix: the
   spec's `apply()` sentence is byte-true and was left verbatim; only the walker sentence needed the
   gate.
5. **`## Coordination` and the removed `## Current state` no longer disagree.** R1 hand-off item 7b
   flagged that `## Coordination` credited "this optimizer spec **family**" while `## Current state`
   claimed O1-O6 shipped under *this* spec. Removing `## Current state` and stating the family scope
   rule in `## Purpose` resolves it without an edit to `## Coordination`'s own sentence. Verified by
   reading both after the change rather than by assuming.

### Source-correctness audit

`AGENTS.md` rule 5 governs a fix once the maintainer authorizes one; it does not make a documentation
cycle a code cycle. Package source was read-only throughout. **No correctness defect was found in
shipped optimizer source.** Every drift row resolved to the spec being behind the package, never the
package being wrong.

One **maintenance** finding, escalated rather than fixed:

- **Four live-code sites still carry the deleted symbol name `_optimizer_field_map`** (corrected at
  final verification from the three this section named at build time; the fourth is in `scripts/`,
  which the build-time sweep scoped to `tests/` and missed):
  - `tests/optimizer/test_field_meta.py` — three test **function names**:
    `test_optimizer_field_map_populated`, `test_optimizer_field_map_contains_relations`,
    `test_optimizer_field_map_respects_fields_filter`.
  - `scripts/review_inspect.py` #"_optimizer_field_map" — a member of the inspector's optimizer-token
    tuple. Dead weight rather than a wrong name: the token can never match, so the inspector silently
    reports nothing for it.

  `_optimizer_field_map` was consolidated into `DjangoTypeDefinition.field_map`, and `AGENTS.md`
  rule 27's closing clause ("renaming a symbol means grep-sweep `::OldName` in the same change") was
  satisfied for package source and missed at all four. It is a rename sweep, in `tests/` and
  `scripts/`, which this cycle may not write; it is also how a reader grepping for the spec's old
  `_optimizer_field_map` finds live hits and concludes the symbol exists. **Owner: maintainer** (or a
  future test-hygiene card). Not a correctness defect — the tests test the right thing under the
  wrong name, and the stale token changes no inspector output.

  **Not part of that sweep, measured so the maintainer does not widen the fix:** the name also
  survives in prose in `CHANGELOG.md`, `KANBAN.md`, `docs/SPECS/spec-010-foundation-0_0_4.md`, and
  `docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md`, where it is a correct record of the
  mechanism `spec-016` retired. Two sibling specs do use it in the present tense —
  `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` (B4 / B7) and
  `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` (its opening constraint list) — but
  both are read-only in this cycle and stale-in-wording only, the same class as hand-off item 4's
  `spec-003` finding.

One **cross-document tension** observed while verifying, escalated to R3 and the maintainer:

- `docs/GLOSSARY.md` gives `## only() projection` **Status:** shipped (`0.0.2`) and
  `## DjangoOptimizerExtension` shipped (`0.0.2`), while `CHANGELOG.md`'s `[0.0.2]` entry describes
  only an "Early `DjangoOptimizerExtension` … for depth-1 N+1 prevention" and puts selection-tree
  planning, nested `Prefetch` chains, `only()` projection and the `get_queryset` downgrade under
  `[0.0.3]`. One of the two is wrong about which release carried O2-O6. **This spec deliberately
  states no version** — `## Visibility status` says "O1 through O6 have shipped" with no number — so
  the reconciliation neither inherits nor propagates the disagreement. `CHANGELOG.md` is closed to
  this cycle (`AGENTS.md` rule 21) and `docs/GLOSSARY.md` is DB-generated; **owner: R3's durable-doc
  audit, escalating to the maintainer.**

Also observed and **not** a defect: `CHANGELOG.md`'s `[0.0.2]` entry says relation resolvers are
"attached at `DjangoType.__init_subclass__`", which D1 falsifies at HEAD. It is correct **as
history** — that is where they were attached at `0.0.2` — and a changelog is a record of releases,
not a standing contract. This is exactly the distinction that makes the same sentence a defect in the
spec and correct in the changelog. No report is owed; recorded so a later pass does not raise it.

### What deliberately STAYED, and why

- **`## Problem statement`, entire.** Both bullets are implementation-relevant "why" (the
  `RelatedManager` fact is why O1 exists; the before-relation-resolvers-evaluate fact is why O3's
  gate is at the root), both are true at HEAD, and bullet 1 is the sole carrier of the `djangotype`
  anchor. The second bullet survives D11 specifically: the *problem* is still that planning must run
  from the operation root; that a second caller now enters the same tail is an architecture fact, and
  it is stated in `## Architecture decision` where it belongs.
- **`## References`, entire.** D15 verified all four locators. The register (bare code spans, one
  symbol-qualified path, two URLs) is unchanged.
- **`## Implementation checklist`, entire.** Six ticked boxes recording what this spec's build
  delivered. It is a closed record, not a promise about the present, so the standing-promise argument
  does not reach it.
- **`## Coordination with spec-001…`'s three claims.** All three re-verified —
  `types/base.py::DjangoType.__init_subclass__` stamps `_is_default_get_queryset`,
  `types/base.py` #"return not cls._is_default_get_queryset" backs `has_custom_get_queryset`, and
  `registry.py::TypeRegistry` is the shared reverse lookup. The only edit is a locator added to the
  sentinel sentence, because D1 moved the *other* thing `__init_subclass__` used to do and a reader
  needs to know this one did not move.
- **`OptimizationPlan.apply()`'s sentence in O5**, verbatim. It is byte-true at HEAD; see the D9
  correction above.
- **`## Visibility status` as a heading.** In the deferral's target set on its own merits, held by a
  live cross-spec pointer in a read-only sibling. Reasoning in the rationale.

### Minimal repairs made to keep surviving prose coherent

Two, both forced by a removal, neither introducing a claim the spec did not already make.

1. **`## Visibility status` absorbed the export path.** `## Current state`'s "`DjangoOptimizerExtension`
   is exported from `django_strawberry_framework.__init__`" and `## Visibility status`'s "The
   optimizer is public via `DjangoOptimizerExtension`" are one fact stated twice at different
   precisions. Merged into the more precise form, in the section whose subject is the public surface.
   Verified: `django_strawberry_framework/__init__.py` #"from .optimizer import DjangoOptimizerExtension"
   plus its `__all__` entry.
2. **The O2 slice absorbed the module path.** `## Current state` was the only place the spec said
   where the walker lives. `optimizer/walker.py` now opens the O2 paragraph, where the symbol it
   qualifies already was.

**Two glossary destinations were added BEFORE the source was removed.** The
`djangooptimizerextension` link was written into `### O3` and into `## Visibility status`, the anchor
map was measured, and only then was `## Current state` deleted. That ordering is what makes an anchor
drop impossible rather than merely unlikely; the reverse order passes the same final check but has a
window in which the file is broken.

### Validation run

```
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-002-optimizer-0_0_2.md
OK: 3 terms - all have glossary entries and at least one spec link.
exit=0

$ uv run python examples/fakeshop/manage.py import_spec_terms --check
OK: 49 done cards have glossary links.
exit=0

$ uv run python scripts/check_trailing_commas.py --check \
    docs/SPECS/spec-002-optimizer-0_0_2.md \
    docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md \
    docs/builder/bld-002-r2-spec_reconciliation.md
exit=0

$ grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+' docs/SPECS/spec-002-optimizer-0_0_2.md \
    docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md
exit=1        # no match, in either file — rule 27 preserved, not established

$ git diff --check
exit=0
```

Every one matches the build plan's recorded baseline and R1's post-move re-run exactly. Both
DB-touching commands are read-only (`check_spec_glossary.py` without `--auto-link`;
`import_spec_terms --check`). Each was run **before** the edits to the identical output, so the edits
are proved neutral rather than merely passing. No `ruff` run: no `.py` file was touched. **No
`pytest` run**: no source and no test is in this diff, none was in the plan, and `AGENTS.md` rule 15
forbids one.

**Anchor map, before and after** (occurrences counted, not matching lines):

```
$ grep -o '\]\[glossary-[a-z0-9_-]*\]' docs/SPECS/spec-002-optimizer-0_0_2.md | sort | uniq -c
   2 ][glossary-djangooptimizerextension]
   1 ][glossary-djangotype]
   1 ][glossary-only-projection]
```

**1 / 1 / 2, up from R1's 1 / 1 / 1** — the one deliberate change, and the first spare link this spec
has carried. `djangooptimizerextension`'s only link lived in `## Current state`, which this pass
removed; it is now in `### O3`'s mechanism sentence and in `## Visibility status`'s public-surface
sentence, both surviving **contract** prose. There are no inline `](../GLOSSARY.md#…)` forms in the
file, so the reference-style count is the whole population. The terms CSV was not opened; `git diff
--stat` on it is empty.

### Link-convention and anchor audit

Checked mechanically for both files by `docs/builder/temp-tests/r2-spec002/audit.py`:

- One `<!-- LINK DEFINITIONS -->` block each, all 10 canonical group headers in `START.md`'s exact
  order, empty groups retained, alphabetical within every group.
- Spec: 4 defs / 4 used refs, 0 undefined, 0 orphaned. Rationale: 19 defs / 19 used refs, 0
  undefined, 0 orphaned.
- Every def target `os.path.exists`-checked with the fragment stripped and URLs excluded: all 23
  present. Depth is right — the rationale sits two levels below `docs/`, so `docs/` targets resolve
  `../../` and `docs/SPECS/` siblings resolve `../`. R2 added nine defs: eight sibling specs, all
  `../spec-NNN-….md`, plus one further spec-002 anchor (`#visibility-status`).
- No inline cross-file link in either body outside fenced code.
- No raw `path:NN` in either body (rule 27).
- Every in-page anchor the rationale cites resolves against a surviving spec heading, computed by
  slugging the spec's actual headings. `#visibility-status` is new and resolves; nothing points at
  the removed `#current-state`.

**A slugger trap worth carrying, measured here.** `scripts/check_spec_glossary.py::github_anchor`
collapses whitespace **runs** to one hyphen; GitHub's own slugger replaces spaces one at a time. For
a heading like `### O1 — Custom relation resolvers` the em dash is stripped and leaves two spaces, so
the script computes `o1-custom-relation-resolvers` where GitHub renders
`o1--custom-relation-resolvers`. Nothing in the tree links to such an anchor today, so no link is
broken — but it is a **false pass**, not a false failure, which is the dangerous direction. It is why
this pass keyed the rationale's new entries to `#shipped-slices` rather than to per-slice anchors.
Third slugger trap in this cycle family; carried to the tracked checker item, not raised as a
finding.

### Spec-versus-rationale overlap

The build plan's DRY rule made mechanical. Both files whitespace-normalized, blockquote markers
stripped, link-definition blocks removed:

- **Longest shared prose run: 12 words, one occurrence** — *"the framework gets from Strawberry field
  resolution to the underlying Django model"*. That is R1's number, unchanged: the seam sentence,
  quoted inside the rationale's statement that it stayed in the spec.
- **2.9% of the spec's 6-word shingles appear anywhere in the rationale** (31 of 1,056).

**The gloss on that second figure was wrong and is corrected here** (Worker 3 Low 4, re-measured at
final verification over a wider population than either pass reported). Build time claimed "every one
is inside a labelled quotation of a spec sentence the entry is explaining"; the review named four
counter-examples. Re-derived, there are **nine** shared runs at six words or longer, and they fall
into three classes rather than one:

| Class | Runs | Rationale sites |
|---|---|---|
| labelled quotation of a spec sentence | 2 | the 12-word seam sentence; the 7-word `## Purpose` scope rule |
| the entry heading naming what the spec's pointer sentence promises the file covers | 1 | `### Whole-document scope — why the optimizer became its own document` |
| the rationale's own unquoted `*Changed — …*` prose | 6 | the four the review named, plus *"implementation, two entry points; the connection path is"* and *"the hand-off the generated relation resolvers"* |

**Disposition: the six are accepted as change-record prose, and the gloss — not the runs — is what
was false.** A `*Changed —*` entry is a dated record of one edit; restating the sentence it explains
is the record doing its job, and a record that stops matching a later spec has not gone stale. The
alternative (reword six rationale sentences to describe rather than restate) adds unreviewed
judgement to close a 6-to-10-word overlap, where R1's one accepted trim removed a restatement of a
`BUILD.md` mechanism that has a canonical home elsewhere. None of these six has one.

**One overlap was found and removed during the pass, which is why the number is 12 and not 14.** The
first draft of the `## Purpose` rationale entry restated the widened scope rule almost verbatim
(a 14-word run) while explaining why it was widened. A rationale that re-states a contract sentence
is the exact mechanism the plan's DRY rule names — the two copies drift, and the reader cannot tell
which is current. Rewritten to describe the rule's *shape* instead of its text. Recorded rather than
silently fixed, because the failure is a template one: an entry explaining a sentence is the place
most likely to quote it.

### Temp tests used

One throwaway script under `docs/builder/temp-tests/r2-spec002/` (gitignored), read-only:

- `audit.py` — link-scaffold audit (defs / uses / undefined / orphans / group-header order /
  alphabetical order / `os.path.exists` per target with the fragment stripped), inline-cross-file-link
  sweep, rule-27 sweep, in-page-anchor resolution against slugged spec headings, the anchor map, and a
  chronology-phrase regex over the whole spec.

The overlap scan and the byte-delta reconciliation were run as inline one-offs rather than saved.
Neither promotes to a permanent test: there is no package behavior to pin and no production code in
the diff. `r2-spec002` is a new directory; the `r1-spec002` and `r1-spec002-fv` siblings were neither
read, reused, nor deleted.

### Failability proofs

None; this pass introduced no new boundary, guard, gate, or rejection path. It writes no executable
code.

### Hot-path budget

Not applicable; plan declares no hot path (`build-002-optimizer-0_0_2.md` preamble: *"Hot-path
declaration: none. No residual item changes package source"*).

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Concurrent-session churn observed (not this pass's, not reverted)

`git status --short` at pass open and at pass close, both measured, **identical at both ends except
for this pass's own artifact**:

```
 M KANBAN.html                                        <- concurrent session (baseline-dirty)
 M KANBAN.md                                          <- concurrent session (baseline-dirty)
 M docs/SPECS/spec-002-optimizer-0_0_2.md             <- this cycle (R1 + R2)
 M docs/SPECS/spec-042-debug_toolbar-0_0_14.md        <- concurrent session (baseline-dirty)
 M docs/SPECS/spec-043-test_client-0_0_14.md          <- concurrent session (baseline-dirty)
 M docs/SPECS/spec-044-debug_extension-0_0_14.md      <- concurrent session (baseline-dirty)
 M docs/SPECS/spec-050-debug_extraction-0_0_19.md     <- concurrent session (baseline-dirty)
 M docs/SPECS/spec-051-boundary_dry_squeeze-0_0_20.md <- concurrent session (baseline-dirty)
 M examples/fakeshop/db.sqlite3                       <- concurrent session (baseline-dirty)
 M examples/fakeshop/test_query/README.md             <- concurrent session (baseline-dirty)
?? docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md  <- this cycle (R1, extended by R2)
?? docs/builder/bld-002-r1-rationale_move.md              <- this cycle (R1)
?? docs/builder/bld-002-r2-spec_reconciliation.md         <- this cycle (this artifact)
?? docs/builder/build-002-optimizer-0_0_2.md              <- Worker 0's plan
```

Fourteen paths: the nine baseline-dirty concurrent-session paths, Worker 0's untracked plan, and
this cycle's four (the spec, the rationale, R1's artifact, and this one). **The list did not grow**,
so nothing is owed to Worker 0 under the plan's growth rule. None
was edited, reverted, or `git checkout`-ed (`AGENTS.md` rule 34); no `stash`, `checkout`, `restore`,
or `worktree` was used at any point. The one read-only HEAD copy went to a scratch path **outside**
the repo.

### Implementation notes

- **The scope rule went into the spec, not just into the pass's judgement.** Ten pointer-versus-
  restate decisions is enough that a rule the document itself carries is cheaper than ten defensible
  paragraphs in a file the next author will not read. It is also the only artifact of this pass that
  constrains a *future* author, which is what makes it contract rather than commentary.
- **Six pointer clauses (spec lines 23, 25, 33, 42, 45, 48), and each one earns its place by what a
  reader would otherwise get wrong.** (`Seven` at build time, which counted the `## Purpose` scope
  paragraph — a rule, argued as such two bullets above — as a seventh clause; corrected at final
  verification.) Not
  "here is where more detail lives" — that is unbounded — but "the sentence above is false without
  this qualifier". A reader who believed the unqualified O5 sentence would expect column deferral on
  a mutation; a reader who believed the unqualified `## Architecture decision` sentence would expect
  `Model.objects` to be skipped. Where no reader is misled (D6's plan fields, D7's key vocabulary
  beyond the module name), there is no pointer.
- **The `## Current state` removal was decided from the document's structure, not from the deferral.**
  The deferral asks about a heading's *name*. Reading the section against the rest of the file
  answered a bigger question — only one of its five facts was stated nowhere else — and the removal
  discharges the deferral as a side effect. Had the section carried unique contract, the answer would
  have been a retitle and the deferral would have been half-discharged at best.
- **Register kept: sibling specs are named as bare `docs/SPECS/…` code spans in the spec, and as
  reference-style links in the rationale.** Measured before choosing: spec-002's body carries six
  spec-filename code spans and, after R1, exactly one reference-style cross-file link (the rationale
  pointer, which R1 justified against `spec-001`'s precedent). Adding six reference links for six
  sibling specs would have inverted the file's own register to gain navigability the code spans
  already imply by path. The rationale's register is the opposite — it already had three sibling
  reference links — so R2's nine new defs match it.
- **`DjangoTypeDefinition.consumer_assigned_relation_fields` is named type-qualified, not
  path-qualified.** Consistent with the file's existing treatment of well-known package types
  (`OptimizationPlan.only_fields`, `TypeRegistry`), and rule 27's `path::QualifiedName` form is used
  for the six symbols a reader would otherwise have to hunt for.
- **No new glossary link was added, deliberately.** Several rewritten sentences name terms with real
  `docs/GLOSSARY.md` anchors (`FK-id elision`, `Plan cache`, `Meta.optimizer_hints`). Linking them
  would put spec links in the file for anchors the terms CSV does not carry, and the CSV is what
  `import_spec_terms` rebuilds card 2's glossary links from — a divergence in the direction the
  checker cannot see. Whether the CSV should grow rows is a DB-and-CSV decision outside this item's
  write set; raised for R3, declined here.

### Notes for Worker 3

- **The audit's sharpest question is over-absorption, not under-correction.** Read
  `### Drift-row dispositions` first, then read the spec end to end asking, per pointer clause,
  whether a reader is genuinely misled without it. Seven clauses name four sibling specs; if one of
  them is "useful context" rather than "the sentence is false without it", it is the scope trap
  landing, and that is a Medium.
- **Attack the `## Current state` removal hardest.** It is the one edit that deletes text rather than
  correcting it, and the argument for it is a duplication claim: of its five facts, only O2's module
  path was stated nowhere else. Re-derive that claim fact by fact against the current spec rather
  than accepting the table — and note that the table's middle row is a *near*-duplicate, not an exact
  one, so it is the row most worth attacking. If any fact the table calls duplicated is not in fact
  stated elsewhere, a contract was lost and that is a High.
- **Attack the `## Purpose` scope sentence second.** It is a universal newly added to a standing
  contract ("it does not restate that spec's rules"), which is the sentence shape most likely to be
  wrong. Ask whether the spec itself now violates it — the O5 and O6 pointer clauses are the closest
  calls.
- Re-run every verification command yourself rather than accepting the quoted output. **The anchor
  map changed** (1/1/1 -> 1/1/2) — confirm the change is the deliberate one described and not an
  accident, and confirm the terms CSV is byte-untouched.
- The diff to read is `git diff -- docs/SPECS/spec-002-optimizer-0_0_2.md` (which contains R1's move
  as well as R2's reconciliation — the R1 half is `final-accepted` and out of scope) plus the
  untracked rationale. **Do not `git stash`, `git checkout`, or `git restore` anything** — the tree
  carries a concurrent session's work.
- **Not a finding, pre-assessed twice:** `## References`'s issue #572 / PR #583 bullet (settled by the
  spec-001 cycle's R3 and re-affirmed by R1), and `CHANGELOG.md`'s `[0.0.2]` `__init_subclass__`
  sentence (correct as history — see `### Source-correctness audit`).
- A passage this pass left in the spec is **not** an R2 finding if the reason it looks wrong is that
  a *durable doc* disagrees with it — that is R3's axis. It **is** an R2 finding if the package
  disagrees with it.

### Notes for Worker 1 (spec reconciliation) — consolidated hand-off

This list carries R1's eight items forward with their status and adds R2's. Later passes **update
these keys** rather than appending a third set. Items marked **CLOSED** need no further action and are
retained so the next pass does not re-open them.

1. **`KANBAN.md:310` — DECIDED HERE, CORRECTED AT FINAL VERIFICATION, R3 EXECUTES.** The replacement
   text and the reasoning are in `### The KANBAN.md:310 decision, written for R3 to execute` below.
   R1 made the bullet stale in two particulars; R2 made it stale in a third and simultaneously
   **discharged the deferral it states**. Final verification rewrote one clause of the replacement
   text: the inherited *"Nothing anywhere cites spec-002 by `#anchor`"* was falsified by R2's own
   `#visibility-status` link definition in the companion rationale. **Apply the text as it stands
   below, which is the corrected version.** Owner: **R3**, as a `CardItem.text` edit on card
   `TODO-ALPHA-052-0.1.0` plus a regenerate, applied on top of the concurrent session's DB state
   without reverting it. R3 needs no further authorization — the build plan pre-authorizes a DB write
   when the audit finds real drift, and this is real drift the cycle itself caused.
2. **Drift rows D3 and D13 — CLOSED.** Both routed, differently, on the "whose contract is the
   answer" test rather than on "did it ship"; D3 became O1 contract, D13 stayed `spec-004`'s. Both
   have rationale change-record entries. Reasoning in `### Drift-row dispositions`.
3. **Anchor budget — UPDATED.** No longer 1/1/1. `only-projection` (`## Purpose` sentence 1) and
   `djangotype` (`## Problem statement` bullet 1) still have exactly one link each and remain
   untouchable without a re-site. `djangooptimizerextension` now has **two** (`### O3`,
   `## Visibility status`), so it has one spare. The add-destinations-before-removing-the-source
   ordering is what R3 should reuse if it ever touches these sentences.
4. **The retitle decision — CLOSED, and it was not a retitle.** `## Current state` removed;
   `## Shipped slices` and `## Implementation checklist` survive the standing-promise argument on
   their merits; `## Visibility status` is held by `spec-006`'s two by-title citations **and by the
   companion rationale's `#visibility-status` link definition** (added at final verification) and
   stays.
   `spec-003…`'s ":333" prose ("Update … current state, visibility status, and checklist") is a
   discharged when-O4-ships instruction that now names a section that does not exist — **stale in
   wording only, in a read-only sibling.** Deferred item for the maintainer / whoever next opens
   `spec-003`; recorded, not edited.
5. **`## References` — CLOSED.** D15's four locators verified present in the checkouts `AGENTS.md`
   line 2 names; the two URLs recorded as unfetched rather than claimed verified. No edit.
6. **The rule-2-versus-reader-rule precedent — EXTENDED.** R1's two cases (move-and-tense-mark vs
   delete) needed a third for a reconciliation: **restate when the corrected behavior is this spec's
   own contract.** All three are now in the plan's `### The two rulings…`, stated once.
7. **R1's two un-acted drift observations — CLOSED.** The missing blank line before `### O4` is
   fixed. The `## Coordination` / `## Current state` framing tension is resolved by the removal; see
   `### Beyond the drift table` item 5.
8. **The spec/rationale consistency checker (`KANBAN.md:309`) — STILL OPEN, needs an owner.** This
   pass hand-rolled the fifth implementation. Two traps to fold in, both measured live in this cycle
   family: normalize whitespace and strip `> ` before any multi-word grep (R1), and **a slugger must
   both keep underscores and NOT collapse whitespace runs** — the whitespace-run divergence measured
   in `### Link-convention and anchor audit` is the third distinct slugger trap and the only one that
   fails *silently*. Carried to the final gate's `### Deferred work catalog`.
9. **NEW — the `_optimizer_field_map` rename-sweep residue, SCOPE CORRECTED at final verification.**
   **Four** live-code sites on a deleted symbol, not three: the three test function names in
   `tests/optimizer/test_field_meta.py` **and** the token in `scripts/review_inspect.py`. Owner:
   **maintainer** / a future test-hygiene card; `tests/` and `scripts/` are outside every residual
   item's write set. The prose survivals in `CHANGELOG.md` / `KANBAN.md` / `spec-010` / `spec-016`
   are correct as history and are **not** in the sweep; `spec-004` and `spec-003` use the name in the
   present tense and are read-only siblings, same class as item 4. Detail in
   `### Source-correctness audit`.
10. **NEW — the `0.0.2`-versus-`0.0.3` disagreement between `docs/GLOSSARY.md` and `CHANGELOG.md`
    about which release carried O2-O6.** Owner: **R3's durable-doc audit**, escalating to the
    maintainer; `CHANGELOG.md` is closed to this cycle. The spec is deliberately version-free on this
    point, so nothing in R2's output depends on the answer.
11. **NEW — whether the terms CSV should gain rows.** Several sentences R2 wrote name glossary-backed
    terms (`FK-id elision`, `Plan cache`, `Meta.optimizer_hints`) that spec-002 does not link. R2
    declined to link them because the CSV is read-only here and is what `import_spec_terms` rebuilds
    card 2's links from. Owner: **R3**, as part of the terms-CSV importability verification it already
    owns — decide whether card 2's glossary-link set is *complete* at three, or report it as
    deliberate.

### The `KANBAN.md:310` decision, written for R3 to execute

**What the bullet says now** (card `TODO-ALPHA-052-0.1.0`, `CardItem.text`, rendered at
`KANBAN.md:310`):

> `docs/SPECS/spec-002-optimizer-0_0_2.md` carries four status-shaped sections: `## Current state`,
> `## Shipped slices`, `## Visibility status`, `## Open questions`. All four are accurate at HEAD
> today, so nothing is wrong now - the deferral is the standing-promise shape itself, which spec-001
> retired by retitling `## Current state` to `## Prior art` on the reasoning that a section named for
> the present is a promise no shipped spec can keep. Nothing anywhere cites spec-002 by `#anchor`, so
> retitling breaks no link, but `spec-003-optimizer_nested_prefetch_chains-0_0_2.md` names those
> sections in prose.

**Why it cannot be number-patched.** Three of its claims are now false and a fourth is spent: the
count (`four`), two of the four named sections (`## Open questions`, removed by R1; `## Current
state`, removed by R2), and the load-bearing *"All four are accurate at HEAD today, so nothing is
wrong now"* — which was the whole argument for deferring. The deferral has been discharged, not
rescheduled.

**The decision: the bullet is REPLACED, not edited.** What survives is the constraints the discharge
did not resolve — `## Visibility status` is still a heading named for the present, and it stays that
way because two live pointers name it. That is a real residual item for the beta line, and it is what
the card should carry.

**The replacement text below was corrected at final verification** (Worker 3 Medium 1). The build
pass carried the old bullet's *"Nothing anywhere cites spec-002 by `#anchor`, so the retitle itself
breaks no link"* over verbatim, and this cycle falsified it: `grep -rn
'spec-002-optimizer-0_0_2.md#' .` returns **seven** link definitions in
`docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md`, one of them `#visibility-status`, which R2
itself added. Sending a future beta-line author a promise that retiring that heading breaks no link
would have produced exactly the dangling reference the clause exists to rule out. The corrected text
states the two constraints that actually hold, and names the count nowhere — a number on the durable
board drifts the next time the companion gains an entry, where the grep is re-derivable forever.

**Replacement `CardItem.text`, for R3 to apply verbatim:**

> `docs/SPECS/spec-002-optimizer-0_0_2.md` carries one status-shaped section left:
> `## Visibility status`. The spec-002 residual cycle discharged the rest - `## Open questions` and
> `## Current state` are gone, and `## Shipped slices` and `## Implementation checklist` survive the
> argument on their merits, since a past-tense fact about what shipped is not a promise about the
> present. `## Visibility status` stays because two live pointers would break with it. First,
> `spec-006-public_surface-0_0_3.md` names it **twice** - once as the quoted section title
> "Visibility status", once as "the local visibility-status amendment" - as the place the
> optimizer-visibility decision is recorded. Second, the companion
> `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` is the only file that cites spec-002 by
> `#anchor` at all, and one of its link definitions targets `#visibility-status`, so a retitle must
> re-point that definition in the same change. Retire the heading in the cycle that owns
> `spec-006`, not this one, and re-point the companion there.
> `spec-003-optimizer_nested_prefetch_chains-0_0_2.md`'s "current state, visibility status, and
> checklist" instruction is now stale in wording: it is a discharged when-O4-ships note naming a
> section that no longer exists.

**Execution notes for R3.** `KANBAN.md` and `KANBAN.html` are DB-generated and currently dirty from a
concurrent session (`## Baseline-dirty out-of-scope files`), so: edit `CardItem.text` in the kanban
DB, regenerate, apply on top of the concurrent state **without reverting it**, verify by
two-consecutive-regenerate byte-stability plus a spot-check that only card 052's bullet changed, and
hand the mixed diff to the maintainer. Do not hand-edit `KANBAN.md`. The sibling bullet at
`KANBAN.md:309` (the consistency checker) is untouched and stays.

---

## Review (Worker 3)

Audit of a **spec reconciliation**, so most code-review axes are absent rather than padded: no source
and no test file is in the diff, no new boundary / guard / gate / rejection path exists, no ORM or
async behavior changed, no public surface moved. `scripts/review_inspect.py` was **not run** —
`BUILD.md` `### When to run the helper during build` triggers on `.py` files and this diff contains
none. **No `pytest` was run and none is owed** (`AGENTS.md` rule 15; nothing executable is in the
diff). No failability proof is owed. Hot-path and floor-verification scopes are both `none` in the
plan preamble.

`git status --short` read at pass open and pass close: **14 paths, identical at both ends** — the
nine baseline-dirty concurrent-session paths, Worker 0's untracked plan, and this cycle's four.
Nothing baseline-dirty was edited, reverted, or `git checkout`-ed; no `stash` / `checkout` /
`restore` / `worktree` at any point. The read-only HEAD copy went to a scratch path outside the repo.

**Isolating R2's own delta.** The working-tree diff carries R1 as well. R1's `## Move performed` and
its final-verification section fix R1's contribution at 7,398 -> **7,006** bytes across five sites
(`## Purpose` para 2 fold, `## Problem statement` lead-in + pointer, `## Architecture decision` para
3, `## O4 extraction` cut, `## Open questions` cut, the `[spec-002-rationale]` def) **plus** the
87-byte `## References` chronology clause removed at R1's own final verification. That last one
matters for attribution: the `## References` hunk in the working-tree diff is **R1's, not R2's**, and
is out of scope here. R2's delta is everything else: the `## Purpose` family sentence, the two
`## Architecture decision` paragraphs, all six O-slice restatements, the `## Coordination` locator,
`## Visibility status`, and the removal of `## Current state`.

**What was re-derived against source versus accepted on the record.** Re-derived independently, at
HEAD, from the named symbols: **D1** (`types/finalizer.py::finalize_django_types` Phase-2 call to
`_attach_relation_resolvers`; `types/base.py::DjangoType.__init_subclass__` stamping
`_is_default_get_queryset` and attaching no resolver; Phase 3 `strawberry.type(...)` as the freeze),
**D2** (`types/resolvers.py::_make_relation_resolver` many-side `bounded_rows` + the
`_prefetched_objects_cache` fast path), **D3** (`skip_field_names=definition.consumer_assigned_relation_fields`),
**D4** (exact signature), **D5** (`_optimizer_field_map` absent from the package;
`DjangoTypeDefinition.field_map` + `optimizer/walker.py::_resolve_field_map` present), **D6** (11
dataclass fields by `ast`, 3 further names are `ClassVar` constants), **D7** (five `DST_OPTIMIZER_*`
keys + `clear_optimizer_context`, cleared from `on_execute`), **D8**
(`optimizer/extension.py::DjangoOptimizerExtension._optimize`: `normalize_query_source` then
`_result_cache is not None`), **D9** (`optimizer/walker.py::_enable_only_for_operation` threaded as
`enable_only`; `optimizer/plans.py::OptimizationPlan.apply` unchanged), **D10**
(`apply_type_visibility_sync` called from the walker's child-queryset build), **D11**
(`::apply_to`, reached from `connection.py` through `apply_connection_optimization`), **D12**
(`nested_planner.py` / `nested_fetch.py` / `lateral_fetch.py` / `single_parent_fetch.py`), **D13**
(the `spec-004` quotation, verbatim), the root gate (`if info.path.prev is not None: return result`),
the resolver-side context read (`types/resolvers.py` imports `DST_OPTIMIZER_PLANNED` /
`DST_OPTIMIZER_FK_ID_ELISIONS` / `DST_OPTIMIZER_STRICTNESS`), the `__init__` export, the three-way
roster count in the HEAD spec, and every validation command. **Accepted on the record:** D15's two
upstream URLs (no network) and its `graphene_django` / `strawberry_django` checkout line numbers
(outside this repo), and Worker 1's account of what its own `temp-tests/r2-spec002/audit.py` did —
my audit re-implements the same checks independently, which is the stronger evidence.

### High:

None.

The dispatch's primary axis is **explanation leaking into the spec**. I classified every R2-added
passage as contract or explanation and found no explanation. There is no amendment block, no
retraction paragraph, no "as of round N", no "previously", no "originally", no "used to". A
deliberately wide chronology sweep
(`as of|originally|previously|used to|no longer|since shipped|during implementation|was extracted|predicted|amendment|retract|formerly|at the time`)
returns **exactly one** hit over the whole spec: line 8, *"every claim it once made and no longer
makes"* — R1's rationale pointer, `final-accepted`, and the sanctioned shape for exactly this.

Worker 1's justification for the +40.5% holds under test. Six of the seven rewritten sites state a
contract the spec previously stated **less specifically than the package implements it**, and three
of the six were flatly false (D1's attachment site, D4's arity, D5's non-existent symbol). Two
"because" clauses are the closest call — *"because the plan is applied to a clone and cloning an
evaluated queryset would silently re-run the consumer's SQL"* and *"because Strawberry's connection
slicing hides the pre-slice queryset from schema middleware"* — but each explains the **behavior**,
not the **edit**, and the spec already carried that shape at HEAD (*"marked uncacheable because they
may depend on request context"*). Not a finding.

**Every restated claim is true at HEAD.** All twelve source-verifiable drift rows re-derived clean
(list above). Two specifically named by the dispatch:

- **D9 — Worker 1's correction of Worker 0's row is CORRECT.** `optimizer/plans.py::OptimizationPlan.apply`
  reads `if self.only_fields: queryset = queryset.only(*self.only_fields)` unconditionally; the
  `QUERY`-only gate is `optimizer/walker.py::_enable_only_for_operation`
  (`operation is None or operation is OperationType.QUERY`), threaded through the whole walk as
  `enable_only`. Under a mutation / subscription `only_fields` is never populated. Leaving the
  `apply()` sentence byte-verbatim and putting the gate on the walker sentence is the right edit.
- **D1 — the `_is_default_get_queryset` sentinel sentence was already right and was not "corrected".**
  `types/base.py::DjangoType.__init_subclass__` #"cls._is_default_get_queryset = not
  has_custom_get_queryset" is intact; the only R2 edit to that sentence is an added locator, which is
  the correct response to moving the *other* thing `__init_subclass__` used to do.

**The `## Current state` removal loses no fact.** Re-derived mechanically against the HEAD copy
rather than from the artifact's table: each of O1-O6 appears at **exactly three** sites in the HEAD
spec (`## Current state` bullet, `### O` heading, `## Implementation checklist` box) — the three-way
duplication claim is a measurement, not an assertion. Of the section's five facts:

| Fact | Survives at |
|---|---|
| the O1-O6 roster | `## Shipped slices` headings + `## Implementation checklist` (unchanged) |
| O2's module path `django_strawberry_framework/optimizer/walker.py` | `### O2`, opening the paragraph — **the unique fact, re-sited** |
| `DjangoOptimizerExtension` exported from `django_strawberry_framework.__init__` | `## Visibility status`, merged at the higher precision |
| "root optimizer plans are stashed on context" | `### O3`, widened (correctly — the stash is also the resolvers' hand-off) |
| "the extension is covered by the optimizer test suite" | **dropped** |

The drop is sound: it is a claim about the repository's test tree, not a contract, it is what
`fail_under = 100` already enforces for every package line, and no reader can act on it. `## Current
state`'s "and same-query recursion" also survives, in `### O4`. Nothing else left with the section.
The spec-001 `## Prior art` precedent genuinely does not transfer — spec-001's section *contained* a
prior-art survey; this one contained a slice roster, so the retitle would have been false and would
have kept the duplication.

**The scope trap holds.** Six pointer clauses name a sibling spec inside slice / architecture prose
(spec lines 23, 25, 33, 42, 45, 48). I read each asking the dispatch's question — is a reader
*misled* without it, or is it "useful context"? All six pass: an unqualified O5 promises column
deferral on a mutation; an unqualified `## Architecture decision` promises `Model.objects` is skipped
and that `DjangoConnectionField` is unoptimized; an unqualified O1 promises an unbounded many-side
list; an unqualified O6 implies the planner calls the consumer's hook. None re-specifies the owner's
rules: no `spec-035` deferred-refetch hazard, no `spec-045` sealing contract, no `spec-033` strategy
seam, no `spec-047` ceiling semantics. **D6 and D13 were correctly ruled `none` / `rationale`** — the
eleven-field `OptimizationPlan` inventory and `Meta.optimizer_hints` stay out, which is where the
pull was strongest. Every pointed-at spec exists on disk at the path given (all 4 sibling paths, plus
19/19 rationale def targets, `os.path.exists`-checked with fragments stripped).

**The 3-anchor constraint holds.** Independently re-counted in **both** forms:
`grep -o '\]\[glossary-[a-z0-9_-]*\]'` gives `2 djangooptimizerextension / 1 djangotype / 1
only-projection`, and a regex for the inline `](../GLOSSARY.md#…)` form returns the empty set, so the
reference-style count is the whole population. The 1/1/1 -> 1/1/2 move is the deliberate one
described: `djangooptimizerextension` is now in `### O3`'s mechanism sentence and in
`## Visibility status`'s public-surface sentence, both surviving contract prose.
`docs/SPECS/appx/spec-002-optimizer-0_0_2-terms.csv` is byte-untouched (`git diff --stat` empty).

### Medium:

#### 1. The `KANBAN.md:310` replacement text hands R3 a claim this cycle falsified

`### The KANBAN.md:310 decision, written for R3 to execute` carries, verbatim from the bullet it
replaces:

```docs/builder/bld-002-r2-spec_reconciliation.md:710
> Nothing anywhere cites spec-002 by `#anchor`, so the retitle itself breaks no link.
```

That is false as of this cycle, and this pass is half the reason. `grep -rn
'spec-002-optimizer-0_0_2.md#' .` now returns **seven** hits, all in
`docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md`'s link-definition block — and one of them is
`[spec-002-visibility]: ../spec-002-optimizer-0_0_2.md#visibility-status`, **added by R2 itself**.
The artifact knows this: `### Link-convention and anchor audit` says outright *"R2 added nine defs:
… plus one further spec-002 anchor (`#visibility-status`)"*. The two statements contradict each other
inside one artifact.

Why it matters rather than being a nit: the replacement text's whole payload is an instruction to a
future beta-line author — *"Retire the heading in the cycle that owns `spec-006`, not this one.
Nothing anywhere cites spec-002 by `#anchor`, so the retitle itself breaks no link."* An author who
acts on that retires `## Visibility status` and dangles `[spec-002-visibility]` in the companion
rationale, which is exactly the failure the sentence exists to rule out. R3 is told to apply the text
**verbatim** to `CardItem.text`, so the falsehood lands on the durable board.

Recommended change: in the replacement text, replace that clause with the true one — the two
constraints on retiring the heading are now `spec-006`'s two by-title citations **and**
`docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md`'s `#visibility-status` link definition, which
that cycle re-points in the same change. (I re-verified the `spec-006` half: `:136` cites
`"Visibility status"` in quotes and `:147` cites the "visibility-status amendment"; both go stale on
a retitle, so the "twice" is right.) Test expectation: none — no behavior.

Everything else in the replacement text is accurate and I re-verified it: the count (`four` -> one
remaining present-tense heading), `## Open questions` gone (R1), `## Current state` gone (R2), the
"All four are accurate at HEAD today" premise spent, and `spec-003…:333`'s "current state, visibility
status, and checklist" now naming a section that does not exist (confirmed at that line). The
`- ` hyphen register and the `**bold**` markup both match existing `CardItem.text` bodies rendered
into `KANBAN.md`, so the drop-in is renderable.

### Low:

#### 1. "Seven fields beyond the five" is six, in the rationale and in the artifact

`ast`-parsed, `optimizer/plans.py::OptimizationPlan` carries **11** dataclass fields
(`select_related`, `prefetch_related`, `only_fields`, `fk_id_elisions`, `planned_resolver_keys`,
`select_path_resolver_keys`, `prefetch_path_resolver_keys`, `finalized_fk_id_elisions`,
`finalized_planned_resolver_keys`, `finalized_lookup_paths`, `cacheable`); the three further
annotated names are `ClassVar` constants. Eleven minus the family's five is **six**, not seven. The
figure appears twice:

- `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md`, *Alternative rejected — restate the
  `OptimizationPlan`'s current field inventory*: "The plan now carries **seven** fields beyond the
  five this family describes". This is the one that matters — it is a standing doc.
- `### Beyond the drift table` item 3 and the D6 re-verification row: "eleven fields, seven beyond the
  five" and "it names six additions, there are seven". D6's row actually names **five** additions
  (`planned_resolver_keys`, `select_path_resolver_keys`, and three `finalized_*`) and there are
  **six**; the "omits `prefetch_path_resolver_keys`" observation is correct, the arithmetic around it
  is off by one on both sides.

Nothing downstream rests on it — the disposition (`none`, do not enumerate) is right either way.
Recommended change: `seven` -> `six` in the rationale, and correct the two artifact figures.

#### 2. "Seven pointer clauses" is six

`### Byte counts` ("roughly 950 bytes are the seven pointer clauses") and `### Implementation notes`
("Seven pointers, and each one earns its place"). Measured: **six** clauses name a sibling spec
inside slice / architecture prose — spec lines 23, 25, 33, 42, 45, 48 — plus the `## Purpose` scope
paragraph, which is a rule rather than a pointer clause and is argued as such two paragraphs earlier.
Recommended change: `seven` -> `six`, or say explicitly that the `## Purpose` paragraph is counted.

#### 3. The `_optimizer_field_map` escalation enumerates three sites; there are four

`### Source-correctness audit` and hand-off item 9 both say the residue is *"three hits, all test
function names, in `tests/optimizer/test_field_meta.py`"*. A tree-wide sweep finds a fourth:

```scripts/review_inspect.py:42
    "_optimizer_field_map",
```

— a member of the inspector's optimizer-token tuple, i.e. the same rule-27 rename-sweep miss, in
`scripts/` rather than `tests/`. It is dead weight (the token can never match) rather than a wrong
name, but a maintainer scoping the fix from this escalation would fix `tests/` and leave it. Both
paths are outside every residual item's write set, so the escalation is right to escalate; only its
scope is short. Recommended change: add the fourth site to hand-off item 9.

Confirmed real and correctly declined, per the dispatch: the three test names exist at
`tests/optimizer/test_field_meta.py:322`, `:339`, `:362` (`tests/` is read-only this cycle), and the
`docs/GLOSSARY.md` `0.0.2` versus `CHANGELOG.md` `0.0.3` disagreement over which release carried
O2-O6 is real, with `CHANGELOG.md` closed by `AGENTS.md` rule 21 and `docs/GLOSSARY.md` DB-rendered.
Routing both to R3 / the maintainer is the correct lever, and the observation that the spec is
deliberately version-free on that point (so the reconciliation neither inherits nor propagates the
disagreement) is correct — `## Visibility status` states no version number.

#### 4. "Every one is inside a labelled quotation" is false for four shared runs

See `### DRY findings`. The headline number (12 words, one occurrence) is exactly right; the gloss
around it is not.

### DRY findings

**The build plan's preamble rule holds on the headline number, re-derived independently.** Both files
whitespace-normalized, `> ` markers stripped, link-definition blocks removed,
`difflib.SequenceMatcher` over word lists: the longest shared prose run between the spec and its
rationale is **12 words, one occurrence** — *"the framework gets from Strawberry field resolution to
the underlying Django model"* — and it is R1's seam-sentence quotation, unchanged. **31 of the spec's
1,056 six-word shingles (2.9%)** appear in the rationale. Both figures match the artifact to the
digit.

**The one claim that does not survive re-measurement** is the qualifier: *"every one is inside a
labelled quotation of a spec sentence the entry is explaining."* Four of the next-longest shared runs
are the rationale's **own unquoted prose**, restating a spec sentence rather than quoting it:

| Run | Spec | Rationale |
|---|---|---|
| "because Strawberry's connection slicing hides the pre-slice queryset from schema" (10w) | `:25` | `:352` |
| "in its Phase 2 window, before Strawberry freezes the class." (10w) | `:31` | `:373` |
| "hands the planner a framework-owned queryset to compose" (8w) | `:48` | `:427` |
| "substitutes a stub carrying only the target's" (7w) | `:33` | `:380` |

These are the exact shape the plan's rule names: one fact, two homes, and the reader cannot tell
which is current. **The counter-argument, recorded so a later pass does not "fix" it wrongly:** all
four sit inside `*Changed — …*` change-record entries, which are a dated record of one edit rather
than a live restatement — a change record that stops matching the spec is doing its job, not going
stale. That is why this is a Low-tier DRY observation routed to Worker 1 rather than a hold. What is
**not** defensible either way is the artifact asserting the property mechanically when it does not
hold; the measurement, not the prose, is what a later pass will trust.

Existence challenge: not raised. Whether a rationale companion should exist is settled by `BUILD.md`
`## Spec rationale extraction`.

No other duplication. The rationale does not restate `spec-003`, and R2's own record of catching and
rewriting a 14-word restatement of the `## Purpose` scope rule mid-pass is corroborated by the
current measurement (that run is absent).

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` -> **empty**. `__all__` and the re-export list
are unchanged. This pass touches no `.py` file at all: the complete diff is one modified `.md`, one
untracked `.md`, and this artifact.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md. Confirmed: `git diff --stat -- CHANGELOG.md` is
empty.

### Documentation / release sanity

This is the pass's main axis. Every `ARTIFACT.md` bullet walked against the two changed documents
read end to end:

- **Version strings, statuses, card IDs.** The spec carries no status/header block (re-confirmed:
  line 1 title, line 2 blank, line 3 `## Purpose`) and, deliberately, no version number anywhere —
  `## Visibility status` says "O1 through O6 have shipped" with no release. R2 introduced no version
  string, shipped/planned status, or card ID. The rationale's `DONE-002-0.0.2` and "twelve patch
  versions ago" are R1's and remain correct against `pyproject.toml`'s `0.0.14`.
- **KANBAN movement.** None. No card moved, no DB write. Both DB-touching commands are read-only
  (`check_spec_glossary.py` without `--auto-link`; `import_spec_terms --check`) and I re-ran both to
  the same output. The `KANBAN.md:310` `CardItem.text` change is **written for R3, not executed here**
  — correctly, since the kanban DB is outside R2's write set. Its adequacy is Medium 1.
- **Links point at existing files.** Re-derived independently, not read from the artifact. Spec: one
  `<!-- LINK DEFINITIONS -->` delimiter, all **10** canonical group headers in `START.md`'s exact
  order verified **positionally**, alphabetical within every group, **4 defs / 4 uses, 0 undefined, 0
  orphaned**, 0 inline non-anchor links in the body. Rationale: same scaffold, **19 defs / 19 uses, 0
  undefined, 0 orphaned**, 0 inline links. **All 23 def targets `os.path.exists`-checked** on the
  normalized join with the fragment stripped and URLs excluded: **23/23 present**, including all
  eight sibling specs R2 added. Depth is right for a file two levels below `docs/` —
  `../../GLOSSARY.md#…` and `../../builder/BUILD.md` for `docs/` and `docs/builder/`,
  `../spec-NNN-….md` for `docs/SPECS/` siblings, a bare filename for the `appx/` sibling.
- **In-page anchors.** All seven `spec-002-optimizer-0_0_2.md#…` def fragments resolve against
  surviving spec headings, computed with a **private** slugger written for this audit (spaces
  replaced one at a time, underscores kept) rather than
  `scripts/check_spec_glossary.py::github_anchor`, whose whitespace-run collapsing is the false-pass
  the artifact measured. My slugger reproduces the divergence it names (`### O1 — Custom relation
  resolvers` -> `o1--custom-relation-resolvers`, two hyphens), which confirms R2's decision to key the
  new entries to `#shipped-slices` instead of per-slice anchors was the right call and not an
  evasion. `#visibility-status` resolves; nothing points at the removed `#current-state`.
- **Verbatim-text confirmation.** The `## References` block, `## Problem statement`, `##
  Coordination`'s first and third paragraphs, and `## Implementation checklist` are byte-identical to
  the R1 baseline; `OptimizationPlan.apply()`'s O5 sentence is byte-identical to HEAD, as the D9
  correction requires. The `spec-004` B4 quotation in the rationale is verbatim against
  `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md:128`.
- **Archival.** No move performed and none owed; spec and `-terms.csv` were already at their archived
  paths and the CSV is byte-untouched. The rationale stays at `docs/SPECS/appx/`.
- **No obsolete "coming soon" / "planned" / old-version wording** in either changed file. No
  script-rendered doc was regenerated, so the docstring-staging bullet does not apply.
- **Validation commands, all re-run by me, all matching the artifact:**

```
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-002-optimizer-0_0_2.md
OK: 3 terms - all have glossary entries and at least one spec link.
exit=0

$ uv run python examples/fakeshop/manage.py import_spec_terms --check
OK: 49 done cards have glossary links.
exit=0

$ uv run python scripts/check_trailing_commas.py --check \
    docs/SPECS/spec-002-optimizer-0_0_2.md \
    docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md \
    docs/builder/bld-002-r2-spec_reconciliation.md
exit=0

$ grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+' <spec> <rationale>
exit=1        # no match in either standing doc

$ git diff --stat -- docs/SPECS/appx/spec-002-optimizer-0_0_2-terms.csv
(empty)
```

- **Byte counts re-derived.** Spec `wc -c` = **9,844**, `wc -l` = **103**; rationale **33,555** /
  **486**. The `+2,838 (+40.5%)` reconciles through HEAD: HEAD copy 7,398, R1's post-final-verification
  total 7,006 (the -305 in R1's build report plus the 87-byte `## References` clause R1's own final
  verification removed), 9,844 - 7,006 = 2,838, and 2,838 / 7,006 = 40.5%. Both of R2's routes agree
  and both are right; a reviewer reading only R1's `### Byte counts` table would wrongly think the
  baseline is 7,093, which is why the reconciliation through the final-verification section is worth
  having on the record.

### What looks solid

- **The disposition table is the load-bearing artifact and it is right.** Fifteen rows, each with a
  named lever (`restate` / `point` / `rationale` / `none`) and a one-line reason, and every
  source-checkable row re-derived clean. The `restate` versus `point` test the pass wrote for itself
  — "is the sentence *false* without this qualifier?" rather than "is more detail available?" — is the
  correct discriminator, and applying it produced `none` on D6 and `rationale` on D13, which is where
  a weaker test would have absorbed a sibling spec.
- **The D9 correction of Worker 0's row.** Worker 0 put the `QUERY`-only gate in
  `OptimizationPlan.apply()`; it is in the walker. Worker 1 caught it, said so, and the resulting edit
  left `apply()`'s sentence byte-verbatim rather than "fixing" a true sentence. That is the failure
  mode this review exists to catch, caught by the pass itself.
- **Destinations added before the source was removed.** Linking `djangooptimizerextension` into
  `### O3` and `## Visibility status`, measuring, and only then deleting `## Current state` makes an
  anchor drop structurally impossible rather than merely caught by the final check. Worth reusing.
- **The `## Purpose` scope sentence is contract, and it does not backfire.** I attacked it as the
  dispatch asked — a newly-added universal ("it does not restate that spec's rules") on a standing
  document — and the spec does not violate it. The closest calls are O5 and O6; both state the
  *behavior that holds for their own slice* and name the owner, which is precisely the licence the
  sentence grants. It is also the only artifact of this pass that constrains a future author.
- **`## Visibility status` held rather than retitled, on evidence.** Both `spec-006` citation sites
  re-verified. Declining a tidy-looking retitle because a read-only sibling names the heading is the
  right call, and the reasoning went to the rationale rather than the spec.
- **Rationale hygiene.** All six entries name a spec section by heading **and** resolving anchor; the
  three keyed to headings that no longer exist say so and name the surviving section their argument
  bears on. Each carries at least one `*Alternative rejected — …*` with why it lost, and a
  `**Claims the spec no longer makes.**` line. The `## How to read this file` bullet explaining why
  sub-headings are keyed to the parent anchor documents the slugger trap in the place a future author
  will hit it. No entry names no decision.
- **Register discipline.** Sibling specs stay bare `docs/SPECS/…` code spans in the spec (matching the
  file's six pre-existing ones) and reference-style links in the rationale (matching its three), and
  the choice was measured before being made rather than defaulted.

### Temp test verification

- `docs/builder/temp-tests/r2-spec002-w3/audit.py` — my own independent re-implementation: link
  scaffold (defs / uses / undefined / orphans, positional group-header order, alphabetical order
  within group, `os.path.exists` per target with fragment stripped and URLs excluded), inline
  cross-file-link sweep with fenced blocks stripped, and in-page anchor resolution against a
  **private** GitHub-shaped slugger. Written from scratch rather than reading
  `docs/builder/temp-tests/r2-spec002/audit.py`, which was neither read, reused, nor deleted; the
  `r1-spec002` / `r1-spec002-fv` siblings likewise.
- The shingle / `difflib` overlap scan, the `ast` field count of `OptimizationPlan`, the roster
  occurrence count against the HEAD copy, and the byte reconciliation were inline one-offs.
- **Disposition: none promoted.** There is no package behavior to pin and no production code in the
  diff. This is the **sixth** hand-rolled implementation of the same scanner in this cycle family —
  see hand-off item 8; my slugger is the third independent one written this week.

### Notes for Worker 1 (spec reconciliation)

Four items, all routed to R2's final verification. None blocks acceptance.

1. **Medium 1 — fix the `KANBAN.md:310` replacement text before R3 executes it.** The clause
   *"Nothing anywhere cites spec-002 by `#anchor`, so the retitle itself breaks no link"* is false;
   R2's own `#visibility-status` def in the rationale is one of seven such citations, and it is the
   one covering the very heading the bullet tells a future author to retire. Two resolution paths:
   (a) replace the clause with the true constraint set (`spec-006`'s two by-title citations **plus**
   the rationale's `#visibility-status` def, re-pointed in the same change), which is what I
   recommend; or (b) drop the clause entirely and let `spec-006` carry the constraint alone —
   cheaper, but it loses the fact that a retitle now has a second, in-family cost. Either way R3 must
   not apply the current text verbatim.
2. **Lows 1-3 — three off-by-one measurements.** "seven fields beyond the five" (six),
   "seven pointer clauses" (six), and the `_optimizer_field_map` residue's "three hits" (four). Only
   the first is in a standing doc (the rationale) and is the one that must be corrected; the other two
   are artifact prose. The pattern is the one this cycle family keeps hitting: **the wrong number is
   always the one in the argumentative position**, never the one the pass derived to make a decision.
   Every disposition, every delta, and every total in this artifact is exact.
3. **Escalated (not held) — the four unlabelled spec/rationale shared runs** under `### DRY
   findings`. Two resolution paths: (a) accept them as change-record prose, and correct the artifact's
   "every one is inside a labelled quotation" to say so explicitly (my recommendation — the runs are
   7-10 words and the entries are dated records); or (b) reword the four rationale sentences to
   describe the spec's claim rather than restate it, as the pass already did once for the
   `## Purpose` scope rule. The target is inside R2's own write set either way, so this is a choice,
   not a constraint.
4. **Carried, not raised as findings.** (a) The `## Purpose` family sentence's *"Where one of them
   changed how one of the slices below behaves"* contains the only "before"-implying verb R2 added;
   it is about sibling specs changing package behavior, not about this document's revisions, so it is
   not the chronology the rule forbids — recorded so a later pass does not "fix" it into something
   weaker. (b) `spec-003…:333`'s stale "current state" wording is correctly left alone as a read-only
   sibling. (c) Hand-off item 11 (whether the terms CSV should gain rows for `FK-id elision` /
   `Plan cache` / `Meta.optimizer_hints`) is correctly R3's — R2's reason for declining to link them
   is right: a spec link to an anchor the CSV does not carry is a divergence `check_spec_glossary.py`
   cannot see.

### Review outcome

`review-accepted`. Zero High. One Medium and four Low findings, every one recorded above with a
recommended change and routed to Worker 1's final verification; the Medium's target (`CardItem.text`
in the kanban DB) sits outside R2's write set and its correction is a two-clause edit to this
artifact's hand-off, which is Worker 1's to make. The deliverable itself — the spec and its rationale
— carries no defect I could find: no explanation leaked into the spec, every restated claim is true
at HEAD against source, no glossary anchor was dropped, the `## Current state` removal lost no fact,
and the scope trap held on all four rows where it bites.

---

## Final verification (Worker 1)

Spawned with no memory of the pass that wrote the plan or performed the reconciliation. Everything
below is re-derived from the artifact, the two changed documents read end to end, the working-tree
diff, and the read-only HEAD copy — never from the artifact's own record of a measurement.

**Spec status-line re-verification (every Worker 1 spawn).** Re-read at this spawn, not inherited:
`spec-002-optimizer-0_0_2.md` line 1 is `# Spec: Optimizer & Reverse-Relation Resolution`, line 2 is
blank, line 3 is `## Purpose`. There is no status / target-release / owner / predecessor block, so
there is nothing for this obligation to falsify. The body's stale-by-tense claims were R2's whole
axis and are audited below.

**Tests: none run, and none owed.** This item's diff contains one modified `.md`, one untracked
`.md`, and this artifact. No package source, no test, no `.py` file of any kind. `AGENTS.md` rule 15
forbids a run after edits; `worker-1.md` `## Final verification job` step 5 asks for the focused
tests *the plan calls for*, and the plan calls for none because none exists to call for. No `--cov*`
flag was passed to anything, `--no-cov` included: nothing was invoked. No `ruff` run either — no
`.py` file was touched by this pass.

### Checklist audit

Every one of the eleven `- [x]` boxes in `### Dispatched findings checklist` audited against the
diff and the two documents. **All eleven landed; none un-ticked; none left `- [ ]`.** Two had their
headline tightened rather than their tick removed — the enumeration under each was true and the
summarizing clause was not, which is a wording fix, not an unlanded contract.

| Box | Verdict | Evidence re-derived at this pass |
|---|---|---|
| 1 — fifteen rows re-verified and disposed | landed | `grep -c '^\| D[0-9]'` = **30** across the two tables: fifteen disposition rows, fifteen re-verification rows, D1-D15 with no gap and no repeat |
| 2 — every false claim restated or handed over | landed | spot-checked at the rows nearest my own edits: D4's signature is byte-exact against `optimizer/walker.py::plan_optimizations`; D5's `_optimizer_field_map` is absent from `django_strawberry_framework/` and the spec now names `DjangoTypeDefinition.field_map` / `::_resolve_field_map`; D6's `none` disposition re-derived by `ast` (below); D9's gate re-read in `::_enable_only_for_operation`, and the spec's `apply()` sentence is byte-identical to the HEAD copy |
| 3 — no explanation landed | landed, headline tightened | `originally` / `as of ` / `used to ` -> exit 1, zero hits. The wide sweep -> exactly one hit, line 8's `no longer` in R1's `final-accepted` rationale pointer. Box reworded to name which regex gives which |
| 4 — a rationale entry per change, by heading **and** anchor | landed | six entries; all seven `spec-002-optimizer-0_0_2.md#…` def fragments resolve against a surviving spec heading under a private GitHub-shaped slugger (spaces one at a time, underscores kept); the three entries keyed to removed headings say so in their own lead |
| 5 — scope trap answered per row | landed | D6 `none`, D10 / D12 `point`, D11 `restate + point`, each with its reason; and the licence is in the spec at `## Purpose`, not only in the artifact |
| 6 — 3-anchor constraint | landed | `check_spec_glossary.py` exit 0; map re-counted **1 / 1 / 2**; `git diff --stat` on the terms CSV empty |
| 7 — `import_spec_terms --check` | landed | re-run, `OK: 49 done cards have glossary links.`, exit 0 |
| 8 — `check_trailing_commas --check` + no raw `path:NN` | landed | re-run on all three files after my edits, exit 0; rule-27 grep exit 1 on both standing docs |
| 9 — byte count by two agreeing measurements | landed | HEAD copy **7,398** (`git show HEAD:… ` into a scratch path outside the repo), R1's recorded delta -392 -> 7,006, working tree **9,844**: 9,844 - 7,006 = **2,838**, and 7,398 + (-392) + 2,838 = 9,844. Both routes close |
| 10 — nothing outside the write set edited | landed | `git status --short` = **14 paths**, unchanged from both prior passes' readings; terms CSV byte-untouched; no `.py`, no `examples/`, no `CHANGELOG.md`, no sibling spec in the diff |
| 11 — the `KANBAN.md:310` decision executable, every hand-over owned | landed, payload corrected | the decision block is present and now states only true things (Medium 1, below); all eleven hand-off items name an owner — R3 (1, 10, 11), the maintainer (4, 9), the final gate's deferred-work catalog (8), CLOSED (2, 3, 5, 6, 7) |

No box was left `- [ ]`, so `### Spec changes made (Worker 1 only)` carries no deferral reason for an
unticked box.

### Disposition of Worker 3's findings

Every finding addressed or rejected with a recorded reason. Three of the five were miscounts; in two
of those the **premise** was wrong as well as the arithmetic, so both were fixed by re-forming the
claim rather than by re-numbering it.

**Medium 1 — the `KANBAN.md:310` replacement text carried a claim this cycle falsified. FIXED.**
Re-measured before rewriting: `grep -rn 'spec-002-optimizer-0_0_2.md#' .` returns **seven** link
definitions, every one in `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md`'s definition block,
and `[spec-002-visibility]: ../spec-002-optimizer-0_0_2.md#visibility-status` is R2's own. The
`spec-006` half verified independently and *not* taken from the review: `:136` names the section as a
quoted title (`"Visibility status"`), `:147` as *the local visibility-status amendment* — two sites,
both stale after a retitle, so "twice" is right and the two spellings are worth naming because they
are not the same shape. The replacement clause now states both constraints and **carries no count**:
a "seven" written onto the durable board goes stale the next time the companion gains an entry, where
the grep is re-derivable forever. Every remaining claim in the replacement text re-verified at this
pass: one status-shaped heading left (the surviving headings are `Purpose`, `Problem statement`,
`Architecture decision`, `Shipped slices`, six `### O` slices, `Coordination…`, `Visibility status`,
`References`, `Implementation checklist`); `## Open questions` and `## Current state` both absent;
`spec-003…:333` confirmed to name a section that no longer exists.

**Low 1 — "seven fields beyond the five" is six. FIXED IN THE RATIONALE, and the premise was wrong
too.** `ast`-parsed at this pass: `optimizer/plans.py::OptimizationPlan` carries **11** dataclass
fields; the three further annotated names (`_FULL_MERGE_FIELDS`, `_METADATA_MERGE_FIELDS`,
`_DERIVED_FINALIZED_FIELDS`) are `ClassVar`. Eleven minus the five the D6 row names is six, so the
review's arithmetic is right. But the sentence's *second* half was false in a way neither pass
flagged: it said those fields' "meanings are specified across `spec-003` and `spec-035`", and five of
the eleven (`select_path_resolver_keys`, `prefetch_path_resolver_keys`, and all three `finalized_*`)
appear in **no file under `docs/SPECS/` at all**. Renumbering seven to six would have left a false
premise behind a true count. The entry is re-formed instead: it now states the eleven fields with
their symbol path, that the spec names exactly one plan attribute (`OptimizationPlan.only_fields`,
re-derived — `grep -o 'OptimizationPlan\.[a-z_()]*'` returns only `only_fields` and `apply()`), and
makes the scope argument over "the other ten" without asserting where they are specified. The two
artifact figures are corrected in place with the build-time value named.

**Low 2 — "seven pointer clauses" is six. FIXED (artifact prose, both sites).** Re-derived by
enumerating every sibling-spec code span in the spec body: ten occurrences at lines 6, 6, 6, 6, 23,
25, 33, 42, 45, 48. Line 6 is the `## Purpose` scope paragraph naming four specs at once — a rule,
not a pointer clause, and argued as a rule two bullets before the miscount. That leaves **six**
clauses, at exactly the lines the review named. Both artifact sites now carry the six line numbers so
the number is re-derivable rather than trusted.

**Low 3 — the `_optimizer_field_map` escalation names three sites; there are four. FIXED, and
scoped.** Confirmed at this pass: three test function names in `tests/optimizer/test_field_meta.py`
plus `scripts/review_inspect.py` #"_optimizer_field_map", a member of the inspector's optimizer-token
tuple that can never match. Both are the same rule-27 rename-sweep miss and both are outside every
residual item's write set, so **the sites were not fixed** — only the escalation's scope was. The
tree-wide sweep also turned up the name in prose in `CHANGELOG.md`, `KANBAN.md`,
`spec-010-foundation-0_0_4.md` and `spec-016-fieldmeta_consolidation-0_0_6.md`, where it is a correct
record of the mechanism `spec-016` retired, and in the present tense in
`spec-004-optimizer_beyond-0_0_3.md` (B4 / B7) and
`spec-003-optimizer_nested_prefetch_chains-0_0_2.md`'s opening constraint list, which are read-only
siblings stale in wording only. Both classes are recorded in `### Source-correctness audit` **so a
maintainer scoping the fix does not widen it into a documentation sweep** — an escalation that is
short is a defect, and one that is long in the wrong direction is another.

**Low 4 — the DRY gloss. ACCEPTED AS CHANGE-RECORD PROSE; THE GLOSS IS CORRECTED, THE RUNS STAND.**
Re-measured independently (both files whitespace-normalized, `> ` stripped, link-definition blocks
removed, `difflib.SequenceMatcher` over word lists): longest shared run **12 words, one occurrence**,
and **31 of 1,058** six-word shingles at **2.9%**. The 12 and the 31 and the 2.9% reproduce the
artifact and the review exactly; my denominator is 1,058 against their 1,056, which is a
tokenizer difference between three hand-rolled scanners and not a finding — the standing rule is that
a shingle denominator is not comparable across implementations, which is one more argument for
hand-off item 8's tracked checker. The gloss does not survive, and **not in the shape the review reported either**: there are
**nine** shared runs at six words or longer, not four unlabelled ones. Two are labelled quotations
(the 12-word seam sentence, the 7-word `## Purpose` scope rule), one is the rationale entry heading
that the spec's own pointer sentence names, and **six** are unquoted `*Changed —*` prose — the four
the review listed plus *"implementation, two entry points; the connection path is"* and *"the hand-off
the generated relation resolvers"*. The six stand: a `*Changed —*` entry is a dated record of one
edit, and restating the sentence it explains is the record working, not a second live copy. The test
that decided it is R1's: does the fix only remove text a reviewer named, or does it add unreviewed
judgement? R1's one accepted trim deleted a restatement of a `BUILD.md` mechanism with a canonical
home elsewhere; none of these six has one, and rewording six sentences to close a 6-to-10-word
overlap is judgement this pass would be adding, not removing. The false thing was the measurement
claim, so the measurement claim is what changed.

### DRY check across R1 and R2

R1 (`final-accepted`) moved the deliberative layer out; R2 reconciled what remained. The duplication
axis between them is the spec-versus-rationale one measured above, and the classification is
unchanged from R1's: one 12-word labelled quotation of the seam sentence, at 2.9% shingle overlap.
Within the spec, the three-way `## Current state` / `## Shipped slices` / `## Implementation
checklist` roster duplication that R2 removed does not recur — `grep` for each of O1-O6 now finds
each slice at exactly two sites (its `###` heading and its checklist box), down from three. No new
duplication was introduced by R2 or by this pass: my edits removed one false premise from the
rationale and touched nothing else in a standing doc.

### Spec reconciliation of R2's own edits

R2 *is* the reconciliation, so the question is whether its output needs a further one. It does not.
Re-checked at this pass rather than accepted: no restated claim is false at HEAD (the rows nearest my
edits re-derived from source, listed in box 2 above), no explanation leaked into the spec (box 3),
and the spec is byte-unchanged by this pass. The one standing-doc correction I made is in the
rationale, which is a change record, not a contract — the spec states no field inventory either way,
so the corrected sentence changes no contract a reader could act on.

### Re-verification commands, run after my edits

```
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-002-optimizer-0_0_2.md
OK: 3 terms - all have glossary entries and at least one spec link.
exit=0

$ uv run python examples/fakeshop/manage.py import_spec_terms --check
OK: 49 done cards have glossary links.
exit=0

$ uv run python scripts/check_trailing_commas.py --check \
    docs/SPECS/spec-002-optimizer-0_0_2.md \
    docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md \
    docs/builder/bld-002-r2-spec_reconciliation.md
exit=0

$ grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+' docs/SPECS/spec-002-optimizer-0_0_2.md \
    docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md
exit=1        # no match in either standing doc

$ grep -o '\]\[glossary-[a-z0-9_-]*\]' docs/SPECS/spec-002-optimizer-0_0_2.md | sort | uniq -c
   2 ][glossary-djangooptimizerextension]
   1 ][glossary-djangotype]
   1 ][glossary-only-projection]

$ git diff --stat -- docs/SPECS/appx/spec-002-optimizer-0_0_2-terms.csv
(empty)
```

**Anchor map 1 / 1 / 2** — the deliberate change R2 reported, unchanged by this pass, and better than
the 1/1/1 the constraint requires.

**Link scaffold, both files, re-implemented rather than re-read** (`docs/builder/temp-tests/
r2-spec002-fv/audit.py`): one `<!-- LINK DEFINITIONS -->` each; all 10 canonical group headers in
`START.md`'s exact order, verified positionally; alphabetical within every group; spec **4 defs / 4
uses / 0 undefined / 0 orphaned**, rationale **19 / 19 / 0 / 0**; **23 / 23** def targets
`os.path.exists`-checked with the fragment stripped and URLs excluded, at the right depth for a file
two levels below `docs/`; no inline cross-file link outside a fence in either body; no raw `path:NN`
in either body. All seven `#…` fragments into the spec resolve against a surviving heading.

**Working tree: 14 paths at close**, identical to the list both prior passes recorded — the nine
baseline-dirty concurrent-session paths, Worker 0's untracked plan, and this cycle's four. Nothing
baseline-dirty was read into an edit, reverted, or `git checkout`-ed; no `stash` / `checkout` /
`restore` / `worktree` at any point in this pass. The HEAD copy went to a scratch path outside the
repo.

**Byte counts.**

| File | Before this pass | After | Delta |
|---|---|---|---|
| `docs/SPECS/spec-002-optimizer-0_0_2.md` | 9,844 / 103 lines | **9,844 / 103 lines** | **0 — not edited** |
| `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` | 33,555 / 486 lines | **33,620 / 487 lines** | **+65, +1 line** |

The spec is byte-identical to what Worker 3 accepted: no finding reached it. Measured at close, after
the last edit to each file.

### Final status

`final-accepted`.

### Summary

R2 reconciled `spec-002-optimizer-0_0_2.md` against the shipped package, fifteen drift rows at a
time. Nine of the fifteen were the spec being **less specific than the code** — a three-parameter
signature for a five-parameter function, an unqualified pass-through rule with two exceptions, a
projection with no operation gate — and three were flatly false: relation resolvers were said to
attach at `DjangoType.__init_subclass__` (they attach in the finalizer's Phase 2 window), the walker
was said to route through `_optimizer_field_map` (**no such symbol exists**), and `plan_optimizations`
was published at the wrong arity. Each is now stated as the contract that holds, with no chronology
and no amendment block; what each replaced is in the companion rationale's change record.

The two structural outputs are worth more than the fifteen corrections. `## Current state` was
**removed** rather than retitled: of its five facts only O2's module path was stated nowhere else, so
the section was a three-way duplicate of the slice roster wearing a standing-promise heading, and its
two unique facts were re-sited into the contract prose that already owned their subjects. And
`## Purpose` gained a **scope rule for the whole optimizer family** — state the behavior that holds,
name the owning spec in one clause, restate none of its rules — which is the only artifact of the
pass that constrains a future author, and the reason six pointer clauses could replace what would
otherwise have been four sibling specs absorbed into their parent.

The spec grew +2,838 bytes (+40.5%) against R1's -392, which is the correct sign for a
reconciliation: a corrected contract costs more words than a wrong one. Three glossary anchors held
throughout — 1/1/2, up from 1/1/1, because both `djangooptimizerextension` destinations were written
**before** its only source was deleted. Nothing outside the two documents was touched.

### Spec changes made (Worker 1 only)

**`docs/SPECS/spec-002-optimizer-0_0_2.md` — no change.** Byte-identical at 9,844 to the file Worker
3 accepted. No finding reached the spec, and the checklist audit left no box `- [ ]`, so no deferral
reason is owed here.

**`docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` — one change, `## Shipped slices` entry,
`*Alternative rejected — restate the `OptimizationPlan`'s current field inventory*` (+65 bytes).**
Worker 3's Low 1 measured the count wrong ("seven fields beyond the five" is six); re-measuring found
the same sentence's premise wrong as well (five of the eleven fields are specified in no spec at
all). Re-formed rather than re-numbered: it now names the eleven dataclass fields with their symbol
path, states that the spec names exactly one plan attribute, and argues the scope trap over "the
other ten" without claiming where they are specified. Reason: the rationale is the one standing,
committed document of the three files this cycle wrote, and a wrong number in it outlives the cycle.

**Deferrals recorded, none of them a checklist box.** All three targets are outside this item's write
set and each carries a named owner in `### Notes for Worker 1 (spec reconciliation) — consolidated
hand-off`: the `KANBAN.md:310` `CardItem.text` edit (**R3**), the `_optimizer_field_map` four-site
rename sweep and `spec-003`'s two stale wordings (**maintainer**), and the spec/rationale consistency
checker at `KANBAN.md:309` (**the final gate's deferred-work catalog**).
