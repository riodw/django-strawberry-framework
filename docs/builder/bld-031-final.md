# Build: Final test-run gate — `031` globalid_encoding / `0.0.9` residual reconciliation cycle

Spec reference: `docs/SPECS/spec-031-globalid_encoding-0_0_9.md` (whole file; the shipped record)
Rationale companion: `docs/SPECS/appx/spec-031-globalid_encoding-0_0_9-rationale.md`
Build plan: `docs/builder/build-031-globalid_encoding-0_0_9.md`
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

Not applicable in the usual sense: this pass writes no code, no test, and no shared shape. It runs the
`docs/builder/BUILD.md` `## Final test-run gate` command list, records each result, and authors the
`### Deferred work catalog`. The one DRY-shaped obligation it does carry — that the catalog is
**re-derived** from every artifact rather than copied from the integration pass's handoff table — is
discharged under `### Deferred work catalog` below, and it changed the population.

### Implementation steps

1. Run every command in `docs/builder/BUILD.md` `## Final test-run gate`, in the order given there.
2. Confirm the floor-verification declaration for every slice in the plan's scope.
3. Re-derive the deferred catalog from all seven prior artifacts; reconcile against the four handed items.
4. Run the closing verification checks (`check_spec_glossary.py`, `check_citations.py`, anchor/link-def
   resolution in both the spec and the companion).
5. Set `Status:`.

### Test additions / updates

None. Worker 1 never edits source or tests, and this cycle's scope fence confines this pass to the spec,
the companion, this artifact, and the Worker 1 memory file.

### Implementation discretion items

None.

### Dispatched findings checklist

This pass is the gate, not a review round; no findings were dispatched to it.

---

## Final verification (Worker 1)

### Spec status-line re-verification

`docs/SPECS/spec-031-globalid_encoding-0_0_9.md` lines 1-11 and the companion's lines 1-10 were re-read at
the start of this spawn. Both describe the build's current state accurately:

- The spec's title, `Shipped in 0.0.9` opener, `Status: **SHIPPED (0.0.9)**` line, `Owner:`, and
  `Predecessors:` are all true at HEAD `5ebcfe9c`, and the header paragraph naming the rationale companion
  is correct — the companion exists at the path it names.
- No status line was falsified by any slice: the spec's unticked `## Slice checklist` is explicitly
  licensed by the shipped-spec convention stated in the same opener, and no predecessor doc was deleted by
  this cycle.

**No spec edit is owed by this pass.** `### Spec changes made (Worker 1 only)` below records the empty set
rather than omitting the section.

### Working-tree baseline, re-read at the start of this pass

`git status --short` at HEAD `5ebcfe9c`:

```text
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

**Every dirty path is this cycle's.** This is a change from the pre-flight baseline and it is recorded
rather than assumed away: the build plan's `### Concurrent work — never edited, never reverted` listed four
concurrent-session paths (`django_strawberry_framework/consumers.py`,
`django_strawberry_framework/utils/sessions.py`, `examples/fakeshop/db.sqlite3`, and the untracked
`tests/test_consumers.py`), and HEAD has moved from the pre-flight `bc4ed00a` to `5ebcfe9c`. All four are
now clean, so the concurrent session committed its work between pre-flight and this gate. Attribution is by
**diff content**, not by path membership: the two dirty `.py` files carry exactly the three docstring
replacements the integration pass's Worker 2 cohort landed (F-1 in `types/definition.py`, F-2 and F-3 in
`types/relay.py`), and nothing else.

`examples/fakeshop/db.sqlite3` is **clean after the full sweep**. It was not written by this gate and was
never reset by it.

---

## Gate results

Every command below was run from the repository root in the shared `.venv`, in the order
`docs/builder/BUILD.md` `## Final test-run gate` gives.

| # | Command | Result |
|---|---|---|
| 1 | `uv run pytest --no-cov` | **PASS** — `6870 passed, 42 skipped in 150.71s (0:02:30)`, exit 0 |
| 2 | `uv run python examples/fakeshop/manage.py check` | **PASS** — `System check identified no issues (0 silenced).`, exit 0 |
| 3 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | **PASS** — `No changes detected`, exit 0 |
| 4 | `uv run ruff format --check .` | **PASS** — `434 files already formatted`, exit 0 |
| 5 | `uv run ruff check .` | **PASS** — `All checks passed!`, exit 0 |
| 6 | `git diff --check` | **PASS** — no output, exit 0 |

