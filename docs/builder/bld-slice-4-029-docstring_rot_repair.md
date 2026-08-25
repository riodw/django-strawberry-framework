# Build: Slice 4 — Docstring-rot repair in `types/base.py`

Spec reference: none. `DONE-029-0.0.9`'s spec has no `## Slice checklist` bullet for this slice — it
was added mid-cycle and its charter is `docs/builder/build-029-consumer_dx_cleanup-0_0_9.md`
`## Slice 4 added mid-cycle (Worker 0, 2026-08-25) — docstring rot in types/base.py`. The spec is
still read here, as the contract the repaired docstrings must agree with (see
`### Docstring-to-spec agreement map`).
Status: final-accepted

## Plan (Worker 1)

### What this slice is

Two docstrings in `django_strawberry_framework/types/base.py` make claims that are false about the
code they sit on. **The fix is the comment, never the code.** No rejection rule is missing, no
ordering is wrong, and no behavior change is proposed — reordering a live loop to match a wrong
comment would be the tail wagging the dog.

**Zero executable-line changes. If the diff contains one, the slice is wrong.**

### Both defects re-derived from source at plan time

Worker 0 verified both before opening the slice; every finding handed to a worker in this cycle has
been a hypothesis, so both were re-derived here independently, against source, not against the
hand-down.

**Defect 1 — `types/base.py::_selected_meta_targets` names 2 of its 3 callers.**

