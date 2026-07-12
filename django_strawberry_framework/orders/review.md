# Pre-BETA review: orders/

Scope: Meta-driven ordering -- `base.py`, `factories.py`, `inputs.py` (order
input generation), `sets.py` (`OrderSet` apply, related-field ordering).

Method: logic read of the `_apply_orderings` body in the real `sets.py` plus the
diffs since `0.0.13` (this cycle split `apply_sync`/`apply_async` over a shared
`_apply_orderings` tail, added `Min`/`Max` aggregation for to-many ordering, and
routed input generation through the shared `emit_set_input_field_triples`).
Coverage here is lighter than the filters review -- orders is structurally the
sibling of filters (both are "sidecar sets" bound identically by
`types/finalizer.py::_bind_sidecar_sets`), so treat the deeper filters findings
as the shared-shape baseline. The initial review was read-only; the hardening
pass added the acceptance coverage below without invoking pytest.

Bottom line: the important correctness property -- ordering a parent by a
to-many related field without exploding rows -- is handled via row-preserving
`Min`/`Max` aggregate annotations. No P0 or P1 found in what was read. Both P2
items below are resolved: the connection concern was reconciled against the
actual root-vs-nested pipelines and pinned over live HTTP in both database
tiers, and the null/omitted semantics are now documented as one no-op contract.

## P0 -- correctness suspicions

None found.

## P1 -- fix before BETA

None found in the read surface. The aggregate-interaction question below is
resolved against the actual connection-routing contract.

## P2 -- polish / hardening

### RESOLVED -- `sets.py::_apply_orderings` and connection pagination
The suspected aggregate/window stack is not a shipped query shape. A root
`DjangoConnectionField` applies the grouped `Min`/`Max` queryset and then
cursor-slices it directly; the optimizer's `_dst_row_number` window is for
nested relation connections. A nested connection carrying `orderBy:` is
deliberately not window/lateral planned and runs the per-parent pipeline, so
the aggregate never sits below that window either.

The live library acceptance test now orders the root Genre connection by the
reverse-M2M `books.title` path, fetches the first and continuation pages, and
asserts the exact node partition, `totalCount`, `hasNextPage`, no duplicates or
missing nodes, and the executed `MIN` + `GROUP BY` / no-row-number SQL shape.
The same test runs in the default SQLite suite and the PostgreSQL CI tier.

### RESOLVED -- empty/`None` direction semantics
An omitted order field and a field supplied with a GraphQL `null` direction
have identical semantics: neither contributes an ordering term, neither fires
that field's active-input-only permission gate, and a wholly term-less input
returns the queryset with its existing order unchanged. The generated input
normalizer, apply tail, public guide, and canonical glossary now state this
contract; the existing live HTTP test pins both `orderBy: []` and
`orderBy: [{ name: null }]`.

## API & consistency notes

- Orders and filters are bound by the same `_bind_sidecar_sets` machinery and
  share the orphan-detection / owner-mismatch / lazy-expansion error paths.
  Any error-message or validation change on one side should be mirrored on the
  other so the two stay symmetric (this is a recurring theme -- they are
  deliberately siblings).
- Permission checks run in both `apply_sync` and `apply_async` before the
  orderings are applied (`_run_permission_checks`), matching the filters side.

## Verified sound (do not re-flag)

- To-many ordering uses `Min`/`Max` aggregate annotations rather than a naive
  JOIN order, so ordering a parent by a related field does not multiply parent
  rows (`sets.py::_apply_orderings`).
- `apply_sync`/`apply_async` share the `_apply_orderings` tail so the two colors
  cannot drift in how they parse or apply orderings; the async color wraps the
  blocking work in a sync boundary.
- Input generation was unified onto `emit_set_input_field_triples` /
  `optional_field_kwargs`, removing the previously duplicated per-side field-spec
  assembly.

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
