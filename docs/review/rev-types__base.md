# Review: `django_strawberry_framework/types/base.py`

Status: verified

## DRY analysis

- **Pre-collected reflective Meta reads via `getattr(meta, key, None)`.** `_validate_meta` at `base.py:548,563,564,568,582,583` performs six `getattr(meta, ...)` reads against the same `meta` instance; `_validate_interfaces` adds a seventh at `base.py:453`; `_meta_optimizer_hints` adds an eighth at `base.py:390`; `DjangoType.__init_subclass__` adds two more at `base.py:231,232` (for `name` and `description`). The eight-read pattern is consistent (always `getattr(meta, "<key>", <default>)` with the same default convention) and centralizes the "optional-key with sentinel default" idiom. Defer until a third nested helper needs to read the same pre-validated `meta` instance; at that point fold the readonly-snapshot construction into `_ValidatedMeta` so `name` and `description` thread through alongside the existing five validated fields (eliminating the two `getattr` calls at `base.py:231-232`).

- **`_normalize_fields_spec` and `_normalize_sequence_spec` parallel.** `base.py:301-307` and `base.py:310-316` differ only in the error-message string and the `"__all__"` short-circuit branch. The two-line difference is intentional (`_normalize_fields_spec` accepts the sentinel; `_normalize_sequence_spec` does not), but the `isinstance(value, str) or not isinstance(value, Sequence)` raise-guard is verbatim duplicated. Defer until a third optional-sequence Meta key lands (`Meta.search_fields` per spec roadmap) — at that point hoist the shared shape-guard into a `_reject_non_sequence_spec(value, *, attr)` helper that both normalizers and `search_fields` can call. Today the duplication is two lines per site and the message text differs, so a helper extraction would not measurably shrink readable surface.

- **`_select_fields` re-runs `_normalize_fields_spec` / `_normalize_sequence_spec` at `base.py:685-686` that `_validate_meta` already ran at `base.py:582-583`.** `_ValidatedMeta` already carries `fields_spec` and `exclude_spec` post-normalization (`base.py:517-518`), but `_select_fields` re-reads `meta.fields` / `meta.exclude` and re-normalizes them, doubling the shape-gate raise surface. Act now: change `_select_fields(meta)` to `_select_fields(meta_model, fields_spec, exclude_spec)` and thread the validated values from `__init_subclass__:171` so the shape-gate runs exactly once per class definition (matching the `_ValidatedMeta` docstring at `base.py:506-511` which says "avoids re-running the shape gates ... at multiple sites"). Mechanically: `__init_subclass__` already has `validated.fields_spec` / `validated.exclude_spec` in hand at the line-171 call site, so the change is local — one signature update + two call-site arg threads.

- **`_format_unknown_fields_error` mis-shaped re-use at `base.py:641-650` for selected-but-non-relation hints.** The "excluded_hint_fields" branch routes selected scalar hints AND excluded hints through the same `_format_unknown_fields_error` shape, which renders as `"Category.Meta.optimizer_hints names unknown fields: ['name']. Available: [...]"` even when `name` IS a real field on the model. The message says "unknown fields" but the field is actually known — it just isn't a selected relation. This is a message-shape DRY violation: the format helper is the right shape for typo-guards but the wrong shape for "selected scalar with hint" / "excluded field with hint". Defer until a consumer-visible error-clarity bug is filed OR the `Meta.optimizer_hints` GLOSSARY entry is rewritten — at that point split the helper into `_format_unknown_fields_error` (real typos) and `_format_invalid_hint_target_error` (field exists but is not a selected relation), with the latter naming the actual reason ("not a selected relation field" / "excluded by Meta.exclude") in the message.

## High:

None.

## Medium:

### `_select_fields` re-normalizes specs that `_validate_meta` already validated

`__init_subclass__` at `base.py:170-171` calls `_validate_meta(meta)` (which runs `_normalize_fields_spec` and `_normalize_sequence_spec` at `base.py:582-583` and stores the results on `_ValidatedMeta.fields_spec` / `_ValidatedMeta.exclude_spec`), then immediately calls `_select_fields(meta)` at `base.py:171`. `_select_fields` at `base.py:685-686` re-reads `meta.fields` / `meta.exclude` and re-runs both normalizers, doubling the shape-gate raise path.

Why it matters:

1. **Stated invariant violated.** The `_ValidatedMeta` docstring at `base.py:506-511` explicitly promises "avoids re-running the shape gates (`_normalize_fields_spec`, `_normalize_sequence_spec`, `_meta_optimizer_hints`) at multiple sites in `__init_subclass__`." `_select_fields`'s re-normalization is exactly the kind of duplication the snapshot was introduced to eliminate. The docstring lies — silently — about the helper's purpose, which is a maintenance trap for future contributors who reason about the invariant.
2. **Subtle behavior risk if either normalizer ever raises differently between calls.** Today both normalizers are pure functions over the raw `meta` attribute, so the second call raises identically to the first; the visible failure mode is unchanged. But the redundant call still consults `getattr(meta, "fields", None)` and `getattr(meta, "exclude", None)` against the live class object, so any future evolution that makes a normalizer side-effectful (e.g. emits a deprecation warning) would emit twice per class definition.
3. **Failure-path coverage drift.** The "Meta.exclude must be a non-string sequence" error currently has two reachable raise sites — `_validate_meta` and `_select_fields` — but only one of them ever fires for any given input, because `_validate_meta` runs first and raises before `_select_fields` is reached. The second site is dead code under normal flow; a coverage gap exists if any consumer somehow bypasses `_validate_meta` (e.g. a test that calls `_select_fields` directly).

