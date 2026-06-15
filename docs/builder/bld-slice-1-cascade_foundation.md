# Build: Slice 1 — cascade foundation

Spec reference: `docs/spec-034-permissions-0_0_10.md` (lines 56-63; Decision 4 / Decision 5 / Decision 8 / Decision 9 / Decision 10; Edge cases 383-407; Slice 1 Test plan 413-437)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

- **Existing patterns reused.**
  - **Sync-misuse coroutine probe** — `django_strawberry_framework/utils/querysets.py:93-119` (`apply_type_visibility_sync`): `result = type_cls.get_queryset(...)` → `if inspect.iscoroutine(result): result.close(); raise SyncMisuseError(...)`. Slice 1's per-edge target-hook invocation reuses this exact probe shape (Decision 10, spec line 60/315). **Do NOT re-implement the probe inline in `permissions.py`** — call `apply_type_visibility_sync(target_type, base_qs, info)` so the package has ONE place that runs a sync `get_queryset` and rejects an async hook. That helper already does `type_cls.get_queryset(queryset, info)` + `iscoroutine` close + `SyncMisuseError`; the cascade's per-edge constraint is precisely "run the target type's visibility hook against the target model's rows", which is what `apply_type_visibility_sync` is for. This is the single biggest DRY lever in the slice and the explicit Decision 10 instruction.
  - **`SyncMisuseError`** — `utils/querysets.py:35-55`, re-exported via `types` and the package root. Reused as-is by reusing `apply_type_visibility_sync` (it raises it); `permissions.py` does not define a new error or a new message discipline for the async-hook case. (The helper's current message text names "the Relay node defaults"; see `### Notes for Worker 1 (spec reconciliation)` — the spec wants a message naming the two cascade recourses, which is a tension between reuse and message specificity. Resolution recorded below.)
  - **`sync_to_async(thread_sensitive=True)` async-wrap precedent** — `django_strawberry_framework/filters/sets.py:23` (import) and `:1745-1749` (`return await sync_to_async(cls._apply_common_finalize, thread_sensitive=True)(...)`), plus the `_read_qs` callable-wrapper note at `:91-100`. `aapply_cascade_permissions` follows this verbatim: `from asgiref.sync import sync_to_async`, then `return await sync_to_async(_walk, thread_sensitive=True)(cls, queryset, info, fields)` (or wrap the public sync function). One walk implementation, no sync/async fork (Decision 10, spec line 61/316-319).
  - **Registry primary lookup** — `django_strawberry_framework/registry.py:221-240` (`TypeRegistry.get(model)`): primary-declared → primary; single-type-no-primary → that type; ambiguous/none → `None`. The cascade resolves each FK edge's target type via `registry.get(field.related_model)` and skips on `None` (Decision 5 step 2, spec line 58/258). Import the module-level singleton `from .registry import registry` (registry.py:530), the same import every subsystem uses.
  - **Custom-hook gate** — `django_strawberry_framework/types/base.py:668-686` (`DjangoType.has_custom_get_queryset()`), default identity hook at `:653-666`. The cascade skips a target whose `has_custom_get_queryset()` is `False` (identity adds nothing — no dead `__in` SQL), Decision 5 step 3 (spec line 59/259). Reused as the package's existing sentinel; no new "is this hook custom?" logic.
  - **Base queryset seed** — `utils/querysets.py:58-68` (`initial_queryset(type_cls)`) returns `type_cls.__django_strawberry_definition__.model._default_manager.all()`. The cascade builds its per-edge base from `related_model._default_manager.using(queryset.db).all()` (Decision 5 step 4 / Decision 8). Note this is `related_model`-keyed and alias-pinned, so it is NOT `initial_queryset` (which is type-keyed and unrouted); the `_default_manager.all()` *idiom* matches, but the alias pin is the load-bearing difference (see Duplication risk avoided). Reuse the `_default_manager` choice (not `.objects`) so renamed default managers keep working (upstream note, spec line 260).
  - **`ConfigurationError`** — `django_strawberry_framework/exceptions.py:20-30`. `fields=` validation raises it (Decision 9, spec line 59/307); no new exception class.
  - **Test fixtures** — synthetic-graph + custom-hook `DjangoType` declaration pattern and the `registry.clear()` autouse isolation fixture at `tests/types/test_base.py:59-63` (`_isolate_registry`), `:71-101` (declare a `DjangoType` subclass with `Meta.model` then assert `registry.get(...)`). `tests/test_permissions.py` mirrors this. The multi-DB pin builds on `tests/optimizer/test_multi_db.py` (its in-test `registry.clear()` + minimal-definition + `.using("shard_b")` pattern, lines 59-128), per the Slice 1 Test plan harness note (spec line 420) and build-plan flag (build-034 line 28).
  - **Products fixtures for the transitive/happy-path pins** — `apps.products.services.seed_data(N)` / `create_users(N)` (AGENTS.md "first line" rule). The `Entry → Item → Category` / `Entry → Property → Category` 2-deep FK graph (`examples/fakeshop/apps/products/models.py:44-142`) is the transitive-cascade fixture; all four products models carry `is_private` (BooleanField default False).

- **New helpers justified.** One new module, `django_strawberry_framework/permissions.py` (Decision 3, spec line 230), holding:
  - the two public functions `apply_cascade_permissions(cls, queryset, info, fields=None)` and `aapply_cascade_permissions(cls, queryset, info, fields=None)` (Decision 4);
  - the module-level `_cascade_seen: ContextVar[set | None]` cycle-guard var (Decision 5 step 5 — upstream `_cascade_seen` shape verbatim, spec line 58/261);
  - **one** private `fields=` validation helper (single responsibility: given `cls`'s model + the `fields=` argument, return the validated set of cascadable edge names, or raise `ConfigurationError` / reject the bare string — Decision 9). Single helper, not per-call-site logic (build-034 line 36).
  - the private single sync walk (single responsibility: depth-1 walk of `cls`'s model edges intersecting one constraint per qualifying edge). `aapply_cascade_permissions` wraps THIS walk in `sync_to_async`; there is no second async walk implementation (Decision 10).
  - a private edge-scope predicate (single responsibility: `related_model present AND hasattr(field, "column") AND NOT getattr(field.remote_field, "parent_link", False)` — Decision 5 step 1). Used by both the `fields=None` full walk and the `fields=` validation (the cascadable set the validator compares against IS the set of edges passing this predicate), so the predicate must be the single source of truth for "cascadable edge" to keep validation and walk in lock-step. This is the DRY hinge of the module.

- **Duplication risk avoided.**
  - **Re-implementing the sync-misuse probe** inline (a second `iscoroutine`/`close`/raise site that could drift from `utils/querysets.py`). Avoided by calling `apply_type_visibility_sync` for the per-edge hook run (Decision 10). A visibility-hook-routing mistake is a data-leak bug, so the routing must not be re-decided here (the `utils/querysets.py` module docstring states this exact rule).
  - **A sync/async walk fork.** The naive shape writes `apply_cascade_permissions` and a near-copy `aapply_cascade_permissions` that re-walks edges. Avoided: the async twin is `sync_to_async(thread_sensitive=True)` around the single sync walk (Decision 10, `filters/sets.py:1745` precedent). Async target hooks therefore raise `SyncMisuseError` from BOTH variants (no awaiting context inside the worker thread) — the documented consequence (spec line 317).
  - **Two definitions of "cascadable edge."** If the `fields=` validator enumerated edges with its own predicate while the walk used another, a scope drift would silently under- or over-cascade. Avoided by the single edge-scope predicate above; `fields=` validation is `set(fields) - cascadable_names` where `cascadable_names` comes from that one predicate.
  - **A precomputed/finalize-time cascade plan cache** (an invalidation-semantics layer). Out of scope per Decision 5 alternatives ("measure first") and Risks ("Cascade-call overhead"); the per-call `fields=` set diff is acknowledged redundant-but-bounded (Decision 9, spec line 309). Do NOT add a memo in this slice.
  - **Eager PK materialization** (`pk__in=list(target_qs)`) — an extra round-trip per edge; the constraint MUST compose the unevaluated subquery (`Q(**{f"{field.name}__in": target_qs})`) so Django compiles it into the caller's single SELECT (Decision 7, spec line 288/295). Worker 2 must not call `list(...)` / iterate the target queryset.

### Implementation steps

Line numbers are pin-at-write-time navigational hints; verify against current source before editing.

1. **Create `django_strawberry_framework/permissions.py`** (new module, Decision 3). Module docstring states: the call-time cascade contract, the four upstream invariants, the registry/custom-hook adaptations, and that the async twin wraps the single sync walk. Imports: `from __future__ import annotations`; `import inspect` is NOT needed if the probe is delegated to `apply_type_visibility_sync` (preferred — see DRY); `from contextvars import ContextVar`; `from typing import Any`; `from asgiref.sync import sync_to_async`; `from django.db.models import Q`; `from .exceptions import ConfigurationError`; `from .registry import registry`; `from .utils.querysets import apply_type_visibility_sync`. (Confirm no import cycle: `utils/querysets.py` imports only `django` + `..exceptions` per its docstring lines 19-23, and `registry.py` imports only `.exceptions`; `permissions.py` is a leaf consumed by `__init__.py` and consumer `get_queryset` bodies, so importing registry + utils + exceptions closes no cycle.)

2. **Module-level cycle-guard var.** `_cascade_seen: ContextVar[set | None] = ContextVar("_cascade_seen", default=None)` (Decision 5 step 5; upstream `_cascade_seen` name verbatim, spec line 58/261). Default `None` distinguishes "no walk in flight" (root) from "walk in flight" (re-entry).

3. **Edge-scope predicate** — private helper `_is_cascadable_edge(field) -> bool`: `getattr(field, "related_model", None) is not None and hasattr(field, "column") and not getattr(field.remote_field, "parent_link", False)` (Decision 5 step 1, spec line 57/257; MTI exclusion spec line 397). This is the single definition of "cascadable edge" (DRY hinge). M2M / reverse FK / reverse O2O / GFK / GenericRelation / composite-PK are excluded by construction (no single-column `column`, or `related_model` absent), not by enumeration (spec lines 395-396).

4. **`fields=` validation** — private helper that, given `model` and `fields`, returns the set of edge names to walk:
   - `if fields is None:` return the full cascadable-name set (every `field.name` in `model._meta.get_fields()` passing `_is_cascadable_edge`).
   - `if isinstance(fields, str):` raise `ConfigurationError` naming the non-string-iterable requirement (Decision 9, spec line 59/186/307 — guard FIRST, before any per-name lookup, so `fields="item"` does not validate `'i','t','e','m'`).
   - else: `requested = set(fields)`; `cascadable = {names...}`; `unknown = requested - cascadable`; if `unknown:` raise `ConfigurationError` naming the offending entry/entries, the model, and the cascadable set (spec line 307). `fields=[]` → `requested == set()`, `unknown == ∅`, returns empty set: a defined no-op distinct from `None` (spec line 407; `test_fields_empty_list_cascades_nothing`). A name that is cascadable but whose target has no registered type / no custom hook is accepted here and skipped by the walk's per-edge gate (spec line 406; `test_fields_valid_but_hookless_name_accepted`).

5. **The single sync walk** — private `_cascade_walk(cls, queryset, info, fields)`:
   - Resolve `model = cls.__django_strawberry_definition__.model` (the registered model; same accessor `utils/querysets.py:68` uses).
   - Compute `names_to_walk = _validate_fields(model, fields)` (step 4).
   - **Cycle guard install/clear (Decision 5 step 5):** read `seen = _cascade_seen.get()`. If `seen is None` (root): `seen = set()`, `token = _cascade_seen.set(seen)`, wrap the body in `try/finally` that does `_cascade_seen.reset(token)` (request isolation under WSGI+ASGI, spec line 390). If `cls in seen`: return `queryset` unchanged (partial narrow, never raise — spec line 58/188/261). Else add `cls` to `seen`; on frame exit `seen.discard(cls)` so sibling edges to the same target both cascade (frame-exit discard, spec line 389). Pin down the exact root-vs-nested control flow as an Implementation discretion item (two equivalent shapes — see below).
   - **Per-edge loop:** for each `field` in `model._meta.get_fields()` where `_is_cascadable_edge(field)` and (`fields is None` or `field.name in names_to_walk`):
     - `target_type = registry.get(field.related_model)`; if `target_type is None:` continue (unregistered → skip, spec line 391).
     - if not `target_type.has_custom_get_queryset():` continue (identity hook → skip, no dead SQL, spec line 59/259).
     - `base = field.related_model._default_manager.using(queryset.db).all()` (`_default_manager` not `.objects`; alias pinned to `queryset.db` the resolved property, NOT `_db` — Decision 8, spec line 260/299).
     - `target_qs = apply_type_visibility_sync(target_type, base, info)` (runs the hook + rejects async hook with `SyncMisuseError`, coroutine closed — Decision 10, spec line 60/315). **Unevaluated** — do not materialize.
     - `queryset = queryset.filter(Q(**{f"{field.name}__in": target_qs}) | Q(**{f"{field.name}__isnull": True}))` (Decision 5 step 4; nullable-FK preservation via `__isnull=True` disjunct, spec line 57/385; zero-round-trip lazy subquery, Decision 7).
   - return `queryset`.

6. **`apply_cascade_permissions(cls, queryset, info, fields=None)`** — public sync entry. Thin: delegates to `_cascade_walk(cls, queryset, info, fields)`. (Whether `apply_cascade_permissions` IS `_cascade_walk` or a one-line wrapper is discretion — see below.)

7. **`aapply_cascade_permissions(cls, queryset, info, fields=None)`** — public async entry. `return await sync_to_async(apply_cascade_permissions, thread_sensitive=True)(cls, queryset, info, fields)` (Decision 10, `filters/sets.py:1745` precedent). The `ContextVar` install/reset happens inside the worker thread on the asgiref-copied context, so it never leaks back to the event-loop task (spec line 316/390). Async target hooks still raise `SyncMisuseError` (no awaiting context inside the thread — documented consequence, spec line 317; `test_aapply_async_target_hook_still_raises`).

8. **Export from the package root** — `django_strawberry_framework/__init__.py`: uncomment the staged seam at `__init__.py:32-40` (the `from .permissions import (aapply_cascade_permissions, apply_cascade_permissions)` block), add the two names to `__all__` alphabetically (currently `__init__.py:44-62` — they sort as the first two entries, before `"BigInt"`), and **delete the file-wide `# ruff: noqa: ERA001` directive at `__init__.py:3-8`** (its sole purpose was to silence eradicate on the staged comment block; once uncommented it is dead and must go — Worker 3's public-surface check and the `git diff` of `__init__.py` will scrutinize this). Remove the two `TODO(spec-034 Slice 1)` comment blocks (`:32-36` import-seam comment and `:45-47` `__all__` comment).

9. **Grow the exports pin** — `tests/base/test_init.py::test_public_api_surface_is_pinned` (lines 30-55): add `"aapply_cascade_permissions"` and `"apply_cascade_permissions"` to the expected `__all__` tuple alphabetically (they become the first two entries). Remove the `TODO(spec-034 Slice 1)` comment block at `:35-39`. **Do NOT touch `test_version` (line 10-11) or the `__version__` string** — Decision 13 (build-034 line 22). This is the one card-owned exports growth in an otherwise version-frozen file.

10. **Create `tests/test_permissions.py`** (new) per the Slice 1 Test plan — see `### Test additions / updates`.

### Test additions / updates

All pins below are in new `tests/test_permissions.py` unless noted. Mirror `tests/types/test_base.py` isolation: a `registry.clear()` autouse fixture (`test_base.py:59-63` shape). Synthetic graphs use throwaway `DjangoType` subclasses with custom `get_queryset` hooks; happy-path/transitive pins use products models + `seed_data`/`create_users` (AGENTS.md first-line rule). Each test's assertion shape is pinned below.

The card's four dedicated upstream-invariant pins, first (DoD item 3, spec line 415-421):

- `test_cycle_guard_contextvar_breaks_mutual_cascade` — synthetic A↔B graph where `AType.get_queryset` cascades into B and `BType.get_queryset` cascades back into A. **Assert:** the call terminates (no `RecursionError`); both directions apply each other's *direct* narrowing (assert the composed `Q` / result rows reflect one level of each hook); and `_cascade_seen.get()` is `None` after the root call returns — *and after an exception* (wrap a hook to raise, assert the var is still `None` in `finally`, spec line 390/417). Reach into `_cascade_seen` directly (module-internal, package test).
- `test_single_column_scope_skips_m2m_reverse_and_generic` — synthetic model carrying a forward FK, a forward OneToOne, an M2M, a reverse FK (`related_name`), a reverse OneToOne, a `GenericForeignKey`, a `GenericRelation`, and a composite-FK shape. **Assert:** only the forward FK and forward OneToOne edges produce an `__in`/`__isnull` constraint (inspect `str(result.query)` for the FK column names, or assert which edges were walked via a hook-call spy); M2M/reverse/generic/composite contribute none (spec line 418).
- `test_mti_parent_link_edge_excluded` — synthetic MTI child whose `<parent>_ptr` `OneToOneField(parent_link=True)` would pass the two-predicate test. **Assert:** the `<parent>_ptr` edge is NOT walked (no constraint on it; child row not narrowed by the MTI-parent type's hook), proving the `parent_link` guard (spec line 419/397). Synthetic only — no fakeshop MTI model.
- `test_multi_db_subquery_pinned_to_caller_alias` — **`FAKESHOP_SHARDED`-gated** (the `shard_b` alias only exists under the env var, `settings.py:116`; not runnable under bare `uv run pytest`). Build on `tests/optimizer/test_multi_db.py`'s in-test pattern (lines 59-128: `registry.clear()`, minimal definition register, `.using("shard_b")`). **Assert:** a `.using("shard_b")` caller produces cascade subqueries on `"shard_b"` (inspect `result.query` / the composed subquery's `.db`, or capture queries per alias); a router-divergent model pair stays single-DB. Gate the test (skip marker keyed on `os.environ.get("FAKESHOP_SHARDED") == "1"` or the `shard_b` alias presence) so it no-ops under default settings, matching the multi-DB harness precedent. (Worker 2: the exact gating mechanism — `pytest.mark.skipif` on the env var vs. on `"shard_b" in settings.DATABASES` — is discretion; mirror whatever `test_multi_db.py`/its siblings establish.)
- `test_nullable_fk_rows_preserved` — synthetic graph with a nullable FK whose target hook hides every row. **Assert:** `NULL`-FK rows survive (the `__isnull=True` disjunct); non-null-FK rows pointing at hidden targets drop (spec line 421/385). (Fakeshop FKs are all non-nullable — `models.py:52/92/132/137` have no `null=True` — so this invariant needs a synthetic nullable FK, confirming the Test plan's synthetic-graph choice.)

Then the remaining contract (spec line 423-436):

- `test_cascade_excludes_rows_with_hidden_targets` / `test_hidden_and_missing_targets_indistinguishable` — a parent row whose FK points at a hidden target is absent; indistinguishable from a row pointing at a deleted/missing target (Decision 6, spec line 425/189).
- `test_transitive_cascade_two_deep` — products `Entry → Item → Category` with hooks cascading at each level (the products hooks are NOT yet uncommented in Slice 1, so this uses *synthetic* `DjangoType` subclasses over the products models with custom cascading hooks, OR throwaway models; assert that hiding a `Category` drops the `Entry`s under its `Item`s). **Assert:** transitive narrowing through two edges; the seen-set permits the chain (spec line 426).
- `test_identity_hook_targets_skipped_no_sql` — a target type whose `has_custom_get_queryset()` is `False` contributes no subquery. **Assert:** `str(result.query)` contains no `IN (SELECT ...)` clause for that edge (SQL-string assertion, spec line 427/259).
- `test_unregistered_target_model_skipped` / `test_secondary_type_never_cascade_target` — an FK whose target model has no registered `DjangoType` is skipped; `registry.get(model)` returning the primary means a stricter secondary hook never cascades (spec line 428/392).
- `test_secondary_type_as_root_reaches_primary_on_transitive_revisit` — a cascade rooted on a *secondary* type that re-reaches its own model through another edge narrows by the **primary** hook; walk terminates (seen-set keys on the class object, so `secondary ≠ primary`, spec line 429/393).
- `test_cascade_target_sliced_or_values_queryset_is_consumer_bug` — a target hook returning `.values("col")` mis-narrows / a multi-column `.values()` raises `ValueError` ("the 'in' lookup must have 1 selected field"); the helper does not defensively rewrite the hook's return (cascade-target return contract, spec line 430/398). **Assert:** the `ValueError` propagates for multi-column `.values()` (the load-bearing pin); document the single-column `.values()` mis-narrow.
- `test_fields_scopes_walk` — `fields=["item"]` cascades only the `item` edge, leaves `property` alone (spec line 174/431).
- `test_fields_unknown_name_raises` / `test_fields_non_cascadable_name_raises` — `ConfigurationError` naming the field, the model, and the cascadable set (assert all three substrings in the message, spec line 431/307).
- `test_fields_valid_but_hookless_name_accepted` — a cascadable edge whose target lacks a registered type / custom hook validates clean and contributes nothing (no raise, spec line 431/406).
- `test_fields_bare_string_raises` — `fields="item"` raises `ConfigurationError` from the `isinstance(fields, str)` guard; **assert** the message names the non-string-iterable requirement and does NOT mention a per-character `'i'` lookup (spec line 432/186).
- `test_fields_empty_list_cascades_nothing` — `fields=[]` validates clean and cascades zero edges (defined no-op, distinct from `fields=None` cascading all); no raise (spec line 433/407).
- `test_sync_helper_raises_syncmisuseerror_on_async_target_hook` — a target type with an `async def get_queryset` reached from `apply_cascade_permissions`: **assert** `SyncMisuseError` raised, the coroutine is closed (no `RuntimeWarning` — use `pytest`'s warning capture / `-W error::RuntimeWarning` is already the project default per memory, so an un-closed coroutine would surface), message names the target type. (The message-recourse-wording tension is in Notes for Worker 1 — the reused `apply_type_visibility_sync` message names "the Relay node defaults", which is accurate-but-generic for the cascade path; Worker 1's resolution governs whether the assertion pins cascade-specific recourses.)
- `test_aapply_runs_walk_off_event_loop` — `aapply_cascade_permissions` runs the walk off the event loop; the `_cascade_seen` set installed inside the wrapped thread does NOT leak back into the calling async context (assert `_cascade_seen.get()` is `None` in the async caller after the await — asgiref copies the context into the worker thread, spec line 435/316/390). Async test (mark per the suite's async-test convention).
- `test_aapply_async_target_hook_still_raises` — an `async def` target hook reached via `aapply_cascade_permissions` still raises `SyncMisuseError` (the Decision 10 consequence — no awaiting context inside the thread, spec line 435/317).
- `test_self_referential_fk_cascades_once` — a `parent = FK("self")` type cascades into itself; the seen-set breaks recursion at depth 1 per frame (constraint still applies one level, nested call returns un-narrowed, spec line 436/387).

Exports pin (extends an existing file — DoD item 5, spec line 437):

- `tests/base/test_init.py::test_public_api_surface_is_pinned` — add `"aapply_cascade_permissions"` + `"apply_cascade_permissions"` to the expected `__all__` tuple (alphabetical, first two). Also implicitly pins the package-root import (`from django_strawberry_framework import apply_cascade_permissions`) works, since the module imports the package. **Do not touch `test_version`** (Decision 13).

Temp/scratch test note for Worker 3: the multi-DB pin is `FAKESHOP_SHARDED`-gated and will not run under a default `uv run pytest`; Worker 3 may run it under `FAKESHOP_SHARDED=1 uv run pytest tests/test_permissions.py -k multi_db --no-cov` to confirm it exercises the alias path (no `--cov*` flags). No temp tests are expected to be promoted — all pins land directly in `tests/test_permissions.py`.

### Implementation discretion items

Worker 1 has assessed these and decided they are Worker 2's choice (equivalent shapes / naming):

- **Public-function vs. private-walk factoring.** Whether `apply_cascade_permissions` is itself the walk function, or a thin public wrapper delegating to a private `_cascade_walk`, is discretion — both are equally valid as long as (a) there is exactly ONE walk implementation and (b) `aapply_cascade_permissions` wraps the *public* `apply_cascade_permissions` (so the cycle-guard install/reset runs inside the worker thread). The cleaner shape is likely `apply_cascade_permissions` holding the cycle-guard + walk directly with private `_is_cascadable_edge` / `_validate_fields` helpers; Worker 2 picks.
- **Root-vs-nested control flow shape.** The `seen is None` (root: install + `try/finally` reset) vs. `cls in seen` (re-entry: return unchanged) vs. else (add + `try/finally` discard) branching can be written as one function with nested try/finally or split into a tiny `_with_seen` context-manager-style helper. Either is fine provided the upstream `_cascade_seen` lifecycle holds verbatim (root resets the var, every frame discards its own class, re-entry partial-narrows). Worker 2 picks the readable shape.
- **`names_to_walk` membership test.** Whether the walk filters by `field.name in names_to_walk` for the `fields is not None` case while `fields is None` skips the membership test, or always builds the full name set and tests membership uniformly, is discretion — the single edge-scope predicate must remain the one definition of cascadable either way.
- **`fields=` helper return type** (set vs. frozenset vs. tuple of validated names) and the exact `ConfigurationError` message wording (so long as it names the offending entry, the model, and the cascadable set per Decision 9).
- **Multi-DB test gating mechanism** (`skipif` on the env var vs. on `"shard_b" in settings.DATABASES`) — mirror the `tests/optimizer/test_multi_db.py` family.

These are NOT discretion (architecturally fixed by the spec): the `Q(__in) | Q(__isnull)` shape, `_default_manager` (not `.objects`), `queryset.db` (not `_db`), unevaluated subquery (no `list(...)`), `has_custom_get_queryset()` skip gate, `registry.get` primary lookup, the `isinstance(fields, str)` guard-first ordering, and the single-sync-walk-wrapped-in-`sync_to_async` async shape.

### Spec slice checklist (verbatim)

- [x] `permissions.py` ships `apply_cascade_permissions(cls, queryset, info, fields=None)`: a call-time walk of `cls`'s model single-column forward relations (`field.related_model` present AND `hasattr(field, "column")` AND NOT `getattr(field.remote_field, "parent_link", False)` — the upstream scope test plus the MTI parent-link exclusion; excludes M2M, reverse FK, reverse OneToOne, `GenericForeignKey`, `GenericRelation`, and the MTI `<parent>_ptr` edge precisely), resolving each edge's target type via the registry primary lookup ([`registry.py::TypeRegistry.get`][registry]), skipping targets without a custom hook (`has_custom_get_queryset()` is `False` — the identity default adds nothing), and intersecting `Q(<field>__in=<target visible pks>) | Q(<field>__isnull=True)` into the caller's queryset with the target subquery pinned to `queryset.db` ([Decision 8](#decision-8--multi-db-pinning-usingquerysetdb--the-resolved-alias-not-_db)).
- [x] Cycle detection via a module-level `ContextVar` seen-set (the upstream `_cascade_seen` shape verbatim): re-entry on a type already in the set returns the partially-narrowed queryset without raising; the root call resets the var in a `finally` so request isolation holds under both WSGI and ASGI.
- [x] `fields=` validation: a bare string is rejected up front by an `isinstance(fields, str)` guard (so `fields="item"` fails loudly instead of validating its characters), and unknown names and known-but-non-cascadable names (M2M, reverse relations, virtual fields) raise [`ConfigurationError`][glossary-configurationerror] naming the field, the model, and the cascadable set ([Decision 9](#decision-9--fields-scoping-validates-loudly-with-configurationerror)).
- [x] Sync misuse contract: a target hook returning a coroutine during the sync walk closes the coroutine and raises [`SyncMisuseError`][glossary-syncmisuseerror], reusing the probe shape of [`utils/querysets.py::apply_type_visibility_sync`][querysets] ([Decision 10](#decision-10--syncasync-contract-syncmisuseerror-on-async-hooks-from-the-sync-walk-the-async-variant-wraps-the-walk-in-sync_to_async)).
- [x] `aapply_cascade_permissions(cls, queryset, info, fields=None)` wraps the sync walk in `sync_to_async(thread_sensitive=True)` (the [`filters/sets.py`][filters-sets] precedent) so blocking consumer-hook work (e.g. `user.has_perm(...)`'s permission-table reads) stays off the event loop ([Decision 10](#decision-10--syncasync-contract-syncmisuseerror-on-async-hooks-from-the-sync-walk-the-async-variant-wraps-the-walk-in-sync_to_async)).
- [x] Both symbols export from the package root (`from django_strawberry_framework import apply_cascade_permissions` — the card DoD's import line) and join `__all__`; the public-exports pin in [`tests/base/test_init.py`][test-base-init] grows accordingly (the version pin in the same file is untouched, [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-0010-cut)).
- [x] Package coverage: new `tests/test_permissions.py` per the [Test plan](#test-plan) — including the card's four dedicated upstream-invariant pins (cycle guard; single-column scope; alias pinning; nullable-FK preservation).

### Notes for Worker 1 (spec reconciliation)

Recorded during planning; resolved here or carried to final verification (no spec edit made in the planning pass per the dispatch).

1. **`SyncMisuseError` message wording vs. reuse (resolved in plan; no spec edit needed).** Decision 10 (spec line 60/315) instructs the cascade to *reuse the probe shape of* `apply_type_visibility_sync`, AND describes a `SyncMisuseError` "with a message naming the target type and the two recourses (`aapply_cascade_permissions`, or a sync hook rewrite)". The reused helper's current message (`utils/querysets.py:112-118`) names the target type but points at "the Relay node defaults" and "an async resolver / sync `get_queryset` rewrite" — accurate-but-generic, NOT cascade-specific. Two readings: (a) reuse the helper verbatim (message says "Relay node defaults"), maximally DRY but a slightly-misleading message on the cascade path; (b) `permissions.py` runs its own probe with a cascade-specific message, costing a second `iscoroutine`/close site. **Plan resolution: prefer (a) — reuse `apply_type_visibility_sync`** (the explicit Decision 10 DRY instruction and the data-leak-routing rule in the `utils/querysets.py` docstring outweigh message specificity; the message still names the offending target type and the sync-rewrite recourse). The test `test_sync_helper_raises_syncmisuseerror_on_async_target_hook` therefore pins the *type name + SyncMisuseError + coroutine-closed* and does NOT pin the literal "Relay node defaults" / cascade-recourse wording. **If Worker 3 or final verification judges the generic message materially misleading on the cascade surface**, the higher-quality fix is to generalize the helper's message in `utils/querysets.py` to not hardcode "Relay node defaults" (it now serves three surfaces) — a spec-adjacent refinement Worker 1 can authorize at final verification (it would touch shared source, so it must route through a Worker 2 pass, not a planning-pass edit). Flagged, not actioned.

2. **`review_inspect.py` helper — not required this pass (recorded skip).** Per BUILD.md "When to run the helper during build", Worker 1 must run it when the plan adds logic to an *existing* `.py` file ≥150 source lines, or to any file under `optimizer/` or `types/`. Slice 1 adds a *new* module (`permissions.py` — Worker 3 runs the helper on new files at review), uncomments a staged seam in `__init__.py` (no new logic, ~62 lines), and edits two test files. No existing ≥150-line logic file and nothing under `optimizer/`/`types/` is touched. **Helper skipped for the planning pass with this recorded reason.** Worker 3 must run it on the new `permissions.py` at review (it carries review-worthy logic: the walk, the cycle guard, the validation).

3. **Spec status/header re-verification (lines 1-5).** Read at this spawn. The status line (line 5) reads "planned — no slice has started"; accurate as of this planning pass (Slice 1 not yet built). The on-disk `__version__` is `0.0.9` (`__init__.py:42`), matching the spec's line-3 assertion that the `0.0.9` cut has landed and `0.0.10` is the joint cut's job. **No header edit needed at this pass.** Re-check at final verification: once Slice 1 builds, the status line still says "no slice has started" — Worker 1's final-verification pass for Slice 1 should update it to reflect that Slice 1 has shipped (per worker-1.md "Spec status-line re-verification"). Carried forward, not edited now (planning pass writes only the artifact).

4. **No spec-vs-codebase gap found.** Every symbol the slice names exists: `registry.get` (registry.py:221), `DjangoType.has_custom_get_queryset` (types/base.py:668) + `get_queryset` default (:653), `apply_type_visibility_sync` / `SyncMisuseError` (utils/querysets.py:93/35), `ConfigurationError` (exceptions.py:20), the `sync_to_async(thread_sensitive=True)` precedent (filters/sets.py:1745), the staged `__init__.py` export seam (:32-40) and `__all__` TODO (:45-47), the `test_init.py` exports-pin TODO (:35-39), the products `Entry → Item/Property → Category` graph + `is_private` (products models.py:44-142), and the `FAKESHOP_SHARDED` `shard_b` alias gate (settings.py:116) + `tests/optimizer/test_multi_db.py` harness. The four products cascade hooks are commented and correctly marked `TODO-ALPHA-034-0.0.10` (schema.py:70-182) — they are Slice 4's to uncomment, NOT Slice 1's.

<!-- LINK DEFINITIONS -->
<!-- Root -->
<!-- docs/ -->
[querysets]: ../../django_strawberry_framework/utils/querysets.py
[registry]: ../../django_strawberry_framework/registry.py
[filters-sets]: ../../django_strawberry_framework/filters/sets.py
[glossary-configurationerror]: ../../docs/GLOSSARY.md
[glossary-syncmisuseerror]: ../../docs/GLOSSARY.md
[test-base-init]: ../../tests/base/test_init.py
<!-- docs/SPECS/ -->
<!-- docs/builder/ -->
<!-- django_strawberry_framework/ -->
<!-- tests/ -->
<!-- examples/ -->
<!-- scripts/ -->
<!-- .venv/ -->
<!-- External -->

## Build report (Worker 2)

This is the **recovery completion of the first build pass** (a transient socket error killed the prior run after its code edits landed but before this report). It is the same first pass — no "pass 2" label. The prior pass's edits were on disk (a parsing, stub-marker-free `permissions.py`, the `__init__.py` exports seam, the grown `test_init.py` pin); this pass reviewed `permissions.py` line-by-line against the plan + Decisions 4/5/8/9/10 and the committed Slice-1 test subset, confirmed correctness, ran the validation gates, and wrote the deliverables. No production defect was found, so no code fix was required.

### Files touched

Grounded in `git status --short` (after both ruff runs; identical before and after — ruff introduced zero drift):

- `django_strawberry_framework/permissions.py` — **slice-intended (reviewed; no change this pass).** The prior pass filled the committed `NotImplementedError` seam (235 lines on disk). Reviewed line-by-line; satisfies every load-bearing contract item (see Implementation notes). No edit needed this pass.
- `django_strawberry_framework/__init__.py` — **slice-intended (reviewed; no change this pass).** The prior pass uncommented `from .permissions import (aapply_cascade_permissions, apply_cascade_permissions)`, added both names to `__all__` alphabetically (they sort as the first two entries before `"BigInt"` — verified), deleted the file-wide `# ruff: noqa: ERA001` seam directive, and removed both `TODO(spec-034 Slice 1)` comment blocks. Diff against HEAD confirms exactly the planned Step-8 change and nothing more. Correct and complete.
- `examples/fakeshop/apps/products/schema.py` — **concurrent out-of-scope; NOT mine; left untouched.** The only working-tree change here is a single em-dash→hyphen comment swap (`—`→`-`) inside the Slice 4 `TODO(spec-034 Slice 4)` block (verified via `git diff`: 1 insertion / 1 deletion, comment-only, byte-identical apart from the dash). This is the concurrent maintainer normalization sweep recorded in `build-034`'s "Concurrent-sweep update" section. Per the standing instruction, not reverted, not touched.

Not in the working-tree diff (committed; confirmed correct, no edit needed):

- `tests/base/test_init.py` — committed with the expected `__all__` tuple already grown by both members; verified mutually consistent with `__init__.py`'s `__all__` (identical 16-entry tuple, `"aapply_cascade_permissions"` then `"apply_cascade_permissions"` as entries 12-13; `test_version`/`__version__` untouched at `0.0.9` per Decision 13).
- `tests/test_permissions.py` — pre-committed scaffolding (see next section).

### Tests added or updated

No test files were edited this pass — both relevant test files are committed scaffolding.

- `tests/test_permissions.py` is **pre-committed scaffolding** (landed in `8c5fe2a7`). Its current state is a fully-`@pytest.mark.skip` staged-seam stub: every test is a skip-decorated, docstring-only stub naming its slice and contract, so the file collects cleanly and documents the whole permissions test plan as pending. The only Slice-1 contract it actually enforces today is the module-import header (`from django_strawberry_framework.permissions import SyncMisuseError, aapply_cascade_permissions, apply_cascade_permissions`) — which import-collects iff `permissions.py` parses and exposes all three names. I reasoned through the Slice-1 subset (the four upstream-invariant pins + scope/fields/sync-misuse/async/self-ref pins) against the reviewed code and confirmed `permissions.py` satisfies each (reasoning recorded in Implementation notes); I could not run pytest per the dispatch. **I did not rewrite this file** (per the dispatch). The stubs are filled + un-skipped in the slice that owns each pin; the bulk of Slice 1's assertion-bearing pins are not yet present as live tests — this is the committed scaffolding's design, not a Worker 2 deferral, and is recorded for Worker 1/Worker 3.
- `tests/base/test_init.py` exports pin (`test_public_api_surface_is_pinned`) is committed and already lists both new members; it matches `__init__.py`'s `__all__` exactly. No edit needed.

### Validation run

- `uv run ruff format .` → exit 0, "267 files left unchanged" (the COM812 formatter-conflict line is a pre-existing config advisory, not a change).
- `uv run ruff check --fix .` → exit 0, "All checks passed!" (zero autofixes applied).
- `git status --short` (after both ruff runs, byte-identical to before): `M django_strawberry_framework/__init__.py`, `M django_strawberry_framework/permissions.py`, `M examples/fakeshop/apps/products/schema.py`, `?? docs/builder/bld-slice-1-cascade_foundation.md`, `?? docs/builder/build-034-permissions-0_0_10.md`.
- **Classification.** `__init__.py` + `permissions.py` = slice-intended. `examples/fakeshop/apps/products/schema.py` = concurrent out-of-scope (em-dash sweep) — **explicitly confirmed left untouched**, not mine, not reverted. The two `??` files are build artifacts (this slice artifact + the build plan). **Ruff caused zero drift** (status identical pre/post), so nothing to revert. No pytest run (dispatch forbids it).

### Implementation notes

Design choices in the reviewed code that the plan left to discretion or did not explicitly pin (deltas only):

- **Public-function-holds-the-guard factoring (discretion item resolved).** `apply_cascade_permissions` holds the cycle-guard lifecycle (root install + `try/finally` reset / re-entry break / nested add + `try/finally` discard) and delegates per-edge composition to a private `_walk(model, queryset, info, names_to_walk)`. There is exactly ONE walk implementation; `aapply_cascade_permissions` wraps the *public* `apply_cascade_permissions` via `sync_to_async(thread_sensitive=True)`, so the `ContextVar` install/reset runs inside the asgiref-copied worker-thread context (Decision 10 / spec line 316/390). This is the plan's stated "cleaner shape."
- **`_validate_fields` returns `set | None`, not frozenset/tuple (discretion item).** `None` is the "walk every cascadable edge" sentinel; a plain `set` is the validated edge-name set; `set()` (from `fields=[]`) is the defined no-op. `_walk` keys the membership test on `names_to_walk is not None` so `None` skips the test (full walk) and an empty set walks nothing — the `fields=[]` vs `fields=None` distinction (spec line 407) falls out for free.
- **Edge predicate split into two private helpers.** `_is_cascadable_edge(field)` is the single boolean predicate (the DRY hinge); `_cascadable_edge_names(model)` wraps it into the name-set used by both `_validate_fields` and the conceptual full walk, so scope cannot drift between validation and walk. Readable single-responsibility split, no behavior beyond the plan.
- **`SyncMisuseError` redundant-alias re-export (small drift; not in the plan's import list).** `permissions.py:57` does `from .utils.querysets import SyncMisuseError as SyncMisuseError` — the established `types/relay.py:41` convention (verified identical form). This is **required** for the committed `tests/test_permissions.py:24-28` import to resolve, and the plan's import list (Implementation step 1) did not enumerate it. It adds no new package-root public name (`SyncMisuseError` is already in `__all__` via `types`) and the `X as X` form is ruff-recognized as an intentional re-export (no `# noqa: F401` needed). Recorded here per the small-drift rule; also flagged to Worker 1 below.

Correctness review against the load-bearing contract (all satisfied, no fix needed):

- Scope predicate `related_model is not None AND hasattr(field, "column") AND not getattr(field.remote_field, "parent_link", False)` — matches Decision 5 step 1 incl. the MTI `parent_link` exclusion verbatim.
- `registry.get(field.related_model)` primary lookup, skip on `None`; `has_custom_get_queryset()` gate skip; `Q(<fk>__in=target_qs) | Q(<fk>__isnull=True)`; `field.related_model._default_manager.using(queryset.db).all()` (resolved alias, not `_db` — Decision 8); `apply_type_visibility_sync` reused as the single sync-misuse probe (Decision 10); `aapply` = `sync_to_async(thread_sensitive=True)` wrap of the single sync walk.
- Cycle-guard lifecycle traced for root / re-entry / nested-sibling / self-referential / mutual-A↔B cases: terminates in every case, partial-narrows on cycle (never raises), `finally`-resets the var on the root frame including on exception, frame-exit-discards each class so sibling edges to the same target both cascade. The shared seen-set object is mutated in place by nested frames (they read the same `ContextVar` value, not a new set) — correct.
- `fields=[]` → `_validate_fields` returns `set()` → `_walk` skips every edge (no-op); `fields=None` → returns `None` → walks all. `isinstance(fields, str)` guard fires before any per-name lookup, message names the non-string-iterable requirement and the bracket fix (Decision 9). No stub markers, no `NotImplementedError`, no `TODO(spec-034 Slice 1)` left in `permissions.py`.

### Notes for Worker 3

- **No `scripts/review_inspect.py` shadow file was used** in this review — `permissions.py` is 249 lines and was reviewed directly. Per the plan's "Notes for Worker 1" item 2, Worker 3 owns running the helper on the new `permissions.py` at review (it carries review-worthy logic: the walk, the cycle guard, the validation). Run with `--output-dir docs/shadow` and cite original source line numbers.
- The committed `tests/test_permissions.py` is all-skip scaffolding; the live assertion-bearing Slice-1 pins are NOT yet present (only the import-collect header enforces anything today). When scoping the diff, the `examples/fakeshop/apps/products/schema.py` working-tree change is the concurrent em-dash comment swap, not a Worker 2 edit — treat it as pre-existing concurrent churn per `build-034` line 30.
- `multi_db` pin is `FAKESHOP_SHARDED`-gated and will not run under a bare `uv run pytest` (and it is currently a skip-stub anyway); if/when it is filled, exercise it with `FAKESHOP_SHARDED=1 uv run pytest tests/test_permissions.py -k multi_db --no-cov` (no `--cov*` flags).

### Notes for Worker 1 (spec reconciliation)

1. **The spec's "Current state: No `permissions.py` exists" (spec line 90) is STALE.** Scaffolding was pre-committed by the maintainer in `8c5fe2a7` ("spec-034 - Add TODO comments"): a `permissions.py` (committed as a seam, since filled to 249 lines), the `__init__.py` export seam, the grown `tests/base/test_init.py` pin, and an all-skip `tests/test_permissions.py` stub. As of this pass, `permissions.py` parses, exposes all three names, and carries no stub markers. The spec's Current-state and the slice-checklist "Boxes are unticked because the work has not started" framing predate the scaffolding commit. Carried to final verification (I do not edit the spec per dispatch); the planning artifact's "Notes for Worker 1" item 3 already flags that the spec status line needs updating once Slice 1 ships — this is now the case.
2. **`SyncMisuseError` re-export drift (small, mechanically obvious).** As noted in Implementation notes, `permissions.py:57` re-exports `SyncMisuseError` (the `relay.py:41` redundant-alias convention) — not enumerated in the plan's Implementation-step-1 import list, but required for the committed `tests/test_permissions.py` import header to resolve, and consistent with the plan's DRY-analysis note (which mentions `SyncMisuseError` is "re-exported via `types` and the package root … reused as-is by reusing `apply_type_visibility_sync`"). It adds no new public package-root name. Keep or fold into the plan's import list at final verification.
3. **`SyncMisuseError` cascade-message-wording tension is unresolved-by-design (planning Notes item 1).** The reused `apply_type_visibility_sync` message names "the Relay node defaults" / a sync-`get_queryset`-rewrite recourse — accurate-but-generic on the cascade path; it does NOT name `aapply_cascade_permissions` as a recourse. The plan resolved this in favor of reuse (option (a)), and the committed `test_sync_helper_raises_syncmisuseerror_on_async_target_hook` is still a skip-stub so it pins nothing today. If final verification judges the generic message materially misleading on the cascade surface, the higher-quality fix (generalize the helper's message in `utils/querysets.py`) touches shared source and must route through a Worker 2 pass, not a planning edit. Flagged, not actioned.

---

## Build report (Worker 2, continued — Slice 1 tests)

This is the **same Slice-1 build pass, continued**: the prior continuation (above) filled `permissions.py` + the exports but — under a dispatch constraint that wrongly told it not to touch `tests/test_permissions.py` — left that file as all-`@pytest.mark.skip` scaffolding, so the Slice-1 test deliverable (the four upstream-invariant pins + the rest of the Slice-1 contract) was NOT met. This pass **implements the Slice-1 test bodies**. No production change was needed (the reviewed `permissions.py` is correct; the tests exercised every Slice-1 contract item and exposed no defect). Not a re-pass after a Worker 3 review (no review has run yet) — hence the "continued" label, not "pass 2". Status stays `built`.

### Files touched

Grounded in `git status --short` after both ruff runs + the trailing-comma fixer:

- `tests/test_permissions.py` — **slice-intended (the deliverable of this pass).** Removed the `@pytest.mark.skip` decorator from every `TODO(spec-034 Slice 1)` test and implemented its body to assert exactly what its docstring specified; left the `TODO(spec-034 Slice 2)` and `TODO(spec-034 Slice 3)` stubs skipped (those land in their own slices). Added the local fixture machinery (registry-isolation autouse fixture; a `_cascade_seen`-clean autouse teardown assertion; a `_tables(...)` schema-editor context manager; a `_make_type(...)` `DjangoType`-factory helper).
- `django_strawberry_framework/permissions.py` — **NOT changed this pass.** The 400-line working-tree diff vs HEAD is the prior pass's fill of the committed seam, left intact. No test exposed a defect, so no fix was made (the dispatch's "do not change unless a test exposes a real defect" rule).
- `django_strawberry_framework/__init__.py` — **NOT changed this pass.** The prior pass's exports seam, unchanged.
- `examples/fakeshop/apps/products/schema.py` — **concurrent out-of-scope; NOT mine.** The single-line em-dash→hyphen comment swap from the concurrent normalization sweep (`build-034` "Concurrent-sweep update"). Not reverted, not touched.

### Tests added or updated

All in `tests/test_permissions.py`. The four dedicated upstream-invariant pins:

- `test_cycle_guard_contextvar_breaks_mutual_cascade` — synthetic A↔B `managed=False` graph (real tables), both hooks cascade into each other; asserts the walk terminates, B's direct narrowing reaches A's rows, `_cascade_seen` is `None` after the root returns AND after a root whose **walk body** raises (a target hook raises — the root's own hook is never auto-invoked, so the exception must come from a reached target). Registry cleared between the two `with _tables(...)` blocks to avoid a primary-collision on the re-registration.
- `test_single_column_scope_skips_m2m_reverse_and_generic` — one synthetic model carrying forward FK, forward O2O, M2M, GFK (+ its backing `content_type` FK), GenericRelation, reverse FK, reverse O2O. Asserts `_cascadable_edge_names` == `{"fk", "o2o", "content_type"}` (the GFK's backing FK is itself an ordinary single-column forward FK and legitimately cascadable — documented inline) and per-edge `_is_cascadable_edge` for each kind. Construction-only (no table).
- `test_mti_parent_link_edge_excluded` — synthetic MTI `MtiChild(MtiParent)`; asserts the `mtiparent_ptr` parent-link DOES carry both predicates yet `_is_cascadable_edge(ptr) is False` and is absent from `_cascadable_edge_names`. Construction-only.
- `test_multi_db_subquery_pinned_to_caller_alias` — `FAKESHOP_SHARDED`-gated (`skipif` on the env var) + `@pytest.mark.django_db(databases=["default", "shard_b"])`; a `.using("shard_b")` caller → `result.db == "shard_b"`, a composed `IN (SELECT` subquery, and the walk's `related_model._default_manager.using(result.db).all().db == "shard_b"` (the load-bearing `queryset.db` pin). Not runnable under bare `uv run pytest`.
- `test_nullable_fk_rows_preserved` — synthetic nullable-FK graph (fakeshop FKs are all non-nullable); a target hook hiding everything drops the non-null-FK row and keeps the NULL-FK row (the `__isnull=True` disjunct).

The rest of the Slice-1 contract:

- `test_cascade_excludes_rows_with_hidden_targets` / `test_hidden_and_missing_targets_indistinguishable` — hidden-target row absent; hidden-target and no-target rows equally absent (no existence leak).
- `test_transitive_cascade_two_deep` — real products `Entry → Item → Category` with synthetic cascading `DjangoType` hooks; hiding a `Category` drops the `Entry` two edges away.
- `test_identity_hook_targets_skipped_no_sql` / `test_unregistered_target_model_skipped` — `str(result.query)` carries no `IN (SELECT` and equals `str(Entry.objects.all().query)` (the identity-hook skip / unregistered-target skip).
- `test_secondary_type_never_cascade_target` — primary (identity) + stricter secondary on Category; `Item → Category` resolves the **primary**, so no narrowing.
- `test_secondary_type_as_root_reaches_primary_on_transitive_revisit` — self-ref synthetic graph; a cascade rooted on the secondary re-reaches its model via `registry.get` → the primary, narrows by the primary hook, terminates.
- `test_cascade_target_sliced_or_values_queryset_is_consumer_bug` — a target hook returning multi-column `.values("id", "name")`; the `ValueError` ("the 'in' lookup must have 1 selected field") propagates on evaluation (the helper does not defensively rewrite).
- `test_fields_scopes_walk` — `fields=["item"]` cascades only `item`; a row hidden only via `property` survives.
- `test_fields_unknown_name_raises` / `test_fields_non_cascadable_name_raises` — `ConfigurationError` naming the offending entry, the model, and the cascadable set (all three asserted).
- `test_fields_valid_but_hookless_name_accepted` — `fields=["item"]` against an identity-hook Item validates clean, composes no subquery.
- `test_fields_bare_string_raises` — `fields="item"` raises; message names the non-string-iterable requirement + the `['item']` bracket fix and does NOT surface a per-character `'i'` lookup.
- `test_fields_empty_list_cascades_nothing` — `fields=[]` composes no subquery (defined no-op), distinct from `fields=None` which DOES cascade.
- `test_sync_helper_raises_syncmisuseerror_on_async_target_hook` — async target hook from the sync walk raises `SyncMisuseError` naming the target type; the suite's `filterwarnings = error` policy makes a leaked-coroutine `RuntimeWarning` a hard error, so the closed-coroutine property is enforced by construction (no `recwarn`).
- `test_aapply_runs_walk_off_event_loop` — async test; `aapply` runs the walk, composes `IN (SELECT`, and `_cascade_seen.get()` stays `None` in the awaiting task (asgiref copies the context into the worker thread).
- `test_aapply_async_target_hook_still_raises` — async target hook still raises `SyncMisuseError` via the async variant.
- `test_self_referential_fk_cascades_once` — `parent = FK("self")`; the seen-set breaks the self-edge at depth 1, the direct narrowing still applies, the walk terminates.

Exports pin (`tests/base/test_init.py::test_public_api_surface_is_pinned`) was already committed with both members and is unchanged this pass.

### Fixture approach (synthetic graphs + multi-DB)

- **Synthetic models needing real rows** (A↔B cycle, nullable-FK, hidden-target, self-ref, secondary-as-root, cascade-target-contract) are declared as `managed = False` models under the **installed `products`** app label (so Django wires reverse relations into `_meta.get_fields()`) and given real tables via a `_tables(*models)` context manager wrapping `connection.schema_editor().create_model/delete_model` — the `tests/test_relay_connection.py` / `tests/optimizer/test_relay_id_projection.py` pattern.
- **Construction-only pins** (single-column scope, MTI, identity-hook, unregistered-target, multi-DB) assert on the *composed* query (`str(qs.query)` / `qs.db`) and need no table.
- **`_make_type`** declares a `DjangoType` with `fields=("id",)` by default — a scalar-only selected surface so `finalize_django_types()` never has to resolve a relation field to a (possibly-unregistered) target type, while the cascade still walks the model's `_meta.get_fields()` edges (the "Meta.fields-excluded FK edges still cascade" edge case is what makes this sound).
- **Transitive 2-deep** reuses the real products `Entry → Item/Property → Category` chain with synthetic cascading hooks (the products schema hooks are Slice 4's to uncomment).
- **Multi-DB** builds on the `tests/optimizer/test_multi_db.py` in-test pattern, gated `skipif os.environ.get("FAKESHOP_SHARDED") != "1"` + `@pytest.mark.django_db(databases=["default", "shard_b"])`.

### Validation run

- `uv run ruff format .` → exit 0, "267 files left unchanged".
- `uv run ruff check --fix .` → exit 0, "All checks passed!" (one in-file `C416` was auto-fixed during iteration before the final run).
- `uv run python scripts/check_trailing_commas.py` → reformatted `tests/test_permissions.py` once (expanded `_make_type`'s 6-param signature one-per-line per the ≥4 threshold rule); re-run is clean.
- `uv run ruff format --check tests/test_permissions.py` + `uv run ruff check tests/test_permissions.py` → both clean; `python -m py_compile` → OK.
- `git status --short` (final): `M django_strawberry_framework/__init__.py`, `M django_strawberry_framework/permissions.py`, `M examples/fakeshop/apps/products/schema.py`, `M tests/test_permissions.py`, plus the two `??` build artifacts.
- **Classification.** `tests/test_permissions.py` = slice-intended (this pass's deliverable). `__init__.py` + `permissions.py` = prior-pass slice-intended fill, unchanged this pass. `examples/fakeshop/apps/products/schema.py` = concurrent out-of-scope (em-dash sweep), left untouched. The two `??` files are build artifacts. **Ruff + the trailing-comma fixer touched only `tests/test_permissions.py` and the touch was the trailing-comma layout my own edit triggered** — owned, not drift to revert. No pytest run (dispatch forbids it; Worker 3 runs focused tests).

### Implementation notes

Deltas the plan / prior report did not pin:

- **Two autouse fixtures, not one.** `_isolate_registry` (the `test_base.py` shape) plus `_assert_contextvar_clean` (teardown asserts `_cascade_seen.get() is None`) — the latter turns a leaked seen-set into a hard per-test failure rather than a cross-test flake, mirroring the request-isolation property the production `finally` guarantees. For sync tests it genuinely verifies the reset; for async tests it is weaker (teardown runs in a different context) but never a false failure, and those tests carry their own in-body `_cascade_seen` assertion.
- **`finally`-reset-on-exception pin uses a raising TARGET hook, not a raising root.** The root's own `get_queryset` is never auto-invoked by `apply_cascade_permissions` (a consumer calls the cascade from inside it). To make the **walk body** raise inside the root's `try`, a reached target type's hook raises; the registry is cleared between the two `_tables` blocks so the fresh primary registrations don't collide with the first block's `CycleAType`/`CycleBType`.
- **`_make_type(fields=("id",))`.** Scalar-only selected surface so finalization never resolves a relation to a possibly-unregistered target — sound precisely because the cascade walks `_meta.get_fields()`, not the type's selected fields.
- **The all-relation-kinds scope model includes a backing `content_type` FK** (the GFK requires it), which is itself cascadable; the expected `_cascadable_edge_names` is therefore `{"fk", "o2o", "content_type"}`, documented inline so the inclusion does not read as a scope leak.
- **Multi-DB assertion pins `queryset.db` propagation** (`related_model._default_manager.using(result.db).all().db == "shard_b"`) + the presence of `IN (SELECT`, rather than introspecting `query.where.children` (fragile, and tripped `C416`).
- **Sync-misuse test drops `recwarn`** — `filterwarnings = error` (pytest.ini) already makes an unclosed-coroutine `RuntimeWarning` a hard error, so the closed-coroutine property is enforced by construction; the test pins the type-name + `SyncMisuseError` (not the literal recourse phrasing — see Notes for Worker 1 item 3 above).

### Notes for Worker 3

- Run `scripts/review_inspect.py` on the new `permissions.py` at review (the planning artifact's Notes-for-Worker-1 item 2 assigns this to you; it carries the walk / cycle-guard / validation logic). Cite original source line numbers.
- The `multi_db` pin is `FAKESHOP_SHARDED`-gated and will NOT run under a bare `uv run pytest` (it `skipif`s out). To exercise the alias path: `FAKESHOP_SHARDED=1 uv run pytest tests/test_permissions.py -k multi_db --no-cov` (no `--cov*` flags). All other Slice-1 pins run under the default invocation.
- Several synthetic models are `managed = False` under the **`products`** app label and get/drop real tables via `_tables(...)` (schema-editor). If you run the suite, these create/drop tables inside each test — there is no migration for them. This is the established `tests/test_relay_connection.py` pattern.
- The `examples/fakeshop/apps/products/schema.py` working-tree change is the concurrent em-dash comment swap (`build-034` line 30), not a Worker 2 edit — scope findings to `tests/test_permissions.py`.
- Per the dispatch, `permissions.py` was treated as correct-and-frozen; I verified each Slice-1 contract item against it while writing the tests and found no defect, so I made no production change. If a focused run surfaces a real `permissions.py` defect, the root-cause fix belongs in `permissions.py` (not a test workaround) and routes through a Worker 2 re-pass.

### Notes for Worker 1 (spec reconciliation)

- No new spec-vs-codebase gap surfaced while writing the tests beyond the three items already recorded above (stale "No `permissions.py` exists" Current-state line; the `SyncMisuseError` redundant-alias re-export; the cascade-message-wording tension). The test `test_sync_helper_raises_syncmisuseerror_on_async_target_hook` pins the **target type name + `SyncMisuseError` + (by the `-W error` policy) the closed coroutine** and deliberately does NOT pin the literal "Relay node defaults" / cascade-recourse wording — consistent with the plan's option-(a) resolution. If final verification decides the generic message is materially misleading on the cascade surface, generalizing `utils/querysets.py`'s message (shared source) and tightening this test's assertion would be the higher-quality fix, routed through a Worker 2 pass.

---

## Review (Worker 3)

Static helper run: `python scripts/review_inspect.py django_strawberry_framework/permissions.py --output-dir docs/shadow` — wrote `docs/shadow/django_strawberry_framework__permissions.overview.md` + `.stripped.py`. Walked its Django/ORM markers, the one control-flow hotspot (`apply_cascade_permissions`, 4 branches — the cycle-guard lifecycle), the calls-of-interest (`getattr`/`hasattr`/`isinstance`/`_meta.get_fields`/`has_custom_get_queryset`), and the repeated-string-literals section (zero repeats). Shadow line numbers are not cited below; all citations are symbol-qualified against original source.

Focused test run (mandatory per the dispatch): `uv run pytest tests/test_permissions.py --no-cov -q` → **8 failed, 14 passed, 8 skipped**. This is the dominant finding. The 8 failures are NOT the `FAKESHOP_SHARDED`-gated multi-DB pin (that correctly `skipif`s out among the 8 skips); they are live Slice-1 failures introduced by this slice. They decompose into exactly two defects (one source, one tests), both High. Worker 2 could not run pytest (its dispatch forbade it) and reasoned the code correct by inspection, so the Django-6.0 attribute-shape change and the schema-editor transaction omission both slipped through.

### High:

**H1 — `_is_cascadable_edge` over-includes M2M and `GenericRelation` under Django 6.0 (security-relevant scope leak).**
- Source: `django_strawberry_framework/permissions.py::_is_cascadable_edge` (the `hasattr(field, "column")` predicate), feeding `permissions.py::_cascadable_edge_names`, `permissions.py::_walk`, and `permissions.py::_validate_fields`.
- Why it matters: the predicate is the spec's "two predicates ported from upstream" — `related_model present AND hasattr(field, "column")` (Decision 5 step 1, spec line 257). That `hasattr` test was written against an older Django where `ManyToManyField` / `GenericRelation` did not expose a `column` attribute. **In the pinned Django (6.0.5), both fields DO expose `.column` (value `None`)**, so `hasattr(field, "column")` returns `True` and both pass the predicate. I verified directly: for a synthetic `ScopeModel`, `m2m` (ManyToManyField) and `generics` (GenericRelation) both report `related_model present`, `hasattr column = True`, `parent_link = False` → the shipped `_is_cascadable_edge` returns `True` for both. Consequence: `_cascadable_edge_names(ScopeModel)` returns `{"fk","o2o","content_type","m2m","generics"}` instead of `{"fk","o2o","content_type"}`. The walk would then attempt `Q(m2m__in=target_qs) | Q(m2m__isnull=True)` for an M2M edge — a wrong-shape constraint on a join-table relation — and similarly for a reverse `GenericRelation`. On a security surface (row visibility), silently cascading the wrong relation kinds is exactly the class of bug the spec's explicit scope enumeration exists to prevent (spec lines 395-396, 418).
- This is what `test_single_column_scope_skips_m2m_reverse_and_generic` (`tests/test_permissions.py:297`) catches: `assert names == {"fk","o2o","content_type"}` fails with `m2m` and `generics` as extra items. **The test is written correctly against the contract; the source predicate is wrong.**
- Recommended change: tighten the second predicate from `hasattr(field, "column")` to `getattr(field, "column", None) is not None` in `_is_cascadable_edge` (equivalently `getattr(field, "concrete", False)`). Verified via a temp probe: the `column is not None` form returns `{"fk","o2o","content_type"}` for the scope model and still excludes the MTI `<parent>_ptr` (it stays excluded by the `parent_link` guard), so the MTI pin and all forward FK/O2O behavior are preserved. Update the module docstring + `_is_cascadable_edge` docstring, which currently describe the `hasattr column` shape and assert M2M/`GenericRelation` are "excluded by construction" (no longer true on Django 6.0). Worker 1 may wish to record a spec note: the spec's verbatim `hasattr(field, "column")` ported text (spec line 257 / checklist line 122) is Django-version-fragile and should read `field.column is not None` (or `field.concrete`).
- Test expectation: `test_single_column_scope_skips_m2m_reverse_and_generic` must pass (it already asserts the correct set + per-edge predicate truth values, including `_is_cascadable_edge(m2m) is False` and `_is_cascadable_edge(generics) is False` at `tests/test_permissions.py:304,306`). No new test needed — the existing pin is exactly right and currently red.

**H2 — every `_tables`-using test omits `@pytest.mark.django_db(transaction=True)`; SQLite schema editor raises `NotSupportedError` (test-harness defect).**
- Source: `tests/test_permissions.py` — the `_tables(...)` schema-editor context manager (`tests/test_permissions.py:86-102`) and its 7 callers: `test_cycle_guard_contextvar_breaks_mutual_cascade` (`:136`, which has **no** `@pytest.mark.django_db` marker at all yet calls `_tables` at `:161`/`:207`), `test_nullable_fk_rows_preserved` (`:402`, `@pytest.mark.django_db`), `test_cascade_excludes_rows_with_hidden_targets` (`:450`), `test_hidden_and_missing_targets_indistinguishable` (`:487`), `test_secondary_type_as_root_reaches_primary_on_transitive_revisit` (`:637`), `test_cascade_target_sliced_or_values_queryset_is_consumer_bug` (`:704`), `test_self_referential_fk_cascades_once` (`:961`).
- Why it matters: all 7 fail with `django.db.utils.NotSupportedError: SQLite schema editor cannot be used while foreign key constraint checks are enabled. Make sure to disable them before entering a transaction.atomic() context...`. Under plain `@pytest.mark.django_db`, pytest-django wraps each test in an atomic transaction; SQLite cannot run `schema_editor()` create/delete inside one with FK checks on. The artifact itself cites the precedent (`tests/test_relay_connection.py`) for this `managed=False` + schema-editor pattern — and that precedent uses **`@pytest.mark.django_db(transaction=True)`** (`tests/test_relay_connection.py:184`), which the new tests dropped. So these are real test defects, not environment quirks: under the established pattern the tests would be green.
- I verified at HEAD that `permissions.py` is a `NotImplementedError` staged seam and `tests/test_permissions.py` is fully skip-decorated (31 skip markers = every test), so these failures are slice-introduced, not pre-existing (no pristine-HEAD reproduction possible — the runnable forms did not exist at HEAD). I verified the fix with a temp probe: a `_tables`-using test under `@pytest.mark.django_db(transaction=True)` creates tables, inserts a null-FK row, and asserts cleanly.
- Recommended change: add `@pytest.mark.django_db(transaction=True)` to every `_tables`-using test (and add the marker to `test_cycle_guard_contextvar_breaks_mutual_cascade`, which currently has none). The construction-only pins (scope, MTI, identity-hook str-query, multi-DB) that do not call `_tables` do not need it. Worker 2 owns this (permanent-test edit).
- Test expectation: after the marker fix, all 7 must pass. Combined with H1, a clean `uv run pytest tests/test_permissions.py --no-cov -q` should read 22 passed / 1 skipped (the `FAKESHOP_SHARDED` multi-DB pin).

### Medium:

None. (Both root causes are High; no separate Medium-severity gap surfaced. The spec-line-257 `hasattr` fragility is folded into H1's Worker-1 note rather than raised separately.)

### Low:

None.

### DRY findings

- **Sync-misuse probe reuse — confirmed genuine.** `permissions.py::_walk` runs each target hook via `apply_type_visibility_sync(target_type, base, info)` (`permissions.py` #"target_qs = apply_type_visibility_sync(target_type, base, info)"). There is no local `inspect.iscoroutine`/`.close()`/`raise SyncMisuseError` site in `permissions.py` — confirmed by the helper's calls-of-interest list (no `inspect` import, no second probe) and by reading the source. This is the single biggest DRY lever in the slice (Decision 10) and it is honored: the package keeps ONE sync-misuse site.
- **Async-wrap reuse — confirmed genuine.** `aapply_cascade_permissions` is `await sync_to_async(apply_cascade_permissions, thread_sensitive=True)(...)` — it wraps the *public* sync function (so the `ContextVar` install/reset runs inside the asgiref-copied worker thread), with no second walk implementation. Matches the `filters/sets.py:1745` precedent.
- **Single edge-scope predicate — DRY hinge intact (but buggy, see H1).** `_is_cascadable_edge` is the one definition of "cascadable edge"; both `_cascadable_edge_names` (used by `_validate_fields`) and `_walk` key off it, so validation and walk cannot drift. The H1 fix is a one-line change to that single predicate, which is exactly why the DRY hinge matters — fix once, both surfaces correct.
- **`SyncMisuseError` redundant-alias re-export** (`permissions.py` #"from .utils.querysets import SyncMisuseError as SyncMisuseError") is the established `types/relay.py:41` convention, adds no new package-root public name (already in `__all__` via `types`), and is required for the committed test import. Not a DRY violation — it is the project's intentional-re-export idiom.
- No repeated string literals, no repeated error fragments, no near-copy helpers. The two `ConfigurationError` messages in `_validate_fields` are distinct (bare-string vs unknown-name) and each single-use.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py`: the change is exactly the planned Step-8 surface and nothing more — (a) the file-wide `# ruff: noqa: ERA001` seam directive removed; (b) the staged `from .permissions import (aapply_cascade_permissions, apply_cascade_permissions)` import seam uncommented (with `# noqa: E402`, matching the file's other deferred imports); (c) both `TODO(spec-034 Slice 1)` comment blocks removed; (d) `"aapply_cascade_permissions"` and `"apply_cascade_permissions"` added to `__all__` alphabetically (they sort after `"__version__"`, before `"auto"`). **`__version__ = "0.0.9"` is untouched** (Decision 13 — authorized: spec line 361 explicitly allows the two `__all__` members to grow in Slice 1 while the version constant stays cut-owned). The `tests/base/test_init.py` exports pin is committed (not in the working-tree diff) and consistent: `test_version` asserts `0.0.9` (`tests/base/test_init.py:11`), and both cascade symbols are in the expected `__all__` tuple (`:47-48`). Public surface is correct.

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md`.

### Documentation / release sanity

Not applicable; the diff touches no docs/release/KANBAN/archive surfaces. (`examples/fakeshop/apps/products/schema.py` carries a working-tree change, but it is the concurrent em-dash→hyphen comment sweep recorded in `build-034`'s "Concurrent-sweep update" section — explicitly out of scope for this slice and excluded from review per the dispatch.)

### What looks solid

- The cycle-guard lifecycle in `apply_cascade_permissions` is correct and readable: root (`seen is None`) installs `{cls}` + `try/finally` reset; re-entry (`cls in seen`) returns the queryset unchanged (partial narrow, never raises); nested (`else`) adds `cls` + `try/finally` discard. Frame-exit discard lets sibling edges to the same target both cascade. Traced for root / re-entry / self-ref / mutual-A↔B — terminates in every case, and the `_assert_contextvar_clean` autouse teardown (`tests/test_permissions.py:73-83`) pins the `finally`-reset property as a hard per-test failure.
- The 23 implemented Slice-1 bodies pin load-bearing properties, not mere observability: real SQL-shape assertions (`"IN (SELECT" in str(result.query)`, `str(result.query) == str(Entry.objects.all().query)` for the identity-hook/unregistered skips), absolute `==` on the cascadable edge-name set, per-edge `_is_cascadable_edge` truth values, `.db` propagation for the multi-DB pin, and a propagating `ValueError` for the multi-column `.values()` consumer-bug pin. The `fields=` validation pins assert all three required message substrings (field/model/cascadable set) and the bare-string guard's no-per-character-leak property.
- DRY reuse (sync-misuse probe + async wrap) is genuine, not re-implemented — the slice's central architectural requirement.
- `_validate_fields` returns `set | None` cleanly: `None` → full walk, `set()` (from `fields=[]`) → defined no-op, validated set → scoped walk. The `isinstance(fields, str)` guard fires before any per-name lookup.
- The 7 Slice 2/3 stubs remain correctly `@pytest.mark.skip` and are left untouched.
- The single H1 fix (one-line predicate) flows through the DRY hinge to correct both the walk and `fields=` validation simultaneously — the architecture localizes the fix.

### Temp test verification

Created `docs/builder/temp-tests/slice-1/test_probe.py` (gitignored), ran it green (3 passed), then **deleted it** (disposition: removed; its assertions are already covered by the existing permanent pins once the source/harness fixes land). It proved: (1) the shipped `_is_cascadable_edge` returns `True` for `m2m` and `generics` (H1 bug reproduced); (2) the `getattr(field, "column", None) is not None` form returns exactly `{"fk","o2o","content_type"}` (H1 fix verified); (3) a `_tables`-using test under `@pytest.mark.django_db(transaction=True)` runs the schema editor cleanly and inserts a null-FK row (H2 fix verified). No temp test needs promotion — `test_single_column_scope_skips_m2m_reverse_and_generic` (H1) and the 7 `_tables` tests (H2) are the permanent homes; they just need the source + marker fixes to go green.

### Notes for Worker 1 (spec reconciliation)

- **Spec scope-predicate text is Django-version-fragile (folded into H1, surfaced here for the spec record).** Decision 5 step 1 (spec line 257) and the verbatim checklist (artifact line 122) port the upstream `hasattr(field, "column")` predicate. Under the pinned Django 6.0.5, `ManyToManyField` and `GenericRelation` expose `.column` (value `None`), so `hasattr` no longer discriminates and the predicate over-includes them. The implementation fix is `field.column is not None`; the spec's "excluded by construction" claim for M2M/`GenericRelation` (spec lines 395-396) holds only under that corrected predicate. Recommend Worker 1 update the spec's predicate spelling at final verification so the contract and the Django version agree. (Not escalated as a blocker — the fix is mechanical and the test contract is already correct.)
- The three carry-forward items from Worker 2's "Notes for Worker 1" (stale "No `permissions.py` exists" Current-state line; `SyncMisuseError` redundant-alias re-export; the `SyncMisuseError` cascade-message-wording tension) are unchanged by this review and remain Worker 1's to weigh.

### Review outcome

`revision-needed`. Two High findings, both with verified reproductions and verified fixes:
- **H1** (source): `_is_cascadable_edge` must use `field.column is not None` instead of `hasattr(field, "column")` — Django 6.0 makes the `hasattr` form leak M2M/`GenericRelation` edges into the cascade. Worker 2 owns the `permissions.py` fix (+ docstring update).
- **H2** (tests): the 7 `_tables`-using tests need `@pytest.mark.django_db(transaction=True)` (and `test_cycle_guard_contextvar_breaks_mutual_cascade` needs a `django_db` marker), matching the `tests/test_relay_connection.py:184` precedent the artifact already cites. Worker 2 owns the permanent-test fix.

Both must land in a Worker 2 re-pass; after them, `uv run pytest tests/test_permissions.py --no-cov -q` is expected to read 22 passed / 1 skipped (the `FAKESHOP_SHARDED` multi-DB pin). No Low/Medium findings outstanding. DRY, public-surface, CHANGELOG, and documentation checks all clean.

---

## Build report (Worker 2, pass 2)

Apply-changes pass after Worker 3's `revision-needed` (2 High findings, both with verified fixes). Applied the exact root-cause fixes Worker 3 verified; no new behavior introduced. Did not run `pytest` (the dispatch forbids it; Worker 3 re-runs the focused suite on re-review).

### Files touched

Grounded in `git status --short` after both ruff runs (ruff introduced zero drift — status identical before/after):

- `django_strawberry_framework/permissions.py` — **slice-intended (H1 fix this pass).** Tightened `_is_cascadable_edge`'s second predicate from `hasattr(field, "column")` to `getattr(field, "column", None) is not None`. Updated the `_is_cascadable_edge` docstring and the module docstring's "the `related_model`-plus-`column` test" phrasing to describe the column-*value* test and to record why `hasattr` over-includes M2M/`GenericRelation` under Django 6.0 (their `.column` attribute exists with value `None`). No other change to this file this pass; the prior-pass fill of the committed seam is intact.
- `tests/test_permissions.py` — **slice-intended (H2 fix this pass).** Changed the marker on all 7 `_tables`-using tests from `@pytest.mark.django_db` to `@pytest.mark.django_db(transaction=True)`: `test_cycle_guard_contextvar_breaks_mutual_cascade` (`:135`), `test_nullable_fk_rows_preserved` (`:402`), `test_cascade_excludes_rows_with_hidden_targets` (`:450`), `test_hidden_and_missing_targets_indistinguishable` (`:487`), `test_secondary_type_as_root_reaches_primary_on_transitive_revisit` (`:637`), `test_cascade_target_sliced_or_values_queryset_is_consumer_bug` (`:704`), `test_self_referential_fk_cascades_once` (`:961`). No assertion was weakened — only the marker changed. (Worker 3's H2 text noted the cycle-guard test "has no `django_db` marker"; on-disk it carried a plain `@pytest.mark.django_db`, which is now `transaction=True` — same correct end-state either way.)

Not changed this pass (prior-pass slice-intended fill, left intact):

- `django_strawberry_framework/__init__.py` — the exports seam. Untouched this pass.

Concurrent out-of-scope (NOT mine, NOT reverted):

- `examples/fakeshop/apps/products/schema.py` — the single em-dash→hyphen comment swap from the concurrent normalization sweep (`build-034` "Concurrent-sweep update"). Left untouched; `git diff --stat` confirms 1 insertion / 1 deletion, comment-only.

### Validation run

- `uv run ruff format .` → exit 0, "267 files left unchanged" (the COM812 line is the pre-existing config advisory, not a change).
- `uv run ruff check --fix .` → exit 0, "All checks passed!" (zero autofixes applied).
- `git status --short` (after both ruff runs, byte-identical to before): `M django_strawberry_framework/__init__.py`, `M django_strawberry_framework/permissions.py`, `M examples/fakeshop/apps/products/schema.py`, `M tests/test_permissions.py`, plus the two `??` build artifacts (`bld-slice-1-cascade_foundation.md`, `build-034-permissions-0_0_10.md`).
- **Classification.** `permissions.py` + `tests/test_permissions.py` = slice-intended (the two High fixes this pass, on top of prior-pass fills). `__init__.py` = prior-pass slice-intended, unchanged this pass. `examples/fakeshop/apps/products/schema.py` = concurrent out-of-scope (em-dash sweep), left untouched per the standing instruction. The two `??` files are build artifacts. **Ruff caused zero drift** (status identical pre/post), so nothing of my own to revert. No `pytest` run (dispatch forbids it).

### Implementation notes

- **H1 — column-value test vs attribute-presence under Django 6.0.5.** The upstream-ported predicate used `hasattr(field, "column")` to mean "single-column forward relation". That discriminated correctly on the older Django the upstream was written against, where M2M / `GenericRelation` exposed no `column` attribute. Under the pinned Django 6.0.5, both `ManyToManyField` and `GenericRelation` expose a `column` *attribute* whose value is `None`, so `hasattr` returns `True` and they pass the predicate — over-including join-table / virtual relations and composing wrong-shape `Q(<m2m>__in=...)` constraints on a row-visibility surface (a correctness + security-narrowing bug). The fix tests the *value* (`getattr(field, "column", None) is not None`), which is `True` only for real concrete single-column forward FK/OneToOne edges. Verified the corrected predicate (a) still includes forward FK + forward OneToOne, (b) preserves the `parent_link` MTI exclusion (the `<parent>_ptr` `OneToOneField` carries a real `column` so the value test passes, but the explicit `parent_link` guard still excludes it), and (c) excludes M2M, reverse FK, reverse O2O, `GenericForeignKey` (no `related_model`), and `GenericRelation` (`column` is `None`). This is the DRY hinge: the single predicate feeds `_cascadable_edge_names`, `_validate_fields`, and `_walk`, so the one-line change corrects the full walk and `fields=` validation simultaneously. Chose `column is not None` over the equivalent `getattr(field, "concrete", False)` because it keeps the spec's verbatim "`column`" vocabulary and changes only the test from presence to value. `test_single_column_scope_skips_m2m_reverse_and_generic` is the pin (asserts `_cascadable_edge_names == {"fk","o2o","content_type"}` and per-edge predicate truth values, including `_is_cascadable_edge(m2m) is False` / `_is_cascadable_edge(generics) is False`).
- **H2 — `transaction=True` marker on the schema-editor tests.** The 7 tests that build real tables via the `_tables(...)` schema-editor context manager need `@pytest.mark.django_db(transaction=True)`: under plain `@pytest.mark.django_db`, pytest-django wraps each test in an atomic transaction, and SQLite's schema editor raises `NotSupportedError` (cannot run `create_model`/`delete_model` inside an atomic block with FK constraint checks enabled). This matches the `tests/test_relay_connection.py:184` precedent the artifact already cites for the same `managed=False` + schema-editor pattern. The construction-only pins (single-column scope, MTI, identity-hook str-query, multi-DB) do not call `_tables` and keep their existing markers unchanged; the `databases=["default","shard_b"]` multi-DB marker (`:350`) is untouched. No assertion weakened.

### Notes for Worker 3

- **Both High findings are addressed.** H1: `_is_cascadable_edge` now uses `getattr(field, "column", None) is not None` (+ docstring updates). H2: all 7 `_tables`-using tests carry `@pytest.mark.django_db(transaction=True)`. Per Worker 3's own expectation, `uv run pytest tests/test_permissions.py --no-cov -q` should now read 22 passed / 1 skipped (the `FAKESHOP_SHARDED` multi-DB pin).
- No production-behavior change beyond the one-line predicate value-vs-presence tightening; no test assertion was weakened (markers only). The `examples/fakeshop/apps/products/schema.py` working-tree change remains the concurrent em-dash comment swap, not a Worker 2 edit.

### Notes for Worker 1 (spec reconciliation)

- The H1 fix realizes Worker 3's recorded spec note: the spec's verbatim `hasattr(field, "column")` predicate text (Decision 5 step 1, spec line 257; checklist line 122) is Django-version-fragile and should read `field.column is not None` (or `field.concrete`) so the contract and the pinned Django version agree. Implemented as the value test; the spec-text spelling update is Worker 1's at final verification. The "excluded by construction" claim for M2M/`GenericRelation` (spec lines 395-396) holds only under the corrected predicate. No new spec-vs-codebase gap surfaced this pass; the three carry-forward items (stale "No `permissions.py` exists" Current-state line; `SyncMisuseError` redundant-alias re-export; `SyncMisuseError` cascade-message-wording tension) are unchanged.

---

## Review (Worker 3, pass 2)

Re-review of Worker 2's pass-2 apply-changes diff (the two High fixes), scoped per the artifact's pass-2 `### Files touched`: `django_strawberry_framework/permissions.py` (H1 predicate) and `tests/test_permissions.py` (H2 markers). Inspected with `git diff -- django_strawberry_framework/permissions.py tests/test_permissions.py` (the full diff is the prior-pass fill + this pass's two fixes against a HEAD that carried the staged seam / skip-stubs; I scoped to the pass-2 deltas) and by reading the current source of both files directly.

### H1 resolution — confirmed resolved correctly.

`permissions.py::_is_cascadable_edge` now reads (verified in current source, lines 102-106):

```django_strawberry_framework/permissions.py
return (
    getattr(field, "related_model", None) is not None
    and getattr(field, "column", None) is not None
    and not getattr(field.remote_field, "parent_link", False)
)
```

- **Forward FK + forward OneToOne included.** Both expose a non-`None` single-column `.column`, so both pass the value test. Pinned by `test_single_column_scope_skips_m2m_reverse_and_generic` (`tests/test_permissions.py` #"assert names == {"fk", "o2o", "content_type"}" + `_is_cascadable_edge(by_name["fk"]) is True` / `..."o2o"... is True`).
- **`parent_link` MTI exclusion preserved.** The `<parent>_ptr` `OneToOneField(parent_link=True)` has a real (non-`None`) `column`, so the value test passes — but the explicit `not getattr(field.remote_field, "parent_link", False)` guard still drops it. Pinned by `test_mti_parent_link_edge_excluded` (`tests/test_permissions.py` #"assert _is_cascadable_edge(ptr) is False" after asserting `getattr(ptr.remote_field, "parent_link", False) is True` and `hasattr(ptr, "column")`). Confirmed green.
- **M2M / reverse FK / reverse O2O / GFK / GenericRelation excluded.** M2M and `GenericRelation` carry a `.column` attribute valued `None` under Django 6.0.5 (the exact over-inclusion that the prior `hasattr` form leaked); the value test now excludes both. Reverse FK / reverse O2O (`ForeignObjectRel`) carry no `column`; `GenericForeignKey` carries no `related_model`. All five pinned `is False` in `test_single_column_scope_skips_m2m_reverse_and_generic` (`tests/test_permissions.py` #"assert _is_cascadable_edge(by_name["m2m"]) is False" through `..."profile"... is False`). The GFK's backing `content_type` FK is itself an ordinary single-column forward FK and legitimately cascadable (`{"fk","o2o","content_type"}`), documented inline — not a leak.
- **DRY hinge intact.** `_is_cascadable_edge` remains the single predicate; `_cascadable_edge_names` (`permissions.py:109-111`) wraps it and is consumed by `_validate_fields` (`:137`), and `_walk` calls `_is_cascadable_edge` directly (`:215`). One-token fix in one function corrected the full walk, `fields=` validation, and the name-set simultaneously — validation and walk cannot drift. The docstring (`:80-100`) and module docstring (`:15-16`) were updated to describe the column-*value* test and record why `hasattr` over-includes under Django 6.0; both now read accurately.

### H2 resolution — confirmed resolved.

Every `_tables`-using test carries `@pytest.mark.django_db(transaction=True)`. Mapped each of the 7 `with _tables(...)` call sites to its enclosing test marker (verified in current source):

- `test_cycle_guard_contextvar_breaks_mutual_cascade` (`:135` → `_tables` at `:161`/`:207`) — `transaction=True`; the prior-review "no marker at all" concern is moot (on-disk it now carries the `transaction=True` form).
- `test_nullable_fk_rows_preserved` (`:402` → `:430`) — `transaction=True`.
- `test_cascade_excludes_rows_with_hidden_targets` (`:450` → `:469`) — `transaction=True`.
- `test_hidden_and_missing_targets_indistinguishable` (`:487` → `:514`) — `transaction=True`.
- `test_secondary_type_as_root_reaches_primary_on_transitive_revisit` (`:637` → `:661`) — `transaction=True`.
- `test_cascade_target_sliced_or_values_queryset_is_consumer_bug` (`:704` → `:730`) — `transaction=True`.
- `test_self_referential_fk_cascades_once` (`:961` → `:983`) — `transaction=True`.

No assertion was weakened: the pass-2 change to the test file is marker-only (the contract assertions — cascadable-set equality, per-edge predicate truth values, NULL-FK preservation, hidden-target absence, `ValueError` propagation, etc. — are unchanged). Construction-only / non-`_tables` tests keep their existing markers (`@pytest.mark.django_db` or none); the multi-DB pin keeps `databases=["default","shard_b"]`. Matches the `tests/test_relay_connection.py:184` precedent the artifact cites.

### Focused-test re-run

`uv run pytest tests/test_permissions.py --no-cov -q` → **22 passed, 8 skipped** (0 failed). The 8 skips decompose (via `-rs`) into exactly: **1** `FAKESHOP_SHARDED`-gated multi-DB pin (`:346`, `skipif` on the env var — the expected single skip under a bare run) and **7** Slice-2/Slice-3 future stubs (`:1016`–`:1063`, correctly left `@pytest.mark.skip`; they were skip-stubs at HEAD and are not Slice-1's to fill). All 22 live Slice-1 pins are green; the prior pass's 8 failures (H1 scope leak + H2 schema-editor `NotSupportedError`) are gone. This matches the dispatch's expectation (22 passed; the multi-DB pin is the one Slice-1-relevant skip).

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

- No new DRY issue. The H1 fix did not introduce a second scope definition — it tightened the one existing predicate. The single-predicate hinge (`_is_cascadable_edge` → `_cascadable_edge_names` → `_validate_fields` / `_walk`) is intact and is precisely why the fix was one line.
- The pass-1 DRY confirmations stand unchanged: the single sync-misuse probe (`apply_type_visibility_sync` reused, no local `inspect.iscoroutine` site), the `sync_to_async(thread_sensitive=True)` async wrap of the *public* sync function (no second walk), and the `SyncMisuseError` redundant-alias re-export (the `types/relay.py:41` idiom, no new public name). No repeated literals.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py`: unchanged by this pass (Worker 2's pass-2 touched only `permissions.py` + `tests/test_permissions.py`). The pass-1 surface stands and was already verified correct: `# ruff: noqa: ERA001` seam directive removed; the `from .permissions import (...)` import seam uncommented; both `TODO(spec-034 Slice 1)` blocks removed; `"aapply_cascade_permissions"` + `"apply_cascade_permissions"` added to `__all__` alphabetically; `__version__ = "0.0.9"` untouched (Decision 13 authorizes the two `__all__` members to grow in Slice 1 while the version constant stays cut-owned). The `tests/base/test_init.py` exports pin (committed; not in the pass-2 diff) is consistent. Public surface correct.

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md`.

### Documentation / release sanity

Not applicable; the pass-2 diff touches no docs/release/KANBAN/archive surfaces. (`examples/fakeshop/apps/products/schema.py` carries a working-tree change, but it is the concurrent em-dash→hyphen comment sweep recorded in `build-034`'s "Concurrent-sweep update" section — out of scope and untouched by Worker 2 per the standing instruction.)

### What looks solid

- The H1 fix is the highest-quality root-cause shape: it tests the `column` *value* (the load-bearing property) rather than attribute presence, keeps the spec's verbatim `column` vocabulary, and routes through the single DRY hinge so both the full walk and `fields=` validation are corrected at once. Docstrings were updated to match — the comments now tell a coherent story (why value-not-presence, and the Django-6.0 over-inclusion rationale).
- The H2 fix is marker-only and matches the cited precedent exactly; no assertion shifted, so the test contract that *catches* H1 (the cascadable-set equality + per-edge predicate truth values) is preserved and now passes legitimately rather than being masked.
- The full Slice-1 suite is green and the pins are load-bearing (real SQL-shape assertions, absolute set equality, `.db` propagation, propagating `ValueError`, cycle-guard `_cascade_seen is None` after both clean and exception-path roots), not mere observability.

### Static helper

Re-run **not warranted** (recorded decision). The pass-2 change to `permissions.py` is a single-token tightening (`hasattr(field, "column")` → `getattr(field, "column", None) is not None`) inside `_is_cascadable_edge`, a function already inspected via the helper in the pass-1 review (`docs/shadow/django_strawberry_framework__permissions.overview.md`). It adds no import, no new symbol, no new control-flow branch, and no new string literal — none of the helper's overview sections (imports, symbols, hotspots, ORM markers, calls-of-interest, repeated literals) change. The pass-1 static analysis still characterizes the module accurately, so re-running would surface nothing new. Test-file changes are marker-only and do not meet any "30+/50+ lines of new logic" helper trigger.

### Temp test verification

No temp tests this pass. The two fixes were verified by reading the corrected source (predicate + docstrings, marker map) and by the focused `uv run pytest tests/test_permissions.py --no-cov -q` run (22 passed / 8 skipped). The prior pass's temp probe (`docs/builder/temp-tests/slice-1/test_probe.py`) was already deleted; nothing was recreated, so the temp-test tree stays clean.

### Notes for Worker 1 (spec reconciliation)

- Carried unchanged for final verification: (1) the spec's Decision 5 step 1 / checklist verbatim text still spells the predicate `hasattr(field, "column")`, which is Django-version-fragile — the implementation now uses `field.column is not None`; Worker 1 should update the spec-text spelling (and the "excluded by construction" claim for M2M/`GenericRelation`, which holds only under the corrected predicate) at final verification. (2) The stale "No `permissions.py` exists" Current-state line and the planning-pass status line ("no slice has started"). (3) The `SyncMisuseError` redundant-alias re-export (fold into the plan's import list or leave). (4) The `SyncMisuseError` cascade-message-wording tension (the reused `apply_type_visibility_sync` message names "the Relay node defaults", generic on the cascade path; the test deliberately pins type-name + `SyncMisuseError` + closed-coroutine, not the literal recourse phrasing — Worker 1's call whether to generalize the shared message via a Worker 2 pass). None of these block acceptance.

### Review outcome

`review-accepted`. Both High findings are resolved with verified fixes:
- **H1** (source): `_is_cascadable_edge` now uses `getattr(field, "column", None) is not None` — forward FK + forward O2O still included, the `parent_link` MTI exclusion preserved, M2M / reverse FK / reverse O2O / GFK / `GenericRelation` excluded; the single-predicate DRY hinge feeds `_cascadable_edge_names` / `_validate_fields` / `_walk` consistently.
- **H2** (tests): all 7 `_tables`-using tests carry `@pytest.mark.django_db(transaction=True)` (including the cycle-guard test); no assertion weakened.

Focused suite: `uv run pytest tests/test_permissions.py --no-cov -q` → **22 passed, 8 skipped, 0 failed** (1 `FAKESHOP_SHARDED` multi-DB skip + 7 Slice-2/3 future stubs). No new High/Medium/Low or DRY finding surfaced. Public-surface, CHANGELOG, and documentation checks clean. Artifact `Status:` set to `review-accepted` — ready for Worker 1 final verification.

---

## Final verification (Worker 1)

Final-verification pass for Slice 1 (cascade foundation), after Worker 3 set `review-accepted`. All five BUILD.md final-verification checks pass; the four Worker-3 carry-forward items are resolved (two via spec edits, two via recorded judgment). Top-level `Status:` set to `final-accepted`.

### 1. Spec slice checklist audit

All 7 boxes in the Plan's `### Spec slice checklist (verbatim)` are `- [x]`. Audited each against the shipped diff; every ticked box has matching implementation (no un-tick, no over-tick, no remaining `- [ ]`):

1. **Walk + scope + registry + hook gate + `Q(__in)|Q(__isnull)` + `queryset.db`** — landed. `permissions.py::_is_cascadable_edge` (`:102-106`), `_walk` (`:214-229`): `registry.get(field.related_model)` skip-on-`None`, `has_custom_get_queryset()` skip, `field.related_model._default_manager.using(queryset.db).all()`, `Q(<edge>__in) | Q(<edge>__isnull=True)`.
2. **`ContextVar` cycle guard, `finally` reset** — landed. `apply_cascade_permissions` (`:184-198`): root installs `{cls}` + `try/finally` reset; re-entry returns queryset unchanged; nested adds + `try/finally` discard. `_cascade_seen` (`:76`).
3. **`fields=` validation, `isinstance(str)` guard first** — landed. `_validate_fields` (`:128-145`): bare-string guard before any per-name lookup; unknown/non-cascadable names raise `ConfigurationError` naming entry + model + cascadable set.
4. **Sync-misuse via `apply_type_visibility_sync` reuse** — landed. `_walk:225` calls `apply_type_visibility_sync(target_type, base, info)`; no second `iscoroutine`/`close` site in `permissions.py` (confirmed — only the `as`-alias re-export imports `SyncMisuseError`).
5. **`aapply` = `sync_to_async(thread_sensitive=True)` wrap of the public sync fn** — landed. `aapply_cascade_permissions` (`:249`).
6. **Package-root export + `__all__` + `test_init.py` pin** — landed. `tests/base/test_init.py --no-cov -q` → 4 passed (the grown `__all__` with both cascade symbols passes; `test_version` still `0.0.9`, Decision 13 honored).
7. **`tests/test_permissions.py` incl. the 4 invariant pins** — landed. 23 Slice-1 pins live (cycle guard, single-column scope, alias pinning, nullable-FK), 22 run + 1 `FAKESHOP_SHARDED`-gated; 7 Slice-2/3 stubs correctly skipped.

### 2. DRY check

Slice 1 is the first slice — no prior-slice duplication to check. Internal DRY confirmed:
- **Sync-misuse probe genuinely reuses `utils/querysets.py::apply_type_visibility_sync`** (`_walk:225`) — no re-implemented `inspect.iscoroutine` / `.close()` / `raise SyncMisuseError` site in `permissions.py`. The package keeps ONE sync-misuse routing site (Decision 10).
- **Async wrap genuinely reuses the `sync_to_async(thread_sensitive=True)` precedent** (`filters/sets.py:1745`) around the *public* sync function — one walk implementation, no sync/async fork.
- **Single edge-scope predicate** (`_is_cascadable_edge`) feeds `_cascadable_edge_names` → `_validate_fields` and `_walk` directly; validation and walk cannot drift. No repeated literals; the two `ConfigurationError` messages are distinct and single-use.

### 3. Existing tests still pass (focused scope)

- `uv run pytest tests/test_permissions.py --no-cov -q` → **22 passed, 8 skipped, 0 failed** (1 `FAKESHOP_SHARDED` multi-DB pin + 7 Slice-2/3 stubs). Matches the expected ~22 passed / 8 skipped.
- `uv run pytest tests/base/test_init.py --no-cov -q` → **4 passed** (exports pin green with the new `__all__`).

Working tree left clean of test artifacts (no `--cov*` used; no temp files created).

### 4. Spec reconciliation — four Worker-3 carry-forward items

- **Predicate text (resolved — spec edited).** The spec's Decision 5 step 1 (line 257) and the Slice 1 checklist sub-bullet (line 57) spelled the scope predicate `hasattr(field, "column")`. The shipped, correct form is `getattr(field, "column", None) is not None` (under Django 6.0 M2M / `GenericRelation` expose `.column = None`, so the verbatim-upstream `hasattr` over-includes them). Updated both spec locations to the shipped form with a one-line Django-6.0 rationale, and tightened the dependent edge-case bullets (`GenericForeignKey`/`GenericRelation` line 396; MTI parent-link line 397) so "excluded by construction" reads correctly under the value test. **The artifact's verbatim checklist copy (artifact line 122) is left as the original `hasattr` text per the dispatch (do not retro-edit the verbatim copy); this reconciliation note records the divergence** — the artifact's verbatim box was copied from the spec's pre-correction wording, and the spec is now the corrected source of truth.
- **Stale status lines (resolved — spec edited).** Spec line 5 ("Status: planned — no slice has started") → "Status: in progress — Slice 1 (cascade foundation) shipped; Slices 2-5 remain". The Current-state "No `permissions.py` exists" bullet (line 90) → a "`permissions.py` shipped in Slice 1" bullet recording the module now exists with both symbols package-root exported, products-schema hooks still commented (Slice 4). Edits kept minimal and accurate. (The spec's `## Slice checklist` boxes are intentionally left unticked — spec line 3 establishes "the Slice checklist below stays unticked as the contract record"; not re-ticking it is deliberate.)
- **`SyncMisuseError` re-export (resolved — accepted, no churn).** `permissions.py:57` does `from .utils.querysets import SyncMisuseError as SyncMisuseError` (the `types/relay.py:41` redundant-alias convention) so the committed test import header resolves. Confirmed it adds **no new public package-root name** — `SyncMisuseError` is already exported via `types`/`__all__` (the `tests/base/test_init.py` exports pin is green and unchanged). The `X as X` form is ruff-recognized as an intentional re-export (no `# noqa`). **Judgment: acceptable as-is; not gratuitous** — it lets the cascade's own error surface import from `permissions.py` without reaching into the private `utils` package. No spec edit; no integration follow-up needed.
- **Cascade sync-misuse message wording (resolved — accept the reuse).** `apply_type_visibility_sync`'s `SyncMisuseError` message names "the Relay node defaults" and a sync-`get_queryset`-rewrite recourse — accurate-but-generic on the cascade path (it does not name `aapply_cascade_permissions`). **Decision: accept the reuse (DRY).** Decision 10's explicit "reuse the probe shape" instruction and the data-leak-routing rule in the `utils/querysets.py` docstring outweigh cascade-message specificity; the message still names the offending target type and a valid sync recourse. The test `test_sync_helper_raises_syncmisuseerror_on_async_target_hook` correctly pins type-name + `SyncMisuseError` + closed-coroutine, not the literal recourse phrasing. Generalizing the shared `utils/querysets.py` message would touch shared source (three consumer surfaces) and is **not forced into Slice 1**; flagged here as a low-priority candidate for the integration pass should a future slice find the generic wording materially misleading on the cascade surface. No spec edit, no Slice-1 code change.

### Summary

Slice 1 shipped the cascade foundation: `django_strawberry_framework/permissions.py` (new module) with the public sync `apply_cascade_permissions(cls, queryset, info, fields=None)` and async `aapply_cascade_permissions(...)`. The sync entry owns the `ContextVar` (`_cascade_seen`) cycle-guard lifecycle (root install + `finally` reset / re-entry partial-narrow / nested frame-exit discard) and delegates per-edge composition to a private `_walk`; the async twin is `sync_to_async(thread_sensitive=True)` around the public sync function (one walk, no fork). The single `_is_cascadable_edge` predicate (`related_model` present AND non-`None` single-column `column` AND not MTI `parent_link`) is the DRY hinge feeding both the full walk and `fields=` validation. Each edge resolves its target via `registry.get` (primary lookup), skips identity-hook / unregistered targets, runs the target hook through the reused `apply_type_visibility_sync` probe (single sync-misuse site → `SyncMisuseError` on async hooks), and intersects `Q(<edge>__in=target_qs) | Q(<edge>__isnull=True)` with `target_qs` built from `_default_manager.using(queryset.db).all()` (caller-alias pinned, unevaluated subquery). `fields=` validates loudly (`isinstance(str)` guard first, then `ConfigurationError` for unknown/non-cascadable names). Both symbols export from the package root (`__init__.py` seam uncommented, `# ruff: noqa: ERA001` removed, `__all__` grown alphabetically, `__version__` untouched per Decision 13). `tests/test_permissions.py` carries 23 live Slice-1 pins (incl. the four dedicated upstream-invariant pins) + 7 correctly-skipped Slice-2/3 stubs; `tests/base/test_init.py` exports pin grown. Two High findings from the first review (Django-6.0 `hasattr`-column scope leak; missing `transaction=True` on schema-editor tests) were fixed in Worker 2's pass 2 and verified by Worker 3.

### Spec changes made (Worker 1 only)

- `docs/spec-034-permissions-0_0_10.md` line 257 (Decision 5 step 1) — Slice 1 — corrected the scope predicate from `hasattr(field, "column")` to `getattr(field, "column", None) is not None` with a Django-6.0 rationale (M2M / `GenericRelation` expose `.column = None`); the shipped, correct form.
- `docs/spec-034-permissions-0_0_10.md` line 57 (Slice 1 checklist sub-bullet) — Slice 1 — same predicate correction, noting the upstream-`hasattr`-vs-shipped divergence; keeps the spec checklist text in sync with the implementation.
- `docs/spec-034-permissions-0_0_10.md` line 396 (Edge case, GFK/`GenericRelation`) — Slice 1 — reworded "`column` absent" to the column-*value* test so "excluded by construction" holds under the corrected predicate.
- `docs/spec-034-permissions-0_0_10.md` line 397 (Edge case, MTI parent link) — Slice 1 — noted the `<parent>_ptr` carries a real (non-`None`) `column` and passes the corrected value test, excluded by the `parent_link` guard.
- `docs/spec-034-permissions-0_0_10.md` line 5 (Status line) — Slice 1 — "planned — no slice has started" → "in progress — Slice 1 (cascade foundation) shipped; Slices 2-5 remain" (stale once Slice 1 landed).
- `docs/spec-034-permissions-0_0_10.md` line 90 (Current-state bullet) — Slice 1 — "No `permissions.py` exists" → a bullet recording the module shipped in Slice 1 with both symbols package-root exported; products hooks still commented (Slice 4).

No source or test edits (none needed — both Worker-3 carry-forward code items were resolved by judgment, not change). No commit.
