# DRY review: `django_strawberry_framework/optimizer/_context.py`

Status: verified

## System trace

The target owns the **optimizer ↔ resolver hand-off through Strawberry
`info.context`**: five wire-key constants, the inventory tuple
`DST_OPTIMIZER_KEYS`, and the defensive object/dict/None/frozen dispatch for
read (`get_context_value`), write (`stash_on_context`), and start-of-execution
clear (`clear_optimizer_context` / `_clear_context_key`).

Owned responsibility:

- one key vocabulary for plan introspection, FK-id elisions, planned-resolver
  sentinels, lookup paths, and strictness mode;
- one access-mode contract so object contexts, plain dicts, dict subclasses,
  `__slots__` / bridged mappings, `None`, and read-only shapes (frozen
  mappings, locked `QueryDict`) round-trip the same way on read and write;
- one clear inventory so a reused `context_value` cannot leak correctness
  sentinels across sequential `execute` / `execute_sync` calls.

Connected behavior examined:

- `optimizer/extension.py` — write side: `on_execute` clears via
  `clear_optimizer_context`; `_publish_plan_to_context` stashes plan /
  strictness and unions correctness sets via `_stash_union` (which calls
  `get_context_value` + `stash_on_context`). Historical re-export of
  `_stash_on_context` for older test imports. Sibling plan item still open.
- `types/resolvers.py` — read side: `_check_n1` and `forward_resolver` consume
  `DST_OPTIMIZER_PLANNED`, `DST_OPTIMIZER_STRICTNESS`, and
  `DST_OPTIMIZER_FK_ID_ELISIONS` only through `get_context_value`.
- `optimizer/nested_planner.py` — evidence only (not a plan item); no direct
  context stash/get of these keys (planning feeds the extension publish path).
- `extensions/debug.py` — stashes a debug payload on the extension instance /
  result extensions map, not on `info.context` under `dst_optimizer_*`.
- `utils/permissions.py::request_from_info` — resolves a Django/Channels
  request from `info.context` and **fails loud** with `ConfigurationError`;
  opposite of this module's defensive-coerce stash posture.
- `utils/write_transaction.py` / `permissions.py` / `optimizer/selections.py` —
  `ContextVar` lifecycles for write aliases, cascade seen-sets, and selection
  caches; not `info.context` key dispatch.
- Upstream `strawberry_django/optimizer.py` — keeps optimizer enablement on
  `ContextVar`s; does not implement this package's `info.context` sentinel
  hand-off. Architecture differs by design.
- Pins: `tests/optimizer/test_extension.py` (shape matrix, clear-on-execute,
  frozen/QueryDict no-ops, `_stash_union` coexistence);
  `tests/types/test_resolvers.py` (resolver reads of stashed sentinels);
  live/connection coverage in `tests/test_relay_connection.py` /
  `tests/test_connection.py` for publish/union behavior through real
  pipelines.
- Baseline
  `git diff d10a26b695fcafee0f1540ccee1352c725dc8f4e -- …/optimizer/_context.py`
  is empty. Concurrent dirty paths (`optimizer/__init__.py`, plan file, other
  open siblings) left untouched.

## Verification

Searches:

- Production importers of `_context` symbols: only `extension.py` (write/clear)
  and `types/resolvers.py` (read). No other package module hand-rolls
  `dst_optimizer_*` get/set/delete.
- `"dst_optimizer_"` literals outside the constant definitions: tests (often
  pinning wire strings), archived specs, `scripts/review_inspect.py` — not a
  second production access policy.
- Parallel "context stash" names (`build_and_stash_input`, debug `_payload`,
  mutation Meta stashes): bind-time or extension-instance state with different
  lifecycles and failure modes.
- Optional `export_dry_review.py audit --target …/_context.py`: four
  definitions; reverse imports match the two production consumers above.
  Static similarity alone did not justify further helpers.

Rejected / deferred candidates (tried to disprove shared ownership):

1. **Factor get / stash / clear into one `_object_then_mapping` helper with
   callable ops or exception-set parameters.** Disproved as a DRY win: the
   three paths intentionally differ (read uses `_MISSING` + `dict.get` and
   swallows `KeyError`; write catch-and-chains setattr failures then swallows
   only `TypeError`/`AttributeError` on item write; clear swallows `KeyError`
   on delete). A shared helper would need mode flags or strategy callables to
   reconcile those rules — the anti-pattern `DRY.md` warns against. The three
   functions *are* the already-centralized owner of the symmetry.

