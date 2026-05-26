# Review: `django_strawberry_framework/registry.py`

Status: verified

## DRY analysis

- Defer until a third caller for the rollback shape appears: extract a private `_rollback_register(model, type_cls, pre_primary)` helper from the rollback block at `registry.py:298-308`. Today it's only called from `register_with_definition`'s exception handler and would still need to share the `appended` context with the caller, so the helper signature gains nothing over the current inline anchor comment at `registry.py:298`. Trigger: when a second atomic-pair wrapper (e.g., a hypothetical `register_with_pending` for the pending-relation ingestion path) needs the same rollback shape, fold both call sites through `_rollback_register(model, type_cls, pre_primary, appended)`.

## High:

None.

## Medium:

### `GLOSSARY.md` "Meta.primary" rule 3 still quotes the pre-0.0.7 error message verbatim

`docs/GLOSSARY.md:668` codifies the duplicate-primary contract as:

> Multiple `DjangoType`s, two or more with `Meta.primary = True` — rejected at the second registration: `ConfigurationError("<class> is already declared primary as <existing>")`.

The implementation at `registry.py:131-138` and the test at `tests/test_registry.py:767-771` were updated post-0.0.6 to a more triage-friendly two-clause message:

```django_strawberry_framework/registry.py:131:138
if primary:
    existing_primary = self._primaries.get(model)
    if existing_primary is not None:
        raise ConfigurationError(
            f"Cannot register {type_cls.__name__} as primary for {model.__name__}; "
            f"{existing_primary.__name__} is already the primary type",
        )
```

The new phrasing carries three load-bearing identifiers (attempt name, model name, incumbent primary), which is strictly better than the old shape — but GLOSSARY.md still names the old `"is already declared primary as"` substring as the canonical error contract. Anyone grepping GLOSSARY.md for the exact error their stack trace shows will not find a match; anyone writing a `pytest.raises(...match=...)` against the documented contract will fail on the substring "is already declared primary as" being absent in production. This is documentation-vs-code drift on one of the four Meta.primary contracts the GLOSSARY explicitly enumerates, and the GLOSSARY is the package's public Meta.primary spec, not a casual comment. The fix is on the documentation side — `registry.py` already lines up with the test suite (`tests/test_registry.py:769`) and with the test docstring's "all three load-bearing identifiers" rationale, so the contract evolution is the intentional surface; only the GLOSSARY entry lags. Recommend updating `docs/GLOSSARY.md:668` to quote the new message verbatim (`"Cannot register <class> as primary for <model>; <existing> is already the primary type"`).

### `unregister` clears primary even when a sibling type would be the natural promotion target

`unregister`'s docstring at `registry.py:171-172` describes the post-unregister state truthfully — *"When ``type_cls`` is the primary for its model, the model loses its primary even if siblings remain — the caller is responsible for re-declaring a primary via a fresh registration cycle."* — and the behavior at `registry.py:183-184` is consistent with that promise:

```django_strawberry_framework/registry.py:183:184
if self._primaries.get(model) is type_cls:
    self._primaries.pop(model, None)
```

This is correct for the post-finalize-test-teardown case (`unregister` is a `_check_mutable`-gated test helper, not a production mutator, so any caller necessarily re-runs the registration cycle from scratch). It does, however, leave the registry in a state where:

1. `_types[model]` still has one or more sibling types.
2. `_primaries[model]` is missing.
3. `get(model)` returns `None` (multi-type, no primary path at `registry.py:204-207`).
4. Any subsequent call to `finalize_django_types()` would raise `ConfigurationError` via `_audit_primary_ambiguity` at `types/finalizer.py:103-128`.

The post-unregister state thereby becomes a re-registration-required state by design, but the design is half-encoded — the docstring describes it, no helper enforces it, and there is no test pinning the audit-after-unregister-from-multi-type case (the existing `tests/test_registry.py:1199-1226` test stops at asserting the post-unregister snapshot without finalizing). This is a missing-test-for-an-important-branch Medium per `REVIEW.md` "Severity definitions". The fix is to add a regression test that calls `unregister(primary_for_multi)` and then asserts that `_audit_primary_ambiguity` rejects the resulting state with the canonical ambiguity message — pinning the contract the docstring narrates, and preventing a future maintainer from "helpfully" auto-promoting the next sibling to primary on unregister (which would silently change the relation-resolution target).

