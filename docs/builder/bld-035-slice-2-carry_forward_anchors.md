# Build: Slice 2 — Carry-forward anchor retarget

Spec reference: `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` (Decision 6 lines 196-223, incl. the `#### Carry-forward requirements for the follow-up card` R1-R3 block at 217-223; Decision 7 lines 225-235; the staged-anchor discipline paragraph at line 263; the G3 deferred test plan at lines 323-338)
Status: final-accepted

This is a **retrospective reconciliation slice** under `docs/builder/build-035-optimizer_hardening-0_0_10.md` `## Cycle framing`, not a feature slice. Its whole content is item 5 of that plan's `### Deviations later work introduced`: the G3 carry-forward staged anchors name an owner (`spec-035`, in two spellings) that will never ship the work, because spec-035 Decision 7's maintainer decision moved G3 out of the card entirely.

**Comment-text only.** No executable line changes in any file. The proof obligation is therefore the `BUILD.md` `## Claims are proven mechanically, never accepted on prose` "relocated / carried over unchanged" shape, discharged by an `ast.dump` identity comparison against pristine `HEAD` (`### Test additions / updates`), not by a failability proof.

## Plan (Worker 1)

### Boundary count and the split question

**Estimated new boundaries: 0.** The slice adds no guard, cap, rejection path, validation branch, or gate — it rewrites four `#` comment blocks. `BUILD.md` `### Slice splitting` asks the question against both triggers:

- **Diff shape:** four comment blocks in three files, ~40 changed lines, all contiguous and each independently readable. Well inside one review.
- **Boundary count:** zero, so the per-boundary mutate / run / count-rows / revert / byte-compare load that motivates the boundary trigger is zero.

**Answer: do not split.** The four sites are one decision — a single owner-retarget applied uniformly, whose whole value is that a reader greps one token and finds every seam at once. Splitting them would produce a tree where two sites name the follow-up card and two still name a retired slice, which is the exact half-retargeted state (`dd8dc0b3` retargeted one of five) this slice exists to close.

### No failability proof is owed

`BUILD.md` `### What needs a proof, and what does not`: a proof is required for every **new boundary, guard, gate, or rejection path** a slice introduces, and explicitly **not** for doc edits or changes that move existing text. This slice introduces none — it changes comment text and nothing else, which the AST identity proof below establishes mechanically rather than on assertion.

Worker 2 writes `None; this pass introduced no new boundary.` under `### Failability proofs` and keeps the heading. **Worker 3 must not grade the absence as a gap**, and Worker 1 must not withhold `final-accepted` for it.

### Hot-path budget

Not applicable; the build plan declares no hot path for any slice in this cycle, and this slice changes zero executable lines, so no code runs differently on any path. Worker 2 writes `Not applicable; plan declares no hot path.`

### Floor verification

Not applicable; the build plan declares floor-verification scope `none`. This slice touches no Django / Strawberry / channels integration seam — it touches no executable line at all. Worker 2 writes `Not applicable; plan declares floor-verification scope none.`

### Resolving the two rules that pull on the anchor wording

Both rules are live and they appear to conflict. They do not; the resolution is recorded here so Worker 2 does not have to re-derive it and Worker 3 does not re-litigate it.

**`AGENTS.md` rule 26** requires a staged-but-unbuilt seam to carry `# TODO(spec-NNN slice N): ...` **naming the doc and the owning slice**, removed in the change that ships the slice.

**The standing no-process-provenance rule** (implemented by commit `471d4c6b`, "drop build-process vocabulary from code comments") bans build-slice numbering from comments, but **exempts live `TODO(spec-NNN Slice N)` anchors precisely because rule 26 requires them**. That commit's own message says so: "TODO anchors naming genuinely unbuilt work are untouched, since those are required to name their owning document." Its edit to `walker.py` (verified: `git show 471d4c6b -- django_strawberry_framework/optimizer/walker.py`) stripped ` Slice 3` from both anchors anyway, against the exemption it was implementing.

**The resolution.** Rule 26's `slice N` component names the **owning unit of work**, not a literal slice ordinal. spec-035 Slice 3 is not a deferred-but-owned slice of this card; Decision 7's `**Decision (maintainer): defer G3 entirely from spec-035.**` moved the work to a different card. So:

- Restoring ` Slice 3` would be exemption-compliant and still wrong: it would name a unit of work that will never be built. An anchor that names an owner who will never ship it is the failure rule 26 exists to prevent, not the form it prescribes.
- The compliant form names **the owning card** in the `TODO(...)` head and **the doc holding the design** in the body: `TODO(BACKLOG polymorphic_interface_connections - the abstract-return optimizer entry card)` plus a body clause citing `spec-035 Decision 6` / `Decision 7` and the requirement label (`R1`, `R2`). That is doc-and-owner, which is what rule 26's doc-and-slice is for.
- A bare `spec-NNN Decision N` reference in a comment is on the no-process-provenance rule's explicit **KEEP** list (it is a contract pointer, not process provenance). `Slice`, `Worker`, `Revision`, and review-round vocabulary stay out of every replacement block.
- No raw `path:NN` reference appears in any replacement block (`AGENTS.md` rule 27). Raw `path:NN` in *this artifact* is licensed — it is a per-cycle `docs/builder/bld-*.md` scratchpad.

The head form is copied verbatim from `django_strawberry_framework/optimizer/selections.py #"TODO(BACKLOG polymorphic_interface_connections"`, which commit `dd8dc0b3` already converged. That is the point of the uniformity: one `grep -rn 'polymorphic_interface_connections'` returns `BACKLOG.md`'s card plus every seam, production and test, in one listing.

### Decision: the two package test-tree anchors are KEPT, retargeted — not deleted

`worker-1.md` `### DRY analysis shape` forbids leaving this to Worker 2. Decided here, with the reasoning, so it is not re-argued at review.

The delete case is real: the spec's G3 deferred test plan (lines 323-338) already enumerates every G3 pin **by name** — `test_sibling_type_fragment_excluded_from_plan`, `test_interface_implementor_fragment_planned`, `test_same_named_relation_on_two_members_regression`, `test_primary_fragment_skipped_under_secondary_accepted_under_primary`, `test_unknown_union_condition_recurses_without_direct_fields`, `test_anonymous_inline_fragment_still_inlines`, `test_connection_wrapped_sibling_fragment_narrowed`, `test_strictness_no_false_fire_for_narrowed_sibling_fragment`, plus the R2 and R3 pins — and Decision 8 hands that plan to the follow-up card. `tests/optimizer/test_walker.py #"Pseudocode: synthesize interface/union-like selection trees"` restates seven of those tests as prose; on content alone it is a second copy of a spec section, and `BUILD.md`'s existence challenge would delete it.

**It survives on one fact the spec does not hold: file placement.** The spec's Slice 1 and Slice 2 test-plan headings each name their files (`### Slice 1 — G1 (tests/optimizer/test_extension.py)`, `### Slice 2 — G2 (tests/optimizer/test_walker.py + tests/optimizer/test_extension.py, extend)`). The Slice 3 heading — `### Slice 3 — G3 — DEFERRED (carry-forward requirements for the abstract-return optimizer entry card)` — names **no file**, deliberately, because the work left the card. So each test anchor carries a placement judgement that exists nowhere else in the repo, and `test_extension.py`'s carries a second one the spec also lacks: *"here if it needs real extension execution rather than pure walker inspection"* — a conditional routing call between the two files.

Deleting the anchors would drop information the spec does not carry, and the maintainer's pseudocode-preservation constraint forbids the middle option of trimming only the duplicative lines. So: **all four in-scope anchors are kept and retargeted; every pseudocode line's technical content is preserved verbatim.** The one condition that would change this answer: if Slice 3 (or the follow-up card's own spec) writes the file-placement judgement into the spec's G3 deferred test plan, the two test anchors become pure duplicates and should then be deleted. Recorded for the deferred-work catalog rather than actioned here — Slice 3 may not edit `.py`, and this slice may not edit the spec.

### DRY analysis

- **Helper inventory checked.** Refreshed for the **whole package** this pass (`worker-1.md` `### Package-wide helper inventory before helper planning`), regenerated into `docs/shadow/helper-inventory.md` from `django_strawberry_framework/` recursively — 1,964 lines. Grepped for the shapes this slice could plausibly need: `classif` (22 hits — `classify_transport`, `classify_relation_join`, `unwindowable_child_queryset_reason`, `relation_kind`, `_index_coverage`, none a fragment/type-condition classifier), `fragment` (`selections.py::is_fragment`, `::included_field_selections`, `::named_children`, `::resolve_unvisited_fragment`, `extension.py::_collect_reachable_fragment_definitions`), `type_condition`, `anchor`, and `todo`. **No helper is warranted, and none could be**: the slice writes no executable line, so it has no call site to serve. The inventory is recorded because the step gates *deciding* no helper is needed, not only proposing one.
- **Existing patterns reused.** The anchor head form and the reachability-clause shape are reused verbatim from the one already-correct site, `django_strawberry_framework/optimizer/selections.py:381-392` (`# TODO(BACKLOG polymorphic_interface_connections - the abstract-return` / `# entry card): ...`), which commit `dd8dc0b3` established. That commit is the precedent for *what a retarget contains*: it swapped the owner token **and** added a reachability clause (`registry.model_for_type returns None for the abstract origin, so _optimize passes the queryset through before this inliner runs`) while leaving the pseudocode intact. The contract-pointer form `spec-035 Decision N` is reused from live sites such as `django_strawberry_framework/optimizer/walker.py:456-457` (`the operation-wide G2 projection gate (spec-035 Decision 4)`) and `walker.py:386` (`spec-045-visibility_boundary-0_0_14 Decision 5`).
- **New helpers justified.** None, and none is possible. The condition that would justify one: nothing — a comment carries no logic to extract.
- **Duplication risk avoided.** Two, both real here. (a) **Re-stating `selections.py`'s reachability mechanism at each of the other three sites.** A naive uniform retarget would paste the full `registry.model_for_type` / `_optimize` pass-through explanation four times; four copies of one mechanism drift the moment the entry path changes. The plan states the precondition in **one clause naming R1** at each site and leaves the mechanism at `selections.py`, its natural home (the inliner the classifier is threaded into). (b) **Re-stating the spec's named-test roster.** The two test anchors already restate spec test names; the retarget adds a pointer to the spec's G3 deferred test plan and adds **no** further test names, so the roster keeps exactly one authoritative home.

### Implementation steps

Line numbers are pin-at-write-time navigational hints against the current working tree. All four target files are **clean at `HEAD`** (`git status --short` reports nothing for them), so each edit starts from committed content. Verify before editing.

1. **`django_strawberry_framework/optimizer/walker.py:467-473`**, inside `walker.py::_walk_selections`, immediately above the `merged = _merge_aliased_selections(_included_field_selections(selections))` call. Replace the block

   ```python
       # TODO(spec-035): supply a registry-only type-condition classifier
       # to ``included_field_selections`` at this planning seam.
       # Pseudocode: accept the planning type's GraphQL name plus declared and
       # MRO-inherited interface names; skip known sibling concrete types; recurse
       # fragments-only for unknown composite/union names; never accept the model
       # primary type merely because the Django model matches. The classifier must
       # not call into graphql-core schema introspection.
   ```

   with

   ```python
       # TODO(BACKLOG polymorphic_interface_connections - the abstract-return
       # optimizer entry card): supply a registry-only type-condition classifier
       # to ``included_field_selections`` at this planning seam. Design contract:
       # spec-035 Decision 6 (the tri-state classifier and its accept set) and
       # Decision 7 (narrow, do not multi-plan). That card must first build the
       # abstract-return production-entry contract (R1); until it exists no
       # abstract root field reaches this walker, so the classifier has nothing
       # to narrow.
       # Pseudocode: accept the planning type's GraphQL name plus declared and
       # MRO-inherited interface names; skip known sibling concrete types; recurse
       # fragments-only for unknown composite/union names; never accept the model
       # primary type merely because the Django model matches. The classifier must
       # not call into graphql-core schema introspection.
   ```

   The five `Pseudocode:` lines are unchanged byte-for-byte.

2. **`django_strawberry_framework/optimizer/walker.py:1130-1134`**, inside `walker.py::_selected_scalar_names`, between the `type_cls, _definition, field_map = _resolve_field_map(model)` line and the `No ``_merge_aliased_selections`` here` paragraph. Replace the block

   ```python
       # TODO(spec-035): audit this FK-id-elision helper as the walker's
       # second ``included_field_selections`` consumer. Pseudocode: either share
       # the same type-condition classifier used by ``_walk_selections`` or prove
       # the helper only receives concretely typed relation child selections where
       # sibling fragments are GraphQL-invalid.
   ```

   with

   ```python
       # TODO(BACKLOG polymorphic_interface_connections - the abstract-return
       # optimizer entry card): audit this FK-id-elision helper as the walker's
       # second ``included_field_selections`` consumer. This is that card's
       # requirement R2 in spec-035 Decision 6, and it is unreachable until the
       # same card builds the abstract-return production-entry contract (R1).
       # Pseudocode: either share the same type-condition classifier used by
       # ``_walk_selections`` or prove the helper only receives concretely typed
       # relation child selections where sibling fragments are GraphQL-invalid.
   ```

   The pseudocode's technical content is preserved verbatim; it is only **rewrapped** so `Pseudocode:` opens its own line rather than continuing the prose sentence (`AGENTS.md` rule 17 line length governs the wrap). No word is added, removed, or reordered inside it.

3. **`tests/optimizer/test_walker.py:4962-4970`**, module level, between `test_fk_id_elision_recorded_under_mutation`'s close and the `Helper-move (spec-033 Decision 9) no-regression` comment. Replace only the first line

   ```python
   # TODO(spec-035 Slice 3): add G3 walker narrowing pins here.
   ```

   with

   ```python
   # TODO(BACKLOG polymorphic_interface_connections - the abstract-return
   # optimizer entry card): add G3 walker narrowing pins here. The named test
   # roster is spec-035's G3 deferred test plan; the classifier they pin is
   # spec-035 Decision 6, and they are unreachable until that card builds the
   # abstract-return production-entry contract (R1).
   ```

   The eight `# Pseudocode: synthesize interface/union-like selection trees ...` lines that follow are **untouched**, byte-for-byte.

4. **`tests/optimizer/test_extension.py:5359-5364`**, module level, between `test_plan_cache_shared_across_schemas`'s close and `test_b8_pruned_select_related_stays_strictness_visible`. Replace only the first two lines

   ```python
   # TODO(spec-035 Slice 3): add the strictness no-false-fire package pin here if
   # it needs real extension execution rather than pure walker inspection.
   ```

   with

   ```python
   # TODO(BACKLOG polymorphic_interface_connections - the abstract-return
   # optimizer entry card): add the strictness no-false-fire package pin here if
   # it needs real extension execution rather than pure walker inspection. The
   # test is named in spec-035's G3 deferred test plan; the narrowing it
   # exercises is spec-035 Decision 6, unreachable until that card builds the
   # abstract-return production-entry contract (R1).
   ```

   The four `# Pseudocode: execute an abstract/interface-shaped query ...` lines that follow are **untouched**, byte-for-byte.

5. **Do not touch `django_strawberry_framework/optimizer/selections.py`.** Its anchor is already the reference form and is the convergence target, not a target of this slice. It is deliberately absent from this cycle's ownership partition.

6. **Do not touch `examples/fakeshop/test_query/test_library_api.py`.** Its `TODO(spec-035)` anchor (`:3680`) is the fifth site and is **baseline-dirty** with a concurrent session's work (`git status --short` reports ` M`). `AGENTS.md` rule 34 and the build plan's `### Baseline-dirty out-of-scope files` both apply: never edit, never revert. It is routed to the deferred-work catalog (`### Notes for Worker 1 (spec reconciliation) — plan pass`).

7. **Format and lint, scoped to this pass's own files only** (`ARTIFACT.md` `### Validation run` — never `.`, because this tree carries concurrent sessions' uncommitted work):

   ```shell
   uv run ruff format django_strawberry_framework/optimizer/walker.py tests/optimizer/test_walker.py tests/optimizer/test_extension.py
   uv run ruff check --fix django_strawberry_framework/optimizer/walker.py tests/optimizer/test_walker.py tests/optimizer/test_extension.py
   git status --short
   ```

   Baseline measured this pass: `ruff check` on all four files reports `All checks passed!`, and `ruff format --check` on the three writable ones reports `3 files already formatted`. Any new finding is this slice's. Note `ERA001` is enabled repo-wide; the pseudocode blocks do **not** currently carry `# noqa: ERA001` and do not currently trip it. If a rewrap makes a pseudocode line trip ERA001, add the inline `# noqa: ERA001` — **never refactor the pseudocode to satisfy the lint** (`AGENTS.md` rule 18).

8. **Verify the ASCII-only and line-length rules** (`AGENTS.md` rule 17): every replacement block is ASCII and every line is under 90 characters, comfortably inside the 99 limit. The hyphen in `polymorphic_interface_connections - the abstract-return` is an ASCII hyphen-minus, matching `selections.py`; **no en/em dash may enter a `.py` file.** `uv run python scripts/check_trailing_commas.py --check <the three files>` is the mechanical gate.

### Test additions / updates

**No test is added, changed, or removed.** The slice changes no executable line, so there is nothing new to pin, and a test asserting comment text would pin the anchor's spelling rather than any contract.

What replaces a test here is the **executable-token identity proof** the `BUILD.md` "relocated / carried over unchanged" shape requires. Worker 2 must run it and quote the command **and its output** in the build report. All three writable files are clean at `HEAD`, so the reference is the read-only `git show HEAD:<path>` form `BUILD.md` `## Claims are proven mechanically, never accepted on prose` mandates; `git stash` / `git checkout` / `git restore` / `git worktree` are banned and unnecessary.

**(1) The proof — plain `ast.dump` equality against pristine `HEAD`.** Run from the repository root **after** the edits:

```shell
uv run python - <<'PY'
import ast, subprocess, sys

TARGETS = [
    "django_strawberry_framework/optimizer/walker.py",
    "tests/optimizer/test_walker.py",
    "tests/optimizer/test_extension.py",
]
ok = True
for path in TARGETS:
    head = subprocess.run(
        ["git", "show", f"HEAD:{path}"], capture_output=True, text=True, check=True
    ).stdout
    work = open(path).read()
    same = ast.dump(ast.parse(head)) == ast.dump(ast.parse(work))
    print(f"{'AST-IDENTICAL' if same else 'AST-DIFFERS  '}  {path}")
    ok = ok and same
print("ALL IDENTICAL" if ok else "MISMATCH")
sys.exit(0 if ok else 1)
PY
```

Plain `ast.dump` equality is used rather than the docstring-blanked variant because it is **strictly stronger**: comments are absent from the AST, so equality proves the diff is comment-only, and it additionally proves **no docstring changed** — which is a requirement of this slice, not an incidental. (The docstring-blanked comparison recorded for this repo remains the fallback for a pass that must legitimately change a docstring. This one must not.) Expected output: three `AST-IDENTICAL` rows, `ALL IDENTICAL`, exit 0.

**(2) The negative control — the instrument must be able to report a difference.** A proof instrument that cannot fail reads exactly like a passing proof. Run this **too**, and quote both outputs; it writes nothing to disk:

```shell
uv run python - <<'PY'
import ast, subprocess
path = "django_strawberry_framework/optimizer/walker.py"
head = subprocess.run(
    ["git", "show", f"HEAD:{path}"], capture_output=True, text=True, check=True
).stdout
work = open(path).read()
perturbed = work.replace("        return None\n", "        return ()\n", 1)
assert perturbed != work, "control substitution matched nothing - pick another token"
same = ast.dump(ast.parse(head)) == ast.dump(ast.parse(perturbed))
print("executable-token control:", "AST-IDENTICAL" if same else "AST-DIFFERS")
comment_only = work.replace("polymorphic_interface_connections", "PLACEHOLDER", 1)
same2 = ast.dump(ast.parse(head)) == ast.dump(ast.parse(comment_only))
print("comment-only control:", "AST-IDENTICAL" if same2 else "AST-DIFFERS")
PY
```

Both controls were run at plan time against the pre-edit tree and behaved correctly: `executable-token control: AST-DIFFERS`, `comment-only control: AST-IDENTICAL`. A run where the executable-token control prints `AST-IDENTICAL` means the instrument is broken and its main result proves nothing.

**(3) Focused existing tests, pass-count equality.** Secondary to (1) — comments cannot affect collection — but it is the second half of the method recorded for this repo, and it catches a botched edit that lands inside a string literal or breaks a file:

```shell
uv run pytest tests/optimizer/test_walker.py tests/optimizer/test_extension.py --no-cov -q
```

Pre-edit baseline measured at plan time: **351 passed in 8.93s**, scope green. Worker 2 records the post-edit count; it must be 351, and any deviation is this slice's until proven otherwise. No `--cov*` flag on any invocation (`BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool`); `--no-cov` is required because `addopts` auto-applies `--cov`.

**(4) Anchor sweep, before and after.** Establishes the population rather than sampling it (`BUILD.md` `## Claims are proven mechanically`: search the shortest distinctive token and count occurrences):

```shell
grep -rn 'TODO(spec-035' --include='*.py' . ; grep -rn 'TODO(BACKLOG' --include='*.py' .
```

Expected after the edits: `TODO(spec-035` survives at **exactly one** site, `examples/fakeshop/test_query/test_library_api.py` (baseline-dirty, out of scope); `TODO(BACKLOG` appears at **five** sites — `optimizer/selections.py`, `optimizer/walker.py` twice, `tests/optimizer/test_walker.py`, `tests/optimizer/test_extension.py`. Note `--include` needs quoting in `zsh`; an unquoted glob makes the command fail rather than silently under-report.

**Temp tests:** none, and none is appropriate. `docs/builder/temp-tests/` stays empty for this slice.

### Implementation discretion items

Assessed and delegated to Worker 2:

- **Comment line wrapping inside each replacement block.** The exact break points are Worker 2's, subject to the 99-character limit and to leaving every pseudocode line's technical content unchanged. Step 2's rewrap is the only one this plan prescribes, and only because the original ran `Pseudocode:` on into a prose sentence.
- **Order of the four edits.** Independent; any order.
- **Whether to run the ruff pair once at the end or after each file.** Either, as long as the write-mode invocations name only this slice's three files.

Explicitly **not** discretionary, and not to be re-opened by Worker 2: the keep-vs-delete call on the two test anchors (decided above), the `TODO(BACKLOG polymorphic_interface_connections - the abstract-return optimizer entry card)` head form, the ban on restoring ` Slice 3`, and the untouchability of `selections.py` and `test_library_api.py`.

### Dispatched findings checklist

`BUILD.md` `### Dispatched findings checklist` — this slice has no spec `## Slice checklist` sub-bullets of its own, because spec Slice 3 is `[deferred]` and ships nothing. One box per in-scope anchor site, quoting the anchor as it reads today and citing the symbol-qualified path. Boxes stay `- [ ]` at planning; Worker 2 ticks only a box whose fix landed in its diff; Worker 3 walks the list; Worker 1 audits every tick at final verification.

