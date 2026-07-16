# DRY review: `django_strawberry_framework/filters/base.py`

Status: verified

ITEM_BASELINE: `8452e51715f0ba667168f342003249c8f06a6adf`

## System trace

`filters/base.py` owns the filter **field primitives** (Layers 1–2 of the
six-layer pipeline) plus the consumer-facing `RelatedFilter`:

- **Typed primitives.** `TypedFilter` marker; `ArrayFilter` / `ListFilter` with
  empty-list-aware `method=` install (`_EmptyListAwareFilterMethod` + named
  `ArrayFilterMethod` / `ListFilterMethod`); `RangeFilter` / `RangeField` /
  `validate_range`.
- **Integer overflow safety.** `IntegerInFilter` (per-member coerce + drop via
  `utils/querysets.py::coerce_field_value_or_none`, then match-nothing when a
  non-empty input fully drops) and `IntegerRangeFilter` (decompose `__range`
  into one `gte`+`lte` predicate so bounds never raw-`BETWEEN`-overflow).
- **Lookup application.** Whole-value (never per-element OR) predicate binding
  for list-shaped `in` / array lookups, shared by `ArrayFilter` and
  `GlobalIDMultipleChoiceFilter`'s `in` branch.
- **GlobalID filter decode.** `_target_definition_for` /
  `_accepted_globalid_type_names` / `_decode_and_validate_global_id` plus
  `GlobalIDFilter` / `GlobalIDMultipleChoiceFilter` (including the absent-key
  `None` vs explicit `[]` form-field seam). Strategy memberships come from
  `types/relay.py::MODEL_LABEL_STRATEGIES` / `TYPE_NAME_STRATEGIES` (already
  shared with encode/decode).
- **RelatedFilter.** Thin `RelatedSetTargetMixin` parameterization
  (`_filterset` / `bound_filterset`) + queryset auto-derive + `lookups=`
  rejection; twin is `orders/base.py::RelatedOrder` (already consolidated in
  `sets_mixins`).

Callers: `filters/sets.py::filter_for_lookup` / `FILTER_DEFAULTS` routing,
`filters/inputs.py` annotation conversion, finalizer owner-bind, fakeshop
filtersets, package `tests/filters/test_base.py`, live
`examples/fakeshop/test_query/test_scalars_api.py` /
`test_scalars_filter_api.py` / products+library GlobalID `in: []` paths.

## Verification

- Item-scoped diff vs baseline was empty before this pass; sibling dirty
  paths (`filters/__init__.py`, auth, other dry artifacts) left untouched.