```django_strawberry_framework/registry.py:171:172
When ``type_cls`` is the primary for its model, the model loses
its primary even if siblings remain — the caller is responsible
for re-declaring a primary via a fresh registration cycle.
```

## Low:

### `clear()` resets `_finalized` but does NOT call `_check_mutable`

`clear()` at `registry.py:392-405` intentionally does not call `_check_mutable` so test teardown can reset a finalized registry. This is correct and is the only public mutator that bypasses the guard. The docstring at `registry.py:393-398` says the helper is "Test-only — production code should never need to call this. Wire into ``pytest`` autouse fixtures so each registry-using test starts with a clean registry." The omission of an explicit "_check_mutable is intentionally not called" line in the docstring leaves the next maintainer to derive that fact from the absence of the call. The class-level docstring at `registry.py:34-41` covers the "every production-path mutation runs at import time" contract but does not call out `clear` as the deliberate exception to `_check_mutable`. Recommend a one-sentence addition to the `clear` docstring explicitly naming the intentional bypass — small comment-pass polish, no logic change.

```django_strawberry_framework/registry.py:392:405
def clear(self) -> None:
    """Drop all registered types and enums.

    Test-only — production code should never need to call this.
    Wire into ``pytest`` autouse fixtures so each registry-using test
    starts with a clean registry.
    """
    self._types.clear()
    ...
    self._finalized = False
```

### `register_definition` collision phrasing still diverges from `_already_registered` helper

Forwarded from `rev-registry.md` (0.0.6 cycle) — the project pass landed this as a "the four phrasings stay" decision and the divergence is intentional. Restating here so the project pass for 0.0.7 sees the fact in one place: `register_definition` raises `f"{type_cls.__name__} already has a registered DjangoTypeDefinition"` at `registry.py:272`, which is the fourth distinct "already registered" phrasing in the file alongside the three other inline raises and the `_already_registered` template. Every phrasing is test-pinned by substring at `tests/test_registry.py` (the 0.0.6 review enumerated the lines). Not actionable as a local defect; forwarded again to `rev-django_strawberry_framework.md` only if the project pass wants to revisit the "pluralized vs collapsed" decision.

### `iter_pending_relations` documentation hedges on mutation safety but the iterator is already a generator

The docstring at `registry.py:324-331` reads *"``discard_pending`` may be called between yields by the finalizer; callers that materialize the iterator and then trigger discards will observe a stale view."* This is accurate: `discard_pending` at `registry.py:344-345` rebuilds `self._pending` as a fresh list, so a `yield from self._pending` started earlier holds a reference to the *old* list object and continues iterating over it. The hedge is correctly written — the prose ends with the recommended pattern ("Typical consumers (the finalizer itself) drain into a list before mutating") and the finalizer at `types/finalizer.py` does drain into a list before any `discard_pending`. Minor wording suggestion only: name the rebuild-list-on-discard mechanism explicitly so a future reader does not have to infer it from `discard_pending`'s body. Trivial polish, defer until the comment pass.

## What looks solid

### DRY recap

