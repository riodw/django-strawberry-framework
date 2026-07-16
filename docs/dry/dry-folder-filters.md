# DRY review: folder `django_strawberry_framework/filters/`

Status: verified

## System trace

`filters/` is the six-layer filtering component (spec-027): declarative
`FilterSet` classes become GraphQL `filter:` arguments through finalize-time
input materialization and the `apply_sync` / `apply_async` pipeline.

Folder shape after the five verified file reviews:

- `__init__.py` — public re-exports + Decision-11 `filter_input_type` + helper
  ledger (`_helper_referenced_filtersets`, clear owner
  `filters.helper_references`).
- `base.py` — filter primitives (TypedFilter family, GlobalID*, RelatedFilter,
  IntegerIn/Range routing filters) and decode/validate helpers.
- `inputs.py` — Decision-9 namespace, LOOKUP / logic-key vocabulary, converter
  pair, field/logic builders, materialize + `clear_filter_input_namespace`
  (clear owner `filters.input_namespace`, `before_bind=True`).
- `factories.py` — Layer-5 BFS (`FilterArgumentsFactory`) + unconsumed Layer-6
  dynamic-FilterSet cache (`get_filterset_class` / `_make_hashable`).
- `sets.py` — `FilterSet` / metaclass, expansion, Relay-vs-scalar routing,
  normalize + apply + related-visibility + permission recursion.

Connected behavior re-traced for this folder pass (not inherited as proven):
`orders/` Layer-5 twin + deferred Layer-6 TODO; `sets_mixins` /
`utils/inputs.py` / `utils/input_values.py` / `utils/permissions.py` /
`utils/querysets.py::run_in_one_sync_boundary` / `utils/relations.py`;
finalizer phase 2.5 bind + orphan check; live fakeshop filter queries under
`examples/fakeshop/test_query/` and `apps/*/filters.py` + `filter_input_type`
resolver sites.

Folder-level axes examined: duplicated policy across modules, state ownership
(helper ledger vs input-namespace clear vs Layer-6 cache), competing path /
owner-resolution helpers, public export flavor vs `orders/`, lifecycle work
repeated at several phases.

## Verification

- Item-scoped baseline `4f04e22345b734cd696260eac98947cb28c44241`: working
  tree matched baseline for `filters/` at pass start (concurrent WIP vs HEAD
  already present — empty-list / lookups / logic-keys / `run_in_one_sync_boundary`
  consolidations from file passes). Concurrent dirty paths outside this item
  (`docs/GLOSSARY.md`, `docs/dry/dry-0_0_13.md`, other dry artifacts,
  `examples/fakeshop/db.sqlite3`, auth/permissions/orders/mutations WIP) left
  untouched. Plan checkbox not edited.
- Re-read all five filters sources end-to-end. Grepped package for
  `get_model_field`, `_model_field_for_filter`, `_make_hashable`,
  `register_subsystem_clear` owners under `filters.`, and
  `primary_for(...) or registry.get`.
- Compared `orders/` as connected evidence: Layer-5 factory already shares
  `GeneratedInputArgumentsFactory`; Decision-11 helpers already share
  `build_lazy_input_annotation`; Layer 6 exists only as a TODO on the order
  side. File-pass deferrals on filters↔orders packaging and Layer-6 hashing
  re-proved from source (below).
- Confirmed `_model_field_for_filter` re-implemented the same `__`-path walk
  that `django_filters.utils.get_model_field` already supplies to
  `IntegerInFilter` (`base.py`) and `FilterSet.get_fields` (`sets.py`) —
  a folder-visible competing helper the inputs file pass compared only to
  `utils/relations` (different return contract) and missed.
- Confirmed ledger comment above `_materialized_names` still claimed clear
  `delattr`s module globals while `clear_filter_input_namespace` /
  `clear_generated_input_namespace` deliberately park classes — lifecycle
  ownership prose drift inside the folder.
- Focused proof: four package tests for `_model_field_for_filter` (including
  new related-path walk) passed under
  `uv run pytest tests/filters/test_inputs.py::test_model_field_for_filter_*`
  (coverage gate expected-fail on focused run). No full pytest.

## Opportunities

### 1. Model-field path resolution (accepted)

- **Repeated responsibility:** resolve a filter's `field_name` (possibly
  `__`-separated) to the terminal Django model field, or `None` on a missing
  hop.
