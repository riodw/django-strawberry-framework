# Review: `django_strawberry_framework/types/definition.py`

Status: verified

## DRY analysis

- **Defer-with-trigger — extract `_target_for_field(model, field_name) -> tuple[DjangoTypeDefinition, models.Field] | None` from the `related_target_for` resolution funnel (`definition.py:245-266`).** The five-stage funnel (`get_field` / `FieldDoesNotExist` → `is_relation` guard → `related_model` guard → `registry.get` → `get_definition` → tuple pack) is a pure `(model, field_name)` → `(target_definition, model_field)` mapping; the only `self` coupling is reading `self.model`. The memoization wrapper (`cache_ok` gate + cache read/write) is orthogonal and stays on the method. Defer until a second consumer needs the same funnel without the per-definition cache — likely candidates are the orders Slice-3 wiring or an optimizer relation-traversal site (`filters/sets.py:624` already reaches `related_target_for` reflectively, so it reuses the method, not the funnel). Single live call-funnel today; a helper now would only add an indirection.

- **None beyond the above** — the previously-flagged `registry.primary_for(target_model) or registry.get(target_model)` two-step chain (carried by the stale 0.0.7 artifact) is GONE from live source: `related_target_for` now calls `registry.get(target_model)` directly (`definition.py:257`), and `registry.get` already encodes the "primary first, else single-type, else None" rule as its first return state (`registry.py:234-240`). The redundant chain no longer exists, so that DRY opportunity is closed by prior work, not re-raised.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** `related_target_for` delegates target resolution wholly to `registry.get(target_model)` (`definition.py:257`), which single-sources the "primary-first / single-type-fallback / ambiguous-None" rule (`registry.py:221-240`) — the dataclass does not re-spell that precedence. `origin_has_custom_id_resolver` (module-level, `definition.py:293-307`) is the shared spelling consumed both by the memoized hot path `has_custom_id_resolver_for` (`definition.py:288`) and by the optimizer's definition-less fallback, so the two-shape "custom id resolver" detector cannot drift between the two call sites — the docstring at `definition.py:294-299` states this contract explicitly. `graphql_type_name` (`definition.py:192-203`) centralizes the `self.name or self.origin.__name__` derivation that the docstring notes was previously inlined in three call sites (`finalizer.py`, `filters/base.py`, `filters/inputs.py`).
- **New helpers considered.** The `_target_for_field` funnel extraction (see DRY analysis) — rejected for now, single live funnel, deferred with an explicit trigger.
- **Duplication risk in the current file.** Repeated literals are `2x "resolve_id"` and `2x "__func__"` (per shadow overview). `"resolve_id"` appears once as the resolver-name special-case key in `_class_has_custom_id_resolver` (`definition.py:339`) and once inside the `(pk_name, f"resolve_{pk_name}")` candidate tuple region in `origin_has_custom_id_resolver` (`definition.py:300`) — two distinct roles (default-resolver discriminator vs. override-name candidate), not a consolidatable literal. `"__func__"` is the `getattr(..., "__func__", ...)` MRO-unwrap idiom applied to two different objects (the descriptor under test and `relay.Node.resolve_id`) in `_is_framework_relay_id_resolver` (`definition.py:351-352`); inlining a local would not reduce surface. Both are intentional.

### Other positives

