# Build: Slice 2 — Code correction: citation and provenance rot in `.py` files

Spec reference: `docs/SPECS/spec-028-orders-0_0_8.md` (read-only this slice; Slice 3 owns every spec edit). The input contract is [`build-028-orders-0_0_8.md`][build-028] `## Pre-dispatch verification` -> `### Code work verified as needed (Slice 2 only)`.
Status: final-accepted

## Plan (Worker 1)

### What this slice is, in one paragraph

Eight `.py` files carry citations and provenance notes that a future reader cannot resolve: a review-item id, raw line numbers into a spec Slice 1 has just renumbered, raw `path:NN` line numbers into a source file the DRY-squeeze reshaped, ordinals into an unnumbered list, a wrong-layer pointer, a stale count banner, and a docstring describing an `except ImportError` guard that no longer exists. **Every edit is comment or docstring text. Not one executable statement changes.** The governing rule is [`AGENTS.md`][agents] #"No process provenance in code" plus [`AGENTS.md`][agents] rule 27 (`path::QualifiedName` refs, raw `path:NN` only in per-cycle scratchpads).

### Census correction: the input contract undercounted C2, and there are two more classes

Worker 0's `### Code work verified as needed (Slice 2 only)` names six classes. Re-measured against the working tree by this pass, **two of its counts are low and two further classes exist in the same eight files**. Every number below is an *occurrence* count with the command that produced it, so the reader re-derives rather than accepts.

The instrument that undercounted is the one my own notebook warns about: a single-line `grep` cannot see a citation reflowed across two source lines, and a pattern anchored on `spec-028` cannot see a citation that says only `spec line`.

```shell
# The whitespace-flattened probe. Run from the repository root.
uv run python - <<'PY'
import re
from pathlib import Path

files = [
    "django_strawberry_framework/types/base.py",
    "django_strawberry_framework/orders/base.py",
    "django_strawberry_framework/orders/inputs.py",
    "tests/types/test_base.py",
    "tests/orders/test_inputs.py",
    "tests/test_registry.py",
    "examples/fakeshop/apps/library/orders.py",
    "examples/fakeshop/test_query/test_library_api.py",
]
pats = {
    "raw-line-citation": re.compile(r"\blines?\s+\d+", re.I),
    "path-NN-citation": re.compile(r"[\w./]+\.py:\d+"),
    "Test-N-ordinal": re.compile(r"\bTests?\s+\d+"),
    "review-item-id": re.compile(r"spec-\d{3}\s+[A-Z]\d+|\brev-?\d|adversarial|\bNit\s+\d", re.I),
}
for f in files:
    flat = re.sub(r"\s+", " ", Path(f).read_text())
    for name, pat in pats.items():
        hits = pat.findall(flat)
        if hits:
            print(f"{f}  [{name}] {len(hits)}: {sorted(set(hits))}")
PY
```

| Class | Worker 0's figure | Re-measured | Why the first reading was low |
|---|---|---|---|
| C1 `(spec-028 N3)` | 2 occurrences | **2** — agrees | — |
| C2 raw spec-line-number citations | 2 | **5 occurrences over 4 lines** | `spec-028[^"]*lines? [0-9]` requires the `spec-028` token; two sites say only `Spec line`, and one of those two is **wrapped across two source lines** (`per spec line` / newline / `1039)`) so no single-line pattern can see it at all |
| C3 `Test <N>` ordinals | 9 | **10 occurrences over 9 lines** | line 46 of `orders.py` carries two (`Test 9` and `Test 10`); 9 was the matching-line count, not the occurrence count |
| C4 wrong-layer citation | 1 | **1** — agrees | — |
| C5 stale count banner | 1 banner, section holds 16 functions | **1 banner; 16 functions / 19 rows** | Worker 0's first reading of 15 came from `grep -cE '^def test_.*order'`; re-measured by line range (below) |
| C6 false `except ImportError` docstring | 1 | **1 in scope; 2 more siblings in the same file belong to other cards** | — |
| **C7 raw `path:NN` citations (NEW)** | not named | **8 refs over 7 lines**, all in `tests/orders/test_inputs.py` | not searched for; the pattern is `inputs.py:NN`, not `spec-028 … line NN` |
| **C8 wrong-target Decision citation (NEW)** | not named | **1** | not searched for; it is a `spec-028 + Decision 11` malformation, invisible to `spec-028 Decision [0-9]` |

C7 and C8 are the same defect class as C2 and C4, in files this slice already owns, and three of C7's refs point **past the end of the file they cite**. Leaving them would reproduce the failure this cycle exists to close: a cohort repairing three citations in a file and leaving eight rotted ones beside them. They are in scope, flagged here so Worker 3 audits the expansion rather than reading it as scope creep.

### DRY analysis

- **Helper inventory checked.** Refreshed for the **whole package** this pass — `docs/shadow/helper-inventory.md`, 1,926 lines over every `.py` under `django_strawberry_framework/` (the `worker-1.md` `### Package-wide helper inventory before helper planning` command, verbatim). Shapes grepped: `citation`, `provenance`, `docstring`, `comment`, `banner`, `census`, plus the specific symbols this slice's replacement text must name (`camel`, `input_type_name`, `iter_set_subclasses`, `safe_import`, `make_set_input_namespace`). **No helper candidate found and none is needed:** this slice adds no helper, shared constant, validation branch, coercion utility, or test helper, because it changes no executable statement. The inventory's value here was the reverse — it *confirmed the durable symbol names* the replacement citations must use (`utils/strings.py::graphql_camel_name`, `utils/inputs.py::build_strawberry_input_class`, `::iter_set_subclasses`, `::_safe_import`, `::clear_generated_input_namespace`, `utils/input_values.py::iter_input_items`).
- **Existing patterns reused.** Three, all already in the tree:
  1. **The repaired filter twin** at `tests/test_registry.py::test_clear_tolerates_unimportable_filter_submodules` is the template for C6 — a concurrent session rewrote it mid-cycle and the order twin must read as the same story.
  2. **The unadorned invariant comment** at `django_strawberry_framework/types/base.py::_validate_filterset_class` #"In-function import: dodges the" — a two-line comment stating the cycle invariant with **no citation at all**. That is the model for C1.
  3. **The house citation vocabulary**, measured: `spec-028 Decision N` (37), `spec-028 test plan` (5), plus `spec-028 Decision N step M`, `spec-028 Decision N Layer M`, and `spec-028 Decision 8 Edge case`. Every replacement below uses a form already in use, so nothing new is invented.
- **New helpers justified.** None. The condition that would justify one: if a future slice needed the *section census* (`16 functions / 19 rows`) asserted programmatically rather than written in a banner, that would be a test, not a helper — and it is not this slice's, because the count is documentation of a test section, not a contract.
- **Duplication risk avoided.** Two, both real:
  1. **A new `spec-028 #"substring"` citation.** Slice 3 rewrites prose across every Decision, so any substring citation introduced now is a citation Slice 3 can silently break, and **no gate sees it** (`scripts/check_citations.py` resolves `path::Symbol` only, and `docs/` is outside its scope). **The plan therefore introduces ZERO new `spec-028 #"…"` citations.** Measured precondition: `grep -rohE --include='*.py' 'spec-028[^)]*#"' django_strawberry_framework/ tests/ examples/ | wc -l` -> **0**. The postcondition is also 0.
  2. **A second copy of the C6 story.** `tests/test_registry.py` holds four sibling tests with the same false premise. Repairing the order twin by *paraphrasing* the filter twin would create two divergent tellings of one mechanism. The plan instead has Worker 2 **mirror the filter twin's shape and vocabulary**, so the two read as one story, and leaves the other two twins untouched (see `### Deliberately NOT touched`).

### Boundary count, and the split question answered in writing

**Zero new boundaries.** This slice adds no guard, cap, gate, rejection path, or validation branch — the entire diff is comment and docstring text, and not one executable statement changes. Per [`BUILD.md`][build] `### What needs a proof, and what does not`, **no failability proof is owed by Worker 2**, and `### Failability proofs` in the build report is to read `None; this pass introduced no new boundary.`

**The split question, answered rather than left to inference** ([`BUILD.md`][build] `### Slice splitting`): the slice stays **one unit**. Both split triggers are addressed on their own terms:

