# Build: Slice 1 — `Meta.globalid_strategy` net-new key + `RELAY_GLOBALID_STRATEGY` setting read + precedence resolver

Spec reference: `docs/spec-031-globalid_encoding-0_0_9.md` (lines 84-88)
Status: final-accepted

## Plan (Worker 1)

This slice ships the foundation for the GlobalID-encoding feature: the per-type
opt-in (`Meta.globalid_strategy`), its storage on the canonical definition, the
schema-wide setting read, and the precedence resolver. It writes NO encode/decode
logic — Slices 2/3 consume what this slice pins. The two load-bearing contracts
Slices 2/3 depend on are (a) the definition slot name `DjangoTypeDefinition.globalid_strategy`
(raw normalized value), and (b) the resolver signature `_resolve_globalid_strategy(definition) -> str | Callable`.

Verified against the current source before planning:
- `types/base.py::ALLOWED_META_KEYS` is a `frozenset` at `base.py #"ALLOWED_META_KEYS: frozenset[str]"` (base.py:53-69); `DEFERRED_META_KEYS` at base.py:49-51 holds `{"aggregate_class", "fields_class", "search_fields"}` (NOT touched by this slice).
- `types/base.py::_validate_connection(meta, connection, relay_shaped)` (base.py:145-188) is the cited structural model: `None`-short-circuit → shape checks → `relay_shaped` gate → return normalized value.
- `types/base.py::_validate_meta` (base.py:691-809) computes `relay_shaped = _is_relay_shaped(cls, interfaces)` once (base.py:772) and threads it into `_validate_connection` (base.py:775). It returns a `_ValidatedMeta` NamedTuple (base.py:669-688) bundling every validated key.
- `types/base.py::_is_relay_shaped(cls, interfaces)` (base.py:260-271) is the canonical predicate, True for both the `Meta.interfaces` tuple spelling and direct `relay.Node` inheritance.
- `DjangoType.__init_subclass__` constructs `DjangoTypeDefinition(...)` at base.py:377-401, passing the validated slots (`connection=validated.connection` at base.py:397); the Slice-1 TODO anchor sits at base.py:398-400.
- `types/definition.py::DjangoTypeDefinition` (definition.py:15-205) is a `@dataclass`; the defaulted-field block ends `connection: dict | None = None` at definition.py:108 with the Slice-1/2 TODO anchor at definition.py:109-113 and `finalized: bool = False` at definition.py:114. `from typing import Any, Literal` is already imported (definition.py:6); `Callable` is NOT yet imported.
- `types/relay.py` already imports `inspect` (relay.py:25) and `from collections.abc import Callable` (relay.py:26); `from ..exceptions import ConfigurationError` (relay.py:35). The `_resolve_globalid_strategy` home is pinned by the TODO anchor at relay.py:318-342 ("Keep the GlobalID strategy helpers in this Relay foundation module").
- `conf.py::settings` (conf.py:159) raises `AttributeError` on a missing key (conf.py:133-156); no `RELAY_GLOBALID_STRATEGY` key exists. A non-mapping top-level `DJANGO_STRAWBERRY_FRAMEWORK` raises `ConfigurationError` (conf.py:77-80) — that propagates through a defensive read by design and is the existing contract, not this slice's concern.
- `tests/types/test_base.py` already has an autouse `_isolate_registry` fixture (test_base.py:55-60) and a Slice-1 TODO stub (test_base.py:106-116) describing the exact assertions to add; the `connection` tests (test_base.py:307-397) are the assertion-shape model.

### DRY analysis

**Existing patterns reused.**
- `types/base.py::_validate_connection` (base.py:145-188) is the verbatim structural model for the new `_validate_globalid_strategy(meta, value, relay_shaped)`: same `None`-short-circuit-returns-`None`, same `relay_shaped` gate with the same remediation-message style (`"...requires a Relay-Node-shaped type; add `relay.Node` to `Meta.interfaces`..."`, base.py:183-187), same return-the-normalized-value contract. Spec Decision 6 names this precedent explicitly.
- `types/base.py::_is_relay_shaped(cls, interfaces)` (base.py:260-271) is reused unchanged as the single-source Relay-shape predicate; the slice threads the already-computed `relay_shaped` bool (base.py:772) into the new validator exactly as `_validate_connection` receives it (base.py:775) — NOT recomputed.
- The `connection` / `filterset_class` / `orderset_class` definition-slot pattern (base.py:395-397 → definition.py:106-108) is reused verbatim for the new `globalid_strategy` slot: validate in `_validate_meta`, bundle on `_ValidatedMeta`, pass `globalid_strategy=validated.globalid_strategy` at the `DjangoTypeDefinition(...)` call (base.py:377-401), declare a defaulted dataclass field on `DjangoTypeDefinition`.
- `types/base.py`'s in-function-import cycle-dodge (the `from ..filters.sets import FilterSet` pattern at base.py:107 with its load-cycle comment at base.py:105-106, and the identical `OrderSet` pattern at base.py:133-135) is the reused pattern for `relay.py`'s `_resolve_globalid_strategy` reaching back into `base.py` for `_validate_globalid_strategy` (see "New helpers justified" — the inverse direction, same justification).
- `conf.py::settings` attribute access (conf.py:133-156) is reused as the setting read; the precedence helper reads it defensively (`getattr(conf.settings, "RELAY_GLOBALID_STRATEGY", None)`) so a missing key → `None` → fall through to the package default, honoring the "absent → package default" wording in spec line 87. `tests/filters/test_inputs.py` (test_inputs.py:890-988) demonstrates the `settings.DJANGO_STRAWBERRY_FRAMEWORK = {...}` test-override pattern the precedence test reuses.
- `tests/types/test_base.py` autouse `_isolate_registry` (test_base.py:55-60) and the `connection` test bodies (test_base.py:307-397) are the reused fixture + assertion-shape model for the new tests.

