# Review - spec-035 implementation

Reviewed the current `DONE-035` implementation against
`docs/spec-035-optimizer_hardening-0_0_10.md`, the optimizer/resolver code paths,
the new tests, and the generated docs. I did not find a production-code blocker in
the G2 gate threading itself: `django_strawberry_framework/optimizer/walker.py::plan_optimizations`
derives the operation gate once and threads it through the scalar writer,
relation connector writer, prefetch connector writer, and scalar-only connection
window writer. The FK-id elision fallback in
`django_strawberry_framework/types/resolvers.py::_build_fk_id_stub` also addresses
the consumer-`.only()` hazard at the right layer.

The remaining issues are source-of-truth/documentation correctness and test
depth. The docs are not just cosmetic here: this project treats specs, generated
Kanban output, glossary links, and build artifacts as navigational source for the
next implementer.

## Findings

### P1 - The canonical spec still describes G2 and the doc wrap as unfinished

The implementation and generated board now say card 035 is done, but the spec
file still reads like an in-progress design. Examples:

- `docs/spec-035-optimizer_hardening-0_0_10.md #"Status: G1 shipped"` says
  "G2 + the doc wrap remain" and "Slice 2 ... is the only functional build
  remaining."
- `docs/spec-035-optimizer_hardening-0_0_10.md #"Each top-level item maps"` says
  Slices 2 and 4 are unticked / not started.
- `docs/spec-035-optimizer_hardening-0_0_10.md #"G1 has since been closed"` says
  "G2 and G3 remain."
- `docs/spec-035-optimizer_hardening-0_0_10.md #"grep -rn \"OperationType\""` says
  `OperationType` returns nothing, which is now false because
  `django_strawberry_framework/optimizer/walker.py::_enable_only_for_operation`
  imports and uses it.

This is a real source-of-truth problem. A new developer reading the spec would
believe the G2 runtime work is still pending, while the code and generated board
say it shipped. It also undermines future review because the "Current state" and
DoD sections no longer match the checkout.

Required fix: add a final implementation revision to the spec and update the
status/current-state/checklist/DoD wording to the completed state: G1 shipped in
`d1dea2fd`, G2 shipped in this build, Slice 4 completed, G3 deferred. The
expected-delta/current-grep language should be rewritten or removed rather than
left as stale pre-build evidence. Re-run
`uv run python scripts/check_spec_glossary.py --spec docs/spec-035-optimizer_hardening-0_0_10.md`
afterward.

### P1 - The generated Kanban card points to a non-existent spec and contains stale card text

`KANBAN.md #"Spec:"` links `DONE-035-0.0.10` to
`docs/SPECS/spec-035-optimizer_hardening-0_0_10.md`, but that file is not present.
The live spec remains at `docs/spec-035-optimizer_hardening-0_0_10.md`.

That is not consistent with the repository rule in `AGENTS.md`: completed specs
stay at `docs/spec-NNN-...md` until the next spec author runs the batched
`docs/SPECS/NEXT.md` archive sweep, which moves prior specs and rewrites
cross-references in the same pass. Moving the DB-backed `SpecDoc.url` ahead of
the file move creates a broken public link in the board.

The same generated card also still carries pre-implementation wording:

- `KANBAN.md #"Status: Needs spec"` renders a DONE card as needing a spec.
- `KANBAN.md #"G2 open decision"` still says the FK-id elision decision is open,
  even though the spec and code resolved it with the loaded-check in
  `django_strawberry_framework/types/resolvers.py::_build_fk_id_stub`.
- `KANBAN.md #"G3 - fragment type-condition narrowing"` still describes G3 as a
  shipping implementation and later says "G3 closes" the silent-N+1 class,
  despite the spec deferring all G3 runtime code.
- `KANBAN.md #"Package files"` omits
  `django_strawberry_framework/types/resolvers.py` and
  `tests/types/test_resolvers.py`, which are where Decision 5 actually landed.

Required fix: update the Kanban DB rows, then regenerate `KANBAN.md` and
`KANBAN.html`; do not hand-edit the rendered files. Either keep the spec URL on
`docs/spec-035-optimizer_hardening-0_0_10.md` until the real archive sweep, or
perform the archive move and all reference rewrites in the same change. Also
rewrite the DONE card body to match the final spec: G1 + G2 shipped, G3 deferred,
FK-id decision resolved, resolver file/test included.

### P2 - G2 lacks a real GraphQL mutation execution test

The new G2 tests in `tests/optimizer/test_walker.py` do a good job proving the
walker behavior with synthetic `OperationType.MUTATION` / `OperationType.SUBSCRIPTION`
info objects. `tests/optimizer/test_extension.py::test_query_and_mutation_plans_coexist_distinct_keys`
also proves the printed AST cache-key separation.

What is still missing is one actual Strawberry execution where a `mutation`
root field returns a queryset and the installed `DjangoOptimizerExtension`
receives the real `info.operation.operation` object from the GraphQL runtime.
Without that, the most important integration seam for G2 is inferred from a
test double. A mismatch in Strawberry/graphql-core `Info` shape, enum identity,
or extension handoff would not be caught.

Required fix: add an in-process package test in
`tests/optimizer/test_extension.py` that defines a temporary `Mutation` field
returning `Item.objects.all()`, executes a real `mutation { ... }`, and asserts
the published plan has empty `only_fields` while `select_related` and
`prefetch_related` survive for relation selections. This belongs in `tests/`
rather than `examples/fakeshop/test_query/` because the current fakeshop schema
has no mutation surface; the first card that adds one should add the live HTTP
acceptance test then.

### P2 - The FK-id deferred-column guard is tested with doubles, not a real deferred model instance

`tests/types/test_resolvers.py::test_fk_id_elision_falls_back_when_consumer_only_defers_fk`
is directionally correct and asserts the right contract: do not read the deferred
FK column, force strictness visibility, and fall through to normal relation
resolution under `warn`.

The subtle dependency is Django's actual deferred-field bookkeeping. The
implementation relies on `root.get_deferred_fields()` containing
`field_meta.attname` and the attname being absent from `root.__dict__`.
The current test double simulates that shape, but it does not prove that a real
`Item.objects.only("name")` instance has the exact shape the guard expects.

Required fix: add a small `@pytest.mark.django_db` test in
`tests/types/test_resolvers.py` using a real `Item` loaded via
`Item.objects.only("name").get(...)`. Assert `category_id` is deferred, then run
the generated relation resolver with both FK-id-elision and planned sentinels
present under strictness `raise` or `warn`. This pins the Django contract the
guard depends on without needing a live mutation surface.

## Lower-Risk Notes

- `docs/builder/bld-final.md #"Spec changes made"` records that the stale spec
  status line is still accurate. I disagree with that final-verification
  conclusion for the reasons above; update the artifact or record a correction
  if these build artifacts remain committed for the active cycle.
- The build-artifact reset that removed the prior 034 `docs/builder/build-*` and
  `docs/builder/bld-*` files appears consistent with
  `docs/builder/BUILD.md` pre-flight rules; I would not treat that deletion as a
  defect.
- `uv run python scripts/check_spec_glossary.py --spec docs/spec-035-optimizer_hardening-0_0_10.md`
  currently passes (`OK: 23 terms`), so the glossary-term inventory is not the
  problem. The problem is stale completion state and broken/generated links.
