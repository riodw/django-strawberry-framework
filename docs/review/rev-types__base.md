# Review: `django_strawberry_framework/types/base.py`

Status: verified

Supersedes the on-disk 0.0.7 artifact (was `Status: verified`, referenced `review-0_0_7.md`). Replaced wholesale per the stale-artifact pattern; the active plan box (`review-0_0_9.md`) is unchecked. Live source diffed; no prior-cycle Low re-raised.

## DRY analysis

- **`_is_relay_shaped(cls, interfaces)` recomputed three times in one class-creation path.** Same `(cls, validated.interfaces)` inputs yield the same boolean at `_validate_meta` (`types/base.py:1077`), `__init_subclass__` (`types/base.py:567`), and `_build_annotations` (`types/base.py:1551`). The predicate is intentionally single-sourced as a function (its docstring at `types/base.py:443-454` calls itself "single source of truth"), but the *value* is derived three times per subclass. Act-now-optional: add a `relay_shaped: bool` field to `_ValidatedMeta` (set from the `_validate_meta`-local computation), then read `validated.relay_shaped` at the `__init_subclass__` call site and thread it into `_build_annotations`. Collapses three derivations to one and matches the `_ValidatedMeta` docstring's own promise ("keeps the caller from re-reading ... and avoids re-running the shape gates ... at multiple sites"). Low value (the call is two cheap `issubclass`/`any` walks over a tiny tuple), so a defer is also defensible — **defer until `_validate_meta` gains a fourth `relay_shaped` consumer, then thread the bool through `_ValidatedMeta`.**
- **`_selected_meta_targets` already factors the shared unknown/excluded guard.** The two stage-2 target validators (`_validate_nullability_override_targets`, `_validate_relation_shape_targets`) correctly delegate the model-wide-unknown + not-selected checks to the shared `_selected_meta_targets` helper (`types/base.py:1192-1232`), keeping only domain-specific per-name checks local. This is the right factoring for the 0.0.9 override/relation-shape additions — no further consolidation warranted; the per-name checks are genuinely family-specific (scalar-only/Relay-pk vs non-relation/single-valued).

## High:

None.

## Medium:

None.

## Low:

### Module docstring `Meta` option list is incomplete for 0.0.9

The module docstring (`types/base.py:10-13`) enumerates the supported `Meta` options as `fields`, `exclude`, `name`, `description`, `optimizer_hints`, `interfaces`, `nullable_overrides`, `required_overrides` — but omits the other six keys in `ALLOWED_META_KEYS` (`types/base.py:64-82`): `connection`, `filterset_class`, `globalid_strategy`, `orderset_class`, `primary`, `relation_shapes`. Three of those (`globalid_strategy`, `relation_shapes`, `connection`) are net-new 0.0.9 surface this same docstring's module is centered on. Non-contract (the GLOSSARY is the contract surface and is current; this is the module's own inventory comment), so Low. Recommend listing all twelve `ALLOWED_META_KEYS` entries, or rephrasing to "see `ALLOWED_META_KEYS`" so the prose cannot drift from the frozenset again.

### `_ValidatedMeta` docstring "Returns" omits the 0.0.9 fields

`_validate_meta`'s docstring "Returns" paragraph (`types/base.py:1021-1027`) describes the snapshot as bundling only "the validated interfaces tuple, the `primary` bool, the normalized `optimizer_hints` dict, and the normalized `fields`/`exclude` specs." The actual `_ValidatedMeta` NamedTuple (`types/base.py:978-989`) carries seven more fields shipped in 0.0.9: `filterset_class`, `orderset_class`, `connection`, `globalid_strategy`, `relation_shapes`, `nullable_overrides`, `required_overrides`. Stale-but-harmless (the NamedTuple field list is self-documenting and the validator body is correct); Low. Recommend extending the "Returns" sentence to name the 0.0.9 fields, or pointing at the NamedTuple definition.

## What looks solid

### DRY recap

