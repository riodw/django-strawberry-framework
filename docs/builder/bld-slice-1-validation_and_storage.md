# Build: Slice 1 — Validation + storage

Spec reference: `docs/spec-relay_interfaces.md` (lines 9-29 slice checklist; lines 269-342 Decisions 1, 2, 4, and 5; lines 427-433 implementation plan step 1; lines 462-477 validation/lifecycle tests)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

- **Existing patterns reused.**
  - `_validate_meta` (`django_strawberry_framework/types/base.py:273-303`) already owns Meta-key validation order: required-model, fields/exclude exclusivity, deferred-key rejection, unknown-key rejection. The interface validator slots in as a fifth step at the bottom of that function so consumer-visible failure order stays "first thing wrong is the first thing reported."
  - `_format_unknown_fields_error` (`django_strawberry_framework/types/base.py:262-270`) is the canonical "`<Model>.Meta.<attr> ...`" error shape. The new interface-validator error messages reuse the same `f"{meta.model.__name__}.Meta.interfaces ..."` prefix so consumer-visible failures stay the same shape as `Meta.fields` / `Meta.exclude` / `Meta.optimizer_hints` errors (spec Decision 4, lines 318-319 explicitly tie the new errors to this pattern).
  - `_normalize_sequence_spec` (`django_strawberry_framework/types/base.py:209-213`) is the existing "sequence-or-None to tuple" normalizer used for `exclude_spec`. Its responsibility is narrow (sequence to tuple, no membership checks), and crucially it does **not** reject strings — strings are iterable and would silently pass. The interface validator therefore cannot route through it as-is; it needs its own normalization (tuple/list/single-class accepted, string/set/generator rejected per Decision 4 line 323).
  - `DjangoTypeDefinition.interfaces: tuple[type, ...] = ()` (`django_strawberry_framework/types/definition.py:43`) is the storage slot already reserved by the `0.0.4` foundation. No new dataclass field. The constructor call at `django_strawberry_framework/types/base.py:127-142` is the single site where the normalized tuple is passed through, alongside the other `Meta`-derived kwargs.
  - The `DjangoType` class symbol is already imported / present in `django_strawberry_framework/types/base.py:74-189`, so the "reject `DjangoType` self-reference or other `DjangoType` subclasses" check uses `issubclass(entry, DjangoType)` directly — no extra import or registry lookup needed.
  - The `0.0.4` deferred-key TODO anchor at `django_strawberry_framework/types/base.py:305-309` already names the exact validation contract Slice 1 ships. Slice 1 replaces that anchor with the implementation; it must be removed in the same change per `AGENTS.md` line 10.
  - Test scaffolding lives at `tests/types/test_relay_interfaces.py:1-17` (currently TODO anchors only). The new tests for Slice 1 land in that file. The autouse `_isolate_registry` fixture pattern is at `tests/types/test_base.py:50-55`; Slice 1's new test module mirrors that fixture so each test starts with a clean registry.
  - The existing deferred-key parametric test at `tests/types/test_base.py:135-151` (`test_meta_rejects_each_deferred_key`) still includes `"interfaces"`. Slice 1 keeps `"interfaces"` in `DEFERRED_META_KEYS` per the slice checklist (spec line 10) so that test continues to pass — the interface validator runs in addition to, not instead of, the deferred-key rejection. **However**, this surfaces a non-trivial ordering question: validating `Meta.interfaces` shape before raising the deferred-key error would make the deferred-key test inconsistent (depending on the test fixture, the validator might raise an interface-shape error first instead of the deferred-key error). See "Open questions for Worker 2" — Worker 2 must place the interface validator **after** the deferred-key check so the existing `test_meta_rejects_each_deferred_key` still observes the deferred-key error.

- **New helpers justified.**
  - One new module-local helper: `_validate_interfaces(meta: type) -> tuple[type, ...]`. Single responsibility: take the raw `Meta.interfaces` value (which may be unset, a single Strawberry interface class, or a tuple/list of them), apply the seven Decision-4 rules (lines 322-330), and return the normalized `tuple[type, ...]` ready to pass to `DjangoTypeDefinition.interfaces`. The helper returns `()` when the key is absent or set to an empty tuple/list. Justification for a new helper rather than inlining into `_validate_meta`: `_validate_meta` already encapsulates exactly four small validation steps; inlining adds ~25 lines of branchy logic to a 30-line function. The helper is also the natural return-site for the normalized tuple that the `__init_subclass__` call site at `types/base.py:127-142` needs to pass to `DjangoTypeDefinition`. Without a helper, `__init_subclass__` would have to re-derive the normalized tuple, duplicating the normalization. Justification for placing it in `types/base.py` and not `types/relay.py`: this slice is purely validation and storage. The `relay.py` module (currently a placeholder, see `tests/types/test_relay.py:1-10`) is reserved for the actual Relay helper surface that lands in Slices 2 and 4 (`install_is_type_of`, `apply_interfaces`, `install_relay_node_resolvers`, the four `_resolve_*_default` implementations per spec lines 380-424). Adding `_validate_interfaces` to `relay.py` would muddle "Relay-specific" with "generic interface validation" — non-Relay interfaces are validated by the same helper.
  - `_validate_meta` signature change: instead of returning `None`, it now returns `tuple[type, ...]` (the normalized interfaces tuple, possibly empty). The single caller at `types/base.py:97` already discards the return value. This avoids re-running the validator and re-walking `getattr(meta, "interfaces", None)` at the `DjangoTypeDefinition` construction site. **Alternative shape considered:** return `(unknown_keys, interfaces)` or stash on a small dataclass. Rejected: the slice contract is exactly two new pieces of derived state from `Meta` (the validated interfaces tuple), so a single tuple return is the smallest viable interface.

- **Duplication risk avoided.**
  - **Risk 1: parallel error shapes.** A naive implementation might write `raise ConfigurationError(f"Meta.interfaces ...")` instead of `raise ConfigurationError(f"{meta.model.__name__}.Meta.interfaces ...")`, drifting from the `_format_unknown_fields_error` shape at `types/base.py:262-270`. The plan mandates the same `<Model>.Meta.<attr> ...` prefix for every new error message. Worker 2 is **not** required to route through `_format_unknown_fields_error` itself (which is shaped for unknown-field-name errors with `Available: ...`); the interface-validator errors do not have an "available set" to surface, so they construct the message inline but with the same `<Model>.Meta.interfaces` lead-in. Justification: `_format_unknown_fields_error`'s body is "lists unknown values, lists available values" — the interface validator's errors are categorically different ("this entry is not a Strawberry interface", "this entry duplicates another"). Forcing them through `_format_unknown_fields_error` would either bloat that helper or produce awkward error messages.
  - **Risk 2: re-deriving the normalized tuple at the call site.** Without `_validate_meta` returning the tuple, the `__init_subclass__` call at `types/base.py:127-142` would have to call `getattr(meta, "interfaces", None)` again and re-normalize (handle single-class vs sequence). The plan returns the tuple from `_validate_meta` itself so normalization happens exactly once.
  - **Risk 3: scattering Strawberry-interface detection.** Each entry must satisfy `hasattr(entry, "__strawberry_definition__") and entry.__strawberry_definition__.is_interface` (Decision 4 line 325). This check appears in exactly one place — inside the new `_validate_interfaces` helper. Slice 4's `apply_interfaces` (per spec lines 384-385) does not re-validate; by then the tuple has already been validated at collection time and stored on the definition. Worker 2 must not duplicate this check at the finalizer site.
  - **Risk 4: silent acceptance of `str` as a sequence.** Python's `isinstance(value, (tuple, list))` is the right gate; `Iterable` or `Sequence` would let `str` pass and produce one-character "interface" entries. The plan pins this explicitly under Implementation step 2.
  - **Risk 5: tolerating duplicates "to be helpful".** Decision 4 line 328 is explicit: duplicates raise. The plan calls for `if len(set(entries)) != len(entries)` using class identity (each entry is a class, which is hashable). The error names the duplicate set so the typo is obvious.
  - **Patterns expected to recur in later slices.** (1) The same `getattr(meta, "interfaces", None)` lookup-and-fallback shape is what Slices 2 / 3 / 4 will all use to ask "does this `Meta` declare interfaces?" — Slice 3's `_build_annotations` will need to know "is `relay.Node` in the declared interfaces?" to suppress the `id` annotation; Slice 4's Phase 2.5 will read the validated tuple from `definition.interfaces`, not from `Meta` directly. By having Slice 1 store the normalized tuple on `DjangoTypeDefinition.interfaces`, every later slice reads the same canonical source. The plan does **not** hoist a generic `meta_interfaces()` lookup helper now — the spec is explicit that `definition.interfaces` is the source of truth (Decision 5 line 335). (2) Slice 3 will need to suppress the `id` annotation in `_build_annotations` based on `relay.Node` being among the interfaces. That check belongs in Slice 3; Slice 1 must not preempt it. The validator only knows "is this a real Strawberry interface", not "is this specifically `relay.Node`". Decision 2 line 285 keeps the per-type opt-in tied to declaring `relay.Node` specifically; Slice 3 will check `relay.Node in interfaces`. The TODO anchor at `types/base.py:480-483` already names this Slice 3 work; Slice 1 leaves that anchor untouched.