### 1 — the full sweep, and what it was the backstop for

`uv run pytest --no-cov` is the sweep this cycle still owed. Slice 4 ran the full **live tier** (672 passed
/ 1 skipped) but not the package `tests/` tree, and two failure classes named in `docs/builder/BUILD.md`
are **invisible below the full parallel run**:

- `### Example-project schema changes must sync every schema-module list` — a schema module missing from a
  private hardcoded list surfaces as an order-dependent `DuplicatedTypeName` / `LazyType KeyError` at the
  aggregate schema build, and passes in isolation, single-worker, and any one fixed file order.
- `### Test staleness a focused run cannot see` — an example-model field-set change or a wire-shape
  conversion strands test files the slice never names.

Neither class appeared. The run was the full parallel one (`xdist`, workers `gw0`-`gw6` observed in the
output) across all three test trees, and the known recurring fakeshop schema-registry cross-test-pollution
flake **did not fire**: zero `DuplicatedTypeName`, zero `LazyType KeyError`, zero collection errors, zero
failures. The 42 skips are the suite's standing skips (the `FAKESHOP_SHARDED` cohort and the soft-dep
absence cohort), not new ones.

No coverage-shaped flag other than `--no-cov` was used in this pass, and no line coverage was inspected or
asserted (`docs/builder/BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool`).

### 6 — `git diff --check` against a legitimately shared tree

`git diff --check` covers the **whole** tree, so a whitespace error or conflict marker in a concurrent
session's file would surface here and would not be this cycle's to fix (`AGENTS.md` rule 34 forbids editing
or reverting it). **Nothing surfaced, from any owner.** `git diff --cached --check` was also run and is
likewise clean, so the result does not depend on the index being empty.

There is therefore no baseline exception to invoke, and nothing routes back through a slice loop.

---

## Floor verification

**No floor-verification scope declared.**

The declaration was *established*, not defaulted into, and the reason is mechanical:

- The build plan's `## Build-wide context flags` declares floor-verification scope `none` by default and
  names the condition that would reopen it — any slice dispatching Worker 2 against `types/base.py`,
  `types/relay.py`, `types/finalizer.py`, or `filters/base.py` re-declares the scope at its planning pass.
  All six prior passes **confirmed** the declaration against their own diff rather than inheriting it:
  `bld-031-slice-0` `### Floor verification`, `bld-031-slice-1` `### Floor-verification scope`, and the
  `### Plan declarations` sections of slices 2, 3, 4, and 5, plus the integration pass's Worker 2
  `### Floor verification`.
- The cycle's **only** source diff is comment-only, and three independent inverse proofs on three different
  axes established that executable bytes are byte-equivalent to HEAD: Worker 2's `ast.unparse` of a
  docstring-deleted tree, Worker 3's `ast.dump` with sentinel substitution, and the integration pass's
  final-verification walk of the raw code-object graph under CPython `optimize=2`.
- **Re-run here as the gate's own reading rather than inherited.** A fourth run of the code-object axis,
  written for this pass, against `git show HEAD:<path>` copies in a scratch path outside the repo:

  ```text
  django_strawberry_framework/types/definition.py: IDENTICAL  (worktree nodes=19, HEAD nodes=19)
  django_strawberry_framework/types/relay.py:      IDENTICAL  (worktree nodes=61, HEAD nodes=61)
  control (executable-token mutation):             DIFFERS (instrument can fail)
  ```

  The control renames one executable token in `types/relay.py` and asserts the mutation actually changed
  the source before comparing, so a control that failed to mutate would report itself invalid rather than
  reading as a pass.

No Django / Strawberry / channels seam behavior moved, so there is nothing version-sensitive to re-run at
the floor.