Its docstring (`types/base.py::_selected_meta_targets` #"The first half shared by") reads:

```
    The first half shared by ``_validate_nullability_override_targets`` and
    ``_validate_relation_shape_targets`` (spec-029 / spec-032 Decision 7-8):
```

Call sites, enumerated by grep over the whole repo rather than counted
(`grep -rn "_selected_meta_targets" --include="*.py" .`) — every occurrence is in
`django_strawberry_framework/types/base.py`, and there is **no** call site outside it:

| line | site | kind |
|---|---|---|
| 1421 | `def _selected_meta_targets(` | definition |
| 1514 | inside `types/base.py::_validate_nullability_override_targets` | **call** |
| 1590 | inside `types/base.py::_validate_filesystem_path_targets` | **call** |
| 1655 | inside `types/base.py::_validate_relation_shape_targets` | **call** |
| 979 | inside `types/base.py::_format_unknown_fields_error`'s docstring | prose reference |
| 1426, 1427, 1563 | prose references inside sibling docstrings | prose reference |

Three callers; the docstring names two. `_validate_filesystem_path_targets` (`spec-048` Decision 2,
`Meta.filesystem_path_fields`) is the one omitted. **Confirmed.**

Corroborated independently by two sources that are already correct and complete:

- `types/base.py::_format_unknown_fields_error`'s own docstring enumerates all three families —
  `Meta.nullable_overrides`, `Meta.required_overrides`, `Meta.filesystem_path_fields` **and**
  `Meta.relation_shapes` — so the module's convention is a complete enumeration, and this is a rot
  instance rather than a house style.
- The rationale companion's `## Decision 8` entry records the arrival order explicitly:
  `Meta.relation_shapes` was the second key, and "``Meta.filesystem_path_fields``
  (``DONE-048-0.0.14``…) became the **third** caller." The docstring was written when there were two
  and was never updated when the third landed.

**Defect 1b — the SAME omission, a second time, in the same docstring.** Re-derivation found a site
Worker 0's hand-down did not name. Four lines below the caller list, the same docstring enumerates
the per-name checks the callers keep:

```
    domain-specific per-name checks (consumer-authored, non-relation, Relay-pk,
    many-side) stay in the caller, which iterates the returned names.
```

`many-side` is `_validate_relation_shape_targets`'s check; `consumer-authored` / `non-relation` /
`Relay-pk` are `_validate_nullability_override_targets`'s. `_validate_filesystem_path_targets`'s own
per-name check — `_field_output_type_for(selected_by_name[name]) is None`, i.e. "not a FileField or
ImageField column" — is **absent from the list**. This is the identical false-by-omission claim about
the identical third caller, in the identical docstring, so it is repaired under Defect 1 rather than
recorded as a separate finding. It is not scope expansion: leaving it would fix one sentence of a
two-sentence claim and leave the docstring still telling the reader the seam has two consumers.

**Defect 2 — `types/base.py::_validate_nullability_override_targets`'s stated check order contradicts
its own loop.**

Docstring (`types/base.py::_validate_nullability_override_targets` #"Check order: unknown"):

```
    Check order: unknown -> excluded -> (consumer-authored / relation / Relay-pk).
```

Loop body, read in source order (`types/base.py::_validate_nullability_override_targets`, the
`for name in sorted_targets:` block):

| order | guard | anchor |
|---|---|---|
| 1 | consumer-authored | `if name in consumer_authored_fields:` |
| 2 | **Relay-suppressed pk** | `if name == relay_pk_name:` |
| 3 | **relation** | `if selected_by_name[name].is_relation:` |

Stated `consumer-authored / relation / Relay-pk`; runs `consumer-authored -> Relay-pk -> relation`.
The parenthetical grouping softens the claim but the sentence is introduced by "Check order:", so the
order it lists is the order it asserts. **Confirmed.**

The discrepancy is load-bearing rather than cosmetic: the two guards are reachable by one name (a
relation pk, e.g. `OneToOneField(primary_key=True)`, on a Relay-shaped type), and which one runs
first decides **which error message the consumer sees**. The spec states this explicitly as a
contract (Decision 8 failure-mode rule 4). A reader who trusted the docstring would predict the
relation message and be wrong.

**Defect 2b — the same docstring's `Raises:` clause lists the two in the other order** (`… / a
relation field / the Relay-suppressed pk`). Not false — a `Raises:` enumeration is a set, not an
order — so it is **not** a defect. It is nevertheless repaired, see
`### DRY / existence challenge` decision 2, because two enumerations of one rule in two orders inside
one docstring is the seed of exactly the rot this slice exists to remove, and reordering it changes
no claim's truth value.

### The spec and the source do NOT disagree about HEAD

Asked explicitly by the dispatch. Re-derived: the spec's corrected wording and the shipped code agree
on every point, and the docstrings are the only surface that disagrees with either.

| Claim | Spec (Slice 3, current text) | Source at HEAD | Agree? |
|---|---|---|---|
| check order | Decision 8 stage 2 + DoD 11 + Slice-3 checklist bullet: "unknown / excluded / consumer-authored / Relay-pk / relation targets in that order" | `consumer-authored` → `relay_pk_name` → `is_relation` after the shared unknown/excluded half | **yes** |
| Relay-before-relation reason | Decision 8 rule 4: "checked **before** the relation rule, so a name that is both … is reported with the Relay reason" | the `if name == relay_pk_name:` block raises and returns before `is_relation` is read | **yes** |
| helper name | `_validate_nullability_override_targets` | same | **yes** |
| signature | "keyword-only — `model`, `selected_fields`, `consumer_authored_fields`, `relay_shaped`, `nullable_overrides`, `required_overrides` … takes `relay_shaped: bool` rather than a pre-computed pk name" | identical, `*`-only, `relay_shaped: bool`, derives `model._meta.pk.name` itself under `if relay_shaped` | **yes** |
| shared unknown/excluded half | Decision 8: "It lives in `…::_selected_meta_targets`, which … routes the unknown path through the shared `_format_unknown_fields_error`" | exactly that | **yes** |
| how many keys share it | Decision 8: "Every `Meta` key whose value is a set of field names on the type validates through it — the two override keys here, `Meta.filesystem_path_fields`, and `Meta.relation_shapes`" | three call sites, one per family | **yes** |

**So: no code finding, and no spec finding.** The whole divergence is source-comment-vs-reality, which
is what this slice repairs. Nothing here needs a spec edit, and this slice proposes none.

**Slice 3's spec text is provisional.** Slice 3 is `planned` and awaiting re-review while this plan is
written, and it owns `docs/SPECS/**`. Every spec quotation above is a reading of the working tree at
plan time, not of a settled file. It is cited by heading plus quoted substring, never by line number,
so a further Slice 3 edit that moves text does not break the citation. If Slice 3's re-review changes
any of the five order-stating passages, the integration pass — not this slice — re-checks the pair.

### Docstring-to-spec agreement map

The point of this table is that the integration pass can check the pair **mechanically** rather than
by impression. Each row: the sentence Worker 2 writes, and the spec passage it must agree with.
Spec passages are named by heading + quoted substring because Slice 3 is still moving the text.

| # | Docstring sentence (after repair) | Spec passage it must agree with |
|---|---|---|
| A1 | `_selected_meta_targets`: "The unknown/excluded half shared by every ``Meta`` key whose value is a set of field names on the type" | `## Decision 8`, the paragraph opening **"That unknown/excluded half is shared, not per-key."** — #"Every `Meta` key whose value is a set of field names on the type validates through it" |
| A2 | `_selected_meta_targets`: the per-name remainder list, now five entries incl. `file/image column` | same paragraph, #"each caller keeps only its own per-name rules"; and the three callers' own rejection sets — `_validate_nullability_override_targets` (consumer-authored / Relay-pk / relation), `_validate_filesystem_path_targets` (consumer-authored / not a file-or-image column), `_validate_relation_shape_targets` (non-relation / single-valued / consumer-authored) |
| A3 | `_selected_meta_targets`: the citation `(spec-029 Decision 8 / spec-032 Decision 7 / spec-048 Decision 2)` | the three callers' own docstring citations, which already name exactly these three Decisions |
| B1 | `_validate_nullability_override_targets`: "Check order: unknown -> excluded -> consumer-authored -> Relay-pk -> relation." | `## Definition of done` item 11 — #"unknown / excluded / consumer-authored / Relay-pk / relation targets in that order"; and `## Slice checklist` Slice-3 bullet — #"to reject unknown / excluded / consumer-authored / Relay-pk / relation targets, in that order"; and `## Decision 8` stage 2 — #"for every unknown / excluded / consumer-authored / Relay-suppressed-pk / relation target" |
| B2 | `_validate_nullability_override_targets`: the Relay-precedes-relation reason clause | `## Decision 8` failure-mode rule 4 — #"It is checked **before** the relation rule, so a name that is both" |
| B3 | `_validate_nullability_override_targets`: the `Raises:` enumeration order | `## Definition of done` item 11, same order as B1 |

### Verification: the obligation is the INVERSE of a failability proof

**Failability proofs: `none`, decided, not omitted.** `BUILD.md` `## Failability proofs` `### What
needs a proof, and what does not` exempts this explicitly: proofs are "required for every **new
boundary, guard, gate, or rejection path** a slice introduces" and "**not** required for … doc
edits". This slice introduces no boundary and changes no branch. A manufactured proof for a comment
is the ritual that makes the real ones unaffordable.

**What is owed instead** is `BUILD.md` `## Claims are proven mechanically, never accepted on prose`,
third shape, "relocated, promoted, or carried over unchanged": the claim "the executable code is
unchanged" is exactly the cheapest claim in this build, and it must be **proved by an
executable-token comparison against pristine HEAD, comments and docstrings stripped**, which must come
back identical.

#### The instrument, exactly

Worker 2 writes this file to a scratch path **outside the repository** and runs it. Reproduced in
full so it does not have to be reinvented; it was **written and controlled at plan time** and the
control results below are measurements, not predictions.

```python
"""Prove two Python files are executably identical once comments+docstrings are stripped.

Usage: python ast_identity.py <reference.py> <candidate.py> <anchor-symbol> [<anchor-symbol> ...]
Exit 0 = executably IDENTICAL, exit 1 = DIFFERENT, exit 2 = instrument aborted.
"""

import ast
import hashlib
import sys

DOC_OWNERS = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)


def strip_docstrings(tree):
    for node in ast.walk(tree):
        if not isinstance(node, DOC_OWNERS):
            continue
        body = getattr(node, "body", None)
        if not body:
            continue
        first = body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            node.body = body[1:]
    return tree


def dump(path):
    src = open(path, encoding="utf-8").read()
    tree = strip_docstrings(ast.parse(src))
    return ast.dump(tree, include_attributes=False, indent=None)


def main():
    ref_path, cand_path, *anchors = sys.argv[1:]
    if not anchors:
        print("ABORT: at least one anchor symbol is required")
        return 2
    ref, cand = dump(ref_path), dump(cand_path)
    for blob, label in ((ref, "reference"), (cand, "candidate")):
        if len(blob) < 1000:
            print(f"ABORT: {label} dump is implausibly small ({len(blob)} chars)")
            return 2
        for anchor in anchors:
            if blob.count(f"'{anchor}'") == 0:
                print(f"ABORT: anchor {anchor!r} absent from {label} dump")
                return 2
    print(f"reference  {ref_path}  sha256={hashlib.sha256(ref.encode()).hexdigest()[:16]}  chars={len(ref)}")
    print(f"candidate  {cand_path}  sha256={hashlib.sha256(cand.encode()).hexdigest()[:16]}  chars={len(cand)}")
    if ref == cand:
        print("RESULT: executably IDENTICAL (comments and docstrings stripped)")
        return 0
    print("RESULT: DIFFERENT")
    for i, (a, b) in enumerate(zip(ref, cand)):
        if a != b:
            print(f"  first divergence at char {i}: ...{ref[max(0, i - 90):i + 90]!r}")
            print(f"                          vs ...{cand[max(0, i - 90):i + 90]!r}")
            break
    return 1


sys.exit(main())
```

Why AST and not `diff`/`wc`: `ast.dump(..., include_attributes=False)` drops line and column numbers,
so a docstring rewrite that shifts every following line produces no false difference; comments are
invisible to the parser; the docstring stripper removes the one string form a docstring edit changes;
and **every other** string literal, argument, branch and expression stays in the dump, so an
executable edit anywhere in the file still fires.

The four anchors it must be given: `_selected_meta_targets`,
`_validate_nullability_override_targets`, `_validate_filesystem_path_targets`,
`_validate_relation_shape_targets`. The anchor check exists for the same reason
`BUILD.md`'s failability loop puts its anchor check first: **nothing else in the loop can tell that
its own reference is wrong.**

#### The reference copy

`git show HEAD:django_strawberry_framework/types/base.py > <scratch-outside-repo>/base.HEAD.py`.
Never `git stash` / `git checkout` / `git restore` / `git worktree`, and never a scratch path inside
the tree.

Measured at plan time: **`django_strawberry_framework/types/base.py` is byte-identical to HEAD**
(`git status --short` does not list it; `diff` against the HEAD copy is empty). So pristine HEAD *is*
the pre-edit baseline for this file and no separate pre-copy is needed. **Worker 2 re-measures this
before its first edit** — a concurrent session's work is live in this tree (see the build plan's
`## Concurrent-session activity observed mid-cycle`), and if `base.py` is no longer HEAD-identical at
build time, Worker 2 stops and reports rather than editing.

#### Controlled in both directions — plan-time results

Five sweep instruments have died silently in this cycle and each was caught only by a positive
control. This one was controlled before being written into the plan. All four rows are runs, not
claims:

| Run | Candidate | Expected | Measured |
|---|---|---|---|
| identity | HEAD copy vs itself | exit 0 IDENTICAL | exit 0, `sha256=8382eb52608bb1a0`, 118250 chars |
| **negative control** | HEAD copy vs a copy with **only** the two defective docstring sentences reworded | exit 0 IDENTICAL | exit 0, same `sha256=8382eb52608bb1a0` — proves the stripper is live and the comparison is not byte-naive |
| **positive control** | HEAD copy vs a copy with the `relay_pk_name` and `is_relation` blocks **swapped** — i.e. exactly the forbidden "fix the code to match the comment" | exit 1 DIFFERENT | exit 1, `sha256=5c5fed398dfc819e`, first divergence located at char 96924 inside the `If(test=Compare(left=Name(id='name'…` node |
| **anchor control** | HEAD copy vs itself, with a nonexistent anchor symbol | exit 2 ABORT | exit 2, `ABORT: anchor '_no_such_symbol_xyz' absent from reference dump` |

**One measurement from the positive control is worth carrying:** the swapped-branch copy has the
**same character count** as the original (118250 both). A length check, a `wc -c`, or a
"the diff is docstring-only, look at it" impression would all have passed it. Only the dump
comparison caught it.

Worker 2 re-runs all four rows against **its own** edited file (the positive and negative controls
rebuilt from its post-edit file, not copied from here) and records each exit code and hash in
`### Validation run`. A run of the identity row alone is not the obligation discharged: an instrument
that did not fire reads exactly like a passing proof.

### DRY / existence challenge

`BUILD.md`'s `!!IMPORTANT — DRY FIRST!!` puts "should this exist at all" in scope, and it lands
squarely on Defect 1: the sentence is wrong **because it is an enumeration**, and an enumeration that
must be updated whenever a fourth caller appears is a rot generator with no gate behind it. It has
already rotted once, in exactly that way, when `spec-048` added the third caller.

**Decision 1 — the corrected docstring states the seam's CONTRACT and drops the caller-function
enumeration entirely.** It does not simply gain a third name.

Reasoning, recorded so the next reader does not re-litigate it:

- **A closed list of three is wrong the day a fourth key lands, and nothing gates it.**
  `check_citations.py` resolves `path::Symbol` citations, not prose enumerations; no linter, no test,
  and no review step compares a docstring's caller list against `grep`. The failure mode is silent
  and has already occurred once.
- **The contract sentence carries the load-bearing fact better than the list does.** What makes the
  seam dangerous to change is that it is shared and open-ended. "Every ``Meta`` key whose value is a
  set of field names on the type" says that; "shared by A and B" says the opposite of it, which is
  precisely how the defect misleads.
- **The spec already states it this way**, and stating it identically is what makes row A1 of
  `### Docstring-to-spec agreement map` mechanically checkable rather than a matter of impression.
- **The docstring's closing paragraph already anticipates it** —
  #"Keeping the unknown-vs-excluded distinction here" ("… means a future ``Meta.*`` target feature
  inherits both guards", wrapped across two source lines, so cite the single-line fragment) — so the
  contract framing is the docstring's own, and the caller list was the inconsistent half.
- **A reader who wants the callers has a non-rotting instrument:** `grep -rn "_selected_meta_targets"`.
  A docstring that duplicates a grep result is a cache with no invalidation.

**Why the sibling `_format_unknown_fields_error` docstring is NOT changed to match.** It enumerates
its callers and is currently correct and complete (verified above). It is outside this slice's two
docstrings, changing it is not needed to make anything true, and `### Scope discipline` below governs.
Recorded as an observation, not dispatched: if it rots the same way, the same argument applies to it.

**Decision 2 — the `Raises:` enumeration (Defect 2b) is reordered to match the check order**, even
though it is not false. One docstring holding two enumerations of one rule in two different orders is
the exact seed of this slice's defect; the reorder asserts nothing new, changes no truth value, sits
inside a docstring already being rewritten, and additionally brings the clause into agreement with
spec DoD item 11 (row B3). Decided here rather than delegated, so Worker 2 does not have to guess
whether it is in scope.

**Decision 3 — no new helper, no new constant, no new module.** Nothing is extracted and nothing is
shared; the slice writes prose into two existing docstrings.

**Helper inventory checked — for the WHOLE package.** Refreshed at plan time via `BUILD.md`
`### Package-wide helper inventory before helper planning`'s AST script over
`django_strawberry_framework/` (1941 lines, `docs/shadow/helper-inventory.md`). Shapes searched:
`selected_meta`, `_format_unknown`, `_validate_.*targets`, `normalize_sequence`. Relevant candidates
found: the four symbols this slice reads —
`_normalize_sequence_spec(value, key)`, `_format_unknown_fields_error(*, model, attr, unknown,
available)`, `_selected_meta_targets(*, model, selected_fields, attr, targets, excluded_error)`, and
the three `_validate_*_targets` siblings — all in `django_strawberry_framework/types/base.py`, and no
near-duplicate of the shared-guard shape anywhere else in the package. **No helper is proposed and
none is warranted:** the condition that would change that answer is a fourth `Meta` key needing the
unknown/excluded half, which would call the existing `_selected_meta_targets` rather than justify a
new abstraction.

**Static inspection helper.** `scripts/review_inspect.py django_strawberry_framework/types/base.py
--output-dir docs/shadow` was run at plan time (`types/` is one of the two mandatory directories).
Emitted `docs/shadow/django_strawberry_framework__types__base.overview.md` and `.stripped.py`. Note
for Worker 3: the `.stripped.py` shadow replaces **every** string token with `...`, docstrings
included, so it is structurally blind to this slice's entire diff. It is useful here only as
corroboration that the executable structure is what the plan says it is — the AST instrument above,
not the shadow, is this slice's verification.

### Scope declarations

- **Hot-path declaration: `none`.** Comment-only; no executable line changes, so no operation gains
  cost. Stated explicitly so Worker 2 does not have to infer whether the silence is deliberate.
- **Floor-verification scope: `none`.** No Django / Strawberry / channels seam is touched, and a
  docstring cannot diverge across framework or interpreter versions. Nothing to run at the floor.
- **Failability proofs: `none`,** per `### Verification` above — decided and argued, not omitted.
- **Estimated new boundaries: zero.** No guard, cap, rejection path, or validation branch is added.

### Slice splitting — answered, not skipped

`BUILD.md` `### Slice splitting` asks for a decided answer and silence is not one, so: **one unit, no
split.** Both triggers point the same way. The boundary count is **zero**, far under the "roughly
five" prompt. The diff is two docstrings in one function-neighbourhood of one file, reviewable in a
single read. And the two defects are *one* decision, not two that happen to be adjacent: both are
false claims about the same three-caller seam, they are checked against the same spec Decision, and
both are proved by the same single instrument run. Splitting them would double the artifact and the
verification cost for a diff that is smaller than the artifact describing it.

### Implementation steps

Line numbers are pin-at-write-time navigational hints. Verify against the current source before
editing — this file is HEAD-clean at plan time but the tree carries a concurrent session's work.

1. **Pre-flight the file.** `git status --short -- django_strawberry_framework/types/base.py` must be
   empty, and `git show HEAD:django_strawberry_framework/types/base.py` diffed against disk must be
   empty. If not, **stop and report**; do not edit, do not revert (`AGENTS.md` rule 34).
   Write the HEAD copy to a scratch path outside the repo for step 6.

2. **Defect 1 + 1b — `django_strawberry_framework/types/base.py::_selected_meta_targets`, the second
   docstring paragraph** (currently lines 1426-1435, opening #"The first half shared by"). Replace
   the whole paragraph with:

   ```
       The unknown/excluded half shared by every ``Meta`` key whose value is a set
       of field names on the type (spec-029 Decision 8 / spec-032 Decision 7 /
       spec-048 Decision 2): reject names unknown to the model (via the shared
       ``_format_unknown_fields_error`` keyed on ``attr`` so the consumer-visible
       shape matches the ``Meta.fields`` / ``Meta.exclude`` typo guards), then
       reject names not in the selected set (via the caller's family-specific
       ``excluded_error``, which receives the sorted excluded names). Returns the
       ``{name: field}`` selected map and the sorted target names; the
       domain-specific per-name checks (consumer-authored, non-relation, Relay-pk,
       file/image column, many-side) stay in the caller, which iterates the
       returned names.
   ```

   Changes, and nothing else: the two-name caller enumeration becomes the contract statement
   (Decision 1); the citation gains `spec-048 Decision 2` and spells all three Decisions explicitly
   rather than as the range `Decision 7-8`; `file/image column` joins the per-name list (Defect 1b).
   The summary line and the closing `Keeping the unknown-vs-excluded distinction …` paragraph are
   **not** touched.

3. **Defect 2 — `django_strawberry_framework/types/base.py::_validate_nullability_override_targets`,
   the check-order paragraph** (currently lines 1485-1489, opening #"Check order: unknown"). Replace
   the whole paragraph with:

   ```
       Check order: unknown -> excluded -> consumer-authored -> Relay-pk ->
       relation. The last three operate on selected, known fields, so they run
       only after the first two have confirmed the name exists and is selected.
       Relay-pk precedes relation so a name that is both - a relation pk such as
       ``OneToOneField(primary_key=True)`` on a Relay-shaped type - is reported
       with the Relay reason rather than the relation one. Every failure raises
       ``ConfigurationError`` at type-creation time naming the offending field.
   ```

   The reason clause is not decoration: it is what makes the order non-arbitrary, and therefore what
   stops a future reader "tidying" it back. It restates spec Decision 8 rule 4 (row B2).

4. **Defect 2b — the same function's `Raises:` clause** (currently lines 1507-1509). Reorder the last
   two entries only:

   ```
       Raises:
           ConfigurationError: any target is unknown / excluded / consumer-authored
               / the Relay-suppressed pk / a relation field.
   ```

5. **ASCII and line length.** `AGENTS.md` rule 17: `.py` source is **ASCII-only**, enforced by
   `scripts/check_trailing_commas.py`. A docstring rewrite is exactly where a curly quote, an em-dash,
   an ellipsis character, or a `->` typed as an arrow glyph gets introduced — every dash above is a
   plain hyphen and every arrow is `->` by design. Line length 99 (E501 graced to 110); **the
   formatter does not reflow docstring prose**, so the wrapping above is Worker 2's to preserve, not
   ruff's to fix. Verify with:

   ```shell
   uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/types/base.py
   ```

   Non-ASCII is **gated** (the run exits 1) but is **never auto-fixed** — `--fix` will not repair it —
   so a `--fix` run that prints a non-ASCII line and then reports success on the other three checks is
   not a pass. Read the output, not only the exit code.

6. **Run the AST identity instrument and all four control rows** per `### Verification` above, and
   paste every exit code and hash into `### Validation run`. The identity row alone is not the
   obligation discharged.

7. **Ruff, scoped to this pass's own file** (`ARTIFACT.md` `### Validation run` — never `.`, because
   a repo-wide write-mode run would rewrite a concurrent session's files):

   ```shell
   uv run ruff format django_strawberry_framework/types/base.py
   uv run ruff check --fix django_strawberry_framework/types/base.py
   ```

   Then `git status --short`: the only file this pass may have modified is
   `django_strawberry_framework/types/base.py` (plus this artifact). Anything else is a
   **stop-and-report**, never a revert.

8. **If ruff reformats anything, re-run step 6.** The instrument must be the last word on the file.

### Test additions / updates

**None, and this is a decision rather than an omission.** No test is added, updated, or run for
behavior, because no behavior changes — that is the slice's entire claim, and step 6's instrument is
what proves it. A test asserting the text of a docstring would be a test of this pass's typing, would
pin prose against future improvement, and would itself become the next thing to rot.

No temp tests under `docs/builder/temp-tests/<slice>/` are warranted; nothing here needs a
demonstration that an existing assertion is non-distinguishing.

`AGENTS.md` rule 15 stands: no `pytest` after edits unless asked. If a focused run is wanted for
reassurance, `uv run pytest tests/types/test_base.py --no-cov` is the neighbourhood — **never** with
any `--cov*` flag (`--no-cov` is the only permitted coverage-shaped flag; `pytest.ini`'s `addopts`
auto-applies `--cov`). It proves nothing this slice claims and is not required by this plan.

### Scope discipline — this is a two-docstring repair

Stated here so **Worker 2 cannot read the slice as an invitation to re-audit
`django_strawberry_framework/types/base.py`.** The file is 1950 lines and densely commented; it will
offer more.

- The writable surface is the two docstrings named in steps 2-4. Nothing else in the file.
- **Any further defect found in `types/base.py` is RECORDED in this artifact under
  `### Notes for Worker 1 (spec reconciliation)`, not fixed** — with its symbol-qualified path and
  what is false about it, so the deferred catalog in `bld-final-029.md` can pick it up.
- Defect 1b and Defect 2b are inside scope not because they were found, but because they are the same
  two claims: 1b is the identical omission of the identical third caller in the identical docstring,
  and 2b is the second enumeration of the rule Defect 2 corrects. A finding that needs an argument
  beyond "this is the same sentence" is out.
- No executable line. No import. No signature. No test. No spec file — `docs/SPECS/**` is Slice 3's
  and is being edited concurrently.

### Implementation discretion items

Assessed and decided to be Worker 2's:

- **Exact line-wrapping** of the three replacement blocks, within the 99-char limit. The prose is
  fixed; where the line breaks fall is not.
- **The scratch filenames and directory** used for the HEAD copy, the instrument, and the two control
  copies — any path outside the repository.
- Whether to build the two control copies with a small Python snippet or by hand, provided each
  control is rebuilt from Worker 2's **own post-edit file** and its exit code recorded.

Not discretionary, and not delegated here: whether to enumerate callers (Decision 1), whether the
`Raises:` clause moves (Decision 2), and the check order itself, which is the code's and is not
changing.

### Spec slice checklist (verbatim)

`DONE-029-0.0.9`'s spec has no `## Slice checklist` bullet for Slice 4 — it was added mid-cycle — so
the boxes below are the sub-checks Worker 2 must land, quoting the charter in
`docs/builder/build-029-consumer_dx_cleanup-0_0_9.md` `## Slice 4 added mid-cycle` verbatim where it
states a contract. Boxes stay `- [ ]` at planning; Worker 2 ticks only what lands in its diff; Worker
1 audits every tick at final verification.

- [x] `types/base.py::_selected_meta_targets` no longer "names 2 of its 3 callers": the docstring's
      caller claim is corrected per Decision 1, so it no longer "tells the next reader a seam has
      fewer consumers than it does".
- [x] The same docstring's per-name-check list names `_validate_filesystem_path_targets`'s check
      (file/image column) alongside the other callers' (Defect 1b).
- [x] The same docstring's spec citation names all three source Decisions
      (`spec-029 Decision 8 / spec-032 Decision 7 / spec-048 Decision 2`).
- [x] `types/base.py::_validate_nullability_override_targets`'s "stated check order" no longer
      "contradicts its own loop": it reads `unknown -> excluded -> consumer-authored -> Relay-pk ->
      relation`, the order the loop body runs.
- [x] That paragraph states why Relay-pk precedes relation, agreeing with spec Decision 8 rule 4
      (`### Docstring-to-spec agreement map` row B2).
- [x] The same function's `Raises:` enumeration lists the Relay-suppressed pk before the relation
      field (Decision 2).
- [x] "**The fix is the comment, never the code** … Plan for **zero executable-line changes**" — the
      AST identity instrument reports `RESULT: executably IDENTICAL` against pristine HEAD, with all
      four anchors present.
- [x] The instrument is **controlled in both directions** against Worker 2's own post-edit file: the
      negative control (docstring-only change) exits 0 and the positive control (branch swap) exits 1,
      both recorded with hashes.
- [x] `scripts/check_trailing_commas.py --check` passes on the edited file, with its output read for
      non-ASCII rather than only its exit code (`AGENTS.md` rule 17).
- [x] `uv run ruff format` / `uv run ruff check --fix` run **scoped to this pass's own file** and
      `git status --short` shows no file this pass did not intend.
- [x] "any further defect found there is **recorded in the artifact, not fixed**" — every further
      `types/base.py` defect observed sits under `### Notes for Worker 1 (spec reconciliation)` with
      a symbol-qualified path, and none is repaired.

### Notes for Worker 1 (spec reconciliation)

Recorded at planning; carried into final verification and the integration pass.

1. **Slice 4 falsifies a sentence in the rationale companion, which this slice may not edit.**
   `docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md`, `## Decision 8`, the final
   bullet, ends: #"The helper's own docstring still lists the three per-name rules in the rev1 order;
   that is a source-comment defect outside this cycle's editable surface and is routed to the final
   gate's deferred catalog." Once this slice lands, **all three clauses of that parenthetical are
   false**: the docstring no longer lists the rev1 order, the defect was inside the cycle's editable
   surface (the maintainer's fence is spec files and `.py` files), and it was repaired rather than
   deferred. The file is Slice 3's under the ownership partition and is being edited concurrently, so
   **this slice must not touch it.** Route: Slice 3's custodian pass, or the integration pass. This is
   the one place where the two concurrent slices' outputs actively contradict each other, and no gate
   will see it — `check_citations.py` is `path::Symbol`-only with `docs/` out of scope, and it is
   prose, so no link check sees it either.

2. **The corresponding `### Deferred work catalog` entry must not be written.** `bld-final-029.md`
   would otherwise carry these two docstring defects as deferred, on the strength of Slice 3's
   routing. They are shipped by this slice. Worker 1's final gate owns that catalog and should
   record them as *closed by Slice 4*, not deferred.

3. **No spec edit is proposed by this slice, and none is needed.** See `### The spec and the source
   do NOT disagree about HEAD`. Every spec passage read here was read in a working tree Slice 3 is
   actively editing, so all six rows of `### Docstring-to-spec agreement map` are provisional and are
   the integration pass's to re-check against the settled spec.

4. **Spec status-line re-verification (this spawn).** Read `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md`
   lines 1-9 (title, shipped-in banner, `Status:`, Owner, Predecessors, rationale-companion pointer).
   Nothing there is falsified by this build: the card is shipped, the `Status:` line is the
   completion source of truth, and the rationale-companion pointer resolves to a file that now
   exists (Slice 1 created it). **No edit needed, and none made** — the file is Slice 3's under the
   ownership partition regardless.

5. **Observation, not dispatched:** `types/base.py::_format_unknown_fields_error`'s docstring
   enumerates its callers and is currently complete and correct. It carries the same rot risk this
   slice's Decision 1 removes from `_selected_meta_targets`. Left alone under
   `### Scope discipline`; noted so a future pass has the argument already made.

---

## Build report (Worker 2)

### Files touched

- `django_strawberry_framework/types/base.py` — **docstrings only**, three blocks, all inside the two
  functions the plan names. `git diff --stat`: `1 file changed, 13 insertions(+), 10 deletions(-)`.
  - `types/base.py::_selected_meta_targets`, second docstring paragraph (was 1426-1435, now
    1426-1436): the two-name caller enumeration replaced by the seam's contract statement (plan
    Decision 1); citation now spells all three Decisions; `file/image column` added to the per-name
    check list (Defect 1b). The summary line and the closing
    #"Keeping the unknown-vs-excluded distinction here" paragraph are untouched, as the plan requires.
  - `types/base.py::_validate_nullability_override_targets`, check-order paragraph (was 1485-1489,
    now 1486-1492): order restated as `unknown -> excluded -> consumer-authored -> Relay-pk ->
    relation`, plus the reason clause for why Relay-pk precedes relation.
  - `types/base.py::_validate_nullability_override_targets`, `Raises:` clause (now 1511-1512): last
    two entries swapped so the Relay-suppressed pk precedes the relation field (plan Decision 2).
- `docs/builder/bld-slice-4-029-docstring_rot_repair.md` — this report, the eleven checklist ticks,
  `Status: built`.

**Both defects and both second sites were re-derived from source before any edit**, not taken from
the plan. `grep -rn "_selected_meta_targets" --include="*.py" .` returns six occurrences, all in
`django_strawberry_framework/types/base.py`: the definition (1416), **three** calls (1514 in
`_validate_nullability_override_targets`, 1590 in `_validate_filesystem_path_targets`, 1655 in
`_validate_relation_shape_targets`), and two prose references (979, 1563). No call site exists
outside the module. Defect 1b, Defect 2 and Defect 2b were each read against the loop body at
`types/base.py::_validate_nullability_override_targets` (`consumer_authored_fields` -> `relay_pk_name`
-> `is_relation`) before editing.

### Tests added or updated

**None, per the plan's `### Test additions / updates`** — a decision, not an omission. No behavior
changes; that is the slice's entire claim and the AST instrument is what proves it. A test asserting
docstring prose would pin this pass's typing and become the next thing to rot.

A focused sanity run was made anyway: `uv run pytest tests/types/test_base.py --no-cov -q` ->
**164 passed**. It proves nothing this slice claims and is recorded only as a no-surprise check.

### Validation run

Ordered as run.

**1. Pre-flight (plan step 1) — the file was HEAD-clean before the first edit.**

```shell
git status --short -- django_strawberry_framework/types/base.py   # empty
git show HEAD:django_strawberry_framework/types/base.py > <scratch-outside-repo>/base.HEAD.py
diff <scratch>/base.HEAD.py django_strawberry_framework/types/base.py   # empty, both 93972 bytes
```

Pristine HEAD is therefore the pre-edit baseline; no separate pre-copy was needed. Scratch root is
the session scratchpad **outside** the repository. No `git stash` / `checkout` / `restore` /
`worktree` was used at any point in this pass.

**2. Citation-rot sweep (the dispatch's named hazard) — before and after the edit.** A
`path #"unique substring"` citation into rewritten docstring text breaks silently; `check_citations.py`
is `path::Symbol`-only with `docs/` out of scope, so no gate sees it. Swept every `#"..."` citation in
the corpus `git ls-files --cached --others --exclude-standard` reports (693 files — the oracle was
asserted to name both this slice's target and this artifact, since `git ls-files` alone misses the
cycle's untracked artifacts) against the exact three text blocks being replaced:

- **citations resolving into a rewritten block: 4 occurrences, 2 distinct, all in this artifact** —
  `#"The first half shared by"` and `#"Check order: unknown"`, i.e. the plan quoting the defect it
  ordered repaired. They stop resolving by design, and `docs/builder/bld-*.md` is a per-cycle
  scratchpad exempt from the citation convention (`START.md` "Temp artifact conventions").
  **No standing doc, spec, or source file cites into any rewritten block.**
- **instrument liveness control:** the same sweep widened to the whole file finds **118** citations
  resolving into `types/base.py`, so a zero above is a measurement rather than a broken regex.
- Re-verified after the edit: `#"Keeping the unknown-vs-excluded distinction here"` (the plan's own
  citation into the paragraph deliberately left untouched) still resolves at exactly 1 occurrence.

**3. ASCII / layout gate, with a liveness control on this very file.**

```shell
uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/types/base.py
# no output, exit 0
```

Output read, not only the exit code (non-ASCII is gated but never auto-fixed). Independently
re-derived: **0 bytes > 127** in the edited file, and **0 lines over 99 chars introduced** (18 such
lines before and after, all pre-existing and inside the E501-to-110 grace).

The control matters because the first control attempted **did not run**: a copy planted at
`docs/builder/temp-tests/slice-4-029/ascii_control.py` returned
`excluded from the source-layout rules -- not checked`, exit 0 — a passing-looking non-run. The
control was therefore re-done as a transient mutation of the real file, which is in scope:

```shell
grep -c 'Check order: unknown -> excluded -> consumer-authored -> Relay-pk ->' <file>   # 1, before the copy
cp <file> <scratch>/base.postedit.py
# inject one U+2192 into the rewritten docstring line, then:
uv run python scripts/check_trailing_commas.py --check <file>
#   -> types/base.py:1486:26: non-ASCII U+2192 '→' not allowed in .py (ASCII + emoji only)
#      1 non-ASCII char(s) in .py; replace with ASCII (emoji allowed)   -- exit 1
cp <scratch>/base.postedit.py <file>
cmp <file> <scratch>/base.postedit.py      # exit 0 -- restore proved byte-identical
uv run python scripts/check_trailing_commas.py --check <file>   # exit 0
```

So the gate is demonstrably live on this file's docstrings, and the mutation is reverted and proved.

**4. The claim this slice actually owes: the executable bytes are unchanged.** Per `BUILD.md`
`## Claims are proven mechanically, never accepted on prose` ("relocated, promoted, or carried over
unchanged"). Instrument: the plan's `ast_identity.py`, written verbatim to a scratch path **outside**
the repo; both control copies rebuilt from **this pass's own post-edit file**, never copied from the
plan. Anchors: `_selected_meta_targets`, `_validate_nullability_override_targets`,
`_validate_filesystem_path_targets`, `_validate_relation_shape_targets`.

| Row | Candidate | Expected | Measured |
|---|---|---|---|
| **R0 — the claim** | pristine HEAD vs the post-edit working file | exit 0 IDENTICAL | **exit 0**, `sha256=8382eb52608bb1a0`, 118250 chars — identical to the reference's hash |
| R1 identity | HEAD vs HEAD | exit 0 | **exit 0**, `sha256=8382eb52608bb1a0` |
| R2 negative control | HEAD vs post-edit file carrying a **further** docstring-only reword | exit 0 (stripper is live) | **exit 0**, `sha256=8382eb52608bb1a0` — a 94233-byte file matching a 94227-byte one, so the comparison is not byte-naive |
| R3 **positive control** | HEAD vs post-edit file with the `relay_pk_name` and `is_relation` blocks **swapped** — the forbidden "fix the code to match the comment" | exit 1 DIFFERENT | **exit 1**, `sha256=5c5fed398dfc819e`, first divergence at char 96924: `If(test=Compare(left=Name(id='name'...comparators=[Name(id='relay_pk_name'` vs `If(test=Attribute(value=Subscript(value=Name(id='selected_by_name'` |
| R4 anchor control | HEAD vs post-edit file, bogus anchor | exit 2 ABORT | **exit 2**, `ABORT: anchor '_no_such_symbol_xyz' absent from reference dump` |

Every hash reproduces the plan's plan-time measurement exactly (`8382eb52608bb1a0` / `5c5fed398dfc819e`,
divergence at char 96924), which is an independent second reading of the same file at a different time.

**The measurement worth carrying:** `wc -c` on the post-edit file and on the branch-swapped positive
control is **94227 bytes both**, and their AST dumps are **118250 chars both**. Length is
non-distinguishing in both spellings; only the hash comparison separates them. A reviewer eyeballing
"the diff is docstring-only" would have passed R3.

One process note, because it is the exact failure mode the dispatch warned about: the first run of all
five rows **aborted at exit 2 on every row** — the four anchors had been shell-quoted into a single
argument. It was visible only because the instrument checks its anchors first and refuses rather than
comparing. Had the abort been silent, five green-looking rows would have been five non-runs. The rows
above are the corrected re-run.

**5. Ruff, scoped to this pass's own file** (never `.` — a repo-wide write-mode run would rewrite the
concurrent sessions' files):

```shell
uv run ruff format django_strawberry_framework/types/base.py   # 1 file left unchanged
uv run ruff check --fix django_strawberry_framework/types/base.py   # All checks passed!
```

Ruff reformatted nothing, so plan step 8's "re-run the instrument if ruff touches the file" did not
trigger; the read-only confirmations after the whole sequence are `ruff format --check` -> `1 file
already formatted`, `ruff check` -> `All checks passed!`, `git diff --check` -> exit 0.

**6. `git status --short` churn classification.** `django_strawberry_framework/types/base.py` is the
only file this pass modified. Every other entry is attributed by the build plan's `## Ownership
partition`, not by `git status`:

| Entry | Owner |
|---|---|
| `django_strawberry_framework/types/base.py` | **this slice** |
| `docs/SPECS/spec-029-…md`, `docs/SPECS/appx/spec-029-…-rationale.md`, `docs/SPECS/appx/spec-004-…-rationale.md` | Slices 1/3 — live and being edited concurrently |
| `tests/{forms,mutations,optimizer,types}/…`, `tests/test_relay_connection.py`, `tests/test_ci_governance.py`, `examples/fakeshop/strategy_schemas.py`, `examples/fakeshop/test_query/test_products_visibility_api.py` | Slice 2 |
| `docs/review/**`, `tests/mutations/test_operations.py` | unrelated concurrent session |
| `docs/builder/bld-slice-{1,2,3}-029-*.md`, `build-029-*.md` | other slices / Worker 0 |

Nothing was reverted or tidied. No stop-and-report condition arose.

### Failability proofs

**None; this pass introduced no new boundary.** Decided and argued, not omitted:
`BUILD.md` `### What needs a proof, and what does not` scopes proofs to "every **new boundary, guard,
gate, or rejection path** a slice introduces" and states they are "**not** required for … doc edits".
This pass adds no guard and changes no branch — R0 above is the mechanical proof of exactly that. A
manufactured proof for a comment is the ritual that makes the real ones unaffordable.

The obligation this slice does owe is the inverse one, and it is discharged in
`### Validation run` item 4 with all four control rows re-run against this pass's own post-edit file.
The two transient mutations this pass did make (the ASCII injection, item 3) were reverted inside the
same pass and proved by `cmp`; **no mutation is live at this `Status:` transition.**

### Hot-path budget

**Not applicable; plan declares no hot path.** Comment-only, zero executable-line changes (R0), so no
operation gained cost.

### Floor verification

**Not applicable; plan declares floor-verification scope `none`.** No Django / Strawberry / channels
seam is touched and a docstring cannot diverge across framework or interpreter versions. Nothing was
installed anywhere; the shared `.venv` was not mutated.

### Implementation notes

- **Line wrapping** (the plan's first discretion item) follows the plan's own blocks. The
  `_selected_meta_targets` paragraph gained one line (the added `file/image column` pushes the tail);
  the check-order paragraph gained two (the reason clause). The `Raises:` clause reflows nothing —
  only the two entries after the line break swap. **No untouched docstring line was reflowed**, which
  is what keeps the diff readable and keeps any `#"substring"` citation into the surrounding prose
  intact.
- **Control copies** (third discretion item) were built with a Python snippet asserting each anchor
  matched **exactly once** before substituting, and asserting the result differed from the input — so
  a control that silently failed to apply would abort rather than produce a passing row.
- **Both `Meta` sibling docstrings were checked for falsification by this diff and neither is
  affected.** `types/base.py::_format_unknown_fields_error` (#"which each of their validators calls")
  enumerates all four `Meta` key families and names no caller functions, so it corroborates the new
  "every ``Meta`` key whose value is a set of field names" framing rather than contradicting it;
  `types/base.py::_build_annotations`' comment #"(relation targets rejected) in" makes no order claim.
- **Minor nit in the plan's own call-site table, recorded for accuracy, not acted on.** The row
  "`1426, 1427, 1563` prose references inside sibling docstrings" is right about 1563 but 1426/1427
  are the *caller names* inside the docstring under repair, not occurrences of
  `_selected_meta_targets`. The load-bearing half of the table — one definition, **three** calls, no
  call site outside the module — re-derives exactly as the plan states.

### Notes for Worker 3

- **The diff is three docstring blocks and nothing else.** The AST identity row (R0) is the
  mechanical form of that claim; re-running it is one command and needs only
  `git show HEAD:django_strawberry_framework/types/base.py` into a scratch path outside the repo. The
  instrument source is reproduced verbatim in the plan's `#### The instrument, exactly`.
- **If you re-run the instrument, pass the four anchors as four separate arguments.** Collapsing them
  into one quoted string makes every row abort at exit 2 (see `### Validation run` item 4).
- **`docs/shadow/…types__base.stripped.py` is structurally blind to this entire diff** — it replaces
  every string token, docstrings included, with `...`. The plan already flags this; it is worth not
  spending a pass on.
- **`git status` is not a reading of this slice's diff.** Slice 2's files, Slice 1/3's spec files and
  an unrelated session's `docs/review/**` + `tests/mutations/test_operations.py` are all dirty
  concurrently; the attribution table is in `### Validation run` item 6.
- The `docs/builder/temp-tests/slice-4-029/` directory exists but is **empty** — the only file placed
  there was an ASCII control the layout checker refused to check, and it was removed once the control
  was re-done against the real file.

### Notes for Worker 1 (spec reconciliation)

The plan's five planning-time notes stand unchanged; these are this pass's additions.

6. **`types/base.py::_validate_meta` carries a third enumeration of the same rule, in the pre-repair
   order. Recorded, NOT fixed** — it is outside the two docstrings the plan's `### Scope discipline`
   makes writable, and it needs an argument beyond "this is the same sentence", which that section
   rules out. The comment reads:

   > Target existence / scope checks
   > (unknown / excluded / consumer-authored / relation / Relay-pk) need the
   > selected fields and run later in ``_validate_nullability_override_targets``.

   Symbol-qualified path: `django_strawberry_framework/types/base.py::_validate_meta`
   #"(unknown / excluded / consumer-authored / relation / Relay-pk) need the" (raw ref: 1297).
   **It is not false** — it is introduced by "Target existence / scope checks", not by "Check order:",
   so like Defect 2b it enumerates a set rather than asserting an order. But it is now the *only*
   remaining site in the module listing relation before Relay-pk, i.e. exactly the seed this slice
   removed from the other two, and it is a comment rather than a docstring, so no `Raises:`/`Args:`
   convention hints at its being unordered. Recommended disposition: fold the two-word swap into the
   integration pass (it is `.py`, inside the maintainer's fence) or record it in
   `bld-final-029.md`'s `### Deferred work catalog`. Recommended replacement text — the same
   enumeration in the shipped order:

   > Target existence / scope checks
   > (unknown / excluded / consumer-authored / Relay-pk / relation) need the
   > selected fields and run later in ``_validate_nullability_override_targets``.

7. **The rationale-companion conflict the plan predicted is now live, and this pass did not touch it**
   (as instructed). `docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md` `## Decision 8`,
   final bullet, ends #"that is a source-comment defect outside this cycle's editable surface and is
   routed to the final gate's deferred catalog". All three clauses are false as of this diff. The file
   is Slice 3's under the ownership partition; Worker 0 has already routed the correction to the
   integration pass (`build-029-…md` `## Cross-slice conflict created by Slice 4`). Recorded here only
   so final verification does not have to re-derive that it is now actually false rather than
   predicted-to-become-false.

8. **All six rows of the plan's `### Docstring-to-spec agreement map` were re-verified against the
   working-tree spec at build time and every one still resolves**, each at exactly one occurrence
   (`grep -cF`): #"Every `Meta` key whose value is a set of field names on the type validates through
   it", #"each caller keeps only its own per-name rules",
   #"That unknown/excluded half is shared, not per-key.",
   #"unknown / excluded / consumer-authored / Relay-pk / relation targets in that order",
   #"to reject unknown / excluded / consumer-authored / Relay-pk / relation targets, in that order",
   #"for every unknown / excluded / consumer-authored / Relay-suppressed-pk / relation target", and
   #"It is checked **before** the relation rule, so a name that is both". They remain **provisional**:
   `docs/SPECS/spec-029-…md` is dirty and Slice 3 owns it, so this is a reading of a moving file, not a
   settled one. Nothing was matched against a substitute passage, and no spec passage this pass needed
   had gone missing.

9. **No spec edit is proposed by this slice and none is needed.** The repaired docstrings now say what
   the spec says and what the code does; the three-way agreement is recorded above rather than assumed.

---

## Review (Worker 3)

Reviewed against the build plan above, `docs/builder/build-029-consumer_dx_cleanup-0_0_9.md`
`## Slice 4 added mid-cycle` and `## Ownership partition`, the spec, and the rationale companion.
Every reading below is a run on an instrument written in this pass; nothing is accepted on the build
report's prose. Scratch root for all copies and instruments is the session scratchpad **outside** the
repository; no `git stash` / `checkout` / `restore` / `worktree` was used.

### Scoping claim, confirmed first

`git diff --stat -- django_strawberry_framework/types/base.py` -> `1 file changed, 13 insertions(+),
10 deletions(-)`, matching the build report exactly. `git status --short -- django_strawberry_framework/`
lists exactly one entry (`M .../types/base.py`), so the slice's source footprint is one file. The
diff is three hunks, all inside docstring bodies. `git status` at large carries Slice 1/2/3's files
and an unrelated session's `docs/review/**` + `tests/mutations/test_operations.py`; none was read as
this slice's diff, and nothing was reverted or tidied.

### The central verification: the executable bytes are unchanged

**Failability proofs: considered and dismissed, not omitted.** `BUILD.md` `### What needs a proof,
and what does not` scopes proofs to a new boundary / guard / gate / rejection path and states they
are not required for doc edits. This diff introduces none — proved, not assumed, by R0 below. The
mandatory re-run floor in `worker-3.md` is therefore satisfied by an **empty re-run set, which is
legal only because the diff introduces no boundary meeting the floor**, and that is the case here.
No proof was manufactured.

**The inverse obligation was re-derived on an instrument written in this pass**, deliberately NOT the
plan's `ast.dump` form, so a defect in that form could not survive into my reading. Mine computes
**two independent serializations** and requires both to agree:

- **A. token stream** — `tokenize`, dropping COMMENT / NL / ENCODING / ENDMARKER and every docstring
  STRING token, the docstring tokens located by AST *position* rather than by node identity;
- **B. `ast.unparse`** of the docstring-stripped tree — a source round-trip, not a node dump, sharing
  no code path with `ast.dump`.

Anchors `_selected_meta_targets`, `_validate_nullability_override_targets`,
`_validate_filesystem_path_targets`, `_validate_relation_shape_targets`, checked first, as four
separate arguments (the build report's shell-quoting trap re-read and avoided).

| Row | Candidate | Result on MY instrument |
|---|---|---|
| R0 — the claim | pristine HEAD vs the post-edit working file | **exit 0**, tokens `0bbdf4a12728e270` (len 97593) and unparse `c6f9af09f7c1b9aa` (len 37505) identical on both sides |
| R1 identity | HEAD vs HEAD | exit 0, same pair of hashes |
| R2 negative control | HEAD vs a **further** docstring-only reword I built from the post-edit file | **exit 0** — the stripper is live; a 94238-byte file matching a 93972-byte one |
| R3 **positive control** | HEAD vs the `relay_pk_name` / `is_relation` **swap** I built from the post-edit file | **exit 1** on BOTH serializations; tokens `68b76c35d392805e`, unparse `9ad944f51c618c11`; first token divergence at char 80287 (`(1, 'relay_pk_name')` vs `(1, 'selected_by_name')`) |
| R4 anchor control | bogus anchor | **exit 2**, `ABORT: anchor '_no_such_symbol_xyz' absent from reference` |

Both control copies were built by a script that asserts each anchor block matches **exactly once**
and that the result differs from the input, so a control that failed to apply aborts rather than
producing a passing row.

**The claim that makes the AST check necessary re-derives, and is stronger than reported.** The
branch-swapped copy is **94227 bytes — byte-identical in length to the post-edit file** (measured on
my own independently-constructed swap, not on Worker 2's). Length is non-distinguishing in *three*
serializations, not one: file bytes 94227/94227, token stream 97593/97593, `ast.unparse` 37505/37505.
`wc -c`, a line count, and "the diff is docstring-only, look at it" all pass the forbidden fix.

**Worker 2's plan-form figures were then reproduced exactly**, as a cross-instrument check:
`ast.dump` chars 118250 for HEAD / post-edit / swapped / reworded alike, `sha256=8382eb52608bb1a0`
for HEAD, post-edit and the negative control, `5c5fed398dfc819e` for the swap. My independently-built
swap produced the same hash as Worker 2's, i.e. we constructed the same mutation.

**The forbidden fix was not taken.** Read against source: the loop in
`types/base.py::_validate_nullability_override_targets` runs `if name in consumer_authored_fields:`
-> `if name == relay_pk_name:` -> `if selected_by_name[name].is_relation:`, unchanged from HEAD (R0),
and the new docstring describes **that** order. The code was not bent to the old text.

### High:

None.

### Medium:

None.

### Low:

#### L1 — the citation-rot sweep's stated breakage over-reports by one; `#"Check order: unknown"` still resolves

`### Validation run` item 2 reports "4 occurrences, 2 distinct" citations into a rewritten block and
then says "**They stop resolving by design.**" That second clause is false for one of the two.
`grep -c "Check order: unknown" django_strawberry_framework/types/base.py` -> **1** in the post-edit
file and **1** at HEAD: the repaired sentence still opens `Check order: unknown -> excluded -> ...`,
so every citation spelling `#"Check order: unknown"` resolves exactly as before.

Re-derived on my own sweep, which measures **breakage** rather than overlap — a citation is broken
iff its flattened text resolves in flattened HEAD `base.py` and does **not** resolve in the flattened
post-edit file, so the instrument is not keyed on my guess about which blocks changed. Wrap hazard
handled three ways and the union reported: whole-file flatten then extract (a citation split across
two lines is one string after flattening), per-line extract, and per-adjacent-line-pair extract.
Flattening is casefold + whitespace-run collapse, so a reflow cannot hide a match.

- corpus `git ls-files --cached --others --exclude-standard`: **693 files** (matches the build report);
- citations extracted, all forms: 2979;
- **liveness control: 302 citations resolve into the post-edit `base.py`**, so a zero is a measurement;
- **broken by this diff: 1 distinct — `#"The first half shared by"`** — found by all three extraction
  forms, at `docs/builder/bld-slice-4-029-docstring_rot_repair.md:29` and `:384` (plus the report's
  own quotation of it at `:651`).

**The substantive conclusion is unaffected and re-derives: no standing doc, spec, source file, or
test cites into a block this diff rewrote; the only breakage is inside this slice's own artifact,
a per-cycle scratchpad exempt under `START.md` "Temp artifact conventions".** What is wrong is the
description, not the sweep. Recorded as a superseding measurement rather than routed back: the build
report's row stays standing (`ARTIFACT.md` `## Re-pass sections`), and a comment-only slice does not
earn a re-pass over one clause whose correction now sits where Worker 1 reads it. **Disposition:
addressed here; no change required of Worker 2.**

#### L2 — the replacement contract sentence is imprecise in both directions, and deliberately verbatim from the spec

Tested rather than assumed, because `### DRY / existence challenge` Decision 1 removed the caller
enumeration instead of extending it and the existence challenge cuts both ways. Read strictly against
the module's own vocabulary, "every ``Meta`` key whose value is a set of field names on the type" is:

- **under-inclusive of one of the three callers.** `Meta.relation_shapes` is `dict[str, str] | None`
  (`types/base.py::_validate_relation_shape_targets`, `targets=set(relation_shapes)`); its *keys* are
  field names, its value is a mapping. A reader applying the predicate literally would conclude
  `relation_shapes` does not validate through the seam — which is the same false-by-omission reading
  the slice exists to remove, in a new spelling.
- **over-inclusive.** `types/base.py::_normalize_sequence_spec` #"is a SET of field names whose
  declaration order carries no meaning" applies that exact phrase to `Meta.exclude`, and
  `Meta.exclude` does **not** route through `_selected_meta_targets`.

**Not closed in this slice, with the reason recorded.** The sentence is verbatim from
`docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` `## Decision 8` #"Every `Meta` key whose value is
a set of field names on the type validates through it" (confirmed at exactly 1 occurrence), and the
verbatim match is load-bearing: it is what makes `### Docstring-to-spec agreement map` row A1
mechanically checkable rather than a matter of impression. Correcting the docstring alone would break
that agreement; correcting both surfaces is a spec edit this slice may not make and Slice 3 is
editing that file concurrently. Escalated to Worker 1 — see `### Notes for Worker 1`.

**The DRY call itself is upheld.** The replacement is not merely vaguer: it states the closure
property that makes the seam dangerous to change (shared and open-ended), which the old "shared by A
and B" actively denied, and it carries the enumeration in a form that cannot rot — the three cited
Decisions (`spec-029 Decision 8 / spec-032 Decision 7 / spec-048 Decision 2`) map one-to-one onto the
three call sites, and `check_citations.py` does resolve `path::Symbol` forms even though it cannot
see prose. Deleting a rot-generating enumeration and replacing it with a contract is the right shape.

#### L3 — the precedence the new reason clause documents is pinned by no test, and the harness could pin it

The slice's argument that Defect 2 is load-bearing rather than cosmetic rests on both guards being
reachable by one name, which decides which message the consumer sees. That is true of the code and is
stated as a contract by the spec (`## Decision 8` failure-mode rule 4, #"It is checked **before** the
relation rule, so a name that is both", 1 occurrence). Nothing pins it:
`tests/types/test_base.py::test_override_relay_suppressed_pk_raises` uses `Category`, whose pk is a
plain `AutoField`, so the relation guard is never simultaneously true; `::test_override_relation_field_raises`
uses a non-pk relation. `grep -rn "primary_key=True" tests/ examples/` finds no fixture pairing a
relation pk with a Relay-shaped type and an override.

**This is a finding about the fixture, not about the code, and not about this diff** — the slice
introduces no boundary and the gap predates it. It is explicitly **not** harness-impossible:
`tests/optimizer/test_walker.py` builds a `OneToOneField(primary_key=True)` model at that file's
relation-pk fixture, so the row is writable today. Recorded so the area is not read as clean.
Escalated to Worker 1 for the deferred catalog; **not a hold on this slice.**

### Rulings the dispatch asked for

**1. `types/base.py::_validate_meta`'s third enumeration — scope discipline was right, and the
routing needs deciding rather than offering.**

The comment is `types/base.py::_validate_meta` #"(unknown / excluded / consumer-authored / relation /
Relay-pk) need the" (raw ref: 1291-1298). Verified in source: it is introduced by "Target existence /
scope checks", not by "Check order:", so like Defect 2b it enumerates a set and **is not false**.
Leaving it did not defeat the repair — the repair's claim was that two *false* docstring sentences
become true, and both did.

Worker 2 was right to leave it: the plan's `### Scope discipline` admits a further site only when it
needs no argument beyond "this is the same sentence", and this one needs three (different symbol, a
comment not a docstring, not false). Reopening a `built` comment-only slice for a two-word swap would
also cost a full re-pass Worker 1 must re-verify anyway.

**Ruling on disposition, between the two Worker 2 offered: the integration pass, not
`bld-final-029.md`'s `### Deferred work catalog`.** The integration pass is Worker 1's, has both
`.py` and the spec family inside the maintainer's fence, and is *already* correcting the two
rationale-companion passages this slice falsified — the same cohort of "sites describing this seam".
Pushing a two-word swap into a deferred catalog is exactly how a sixth parallel-site instance becomes
a seventh. Worker 2's recommended replacement text is correct as written.

**2. Is there a further site neither pass has named? No — and that answer rests on two instruments
sharing no vocabulary, not on one sweep.**

Enumerated rather than swept, per the dispatch. Both passes structurally enumerate **every** comment
token-run and **every** docstring node across all of `django_strawberry_framework/` via `ast` +
`tokenize`, then filter:

- **Pass A — rule vocabulary.** Filter: a block mentioning >= 3 of {unknown, excluded,
  consumer-authored, Relay-pk, relation, many-side, file/image, single-valued, not-selected}.
  **20 blocks.** Read individually.
- **Pass B — subject vocabulary, disjoint from A's.** Filter: a block naming the family by symbol
  (`nullable_overrides`, `required_overrides`, `_validate_nullability_override_targets`,
  `_selected_meta_targets`, `relay_pk_name`, "Relay-Node-suppressed"). **19 blocks.** Read
  individually. Pass B surfaces one block Pass A's threshold could not (`types/base.py::_build_annotations`
  #"(relation targets rejected) in") — the one Worker 2 also checked; it names two rules and asserts
  no order.

Both land on the same answer: **`_validate_meta`'s comment is the only remaining site in the package
listing relation before Relay-pk.** The other order-stating sites are each correct for their own
family — `_validate_relation_shape_targets` #"Check order mirrors the sibling: unknown -> excluded"
and `_validate_relation_shapes` #"Field-level checks (unknown / excluded / non-relation /
single-valued / consumer-authored)" both match that validator's actual loop (non-relation ->
single-valued -> consumer-authored), and `_validate_meta`'s own numbered "Validation order:" list is
about Meta-key stages, not the per-name checks. A fourth site states the same precedence and
**agrees** with the shipped order: `management/commands/inspect_django_type.py::_resolve_row` #"A
Relay-Node-suppressed pk wins over everything", which independently documents the relation-pk-on-a-
Relay-type case with the same `OneToOneField(primary_key=True)` example the new docstring uses. That
agreement is corroboration for the repair, not a finding.

**3. The plan's call-site table nit re-derives as Worker 2 states it.**
`grep -rn "_selected_meta_targets" --include="*.py" .` -> six occurrences, all in
`django_strawberry_framework/types/base.py`: definition 1416, calls 1517 / 1593 / 1658, prose 979 /
1566. No call site outside the module. The plan's "1426, 1427" rows are indeed the two caller *names
inside the docstring under repair* at HEAD, not occurrences of the symbol. The load-bearing half —
one definition, three calls, none outside the module — is correct.

### Both re-done non-runs verified as genuinely re-done, and one of them was avoidable

**(a) The five-row abort.** Reproduced the mechanism: the instrument checks anchors before comparing,
so four anchors collapsed into one quoted argument exits 2 on every row. My R4 row confirms the abort
path fires (`exit 2`, `ABORT: anchor ... absent`). My own five rows were run with the four anchors as
four separate arguments and returned three distinct verdicts (0 / 0 / 1 / 2), which is itself the
evidence they were not a uniform non-run.

**(b) The ASCII control.** The build report's first attempt landed under `docs/builder/temp-tests/`
and returned `excluded from the source-layout rules -- not checked`, exit 0. Mechanism confirmed at
`scripts/check_trailing_commas.py` #"excluded from the source-layout rules -- not checked" — skipped
paths are printed and then simply not checked, so the run exits 0 having measured nothing.

I re-derived the liveness control **without any source mutation**: `iter_files` accepts an explicit
path outside the repository, so a U+2192 injected into a scratch copy of the post-edit file is
checked normally. Result:
`.../base.ASCIICTRL.py:1486:26: non-ASCII U+2192 '→' not allowed in .py`, exit 1 — the **same line
and column** Worker 2 recorded, on the same content. The clean scratch copy exits 0. Both directions
controlled, gate demonstrably live on this file's docstrings.

**Worth carrying: Worker 2's transient source mutation for this control was not necessary.** Running
the layout gate on an out-of-repo copy gives the identical reading with no mutation to revert and no
window in which the tree carries deliberately broken source. Worker 2's mutation was nonetheless
correctly performed and correctly proved (`cmp` exit 0), and it is reverted.

**No mutation is live, and the file is byte-clean.** Independently: 0 bytes > 127 in
`django_strawberry_framework/types/base.py` (byte scan, not a grep); `check_trailing_commas.py --check`
exit 0 with empty output; R0 above proves the executable bytes equal HEAD's, which no live code
mutation could survive. `docs/builder/temp-tests/slice-4-029/` is empty, as the build report states.

### Gates re-run independently

| Gate | Result |
|---|---|
| `uv run ruff format --check django_strawberry_framework/types/base.py` | `1 file already formatted` |
| `uv run ruff check django_strawberry_framework/types/base.py` | `All checks passed!` |
| `uv run python scripts/check_trailing_commas.py --check <file>` | exit 0, no output |
| non-ASCII bytes | **0**, by byte scan |
| lines over 99 | **18 at HEAD, 18 after** — no new one; the single >110 line is pre-existing and unchanged |
| `git diff --check` | exit 0 |
| `uv run pytest tests/types/test_base.py --no-cov -q` | **164 passed** (no `--cov*` flag used anywhere in this pass) |

### Spec-agreement rows re-derived

All seven passages the plan's `### Docstring-to-spec agreement map` depends on resolve at **exactly 1
occurrence** (`grep -cF`) in `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` as it stands now, and
the repaired docstrings agree with each: the check order (`unknown / excluded / consumer-authored /
Relay-pk / relation`, three independent spec statements), the Relay-before-relation reason, the
shared-half contract sentence, and the per-name remainder. This is a reading of a file Slice 3 owns
and is editing, so it stays **provisional** and is the integration pass's to re-settle — as both the
plan and the build report already say.

### Spec slice checklist audit

All **11** boxes ticked, **0** left open. Each walked against the diff and against source:

1-3 (`_selected_meta_targets`) — the two-name enumeration is gone, replaced by the contract sentence;
`file/image column` is present in the per-name list; the citation reads
`spec-029 Decision 8 / spec-032 Decision 7 / spec-048 Decision 2`. Verified against the three
callers' actual per-name checks: `_validate_nullability_override_targets` (consumer-authored /
Relay-pk / relation), `_validate_filesystem_path_targets` (consumer-authored /
`_field_output_type_for(...) is None`), `_validate_relation_shape_targets` (non-relation /
`is_many_side` / consumer-authored). The five-entry list is the exact union of their check topics.
4-6 (`_validate_nullability_override_targets`) — order matches the loop; the reason clause is present
and true of the code (`relay_pk_name` is only non-`None` under `relay_shaped`, so "on a Relay-shaped
type" is precise); `Raises:` now reads `... / the Relay-suppressed pk / a relation field`.
"The last three" in the following sentence still resolves correctly to the last three of five.
7-8 (instrument) — re-run above, all four rows plus a fifth serialization.
9-10 (gates) — re-run above.
11 (record-not-fix) — build-report note 6 carries the `_validate_meta` site with a symbol-qualified
path, the argument, and replacement text; the diff repairs nothing outside the two docstrings.

**No box is ticked without a matching change in the diff, and no box the diff leaves unaddressed.**

### DRY findings

- **Existence challenge, tested and upheld.** Decision 1's deletion of the caller enumeration is the
  right call and is a first-class DRY win: the enumeration had already rotted once, in exactly the
  way an ungated closed list rots, and nothing in the repo gates it (`check_citations.py` resolves
  `path::Symbol`, not prose; no test, linter, or review step compares a docstring's caller list
  against `grep`). The replacement carries the load-bearing fact — the seam is shared and
  open-ended — which the old sentence denied. Its residual imprecision is L2 above, and it is
  inherited from the spec by design rather than introduced here.
- **No new helper, constant, module, or indirection** is added; nothing to consolidate and nothing
  whose existence to challenge. `scripts/review_inspect.py` was run (below) and its **Repeated string
  literals** section is unchanged from the pre-edit structure, as it must be — the diff adds no
  executable literal.
- **Recorded, not flagged as duplication:** `types/base.py::_format_unknown_fields_error` still
  enumerates its callers and is currently complete and correct (verified: it names
  `Meta.fields` / `Meta.exclude` / `Meta.optimizer_hints` / `nullable_overrides` /
  `required_overrides` / `filesystem_path_fields` / `relation_shapes`). The plan already recorded
  the same observation with the argument made. Its rot risk is real but it is not a duplication of
  anything and is not this slice's to change.

### Static helper use

`uv run python scripts/review_inspect.py django_strawberry_framework/types/base.py --output-dir docs/shadow`
— run, as `BUILD.md` `### When to run the helper during build` requires for any slice touching an
existing `.py` file under `types/`. Emitted `docs/shadow/django_strawberry_framework__types__base.overview.md`
and `.stripped.py`. **No skip to record.** Its evidentiary value here is limited exactly as the plan
and build report warn — `.stripped.py` replaces every string token including docstrings with `...`,
so it is structurally blind to this entire diff. It was used only to confirm the executable structure
is what the plan describes; the AST/token instruments above are this slice's verification.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty**; the file is not listed by
`git status --short`. `__all__` and the re-export list are unchanged. No new public export.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. The only file it wrote
outside its own artifact is `django_strawberry_framework/types/base.py`. Noted for completeness:
`docs/TREE.md` renders from **module** docstrings, and this diff touches neither the module docstring
nor any staging language, so no regenerate is owed.

### Hot-path budget and floor verification

Plan declares both `none` and both declarations are correct rather than merely stated: R0 proves zero
executable-line changes, so no operation can have gained cost, and a docstring cannot diverge across
Django / Strawberry / Python versions. No number is owed and none is missing.

### What looks solid

- **The verification is inverted correctly and argued from the right section.** Worker 1 declared
  proofs `none` by citing `### What needs a proof, and what does not` rather than by silence, and
  Worker 2 discharged the obligation that actually applies. That is the distinction between a decided
  answer and an omission, and it held through both passes.
- **The positive control is the forbidden fix itself.** Choosing "swap the two branches" as the
  mutation means the instrument is controlled against precisely the failure this slice must not
  commit, rather than against an arbitrary edit. The byte-length coincidence it exposed is the whole
  argument for the AST check and it re-derives independently.
- **Both self-caught non-runs were reported rather than buried,** including the one that would have
  read as five green rows. That is the behavior the cycle's eight dead instruments argue for.
- **The reason clause is the durable half of the Defect 2 repair.** An order without a reason invites
  a future reader to "tidy" it; the clause names the consequence (which error message the consumer
  sees) and matches an independently-written precedent in `inspect_django_type::_resolve_row`.
- **Line wrapping was preserved rather than reflowed.** No untouched docstring line moved, which is
  why exactly one citation broke instead of a cohort — the wrap hazard this cycle has been bitten by
  repeatedly.

### Temp test verification

No temp test was written. `docs/builder/temp-tests/slice-4-029/` is empty and stays empty; a
docstring repair offers no assertion to demonstrate as non-distinguishing, and L3 above is a fixture
gap for Worker 1 to route, not a suspicion to prove with a scratch row. Four instruments were written
to the session scratchpad **outside** the repository (dual-serialization identity checker, control
builder, citation-breakage sweep, two-pass parallel-site enumerator); none is inside the tree and
none is proposed for promotion.

### Notes for Worker 1 (spec reconciliation)

The plan's notes 1-5 and the build report's notes 6-9 all stand; verified rather than restated. These
are this review's additions.

10. **Escalated — the shared-half contract sentence is imprecise in both directions, on both surfaces
    (L2).** `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` `## Decision 8` and the repaired
    `types/base.py::_selected_meta_targets` docstring both read "every ``Meta`` key whose value is a
    set of field names on the type". `Meta.relation_shapes` is a `dict` (under-inclusive of a caller
    that *does* route through the helper) and `Meta.exclude` satisfies the predicate under this
    module's own vocabulary (`types/base.py::_normalize_sequence_spec` #"is a SET of field names
    whose declaration order carries no meaning") while *not* routing through it. Resolution paths:
    **(a)** amend both surfaces together at the integration pass to a predicate that is exact in both
    directions — e.g. "every ``Meta`` key that names target field names validated against the
    selected set" — preserving the verbatim match row A1 depends on; **(b)** leave both, on the
    grounds that the spec defines the phrase by the enumeration that immediately follows it and the
    docstring's three cited Decisions carry the same enumeration. **Not (c):** changing the docstring
    alone, which silently breaks the mechanical agreement. Worker 1 owns the call; the docstring is
    not wrong in a way that misleads about behavior, so this is not a hold.

11. **Escalated — the Relay-pk-before-relation tie-break is documented as a contract and pinned by no
    test (L3).** Spec `## Decision 8` rule 4 states it; the repaired docstring now states it; the code
    holds it; no fixture pairs a relation pk with a Relay-shaped type and an override, so no row can
    fail if the precedence is lost. **Not harness-impossible** — `tests/optimizer/test_walker.py`
    already builds a `OneToOneField(primary_key=True)` model, so the row is writable today. Route to
    `bld-final-029.md`'s `### Deferred work catalog`, or to a follow-up slice if the cycle has room.
    Pre-existing at HEAD and outside this slice's contract, so it is escalated rather than filed
    against Worker 2.

12. **Ruled, so it does not arrive at the integration pass as an open question:** the third
    enumeration at `types/base.py::_validate_meta` #"(unknown / excluded / consumer-authored /
    relation / Relay-pk) need the" belongs to the **integration pass**, not the deferred catalog.
    Reasons in `### Rulings the dispatch asked for` item 1; Worker 2's recommended replacement text is
    correct as written and needs no re-derivation.

13. **Record correction for the deferred catalog's benefit (L1):** exactly **one** distinct citation
    was broken by this diff, `#"The first half shared by"`, and it lives only in this slice's own
    artifact. `#"Check order: unknown"` still resolves at 1 occurrence in the post-edit file. If the
    final gate's catalog copies the build report's "2 distinct" figure it will be carrying a number
    that does not re-derive.

14. **Not filed, but examined, so silence is not read as a miss.** (a) The per-name list's word
    "non-relation" means opposite things for two of the three callers (nullability rejects relations;
    relation-shapes rejects non-relations) — pre-existing wording the slice was right not to widen
    into. (b) `git status` shows `docs/SPECS/appx/spec-029-...-rationale.md` as untracked (`??`)
    where the build report's attribution table implies modified; the ownership attribution is
    unaffected. Neither is a finding.

### Review outcome

`review-accepted`.

Three Low findings, each with a recorded disposition: **L1** addressed in this section as a
superseding measurement, no change required of Worker 2; **L2** and **L3** intentionally not closed
here, with reasons recorded, and escalated to Worker 1 under notes 10 and 11 — both require spec
context or a fixture Worker 2 cannot supply from this slice's contract, and neither describes wrong
behavior. No High or Medium finding. The diff delivers its contract: three docstring blocks, the
executable bytes provably unchanged against pristine HEAD on three independent serializations, the
forbidden branch-swap proved detectable and not taken, all eleven checklist boxes landed, every gate
green, and the one remaining parallel site correctly recorded rather than fixed and now ruled to the
integration pass.

---

## Final verification (Worker 1)

Every reading below is a run on an instrument this pass wrote, controlled before it was believed.
Scratch root for the HEAD copy, the identity instrument and the branch-swap control is the session
scratchpad **outside** the repository; no `git stash` / `checkout` / `restore` / `worktree` was used.
`git status` was read for attribution only, never as this slice's diff.

### Verdicts on the three Low findings

#### L1 — confirmed as Worker 3 recorded it; no re-pass owed

Re-derived on a third instrument (mine dedups per file rather than counting occurrences, so its
totals differ from Worker 3's by construction and its answer must not): corpus
`git ls-files --cached --others --exclude-standard` = **693 files**, **1010 distinct citations**,
**liveness control 104 citations resolving into the post-edit `base.py`** so a zero is a measurement.
Broken by the whole slice, HEAD -> disk: **1 distinct, `#"The first half shared by"`, and it lives
only in this artifact** — a per-cycle scratchpad exempt under `START.md` "Temp artifact conventions".
`grep -c "Check order: unknown" django_strawberry_framework/types/base.py` -> **1**, so that citation
still resolves and the build report's "both stop resolving by design" clause is the thing that was
wrong, not the sweep. Worker 3's substantive conclusion holds: **no standing doc, spec, source file
or test cites into any block this diff rewrote.** Superseding measurement accepted; Worker 2 owes
nothing.

#### L2 — upheld in substance, narrowed in extent, and closed by moving BOTH surfaces

Both halves were re-derived at source before ruling, because a finding handed to me is a hypothesis.

- **Under-inclusion: confirmed, and it is the clear-cut half.** `Meta.relation_shapes` is
  `dict[str, str] | None` (`types/base.py::_validate_relation_shapes` signature), and
  `types/base.py::_validate_relation_shape_targets` reaches the seam via
  #"targets=set(relation_shapes)" — its *keys* are the targeted names. A predicate quantified over
  the key's **value shape** therefore excludes a caller that demonstrably routes through the helper.
  That is a false claim about the seam's membership, in the docstring whose entire contract is that
  it no longer makes one.
- **Over-inclusion: real but weaker than stated.** Worker 3 rests it on
  `types/base.py::_normalize_sequence_spec` #"is a SET of field names whose declaration order carries
  no meaning", which does apply that phrase to `Meta.exclude`. But the sentence under review says
  "field names **on the type**", and `Meta.exclude`'s names are precisely the ones that will *not* be
  on the type — so the existing qualifier already carries most of the distinction. Right in
  substance, overstated in extent; recorded so the extent is not inherited.

**The measurement that decides the shape of the fix, which neither prior pass ran:** the population
{`nullable_overrides`, `required_overrides`, `filesystem_path_fields`, `relation_shapes`} is **not
characterized by any semantic property**. `Meta.optimizer_hints` has the same shape — its keys must
name model fields and must be in a *selected* subset — and it performs both checks inline in
`types/base.py::_validate_optimizer_hints` rather than through the seam
(`_format_unknown_fields_error` is the only piece it shares). So a predicate of the form "every
`Meta` key whose declared names are validated against the selected set" is over-inclusive too, in a
new direction. **No short, exact, non-enumerative predicate exists**; membership is defined by the
call graph. That is why the answer is not "find a better universal".

**Ruling: tighten both surfaces by one phrase, keeping the verbatim agreement intact.**
`whose value is a set of field names on the type` -> `that targets a set of field names on the type`,
applied to the docstring **and** to `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` `## Decision 8`
in the same pass. Why this and not the alternatives:

- It removes the clear-cut falsehood (a claim about Python value shape) and replaces it with a claim
  about **role**, which is this module's own term of art — `_selected_meta_targets`, the `targets=`
  parameter, the three `_validate_*_targets` callers, and the shipped error text
  #"The override targets a field that will not appear" all use it, and nothing in the module calls
  `Meta.exclude`, `Meta.fields` or `Meta.optimizer_hints` a target.
- It is **not the vaguer-but-not-false trade** the dispatch warns about. The replacement says more
  than the original, not less: it names what the key does to the seam rather than what its literal
  happens to be.
- It **does not reopen Decision 1.** No caller enumeration returns to the docstring; the rot
  generator stays deleted. The existence challenge is upheld, exactly as Worker 3 found.
- The spec side was **independently defective**, which is what licenses the custodian edit rather
  than a docstring-only change: at `:360` the sentence's own appositive names `Meta.relation_shapes`
  as a member while its predicate excludes dict-valued keys — the sentence contradicts itself. So
  option (b) "tighten the docstring and retire the verbatim agreement" would have left a
  self-contradicting spec sentence standing to buy nothing, and option (c) "accept" would have left
  the same falsehood on two surfaces.
- Row A1 of `### Docstring-to-spec agreement map` survives with a new quoted string; both sides moved
  together and the pair is still mechanically checkable. **The citation row A1 must now be spelled**
  #"Every `Meta` key that targets a set of field names on the type validates through it" — the old
  spelling resolves nowhere.

Population of the retired phrase, enumerated rather than swept (whitespace-flattened containment over
the same 693-file corpus, with the liveness control at 108 citations into `spec-029`): the two live
surfaces I edited, plus prose quotations inside `bld-slice-3-…md` and this artifact — both per-cycle
scratchpads. Citations broken by my edit: **1** — the retired-phrase citation
#"Every `Meta` key whose value is a set of field names on the type validates through it",
at this artifact's `:848`, i.e. Worker 2's own quotation of
the row it was checking. Same exempt class as L1. **No standing doc, sibling spec, source file or
test carried the retired phrase.** `docs/SPECS/spec-048-…md:478` and its rationale use the same
"set of field names" vocabulary, but about `_normalize_sequence_spec`'s four sequence-normalized keys
— a different helper and a still-true statement; no contradiction is created and neither file is
touched.

#### L3 — confirmed at source; **deferred, not `revision-needed`** — and it is neither of the two named cases

Re-derived: `tests/types/test_base.py::test_override_relay_suppressed_pk_raises` builds a Relay-shaped
type over `Category`, whose pk is not a relation, so the relation guard is never simultaneously true;
`::test_override_relation_field_raises` uses a non-pk relation. `grep -rn "primary_key=True" tests/
examples/` finds no fixture pairing a relation pk with a Relay-shaped type and an override. And
`tests/optimizer/test_walker.py::test_plan_relay_id_projects_attname_when_pk_is_relation` does build
`ProfileSource.user = OneToOneField(UserTarget, primary_key=True)`, so Worker 3 is right that the
fixture is writable today. **Not harness-impossible.**

**Naming which case this is, as the dispatch requires: neither.**

- `BUILD.md` `### Acceptance rule: weakly pinned is revision-needed` keys off a **failability proof**
  measuring 0 or 1 rows on a boundary **a slice introduces**. This slice introduces no boundary —
  proved, not asserted, by the AST identity re-run below — and therefore owes no proof at all under
  `### What needs a proof, and what does not`. The rule has no measurement to bite on here.
- `### Harness-impossible interleavings` prescribes a production-call-site invariant assertion when
  the harness *cannot* exhibit the failure. This harness can. So that section does not apply either,
  and invoking it would be the wrong remedy.

What this actually is: a **pre-existing test-coverage gap in shipped surface, surfaced by a
documentation pass.** The precedence has been the shipped behavior since `0.0.9`; the spec has
asserted it as a contract since Slice 3's reconciliation; the code holds it; nothing about it changed
in this diff. `fail_under = 100` cannot see the gap because both guards' statements are covered — what
is unpinned is which one wins when both are true, an interleaving, not a statement. Routing a
comment-only slice back to a builder to author a fixture is exactly the manufactured obligation
`### What needs a proof, and what does not` warns makes the real proofs unaffordable, and it would
expand a two-docstring repair into a test-authoring slice.

**Disposition: deferred to `bld-final-029.md`'s `### Deferred work catalog`, carried forward below
with the exact row that is owed so the entry is actionable rather than a note.** Recorded distinction
for the next reader: an unpinned boundary *introduced* by a slice is `revision-needed`; a pre-existing
one merely *documented* by it is a catalog item. This is the second.

### `_validate_meta`'s third enumeration — routing confirmed, carried forward precisely

Worker 3's ruling is confirmed rather than reopened. Verified at source that the site is still present
and unrepaired (`django_strawberry_framework/types/base.py::_validate_meta`
#"(unknown / excluded / consumer-authored / relation / Relay-pk) need the", raw ref 1297), that it is
introduced by "Target existence / scope checks" and so **is not false**, and that Worker 2 was right
to leave it under `### Scope discipline`. Worker 3's two disjoint-vocabulary enumerations (rule-token
filter, 20 blocks; subject-symbol filter, 19 blocks; both over every comment run and docstring node in
the package) and the agreeing fourth site at
`django_strawberry_framework/management/commands/inspect_django_type.py::_resolve_row`
#"A Relay-Node-suppressed pk wins over everything" are accepted as the population; I did not re-run
them, and the routing does not depend on re-running them. **Integration pass, not the deferred
catalog**, for the reason Worker 3 gave: it is the same cohort as the companion passage this slice
falsified, and Worker 1 owns both `.py` and the spec family there. Worker 2's recommended replacement
text is correct as written.

### The slice delivered its contract

**Four docstring sites corrected, in three hunks across two docstrings** — the caller enumeration
(Defect 1) and the per-name check list (Defect 1b) in `_selected_meta_targets`; the check-order
paragraph (Defect 2) and the `Raises:` clause (Defect 2b) in
`_validate_nullability_override_targets`. Plus this pass's one-phrase L2 tightening inside site 1.
`git diff --stat -- django_strawberry_framework/types/base.py` -> `1 file changed, 13 insertions(+),
10 deletions(-)`, unchanged by my edit (a same-length phrase swap), and the diff read in full is
three hunks, every one inside a docstring body.

**Zero executable-line changes, re-derived on my own instrument.** Third independent
`ast.dump(include_attributes=False)` implementation, docstring-stripped, four anchors passed as four
separate arguments:

| Row | Candidate | Result |
|---|---|---|
| R1 identity | HEAD vs HEAD | exit 0, `sha256=8382eb52608bb1a0`, 118250 chars |
| **R0 the claim** | pristine HEAD vs the working file **after my L2 edit** | **exit 0**, `sha256=8382eb52608bb1a0` |
| **R3 positive control** | HEAD vs a branch swap I built myself from the post-edit file | **exit 1**, `sha256=5c5fed398dfc819e`, first divergence at char 96924 (`If(test=Compare(left=Name(id='name'` vs `If(test=Attribute(value=Subscript(value=Name(id='selected_by_name'`) |
| R4 anchor control | bogus anchor | exit 2, `ABORT: anchor '_no_such_symbol_xyz' absent from reference` |

The swap builder asserted each block matched **exactly once** and that the result differed from its
input, so a control that failed to apply would abort rather than produce a passing row. My swap
reproduces Worker 2's and Worker 3's hash (`5c5fed398dfc819e`) and divergence offset, i.e. three
independently-built mutations are the same mutation.

**The non-distinguishing-length property spot-checked, and it is stronger again.** My own branch swap
is **94227 bytes and 1953 lines** — byte-identical *and* line-identical to the post-edit file — while
its AST dump is 118250 chars, the same as the identical file's. So length is non-distinguishing in
**four** serializations now (file bytes, line count, `ast.dump` chars, and Worker 3's token stream /
`ast.unparse` pair). `wc -c`, `wc -l`, and "the diff is docstring-only, look at it" all pass the
forbidden fix; only the hash comparison separates them. Worker 3's report of the property is
confirmed as measured, not inflated.

**The forbidden fix was not taken.** Read at source: the loop in
`types/base.py::_validate_nullability_override_targets` runs
`name in consumer_authored_fields` -> `name == relay_pk_name` -> `selected_by_name[name].is_relation`,
enumerated by AST rather than by eye, and the repaired docstring describes that order.

**No mutation is live; the file is byte-clean.** 0 bytes > 127 by byte scan (not a grep) over all
94227 bytes; `check_trailing_commas.py --check` exit 0 with empty output;
`docs/builder/temp-tests/slice-4-029/` is **empty** (`ls -la` -> `.` and `..` only); R0 proves the
executable bytes equal HEAD's, which no live code mutation could survive.
`git status --short -- django_strawberry_framework/` lists exactly one entry.

**Failability proofs `none` — the dismissal record exists and was not manufactured.** Confirmed
present in all three prior passes: the build plan's `## Slice 4 added mid-cycle` "Obligations"
paragraph, the artifact's `### Verification: the obligation is the INVERSE of a failability proof`,
Worker 2's `### Failability proofs` (`None; this pass introduced no new boundary.`), and Worker 3's
`### The central verification`. Each argues it from `BUILD.md` `### What needs a proof, and what does
not` rather than by silence. My duty is to confirm the record, not to write a fourth one, and I have
not. Hot-path `none` and floor-verification scope `none` are likewise declared and correct: R0 proves
no operation gained cost, and a docstring cannot diverge across framework or interpreter versions.

### Spec slice checklist audit — all 11 boxes

Audited against the diff and against source, not against Worker 3's audit. **All 11 correctly `- [x]`;
no over-tick, no landed box left open, nothing left `- [ ]` and therefore no deferral reason owed.**

1-3 — the two-name enumeration is gone from the diff's first hunk; `file/image column` is present in
the per-name list; the citation reads `spec-029 Decision 8 / spec-032 Decision 7 / spec-048 Decision 2`.
Re-derived the seam's membership myself: `grep -rn "_selected_meta_targets" --include="*.py" .` ->
six occurrences, all in `types/base.py` — definition 1416, **three** calls (1517 / 1593 / 1658), prose
979 / 1566 — so "three callers, one omitted at HEAD" is a measurement.
4-6 — the stated order matches the AST-enumerated loop; the reason clause is present and true of the
code (`relay_pk_name` is `None` unless `relay_shaped`, so "on a Relay-shaped type" is precise); the
`Raises:` clause reads `... / the Relay-suppressed pk / a relation field`. "The last three" in the
following sentence still resolves to the last three of five.
7-8 — instrument and both control directions re-run above on a third implementation.
9-10 — gates re-run below; independent byte scan; `git status --short` shows one package source file.
11 — the `_validate_meta` site is recorded with a symbol-qualified path and replacement text in build
report note 6 and is **not** repaired in the diff; the diff touches nothing outside the two docstrings.

### DRY check across this slice and the prior accepted slices

No new duplication. The slice adds no helper, constant, module, literal or indirection — it cannot,
having zero executable-line changes. The existence challenge that produced Decision 1 is upheld
(L2 above), and the one shape this pass touched, the contract predicate, now reads identically on its
two surfaces by construction rather than by coincidence.

### Gates re-run

| Gate | Result |
|---|---|
| `uv run ruff format --check .` | `429 files already formatted`, exit 0 |
| `uv run ruff check .` | `All checks passed!`, exit 0 |
| `uv run python scripts/check_trailing_commas.py --check` | exit 0, no output |
| `uv run python scripts/check_citations.py` | `OK: 789 citations resolve (712 in 426 .py files, 77 in KANBAN.md).`, exit 0 |
| `git diff --check` | exit 0 |
| `uv run pytest tests/types/test_base.py --no-cov -q` | **164 passed** |
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-029-…md` | `OK: 44 terms - all have glossary entries and at least one spec link.` |
| non-ASCII bytes in `base.py` | **0**, by byte scan over 94227 bytes |
| lines over 99 in `base.py` | **18 at HEAD, 18 now** — none introduced |

No `--cov*` flag was used in any command of this pass; `--no-cov` only.

**Staged-anchor sweep** (`grep -rEn 'TODO\(spec-029|TODO-(ALPHA|BETA|STABLE)-029' .`, excluding
`KANBAN.md` / `KANBAN.html` / `BACKLOG.md`): **no live anchor.** Every hit is prose *about* the
scaffold, inside the spec's staging-notes section, the rationale companion's rev7 record, a sibling
spec's superseded-card list, or a prior slice artifact. **Control: the sweep fires** — the same
pattern relaxed to `TODO(spec-` returns three live anchors in `.py`
(`tests/test_permissions.py:43` spec-036, `tests/test_connection.py:1592` spec-033,
`tests/optimizer/test_extension.py:5342` spec-035), so the zero for `029` is a measurement rather
than a dead regex.

### Method note carried forward from Worker 3

**The narrow source carve-out is a last resort and was not needed here.** Worker 2's transient U+2192
injection into `types/base.py` for the ASCII liveness control was correctly performed, correctly
reverted and correctly proved by `cmp` — but it was avoidable: `scripts/check_trailing_commas.py`
accepts an explicit path, including one outside the repository, and Worker 3 obtained the identical
`1486:26 U+2192` reading on an out-of-repo scratch copy with **zero source mutation**. Recorded as
method, not as a finding: prefer the out-of-repo copy, so the tree never carries deliberately broken
source and there is no window for `### Mutations are transient` to bite.

### Summary

Slice 4 repaired four false-or-inconsistent docstring sites in
`django_strawberry_framework/types/base.py` — the `_selected_meta_targets` caller enumeration and
per-name check list, and the `_validate_nullability_override_targets` check-order paragraph and
`Raises:` clause — with **zero executable-line changes**, proved against pristine HEAD on three
independently-written instruments and controlled in both directions on each. This pass added a
one-phrase tightening of the shared-half contract predicate on **both** the docstring and the spec,
closing L2 without reopening Decision 1's deletion of the caller enumeration. L1 is confirmed as a
description defect already superseded by Worker 3's measurement; L3 is a pre-existing test-coverage
gap deferred to the final gate's catalog with the owed row named. `_validate_meta`'s surviving
enumeration is routed to the integration pass. Every gate is green and the working file is byte-clean.

**Final status: `final-accepted`.**

### Spec changes made (Worker 1 only)

1. **`docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md:360`** (`## Decision 8`, the paragraph opening
   **"That unknown/excluded half is shared, not per-key."**) — the clause
   "Every `Meta` key whose **value is** a set of field names on the type validates through it"
   becomes "Every `Meta` key that **targets** a set of field names on the type validates through
   it". Triggered by Slice 4 / finding L2. Reason: the
   sentence contradicted its own appositive, which names `Meta.relation_shapes` — a `dict`-valued key
   — as a member of a population the predicate defined by set-valued *literals*. The replacement
   quantifies over the key's role, which is the module's own term of art and is exact for all four
   members. Verified after the edit: `check_spec_glossary.py --spec …` exit 0 (44 terms), the
   `check_trailing_commas` markdown scaffold check exit 0, no in-page anchor or reference-style
   definition touched, and the retired phrase resolves in **no** standing doc, sibling spec, source
   file or test.
2. **`django_strawberry_framework/types/base.py::_selected_meta_targets`** — the same phrase, so the
   pair keeps the verbatim agreement `### Docstring-to-spec agreement map` row A1 depends on. Not a
   spec file, recorded here because the two edits are one decision and neither is correct alone. AST
   identity re-run after it (R0 above): `exit 0`, `sha256=8382eb52608bb1a0` — still executably
   identical to pristine HEAD.
3. No other spec edit is needed. **Spec status-line re-verification (this spawn):** read
   `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` lines 1-9 — title, shipped-in banner,
   `Status: **SHIPPED (0.0.9)**`, Owner, Predecessors, and the rationale-companion pointer. Nothing
   there is falsified by this build; the companion the pointer names exists (Slice 1 created it). **No
   edit made.**

### Notes for Worker 1 (spec reconciliation)

Carry-forward for the integration pass and the final gate. The plan's notes 1-5, the build report's
6-9 and the review's 10-14 all stand; these are the dispositions.

15. **Integration pass — `types/base.py::_validate_meta`'s third enumeration.** Symbol-qualified path
    `django_strawberry_framework/types/base.py::_validate_meta`
    #"(unknown / excluded / consumer-authored / relation / Relay-pk) need the". Same cohort as the
    falsified companion passage in item 16, which is why it belongs here and not in the deferred
    catalog. Not false, but the only remaining site in the package listing relation before Relay-pk.
    Replacement text, verified correct as written:
    `# (unknown / excluded / consumer-authored / Relay-pk / relation) need the`. It is a `.py` comment
    inside the maintainer's fence; a two-word swap with no executable line touched.

16. **Integration pass — the companion's trailing parenthetical, false *on disk* now.**
    `docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md` `## Decision 8`, the bullet
    **"Claim this Decision may no longer make…"**, trailing parenthetical at `:245`:
    #"that is a source-comment defect outside this cycle's editable surface and is routed to the final
    gate's deferred catalog". All three clauses are false as of this slice's bytes — the docstring no
    longer lists the rev1 order, the defect was inside the fence, and it was repaired rather than
    deferred. **The population is ONE sentence.** Slice 3's final verification enumerated it on three
    disjoint vocabularies and `:244` already names the third caller, so nothing asserts the
    `_selected_meta_targets` defect at all. The build plan's earlier "at least two passages" framing
    was itself the parallel-site error in miniature and is superseded; **do not re-inflate it.** No
    gate sees this class — it is prose, and `check_citations.py` is `path::Symbol`-only with `docs/`
    out of scope.

17. **Integration pass — row A1's citation string changed in this pass.** Any re-check of
    `### Docstring-to-spec agreement map` must spell it
    #"Every `Meta` key that targets a set of field names on the type validates through it". The old
    spelling resolves nowhere; the only surviving occurrences of the retired phrase are prose
    quotations inside `bld-slice-3-029-…md` and this artifact, both per-cycle scratchpads that close
    with the cycle. Rows A2, A3, B1-B3 are unchanged and were re-derived by Worker 3 at 1 occurrence
    each.

18. **Final gate `### Deferred work catalog` — L3, the unpinned precedence.** Source:
    `### Review (Worker 3)` L3 and this section. **Owed row:** a test pairing a relation pk with a
    Relay-shaped type and an override naming that pk, asserting the **Relay** message
    (`"Relay-Node-suppressed pk"`) rather than the relation one — the fixture pattern already exists
    at `tests/optimizer/test_walker.py::test_plan_relay_id_projects_attname_when_pk_is_relation`
    (`OneToOneField(..., primary_key=True)`), and the assertion neighbourhood is
    `tests/types/test_base.py::test_override_relay_suppressed_pk_raises`. Licensing clause: the
    precedence is a shipped contract stated at `docs/SPECS/spec-029-…md` `## Decision 8` failure-mode
    rule 4; the gap is **pre-existing at HEAD**, predates this slice, and this slice introduced no
    boundary, so no failability-proof obligation attaches and neither
    `### Acceptance rule: weakly pinned is revision-needed` nor `### Harness-impossible interleavings`
    applies. `fail_under = 100` structurally cannot see it: both guards' statements are covered; what
    is unpinned is which wins when both are true.

19. **Final gate `### Deferred work catalog` — record the two docstring defects as CLOSED by Slice 4,
    not deferred**, per the build plan's `## Cross-slice conflict created by Slice 4` and plan note 2.
    A catalog entry that defers work the cycle actually did is the same false-description defect this
    cycle exists to repair. If the catalog quotes L1's figures, the correct one is **one** distinct
    broken citation (`#"The first half shared by"`), not two — plus, from this pass, **one** more
    (the retired-phrase citation #"Every `Meta` key whose value is a set of field names…"), both
    inside this artifact.

20. **Observation, still not dispatched.** `types/base.py::_format_unknown_fields_error` enumerates
    its callers and is currently complete and correct (re-verified: it names `Meta.fields`,
    `Meta.exclude`, `Meta.optimizer_hints`, `nullable_overrides`, `required_overrides`,
    `filesystem_path_fields`, `relation_shapes`). It carries the same rot risk Decision 1 removed
    from `_selected_meta_targets`, and the argument for deleting it is already made in the plan.
    Left alone; noted so a future pass does not have to re-derive it.

21. **DRY candidate surfaced by the L2 re-derivation, recorded not dispatched.**
    `types/base.py::_validate_optimizer_hints` performs its own unknown-name and not-in-selected-set
    checks inline instead of routing through `_selected_meta_targets`, sharing only
    `_format_unknown_fields_error`. The difference is real — it validates against selected *relation*
    names and its targets are dict keys — so this is a genuine question, not an obvious consolidation,
    and it is squarely out of a comment-repair slice's scope. It is also **the fact that makes the L2
    ruling non-arbitrary**: it is why no exact universal predicate exists for the seam's membership.
    Candidate for a future spec's DRY pass, not for this cycle.