- [x] `django_strawberry_framework/optimizer/walker.py::_walk_selections #"TODO(spec-035): supply a registry-only type-condition classifier"` — anchor today reads `# TODO(spec-035): supply a registry-only type-condition classifier`; retarget the head to the follow-up card and add the `spec-035 Decision 6` / `Decision 7` design pointer plus the R1 precondition, pseudocode verbatim.
- [x] `django_strawberry_framework/optimizer/walker.py::_selected_scalar_names #"TODO(spec-035): audit this FK-id-elision helper"` — anchor today reads `# TODO(spec-035): audit this FK-id-elision helper as the walker's` `# second ``included_field_selections`` consumer.`; retarget the head and name this as requirement **R2** of `spec-035 Decision 6`, pseudocode content verbatim (rewrap permitted).
- [x] `tests/optimizer/test_walker.py #"TODO(spec-035 Slice 3): add G3 walker narrowing pins here."` — retarget the head to the follow-up card, drop ` Slice 3`, add the pointer to spec-035's G3 deferred test plan and Decision 6; the eight pseudocode lines below are untouched.
- [x] `tests/optimizer/test_extension.py #"TODO(spec-035 Slice 3): add the strictness no-false-fire package pin here"` — retarget the head to the follow-up card, drop ` Slice 3`, keep the `if it needs real extension execution rather than pure walker inspection` placement judgement intact, add the pointer to spec-035's G3 deferred test plan and Decision 6; the four pseudocode lines below are untouched.
- [x] **Executable-token identity proved.** `ast.dump` equality against pristine `HEAD` for all three touched files, **plus** the negative control, both quoted with their output in the build report (`### Test additions / updates`).

**Pass 2 (apply-changes) boxes** — one per raw-line-number spec citation in the population Worker 0 re-derived with `grep -rnoE "edge case[s]? (line )?[0-9]+" --include='*.py' .` (`build-035-…` `#### Partition correction`). Each replacement is bound to its bullet by **content**, not by counting lines, and every anchor was verified to resolve exactly once in the spec before it was written.

- [x] `django_strawberry_framework/optimizer/walker.py::_record_relation_access #"edge case line 315"` — replaced with `Decision 4 / Edge cases #"every projection writer checks the gate"`; `Decision 4` kept.
- [x] `tests/optimizer/test_walker.py::test_subscription_operation_gated #"edge case line 317"` — replaced with `spec-035 Decision 4 / Edge cases #"subscription operations are gated identically"`; `Decision 4` kept.
- [x] `tests/optimizer/test_walker.py::test_enable_only_defaults_enabled_without_info #"edge case line 320"` — replaced with `spec-035 Decision 4 / Edge cases #"defaults to enabled"`; `Decision 4` kept.
- [x] `tests/types/test_resolvers.py::test_fk_id_elision_falls_back_when_consumer_only_defers_fk`, whose pre-fix docstring read `spec-035 edge case 316` (quoted as history, not as a live anchor — it resolves zero times at `HEAD` by design) — replaced with `spec-035 Decision 5 / Edge cases #"can defer the FK column (both"`; the docstring's opening `Decision 5:` label kept, and the `Decision 5` component now also rides the citation itself.
- [x] **Identity re-proved for pass 2** under the docstring-blanked instrument (all four citations live inside docstrings), with three negative controls, quoted with output in `## Build report (Worker 2, pass 2)`.

**Pass 3 (apply-changes) box** — the Worker 3 pass-2 Medium finding: the **fifth** in-scope spec-035 raw line citation, wrap-invisible to the line-oriented instrument both prior passes used.

- [x] `tests/optimizer/test_walker.py::test_mutation_scalar_only_connection_window_no_only #"spec-035 Decision 4 / edge case" + "line 315"` (wrapped across two source lines) — replaced with `spec-035 Decision 4 / Edge cases #"every projection writer checks the gate"`; `Decision 4` kept; the `#"..."` anchor written whole on one source line. Population re-derived with a whitespace-flattening instrument and reported as an occurrence list in `## Build report (Worker 2, pass 3)`.

### Notes for Worker 1 (spec reconciliation) — plan pass

**Is the retarget the right call?** Yes, and no escalation is needed. Every claim in the build plan's item 5 was re-derived from source this pass rather than accepted on prose:

- `git show 471d4c6b -- django_strawberry_framework/optimizer/walker.py` shows exactly two hunks, both `- # TODO(spec-035 Slice 3): ...` / `+ # TODO(spec-035): ...`. Confirmed.
- `git show dd8dc0b3 -- django_strawberry_framework/optimizer/selections.py` shows the one retarget, and shows it added a reachability clause rather than swapping a token. Confirmed, and it is why the replacements above carry an R1 clause.
- Spec Decision 7 line 233 carries `**Decision (maintainer): defer G3 entirely from spec-035.**` and routes the work to the `polymorphic_interface_connections` card. So the owner the retarget names is the owner the spec names. Confirmed.
- Spec line 263 is the staged-anchor paragraph, and its claim of "three `TODO(spec-035 Slice 3)` comments" is stale on both count (five sites) and form (no site still reads `Slice 3` in the spelling it names, after this slice none reads `spec-035` at all except the out-of-scope one). **Slice 3 owns that sentence**; this slice must not edit the spec.

**Status-line re-verification (`worker-1.md` `## Spec status-line re-verification`), performed this spawn.** Re-read `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md:1-11`. Title, `Status:`, `Owner:`, `Predecessors:`, and the new rationale-companion pointer are accurate at `HEAD`. The two claims Slice 1 flagged are **confirmed still present and still recorded for Slice 3** — not fixed here, per this slice's scope:

- **The live-working-path claim, at four sites**, re-grepped this pass: `:137` (`The spec file lives at **`docs/spec-035-optimizer_hardening-0_0_10.md`** (this document).`), `:357` (the Slice 4 card-wrap bullet pinning the card's spec reference to the "**live** working path"), `:380` (Definition-of-done item 1, carrying the stale path twice — once as prose and once inside a `--spec` argument, so the verification command as written exits 2), and `:406` (DoD item 10). The file is at `docs/SPECS/`. Slice 3's.
- **The `0.0.9` on-disk-version parenthetical** at `:3` ("the on-disk version reads `0.0.9` as of this writing"). `django_strawberry_framework/__init__.py` reads `0.0.15`. Slice 3's judgement call: keep it dated or drop it.

**For the `### Deferred work catalog` in `docs/builder/bld-035-final.md`** (Worker 1 is its only author):

1. **The fifth carry-forward anchor is unretargeted.** `examples/fakeshop/test_query/test_library_api.py:3680` still reads `# TODO(spec-035): extend this live connection-fragment block with the ...`. The file is baseline-dirty with a concurrent session's work, so this cycle may neither edit nor revert it (`AGENTS.md` rule 34; build plan `### Baseline-dirty out-of-scope files`). It should receive the same `TODO(BACKLOG polymorphic_interface_connections - the abstract-return optimizer entry card)` head once that session's work lands. **This is also the one anchor that will make `BUILD.md` `## Cross-slice integration pass` step 6's sweep (`grep -rEn 'TODO\(spec-035'`) non-empty at integration** — flagged here so the integration pass reads it as a recorded deferral rather than a new finding.
2. **The two package test-tree anchors become deletable once the spec records their file placement.** They survive this slice only because the spec's G3 deferred test-plan heading names no file, unlike its Slice 1 and Slice 2 headings. If Slice 3 (or the follow-up card's own spec) writes that placement into the deferred test plan, both anchors reduce to duplicates of a spec section and should be deleted then. Not actionable in this cycle: Slice 3 may not edit `.py`, and this slice may not edit the spec.

**Static-inspection helper (`BUILD.md` `### When to run the helper during build`).** Required here because the slice's files sit under `django_strawberry_framework/optimizer/`. Run this pass with the mandatory `--output-dir docs/shadow`:

```shell
uv run python scripts/review_inspect.py django_strawberry_framework/optimizer/walker.py --output-dir docs/shadow
uv run python scripts/review_inspect.py django_strawberry_framework/optimizer/selections.py --output-dir docs/shadow
```

Both wrote their `.overview.md` / `.stripped.py` pair. `walker.py`: 24 imports, 37 symbols, 8 control-flow hotspots, 7 repeated string literals, **2 TODO comments** — `docs/shadow/django_strawberry_framework__optimizer__walker.overview.md:278-279` names both target lines. `selections.py`: **1 TODO comment**, `:146`, the already-correct reference anchor. The overviews confirm the anchor population in these two files is exactly what this plan targets and nothing else; no hotspot, ORM marker, or repeated literal is implicated, because the slice adds no executable line. Shadow line numbers are not canonical and are not cited in any source edit.

---

## Build report (Worker 2)

### Files touched

Grounded in `git status --short` after both ruff invocations (quoted under `### Validation run`).

- `django_strawberry_framework/optimizer/walker.py` - both `TODO(spec-035)` anchor heads retargeted to `TODO(BACKLOG polymorphic_interface_connections - the abstract-return optimizer entry card)`. Site 1 (`walker.py::_walk_selections`, the classifier planning seam) gained the `spec-035 Decision 6` / `Decision 7` design-contract pointer and the R1 precondition clause; its five `Pseudocode:` lines are byte-identical. Site 2 (`walker.py::_selected_scalar_names`, the second-consumer audit) gained the **R2** requirement label plus the R1 unreachability clause, and its pseudocode was rewrapped so `Pseudocode:` opens its own line - no word added, removed, or reordered.
- `tests/optimizer/test_walker.py` - the module-level G3 walker-narrowing-pins anchor head retargeted; ` Slice 3` dropped; a pointer to spec-035's G3 deferred test plan and Decision 6 plus the R1 precondition added. The eight `# Pseudocode: synthesize interface/union-like selection trees ...` lines are untouched.
- `tests/optimizer/test_extension.py` - the module-level strictness no-false-fire pin anchor head retargeted; ` Slice 3` dropped; the `if it needs real extension execution rather than pure walker inspection` placement judgement kept verbatim; the spec G3 deferred-test-plan / Decision 6 pointer and R1 precondition added. The four `# Pseudocode: execute an abstract/interface-shaped query ...` lines are untouched.
- `docs/builder/bld-035-slice-2-carry_forward_anchors.md` - this build report; `Status: built`; five `### Dispatched findings checklist` boxes ticked.
- `docs/builder/worker-memory/worker-2.md` - memory entry appended.

**Not touched, per the plan:** `django_strawberry_framework/optimizer/selections.py` (reference form, step 5) and `examples/fakeshop/test_query/test_library_api.py` (baseline-dirty, out of scope, step 6). Both verified unaltered by this pass - `selections.py` reports nothing in `git status --short`, and `test_library_api.py`'s ` M` state is the concurrent session's, untouched here.

### Tests added or updated

**None**, per the plan's `### Test additions / updates`: the slice changes no executable line, and a test asserting comment text would pin the anchor's spelling rather than a contract. The substitute is the executable-token identity proof below. `docs/builder/temp-tests/` stays empty for this slice.

### Validation run

Format and lint, scoped to this pass's three files only (never `.`):

```shell
$ uv run ruff format django_strawberry_framework/optimizer/walker.py tests/optimizer/test_walker.py tests/optimizer/test_extension.py
warning: The following rule may cause conflicts when used with the formatter: `COM812`. ...
3 files left unchanged

$ uv run ruff check --fix django_strawberry_framework/optimizer/walker.py tests/optimizer/test_walker.py tests/optimizer/test_extension.py
All checks passed!

$ uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/optimizer/walker.py tests/optimizer/test_walker.py tests/optimizer/test_extension.py
(no output)      # exit 0
```

No `ERA001` finding appeared, so no `# noqa: ERA001` was needed and no pseudocode line was refactored (`AGENTS.md` rule 18). The plan's baseline is unchanged: `ruff format` reports `3 files left unchanged`, i.e. the hand-written wraps needed no reflow.

`git status --short` after both ruff invocations - the three slice files are present, and every other row is the pre-existing concurrent-session baseline or Slice 1's own output (`docs/SPECS/spec-035-...md`, untracked `docs/SPECS/appx/spec-035-...-rationale.md`, `docs/builder/bld-035-*`), matching the build plan's `### Baseline-dirty out-of-scope files`. **No unexpected churn; nothing reverted.** Slice-intended rows:

```
 M django_strawberry_framework/optimizer/walker.py
 M tests/optimizer/test_extension.py
 M tests/optimizer/test_walker.py
```

The remaining 50 modified / 7 untracked rows are baseline, including ` M examples/fakeshop/test_query/test_library_api.py` and ` M tests/types/test_finalizer.py`, both explicitly out of scope.

ASCII-only and line length (`AGENTS.md` rule 17), measured rather than asserted:

```shell
$ for f in <the three files>; do awk 'length($0)>99 {print FILENAME": "NR}' "$f"; LC_ALL=C grep -n '[^ -~\t]' "$f"; done
```

Zero non-ASCII bytes in all three files. The over-99 rows reported are all pre-existing lines far from the edited hunks (`walker.py:181`; `test_walker.py:1636,1791,1823,3327`; eleven rows in `test_extension.py`) - none is in this diff, and `ruff check` passes on all three. Every line this pass wrote is <= 78 characters.

Focused test scope (plan step (3); no `--cov*` flag):

```shell
$ uv run pytest tests/optimizer/test_walker.py tests/optimizer/test_extension.py --no-cov -q
============================= 351 passed in 9.13s ==============================
```

**351 passed** - exactly the plan's pre-edit baseline (351 passed in 8.93s). No deviation.

### Executable-token identity proof (the `BUILD.md` "carried over unchanged" shape)

**(1) The proof.** Pristine `HEAD` obtained read-only via `git show HEAD:<path>` - no `git stash` / `checkout` / `restore` / `worktree` at any point. Run twice: once with the HEAD text held in memory (the plan's script verbatim), and once with the HEAD text materialized into a scratch directory **outside the repository**, so the comparison is reproducible from files on disk.

```shell
$ uv run python - <<'PY'   # the plan's script, verbatim
... ast.dump(ast.parse(head)) == ast.dump(ast.parse(work)) ...
PY
AST-IDENTICAL  django_strawberry_framework/optimizer/walker.py
AST-IDENTICAL  tests/optimizer/test_walker.py
AST-IDENTICAL  tests/optimizer/test_extension.py
ALL IDENTICAL
# exit 0
```

Same comparison against out-of-repo HEAD copies written by `git show HEAD:<path> > $SCRATCH/<flattened path>` (`$SCRATCH` = `/private/tmp/claude-501/-Users-riordenweber-projects-django-strawberry-framework/f4b7d889-6e73-477e-b5c0-30ac0e17a204/scratchpad/head-035/`):

```
AST-IDENTICAL  django_strawberry_framework/optimizer/walker.py  (HEAD copy: $SCRATCH/django_strawberry_framework_optimizer_walker.py)
AST-IDENTICAL  tests/optimizer/test_walker.py  (HEAD copy: $SCRATCH/tests_optimizer_test_walker.py)
AST-IDENTICAL  tests/optimizer/test_extension.py  (HEAD copy: $SCRATCH/tests_optimizer_test_extension.py)
ALL IDENTICAL
# exit 0
```

Plain `ast.dump` equality (not the docstring-blanked variant): comments are absent from the AST, so equality proves the diff is comment-only **and** that no docstring changed, which this slice required.

**(2) The negative control** - the instrument must be able to report a difference. It writes nothing to disk; `git status --short -- django_strawberry_framework/optimizer/walker.py` after it still reports the single expected ` M` row, so no mutation was left behind.

```shell
$ uv run python - <<'PY'
... perturbed = work.replace("        return None\n", "        return ()\n", 1)   # executable token
... comment_only = work.replace("polymorphic_interface_connections", "PLACEHOLDER", 1)
PY
executable-token control: AST-DIFFERS
comment-only control: AST-IDENTICAL
# exit 0
```

The instrument reports `AST-DIFFERS` on an executable-token perturbation and `AST-IDENTICAL` on a comment-only one - it can fail, so its `ALL IDENTICAL` result above is a measurement, not a tautology.

**(3) Anchor sweep, post-edit** (occurrences counted with `grep -ro`, not matching lines):

```shell
$ grep -rn 'TODO(spec-035' --include='*.py' .
examples/fakeshop/test_query/test_library_api.py:3680:# TODO(spec-035): extend this live connection-fragment block with the

$ grep -rn 'TODO(BACKLOG' --include='*.py' .
tests/optimizer/test_extension.py:5359:# TODO(BACKLOG polymorphic_interface_connections - the abstract-return
tests/optimizer/test_walker.py:4962:# TODO(BACKLOG polymorphic_interface_connections - the abstract-return
django_strawberry_framework/optimizer/selections.py:381:# TODO(BACKLOG polymorphic_interface_connections - the abstract-return optimizer
django_strawberry_framework/optimizer/walker.py:467:    # TODO(BACKLOG polymorphic_interface_connections - the abstract-return
django_strawberry_framework/optimizer/walker.py:1136:    # TODO(BACKLOG polymorphic_interface_connections - the abstract-return

$ grep -ro 'TODO(spec-035' --include='*.py' . | wc -l   ->  1
$ grep -ro 'TODO(BACKLOG' --include='*.py' . | wc -l    ->  5
```

Exactly the plan's expectation: `TODO(spec-035` survives at **one** site only (the baseline-dirty, out-of-scope `test_library_api.py`), and `TODO(BACKLOG` stands at **five** - the reference `selections.py` site, both `walker.py` sites, and both package test sites. No site retains the ` Slice 3` spelling.

### Failability proofs

None; this pass introduced no new boundary. (The slice changes comment text only; `BUILD.md` `### What needs a proof, and what does not` scopes proofs to new boundaries / guards / gates / rejection paths, and the plan's `### No failability proof is owed` records the same conclusion. The obligation this pass carries instead is the executable-token identity proof above, run with its negative control.)

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- **Wrap points.** The plan delegated break points to Worker 2 (`### Implementation discretion items`). Every replacement block was written at the plan's exact wording and wrapped at <= 78 characters, matching the surrounding comment column in each file; `ruff format` left all three files unchanged, so no wrap fought the formatter.
- **The head form is two lines at every site, but breaks one word earlier than `selections.py`.** The reference anchor is module-level and breaks after `... - the abstract-return optimizer`; the two `walker.py` sites sit four spaces in, inside function bodies, so the same text breaks after `... - the abstract-return`. The two module-level test anchors use the walker break too, so all four new sites read identically to each other. The token a sweep greps (`TODO(BACKLOG polymorphic_interface_connections`) is intact on the first line at all five sites - that uniformity is the point of the slice.
- **Edit order** was site 1, site 2, `test_walker.py`, `test_extension.py` (the plan declared order immaterial); one ruff pair at the end, on the three files only.
- **No `# noqa: ERA001` was added.** The rewrapped `_selected_scalar_names` pseudocode did not trip ERA001, so the plan's conditional did not fire and no pseudocode was restructured.

### Notes for Worker 3

- **The static-inspection helper was not re-run this pass.** `BUILD.md` `### When to run the helper during build` makes it a *may* for Worker 2, and the plan already carries fresh output: `docs/shadow/django_strawberry_framework__optimizer__walker.overview.md` (24 imports, 37 symbols, 2 TODO comments - both this slice's targets) and the `selections.py` pair (1 TODO - the reference anchor). Nothing in this diff changes any symbol, import, hotspot, or literal those overviews enumerate, so the plan-pass output is still accurate against it. Worker 3's own trigger fires (`touches an existing .py file under optimizer/`), so re-run it there for an independent read.
- **What to re-derive rather than accept from this report:** the AST proof and its negative control both re-run in seconds and write nothing (`git show HEAD:<path>` only). If you re-run the control, check afterwards that `git status --short -- django_strawberry_framework/optimizer/walker.py` still shows exactly one ` M` row - the control mutates only an in-memory string, and that check is what proves it.
- **Boxes ticked:** all five `### Dispatched findings checklist` boxes. The first four each correspond to one retargeted anchor visible in the diff; the fifth is the identity proof recorded above. Nothing was deferred, so no box was left open.
- **The pseudocode blocks are the review's load-bearing invariant.** Sites 1, 3 and 4 have byte-identical pseudocode across the diff (verify with `git diff` - those lines are context, not `+`/`-`). Site 2's is the one rewrap the plan prescribed: `Pseudocode:` now opens its own line instead of continuing the prose sentence. Its words are unchanged in content and order; only the line breaks differ.
- **`selections.py` and `examples/fakeshop/test_query/test_library_api.py` are deliberately absent from the diff** (plan steps 5 and 6). The latter is the fifth anchor site and stays `TODO(spec-035)`; that is a recorded deferral, not a miss.

### Notes for Worker 1 (spec reconciliation)

**No plan-vs-implementation drift.** Every replacement block landed at the plan's prescribed wording; no architectural call was made in this pass.

Two items for the `### Deferred work catalog` in `docs/builder/bld-035-final.md`. Both restate the plan pass's routing with the post-build measurement attached, so the catalog can cite a measured state rather than a prediction:

1. **The fifth carry-forward anchor is still unretargeted, and it is now the *only* `TODO(spec-035` occurrence in the tree.** Measured post-edit: `grep -ro 'TODO(spec-035' --include='*.py' . | wc -l` -> **1**, at `examples/fakeshop/test_query/test_library_api.py:3680` (`# TODO(spec-035): extend this live connection-fragment block with the ...`). The file is baseline-dirty with a concurrent session's work, so this cycle may neither edit nor revert it (`AGENTS.md` rule 34). It should receive the same `TODO(BACKLOG polymorphic_interface_connections - the abstract-return optimizer entry card)` head once that session's work lands. This is the single anchor that will make `BUILD.md` `## Cross-slice integration pass` step 6's sweep non-empty at integration - a recorded deferral, not a new finding.
2. **The two package test-tree anchors become deletable once the spec records their file placement.** Unchanged from the plan pass: they survive only because the spec's G3 deferred test-plan heading names no file, unlike its Slice 1 and Slice 2 headings. Not actionable this cycle (Slice 3 may not edit `.py`; this slice may not edit the spec).

**Spec amendment recommended - one, owned by Slice 3.** The staged-anchor paragraph is now falsified by this diff in a third way (its two originally-stale claims were recorded at plan time; the retarget adds a third - the `spec-035` spelling is now absent from the package entirely). In the three-part amendment form so the custodian does not re-derive it:

- **Where it lives:** `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md`, `## Implementation plan`, the final paragraph beginning `Staged-but-not-implemented seams follow the ...` (immediately preceding `## Edge cases and constraints`).
- **Current wording, quoted:** "Deferring Slice 3 introduced exactly the cross-slice seams the discipline anticipates: the `TODO(spec-035 Slice 3)` comments at the [`included_field_selections`][selections] inliner, the [`_walk_selections`][walker] planning seam, and the `_selected_scalar_names` second-consumer site."
- **Recommended replacement:** "Deferring G3 introduced exactly the cross-slice seams the discipline anticipates. Because the deferral moved the work to the abstract-return optimizer entry card rather than to a later slice of this card, each seam names that card, not this spec: `TODO(BACKLOG polymorphic_interface_connections - the abstract-return optimizer entry card)` anchors stand at the [`included_field_selections`][selections] inliner, the [`_walk_selections`][walker] planning seam, the `_selected_scalar_names` second-consumer site, and the two package test sites that will host the deferred pins ([`tests/optimizer/test_walker.py`][test-opt-walker], [`tests/optimizer/test_extension.py`][test-opt-extension]). Each body cites this spec's Decision 6 / Decision 7 as the design contract and the R1 entry-contract precondition."
- **Why:** the sentence's count (three) and form (`TODO(spec-035 Slice 3)`) are both false against the package after this slice - five sites, none spelled `spec-035`. Backing measurement: `grep -ro 'TODO(BACKLOG' --include='*.py' .` -> **5**; `grep -ro 'TODO(spec-035' --include='*.py' .` -> **1**, and that one is `examples/fakeshop/test_query/test_library_api.py`, outside the package. If Slice 3 prefers to keep the example-project site in the sentence, it is the sixth seam and still carries the old spelling per deferral item 1 above.

---

## Review (Worker 3)

Every number below was re-measured this pass; nothing is carried from the build report. Working-tree
diff read at `git diff -- django_strawberry_framework/optimizer/walker.py tests/optimizer/test_walker.py
tests/optimizer/test_extension.py`: **27 added lines, 10 removed, all `#` comment lines** (measured:
`git diff ... | grep '^+[^+]' | grep -vc '^+\s*#'` -> 0 non-comment additions).

**Independent re-derivation of the "carried over unchanged" claim.** Not accepted from the build
report. Pristine `HEAD` obtained read-only via `git show HEAD:<path>` into
`/private/tmp/claude-501/.../scratchpad/w3-035-s2/` (outside the repository); no `git stash` /
`checkout` / `restore` / `worktree` at any point. My own `ast.dump(ast.parse(...))` comparison:

```
AST-IDENTICAL  django_strawberry_framework/optimizer/walker.py
AST-IDENTICAL  tests/optimizer/test_walker.py
AST-IDENTICAL  tests/optimizer/test_extension.py
ALL IDENTICAL                                            # exit 0
```

**My own negative controls** (in-memory only; nothing written to the tree). The plan's two, plus a
third I added because plain `ast.dump` equality is also being relied on to prove *no docstring
changed* — an instrument that cannot see a docstring edit would not have proved that half:

```
executable-token control: AST-DIFFERS      # "return None" -> "return ()", first occurrence
comment-only control:     AST-IDENTICAL    # "polymorphic_interface_connections" -> "PLACEHOLDER"
docstring control:        AST-DIFFERS      # first '"""' -> '"""ZZZ'
```

`git status --short` for the three files after the controls still reports exactly three ` M` rows —
no mutation left behind.

**The one rewrap, checked word-for-word rather than on assertion.** Site 2's pseudocode is the only
block whose bytes changed, so byte-identity is unavailable and "no word added, removed, or reordered"
had to be measured. Extracting the comment run from HEAD and from the working tree and comparing the
token sequence from `Pseudocode:` onward returns `WORD-SEQUENCE EQUAL: True`. The other three sites'
pseudocode lines appear as diff context (`+`/`-` free), which is byte-identity directly.

**Dispatched findings checklist walk** — all five boxes ticked by Worker 2, all five confirmed against
the diff, none over-ticked, nothing deferred without a record:

1. `walker.py::_walk_selections` — head retargeted, `spec-035 Decision 6` / `Decision 7` pointer and
   the R1 precondition added, five `Pseudocode:` lines byte-identical. **Landed.**
2. `walker.py::_selected_scalar_names` — head retargeted, **R2** label present and correctly attributed
   (R2 does live under Decision 6's `#### Carry-forward requirements` block), pseudocode word-identical
   after the prescribed rewrap. **Landed.**
3. `tests/optimizer/test_walker.py` — head retargeted, ` Slice 3` gone, G3-deferred-test-plan and
   Decision 6 pointers added, **no new test name introduced** (measured: zero test identifiers in the
   27 added lines), eight pseudocode lines untouched. **Landed.**
4. `tests/optimizer/test_extension.py` — head retargeted, ` Slice 3` gone, the placement judgement
   `if it needs real extension execution rather than pure walker inspection` preserved verbatim, four
   pseudocode lines untouched. **Landed.**
5. Executable-token identity proof + negative control — recorded with output, and re-derived above
   rather than accepted. **Landed.**

**Failability proof: none is owed, and its absence is not graded as a gap.** Confirmed by reading the
diff rather than by accepting the plan's declaration: 27 added lines, every one a `#` comment; zero
executable additions; AST identity against `HEAD` on all three files. No guard, gate, cap, rejection
path, or validation branch rode along. Hot-path and floor verification are `none` per the build plan's
declarations, correctly so — nothing runs differently on any path.

**Gates re-run, not read.** `uv run ruff format --check .` -> `435 files already formatted`;
`uv run ruff check .` -> `All checks passed!` (both tree-wide, so no attribution question arises —
neither reported a failure anywhere, in this cohort or in the concurrent sessions' files).
`uv run python scripts/check_trailing_commas.py --check <the three files>` -> exit 0 (this is also the
ASCII-only gate). `uv run pytest tests/optimizer/test_walker.py tests/optimizer/test_extension.py
--no-cov -q` -> **351 passed in 9.05s**, matching the plan's pre-edit baseline exactly. No `--cov*`
flag on any invocation.

**Rule-compliance sweep over the 27 added lines**, each measured, not eyeballed: process vocabulary
(`slice` / `worker` / `revision` / `review round`) -> **0 hits**; raw `path:NN` refs (`AGENTS.md` rule
27) -> **0 hits**; non-ASCII bytes -> **0**; longest added line -> **78 characters** (limit 99). No
`# noqa: ERA001` needed and none added, so no pseudocode was restructured to satisfy a lint
(`AGENTS.md` rule 18).

**Anchor sweep, re-derived with my own vocabulary rather than the plan's.** `TODO(spec-035` across
`*.py` -> **1** occurrence, `examples/fakeshop/test_query/test_library_api.py:3680` (baseline-dirty,
out of scope). `TODO(BACKLOG` -> **5**, the reference `selections.py` site plus this slice's four. I
also swept three vocabularies the plan's token could not reach — bare `spec-035` in `*.py`, `\bG3\b`
in `*.py`, and `TODO(spec-035` across **all** file types, not just `*.py` — because a long or single
token samples a claim's vocabulary rather than establishing its population. Result: every remaining
`spec-035` mention in `.py` is a **provenance citation** (`spec-035 Decision 4` / `Decision 5` in
docstrings and comments), not a staged anchor; the only non-`.py` occurrences are the spec sentence
Slice 3 owns, this cycle's own artifacts, and archived `DONE/` build plans. **No fifth in-scope
anchor was missed.**

**The anchor's owner is real, verified rather than assumed.** `BACKLOG.md:1203` carries
`### \`polymorphic_interface_connections\``, so `grep -rn 'polymorphic_interface_connections'` returns
the owning card plus all five seams in one listing — which is the entire value proposition of the
retarget, and it holds.

**Verdict on the two standing rules (asked for explicitly; this is where I land).** The landed wording
satisfies both, and Worker 1's resolution is the right one — I am not re-litigating it, I am confirming
it against the sources.

- **`AGENTS.md` rule 26** wants a staged anchor to name **the doc and the owning slice**. The landed
  form names the doc (`spec-035 Decision 6` / `Decision 7` in every body) and the owner (the
  `BACKLOG.md` card in every head). Its *literal* `spec-NNN slice N` spelling is not satisfied, and
  cannot be: the unit rule 26 would have it name — spec-035 Slice 3 — was abolished by Decision 7's
  `**Decision (maintainer): defer G3 entirely from spec-035.**`, which routes the work to a different
  card. An anchor naming an owner that will never ship it is the failure rule 26 exists to prevent,
  not the form it prescribes. Substance over spelling is the correct reading here.
- **The standing no-process-provenance rule** is satisfied mechanically: zero `Slice` / `Worker` /
  `Revision` / review-round tokens in the added text (measured above), and `spec-NNN Decision N` is a
  contract pointer on that rule's KEEP list, not process provenance.
- **The anchor still tells a future implementer what to build:** head names the owner, body names the
  design contract and the R1 precondition, pseudocode carries the mechanism. **No pseudocode line lost
  technical content** — three sites byte-identical, the fourth word-identical.
- Corroboration, not a finding: `tests/test_permissions.py:43` still carries a live
  `TODO(spec-036 Slice 3)`. The canonical rule-26 spelling remains in the tree where its owning slice
  is still real, so this slice's departure is scoped to the case where the owner was retired — exactly
  as intended, not a drift in the convention.

**Existence challenge (`BUILD.md` DRY-first), both legs re-derived.** Worker 1 kept the two package
test-tree anchors on the ground that they carry a file-placement judgement the spec does not hold. Both
halves check out:

- `grep -n '^### Slice' docs/SPECS/spec-035-optimizer_hardening-0_0_10.md`: the Slice 1 and Slice 2
  test-plan headings name their files; **`### Slice 3 — G3 — DEFERRED ...` names none.**
- `grep -rn 'real extension execution'` over the spec **and** its rationale companion -> **no hits**.
  `test_extension.py`'s conditional routing judgement exists nowhere else in the repo.

So deleting the anchors would drop information the spec does not carry, and the maintainer's
pseudocode-preservation constraint forecloses trimming only the duplicative half. **I agree with the
keep-and-retarget decision**, and with the recorded flip condition (if the deferred test plan ever
records the file placement, both anchors reduce to duplicates and should be deleted then). Re-carried
to Worker 1's catalog below rather than actioned, since this slice may not edit the spec.

**Static inspection helper**, run as required (the slice touches an existing `.py` file under
`django_strawberry_framework/optimizer/`):

```shell
uv run python scripts/review_inspect.py django_strawberry_framework/optimizer/walker.py --output-dir docs/shadow
```

Fresh output: 24 imports, 37 symbols, 8 control-flow hotspots, 65 executable marker lines, 7 repeated
string literals, **2 TODO comments**. No skip to record.

- **TODO comments (2)** — `walker.py:467` and `walker.py:1136`, both this slice's targets, both now
  reading `# TODO(BACKLOG polymorphic_interface_connections - the abstract-return`. The helper's own
  count is the independent confirmation that walker.py holds no third anchor this slice missed.
- **Django / ORM markers (65)** and **repeated string literals (7: `prefetch` 3x, `connection` 3x,
  `arguments` 3x, `operation` 2x, `_optimizer_runtime_prefixes` 2x, `prefetch_through` 2x,
  `selections` 2x)** — one justification covers the whole population rather than 72 restatements of
  the same fact: every marker and every literal sits on an **executable** line, and this diff adds no
  executable line (AST identity proved above, zero non-comment additions measured). Not one entry is
  inside this diff, so none is this slice's to justify individually and none yields a finding. Cited
  by symbol / original-source line only; no shadow line number appears anywhere in this review.

**Test staleness (run independently of the slice's file list, per my role's delta).** The change set
is provably comment-only, so no test in any tree can be stranded by it: no example-model field moved,
no wire shape converted, no symbol renamed. The full focused scope passes at the plan's exact
pre-edit count. Nothing to sweep.

### High:

None.

### Medium:

None.

### Low:

#### Raw spec line-number citations in shipped `.py` comments, falsified by this cycle's own Slice 1

`AGENTS.md` rule 27 permits raw `path:NN` refs **only** in per-cycle scratchpads and forbids them in
code comments. Four shipped comments cite the spec by line number, and two of them sit in files inside
Slice 2's own ownership partition:

```
django_strawberry_framework/optimizer/walker.py:853   ... regardless of operation (Decision 4 / edge case line 315).
tests/optimizer/test_walker.py:4896                   ... identically to MUTATION (spec-035 Decision 4 / edge case line 317).
tests/optimizer/test_walker.py:4912                   ... by default (spec-035 Decision 4 / edge case line 320). Also drives the
tests/types/test_resolvers.py:1035                    ... so ``operation_arm`` only documents the two shapes - spec-035 edge case 316).
```

Why it matters, measured rather than asserted: the spec went from **542 lines at `HEAD` to 498 lines**
in the working tree, because **Slice 1 of this cycle** moved the deliberative layer into
`docs/SPECS/appx/…-rationale.md`. At `HEAD`, spec lines 316 / 317 / 320 held the
`every projection writer checks the gate` / `consumer-provided .only(...)` / `DjangoConnectionField is
gated by construction` edge-case bullets; in the working tree lines 316-317 are Slice-2 **test-plan**
bullets and line 320 is blank. Those bullets now live at 271 / 272 / 275. Every one of the four
citations sends a reader to the wrong text today. (One was already off by one at `HEAD` — the
subscription bullet the `:4896` comment describes was at `HEAD`:318, not 317 — which is the standing
reason the convention bans the form: a line citation rots silently and nothing gates it.)

Recommended change: replace each with the symbol/substring form rule 27 prescribes — a
`spec-035 #"<unique substring>"`-style pointer or a bare `spec-035 Decision 4` (a contract pointer,
already the dominant spelling in these same files), dropping the line number entirely. No behavior is
affected, so no test expectation changes.

**Recorded disposition — not routed back to Worker 2 in this pass, and this is why.** The citations
pre-date the slice, are not on the `### Dispatched findings checklist`, and lie outside the four
anchor sites the maintainer scoped Slice 2 to. But they are not simply pre-existing either: this
cycle's Slice 1 is what guaranteed they are now wrong, and `BUILD.md` `### Test staleness a focused run
cannot see` makes a regression the build introduced the build's to fix in-loop. Whether that lands as
a comment-only follow-up pass in this cycle or in the deferred-work catalog is a scope call that
belongs to Worker 1, so it is escalated below rather than decided here. It does not block acceptance
of this slice.

### DRY findings

- **Examined and rejected: the four R1 precondition clauses are not a consolidation target.** Each new
  block restates "the abstract-return production-entry contract (R1)" in its own grammatical frame
  (`That card must first build …` / `it is unreachable until the same card builds …` / `they are
  unreachable until that card builds …` / `unreachable until that card builds …`). Four near-copies of
  one sentence is the shape I would normally flag. It is right here: a staged anchor is reached by
  `grep`, and a reader who lands on one must not have to jump to learn whether the work is reachable.
  What would actually drift — the **mechanism** (`registry.model_for_type` returns `None` for the
  abstract origin, so `_optimize` passes the queryset through before the inliner runs) — is stated
  exactly **once**, at `selections.py #"TODO(BACKLOG polymorphic_interface_connections"`, and is not
  repeated at any of the four new sites. That is the correct split, and the plan's
  `### DRY analysis` (a) anticipated it.
- **Examined and rejected: the spec's named-test roster is not duplicated further.** The retarget adds
  a pointer to the G3 deferred test plan and **zero** additional test names (measured: no test
  identifier appears in the 27 added lines), so the roster keeps one authoritative home.
- **No new helper, constant, indirection, or abstraction is introduced** — the slice writes no
  executable line, so there is nothing to extract and nothing whose existence could be challenged
  beyond the anchors themselves (challenged above, kept).
- Cross-cohort duplication review: not applicable; the build plan declares `ownership partition: none;
  sequential slices`, so there is no parallel cohort to compare against.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **not** empty, and the change is **not this
slice's**:

```
-__version__ = "0.0.14"
+__version__ = "0.0.15"
```

`__all__` and the re-export list are **unchanged** — the single changed line is the `__version__`
literal. `django_strawberry_framework/__init__.py` appears in no cohort of the build plan's
`## Declarations` ownership table, and Slice 2's diff is confined to the three cohort files, so this is
a concurrent session's release-line bump and falls under `AGENTS.md` rule 34 (never edit, never
revert). Slice 2 adds no public export, consistent with spec Decision 9's "this card adds no public
symbol".

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. (This artifact and
`docs/shadow/` are per-cycle scratchpads, not doc surfaces; the spec was correctly left untouched.)

### What looks solid

- **The claim that carried the whole slice is the one that was actually proved.** "Comment-text only"
  is exactly the shape `BUILD.md` calls the cheapest claim in the build, and it was discharged with a
  mechanical instrument plus a negative control rather than with prose — and the control was the right
  control, because plain `ast.dump` equality was also load-bearing for "no docstring changed", which my
  third control confirms the instrument can see.
- **The plan pre-resolved the rule-26 / no-process-provenance tension in writing, with the commit
  evidence attached.** That is the difference between a decision and a coincidence: a reviewer with no
  memory of this cycle can check it instead of re-fighting it, which is precisely what happened here.
- **Uniform head form across all five sites.** `grep -rn 'TODO(BACKLOG polymorphic_interface_connections'`
  now returns the owning `BACKLOG.md` card plus every production and test seam in one listing. The
  half-retargeted state that commit `dd8dc0b3` left behind is closed for every site this cycle may
  touch.
- **The out-of-scope sites were left alone and said so.** `selections.py` (reference form) and
  `test_library_api.py` (baseline-dirty) are absent from the diff and both are recorded as deliberate
  with the rule that licenses each. The integration pass's step-6 sweep being non-empty is
  pre-announced as a recorded deferral rather than left to surface as a new finding.
- **The lint conditional did not fire and was not forced.** No `# noqa: ERA001` was added and no
  pseudocode was restructured; `ruff format` left all three files unchanged, so the hand-written wraps
  agree with the formatter.

### Temp test verification

- No temp test was written. `docs/builder/temp-tests/` is empty (measured: 0 entries) and correctly
  stays so — the slice changes no behavior, so there is nothing a temp test could demonstrate, and a
  test asserting comment text would pin an anchor's spelling rather than a contract.
- The verification scripts I ran live **outside the repository**, under
  `/private/tmp/claude-501/.../scratchpad/w3-035-s2/`, and write nothing into the tree.
- Disposition: nothing to promote.

### Notes for Worker 1 (spec reconciliation)

**The recorded spec amendment is on disk and is correct — with one omission.** Worker 2's
`### Notes for Worker 1 (spec reconciliation)` carries the amendment in the three-part form (where it
lives, current wording quoted, recommended replacement, why), and I verified the two link ids the
replacement introduces both already resolve in the spec's own definition block
(`[test-opt-walker]`, `[test-opt-extension]` — present, alongside `[selections]` and `[walker]`), so
the replacement will not create link rot. The omission:

- **The sentence *preceding* the one being replaced is also falsified, and the amendment leaves it
  standing.** The staged-anchor paragraph opens
  `a source-site \`TODO(spec-035 Slice N)\` comment naming this spec and the owning slice`. After this
  slice, no seam in the package carries that spelling; the sentence sets up, in the present tense, the
  exact form the retarget deliberately departed from, and a reader reaching the corrected second
  sentence has just been told to expect something else. Slice 3 should rewrite the opening clause too —
  generalising it to the discipline (an anchor names its owning document and the unit that will ship
  the work) rather than to one spelling — so the paragraph reads as one coherent contract. **Not
  actionable by me**: Worker 3 never edits the spec.

**Escalated: the four raw spec-line citations in shipped `.py` comments** (the Low finding above;
`walker.py:853`, `test_walker.py:4896`, `test_walker.py:4912`, `test_resolvers.py:1035`). Measured:
the spec shrank 542 -> 498 lines under **this cycle's Slice 1**, so all four now point at the wrong
text, and the form is an `AGENTS.md` rule 27 violation independent of the drift. Two resolution paths,
Worker 1's call at final verification:

1. **Fix in-loop** as a comment-only follow-up pass — the work is identical in kind to Slice 2, two of
   the four sites are already in Slice 2's ownership partition, and `BUILD.md`
   `### Test staleness a focused run cannot see` says a regression the build introduced is the build's
   to fix in-loop rather than to hand off. Note `tests/types/test_resolvers.py` is in **no** cohort of
   the plan's ownership table, so this path needs Worker 0 to extend the partition.
2. **Catalog it** in `bld-035-final.md` `### Deferred work catalog` as a follow-up, on the ground that
   the maintainer scoped this cycle to the four anchor sites and the citations are not anchors.

I did not decide between them because the scope call is not a reviewer's; the finding does not block
acceptance either way.

**Carried forward to the `### Deferred work catalog` in `docs/builder/bld-035-final.md`** — Worker 2's
two items stand, re-derived rather than restated, plus one new:

1. **The fifth anchor is unretargeted**, confirmed by my own sweep:
   `examples/fakeshop/test_query/test_library_api.py:3680` is the sole `TODO(spec-035` occurrence in
   any `.py` file. Baseline-dirty; never edit, never revert. Confirmed as the one anchor that makes the
   integration pass's step-6 sweep non-empty.
2. **The two package test-tree anchors become deletable once the spec records their file placement** —
   both legs of that condition independently verified above (the G3 deferred test-plan heading names no
   file; `real extension execution` appears nowhere in the spec or its rationale).
3. **New: the reference anchor is now the least informative of the five. CLOSED 2026-09-01.**
   `django_strawberry_framework/optimizer/selections.py` cited `(R1)` **without naming the document
   that defines it** — it was the one site of five whose body carried no `spec-035 Decision N`
   pointer, so a reader landing there by `grep` could find the owning card but not the design
   contract. The four sites this slice wrote all carry the pointer. `selections.py` was deliberately
   outside this cycle's ownership partition when this slice ran, so it was catalogued as
   `bld-035-final.md` D3 rather than raised as a finding against Slice 2, and the maintainer later
   authorized the one-clause close. The body now reads
   `#"contract: spec-035 Decision 6 (the tri-state classifier and its accept set)"` and
   `#"contract (spec-035 Decision 6 R1). Pseudocode:"` — both quoted as they sit on a *single*
   comment line, since the prose word `Design` that precedes the first one is on the line above and a
   pinpoint spanning that wrap resolves zero times. **Note for any later citation into this
   block:** the original pinpoint here was `#"contract (R1). Pseudocode:"`, and that close broke it —
   an anchor quoting the very text a catalogued fix is going to rewrite cannot survive the fix, so
   cite the *stable* neighbourhood (the `TODO(BACKLOG ...` opener) rather than the defective phrase
   when recording a defect for later repair.

### Review outcome

`review-accepted`.

The diff does exactly what the artifact says and nothing else, mechanically proved rather than
asserted: 27 comment lines, zero executable change, AST-identical to `HEAD` on all three files under an
instrument my own three controls show can fail. All five dispatched boxes landed; no box is over-ticked;
no boundary was introduced, so no failability proof is owed and its absence is not graded. Every gate
re-run green at the recorded scope. The single Low finding is recorded with its disposition and is
escalated to Worker 1 rather than left open, per `worker-3.md` `### Acceptance gate` — it concerns
comments this slice did not write, and resolving it is a scope decision Worker 2 cannot make.

---

## Build report (Worker 2, pass 2)

Apply-changes pass for the Worker 3 Low finding **Raw spec line-number citations in shipped `.py`
comments, falsified by this cycle's own Slice 1**. Nothing from pass 1 is withdrawn: the four
retargeted carry-forward anchors stand exactly as they landed, and this pass only **adds** the four
citation fixes.

- **Mid-flight instruction from Worker 0, mirrored here per `worker-0.md`
  `### Mid-flight instructions are mirrored into the artifact`.** After pass 1, Worker 0 instructed
  that **resolution path 1 is chosen** — fix the citations in-loop rather than catalog them — and
  that **`tests/types/test_resolvers.py` is folded into Slice 2's ownership partition** so this pass
  may write it. The reason given is `BUILD.md` `### Test staleness a focused run cannot see`: a
  regression either shape introduces is the build's to fix **in-loop**, never a separate-session
  follow-up. This cycle's Slice 1 shrank the spec from 542 to 498 lines, so this cycle owns the
  breakage.

### Files touched

Grounded in `git status --short` after both ruff invocations (quoted under `### Validation run`).

- `django_strawberry_framework/optimizer/walker.py` — `_record_relation_access`'s docstring: the
  raw citation `(Decision 4 / edge case line 315)` replaced by
  `(Decision 4 / Edge cases #"every projection writer checks the gate")`. `Decision 4` kept.
- `tests/optimizer/test_walker.py` — two docstrings.
  `test_subscription_operation_gated`: `(spec-035 Decision 4 / edge case line 317)` ->
  `(spec-035 Decision 4 / Edge cases #"subscription operations are gated identically")`.
  `test_enable_only_defaults_enabled_without_info`: `(spec-035 Decision 4 / edge case line 320)` ->
  `(spec-035 Decision 4 / Edge cases #"defaults to enabled")`, with the following sentence rewrapped
  by one word to hold the 99-column limit. `Decision 4` kept at both sites.
- `tests/types/test_resolvers.py` — newly in this cohort.
  `test_fk_id_elision_falls_back_when_consumer_only_defers_fk`'s docstring:
  `- spec-035 edge case 316).` -> `), per spec-035 Decision 5 / Edge cases
  #"can defer the FK column (both".` The trailing parenthetical is closed one clause earlier so the
  anchor ends the sentence instead of nesting a quote inside a paren. The docstring's own opening
  `Decision 5:` label is untouched.
- `docs/builder/bld-035-slice-2-carry_forward_anchors.md` — this build report; `Status: built`;
  five new `### Dispatched findings checklist` boxes added and ticked.
- `docs/builder/worker-memory/worker-2.md` — memory entry appended.

**Not touched:** `tests/optimizer/test_extension.py` (in the writable list, but its three
`Decision 7 line 346/347` citations name **other** specs and are explicitly cataloged-not-fixed);
`django_strawberry_framework/optimizer/selections.py`; the spec, its `-rationale.md` and
`-terms.csv`; `examples/fakeshop/test_query/test_library_api.py` and every other baseline-dirty
out-of-scope file.

### How each citation was bound to its bullet

By **content**, read out of the spec's current `## Edge cases and constraints` section — never by
counting to a line. All four were already off by one or two before this cycle, so the pre-existing
numbers were not usable even as a starting point.

| Site | Bullet it describes | Anchor written |
|---|---|---|
| `walker.py::_record_relation_access` | `**G2 — every projection writer checks the gate, not just scalar appends.**` — the bullet names `_record_relation_access` explicitly as the FK-connector-column writer | `#"every projection writer checks the gate"` |
| `test_walker.py::test_subscription_operation_gated` | `**G2 — subscription operations are gated identically.**` | `#"subscription operations are gated identically"` |
| `test_walker.py::test_enable_only_defaults_enabled_without_info` | `**G2 — a missing `info` *or* `info.operation` defaults to enabled.**` | `#"defaults to enabled"` |
| `test_resolvers.py::test_fk_id_elision_falls_back_when_consumer_only_defers_fk` | `**G2 / Decision 5 — consumer-provided `.only(...)` can defer the FK column (both `QUERY` and non-`QUERY`).**` — that bullet names this exact test as its pin | `#"can defer the FK column (both"` |

Anchor uniqueness verified **before writing**, occurrences (not matching lines) counted against the
working-tree spec:

```shell
$ S=docs/SPECS/spec-035-optimizer_hardening-0_0_10.md
$ for a in 'every projection writer checks the gate' \
           'subscription operations are gated identically' \
           'defaults to enabled' 'can defer the FK column (both'; do
      printf '%-50s %s\n' "$a" "$(grep -oF "$a" $S | wc -l)"; done
every projection writer checks the gate             1
subscription operations are gated identically       1
defaults to enabled                                 1
can defer the FK column (both                       1
```

`can defer the FK column` alone occurs **3** times in the spec (`:22`, `:50`, `:272`) and was
rejected for that reason; `(both` is the shortest suffix that makes it resolve once. Every anchor is
written **whole on one line** — a citation wrapped across two lines is invisible to the sweep that
would catch its regression.

Population re-derived after the edits with Worker 0's own instrument (an anchor measurement, not
this slice's token):

```shell
$ grep -rnoE "edge case[s]? (line )?[0-9]+" --include='*.py' .
(no output)
```

Zero occurrences tree-wide. The out-of-scope `Decision 7 line 346` / `347` citations in
`tests/optimizer/test_extension.py` and the three in `tests/mutations/test_sets.py` use a different
grammar and are **not** in this population; they are cataloged by Worker 0 against another card and
were deliberately left alone.

### Tests added or updated

**None.** The pass changes no executable line; a test asserting comment or docstring prose would pin
the citation's spelling rather than a contract. The substitute is the identity proof below.
`docs/builder/temp-tests/` stays empty for this slice.

### Validation run

Format and lint, scoped to this pass's files (never `.` in write mode — `worker-2.md` step 5; the
tree carries concurrent work). The file list was passed as a **zsh array**, because `$F` does not
word-split in zsh and a bare `$F` makes the invocation fail (or, worse for a sweep, silently run
once on a joined path):

```shell
$ F=(django_strawberry_framework/optimizer/walker.py tests/optimizer/test_walker.py \
     tests/types/test_resolvers.py tests/optimizer/test_extension.py)
$ echo "population: ${#F[@]}"
population: 4

$ uv run ruff format "${F[@]}"
4 files left unchanged

$ uv run ruff check --fix "${F[@]}"
All checks passed!

$ uv run python scripts/check_trailing_commas.py --check "${F[@]}"
(no output)      # exit 0
```

Repo-wide, **read-only** (the gate `AGENTS.md` rule 16 targets, without writing into another
session's files):

```shell
$ uv run ruff format --check .
435 files already formatted
$ uv run ruff check .
All checks passed!
```

`AGENTS.md` rule 17, measured: **zero** non-ASCII bytes in all four files
(`LC_ALL=C grep -n '[^ -~\t]'` returns nothing). The longest line this pass wrote is **78**
characters (`git diff | grep -E '^\+[^+]' | awk '{print length($0)-1}' | sort -rn | head -1`); the
over-99 rows that exist in these files (1 in `walker.py`, 4 in `test_walker.py`, 6 in
`test_resolvers.py`, 11 in `test_extension.py`) are all pre-existing and none is in this diff.

`git status --short` after both ruff invocations — 62 rows, of which exactly **four** are this
pass's or pass 1's:

```
 M django_strawberry_framework/optimizer/walker.py
 M tests/optimizer/test_extension.py        <- pass 1 only; untouched this pass
 M tests/optimizer/test_walker.py
 M tests/types/test_resolvers.py
```

Every other row is the pre-existing concurrent-session baseline or this cycle's own doc output.
Note `tests/rest_framework/test_resolvers.py` is **also** ` M` and is **not** mine — it is
baseline-dirty and must not be confused with `tests/types/test_resolvers.py`. Nothing unexpected was
touched and nothing was reverted.

Focused run (no `--cov*` flag; `--no-cov` only):

```shell
$ uv run pytest tests/optimizer/test_walker.py tests/optimizer/test_extension.py \
    tests/types/test_resolvers.py --no-cov -q
============================= 399 passed in 10.90s =============================
```

**399 passed.** Attributable against pass 1's recorded baseline: the two optimizer files alone still
report **351 passed in 9.04s** (identical to pass 1 and to the plan's pre-edit baseline), and the
newly cohorted `tests/types/test_resolvers.py` contributes **48 passed in 4.24s**. 351 + 48 = 399,
so the count grew only by the file the partition added — no test changed status.

### Identity proof — which instrument, per file, and why

**The instrument changed for three files, and this is stated rather than switched silently.** The
dispatch predicted that only `tests/types/test_resolvers.py`'s citation sat inside a docstring. It is
**all four**: `walker.py:853` is inside `_record_relation_access`'s docstring, and both
`test_walker.py` citations are inside their test docstrings. Plain `ast.dump` equality therefore
legitimately differs for three of the four files, and the docstring-blanked comparison is the
instrument for them. `tests/optimizer/test_extension.py` is unchanged this pass and still satisfies
the **stronger** plain-`ast.dump` equality, which is reported alongside as evidence pass 1's
comment-only claim for that file still holds.

Pristine `HEAD` obtained read-only via `git show HEAD:<path>` into a scratch directory **outside the
repository** — `/private/tmp/claude-501/-Users-riordenweber-projects-django-strawberry-framework/f4b7d889-6e73-477e-b5c0-30ac0e17a204/scratchpad/head-035-pass2/`.
No `git stash` / `checkout` / `restore` / `worktree` at any point. `HEAD` is pristine of **both**
passes, so every result below covers pass 1 and pass 2 together.

The comparison also enumerates **which** docstrings differ, so "no docstring changed except the
citations" is measured rather than asserted:

```
PLAIN-DIFFERS   BLANKED-IDENTICAL  docstrings changed: ['_record_relation_access']                      django_strawberry_framework/optimizer/walker.py
PLAIN-DIFFERS   BLANKED-IDENTICAL  docstrings changed: ['test_subscription_operation_gated',
                                                        'test_enable_only_defaults_enabled_without_info']  tests/optimizer/test_walker.py
PLAIN-IDENTICAL BLANKED-IDENTICAL  docstrings changed: none                                             tests/optimizer/test_extension.py
PLAIN-DIFFERS   BLANKED-IDENTICAL  docstrings changed: ['test_fk_id_elision_falls_back_when_consumer_only_defers_fk']  tests/types/test_resolvers.py
ALL BLANKED-IDENTICAL
# exit 0
```

Exactly four docstrings differ — one per citation site, no fifth. Combined with the diff itself
(`git diff | grep -E '^[+-][^+-]'` shows only comment lines from pass 1 and these four docstring
lines), the "no executable line changed" claim holds across both passes.

**Negative controls — three, run in memory, nothing written to the tree.** The blanked instrument
deliberately cannot see a docstring edit, so a docstring control under it *must* print IDENTICAL;
the same control under the plain instrument is what proves the docstring enumeration above is itself
a measurement:

```
executable-token control (blanked instrument): DIFFERS     # "return None" -> "return ()", 1st occurrence
comment-only control     (blanked instrument): IDENTICAL   # "polymorphic_interface_connections" -> "PLACEHOLDER"
docstring control        (blanked instrument): IDENTICAL   # first '"""' -> '"""ZZZ' - blinded by design
docstring control        (plain instrument)  : DIFFERS     # same mutation, seen
```

Each substitution is `assert`ed to have matched something before it is used, so a control that
silently matched nothing cannot masquerade as a pass. `git status --short` for the four files after
the controls still reports exactly four ` M` rows — no mutation left behind.

### Failability proofs

None; this pass introduced no new boundary. It rewrites citation text inside four docstrings and
adds no guard, gate, rejection path, or validation branch (`BUILD.md`
`### What needs a proof, and what does not`; the build plan's `#### Partition correction` states
"No failability proof is owed").

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- **`Edge cases #"..."` is the house form, not an invention.** `AGENTS.md` rule 27 gives
  `path #"unique substring"`; the dominant in-repo spelling for a spec section is
  `spec-NNN <Section> #"substring"` (`consumers.py #"spec-046 Edge cases"`,
  `routers.py #"spec-046 Edge cases"`, `filters/factories.py #"spec-027 Non-goals"`). The four new
  citations follow it, keeping the `Decision N` component ahead of the section so the contract
  pointer stays first.
- **Anchors chosen from each bullet's own bolded heading**, not its body, so a reader who greps the
  anchor lands on the bullet's first line rather than mid-paragraph. Backtick-bearing runs were
  avoided: an anchor containing a markdown code span reads badly inside an RST-flavoured docstring
  that already uses ``double backticks``.
- **`test_resolvers.py`'s sentence was restructured by one clause** rather than left as
  `... - spec-035 Decision 5 / Edge cases #"can defer the FK column (both").` The outer parenthesis
  now closes after `two shapes)`, so the anchor's closing `"` is not immediately followed by a `)`
  that belongs to a different construct. No word of the surrounding explanation was added, removed,
  or reordered.
- **No `Decision N` component was dropped anywhere.** Two sites already carried `Decision 4` inside
  the same parenthetical (kept); the `test_resolvers.py` site carried its `Decision 5` only in the
  docstring's opening line, and the rewrite now names `Decision 5` in the citation too — a strict
  addition.

### Notes for Worker 3

- **Instrument change is the thing to re-derive first.** Three of the four citations turned out to
  live in docstrings, not comments, so this pass's identity claim rests on **docstring-blanked** AST
  equality plus an explicit enumeration of which docstrings differ — not on the plain `ast.dump`
  equality pass 1 used. The scripts are at
  `.../scratchpad/proof_pass2.py` and `.../controls_pass2.py` under this session's scratchpad; both
  read `git show HEAD:<path>` copies only and write nothing. Re-run them and check afterwards that
  `git status --short` for the four files still shows four ` M` rows.
- **The binding, not the anchor spelling, is the review's load-bearing invariant.** A citation that
  resolves cleanly to the wrong bullet is worse than the stale line number it replaced. The mapping
  table above is the claim to check: read each bullet in the spec's current
  `## Edge cases and constraints` and confirm it is the one the docstring is describing. The
  `test_resolvers.py` case is self-confirming — its target bullet names that exact test as its pin.
- **`tests/optimizer/test_extension.py` is in this pass's writable list but deliberately unedited.**
  Its `Decision 7 line 346` (x2) and `line 347` citations name other specs and are cataloged against
  another card. Leaving them is the instruction, not an oversight; the population sweep Worker 0
  specified does not match them.
- **Population is zero now.** `grep -rnoE "edge case[s]? (line )?[0-9]+" --include='*.py' .` returns
  nothing tree-wide. If it returns anything on your re-run, that is new work by a concurrent session,
  not this pass.

### Notes for Worker 1 (spec reconciliation)

**No plan-vs-implementation drift, and no architectural call was made.** One dispatch-vs-reality
correction, recorded because it changed a proof instrument rather than the fix: the dispatch
described three of the four citations as living in comments and one in a docstring; all four are in
docstrings. The fix itself is unchanged by that; only the identity instrument is (see
`### Identity proof — which instrument, per file, and why`).

**No spec amendment is owed by this pass.** The four citations now point at spec text by content, so
no spec sentence became false; the spec was neither read for line numbers nor edited. Pass 1's
single recommended amendment (the staged-anchor paragraph in `## Implementation plan`) stands
unchanged and is still Slice 3's.

**One item for the `### Deferred work catalog` in `docs/builder/bld-035-final.md`** (Worker 1 is its
only author), added to the two pass 1 recorded:

3. **The same defect class survives in six citations this cycle may not fix.**
   `tests/optimizer/test_extension.py` carries `Decision 7 line 346` twice and `Decision 7 line 347`
   once, and `tests/mutations/test_sets.py` carries three more raw spec line-number citations. All
   six name **other** specs, so they belong to those cards, not to spec-035 — Worker 0 cataloged
   them at dispatch and this pass deliberately left them. Worth carrying forward as a single
   rule-27 sweep item: the population instrument that finds them is an anchor measurement over the
   citation grammar (`grep -rnE '(Decision [0-9]+|edge case[s]?)( line)? [0-9]+' --include='*.py' .`),
   not any one slice's token, and nothing in CI gates the form today.

---

## Review (Worker 3, pass 2)

Re-review of the apply-changes pass. Every number below was re-measured this pass against the working
tree; nothing is carried from Worker 2's pass-2 build report, and nothing is carried from my own pass-1
section. Cumulative cohort diff read at
`git diff -- django_strawberry_framework/optimizer/walker.py tests/optimizer/test_walker.py tests/optimizer/test_extension.py tests/types/test_resolvers.py`:
**35 added lines, 15 removed** across both passes, of which 6 additions are docstring prose and the rest
`#` comment lines. Longest added line **78** characters; non-ASCII bytes in added lines **0**; process
vocabulary (`slice` / `worker` / `revision` / `review round`) in added lines **0**.

### 1. Each of the four anchors resolves, and resolves to the right bullet

Re-derived, not accepted. `grep -oF '<anchor>' docs/SPECS/spec-035-optimizer_hardening-0_0_10.md | wc -l`
against the working-tree spec, occurrences counted (not matching lines):

```
every projection writer checks the gate         1   -> spec :271
subscription operations are gated identically   1   -> spec :273
defaults to enabled                             1   -> spec :277
can defer the FK column (both                   1   -> spec :272
```

Each bullet read in full and matched against the code it is cited from — the load-bearing half, since a
citation that resolves uniquely to the **wrong** bullet is worse than the stale number it replaced:

| Citing site | Bullet landed on | Right bullet? |
|---|---|---|
| `walker.py::_record_relation_access` (docstring: the FK-connector-column append is gated, the `planned_resolver_keys` append is not) | `**G2 — every projection writer checks the gate, not just scalar appends.**` — names `_record_relation_access` explicitly as the FK-connector-column writer | **yes** |
| `test_walker.py::test_subscription_operation_gated` | `**G2 — subscription operations are gated identically.**` | **yes** |
| `test_walker.py::test_enable_only_defaults_enabled_without_info` | `**G2 — a missing \`info\` *or* \`info.operation\` defaults to enabled.**` — the three-arm truth table the test drives | **yes** |
| `test_resolvers.py::test_fk_id_elision_falls_back_when_consumer_only_defers_fk` | `**G2 / Decision 5 — consumer-provided \`.only(...)\` can defer the FK column (both \`QUERY\` and non-\`QUERY\`).**` — that bullet names this exact test as its pin | **yes** (self-confirming) |

**The `(both` suffix re-derived rather than accepted.** `grep -oF 'can defer the FK column'` returns **3**
occurrences (`:22` the glossary-reference bullet, `:50` the Slice-2 checklist sub-bullet, `:272` the edge
case). `can defer the FK column (both` returns **1**. The suffix is necessary and sufficient, and it is
the shortest disambiguating extension — confirmed, not taken on the build report's word.

Every anchor is written whole on one line in its docstring, so a future sweep can see it.

### 2. Population: NOT empty. A fifth in-scope site was missed — see the Medium finding

Worker 0's instrument re-run by me returns nothing:

```shell
$ grep -rnoE "edge case[s]? (line )?[0-9]+" --include='*.py' .
(no output)        # exit 1
```

That measurement is real and it is not the population. Sweeping a **different** vocabulary the slice's own
token cannot reach — a whitespace-normalized scan of every `*.py` file for `\blines?\s+\d+`, which sees a
citation **wrapped across two source lines** that any line-oriented grep cannot — returns **25**
occurrences, and one of them is a live `spec-035` citation inside this cohort's own file:

```
tests/optimizer/test_walker.py:4849   ... still present (spec-035 Decision 4 / edge case
tests/optimizer/test_walker.py:4850       line 315).
```

Graded below. The other 24 are accounted for: 4 in `tests/mutations/test_sets.py` (spec-036), 4 in
`tests/optimizer/test_extension.py` (spec-033 — three `Decision 7 line 346/347` plus a fourth Worker 0's
catalog does not name, see `### Notes for Worker 1`), 2 cookbook citations in `tests/orders/`, and 14
source-line navigation comments in `tests/test_exceptions.py` / `tests/types/test_resolvers.py` /
`tests/test_export_dry_review.py` / `scripts/check_trailing_commas.py` that cite no document.

Anchor sweep for the pass-1 work, also re-derived with my own vocabulary: `TODO(spec-035` across `*.py`
-> **1** (`examples/fakeshop/test_query/test_library_api.py:3680`, baseline-dirty, recorded deferral);
`TODO(BACKLOG` -> **5**. Unchanged by pass 2, as claimed.

### 3. Instrument switch: audited, and the weaker instrument is sufficient — as stated

Re-derived independently. Pristine `HEAD` obtained read-only via `git show HEAD:<path>` into
`/private/tmp/claude-501/-Users-riordenweber-projects-django-strawberry-framework/f4b7d889-6e73-477e-b5c0-30ac0e17a204/scratchpad/w3-035-s2-pass2/head/`
(outside the repository). No `git stash` / `checkout` / `restore` / `worktree` at any point. My own
script, not Worker 2's: plain `ast.dump` equality, docstring-blanked `ast.dump` equality, **and** an
independent qualname->docstring map difference so "which docstrings changed" is measured by direct string
comparison rather than inferred from the blanked dump:

```
PLAIN-DIFFERS    BLANKED-IDENTICAL  docstrings changed: ['_record_relation_access']                                  <- django_strawberry_framework/optimizer/walker.py
PLAIN-DIFFERS    BLANKED-IDENTICAL  docstrings changed: ['test_enable_only_defaults_enabled_without_info',
                                                         'test_subscription_operation_gated']                        <- tests/optimizer/test_walker.py
PLAIN-IDENTICAL  BLANKED-IDENTICAL  docstrings changed: none                                                         <- tests/optimizer/test_extension.py
PLAIN-DIFFERS    BLANKED-IDENTICAL  docstrings changed: ['test_fk_id_elision_falls_back_when_consumer_only_defers_fk'] <- tests/types/test_resolvers.py
ALL BLANKED-IDENTICAL                                                                                                 # exit 0
```

**Exactly four docstrings differ, one per citation site, no fifth** — which is the condition that makes
the weaker instrument sufficient. Blanked equality proves everything-but-docstrings identical; the
enumeration closes the one hole blanking opens. `tests/optimizer/test_extension.py` still satisfies the
stronger plain equality, confirming pass 1's comment-only claim for that file survives pass 2.

**Negative controls re-run, mine, in memory only** — each substitution `assert`ed to have matched
something first, so a control that matched nothing cannot masquerade as a pass:

```
executable-token (return None -> return ())      blanked=DIFFERS    plain=DIFFERS
comment-only (anchor token -> PLACEHOLDER)       blanked=IDENTICAL  plain=DIFFERS
docstring (first '"""' -> '"""ZZZ')              blanked=IDENTICAL  plain=DIFFERS
```

The blanked instrument reports `DIFFERS` on an executable-token perturbation, so it can fail; it is
blinded to a docstring edit by design, as the build report says; and the plain instrument **can** see a
docstring edit, which is what makes the four-docstring enumeration a measurement rather than an
assertion. (`comment-only plain=DIFFERS` is expected and not a control failure: `walker.py`'s working tree
already differs from `HEAD` in a docstring, so the plain comparison differs whatever the comment does.)
`git status --short` for the four files after the controls still reports exactly four ` M` rows — no
mutation left behind.

**The instrument switch was stated openly rather than performed silently.** That is the behaviour this
seat exists to reward, and I am recording that it was done correctly.

### 4. No executable line changed; no boundary rode along

Blanked AST identity against `HEAD` on all four files is the direct proof: no statement, expression,
branch, or signature differs. The 6 non-`#` added lines are enumerated above and are all docstring prose.
No guard, gate, cap, rejection path, or validation branch appears in the diff. **No failability proof is
owed and its absence is not graded as a gap** (`BUILD.md` `### What needs a proof, and what does not`;
the plan's `### No failability proof is owed`). Hot-path and floor-verification are `none` per the build
plan's declarations, correctly — nothing runs differently on any path.

### 5. Dispatched findings checklist walk — both passes' boxes

All ten boxes are ticked; every tick was checked against the diff, and none is an over-tick.

Pass 1 (five boxes) — re-confirmed against the cumulative diff, unchanged by pass 2: both `walker.py`
anchor heads retargeted with the `spec-035 Decision 6` / `Decision 7` pointers and R1 (and R2 at
`_selected_scalar_names`); both test anchors retargeted with ` Slice 3` dropped and the placement
judgement preserved verbatim at `test_extension.py`; identity proof recorded. **All landed.**

Pass 2 (five boxes):

1. `walker.py::_record_relation_access` — `(Decision 4 / edge case line 315)` -> `(Decision 4 / Edge cases #"every projection writer checks the gate")`, `Decision 4` kept. **Landed.**
2. `test_walker.py::test_subscription_operation_gated` — anchor written, `Decision 4` kept. **Landed.**
3. `test_walker.py::test_enable_only_defaults_enabled_without_info` — anchor written, `Decision 4` kept, following sentence rewrapped by one word. **Landed.**
4. `test_resolvers.py::test_fk_id_elision_falls_back_when_consumer_only_defers_fk` — anchor written, `Decision 5` now rides the citation as well as the docstring's opening label (a strict addition). **Landed.**
5. Identity re-proved under the docstring-blanked instrument with negative controls — recorded, and re-derived by me above rather than accepted. **Landed.**

No box is unaddressed and nothing was deferred without a record. The Medium below is **not** a checklist
box — it is a site the checklist's own population under-derived.

### 6. Worker 0's mid-flight instruction is mirrored into the artifact

Confirmed on disk, not in a transcript. `## Build report (Worker 2, pass 2)` opens with the mirror bullet
citing `worker-0.md` `### Mid-flight instructions are mirrored into the artifact`, and it carries all
three components: **resolution path 1 chosen** (fix in-loop, not catalog), `tests/types/test_resolvers.py`
**folded into Slice 2's ownership partition**, and the `BUILD.md` `### Test staleness a focused run
cannot see` in-loop rationale with the 542 -> 498 shrink as the reason this cycle owns the breakage. The
build plan carries the matching `#### Partition correction (Worker 0, mid-flight after Slice 2's first
review pass)` subsection with the four-row population table. Both halves present; nothing lives only in
the dispatch.

### 7. The pass-1 spec amendment still stands on disk, and so does the omission I added

Re-read on disk this pass. Worker 2's pass-1 `### Notes for Worker 1 (spec reconciliation)` still carries
the three-part amendment (where it lives, current wording quoted, recommended replacement, why) for the
`## Implementation plan` staged-anchor paragraph, and pass 2's notes explicitly say it "stands unchanged
and is still Slice 3's" — correct, pass 2 owed no amendment of its own. My pass-1 omission note (the
sentence **preceding** the replaced one also describes the anchors as `TODO(spec-035 Slice N)`) is still
present under my pass-1 `### Notes for Worker 1`. Both target sentences are still un-amended in the spec
(`docs/SPECS/spec-035-optimizer_hardening-0_0_10.md:263` carries both), which is correct — no worker in
this slice may edit the spec. Nothing further to add under that heading beyond what is recorded below.

### 8. Gates re-run by me, not read

- `uv run ruff format --check .` -> `435 files already formatted`
- `uv run ruff check .` -> `All checks passed!`
- `uv run python scripts/check_trailing_commas.py --check` on the four cohort files (population echoed as
  `4` before the run, so the invocation cannot silently have run on one joined path) -> exit 0
- `uv run pytest tests/optimizer/test_walker.py tests/optimizer/test_extension.py tests/types/test_resolvers.py --no-cov -q`
  -> **399 passed in 8.99s**, matching the build report exactly. No `--cov*` flag on any invocation.

Both repo-wide lint gates are green tree-wide, so no attribution question arises for the concurrent
sessions' dirty files.

### 9. Static inspection helper

Required (the slice touches an existing `.py` file under `django_strawberry_framework/optimizer/`), run
this pass:

```shell
uv run python scripts/review_inspect.py django_strawberry_framework/optimizer/walker.py --output-dir docs/shadow
```

Fresh output: 24 imports, 37 symbols, 8 control-flow hotspots, 7 repeated string literals, **2 TODO
comments** (`walker.py:467`, `walker.py:1137` — both this slice's retargeted anchors, independently
confirming `walker.py` holds no third anchor). No skip to record. The ORM-marker and repeated-literal
populations sit entirely on executable lines, and this diff adds no executable line (blanked AST identity
above), so none is inside the diff and none yields a finding. Cited by symbol / original-source line only;
no shadow line number appears in this review.

### High:

None.

### Medium:

#### The re-derived population missed a fifth in-scope spec-035 line citation, in a cohort file, because the citation is wrapped across two lines

`tests/optimizer/test_walker.py:4849-4850`, in
`tests/optimizer/test_walker.py::test_mutation_scalar_only_connection_window_no_only`:

```tests/optimizer/test_walker.py:4849:4850
    and the prefetch itself are still present (spec-035 Decision 4 / edge case
    line 315).
```

This is the same defect the apply-changes pass was dispatched to eliminate: a shipped docstring citing
spec-035 by raw line number (`AGENTS.md` rule 27), in a file **already inside** Slice 2's ownership
partition, unchanged at `HEAD` and unchanged by either pass (my docstring enumeration lists only
`test_subscription_operation_gated` and `test_enable_only_defaults_enabled_without_info` as changed in
that file, so this docstring is provably untouched).

**Why it matters, measured.** `line 315` is wrong twice over. At `HEAD` the spec's line 315 was the
`**G1 — async path inherits the guard.**` bullet — an unrelated G1 bullet, so the citation was already
pointing at the wrong text before this cycle; the bullet it describes sat at `HEAD`:316. In the working
tree, after Slice 1 shrank the spec 542 -> 498 lines, line 315 is a Slice-2 **test-plan** bullet
(`test_query_and_mutation_plans_coexist_distinct_keys`) and the bullet it describes is at 271. A reader
following this citation lands on unrelated text today, and landed on unrelated text yesterday.

**Why it escaped.** Worker 0's instrument and Worker 2's post-edit sweep are both
`grep -rnoE "edge case[s]? (line )?[0-9]+"`, which is line-oriented. Here `edge case` ends line 4849 and
`line 315)` opens line 4850, so the citation is invisible to it — the exact hazard Worker 2's own
`### How each citation was bound to its bullet` names ("a citation wrapped across two lines is invisible
to the sweep that would catch its regression") when choosing how to *write* the new anchors, but did not
apply to *measuring* the population. Consequently the build report's stated count is false:
`### Notes for Worker 3` says "**Population is zero now** ... returns nothing tree-wide", and
`### How each citation was bound to its bullet` says "**Zero occurrences tree-wide**". Both are wrong.
`BUILD.md` `## Claims are proven mechanically, never accepted on prose` grades a stated count of this
shape a Medium, and names this failure mode exactly: a grep phrase samples a claim's vocabulary rather
than establishing its population.

**Recommended change.** Replace the citation with the anchor form, bound by content like the other four.
The target bullet is the same one `walker.py::_record_relation_access` now cites — spec `:271`,
`**G2 — every projection writer checks the gate, not just scalar appends.**`, which names
`_project_scalar_only_window` calling `.only(...)` directly as the writer this test gates. So:

```
    and the prefetch itself are still present (spec-035 Decision 4 / Edge cases
    #"every projection writer checks the gate").
```

written **whole on one line** where the wrap allows, and `Decision 4` kept, exactly as the other four
were done. `grep -oF 'every projection writer checks the gate' <spec> | wc -l` -> 1, verified above; a
second citing site does not affect the anchor's uniqueness in the spec. No behavior is affected, so no
test expectation changes; re-run the same four-file scope and the identity proof, and the docstring
enumeration should then list **five** changed docstrings, still one per citation site.

**Re-measure the population with an instrument that can see a wrap**, not with the line-oriented grep
that produced the false zero — e.g. normalize whitespace per file before matching, or match
`(edge case[s]?|Decision [0-9]+|spec)\s+(line\s+)?[0-9]+` against the joined text. The line-oriented form
is fail-open here in the literal sense: it prints a clean pass.

`tests/types/test_resolvers.py` needs no further partition change — the site is in `test_walker.py`,
already owned.

### Low:

None. (Pass 1's Low is closed at four of its five real sites; the fifth is the Medium above, regraded
because the pass additionally asserts a population that does not hold.)

### DRY findings

- **Examined and rejected: the four `Edge cases #"..."` citations are not a consolidation target.** They
  are contract pointers, one per citing symbol, each naming a different bullet. There is no shared
  mechanism to home; the thing that could drift — the bullet text — has exactly one home, the spec, which
  is the point of the anchor form.
- **Examined and rejected: `Decision 4` appearing in three of the four citations is not a repeated
  literal in the DRY sense.** It is the contract identifier the three sites genuinely share (they all
  document one Decision), and dropping it to "avoid repetition" would strip the pointer rule 27 exists to
  preserve. Two sites already carried it; the `test_resolvers.py` site gained `Decision 5` — a strict
  addition, correctly done.
- **No new helper, constant, indirection, or abstraction is introduced** by either pass — blanked AST
  identity proves no executable line exists to extract. Nothing to challenge on existence grounds beyond
  the anchors themselves, which I challenged and upheld in pass 1 (both legs re-verified there) and which
  pass 2 did not touch.
- Cross-cohort duplication review: not applicable; the build plan declares `ownership partition: none;
  sequential slices`, and the mid-flight correction folded a file into the one cohort rather than
  creating a second.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **not** empty, and the change is **not this
slice's**:

```
-__version__ = "0.0.14"
+__version__ = "0.0.15"
```

`__all__` and the re-export list are **unchanged**; the single changed line is the `__version__` literal.
That file appears in no cohort of the build plan's `## Declarations` ownership table (the mid-flight
correction added `tests/types/test_resolvers.py`, not this), so it is a concurrent session's release-line
bump under `AGENTS.md` rule 34 — never edit, never revert. Slice 2 adds no public export, consistent with
spec Decision 9's "this card adds no public symbol".

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. The spec, its `-rationale.md`
and its `-terms.csv` were correctly left untouched by both passes; this artifact and `docs/shadow/` are
per-cycle scratchpads, not doc surfaces.

### What looks solid

- **The four bindings are right, and they are right for the reason that is hard to get right.** Each
  anchor resolves once *and* lands on the bullet the citing symbol is actually about — including the
  `test_resolvers.py` case, where the target bullet names that exact test as its pin, so the binding is
  self-confirming. Binding by content rather than by counting lines is what makes them regression-proof
  in a way the numbers never were.
- **The instrument downgrade was declared, not slipped.** Pass 2 could have reported plain `ast.dump`
  equality for one file and stayed quiet about the other three; instead it says which instrument covers
  which file and why, and supplies the docstring enumeration that closes the hole blanking opens. That
  enumeration is what makes the weaker instrument sufficient rather than merely weaker, and it reproduces
  exactly under my own independent script.
- **The `(both` suffix was justified with a measurement, and the measurement holds.** Three occurrences
  of the bare phrase, one with the suffix — re-derived here. Reaching for the shortest disambiguating
  extension rather than a longer quotation is the right instinct: a long quotation is what breaks on
  reflow.
- **`tests/optimizer/test_extension.py` was in the writable list and deliberately left alone**, with the
  reason recorded (its citations name spec-033, another card's). Restraint inside a writable partition,
  said out loud.
- **The pass-1 work was not disturbed.** All five pass-1 boxes still hold against the cumulative diff,
  the anchor sweep is unchanged at 1/5, and `test_extension.py` still satisfies the stronger plain-AST
  equality — so pass 2 is provably additive.

### Temp test verification

- No temp test was written, and none is appropriate: the change set is provably comment-and-docstring
  only, so there is no behavior a temp test could demonstrate, and a test asserting docstring prose would
  pin a citation's spelling rather than a contract. `docs/builder/temp-tests/` stays empty (measured: 0
  entries).
- The verification scripts I ran this pass live **outside the repository**, under
  `/private/tmp/claude-501/-Users-riordenweber-projects-django-strawberry-framework/f4b7d889-6e73-477e-b5c0-30ac0e17a204/scratchpad/w3-035-s2-pass2/`
  (`proof_w3.py`, `controls_w3.py`, `head/`) plus a whitespace-normalizing population sweep in the same
  scratchpad. None writes into the tree.
- Disposition: nothing to promote.

### Notes for Worker 1 (spec reconciliation)

**No spec amendment is owed by this pass, and pass 1's stands.** The four citations point at spec text by
content, so no spec sentence became false. Pass 1's single recommended amendment (the `## Implementation
plan` staged-anchor paragraph) and my pass-1 addition to it (the *preceding* sentence, which still
describes the anchors as `TODO(spec-035 Slice N)` in the present tense) are both on disk under the
respective `### Notes for Worker 1` sections and remain Slice 3's. Nothing further to add there.

**Catalog corrections — the out-of-scope population is larger than recorded, and its proposed instrument
cannot find all of it.** Worker 2's deferred-catalog item 3 names six other-spec citations
(`test_extension.py` x3, `test_sets.py` x3) and proposes
`grep -rnE '(Decision [0-9]+|edge case[s]?)( line)? [0-9]+' --include='*.py' .` as the sweep instrument.
Both need correcting before the catalog item is written:

- There is a **seventh**: `tests/optimizer/test_extension.py:2248-2249` reads
  `... so the plan is cacheable (spec line` / `350: the visibility-bearing library shape ...)`. It names
  **no** spec at all (context puts it on spec-033, per the `spec-033` header comment above it), and it is
  *also* wrapped across two lines. So it is invisible to the proposed instrument on two independent
  counts — the grammar and the wrap.
- The proposed instrument would therefore under-report the very population the catalog item exists to
  size. Recommend the catalog record a **wrap-aware** sweep (normalize whitespace per file, then match
  `(spec[- ][0-9]*|Decision [0-9]+|[Ee]dge cases?)[^.]{0,60}?\blines?\s+[0-9]+`), and note that the
  cookbook-line citations in `tests/orders/test_sets.py:169` and `tests/orders/test_factories.py:251` are
  the same defect class against a non-spec document.
- Also worth a line in the catalog now that `tests/types/test_resolvers.py` is in a cohort:
  `tests/types/test_resolvers.py:1797,1802,1808,1817,1828,1908,1915,1920,1931` carry bare `(line NNN)`
  coverage-arm comments citing line numbers **of `types/resolvers.py` itself**. They name no document and
  no spec, they pre-date this cycle, and nothing this cycle did falsified them — so they are not this
  slice's and I am not grading them — but they are the same rot shape and rule 27's `path::Symbol` form
  is what they should carry.

**Non-blocking observation, deliberately not filed as a finding.** Of the four anchors, `#"defaults to
enabled"` is the least distinctive — four common words with no `G2` / `info` token — so it is the one
most exposed if the spec grows a second sentence using that phrasing. It resolves uniquely today
(measured), which is what rule 27 requires, so there is no defect; if a hardening pass ever touches that
docstring, `#"info.operation` defaults to enabled"` or similar would be sturdier. Recording it so the
observation is not lost, not asking for a change.

**The two carry-forward items from pass 1 stand**, both re-verified this pass: (1)
`examples/fakeshop/test_query/test_library_api.py:3680` is still the sole `TODO(spec-035` occurrence in
any `.py` file, baseline-dirty and out of scope, and is the one anchor that makes the integration pass's
step-6 sweep non-empty; (2) the two package test-tree anchors become deletable if and only if the spec's
G3 deferred test plan ever records their file placement. My pass-1 item (3) — `selections.py`'s reference
anchor is the only one of five whose body cites no `spec-035 Decision N` — also stands unchanged.

### Review outcome

`revision-needed`.

The four dispatched citation fixes are correct in substance and correct in binding — each resolves
exactly once and lands on the bullet its symbol is about, re-derived here rather than accepted — and the
instrument switch is both honestly declared and sufficient, which I confirmed with my own script and
controls. What blocks acceptance is not those four: it is that the population they were drawn from was
established with a line-oriented grep against a citation that wraps across two lines, so a **fifth**
spec-035 raw line citation survives untouched in `tests/optimizer/test_walker.py` — a file this cohort
already owns — while the build report states the population is zero tree-wide. One more comment-only pass
closes it: retarget `test_mutation_scalar_only_connection_window_no_only`'s citation to the
`#"every projection writer checks the gate"` bullet it is actually about, and re-derive the population
with an instrument that can see a wrapped citation.

---

## Build report (Worker 2, pass 3)

Apply-changes pass for the Worker 3 pass-2 Medium finding **The re-derived population missed a
fifth in-scope spec-035 line citation, in a cohort file, because the citation is wrapped across
two lines**. Nothing from pass 1 or pass 2 is withdrawn: the four retargeted carry-forward
anchors and the four retargeted citations stand exactly as they landed. This pass adds the fifth
citation fix and replaces pass 2's population instrument with a wrap-aware one.

### Files touched

Grounded in `git status --short` after both ruff invocations (quoted under `### Validation run`).

- `tests/optimizer/test_walker.py` — one docstring.
  `test_mutation_scalar_only_connection_window_no_only`:
  `(spec-035 Decision 4 / edge case` / `line 315).` ->
  `(spec-035 Decision 4 / Edge cases` / `#"every projection writer checks the gate").`
  `Decision 4` kept; the `#"..."` anchor sits whole on one source line so it cannot itself become
  wrap-invisible. The wrap point moved from *inside* the citation to *between* its
  `Decision N / Section` half and its `#"substring"` half, which is the same shape the already-
  accepted `walker.py::_record_relation_access` site carries.
- `docs/builder/bld-035-slice-2-carry_forward_anchors.md` — this build report; `Status: built`;
  one new `### Dispatched findings checklist` box added and ticked.
- `docs/builder/worker-memory/worker-2.md` — memory entry appended.

**Not touched:** `django_strawberry_framework/optimizer/walker.py`,
`tests/optimizer/test_extension.py`, `tests/types/test_resolvers.py` (all three done and accepted
in prior passes); `django_strawberry_framework/optimizer/selections.py`; the spec, its
`-rationale.md` and `-terms.csv`; every baseline-dirty out-of-scope file, including
`tests/rest_framework/test_resolvers.py` and `examples/fakeshop/test_query/test_library_api.py`.
No other `.py` file in the tree was written this pass.

### How the fifth citation was bound to its bullet

By **content**, read out of the spec's current `## Edge cases and constraints` section. The test
asserts that a scalar-only nested connection window **under a mutation** applies no `.only(...)`
while the window annotation and the prefetch survive. The bullet at spec `:271` reads, in the
part that governs:

> **G2 — every projection writer checks the gate, not just scalar appends.** ... and
> [`_project_scalar_only_window`][walker] calls `.only(...)` directly (never touching
> `only_fields`). Under a non-`QUERY` operation the `enable_only` gate is consulted in all four
> projection writers ... so no FK / prefetch connector column is appended and no scalar-window
> `.only(...)` is applied — a relation-selecting mutation and a scalar-only nested connection
> window both end with no column deferral on the *applied* queryset.

The docstring's own first line names `_project_scalar_only_window` as "the direct `.only(...)`
writer that never touches `OptimizationPlan.only_fields`" — the same clause, the same writer, and
the bullet's closing sentence names this test's exact scenario ("a scalar-only nested connection
window"). Confirmed the right bullet, not merely a resolving one.

Anchor uniqueness verified **before** the citation was written, occurrences (not matching lines)
counted against the working-tree spec:

```shell
$ S=docs/SPECS/spec-035-optimizer_hardening-0_0_10.md
$ grep -oF 'every projection writer checks the gate' $S | wc -l
       1
$ grep -n 'every projection writer checks the gate' $S | cut -c1-60
271:- **G2 — every projection writer checks the gate, not jus
```

This is the second citing site for that one bullet (`walker.py::_record_relation_access` is the
first). Two citers do not affect the anchor's uniqueness *in the spec*, which is what rule 27
requires, and the bullet genuinely governs both writers — it is the bullet that says *all four*
projection writers consult the gate.

Final docstring as it now reads:

```tests/optimizer/test_walker.py:4843:4851
def test_mutation_scalar_only_connection_window_no_only():
    """A scalar-only connection window under a mutation applies no ``.only(...)``.

    Gates ``_project_scalar_only_window`` (the direct ``.only(...)`` writer that
    never touches ``OptimizationPlan.only_fields``): the windowed ``Prefetch``
    child carries Django's default empty defer-set while the window annotations
    and the prefetch itself are still present (spec-035 Decision 4 / Edge cases
    #"every projection writer checks the gate").
    """
```

### Population re-measured with a wrap-aware instrument — occurrence list, not a count

**Correction to pass 2's stated count (this pass supersedes it).** `## Build report (Worker 2,
pass 2)` states, under `### How each citation was bound to its bullet`, "**Zero occurrences
tree-wide**", and under `### Notes for Worker 3`, "**Population is zero now.**". Both were
measured with `grep -rnoE "edge case[s]? (line )?[0-9]+" --include='*.py' .`, which is
**line-oriented** and therefore cannot see a citation whose `edge case` and `line 315` sit on two
different source lines. That is exactly the shape `BUILD.md` `## Claims are proven mechanically,
never accepted on prose` grades Medium — "a long grep phrase samples a claim's vocabulary rather
than establishing its population" — and pass 2's own `### How each citation was bound to its
bullet` names the wrap hazard for *writing* an anchor without applying it to *measuring* the
population. **Those two sentences are superseded by the occurrence list below.** Pass 2's text is
left as written (prior sections are never edited); this bullet is the correction of record.

Instrument used this pass — whitespace flattened per file **before** matching, so a wrapped
citation is one contiguous match:

```python
import re, pathlib
pat = re.compile(r"(edge case[s]?|spec|Decision|item|bullet)[^\n]{0,60}?line\s*/?\s*[0-9]+", re.I)
root = pathlib.Path("/Users/riordenweber/projects/django-strawberry-framework")
files = sorted(root.rglob("*.py"))
print("population of files scanned:", len(files))
for p in files:
    if ".venv" in p.parts or ".git" in p.parts:
        continue
    flat = re.sub(r"\s+", " ", p.read_text(errors="replace"))
    for m in pat.finditer(flat):
        print(p.relative_to(root), "|", m.group(0)[:90])
```

Result **after** this pass's edit — the full occurrence list, so the count is `len()` of the rows
and re-derivable rather than asserted (`BUILD.md` `### What gets recorded`):

```
population of files scanned: 4826      # pre-filter; 569 after dropping .venv/ and .git/
tests/mutations/test_sets.py       | spec-036 Decision 6 line 334
tests/mutations/test_sets.py       | ItemInput`` as an un-narrowed create (spec-036 Edge cases line 509
tests/mutations/test_sets.py       | spec-036 Decision 6 line 334
tests/mutations/test_sets.py       | Edge cases line 509
tests/optimizer/test_extension.py  | Decision 7 line 346
tests/optimizer/test_extension.py  | Decision 7 line 346
tests/optimizer/test_extension.py  | Decision 7 line 347
tests/optimizer/test_extension.py  | spec line 350
tests/types/test_resolvers.py      | Item) # Scoped (line 556
occurrences: 9
```

**In-scope (spec-035) population: EMPTY.** No row names `spec-035`. Confirmed by a second,
spec-035-specific wrap-aware sweep over the same 569 post-filter files:

```
spec-035 line citations: 0
edge-case/Decision-N line citations: 7
```

(the `spec-035[^\n]{0,80}?line\s*[0-9]+` pattern returns nothing; the second number is the
`(edge case[s]?|Decision [0-9]+)...\blines?\s+[0-9]+` grammar, which by construction misses the
`spec line 350` row that names no spec and no Decision.)

**Out-of-scope population: EIGHT spec-referencing occurrences, not seven** — and this pass does
not touch any of them. Reconciling the list against the two counts on record:

- `tests/mutations/test_sets.py` — **four** occurrences on three source lines (spec-036):
  `:1034` `spec-036 Decision 6 line 334`, `:1039` `spec-036 Edge cases line 509`, and `:1073`
  which carries **two** (`spec-036 Decision 6 line 334` *and* `Edge cases line` wrapping onto
  `:1074` as `509`). The build plan's `#### Partition correction` records "three in
  `tests/mutations/test_sets.py`" — that is three *source lines*, and the fourth occurrence is
  precisely the wrapped one, so the same wrap hazard under-reported this file too.
- `tests/optimizer/test_extension.py` — **four** occurrences: `Decision 7 line 346` twice,
  `Decision 7 line 347` once, and `spec line 350` (which wraps and names no spec), matching
  Worker 3's pass-2 `### Notes for Worker 1` correction that there is a seventh.
- Total spec-referencing out-of-scope occurrences: 4 + 4 = **8**. The dispatch's expected "seven"
  and the build plan's "re-derived wrap-aware: **seven**" both stand one short of the measured
  list, for the same reason pass 2's zero did: `test_sets.py:1073`'s second citation wraps. Not
  fixed here — different card, and the correction is routed under
  `### Notes for Worker 1 (spec reconciliation)` below.
- The ninth row, `tests/types/test_resolvers.py:1908` `# Scoped (line 556)`, is **not** a spec
  citation at all — the regex's `item` alternative matched the word `Item` in the preceding code.
  It is one of the bare `(line NNN)` coverage-arm comments citing `types/resolvers.py`'s own line
  numbers that Worker 3 already flagged as a same-shape-but-different-document class. Left alone.

### Tests added or updated

**None.** The pass changes no executable line; a test asserting docstring prose would pin the
citation's spelling rather than a contract. The substitute is the identity proof below.
`docs/builder/temp-tests/` stays empty for this slice.

### Validation run

Format and lint, write mode scoped to the single file this pass touched (`worker-2.md` step 5:
never `.` in write mode — the tree carries 64 dirty rows of concurrent work). The file list is a
**zsh array** and its size is printed, because `$F` does not word-split in zsh:

```shell
$ F=(tests/optimizer/test_walker.py)
$ echo "population: ${#F[@]}"
population: 1

$ uv run ruff format "${F[@]}"
1 file left unchanged

$ uv run ruff check --fix "${F[@]}"
All checks passed!

$ uv run python scripts/check_trailing_commas.py --check "${F[@]}"
(no output)      # exit 0
```

`AGENTS.md` rule 16's repo-wide pair, run **read-only** (the only form that does not write into
another session's files):

```shell
$ uv run ruff format --check .
435 files already formatted
$ uv run ruff check .
All checks passed!
```

`AGENTS.md` rule 17, measured on the touched file: `LC_ALL=C grep -c '[^ -~\t]'
tests/optimizer/test_walker.py` -> **0** non-ASCII lines. Longest line added across all three
passes in that file: **79** characters
(`git diff -- tests/optimizer/test_walker.py | grep -E '^\+[^+]' | awk '{print length($0)-1}' |
sort -rn | head -1`); this pass's two new lines are 78 and 48.

`git status --short` after both ruff invocations — **64** rows, of which four belong to this
cohort across all three passes:

```
 M django_strawberry_framework/optimizer/walker.py     <- passes 1-2; untouched this pass
 M tests/optimizer/test_extension.py                   <- pass 1 only; untouched this pass
 M tests/optimizer/test_walker.py                      <- passes 1-3
 M tests/types/test_resolvers.py                       <- pass 2 only; untouched this pass
```

Every other row is the pre-existing concurrent-session baseline or this cycle's own doc output.
`tests/rest_framework/test_resolvers.py` is ` M` and is **not** mine — baseline-dirty, and not to
be confused with `tests/types/test_resolvers.py`. Nothing unexpected was touched and nothing was
reverted.

Focused run — the same scope pass 2 recorded, no `--cov*` flag (`--no-cov` only):

```shell
$ uv run pytest tests/optimizer/test_walker.py tests/optimizer/test_extension.py \
    tests/types/test_resolvers.py --no-cov -q
============================= 399 passed in 8.96s ==============================
```

**399 passed**, identical to pass 2's recorded 399. A docstring edit cannot change collection or
status, and it did not.

### Identity proof — which instrument, and why

**Instrument: docstring-blanked `ast.dump` equality, plus an enumeration of which docstrings
differ.** The citation lives inside a docstring, so plain `ast.dump` equality legitimately differs
for this file and is *not* the instrument for it; the blanked variant is. Stating the instrument
per file rather than switching silently is the pass-2 discipline, carried forward. The blanked
comparison alone would be too weak on its own — it is blind to *any* docstring edit — so it is
paired with the enumeration, which turns "no docstring changed except the citation sites" into a
measurement. `tests/optimizer/test_extension.py` is unchanged since pass 1 and still satisfies the
**stronger** plain-`ast.dump` equality, reported alongside as evidence pass 1's comment-only claim
for that file still holds.

Pristine `HEAD` obtained read-only via `git show HEAD:<path>` into a scratch directory **outside
the repository** —
`/private/tmp/claude-501/-Users-riordenweber-projects-django-strawberry-framework/f4b7d889-6e73-477e-b5c0-30ac0e17a204/scratchpad/head-035-pass3/`.
No `git stash` / `checkout` / `restore` / `worktree` at any point (`BUILD.md` `## Claims are
proven mechanically, never accepted on prose`; the maintainer runs concurrent sessions on this
tree). `HEAD` is pristine of **all three** passes, so every row below covers passes 1-3 together.

```
PLAIN-DIFFERS   BLANKED-IDENTICAL  docstrings changed: ['_record_relation_access']                       django_strawberry_framework/optimizer/walker.py
PLAIN-DIFFERS   BLANKED-IDENTICAL  docstrings changed: ['test_enable_only_defaults_enabled_without_info',
                                                        'test_mutation_scalar_only_connection_window_no_only',
                                                        'test_subscription_operation_gated']             tests/optimizer/test_walker.py
PLAIN-IDENTICAL BLANKED-IDENTICAL  docstrings changed: none                                              tests/optimizer/test_extension.py
PLAIN-DIFFERS   BLANKED-IDENTICAL  docstrings changed: ['test_fk_id_elision_falls_back_when_consumer_only_defers_fk']  tests/types/test_resolvers.py
ALL BLANKED-IDENTICAL
# exit 0
```

**`tests/optimizer/test_walker.py` now lists exactly three changed docstrings — the three citation
sites in that file, and no fourth.** Cohort-wide the total is five changed docstrings, one per
citation site across all three passes. `BLANKED-IDENTICAL` on all four files is the "no executable
line changed" claim, and the three-name enumeration is the "no unrelated docstring changed" claim.

**Negative controls — three, run in memory against `HEAD` copies, nothing written to the tree.**
The blanked instrument is deliberately blind to a docstring edit, so a docstring control under it
*must* print IDENTICAL; the same mutation under the plain instrument printing DIFFERS is what
proves the docstring enumeration above is itself a measurement rather than a formality:

```
executable-token control (blanked instrument): DIFFERS     # "registry.clear()" -> "registry.clear", 1st occurrence
comment-only control     (blanked instrument): IDENTICAL   # "# The window itself is still planned" -> "# PLACEHOLDER"
docstring control        (blanked instrument): IDENTICAL   # '"""A scalar-only' -> '"""ZZZ scalar-only' - blinded by design
docstring control        (plain instrument)  : DIFFERS     # same mutation, seen
# exit 0
```

Every substitution is `assert`ed to have matched something before it is used, so a control that
silently matched nothing cannot masquerade as a pass. `git status --short` for the four cohort
files after the controls still reports exactly four ` M` rows — no mutation left behind.

Scripts, both read-only:
`.../scratchpad/proof_pass3.py`, `.../scratchpad/controls_pass3.py`,
plus the two population sweeps `.../scratchpad/pop_pass3.py` and `.../scratchpad/pop035.py`.

### Failability proofs

None; this pass introduced no new boundary. It rewrites citation text inside one docstring and
adds no guard, gate, rejection path, or validation branch (`BUILD.md` `### What needs a proof, and
what does not`; the plan's `### No failability proof is owed`, and the dispatch restates it).

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- **The wrap was moved, not eliminated.** The docstring is 4-space-indented prose inside a 99-column
  budget, so the citation cannot fit on one line. What matters is *where* the break falls: the
  `#"every projection writer checks the gate"` anchor is whole on its own line, so a future
  wrap-aware **or** line-oriented sweep for the anchor grammar sees it. Breaking between
  `Edge cases` and `#"..."` is the same shape the accepted `walker.py::_record_relation_access`
  site already carries, so the two citers of this one bullet are spelled identically.
- **Worker 3's prescribed replacement text was taken verbatim**, including the `Edge cases`
  capitalization and the `Decision 4` retention. No drift.
- **The bullet was re-read in full before the anchor was written**, not matched on its heading
  alone: the heading names "every projection writer", but it is the bullet's *body* that names
  `_project_scalar_only_window`'s direct `.only(...)` and its closing sentence that names the
  scalar-only nested connection window. Binding on the heading alone would have been a guess that
  happened to be right.
- **The population instrument was replaced, not supplemented.** The line-oriented grep is retained
  in the report only as the thing being corrected; the wrap-aware flatten is the measurement of
  record. A line-oriented sweep of a wrapping grammar prints a clean pass, which is the fail-open
  shape `BUILD.md` `### Fail-open shapes` describes applied to an instrument rather than to code.

### Notes for Worker 3

- **The correction of record is a report bullet, not an edit to pass 2.** `ARTIFACT.md`
  `## Re-pass sections` forbids editing a prior entry, so pass 2's two "population is zero"
  sentences are still on disk as written; the superseding occurrence list is under
  `### Population re-measured with a wrap-aware instrument` above, which names both sentences
  explicitly. Please confirm that shape is what you wanted rather than a rewrite.
- **Two numbers in the dispatch and the build plan do not survive measurement**, and I did not
  edit either document to match (the build plan is Worker 0's, and I may not write it): the
  out-of-scope population is **eight** spec-referencing occurrences, not seven. The extra one is a
  *second* citation on `tests/mutations/test_sets.py:1073`, wrapping onto `:1074`. Full list and
  derivation above; routed to Worker 1 below. Nothing in scope changed as a result.
- **The `#"every projection writer checks the gate"` bullet now has two citing sites.** That is
  deliberate and Worker 3's own prescription; the bullet is the one that says *all four* projection
  writers consult the gate, and `_record_relation_access` and `_project_scalar_only_window` are two
  of the four. Uniqueness is a property of the anchor's occurrences **in the spec** (1), not of the
  number of citers.
- **Re-run scope for the identity claim:** `proof_pass3.py` then `controls_pass3.py`, in that
  order (the controls import the proof module's helpers), then check `git status --short` for the
  four cohort files still shows four ` M` rows. Both read `git show HEAD:<path>` copies under
  `.../scratchpad/head-035-pass3/` and write nothing.

### Notes for Worker 1 (spec reconciliation)

**No plan-vs-implementation drift, and no architectural call was made.** The fix is the one Worker
3 prescribed, at the site Worker 3 named, bound to the bullet Worker 3 named — re-derived from the
spec's `## Edge cases and constraints` rather than accepted on the review's word.

**No spec amendment is owed by this pass.** The fifth citation now points at spec text by content,
so no spec sentence became false; the spec was neither read for line numbers nor edited. Pass 1's
single recommended amendment (the `## Implementation plan` staged-anchor paragraph) and Worker 3's
pass-1 addition to it stand unchanged and remain Slice 3's.

**Correction to the `### Deferred work catalog` item, for `docs/builder/bld-035-final.md`** (Worker
1 is its only author). This supersedes the sizing in my pass-2 item 3 and refines Worker 3's
pass-2 correction of it:

4. **The out-of-scope rule-27 line-citation population is EIGHT occurrences, not six and not
   seven** — and every count on record so far was produced by an instrument that cannot see a
   wrapped citation. Measured this pass over 569 post-filter `.py` files with the whitespace-
   flattening sweep quoted in `### Population re-measured with a wrap-aware instrument`:
   `tests/mutations/test_sets.py` carries **four** (spec-036: `:1034`, `:1039`, and **two** on
   `:1073`, the second wrapping onto `:1074`), and `tests/optimizer/test_extension.py` carries
   **four** (spec-033: `Decision 7 line 346` x2, `Decision 7 line 347`, and `spec line 350` which
   wraps *and* names no spec). The build plan's `#### Partition correction` records "three in
   `tests/mutations/test_sets.py`" and a wrap-aware total of "seven"; both are one short, for the
   same reason pass 2's "zero" was wrong. **Recommended catalog wording:** record the sweep as an
   occurrence *list* rather than a total, and specify the instrument as a per-file whitespace
   flatten before matching — `re.sub(r"\s+", " ", text)` then
   `(spec[- ][0-9]*|Decision [0-9]+|[Ee]dge cases?)[^.]{0,60}?\blines?\s+[0-9]+` — since any
   line-oriented `grep` of this grammar is fail-open and prints a clean pass. Also worth recording
   that the same sweep surfaces `tests/types/test_resolvers.py:1908`-style bare `(line NNN)`
   comments citing a source file's own lines (Worker 3's pass-2 list), which are the same rot shape
   against a different document and want `path::Symbol`.

**Amendment shape note.** Nothing above asks for a change to the spec — items 1-4 of the catalog
are all `.py` or process surfaces — so no `### Notes for Worker 1` amendment carries a spec
heading / current-wording / replacement triple this pass. Item 4's recommended wording targets the
**final artifact's** catalog section, which Worker 1 authors.

---

## Review (Worker 3, pass 3)

Third review pass. Every number below was re-measured this pass against the working tree with my own
instruments; nothing is carried from Worker 2's pass-3 build report, and nothing is carried from my own
pass-1 or pass-2 sections. Cumulative cohort diff read at
`git diff -- django_strawberry_framework/optimizer/walker.py tests/optimizer/test_walker.py tests/optimizer/test_extension.py tests/types/test_resolvers.py`:
**37 added lines, 17 removed**, of which 7 are docstring prose and 30 are `#` comment lines. Longest added
line **79** characters; non-ASCII bytes in added lines **0**; process vocabulary
(`slice` / `worker` / `revision` / `review round`) in added lines **0**.

### 1. The new anchor resolves exactly once, and it lands on the right bullet

Occurrences (not matching lines) against the working-tree spec, all five cohort anchors re-derived:

```
every projection writer checks the gate         1   -> spec :271
subscription operations are gated identically   1   -> spec :273
defaults to enabled                             1   -> spec :277
can defer the FK column (both                   1   -> spec :272
```

**The bullet was read in full, and the test body read against it** — not the docstring's account of the
test. `tests/optimizer/test_walker.py::test_mutation_scalar_only_connection_window_no_only` plans
`booksConnection(first: 3) { totalCount }` on a relay `Shelf` under `info=_op_info(OperationType.MUTATION)`,
then asserts `prefetch.queryset.query.deferred_loading == (frozenset(), True)` (Django's default empty
defer-set, i.e. no `.only(...)` applied) **and** `WINDOW_ROW_NUMBER in prefetch.queryset.query.annotations`
(window annotation and prefetch survive). Spec `:271`'s body names
`` [`_project_scalar_only_window`][walker] calls `.only(...)` directly (never touching `only_fields`) ``
and its closing sentence names this exact scenario: "a relation-selecting mutation and **a scalar-only
nested connection window** both end with no column deferral on the *applied* queryset." Right bullet.

**Two citers on one bullet: correct, and I checked the alternative.** `:271` is the only bullet in
`## Edge cases and constraints` that covers *either* writer — it is the bullet that says the gate is
consulted in *all four* projection writers, and it names `_record_relation_access` and
`_project_scalar_only_window` by symbol in the same sentence. Neither citation has a more specific home:

- `walker.py::_record_relation_access` — no other bullet mentions the FK-connector-column append at all.
- `test_mutation_scalar_only_connection_window_no_only` — the plausible alternative is `:275`
  (`**G2 — a mutation returning a DjangoConnectionField is gated by construction.**`), and it would have
  been **wrong**: that bullet is about a *root* connection field needing no separate gate site and says
  outright that "the path is covered by construction rather than a dedicated test." This test *is* a
  dedicated test, of the *nested* window writer. Binding to `:275` would have resolved uniquely to a
  bullet that denies the test exists.

Uniqueness is a property of the anchor's occurrences **in the spec** (1 each), not of the number of citing
sites, so two citers is not a defect. **No finding.**

**Anchor is whole on one source line**, mechanically: `grep -rn '#"[^"]*$'` across the four cohort files
returns nothing, so no `#"..."` anchor in the cohort opens on one line and closes on another. The five
anchors sit at `walker.py:854`, `test_walker.py:4850`, `:4897`, `:4913`, `test_resolvers.py:1036`.

**The anchored text has not moved.** The spec is ` M` (Slice 1's rationale extraction: 34 insertions, 78
deletions, 542 -> 498 lines), so I checked whether the section the anchors bind into is part of that churn:
`diff` of `awk '/^## Edge cases and constraints/,/^## Test plan/'` between `git show HEAD:<spec>` (into the
out-of-repo scratchpad) and the working tree is **empty** — the Edge cases section is byte-identical to
`HEAD`. The anchors are bound into text this cycle did not touch.

### 2. Population re-derived with my own instrument, in a vocabulary Worker 2's cannot reach

Worker 2's pass-3 sweep is
`(edge case[s]?|spec|Decision|item|bullet)[^\n]{0,60}?line\s*/?\s*[0-9]+` over whitespace-flattened text.
Its `line\s*/?\s*[0-9]+` has **no `s?`** and permits only whitespace or a slash between the token and the
number, so it cannot reach `lines 315-320`, `spec-035:271`, `L271`, or a citation whose wrap inserts a `#`
continuation marker. My instrument therefore drops the prefix-keyword requirement entirely and matches on
the number-bearing form, over per-file whitespace-flattened text, in three grammars:

```python
PAT_A = r"\blines?\s*(?:no\.?|number)?\s*[:#]?\s*\d+"     # line OR lines, no keyword prefix required
PAT_B = r"(?:spec[-\s]?\d{2,3}[\w.\-]*|\.md)\s*[:#]\s*\d+" # colon/hash form
PAT_C = r"\bL\d{2,4}\b"                                     # bare L-number
```

Script: `.../scratchpad/w3-035-s2-pass3/pop_w3.py`. Population size printed, not assumed: **434** `.py`
files (excluding `.venv/`, `.git/`, `docs/`), **569** on the second sweep that includes `docs/`.
**41 occurrences** total, enumerated in the run output.

**(a) The in-scope spec-035 set is genuinely EMPTY — re-derived two ways.** First, the ±120-char proximity
sweep: 0 of the tree's `spec-035` occurrences carry a number citation nearby. Second, and stronger, I
enumerated **all 48** `spec-035` occurrences across all 569 `.py` files with their flattened context and a
per-occurrence number-citation check; every one returns `numcite=[]`. No spec-035 raw line citation survives
anywhere in the tree. Confirmed.

**(b) Out-of-scope spec-referencing occurrences: NINE, not eight.** Worker 2's two corrections both hold,
and there is a third the wrap-aware instrument still missed:

| Site | Occurrences | Note |
|---|---|---|
| `tests/mutations/test_sets.py:1034` | 1 | `spec-036 Decision 6 line 334` |
| `tests/mutations/test_sets.py:1039` | 1 | `spec-036 Edge cases line 509` |
| `tests/mutations/test_sets.py:1073-1074` | **2** | `spec-036 Decision 6 line 334` **and** `Edge cases line` wrapping onto `:1074` as `509` |
| `tests/optimizer/test_extension.py` | 3 | `Decision 7 line 346` x2, `Decision 7 line 347` (spec-033) |
| `tests/optimizer/test_extension.py:2248-2249` | 1 | `spec line` / `350` — wraps AND names no spec |
| **`examples/fakeshop/config/settings.py:74-75`** | **1** | **`Decision 13 / spec line` / `# 969` (spec-039) — see the Low below** |

- **Worker 2's `test_sets.py` correction: upheld.** I read `:1030-1042` and `:1070-1078` at source. The
  second docstring's citation reads `(spec-036 Decision 6 line 334 / Edge cases line` + newline + `509)`,
  so that one region carries two occurrences and the second wraps. Four occurrences on three source lines;
  the plan's `#### Partition correction` counted source lines. Worker 2 is right and the reason it gives is
  the right reason.
- **Worker 2's `Item) # Scoped (line 556` false-positive call: upheld.** Read at
  `tests/types/test_resolvers.py:1906-1908`: `_make_relation_resolver(fwd_field, parent_type=Item)` then
  `# Scoped (line 556)`. The `item` alternative matched `parent_type=Item`; the comment cites
  `types/resolvers.py`'s own line numbers and names no spec. Not a spec citation. My own sweep classes it
  with the bare source-line comments, same as Worker 2 did.

Non-spec-document citations, unchanged and not this slice's: `tests/orders/test_factories.py:251`
(`cookbook lines 124-130` — note the **plural**, which is exactly what Worker 2's regex cannot see) and
`tests/orders/test_sets.py:169` (`cookbook line 280`). Bare source-line comments citing a `.py` file's own
lines: `tests/types/test_resolvers.py` (12), `tests/test_exceptions.py` (3), `tests/filters/test_base.py`
(2), `tests/test_export_dry_review.py` (1). Two `#L45-L52` GitHub permalinks in
`django_strawberry_framework/_strawberry_patches.py` are correctly-formed upstream URLs, not citations.

### 3. Identity proof audited and re-derived, enumeration included

My own script (`.../scratchpad/w3-035-s2-pass3/proof_w3.py`), pristine `HEAD` via `git show HEAD:<path>`
written into
`/private/tmp/claude-501/-Users-riordenweber-projects-django-strawberry-framework/f4b7d889-6e73-477e-b5c0-30ac0e17a204/scratchpad/w3-035-s2-pass3/head/`
— **outside the repository**. No `git stash` / `checkout` / `restore` / `worktree` at any point. Three
instruments per file, the third being an independent qualname->docstring **map difference** so "which
docstrings changed" is measured by direct string comparison rather than inferred from the blanked dump:

```
PLAIN-DIFFERS   BLANKED-IDENTICAL  docstrings changed (1): ['_record_relation_access']                     <- django_strawberry_framework/optimizer/walker.py
PLAIN-DIFFERS   BLANKED-IDENTICAL  docstrings changed (3): ['test_enable_only_defaults_enabled_without_info',
                                                            'test_mutation_scalar_only_connection_window_no_only',
                                                            'test_subscription_operation_gated']           <- tests/optimizer/test_walker.py
PLAIN-IDENTICAL BLANKED-IDENTICAL  docstrings changed (0): none                                            <- tests/optimizer/test_extension.py
PLAIN-DIFFERS   BLANKED-IDENTICAL  docstrings changed (1): ['test_fk_id_elision_falls_back_when_consumer_only_defers_fk']  <- tests/types/test_resolvers.py
ALL BLANKED-IDENTICAL
# exit 0
```

Reproduces Worker 2's rows exactly. **`test_walker.py` lists exactly three changed docstrings — the three
citation sites in that file, and no fourth**; cohort-wide five, one per citation site across all three
passes. `test_extension.py` still satisfies the **stronger** plain equality, so pass 1's comment-only claim
for that file survives passes 2 and 3. The per-file docstring counts also independently confirm the pass-3
files-touched claim: walker.py 1 (unchanged from pass 2), test_resolvers.py 1 (unchanged), test_extension.py
0 (unchanged), test_walker.py 2 -> **3**. Only `test_walker.py` was written this pass.

**Negative controls — four, mine, in memory, nothing written to the tree.** Each substitution is
`assert`ed to have matched something first, so a control that silently matched nothing cannot masquerade as
a pass:

```
executable-token (registry.clear() -> registry.clear)   blanked=DIFFERS    plain=DIFFERS
comment-only (a # comment -> # PLACEHOLDER)             blanked=IDENTICAL  plain=DIFFERS
docstring ('"""A scalar-only' -> '"""ZZZ scalar-only')  blanked=IDENTICAL  plain=DIFFERS
enumeration control (perturb a NON-citation docstring)  changed=[...4 names, incl. test_mutation_id_only_relation_still_records_elision]
```

The blanked instrument reports `DIFFERS` on an executable-token perturbation, so it **can** fail; it is
blinded to a docstring edit by design; and the plain instrument sees that same edit, which is what makes the
three-name enumeration a measurement rather than a formality. The fourth control is mine and the build
report does not run it: perturbing a docstring that is **not** a citation site
(`test_mutation_id_only_relation_still_records_elision`) makes the enumeration grow to four names — so
"exactly three, no fourth" is a result the instrument was capable of contradicting. `git status --short` for
the four cohort files after every control still reports exactly four ` M` rows: no mutation left behind.

**Pseudocode preservation re-derived, word-for-word.** All four `Pseudocode:` blocks extracted from
`git show HEAD:<path>` and from the working tree, flattened, and compared token by token: `walker.py`
block 1, `test_walker.py`, `test_extension.py` all **WORD-IDENTICAL**; `walker.py` block 2 (the one rewrap
the plan prescribed) is word-identical **from `Pseudocode:` onward** — the only delta is that at `HEAD` the
label continued a prose sentence, so three preceding words sat inside my extractor's window. No word added,
removed, or reordered in any block.

### 4. No executable line changed; no boundary rode along

`BLANKED-IDENTICAL` on all four files is the direct proof: no statement, expression, branch, or signature
differs from `HEAD`. Every one of the 7 non-`#` added lines is docstring prose, enumerated:

```
walker.py            relation regardless of operation (Decision 4 / Edge cases
test_walker.py       and the prefetch itself are still present (spec-035 Decision 4 / Edge cases
test_walker.py       identically to MUTATION (spec-035 Decision 4 / Edge cases
test_walker.py       by default (spec-035 Decision 4 / Edge cases #"defaults to enabled"). Also
test_walker.py       drives the ``_enable_only_for_operation`` three-arm truth table directly.
test_resolvers.py    so ``operation_arm`` only documents the two shapes), per spec-035
test_resolvers.py    Decision 5 / Edge cases #"can defer the FK column (both".
```

No `if`, `raise`, `return`, `assert`, decorator, import, or signature appears in the added set. No guard,
gate, cap, rejection path, or validation branch. **No failability proof is owed and its absence is not
graded** (`BUILD.md` `### What needs a proof, and what does not`; the plan's `### No failability proof is
owed`, which the dispatch restates). Hot-path and floor-verification are `none` per the plan's
declarations, correctly — nothing runs differently on any path.

Forbidden surfaces confirmed untouched: `git status --short` reports **nothing** for
`django_strawberry_framework/optimizer/selections.py`, and the spec's Edge cases section is byte-identical
to `HEAD` (above). `docs/SPECS/appx/…-terms.csv` is not dirty. `docs/builder/temp-tests/` is empty (0
entries).

### 5. Dispatched findings checklist walk — all three passes, eleven boxes

All eleven are `- [x]`; every tick checked against the cumulative diff; none is an over-tick and none is
unaddressed.

- **Pass 1, boxes 1-4** (four anchor retargets): both `walker.py` heads carry
  `TODO(BACKLOG polymorphic_interface_connections - the abstract-return optimizer entry card)` with the
  `spec-035 Decision 6` / `Decision 7` pointers, R1 at `_walk_selections` and R1+R2 at
  `_selected_scalar_names`; both test anchors retargeted with ` Slice 3` dropped and
  `test_extension.py`'s placement judgement (`if it needs real extension execution rather than pure walker
  inspection`) intact. `review_inspect.py` independently reports **2** TODO comments in `walker.py`
  (`:467`, `:1137`), both this slice's, confirming no third anchor. **All landed.**
- **Pass 1, box 5** (identity proved): recorded, and re-derived by me here.
- **Pass 2, boxes 1-4** (four citation retargets): all four present in the diff with `Decision 4` /
  `Decision 5` retained. **Landed.**
- **Pass 2, box 5** (identity re-proved under the blanked instrument + controls): recorded, re-derived.
- **Pass 3, box 1** (`test_mutation_scalar_only_connection_window_no_only`): the citation now reads
  `(spec-035 Decision 4 / Edge cases` / `#"every projection writer checks the gate")`, `Decision 4` kept,
  anchor whole on one line, population re-derived as an occurrence list. **Landed**, and re-derived above
  rather than accepted.

### 6. Correction-of-record discipline: both halves verified on disk

- **Pass 2's false count is named as superseded.** `## Build report (Worker 2, pass 3)`
  `### Population re-measured with a wrap-aware instrument` quotes both sentences, names where each lives,
  says why each was wrong, and states "**Those two sentences are superseded by the occurrence list
  below.**" That is a correction of record, not a silent rewrite.
- **Pass 2's own text was NOT rewritten.** Both sentences are still on disk verbatim:
  `:922` `Zero occurrences tree-wide.` (in `### How each citation was bound to its bullet`) and `:1104`
  `- **Population is zero now.**` (in `### Notes for Worker 3`). `ARTIFACT.md` `## Re-pass sections`
  satisfied in both directions — pass 3 is appended at the same `##` top level (`:1537`), not nested, and
  no prior entry was edited.

To Worker 2's question in `### Notes for Worker 3` — yes, that is the shape I wanted. A report bullet that
quotes the superseded sentence and says what replaces it is exactly right; rewriting `:922` / `:1104` would
have destroyed the evidence that the instrument was the defect.

### 7. Spec amendments and deferred-catalog items still stand on disk

Re-read on disk this pass, not carried from my prior sections:

- **Pass-1 staged-anchor amendment**: present in the pass-1 build report `### Notes for Worker 1 (spec
  reconciliation)` in the three-part form (where it lives / current wording quoted / recommended
  replacement / why).
- **My pass-1 omission note** (the sentence *preceding* the replaced one also describes the anchors as
  `TODO(spec-035 Slice N)`): present under my pass-1 `### Notes for Worker 1`.
- **Both target sentences are still un-amended in the spec.** `spec-035…:263` still opens
  `a source-site \`TODO(spec-035 Slice N)\` comment naming this spec and the owning slice` and still says
  `the \`TODO(spec-035 Slice 3)\` comments at ... three` sites. Correct: no worker in this slice may edit
  the spec, and Slice 3 owns it.
- **Deferred-catalog items**: pass-1 report items 1-2, my pass-1 items 1-3, pass-2 report item 3, my pass-2
  corrections, and pass-3 report item 4 are all on disk under their respective
  `### Notes for Worker 1 (spec reconciliation)` headings. Nothing lives only in a dispatch.

### 8. Gates re-run by me, not read

- `uv run ruff format --check .` -> `435 files already formatted`
- `uv run ruff check .` -> `All checks passed!`
- `uv run python scripts/check_trailing_commas.py --check` on the four cohort files (zsh **array**,
  population echoed as `4` before the run so the invocation cannot silently have run on one joined path)
  -> exit 0
- `uv run pytest tests/optimizer/test_walker.py tests/optimizer/test_extension.py tests/types/test_resolvers.py --no-cov -q`
  -> **399 passed in 9.03s**, matching both prior passes. No `--cov*` flag on any invocation.

Both repo-wide lint gates are green **tree-wide**, so no attribution question arises against the 64 dirty
rows of concurrent work — there is no failure to attribute.

### 9. Static inspection helper

Required (the slice touches an existing `.py` file under `django_strawberry_framework/optimizer/`), re-run
this pass:

```shell
uv run python scripts/review_inspect.py django_strawberry_framework/optimizer/walker.py --output-dir docs/shadow
```

Wrote both `.overview.md` and `.stripped.py`. Fresh output: 24 imports, 37 symbols, 8 control-flow
hotspots, 7 repeated string literals, **2 TODO comments** (`walker.py:467`, `:1137` — both this slice's
retargeted anchors). No skip to record. The ORM-marker and repeated-literal populations sit entirely on
executable lines and this diff adds no executable line (blanked AST identity above), so none is inside the
diff and none yields a finding. Cited by symbol / original-source line only; no shadow line number appears
in this review.

### High:

None.

### Medium:

None. Pass 2's Medium is closed: the fifth in-scope citation is retargeted, bound by content to the right
bullet, and the in-scope spec-035 population is now empty under an instrument that reaches vocabularies
Worker 2's cannot.

### Low:

#### The replacement wrap-aware instrument is still fail-open on one wrap shape: the out-of-scope population is NINE, not eight

`examples/fakeshop/config/settings.py:74-75`:

```examples/fakeshop/config/settings.py:72:75
    # NOTE(spec-039): `"rest_framework"` is intentionally NOT installed. The
    # products `ItemSerializer` is a flat `ModelSerializer` whose validation +
    # `UniqueTogetherValidator` need no DRF app registry (Decision 13 / spec line
    # 969); DRF being a dev-group dependency keeps it importable in the test context.
```

A raw spec line-number citation of the same class (`AGENTS.md` rule 27), and it is invisible to the
instrument this pass installed as the measurement of record. Flattened, the text reads `spec line # 969`,
and Worker 2's `line\s*/?\s*[0-9]+` permits only whitespace and an optional slash between the token and the
number — a `#` comment-continuation marker between them defeats it. Verified directly: Worker 2's regex on
this file returns `[]`; mine returns `['line # 969']`. So the out-of-scope spec-referencing population is
**nine** occurrences, not the eight the build report states.

The same blind spot also hides the **plural** form: `tests/orders/test_factories.py:251` reads
`cookbook lines 124-130`, which Worker 2's `line` (no `s?`) cannot match. That one is a non-spec document,
so it does not change the nine, but it is the same fail-open shape and it is the second instance of it.

**Why it is Low and not Medium.** The slice's own contract is met — the in-scope spec-035 set is empty,
re-derived independently. `examples/fakeshop/config/settings.py` sits in no cohort of the plan's ownership
table, cites a different spec, is clean at `HEAD` (not baseline-dirty), and nothing this cycle did
falsified it. The defect is in a **count stated about out-of-scope work**, and `BUILD.md` `## Claims are
proven mechanically` is the rule it lands under.

**Recommended change:** none in this slice. Route to the deferred-work catalog with the instrument
corrected — see `### Notes for Worker 1` below. **No test expectation changes**; no behavior is affected.

### DRY findings

- **Examined and rejected: the fifth `Edge cases #"..."` citation is not a duplication of the first.**
  `walker.py::_record_relation_access` and `test_walker.py::test_mutation_scalar_only_connection_window_no_only`
  cite the same bullet because the bullet governs both of them by name. The pointer is one line at each
  site; there is no mechanism to home and nothing that could drift independently. Collapsing them would
  mean deleting one symbol's contract pointer, which is the opposite of what rule 27 asks.
- **Examined and rejected: `Decision 4` in four of the five citations.** Same reasoning as pass 2 — it is
  the contract identifier those sites genuinely share, and dropping it to avoid repetition strips the
  pointer.
- **No new helper, constant, indirection, or abstraction is introduced.** Blanked AST identity proves there
  is no executable line to extract, so there is nothing to raise an existence challenge against beyond the
  anchors themselves, which I challenged and upheld in pass 1 (both legs re-verified there) and which
  neither pass 2 nor pass 3 touched.
- **Cross-cohort duplication review: not applicable.** The build plan declares `ownership partition: none;
  sequential slices`; the mid-flight correction folded a file into the one cohort rather than creating a
  second.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **not** empty, and the change is **not this
slice's**:

```
-__version__ = "0.0.14"
+__version__ = "0.0.15"
```

`__all__` and the re-export list are **unchanged**; the single changed line is the `__version__` literal.
That file appears in no cohort of the build plan's ownership table, so it is a concurrent session's
release-line bump under `AGENTS.md` rule 34 — never edit, never revert. Slice 2 adds no public export,
consistent with spec Decision 9's "this card adds no public symbol".

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. The spec's dirty state is Slice
1's rationale extraction (34 insertions / 78 deletions), not this slice's, and its `## Edge cases and
constraints` section is byte-identical to `HEAD`. The `-rationale.md` (untracked, Slice 1's) and
`-terms.csv` were correctly left untouched. This artifact and `docs/shadow/` are per-cycle scratchpads, not
doc surfaces.

### What looks solid

- **The fifth binding is right for the reason that is hard to get right, and the wrong answer was
  available.** `:275` resolves uniquely, mentions connections and mutations, and would have been a
  defensible-looking choice — and it explicitly denies this test exists. Worker 2 read the bullet's *body*
  rather than its heading and says so in `### Implementation notes`. That is the difference between a
  binding and a guess that happened to be right.
- **The wrap was moved, not papered over.** The docstring cannot hold the citation on one line inside the
  column budget, so the break was relocated to fall *between* the `Decision N / Section` half and the
  `#"substring"` half, leaving the anchor whole. That makes the new citation visible to a line-oriented
  sweep **and** a wrap-aware one — the shape the accepted `_record_relation_access` site already carried.
  The fix generalises rather than patching the one site.
- **The instrument was replaced, not supplemented, and the replacement is stated as the measurement of
  record.** Keeping the line-oriented grep as a co-equal reading is exactly how a fail-open instrument
  survives being caught. `### Implementation notes` names the retired one as "the thing being corrected".
- **The correction of record is a bullet, not a rewrite.** Pass 2's two false sentences are still on disk,
  quoted and superseded. An agent under pressure to look consistent edits the earlier line; this one did
  not, and asked me to confirm the shape.
- **The population is reported as an occurrence list with the scanned-file count printed.** Both prior
  counts on record were wrong; a list the next reader can re-derive is the only form that stops the third
  one being wrong too.
- **Restraint held for a third pass.** `test_extension.py` and `test_resolvers.py` were in the writable set
  and were provably not written (0 and 1 changed docstrings, unchanged from prior passes); the two
  baseline-dirty look-alikes (`tests/rest_framework/test_resolvers.py`,
  `examples/fakeshop/test_query/test_library_api.py`) are untouched and named as such.

### Temp test verification

- No temp test was written, and none is appropriate: the change set is provably comment-and-docstring only,
  so there is no behavior a temp test could demonstrate, and a test asserting docstring prose would pin a
  citation's spelling rather than a contract. `docs/builder/temp-tests/` stays empty (measured: 0 entries).
- The verification scripts I ran this pass live **outside the repository**, under
  `/private/tmp/claude-501/-Users-riordenweber-projects-django-strawberry-framework/f4b7d889-6e73-477e-b5c0-30ac0e17a204/scratchpad/w3-035-s2-pass3/`
  (`proof_w3.py`, `controls_w3.py`, `pop_w3.py`, `head/`, `spec-head.md`, `edge-head.txt` /
  `edge-work.txt`). None writes into the tree.
- Disposition: nothing to promote.

### Notes for Worker 1 (spec reconciliation)

**No spec amendment is owed by this pass, and the prior ones stand.** The fifth citation points at spec
text by content, so no spec sentence became false. Pass 1's single recommended amendment (the
`## Implementation plan` staged-anchor paragraph) and my pass-1 addition to it (the *preceding* sentence,
still describing the anchors as `TODO(spec-035 Slice N)` in the present tense) are both on disk and remain
Slice 3's, verified at `spec-035…:263` this pass.

**Catalog correction, superseding every count on record — the out-of-scope population is NINE.** This
refines Worker 2's pass-3 item 4 (which says eight) and my own pass-2 correction (which said seven). Add
`examples/fakeshop/config/settings.py:74-75` — `Decision 13 / spec line` / `# 969`, a spec-039 citation
whose wrap puts a `#` comment-continuation marker between `line` and the number. The instrument Worker 2
recommends for the catalog,
`(spec[- ][0-9]*|Decision [0-9]+|[Ee]dge cases?)[^.]{0,60}?\blines?\s+[0-9]+`, would **also** miss it (its
`\s+` cannot cross the `#`), so the recommended catalog wording needs one more repair. Suggested grammar,
which finds all nine plus the two `cookbook line(s)` sites:

```python
# per-file whitespace flatten FIRST, then:
r"\blines?\s*(?:#\s*)?[:]?\s*\d+"     # 'line'/'lines', optional wrap-marker '#', optional ':'
r"(?:spec[-\s]?\d{2,3}[\w.\-]*|\.md)\s*[:#]\s*\d+"   # colon/hash form
```

Two lessons worth carrying into the catalog entry, both measured here: a `line`-without-`s?` pattern is
blind to the plural (`cookbook lines 124-130`), and a comment-continuation `#` inside a wrapped citation
defeats any pattern that allows only whitespace between the token and the number. **The out-of-scope sites
are: `tests/mutations/test_sets.py` (4, spec-036), `tests/optimizer/test_extension.py` (4, spec-033),
`examples/fakeshop/config/settings.py` (1, spec-039) = 9.** None is in a cohort; none is fixed here.

**Escalated: the bullet both `#"every projection writer checks the gate"` citations now point at carries a
stale symbol claim of its own.** The `-rationale.md` `## Post-ship divergences (spec vs. HEAD)` item 1
records that commit `991d5120` relocated `_project_scalar_only_window` to
`optimizer/nested_planner.py`, `walker.py` keeping a module-level alias, and that the spec still names
`walker.py::_project_scalar_only_window` in eight places **including two Edge cases** — one of which is
`:271`, the bullet this pass's citation binds to. This is **not a Slice 2 defect**: the Edge cases section
is byte-identical to `HEAD`, the divergence pre-dates this cycle, and the rationale already assigns the
correction to Slice 3. I am naming it because Slice 3 now has a second reason to touch `:271` — two shipped
docstrings point a reader there — so the correction should keep the bullet's two named writers intact while
fixing the symbol's home. Resolution paths for Worker 1: (a) Slice 3 corrects the eight sites in the spec
body per divergence item 1, and the two citations need no change because they bind to the *bullet text*,
not the symbol; or (b) if Slice 3 rewords the bullet's opening phrase, the two `#"..."` anchors break and
must be re-derived in the same change — the anchor phrase `every projection writer checks the gate` is the
thing to preserve.

**Non-blocking, carried forward from pass 2 and still true.** Of the five anchors, `#"defaults to enabled"`
remains the least distinctive (four common words, no `G2` / `info` token). It resolves uniquely today
(re-measured: 1), so there is no defect; if a hardening pass ever touches that docstring,
`` #"info.operation` defaults to enabled" `` or similar would be sturdier.

**The three carry-forward items stand**, all re-verified this pass: (1)
`examples/fakeshop/test_query/test_library_api.py:3680` is still the sole `TODO(spec-035` occurrence in any
`.py` file, baseline-dirty and out of scope, and is the one anchor that makes the integration pass's step-6
sweep non-empty; (2) the two package test-tree anchors become deletable if and only if the spec's G3
deferred test plan ever records their file placement; (3) `selections.py`'s reference anchor is still the
only one of five whose body cites no `spec-035 Decision N`, so a reader landing there by `grep` finds the
owning card but not the design contract.

### Review outcome

`review-accepted`.

The dispatched Medium is closed, and closed at the level it was raised: the fifth citation is retargeted,
bound by content to the one bullet that names both its writer and its exact scenario — with the plausible
wrong bullet identified and ruled out — and the in-scope spec-035 population is genuinely empty, which I
re-derived by enumerating all 48 `spec-035` occurrences across 569 `.py` files with a number-citation check
on each, in vocabularies (plural `lines`, colon form, bare `L`-number) the pass's own instrument cannot
reach. The identity proof reproduces exactly under my own script, the three-docstring enumeration survives
a control that proves it could have named a fourth, and the correction-of-record discipline holds in both
directions — pass 2's false sentences are superseded in pass 3's report and still on disk unedited. All
eleven checklist boxes landed, no boundary rode along, and every gate is green at the recorded scope.

What remains is one Low, and it is out of scope by construction: the replacement wrap-aware instrument is
itself still blind to a `#`-continuation wrap, so a ninth out-of-scope rule-27 citation sits in
`examples/fakeshop/config/settings.py` — a file in no cohort, citing a different spec, clean at `HEAD`, and
not falsified by anything this cycle did. `BUILD.md` `### Spawn-per-cycle dispatch` step 4 routes that to
the deferred-work catalog rather than a fourth loop; it is recorded above with the corrected instrument.
`revision-needed` is reserved for a finding that leaves the slice's contract unmet, and this one does not.

---

## Final verification (Worker 1)

Every number below was re-measured this pass with my own instruments, from the repository root, against
the working-tree diff `git diff -- django_strawberry_framework/optimizer/walker.py
tests/optimizer/test_walker.py tests/optimizer/test_extension.py tests/types/test_resolvers.py`. No
Worker 2 or Worker 3 measurement is carried. Scratch scripts live **outside** the repository, under
`/private/tmp/claude-501/-Users-riordenweber-projects-django-strawberry-framework/f4b7d889-6e73-477e-b5c0-30ac0e17a204/scratchpad/`
(`w1_identity.py`, `w1_control.py`, `w1_controlD.py`, `w1_rawcite.py`, `w1_035.py`); pristine `HEAD` was
read exclusively through `git show HEAD:<path>`. No `git stash`, `git checkout`, `git restore`, or
`git worktree` at any point.

### Step 2 — every planned step implemented or rejected with a reason

All eight plan steps landed. Steps 1-4 are the four anchor retargets, visible in the diff. Step 5
(`selections.py` untouched) and step 6 (`test_library_api.py` untouched) are confirmed by their absence
from `git status --short` and from the diff. Step 7's ruff pair and step 8's ASCII / line-length gate
re-run green below. The two mid-flight apply-changes passes (the four rule-27 citation replacements, then
the fifth wrapped one) were added by Worker 0's partition correction, which the artifact mirrors on disk at
`### Dispatched findings checklist` pass-2 and pass-3 blocks; both are implemented.

### Step 3 — `### Dispatched findings checklist` audit, all eleven boxes across three passes

Every box is `- [x]`, and every `- [x]` contract is present in the diff. Nothing is over-ticked, nothing
landed that was left open, and nothing is deferred, so no box carries a deferral reason.

Pass 1 (five boxes):

1. `walker.py::_walk_selections` — head is now `TODO(BACKLOG polymorphic_interface_connections - the
   abstract-return optimizer entry card)`; body carries `spec-035 Decision 6` + `Decision 7` and the R1
   precondition. The five `Pseudocode:` lines are diff **context**, not `+`/`-`. Confirmed.
2. `walker.py::_selected_scalar_names` — head retargeted; body names requirement **R2** in `spec-035
   Decision 6` plus the R1 unreachability clause. Pseudocode content preserved word-for-word, rewrapped so
   `Pseudocode:` opens its own line — I diffed the two pseudocode texts with whitespace flattened and they
   are identical. Confirmed.
3. `tests/optimizer/test_walker.py` module-level anchor — head retargeted, ` Slice 3` gone, G3
   deferred-test-plan + Decision 6 + R1 pointer added; the eight `# Pseudocode: synthesize
   interface/union-like ...` lines are context. Confirmed.
4. `tests/optimizer/test_extension.py` module-level anchor — head retargeted, ` Slice 3` gone, the
   `if it needs real extension execution rather than pure walker inspection` placement judgement kept
   verbatim, spec pointer added; the four pseudocode lines are context. Confirmed.
5. Executable-token identity proved — re-derived by me below rather than read. Confirmed.

Pass 2 (five boxes) — each replacement re-read against the spec bullet it names:

6. `walker.py::_record_relation_access` — `Decision 4 / edge case line 315` is gone; the docstring now
   reads `(Decision 4 / Edge cases` / `#"every projection writer checks the gate")`, and the bare
   `Decision 4` component is kept as the box claims. Confirmed.
7. `test_walker.py::test_subscription_operation_gated` — `spec-035 Decision 4 / Edge cases
   #"subscription operations are gated identically"`. Confirmed.
8. `test_walker.py::test_enable_only_defaults_enabled_without_info` — `spec-035 Decision 4 / Edge cases
   #"defaults to enabled"`. Confirmed.
9. `tests/types/test_resolvers.py::test_fk_id_elision_falls_back_when_consumer_only_defers_fk` — now
   `per spec-035` / `Decision 5 / Edge cases #"can defer the FK column (both"`, and the docstring's opening
   `Decision 5:` label is still on disk (`tests/types/test_resolvers.py` docstring line 1 reads
   `Decision 5: a deferred consumer-``.only()`` FK column falls back loudly.`). Both halves of the box are
   true. Confirmed.
10. Identity re-proved under the docstring-blanked instrument with negative controls — re-derived by me
    below. Confirmed.

Pass 3 (one box):

11. `test_walker.py::test_mutation_scalar_only_connection_window_no_only` — the wrapped `spec-035 Decision
    4 / edge case` + `line 315` citation is gone; the docstring now reads `(spec-035 Decision 4 / Edge
    cases` / `#"every projection writer checks the gate")`, and the `#"..."` anchor is **whole on one
    source line** (`tests/optimizer/test_walker.py:4850`), which is the box's specific claim. Confirmed.

### `### Verifying relocation / promotion claims` — the central claim re-proved by me

The slice's claim is *comment/docstring text only; no executable line changed*. Plain `ast.dump` equality
is **not** the right instrument here and the plan's original prescription of it is superseded: five
docstrings genuinely changed (the rule-27 citation replacements), so plain equality fails on three of the
four files by design. The correct instrument is docstring-blanked `ast.dump` equality **plus** an
enumeration of every changed docstring — blanking alone would hide an arbitrary docstring rewrite, and the
enumeration is what closes that hole. Re-derived (`w1_identity.py`):

```
django_strawberry_framework/optimizer/walker.py
  plain ast.dump equal          : False
  docstring-blanked ast.dump eq : AST-IDENTICAL
  docstrings total=37  changed=1
    -- CHANGED DOCSTRING: _record_relation_access (HEAD lineno 825)
       -    relation regardless of operation (Decision 4 / edge case line 315).
       +    relation regardless of operation (Decision 4 / Edge cases
       +    #"every projection writer checks the gate").

tests/optimizer/test_walker.py
  plain ast.dump equal          : False
  docstring-blanked ast.dump eq : AST-IDENTICAL
  docstrings total=192  changed=3
    -- CHANGED DOCSTRING: test_mutation_scalar_only_connection_window_no_only (HEAD lineno 4843)
    -- CHANGED DOCSTRING: test_subscription_operation_gated (HEAD lineno 4892)
    -- CHANGED DOCSTRING: test_enable_only_defaults_enabled_without_info (HEAD lineno 4907)

tests/optimizer/test_extension.py
  plain ast.dump equal          : True
  docstring-blanked ast.dump eq : AST-IDENTICAL
  docstrings total=171  changed=0

tests/types/test_resolvers.py
  plain ast.dump equal          : False
  docstring-blanked ast.dump eq : AST-IDENTICAL
  docstrings total=48  changed=1
    -- CHANGED DOCSTRING: test_fk_id_elision_falls_back_when_consumer_only_defers_fk (HEAD lineno 1025)

ALL DOCSTRING-BLANKED IDENTICAL
EXIT=0
```

**Docstring counts are equal HEAD-vs-work in all four files** (37 / 192 / 171 / 48), so no docstring was
added, deleted, or moved — the enumeration compares position-for-position, not by name lookup, so a moved
docstring would surface as a mismatch rather than slipping through. **Five docstrings changed, and all five
are exactly the five rule-27 citation replacements the checklist claims** — zero unexplained docstring
edits. `test_extension.py` changed no docstring at all, matching its comment-only box.

**Four negative controls, because a proof instrument that cannot fail reads exactly like a passing proof**
(`w1_control.py`, `w1_controlD.py`, all in-memory string perturbations; `git status --short` on the cohort
was unchanged afterwards):

```
A executable-token control : AST-DIFFERS (instrument can fail)
B comment-only control     : AST-IDENTICAL (correct)
C non-docstring-literal ctl: AST-DIFFERS (blanking does not hide code strings)
D docstring-text control   : AST-IDENTICAL (blind - enumeration required)
   same perturbation under PLAIN ast.dump: DIFFERS (plain instrument sees it)
```

Control C matters and was not previously run: it proves the blanking targets *docstrings only* and does not
also mask a non-docstring string literal, which would have made the whole proof vacuous for any string
constant in the module. Control D is the one that establishes the instrument's known blind spot — it was
run against a perturbation the AST itself confirms is inside a docstring — and it is why the enumeration
above is load-bearing rather than decorative.

**Verdict: the relocation claim is proven, not accepted.**

### `### Failability and fail-open checks`

- **The record exists and says the right thing at all three passes.** `### Failability proofs` is present
  in every build report and reads `None; this pass introduced no new boundary.` (pass 1, verbatim; passes 2
  and 3 carry the same sentence plus a citation of `BUILD.md` `### What needs a proof, and what does not`).
  Not absent, not silently dropped.
- **And it is actually true**, which I confirmed against the diff rather than against the sentence: the
  docstring-blanked AST identity above proves there is no new executable line in any of the four files, so
  there is no guard, cap, gate, rejection path, or validation branch that could owe a proof. A boundary
  cannot be introduced by a comment.
- **No fail-open shape landed.** Read the diff for the catalogued shapes — bare `except`, `except
  Exception: pass`, `getattr(..., <default>)` swallowing an absent attribute, `or {}` / `or ()` defaulting,
  a `return True` on an unmeasured path, a silent `continue`. There are none, and there can be none: every
  added line is a `#` comment or docstring prose. Saying so explicitly rather than being silent, per
  `worker-1.md` `### Failability and fail-open checks`.

### Anchor citations — all five resolve exactly once and land on the right bullet

Four distinct substrings across five citing symbols (`#"every projection writer checks the gate"` is cited
twice, by the two symbols the bullet names). `grep -oF '<substring>' docs/SPECS/spec-035-optimizer_hardening-0_0_10.md | wc -l`:

| citing symbol | anchor substring | count | resolves to | right bullet? |
| --- | --- | --- | --- | --- |
| `walker.py::_record_relation_access` | `every projection writer checks the gate` | 1 | Edge-cases bullet `G2 - every projection writer checks the gate` | yes; the bullet names `_record_relation_access` explicitly as the FK-connector-column appender under the gate |
| `test_walker.py::test_mutation_scalar_only_connection_window_no_only` | `every projection writer checks the gate` | 1 | same bullet | yes; the bullet names `_project_scalar_only_window` calling `.only(...)` directly, which is exactly what the test gates |
| `test_walker.py::test_subscription_operation_gated` | `subscription operations are gated identically` | 1 | Edge-cases bullet `G2 - subscription operations are gated identically` | yes; the bullet is the SUBSCRIPTION arm of the same gate |
| `test_walker.py::test_enable_only_defaults_enabled_without_info` | `defaults to enabled` | 1 | Edge-cases bullet `G2 - a missing info *or* info.operation defaults to enabled` | yes; the bullet enumerates the three arms the test drives |
| `tests/types/test_resolvers.py::test_fk_id_elision_falls_back_when_consumer_only_defers_fk` | `can defer the FK column (both` | 1 | Edge-cases bullet `G2 / Decision 5 - consumer-provided .only(...) can defer the FK column` | yes; the bullet names this test **by name** in its closing sentence |

All four bullets sit inside `## Edge cases and constraints` (spec section 265-289), so every citation's
`Edge cases` section-name component is accurate, and every `Decision N` component matches its bullet's own
Decision attribution (`Decision 4` for three, `Decision 5` for the fourth). The `Edge cases #"..."` spelling
matches existing repo precedent (`routers.py #"spec-046 Edge cases"`, `mutations/sets.py #"spec-036 Edge
cases"`), so the citation shape is consistent with prior accepted work rather than newly invented.

Every `#"..."` anchor is **whole on one source line** — enumerated across all four cohort files, seven
`#"` occurrences, five of them this slice's and each unbroken. That is what makes them visible to a plain
line-oriented grep and is the generalisation the pass-3 fix bought.

### Step 5 — focused tests

```
uv run pytest tests/optimizer/test_walker.py tests/optimizer/test_extension.py tests/types/test_resolvers.py --no-cov -q
8 workers [399 items]
============================= 399 passed in 9.63s ==============================
```

They run. 399, matching the figure the prior passes recorded. No `--cov*` flag.

Gates re-run by me on the cohort files only (never `.`, this tree carries concurrent sessions' work):
`ruff format --check` -> `4 files already formatted`; `ruff check` -> `All checks passed!`;
`scripts/check_trailing_commas.py --check` -> silent (clean). Non-ASCII bytes in added lines: **none**
(`LC_ALL=C grep '[^ -~]'` over the `+` lines returns nothing, so no en/em dash entered a `.py` file).
Longest added line: **79** characters, inside the 99 limit.

### Step 6 — staged-anchor sweep

`grep -rn 'TODO(spec-035' .` is non-empty, as the dispatch says it will be, and I re-derived the reason
rather than assuming it. Exactly one `.py` survivor:

- `examples/fakeshop/test_query/test_library_api.py:3680` — `# TODO(spec-035): extend this live
  connection-fragment block with the ...`. Baseline-dirty with a concurrent session's work; `AGENTS.md`
  rule 34 forbids editing or reverting it. **Legitimate survivor, recorded as a deferral** (see
  `### Spec changes made (Worker 1 only)` below), not a `revision-needed`. Its anchor names still-open
  carry-forward work, which is the form `BUILD.md` step 6 permits.

Every other hit is a `docs/` prose mention (this artifact, the build plan, Slice 1's artifact, the spec's
own staged-anchor sentence, two `DONE/` artifacts, two archived rationales) — no code site.

`grep -rn 'TODO(BACKLOG' --include='*.py' .` returns **five**, all carrying the identical head token
`TODO(BACKLOG polymorphic_interface_connections` on the first line: `optimizer/selections.py:381` (the
pre-existing reference site), `optimizer/walker.py:467`, `optimizer/walker.py:1137`,
`tests/optimizer/test_walker.py:4963`, `tests/optimizer/test_extension.py:5359`. No in-scope anchor whose
work this slice shipped survives, and the uniformity the slice existed to buy is on disk.

**In-scope rule-27 raw line citations: population empty.** Re-derived with my own wrap-aware instrument
(`w1_035.py`), which flattens each file's whitespace *including newlines* before matching and prints the
population size: **434 `.py` files scanned, 0 occurrences** of a `spec-035` reference within 200 flattened
characters of a raw `line NNN` / `edge case NNN` token. This is the slice's contract and it is met.

**Out-of-scope population independently confirmed at NINE.** My separate broad sweep (`w1_rawcite.py`,
434 files, occurrence list not a count) reproduces Worker 3's pass-3 figure from a different grammar:
`tests/mutations/test_sets.py` 4 (spec-036, at `:1034`, `:1039`, and two on `:1073`),
`tests/optimizer/test_extension.py` 4 (spec-033, at `:1718`, `:1754`, `:1817`, `:2248`),
`examples/fakeshop/config/settings.py` 1 (spec-039, `Decision 13 / spec line # 969` at `:74`) = **9**. My
instrument found the `settings.py` site through a different pattern than Worker 3's, which is what makes it
a confirmation rather than a restatement. The same sweep also surfaces the non-spec `cookbook lines
124-130` shape (`tests/orders/test_factories.py:251`) and the bare self-referencing `(line NNN)` comments
in `tests/types/test_resolvers.py` and `tests/test_exceptions.py`. None is in a cohort; none is this
slice's; all route to the catalog.

### Step 4 — DRY against prior accepted slices

No new duplication. Slice 1 moved spec prose into a rationale companion and touched no `.py`; Slice 2
writes no executable line, so there is no logic, helper, constant, or literal to share or duplicate. Three
repetition candidates examined:

- **The five-way identical anchor head.** Deliberate and load-bearing: it is a grep token, and its whole
  value is that one `grep -rn 'polymorphic_interface_connections'` returns `BACKLOG.md`'s card plus every
  seam in one listing. There is no mechanism behind it to home. Upheld.
- **Two citations of `#"every projection writer checks the gate"`.** The bullet governs both symbols by
  name; collapsing them means deleting one symbol's contract pointer. Upheld, agreeing with Worker 3.
- **The two package test-tree anchors versus the spec's G3 deferred test plan.** Re-derived the plan-pass
  keep decision rather than accepting it: the spec's Slice 1 and Slice 2 test-plan headings each name their
  files, the Slice 3 heading names none, so each anchor holds a file-placement judgement that exists
  nowhere else, and `test_extension.py`'s holds a second (the conditional routing call). Kept. The
  named condition that flips this is in the catalog below.

**DRY conclusion: no outstanding DRY opportunity.** What remains is one Low, out of scope by construction
and already routed to the deferred-work catalog, which `worker-1.md` `## Final verification job` permits
accepting on.

### Step 7 — Slice 3's inbox is complete on disk

No spec reconciliation this pass; Slice 3 owns it and has its own artifact. I confirmed every routed item
is on disk under a `### Notes for Worker 1 (spec reconciliation)` section of **this** artifact, in enough
detail to act on without the dispatch transcript:

1. **The `## Implementation plan` staged-anchor paragraph amendment** — Worker 2 pass 1, in the full
   three-part form (where it lives, current wording quoted verbatim, recommended replacement quoted in
   full, why), and Worker 3 pass 1 adds the omission: the *preceding* sentence
   (`a source-site TODO(spec-035 Slice N) comment naming this spec and the owning slice`) is falsified too
   and must be rewritten in the same pass, or the paragraph contradicts itself. Both link ids the
   replacement introduces (`[test-opt-walker]`, `[test-opt-extension]`) were verified present in the spec's
   definition block. Actionable as written.
2. **The escalated stale symbol claim in the bullet both `#"every projection writer checks the gate"`
   citations point at** — Worker 3 pass 3, present on disk with the constraint recorded explicitly. I
   re-derived the underlying fact rather than accepting it: `_project_scalar_only_window` is **defined** at
   `django_strawberry_framework/optimizer/nested_planner.py:652`, and `walker.py:81` holds only
   `_project_scalar_only_window = _nested_planner._project_scalar_only_window`, a module-level alias, so
   the spec's `[`_project_scalar_only_window`][walker]` names the wrong home. Commit `991d5120`
   ("fix(optimizer): isolate nested planning") is the relocation. **The constraint Slice 3 must honour is
   recorded on disk in Worker 3's own words** — "the anchor phrase `every projection writer checks the
   gate` is the thing to preserve" — with both resolution paths spelled out: correct the symbol's path and
   the two citations need no change (they bind to bullet *text*), or reword the bullet's opening phrase and
   re-derive both `#"..."` anchors in the same change. Two shipped docstrings now bind to that phrase, so
   the preserve-verbatim constraint is load-bearing. Confirmed complete; **not actionable by this slice**
   (the spec's `## Edge cases and constraints` is byte-identical to `HEAD` and the divergence pre-dates
   this cycle).
3. **The four `spec-035` header/status claims** — plan-pass notes: the live-working-path claim at `:137`,
   `:357`, `:380` (twice, one inside a `--spec` argument so DoD item 1's command exits 2 as written), and
   `:406`; plus the `0.0.9` on-disk-version parenthetical at `:3` against an actual `0.0.15`. Re-confirmed
   present this pass. Slice 3's.
4. **The spec `:263` count-and-form staleness** — same paragraph as item 1, recorded with its backing
   measurements.
5. **Slice 1's `## Post-ship divergences (spec vs. HEAD)`** in the rationale companion (7 entries,
   including the `991d5120` relocation that item 2 above depends on) remains Slice 3's primary inbox.

**Spec status-line re-verification (`worker-1.md` `## Spec status-line re-verification`), this spawn.**
Re-read `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md:1-11`. Title, `Status:`, `Owner:`,
`Predecessors:`, and the rationale-companion pointer are accurate. The two falsified header claims (the
`0.0.9` parenthetical at `:3`; the live-working-path claim) are unchanged from the plan pass and remain
routed to Slice 3 — this pass may not edit the spec, so no status-line edit was made and none is recorded
under `### Spec changes made (Worker 1 only)`.

### Summary

Slice 2 shipped two things in one cohort, both comment/docstring text only, both proven mechanically:

- **The carry-forward anchor retarget.** All four in-scope `TODO(spec-035…)` anchors now name the owner who
  will actually ship the work — `TODO(BACKLOG polymorphic_interface_connections - the abstract-return
  optimizer entry card)` — matching the one already-converged site at `selections.py`, with each body
  citing `spec-035 Decision 6` / `Decision 7` as the design contract and the R1 entry-contract
  precondition. Five sites, one grep token, every pseudocode block's technical content preserved.
- **Five rule-27 citation repairs**, added mid-flight by Worker 0's partition correction after Slice 1
  shrank the spec 542 -> 498 lines and falsified every raw line reference into it. Raw `edge case line
  NNN` citations became `Edge cases #"substring"` anchors, each resolving exactly once and landing on the
  bullet its symbol is about, each written whole on one source line. The in-scope population is now empty
  under a wrap-aware instrument.

The three-pass loop is worth recording as working correctly: each pass's population claim was falsified by
the next reviewer's instrument (zero -> one wrapped survivor -> a `#`-continuation wrap the replacement
still could not see), and each correction was made as a superseding bullet rather than an edit to the false
sentence, so the record shows what was believed and when.

### Spec changes made (Worker 1 only)

**No spec edit this pass.** Slice 3 owns spec reconciliation and has its own artifact; every item routed to
it is inventoried under `### Step 7` above.

**Deferral reasons.** No `### Dispatched findings checklist` box is `- [ ]`, so no box needs one. The one
survivor of the step-6 anchor sweep does:

- `examples/fakeshop/test_query/test_library_api.py:3680` keeps its `TODO(spec-035)` head. **Target:
  maintainer follow-up once the concurrent session's work on that file lands** — the file is baseline-dirty
  and `AGENTS.md` rule 34 forbids editing or reverting it, so no worker in this cycle could touch it. It
  should receive the same `TODO(BACKLOG polymorphic_interface_connections - the abstract-return optimizer
  entry card)` head. This is the recorded reason the integration pass's step-6 sweep is non-empty.

**For the `### Deferred work catalog` in `docs/builder/bld-035-final.md`** (Worker 1 is its only author) —
four items, carried forward with the corrections the three review passes made to each other:

1. **The fifth carry-forward anchor is unretargeted**, as above. Baseline-dirty; never edit, never revert.
2. **The two package test-tree anchors become deletable if and only if the spec's G3 deferred test plan
   records their file placement.** Both legs re-verified: the G3 heading names no file (unlike the Slice 1
   and Slice 2 headings), and `real extension execution` appears nowhere in the spec or its rationale.
3. **`selections.py`'s reference anchor is the least informative of the five** — the only one whose body
   cites no `spec-035 Decision N`, so a reader landing there by `grep` finds the owning card but not the
   design contract. One clause closes it. Outside this cycle's partition.
4. **The out-of-scope rule-27 line-citation population is NINE occurrences**, and I confirmed the figure
   independently rather than carrying it: `tests/mutations/test_sets.py` 4 (spec-036),
   `tests/optimizer/test_extension.py` 4 (spec-033), `examples/fakeshop/config/settings.py` 1 (spec-039).
   Record it as an **occurrence list, never a total** — three successive totals on record (zero, six/seven,
   eight) were each produced by an instrument that could not see one wrap shape. Two instrument lessons
   both belong in the entry: a `line`-without-`s?` pattern is blind to the plural (`cookbook lines
   124-130`), and a comment-continuation `#` between the token and the number (`spec line` / `# 969`)
   defeats any pattern allowing only whitespace there. The sweep must flatten each file's whitespace,
   newlines included, **before** matching, and must print the scanned-file count so a zero result is
   distinguishable from a zero-population run. The same sweep surfaces bare self-referencing `(line NNN)`
   comments in `tests/types/test_resolvers.py` and `tests/test_exceptions.py` — the same rot shape against
   a different document, wanting `path::Symbol`.

Also worth carrying, non-blocking and agreed with Worker 3: of the five anchors, `#"defaults to enabled"`
is the least distinctive (four common words, no `G2` / `info` token). It resolves uniquely today
(re-measured: 1), so there is no defect; a future pass touching that docstring should prefer something like
`#"info.operation` defaults to enabled"`.

### Final status

`final-accepted`.

The central claim is proven rather than accepted: docstring-blanked `ast.dump` identity against pristine
`HEAD` on all four cohort files, with equal docstring counts and a position-for-position enumeration
naming exactly the five changed docstrings the checklist claims — under four negative controls, one of
which (a non-docstring string literal) had not been run before and closes the last way the blanking could
have been vacuous. All eleven checklist boxes landed with no over-tick and no silent un-tick. The
failability record exists at all three passes, says `None; this pass introduced no new boundary.`, and the
diff confirms it is true; no fail-open shape landed, and none could. All five `#"..."` anchors resolve
exactly once and land on the bullet their citing symbol is about, every bullet inside `## Edge cases and
constraints`, every anchor whole on one source line. The in-scope `spec-035` raw-citation population is
genuinely empty across 434 `.py` files under a wrap-aware instrument that prints its population size. 399
focused tests pass; ruff, the source-layout gate, ASCII, and line length are all green on the cohort.

What remains does not block: one Low in `examples/fakeshop/config/settings.py` (a different spec, no
cohort, clean at `HEAD`, not falsified by anything this cycle did) and one baseline-dirty anchor no worker
in this cycle was permitted to touch — both routed to the deferred-work catalog with the instrument
corrected. Spec reconciliation is Slice 3's, and its inbox is complete on disk, including the
preserve-the-anchor-phrase-verbatim constraint that two shipped docstrings now depend on.

---

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