- **Boundary-count trigger: zero.** There are no proofs to load the builder with, which is the load the trigger exists to bound.
- **Diff-shape trigger: one coherent unit.** Eight files, ~30 lines of prose, one defect family (unresolvable citations), one governing rule (`AGENTS.md` rule 27 + #"No process provenance in code"). The findings are not separable in a way that helps review: C1/C2/C7 are the same "the coordinate is gone" defect at three different coordinate systems, and C4/C8 are the same "the coordinate points at the wrong thing" defect. Splitting would cost two extra artifacts and two extra full worker cycles to review ~15 lines each.
- **The one axis on which a split WOULD be defensible** is C6, whose repair carries a judgement call (does the test still pin anything?) rather than a mechanical substitution. It stays in this slice because the judgement is Worker 3's and needs no separate builder pass; it is called out under `### Test additions / updates` so it cannot be lost in the mechanical work.

### Hot-path declaration

**Not applicable; the plan declares no hot path for this cycle.** Copied from the build plan's preamble: *"Hot-path declaration: none. No production behavior changes. Slice 2 edits comment and docstring text only; nothing runs per request, per resolver, per row, per connection, or per outbound message."* **No before/after number is owed by this slice.** `### Hot-path budget` in the build report is to read `Not applicable; plan declares no hot path.`

### Floor verification

**Not applicable; the plan declares floor-verification scope `none`.** No slice in this cycle touches a Django / Strawberry / channels integration seam, because no slice changes an executable statement. **No floor venv is built and no floor run is owed.** For reference only, from [`BUILD.md`][build] `## Floor verification`: the supported floor is Django 5.2.16 on Python 3.10 with strawberry-graphql 0.316.0. Nothing in this slice reasons about version-dependent behavior. `### Floor verification` in the build report is to read `Not applicable; plan declares floor-verification scope none.`

### Static inspection helper

Run for `django_strawberry_framework/types/base.py`, the only touched file under `django_strawberry_framework/types/`:

```shell
uv run python scripts/review_inspect.py django_strawberry_framework/types/base.py --output-dir docs/shadow
```

Exit 0; wrote `docs/shadow/django_strawberry_framework__types__base.overview.md` (18,542 bytes) and `…stripped.py`.

**Skipped for the other seven files, with the reason:** [`BUILD.md`][build] `### When to run the helper during build` obliges Worker 1 to run it "when the plan **adds logic** to any existing `.py` file of 150+ source lines, or to any file under `optimizer/` or `types/`." This plan adds **no logic** to any file, so the trigger does not fire for any of the eight — `types/base.py` was run anyway because it is under `types/` and the run is free. Worker 2 and Worker 3 are likewise not obliged (`### When to run the helper during build`'s Worker 3 triggers are new files, `optimizer/` / `types/` source changes, and 30+/50+ new logic lines; this slice hits none). **A skip is recorded, not assumed.** Note that shadow line numbers are shifted by the stripping pass and are never citable — which is the same defect this slice repairs.

### Working-tree discipline: three of the eight files are baseline-dirty

`tests/types/test_base.py` (C1), `tests/test_registry.py` (C6), and `examples/fakeshop/test_query/test_library_api.py` (C3, C5) all carry uncommitted work that is **not this cycle's**. Both Worker 2 and Worker 3 apply this:

- **Diff with `git diff HEAD -- <path>`, never `git diff -- <path>`.** A concurrent session's `git add` makes the latter read clean, so the plain form will tell you a dirty file is untouched. Verified this pass: `git diff HEAD --stat -- tests/test_registry.py` reports `20 ++++++--- / 12 insertions, 8 deletions`, and `git diff -- tests/test_registry.py` is the reading that can lie.
- **Edits are additive to the named lines. No `027` hunk is ever reverted, tidied, or reformatted.** Never `git checkout`, `git restore`, `git stash`, or `git worktree` on any of the eight.
- **`tests/test_registry.py` changed mid-cycle and its C6 sibling was repaired by someone else.** Read it against HEAD yourself before editing (`git diff HEAD -- tests/test_registry.py`) rather than trusting the build plan's quotation of the docstring — the quotation predates the concurrent edit.
- **Run `ruff` scoped to your own files, never `.`**: `uv run ruff format <the files this pass touched>` then `uv run ruff check --fix <the same files>`. A repo-wide write-mode run would reformat the concurrent session's in-flight code. Then `git status --short`: any file outside `### Files touched` is a **stop-and-report**, never a revert.

### Implementation steps

Line numbers are pin-at-write-time navigational hints — verify against the current source before editing, because three of these files are being written by another session. Every anchor below is *also* given as a unique substring so it survives a shift.

---

#### C1 — retire the review-item id `(spec-028 N3)` (2 occurrences)

`N3` was rev-1 review Nit 3. Slice 1 moved the whole revision history into the rationale companion, so `N3` is now unresolvable **from the spec at all** — and a review-item id was never resolvable to a future reader in the first place ([`AGENTS.md`][agents] #"No process provenance in code"). **The invariant is already stated in both sentences**, so the durable replacement is the first-preference form: no citation at all.

1. `django_strawberry_framework/types/base.py::_validate_set_sidecar` #"(spec-028 N3) and the ``None``-means-unset" (~line 150). Delete the parenthetical and reflow:

   ```
       The type-gate skeleton ``Meta.filterset_class`` and ``Meta.orderset_class``
       share. Wrappers keep the cycle-safe local import of ``FilterSet`` /
       ``OrderSet`` in their own body and the ``None``-means-unset
       short-circuit; this owns only the subclass check and the
       ``must be {article} {expected.__name__} subclass`` wording.
   ```

   Why no replacement citation: the sibling comment 26 lines below (`_validate_filterset_class` #"In-function import: dodges the") states the same invariant with no citation, and this helper serves **both** subsystems — a lone `spec-028` pointer on a shared helper is asymmetric as well as unresolvable.

2. `tests/types/test_base.py::test_filterset_and_orderset_meta_validators_ride_validate_set_sidecar` #"cycle-safe local imports (spec-028 N3); the" (~line 760). Delete the parenthetical:

   ```
       The wrappers keep the cycle-safe local imports; the subclass check
       and ``must be {article} {Name} subclass`` wording live once in the
       shared helper.
   ```

   The test body already *asserts* the invariant by source inspection (`assert "from ..orders.sets import OrderSet" in src_order`), so the docstring needs no external pointer.

**Expected effect on the `spec-028` census:** −2 occurrences (68 -> 66). Record it, so the integration pass does not read the drop as breakage.

---

#### C2 — retire the raw spec-line-number citations (5 occurrences over 4 lines)

[`AGENTS.md`][agents] rule 27 permits raw `path:NN` "only in per-cycle scratchpad artifacts … never in code comments specs or standing docs". All five were already pointing at the wrong place before Slice 1; Slice 1 renumbered the whole spec, so they are now arbitrary.

3. `django_strawberry_framework/orders/inputs.py::_get_concrete_field_names_for_order` #"per spec-028 Decision 3 line 452. The" (~line 167). Drop ` line 452` and reflow the sentence onto one line:

   ```
       Backs ``OrderSet._expand_meta_fields`` when ``Meta.fields = "__all__"``
       per spec-028 Decision 3. The cookbook's ``get_concrete_field_names``
       at ``django_graphene_filters/mixins.py`` uses ``hasattr(f, "column")``
   ```

   `spec-028 Decision 3` is the correct target and a durable form (37 existing uses). Verified: Decision 3's `**Meta.fields = "__all__" scope**` paragraph is what the helper implements.

4. `django_strawberry_framework/orders/inputs.py::_build_input_fields` #"Spec Edge cases line 980) maps python attr" (~line 227). Drop ` line 980`:

   ```
       Populates ``_field_specs`` so the runtime ``normalize_input_value``
       walker can reconstruct the ORM path from each Strawberry input
       dataclass attribute. The ``shelf__code`` flat-shorthand path (per
       spec-028 Edge cases) maps python attr ``shelf_code`` ->
       GraphQL alias ``shelfCode`` -> django source path ``shelf__code``.
   ```

   `spec-028 Edge cases` is a durable form already in use (`orders/inputs.py` neighbours it with `spec-028 Decision 8  Edge case`). Verified: the spec's Edge-cases bullet #"**`Meta.fields = ["shelf__code"]`**" pins exactly this shape.

5. `tests/orders/test_inputs.py::test_ordering_enum_has_six_members` #"spec-028 Decision 5 lines 525-532 are present" (~line 62). Drop ` lines 525-532`:

   ```
       """All six members from spec-028 Decision 5 are present."""
   ```

   This also makes the docstring consistent with its own immediate neighbour, `::test_ordering_member_values_are_string_names`, which already reads `(Decision 5)` with no line range.

6. `examples/fakeshop/test_query/test_library_api.py::test_root_get_queryset_runs_before_order_apply` #"Spec line 1038 names ``name: DESC``" (~lines 2206-2217). **This one is a deletion, not a substitution, and it is the wrapped site** — `per spec line` ends line 2207 and `1039)` opens 2208, which is why no single-line grep saw it.

   The paragraph exists only to narrate a divergence between the spec and the code. **That divergence no longer exists:** the spec's Test-plan bullet for this test now reads `orderBy: [{ city: DESC }]` and explains the `city`-not-`name` choice itself. So the claim "Spec line 1038 names `name: DESC` as the order field" is **false against the current spec**, and per [`worker-1.md`][worker-1] `### Performing the rationale move` a falsified sentence is deleted rather than repaired. Replace lines 2206-2217 with the invariant alone:

   ```
       """Spec-028 test plan - root ``get_queryset`` runs before ``apply_sync``.

       ``BranchType.get_queryset`` strips ``city="restricted"`` for
       anonymous users so the DESC order clause sees only the visible
       rows. Staff bypass the gate and see all rows ordered.

       Orders by ``city`` (an unguarded scalar) rather than ``name``:
       ``BranchOrder.check_name_permission`` would deny the anonymous
       half before any row reached the order clause, and the staff client
       cannot substitute because staff bypass the very ``get_queryset``
       hook under test. The relation-gate test's quiet half substitutes
       ``city`` for ``name`` for the same reason.
       """
   ```

   Keep the existing `Spec-028 test plan` opener — that is the durable pointer, and it is already there.

---

#### C7 — retire the raw `path:NN` citations into `orders/inputs.py` (8 refs over 7 lines) — NEW CLASS

All seven live in `tests/orders/test_inputs.py`, in one contiguous `# inputs.py edge-case branches` block. They are rule-27 violations twice over: raw line numbers, **and** a bare `inputs.py` basename that resolves ambiguously to **six** files in this repo (`filters/`, `forms/`, `mutations/`, `orders/`, `rest_framework/`, `utils/`) — which is precisely the ambiguity `check_citations.py`'s docstring says rule 27 exists to remove.

They have also **rotted past the end of the file**: `orders/inputs.py` is 388 lines, and three cited coordinates are `410`, `461-462`, `476-477`. And the expressions they quote have moved into the shared substrate or been reshaped by the DRY-squeeze, so this class carries a **content** correction as well as a coordinate one.

**Every replacement is a `path::Symbol` form, which moves the citation from ungated to gated** — `scripts/check_citations.py` is fail-closed on first-party `.py` refs, so from this slice forward a rename breaks the build instead of rotting silently. Each target below was verified present this pass.

| Line | Current | Replace with | Verified |
|---|---|---|---|
| ~747 | ``Closes ``inputs.py:168`` -- ``if not parts: return name`` early return.`` | ``Covers ``utils/strings.py::graphql_camel_name`` #"if not core:" -- the all-underscore passthrough behind the ``orders/inputs.py`` ``_camel_case`` alias.`` | `orders/inputs.py` #"_camel_case = graphql_camel_name"; the guard at HEAD is `core = name.strip("_")` / `if not core: return name`. **The quoted expression changed** (`parts` -> `core`); the test's own assertions (`""`, `"_"`, `"__"` unchanged) already match current behavior. |
| ~761 | ``Closes ``inputs.py:222`` -- ``description`` kwarg threads through ``strawberry.field``.`` | ``Covers ``utils/inputs.py::build_strawberry_input_class`` -- the ``description`` kwarg threading through ``strawberry.field``, reached via the ``orders/inputs.py`` ``build_input_class`` alias.`` | `orders/inputs.py` #"build_input_class = build_strawberry_input_class"; the target's own docstring names the `description=` kwarg. |
| ~778 | ``Closes ``inputs.py:336`` -- ``if dataclass_fields is None: return []``.`` | ``Covers ``utils/input_values.py::iter_active_fields`` #"if items is None:" -- a non-walkable input yields nothing, so ``normalize_input_value`` returns ``[]``.`` | `iter_input_items` returns `None` for a non-dict without `__dataclass_fields__`; `iter_active_fields` returns on `if items is None:`. **The cited expression is not the one that runs** — `if dataclass_fields is None` is now one layer deeper, inside `::iter_input_items`. |
| ~794 | ``Closes ``inputs.py:344`` -- ``if spec is None: continue`` defensive skip.`` | ``Covers ``orders/inputs.py::normalize_input_value`` #"if field.spec is None:" -- the defensive skip.`` | Still in this file, reworded `spec` -> `field.spec`. |
| ~823 | ``Closes ``inputs.py:352`` -- ``if child_orderset is None: continue`` skip.`` | ``Covers ``orders/inputs.py::normalize_input_value`` #"if child_orderset is None:" -- the placeholder-branch skip.`` | Still in this file, expression unchanged. |
| ~873 | ``Closes ``inputs.py:410`` -- ``if cls in seen: continue`` diamond dedup.`` | ``Covers ``utils/inputs.py::iter_set_subclasses`` #"if cls in seen:" -- the diamond dedup behind the ``orders/inputs.py`` ``_iter_orderset_subclasses`` alias.`` | `orders/inputs.py` #"_iter_orderset_subclasses = iter_set_subclasses". **`410` is past EOF (388 lines).** |
| ~904 | ``Closes ``inputs.py:461-462`` and ``inputs.py:476-477`` in ONE test.`` | ``Covers both best-effort submodule lookups in ``utils/inputs.py::clear_generated_input_namespace`` in ONE test -- the two ``utils/inputs.py::_safe_import`` calls whose ``None`` return drives the ``if factory_cls is not None:`` / ``if set_root is not None:`` skips.`` | `clear_order_input_namespace` at HEAD is a two-line wrapper over `make_set_input_namespace`'s clear and carries **no** `except ImportError` of its own. **Both coordinates are past EOF.** |

7. Additionally, both cross-test line ranges in the same block are wrong **and swapped**, and point into a baseline-dirty file the concurrent session is still writing:

   - ~877: `(lines 1036-1056)` cites the twin `tests/filters/test_inputs.py::test_iter_filterset_subclasses_dedupes_diamond_inheritance`, which is at line **1450**.
   - ~908: `(lines 1009-1028)` cites `tests/filters/test_inputs.py::test_clear_filter_input_namespace_tolerates_unimportable_submodules`, which is at line **1417**.

   **Both docstrings already name the twin by full `path::Symbol`.** The repair is to delete the parenthetical line range and keep the name. No new citation is written.

8. While in the ~904 docstring, correct the mechanism sentence too. It currently says *"Setting `sys.modules[name] = None` makes `from ... import ...` raise `ImportError`, exercising BOTH `except ImportError: pass` guards in `clear_order_input_namespace`."* At HEAD `clear_order_input_namespace` has no such guard. Restate as the invariant: the `None` sentinel makes the shared helper's two `_safe_import` lookups return `None`, and each `is not None` skip is the branch under test. **This is the C6 defect in a second file — repair it here so the two stories agree.**

---

#### C3 — retarget the `Test <N>` ordinals to the tests' actual names (10 occurrences over 9 lines)

The spec's `### examples/fakeshop/test_query/test_library_api.py (extend)` section is a **bulleted** list, so no ordinal resolves; and the shipped section now holds 16 functions against the plan's 14, so an ordinal a reader counted out would land on the wrong test. An ordinal into an unnumbered list is process provenance in the exact sense [`AGENTS.md`][agents] bans.

**The ordinal -> name mapping, derived by walking the spec's Test-plan bullets in order and matching each against the shipped section (all names verified present):**

| Ordinal | Shipped test |
|---|---|
| Test 1 | `test_library_branches_order_by_name_asc` |
| Test 3 | `test_library_books_order_by_forward_fk_relation` |
| Test 7 | `test_library_books_order_preserves_optimizer_cooperation` |
| Test 8 | `test_root_get_queryset_runs_before_order_apply` |
| Test 9 | `test_order_check_permission_denies_for_active_field` |
| Test 10 | `test_order_check_permission_quiet_for_inactive_field` |
| Test 11 | `test_order_check_permission_denies_active_related_branch` |
| Test 12 | `test_library_books_order_by_multi_field_priority` |

**One of the ordinal claims is substantively wrong, not merely unresolvable.** `examples/fakeshop/apps/library/orders.py` ~line 102 says the nested `shelf: ShelfOrderInputType` surface is *"used by Tests 3, 7, 8, and 12"*. Measured repo-wide, the nested order input is used by exactly **two** live tests:

```shell
grep -rn --include='*.py' '{ shelf: {' examples/ tests/
# -> test_library_api.py:1862  (test_library_books_order_by_forward_fk_relation)
# -> test_library_api.py:2378  (test_library_books_order_by_multi_field_priority)
```

Test 7 orders by `title: ASC` and merely *selects* `shelf { code }` (an output-type surface, not an order-input one); Test 8 orders `Branch` rows by `city: DESC` and touches no shelf at all. **So the retarget corrects 4 -> 2.** Worker 2 writes the two names, not four.

**Citation form:** the bare basename `test_library_api.py::<name>` — verified unique in the repo (one match under `django_strawberry_framework/`, `tests/`, `examples/`, `scripts/`), resolvable by `check_citations.py`'s basename index from any directory, and already the form six existing citations use. The full path form is **not** used here: `examples/fakeshop/test_query/test_library_api.py::` is 48 characters, which pushes the longest names past the 110-column E501 grace and forces a wrap.

> **Wrap hazard — this is the one way to get C3 wrong.** A `path::Symbol` citation broken across two source lines is invisible to `check_citations.py`, which turns a gated citation back into silent rot. There are already two such wrapped citations in this repo (`tests/test_list_field.py` ~29 and ~1269). **Every citation Worker 2 writes must sit unbroken on one line.** `ruff format` does not rewrap docstring prose, and E501 is graced to 110 columns, so the basename form always fits: longest case is `        ``test_library_api.py::test_order_check_permission_denies_active_related_branch``` at 89 columns.

9. `examples/fakeshop/apps/library/orders.py::BranchOrder.check_name_permission` docstring (~lines 46-52), which carries four of the ten occurrences:

   ```
           """Active-input-only scalar gate: denies an anonymous order by ``name``.

           The gate fires ONLY when the consumer's input names ``name``
           (``orderBy: [{ name: ASC }]``); an input naming another scalar
           (``orderBy: [{ city: ASC }]``) leaves it quiet. Both halves are
           pinned live by
           ``test_library_api.py::test_order_check_permission_denies_for_active_field``
           and
           ``test_library_api.py::test_order_check_permission_quiet_for_inactive_field``.
           """
   ```

10. `examples/fakeshop/apps/library/orders.py::BranchOrder.check_shelves_permission` docstring (~lines 62-69), three occurrences:

    ```
            """Active-related-branch gate: denies an anonymous order through ``shelves``.

            Active-branch dispatch: the gate fires ONLY when the consumer's
            input names the ``shelves`` RelatedOrder branch
            (``orderBy: [{ shelves: { code: ASC } }]``); an input naming the
            unguarded ``city`` scalar fires neither this gate nor
            ``check_name_permission``. Both halves are pinned live by
            ``test_library_api.py::test_order_check_permission_denies_active_related_branch``.
            """
    ```

11. `examples/fakeshop/apps/library/orders.py::BookOrder` docstring (~lines 97-103), the `Tests 3, 7, 8, and 12` sentence — the 4 -> 2 correction:

    ```
        ``BookOrder.Meta.fields`` carries the path-shorthand ``"shelf__code"``
        which renders as ``shelfCode: Ordering`` on the input type per
        spec-028 test plan (flat-shorthand path), pinned live by
        ``test_library_api.py::test_library_books_order_by_flat_shorthand_path``.
        The explicit ``shelf = RelatedOrder("ShelfOrder", field_name="shelf")``
        declaration produces the nested-shape ``shelf: ShelfOrderInputType``
        surface, pinned live by
        ``test_library_api.py::test_library_books_order_by_forward_fk_relation``
        and
        ``test_library_api.py::test_library_books_order_by_multi_field_priority``.
        Both surfaces coexist on the same input type.
    ```

12. `examples/fakeshop/test_query/test_library_api.py::test_library_branches_order_by_name_asc` docstring (~lines 1783-1791), the remaining two occurrences. `Test 1` is a self-reference — a test citing its own ordinal — so it is deleted rather than retargeted:

    ```
        """Spec-028 test plan - scalar ASC on ``Branch.name``.

        Uses staff context because ``BranchOrder.check_name_permission``
        (declared in ``apps.library.orders``) denies anonymous requests
        that order by ``name``. That gate is what
        ``test_order_check_permission_denies_for_active_field`` pins; this
        test pins the ASC ordering contract instead, so it bypasses the
        gate on staff rather than re-asserting the denial.
        """
    ```

    The sibling name needs no path prefix — it is in this same file.

---

#### C4 — correct the wrong-layer citation (1 occurrence)

13. `django_strawberry_framework/orders/base.py` #"Layer 2 of the spec-028 six-layer plan" (line 3). **`Layer 2` -> `Layer 1`.** One word.

    Verified against Decision 3: **Layer 1** is *"Lazy class references in `RelatedOrder` … `RelatedOrder` accepts target as class, absolute import path string, or unqualified name. `_orderset` stores it unresolved; the `.orderset` property triggers resolution"* — which is exactly and only what this module ships. **Layer 2** is the module-fallback resolution, which lives in `django_strawberry_framework/sets_mixins.py::LazyRelatedClassMixin` (not in this slice's writable set, and correctly attributed there). The `docs/GLOSSARY.md` `RelatedOrder` entry independently confirms it: *"The shared Layer-2 module-fallback resolution is a sibling import from `sets_mixins.LazyRelatedClassMixin`."*

    Nothing else in the docstring changes. The module's Layer-2 **reuse** is already stated correctly in the very next sentence (`LazyRelatedClassMixin` is reused from the neutral module via sibling import), so after the one-word fix the docstring reads: this module IS Layer 1, and it consumes Layer 2 from elsewhere. That is the invariant.

14. **Verify before editing, then leave alone:** `django_strawberry_framework/orders/factories.py` #"Layer 5 of the spec-028 six-layer pipeline" is **CORRECT** and is **not in this slice's writable set**. Verified this pass against Decision 3: *"Layer 5 — BFS schema build with module-global materialization (Strawberry-adapted)"*, and the module docstring's own gloss *"(the BFS that builds every …)"* matches. Worker 2 re-confirms and does not touch the file. Do not chase the `plan` / `pipeline` wording difference between the two docstrings — it is cosmetic and touching `factories.py` is out of scope.

---

#### C5 — replace the stale count banner (1 banner)

15. `examples/fakeshop/test_query/test_library_api.py` #"(spec-028 - 14 acceptance tests)" (line 1738).

    **Re-measured by line range, not by a name pattern** — the pattern reading is what produced two wrong numbers already (Worker 0's `grep -cE '^def test_.*order'` gave 15, missing `test_library_genres_connection_pages_by_to_many_aggregate` because its name carries no `order` token):

    ```shell
    # Section bounds: the spec-028 banner at 1738 to the spec-029 banner at 2482.
    grep -n 'spec-028 - 14 acceptance tests\|^# spec-029' examples/fakeshop/test_query/test_library_api.py
    awk 'NR>=1738 && NR<=2482 && /^def test_/' examples/fakeshop/test_query/test_library_api.py | wc -l   # -> 16
    awk 'NR>=1738 && NR<=2482 && /parametrize/'  examples/fakeshop/test_query/test_library_api.py          # -> one, at 1813
    ```

    **16 test functions. Exactly one is parametrized** (`test_library_books_order_by_subtitle_null_positioning`, four NULLS directions), so **19 test rows**: 16 − 1 + 4.

    The two functions the spec names nowhere are `test_library_branches_order_by_scalar_then_to_many_aggregate_no_multiplication` and `test_library_genres_connection_pages_by_to_many_aggregate`; both docstrings identify them as the row-preserving to-many aggregate contract from `spec-030-connection_field-0_0_9` P1-B, and the section's own seed helper at ~1746 already cites that spec. Naming them **gives the count a subject**, which is what the old banner lacked.

    ```
    # ---------------------------------------------------------------------------
    # Live HTTP order coverage (spec-028 test plan), plus the row-preserving
    # to-many aggregate cases from ``spec-030-connection_field-0_0_9`` P1-B.
    # 16 test functions / 19 test rows -- the three extra rows come from
    # ``test_library_books_order_by_subtitle_null_positioning``, parametrized
    # over four NULLS directions.
    # ---------------------------------------------------------------------------
    ```

    The multi-line-inside-the-rules shape is this file's own convention (compare the `spec-029` banner at 2482). **A count in a banner is a standing rot risk** — no gate maintains it — but the instruction is to keep a number and disambiguate functions from rows, and naming both the subject and the derivation is what makes the next re-measurement cheap. Recorded under `### Notes for Worker 1 (spec reconciliation)` so the integration pass sees the residual risk.

---

#### C6 — repair the docstring describing a guard that no longer exists (1 in scope)

16. `tests/test_registry.py::test_clear_tolerates_unimportable_order_submodules` (~lines 1655-1663). It opens *"Both order-side `except ImportError` guards in `clear()` are best-effort"* and says the co-clear *"uses cycle-safe local imports per spec-028 Decision 9."* **Both claims are false at HEAD.** Verified this pass:

    - `django_strawberry_framework/registry.py::TypeRegistry.clear` contains **no** `except ImportError` and **no** local subsystem import for any subsystem. Its whole subsystem step is `for clear in iter_subsystem_clears(): clear()`.
    - Each subsystem binds its own teardown at **its** import time: `orders/inputs.py` registers `clear_order_input_namespace` (owner `orders.input_namespace`, `before_bind=True`); `orders/__init__.py::_clear_helper_referenced_ordersets` registers under owner `orders.helper_references`. `orders/__init__.py`'s own comment already records that the older shape *"predates the registration seam."*

    **The repaired filter twin immediately above is the template.** A concurrent session rewrote `::test_clear_tolerates_unimportable_filter_submodules` mid-cycle to *"`clear()` itself imports nothing, so a broken `sys.modules` cannot break it"* — with the reasoning that every submodule lookup the replayed callback makes is best-effort. **Read that twin against the current tree yourself** (`git diff HEAD -- tests/test_registry.py`); it arrived mid-cycle and is not this cycle's work. Mirror its shape and vocabulary so the two twins read as one story, then substitute the order specifics (`orders.inputs` / `orders`, `spec-028 Decision 9`).

    Also update the inline comment at ~1675-1676 (*"makes `from <name> import ...` raise ImportError, exercising both order-side guards"*), mirroring the filter twin's rewritten comment. Leaving the docstring right and the comment wrong is a half-fix.

17. **Worker 3 judges whether the test still pins anything at all, and records the judgement.** This is a named deliverable of the slice, not an optional extra. The question is real: poisoning `sys.modules` cannot reach a callback whose function object was captured at import time, and the callback's own `_safe_import` lookups target `orders.factories` / `orders.sets` — **not** the two modules the test poisons. So the test may be pinning only "`clear()` does not raise", which is trivially true of a function that imports nothing.

    My reading, offered as a starting point and not as the answer: it still pins a real **negative** invariant — *`clear()` performs no direct import of the order submodules* — because reintroducing a `from .orders.inputs import clear_order_input_namespace` inside `clear()` would make the poisoned module raise and the test fail. That is exactly what the repaired filter twin now claims for its half.

    Worker 3 may confirm this by mutation under its narrow source carve-out ([`BUILD.md`][build] `### Who performs it`): add such an import inside `TypeRegistry.clear`, run `uv run pytest tests/test_registry.py --no-cov`, and check whether the order twin fails. **`django_strawberry_framework/registry.py` is NOT in this slice's writable set**, so if Worker 3 takes this path it must record the mutation in the artifact *before* making it, revert it inside the same pass, and **prove the revert by byte-comparison** (`cp` to a scratch path **outside** the repo first, then `cmp`) — never `git checkout`. No failability proof is *owed* (zero new boundaries); this is a diagnostic, and a reasoned answer with the mechanism spelled out discharges the obligation just as well.

    **Whichever way the judgement lands, no worker deletes the test and no worker silently accepts it.** A boundary-less test is a finding for the maintainer. If Worker 3 concludes it pins nothing, that goes in the review section as a Low finding with the mechanism, and I carry it to `### Notes for Worker 1 (spec reconciliation)` for the maintainer at final verification.

---

#### C8 — correct the wrong-target Decision citation (1 occurrence) — NEW CLASS

18. `examples/fakeshop/apps/library/orders.py` module docstring, line 10: `(spec-028 + Decision 11)`. Two defects in five characters — a stray `+` that makes the reference malformed (it does not even match `spec-028 Decision [0-9]`, which is why no census counted it), and a wrong target. The sentence it closes is about the Layer-2 `import_string` first-attempt branch resolving an absolute-path `RelatedOrder`. **Decision 11 is the `order_input_type(OrderSet)` consumer helper** and has nothing to do with lazy target resolution. The correct target is Decision 3's Layer 2.

    ```
    (spec-028 Decision 3 Layer 2).
    ```

    `spec-028 Decision N Layer M` is a durable form already in use in this tree (`spec-028 Decision 3 Layer 4`).

### Deliberately NOT touched — verify, then leave alone

Recorded so neither Worker 2 nor Worker 3 reads any of these as an omission, and so nobody "helpfully" fixes one.

- **`django_strawberry_framework/orders/factories.py` #"Layer 5 of the spec-028 six-layer pipeline"** — verified CORRECT (step 14). Not in the writable set.
- **The other two `except ImportError` twins in `tests/test_registry.py`.** `::test_clear_tolerates_unimportable_connection_submodule` (~1691) and `::test_clear_tolerates_unimportable_relay_module` (~1725) carry the **same** false premise as C6 — `TypeRegistry.clear` has no `except ImportError` for any subsystem. Their contracts belong to `spec-030-connection_field-0_0_9` and `spec-032` respectively, whose own residual cycles own them. Repairing them here would mean a worker writing claims about two other cards' behavior this cycle has not verified. **This leaves the file with two of four twins repaired and two not — a known cross-cohort seam, deliberately left, escalated to the maintainer in `### Notes for Worker 1`.** Worker 3: do not flag these as omissions; do flag it if Worker 2 touched them.
- **Raw line-number citations in `.py` files outside the writable eight.** Measured this pass with `grep -rniE '\bspec[^ ]* ?lines? [0-9]|\blines? [0-9]{2,}' --include='*.py' django_strawberry_framework/ tests/ examples/`: further sites in `optimizer/walker.py`, `mutations/{resolvers,fields,sets}.py`, `orders/sets.py`, `tests/optimizer/{test_extension,test_walker}.py`, `tests/mutations/test_sets.py`, `tests/orders/{test_sets,test_factories}.py`, and `examples/fakeshop/test_query/test_products_api.py`. They cite `spec-035`, `spec-036`, `spec-038`, and the upstream cookbook. **Out of scope; do not touch.** Surfaced for the maintainer in `### Notes for Worker 1`.
- **`examples/fakeshop/test_query/test_glossary_api.py`'s pre-archive `"docs/spec-028-orders-0_0_8.md"` strings** — verified-and-rejected by Worker 0 as fixture data, not documentary references. Not in the writable set. Do not re-flag.
- **Every `027`-cycle hunk in the three baseline-dirty files.** Never reverted, never reformatted.
- **The spec and its rationale companion.** Slice 3 owns both. This slice edits no `.md` except this artifact.

### Test additions / updates

**No test is added, removed, renamed, or re-asserted.** Not one executable statement changes, so no test can observe this slice — which is exactly why the verification below is static rather than behavioral.

Two docstring repairs sit on tests and therefore need a reader's judgement rather than an assertion change:

- **C6 (step 17)** — Worker 3 judges whether `::test_clear_tolerates_unimportable_order_submodules` still pins a boundary, per the mechanism, carve-out, and byte-compare requirements spelled out above. **This is a required deliverable of the review pass.**
- **C7 step 8** — the same question in miniature for `tests/orders/test_inputs.py::test_clear_order_input_namespace_tolerates_unimportable_submodules`. Here the answer is already established by reading: the two `except ImportError: pass` guards it names became `utils/inputs.py::_safe_import` calls, so the test **does** still reach both `is not None` skip branches through the wrapper. Only the docstring's coordinates and vocabulary are wrong. Worker 2 fixes the text; Worker 3 confirms the reading.

**Temp tests:** none appropriate. There is no behavior to demonstrate and nothing to prove non-distinguishing. Any temp file Worker 3 writes for the C6 mutation goes under `docs/builder/temp-tests/slice-2/` and is dispositioned in `### Temp test verification`.

**No `pytest` run is planned as routine slice work** ([`AGENTS.md`][agents] #"No pytest after edits"). **No `--cov*` flag in any command, in any pass** ([`BUILD.md`][build] `## Coverage is the maintainer's gate, not a worker's tool`). A focused `uv run pytest <path> --no-cov` is permitted only to confirm an edited test module still **collects** — reasonable for `tests/orders/test_inputs.py`, `tests/test_registry.py`, `tests/types/test_base.py`, and `examples/fakeshop/test_query/test_library_api.py`, since C3/C5/C7 rewrite docstrings and a mangled triple-quote is the one way a prose-only edit breaks something. Prefer the cheaper `uv run python -m compileall -q <files>` if a full collection is awkward under the concurrent tree.

### Implementation discretion items

Assessed and decided as Worker 2's, per [`ARTIFACT.md`][artifact]:

- **Exact line breaks and reflow inside each replacement docstring.** The text above is the content contract, not a character-for-character template. Reflow to read naturally at the file's indent. **Two constraints are NOT discretionary:** a `path::Symbol` citation never wraps across two source lines (the gate goes blind), and no line exceeds the 110-column E501 grace.
- **Whether to write `Covers` or `Closes` in the C7 docstring openers.** `Covers` is used above because the coordinate is a symbol rather than a line and "closes line N" no longer parses; either verb is fine as long as all seven agree.
- **Whether the C6 order twin's opening line paraphrases or reuses the filter twin's sentence.** Reuse-with-substitution is the safer default (the two must read as one story); a paraphrase that stays faithful to the mechanism is acceptable.
- **Ordering of the eighteen edits.** They are independent. Grouping by file is the obvious economy and keeps the scoped `ruff` invocations small.

Not discretionary and not delegated: which Decision / Layer / symbol each citation names, and the 4 -> 2 correction in C3. Those are decided above with their evidence.

### Verification this slice owes, and the exact check for each finding class

Every check re-derivable from its command. Worker 2 records the readings in `### Validation run`; I re-run all of them at final verification rather than reading Worker 2's numbers as measured.

| Finding | Postcondition | Command |
|---|---|---|
| C1 | **0** occurrences of the review-item id | `grep -roh --include='*.py' '(spec-028 N3)' django_strawberry_framework/ tests/ examples/ \| wc -l` |
| C1 | `spec-028` census drops by exactly 2: **68 -> 66** | `grep -rohE --include='*.py' 'spec-028' django_strawberry_framework/ tests/ examples/ \| wc -l` |
| C2 + C7 | **0** raw line-number and `path:NN` citations in the eight files, **whitespace-flattened** so a wrapped citation cannot hide | the flattened probe fenced under `### Census correction` — every class must print nothing |
| C3 | **0** `Test <N>` ordinals in the eight files | same flattened probe (`Test-N-ordinal` class) |
| C3 | the two nested-`shelf` test names cited are the only two that use the surface | `grep -rn --include='*.py' '{ shelf: {' examples/ tests/` -> the two `test_library_api.py` order sites only |
| C4 | `orders/base.py` reads Layer **1**; `factories.py` still reads Layer **5** and is unmodified | `grep -rn --include='*.py' -E 'Layer [0-9] of the spec-028' django_strawberry_framework/` and `git diff HEAD --stat -- django_strawberry_framework/orders/factories.py` (must be empty) |
| C5 | the banner carries **16 functions / 19 rows** and no `14` | `awk 'NR>=1738 && NR<=2482 && /^def test_/' … \| wc -l` -> 16; `awk 'NR>=1738 && NR<=2482 && /parametrize/' …` -> one hit. Re-derive the bounds first (`grep -n 'Live HTTP order coverage\|^# spec-029' …`) — this slice's own edit shifts them |
| C6 | **0** `except ImportError` claims about `clear()` in the order twin; `registry.py::TypeRegistry.clear` still has no such guard | `grep -n 'except ImportError' django_strawberry_framework/registry.py` -> no output; read the order twin against the filter twin |
| C8 | **0** occurrences of the malformed form; `spec-028 Decision N` census rises 37 -> **38** | `grep -rn --include='*.py' 'spec-028 + Decision' examples/`; `grep -rohE --include='*.py' 'spec-028 Decision [0-9]+' django_strawberry_framework/ tests/ examples/ \| wc -l` |
| all | citation gate green, and the count **rises** (every new `path::Symbol` ref is now gate-enforced) | `uv run python scripts/check_citations.py` — baseline `OK: 743 citations resolve (666 in 422 .py files, 77 in KANBAN.md)`, exit 0 |
| all | **0** new `spec-028 #"substring"` citations, single-line AND flattened | `grep -rohE --include='*.py' 'spec-028[^)]*#"' django_strawberry_framework/ tests/ examples/ \| wc -l` -> 0 (baseline 0), plus the flattened equivalent |
| all | ASCII-only `.py`, trailing-comma / layout gate | `uv run python scripts/check_trailing_commas.py --check <the eight files>` |
| all | format + lint, **scoped**, never `.` | `uv run ruff format <files touched>` then `uv run ruff check --fix <the same files>` |
| all | no collateral churn | `git status --short` after both ruff runs; anything outside `### Files touched` is a stop-and-report |
| all | no `027` hunk reverted in the three dirty files | `git diff HEAD -- <path>` per file, confirming the `027` hunks survive alongside the new ones |

Two readings to take **before** editing, so the deltas above are differences and not guesses: the `spec-028` census (68 / 37 / 5) and the citation gate (743, exit 0). Both are recorded above as this pass's measurements.

### Spec slice checklist (verbatim)

The spec's own `## Slice checklist` carries **no entry for this cycle** — `028` shipped as `DONE-028-0.0.8` and its six original slices are all closed and ticked. This slice's contract comes from the build plan's checklist line for Slice 2 plus its `### Code work verified as needed (Slice 2 only)` findings, as corrected by the census above. The boxes below are that contract. **Boxes stay `- [ ]` at planning.** Worker 2 ticks each `- [x]` in the same build report that lands its contract, and only when the change is actually in its diff; I audit every tick at final verification.

- [x] **C1** — retire both `(spec-028 N3)` review-item ids; `django_strawberry_framework/types/base.py::_validate_set_sidecar` and `tests/types/test_base.py::test_filterset_and_orderset_meta_validators_ride_validate_set_sidecar`. Replacement is the invariant with **no** citation.
- [x] **C2** — retire all **5** raw spec-line-number citations over 4 lines: `orders/inputs.py` #"line 452" -> `spec-028 Decision 3`; `orders/inputs.py` #"line 980" -> `spec-028 Edge cases`; `tests/orders/test_inputs.py` #"lines 525-532" -> `spec-028 Decision 5`; and the **wrapped** `line 1038` / `line 1039` pair in `test_library_api.py::test_root_get_queryset_runs_before_order_apply`, **deleted** because the spec now agrees with the code.
- [x] **C3** — retarget all **10** `Test <N>` ordinal occurrences over 9 lines to the tests' actual names, using the unbroken `test_library_api.py::<name>` form; four sites in `examples/fakeshop/apps/library/orders.py`, one in `test_library_api.py`.
- [x] **C3b** — correct the substantive claim inside C3: the nested `shelf: ShelfOrderInputType` surface is used by **two** live tests, not four (`Tests 3, 7, 8, and 12` -> `..._order_by_forward_fk_relation` + `..._order_by_multi_field_priority`).
- [x] **C4** — `django_strawberry_framework/orders/base.py` line 3: `Layer 2` -> `Layer 1`. Verify `orders/factories.py`'s Layer 5 citation is correct and leave the file unmodified.
- [x] **C5** — replace the `(spec-028 - 14 acceptance tests)` banner with the re-measured **16 test functions / 19 test rows**, naming whether the number counts functions or rows and naming the two post-ship `spec-030-connection_field-0_0_9` P1-B additions. **UN-TICKED by Worker 1 at final verification: over-tick.** The count and the functions-vs-rows half landed; the "naming the two post-ship additions" half did not — the shipped banner names their class and source (`the row-preserving to-many aggregate cases from spec-030-connection_field-0_0_9 P1-B`) and neither test name. Repair in step 19 below. **RE-TICKED by Worker 1 at the second final verification: step 19 landed and the box is satisfied in both halves** — the banner carries `16 test functions / 19 test rows`, the parametrized derivation, and both test names, and 16/19 was re-derived from the AST at this pass. The un-tick above is the preserved historical record of pass 1, not a live state.
- [x] **C6** — repair `tests/test_registry.py::test_clear_tolerates_unimportable_order_submodules`'s docstring **and** its inline comment, mirroring the concurrently-repaired filter twin's shape and vocabulary.
- [x] **C6b** — Worker 3 records a judgement on whether that test still pins anything, with the mechanism. No worker deletes it; no worker silently accepts it.
- [x] **C7** — retire all **8** raw `path:NN` citations over 7 lines in `tests/orders/test_inputs.py`, each replaced by the verified `path::Symbol` form in the step-C7 table (three of the old coordinates point past the 388-line EOF).
- [x] **C7b** — delete both wrong-and-swapped cross-test line ranges (`(lines 1036-1056)`, `(lines 1009-1028)`); the twin's full `path::Symbol` name is already in each docstring.
- [x] **C7c** — correct the `except ImportError: pass` mechanism sentence in `::test_clear_order_input_namespace_tolerates_unimportable_submodules` to the shared-substrate `_safe_import` reality.
- [x] **C8** — `examples/fakeshop/apps/library/orders.py` line 10: `(spec-028 + Decision 11)` -> `(spec-028 Decision 3 Layer 2)`.

**Boxes added by Worker 1 at final verification.** C5 is re-opened above; C6c, C9, C10, C11 and C12 are new. All six are specified step-by-step under `### Re-pass steps (Worker 1, final verification)` and carry no architectural discretion.

- [x] **C6c** — narrow the non-operative "every submodule lookup it makes is best-effort, so …" causal clause in **both** `tests/test_registry.py::test_clear_tolerates_unimportable_order_submodules` and `::test_clear_tolerates_unimportable_filter_submodules`, docstring and inline comment in each. The connection and relay twins stay untouched.
- [x] **C9** — `examples/fakeshop/apps/library/orders.py` module docstring line 3: `Five ordersets` -> `Seven ordersets`, naming `PeriodicalOrder` / `IssueOrder` and their keyset-cursor substrate role.
- [x] **C10** — retire the **9 first-party** prose `line NN` citations in `tests/orders/` out of a measured population of 11 (`test_sets.py` 7, `test_factories.py` 3, `test_composition.py` 1); six of the nine point past their target file's EOF. The **2 upstream-cookbook** refs stay byte-identical per Ruling 2 and are named in step 22's table so the skip is recorded, not assumed.
- [x] **C11** — retire all **12** raw `path:NN` citations in `tests/orders/` (`test_sets.py` 10, `test_factories.py` 1, `test_base.py` 1); three past EOF and every one of the twelve pointing at wrong content at its cited line.
- [x] **C12** — respell all **16** in-family bare `Spec Decision N` / `Spec DoD N` citations to the durable `spec-028 …` form, the **wrapped** site at `django_strawberry_framework/orders/sets.py` #"(Spec Decision" included. `tests/types/test_relay_interfaces.py`'s `spec-015` site is out of family and stays byte-identical.
- [x] **Zero new `spec-028 #"substring"` citations** introduced anywhere (baseline 0, postcondition 0, measured single-line AND whitespace-flattened). **Tick confirmed by Worker 1 at final verification (0 / 0); the re-pass re-verifies it as a standing postcondition, since C10-C12 write new citations.**
- [x] **No executable statement changed** in any of the eight files — the whole diff is comment and docstring text.
- [x] Nothing edited outside the eight writable `.py` paths; no `.md` touched but this artifact; no `027` hunk reverted in the three baseline-dirty files.
- [x] `uv run ruff format` and `uv run ruff check --fix` run **scoped to the files this pass touched**, never `.`; `git status --short` clean of collateral churn.
- [x] `scripts/check_citations.py` exits 0 with a count at or above the 743 baseline, and `scripts/check_trailing_commas.py --check` exits 0 for the eight files.

### Notes for Worker 1 (spec reconciliation)

Written on disk, not only into a return report, per [`BUILD.md`][build] `### Cohorting, naming, and closure`. Items 1-5 are for **Slice 3**; items 6-8 are for the maintainer or the integration pass.

1. **Decision 3's quoted `"__all__"` helper expression is stale at HEAD, and Worker 0's verification table read only half of it.** The spec's Decision 3 states the helper is `[f.name for f in model._meta.get_fields() if hasattr(f, "column") and not getattr(f, "many_to_many", False)]`. At HEAD `orders/inputs.py::_get_concrete_field_names_for_order` is `... if getattr(f, "column", None) is not None and not getattr(f, "many_to_many", False)`. Worker 0's table confirmed *"the deliberate `and not getattr(f, "many_to_many", False)` clause Decision 3 pins is there"* — true, and the **first** half diverged. The code's own docstring gives the reason (Django's virtual `GenericRelation` / `GenericForeignKey` descriptors also expose `column = None`, so `hasattr` alone lets them through), which is a *stronger* guarantee than the spec claims. **Slice 3 should state the shipped expression.** This is a new finding, not part of D3-D16.

2. **Decision 5's `Ordering.resolve` code example diverges from HEAD in two ways.** The example uses `if "ASC" in self.name` (substring); HEAD routes through the new `Ordering.is_ascending` property, `self.name.startswith("ASC")` (prefix), whose own docstring says the prefix test *"keeps the rule precise if future members embed `ASC` elsewhere in the name."* And `is_ascending` is a second consumer — `OrderSet._resolve_order_expressions` uses it to pick `Min` vs `Max` for to-many terms. The spec names neither. **New finding, not part of D3-D16.**

3. **Two spec claims Slice 2 now depends on, which Slice 3 must not weaken.** C2's replacements cite `spec-028 Decision 3` (the `"__all__"` scope paragraph) and `spec-028 Edge cases` (the `Meta.fields = ["shelf__code"]` bullet). Both are bare-heading forms, so they survive any rewording *inside* those sections — but not the removal or renaming of the `### Decision 3` heading or the `## Edge cases and constraints` heading. Same standing obligation Slice 1 discharged for the 37 `spec-028 Decision N` and 5 `spec-028 test plan` references.

4. **C8's repair adds a 38th `spec-028 Decision N` reference.** Slice 1's postcondition sweep recorded 37 in both directions. **CORRECTED by Worker 1 at final verification — the `66` / `38` / `5` this note originally carried was wrong in two of three digits and must not be used.** After Slice 2 the durable-form census is `spec-028` **67**, `spec-028 Decision N` **38**, `spec-028 test plan` **6**. Slice 3 and the integration pass re-derive against **67 / 38 / 6**. Four independent measurements agree (Worker 2, Worker 3, Worker 0, and this pass); the cause is that this plan's own replacement text adds tokens the `−2` prediction did not net out — C2 step 4's `spec-028 Edge cases` adds one `spec-028`, and C5's banner adds one `spec-028 test plan`. **The C12 re-pass moves all three again**, so the number to re-derive against is the one measured after the re-pass closes, not this one.

5. **C5's banner and the spec's `14` census now disagree by construction, and that is correct.** The banner will read 16 functions / 19 rows; the spec still asserts 14 at what Slice 1 measured as a **13-site** census (rewriting the `Status:` line removed one site). The two numbers describe different populations: the spec's 14 is the *planned* contract, the banner's 16 is the *shipped* section. **Slice 3 owns reconciling the spec's side** (D12), and should state the shipped count with its subject rather than moving 14 to 16 silently — the two post-ship additions came from `spec-030-connection_field-0_0_9` P1-B, not from this card. This is the "a count can be right in every digit and wrong in its SUBJECT" hazard, and it is why the banner names its subject.

6. **MAINTAINER DECISION — `tests/test_registry.py` will carry two of four twins repaired.** All four `test_clear_tolerates_unimportable_*` tests share the false `except ImportError` premise. The filter twin was repaired mid-cycle by a concurrent session; this slice repairs the order twin; the **connection** twin (`spec-030-connection_field-0_0_9` P3b) and the **relay** twin (`spec-032` Decision 8) are left because their contracts belong to other cards. A reader of that file will find two current stories and two stale ones. **Either those two cards' residual cycles pick them up, or the maintainer authorizes a one-off sweep.** Flagged here rather than fixed, because a worker repairing them would be writing claims about two specs this cycle never verified.

7. **MAINTAINER / FUTURE-CYCLE — raw line-number citations are a tree-wide population, not a `spec-028` one.**

   **CORRECTED by Worker 1 at final verification.** As originally written this note described the `tests/orders/` sites under the wrong finding class, with the wrong instrument, attributed to the wrong specs, and omitted `tests/orders/test_base.py` entirely. `tests/orders/` carries **two disjoint populations, 23 occurrences in total**, and they are now C10 and C11 of this slice rather than a deferral:

   - **prose `line NN`: 11 occurrences** — `test_sets.py` 7, `test_factories.py` 3, `test_composition.py` 1. Only **two** cite the upstream cookbook (`test_factories.py` #"cookbook lines 124-130", `test_sets.py` #"per cookbook line 280"); one cites a standing doc (`test_composition.py` #"``AGENTS.md`` line 8 carve-out"); the other eight cite this card's own modules.
   - **raw `path:NN`: 12 occurrences** — `test_sets.py` 10, `test_factories.py` 1, `test_base.py` 1. None cites `spec-035` / `spec-036` / `spec-038`; every one cites `django_strawberry_framework/orders/{sets,factories,base}.py`.
   - **9 coordinates point past their target file's EOF**: `orders/sets.py` is 496 lines and is cited at `526`, `532`, `535`, `571`, `579` (prose) and `534-535`, `570-571`, `578-579` (path form); `orders/factories.py` is 155 lines and is cited at `line 159`.

   The residual tree-wide population, genuinely out of this cycle's scope, is the one below. Further rule-27 violations sit in `optimizer/walker.py`, `mutations/{resolvers,fields,sets}.py`, `tests/optimizer/{test_extension,test_walker}.py`, `tests/mutations/test_sets.py`, and `examples/fakeshop/test_query/test_products_api.py`, citing `spec-035` / `spec-036` / `spec-038` and the upstream cookbook. (`orders/sets.py` and `tests/orders/{test_sets,test_factories}.py` are struck from this residual list — they are in the writable set and are C10 / C11 / C12 work.) **`scripts/check_citations.py` cannot see any of them** — it resolves `path::Symbol` only. A cheap gate extension (flag `\blines? \d+` and `[\w./]+\.py:\d+` in first-party `.py`) would close the class permanently and would have caught every C2 and C7 site in this slice. Worth a card.

8. **A banner count is unmaintained by construction.** C5 replaces one rotted number with a fresher one and names its derivation, which is the best available under the instruction to keep a number — but nothing stops it rotting again the next time a test lands in that section. If the maintainer prefers, the durable alternative is to drop the count and let the banner name only the contract; recorded so the choice is visible rather than defaulted into.

---

## Build report (Worker 2)

All eighteen implementation steps landed. **Not one executable statement changed** — proved mechanically below, not asserted. The one plan-level deviation is an arithmetic slip in the plan's own predicted census deltas, recorded under `### Notes for Worker 1 (spec reconciliation)`.

### Files touched

Grounded in `git status --short` (run after both scoped `ruff` invocations). Exactly the eight source paths plus this artifact and my memory file; nothing else.

- `django_strawberry_framework/types/base.py` — C1 step 1: deleted the `(spec-028 N3)` parenthetical from `::_validate_set_sidecar`'s docstring and reflowed the sentence. No replacement citation, per the plan's first-preference form.
- `django_strawberry_framework/orders/base.py` — C4 step 13: module docstring line 3, `Layer 2` -> `Layer 1`. One word; nothing else in the docstring changed.
- `django_strawberry_framework/orders/inputs.py` — C2 steps 3 and 4: `::_get_concrete_field_names_for_order` drops ` line 452` (keeps `spec-028 Decision 3`) and reflows; `::_build_input_fields` replaces `Spec Edge cases line 980` with `spec-028 Edge cases`.
- `tests/types/test_base.py` — C1 step 2: deleted the `(spec-028 N3)` parenthetical from `::test_filterset_and_orderset_meta_validators_ride_validate_set_sidecar` and reflowed. **Baseline-dirty from 027; the edit is additive and no 027 hunk was touched.**
- `tests/orders/test_inputs.py` — C2 step 5 (`::test_ordering_enum_has_six_members` drops ` lines 525-532`) plus the whole C7 class: all seven docstrings in the `# inputs.py edge-case branches` block rewritten to `path::Symbol` form, both cross-test line ranges deleted, and the C7c mechanism sentence restated. Two body comments in the same two tests corrected as well (see `### Implementation notes`).
- `tests/test_registry.py` — C6 step 16: `::test_clear_tolerates_unimportable_order_submodules`'s docstring and its inline comment, both mirroring the concurrently-repaired filter twin. **Baseline-dirty from 027; the filter twin's 027 hunks survive verbatim alongside the new order-twin hunks (`git diff HEAD -- tests/test_registry.py` confirms both).**
- `examples/fakeshop/apps/library/orders.py` — C3 steps 9, 10, 11 (three docstrings retargeted to `test_library_api.py::<name>`, including the 4 -> 2 correction) and C8 step 18 (`(spec-028 + Decision 11)` -> `(spec-028 Decision 3 Layer 2)`).
- `examples/fakeshop/test_query/test_library_api.py` — C2 step 6 (the wrapped `line 1038` / `1039` paragraph deleted, invariant kept), C3 step 12 (`::test_library_branches_order_by_name_asc`'s `Test 1` / `Test 9` self-reference retargeted), C5 step 15 (the banner). **Baseline-dirty from 027; edits are additive to the named lines.**
- `docs/builder/bld-slice-2-028-citation_and_provenance_rot.md` — this report plus sixteen checklist ticks.
- `docs/builder/worker-memory/worker-2-028.md` — one appended entry.

Every other path in `git status --short` is the 027 cycle's baseline-dirty work or this cycle's Slice 1 output (`docs/SPECS/spec-028-orders-0_0_8.md` modified, `docs/SPECS/appx/spec-028-orders-0_0_8-rationale.md` untracked). **No collateral churn: both `ruff` invocations were scoped to the eight files and both reported no rewrite.** `django_strawberry_framework/orders/factories.py` is absent from the list, as the do-not-touch instruction requires.

### Tests added or updated

**None.** No test was added, removed, renamed, or re-asserted; no assertion changed. Two test *docstrings* and three test *body comments* were corrected as documentation (C6, C7, C7c) — the assertions under them are untouched. Verified mechanically in `### Validation run`.

### Validation run

**Two readings taken BEFORE any edit**, so every delta below is a difference rather than a guess:

- `uv run python scripts/check_citations.py` -> `OK: 743 citations resolve (666 in 422 .py files, 77 in KANBAN.md)`, exit 0.
- census: `spec-028` **68**, `spec-028 Decision [0-9]+` **37**, `spec-028 test plan` **5**, `spec-028[^)]*#"` **0**.
- the flattened probe, before: `types/base.py [review-item-id] 1`; `orders/inputs.py [raw-line-citation] 2` (`line 452`, `line 980`); `tests/types/test_base.py [review-item-id] 1`; `tests/orders/test_inputs.py [raw-line-citation] 3` + `[path-NN-citation] 8`; `examples/.../library/orders.py [Test-N-ordinal] 8`; `test_library_api.py [raw-line-citation] 2` + `[Test-N-ordinal] 2`. **28 occurrences over the four classes** — matching the plan's re-measured census exactly, including the wrapped `line 1038` / `1039` pair that only the flattened form can see.

Per-finding postconditions, each with the command as the plan's table specifies it:

| Finding | Command | Result |
|---|---|---|
| C1 | `grep -roh --include='*.py' '(spec-028 N3)' django_strawberry_framework/ tests/ examples/ \| wc -l` | **0** (was 2) |
| C1 census | `grep -rohE --include='*.py' 'spec-028' …` | **67** — the plan predicted 66; see the deviation note below. The digit is measured, not the plan's |
| C2 + C7 + C3 | the flattened probe over all four classes | **CLEAN** — every class prints nothing (was 28 occurrences) |
| C3 | `grep -rn --include='*.py' '{ shelf: {' examples/ tests/` | the only two live *order* sites are `test_library_api.py:1862` (inside `::test_library_books_order_by_forward_fk_relation`, which opens at 1845) and `:2378` (inside `::test_library_books_order_by_multi_field_priority`, opens at 2359). The three `filter: {{ shelf: {{` hits at 1059 / 1551 / 1565 / 1582 are filter-input sites, not order-input ones, and 2362 is the multi-field test's own docstring. **The 4 -> 2 correction is confirmed by measurement, and the two names written are those two** |
| C3 | `find … -name 'test_library_api.py' \| wc -l` | **1** — the bare basename form is unambiguous, as the plan verified |
| C4 | `grep -rn --include='*.py' -E 'Layer [0-9] of the spec-028' django_strawberry_framework/` | `orders/base.py:3: Layer 1 …`; `orders/factories.py:3: Layer 5 …` |
| C4 | `git diff HEAD --stat -- django_strawberry_framework/orders/factories.py` | **empty** — the do-not-touch file is unmodified |
| C5 | re-derived bounds `grep -n 'Live HTTP order coverage' …` -> 1738 and `grep -n '^# spec-029' …` -> 2483; `awk 'NR>=1738 && NR<=2483 && /^def test_/' … \| wc -l` -> **16**; `awk … /parametrize/` -> **one**, at 1813, over **four** NULLS directions on `::test_library_books_order_by_subtitle_null_positioning` | 16 functions / 19 rows, independently re-derived before writing the number. The 16 names are listed in full in my memory entry; the two the spec names nowhere are `::test_library_branches_order_by_scalar_then_to_many_aggregate_no_multiplication` and `::test_library_genres_connection_pages_by_to_many_aggregate`, both named in the new banner |
| C6 | `grep -c 'except ImportError' django_strawberry_framework/registry.py` | **0** — the premise the old docstring asserted does not exist at HEAD, confirming the repair rather than a reword |
| C6 | `grep -n 'register_subsystem_clear' orders/inputs.py orders/__init__.py` | both registrations present; `orders/__init__.py:48` registers `_clear_helper_referenced_ordersets` (owner `orders.helper_references`) and `orders/inputs.py:383` registers the input-namespace clear. **Both symbols the new docstring names were verified before it was written** |
| C8 | `grep -rn --include='*.py' 'spec-028 + Decision' examples/` | **0**; `spec-028 Decision [0-9]+` census **38** (was 37), exactly the +1 the plan predicts |
| all | `uv run python scripts/check_citations.py` | `OK: 758 citations resolve (681 in 422 .py files, 77 in KANBAN.md)`, exit **0**. **The count ROSE by 15** — every replacement is now gate-enforced. A fall would have meant a broken ref |
| all | single-line `grep -rohE 'spec-028[^)]*#"' …` and the whitespace-flattened equivalent | **0** and **0** (baseline 0 both ways) |
| all | wrapped-citation probe: every `path::Symbol` found whitespace-flattened, differenced against those found single-line, across the eight files | **0 wrapped** — no citation this pass wrote crosses a line boundary, and the longest new line is 106 columns (the pre-existing `tests/filters/test_inputs.py::test_clear_filter_input_namespace_tolerates_unimportable_submodules` reference), inside the 110-column E501 grace |
| all | `uv run python scripts/check_trailing_commas.py --check <the eight>` | exit **0** (ASCII-only `.py` + layout gate) |
| all | `uv run ruff format <the eight>` | exit 0, `8 files left unchanged` |
| all | `uv run ruff check --fix <the eight>` | exit 0, `All checks passed!` |
| all | `git status --short` after both `ruff` runs | no path outside `### Files touched` changed; see the classification above |
| all | `git diff HEAD -- <path>` for each of the three baseline-dirty files | `tests/types/test_base.py` 4+/4-, `tests/test_registry.py` 28+/18-, `test_library_api.py` 27+/29-. **Every 027 hunk survives**: the diff for `tests/test_registry.py` shows the concurrent session's filter-twin rewrite intact directly above my new order-twin hunks |

**Both `ruff` invocations were scoped to the eight files, never `.`** — a repo-wide write-mode run would have reformatted the concurrent session's in-flight code, which is not mine to revert.

**Proof that no executable statement changed** — the load-bearing claim of this slice, so it is measured rather than asserted. For each of the eight files I fetched the pristine HEAD copy read-only (`git show HEAD:<path>` into a scratch path **outside** the repo — no `git checkout`, `restore`, `stash`, or `worktree` anywhere in this pass), parsed both versions with `ast`, removed every module / class / function docstring node, and compared `ast.dump` of the two trees:

```
SAME  django_strawberry_framework/types/base.py
SAME  django_strawberry_framework/orders/base.py
SAME  django_strawberry_framework/orders/inputs.py
SAME  tests/types/test_base.py
SAME  tests/orders/test_inputs.py
SAME  tests/test_registry.py
SAME  examples/fakeshop/apps/library/orders.py
SAME  examples/fakeshop/test_query/test_library_api.py
```

Eight of eight identical. Because the comparison is against **HEAD** rather than a pre-edit snapshot, it proves the stronger statement: neither this slice nor the 027 cycle's concurrent hunks in the three dirty files changed an executable statement in any of the eight.

**Collection check** (a mangled triple-quote is the one way a prose-only edit breaks something, so this is confirmed two ways):

- `uv run python -m compileall -q <the eight>` — exit **0**.
- `uv run pytest tests/orders/test_inputs.py tests/test_registry.py tests/types/test_base.py examples/fakeshop/test_query/test_library_api.py --no-cov --collect-only -q` — **479 tests collected**, no collection errors.

**No `pytest` run as routine slice work, and no `--cov*` flag in any command in this pass.** The one `pytest` invocation above is `--collect-only --no-cov`; it asserts nothing and executes no test body.

### Failability proofs

`None; this pass introduced no new boundary.`

The plan answered the split question in writing and recorded zero new boundaries; the mechanical proof of that is the AST comparison above — a pass that changes no executable statement cannot add a guard, gate, or rejection path. No mutation was made to any file in this pass, so no `ACTIVE-MUTATION.json` and no scratch mutation copy exists to clean up.

### Hot-path budget

`Not applicable; plan declares no hot path.`

### Floor verification

`Not applicable; plan declares floor-verification scope none.`

No floor venv was built and the shared `.venv` was not mutated.

### Implementation notes

Wording, reflow, and ordering were the plan's declared discretion; which Decision / Layer / symbol each citation names, and the 4 -> 2 correction, were taken from the plan unchanged.

- **`Covers` everywhere in C7, and all seven agree.** `Closes` no longer parses once the coordinate is a symbol rather than a line ("closes line N" was the original sense), and the plan licensed either verb provided they are consistent.
- **The C6 order twin REUSES the filter twin's sentence rather than paraphrasing it.** Its summary line is now byte-identical to the filter twin's, with the body substituted for the order specifics and `spec-027 Decision 9` -> `spec-028 Decision 9`. The plan named reuse-with-substitution the safer default because the two must read as one story; a paraphrase would have produced two tellings of one mechanism. The `Order twin of …` cross-reference that opens the body is retained from the original.
- **The C6 order twin's docstring names the two registered callbacks by symbol** (`clear_order_input_namespace`, `_clear_helper_referenced_ordersets`) rather than describing "the order-namespace co-clear" abstractly. Both were verified present at their `register_subsystem_clear` call sites first; naming them is what makes the claim checkable instead of merely true.
- **Three body comments were corrected alongside their docstrings, because leaving one right and the other wrong is the half-fix the plan names for C6.** All three sit in tests whose docstrings this slice was already repairing, all three asserted the same retired mechanism, and none changes an executable statement:
  1. `tests/orders/test_inputs.py::test_normalize_input_value_skips_attrs_with_no_field_spec_entry` — the body comment said `` `if spec is None: continue` `` where the guard reads `if field.spec is None:`. Same reword the C7 table records for that docstring.
  2. `tests/orders/test_inputs.py::test_clear_order_input_namespace_tolerates_unimportable_submodules` — the body comment said "exercising both `except ImportError` guards", the exact false premise C7c retires from the docstring above it.
  3. `tests/test_registry.py::test_clear_tolerates_unimportable_order_submodules` — the inline comment the plan's step 16 explicitly names, rewritten to mirror the filter twin's rewritten comment.
- **C1 took the no-citation form at both sites, not a `spec-028 Decision 7` pointer.** The plan's reasoning held on inspection: `types/base.py::_validate_set_sidecar` serves both the filter and the order subsystem, so a lone `spec-028` pointer on it would be asymmetric as well as unresolvable, and its sibling `::_validate_filterset_class` states the same cycle invariant 20 lines below with no citation at all. On the test side, the body already asserts the invariant by source inspection (`assert "from ..orders.sets import OrderSet" in src_order`), so an external pointer adds nothing a reader can act on.
- **C2 step 6 is the only deletion in the slice, and the deletion is what the evidence supports.** I re-read the spec's Test-plan bullet for `::test_root_get_queryset_runs_before_order_apply` before deleting: it now reads `{ allLibraryBranches(orderBy: [{ city: DESC }]) { id name city } }` and explains the `city`-not-`name` choice itself, so the docstring's claim that "Spec line 1038 names `name: DESC`" is **false against the current spec**, not merely un-navigable. The surviving paragraph states the invariant (why `city`, why staff cannot substitute) with no coordinate at all.
- **The C5 banner names its subject and its derivation.** `16 test functions / 19 test rows` plus the sentence attributing the three extra rows to the one parametrized test, and a first line attributing the two post-ship additions to `spec-030-connection_field-0_0_9` P1-B. A bare `16` would have been the same defect as the `14` it replaces one card later — right in every digit, wrong in its subject. The multi-line-inside-the-rules shape follows this file's own `spec-029` banner convention.
- **Edits were grouped by file** (the plan's declared economy), which kept each scoped `ruff` invocation to the file just touched and made the per-file `git diff HEAD` reading cheap.

### Notes for Worker 3

- **Nothing to re-run for a boundary.** Zero new boundaries, so there is no proof record to audit and no mutation to check for. The one thing worth independently re-deriving is the AST-identity claim above; the script is eight lines and the command shape is in `### Validation run`.
- **C6b is yours and is still `- [ ]`.** I did not tick it and did not pre-empt the judgement. Two things to carry in: `TypeRegistry.clear`'s entire subsystem step is `for clear in iter_subsystem_clears(): clear()` (verified, `grep -c 'except ImportError' django_strawberry_framework/registry.py` -> 0), and the replayed order callback's own lookups target `orders.factories` / `orders.sets` — **not** the `orders.inputs` / `orders` modules the test poisons. So the plan's reading (that the test pins the *negative* invariant "`clear()` performs no direct import of the order submodules") is the one the mechanism supports, and the new docstring is written to state exactly that rather than to claim a guard.
- **If you take the mutation route for C6b, `django_strawberry_framework/registry.py` is outside this slice's writable set** — record it in the artifact before mutating, revert inside the same pass, and prove the revert by `cmp` against a copy taken to a path **outside** the repo. Never `git checkout`: this tree carries the 027 cycle's uncommitted work and a concurrent session's writes.
- **Read the three baseline-dirty files with `git diff HEAD -- <path>`, never `git diff -- <path>`.** A concurrent `git add` makes the plain form read clean; I used the `HEAD` form throughout and the readings are in the table above.
- **No shadow file was used and `scripts/review_inspect.py` was not re-run.** The plan recorded the skip with its reason (no logic added anywhere, so neither the Worker 2 nor the Worker 3 trigger fires); nothing in implementation changed that.
- **The two untouched `except ImportError` twins are deliberate**, per the plan's `### Deliberately NOT touched`. `git diff HEAD -- tests/test_registry.py` shows hunks at the filter twin (027's, not mine) and the order twin (mine) only — the connection twin at ~1691 and the relay twin at ~1725 are absent from the diff, which is the check.

### Notes for Worker 1 (spec reconciliation)

Written on disk, not only in my return report.

1. **DEVIATION — the plan's predicted census deltas are off by one in two places, and its own replacement text is why.** The measured postcondition is `spec-028` **67** (plan predicted 66) and `spec-028 test plan` **6** (plan predicted 5, unchanged). Neither is a wording deviation: I wrote the plan's text verbatim in both places, and the plan's arithmetic did not count the tokens that text adds.
   - C2 step 4 replaces `Spec Edge cases line 980` with `spec-028 Edge cases`, which **adds** a `spec-028` occurrence the `−2` prediction did not net out. So 68 − 2 (C1) + 1 (C2 step 4) = **67**.
   - C5 step 15 replaces the banner's `spec-028 - 14 acceptance tests` with `spec-028 test plan`, which is `spec-028`-neutral but **adds** a durable-form `spec-028 test plan` occurrence. So 5 + 1 = **6**.
   - `spec-028 Decision N` is **38** exactly as predicted (C8's +1).
   - **This matters because the artifact's own note 4 instructs Slice 3 and the integration pass to re-derive against `66` / `38` / `5`.** The correct post-Slice-2 baseline is **`spec-028` 67, `spec-028 Decision N` 38, `spec-028 test plan` 6.** Recommended replacement for note 4's closing sentence: *"After Slice 2 the durable-form census is `spec-028` **67**, `spec-028 Decision N` **38**, `spec-028 test plan` **6**. Slice 3 and the integration pass re-derive against these numbers."* Worth noting that this is the same class as the hazard the plan itself names — a count asserted in the same breath as the change that moves it.
2. **Two more spec headings are now load-bearing for `.py` citations, on top of the three the plan's note 3 lists.** C2 step 4 cites `spec-028 Edge cases`, resolving to the `## Edge cases and constraints` heading, and C6's repaired docstring cites `spec-028 Decision 9`, resolving to `### Decision 9 — Input-class namespace vs TypeRegistry and lifecycle`. Both are bare-heading forms, so they survive any rewording *inside* those sections but not the removal or renaming of either heading. Same standing obligation as the 37-plus-5 cohort.
3. **A `.py` docstring claim that is false at HEAD, in a file this slice owns, that is NOT in any finding class.** `examples/fakeshop/apps/library/orders.py`'s module docstring opens *"Five ordersets mirror the relation shape `apps.library.schema` exposes"*. Seven ship in that module (`grep -c '^class .*Order(OrderSet)'` -> 7: the five named plus `PeriodicalOrder` and `IssueOrder`), which is D15 of the build plan appearing on the **code** side rather than the spec side. **I did not touch it** — it is outside the eight findings this slice was dispatched with, and inventing a ninth mid-build is exactly the scope creep the artifact fences. Recommended: carry it into Slice 3's D15 work as a code-side sibling, or dispatch it as a one-line C9 to a re-pass. The sentence to correct is `Five ordersets mirror the relation shape`; the shipped count is **seven**, the two extra being the keyset-cursor substrate pair whose own docstring already says so.
4. **The C5 banner and the spec's `14` still disagree by construction, as the plan intends.** The banner now reads `16 test functions / 19 test rows` and names its subject; the spec's side is Slice 3's (D12). Recording the re-derivation here so Slice 3 need not re-measure: section bounds are the `Live HTTP order coverage` banner through the `# spec-029` banner, **16** `^def test_`, exactly **one** `parametrize` (at the pre-edit line 1813) over **four** NULLS directions, hence 16 − 1 + 4 = **19** rows.
5. **Everything the plan escalated in its own notes 6, 7 and 8 stands unchanged by this pass** — the two-of-four `except ImportError` twins in `tests/test_registry.py` (I repaired only the order twin; the connection and relay twins are absent from my diff), the tree-wide raw-line-number population outside the eight files, and the standing rot risk of any banner count. None needs re-derivation from me; all three were measured at plan time and this slice changed nothing about them.


---

## Review (Worker 3)

### C6b diagnostic mutation — recorded BEFORE it is made

Per [`worker-3.md`][worker-3] `## Scope` and [`BUILD.md`][build] `### Who performs it`, the narrow
source carve-out is recorded here **before** the mutation is applied. This is the plan's step 17
diagnostic, not an owed failability proof (the slice introduces zero boundaries).

- **Target (outside this slice's writable set):** `django_strawberry_framework/registry.py::TypeRegistry.clear`.
- **Anchor check, first, before any copy:** `grep -c 'for clear in iter_subsystem_clears():' django_strawberry_framework/registry.py` -> **1** (exactly one; nothing else in the loop can tell that its own reference is already mutated). `git diff HEAD --stat -- django_strawberry_framework/registry.py` -> **empty**, so the file is at HEAD and carries no live mutation from a prior pass. `md5 -q` before: `dd191a70f982cbefaab9f62d16c884a6`.
- **Pristine copy taken to a path OUTSIDE the repository:** `/private/tmp/claude-501/.../scratchpad/dsf-proof-registry-clear.orig`. Never `git checkout` / `restore` / `stash` / `worktree` — this tree carries the 027 cycle's uncommitted work.
- **Mutation to be applied:** re-introduce the retired direct import inside `clear()`, immediately
  above the `for clear in iter_subsystem_clears():` replay:
  `from .orders.inputs import clear_order_input_namespace as _reintroduced` followed by
  `_reintroduced()`. This removes the property under test (that `clear()` performs **no** direct
  import of an order submodule) rather than merely perturbing code near it.
- **Scope as run:** `uv run pytest tests/test_registry.py --no-cov`.
- **Revert:** restore from the scratch copy and prove by `cmp` (exit 0) plus the `md5` above.

Result recorded under `#### C6b — does the order twin still pin anything?` below.

### Working-tree event this review must record first: HEAD moved mid-pass and swallowed three of the eight files

At review start `git status --short` matched the plan's baseline-dirty list. At **09:45**, mid-review, the
maintainer committed the `027` residual cycle as `8a9840dc` *"docs(specs): complete the spec-027 record and
reconcile its Decision 9 claims"* — and that commit's `--name-status` includes
`tests/types/test_base.py`, `tests/test_registry.py`, and
`examples/fakeshop/test_query/test_library_api.py`, i.e. **the three baseline-dirty files this slice was
authorized to edit additively**. Slice 2's hunks in those three are now in HEAD, inside a commit whose
message describes only `027` work.

- **Nothing was reverted and nothing was lost.** Verified against HEAD, not against the working tree:
  `git show HEAD:tests/test_registry.py | grep -n 'so the poisoning can only reach a replayed callback'` ->
  lines **1639** (filter twin, `027`'s) and **1681** (order twin, this slice's) both present;
  `git show HEAD:examples/.../test_library_api.py | grep -c '16 test functions / 19 test rows'` -> **1**;
  `... | grep -c 'That gate is what'` -> **1**; `... | grep -c 'Spec line 1038'` -> **0** (the C2 step-6
  deletion landed); `git show HEAD:tests/types/test_base.py | grep -n 'The wrappers keep the cycle-safe local imports;'`
  -> **760**. The `027` hunks survive too (`grep -c 'Spec-027:'` -> 9, `'Spec-021:'` -> 0).
- **Consequence for every later pass: `git diff HEAD -- <path>` is now EMPTY for those three files.** A
  final-verification, integration, or final-gate pass that reads `git diff HEAD` to confirm Slice 2's work
  will see nothing for three of the eight paths and could read it as "reverted" or "never landed". The
  reproduction commands are `git show 8a9840dc -- <path>` (which carries **both** cohorts' hunks — 48
  changed lines in `tests/test_registry.py`, of which 2 added lines carry the order-twin / `spec-028`
  text) or `git diff 5c6fdd71 -- <path>` against the pre-commit HEAD.
- Worker 2's `### Validation run` per-file readings (`4+/4-`, `28+/18-`, `27+/29-`) were accurate when
  taken and are **no longer reproducible against HEAD**. They are not wrong; their reference moved.
- **No worker action.** [`AGENTS.md`][agents] #"Files dirty at task start" and [`BUILD.md`][build]
  `## Slice handoff` (workers never amend, force-push, or rewrite history) both apply. Recorded for the
  maintainer under `### Notes for Worker 1` item 3; not reverted, not re-staged, not amended.

### Independent re-derivations (Worker 2's numbers re-measured, not read)

Every reading below was taken by this pass. `git show HEAD:<path>` into
`/private/tmp/claude-501/.../scratchpad/head/` — outside the repository. No `git stash`, `checkout`,
`restore`, or `worktree` anywhere in this pass.

**1. The zero-executable-change claim — confirmed on TWO independent instruments, 8/8.** Worker 2 recorded
one (docstring-stripped `ast.dump`). I re-derived it and added a second so the result does not rest on one
normalization:

- *AST:* parse both versions, delete the leading `Expr(Constant(str))` of every `Module` / `ClassDef` /
  `FunctionDef` / `AsyncFunctionDef`, compare `ast.dump` (no `include_attributes`, so reflow is invisible).
- *Tokens:* `tokenize.generate_tokens` on both, drop `COMMENT` / `NL` / `NEWLINE` / `INDENT` / `DEDENT`,
  collapse only **statement-position** `STRING` tokens to a placeholder, and keep every other string token
  **verbatim** — so a changed non-docstring literal would surface as `DIFFERENT`.

```
SAME      ast   SAME      tokens   django_strawberry_framework/types/base.py
SAME      ast   SAME      tokens   django_strawberry_framework/orders/base.py
SAME      ast   SAME      tokens   django_strawberry_framework/orders/inputs.py
SAME      ast   SAME      tokens   tests/types/test_base.py
SAME      ast   SAME      tokens   tests/orders/test_inputs.py
SAME      ast   SAME      tokens   tests/test_registry.py
SAME      ast   SAME      tokens   examples/fakeshop/apps/library/orders.py
SAME      ast   SAME      tokens   examples/fakeshop/test_query/test_library_api.py
OK: 8/8 identical on both instruments
```

The HEAD references were fetched at 09:42, **before** `8a9840dc`, so this compares the current tree against
the genuinely pre-Slice-2 baseline — the stronger comparison, and the reason the mid-pass commit did not
invalidate it.

**2. Boundary count zero — verified, not accepted.** Worker 1 declared it and Worker 2 relied on it; the
whole slice rests on it. It is now proved rather than asserted: a pass whose executable token stream is
byte-identical to HEAD in all eight files **cannot** have introduced or weakened a guard, gate, cap,
rejection path, or validation branch. So no failability proof is owed, `### Failability proofs` reading
`None; this pass introduced no new boundary.` is correct, and the mandatory re-run floor
([`worker-3.md`][worker-3] "Reading is necessary, not sufficient") is satisfied by an **empty** set,
which is legal only in exactly this case. The one mutation this pass ran is the C6b **diagnostic** below,
not a proof re-run.

**3. The plan-arithmetic deviation — Worker 2 is right and the plan is wrong.** Re-measured repo-wide over
`django_strawberry_framework/` + `tests/` + `examples/`:

| Census | Plan predicted | Worker 2 measured | This pass measured |
|---|---|---|---|
| `spec-028` | 66 | 67 | **67** |
| `spec-028 Decision [0-9]+` | 38 | 38 | **38** |
| `spec-028 test plan` (case-sensitive) | 5 | 6 | **6** |

And the delta is attributable, not merely equal. Differencing the eight files' own counts against the
pre-`8a9840dc` HEAD copies: `spec-028` **27 -> 26** (-1), `spec-028 Decision N` **13 -> 14** (+1),
`spec-028 test plan` **4 -> 5** (+1). So the repo baseline was 68 / 37 / 5 and Worker 2's account of the
cause is exact: C1 removes 2 `spec-028` tokens, C2 step 4 adds 1 back
(`Spec Edge cases line 980` -> `spec-028 Edge cases`), netting **-1** rather than the plan's **-2**; C5 adds
one durable `spec-028 test plan`; C8 adds one `spec-028 Decision N`. **The post-Slice-2 baseline for Slice 3
and the integration pass is `spec-028` 67 / `spec-028 Decision N` 38 / `spec-028 test plan` 6** — note 4's
`66 / 38 / 5` must not be used.

**4. Every postcondition in `### Verification this slice owes`, re-run at the recorded scope.**

| Postcondition | Command re-run | Result |
|---|---|---|
| C1 — 0 review-item ids | `grep -roh --include='*.py' '(spec-028 N3)' django_strawberry_framework/ tests/ examples/ \| wc -l` | **0** |
| C2 + C3 + C7 — whitespace-flattened four-class probe over the eight | the probe fenced under `### Census correction`, verbatim | **prints nothing** |
| C3 — the nested `shelf:` order surface has exactly two live users | `grep -rn --include='*.py' '{ shelf: {' examples/ tests/` | 7 hits; the four `filter: {{ shelf: {{` sites (1059/1551/1565/1582) are filter-input, 2360 is a docstring; the only **order** sites are **1866** (inside `::test_library_books_order_by_forward_fk_relation`, opens 1845) and **2376** (inside `::test_library_books_order_by_multi_field_priority`, opens 2359). **4 -> 2 confirmed, and those are the two names written** |
| C3 — bare basename is unambiguous | `find django_strawberry_framework tests examples scripts -name 'test_library_api.py' \| wc -l` | **1** |
| C4 — Layer 1 here, Layer 5 there, `factories.py` untouched | `grep -rnE 'Layer [0-9] of the spec-028' django_strawberry_framework/`; `git diff HEAD --stat -- .../orders/factories.py` | `orders/base.py:3: Layer 1`, `orders/factories.py:3: Layer 5`; factories stat **empty** |
| C5 — 16 functions / 19 rows | bounds re-derived (`Live HTTP order coverage` -> **1738**, `^# spec-029` -> **2481**); `awk 'NR>=1738 && NR<2481 && /^def test_/'` -> **16**; one `parametrize` at 1817 over four NULLS directions | **16**, and rows confirmed by real collection rather than arithmetic: `pytest examples/fakeshop/test_query/test_library_api.py --collect-only -n 0`, summing `<Function …>` nodes for those 16 names -> **19**, with `…null_positioning[ASC_NULLS_FIRST…]`/`[ASC_NULLS_LAST…]`/`[DESC_NULLS_FIRST…]`/`[DESC_NULLS_LAST…]` the four |
| C6 — no `except ImportError` in `registry.py` | `grep -n 'except ImportError' django_strawberry_framework/registry.py` | no output. `TypeRegistry.clear`'s whole subsystem step is `for clear in iter_subsystem_clears(): clear()` |
| C8 — malformed form gone | `grep -rn --include='*.py' 'spec-028 + Decision' django_strawberry_framework/ tests/ examples/ \| wc -l` | **0** |
| citation gate green and count risen | `uv run python scripts/check_citations.py` | `OK: 758 citations resolve (681 in 422 .py files, 77 in KANBAN.md).` exit **0** — 758 >= the 743 baseline |
| 0 new `spec-028 #"substring"` citations, single-line AND flattened | `grep -rohE --include='*.py' 'spec-028[^)]*#"' …` + flattened equivalent | **0** and **0** |
| no `path::Symbol` citation wraps a line | every ``` `` ``-delimited span in the eight files matched with `re.S`, flagged when it contains `\n` and (`::` or `.py`) | **0 wrapped**. Longest added line in the whole diff is **106** columns (the pre-existing `tests/filters/test_inputs.py::test_clear_filter_input_namespace_tolerates_unimportable_submodules` reference), inside the 110-column E501 grace |
| layout / ASCII gate | `uv run python scripts/check_trailing_commas.py --check <the eight>` | exit **0** |
| lint / format, read-only (never `--fix`) | `uv run ruff check <the eight>`; `uv run ruff format --check <the eight>` | `All checks passed!`; `8 files already formatted` |
| no collateral churn | `git status --short` | the six still-uncommitted paths are exactly this cycle's: `orders/base.py`, `orders/inputs.py`, `types/base.py`, `library/orders.py`, `tests/orders/test_inputs.py`, and Slice 1's spec + rationale. `registry.py` is **absent** — my C6b mutation is byte-restored |
| `027` hunks survive | `git show 8a9840dc -- <path>` (the `git diff HEAD` form is now empty — see above) | both cohorts' hunks present in all three |

**5. Every new citation target resolves — checked by hand, because `check_citations.py` does not.** The gate
resolves `path::Symbol` and is blind to the `#"substring"` half, so the substrings the C7 replacements
introduce are ungated and were verified individually:
`utils/strings.py::graphql_camel_name` #"if not core:" (185) - `utils/inputs.py::build_strawberry_input_class`
(1168) - `utils/input_values.py::iter_input_items` (71) / `::iter_active_fields` #"if items is None:" (239) -
`orders/inputs.py::normalize_input_value` #"if field.spec is None:" (318) / #"if child_orderset is None:"
(324) - `utils/inputs.py::iter_set_subclasses` #"if cls in seen:" (1477) -
`::clear_generated_input_namespace` (1504) / `::_safe_import` (1485) / #"if factory_cls is not None:" (1544) /
#"if set_root is not None:" (1549) - the two filter twins at `tests/filters/test_inputs.py` **1417** and
**1450** (which is what makes the deleted `(lines 1009-1028)` / `(lines 1036-1056)` ranges provably wrong
*and* swapped, as the plan said) - and all seven `test_library_api.py::<name>` targets, each exactly one
definition repo-wide.

**6. C7's and C7c's mechanism claims are operative, not merely true.** `orders/inputs.py`'s
`make_set_input_namespace(...)` call passes `factory_module="django_strawberry_framework.orders.factories"`
and `set_module="django_strawberry_framework.orders.sets"` — **precisely the two names
`::test_clear_order_input_namespace_tolerates_unimportable_submodules` poisons**. So the `None` sentinel
really does drive both `_safe_import` calls to `None` and both `is not None` blocks are really skipped. The
plan asked Worker 3 to "confirm the reading"; confirmed by tracing the argument values, not by reading the
prose.

#### C6b — does the order twin still pin anything? (the required judgement)

**Yes. It pins a real negative invariant, and exactly one row pins it.** Proved by the mutation recorded
above, not reasoned.

- Anchor: `grep -c 'for clear in iter_subsystem_clears():' django_strawberry_framework/registry.py` -> **1**,
  taken **before** the copy; `git diff HEAD --stat` empty and `md5 -q` = `dd191a70f982cbefaab9f62d16c884a6`,
  so the file carried no live mutation from an earlier pass.
- Pre-mutation, at the scope run: `uv run pytest tests/test_registry.py --no-cov` -> **80 passed** (green;
  nothing to difference against).
- Mutation applied: `from .orders.inputs import clear_order_input_namespace as _reintroduced` +
  `_reintroduced()` inserted immediately above the replay loop in `TypeRegistry.clear` — the retired direct
  import, i.e. the property under test removed rather than code near it perturbed.
- Mutant, same scope: **1 failed, 79 passed.** Failing node id, listed:
  `tests/test_registry.py::test_clear_tolerates_unimportable_order_submodules`, with
  `ModuleNotFoundError: import of django_strawberry_framework.orders.inputs halted; None in sys.modules` at
  `registry.py:606`. **Collection / setup errors: 0.**
- Revert proved by byte-comparison: `cp <scratch>/dsf-proof-registry-clear.orig
  django_strawberry_framework/registry.py` then `cmp` -> exit **0**; `md5 -q` back to
  `dd191a70f982cbefaab9f62d16c884a6`; `git diff HEAD --stat -- .../registry.py` empty;
  `grep -c '_reintroduced'` -> **0**. No `git checkout` / `restore` / `stash` / `worktree` was used.

So the plan's starting reading is the one the mechanism supports: the test pins **"`clear()` performs no
direct import of an order submodule"**, and reintroducing one is caught. Two further facts the mutation
settles, which reading alone could not:

- The **filter twin did not fail** under the order-side mutation. The two twins are genuinely distinct rows
  for distinct halves, so the mirrored wording has not collapsed them into one assertion.
- The invariant rests on **one row** (itself). That is not the weakly-pinned `revision-needed` rule — that
  rule governs a boundary a slice *introduces*, and this slice introduces none — but it is worth the
  maintainer knowing: a single fixture change or skip retires the only pin on "`clear()` imports nothing",
  and the same is true of each of the four `test_clear_tolerates_unimportable_*` twins.

**Box C6b: ticked.** The judgement, its mechanism, and its evidence are recorded here. **No worker deleted
the test and no worker silently accepted it** — it pins a real invariant, so deletion was never the answer.
The residual precision problem in *how the docstring states* the mechanism is L1 below.

#### Static inspection helper

**Run, not skipped** — and the plan's justification for skipping is wrong on a point of fact (L3).
[`BUILD.md`][build] `### When to run the helper during build` obliges Worker 3 to run it when the slice
"touches an existing `.py` file under `optimizer/` or `types/`", **unconditional on whether logic was
added**; `django_strawberry_framework/types/base.py` is in the diff, so the trigger fires.

```shell
uv run python scripts/review_inspect.py django_strawberry_framework/types/base.py --output-dir docs/shadow
```

Exit **0**; wrote `docs/shadow/django_strawberry_framework__types__base.overview.md` (18,542 bytes) and
`…stripped.py`. Nothing in the overview changes any finding: the file's only diff is a docstring reflow, so
its Django/ORM markers, repeated string literals, control-flow hotspots, and imports are identical to
HEAD's by construction (instrument 2 above proves the token stream is unchanged). Shadow line numbers are
not cited anywhere in this review.

**Skip recorded, with the reason, for the other seven:** none is a new file, none is under
`optimizer/` or `types/` in the package tree (`tests/types/test_base.py` is a test-tree path, not
`django_strawberry_framework/types/`), and none gains a line of logic — the diff's executable token stream
is byte-identical to HEAD in all eight, so the 30+/50+-new-logic thresholds cannot fire. Their artifact
disposition is "no review-worthy logic" in the strictest possible sense: no logic at all.

#### Hot-path budget

`Not applicable; plan declares no hot path.` Verified rather than accepted: the executable token stream is
unchanged in all eight files, so nothing new runs per request, per resolver, per row, per connection, or per
outbound message. **No before/after number is owed and its absence is not flagged.**

#### Floor verification

`Not applicable; plan declares floor-verification scope none.` Verified on the same basis: no executable
statement changed, so no Django / Strawberry / channels integration seam is touched. No floor venv was
built and the shared `.venv` was neither mutated nor read for a version claim.

### High:

None.

### Medium:

#### M1 — the C7 defect class's real population is 20 raw `path:NN` refs in `tests/orders/`, and the artifact's deferral describes a different population than the one that exists

The slice retired 8 of them, all in `tests/orders/test_inputs.py`. An **independent** sweep — every tracked
`.py` under `django_strawberry_framework/` + `tests/` + `examples/`, whitespace-flattened, run against the
tree rather than against the slice's file list — finds **12 more, all in sibling files of the same
subsystem**:

```tests/orders/test_sets.py
sets.py:184   sets.py:269   sets.py:270   sets.py:317   sets.py:327
sets.py:330   sets.py:342   sets.py:534   sets.py:570   sets.py:578
```
```tests/orders/test_factories.py:371
orders/factories.py:138
```
```tests/orders/test_base.py:185
orders/base.py:82
```

`django_strawberry_framework/orders/sets.py` is **496** lines, so `:534`, `:570`, and `:578` point **past
EOF** — the identical rot C7's `:410` / `:461-462` / `:476-477` had, at the identical magnitude (three
past-EOF coordinates in each cohort).

The record is what is defective, not the scope decision. The plan's `### Deliberately NOT touched` third
bullet and note 7 *do* name `tests/orders/{test_sets,test_factories}.py` — but under the **C2** raw-*spec*-line
class, measured with `grep -rniE '\bspec[^ ]* ?lines? [0-9]|\blines? [0-9]{2,}'`, a pattern that cannot
match `sets.py:184`; and they attribute those files' refs to "`spec-035` / `spec-036` / `spec-038` and the
upstream cookbook". They are C7-class `path:NN` refs into **spec-028's own modules**. `tests/orders/test_base.py`
is named nowhere at all.

Why it matters: a deferral recorded against a mis-measured population reads to the next cycle as *already
assessed*, and the next reader has no way to tell the record is describing 12 refs it never saw. This is the
same instrument failure the plan's own `### Census correction` diagnosed for C2 — a finding's grep
vocabulary is not its population — arriving one class over.

**Recommended change:** Worker 1 corrects note 7 at final verification, stating the C7 `path:NN` population
**separately** from C2's raw-spec-line population, naming all three files, and recording the three past-EOF
coordinates. Worker 1 owns the artifact's final sections, so this needs no Worker 2 pass. Not in this
slice's writable set, so no code change is requested here.

Severity Medium per [`worker-3.md`][worker-3] `## Claim verification`: a stated count and scope a reader
would re-derive differently.

#### M2 — 11 `Spec <Decision|DoD>` citations are invisible to every probe this cycle ran, five of them in a file this slice edited, and they leave Slice 3's protect-list incomplete

Independent sweep for `\bSpec (line|Decision|Edge|test plan|DoD)`: **17 occurrences over 7 files**, of which
the order subsystem carries 13:

| File | n | Forms |
|---|---|---|
| `django_strawberry_framework/orders/sets.py` | 6 | `Spec DoD 4(c)` x2, `Spec Decision 8 step 6`, `Spec Decision 5` x2, `Spec Decision 13` |
| `django_strawberry_framework/orders/inputs.py` | 5 | `Spec Decision 5` x3, `Spec Decision 13`, `Spec Decision 8 step 6` |
| `django_strawberry_framework/utils/inputs.py` | 2 | `Spec Decision 8` x2 |
| `django_strawberry_framework/orders/__init__.py` | 1 | `Spec Decision 5` |
| `django_strawberry_framework/orders/factories.py` | 1 | `Spec Decision 8` |
| `tests/orders/test_composition.py` | 1 | `Spec Decision 5` |
| `tests/types/test_relay_interfaces.py` | 1 | `Spec Decision 2 (spec-015 …)` — carries its spec id, out of family |

Two consequences, and the second is the load-bearing one:

1. **A parallel-site skip inside an owned file.** `orders/inputs.py` is one of the eight. C2 steps 3-4
   standardized two sites in it (`per spec-028 Decision 3 line 452` -> `spec-028 Decision 3`,
   `Spec Edge cases line 980` -> `spec-028 Edge cases`) and left **five siblings** in the non-durable
   `Spec Decision N` spelling, which omits the spec id entirely.
2. **Slice 3's stated obligation is incomplete by 11.** The plan's note 3, Worker 2's note 2, and the build
   plan's `### Standing hazard` all derive the protect-list from the `spec-028 Decision N` (38) and
   `spec-028 test plan` (6) censuses. `Spec Decision 13`, `Spec Decision 8 step 6`, and `Spec DoD 4(c)`
   point at spec sections Slice 3 will rewrite, and **no census sees any of them** — they do not carry the
   `spec-028` token, so they are absent from the 67, the 38, and the 6 alike. Slice 3 could rename
   `### Decision 13` or renumber a DoD item and break eleven `.py` citations with every gate green.

**Recommended change:** before Slice 3 runs, Worker 1 folds the 11 in-family sites into note 3's
protect-list, and then chooses between (a) dispatching a one-step C9 re-pass to respell them
`spec-028 Decision N` / `spec-028 DoD N`, or (b) recording the deferral against the **measured** population.
The choice needs spec context Worker 2 cannot supply — whether Slice 3 intends to renumber those anchors —
which is why this escalates rather than blocking the slice. Note that (a) is not free: the plan's own
`### DRY analysis` duplication-risk item 2 warns that a citation Slice 3 can silently break is worse than
none, and `spec-028 DoD 4(c)` has no gate behind it either way.

### Low:

#### L1 — the C6 order twin's stated mechanism is true but is not the operative one for the modules the test poisons

```tests/test_registry.py:1656
"""``clear()`` itself imports nothing, so a broken ``sys.modules`` cannot break it.
...
already-resolved callables. That replay is the only place a poisoned
``sys.modules`` can be reached at all, and every submodule lookup it
makes is best-effort, so poisoning the order modules (done here) cannot
make ``clear()`` raise: ...
```

The test poisons `django_strawberry_framework.orders.inputs` and `django_strawberry_framework.orders`. The
two replayed order callbacks look up **neither**:
`clear_order_input_namespace` -> `clear_generated_input_namespace` `_safe_import`s `orders.factories` and
`orders.sets`; `orders/__init__.py::_clear_helper_referenced_ordersets` closes over a module-level `set` and
imports nothing at all. So the "every submodule lookup it makes is best-effort" clause is a true statement
about a **different pair of modules**, and the `so` that follows it does not carry. What actually makes the
test pass is the preceding clause alone — the replay is the only reachable site — plus the fact that the
replayed callbacks never touch the poisoned names. The C6b mutation is what settles it: the row fails only
when a **direct** import is reintroduced, which is precisely the invariant, and nothing about best-effort
lookups is exercised.

Every clause is individually true, so this is not a false docstring. It is a docstring whose causal chain a
reader cannot verify against the test's own inputs — the class of defect this slice exists to retire, one
notch subtler than the `except ImportError` claim it replaced.

**Recommended change:** narrow the middle clause to what the row actually pins — that `clear()` performs no
**direct** import of an order submodule, so poisoning either module name cannot reach it — and drop or
relocate the best-effort-lookup clause, which belongs to `tests/orders/test_inputs.py::test_clear_order_input_namespace_tolerates_unimportable_submodules`
where it *is* operative (verified above).

**Do not repair it alone.** The concurrently-rewritten filter twin (`027`'s work, now committed in
`8a9840dc`, out of this slice's scope) carries the **identical** shape, so a one-sided fix re-opens the
divergence C6 step 16 was closing. This routes to the maintainer's two-of-four-twins decision (the plan's
note 6), which is why it is escalated rather than requested.

#### L2 — the build report claims the two post-ship additions are "both named in the new banner"; they are not

The shipped banner names their **class and source** — "the row-preserving to-many aggregate cases from
``spec-030-connection_field-0_0_9`` P1-B" — and never
`test_library_branches_order_by_scalar_then_to_many_aggregate_no_multiplication` or
`test_library_genres_connection_pages_by_to_many_aggregate`. Worker 2's `### Validation run` C5 row asserts
"both named in the new banner", which is false; so is the report's `### Implementation notes` phrasing "a
first line attributing the two post-ship additions", which is accurate only at the level of category.

**C5 stays ticked, deliberately.** Worker 2 wrote the plan's prescribed banner text **verbatim**, which is
the correct builder behavior, and that text is what the box's contract is. I considered un-ticking and did
not: the defect is not in the diff. It is a mismatch between the plan's prose rationale ("Naming them
**gives the count a subject**, which is what the old banner lacked") and the plan's own fenced replacement
text, which names the category instead — inherited faithfully into the report's claim about it.

**Recommended change,** Worker 1's pick: either add the two names to the banner (two lines, inside the
110-column grace, and it is what the plan's rationale asked for), or correct the build report's sentence to
say the banner attributes the two additions by contract and source rather than by name.

#### L3 — the plan's Worker-3 helper-skip justification misquotes `BUILD.md`

The plan's `### Static inspection helper` says the Worker 3 triggers are "new files, `optimizer/` / `types/`
**source changes**, and 30+/50+ new logic lines; this slice hits none". [`BUILD.md`][build]
`### When to run the helper during build` says Worker 3 must run it when the slice "touches an existing
`.py` file under `optimizer/` or `types/`" — with no logic qualifier. `django_strawberry_framework/types/base.py`
is in the diff, so the trigger fires and the stated skip does not apply to it.

No finding follows from the run itself (see `#### Static inspection helper` — the output is identical to
HEAD's by construction). **Closed by this pass**, not escalated: I ran the helper rather than rely on the
misquote, and the correct skip reasoning for the other seven is now recorded above. Flagged only because the
sentence as written would license a real skip in a future cycle whose `types/` edit *does* add logic.

### DRY findings

**No duplication introduced by this slice.** It adds no helper, constant, branch, or test; the executable
token stream is unchanged in all eight files. `### Files touched` and the token-identity proof are jointly
sufficient on that.

**Existence challenge (escalated, not acted on).** The prompt's question — whether ten near-identical
docstring repairs across four test modules mean the *tests* duplicate — has a measured answer: **yes, three
contracts are pinned two or three times over one single-sited implementation.** The C7 repairs made this
visible precisely because they now spell out which `utils/` symbol each test reaches.

| Contract, single-sited in `utils/` | Family-neutral pin | Family copies |
|---|---|---|
| `utils/inputs.py::iter_set_subclasses` #"if cls in seen:" | `tests/utils/test_inputs.py::test_iter_set_subclasses_dedupes_diamond_inheritance` (241) | `tests/orders/test_inputs.py:879` + `tests/filters/test_inputs.py:1450` — **3 copies** |
| `utils/inputs.py::clear_generated_input_namespace`'s two `_safe_import` skips | `tests/utils/test_inputs.py::test_make_set_input_namespace_returns_heavy_ledger_field_specs_materialize_clear` (374), whose own docstring says "Unimportable factory / set modules are tolerated (the same cycle-safe skip `clear_generated_input_namespace` uses)", driven with deliberately unimportable module names | `tests/orders/test_inputs.py:911` + `tests/filters/test_inputs.py:1417` — **3 copies** |
| `utils/strings.py::graphql_camel_name` #"if not core:" | **none** | `tests/orders/test_inputs.py:756` + `tests/filters/test_inputs.py:834` — **2 copies, no neutral pin** |

Two distinct findings sit in that table:

1. **Rows 1-2 are redundant family copies.** `tests/utils/test_inputs.py:184-185` already asserts
   `filter_inputs._iter_filterset_subclasses is iter_set_subclasses` and
   `order_inputs._iter_orderset_subclasses is iter_set_subclasses`. Given an alias-identity assertion **plus**
   a neutral behavior test, the two family behavior copies add nothing: they re-exercise one function object
   through two names. The precedent for the consolidation is already in this repo and is recorded in the
   build plan's own D13 — the double-dispatch-plus-dedup contract was single-sited family-neutrally at
   `tests/utils/test_permissions.py::test_run_active_input_permission_checks_double_dispatch_and_dedup`, and
   four spec-named per-family tests ceased to exist. Deleting the two family copies costs no coverage (the
   neutral test executes the same statements) and the DRY win is a **deletion**, which is what
   [`BUILD.md`][build] "DRY FIRST" means by maximally DRY.
2. **Row 3 is the mirror-image defect and is the one I would fix first.** The only pin on a
   `utils/strings.py` branch lives in two *family* test modules and nowhere neutral. If either family alias
   is ever inlined or renamed, the last coverage of `graphql_camel_name`'s empty-core passthrough leaves with
   it, silently — and `fail_under = 100` will not notice, because the other copy still runs it. The fix is
   the cheap direction: add the `""` / `"_"` / `"__"` rows to
   `tests/utils/test_strings.py` (which already pins the sibling `pascal_case("")` / `pascal_case("_")`
   contract at lines 91-92) and let the family copies become alias-binding assertions or go.

**Routed to the maintainer, not acted on.** Whether these abstractions-and-their-tests should exist is a
**contract-level** question in [`BUILD.md`][build] `### Contract-level findings are escalated as maintainer
decisions before dispatch` terms, and [`worker-3.md`][worker-3] `### The existence challenge` is explicit
that Worker 3 raises it and never deletes it, and never holds a unit at `revision-needed` on an unresolved
existence challenge alone. It is also **out of this slice's writable set** on both sides
(`tests/filters/test_inputs.py`, `tests/utils/*`). Escalated as item 5 below.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` -> **empty**. `__all__` and the re-export list
are unchanged, consistent with the plan's zero-new-public-exports posture and with the token-identity proof
(the file is not in the diff at all). No spec authorization is needed because nothing changed.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md. Confirmed by `git diff HEAD --stat -- CHANGELOG.md` ->
empty.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. The only `.md` this slice writes
is this artifact. `docs/SPECS/spec-028-orders-0_0_8.md` and
`docs/SPECS/appx/spec-028-orders-0_0_8-rationale.md` are dirty from **Slice 1**, not this slice; the eight
writable paths are all `.py`. None of the concurrent-writable tracked binary / generated files
(`examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`) appears in
`git status --short`.

One item from that checklist *does* apply and passes on its own terms: this slice edits `.py` docstrings that
feed no script-rendered doc (`docs/TREE.md` renders **module** docstrings; the only module docstrings touched
are `orders/base.py`'s Layer word and `library/orders.py`'s C8 parenthetical, neither of which introduces
staging language — no "planned", no "Slice N", no `TODO(`). The `spec-028` / `spec-030` references the new
text adds are provenance citations of design rationale, which that checklist explicitly says to **keep**.

### What looks solid

- **The load-bearing claim is the one that was actually proven.** Worker 2 chose the right instrument for
  "nothing executable changed" — pristine-HEAD fetch, docstring-stripped AST, `ast.dump` comparison — and it
  survives an independently written second instrument that keeps non-docstring string literals verbatim. It
  is also what makes the zero-boundary declaration checkable rather than assertable, which is the whole
  slice's foundation.
- **The deviation was self-reported with its cause, not smoothed over.** The plan's census arithmetic was
  wrong in two of three digits; Worker 2 measured, disagreed with the plan, attributed the delta to the
  plan's own replacement text, wrote the correction to disk under `### Notes for Worker 1`, and named it as
  the same hazard class the plan itself warns about. Re-measurement confirms it exactly, including the
  per-file differencing.
- **C2 step 6's deletion is the right call and rests on evidence.** The spec's Test-plan bullet for
  `::test_root_get_queryset_runs_before_order_apply` now reads
  `{ allLibraryBranches(orderBy: [{ city: DESC }]) { id name city } }` and explains the `city`-not-`name`
  choice itself, so the docstring's "Spec line 1038 names ``name: DESC``" was **false**, not merely
  unnavigable. A false sentence is deleted, not repaired, and the surviving paragraph keeps both operative
  reasons (the gate denies the anonymous half; staff cannot substitute because staff bypass the very
  `get_queryset` hook under test).
- **C4 verified from three independent directions.** Decision 3 puts lazy class references in `RelatedOrder`
  at **Layer 1** (spec 372) and the module-fallback resolution at **Layer 2** in `sets_mixins.py` (374); the
  rationale companion's Decision 3 records `rev4 H1` moving Layer 2's home there; and after the one-word fix
  the docstring reads coherently — this module **is** Layer 1 and consumes Layer 2 by sibling import.
  `factories.py`'s `Layer 5` was re-confirmed correct and its diff is **empty**.
- **C3's substantive correction is a measurement, not a re-count.** The nested `shelf:` order surface has
  exactly two live users, and the two names written are those two. The three `filter: {{ shelf: {{` sites and
  the `shelves:` sites are correctly excluded — `shelves` is `BranchOrder`'s branch, not the `BookOrder.shelf`
  surface the docstring is about.
- **C5's banner gives the count a derivation.** Functions vs rows distinguished, the parametrized source of
  the three extra rows named, and the two out-of-card additions attributed to their real spec. The 19 is now
  confirmed by real collection rather than `16 - 1 + 4` arithmetic.
- **The three unplanned body-comment fixes are in scope and correctly reasoned** — see the dedicated
  assessment below.
- **The plan's forbidden edges all held.** `factories.py` diff empty. The connection twin (~1697) and relay
  twin are absent from the `tests/test_registry.py` diff — verified from the hunk ranges, not from Worker 2's
  say-so. `test_glossary_api.py` untouched. No `027` hunk reverted, reformatted, or tidied in any of the
  three baseline-dirty files, including through the mid-pass commit.
- **Zero wrapped citations, measured with the right instrument.** The wrap hazard is what turns a gated
  citation back into silent rot, and every one of the ~20 new `path::Symbol` refs sits unbroken on one line,
  longest at 106 columns.

#### The three unplanned body-comment fixes: in scope, and adequately recorded with one gap

Judged rather than waved through, because an unplanned edit is a scope question either way and
`### Spec slice checklist (verbatim)` has no box for one.

**In scope.** All three sit inside tests whose docstrings this slice was already repairing; all three
asserted a **retired mechanism**, i.e. the same defect class as the docstring above them; none touches an
assertion; and the plan's step 16 already established the governing principle by name — *"Leaving the
docstring right and the comment wrong is a half-fix"* — for the third of the three. Applying a rule the plan
states for one site to two structurally identical sites in the same files is faithful execution, not scope
creep. Verified individually: `orders/inputs.py`'s guard really reads `if field.spec is None:` (line 318), so
the `if spec is None` comment was stale; and `clear_generated_input_namespace` really carries no
`except ImportError`, so the "exercising both `except ImportError` guards" comment was false.

**Distinguished from the ninth finding, and the distinction is the right one.** These three are the *same*
finding recurring in a second site within an owned file. The `library/orders.py` "Five ordersets" sentence is
a *different, already-catalogued* finding (**D15**) that belongs to another slice. Worker 2 drew exactly that
line, and it holds.

**Adequately recorded, with one gap.** Worker 2's `### Implementation notes` names all three by
symbol-qualified path with the reason and the "half-fix" citation — enough for a maintainer to audit them
from the artifact alone, which is the standard. The gap: they are recorded **only** there, and Worker 1's
final verification audits **ticks**, so nothing in the checklist will draw its eye to three edits no box
covers. Recommended: Worker 1 records a one-line acknowledgement under
`### Spec changes made (Worker 1 only)` at final verification so the maintainer's diff read and the
checklist agree.

### Temp test verification

- **No temp test written; `docs/builder/temp-tests/slice-2/` is untouched and empty.** There is no behavior
  to demonstrate (nothing executable changed) and no assertion to show non-distinguishing. The C6b question
  was settled by the mutation loop above, which needs no test file.
- Scratch artifacts used, all **outside** the repository under
  `/private/tmp/claude-501/.../scratchpad/`: `head/` (eight pristine `git show HEAD:` copies),
  `ast_check.py` (the two-instrument comparison), `dsf-proof-registry-clear.orig` (the C6b pristine copy).
  Disposition: throwaway, outside the tree, nothing to promote or delete in-repo.
- No `--cov*` flag appears in any command in this pass. The three `pytest` invocations are
  `tests/test_registry.py --no-cov` (twice, the C6b pre-mutation and mutant runs) and
  `test_library_api.py --no-cov --collect-only -n 0` (the C5 row count, which executes no test body).

### Notes for Worker 1 (spec reconciliation)

1. **Escalated: the ninth finding was correctly left alone, but its only stated resolution path does not
   exist.** `examples/fakeshop/apps/library/orders.py`'s module docstring opens *"Five ordersets mirror the
   relation shape…"*; **seven** ship (verified: `BranchOrder`, `ShelfOrder`, `BookOrder`, `LoanOrder`,
   `PatronOrder`, `PeriodicalOrder`, `IssueOrder` — `grep -c '^class .*Order(OrderSet)'` -> 7), the two extra
   being the keyset-cursor substrate pair. This is build-plan finding **D15** surfacing on the code side.

   **Leaving it was the right call, and the reason belongs on the record so it is not re-fought.** Three
   things distinguish it from the three body comments Worker 2 *did* fix unplanned: it is not the same
   finding recurring in a second site but a **separate catalogued finding owned by another slice**; its
   correct wording depends on how Slice 3 states DoD 13-14's shipped shape (five-vs-seven ordersets and
   six-vs-eight `Meta.orderset_class` wirings are one claim, and having the code say seven while the spec
   says five is not obviously better than having both say five); and a builder inventing a ninth finding
   mid-pass is precisely the drift the artifact-as-contract model exists to stop. Worker 2 escalated it on
   disk with the exact sentence and the correct number, which is the behavior the contract asks for.

   **What Worker 2's note 3 gets wrong is the disposition, not the decision.** It recommends "carry it into
   Slice 3's D15 work as a code-side sibling" — but Slice 3 is Worker 1's alone and **Worker 1 does not edit
   source** ([`BUILD.md`][build] `## Required reading per worker`: relevant source is `yes (read-only)` for
   Worker 1). So Slice 3 structurally **cannot** close the code side. The only two mechanisms that can are
   (a) a one-step **C9 re-pass** dispatching Worker 2 back to this artifact for the sentence
   (`Five` -> `Seven`, naming `PeriodicalOrder` / `IssueOrder` and their substrate role — the file's own
   `PeriodicalOrder` docstring already states it), sequenced **after** Slice 3 fixes D15's spec side so both
   land on one number; or (b) hand it to the maintainer as a known-false docstring. Please pick one
   explicitly — if neither is chosen, it falls through the seam between two slices, which is the class of
   defect this whole cycle exists to close.

2. **Escalated: M2 is a Slice 3 precondition, not a cosmetic.** Eleven `Spec Decision N` / `Spec DoD N`
   citations in the order subsystem's `.py` files are invisible to the `spec-028` (67), `spec-028 Decision N`
   (38), and `spec-028 test plan` (6) censuses, because they carry no `spec-028` token. Three of them point
   at anchors Slice 3 may rewrite (`Spec Decision 13`, `Spec Decision 8 step 6`, `Spec DoD 4(c)`). Fold them
   into note 3's protect-list **before** Slice 3 runs, then choose between a C9 respelling pass and a
   deferral recorded against the measured population. Full table under **M2**.

3. **MAINTAINER — Slice 2's edits in three files were committed inside the `027` cycle's commit.**
   `8a9840dc` *"docs(specs): complete the spec-027 record and reconcile its Decision 9 claims"* carries
   `tests/types/test_base.py`, `tests/test_registry.py`, and
   `examples/fakeshop/test_query/test_library_api.py`, each holding both cohorts' hunks. Nothing is lost and
   nothing was reverted (verified against `git show HEAD:<path>` — evidence in
   `### Working-tree event this review must record first`). Two live consequences: **`git diff HEAD` is now
   empty for three of the eight paths**, so any later pass verifying Slice 2 must read `git show 8a9840dc --
   <path>` or `git diff 5c6fdd71 -- <path>` instead; and three `spec-028` hunks sit in committed history
   under a `spec-027` message. Both are the maintainer's to resolve. No worker reverted, re-staged, or
   amended anything ([`AGENTS.md`][agents] #"Files dirty at task start"; [`BUILD.md`][build] workers never
   rewrite history).

4. **M1 — correct note 7's C7 population at final verification.** It currently describes 12 `path:NN` refs
   it never measured, under the wrong finding class, attributed to the wrong specs, and omits
   `tests/orders/test_base.py` entirely. Three of the 12 point past `orders/sets.py`'s 496-line EOF. Worker 1
   owns that section, so no Worker 2 pass is needed. Full evidence under **M1**.

5. **Escalated: DRY existence challenge — three contracts on the single-sited `utils/` substrate are pinned
   two or three times over.** Measured table under `### DRY findings`. The resolution paths, for the
   maintainer to pick between: **(a)** delete the two family copies of the diamond-dedup and
   clear-namespace-tolerance contracts, keeping the neutral pin plus the existing alias-identity assertions
   at `tests/utils/test_inputs.py:184-185` — the deletion costs no coverage and follows the precedent D13
   already records for `tests/utils/test_permissions.py`; **(b)** keep them but restate each family
   docstring as pinning the *alias binding* rather than the shared behavior; **(c)** leave as-is. Independent
   of that choice, `utils/strings.py::graphql_camel_name` #"if not core:" has **no** neutral pin and should
   gain one at `tests/utils/test_strings.py` beside the existing `pascal_case("")` / `pascal_case("_")` rows,
   because today its only coverage rides two family aliases and would leave with either. All sites are
   outside this slice's writable set.

6. **L1 and L2 need your pick, both recorded above with the two options each.** L1 (the C6 docstring's
   non-operative causal clause) must be repaired **paired with the filter twin** or not at all, so it folds
   into the plan's note 6 two-of-four-twins decision. L2 (the banner names the two additions by category, not
   by name; the build report says otherwise) is either a two-line banner edit or a one-sentence report
   correction.

7. **Everything the plan and Worker 2 escalated in their own notes stands unchanged by this review**, with
   the corrections above folded in: note 4's `66 / 38 / 5` is superseded by **67 / 38 / 6** (re-measured and
   attributed here); note 7's population is superseded by M1; note 3's protect-list is incomplete by M2's 11
   sites. The `check_citations.py` gate-extension proposal in note 7 remains the right card and would have
   caught **every** C2 and C7 site in this slice **and** all 12 in M1 — worth adding that it should also
   flag the bare `Spec (Decision|DoD|Edge)` form from M2, which no proposed pattern in note 7 covers.

### Checklist audit

Every box walked against the diff, not against the build report. **Sixteen ticks confirmed landed; C6b
ticked by this pass; no box un-ticked; no box left silently unaddressed.**

- C1, C2, C3, C3b, C4, C5, C6, C7, C7b, C7c, C8 — each confirmed by the postcondition table above, at the
  command the plan specifies, plus per-site reading of the diff.
- **C6b — now `- [x]`.** The judgement, mechanism, mutation, failing node id, and byte-proved revert are in
  `#### C6b`. This was the only box Worker 2 left open and it was correctly left to this pass.
- "Zero new `spec-028 #"substring"` citations" — 0 single-line and 0 flattened.
- "No executable statement changed" — two independent instruments, 8/8.
- "Nothing edited outside the eight writable `.py` paths" — confirmed, with one declared exception: this
  review transiently mutated `django_strawberry_framework/registry.py` for the C6b diagnostic under
  [`worker-3.md`][worker-3]'s narrow carve-out, recorded **before** the mutation, reverted inside this pass,
  revert proved by `cmp` exit 0 plus matching `md5` plus an empty `git diff HEAD --stat`.
- ruff scoped / `git status --short` clean — re-run read-only (`ruff check`, `ruff format --check`; never
  `--fix`), both clean; no path outside `### Files touched` is dirty.
- gates — `check_citations.py` **758**, exit 0 (>= 743); `check_trailing_commas.py --check` exit 0.
- **C5's tick examined and deliberately kept** — reasoning in L2.

### Review outcome

`review-accepted`.

The slice does what it says: eight classes of unresolvable citation retired across eight files with **zero
executable statements changed**, proven on two independent instruments rather than asserted; every
replacement target verified to resolve, including the `#"substring"` halves no gate sees; both gates green
with the citation count **risen** from 743 to 758 because ungated coordinates became gated symbols; and no
citation wrapped across a line, which is the one way this class of repair silently undoes itself. The
required C6b judgement is delivered with a mutation, a failing node id, and a byte-proved revert: the test
pins a real negative invariant, so no deletion was ever warranted.

Two Medium findings and three Low remain, none of them a defect in the diff and none resolvable by Worker 2
without spec context Worker 1 owns:

- **M1** and **M2** are defects in the artifact's own *record* of what it deferred — a population
  mis-measured by one finding class, and a protect-list eleven sites short of the population Slice 3 is
  about to walk over. Both are corrected by Worker 1 in sections Worker 1 owns; M2 additionally needs a
  Slice-3-scope decision.
- **L1** cannot be fixed one-sided without re-opening the twin divergence C6 was closing, so it belongs to
  the maintainer's two-of-four-twins call. **L2** is a choice between a two-line banner edit and a
  one-sentence report correction. **L3** is closed by this pass — I ran the helper rather than accept the
  misquoted skip.

Accepted under [`worker-3.md`][worker-3]'s escalation clause with every finding routed above under an
`Escalated:` or explicit-recommendation form and its resolution paths named. Holding the slice at
`revision-needed` would buy nothing: no finding names a change Worker 2 could make to a file it owns, and
one — the DRY existence challenge — is a contract-level question [`worker-3.md`][worker-3] forbids blocking
on. Worker 1's final verification owns the decisions.

---

## Final verification (Worker 1)

### Summary

The eighteen dispatched steps landed and the load-bearing claim holds: **zero executable statements changed in all eight original files**, re-derived by this pass on a third instrument against two reference points. Sixteen ticks survive audit, **one is an over-tick and is un-ticked** (C5 — the banner names the two post-ship additions' *category*, and the box's own text says "naming the two post-ship … additions"). C6b's judgement is delivered with a mutation, a failing node id and a byte-proved revert; L3 is closed.

`Status: revision-needed`, for three independent reasons, any one of which is sufficient:

1. **The C5 over-tick.** `BUILD.md` `### Dispatched findings checklist` and `worker-1.md` `## Final verification job` step 3 both make an over-tick `revision-needed` without discretion.
2. **M1 and M2 are the partial claim fix, and the partition is extended** — with corrected measurements, because *both* Worker 0's and Worker 3's readings are incomplete and in M1's case they measured two different populations while each reporting one.
3. **The ninth finding's code half has nowhere else to land.** Slice 3 is mine and I do not edit source; the file is already writable here.

Nothing in the diff is a defect. Everything below is either a record defect in this artifact (mine to fix, done) or a population this slice repaired part of.

### Checklist audit — every tick re-derived, not read

Re-measured against the **current files**, not against any diff: three of the eight paths were swept into `8a9840dc` mid-review, so `git diff HEAD -- <path>` is empty for them and present-state reading is the only valid instrument.

| Box | Verdict | Re-derivation |
|---|---|---|
| C1 | **holds** | `grep -roh --include='*.py' '(spec-028 N3)' …` -> **0** |
| C2 | **holds** | flattened four-class probe over the eight -> `CLEAN` (the wrapped `line 1038`/`1039` pair is the site only this instrument can see, and it is gone) |
| C3 | **holds** | same probe, `Test-N-ordinal` class -> nothing |
| C3b | **holds** | `library/orders.py` cites exactly `::test_library_books_order_by_forward_fk_relation` + `::test_library_books_order_by_multi_field_priority`; the 4 -> 2 correction is in the file |
| C4 | **holds** | `orders/base.py:3` reads `Layer 1`, `orders/factories.py:3` reads `Layer 5`, `git diff HEAD --stat -- orders/factories.py` empty |
| **C5** | **OVER-TICK — un-ticked** | banner read at `test_library_api.py` ~1737-1743. It carries `16 test functions / 19 test rows`, the parametrized derivation, and `the row-preserving to-many aggregate cases from ``spec-030-connection_field-0_0_9`` P1-B` — and **neither test name**. See the ruling below |
| C6 | **holds** (text landed; its accuracy is L1) | docstring + inline comment read at `tests/test_registry.py` 1655-1694; both mirror the filter twin |
| C6b | **holds** | Worker 3's record carries the anchor count, the `md5`, the mutation, `1 failed, 79 passed`, the failing node id, `0` collection errors, and the `cmp`-proved revert. Every field `BUILD.md` `### What gets recorded` asks for is present |
| C7 | **holds** | seven `Covers` docstrings in the block, all `path::Symbol`; no `path-NN-citation` hit in the probe |
| C7b | **holds** | both cross-test line ranges absent; the twins' full names survive |
| C7c | **holds** | `::test_clear_order_input_namespace_tolerates_unimportable_submodules` opens `Covers both best-effort submodule lookups in ONE test` |
| C8 | **holds** | `grep 'spec-028 + Decision'` -> **0**; `library/orders.py:10` reads `(spec-028 Decision 3 Layer 2)` |
| Zero new `#"substring"` citations | **holds** | `0` single-line, `0` flattened |
| No executable statement changed | **holds** | third instrument, below |
| Nothing outside the eight | **holds** | `git status --short` lists six paths, all this cycle's; `registry.py` absent (Worker 3's revert is byte-proved) |
| ruff scoped / no churn | **holds** | `ruff format --check` -> `8 files already formatted`; `ruff check` -> `All checks passed!`; never `.`, never `--fix` in this pass |
| gates | **holds** | `check_citations.py` -> `OK: 758 citations resolve (681 in 422 .py files, 77 in KANBAN.md)`, exit 0 (>= 743); `check_trailing_commas.py --check <the eight>` exit 0 |

**Zero-executable-change, re-derived independently (instrument 3).** Docstring-stripped `ast.dump` against **both** reference points, because HEAD moved:

```
SAME  dirty-vs-HEAD        django_strawberry_framework/types/base.py
SAME  dirty-vs-HEAD        django_strawberry_framework/orders/base.py
SAME  dirty-vs-HEAD        django_strawberry_framework/orders/inputs.py
SAME  at-HEAD(committed)   tests/types/test_base.py            + SAME vs 5c6fdd71
SAME  dirty-vs-HEAD        tests/orders/test_inputs.py
SAME  at-HEAD(committed)   tests/test_registry.py              + SAME vs 5c6fdd71
SAME  dirty-vs-HEAD        examples/fakeshop/apps/library/orders.py
SAME  at-HEAD(committed)   examples/fakeshop/test_query/test_library_api.py  + SAME vs 5c6fdd71
```

For the three swept files `git show HEAD:<path>` is now the post-Slice-2 content, so `SAME` there is trivially true and proves nothing on its own; the `5c6fdd71` column is what carries the claim. **Recorded so no later pass mistakes the trivial reading for the proof.**

**Boundary count zero — confirmed, and the failability record is confirmed ABSENT-BY-ENTITLEMENT rather than missing.** Zero boundaries, so `### Failability proofs` reading `None; this pass introduced no new boundary.` is the correct content, and the empty mandatory-re-run set is legal in exactly this case. The entitlement rests on the token-identity proof, which is re-derivable as recorded; I did not re-run both of Worker 3's instruments and per my role file I need not. **No fail-open shape can have landed**: a fail-open expression is an executable expression, and the executable token stream is unchanged in all eight files.

**Hot-path: none owed, none flagged.** **Floor verification: none owed** — no floor venv was built and the shared `.venv` was not mutated by any pass. **Staged-anchor sweep:** `grep -rn 'TODO(spec-028' .` -> no hits, tree-wide.

### Ruling 1 — C5 / L2: the box is un-ticked and the banner gains the two names

Worker 3 saw the mismatch (L2), considered un-ticking, and kept the tick on the ground that Worker 2 wrote the plan's fenced text verbatim. That reasoning protects the builder correctly and identifies the wrong contract. **The checklist box is the contract Worker 1 audits**, not the plan's fenced illustration of it — `BUILD.md` `### Dispatched findings checklist` names "a box ticked with no matching fix" as the over-tick shape, and `ARTIFACT.md` `## Final verification (Worker 1)` makes an over-tick block `final-accepted`. The box says "naming the two post-ship `spec-030-connection_field-0_0_9` P1-B additions"; the banner names a category. Half the box's contract did not land.

Worker 2 is not at fault and the plan's fenced text is the defect: it contradicts its own stated rationale ("Naming them **gives the count a subject**"). Repair in **step 19**, which also discharges L2's first option. L2's second option — leaving the banner and correcting the build report's sentence instead — is **rejected**: it would make the report accurate about a banner that still fails the box.

### Ruling 2 — M1: extend, and the two workers measured two different populations

Both re-verifications are correct readings of their own instrument and **neither measured the population**. They are not competing readings of one number; they are disjoint classes, and reporting either as "the" figure hides the other entirely. Measured by this pass over `tests/orders/`:

| Class | Occurrences | Per file | Worker 0 | Worker 3 |
|---|---|---|---|---|
| prose `line NN` | **11** | `test_sets.py` 7, `test_factories.py` 3, `test_composition.py` 1 | 10 (its `[0-9]{2,4}` pattern excludes `line 8`) | not measured |
| raw `path:NN` | **12** | `test_sets.py` 10, `test_factories.py` 1, `test_base.py` 1 | not measured | **12 — correct** |
| **total** | **23** | | | |

Two corrections to the authorization's own figures, both material to what the re-pass must do:

- **Worker 0's per-file split is wrong and its tenth site is double-counted.** It reports "test_sets.py (6) and test_factories.py (3); the tenth is test_composition.py". `test_sets.py` carries **7** prose sites, `test_factories.py` 3 — that is the 10 its pattern matched — and `test_composition.py` #"``AGENTS.md`` line 8 carve-out" is an **eleventh** site its pattern cannot see (one digit against a `{2,4}` quantifier). The same single-digit blind spot, one class over, that the plan's own `### Census correction` diagnosed.
- **"Four more cite the upstream cookbook by line" is wrong: exactly two do.** `test_factories.py` #"cookbook lines 124-130" and `test_sets.py` #"per cookbook line 280". The other eight prose sites and all twelve `path:NN` sites cite **this card's own modules**.

**Past-EOF count is 9, not 5.** `orders/sets.py` is 496 lines and is cited at `526`, `532`, `535`, `571`, `579` (prose) and `534-535`, `570-571`, `578-579` (path form); `orders/factories.py` is 155 lines and `test_factories.py` cites `(line 159)`.

**And the coordinate rot is the smaller half — every one of the twelve `path:NN` refs points at wrong content, several because the guard it names moved out of the file entirely** (the D5 shared-substrate squeeze, the same cause as C7's). Verified this pass:

| Cited | What is actually at that line | Where the named guard lives at HEAD |
|---|---|---|
| `sets.py:184` | a `get_fields` docstring bullet about the cache gate | `orders/sets.py::OrderSet._expand_meta_fields` #"if meta_fields is None:" |
| `sets.py:269`, `:270-271`, `:317-318`, `:327-329`, `:330-331` | a `ConfigurationError` f-string / a DISTINCT-ON docstring bullet | `utils/input_values.py::iter_input_items` (dict branch, `__dataclass_fields__`-is-`None` return) via `orders/inputs.py::normalize_input_value` |
| `sets.py:342-346` | `result.append(...)` inside `get_flat_orders` | `utils/permissions.py::active_permission_targets` #"else fallback_path(field.python_attr)" |
| `sets.py:534-535`, `:570-571`, `:578-579` | **past EOF** | `orders/sets.py::OrderSet._apply_orderings` #"if not data:" and #"if not expressions:" — the sync/async pair collapsed into one helper, so three of these coordinates also assert a split that no longer exists |
| `factories.py:138` | `get_orderset_class`'s `Args:` docstring | `utils/inputs.py` #"if set_cls in seen:" (pop-time) |
| `factories.py` `(line 159)` | **past EOF** | `utils/inputs.py` #"if target is not None and target not in seen:" (enqueue-time) |
| `base.py:82` | a **blank line** | `orders/base.py::RelatedOrder.orderset` (the setter, 84-85) |

I therefore agree with Worker 0's position and adopt it: this is the partial claim fix — 8 of 20 `path:NN` sites in this card's own test tree repaired, 0 of 11 prose sites — and `AGENTS.md` #"never offer defer-the-real-fix sequencing" forbids cataloguing the residue instead. **Extend. C10 and C11 below.**

**One sub-class is deliberately NOT repaired, and the ground is decidable so it is not re-fought.** The **cookbook** line refs — 2 in `tests/orders/`, plus 4 more inside `orders/sets.py` itself that neither Worker 0 nor Worker 3 measured (`lines 30-38`, `lines 265-285`, `line 279-280`, `lines 115-170`) — stay byte-identical. Rule 27's remedy is `path::QualifiedName`, and the target is a third-party checkout at `~/projects/django-graphene-filters/` that this repo neither vendors nor pins: a rewrite would produce a citation `check_citations.py` still cannot resolve (first-party only) whose truth depends on an unpinned external version. There is no durability to gain. Carried to `bld-final-028.md`'s `### Deferred work catalog` as **six cookbook line refs, left with reason**, so the next reader inherits the ruling rather than the sites.

### Ruling 3 — M2: extend, and the population is 17 / 16 in-family, not 16 / 15

**Worker 3's 17 is right; Worker 0's single-line re-measurement of 16 missed a WRAPPED site.** `django_strawberry_framework/orders/sets.py` lines 451-452 read `(Spec Decision` / newline / `8 step 6 -- denial gates raise pre-mutation)`. No single-line grep can see it. Flattened, per file:

| File | n | in-family |
|---|---|---|
| `django_strawberry_framework/orders/sets.py` | **6** (one wrapped) | 6 |
| `django_strawberry_framework/orders/inputs.py` | 5 | 5 |
| `django_strawberry_framework/utils/inputs.py` | 2 | 2 |
| `django_strawberry_framework/orders/__init__.py` | 1 | 1 |
| `django_strawberry_framework/orders/factories.py` | 1 | 1 |
| `tests/orders/test_composition.py` | 1 | 1 |
| `tests/types/test_relay_interfaces.py` | 1 | **0** (`spec-015`, correct, stays byte-identical) |
| **total** | **17** | **16** |

This is the third time in two slices that a citation-rot population was under-measured by exactly the wrapped-site count, and the second time in this slice's own paperwork. **My own carry-forward said to run the flattened probe as the FIRST measurement of any citation-rot population, and the authorized partition was measured single-line anyway.** The finding is not that a number was off by one; it is that the *authorization* was written against an instrument known in this cycle to be blind.

The Slice-3 precondition argument is sound and decides it: I run Slice 3 next, it rewrites every `### Decision N` heading's prose, and all sixteen sites carry no `spec-028` token — so `spec-028` 67, `spec-028 Decision N` 38 and `spec-028 test plan` 6 are all blind to them and no gate watches them. Renaming a heading would break sixteen citations with every gate green and every census unchanged. **Extend. C12 below.**

Worker 3's option (b) — record the deferral against the measured population instead — is **rejected**: it defers a precondition of the very next slice past the point where it can be honoured.

### Ruling 4 — the ninth finding: the code half lands HERE, as C9

Slice 3 structurally cannot close it. Worker 3 is right about the mechanism (`BUILD.md` `## Required reading per worker` gives Worker 1 source as `yes (read-only)`; `worker-1.md` `## Scope` forbids editing source outright), and Worker 2's recommended disposition is therefore void. Of the two mechanisms Worker 3 names I take **(a), a step in this re-pass**, not (b), hand to the maintainer:

- The file is **already in the writable set** and this slice was **already editing it** (C3 steps 9-11, C8 step 18). A false count in a docstring three lines above a citation this slice repaired is not a separate card's work.
- **"Seven" is a measurement, not a wording choice**: `grep -c '^class .*Order(OrderSet)' examples/fakeshop/apps/library/orders.py` -> **7** (`BranchOrder`, `ShelfOrder`, `BookOrder`, `LoanOrder`, `PatronOrder`, `PeriodicalOrder`, `IssueOrder`). It does not depend on how Slice 3 words D15.
- Worker 3's sequencing worry — that code saying seven while the spec says five is "not obviously better" — **inverts**. D15's own resolution is for the spec to state the shipped shape, so both sides land on seven either way; holding a known-false count in code to preserve agreement with a sentence Slice 3 is about to correct preserves nothing, and the seam it leaves is exactly the class of defect this cycle exists to close.

No sequencing constraint is imposed: the two halves are independently true.

### Ruling 5 — L1: repair, and repair BOTH twins

Worker 3's diagnosis is correct and I verified the mechanism myself on **both** sides. The clause "every submodule lookup it makes is best-effort, so poisoning the order modules … cannot make `clear()` raise" is true of a *different pair of modules* than the test poisons:

- order twin poisons `…orders.inputs` / `…orders`; the replayed callback `_safe_import`s `…orders.factories` / `…orders.sets` (`orders/inputs.py::make_set_input_namespace` call args) and `orders/__init__.py::_clear_helper_referenced_ordersets` imports nothing at all.
- **filter twin poisons `…filters.inputs` / `…filters`; its callback `_safe_import`s `…filters.factories` / `…filters.sets`** — `filters/inputs.py` lines 166 and 169, read this pass. **Identical non-operativity, identical mechanism.**

So Worker 3's constraint ("repair paired with the filter twin or not at all") and accuracy are not in tension: **both twins get the same narrowing**, and they stay one story. The filter twin is in `tests/test_registry.py`, already in the writable set, and now committed rather than concurrently dirty. The scope ground: the clause is a claim about the **shared `TypeRegistry.clear` replay mechanism**, not about either family's contract — the same shared-substrate reasoning that put `django_strawberry_framework/utils/inputs.py` into the writable set for M2. The connection and relay twins are a different case and stay untouched: their defect is the original `except ImportError` premise, which is a claim about *their* cards' registration shapes, and the maintainer decision (note 6) still owns them.

### Ruling 6 — L3: confirmed closed

Worker 3 ran `review_inspect.py` on `django_strawberry_framework/types/base.py` rather than accept a skip whose `BUILD.md` trigger the plan misquoted; exit 0, `docs/shadow/django_strawberry_framework__types__base.overview.md` (18,542 bytes). The trigger genuinely is unconditional on added logic, so the plan's sentence was wrong and the run was owed. No finding follows from the output. The misquoted sentence lives in Worker 0's plan and `BUILD.md` is fenced this cycle, so the correction is recorded here and in the deferred-work catalog rather than edited into either file.

### Ruling 7 — the DRY existence challenge: deferred, deliberately, and here is why it is not this slice's

**Not folded into Slice 2, and not the integration pass's.** Every resolution path changes executable statements — adding rows to `tests/utils/test_strings.py`, or deleting the family test copies — which destroys the property the whole slice's verification rests on (zero executable change, proved on three instruments) and would newly owe the boundary machinery the slice is currently entitled to skip. Both halves also sit outside the writable set (`tests/filters/test_inputs.py`, `tests/utils/*`). The integration pass is mine and does not edit source either.

**Recorded as deferred work** for `bld-final-028.md` `### Deferred work catalog`, split because the two halves are different kinds of question:

- **Rows 1-2 — a contract-level maintainer decision.** Diamond dedup and clear-namespace tolerance are each pinned three times over one single-sited `utils/` implementation, with a family-neutral pin plus alias-identity assertions already in place at `tests/utils/test_inputs.py`. The higher-quality fix is a **deletion** of the two family copies, and the precedent is already in this repo (D13: the double-dispatch-plus-dedup contract was single-sited family-neutrally and four spec-named per-family tests ceased to exist). `worker-3.md` `### The existence challenge` reserves the delete call for the maintainer and I do not pre-empt it.
- **Row 3 — a coverage-fragility finding, and the one I would action first.** `utils/strings.py::graphql_camel_name` #"if not core:" has **no** family-neutral pin; its only coverage rides two family aliases, so inlining or renaming either alias silently retires the last pin while `fail_under = 100` stays green because the other copy still executes the line. Cheap fix, opposite direction from rows 1-2: add the `""` / `"_"` / `"__"` rows to `tests/utils/test_strings.py` beside the existing `pascal_case("")` / `pascal_case("_")` pair. **Worth a card in its own right**, independent of how rows 1-2 are decided.

### Ruling 8 — census baseline confirmed and note 4 corrected

Re-derived once more by this pass, a fifth independent measurement: `spec-028` **67**, `spec-028 Decision [0-9]+` **38**, `spec-028 test plan` **6**, `spec-028[^)]*#"` **0**. `### Notes for Worker 1` note 4 is corrected in place — it told Slice 3 to re-derive against `66 / 38 / 5`, and Slice 3 is mine, so a wrong baseline there propagates straight into the slice I run next. Note 7's M1 population is corrected in place for the same reason.

**Note the re-pass moves all three again**, so 67 / 38 / 6 is this slice's *mid-state*, not its handoff number. C12 alone adds sixteen `spec-028` tokens. The re-pass records the closing census and that reading — not this one — is what Slice 3 and the integration pass differences against.

### Re-pass steps (Worker 1, final verification)

**Writable set: the eight original paths plus the five Worker 0 authorized plus `tests/orders/test_sets.py` and `tests/orders/test_factories.py`, plus `tests/orders/test_base.py`** — the thirteenth path M1's `path:NN` class requires and which the authorization omits because no earlier measurement saw it. Single cohort throughout; nothing runs concurrently against these files. `django_strawberry_framework/orders/factories.py` remains **M2/C12-only**: its `Layer 5 of the spec-028 six-layer pipeline` citation is verified correct by four passes and stays byte-identical.

**Standing constraints on every step below, none discretionary.** No `path::Symbol` or `#"substring"` citation wraps across two source lines (the wrap is what turned M2's population invisible and C2's site ungreppable — it is the defect this slice exists to retire, not a style note). No line past the 110-column E501 grace. **Zero new `spec-028 #"substring"` citations.** No executable statement changes in any file: the third-instrument AST/token identity must still read `SAME` for all thirteen paths at the end of the pass. `ruff format` / `ruff check --fix` scoped to the files touched, never `.`.

---

**Step 19 — C5: the banner names both post-ship additions.** `examples/fakeshop/test_query/test_library_api.py`, the `Live HTTP order coverage` banner. Keep every line that is there and add the two names, e.g. as a closing pair of comment lines:

```
# The two out-of-card additions are
# ``test_library_branches_order_by_scalar_then_to_many_aggregate_no_multiplication``
# and ``test_library_genres_connection_pages_by_to_many_aggregate``.
```

Both fit inside 110 columns as shown. Re-derive the count before writing, per the box: bounds from the `Live HTTP order coverage` banner to the `^# spec-029` banner, `^def test_` -> 16, exactly one `parametrize` over four NULLS directions -> 19 rows. **Also correct the build report's two false sentences** — the `### Validation run` C5 row's "both named in the new banner" and `### Implementation notes`' "a first line attributing the two post-ship additions" were true of neither the old banner nor the plan's fenced text; after this step the first becomes true and the second should read "a first line attributing them by contract and source".

**Step 20 — C6c / L1: narrow the non-operative clause in both registry twins.** `tests/test_registry.py`, `::test_clear_tolerates_unimportable_order_submodules` (docstring ~1655-1667 and inline comment ~1677-1681) and `::test_clear_tolerates_unimportable_filter_submodules` (docstring ~1617 and inline comment ~1638-1641).

The operative invariant, established by Worker 3's mutation and by nothing else: **`clear()` performs no direct import of the subsystem's submodules, so poisoning either module name cannot reach it.** Keep the preceding clause (the replay is the only site a poisoned `sys.modules` can be reached at all) and the `register_subsystem_clear` mechanism sentence naming the two registered callbacks by symbol. **Drop the "every submodule lookup it makes is best-effort, so …" clause and the `so` that hangs off it** — the lookups it describes target `{orders,filters}.factories` / `{orders,filters}.sets`, which this test does not poison. Do not relocate the clause into these tests; it is already operative and already stated where it belongs, at `tests/orders/test_inputs.py::test_clear_order_input_namespace_tolerates_unimportable_submodules`.

Verify before writing, per side, that the callback's `_safe_import` targets are the `.factories` / `.sets` pair and not the poisoned names: `{orders,filters}/inputs.py`'s `make_set_input_namespace(...)` call args. **If either side's callback does look up a poisoned module, that side keeps its clause and the asymmetry is recorded as factual** — but both were read this pass and neither does. Both twins end up with the same shape, which is what C6 step 16 was for. `::test_clear_tolerates_unimportable_connection_submodule` and `::test_clear_tolerates_unimportable_relay_module` stay byte-identical.

**Step 21 — C9: the ninth finding.** `examples/fakeshop/apps/library/orders.py` module docstring, line 3. `Five ordersets mirror the relation shape` -> `Seven ordersets mirror the relation shape`, and name the two: `PeriodicalOrder` and `IssueOrder` are the keyset-cursor `orderBy:` substrate, which the file's own `PeriodicalOrder` docstring already states — reuse its vocabulary rather than inventing a second telling. Re-derive the count before writing (`grep -c '^class .*Order(OrderSet)'` -> 7). Do not touch the `schema.py` wiring count; eight wirings vs DoD 14's six is D15's spec-side half and Slice 3 owns it.

**Step 22 — C10: the 11 prose `line NN` citations in `tests/orders/`.** Per site, decided:

| Site | Current | Repair |
|---|---|---|
| `test_sets.py` #"the spec lookup at line 341-348" | body comment | drop the coordinate; cite `utils/permissions.py::active_permission_targets` |
| `test_sets.py` #"(skipping line 526)" / #"filter at line 532" / #"early return at line 535" | one docstring, 3 refs | drop all three coordinates; the docstring already quotes the guards verbatim, and `orders/sets.py::OrderSet._apply_orderings` is the one symbol all three now live in |
| `test_sets.py` #"early return at line 571" | docstring | drop the coordinate; same symbol |
| `test_sets.py` #"at line 579" | docstring | drop the coordinate; same symbol |
| `test_factories.py` #"gate (line 159)" | docstring | drop; cite `utils/inputs.py` #"if target is not None and target not in seen:" |
| `test_factories.py` #"gate (line 138)" | docstring | drop; cite `utils/inputs.py` #"if set_cls in seen:" |
| `test_composition.py` #"``AGENTS.md`` line 8 carve-out" | docstring | drop ` line 8`; the docstring already quotes the rule text verbatim, which is self-anchoring. `AGENTS.md` has no headings and no symbols, so a quotation is the only durable form available |
| `test_sets.py` #"per cookbook line 280" | docstring | **leave byte-identical** (cookbook ruling above) |
| `test_factories.py` #"cookbook lines 124-130" | body comment | **leave byte-identical** (cookbook ruling above) |

**Step 23 — C11: the 12 raw `path:NN` citations in `tests/orders/`.** Every one becomes the `path::Symbol` form (gate-enforced, exactly as C7's did) plus a `#"substring"` where the symbol is not itself the target. **The current-home column of Ruling 2's table is the decided target for each**; it was verified against source this pass. Two constraints:

- **The cited coordinate and the cited expression are both wrong at nine of the twelve sites**, so this is a content correction as well as a coordinate one — Worker 2 reads the guard at its new home and restates the expression as it now reads, exactly as the C7 table did (`if not parts` -> `if not core`, `spec` -> `field.spec`). Do not carry a stale expression forward onto a fresh symbol.
- **Three of the twelve assert a sync/async split that no longer exists** (`sets.py:534-535` / `:570-571` / `:578-579` — `apply_sync` and `apply_async` both route through `OrderSet._apply_orderings`, one helper, `if not data:` and `if not expressions:`). Restate what each row now distinguishes, or say plainly that both rows exercise one helper through the two entry points. Worker 2 resolves each `#"substring"` against the named symbol and confirms it is unique inside it before writing; `Covers` is the verb, consistent with C7.

**Step 24 — C12: the 16 in-family bare `Spec Decision N` / `Spec DoD N` citations.** Respell each to the durable `spec-028 Decision N` / `spec-028 DoD N` form, preserving any `step M` / `Layer M` / `(c)` suffix exactly (`Spec Decision 8 step 6` -> `spec-028 Decision 8 step 6`; `Spec DoD 4(c)` -> `spec-028 DoD 4(c)`). Sites: `orders/sets.py` 6, `orders/inputs.py` 5, `utils/inputs.py` 2, `orders/__init__.py` 1, `orders/factories.py` 1, `tests/orders/test_composition.py` 1.

- **The wrapped site is the one that must not be missed.** `orders/sets.py` #"(Spec Decision" at 451-452 breaks across two lines. Respell it **and reflow so the finished citation sits unbroken on one line** — a wrapped `spec-028 Decision 8 step 6` is a citation the next census cannot see, which is the whole defect.
- **`utils/inputs.py`'s two sites are shared substrate serving both set families.** Qualify without re-attributing: the sentence must stay true for the filter family. `spec-028 Decision 8` is the order family's contract, so the correct form names the order family explicitly as the origin of the no-operator-bag shape rather than implying `utils/inputs.py` belongs to `spec-028`. Decide the wording once and use it at both sites.
- **`tests/types/test_relay_interfaces.py` #"Spec Decision 2 (spec-015" stays byte-identical** — it carries its own spec id and is correct.
- Postcondition: `grep -rnE --include='*.py' 'Spec (Decision|DoD) [0-9]'` finds only the `spec-015` site, **and the flattened equivalent finds only the same one**.

---

**Verification the re-pass owes**, on top of every postcondition in `### Verification this slice owes` re-run at the recorded scope:

| Check | Postcondition |
|---|---|
| flattened four-class probe, over **all thirteen** writable paths | `raw-line-citation` and `path-NN-citation` print nothing except the **six** cookbook refs (2 in `tests/orders/`, 4 in `orders/sets.py`), which are named and expected |
| flattened bare-`Spec` probe, tree-wide | exactly **1** occurrence, the `spec-015` site |
| citation gate | `uv run python scripts/check_citations.py` exit 0, count at or above **758** (it must *rise* — every C11 replacement becomes gate-enforced) |
| wrap probe | **0** wrapped `path::Symbol` or `spec-028 …` citations, in every touched file, whitespace-flattened and differenced against the single-line reading |
| zero-executable-change | AST + token identity `SAME` for all thirteen paths, against `git show HEAD:<path>` for the dirty ones and `5c6fdd71` for the three swept into `8a9840dc` |
| layout / lint | `check_trailing_commas.py --check <touched>` exit 0; `ruff format --check` and `ruff check` scoped, both clean |
| churn | `git status --short` shows nothing outside the thirteen plus this artifact, the memory files, and Slice 1's spec + rationale |
| closing census | record `spec-028` / `spec-028 Decision N` / `spec-028 test plan` **after** the pass. That reading, not 67 / 38 / 6, is Slice 3's baseline |

No failability proof, no hot-path number, and no floor run is owed by the re-pass either, on the same ground and subject to the same check: the AST/token identity must still read `SAME` for all thirteen paths. **If any file's executable tokens change, the entitlement lapses and the boundary machinery is owed** — that is the one way this re-pass could quietly acquire an obligation.

### Spec changes made (Worker 1 only)

**No spec edit this pass.** `docs/SPECS/spec-028-orders-0_0_8.md` and its rationale companion are Slice 3's and Slice 3 has not run; nothing Slice 2 landed falsifies a spec sentence. Per-spawn status-line re-verification done: lines 1-6 read as a shipped-state record, the rationale-companion pointer Slice 1 added resolves, and Slice 2 falsified none of it.

Deferral reasons for the boxes left `- [ ]`, per `worker-1.md` `## Final verification job` step 3 — **none is a deferral; all six are re-pass work in this slice**:

- **C5** — un-ticked as an over-tick, not deferred. Step 19.
- **C6c, C9, C10, C11, C12** — new boxes, dispatched to this slice's re-pass. Steps 20-24.

Recorded so the maintainer's diff read and the checklist agree, per Worker 3's request:

- **Three unplanned body-comment fixes are in the diff and no checklist box covers them** — `tests/orders/test_inputs.py::test_normalize_input_value_skips_attrs_with_no_field_spec_entry`, `::test_clear_order_input_namespace_tolerates_unimportable_submodules`, and `tests/test_registry.py::test_clear_tolerates_unimportable_order_submodules`. **Acknowledged and accepted.** Each sits inside a test whose docstring this slice was repairing, each asserted the same retired mechanism as the docstring above it, none touches an assertion, and the plan's step 16 states the governing rule by name ("leaving the docstring right and the comment wrong is a half-fix"). Applying a stated rule to structurally identical sites in the same files is faithful execution. Verified individually against source this pass.

Deferred to `bld-final-028.md` `### Deferred work catalog` (nothing here is code-defect work):

1. **Six upstream-cookbook line refs**, left with the reason under Ruling 2 — 2 in `tests/orders/`, 4 in `orders/sets.py`. Do not re-open without pinning the cookbook.
2. **The tree-wide raw-line-citation population outside this cycle's paths** — corrected inventory at `### Notes for Worker 1` note 7.
3. **The `check_citations.py` gate extension**, note 7's proposal, plus Worker 3's addition: it must also flag the bare `Spec (Decision|DoD|Edge)` form, **and it must match whitespace-flattened** — every miss in this cycle's paperwork, C2's wrapped site and M2's wrapped site alike, was a single-line instrument reading a wrapped citation.
4. **The two-of-four `except ImportError` twins** in `tests/test_registry.py` — maintainer decision, note 6, unchanged by this pass. Now narrower: after step 20 the file carries two accurate twins and two carrying the original false premise.
5. **The DRY existence challenge**, both halves, per Ruling 7 — rows 1-2 as a contract-level maintainer decision, row 3 (`graphql_camel_name`'s unpinned empty-core branch) as a card in its own right.
6. **The banner count is unmaintained by construction**, note 8, unchanged — step 19 makes it accurate and named, not durable.
7. **`8a9840dc` carries three `spec-028` hunks under a `spec-027` commit message**, and `git diff HEAD -- <path>` is empty for those three paths. Maintainer's to resolve; no worker amended, re-staged, or force-pushed anything.
8. **Two plan-text defects, unfixed because their files are fenced or not mine.** Worker 0's plan misquotes `BUILD.md` `### When to run the helper during build` for Worker 3 (L3 — it adds a logic qualifier the rule does not have, which would license a real skip in a future cycle whose `types/` edit does add logic); and `### Partition correction 1`'s M1/M2 measurements are superseded by Rulings 2 and 3.

### Final status

`revision-needed`. Worker 0 dispatches Worker 2 for steps 19-24 against the thirteen-path writable set, then Worker 3, then this pass runs again.

---

## Build report (Worker 2, pass 2)

Steps 19-24 from `### Re-pass steps (Worker 1, final verification)`. All six boxes (C5, C6c, C9, C10, C11, C12) landed and are ticked. **Zero executable statements changed in all sixteen writable paths**, so the zero-boundary entitlement holds — re-derived below on the docstring-stripped-AST instrument against both reference points.

### Files touched

Grounded in `git status --short` (full output under `### Validation run`). Thirteen of the sixteen writable paths were edited this pass; `types/base.py`, `tests/types/test_base.py`, and `tests/orders/test_inputs.py` carry only pass-1 work and were not touched.

- `examples/fakeshop/test_query/test_library_api.py` — **C5 / step 19.** Three comment lines appended to the `Live HTTP order coverage` banner naming both post-ship additions by test name. Count re-derived first: bounds `1738` (banner) to `2484` (`# spec-029`), `^def test_` -> **16**, exactly one `@pytest.mark.parametrize` over four NULLS directions -> **19 rows**. The existing `16 test functions / 19 test rows` line was already correct and is unchanged.
- `tests/test_registry.py` — **C6c / L1 / step 20.** The non-operative "every submodule lookup it makes is best-effort, so …" clause dropped from **both** twins, docstring and inline comment in each (four sites). Replaced with the operative invariant: the replay "imports neither poisoned name". Verified per side before writing that the callback's `_safe_import` targets are the `.factories` / `.sets` pair, not the poisoned `.inputs` / package names (`{orders,filters}/inputs.py`'s `make_set_input_namespace(...)` call args at `orders/inputs.py` 155/158 and `filters/inputs.py` 166/169, both reaching `utils/inputs.py::clear_generated_input_namespace`'s two `_safe_import` calls). Neither side looks up a poisoned module, so no asymmetry is recorded. `::test_clear_tolerates_unimportable_connection_submodule` and `::test_clear_tolerates_unimportable_relay_module` are byte-identical.
- `examples/fakeshop/apps/library/orders.py` — **C9 / step 21.** Module docstring `Five ordersets` -> `Seven ordersets`, naming `PeriodicalOrder` / `IssueOrder` as the keyset-cursor `orderBy:` substrate in the file's own `IssueOrder` vocabulary ("a root `orderBy: {title: ASC}` page mints value cursors fingerprinted to THAT order"). Count re-derived: `grep -c '^class .*Order(OrderSet)'` -> **7** (`BranchOrder`, `ShelfOrder`, `BookOrder`, `LoanOrder`, `PatronOrder`, `PeriodicalOrder`, `IssueOrder`). The paragraph was reflowed to absorb the insert; no `schema.py` wiring count was touched (D15's spec-side half is Slice 3's).
- `tests/orders/test_sets.py` — **C10 + C11 / steps 22-23.** Seven prose `line NN` refs and ten `path:NN` refs retired across nine docstrings and one body comment. Six distinct `path::Symbol` targets, each read at its new home and its expression restated: `orders/sets.py::OrderSet._expand_meta_fields` #"if meta_fields is None:", `utils/permissions.py::extract_branch_value` #"if input_value is None:", `utils/input_values.py::input_field_value`'s dict arm, `utils/input_values.py::iter_active_fields` #"is_inactive_value(input_value" and #"if items is None:", `utils/input_values.py::iter_input_items` #"if isinstance(input_value, dict):", `utils/permissions.py::active_permission_targets` #"else fallback_path(field.python_attr)" (plus the `_field_specs`-population body comment), and `orders/sets.py::OrderSet._apply_orderings` #"if not data:" / #"if not expressions:". The one cookbook ref (#"per cookbook line 280") is byte-identical.
- `tests/orders/test_factories.py` — **C10 + C11 / steps 22-23.** The docstring retargeted to `utils/inputs.py::GeneratedInputArgumentsFactory._ensure_built` #"if set_cls in seen:" with the enqueue-time sibling cited as #"if target is not None and target not in seen:". Its `(line 159)` / `(line 138)` coordinates are gone. The one cookbook ref (#"cookbook lines 124-130") is byte-identical.
- `tests/orders/test_base.py` — **C11 / step 23.** `orders/base.py:82` (a blank line at HEAD) -> `orders/base.py::RelatedOrder.orderset` #"self._set_target(value)", and the body now names the shared delegate `sets_mixins.py::RelatedSetTargetMixin._set_target` that performs the assignment.
- `tests/orders/test_composition.py` — **C10 + C12 / steps 22, 24.** ` line 8` dropped from the `AGENTS.md` carve-out citation (the quotation that follows is self-anchoring); `Spec Decision 5` -> `spec-028 Decision 5`.
- `django_strawberry_framework/orders/sets.py` — **C12 / step 24.** Six sites respelled (2 `DoD 4(c)`, 4 `Decision N`), including the **wrapped** one at 451-452, which is reflowed so `spec-028 Decision 8 step 6` sits unbroken on one line. The four cookbook `line NN` refs are byte-identical.
- `django_strawberry_framework/orders/inputs.py` — **C12-adjacent wrap repair.** No bare `Spec Decision` site here; the wrap probe found a pre-existing **wrapped** `spec-028` / `Decision 9` pair at 364-365, reflowed so the citation sits on one line. See `### Notes for Worker 1` item 1.
- `django_strawberry_framework/orders/base.py` — **C12-adjacent wrap repair.** Same shape: a pre-existing wrapped `per spec-028` / `Decision 2` pair at 33-34, reflowed.
- `django_strawberry_framework/orders/factories.py` — **C12 only.** One site, `Spec Decision 8` -> `spec-028 Decision 8` (line 103). The `Layer 5 of the spec-028 six-layer pipeline` citation is untouched — verified with `git diff HEAD -- <path> | grep 'Layer 5'`, no hit.
- `django_strawberry_framework/orders/__init__.py` — **C12 only.** One site, `Spec Decision 5` -> `spec-028 Decision 5`.
- `django_strawberry_framework/utils/inputs.py` — **C12 only.** Two sites (1708, 1733). Qualified, not re-attributed: both sentences already scope the claim to "the order family" and explicitly contrast the filter family ("The filter family never reaches this branch"; "The filter family appends `_build_logic_fields`"), so adding the `spec-028` token names the order family's contract as the origin and leaves both sentences true for the filter family. One wording decided and used at both sites.

Plus this artifact (six ticks + this report + `Status: built`) and `docs/builder/worker-memory/worker-2-028.md`.

### Tests added or updated

**No test is added, removed, renamed, or re-asserted.** Every edit is comment or docstring text; not one assertion, fixture, or `sys.modules` manipulation changes. The C6c narrowing removes a *claim* from two docstrings and two comments, not a boundary.

### Validation run

Every "before" reading was taken before the first edit, so the deltas below are differences and not guesses.

| Check | Before | After | Verdict |
|---|---|---|---|
| flattened four-class probe over **all sixteen** paths, `raw-line-citation` | 15 (4 cookbook in `orders/sets.py` + 11 in `tests/orders/`) | **6** — `orders/sets.py` 4 + `test_sets.py` 1 + `test_factories.py` 1, all cookbook | pass (exactly the six named refs) |
| same probe, `path-NN-citation` | 12 (`test_sets.py` 10, `test_factories.py` 1, `test_base.py` 1) | **0** | pass |
| same probe, `Test-N-ordinal` | 0 | **0** | pass |
| same probe, `bare-Spec-Decision` | 16 | **0** | pass |
| flattened bare-`Spec (Decision\|DoD\|Edge) N`, **tree-wide** | 17 | **1** — `tests/types/test_relay_interfaces.py` `Spec Decision 2` (`spec-015`, correct) | pass |
| single-line vs flattened bare-`Spec`, tree-wide | 16 vs 17 (the wrapped `orders/sets.py` site) | **1 vs 1** | pass |
| wrap probe (`path::Symbol`, `spec-028 …`, `#"substring"`), 16 paths, flattened differenced against single-line | 2 wrapped `spec-028 Decision N` (`orders/base.py` 33-34, `orders/inputs.py` 364-365) | **0** | pass |
| wrap probe, `spec-028 …`, **tree-wide** | not taken before | **0** | pass |
| `spec-028` census (`.py`, single-line) | 67 | **83** (+16, one per C12 respelling) | pass |
| `spec-028 Decision N` census | 38 | **54** (+14 C12 Decision sites, +2 newly visible from the two reflowed wraps) | pass |
| `spec-028 test plan` census | 6 | **6** | pass |
| `spec-028 DoD N` census (new form) | 0 | **2** | pass |
| all four censuses, flattened | — | **83 / 54 / 6 / 2** — identical to single-line | pass (no wrapped residue) |
| `spec-028[^)]*#"` substring citations, single-line **and** flattened | 0 / 0 | **0 / 0** | pass |
| `uv run python scripts/check_citations.py` | `OK: 758 citations resolve (681 in 422 .py files, 77 in KANBAN.md)`, exit 0 | `OK: 772 citations resolve (695 in 422 .py files, 77 in KANBAN.md)`, exit 0 | pass (**rose** by 14) |
| docstring-stripped `ast.dump` identity, all 16 paths, vs `HEAD` **and** vs `5c6fdd71` for the three swept into `8a9840dc` | 19 readings, `MISMATCHES: 0` | 19 readings, `MISMATCHES: 0` | pass |
| `uv run python scripts/check_trailing_commas.py --check <13 touched>` | — | exit 0 | pass |
| `uv run ruff format <13 touched>` | — | `13 files left unchanged` | pass |
| `uv run ruff check --fix <the same 13>` | — | `All checks passed!` | pass |
| `uv run python -m compileall -q <the same 13>` | — | exit 0 | pass |
| `uv run pytest tests/orders/ tests/test_registry.py --no-cov --collect-only -q` | — | `229 tests collected`, 0 errors | pass |
| `uv run pytest examples/fakeshop/test_query/test_library_api.py --no-cov --collect-only -q` | — | `197 tests collected`, 0 errors | pass |

`ruff` was run **scoped to the thirteen files this pass touched, never `.`**, and never with `--fix` on anything outside them. No `pytest` was run as routine slice work; the two invocations above are `--collect-only` and exist solely because a mangled triple-quote is the one way a prose-only edit breaks something. **No `--cov*` flag was passed in any command this pass.**

**`git status --short` after both ruff invocations:**

```
 M django_strawberry_framework/orders/__init__.py
 M django_strawberry_framework/orders/base.py
 M django_strawberry_framework/orders/factories.py
 M django_strawberry_framework/orders/inputs.py
 M django_strawberry_framework/orders/sets.py
 M django_strawberry_framework/types/base.py
 M django_strawberry_framework/utils/inputs.py
 M docs/SPECS/spec-028-orders-0_0_8.md
 M docs/builder/build-027-filters-0_0_8.md
 M examples/fakeshop/apps/library/orders.py
 M examples/fakeshop/test_query/test_library_api.py
 M tests/orders/test_base.py
 M tests/orders/test_composition.py
 M tests/orders/test_factories.py
 M tests/orders/test_inputs.py
 M tests/orders/test_sets.py
 M tests/test_registry.py
?? docs/SPECS/appx/spec-028-orders-0_0_8-rationale.md
?? docs/builder/bld-slice-1-028-rationale_extraction.md
?? docs/builder/bld-slice-2-028-citation_and_provenance_rot.md
?? docs/builder/build-028-orders-0_0_8.md
```

Every entry is a Slice-2 writable path, Slice 1's spec + rationale, or a cycle artifact — **except one, which is a stop-and-report, not a revert:**

- **`docs/builder/build-027-filters-0_0_8.md` is modified and no pass of this cycle touched it.** It was untracked at this cycle's pre-flight, was swept into `8a9840dc`, and is now tracked-and-dirty with **21 inserted lines** added by a concurrent session. Left exactly as found. Its content is a live cross-cycle ownership collision — see `### Notes for Worker 1` item 2, which is the reason this is reported rather than shrugged at.
- Three tracked concurrent-writable binaries/generated files (`examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`) are all clean; this pass planned no edit to any of them and observed no churn.
- No `027` hunk was reverted, tidied, or reformatted in any file; no `git checkout` / `restore` / `stash` / `worktree` was run at any point.

### Failability proofs

`None; this pass introduced no new boundary.`

The entitlement is proved, not asserted: docstring-stripped `ast.dump` identity reads `SAME` for **all sixteen** writable paths, against `git show HEAD:<path>` for the thirteen dirty-vs-HEAD and additionally against `5c6fdd71` for the three swept into `8a9840dc` (where the HEAD reading is trivially true and proves nothing on its own). Pristine copies were obtained read-only via `git show` into a scratch path **outside** the repo; no `git checkout`, `restore`, or `stash` was involved. Nineteen readings, `MISMATCHES: 0`, before and after this pass. No fail-open shape can have landed, because a fail-open expression is an executable expression and the executable token stream is unchanged everywhere.

### Hot-path budget

`Not applicable; plan declares no hot path.`

### Floor verification

`Not applicable; plan declares floor-verification scope none.`

### Implementation notes

- **`Covers` throughout, matching C7's seven docstrings.** `Closes ``path:NN``` no longer parses once the coordinate is a symbol, and mixing verbs across one file would read as two conventions. Every `"""Closes` in `tests/orders/` is gone (`grep -rn '"""Closes' tests/orders/` -> no output).
- **C11's targets were re-derived per test, not per Ruling-2 row.** Ruling 2's table maps `sets.py:269`, `:270-271`, `:317-318`, `:327-329`, `:330-331` to one current home (`utils/input_values.py::iter_input_items` via `orders/inputs.py::normalize_input_value`). Read against source, those five coordinates belong to **two** different delegate chains — `OrderSet._extract_branch_value` -> `utils/permissions.py::extract_branch_value` -> `utils/input_values.py::input_field_value`, and `OrderSet._active_permission_field_paths` -> `::_active_permission_targets` -> `utils/permissions.py::active_permission_targets` -> `utils/input_values.py::iter_active_fields` -> `::iter_input_items` — and neither runs through `normalize_input_value`. Step 23 requires reading the guard at its new home and restating it, so each site cites the symbol that actually holds its guard. Same module family as the ruling named; only the per-site symbol is finer. Recorded as small drift under `### Notes for Worker 1` item 3.
- **Three body-level expression corrections came with the docstring repairs**, on the "leaving the docstring right and the comment wrong is a half-fix" rule the plan's step 16 states by name: `tests/orders/test_factories.py`'s **section banner** and closing docstring sentence both said `if os_class in seen: continue` (the parameter is `set_cls`; `grep -rn 'os_class' --include='*.py' .` now returns only an unrelated `tests/test_views.py` test name), and `tests/orders/test_sets.py`'s `_expand_meta_fields` docstring said the read is `getattr(meta, "fields", None)` when at HEAD it is `read_set_meta_fields(meta)`.
- **The two wrap repairs were not in the step list and are postcondition work, not scope creep.** The re-pass verification table requires "**0** wrapped `path::Symbol` or `spec-028 …` citations, in every touched file". The probe found two, both pre-existing and both in files this cycle edits. Reflowed only; the citation text is unchanged.
- **The C6c replacement states the operative invariant rather than merely deleting the clause.** "…and it imports neither poisoned name" is what Worker 3's mutation established and what makes the following "therefore cannot make `clear()` raise" sound; a bare `therefore` would have left the docstring's conclusion resting on the clause that was just removed.
- **Edits were grouped by file** so each scoped `ruff` invocation stayed small, per the plan's discretion item.

### Notes for Worker 3

- **Read the three swept files by present state, not by diff.** `git diff HEAD -- <path>` is empty-of-pass-1 for `tests/types/test_base.py`, `tests/test_registry.py`, and `examples/fakeshop/test_query/test_library_api.py`; use `git diff 5c6fdd71 -- <path>` or read the file.
- **The probes are reproducible.** All three (four-class census, wrap differencer, AST identity) were run as standalone scripts outside the repo; each is reconstructable from the commands and file lists quoted above, and the wrap differencer is the only instrument that can see a wrapped citation — the single-line reading of the tree-wide bare-`Spec` population was 16 and the true figure was 17.
- **The `raw-line-citation` class does not reach zero and must not.** Six cookbook refs survive by Ruling 2: 4 in `orders/sets.py` (#"lines 30-38", #"lines 265-285", #"line 279-280", #"lines 115-170") and 2 in `tests/orders/` (`test_sets.py` #"per cookbook line 280", `test_factories.py` #"cookbook lines 124-130"). All six are byte-identical to HEAD.
- **`git status` carries one file no pass of this cycle touched** (`docs/builder/build-027-filters-0_0_8.md`). Do not read it as this pass's churn, and do not revert it.

### Notes for Worker 1 (spec reconciliation)

Written on disk because a return message reaches nobody. Items 1-3 concern this slice's diff; items 4-6 are for the maintainer, Slice 3, or the deferred-work catalog.

1. **Two wrapped `spec-028 Decision N` citations existed at HEAD and no census in this cycle ever saw them — including the "confirmed" 38.** `django_strawberry_framework/orders/base.py` 33-34 read `per spec-028` / newline / `Decision 2.`, and `orders/inputs.py` 364-365 read `raise (spec-028` / newline / `Decision 9).`. Both were invisible to every single-line `spec-028 Decision [0-9]+` reading, which is why five independent passes agreed on 38: **the instrument was shared, so the agreement measured the instrument, not the population.** The flattened figure at pass-2 entry was therefore **40**, not 38. Both are reflowed, and the closing census is single-line-equal-to-flattened at every class. Recommended replacement for `### Ruling 8`'s wording — no anchor quote needed beyond the heading, since the numbers are the whole content:
   - current: "Re-derived once more by this pass, a fifth independent measurement: `spec-028` **67**, `spec-028 Decision [0-9]+` **38**, `spec-028 test plan` **6**, `spec-028[^)]*#"` **0**."
   - replacement: "Re-derived once more by this pass, a fifth independent measurement, **all four on the whitespace-flattened probe**: `spec-028` **67**, `spec-028 Decision [0-9]+` **40** (two sites wrapped across two source lines and invisible to every single-line reading this cycle took, including the four that agreed on 38), `spec-028 test plan` **6**, `spec-028[^)]*#"` **0**."
2. **CROSS-CYCLE COLLISION, live right now — a concurrent `spec-027` cohort has declared four of this slice's writable files as its own, and has already written its partition to disk.** `docs/builder/build-027-filters-0_0_8.md` gained a section `### Catalog-discharge cohorts (added 2026-08-20, post-commit 8a9840dc)` that declares cohorts B and C over, among others, **`django_strawberry_framework/orders/sets.py`**, **`orders/__init__.py`**, **`orders/factories.py`**, and **`django_strawberry_framework/utils/inputs.py`** — all four in this slice's sixteen, all four edited by this pass for C12. That section explicitly lists the files it treats as blocked-because-028-has-them (`types/base.py`, `tests/test_registry.py`, `tests/orders/test_inputs.py`, `orders/base.py`, `orders/inputs.py`, `library/orders.py`, `test_library_api.py`, the spec) — and those four are **not** on that list, because they were still clean when it was written. Its cohort C is scoped to "item 5: bare `Decision N`", the same defect family as C12. **This is the one thing in this report that cannot wait for the integration pass**: two cycles now believe they own the same four files for the same class of edit, and the 027 plan is not a document any Worker 2 may edit. Escalate to the maintainer.
3. **Small drift, C11's targets (already in `### Implementation notes`, repeated here because this is the louder channel).** Ruling 2's current-home column gives one symbol for five cited coordinates that belong to two distinct delegate chains; each site now cites the symbol that actually holds its guard, inside the same `utils/` modules the ruling named. If you prefer the coarser attribution, the change is one line per docstring.
4. **Slice 3's baseline is `spec-028` 83 / `spec-028 Decision N` 54 / `spec-028 test plan` 6, plus a new `spec-028 DoD N` 2 class.** Single-line and flattened agree at every class. The arithmetic is re-derivable: 67 + 16 C12 respellings = 83; 38 + 14 C12 `Decision` sites + 2 newly-visible reflowed wraps = 54; the 2 remaining C12 sites are the `DoD 4(c)` pair in `orders/sets.py`, which is why a **fourth** census class now exists that no prior pass tracked. **Slice 3 must protect the `### DoD` / definition-of-done anchor as well as the `### Decision N` and `## Test plan` headings** — the note-3 obligation from the plan now covers a form it did not name.
5. **A much wider bare-`Decision N` population exists in the writable files and C12 did not close it, by design.** C12's population was the `Spec (Decision|DoD) N` spelling. The unprefixed `Decision N` form (no `Spec`, no `spec-NNN`) survives at `orders/factories.py:9` (`Layer 5 + Decision 4 H1`), `utils/inputs.py:1300` (`the Decision 9 lifecycle clause`), and across `types/base.py`, `tests/types/test_base.py`, `tests/orders/test_inputs.py`, and `test_library_api.py` — mostly naming **other cards'** decisions (`spec-030`, `spec-032`, `spec-033`). It is out of C12's decided population and re-scoping it is a plan-level call, not a wording one, so this pass left every one alone. It is also exactly what the concurrent 027 cohort C intends to measure (item 2), which makes the scope question urgent rather than academic.
6. **Two review-item ids for other cards sit in a file this slice edited.** `django_strawberry_framework/utils/inputs.py` carries `spec-039 P2` and `spec-040 D6` (3 occurrences) — the identical defect class as C1's `(spec-028 N3)`, but claims about two cards this cycle never verified. Left alone on the same ground as the connection and relay registry twins. Worth a bullet in `bld-final-028.md`'s `### Deferred work catalog`.

### Late-breaking working-tree event, recorded after this pass's checks closed

Between the pass's `git status` reading and its final re-verification, the concurrent `spec-027`
cohorts started writing. Item 2 of the notes above is no longer a declared intent — **it is
happening.** Read this before reviewing:

- **Six new dirty paths appeared, none in this slice's sixteen:** `consumers.py`, `routers.py`,
  `filters/factories.py`, `types/finalizer.py`, `types/relay.py` (their cohort A) and
  `docs/SPECS/spec-055-search_fields-0_1_2.md` (their cohort D). No collision there.
- **`django_strawberry_framework/orders/sets.py` — a file in BOTH partitions — has been edited by
  that session, and the edit rewrites the four upstream-cookbook `line NN` refs that Ruling 2
  ordered to stay byte-identical.** The flattened `raw-line-citation` reading over the sixteen paths
  fell from **6** to **2** without any action by this pass; the two survivors are the
  `tests/orders/` cookbook pair, still byte-identical as ruled. Ruling 2's cookbook carve-out and
  its deferred-work entry ("six cookbook line refs, left with reason") are therefore **already
  overtaken by events** for four of the six, by a cycle that never saw the ruling.
- **This pass's own work in that file is intact and was re-verified after their edit:** all six C12
  respellings are present (`orders/sets.py` 13, 19, 121, 321, 455, 464), the reflowed
  `spec-028 Decision 8 step 6` still sits unbroken on one line, and the file still reads
  docstring-stripped-AST `SAME` — so their hunks are prose-only too and nothing of either cycle's
  work was lost.
- **Nothing was reverted, reformatted, or re-staged.** Per `AGENTS.md` rule 34 this is
  concurrent work, and per `worker-2.md` step 6 unexpected churn is a stop-and-report.
- **All postconditions re-run after their edit still hold:** `check_citations.py`
  `OK: 772 citations resolve`, exit 0; wrap probe 0; flattened bare-`Spec` tree-wide 1
  (the `spec-015` site); AST identity `MISMATCHES: 0` across all sixteen.

The maintainer decision this needs is narrow: **which cycle owns `orders/sets.py`,
`orders/__init__.py`, `orders/factories.py`, and `utils/inputs.py`** — and whether Ruling 2's
cookbook carve-out survives the 027 cohort's contrary treatment of the same four refs.

---

## Review (Worker 3, pass 2)

Scope: **steps 19-24 only** — C5 (re-opened), C6c, C9, C10, C11, C12 — plus the standing
whole-diff properties. C1-C8 landed in pass 1, were reviewed there, and were confirmed at final
verification; nothing below re-litigates them.

**Every population in this section is measured on a whitespace-flattened probe as well as a
single-line one, and I say when they disagree.** They disagree in exactly one place, and it is a
finding (M1). The instruments are three standalone scripts run from a scratch path outside the
repo: an AST+token identity differencer, a flattened/single-line census differencer, and a wrap
differencer. No `git stash` / `checkout` / `restore` / `worktree` was run at any point; pristine
references were obtained read-only with `git show`.

### The tree moved under this review, twice, and the attribution is clean in both directions

This must be read before any number below. A concurrent `spec-027` cohort is writing this same
tree and its declared partition overlaps four of Slice 2's sixteen paths for the same defect
family. Attribution, established independently of Worker 2's report:

- **`orders/sets.py` — the four upstream-cookbook `line NN` refs Ruling 2 ordered left
  byte-identical are GONE, and the delta is wholly the other cohort's.** Proof, three ways:
  `git show HEAD:django_strawberry_framework/orders/sets.py | grep -iE '\blines? [0-9]'` returns
  all four (94, 179, 256, 312) and the working tree returns none; the replacement text converts
  them to `django_graphene_filters/orderset.py::Symbol` + `#"substring"` form, which is the
  treatment Ruling 2 explicitly declined; and the other cycle's own artifact
  `docs/builder/bld-slice-7-027-raw_line_refs.md` ticks all four as cohort B's work
  (`- [x] orders/sets.py #"the cookbook lines 30-38 behavior"`, …, plus a census-added fourth at
  256) while recording that it did **not** build Slice 2's `Spec Decision N` / `Spec DoD 4(c)`
  hunks in the same file and verified they coexist. **Nothing of Slice 2's was lost:** all six C12
  respellings are present (13, 19, 121, 321, 455, 464), the reflowed `spec-028 Decision 8 step 6`
  sits unbroken on one line, and the file reads AST- and token-identical to HEAD.
- **`orders/__init__.py` (+3) and `utils/inputs.py` (+2) gained cohort-C hunks AFTER Worker 2's
  report closed.** File mtimes 10:39:31 and 10:39:57 against the artifact's 10:35:06; the voice is
  the dual `spec-027 / spec-028 Decision N` attribution no `028` worker would write; and cohort C's
  declared partition names both files for catalog item 5, the unprefixed bare-`Decision N` class.
  Worker 2's C12 sites in both files survive intact. **Confirmed from that cohort's own artifact,
  which appeared during this review:** `docs/builder/bld-slice-8-027-decision_attribution.md`
  records its edits as `orders/__init__.py` lines 5 / 32 / 77 and `utils/inputs.py` lines 400 /
  1441, and records Slice 2's `orders/__init__.py:60` and `utils/inputs.py:1708` / `:1733` as the
  028 session's, untouched by it. Both cycles' accounts agree line-for-line and neither overlaps
  the other's sites.

**Ruling 2's cookbook postcondition no longer describes the tree, and that is a record to correct,
not a builder to fault.** It says "exactly the 6 named cookbook refs remain"; the tree now holds
**2** (`tests/orders/test_sets.py` #"per cookbook line 280", `tests/orders/test_factories.py`
#"cookbook lines 124-130"), both byte-identical to `5c6fdd71` as ruled. The missing four are the
`orders/sets.py` set above, removed by a cycle that never saw the ruling. See R1.

**Nothing of the other cohort's was reverted, reformatted, or "reconciled" by this pass**, in any
file. Out of scope and untouched: `consumers.py`, `routers.py`, `filters/factories.py`,
`types/finalizer.py`, `types/relay.py`, `mutations/{fields,resolvers,sets}.py`,
`optimizer/extension.py`, `rest_framework/{sets,resolvers,serializer_converter}.py`,
`test_products_api.py`, `docs/SPECS/spec-055-search_fields-0_1_2.md`, and every
`docs/builder/*-027*.md`.

### Independent re-derivations

Worker 2's numbers were re-measured, not read. Every command below was run by this pass.

| Claim | Worker 2 | This pass | Verdict |
|---|---|---|---|
| zero executable change, all 16 paths | 19 readings, `MISMATCHES: 0` (docstring-stripped `ast.dump`) | **38 readings, `MISMATCHES: 0`** — two instruments (docstring-stripped `ast.dump` **and** a token stream with statement-position strings collapsed and every other literal kept verbatim), vs `git show HEAD:<path>` for all 16 and additionally vs `5c6fdd71` for the three swept into `8a9840dc` | **confirmed, on a second instrument** |
| C5 banner bounds / counts | 1738 -> 2484, `^def test_` 16, one `parametrize` x4 -> 19 rows | **16 functions / 19 rows re-derived by AST structure**, not by grep: module-level `test_*` nodes whose earliest decorator-or-def line falls in [1738, 2484) -> 16; exactly one `@pytest.mark.parametrize` with 4 argvalues -> 19 | **confirmed by structure** |
| C9's seven ordersets | 7 | **7** — `BranchOrder` 31, `ShelfOrder` 85, `BookOrder` 96, `LoanOrder` 135, `PatronOrder` 146, `PeriodicalOrder` 156, `IssueOrder` 164 | **confirmed** |
| C10: prose `line NN` in `tests/orders/` | 11 -> 2 (cookbook) | **2**, single-line and flattened, both cookbook, both byte-identical to `5c6fdd71` | **confirmed** |
| C11: raw `path:NN` in the 16 | 12 -> 0 | **0**, single-line and flattened | **confirmed** |
| C12: bare `Spec (Decision\|DoD\|Edge) N` | tree-wide 17 -> 1 | **1**, and single-line == flattened: `tests/types/test_relay_interfaces.py:371` (`spec-015`, out of family, byte-identical) | **confirmed** |
| closing census `spec-028` / `Decision N` / `DoD N` / `test plan` | 83 / 54 / 6 / 2 | **83 / 54 / 6 / 2 reproduced on my first reading; 88 / 59 / 6 / 2 on my last** — the +5 is cohort C's, attributed per file above | **confirmed as measured, then superseded by a concurrent writer.** See R2 |
| `spec-028[^)]*#"` substring citations | 0 / 0 | **0 / 0** | **confirmed** |
| citation gate | `OK: 772 …`, exit 0 | `OK: 779 citations resolve (702 in 422 .py files, 77 in KANBAN.md)`, **exit 0** | **gated on exit code.** See R3 |
| `check_trailing_commas.py --check` (16) | exit 0 | **exit 0** | confirmed |
| `ruff format --check` / `ruff check` (16, read-only, never `.`, never `--fix`) | `13 files left unchanged` / `All checks passed!` | **`16 files already formatted`** / **`All checks passed!`** | confirmed |
| no line past the 110-column grace in this pass's edits | implied | **confirmed** — the 18 lines over 110 in the sixteen are all pre-existing and none is in a pass-2 hunk | confirmed |
| public surface | — | `git diff HEAD -- django_strawberry_framework/__init__.py` **empty** | confirmed |
| wrap probe over the 16 | **0** | **2 wrapped `::Symbol #"substring"` citations, both written by this pass** | **REFUTED — M1** |

**Zero executable change carries the boundary entitlement, and I re-derived it rather than
accepting it.** For the four files both cycles wrote, `SAME` covers the union of both cycles'
hunks, which proves each part prose-only as well as the whole. Because no executable token changed
anywhere, `### Failability proofs` reading `None; this pass introduced no new boundary.` is the
correct content, no fail-open shape can have landed (a fail-open shape is an executable
expression), and **the mandatory re-run floor is legally empty rather than skipped** — there is no
boundary in the diff that meets it. Saying that out loud is the point; an empty re-run set left
silent is indistinguishable from a reviewer who did not look.

### C10 / C11's substantive half: the restated expressions, checked against the code

Coordinates that resolve while describing the wrong thing are the same defect wearing a valid
coordinate, and this cycle already caught one (`name: DESC` vs `city: DESC` in C2). So I resolved
every new citation by hand rather than trusting the gate, which is `path::Symbol`-only and
line-scoped: for each `path::Symbol #"substring"` I parsed the target, extracted that symbol's
source segment, and asserted the substring occurs **exactly once inside it**.

| Citation | Substring resolves inside the named symbol | Restated expression true of the code |
|---|---|---|
| `orders/sets.py::OrderSet._expand_meta_fields` #"if meta_fields is None:" | unique | yes — and the docstring's `read_set_meta_fields(meta)` correction is right; `getattr(meta, "fields", None)` is gone |
| `utils/permissions.py::extract_branch_value` #"if input_value is None:" | unique | yes |
| `utils/input_values.py::input_field_value` (dict arm) | symbol resolves; the arm's own #"if isinstance(input_value, dict):" is quoted in the body | yes |
| `utils/input_values.py::iter_active_fields` #"is_inactive_value(input_value" | unique | yes |
| `utils/input_values.py::iter_active_fields` #"if items is None:" | unique | yes |
| `utils/input_values.py::iter_input_items` #"if isinstance(input_value, dict):" | unique | yes |
| `utils/permissions.py::active_permission_targets` #"else fallback_path(field.python_attr)" | unique | yes — and the `field.spec is None` restatement is correct |
| `orders/sets.py::OrderSet._apply_orderings` #"if not data:" / #"if not expressions:" | each unique | yes — and the three rows that used to assert a sync/async split now say plainly that both entry points reach one shared helper, which is what the code does |
| `utils/inputs.py::GeneratedInputArgumentsFactory._ensure_built` #"if set_cls in seen:" (pop-time) and #"if target is not None and target not in seen:" (enqueue-time) | both unique, both inside `_ensure_built` (1660 and 1687; symbol opens at 1647) | yes — and the `os_class` -> `set_cls` correction in the section banner and the docstring is right: `grep -rn 'os_class' --include='*.py' .` now finds only an unrelated `tests/test_views.py` test name |
| `orders/base.py::RelatedOrder.orderset` #"self._set_target(value)" | 1 occurrence in the file; it lives in the `@orderset.setter` half of the property pair, which the substring is what disambiguates | yes — the setter body is exactly `self._set_target(value)`, and `sets_mixins.py::RelatedSetTargetMixin._set_target` is where the assignment happens |

Worker 2's finer-than-the-ruling attribution (`### Implementation notes`, C11 targets re-derived per
test rather than per Ruling-2 row) is **correct and is an improvement, not drift.** Ruling 2 mapped
`sets.py:269`, `:270-271`, `:317-318`, `:327-329`, `:330-331` to one home via
`normalize_input_value`; traced against source those five belong to two distinct delegate chains
(`_extract_branch_value` -> `extract_branch_value` -> `input_field_value`, and
`_active_permission_field_paths` -> `active_permission_targets` -> `iter_active_fields` ->
`iter_input_items`) and neither runs through `normalize_input_value`. Each site now cites the symbol
that actually holds its guard. Step 23 required exactly that reading.

### C6b, C6c, and the two fenced twins

- **C6c landed in both twins, docstring and inline comment in each (four sites).** The two inline
  comments are now byte-identical and the two docstrings differ only in the family words and the
  named callbacks — one story, which is what C6 step 16 was for.
- **`::test_clear_tolerates_unimportable_connection_submodule` and
  `::test_clear_tolerates_unimportable_relay_module` are byte-identical.** The pass-2 diff of
  `tests/test_registry.py` carries exactly four hunks, at 1620, 1636, 1661 and 1678; both fenced
  twins begin below 1697. **Worker 2 did not touch them.**
- **C6b is not re-opened.** Its record carries the anchor count, the mutation, the failing node id,
  `0` collection errors and a `cmp`-proved revert; Worker 1 audited it; this pass adds nothing.
- **One accuracy defect in the C6c replacement, measured with a temp test — L4 below.**

### High:

None.

### Medium:

#### M1 — two of C11's own new citations wrap across two source lines, and the build report reports the wrap probe as 0

`tests/orders/test_sets.py:657-658` and `tests/orders/test_factories.py:371-372`.

```tests/orders/test_sets.py:657:658
    """Covers ``utils/permissions.py::active_permission_targets``
    #"else fallback_path(field.python_attr)" -- the defensive fallback.
```

```tests/orders/test_factories.py:371:372
    """Covers ``utils/inputs.py::GeneratedInputArgumentsFactory._ensure_built``
    #"if set_cls in seen:" -- the pop-time skip.
```

**Why it matters, and why it is not a style note.** Worker 1's `### Re-pass steps` opens with a
standing constraint that is explicitly *not* discretionary: "No `path::Symbol` or `#"substring"`
citation wraps across two source lines (the wrap is what turned M2's population invisible and C2's
site ungreppable — it is the defect this slice exists to retire, not a style note)." The plan's
`### Implementation discretion items` says the same thing in the same words. And the re-pass
verification table sets the postcondition at **0**; `### Validation run` reports `0` and `pass`.
Both readings are wrong. The failure mode is the one this cycle has now hit four times: Worker 2's
wrap differencer differenced `path::Symbol`, `spec-028 …` and `#"substring"` **as separate forms**,
each of which is intact on its own line here — what wraps is the **join** between the symbol and
its anchor, so an instrument that never probes `::Symbol` *followed by* `#"` cannot see it. The
population reported was the instrument's, not the tree's. My differencer over the sixteen paths
prints exactly these two and nothing else (`[Symbol #"sub"]` single=8 flat=9 in `test_sets.py`,
single=0 flat=1 in `test_factories.py`).

The concrete loss: a line-scoped reader — `scripts/check_citations.py`, and any future census of
which citations carry a substring anchor — sees a bare `path::Symbol` citation at these two sites
and no anchor. My own by-hand resolver logged `utils/permissions.py::active_permission_targets`
twice, once "symbol only" and once with its substring, for exactly this reason. The gate still
exits 0 because the symbol half is intact, which is precisely why nothing catches it.

**Recommended change**, with both line lengths measured so the 110-column grace is not a guess.
Keep the citation whole on the opening line and move the trailing gloss into the docstring body:

- `tests/orders/test_sets.py:657` ->
  `    """Covers ``utils/permissions.py::active_permission_targets`` #"else fallback_path(field.python_attr)".`
  = **106 columns**. The `-- the defensive fallback` gloss folds into the paragraph below, which
  already says it.
- `tests/orders/test_factories.py:371` ->
  `    """Covers ``utils/inputs.py::GeneratedInputArgumentsFactory._ensure_built`` #"if set_cls in seen:".`
  = **103 columns**. Same for `-- the pop-time skip`, which the section banner two lines above
  already states.

Then correct the pass-2 `### Validation run` wrap-probe row, and re-run the differencer in the form
that can see this class: difference `::[\w.]+``? #"` (and `[\w./]+\.py``? #"`) flattened against
single-line, not only the three forms already probed.

**Test expectation:** none; no behavior is affected. The postcondition is `0` wrapped-only
occurrences of every citation form over all sixteen paths, single-line differenced against
flattened.

### Low:

#### L4 — C6c's replacement claim is state-dependent, and the clause it replaced is the guard that holds in the other state

`tests/test_registry.py:1663-1665` (order twin) and `:1622-1624` (filter twin), plus both inline
comments at `:1678-1680` and `:1636-1638`.

The new text says the replay "imports neither poisoned name. Poisoning the order modules (done
here) therefore cannot make `clear()` raise", and the comment says "the replayed callbacks look up
neither poisoned name, so **no step of the teardown path can raise**."

The first half is literally true: the replayed callback `_safe_import`s
`django_strawberry_framework.orders.{factories,sets}`, and the test poisons `…orders.inputs` and
`…orders`. But **both lookup targets are submodules OF the poisoned package**, and
`orders.factories` is imported lazily from exactly one site — a function-local
`from ..orders.factories import OrderArgumentsFactory` inside `types/finalizer.py::_bind_ordersets`.
When it is not already in `sys.modules`, `importlib` must resolve the parent, the parent is `None`,
and the import raises — so `utils/inputs.py::_safe_import`'s best-effort swallow is what keeps
`clear()` quiet in that state, which is the clause C6c removed.

Measured, not reasoned, with a temp test (disposition below):

- cold `orders.factories` + poisoned parent -> `_safe_import(...)` returns `None`: **the
  best-effort skip fires.**
- warm `orders.factories` + poisoned parent -> returns the class: the poisoned parent is never
  consulted.
- and in a `pytest tests/test_registry.py` session, `django_strawberry_framework.orders` is not
  loaded at all at that point, so the twin's own reachability is session-dependent too.

**The two families are symmetric** — `filters.factories` is likewise imported only from
`types/finalizer.py` — so Worker 1's paired-repair constraint is untouched and no asymmetry needs
recording. This is Worker 1's step-20 escape clause arriving one level down than the pass checked:
the callback does not look up a poisoned *module*, but it looks up submodules of a poisoned
*package*.

**Recommended change** (Worker 1's call, escalated below rather than dispatched): keep the
narrowing, and replace the absolute conclusion with the operative one — "…and it imports neither
poisoned name directly; the two submodule lookups it does make are best-effort, so neither the
poisoned package nor the poisoned `inputs` module can make `clear()` raise." That states both the
invariant the mutation established **and** the guard that carries the cold-module case, without
restoring the over-broad clause L1 objected to. Alternatively keep the current text and record the
state-dependency in the artifact. What is not right is the current absolute "no step of the
teardown path can raise", because a measurable state exists in which one step does raise and is
swallowed.

#### L5 — step 19's second instruction was neither performed nor deferred, and it conflicts with `ARTIFACT.md`

Step 19 ends: "**Also correct the build report's two false sentences** — the `### Validation run`
C5 row's 'both named in the new banner' and `### Implementation notes`' 'a first line attributing
the two post-ship additions'". Both sentences are still there verbatim (this file's lines 567 and
633) and the pass-2 report does not mention the instruction.

**Worker 2 was most likely right not to do it** — `ARTIFACT.md` `## Re-pass sections` says "never
edit prior entries", so the instruction asks for something the artifact contract forbids — but a
conflicting instruction is discharged by recording the conflict, not by silence. The substance is
already safe: my pass-1 L2 and Worker 1's Ruling 1 both name those two sentences as false, so a
linear reader is corrected within the same document. Recommended change: one bullet in the next
build report naming the conflict and stating that the correction lives in Ruling 1, or Worker 1
settles which document wins. No source change.

#### L6 — C9's docstring attributes the `orderBy: {title: ASC}` gloss to both new ordersets, and `PeriodicalOrder` has no `title`

`examples/fakeshop/apps/library/orders.py:3-8`: "``PeriodicalOrder`` and ``IssueOrder`` are the
keyset-cursor ``orderBy:`` substrate, where a root ``orderBy: {title: ASC}`` page mints value
cursors fingerprinted to THAT order."

The vocabulary is the file's own — lifted from `IssueOrder`'s docstring, exactly as step 21 asked —
and the pairing is defensible (`PeriodicalOrder` is the related target `IssueOrder.periodical`
reaches, so the pair is the substrate). But the `title: ASC` clause is `IssueOrder`'s alone:
`PeriodicalOrder.Meta.fields` is `["id", "name"]`, and `PeriodicalOrder`'s own docstring claims
only "the related target for ``IssueOrder.periodical``". A reader checking the pair against the
classes finds the example does not apply to one of them.

**Recommended change:** attribute the clause, e.g. "…are the keyset-cursor ``orderBy:`` substrate:
a root ``orderBy: {title: ASC}`` page over ``IssueOrder`` mints value cursors fingerprinted to THAT
order, and ``PeriodicalOrder`` is the related target its ``periodical`` order reaches." Not
blocking; recorded so the next reader does not re-derive it. The count itself is right (7).

### DRY findings

- **No new code, so no new duplication.** This pass changes zero executable tokens; there is no
  helper, constant, branch or literal to consolidate. The static helper's repeated-string-literal
  evidence would be identical to pass 1's by construction.
- **The C6c repair is deliberately one story across two twins, not duplication.** The two inline
  comments are byte-identical and the docstrings differ only where the families differ. That is the
  shape Ruling 5 ordered and the right one; flagging it would be flagging the fix.
- **Observation, no action: `OrderSet._apply_orderings`'s two guards are each now pinned twice over
  one implementation**, once through `apply_sync` and once through `apply_async`, because the
  sync/async split collapsed into one helper. The pairs are not redundant — they pin that both
  entry points route through the shared helper, and Worker 2's docstrings now say so explicitly
  rather than implying two copies of the guard. Recorded because it is the **same family** as the
  deferred existence challenge (a contract pinned N times over a single-sited implementation): if
  the maintainer takes up Ruling 7's rows 1-2, this pair belongs in the same look, not in a
  separate one.
- **The deferred existence challenge is recorded well enough that the next reader cannot re-fight
  it, and `graphql_camel_name` is flagged.** Ruling 7 carries the reason it is not this slice's
  (every resolution changes executable statements and forfeits the zero-boundary entitlement; both
  halves sit outside the writable set), the reason it is not the integration pass's, the precedent
  (D13's family-neutral single-siting), and who owns the delete call. `### Spec changes made`
  item 5 routes both halves to `bld-final-028.md` `### Deferred work catalog`, with row 3 —
  `utils/strings.py::graphql_camel_name` #"if not core:", no family-neutral pin, coverage riding
  two family aliases — named as a card in its own right. **Confirmed adequate; I do not reopen the
  deferral.**

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` is **empty**. `__all__` and the
re-export list are unchanged; no new public export. Consistent with a pass that changes zero
executable tokens.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. `docs/SPECS/spec-028-orders-0_0_8.md`
is dirty from **Slice 1**, not this slice; `docs/SPECS/spec-055-search_fields-0_1_2.md` and every
`docs/builder/*-027*.md` are the concurrent cohort's. All four concurrent-writable generated /
binary files (`examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`) are
clean, as at pass 1.

### Static inspection helper

**Skip, recorded with its reason.** `BUILD.md` `### When to run the helper during build` fires for
Worker 3 on a new `.py` file, a touched file under `optimizer/` or `types/`, or 30+/50+ new logic
lines. This pass touches **no** file under `types/` or `optimizer/` — `types/base.py` carries pass-1
work only and `types/finalizer.py` is the concurrent cohort's — adds no file, and adds **zero**
logic lines. The one file the slice does own under `types/` was run in pass 1 against the
unconditional "touches" trigger (Ruling 6), exit 0,
`docs/shadow/django_strawberry_framework__types__base.overview.md`, and it is byte-unchanged since.
No re-run is owed and none was performed.

### Hot-path budget

Not applicable; plan declares no hot path, and this pass changes no executable token, so nothing
was added to any per-request / per-resolver / per-row path. No number is owed.

### Floor verification

Not applicable; plan declares floor-verification scope `none`. No floor venv was built and the
shared `.venv` was not mutated by this pass.

### Test staleness sweep (run independently, not against the slice's file list)

Both shapes `BUILD.md` `### Test staleness a focused run cannot see` names require an executable
change: an example-model field added / removed / renamed, or a wire-shape conversion. The AST and
token streams of all sixteen paths are identical to their references, and no model, schema module,
or field set is touched anywhere in the diff, so neither shape can have been introduced. Staged
anchors: `grep -rn 'TODO(spec-028' .` -> no hits tree-wide.

### What looks solid

- **The C5 box is now satisfied in both halves.** The banner carries the count with its subject
  (`16 test functions / 19 test rows`), the derivation (the three extra rows and which test
  parametrizes them), the source of the two out-of-card additions
  (`spec-030-connection_field-0_0_9` P1-B), **and both test names**. I re-derived 16 / 19 by AST
  structure rather than by the grep that produced Worker 0's original wrong 15, and both named
  tests are in the range.
- **C11 is the substantive repair it was asked to be, not a coordinate swap.** Every one of the
  twelve old coordinates pointed at wrong content; every new one resolves to a symbol that holds
  the guard, with a substring unique inside it, and the restated expressions are true of the code
  at HEAD. The three that asserted a sync/async split now say plainly that one helper is reached
  through two entry points.
- **C12's wrapped site is the one that mattered and it is fixed the right way.** `orders/sets.py`
  451-452 is respelled *and* reflowed so `spec-028 Decision 8 step 6` sits unbroken on one line,
  which is what makes it visible to the next census. Tree-wide the bare form is down to the single
  out-of-family `spec-015` site, single-line and flattened agreeing.
- **`utils/inputs.py`'s two C12 sites are qualified without being re-attributed.** Both sentences
  already scoped their claim to the order family and explicitly contrasted the filter family, so
  adding the `spec-028` token names the order family's contract as the origin and leaves both
  sentences true for the filter side. One wording, used at both sites.
- **Worker 2's boundary discipline under a live collision was correct.** It reported the churn
  instead of reverting it, re-verified its own hunks in the shared file after the other session
  wrote it, escalated the ownership question to the maintainer on disk rather than only in a return
  report, and named the four contested paths precisely. Its `### Late-breaking working-tree event`
  block is the reason this review could attribute the cookbook delta in minutes.
- **The two out-of-family review-item ids left alone in `utils/inputs.py` are the right boundary.**
  `spec-039 P2` and `spec-040 D6` (3 occurrences, unchanged) are C1's exact defect class, but they
  are claims about two cards this cycle never verified — the same ground that fences the connection
  and relay registry twins. Repairing them would mean a worker asserting two other specs'
  contracts. Correctly deferred, and now doubly so: `utils/inputs.py` is claimed by the concurrent
  cohort C as well.

### Records to correct (not findings against the diff)

- **R1 — Ruling 2's cookbook postcondition and its deferred-work entry.** "Exactly the 6 named
  cookbook refs remain" is no longer true of the tree; **2** remain. The delta is wholly the
  concurrent cohort B's, proven three ways above, including from that cohort's own artifact. The
  `bld-final-028.md` `### Deferred work catalog` bullet must read **two** cookbook line refs left
  with reason (both in `tests/orders/`), not six — otherwise the next reader hunts four sites that
  no longer exist and may re-open a ruling the other cycle has already overtaken. Whether Ruling
  2's carve-out survives cohort B's contrary treatment of the same class is the maintainer's, as
  Worker 2 said.
- **R2 — the handoff census is a moving target and Slice 3 must re-derive it at entry.**
  83 / 54 / 6 / 2 was correct when Worker 2 measured it and I reproduced it exactly on my first
  reading. My last reading is **88 / 59 / 6 / 2**; the +5 is cohort C's, in `orders/__init__.py`
  (+3, three `Decision-11` sites) and `utils/inputs.py` (+2, the `Decision-9` / `Decision-11`
  sites), each respelling adding one `spec-028` and one `spec-028 Decision N`. Single-line and
  flattened agree at every class at both readings. **Slice 3 is Worker 1's own next slice and it
  rewrites every `### Decision N` heading's prose, so the protect-list must be measured at Slice 3
  entry, not read from this artifact** — and it must also protect the `### DoD` anchor (2 sites)
  and `## Test plan` (6). A number written down here rots while a concurrent cycle is respelling
  citations into the same family.
- **R3 — the citation gate's count is not a valid pass/fail while the other cycle runs.** Three
  successive readings in this cycle: 758, 772, **779**, all exit 0. Only the **exit code** plus a
  reading attributable to Slice 2 is evidence; the absolute number is not stable, and a later pass
  differencing against `772` will read a rise it did not cause. The gate is also
  `path::Symbol`-only and **line-scoped**, so it is structurally blind to M1's wrapped anchors and
  to every `#"substring"` half — confirmed by reading `scripts/check_citations.py`'s module
  docstring and `iter_citations`.

### Temp test verification

- `docs/builder/temp-tests/slice-2/test_parent_poison_probe.py` — three rows probing whether the
  C6c replacement claim holds in the state the registry twins actually run in: which order
  submodules are loaded, and what `utils/inputs.py::_safe_import` returns with the parent package
  poisoned and the target module cold vs warm. All three passed
  (`uv run pytest … --no-cov -q`, 3 passed; no `--cov*` flag in any command this pass).
- **Disposition: deleted after use.** It produced L4, which is a docstring-accuracy finding rather
  than a behavior bug, so there is nothing to promote — the existing
  `::test_clear_tolerates_unimportable_order_submodules` already exercises the path; what is wrong
  is the sentence describing it. If Worker 1 prefers the invariant pinned rather than described,
  the promotable shape is a row asserting `_safe_import` returns `None` for a cold submodule of a
  poisoned package, under `tests/utils/`, and that would be a **new executable statement** and so
  cannot land in this slice without forfeiting the zero-boundary entitlement.

### Notes for Worker 1 (spec reconciliation)

1. **Escalated: L4, the C6c accuracy defect.** Your step 20 said "If either side's callback does
   look up a poisoned module, that side keeps its clause and the asymmetry is recorded as factual".
   Measured: neither callback looks up a poisoned *module*, but both look up submodules of the
   poisoned *package*, and with `orders.factories` cold (it is imported from exactly one lazy site,
   `types/finalizer.py::_bind_ordersets`) importlib resolves the poisoned parent and raises, so the
   best-effort swallow is operative in that state. Both families are symmetric, so nothing forces
   an asymmetry. Two resolution paths: (a) restore a *narrow* best-effort clause naming the
   parent-resolution case, wording suggested under L4 — accurate, keeps one story, and does not
   restore the over-broad clause L1 objected to; or (b) keep the text and record the
   state-dependency here. I recommend (a); it is your call because the wording is your ruling's.
2. **Escalated: L5's document conflict.** Step 19 instructed Worker 2 to correct two sentences in
   the pass-1 build report; `ARTIFACT.md` `## Re-pass sections` says never edit prior entries. The
   instruction was not performed and not deferred. Please settle which document wins so the next
   re-pass is not handed the same contradiction.
3. **R1, R2 and R3 above are yours to carry into `bld-final-028.md` and Slice 3.** R1 changes a
   deferred-work bullet from six sites to two; R2 says the protect-list must be re-measured at
   Slice 3 entry and must now cover the `### DoD` anchor as well; R3 says the citation gate's
   count is not differenceable while the other cycle runs.
4. **The cross-cycle ownership question Worker 2 escalated is real and I confirmed it from the
   other cycle's own documents**, not from its report: `docs/builder/build-027-filters-0_0_8.md`
   `### Catalog-discharge cohorts` declares cohort B over `orders/sets.py` and cohort C over
   `orders/{__init__,factories}.py` + `utils/inputs.py`, and cohort C's item-5 population names
   `utils/inputs.py` 1300 / 1708 / 1733 — two of which are C12's own sites. Both cycles have now
   written all four files. Nothing was lost either way, and both cycles' hunks are prose-only, but
   the partition question is the maintainer's and it is live, not hypothetical.
5. **Out-of-scope observation, offered once and not pursued.** My wrap differencer over the whole
   `.py` tree finds **49** occurrences of a `spec-NNN <Decision|DoD|Edge|test plan>` citation that
   is visible flattened and invisible single-line, across 30 files — the same class the other
   cycle's catalog item 1 is discharging at a much smaller measured population. Different shapes
   may be intended; I am not correcting their count. It is recorded because it is the strongest
   available evidence for R3's proposal that any gate extension must match whitespace-flattened,
   which `### Spec changes made` item 3 already carries.

### Checklist audit

Walked every box, including the twelve from pass 1 (confirmed, not re-litigated) and the six from
the re-pass.

| Box | Verdict | Basis |
|---|---|---|
| C1, C2, C3, C3b, C4, C6, C6b, C7, C7b, C7c, C8 | **hold** | landed pass 1, reviewed pass 1, audited by Worker 1; re-confirmed only where a pass-2 postcondition covers them (flattened probe: 0 `path:NN`, 0 `Test <N>`, 0 `(spec-028 N3)`) |
| **C5** | **holds — the over-tick is repaired** | banner names both post-ship additions; count re-derived 16/19 by AST structure |
| **C6c** | **holds; the text landed in both twins, and its accuracy is L4** | four sites, connection and relay twins byte-identical |
| **C9** | **holds** | `Seven ordersets`, 7 re-derived, both names present; the `title: ASC` attribution is L6 |
| **C10** | **holds** | prose `line NN` in `tests/orders/` 11 -> 2, both survivors cookbook and byte-identical |
| **C11** | **holds on population and target; the citation FORM is M1 at 2 of 12 sites** | 12 -> 0 raw `path:NN`; every replacement resolves and restates correctly; two wrap across two source lines |
| **C12** | **holds** | bare form tree-wide 17 -> 1 (`spec-015`, out of family); wrapped site respelled and reflowed onto one line |
| Zero new `spec-028 #"substring"` citations | **holds** | 0 / 0, single-line and flattened |
| No executable statement changed | **holds** | 38 readings, two instruments, `MISMATCHES: 0` |
| Nothing edited outside the sixteen | **holds** | `git status --short` carries only the sixteen, this cycle's artifacts, Slice 1's spec + rationale, and the concurrent cohort's files — all attributed above |
| ruff scoped / no churn | **holds** | `16 files already formatted`, `All checks passed!`, read-only, never `.` |
| gates | **holds** | `check_citations.py` exit 0; `check_trailing_commas.py --check` exit 0 |

**No box is un-ticked by this pass.** M1 is a defect in how two of C11's replacements are
*written*, not a claim that C11's contract did not land, so un-ticking it would mis-describe the
diff; the box stays `- [x]` and the finding carries the repair.

### Review outcome

`revision-needed`.

One Medium and three Lows, none of which needs spec context Worker 2 cannot supply, so none is a
candidate for accept-with-escalation:

- **M1** — two of this pass's own citations wrap across two source lines, violating a constraint
  Worker 1 declared non-discretionary and the plan declared non-discretionary before it, and the
  build report's wrap-probe row reports the postcondition as met when it is not. Two docstring
  lines; both replacements measured to fit the 110-column grace.
- **L4** — the C6c replacement's conclusion is stronger than the measured truth. Worker 1 chooses
  the wording (item 1 above); Worker 2 applies it.
- **L5** — step 19's build-report correction neither performed nor deferred; needs a recorded
  reason, and Worker 1 settles the `ARTIFACT.md` conflict.
- **L6** — one clause in C9's docstring attributes an `IssueOrder`-only example to both new
  ordersets.

Everything else in steps 19-24 landed and holds under independent re-derivation, the
zero-executable-change entitlement is intact on two instruments across 38 readings, and the
mandatory failability re-run floor is empty **by entitlement** rather than by omission.

---

## Build report (Worker 2, pass 3)

Scope: **M1, L4, L5, L6 from `## Review (Worker 3, pass 2)`** — four items, all comment and
docstring text, across four of Slice 2's sixteen authorized paths. **No checklist box is ticked,
un-ticked, or re-worded by this pass.** M1 / L4 / L6 are defects in how three already-landed boxes
(C11, C6c, C9) are *written*, not claims that their contract did not land — Worker 3's checklist
audit says so explicitly and I do not re-describe the diff by moving a marker. L5 is a records
item, discharged in this report.

**Zero executable statements changed in all four files**, proved below on two instruments against
two reference points, so the zero-boundary entitlement the slice's whole verification rests on is
intact and no failability proof, hot-path number, or floor run is owed.

### Files touched

Grounded in `git status --short` (full output and its classification below).

- `tests/orders/test_sets.py` — **M1.** `::test_orderset_active_permission_field_paths_falls_back_to_python_attr_when_no_field_spec_entry`'s opening docstring line: the `utils/permissions.py::active_permission_targets` symbol half and its `#"else fallback_path(field.python_attr)"` anchor half now sit unbroken on ONE source line. The `-- the defensive fallback` gloss is dropped rather than relocated; the paragraph below it already says the walker falls back to the python-attr token rather than dropping the field.
- `tests/orders/test_factories.py` — **M1.** `::test_factory_dedupes_double_enqueued_target_via_seen_check`'s opening docstring line: `utils/inputs.py::GeneratedInputArgumentsFactory._ensure_built` joined to `#"if set_cls in seen:"` on one line. The `-- the pop-time skip` gloss is dropped; the section banner two lines above already states it.
- `tests/test_registry.py` — **L4.** Four sites, two per twin: `::test_clear_tolerates_unimportable_order_submodules` and `::test_clear_tolerates_unimportable_filter_submodules`, docstring and inline comment in each. The absolute conclusion is replaced by one that is true in **every** state, warm and cold-plus-poisoned-parent alike. `::test_clear_tolerates_unimportable_connection_submodule` and `::test_clear_tolerates_unimportable_relay_module` are proved byte-identical below.
- `examples/fakeshop/apps/library/orders.py` — **L6.** Module docstring: the `orderBy: {title: ASC}` clause is attributed to `IssueOrder` alone and `PeriodicalOrder` is named as the related target `IssueOrder.periodical` reaches. Orderset count re-derived from scratch, not carried forward.

Plus this artifact (this report + `Status: built`; no box marker touched) and
`docs/builder/worker-memory/worker-2-028.md`.

### Tests added or updated

**None.** No test is added, removed, renamed, or re-asserted; not one assertion, fixture, or
`sys.modules` manipulation changes. L4 replaces a *claim about* the teardown path, not the path.

### Validation run

Every "before" reading was taken before the first edit of this pass.

#### The join-aware wrap probe — the instrument M1 says was owed

The pass-2 `### Validation run` wrap-probe row read `0` / `pass` and **that reading was wrong**, for
the reason M1 gives: the differencer probed `path::Symbol`, `spec-028 …` and `#"substring"` as three
*separate* forms, and at both M1 sites each form is intact on its own line. What wrapped was the
**join** between the symbol half and the anchor half, which no single-form probe can express. The
instrument's agreement with the earlier passes therefore measured the instrument, not the
population — the seventh time this cycle a citation census has been under-measured by exactly the
count its instrument could not see.

The replacement probe matches the join: the symbol-or-module half, then `[ \t]*\n[ \t]*` (whitespace
that **crosses a newline**), then an optional comment-continuation `#`, then the `#"` anchor. Run
repo-wide over every non-`.venv` `.py` file, before and after:

| Reading | Sites | Detail |
|---|---|---|
| **before**, repo-wide `.py` (424 files) | **4** | `tests/orders/test_sets.py:657`, `tests/orders/test_factories.py:371`, `examples/fakeshop/test_query/test_library_api.py:8014`, `django_strawberry_framework/orders/sets.py:258` |
| **after**, repo-wide `.py` | **2** | only the two out-of-scope sites below; **both first-party in-scope joins are closed** |

The two survivors are classified, not missed, and both cite a **third-party** tree, which
`scripts/check_citations.py` is by design **not** fail-closed on (its module docstring scopes
fail-closed to `django_strawberry_framework/`, `tests/`, `examples/`, `scripts/`):

- **`examples/fakeshop/test_query/test_library_api.py:8014`** — `django/db/models/fields/related_descriptors.py::_filter_prefetch_queryset` joined to `#"reuse_all=True"`. **Outside Slice 2's scope:** line 8014 is far past the spec-028 section's 1738-2484 bounds, and the citation names Django's own source. Left byte-identical, exactly as the task's scope ruling directs.
- **`django_strawberry_framework/orders/sets.py:258`** — `django_graphene_filters/orderset.py::AdvancedOrderSet.get_fields` joined to `#"Works for both dict (iterates keys)"`. **This one is NEW since Worker 0's probe reading and it is the concurrent `spec-027` cohort's own hunk**, not a site any pass of this cycle wrote. Proof, read-only: `git show HEAD:django_strawberry_framework/orders/sets.py` at that region carries `# Cookbook line 279-280: "Works for both dict (iterates keys) and`, and `git diff HEAD -- django_strawberry_framework/orders/sets.py` shows the three-line `path::Symbol` + `#"substring"` replacement as `+` lines — i.e. cohort B converting the very cookbook `line NN` ref Ruling 2 ordered left byte-identical, in the treatment Ruling 2 declined. Per the maintainer's standing instruction for this cycle and `AGENTS.md` #"Files dirty at task start", it is **not reverted, not reformatted, not reconciled**. It is named here so the record shows it was seen and classified.

#### Flattened multi-class citation probe, the four files touched

Every class counted twice over the same text — as written, and with every whitespace run collapsed
to one space. A class whose two readings disagree has a wrapped citation.

| Class | single-line | flattened | Verdict |
|---|---|---|---|
| `spec-028` | 5 | 5 | agree |
| `spec-028 Decision N` | 2 | 2 | agree |
| `spec-028 DoD N` | 0 | 0 | agree |
| `spec-028 test plan` | 3 | 3 | agree |
| `spec-028[^)]*#"` | **0** | **0** | agree; baseline 0 held |
| `raw-line-citation` (`\blines? [0-9]+`) | 2 | 2 | agree; **both are the Ruling-2 cookbook pair** (`test_sets.py` #"per cookbook line 280", `test_factories.py` #"cookbook lines 124-130"), byte-identical |
| `path-NN-citation` | 0 | 0 | agree |
| `Test-N-ordinal` | 0 | 0 | agree |
| `bare-Spec-Decision` | 0 | 0 | agree |

#### The three durable-form censuses, tree-wide, with their timestamp

Reported **with the time they were taken and with the concurrent cohort's contribution attributed**,
because R2 is right that the absolute values move while the other cycle respells citations into the
same family.

| Class | before, `2026-08-20T14:58:52Z` | after, `2026-08-20T15:02:51Z` | Delta |
|---|---|---|---|
| `spec-028` | 88 | **88** | 0 |
| `spec-028 Decision N` | 59 | **59** | 0 |
| `spec-028 test plan` | 6 | **6** | 0 |
| `spec-028 DoD N` (fourth class) | 2 | **2** | 0 |
| all four, flattened | 88 / 59 / 6 / 2 | **88 / 59 / 6 / 2** | single-line == flattened at every class, both readings |

**Attribution of the delta against pass 2's closing 83 / 54 / 6 / 2:** none of the `+5` is this
pass's. My pre-edit reading already stood at 88 / 59 / 6 / 2 — identical to Worker 3's *last*
pass-2 reading, which attributed the `+5` to the concurrent cohort C in `orders/__init__.py` (+3)
and `utils/inputs.py` (+2). This pass moved no census class in either direction: it added no
`spec-028` token and removed none.

#### Everything else

| Check | Before | After | Verdict |
|---|---|---|---|
| `uv run python scripts/check_citations.py` | `OK: 780 citations resolve (703 in 422 .py files, 77 in KANBAN.md)`, **exit 0** | `OK: 782 citations resolve (705 in 422 .py files, 77 in KANBAN.md)`, **exit 0** | pass — **exit code is the criterion**, per R3; the absolute count is not stable while the other cycle runs (758 / 772 / 779 / 780 / 782 across five readings now). The `+2` is attributable and expected: the two new `utils/inputs.py::_safe_import` citations the L4 wording adds, one per registry twin, both first-party and therefore fail-closed-resolved |
| `uv run python scripts/check_trailing_commas.py --check <the 4 files>` | — | exit 0 | pass |
| docstring-stripped `ast.dump` **and** executable-token identity, 4 paths vs `HEAD` | 4 readings, `MISMATCHES: 0` | 4 readings, `MISMATCHES: 0` | **SAME** |
| same, `tests/test_registry.py` vs `5c6fdd71` | 1 reading, `MISMATCHES: 0` | 1 reading, `MISMATCHES: 0` | **SAME** — run because `8a9840dc` swept that file, so the HEAD reading alone is trivially true there |
| `uv run ruff format <the 4 files>` | — | `4 files left unchanged` | pass (scoped, never `.`) |
| `uv run ruff check --fix <the same 4>` | — | `All checks passed!` | pass (scoped) |
| `uv run python -m compileall -q <the same 4>` | — | exit 0 | pass |
| `uv run pytest tests/orders/test_sets.py tests/orders/test_factories.py tests/test_registry.py --no-cov --collect-only -q` | — | `152 tests collected`, 0 errors | pass |
| `uv run pytest examples/fakeshop/apps/library --no-cov --collect-only -q` | — | `10 tests collected`, 0 errors | pass |
| connection + relay twins byte-identical | — | `cmp` exit 0 against **both** `HEAD` and `5c6fdd71` | pass |
| every line inside the 110-column E501 grace, 4 files | — | 0 lines over 110 **that this pass wrote** | pass (one pre-existing 164-column line, below) |

No `pytest` was run as routine slice work; the two invocations above are `--collect-only` and exist
solely because a mangled triple-quote is the one way a prose-only edit breaks something. **No
`--cov*` flag was passed in any command this pass.** No `git stash` / `checkout` / `restore` /
`worktree` was run at any point; every pristine reference came read-only from `git show` into a
scratch path **outside** the repository.

**One line over the grace, and it is not this pass's.** `tests/test_registry.py:1537` is 164
columns. `git show HEAD:tests/test_registry.py` carries the identical line at the identical line
number, so it pre-dates this cycle; `tests/**` ignores `E501` in ruff, which is why it has never
failed a gate. Reported rather than fixed: measured, it sits inside
`tests/test_registry.py::test_unregister_of_primary_leaves_state_that_audit_rejects`, outside all
four items this pass owns.

#### `git status --short` after both ruff invocations

```
 M django_strawberry_framework/consumers.py
 M django_strawberry_framework/filters/factories.py
 M django_strawberry_framework/mutations/fields.py
 M django_strawberry_framework/mutations/resolvers.py
 M django_strawberry_framework/mutations/sets.py
 M django_strawberry_framework/optimizer/extension.py
 M django_strawberry_framework/orders/__init__.py
 M django_strawberry_framework/orders/base.py
 M django_strawberry_framework/orders/factories.py
 M django_strawberry_framework/orders/inputs.py
 M django_strawberry_framework/orders/sets.py
 M django_strawberry_framework/rest_framework/resolvers.py
 M django_strawberry_framework/rest_framework/serializer_converter.py
 M django_strawberry_framework/rest_framework/sets.py
 M django_strawberry_framework/routers.py
 M django_strawberry_framework/types/base.py
 M django_strawberry_framework/types/finalizer.py
 M django_strawberry_framework/types/relay.py
 M django_strawberry_framework/utils/inputs.py
 M docs/SPECS/spec-028-orders-0_0_8.md
 M docs/SPECS/spec-055-search_fields-0_1_2.md
 M docs/builder/build-027-filters-0_0_8.md
 M examples/fakeshop/apps/kanban/schema.py
 M examples/fakeshop/apps/library/orders.py
 M examples/fakeshop/test_query/test_library_api.py
 M examples/fakeshop/test_query/test_products_api.py
 M tests/orders/test_base.py
 M tests/orders/test_composition.py
 M tests/orders/test_factories.py
 M tests/orders/test_inputs.py
 M tests/orders/test_sets.py
 M tests/test_registry.py
 M tests/test_relay_connection.py
?? docs/SPECS/appx/spec-028-orders-0_0_8-rationale.md
?? docs/builder/bld-slice-1-028-rationale_extraction.md
?? docs/builder/bld-slice-10-027-wrapped_citations_outside_package.md
?? docs/builder/bld-slice-2-028-citation_and_provenance_rot.md
?? docs/builder/bld-slice-6-027-wrapped_citations.md
?? docs/builder/bld-slice-7-027-raw_line_refs.md
?? docs/builder/bld-slice-8-027-decision_attribution.md
?? docs/builder/bld-slice-9-027-spec_055_refs.md
?? docs/builder/build-028-orders-0_0_8.md
```

Classified in full. **Nothing was reverted, reformatted, or re-staged.**

- **Four paths this pass edited:** `tests/orders/test_sets.py`, `tests/orders/test_factories.py`, `tests/test_registry.py`, `examples/fakeshop/apps/library/orders.py`.
- **Nine more of Slice 2's sixteen**, carrying passes 1-2 only and untouched here: `orders/{__init__,base,factories,inputs,sets}.py`, `types/base.py`, `utils/inputs.py`, `tests/orders/{test_base,test_composition,test_inputs}.py`, `examples/fakeshop/test_query/test_library_api.py`. (`tests/types/test_base.py` is absent from the listing because `8a9840dc` swept it and no pass has touched it since — read it by present state, not by diff.)
- **Slice 1's output:** `docs/SPECS/spec-028-orders-0_0_8.md` + the untracked rationale companion. **Cycle artifacts:** `bld-slice-1-028`, `bld-slice-2-028`, `build-028`.
- **The concurrent `spec-027` cohort's already-known files:** `consumers.py`, `routers.py`, `filters/factories.py`, `types/finalizer.py`, `types/relay.py`, `mutations/{fields,resolvers,sets}.py`, `test_products_api.py`, `docs/SPECS/spec-055-search_fields-0_1_2.md`, `docs/builder/build-027-filters-0_0_8.md`.
- **STOP-AND-REPORT — six paths that no prior pass of this cycle, and no brief handed to me, names.** All six are unmistakably the same cohort's citation-and-provenance work in other cards' modules, and I read each diff rather than assuming it: `optimizer/extension.py` (bare `Decision 7` -> `spec-033 Decision 7`, 14 lines), `rest_framework/resolvers.py` (`spec-039 Decision 7`, 20 lines), `rest_framework/serializer_converter.py` (review-item id `M3` -> `spec-039 M3`), `rest_framework/sets.py` (`spec-039 Decision 6/10/11/12`), `tests/test_relay_connection.py` (`Revision N PN` review-item ids struck out — C1's exact defect class), and `examples/fakeshop/apps/kanban/schema.py`, which is repairing a **wrapped `#"substring"` anchor** into an unbroken `optimizer/walker.py::_walk_selections #"snake_case(sel.name), None"` — the same defect M1 closes, in a file neither cycle's partition named to me. Plus five new `bld-slice-{6,7,8,9,10}-027-*.md` artifacts whose slugs (`wrapped_citations`, `raw_line_refs`, `decision_attribution`, `spec_055_refs`, `wrapped_citations_outside_package`) name this slice's whole finding taxonomy. **None is in Slice 2's sixteen and none was touched.** The cross-cycle ownership question pass 2 escalated has widened, not settled: see `### Notes for Worker 1` item 3.
- All four concurrent-writable tracked binaries / generated files (`examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`) are **clean**; this pass planned no edit to any and observed no churn.

### Failability proofs

`None; this pass introduced no new boundary.`

The entitlement is proved, not asserted. Docstring-stripped `ast.dump` **and** executable-token
identity both read `SAME` for all four paths, before and after, against `git show HEAD:<path>` and
additionally against `5c6fdd71` for `tests/test_registry.py`, whose HEAD reading is trivially true
because `8a9840dc` swept it. Ten readings across two instruments, `MISMATCHES: 0`. Pristine copies
came read-only from `git show` into a scratch path outside the repository. No fail-open shape can
have landed, because a fail-open expression is an executable expression and the executable token
stream is unchanged everywhere.

### Hot-path budget

`Not applicable; plan declares no hot path.`

### Floor verification

`Not applicable; plan declares floor-verification scope none.`

### L5 — the correction step 19 asked for, stated here instead of by editing a prior entry

Step 19's second instruction was to correct two sentences **inside the pass-1 build report**.
`ARTIFACT.md` `## Re-pass sections` says "never edit prior entries", so performing it as written is
not available to me. L5 is right that silence is not the discharge either. So, plainly, on the
record, in this pass's own report:

- **The pass-1 `### Validation run` C5 row was false where it said the banner named "both" post-ship additions.** It did not. The banner as shipped by pass 1 named their *class and source* (`the row-preserving to-many aggregate cases from spec-030-connection_field-0_0_9 P1-B`) and neither test name. Worker 3's pass-1 L2 found it, Worker 1's Ruling 1 un-ticked C5 for it, and pass 2's step-19 work is what made the claim true.
- **The pass-1 `### Implementation notes` sentence "a first line attributing the two post-ship additions" was false in the same way.** What that line attributed was the two additions' contract and source, not their names. The accurate wording is "a first line attributing them by contract and source".

Both pass-1 sentences stand unedited in this file. A linear reader reaches this correction, Worker
3's L2, and Ruling 1 before reaching the final gate, and `bld-final-028.md` needs no further
carry-forward for it.

### Implementation notes

- **The wrap probe had to be re-designed, not re-run.** Probing `[Symbol]`, `[spec-028 …]` and `[#"sub"]` and differencing each against its flattened self is structurally incapable of seeing M1: both halves are individually unwrapped. The join is the unit of the citation grammar, so the pattern is `(?:::[\w.]+|[\w./]+\.py)`{0,2}[ \t]*\n[ \t]*(?:#[ \t]*)?#"` — the `\n` inside the pattern is the whole point. It found both M1 sites plus two third-party ones, one of which no earlier reading of this cycle could have contained because it did not exist yet.
- **Both replacement widths were measured, not trusted.** `tests/orders/test_sets.py:657` is **107** columns, not the 106 Worker 3 measured; `tests/orders/test_factories.py:371` is **103**, matching exactly. Both are inside the 110-column E501 grace, and `tests/**` ignores `E501` regardless, so the one-column disagreement changes no verdict — recorded because a width read off a formatter rather than a file is the same class of unmeasured number this cycle keeps finding.
- **L4's replacement names the mechanism by symbol rather than describing it.** The new clause reads "it imports neither poisoned name **directly**; the two submodule lookups it does make are best-effort (``utils/inputs.py::_safe_import``)", and the conclusion becomes "neither the poisoned package nor the poisoned ``inputs`` module can make ``clear()`` raise". That is true in the warm state AND in the cold-plus-poisoned-parent state Worker 3 measured, where `importlib` must resolve the `None`-poisoned parent and the swallow is what holds. Adding the `_safe_import` citation makes the "best-effort" half checkable and gate-enforced instead of asserted — verified against source first: `utils/inputs.py::clear_generated_input_namespace` makes exactly two `_safe_import` calls, and `_safe_import`'s own docstring states the `None`-in-`sys.modules` shape raises `ImportError` there.
- **The two inline comments are byte-identical across the twins and the conclusion is re-scoped rather than re-hedged.** "no step of the teardown path can raise" becomes "nothing on the teardown path can raise **OUT of** ``clear()``" — a statement about what propagates, which is what the test asserts, rather than about what executes. The docstrings differ only where the families differ, which is the shape Ruling 5 ordered.
- **L6 keeps the file's own vocabulary and re-derives the count.** The `orderBy: {title: ASC}` clause is `IssueOrder`'s own docstring sentence and now says so; the `PeriodicalOrder` half reuses that class's own docstring phrase, "the related target for ``IssueOrder.periodical``". Verified before writing: `PeriodicalOrder.Meta.fields` is `["id", "name"]` with no `title`. Count re-derived from scratch, `grep -c '^class .*Order(OrderSet)'` -> **7**, enumerated as `BranchOrder`, `ShelfOrder`, `BookOrder`, `LoanOrder`, `PatronOrder`, `PeriodicalOrder`, `IssueOrder`; `Seven` was already right and is unchanged.
- **Reflow discipline in the L6 paragraph.** Absorbing the insert pushed a two-word orphan line; I re-flowed the following sentence to close it, and deliberately backed out a variant that split the ```` ``BookOrder.genres = RelatedOrder(...)`` ```` code span across two lines. A wrapped code span is the same failure shape as a wrapped citation, and this slice is the last place to introduce one.

### Notes for Worker 3

- **The join-aware probe is the instrument to re-run, and a three-form probe will agree with pass 2's wrong reading.** It is reconstructable from the pattern quoted under `### Implementation notes`; run it repo-wide over `.py`, not only over the sixteen paths, or the `orders/sets.py:258` site the other cohort introduced mid-cycle stays invisible.
- **Two wrapped joins survive on purpose and are named with their reason** under the wrap-probe table: `test_library_api.py:8014` (third-party Django target, far past the 1738-2484 section bounds) and `orders/sets.py:258` (third-party cookbook target, and the other cycle's own new hunk). Both cite trees `check_citations.py` is not fail-closed on. Neither is a miss.
- **Read `tests/types/test_base.py` and the pass-1 halves of `tests/test_registry.py` / `test_library_api.py` by present state, not by diff** — `8a9840dc` swept them, so `git diff HEAD -- <path>` is empty of pass-1 work. Use `git diff 5c6fdd71 -- <path>`.
- **Six dirty paths outside every partition named to me are reported under `git status --short`, with each diff read rather than assumed.** They are the other cohort's, they include a wrapped-anchor repair identical in kind to M1, and none was touched.
- **The pre-existing 164-column line at `tests/test_registry.py:1537` is not this pass's** and is proved so against HEAD at the same line number.

### Notes for Worker 1 (spec reconciliation)

Written on disk because a return message reaches nobody.

1. **L5 is discharged in this report, not by an edit to a prior entry, and the `ARTIFACT.md` conflict still wants your ruling.** The correction is stated verbatim under `### L5` above. Your step 19 asked for an edit to the pass-1 report; `ARTIFACT.md` `## Re-pass sections` forbids it. I resolved it the way that rule permits and recorded which two sentences were wrong and how. If you want the convention settled for future cycles, the choice is between "a later report corrects an earlier one" (what I did) and licensing a custodian-only correction-in-place; a builder cannot pick between two standing documents.
2. **The wrap-probe blindness is now a measured pattern with a named cause, and it is worth one sentence in the spec-side lesson rather than a seventh recurrence.** Every under-measurement in this cycle — C2's wrapped site, M2's wrapped site, the two pre-existing `spec-028 Decision N` wraps found in pass 2, and now M1's two joins — was **a single-form instrument reading a multi-part citation**. The `check_citations.py` gate-extension entry already in `### Spec changes made` item 3 says the extension must match whitespace-flattened; recommend it also say **the gate must match the JOIN of symbol and anchor, not either half**, because a flattened per-form probe still would not have caught M1. Recommended replacement for that item's second clause: current "and it must match whitespace-flattened"; replacement "and it must match whitespace-flattened **and must resolve `path::Symbol` together with its `#\"substring\"` anchor as one citation, since a per-form probe reads both halves of a wrapped citation as intact**".
3. **The cross-cycle ownership collision pass 2 escalated has WIDENED and is still unresolved.** At pass 2 the overlap was four files. As of this pass the concurrent cohort has also written `optimizer/extension.py`, `rest_framework/{resolvers,serializer_converter,sets}.py`, `examples/fakeshop/apps/kanban/schema.py` and `tests/test_relay_connection.py`, and has published five further artifacts — `bld-slice-{6,7,8,9,10}-027-*.md` — whose slugs are this slice's entire finding taxonomy (`wrapped_citations`, `raw_line_refs`, `decision_attribution`, `wrapped_citations_outside_package`). Two cycles are now discharging the same defect class across overlapping trees with independent censuses. Nothing has been lost in either direction and every hunk on both sides is prose-only, but the maintainer decision pass 2 asked for is now larger than four files, and `bld-final-028.md`'s deferred-work catalog should carry it as such.
4. **Two tree-wide wrapped `lines? NN` citations exist outside this cycle's paths, and they are the residual population note 7 already catalogues.** Measured on the flattened census: `raw-line-citation` reads single=14 / flat=16 tree-wide. The two wrapped sites are `tests/mutations/test_sets.py` (`spec-036 Decision 6 line 334` wrapped) and `tests/optimizer/test_extension.py` (`Decision 7 line 346` wrapped). Both cite other cards, both are outside the sixteen, neither was touched. Recorded so the next pass reads the 14-vs-16 disagreement as classified rather than as new.
5. **R1, R2 and R3 from Worker 3's pass-2 review are unchanged by this pass and still yours.** My readings corroborate all three: the cookbook population in the sixteen is 2 not 6 (R1 — and `orders/sets.py:258` shows cohort B converting a third one *while this pass ran*); the census is 88 / 59 / 6 / 2 at `15:02:51Z` with the `+5` attributable to cohort C and not to Slice 2 (R2); and the citation gate has now read 780 then 782, exit 0 both times, so only the exit code is evidence (R3).

---

## Review (Worker 3, pass 3)

Scope: **exactly the four items my pass-2 review raised** — M1, L4, L5, L6. C1-C12 landed and were
reviewed in passes 1-2 and are not re-litigated; I confirm below only that no box needed un-ticking.
Every number in this section was re-derived by my own instrument. Where my instrument disagreed with
Worker 2's, I say which was wrong and why — that happened once, and it was mine.

### The mandatory failability re-run floor is empty BY ENTITLEMENT, not by omission

The zero-executable-change property is also the proof of the zero-boundary declaration: a boundary is
an executable expression, and the executable token stream of all four files is unchanged. So there is
no boundary meeting the re-run floor, the legal re-run set is empty, and no proof was owed by Worker 2
(`### Failability proofs` correctly reads `None; this pass introduced no new boundary.`). Stated
explicitly so an empty set is not read as a skipped check.

**Re-derived on two instruments against two reference points, 16 readings, `MISMATCHES: 0`:**

| Instrument | What it can see that the other cannot | Result |
|---|---|---|
| **A** — docstring-stripped `ast.dump` | structure, but blind to a moved non-docstring literal | 8/8 SAME |
| **B** — `tokenize` stream, `COMMENT`/`NL` dropped, only *docstring* `STRING` tokens collapsed, every other literal kept verbatim | a reworded or relocated non-docstring string | 8/8 SAME |

Reference points: `git show HEAD:<path>` for all four, **and** `git show 5c6fdd71:<path>` for all four
(not only `tests/test_registry.py`) — `8a9840dc` swept that file, so its HEAD reading alone is
trivially true and proves nothing. Both baselines agree at both instruments for every file. Pristine
copies were extracted read-only into a scratch path **outside the repository**; no `git stash`,
`checkout`, `restore`, or `worktree` was run at any point in this pass.

### M1 — settled. Both joins are closed, the dropped glosses are genuinely carried, and the probe is join-aware

**The two sites, read directly rather than diffed** (their pass-2 wrapped form is quoted verbatim in
my own pass-2 finding, which is the provenance for the "before"; neither citation exists at `HEAD`,
because C11 wrote them in pass 2 and pass 2 is uncommitted):

- `tests/orders/test_sets.py:657` — `path::Symbol` and `#"anchor"` halves unbroken on one line,
  measured at **107 columns**. Worker 2's correction of my pass-2 reading of 106 is right; I
  re-measured with `awk length($0)` and got 107. My 106 was the error.
- `tests/orders/test_factories.py:371` — unbroken, **103 columns**, matching both readings.

**The dropped-gloss claim, verified rather than accepted.** Worker 2 dropped `-- the defensive
fallback` and `-- the pop-time skip` instead of relocating them, on the ground that surrounding text
already carries them. It does, in both cases, and in both cases the surrounding text is *more*
specific than the gloss was:

- `test_sets.py` — the docstring's own next paragraph reads "``field.spec`` is ``None`` and the walker
  falls back to the python-attr token rather than dropping the field." That is the defensive fallback,
  named with its trigger.
- `test_factories.py` — the section banner two lines above the `def` reads
  `# Pop-time ``if set_cls in seen: continue`` skip`, and the docstring body separately says "the
  second pop hits the ``if set_cls in seen: continue`` skip." Two carriers, not one.

So this is not the "citation resolves while its explanation vanished" failure mode. Nothing was lost.

**Both citations still resolve.** Re-resolved by hand, because `check_citations.py` is
`path::Symbol`-only and blind to the `#"substring"` half: `utils/permissions.py::active_permission_targets`
exists and `else fallback_path(field.python_attr)` occurs **1** time inside that symbol and **1** time
in the whole file; `utils/inputs.py::GeneratedInputArgumentsFactory._ensure_built` exists and
`if set_cls in seen:` likewise **1** / **1**.

**Is Worker 2's probe genuinely join-aware, or a fourth blind instrument?** Genuinely join-aware. Its
pattern puts the `\n` *inside* the expression — `(?:::[\w.]+|[\w./]+\.py)`{0,2}[ \t]*\n[ \t]*(?:#[ \t]*)?#"` —
so it matches the symbol half at end-of-line followed by the anchor half at start-of-next-line, which
is the unit no per-form probe can express. I did not accept that on reading. I wrote a
**differently-shaped** instrument and compared results:

- **My instrument is anchor-first and backward-looking**, not a forward regex over the file text: for
  every `#"` occurrence in every non-`.venv` `.py` file, ask whether *any* citation head (a `.py`/`.md`
  path, a `::symbol`, or a `spec-NNN` / bare `spec` token) appears earlier **on that same physical
  line**; only when none does, ask whether the previous line *ends* in a `.py` path or `::symbol`.
  Different failure surface, same question.
- **Result: exactly 2 wrapped joins repo-wide**, at `django_strawberry_framework/orders/sets.py`
  258-259 and `examples/fakeshop/test_query/test_library_api.py` 8014-8015 — Worker 2's two survivors,
  and nothing else. Two instruments of different shape agreeing at 2 is the first time in this cycle
  a citation census has been corroborated by an instrument that does not share its predecessor's
  blindness.
- I then probed the residual blind spot **both** instruments share — a symbol half that is itself
  split across a newline, and a join separated by more than one line. Gap-joins: **0**. Split paths:
  **1**, at `examples/fakeshop/test_query/test_products_api.py:3334`
  (`` `tests/rest_framework/ `` / newline / `` test_resolvers.py` ``), byte-identical at `HEAD`, a bare
  wrapped *path* with no `::Symbol` and no anchor, in a file that is **not** one of Slice 2's sixteen
  and is the concurrent cohort's. Classified, untouched, and recorded for the deferred catalog.

**Leaving both survivors is right, and I verified each reason rather than reading it:**

1. **`examples/fakeshop/test_query/test_library_api.py:8014`** — cites Django's own
   `django/db/models/fields/related_descriptors.py::_filter_prefetch_queryset`. `git show HEAD:` carries
   the identical wrapped pair at line **8011** (shifted to 8014 by this cycle's earlier edits above it),
   so it is **pre-existing**, not this pass's and not this cycle's. And it is nowhere near the slice's
   territory: the only `spec-028` tokens in that file are at lines **1738** and **1770**. Repairing a
   line 6,200 lines away from the section, pointing at a third-party tree, would be scope expansion.
2. **`django_strawberry_framework/orders/sets.py:258`** — cites the cookbook's
   `django_graphene_filters/orderset.py::AdvancedOrderSet.get_fields`. Confirmed **new** and confirmed
   **not this cycle's**, from the other cycle's own artifact rather than from Worker 2's account:
   `git show HEAD:django_strawberry_framework/orders/sets.py` carries
   `# Cookbook line 279-280: "Works for both dict (iterates keys) and` at that region, and
   `docs/builder/bld-slice-7-027-raw_line_refs.md:29` ticks `` `orders/sets.py` #"Cookbook line 279-280" ``
   as a **census-added box of its own**, with its line 74 spelling out the exact replacement text now
   standing in the tree. That is cohort B converting the very ref Ruling 2 ordered left byte-identical,
   in the treatment Ruling 2 declined. `AGENTS.md` #"Files dirty at task start" and the maintainer's
   standing instruction for this cycle both forbid touching it. **Attribute, do not revert** — and do
   not grade Slice 2 for a postcondition another cycle moved out from under it.

**One cross-cycle observation, recorded because it is the eighth occurrence of the same blind spot and
it is about to be certified by the other cycle's gate rather than mine.**
`docs/builder/bld-slice-7-027-raw_line_refs.md:214` states "This pass introduced no wrapped citation:
the three new `#"…"` forms … all open and close on one line." That is true of each **anchor**, and the
site it wrote is a wrapped **join** — the same instrument error M1 named here, in another cycle's
artifact, standing as a satisfied postcondition. Not a finding against this slice and not mine to fix.
Routed to Worker 1 under `### Notes for Worker 1` so the maintainer decision already in flight carries
it.

### L4 — settled. The re-scoped claim is now true in every state, and I measured the states rather than reasoning about them

**The count Worker 2 says it verified before writing, re-derived by counting CALLS rather than
grepping.** A temp test wrapped `utils/inputs.py::_safe_import` with a spy and invoked
`clear_generated_input_namespace` with the order family's real arguments (`collision_registry_attr` is
`_type_orderset_registry`, read off `orders/inputs.py:157`). **Exactly 2 calls**, matching the two
call sites at `utils/inputs.py:1543` and `:1548`. Worker 2's "exactly two" is right.

I also checked the thing a call-count inside one helper cannot see: whether the *replay* makes other
lookups on the poisoned family's path. The order side registers exactly two callbacks —
`orders/inputs.py::clear_order_input_namespace` (owner `orders.input_namespace`) and
`orders/__init__.py::_clear_helper_referenced_ordersets` (owner `orders.helper_references`) — and the
second is a bare `set.clear()` with no import at all. So the order family's whole teardown path makes
**two** submodule lookups, both through `_safe_import`. The docstring's "the two submodule lookups it
does make" is accurate at the family scope its sentence is written in.

**State-independence, measured on four rows rather than argued.** A temp test poisoned
`{orders,filters}.inputs` **and** the `{orders,filters}` package, in the **warm** state and in the
**cold** state (`{orders,filters}.{factories,sets}` popped from `sys.modules` first, which is what
forces `importlib` to resolve the `None`-poisoned parent), and called `registry.clear()`:

| family | state | `clear()` raises? |
|---|---|---|
| `orders` | warm | no |
| `orders` | **cold + poisoned parent** | **no** |
| `filters` | warm | no |
| `filters` | **cold + poisoned parent** | **no** |

4 rows, all pass. The mechanism is closed end to end by reading: `registry.py::TypeRegistry.clear`
(580-607) contains **no import statement** and ends in `for clear in iter_subsystem_clears(): clear()`;
`utils/inputs.py::_safe_import` delegates to `utils/imports.py::import_attr_if_importable`, whose
`except ImportError: return None` (imports.py:52-53) is the swallow; and both `_safe_import` results
are guarded by `if … is not None`. So the new wording holds in both states, and "nothing on the
teardown path can raise **OUT of** ``clear()``" is a statement about propagation, which is what the
test actually asserts. The absolute claim my pass-2 L4 objected to is gone and what replaced it is not
state-dependent. This is the right resolution — Worker 1's path (a), applied.

The rationale companion agrees at the mechanism level, which is worth naming because it is the record
the next reader will reach first:
`docs/SPECS/appx/spec-028-orders-0_0_8-rationale.md` line 360 records that at HEAD the seam is
`register_subsystem_clear` / `iter_subsystem_clears` with **no** `except ImportError` guard for either
subsystem, and line 483 says the two guards are gone and "whether it still pins anything is a live
question for the `028` cycle's Slice 2." That question is now answered on the record in three places:
pass 1's mutation (1 failing row — the test itself, pinning a real negative invariant), pass 2's
`_safe_import` probe, and this pass's four-row state matrix.

**The two fenced twins are untouched.** `::test_clear_tolerates_unimportable_connection_submodule`
and `::test_clear_tolerates_unimportable_relay_module` extracted by AST bounds and byte-compared:
`cmp` exit 0 against **both** `HEAD` and `5c6fdd71`, both twins (1372 and 1445 bytes). Worker 2 did not
touch the two tests fenced to `spec-030` / `spec-032`.

**All four `clear_tolerates` rows pass** — `uv run pytest tests/test_registry.py -k "clear_tolerates"
--no-cov -q` -> `4 passed`. No `--cov*` flag was passed in any command this pass.

### L5 — settled. Discharged the one way `ARTIFACT.md` permits

`ARTIFACT.md` `## Re-pass sections` says "never edit prior entries", so step 19's instruction to edit
the pass-1 build report was not available. Worker 2 discharged it in **its own pass-3 report**
(`### L5 — the correction step 19 asked for, stated here instead of by editing a prior entry`), and
**both false sentences are named explicitly**:

1. the pass-1 `### Validation run` C5 row's "both named in the new banner";
2. the pass-1 `### Implementation notes`' "a first line attributing the two post-ship additions".

I verified the prior entries were **not** edited: both sentences still stand verbatim at this file's
lines 567 and 633. The conflict is recorded, the substance is corrected in-document, and a linear
reader meets the correction before the final gate. Nothing further is owed here; whether the
convention should be settled for future cycles is Worker 1's, and Worker 2 routed it there.

### L6 — settled, and the count is right in its digit AND its subject

`examples/fakeshop/apps/library/orders.py` lines 3-8 now read: "…``PeriodicalOrder`` and
``IssueOrder`` are the keyset-cursor ``orderBy:`` substrate: a root ``orderBy: {title: ASC}`` page
**over ``IssueOrder``** mints value cursors fingerprinted to THAT order, and ``PeriodicalOrder`` is the
related target ``IssueOrder.periodical`` reaches."

Verified against the classes, not against the report:

- `PeriodicalOrder.Meta.fields` is `["id", "name"]` — **no `title`**. `IssueOrder.Meta.fields` is
  `["id", "number", "title"]`. So the `title: ASC` example belongs to `IssueOrder` alone, and now says so.
- `IssueOrder` carries `periodical = RelatedOrder("PeriodicalOrder", field_name="periodical")`, so
  "the related target ``IssueOrder.periodical`` reaches" is exact.
- The wording is lifted from the two classes' own docstrings (`IssueOrder`'s keyset sentence,
  `PeriodicalOrder`'s "the related target for ``IssueOrder.periodical``"), so the file still tells one
  story in one vocabulary.

**Count re-derived from scratch, by AST rather than by `grep -c`** — because `grep -c '^class .*Order(OrderSet)'`
is exactly the shape of instrument that produced Worker 0's wrong `15` earlier in this cycle. Parsing
the module and selecting `ClassDef` nodes with an `OrderSet` base gives **7**: `BranchOrder`,
`ShelfOrder`, `BookOrder`, `LoanOrder`, `PatronOrder`, `PeriodicalOrder`, `IssueOrder`. `Seven` is right.

And the **subject** is right, which is the half this cycle keeps getting wrong: `orders_genre.py`
carries an eighth (`GenreOrder`), so "Seven" would be false as a claim about the order graph — but the
sentence is this module's docstring and its closing paragraph explicitly says `GenreOrder` lives in the
sibling module. Scoped correctly. No line in the file exceeds 99 columns, so the reflow Worker 2
describes did not cost anything.

### High:

None.

### Medium:

None.

### Low:

None.

All four items my pass-2 review raised are discharged, each verified by an independent measurement
rather than by reading Worker 2's account. Nothing new was found in the four files.

### DRY findings

- **No new code, so no new duplication.** Zero executable tokens changed on two instruments against two
  baselines. There is no helper, constant, branch, or literal introduced to consolidate, and the static
  helper's repeated-string-literal output would be identical to pass 1's by construction.
- **L4's two-twin symmetry is the fix, not duplication.** The two inline comments are byte-identical and
  the docstrings diverge only where the families do. That is the shape Ruling 5 ordered; flagging it
  would be flagging the repair. The `_safe_import` citation added to both twins is the same
  single-sited symbol, cited once per twin — the citation is what makes "best-effort" checkable by the
  gate instead of asserted in prose, which is a strict improvement over the wording it replaced.
- **Cross-cohort duplication review: not applicable, and the reason is structural.** The build plan
  declares `Ownership partition: none; sequential slices`, one cohort over sixteen paths, so there is no
  second cohort of this cycle whose additions could converge. The live convergence in this tree is
  **cross-cycle**, not cross-cohort, and it is a maintainer decision already escalated twice — see
  `### Notes for Worker 1`.
- **The deferred existence challenge stays deferred and I do not reopen it.** Ruling 7's reasoning is
  intact and nothing this pass touched bears on it. `utils/strings.py::graphql_camel_name` #"if not core:"
  — no family-neutral pin, coverage riding two family aliases — remains routed to
  `bld-final-028.md` `### Deferred work catalog` as a card in its own right. One addition to that
  catalog from this pass, below.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` is **empty**. `__all__` and the re-export
list are unchanged; no new public export. Consistent with a pass whose executable token stream is
identical to two separate reference points.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md. Confirmed clean in `git status --short`.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. `docs/SPECS/spec-028-orders-0_0_8.md`
and its untracked rationale companion are **Slice 1's**, not this pass's, and I read both read-only.
All four concurrent-writable generated / binary files (`examples/fakeshop/db.sqlite3`, `KANBAN.md`,
`KANBAN.html`, `docs/GLOSSARY.md`) are **clean**, as at passes 1 and 2. `CHANGELOG.md`, `docs/TREE.md`,
`README.md` and `TODAY.md` are clean.

### Static inspection helper

**Skip, recorded with its reason.** `BUILD.md` `### When to run the helper during build` (lines 402-406)
fires for Worker 3 on three triggers: a new `.py` file, a touched existing `.py` file under
`optimizer/` or `types/`, or 30+ new logic lines inside the package / 50+ outside it. This pass adds no
file, touches **no** file under `optimizer/` or `types/` (the four paths are two under `tests/orders/`,
one at `tests/test_registry.py`, one under `examples/fakeshop/apps/library/`), and adds **zero** logic
lines — proved, not estimated, by the token-identity readings above. No trigger fires; no run was
performed. The pass-1 run of `types/base.py` against Ruling 6's unconditional reading stands, exit 0,
`docs/shadow/django_strawberry_framework__types__base.overview.md`, byte-unchanged.

### Hot-path budget

Not applicable; plan declares no hot path (`build-028-orders-0_0_8.md` line 8, verbatim: "Hot-path
declaration: none. No production behavior changes."). This pass changed no executable token, so nothing
entered any per-request / per-resolver / per-row / per-connection path. **No before/after number is
owed and none is missing.**

### Floor verification

Not applicable; plan declares floor-verification scope `none` (`build-028-orders-0_0_8.md` line 9). No
floor venv was built by this review and the shared `.venv` was not mutated. Reference only, from
`BUILD.md` `## Floor verification`: Django 5.2.16 on Python 3.10 with strawberry-graphql 0.316.0.

### Validation, re-run independently

| Check | My reading | Verdict |
|---|---|---|
| `uv run python scripts/check_citations.py` | `OK: 782 citations resolve (705 in 422 .py files, 77 in KANBAN.md)`, **exit 0** | pass — **exit code is the criterion** per R3; 782 matches Worker 2's after-reading, and is the sixth value this cycle (758 / 772 / 779 / 780 / 782) |
| `uv run python scripts/check_trailing_commas.py --check` (4 files) | exit 0 | pass |
| `uv run ruff format --check` (4 files, never `.`, read-only) | `4 files already formatted`, exit 0 | pass |
| `uv run ruff check` (4 files, **no `--fix`** in a verification pass) | `All checks passed!`, exit 0 | pass |
| Zero-executable-change, instruments A + B x {`HEAD`, `5c6fdd71`} x 4 files | 16 readings, `MISMATCHES: 0` | **SAME** |
| Zero new `spec-028 #"substring"` citations | single-line **0**, whitespace-flattened tree-wide **0** | baseline 0 held |
| Wrapped citation joins, repo-wide `.py`, independent instrument | **2**, both classified above | pass |
| Lines past the 110-column E501 grace, 4 files | **1**: `tests/test_registry.py:1537` at 164 columns | **pre-existing**, see below |
| `uv run pytest <the 3 test paths> examples/fakeshop/apps/library --no-cov --collect-only -q` | `162 tests collected`, 0 errors | pass |
| `uv run pytest tests/test_registry.py -k clear_tolerates --no-cov -q` | `4 passed` | pass |
| `git diff HEAD -- django_strawberry_framework/__init__.py` | empty | pass |

**The 164-column line is confirmed pre-existing and not this pass's.** `sed -n 1537p` on the working
tree and on `git show HEAD:tests/test_registry.py` `diff` **identical, at the identical line number**.
It sits at 1537, ahead of both L4 twins (1617-1701), inside a function no item of this pass owns, and
`tests/**` ignores `E501` in ruff — which is why it has never failed a gate. Reported, not fixed;
fixing it would be an unrelated edit in a verification pass.

### Test staleness sweep (run independently, not against the slice's file list)

Both shapes `BUILD.md` `### Test staleness a focused run cannot see` names require an **executable**
change — an example-model field added / removed / renamed, or a wire-shape conversion. Instruments A
and B read SAME for all four files against both baselines, so neither shape can have been introduced by
this pass regardless of what any file list says. Staged anchors: `grep -rn 'TODO(spec-028' .` -> no
hits tree-wide.

### What looks solid

- **M1's repair fixed the defect *and* the instrument, which is the part that generalises.** The
  cheapest available discharge was to rewrite two lines and re-run the same three-form probe, which
  would have kept reporting 0 and would have looked identical in the report. Worker 2 instead named why
  the old probe was structurally incapable of seeing the class, put the `\n` inside the pattern, and
  reported the survivor count **rising** from its own earlier reading rather than confirming it. A
  builder correcting its own postcondition upward is the opposite of the failure mode this cycle keeps
  hitting.
- **The `orders/sets.py:258` survivor is the strongest attribution work in this artifact.** It is a
  wrapped join, in one of Slice 2's own sixteen paths, matching the exact class M1 closes — the single
  easiest thing in this tree to mis-grade as a builder's regression. Worker 2 proved it was the other
  cycle's from `git show HEAD:` plus that cycle's own ticked box, left it byte-identical, and named it
  in the report so the record shows it was seen. I re-derived the same attribution independently and
  reached the same place.
- **L4 was re-scoped rather than re-hedged.** "no step of the teardown path can raise" became "nothing
  on the teardown path can raise **OUT of** `clear()`" — a claim about propagation, which is what the
  test asserts, and which is true in the warm state and in the cold-plus-poisoned-parent state alike.
  It also *gained* precision: the `utils/inputs.py::_safe_import` citation makes the "best-effort" half
  gate-checkable instead of asserted, and it is the source of the citation gate's attributable `+2`.
- **L6 re-derived its count instead of carrying mine forward.** The `7` was already right, and Worker 2
  measured it again anyway. That is the correct instinct in a cycle whose recurring defect is a number
  inherited from an instrument nobody re-ran.
- **The concurrent-collision discipline held at three times pass-2's scale.** Worker 2 found six dirty
  paths named by no partition it was handed, **read each diff** instead of assuming, classified all six
  as the other cohort's same-family prose work, reverted nothing, reformatted nothing, and escalated the
  widened ownership question on disk. I spot-verified two of the six independently
  (`examples/fakeshop/apps/kanban/schema.py`'s wrapped-anchor repair and `tests/filters/test_inputs.py`'s
  `Decision-3` -> `spec-027 Decision 3`) and both are unmistakably 027's.
- **Both out-of-scope observations Worker 2 flagged are classified, not missed** — confirmed below with
  a correction to my own instrument, not to its.

### Records to correct (not findings against the diff)

- **R4 — my own `lines? NN` census instrument was wrong, and Worker 2's 14-vs-16 reading is the correct
  one.** My first tree-wide sweep read single=16 / flattened=16 and I nearly recorded the 14/16
  disagreement as closed. The bug was mine: `\s` in `\blines?\s+\d+` **crosses a newline**, so my
  "single-line" pattern was silently a flattened pattern. Re-run with `[ \t]+` it reads
  **line-scoped 14 / flattened 16**, with the two wrapped-only sites exactly where Worker 2 said —
  `tests/mutations/test_sets.py` (`Edge cases line` / `509`, 1073-1074) and
  `tests/optimizer/test_extension.py` (`spec line` / …, 2248). Both cite other cards (`spec-036` and the
  optimizer's Decision 7), both are outside the sixteen, neither was touched. **Classified, not missed.**
  Recorded against myself because it is the ninth instance of this cycle's one recurring defect, and it
  happened to the reviewer, in the pass whose whole subject was instrument blindness.
- **R2 is confirmed again and has moved AGAIN inside this review.** My census at **`2026-08-20T15:15:57Z`**,
  single-line and flattened agreeing at every class: `spec-028` **91**, `spec-028 Decision N` **62**,
  `spec-028 test plan` **6**, `spec-028 DoD N` **2**. Worker 2's reading 13 minutes earlier was
  88 / 59 / 6 / 2. The **+3 is fully attributed and is not this pass's**: `django_strawberry_framework/sets_mixins.py`
  (+2) and `tests/test_sets_mixins.py` (+1), two files that appear in **neither** Worker 2's
  `git status --short` listing **nor** Slice 2's sixteen, both now carrying `spec-027 / spec-028 Decision 8`
  dual-family citations written by the concurrent cohort. Per-file `now`-vs-`HEAD` counts confirm the four
  files this pass touched moved **no** census class in either direction. The dirty set is now **79 paths**
  and a twelfth `027` artifact (`bld-slice-12-027-wrapped_citations_in_specs.md`) has appeared since
  Worker 2's report.
- **R5 — the anchor Slice 3 must protect is `## Definition of done`, not a `### DoD` heading.** The
  citation *form* is `spec-028 DoD N`, but the spec has **no** `### DoD` heading; its top-level headings
  are enumerated at lines 10-990 and the relevant one is `## Definition of done` (line 990). Both `DoD`
  citations are in `django_strawberry_framework/orders/sets.py` (lines 13 and 121), both spell
  `spec-028 DoD 4(c)`, and both resolve correctly — DoD item 4(c) is "**NO `apply(...)` dispatcher**",
  verified verbatim. A protect-list written against `### DoD` would guard a heading that does not exist
  while the real one moved.
- **R1 and R3 are unchanged and still Worker 1's.** My readings corroborate both: the cookbook
  population inside the sixteen is **2**, not the 6 Ruling 2's postcondition states (and
  `orders/sets.py:258` is cohort B converting a third while this cycle ran); and the citation gate has
  now produced six different totals, all exit 0, so only the exit code plus an attributable reading is
  evidence.

### Temp test verification

- `docs/builder/temp-tests/slice-2/test_l4_state_independence.py` — 5 rows. Four parametrized rows
  (`{orders, filters}` x `{warm, cold}`) poison the family `inputs` module **and** the family package and
  call `registry.clear()`, asserting it does not raise; the cold rows first pop
  `{family}.{factories,sets}` from `sys.modules` so `importlib` must resolve the `None`-poisoned parent.
  A fifth row spies on `utils/inputs.py::_safe_import` and asserts
  `clear_generated_input_namespace` makes **exactly 2** calls. `uv run pytest … --no-cov -q` -> **5
  passed**. No `--cov*` flag in any command this pass.
- **Disposition: deleted after use** (file and its `__pycache__`; `git status --short docs/builder/temp-tests`
  is empty). It caught no behavior bug — it **confirmed** L4's re-scoped claim in the one state pass 2
  had measured only at the `_safe_import` level, and re-derived the "exactly two" count by counting
  calls instead of grepping. There is therefore nothing to promote as a defect pin, and the existing
  `::test_clear_tolerates_unimportable_{order,filter}_submodules` rows already exercise the path.
- **The promotable shape, routed to the deferred catalog rather than dropped.** If the maintainer prefers
  the invariant *pinned* rather than *described*, the shape is a `tests/utils/` row asserting
  `_safe_import` returns `None` for a **cold submodule of a poisoned package**, plus a row asserting the
  two-call count. Both are **new executable statements** and cannot land in this slice without
  forfeiting the zero-boundary entitlement the whole verification rests on — the same reasoning pass 2
  recorded, unchanged. Added to `### Notes for Worker 1` item 4.

### Notes for Worker 1 (spec reconciliation)

1. **Slice 3 must re-measure its protect-list at entry and must not read any number out of this
   artifact.** Slice 3 is your own next slice and it rewrites every `### Decision N` heading's prose.
   The census moved **twice inside this single review pass** (88/59/6/2 at 15:02:51Z -> 91/62/6/2 at
   15:15:57Z, the delta fully attributed to the concurrent cohort in two files outside the sixteen), and
   the citation gate has now produced six different totals. **Measure at entry; the number here is a
   timestamped observation, not a contract.** Two additions to the list's *scope*, both new information:
   - the protected anchor for the `DoD N` citation form is **`## Definition of done`**, not a `### DoD`
     heading — there is no `### DoD` heading in the spec (R5 above);
   - `## Test plan` (6 citations) needs protecting alongside the Decision headings, and the concurrent
     cohort is now writing **dual-family `spec-027 / spec-028 Decision 8`** citations into files no pass
     of this cycle has read (`django_strawberry_framework/sets_mixins.py`, `tests/test_sets_mixins.py`).
     Renaming spec-028's `### Decision 8` breaks those too, and they are outside the sixteen.
2. **Escalated (cross-cycle, maintainer's): the wrap-probe blind spot is now certified as satisfied
   inside the OTHER cycle's artifact.** `docs/builder/bld-slice-7-027-raw_line_refs.md:214` states that
   pass "introduced no wrapped citation", and the site it wrote —
   `django_strawberry_framework/orders/sets.py:258` — is a wrapped **join**. Its claim is true of each
   anchor and false of the citation. I did not touch that file or that artifact. Worker 2's item-2
   recommendation is the right correction and I endorse its exact wording: the `check_citations.py`
   gate-extension entry in `### Spec changes made` should say the gate must resolve `path::Symbol`
   **together with** its `#"substring"` anchor as one citation, because a flattened *per-form* probe
   still would not have caught M1. Add one clause: **the join must be probed with the newline inside the
   pattern**, since that is the only shape that expresses it.
3. **The cross-cycle ownership collision has widened again since Worker 2's report.** Worker 2 named six
   further paths and five new `027` artifacts; as of this review the dirty set is **79 paths**, a
   **twelfth** `027` artifact exists (`bld-slice-12-027-wrapped_citations_in_specs.md`), and two of
   Slice 2's **own sixteen** are now carrying the other cohort's hunks — `tests/types/test_base.py`
   (`Decision-4` -> `spec-015 Decision 4`, one line; C1's own site is intact, zero `spec-028 N3`
   occurrences remain) and `django_strawberry_framework/orders/sets.py`. Nothing is lost in either
   direction and every hunk on both sides is prose-only, but the decision passes 2 and 3 asked for is
   now materially larger than four files and `bld-final-028.md`'s deferred-work catalog should carry it
   at this size.
4. **Three additions for `bld-final-028.md` `### Deferred work catalog`:**
   - the two third-party-target wrapped joins deliberately left (`test_library_api.py:8014`,
     `orders/sets.py:258`), with the reason: both cite trees `check_citations.py` is not fail-closed on,
     one is pre-existing and 6,200 lines from the section, one is another cycle's live hunk;
   - one **split-path** wrapped reference at `examples/fakeshop/test_query/test_products_api.py:3334`,
     byte-identical at `HEAD`, outside the sixteen — a shape **both** wrap instruments used in this
     cycle would miss, found only by probing for it deliberately;
   - the promotable `_safe_import` pins from `### Temp test verification` (cold-submodule-of-poisoned-package
     returns `None`; the two-call count), which cannot land in this slice without forfeiting the
     zero-boundary entitlement.
5. **The two out-of-scope wrapped `lines? NN` citations Worker 2 flagged are confirmed classified**
   (`tests/mutations/test_sets.py`, `tests/optimizer/test_extension.py`), and the 14-vs-16 disagreement
   should be read as **classified residue**, not as new. See R4 — my own first instrument read it as
   closed and was wrong.

### Checklist audit

Walked all **22** boxes. **22 ticked, 0 open.** No box is ticked, un-ticked, or re-worded by this pass,
and none needed to be: M1 / L4 / L6 were defects in how three already-landed contracts (C11, C6c, C9)
are **written**, not claims that they did not land, and L5 is a records item. Un-ticking any of them
would mis-describe the diff. Re-confirmed the boxes whose postconditions this pass could have moved:

| Box | Verdict | Basis re-derived this pass |
|---|---|---|
| **C11** | **holds, and M1's form defect is now closed** | both repaired citations unbroken on one line (107 / 103 columns), both symbols exist, both substrings unique inside their symbol and in their file |
| **C6c** | **holds, and L4's accuracy defect is now closed** | four sites, both twins; claim measured true in warm AND cold+poisoned-parent for both families; the two fenced twins byte-identical against both baselines |
| **C9** | **holds, and L6's attribution defect is now closed** | `Seven` re-derived by AST (7 `OrderSet` subclasses), subject correctly scoped to the module, `title: ASC` attributed to the class that has a `title` |
| **C1** | **holds** | zero `spec-028 N3` occurrences; `types/base.py:176-177` / `:205-207` carry the invariant with no citation, despite the file's twin being written by the other cohort mid-review |
| **C5** | **holds** | the over-tick Ruling 1 opened was repaired in pass 2 and re-derived there by AST structure; the embedded "UN-TICKED by Worker 1" note is Worker 1's preserved historical record, not a live un-tick |
| Zero new `spec-028 #"substring"` citations | **holds** | 0 single-line, 0 flattened tree-wide |
| No executable statement changed | **holds** | 16 readings, 2 instruments, 2 baselines, `MISMATCHES: 0` |
| Nothing edited outside the writable paths | **holds** | all four are within the sixteen; every other dirty path attributed to Slice 1, this cycle's artifacts, or the concurrent cohort |
| ruff scoped / no churn | **holds** | `4 files already formatted`, `All checks passed!`, read-only, never `.`, never `--fix` |
| gates | **holds** | `check_citations.py` exit 0 (782); `check_trailing_commas.py --check` exit 0 |

Do-not-touch audit: `tests/test_registry.py::test_clear_tolerates_unimportable_connection_submodule`
and `::test_clear_tolerates_unimportable_relay_module` byte-identical against both baselines;
`examples/fakeshop/test_query/test_glossary_api.py`, `tests/utils/test_strings.py` and
`tests/utils/test_inputs.py` clean; `tests/filters/test_inputs.py` is dirty and is the concurrent
cohort's (`Decision-3` -> `spec-027 Decision 3`, three lines), not Worker 2's; `docs/builder/BUILD.md`,
`ARTIFACT.md`, every `worker-*.md` and every `*-027*.md` untouched by me.

### Review outcome

`review-accepted`.

All four items are settled, each verified by an independent measurement rather than by reading the
build report: **M1** closed at both sites with the dropped glosses confirmed carried, the probe
confirmed genuinely join-aware by a differently-shaped second instrument agreeing at 2, and both
survivors correctly left (one pre-existing and 6,200 lines outside the section, one the concurrent
cohort's live hunk that `AGENTS.md` forbids touching). **L4** re-scoped to a claim that is true in every
state, measured on a four-row warm/cold matrix across both families, with the two-`_safe_import` count
re-derived by counting calls. **L5** discharged the one way `ARTIFACT.md` permits, both false sentences
named, prior entries verifiably unedited. **L6** attributed to the class that has a `title`, with the
count re-derived by AST and its subject checked.

Zero High, zero Medium, zero Low. The zero-executable-change entitlement holds on two instruments
against two reference points, so the mandatory failability re-run floor is empty **by entitlement**,
which is why no boundary is named as re-run and none as accepted on Worker 2's record. Everything
routed to Worker 1 above is either a record to correct, a cross-cycle maintainer decision already in
flight, or a deferred-catalog entry — none of it is a reason to hold this slice.


---

## Final verification (Worker 1, pass 2)

### Summary

`Status: final-accepted`. **All 22 checklist boxes hold, every tick re-derived by this pass rather than
read**, and the zero-executable-change entitlement is confirmed across **all sixteen** authorized paths
(not only pass 3's four) on two instruments against two reference points: **64 readings, 0 mismatches**.
The C5 over-tick this role opened at the first final verification is closed — step 19 landed and the
banner now satisfies both halves of its box — so no box is un-ticked and nothing routes back to a fourth
revision loop.

**Boundary count: zero, and the failability re-run floor is empty BY ENTITLEMENT, not by omission.** A
boundary is an executable expression; the executable token stream of all sixteen paths is identical to
both baselines, so there is no boundary that could owe a proof. `### Failability proofs` reading
`None; this pass introduced no new boundary.` is the correct content in all three build reports, and no
fail-open shape can have landed for the same structural reason. A reader who finds no proof section here
is looking at an entitlement, not a gap. **Hot path: none declared, none owed, none flagged. Floor
verification: scope `none`; no floor venv was built and the shared `.venv` was not mutated by this pass**
(reference only, from [`BUILD.md`][build] `## Floor verification`: Django 5.2.16 on Python 3.10 with
strawberry-graphql 0.316.0).

Everything else raised in pass 3 is a record to correct, a cross-cycle maintainer decision already in
flight, or a deferred-catalog entry. Rulings 9-15 below dispose of each.

### The entitlement, confirmed across all sixteen paths

Two instruments x two baselines x sixteen paths. Instrument A is a docstring-stripped `ast.dump`;
instrument B is a `tokenize` stream with `COMMENT`/`NL` dropped and **only** statement-position (docstring)
`STRING` tokens collapsed, every other literal kept verbatim — so a reworded or relocated non-docstring
string would surface. Pristine references were extracted read-only with `git show` into a scratch path
**outside** the repository; no `git stash` / `checkout` / `restore` / `worktree` at any point in this pass.

```
READINGS: 64  MISMATCHES: 0
```

**Which baseline carries the claim, per path.** `git diff --name-only 5c6fdd71 HEAD` over the sixteen
returns **four** paths, not the three the brief names: `tests/types/test_base.py`,
`tests/test_registry.py`, `examples/fakeshop/test_query/test_library_api.py` — and
`django_strawberry_framework/utils/inputs.py`. For the first three, `8a9840dc` swept this slice's pass-1
work, so `git show HEAD:<path>` is post-Slice-2 content and the HEAD reading is **trivially true**; only
the `5c6fdd71` column proves anything there. The fourth is different and is worth naming so no later pass
mis-reads it: `utils/inputs.py`'s `5c6fdd71`->`HEAD` delta is a single **`spec-027`** prose hunk in
`create_dynamic_set_class`'s docstring (`Spec-027 line 247` -> `Spec-027`), **not** Slice-2 work, so both
of its baselines are non-trivial. For the remaining twelve paths HEAD and `5c6fdd71` are the same content
and both readings are non-trivial. I ran `5c6fdd71` for all sixteen rather than only the swept subset, so
**every path has at least one non-trivial baseline** and the entitlement does not rest anywhere on a
trivial reading.

Both instruments agree at both baselines for every file, so the entitlement holds. It has now been proved
on **five** distinct instruments by three roles across four passes, and no reading has ever dissented.

### Checklist audit — all 22 boxes, every tick re-derived

Measured against the **current files**, never against a diff or a prior pass's number: four of the sixteen
differ from HEAD for reasons outside this slice, and two of the sixteen now carry the concurrent cohort's
hunks, so present-state reading is the only valid instrument.

| Box | Verdict | Re-derivation by this pass |
|---|---|---|
| C1 | **holds** | `(spec-028 N3)` -> **0** tree-wide; `types/base.py:149` and `tests/types/test_base.py:760` carry the invariant with no citation. The only hunk in `test_base.py` vs HEAD is the other cohort's `Decision-4` -> `spec-015 Decision 4` at 716, 40 lines clear of C1's site |
| C2 | **holds** | flattened `raw-line-citation` over the sixteen -> **2**, both the ruled cookbook pair; the wrapped `line 1038`/`1039` pair is gone. `orders/inputs.py`'s `line 452` removal is a reflow — `spec-028 Decision 3` survives on the joined line |
| C3 | **holds** | flattened `Test-N-ordinal` over the sixteen -> **0**; six unbroken `test_library_api.py::<name>` citations in `library/orders.py`, every name present in the AST enumeration below |
| C3b | **holds** | `grep '{ shelf: {'` -> five `filter:` sites plus exactly **two** `orderBy:` sites, at 1869 (`..._order_by_forward_fk_relation`) and 2379 (`..._order_by_multi_field_priority`) — the two names cited. 4 -> 2 correct |
| C4 | **holds** | `orders/base.py:3` reads `Layer 1`; `orders/factories.py:3` reads `Layer 5` and its `git diff 5c6fdd71` carries no `Layer 5` change (the file's only non-C12 hunk is the other cohort's `Decision 4 H1` -> `spec-027 Decision 4` at line 9) |
| **C5** | **holds — the over-tick is CLOSED** | banner at 1738-1747 carries `16 test functions / 19 test rows`, the parametrized derivation, the P1-B source, **and both test names**. Re-derived from the AST, not by grep: module-level `test_*` nodes whose earliest decorator-or-def line falls in [1738, 2484) -> **16**; exactly one `@pytest.mark.parametrize` with **4** argvalues -> **19 rows**. Both named tests are in range (1922, 1986) |
| C6 | **holds** | order twin's docstring and inline comment repaired and mirroring the filter twin; `registry.py` still carries **no** `except ImportError` |
| C6b | **holds** | record re-read: anchor count taken before the copy, `md5`, the exact mutation, `1 failed / 79 passed`, the failing node id listed, **0** collection errors, `cmp`-proved revert. Confirmed the tree carries no residue: `grep -c '_reintroduced' registry.py` -> **0** and `registry.py` is absent from `git status` |
| C7 | **holds** | flattened `path-NN-citation` over the sixteen -> **0**; seven `Covers` docstrings in the block, all `path::Symbol` (+ `#"anchor"` where the symbol is not the target) |
| C7b | **holds** | `grep -E '\(lines? [0-9]'` in `tests/orders/test_inputs.py` -> nothing; both twins' full names survive |
| C7c | **holds** | `::test_clear_order_input_namespace_tolerates_unimportable_submodules` states the two `utils/inputs.py::_safe_import` lookups and the `is not None` skips. The only surviving `except ImportError` claims in `tests/test_registry.py` are 1436 (`unregister`, out of scope) and the two fenced twins |
| C8 | **holds** | `spec-028 + Decision` -> **0**; `library/orders.py:14` reads `(spec-028 Decision 3 Layer 2)` |
| **C6c** | **holds; L4's accuracy defect closed** | both twins carry the narrowed clause plus `(``utils/inputs.py::_safe_import``)` and the propagation-scoped conclusion; the diff is a reflow — `(spec-027 Decision 9)` and `(spec-028 Decision 9)` both survive, so no `027` hunk was reverted |
| **C9** | **holds; L6's attribution closed** | `Seven ordersets`; `title: ASC` attributed to `IssueOrder` alone, `PeriodicalOrder` named as the target `IssueOrder.periodical` reaches |
| **C10** | **holds** | prose `line NN` in `tests/orders/` -> **2**, both cookbook, both **byte-identical to `5c6fdd71`** (verified by extracting the two lines from `git show 5c6fdd71:` and comparing: `test_sets.py:169` and `test_factories.py:251`, identical text at identical line numbers). 9 first-party sites retired |
| **C11** | **holds; M1's form defect closed** | 12 -> **0** raw `path:NN`; both repaired citations unbroken, measured **107** and **103** columns; the three sync/async rows now say one shared helper is reached through two entry points |
| **C12** | **holds** | bare `Spec (Decision\|DoD\|Edge) N` -> **0** in the sixteen and **1** tree-wide (`tests/types/test_relay_interfaces.py`, `spec-015`, out of family), single-line **==** flattened. The reflowed `spec-028 Decision 8 step 6` sits unbroken at `orders/sets.py:19` and `:455` |
| Zero new `spec-028 #"substring"` | **holds** | **0** single-line and **0** flattened, tree-wide |
| No executable statement changed | **holds** | 64 readings, 2 instruments, 2 baselines, all sixteen paths, `MISMATCHES: 0` |
| Nothing edited outside the writable paths | **holds** | every do-not-touch path clean (`terms.csv`, `GLOSSARY.md`, `KANBAN.md`/`.html`, `CHANGELOG.md`, `docs/TREE.md`, `README.md`, `TODAY.md`, `db.sqlite3`, `BUILD.md`, `ARTIFACT.md`, all four `worker-*.md`); `docs/builder/temp-tests/slice-2/` empty; every dirty path outside the sixteen carries the other cohort's voice on inspection |
| ruff scoped / no churn | **holds** | `16 files already formatted`; `All checks passed!`; read-only, never `.`, never `--fix`. `git diff --check` over the sixteen exit 0 |
| gates | **holds** | `check_citations.py` -> `OK: 782 citations resolve`, **exit 0**; `check_trailing_commas.py --check <the sixteen>` exit 0 |

**No box is un-ticked. No box is left `- [ ]`.** The C5 box's embedded "UN-TICKED" sentence is pass 1's
preserved record; I appended a closing clause to it in the Plan section so a reader cannot mistake the
history for a live state — the only edit this pass makes to an earlier section, and one
[`ARTIFACT.md`][artifact] provides for by making the checklist the custodian's to audit across passes.

**Citation resolution, run by hand because the gate cannot.** `check_citations.py` is `path::Symbol`-only
and line-scoped, so I resolved every `` ``path.py::Symbol`` `` (+ optional `#"anchor"`) in the sixteen
myself: parse the target, extract the symbol's source segment, assert the anchor occurs exactly once
inside it. **98 citations; every in-family target resolves and every anchor is unique in its symbol.**
Two instrument artifacts, neither a defect: third-party `django_graphene_filters/` targets do not exist in
this repo (by design — the gate is not fail-closed on them), and module-level constants
(`INPUTS_MODULE_PATH`, `_materialized_names`, `_pascalize_token`) are not `def`/`class` nodes so a
symbol-walker cannot see them. One case deserves naming because it looks like a failure and is not:
`tests/orders/test_base.py:185` cites `orders/base.py::RelatedOrder.orderset` #"self._set_target(value)",
and `orderset` is a **property pair** — two `FunctionDef`s of that name. A first-match walker lands on the
getter and reports the anchor absent; the anchor is at line 85 inside the `@orderset.setter` half, is the
**only** occurrence in the file, and is exactly what disambiguates which half is meant. Worker 3 reached
the same reading in pass 2. The citation is correct; the naive resolver is what is wrong.

### Ruling 9 — the census this artifact hands forward: a timestamped observation, never a contract

**Worker 3's recommendation is adopted in full: Slice 3 re-measures at entry and reads no number out of
this artifact.** My own reading, taken at `2026-08-20T15:28:26Z`, single-line and flattened agreeing at
every class: `spec-028` **91**, `spec-028 Decision N` **62**, `spec-028 test plan` **6**,
`spec-028 DoD N` **2**, `spec-028[^)]*#"` **0**. That reproduces Worker 3's last pass-3 reading
(15:15:57Z) exactly and stands 13 minutes later, so the `+3` it attributed to the concurrent cohort in
`sets_mixins.py` / `tests/test_sets_mixins.py` is confirmed and has settled — I verified those files
carry three `spec-027 / spec-028 Decision 8` dual-family additions, and neither file is in the sixteen.

The ground for the ruling is not that the number is wrong. **It is that the number's referent is a tree a
second cycle is actively editing in the same citation family**, so any figure written here is stale the
moment a cohort commits, and Slice 3's whole job is to rewrite the headings those citations point at. Five
readings inside this one slice — 67, 83, 88, 91, and 62-not-59 for the Decision class — all correct when
taken. A protect-list built on a stale count protects the wrong population, and a heading rename with
every gate green is exactly the silent breakage this cycle exists to close.

**What Slice 3 inherits is therefore a method and a scope, not a figure**:

- measure the four classes at entry on a **whitespace-flattened** probe, and difference it against the
  single-line reading; a disagreement means a wrapped citation, and this cycle has hit that nine times;
- the protected anchors are `### Decision N`, `## Test plan`, `## Edge cases and constraints`, and
  `## Definition of done`;
- the population extends **outside** the sixteen. Measured this pass: **11** `spec-028
  (Decision|DoD|test plan)` sites live in five files no pass of this cycle read —
  `django_strawberry_framework/types/finalizer.py` (5, `Decision 6`),
  `django_strawberry_framework/sets_mixins.py` (2, dual-family `Decision 8`),
  `examples/fakeshop/apps/library/orders_genre.py` (2), `tests/orders/test_finalizer.py` (1), and
  `tests/test_sets_mixins.py` (1, dual-family). That file list is the durable half of this ruling; the
  count beside it is not.

### Ruling 10 — the two protect-list corrections are confirmed, and both are adopted

**R5 is right and I re-derived it from the spec rather than from the review.** The spec's top-level
headings are enumerable (`grep -n '^## '`) and there is **no `### DoD` heading** — `grep -n '^### DoD'`
returns nothing. The anchor is **`## Definition of done`** at spec line 990. Both `spec-028 DoD 4(c)`
citations are in `django_strawberry_framework/orders/sets.py` (lines 13 and 121), and both resolve
correctly: DoD item 4(c) reads **"NO `apply(...)` dispatcher"**, verified verbatim against line 997. A
protect-list written against `### DoD` would have guarded a heading that does not exist while the real one
moved — the same shape of defect as a count that is right in its digit and wrong in its subject.

**The dual-family widening is confirmed and is the more consequential half.** The concurrent cohort is
writing `spec-027 / spec-028 Decision 8` into `sets_mixins.py` and `tests/test_sets_mixins.py`, and those
citations break if spec-028's `### Decision 8` heading is renamed even though neither file is in any
partition of this cycle. Folded into Ruling 9's file list above so Slice 3 meets it as scope rather than as
a surprise.

### Ruling 11 — `bld-slice-7-027:214` belongs in this cycle's record, routed to the maintainer

**Verified independently, read-only, before ruling.** The claim at
`docs/builder/bld-slice-7-027-raw_line_refs.md:214` is *"This pass introduced no wrapped citation: the
three new `#"…"` forms … all open and close on one line."* True of each **anchor**. The site that pass
wrote is `django_strawberry_framework/orders/sets.py` 258-259, where
`` ``django_graphene_filters/orderset.py::AdvancedOrderSet.get_fields`` `` ends 258 and
`#"Works for both dict (iterates keys)"` opens 259 — a wrapped **join**, which is precisely the class M1
named here. `git show HEAD:` carries `# Cookbook line 279-280: "Works for both dict (iterates keys) and`
at that region, so the hunk is new and is that cohort's.

**Disposition: it stays in this cycle's record, in `bld-final-028.md`'s `### Deferred work catalog`, and
nowhere else.** Three reasons, in order of weight:

1. **No worker may edit it.** That artifact is on this cycle's do-not-touch list and belongs to a cycle
   whose review is not ours. Correcting another cycle's postcondition would be a worker asserting a
   verdict on work this cycle never reviewed.
2. **The maintainer is the only party who can act on it**, because the fix is either a correction in that
   cycle's artifact or a gate extension in `scripts/check_citations.py` — and the gate extension is
   already a catalogued deferral of ours, so the two arrive together or the next reader gets half.
3. **It is the strongest available evidence for the gate-extension proposal**, which is the durable
   outcome. One cycle's blind spot is an anecdote; the same blind spot certified as *satisfied* inside a
   second cycle's artifact, by a different agent, on a different card, is a measurement. Dropping it
   because it is out of scope would discard the only cross-cycle datapoint the proposal has.

I adopt Worker 2's and Worker 3's joint wording for the catalog entry: the gate must match
whitespace-flattened **and** must resolve `path::Symbol` together with its `#"substring"` anchor as one
citation, **with the newline inside the pattern**, because a flattened *per-form* probe still would not
have caught M1.

### Ruling 12 — the split-path wrap at `test_products_api.py:3334`: deferred, with its shape named

**Verified, then dispositioned.** My own probe found it independently: `` `tests/rest_framework/ ``ends one
line and `` test_resolvers.py` `` opens the next, a bare wrapped **path** with no `::Symbol` and no anchor.
`git show HEAD:` carries the identical two lines at **3330-3331**; the working tree has them at 3334-3335,
shifted by the other cohort's edits above. So it is byte-identical at HEAD, pre-existing, in a file that is
**not** one of Slice 2's sixteen and is the concurrent cohort's.

**Deferred to the catalog, not repaired**, and the reason is the shape rather than the ownership: it is a
**third** wrap grammar, distinct from both classes this cycle closed. C2's site wrapped a `spec … line NN`
phrase; M1's sites wrapped the join between a symbol and its anchor; this one wraps the **path token
itself**, mid-segment, at a `/`. Both wrap instruments used in this cycle would miss it — Worker 3 found it
only by probing for it deliberately, and my own instrument found it only because I wrote a `split-path`
class for exactly that reason. That makes it the third required clause on the gate-extension card, and the
card is where it earns its keep. Repairing one occurrence in another cohort's file would close the
occurrence and leave the class.

### Ruling 13 — R4 is the cycle's standing instrument lesson, and it is recorded as such

**Re-derived: Worker 3's self-correction is right, Worker 2's 14-vs-16 reading is right, and Worker 3's
first sweep was wrong for the reason it names.** `\s` in Python's `re` matches `\n`, so a pattern written
as the "single-line" control — `\blines?\s+\d+` — is silently a flattened pattern and cannot disagree with
its own flattened counterpart. Re-run with `[ \t]+` as the line-scoped form and `\s+` only after
flattening, my tree-wide reading is **line-scoped 14 / flattened 16**, with exactly two wrapped-only sites:
`tests/mutations/test_sets.py` (3 vs 4) and `tests/optimizer/test_extension.py` (3 vs 4). Both cite other
cards, both are outside the sixteen, neither was touched. **Classified residue, not new.**

**Worth recording as the cycle's standing lesson, and this is the form it should take:** a whitespace class
that crosses a newline cannot serve as the *control* in a wrapped-citation differencer, because it makes
the two readings the same instrument. This is the ninth under-measurement in this cycle and the only one
that hit the reviewer, in the pass whose entire subject was instrument blindness — which is the point. The
lesson is not "run the flattened probe"; every pass here did that. It is that **a differencer proves
nothing unless its two halves are provably different instruments**, and `\s` vs `\s` is one instrument
written twice. Carried to my memory file and named in the catalog beside the gate-extension card, whose
own control this constrains.

### Ruling 14 — the `_safe_import` promotable pins: routing to the deferred catalog CONFIRMED

Confirmed, and the reasoning is the entitlement rather than a preference. Both promotable shapes —
`_safe_import` returns `None` for a **cold submodule of a poisoned package**, and
`clear_generated_input_namespace` makes **exactly two** `_safe_import` calls — are new test rows, i.e. new
**executable statements**. Landing either would (a) break the zero-executable-change property on which
every verification in this slice rests, across four passes and five instruments, and (b) newly owe the
boundary machinery this slice is entitled to skip: a row asserting a `None` return on an unimportable
target pins a guard, which is a boundary, which owes a mutate / run / count-rows / revert / byte-compare
loop. The target home is `tests/utils/`, outside the writable sixteen either way.

**Nothing is lost by deferring, because nothing is unpinned.** Worker 3's temp test measured the claim on a
four-row warm/cold matrix across both families and it passed in every state; what the catalog carries
forward is the choice to *pin* the invariant rather than *describe* it. Routed as a card, with both row
shapes and their home stated, so the next reader can write them without re-deriving the mechanism.

### Ruling 15 — the cross-cycle collision: attributed, nothing reverted, escalated at its current size

The dirty set is **80 paths** at this pass's reading, with **12** `027` artifacts on disk. Two of Slice 2's
own sixteen carry the other cohort's hunks and I attributed both from source rather than from a report:
`tests/types/test_base.py` (one line, `Decision-4` -> `spec-015 Decision 4` at 716; C1's site at 757-762
intact and `(spec-028 N3)` still 0 tree-wide) and `django_strawberry_framework/orders/sets.py` (the four
cookbook conversions plus the wrapped join of Ruling 11; all six C12 respellings present, the reflowed
`Decision 8 step 6` unbroken, the file AST- and token-identical to both baselines).

**Ruling 2's cookbook carve-out is overtaken for four of its six sites and I correct the record rather than
the tree.** The postcondition it wrote — "exactly the 6 named cookbook refs remain" — no longer describes
this tree: **2** remain, both in `tests/orders/`, both byte-identical to `5c6fdd71` as ruled (verified line
by line against `git show 5c6fdd71:`). The missing four are `orders/sets.py`'s, converted by cohort B to
the `django_graphene_filters/orderset.py::Symbol` form Ruling 2 explicitly declined, and that cohort's own
artifact ticks all four as its work. `AGENTS.md` #"Files dirty at task start" and the maintainer's standing
instruction for this cycle both forbid touching them. **A postcondition another cycle moved out from under
this slice is a record to correct, not a builder to fault** — and `bld-final-028.md`'s catalog entry must
read **two** cookbook refs left with reason, not six, or the next reader hunts four sites that no longer
exist and may re-open a ruling that has already been overtaken.

**No `027` hunk was reverted, reformatted, or reconciled by this pass, and I checked rather than assumed:**
every `-` line in `git diff HEAD` over the sixteen that mentions `spec-027`, `cookbook`, or
`django_graphene_filters` was traced to its `+` counterpart, and all of them are reflows in which the cited
content survives (`orders/base.py`'s `per spec-028` / `Decision 2` unwrap, `orders/inputs.py`'s `line 452`
drop, the two registry twins' C6c narrowing where both `(spec-027 Decision 9)` and `(spec-028 Decision 9)`
survive, `tests/orders/test_base.py`'s setter docstring) or are cohort B's own conversions in
`orders/sets.py`. Not one citation was deleted without its replacement landing on the joined line.

The ownership question is the maintainer's and is now materially larger than the four files pass 2 raised.
Carried at its current size to the catalog.

### Slice-local checks, run by this pass

| Check | Reading |
|---|---|
| join-aware wrap probe, repo-wide `.py`, **newline inside the pattern** | strict join form **0**; loose form **2**, exactly the two classified survivors (`orders/sets.py:258`, `test_library_api.py:8014`), both third-party targets |
| split-path / split-symbol / gap-join wrap classes, repo-wide | split-path **1** (`test_products_api.py:3334`, Ruling 12); split-symbol **0**; gap-join **0** |
| flattened multi-class citation probe, over all sixteen | `raw-line-citation` **2** (cookbook), `path-NN-citation` **0**, `Test-N-ordinal` **0**, `bare-Spec-Decision` **0**, `spec-028 #"sub"` **0**; `review-item-id` **3** (`spec-039 P2`, `spec-040 D6` in `utils/inputs.py` — other cards', deliberately left) |
| flattened bare-`Spec` probe, tree-wide | **1**, the `spec-015` site; single-line **==** flattened |
| by-hand citation resolver over the sixteen | **98** citations, every in-family target and anchor resolves |
| `uv run python scripts/check_citations.py` | `OK: 782 citations resolve (705 in 422 .py files, 77 in KANBAN.md)`, **exit 0** — the criterion is the exit code (readings this slice: 758 / 772 / 779 / 780 / 782 / 782) |
| `uv run python scripts/check_trailing_commas.py --check <the sixteen>` | exit 0 |
| `uv run ruff format --check <the sixteen>` (never `.`, never `--fix`) | `16 files already formatted` |
| `uv run ruff check <the sixteen>` (never `.`, never `--fix`) | `All checks passed!` |
| `git diff --check` over the sixteen | exit 0 |
| zero-executable-change | 64 readings, 2 instruments, 2 baselines, `MISMATCHES: 0` |
| focused collection, no `--cov*` | `tests/orders/ tests/test_registry.py tests/types/test_base.py` -> **389 collected, 0 errors**; `test_library_api.py examples/fakeshop/apps/library` -> **207 collected, 0 errors** |
| fenced twins byte-identical | `::test_clear_tolerates_unimportable_connection_submodule` (1371 bytes) and `::test_clear_tolerates_unimportable_relay_module` (1444 bytes), extracted by AST bounds, identical against **both** `HEAD` and `5c6fdd71` |
| staged anchors | `grep -rn 'TODO(spec-028' .` -> no hits in source or tests (the only two hits are prose inside this artifact) |
| C6b mutation residue | `grep -c '_reintroduced' registry.py` -> **0**; `registry.py` absent from `git status`; `git diff HEAD --stat` empty |
| do-not-touch audit | all fifteen fenced paths clean; `docs/builder/temp-tests/slice-2/` empty (Worker 3's temp tests deleted as recorded) |
| `git status --short` | 80 paths; the sixteen plus Slice 1's spec + rationale plus this cycle's three artifacts are ours, every other path carries the other cohort's voice on inspection (spot-checked `filters/inputs.py`, `tests/mutations/test_sets.py`, `sets_mixins.py`) |

No `pytest` was run as routine slice work; the two invocations are `--collect-only`, and **no `--cov*`
flag was passed in any command this pass**. No `git stash` / `checkout` / `restore` / `worktree`, no
commit, no branch, no amend. No `.py` was edited by this pass; no spec or rationale edit was made.

### DRY check across this slice and prior accepted slices

**No new duplication, and structurally none possible**: zero executable tokens changed across sixteen
paths on two instruments against two baselines, so there is no helper, constant, branch, or literal
introduced to consolidate. The two prose symmetries in the diff are the fix rather than duplication —
the C6c/L4 narrowing is deliberately one story across two twins (Ruling 5's shape), and `utils/inputs.py`'s
two C12 sites use one decided wording at both. Slice 1 moved `.md` text only and shares no code surface.

**The deferred existence challenge stays deferred and I do not reopen it.** Ruling 7's reasoning is
untouched by anything in passes 2-3: every resolution path changes executable statements and forfeits the
entitlement, and both halves sit outside the writable set. Worker 3's pass-2 observation that
`OrderSet._apply_orderings`'s two guards are each pinned twice over one implementation belongs in the
**same** maintainer look as rows 1-2, not a separate one; folded into the catalog entry below.

### Spec changes made (Worker 1 only)

**No spec edit this pass, and none owed.** `docs/SPECS/spec-028-orders-0_0_8.md` and its rationale
companion are Slice 3's and Slice 3 has not run; mixing its work into a verification pass would leave this
artifact describing a contract nobody reviewed. Per-spawn status-line re-verification done: lines 1-8 read
as a shipped-state record (`Shipped in 0.0.8`, `Status: shipped in 0.0.8`, Owner, Predecessors), the
rationale-companion pointer Slice 1 added resolves on disk, and nothing Slice 2 landed falsifies any of it.

**Deferral reasons for boxes left `- [ ]`: none. All 22 boxes are `- [x]` and every tick was re-derived
above.** C5's re-opened box is closed by step 19; C6c, C9, C10, C11 and C12 all landed and hold.

**Carried to `bld-final-028.md` `### Deferred work catalog`** — the authoritative list, superseding the
first final verification's where they differ, each stated so the next reader can act without re-deriving:

1. **Two upstream-cookbook line refs left with reason** (`tests/orders/test_sets.py:169` #"per cookbook
   line 280", `tests/orders/test_factories.py:251` #"cookbook lines 124-130"), byte-identical to
   `5c6fdd71`. Ruling 2's ground stands for these two: rule 27's remedy is `path::QualifiedName`, the
   target is an unvendored, unpinned third-party checkout at `~/projects/django-graphene-filters/`, and
   `check_citations.py` is first-party-only — so a rewrite buys a citation the gate still cannot resolve
   whose truth depends on an external version. **Corrected from "six" to "two":** the other four, in
   `orders/sets.py`, were converted by the concurrent `spec-027` cohort B during this cycle (Ruling 15).
   Do not re-open without pinning the cookbook.
2. **The `scripts/check_citations.py` gate extension** — flag `\blines? \d+` and `[\w./]+\.py:\d+` in
   first-party `.py`, and the bare `Spec (Decision|DoD|Edge)` form. Three constraints on the instrument,
   each earned by a measured miss in this cycle: it must match **whitespace-flattened**; it must resolve
   `path::Symbol` **together with** its `#"substring"` anchor as **one** citation, **with the newline
   inside the pattern** (a flattened *per-form* probe reads both halves of a wrapped citation as intact —
   that is M1); and it must also catch a **path token split mid-segment at a `/`** (Ruling 12's third
   grammar, which both of this cycle's wrap instruments miss). Its differencer's two halves must be
   provably different instruments — see item 3. Would have caught every C2, C7, C10, C11 and M1 site.
3. **Standing instrument lesson (Ruling 13).** A whitespace class that crosses a newline cannot serve as
   the line-scoped control in a wrapped-citation differencer: `\s` matches `\n`, so `\s`-vs-flattened is
   one instrument written twice and can never disagree. Use `[ \t]+` for the line-scoped half. Nine
   under-measurements in this cycle, the last one the reviewer's own.
4. **`bld-slice-7-027-raw_line_refs.md:214` certifies "no wrapped citation introduced" while the site it
   wrote (`django_strawberry_framework/orders/sets.py` 258-259) is a wrapped join** (Ruling 11). Another
   cycle's artifact; no worker of this cycle may edit it. Maintainer's to correct there, and the strongest
   cross-cycle evidence for item 2.
5. **One split-path wrapped reference at `examples/fakeshop/test_query/test_products_api.py:3334**
   (`` `tests/rest_framework/ `` / newline / `` test_resolvers.py` ``), byte-identical at `HEAD` (there at
   line 3330), outside the sixteen, the concurrent cohort's file. The third wrap grammar; folded into
   item 2 as a required clause (Ruling 12).
6. **Two third-party-target wrapped joins deliberately left**: `test_library_api.py:8014` (Django's
   `related_descriptors.py::_filter_prefetch_queryset`, pre-existing, ~6,200 lines outside the spec-028
   section's 1738-2484 bounds) and `orders/sets.py:258` (the cookbook, and the other cycle's live hunk).
   Both cite trees `check_citations.py` is not fail-closed on.
7. **The tree-wide raw-line-citation residue outside this cycle's paths** — corrected inventory at
   `### Notes for Worker 1` note 7, plus the two wrapped-only sites Ruling 13 classifies
   (`tests/mutations/test_sets.py`, `tests/optimizer/test_extension.py`). Tree-wide reading: line-scoped
   14 / flattened 16.
8. **The two-of-four `except ImportError` twins in `tests/test_registry.py`** — maintainer decision, note
   6, now narrower: after C6c the file carries two accurate twins and two
   (`::test_clear_tolerates_unimportable_connection_submodule`,
   `::test_clear_tolerates_unimportable_relay_module`) still on the original false premise, fenced to
   `spec-030-connection_field-0_0_9` P3b and `spec-032` Decision 8. Both proved byte-identical against
   both baselines by this pass.
9. **The DRY existence challenge, both halves** (Ruling 7, unchanged). Rows 1-2 — diamond dedup and
   clear-namespace tolerance, each pinned three times over one single-sited `utils/` implementation with a
   family-neutral pin already in place — are a **contract-level maintainer decision** whose higher-quality
   fix is a deletion of the two family copies, precedent D13; `worker-3.md` reserves the delete call.
   **`OrderSet._apply_orderings`'s two guards, each pinned twice over one helper through `apply_sync` and
   `apply_async`, belong in the SAME look** — same family, not a separate item. Row 3 —
   `utils/strings.py::graphql_camel_name` #"if not core:" has **no** family-neutral pin and its only
   coverage rides two family aliases, so inlining or renaming either alias silently retires the last pin
   while `fail_under = 100` stays green because the other copy still executes the line — is a **card in
   its own right** and the one I would action first. Cheap fix, opposite direction from rows 1-2: add the
   `""` / `"_"` / `"__"` rows to `tests/utils/test_strings.py` beside the existing
   `pascal_case("")` / `pascal_case("_")` pair. All of it changes executable statements, which is why none
   of it could land in this slice.
10. **The promotable `_safe_import` pins** (Ruling 14) — a `tests/utils/` row asserting `_safe_import`
    returns `None` for a **cold submodule of a poisoned package**, plus a row asserting
    `clear_generated_input_namespace` makes **exactly two** calls. New executable statements, so they
    forfeit the entitlement; home is outside the sixteen either way. The invariant is currently *described*
    accurately and measured green in all four warm/cold x family states — the card is to *pin* it.
11. **Two out-of-family review-item ids in a file this slice edited** — `django_strawberry_framework/utils/inputs.py`
    carries `spec-039 P2` and `spec-040 D6` (3 occurrences, measured again this pass). C1's exact defect
    class, left because they are claims about two cards this cycle never verified — the same ground that
    fences the connection and relay registry twins.
12. **The cross-cycle ownership collision, at its current size** (Ruling 15). 80 dirty paths, 12 `027`
    artifacts, two of Slice 2's own sixteen carrying the other cohort's hunks, and both cycles discharging
    the same defect taxonomy with independent censuses. Nothing lost in either direction and every hunk on
    both sides prose-only, but the partition question is the maintainer's and it is live.
13. **`8a9840dc` carries three `spec-028` hunks under a `spec-027` commit message**, so
    `git diff HEAD -- <path>` is empty of pass-1 work for `tests/types/test_base.py`,
    `tests/test_registry.py` and `examples/fakeshop/test_query/test_library_api.py`. Read those by present
    state or against `5c6fdd71`. Maintainer's to resolve; no worker amended, re-staged, or force-pushed.
14. **A banner count is unmaintained by construction** (note 8, unchanged) — step 19 made C5's banner
    accurate, named, and derivable, not durable. The alternative, if the maintainer prefers it, is to drop
    the count and let the banner name only the contract.
15. **Two plan-text defects, unfixed because their files are fenced or not mine**: Worker 0's plan
    misquotes `BUILD.md` `### When to run the helper during build` for Worker 3 (L3 — it adds a
    logic-added qualifier the rule does not have, which would license a real skip in a future cycle whose
    `types/` edit *does* add logic), and `### Partition correction 1`'s M1/M2 measurements are superseded
    by Rulings 2 and 3.
16. **Slice 3's protect-list scope** (Rulings 9 and 10) — anchors `### Decision N`, `## Test plan`,
    `## Edge cases and constraints`, `## Definition of done` (there is **no** `### DoD` heading); and 11
    in-family citations live outside the sixteen, in `types/finalizer.py`, `sets_mixins.py`,
    `library/orders_genre.py`, `tests/orders/test_finalizer.py` and `tests/test_sets_mixins.py`, two of
    them dual-family `spec-027 / spec-028` sites the concurrent cohort wrote. Re-measure at entry; read no
    number out of this artifact.

### Final status

`final-accepted`.

Twenty-two boxes, twenty-two ticks, every one re-derived from the current files by this pass. The
zero-executable-change entitlement holds across **all sixteen** authorized paths on two instruments
against two reference points — 64 readings, 0 mismatches — with every path carrying at least one
non-trivial baseline, so **boundary count zero is confirmed and the failability re-run floor is empty by
entitlement, not by omission**. No hot-path number is owed and none is missing; floor-verification scope is
`none` and no floor venv was built. Both gates green on their exit codes, ruff clean scoped to the sixteen,
no collateral churn attributable to this slice, no `027` hunk reverted, and every fenced path untouched.

Nothing remaining is a defect in the diff. Sixteen items are routed to `bld-final-028.md`'s deferred-work
catalog, each with enough specificity to act on without re-deriving it; two of those are cross-cycle
maintainer decisions this cycle can only record. Worker 0 marks the Slice 2 checkbox and dispatches
Slice 3's planning pass.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[artifact]: ARTIFACT.md
[build]: BUILD.md
[build-028]: build-028-orders-0_0_8.md
[worker-1]: worker-1.md
[worker-3]: worker-3.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