Recommended change: change `_select_fields(meta: type)` to `_select_fields(model: type[models.Model], fields_spec: tuple[str, ...] | str | None, exclude_spec: tuple[str, ...] | None)` and update the single call site at `base.py:171` to pass `meta.model, validated.fields_spec, validated.exclude_spec`. Drop the `_normalize_fields_spec` / `_normalize_sequence_spec` calls at `base.py:685-686`. The function body downstream of the rename uses only `model` (the existing `model = meta.model` at `base.py:684` collapses), `fields_spec`, and `exclude_spec` — no other local rewrites. Mirror the test surface by adding a regression in `tests/types/test_base.py` that calls `_select_fields(...)` directly with the new signature to pin the contract (the existing module-level tests still cover the integrated path through `__init_subclass__`).

```django_strawberry_framework/types/base.py:170-171
        validated = _validate_meta(meta)
        fields = _select_fields(meta)
```

```django_strawberry_framework/types/base.py:684-687
    model = meta.model
    fields_spec = _normalize_fields_spec(getattr(meta, "fields", None))
    exclude_spec = _normalize_sequence_spec(getattr(meta, "exclude", None))
```

### `test_meta_rejects_each_deferred_key` includes `"interfaces"` but `interfaces` is shipped, not deferred

`tests/types/test_base.py:196-212` parametrizes `test_meta_rejects_each_deferred_key` over six keys: `filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`, `search_fields`, **and `interfaces`**. The test docstring says "Every key in `DEFERRED_META_KEYS` must raise until the spec that owns it ships." But `DEFERRED_META_KEYS` at `base.py:48-56` lists exactly five keys (no `interfaces`); `interfaces` is in `ALLOWED_META_KEYS` at `base.py:58-69` and is shipped behavior (`_validate_interfaces` at `base.py:427-501` is the full Decision-4 validator with shape rules, duplicate detection, interface-class validation, and `DjangoType`-subclass rejection).

The test still passes for the wrong reason: the `meta_attrs = {... "interfaces": object()}` value is neither a string nor a type nor a tuple/list, so `_validate_interfaces` hits the `_interfaces_shape_error(meta, type(raw).__name__)` raise at `base.py:463` with message `"Category.Meta.interfaces must be a tuple/list of Strawberry interface classes or a single interface class, got object."`. The `match=deferred_key` regex matches the substring `"interfaces"` in the message body, so `pytest.raises` is satisfied — but for shape-validation reasons, not deferred-key reasons.

Why it matters:

1. **Test docstring contradicts shipped behavior.** A future contributor reading the parametrize block reasonably concludes that `interfaces` is in `DEFERRED_META_KEYS`, when in fact the `_validate_interfaces` code path is the entire Decision-4 validator. Cross-checking against `base.py:48-56` shows only five keys; the test is silently out of date with the production set.
2. **Wrong-reason green tests are a calibration risk.** When a future change makes `_validate_interfaces` accept `object()` (e.g. a future shape that wraps `object()` into a `(object(),)` tuple before validating per-entry), this parametrize case would start failing for the right reason, but the failure message would point at the `deferred_key` parametrize — which would be a misleading bug-hunt starting point.
3. **GLOSSARY-vs-test drift.** `docs/GLOSSARY.md:380-391` lists shipped capability for `DjangoType` and includes `Meta.interfaces` in the shipped key list at `docs/GLOSSARY.md:121` (the index line). The test stub still treats `interfaces` as deferred, which is doc-vs-test drift in the opposite direction from the usual GLOSSARY-quoted-error-string contracts — here the GLOSSARY is correct and the test is stale.

Recommended change: remove `"interfaces"` from the parametrize block at `tests/types/test_base.py:204` (drop the line, keep the other five). If a regression test for the `_validate_interfaces` shape rejection is wanted, add it as a dedicated test that asserts the actual shape-validator message (`"Meta.interfaces must be a tuple/list of Strawberry interface classes"`) rather than piggybacking on the deferred-key path. The `_validate_interfaces` raise sites at `base.py:457,463,470-474,476-478,480-484,487-491,498-500` have rich, well-shaped error messages that deserve their own parametrize block; the current "interfaces in deferred-key list" is the wrong test scope.

```tests/types/test_base.py:196-213
@pytest.mark.parametrize(
    "deferred_key",
    [
        "filterset_class",
        "orderset_class",
        "aggregate_class",
        "fields_class",
        "search_fields",
        "interfaces",
    ],
)
def test_meta_rejects_each_deferred_key(deferred_key):
    """Every key in DEFERRED_META_KEYS must raise until the spec that owns it ships."""
```

## Low:

### `_validate_optimizer_hints` "selected-relation" branch reports "unknown fields" for a known field

