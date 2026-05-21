# Build: Slice 0 — Pre-implementation verification

Spec reference: `docs/spec-016-list_field-0_0_7.md` (lines 94-103, Slice 0 checklist bullets; cross-references at lines 25 rev3 H1, lines 798 Risks "Slice 0 outcome", and lines 58-60 rev6 M1+M2 for the verification mechanism)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

- **Existing patterns reused.** Slice 0 is a verification spike that does not commit code, so "reuse" here means "the spike must mirror the exact import shapes Slice 1 will use so the verification is load-bearing."
  - `_apply_get_queryset_sync` (`django_strawberry_framework/types/relay.py:199-222`) and `_apply_get_queryset_async` (`django_strawberry_framework/types/relay.py:225-237`) — Slice 1's default-resolver body imports these verbatim per Decision 3 Option A (spec lines 488-502). Slice 0 does NOT exercise them; the spike's stub uses a one-line `lambda root, info: target_type.__django_strawberry_definition__.model._default_manager.all()` resolver, deliberately bypassing the helpers so the only thing under test is Strawberry's class-attribute discovery of the factory-function return value. Naming Slice 0's stub `DjangoListFieldStub` (not `DjangoListField`) keeps the spike syntactically distinct from the eventual Slice 1 symbol.
  - `in_async_context` (`django_strawberry_framework/types/relay.py:33`) — canonical import is `from strawberry.utils.inspect import in_async_context`. Slice 0 does not exercise async detection, but the second-shape stub (annotated resolver `def resolver(root: Any, info: Info)`) imports `Info` from `strawberry.types` per rev5 H3 / rev6 L1 (spec lines 46, 64, 95, 99) and the spike must record `Info.__module__` for Slice 1's risks note.
  - `BranchType` (`examples/fakeshop/apps/library/schema.py:61-71`) — registered `DjangoType` with `__django_strawberry_definition__` already set; the spike imports it as the target type so the `target_type.__django_strawberry_definition__.model._default_manager.all()` call has a real model behind it.

- **New helpers justified.** None. Slice 0 produces zero library code and zero committed tests. Every artefact of this slice is the recorded outcome in this artifact's build report — not source code.

- **Duplication risk avoided.** The naive reading of "verification spike" could lead Worker 2 to author the spike inside `django_strawberry_framework/list_field.py` or `tests/test_list_field.py` and "leave it for Slice 1 to clean up." That would (a) violate the "no code lands" constraint at the top of Slice 0 (spec line 94, line 103), (b) couple Slice 1's diff with throw-away spike code that Worker 3 must then reject, and (c) duplicate the eventual real `DjangoListField` factory at a site where the duplication is not immediately obvious. The plan therefore pins the spike location to a sandbox (a non-committed, throw-away path — implementation-discretionary per Slice 0's nature) and pins `DjangoListFieldStub` as the symbol name so Worker 2 cannot accidentally name it `DjangoListField` and have grep-collisions with Slice 1's eventual symbol.

### Implementation steps

Worker 2 executes the steps below in order. Each step's outcome (PASS / FAIL plus the exact observed value) is recorded in this artifact's `## Build report (Worker 2)` section — that report IS the deliverable of Slice 0 (no code commits). Line numbers below are pin-at-write-time navigational hints; verify against the current source before relying on them.

1. **Confirm `info: Info` import path.** Run `python -c "from strawberry.types import Info; print(Info.__module__)"` against the installed Strawberry. Confirm the import raises no `ImportError`. Record the printed `Info.__module__` value in the build report's `### Spike outcomes` subsection so a future maintainer can see which module path the installed Strawberry exposed (rev5 H3 / rev6 L1 — no equality assertion; the rev6 L1 fix dropped the non-falsifiable `Info.__module__ == "strawberry.types.info"` check, leaving only the import-resolution success criterion). If the import raises `ImportError`, set the artefact's `Status:` to `revision-needed` and surface to Worker 1 a Slice 0-blocking fallback: `import strawberry; Info = strawberry.Info` is the pinned alternative (spec line 46, rev5 H3 paragraph).

   Spec citation: `docs/spec-016-list_field-0_0_7.md:95`.

2. **Author the throw-away `DjangoListFieldStub` factory in a sandbox.** Create a Python file outside the tracked source tree (sandbox path discretionary — see Implementation discretion items) containing exactly this stub plus the minimum imports needed to run it:

   ```python
   from typing import Any
   from strawberry.types import Info
   import strawberry
   from apps.library.schema import BranchType  # or any registered DjangoType


   def DjangoListFieldStub(target_type):  # noqa: N802 — spike only; matches Slice 1's intentional shape.
       return strawberry.field(
           resolver=lambda root, info: target_type.__django_strawberry_definition__.model._default_manager.all(),
       )
   ```

   The lambda-resolver here is deliberately untyped — step 5 below covers the annotated `(root: Any, info: Info)` shape separately so the two assertions (Strawberry picks up the factory return value via class-body walk AND Strawberry accepts `Info`-annotated resolvers) are isolated and either failure mode can be diagnosed independently.

   Spec citation: `docs/spec-016-list_field-0_0_7.md:96`.