2. **Move `DjangoOptimizerExtension._stash_union` into `_context.py`.**
   Deferred / owned elsewhere: union-with-subset-early-out is **publish
   policy** for nested FALLBACK connection re-entry (spec-033 Decision 8), not
   generic key access. It correctly *uses* this module's get/stash. Sibling
   `extension.py` item remains the place to revisit publish ownership.

3. **Unify with `utils/permissions.py::request_from_info` (or a package-wide
   "context access" util).** Disproved: fail-loud request resolution vs
   silent optimizer introspection/sentinel hand-off — different contracts and
   change axes.

4. **Unify with `extensions/debug.py` payload stash or mutation/form
   `build_and_stash_*`.** Disproved: different storage sites, lifecycles, and
   consumers; only the word "stash" overlaps.

5. **Retarget strawberry-django's `ContextVar` optimizer state into this
   module (or vice versa).** Disproved: this package's resolver-visible
   sentinels on `info.context` are an intentional cross-resolver contract;
   upstream enablement ContextVars are a different mechanism.

6. **Retire `extension` re-export of `_stash_on_context`; force all tests
   through `_context`.** Deferred as test-import churn with no duplicated
   production policy. Canonical body already lives here.

7. **Add typed wrappers (`get_planned`, `stash_strictness`, …) around the
   five keys.** Disproved: callers already share constants + get/stash; wrappers
   would add a second API without removing a second implementation.

8. **Migrate test wire-string literals to `DST_OPTIMIZER_*` constants (or
   force all tests through `get_context_value`).** Disproved for this pass:
   intentional test-legibility / wire-format pins; `DRY.md` preserves
   independent test repetition. No production drift site.

## Opportunities

None — the target is already the single owner of optimizer `info.context`
key vocabulary and object/dict/frozen dispatch. Write-side publish union,
resolver N+1 policy, and unrelated context/request helpers correctly stay
outside this module. Item-scoped baseline diff is empty.

## Judgment

Zero-edit. Prior extraction into `_context.py` already solved the
cross-subpackage duplication the module docstring describes. Further
collapsing read/write/clear or absorbing `_stash_union` would obscure distinct
contracts rather than remove a shared change axis. Ready for Worker 2
independent verification.

## Independent verification (Worker 2)

Re-traced ownership end-to-end: wire keys + `DST_OPTIMIZER_KEYS` inventory +
object/dict/None/frozen dispatch for get / stash / clear. Production consumers
are only `optimizer/extension.py` (write/clear/`_stash_union`) and
`types/resolvers.py` (read via `get_context_value`). No other package module
defines or hand-rolls `dst_optimizer_*` access.

Scoped baseline diff empty:

`git diff d10a26b695fcafee0f1540ccee1352c725dc8f4e -- django_strawberry_framework/optimizer/_context.py`
→ no output (HEAD `b9f56a6009b5b258ae59f524c46f6562c3ed888a`).

Challenges to rejected candidates (all upheld):

1. **Shared `_object_then_mapping` helper** — Confirmed distinct contracts: read
   uses `_MISSING` + `dict.get` and swallows `KeyError`; write catch-and-chains
   setattr then swallows only `TypeError`/`AttributeError` on item write (not
   `KeyError`); clear swallows `KeyError` on delete. Factoring would need
   strategy callables / mode flags — not a DRY win.
2. **`_stash_union` into `_context`** — Publish/union/subset-early-out policy
   (nested FALLBACK re-entry); correctly *uses* get/stash. Sibling
   `extension.py` ownership stands.
3. **`request_from_info`** — Fail-loud Django/Channels request resolution vs
   silent sentinel hand-off; opposite postures.
4. **Debug / `build_and_stash_*`** — Different storage sites and lifecycles;
   name overlap only.
5. **Upstream ContextVar optimizer state** — Enablement/lifecycle ContextVars
   vs resolver-visible `info.context` sentinels; intentional split.
6. **Retire extension `_stash_on_context` re-export** — Compatibility alias;
   canonical body already here; no second production policy.
7. **Per-key typed wrappers** — Would add API surface without removing a second
   implementation.
8. **Test wire-string pins → constants** — Intentional wire-format / shape
   pins; `DRY.md` preserves test-legible repetition.

Missed-opportunity search: no production bypass of get/stash/clear; no
parallel key vocabulary; ContextVar caches in extension/nested_fetch are
execution-scoped, not `info.context` key dispatch. Dual fk-id elision
surfaces (plan field vs standalone set) are publish design, not access-policy
duplication.

Disposition: zero-edit verified. No blockers.
