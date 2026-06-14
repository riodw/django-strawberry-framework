# Review: `django_strawberry_framework/utils/inputs.py`

Status: verified

Neutral generated-input substrate shared by the filter and order set families: the per-field spec dataclass (`GeneratedInputFieldSpec`), the GraphQL camel-name helper (`graphql_camel_name`), the Strawberry input-class builder (`build_strawberry_input_class`), the materialization ledger (`materialize_generated_input_class`), the Decision-11 consumer-helper body (`build_lazy_input_annotation`), the subclass-walk (`iter_set_subclasses`), the cycle-safe import (`_safe_import`), the namespace-clear lifecycle (`clear_generated_input_namespace`), and the BFS arguments-factory base (`GeneratedInputArgumentsFactory`). No prior on-disk artifact existed (new 0.0.9 DRY-pass file); created fresh. Plan box unchecked.

Static helper: shadow overview pre-existed under `docs/shadow/`; reviewed (2 control-flow hotspots — `clear_generated_input_namespace` 60L/5br and `_ensure_built` 36L/8br; 0 Django/ORM markers; 13 calls-of-interest all reflective-access audited; 4 repeated literals all benign).

## DRY analysis

- None — this file *is* the DRY-consolidation target. It single-sites the previously hand-mirrored spec-027 / spec-028 mechanics (materialization ledger, BFS collision check, namespace-clear lifecycle, consumer-helper body) that `filters/` and `orders/` now delegate into. The two family factories (`filters/factories.py::FilterArgumentsFactory`, `orders/factories.py::OrderArgumentsFactory`) subclass `GeneratedInputArgumentsFactory` directly and supply only family-specific caches/hooks; the two `inputs.py` delegators wrap the substrate functions under spec-named aliases. There is no further consolidation candidate inside this file, and the AggregateSet family (the only plausible third consumer) is a standing-deferred non-goal — when it lands it joins the existing base by the same direct-subclass contract, requiring no new extraction.

## High:

None.

## Medium:

None.

## Low:

### `build_strawberry_input_class` silently drops unrecognized `field_kwargs` keys

`build_strawberry_input_class` (`django_strawberry_framework/utils/inputs.py:85-98`) pops `default`, `name`, and `description` from each triple's `field_kwargs` and ignores any remaining keys: the `kwargs` dict is copied, three keys are consumed, and the leftover is discarded without inspection. Every current call site passes only those three keys (`filters/inputs.py::_build_input_fields`, `_build_range_input_class`, `_build_logic_fields`; `orders/inputs.py::_build_input_fields`), so this is correct today. But a future caller that passes e.g. `field_kwargs={"deprecation_reason": ...}` would have it silently dropped rather than forwarded to `strawberry.field(...)` or rejected. Forward-looking only. Defer until a call site needs a fourth `strawberry.field` kwarg; at that point either thread the remaining `kwargs` into `strawberry_field_kwargs` wholesale (forward-all) or raise on unrecognized keys (fail-loud). No action now — adding a guard for a key no caller passes would be speculative.

### `_ensure_built` re-walks the full BFS on every `arguments` read

`GeneratedInputArgumentsFactory.arguments` (`django_strawberry_framework/utils/inputs.py:351-357`) calls `_ensure_built()` unconditionally on each access, and `_ensure_built` (`:359-394`) re-runs the entire breadth-first walk every time — re-reading the collision registry and re-iterating `related_*` for every reachable set, even when all classes are already cached. The walk is correctly idempotent (the `target_name not in self.input_object_types` gate skips the rebuild, and the collision check sees `existing_owner is set_cls` so it never raises on a re-hit), so this is a correctness no-op, not a bug. The only consumer (`types/finalizer.py:1236` `_ = factory.arguments`) touches `.arguments` once per finalize, so the redundant re-walk never actually fires in production. Forward-looking only. Defer until a consumer reads `.arguments` more than once per factory instance in a hot path; then gate `_ensure_built` behind a `self._built` flag or memoize on the instance. No action now — the single-touch consumer makes the re-walk unobservable, and a premature `_built` flag adds state for no current benefit.

## What looks solid

### DRY recap

