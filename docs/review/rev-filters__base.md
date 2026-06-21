# Review: `django_strawberry_framework/filters/base.py`

Status: verified

## DRY analysis

- **Defer-with-trigger: collapse the `method` setter + `*FilterMethod` subclass pair.** `filters/base.py::ArrayFilter.method` (lines 117-122) and `filters/base.py::ListFilter.method` (lines 174-179) are near-byte-identical setters — both call `TypedFilter.method.fset(self, value)` then, on `value is not None`, assign `self.filter = <X>FilterMethod(self)`; the only delta is the `ArrayFilterMethod` vs `ListFilterMethod` class. Those two classes (lines 85-86, 161-162) are themselves empty subclasses of `_EmptyListAwareFilterMethod` whose only purpose is to be the distinct type each setter installs. A shared helper (e.g. a `_install_empty_list_aware_method(self, value, method_cls)` on a mixin, or a `_method_class` ClassVar read by one shared setter) would single-site the setter body. **Do not act now:** the two `*FilterMethod` subclasses carry distinct docstrings naming their owning filter and exist as named hooks for future per-filter divergence; folding them now trades two trivially-readable 5-line siblings for indirection with no third caller. **Defer until a third `TypedFilter` subclass needs the empty-list-aware `method` swap; then introduce the shared `_method_class` ClassVar + single setter across all three.**

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** The empty-list-aware custom-method path is already single-sited: `filters/base.py::_EmptyListAwareFilterMethod.__call__` (lines 78-82) is the one place the "`None` short-circuits, `[]` reaches `self.method`" contract lives, and `ArrayFilterMethod` / `ListFilterMethod` inherit it unchanged (the 0.0.9 DRY pass, cited in the class docstring line 69). The GlobalID decode/validate path is single-sourced through three private module functions — `_target_definition_for` (lines 188-228), `_accepted_globalid_type_names` (lines 231-258), `_decode_and_validate_global_id` (lines 261-294) — consumed by both `GlobalIDFilter.filter` (line 320) and `GlobalIDMultipleChoiceFilter.filter` (line 365, with `index=`), so single-value and multi-value validation cannot drift. `RelatedFilter` (lines 370-486) delegates all owner-bind / lazy-target machinery to `sets_mixins.RelatedSetTargetMixin` via `_bind_owner` / `_resolved_target` / `_set_target` (parameterized by `_target_attr`/`_owner_attr`, lines 393-394) — the shared set-family primitive, not a local copy. The strategy frozensets `MODEL_LABEL_STRATEGIES` / `TYPE_NAME_STRATEGIES` are imported from `types/relay.py` (line 47), the single source of truth shared with the encoder/decoder, rather than re-declared here.
- **New helpers considered.** The `method` setter + `*FilterMethod` pair was the one act-now candidate evaluated; rejected/deferred above (no third caller, the named subclasses are intentional hooks). The two `filter` overrides (`ArrayFilter.filter` lines 124-131 vs `ListFilter.filter` lines 181-185) are NOT a consolidation candidate — they implement opposite empty-list semantics (`ArrayFilter` treats `[]` as a real lookup value; `ListFilter` short-circuits `[]` to `qs.none()`/`qs`), so a shared body would have to branch on the very difference that justifies two classes.
- **Duplication risk in the current file.** None — `scripts/review_inspect.py` reports 0 repeated string literals. The two near-identical setters are the only structural near-copy and are addressed in DRY analysis.

### Other positives

