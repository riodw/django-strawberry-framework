# Review: `django_strawberry_framework/types/definition.py`

Status: verified

## DRY analysis

- None — the module is already the single source for every derivation it owns. `graphql_type_name` (`types/definition.py::DjangoTypeDefinition.graphql_type_name`) is the explicit consolidation of three former inline copies (finalizer, `filters/base.py`, `filters/inputs.py`) and is now the sole `self.name`-or-`self.origin.__name__` source — grep confirms `registry.py:359/378`, `relay.py:167-168`, `filters/base.py:257`, `filters/inputs.py:589`, `types/relay.py:456/474/482` all read it rather than re-spell the rule. `origin_has_custom_id_resolver` (`types/definition.py::origin_has_custom_id_resolver`) is itself the dedupe primitive: the memoized `has_custom_id_resolver_for` hot path and the optimizer's definition-less fallback (`optimizer/walker.py #"origin_has_custom_id_resolver"`, walker.py:902) both call it, so the registered and unregistered FK-id-elision guards cannot drift. The four-helper id-resolver chain (`origin_has_custom_id_resolver` -> `_class_has_custom_id_resolver` / `_resolves_id_off_pk` -> `_is_framework_relay_id_resolver`) is heterogeneous-body decomposition (MRO scan vs NodeID-off-pk check vs framework-default identity), not near-copies; no new helper or shared dataclass is warranted at this granularity.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** `graphql_type_name` is the canonical single-source `self.name or self.origin.__name__` derivation reused by `registry.py`, `relay.py`, `filters/base.py`, `filters/inputs.py`, `types/relay.py` (`types/definition.py:199-209`; its docstring names the three former inline copies). `origin_has_custom_id_resolver` is shared verbatim by `has_custom_id_resolver_for` (`types/definition.py:294`) and the optimizer fallback (`optimizer/walker.py:902`) so the two FK-id-elision guards stay in lockstep (`types/definition.py:299-313`). Field-name normalization for `relation_connections` lookups reuses the SAME `snake_case(sel.name)` the `field_map` lookup uses (docstring `:99-100`), keeping walker resolution single-channel.
- **New helpers considered.** Folding the four id-resolver helpers into one — rejected; bodies are distinct detection strategies (MRO class-attr scan, NodeID-off-pk check, framework-default identity). Hoisting `"resolve_id"` / `"__func__"` to module constants — rejected at N=2 (not dispatch keys). A wrapper around `related_target_for`'s `get → get_definition` two-step — rejected; sole caller, and the registry already encapsulates the `primary_for`-first / single-type-fallback rule.
- **Duplication risk in the current file.** The two repeated literals the static overview flags — `"resolve_id"` (×2) and `"__func__"` (×2) — are intentional sibling reads: `"resolve_id"` distinguishes the framework-default-aware branch in `_class_has_custom_id_resolver` (`:345`) from the resolver-name tuple in `origin_has_custom_id_resolver` (`:306`); `"__func__"` unwraps two distinct descriptors (`value` vs `relay.Node.resolve_id`) in `_is_framework_relay_id_resolver` (`:357-359`). The two caches (`_related_target_cache`, `_custom_id_resolver_cache`) share a `dict default_factory, repr=False, membership-not-get` shape but key different value spaces (`(target_definition, model_field) | None` tuples vs `bool`) and gate on different stability signals (`registry.is_finalized()` vs always-stable MRO/annotation inputs) — correctly NOT a shared abstraction.

### Other positives

