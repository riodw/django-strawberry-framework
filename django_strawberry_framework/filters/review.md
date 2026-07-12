# Pre-BETA review: filters/

Scope: Meta-driven FilterSets -- `base.py` (filter primitives), `factories.py`
(argument factory), `inputs.py` (input-type generation), `sets.py` (the
`FilterSet` with tree-form `and`/`or`/`not` logic, visibility scoping, apply).

Method: full logic read of `base.py` and the apply/logic-tree/related-constraint
sections of `sets.py` in `docs/shadow/current/`, plus the diffs since `0.0.13`
(this cycle extracted `_apply_lookup_predicate`, added the shared
`should_cache_expansion` gate, and routed input-field collision detection
through the shared `iter_input_field_collisions`). Read-only; no tests run.

Bottom line: mature and careful -- to-many joins are collapsed via `pk__in`
subqueries (no duplicate parent rows, no consumer-visible `.distinct()`
mutation), malformed input raises a structured `GraphQLError`, and async parity
pre-walks nested visibility. One empty-list semantic is inconsistent with the
sibling `ListFilter` and is worth reconciling before the API freezes.

## P0 -- correctness suspicions

None found.

## P1 -- fix before BETA

### `base.py::GlobalIDMultipleChoiceFilter.filter` -- empty id list returns ALL rows, not none
Confidence: medium. For the default lookup, an empty decoded `node_ids` list
takes the `if not node_ids: return qs` branch -- i.e. `id__in: []` returns the
*entire* queryset unfiltered. The sibling `ListFilter.filter` deliberately
returns `qs.none()` for an empty non-exclude list (matching SQL `IN ()`
semantics: an empty membership set matches nothing). These two multi-value
filters therefore answer an empty list oppositely. The "return all" reading is
django-filter's own `MultipleChoiceField` default, but the package already
overrode that intuition for `ListFilter`, so a consumer reasonably expects the
GlobalID variant to match. Pick one semantic (empty membership -> match nothing
is the defensible one) and apply it to both.
Verify: `where(id: { in: [] })` on a GlobalID filter -- assert row count is 0,
and compare to the `ListFilter` empty-list result.

## P2 -- polish / hardening

### `base.py::IntegerInFilter._coerce_int_in_members` -- silently drops invalid `__in` members
Confidence: low (behavioral, likely intentional). Non-coercible members of an
integer `__in` list are dropped (`continue`), and an all-invalid list collapses
to `qs.none()`. This is the fix for the historical GlobalID in-filter
string-explosion, so dropping is deliberate -- but silently discarding a
malformed member (`id__in: [1, "abc", 3]` -> filters on `[1, 3]`) can mask a
client bug. Consider whether BETA wants a structured error for a malformed
member instead of a silent drop; at minimum document the drop.

### Leaf filters spanning to-many relations -- confirm duplicate-row handling
Confidence: low. The `RelatedFilter` path and the `and`/`or`/`not` tree both use
`pk__in` subqueries, which correctly collapse to-many duplicates. But a plain
generated leaf filter whose `field_name` traverses a to-many relation
(e.g. `tags__name`) goes through django-filter's own `filter()`, and
`_apply_lookup_predicate` only calls `.distinct()` when `filter_instance.distinct`
is set. Verify the factory sets `distinct=True` for any generated lookup that
spans a to-many relation, or that such lookups are not auto-generated -- otherwise
those leaves can return duplicate parent rows and corrupt connection counts.
Verify: generate a filter over a reverse-FK/M2M path and check for duplicate
parent nodes in a list/connection result.

## API & consistency notes

- `_validate_form_or_raise` explicitly calls `form.is_valid()` and raises a
  `GraphQLError` with a structured `extensions` payload
  (`code: "FILTER_INVALID"`, per-field `errors`). This is the right posture --
  `BaseFilterSet.qs` would otherwise silently ignore invalid input. Keep the
  `extensions` shape aligned with the orders side so filter and order validation
  errors look like siblings.
- `RelatedFilter` with a cross-model explicit `queryset=` raises a typed
  `ConfigurationError` naming both models instead of Django's opaque
  "Cannot combine queries on two different base models" `TypeError`. Good.

## Verified sound (do not re-flag)

- To-many duplicate handling: `sets.py::_apply_related_constraints` builds the
  parent restriction as `constrained.filter(pk__in=<parent-pk subquery>)`
  keyed on the relation's ORM path (not the declared attr name), collapsing
  duplicates without a consumer-visible `.distinct()` and deriving the subquery
  from `constrained` so the DB alias and custom-manager filtering carry through.
- Tree logic: `_evaluate_logic_tree` composes `and`/`or`/`not` via
  `Q(pk__in=child_qs.values("pk"))` against sibling filterset instances that
  reuse the parent's already-visibility-scoped queryset, so visibility-before-
  filter holds at every recursion level; depth is capped (`_MAX_LOGIC_DEPTH`).
- Async parity: `apply_async` pre-walks nested branch visibility
  (`_collect_nested_visibility_querysets_async`) before the sync `.qs` read, so a
  nested branch whose target has an async-only `get_queryset` does not raise
  `SyncMisuseError` mid-evaluation; the finalize step runs under
  `sync_to_async(thread_sensitive=True)`.
- `GlobalIDFilter`/`GlobalIDMultipleChoiceFilter` validate each decoded id's
  `type_name` against the accepted set for the target definition's
  effective GlobalID strategy, rejecting cross-type ids with a `GraphQLError`.

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