- **Existing patterns reused.** The module sits at the bottom of the internal dependency graph and imports only `collections.abc`, `enum`, `typing`, `django.db.models`, and `.exceptions.ConfigurationError` (`registry.py:18-26`). `TYPE_CHECKING`-guarded imports of `DjangoTypeDefinition` and `PendingRelation` at `registry.py:28-30` keep the runtime graph acyclic — both modules in `types/` import this one. The canonical "already registered" error builder `_already_registered` at `registry.py:67-79` is the only error-message helper, called from `register`'s reverse-collision branch at `registry.py:121` and `register_enum`'s `(model, field_name)` collision at `registry.py:377-381`. Outside callers reach the registry only through the public surface (`get`, `model_for_type`, `iter_types`, `primary_for`, `types_for`, `models_with_multiple_types`, `get_definition`, `iter_definitions`, `iter_pending_relations`, `get_enum`, `is_finalized`, and the `register_*` / `unregister` / `clear` / `mark_finalized` mutators); the `_types`/`_primaries`/`_models`/`_definitions`/`_pending`/`_enums` dicts are never reached directly from outside this file. `register_with_definition` is the only intra-module caller of public `register`; outside callers always go through `register_with_definition` (the only one in `django_strawberry_framework/` is `types/base.py:247`).
- **New helpers considered.** Two adjacent "drop empty list" idioms (`registry.py:181-182` and `registry.py:302-303`) are intentional inline duplication of the lock-step invariant — extracting a `_drop_if_empty(model)` helper would obscure the comment at `registry.py:176-178` that justifies the invariant for `unregister`'s clean-up. The 0.0.6 review reached the same conclusion; no change in 0.0.7.
- **Duplication risk in the current file.** Four distinct "already registered" phrasings still co-exist: the `_already_registered` template (`registry.py:79`), the primary-flip phrasing (`registry.py:127-129`), the duplicate-primary phrasing (`registry.py:134-137`, updated in 0.0.7), and `register_definition`'s phrasing (`registry.py:272`). The 0.0.6 project pass deferred-with-no-trigger on consolidating; restated here as a Low forward only. The 0.0.7 phrasing change to the duplicate-primary message did not alter the count of distinct phrasings (no consolidation, just a more triage-friendly wording). The repeated-string-literal scan returns zero hits at the helper boundary (different `{label}` substitutions and different f-string shapes mean no two raise sites share an exact prefix or suffix). Tests at `tests/test_registry.py:769,784,795,810,1004` pin each substring.

### Other positives

- **Static helper coverage matches scope.** The helper output at `docs/shadow/django_strawberry_framework__registry.overview.md` flags two control-flow hotspots — `register` at 62 lines / 7 branches and `unregister` at 43 lines / 3 branches — and every branch is covered by a dedicated test in `tests/test_registry.py`. The Django/ORM marker table is dominated by docstring mentions of `DjangoType`; no live ORM call lives in this file (the module is a pure dict-shaped registry, as `AGENTS.md` and `START.md` describe). Zero repeated string literals across the file. Zero TODO comments.
- **Thread/process-safety contract is explicit at the class boundary.** The class docstring at `registry.py:34-41` documents the unlocked-but-safe invariant — every production-path mutation runs at import time from `DjangoType.__init_subclass__`, which is single-threaded module loading. `_check_mutable` at `registry.py:52-65` enforces the defense-in-depth guard and fires from every public mutator: `register` (`registry.py:118`), `unregister` (`registry.py:172`), `register_definition` (`registry.py:269`), `register_with_definition` via the inner `register` call, `add_pending_relation` (`registry.py:321`), `discard_pending` (`registry.py:343`), `register_enum` (`registry.py:373`). `clear` deliberately bypasses the guard for test teardown.
- **Primary-ambiguity contract is partitioned at the right seam.** Two of the four GLOSSARY.md `Meta.primary` ambiguity rules are pinned at registration time (`registry.py`: rule 1 by `register` allowing single-type-no-primary, rule 3 by the duplicate-primary raise at `registry.py:131-138`); the other two are pinned at finalize time (`types/finalizer.py`: rule 2 by `_audit_primary_ambiguity` accepting single-primary, rule 4 by raising on multi-type-no-primary). `registry.py` exposes the three helpers the finalizer needs — `primary_for`, `types_for`, `models_with_multiple_types` — without leaking the internal `_types`/`_primaries` dicts. Tests at `tests/test_registry.py:751-774` and `tests/test_registry.py:1060-1129` lock both halves.
- **Idempotency of `register` is documented and pinned.** `register`'s docstring at `registry.py:88-117` enumerates the four behavior branches (first registration, idempotent re-register, second type same model, primary collision) and the return-value contract (`True` when state was added, `False` for no-op idempotent re-register). The primary-flip-on-idempotent-re-register guard at `registry.py:123-129` rejects mismatched flag values in both directions — pinning that primary status is a *declaration*, not a mutable property — and is locked by `tests/test_registry.py:777-796`.
- **`register_with_definition` rollback semantics are tight.** The wrapper at `registry.py:275-309` snapshots `pre_primary` before `register`, captures the `appended` flag from `register`'s return value, and on `register_definition` failure rolls back exactly the state added by *this* call: a pre-existing idempotent registration survives a re-register-with-different-definition failure intact (`tests/test_registry.py:855-873`); a pre-existing primary is restored when a NEW non-primary type's `register_definition` fails (`tests/test_registry.py:820-852`). The anchor comment at `registry.py:298` makes the inverse-of-register invariant explicit so a future side-effect addition to `register` is forced into review of this block.
- **`clear()` correctness covers every map.** The body at `registry.py:399-405` resets `_types`, `_primaries`, `_models`, `_enums`, `_definitions`, `_pending`, and `_finalized`. Test coverage at `tests/test_registry.py:150-169` and `tests/test_registry.py:1008-1017` locks the post-clear empty-state snapshot, including the `_primaries` reset and the `_finalized` flag flip back to `False`.
- **`unregister` symmetry with `register`.** The body at `registry.py:172-186` is the inverse of `register`: pop from `_models`, remove from `_types[model]` (popping the empty list), drop the primary slot if the unregistered type held it, drop the definition, and rebuild `_pending` to exclude records sourced from this type. The lock-step invariant between `_models` and `_types[model]` is documented inline at `registry.py:176-178` and lets `unregister` skip the `_types[model]`-present guard the rollback site explicitly carries. Coverage at `tests/test_registry.py:1141-1257` exhausts the multi-type-with-siblings, unknown-type-no-op, and post-finalize-raise paths.

