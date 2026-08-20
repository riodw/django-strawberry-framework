# Build: Slice 2 — Retire the stale "only `SET_NULL` in the example tree" claims

Spec reference: `docs/SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md` (whole file, 3,668 bytes after Slice 1; the claim this slice retires lives in the `## Other` bullet at line 27 and is Slice 3's to fix on the spec side)
Status: final-accepted

Build-plan declarations, restated here because this artifact is the contract Workers 2 and 3 read:

- **Ownership partition:** none. Sequential slices; this is the only slice of the `026` cycle with a Worker 2 / Worker 3 cycle.
- **Hot-path declaration:** none. This slice edits comment and docstring text only. Nothing it touches runs per request, per resolver, or per row, so no hot-path budget is owed and Worker 2 writes `Not applicable; plan declares no hot path.`
- **Floor-verification scope:** none. No Django / Strawberry / channels integration seam is touched. Worker 2 writes `Not applicable; plan declares floor-verification scope none.`
- **Failability proofs: exempt, deliberately.** `docs/builder/BUILD.md` `### What needs a proof, and what does not` scopes the obligation to a new boundary, guard, gate, or rejection path. This slice introduces none — no branch, no validation, no rejection path, no behavior change of any kind. Worker 2 writes `None; this pass introduced no new boundary.` and must not invent a mutation to prove; Worker 3 must not read the absence as an omission.
- **Boundary count (`worker-1.md` `### Boundary count is a split trigger`):** 0 new guards, caps, rejection paths, or validation branches. Split question answered: no split. The slice's whole diff is four prose passages in two files that make one claim between them; splitting it would put halves of one claim in different passes, which is the defect being fixed.

## Plan (Worker 1)

### The claim being retired, re-derived

Worker 0's finding `D2` is a measurement, not a hypothesis, and this pass re-derived every number in it rather than inheriting it.

| Measurement | Command | Result |
| --- | --- | --- |
| `on_delete=models.SET_NULL` occurrences in example models at `HEAD` | `git grep -o 'on_delete=models.SET_NULL' -- 'examples/fakeshop/apps/*/models.py' \| wc -l` | **4** |
| the same at the ship commit | `git grep -o 'on_delete=models.SET_NULL' 2701eb88 -- 'examples/fakeshop/apps/*/models.py' \| wc -l` | **1** |
| example apps that existed at the ship commit | `git ls-tree --name-only 2701eb88 examples/fakeshop/apps/` | `library`, `products`, `scalars` (no `kanban`) |

Occurrences are counted with `grep -o | wc -l`, not `grep -c`: `grep -c` counts matching **lines**, which is a different population and has produced wrong numbers in this repo before.

The four sites at `HEAD`, each read in source:

1. `examples/fakeshop/apps/kanban/models.py` #"related_name=\"verified_items\"" — `CardItem.verified_by` -> `Actor`. Cross-model.
2. `examples/fakeshop/apps/kanban/models.py` #"related_name=\"superseded_by_set\"" — `Decision.supersedes` -> `"self"`. **Intra-model self-FK**, so `SET_NULL` is no longer even exclusively a cross-model shape in the tree.
3. `examples/fakeshop/apps/scalars/models.py::ScalarSpecimen` #"related_name=\"tagged_specimens\"" — `tag` -> `ScalarSpecimenTag`, the O6 `Prefetch`-downgrade substrate. Cross-model, and inside the same app.
4. `examples/fakeshop/apps/scalars/models.py::NullableScalarSpecimen` #"related_name=\"nullable_partners\"" — `partner` -> `ScalarSpecimen`. The site this slice's prose is about.

`apps/kanban` did not exist at the ship commit and `ScalarSpecimen.tag` was added by the later O6 card, so the claim was true when written and is false now. Nothing was ever wrong in the code; three prose passages simply outlived their measurement.

### Candidate replacement claims, and why each was rejected or kept

The failure mode this slice must not repeat is trading one over-claim for a differently-worded over-claim. Each candidate framing was measured before being kept or dropped.

- **"the example tree's `SET_NULL` cross-model FK under the optimizer" — REJECTED, false.** `ScalarSpecimen.tag` (site 3) is also cross-model, also `SET_NULL`, and is also planned by the optimizer; that is the entire point of the O6 downgrade substrate.
- **"the only `SET_NULL` edge exposed through a `DjangoType` relation field" — REJECTED, false.** Measured: all four sites are exposed. `"verified_by"` and `"supersedes"` are both in `examples/fakeshop/apps/kanban/schema.py` `Meta.fields` tuples; `"tag"` is in `apps/scalars/schema.py::ScalarSpecimenType`; `"partner"` is in `apps/scalars/schema.py::NullableScalarSpecimenType`. The kanban app's `Query` and `Mutation` are composed into `examples/fakeshop/config/schema.py`, so its types are in the same live schema build.
- **"the only `SET_NULL` ondelete whose detach behavior any test exercises" — REJECTED, true but structurally unsafe.** It is true today: sweeping `.delete()` across `tests/`, `examples/fakeshop/test_query/`, `examples/fakeshop/tests/`, and `examples/fakeshop/apps/*/tests/` finds no test that deletes an `Actor`, a `Decision`, or a `ScalarSpecimenTag`. It is rejected anyway, because it is the same *shape* of claim as the one being retired: a census over the whole test corpus, falsifiable by growth in an unrelated app, invisible from the site that asserts it. Replacing a rotted census with a fresh census buys one more rotation, not a fix.
- **A narrower per-app statement — REJECTED as insufficient on its own.** "the only `SET_NULL` out of `NullableScalarSpecimen`" is trivially true (one FK on the model) and tells a reader nothing they cannot see from the field list two lines below.
- **KEPT: state the local invariant, with no quantifier over any population the site cannot see.** Every replacement below is a statement about this field, this model, and this test, verifiable by reading the file it lives in plus the one file it names. That is what makes it durable: no edit to `apps/kanban` or any future example app can falsify it.

The load-bearing content the three sentences currently carry, which the replacements must preserve rather than delete: (a) why `partner` is `SET_NULL` rather than `CASCADE`; (b) that `partner` is a cross-model edge distinct from the intra-model `ScalarSpecimen.parent` self-FK; (c) why the live HTTP test exists at all.

### Should the three sites say the same thing three times? No.

`docs/builder/BUILD.md` DRY-first applies to prose too, and a near-identical claim repeated across two files is the shape it asks about. It is also mechanically what made this drift a three-site fix instead of a one-site fix: the census was written once and copied twice, so it rotted in triplicate.

The plan is **one authoritative statement plus two narrower local ones**:

- **Authoritative — the `NullableScalarSpecimen` class docstring.** It is the class-level contract, it already carries the model's purpose, and it is the natural home for the one cross-file pointer to the live pin.
- **Narrow-local — the `partner` field comment.** States only why *this field* is `SET_NULL` rather than `CASCADE`. It does not restate the docstring and does not repeat the pointer; a reader eight lines below the docstring does not need it twice.
- **Narrow-local — the test docstring.** States what *this test* pins. It names the FK and the behavior; it makes no claim about any other model, app, or test.

No shared constant or helper is possible or wanted here — prose in three files is not a duplication a helper can remove; the fix is that each site says only what its own scope knows.

### Scope check: other absolute claims in `apps/scalars/` and `test_query/test_scalars_api.py`

Answered explicitly for each, per the maintainer's instruction that a claim checked and found true is a decided answer worth recording.

**The prompt's "fourth candidate" from `git grep 'the only' examples/fakeshop/apps/scalars/` does not exist.** The command returns exactly two lines, both in `models.py` and both already in scope:

```
examples/fakeshop/apps/scalars/models.py:149:    from the intra-model self-FK on ``ScalarSpecimen.parent``, and the only
examples/fakeshop/apps/scalars/models.py:172:    # row instead of cascading - the only ``SET_NULL`` ondelete in the
```

Line 149 is the wrapped opening of site 1's sentence (whose distinctive substring lands on line 150) and line 172 is site 2. Widening the sweep to `-i 'only'`, `'the sole'`, `'no other'`, `'the one place'`, `'only place'`, `'only app'`, and `'in the example tree'` across both paths surfaces no further example-tree census. So the three sites Worker 0 named are the complete population of this claim in the fenced files. Recorded because a population stated and not re-derived is how the last three cycles went wrong.

Other absolutes read and adjudicated:

- `apps/scalars/models.py::ScalarSpecimen` #"the same entry; both stay because" — "the scalar coverage app is the place that pins every entry in one query". **STILL TRUE, out of scope.** It is scoped to the app's purpose, and the module docstring three dozen lines above already names the two deliberate exclusions (`ArrayField` / `HStoreField`). Not a tree census.
- `apps/scalars/models.py::ScalarSpecimen` #"Distinct from the library app, where every relation" — **VERIFIED STILL TRUE.** `apps/library/models.py` carries eight models and no self-referential relation: `TaggedItem.content_type`, `Shelf.branch`, `Shelf.alt_branches` (M2M -> `Branch`), `Book.shelf`, `Book.genres`, `MembershipCard.patron`, `Issue.periodical`, `Loan.book`, `Loan.patron` all cross a model boundary. The claim names one app rather than the tree, which is exactly why it survived where the `SET_NULL` census did not.
- `apps/scalars/models.py` #"deliberately absent" — the `ArrayField` / `HStoreField` exclusion. **VERIFIED STILL TRUE:** `git grep -n 'ArrayField\|HStoreField' -- examples/` matches only these two docstring lines; neither field type appears in any example model.
- `apps/scalars/schema.py::MediaSpecimenWithPathType` #"reachable only through its own" — a statement of what `primary = False` means for this type, not a population census. **STILL TRUE, out of scope.**
- `test_query/test_scalars_api.py` #"is the only way the value can survive" — about JSON numeric precision past `2**53 - 1`, not about the example tree. **STILL TRUE, out of scope.**

**One further stale claim IS pulled into scope**, and it is inside the very docstring's own test function:

- `test_query/test_scalars_api.py::test_scalars_set_null_ondelete_detaches_partner_in_http_query` #"mutations aren't in the example schema yet" — **FALSE at `HEAD`.** `examples/fakeshop/apps/scalars/schema.py::Mutation` exists (`CreateMediaSpecimen`, `CreateMediaSpecimenImageViaForm`) and `examples/fakeshop/config/schema.py::Mutation` composes it alongside four sibling app mutations. The comment's *conclusion* — that the trigger goes through the ORM — is still right; its stated reason is not. Re-derived precisely: the example schema does have a delete mutation (`apps/products/schema.py::DeleteItem`), but the scalars app exposes none, so the true reason is app-scoped, not schema-wide. It is one contiguous comment inside the same function whose docstring this slice is already rewriting, in a file already open; leaving a known-false sentence three lines from a sentence being corrected for being false is the "correct new text on the wrong side of a scope boundary" failure. In scope, as site 4.

### Implementation steps

Line numbers are pin-at-write-time navigational hints, read at `HEAD` `ddf8bbaf` with the tree baseline-dirty. Verify against the current source before editing; anchor on the quoted substrings, which are stable.

1. **Site 1 — `examples/fakeshop/apps/scalars/models.py::NullableScalarSpecimen` class docstring** (currently lines 147-151, the sentence beginning "``partner`` is a nullable"). Replace the trailing `, and the only place in the example tree that exercises ``SET_NULL`` ondelete planning under the optimizer` with the authoritative local statement. Intended content, wording at Worker 2's discretion within the constraints below:

   > ``partner`` is a nullable cross-model FK to ``ScalarSpecimen`` (``on_delete=SET_NULL``) - distinct from the intra-model self-FK on ``ScalarSpecimen.parent``. Deleting the target clears ``partner_id`` and leaves this row in place, so a later query resolves ``partner`` as ``null`` with the source row still present; that end-to-end shape is pinned by ``examples/fakeshop/test_query/test_scalars_api.py::test_scalars_set_null_ondelete_detaches_partner_in_http_query``.

   Keep the "distinct from the intra-model self-FK" clause verbatim — it is the (b) content above and is still true. The symbol-path pointer is the one cross-file reference this slice adds, in the `AGENTS.md` `path::QualifiedName` form the file already uses elsewhere (see the `tests/types/test_resolvers.py` reference in the module docstring).

2. **Site 2 — `examples/fakeshop/apps/scalars/models.py` #"row instead of cascading"**, the inline comment on the `partner` field (currently lines 170-173). Replace the census clause with the local why-this-ondelete statement. Intended content:

   > \# Cross-model link: a ``NullableScalarSpecimen`` may point at one
   > \# ``ScalarSpecimen``. ``SET_NULL`` rather than ``CASCADE`` because this
   > \# model's contract is that every column can read ``null``: losing the
   > \# target must clear the FK, never delete the mirror row.

   No pointer here and no restatement of the docstring: this comment answers only "why this ondelete on this field".

3. **Site 3 — `examples/fakeshop/test_query/test_scalars_api.py::test_scalars_set_null_ondelete_detaches_partner_in_http_query` #"Pins the only"** (currently lines 608-609). Replace `Pins the only ``SET_NULL`` ondelete in the example tree (the ``NullableScalarSpecimen.partner`` FK) end-to-end.` with a statement of what the test pins, carrying no population claim. Intended content:

   > Pins ``NullableScalarSpecimen.partner``'s ``SET_NULL`` ondelete end-to-end.

   The rest of that docstring — the setup-trigger-observe explanation and the numbered three-assertion list — is accurate and stays, except as noted in step 4 and the discretion item below.

4. **Site 4 — same file, the `# TRIGGER` comment** #"mutations aren't in the example schema yet" (currently around lines 649-651). Replace the false premise with the true, app-scoped one; keep the conclusion. Intended content:

   > \# TRIGGER - delete the partner target via ORM (the scalars app exposes
   > \# no delete mutation; deletion goes through the same path every seed
   > \# uses, just in reverse).

5. **Constraints on every replacement**, all of which Worker 3 should check:
   - **No process provenance.** `AGENTS.md` and the standing rule: a comment states the invariant, never how the change came to be. No card id, no commit hash, no date, no "previously", no "used to be", no "as of", no spec number. The text must read as though it had always said this.
   - **ASCII-only.** `scripts/check_trailing_commas.py` enforces ASCII in `.py` source and its `--check` runs in pre-commit and CI. Use `-`, never an em-dash; the surrounding lines already use `-` for exactly this reason.
   - **Line length 100** (`[tool.ruff]` `line-length = 100`). Re-wrap the whole affected paragraph rather than leaving a long line; `ruff format` will not re-wrap comment or docstring prose for you.
   - **Touch no code.** No field argument, no `on_delete` value, no assertion, no import. `git diff` for this slice must be comment and docstring lines only.
   - Do not touch the `## Other` bullet in `docs/SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md:27`, which carries the same retired claim. It is Slice 3's (finding `D2`/`D3` on the spec side) and the spec is not this slice's to edit.

6. **Validation.** `uv run ruff format examples/fakeshop/apps/scalars/models.py examples/fakeshop/test_query/test_scalars_api.py` then `uv run ruff check --fix` on the same two paths — scoped to these files, never `.`, because the tree carries two other sessions' uncommitted work. Then `git status --short`: any modified file other than these two and this artifact is a stop-and-report, never a revert.

### Test additions / updates

**No test needs adding and no test needs updating.** Stated plainly because an empty section here would be ambiguous:

- The slice changes zero lines of executable code. Sites 1, 2 and 4 are a docstring and two comments; site 3 is a docstring. No assertion, no fixture, no field definition, and no wire shape changes, so there is no new behavior for a test to pin and no existing assertion that could become wrong.
- Nothing in the repo asserts on these strings. Verified: no test greps source text, and `scripts/build_tree_md.py` renders **module** docstrings only, so neither the class docstring at site 1 nor the test docstring at site 3 feeds a generated doc. `docs/TREE.md` therefore needs no regeneration, which also keeps this slice clear of the concurrent sessions' generated-file surface.
- **One focused run as a regression guard**, not as new coverage: `uv run pytest examples/fakeshop/test_query/test_scalars_api.py -q`. It proves the edited file still imports and collects (a mangled docstring quote is the one way a prose edit can break a module) and that the 29 tests in it still pass. **No `--cov*` flag** — `docs/builder/BUILD.md` "Coverage is the maintainer's gate, not a worker's tool". Worker 2 records the invocation and its pass/fail under `### Validation run`.
- **Temp tests: none are appropriate.** There is nothing for a temp test under `docs/builder/temp-tests/` to demonstrate; Worker 3's review here is a read of four prose passages against measured source, not a behavioral question.

### DRY analysis

**Helper inventory checked.** Not applicable and not run, recorded rather than silently skipped. `worker-1.md` `### Package-wide helper inventory before helper planning` exists to stop a plan proposing a duplicate *code* shape; this slice writes no Python statement, adds no helper, constant, validation branch, coercion utility, or test helper, and its diff contains no executable line for an inventory to match against. Nothing under `django_strawberry_framework/` is read or written by this slice at all.

- **Existing patterns reused.** The replacement text reuses two conventions already in these files rather than inventing a form: the `path::QualifiedName` symbol-path citation from a docstring to a pinning test (`examples/fakeshop/apps/scalars/models.py:41-42` cites `tests/types/test_resolvers.py` the same way) and the "state the mechanism, then name where it is pinned" shape of the `ScalarSpecimen.tag` comment at `examples/fakeshop/apps/scalars/models.py:122-128`. Wrapping, `` `` `` double-backtick markup, and `-` in place of em-dash all follow the surrounding file.
- **New helpers justified.** None, and none is possible: prose in two files cannot be factored into a shared symbol.
- **Duplication risk avoided.** The specific risk is the one that created this slice — writing the same replacement sentence into all three (now four) sites, which would leave a claim that has to be corrected in four places the next time the tree grows. Prevented by construction above: one authoritative statement in the class docstring, and three narrower statements each scoped to what its own site can see. Worker 3 should treat a replacement that repeats the docstring's sentence at the field comment or in the test as a DRY finding, not as thoroughness.

### Implementation discretion items

Assessed and decided to be Worker 2's:

- **Exact wording and line wrapping** of all four replacements, within the constraints in step 5. The intended content above fixes the claim and the scope; the sentence rhythm is not an architectural question.
- **Whether the site-1 pointer names the test by full path or by file-relative symbol path.** Both forms appear in the repo; either satisfies `AGENTS.md`. Pick the one that wraps better inside 100 columns.
- **Whether to keep or lightly repair the word "cascade" in the site-3 docstring's numbered assertion list** — assertion 1 says "after the cascade" and assertion 2 says "cascade is ``SET_NULL``, not ``CASCADE``", which reads confusingly for an ondelete that is by definition not a cascade. Substituting "the delete" changes no claim and asserts nothing new. Permitted, not required; if Worker 2 changes it, note it under `### Implementation notes`.

Nothing else is delegated. The claim each site is permitted to make is fixed by this plan, not by Worker 2's judgement.

### Spec slice checklist (verbatim)

The `026` spec is a stub with no `## Slice checklist` (Worker 0's finding `D1`; Slice 3 is what creates one), so there is no verbatim spec text to copy. Per `docs/builder/ARTIFACT.md` the boxes below stand in its place, one per site Worker 2 must land, under the identical tick-and-audit discipline: Worker 2 ticks a box only when that site's contract is in its diff, and Worker 1 audits every tick at final verification.

- [x] `examples/fakeshop/apps/scalars/models.py::NullableScalarSpecimen` #"place in the example tree that exercises" — the tree-wide `SET_NULL` census is gone from the class docstring, replaced by the local detach-and-survive statement naming the live pin; the "distinct from the intra-model self-FK on `ScalarSpecimen.parent`" clause is preserved.
- [x] `examples/fakeshop/apps/scalars/models.py` #"row instead of cascading" — the `partner` field comment states why this edge is `SET_NULL` rather than `CASCADE` and makes no claim about any other model, app, or file.
- [x] `examples/fakeshop/test_query/test_scalars_api.py::test_scalars_set_null_ondelete_detaches_partner_in_http_query` #"Pins the only" — the docstring states what the test pins, carrying no population claim; the setup-trigger-observe paragraph and the three-assertion list survive.
- [x] `examples/fakeshop/test_query/test_scalars_api.py::test_scalars_set_null_ondelete_detaches_partner_in_http_query` #"mutations aren't in the example schema yet" — the `# TRIGGER` comment's false premise is replaced by the app-scoped true one (the scalars app exposes no delete mutation); the ORM-trigger conclusion is preserved.
- [x] No replacement names a card, commit, date, spec number, or any "used to / now" history, and no replacement re-states another site's claim.
- [x] `examples/fakeshop/apps/scalars/models.py` #"model's contract is that every column" — the `partner` field comment quantifies over the fields **this model declares** (all twelve are `null=True`), never over its *columns*: the implicit `id` primary key is a column of this model and is `NOT NULL` in the schema and non-null on the wire, so "every column can read `null`" is false as landed. Added by Worker 1 at final verification (overturned Worker 3 Low #1).
- [x] The diff contains comment and docstring lines only, in exactly these two files; `ruff format` and `ruff check --fix` were run scoped to those two paths and `git status --short` shows no third modified source file.

---

---

## Build report (Worker 2)

### Files touched

Grounded in `git status --short` after both ruff invocations.

- `examples/fakeshop/apps/scalars/models.py` — two prose passages. (a) `NullableScalarSpecimen` class docstring: the tree-wide `SET_NULL` census clause replaced by the local detach-and-survive statement plus the symbol-path pointer to the live pin; the "distinct from the intra-model self-FK on `ScalarSpecimen.parent`" clause preserved verbatim. (b) the `partner` field comment: census clause replaced by the why-`SET_NULL`-rather-than-`CASCADE` statement scoped to this model's all-nullable contract.
- `examples/fakeshop/test_query/test_scalars_api.py` — two prose passages. (a) `test_scalars_set_null_ondelete_detaches_partner_in_http_query` docstring: opening sentence now states what the test pins with no population claim; the setup-trigger-observe paragraph and the three-assertion list survive (re-wrapped, plus the permitted "cascade" repair below). (b) the `# TRIGGER` comment: the false "mutations aren't in the example schema yet" premise replaced by the true app-scoped one; the ORM-trigger conclusion preserved.

No other file in the working tree was modified by this pass. `git status --short` also lists the two concurrent sessions' `024` / `025` work, the baseline-dirty out-of-scope set named in the build plan, and this cycle's own Slice 1 outputs (`docs/SPECS/spec-026-...md`, `docs/SPECS/appx/spec-026-...-rationale.md`, `docs/builder/bld-slice-1-026-...md`, `docs/builder/build-026-...md`). None of those was touched or reverted.

### Tests added or updated

None, per the plan's `### Test additions / updates`. The diff changes zero executable lines, so there is no new behavior for a test to pin and no existing assertion that could become wrong. The three-assertion list in the edited test docstring describes assertions that were already there and are unchanged.

### Validation run

- `uv run ruff format examples/fakeshop/apps/scalars/models.py examples/fakeshop/test_query/test_scalars_api.py` — **pass** (`2 files left unchanged`; the edits were already formatter-clean). Scoped to the two files, never `.`.
- `uv run ruff check --fix examples/fakeshop/apps/scalars/models.py examples/fakeshop/test_query/test_scalars_api.py` — **pass** (`All checks passed!`). Same scope. The `COM812`-vs-formatter warning ruff prints is the repo's standing configuration notice, not a finding from this diff.
- `uv run python scripts/check_trailing_commas.py --check examples/fakeshop/apps/scalars/models.py examples/fakeshop/test_query/test_scalars_api.py` — **pass**, exit 0. This is the gate that owns the ASCII-only rule, so it is the mechanical proof of the ASCII constraint.
- `git status --short` after both ruff invocations — classified above; every modified file is slice-intended or pre-existing concurrent/baseline work. Nothing unexpected, nothing reverted.
- Focused regression run, exactly the one the plan names: `uv run pytest examples/fakeshop/test_query/test_scalars_api.py -q --no-cov` — **29 passed in 14.66s**, 0 failures, 0 collection errors. `--no-cov` because `pytest.ini`'s `addopts` auto-applies coverage; no `--cov*` flag was passed. The count 29 is read from the run's own summary line, not inherited from the plan.

Independent measurements taken while writing this report, each run as it was written:

- `git grep -o 'on_delete=models.SET_NULL' -- 'examples/fakeshop/apps/*/models.py' | wc -l` -> **4**. The plan's headline number confirmed at HEAD before editing, so the claim being retired is confirmed false rather than assumed false.
- `grep -n 'class Mutation' -A 12 examples/fakeshop/apps/scalars/schema.py` -> `Mutation` exposes exactly `create_media_specimen` and `create_media_specimen_image_via_form`; no delete mutation. This is the mechanical proof of site 4's replacement premise.
- `git grep -n 'DeleteMutation\|class Delete' -- 'examples/fakeshop/apps/*/schema.py'` -> a single hit, `examples/fakeshop/apps/products/schema.py:261:class DeleteItem(DjangoMutation)`. Confirms the plan's distinction: the example schema does carry a delete mutation, so the app-scoped wording ("the scalars app exposes no delete mutation") is the true form and the old schema-wide wording was false.
- Post-edit sweep for a residual census in the two files, `grep -n -i 'the only\|example tree\|no other\|the sole'` over both paths -> exactly **1** line, `examples/fakeshop/test_query/test_scalars_api.py:24` ("decimal-string serialization is the only way the value can survive"), which is the JSON numeric-precision claim the plan read and adjudicated out of scope. Zero example-tree censuses remain.
- Non-ASCII sweep, `LC_ALL=C grep -n '[^ -~]'` over both paths -> **0** lines.

### Failability proofs

None; this pass introduced no new boundary. Recorded as a deliberate exemption, not an omission: `docs/builder/BUILD.md` `### What needs a proof, and what does not` scopes the obligation to a new boundary, guard, gate, or rejection path, and this pass's diff is four prose passages containing no branch, no validation, no rejection path, and no executable statement of any kind. There is nothing to mutate, so no mutation was invented.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- **Site 1's pointer uses the fakeshop-relative path, not the repo-relative one** — `` `test_query/test_scalars_api.py::test_scalars_set_null_ondelete_detaches_partner_in_http_query` ``. This is the plan's explicit discretion item ("full path or file-relative symbol path... pick the one that wraps better"). Measured: the repo-relative form is 110 characters before markup, which with the four backticks and the four-space docstring indent lands at 118 and breaks the E501 grace ceiling of 110; the fakeshop-relative form puts the line at **102**, inside that grace. The shortened form is also the convention this very file already uses for in-example references (`apps/scalars/schema.py` in the module docstring). The path is kept on one unbroken line: splitting a symbol path across a line break would make it un-greppable, which defeats the point of citing it.
- **The pointer sentence names the observable behavior before naming the test.** "Deleting the target clears `partner_id` and leaves this row in place, so a later query resolves `partner` as `null` with the source row still present" is verifiable from this file plus the one file it names, and stays true no matter what any other app does. That is the plan's KEPT framing applied literally: no quantifier over any population this site cannot see.
- **Site 2 carries no pointer and no restatement of the docstring**, per the plan's DRY split. It answers only "why this ondelete on this field", grounding the answer in this model's own all-nullable contract - a fact visible in the eleven field definitions directly above the comment.
- **The permitted "cascade" repair was taken** (plan `### Implementation discretion items`, third bullet). Assertion 1's "after the cascade" is now "after the delete" and assertion 2's "cascade is `SET_NULL`, not `CASCADE`" is now "the ondelete is `SET_NULL`, not `CASCADE`". Both changes are wording only; neither adds, removes, or weakens a claim, and the three assertions they describe are byte-identical to before.
- **The test docstring's opening paragraph was re-wrapped**, not just edited in place: shortening the first sentence left ragged lines that would have read as an unfinished edit. The re-wrap moves no content across paragraph boundaries.

### Notes for Worker 3

- The diff is comment and docstring lines only. `git diff -- examples/fakeshop/apps/scalars/models.py examples/fakeshop/test_query/test_scalars_api.py` shows no field argument, no `on_delete` value, no assertion, no import, and no executable line changed. Worth confirming independently, since "touch no code" is the plan's step-5 constraint and the whole slice rests on it.
- No shadow file and no `scripts/review_inspect.py` run was used this pass; the four sites were read directly in source.
- **Process-provenance check, the constraint most likely to fail this slice:** no replacement text names a card, commit hash, date, spec number, version, or any "used to / previously / now / as of" history. Every replacement reads as though the file had always said it. This is checkable by reading the four passages in the diff.
- **The DRY split is deliberate and should not be read as an omission.** The class docstring is the only site carrying the cross-file pointer; the field comment and the test docstring each state only what their own scope knows. Per the plan, a replacement that repeated the docstring's sentence at the other sites would be the DRY finding, not the reverse.
- The one surviving `the only` in the touched files (`test_scalars_api.py:24`) is the JSON numeric-precision claim, read and adjudicated out of scope by the plan's `### Scope check`. It makes no claim about the example tree.
- The plan's spec-side twin of this claim (`docs/SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md` `## Other`) is untouched by design - Slice 3's, and not Worker 2's to edit.

### Notes for Worker 1 (spec reconciliation)

- **No plan-vs-implementation drift, structural or mechanical.** The plan's framing was checked against source before editing and held: the four `SET_NULL` sites, the scalars app's mutation surface, and the products app's `DeleteItem` all measured exactly as the plan states. No pause is being raised and `Status:` is `built`, not `revision-needed`.
- **Spec-side item still open, for Slice 3, not an amendment request against this pass.** The retired census also lives in `docs/SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md`, section **`## Other`**, currently worded as the only `SET_NULL` ondelete in the example tree. Recommended replacement, matching what the `.py` sites now say: state that `NullableScalarSpecimen.partner` is a nullable cross-model FK whose `SET_NULL` ondelete clears `partner_id` and leaves the source row in place, pinned end-to-end by `test_query/test_scalars_api.py::test_scalars_set_null_ondelete_detaches_partner_in_http_query` - with no quantifier over the example tree. Flagged here so the spec side lands the same framing rather than a re-worded census.
- **One measurement worth carrying into Slice 3's D4 reconciliation.** The `# TRIGGER` comment's old premise (schema-wide "mutations aren't in the example schema yet") was false while its app-scoped form is true, and the same distinction applies to any spec sentence about what the example schema exposes: `examples/fakeshop/apps/products/schema.py::DeleteItem` exists, so a schema-wide "no mutations" or "no delete mutation" statement anywhere in the spec is false at HEAD. Recommended wording wherever such a sentence appears: scope it to the scalars app.

Status: built

---

## Review (Worker 3)

Every number below was measured while this section was written, against the working tree, not inherited from the plan or the build report. Commands are recorded inline so Worker 1 can re-run them.

**The diff reviewed.** `git diff HEAD -- examples/fakeshop/apps/scalars/models.py examples/fakeshop/test_query/test_scalars_api.py` -> 5 hunks, **18 added lines**, all inside a docstring or a `#` comment. Verified mechanically rather than by eye: the added-line set contains no `def`, no assignment, no call, no import, no field argument, and no `on_delete` value. The plan's step-5 "touch no code" constraint holds. `git status --short` shows exactly two modified source files beyond the baseline-dirty / concurrent set the build plan fences (`docs/SPECS/spec-024`, `spec-025`, `spec-026` and the `-024`/`-025`/`-026` artifacts are the other sessions' and Slice 1's; none was touched).

### Re-derivation of every replacement claim

The prompt's characteristic failure mode is a replacement that is itself false. Each landed sentence was re-derived against source independently of Worker 2's report.

| Landed claim | How measured | Result |
| --- | --- | --- |
| the retired census was false (4 `SET_NULL` sites, not 1) | `grep -o 'on_delete=models.SET_NULL' examples/fakeshop/apps/*/models.py \| wc -l` | **4** — `apps/kanban/models.py` twice (843, 995), `apps/scalars/models.py` twice (133, 180). Full ondelete census for context: 60 `CASCADE`, 19 `PROTECT`, 4 `SET_NULL` |
| site 4: `apps/scalars/schema.py::Mutation` exposes no delete mutation | read `class Mutation` in full | **true** — exactly `create_media_specimen` and `create_media_specimen_image_via_form`, then `__all__` |
| site 4's premise is app-scoped because a delete mutation *does* exist elsewhere | `grep -rn 'class Delete\|delete_' examples/fakeshop/apps/*/schema.py examples/fakeshop/config/schema.py` | **1 delete mutation in the tree**: `apps/products/schema.py::DeleteItem` (line 261), wired at line 447. So the old schema-wide premise was false and the new app-scoped one is true |
| site 1: deleting the target clears `partner_id`, leaves the row, and a later query resolves `partner` as `null` | read `test_scalars_set_null_ondelete_detaches_partner_in_http_query` body | **true and pinned** — the AFTER query asserts `{"label": "linked", "partner": None}`, then `refresh_from_db()` + `pk is not None` + `partner_id is None`. The docstring describes the assertions that are actually there |
| site 1's cited test symbol resolves | `git grep -n 'test_scalars_set_null_ondelete_detaches_partner_in_http_query'` | **2 hits**: the citation and `test_scalars_api.py:605`, the `def`. No dangling reference |
| site 1's preserved clause ("distinct from the intra-model self-FK on `ScalarSpecimen.parent`") is still true | `ScalarSpecimen.parent` at `models.py:115` | **true**, `ForeignKey` to self, `on_delete=CASCADE` |
| the one surviving `the only` in the two files is still true | `grep -n -i 'the only\|example tree\|no other\|the sole\|only place\|only app\|elsewhere'` over both paths | **1 line**, `test_scalars_api.py:24` — the `2**53 - 1` decimal-string JSON claim. Read in context: it is about wire format, not about the example tree, and is true. Zero example-tree censuses remain in the fenced files |

**Durability judgement, per site.** The test the prompt sets is whether unrelated growth in another app could falsify the sentence.

- Site 1 (class docstring) — statement about this FK's runtime behavior plus a pointer to the one file that pins it. Falsifiable only by changing `partner`'s `on_delete` or deleting that test. **Not a census.**
- Site 2 (`partner` field comment) — statement about this model's own columns. Falsifiable only by editing this model. **Not a census.**
- Site 3 (test docstring) — statement about what this test pins. **Not a census.**
- Site 4 (`# TRIGGER` comment) — "the scalars app exposes no delete mutation" is a quantifier, but over one sibling file in the same app. Growth in `apps/kanban`, `apps/library`, or any future app cannot falsify it; only editing `apps/scalars/schema.py` can. That is a scope the site can see, so it passes the test the plan set. Recorded explicitly because it is the one landed sentence that carries any quantifier at all.

### High:

None.

### Medium:

#### The plan's "complete population" statement is falsified by a fifth census in the same file

Not a defect in what Worker 2 landed — Worker 2 executed the plan's four sites exactly. It is a defect in the plan's population claim, which Worker 3 is required to re-derive rather than inherit, and which the build report repeats.

The plan's `### Scope check` states: "the three sites Worker 0 named are the complete population of this claim in the fenced files", reached by sweeping `-i 'only'`, `'the sole'`, `'no other'`, `'the one place'`, `'only place'`, `'only app'`, and `'in the example tree'`. That vocabulary does not match a universal quantifier spelled positively. The module docstring of the very file Slice 2 edits carries one:

```examples/fakeshop/apps/scalars/models.py:7:8
The trivial-collapse entries (everything mapped to plain
``int`` or plain ``str``) are covered transitively by every other example app.
```

Measured at HEAD: `examples/fakeshop/apps/accounts/` is an installed example app (`config/settings.py`, and `test_query/README.md` names it as one of the six apps composing the project `Query`) that has **no `models.py` at all** — `ls examples/fakeshop/apps/accounts/` returns `__init__.py`, `apps.py`, `schema.py` and nothing else. It therefore covers no converter row, transitively or otherwise, so "every other example app" is false at HEAD. Per-app field counts for the rest, `grep -cE 'models\.(TextField|IntegerField|CharField|BooleanField)'`: glossary 15, kanban 27, library 16, products 12, scalars 11, accounts **0 (no file)**.

This is the same defect class the slice exists to retire — a quantifier over a population the source file cannot see, true when written, falsified by an app that arrived later — sitting eight lines above the passages being corrected, in the file already open. Leaving it is the "correct new text on the wrong side of a scope boundary" failure the plan itself names when it pulled site 4 into scope on identical reasoning.

Recommended change: replace the quantifier with a statement of the mechanism, e.g. "…are covered transitively wherever an example model carries a plain `int` or `str` column", which names no population. Whether that lands as a Worker 2 re-pass or folds into Slice 3 is a plan-scope decision, not Worker 2's — **escalated to Worker 1 below rather than held at `revision-needed`**, per `worker-3.md` `### Acceptance gate`.

### Low:

#### "every column can read `null`" includes the `id` column, which cannot

```examples/fakeshop/apps/scalars/models.py:171:173
    # ``ScalarSpecimen``. ``SET_NULL`` rather than ``CASCADE`` because this
    # model's contract is that every column can read ``null``: losing the
    # target must clear the FK, never delete the mirror row.
```

The model's implicit `id` `AutoField` is a column and is not nullable. The class docstring five lines above uses the precise form — "Every scalar field is `null=True, blank=True`". Recommended: "every scalar column".

**Intentionally rejected, not held.** The sentence sits directly beneath eleven `null=True, blank=True` field definitions and directly above the `partner` FK it explains; no reader takes it as a claim about the surrogate key, and the reading that makes it false requires ignoring the docstring that scopes it. Recorded so the judgement is visible rather than silently skipped.

#### Site 1's cited path is fakeshop-relative while its sibling citations are repo-relative

```examples/fakeshop/apps/scalars/models.py:153
    ``test_query/test_scalars_api.py::test_scalars_set_null_ondelete_detaches_partner_in_http_query``.
```

The same docstring cites `django_strawberry_framework/types/converters.py::SCALAR_MAP` and the module docstring cites `tests/types/test_resolvers.py`, both repo-relative. A reader resolving this one from the repo root finds nothing (there is no top-level `test_query/`).

**Intentionally rejected, not held**, on two measured grounds. (1) The plan delegated the choice explicitly (`### Implementation discretion items`, second bullet: "full path or file-relative symbol path… pick the one that wraps better"), and both forms satisfy `AGENTS.md`. (2) The repo-relative form is mechanically unavailable: the landed line measures **102** columns (`awk 'NR==153{print length}'`), and prefixing `examples/fakeshop/` adds 18 to **120**, past the E501 grace ceiling of 110 that `[tool.ruff.lint.pycodestyle] max-line-length` sets — and a symbol path split across a line break stops being greppable, which is the point of citing it. The file already carries the fakeshop-relative form (`apps/scalars/schema.py` in the module docstring), so the mixed convention predates this slice.

### DRY findings

The plan's specific instruction was to treat a replacement that repeats the docstring's sentence at another site as a DRY finding. Checked by reading all four landed passages side by side: **no shared sentence, no shared clause, and one cross-file pointer total.**

- Site 1 is the only site carrying the pointer to the pinning test.
- Site 2 states only why this ondelete on this field, grounded in the model's own columns. It does not restate the docstring and carries no pointer.
- Site 3 states only what the test pins. It names no other model, app, or test.
- Site 4 states only what the scalars app's schema exposes.

The one-authoritative-plus-narrow-local split landed as planned. No repeated string literal, no repeated helper, no abstraction to challenge — the diff adds no symbol of any kind, so `### The existence challenge` has no subject this pass. `scripts/review_inspect.py` was **not run**, recorded as a deliberate skip: its outputs are repeated-literal and import-boundary evidence over Python constructs, and this diff contains no Python construct. The four passages were read directly in source.

### Failability proofs, hot-path budget, floor verification

All three declarations re-verified against the landed diff rather than accepted from the plan.

- **Failability proofs — exemption confirmed, and the artifact records it.** `BUILD.md` `### What needs a proof, and what does not` scopes the obligation to a new boundary, guard, gate, or rejection path. Verified against the diff, not the plan: the 18 added lines contain no `if`, no `raise`, no `return`, no comparison, no validation, and no executable statement, so there is nothing that could be mutated to stop holding. Worker 2 wrote `None; this pass introduced no new boundary.` under the required heading rather than leaving it blank. **Independent re-run set: empty, and legal** — `worker-3.md`'s mandatory floor is computed over boundaries the diff introduces, and this diff introduces zero, so no boundary meets it. Nothing was accepted on Worker 2's record because there was no record to accept.
- **Hot-path budget — declaration still correct.** The diff changes no line that executes. Nothing here runs per request, per resolver, or per row, because nothing here runs at all. `Not applicable; plan declares no hot path.` stands.
- **Floor verification — declaration still correct.** No Django, Strawberry, or channels integration seam appears in the diff; no import changed, no version-sensitive API is touched. `Not applicable; plan declares floor-verification scope none.` stands.

### Layout and encoding gates

- `uv run python scripts/check_trailing_commas.py --check examples/fakeshop/apps/scalars/models.py examples/fakeshop/test_query/test_scalars_api.py` -> **exit 0**. Re-run independently; this is the gate that owns the ASCII-only rule.
- `LC_ALL=C grep -n '[^ -~]'` over both paths -> **0 lines**. No em-dash, no smart quote; the replacements use `-` as the surrounding lines do.
- `uv run ruff check <the two paths>` -> `All checks passed!`. `uv run ruff format --check <the same>` -> `2 files already formatted`.
- **Re-wrapped-docstring line-length audit**, the place the plan says a violation would hide. `awk 'length>100'` over both paths at HEAD and in the working tree: `models.py` had **0** long lines at HEAD and has **1** now (line 153, 102 columns, the unbreakable symbol path, inside the 110 grace). `test_scalars_api.py` has 4 long lines (105, 111, 120, 120) — **all four present at HEAD** (`git show HEAD:… | awk`), at the same content shifted one line by the re-wrap. The re-wrap introduced no new long line.

### Spec slice checklist audit

Six boxes, all ticked by Worker 2. Walked one at a time against the diff; every tick has a matching change and no box the diff addresses was left open.

1. `NullableScalarSpecimen` docstring census gone, clause preserved — **confirmed.** `the only place in the example tree that exercises` returns 0 hits repo-wide; the "distinct from the intra-model self-FK on `ScalarSpecimen.parent`" clause is byte-identical, only its trailing punctuation changed from `,` to `.`.
2. `partner` field comment scoped to this edge — **confirmed.** `row instead of cascading` returns 0 hits repo-wide.
3. Test docstring carries no population claim; setup-trigger-observe paragraph and three-assertion list survive — **confirmed.** `Pins the only` returns 0 hits repo-wide; all three numbered assertions are present and describe assertions that are unchanged in the body.
4. `# TRIGGER` premise replaced, ORM conclusion preserved — **confirmed.** `mutations aren` returns 0 hits repo-wide; "deletion goes through the same path every seed uses, just in reverse" survives.
5. No card, commit, date, spec number, or "used to / now" history, and no cross-site restatement — **confirmed mechanically.** `grep -iE 'spec-[0-9]|card|commit|previously|used to|as of|no longer|formerly|2026|[0-9a-f]{8}|TODO|slice'` over the 18 added lines -> **0 matches**. Every replacement reads as though the file had always said it.
6. Comment and docstring lines only, in exactly these two files; ruff scoped; no third modified source file — **confirmed** (see the diff paragraph above and the gate results).

The permitted "cascade" repair (plan discretion item 3) was taken and is recorded under `### Implementation notes` as the plan required. Checked that it changes no claim: "after the cascade" -> "after the delete" and "cascade is `SET_NULL`, not `CASCADE`" -> "the ondelete is `SET_NULL`, not `CASCADE`" both describe the same three assertions, which are byte-identical in the diff.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` -> **0 lines of output**. `__all__` and the re-export list are unchanged. Nothing under `django_strawberry_framework/` is read or written by this slice.

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md`.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. Confirmed rather than assumed: no version string, card ID, or generated doc appears in the diff, and `scripts/build_tree_md.py` renders **module** docstrings only — neither the class docstring at site 1 nor the test docstring at site 3 feeds `docs/TREE.md`, so no regeneration is owed and this slice stays clear of the concurrent sessions' generated-file surface. Two parallel sites that *do* carry the retired census are outside this cycle's scope fence and are reported under `### Notes for Worker 1` rather than silently passed over.

### Test staleness

Swept independently of the slice's file list, per `worker-3.md`. `git grep -ln '__doc__' -- tests examples` -> **0 files**: nothing in any of the three test trees asserts on source prose, so no test could have gone stale on these edits. The retired phrasings return 0 hits anywhere in the repo. Focused regression run reproduced: `uv run pytest examples/fakeshop/test_query/test_scalars_api.py -q --no-cov` -> **29 passed in 14.62s**, 0 failures, 0 collection errors, matching the build report's count read from my own run's summary line. No `--cov*` flag was used at any point in this review.

### What looks solid

- The replacements are local statements, not fresh censuses. Site 1 in particular buys durability the right way: it names an observable behavior verifiable from this file plus the one file it cites, so no future example app can rot it. The plan measured and rejected three candidate framings on falsity grounds and the landed text is the fourth, and it holds.
- Site 4 was pulled into scope on a re-derived premise and the re-derivation is correct in both directions — the scalars app really exposes no delete mutation, and `products/schema.py::DeleteItem` really exists, which is exactly why the app-scoped wording is the true form and the old schema-wide one was false.
- The DRY split is the substantive design call in the slice and it is right. The original defect was one census written once and copied twice; four sites each saying only what their own scope knows is what stops that recurring.
- Process provenance is clean under a mechanical sweep, not just a reading.

### Temp test verification

- Temp test files used: **none**. `docs/builder/temp-tests/slice-2-026/` was not created.
- Disposition: not applicable. The review question here is whether four prose passages are true of the source, which is answered by measuring the source; a temp test can demonstrate a non-distinguishing assertion, and this slice adds no assertion. The one executable check that could bear on the slice — that the edited modules still import and collect — is the focused run above.

### Notes for Worker 1 (spec reconciliation)

- **Escalated (Medium): the fifth census, `apps/scalars/models.py` module docstring #"covered transitively by every other example app".** Falsified above: `apps/accounts` is an installed example app with no `models.py`. The plan's `### Scope check` asserts the fenced files' census population is complete; it is not, and the sweep vocabulary is why. Resolution paths, Worker 1's pick: (a) dispatch a Worker 2 re-pass adding it as site 5, which is the cheapest option and keeps the whole claim class retired in one commit, and is what the plan's own site-4 reasoning argues for; (b) fold it into Slice 3 as a `.py` companion to the `D2`/`D4` spec edits; (c) record it as out of scope with the fence stated explicitly, so the next cycle does not re-discover it. Not held at `revision-needed` because it is a plan-scope decision Worker 2 cannot make.
- **Parallel site: `KANBAN.md:3846` carries the retired sentence verbatim, both clauses.** It ends "the only `SET_NULL` ondelete in the example tree, and the only cross-model FK in the scalars app" — identical to the spec's `## Other` bullet at `spec-026…md:27`. Both clauses are false at HEAD: the `SET_NULL` half by the four-site measurement above, and the cross-model half because `ScalarSpecimen.tag` -> `ScalarSpecimenTag` is a second cross-model FK inside the scalars app (`models.py:129`; `partner` remains the only cross-model FK *out of* `NullableScalarSpecimen`). The build plan records the second clause as `D3`, but `D3` is scoped to the spec; `KANBAN.md` is on the baseline-dirty do-not-edit list and the cycle's scope fence excludes KANBAN movement, so nothing in this cycle closes it. It also cannot be hand-edited — `KANBAN.md` renders from the fakeshop kanban DB, so a fix is a DB edit plus `scripts/build_kanban_md.py`. Flagged so the cycle closes with the gap recorded rather than unnoticed.
- **`KANBAN.md:3847` and `CHANGELOG.md:175` carry `D4`'s shape too** ("upstream code paths **no other example app reaches**"; "surfaces **no other example app** touches"). Both are on the do-not-edit list and the CHANGELOG entry is a historical ship record, so neither is this cycle's to change. Noted only so Slice 3's `D4` rewrite is understood to fix the spec copy alone.
- **Worker 2's recommended spec wording covers half of one sentence.** Its `### Notes for Worker 1` proposes replacement text for the `SET_NULL` clause of `spec-026…md:27`. That sentence carries two false clauses; the cross-model one (`D3`) needs replacing in the same edit or Slice 3 lands a half-corrected sentence.
- **Worker 2's `D4` observation is confirmed and worth acting on verbatim:** a schema-wide "no delete mutation" statement is false anywhere it appears, because `apps/products/schema.py::DeleteItem` exists. Measured independently: exactly one delete mutation in the whole example tree.

### Review outcome

`review-accepted`. High: none. Medium: one, transparently escalated to Worker 1 above with its resolution paths, per `worker-3.md` `### Acceptance gate` — it is a plan-scope question Worker 2 cannot resolve, and every site the plan did fence landed correctly. Low: two, each intentionally rejected with the reason and the measurement recorded. DRY: no findings; the split the plan called for is what landed. The diff is 18 prose lines in two files, changes zero executable lines, retires four false claims, introduces none, and carries no process provenance.

Status: review-accepted

---

## Final verification (Worker 1)

Every number below was measured in this pass, against the working tree. Nothing is inherited from the plan, the build report, or the review; where a prior section stated a number, the re-derivation is recorded even when it matched.

### The escalated Medium: DECIDED, no change. The claim is true at HEAD.

`examples/fakeshop/apps/scalars/models.py` #"covered transitively by every other example app".

Worker 3's falsification does not hold, and the reason is worth stating precisely because it is the same reading error the slice exists to correct, running the other way. Worker 3 measured **model ownership** (`apps/accounts` has no `models.py`) against a sentence whose subject is **converter-row coverage**. The sentence's own word for the gap is `transitively`: an app covers a trivial-collapse `SCALAR_MAP` row by exercising a plain `int` / `str` column over the live surface, not by declaring the model that carries it.

Measured, app by app, at HEAD:

| App | Trivial-collapse coverage | Evidence |
| --- | --- | --- |
| `accounts` | **yes, transitively** | `apps/accounts/schema.py::UserType` selects `username` (`CharField` -> `str`) and `email` (`EmailField` -> `str`) over `auth.User`; queried live at `test_query/test_auth_api.py` #"node{ username email }" |
| `glossary` | yes | 22 `Text/Char/Integer/Auto` columns in `apps/glossary/models.py`; four `Meta.fields` selections; live at `test_query/test_glossary_api.py` |
| `kanban` | yes | 34 such columns; live at `test_query/test_kanban_api.py` |
| `library` | yes | 16 such columns; live at `test_query/test_library_api.py` |
| `products` | yes | 8 such columns; live at `test_query/test_products_api.py` |

All six apps compose into the one root `Query` (`examples/fakeshop/config/schema.py:35`), and each has its own `test_query/` live module. `models.AutoField: int`, `models.CharField: str`, `models.TextField: str`, `models.EmailField: str` are the trivial-collapse rows in question (`django_strawberry_framework/types/converters.py` `SCALAR_MAP`).

So `every other example app` is **true at HEAD** — including the one app Worker 3 offered as the counterexample, which is in fact the sentence's clearest illustration of `transitively`. No edit is required, and none is authorized: correcting a true sentence is not in this slice's scope, and re-dispatching Worker 2 for it would ship a change with no defect behind it.

Two things are nonetheless recorded rather than dropped:

- **The escalation itself was correct.** Worker 3 found a universal the plan's sweep vocabulary structurally could not reach and handed it up rather than acting on it. The measurement was wrong; the reflex was right.
- **The sweep-vocabulary lesson is the durable part, and it is Worker 1's to carry.** The plan's `### Scope check` swept `only` / `sole` / `no other` / `the one place` / `only place` / `only app` / `in the example tree` — an entirely negative vocabulary. A census spelled positively (`every`, `all`, `always`, `each`) is invisible to it, and this file carries one eight lines above the passages the slice corrected. The plan's "complete population" statement was therefore **unproven when written**, and is corrected here: it was complete for negatively-spelled censuses only. Recorded in `worker-memory/worker-1-026.md` and carried into Slice 3, whose sweep must run both polarities.
- **Durability, stated so the next reader does not re-open it.** The sentence is a universal over installed example apps, so a future app that neither declares a model nor exposes a model-backed type would falsify it. That is a hypothetical, not a defect: the standard applied throughout this slice is that a claim measured true stays, and the wording question belongs to whoever next has cause to edit that docstring. Not deferred work, not a carded item.

### Worker 3's two rejected Lows, each re-measured

**Low #1 — "every column can read `null`" — OVERTURNED. The sentence is false as landed, and this pass authored it.**

```
examples/fakeshop/apps/scalars/models.py:171:173
    # ``ScalarSpecimen``. ``SET_NULL`` rather than ``CASCADE`` because this
    # model's contract is that every column can read ``null``: losing the
    # target must clear the FK, never delete the mirror row.
```

Measured at the schema, not by reading: `sqlite_master` for `scalars_nullablescalarspecimen` gives `"id" integer NOT NULL PRIMARY KEY AUTOINCREMENT` followed by twelve `NULL` columns. One of the model's thirteen columns cannot read `null`, and it is not a hidden one — `id` (a `BigAutoField`, the project's `DEFAULT_AUTO_FIELD`) is selected in `apps/scalars/schema.py::NullableScalarSpecimenType` `Meta.fields`, so it is non-null on the wire too. *(Counts corrected in `## Final verification (Worker 1, pass 2)`; as first written this paragraph said thirteen of fourteen.)*

Worker 3 rejected it on the ground that the class docstring five lines above scopes the reading. It does not: the docstring says `Every scalar field is null=True, blank=True`, and the comment **widened** that quantifier from `scalar field` to `column`. Widening a true quantifier into a false one is the defect, not a rescue from it.

Decisive on the disposition rather than the grade: this is not inherited prose that rotted, it is a **new false universal written by the pass whose contract is retiring false universals**, in the same passage, on the same screen. The slice's own site-4 reasoning — a known-false sentence three lines from one being corrected for falsity is the wrong-side-of-the-boundary failure — applies to it exactly. Cost of the fix is one clause; cost of shipping it is that the next cycle re-discovers this file as a false-claim site and cannot tell which half is current.

**Required change** (this is checklist box 7, and it amends this plan's own `### Implementation steps` step 2 intended content, which is where the wording originated — Worker 2 implemented the plan faithfully and is not at fault):

- The clause must quantify over the fields **this model declares** — all twelve (`label`, `flag`, `score`, `price`, `occurred_on`, `occurred_at`, `occurred_time`, `payload`, `external_id`, `signed_big`, `unsigned_big`, `partner`) are `null=True` — and must not quantify over the model's *columns*, which include the implicit `id` primary key.
- Exact wording is Worker 2's within that constraint; the class docstring's `Every scalar field is null=True, blank=True` is the precise form already in the file if a match is wanted.
- Everything else in that comment stays: it keeps no pointer, restates no other site, and its `SET_NULL`-rather-than-`CASCADE` reasoning is correct.
- All other constraints from `### Implementation steps` step 5 continue to apply (no process provenance, ASCII-only, re-wrap inside the line budget, touch no code).

**Low #2 — fakeshop-relative citation path — REJECTION CONFIRMED, mechanically.**

`awk 'length>100'` over `apps/scalars/models.py`: exactly one line, **153**, at **102** columns — the symbol path. `pyproject.toml` sets `line-length = 99` with `[tool.ruff.lint.pycodestyle] max-line-length = 110`, so 102 is inside the grace and 102 + `len("examples/fakeshop/")` = **120** is not. The repo-relative form is mechanically unavailable, splitting a symbol path across a line break destroys its greppability, and the same file already uses the fakeshop-relative form in its module docstring. Worker 3's rejection stands on its own measurement, re-run here.

(Incidental, non-blocking: the plan's step-5 constraint says "Line length 100"; the configured value is 99, with the 110 E501 grace the plan states correctly. No landed line is affected.)

### Spec slice checklist audit

Seven boxes. Six were ticked by Worker 2; each was re-audited against the diff independently of Worker 3's audit, and all six hold. Box 7 is new, added by this pass, and is `- [ ]` because its work has not been done — it is not a deferral.

| Box | Verdict | Proof run in this pass |
| --- | --- | --- |
| 1 — docstring census gone, self-FK clause preserved | **tick stands** | `git grep -F "place in the example tree that exercises"` -> 0 hits outside this artifact; the `distinct from the intra-model self-FK on ``ScalarSpecimen.parent``` clause is present in the diff's added lines |
| 2 — `partner` comment scoped to this edge | **tick stands** | `git grep -F "row instead of cascading"` -> 0 hits. (Its replacement carries the separate Low-#1 defect above; the box's own contract — the census is gone and no other model, app, or file is named — did land) |
| 3 — test docstring carries no population claim | **tick stands** | `git grep -F "Pins the only"` -> 0 hits; the setup-trigger-observe paragraph and all three numbered assertions are present in the diff |
| 4 — `# TRIGGER` premise replaced, ORM conclusion kept | **tick stands** | `git grep -F "mutations aren't in the example schema"` -> 0 hits; premise re-derived: `apps/scalars/schema.py::Mutation` exposes only `create_media_specimen` / `create_media_specimen_image_via_form`, and `apps/products/schema.py::DeleteItem` is the tree's one delete mutation, so the app-scoped form is the true one |
| 5 — no process provenance, no cross-site restatement | **tick stands** | `grep -icE 'spec-[0-9]\|card\|commit\|previously\|used to\|as of\|no longer\|formerly\|2026\|TODO\|slice'` over the 18 added lines -> **0** |
| 6 — comment/docstring lines only, two files, gates run | **tick stands** | added-line sweep for `def\|class\|import\|return\|if\|assert\|raise\|=\|call()` -> 1 hit, and it is the prose string ``target.delete()`` inside a docstring; `git status --short` lists exactly two modified `.py` files, both intended; `check_trailing_commas.py --check` exit **0**; `LC_ALL=C grep -c '[^ -~]'` -> **0** on both files |
| 7 — `every column` -> the fields this model declares | **not done** | new; see Low #1 above |

No box was over-ticked and no box needed ticking that Worker 2 left open, so `### Spec changes made (Worker 1 only)` carries no deferral reason for boxes 1-6. Box 7 is open work in this slice, not deferred out of it.

### Plan contract, declarations, and the three exemptions

- **Every planned step landed.** Sites 1-4 are all present in the diff in the planned shape, and the one discretion item Worker 2 exercised (the "cascade" -> "delete" / "the ondelete" repair) is recorded under `### Implementation notes` as the plan required. Nothing planned was dropped or silently rejected.
- **Ownership partition: none — still correct.** One cohort, one builder, one reviewer; no second cohort's diff exists to collide with.
- **Hot-path declaration: none — re-verified against the landed diff, not accepted from the plan.** No added line executes: the added-line sweep above finds no statement, and `uv run python -m py_compile` on both files succeeds, so the modules still parse with zero runtime surface changed.
- **Floor-verification scope: none — re-verified.** No import, no Django / Strawberry / channels API, and no version-sensitive construct appears in the diff.
- **Failability proofs: exemption confirmed, and the artifact records it.** Worker 2 wrote `None; this pass introduced no new boundary.` under the required heading and Worker 3 re-derived it against the diff rather than the plan. The record exists; no proof is owed and none was invented. That is the required outcome of the exemption, not a gap.
- **Fail-open shapes: none possible.** A fail-open shape is an expression that returns a permissive value on an unexpected input; this diff adds no expression.
- **Cross-slice duplication (final-verification step 4).** Checked against Slice 1's landed work: Slice 1 wrote `docs/SPECS/appx/spec-026-...-rationale.md` and the spec pointer, Slice 2 wrote four prose passages in two `.py` files. No shared sentence, no repeated literal, no helper in either. The one shape both slices use — a symbol-path citation to the site that proves a claim — is `AGENTS.md`'s convention, reused rather than reinvented.
- **Focused test run: not re-run here, deliberately.** `AGENTS.md` #"No pytest after edits" forbids running it unmasked, and this pass made no `.py` edit. The plan's one focused run was executed twice already, by Worker 2 and independently by Worker 3, both reporting `29 passed` with `--no-cov` and no `--cov*` flag. The failure mode that run guards against — a mangled docstring quote breaking import — is instead proven here by `py_compile` on both files, which succeeded.
- **Staged-anchor sweep:** `git grep -n "TODO(spec-026"` -> **0** repo-wide. Not owed by this slice (it is neither doc-wrap nor the final in-spec slice) and run anyway because it costs one command.

### Spec changes made (Worker 1 only)

**None this pass.** The spec was not edited and this slice plans no spec edit; Slice 3 owns the reconstruction.

Per-spawn status-line re-verification (`worker-1.md` `## Spec status-line re-verification`): `docs/SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md` lines 1-5 read the same as at Slice 1's close. The `Status:` line is still the placeholder Worker 0 recorded as `D9` ("shipped — canonical spec stub created to keep the Kanban DB one-to-one spec invariant intact") and the `## Planning note` is still the single word `shipped` (`D10`). Nothing this slice landed falsified either, and both are Slice 3's to resolve — recorded here so the next reader does not mistake the omission for an oversight.

### Instruction to Slice 3 (spec reconstruction) — the `## Other` sentence has TWO false clauses

This is the live consequence of Worker 3's out-of-scope flag and the one item that must not be lost between artifacts.

`docs/SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md:27` ends:

> ... — the only `SET_NULL` ondelete in the example tree, and the only cross-model FK in the scalars app.

Both halves are false at HEAD, and Slice 3 must correct **both in one edit**. A fix that lands only the `SET_NULL` half leaves a half-corrected sentence, which is worse than an uncorrected one because a reader cannot tell which half is current.

- **Clause 1 (`D2`), `the only SET_NULL ondelete in the example tree`** — false: `git grep -o 'on_delete=models.SET_NULL' -- 'examples/fakeshop/apps/*/models.py' | wc -l` -> **4** (`apps/kanban/models.py` twice, `apps/scalars/models.py` twice). Replacement framing: the one this slice landed in the `.py` sites — state that `NullableScalarSpecimen.partner` is a nullable cross-model FK whose `SET_NULL` ondelete clears `partner_id` and leaves the source row in place, pinned end-to-end by `test_query/test_scalars_api.py::test_scalars_set_null_ondelete_detaches_partner_in_http_query`. **No quantifier over the example tree, and no replacement census.**
- **Clause 2 (`D3`), `the only cross-model FK in the scalars app`** — false: `apps/scalars/models.py` declares three `ForeignKey`s (lines 115, 129, 176). `parent` -> self is intra-model; **`tag` -> `ScalarSpecimenTag` and `partner` -> `ScalarSpecimen` are both cross-model**, so there are two, not one. The narrowest true form is that `partner` is the only cross-model FK **out of `NullableScalarSpecimen`** — which is trivially true of a model with one FK and therefore probably not worth stating at all.

Also for Slice 3, carried from this slice's measurements:

- A schema-wide "no mutations" or "no delete mutation" sentence is false anywhere it appears: `apps/products/schema.py::DeleteItem` is the tree's one delete mutation. Scope such a sentence to the scalars app, which genuinely exposes none.
- Slice 3's own scope sweep must run **both polarities** — `every` / `all` / `always` / `each` alongside `only` / `sole` / `no other` — for the reason recorded above.

### Deferred work, for the final gate's `### Deferred work catalog`

Two items, both measured, neither closable by any slice of this cycle.

1. **`KANBAN.md:3846` carries the retired sentence verbatim, with both false clauses.** Byte-identical to `spec-026...md:27` (verified: `grep -n "only cross-model FK in the scalars app" KANBAN.md docs/SPECS/*.md` returns exactly those two lines). `KANBAN.md` is on the build plan's baseline-dirty do-not-edit list, the maintainer's fence limits this cycle to spec and `.py` files, and the file is DB-rendered — a fix is a fakeshop kanban DB edit plus `scripts/build_kanban_md.py`, never a hand edit. **No slice of this cycle closes it.** Recorded so the gap is known rather than re-discovered.
2. **`KANBAN.md:3847` and `CHANGELOG.md:175` carry `D4`'s shape** ("upstream code paths **no other example app reaches**" / "surfaces **no other example app** touches"). Both files are on the do-not-edit list; the `CHANGELOG` entry is a historical ship record, which is a further reason not to rewrite it. Slice 3's `D4` rewrite fixes the spec copy alone.

### Outcome

`revision-needed`, on exactly one item: checklist box 7, the `every column` -> declared-fields correction in the `partner` field comment. Everything else the slice set out to do landed and holds under re-measurement — four false claims retired, none introduced by a replacement's *scope*, no code touched, no process provenance, all gates green.

The escalated Medium is decided and closed: `covered transitively by every other example app` is **true at HEAD**, and is not to be re-opened by the re-pass. Worker 2's next pass touches one clause in one comment and nothing else.

Status: revision-needed

---

## Build report (Worker 2, pass 2)

Scope of this pass: checklist box 7 only - the one required change from `## Final verification (Worker 1)`. Nothing else in the slice was re-opened; the escalated Medium (#"covered transitively by every other example app") was decided true at HEAD by Worker 1 and is untouched.

### Files touched

- `examples/fakeshop/apps/scalars/models.py` - one clause in the `partner` field comment. The quantifier now ranges over the fields the model **declares**, not over its columns. Landed text:

```
    # Cross-model link: a ``NullableScalarSpecimen`` may point at one
    # ``ScalarSpecimen``. ``SET_NULL`` rather than ``CASCADE`` because every
    # field this model declares is ``null=True``: losing the target must
    # clear the FK, never delete the mirror row.
```

`examples/fakeshop/test_query/test_scalars_api.py` was **not** reached by this change and was not edited this pass - the required change is confined to one comment in one file, as Worker 1 anticipated. No other file in the tree was modified by this pass.

### Tests added or updated

None. The pass changes zero executable lines; it edits one comment.

### Validation run

Every number below was measured in this pass, as it was written.

- **The replacement's quantifier, measured against the model before writing it** (the constraint Worker 1 set: do not trade one false quantifier for another). Read from Django's own metadata, not from the source text:
  - `M._meta.local_fields` -> 13 entries. Exactly one, `id`, has `auto_created=True` and `null=False`; it is not declared by the model.
  - Declared (non-auto-created) fields -> **12**: `label`, `flag`, `score`, `price`, `occurred_on`, `occurred_at`, `occurred_time`, `payload`, `external_id`, `signed_big`, `unsigned_big`, `partner`. `all(f.null for f in declared)` -> **True**. So "every field this model declares is `null=True`" is true of exactly that set, with no member outside it.
  - `sqlite_master` for `scalars_nullablescalarspecimen` -> `"id" integer NOT NULL PRIMARY KEY AUTOINCREMENT` plus **12** `NULL` columns, **13** columns in total. This is why the old "every column" form was false and the new form is not: `id` is a column and is not a declared field.
- `uv run ruff format examples/fakeshop/apps/scalars/models.py` - **pass** (`1 file left unchanged`). Scoped to the one file, never `.`.
- `uv run ruff check --fix examples/fakeshop/apps/scalars/models.py` - **pass** (`All checks passed!`). The `COM812` notice ruff prints is the repo's standing configuration warning, not a finding from this diff.
- `uv run python scripts/check_trailing_commas.py --check examples/fakeshop/apps/scalars/models.py` - **pass**, exit **0**. This is the gate that owns the ASCII-only rule.
- `awk 'length>100'` over the file -> exactly **one** line, **153** at **102** columns: the pre-existing symbol-path citation Worker 1 re-measured and confirmed inside the 110 grace. The three lines this pass rewrote measure 73, 76 and 70 columns.
- `LC_ALL=C grep -c '[^ -~]'` over the file -> **0**.
- `git status --short` after both ruff invocations - the only modified source files are `examples/fakeshop/apps/scalars/models.py` and `examples/fakeshop/test_query/test_scalars_api.py` (the latter carrying pass 1's landed edit, untouched this pass). Everything else listed is the baseline-dirty out-of-scope set and the concurrent sessions' `024` / `025` / `026` work. Nothing unexpected, nothing reverted.
- Focused regression run, the one the plan names: `uv run pytest examples/fakeshop/test_query/test_scalars_api.py -q --no-cov` - **29 passed in 14.78s**, 0 failures, 0 collection errors. `--no-cov` because `pytest.ini`'s `addopts` auto-applies coverage; no `--cov*` flag was passed. The count is read from the run's own summary line.
- Process-provenance sweep over the three rewritten lines: no card id, commit, date, spec number, version, or "used to / previously / now / as of" wording. The comment reads as though it had always said this.

### Failability proofs

None; this pass introduced no new boundary. The exemption is the plan's, restated: the diff is one comment clause containing no branch, no guard, no validation, no rejection path, and no executable statement. Nothing exists to mutate, so no mutation was invented.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- **"every field this model declares" rather than the docstring's "Every scalar field".** Worker 1 offered the docstring form as a permitted match. It was measured and not used: `partner` is a `ForeignKey`, not a scalar field, so "every scalar field is `null=True`" would be true of the eleven scalar fields while silently excluding the very field the comment is attached to - a comment whose subject falls outside its own quantifier. "Every field this model declares" covers all twelve including `partner`, which is what makes the following clause ("losing the target must clear the FK") follow from it rather than sit beside it.
- **`null=True` is stated as the field argument, not as a can-read-`null` paraphrase.** The old wording described a runtime capability ("can read `null`") whose population is columns; naming the declaration argument keeps the sentence's subject and its evidence the same thing - the twelve `null=True` declarations visible in the lines directly above the comment.
- **Scope held to one clause.** The comment's `SET_NULL`-rather-than-`CASCADE` reasoning, its lack of a pointer, and its silence about other models, apps and files are all unchanged, per Worker 1's "everything else in that comment stays".

### Notes for Worker 3

- The whole diff of this pass is three comment lines in one file. `git diff -- examples/fakeshop/apps/scalars/models.py` against pass 1's state shows no field argument, no `on_delete` value, no import, and no executable line changed.
- The claim to check is the quantifier, and it is checkable in one command rather than by reading: the declared-field set is `[f for f in NullableScalarSpecimen._meta.local_fields if not f.auto_created]` -> 12 entries, every one `null=True`. `id` is the only `auto_created` entry and is deliberately outside the sentence.
- Checklist box 7 is ticked with its original citation text intact. Its `#"model's contract is that every column"` substring no longer resolves in source - by design, since removing that substring is the box's contract. The landed replacement is quoted verbatim under `### Files touched` above.

### Notes for Worker 1 (spec reconciliation)

- **No spec issue surfaced by this pass**, and no spec file was touched.
- **One incidental correction to a number in `## Final verification (Worker 1)`, non-blocking and not a defect in the decision.** That section reads the schema as "thirteen `NULL` columns" out of "fourteen". Measured this pass: `scalars_nullablescalarspecimen` has **13** columns - `id` plus **12** `NULL` ones - matching the 12 declared fields the same section enumerates correctly. The off-by-one does not touch the finding: `id` is `NOT NULL`, is selected in `apps/scalars/schema.py::NullableScalarSpecimenType` `Meta.fields`, and the old quantifier was false either way. Recorded because the count appears in the artifact Worker 3 re-reads.

Status: built

---

## Review (Worker 3, pass 2)

Re-review scope is Worker 2's pass-2 change (checklist box 7) plus a regression check that pass 1's four passages are undisturbed. Every number below was measured in this pass against the working tree; nothing is inherited from the plan, either build report, my own pass-1 section, or the final-verification section.

### The new clause's quantifier, re-derived independently

Landed text, `examples/fakeshop/apps/scalars/models.py:170:173`:

```
    # Cross-model link: a ``NullableScalarSpecimen`` may point at one
    # ``ScalarSpecimen``. ``SET_NULL`` rather than ``CASCADE`` because every
    # field this model declares is ``null=True``: losing the target must
    # clear the FK, never delete the mirror row.
```

Measured from Django's metadata, not from the source text:

| Measurement | Result |
| --- | --- |
| `NullableScalarSpecimen._meta.local_fields` | **13** |
| entries with `auto_created=True` | **1**, `id` (`BigAutoField`, `null=False`) |
| declared (non-`auto_created`) fields | **12**: `label`, `flag`, `score`, `price`, `occurred_on`, `occurred_at`, `occurred_time`, `payload`, `external_id`, `signed_big`, `unsigned_big`, `partner` |
| `all(f.null for f in declared)` | **True** |
| `local_many_to_many` | `[]` — no field escapes `local_fields` |
| `_meta.parents` | `{}` — no inherited field the quantifier would silently pick up |

So the sentence is true of exactly the set it names, with no member outside it and no field the enumeration misses. Worker 2's reported 13-local / 12-declared split reproduces exactly.

**Is it a fresh false universal?** No, on the standard this slice set. Its population is the fields of one model, declared in the twelve lines directly above the comment. Nothing outside this file can falsify it — no new app, no new model, no growth in `apps/kanban`. It is falsifiable only by editing this class, which is a scope the site can see. That is the same test sites 1-4 passed in pass 1, and it is the test the retired `every column` form failed: `column` reaches the implicit `id`, which the class body does not declare and which is `NOT NULL`.

### Does the clause still do the field comment's job?

Yes. The plan's load-bearing content (a) for this site is *why `SET_NULL` rather than `CASCADE`*. The sentence names both ondelete values explicitly, gives the reason (the model's all-nullable declaration means the FK must be clearable), and draws the consequence (`losing the target must clear the FK, never delete the mirror row`). Nothing was lost relative to pass 1 — the only clause that changed is the one Worker 1 required changed.

**Worker 2's ground for declining Worker 1's offered wording holds against source.** Worker 1 offered the class docstring's form, `Every scalar field is null=True, blank=True`. Measured: `partner` is `ForeignKey`, and the file's own vocabulary reserves "scalar field" for `SCALAR_MAP`-converted columns (module docstring #"Each field on ``ScalarSpecimen`` exercises a single entry"). The scalar fields of this model number **11**; `partner` is the twelfth declared field and is not one of them. A comment attached to `partner` whose quantifier excludes `partner` would not support the clause that follows it. Declining was correct, and the substituted form ("every field this model declares") is the one that makes the consequence follow rather than sit beside the premise.

### Regression check on pass 1's four passages

`git diff HEAD -- examples/fakeshop/apps/scalars/models.py examples/fakeshop/test_query/test_scalars_api.py` -> **18 added lines**, unchanged in count from pass 1 (the site-2 replacement is three lines in both passes). Read end to end:

- Site 1 (class docstring, detach-and-survive statement + the pointer) — byte-identical to pass 1.
- Site 3 (test docstring) and site 4 (`# TRIGGER` comment) — byte-identical to pass 1; `test_scalars_api.py` carries no pass-2 hunk at all.
- Site 2 — the only passage this pass touched.

**Zero executable lines added, verified mechanically.** Sweeping the added-line set for `def|class|import|from|return|if|for|while|assert|raise|with|try`, `=`, and `()` yields three hits, each read in context and each prose inside a docstring or `#` comment: `from the intra-model self-FK…`, `` `null=True` `` as a quoted field argument, and `` `target.delete()` `` named in the test docstring. No field argument, no `on_delete` value, no assertion, no import changed.

Retired phrasings, repo-wide excluding this cycle's artifacts: `model's contract is that every column`, `place in the example tree that exercises`, `row instead of cascading`, `Pins the only`, `mutations aren't in the example schema` -> **0 hits each**.

### The count discrepancy Worker 2 flagged: Worker 2 is right, Worker 1's number is wrong

`## Final verification (Worker 1)` reads the schema as "thirteen `NULL` columns" of "fourteen". Settled from the table definition itself:

```
CREATE TABLE "scalars_nullablescalarspecimen" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
 "label" text NULL UNIQUE, "flag" bool NULL, "score" real NULL, "price" decimal NULL,
 "occurred_on" date NULL, "occurred_at" datetime NULL, "occurred_time" time NULL,
 "payload" text NULL CHECK (...), "external_id" char(32) NULL, "signed_big" bigint NULL,
 "unsigned_big" bigint unsigned NULL CHECK (...), "partner_id" bigint NULL REFERENCES ...)
```

**13 columns: `id` (`NOT NULL`) plus 12 `NULL`.** Worker 2's `12 of 13` is correct; Worker 1's `13 of 14` is off by one in both halves. The count is internally inconsistent with the same section's own correctly-enumerated twelve declared fields, and with its own `local_fields` framing — a model with 12 declared fields plus one implicit pk has 13 columns, not 14.

The finding it supports is unaffected: `id` is `NOT NULL`, is selected in `apps/scalars/schema.py::NullableScalarSpecimenType` `Meta.fields`, and so `every column can read null` was false regardless of the total. Recorded as a Low against the artifact rather than the source, because a wrong number in the artifact reaches the final gate reading as measured. One further incidental in the same paragraph: it calls `id` an `AutoField`; it is a `BigAutoField` (the project's `DEFAULT_AUTO_FIELD`). Neither correction changes any disposition.

### The escalated Medium: closure accepted, not re-opened

Worker 1's reading is right and my pass-1 measurement was of the wrong subject. Verified independently rather than conceded: `apps/accounts/schema.py::UserType` `Meta.fields` is `("id", "username", "email")` over `auth.User` — `AutoField`, `CharField`, `EmailField`, all trivial-collapse `SCALAR_MAP` rows — and the app is composed into the root `Query` with its own live `test_query/` module. Coverage of a converter row is exercise over the live surface, not ownership of the model that declares the column, which is what `transitively` denotes. `covered transitively by every other example app` is true at HEAD. Closed; the sweep-vocabulary lesson (a census spelled positively is invisible to a negative-vocabulary sweep) is the part that carries forward, and Worker 1 has already routed it to Slice 3.

### High:

None.

### Medium:

None.

### Low:

#### `## Final verification (Worker 1)` states the column count as 13-of-14; it is 12-of-13

Artifact-internal, not source. Measured above from `sqlite_master` and from `_meta.local_fields`. **Not held**: the number is not load-bearing for the finding it supports, no source text repeats it, and Worker 1 owns that section — Worker 3 cannot edit a prior worker's section. Recorded here so the final gate reads the corrected number rather than the stated one. Same paragraph, same disposition: `id` is a `BigAutoField`, not an `AutoField`.

### DRY findings

None. The pass-2 diff is one comment clause; it adds no symbol, no literal, no helper, and no abstraction, so `### The existence challenge` has no subject. The one-authoritative-plus-narrow-local split from pass 1 is intact: site 2 still carries no pointer and restates no other site's sentence, and the new clause introduces no phrase shared with the class docstring above it. `scripts/review_inspect.py` **not run**, recorded as a deliberate skip on the same ground as pass 1 — its output is repeated-literal and import-boundary evidence over Python constructs, and this diff contains none.

### Failability proofs, hot-path budget, floor verification

- **Failability proofs — exemption confirmed and recorded, not blank.** Worker 2's pass-2 report carries the heading with `None; this pass introduced no new boundary.` beneath it. Verified against the diff rather than the declaration: three comment lines, no branch, no guard, no gate, no rejection path, no executable statement — nothing exists that could be mutated to stop holding. Independent re-run set: **empty, and legal**, since the mandatory floor is computed over boundaries the diff introduces and this diff introduces zero. No proof was invented and none is owed.
- **Hot-path budget — `Not applicable; plan declares no hot path.` stands.** No added line executes.
- **Floor verification — `Not applicable; plan declares floor-verification scope none.` stands.** No import, no Django / Strawberry / channels API, no version-sensitive construct in the diff.

### Layout and encoding gates

- `uv run python scripts/check_trailing_commas.py --check <both paths>` -> exit **0**. This is the gate that owns the ASCII-only rule.
- `LC_ALL=C grep -c '[^ -~]'` -> **0** on both files. The rewritten lines use `-`, matching the surrounding file.
- `uv run ruff check <both paths>` -> `All checks passed!`. `uv run ruff format --check <both paths>` -> `2 files already formatted`.
- **Re-wrapped-comment line-length audit**, the place a violation would hide. `awk 'length>100'` in the working tree: `models.py` **1** line (153, 102 columns — the unbreakable symbol path, pre-existing since pass 1 and already adjudicated inside the 110 grace); `test_scalars_api.py` **4** lines (259/105, 969/111, 1015/120, 1112/120). The same command over `git show HEAD:<path>` returns those same four in `test_scalars_api.py` at 259/970/1016/1113 — identical content, shifted one line by pass 1's re-wrap — and **0** in `models.py`. The three lines pass 2 rewrote measure 73, 76 and 70 columns. No new long line. (`pyproject.toml` sets `line-length = 99` with `max-line-length = 110`; the plan's step-5 "Line length 100" is one off the configured value and affects no landed line.)

### Spec slice checklist audit

Seven boxes, all `- [x]`. Boxes 1-6 re-audited against the current diff independently of pass 1: every tick still has a matching change, and pass 2 disturbed none of them.

- Box 7 — **tick stands.** Its contract is that the `partner` comment quantifies over the fields this model declares and not over its columns. Landed: the `every column` form returns 0 hits repo-wide outside this artifact, and the replacement's quantifier is the 12 declared fields, all `null=True`, measured above. The box's `#"model's contract is that every column"` citation no longer resolves in source, which is the box's contract, not rot.
- Boxes 1-5 — retired phrasings return 0 hits repo-wide; the preserved clauses (`distinct from the intra-model self-FK on ScalarSpecimen.parent`, the setup-trigger-observe paragraph, the three numbered assertions, the ORM-trigger conclusion) are all present in the current file.
- Box 6 — `git status --short` lists exactly two modified `.py` files from this slice. The three other modified `.py` files in the tree (`django_strawberry_framework/_strawberry_patches.py`, `django_strawberry_framework/optimizer/hints.py`, `tests/optimizer/test_hints.py`) are the build plan's baseline-dirty out-of-scope set; untouched and unreverted.

**Process provenance** — `grep -icE 'spec-[0-9]|card|commit|previously|used to|as of|no longer|formerly|202[0-9]|TODO|slice|pass [0-9]'` over the 18 added lines -> **0**. The comment reads as though the file had always said it.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` -> **0 lines**. `__all__` and the re-export list unchanged; nothing under `django_strawberry_framework/` is read or written by this slice.

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md`.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. The pass-2 edit is a class-body comment, and `scripts/build_tree_md.py` renders **module** docstrings only, so `docs/TREE.md` needs no regeneration and this slice stays clear of the concurrent sessions' generated-file surface.

### Test staleness

Re-swept independently of the slice's file list. `git grep -ln '__doc__' -- tests examples` -> **0 files**; nothing in any of the three test trees asserts on source prose, so no test could go stale on a comment edit. Independent regression run reproduced: `uv run python -m py_compile <both paths>` -> OK, and `uv run pytest examples/fakeshop/test_query/test_scalars_api.py -q --no-cov` -> **29 passed in 14.62s**, 0 failures, 0 collection errors, matching both prior runs. No `--cov*` flag at any point in this review.

### What looks solid

- The re-pass did the one required thing and nothing else. Three lines, one clause, one file; `test_scalars_api.py` was correctly left alone.
- The replacement quantifier is checkable in one command rather than by reading, and Worker 2 wrote it that way deliberately — naming the declaration argument (`null=True`) instead of a runtime paraphrase (`can read null`) keeps the sentence's subject and its evidence the same object.
- Declining Worker 1's offered wording was the right call and the ground for it is measurable, not stylistic: the offered form's quantifier excludes the field the comment is attached to.
- Worker 2 flagged a wrong number in a section it does not own instead of quietly working around it. That is the behavior that stops a mis-measurement reaching the final gate as fact.

### Temp test verification

- Temp test files used: **none**. `docs/builder/temp-tests/slice-2-026/` was not created.
- Disposition: not applicable. The review question is whether one comment clause is true of the model, which is answered by reading the model's metadata; this slice adds no assertion for a temp test to exercise.

### Notes for Worker 1 (spec reconciliation)

- **Correct the column count when the final gate quotes it.** `## Final verification (Worker 1)` says thirteen `NULL` columns of fourteen; the table has **13 columns, 12 of them `NULL`**. The Low #1 disposition is unaffected. Also in that paragraph: `id` is a `BigAutoField`.
- **The escalated Medium is closed and I concur on the measurement**, verified independently above rather than accepted. No re-open.
- Everything carried forward from pass 1 stands unchanged and is not restated here: the two out-of-scope parallel sites (`KANBAN.md:3846`, `KANBAN.md:3847` / `CHANGELOG.md:175`), the two-false-clause instruction to Slice 3, and the app-scoped-mutation wording rule are all already recorded in `## Final verification (Worker 1)`.

### Review outcome

`review-accepted`. High: none. Medium: none — pass 1's only Medium was escalated, decided by Worker 1, and verified closed here. Low: one, artifact-internal (a wrong column count in a section Worker 3 cannot edit), recorded and not held. DRY: none. Checklist: seven boxes, seven ticks, each with a matching change. The slice's total contribution to the tree is 18 prose lines in two files, zero executable lines, four retired false claims, and no new false universal.

Status: review-accepted

---

## Final verification (Worker 1, pass 2)

Second final verification, after one revision loop. Every number below was measured in this pass against the working tree; nothing is inherited from the plan, either build report, either review, or my own pass-1 section — including the numbers those sections and this one already agreed on.

### The count in `## Final verification (Worker 1)` was wrong, and is corrected

Worker 3's pass-2 Low is upheld. Re-measured here from both sources independently:

| Measurement | Command | Result |
| --- | --- | --- |
| columns in `scalars_nullablescalarspecimen` | `sqlite_master` `CREATE TABLE` text, columns enumerated | **13** — `id` plus 12 |
| of those, `NULL` | same | **12** |
| `NullableScalarSpecimen._meta.local_fields` | Django metadata | **13** |
| `auto_created=True` entries | same | **1** — `id`, `BigAutoField`, `null=False` |
| declared (non-`auto_created`) fields | same | **12**, `all(f.null ...)` -> **True** |
| `local_many_to_many` / `_meta.parents` | same | `[]` / `{}` — nothing escapes `local_fields` |

`12 of 13`, not `13 of 14`. My pass-1 paragraph was off by one in both halves while its own field enumeration four lines earlier listed the twelve correctly — the number was asserted, not measured, in a section whose subject is a claim that was asserted rather than measured. **That paragraph is now corrected in place** (`## Final verification (Worker 1)`, the Low #1 block): `thirteen` -> `twelve`, `fourteen` -> `thirteen`, with an inline note pointing here so a reader is never left holding two numbers and no verdict. No disposition changes: `id` is `NOT NULL`, is selected in `apps/scalars/schema.py::NullableScalarSpecimenType` `Meta.fields`, and `every column can read null` was false at any total.

One correction to the correction, re-derived rather than accepted: Worker 3 places the `AutoField` mislabel "in the same paragraph". It is not — `grep -n 'AutoField'` over this artifact returns four hits, and the only one calling `id` an `AutoField` is line 299, inside Worker 3's **own** pass-1 Low. The type is nonetheless `BigAutoField`, and my corrected paragraph now says so; Worker 3's pass-1 text is not mine to edit.

### Spec slice checklist audit — all seven, re-audited against the diff

Seven boxes, all `- [x]`. Audited independently of Worker 3's pass-2 audit, against `git diff HEAD -- examples/fakeshop/apps/scalars/models.py examples/fakeshop/test_query/test_scalars_api.py` (**18 added lines**, 5 hunks, counted in this pass).

| Box | Verdict | Proof run in this pass |
| --- | --- | --- |
| 1 — docstring census gone, self-FK clause preserved, live pin named | **tick stands** | the removed lines in the diff carry `and the only place in the example tree that exercises SET_NULL ondelete planning under the optimizer`; the added lines carry `distinct from the intra-model self-FK on ``ScalarSpecimen.parent``` and the symbol-path pointer. `git grep -F "place in the example tree that exercises"` outside this cycle's artifacts -> **0 files** |
| 2 — `partner` comment scoped to this edge, no other model/app/file claimed | **tick stands** | `git grep -F "row instead of cascading"` outside this cycle's artifacts -> **0 files**; the landed clause names only this model's declaration and the two ondelete values |
| 3 — test docstring carries no population claim; paragraph and three assertions survive | **tick stands** | `git grep -F "Pins the only"` -> **0 files**; the diff preserves the setup-trigger-observe paragraph and all three numbered assertions, with the permitted `cascade` -> `delete` / `the ondelete` repair visible and claim-neutral |
| 4 — `# TRIGGER` premise app-scoped, ORM conclusion kept | **tick stands** | `git grep -F "mutations aren't in the example schema"` -> **0 files**; premise re-derived here: `git grep -n 'class Delete' -- 'examples/fakeshop/apps/*/schema.py'` -> exactly **1** hit, `apps/products/schema.py:261::DeleteItem`, so schema-wide was false and app-scoped is true |
| 5 — no process provenance, no cross-site restatement | **tick stands** | `grep -icE 'spec-[0-9]\|card\|commit\|previously\|used to\|as of\|no longer\|formerly\|202[0-9]\|TODO\|slice\|pass [0-9]'` over the 18 added lines -> **0**; the four passages share no sentence and one pointer exists in total |
| 6 (the box this pass's revision loop opened) — `every column` -> the fields this model declares | **tick stands** | `git grep -F "model's contract is that every column"` outside this cycle's artifacts -> **0 files**; the landed quantifier is the 12 declared fields, `all(f.null)` **True**, with `local_many_to_many` `[]` and `parents` `{}` so nothing escapes the enumeration. `id` is `auto_created` and deliberately outside the sentence |
| 7 — comment/docstring lines only, exactly two files, gates run | **tick stands** | the diff's added lines contain no `def`, `class`, `import`, assignment, call, field argument, or `on_delete` value — the three `=`/`()` hits are the prose strings ``null=True`` and ``target.delete()`` inside comment and docstring text. `git status --short` lists **5** modified `.py` files: these two plus `_strawberry_patches.py`, `optimizer/hints.py`, `tests/optimizer/test_hints.py`, all three on the build plan's baseline-dirty out-of-scope list, untouched and unreverted |

No box was over-ticked, none needed ticking, and none is left `- [ ]`. `### Spec changes made (Worker 1 only)` therefore carries no deferral reason for any box.

### Plan contract as amended, and the three declarations

- **The amended contract landed and nothing else moved with it.** Pass 2's required change was box 6 alone; `test_scalars_api.py` carries no pass-2 hunk, and pass 1's three other passages are byte-identical in the current diff to pass 1's. The added-line count is 18 in both passes because site 2's replacement is three lines either way.
- **Worker 2's ground for declining my offered wording is correct and I accept it.** I offered the class docstring's `Every scalar field is null=True, blank=True`. Re-measured: `partner` is a `ForeignKey` and the file reserves "scalar field" for `SCALAR_MAP`-converted columns, of which this model has **11**; a quantifier attached to `partner` that excludes `partner` would not carry the clause that follows it. `every field this model declares` is the correct form and is the one that landed.
- **Ownership partition: none — holds.** One cohort, one builder, one reviewer, two passes; no second cohort's diff exists.
- **Hot-path declaration: none — re-verified against the landed diff.** No added line executes; `uv run python -m py_compile` on both files succeeds, so the modules parse with zero runtime surface changed.
- **Floor-verification scope: none — re-verified.** No import, no Django / Strawberry / channels API, no version-sensitive construct in the diff.
- **Failability-proof exemption: still correct, and recorded rather than blank.** Both build reports carry `None; this pass introduced no new boundary.` under the heading; verified against the diff, the added lines contain no branch, guard, gate, or rejection path, so there is nothing to mutate. No proof was invented, which is the required outcome of the exemption.
- **Layout gates, re-run here:** `LC_ALL=C grep -c '[^ -~]'` -> **0** on both files. `awk 'length>100'` -> `models.py` **1** line (153, 102 columns, the unbreakable symbol path, inside the 110 E501 grace); `test_scalars_api.py` **4** lines (259/105, 969/111, 1015/120, 1112/120), the same four content lines present at `HEAD` (at 259/970/1016/1113), shifted one line by pass 1's re-wrap. No new long line in either pass.
- **Focused test run: not re-run in this pass, deliberately.** `AGENTS.md` #"No pytest after edits" — this pass edits no `.py` file at all, only this artifact. The plan's one focused run was executed three times (`29 passed`, `--no-cov`, no `--cov*`) across the two build passes and both reviews, and the failure mode it guards (a mangled docstring quote breaking import) is proven here by `py_compile`.
- **Staged-anchor sweep:** `git grep -n "TODO(spec-026"` -> **0** repo-wide.
- **Cross-slice duplication:** unchanged from pass 1. Slice 1 wrote the rationale companion and the spec pointer; Slice 2 wrote four prose passages in two `.py` files. No shared sentence, no repeated literal, no helper in either.

### Both-polarity scope sweep, run here because pass 1's was single-polarity

The pass-1 plan's `### Scope check` swept negative vocabulary only, which is why the module-docstring universal reached review as an escalation instead of a plan item. Re-run over the two fenced files with **both** polarities — `the only` / `the sole` / `no other` / `only place` / `only app` / `in the example tree` **and** `every` / `all <noun>` / `each <noun>` / `always`:

- **23 hits.** Every one read in context. The only example-tree-wide census is `models.py` #"covered transitively by every other example app", which is the escalated Medium, decided true at HEAD, closed in pass 1 and independently re-verified by Worker 3 in pass 2. **Not re-opened.**
- Four hits are per-app or per-file claims, each re-measured true: `models.py` #"where every relation crosses a model boundary" (all 11 relations declared in `apps/library/models.py` target another model; none is `"self"`), `test_scalars_api.py` #"every reverse-FK in the library app" (same measurement), `models.py` #"that pins every entry in one query", and `models.py` #"like every other entry in this app". Each quantifies over a scope its own file names, which is the standard this slice set.
- The rest quantify over rows, fields, or seed values inside a single test or model — not censuses.

Recorded so Slice 3 inherits a swept population rather than a swept vocabulary.

### Spec changes made (Worker 1 only)

**None this pass.** The spec was not edited; Slice 3 owns the reconstruction. No checklist box is deferred, so no deferral reason is owed.

Per-spawn status-line re-verification (`worker-1.md` `## Spec status-line re-verification`): `docs/SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md` lines 1-5 are unchanged since Slice 1's close. `Status:` is still the `D9` placeholder and `## Planning note` is still the single word `shipped` (`D10`); nothing this slice landed falsified either, and both are Slice 3's. `check_spec_glossary.py --spec docs/SPECS/spec-026-…md` re-run in this pass -> `OK: 3 terms`, exit 0.

### Carried to Slice 3 (spec reconstruction), every locator re-derived in this pass

Not carried on trust from pass 1 — each line was re-read and each count re-run here.

1. **`docs/SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md:27` carries TWO false clauses in ONE sentence. Both must be corrected in the same edit.** A fix landing only the `SET_NULL` half leaves a half-corrected sentence, which is worse than an uncorrected one because the reader cannot tell which half is current.
   - **Clause 1 (`D2`), `the only SET_NULL ondelete in the example tree`** — false. `git grep -o 'on_delete=models.SET_NULL' -- 'examples/fakeshop/apps/*/models.py' | wc -l` -> **4**, at `apps/kanban/models.py:843` and `:995` and `apps/scalars/models.py:133` and `:180`. (Occurrences via `grep -o | wc -l`, never `grep -c`.) Replacement framing: the one the `.py` sites now carry — `NullableScalarSpecimen.partner` is a nullable cross-model FK whose `SET_NULL` ondelete clears `partner_id` and leaves the source row in place, pinned end-to-end by `test_query/test_scalars_api.py::test_scalars_set_null_ondelete_detaches_partner_in_http_query`. **No quantifier over the example tree, and no replacement census.**
   - **Clause 2 (`D3`), `the only cross-model FK in the scalars app`** — false. `apps/scalars/models.py` declares three `ForeignKey`s: `parent` (line 115, `"self"`, intra-model), `tag` (line 129 -> `ScalarSpecimenTag`) and `partner` (line 176 -> `ScalarSpecimen`). **`tag` and `partner` are both cross-model**, so there are two, not one. The narrowest true form — `partner` is the only cross-model FK *out of* `NullableScalarSpecimen` — is trivially true of a model with one FK and probably not worth stating.
2. **Scope any "no delete mutation" / "no mutations" claim to the scalars app.** Schema-wide it is false: `git grep -n 'class Delete' -- 'examples/fakeshop/apps/*/schema.py'` -> exactly **1** hit, `apps/products/schema.py:261::DeleteItem`. `apps/scalars/schema.py::Mutation` genuinely exposes none.
3. **Slice 3's own scope sweep must run BOTH polarities** — `every` / `all` / `each` / `always` alongside `only` / `sole` / `no other`. A positively-spelled universal is invisible to a negative-vocabulary sweep, and that exact blind spot cost this slice a revision loop.

### Deferred work catalog, for the final gate — re-derived, not carried forward on trust

Three items. Each locator was re-run in this pass; a catalog is a claim.

1. **`KANBAN.md:3846` carries `spec-026…md:27` verbatim, both false clauses.** Verified: `grep -rn "only cross-model FK in the scalars app" KANBAN.md docs/SPECS/ CHANGELOG.md` returns exactly **two** lines, `KANBAN.md:3846` and `docs/SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md:27`, and they are the same sentence.
2. **`KANBAN.md:3847` carries `D4`'s shape** — "upstream code paths **no other example app reaches**", followed by the five paths, four of which `apps/library` already reached at the ship commit.
3. **`CHANGELOG.md:175` carries the same shape** — "surfaces **no other example app** touches", inside the `0.0.7` ship entry. `grep -n "no other example app" KANBAN.md CHANGELOG.md` returns exactly these two lines and no third site.

**No slice of this cycle closes any of the three**, and this is a fence, not an omission: `KANBAN.md` and `CHANGELOG.md` are both on the build plan's baseline-dirty do-not-edit list; the maintainer's scope fence limits this cycle to spec and `.py` files; `KANBAN.md` is DB-rendered, so a fix there is a fakeshop kanban DB edit plus `scripts/build_kanban_md.py`, never a hand edit; and the `CHANGELOG` entry is a historical ship record. Slice 3's `D2`/`D3`/`D4` work fixes the spec copies alone.

### Summary

Slice 2 retired four false claims from two `.py` files — a tree-wide `SET_NULL` census in the `NullableScalarSpecimen` class docstring, the same census on the `partner` field comment, a population claim in the live test's docstring, and a false schema-wide premise in that test's `# TRIGGER` comment — and replaced each with a statement verifiable from the file it lives in plus at most the one file it names. 18 added lines, zero executable lines, two files, no new public surface, no process provenance. The one revision loop corrected a false universal the slice's own first pass authored (`every column can read null`, false because the implicit `BigAutoField` `id` is a column); the escalated Medium was measured true at HEAD and closed by both remaining roles; and a wrong column count in my own prior section is corrected in place with the verdict recorded above.

### Outcome

`final-accepted`. Seven checklist boxes, seven ticks, each re-audited against the diff in this pass. Plan contract as amended delivered in full; ownership-partition, hot-path and floor-verification declarations all `none` and all re-verified against the landed diff; the failability-proof exemption holds and is recorded rather than blank. No spec edit made and none owed by this slice. Everything Slice 3 and the final gate need is on disk above, with every locator re-derived here.

Status: final-accepted

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