- Re-read graphene_django `array_filter.py` / `list_filter.py`: upstream
  still has byte-parallel `method` setters and parallel empty
  `*FilterMethod.__call__` bodies. This package already single-sited
  `__call__` on `_EmptyListAwareFilterMethod` (0.0.9); the setters remained
  duplicated. Fresh check: both setters encode one rule ("install
  empty-list-aware FilterMethod when `method=` is set") and must change
  together when that install contract moves; the named subclasses stay as
  distinct public type identities (spec-027 Decision 4 / graphene-parity
  names + `isinstance` tests).
- Confirmed `ArrayFilter.filter` vs `ListFilter.filter` are **different**
  empty-list contracts (`[]` is a real lookup value vs match-nothing) — must
  not share a `filter()` body.
- Confirmed `IntegerRangeFilter.filter` duplicated the
  `distinct` + `get_method(qs)(**lookups)` seam already owned for whole-value
  list predicates by `_apply_lookup_predicate`. Same responsibility; range
  just supplies a two-key lookup dict.
- Confirmed three sites returned `qs if exclude else qs.none()` for
  restrictive-empty membership (`ListFilter`, `GlobalIDMultipleChoiceFilter`,
  `IntegerInFilter` fully-dropped coerce). Same wire outcome; prior bug_hunt
  already showed this contract drifts when re-decided per filter.
- Traced `_coerce_int_in_members` → `coerce_field_value_or_none`: already the
  landed ownership from the relay.py DRY pass. Do not reverse. Sibling
  wrappers (`relay.py::_coerce_pk_or_none`,
  `utils/write_values.py::coerce_relation_pk_or_none`) keep field selection.
- Compared GlobalID filter decode to `types/relay.py::decode_global_id` /
  `relay.py::_decode_or_graphql_error`: different contracts (filter is
  defense-in-depth `type_name` against owner/target definition with
  node-id-only fallback; node path is registry resolve-then-enforce +
  `ConfigurationError` → `GLOBALID_INVALID`). Malformed-payload message
  text is similar but not the same owner — defer.
- Compared `RelatedFilter` to `RelatedOrder`: bind/resolve already live on
  `RelatedSetTargetMixin`; remaining wrappers are family-named surface.
  Cross-family packaging of anything further → folder/project.
- `_accepted_globalid_type_names` already keys off the shared strategy
  frozensets; further folding into `_accepts_*_decode` booleans would not
  remove knowledge (filter builds a set of accepted wire names).

## Opportunities

**1. Shared `method=` install for ArrayFilter / ListFilter**

- **Repeated responsibility:** when a consumer supplies `method=`, replace
  django-filter's default `FilterMethod` with an empty-list-aware wrapper.
- **Sites:** `ArrayFilter.method` setter, `ListFilter.method` setter (bodies
  identical except `ArrayFilterMethod` vs `ListFilterMethod`).
- **Evidence:** same install sequence; `__call__` already shared; only the
  installed class name differs; both must move if the install contract
  changes.
- **Owner:** `filters/base.py::_install_empty_list_aware_method`.
- **Consolidation:** both setters call the helper with their named
  `*FilterMethod` class; keep the empty subclasses as public type identities.
- **Proof:** existing `tests/filters/test_base.py` method-setter /
  `__call__` tests (`isinstance(..., ArrayFilterMethod|ListFilterMethod)`,
  `None` short-circuit, empty-list dispatch).
- **Risks / non-goals:** do not merge `ArrayFilter.filter` with
  `ListFilter.filter` (divergent empty-list semantics); do not collapse the
  two `*FilterMethod` names into one alias (public graphene-parity surface).

**2. Shared distinct + lookup binding**

- **Repeated responsibility:** honor `distinct`, then apply lookup kwargs in
  one `get_method(qs)(**lookups)` call (never per-element OR).
- **Sites:** `_apply_lookup_predicate` (ArrayFilter + GlobalID `in`);
  `IntegerRangeFilter.filter` (inline `gte`/`lte` dict).
- **Evidence:** identical distinct/get_method seam; only the lookup dict
  differs.
- **Owner:** `filters/base.py::_apply_lookups`, with `_apply_lookup_predicate`
  as the single-lookup convenience.
- **Consolidation:** `IntegerRangeFilter` routes through `_apply_lookups`.
- **Proof:** `tests/filters/test_base.py` IntegerRangeFilter distinct /
  gte+lte tests; live
  `examples/fakeshop/test_query/test_scalars_api.py::test_filter_specimens_by_bigint_range_out_of_range_bound_no_overflow`.
- **Risks / non-goals:** do not fold GlobalID non-`in` OR-delegation into this
  helper (intentionally upstream per-element semantics).

**3. Shared restrictive-empty membership result**

- **Repeated responsibility:** a restrictive empty membership matches nothing
  (`qs.none()`), or every row under `exclude=True` — never django-filter's
  empty-value skip.
- **Sites:** `ListFilter.filter`, `GlobalIDMultipleChoiceFilter.filter`,
  `IntegerInFilter.filter` (fully-dropped non-empty coerce).
- **Evidence:** identical return expression; same anti-widen invariant;
  historically drifted when re-implemented per filter.
- **Owner:** `filters/base.py::_match_none_queryset`.
- **Consolidation:** all three call sites use the helper.
- **Proof:** package empty-list / fully-dropped tests in
  `tests/filters/test_base.py`; live
  `test_scalars_api.py` bigint `in` drop / explicit `in: []` noop;
  products/library `id: { in: [] }` paths.
- **Risks / non-goals:** explicit empty `IntegerInFilter` input (`in: []`)
  keeps django-filter skip — only the fully-dropped non-empty path uses the
  helper; `ArrayFilter` must not use it (`[]` is a real value).

## Judgment

Three in-file consolidations were warranted and implemented. Cross-family
GlobalID malformed-parse messaging and any deeper RelatedFilter/RelatedOrder
surface packaging stay deferred. Coercion ownership already correctly sits on
`coerce_field_value_or_none`. Ready for Worker 2.

## Implementation (Worker 1)

- **Owner chosen:** module-private helpers in `filters/base.py`
  (`_install_empty_list_aware_method`, `_apply_lookups`,
  `_match_none_queryset`).
- **Migrated sites:** Array/List `method` setters; `_apply_lookup_predicate` +
  `IntegerRangeFilter.filter`; ListFilter / GlobalIDMultipleChoiceFilter /
  IntegerInFilter match-nothing returns.
- **Kept separate:** Array vs List `filter()` empty-list contracts; named
  `*FilterMethod` subclasses; GlobalID decode vs `decode_global_id`;
  RelatedFilter vs RelatedOrder family wrappers; explicit `in: []` skip on
  IntegerInFilter.
- **Tests:** no new permanent tests — existing package + live GraphQL
  coverage already pins each migrated contract. No full pytest this pass.
- **Validation:** `uv run ruff format .` and `uv run ruff check --fix .`.
- **Changelog:** no — internal ownership refactor, no consumer-visible
  behavior change.
- **Rejected / deferred (strongest):**
  - Fold filter GlobalID `from_id` + `GLOBALID_INVALID` into
    `types/relay.py::decode_global_id` / `relay.py::_decode_or_graphql_error`
    — different acceptance/fallback contracts; project/types.relay if a
    shared "parse wire GlobalID or coded error" primitive is ever justified.
  - Further RelatedFilter/RelatedOrder extraction — already on
    `RelatedSetTargetMixin`; folder/project only.
  - Alias `ArrayFilterMethod`/`ListFilterMethod` to one class — would erase
    public type identity without clarifying ownership beyond the setter
    helper.

## Independent verification (Worker 2)

Re-traced `filters/base.py` end-to-end against ITEM_BASELINE
`8452e51715f0ba667168f342003249c8f06a6adf` (item-scoped diff only adds the three
helpers and rewires the claimed call sites). No production edits this pass.

**1. `_install_empty_list_aware_method` — accepted.** ArrayFilter and ListFilter
`method` setters previously duplicated one install sequence
(`TypedFilter.method.fset` then swap `self.filter` for a named
`*FilterMethod`). Both now call the helper with their public subclass; no
leftover setter bodies. Named `ArrayFilterMethod` / `ListFilterMethod` type
identities remain (exported + `isinstance` tests). Array vs List `filter()`
empty-list contracts stay divergent and correctly unmerged.

**2. `_apply_lookups` — accepted.** Shared contract is honor `distinct` then one
`get_method(qs)(**lookups)` bind (never per-element OR). Callers:
`_apply_lookup_predicate` (single lookup key; ArrayFilter + GlobalID `in`) and
`IntegerRangeFilter.filter` (gte+lte dict). Inline distinct/get_method body is
gone from IntegerRangeFilter. GlobalID non-`in` still delegates to
`super().filter` (upstream OR) — correctly outside this helper.

**3. `_match_none_queryset` — accepted.** Shared contract is the restrictive-empty
*outcome* (`qs` under `exclude`, else `qs.none()`), not the per-filter trigger.
Migrated sites: `ListFilter.filter` (`[]`), `GlobalIDMultipleChoiceFilter.filter`
(`[]`), `IntegerInFilter.filter` (non-empty input fully dropped after coerce).
No leftover `qs if self.exclude else qs.none()` in package source. Boundaries
preserved: `ArrayFilter` never uses the helper (`[]` is a real lookup value);
`IntegerInFilter` explicit `in: []` still hits `EMPTY_VALUES` → django-filter
skip via `super().filter`.

**Rejected candidates (re-challenged, still separate).**

- **Filter GlobalID decode vs `types/relay.py::decode_global_id` /
  `relay.py::_decode_or_graphql_error`:** different ownership. Filter path is
  defense-in-depth `type_name` against owner/target definition with
  node-id-only fallback and filter-shaped mismatch messaging; node path is
  registry resolve-then-enforce raising `ConfigurationError` → wire
  `GLOBALID_INVALID`. Malformed-payload wording is similar; collapsing would
  couple distinct acceptance/fallback contracts. Defer stands.
- **RelatedFilter vs RelatedOrder:** bind/resolve already on
  `RelatedSetTargetMixin`; remaining wrappers are family surfaces
  (`bind_filterset` / `filterset` / `ModelChoiceFilter` + `lookups=` reject +
  queryset auto-derive vs `bind_orderset` / `orderset`). Further extraction is
  folder/project, not this file.

**`coerce_field_value_or_none` path:** preserved.
`_coerce_int_in_members` still drops via
`utils/querysets.py::coerce_field_value_or_none`; no parallel coerce body
reintroduced. Sibling field-selection wrappers (`relay._coerce_pk_or_none`,
`write_values.coerce_relation_pk_or_none`) remain correctly separate.

**Proof / tests / placement:** no new permanent tests in the Worker 1 diff —
correct. Existing pins cover each migrated contract:
`tests/filters/test_base.py` (method-setter `isinstance`, ListFilter /
GlobalID empty + exclude complements, IntegerRangeFilter distinct/gte+lte);
live `examples/fakeshop/test_query/test_scalars_api.py` (bigint `in` full-drop
→ match-nothing, explicit `in: []` noop, range out-of-range bound);
products/library `id: { in: [] }` paths. No new `test_query` files, so
`test_query/README.md` placement rules are not implicated.

**Missed opportunities:** none material in-scope. Further GlobalID parse
messaging or Related* packaging remain deferred as above. No stale duplicate
install / distinct-bind / match-none bodies found outside the new owners.

**Blockers:** none.

**Disposition:** Status `verified`; plan item
`File \`filters/base.py\`` checked.
