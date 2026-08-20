# Build: Integration consolidation — bare `Decision N` citations in `tests/orders/test_inputs.py`

Spec reference: `docs/SPECS/spec-028-orders-0_0_8.md` (read-only; `final-accepted` at Slice 3, and this pass edits no spec). The input contract is [`bld-integration-028.md`][bld-integration] `### X3 — one coherent story: yes on four axes, NO on one, with the two sites named` and its `### Consolidation required — what Worker 0 dispatches` block, carried into the plan as [`build-028-orders-0_0_8.md`][build-028] `### Integration-pass consolidation cohort, 2026-08-20`.
Status: final-accepted

## Dispatch contract (transcribed by Worker 2 — no Worker 1 planning pass ran for this cohort)

This cohort was opened by the integration pass, which set `Status: revision-needed` on one Medium it may not fix itself (it does not write `.py`), and Worker 0 verified the finding against source before dispatch. There is therefore no `## Plan (Worker 1)` section: the plan-level content lives in the two documents cited above, and the checklist below is a verbatim transcription of the integration pass's two dispatched repairs, not a plan Worker 2 authored. Worker 1 audits the ticks at final verification exactly as it would for a plan it wrote.

### Dispatched findings checklist

- [x] `tests/orders/test_inputs.py::test_ordering_member_values_are_string_names` docstring: `(Decision 5)` -> `(spec-028 Decision 5)`.
- [x] `tests/orders/test_inputs.py::test_registry_clear_invokes_clear_order_input_namespace` body comment: `per Decision 9` -> `per spec-028 Decision 9`.