The floor itself, for the record, is the one `docs/builder/BUILD.md` `## Floor verification` states: Django
**5.2.16** on Python **3.10** with strawberry-graphql **0.316.0**. No floor venv was built, because no
scope was declared. The shared `.venv` is **not** the floor and was neither mutated nor installed into; its
own versions are quoted only as a reading taken in this pass (`uv pip list`, and
`uv run python -c "import sys; print(sys.version)"`), never from memory or from a number written down in a
document: **Django 6.1, strawberry-graphql 0.323.2, channels 4.3.2, Python 3.14.2**.

---

## Verification checks before closing

| Check | Command | Result |
|---|---|---|
| Spec glossary | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-031-globalid_encoding-0_0_9.md` | **PASS**, exit 0 — `OK: 31 terms - all have glossary entries and at least one spec link.` |
| Citations | `uv run python scripts/check_citations.py` | **PASS**, exit 0 — `OK: 812 citations resolve (731 in 431 .py files, 81 in KANBAN.md).` |
| Anchors / link defs, spec | in-page anchor + reference-def resolver over `spec-031` | **PASS** — 45 headings, 87 link defs, 87 distinct ref uses, 147 inline `#anchor` **occurrences** across **20 distinct targets**; zero unresolved anchors, zero dangling ref ids, zero unused defs, zero unresolved def targets (file and `#fragment` both checked, including the cross-file fragments into `docs/GLOSSARY.md`) |
| Anchors / link defs, companion | same resolver over the rationale companion | **PASS** — 57 headings, 60 link defs, 60 distinct ref uses, 60 inline `#anchor` occurrences across 15 distinct targets; zero unresolved on every axis, including the six `spec-031-d*` fragments pointing back into the spec |

Occurrences and distinct targets are named separately on purpose: 147 and 20 are both correct figures about
the same file, and a later pass reading one as the other reads a regression that is not there.

**Staged-anchor sweep**, re-measured rather than inherited:

```shell
grep -rEn 'TODO\(spec-031|TODO-(ALPHA|BETA|STABLE)-031' . \
  | grep -v '^\./\.git/' | grep -v 'KANBAN.md\|KANBAN.html\|BACKLOG.md'
```

**Clean: zero surviving staged anchors in shipped source, tests, or comments.** Nine hits, every one prose
*describing* an anchor: the spec's Slice-4 checklist (`:76`) and plan row (`:420`), the companion's Slice-4
post-ship bullet (`:416`), four prior artifacts' own sweep records (`bld-031-slice-0:233`,
`bld-031-slice-4:80`, `bld-031-slice-5:141` and `:339`), the integration pass's own record
(`bld-031-integration:266`), and `docs/SPECS/appx/spec-022-export_schema-0_0_7-rationale.md:350`, a
card-renumber history row naming a *different* card that once held the number 031.

The count reads 6 → 8 → 9 across Slice 5, the integration pass, and this gate. The deltas are structural,
not drift: each pass's sweep cannot see the record that pass is about to write, and the two spec/companion
line numbers moved (`:419` → `:420`, `:413` → `:416`) because the integration pass appended to both files
after its own sweep ran.

---

## The cycle's headline result

**No. The `031` build skipped, dropped, and forgot nothing the spec planned.** Every one of the five spec
slices closed with an **empty CODE GAP list**, across **111 contracted surfaces** audited at HEAD:

| Slice | Contracted surfaces audited | CODE GAP list |
|---|---|---|
| 1 — `Meta.globalid_strategy` key + `RELAY_GLOBALID_STRATEGY` + the precedence resolver | **33** (21 source surfaces + 12 `## Test plan` rows) | **empty** |
| 2 — the encode seam (four encoders, Phase-2.5 install, default flip, strategy-aware `GlobalID` filter validation) | **14** (`CG-1`…`CG-14`) | **empty** |
| 3 — the decode seam (`decode_global_id` dispatch, encoder/decoder symmetry, transitional `type+model`) | **32** (21 source surfaces + 11 test rows) | **empty** |
| 4 — live HTTP coverage on a Relay-Node-shaped fakeshop type | **16** (`G1`…`G16`) | **empty** |
| 5 — doc updates + card-completion wrap (audit-only; the doc surfaces are out of fence) | **16** across four contracted-surface tables | **empty** |