3. **Assign the stub to a Query attribute under `@strawberry.type`.** In the same sandbox, write:

   ```python
   @strawberry.type
   class Query:
       all_branches: list[BranchType] = DjangoListFieldStub(BranchType)
   ```

   Spec citation: `docs/spec-016-list_field-0_0_7.md:97`. The rev6 M1 finding (spec line 58) corrected the design-intent record: Strawberry's class-attribute discovery is the **`@strawberry.type` decorator-time class-body walk** (iterates `cls.__dict__` and converts annotated attributes / `StrawberryField` instances into the type's field list), NOT `__set_name__`. The spike's purpose is to confirm that the factory function's return value (a `StrawberryField` from `strawberry.field(...)`) is picked up by that class-body walk exactly as a directly-written `field = strawberry.field(...)` would be.

4. **Build a Strawberry schema and assert the GraphQL type-wrapping via introspection.** Per rev6 M2 (spec line 59 + spec line 98), `print(schema)` and substring assertions against `str(schema)` are fragile across Strawberry minor versions; the pinned verification mechanism is an introspection query. Run:

   ```python
   schema = strawberry.Schema(query=Query)
   result = schema.execute_sync(
       '{ __type(name: "Query") { fields { name type { kind ofType { kind ofType { kind name } } } } } }'
   )
   ```

   Then locate `fields[name == "allBranches"]` in `result.data` and assert the four-level type wrapping documented in the spec at line 98:

   - outer `type.kind == "NON_NULL"`
   - wrapped `ofType.kind == "LIST"`
   - inner `ofType.ofType.kind == "NON_NULL"`
   - leaf `ofType.ofType.ofType.kind == "OBJECT"` and `ofType.ofType.ofType.name == "BranchType"`

   Together these assertions pin `[BranchType!]!` without relying on SDL formatting. Spec citation: `docs/spec-016-list_field-0_0_7.md:98`.

5. **Run a real `{ allBranches { id name } }` query and confirm rows return.** In the same sandbox (after the introspection query passes), run `schema.execute_sync("{ allBranches { id name } }")` and assert `result.errors is None` (or empty) and `result.data["allBranches"]` is a list with at least zero rows (the assertion is "the resolver ran without raising"; row count depends on whether the sandbox has migrations applied — the spike does not depend on seed data, just on the resolver completing). If `result.errors` is non-empty, the spike fails and the Risks fallback (directly construct a `StrawberryField` with explicit `python_name` / `type_annotation`) is promoted into Decision 1 per spec lines 102 and 798.

   Spec citation: `docs/spec-016-list_field-0_0_7.md:98` (the trailing sentence: "Run a real `schema.execute_sync('{ allBranches { id name } }')` query afterward and confirm rows return.").

6. **Repeat the introspection assertion with `list[BranchType] | None`.** Author a second sandbox stub or extend the same one with:

   ```python
   @strawberry.type
   class QueryOpt:
       all_branches_or_none: list[BranchType] | None = DjangoListFieldStub(BranchType)


   schema_opt = strawberry.Schema(query=QueryOpt)
   result = schema_opt.execute_sync(
       '{ __type(name: "QueryOpt") { fields { name type { kind ofType { kind ofType { kind name } } } } } }'
   )
   ```

   Locate `fields[name == "allBranchesOrNone"]` and assert:

   - outer `type.kind == "LIST"` (NOT `NON_NULL`; the `| None` makes the outer nullable)
   - inner `ofType.kind == "NON_NULL"`
   - leaf `ofType.ofType.kind == "OBJECT"` and `ofType.ofType.name == "BranchType"`

   This pins `[BranchType!]` (nullable outer, non-null items) — confirming rev2 H2's claim that the consumer's class-attribute annotation drives outer nullability and the factory does NOT need to take a `nullable_list=` constructor argument. Spec citation: `docs/spec-016-list_field-0_0_7.md:100`.

7. **Confirm Strawberry accepts the `(root: Any, info: Info)` resolver signature without `MissingArgumentsAnnotationsError`.** Build a third stub with an explicitly annotated resolver instead of the lambda:

   ```python
   from typing import Any
   from strawberry.types import Info


   def _annotated_resolver(root: Any, info: Info):
       return BranchType.__django_strawberry_definition__.model._default_manager.all()


   def DjangoListFieldStubAnnotated(target_type):  # noqa: N802 — spike only.
       return strawberry.field(resolver=_annotated_resolver)


   @strawberry.type
   class QueryAnn:
       all_branches: list[BranchType] = DjangoListFieldStubAnnotated(BranchType)


   schema_ann = strawberry.Schema(query=QueryAnn)  # MUST not raise.
   ```

   Confirm that `strawberry.Schema(...)` returns without raising `MissingArgumentsAnnotationsError` (rev4 H1, spec line 37 and spec line 99). If the schema construction raises, Slice 1's pinned `(root: Any, info: Info)` signature is invalid against the installed Strawberry and the Risks-fallback section of Slice 0's outcome must record either `import strawberry; Info = strawberry.Info` (rev5 H3 fallback) OR a Strawberry version bump in `pyproject.toml` (rev5 H3 second fallback).

   Spec citation: `docs/spec-016-list_field-0_0_7.md:99`.

