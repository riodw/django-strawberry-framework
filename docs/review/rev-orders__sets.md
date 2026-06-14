# Review: `django_strawberry_framework/orders/sets.py`

Status: verified

## DRY analysis

- **Defer — `apply_sync` / `apply_async` shared tail.** `apply_sync` (sets.py:565-576) and `apply_async` (sets.py:604-618) share a six-line tail verbatim (`_normalize_input` -> empty-guard -> `get_flat_orders` -> `_resolve_order_expressions` -> `not expressions` guard -> conditional `annotate` + `order_by`); they diverge only in step 2 (sync direct `_run_permission_checks` call vs `await sync_to_async(...)`). This is the package's canonical sync/async-twin shape (relay/list_field/connection/filters) — awaitable-unwrap makes a 2-site extraction net-negative, and the divergent permission-check line is load-bearing. **Defer until a third apply surface lands** (e.g. a streaming/bulk variant); collapse the post-permission tail into a `_finish_order(cls, queryset, input_value)` helper then. Do NOT act now.
- **Defer — order/filter `_run_permission_checks` prologue twin.** The `OrderSet._run_permission_checks` prologue (sets.py:427-446: None-guard, `_fired` init, `bare` allocation, single `run_active_input_permission_checks` call) is a near-mirror of the filter side minus the `and`/`or`/`not` logical recursion and depth cap. The shared core already lives in `utils/permissions.py::run_active_input_permission_checks`; the remaining per-family prologue divergence (filter has logic recursion + depth cap, order has neither) is exactly the load-bearing difference. **Defer until a third set family (`AggregateSet`) lands its own `_run_permission_checks`**; re-triage a `_run_permission_checks_prologue` helper then.
- None beyond the two deferred twins — every reusable mechanic (`collect_related_declarations`, `expanded_once`, the six `utils/permissions.py` delegates, `relation_kind`/`is_many_side_relation_kind`, `normalize_input_value`, `SetLifecycleAttrs`) is already single-sited through the 0.0.9 DRY pass and consumed here via thin family-named wrappers.

## High:

None.

## Medium:

None.

## Low:

### `apply_sync` / `apply_async` docstring step lists drift on the `annotate` step vs the code

Both apply docstrings (sets.py:544-564, 585-601) describe steps 1-5 but predate the to-many aggregate machinery being fully wired into the step numbering: step 5 in `apply_sync` (sets.py:561-563) now reads "`annotate(**annotations)` (when any to-many term produced one) then `order_by(*expressions)`", which is accurate, but `apply_async`'s docstring (sets.py:585-601) never mentions the `annotate(**annotations)` call at all even though its body performs it identically (sets.py:616-617). The async docstring only enumerates "`get_flat_orders` and `queryset.order_by(...)` are NOT wrapped" and omits the annotate step from its prose entirely. Minor stale-but-harmless docstring asymmetry — recommend adding the same "`annotate` (when a to-many term produced one)" clause to the `apply_async` docstring so the sibling pair stays symmetric. Comment-pass tier; no behavior at stake.

### `check_permissions` bound-method form depends on a `_input_value` slot only ever written by a test

`check_permissions` (sets.py:448-460) routes through `getattr(self, "_input_value", None)`, but no source path in the package ever writes `self._input_value` — the only writer is `tests/orders/test_sets.py:464` (`instance._input_value = input_value`), which exercises the cookbook bound-method contract. The `getattr(..., None)` fallback means the production-reachable path (no parked input) collapses to `_run_permission_checks(None, request)` -> immediate return. This is deliberate cookbook parity (the upstream `AdvancedOrderSet.check_permissions` is a bound-method gate) and is covered by a real test, so it is not dead code. Forward-looking Low only: **if a future slice wires a resolver-layer site that parks `_input_value` on an instance**, document the writer site in the `check_permissions` docstring at that point so the slot's provenance is not test-only. No action now.

## What looks solid

### DRY recap