Every contracted symbol, field, method, message, and named test existed at HEAD in the shape the spec
states. The audits did not merely match names: each row was read for shape and behavior against the spec
sentence it is filed under, and Worker 0's pre-verified hand-offs were re-derived rather than accepted —
twice they did not survive re-derivation, and accepting either would have written a falsehood into the
spec.

**The cycle's only source change was three comment-only docstring corrections**
(`types/definition.py::DjangoTypeDefinition`'s invariants docstring, `types/relay.py::encode_typename`, and
`types/relay.py::decode_global_id`), and they were found by the **cross-slice integration pass**, not by
any slice. That is the shape worth carrying forward: five per-slice audits each reading their own region
found nothing wrong in source, and reading the whole thing as one document found three false claims in it.
All three are comment-only, proved so on four independent axes, and none is a CODE GAP — the shipped
behavior was always correct; the comments describing it had gone stale under later cards.

### Spec byte trajectory

| Point | `spec-031-globalid_encoding-0_0_9.md` | `appx/…-rationale.md` |
|---|---|---|
| Pre-flight (HEAD `bc4ed00a`, before the rationale move) | **190,961 bytes** / 801 lines | did not exist |
| After Slice 0's rationale move | **148,526 bytes** / 670 lines | **82,045 bytes** |
| Final (this gate) | **178,300 bytes** / 706 lines | **122,898 bytes** / 502 lines |

The move itself removed 42,435 net bytes from the spec (48,167 out through the four routes, 5,732 of
framing put back). The spec then grew 29,774 bytes back over Slices 1-5 and the integration pass — that
growth is **reconciliation**, not the move unwinding: fifty-odd spec edits contracting shipped behavior the
spec had never stated. The companion grew 40,853 bytes over the same span, all of it `**Post-ship:**`
bullets recording why each contract changed. Spec plus companion is 301,198 bytes against the 190,961 the
cycle started with, and the deliberative layer is now 41% of it and out of the contract's way.

---

### Deferred work catalog

The next spec author's reading list. Re-derived from all seven prior artifacts' spec-reconciliation notes,
`What looks solid`, `### Notes for Worker 1`, `### Handed forward`, and `### Deferred to …` sections rather
than copied from the integration pass's handoff. **Every bullet has a named owner.**

The re-derivation moved the population by one: the integration pass handed forward **four** items, and the
walk of the artifacts finds **five**. Item 5 below is the addition — `bld-031-slice-2` routed it explicitly
"for `### Deferred work catalog` visibility only", and the integration pass reclassified it as closed with
"no owner needed", which is exactly the shape that does not survive.