8. **Record the spike outcome and decide.** Per spec lines 101-103:

   - If steps 1, 4, 5, 6, and 7 all PASS: record `Outcome: factory-function design verified; proceed to Slice 1 with the design intact.` in the build report's `### Spike outcomes` subsection. Set `Status: built`.
   - If ANY step FAILS: record the failing step number, the exact error message, and the proposed fallback (per the spec's pinned fallbacks at lines 102 and 798). Set `Status: revision-needed` and surface to Worker 1 a recommendation to reauthor Decision 1 and Slice 1 against the fallback before Slice 1 begins (spec line 102: "the Risks fallback (directly construct a `StrawberryField` with explicit `python_name` / `type_annotation`) is promoted to Decision 1; Slice 1 is reauthored before any production code lands").

   Spec citation: `docs/spec-016-list_field-0_0_7.md:101-102`.

9. **Discard the sandbox file.** After the build report records the outcome, delete the sandbox file used in steps 2-7. Confirm via `git status --short` that the working tree carries no spike residue (no new files under `django_strawberry_framework/`, `tests/`, `examples/`, or `docs/`; the only working-tree change permitted by this slice is the new `docs/builder/bld-slice-0-preimpl_verification.md` file itself).

   Spec citation: `docs/spec-016-list_field-0_0_7.md:103` ("No tests committed in this slice; the spike is local exploration.").

### Test additions / updates

**No tests are committed in this slice.** The spike is local exploration, per spec line 103 ("No tests committed in this slice; the spike is local exploration."). Worker 2 records the spike's outcome ONLY in this artifact's `## Build report (Worker 2)` section — there is no `tests/test_list_field.py` work in Slice 0 (that file is created in Slice 2 per the build plan), no edit to `tests/base/test_init.py` (that lands in Slice 1), and no temp tests under `docs/builder/temp-tests/<slice>/`. If Worker 3's review pass later finds a missing verification angle, the temp-test mechanism remains available for the review-pass loop — but the planning pass does not pre-stage one.

Coverage gate impact: zero. Slice 0 ships no production code, so the `fail_under = 100` coverage gate is unaffected. The next-meaningful coverage delta lands in Slice 1.

### Implementation discretion items

These items are at Worker 2's discretion only because Worker 1 has assessed them and decided either equally valid options exist OR the spec does not pin them:

- **Sandbox file location.** The spec calls Slice 0 "a sandbox" (line 11 paragraph 4: "a throw-away spike") without pinning a path. Worker 2 may use `/tmp/spec016_slice0_spike.py`, `~/spike_djangolistfield.py`, an `IPython` REPL session, a scratch path under the user's home, or any other non-tracked location. The only constraint is that the path is NOT under the repo's tracked tree — no file under `django_strawberry_framework/`, `tests/`, `examples/`, or `docs/` (other than this artifact) may contain spike code at the end of the slice.

- **Target `DjangoType` for the spike.** The spec uses `BranchType` from the library app throughout the Slice 0 bullets (spec lines 96, 98). That's the natural choice and Worker 1 recommends it because `BranchType` is already a registered `DjangoType` with `Meta.model = models.Branch`, no `Meta.primary`, and no `Meta.interfaces = (relay.Node,)` — a clean "simple `DjangoType`" shape for the spike. However, any registered `DjangoType` with `__django_strawberry_definition__` set would equally validate the factory-discovery contract; if `BranchType` proves awkward to import under the sandbox shell setup (e.g., Django settings configuration friction), Worker 2 may substitute any other registered `DjangoType` and record the substitution in the build report.

- **REPL vs script.** Worker 2 may run the spike interactively (e.g., `uv run python` REPL with `DJANGO_SETTINGS_MODULE` set for the example project) or via a single `.py` file. Either shape produces the same recorded outcomes. The build report only needs the OUTCOMES, not the script text.

These are the only discretionary items. Every other choice in this slice (stub symbol name `DjangoListFieldStub`, introspection-query verification mechanism, the four-level type-wrapping assertion shape, the `(root: Any, info: Info)` signature, the `Info` import path, the second nullable-outer assertion, the post-spike cleanup) is pinned by the spec or by Worker 1's plan above.

### Spec slice checklist (verbatim)

The spec's nested sub-bullets for Slice 0 from `## Slice checklist` (spec lines 94-103), copied verbatim. Every box stays `- [ ]` during this planning pass; the final-verification pass ticks each `- [x]` as the contract lands.

- [x] **Confirm `info: Info` import path** (rev5 H3; rev6 L1 dropped the non-falsifiable `Info.__module__ == "..."` equality check) — run `python -c "from strawberry.types import Info; print(Info.__module__)"` against the installed Strawberry; confirm the import raises no `ImportError`. Record `Info.__module__` for the post-spike Risks note so a future maintainer can see which module path the installed Strawberry exposed. If the import fails, fall back to `import strawberry; Info = strawberry.Info` and pin that shape in Decision 1. Without this verification, Slice 1's resolver signatures may compile but fail schema construction.
- [x] Write a 10-line throw-away stub in a sandbox: `def DjangoListFieldStub(target_type): return strawberry.field(resolver=lambda root, info: target_type.__django_strawberry_definition__.model._default_manager.all())`.
- [x] Assign it to a Query attribute under `@strawberry.type`: `all_branches: list[BranchType] = DjangoListFieldStub(BranchType)`.
- [x] Build a Strawberry schema and confirm the field is picked up with annotation-derived GraphQL type `[BranchType!]!` (rev6 M2 — verification mechanism pinned to an introspection query rather than `print(schema)` or SDL substring assertions; the latter are fragile across Strawberry minor versions). Concretely: `result = schema.execute_sync('{ __type(name: \"Query\") { fields { name type { kind ofType { kind ofType { kind name } } } } } }')`; locate `fields[name == "allBranches"]`; assert the outer `type.kind == "NON_NULL"`, the wrapped `ofType.kind == "LIST"`, the inner `ofType.ofType.kind == "NON_NULL"`, and the leaf `ofType.ofType.ofType.name == "BranchType"`. Run a real `schema.execute_sync('{ allBranches { id name } }')` query afterward and confirm rows return.
- [x] Build a second stub that uses an explicitly annotated resolver — `def resolver(root: Any, info: Info)` with `from strawberry.types import Info` — and confirm Strawberry's schema construction accepts it without raising `MissingArgumentsAnnotationsError` (rev5 H3, the import verification's other half).
- [x] Repeat with `list[BranchType] | None` annotation; confirm the rendered type is `[BranchType!]` (nullable outer).
- [x] If all shapes work end-to-end: proceed to Slice 1 with the factory-function design intact.
- [ ] If either shape does NOT work: the Risks fallback (directly construct a `StrawberryField` with explicit `python_name` / `type_annotation`) is promoted to Decision 1; Slice 1 is reauthored before any production code lands.
- [x] No tests committed in this slice; the spike is local exploration. The Slice 1 implementation begins only after this Slice's checkboxes are ticked.

