# Review: `django_strawberry_framework/registry.py`

Status: verified

## DRY analysis

- None — the one cross-method near-copy (the register-side mutation undone in `register_with_definition`'s rollback, `registry.py:158-162` vs `registry.py:335-343`) is a deliberate inverse-of-register block whose correctness depends on staying lexically adjacent to and readable against the forward mutation; the `# Inverse of register's mutations above` comment (`registry.py:333`) pins the coupling, and factoring it into a shared `_undo_register` helper would split a 2-call invariant across a function boundary for no reuse gain (only one rollback site exists). The "already registered" phrasing and the cycle-safe local-import shape were both already consolidated in the 0.0.9 DRY pass (`_already_registered`, `registry.py:87-99`; `_clear_if_importable`, `registry.py:34-50`), so the standing duplication is already collapsed.

## High:

None.

## Medium:

None.

## Low:

### `register_with_definition` rollback is hand-maintained against `register`'s mutation set

`register` (`registry.py:158-162`) performs three coordinated mutations on a True-returning append: `existing_types.append`, `self._models[type_cls] = model`, and conditionally `self._primaries[model] = type_cls`. The rollback in `register_with_definition` (`registry.py:335-343`) inverts exactly those three, gated on the `appended` snapshot and the `pre_primary` snapshot. This is correct today and the `# Inverse of register's mutations` comment (`registry.py:333`) flags the coupling, but the invariant is enforced only by reviewer vigilance — a future fourth mutation in `register` (e.g. a new index keyed on `type_cls`) that the author forgets to mirror here leaks state on the `register_definition`-raises path.

Defer until `register` gains a fourth coordinated mutation on the append path; at that point extract the forward mutation and its inverse into a paired `_apply_registration` / `_undo_registration` private helper so the two sites cannot drift. No action now — a single rollback caller does not justify the indirection, and the comment carries the contract in the interim.

### `get()` conflates "ambiguous multi-type" and "unregistered" into a single `None`

`get()` (`registry.py:221-240`) returns `None` both for an unregistered model and for a registered model with multiple types and no declared primary; the docstring (`registry.py:230-233`) documents this and tells callers to disambiguate via `types_for(model)`. This is an intentional pre-finalize contract — `_audit_primary_ambiguity` (finalizer Slice 3, fed by `models_with_multiple_types`, `registry.py:284-290`) is what converts the ambiguous state into a loud `ConfigurationError` before any consumer relies on `get()`. No change; recorded so a future caller that treats `get() is None` as "definitely unregistered" is recognized as the bug rather than `get()` itself.

## What looks solid

### DRY recap

- **Existing patterns reused.** `_already_registered` (`registry.py:87-99`) centralizes the cross-key "already registered" phrasing for the two collision sites (`register`'s reverse-collision `registry.py:141`, `register_enum`'s key collision `registry.py:457-461`); `_clear_if_importable` (`registry.py:34-50`) single-sites the cycle-safe best-effort local-import-and-clear shape used by both `unregister` (`registry.py:215-219`) and `clear` (`registry.py:498-527`). Both are products of the 0.0.9 DRY pass (`docs/feedback.md` "Registry Clear Optional-Callback Pattern") and are applied consistently.
- **New helpers considered.** A paired `_apply_registration`/`_undo_registration` helper for the `register` forward mutation + `register_with_definition` rollback was evaluated and rejected for now — only one rollback site exists, so the indirection costs readability without reuse (captured as the Low deferral with an explicit trigger).
- **Duplication risk in the current file.** The repeated literal `"django_strawberry_framework.connection"` (flagged 2x by the helper) is intentional sibling design: `unregister` evicts one entry (`registry.py:216`) while `clear` purges the whole cache via a different attribute (`registry.py:519`), so the two call sites target different functions on the same module and a shared module-path constant would not reduce the two distinct `attr_name` arguments. Leaving the literal inline keeps each `_clear_if_importable` call self-describing.

### Other positives

- **Mutability contract is coherent and defense-in-depth layered.** `_check_mutable` (`registry.py:72-85`) guards every mutator except `clear` (the documented test-only escape hatch, `registry.py:468-476`); the docstring correctly notes `__init_subclass__` already rejects post-finalize subclasses, making this the boundary backstop. The class docstring (`registry.py:53-61`) is explicit that no lock guards mutation and explains why (import-time single-threaded mutation; never mutate from a request/async path) — the right contract for a process-global singleton, and consistent with worker-1's prior calibration that request-scope-vs-import-time state must be documented at the boundary.
- **`unregister` lock-step invariant is verified, not assumed.** The `_models.pop` → `_types[model]` reach (`registry.py:193-202`) is justified by the inline comment (`registry.py:196-198`) that `register` keeps the two maps in lock-step, so the unconditional `self._types[model]` index after a non-None `pop` cannot `KeyError`. The connection-cache eviction is correctly scoped: the cache is identity-keyed on the node type (`connection.py:704, 731`), so evicting `_connection_type_cache.pop(type_cls, None)` (`registry.py:216`) targets the right key, and the comment (`registry.py:209-214`) honestly grades it hygiene-not-correctness.
- **`unregister` "all traces" wording does not over-promise.** It drops `_types`/`_models`/`_primaries`/`_definitions`/pending and the connection cache, but deliberately leaves `_enums` — enums are keyed on `(model, field_name)` and shared across multiple types for the same model (`register_enum` docstring, `registry.py:441-452`), so they are traces of the model, not of `type_cls`. The docstring's enumerated drop list (`registry.py:165-167`) omits enums, matching behavior.
- **`iter_pending_relations` staleness contract is honored by the real consumer.** The docstring (`registry.py:401-411`) warns that `discard_pending` rebinds `self._pending` to a fresh list (`registry.py:425`), so a caller mid-`yield from` sees a stale view; the sole production consumer (`finalizer.py:578-613`) drains the iterator into `unresolved`/`resolved`/`consumer_authored` lists before calling `discard_pending`, so the documented hazard never fires on the live path. Identity-based discard (`id()`, `registry.py:424`) is the correct contract given the finalizer hands back the same instances.
- **`register_with_definition` atomicity is genuinely failure-atomic.** It snapshots `pre_primary` before `register` and captures the `appended` return, so a `register_definition` raise rolls back only state THIS call added — an idempotent same-type re-register (`register` returns False, `registry.py:150`) survives a later different-definition failure intact, matching the docstring (`registry.py:318-327`) and the `register` return-value contract (`registry.py:128-130`).
- **`definition_for_graphql_name` keys on the right attribute.** It scans `iter_definitions()` for a unique `graphql_type_name` match restricted to Relay-Node definitions (`registry.py:375-390`), keying on `definition.graphql_type_name` (which honors `Meta.name`, `definition.py:193-203`) rather than `type_cls.__name__`, with distinct miss vs. ambiguity errors. The in-function `implements_relay_node` import (`registry.py:373`) and its rationale comment (`registry.py:368-372`) correctly avoid coupling the early-imported `registry` module top to `types.relay`.

### Summary

A mature, heavily-reviewed module (Round-4 and 0.0.9 DRY-pass artifacts are visible in the comments) with no correctness, isolation, or DRY defects found. The mutability/finalization contract is coherent and documented at the boundary; the process-global-singleton thread-safety stance is explicitly justified rather than left implicit; the two public mutators (`unregister`, `clear`) reuse the single-sited `_clear_if_importable` helper consistently and the connection-cache eviction targets the correct identity key. The only items are two forward-looking Lows: a trigger-gated suggestion to pair the `register`/`register_with_definition` rollback mutations if `register` grows a fourth coordinated mutation, and a recorded note that `get()`'s ambiguous-vs-unregistered `None` collapse is intentional and audited at finalize-time. GLOSSARY prose (lines 524, 816, 825, 930) matches source behavior — no drift. No source edit warranted.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched

None — no-source-edit cycle.

### Tests added or updated

None — no-source-edit cycle.

### Validation run

- `uv run ruff format .` — 0 files reformatted (clean).
- `uv run ruff check --fix .` — All checks passed.

### Notes for Worker 3

- Both Lows are forward-looking / recorded-intent, requiring no edit:
  - **`register_with_definition` rollback coupling** — deferred with explicit trigger ("until `register` gains a fourth coordinated mutation on the append path"); contract held by the `# Inverse of register's mutations` comment in the interim.
  - **`get()` ambiguous-vs-unregistered `None`** — intentional pre-finalize contract audited by `_audit_primary_ambiguity` at finalize-time; recorded only so a future misreading caller is the recognized bug.
- No GLOSSARY-only fix in scope — GLOSSARY prose (lines 524, 816, 825, 930) already matches source behavior; no drift found.
- No shadow regeneration needed; the plan-time `--all` overview at `docs/shadow/django_strawberry_framework__registry.overview.md` matches current source.

---

## Verification (Worker 3)

Shape #5 no-source-edit cycle. Independently re-inspected `registry.py` against the baseline; both Lows confirmed forward-looking with no code change warranted.

### Logic verification outcome

- **Baseline diff empty.** `git diff 0872a20f -- django_strawberry_framework/registry.py` empty; `git diff --stat 0872a20f` over owned paths (`django_strawberry_framework/`, `tests/`, `examples/`, `docs/GLOSSARY.md`, `docs/TREE.md`, `CHANGELOG.md`) empty. Files-touched "None" holds.
- **Both Lows genuinely forward-looking, re-derived from source (not trusted from artifact):**
  - *Rollback coupling* — `register`'s True-path mutations (`registry.py:158-161`: `existing_types.append`, `self._models[type_cls] = model`, conditional `self._primaries[model] = type_cls`) are mirrored exactly by the rollback (`registry.py:335-343`: `types.remove` + empty-list pop, `_models.pop`, `_primaries` restore-to-`pre_primary`/pop-when-`pre_primary`-None). Inverse is correct today; the `# Inverse of register's mutations` comment (`registry.py:333`) pins the coupling; the deferral trigger ("until `register` gains a fourth coordinated mutation") is real. No edit.
  - *`get()` ambiguous-vs-unregistered `None`* — collapse is documented (`registry.py:229-232`) and audited at finalize by `_audit_primary_ambiguity` (`finalizer.py:129`, fed by `models_with_multiple_types`, `registry.py:284-290`). Recorded-intent only. No edit.
- **Load-bearing claims independently confirmed:**
  - Connection-cache eviction targets the correct key — `_connection_type_cache` is identity-keyed on the node/target type (`connection.py:512` decl, `:708` get, `:731` set), so `unregister`'s `cache.pop(type_cls, None)` (`registry.py:215-219`) hits the right entry.
  - `iter_pending_relations` staleness hazard never fires on the live path — the sole consumer (`finalizer.py:578-600`) fully drains the iterator into `unresolved`/`resolved`/`consumer_authored` before `discard_pending` (`finalizer.py:613`).
  - `_already_registered` reuse spans both collision sites (`register` reverse-collision `registry.py:141`; `register_enum` key collision `registry.py:457-461`).
- **Reset/mutability semantics coherent.** `_check_mutable` guards every mutator except `clear` (documented test-only escape hatch); `unregister` fires the guard before the registration check (post-finalize unknown-type calls raise, not no-op); `clear` resets `_finalized = False` and runs the independent best-effort co-clears. Register vs rollback symmetry holds. No defect found.

### DRY findings disposition

DRY analysis records None. Verified the two single-sited helpers (`_already_registered`, `_clear_if_importable`) are applied consistently and the deliberate `register`/rollback inverse-block "duplication" is correctly left un-extracted (single rollback site, comment-pinned). The repeated `"django_strawberry_framework.connection"` literal is intentional sibling design (two distinct `attr_name` targets). Carried forward as the rollback Low's trigger; no action now.

### Temp test verification

None — no temp test needed. Verification was by direct source inspection and grep against the cited symbols/lines; pytest not run (no test introduced, no focused confirmation required), consistent with the shape #5 no-edit cycle and AGENTS.md "Do not run pytest".

### Verification outcome

cycle accepted; verified — sets top-level `Status: verified` AND marks the `registry.py` checklist box. Zero owned-source edits vs baseline; ruff format-check + check clean; changelog Not-warranted (empty `git diff -- CHANGELOG.md`) with both citations; GLOSSARY (524/816/825/930) aligned; both Lows confirmed forward-looking with verbatim/recorded triggers, no GLOSSARY-only fix. Dirty tracked files are only `docs/review/rev-*.md` artifacts plus deleted root `feedback2.md`/`feedback3.md` (AGENTS.md #33 concurrent-maintainer work, out of scope).

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment or docstring edits warranted — docstrings accurately describe behavior across every reviewed method; no stale, restating, or over-promising prose found.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — no source change; per `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan's silence on a changelog entry for this item, no `CHANGELOG.md` edit is made.

---

## Iteration log