- **GlobalID validation is correctly defense-in-depth, not the error contract.** `_accepted_globalid_type_names` returns `None` (skip the guard, node-id-only fallback) for `callable`/`custom` strategies, an unbound owner, an unresolvable target, or an absent strategy — never raises. The docstring (lines 244-248) is explicit that decode owns the uniform-error contract and the filter only falls back. This matches the GLOSSARY's `RelatedFilter` visibility-vs-constraint framing.
- **`_target_definition_for` routing is single-sited and well-documented.** The own-PK-vs-relation branch (lines 222-228) resolves WHICH definition once, so the strategy check downstream consumes a single definition (spec-031 Decision 13). The `head, _sep, _tail = field_name.partition("__")` split correctly handles both bare PK names and expanded child paths like `"genres__id"`. The 6-branch / 41-line hotspot flagged by the static helper is justified by the documented two-branch routing plus null-guards; no missing-branch test smell.
- **`_GlobalIDMultipleChoiceField.valid_value` override is correct and necessary.** Stock `MultipleChoiceField.valid_value` would reject every GlobalID against the empty `choices` set at form-clean time before the filter's decode runs; accepting any value and deferring to `filter` mirrors graphene-django. The `noqa: ARG002` on the Django-fixed signature is appropriate.
- **`RelatedFilter.__init__` guards `lookups=` ahead of `super().__init__`.** The guard runs before `ModelChoiceFilter.__init__` precisely because `django_filters.Filter.__init__` would silently absorb the dead kwarg into `self.extra` and mask it — a deliberate root-cause placement, not a surface check.
- **Import-cycle reasoning is documented at the module-top import (lines 41-47).** The `filters/base.py -> types/relay.py` module-top import is explained as acyclic (the documented safe direction; `types/relay.py` reaches into `filters`/`registry` only via in-function imports), so the strategy frozensets can be a module-top import rather than a deferred one.

### Summary

`filters/base.py` is the filter-primitives + `RelatedFilter` module — a careful, well-annotated port of the matching graphene-django / django-graphene-filters primitives with Graphene-only constructor args dropped and the GlobalID decode substituted to `strawberry.relay.GlobalID.from_id`. The cycle diff is empty against both the per-cycle baseline (`03e84d31`) and HEAD, and the GLOSSARY prose for every public symbol (`RelatedFilter` entry at 1043-1051, and the corroborating `RelatedOrder` note at 1057 that explicitly relocates the shared Layer-2 resolution to `sets_mixins.LazyRelatedClassMixin` "not `filters.base` as named in earlier revisions") is accurate to the on-disk code. No High/Medium/Low findings; one defer-with-trigger DRY candidate (the `method`-setter + `*FilterMethod` pair). Genuine no-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; `289 files left unchanged`.
- `uv run ruff check --fix .` — pass; `All checks passed!`.

### Notes for Worker 3
- Cycle diff is empty vs both the per-cycle baseline (`03e84d3112416f6b62caa8eacb3cc7cc95535c60`) and HEAD; zero edits to any tracked file.
- No High; no Medium; no Low. The single DRY-analysis bullet (the `method` setter + `*FilterMethod` subclass pair) is explicitly defer-with-trigger ("Defer until a third `TypedFilter` subclass needs the empty-list-aware `method` swap"), not act-now.
- No GLOSSARY-only fix in scope: the `RelatedFilter` entry (GLOSSARY.md:1043-1051) and the `RelatedOrder` corroborating note (GLOSSARY.md:1057) are accurate to on-disk source; the shared Layer-2 resolution correctly attributed to `sets_mixins.LazyRelatedClassMixin`, and the mixin slots / strategy-frozenset cross-module references all resolve to live symbols.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted — no source, test, GLOSSARY, or other tracked-file edits this cycle (AGENTS.md: do not update CHANGELOG.md unless explicitly instructed; the active plan `docs/review/review-0_0_11.md` is silent on any changelog entry for this item).

---

## Verification (Worker 3)