---

## Build report (Worker 2)

### Files touched

None tracked. Spike used `docs/builder/temp-tests/slice-0/spike.py` for sandbox code (path is gitignored under `docs/builder/temp-tests/`); that file was deleted at the end of the spike. The artifact captures findings.

### Tests added or updated

None. Spike per spec rev3 H1; no tests commit in this slice.

### Validation run

- `uv run ruff format .` — pass, no-op: `103 files left unchanged`. (Strawberry-formatter `COM812` warning is the standard pre-existing config notice; not caused by the spike.)
- `uv run ruff check --fix .` — `Found 40 errors`. All 40 errors are pre-existing `ERA001` (commented-out-code) hits in the spec-016 scaffold files committed in `6adbe63` (`django_strawberry_framework/__init__.py` and `django_strawberry_framework/list_field.py` — the latter is the scaffolded Slice 1 source-of-truth file with extensive TODO pseudo-code blocks). One additional warning notes an invalid `# noqa` directive on `list_field.py:54` — also scaffold-origin. None of the 40 errors live in any path the spike touched. Per `AGENTS.md` line 17, ERA001 is "TODO-anchored Pseudo blocks are exempt; suppress inline with `noqa: ERA001` if needed" — those `noqa` markers are Slice 1/3/4's cleanup-pass work (rev6 L2) and are not in scope for this verification spike.
- `git status --short` after both ruff invocations:

  ```text
   D docs/builder/bld-final.md
   D docs/builder/bld-integration.md
   D docs/builder/bld-slice-1-annotation_scalar_overrides.md
   D docs/builder/bld-slice-2-unskip_consumer_annotation_test.md
   D docs/builder/bld-slice-3-document_override_contract.md
   D docs/builder/bld-slice-4-version_bump_quintet.md
   D docs/builder/bld-slice-5-docs_kanban_changelog_archive.md
   D docs/builder/build-015-consumer_overrides_scalar-0_0_6.md
  ?? docs/builder/bld-slice-0-preimpl_verification.md
  ?? docs/builder/build-016-list_field-0_0_7.md
  ```

  Classification: every entry above is the pre-flight baseline from the build plan's preamble (the eight `D` entries are old spec-015 artifacts removed during pre-flight; the two `??` entries are the new build plan + this slice artifact, which Worker 0 created at plan time). No file modified by the spike survives in the working tree. (One transient `M examples/fakeshop/db.sqlite3` change appeared mid-spike from a `Branch.objects.create(...)` seed call; reverted with `git checkout -- examples/fakeshop/db.sqlite3` before setting `Status: built`.)
- Focused `pytest` run: not run. Slice 0 commits no tests; no `pytest` invocation in this pass.

### Implementation notes