- **`related_target_for` caching is correctly fail-safe.** The cache is consulted/populated only when `registry.is_finalized()` (`types/definition.py:247,274`); pre-finalize the registry can still gain types, so a transient `None` is never locked in. The cache stores the full `(target_definition, model_field) | None` tuple, making `None` a valid cached negative without an in-band sentinel — matched by `has_custom_id_resolver_for`'s membership-check pattern (`:291`, `False` cacheable). All four registry methods it relies on exist: `is_finalized` (`registry.py:427`), `get` (`:221`), `get_definition` (`:346`), `primary_for` (`:268`).
- **In-function imports are genuine, documented cycle-dodges.** `related_target_for` imports `registry` inside the body because `registry.py` imports `DjangoTypeDefinition` only under `TYPE_CHECKING` (`registry.py:29-30`); hoisting would close a `definition → registry → definition` load cycle. `_resolves_id_off_pk`/`_is_framework_relay_id_resolver` defer the `strawberry.relay` and `.relay` imports for the same reason. The inline comment (`:230-232`) accurately names the cycle.
- **FK-id-elision guard is fail-closed and precise.** `_class_has_custom_id_resolver` ignores the framework-installed Relay default (`_resolve_id_default` at `types/relay.py:273`, plus `relay.Node.resolve_id`) so only true consumer overrides count; `_resolves_id_off_pk` returns `False` for non-Relay targets and for Relay targets whose `NodeID` resolves to `"pk"`/`pk_name`, flagging only the genuinely-unsafe off-pk `NodeID` case. The `isinstance(origin, type) and issubclass(...)` guard (`:330`) short-circuits before `issubclass` can throw on a non-class; `FieldDoesNotExist`/`NodeIDAnnotationError` are caught and mapped to `None`/safe.
- **Docstring/source fidelity is high.** The invariants docstring's cross-module claims all verify at source: `effective_globalid_strategy` set once at `types/relay.py:586/594` and read by `decode_global_id` (`relay.py:718`) / filters / testing; `relation_connections` written by `finalizer.py::_synthesize_relation_connections` (`:347-349`) and read by `walker.py:331`; `globalid_strategy` precedence resolved through `_resolve_globalid_strategy` (`types/relay.py:341`). The `fields_class` slot (`:161`, docstring `:64-68`) stays `None` until `TODO-BETA-046-0.1.1`: it IS in `DEFERRED_META_KEYS` (`types/base.py:64`), `Meta.fields_class` is rejected at validation (`base.py:1070`), and grep finds no populator — an inert structural mirror of the shipped `filterset_class`/`orderset_class` slots, not a premature surface. No stale or over-promising prose; static overview reports 0 TODO comments.
- **GLOSSARY accuracy, no drift.** `DjangoTypeDefinition`, `related_target_for`, `effective_globalid_strategy`, `graphql_type_name`, `relation_connections`, and `origin_has_custom_id_resolver` carry no GLOSSARY entry — all private internal symbols absent from `types/__init__.py __all__` (`= ("DjangoType", "SyncMisuseError", "finalize_django_types")`), so the absence is correct. The contract-level `Meta.globalid_strategy` entry (GLOSSARY:734-755) abstracts over the slot and its precedence (`Meta.globalid_strategy → RELAY_GLOBALID_STRATEGY → "model"`) matches `_resolve_globalid_strategy`'s spec-031 Decision 5 docstring byte-for-byte; the relation-connections prose (GLOSSARY:260) accurately describes reading the slot via definition metadata; `Meta.fields_class` is "planned for `0.1.1`" (GLOSSARY:95/686-692), consistent with the inert slot.

### Summary

`types/definition.py` is the canonical, immutable metadata record for collected `DjangoType` classes — a pure dataclass plus its id-resolver predicate family, with no schema build, no ORM query construction, and no request-scope state. Both `git diff f5a3a9a1 -- types/definition.py` and `git diff HEAD -- types/definition.py` are empty and `git log baseline..HEAD` shows no commit touching the file, so this is a genuine no-source-edit cycle. The relation-target lookup, the two per-instance caches (both finalize-gated / negative-cacheable), the FK-id-elision guard, and the strategy-resolution slots all verify correct at source; every cross-module docstring claim holds; the file's only symbols are private and correctly carry no GLOSSARY entry. No High/Medium/Low findings; DRY is already at its single-source shape.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — `289 files left unchanged` (no changes; pre-existing COM812-vs-formatter advisory warning only).
- `uv run ruff check --fix .` — `All checks passed!`