- **Sites:** `filters/inputs.py::_model_field_for_filter` (custom walk);
  `filters/base.py::IntegerInFilter.filter` (`get_model_field`);
  `filters/sets.py::FilterSet.get_fields` (`get_model_field`).
- **Evidence:** all three encode django-filter's relation-path walk; unknown
  names return `None`; nested paths yield the terminal field. Drift would
  mistype a nested leaf annotation while runtime `__in` / `"__all__"`
  expansion still resolve correctly (or the reverse).
- **Owner:** `django_filters.utils.get_model_field` — already the runtime /
  metaclass owner inside this folder; inputs keeps only the filterset /
  `field_name` guards.
- **Consolidation:** `_model_field_for_filter` delegates to `get_model_field`;
  remove the private walk. Ledger comment for `_materialized_names` aligned
  with the park-not-`delattr` clear contract.
- **Proof:** existing
  `tests/filters/test_inputs.py::test_model_field_for_filter_*` plus
  `test_model_field_for_filter_walks_related_path`. Live GraphQL filter
  annotation shapes already covered under `examples/fakeshop/test_query/`
  (library / kanban / scalars); private helper change is not newly earnable
  over HTTP.
- **Risks / non-goals:** do not fold into `utils/relations` path walkers
  (fan-out / relation-kind contracts); do not change public converter
  signatures.

### Rejected / kept separate

1. **Extract `_make_hashable` / `_make_cache_key` to `utils/inputs.py` now.**
   One concrete Layer-6 site; `orders/factories.py` only reserves symbols in a
   standing deferred Non-goal. Premature shared owner. Defer-with-trigger:
   when orders ships a real `get_orderset_class` + `_dynamic_orderset_cache`,
   or the project pass revisits cross-family packaging. Re-proved.

2. **`make_helper_ledger` / further collapse of Decision-9 family wrappers
   with `orders/`.** Substrate already shared (`build_lazy_input_annotation`,
   materialize/clear, BFS base). Remaining mirror is per-subsystem namespace
   + ledger ownership. Cross-family packaging needs orders as co-owner —
   recorded for project pass. Not this folder's solo consolidation.

3. **Unify `_resolve_relation_target_type` with `_target_type_for_related_filter`.**
   Both fall back via `registry.primary_for(...) or registry.get(...)`, but
   primary paths differ: owner `related_target_for(field_name)` for
   Relay-vs-scalar class selection vs child filterset `_owner_definition.origin`
   for visibility `get_queryset` scoping. Shared one-liner fallback is not one
   responsibility; extracting a mode-flagged helper would obscure the two
   change axes. Rejected.

4. **`_target_definition_for` (base GlobalID decode) vs sets owner routing.**
   Runtime filter instance walks `parent._owner_definition`; class-level
   routing uses `cls._owner_definition` / related_target_for for filter *class*
   selection. Same binding seam, different consumers and phases. Kept
   separate.

5. **Dual clear owners (`filters.helper_references` vs
   `filters.input_namespace`).** Intentional: orphan-check ledger vs rebuild
   bookkeeping (`before_bind=True`). Layer-6 dynamic cache has no clear hook
   by documented design (model identity in keys). Not consolidation
   candidates.

6. **Public flavor vs `orders/`.** `FilterSetMetaclass` in `__all__`;
   `FilterArgumentsFactory` / `get_filterset_class` stay advanced imports —
   matches order twin. `Filter` re-export shadowing is documented surface
   continuity. Consistent.

7. **`_unwrap_enum_member` vs `write_values.raw_choice_value`.** Identical
   one-liner; write-flavor scoping intentional. Project-pass neutral util
   question, not folder ownership.

## Judgment

Folder ownership is already layered correctly after the 0.0.9 substrate
extraction and the file-pass consolidations sitting in the concurrent WIP.
The one cross-module policy still spelled twice inside `filters/` — model-field
path resolution — now delegates to the same `get_model_field` owner
`base.py` / `sets.py` already use. Filters↔orders Layer-6 hashing and
Decision-9 packaging remain deferred for a co-owned project pass. Ready for
Worker 2.

## Implementation (Worker 1)

- **Owner chosen:** `django_filters.utils.get_model_field` via
  `filters/inputs.py::_model_field_for_filter`.