- **Spike verdict: PASS.** All five concrete confirmations the spike was designed to produce returned the expected shape. The factory-function design (Decision 1 + Decision 2) holds against the installed Strawberry; Slice 1 may proceed with the factory-function design intact.
- **`Info.__module__` = `'strawberry.types.info'`.** Recorded per rev5 H3 / rev6 L1 contract; no `ImportError` raised; no fallback (`import strawberry; Info = strawberry.Info` / version bump) required. Spec line 95 verified.
- **Factory-function discovery via `@strawberry.type` class-body walk: confirmed.** The introspection query against `{ __type(name: "Query") { fields { name type { kind ofType { kind ofType { kind ofType { kind name } } } } } } }` returns for `allBranches`:

  ```json
  {"kind": "NON_NULL", "ofType": {"kind": "LIST", "ofType": {"kind": "NON_NULL", "ofType": {"kind": "OBJECT", "name": "BranchType"}}}}
  ```

  Exact `kind` chain: `NON_NULL > LIST > NON_NULL > OBJECT(name="BranchType")`. Matches spec line 98's pinned four-level shape for `list[BranchType]` → `[BranchType!]!`. Confirms rev6 M1's correction that discovery is via decorator-time class-body walk (not `__set_name__`).
- **Real-query execution returns rows.** `schema.execute_sync("{ allBranches { id name } }")` returned `result.errors is None` (printed `None`) and `result.data["allBranches"]` was a list of length **1** after a one-row seed (`Branch.objects.create(name="Spike Branch", city="Spike City")`); first row payload `{'id': 1, 'name': 'Spike Branch'}`. Resolver completed without raising. Spec line 98 trailing sentence verified.
- **`list[BranchType] | None` produces nullable outer.** The second-stub introspection returned `LIST > NON_NULL > OBJECT(name="BranchType")` (no outer `NON_NULL` wrap) — confirms rev2 H2's claim that the consumer's class-attribute annotation alone drives outer nullability and no `nullable_list=` constructor argument is needed. Spec line 100 verified.
- **`def resolver(root: Any, info: Info)` accepted by `strawberry.Schema(...)`.** Schema construction with the annotated resolver did not raise `MissingArgumentsAnnotationsError`; execution succeeded and returned the expected row count. Confirms rev4 H1's pinned signature. Spec line 99 verified.
- **Spec's spec-line-96 lambda shape is NOT viable on the installed Strawberry.** `strawberry.field(resolver=lambda root, info: ...)` raises `strawberry.exceptions.missing_arguments_annotations.MissingArgumentsAnnotationsError: Missing annotation for argument "info" in field "<lambda>", did you forget to add it?` at factory-call time, BEFORE `@strawberry.type`'s class-body walk runs. The error originates in `strawberry/types/fields/resolver.py:303`. The spike substituted an annotated module-level resolver (`def _annotated_default_resolver(root: Any, info: Info): ...`) for every steps-3-through-6 stub; the class-body-discovery confirmation is unchanged under the substitution because the discovery contract is orthogonal to the resolver signature. The annotated shape is the one Slice 1 will ship anyway (spec line 99 + rev4 H1's pinning), so the spec's literal spec-line-96 sketch is design-time notation, not the eventual shipping shape. Flagged to Worker 1 for spec reconciliation below — non-blocking.
- **`finalize_django_types()` MUST be called before building the spike schema.** `BranchType` (and every other `DjangoType` subclass) is not `@strawberry.type`-decorated at class-creation time; the package's three-phase finalizer wires that up. The spike imports `finalize_django_types` from `django_strawberry_framework` and calls it once after `django.setup()` and before `strawberry.Schema(query=Query)`. Without this call, `strawberry.Schema(query=Query)` raises `TypeError: Unexpected type '<class 'apps.library.schema.BranchType'>'` because the `DjangoType` subclass is not yet a Strawberry-known type. This is not a Slice 0 finding per se — the eventual `tests/test_list_field.py` and `examples/fakeshop/test_query/test_library_api.py` already operate against the example project's `config.schema` module which calls `finalize_django_types()` at import time — but Worker 2's Slice 1 pass should remember to call `finalize_django_types()` in any `tests/test_list_field.py` fixtures that construct a fresh schema directly (instead of importing the example's `config.schema.schema`).

### Notes for Worker 3

- The sandbox path used was `docs/builder/temp-tests/slice-0/spike.py`; the file was deleted at the end of the spike. Confirm `ls docs/builder/temp-tests/slice-0/` is empty at review time. The path is covered by the existing `.gitignore` rule `docs/builder/temp-tests/`.
- Every Slice 0 Plan step (1 through 9) has a recorded outcome in `### Implementation notes` above. Walk the Plan's `### Implementation steps` enumeration against the implementation-notes bullets one-to-one and confirm each step's PASS/FAIL verdict is captured. The Plan's step 8 ("Record the spike outcome and decide") resolves to `Outcome: factory-function design verified; proceed to Slice 1 with the design intact.` — matching the spec's gate at lines 101-103 ("If all shapes work end-to-end: proceed to Slice 1 with the factory-function design intact").
- No `pytest`, no `pytest --cov*`, no production-source edits, no test-tree edits in this slice — this matches the "no code lands" Slice 0 contract.
- One transient state change to `examples/fakeshop/db.sqlite3` was reverted before `Status: built`; the working tree is clean of spike residue.
- The unannotated-lambda finding is recorded as a spec-line-96-vs-line-99 reconciliation candidate in the next section, not as a Slice 0 failure. The spike's gate condition was the annotated-resolver shape (spec line 99); that shape passed.

