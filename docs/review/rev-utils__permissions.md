# Review: `django_strawberry_framework/utils/permissions.py`

Status: verified

## DRY analysis

- **None — this module IS the DRY consolidation.** The whole file is the 0.0.9 single-siting of the active-input permission contract that `FilterSet` and `OrderSet` had independently grown (`docs/feedback.md` Major 3). The remaining family-specific shape correctly stays at the call sites as configuration (`unset_sentinel`, `handle_top_level_list`, `logic_keys`, `fallback_path`, the filter-only `and`/`or`/`not` recursion + depth cap). No further extraction is warranted: `request_from_info` / `extract_branch_value` / `invoke_permission_method` / `active_related_branches` / `active_permission_field_paths` / `run_active_input_permission_checks` are each single-purpose and consumed by both families through thin delegate methods (`filters/sets.py:46-54`, `orders/sets.py:40-47`). The `iter_input_items` re-export (`permissions.py:34-55`) is a deliberate import-path-preservation shim over `input_values.py` (`docs/feedback.md` Major 1), not duplication.
- **Defer (folder/project pass): `check_<field>_permission` method-name formula is spelled twice.** `invoke_permission_method` builds `f"check_{field_path.replace('__', '_')}_permission"` (`permissions.py:123`); `FilterSet.check_permissions`'s explicit-`requested_fields` arm re-spells the identical formula inline (`filters/sets.py:1302`). Defer until a third construction site of this method name appears, OR until the `check_permissions` explicit-set path is folder-reviewed; then route the explicit arm through `invoke_permission_method` (it would need a `fired=None`, bound-instance call). Quote-trigger: "third `check_…_permission` name-construction site, or filters/sets.py folder pass."

## High:

None.

## Medium:

None.

## Low:

### Active-but-unresolved child branch skips the child recursion silently (recorded-intent, scoped to permissions.py)

`run_active_input_permission_checks` (`permissions.py:251-259`) iterates active related branches and runs the child set's `_run_permission_checks` only behind `if child_set is not None and hasattr(child_set, "_run_permission_checks")`. When an active branch's `getattr(related_obj, target_attr)` is `None` (an unresolved `RelatedFilter`/`RelatedOrder` target), the **child** recursion is skipped silently — but this is NOT a gate-skip defect:

- The **parent's** per-branch gate (`cls._invoke_permission_method(bare, field_name, request, …)`, `permissions.py:259`) fires unconditionally on the next line regardless of the child-set state, so the deny gate the consumer can actually declare on the owning set (`check_<branch>_permission`) is never skipped.
- An unresolved child set is a child class that does not exist yet, so there are no child-side `check_*_permission` methods to run; skipping the recursion drops nothing that could have fired.
- The filter side independently fails loud on this exact misconfiguration in a *different* pipeline step: `_iter_visibility_steps` (`filters/sets.py:937-952`) raises `ConfigurationError` for an active branch whose `target_type`/`child_filterset` is unresolved, before any queryset is returned. So the silent skip here is backstopped by a loud error on the security-relevant (filter visibility) path.

Recorded as intent rather than a finding: the gate that matters (parent branch gate) cannot be skipped by this branch, and the order side has no visibility-derive step so its only contract is the gate dispatch, which holds. No change recommended. Re-promote to Medium only if a future consumer path can leave an active branch's child set `None` while a declared child-side gate exists that must fire — not reachable today.

### `request_from_info` returns the first non-`None` `context.request` without type-checking it

`request_from_info` (`permissions.py:73-77`) returns `getattr(context, "request", None)` whenever it is not `None`, type-checking against `HttpRequest` only on the bare-context fallback arm. A context object exposing a non-`HttpRequest` `.request` attribute would be returned verbatim and handed to the consumer's `check_*_permission(request)` hooks. This is correct-by-intent (duck-typed: Strawberry-Django wraps the real request under `.request`; the package must not hard-gate on `HttpRequest` there because consumers may use a subclass or an ASGI request), and the docstring documents the canonical shape. Low / no action — the alternative (isinstance-gating the `.request` arm too) would reject legitimate request subclasses. Noted so a future reviewer does not mistake the asymmetry between the two arms for an oversight.

## What looks solid

### DRY recap