### Summary

Registry is the bottom of the internal dependency graph and the package's only writable singleton; the contract surface is broad (24 methods across the type / definition / pending / enum / lifecycle quadrants) but every method has a docstring and a dedicated test. No High findings — the file is structurally unchanged from the verified 0.0.6 baseline, with one targeted 0.0.7 phrasing improvement on the duplicate-primary error message. Two Mediums: (1) the GLOSSARY.md `Meta.primary` rule 3 quote at `docs/GLOSSARY.md:668` still names the pre-0.0.7 message verbatim — documentation-vs-code drift on a publicly-enumerated contract; (2) `unregister(primary_for_multi)` leaves the registry in a re-registration-required state by design but the contract has no regression test pinning that `finalize_django_types` rejects the resulting state. Three Lows are localized polish: a missing "intentional `_check_mutable` bypass" sentence on `clear`'s docstring; a restated forward to the project pass on the four "already registered" phrasings; and an `iter_pending_relations` wording suggestion. Thread/process safety, key-shape consistency, TYPE_CHECKING cycle avoidance, idempotency, primary-ambiguity partitioning, and rollback semantics are all solid.

---

## Fix report (Worker 2)

### Files touched
- `docs/GLOSSARY.md:668` — replaced the pre-0.0.7 `"<class> is already declared primary as <existing>"` substring with the verbatim 0.0.7 message `"Cannot register <class> as primary for <model>; <existing> is already the primary type"`, matching `registry.py:131-138` and the `tests/test_registry.py:769` substring assertion. Documentation-only fix per Worker 1's M1 prose ("`registry.py` already lines up with the test suite ... only the GLOSSARY entry lags").
- `tests/test_registry.py` — added `test_unregister_of_primary_leaves_state_that_audit_rejects` (placed between `test_unregister_keeps_siblings_intact_in_multi_type_case` and `test_unregister_is_noop_on_unknown_type` to co-locate the audit-rejection coverage with the snapshot test that previously stopped at the post-unregister state). Pins the contract narrated by `registry.py:168-170`: registers three `DjangoType` subclasses with the first as primary, unregisters the primary, then calls `finalize_django_types()` and asserts the canonical ambiguity error fires (model + two surviving siblings + actionable fix sentence).

### Tests added or updated
- `tests/test_registry.py::test_unregister_of_primary_leaves_state_that_audit_rejects` — pins that `unregister(primary_for_multi)` leaves a registry state `finalize_django_types()` refuses via the `_audit_primary_ambiguity` ambiguity raise. Three `DjangoType` subclasses are needed (not two) so the surviving-sibling list still exceeds two and triggers `models_with_multiple_types()`.

### Validation run
- `uv run ruff format .` — pass (118 files left unchanged; the new test slotted in cleanly under line-length 110 / COM812).
- `uv run ruff check --fix .` — pass (all checks passed).
- No pytest run per `AGENTS.md` standing rule; Worker 3 will exercise the new test on the verification pass.