**New helpers justified.**
- `types/base.py::_validate_globalid_strategy(meta, value, relay_shaped, *, source=...)` — single responsibility: validate ONE `globalid_strategy`-shaped value (a `Meta` value OR a setting value) and return the normalized form. It is the ONE validator both call sites share (the `Meta` path via `_validate_meta`, the setting path via `_resolve_globalid_strategy`), per spec Decisions 6/7's "one validator, two sources, source-specific error text" rule. Source-specific error text is achieved by a `source` discriminator (default the `Meta` framing naming the type via `meta.model.__name__`; the setting framing naming `RELAY_GLOBALID_STRATEGY`). The callable arity/sync-ness check (`inspect.signature` must accept the four positional params `(type_cls, model, root, info)`; `inspect.iscoroutinefunction` must be `False`) lives in this one helper so it is not duplicated across the `Meta` and setting paths. Worker 2 has discretion on the exact `source` parameter spelling (see Implementation discretion items).
- `types/relay.py::_resolve_globalid_strategy(definition)` — single responsibility: apply the three-tier precedence (`definition.globalid_strategy` → `conf.settings.RELAY_GLOBALID_STRATEGY` → `"model"`) and return the resolved raw strategy (string or callable), validating the setting branch through `_validate_globalid_strategy`. It serves the Slice-2 `install_globalid_typename_resolver` call site (relay.py TODO at relay.py:329-336). Home is `types/relay.py` per the pinned TODO (relay.py:318-321 / definition TODO). The `relay_shaped` argument the validator expects is `True` for the setting branch (the resolver is only ever called for a Relay-Node-shaped type at finalization — the gate already passed at type creation), so the setting-path call passes `relay_shaped=True` and `source=` the setting framing.

**Duplication risk avoided.**
- The callable arity/sync validation could be naively written twice (once for `Meta`, once for the setting). The plan forbids that: the single `_validate_globalid_strategy` is the only place the `inspect.signature`/`iscoroutinefunction` logic lives; `_resolve_globalid_strategy` calls it rather than re-implementing.
- The valid-strategy string set `{"model", "type", "type+model"}` could become a parallel literal in the validator, the resolver, and later the encoder/decoder. This slice pins it as ONE named module-level constant in `types/base.py` (e.g. `STRING_GLOBALID_STRATEGIES = frozenset({"model", "type", "type+model"})`), exported for reuse so Slice 2's encoder and Slice 3's decoder reference the same source of truth rather than re-typing the set (build-plan DRY watch point, build-031 plan "DRY-first rule"). Worker 2 has discretion on the constant's exact name; the requirement is that it is named once and not duplicated.
- The Relay-shape predicate is NOT recomputed: the slice reuses the `relay_shaped` bool `_validate_meta` already computes (base.py:772), exactly as `_validate_connection` does (base.py:775).
- The `"model"` default literal recurs in the resolver and (Slice 2) the encoder default. To keep one source of truth, plan a named default constant (e.g. `DEFAULT_GLOBALID_STRATEGY = "model"`) alongside the string-set constant in `types/base.py`. Worker 2 discretion on the name; the requirement is single-sourcing.

### Implementation steps

Line numbers are pin-at-write-time navigational hints — verify against current source before editing.

1. **`django_strawberry_framework/types/base.py` — add the strategy constants.** Near the `ALLOWED_META_KEYS` / `DEFERRED_META_KEYS` block (base.py:49-74), add `STRING_GLOBALID_STRATEGIES = frozenset({"model", "type", "type+model"})` and `DEFAULT_GLOBALID_STRATEGY = "model"` (names at Worker 2 discretion). These are the single source of truth Slices 2/3 reuse for the encoder default and the decode-shape enforcement.
2. **`django_strawberry_framework/types/base.py::ALLOWED_META_KEYS` — grow the set.** Add `"globalid_strategy"` to the `ALLOWED_META_KEYS` frozenset (base.py:53-69). Do NOT touch `DEFERRED_META_KEYS` (base.py:49-51). Update the net-new-key comment block (base.py:70-74) to name `globalid_strategy` (spec-031 Decision 6) alongside the existing spec-029/spec-030 keys, and remove the now-satisfied Slice-1 TODO at base.py:76-88.
3. **`django_strawberry_framework/types/base.py` — add `_validate_globalid_strategy`.** Place it immediately after `_validate_connection` (after base.py:188), structurally modeled on it. Signature: `_validate_globalid_strategy(meta, value, relay_shaped, *, source=<Meta framing>) -> str | Callable | None`. Logic (spec Decision 6, base.py:358-363):
   - `value is None` → return `None`.
   - `value` a string in `STRING_GLOBALID_STRATEGIES` → return it.
   - `value` a string NOT in the set (and not callable) → `ConfigurationError` naming the offending value and listing the valid strategies (typo guard).
   - `value` callable → validate via `inspect.signature(value)` accepts the four positional params `(type_cls, model, root, info)` AND `inspect.iscoroutinefunction(value)` is `False`; a wrong-arity or `async def` callable → `ConfigurationError` naming the expected `(type_cls, model, root, info) -> str` shape; otherwise return the callable.
   - `value` neither string nor callable (wrong type, e.g. `42`) → `ConfigurationError`.
   - the key on a non-Relay-Node type — `relay_shaped` is `False` → `ConfigurationError` ("`Meta.globalid_strategy` requires a Relay-Node-shaped type; add `relay.Node` to `Meta.interfaces` or remove the key"), mirroring `_validate_connection`'s gate (base.py:183-187).
   - Error text is source-specific: the `Meta` framing names the type (via `meta.model.__name__`, as `_validate_connection` does at base.py:170 etc.); the setting framing names `RELAY_GLOBALID_STRATEGY`. The `relay_shaped` gate is a `Meta`-only concern — under the setting framing it does not apply (the per-type gate already ran at type creation), so the setting call passes `relay_shaped=True`.
   - `inspect` is already imported by `base.py`? Confirm — `base.py` imports `re`, `typing`, etc. (base.py:29-32) but NOT `inspect`. Add `import inspect` to the `base.py` standard-import block. (`relay.py` already imports `inspect` at relay.py:25.)