- **Existing patterns reused.** Reuses the shared `ConfigurationError` (`:35`) for both the materialization collision (`:131-136`) and the BFS name collision (`:379-385`) — same error type, parallel message shape (`. Rename one … so its class-derived input type name is unique.`), so the two repeated literal fragments flagged by the static helper are intentional cross-method message parity, not stray duplication. `clear_generated_input_namespace` reads the per-family binding-attr names from `set_root._lifecycle.binding_attrs` (`:265`, the `SetLifecycleAttrs` descriptor at `sets_mixins.py:279-298`) rather than re-spelling the `(owner, cache, guard)` tuple — exactly the `docs/feedback.md` Major 3 single-siting.
- **New helpers considered.** Considered extracting the `existing is cls` / `existing is not None` collision shape shared between `materialize_generated_input_class` (`:127-136`) and `_ensure_built` (`:377-385`) into one helper. Rejected: the two operate on different ledgers (`name -> input class` vs `name -> set class`), produce different message vocabulary (`family_label`/qualified-class vs `_factory_label`/`_family_label`/`_rename_noun`), and key off different identity comparisons (`is cls` idempotency vs `is set_cls` re-hit). A merged helper would need so many parameters it would not read more clearly than the two explicit sites. Correct as-is.
- **Duplication risk in the current file.** The two `getattr` reflective reads in `_ensure_built` (`:390-391`, `related` collection then `related_target_attr`) and the `_collision_registry` property's `getattr(type(self), self._collision_registry_attr)` (`:348`) are the deliberate family-hook indirection that lets one base serve both families; they are addressability-by-design, not near-copies.

### Other positives