### Implementation steps

1. **Remove the deferred-key validation TODO anchor at `django_strawberry_framework/types/base.py:305-309`** in the same change that adds the validator (per `AGENTS.md` line 10: anchors are paired with the code that ships the slice and are removed in that same change). The other two `0.0.5 relay interfaces` anchors at `types/base.py:84-86` and `types/base.py:124-126` and `types/base.py:480-483` remain because their respective behavior lands in Slices 2, 3, and 4. The `DEFERRED_META_KEYS` block-comment anchor at `types/base.py:48-58` also remains until Slice 5.

2. **Add `_validate_interfaces` helper to `django_strawberry_framework/types/base.py`** (place it adjacent to `_validate_meta`, after `_format_unknown_fields_error` at line 270 and before `_validate_meta` at line 273 so the validator helpers cluster together). Signature: `def _validate_interfaces(meta: type) -> tuple[type, ...]`. Body, in this order:

   a. Read raw value: `raw = getattr(meta, "interfaces", None)`.

   b. If `raw is None`, return `()` (key absent — `0.0.4`-identical behavior).

   c. **Reject `str` first** (before any other isinstance check): `if isinstance(raw, str): raise ConfigurationError(f"{meta.model.__name__}.Meta.interfaces must be a tuple/list of Strawberry interface classes or a single interface class, got a string.")`. Strings are iterable and would otherwise sneak past a generic isinstance(tuple/list) → fall-through-to-class-check guard.

   d. If `raw` is a class (per Decision 4 line 323 "a single real Strawberry interface class such as `interfaces = relay.Node`"): normalize to a one-item tuple `entries = (raw,)`. Use `isinstance(raw, type)` to detect class-ness. **Do not** also accept `raw` being a non-tuple non-list iterable (generators, sets) — those are explicitly rejected per Decision 4 line 323.

   e. Else if `isinstance(raw, (tuple, list))`: `entries = tuple(raw)`.

   f. Else: raise `ConfigurationError(f"{meta.model.__name__}.Meta.interfaces must be a tuple/list of Strawberry interface classes or a single interface class, got {type(raw).__name__}.")`. This covers `set`, generator, dict, int, etc.

   g. If `entries == ()`: return `()` (empty tuple is a no-op per Decision 4 line 324).

   h. Walk `entries` once, building two collections: `seen_ids: set[int]` and `duplicates: list[str]`. For each `entry`:
      - If `isinstance(entry, str)`: raise `ConfigurationError(f"{meta.model.__name__}.Meta.interfaces must contain interface classes, not strings (got {entry!r}). Lazy/forward-reference interface lookup is out of scope for 0.0.5.")` (Decision 4 line 326).
      - If `not isinstance(entry, type)`: raise the same "must be interface classes" error with `got {entry!r}` (non-string non-class entries: instances, modules, etc.).
      - If `issubclass(entry, DjangoType)`: raise `ConfigurationError(f"{meta.model.__name__}.Meta.interfaces may not contain DjangoType or DjangoType subclasses (got {entry.__name__}). DjangoType is not a Strawberry interface.")` (Decision 4 line 327; the `DjangoType` symbol is already in module scope at `types/base.py:74`).
      - If `not (hasattr(entry, "__strawberry_definition__") and getattr(entry.__strawberry_definition__, "is_interface", False))`: raise `ConfigurationError(f"{meta.model.__name__}.Meta.interfaces entry {entry.__name__} is not a Strawberry interface. Use @strawberry.interface or one of the strawberry.relay interface classes.")` (Decision 4 line 325). Use `getattr(..., "is_interface", False)` defensively in case `__strawberry_definition__` exists but has no `is_interface` attribute (this is the same defensive-`getattr` pattern at `types/base.py:259, 287, 388-389, 459`).
      - Duplicate detection: `entry_id = id(entry)`. If `entry_id in seen_ids`, append `entry.__name__` to `duplicates`. Else `seen_ids.add(entry_id)`.

   i. After the walk, if `duplicates`: raise `ConfigurationError(f"{meta.model.__name__}.Meta.interfaces contains duplicate entries: {sorted(set(duplicates))}.")` (Decision 4 line 328).

   j. Return `entries`.

   **Note on Decision 4 line 329 ("a class that already inherits from one of the listed interfaces directly is accepted"):** This is **not** a check `_validate_interfaces` performs — the validator does not inspect `cls.__mro__`. The validator only validates the `Meta.interfaces` tuple itself. The "no-op duplicate" semantics happen later in Slice 4's Phase 2.5 (per spec line 339, "skip those already present in `cls.__mro__`"). Slice 1's job is to accept the tuple without erroring; the actual base-injection no-op happens in Slice 4. The Slice 1 test `test_class_already_inherits_relay_node_directly` therefore only asserts "validation accepts this case without raising" — it does **not** assert that `relay.Node` is or is not in `__bases__`, because that's Slice 4's contract.

3. **Modify `_validate_meta` at `django_strawberry_framework/types/base.py:273-303`** to:

   a. Change return type from `None` to `tuple[type, ...]`.

   b. Update the docstring at lines 274-286 to add a fifth validation step: "5. If `Meta.interfaces` is declared, validate per `_validate_interfaces` (Decision 4)." Also update the "Validation order" wording so the deferred-key check (step 3) is explicitly noted as running before the interfaces check.

   c. At the very end of the function (after the existing unknown-key check at lines 301-303 and **after** the deferred-key check at lines 295-299), call `interfaces = _validate_interfaces(meta)` and `return interfaces`. This placement is load-bearing: while `"interfaces"` is in `DEFERRED_META_KEYS`, the deferred-key check at lines 295-299 raises before the interface validator ever runs (the existing `test_meta_rejects_each_deferred_key` at `tests/types/test_base.py:135-151` still passes). The interface validator only runs in practice when `"interfaces"` is **not** in `DEFERRED_META_KEYS`, i.e. once Slice 5 promotes it. Slice 1 still wires the validator and tests it directly via unit tests that bypass `_validate_meta` (see test plan below) — the validator must work end-to-end before Slice 5 promotes the key.

   d. Remove the inline `# TODO(0.0.5 relay interfaces...)` comment at lines 305-309 (per step 1 above).

4. **Modify the `__init_subclass__` call site at `django_strawberry_framework/types/base.py:97`** to capture the return value: `interfaces = _validate_meta(meta)`.

5. **Modify the `DjangoTypeDefinition(...)` construction at `django_strawberry_framework/types/base.py:127-142`** to pass `interfaces=interfaces` (the variable captured in step 4) through to the existing `interfaces: tuple[type, ...] = ()` slot at `types/definition.py:43`. Place the kwarg adjacent to `consumer_assigned_scalar_fields=consumer_assigned_scalar_fields,` at line 141 so the `Meta`-derived block stays together. Maintain the trailing-comma convention per `AGENTS.md` line 23 and `START.md` line 30.

6. **Remove the TODO anchor at `django_strawberry_framework/types/base.py:124-126`** in the same change (step 5 lands the behavior the anchor describes). Per `AGENTS.md` line 10.

7. **Update the `DjangoTypeDefinition.interfaces` field anchor at `django_strawberry_framework/types/definition.py:40-43`** to remove the `# TODO(0.0.5 relay interfaces...)` comment block at lines 40-42 because Slice 1 lands the population step. The `interfaces: tuple[type, ...] = ()` line at 43 itself stays. **However**, the remaining contract — "keep it as the finalizer's source of truth for Phase 2.5 base injection" — is Slice 4's work. To avoid removing an anchor whose Slice 4 contract is still unshipped, the plan is to **re-scope the comment** rather than delete it: replace lines 40-42 with a one-line comment "Populated by `_validate_meta`; consumed by `finalize_django_types()` Phase 2.5 (Slice 4)." That preserves the cross-reference without leaving a TODO claiming the field is still unpopulated.