4. **`django_strawberry_framework/types/base.py::_validate_meta` — wire the validator in.** After the `connection = _validate_connection(...)` line (base.py:775), add `globalid_strategy = _validate_globalid_strategy(meta, getattr(meta, "globalid_strategy", None), relay_shaped)` using the already-computed `relay_shaped` (base.py:772).
5. **`django_strawberry_framework/types/base.py::_ValidatedMeta` — add the field.** Add `globalid_strategy: str | Callable[..., str] | None` to the `_ValidatedMeta` NamedTuple (base.py:669-688) and include it in the `return _ValidatedMeta(...)` construction (base.py:798-809). `Callable` must be importable — `base.py` imports from `collections.abc`? It imports `Mapping, Sequence` from `collections.abc` (base.py:31); add `Callable` to that import (or use `typing.Callable` — Worker 2 discretion, match the file's prevailing style).
6. **`django_strawberry_framework/types/base.py::DjangoType.__init_subclass__` — pass it to the definition.** Replace the Slice-1 TODO at base.py:398-400 with `globalid_strategy=validated.globalid_strategy,` in the `DjangoTypeDefinition(...)` call (base.py:377-401), mirroring `connection=validated.connection` (base.py:397).
7. **`django_strawberry_framework/types/definition.py::DjangoTypeDefinition` — add the raw slot.** Add `globalid_strategy: str | Callable[..., str] | None = None` to the defaulted-field block (after `connection: dict | None = None`, definition.py:108), per the TODO at definition.py:109-113. NOTE: this slice adds ONLY the raw `globalid_strategy` slot; the `effective_globalid_strategy: str | None = None` field named in the same TODO is a **Slice 2** deliverable (it is finalization-set, not class-creation-set — spec Decision 10) and is OUT OF SCOPE here. Import `Callable` (`from collections.abc import Callable` or `typing.Callable`; `from typing import Any, Literal` is already present at definition.py:6 — Worker 2 discretion, match file style). Update the dataclass docstring's TODO at definition.py:70-75 to describe the now-present `globalid_strategy` raw slot and leave the `effective_globalid_strategy` portion as a Slice-2 TODO.
8. **`django_strawberry_framework/types/relay.py` — add `_resolve_globalid_strategy(definition)`.** Place it near the GlobalID-strategy TODO (relay.py:318-342). Logic (spec Decision 5, spec line 87):
   - `strategy = definition.globalid_strategy` (the `Meta` override); if not `None`, return it (already validated at type creation — no re-validation needed).
   - else read the setting defensively: `setting = getattr(conf.settings, "RELAY_GLOBALID_STRATEGY", None)`; if not `None`, run it through `_validate_globalid_strategy(meta=None, value=setting, relay_shaped=True, source=<setting framing>)` and return the validated value (unknown string / wrong-arity / `async def` callable → `ConfigurationError` naming `RELAY_GLOBALID_STRATEGY`).
   - else return the `DEFAULT_GLOBALID_STRATEGY` (`"model"`).
   - Use an **in-function import** for both `_validate_globalid_strategy`/the default constant from `..types.base` (or `from .base import ...`) AND `from ..conf import settings as conf_settings` — `base.py` imports `install_is_type_of` from `relay.py` at module top (base.py:47), so a module-top `relay.py → base.py` import would close the load cycle. `_resolve_globalid_strategy` is only called at finalization (Slice 2), well after module load, so the in-function import resolves cheaply — the identical justification `base.py` documents for its `FilterSet`/`OrderSet` in-function imports (base.py:105-106, 133-134). Add the cycle-dodge comment.
   - The `_validate_globalid_strategy` signature must accommodate `meta=None` for the setting path; the `source` discriminator selects the setting error framing so no `meta.model.__name__` access happens on the setting branch.

   NOTE: `_resolve_globalid_strategy` is created in THIS slice but its only caller (`install_globalid_typename_resolver`) lands in Slice 2. The focused precedence test (step below) is what exercises it in this slice.

### Test additions / updates

All package-internal; pinned to `tests/types/test_base.py` per spec Test plan "Slice 1" (spec.md:566-573) and the existing Slice-1 TODO stub (test_base.py:106-116). The autouse `_isolate_registry` fixture (test_base.py:55-60) keeps each test clean. Use a fakeshop model (e.g. `Category`/`Item`) + `interfaces = (relay.Node,)` for the Relay-shaped types, mirroring the `connection` tests (test_base.py:307-397). Settings overrides reuse the `settings.DJANGO_STRAWBERRY_FRAMEWORK = {...}` pattern (test_inputs.py:890-988); restore/clear via the test harness's existing settings-reload conventions.

- `test_meta_globalid_strategy_in_allowed_meta_keys` — `"globalid_strategy" in ALLOWED_META_KEYS` and `"globalid_strategy" not in DEFERRED_META_KEYS` (mirror `test_meta_connection_in_allowed_meta_keys`, test_base.py:307-316).
- `test_meta_globalid_strategy_unknown_string_raises` — `Meta.globalid_strategy = "modle"` on a Relay-Node type raises `ConfigurationError` (typo guard).
- `test_meta_globalid_strategy_non_relay_type_raises` — `Meta.globalid_strategy = "model"` on a type whose `interfaces` omits `relay.Node` raises `ConfigurationError` (the `relay_shaped` gate; mirror `test_meta_connection_non_relay_type_raises`, test_base.py:361-369).
- `test_meta_globalid_strategy_wrong_type_raises` — `Meta.globalid_strategy = 42` (neither string nor callable) raises `ConfigurationError`.
- `test_meta_globalid_strategy_callable_accepted` — a well-formed `def enc(type_cls, model, root, info): ...` validates and is stored (no raise).
- `test_meta_globalid_strategy_callable_wrong_arity_raises` — `def enc(type_cls, model): ...` raises `ConfigurationError` at type creation (the `inspect.signature` check).
- `test_meta_globalid_strategy_async_callable_raises` — `async def enc(type_cls, model, root, info): ...` raises `ConfigurationError` at type creation (the `inspect.iscoroutinefunction` check).
- `test_meta_globalid_strategy_stored_on_definition` — `NodeType.__django_strawberry_definition__.globalid_strategy == "model"` (and the callable case stores the callable object); mirror `test_meta_connection_stored_on_definition` (test_base.py:396-397).
- `test_resolve_globalid_strategy_precedence` — pins the three tiers AND the unknown-setting failure:
  - `Meta.globalid_strategy = "type"` + a `RELAY_GLOBALID_STRATEGY = "type+model"` setting → resolver returns `"type"` (Meta beats setting).
  - no `Meta` key + `RELAY_GLOBALID_STRATEGY = "type"` setting → resolver returns `"type"` (setting beats default).
  - no `Meta` key + no setting → resolver returns `"model"` (package default).
  - no `Meta` key + `RELAY_GLOBALID_STRATEGY = "nonsense"` setting → `ConfigurationError` whose message names `RELAY_GLOBALID_STRATEGY` (the setting-path framing, distinct from the type-named `Meta` framing).
  - Import `_resolve_globalid_strategy` from `django_strawberry_framework.types.relay`; build a Relay-Node `DjangoType`, read its `__django_strawberry_definition__`, and call the resolver on it under each settings state.

Temp/scratch tests: none required — every assertion is package-internal and directly covers a Slice-1 contract. Worker 3 should confirm the precedence test exercises all four branches (Meta-wins, setting-wins, default, unknown-setting-raises) since the resolver's branches are otherwise only reachable from Slice 2's call site.

### Implementation discretion items

These are assessed and intentionally delegated to Worker 2 (equivalent-shape / naming choices):

- The exact spelling of the strategy constants (`STRING_GLOBALID_STRATEGIES`, `DEFAULT_GLOBALID_STRATEGY`) — any clear name; the requirement is single-sourcing, not the literal name.
- The `_validate_globalid_strategy` source-discriminator mechanism — a keyword `source="meta"|"setting"` enum-ish string, a separate `setting_name` kwarg, or two thin wrappers around a shared core — any shape that yields source-specific error text (type-named vs `RELAY_GLOBALID_STRATEGY`-named) and keeps the arity/sync logic single-sited. Whatever shape is chosen must accept the setting path's `meta=None`.
- `Callable` import source (`collections.abc.Callable` vs `typing.Callable`) in `base.py` and `definition.py` — match each file's prevailing style.
- The precise `inspect.signature` arity-check formulation (counting positional-or-keyword params, tolerating `*args`/defaults, etc.) — Worker 2 picks the formulation that accepts a plain `(type_cls, model, root, info)` def and rejects a 2-arg def and an `async def`; the spec fixes only the four-positional-parameter contract and the sync-ness requirement.
- Whether `_resolve_globalid_strategy` re-imports `conf.settings` in-function or accepts it as a param — in-function import is the planned shape (matches `base.py`'s cycle-dodge precedent), but the equivalent passing-by-param shape is acceptable if it reads cleaner at the Slice-2 call site (Worker 2's call, since Worker 2 owns the Slice-2 wiring).
- Exact wording of the new/updated comments and the `ConfigurationError` messages, within the spec's required content (offending value + valid strategies for the typo guard; the `(type_cls, model, root, info) -> str` shape for the callable guard; the `relay.Node`-remediation for the gate; `RELAY_GLOBALID_STRATEGY` named in the setting-path error).

No unresolved architectural questions — nothing escalated to the maintainer.

### Spec slice checklist (verbatim)

- [x] [`django_strawberry_framework/types/base.py::ALLOWED_META_KEYS`][base] grows `"globalid_strategy"` (net-new public key — NOT a [`DEFERRED_META_KEYS`][base] promotion, mirroring [`spec-030`][spec-030] [Decision 8][spec-030] and [`spec-029`][spec-029] [Decision 6][spec-029]). A `_validate_globalid_strategy` helper (called from [`_validate_meta`][base], structurally modeled on `_validate_connection`) accepts `"model"` / `"type"` / `"type+model"` or a callable; an unknown string or wrong type raises [`ConfigurationError`][glossary-configurationerror]; a callable is **validated for arity and sync-ness** via `inspect.signature` (must accept `(type_cls, model, root, info)`) and `inspect.iscoroutinefunction` (must be False), so a wrong-arity or `async def` encoder fails at type creation rather than as a raw `TypeError` / coroutine per request ([`docs/feedback.md`][feedback] P2); the key is gated to a Relay-Node-shaped type via the precomputed `relay_shaped` bool (`_is_relay_shaped(cls, interfaces)`).
- [x] The normalized value is **stored on [`DjangoTypeDefinition`][definition]** (a new `globalid_strategy` slot, populated in [`__init_subclass__`][base] like the `connection` / `filterset_class` / `orderset_class` slots) so the Phase-2.5 injection reads the per-type opt-in from the definition, not by re-parsing `Meta`.
- [x] A `_resolve_globalid_strategy(definition)` helper applies the precedence — `definition.globalid_strategy` (the `Meta` override) → [`conf.settings`][conf]`.RELAY_GLOBALID_STRATEGY` (the schema-wide setting, read defensively as "absent → package default") → the `"model"` package default — and validates the **setting** value through the **same** `_validate_globalid_strategy` rule the `Meta` path uses (unknown string, wrong-arity callable, or `async def` callable → [`ConfigurationError`][glossary-configurationerror] naming `RELAY_GLOBALID_STRATEGY`, [`docs/feedback.md`][feedback] P2), since [`conf.py`][conf] is a thin reader that does not validate domain values.
- [x] Package coverage: [`tests/types/test_base.py`][test-types-base] gains the `"globalid_strategy"`-in-`ALLOWED_META_KEYS` / not-in-`DEFERRED_META_KEYS` assertion, the `_validate_globalid_strategy` failure modes (unknown string, non-Relay type, wrong type, **callable wrong-arity, `async def` callable**), and the `definition.globalid_strategy` storage assertion. A focused `tests/types/` test pins the three-tier precedence and the unknown-setting `ConfigurationError`.

---

## Build report (Worker 2)

### Files touched

- `django_strawberry_framework/types/base.py` — added `import inspect` and `Callable` to the `collections.abc` import; grew `ALLOWED_META_KEYS` with `"globalid_strategy"` and updated the net-new-key comment block (removing the now-satisfied Slice-1 TODO); added the single-source `STRING_GLOBALID_STRATEGIES` frozenset + `DEFAULT_GLOBALID_STRATEGY` constants; added `_validate_globalid_strategy(meta, value, relay_shaped, *, source="meta")` (modeled on `_validate_connection`) plus a small `_validate_globalid_callable` helper and the `_GLOBALID_CALLABLE_PARAMS` tuple; wired the validator into `_validate_meta` (using the already-computed `relay_shaped`), added the `globalid_strategy` field to the `_ValidatedMeta` NamedTuple and its construction; passed `globalid_strategy=validated.globalid_strategy` to the `DjangoTypeDefinition(...)` call (replacing the Slice-1 TODO).
- `django_strawberry_framework/types/definition.py` — added `from collections.abc import Callable`; added the raw `globalid_strategy: str | Callable[..., str] | None = None` defaulted field; rewrote the docstring TODO to describe the now-present raw slot and narrowed the remaining TODO to the Slice-2-only `effective_globalid_strategy` field.
- `django_strawberry_framework/types/relay.py` — replaced the resolver-pseudocode portion of the GlobalID TODO with the real `_resolve_globalid_strategy(definition)` (three-tier precedence, in-function imports of `conf.settings` + `base.DEFAULT_GLOBALID_STRATEGY` / `_validate_globalid_strategy` to dodge the `relay -> base` load cycle); left the encode-install / decode pseudocode TODO for Slices 2-3.
- `tests/types/test_base.py` — removed the satisfied Slice-1 TODO stub; added a `spec-031 Slice 1` test section (10 tests; see below).

### Tests added or updated

- `tests/types/test_base.py::test_meta_globalid_strategy_in_allowed_meta_keys` — `"globalid_strategy"` in `ALLOWED_META_KEYS` and not in `DEFERRED_META_KEYS`.
- `::test_meta_globalid_strategy_unknown_string_raises` — `"modle"` typo on a Relay type → `ConfigurationError`.
- `::test_meta_globalid_strategy_non_relay_type_raises` — `"model"` on a non-Relay type → `ConfigurationError` (the `relay_shaped` gate).
- `::test_meta_globalid_strategy_wrong_type_raises` — `42` (non-string, non-callable) → `ConfigurationError`.
- `::test_meta_globalid_strategy_callable_accepted_and_stored` — a well-formed `(type_cls, model, root, info)` encoder validates and is stored as the callable object.
- `::test_meta_globalid_strategy_callable_wrong_arity_raises` — a 2-arg encoder → `ConfigurationError` at type creation (the `inspect.signature` bind check).
- `::test_meta_globalid_strategy_async_callable_raises` — an `async def` encoder → `ConfigurationError` at type creation (the sync-ness check).
- `::test_meta_globalid_strategy_stored_on_definition` — `"model"` lands on `definition.globalid_strategy`.
- `::test_meta_globalid_strategy_absent_leaves_definition_none` — absent key leaves the raw slot at its `None` default.
- `::test_resolve_globalid_strategy_precedence` — pins all four resolver branches: Meta-wins, setting-wins, package-default, and unknown-setting `ConfigurationError` (message names `RELAY_GLOBALID_STRATEGY`), driven via the pytest-django `settings` fixture.

### Validation run

- `uv run ruff format .` — pass (reformatted `types/base.py`: the `subject` ternary wrapped onto its own lines; no semantic change).
- `uv run ruff check --fix .` — pass ("All checks passed!").
- `git status --short` after both ruff invocations — modified files, all slice-intended (appear in `### Files touched`):
  - `M django_strawberry_framework/types/base.py` — slice-intended.
  - `M django_strawberry_framework/types/definition.py` — slice-intended.
  - `M django_strawberry_framework/types/relay.py` — slice-intended.
  - `M tests/types/test_base.py` — slice-intended.
  - `?? docs/builder/build-031-globalid_encoding-0_0_9.md`, `?? docs/builder/bld-slice-1-globalid_strategy_key.md` — the build cycle's own plan + this artifact (maintainer-committed cycle artifacts, not tool churn).
  - No unrelated tool churn; nothing reverted. The spec-030 build-artifact deletions noted in the build plan's pre-flight are NOT present in the tree (already handled by the maintainer's concurrent "archive 030" commit — left untouched per the dispatch note).