### Notes for Worker 3
- Shape #5 (no-source-edit). Both `git diff f5a3a9a1a68e7074308a0814ea829acbe42ce515 -- django_strawberry_framework/types/definition.py` and `git diff HEAD -- django_strawberry_framework/types/definition.py` are empty; `git log baseline..HEAD -- <target>` returns nothing. No High / no Medium / no Low; all severities `None.`
- No GLOSSARY-only fix in scope. `DjangoTypeDefinition` and all its methods/functions are private (absent from `types/__init__.py __all__`); GLOSSARY documents only the `Meta.globalid_strategy` contract key (precedence verified against `types/relay.py::_resolve_globalid_strategy`), the relation-connections behavior (GLOSSARY:260), and the `Meta.fields_class` "planned for 0.1.1" note (GLOSSARY:95/686-692) — all accurate.
- Cross-module single-source claims re-verified at source: `origin_has_custom_id_resolver` shared by definition + `walker.py:902`; `graphql_type_name` reused by registry/relay/filters; in-function `registry` import is a real `TYPE_CHECKING`-backed cycle-dodge (`registry.py:29-30`); `fields_class` slot inert (no populator, rejected in `DEFERRED_META_KEYS`).

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment or docstring changes. The invariants docstring (`:17-137`) and the inline cycle-dodge / cache / `fields_class`-reservation comments were checked against source and are accurate; no stale, restating, or over-promising prose found (static overview: 0 TODO comments).

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted. No source, test, GLOSSARY, or behavior change this cycle; per `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan `docs/review/review-0_0_11.md`'s silence on `types/definition.py` changelog entries, no entry is added.

---

## Verification (Worker 3)

### Logic verification outcome
No High / Medium / Low findings to address; all severities `None.`, so the verification is the independent confirmation that the `None.` findings are genuine (shape #5).

- **Zero-edit proof (all axes).** `git diff f5a3a9a1a68e7074308a0814ea829acbe42ce515 -- django_strawberry_framework/types/definition.py` empty; `git diff HEAD -- django_strawberry_framework/types/definition.py` empty; target absent from the owned-paths stat (`django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` — grep for "definition" returns nothing); `git log f5a3a9a1..HEAD -- <target>` empty. The dirty working tree is entirely `docs/` (review artifacts, `docs/dry/`, `docs/feedback2.md`, `docs/spec-038*`) — no source/test/GLOSSARY/CHANGELOG path, so no sibling-cycle attribution is needed. The cycle's "Files touched: None" claim holds.
- **`related_target_for` relation lookup.** Verified at source: the call site is `target_type = registry.get(target_model)` (definition.py:263), NOT the historical `primary_for(...) or get(...)` chain; the primary-first contract is delegated to `registry.get` and pinned end-to-end by `test_related_target_for_resolves_to_primary_when_two_types_share_target_model` (asserts the primary `AdminShelfType` wins). All four registry methods exist (`is_finalized` registry.py:427-region, `get`, `get_definition`, `primary_for`). Non-relation → `None` (`test_related_target_for_resolves_fk_m2m_and_reverse` scalar arm), missing field → `None` (`FieldDoesNotExist` caught, same test), GFK (`related_model is None`) → `None` (`test_related_target_for_returns_none_for_generic_foreign_key`). Cache gated on `registry.is_finalized()` so a transient pre-finalize `None` is never locked in.
- **`effective_globalid_strategy` precedence (Meta → setting → default).** Confirmed at `types/relay.py::_resolve_globalid_strategy` (:378-389): returns `definition.globalid_strategy` when non-`None`, else the validated `RELAY_GLOBALID_STRATEGY` setting when present, else `DEFAULT_GLOBALID_STRATEGY = "model"` (base.py:123). Matches the invariants-docstring claim byte-for-byte. The `effective_globalid_strategy` slot is the distinct finalization-time classification string (default `None`), set once Phase-2.5; not the raw slot.
- **`origin_has_custom_id_resolver` single-source.** 1 def (definition.py:299), 2 consumers: `has_custom_id_resolver_for` (memoized hot path) and `optimizer/walker.py:902` (definition-less fallback). The two FK-id-elision guards cannot drift. Detection family (`_class_has_custom_id_resolver` / `_resolves_id_off_pk` / `_is_framework_relay_id_resolver`) is heterogeneous-body, correctly not folded — and the framework Relay default is exempted (pinned by `test_has_custom_id_resolver_for_ignores_framework_relay_default` + `_ignores_inherited_relay_default`); off-pk `NodeID` flagged (`_flags_non_pk_node_id`), pk `NodeID` allowed (`_allows_pk_node_id`); memoization with membership-not-`.get` pinned by the `_custom_id_resolver_cache == {...}` asserts.
- **Dataclass field contracts.** Field order/types in the dataclass body match the construction-site usage exercised by the direct-construction tests (`DjangoTypeDefinition(origin=..., model=..., name=None, ...)`); the two caches use `field(default_factory=dict, repr=False)` keying different value spaces (tuple|None vs bool) — correctly not a shared abstraction.
- **Inert `fields_class` slot.** `None` default (definition.py:161); in `DEFERRED_META_KEYS` (base.py:64); `Meta.fields_class` rejected at validation (base.py:1070-1074, "Meta keys not supported yet"); no populator. Inert structural mirror of the shipped `filterset_class`/`orderset_class` slots.
- **GLOSSARY (genuine #5).** All definition.py symbols are private — `types/__init__.py __all__ = ("DjangoType", "SyncMisuseError", "finalize_django_types")` — so the absence of any `DjangoTypeDefinition` / `related_target_for` / `origin_has_custom_id_resolver` / `effective_globalid_strategy` / `graphql_type_name` / `relation_connections` GLOSSARY entry is correct, not drift. No GLOSSARY-only fix in scope (would be disqualifying); none present.
- **Shape-#5 gate.** Each Worker 2 section opens "Filled by Worker 1 per no-source-edit cycle pattern."; changelog Not-warranted cites BOTH `AGENTS.md` and active-plan silence; `git diff -- CHANGELOG.md` empty (matches disposition). Ruff format-check (`1 file already formatted`, COM812-vs-formatter advisory only) + `ruff check` (`All checks passed!`) on the target.

### DRY findings disposition
DRY-None is genuine: `graphql_type_name` is the single-source `self.name or self.origin.__name__` derivation; `origin_has_custom_id_resolver` is the dedupe primitive shared with the walker fallback; the four-helper id-resolver chain is heterogeneous-body decomposition, not near-copies. No DRY items to carry forward.

### Temp test verification
- No temp tests created — empty-diff #5; the existing `tests/types/test_definition_relations.py` suite already pins the relation-lookup and id-resolver predicates positive AND negative.
- Disposition: none.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `types/definition.py` checklist box in `docs/review/review-0_0_11.md`.