- **Existing patterns reused.** Stage-2 target validators delegate the shared unknown/excluded guard to `_selected_meta_targets` (`types/base.py:1192-1232`); both unknown-field paths route through `_format_unknown_fields_error` (`types/base.py:798-812`) so the consumer-visible typo-guard shape matches `Meta.fields`/`Meta.exclude`/`Meta.optimizer_hints`. The Relay-Node gate text is single-sourced: `_RELAY_NODE_GATE_LEAD` + `_RELAY_NODE_GATE_INHERIT_TAIL` (`types/base.py:104-110`) compose at the `connection`/`globalid_strategy` gates, and `_validate_relation_shapes` appends the spec-pinned "or remove the key." tail — the comment block at `types/base.py:98-109` correctly documents which compose sites share which literal. The vocabulary frozensets (`RELATION_SHAPE_VALUES`/`DEFAULT_RELATION_SHAPE` at 95-96; `STRING_GLOBALID_STRATEGIES`/`DEFAULT_GLOBALID_STRATEGY` at 119-120) are single-sourced for validator text + finalizer default + consumer error text.
- **New helpers considered.** A `relay_shaped`-on-`_ValidatedMeta` field was evaluated to collapse the three-site recomputation (see DRY analysis) — deferred on cost/benefit. No other new helper warranted: the four `_validate_*` shape validators (`_validate_connection`/`_validate_relation_shapes`/`_validate_globalid_strategy`/`_validate_interfaces`) share a deliberate structural template (`None`-short-circuit → shape-check → Relay-gate) but differ enough in body that a meta-validator abstraction would be less readable, not more.
- **Duplication risk in the current file.** The `model._meta.get_fields()` walk appears in `_validate_optimizer_hints`, `_selected_meta_targets`, and `_select_fields` — but each derives a different name set (model-wide valid names vs selected-relation names vs selection filter) at a different pipeline stage, so they are not collapsible. The two `getattr(meta, ...)` vs `meta.__dict__` membership idioms in `_validate_meta` are intentionally distinct (MRO-walking vs own-keys-only) and the comment at `types/base.py:1038-1044` explicitly warns against unifying them.

### Other positives