- **`relation_connections` read/write contract is sound end-to-end (spec-033 Decision 3 — a 0.0.9 focus slot).** Writer: `finalizer.py::_record_relation_connection` (`finalizer.py:347-349`) lazily initializes the slot to `{}` and assigns `generated -> name`; it is called only from the Phase-2.5 synthesis (`_synthesize_relation_connections`, `finalizer.py:352`), and suppressed shapes (`"list"` narrowing, non-Node target, consumer-authored) record nothing — so the slot's keys are exactly the connections that genuinely exist, matching the docstring at `definition.py:81-95`. The assignment is idempotent (plain dict set), so the documented re-entrancy `continue` path (a partial finalize re-running Phase 2.5) leaves the same mapping. Reader: `walker.py::_walk_selections` (`walker.py:284`) reads it via `getattr(definition, "relation_connections", None) or {}` and gates the synthesized-connection branch on `snake_case(sel.name) in relation_connections` (`walker.py:286,297`) — the SAME `snake_case` normalization the field-map lookup uses, exactly as the docstring promises (`definition.py:94-95`). Second reader `inspect_django_type.py:262` (`definition.relation_connections or {}`) consumes it as the documented channel for recognizing synthesized connections in the introspection command — the two readers agree on the `None`-as-empty coercion. The slot is the metadata channel the docstring describes ("the same channel it uses for `field_map` / `optimizer_hints`"), keeping the walker out of `connection.py` internals.
- **`related_target_for` cache discipline is correct (`definition.py:241-269`).** The `cache_ok = registry.is_finalized()` gate means a transient `None` computed pre-finalize is never cached (the registry can still grow more `DjangoType` registrations), so a wrong answer cannot be locked in; only post-finalize results memoize. A cached `None` IS a valid entry (membership-checked via `field_name in self._related_target_cache`, `definition.py:242`), so the negative-result cache works without an in-band sentinel — matching the field-comment at `definition.py:175-184`. `related_model is None` and non-relation fields both funnel to `result = None` cleanly, and `FieldDoesNotExist` is caught locally (no leak).
- **`has_custom_id_resolver_for` memoization handles `False` correctly (`definition.py:285-290`).** Membership check (`pk_name in self._custom_id_resolver_cache`) rather than `dict.get`, so a cached `False` is a hit, not a recompute — the field-comment at `definition.py:186-189` calls this out and the code matches.
- **Write-once invariants verified against live source.** `finalized` is assigned exactly once at `finalizer.py:688` (matches the docstring's "flips exactly once" claim, `definition.py:33-36`); `selected_fields` is set only at the construction sites in `types/base.py` (570/579/625/1292/1364), never mutated post-construction (matches `definition.py:30-32`); `effective_globalid_strategy` is set only in `relay.py:597` (custom-callable branch) and `relay.py:605` (classification branch) — mutually exclusive per call, so "set exactly once by the Phase-2.5 install" holds (`definition.py:104-116`).
- **In-function imports are justified and load-bearing.** `related_target_for` imports `FieldDoesNotExist` and `registry` inside the method body (`definition.py:227-229`) with a comment naming the `definition -> registry -> definition` module-load cycle; `_resolves_id_off_pk` and `_is_framework_relay_id_resolver` defer `strawberry.relay` / `.relay` imports likewise. These are not lazy-for-laziness — hoisting would reintroduce the cycle (registry imports `DjangoTypeDefinition` lazily under `TYPE_CHECKING`).
- **`selected_fields` is the package's own attribute, distinct from Strawberry's `info.selected_fields`.** Confirmed: package readers (`finalizer.py:413/468/627`, `resolvers.py:306`, `inspect_django_type.py:167`) all read `definition.selected_fields` (Django field instances in `_meta.get_fields()` order); the `info.selected_fields` reads (`connection.py:390`, `optimizer/selections.py`) are Strawberry's GraphQL selection set — a different object entirely. No conflation in this file or its consumers.
- **Reflective access is bounded and safe.** Every `getattr` carries a default (`is_relation`/`related_model`/`__mro__`/`__dict__`/`__func__` — `definition.py:250,253,303,336,351,352`), so a malformed origin/field degrades to the safe branch rather than raising. `isinstance(origin, type) and issubclass(origin, relay.Node)` (`definition.py:324`) guards the `issubclass` against a non-class `origin`.
- **`related_target_for` control-flow hotspot (66 lines / 9 branches per shadow overview) is the memoization wrapper plus the resolution funnel, not accidental complexity.** Each branch is a distinct early-return reason (field-missing, non-relation, no related model, no registered type, no definition) plus the two cache gates; the nesting reads top-down and is fully exercised by the consuming filter/optimizer paths.

### Summary

`DjangoTypeDefinition` is the canonical, write-once-after-construction metadata record for collected `DjangoType` classes, and the file is in excellent shape. The 0.0.9 focus areas all check out against live source: the `relation_connections` slot has a clean single-writer (Phase-2.5 synthesis, suppressed shapes record nothing) / dual-reader (walker + inspect command, both `None`-coercing, both `snake_case`-normalized) contract that keeps the walker out of `connection.py` internals; `selected_fields` is the package's own ordered-Django-field tuple, correctly distinct from Strawberry's `info.selected_fields`; and `related_target_for` resolves relation targets through `registry.get` (which single-sources the primary-honoring precedence) with finalize-gated negative-result memoization. The stale 0.0.7 on-disk artifact's primary DRY finding (the `primary_for(...) or get(...)` chain) is moot — live source already calls `registry.get` directly. No High, Medium, or Low findings; one defer-with-trigger DRY opportunity recorded. Ruff format and check both clean with zero changes. No-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format django_strawberry_framework/types/definition.py` — `1 file left unchanged`.
- `uv run ruff check django_strawberry_framework/types/definition.py` — `All checks passed!`.

### Notes for Worker 3
- No High / no Medium / no Low findings; nothing to disposition.
- One DRY item is a defer-with-trigger (`_target_for_field` funnel extraction) — explicitly deferred, not actionable now.
- No GLOSSARY-only fix in scope: GLOSSARY:234 accurately describes the `relation_connections` walker-read contract (matches walker.py:284-301 and the slot docstring); no drift on any documented public-contract symbol from this file.
- Stale 0.0.7 on-disk artifact (`Status: verified`, refs `:NN` line numbers, primary DRY bullet on the now-removed `primary_for(...) or get(...)` chain) superseded wholesale.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. Docstrings and field-comments were audited as part of the logic pass and are accurate against live source — every invariant claim (write-once `finalized`/`selected_fields`/`effective_globalid_strategy`, the `relation_connections` read/write contract, cache-validity gating, `registry.get` primary precedence) was verified against the cited consumer sites. No comment edits warranted.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — no source, test, GLOSSARY, or behavior change in this cycle (AGENTS.md: "Do not update CHANGELOG.md unless explicitly instructed"; the active plan `docs/review/review-0_0_9.md` is silent on any CHANGELOG entry for this item).

---

## Verification (Worker 3)

### Logic verification outcome
No High / Medium / Low findings to disposition. Independently re-verified the four dispatch claims against live source (definition.py byte-unchanged from baseline `0872a20`):

- **Single-writer `relation_connections`.** `finalizer.py::_record_relation_connection` (`finalizer.py #"if definition.relation_connections is None"`, :347-349) lazily inits the slot to `{}` and sets `relation_connections[generated] = name`; called only from `_synthesize_relation_connections` (:464, :516), itself invoked once at the Phase-2.5 site (:668). Suppressed shapes (`"list"` narrowing / non-Node / consumer-authored) take callers that never reach `_record_relation_connection`, so keys are exactly the connections that exist. Plain dict-set → idempotent under the documented re-entrancy `continue`.
- **Dual-reader, both None-coercing + snake_case-normalized.** Reader 1 `walker.py::_walk_selections` (:284) `getattr(definition, "relation_connections", None) or {}`, gates the synthesized branch on `snake_case(sel.name) in relation_connections` (:286/:297) — same snake_case the field-map lookup uses. Reader 2 `inspect_django_type.py::_suppressed_connection_name` (:262) `definition.relation_connections or {}`, inverted `gen for gen, rel ... if rel == field.name`. Both coerce None→empty identically.
- **`selected_fields` is the package's own ordered-Django-field tuple, not Strawberry's `info.selected_fields`.** Typed `tuple[models.Field, ...]` (definition.py:140), set only at the 5 base.py construction sites (570/579/625/1292/1364). Distinct object from Strawberry's GraphQL selection set (which only `connection.py` reads via the converting property) — no conflation in this file or its consumers.
- **`related_target_for` via `registry.get` with finalize-gated negative memoization.** `cache_ok = registry.is_finalized()` (:241); cache read membership-gated (`field_name in self._related_target_cache`, :242 — cached `None` is a hit); resolution funnel calls `registry.get(target_model)` directly (:257), not the removed `primary_for(...) or get(...)` chain; write gated on `cache_ok` (:268-269) so a transient pre-finalize `None` is never locked in. Stale 0.0.7 DRY finding confirmed moot.
- **Write-once invariants.** `finalized` assigned only at `finalizer.py:688`; `effective_globalid_strategy` only at `relay.py:597`/`:605` (mutually exclusive per call); `selected_fields` only at the 5 base.py sites — none mutated post-construction.

### DRY findings disposition
Lone DRY item (`_target_for_field` funnel extraction) is a defer-with-trigger (single live call funnel today; second cacheless consumer is the trigger). Correctly recorded, not actionable now. The previously-flagged `primary_for(...) or get(...)` chain is closed by prior work (live source calls `registry.get` directly).

### Temp test verification
None — no-source-edit cycle; verification was read-only source inspection.

### Shape #5 (no-source-edit) checks
1. `git diff --stat 0872a20 -- django_strawberry_framework/types/definition.py` empty; absent from the wider owned-scope stat → byte-unchanged. "Files touched: None" holds.
2. Each Worker 2 section opens `Filled by Worker 1 per no-source-edit cycle pattern.`
3. No GLOSSARY-only fix in scope (Worker 2 Note confirms GLOSSARY:234 accurate); zero Lows to forward.
4. Changelog `Not warranted` cites BOTH AGENTS.md and plan silence; `git diff -- CHANGELOG.md` empty; internal-only framing honest (no source/behavior change).
5. Ruff format-check + check pass (COM812 standing warning only).

**Sibling-cycle attribution.** Dirty hunks in the wider stat (conf, connection, exceptions, filters/factories, filters/sets, list_field, management/commands/inspect_django_type + test, optimizer/extension, optimizer/selections + test, optimizer/walker, orders/factories, orders/inputs, docs/GLOSSARY.md) all attribute to closed sibling cycles I previously verified+[x] (per worker-memory log). definition.py itself is untouched.

### Verification outcome
- `cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box.