`_validate_optimizer_hints` at `base.py:641-650` reports excluded-or-scalar hint keys through `_format_unknown_fields_error` with `attr="optimizer_hints"` — the rendered message reads `"<Model>.Meta.optimizer_hints names unknown fields: ['name']. Available: [...]"` even when `'name'` IS a known scalar field on the model that just happens not to be a selected relation. The wording "unknown fields" is technically wrong for this branch: the field is known, it just doesn't qualify for an optimizer hint. The `available=selected_relation_names` argument also limits the "Available:" list to selected relations, so a consumer staring at the message sees their field isn't in the available list and (correctly) concludes it must be a typo — but the underlying cause is the field IS valid, just not a relation.

The test `test_meta_optimizer_hints_for_selected_scalar_field_raises` at `tests/types/test_base.py:289-296` pins the current behavior with `match="optimizer_hints names unknown fields"`, so any error-text fix is a coordinated edit (source + test).

Defer until either (a) a consumer files an error-clarity bug, OR (b) `Meta.optimizer_hints`'s GLOSSARY entry at `docs/GLOSSARY.md` (the `optimizer_hints` index line at `docs/GLOSSARY.md:123`) is rewritten to enumerate the three rejection reasons. At that point, split `_format_unknown_fields_error` into two helpers (typo path vs. "field exists but is not a selected relation" path) and update the test match strings accordingly. Today the message is wrong-shape but the consumer's debugging path (look at the field list, notice the field isn't there, realize it isn't a relation) is short, and the test pins the contract.

```django_strawberry_framework/types/base.py:641-650
    excluded_hint_fields = sorted(set(hints) - selected_relation_names)
    if excluded_hint_fields:
        raise ConfigurationError(
            _format_unknown_fields_error(
                model=model,
                attr="optimizer_hints",
                unknown=excluded_hint_fields,
                available=selected_relation_names,
            ),
        )
```

### `_consumer_assigned_fields` raises on non-`StrawberryField` shadow only for selected fields

`_consumer_assigned_fields` at `base.py:319-380` walks `fields` (the selected list from `_select_fields`) and rejects non-`StrawberryField` shadows with a `ConfigurationError`. A consumer who writes a class attribute on an EXCLUDED Django field name (e.g. `description = "something"` when `description` is in `Meta.exclude`) gets no error — the loop body short-circuits at `if field.name not in class_dict: continue` because `description` was filtered out of `fields`. This is internally consistent (only selected fields participate in synthesis), but the symmetry argument is subtle and not pinned by a test.

Defer until either (a) a consumer files a bug about excluded-field shadows silently bypassing the typo-guard, OR (b) the `_consumer_assigned_fields` docstring at `base.py:323-360` (the four-corner override contract) grows a fifth corner. At that point widen the loop to walk all Django model fields (`source_model._meta.get_fields()`) and raise on any non-`StrawberryField` shadow regardless of selection — the override-contract's "we trust the consumer's intent" promise applies to every Django field, not just selected ones. Today the asymmetry is harmless because excluded fields don't appear in the synthesized annotations dict; a class-attribute shadow on an excluded field is dead state that no downstream code reads.

### `_detect_custom_get_queryset` ignores `get_queryset` declared on `DjangoType` itself

`_detect_custom_get_queryset` at `base.py:291-298` walks `cls.__mro__` and returns `False` immediately when it hits `DjangoType` itself (line 294). This is the right shape because `DjangoType.get_queryset` IS the default and finding it should not flip the flag. But the contract is brittle in one edge: a subclass that explicitly does `get_queryset = DjangoType.get_queryset` (e.g. to "re-declare the default explicitly" or to satisfy a static-analysis lint) would put `"get_queryset"` into the subclass's own `__dict__`, and `_detect_custom_get_queryset` would return `True` at line 297 — even though the method body IS the identity hook from `DjangoType` itself.

The walker's downstream `select_related` → `Prefetch` downgrade would then trigger on a type that has no functional override, costing the consumer the per-row prefetch cost for no behavior change.

Defer until either (a) a consumer files a perf bug naming this exact shape, OR (b) the `has_custom_get_queryset` GLOSSARY contract is rewritten to mention "function-identity" semantics. At that point either (i) compare `base.get_queryset is DjangoType.get_queryset` in the walk and treat function-identity as "no override," or (ii) document the brittle edge in the `has_custom_get_queryset` docstring at `base.py:271-284` so the consumer knows to drop the explicit re-declaration. Today the trap is genuinely narrow (consumers who explicitly re-declare the default to no functional effect) and the perf cost is bounded.

### `_validate_meta` `not isinstance(model, type)` guard reads `model.__name__` before validating shape

`_validate_meta` at `base.py:551-552` validates `Meta.model` via `if not isinstance(model, type) or not issubclass(model, models.Model)`. The check is correct, but downstream `_select_fields` reads `meta.model._meta.get_fields()` at `base.py:688` and `_meta_optimizer_hints` reads `meta.model.__name__` at `base.py:395`. The `__name__` access happens only when `optimizer_hints` is declared with a non-mapping value AND model validation has already passed — so the guard ordering is correct and reachable. But the `_meta_optimizer_hints` helper is also reachable from `_validate_meta` at `base.py:584`, which runs AFTER the model-class validation at `base.py:551-552`, so the `meta.model.__name__` access cannot fault.