### Logic verification outcome
All High / Medium / Low are `None.` and genuine — verified independently, not accepted on the artifact's word. Each filter primitive is pinned by a named test in `tests/filters/test_base.py`:
- `ArrayFilter`: `test_array_filter_treats_empty_list_as_value`, `test_array_filter_passes_through_none`, `test_array_filter_method_setter_swaps_in_array_filter_method` (asserts `isinstance(f.filter, ArrayFilterMethod)`).
- `RangeFilter` / `validate_range`: accepts-two / rejects-single / rejects-three + `test_range_filter_uses_range_field_class`.
- `ListFilter`: `test_list_filter_returns_qs_none_on_empty_list`, `..._returns_qs_when_excluding_on_empty_list`, `..._defers_to_super_for_nonempty_lists`, `test_list_filter_method_setter_swaps_in_list_filter_method`.
- `GlobalIDFilter` / `GlobalIDMultipleChoiceFilter`: decode-via-strawberry-relay + None-passthrough (both), `..._decodes_every_element` (multi).
- `LazyRelatedClassMixin`: all 5 branches — absolute-path, bound-module fallback, class-as-is, callable factory, raise-when-unresolved-string-has-no-bound-class.
- `RelatedFilter`: class/absolute-path/unqualified-name args, `bind_filterset` sets `bound_filterset`, `.filterset` property lazy resolution (string + absolute), `get_queryset` auto-derive from target model, and `test_related_filter_rejects_lookups_kwarg` (pins the pre-`super().__init__` `lookups=` guard + absence from `inspect.signature`).

The `RelatedFilter` lazy-target machinery is correctly delegated: `RelatedSetTargetMixin(LazyRelatedClassMixin)` at `sets_mixins.py:142` provides `_bind_owner`/`_resolved_target`/`_set_target` (171/176/185); `resolve_lazy_class` (102-141) implements the two-attempt resolution with the raw `ImportError` propagating unchanged when `bound_class` is falsy — matching the GLOSSARY prose verbatim. Strategy frozensets `MODEL_LABEL_STRATEGIES` / `TYPE_NAME_STRATEGIES` resolve to `types/relay.py:413-414`. No masked defect forcing a source edit.

### DRY findings disposition
Single DRY item (the `ArrayFilter.method` / `ListFilter.method` setter + `ArrayFilterMethod` / `ListFilterMethod` subclass pair) is correctly **defer-with-trigger**: carries the verbatim trigger ("Defer until a third `TypedFilter` subclass needs the empty-list-aware `method` swap"). The named `*FilterMethod` subclasses are intentional per-filter hooks; folding now would add indirection with no third caller. The two `filter` overrides are correctly excluded as non-candidates — `ArrayFilter` treats `[]` as a real lookup value while `ListFilter` short-circuits `[]` to `qs.none()`/`qs`, the opposite-semantics difference that justifies two classes. No act-now DRY obligation.

### Temp test verification
- None — no temp tests needed; existing permanent suite (`tests/filters/test_base.py`) pins every primitive.

### Shape #5 (no-source-edit) checks
1. Zero-edit proof two ways: `git diff 03e84d3112416f6b62caa8eacb3cc7cc95535c60 -- django_strawberry_framework/filters/base.py` empty AND `git diff HEAD -- ...` empty; `filters/base.py` absent from the owned-paths `--stat`.
2. Each Worker 2 section opens with `Filled by Worker 1 per no-source-edit cycle pattern.` (Files touched / Tests / Changelog).
3. No Low findings (all `None.`); no GLOSSARY-only fix in scope.
4. Changelog `Not warranted` cites BOTH AGENTS.md and the active plan's silence; `git diff -- CHANGELOG.md` empty.
5. `uv run ruff format --check` (already formatted) + `uv run ruff check` (All checks passed!) both pass on the target.

The only owned-paths `--stat` dirt is `django_strawberry_framework/types/resolvers.py` — a NON-target sibling cycle with its own `docs/review/rev-types__resolvers.md` artifact (box `[ ]` at `review-0_0_11.md:139`). Per diff-scoping, a non-target hunk is out of scope regardless of its rev state (closed-sibling carve-out only matters when attributing a hunk that touches the target itself; the target diff is clean, so this is informational).

#4-vs-#5 gate: genuine #5, not a missed #4. The GLOSSARY `RelatedFilter` (heading at line 1043) and `RelatedOrder` (1057) entries read accurate against live source — no owed GLOSSARY fix.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` and marks the `filters/base.py` checklist box in `docs/review/review-0_0_11.md`.
