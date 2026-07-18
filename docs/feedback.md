# Adversarial review: optimizer improvement implementation

> **Status (2026-07-17): historical record — every finding below is RESOLVED at HEAD.**
> This fifth review was written against the pre-commit working tree. Its two P2 findings
> and the P3 shipped in the program's landing commits: the shared window-predicate
> signature boundary (`optimizer/lateral_fetch.py::window_predicate_signature`, gating
> both `_recognize_lateral_fetch` and
> `optimizer/single_parent_fetch.py::_fetch_single_parent_rows`), the
> `UniqueConstraint.opclasses` uninspectable gate plus
> `optimizer/nested_planner.py::_every_backend_supports_index_column_ordering`, and the
> `SINGLE_PARENT_FAST_PATH` public docs/config-contract tests. The present-tense prose
> below describes the reviewed snapshot, not the committed code.

## Executive summary

No P0 or P1 defect was found. The three findings from the previous review were addressed: ordinary
`Index` access methods are now classified conservatively, the indexing documentation describes
the expanded metadata inventory, and the recognizer/runtime-import rename sweep is complete (the
historical optimizer plan carries an explicit as-shipped correction for its preserved old name).

Two P2 defects and one P3 documentation/test-hygiene issue remain. The most important new finding
is shared by the lateral executor and the new single-parent fast path: both recognize any lookup
whose left side is a `Window` expression as an approved pagination predicate without proving its
operator, bound, annotation identity, or tree shape. A changed row-number bound is therefore
silently ignored while execution uses the original spec. The index fix also remains incomplete for
opclass-bearing `UniqueConstraint`s and for plans that can execute on a different database alias
from the alias consulted during planning.

## Findings

### P2 - The shared window recognizer accepts altered pagination predicates

[`django_strawberry_framework/optimizer/lateral_fetch.py::_is_window_qual`][lateral-fetch]
classifies a leaf as a window qual solely because its `lhs` is a `Window`. For a nested node it
checks only that the node is not negated and that every descendant passes the same broad test. It
does not prove:

- which `_dst_*` annotation the lookup targets;
- the lookup operator (`gt`, `lte`, or exact marker);
- the bound value;
- the expected `AND`/marker-`OR` tree;
- that every expected planned range lookup is present exactly once.

Both consumers then discard every accepted window qual and execute from their stored plan rather
than the fetch-time predicate:

- [`django_strawberry_framework/optimizer/lateral_fetch.py::_recognize_lateral_fetch`][lateral-fetch]
  returns the stored `LateralWindowSpec`, whose raw SQL is rendered from the original
  offset/limit/reverse values.
- [`django_strawberry_framework/optimizer/single_parent_fetch.py::_single_parent_where_ids`][single-parent]
  returns only the parent ids, after which
  [`django_strawberry_framework/optimizer/single_parent_fetch.py::_fetch_single_parent_rows`][single-parent]
  slices the pristine queryset with the original `fetch_limit`.

Read-only queryset probes reproduced the divergence. Starting from a planned `first: 2` window
whose WHERE contains `_dst_row_number <= 2`, appending
`filter(_dst_row_number__lte=1)` produced these results:

```text
single-parent recognized ids: [1]
fetch-time window lookups:     [('lte', 2), ('lte', 1)]
single-parent spec limit:      2
lateral recognized:            True
lateral spec limit:            2
```

The ORM-mutated query asks for at most one row, but either optimization still executes the stored
two-row page. This input is not expected from normal Django prefetch today, but both implementations
explicitly promise to fail closed on consumer mutation or Django-internals drift. The recognizer is
the safety boundary that makes replacing the ORM query with different execution legal, so a
structural “some Window lookup” test is insufficient.

Create one normalized window-predicate signature shared by both executors. It should encode the
annotation name, lookup, normalized RHS, connector, negation, nesting, and required multiplicity;
derive the expected signature from the same `WindowRangePlan` that renders the ORM and lateral
ranges. An alternative is to capture the exact planned range tree when the already-windowed
queryset is wrapped, then compare a normalized fetch-time range tree to it. In either design,
parent/visibility/keyset residues remain separate and every missing, changed, duplicated, or extra
window lookup must downgrade to the ORM window. Add tests for changed upper/lower bounds, a removed
bound, an extra bound, the wrong `_dst_*` annotation, reversed ranges, and marker `OR` shape in both
the lateral and single-parent suites.

### P2 - Index capability normalization still has an opclass and alias-early escape

The access-method fix in
[`django_strawberry_framework/optimizer/nested_planner.py::_index_leading_terms`][nested-planner]
correctly admits only exact `models.Index`/PostgreSQL `BTreeIndex` types and degrades non-default
`Index.opclasses` to unknown. However,
[`django_strawberry_framework/optimizer/nested_planner.py::_model_index_shapes`][nested-planner]
handles field-based `UniqueConstraint` entries through `_plain_field_terms` without checking
`constraint.opclasses`. An otherwise matching unique constraint with a non-default opclass is
therefore still classified as an ordinary ascending B-tree.

A targeted metadata probe created this constraint:

```python
models.UniqueConstraint(
    fields=["parent", "title", "id"],
    name="probe_uc_opclass",
    opclasses=["int4_ops", "varchar_pattern_ops", "int4_ops"],
)
```

For `(parent_id) + ORDER BY title, id`, `_index_coverage(...)` returned `"covered"`. That
contradicts both the fail-soft policy and [the README][docs-readme], which now promises that a
non-default opclass leaves coverage unknown.