- **Existing patterns reused.** Consumes the shared traversal substrate end-to-end: `is_inactive_value` for the single active-input rule (`permissions.py:106` via `extract_branch_value`), `iter_active_fields` + `SetInputTraversal` for the leaf/related/logic classification (`permissions.py:160-170`, `204-217`), and re-exports `iter_input_items` from `input_values.py` to preserve consumer import paths (`permissions.py:34-55`). The `LEAF` / `RELATED` kind filtering (`permissions.py:169`, `216`) is the canonical post-classification pattern.
- **New helpers considered.** Routing `FilterSet.check_permissions`'s explicit-`requested_fields` arm (`filters/sets.py:1302`) through `invoke_permission_method` was considered and deferred (see DRY analysis) — it lives in the consumer file, out of this file's scope, and the trigger is not yet met.
- **Duplication risk in the current file.** The `cls._active_permission_field_paths` / `cls._iter_active_related_branches` / `cls._invoke_permission_method` indirection in `run_active_input_permission_checks` (`permissions.py:248-259`) re-dispatches through instance methods rather than calling the module functions directly. This is intentional and load-bearing: each family's thin method supplies the family-specific config (sentinel, list-handling, logic keys, fallback), so the shared core stays family-agnostic. Collapsing it to direct module calls would re-couple the core to per-family config and defeat the consolidation.

### Other positives

- **Active-input scope is enforced at the classifier, not re-derived here.** `active_permission_field_paths` and `active_related_branches` both lean on `iter_active_fields`, which applies `is_inactive_value` to the whole input and to each field (`input_values.py:163`, `174`). A gate therefore fires for exactly the fields the consumer supplied — `None`/`UNSET` (filter) or `None` (order) inputs are skipped uniformly, and an *active* related branch is kept "regardless of the inner value's emptiness" (`permissions.py:143-147`), so an empty-but-present branch still exercises the parent branch gate. The active-input-only contract (deny gate fires only for supplied inputs, never silently skipped for a supplied one) holds across both consumers.
- **Parent-vs-child double dispatch is correct by construction.** The child recursion (`permissions.py:256`) keys its own per-class set inside the shared `fired` map (a fresh `fired.setdefault(child_cls, set())` on re-entry), while the parent branch gate (`permissions.py:259`) dedups against the parent's `class_fired`. Different classes → different dedup sets → both gates fire exactly once. This matches the GLOSSARY contract for both `FilterSet` (#filterset) and `OrderSet` (#orderset active-branch double-dispatch) verbatim.
- **Per-class dedup is keyed on the resolved set class, not the input shape.** `class_fired = fired.setdefault(cls, set())` (`permissions.py:244`) plus the `fired`-aware short-circuit in `invoke_permission_method` (`permissions.py:124-125`) means a gate fires at most once per class per top-level call, surviving the order side's `handle_top_level_list` element-by-element walk and the filter side's `and`/`or`/`not` sibling-arm re-entry (which threads the same `_fired` map, `filters/sets.py:1216-1243`). No gate is double-fired and none is dropped.
- **Deny-by-raise semantics preserved.** `invoke_permission_method` calls `method(request)` with no try/except (`permissions.py:127-128`); a consumer's `check_*_permission` that raises propagates straight up through the shared core into the consumer's `apply_sync`/`apply_async`, which run the checks *before* any `order_by`/`.qs` mutation (`orders/sets.py:566`, `filters/sets.py:1671`). The gate's denial therefore aborts the query pre-mutation, as the spec requires.
- **`request_from_info` error messages name the family.** Both `ConfigurationError` raises (`permissions.py:70`, `78`) interpolate `family_label` (`FilterSet`/`OrderSet`), so a context-resolution failure tells the consumer which sidecar's `apply` failed — the consumer-visible diagnostic the docstring promises (`permissions.py:62-66`).
- **No import-time side effects, no cycle.** Module imports only stdlib, `django.http`, `..exceptions`, and `.input_values` (all leaves); it operates on a duck-typed `cls`, so neither family package is imported — the no-cycle contract the docstring states (`permissions.py:21-23`) holds. Static overview confirms zero ORM markers and zero repeated string literals.

### Summary