This is not a bug — it is a happy reading of the ordering. The defer-with-trigger is: if `_meta_optimizer_hints` ever moves to a context where `meta.model` is not pre-validated (e.g. a future helper that processes raw `Meta` introspection before model validation), the `meta.model.__name__` reference would `AttributeError` on a non-class `model` value. Add a defensive `getattr(meta.model, "__name__", repr(meta.model))` then. Today the call-order contract holds and the guard is right.

### `cls.__annotations__` rebuild at `base.py:250` loses synthesized order for consumer-overridden names

`base.py:250` does `cls.__annotations__ = {**synthesized, **consumer_annotations}`. Python dict union preserves insertion order with the right-side overriding left-side values BUT reusing the left-side key's position when overwritten — actually, per the CPython 3.7+ contract, `{**a, **b}` produces a dict where keys from `a` appear in `a`'s order, then keys from `b` not in `a` appear in `b`'s order, and any key in `b` that was also in `a` keeps `a`'s position but takes `b`'s value. So a consumer-overridden relation annotation (e.g. `items: list["AdminItemType"]`) keeps the position the synthesized walker assigned, which is Django's `_meta.get_fields()` order.

This is correct today (the GraphQL field order follows Django's declared order, which is the contract). But the dict-union ordering rule is subtle and not documented at the call site — a future refactor that changes to `cls.__annotations__ = consumer_annotations | synthesized` (or `dict(consumer_annotations, **synthesized)`) would flip the order silently. Defer until a third reader of `cls.__annotations__` ordering lands (e.g. an introspection helper that snapshots GraphQL field order); at that point add a one-line comment at `base.py:250` documenting the order contract verbatim, citing the CPython dict-union semantics.

## What looks solid

### DRY recap

- **Existing patterns reused.** `_format_unknown_fields_error` at `base.py:401-409` is the single source of truth for "unknown field name" error formatting — consumed by `_select_fields` (`base.py:697-704` for `Meta.fields` typos, `base.py:707-716` for `Meta.exclude` typos) and `_validate_optimizer_hints` (`base.py:632-640` for hint-key typos, `base.py:641-650` for non-relation hint targets). The four call sites converge on the same `"<Model>.Meta.<attr> names unknown fields: <list>. Available: <set>."` shape so consumer-visible typo messages stay grep-able. `_interfaces_shape_error` at `base.py:417-424` centralizes the long lead-in `_INTERFACES_SHAPE_ERROR_LEAD_IN` at `base.py:412-414` for the two `_validate_interfaces` raise sites that share the wording. `_is_relay_shaped` at `base.py:132-143` is the single predicate consumed by both the H1 Relay-id collision guard at `base.py:194` (class-creation timing) AND the synthesized-pk suppression branch at `base.py:798` (annotation-synthesis timing), preventing the two computations from drifting. `snake_case` from `..utils.strings` keys the `field_map` at `base.py:174`, matching the snake_case key contract that `optimizer/walker.py:175-176`, `types/finalizer.py:192`, and `types/resolvers.py:179` all rely on. `_meta_optimizer_hints` at `base.py:383-398` centralizes the `Meta.optimizer_hints`-as-mapping shape gate so `__init_subclass__` and `_validate_meta` cannot drift on the rejection message.
- **New helpers considered.** Three are surfaced as DRY analysis entries above: (a) folding `name` and `description` `getattr` reads into `_ValidatedMeta` (deferred until a third nested helper); (b) hoisting the `isinstance(value, str) or not isinstance(value, Sequence)` shape-guard out of `_normalize_fields_spec` and `_normalize_sequence_spec` (deferred until `Meta.search_fields` lands); (c) splitting `_format_unknown_fields_error` into typo vs. invalid-target shapes (deferred to error-clarity bug or GLOSSARY rewrite). The `_select_fields` re-normalization is promoted to Medium because the `_ValidatedMeta` docstring states the eliminated-duplication invariant explicitly.
- **Duplication risk in the current file.** Repeated string literals (per shadow overview) are `optimizer_hints` (4x — used as the `attr=` kwarg to `_format_unknown_fields_error` at two sites plus the dict-key reads), `description` (2x — class docstring + `Meta.description` `getattr` at `base.py:232`), and `interfaces` (2x — class docstring + `Meta.interfaces` `getattr` at `base.py:453`). All three are local string-keyed dispatch, not cross-file drift candidates. The four-corner override contract names (`consumer_annotated_relation_fields`, `consumer_assigned_relation_fields`, `consumer_annotated_scalar_fields`, `consumer_assigned_scalar_fields`) at `base.py:176-193` are the intentional parallel that `DjangoTypeDefinition.consumer_*` stores as separate introspection attributes — the parallel is the contract, not drift.

### Other positives

- Carry-forward from `rev-optimizer__field_meta.md` Low 2 (snake_case-keyed dict-comprehension at `base.py:174` silently collapses key collisions): the trigger-gated deferral is restated verbatim here. Trigger: **either (a) Django relaxes its field-name uniqueness rule on `Meta.fields`, OR (b) a consumer files a bug where two columns collide on snake-cased names**. On trigger fire: replace the dict-comprehension at `base.py:174` with an explicit loop that raises `ConfigurationError` on key collision, naming both offending Django field names. Today contained by Django's own `_meta` field-name validation; the snake_case keying contract spans walker / finalizer / resolvers and is internally consistent.
- The H1 Relay-id collision guard at `base.py:194-219` (with the four-corner failure-mode prose in the `ConfigurationError` message) is a textbook example of consumer-visible error quality: the message names the bad construct, the legitimate alternatives (`@classmethod resolve_id`, `id: relay.NodeID[<pk_type>]`, resolver-backed sibling), AND the exit hatch ("remove `relay.Node` from `Meta.interfaces`"). Tests pin both branches: `has_id_assignment` raise + `has_id_annotation and not _id_annotation_is_relay_node_id(cls)` raise.
- The `_is_default_get_queryset` sentinel-flip-before-early-return ordering at `base.py:154-164` is pinned by the explicit comment block at `base.py:154-159` AND by the `test_has_custom_get_queryset_inherits_through_abstract_base_without_meta` regression at `tests/types/test_base.py:609-642`. The comment block names the regression test, making the invariant grep-able from both sides.
- `_id_annotation_is_relay_node_id` at `base.py:90-129` collapses the prior 3.10-vs-3.11 `typing.get_type_hints` divergence into a single reliable shape (reads `cls.__annotations__` directly, dispatches on `isinstance(raw, str)`). The docstring at `base.py:91-125` explicitly calls out the precondition (`"id" in cls.__annotations__`) and the only call site's pre-gate — a future caller violating the precondition gets a loud `KeyError` rather than a misleading `False`.
- The `_validate_interfaces` Decision-4 validator at `base.py:427-501` handles every rejection axis explicitly with rich, well-shaped error messages: string entries, non-class entries, `DjangoType` self-reference, non-Strawberry-interface classes, and duplicate detection. Each raise names the offending entry and the surface reason. The composite-pk + `relay.Node` MRO inspection is correctly deferred to `finalize_django_types()` (Relay finalization phase) per the docstring at `base.py:448-451`.
- The `cls.__annotations__ = {**synthesized, **consumer_annotations}` rebuild at `base.py:250` correctly preserves consumer-supplied annotations as overrides; the dict-union order is the right shape (consumer overrides win, but synthesized order survives for non-overridden keys).
- The `convert_scalar(field, cls.__name__)` call at `base.py:857` threads `cls.__name__` through so generated choice enums carry a stable name. The contract is documented at `base.py:756-757`.
- The `getattr(field, "related_model", None) is None` guard at `base.py:813` correctly rejects GenericForeignKey and other relation shapes that cannot auto-map; the error names the source model, the field name, the legitimate alternative (`Meta.exclude`), and the override path (explicit annotation/resolver). `tests/types/test_generic_foreign_key.py` covers the contract.
- `_consumer_assigned_fields` at `base.py:319-380` returns BOTH relation and scalar four-corner sets as `frozenset[str]` (immutable) and the loop's "non-StrawberryField shadow" raise at `base.py:374-379` produces a uniform error shape across scalar and relation columns. The docstring at `base.py:323-359` explicitly enumerates the four corners with grep-able names.
- Test discipline: `tests/types/test_base.py` covers Meta validation (required model, mutually-exclusive specs, deferred-key rejection, unknown-key rejection, typo paths), `primary` boolean semantics (including the `isinstance(1, bool) is False` int-trap defense at `test_meta_primary_non_bool_raises_configuration_error`), and the `_is_default_get_queryset` sentinel-flip path with the abstract-base regression. Relation tests cover forward FK, reverse FK, list widening, unregistered-target rejection at finalization, and the full chain. The four-corner override contract is exercised end-to-end via the consumer-assigned-field tests in adjacent `test_resolvers.py` / `test_converters.py`.
- The `__init_subclass__` runs `registry.register_with_definition(...)` at `base.py:247` BEFORE the `cls.__annotations__` rebuild at `base.py:250` AND BEFORE `install_is_type_of(cls)` at `base.py:252`. A `ConfigurationError` raised by the registry (primary collision) propagates out of `__init_subclass__` so the consumer's class creation fails atomically — no half-registered state.

### Summary

`types/base.py` is the largest file in `types/` (858 lines) and the structural heart of the framework's consumer-facing API. The factoring is mature: the four-corner override contract is fully pinned, the Relay-id collision guard handles every failure axis with rich error messages, the `_ValidatedMeta` snapshot pattern (and `_format_unknown_fields_error` helper) consolidate the Meta validation surface, and the abstract-base sentinel-flip ordering is pinned by both comment and regression test. Two real findings this cycle: one Medium for the `_select_fields` re-normalization that contradicts `_ValidatedMeta`'s stated invariant (act-now signature change with one call-site update); one Medium for the stale `tests/types/test_base.py:196-212` parametrize block that includes `"interfaces"` in a `DEFERRED_META_KEYS` test docstring even though `interfaces` is shipped — the test passes coincidentally because the shape-validation message contains the substring `"interfaces"`, not because the key is in the deferred set. Five trigger-gated Lows are forward-looking and defend intentional shapes from false-positive future reviewers. The Low forwarded from `rev-optimizer__field_meta.md` (the `base.py:174` `snake_case` collision-tolerant dict-comprehension) is restated verbatim in `### Other positives` with the original trigger condition preserved.

---

## Fix report (Worker 2)

### Files touched
- `django_strawberry_framework/types/base.py:171` — call-site update: `_select_fields(meta.model, validated.fields_spec, validated.exclude_spec)` (threads the validated specs from the `_ValidatedMeta` snapshot rather than re-reading `meta.fields`/`meta.exclude`).
- `django_strawberry_framework/types/base.py:659-694` — `_select_fields` signature change from `(meta: type)` to `(model: type[models.Model], fields_spec: tuple[str, ...] | str | None, exclude_spec: tuple[str, ...] | None)`. Dropped the two `_normalize_*` re-runs and the `model = meta.model` line; body downstream uses the passed-in `model`/`fields_spec`/`exclude_spec` unchanged. Docstring updated inline to describe the new signature (the contract IS the signature here, so the docstring landed with the logic diff — the `_ValidatedMeta` snapshot invariant promise is now restated in the helper docstring itself).
- `tests/types/test_base.py:196-205` — M2: dropped `"interfaces"` from the `test_meta_rejects_each_deferred_key` parametrize list (was passing for the wrong reason because the `_validate_interfaces` shape-error message contains the substring `"interfaces"`).
- `tests/types/test_base.py:208-227` — M2 positive case: new `test_interfaces_is_shipped_not_deferred` asserts `"interfaces" in ALLOWED_META_KEYS` and `"interfaces" not in DEFERRED_META_KEYS`. Guards against future regressions of the same shape.
- `tests/types/test_base.py:230-249` — M1 regression test: new `test_select_fields_signature_accepts_validated_specs` calls `_select_fields(...)` directly with the new signature and pins (a) `(None, None)` -> all fields, (b) `(("id", "name"), None)` -> narrowed, (c) `(None, ("description",))` -> excluded.

### Tests added or updated
- `tests/types/test_base.py::test_select_fields_signature_accepts_validated_specs` — M1 direct-call contract regression.
- `tests/types/test_base.py::test_interfaces_is_shipped_not_deferred` — M2 positive assertion against the deferred/allowed key sets.
- `tests/types/test_base.py::test_meta_rejects_each_deferred_key[interfaces]` — removed parametrize case (was wrong-reason green).

### Validation run
- `uv run ruff format .` — pass / 118 files left unchanged.
- `uv run ruff check --fix .` — pass / all checks passed.
- No pytest run per `AGENTS.md` standing rule (formatting only).

### Notes for Worker 3
- No shadow file used during the edit.
- Stale `_select_fields(meta)` docstring references survive at `django_strawberry_framework/types/base.py:750` (`_build_annotations` docstring naming the precomputation step) and `django_strawberry_framework/types/resolvers.py:19` (module docstring naming the precomputation step). Both are docstring-only references to the new signature's *caller-side* shape, not the helper's own signature. Per Worker 2 dicta ("Do not update comments before logic is approved") these will be addressed in the comment pass — flagged here so Worker 3's first verification scan can confirm the intentional carry-forward.
- All five Lows are explicitly trigger-gated forward-looking per Worker 1's own prose ("Defer until …" framing on each). No in-cycle source edits required; verbatim trigger conditions per Low:
  - **L1** (`_validate_optimizer_hints` "unknown fields" wording for known-but-non-relation field at `base.py:641-650`): trigger = "either (a) a consumer files an error-clarity bug, OR (b) `Meta.optimizer_hints`'s GLOSSARY entry at `docs/GLOSSARY.md` (the `optimizer_hints` index line at `docs/GLOSSARY.md:123`) is rewritten to enumerate the three rejection reasons". On fire: split `_format_unknown_fields_error` into typo vs. invalid-target shapes and update the matching tests at `tests/types/test_base.py:289-296`.
  - **L2** (`_consumer_assigned_fields` raises on shadow only for selected fields at `base.py:319-380`): trigger = "either (a) a consumer files a bug about excluded-field shadows silently bypassing the typo-guard, OR (b) the `_consumer_assigned_fields` docstring at `base.py:323-360` (the four-corner override contract) grows a fifth corner".
  - **L3** (`_detect_custom_get_queryset` ignores `get_queryset = DjangoType.get_queryset` re-declaration at `base.py:291-298`): trigger = "either (a) a consumer files a perf bug naming this exact shape, OR (b) the `has_custom_get_queryset` GLOSSARY contract is rewritten to mention 'function-identity' semantics". On fire: either compare `base.get_queryset is DjangoType.get_queryset` in the walk or document the brittle edge in the `has_custom_get_queryset` docstring at `base.py:271-284`.
  - **L4** (`_meta_optimizer_hints` `meta.model.__name__` access depends on validation order at `base.py:551-552`/`584`/`395`): trigger = "if `_meta_optimizer_hints` ever moves to a context where `meta.model` is not pre-validated (e.g. a future helper that processes raw `Meta` introspection before model validation)". On fire: add `getattr(meta.model, "__name__", repr(meta.model))` defensively.
  - **L5** (`cls.__annotations__` rebuild at `base.py:250` dict-union ordering is subtle): trigger = "a third reader of `cls.__annotations__` ordering lands (e.g. an introspection helper that snapshots GraphQL field order)". On fire: add a one-line comment at `base.py:250` documenting the CPython dict-union order contract verbatim.
- DRY bullets restated for grep-discovery during future cycles:
  - **DRY-1** (eight `getattr(meta, ...)` reads convergent on the snapshot pattern): trigger = "a third nested helper needs to read the same pre-validated `meta` instance". On fire: fold `name`/`description` into `_ValidatedMeta` alongside the existing five fields.
  - **DRY-2** (`_normalize_fields_spec` / `_normalize_sequence_spec` parallel shape-guard): trigger = "a third optional-sequence Meta key lands (`Meta.search_fields` per spec roadmap)". On fire: hoist `_reject_non_sequence_spec(value, *, attr)` shared helper.
  - **DRY-3** (`_format_unknown_fields_error` mis-shaped re-use for selected-but-non-relation hints at `base.py:641-650`): trigger = "either a consumer-visible error-clarity bug is filed OR the `Meta.optimizer_hints` GLOSSARY entry is rewritten". On fire: split into `_format_unknown_fields_error` (real typos) and `_format_invalid_hint_target_error` (field exists but is not a selected relation). Same trigger as L1.
- No false-premise rejections this pass.

---

## Verification (Worker 3)

### Logic verification outcome

- **M1** (`_select_fields` re-normalization): accepted. `git diff -- django_strawberry_framework/types/base.py` shows the signature change verbatim — `def _select_fields(model: type[models.Model], fields_spec: tuple[str, ...] | str | None, exclude_spec: tuple[str, ...] | None) -> tuple[Any, ...]:` at line 659. Both `_normalize_fields_spec` and `_normalize_sequence_spec` calls in the body removed (former lines 685-686 now absent). Call site at `base.py:171` updated to `_select_fields(meta.model, validated.fields_spec, validated.exclude_spec)`. Docstring updated to reference `model._meta.get_fields()` and the new spec parameter names, plus the inline restatement of the `_ValidatedMeta` invariant promise (matches Worker 1's "stated invariant violated" finding). Body downstream uses passed-in `model`/`fields_spec`/`exclude_spec` unchanged.
- **M2** (`test_meta_rejects_each_deferred_key` includes shipped `"interfaces"`): accepted. `git diff -- tests/types/test_base.py` shows `"interfaces"` removed from the parametrize list (one-line deletion at line 204). New `test_interfaces_is_shipped_not_deferred` (lines 214-227) asserts the positive case: `"interfaces" in ALLOWED_META_KEYS` and `"interfaces" not in DEFERRED_META_KEYS`. Docstring cites the prior wrong-reason-green failure mode verbatim. New `test_select_fields_signature_accepts_validated_specs` (lines 230-249) pins the M1 contract with three direct-call cases: `(Category, None, None)` returns ≥ all scalar fields, `(Category, ("id", "name"), None)` narrows to the tuple, `(Category, None, ("description",))` excludes the named field while keeping `"name"`.
- **L1-L5**: accepted as forward-looking. Worker 2's `### Notes for Worker 3` block at artifact lines 173-178 preserves each Low's verbatim trigger phrasing including all disjunctive arms. L1 two-arm ((a) consumer files error-clarity bug OR (b) GLOSSARY entry rewrite enumerating three rejection reasons) preserved at artifact line 174. L2 two-arm ((a) consumer bug about excluded-field shadows OR (b) docstring grows a fifth corner) preserved at line 175. L3 two-arm ((a) consumer perf bug OR (b) `has_custom_get_queryset` GLOSSARY rewrite for function-identity semantics) preserved at line 176. L4 single conditional trigger preserved at line 177. L5 trigger (third reader of `cls.__annotations__` ordering) preserved at line 178. Cross-checked against Worker 1's Low prose at artifact lines 80-82, 99-101, 105-109, 113-115, 118-121 — all match.

### DRY findings disposition

Three DRY observations restated by Worker 2 in `### Notes for Worker 3` at artifact lines 180-182 with verbatim trigger phrasing: DRY-1 (eight `getattr(meta, ...)` reads, defer until third nested helper), DRY-2 (`_normalize_*` parallel shape-guard, defer until `Meta.search_fields` lands), DRY-3 (`_format_unknown_fields_error` mis-shape, same trigger as L1). The original Medium-promoted DRY observation (`_select_fields` re-normalization) was implemented as M1 above. No carry-forward edits needed.

### Temp test verification

- No temp test files needed; the diff is small and Worker 2's three new permanent regression-test cases (`test_interfaces_is_shipped_not_deferred`, `test_select_fields_signature_accepts_validated_specs` direct-call) provide the contract pins inline. The integrated path through `__init_subclass__` is already covered by the existing module-level tests (per Worker 1's recommendation at artifact line 31).

### Verification outcome

`logic accepted; awaiting comment pass`

Stale `_select_fields(meta)` docstring references at `django_strawberry_framework/types/base.py:750` (`_build_annotations`) and `django_strawberry_framework/types/resolvers.py:19` (module docstring) flagged by Worker 2 in `### Notes for Worker 3` (artifact line 172) as intentional carry-forward to the comment pass per the "Do not update comments before logic is approved" dicta. Confirmed both sites are caller-side shape references, not the helper's own signature — the comment pass owns them. `git diff -- CHANGELOG.md` empty (will be re-checked against the disposition state in the final pass). Ruff `format --check` passes (118 files unchanged); ruff `check` passes (all checks passed). Top-level `Status:` line stays `fix-implemented (awaiting comment pass)` per Worker 2's interim-pass convention.

---

## Comment/docstring pass

### Files touched
- `django_strawberry_framework/types/base.py:750-754` — `_build_annotations` docstring: updated the caller-side reference from `_select_fields(meta)` to `_select_fields(model, fields_spec, exclude_spec)` and named the `_ValidatedMeta` snapshot as the spec source so the precomputation step's contract reads correctly post-M1.
- `django_strawberry_framework/types/resolvers.py:18-20` — module docstring: updated the caller-side reference from `base._select_fields(meta)` to `base._select_fields(model, fields_spec, exclude_spec)` to mirror the new signature for the sibling-import precomputation note.

### Per-finding dispositions
- **M1** (`_select_fields` re-normalization, logic pass): comment work for the helper's own docstring landed inside the logic pass diff (the contract IS the signature). This comment pass addresses the two sibling-file docstrings that referenced the old caller-side shape — both updated to the new three-arg signature.
- **M2** (`test_meta_rejects_each_deferred_key` includes `"interfaces"`, logic pass): no-op for the comment pass. The new positive-case test docstring landed with the M2 logic diff; the parametrize block deletion needed no docstring edit.
- **L1-L5**: no-op for the comment pass. All five Lows are explicitly trigger-gated forward-looking per Worker 1's "Defer until …" framing; no in-cycle docstring edits implied. Verbatim triggers preserved in `## Fix report (Worker 2)` `### Notes for Worker 3` (lines 173-178).
- **DRY-1 / DRY-2 / DRY-3**: no-op for the comment pass. Same trigger-gated forward-looking shape as the Lows; verbatim triggers preserved in `## Fix report (Worker 2)` `### Notes for Worker 3` (lines 180-182).

### Validation run
- `uv run ruff format .` — pass / 118 files left unchanged.
- `uv run ruff check --fix .` — pass / all checks passed.

### Notes for Worker 3
Sweep beyond the two flagged sites: `grep -rn "_select_fields(meta" --include="*.py" --include="*.md"` returns only the two sibling-file docstrings (now updated), the `base.py:171` call site (already in the new shape with three args), and the artifact's own restatement of Worker 1's recommendation prose. No additional stale references in source, tests, or docs/GLOSSARY. The CHANGELOG.md disposition is batched into this same spawn per the dispatch prompt — see `## Changelog disposition` below.

---

## Changelog disposition

### State
`Not warranted`.

### Reason
- `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed").
- The active plan `docs/review/review-0_0_7.md` is silent on changelog authorization for this cycle.
- M1 is an internal refactor with no consumer-visible behaviour change (the helper is private, the call site is private, and both normalizers still raise identically — the second raise site simply collapses into the first); M2 is a test-only fix (parametrize-block correction plus a new positive-case assertion) with no source-side behaviour change. Per the cycles 2-12 / 13-19 0.0.7 precedent chain (now nineteen `Not warranted` calls deep), internal-only refactors plus test-only fixes are the canonical `Not warranted` shape — the chain depth itself dominates.

### What was done
No `CHANGELOG.md` edit.

### Validation run
- `uv run ruff format .` — pass / 118 files left unchanged.
- `uv run ruff check --fix .` — pass / all checks passed.

---

## Iteration log

## Verification (Worker 3, pass 2)

### Comment-pass logic verification
- `git diff -- django_strawberry_framework/types/base.py django_strawberry_framework/types/resolvers.py` confirms the comment-pass touches exactly the two flagged docstring sites Worker 2 carry-forwarded from pass 1: `base.py:747-753` (`_build_annotations` docstring) updated from `_select_fields(meta)` to `_select_fields(model, fields_spec, exclude_spec)` with the `_ValidatedMeta` snapshot reference; `resolvers.py:18-20` module docstring updated to the same three-arg shape. The M1 logic-pass hunks at `base.py:171` and `base.py:659-694` remain intact and unmodified — comment-pass diff is additive to the prior verified logic diff.
- Cross-folder grep `_select_fields(meta)` finds no remaining stale references in source, tests, or `docs/GLOSSARY.md`; only `docs/shadow/` (regenerable, out-of-scope per Worker 3 dicta) and the artifact's own historical prose retain the old shape. All Lows (L1-L5) and DRY observations (DRY-1, DRY-2, DRY-3) remain explicitly forward-looking per Worker 1's "Defer until …" framing; no in-cycle comment edits implied for any of them, and Worker 2's `### Per-finding dispositions` correctly records each as a no-op.

### Changelog verification
- `git diff -- CHANGELOG.md` empty. Disposition `Not warranted` cites the three-leg framework: `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed"), plan silence on changelog authorization for this cycle, and the twenty-cycle 0.0.7 precedent chain (this cycle is the twentieth). M1 is an internal refactor with no consumer-visible behaviour change (private helper, private call site, both normalizers still raise identically — the second raise site collapses into the first); M2 is a test-only fix (parametrize-block correction plus positive-case assertion) with no source-side behaviour change. Internal-only framing matches the diff scope.

### Validation
- `uv run ruff format --check .` — pass / 118 files already formatted.
- `uv run ruff check .` — all checks passed.

### Verification outcome
`cycle accepted; verified` — top-level `Status: verified`, `docs/review/review-0_0_7.md:117` checkbox for `types/base.py` ticked.