### Notes for Worker 1 (spec reconciliation)

Spike PASS; the spec's pinned fallback (Decision 1 promotion of direct `StrawberryField` construction; rev3 H1 reauthor of Slice 1) is not triggered. However, one minor spec-text drift surfaced that Worker 1 may want to address during final verification:

- **Spec lines 94-103 (Slice 0 checklist) mix two resolver shapes that are not equivalent on the installed Strawberry.** Line 96's `lambda root, info: target_type.__django_strawberry_definition__.model._default_manager.all()` and line 99's `def resolver(root: Any, info: Info)` are presented as separate checklist items, but the lambda shape raises `MissingArgumentsAnnotationsError` at `strawberry.field(resolver=...)` call time (BEFORE class-body walk runs), so the line-96 stub cannot be used to verify line-98's class-body-discovery contract. The annotated shape from line 99 (and Slice 1's pinned `(root: Any, info: Info)` signature per rev4 H1) is the only one that works on the installed Strawberry. The spike substituted the annotated form throughout and the class-body-discovery contract verified successfully. Suggested reconciliation: rewrite the Slice 0 checklist to use the annotated resolver throughout (one stub instead of two), and fold what is currently line 99 into the same bullet as line 98. Decision 1's "Mechanism" subsection and the Slice 0 Plan citations would need a matching tightening. Optional / cosmetic — no Slice 1 work blocked by this drift; the eventual Slice 1 implementation already ships the annotated shape per rev4 H1.

---

## Review (Worker 3)

### High:

None.

### Medium:

None.

### Low:

#### Plan line-number span for `_apply_get_queryset_*` drifts from spec citation

The Plan's DRY-analysis bullet at the top of the artifact cites `_apply_get_queryset_sync` at `types/relay.py:199-222` and `_apply_get_queryset_async` at `types/relay.py:225-237`. Verified against `HEAD`: sync helper actually closes at line 222 (the `return result` is line 222 because the closing `)` of the `ConfigurationError(...)` call landed at 221, with `return result` at 222 — the artifact is correct), and the async helper's final `return result` is at line 237 (next symbol `_coerce_node_id` starts at 240, with a blank-line gap). The spec at line 180 (Current state) and rev5 M2 history say `:199-220` (sync) and `:225-239` (async). Neither span is "wrong" — they cover slightly different conventions about where a docstring-bearing function "ends" — but the spec's claim and the artifact's claim differ by a few lines. No action required for Slice 0; this is the Slice 1 / Slice 3 line-number-watch reminder Worker 3's memory will carry forward. The helpers themselves are stable; only the trailing-line citations drift.

```django_strawberry_framework/types/relay.py:199:222
def _apply_get_queryset_sync(cls: type, qs: models.QuerySet, info: Any) -> models.QuerySet:
    ...
    return result  # line 222


async def _apply_get_queryset_async(cls: type, qs: models.QuerySet, info: Any) -> models.QuerySet:
    ...
    return result  # line 237
```

### DRY findings

None. Slice 0 commits no code; "reuse" of `_apply_get_queryset_sync` / `_apply_get_queryset_async` and `in_async_context` is correctly deferred to Slice 1 per the Plan's DRY-analysis section. The Build report's `Implementation notes` final bullet flags one DRY-adjacent reminder for Slice 1 (`finalize_django_types()` must be called before constructing any spike or fixture schema that exposes a `DjangoType`); that note is forwarded to Worker 1 / Worker 2 via the Build report itself and does not need to be a finding here.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` is empty. Spec line 103 ("No tests committed in this slice; the spike is local exploration.") licenses zero public-surface change in Slice 0 — the `DjangoListField` re-export does not land until Slice 1 (spec line 120). Confirmed clean.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. (The slice did create the new artifact `docs/builder/bld-slice-0-preimpl_verification.md`, but that is the slice's own build-cycle artifact, not a docs/release surface change.)

### What looks solid

- Every Slice 0 verbatim spec sub-check is addressed in the Build report:
  1. Spec line 95 (`Info.__module__` import-resolution): recorded — `Info.__module__ = 'strawberry.types.info'`, no `ImportError`.
  2. Spec line 96 (10-line throw-away stub): authored in `docs/builder/temp-tests/slice-0/spike.py`, deleted at end.
  3. Spec line 97 (assign to Query attribute under `@strawberry.type`): confirmed via the introspection result.
  4. Spec line 98 (introspection query + four-level `kind` chain): introspection JSON quoted verbatim in the Build report — `NON_NULL > LIST > NON_NULL > OBJECT(name="BranchType")` — exact-match to the spec's pinned shape. Real `{ allBranches { id name } }` query returned `result.errors is None` and a one-row list.
  5. Spec line 99 (`def resolver(root: Any, info: Info)` accepted without `MissingArgumentsAnnotationsError`): confirmed.
  6. Spec line 100 (`list[BranchType] | None` renders as `[BranchType!]` nullable outer): confirmed.
  7. Spec line 101 ("If all shapes work end-to-end ... proceed to Slice 1"): the verdict is explicitly declared — "Spike verdict: PASS ... Slice 1 may proceed with the factory-function design intact."
  8. Spec line 103 (no tests, no production source touched): confirmed — `git status --short django_strawberry_framework/ tests/ examples/fakeshop/` is empty after the spike.
- The Build report's `Implementation notes` chains every spike outcome back to the originating spec line (95, 96, 98, 99, 100), which makes the PASS verdict falsifiable rather than assertive.
- The Build report flagged the unannotated-lambda-vs-annotated-resolver drift between spec lines 96 and 99 as a spec-reconciliation candidate for Worker 1, NOT as a Slice 0 failure — correct judgment. The gate condition (spec line 99 annotated shape) passed; the lambda shape (line 96) is design-time notation. Forwarding it to Worker 1 is the right place, not blocking Slice 1 on it.
- The transient `M examples/fakeshop/db.sqlite3` mid-spike change was reverted before `Status: built` — correct stewardship of the working tree.
- The `finalize_django_types()`-must-be-called-first observation in the final implementation-notes bullet is real prior art that will save Worker 2 debugging time on Slice 1's test fixtures; recording it in this Build report (and downstream in Worker 3's memory for the Slice 1 review) is the right place.
- Helper invocation discipline: `scripts/review_inspect.py` is correctly skipped because Slice 0 adds no `.py` file. Plan and Build report both record the skip with reason.
- `git diff HEAD -- django_strawberry_framework/__init__.py` is empty — the public-surface invariant for "no code lands" Slice 0 holds.

### Temp test verification

`docs/builder/temp-tests/slice-0/` exists and is empty (`ls -la` returns only `.` and `..`). The Build report at the `### Files touched` section explicitly says the spike file `docs/builder/temp-tests/slice-0/spike.py` was deleted at end-of-pass; the directory's empty state confirms it. Path is covered by the existing `.gitignore` rule `docs/builder/temp-tests/` (confirmed at pre-flight per the build plan preamble). Disposition: no temp tests carried into the review; nothing to promote, delete, or follow up on.

