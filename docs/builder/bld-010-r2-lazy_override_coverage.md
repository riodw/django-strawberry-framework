# Build: R2 — close the untested `strawberry.lazy` relation-override claim (F16)

Spec reference: `docs/SPECS/spec-010-foundation-0_0_4.md` #"### Manual annotation contract for relation fields" (the `Tests cover all four shapes` list) and #"## Strawberry finalization strategy" (the `Annotated[..., strawberry.lazy("module.path")]` optional-override bullet)
Build plan: `docs/builder/build-010-foundation-0_0_4.md` #"### R2 finding — the one code gap"
Status: final-accepted

## Plan (Worker 1)

### Verdict on question 1: the shape works at `HEAD`

**It works, end to end. R2 stays a test-only item; no source finding, no re-partition.**

Worker 0 dispatched F16 with the remediation framed as a hypothesis (`docs/builder/BUILD.md` `## Review rounds`: a prescribed remediation is never an instruction). The hypothesis was tested two ways before this plan was written — by reading the call graph, and by executing the shape.

**Call-graph reading, confirmed against source:**

1. `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__` #"consumer_annotated_relation_fields = frozenset(" collects the name from `cls.__annotations__` on the sole test `field.name in consumer_annotations` (plus the `auto`-exclusion). It never inspects the annotation's *shape*, so an `Annotated[...]` object routes identically to a plain `list["ItemType"]`.
2. The name lands in the `consumer_authored_fields` union (`base.py::DjangoType.__init_subclass__` #"consumer_authored_fields = frozenset(").
3. `base.py::_build_annotations` #"if field.name in consumer_authored_fields" (relation branch) `continue`s before both `annotations[field.name] = PendingRelationAnnotation` and the `pending.append(PendingRelation(` call — so **no placeholder is synthesized and no `PendingRelation` is recorded**.
4. `base.py::DjangoType.__init_subclass__` #"cls.__annotations__ = {**synthesized, **consumer_annotations}" — `synthesized` carries no entry for the name, so the consumer's `Annotated[...]` object survives byte-identical.
5. `types/finalizer.py::finalize_django_types` phase 2 calls `_attach_relation_resolvers(..., skip_field_names=definition.consumer_assigned_relation_fields)`. The skip set is the **assigned** set only, so an annotation-only override still receives the generated resolver (`types/resolvers.py::_attach_relation_resolvers`).
6. Strawberry prioritises the class annotation over the resolver return type — `.venv/lib/python3.14/site-packages/strawberry/types/field.py::StrawberryField.resolve_type` #"Prioritise the field type over the resolver return type" — which matters here because every generated resolver is annotated `-> Any` (`types/resolvers.py::_make_relation_resolver`). Without that precedence the lazy annotation would be discarded and the field would be untyped.

**Executed proof.** A throwaway probe outside the repo (scratchpad, never in the tree) declared a target `DjangoType` in a standalone importable module and a source type carrying
`items: list[Annotated["LazyItemType", strawberry.lazy("lazy_item_module")]]`, with the target's name **absent from the source module's namespace** so the forward reference could only resolve through the lazy module path. Measured, in one run:

```text
consumer_authored: frozenset({'items'})
annotated_relation: frozenset({'items'})
assigned_relation:  frozenset()
pending:            []
annotation preserved: list[typing.Annotated[ForwardRef('LazyItemType', is_class=True),
                      <strawberry.types.lazy_type.StrawberryLazyReference object>]]
resolver: resolve_items
SDL: items: [LazyItemType!]!
schema.get_type_by_name("LazyItemType").origin is lazy_item_module.LazyItemType -> True
```

A second probe added a **primary** `DjangoType` for the same Django model (`primary = True`) alongside the lazily-referenced one and re-measured: `items` still resolved to the lazily-referenced class, and the primary type never entered the SDL. That second run is the basis for Test 2 below.

Consequence for the plan: F16 is exactly what Worker 0 graded it — a shipped contract asserted in two consumer-facing documents (`docs/SPECS/spec-010-foundation-0_0_4.md` and `docs/GLOSSARY.md#definition-order-independence`) with nothing pinning it. The remedy is test rows, and the spec text needs no correction.

### Verdict on question 2: tier and fixture placement

**Tier: package `tests/`, in the existing `tests/types/test_definition_order.py`, beside its three sibling shapes.**

`AGENTS.md` rule 10 puts anything reachable by a real fakeshop GraphQL query in `examples/fakeshop/test_query/`. This is not that. The subject is a **consumer declaration shape** — what a `DjangoType` subclass may write in its class body — not a query path. Pinning it live would require adding a permanent `strawberry.lazy` relation override to a shipped fakeshop app schema, which changes the example project's public schema surface, drags in the `docs/builder/BUILD.md` `### Example-project schema changes must sync every schema-module list` obligation, and buys no new package-line coverage: the package lines involved (`_build_annotations`'s short-circuit, `_attach_relation_resolvers`'s skip set) are already executed by every live fakeshop query. The three sibling shapes are pinned in `tests/types/test_definition_order.py`; the fourth corner of one contract belongs with them, not in a different tree.

**Fixture: add ONE new module beside the existing pair, do not reuse or extend them.**

`tests/types/fixtures/branch_module.py` and `tests/types/fixtures/shelf_module.py` exist, and reuse was assessed rather than assumed:

- **Reject extending them.** Both are spec-021 `Meta.filterset_class` fixtures — their docstrings say so, they pair with each other, and `tests/types/test_definition_order.py::test_filterset_class_resolves_across_module_boundary` asserts against their exact `Meta` surface. Adding a relation field to `BranchType` changes that surface and risks a finding in a test R2 does not own.
- **Reject extending them, second reason.** Both carry `from __future__ import annotations`, which stringifies the whole annotation. `docs/GLOSSARY.md#definition-order-independence` lists *stringified annotations from `from __future__ import annotations`* as a **separate** supported shape from the lazy one. Landing the lazy shape inside a `__future__`-annotated module would exercise a blend of two listed shapes and pin neither cleanly.
- **Reject pointing `strawberry.lazy(...)` at an existing fakeshop app schema module.** It would couple a package test to example-app module names and force a `sys.modules` eviction of a real app schema module — precisely the cross-test-pollution / `DuplicatedTypeName` hazard `docs/builder/BUILD.md` `### Example-project schema changes must sync every schema-module list` describes.
- **Accept: one new module holding only the lazy target.** The source `DjangoType` stays declared inside the test function, matching this file's dominant idiom. The lazy reference still genuinely crosses a module boundary — resolution happens against the *referenced* module, so where the source class lives is irrelevant (the probe confirmed this with the source at module scope and again with it unreachable by name).

**Why only one new module, not two.** The escape hatch's whole point is that the referring side needs no import of the target, so a second fixture module would add a tracked file that proves nothing the single one does not.

### Verdict on question 3: what the test must assert

`docs/builder/BUILD.md` `### Query-shape tests must pin the load-bearing property, not observability` governs. Constructing the class and reading an attribute would pass whether or not the lazy reference ever resolved. Four properties, each asserted directly:

- **(A) The consumer's annotation survives collection unrewritten.** Read `SourceType.__annotations__["items"]`, unwrap with `typing.get_args`, and assert the inner `__metadata__[0]` is a `strawberry.types.lazy_type.StrawberryLazyReference` whose `.module` equals the fixture's dotted path. Verified attribute name: `.module`. A rewrite would leave `PendingRelationAnnotation` or a concrete class here instead.
- **(B) No `PendingRelation` is recorded for that field.** Assert no record in `registry.iter_pending_relations()` has `source_type is SourceType`, checked **before** `finalize_django_types()` (the finalizer discards resolved records, so a post-finalize read cannot distinguish "never recorded" from "recorded and resolved").
- **(C) The generated relation resolver is still attached.** This is the annotation-only branch, which keeps it. Use the file's existing `_strawberry_field(SourceType, "items")` helper and assert `base_resolver.wrapped_func.__name__ == "resolve_items"`, the same assertion shape as `::test_annotation_only_relation_override_keeps_generated_resolver`.
- **(D) The schema builds and the field resolves to the lazily-referenced target type.** This is what separates the lazy shape from the plain-string one already covered, and none of A-C reaches it. Build a real schema (`@strawberry.type Query` with a resolver returning `list[SourceType]`, then `strawberry.Schema(query=Query)`) and assert **type identity, not name**: `schema.get_type_by_name("LazyItemType").origin is <fixture module>.LazyItemType`. Corroborate with the SDL line `items: [LazyItemType!]!`. Schema construction is itself load-bearing here — an unresolvable lazy reference raises there — which is why none of the three sibling override tests, which stop at `finalize_django_types()`, could have caught this.

### Verdict on question 4: two rows, both working cases — not a rejection case

**There is no rejection path to test.** The package validates nothing about a lazy relation annotation: `docs/SPECS/spec-010-foundation-0_0_4.md` #"Validation that a consumer-supplied annotation matches the Django relation cardinality" defers cardinality validation explicitly, and a bad module path raises `ModuleNotFoundError` from Strawberry at schema build — third-party behavior, not this package's contract, and pinning it would make the suite fail on an upstream message change for no contract gain.

**Two rows are still owed, because one is not distinguishing.** Assertion (D) alone proves a type named `LazyItemType` won, and in Test 1 that is the only candidate — so a regression that dropped the annotation-only short-circuit entirely would resolve the pending relation back to the same class and (D) would still pass. Test 2 removes that degeneracy: it declares a **second** `DjangoType` for the same Django model with `primary = True` inside the test, so synthesis and the consumer override name *different* classes. Under a regression the field would resolve to the primary; under the contract it resolves to the lazily-referenced fixture class. Measured in the probe.

Two rows also mean the mutation in `### Failability proof obligation` cannot land in weakly-pinned territory on the strength of one assertion.

### DRY analysis

**Helper inventory checked.** Refreshed package-wide this pass — `docs/shadow/helper-inventory.md`, 1789 lines, regenerated from `django_strawberry_framework/` with the `worker-1.md` `### Package-wide helper inventory before helper planning` script (`wc -l docs/shadow/helper-inventory.md` -> `1789`). Shapes searched: `lazy`, `forward`, `annotated`, `fixture`, `module_path` (`grep -in "lazy\|forward\|annotated\|fixture\|module_path" docs/shadow/helper-inventory.md`). One relevant candidate found and **deliberately not reused**:

- `django_strawberry_framework/mutations/fields.py::_lazy_ref` — "Return `Annotated[<type_name>, strawberry.lazy(module_path)]`". It builds the exact annotation object the test needs, and using it would be a defect: the test's subject is **what a consumer writes by hand**, and routing through a package-internal builder would pin the package's own helper instead of the documented consumer shape, while masking a regression in which the package stops accepting a hand-written `Annotated[...]`. Write the annotation literally.

Nothing else in the inventory is a candidate: no package helper participates in consumer-supplied relation annotations at all — `_build_annotations` short-circuits *before* touching them.

**Existing patterns reused.**

- `tests/types/test_definition_order.py:37-48` `_strawberry_field(type_cls, field_name)` — the finalized-field accessor both new tests use for assertion (C). No new accessor.
- `tests/types/test_definition_order.py:29-34` the autouse `_isolate_registry` fixture — both new tests inherit registry isolation; neither adds its own teardown.
- `tests/types/test_definition_order.py:1107-1135` `::test_filterset_class_resolves_across_module_boundary` — the established idiom for a fixture module that registers `DjangoType`s at import time: pop the dotted name from `sys.modules`, then import inside the test body so the module executes *after* the autouse `registry.clear()`. Its inline comment already explains why `importlib.reload` is wrong here. Both new tests copy this idiom; neither re-derives it.
- `tests/types/fixtures/branch_module.py` / `shelf_module.py` — the shape of a fixture module (module docstring naming what it exercises, `apps.*.models` import, minimal `Meta`). The new fixture follows it, minus `from __future__ import annotations`.

**New helpers justified.** None. One new *fixture module* is justified (`### Verdict on question 2`); it declares one `DjangoType` and no functions.

**Duplication risk avoided.** The naive implementation writes a private `_lazy_annotation(...)` builder or a second finalized-field accessor in the test file, and repeats the `sys.modules`-eviction dance as free-standing lines in each of the two tests. The plan prevents all three: annotation written literally in each class body (that literal *is* the subject under test, so its repetition across two tests is the contract being asserted twice, not duplication); `_strawberry_field` reused; and the eviction reduced to a single shared statement per test against one dotted name (one line, not a helper — extracting a two-line helper for two call sites in one file would be premature; the condition that would justify extracting it is a **third** fixture-module test appearing in this file, at which point the eviction-plus-import pair becomes a `pytest` fixture).

The fixture's dotted module path is a repeated string literal across the fixture module, both tests' `strawberry.lazy(...)` calls, and both tests' `sys.modules.pop(...)`. Bind it once as a module-level constant in the test file and reference it from the `sys.modules` and assertion sites; the `strawberry.lazy("...")` calls keep the literal, because a `strawberry.lazy(CONSTANT)` call is not the shape a consumer writes and the test exists to pin the consumer shape. State this split in `### Implementation notes`.

### Boundary count and the split question

**Zero new boundaries.** R2 adds no guard, cap, rejection path, or validation branch — it adds two test rows and one fixture module for behavior that already exists. `docs/builder/BUILD.md` `### Slice splitting`: the unit is one coherent diff (three files, one contract, one focused test scope) and is not split.

### Implementation steps

Line numbers are pin-at-write-time navigational hints. Verify against the current source before editing — `tests/types/test_definition_order.py` was clean at plan time (`git status --porcelain | grep -c "tests/types"` -> `0`), but this tree carries a concurrent session's work and the baseline has moved three times this cycle.

1. **Create `tests/types/fixtures/lazy_relation_target_module.py`.** Module docstring in the established fixture voice: it declares the lazy-reference *target* for the cross-module `Annotated[..., strawberry.lazy(...)]` relation-override shape, is imported by name from `tests/types/test_definition_order.py`, and exists because `strawberry.lazy` requires a real importable module path (`docs/SPECS/spec-010-foundation-0_0_4.md` #"Spike C"). Body: one `DjangoType` on `apps.products.models.Item` with `fields = ("id", "name")`. **Do NOT add `from __future__ import annotations`** — the reason is in `### Verdict on question 2` and belongs in the docstring too, so a future tidy-up does not add it back. Do not declare a `FilterSet`, a relation field, or a second class.

2. **Add Test 1 to `tests/types/test_definition_order.py`,** immediately after `::test_assigned_relation_field_override_keeps_consumer_resolver` (ends ~line 276, before `::test_relation_field_class_attribute_shadowing_raises` at ~line 278). Placement is by **contract cohesion**: the four shapes of one spec contract read as one block. Name it for the property, e.g. `test_cross_module_lazy_relation_override_resolves_to_the_referenced_type`. Body:
   - pop the fixture's dotted name from `sys.modules`, then `from tests.types.fixtures import lazy_relation_target_module` inside the test — the idiom and its rationale are at `tests/types/test_definition_order.py:1118-1124`;
   - declare the source `DjangoType` on `apps.products.models.Category`, `fields = ("id", "name", "items")`, with the annotation written literally:
     `items: list[Annotated["LazyItemType", strawberry.lazy("tests.types.fixtures.lazy_relation_target_module")]]`;
   - assert the definition's split sets: `consumer_annotated_relation_fields == frozenset({"items"})`, `consumer_assigned_relation_fields == frozenset()`;
   - assertions (A), (B), (C), (D) from `### Verdict on question 3`, with (B) taken **before** `finalize_django_types()`.
   - `typing` is not currently imported in this file; add what the unwrap needs (`Annotated` and whichever of `get_args` / `__metadata__` the implementation uses) to the existing import block, keeping ruff's ordering.

3. **Add Test 2 immediately after Test 1** — same fixture module, same annotation, plus an in-test `DjangoType` on `apps.products.models.Item` carrying `primary = True`. Assert the same (A)-(D) set, and add the discriminating pair: `schema.get_type_by_name(...).origin is lazy_relation_target_module.LazyItemType`, and the primary type's GraphQL name is **absent** from `schema.as_str()`. Name it for what it discriminates, e.g. `..._wins_over_the_registered_primary_type`. `Meta.primary` is spec-018 surface used here only as a foil; do not assert anything about `Meta.primary`'s own contract.

4. **Bind the fixture's dotted path as a module-level constant** in `tests/types/test_definition_order.py` per `### DRY analysis`, and use it at the `sys.modules` and assertion sites.

5. **Run the focused scope** `uv run pytest tests/types/test_definition_order.py --no-cov` and record it. No `--cov*` flags in any form (`docs/builder/BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool`); `--no-cov` is required because `pytest.ini`'s `addopts` auto-applies `--cov`.

6. **Run the floor verification** named in `### Floor-verification scope` below, in the build pass, and record it in the build report's `### Floor verification` subsection.

7. **Perform the failability proof** in `### Failability proof obligation` below, and record it in `### Failability proofs`.

8. **`uv run ruff format` and `uv run ruff check --fix` scoped to the two files this pass touches**, never `.` (`docs/builder/ARTIFACT.md` `### Validation run` — scoping is what stops churn on the concurrent session's files). Then `git status --short`: anything modified beyond the two writable files is a **stop-and-report**, never a revert.

9. **Do not touch** any baseline-dirty path. Re-derive the baseline with `git status --porcelain` rather than quoting the plan's list — it stood at 47 paths at pre-flight, 71 at this planning pass's dispatch, and **77** when this plan was written (`git status --porcelain | wc -l` -> `77`). Everything outside this cycle's `bld-010-*` / `build-010-*` / `spec-010` paths and R2's two writable files is out of scope in both directions.

**Maintainer obligation this pass cannot discharge — surface it, do not attempt it.** `examples/fakeshop/apps/kanban/constants.py` is rendered by `scripts/build_kanban_tracked_path_constants.py`, which enumerates **`git ls-files`** (`scripts/build_kanban_tracked_path_constants.py::tracked_file_paths`), and its `source-layout`/kanban pre-commit hook fails when the file is stale. `tests/types/fixtures/branch_module.py` and `shelf_module.py` are both listed there today. The new fixture module is **untracked** until the maintainer stages it, so regenerating now produces no change, and workers never stage or commit. Worker 2 records in `### Notes for Worker 1 (spec reconciliation)` that after `git add tests/types/fixtures/lazy_relation_target_module.py` the maintainer must run `uv run python scripts/build_kanban_tracked_path_constants.py` before committing, or the hook blocks the commit. Do not edit `constants.py` by hand.

### Test additions / updates

- `tests/types/fixtures/lazy_relation_target_module.py` — **new**. One `DjangoType` on `apps.products.models.Item`. Its only job is to be a real importable module path for `strawberry.lazy`.
- `tests/types/test_definition_order.py::test_cross_module_lazy_relation_override_...` (Test 1) — pins (A) annotation survives collection unrewritten, (B) no `PendingRelation` recorded, (C) generated relation resolver still attached, (D) schema builds and the field's type **is** the fixture module's class (identity, plus SDL corroboration).
- `tests/types/test_definition_order.py::test_cross_module_lazy_relation_override_..._primary...` (Test 2) — same four, plus the discriminator: with a `primary = True` type registered for the same model, the consumer's lazily-referenced type still wins and the primary never enters the SDL.
- **No temp/scratch tests are needed for Worker 3.** The behavior is directly assertable; nothing here needs a scratch harness to demonstrate a non-distinguishing assertion. Worker 3 may of course write one under `docs/builder/temp-tests/r2/` if it distrusts assertion (D).
- **No other test tree is touched.** `docs/builder/BUILD.md` `### Example-project schema changes must sync every schema-module list` was checked and **does not apply**: the private schema-module enumerations are `examples/fakeshop/test_query/conftest.py`'s `_PROJECT_APP_SCHEMA_MODULES` and `examples/fakeshop/tests/test_inspect_django_type.py`'s `_SCHEMA_MODULES`, and both enumerate *example-app* schema modules. Evidence that a `tests/types/fixtures/` module is not a member of either: `grep -rn "branch_module\|shelf_module" tests/ examples/ django_strawberry_framework/` returns **8** occurrences, all in `tests/types/test_definition_order.py`, the two fixture docstrings, and `examples/fakeshop/apps/kanban/constants.py` — **zero** in any schema-module list. `docs/builder/BUILD.md` `### Test staleness a focused run cannot see` likewise does not apply: no example-model field set changes and no wire shape converts.

### Failability proof obligation

`docs/builder/BUILD.md` `## Failability proofs: prove the test can fail` scopes the requirement to a **new boundary, guard, gate, or rejection path**. **R2 introduces none** — it adds test rows for behavior that already exists. Stating that and stopping would be the wrong call here, so the decision is made rather than left open:

**A proof IS owed, and this plan requires it.** The new rows' entire value is that they fail when the behavior is absent, and nothing else in the process can establish that for a test-only pass. Worker 2 performs exactly one:

- **Target:** `django_strawberry_framework/types/base.py::_build_annotations`, relation branch.
- **Anchor (checked first, per the loop's opening step):** `field_meta = field_map[snake_case(field.name)]`. Measured unique — `grep -c -F 'field_meta = field_map[snake_case(field.name)]' django_strawberry_framework/types/base.py` -> **1**. Do **not** anchor on `if field.name in consumer_authored_fields:`; that string occurs **2** times in the file (relation and scalar branches) and the loop aborts on a non-unique anchor.
- **Mutation:** delete the relation branch's two-line short-circuit — the `if field.name in consumer_authored_fields:` / `continue` pair sitting immediately **above** the anchor line. That removes the mechanism the whole shape depends on; it does not merely perturb code near it.
- **Scope as run:** `uv run pytest tests/types/test_definition_order.py --no-cov`. Record the pre-mutation state of that same scope first.
- **Expected:** both new rows fail, alongside the existing annotation-only override rows. List the failing node ids; never assert a count. Collection/setup errors must be **0** or the count is not a valid count.
- **Restore and prove it:** `cp` from a scratch path **outside** the repository, then `cmp`, exit 0. Never `git checkout -- <path>` — this tree is legitimately dirty with a concurrent session's work.
- `uv run python scripts/prove_failability.py <manifest>` is the supported way to run it (`docs/builder/BUILD.md` `### Mechanized: scripts/prove_failability.py`); manifest home `docs/builder/temp-tests/r2/proofs.json`.

Because this proof mutates a package source file, note for Worker 3: the mutation is authorized by this plan and by the proof loop, is transient, and must not appear in the final diff. `django_strawberry_framework/types/base.py` is **not** in R2's writable set for any other purpose.

### Hot-path budget

**Not applicable; this plan declares no hot path**, consistent with the build plan's `Hot-path declaration: none.` R2 lands two test rows and one test fixture module — no package source, nothing that runs per request, per resolver, per row, per connection, or per outbound message. The analysis in `### Verdict on question 1` confirms the shape needs no production change, so the declaration is not quietly overridden. If Worker 2 or Worker 3 concludes otherwise, record it under `### Notes for Worker 1 (spec reconciliation)`; Worker 0 re-partitions rather than a worker overriding the declaration in place.

### Floor-verification scope

**R2 is this cycle's only floor-scoped item**, per the build plan. A `strawberry.lazy` forward reference is resolved by Strawberry at schema-construction time — the "schema and type construction against Strawberry internals" seam in `docs/builder/BUILD.md` `### When it is required`.

- **Owning pass: Worker 2's build pass.** The final gate is the backstop that confirms it happened, not a second owner.
- **Focused scope to re-run at the floor:** `tests/types/test_definition_order.py`. Not the full sweep; this file is the seam's home and carries all four override shapes.
- **Floor versions:** take them from `docs/builder/BUILD.md` `## Floor verification`, which is their single canonical statement — Django 5.2.16 on Python 3.10 with strawberry-graphql 0.316.0. Never restate `.venv`'s versions from memory; read them if a pass needs them.
- **Isolated venv outside the repo, explicit `--python`.** Follow `### How to build the floor venv` exactly. **Never** install into the shared `.venv`; `uv pip install` ignores `UV_PROJECT_ENVIRONMENT` and will land in `.venv` if the `--python` is omitted, silently changing the floor for every later pass and every concurrent session on this tree.
- **Record** the scratch venv path, the resolved versions as read by `uv pip list --python <venv>/bin/python`, the command, and pass/fail, in the build report's `### Floor verification` subsection. An unrecorded floor run is not verifiable later.
- **Named floor risk.** The assertion-(D) accessor `strawberry.Schema.get_type_by_name` was confirmed present in the shared `.venv` only. If it is absent or differently shaped at 0.316.0, that is a **test-authoring** adjustment, not a contract failure — see `### Implementation discretion items`. A genuine failure of the *shape* at the floor is a different matter and routes back here: the fix is production code that works at the floor, never a raised floor and never a `pragma: no cover`.

### Implementation discretion items

Assessed and decided as Worker 2's:

- **The exact accessor for assertion (D)'s type identity.** The required property is fixed — **identity against the fixture module's class, not a name match** — and `schema.get_type_by_name("<name>").origin is <fixture>.LazyItemType` is verified working in the shared `.venv`. If the floor run shows that accessor absent or reshaped at strawberry-graphql 0.316.0, Worker 2 picks an equivalent that still asserts identity (unwrapping the finalized `StrawberryField.type` to its `LazyType` and resolving it is one; the `schema_converter` type map is another) and records which and why in `### Implementation notes`. An SDL-string-only fallback is **not** acceptable — it asserts a name, which is exactly the observability failure `docs/builder/BUILD.md` warns about.
- **Test function names**, provided each names the property it pins rather than the mechanism.
- **The class names inside the tests** (`LazyItemType` on the fixture is fixed, since the lazy string references it by name; the source and primary type names are free).
- **How assertion (A) unwraps the annotation** — `typing.get_args(...)[0].__metadata__[0]` versus `typing.get_type_hints(..., include_extras=True)` or an equivalent. The required end state is fixed: a `StrawberryLazyReference` whose `.module` equals the fixture's dotted path.
- **Whether the `sys.modules` eviction is one inline statement or a loop** over a one-element tuple mirroring `::test_filterset_class_resolves_across_module_boundary`. Either is fine; do not extract a helper for two call sites.

### Dispatched findings checklist

One box per sub-check Worker 2 must land. Boxes stay `- [ ]` at planning; Worker 2 ticks `- [x]` only what actually landed in its diff and states any deferral in the build report rather than ticking; Worker 1 audits every tick at final verification.

- [x] F16 (`docs/builder/build-010-foundation-0_0_4.md` `### R2 finding — the one code gap`): "Spec-010 `### Manual annotation contract for relation fields` states 'Tests cover all four shapes' and lists the cross-module `Annotated[..., strawberry.lazy("...")]` relation override as one of them. **No test anywhere exercises that shape on a `DjangoType` relation field.**" — closed by the rows below. Verified at `HEAD` against `django_strawberry_framework/types/base.py::_build_annotations` and `django_strawberry_framework/types/finalizer.py::finalize_django_types`.
- [x] `tests/types/fixtures/lazy_relation_target_module.py` created: module docstring in the established fixture voice, one `DjangoType` on `apps.products.models.Item`, **no** `from __future__ import annotations`, no `FilterSet`, no second class.
- [x] Test 1 added to `tests/types/test_definition_order.py`, placed immediately after `::test_assigned_relation_field_override_keeps_consumer_resolver`.
- [x] Test 1 asserts (A): the consumer's `Annotated[...]` annotation survives collection unrewritten — inner `__metadata__[0]` is a `StrawberryLazyReference` with `.module` equal to the fixture's dotted path.
- [x] Test 1 asserts (B): no `PendingRelation` is recorded for the overridden field, checked **before** `finalize_django_types()`.
- [x] Test 1 asserts (C): the generated relation resolver is still attached (`base_resolver.wrapped_func.__name__ == "resolve_items"`), via the file's existing `_strawberry_field` helper.
- [x] Test 1 asserts (D): a real `strawberry.Schema` builds, and the field's type **is** `lazy_relation_target_module.LazyItemType` by identity, with the SDL line as corroboration.
- [x] Test 2 added: same shape plus an in-test `primary = True` `DjangoType` on the same model; asserts the consumer's lazily-referenced type wins and the primary type's GraphQL name is absent from the SDL.
- [x] The fixture's dotted module path is bound once as a module-level constant and reused at the `sys.modules` and assertion sites (the `strawberry.lazy("...")` literals stay literal, per `### DRY analysis`).
- [x] No package source, no spec, no other test tree, and no baseline-dirty path was modified; `git status --short` after the scoped ruff runs shows only R2's two writable files.
- [x] Focused run recorded: `uv run pytest tests/types/test_definition_order.py --no-cov`, no `--cov*` flag in any form.
- [x] Floor verification performed **in this build pass** and recorded in `### Floor verification`: isolated venv outside the repo, explicit `--python`, resolved versions read via `uv pip list --python <venv>/bin/python`, focused scope `tests/types/test_definition_order.py`, pass/fail. Shared `.venv` untouched.
- [x] Failability proof performed and recorded in `### Failability proofs` per `### Failability proof obligation`: anchor uniqueness checked first, the relation-branch short-circuit removed, failing node ids **listed**, collection/setup errors 0, pre-mutation state of the same scope recorded, revert proved by byte-comparison.
- [x] `### Notes for Worker 1 (spec reconciliation)` records the maintainer obligation to regenerate `examples/fakeshop/apps/kanban/constants.py` after staging the new fixture file — and records that no spec edit is owed, since the shape works as the spec and `docs/GLOSSARY.md#definition-order-independence` describe.

### Notes for Worker 1 (spec reconciliation)

Recorded at planning; revisit at final verification.

- **No spec edit is owed by this item as planned.** Question 1 resolved in favour of the spec: `docs/SPECS/spec-010-foundation-0_0_4.md` #"Tests cover all four shapes" becomes true when R2 lands, rather than needing correction. Likewise `docs/GLOSSARY.md#definition-order-independence`'s "cross-module `Annotated[..., strawberry.lazy("module.path")]` annotations" bullet — which is generated from `examples/fakeshop/db.sqlite3` and must never be hand-edited in any case.
- **Spec status/header lines re-verified this spawn** (`worker-1.md` `## Spec status-line re-verification`). `docs/SPECS/spec-010-foundation-0_0_4.md` lines 1-5 were rewritten by R1 earlier in this cycle and still describe the build's current state; no line was falsified by this planning pass. No edit made.
- **Spec-009 anchors not touched.** R2 reads neither spec-009 nor its anchors; the concurrent session reconciling it is unaffected in both directions.
- **`examples/fakeshop/apps/kanban/constants.py` staleness** is a commit-time maintainer obligation, not a worker one — reasoning under `### Implementation steps`. Confirm at final verification that Worker 2 surfaced it rather than acting on it.

---

## Build report (Worker 2)

### Files touched

Grounded in `git status --porcelain -- tests/ docs/builder/temp-tests/`, run after both scoped ruff invocations. Exactly two paths in the whole tree are this pass's:

- `tests/types/test_definition_order.py` (` M`) — three imports added (`importlib`, `typing.Annotated` / `typing.get_args`, `strawberry.types.lazy_type.StrawberryLazyReference`), the module-level `_LAZY_TARGET_MODULE` constant, and the two new test rows placed immediately after `::test_assigned_relation_field_override_keeps_consumer_resolver`.
- `tests/types/fixtures/lazy_relation_target_module.py` (`??`, new) — one `DjangoType` (`LazyItemType`) on `apps.products.models.Item` with `fields = ("id", "name")`. No `from __future__ import annotations`, no `FilterSet`, no second class; the docstring states why the `__future__` import must not be added back.

Everything else `git status` reports is the concurrent session's baseline work, re-derived this pass rather than quoted from the plan: `git status --porcelain | wc -l` -> **87** (the plan recorded 77; `django_strawberry_framework/types/definition.py` and both spec-009/spec-010 spec + rationale files are among the paths that moved). Nothing outside the two paths above was edited, reverted, staged, or checked out. `docs/builder/temp-tests/r2/` is gitignored and reports nothing.

### Tests added or updated

- `tests/types/test_definition_order.py::test_cross_module_lazy_relation_override_types_the_field_as_the_referenced_class` — the plan's (A) annotation survives collection unrewritten (`get_args(...)[0].__metadata__[0]` is a `StrawberryLazyReference` whose `.module` equals `_LAZY_TARGET_MODULE`); (B) no `PendingRelation` recorded for the field, read **before** `finalize_django_types()`; (C) the generated relation resolver is still attached (`base_resolver.wrapped_func.__name__ == "resolve_items"`, via the file's existing `_strawberry_field`); (D) a real `strawberry.Schema` builds and `schema.get_type_by_name("LazyItemType").origin is lazy_relation_target_module.LazyItemType` by identity, corroborated by the SDL line `items: [LazyItemType!]!`. Also pins the definition's split sets.
- `tests/types/test_definition_order.py::test_cross_module_lazy_relation_override_wins_over_the_registered_primary_type` — the same (A)-(D) set with an in-test `Meta.primary = True` `DjangoType` on the same Django model, plus the discriminator: `"PrimaryItemType" not in schema.as_str()`. Nothing about `Meta.primary`'s own contract is asserted.
- No temp/scratch test was needed or written. `docs/builder/temp-tests/r2/` holds only the proof manifest and the tool's emitted report.

### Validation run

- `uv run ruff format tests/types/test_definition_order.py tests/types/fixtures/lazy_relation_target_module.py` — pass (scoped, never `.`).
- `uv run ruff check --fix tests/types/test_definition_order.py tests/types/fixtures/lazy_relation_target_module.py` — pass (`All checks passed!`). The first run reported two `F821 Undefined name 'LazyItemType'`; see `### Implementation notes`.
- `uv run python scripts/check_trailing_commas.py --check tests/types/test_definition_order.py tests/types/fixtures/lazy_relation_target_module.py` — exit 0 (ruff does not replicate `AGENTS.md` rule 17).
- `git status --short` after both ruff invocations — classified above; every modified file is either this pass's or baseline-dirty. Nothing was reverted.
- `uv run pytest tests/types/test_definition_order.py --no-cov` — **45 passed** (xdist, 8 workers). Re-run serially, `uv run pytest tests/types/test_definition_order.py --no-cov -n0` — 45 passed, so the two rows are not order-dependent.
- `uv run pytest tests/types/ --no-cov` — **444 passed**. Run because the new fixture module registers a `DjangoType` at import time and the neighbouring files share the global registry; it is the cross-pollution check `docs/builder/BUILD.md` `### Example-project schema changes must sync every schema-module list` describes for the tree this fixture actually lives in.
- No `--cov*` flag was used in any form in any run this pass.

### Failability proofs

Performed with `uv run python scripts/prove_failability.py docs/builder/temp-tests/r2/proofs.json --output docs/builder/temp-tests/r2/proofs.md`, exit **0**. The anchor check ran first and separately (`--check-anchors-only`, exit 0) before any copy, and `git status --porcelain -- django_strawberry_framework/types/base.py` was **empty immediately before the copy and again immediately after the restore** — the proof target was not among the concurrent session's dirty paths at any point, so the `cp`-based restore could not overwrite another session's work. The scratch root is outside the repository (the session scratchpad, `.../scratchpad/failability-proofs`).

- `django_strawberry_framework/types/base.py::_build_annotations` — mutation applied: the relation branch's two-line consumer-authored short-circuit **deleted**, i.e. the anchor `if field.name in consumer_authored_fields:` / `continue` / `field_meta = field_map[snake_case(field.name)]` replaced by the bare `field_meta = ...` line, so a consumer-supplied relation annotation is overwritten by the synthesized placeholder and a pending relation is recorded for it. Anchor uniqueness verified first: `grep -c -F 'field_meta = field_map[snake_case(field.name)]' django_strawberry_framework/types/base.py` -> **1**, and the tool independently asserted exactly-once. Scope as run: `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/types/test_definition_order.py`. Pre-mutation state of that same scope: `45 passed` (pytest exit 0); pre-existing failing rows excluded from the count: 0. Failing node ids:
  - `tests/types/test_definition_order.py::test_cross_module_lazy_relation_override_types_the_field_as_the_referenced_class`
  - `tests/types/test_definition_order.py::test_cross_module_lazy_relation_override_wins_over_the_registered_primary_type`

  Collection/setup errors: **0** (pytest exit 1, `2 failed, 43 passed`). Revert proved by byte-comparison: `filecmp.cmp(shallow=False)` -> True plus sha256 `63eace5ea5996f80...` == `63eace5ea5996f80...` against the pre-mutation copy. Not weakly pinned (2 rows > 1); inside Worker 3's mandatory independent re-run floor (<= 3 rows).

**A measured result the plan did not predict, and it is the finding, not noise.** The plan expected "both new rows fail, alongside the existing annotation-only override rows". The existing rows do **not** fail: with the short-circuit gone, `::test_annotation_only_relation_override_keeps_generated_resolver`'s plain `list[ItemType]` annotation is overwritten by `PendingRelationAnnotation` and then resolved by the finalizer back to `list[ItemType]` — the same object, so every one of its assertions still holds, and its `consumer_*` set assertions read state computed in `__init_subclass__` rather than in `_build_annotations`. The two new rows are therefore the **only** rows in the suite that pin this short-circuit at all, which is a stronger justification for F16 than the plan's own reasoning: before this pass the mechanism was not merely untested for the lazy shape, it was unpinned for every shape.

### Hot-path budget

Not applicable; plan declares no hot path. Nothing in this pass runs per request, per resolver, per row, per connection, or per outbound message — the diff is two test rows and one test fixture module, and no package source changed (the proof mutation was transient and is proved reverted above). The plan's `### Hot-path budget` conclusion is confirmed rather than overridden.

### Floor verification

Owned by this pass per the plan's `### Floor-verification scope`. The shared `.venv` was **not** touched: every install carried an explicit `--python`, and the venv lives outside the working tree.

- Scratch venv path: `/tmp/dsf-floor-r2` (outside the repository).
- Built per `docs/builder/BUILD.md` `### How to build the floor venv`: `uv venv /tmp/dsf-floor-r2 --python 3.10`; `uv pip install --python /tmp/dsf-floor-r2/bin/python -e . --group dev`; `uv pip install --python /tmp/dsf-floor-r2/bin/python 'django==5.2.16' 'strawberry-graphql==0.316.0'` (which downgraded the resolved `django==5.2.17` / `strawberry-graphql==0.324.0` to the floor points).
- Resolved versions, read by `uv pip list --python /tmp/dsf-floor-r2/bin/python`: `django 5.2.16`, `strawberry-graphql 0.316.0`, `django-filter 26.1`, `pytest 9.1.1`; interpreter `/tmp/dsf-floor-r2/bin/python -V` -> `Python 3.10.19`.
- Focused scope as run: `/tmp/dsf-floor-r2/bin/python -m pytest tests/types/test_definition_order.py --no-cov` -> **45 passed** (pytest reports `django: version: 5.2.16`, `platform darwin -- Python 3.10.19`). **Pass.**
- **The named floor risk did not materialise.** `strawberry.Schema.get_type_by_name` exists and behaves identically at strawberry-graphql 0.316.0, so assertion (D) kept its identity form unchanged and the plan's identity-preserving fallback was not needed. No SDL-string-only weakening was applied anywhere.

### Implementation notes

- **`importlib.import_module(_LAZY_TARGET_MODULE)` instead of the sibling test's `from tests.types.fixtures import lazy_relation_target_module`.** The plan offered the `sys.modules`-eviction idiom of `::test_filterset_class_resolves_across_module_boundary`, and copying it verbatim **failed**, reproducibly and only when both new rows ran in the same process: `from <package> import <submodule>` is satisfied by the parent package's still-set attribute, so after the `sys.modules.pop(...)` it hands back the stale module object without repopulating `sys.modules`. The fresh execution then happened later, inside `strawberry.Schema(...)` when the lazy reference imported the path — i.e. **after** `finalize_django_types()` — and the registry correctly refused it (`cannot register LazyItemType after finalization`). `importlib.import_module` bypasses the parent-attribute shortcut and re-executes the module at the point the test intends. The reasoning is stated in the test as an invariant comment. This is small, mechanically obvious drift within the plan's discretion item on eviction shape, but it also means the sibling test's idiom is load-bearing only on a first import — see `### Notes for Worker 3`.
- **`# noqa: F821` on the `"LazyItemType"` forward reference.** `F821` is selected in this repo's ruff config and fires on a forward-reference string naming a symbol the module never imports — which is precisely the shape under test. The alternative, a `if TYPE_CHECKING:` import of the target, would put the name in the module's namespace and weaken the very property assertion (D) exists to prove (that resolution goes through the module path). The adjacent comment states that invariant rather than the lint.
- **The dotted path split, as the plan's `### DRY analysis` specified.** `_LAZY_TARGET_MODULE` is used at the `sys.modules.pop`, the `importlib.import_module`, and the `.module` assertion; the two `strawberry.lazy("...")` calls keep the literal, because a literal there is the consumer shape under test.
- **Assertion (A) unwrap:** `get_args(annotation)[0].__metadata__[0]`, the plan's first-named option — one expression, no `get_type_hints` namespace plumbing, and it reads the annotation object actually stored on the class rather than a re-evaluated copy.
- **No `seed_data(N)` / `create_users(N)` first line.** `AGENTS.md` rule 8 governs catalog/auth tests; these rows touch no database (no `django_db` marker, no model instances), exactly like the three sibling override rows they sit beside. Matching the precedent.
- **`registry.iter_pending_relations()` filtered by `source_type is CategoryType`** rather than asserting the whole pending set is empty: the fixture module's own `LazyItemType` selects only `("id", "name")` and records nothing, but scoping the assertion to the type under test keeps it true regardless of what else a future fixture registers.

### Notes for Worker 3

- **The `docs/builder/temp-tests/r2/` scratch holds `proofs.json` (the manifest) and `proofs.md` (the tool's emitted report).** The `### Failability proofs` entry above transcribes every measured field from that report; re-running `uv run python scripts/prove_failability.py docs/builder/temp-tests/r2/proofs.json` reproduces it. The scratch root inside the manifest points outside the repository.
- **Before re-running the proof, re-check `git status --porcelain -- django_strawberry_framework/types/base.py`.** It was clean at this pass's proof time, but the concurrent session's dirty set grew from 77 to 87 paths during this pass and already includes `django_strawberry_framework/types/definition.py`, a file in the same subsystem. If `base.py` has gone dirty, the `cp` restore is no longer safe and the proof must be skipped and reported, not forced.
- **The two new rows share a large amount of assertion text by design.** The repetition is the contract asserted twice under different registry conditions (plan `### Verdict on question 4`); the literal `Annotated[...]` block in particular is the subject under test and is deliberately not extracted into a helper (plan `### DRY analysis`, which also rejects reusing `mutations/fields.py::_lazy_ref` for the same reason).
- **No shadow file was generated or read this pass.** `scripts/review_inspect.py` was not run: this pass adds no package source and no new `.py` file under `django_strawberry_framework/`; the one new `.py` file is a pure class-definition fixture module with no logic.
- **`docs/builder/BUILD.md` `### Test staleness a focused run cannot see` does not apply** — no example-model field set changed and no wire shape converted — so the full `uv run pytest tests/ --no-cov` sweep it mandates is not owed by this pass. `tests/types/` was swept anyway (444 passed) for the registry-pollution reason above.

### Notes for Worker 1 (spec reconciliation)

- **Maintainer obligation at commit time, surfaced and deliberately not acted on.** `examples/fakeshop/apps/kanban/constants.py` is rendered from `git ls-files` by `scripts/build_kanban_tracked_path_constants.py::tracked_file_paths`, and its pre-commit hook fails when the file is stale. The new fixture `tests/types/fixtures/lazy_relation_target_module.py` is **untracked**, so regenerating now would produce no change; after `git add tests/types/fixtures/lazy_relation_target_module.py` the maintainer must run `uv run python scripts/build_kanban_tracked_path_constants.py` before committing, or the hook blocks the commit. `constants.py` was not hand-edited and no regenerate was attempted.
- **No spec edit is owed by this pass, and the plan's verdict on question 1 is confirmed by execution.** The shape works at `HEAD` exactly as `docs/SPECS/spec-010-foundation-0_0_4.md` #"Tests cover all four shapes" and `docs/GLOSSARY.md#definition-order-independence` describe: the tests were written against the shipped behavior and passed without a single production change, at the shared `.venv` and at the floor. No production code change was required or made, so `docs/builder/worker-0.md` `## Per-slice dispatch` step 6a's re-partition route was not taken.
- **One measured correction to the plan's expectation, recorded because it strengthens rather than weakens the item** (detail under `### Failability proofs`): removing the relation-branch short-circuit fails **only** the two new rows, not the pre-existing annotation-only override row the plan predicted would also fail. The pre-existing rows cannot fail on that mutation, because the placeholder resolves back to the same class. Nothing in the spec asserts otherwise, so this is not a spec amendment — but if a future reader cites `::test_annotation_only_relation_override_keeps_generated_resolver` as pinning the collection-phase short-circuit, that citation is wrong.
- **Small, mechanically obvious drift, implemented and recorded** (`worker-2.md` `## Plan-vs-implementation drift`): the fixture-module import uses `importlib.import_module` rather than the `from ... import ...` form the plan's step 2 sketched, for the reason in `### Implementation notes`. It stays inside the plan's own discretion item on the eviction shape and changes no architectural call. A side observation for whoever next touches `::test_filterset_class_resolves_across_module_boundary`: its `sys.modules.pop` + `from ... import ...` pair re-executes the fixture modules only on their first import in a process, so its eviction is weaker than its comment implies. That test is not in R2's writable set and was not touched.

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

---

## Review (Worker 3)

### Independent failability re-run — mutation recorded BEFORE it is made

Per `docs/builder/worker-3.md` `### Reading is necessary, not sufficient: the failability proof`, this
record is written before the source is touched.

- **Dirty-check first (the abort rule).** `git status --porcelain -- django_strawberry_framework/types/base.py`
  -> **0 lines** (empty), so the proof target is NOT among the concurrent session's dirty paths and the
  `cp`-based restore cannot overwrite another session's uncommitted edit. The re-run proceeds.
- **Anchor check first, per the loop's opening step.**
  `grep -c -F 'field_meta = field_map[snake_case(field.name)]' django_strawberry_framework/types/base.py`
  -> **1**. (`grep -c -F 'if field.name in consumer_authored_fields:'` -> **2**, which is why the
  three-line block, not that line alone, is the anchor.)
- **Boundary re-run:** `django_strawberry_framework/types/base.py::_build_annotations`, relation branch.
- **Mutation to be applied:** delete the two-line consumer-authored short-circuit
  (`if field.name in consumer_authored_fields:` / `continue`) sitting immediately above the anchor line,
  leaving the bare `field_meta = field_map[snake_case(field.name)]`. This removes the mechanism the
  documented override contract depends on rather than perturbing code near it.
- **Scope, as Worker 2 recorded it:** `tests/types/test_definition_order.py`.
- **Restore:** `cp` from a scratch path OUTSIDE the repository, proved by byte-comparison. Never
  `git checkout` / `git restore` / `git stash`.

Measured results are recorded under `### Temp test verification` below once the run completes.

### Independent failability re-run — measured result

Run with `uv run python scripts/prove_failability.py docs/builder/temp-tests/r2/w3-proofs.json --output
docs/builder/temp-tests/r2/w3-proofs.md`, exit **0**. Manifest and emitted report are W3-owned copies
(`w3-*`), written beside Worker 2's rather than over them, so the two records are separately readable.

- **Scope as run** (Worker 2's, unchanged): `uv run pytest --no-cov --color=no -p no:cacheprovider
  --tb=no -q -rfE tests/types/test_definition_order.py`.
- **Pre-mutation state of that same scope:** `45 passed`, pytest exit 0; pre-existing failing rows
  differenced out: 0.
- **Failing node ids under the mutation** (`len()` = 2; collection/setup errors **0**, pytest exit 1,
  `2 failed, 43 passed`):
  - `tests/types/test_definition_order.py::test_cross_module_lazy_relation_override_types_the_field_as_the_referenced_class`
  - `tests/types/test_definition_order.py::test_cross_module_lazy_relation_override_wins_over_the_registered_primary_type`
- **Node-id set comparison with Worker 2's record: identical** (set difference empty in both
  directions), at the same recorded scope. Not weakly pinned (2 > 1).
- **Revert proved by byte-comparison:** `filecmp.cmp(shallow=False)` -> True plus sha256
  `63eace5ea5996f80...` == `63eace5ea5996f80...` against the pre-mutation copy taken outside the repo.
  Post-run `git status --porcelain -- django_strawberry_framework/types/base.py` -> **0 lines**. No
  `git checkout` / `restore` / `stash` was used at any point.

**Boundaries re-run vs accepted on Worker 2's record.** The diff carries exactly one proof entry and it
sits inside the mandatory floor (<= 3 rows), so the re-run set is `{ types/base.py::_build_annotations
relation-branch short-circuit }` and the accepted-on-record set is **empty**.

**Worker 2's unpredicted measurement is confirmed, independently.** The plan expected the pre-existing
annotation-only override row to fail under the same mutation. It does not: 45 rows ran pre-mutation,
`::test_annotation_only_relation_override_keeps_generated_resolver` among them, and it is absent from
the mutant's failing set. The mechanism Worker 2 gives for that — the synthesized placeholder resolves
back to the same class, so every assertion in that row still holds — is consistent with the probe result below, where synthesis with no competing primary names the identical class. The consequence
Worker 2 draws is the correct one and is the strongest available justification for F16: before this
pass the relation-branch short-circuit was unpinned for **every** override shape, not merely untested
for the lazy one.

### High:

None.

### Medium:

None. (One Medium-weight **spec-text** defect was found; it is not R2's to fix and is escalated under
`### Notes for Worker 1 (spec reconciliation)` below, per `docs/builder/worker-3.md` `### Acceptance
gate`.)

### Low:

None.

### DRY findings

- **The fixture module's existence was challenged and the challenge fails.** `docs/builder/worker-3.md`
  `### The existence challenge`: the live question is whether
  `tests/types/fixtures/lazy_relation_target_module.py` needs to exist when
  `tests/types/fixtures/branch_module.py` / `shelf_module.py` already do. The plan's two recorded
  reasons hold on inspection and are not re-raised: both siblings are spec-021 `Meta.filterset_class`
  fixtures whose exact `Meta` surface is asserted by
  `tests/types/test_definition_order.py::test_filterset_class_resolves_across_module_boundary`, and
  both carry `from __future__ import annotations`, which `docs/GLOSSARY.md` lists as a **separate**
  supported forward-reference shape from the lazy one. Landing the lazy target in either would pin a
  blend of two shapes. The module is 22 lines, holds one class and no logic, and deleting it would
  leave `strawberry.lazy` with no importable path to resolve — which is the escape hatch's whole
  premise. It should exist.
- **`tests.types.fixtures.lazy_relation_target_module` appears 3x** (`scripts/review_inspect.py`
  overview, `## Repeated string literals`): once as `_LAZY_TARGET_MODULE`, twice as the literal inside
  `strawberry.lazy("...")`. Not a finding — the plan's `### DRY analysis` rejects collapsing the two
  call sites with a stated reason (`strawberry.lazy(CONSTANT)` is not the shape a consumer writes, and
  the consumer shape is the subject under test), and the diff implements exactly that split.
- **The two rows' near-identical assertion blocks are the contract asserted twice**, not duplication:
  they differ only in the registry condition (a competing `primary = True` type) and that difference is
  what makes the second row a discriminator. Extracting the shared body into a helper would hide the
  one axis the pair exists to vary. No consolidation recommended.
- **No package-internal helper was routed through.** The plan's rejection of
  `django_strawberry_framework/mutations/fields.py::_lazy_ref` is correct and the diff honours it: the
  annotation is written literally in both class bodies, so a regression that stopped accepting a
  hand-written `Annotated[...]` still fails these rows.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` -> **empty**. `__all__` and the re-export list
are unchanged; the pass lands no package source at all.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. The one adjacent obligation —
`examples/fakeshop/apps/kanban/constants.py` staleness once the new fixture is staged — was correctly
surfaced rather than acted on, and is verified real: `grep -n "branch_module\|shelf_module"
examples/fakeshop/apps/kanban/constants.py` -> **2** occurrences (lines 273-274), so the tracked-path
list does enumerate `tests/types/fixtures/*.py` and will go stale at `git add`.

### What looks solid

- **Assertion (D) is the load-bearing one and it survived at full strength.** It asserts type
  **identity** (`schema.get_type_by_name("LazyItemType").origin is
  lazy_relation_target_module.LazyItemType`), with the SDL line kept only as corroboration - not the
  reverse. `docs/builder/BUILD.md` `### Query-shape tests must pin the load-bearing property, not
  observability` is the rule this could most easily have failed, and the plan's named floor risk (the
  accessor missing at strawberry-graphql 0.316.0, which would have tempted an SDL-string fallback) did
  not materialise and no weakening was applied.
- **The second row is a genuine discriminator, verified by probe rather than by reading.** See
  `### Temp test verification`: with the override removed, synthesis names `LazyItemType` in Test 1's
  registry condition (so Test 1 alone WOULD pass vacuously, exactly as the plan argues) and names
  `PrimaryItemType` in Test 2's. The divergence Test 2 claims to create is real.
- **The `importlib.import_module` drift is correct and necessary**, also verified by probe rather than
  accepted: after `sys.modules.pop`, `from tests.types.fixtures import <mod>` returns the **stale**
  module object and leaves `sys.modules` un-repopulated, while `importlib.import_module` returns a
  fresh object and repopulates. Worker 2's account of the downstream failure (fresh execution deferred
  into the schema build, i.e. after finalization, where registration is refused) follows from that.
- **Order independence checked four ways**, all green: each row alone (`-n0`), the pair in **reverse**
  declaration order (`T2 T1`, `-n0`), the whole file, and `uv run pytest tests/types --no-cov -q -n0`
  -> **444 passed**. The rows carry no ordering assumption in either direction.
- **The `# noqa: F821` is the right call, not a lint dodge.** The alternative (`if TYPE_CHECKING:`
  importing the target) would put `LazyItemType` in the test module's namespace and destroy the exact
  property assertion (D) exists to prove; the adjacent comment states that invariant rather than the
  lint.
- **`AGENTS.md` rule 8 is satisfied by exemption, correctly.** Neither row touches the database (no
  `django_db` marker, no model instances), matching the three sibling override rows they sit beside.
- **Floor verification reproduced as written.** `uv pip list --python /tmp/dsf-floor-r2/bin/python` ->
  `django 5.2.16`, `strawberry-graphql 0.316.0`, `django-filter 26.1`, `pytest 9.1.1`;
  `/tmp/dsf-floor-r2/bin/python -V` -> `Python 3.10.19`; `/tmp/dsf-floor-r2/bin/python -m pytest
  tests/types/test_definition_order.py --no-cov` -> **45 passed**. The venv is outside the repo and the
  shared `.venv` is untouched (it reports Python 3.14.2 / Django 6.1, so the two are unmistakably
  distinct environments).
- **Test placement holds against `AGENTS.md` rule 10, and the plan's supporting claim is true.** Rule
  10 sends anything reachable by a real fakeshop query to `examples/fakeshop/test_query/`; the plan
  argues the subject is a consumer **declaration** shape and that the package lines involved are
  already executed live. That second half was checked rather than assumed:
  `examples/fakeshop/apps/kanban/schema.py` #"dependencies: list[" declares annotation-only relation
  overrides on a shipped fakeshop type, so `types/base.py::_build_annotations`' relation-branch
  short-circuit does run under live `/graphql` traffic. No package line is stranded by keeping the row
  in `tests/`, and pinning it live would have forced a permanent `strawberry.lazy` override into a
  shipped example schema for no coverage gain.
- **The schema-module-list obligation was re-derived independently**, not read off the diff:
  `grep -rn "SCHEMA_MODULES" tests examples --include="*.py"` finds exactly two enumerations
  (`examples/fakeshop/schema_reload.py::_PROJECT_APP_SCHEMA_MODULES`,
  `examples/fakeshop/tests/test_inspect_django_type.py::_SCHEMA_MODULES`), both listing example-app
  schema modules only. A `tests/types/fixtures/` module is not a member of either, so
  `docs/builder/BUILD.md` `### Example-project schema changes must sync every schema-module list` is
  genuinely not engaged.
- **Full parallel sweep run independently** (`uv run pytest --no-cov`, 8 workers): **5681 passed, 40
  skipped, 1 failed in 130.79s**. The single failure is
  `tests/rest_framework/test_inputs.py::test_dedupe_serializer_input_shape_is_sole_cache_protocol`,
  which lives in the concurrent session's baseline-dirty set alongside
  `django_strawberry_framework/rest_framework/inputs.py`. It is untouched by and unrelated to R2 (a
  serializer-input cache-identity assertion), was not reverted or edited, and is recorded here rather
  than acted on per `AGENTS.md` rule 34. Every `tests/types/` row is green.
- Lint re-verified read-only: `uv run ruff format --check`, `uv run ruff check`, and
  `uv run python scripts/check_trailing_commas.py --check` on both R2 files all clean.

### Static helper use

`uv run python scripts/review_inspect.py tests/types/test_definition_order.py --output-dir docs/shadow`
was **run**, not skipped: `docs/builder/BUILD.md` `### When to run the helper during build` triggers on
"50+ lines to any file outside" the package, and the diff adds ~146 lines to that file. Output:
`docs/shadow/tests__types__test_definition_order.overview.md` / `.stripped.py`. Its
`## Repeated string literals` section is the evidence behind the second DRY bullet above; no cross-folder
import or control-flow hotspot was introduced.

`tests/types/fixtures/lazy_relation_target_module.py` is **skipped**, under the rule's own exemption for
a new pure-class-definition module: one docstring, two imports, one `class` with a `Meta` block, zero
statements of logic.

### Temp test verification

Three probes under `docs/builder/temp-tests/r2/` (gitignored; none is a promotion candidate — each
tests a claim about the diff, not a package contract R2 owns):

- `test_discriminator_probe.py` — **2 passed.** Removes the consumer override from each row's registry
  condition and asks what synthesis picks instead.
  `::test_without_override_and_without_a_primary_synthesis_picks_the_same_class` passes, proving Test 1's
  identity assertion is non-distinguishing on its own and that the second row is genuinely owed;
  `::test_without_override_but_with_a_primary_synthesis_picks_the_primary` passes, proving the field
  types as `[PrimaryItemType!]!` absent the override, so Test 2's identity assertion does discriminate.
  Disposition: kept as scratch, not promoted — its subject is `Meta.primary` synthesis (spec-018), not
  R2's contract, and the mutant run already pins the same property from the other direction.
- `test_import_idiom_probe.py` — **2 passed.** Measures the plan-vs-implementation drift directly:
  after `sys.modules.pop`, `from ... import ...` returns the same object as before the pop (`True`) and
  does **not** repopulate `sys.modules` (`False`), while `importlib.import_module` returns a different
  object (`False`) and does repopulate (`True`). Its second row measures the same two values for
  `tests.types.fixtures.branch_module` and gets the same stale-object result — the basis for the
  sibling-test note routed to Worker 1 below. Disposition: kept as scratch, not promoted; it pins
  CPython import semantics, not package behavior.
- `test_outer_annotated_shape_probe.py` — **1 failed, deliberately.** Declares the relation override in
  the *outer* spelling the spec's own contract bullet uses,
  `items: Annotated[list["LazyItemType"], strawberry.lazy(...)]`, and schema construction raises
  `strawberry.exceptions.unresolved_field_type.UnresolvedFieldTypeError: Could not resolve the type of
  'items'`. This is the evidence for the escalated spec finding below. Disposition: kept as scratch,
  not promoted — a permanent row pinning an upstream error class for an unsupported spelling would fail
  on any Strawberry message change for no contract gain, which is the same reasoning the plan used to
  reject pinning `ModuleNotFoundError`.

### Dispatched findings checklist audit

All 14 boxes are ticked; each was walked against the diff. No box is ticked without a matching fix and
no box is silently unaddressed.

- F16 closed — the two rows exist and, per the independent mutant run, are the only rows in the scope
  that fail when the mechanism is removed.
- Fixture created to spec: docstring in the established voice, one `DjangoType` on
  `apps.products.models.Item` with `fields = ("id", "name")`, **no** `from __future__ import
  annotations` (and the docstring states why, so a future tidy-up does not add it back), no `FilterSet`,
  no second class. Verified by reading the file end to end.
- Placement: Test 1 begins immediately after
  `::test_assigned_relation_field_override_keeps_consumer_resolver` ends, ahead of
  `::test_relation_field_class_attribute_shadowing_raises`. The four shapes now read as one block.
- (A) asserted — `get_args(CategoryType.__annotations__["items"])[0].__metadata__[0]` is a
  `StrawberryLazyReference` with `.module == _LAZY_TARGET_MODULE`. Reads the object actually stored on
  the class, not a re-evaluated copy.
- (B) asserted **before** `finalize_django_types()` in both rows, scoped `if pending.source_type is
  CategoryType` — the scoping is a strengthening, not a weakening: it stays true regardless of what a
  future fixture registers.
- (C) asserted via the file's existing `_strawberry_field` helper; no second accessor was written.
- (D) asserted by identity in both rows, SDL as corroboration.
- Test 2 adds the in-test `primary = True` type and `"PrimaryItemType" not in schema.as_str()`; it
  asserts nothing about `Meta.primary`'s own contract, as the plan required.
- The dotted path is bound once and used at the `sys.modules.pop`, the `importlib.import_module`, and
  the `.module` assertion; the two `strawberry.lazy("...")` literals stay literal per the recorded
  split.
- No package source, spec, other test tree, or baseline-dirty path was modified: `git status
  --porcelain tests/types` -> exactly ` M tests/types/test_definition_order.py` and
  `?? tests/types/fixtures/lazy_relation_target_module.py`. The 23 dirty package sources and every other
  dirty path are the concurrent session's, re-derived this pass (`git status --porcelain | wc -l` ->
  **95**, up from the build report's 87 and the plan's 77 — the baseline is still moving).
- Focused run reproduced: `uv run pytest tests/types/test_definition_order.py --no-cov` -> 45 passed
  (and 45 passed at `-n0`). No `--cov*` flag was used in any form in any command this review ran.
- Floor verification reproduced as recorded — numbers under `### What looks solid`.
- Failability proof reproduced independently with an identical node-id set — record above.
- The maintainer `constants.py` obligation and the "no spec edit owed" statement are both present in the
  build report's `### Notes for Worker 1 (spec reconciliation)`; the first is verified real above, and
  the second is where I depart from Worker 2 — see below.

### Notes for Worker 1 (spec reconciliation)

- **Escalated (Medium): spec-010's own example of the shape R2 just pinned does not work.**
  `docs/SPECS/spec-010-foundation-0_0_4.md` #"Annotation override" spells the lazy override as
  `items: Annotated[list["ItemType"], strawberry.lazy("...")]` — the `Annotated` wrapping the `list`.
  Measured: that spelling raises
  `strawberry.exceptions.unresolved_field_type.UnresolvedFieldTypeError: Could not resolve the type of
  'items'` at schema construction (`docs/builder/temp-tests/r2/test_outer_annotated_shape_probe.py`).
  The working spelling is the inner one, `list[Annotated["Target", strawberry.lazy("module.path")]]`,
  which is what R2's rows use — and the same spec **already names it the correct one**, at
  #"Spike C confirmed same-module string forward references", so the document contradicts itself rather
  than merely being terse. `docs/GLOSSARY.md` #"cross-module `Annotated[..., strawberry.lazy(" is
  shape-agnostic (`...`) and needs nothing. This is a spec-text defect in a file only Worker 1 may edit,
  it is not R2's to fix, and it does not block acceptance of R2's diff. Resolution paths: (a) correct
  the contract bullet's example to the inner spelling and add a rationale entry keyed to
  `### Manual annotation contract for relation fields` recording that the outer spelling was measured
  non-working; (b) keep both spellings and add the outer one as a documented rejection with its error;
  (c) judge it out of this cycle's F1-F19 scope and card it. Worker 2's "no spec edit is owed by this
  pass" is right about *its own* diff and I am not contradicting it — this is a claim the spec makes
  that no finding in the plan covered, surfaced by writing the test.
- **Low, routed rather than fixed: the sibling test's module eviction is weaker than its comment says.**
  `tests/types/test_definition_order.py::test_filterset_class_resolves_across_module_boundary` pops two
  fixture modules from `sys.modules` and then re-imports them with `from tests.types.fixtures import
  branch_module, shelf_module`, under a comment asserting the pop makes "the next import trigger a fresh
  execution". Measured: it does not — the parent package's still-set attribute satisfies the import, so
  the stale module object comes back and `sys.modules` is never repopulated
  (`docs/builder/temp-tests/r2/test_import_idiom_probe.py::test_sibling_filterset_idiom_has_the_same_weakness`).
  The row passes today only because nothing else imports those two modules first, which makes it a
  latent order dependence of exactly the class `docs/builder/BUILD.md` `### Example-project schema
  changes must sync every schema-module list` describes as invisible below the full parallel run.
  **Pre-existing at HEAD**, verified read-only (`git show HEAD:tests/types/test_definition_order.py` into
  a scratch path outside the repo, then read — the same `from ... import ...` pair and the same comment
  are there). Worker 2 was right to leave it alone: it is outside R2's writable set, and Worker 2's own
  note already flags it. Recommend it be carded or folded into a later item rather than bolted onto R2 —
  the fix is one `importlib.import_module` per module plus a corrected comment.
- **Not a finding, recorded so the next reader does not re-derive it:** the full parallel sweep this
  review ran fails one row in the concurrent session's dirty area
  (`tests/rest_framework/test_inputs.py::test_dedupe_serializer_input_shape_is_sole_cache_protocol`).
  Per `docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`, a failing
  row's HEAD status is not worker-verifiable on a tree this dirty, so it is escalated rather than
  diagnosed. The final gate will meet it again; it is unrelated to R2 in both directions.
- **The hot-path declaration stands.** R2 lands no package source; nothing runs per request, resolver,
  row, connection, or outbound message. `Not applicable` is correct and was not quietly overridden.

### Review outcome

`review-accepted`.

Every checklist box is landed and audited, the one boundary in scope is proved failable at 2 rows with a
node-id set I reproduced independently at the recorded scope, the mutation was recorded before it was
made and its revert is proved by byte-comparison with the target confirmed clean before and after, the
floor run reproduces as written, and the two rows pin type **identity** rather than an SDL string — with
the second row measured to be a real discriminator rather than a restatement of the first. No High,
Medium, or Low finding stands against the diff. The one Medium-weight issue found is a defect in the
spec's own worked example, which only Worker 1 may edit; it is escalated above with resolution paths per
`docs/builder/worker-3.md` `### Acceptance gate`, and Worker 1's final verification owns the decision.

---

## Final verification (Worker 1)

Every number below was command-produced at the moment it was written; commands are quoted beside their
results. `git status --porcelain | wc -l` -> **107** at the start of this pass (95 at Worker 3's review,
87 at the build report, 77 at planning) — the concurrent session's baseline is still moving, so nothing
here is quoted from an earlier pass's list.

### The escalated spec defect — verified independently, and it holds

Worker 3's finding is a claim about the engine, so `docs/builder/BUILD.md` `## Review rounds` ("a
prescribed remediation is a hypothesis, never an instruction") was applied to it exactly as Worker 0
applied it to F16. I did not accept the probe; I re-measured both spellings myself, from a scratch
script **outside** the repository (`<session scratchpad>/w1_verify_lazy_shapes.py`), against the shipped
package with `django.setup()` and the same fixture module R2 landed.

Measured, one run, both rows:

```text
=== OUTER  Annotated[list[...], lazy] ===
  annotation stored: typing.Annotated[list['LazyItemType'], <StrawberryLazyReference object>]
  RESULT: RAISED strawberry.exceptions.unresolved_field_type.UnresolvedFieldTypeError
  msg: Could not resolve the type of 'items'. Check that the class is accessible from the global module scope.
=== INNER  list[Annotated[..., lazy]] ===
  annotation stored: list[typing.Annotated[ForwardRef('LazyItemType', is_class=True), <StrawberryLazyReference object>]]
  SDL items line: ['  items: [LazyItemType!]!']
  RESULT: schema built OK
```

**The finding holds.** The spec's `### Manual annotation contract for relation fields` offered the outer
spelling as the worked example while its own `### Spike outcome (Phase 0 complete)` named the inner one
correct. One of the two had to be wrong and it was the contract bullet — the half a consumer copies.

**Root cause, read at the seam rather than inferred.**
`.venv/lib/python3.14/site-packages/strawberry/utils/typing.py::eval_type` converts a lazy reference
into a `LazyType` only under `arg.resolve_forward_ref(args[0]) if isinstance(args[0], ForwardRef) else
args[0]`. In the outer spelling `args[0]` is `list["LazyItemType"]`, a generic alias and not a
`ForwardRef`, so the marker is discarded.

**A second measurement, because "it raises" is the weaker half of the story.** A follow-up probe
(`<session scratchpad>/w1_verify_outer_inert.py`) bound the target name in the declaring module's
namespace and re-ran the *outer* spelling: it builds, emitting `items: [LazyItemType!]!`. So the outer
spelling is not broken syntax — it is an **inert marker** that degrades to a plain string forward
reference. It appears to work in exactly the cases where the escape hatch is unnecessary and fails in
the only case it exists for, which is why the correction had to state placement normatively rather than
just swap one example for another.

**`docs/GLOSSARY.md#definition-order-independence`: Worker 0's reading is CONFIRMED, no glossary change
is owed.** Read at `docs/GLOSSARY.md` #"cross-module `Annotated[..., strawberry.lazy(" — the bullet
elides the annotated type (`...`), so it names the marker without committing to its placement. That is
unspecific, not false: the working shape does contain `Annotated[<target>, strawberry.lazy("module.path")]`.
The file is generated from `examples/fakeshop/db.sqlite3` and a change would be a DB edit plus a
regenerate — a Worker 2 re-partition — for a bullet that is not wrong. The placement rule belongs in the
contract document and is now there. Nothing is stopped and recorded for Worker 0 on this point.

### Dispatched findings checklist — every tick audited against the diff

All 14 boxes read `- [x]`. I walked each against the working-tree diff rather than inheriting Worker 3's
walk. **No over-tick found; no box un-ticked; nothing left `- [ ]`, so no deferral reason is owed.** The
non-obvious ones:

- **Box 2 (fixture)** — read end to end. `tests/types/fixtures/lazy_relation_target_module.py` holds one
  `DjangoType` on `apps.products.models.Item` with `fields = ("id", "name")`, no
  `from __future__ import annotations` (and the docstring says why, so a tidy-up does not add it back),
  no `FilterSet`, no second class. Landed as specified.
- **Box 3 (placement)** — `grep -n "^def test_" tests/types/test_definition_order.py` puts
  `::test_assigned_relation_field_override_keeps_consumer_resolver` at 258,
  `::test_cross_module_lazy_relation_override_types_the_field_as_the_referenced_class` at 287,
  `::..._wins_over_the_registered_primary_type` at 361, and
  `::test_relation_field_class_attribute_shadowing_raises` at 427. The four override shapes read as one
  contiguous block, as planned.
- **Boxes 4-7 (A-D)** — each assertion is in the diff in the required form. (B) is read before
  `finalize_django_types()` in both rows and is **scoped** to `pending.source_type is CategoryType`; that
  scoping is a strengthening, not a weakening, since an unscoped emptiness assertion would silently start
  depending on what other fixtures register. (D) asserts identity
  (`schema.get_type_by_name("LazyItemType").origin is lazy_relation_target_module.LazyItemType`) with the
  SDL line as corroboration and not the reverse — the one place this item could most easily have
  degraded into an observability assertion, and it did not.
- **Box 10 (nothing else modified)** — `git status --porcelain -- tests/types` -> exactly
  ` M tests/types/test_definition_order.py` and `?? tests/types/fixtures/lazy_relation_target_module.py`.
  Everything else dirty under `tests/` (18 further files) is the concurrent session's and was neither
  edited nor reverted.
- **Box 14** — the box asserts that the note was *recorded*, and it was. Worker 2's "no spec edit is owed
  by this pass" was true of its own diff and is not contradicted by the spec correction above, which
  comes from a claim the spec makes that no dispatched finding covered. The tick stands.

### The two obligations, confirmed mechanically

**Failability proof and its independent re-run — the tree is clean.**

- `git status --porcelain -- django_strawberry_framework/types/base.py` -> **0 lines**. The proof target
  carries no residue of either mutation.
- The boundary is present and intact:
  `grep -c -F 'field_meta = field_map[snake_case(field.name)]' django_strawberry_framework/types/base.py`
  -> **1**, and the relation branch reads `if field.is_relation:` / `if field.name in
  consumer_authored_fields:` / `continue` / `field_meta = ...` in that order
  (`django_strawberry_framework/types/base.py::_build_annotations`). The deleted short-circuit is back.
- **No `ACTIVE-MUTATION.json` marker survives anywhere**: `find / -name "ACTIVE-MUTATION.json"` returns
  nothing, so neither `scripts/prove_failability.py` run left a live mutation behind — repo-wide and
  beyond, since the marker is written by the tool rather than into the tree.
- Both records carry every field `docs/builder/BUILD.md` `### What gets recorded` requires: the
  symbol-qualified boundary, the exact mutation, the scope as run, the pre-mutation state of that same
  scope (`45 passed`, 0 pre-existing failing rows), the failing node ids **listed** (2), collection/setup
  errors **0**, and a byte-compared revert. Worker 3 re-ran at the recorded scope and reports an
  identical node-id set. 2 rows is above the weakly-pinned threshold and inside Worker 3's mandatory
  re-run floor, so the re-run was owed rather than optional and it happened.

**Floor verification — the record exists, the versions resolve, the shared `.venv` is untouched.**

- The plan scopes floor verification to R2 alone and assigns the run to Worker 2's build pass; the build
  report's `### Floor verification` subsection carries it. `docs/builder/BUILD.md` `## Floor verification`
  is the canonical statement of the floor and reads Django **5.2.16** on Python **3.10** with
  strawberry-graphql **0.316.0** — taken from there, not from any restatement.
- Re-read at final verification: `uv pip list --python /tmp/dsf-floor-r2/bin/python` -> `django 5.2.16`,
  `strawberry-graphql 0.316.0`; `/tmp/dsf-floor-r2/bin/python -V` -> `Python 3.10.19`. All three match
  the canonical floor.
- **Shared `.venv` not mutated**: `uv pip list` -> `django 6.1`, `strawberry-graphql 0.323.2` — nowhere
  near the floor points, so no floor install leaked into it. The floor venv is at `/tmp/dsf-floor-r2`,
  outside the working tree.
- Pass/fail per command is recorded: `/tmp/dsf-floor-r2/bin/python -m pytest
  tests/types/test_definition_order.py --no-cov` -> 45 passed. The plan's named floor risk (assertion
  (D)'s accessor missing at 0.316.0) did not materialise, so no identity-preserving fallback was needed
  and no SDL-string weakening was applied.

### Focused run

`uv run pytest tests/types/test_definition_order.py --no-cov -q` -> **45 passed in 1.70s**. It runs. No
`--cov*` flag was used in any form in any command this pass issued.

### DRY across this cycle's items

No new duplication. R1 wrote Markdown only, so there is no cross-item code surface to compare. Within R2:
the two rows' near-identical assertion blocks vary exactly one axis (a competing `primary = True` type)
and that axis is what makes the second row a discriminator — extracting the shared body would hide it.
The dotted module path is bound once as `_LAZY_TARGET_MODULE` and the two `strawberry.lazy("...")`
literals stay literal, which is the split the plan decided and the diff implements. The plan's rejection
of `django_strawberry_framework/mutations/fields.py::_lazy_ref` is honoured: the annotation is written
literally in both class bodies, so a regression that stopped accepting a hand-written `Annotated[...]`
still fails these rows.

### Staged-anchor sweep

`grep -rEn 'TODO\(spec-010|TODO-(ALPHA|BETA|STABLE)-010' .` (excluding `.git`, `.venv`, and the three
board files) -> **no matches**. Nothing staged under this spec's or card's name survives anywhere in the
tree.

### Maintainer escalations

Three items, none blocking `final-accepted`. Recording plus escalating discharges the obligation
(`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`).

1. **An unrelated suite failure in the concurrent session's dirty area — escalated, not chased.**
   Worker 3's independent full parallel sweep returned 5681 passed / 40 skipped / **1 failed**:
   `tests/rest_framework/test_inputs.py::test_dedupe_serializer_input_shape_is_sole_cache_protocol`.
   Evidence gathered read-only this pass, no fix and no revert attempted:
   - **Not in R2's diff.** R2 lands `tests/types/test_definition_order.py` and
     `tests/types/fixtures/lazy_relation_target_module.py` and no package source; the failing row is in
     neither.
   - **Both the test file and the module it exercises are baseline-dirty.**
     `git status --porcelain -- tests/rest_framework/test_inputs.py
     django_strawberry_framework/rest_framework/inputs.py` -> ` M` on both.
   - **The failing node does not exist at HEAD.** `git show HEAD:tests/rest_framework/test_inputs.py`
     into a scratch path **outside** the repo, then
     `grep -c test_dedupe_serializer_input_shape_is_sole_cache_protocol` -> **0** in the HEAD copy and
     **1** in the working copy. It is a row the concurrent session is currently adding, not a regression
     this cycle could have caused.
   - **Reproduced read-only for the maintainer's convenience**, `-n0`: it fails at
     `assert shape_a == shape_b`, the differing attribute being `serializer_class` — two distinct
     function-local `ItemSer` classes with the same qualname, i.e. an in-flight cache-identity
     assertion.
   - Per `docs/builder/BUILD.md` `## Claims are proven mechanically…`, a failing test's
     pre-existing-at-HEAD status is **not worker-verifiable at all** on a tree this dirty. The above is
     the evidence available; the maintainer is the only party who can run a clean HEAD tree.

2. **The spec's four-shape test claim is now true for three of four, not four.** Measured while
   auditing the corrected section: `### Manual annotation contract for relation fields` lists
   `explicit strawberry.field(resolver=...) assignment on a relation field` as a distinct shape from
   the `@strawberry.field` decorator, and only the decorator form has a relation-field row
   (`tests/types/test_definition_order.py::test_assigned_relation_field_override_keeps_consumer_resolver`).
   `grep -rn "= strawberry.field(resolver=" tests/ examples/ --include="*.py"` returns 10 occurrences,
   none of which is an assignment to a **relation** field on a `DjangoType` — the nearest,
   `tests/types/test_base.py::test_consumer_assigned_field_resolver_on_file_column_is_not_clobbered`,
   is a file **column**. This is the same class of gap as F16 and outside R2's dispatched scope, so it
   is escalated rather than folded in. **No spec edit made**: the four shapes are the contract and the
   contract is right; only a test row is missing, and correcting the spec's test-plan sentence would
   paper over the gap instead of closing it.

3. **Two carried forward from earlier passes, unchanged and still owed at commit time.**
   `examples/fakeshop/apps/kanban/constants.py` goes stale the moment the new fixture is staged — it is
   rendered from `git ls-files` by `scripts/build_kanban_tracked_path_constants.py::tracked_file_paths`
   and its pre-commit hook fails on staleness — so after
   `git add tests/types/fixtures/lazy_relation_target_module.py` the maintainer must run
   `uv run python scripts/build_kanban_tracked_path_constants.py`. Confirmed real:
   `grep -c "branch_module\|shelf_module" examples/fakeshop/apps/kanban/constants.py` -> **2**, so the
   tracked-path list does enumerate `tests/types/fixtures/*.py`. Worker 2 correctly surfaced it rather
   than attempting it, and no worker hand-edited `constants.py`. Separately, Worker 3's Low finding on
   `::test_filterset_class_resolves_across_module_boundary` — whose `sys.modules.pop` +
   `from ... import ...` pair re-executes the fixture modules only on a first import, making its
   eviction weaker than its comment claims — is pre-existing at HEAD, outside R2's writable set, and
   worth carding; the fix is one `importlib.import_module` per module plus a corrected comment.

### Summary

R2 closed F16 with two test rows and one fixture module, and no package source. The rows pin the
cross-module `strawberry.lazy` relation override at type **identity** rather than at an SDL string, at
the shared `.venv` and at the floor, and the second row is a measured discriminator rather than a
restatement of the first. The item also produced something the plan did not anticipate: writing the test
proved the spec's own worked example of the shape does not work, a defect that had stood since `0.0.4`
in a document that already named the correct spelling elsewhere. That correction is the item's second
deliverable and is recorded below.

### Spec changes made (Worker 1 only)

Both edits triggered by Worker 3's escalated finding, re-verified by my own measurement above.

1. **`docs/SPECS/spec-010-foundation-0_0_4.md` `### Manual annotation contract for relation fields`,
   the `**Annotation override**` bullet (line 71) and the new bullet after it.** The worked example's
   lazy spelling changed from `items: Annotated[list["ItemType"], strawberry.lazy("...")]` to
   `items: list[Annotated["ItemType", strawberry.lazy("module.path")]]`, and a new normative bullet
   states that marker placement is load-bearing, gives the to-many and nullable-FK forms, and says what
   the outer spelling does instead (marker discarded, degrades to a plain forward reference,
   `UnresolvedFieldTypeError` at schema construction). *Reason:* the spec's own example did not work;
   the spec also contradicted itself, since `### Spike outcome (Phase 0 complete)` already named the
   inner spelling correct. Stated as the contract that holds, with no note that it used to say
   otherwise (`docs/builder/BUILD.md` `## Spec rationale extraction`).
2. **Same section, the `Tests cover all four shapes` list (line 78 pre-edit).**
   `` `Annotated[..., strawberry.lazy("...")]` cross-module override `` became
   `` `list[Annotated["ItemType", strawberry.lazy("module.path")]]` cross-module override ``.
   *Reason:* the elision hid the placement the bullet above now pins, and this list is what a reader
   maps onto the rows R2 landed.

Both edits verified: `uv run python scripts/check_spec_glossary.py --spec
docs/SPECS/spec-010-foundation-0_0_4.md` -> `OK: 12 terms - all have glossary entries and at least one
spec link.`, exit **0**. The twelve anchors the spec body names are unchanged, so
`docs/SPECS/appx/spec-010-foundation-0_0_4-terms.csv` was **not** touched and needs no DB work. No
inline cross-file Markdown link was added (that conversion is R3's item).
`uv run python scripts/check_trailing_commas.py --check` on both edited files -> exit **0**.

**Rationale entry, keyed to the corrected section.**
`docs/SPECS/appx/spec-010-foundation-0_0_4-rationale.md` gains
`## Coverage pass — the claim that was never true` holding one entry,
`### \`### Manual annotation contract for relation fields\` — the lazy override's worked example (F16)`.
It records what the spec used to claim, what is true now, why the outer spelling cannot work (the
`eval_type` seam plus both measurements), that this claim was **never** true rather than falsified by a
later card — it has stood since `0.0.4`, and survived precisely because the `Tests cover all four
shapes` sentence was itself false for this shape — that the spec's own Spike C had it right all along,
the rejected alternative (documenting the outer spelling as a rejection path) with its reason, and the
confirmation that `docs/GLOSSARY.md` is unspecific rather than wrong and is deliberately not changed.
The file's `## How to read this file` index was corrected from two blocks to three in the same pass, so
the index does not describe a file that no longer exists. Rationale file: 43,044 -> **47,219** bytes;
spec: 70,504 -> **71,470** bytes. The `docs/builder/` corpus ratchet does not reach specs or rationales,
only the six workflow files.

### Final status

`final-accepted`.