8. **Confirm `"interfaces"` remains in `DEFERRED_META_KEYS` at `django_strawberry_framework/types/base.py:41-60`.** No change to this block. The block comment at lines 48-57 stays intact (it explicitly mentions the validation step landing first, which is exactly what Slice 1 is).

### Test additions / updates

All new tests land in `tests/types/test_relay_interfaces.py` (currently a TODO-only placeholder; the new tests replace the three TODO comment blocks at lines 1-17 — the comments are removed in the same change that adds the test bodies, per `AGENTS.md` ERA001 contract since real code is replacing the anchored work).

The autouse `_isolate_registry` fixture from `tests/types/test_base.py:50-55` is mirrored in the new file (re-declared, not imported, so the two test modules stay independent). The test module-level docstring is rewritten from the TODO-only placeholder to a real "Tests for the 0.0.5 Relay interfaces slice. Slice 1 covers validation and storage." sentence.

A test-level note: because `"interfaces"` is still in `DEFERRED_META_KEYS` after Slice 1 ships, the Slice 1 validation tests cannot exercise `_validate_meta` end-to-end with `Meta.interfaces` declared — the deferred-key rejection raises first. The tests therefore call `_validate_interfaces` directly as a unit, importing it from `django_strawberry_framework.types.base`. The end-to-end path becomes testable in Slice 5 (when `"interfaces"` is promoted to `ALLOWED_META_KEYS`); for Slice 1, the unit-level tests are what we have. The storage test (`test_meta_interfaces_stored_on_definition`) is the one exception: it constructs a `DjangoType` subclass with `Meta.interfaces = (relay.Node,)` after temporarily setting up `_validate_meta` to skip the deferred-key check — but that monkey-patching is fragile. **Better path:** the storage test asserts the behavior at the `DjangoTypeDefinition` construction site directly, by calling `_validate_interfaces(meta)` then constructing a `DjangoTypeDefinition` and checking `definition.interfaces`. The alternative — moving the deferred-key check ordering so the interface check runs first — would break `test_meta_rejects_each_deferred_key`. Worker 2 should use the unit-level approach.

Tests (all pinned to `tests/types/test_relay_interfaces.py::<test_name>`):

- `test_meta_interfaces_accepted` — `Meta` with `interfaces = (relay.Node,)` is normalized to `(relay.Node,)` by `_validate_interfaces`. Asserts the returned tuple is `(relay.Node,)` and that no exception is raised. (Spec test plan line 467.)
- `test_meta_interfaces_accepts_single_interface_class` — three variants in one parametrized test: `interfaces = relay.Node` (no tuple at all), `interfaces = (relay.Node,)` (canonical), and `interfaces = (relay.Node)` (missing comma — Python sees this as plain `relay.Node`, identical to variant 1, but the spec lines 192-193 / 323 / 468 / 576 explicitly mention this spelling so it's tested verbatim). All three normalize to `(relay.Node,)`.
- `test_meta_interfaces_rejects_non_sequence` — parametrized over invalid values: a set `{relay.Node}`, a generator expression `(x for x in (relay.Node,))`, a dict `{relay.Node: None}`, an int `42`. Each raises `ConfigurationError` with the "must be a tuple/list" wording. (Spec test plan line 469; per Decision 4 line 323.)
- `test_meta_interfaces_rejects_string_entries` — two cases: top-level `interfaces = "Node"` (rejected as not-a-class), and tuple-with-string `interfaces = ("Node",)` (rejected as string entry). Both raise `ConfigurationError`. (Spec test plan line 470.)
- `test_meta_interfaces_rejects_non_interface_classes` — `interfaces = (object,)` and `interfaces = (int,)` raise `ConfigurationError` mentioning "not a Strawberry interface." A class that has `__strawberry_definition__` but `is_interface = False` (e.g. a `@strawberry.type` class) is also rejected; this is covered by constructing a `@strawberry.type`-decorated test fixture class inline in the test. (Spec test plan line 471.)
- `test_meta_interfaces_rejects_djangotype_self_reference` — `interfaces = (DjangoType,)` raises with the "may not contain DjangoType" message. Also tests a `DjangoType` subclass: declare a tiny `class SomeType(DjangoType): pass`-style subclass (without `Meta` so it skips registration), then assert `_validate_interfaces` on a `Meta` with `interfaces = (SomeType,)` raises. (Spec test plan line 472.)
- `test_meta_interfaces_rejects_duplicates` — `interfaces = (relay.Node, relay.Node)` raises `ConfigurationError` mentioning "duplicate entries" and naming `Node`. (Spec test plan line 473.)
- `test_meta_interfaces_empty_tuple_treated_as_unset` — `_validate_interfaces` on a `Meta` with `interfaces = ()` returns `()`. Cross-checked against `_validate_interfaces` on a `Meta` without the attribute at all (also `()`). Confirms bit-for-bit identical return value. (Spec test plan line 474.)
- `test_meta_interfaces_stored_on_definition` — constructs a `Meta` with `interfaces = (relay.Node,)`, calls `_validate_interfaces` to get the normalized tuple, then constructs a `DjangoTypeDefinition(...)` (using a real fakeshop model from `apps.products.models` for minimal `origin`/`model`/`fields_spec`/etc. defaults) with `interfaces=normalized`, and asserts `definition.interfaces == (relay.Node,)`. This pins the storage contract from spec lines 116, 432, 574. (Spec test plan line 475.)
- `test_class_already_inherits_relay_node_directly` — `_validate_interfaces` on a `Meta` with `interfaces = (relay.Node,)`, where the test's containing class hierarchy already includes `relay.Node` as a base, accepts the tuple without raising. The Slice 1 contract is only "validation accepts this case" — the base-injection no-op is Slice 4. The test calls `_validate_interfaces` directly; it does **not** assert anything about `__bases__` mutation. (Spec test plan line 476; per Decision 4 line 329 and Slice 1's checklist line 28.)
- `test_relay_node_with_composite_pk_raises` — **explicitly deferred to Slice 4.** The spec slice-1 checklist (line 29) lists this test name, but Decision 4 line 330 and implementation-plan step 1 (line 431) explicitly say the composite-pk check is **not** done in Slice 1 (it lives in Phase 2.5, which is Slice 4). Worker 2 should add a placeholder test that `pytest.mark.skip(reason="composite-pk check lives in Slice 4 / Phase 2.5; see spec line 431")` so the test name is reserved and the Slice 1 build does not look like it omitted a listed test. Slice 4 unskips it. **Flagged for Worker 2 below.**

Temp/scratch test candidates for Worker 3 (flagged here per the plan-time DRY discipline; Worker 3 owns the actual decision):

- During implementation, Worker 2 may find it useful to write a small `docs/builder/temp-tests/slice-1/test_validator_paths.py` that exercises each rejection branch in isolation (one test per `raise ConfigurationError`) without the test-file structure overhead. These would be Worker 3's decision to keep as permanent additions or delete; the eleven listed tests above cover every rejection branch, so the temp tests are not load-bearing — they're a Worker 2 debugging aid only.

### Open questions for Worker 2

1. **Deferred-key check ordering vs interface validator.** The validator placement at the end of `_validate_meta` is load-bearing: it must run **after** the deferred-key check at `types/base.py:295-299`. Until Slice 5 promotes `"interfaces"` to `ALLOWED_META_KEYS`, end-to-end `_validate_meta` paths with `Meta.interfaces` declared always hit the deferred-key error first. Worker 2 must verify this ordering preserves the existing `test_meta_rejects_each_deferred_key` parametrization at `tests/types/test_base.py:135-151` (which includes `"interfaces"`). If for any reason Worker 2 needs to reorder these checks, that is a spec-relevant decision and Worker 2 must flag it back to Worker 1 via the "Notes for Worker 1 (spec reconciliation)" section rather than silently changing the order.

2. **`test_relay_node_with_composite_pk_raises` test placement.** Slice 1's spec checklist (line 29) lists this test, but the composite-pk check itself is Slice 4 work (per Decision 4 line 330 and implementation-plan step 1 at spec line 431). The plan's recommendation is to add the test name as a `pytest.mark.skip` placeholder in Slice 1 with a skip reason citing the slice ownership. Worker 2 may instead choose to add no placeholder at all and let Slice 4 add it from scratch; Worker 3 should accept either approach as long as Slice 4 ultimately delivers a passing test of that name.