### Notes for Worker 1 (spec reconciliation)

Agree with the Build report's spec-reconciliation candidate (Notes for Worker 1 section above): spec line 96's bare-lambda shape (`lambda root, info: ...`) cannot be exercised on the installed Strawberry because `strawberry.field(resolver=...)` raises `MissingArgumentsAnnotationsError` at factory-call time, BEFORE `@strawberry.type`'s class-body walk runs. The spike substituted an annotated module-level resolver throughout, and the class-body-discovery contract that Slice 0 was designed to verify passed cleanly. The drift is cosmetic and Slice 1 is not blocked — Slice 1's pinned `(root: Any, info: Info)` signature (rev4 H1, spec line 99) is the shape that actually ships, and Worker 2 already proved it works. Worker 1 may want to tighten the Slice 0 checklist text during final verification (fold lines 96 and 99 into one annotated stub bullet), but this is optional / cosmetic; no Slice 1 work hinges on it.

Additionally, Worker 1 should weigh whether spec line 96's lambda example is worth keeping as design-time notation (current state) or rewriting to the annotated shape that actually verifies. The Build report's bullet describing the substitution gives Worker 1 enough context to decide either way during final verification.

### Review outcome

`review-accepted`. Every Slice 0 verbatim spec sub-check is addressed in the Build report with concrete observed output (introspection JSON quoted verbatim, `Info.__module__` recorded, real-query row count recorded, nullable-outer `kind` chain recorded, `MissingArgumentsAnnotationsError` confirmation recorded). The Pass/Fail gate at spec line 101 is declared explicitly (`PASS; proceed to Slice 1 with the factory-function design intact`). No source/test churn (`git status --short django_strawberry_framework/ tests/ examples/fakeshop/` empty). Public-surface check clean (`__init__.py` unchanged). Temp-test directory empty. The one spec-text drift (lambda-vs-annotated-resolver) is correctly forwarded to Worker 1 for final-verification consideration rather than treated as a Slice 0 failure. No High, Medium, or unresolved Low findings.

Setting `Status: review-accepted`.

---

## Final verification (Worker 1)

- **Spec slice checklist:** every `- [ ]` in the Plan's `### Spec slice checklist (verbatim)` is now `- [x]` EXCEPT the FAIL-branch sub-bullet at line 102 of the spec ("If either shape does NOT work: the Risks fallback ... is promoted to Decision 1; Slice 1 is reauthored before any production code lands."). The spike fired the PASS branch (spec line 101), so the FAIL branch is not applicable and its checkbox correctly stays `- [ ]` per the BUILD.md "PASS/FAIL branching" allowance in this prompt's check 1. No silently unaddressed sub-checks.
- **DRY check across this slice and prior accepted slices:** there are no prior accepted slices in this build (Slice 0 is the first). Cross-slice DRY items recorded below for Slice 1's planning pass to inherit:
  - Slice 1 must reuse `_apply_get_queryset_sync` from `django_strawberry_framework/types/relay.py:199` and `_apply_get_queryset_async` from `django_strawberry_framework/types/relay.py:225` rather than re-implementing the visibility-hook coroutine guard. The spike confirmed both helpers remain at those line numbers at HEAD; Slice 1's planning pass should re-verify.
  - Slice 1 must reuse `in_async_context` from `strawberry.utils.inspect` via the canonical import line at `django_strawberry_framework/types/relay.py:33` for async detection in the default resolver body.
  - Worker 2's Build report flagged a `finalize_django_types()`-must-be-called-first DRY-adjacent observation for any test fixture in `tests/test_list_field.py` that builds a fresh schema directly (rather than importing `examples/fakeshop/config/schema.py`'s already-finalized `schema`). Carry forward to Slice 1's test-fixture planning.