1. **`spec-032`'s eight dangling citations into text that left `spec-031`.**
   Source: `bld-031-slice-0` `### Notes for Worker 1` note 4; population grown from 3 to 8 by
   `bld-031-integration` `## Known-open item 3`. Licensing spec line: none — this is link rot the Slice-0
   move created in an out-of-fence file, not a deferral the spec authorizes.
   **Owner: maintainer, or a future `032` cycle.**
   Count and line numbers **re-derived by this pass** against the current
   `docs/SPECS/spec-032-full_relay-0_0_9.md`: 37 `spec-031` occurrences over 16 citing lines plus the link
   def at `:753`; **8 of the 16 cite text that is now in the companion**, in four claim families:
   - `:13` ("recorded in full in `spec-031` Revision 7") and `:513` ("its Revision 6 swept the stale
     shipped-slice anchors") — `spec-031` now carries **zero** `Revision N` entries; both live under the
     companion's `## Revision history` (companion `:26`).
   - `:281` ("Decision 1 set the precedent of … recording the card's older name") — Decision 1's rejected
     alternatives moved; the naming alternatives are the companion's Decision 1
     `### Alternatives considered (and rejected)`.
   - `:312` ("the same reasoning that rejected the global `resolve_typename` patch in Decision 3") — that
     alternative is companion `:121` ("Monkeypatch `strawberry.relay.GlobalID` / `Node.resolve_typename`
     globally").
   - `:9`, `:143`, `:464` (Decision 11 "explicitly deferred / reserved the top-level `relay.py` module")
     and `:452` (Decision 11 "withheld the public export because 'no shipped `0.0.9` consumer'") — the
     spec's Decision 11 states the no-public-export contract but names no top-level `relay.py` and does not
     carry that quote; both are companion `:333` and `:334`. The spec's one surviving `no shipped` hit
     (`:109`) is a *different* claim, about Strawberry's native `resolve_type`, and is not what `:452`
     cites.
   The other eight citing lines (`:30`, `:97`, `:127`, `:304`, `:385`, `:479`, `:493`, `:634`) point at
   Decisions 6 / 12, the Slice-4 precedent, and the `spec-031`-build precedent — all still in the spec, all
   resolving.

2. **The `"Relay"` / `"Type generation"` Browse-by-category slash in the Slice-5 GLOSSARY checklist bullet
   and `## Doc updates`.**
   Source: `bld-031-slice-5` `## Deferred to …` (finding G4). Licensing spec line: none needed — the spec
   text admits two readings and `docs/GLOSSARY.md` satisfies the better one (each symbol filed under the
   row it belongs in). **Not a defect**, and `docs/GLOSSARY.md` is out of fence for the whole cycle.
   **Owner: maintainer.** Worth one sentence only if a future spec's template disambiguates the slash.

3. **`docs/builder/bld-003-final.md` surviving from the `spec-003` cycle.**
   Source: the build plan's pre-flight step 3, recorded there as a **deviation**. It is tracked and
   committed, deleting it is out of the maintainer's fence (`.md`, neither a spec nor a `.py`) and
   destructive to committed history, and it cannot collide with this cycle's `031`-named artifacts.
   **Owner: maintainer.** A pre-flight deviation, not a defect.

4. **`tests/types/test_relay_interfaces.py:2151`'s "goes live for exactly this shape" docstring.**
   Source: `bld-031-integration` Worker 3 Low #2, adjudicated at the Worker 1 re-run. Verdict recorded:
   **no change owed.** It is an installation claim inside
   `::test_type_strategy_child_shadows_inherited_framework_closure`, whose whole subject is closure
   installation — narrower than, and different from, the unscoped population claim F-2 retired from source,
   and defensible under the same `id`-resolution scoping Decision 10 uses.
   **Owner: maintainer, or whichever future pass owns that test file.** Listed so a future grep for the
   retired phrasing finds the verdict instead of re-opening the question; act only if that file is being
   rewritten for another reason.

5. **`types/finalizer.py::_first_model_label_emitter` and `::_audit_model_label_routing`'s
   "registered type has no `DjangoTypeDefinition`" raises are shipped with no spec sentence.**
   Source: `bld-031-slice-2` `### CODE GAP audit` finding 5 and its `### Deferred to …` section, which
   routed it here explicitly. Licensing spec line: none — this is a **deliberate non-contract**, decided
   during the cycle: the two raises assert an internal invariant the finalizer's own construction excludes,
   and giving them spec sentences would invite a reader to treat an impossible registry state as a
   supported one. They are pinned by `tests/types/test_finalizer.py`.
   **Owner: maintainer.** No change owed; listed because a future audit that greps shipped raises against
   spec sentences will find these two and needs the verdict rather than a fifth re-derivation of it.

**Closed during the cycle, listed so the gate can show they were not dropped** (these are not catalog
items):

- The stale `.py` docstring/comment batch — raised across Slices 1, 2, and 3 as four clauses, re-derived by
  the integration pass to **three** (`::_install_typename_closure` was a mis-attribution and is correct as
  written), dispatched to Worker 2, reviewed by Worker 3, and audited at the Worker 1 re-run. Shipped in
  this cycle's diff; no longer deferred.
- `TODAY.md:14`'s "own-PK GlobalID filtering, `node(id:)` refetch shape" phrasing — flagged by Slice 4 for
  Slice 5's audit, closed there: accurate on its own terms (both halves of the capability shipped), no doc
  obligation implied.
- Slice 0's notes 1-3 — the `install_globalid_typename_resolver` arity contradiction (discharged by Slice 2
  as S1), DoD item 1's false terms-CSV claim (Slice 5, four homes), and Decision 1's pre-archival
  `docs/spec-031-…` path (Slice 5, five sites / seven occurrences). Each re-verified by the integration
  pass; `grep -n 'docs/spec-031' <spec>` returns zero.
- Slice 1's two hand-offs to Slice 2 — the `types/definition.py` node-id-only docstring (became F-1) and
  `_warn_model_label_secondary_collapse`'s unowned status (contracted by Slice 2 as S7, now named in five
  consistent homes).