- Focused tests (optional, no `--cov*` flags): `uv run pytest --no-cov tests/types/test_base.py -k "globalid_strategy or resolve_globalid"` → 10 passed; full-file `uv run pytest --no-cov tests/types/test_base.py` → 89 passed (no regression from the `_ValidatedMeta` field addition).

### Implementation notes

- **`source` discriminator shape.** Chose a `source: str = "meta"` keyword (values `"meta"` / `"setting"`) over two wrapper functions or a `setting_name` kwarg (Worker 1 discretion item). It keeps the arity/sync logic single-sited and reads the source framing inline; `is_meta = source == "meta"` drives both the `subject` string and the Relay-gate skip.
- **Relay-gate placement.** The `relay_shaped` gate runs AFTER shape/typo/callable validation (matching `_validate_connection`, which shape-checks before gating), and is skipped on the `"setting"` path — so an unknown setting string still surfaces its typo error rather than a misleading relay-shape error.
- **Callable arity check via `inspect.signature(value).bind(*_GLOBALID_CALLABLE_PARAMS)`.** Picked `.bind(...)` over manual parameter counting (Worker 1 discretion item) because it naturally tolerates defaults / `*args` while rejecting a 2-arg def, and the four param names are single-sourced in `_GLOBALID_CALLABLE_PARAMS` (also reused in the error text). The `iscoroutinefunction` check runs first so an async 4-arg def fails with the clearer "must be sync" message.
- **`Callable` import source.** Used `collections.abc.Callable` in both `base.py` (already imports `Mapping, Sequence` from there) and `definition.py` (matching each file's prevailing style per the discretion item).
- **In-function imports in `_resolve_globalid_strategy`.** Imported `conf.settings` AND `base.{DEFAULT_GLOBALID_STRATEGY, _validate_globalid_strategy}` at function scope (not module top) — `base.py` imports `install_is_type_of` from `relay.py` at module top, so a module-top `relay -> base` import would close the load cycle. Same cycle-dodge precedent `base.py` documents for its `FilterSet` / `OrderSet` in-function imports. Kept in-function rather than param-passing since the only Slice-2 caller (`install_globalid_typename_resolver`) has the definition but not the validator in hand.
- **Setting read.** `getattr(conf.settings, "RELAY_GLOBALID_STRATEGY", None)` returns `None` for a missing key because `conf.Settings.__getattr__` converts the `KeyError` to `AttributeError`; a malformed (non-mapping) `DJANGO_STRAWBERRY_FRAMEWORK` still raises `ConfigurationError` through the read by design (the existing conf contract), not this slice's concern.

### Notes for Worker 3

- No shadow file used for implementation (the changes were small, localized additions modeled directly on `_validate_connection`).
- `effective_globalid_strategy` is **intentionally NOT added** — it is Slice-2 scope (finalization-set, spec Decision 10). The `definition.py` docstring and a narrowed inline TODO mark it as the Slice-2 deliverable. This is per Worker 1's plan step 7, not a deferral of any Slice-1 sub-check.
- `_resolve_globalid_strategy` is created in this slice but its only production caller lands in Slice 2; `test_resolve_globalid_strategy_precedence` is what exercises all four of its branches here. Per Worker 1's plan, confirm the precedence test covers Meta-wins / setting-wins / default / unknown-setting-raises.
- DRY single-sourcing landed as planned: `STRING_GLOBALID_STRATEGIES` + `DEFAULT_GLOBALID_STRATEGY` are the one source of truth Slices 2/3 reuse for the encoder default and decode-shape enforcement; `_GLOBALID_CALLABLE_PARAMS` single-sources the four-param contract for the validator + its error text.

### Notes for Worker 1 (spec reconciliation)

None. No spec gap, conflict, or unstated assumption surfaced; the plan resolved cleanly against the current source. No plan-vs-implementation drift.

---

## Review (Worker 3)

Reviewed the working-tree diff (`git diff -- django_strawberry_framework/ tests/`) against spec-031 Decisions 5/6/7, the Slice-1 checklist sub-bullets (spec lines 84-88), the Test plan Slice 1 (spec lines 566-573), and DoD items 2-3 (spec lines 668-669). Static helper run (required — slice touches three `types/` files): `review_inspect.py` on `base.py`, `definition.py`, `relay.py`, all written to `docs/shadow`. Focused tests run without `--cov*`. Diff is the four slice-intended files plus the two untracked cycle artifacts (out of review scope, as dispatched).

### High:

None.

### Medium:

None.

### Low:

None.

### Spec slice checklist walk (verbatim boxes)

All four boxes ticked `- [x]` by Worker 2; each verified against the diff:

1. **`ALLOWED_META_KEYS` grows `"globalid_strategy"` + `_validate_globalid_strategy`** — Confirmed. `"globalid_strategy"` is in the `ALLOWED_META_KEYS` frozenset (base.py:62) and NOT in `DEFERRED_META_KEYS` (unchanged). `_validate_globalid_strategy` (base.py:197-254) is structurally modeled on `_validate_connection` (base.py:143-186): same `None`-short-circuit → shape checks → `relay_shaped` gate → return-normalized contract. Accepts `model`/`type`/`type+model` via the single-sourced `STRING_GLOBALID_STRATEGIES` frozenset; unknown string → `ConfigurationError` (typo guard); non-str/non-callable → `ConfigurationError`; callable arity + sync-ness via the extracted `_validate_globalid_callable` (base.py:257-277) using `inspect.iscoroutinefunction` then `inspect.signature(value).bind(*_GLOBALID_CALLABLE_PARAMS)`; Relay-gate via the precomputed `relay_shaped` bool threaded from `_validate_meta` (base.py:863). `import inspect` and `Callable` added to imports.

2. **Stored on `DjangoTypeDefinition`** — Confirmed. `globalid_strategy: str | Callable[..., str] | None = None` added to the defaulted-field block (definition.py:117), populated via `globalid_strategy=validated.globalid_strategy` in the `DjangoTypeDefinition(...)` call (base.py:487, replacing the Slice-1 TODO), with the `_ValidatedMeta` field (base.py:774) and `_validate_meta` wiring (base.py:864-868, 900) in place — exactly mirroring the `connection`/`filterset_class`/`orderset_class` slot pattern.

3. **`_resolve_globalid_strategy(definition)` precedence** — Confirmed (relay.py:320-372). `definition.globalid_strategy` → `getattr(conf_settings, "RELAY_GLOBALID_STRATEGY", None)` → `DEFAULT_GLOBALID_STRATEGY` (`"model"`). The setting branch runs through the SAME `_validate_globalid_strategy` with `source="setting"`, so an unknown / wrong-arity / async setting raises `ConfigurationError` naming `RELAY_GLOBALID_STRATEGY`. In-function imports (`conf.settings` + `base.{DEFAULT_GLOBALID_STRATEGY, _validate_globalid_strategy}`) correctly dodge the `relay -> base` load cycle (`base.py` imports `install_is_type_of` from `relay.py` at module top), matching the documented `FilterSet`/`OrderSet` cycle-dodge precedent.

4. **Tests** — Confirmed. `tests/types/test_base.py` gains the ALLOWED/not-DEFERRED assertion, all five validator failure modes (unknown string, non-Relay type, wrong type, callable wrong-arity, `async def`), the callable-accepted-and-stored case, the string-stored-on-definition case, the absent→None case, and `test_resolve_globalid_strategy_precedence` exercising all four resolver branches (Meta-wins, setting-wins, default, unknown-setting-raises naming the setting). 10/10 pass.

No box was ticked without matching implementation; no sub-check is silently un-addressed.

### Correctness verification performed

- **Arity check semantics.** Verified `inspect.signature(fn).bind("type_cls","model","root","info")` BINDS a 4-arg def and raises `TypeError` ("too many positional arguments") for a 2-arg def — the exact spec reject case. Tolerant forms (`*args`, `**kwargs`, trailing-default param) bind, which the plan's discretion item explicitly licenses ("tolerating `*args`/defaults"). An `async def` 4-arg def is caught first by `iscoroutinefunction` (the clearer "must be sync" message), so it never reaches the arity check.
- **Defensive setting read.** Verified `conf.Settings.__getattr__` (conf.py:133-156) converts `KeyError` → `AttributeError`, so `getattr(conf_settings, "RELAY_GLOBALID_STRATEGY", None)` yields `None` for a missing key → falls through to the `"model"` default ("absent → package default", spec line 87). A malformed (non-mapping) top-level `DJANGO_STRAWBERRY_FRAMEWORK` still raises `ConfigurationError` through the read by design — the existing conf contract, not this slice's concern.
- **Precedence-test setting re-read.** `test_resolve_globalid_strategy_precedence` flips `settings.DJANGO_STRAWBERRY_FRAMEWORK` mid-test via the pytest-django `settings` fixture; the `setting_changed` signal resets the lazy `Settings._user_settings` cache so each tier re-reads fresh. Same pattern the existing `test_inputs.py` precedence tests use; the test passing confirms it.
- **`DjangoTypeDefinition` annotation in relay.py.** The `definition: DjangoTypeDefinition` parameter annotation resolves under `from __future__ import annotations` + the `TYPE_CHECKING` import (relay.py:23, 37-38) — no runtime import, consistent with the existing `apply_interfaces` signature.

### DRY findings

None — the slice is exemplary on DRY:

- The valid-string set is single-sourced as `STRING_GLOBALID_STRATEGIES` (base.py) and the default as `DEFAULT_GLOBALID_STRATEGY`; both are referenced (not re-typed) by the validator, the error text, and the resolver, and are positioned for Slice 2/3 reuse per the build-plan DRY watch point.
- The four-param callable contract is single-sourced as `_GLOBALID_CALLABLE_PARAMS`, reused by both the `.bind(...)` arity check and the error text.
- The arity/sync validation lives in ONE helper (`_validate_globalid_callable`) serving both the `Meta` and setting paths — no parallel validators.
- The `_validate_globalid_strategy` rule is genuinely ONE validator with a `source` discriminator, satisfying Decisions 6/7's "one validator, two sources, source-specific error text" rule. The `relay_shaped` predicate is reused (not recomputed) via the bool `_validate_meta` already threads.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is empty — no change to `__all__` or the re-export list. Consistent with spec Decision 11 ("no public export in 0.0.9"; the public testing helpers ship with sibling card 032). Confirmed.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. (The `definition.py` / `base.py` / `relay.py` docstring + comment edits are source-internal, not standing-doc surfaces; the dangling Slice-2/3 TODO comments left in `definition.py` and `relay.py` correctly scope the remaining work and are appropriate per AGENTS.md's staged-slice TODO convention.)