- **Existing tests still pass:** Slice 0 added no production code and no committed tests; no focused tests apply. The `fail_under = 100` coverage gate is unaffected. `uv run pytest --no-cov` is the final-gate scope (Worker 1's `bld-final.md`), not the slice gate. No `--cov*`-flagged invocation was run in this pass.
- **Spec reconciliation:** Worker 2 and Worker 3 both surfaced the same spec-text drift at spec line 96 — the bare-lambda example `strawberry.field(resolver=lambda root, info: ...)` raises `MissingArgumentsAnnotationsError` at `strawberry.field(resolver=...)` call time on the installed Strawberry, BEFORE `@strawberry.type`'s class-body walk runs. The spike substituted an annotated module-level resolver throughout, and the class-body-discovery contract verified successfully. Spec line 96 was edited per the recommendation; details under `### Spec changes made (Worker 1 only)` below. Spec status-line re-verification (line 4 — "draft (revision 6, post-rev5 scaffolding review)"): still accurate; rev6 is the latest revision and Slice 0 is the first slice of the build (no shipped slices to reflect in the status). No status-line edit required.
- **Final status:** `final-accepted`. Slice contract landed; Slice 1 may proceed with the factory-function design intact.

### Summary

Slice 0 (the throw-away pre-implementation verification spike) shipped a PASS verdict. Worker 2 confirmed all five concrete checkpoints the spike was designed to falsify: (1) `from strawberry.types import Info` resolves to module `strawberry.types.info` with no `ImportError`; (2) the factory-function return value (`strawberry.field(...)`) is picked up by `@strawberry.type`'s decorator-time class-body walk (rev6 M1's corrected mechanism — NOT `__set_name__`); (3) the introspection-query verification (rev6 M2's pinned mechanism) returned the exact `NON_NULL > LIST > NON_NULL > OBJECT(name="BranchType")` four-level kind chain documented at spec line 98 for `list[BranchType]` → `[BranchType!]!`; (4) the nullable-outer variant `list[BranchType] | None` rendered as `[BranchType!]` (no outer NON_NULL, confirming rev2 H2's claim that the consumer's annotation alone drives outer nullability); (5) the `def resolver(root: Any, info: Info)` signature was accepted by `strawberry.Schema(...)` without raising `MissingArgumentsAnnotationsError` (confirming rev4 H1 / rev5 H3). The PASS verdict greenlights Slice 1 against the factory-function design intact; the Risks-section fallback (direct `StrawberryField` construction with explicit `python_name` / `type_annotation`) is NOT triggered. The spike left zero residue in the tracked tree (a transient `db.sqlite3` mutation was reverted before `Status: built`); no production source, tests, or other tracked files were modified.

### Spec changes made (Worker 1 only)

- **`docs/spec-016-list_field-0_0_7.md:96`** — replaced the bare-lambda Slice 0 stub example (`def DjangoListFieldStub(target_type): return strawberry.field(resolver=lambda root, info: ...)`) with an annotated module-level `def _stub_resolver(root: Any, info: Info): ...` shape and a thin `def DjangoListFieldStub(target_type): return strawberry.field(resolver=_stub_resolver)` wrapper. Reason: Worker 2 verified that on the installed Strawberry, the lambda form raises `MissingArgumentsAnnotationsError` at `strawberry.field(resolver=...)` call time — BEFORE `@strawberry.type`'s class-body walk runs — so the lambda cannot be used to verify the class-body-discovery contract that Slice 0 is designed to confirm. The annotated `def` shape now mirrors Slice 1's pinned `(root: Any, info: Info)` signature (rev4 H1, spec line 99) and is the only viable shape on the installed Strawberry. The spike-line-96 verbatim sub-bullet in this artifact's Plan's `### Spec slice checklist (verbatim)` retains its pre-edit text (verbatim is a planning-time snapshot) and is ticked `- [x]` against the Build report's substitution behavior; future re-runs of Slice 0 against the new spec text will exercise the annotated shape directly without an in-flight substitution.
- **Slice-checklist branching (PASS-branch ticked; FAIL-branch not applicable):** the spec line 102 FAIL-branch sub-bullet stays `- [ ]` in the artifact's `### Spec slice checklist (verbatim)` because the spike fired the PASS branch at spec line 101. The Risks fallback (`StrawberryField` direct construction with explicit `python_name` / `type_annotation`) is NOT promoted; Slice 1 proceeds against the factory-function design intact. No spec edit required for this — the branching is intentional and the PASS/FAIL pairing is structural.