3. **`DjangoTypeDefinition` storage test minimal fixture.** `test_meta_interfaces_stored_on_definition` constructs a `DjangoTypeDefinition` directly. The dataclass has many required fields (`origin`, `model`, `name`, `description`, `fields_spec`, `exclude_spec`, `selected_fields`, `field_map`, `optimizer_hints`, `has_custom_get_queryset`). Worker 2 should use the smallest viable defaults (e.g. `selected_fields=()`, `field_map={}`, `optimizer_hints={}`, `has_custom_get_queryset=False`) and a real fakeshop model for `model` (per `AGENTS.md` line 8: "package tests intentionally use real example-project models from `apps.products.models` and `apps.library.models`"). The test focus is solely on `definition.interfaces` after construction; the other fields are just "what the dataclass needs to instantiate."

4. **Error-message wording precision.** The plan specifies exact wording for each `ConfigurationError`. Worker 2 may tighten the wording for clarity but must keep (a) the `<Model>.Meta.interfaces` prefix and (b) the substring that the corresponding test's `match=` regex pins (e.g. `"not a Strawberry interface"`, `"duplicate entries"`, `"may not contain DjangoType"`, `"must be a tuple/list"`). The tests as specified pin substrings, not the full message.

5. **`_validate_interfaces` placement within `types/base.py`.** The plan recommends placing it adjacent to `_validate_meta` (between `_format_unknown_fields_error` at line 270 and `_validate_meta` at line 273). Worker 2 may instead place it after `_validate_meta` if call-site clarity is improved. The validator must be a module-level helper (not nested inside `_validate_meta`) so it is callable from the new unit tests.

6. **Import of `relay` in the test module.** The tests need `from strawberry import relay`. Worker 2 should confirm the local `strawberry-graphql>=0.262.0` lower bound (per `pyproject.toml`) exposes `strawberry.relay.Node`; the spec risk note at lines 538-539 confirms it does. Worker 2 should not add `strawberry-graphql` to any new dependency surface; it is already a hard dependency.

---

## Build report (Worker 2)

### Files touched

- `django_strawberry_framework/types/base.py` — added module-level `_validate_interfaces(meta) -> tuple[type, ...]` helper implementing the seven Decision-4 rules (str rejection first, single-class normalization, tuple/list normalization, per-entry checks for str/non-class/`DjangoType` subclass/non-Strawberry-interface, and duplicate detection by class identity). Changed `_validate_meta` return type from `None` to `tuple[type, ...]` and added a fifth validation step that returns `_validate_interfaces(meta)` at the end. Captured the return at the single call site in `__init_subclass__` (`interfaces = _validate_meta(meta)`) and threaded it through to `DjangoTypeDefinition(...)` as `interfaces=interfaces`. Removed the two TODO anchors the slice ships (`# TODO(0.0.5 relay interfaces ...)` at the former `__init_subclass__` site above the `DjangoTypeDefinition(...)` call, and the inline anchor at the former tail of `_validate_meta`). The other Slice-2/3/4 anchors at the `install_is_type_of` site, the `_build_annotations` `id`-suppression site, and the `DEFERRED_META_KEYS` block comment are untouched.
- `django_strawberry_framework/types/definition.py` — replaced the `# TODO(0.0.5 relay interfaces ...)` comment block above `interfaces: tuple[type, ...] = ()` with a one-line cross-reference noting `_validate_meta` populates the field and Slice 4's Phase 2.5 consumes it. The field declaration itself is unchanged.
- `tests/types/test_relay_interfaces.py` — replaced the three TODO-only placeholder comments with the actual Slice 1 test module (validation + storage tests, autouse `_isolate_registry` fixture mirrored from `tests/types/test_base.py`, `_meta(**attrs)` helper to build throw-away `Meta` classes against `Category`).

### Tests added or updated

All under `tests/types/test_relay_interfaces.py`:

- `test_meta_interfaces_accepted` — asserts `_validate_interfaces` returns `(relay.Node,)` for `interfaces = (relay.Node,)`.
- `test_meta_interfaces_accepts_single_interface_class` — parametrized over `relay.Node`, `(relay.Node,)`, and the missing-comma spelling `(relay.Node)`; all three normalize to `(relay.Node,)`.
- `test_meta_interfaces_rejects_non_sequence` — parametrized over `{relay.Node}`, a generator expression, `{relay.Node: None}`, and `42`; each raises `ConfigurationError` matching `"must be a tuple/list"`.
- `test_meta_interfaces_rejects_string_entries` — `interfaces = "Node"` raises `"must be a tuple/list"` (str caught at the top-level isinstance guard); `interfaces = ("Node",)` raises `"must contain interface classes"`.
- `test_meta_interfaces_rejects_non_interface_classes` — `object`, `int`, and a `@strawberry.type`-decorated class each raise `"not a Strawberry interface"`.
- `test_meta_interfaces_rejects_djangotype_self_reference` — `DjangoType` itself and a `DjangoType` subclass each raise `"may not contain DjangoType"`.
- `test_meta_interfaces_rejects_duplicates` — `(relay.Node, relay.Node)` raises `"duplicate entries"`.
- `test_meta_interfaces_empty_tuple_treated_as_unset` — `interfaces = ()` and absent key both return `()`.
- `test_meta_interfaces_stored_on_definition` — constructs a `DjangoTypeDefinition` with the smallest viable defaults (`origin=object`, `model=Category`, empty `selected_fields`/`field_map`/`optimizer_hints`) plus `interfaces=normalized`, asserts `definition.interfaces == (relay.Node,)`.
- `test_class_already_inherits_relay_node_directly` — `_validate_interfaces` accepts the tuple when the host class already inherits `relay.Node` directly; the test deliberately does not inspect `__bases__` (Slice 4's contract).
- `test_relay_node_with_composite_pk_raises` — staged as `pytest.mark.skip(reason="composite-pk check lives in Slice 4 / Phase 2.5; see spec line 431")` per Open Question 2 in the plan. Slice 4 unskips and implements.

### Validation run

- `uv run ruff format .` — pass (1 file reformatted on first run, clean on confirmation re-run).
- `uv run ruff check --fix .` — pass (1 error auto-fixed on first run — sorted-import order in the new test file; clean on confirmation re-run).
- `pytest` — not run (per `START.md` line 24 the standing rule is formatting only; Worker 1 owns the test gates).

### Notes for Worker 3

- The interface validator is **not** routed through `_format_unknown_fields_error` (`types/base.py:262`). That helper's body is "lists unknown values, lists available values"; the interface-validator errors do not have an "available set" to surface and are categorically different. The plan flagged this explicitly under Risk 1 / DRY analysis. Each new error message keeps the `{meta.model.__name__}.Meta.interfaces ...` lead-in to match the existing error-shape convention.
- The deferred-key check at `_validate_meta` (the existing `raise ConfigurationError(f"Meta keys not supported yet: ...")`) runs **before** `_validate_interfaces`, so the existing `test_meta_rejects_each_deferred_key` parametrization at `tests/types/test_base.py:135-151` (which includes `"interfaces"`) continues to short-circuit before the interface validator ever runs end-to-end. The Slice 1 tests therefore call `_validate_interfaces` directly as a unit; end-to-end coverage of `_validate_meta` with `Meta.interfaces` declared is Slice 5's contract (after the key is promoted).
- The `_validate_interfaces` helper is placed **after** `_validate_meta` in `types/base.py`, not before. The plan was indifferent on placement (Open Question 5); placing it after `_validate_meta` keeps the docstring-order reading "validate the high-level Meta first, then drill into the interface-specific rules" and lets the cross-reference in `_validate_meta`'s docstring point forward to a helper defined below.
- The `_validate_interfaces` `entry == ()` short-circuit at the post-normalization step handles the empty-list edge case (`interfaces = []` normalizes to `()` via `tuple([])` and returns early before the walk). That preserves the bit-for-bit no-op contract Decision 4 line 324 requires.
- Duplicate detection uses `id(entry)` (class identity) rather than `==`, matching Python class-identity semantics. The error message reports the duplicated class names sorted and deduped so repeated typos surface as `['Node']` rather than `['Node', 'Node']`.
- The static inspection helper (`scripts/review_inspect.py`) was **not** run during this build pass. `types/base.py` is well above the 150-line threshold the plan/BUILD doc names for Worker-1 planning runs, but Worker 2 only re-runs the helper "when the logic is hard to read with docstrings inline" (BUILD.md line 380). The diff was small and structurally local (one new helper, one return-type change, one constructor kwarg added), so the helper would have added overhead without surfacing additional signal. Worker 3 should still run the helper per its own when-to-run rules.
- The new test file references `_Host` (a class declared inside `test_class_already_inherits_relay_node_directly`) via `assert relay.Node in _Host.__mro__` purely to satisfy ruff's unused-class check while keeping the host-class declaration as the test's structural anchor. Removing the assertion would force a `# noqa` and obscure the intent; the assertion is informational rather than load-bearing.

### Notes for Worker 1 (spec reconciliation)

None.

---

## Review (Worker 3)

### High:

#### Coverage gate breach: line 325 (non-class non-string entry rejection) is unreachable from the new tests

The new `_validate_interfaces` helper has a branch at `django_strawberry_framework/types/base.py:324-327` that rejects entries inside the tuple that are neither strings nor classes (e.g. instances, modules, `42`, an `object()`). The eleven Slice 1 tests never feed such an entry through the validator — `test_meta_interfaces_rejects_non_sequence` covers only top-level non-sequence values (those raise at line 309-312, not 325), and every other rejection test feeds either strings, real classes, or `DjangoType` subclasses. Running the full `tests/` suite plus the new tests yields 99.92% coverage on `django_strawberry_framework/types/base.py` with the single uncovered line being 325 (verified via `uv run pytest tests/ --cov=django_strawberry_framework.types.base --cov-report=term-missing`). Per `AGENTS.md` "Coverage is 100% on the package" and the spec Definition of done item 7, this fails the package's `fail_under = 100` gate; the slice cannot land in this state. The temp test under `docs/builder/temp-tests/slice-1-validation_and_storage/test_non_class_entry.py` confirms both that line 325 is reachable and that the validator behaves correctly for non-class non-string entries — promoting one of those cases into the permanent suite fixes the gap.

Why it matters: the slice in its current form would not pass CI; a future Worker 2 / Worker 3 cycle would have to re-open Slice 1 simply to add the missing case. The branch is also one of the seven Decision-4 rules (Decision 4 line 322 reads "Strings, sets, generators, and other invalid non-sequence values raise `ConfigurationError`"; "other invalid non-sequence values" at the entry level is exactly this branch).

Recommended change: extend `tests/types/test_relay_interfaces.py::test_meta_interfaces_rejects_non_interface_classes` (or add a small companion test such as `test_meta_interfaces_rejects_non_class_entries`) to feed at least one non-class non-string entry — e.g. `interfaces=(object(),)` or `interfaces=(42,)` — and assert `ConfigurationError` matching `"must contain interface classes"`. The temp test under `docs/builder/temp-tests/slice-1-validation_and_storage/test_non_class_entry.py` is ready for promotion as the smallest viable patch.

```django_strawberry_framework/types/base.py:324:9
        if not isinstance(entry, type):
            raise ConfigurationError(
                f"{meta.model.__name__}.Meta.interfaces must contain interface classes, got {entry!r}.",
            )
```

### Medium:

#### Repeated `must be a tuple/list` error-prefix literal

The top-level rejection messages at `django_strawberry_framework/types/base.py:300-303` (string-typed raw) and `django_strawberry_framework/types/base.py:309-312` (other non-sequence raw) share the long lead-in `"{meta.model.__name__}.Meta.interfaces must be a tuple/list of Strawberry interface classes or a single interface class, got ..."`. The shadow overview's "Repeated string literals" section confirms `must be a tuple/list` appears 2x (and the surrounding prefix is repeated by hand). Two sites is borderline; the spec is also explicit that future slices will not re-derive this validation, so the duplication is bounded to one helper. The helper's other error sites (entry-level `must contain interface classes`, `may not contain DjangoType`, `not a Strawberry interface`, duplicate listing) each appear exactly once, so this is the only repeated-literal site in the validator.

Why it matters: keeping the two top-level rejection messages in lockstep matters because tests `pytest.raises(..., match="must be a tuple/list")` pin the substring; drift between the two sites would silently break one of the parametrized rejection cases.

Recommended change: optional. If kept, a module-level constant such as `_INTERFACES_SHAPE_ERROR_LEAD_IN = "Meta.interfaces must be a tuple/list of Strawberry interface classes or a single interface class"` would let both sites read `f"{meta.model.__name__}.{_INTERFACES_SHAPE_ERROR_LEAD_IN}, got <variant>."` and would localize future wording updates. If left as-is, the two sites must remain in lockstep — Worker 2 may intentionally reject this finding with a recorded reason ("two sites only, not yet load-bearing across slices").

```django_strawberry_framework/types/base.py:300:9
            f"{meta.model.__name__}.Meta.interfaces must be a tuple/list of Strawberry "
            "interface classes or a single interface class, got a string.",
```
```django_strawberry_framework/types/base.py:309:9
            f"{meta.model.__name__}.Meta.interfaces must be a tuple/list of Strawberry "
            f"interface classes or a single interface class, got {type(raw).__name__}.",
```

### Low:

#### `sorted(set(duplicates))` is redundant; class-identity dedupe already happens upstream

At `django_strawberry_framework/types/base.py:348` the duplicates error message wraps `duplicates` in `set(...)` even though the upstream walk at line 341-345 uses `id(entry)` to avoid appending the same class twice. `duplicates` already contains at most one entry per duplicated class, so `sorted(set(duplicates))` collapses to `sorted(duplicates)`. The `set(...)` adds visual noise without affecting output; future readers may wonder whether the `set` is guarding against an upstream bug.

Recommended change: replace `sorted(set(duplicates))` with `sorted(duplicates)`. Optional polish; no behavior change.

```django_strawberry_framework/types/base.py:346:5
    if duplicates:
        raise ConfigurationError(
            f"{meta.model.__name__}.Meta.interfaces contains duplicate entries: {sorted(set(duplicates))}.",
        )
```

#### `(relay.Node)` parametrize case is identical to bare `relay.Node`

`tests/types/test_relay_interfaces.py:49-60` parametrizes three cases for `test_meta_interfaces_accepts_single_interface_class`: `relay.Node`, `(relay.Node,)`, and `(relay.Node)`. Python evaluates `(relay.Node)` to the bare class identity — it is not a tuple — so cases 1 and 3 produce the same object. Pytest renames the second `Node` to `Node1` in the parameter id, which can confuse a future maintainer scanning the parametrize block looking for three distinct shapes. The Slice 1 plan acknowledged this (Plan line 96: "Python sees this as plain `relay.Node`, identical to variant 1, but the spec lines 192-193 / 323 / 468 / 576 explicitly mention this spelling so it's tested verbatim"), so this is documented-intentional, not a bug. Recording as Low so a future reader does not silently dedupe the cases.

Recommended change: leave as-is, or add an inline comment in the parametrize list spelling out that the third case is the missing-comma spec spelling and is intentionally identical to the first.

```tests/types/test_relay_interfaces.py:49:1
@pytest.mark.parametrize(
    "raw",
    [
        relay.Node,
        (relay.Node,),
        (relay.Node),
    ],
)
```

### DRY findings

- **Repeated rejection-message lead-in.** `django_strawberry_framework/types/base.py:300-303` and `django_strawberry_framework/types/base.py:309-312` repeat the long `f"{meta.model.__name__}.Meta.interfaces must be a tuple/list of Strawberry interface classes or a single interface class, got ..."` lead-in across two sites. See the Medium finding above. The shadow overview's `Repeated string literals` flags `must be a tuple/list` (2x) which is the user-visible signal for this.
- **`{meta.model.__name__}.Meta.interfaces` prefix.** Every error in `_validate_interfaces` (six raise sites at lines 300, 309, 319, 325, 329, 336, 347) shares the prefix `f"{meta.model.__name__}.Meta.interfaces ..."`. This is the intentional re-use of the `_format_unknown_fields_error` shape per Decision 4 line 319, so it is a wanted DRY pattern, not a defect. The plan (Risk 1) is explicit that the validator should not route through `_format_unknown_fields_error` because the error categories differ; that justification holds. Worth carrying forward as Slice-2/3/4 add their own validators — they should all reuse this same prefix shape rather than inventing new error wording.
- **Test-file `must be a tuple/list` / `may not contain DjangoType` repeated literals.** The shadow overview for `tests/types/test_relay_interfaces.py` flags both substrings at 2x. These are intentional `pytest.raises(..., match=...)` substring pins covering separate cases (top-level string vs other non-sequence; `DjangoType` self vs subclass); promoting them to constants would obscure the rejection cases rather than help. Not a finding.
- **`getattr(meta, "interfaces", None)` is the canonical lookup site.** The plan (DRY analysis, "Patterns expected to recur in later slices") committed to a single read-site at the new validator. Slice 3 will need to ask "is `relay.Node` among the declared interfaces?" — that should read from `definition.interfaces` (already populated by Slice 1), not re-derive from `meta`. Worth carrying as a Slice-3/4 watch item; this slice itself does not duplicate the read.

### What looks solid

- The seven Decision-4 rules each map to a focused branch (str rejection → single-class normalization → tuple/list normalization → empty short-circuit → per-entry str-then-class-then-DjangoType-then-Strawberry-interface checks → duplicate detection by class identity). Reading top-to-bottom, the order is the spec's order.
- Error messages all keep the `<Model>.Meta.interfaces ...` lead-in consistent with `_format_unknown_fields_error` per Decision 4. The choice to inline rather than route through `_format_unknown_fields_error` is documented in the build report and matches the plan's Risk-1 reasoning (the helper's "unknown values + Available: ..." body doesn't fit interface-validator errors).
- `"interfaces"` is preserved in `DEFERRED_META_KEYS` at `django_strawberry_framework/types/base.py:58`; `tests/types/test_base.py:135-151` `test_meta_rejects_each_deferred_key` parametrization still includes it, so end-to-end use of `Meta.interfaces` still raises the deferred-key error first. Confirmed by inspecting the source: the deferred-key check at `base.py:385-389` runs before the new `return _validate_interfaces(meta)` at `base.py:395`.
- The normalized interfaces tuple flows from `_validate_meta` (`base.py:395`) into `__init_subclass__` (`base.py:97`) and then into the `DjangoTypeDefinition(...)` construction at `base.py:139` as `interfaces=interfaces`. No new dataclass slot was added — the field at `django_strawberry_framework/types/definition.py:42` is the storage shape the `0.0.4` foundation reserved.
- Boundary discipline. Slice 1 does not preemptively implement Slice-2's `is_type_of` injection, Slice-3's `id` annotation stripping, Slice-4's `cls.__bases__` mutation, or the composite-pk check. The three forward-looking TODO anchors at `base.py:84-86`, `base.py:566-569`, and `definition.py:32-34` are untouched. The deferred-key block-comment at `base.py:48-58` is also untouched (it stays until Slice 5 promotes the key).
- Test placement obeys `AGENTS.md` line 8 / line 14: the new tests live under `tests/types/test_relay_interfaces.py`, not under `tests/base/`; they use real example-project models (`apps.products.models.Category`) per `AGENTS.md` line 8.
- The autouse `_isolate_registry` fixture is mirrored from `tests/types/test_base.py:50-55` rather than imported, so the two modules stay independent — matches the build report's stated approach.
- Composite-pk test is staged with `pytest.mark.skip(reason="composite-pk check lives in Slice 4 / Phase 2.5; see spec line 431")`. The skip reason explicitly names Slice 4 and the spec line, so Slice 4's checklist can find it.
- Duplicate detection uses `id(entry)` rather than `==`, matching Python's class-identity semantics. Two distinct classes that happen to compare equal would not be wrongly conflated; conversely, two references to the same class (the common typo case) are caught.

### Temp test verification

- `docs/builder/temp-tests/slice-1-validation_and_storage/test_non_class_entry.py` — two tests (`test_instance_entry_rejected`, `test_int_instance_entry_rejected`) confirming the non-class non-string entry branch at `base.py:324-327` raises correctly. Both pass under focused pytest. **Disposition: recorded as the High finding above; Worker 2 should promote one of these cases into `tests/types/test_relay_interfaces.py` to close the coverage gap.** The temp file itself can stay until Worker 2 promotes a case, then be deleted at slice close.

### Notes for Worker 1 (spec reconciliation)

- Decision 4 line 323 reads "Strings, sets, generators, and other invalid non-sequence values raise `ConfigurationError`." The "other invalid non-sequence values" phrasing covers both the top-level shape rejection (line 309 in the implementation) and the per-entry "not a class" rejection (line 325). The spec language is consistent enough that no spec edit is needed; just naming the two sites here so Worker 1 can confirm during final verification.
- The plan flagged Open Question 2 ("`test_relay_node_with_composite_pk_raises` test placement") and Worker 2 chose the `pytest.mark.skip` placeholder route. The skip reason names Slice 4 explicitly. Accepted as the cleaner approach.
- The plan flagged Open Question 5 (helper placement within `types/base.py`). Worker 2 placed `_validate_interfaces` **after** `_validate_meta` rather than before. The diff reads correctly either way; recording so Worker 1 knows the deviation was intentional and documented in the build report.

### Review outcome

`revision-needed` — the single High finding (coverage gate breach on line 325) prevents acceptance. The fix is mechanical: promote one case from the temp test into the permanent suite. The Medium and Low findings are polish and can be addressed in the same Worker 2 re-pass or intentionally rejected with a recorded reason. After Worker 2 closes the High finding, this artifact should return to `built` and Worker 3 will re-review.

---

## Build report (Worker 2, pass 2)

### Files touched

- `django_strawberry_framework/types/base.py` — consolidated the duplicated `Meta.interfaces` shape-rejection lead-in into a module-level constant `_INTERFACES_SHAPE_ERROR_LEAD_IN` (Medium finding) and a small `_interfaces_shape_error(meta, got_suffix)` formatter; both top-level rejection sites (`isinstance(raw, str)` and `else`) now route through that helper so the substring `"must be a tuple/list"` cannot drift between them. Also dropped the redundant `set(...)` wrapper in the duplicates error from `sorted(set(duplicates))` to `sorted(duplicates)` (Low finding; class-identity dedupe already happens upstream at the walk).
- `tests/types/test_relay_interfaces.py` — added `test_meta_interfaces_rejects_non_class_entries` (parametrized over `object()` and `42`) which exercises the non-class non-string entry branch at `_validate_interfaces` (the line 325-equivalent rejection that the High finding flagged uncovered). Added an inline comment in the `test_meta_interfaces_accepts_single_interface_class` parametrize block spelling out that the third case `(relay.Node)` is the missing-comma spec spelling and is intentionally identical to the first (Low finding clarity).

No other files touched. The temp test directory under `docs/builder/temp-tests/slice-1-validation_and_storage/` was emptied (test file removed; only the gitignored directory shell remains).

### Tests added or updated

- `tests/types/test_relay_interfaces.py::test_meta_interfaces_rejects_non_class_entries[entry0]` (`object()`) — pins the non-class non-string entry branch. Promotes the temp test's `test_instance_entry_rejected` shape into the permanent suite.
- `tests/types/test_relay_interfaces.py::test_meta_interfaces_rejects_non_class_entries[42]` — pins the int-instance variant from the temp test's `test_int_instance_entry_rejected`.

All eleven prior Slice 1 tests still pass unchanged (the consolidation kept the `"must be a tuple/list"` substring intact for the `pytest.raises(..., match=...)` assertions).

### Validation run

- `uv run ruff format .` — pass (1 file reformatted: `types/base.py` re-wrapped the new constant; clean on confirmation re-run).
- `uv run ruff check --fix .` — pass (no auto-fixes needed).
- `uv run pytest tests/types/test_relay_interfaces.py --cov=django_strawberry_framework --cov-report=term-missing` — 17 passed, 1 skipped (the deferred `test_relay_node_with_composite_pk_raises` placeholder for Slice 4). The focused-file coverage shows `django_strawberry_framework/types/base.py` at 41% with the new helper region (lines 271-359) fully covered by these tests; the remaining missing lines belong to `__init_subclass__`, `_validate_meta` end-to-end, `_validate_optimizer_hints`, `_select_fields`, `_build_annotations`, etc., which are exercised by `tests/types/test_base.py` and other test modules — they are not coverage gaps introduced by this slice. The 33% total-coverage failure that pytest prints is expected: a single test file cannot cover the full package; the package-level 100% gate runs against the full `tests/` sweep, not this focused command.

### Findings addressed

- **High — coverage gate breach on the non-class non-string entry branch.** Fixed by adding `test_meta_interfaces_rejects_non_class_entries` in `tests/types/test_relay_interfaces.py` parametrized over an `object()` instance and an `int` instance. Both pin the `"must contain interface classes"` substring and exercise the branch at `django_strawberry_framework/types/base.py:333-336` (the post-format line numbers after the consolidation; was line 324-327 in Worker 3's review). The temp test under `docs/builder/temp-tests/slice-1-validation_and_storage/test_non_class_entry.py` was deleted in the same change per the task brief.
- **Medium — repeated `must be a tuple/list` rejection-prefix literal.** Fixed via consolidation: `_INTERFACES_SHAPE_ERROR_LEAD_IN` constant + `_interfaces_shape_error(meta, got_suffix)` formatter at `django_strawberry_framework/types/base.py:271-283`. Both raise sites now read `raise ConfigurationError(_interfaces_shape_error(meta, "a string"))` and `raise ConfigurationError(_interfaces_shape_error(meta, type(raw).__name__))` so the long lead-in lives in exactly one place. The existing `pytest.raises(..., match="must be a tuple/list")` assertions continue to pin the substring the helper outputs.
- **Low — `sorted(set(duplicates))` redundancy.** Fixed: now reads `sorted(duplicates)` at `django_strawberry_framework/types/base.py:357`. Class-identity dedupe at the walk (`if entry_id in seen_ids: duplicates.append(...)`) already guarantees `duplicates` contains at most one entry per duplicated class, so the `set(...)` wrapper was visual noise.
- **Low — `(relay.Node)` parametrize case is identical to bare `relay.Node`.** Addressed via inline comment in the parametrize list at `tests/types/test_relay_interfaces.py` explaining that Python evaluates `(relay.Node)` to the bare class identity (not a tuple) and the case is included verbatim per spec lines 192-193 / 323. A future maintainer scanning the block now sees the intent without having to consult the plan.

### Notes for Worker 3

- The consolidated lead-in lives at `django_strawberry_framework/types/base.py:271-283` (`_INTERFACES_SHAPE_ERROR_LEAD_IN` constant + `_interfaces_shape_error` formatter). Both shape-rejection sites in `_validate_interfaces` now call the formatter; the substring `"must be a tuple/list"` that the parametrized rejection tests pin still appears in the final formatted message via the constant. The constant deliberately holds only the lead-in (no trailing `", got ..."`) so the formatter owns the `got {suffix}` tail.
- The entry-level "must contain interface classes" rejection sites (line 329 for the string entry, line 335 for the non-class entry) are intentionally **not** consolidated. They share a shorter substring but the surrounding wording differs (the string-entry message also says "not strings (got <repr>). Lazy/forward-reference interface lookup is out of scope for 0.0.5." while the non-class entry message reads "got <repr>" only). Hoisting them would either bloat the helper signature with multiple optional tails or split into two helpers — neither pays for itself at two sites with categorically different trailing wording. Recording here so Worker 3 does not flag it as a missed DRY opportunity.
- The new `test_meta_interfaces_rejects_non_class_entries` parametrizes over `object()` and `42` (both non-class non-string). The branch the High finding flagged (`if not isinstance(entry, type):`) is unreachable for `int` as a class because `int` is itself a class — only `int` *instances* like `42` flow through. The test fixture passes `42` directly so the parametrization shape matches.
- `_validate_interfaces` is now a self-contained helper at `types/base.py:286-359`; the constant and formatter are above it at 271-283 so Slice 2/3/4 readers find the error scaffolding next to the validator that uses it.

### Notes for Worker 1 (spec reconciliation)

None.

---

## Review (Worker 3, pass 2)

### Prior-pass disposition

- **High — Coverage gate breach on the non-class non-string entry branch (former `base.py:325`).** Addressed correctly. Worker 2 promoted the temp test into the permanent suite as `tests/types/test_relay_interfaces.py::test_meta_interfaces_rejects_non_class_entries`, parametrized over `object()` and `42`. Focused-coverage re-run (`uv run pytest tests/types/test_relay_interfaces.py --cov=django_strawberry_framework.types.base --cov-report=term-missing`) confirms `_INTERFACES_SHAPE_ERROR_LEAD_IN`, `_interfaces_shape_error`, and `_validate_interfaces` (lines 271-359) are not in the missing-lines list — the new code is fully covered by the new test file. The line numbers shifted slightly post-consolidation; the rejection branch now lives at `django_strawberry_framework/types/base.py:333-336` and is exercised end-to-end.
- **Medium — Repeated `must be a tuple/list` error-prefix literal.** Addressed correctly. The lead-in is now a module-level constant at `django_strawberry_framework/types/base.py:271-273` (`_INTERFACES_SHAPE_ERROR_LEAD_IN`) plus a formatter `_interfaces_shape_error(meta, got_suffix)` at `base.py:276-283`. Both raise sites at `base.py:315` (string-typed raw) and `base.py:321` (other non-sequence raw) call the formatter. The substring `"must be a tuple/list"` that the parametrized rejection tests pin still appears in the final message via the constant.
- **Low — `sorted(set(duplicates))` redundancy.** Addressed correctly. Now reads `sorted(duplicates)` at `django_strawberry_framework/types/base.py:357`. Class-identity dedupe at the walk already guarantees `duplicates` contains at most one entry per duplicated class.
- **Low — `(relay.Node)` parametrize case is identical to bare `relay.Node`.** Addressed correctly. The inline comment now sits in the parametrize block at `tests/types/test_relay_interfaces.py:54-57` spelling out that Python evaluates `(relay.Node)` to the bare class identity and that the case is intentional per the spec.

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

- **New `_INTERFACES_SHAPE_ERROR_LEAD_IN` constant + `_interfaces_shape_error` formatter pair.** Cleanly single-responsibility. The constant holds only the lead-in (no trailing `", got ..."`); the formatter owns the `got {suffix}` tail. Both raise sites in `_validate_interfaces` now read identically modulo the suffix. The package has no existing generic error-formatter the new code could route through — `_format_unknown_fields_error` at `django_strawberry_framework/types/base.py:260-268` is shape-specific to "unknown values + Available: ..." (the original Risk-1 reasoning still holds), and there is no other module-level error helper in the package today. Adding a new helper for two sites is borderline; the helper pays for itself by (a) keeping the long lead-in out of the function body, (b) making the test substring pin (`"must be a tuple/list"`) point at exactly one source of truth, and (c) providing the same shape that Slice 4's composite-pk check (also a `Meta.interfaces`-rooted error) can route through if it wants the same `<Model>.Meta.interfaces` lead-in. Not a finding.
- **Entry-level "must contain interface classes" rejections not consolidated.** Worker 2 deliberately left the two entry-level sites (`base.py:329` string entry vs `base.py:335` non-class entry) un-hoisted, with the reason recorded in `Notes for Worker 3` of the pass-2 build report. The string-entry message has an extra trailing clause about lazy/forward-reference lookup; the non-class entry message does not. Hoisting them would force either a multi-tail helper signature or two helpers; neither pays for itself at two sites with categorically different trailing wording. Accepted.
- **Shared `f"{meta.model.__name__}.Meta.interfaces ..."` prefix.** Unchanged from pass 1: this is the intentional re-use of the `_format_unknown_fields_error` shape per Decision 4 line 319, and Slice-2/3/4 validators should keep using it. Carry-forward, not a finding.

### What looks solid

- The High coverage finding is resolved: focused `uv run pytest tests/types/test_relay_interfaces.py --cov=django_strawberry_framework.types.base --cov-report=term-missing` shows the new code at `base.py:271-359` is fully covered. The 33% total-coverage failure printed by pytest is expected (one test file cannot cover the whole package); the package-level 100% gate runs against the full `tests/` sweep, which is Worker 1's final-verification job.
- The consolidation kept the `"must be a tuple/list"` substring intact, so the four parametrized `test_meta_interfaces_rejects_non_sequence` cases and the string-top-level case in `test_meta_interfaces_rejects_string_entries` still pass against the formatter's output.
- The new `test_meta_interfaces_rejects_non_class_entries` parametrizes over `object()` (an instance — not a class — that is also not a string) and `42` (an `int` instance — same shape). Both pin the substring `"must contain interface classes"`, which is the same substring the tuple-of-string case in `test_meta_interfaces_rejects_string_entries` pins on. There is no test substring collision — the string-entry branch raises a longer message that still contains `"must contain interface classes"` as a prefix, so each branch is uniquely identified by its full match clause.
- Boundary discipline still holds. The pass-2 diff did not introduce composite-pk enforcement, `is_type_of` injection, `id` annotation stripping, interface-base injection, or any Relay resolver. Slice-2/3/4 TODO anchors remain in place. The `DEFERRED_META_KEYS` block at `base.py:41-60` is unchanged and `"interfaces"` is still in it.
- Standing rules. Line length is preserved (the constant line is 105 chars; the consolidated raise sites are short). Trailing commas appear on multi-arg calls. Test placement still obeys `AGENTS.md` (under `tests/types/`, real example-project model). The new parametrized test follows the same `_meta(interfaces=(entry,))` + `pytest.raises(ConfigurationError, match=...)` shape as the rest of the file.

### Temp test verification

- The pass-1 temp test at `docs/builder/temp-tests/slice-1-validation_and_storage/test_non_class_entry.py` has been deleted (Worker 2 confirmed in the pass-2 build report). Verified: `docs/builder/temp-tests/slice-1-validation_and_storage/` is empty.
- No new temp tests were created during this re-review; the focused-coverage `uv run pytest` command above gave sufficient signal to confirm the High finding was closed without additional scaffolding.

### Notes for Worker 1 (spec reconciliation)

- None. The pass-1 reconciliation notes (Decision 4 line 323 ambiguity around "other invalid non-sequence values" covering both the top-level shape rejection and the per-entry non-class rejection) still stand; no new ambiguities surfaced during this pass.

### Review tooling notes

- `scripts/review_inspect.py` was not re-run for this re-review pass. The pass-2 changes were small and structurally local: one new constant, one new formatter helper, one new parametrized test, one inline test comment, and one `set(...)` removal. Per `docs/builder/BUILD.md` "When to run the helper during build" the helper re-run is optional when pass-2 changes are this contained; the pass-1 shadow overview's signal (one repeated-literal hit on `"must be a tuple/list"`) was the basis for the Medium finding, and that hit is now structurally impossible because the lead-in lives in exactly one place. Skip recorded here per the BUILD.md exception clause.
- The focused coverage command `uv run pytest tests/types/test_relay_interfaces.py --cov=django_strawberry_framework.types.base --cov-report=term-missing` was run once during this re-review (per the BUILD.md exception for verifying the prior-pass High coverage finding). It is the only pytest run in this pass.

### Review outcome

`review-accepted` — every prior-pass finding (one High, one Medium, two Low) is addressed correctly; no new findings introduced in pass 2; the consolidated helper is single-responsibility and routes through one source of truth for the repeated lead-in; coverage of the new Slice 1 code is now 100% on `django_strawberry_framework/types/base.py:271-359`. Status flipped to `review-accepted`; Worker 1 takes the slice into final verification next.

---

## Final verification (Worker 1)

- **DRY check.** This is the first accepted slice in the build, so there are no prior accepted slices to compare against. Within the slice itself, the consolidated `_INTERFACES_SHAPE_ERROR_LEAD_IN` constant + `_interfaces_shape_error(meta, got_suffix)` formatter at `django_strawberry_framework/types/base.py:271-283` is single-responsibility: the constant holds the lead-in wording only (no trailing `", got ..."`); the formatter owns the `got {suffix}` tail. The two top-level shape-rejection sites in `_validate_interfaces` (`base.py:315` for `isinstance(raw, str)` and `base.py:321` for `else`) now route through the same formatter so the substring `"must be a tuple/list"` cannot drift between them. The two entry-level "must contain interface classes" sites (string entry at `base.py:329` vs non-class entry at `base.py:335`) are intentionally **not** hoisted because their trailing wording differs categorically (the string-entry message has the "Lazy/forward-reference interface lookup is out of scope for 0.0.5" clause; the non-class-entry message does not). Per Worker 2's pass-2 build report `Notes for Worker 3`, hoisting them would force either a multi-tail helper signature or two helpers; neither pays for itself at two sites with categorically different trailing wording. Agreed — the duplication risk for those two sites is bounded (one helper, immediate visual proximity in the function body) and the wording difference is content-driven, not stylistic. No new DRY violations introduced; the shared `f"{meta.model.__name__}.Meta.interfaces ..."` prefix across the six raise sites is the intentional reuse of the `_format_unknown_fields_error` shape per Decision 4 line 319 and should be carried forward into Slice 2/3/4 validators.
- **Existing tests.** Ran `uv run pytest tests/types/ --cov=django_strawberry_framework.types.base --cov-report=term-missing`: 108 passed, 2 skipped (`test_relay_module_imports_for_future_slice_anchor` placeholder for later slices, plus `test_relay_node_with_composite_pk_raises` staged for Slice 4 / Phase 2.5). No failures, no new warnings introduced by the slice. Coverage on `django_strawberry_framework/types/base.py` reports 97% under this focused command with missing lines at `93, 431, 449-451`; these are pre-existing branches (the `registry.is_finalized()` short-circuit in `__init_subclass__` and the unknown/excluded-hint and bad-OptimizerHint-value rejection paths in `_validate_optimizer_hints`) covered by other test trees (`tests/test_registry.py` for the finalized short-circuit, `tests/types/test_optimizer_hints.py` and `tests/types/test_base.py` for the optimizer-hint paths), not coverage gaps introduced by Slice 1. The new Slice 1 code at `base.py:271-359` (the `_INTERFACES_SHAPE_ERROR_LEAD_IN` constant, the `_interfaces_shape_error` formatter, and the entire `_validate_interfaces` helper) is not in the missing-lines list — fully covered by the new tests in `tests/types/test_relay_interfaces.py`. Per BUILD.md "Final test-run gate" the package-level 100% gate is the build-closing pass, not slice-local final verification; this gate only requires that existing tests still pass for the focused scope, which they do.
- **Spec reconciliation.** No spec edit needed. Reviewed the two reconciliation notes from the review passes: (1) Worker 3 pass-1's Decision 4 line 323 observation — "Strings, sets, generators, and other invalid non-sequence values raise `ConfigurationError`" cleanly covers both the top-level shape rejection at `base.py:315/321` and the per-entry non-class rejection at `base.py:335`; the spec wording is consistent enough that no edit is required. (2) Worker 2's `pytest.mark.skip` placement for `test_relay_node_with_composite_pk_raises` is faithful to Decision 4 line 330 / Decision 5 / implementation-plan step 1 line 431 — the spec is internally consistent that the composite-pk check lives in Phase 2.5 (Slice 4); the test name appears under Slice 1's checklist (spec line 29) because the file `tests/types/test_relay_interfaces.py` is introduced by Slice 1, but the body is reserved for Slice 4. The skip reason explicitly names "Slice 4 / Phase 2.5" and cites spec line 431, so Slice 4's checklist can find it. No ambiguity to resolve.

### Summary

Slice 1 lands the validation and storage half of `Meta.interfaces` support. `_validate_interfaces` in `django_strawberry_framework/types/base.py` normalizes the raw `Meta.interfaces` value (accepting tuples/lists or a single Strawberry interface class such as `interfaces = relay.Node`, including the missing-comma spelling `interfaces = (relay.Node)`), rejects strings, sets, generators, and other non-sequence shapes, then walks each entry and rejects strings, non-class entries, `DjangoType` self-references / subclasses, classes that are not real Strawberry interfaces (`__strawberry_definition__.is_interface` must be `True`), and duplicates. The normalized `tuple[type, ...]` is returned from `_validate_meta` (signature changed from `None` to `tuple[type, ...]`), captured in `__init_subclass__`, and threaded through to the existing `DjangoTypeDefinition.interfaces` slot at `django_strawberry_framework/types/definition.py:42` — no new dataclass field. The error scaffolding (`_INTERFACES_SHAPE_ERROR_LEAD_IN` constant + `_interfaces_shape_error` formatter) consolidates the long top-level shape-rejection lead-in so the test-pinned substring `"must be a tuple/list"` cannot drift between the two shape-rejection sites. `"interfaces"` remains in `DEFERRED_META_KEYS` until Slice 5 promotes it; the new validator is reachable end-to-end only after that promotion, so Slice 1 tests in `tests/types/test_relay_interfaces.py` call `_validate_interfaces` directly as a unit (with one `DjangoTypeDefinition` construction test for the storage contract). The composite-pk check from Decision 2 is staged with `pytest.mark.skip` and explicitly deferred to Slice 4 / Phase 2.5. Three TODO anchors are removed in the same change that ships the behavior (the anchor in `__init_subclass__` above the `DjangoTypeDefinition(...)` call, the anchor at the tail of `_validate_meta`, and the comment block above `DjangoTypeDefinition.interfaces` in `definition.py`); the three Slice-2/3/4 anchors and the `DEFERRED_META_KEYS` block comment are untouched.

### Spec changes made (Worker 1 only)

No spec edits.

### Final status

`final-accepted`
