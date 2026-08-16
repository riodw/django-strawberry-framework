# Build: R2b — close the untested `strawberry.field(resolver=...)` relation-assignment claim (F20)

Spec reference: `docs/SPECS/spec-010-foundation-0_0_4.md` `### Manual annotation contract for relation fields` (lines 69-82; the four-shape list is lines 77-81, and the shape this item pins is line 80)
Build plan: `docs/builder/build-010-foundation-0_0_4.md` `### R2b finding — a second uncovered shape, found by R2's final verification`
Status: final-accepted

## Plan (Worker 1)

### Preamble: declarations carried from the build plan

Copied as written from `docs/builder/build-010-foundation-0_0_4.md`, with this item's assessment beside each.

- **Ownership partition:** `none; sequential items.` R2b writes `tests/types/test_definition_order.py`, which R2 also wrote. R2 is `final-accepted` and closed, so there is no live overlap — but the two share one file and could never have run concurrently under `docs/builder/BUILD.md` `### Parallel cohorts under a declared ownership partition` ("Any file owned by two cohorts serializes them"). **Assessment: unchanged.** R2b's writable set is one already-tracked test file plus its own artifact and an untracked proof manifest.
- **Hot-path declaration:** `none.` R2b adds one test row and no package source. **Assessment: unchanged, and affirmatively so.** No package `.py` file is in the writable set at all, so there is no code path — hot or cold — whose cost this item can change. `docs/builder/worker-1.md` `### Hot-path declaration` warns against resolving a hard measurement by declaring `none`; that warning does not reach here, because the reason is absence of production diff, not measurement difficulty.
- **Floor-verification scope:** **R2b is IN scope — this is a change from the plan's "R2 only" text, and it is a widening, not a correction of an error.** Reasoning below.

#### Floor verification: scoped, and the owning pass named

`docs/builder/BUILD.md` `## Floor verification` is the single canonical statement of the floor versions; they are read from that section (`## Floor verification`, the sentence beginning "The supported floor is"), never restated from memory here:

- **Django 5.2.16, Python 3.10, strawberry-graphql 0.316.0.**

R2 was scoped because a `strawberry.lazy` forward reference is resolved by Strawberry at schema-construction time. R2b reaches the same seam by a different route and therefore inherits the scope:

- The row ends in a real `strawberry.Schema(query=Query)` build, which is `### When it is required`'s "schema and type construction against Strawberry internals" on its face.
- More specifically, the row depends on a **Strawberry precedence rule that is not this package's**: when a `StrawberryField` built by `strawberry.field(resolver=fn)` is assigned to a name that *also* carries a class annotation, the annotation supplies the GraphQL type and the resolver's return type does not. Worker 1's R2 pass measured this same precedence from the other side (`StrawberryField.resolve_type` prioritises the class annotation over the resolver return type). A precedence rule inside a dependency is exactly the class of behavior a floor run exists to pin, because it can differ between 0.316.0 and the version the shared `.venv` happens to carry.
- **Focused scope:** `tests/types/test_definition_order.py`, no `--cov*` flags.
- **Owning pass: Worker 2's build pass**, mirroring R2. The final gate (`docs/builder/bld-010-final.md`) is the backstop that confirms it happened, not a second owner. Worker 2 records the scratch venv path, the resolved versions as read by `uv pip list --python <venv>/bin/python`, and pass/fail under `### Floor verification` in its build report. **Never install into the shared `.venv`** (`docs/builder/BUILD.md` `### How to build the floor venv`).

#### Boundary count and the split question

`docs/builder/BUILD.md` `### Slice splitting` obliges an answer in writing, not a split.

**New boundaries introduced by this item: zero.** R2b adds a test row and no guard, cap, rejection path, or validation branch. The failability proof it owes (below) is against an **existing** boundary — the phase-2 skip in `types/finalizer.py::finalize_django_types` — which is precisely `### What needs a proof, and what does not`'s point that the obligation attaches to boundaries rather than to changed lines. One test row is one unit; there is nothing to split.

### Answers to the four planning questions

These four were posed in the dispatch and each is answered from measurement, not inference (`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`). The measurements were taken with a scratchpad probe outside the repository — `django.setup()` against `config.test_settings` with `examples/fakeshop` on the path — because the question "does this shape work at `HEAD`?" is answered by executing it, never by reading the call graph.

#### 1. Is the assignment form a distinct code path, or a distinction the collection seam does not draw?

**Distinct. The spec's four-shape enumeration stands, and no spec correction is owed on this point.**

The classification *predicate* is shared: `django_strawberry_framework/types/base.py::_consumer_assigned_fields` tests `isinstance(value, StrawberryField)` on the class-dict value, and both forms put a `StrawberryField` there. Had that been the whole story, F20 would have been a finding about the spec's enumeration rather than a test to write, and this section would be planning a spec correction instead.

It is not the whole story. The spec spells the assignment form as `items: list["ItemType"] = strawberry.field(resolver=custom_items)` (line 80 and the worked example on line 73) — **an annotated assignment**. That produces a definition state no existing row pins, because the name lands in *both* relation sets:

| shape | `consumer_annotated_relation_fields` | `consumer_assigned_relation_fields` | pinned at `HEAD` by |
|---|---|---|---|
| annotation-only | `{"items"}` | `frozenset()` | `tests/types/test_definition_order.py::test_annotation_only_relation_override_keeps_generated_resolver` |
| `Annotated[..., strawberry.lazy(...)]` | `{"items"}` | `frozenset()` | R2's two rows |
| `@strawberry.field` decorator | `frozenset()` | `{"items"}` | `::test_assigned_relation_field_override_keeps_consumer_resolver` |
| **`= strawberry.field(resolver=...)` assignment** | **`{"items"}`** | **`{"items"}`** | **nothing** |

Measured, not assumed. The probe printed, for the annotated-assignment shape:

```
authored      : ['items']
annot_rel     : ['items']
assign_rel    : ['items']
annot_scalar  : []
assign_scalar : []
pending       : []
class __dict__ items type: <class 'strawberry.types.field.StrawberryField'>
class annotations items  : list[__main__.ItemType]
```

Two consequences make the shape load-bearing rather than cosmetic:

- The **double membership** is the only configuration in which the two skip sets phase 2 consumes disagree in a way that matters. `types/finalizer.py::finalize_django_types` passes `skip_field_names=definition.consumer_assigned_relation_fields` to `types/resolvers.py::_attach_relation_resolvers` and `skip_field_names=definition.consumer_authored_fields` (the broader union) to `::_attach_file_resolvers`. In the annotation-only shape the narrower set is empty and the generated resolver is *supposed* to attach; in this shape the narrower set is populated and it must not. Nothing currently exercises the state where a name is in the union *and* in the narrower set.
- The **type source differs**. In the decorator form the GraphQL type comes from the decorated function's return annotation; here it comes from the class annotation, with the resolver's own return type not consulted. That is Strawberry-internal precedence, and is why this item takes a floor scope.

`### Notes for Worker 1 (spec reconciliation)` therefore records no shape-collapse finding. **The item's shape is unchanged and Worker 0 need not re-partition.** Per `docs/builder/BUILD.md` `## Review rounds`, this plan's prescribed remediation remains a hypothesis: if Worker 2's own execution contradicts the table above, that is a source or spec finding and the plan is re-partitioned — never a test bent to fit.

#### 2. What must the row assert to be distinguishing rather than merely observable?

`docs/builder/BUILD.md` `### Query-shape tests must pin the load-bearing property, not observability` is the governing rule, and R2's near-miss is the governing precedent: its first-draft assertion would have passed vacuously because synthesis and the override named the same class.

**The same trap does apply here, on a different axis, and the design below is against it.**

The measurement that settles it: the probe was re-run with phase 2's skip neutralized in-process (wrapping `_attach_relation_resolvers` so `skip_field_names` is always empty), which is the semantic equivalent of the mutation the failability proof will apply. What changed and what did not:

| observation | skip intact | skip neutralized | distinguishing? |
|---|---|---|---|
| `base_resolver.wrapped_func` | `custom_items` (the consumer's function) | `_make_relation_resolver.<locals>.many_resolver` | **yes** |
| `base_resolver.wrapped_func is custom_items` | `True` | `False` | **yes** |
| `field.type` / SDL line | `items: [ItemType!]!` | `items: [ItemType!]!` | **no — identical** |
| the four definition sets | as tabled above | as tabled above | no — collection-phase state, unaffected by phase 2 |

So: **a wire/SDL assertion is non-distinguishing for this boundary and must not be presented as the pin.** The whole GraphQL surface is byte-identical whether the consumer's resolver survived or was clobbered by the framework's — the exact failure mode `### Query-shape tests must pin the load-bearing property, not observability` describes.

The row must therefore assert **both halves of the contract spec line 73 states**, and the identity assertion carries both at once:

- **(A) The consumer's resolver wins** — execution routes through it.
- **(B) The framework's generated resolver is not attached over it** — the `skip_field_names=definition.consumer_assigned_relation_fields` boundary.

`base_resolver.wrapped_func is custom_items` is the single assertion that flips on (B) and proves (A): if the framework attached over the consumer's field, the identity fails. Identity (`is`) rather than a name or `__qualname__` comparison is deliberate — it is non-vacuous by construction and cannot be satisfied by a coincidentally-named framework function.

**No competing registration is required, and this is a decided answer, not a deferral.** R2 needed a `Meta.primary = True` sibling because its assertion was about *which class the field is typed as*, and without the sibling synthesis and the override named the same class. R2b's assertion is about *which function is bound*, and the two candidate functions are already distinct by construction and measured distinct above. Adding a primary sibling here would make the SDL/type assertion distinguishing for a *synthesis-path* regression — but that regression is R2's territory and is already double-pinned by `::test_cross_module_lazy_relation_override_wins_over_the_registered_primary_type`. Duplicating it would be a near-copy pinning no new boundary, which `### DRY analysis` below records as the duplication risk this plan avoids.

#### 3. Where does the row go, and does it need a fixture?

**File:** `tests/types/test_definition_order.py`. **Position:** immediately after `::test_assigned_relation_field_override_keeps_consumer_resolver` (currently lines 258-284), which is its sibling shape — the same contract clause, the other spelling. The file is 1284 lines and holds all four shapes' rows; splitting one row into a new module would strand it from `_strawberry_field` and the `_isolate_registry` autouse fixture.

**No fixture module is needed, and `tests/types/fixtures/lazy_relation_target_module.py` must not be touched.** Confirmed: R2 needed a cross-module fixture because a `strawberry.lazy("module.path")` reference is only meaningful when the target is genuinely not importable in the declaring module — that is the escape hatch's whole point. The assignment form carries no module-path indirection at all; its target type is an ordinary class defined in the test body, exactly as the decorator row's is. The fixture file is R2's, closed, and out of this item's writable set.

#### 4. Failability proof — owed, with the mutation and a measured-unique anchor

**A proof is owed.** Worker 0's reading is correct and this pass confirms it independently. R2's proof mutated the relation-branch consumer-authored short-circuit in `types/base.py::_build_annotations` — a **collection-phase** boundary. R2b's contract half (B) rests on a **different, later** boundary: the phase-2 resolver-attachment skip in the finalizer. R2 established that the annotation-only rows do *not* fail when a neighbouring short-circuit is removed, so nothing is assumed here about what pins what; the probe above measured the flip directly.

- **Boundary:** `django_strawberry_framework/types/finalizer.py::finalize_django_types #"skip_field_names=definition.consumer_assigned_relation_fields"`.
- **Anchor, measured unique.** The naive anchor is *not* unique and would abort the entry rather than remove the boundary — the exact failure mode R2's plan hit. Measured with `python3 -c` over the file text (occurrences, not matching lines):
  - `"consumer_assigned_relation_fields"` -> **2** occurrences (one is prose in the comment two lines below). **Do not use.**
  - `"            skip_field_names=definition.consumer_assigned_relation_fields,\n"` (12-space indent, trailing comma, trailing newline) -> **1** occurrence. **Use this.**
- **Replacement:** `            skip_field_names=frozenset(),` — this **removes the boundary** rather than perturbing code near it: phase 2 then attaches the generated relation resolver over every consumer-assigned relation field, which is what the skip exists to prevent.
- **Scope as run:** `tests/types/test_definition_order.py` (45 rows, green at plan time — see `### Test additions / updates`). No `-x`, no `--maxfail`, no `--cov*`; the tool refuses them.
- **Expected failing rows: 2** — the new R2b row and the existing `::test_assigned_relation_field_override_keeps_consumer_resolver`. This is an expectation, not a recorded measurement; Worker 2 records the measured node-id list, never a count.
  - **2 rows clears the weakly-pinned rule** (0 or 1 is `revision-needed`) but sits **at or below Worker 3's mandatory independent re-run floor of 3**, so Worker 3 will re-run this proof at the scope Worker 2 records. Worker 2 should expect that and record the scope precisely.
  - **If the measurement comes back 0 or 1, it is weakly pinned, not harness-impossible.** The probe above exhibited the flip in-process, so the harness *can* see it; a zero would mean the new row's assertion was written against something the mutation does not move. The remedy is more or better-targeted rows, never a weaker boundary and never a recorded exception.
- **Tooling:** `uv run python scripts/prove_failability.py <manifest>` is the supported way to run it (`docs/builder/BUILD.md` `### Mechanized: scripts/prove_failability.py`). Manifest home `docs/builder/temp-tests/r2b/proofs.json` (untracked scratch, cleared per cycle); scratch root **outside the repository**. A ready manifest is given in `### Implementation steps` step 5.

### DRY analysis

**Helper inventory checked.** Refreshed **for the whole package** at plan time — `docs/shadow/helper-inventory.md`, 1791 lines, regenerated by the command in `docs/builder/worker-1.md` `### Package-wide helper inventory before helper planning` against `django_strawberry_framework/` (not just `utils/`). Grepped for the shapes this item needs: `consumer`, `attach_relation`, `attach_file`, `skip`, `assigned`. Relevant hits, all read at source: `types/base.py::_consumer_assigned_fields`, `types/base.py::_build_annotations`, `types/resolvers.py::_attach_relation_resolvers`, `types/resolvers.py::_attach_file_resolvers`. **No new package helper is proposed or needed** — this item adds no package source. `scripts/review_inspect.py tests/types/test_definition_order.py --output-dir docs/shadow` was also run (the target file is 1284 lines, well past the 150-line trigger); the emitted overview is at `docs/shadow/tests__types__test_definition_order.overview.md`.

- **Existing patterns reused.**
  - `tests/types/test_definition_order.py:46-57` — `_strawberry_field(type_cls, field_name)`, the finalized-field lookup by Python name. The new row uses it; it must not grow a second lookup helper.
  - `tests/types/test_definition_order.py:38-43` — the `_isolate_registry` autouse fixture. Automatic; the new row adds no registry teardown of its own.
  - `tests/types/test_definition_order.py:11-12` — `Category` and `Item` are already imported from `apps.products.models`. The new row adds **no import**; `strawberry` and `DjangoType`/`finalize_django_types` are already imported too.
  - `tests/types/test_definition_order.py:258-284` — the decorator row is the structural template: define `ItemType`, define `CategoryType`, assert the four definition sets, `finalize_django_types()`, assert the resolver. Follow its shape so a reader sees the two spellings side by side.
- **New helpers justified.** **None.** The only new callable is the test-local resolver function the row assigns, which exists to *be* the thing under test and has exactly one call site by construction. Extracting it would defeat the identity assertion's readability.
- **Duplication risk avoided.** Two near-copies a naive implementation would introduce, and how the plan prevents each:
  1. **A second `_strawberry_field`-shaped lookup** (e.g. reaching into `__strawberry_definition__.fields` inline). Prevented by naming the existing helper as the required accessor in `### Implementation steps`.
  2. **A `Meta.primary = True` discriminator copied from R2's lazy rows.** It looks like diligence and is a near-copy pinning nothing new here — answer 2 above records the assessment and the reason. Prevented by deciding it in the plan rather than leaving it to Worker 2, per `docs/builder/worker-1.md` `### DRY analysis shape` ("a plan that leaves a shared shape undecided guarantees that argument").

  The condition that would change answer (2): if a future item pins a contract where the *class annotation* and the *resolver's return type* name different types, a discriminating sibling registration becomes necessary. That is not spec-010's contract — cardinality/type validation of a consumer annotation is explicitly deferred (spec line 76) — so it is not this item's.

### Implementation steps

Line numbers are pin-at-write-time navigational hints. Verify against the current source before editing — this tree carries a concurrent session's uncommitted work and the file may have shifted.

1. **Re-derive the baseline.** `git status --porcelain` at the start of the pass. Every path that is not `tests/types/test_definition_order.py`, `docs/builder/bld-010-r2b-assigned_override_coverage.md`, or `docs/builder/temp-tests/r2b/` belongs to the concurrent session and is out of scope: never edit, revert, stage, or `git checkout` any of it. `tests/rest_framework/test_inputs.py` carries a failing row that belongs to that session and is already escalated — it is not this item's.

2. **Confirm the shape at `HEAD` before writing the assertion**, by executing rather than reading. A focused run of `tests/types/test_definition_order.py --no-cov` must be green first (45 rows at plan time); if it is not, stop and report rather than writing a row on top of an unknown baseline.

3. **Add one test row** to `tests/types/test_definition_order.py`, immediately after `::test_assigned_relation_field_override_keeps_consumer_resolver` (currently ending line 284) and before `::test_cross_module_lazy_relation_override_types_the_field_as_the_referenced_class` (currently line 287). Name: `test_assigned_relation_field_resolver_kwarg_override_keeps_consumer_resolver`. Shape — the type and resolver names are Worker 2's (see `### Implementation discretion items`), the structure is not:

   - define an `ItemType(DjangoType)` with `Meta.model = Item`, `fields = ("id", "name")`;
   - define a module-free resolver function **in the test body**, named distinctly (NOT `resolve_items`, NOT `items`), returning `list[ItemType]`;
   - define `CategoryType(DjangoType)` carrying the annotated assignment `items: list[ItemType] = strawberry.field(resolver=<that function>)` and `Meta.model = Category`, `fields = ("id", "name", "items")`;
   - the docstring states the contract in one line and names it as spec-010's third listed shape, distinct from the `@strawberry.field` decorator form the row above pins.

4. **Assertions, in this order.** Every one is required; the rationale for each is in answer 2.

   Before `finalize_django_types()`:
   - `definition.consumer_annotated_relation_fields == frozenset({"items"})`
   - `definition.consumer_assigned_relation_fields == frozenset({"items"})` — **the double membership is the shape's signature; both lines are required and neither substitutes for the other.**
   - `definition.consumer_authored_fields == frozenset({"items"})`
   - `definition.consumer_assigned_scalar_fields == frozenset()` — pins the relation/scalar split of the four-corner contract for this spelling.
   - the consumer's annotation survived collection unrewritten: `CategoryType.__annotations__["items"] == list[ItemType]`. A rewrite would leave a `PendingRelationAnnotation` sentinel or a concrete synthesized class here instead.
   - **no pending relation was recorded**, read as a list comprehension over `registry.iter_pending_relations()` filtered to `source_type is CategoryType`, asserting `== []`. **Read it BEFORE finalization** — R2's recorded lesson, and it holds identically here: after finalization, "never recorded" and "recorded and resolved" are indistinguishable, because the finalizer discards resolved records.

   Then `finalize_django_types()`, then:
   - `items_field = _strawberry_field(CategoryType, "items")`
   - `items_field.base_resolver is not None`
   - **`items_field.base_resolver.wrapped_func is <the resolver function>`** — the load-bearing assertion, carrying both halves (A) and (B). Identity, not a name or `__qualname__` comparison. A one-line comment beside it must say that this is the assertion the phase-2 skip is pinned by, and that the SDL below is unchanged when the skip is removed.

   Then an end-to-end schema build, exactly as the sibling rows do it: a `@strawberry.type class Query` exposing `list[CategoryType]`, `strawberry.Schema(query=Query)`, and one SDL assertion that `items: [ItemType!]!` appears. **This is corroboration that the shape finalizes end-to-end, explicitly NOT the pin** — measured identical under the mutation. Say so in a comment; do not let a later reader mistake it for the boundary assertion.

5. **Run the failability proof** with `scripts/prove_failability.py`. Write `docs/builder/temp-tests/r2b/proofs.json` (untracked scratch; create the directory) with this manifest, verified against the current source first:

   ```json
   {
     "scratch_root": "/tmp/dsf-failability-r2b",
     "proofs": [
       {
         "label": "django_strawberry_framework/types/finalizer.py::finalize_django_types #\"skip_field_names=definition.consumer_assigned_relation_fields\"",
         "target": "django_strawberry_framework/types/finalizer.py",
         "anchor": "            skip_field_names=definition.consumer_assigned_relation_fields,",
         "replacement": "            skip_field_names=frozenset(),",
         "mutation": "phase 2's consumer-assigned relation skip set emptied, so _attach_relation_resolvers attaches the generated relation resolver over every consumer-assigned relation field",
         "scope": ["tests/types/test_definition_order.py"]
       }
     ]
   }
   ```

   Run `--check-anchors-only` first and confirm the anchor matches exactly once **before** the mutating run — that check is first in the loop precisely because nothing else in it can tell that its own reference is already mutated. Then the full run with `--output`, and paste the emitted block into `### Failability proofs`. The tool leaves only the **why 0** judgement by hand, and a zero here is weakly pinned rather than harness-impossible (answer 4).

6. **Floor verification**, owned by this pass. Build the venv under a scratch path outside the repo with an explicit `--python`, per `docs/builder/BUILD.md` `### How to build the floor venv`, at the versions that section states. Run `tests/types/test_definition_order.py --no-cov` in it. Record the venv path, the resolved versions as read by `uv pip list --python <venv>/bin/python`, and pass/fail under `### Floor verification`. **Never `uv pip install` without `--python <venv>/bin/python`** — it ignores `UV_PROJECT_ENVIRONMENT` and mutates the shared `.venv`, which silently changes the floor for every later pass and every concurrent session in this tree.

7. **Format and lint, scoped to your own file only**: `uv run ruff format tests/types/test_definition_order.py` then `uv run ruff check --fix tests/types/test_definition_order.py`. Never `.` — this tree carries a concurrent session's work. Then `git status --short`; anything modified beyond this item's paths is a **stop-and-report**, never a revert.

8. **Tick `### Dispatched findings checklist`** for each sub-check that actually landed in this pass's diff, and state any deferral in the build report rather than ticking.

### Test additions / updates

- **Added:** `tests/types/test_definition_order.py::test_assigned_relation_field_resolver_kwarg_override_keeps_consumer_resolver` — pins spec-010 `### Manual annotation contract for relation fields` line 80, the `= strawberry.field(resolver=...)` assignment on a relation field. Assertion shape is fixed in `### Implementation steps` step 4; the load-bearing one is `base_resolver.wrapped_func is <consumer resolver>`.
- **Updated:** nothing. No existing row is re-pinned, weakened, or renamed. In particular `::test_assigned_relation_field_override_keeps_consumer_resolver` (the decorator form) stays exactly as it is — it will co-fail under the proof's mutation, which is corroboration that the two spellings share the phase-2 boundary, not a reason to touch it.
- **Not touched:** `tests/types/fixtures/lazy_relation_target_module.py` (R2's, closed — answer 3).
- **Baseline, measured at plan time:** `uv run pytest tests/types/test_definition_order.py --no-cov -q` -> `45 passed in 1.77s`. Worker 2 re-measures rather than quoting this.
- **Test-staleness sweep:** not owed. `docs/builder/BUILD.md` `### Test staleness a focused run cannot see` triggers on an example-model field change or a wire-shape conversion; this item changes neither, adds no example-project app or schema module, and touches no schema-module enumeration (`### Example-project schema changes must sync every schema-module list` likewise does not reach it).
- **Temp tests for Worker 3:** the productive one is a **non-distinguishing-assertion demonstration**. Worker 3 may write, under `docs/builder/temp-tests/r2b/`, a variant of the new row whose only post-finalize assertion is the SDL line, and confirm it still passes under the phase-2 mutation — which is the measured claim in answer 2 and the reason the identity assertion is the pin. That is a temp test in the sense `docs/builder/BUILD.md` `### Who performs it` licenses: demonstrating an assertion is non-distinguishing.
- **Kanban tracked-path note:** none owed. The new row lands in an **already-tracked** file, so unlike R2 there is no `apps/kanban/constants.py` regeneration question and no commit-time maintainer obligation to surface.

### Implementation discretion items

Assessed and decided to be Worker 2's. None of these is an architectural question.

- **The names** of the test-local `ItemType`, `CategoryType`, and the consumer resolver function — subject to the one hard constraint in step 3 that the resolver's name is not `resolve_items` and not `items`, so the identity assertion cannot be read as coincidental.
- **The resolver's signature** — `def custom_items(root) -> list[ItemType]` was what the plan-time probe executed and is known to work, but any signature Strawberry accepts for a `resolver=` kwarg (with or without `root`, with or without `info`) is equally valid; the row does not execute the resolver.
- **Whether the SDL corroboration assertion also checks the type's presence in the schema** (e.g. an additional `schema.get_type_by_name(...)` line) — either is fine, since neither is the pin.
- **Comment wording** throughout, subject to `AGENTS.md` rule 27 (symbol-qualified refs, never `path:NN`) and the standing ban on process provenance in source: state the invariant, never how the change came to be. No review-doc names, no `R2b`, no worker or finding numbers in the test file.

### Dispatched findings checklist

One box per sub-check Worker 2 must land. Boxes stay `- [ ]` at planning; Worker 2 ticks only a box whose contract actually landed in its diff this pass and states any deferral in the build report rather than ticking; Worker 1 audits every tick at final verification.

**F20** — quoting the finding as `docs/builder/build-010-foundation-0_0_4.md` `### R2b finding` states it: *"Spec-010 lists four override shapes as tested. R2 closed the `strawberry.lazy` one, leaving three of four covered. The fourth — an explicit `= strawberry.field(resolver=...)` assignment on a relation field, which the spec lists as distinct from the `@strawberry.field` decorator form — is still unpinned, so 'Tests cover all four shapes' remains false."* Verified against source at `django_strawberry_framework/types/base.py::_consumer_assigned_fields` and `django_strawberry_framework/types/finalizer.py::finalize_django_types #"skip_field_names=definition.consumer_assigned_relation_fields"`.

- [x] A new row exists in `tests/types/test_definition_order.py` exercising an annotated `= strawberry.field(resolver=...)` assignment on a **relation** field of a `DjangoType`, positioned adjacent to the decorator-form row.
- [x] The row asserts the double set membership: the field name is in **both** `consumer_annotated_relation_fields` and `consumer_assigned_relation_fields`, and in `consumer_authored_fields`.
- [x] The row asserts `consumer_assigned_scalar_fields == frozenset()`, pinning the relation/scalar split for this spelling.
- [x] The row asserts the consumer's class annotation survived collection unrewritten.
- [x] The row asserts no pending relation was recorded for the type, **read before `finalize_django_types()`**.
- [x] The row asserts, after finalization, that `base_resolver.wrapped_func` **is** the consumer's resolver function — by identity, not by name — pinning both that the consumer's resolver wins and that the generated resolver was not attached over it.
- [x] A real `strawberry.Schema(...)` builds from the type and the SDL carries the relation field, recorded in the test as corroboration and explicitly not as the pin.
- [x] `tests/types/fixtures/lazy_relation_target_module.py` is unmodified, and no other test file is modified.
- [ ] A failability proof for `django_strawberry_framework/types/finalizer.py::finalize_django_types #"skip_field_names=definition.consumer_assigned_relation_fields"` is recorded under `### Failability proofs` with every field `docs/builder/BUILD.md` `### What gets recorded` requires — anchor verified unique before mutating, node ids listed rather than counted, collection/setup errors `0`, pre-mutation baseline stated, revert proved by byte comparison.
- [x] Floor verification ran in an isolated scratch venv at the versions `docs/builder/BUILD.md` `## Floor verification` states, over the focused scope `tests/types/test_definition_order.py`, with the venv path, resolved versions and result recorded under `### Floor verification`. The shared `.venv` was not mutated.
- [x] `uv run ruff format` and `uv run ruff check --fix` ran **scoped to this item's own file**, and `git status --short` afterwards shows nothing beyond this item's paths.

### Notes for Worker 1 (spec reconciliation)

- **No spec edit is owed by this plan, and none may be made now.** `docs/SPECS/spec-010-foundation-0_0_4.md` line 77's "Tests cover all four shapes" becomes **true** the moment this row lands — the sentence needs no rewrite, only a landed row. Worker 1's final-verification pass confirms all four shapes now have rows and records the confirmation; it does not edit line 77.
- **Spec status-line re-verification, performed this spawn** (`docs/builder/worker-1.md` `## Spec status-line re-verification`). Spec-010's header lines carry a title, a rationale-companion pointer, and `## Purpose`; there is no status/predecessor line this item falsifies. **No edit made.**
- **Spec-009 anchors: not opened.** Spec-010 cites `docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md` twice by heading anchor (`## Strawberry finalization strategy` and `### Unresolved-target error format`). A concurrent maintainer session is reconciling spec-009. This item touches neither citation and neither spec file, so nothing was read from spec-009 and no divergence is reported. Worker 2 must not open it either.
- **For the final gate's `### Deferred work catalog`:** nothing is deferred by this item.

---

<!-- Worker 2 appends `## Build report (Worker 2)` below; Worker 3 appends `## Review (Worker 3)`; Worker 1 appends `## Final verification (Worker 1)`. -->

## Build report (Worker 2)

### Files touched

- `tests/types/test_definition_order.py` — added one row, `::test_assigned_relation_field_resolver_kwarg_override_keeps_consumer_resolver`, immediately after `::test_assigned_relation_field_override_keeps_consumer_resolver` and before `::test_cross_module_lazy_relation_override_types_the_field_as_the_referenced_class`. No other line of the file changed; no import was added (`strawberry`, `Category`, `Item`, `DjangoType`, `finalize_django_types`, `registry`, `_strawberry_field` were all already present).
- `docs/builder/bld-010-r2b-assigned_override_coverage.md` — this build report; `Status:` set to `built`; ten of eleven `### Dispatched findings checklist` boxes ticked (the failability box is deliberately left `- [ ]`, see below).
- `docs/builder/temp-tests/r2b/proofs.json` — the plan's manifest, written verbatim and anchor-verified, but **not run** (see `### Failability proofs`). Untracked scratch; gitignored, so it does not appear in `git status --short`.
- `docs/builder/worker-memory/worker-2.md` — memory entry appended. Untracked scratch.

**Baseline re-derived at the start of this pass** rather than quoted from the plan: `git status --porcelain | wc -l` -> **126** at pass start, **127** at pass end (`django_strawberry_framework/types/definition.py` appeared mid-pass). Both counts include this item's own `tests/types/test_definition_order.py` and the four `docs/builder/` untracked artifacts. Every other path is a concurrent session's; none was edited, reverted, staged, or checked out. The plan's recorded 47 has more than doubled and is still moving — re-derive, never quote.

No `examples/fakeshop/apps/kanban/constants.py` obligation is owed, confirmed rather than assumed: the row lands in `tests/types/test_definition_order.py`, which is already tracked (`git status --short` reports it ` M`, not `??`), and this pass creates no tracked file.

### Tests added or updated

- `tests/types/test_definition_order.py::test_assigned_relation_field_resolver_kwarg_override_keeps_consumer_resolver` — pins spec-010 `### Manual annotation contract for relation fields`'s third listed shape, the annotated `items: list[ItemType] = strawberry.field(resolver=category_items)` assignment on a relation field. Assertions in the plan's prescribed order: the double set membership (`consumer_annotated_relation_fields` **and** `consumer_assigned_relation_fields` both `frozenset({"items"})`) plus `consumer_authored_fields`; `consumer_assigned_scalar_fields == frozenset()`; the class annotation surviving collection unrewritten (`== list[ItemType]`); no pending relation recorded, read **before** finalization; then, after `finalize_django_types()`, the load-bearing `items_field.base_resolver.wrapped_func is category_items` by identity; then a real `strawberry.Schema(query=Query)` build with `"items: [ItemType!]!" in schema.as_str()` marked in a comment as corroboration and explicitly not the pin.
- **Updated: nothing.** `::test_assigned_relation_field_override_keeps_consumer_resolver` and `tests/types/fixtures/lazy_relation_target_module.py` are byte-unchanged; `git status --short` lists no other test file this pass touched.

### Validation run

- `uv run ruff format tests/types/test_definition_order.py` -> `1 file left unchanged` (the row was written pre-formatted). Pass.
- `uv run ruff check --fix tests/types/test_definition_order.py` -> `All checks passed!`. Pass.
- `uv run python scripts/check_trailing_commas.py --check tests/types/test_definition_order.py` -> exit 0. Pass. (`AGENTS.md` rule 17 layout is not replicated by ruff.)
- `git status --short` after both ruff invocations — the only modified path attributable to this pass is `tests/types/test_definition_order.py`. Everything else modified is the concurrent session's, enumerated in the baseline above; nothing was cleaned up or reverted.
- `uv run pytest tests/types/test_definition_order.py --no-cov -q` **before** the edit -> `45 passed in 1.70s` (the plan's step 2 gate: a known-green baseline before writing on top of it). **After** the edit -> `46 passed in 1.91s`. Single-worker confirmation at the same scope, `-n0`: `46 passed in 0.11s`. No `--cov*` flag in any invocation.

### Failability proofs

**The `BUILD.md` proof was ABORTED and is still OWED. What follows is a substitute, not the `BUILD.md` proof.** Worker 3 judges whether the substitute suffices; that judgement is not this pass's.

**Why aborted.** The proof target `django_strawberry_framework/types/finalizer.py` is dirty with a concurrent maintainer session's uncommitted work, both at pass start and re-checked immediately before the copy step:

```
$ git status --porcelain -- django_strawberry_framework/types/finalizer.py
 M django_strawberry_framework/types/finalizer.py
$ git diff --stat -- django_strawberry_framework/types/finalizer.py
 django_strawberry_framework/types/finalizer.py | 11 +++++------
 1 file changed, 5 insertions(+), 6 deletions(-)
```

The uncommitted hunk is a comment rewrite inside `::finalize_django_types` (the `loaded_attr` guard comment, repointing its cross-reference from `registry.py::_clear_if_loaded` to `utils/imports.py`). The proof loop restores by copying a pre-mutation snapshot back over the file, which silently overwrites any write that lands between the copy and the restore. `AGENTS.md` rule 34 and `docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose` both refuse that trade; no verification need justifies destroying a concurrent session's edit. The abort was the decision, not a failure of the loop.

**Read-only work that WAS completed, so the proof is ready to run the moment the file is clean:**

- Anchor uniqueness, measured as occurrences over the file text (no mutation, no copy):

  ```
  $ python3 -c 'read the file; count substrings'
  exact-anchor occurrences: 1     # "            skip_field_names=definition.consumer_assigned_relation_fields,\n"
  naive occurrences: 2            # "consumer_assigned_relation_fields" — do NOT use
  ```

  The plan's measurement reproduces exactly at `HEAD`+concurrent-dirt: the 12-space-indent, trailing-comma, trailing-newline anchor matches once; the naive token matches twice.
- The manifest is on disk unchanged from the plan at `docs/builder/temp-tests/r2b/proofs.json`, scratch root `/tmp/dsf-failability-r2b` (outside the repository). `scripts/prove_failability.py` was **not** invoked, in either `--check-anchors-only` or mutating mode, because its check step is not what the abort was about — the mutation-and-restore is.

**Substitute: the same flip demonstrated in-process, with no file on disk modified.** Phase 2's consumer-assigned relation skip was neutralized at runtime by rebinding `django_strawberry_framework.types.finalizer._attach_relation_resolvers` to a wrapper that forces `skip_field_names=frozenset()` — the exact semantic of the manifest's replacement — and restoring the original binding in the same `try/finally` or fixture teardown. Both scratch files live **outside** the repository under `/tmp/dsf-failability-r2b/`.

1. **Direct probe** (`/tmp/dsf-failability-r2b/substitute_probe.py`, `uv run python`), building the annotated-assignment shape twice:

   ```
   skip intact        wrapped_func='run.<locals>.category_items'                is_consumer=True  sdl=['items: [ItemType!]!']
   skip neutralized   wrapped_func='_make_relation_resolver.<locals>.many_resolver' is_consumer=False sdl=['items: [ItemType!]!']
   ```

   `base_resolver.wrapped_func` flips from the consumer's function to the framework's generated `many_resolver`, exactly as the plan's answer 2 measured — and the SDL line is **byte-identical across the flip**, which is the independent re-measurement of the plan's claim that a wire/SDL assertion here is non-distinguishing.

2. **Real failing node ids at the plan's focused scope.** The same neutralization was applied as an autouse fixture in a pytest plugin outside the repo (`/tmp/dsf-failability-r2b/neutralize_plugin.py`, loaded via `PYTHONPATH=/tmp/dsf-failability-r2b … -p neutralize_plugin`), so the recorded rows are measured pytest outcomes rather than an inference from the probe.

   - **Boundary:** `django_strawberry_framework/types/finalizer.py::finalize_django_types #"skip_field_names=definition.consumer_assigned_relation_fields"`.
   - **Mutation applied (in-process, not on disk):** the consumer-assigned relation skip set emptied, so `types/resolvers.py::_attach_relation_resolvers` attaches the generated relation resolver over every consumer-assigned relation field. This removes the boundary rather than perturbing code near it.
   - **Scope as run:** `PYTHONPATH=/tmp/dsf-failability-r2b uv run pytest tests/types/test_definition_order.py --no-cov -q -n0 -p neutralize_plugin`. No `-x`, no `--maxfail`, no `--cov*`.
   - **Pre-mutation state of that same scope:** green — `uv run pytest tests/types/test_definition_order.py --no-cov -q -n0` -> `46 passed in 0.11s`.
   - **Failing node ids, listed:**
     - `tests/types/test_definition_order.py::test_assigned_relation_field_override_keeps_consumer_resolver`
     - `tests/types/test_definition_order.py::test_assigned_relation_field_resolver_kwarg_override_keeps_consumer_resolver`
   - **Collection / setup errors: 0.** Run summary: `2 failed, 44 passed in 0.15s`; 46 rows collected, matching the pre-mutation collection.
   - **Revert:** no on-disk revert exists to prove, because no file on disk was mutated. The in-process rebinding is undone in the fixture's teardown and the probe's `finally`. What stands in for the byte-comparison is that `django_strawberry_framework/types/finalizer.py`'s working-tree diff is unchanged across the whole pass — `git diff --stat` reports the same `5 insertions(+), 6 deletions(-)` (the concurrent session's comment hunk) before and after, and its `git diff | md5` is stable at `91a39c748dc31b73b86f15752e9ff2d9`. No package source appears in this pass's `### Files touched`.
   - **Not a zero-row result**, so no `why 0` judgement is owed. 2 rows clears the weakly-pinned rule (0 or 1) and, as the plan predicted, sits at or below Worker 3's mandatory independent re-run floor of 3 — Worker 3 should re-run at the scope recorded above.

**What the substitute does not establish.** It exercises the same call with a different skip set, but it does not prove that the *source line* carrying the boundary is the one the tests depend on: a rebinding cannot catch a case where the recorded anchor is not the live call site. Only the on-disk mutation closes that gap. The manifest is ready; the file needs to be clean.

### Hot-path budget

Not applicable; plan declares no hot path. Affirmatively so — no package `.py` file is in this pass's diff.

### Floor verification

Owned by this pass per the plan's widened declaration. Run in an isolated scratch venv; the shared `.venv` was **not** mutated (every install carried an explicit `--python /tmp/dsf-floor-r2b/bin/python`).

- **Scratch venv path:** `/tmp/dsf-floor-r2b` (outside the repository), built per `docs/builder/BUILD.md` `### How to build the floor venv`: `uv venv /tmp/dsf-floor-r2b --python 3.10`, then `uv pip install --python /tmp/dsf-floor-r2b/bin/python -e . --group dev`, then `uv pip install --python /tmp/dsf-floor-r2b/bin/python 'django==5.2.16' 'strawberry-graphql==0.316.0'` (which downgraded the resolved `strawberry-graphql==0.324.0` to `0.316.0`).
- **Resolved versions**, as read by `uv pip list --python /tmp/dsf-floor-r2b/bin/python`: `django 5.2.16`, `strawberry-graphql 0.316.0`, `pytest 9.1.1`; interpreter `Python 3.10.19` (`/tmp/dsf-floor-r2b/bin/python -V`). These match the floor `docs/builder/BUILD.md` `## Floor verification` states.
- **Focused scope run:** `/tmp/dsf-floor-r2b/bin/python -m pytest tests/types/test_definition_order.py --no-cov` -> **`46 passed in 3.07s`. Pass.** The Strawberry precedence the plan flagged — a class annotation beside a `strawberry.field(resolver=...)` assignment supplying the GraphQL type — holds identically at 0.316.0, and `base_resolver.wrapped_func` carries the consumer's function there too.

### Implementation notes

- **Resolver signature and name.** `def category_items(root) -> list[ItemType]` inside the test body, taking the plan's known-to-work shape. The name is neither `resolve_items` nor `items`, per the plan's one hard constraint, so the identity assertion cannot be read as coincidental against the framework's `resolve_items`-named generated resolver.
- **`ItemType` is defined before the resolver function**, because the resolver's return annotation `list[ItemType]` is evaluated eagerly (the module carries no `from __future__ import annotations`), as is the class annotation `items: list[ItemType]`. Ordering is load-bearing, not stylistic.
- **`consumer_authored_fields` asserted first, then the two split sets**, mirroring the assertion order of both sibling rows above it so a reader sees the three spellings' definition states in the same shape.
- **The SDL corroboration is a bare `in schema.as_str()` check**, without the additional `schema.get_type_by_name(...)` line R2's lazy rows carry — the plan made that discretionary, and R2's version exists to prove which *class* the field resolved to, a question this shape does not raise.
- **No `Meta.primary = True` sibling**, per the plan's decided answer 2. The two candidate resolver functions are distinct by construction, so the identity assertion is non-vacuous without a discriminator; adding one would duplicate `::test_cross_module_lazy_relation_override_wins_over_the_registered_primary_type`'s pin.

### Notes for Worker 3

- **The failability proof is the one open item of this pass.** The `BUILD.md` file-mutation proof is owed and unrun; `### Failability proofs` records the dirty-file evidence that forced the abort, and the substitute in-process demonstration in its place. The checklist box for it is deliberately **not** ticked. If `django_strawberry_framework/types/finalizer.py` has been committed by the time you review, the manifest at `docs/builder/temp-tests/r2b/proofs.json` is verified-ready and `uv run python scripts/prove_failability.py docs/builder/temp-tests/r2b/proofs.json --output …` should run as written — re-check `git status --porcelain -- django_strawberry_framework/types/finalizer.py` yourself first, since the tree moves minute to minute.
- **The two scratch files that produced the substitute are outside the repo** and re-runnable as recorded: `/tmp/dsf-failability-r2b/substitute_probe.py` and `/tmp/dsf-failability-r2b/neutralize_plugin.py`.
- **The plan's productive temp test is still worth writing**: a variant of the new row whose only post-finalize assertion is the SDL line, confirmed to still pass under the neutralization. This pass measured the SDL identity directly (probe output above) but did not build that variant.
- **No shadow file was regenerated this pass.** The plan's `scripts/review_inspect.py` output for the target file is Worker 1's, at `docs/shadow/tests__types__test_definition_order.overview.md`.
- **A concurrent session's failing row exists at `tests/rest_framework/test_inputs.py`** and is already escalated to the maintainer. It is neither this item's nor evidence about this item's work; the focused scope this pass ran never touches it.

### Notes for Worker 1 (spec reconciliation)

- **No spec edit is owed by this pass, and none was made.** `docs/SPECS/` was not opened for writing at any point. Spec-010 `### Manual annotation contract for relation fields`'s "Tests cover all four shapes" is now **true**: the four shapes map to `::test_annotation_only_relation_override_keeps_generated_resolver`, R2's two `::test_cross_module_lazy_relation_override_*` rows, `::test_assigned_relation_field_override_keeps_consumer_resolver`, and this pass's `::test_assigned_relation_field_resolver_kwarg_override_keeps_consumer_resolver`. The sentence needs a landed row, not a rewrite, and the row has landed.
- **The plan's answer-1 table is confirmed by execution, not accepted on prose.** The annotated-assignment shape does put `"items"` in **both** `consumer_annotated_relation_fields` and `consumer_assigned_relation_fields`, records no pending relation, and leaves `CategoryType.__annotations__["items"] == list[ItemType]` unrewritten — all four now asserted in a permanent row rather than in a scratchpad probe. No shape-collapse finding; no re-partition needed.
- **For the final gate's `### Deferred work catalog`:** one item, and it is procedural rather than a contract deferral — **the `BUILD.md` file-mutation failability proof for `types/finalizer.py::finalize_django_types #"skip_field_names=definition.consumer_assigned_relation_fields"` remains owed**, aborted because the target file carries a concurrent session's uncommitted work. The manifest is on disk and anchor-verified; the run needs a clean target file. Nothing about the spec's contract is deferred.
- **Spec-009 was not opened**, in either direction, per the plan's standing constraint.

---

## Review (Worker 3)

### Baseline re-derived, not accepted

`git status --porcelain | wc -l` -> **128** at review start (the dispatch's figure, re-measured rather than quoted; the plan's 47 and the build report's 126/127 are both stale). R2b's contribution to that baseline is **one path**, `tests/types/test_definition_order.py`, and inside it **one added row** — the working-tree diff of that file is 216 added lines, of which R2's three accepted rows and its module-level `_LAZY_TARGET_MODULE` / import additions are the remainder. The R2b block is lines 287-353 (67 lines including the trailing separators, 40 non-blank non-comment). `tests/types/fixtures/lazy_relation_target_module.py` is `??` — R2's, untracked, and outside this item.

Everything else dirty is the concurrent maintainer session's: 23 other `tests/` files, `examples/fakeshop/test_query/test_transport_api.py`, `django_strawberry_framework/schema.py`, `docs/review/rev-*.md`, and the rest. None was read as evidence about R2b, none edited, none reverted, none staged.

### High:

None.

### Medium:

None.

### Low:

#### The floor-verification widening's *second* stated ground is not exercised by the landed row

`### Floor verification: scoped, and the owning pass named` justifies pulling R2b into floor scope on two grounds. The first — "the row ends in a real `strawberry.Schema(query=Query)` build", i.e. `docs/builder/BUILD.md` `### When it is required`'s "schema and type construction against Strawberry internals" — holds on its face and is sufficient on its own. The second is narrower and, as the row actually landed, non-discriminating:

> when a `StrawberryField` built by `strawberry.field(resolver=fn)` is assigned to a name that *also* carries a class annotation, the annotation supplies the GraphQL type and the resolver's return type does not

In the landed row the class annotation is `list[ItemType]` and `category_items`'s return annotation is *also* `list[ItemType]` (`tests/types/test_definition_order.py:300` and `:305`). The two candidates name the same type, so the SDL is identical under either precedence and the row cannot tell which one Strawberry applied — the same vacuity axis R2's first-draft assertion had, transposed onto the type rather than the resolver. Discriminating it would need the two annotations to name *different* types, which is the condition `### DRY analysis` itself names as belonging to a future item ("if a future item pins a contract where the *class annotation* and the *resolver's return type* name different types").

**Recorded rejection — no change requested, and no re-loop.** The floor scope stands entirely on ground one; the floor run was performed and reproduces (below). Making the row discriminate the precedence would pin an *upstream* rule spec-010 does not contract for, and spec-010 explicitly defers annotation/cardinality validation (`### Manual annotation contract for relation fields`, the "Validation ... is **deferred**" bullet). The finding is recorded so a later reader does not mistake the floor run for evidence about that precedence, and it is repeated under `### Notes for Worker 1 (spec reconciliation)` as informational only.

### The central judgement: Worker 2 aborted the `BUILD.md` proof and supplied a substitute

**Verdict: the substitute is accepted, the on-disk proof is carried forward as an explicit obligation, and the checklist box stays `- [ ]`.** The reasoning, and every fact re-derived rather than accepted:

**1. The abort condition still holds, so the same rule binds me.**

```
$ git status --porcelain -- django_strawberry_framework/types/finalizer.py
 M django_strawberry_framework/types/finalizer.py
$ git diff --stat -- django_strawberry_framework/types/finalizer.py
 django_strawberry_framework/types/finalizer.py | 11 +++++------
 1 file changed, 5 insertions(+), 6 deletions(-)
$ git diff -- django_strawberry_framework/types/finalizer.py | md5
91a39c748dc31b73b86f15752e9ff2d9
```

Still dirty at review time. The hunk is exactly what the build report describes — a comment rewrite inside `::finalize_django_types` at the `loaded_attr` guard, repointing its cross-reference from `registry.py::_clear_if_loaded` to `utils/imports.py`; no executable line changes. The md5 is **identical to the one Worker 2 recorded**, which establishes two things at once: no mutation was left behind by Worker 2's pass, and the concurrent session has not written to the file since. My source carve-out does not reach another session's uncommitted work, so I did not run the on-disk loop either. `docs/builder/worker-3.md` "Scope" plus `AGENTS.md` rule 34 are the authority; the restore step of `docs/builder/BUILD.md`'s fenced loop is a blind `cp` back over the file and would silently discard whatever landed in the window.

**2. The anchor is still unique, so the aborted proof remains runnable as written.** Measured as occurrences over the file text, not matching lines:

```
$ python3 -c "s=open('django_strawberry_framework/types/finalizer.py').read(); ..."
exact anchor occurrences: 1     # "            skip_field_names=definition.consumer_assigned_relation_fields,\n"
naive occurrences: 2            # "consumer_assigned_relation_fields"
```

**3. I re-ran the boundary independently, and the node-id set is identical.** The recorded count is 2, at or below `docs/builder/worker-3.md`'s mandatory re-run floor of 3, so this boundary is in the mandatory subset. I did **not** reuse Worker 2's `/tmp/dsf-failability-r2b/` scratch files — I wrote my own plugin at `/tmp/dsf-w3-r2b/w3_neutralize.py` (outside the repository), which rebinds `django_strawberry_framework.types.finalizer._attach_relation_resolvers` to a wrapper forcing `skip_field_names=frozenset()` and restores the original binding in fixture teardown.

- **Pre-mutation state of that same scope:** `uv run pytest tests/types/test_definition_order.py --no-cov -q -n0` -> `46 passed in 0.28s`. Green.
- **Scope as run (Worker 2's recorded scope):** `PYTHONPATH=/tmp/dsf-w3-r2b uv run pytest tests/types/test_definition_order.py --no-cov -q -n0 -p w3_neutralize`.
- **Failing node ids, listed:**
  - `tests/types/test_definition_order.py::test_assigned_relation_field_override_keeps_consumer_resolver`
  - `tests/types/test_definition_order.py::test_assigned_relation_field_resolver_kwarg_override_keeps_consumer_resolver`
- **Collection / setup errors: 0.** Run summary `2 failed, 44 passed in 0.14s`; 46 collected, matching the pre-mutation collection exactly.
- **Set comparison, not count comparison:** my set and Worker 2's are the **same two node ids**. The new R2b row fails on `assert items_field.base_resolver.wrapped_func is category_items`, with the actual value `_make_relation_resolver.<locals>.many_resolver` — the flip the plan predicted, observed as a real pytest outcome.
- **Revert:** nothing on disk was mutated, so there is no snapshot to `cmp`. The property byte-comparison exists to guarantee — that the tree carries no live mutation — is discharged by the md5 in (1) being unchanged from Worker 2's record through the end of my pass, and by `git status --porcelain` listing no package source attributable to either pass.

**4. I closed the gap Worker 2 itself named.** The build report's `### What the substitute does not establish` says a rebinding "does not prove that the *source line* carrying the boundary is the one the tests depend on". That gap is now measured shut, read-only:

- `grep -rn "_attach_relation_resolvers" django_strawberry_framework/` returns **exactly one call site**, `django_strawberry_framework/types/finalizer.py:793`, whose `skip_field_names=` kwarg is the anchor line at `:796`. Every other hit is an import, a docstring, or a comment. So there is no second call site a rebinding could be conflating with the anchor.
- My wrapper additionally **records the value the live call site passes**. At the R2b row it observed `[('CategoryType', frozenset({'items'}))]` — i.e. the live call really is fed by `definition.consumer_assigned_relation_fields`, populated, from the anchor line. A rebinding that both intercepts the sole call site and observes the anchor's own expression arriving at it is not distinguishable in effect from replacing that line with `skip_field_names=frozenset(),`.

**What the substitute does and does not establish, stated precisely.** It establishes that the boundary is pinned by two rows, that neither is vacuous, and that the anchor line is the live argument source. It does **not** establish the one thing only an on-disk edit can: that `scripts/prove_failability.py`'s own machinery — anchor match, `cp`/`cmp` round trip, `ACTIVE-MUTATION.json` marker — runs clean against this manifest. That residue is procedural, not a gap in the evidence about the code.

**Why not `revision-needed`.** `docs/builder/BUILD.md` `### Who performs it` makes a "missing, unconvincing, or unreverted proof" `revision-needed`. This proof is none of the three: it is recorded with every field `### What gets recorded` requires; it is convincing, having reproduced to an identical node-id set under an independently written mutation plus the call-site closure above; and there is nothing unreverted because nothing on disk was mutated. Beyond that, `revision-needed` would loop Worker 2 against a blocker only the maintainer can clear — the target file's cleanliness is not in any worker's gift, and a verdict that cannot be acted on is not a verdict.

**The checklist box should stay `- [ ]`.** The box's contract is the `BUILD.md` file-mutation proof, and that did not land. Ticking it would be the "tick with no matching fix" failure `docs/builder/BUILD.md` `### Dispatched findings checklist` names. Worker 1 records the one-line deferral reason at final verification under `### Spec changes made (Worker 1 only)`, per `docs/builder/ARTIFACT.md` `## Final verification (Worker 1)`, and carries the obligation into `bld-010-final.md`'s `### Deferred work catalog` where the build report already routed it.

**Boundaries re-run vs accepted on Worker 2's record.** Re-run: `django_strawberry_framework/types/finalizer.py::finalize_django_types #"skip_field_names=definition.consumer_assigned_relation_fields"` — the only boundary in this item's proof set. Accepted on Worker 2's record: none. R2b introduces no new boundary of its own (`### Boundary count and the split question`, confirmed — the diff contains no package source at all).

### The assertion is distinguishing, and the row cannot pass vacuously

Three independent checks, each measured:

1. **The identity assertion flips under the mutation.** Shown in (3) above: `wrapped_func` becomes `_make_relation_resolver.<locals>.many_resolver`. Not an inference.
2. **The SDL corroboration does not flip, so it would have been worthless as the pin.** Demonstrated with a temp test rather than argued — `docs/builder/temp-tests/r2b/test_sdl_assertion_is_non_distinguishing.py`, two rows over the same shape. Boundary intact: `2 passed`. Boundary neutralized: `1 failed, 1 passed`, the SDL-only row passing and the identity row failing. This is the plan's `### Test additions / updates` "productive temp test", which Worker 2 flagged as unbuilt; it is now built and the plan's claim reproduces.
3. **Identity cannot be satisfied coincidentally.** `is` on a function object defined in the test body, named `category_items` — neither `items` nor the framework's `resolve_items`. The two candidate objects are distinct by construction and measured distinct.

**Skipping the competing `Meta.primary = True` registration was right.** The plan's stated reason — R2's assertion is *which class*, R2b's is *which function*, and the two functions are distinct by construction — holds, and check (1) is the proof that it holds: the mutation moves the assertion without any discriminator present. Adding a primary sibling would duplicate `::test_cross_module_lazy_relation_override_wins_over_the_registered_primary_type`'s pin while pinning nothing new. Not re-raised.

### The double-membership claim: verified, and it is what makes the row distinct

The claim is that the spec spells the assignment form as an **annotated** assignment, so the field name lands in **both** `consumer_annotated_relation_fields` and `consumer_assigned_relation_fields`, and that nothing pre-existing pins that state.

- **Spec side.** `docs/SPECS/spec-010-foundation-0_0_4.md` `### Manual annotation contract for relation fields`, the "Field / resolver override" bullet, spells it `items: list["ItemType"] = strawberry.field(resolver=custom_items)` — annotated. The four-shape list's third entry ("explicit `strawberry.field(resolver=...)` assignment on a relation field") is the shape this row closes. Confirmed by reading the spec, not the plan's quotation of it.
- **Runtime side.** Asserted in the landed row and green: `consumer_annotated_relation_fields == frozenset({"items"})` **and** `consumer_assigned_relation_fields == frozenset({"items"})`.
- **Nothing pre-existing pins it.** `grep -rn "consumer_annotated_relation_fields\|consumer_assigned_relation_fields" tests/` returns eight assertion sites outside the new row; in every one of them exactly one of the two sets is non-empty. The two other relation-assignment rows in the tree are both *un*annotated by construction — `tests/types/test_base.py::test_relation_shapes_on_consumer_assigned_relation_raises` passes the field via `namespace_extra` with no annotation, and `tests/optimizer/test_walker.py::_shelf_types_with_consumer_books` sets `"__annotations__": {}` explicitly. Read at source, not inferred from the grep.
- **Why it matters rather than being trivia.** `types/finalizer.py::finalize_django_types` hands the narrow set to `_attach_relation_resolvers` and the broad `consumer_authored_fields` union to `_attach_file_resolvers` (`finalizer.py:796` and `:810`). The rationale's F11 entry says the two skip sets "look like a typo and are not". Double membership is the only relation-field configuration in which the narrow set is populated *and* the name is in the union, so this row is the first thing in the suite that exercises that state. Genuine fourth case, not a near-copy.

### DRY findings

- **No duplication introduced.** The row reuses `tests/types/test_definition_order.py::_strawberry_field` for the finalized-field lookup rather than reaching into `__strawberry_definition__.fields` inline, reuses the `_isolate_registry` autouse fixture, and adds **no import** — the diff's only import additions (`importlib`, `Annotated`, `get_args`, `StrawberryLazyReference`) and the `_LAZY_TARGET_MODULE` constant all belong to R2, which is `final-accepted`.
- **No new abstraction, so no existence challenge is owed.** The only new callable is `category_items`, which exists to *be* the object under test and has one call site by construction; extracting it would destroy the identity assertion. `docs/builder/worker-3.md` "The existence challenge" says raise it on grounds, not on a schedule, and there are none here.
- **Repeated-literal evidence, mechanical.** `uv run python scripts/review_inspect.py tests/types/test_definition_order.py --output-dir docs/shadow` re-run at review time (Worker 1's copy predates both R2 and R2b). Its **Repeated string literals** section carries no literal introduced by R2b: `items: [ItemType!]!` appears once and is absent from the 2x+ list. The 3x `tests.types.fixtures.lazy_relation_target_module` is R2's, and R2's own module-level comment records the deliberate reason the literal stays inline in the `strawberry.lazy("...")` calls. Nothing to consolidate.
- **Structural near-copy assessed and cleared.** The row mirrors `::test_assigned_relation_field_override_keeps_consumer_resolver`'s shape deliberately (define `ItemType`, define `CategoryType`, assert the definition sets, finalize, assert the resolver), which is the plan's stated intent so a reader sees the two spellings side by side. The assertions differ where the shapes differ — the double membership, the surviving `__annotations__` entry, identity instead of `__qualname__.endswith`.

### Checklist walk

All eleven `### Dispatched findings checklist` boxes walked against the diff.

| box | tick | verified |
|---|---|---|
| new row, annotated `= strawberry.field(resolver=...)` on a relation field, adjacent to the decorator row | `- [x]` | correct — `tests/types/test_definition_order.py:287`, immediately after the decorator row ending `:284` |
| double set membership + `consumer_authored_fields` | `- [x]` | correct — `:312`, `:315`, `:316` |
| `consumer_assigned_scalar_fields == frozenset()` | `- [x]` | correct — `:317` |
| class annotation survived collection unrewritten | `- [x]` | correct — `assert CategoryType.__annotations__["items"] == list[ItemType]` |
| no pending relation, read **before** finalization | `- [x]` | correct — the `iter_pending_relations()` comprehension precedes `finalize_django_types()`; ordering re-checked in the source, not taken from the report |
| `base_resolver.wrapped_func` **is** the consumer's function | `- [x]` | correct — `:342`, `is`, and proven load-bearing by the re-run |
| real `strawberry.Schema(...)` + SDL, recorded as corroboration not pin | `- [x]` | correct — and the accompanying comment says so explicitly, which the temp test confirms is the honest characterization |
| fixture module unmodified, no other test file modified | `- [x]` | correct with one stated limit — the fixture module is untracked (`??`), so "byte-unchanged" is not mechanically checkable against HEAD for it; R2's three rows all still pass at this scope, which is the available corroboration. No other test file in `git status` is attributable to this pass |
| failability proof recorded with every `### What gets recorded` field | `- [ ]` | **correctly left open.** Deferral recorded in `### Failability proofs` and routed to the final gate's catalog. Judged above; the box stays open |
| floor verification in an isolated venv, shared `.venv` unmutated | `- [x]` | correct, and reproduced — below |
| ruff scoped to own file, `git status --short` clean of anything else | `- [x]` | correct — re-verified read-only below |

No box is ticked without a matching fix; the one open box carries a recorded deferral. No Medium finding arises from the walk.

### Floor verification: reproduced, and the shared `.venv` is intact

Re-run rather than read. Worker 2's scratch venv is still on disk at `/tmp/dsf-floor-r2b` (outside the repository):

```
$ /tmp/dsf-floor-r2b/bin/python -V                     -> Python 3.10.19
$ uv pip list --python /tmp/dsf-floor-r2b/bin/python   -> django 5.2.16, strawberry-graphql 0.316.0, pytest 9.1.1
$ /tmp/dsf-floor-r2b/bin/python -m pytest tests/types/test_definition_order.py --no-cov
                                                       -> 46 passed in 1.47s
```

These match `docs/builder/BUILD.md` `## Floor verification`'s canonical floor — Django **5.2.16**, Python **3.10**, strawberry-graphql **0.316.0** — read from that section, not from memory. The record is reproducible exactly as written.

**Shared `.venv` not mutated**, verified by reading rather than by trusting the `--python` flags: `uv pip list` on the shared environment reports `django 6.1` and `strawberry-graphql 0.323.2` — i.e. still the newest-supported set, not the floor. Had a floor install leaked into `.venv`, those two numbers would read 5.2.16 / 0.316.0.

### Validation re-run, read-only

- `uv run ruff format --check tests/types/test_definition_order.py` -> `1 file already formatted`.
- `uv run ruff check tests/types/test_definition_order.py` -> `All checks passed!`.
- `uv run python scripts/check_trailing_commas.py --check tests/types/test_definition_order.py` -> exit 0 (`AGENTS.md` rule 17 layout; ruff does not replicate it).
- ASCII-only over the R2b block, measured by codepoint rather than eyeballed: no line in `287-353` carries a codepoint above 127.
- `uv run pytest tests/types/test_definition_order.py --no-cov -q -n0` -> `46 passed`. No `--cov*` flag in any invocation this pass.
- Source-reference discipline: the row's comments cite `types/finalizer.py::finalize_django_types` and `types/resolvers.py::_attach_relation_resolvers` symbol-qualified (`AGENTS.md` rule 27), and carry no process provenance — no worker or finding numbers, no review-doc names, no `R2b`. The docstring's "Spec-010's third listed manual-annotation shape" is a spec pointer, which is on the permitted side of that line.

### Test-staleness sweep, run independently

Run against the tree rather than against the artifact's enumerated file list, per `docs/builder/worker-3.md` "Test staleness". Neither trigger in `docs/builder/BUILD.md` `### Test staleness a focused run cannot see` fires: no example-model field was added, removed, or renamed (no `apps/*/models.py` is in R2b's diff), and no wire-shape conversion occurred (no field became a connection; the `edges`/`node`/argument envelope is untouched). `### Example-project schema changes must sync every schema-module list` likewise does not reach — R2b adds no example app and no schema module, so no private schema-module enumeration needs syncing. Nothing owed.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` -> empty. `__all__` and the re-export list are unchanged. R2b's diff contains no package source at all.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. (`docs/SPECS/` was not opened for writing, confirmed by its absence from `git status --porcelain`; `docs/builder/bld-010-r2b-*.md` is this cycle's own artifact.)

### Static helper use

`scripts/review_inspect.py` **was run**, not skipped. `docs/builder/BUILD.md` `### When to run the helper during build` triggers on the third Worker 3 condition — 50+ lines of new logic to a file outside `django_strawberry_framework/` — since the R2b block is 67 lines. The first two conditions do not fire (no new `.py` file; nothing under package `optimizer/` or `types/`). Invocation: `uv run python scripts/review_inspect.py tests/types/test_definition_order.py --output-dir docs/shadow`, emitting `docs/shadow/tests__types__test_definition_order.overview.md` and `.stripped.py`. Findings drawn from it are in `### DRY findings`; no shadow line numbers are cited anywhere in this review.

### What looks solid

- **The abort was the right call and was reported loudly rather than papered over.** The build report leads with "The `BUILD.md` proof was ABORTED and is still OWED", leaves the box unticked, and routes the residue to the final gate's catalog. That is the shape a blocked obligation should have — the failure mode worth fearing is a proof written from memory and a box ticked anyway.
- **The substitute produced measurements, not an argument.** Real pytest node ids at the recorded scope with 0 collection errors, plus a directly observed SDL byte-identity across the flip. It reproduced under an independently written mutation.
- **The pin was chosen against the vacuity trap rather than for observability.** The plan measured that the SDL is identical either way *before* choosing the assertion, and the landed row says so in a comment beside the assertion so the next reader cannot mistake the corroboration for the pin.
- **Read-only work was completed up to the blocked step.** Anchor uniqueness measured as occurrences, manifest on disk and verified — so the moment the target file is clean, the proof runs without re-derivation.
- **The row's ordering constraints are load-bearing and recorded as such** (`### Implementation notes`): `ItemType` before the resolver because the return annotation evaluates eagerly, and the pending-relation read before finalization because the finalizer discards resolved records. Both were re-checked in the source.

### Temp test verification

- `docs/builder/temp-tests/r2b/test_sdl_assertion_is_non_distinguishing.py` — two self-contained rows over the annotated-assignment shape, one asserting only the SDL line, one asserting resolver identity. Boundary intact: `2 passed`. Boundary neutralized via `/tmp/dsf-w3-r2b/w3_neutralize.py`: `1 failed, 1 passed`, the SDL row passing.
- **Disposition: deleted at cycle end, not promoted.** It catches no bug — it demonstrates that an assertion the row deliberately did *not* rely on is non-distinguishing, which is exactly the use `docs/builder/BUILD.md` `### Who performs it` licenses ("Worker 3 may still write a temp test ... to demonstrate that an existing assertion is non-distinguishing"). Promoting it would ship a permanently-passing row that pins nothing, which `### Harness-impossible interleavings` calls out as manufacturing confidence. The permanent row already carries the finding as a comment.
- `/tmp/dsf-w3-r2b/w3_neutralize.py` — my re-run plugin, outside the repository, re-runnable as recorded. Not Worker 2's file; written independently so the re-run is not a replay.

### Notes for Worker 1 (spec reconciliation)

- **Escalated: the `BUILD.md` file-mutation failability proof for `django_strawberry_framework/types/finalizer.py::finalize_django_types #"skip_field_names=definition.consumer_assigned_relation_fields"` is still owed, and no worker can clear it.** The target file carries a concurrent maintainer session's uncommitted comment-only hunk, unchanged in content since Worker 2's pass (md5 `91a39c748dc31b73b86f15752e9ff2d9`). Resolution paths, for Worker 1 to pick between: **(a)** accept the substitute as discharging the evidentiary obligation — my recommendation, on the grounds recorded above, and carry the on-disk run into `bld-010-final.md`'s `### Deferred work catalog` as a maintainer item to run once the file is committed or reverted; **(b)** hold the item and re-run `uv run python scripts/prove_failability.py docs/builder/temp-tests/r2b/proofs.json --output …` at final verification **if and only if** `git status --porcelain -- django_strawberry_framework/types/finalizer.py` is empty by then — the manifest is anchor-verified and needs no edit; **(c)** escalate to the maintainer for a commit of the concurrent hunk. Whichever path is taken, the checklist box needs its one-line deferral reason under `### Spec changes made (Worker 1 only)` rather than a tick.
- **Informational, no action requested: the floor-verification widening's second ground is not exercised.** See the Low above. The widening itself is correct on its first ground and the floor run passed at 0.316.0; the note exists so the run is not later cited as evidence about Strawberry's annotation-vs-resolver-return-type precedence, which the landed row cannot discriminate because both name `list[ItemType]`.
- **"Tests cover all four shapes" is now true, confirmed independently of the build report.** Reading the file rather than the report, the four rows are `::test_annotation_only_relation_override_keeps_generated_resolver`, `::test_cross_module_lazy_relation_override_types_the_field_as_the_referenced_class` (with `::…_wins_over_the_registered_primary_type` as its discriminator), `::test_assigned_relation_field_override_keeps_consumer_resolver`, and `::test_assigned_relation_field_resolver_kwarg_override_keeps_consumer_resolver`. Spec-010 `### Manual annotation contract for relation fields` needs no edit — the sentence needed a landed row, and the row landed.
- **No rejected alternative re-raised.** `docs/SPECS/appx/spec-010-foundation-0_0_4-rationale.md` was read: F5 (the four-corner matrix), F6 (the positive `StrawberryField` detection rule), F11 (the two different phase-2 skip sets), and F16 (the lazy marker's inner spelling). Nothing in the implementation contradicts them, and F11 in particular is *corroborated* — R2b's row is the first thing in the suite exercising the state where the narrow and broad skip sets genuinely diverge for a relation field.
- **Spec-009 was not opened**, in either direction, matching the plan's and the build report's standing constraint.

### Review outcome

`review-accepted`.

Every High/Medium tier is empty. The one Low carries a recorded rejection with its reason. The single open checklist box carries a recorded deferral, is correctly left unticked, and is escalated above with resolution paths rather than silently dropped. The boundary in the mandatory re-run subset was re-run independently to an identical node-id set, and the gap the builder itself named was closed by measurement during this pass.

---

## Final verification (Worker 1)

Every number below is command-produced with the command beside it, counted as **occurrences** where occurrences and matching lines differ, and re-derived rather than inherited from the build report or the review (`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`).

**Baseline re-derived, not quoted.** `git status --porcelain | wc -l` -> **141** at final-verification start (plan 47, build report 126/127, review 128 — all stale, as expected in this tree). R2b's contribution remains one tracked path.

### 1. The unticked failability box — disposition decided

**Decision: the box stays `- [ ]`, this item is `final-accepted`, and the on-disk proof is carried forward as a named maintainer obligation.** Not `revision-needed`, and not a tick.

Three findings drive it, each measured this pass.

**(a) `docs/builder/BUILD.md`'s mandatory proof obligation does not attach to this item at all.** `### What needs a proof, and what does not` scopes it to "every **new** boundary, guard, gate, or rejection path a slice introduces". R2b introduces none: `git diff --stat -- tests/types/test_definition_order.py` -> `216 insertions(+)`, and `git diff -- tests/types/test_definition_order.py | grep -c '^-[^-]'` -> **0**; no package source is in this item's diff (`git diff -- django_strawberry_framework/__init__.py` empty; `types/base.py` clean). The proof here is against an **existing** boundary and was elected by the plan as extra diligence. So `### Failability and fail-open checks`'s "confirm the record EXISTS" is satisfied vacuously — there is no new boundary whose record could be missing — and the open box is a plan-elected obligation, not a waived gate. That distinction is what makes a deferral honest rather than a hole.

**(b) The blocker still holds and is not in any worker's gift.** `git status --porcelain -- django_strawberry_framework/types/finalizer.py` -> ` M`; `git diff -- django_strawberry_framework/types/finalizer.py | md5` -> `91a39c748dc31b73b86f15752e9ff2d9`, **identical to the md5 both Worker 2 and Worker 3 recorded**, so the concurrent session has not written to the file across three passes and neither pass left a mutation behind. Reading the hunk: five comment lines rewritten inside `::finalize_django_types` at the `loaded_attr` guard, repointing a cross-reference to `utils/imports.py`; **no executable line changes**, and it does not touch the anchor. `revision-needed` would dispatch Worker 2 against a condition only the maintainer can clear by committing or reverting their own work — a verdict that cannot be acted on is not a verdict.

**(c) The substitute's one named gap is closed, re-derived here rather than inherited.** Worker 2 named it: a rebinding cannot prove the recorded anchor is the live call site. Measured myself over the package, as occurrences:

```
$ python: count "_attach_relation_resolvers" per file under django_strawberry_framework/
types/finalizer.py: 3   types/resolvers.py: 3   types/__init__.py: 1   types/base.py: 1   (total 8)
$ grep -n "_attach_relation_resolvers" django_strawberry_framework/types/finalizer.py
17:  (module docstring)   80:  (import)   793:  (the call)
```

Reading each of the other seven: `resolvers.py:425` is the definition, `resolvers.py:17` and `:483` and `types/__init__.py:8` and `base.py:1580` are docstring/comment prose. **Exactly one call site exists**, `finalizer.py:793`, and the anchor line is its own `skip_field_names=` argument (`sed -n '790,800p'` read directly). Anchor uniqueness re-measured on the current file text: exact 12-space anchor -> **1** occurrence; naive token -> **2**. A rebinding that intercepts the sole call site, and observes the anchor's own expression arriving there populated, is indistinguishable in effect from editing that line.

**The obligation does not evaporate.** It is carried, named, to two places: `bld-010-final.md`'s `### Deferred work catalog` (where the build report and review both already routed it), and the maintainer, as the only party who can clear it. Stated once, precisely, so it is actionable without re-deriving this artifact:

> **Owed, maintainer-gated:** run `uv run python scripts/prove_failability.py docs/builder/temp-tests/r2b/proofs.json --output <path>` once `git status --porcelain -- django_strawberry_framework/types/finalizer.py` is empty. The manifest is on disk, anchor-verified, and needs no edit. Expected result, from three independent in-process measurements: 2 failing rows — `::test_assigned_relation_field_override_keeps_consumer_resolver` and `::test_assigned_relation_field_resolver_kwarg_override_keeps_consumer_resolver` — with 0 collection errors. A different node-id set is a finding.

Worker 3's path (a) is the one taken; (b) was tested against the tree this pass and its precondition is still false; (c) is what the carried obligation above performs.

### 2. The spec sentence this sub-item existed to make true

**Confirmed true. No spec edit made, and none is owed.** `docs/SPECS/spec-010-foundation-0_0_4.md` `### Manual annotation contract for relation fields` lists four shapes; each now has exactly one pinning row, and the four names map one-to-one with none doubled up. Verified by reading the rows themselves (`sed -n '231,353p'` and `'354,372p'`), not the reports:

| spec-listed shape | pinning row | how the row spells it |
|---|---|---|
| annotation-only (`items: list["ItemType"]`) | `::test_annotation_only_relation_override_keeps_generated_resolver` (`:231`) | bare `items: list[ItemType]`; asserts the **generated** resolver still attaches |
| `list[Annotated["ItemType", strawberry.lazy(...)]]` cross-module | `::test_cross_module_lazy_relation_override_types_the_field_as_the_referenced_class` (`:354`) | inner-spelled marker via the fixture module |
| explicit `strawberry.field(resolver=...)` assignment | `::test_assigned_relation_field_resolver_kwarg_override_keeps_consumer_resolver` (`:287`) | `items: list[ItemType] = strawberry.field(resolver=category_items)` |
| `@strawberry.field` decorator | `::test_assigned_relation_field_override_keeps_consumer_resolver` (`:258`) | `@strawberry.field def items(self) -> list[ItemType]` |

No doubling: the four rows use four structurally different spellings and four different post-finalize assertions (`__name__ == "resolve_items"`, the lazy row's type identity, `wrapped_func is category_items`, `__qualname__.endswith("CategoryType.items")`). `::test_cross_module_lazy_relation_override_wins_over_the_registered_primary_type` (`:428`) is the lazy row's **discriminator**, not a fifth shape — counting it as one would be the doubling this check exists to catch. `grep -c` on the new row's name across `tests/` -> **1**.

One cosmetic residue, recorded and deliberately not acted on: the lazy row's docstring calls itself "The fourth shape" while the spec lists it second and the R2b row's docstring correctly says "third listed". The row is R2's, `final-accepted` and closed, the ordinal is prose in a docstring rather than a contract, and re-opening a closed item to renumber a docstring is not worth a re-loop. Noted for `bld-010-final.md` as a Low-tier cosmetic only.

### 3. Audit of the other ten ticks — against the diff, not against the review

Walked each box against `git diff -- tests/types/test_definition_order.py` and the source. **No over-tick found; no box needed un-ticking; no landed box was left open.**

| box | verdict |
|---|---|
| new row, annotated `= strawberry.field(resolver=...)`, adjacent to the decorator row | correct — `:287`, directly after the decorator row's last line `:284` |
| double membership + `consumer_authored_fields` | correct — all three asserts present, `consumer_annotated_relation_fields` **and** `consumer_assigned_relation_fields` each `frozenset({"items"})` |
| `consumer_assigned_scalar_fields == frozenset()` | correct — present |
| class annotation survived unrewritten | correct — `assert CategoryType.__annotations__["items"] == list[ItemType]` |
| no pending relation, read **before** finalization | correct — the `iter_pending_relations()` comprehension is textually above `finalize_django_types()`; ordering read in the source |
| `wrapped_func` **is** the consumer's function | correct — `is`, against `category_items`, a name that is neither `items` nor the framework's `resolve_items` |
| real `Schema` + SDL, corroboration not pin | correct — and the comment beside the identity assert says the SDL is byte-identical either way, so a later reader cannot mistake it |
| fixture module unmodified, no other test file modified | correct, with the review's stated limit accepted. The fixture module is `??` (untracked, R2's) so no HEAD comparison exists; independently, the one other tree file containing `category_items` — `tests/optimizer/test_extension.py` — is **clean** (`git status --porcelain` empty for it) and carries that name at HEAD already (`git show HEAD:… \| grep -c` -> 1 = working copy's 1), so it is a pre-existing coincidence and not this pass's writing |
| floor verification in an isolated venv, shared `.venv` unmutated | correct — reproduced in item 5 below |
| ruff scoped, `git status --short` clean of anything else | correct — re-verified read-only in item 5 |

### 4. Worker 3's Low finding — the rejection is judged and upheld

**I agree with the rejection; the finding is factually right and the remedy is correctly refused.** Verified at source rather than accepted: the row's class annotation is `items: list[ItemType]` and `def category_items(root) -> list[ItemType]` — the two candidates name the same type, so the schema is identical under either precedence and the row genuinely cannot discriminate which one Strawberry applied.

Three grounds for upholding. The floor widening stands entirely on its first ground (the row ends in a real `strawberry.Schema(query=Query)` build — `### When it is required`'s "schema and type construction against Strawberry internals" on its face), so nothing depends on the second. Discriminating the second would require the class annotation and the resolver return type to name **different** types, which is precisely the validation spec-010 defers ("trust the user's annotation; do not silently overwrite") — pinning it here would contract for a rule the spec declines to hold. And it would pin an **upstream** precedence, buying a suite failure on a future Strawberry release for no contract gain.

**Making sure the floor run is not later citable as evidence about that precedence** is the actionable half, and prose in a closing artifact is not enough on its own. Discharged in two durable places: a `*Consequence to carry*` sentence in the new rationale entry (item 6), which is the tracked, spec-keyed record a later reader reaches; and an instruction that `bld-010-final.md`'s floor-verification confirmation for R2b record the scope as **schema-and-type-construction only**, naming the precedence as explicitly out of what the run evidences. No test change, no spec change — Worker 3 was right that it is neither.

### 5. Mechanical confirmations

- **No proof or re-run residue on the two package files.** `django_strawberry_framework/types/base.py` -> `git status --porcelain` **empty** (clean; untouched by any pass). `django_strawberry_framework/types/finalizer.py` -> dirty with **exactly** the concurrent session's five-comment-line rewrite, read hunk by hunk: no executable line changed, the anchor line is untouched, and the diff md5 is unchanged across Worker 2's, Worker 3's, and this pass. Attribution to the concurrent session is therefore established by content, not by absence of evidence.
- **No `ACTIVE-MUTATION.json` anywhere.** `find . -name 'ACTIVE-MUTATION.json' -not -path './.git/*'` -> no output.
- **Floor verification: record exists, resolved versions and result recorded, shared `.venv` not mutated.** The canonical floor was read this pass from `docs/builder/BUILD.md` `## Floor verification` — Django **5.2.16**, Python **3.10**, strawberry-graphql **0.316.0** — never from memory or from a restated number. The build report records venv `/tmp/dsf-floor-r2b` (outside the repo), `django 5.2.16` / `strawberry-graphql 0.316.0` / `Python 3.10.19`, scope `tests/types/test_definition_order.py --no-cov`, result `46 passed`; Worker 3 reproduced it. Shared-`.venv` non-mutation verified by reading it here rather than by trusting the `--python` flags: `uv pip list` -> `django 6.1`, `strawberry-graphql 0.323.2` — the newest-supported set, not the floor. A leaked floor install would have shown 5.2.16 / 0.316.0.
- **Temp-test disposition is recorded.** `### Temp test verification` states "deleted at cycle end, not promoted", with its reason. The file is on disk at `docs/builder/temp-tests/r2b/test_sdl_assertion_is_non_distinguishing.py` alongside `proofs.json` and a `__pycache__/`; the directory is untracked scratch cleared per cycle by `scripts/clean_up.py`. **The deletion belongs to closeout, not to this pass, and was not performed here.**
- **Focused scope green, no `--cov*` anywhere.** `uv run pytest tests/types/test_definition_order.py --no-cov -q -n0` -> `46 passed in 0.17s`. Recorded as run, per `## Final verification job` step 5. Grepping this artifact for `--cov` outside the literal `--cov*` prohibitions and `--no-cov` returns nothing, so no pass in this item used a coverage flag in any form.
- **Staged-anchor sweep: not owed here.** R2b is neither a doc-wrap nor a final in-spec slice; `bld-010-final.md` carries the tree-wide `TODO(spec-010` sweep.

### Summary

R2b shipped one test row, `tests/types/test_definition_order.py::test_assigned_relation_field_resolver_kwarg_override_keeps_consumer_resolver`, and no package source. It closes F20: spec-010's `Tests cover all four shapes` sentence is now true, each of the four listed shapes pinned by exactly one row with none doubled up, and the sentence needed a landed row rather than a rewrite. The row pins the annotated-assignment shape's double set membership — the only relation configuration in which the narrow phase-2 skip set is populated *and* the name sits in the broader union — and its load-bearing assertion is resolver identity, chosen because the SDL was measured byte-identical whether the boundary holds or not. The `BUILD.md` file-mutation failability proof against the pre-existing phase-2 skip remains owed and maintainer-gated; it is carried forward named rather than waived.

### Spec changes made (Worker 1 only)

**No edit to `docs/SPECS/spec-010-foundation-0_0_4.md`.** Item 2 confirmed the sentence became true by the row landing, exactly as the plan predicted; `### Manual annotation contract for relation fields` needs no rewrite. Spec status-line re-verification performed this spawn (`docs/builder/worker-1.md` `## Spec status-line re-verification`): the header carries a title, a rationale-companion pointer, and `## Purpose`, with no status or predecessor line this item falsifies. `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-010-foundation-0_0_4.md` -> exit **0** (`OK: 12 terms`); `docs/SPECS/appx/spec-010-foundation-0_0_4-terms.csv` untouched, since no glossary anchor named by the spec body changed.

**Deferral reason for the one `- [ ]` box** (`docs/builder/ARTIFACT.md` `## Final verification (Worker 1)`): the `BUILD.md` file-mutation failability proof for `django_strawberry_framework/types/finalizer.py::finalize_django_types #"skip_field_names=definition.consumer_assigned_relation_fields"` is deferred to **maintainer follow-up** — the target file carries a concurrent session's uncommitted comment-only hunk, no worker may `cp`-restore over it, and the item introduces no new boundary, so no mandatory `BUILD.md` obligation is waived; the anchor-verified manifest is on disk and the run is carried into `bld-010-final.md`'s `### Deferred work catalog` with its expected node-id set.

**Rationale entry appended** to `docs/SPECS/appx/spec-010-foundation-0_0_4-rationale.md` `## Coverage pass — the claim that was never true`: a keyed **F20** entry beside F16 — the claim the spec could not make, the four-to-four row mapping that makes it true, why the annotated assignment is a genuine fourth case (the double membership against F11's two skip sets), and the rejected alternative of making the row discriminate Strawberry's annotation-over-resolver-return-type precedence, with the consequence that the floor run is not evidence about that precedence. Appended during the build as `### Performing the rationale move` rule 4 permits; `scripts/check_trailing_commas.py --check` on the file -> exit 0.

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