- **Existing patterns reused.** Set-family collection via `collect_related_declarations(..., inherit_from_bases=True, declaration_type=RelatedOrder, collection_attr="related_orders")` (sets.py:111-118); the class-level expansion-cache + reentry-guard skeleton via `expanded_once(...)` keyed off `_lifecycle.cache`/`_lifecycle.guard` (sets.py:220-225); the six permission-pipeline delegates (`request_from_info`, `extract_branch_value`, `active_related_branches`, `active_permission_field_paths`, `invoke_permission_method`, `run_active_input_permission_checks`) all single-sited in `utils/permissions.py` (sets.py:287-446); `SetLifecycleAttrs` as the single source for the lifecycle attr-name tuple shared with `registry.clear()` (sets.py:171-175); cardinality classification wholly delegated to `utils/relations.py::relation_kind`/`is_many_side_relation_kind` (sets.py:76, `_path_traverses_to_many`).
- **New helpers considered.** The two apply-pipeline twins (sync/async tail; order/filter `_run_permission_checks` prologue) were evaluated and deferred-with-trigger — see `## DRY analysis`. The 5x `related_orders` literal (shadow repeated-literal signal) is an intentional family parameter passed to the shared collectors/delegates (`collection_attr`/`related_attr`), NOT a constant candidate — same calibration as `filters/sets.py`'s `related_filters`.
- **Duplication risk in the current file.** `_normalize_input` (sets.py:273-284) is a one-line delegate to `normalize_input_value`; it has NO operator-bag and therefore NO analogue of the `filters/sets.py::_normalize_input` redundant-`.get` Low (`all_filters.get(form_key) or all_filters.get(suffixed_key)`, filters/sets.py:743-745) — the order side never threads form-data through django-filter, so that act-now tidy has no counterpart here. Cross-file directive resolved: nothing to flag.

### Other positives

- **To-many fan-out defense is correct (the headline data-correctness surface).** `_resolve_order_expressions` (sets.py:497-535) routes a to-many path (`_path_traverses_to_many`, sets.py:56-82) through an `.annotate(<alias>=Min/Max(path))` + order-by-alias instead of a raw `order_by("rel__col")`. The aggregate forces a GROUP BY on the parent so exactly one row per parent survives — this prevents the fan-out JOIN that would silently duplicate/skip nodes under positional cursors and inflate `totalCount` (docs/feedback.md P1-B). `Min` for ascending / `Max` for descending is the correct monotone choice. The alias `_dst_order_{index}_{path}` is keyed on the `enumerate` index (sets.py:529), so two terms over the same to-many path get distinct aliases — no annotation-key collision.
- **`_path_traverses_to_many` walk is conservative and termination-safe.** Stops at the first non-relation segment (terminal scalar) or unresolvable segment (transform/lookup) returning `False` (sets.py:73-77); only returns `True` on a genuine many-side segment per `is_many_side_relation_kind`. To-one paths (forward FK/O2O, reverse O2O) correctly fall through to the direct `order_by` branch. `FieldDoesNotExist` caught -> `False` (a lookup/transform tail cannot multiply).
- **`Ordering` direction sense via `"ASC" in direction.name`.** `_resolve_order_expressions` picks `Min` vs `Max` off `"ASC" in direction.name` (sets.py:530). Verified against the `Ordering` enum (inputs.py:62-106): every ascending member name contains `ASC` (`ASC`, `ASC_NULLS_FIRST`, `ASC_NULLS_LAST`) and no `DESC*` member contains the substring `ASC`, so the substring test is unambiguous. NULLS positioning carries onto the aggregate alias because the alias is resolved through the same `direction.resolve(alias)`.
- **Permission gate ordering is pre-mutation.** Both apply paths run `_run_permission_checks` BEFORE any `order_by`/`annotate` touches the queryset (sets.py:566/605), so a denial gate raises before the queryset is mutated — spec-028 Decision 8 step 6. `None`-direction terms are filtered in `_resolve_order_expressions` (sets.py:526), and an all-`None`/empty input returns the queryset unchanged (sets.py:568-569/572-573).
- **Active-branch double dispatch + per-class dedup verified at the util.** `run_active_input_permission_checks` (utils/permissions.py:220-259) fires the per-field gate loop, recurses into each active child set's own `_run_permission_checks` (keyed by `target_attr="orderset"`, sets.py:445), then fires the parent's per-branch gate against a DIFFERENT per-class `_fired` set — so parent `check_<branch>_permission` and child field gates both fire once. `handle_top_level_list=True` (sets.py:336/362) correctly walks each dataclass element of the top-level `list[<T>OrderInputType]` shape separately, with `_fired` collapsing repeats per class.
- **`get_fields` cache-write gate matches the filter side's two-condition guard.** The cache writes only when `"related_orders" in cls.__dict__` AND every `_orderset` is a real class (no string forward-ref left) (sets.py:209-212); `cls.__dict__.get` (not `getattr`) prevents a subclass inheriting a parent's completed cache via MRO. `_expand_meta_fields` handles `None`-Meta, `None`-fields, `"__all__"` (via `_get_concrete_field_names_for_order`, with a `ConfigurationError` when `Meta.model` is absent, sets.py:252-256), and list/tuple/dict iteration. The `"__all__"` branch's local import of `_get_concrete_field_names_for_order` (sets.py:248) correctly dodges the `orders/sets.py` <-> `orders/inputs.py` runtime cycle.
- **Metaclass collection ordering.** `OrderSetMetaclass.__new__` calls `super().__new__` first, then `collect_related_declarations` with `inherit_from_bases=True` (sets.py:103-118) — correct because the plain `type` metaclass does no MRO merge of `related_orders`, so the collector must copy each base's collection (reversed MRO, later bases win) before the class body's own `attrs` override. This mirrors the cookbook and is the deliberate divergence from the filter side (django-filter pre-merges `declared_filters`, so filters pass `inherit_from_bases=False`).
- **GLOSSARY clean.** `#orderset` (914-922), `#relatedorder` (1000-1008), `#ordering` (910-912), `#metaorderset_class` (800-810), `#order_input_type` (924-932) all check out against live source: the apply-pair shape, active-input-only + active-branch double-dispatch contract, the six-member `Ordering` enum + `resolve` semantics, and the RelatedOrder raw-`ImportError`-propagates-unrewrapped clause (1004) all match. No drift requiring an edit.