Standing constraints carried with the dispatch, each verified in `### Validation run` below: the citation sits unbroken on one line; no line past the 110-column E501 grace; zero new `spec-028 #"substring"` citations; no executable statement changes, with AST **and** token identity still `SAME` against `HEAD` and `5c6fdd71`; `ruff format` / `ruff check --fix` scoped to the one file. Explicitly out of scope and untouched: the out-of-family unprefixed `Decision N` sites in `django_strawberry_framework/types/base.py`, `tests/types/test_base.py`, and `examples/fakeshop/test_query/test_library_api.py` (other cards' contracts), and [`django_strawberry_framework/utils/inputs.py`][utils-inputs] `#"the Decision 9 lifecycle clause"` (genuine anaphora four lines under the full form, decided by the integration pass).

---

## Build report (Worker 2)

### Files touched

- `tests/orders/test_inputs.py` — two citations brought onto the file's own durable convention. Line 74's sibling-test docstring now reads `(spec-028 Decision 5)`, matching line 62 twelve lines above; line 681's body comment now reads `per spec-028 Decision 9`. Both are the *axis* the dispatch decided (carry the spec id); the wording is otherwise unchanged, so each repair is a nine-character insertion and nothing else.
- `docs/builder/bld-slice-4-028-decision_citation_consistency.md` — this artifact, created from the [`ARTIFACT.md`][artifact] template.
- `docs/builder/worker-memory/worker-2-028.md` — consolidated (the file was at 77 lines, past the ~50-line cap, so the merge was performed **before** appending) plus one entry for this pass. Gitignored.

The whole diff of this pass, against the pre-edit working copy:

```
74c74
<     """Members carry string values matching their names (Decision 5)."""
---
>     """Members carry string values matching their names (spec-028 Decision 5)."""
681c681
<     # Module global is left parked (parking is load-bearing per Decision 9).
---
>     # Module global is left parked (parking is load-bearing per spec-028 Decision 9).
```

### Tests added or updated

None. No test's name, scope, or assertion changed — the two edits are a docstring and a comment. The file's 42 collected tests are byte-identical in their executable content (`### Validation run`, identity readings).

### Validation run

Every "before" reading was taken **before** the edits, so each delta below is a difference rather than a projection.

#### The three-instrument citation probe over `tests/orders/test_inputs.py`

Four instruments were run, not three: plain whitespace-flattening turned out to be **blind to a citation wrapped inside a `#` comment**, because the continuation line's `#` lands between the two halves of the citation and defeats the pattern. That blindness is demonstrated below rather than asserted, and a fourth instrument (join-normalized flatten) closes it.

| Instrument | Definition | Can it cross a newline? |
| --- | --- | --- |
| **A** line-scoped | separator class is `[ \t]` only | **No** — `re.fullmatch(r"[ \t]+", "\n")` is `None` |
| **B** flattened | every `\s+` run collapsed to one space, then pattern A applied | Yes, but not across a `#` continuation marker |
| **B2** join-flattened | `\n[ \t]*#?[ \t]*` collapsed first, then `\s+`, then pattern A | Yes, including `#` continuations |
| **C** join-aware | the `\n` is **inside** the pattern (`spec-028[ \t]*\n[ \t]*(?:#[ \t]*)?(?:Decision\|DoD\|test\|Edge)`) | Matches **only** wrapped citations |

**A and B are provably different instruments, not one pattern written twice.** A's separator class is newline-free by construction; the control below shows a `\s`-based "single-line" pattern — the exact mistake an earlier pass made — *would* have crossed the newline:

```
synthetic wrapped citation ("... per spec-028\n    # Decision 5 ..."):
  A line-scoped on raw text   = 0   (A is blind, as designed)
  B same pattern on flattened = 0   (B is ALSO blind: the continuation '#' sits between the halves)
  B2 join-flattened           = 1   (sees it)
  C join-aware on raw text    = 1   (sees it)
synthetic single-line citation:
  A = 1   B = 1   B2 = 1   C = 0    (C must be 0 on an unwrapped site, and is)
  does A's [ \t] class match a newline?      False
  would a \s-based "single-line" control?     True   <-- the instrument-collapse trap
```

Readings for the file, before and after. The three instruments **agree at every class, before and after**, so there is nothing to reconcile between them:

| Class | Before (A / B / B2) | After (A / B / B2) |
| --- | --- | --- |
| `spec-028` | 2 / 2 / 2 | **4 / 4 / 4** |
| `spec-028 Decision N` | 1 / 1 / 1 | **3 / 3 / 3** |
| `spec-028 DoD N` | 0 / 0 / 0 | 0 / 0 / 0 |
| `spec-028 test plan` | 0 / 0 / 0 | 0 / 0 / 0 |
| bare `Spec\|spec (Decision\|DoD) N` | 0 / 0 / 0 | 0 / 0 / 0 |
| `Decision N` (any prefix) | 3 / 3 / 3 | 3 / 3 / 3 |
| **`Decision N` NOT preceded by `spec-NNN`** | **2 / 2 / 2** | **0 / 0 / 0** |
| C join-aware, all three joins | 0 | **0** |

The last two rows are the finding and its closure: the file's bare in-family count goes 2 -> 0 while the total `Decision N` count is unchanged at 3, which is what proves the repair *qualified* the two citations rather than adding new ones.

#### Case-insensitive tree-wide censuses (`.py` under `django_strawberry_framework/`, `tests/`, `examples/`, `scripts/`)

Every pattern is anchored on `[Ss]pec-028`, so the 15 sentence-initial `Spec-028` occurrences the integration pass found are inside these numbers.

| Census | Before | After | Expected |
| --- | --- | --- | --- |
| `spec-028` | **106** | **108** | 108 (matches the dispatch's prediction) |
| `spec-028 Decision N` | **62** | **64** | 64 (matches) |
| `spec-028 DoD N` | 2 | 2 | unchanged |
| `spec-028 test plan` | 20 | 20 | unchanged |
| bare `Spec (Decision\|DoD) N`, **capital-`Spec` only** | **1** | **1** | undisturbed — the out-of-family `spec-015` site |
| bare `[Ss]pec (Decision\|DoD) N`, **case-insensitive** | **5** | **5** | undisturbed |

Single-line == flattened == join-flattened at every one of those classes, before and after. The join-aware probe reads **0** for `spec-028` tree-wide, before and after.

**One reading the dispatch did not predict, and it is a measurement rather than a defect.** The prompt's baseline of `1` for the bare `Spec (Decision|DoD) N` class is the **capital-`Spec`** reading. Measured case-insensitively — which this pass was required to do — the class is **5**: the `spec-015` site plus four lowercase `spec Decision N` sites that belong to other cards, listed under `### Notes for Worker 1 (spec reconciliation)`. None is in this cohort's writable set, none was touched, and both readings are unchanged by this pass. It is recorded because "baseline 1" and "baseline 5" are the same population measured with and without the case fix, and the cycle has now been under-measured by case once already.

#### Every citation written resolves against the spec

Confirmed by reading the spec, not by assuming. `grep -n '^### Decision 5 \|^### Decision 9 ' docs/SPECS/spec-028-orders-0_0_8.md`:

```
438:### Decision 5 — `Ordering` enum and argument shape
641:### Decision 9 — Input-class namespace vs `TypeRegistry` and lifecycle
```

Both target headings exist, each exactly once, and each is the subject the citing site claims: Decision 5 is the `Ordering` enum block whose six members and string values lines 62 and 74 assert, and Decision 9 is the input-namespace lifecycle whose "**leaves already-materialized module globals parked**… Parking is **load-bearing**" clause line 681 asserts. Read at source; the parking language is Decision 9's own.

#### Zero new substring citations

`spec-028 #"..."` in `.py`: **0** before, **0** after (baseline preserved). Neither repair introduces one.

#### Line length

Line 74 is 81 columns, line 681 is 85 — both inside the 99-column limit, so the 110-column E501 grace is not even reached and no reflow was needed. The file's two pre-existing over-99 lines (427 at 104, 922 at 106) are Slice 2's and untouched. **Neither citation wraps**: `ruff format` reported `1 file left unchanged`, so the formatter had no opportunity to break either line.

#### Executable-token / AST identity — the entitlement

Two instruments, both falsifiable, against two read-only baselines extracted with `git show <ref>:<path>` into a scratch path **outside** the repository. No `git stash`, `checkout`, `restore`, or `worktree` was used.

- **A** — `ast.dump` after deleting every module/class/function docstring node (structural; blind to a moved non-docstring literal).
- **B** — `tokenize` stream with `COMMENT` / `NL` / `NEWLINE` / `INDENT` / `DEDENT` dropped and **only statement-position** `STRING` tokens collapsed, every other literal kept verbatim.

```
A ast-dump(docstrings stripped):        SAME   (HEAD:tests/orders/test_inputs.py vs working tree)
B token-stream(stmt strings collapsed): SAME   (HEAD:tests/orders/test_inputs.py vs working tree)
A ast-dump(docstrings stripped):        SAME   (pre-edit working copy vs working tree)
B token-stream(stmt strings collapsed): SAME   (pre-edit working copy vs working tree)
```

`cmp` proves `git show HEAD:tests/orders/test_inputs.py` and `git show 5c6fdd71:tests/orders/test_inputs.py` are **byte-identical** for this path — this file's Slice-2 work is entirely dirty, none of it committed — so the two required baselines are one file and the HEAD reading is the non-trivial one. Both readings therefore carry the claim.

**The instruments were proved falsifiable before the readings were believed**, on four transient controls applied to *copies in the scratch path* (never to the tree):

| Control | A | B | What it proves |
| --- | --- | --- | --- |
| t1 — docstring text replaced | SAME | SAME | a docstring edit is invisible to both, i.e. this pass's shape |
| t2 — `==` flipped to `!=` | **DIFFERENT** | **DIFFERENT** | an executable-token change is caught |
| t3 — a non-docstring string literal edited | **DIFFERENT** | **DIFFERENT** | B is not collapsing every string; a literal change is caught |
| t4 — redundant parentheses added | SAME | **DIFFERENT** | **A and B disagree**, so they are two instruments and not one written twice |

A control-hygiene note worth carrying: the first attempt at t2/t3 used BSD `sed`'s `0,/re/s//…/` form, which silently applied **nothing** — and both instruments dutifully reported `SAME`. A `cmp` guard caught it and the controls were re-applied in Python with an `assert` that the text actually changed. A control that did not mutate reads exactly like a passing proof.

#### Gates and collection

| Command | Before | After |
| --- | --- | --- |
| `uv run python scripts/check_citations.py` | `OK: 782 citations resolve (705 in 422 .py files, 77 in KANBAN.md)`, exit 0 | **identical, exit 0** |
| `uv run python scripts/check_trailing_commas.py --check tests/orders/test_inputs.py` | exit 0 | exit 0 |
| `uv run ruff format tests/orders/test_inputs.py` | — | `1 file left unchanged` |
| `uv run ruff check --fix tests/orders/test_inputs.py` | — | `All checks passed!` |
| `uv run python -m compileall -q tests/orders/test_inputs.py` | — | exit 0 |
| `uv run pytest tests/orders/test_inputs.py --no-cov --collect-only -q` | — | `42 tests collected`, exit 0 |

The citation count holds at 782 rather than rising, and that is the correct postcondition here: `check_citations.py` resolves `path::Symbol` references, and both repairs add a `spec-NNN Decision N` prose reference, which no gate in this repo can see. A **fall** would have meant a broken reference; it did not fall.

Both ruff invocations were scoped to the single file, never `.`.

#### `git status --short`

Byte-identical to the pre-edit status apart from this artifact appearing as untracked:

```
 M django_strawberry_framework/orders/base.py
 M django_strawberry_framework/orders/inputs.py
 M django_strawberry_framework/types/base.py
 M docs/SPECS/spec-028-orders-0_0_8.md
 M examples/fakeshop/apps/library/orders.py
 M examples/fakeshop/test_query/test_library_api.py
 M tests/orders/test_inputs.py
 M tests/test_registry.py
?? docs/SPECS/appx/spec-028-orders-0_0_8-rationale.md
?? docs/builder/bld-integration-028.md
?? docs/builder/bld-slice-1-028-rationale_extraction.md
?? docs/builder/bld-slice-2-028-citation_and_provenance_rot.md
?? docs/builder/bld-slice-3-028-spec_reconciliation.md
?? docs/builder/build-028-orders-0_0_8.md
```

Every entry is this cycle's own work — the eight modified paths are Slices 1-3's, the six untracked are the cycle's spec companion and artifacts. **No collateral churn, and nothing was reverted or reformatted.** The concurrent `spec-027` cycle is fully committed at `5447c9eb`, so no other session's uncommitted work is present in this tree to protect, which is the quietest state this cycle has seen.

### Failability proofs

**None; this pass introduced no new boundary.** Zero guards, gates, and rejection paths were added, changed, or removed — the diff is one docstring and one comment, and the entitlement is proved above rather than asserted: AST and token identity `SAME` on two falsifiable instruments against a read-only HEAD baseline. There is nothing whose removal could fail a row, so the weakly-pinned acceptance rule has no subject here and the re-run floor for Worker 3 is empty **by entitlement, not by sampling**. No fail-open shape can have landed either: a fail-open shape is an executable expression, and the executable token stream is unchanged.

### Hot-path budget

Not applicable; plan declares no hot path. Docstring and comment text only — nothing runs per request, per resolver, per row, per connection, or per outbound message, and the plan's build-wide declaration states `none` with no before/after number owed.

### Floor verification

Not applicable; plan declares floor-verification scope `none`. No Django / Strawberry / channels integration seam is touched — no executable statement is touched at all. No floor venv was built and the shared `.venv` was not mutated.

### Implementation notes

- **The axis was decided, the wording was mine, and I kept the wording minimal.** Each repair is a nine-character insertion of `spec-028 ` in front of the existing `Decision N`. Rewriting either sentence would have made the diff harder to audit against the two-token dispatch for no reader gain — line 74's sentence already says what it asserts, and line 681's already names parking as load-bearing.
- **Line 681 sits in the comment, not in the enclosing docstring.** The alternative repair — adding a `spec-028` anchor to `::test_registry_clear_invokes_clear_order_input_namespace`'s docstring and leaving the comment bare as anaphora — was rejected because it manufactures an anchor for a citation 8 lines below it rather than making the citation self-resolving, and because the dispatch names the comment itself as the site. Qualifying in place is what makes a reader landing on line 681 able to resolve it without scanning.
- **No `#"substring"` form was used** for either citation, deliberately. The prose `spec-028 Decision N` form is what the file's own convention (line 62) uses and what the dispatch decided; a substring citation into a spec heading would add a form the gate cannot see and the spec's own text could break on reflow.
- **The wrap check is a postcondition here, not only a precondition.** Both instruments C and B2 were re-run after the edit, on the file and tree-wide, precisely because a repair that lengthens a line is the event most likely to mint a wrap. Neither line was long enough for the formatter to touch, and `ruff format` confirmed it independently.

### Notes for Worker 3

- The whole pass is the two-line diff quoted under `### Files touched`. `git diff HEAD -- tests/orders/test_inputs.py` shows 52 insertions / 40 deletions, of which **all but two lines are Slice 2's uncommitted work** in the same file — read against the pre-edit copy, not against HEAD, to see this pass alone. `git diff -- <path>` was never used (a concurrent `add -A` makes it read clean); every reading above is `git diff HEAD --`, `git show <ref>:<path>`, or the current file.
- No `review_inspect.py` run: zero review-worthy logic changed, and the file is a test module whose executable content is provably identical to HEAD's. Recorded as an explicit skip with that reason, matching the disposition every other file in this cycle carries.
- **Worth an independent re-derivation, since it is the one number in this report that disagrees with the dispatch:** the bare `Spec (Decision|DoD) N` census is 1 under a capital-only pattern and 5 case-insensitively. Both readings are unchanged before and after; the four extra sites are other cards' and named below.
- No `pytest` beyond the collection check, and no `--cov*` flag at any point.

### Notes for Worker 1 (spec reconciliation)

No spec edit is owed by this pass and none was made — the spec and its rationale companion closed `final-accepted` at Slice 3 and were read-only here. Three items for the record:

- **The bare `Spec (Decision|DoD) N` population is 5, not 1, once the census is case-insensitive**, and the four sites the capital-only pattern cannot see are all out-of-family: `django_strawberry_framework/list_field.py` `#"see spec Decision 2,"`, `django_strawberry_framework/filters/factories.py` `#"spec Decision 4"`, `tests/test_list_field.py` `#"spec Decision 2 async path"`, and `tests/types/test_resolvers.py` `#"per spec Decision 5 +"`. They name other cards' decisions this cycle never verified, so respelling them would be a worker asserting another card's contract — the same ground that fenced the connection/relay registry twins. **Not touched, and not a `spec-028` defect.** Recommended disposition: carry as one line in `bld-final-028.md`'s `### Deferred work catalog`, beside the existing `check_citations.py` gate-extension proposal, since the gate clause that would resolve a `spec-NNN Decision N` citation is exactly the clause that would flag a `spec Decision N` citation naming no spec at all.
- **The `check_citations.py` gate-extension proposal gains a fifth clause, distinct from the four already recorded.** This pass demonstrated that **whitespace-flattening alone is blind to a citation wrapped inside a `#` comment**: the continuation line's `#` lands between the citation's halves and defeats the pattern. Every "flattened" probe in this cycle that ran over comment text therefore carried a blind spot, and only a join-aware pattern (or a flatten that also strips the continuation `#`) closes it. Recommended wording for the card: *"the flattened probe must collapse `\n[ \t]*#?[ \t]*`, not merely `\s+`, or a citation wrapped inside a comment stays invisible to it."*
- **A control-hygiene clause for the same card.** A BSD-`sed` mutation control silently applied nothing and both identity instruments reported `SAME`, which is indistinguishable from a passing proof. Recommended wording: *"every transient mutation control asserts that the text actually changed (`cmp` or an equality assert) before its reading is believed."* This is the `### What gets recorded` collection-error lesson in a new spelling — a control that did not run reads as a control that passed.

---

## Review (Worker 3)

Reviewed the working-tree state of `tests/orders/test_inputs.py` against `HEAD` (`5447c9eb`), against `5c6fdd71`, and against a **reconstructed pre-edit copy** built in a scratch path outside the repo by deleting the two nine-character insertions from the current file. `cmp` re-derived independently: `git show HEAD:tests/orders/test_inputs.py` and `git show 5c6fdd71:tests/orders/test_inputs.py` are byte-identical, so this file's whole Slice-2 contribution is dirty and one baseline carries both claims. `git diff HEAD --numstat` reads `52 40`, matching the build report. No `git diff -- <path>`, no `stash` / `checkout` / `restore` / `worktree`, no source mutation (the item-4 carve-out was **not** invoked; every control below ran on scratch copies).

### High:

None.

### Medium:

None.

### Low:

#### The dispatch's characterization of line 516 is imprecise; the conclusion it supports is not

The dispatch (and the plan's cohort section) justifies "line 681 is not anaphora" partly on line 516 being "165 lines away **on a different topic**". Line 516 is `::test_clear_order_input_namespace_leaves_module_globals_parked` — `"""The materialized class stays on the module dict per spec-028."""` — which is the *same* subject as line 681's parked-globals claim, not a different one. The non-anaphora conclusion survives untouched and by a stronger route: 516 carries **no Decision number at all**, so it could never have been the antecedent for a bare `Decision 9`, and it sits in a different function 165 lines up. Nothing in the diff changes; this is a correction to the *record* so a later reader does not inherit a false description of the file (the recurring shape: a finding's description going wrong while its finding is right). Routed below rather than looped.

#### Line 516's own `per spec-028` names no Decision (adjacent class, not the dispatched one)

`tests/orders/test_inputs.py:516` cites the spec with no Decision anchor, where the content it asserts is Decision 9's parking clause. It is **not** a bare `Decision N` site, so it is outside the dispatched class, and qualifying it would *add* a citation (the census the repair was graded on would go 3 -> 4 for exactly the reason item 1 of this review exists to detect). Left alone deliberately; routed to the deferred catalog.

### Findings verification — the five things this review had to settle

**1. The repair qualified rather than added.** Re-derived both halves on the reconstructed pre-edit copy and the current file, all three instruments, case-insensitively:

| Class | BEFORE (A / B / B2) | AFTER (A / B / B2) |
| --- | --- | --- |
| `spec-028` (any) | 2 / 2 / 2 | 4 / 4 / 4 |
| `spec-028 Decision N` | 1 / 1 / 1 | 3 / 3 / 3 |
| `Decision N` (any prefix) | **3 / 3 / 3** | **3 / 3 / 3** |
| `Decision N` NOT preceded by `spec-NNN` | **2 / 2 / 2** | **0 / 0 / 0** |
| bare `[Ss]pec (Decision\|DoD) N` | 0 / 0 / 0 | 0 / 0 / 0 |
| C join-aware (wrapped only) | 0 | 0 |

Total `Decision N` unchanged at 3 while the bare subset goes 2 -> 0: the two citations were **qualified**, not supplemented. A third citation would have read 3 -> 4 and does not. The byte delta of the reconstruction is exactly **18** = 2 x 9 characters, which independently confirms "a nine-character insertion and nothing else" — no wording drifted anywhere else in the file. `HEAD` reads identically to BEFORE on every class above, so Slice 2 added no `spec-028` token to this file and the deltas are wholly this pass's.

**2. Both citations resolve, and to the subjects they claim.** Checked by reading the rewritten spec, not the anchor alone. `### Decision 5 — `Ordering` enum and argument shape` at spec:438, exactly one occurrence; its fenced block is the six-member enum with `ASC = "ASC"` … `DESC_NULLS_LAST = "DESC_NULLS_LAST"`, i.e. member **values matching member names** — precisely what line 74 asserts and what its sibling at line 62 already cites. `### Decision 9 — Input-class namespace vs `TypeRegistry` and lifecycle` at spec:641, exactly one occurrence; its lifecycle bullet says `registry.clear()` "**leaves already-materialized module globals parked in `orders.inputs.__dict__`**" and "**Parking is load-bearing**" — the exact claim line 681's comment makes, in the spec's own vocabulary. Cross-checked against the rationale companion: D5 rev4 B1/B3 own the enum surface, D9 rev4 B2 is where the parking rule was made explicit. Neither citation re-raises a rejected alternative (D9's three rejections are the sidecar dict, the shared dict, and skipping the `registry.clear()` integration; the `delattr` alternative is the one parking rejects, which is what line 681 pins).

**3. Zero executable change, on my own instruments, falsified first.** Two instruments written independently: **A** = `ast.dump` after deleting every module/class/function docstring node; **B** = `tokenize` stream with `COMMENT` / `NL` / `NEWLINE` / `INDENT` / `DEDENT` dropped and only statement-position `STRING` tokens collapsed. Baselines extracted with `git show <ref>:<path>` into a scratch path outside the repo.

```
A ast=SAME       B tok=SAME    HEAD (5447c9eb) vs working tree
A ast=SAME       B tok=SAME    5c6fdd71 vs working tree
A ast=SAME       B tok=SAME    reconstructed pre-edit copy vs working tree
```

Falsified on five controls, each applied in Python to a scratch copy **with an `assert mut != base`** so a control that does not mutate cannot masquerade as a passing proof (adopting Worker 2's BSD-`sed` lesson; the assert also printed the before/after byte counts):

| Control | A | B | Proves |
| --- | --- | --- | --- |
| t1 line-74 docstring replaced wholesale | SAME | SAME | a docstring edit is invisible to both — this pass's first shape |
| t2 `==` flipped to `!=` in `test_ordering_member_values_are_string_names` | DIFFERENT | DIFFERENT | an executable-token change is caught |
| t3 non-docstring literal `("stub", "title")` -> `("stub", "ZZZZ")` | DIFFERENT | DIFFERENT | B is not collapsing every string |
| t4 redundant parentheses added | SAME | **DIFFERENT** | A and B **disagree** — two instruments, not one written twice |
| t5 line-681 comment text rewritten wholesale | SAME | SAME | a comment edit is invisible to both — this pass's second shape |

Every control landed on its expected pair. The entitlement holds: **zero executable statements changed**, so the zero-boundary declaration is proved rather than asserted, and no fail-open shape can have landed (a fail-open shape is an executable expression).

**4. Wrap and case blind spots.** Instruments: **A** line-scoped with `[ \t]` applied per physical line, **B** `\s+`-flattened, **B2** join-flattened (`\n[ \t]*#?[ \t]*` collapsed first), **C** join-aware with the `\n` inside the pattern. Provably different, on synthetic controls run before the readings:

```
synthetic wrapped-in-comment citation:  A=0  B=0  B2=1  C=1
synthetic single-line citation:         A=1  B=1  B2=1  C=0
re.fullmatch(r"[ \t]+", "\n") -> False        re.fullmatch(r"\s+", "\n") -> True
```

Worker 2's fifth blind spot **reproduces on my own instrument**: plain `\s+`-flattening reads **0** on a citation wrapped inside a `#` comment, because the continuation `#` lands between the halves — B and B2 are not the same pattern, and only B2/C see it. Confirmed independently, so the routed clause is a real gap and not a rationalization. Tree-wide, case-insensitive over 422 `.py` files under `django_strawberry_framework/`, `tests/`, `examples/`, `scripts/`:

| Census | BEFORE | AFTER | Report claimed |
| --- | --- | --- | --- |
| `[Ss]pec-028` | 106 | 108 | 106 -> 108 (matches) |
| `[Ss]pec-028 Decision N` | 62 | 64 | 62 -> 64 (matches) |
| `[Ss]pec-028 DoD N` | 2 | 2 | unchanged (matches) |
| `[Ss]pec-028 test plan` | 20 | 20 | unchanged (matches) |
| bare `Spec (Decision\|DoD) N`, capital-only | 1 | 1 | 1 (matches) |
| bare `[Ss]pec (Decision\|DoD) N`, case-insensitive | **5** | **5** | 5 (matches) |
| C join-aware `spec-028` wrapped | 0 | 0 | 0 (matches) |

A == B == B2 at every class, before and after; nothing to reconcile between instruments. The 15 sentence-initial `Spec-028` occurrences are inside the 106/108 by construction (`[Ss]` anchor). Every number in the build report re-derives exactly, measured 2026-08-20 13:52 EDT.

**5. The three routed notes are correctly scoped.** Judged individually, not as a set:

- **(a) the case-only census delta — correctly routed, and genuinely other cards' work.** Independently enumerated all five sites of the case-insensitive class. The capital-only one is `tests/types/test_relay_interfaces.py:371` (`spec-015`, out of family, on the do-not-touch list). The four lowercase ones are `django_strawberry_framework/filters/factories.py:143` (a cookbook `get_filterset_class` name-collision note — filter side, `spec-027`), `django_strawberry_framework/list_field.py:192` (async-detection asymmetry in `DjangoListField`), `tests/test_list_field.py:206` (the same `DjangoListField` async path), `tests/types/test_resolvers.py:785` (a `router.db_for_read` mock pattern in `types/resolvers`). **None is in the orders family**; each names a decision of a card this cycle never verified, so respelling any of them would be a worker asserting another card's contract. The recommended home — one line in `bld-final-028.md`'s `### Deferred work catalog` beside the gate-extension proposal — is right, and the pairing argument is right too: the clause that would resolve `spec-NNN Decision N` is the clause that would flag `spec Decision N` naming no spec.
- **(b) the `#`-comment flattening clause — correctly routed.** It is an instrument/gate property, reproduced above on my own instrument, and it belongs on the `check_citations.py` gate-extension card rather than in any `.py` this cohort owns.
- **(c) the control-hygiene clause — correctly routed, and adopted here.** It is the `### What gets recorded` collection-error lesson in a new spelling (a control that did not run reads as a control that passed), so the gate-extension card is the right home; I applied it as an `assert` in all five controls above rather than trusting the readings.

### DRY findings

- **No new duplication.** The pass changed zero executable tokens, so no literal, key, error shape, or branch was added, and `review_inspect.py`'s repeated-literal signal has nothing new to report by construction. Lines 62 and 74 now both cite `spec-028 Decision 5`; that is convergent **citation** between two sibling tests asserting two halves of one Decision (member set, member values) — the file's own durable convention, not duplicated logic, and the axis the dispatch decided.
- **The existence challenge stays deferred.** Worker 1's earlier ruling over the triple-pinned single-sited `utils/` contracts is not reopened here; the ground (every resolution changes executable statements and forfeits the zero-boundary entitlement) is unchanged by this pass. Nothing in this diff creates a new abstraction, helper, registry, or indirection to challenge.

### `AGENTS.md` "No process provenance in code"

Both insertions are **durable spec-Decision pointers** — the explicit KEEP-list form — not review-item ids, round numbers, cycle names, or any account of how the change came to be. Verified against the spec that `Decision 5` and `Decision 9` are the spec's own stable heading numbers (13 `### Decision N` headings, each unique), and against `AGENTS.md`'s source-reference rule that the prose `spec-NNN Decision N` form is the correct spelling for a spec pointer (no `path:NN`, no `#"substring"` minted — the file's `spec-028 #"..."` count is 0 before and after). The comment at line 681 states the invariant ("parking is load-bearing") and cites where it is decided; it says nothing about the repair, the integration pass, or this cohort.

### `scripts/review_inspect.py`

**Skipped, deliberately, with the trigger quoted verbatim.** `BUILD.md` `### When to run the helper during build` fires for Worker 3 when the slice "adds a new `.py` file of any size", "touches an existing `.py` file under `optimizer/` or `types/`", or "adds 30+ lines of new logic to any file under `django_strawberry_framework/`, or 50+ lines to any file outside it". This pass adds no file; touches `tests/orders/test_inputs.py`, which is under neither `optimizer/` nor `types/`; and adds **zero** lines of logic (18 bytes of docstring and comment text, executable identity `SAME` on two falsifiable instruments). No trigger fires, and the disposition is the "no review-worthy logic" skip the rest of this cycle's sixteen files carry. Recorded explicitly so no reader has to infer it — an earlier pass in this cycle misquoted this trigger as needing "source changes" and nearly skipped a run it owed.

### Failability proofs — re-run set

**Empty by entitlement, not by sampling.** The diff introduces no boundary, guard, gate, or rejection path: I re-derived the zero-executable-change claim myself on two independently-written, independently-falsified instruments against `HEAD`, `5c6fdd71`, and the reconstructed pre-edit copy (item 3 above). With no executable token changed there is nothing whose removal could fail a row, so the mandatory floor ("every boundary whose recorded failing-row count is 3 or fewer, and every security / data-isolation boundary") has **no members**, the weakly-pinned rule has no subject, and Worker 2's record of `None` is correct rather than thin. Boundaries re-run: none. Boundaries accepted on Worker 2's record: none — there are none to accept.

### Hot-path budget

Not applicable; the plan declares no hot path and this pass changes docstring and comment text only. No before/after number is owed and none is missing.

### Floor verification

Not applicable; the plan declares floor-verification scope `none` and no Django / Strawberry / channels seam is touched (no executable statement is touched at all). No floor venv was built; the shared `.venv` was not mutated or inspected for versions.

### Gates re-run independently (read-only)

| Command | Result |
| --- | --- |
| `uv run python scripts/check_citations.py` | `OK: 782 citations resolve (705 in 422 .py files, 77 in KANBAN.md)`, exit 0 — same total as the build report, and correctly **flat**: both repairs add prose refs no gate resolves; a fall would have meant breakage |
| `uv run python scripts/check_trailing_commas.py --check tests/orders/test_inputs.py` | exit 0 |
| `uv run ruff format --check tests/orders/test_inputs.py` | `1 file already formatted`, exit 0 (`--check`, never `--fix`) |
| `uv run ruff check tests/orders/test_inputs.py` | `All checks passed!`, exit 0 |
| `uv run python -m compileall -q tests/orders/test_inputs.py` | exit 0 |
| `uv run pytest tests/orders/test_inputs.py --no-cov --collect-only -q` | `42 tests collected`, exit 0. No `--cov*` flag at any point in this pass |

Line lengths re-measured: line 74 = **81** columns, line 681 = **85** — both inside the 99 limit, so the 110-column E501 grace is not reached and neither line could have been reflowed into a wrap. The file's only over-99 lines are 427 (104) and 922 (106), both Slice 2's and both untouched. File is pure ASCII (`all(c < 128)` over the bytes), and both edited lines are ASCII.

### Dispatched findings checklist audit

Both boxes are `- [x]` and both fixes are present in the working tree at the cited symbols — `::test_ordering_member_values_are_string_names` line 74 reads `(spec-028 Decision 5)`, `::test_registry_clear_invokes_clear_order_input_namespace` line 681 reads `per spec-028 Decision 9`. **No over-tick, nothing un-ticked, and no box the diff leaves unaddressed**, so neither Medium the round's tick discipline defines applies.

### Ownership partition held

Only `tests/orders/test_inputs.py` was written in this pass's window (mtime 13:45:07); the other six dirty `.py` paths all share mtime 13:17:27, before it, and the artifact itself is 13:48:11. Combined with the two-line reconstruction and the tree-wide census delta of exactly `+2 / +2` attributable to that one file, the declared single-file partition held.

### Test staleness (independent sweep)

Neither shape `BUILD.md` `### Test staleness a focused run cannot see` names can arise from this pass: no example-model field was added, removed, or renamed, and no wire-shape / envelope conversion occurred — the executable token stream of the only touched file is identical to `HEAD`'s on two instruments, and no other file was touched. Swept independently rather than from the artifact's file list; nothing to re-pin.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` is **empty** — `__all__` and the re-export list are unchanged. No public surface moved, consistent with "no new public exports".

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md`. Confirmed by an empty `git diff HEAD --stat` over `CHANGELOG.md`.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. Confirmed by an empty `git diff HEAD --stat` over `CHANGELOG.md`, `docs/GLOSSARY.md`, `docs/TREE.md`, `KANBAN.md`, `KANBAN.html`, `README.md`, `TODAY.md`. The only doc written is this per-cycle `bld-*.md` scratchpad, which `START.md` exempts from standing-doc treatment.

### What looks solid

- **The repair is the minimum that closes the finding.** Nine characters in front of an existing `Decision N`, twice, with the surrounding sentences untouched — which is what makes the census-based proof (`3 -> 3` total, `2 -> 0` bare) auditable at a glance and what keeps the entitlement intact. Rewriting either sentence would have cost the diff its own audit trail for no reader gain.
- **Qualifying in place rather than manufacturing an anchor.** The rejected alternative (anchor the enclosing docstring, leave the comment as anaphora over 8 lines) is recorded with its reason, and it is the right rejection: a reader landing on line 681 now resolves it without scanning, which is the whole content of the finding.
- **The report's numbers are all re-derivable and all re-derived.** Every reading in `### Validation run` reproduced on independently-written instruments — file-level censuses, tree-wide censuses, line lengths, the citation-gate total, the collection count, the `cmp` baseline collapse. Nothing had to be taken on prose.
- **The blind spots are demonstrated rather than asserted.** The `#`-comment flattening gap and the `\s`-crosses-a-newline trap are both shown on synthetic controls in the report, and both reproduce on my instruments. That is the shape a claim about an instrument has to take.

### Temp test verification

None created; `docs/builder/temp-tests/slice-4/` was not used and does not exist. Nothing in a diff of two prose lines has a behavior a temp test could pin that the identity instruments do not settle more directly — and a temp test asserting docstring text would pin the citation's spelling, not any contract. Disposition: no temp tests, nothing to promote.

### Notes for Worker 1 (spec reconciliation)

No spec edit is owed by this pass and none was made; the spec and its rationale companion were read-only (`final-accepted` at Slice 3) and both were read to verify the two citations' subjects. Four items for the final gate's `### Deferred work catalog`, none of which reopens this cohort:

- **Escalated: one non-anaphoric bare in-family `Decision N` site survives at *family* scope, outside this cohort's partition.** The dispatch scoped C12's residue to one *file*, and inside that file the class is now genuinely 0. Measured across the orders family (`django_strawberry_framework/orders/**`, `tests/orders/**`, plus `utils/inputs.py`) the class is **3**: `tests/orders/test_finalizer.py:14` (`Per Decision 6`, 4 lines under the module docstring's own `per spec-028` — anaphora, fine), `django_strawberry_framework/utils/inputs.py:1300` (the integration pass's decided anaphora, 3 lines under the full form, byte-identical and untouched), and **`tests/orders/test_finalizer.py:432`** — a section-banner comment `# Decision 6 -- first-bind model compatibility` whose nearest earlier `spec-028` token is **320 lines** up, with the full `spec-028 Decision 6` form 158 lines *below* it. That is structurally the same site shape as the line 681 this cohort just repaired (165 lines, different function). Resolution paths: (i) carry it in the deferred catalog as the family-scope remainder, or (ii) dispatch a one-line cohort over `tests/orders/test_finalizer.py` on the same zero-boundary entitlement. Worth stating explicitly because the dispatch's "2 of 18 sites of C12's own class" invites a reader to conclude the class is closed after this repair; at file scope it is, at family scope it is not.
- **Correct the record on line 516's topic.** The dispatch and the plan's cohort section describe `tests/orders/test_inputs.py:516` as "165 lines away on a different topic". It is `::test_clear_order_input_namespace_leaves_module_globals_parked` — the *same* parked-globals subject as line 681. The not-anaphora conclusion is unaffected and in fact stronger (516 carries no Decision number, so it could never have been the antecedent), but the description is false as written and this cycle's dominant defect class is exactly a true finding carried by a false description.
- **Line 516's `per spec-028` names no Decision.** Same file, adjacent class, deliberately untouched: it is not a bare `Decision N`, and qualifying it would *add* a citation (census 3 -> 4) rather than qualify one. Candidate for whichever future pass owns under-specified `spec-NNN`-without-Decision refs; it would be a one-word change to `per spec-028 Decision 9`.
- **The three notes Worker 2 routed are correctly homed and I re-derived each** (see item 5 above): the case-insensitive bare-`spec Decision N` population is 5 with all four extra sites belonging to other cards, the `#`-comment flattening clause reproduces, and the control-hygiene clause is the collection-error lesson respelled. All three belong in the deferred catalog beside the `check_citations.py` gate-extension proposal; none is `spec-028` residue.

### Concurrent-tree drift observed (attributed, not graded)

Since Worker 2's `git status` reading, another session moved the `027` build plan: `D docs/builder/build-027-filters-0_0_8.md` plus `?? docs/builder/DONE/build-027-filters-0_0_8.md`. Not this cohort's work, not touched, not reverted — recorded only so the final gate does not read it as this cycle's churn. The eight `M` paths and the cycle's untracked artifacts are otherwise exactly as the build report lists.

### Review outcome

`review-accepted`. Both dispatched repairs landed as specified and nothing else moved: the bare in-family census in the cohort's file goes 2 -> 0 while total `Decision N` holds at 3, the reconstruction's byte delta is exactly 2 x 9, both citations resolve to headings that exist once each and that own the claims made against them, executable identity is `SAME` on two instruments falsified on five asserted controls, no wrap was minted on any of four wrap instruments, and every tree-wide census reproduces the report to the digit. Zero High, zero Medium; two Lows, both about the *record* rather than the diff, both routed rather than looped. The failability re-run floor is empty **by entitlement** — the zero-executable-change proof is also the zero-boundary proof — not by sampling.

---

## Final verification (Worker 1)

### Summary

`Status: final-accepted`. Both dispatched boxes hold, and **every claim was re-derived by this pass on instruments this pass wrote** rather than read out of the build report or the review. Nothing routes back to a second loop: the two Lows are record corrections, both adopted below, and the one escalation is ruled on with a measurement.

**Boundary count: zero, and the failability record is absent BY ENTITLEMENT rather than missing.** A boundary is an executable expression; the executable token stream of `tests/orders/test_inputs.py` is identical to three separate reference points on two independent instruments (6 readings, 0 mismatches, below), so there is no boundary that could owe a proof and no fail-open shape can have landed. `### Failability proofs` reading `None; this pass introduced no new boundary.` is the correct content. **Hot path: none declared, none owed, none flagged. Floor-verification scope: `none`**; no floor venv was built and the shared `.venv` was not mutated or read for a version claim. (Reference only, from [`BUILD.md`][build] `## Floor verification`: Django 5.2.16 on Python 3.10 with strawberry-graphql 0.316.0.)

### Dispatched findings checklist audit — both ticks re-derived

Measured against the **current file**, never against a diff: `cmp` re-confirms `git show HEAD:tests/orders/test_inputs.py` and `git show 5c6fdd71:tests/orders/test_inputs.py` are byte-identical (34,252 bytes both), so this file's whole Slice-2 contribution is dirty and a diff reading cannot isolate this pass.

| Box | Verdict | Re-derivation by this pass |
| --- | --- | --- |
| `::test_ordering_member_values_are_string_names` docstring `(Decision 5)` -> `(spec-028 Decision 5)` | **holds** | line 74 reads `"""Members carry string values matching their names (spec-028 Decision 5)."""`; the enclosing symbol was resolved from the AST (not from the line number) and is that function |
| `::test_registry_clear_invokes_clear_order_input_namespace` comment `per Decision 9` -> `per spec-028 Decision 9` | **holds** | line 681 reads `# Module global is left parked (parking is load-bearing per spec-028 Decision 9).`; AST-resolved owner is that function |

**No box is un-ticked and none is left `- [ ]`.** No deferral reason is owed.

### Claim 1 — qualified, not added: re-derived on three instruments

Instruments written this pass, and **provably three rather than one written thrice**: **I1** line-scoped with the separator class `[ \t]` applied per physical line; **I2** whole-file `\s+`-flattened; **I3** join-flattened (`\n[ \t]*#?[ \t]*` collapsed *first*, then `\s+`). Falsified on synthetic controls before any reading was believed, each control asserting the text actually changed:

```
synthetic WRAPPED-in-comment citation: I1=0  I2=0  I3=1  I4(join-aware)=1
synthetic SINGLE-line citation:        I1=1  I2=1  I3=1  I4=0
re.fullmatch(r'[ \t]+', '\n') -> False        re.fullmatch(r'\s+', '\n') -> True
```

Readings, case-insensitive, over the reconstructed pre-edit copy (built in a scratch path outside the repo by deleting the two nine-character insertions), the current file, and `HEAD`:

| Class | pre-edit (I1/I2/I3) | current (I1/I2/I3) | `HEAD` (I1/I2/I3) |
| --- | --- | --- | --- |
| `spec-028` | 2 / 2 / 2 | **4 / 4 / 4** | 2 / 2 / 2 |
| `spec-028 Decision N` | 1 / 1 / 1 | **3 / 3 / 3** | 1 / 1 / 1 |
| `Decision\|DoD N`, total | **3 / 3 / 3** | **3 / 3 / 3** | 3 / 3 / 3 |
| ... NOT preceded by `spec-NNN` | **2 / 2 / 2** | **0 / 0 / 0** | 2 / 2 / 2 |
| join-aware wrapped `spec-028` joins | 0 | **0** | 0 |

**Total `Decision N` unchanged at 3 while the bare subset goes 2 -> 0 is the proof: the two citations were qualified, not supplemented.** A third citation would read 3 -> 4 and does not. The reconstruction's byte delta is **exactly 18 = 2 x 9** (34,935 -> 34,917), which independently forecloses any other wording drift in the file. `HEAD` reads identically to the reconstruction at every class, so Slice 2 added no `spec-028` token to this file and both deltas are wholly this cohort's.

**Worker 2's and Worker 3's fifth blind spot reproduces on my instrument too**, which is why the routed clause is a real gap rather than a rationalization: I2 reads **0** on a citation wrapped inside a `#` comment, because the continuation `#` lands between the halves and defeats a `\s+`-only flatten. Only I3 (which collapses the continuation marker first) and the join-aware form see it.

### Claim 2 — both citations resolve, and to the subjects they claim

Checked by reading the **rewritten** spec, because this cycle has already caught a citation that resolved while describing the wrong thing.

- `### Decision 5 — `Ordering` enum and argument shape` at spec line **438**, `grep -c '^### Decision 5 '` -> **1**. Its fenced block is the six-member enum with `ASC = "ASC"` through `DESC_NULLS_LAST = "DESC_NULLS_LAST"` — **member values equal to member names**, which is precisely what line 74 asserts and what line 62 twelve lines above already cites in the durable form.
- `### Decision 9 — Input-class namespace vs `TypeRegistry` and lifecycle` at spec line **641**, `grep -c '^### Decision 9 '` -> **1**. Its lifecycle bullet reads verbatim that `registry.clear()` **"leaves already-materialized module globals parked in `orders.inputs.__dict__`"** and that **"Parking is load-bearing"**, with the `delattr`-breaks-a-held-`LazyType` reason — the exact claim line 681's comment makes, in the spec's own vocabulary. The same Decision's `clear_order_input_namespace` bullet (e) restates it: the helper **"does NOT `delattr` materialized module globals"**.

Both anchors exist exactly once and each owns the claim made against it. All 13 `### Decision N` headings are present.

### Claim 3 — zero executable change, on two instruments falsified on six controls

Instruments written independently this pass: **A** = `ast.dump` after deleting every module/class/function docstring node (structure; blind to a moved non-docstring literal); **B** = `tokenize` stream with `COMMENT` / `NL` / `NEWLINE` / `INDENT` / `DEDENT` dropped and **only statement-position** `STRING` tokens collapsed, every other literal kept verbatim. Baselines extracted read-only with `git show <ref>:<path>` into a scratch path **outside** the repository; no `git stash` / `checkout` / `restore` / `worktree` at any point in this pass.

```
A=SAME  B=SAME   HEAD (5447c9eb) vs working tree
A=SAME  B=SAME   5c6fdd71        vs working tree
A=SAME  B=SAME   reconstructed pre-edit copy vs working tree
READINGS: 6  MISMATCHES: 0
```

Falsified on **six** controls, each applied to a scratch copy under an `assert mut != base` so a control that did not mutate cannot masquerade as a passing proof — Worker 2's BSD-`sed` lesson, adopted:

| Control | A | B | Proves |
| --- | --- | --- | --- |
| c1 line-74 docstring replaced wholesale | SAME | SAME | a docstring edit is invisible to both — this pass's shape 1 |
| c2 line-681 comment replaced wholesale | SAME | SAME | a comment edit is invisible to both — this pass's shape 2 |
| c3 `==` flipped to `!=` | DIFFERENT | DIFFERENT | an executable-token change is caught |
| c4 non-docstring literal `"ASC_NULLS_FIRST"` edited | DIFFERENT | DIFFERENT | B is not collapsing every string |
| c5 redundant parentheses added | SAME | **DIFFERENT** | **A and B disagree — two instruments, not one written twice** |
| c6 two statements reordered | DIFFERENT | DIFFERENT | ordering is caught, so `ast.dump` is not order-blind |

Every control landed on its expected pair, c5 included. **The entitlement is proved, not asserted**, and it is what licenses skipping the boundary machinery for this cohort.

### Low 1 — adopted: the dispatch's description of line 516 is false, and the conclusion is unaffected

Confirmed on my own reading. `tests/orders/test_inputs.py:516` is `::test_clear_order_input_namespace_leaves_module_globals_parked` (AST-resolved), whose docstring reads `"""The materialized class stays on the module dict per spec-028."""` — the **same** parked-globals subject as line 681, not "a different topic" as [`bld-integration-028.md`][bld-integration] `### X3` and [`build-028-orders-0_0_8.md`][build-028] `### Integration-pass consolidation cohort, 2026-08-20` both say.

**The record is corrected here and the finding is untouched, by a stronger route than the one the dispatch used:** line 516 carries **no Decision number at all**, so it could never have been the antecedent for a bare `Decision 9` whatever its topic. Distance was never load-bearing; the absence of a number is. This is the cycle's dominant defect class one more time — a true finding carried by a false description — and it is corrected rather than routed because the sentence is in documents this pass and the plan's author own.

### Low 2 — adopted and catalogued: line 516's own `spec-028` names no Decision

Confirmed: `per spec-028` with no Decision anchor, where the content it asserts is Decision 9's parking clause. It is **not** a bare `Decision N` site, so it sits outside the dispatched class, and qualifying it would **add** a citation — the file's `Decision N` total would read 3 -> 4, which is the exact reading Claim 1 exists to detect. **Correctly left byte-identical.** Routed to `bld-final-028.md`'s `### Deferred work catalog` as the adjacent class: an under-specified `spec-NNN`-without-Decision reference, a one-word change to `per spec-028 Decision 9` for whichever future pass owns that class.

### Ruling — the escalated `tests/orders/test_finalizer.py` site: DEFERRED, and here is the discriminator so it is not re-fought

Worker 3 escalated `tests/orders/test_finalizer.py` #"Decision 6 -- first-bind model compatibility" as structurally the same shape as line 681, and warned that "2 of 18" invites the wrong conclusion at family scope. Worker 0 answered with a whole-population measurement keyed on anchor presence. **I confirm the measurement, refine it in two places, and adopt the disposition.**

**The sites, read directly.** `tests/orders/test_finalizer.py` is 729 lines and carries three `spec-028` anchors (10, 112, 590) and two unprefixed `Decision 6` occurrences: line **14** (`Per Decision 6 second paragraph …`, four lines under line 10's `per spec-028` inside the same module docstring) and line **432** (`# Decision 6 -- first-bind model compatibility`, a section banner whose nearest earlier `spec-028` token is line 112, 320 lines up, with the full form at 590, 158 lines below). Worker 3's description of both sites is exact.

**Worker 0's measurement, re-derived on my own instrument:**

| Reading | Worker 0 | This pass | Verdict |
| --- | --- | --- | --- |
| unprefixed `Decision N` / `DoD N`, tree-wide `.py` | 442 | **442** for package + tests + examples; **443** including one occurrence in `docs/review/temp-tests/_request_body/baseline_request_body.py` | **confirmed — the one-occurrence gap is a CORPUS difference, not a digit.** Worker 0's corpus (first-party source and test trees) is the right one; a prior review cycle's scratchpad `.py` is not source |
| of those, in a file carrying **no** `spec-NNN` anchor anywhere | 16 | **16** | **confirmed** |
| per-file split of those 16 | `permissions.py` 7, + 5 files | **`permissions.py` 8**, `optimizer/hints.py` 1, `management/commands/inspect_django_type.py` 1, `tests/optimizer/test_selections.py` 1, `tests/test_apps.py` 3, `examples/fakeshop/apps/products/filters.py` 2 | **total right, one digit one low.** Worker 0's own list sums to **15** against its stated 16; `permissions.py` carries 8 occurrences over 8 lines (`grep -o` = `grep -c` here, so no line/occurrence collapse caused it). None is in the orders family — that half is confirmed |
| orders family | 2, both in `tests/orders/test_finalizer.py` (3 anchors) | **2** over `orders/**` + `tests/orders/**`; **3** if `utils/inputs.py` is counted in the family, which is Worker 3's scope and the extra is the integration pass's decided anaphora at `:1300` | **confirmed; 2-vs-3 is a family-boundary definition, not a disagreement.** Every other family file reads 0 unprefixed against 2-20 anchors, which I re-derived per file |

**One refinement that matters more than any of the digits, and it strengthens the ruling rather than weakening it.** The 442 is a **line-scoped** reading, and 58 of those 442 are not unprefixed at all — they are spec-qualified citations **wrapped across two source lines**, with the qualifier ending one line and `Decision N` opening the next. Credited, the genuine tree-wide unprefixed population is **384**:

```
unprefixed Decision/DoD N, package + tests + examples .py
  line-scoped        = 442
  plain \s+ flatten  = 399   (43 wrapped qualifiers credited)
  join-aware flatten = 384   (58 wrapped qualifiers credited)
  the #-comment-continuation blind spot = 15 further sites, invisible to a plain flatten
```

The 15-site gap between the two flattens is the same `#`-continuation blind spot Worker 2 measured and Worker 3 reproduced, now measured tree-wide; the 43 is consistent with Worker 3's Slice-2 pass-2 count of 49 for the neighbouring `spec-NNN <Heading>` class under a plain flatten. **None of the 58 is in the orders family** (heaviest: `mutations/sets.py` 5, `testing/client.py` 4, `tests/test_routers.py` 3, `auth/mutations.py` 3), so the family's 2 are genuinely unprefixed and Worker 0's family reading is untouched.

**Ruling: deferred, and the discriminator is not distance.** Worker 0's position is adopted with its reason sharpened, so the next reader inherits a test rather than a judgement:

> **A bare `Decision N` is a defect when nothing a reader passes on the way to it establishes the spec. It is anaphora when something does.** At line 681 the file's only two `spec-028` tokens were line 62 — a *sibling test's* docstring twelve lines up, which a reader lands on only by chance — and line 516, which carries no Decision number and so could not be an antecedent at any distance. At `test_finalizer.py:432` the antecedent is the **module docstring**, lines 10 and 14, which names both `spec-028` *and* `Decision 6` in the file's first fourteen lines and which no reader of the file bypasses. That is a structural difference, not a distance quibble: 320 lines of *file* is not 320 lines of *reading order* when the antecedent is the module's own opening. The same test disposes of `utils/inputs.py:1300` (three lines under the full form) identically, which is why the integration pass's decision to leave it was right.

Three further grounds, each measured rather than asserted:

1. **The class is a repo-wide convention, not an orders defect.** 384 genuine unprefixed occurrences tree-wide against **0** in the orders family's production modules and test files other than `test_finalizer.py`. Qualifying the family further would diverge it from every other subsystem — the opposite of the consistency this cohort was dispatched for.
2. **The 16 anchorless-file occurrences are other cards' surfaces** (`permissions.py`, `optimizer/hints.py`, `inspect_django_type.py`, `tests/optimizer/test_selections.py`, `tests/test_apps.py`, `products/filters.py`). A worker qualifying them would be asserting contracts this cycle never verified — the same ground that fenced the connection and relay registry twins and the four lowercase `spec Decision N` sites below.
3. **The distance-based reading condemns every long file and clears nothing.** It makes `test_finalizer.py:432` a defect and `utils/inputs.py:1300` not one on a threshold nobody has set, and it would re-open at the next long file. The anchor-based reading is decidable from the file alone.

Worker 3's warning about "2 of 18" is correct and is why this ruling is written at family scope rather than file scope: **at file scope the class is 0; at family scope it is 2, and both are anaphora under the test above.** Catalogued for `bld-final-028.md` with the 442 / 384 / 16 / 2 measurement attached, so the next reader re-derives the *measurement* and not the *ruling*.

### Slice-local checks run by this pass

| Check | Reading |
| --- | --- |
| bare in-family `Decision N` in `tests/orders/test_inputs.py` | **0** on three instruments (was 2); total `Decision N` **3**, unchanged |
| reconstruction byte delta | **18** = 2 x 9 |
| zero-executable-change | 2 instruments x 3 baselines = **6 readings, 0 mismatches**; 6 controls, all on their expected pair |
| both citation targets resolve, and to their claimed subjects | `### Decision 5` spec:438 (x1), `### Decision 9` spec:641 (x1); parking-is-load-bearing verbatim |
| wrapped `spec-028` joins in the file | **0**, join-aware probe with the `\n` inside the pattern |
| `spec-028 #"substring"` citations in the file | **0** before, **0** after |
| bare `[Ss]pec (Decision\|DoD\|Edge) N`, tree-wide, case-insensitive | **5** — `tests/types/test_relay_interfaces.py:371` (`spec-015`, capital) plus four lowercase in other cards' files (`filters/factories.py:143`, `list_field.py:192`, `tests/test_list_field.py:206`, `tests/types/test_resolvers.py:785`). Unchanged by this pass; Worker 2's case-insensitive re-measure of the dispatch's "baseline 1" is confirmed |
| `uv run python scripts/check_citations.py` | `OK: 782 citations resolve (705 in 422 .py files, 77 in KANBAN.md)`, **exit 0** — correctly flat: both repairs add prose refs no gate resolves, and a fall would have meant breakage |
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-028-orders-0_0_8.md` | `OK: 44 terms - all have glossary entries and at least one spec link.` **exit 0** |
| `uv run python scripts/check_trailing_commas.py --check` (the sixteen + spec + rationale) | exit 0 |
| `uv run ruff format --check` / `ruff check` (the sixteen, never `.`, never `--fix`) | `16 files already formatted` / `All checks passed!` |
| `git diff --check` | exit 0 |
| focused collection, no `--cov*` | `uv run pytest tests/orders/test_inputs.py --no-cov --collect-only -q` -> **42 tests collected**, 0 errors; the file's AST carries 42 `test_*` functions and **no duplicate function name** |
| line lengths | line 74 = 81 columns, line 681 = 85; the file's only over-99 lines are 427 (104) and 922 (106), both Slice 2's and untouched |
| `review_inspect.py` | Worker 3's skip confirmed: the trigger is quoted verbatim in its section, the file is under neither `optimizer/` nor `types/`, no file was added, and **zero** logic lines changed (proved above, not estimated). No run owed, none performed |

No `pytest` beyond the collection check, **no `--cov*` flag in any command in this pass**, no `.py` edited, no spec or rationale edit, no commit, no branch, no amend.

### DRY check across this cohort and prior accepted slices

**No new duplication, and structurally none possible**: zero executable tokens changed, so there is no helper, constant, branch, or literal introduced to consolidate. Lines 62 and 74 now both cite `spec-028 Decision 5`; that is convergent **citation** between two sibling tests pinning two halves of one Decision (member set, member values) — the file's own durable convention and the axis the dispatch decided, not duplicated logic.

**The DRY existence challenge stays deferred and I do not reopen it.** Ruling 7's ground is untouched by this cohort: every resolution path changes executable statements and forfeits the zero-boundary entitlement four passes and now seven instruments rest on, and both halves sit outside the writable set.

### Spec changes made (Worker 1 only)

**None, and none owed.** `docs/SPECS/spec-028-orders-0_0_8.md` and its rationale companion closed `final-accepted` at Slice 3 and were **read-only** to this pass — both were read to verify the two citations' subjects, and Decision 9's parking clause was read at source rather than quoted from a prior artifact. Nothing this pass measured is a spec defect: both cited anchors exist exactly once and own their claims, and no Slice-3 re-loop is needed.

Per-spawn status-line re-verification done: spec lines 1-8 read as a shipped-state record, `CHANGELOG.md` carries the Ordering Added and Changed bullets under `## [0.0.8] - 2026-06-03` with **no `[Unreleased]` heading**, `docs/GLOSSARY.md`'s Index reads `shipped (0.0.8)` for all five Ordering symbols, and the rationale-companion pointer resolves on disk. Nothing this cohort landed falsifies any of it. **No spec edit.**

**Deferral reasons for boxes left `- [ ]`: none.** Both boxes are `- [x]` and both ticks were re-derived above.

**Carried to `bld-final-028.md` `### Deferred work catalog`,** stated so the next reader can act without re-deriving:

1. **`tests/orders/test_inputs.py:516`'s `per spec-028` names no Decision** where the content it asserts is Decision 9's parking clause. Not a bare `Decision N`, so outside the dispatched class; qualifying it would take the file's `Decision N` total 3 -> 4. One-word change to `per spec-028 Decision 9` for whichever future pass owns the under-specified `spec-NNN`-without-Decision class.
2. **The four lowercase `spec Decision N` sites naming other cards' decisions** — `django_strawberry_framework/filters/factories.py:143` (cookbook `get_filterset_class` name-collision note, filter side), `django_strawberry_framework/list_field.py:192` and `tests/test_list_field.py:206` (the `DjangoListField` async-detection asymmetry), `tests/types/test_resolvers.py:785` (the `router.db_for_read` mock pattern). Plus the capital-`Spec` `spec-015` site at `tests/types/test_relay_interfaces.py:371`, which carries its own spec id and is correct. **The class is 5 case-insensitively and 1 under a capital-only pattern** — the same case door that under-read Slice 3's protect-list 3.3x. None is in the orders family; respelling any would be a worker asserting another card's contract. Pairs with the `check_citations.py` gate-extension card: the clause that resolves `spec-NNN Decision N` is the clause that flags `spec Decision N` naming no spec.
3. **Gate-extension clause: the flattened probe must collapse `\n[ \t]*#?[ \t]*`, not merely `\s+`, or a citation wrapped inside a `#` comment stays invisible to it.** Demonstrated by Worker 2, reproduced by Worker 3, and reproduced again on a third instrument by this pass; **measured tree-wide at 15 sites** that a plain `\s+` flatten cannot see (58 wrapped-qualifier sites join-aware vs 43 plain).
4. **Control-hygiene clause for the same card: every transient mutation control asserts that the text actually changed (`cmp` or an equality assert) before its reading is believed.** A BSD-`sed` control that silently applied nothing made both of Worker 2's identity instruments report `SAME` — a control that did not run reads identically to a passing proof. This is the `### What gets recorded` collection-error lesson in a new spelling. Applied as an `assert` in all six of this pass's controls.
5. **The anchor measurement behind the deferral ruling above**, so the residue cannot be re-fought as an open question: **442** line-scoped unprefixed `Decision N` / `DoD N` occurrences in package + tests + examples `.py` (**384** once wrapped qualifiers are credited, **443** if a prior cycle's `docs/review/temp-tests/` scratchpad is included); **16** in files carrying no `spec-NNN` anchor anywhere, none in the orders family, `permissions.py` holding **8** of them; the orders family at **2** (both `tests/orders/test_finalizer.py:14` and `:432`, in a file with 3 `spec-028` anchors including two in its module docstring), or **3** counting `utils/inputs.py:1300`. Every other family file: 0 unprefixed against 2-20 anchors. The discriminator is the ruling's anchor-in-reading-order test, not distance.

### Final status

`final-accepted`.

Two boxes, two ticks, both re-derived from the current file. The repair is proved to have **qualified rather than added** — bare in-family `Decision N` 2 -> 0 on three provably-different instruments while the total holds at 3, with a reconstruction byte delta of exactly 18 — and both citations resolve to headings that exist exactly once and that carry, verbatim, the claims made against them. **Zero executable change holds on two instruments against three reference points, 6 readings and 0 mismatches, with six controls each asserting its own mutation landed and c5 proving the two instruments disagree** — so boundary count zero is confirmed and the failability re-run floor is empty **by entitlement, not by omission**. No hot-path number is owed and none is missing; floor-verification scope is `none`. Both gates green on their exit codes, ruff clean scoped to the sixteen, no collateral churn attributable to this cohort, no spec or rationale edit.

Both Lows are adopted as record corrections rather than looped, and the escalation is ruled **deferred** with the measurement and the discriminator attached. Five items routed to the deferred-work catalog. The integration pass may close.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

[artifact]: ARTIFACT.md
[bld-integration]: bld-integration-028.md
[build]: BUILD.md
[build-028]: build-028-orders-0_0_8.md

<!-- django_strawberry_framework/ -->

[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