### Notes for Worker 3
- Shadow file used: `docs/shadow/django_strawberry_framework__registry.overview.md` (Worker 1's overview re-read for the unregister/audit seam; no new shadow refresh needed).
- Test placement intentionally uses the **global** `registry` (not `fresh_registry`) so `DjangoType.__init_subclass__` populates real definitions and the live `finalize_django_types()` path runs end-to-end. The `_isolate_global_registry` autouse fixture (`tests/test_registry.py:34-39`) handles teardown.
- L1 (`clear()` docstring bypass note), L2 (forward to project pass on the four "already registered" phrasings), and L3 (`iter_pending_relations` wording polish) are all comment-pass deferrals per Worker 1's own prose ("comment-pass polish", "forwarded again", "defer until the comment pass") — no edit this sub-pass.
- M1 (GLOSSARY drift) was a documentation-only edit; the implementation at `registry.py:131-138` and the pinning test at `tests/test_registry.py:769` were already aligned — only the public spec entry lagged.

---

## Verification (Worker 3)

### Logic verification outcome
- **M1 (GLOSSARY drift)** — accepted. `docs/GLOSSARY.md:668` now reads `ConfigurationError("Cannot register <class> as primary for <model>; <existing> is already the primary type")`, matching the live raise at `registry.py:134-137` (`f"Cannot register {type_cls.__name__} as primary for {model.__name__}; "` + `f"{existing_primary.__name__} is already the primary type"`) and the substring pin at `tests/test_registry.py:769`. Documentation-only diff; no source/test logic change beyond the GLOSSARY swap.
- **M2 (missing audit-after-unregister regression)** — accepted. `tests/test_registry.py:1229` (`test_unregister_of_primary_leaves_state_that_audit_rejects`) registers three `DjangoType` subclasses (`ItemTypeA` primary, `ItemTypeB`, `ItemTypeC`) against `Item`, snapshots `primary_for(Item) is ItemTypeA` + `types_for(Item) == (ItemTypeA, ItemTypeB, ItemTypeC)`, calls `registry.unregister(ItemTypeA)`, re-snapshots `primary_for(Item) is None` + `types_for(Item) == (ItemTypeB, ItemTypeC)`, then asserts `pytest.raises(ConfigurationError)` on `finalize_django_types()` with the canonical ambiguity-header substring ("Models with multiple registered DjangoType subclasses and no primary"), model name (`Item`), both surviving sibling names (`ItemTypeB`, `ItemTypeC`), and the verbatim fix sentence ("Declare Meta.primary = True on exactly one of the registered DjangoType subclasses."). All five substrings grep-match `django_strawberry_framework/types/finalizer.py:96-99`. Behavior pinned, not smoke — the test fails if a future maintainer auto-promotes the next sibling on unregister, which was Worker 1's stated worry. Test placement (`tests/test_registry.py:1229`, between the multi-type-siblings snapshot test and the noop-unknown-type test) co-locates the audit-rejection coverage with the snapshot test that previously stopped at the post-unregister state, per Worker 2's `### Files touched` rationale. Global-`registry` usage (not `fresh_registry`) is correct: `DjangoType.__init_subclass__` writes to the global, the live `finalize_django_types()` path needs that, and the `_isolate_global_registry` autouse fixture at `tests/test_registry.py:34-39` handles teardown.
- **L1 / L2 / L3** — all deferred to the comment pass with trigger phrasing matching Worker 1's verbatim prose ("comment-pass polish" at `rev-registry.md:63`; "forwarded again" at line 80; "defer until the comment pass" at line 84). Worker 2's `### Notes for Worker 3` quote at line 127 echoes all three verbatim. No logic change required this sub-pass.

### DRY findings disposition
The single DRY entry (deferred extraction of `_rollback_register(...)` until a second atomic-pair wrapper exists) is carried forward unchanged; Worker 2 did not need to touch the rollback block this cycle. Trigger condition unchanged.

### Temp test verification
- No temp test files created under `docs/review/temp-tests/registry/`. M2's regression is a permanent suite addition at `tests/test_registry.py:1229`; M1 is a documentation-only fix with no test-level surface.

### Verification outcome
`logic accepted; awaiting comment pass`

---

## Comment/docstring pass

### Files touched
- `django_strawberry_framework/registry.py:392-400` — added a single sentence to `clear()`'s docstring naming the intentional `_check_mutable` bypass and calling out that this is the only public mutator that bypasses the guard, per Worker 1's L1 recommended wording ("a one-sentence addition to the `clear` docstring explicitly naming the intentional bypass — small comment-pass polish, no logic change").
- `django_strawberry_framework/registry.py:324-333` — expanded `iter_pending_relations`'s mutation-safety hedge to explicitly name the rebuild-list-on-discard mechanism (`discard_pending` rebinds `self._pending` to a fresh list, leaving any in-flight `yield from` iterating the original list object), per Worker 1's L3 recommended wording ("name the rebuild-list-on-discard mechanism explicitly so a future reader does not have to infer it from `discard_pending`'s body").

### Per-finding dispositions
- L1 (`clear()` docstring missing intentional-bypass note) — accepted and edited per Worker 1's recommended wording; one-sentence addition co-located with the test-only/autouse-fixture context already in the docstring.
- L2 (`register_definition` collision phrasing divergence) — forwarded to the project pass per Worker 1's explicit instruction ("forwarded again to `rev-django_strawberry_framework.md` only if the project pass wants to revisit the 'pluralized vs collapsed' decision"); no in-cycle edit. The four phrasings stay as the 0.0.6 cycle's "the four phrasings stay" decision.
- L3 (`iter_pending_relations` wording polish) — accepted and edited per Worker 1's recommended wording; the rebuild-list-on-discard mechanism is now named in-prose rather than left for inference from `discard_pending`'s body.

### Validation run
- `uv run ruff format .` — pass (118 files left unchanged).
- `uv run ruff check --fix .` — pass (all checks passed).

### Notes for Worker 3
- Comments/docstrings only — no logic edits this sub-pass. The L1 sentence is co-located with `clear()`'s existing test-teardown context; the L3 wording extends the existing hedge without breaking the "Typical consumers ... drain into a list before mutating" recommendation that follows.
- L2 is recorded as forwarded-to-project-pass with no in-cycle edit, matching Worker 1's explicit "forwarded again" framing. The `_already_registered` template, the primary-flip phrasing, the duplicate-primary phrasing, and `register_definition`'s phrasing all remain test-pinned by substring at `tests/test_registry.py:769,784,795,810,1004` per Worker 1's enumeration.
- No new tests this sub-pass; the L1/L3 docstring edits describe behavior already pinned by the M2 logic-pass test (`test_unregister_of_primary_leaves_state_that_audit_rejects` at `tests/test_registry.py:1229`) plus the pre-existing `clear`/`discard_pending` coverage at `tests/test_registry.py:150-169,1008-1017`.

---

## Changelog disposition

### State
`Not warranted`.

### Reason
Three lined-up citations:

1. **AGENTS.md** — "Do not update CHANGELOG.md unless explicitly instructed" (line 21 of `AGENTS.md`).
2. **Plan silence** — `docs/review/review-0_0_7.md` does not authorize a `CHANGELOG.md` edit for the registry cycle (the active plan names this cycle as `rev-registry.md` without any "warranted-and-edited" annotation; the dispatch prompt similarly does not authorize a changelog edit).
3. **Prior 0.0.7 precedent chain** — every preceding 0.0.7 review cycle (`rev-_django_patches.md`, `rev-apps.md`, `rev-conf.md`, `rev-exceptions.md`, `rev-list_field.md`) landed `Not warranted` for changes of the same internal/docstring/test-polish shape. The 0.0.7 logic-pass landings in this cycle (the GLOSSARY.md drift fix at line 668 and the new regression test at `tests/test_registry.py:1229`) are both documentation-of-existing-behavior and test additions, not consumer-visible contract changes — the live `registry.py:131-138` error message has been in `tests/test_registry.py:769`'s substring assertion since the 0.0.7 phrasing improvement; the GLOSSARY edit aligns the public spec with code-already-shipped, and the regression test pins a contract the docstring at `registry.py:168-170` already narrates. The comment-pass edits (L1 and L3) are pure docstring polish with no behavioural surface.

The internal-only shape of this cycle's edits matches AGENTS.md's `Not warranted` criteria ("docstring polish ... additive substring-compatible wording") and the plan's silence is the second leg; the prior precedent chain is the third leg that hardens the disposition against a Worker 3 nit on the strength of leg two.

### What was done
No `CHANGELOG.md` edit.

### Validation run
- `uv run ruff format .` — pass (no changes since the comment-pass run; same 118-files-unchanged result).
- `uv run ruff check --fix .` — pass (all checks passed).

---

## Iteration log

## Verification (Worker 3, pass 2)

### Comment-pass verification outcome
- **L1 (`clear()` docstring intentional-bypass note)** — accepted. `django_strawberry_framework/registry.py:400-402` now reads `_check_mutable is intentionally not called so test teardown can reset a finalized registry; this is the only public mutator that bypasses the guard.`, co-located with the existing test-teardown/autouse-fixture context. Wording matches Worker 1's L1 recommendation at `rev-registry.md:63` ("a one-sentence addition to the `clear` docstring explicitly naming the intentional bypass — small comment-pass polish, no logic change") and the class-level invariant at `registry.py:34-41`. The `## What looks solid` bullet at `rev-registry.md:97` already framed `clear` as the deliberate exception to `_check_mutable`; the docstring now states it explicitly.
- **L2 (`register_definition` collision phrasing divergence)** — accepted as forwarded-to-project-pass with no in-cycle edit. Worker 2's `Per-finding dispositions` quotes Worker 1's "forwarded again to `rev-django_strawberry_framework.md` only if the project pass wants to revisit the 'pluralized vs collapsed' decision" verbatim. The four phrasings at `registry.py:79,127-129,134-137,272` remain test-pinned by substring per Worker 1's enumeration at `rev-registry.md:92` (`tests/test_registry.py:769,784,795,810,1004`); no consolidation in 0.0.7, matching the 0.0.6 cycle's "the four phrasings stay" decision.
- **L3 (`iter_pending_relations` rebuild-list mechanism)** — accepted. `django_strawberry_framework/registry.py:328-332` now reads `... will observe a stale view because discard_pending rebinds self._pending to a fresh list, leaving any in-flight yield from iterating the original list object.` Wording matches Worker 1's L3 recommendation at `rev-registry.md:84` ("name the rebuild-list-on-discard mechanism explicitly so a future reader does not have to infer it from `discard_pending`'s body"). The "Typical consumers (the finalizer itself) drain into a list before mutating" recommendation that follows is preserved unbroken; `discard_pending` at `registry.py:344-345` does rebuild `self._pending` as a fresh list, confirming the mechanism named in the new docstring prose.

### Diff scope check
`git diff -- django_strawberry_framework/registry.py` shows exactly two hunks: lines 326-333 (`iter_pending_relations` docstring) and lines 394-400 (`clear()` docstring). No logic change, no other file touched in this sub-pass beyond the artifact itself. Diff matches Worker 2's claim at `## Comment/docstring pass` → `### Files touched`.

### Changelog verification outcome
`Not warranted`. `git diff -- CHANGELOG.md` is empty (verified). Worker 2's disposition cites three lined-up legs at `## Changelog disposition` → `### Reason`:
1. **AGENTS.md** — line 21, "Do not update CHANGELOG.md unless explicitly instructed".
2. **Plan silence** — `docs/review/review-0_0_7.md` does not authorize a `CHANGELOG.md` edit for the registry cycle.
3. **Prior 0.0.7 precedent chain** — `rev-_django_patches.md`, `rev-apps.md`, `rev-conf.md`, `rev-exceptions.md`, `rev-list_field.md` all landed `Not warranted` for internal/docstring/test-polish shape.

The two-citation bar is comfortably cleared (AGENTS.md + plan silence); the precedent chain is the third leg. The cycle's edits are documentation-only (GLOSSARY drift fix aligning the public spec to code-already-shipped, plus the regression test pinning a contract the docstring already narrates, plus L1/L3 docstring polish); the `Not warranted` framing matches the internal-only diff scope and does NOT inflate to "Warranted but deferred to maintainer" — correct three-state mapping.

### Validation run
- `uv run ruff format .` — pass (118 files left unchanged).
- `uv run ruff check --fix .` — pass (all checks passed).

### Verification outcome
`cycle accepted; verified`. Sets top-level `Status: verified`; marks the checklist box at `docs/review/review-0_0_7.md:98` for `registry.py`.