### What looks solid

- The validator is a faithful structural clone of `_validate_connection` — same control-flow skeleton, same gate-after-shape ordering, same remediation-message style — so it reads as a native member of the file rather than a bolt-on.
- The `effective_globalid_strategy` field is correctly NOT added — it is finalization-set Slice-2 scope (spec Decision 10), and the `definition.py` docstring + a narrowed inline TODO mark it as the Slice-2 deliverable. Its absence is correct, not a gap.
- The Relay-gate is correctly skipped on the setting path (the per-type gate already ran at type creation), so an unknown setting string surfaces its typo error rather than a misleading relay-shape error — verified by `test_resolve_globalid_strategy_precedence`'s unknown-setting branch asserting the `RELAY_GLOBALID_STRATEGY` framing.
- `iscoroutinefunction` runs before the arity check, so an `async def` 4-arg encoder gets the clear "must be sync" message instead of a confusing arity error.
- TODO/pseudocode hygiene: every satisfied Slice-1 TODO (base.py comment block, the `__init_subclass__` call, the `definition.py` field block, the `test_base.py` stub, the `relay.py` resolver pseudocode) was removed or narrowed to the genuinely-remaining Slice-2/3 work.

### Temp test verification

No temp tests created. Every Slice-1 contract is package-internal and directly asserted by the 10 permanent tests added to `tests/types/test_base.py`; the resolver's four branches (otherwise only reachable from Slice 2's call site) are all exercised by `test_resolve_globalid_strategy_precedence`. No suspicion required a scratch probe; the `inspect.bind` and `conf.getattr` behaviors were verified with throwaway one-shot `python -c` checks (not files), recorded under "Correctness verification performed".