- **Migrated:** custom `__`-walk in `_model_field_for_filter` →
  `get_model_field(model, field_name)`; `_materialized_names` ledger comment
  updated to park-not-`delattr` contract.
- **Tests:** `test_model_field_for_filter_walks_related_path` added;
  unknown-name test docstring updated. Existing none-model / none-field-name /
  unknown-name tests kept.
- **Kept separate:** Layer-6 hashing; filters↔orders Decision-9 wrappers;
  the two DjangoType resolution paths in `sets.py`; GlobalID
  `_target_definition_for`; dual clear ledgers; enum unwrap vs write path.
- **Validation:** `uv run ruff format` + `uv run ruff check --fix` on edited
  paths; focused `_model_field_for_filter_*` tests — 4 passed.
- **Changelog:** no — internal path-walk ownership; no public API change.
- **Concurrent paths preserved:** edits only in `filters/inputs.py`,
  `tests/filters/test_inputs.py`, and this artifact. Pre-existing WIP under
  `filters/{__init__,base,sets}.py` and other packages left alone. Plan
  checkbox not touched.

## Independent verification (Worker 2)

Re-traced `filters/` as one component (all five modules + Decision-11
helper, Layer-5/6 factories, dual clear owners, sets owner-routing /
visibility paths) against connected `orders/`, `utils/inputs.py`,
`utils/relations.py`, and `utils/write_values.py`. Did not treat Worker 1
findings as proven.

**Challenged Opportunity 1 (`get_model_field` consolidation).** Confirmed
shared responsibility: resolve `__`-separated `field_name` to the terminal
model field or `None`. Item-scoped diff only migrates the custom walk in
`inputs.py::_model_field_for_filter`; `base.py::IntegerInFilter.filter` and
`sets.py::FilterSet.get_fields` already call `django_filters.utils.get_model_field`.
Executable parity check (`PYTHONPATH=examples/fakeshop`) against the old
`is_relation` / `related_model` walk on forward FK, reverse FK, M2M, nested
paths, and missing hops — identical objects (e.g. `Shelf.branch__name`,
`Shelf.books__title`, `Book.genres__name`, `Book.shelf__branch__name`).
Wrapper correctly retains filterset / `field_name` guards (converter receives
a filter instance). Known micro-divergence (django-filter raises
`RuntimeError` on unresolved lazy relations; old walk soft-failed to `None`)
aligns inputs with the folder's established django-filter contract rather
than preserving a softer private walk — acceptable. Not folded into
`utils/relations.py::path_traverses_to_many` (fan-out boolean, different
contract). Focused proof re-run:
`test_model_field_for_filter_*` — 4 passed (`--no-cov`).

**Clear-lifecycle comment.** `_materialized_names` ledger prose now matches
`clear_filter_input_namespace` (park classes; reset ledger; no `delattr`).

**Deferred filters↔orders items — correctly left for project pass.**
Re-proved from source: (1) `_make_hashable` / `_make_cache_key` have one
concrete Layer-6 site; `orders/factories.py` only TODO-reserves
`_dynamic_orderset_cache` / `get_orderset_class` — premature shared owner.
(2) Decision-11 / Decision-9 mirrors already share substrate
(`build_lazy_input_annotation`, `clear_generated_input_namespace`,
`GeneratedInputArgumentsFactory`); remaining per-subsystem namespace + ledger
ownership needs orders as co-owner. (3) `_unwrap_enum_member` vs
`write_values.raw_choice_value` — identical one-liner, write-flavor scoping;
project-pass neutral util question.

**Rejected candidates re-checked.** Dual clear owners
(`filters.helper_references` vs `filters.input_namespace`, `before_bind=True`)
remain intentional. `_resolve_relation_target_type` vs
`_target_type_for_related_filter` still differ on primary path
(owner `related_target_for` vs child filterset `_owner_definition.origin`).
`_target_definition_for` (runtime GlobalID decode) stays phase-distinct from
class-level Relay routing. Public export flavor matches orders twin.

**Missed folder-level consolidations.** Searched remaining `__` / `_meta.get_field`
/ path-walk sites inside `filters/` — only the three `get_model_field` call
sites remain; no second private walk. No additional cross-module policy
inside this folder warrants a solo consolidation before the project pass.

**Scope.** No production edits by Worker 2. Plan item checked. Concurrent WIP
outside the item-scoped diff left untouched.

**Disposition:** verified.