- **BFS termination is provably correct.** `_ensure_built` (`:359-394`) uses a FIFO `pending` list plus a `seen` identity set; every dequeued set is added to `seen` before enqueueing children, and children are enqueued only when `target is not None and target not in seen` (`:393`). Cycles (`A -> B -> A`) terminate because the second visit to `A` is gated out at enqueue time; the finite live-subclass graph guarantees the queue drains. Each set's class is built exactly once via the `target_name not in self.input_object_types` gate (`:387`).
- **Collision registry and class cache stay in lockstep.** `_build_class_type` (`:396-403`) writes `input_object_types[type_name]` and `_collision_registry[type_name]` together, and the collision read (`:377`) precedes the build gate (`:387`) — so a name can never appear in one ledger without the other, and the `existing_owner is not set_cls` discriminator (`:378`) cleanly distinguishes a true cross-set collision from an idempotent re-hit of the same set.
- **Subclass-rejection guard is sound.** `__init_subclass__` (`:324-338`) permits a class only when `GeneratedInputArgumentsFactory in cls.__bases__` — i.e. a direct family factory — and raises `TypeError` for any grand-subclass, because the class-level mutable cache dicts would be inherited (shared) rather than isolated. The error names the offending parent and class and points to composition. Both family factories satisfy the guard (`FilterArgumentsFactory`/`OrderArgumentsFactory` list the base directly).
- **Annotation-only cache declarations fail loud.** `input_object_types` and the collision-registry attr are declared `ClassVar` annotation-only on the base (`:316-322`) with no default, so a family that forgets to redefine them `AttributeError`s at first use instead of silently sharing the base namespace across filter and order builds — the correct fail-loud posture for a shared substrate.
- **`materialize_generated_input_class` idempotency + collision are both correct.** Re-materializing the same `(name, cls)` pair is a no-op (`:128-129`, supports partial-finalize recovery without a sentinel pass); a distinct class under the same name raises `ConfigurationError` naming both qualified class names plus the family label (`:130-136`). The `setattr` on `sys.modules[module_path]` (`:137-138`) is the single documented entry point Strawberry's `LazyType.resolve_type` reads, matching the `strawberry.lazy(...)` contract pinned in both family docstrings.
- **`iter_set_subclasses` contract is the right one for a test-isolation clear.** It walks `type.__subclasses__()` (live subclasses only; GC'd definitions silently drop) with identity dedup (`:185-195`) — a collected definition has no binding state to reset, so dropping it is correct, and the `delattr`-only-when-`in subclass.__dict__` guard in `clear_generated_input_namespace` (`:272-274`) restores the inherited base default rather than masking it, and tolerates a subclass that never bound.
- **`_safe_import` encapsulates the partial-load lifecycle correctly.** Returns `None` on `ImportError` (including the `None`-in-`sys.modules` test-isolation simulation) so the two independent subsystem lookups in `clear_generated_input_namespace` (`:255-261`) each clear whatever is reachable without one unreachable module blocking the other — the documented best-effort contract.
- **`build_lazy_input_annotation` keeps the ForwardRef wrapping load-bearing.** The runtime-computed type name is passed as a string *into* `Annotated[...]` (`:174`) rather than interpolated into a literal outside the call, preserving the ForwardRef form `LazyType.resolve_type` resolves at schema build. The eager `issubclass` guard (`:171-172`) raises family-worded `TypeError` at the resolver-declaration site. Confirmed consumed by both `filters/__init__.py::filter_input_type` and `orders/__init__.py::order_input_type` (verified at source) — not a built-but-unconsumed surface.
- **Cycle-free dependency direction.** Imports only stdlib (`importlib`/`sys`/`collections.abc`/`dataclasses`/`typing`), `strawberry`, and the one local `..exceptions.ConfigurationError` (`:25-35`) — depends on neither family package, so both import it without a cycle (same contract as `utils/connections.py`, as the module docstring states). No first-party back-edge into `filters/`/`orders/`/`types/`.
- **GLOSSARY: no drift.** Zero GLOSSARY hits for any `utils/inputs.py` symbol — correct by design. The substrate is neutral mechanics; domain behavior is documented under feature anchors (`#filterset`, `#metafilterset_class` `docs/GLOSSARY.md:675`, `#metaorderset_class` `:809`, `#filter_input_type`, `#filterset` generated-input prose `:469`) which describe the BFS factory / materialization / consumer-helper behavior without reaching the neutral symbol names. Same no-symbol-entry pattern as `utils/connections.py` and `types/relations.py` internal scaffolding. No replacement text needed.

### Summary

`utils/inputs.py` is the 0.0.9-DRY-pass single-site for the generated-input mechanics previously hand-mirrored across spec-027 (filters) and spec-028 (orders). It reviews clean: the BFS arguments-factory base terminates provably (FIFO + identity-`seen` gate), builds each reachable set exactly once, keeps its class cache and collision registry in lockstep, and rejects grand-subclassing to protect the shared mutable caches; the materialization ledger is correctly idempotent on `(name, cls)` and loud on genuine collisions; the namespace-clear lifecycle is best-effort partial-load-tolerant and reads binding-attr names from the `SetLifecycleAttrs` descriptor rather than re-spelling them; the consumer-helper body preserves the load-bearing ForwardRef wrapping and is confirmed consumed by both families. No High or Medium findings. Two forward-looking Lows only — `build_strawberry_input_class` silently dropping unrecognized `field_kwargs` (defer until a 4th `strawberry.field` kwarg is needed) and `_ensure_built` re-walking the BFS per `arguments` read (defer until a multi-touch hot-path consumer appears) — neither warranting any edit now. Zero edits to any tracked file: no-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
None — no-source-edit cycle.

### Tests added or updated
None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — no changes (265 files left unchanged).
- `uv run ruff check --fix .` — all checks passed (standing COM812/formatter config warning only, pre-existing, not a change).

### Notes for Worker 3
- **Low 1 (`build_strawberry_input_class` drops extra `field_kwargs`):** forward-looking, recorded only. Trigger to revisit: a call site needs a 4th `strawberry.field` kwarg beyond `default`/`name`/`description`. No edit.
- **Low 2 (`_ensure_built` re-walks per `arguments` read):** forward-looking, recorded only. Correctness no-op (idempotent walk); the sole consumer touches `.arguments` once per finalize. Trigger: a multi-touch hot-path consumer. No edit.
- No GLOSSARY-only fix in scope — zero `utils/inputs.py` symbols appear in `docs/GLOSSARY.md`; the substrate is documented under feature anchors by design.

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment/docstring edits warranted — module and per-symbol docstrings are accurate, current, and cite the controlling spec decisions and `docs/feedback.md` Major items correctly; no stale TODO, no behavior-promise drift.

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. **Not warranted** — no source/test/doc edit was made (per AGENTS.md "Do not update CHANGELOG.md unless explicitly instructed"), and the active plan (`docs/review/review-0_0_9.md`) carries no changelog directive for this item.

---

## Verification (Worker 3)

### Logic verification outcome
No High/Medium findings. Both Lows confirmed forward-looking with triggers genuinely unmet, no edit warranted:
- **Low 1 (`build_strawberry_input_class` drops extra `field_kwargs`):** every production caller's `field_kwargs` carries only `name` (filters/inputs.py:692-694, orders/inputs.py:229-231) plus `default` via the spec path; `description`/4th key never passed (`grep description` over both family `inputs.py` = zero hits). Drop is current-correct; trigger (a 4th `strawberry.field` kwarg) unmet. Recorded-only correct.
- **Low 2 (`_ensure_built` re-walks per `arguments` read):** sole PRODUCTION consumer = finalizer.py:1236 `_ = factory.arguments` (single touch per finalize); all multi-touch `.arguments` reads are in tests/ (exempt). Walk is idempotent — verified live: second `.arguments` read returns the same object with no raise. Trigger (multi-touch hot-path production consumer) unmet. Recorded-only correct.

### Independent live verification (no-source-edit shape #5)
20-assertion `uv run python` probe (config.settings, fakeshop) — ALL PASS:
- **BFS termination:** A↔B cycle + A self-cycle + `Related(None)` placeholder all terminate; both A and B built exactly once (FIFO `pending.pop(0)` + identity-`seen` enqueue gate at :393 `target not in seen`).
- **Cache↔collision-registry lockstep:** `set(input_object_types) == set(_collision_registry)` after build; registry maps name→set_cls; `_build_class_type` (:402-403) writes both together.
- **Grand-subclassing rejection:** direct subclass of base allowed (fresh caches); grand-subclass of a concrete factory → `TypeError` naming parent+child+"composition" (:330-338). Forgetful subclass (no cache redefine) → `AttributeError` (annotation-only ClassVar, fail-loud :316).
- **Collision vs idempotency:** distinct set claiming an existing name → `ConfigurationError` (`existing_owner is not set_cls`, :378); same-set re-hit no raise; materialize idempotent on `(name,cls)`, distinct class same name → `ConfigurationError` naming both + family (:130-136).
- **`graphql_camel_name`** edge cases (`galaxy_name`→`galaxyName`, `""`→`""`, `"_"`→`"_"`).

### Cross-file consumption (`build_lazy_input_annotation` consumed by BOTH families)
Confirmed at source — NOT built-but-unconsumed: `filters/__init__.py:19/75` (`filter_input_type`) and `orders/__init__.py:27/76` (`order_input_type`) both import and call it. Both `FilterArgumentsFactory` (factories.py:67) and `OrderArgumentsFactory` (factories.py:33) subclass `GeneratedInputArgumentsFactory` DIRECTLY, define fresh `input_object_types = {}` + own collision registry, and supply all 5 hook attrs. `clear_generated_input_namespace` reads `set_root._lifecycle.binding_attrs` from the `SetLifecycleAttrs` descriptor (`sets_mixins.py`) rather than re-spelling — confirmed.

### DRY findings disposition
None — this file IS the DRY-consolidation single-site (feedback.md Major 1/3). No further extraction candidate; AggregateSet third consumer is standing-deferred non-goal.

### Temp test verification
- Temp test: `docs/review/temp-tests/utils_inputs/repro.py` (gitignored).
- Disposition: deleted post-run. 4 family factory consumers + the existing permanent suite (tests/filters/test_factories.py, tests/orders/test_factories.py, tests/orders/test_sets.py) already cover the shipped behavior; temp test was confirmation only.

### Shape #5 scope checks
- `git diff --stat 0872a20 -- django_strawberry_framework/utils/inputs.py` EMPTY (byte-unchanged); absent from `git status` worktree. "Files touched: None" holds.
- Every Worker 2 section starts with the no-source-edit boilerplate. Both Lows have forward-looking trigger phrasing. No GLOSSARY-only fix in scope (zero `utils/inputs.py` symbols in GLOSSARY — neutral scaffolding, by design).
- Changelog: `git diff -- CHANGELOG.md` empty; Not-warranted cites BOTH AGENTS.md + plan silence; internal-only framing honest (no public-API surface touched).
- Ruff: `format --check` "1 file already formatted"; `check` "All checks passed!" (standing COM812 config warning only).

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `utils/inputs.py` box in `docs/review/review-0_0_9.md`.