### Summary

Single-file logic review of `OrderSet` + `OrderSetMetaclass`. No High, no Medium; two forward-looking Lows (an `apply_async` docstring omitting the `annotate` step, and a `check_permissions` `_input_value` slot whose only writer is a test) and two deferred-with-trigger DRY twins (sync/async apply tail; order/filter permission-prologue). The to-many fan-out aggregate defense — the headline data-correctness surface — is correct and well-reasoned. The cross-file directive resolved cleanly negative: the order side's `_normalize_input` is a one-line delegate with no operator-bag, so it has no analogue of the filter side's redundant-`.get` Low. Every reusable mechanic is already single-sited through the 0.0.9 DRY pass and consumed via thin family-named wrappers. Both Lows are forward-looking with explicit triggers and no act-now source edit, the GLOSSARY is accurate, so this is a no-source-edit (shape #5) cycle.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
None — no-source-edit cycle.

### Tests added or updated
None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — 265 files left unchanged.
- `uv run ruff check --fix .` — All checks passed.

### Notes for Worker 3
- Low (`apply_async` docstring omits the `annotate` step): forward-looking comment-pass tier; deferred, no edit this cycle.
- Low (`check_permissions` `_input_value` writer is test-only): forward-looking, gated on "a future slice wires a resolver-layer site that parks `_input_value`"; no edit now.
- DRY: both bullets deferred-with-trigger (third apply surface; third set-family `_run_permission_checks`). No act-now consolidation.
- No GLOSSARY-only fix in scope — `#orderset`/`#relatedorder`/`#ordering`/`#metaorderset_class`/`#order_input_type` all verified accurate against live source.
- Cross-file directive (filters/sets.py `_normalize_input` redundant-`.get` analogue): resolved negative — order side `_normalize_input` is a one-line delegate with no operator-bag, no analogous pattern exists.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment/docstring edits made this cycle; the two Lows are forward-looking and recorded for a future touch (the `apply_async` annotate-step clause and the `check_permissions` `_input_value` provenance note), neither warranting a standalone edit now.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — no source/test/doc change this cycle (AGENTS.md "Do not update CHANGELOG.md unless explicitly instructed"; active plan `docs/review/review-0_0_9.md` is silent on a changelog entry for this item).

---

## Verification (Worker 3)

### Logic verification outcome
Shape #5 no-source-edit cycle confirmed: `git diff --stat 0872a20… -- django_strawberry_framework/orders/sets.py` is empty (byte-unchanged at baseline). No High/Medium findings; the two Lows are forward-looking with explicit triggers (verified below). Independently drove the riskiest claim — the to-many fan-out aggregate DEFENSE in `_resolve_order_expressions` — and the permission-gate dispatch LIVE.

**To-many fan-out defense (headline data-correctness surface) — VERIFIED live** (`config.settings`, no-DB query-compilation probe):
- `_path_traverses_to_many`: reverse FK `Category.items` → True; `items__name` (to-many then scalar) → True; forward FK `Item.category` → False; `category__name` (to-one then scalar) → False; scalar `name` → False; `FieldDoesNotExist` (`bogus`) → False. Conservative, termination-safe, classification correct.
- **Aggregate forces GROUP BY (one row per parent), NOT a fan-out JOIN:** the aggregate form's compiled SQL contains `GROUP BY`; the raw `order_by("items__name")` it defends against does NOT (the row-multiplying fan-out). This is the exact P1-B defense and it is real at the SQL layer.
- **Enumerate-keyed alias uniqueness:** two terms over the SAME to-many path (`items__name` ASC, `items__name` DESC) produced distinct aliases `_dst_order_0_items_name` / `_dst_order_1_items_name` — no annotation-key collision.
- **Direction sense `"ASC" in direction.name`:** ASC/ASC_NULLS_FIRST → `Min`; DESC → `Max`. Confirmed against the `Ordering` enum (inputs.py:84-89): all three ascending members contain `"ASC"`, no `DESC*` member contains the substring. Unambiguous.
- To-one / scalar fall-through: no annotation, direct `F(name)` expression. `None`-direction terms filtered (expr count drops correctly).

**Permission gating — VERIFIED live:**
- Active-input-only: supplied `{title}` fires only the `title` gate; the `shelf` gate stays silent. Empty `{}` and `None` fire nothing (`None` early-returns at sets.py:427).
- Per-class dedup across top-level list: `[{title},{title}]` fires the `title` gate exactly once (`_fired` collapses repeats per class under `handle_top_level_list=True`).
- Active-branch double dispatch confirmed at `utils/permissions.py::run_active_input_permission_checks` (248-259): per-field loop, then per active related branch recurse into child set's own `_run_permission_checks` (different per-class `_fired`) AND fire parent's per-branch gate via the same `cls._fired` — both fire once because they live in different per-class sets.
- Pre-mutation ordering: `apply_sync`:566 / `apply_async`:605 call `_run_permission_checks` strictly before any `annotate`/`order_by` (sets.py:574-576 / 616-618) — denial gates raise before queryset mutation.

Metaclass collection (`super().__new__` first → `collect_related_declarations(inherit_from_bases=True)`), Meta validation (`"__all__"` → `_get_concrete_field_names_for_order` with `ConfigurationError` on absent `Meta.model`; local import dodges the orders/sets ↔ orders/inputs cycle), and the two-condition `get_fields` cache-write gate (`"related_orders" in cls.__dict__` AND all `_orderset` are real classes; `cls.__dict__.get` not `getattr`) all read correctly against source.

**Two Lows confirmed forward-looking:**
1. `apply_async` docstring omits the `annotate` step — confirmed: `apply_sync` docstring step 5 (line 561) names `annotate(**annotations)`, `apply_async` docstring (585-601) does not, though its body performs it identically (line 617). Comment-pass tier, no behavior at stake.
2. `check_permissions` `_input_value` slot writer is test-only — confirmed via grep: the only `self._input_value` writer is `tests/orders/test_sets.py:464`; no source path writes it. `getattr(self, "_input_value", None)` fallback (sets.py:460) + the graceful-no-op test at test_sets.py:470 make it real cookbook-parity behavior, not dead code. Correctly gated on a future resolver-layer writer.

### DRY findings disposition
Both DRY bullets deferred-with-trigger and correctly justified: (1) sync/async apply tail — canonical sync/async-twin shape, awaitable-unwrap makes a 2-site extraction net-negative, divergent permission-check line load-bearing; defer until a third apply surface. (2) order/filter `_run_permission_checks` prologue — shared core already single-sited in `utils/permissions.py::run_active_input_permission_checks`; the remaining filter-only logic recursion + depth cap is the load-bearing divergence; defer until a third set family (`AggregateSet`). The 5× `related_orders` literal is an intentional family parameter (matches filters/sets.py `related_filters` calibration), not a constant candidate. No act-now consolidation — accepted.

### Sibling-cycle attribution (shape #5)
`orders/sets.py` itself is byte-unchanged at baseline (empty owned-path diff). The wider owned-scope `git diff --stat 0872a20…` is dirty only at CLOSED sibling cycles, each `verified` + `[x]` in `review-0_0_9.md`: conf.py(:70), connection.py(:71), exceptions.py(:72), list_field.py(:73), filters/factories.py(:80), filters/sets.py(:82), management/commands/inspect_django_type.py(:87), optimizer/extension.py(:92), optimizer/selections.py(:96), optimizer/walker.py(:98), docs/GLOSSARY.md (closed sibling hunks), tests/management/test_inspect_django_type.py + tests/optimizer/test_selections.py (those cycles' tests). `feedback2/3.md` delete = AGENTS.md #33 concurrent-maintainer; `db.sqlite3` = test artifact. The cycle's "Files touched: None" claim holds.

### Temp test verification
- Temp tests: `docs/review/temp-tests/orders_sets/probe.py` (to-many fan-out defense + alias uniqueness + direction sense + SQL GROUP BY), `docs/review/temp-tests/orders_sets/probe2.py` (active-input-only + per-class dedup dispatch). Gitignored, no permanent promotion warranted (existing suite already pins these via tests/orders/test_sets.py + test_inputs.py).
- Disposition: deleted at cycle closeout by Worker 0.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `orders/sets.py` checklist box. Empty owned-path baseline diff, CHANGELOG diff empty (Not-warranted with both citations), ruff format-check + check pass (COM812 standing notice). The headline to-many aggregate defense is correct and proven live; both Lows are genuinely forward-looking.