The backend-direction correction is also alias-early.
[`django_strawberry_framework/optimizer/nested_planner.py::_supports_index_column_ordering`][nested-planner]
calls `router.db_for_read(model)` with no parent-instance hint and has no explicit queryset alias.
Nested plans are intentionally backend-neutral and can later be cloned onto the parent prefetch's
actual `.using(...)` alias. A divergent router can therefore return a direction-capable default
database during planning while the same cached plan executes on a shard without
`supports_index_column_ordering`; a descending metadata term is then falsely trusted as physical
DESC. This repeats the alias-early class of error already removed from GenericRelation planning.

Move every represented index source through one capability-normalization boundary rather than
letting `Index`, `UniqueConstraint`, `unique_together`, and field-level indexes make independent
claims. Reject non-default `UniqueConstraint.opclasses` as unknown. For backend-specific direction,
do not consult one unhinted route and treat it as universal: either carry a guaranteed execution
alias in a cache-safe way, or claim descending coverage only when every alias on which the cached
plan may execute supports it; otherwise remain unknown. Add a unique-constraint opclass regression
and a divergent-router test where the no-hint planning alias and parent-instance fetch alias expose
different direction capabilities.

### P3 - The default-on single-parent fast path has no public documentation

The new optimization and its consumer setting are documented thoroughly in internal source and
[`feedback2.md`][feedback2], but not in the public documentation. Repository search finds
`SINGLE_PARENT_FAST_PATH` only in configuration source and tests; it is absent from the root
README, [the package README][docs-readme], `TODAY.md`, and `docs/GLOSSARY.md`.

That omission matters because the feature is enabled by default and replaces the window query at
runtime. Consumers need to know:

- the eligible shape: one parent id, direct FK, count-free bounded first page;
- that it uses a plain filtered `LIMIT`, synthesizes row numbers, and falls back to the existing
  window on every refusal;
- which shapes remain windowed (counted/reversed/offset/keyset-seek, M2M/generic, visibility or
  other unrecognized predicates);
- that `DJANGO_STRAWBERRY_FRAMEWORK["SINGLE_PARENT_FAST_PATH"] = False` disables it at fetch time;
- how it composes with explicit `windowed`, `lateral`, and `auto` strategies, including the fact
  that a lateral plan that downgrades through `WINDOWED_STRATEGY` can still receive this wrapper.

Add the setting and behavior to the public optimizer documentation and glossary rather than
leaving a default-on execution change discoverable only from source. The configuration reader
also deserves the normal direct setting-contract tests (default, explicit false, live settings
reload, and the intended invalid-value policy), in addition to the current execution-level toggle
tests.

One small test-hygiene cleanup belongs with that work:
[`tests/optimizer/test_single_parent_fetch.py::test_fast_path_accepts_a_duplicated_single_parent_id`][single-parent-tests]
calls `_seed_shelf(["t1", "t2", "t3"])` twice and immediately overwrites the first result. The
unused first parent does not strengthen the duplicate-id assertion; it only adds unrelated rows
and obscures that the test passes the same parent object twice. Remove the first seed call.

## Previous findings verified as resolved

- PostgreSQL GIN, GiST, hash, BRIN, and SP-GiST indexes, custom `Index` subclasses, expression and
  partial indexes, and non-default `Index.opclasses` now degrade to unknown; exact
  `models.Index`/`BTreeIndex` shapes remain inspectable. The remaining `UniqueConstraint` escape is
  the narrower finding above.
- User-facing and source documentation now describes `Meta.indexes`, field-based
  `UniqueConstraint`, `unique_together`, and field-level primary-key/unique/`db_index` inventory,
  and correctly calls only database-only indexes invisible.
- `_recognize_lateral_fetch` references replaced the removed `_extract_parent_ids` name in
  `feedback2.md` and both DRY reports. The completed optimizer plan explicitly marks its preserved
  historical references as superseded.
- `StrategySelection` now documents the real runtime import from `hints.py`; runtime
  `typing.get_type_hints(OptimizerHint)` remains resolvable.

## DRY and architecture assessment

The new single-parent implementation reuses the existing strategy floor, `WindowRangePlan`,
parent-id matcher, and deduplicator rather than reimplementing them. That is the right dependency
direction. The remaining window-recognition defect is also a DRY opportunity: strengthening one
shared predicate-signature owner should protect both lateral raw SQL and the single-parent re-query.
Likewise, the index issue should be fixed in one capability descriptor consumed by every metadata
source, not with another constraint-only conditional. No other material production duplication was
found in this pass.

## Verification performed

This pass re-reviewed every previous finding, the corrected index inventory and documentation, and
the newly landed single-parent fast path across production code, package tests, live HTTP tests,
and PostgreSQL parity coverage. `git diff --check` was used during review. Targeted read-only Django
probes reproduced the `UniqueConstraint.opclasses` false-`covered` result and demonstrated that
both window recognizers accept an appended conflicting row-number bound. Per repository
instruction, pytest and coverage were not run. Ruff formatting and lint were run after replacing
this document.

<!-- LINK DEFINITIONS -->

<!-- Root -->

[feedback2]: ../feedback2.md

<!-- docs/ -->

[docs-readme]: README.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

[lateral-fetch]: ../django_strawberry_framework/optimizer/lateral_fetch.py
[nested-planner]: ../django_strawberry_framework/optimizer/nested_planner.py
[single-parent]: ../django_strawberry_framework/optimizer/single_parent_fetch.py

<!-- tests/ -->

[single-parent-tests]: ../tests/optimizer/test_single_parent_fetch.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