- Worker 3's Low #1 on F-1's parenthetical — raised and intentionally rejected with the reason recorded
  (the appositive describes the cited function's standing role and matches the shipped sibling docstring
  verbatim). No future work named.

### DRY check across this pass and prior accepted slices

No duplication introduced — this pass writes no code, no test, and no helper. No consolidation candidate
survives from any prior slice: the integration pass's reader-check found live single-sitings rather than
dead pairs, and its Worker 3 recorded `DRY findings: None` against a diff that adds no helper, constant,
branch, or literal.

### Failability, fail-open, and relocation claims

- **Failability proofs:** not applicable at this gate; zero new boundaries were introduced by this pass,
  and the integration pass's Worker 2 cohort introduced none either (comment-only).
- **Fail-open shapes:** none introduced. The gate's own inverse proof establishes that no executable byte
  changed, which is the strongest available form of that check for this cycle.
- **Relocation / promotion claims:** the one claim of that shape in the cycle — "the diff is comment-only,
  executable bytes unchanged" — was **re-proved by this pass** rather than read off Worker 3's acceptance,
  under `## Floor verification` above.

### Spec slice checklist audit

Not applicable to this artifact: the gate has no spec `## Slice checklist` of its own. Every slice's
verbatim checklist was audited at that slice's own final verification, and all six prior artifacts carry
`Status: final-accepted`. The build plan's `## Checklist` shows Slices 0-5 and the integration pass all
`- [x]`; the final box is Worker 0's to mark.

### Spec changes made (Worker 1 only)

**None.** This pass edited neither `docs/SPECS/spec-031-globalid_encoding-0_0_9.md` nor
`docs/SPECS/appx/spec-031-globalid_encoding-0_0_9-rationale.md`. The status-line re-verification found
nothing falsified, the gate found nothing that routes back through a slice loop, and no deferral reason is
owed for an un-ticked box because there is none.

### Final status

`final-accepted`.

### Summary

Every gate command passes. The full parallel sweep — the one thing this cycle still owed, because Slice 4
ran only the live tier — is green at **6870 passed / 42 skipped**, with neither of the two failure classes
`docs/builder/BUILD.md` says are invisible below it, and no sign of the recurring fakeshop schema-registry
cross-test-pollution flake. Django's `check` and `makemigrations --check --dry-run`, `ruff format --check`,
`ruff check`, and `git diff --check` are all clean, the last of those across the whole tree and therefore
across any concurrent work; the four concurrent paths that were dirty at pre-flight have since been
committed and the tree now carries only this cycle's changes.

The floor declaration is `none` and it was established rather than defaulted into: six prior passes each
confirmed it against their own diff, and four independent inverse proofs on four axes — `ast.unparse`,
`ast.dump` with sentinel substitution, and the code-object graph under CPython `optimize=2` twice, the
second run written for this gate with a self-invalidating control — show both changed files byte-equivalent
to HEAD in executable bytes. Nothing version-sensitive moved.

The question the maintainer commissioned this cycle to answer has a one-sentence answer: the `031` build
skipped, dropped, and forgot nothing, and 111 contracted surfaces across five slices closed with an empty
CODE GAP list every time. The only source change the whole cycle produced was three stale docstring
clauses, and the pass that found them was the cross-slice read, not any slice — five audits each reading
their own region found nothing wrong in source, and reading the document as one thing found three false
sentences in it.

The deferred catalog re-derives to five items where four were handed forward. The fifth — the two
`_audit_model_label_routing` no-definition raises — had been reclassified from "catalog item" to "closed,
no owner needed", which is precisely the reclassification that loses an item; it is listed with a verdict
and an owner so the next audit finds the answer instead of re-deriving it. `spec-032`'s dangling-citation
count re-derives to eight, matching the handed figure, and its current line numbers are recorded.

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