`utils/permissions.py` is the 0.0.9 single-siting of the active-input permission-traversal contract shared by `FilterSet` and `OrderSet`, and it is clean. Request resolution, active-input-only scoping, parent/child branch dispatch, per-field `check_*_permission` dispatch, and deny-by-raise all verify correct against both consumers and the GLOSSARY. The security-critical invariants hold: a deny gate fires for exactly the inputs the consumer supplied and is never silently skipped for a supplied input; the parent branch gate fires unconditionally even when an active child set is unresolved (the one silent skip is the child recursion, which has nothing to run and is loud-backstopped on the filter visibility path). No High or Medium findings. Two recorded-intent Lows (benign unresolved-child child-recursion skip; intentional `request_from_info` arm asymmetry) and one defer-with-trigger DRY (the `check_…_permission` name formula spelled twice, second site in the consumer file). GLOSSARY has no per-symbol entry for these internal helpers (correct — the contract is documented under #filterset / #orderset / #per-field-permission-hooks, and that prose is accurate).

---

## Fix report (Worker 2)

Consolidated single-spawn (no-findings file pass for the in-scope file). `utils/permissions.py` is clean: zero High/Medium, two recorded-intent Lows (no action), one defer-with-trigger DRY (second site lives in a consumer file, trigger not met). The cross-file `OrderSet.check_permissions`/`self._input_value` follow-up was investigated at source and classified (see Notes). Zero edits to `utils/permissions.py`.

### Files touched

- None in scope. `django_strawberry_framework/utils/permissions.py` received zero edits.
- Repro only (not a tracked test): `docs/review/temp-tests/utils_permissions/repro_orderset_check_permissions.py`.

### Tests added or updated

- None. The in-scope file changed no behavior; the classified finding is out-of-scope (orders/sets.py) and forwarded, not fixed here.

### Validation run

- `uv run ruff format .` — pass / no-changes (265 files left unchanged).
- `uv run ruff check --fix .` — pass (All checks passed!).
- `uv.lock` — clean (untouched by the `uv run` invocations).
- Focused repro (proves the classification, NOT a regression test):
  `DJANGO_SETTINGS_MODULE=config.settings PYTHONPATH=examples/fakeshop uv run python docs/review/temp-tests/utils_permissions/repro_orderset_check_permissions.py` — A/B/C all PASS.

### Notes for Worker 3

**Shadow file used:** `docs/shadow/django_strawberry_framework__utils__permissions.overview.md` (read-only). Source line numbers cited throughout; overview confirms zero ORM markers and zero repeated string literals.

**The 2 recorded-intent Lows — Worker 1's dispositions hold, no source edit:**
1. *Active-but-unresolved child-branch silent skip* (`permissions.py:251-259`): re-verified the parent branch gate `cls._invoke_permission_method(bare, field_name, request, fired=class_fired)` (`permissions.py:259`) fires unconditionally on the line AFTER the `if child_set is not None and hasattr(...)` guard, so the gate the consumer can declare on the owning set is never skipped; an unresolved child set has no `check_*_permission` methods to run. Backstopped loud on the filter visibility path (`filters/sets.py` `_iter_visibility_steps`). Benign. No change.
2. *`request_from_info` arm asymmetry* (`permissions.py:73-77`): correct-by-intent duck-typing — the `.request` arm must not `isinstance`-gate on `HttpRequest` or it would reject legitimate ASGI/subclass requests; the bare-context fallback arm gates because there is no wrapper to trust. No change.

**CLASSIFICATION of the `OrderSet.check_permissions` / `self._input_value` finding — DEAD-CODE LOW (NOT a broken-gate High), located in `orders/sets.py` (OUT of this cycle's scope) → FORWARD to the project pass. orders/sets.py does NOT need to re-open for a security fix.**

Evidence (grep + repro, not assertion):
- `_input_value` is **written by exactly one site in the entire tree, and it is a test**: `tests/orders/test_sets.py:464` (`instance._input_value = input_value`). `grep -rn "_input_value\s*=" django_strawberry_framework/ examples/ tests/` returns only that one assignment; the package source has **zero writers**. The read at `orders/sets.py::OrderSet.check_permissions #"getattr(self, \"_input_value\""` is a defensive `getattr(self, "_input_value", None)` with a `None` fallback.
- `OrderSet.check_permissions` (the bound method, `orders/sets.py:448-460`) is **called only by tests** (`tests/orders/test_sets.py:466,480`). `grep -rn "check_permissions" examples/ tests/` shows no production caller; the live order resolver path is fully classmethod-driven: `apply_sync`/`apply_async` (`orders/sets.py:565-566`) call `cls._run_permission_checks(input_value, request)` with the input passed as an **argument**, never via `self._input_value`. `OrderSet` instances are never constructed with input parked on them in production (`OrderSetMetaclass.__new__` only builds the class; the only `object.__new__(cls)` in source is the gate-dispatch `bare` at `orders/sets.py:431`, which is never assigned `_input_value`).
- **Contrast with the filter side, which is functional:** `FilterSet.check_permissions` (`filters/sets.py:1290-1310`) delegates with `self.data or {}` — `self.data` is the bound Django form data populated by the FilterSet's normal instance lifecycle, a real production source. The order side has no instance-bound input equivalent, so its bound method has nothing to read in production.
- **Why this is a LOW, not a High:** the live order-side per-field `check_<field>_permission` denial gate DOES fire and aborts pre-mutation — proven by repro step B (`apply_sync` raised `PermissionError` from `check_title_permission`). No data-isolation gate fails to fire; the working path is the active-input `_run_permission_checks` one. The bound `check_permissions` + `_input_value` read are vestigial cookbook-compat surface (per the module docstring at `orders/sets.py #"Add the ``check_permissions`` instance method"`) with no production writer — dead code, not a broken security gate. Repro steps A (production-shaped instance → no-op, gate never fires) and C (only the test-only `_input_value` write makes it fire) confirm.
- **Scope discipline:** the dead code is entirely in `orders/sets.py` (the `check_permissions` method body + its docstring's `self._input_value` reference) and the test-only writer in `tests/orders/test_sets.py`. Per the dispatch instruction, `orders/sets.py` is NOT edited in this `utils/permissions.py` cycle. Recorded here as a forward to the project pass / orders/sets.py folder review. A spawn_task chip is raised for the cleanup.

**DRY defer-with-trigger** (`check_…_permission` name formula spelled twice): confirmed second site `filters/sets.py:1302` still re-spells the formula inline; trigger ("third construction site, OR filters/sets.py folder pass") not met. Left as recorded.

**Temp-test caveat:** the repro under `docs/review/temp-tests/utils_permissions/` is a classification proof, not a regression test, and is not placed under any `tests/` tree — the in-scope file changed no behavior so no pinning test is warranted.

---

## Verification (Worker 3)

No-source-edit (shape #5) consolidated pass. Cycle diff for `permissions.py` is EMPTY
(`git diff --stat <baseline> -- django_strawberry_framework/utils/permissions.py` empty;
`git status` clean). CHANGELOG diff empty. Ruff format-check + check pass on the file.

### Logic verification outcome

**SECURITY-SENSITIVE classification independently confirmed — DEAD-CODE LOW, NOT a broken gate.**
Did not trust the artifact; re-derived from grep + repro:

- `_input_value` has ZERO production writers: `grep -rn "_input_value\s*=" django_strawberry_framework/ examples/ tests/` returns exactly ONE assignment, `tests/orders/test_sets.py:464` (a test). The read at `orders/sets.py::OrderSet.check_permissions` is `getattr(self, "_input_value", None)` with a `None` fallback.
- Bound `OrderSet.check_permissions` (`orders/sets.py:448-460`) has NO production caller: `grep -rn check_permissions` across source shows the only callers are tests (`tests/orders/test_sets.py:466,480`); the package source never calls it. The only `object.__new__(cls)` in orders source is the gate-dispatch `bare` at `orders/sets.py:431`, never assigned `_input_value`.
- The LIVE order-side gate fires via the classmethod path: `apply_sync:566` / `apply_async:605` call `cls._run_permission_checks(input_value, request)` with the input passed as an ARGUMENT, never via `self._input_value`.

Repro (`docs/review/temp-tests/utils_permissions_verify/repro_classification.py`, run under `config.settings`): **A** production-shaped instance (no `_input_value`) → bound `check_permissions` is a NO-OP (gate never fires); **B** `apply_sync` DOES raise `PermissionError` from `check_title_permission` (the real path works, denial aborts pre-mutation); **C** the gate fires from the bound method ONLY when the test-only `_input_value` write is present. ALL PASS. → vestigial cookbook-compat surface, not a reachable-but-silently-failing security gate. **orders/sets.py does NOT re-open for a security fix.**

**Substrate `permissions.py` is clean.** Read `run_active_input_permission_checks` (permissions.py:220-259): the parent per-branch gate `cls._invoke_permission_method(bare, field_name, request, fired=class_fired)` (line 259) fires UNCONDITIONALLY after the `if child_set is not None and hasattr(...)` guard (line 253), so the deny gate the consumer declares on the owning set is never skipped. The lone silent skip is the CHILD recursion when an active branch's target is unresolved — benign: an unresolved child set has no `check_*_permission` methods to run, and the filter side fails loud on the same misconfig at `filters/sets.py::_iter_visibility_steps` (lines 937-945 raise `ConfigurationError` when `target_type is None or child_filterset is None`). Active-input-only deny contract holds (gate fires for exactly the supplied inputs; none silently skipped for a supplied one).

Two recorded-intent Lows (unresolved-child child-recursion skip; `request_from_info` arm asymmetry) hold as Worker 1 dispositioned — both benign, no source change warranted.

### DRY findings disposition

The defer-with-trigger DRY (`check_…_permission` name formula spelled twice; second site `filters/sets.py:1302`) — trigger ("third construction site, OR filters/sets.py folder pass") not met; left recorded. The dead-code LOW is recorded in this artifact's `## Fix report (Worker 2)` Notes (the contract input the orders/project pass reads) AND a spawn_task chip was raised; forward targets `rev-orders__sets.md` and `rev-django_strawberry_framework.md` both exist and reference `check_permissions`/`_input_value`. Forward is routed, NOT silently dropped.

### Temp test verification

- Temp test: `docs/review/temp-tests/utils_permissions_verify/repro_classification.py` (classification proof, A/B/C all PASS).
- Disposition: deleted at cycle closeout (Worker 0). NOT promoted — the in-scope file changed no behavior, so no pinning test is warranted; the dead-code cleanup (and any test) belongs to the orders/sets.py / project pass that performs it.

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `utils/permissions.py` checklist box in `docs/review/review-0_0_9.md`.

---

## Comment/docstring pass

### Files touched

- None. The in-scope file (`utils/permissions.py`) needed no logic change, so no comment/docstring update is warranted. Its docstrings accurately describe the active-input contract verified above (parent-vs-child double dispatch, deny-by-raise, active-input-only scope).

### Per-finding dispositions

- Low 1 (unresolved child-branch silent skip): recorded-intent, no action — docstring at `permissions.py:233-242` already documents the parent-vs-child double dispatch and the unconditional parent gate accurately.
- Low 2 (`request_from_info` arm asymmetry): recorded-intent, no action — docstring at `permissions.py:59-67` already documents the canonical/fallback shapes; the asymmetry is intentional.
- DRY defer-with-trigger (`check_…_permission` formula spelled twice): trigger not met, left.
- Cross-file `OrderSet.check_permissions`/`_input_value`: classified DEAD-CODE LOW in `orders/sets.py` → forwarded to project pass (out of this file's scope; not edited here).

### Validation run

- `uv run ruff format .` — pass / no-changes (265 unchanged).
- `uv run ruff check --fix .` — pass.

### Notes for Worker 3

Consolidated single-spawn: no-findings file pass for `utils/permissions.py` (zero edits), with the cross-file follow-up classified and forwarded. The classification (dead-code LOW in orders/sets.py, NOT a broken-gate High) is the substantive output of this cycle and is backed by the grep evidence + repro recorded in `## Fix report (Worker 2)`.

---

## Changelog disposition

### State

`Not warranted`.

### Reason

- `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed"): no changelog authorization in scope.
- The active plan is silent on changelog authorization for this cycle; per the role file, a per-file cycle is never the authorising scope.
- Additionally there is no consumer-visible change to record: zero edits to `utils/permissions.py`, and the classified `OrderSet.check_permissions` finding is dead code (no production writer of `_input_value`, no production caller of the bound method) whose removal would be invisible to consumers. Any changelog disposition for that cleanup belongs to the orders/sets.py / project pass that actually performs it.

### What was done

No `CHANGELOG.md` edit.

### Validation run

- `uv run ruff format .` — pass / no-changes.
- `uv run ruff check --fix .` — pass.

---

## Iteration log