- **Two-stage override/relation-shape validation is correct and well-justified.** Shape + both-sets collision run at `_validate_meta` time (visible from raw `Meta` alone: `types/base.py:1099-1111`); target existence/scope checks defer to `__init_subclass__` after `_select_fields` + `consumer_authored_fields` + `relay_shaped` exist (`_validate_nullability_override_targets` 1235-1322, `_validate_relation_shape_targets` 1325-1393). The both-sets collision raising at the shape stage (no model access needed) is the right placement.
- **`relation_shapes` cardinality is read from the single-source classifier.** `_validate_relation_shape_targets` keys on `field_map[snake_case(name)].is_many_side` (`types/base.py:1381`) — the same `FieldMeta.is_many_side` property the resolvers and Phase-2.5 synthesis use — so the validator and synthesis cannot disagree about connection-eligibility. The `snake_case(name)` lookup is identity for real Django field names (always snake_case), so it agrees with the raw-`name`-keyed `selected_by_name` map; no key-mismatch bug.
- **`isinstance`-before-set-membership ordering in `_validate_relation_shapes`** (`types/base.py:261`, comment 257-260) correctly prevents an unhashable shape value (`{"items": ["both"]}`) from leaking `TypeError: unhashable type` out of the set membership — it raises the configured `ConfigurationError` instead. Good edge-case hardening (spec-032 feedback P3).
- **`_validate_globalid_callable` uses `is_async_callable`, not `inspect.iscoroutinefunction`** (`types/base.py:360`, docstring 346-359) — correctly catches `async def __call__` instances and `functools.partial` wrappers an `iscoroutinefunction`-only check would miss, promoting an opaque per-request `TypeError`/coroutine to a build-time `ConfigurationError`. The shared sync-ness helper matches the field factories (avoids the `list_field.py` comment-vs-code drift noted in prior memory).
- **`globalid_strategy` validator's `source`-parameterized error framing** (`types/base.py:287-343`) cleanly single-sources one validator across the `Meta` path and the `RELAY_GLOBALID_STRATEGY` setting path with source-specific subject text and a `Meta`-only Relay gate — exactly the "one validator, two sources" rule.
- **Relay `id`-collision guard correctness** (`__init_subclass__` 583-607): assigned-`StrawberryField` rejected with a thorough remediation message; annotation accepted only when `_id_annotation_is_relay_node_id` confirms `relay.NodeID[...]` shape. The string-form regex `_NODEID_STRING_RE` (`types/base.py:381`) anchors on `(?:^|\.)` to reject prefixed lookalikes (`NotNodeID[`) — and reads `cls.__annotations__` directly (no `get_type_hints`) so an unresolved sibling forward-ref cannot mask `id` and behavior is interpreter-version-stable (docstring 399-436, pinned by `test_definition_order.py`).
- **`_is_default_get_queryset` sentinel stamped before the `meta is None` early return** (`__init_subclass__` 465-472) so an abstract base overriding `get_queryset` without a `Meta` still flips the flag and concrete subclasses inherit it — pinned by `test_has_custom_get_queryset_inherits_through_abstract_base_without_meta`.
- **Import-time side effects are bounded and safe.** Module scope only compiles one regex (`_NODEID_STRING_RE`), builds frozensets/tuples of literals, and imports first-party leaves; the `FilterSet`/`OrderSet` validators use documented in-function imports (`types/base.py:139,167`) to dodge the `types -> filters/orders -> types` module-load cycle — correctly NOT hoisted. The finalized-registry guard (`__init_subclass__` 476-480) raises a clear `ConfigurationError` on post-finalization registration.
- **GLOSSARY is accurate.** `#metanullable_overrides` / `#metarequired_overrides` validation tables list exactly the six failure modes the source raises (unknown/excluded/consumer-authored/relation/Relay-pk/both-sets); `#metarelation_shapes` matches both validation stages (shape/Relay-gate + non-relation/single-valued/consumer-authored/unknown/excluded) and the `"list"`/`"connection"`/`"both"` vocabulary with `"both"` default; `#metaglobalid_strategy` matches the string-set + callable + Relay-gate + precedence chain; `#djangotype` accurate. No drift — no verbatim replacement text needed.

### Summary

`types/base.py` is the public-API core — the `__init_subclass__` collection pipeline plus its `Meta` validators — and it holds up rigorously. The 0.0.9 additions (`nullable_overrides`/`required_overrides`, `relation_shapes`, `globalid_strategy`, the `DEFERRED_META_KEYS`/`ALLOWED_META_KEYS` partition) are correctly two-staged (raw-`Meta` shape checks in `_validate_meta`, field-scope checks deferred to `__init_subclass__` once selected fields exist), single-source their vocabularies and error-text lead-ins, and route every typo through the shared `_format_unknown_fields_error`. No High or Medium findings: validation completeness is full (every override/relation-shape failure mode — unknown/excluded/consumer-authored/relation-or-non-relation/single-valued/Relay-suppressed-pk/both-sets-collision — raises `ConfigurationError` with a field-naming message), the relation-shape cardinality classifier is single-sourced against synthesis, and the `globalid_strategy` callable async-guard uses the correct `is_async_callable` seam. Two comment-tier Lows (module docstring + `_ValidatedMeta` docstring "Returns" both lag the 0.0.9 key set) and one optional DRY candidate (`_is_relay_shaped` recomputed three times per class creation). The two Lows want a real docstring edit, so this is a standard cycle, not shape #5.

---

## Fix report (Worker 2)

Consolidated single-spawn: both Lows are comment-tier (docstring-only, NO logic change); the DRY bullet is defer-with-trigger and left untouched. Logic + comment + changelog disposition collapsed into one pass.