### Notes for Worker 1 (spec reconciliation)

None. The slice ships exactly the Decisions 5/6/7 contract; no spec ambiguity surfaced. The intentional Slice-2 deferral of `effective_globalid_strategy` is already recorded by Worker 2 and is on-plan (Worker 1 plan step 7), so no deferral note is needed at final verification beyond confirming the field's absence is in-scope.

### Review outcome

`review-accepted` — every spec-required Slice-1 behavior is reflected in the diff, all four verbatim checklist boxes verified landed, the 10 tests pin every named branch, DRY is exemplary, and the public surface is unchanged. No High/Medium/Low findings.

---

## Final verification (Worker 1)

Verified the full slice artifact, the Worker 2 build report and Worker 3 review, and the working-tree diff (`git diff -- django_strawberry_framework/ tests/`: `types/base.py`, `types/definition.py`, `types/relay.py`, `tests/types/test_base.py`). The diff is exactly the four planned slice files plus the two untracked cycle artifacts (this artifact + the build plan); `django_strawberry_framework/__init__.py` is unchanged (no public-surface drift, consistent with spec Decision 11's "no public export in 0.0.9"). The expected spec-030 archive deletions are the maintainer's concurrent "archive 030" commit, out of scope.

**Spec status-line re-verification (per-spawn).** Read spec lines 1-9 (title / planned-version / status / owner / predecessors). The status line (`Status: planned — not started`) and the unticked `## Slice checklist` are an intentional contract record, not a build tracker — spec line 5 states "The Slice checklist below stays unticked as the contract record (build progress is tracked in the build plan, not here)." So neither the spec header nor the spec checklist requires a Worker 1 edit at this slice; build progress lives in `build-031-...md`. No predecessor reference broke.

**Spec slice checklist audit (boxes verified against the diff).** All four `- [x]` boxes Worker 2 ticked truly landed; none over-ticked, none silently un-ticked:

1. `ALLOWED_META_KEYS` grows `"globalid_strategy"` (confirmed in the frozenset; `DEFERRED_META_KEYS` unchanged — not a promotion); `_validate_globalid_strategy` is structurally modeled on `_validate_connection`, accepts `model`/`type`/`type+model` via the single-sourced `STRING_GLOBALID_STRATEGIES` frozenset or a callable, raises `ConfigurationError` on unknown string / wrong type, validates callable arity (`inspect.signature(...).bind(*_GLOBALID_CALLABLE_PARAMS)`) + sync-ness (`inspect.iscoroutinefunction`), and gates on the precomputed `relay_shaped` bool from `_validate_meta`. `import inspect` + `Callable` imports added. **Landed.**
2. Normalized value stored on `DjangoTypeDefinition` via the new raw `globalid_strategy` slot (`definition.py`), populated by `globalid_strategy=validated.globalid_strategy` in `__init_subclass__`'s `DjangoTypeDefinition(...)` call, threaded through the `_ValidatedMeta` NamedTuple + `_validate_meta` — mirroring the `connection`/`filterset_class`/`orderset_class` pattern. `effective_globalid_strategy` correctly NOT added (finalization-set Slice-2 scope per spec Decision 10; narrowed TODO marks it). **Landed.**
3. `_resolve_globalid_strategy(definition)` (`relay.py`) applies `definition.globalid_strategy` → `getattr(conf_settings, "RELAY_GLOBALID_STRATEGY", None)` → `DEFAULT_GLOBALID_STRATEGY` (`"model"`); the setting branch runs through the SAME `_validate_globalid_strategy` with `source="setting"` (unknown / wrong-arity / async → `ConfigurationError` naming `RELAY_GLOBALID_STRATEGY`); in-function imports dodge the `relay → base` load cycle. **Landed.**
4. `tests/types/test_base.py` gains the ALLOWED/not-DEFERRED assertion, all five validator failure modes (unknown string, non-Relay type, wrong type, callable wrong-arity, `async def`), the callable-accepted-and-stored case, the string-stored-on-definition case, the absent→`None` case, and `test_resolve_globalid_strategy_precedence` exercising all four resolver branches (Meta-wins, setting-wins, default, unknown-setting-raises naming the setting). 10 net-new tests; pin every named branch. **Landed.**

No box was ticked without matching implementation; no landed box was left un-ticked; no remaining `- [ ]` to defer.

**DRY check.** Slice 1 is the first slice (no prior accepted slices to cross-check). Within the slice the shared-validator / single-source-constants shape is clean and introduces no duplication: one `_validate_globalid_strategy` serves both sources via the `source` discriminator; the arity/sync logic is single-sited in `_validate_globalid_callable`; the four-param contract is single-sourced in `_GLOBALID_CALLABLE_PARAMS`; the strategy vocabulary is single-sourced in `STRING_GLOBALID_STRATEGIES` + `DEFAULT_GLOBALID_STRATEGY`, both positioned for Slice 2 (encoder) / Slice 3 (decoder) reuse per the build-plan DRY watch point. No new duplication.

**Existing tests still pass.** `uv run pytest tests/types/test_base.py --no-cov` → **89 passed** (includes the 10 net-new Slice-1 tests; no regression from the `_ValidatedMeta` field addition). No `--cov*` flags used.

**Spec reconciliation.** None needed. Slice 1 is the foundation and landed exactly as specified; no spec gap, conflict, or inaccuracy surfaced (Worker 2 and Worker 3 both recorded "None" for spec reconciliation, confirmed against the diff). No spec edit made.

### Summary

Slice 1 ships the GlobalID-encoding foundation: the net-new `Meta.globalid_strategy` key (validated by `_validate_globalid_strategy`, modeled on `_validate_connection`, with callable arity/sync-ness checks and a Relay-Node-shape gate), its raw storage on `DjangoTypeDefinition.globalid_strategy`, and the `_resolve_globalid_strategy(definition)` three-tier precedence resolver (`Meta` → `RELAY_GLOBALID_STRATEGY` setting → `"model"` default) that validates the setting through the same shared rule. The strategy vocabulary and four-param callable contract are single-sourced as module constants for Slice 2/3 reuse. No encode/decode logic and no `effective_globalid_strategy` field (both Slice 2). Public surface unchanged.

### Spec changes made (Worker 1 only)

None. The spec was not edited — Slice 1 landed exactly as specified, and the spec's `Status:` line + unticked `## Slice checklist` are an intentional contract record (spec line 5), not a build tracker, so no per-spawn header reconciliation was required.