### Files touched
- `types/base.py:10-15` — module docstring `Meta`-option enumeration extended from 8 to the full optional set (added `connection`, `filterset_class`, `orderset_class`, `globalid_strategy`, `relation_shapes`, `primary`) and anchored with "see ``ALLOWED_META_KEYS`` for the authoritative set" to stop future drift. `model` stays implicit (it is the required base, not an optional key). Confirmed against the live `ALLOWED_META_KEYS` frozenset at `types/base.py:64-82` (15 entries; the 14 non-`model` optional keys = the 8 already listed + the 6 added).
- `types/base.py:1024-1035` — `_validate_meta` "Returns" paragraph extended to name the seven 0.0.9 fields the `_ValidatedMeta` NamedTuple actually carries (`filterset_class`/`orderset_class`/`connection`/`globalid_strategy`/`relation_shapes` sidecars + `nullable_overrides`/`required_overrides` frozensets) and anchored with "see the ``_ValidatedMeta`` definition for the authoritative field list". Confirmed against the NamedTuple field list at `types/base.py:978-989`.

### Tests added or updated
- None. Docstring-only change, no behaviour change; no test surface to pin (consistent with the artifact's "comment-tier Low" framing).

### Validation run
- `uv run ruff format .` — pass (265 files unchanged)
- `uv run ruff check --fix .` — pass (All checks passed)
- `git diff --stat 0872a20` for `types/base.py` — `13 +-`, all inside the two docstrings; confirmed docstring-only via full `git diff` (no code lines touched).

### Notes for Worker 3
- Shadow file used: `docs/shadow/django_strawberry_framework__types__base.overview.md` (overview only; cited original source line numbers throughout).
- `ALLOWED_META_KEYS` confirmed at `types/base.py:64-82`; `_ValidatedMeta` NamedTuple confirmed at `types/base.py:978-989` — both before editing.
- Lower-drift choice per the artifact's two-option offer + AGENTS.md "pick the lower-drift option that matches local idiom": kept the human-readable enumeration (local idiom for this consumer-surface module docstring and the `_validate_meta` Returns prose) AND added a source-of-truth pointer to each site so the prose cannot silently re-drift from the frozenset / NamedTuple.
- Working tree carries unrelated concurrent edits (other base.py-adjacent files, GLOSSARY, other rev-*.md, example tests); per AGENTS.md #33 left untouched. base.py itself had NO prior concurrent edit — the full 13-line diffstat vs baseline is exactly these two docstring edits.
- `uv.lock` not modified.
- DRY bullet (`_is_relay_shaped` recomputed 3x) intentionally left per its defer-with-trigger disposition (thread `relay_shaped` through `_ValidatedMeta` only when a fourth consumer appears).

---

## Verification (Worker 3)

### Logic verification outcome

Cycle diff vs baseline `0872a20` is docstring-only — confirmed via full `git diff`: the only two hunks are the module docstring (lines 9-15) and the `_validate_meta` "Returns" paragraph (lines 1024-1035). No executable line changed; all of Worker 1's "What looks solid" logic conclusions are untouched by definition.

- **Low 1 (module docstring `Meta`-option list incomplete):** fixed and ACCURATE. The new enumeration lists `fields`, `exclude`, `name`, `description`, `optimizer_hints`, `interfaces`, `nullable_overrides`, `required_overrides`, `connection`, `filterset_class`, `orderset_class`, `globalid_strategy`, `relation_shapes`, `primary` = exactly the 14 non-`model` keys in the live `ALLOWED_META_KEYS` frozenset (`types/base.py:67-85`; 15 entries minus the required `model`). No omitted optional key, no extra. The added "see ``ALLOWED_META_KEYS`` for the authoritative set" pointer is correct (`model` correctly left implicit as the required base, not an optional key).
- **Low 2 (`_ValidatedMeta` "Returns" omits 0.0.9 fields):** fixed and ACCURATE. The "Returns" prose now names the 5 original (interfaces, primary, optimizer_hints, fields, exclude) + the 7 added (`filterset_class`, `orderset_class`, `connection`, `globalid_strategy`, `relation_shapes`, `nullable_overrides`, `required_overrides`) = all 12 fields of the `_ValidatedMeta` NamedTuple (`types/base.py:981-992`). No omitted/extra field. The added "see the ``_ValidatedMeta`` definition for the authoritative field list" pointer is correct.

### DRY findings disposition

- `_is_relay_shaped` recomputed 3x: stayed DEFERRED (no edit) per Worker 1's defer-with-trigger (thread `relay_shaped` through `_ValidatedMeta` only on a fourth `_validate_meta`-local consumer). Confirmed absent from the diff.
- `_selected_meta_targets` factoring: no action warranted (already correctly factored). Confirmed absent from the diff.

### Temp test verification

None. Docstring-only change with zero behaviour delta; no temp test earns its keep.

### Sibling-cycle attribution

Wider owned-scope diff stat (`django_strawberry_framework/`, `tests/`, `docs/GLOSSARY.md`, `CHANGELOG.md`) is dirty only at closed verified+[x] sibling cycles — conf/connection/exceptions/list_field/filters.factories/filters.sets/inspect_django_type/optimizer.extension/optimizer.selections/optimizer.walker/orders.factories/orders.inputs (all `Status: verified`, all `[x]` at review-0_0_9.md:70-102) plus their tests and the GLOSSARY hunks (lines 42/287/804/916/992/1002/1179 → testing.relay / connection / orders / filters / inspect cycles; none touch a `types/base.py`-owned entry). `types/base.py`'s own GLOSSARY entries (`#djangotype`, the override/relation-shape/globalid tables) were untouched, matching the artifact's "GLOSSARY is accurate — no verbatim replacement text needed." The cycle's "Files touched: types/base.py docstrings only" claim holds.

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box. Diff is docstring-only (executable lines byte-unchanged); both updated enumerations are accurate against live `ALLOWED_META_KEYS` (14 optional keys) and `_ValidatedMeta` (12 fields) with correct source-of-truth pointers; `_is_relay_shaped` DRY bullet stayed deferred; ruff format-check + check clean (COM812 = standing notice); CHANGELOG diff empty with `Not warranted` citing both AGENTS.md and the active plan's silence.

---

## Comment/docstring pass

### Files touched
- `types/base.py:10-15` and `types/base.py:1024-1035` — the two docstring edits described in `## Fix report (Worker 2)`. These ARE the cycle's only edits (both Lows are comment-tier), so the comment pass and the logic pass coincide.

### Per-finding dispositions
- Low 1 (module docstring `Meta`-option list incomplete): fixed — enumerated all 14 optional keys + `ALLOWED_META_KEYS` pointer.
- Low 2 (`_ValidatedMeta` "Returns" omits 0.0.9 fields): fixed — named the seven additional fields + `_ValidatedMeta`-definition pointer.
- DRY (`_is_relay_shaped` recomputed 3x): deferred-with-trigger per Worker 1's disposition; no edit. Trigger: a fourth `_validate_meta`-local `relay_shaped` consumer.
- DRY (`_selected_meta_targets` factoring): no action warranted (already correctly factored, per Worker 1).

### Validation run
- `uv run ruff format .` — pass (265 files unchanged)
- `uv run ruff check --fix .` — pass

### Notes for Worker 3
Docstring-only; no stale or now-obvious comments introduced; no broad rewrite outside reviewed scope.

---

## Changelog disposition

### State
`Not warranted`.

### Reason
The cycle's only edits are internal docstring polish (additive, substring-compatible enumeration + source-of-truth pointers) with zero behaviour change. Per `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed") AND the active plan's silence on changelog authorization for this per-file cycle (per-file cycles are never the authorising scope and forward any drift to the project pass), no edit is warranted.

### What was done
No `CHANGELOG.md` edit.

### Validation run
- `uv run ruff format .` — pass (265 files unchanged)
- `uv run ruff check --fix .` — pass

---

## Iteration log
