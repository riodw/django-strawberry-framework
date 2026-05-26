# Review: `django_strawberry_framework/test/_wrap.py`

Status: verified

## DRY analysis

- Defer until a third lifecycle site grows the same predicate; then promote `_is_database_failure` from a `_django_patches`-private helper to a folder-level (or package-internal `_utils`) name. The carry-forward "Medium #1 candidate" from `rev-_django_patches.md` was pre-fixed in the working tree by the maintainer: `_wrap.py:27` now imports `_is_database_failure` from `_django_patches` instead of re-doing the bare `from django.test.testcases import _DatabaseFailure` shape. That consolidation is the same shape the prior cycle's DRY bullet anticipated ("when the wrap-time helper grows a second connection-aware primitive ... extract the shared ``isinstance(getattr(connection, name), _DatabaseFailure)`` primitive"), but the maintainer reached the consolidation by a different trigger — defensive-import-hygiene parallel rather than a new wrap-time primitive. The current factoring (predicate function lives in the unwrap-time module; wrap-time module imports it) is correct because (a) the predicate's defensive `_DatabaseFailure is None` fallback already lives in `_django_patches` and would be duplicated by a sibling copy in `_wrap.py`, and (b) the two modules' docstrings now jointly frame the shared predicate as the bridge between the two halves of the defense-in-depth (`_wrap.py:17-19` "Both halves share the same private ``_DatabaseFailure`` predicate"). Acting further now would over-engineer for a two-site primitive. The trigger is "a third Django lifecycle site (e.g. async cursor instrumentation, a `connections[alias].chunked_cursor` wrap at request time, or a future package-owned middleware that wraps a connection method) needs the same `_DatabaseFailure` predicate". When that lands, move `_is_database_failure` to a folder-local module (e.g. `django_strawberry_framework/_database_failure.py`) so neither lifecycle site owns the predicate by accident of historical introduction order. Cross-folder DRY scope; the canonical resolution home is the folder pass at `rev-test.md`.

## High:

None.

## Medium:

### `wrapper` type annotation overstates what the helper validates

Line 33 declares `wrapper: Callable[..., Any]`, but the function never validates that `wrapper` is callable — `setattr(connection, method_name, wrapper)` at line 136 accepts any object. The test suite documents the gap by passing `mock.sentinel.consumer_wrapper` (a non-callable sentinel) at `tests/test/test_wrap.py:35,57,80,100,145` and asserting installation succeeds; the type system would reject those calls if treated literally. A consumer who passes a typo (e.g. `connection.cursor` instead of `lambda: connection.cursor()`) or any non-callable object would silently install a broken `connection.<method>` attribute, and the failure mode is a delayed `TypeError: 'X' object is not callable` at the next `connection.cursor()` invocation — typically deep inside Django's ORM machinery, with no traceback line pointing at the wrap site.

Why it matters. The helper's whole reason to exist is to harden the wrap site against silent failure modes (specifically the `_DatabaseFailure` clobber that crashes `tearDownClass`). Allowing a wrong-shape `wrapper` to install silently re-introduces a similar class of silent failure at the same site — wrap-time deferred to call-time. The discrepancy between the type hint and the test fixture also means a `mypy --strict` consumer downstream would be forced to silence the type checker at every call site that uses the test idiom the docstring itself promotes (line 89 docstring `def my_wrapped_cursor(*args, **kwargs)` is callable, but tests show non-callable sentinels are accepted in practice).

Recommended change. Pick one of two reconcilations:

- **Tighten code to match annotation.** Add a `callable(wrapper)` check that raises `TypeError(f"safe_wrap_connection_method() received a non-callable wrapper: {wrapper!r}")` before the `_is_database_failure(current)` branch at line 134. Update the four test sites that pass `mock.sentinel` to wrap them in a `lambda: mock.sentinel.consumer_wrapper` or replace with a real callable like `mock.Mock()`. The recommended-test shape is a new `test_safe_wrap_connection_method_raises_on_non_callable_wrapper` pin.
- **Widen annotation to match code.** Change line 33 to `wrapper: object` (or a `Callable[..., Any] | object` union — leaning toward plain `object` since the helper never introspects `wrapper`). Add a docstring sentence under "Args" naming the deliberate non-validation ("``wrapper`` is installed verbatim; the helper does not require it to be callable — non-callable wrappers will fail at the next invocation site, which is the same fail-late shape Django itself ships when the method is replaced via raw ``setattr``"). Keep the tests as-is.

Path (a) is the higher-quality fix because it surfaces the typo at the wrap site instead of the call site. Path (b) is the pragmatic option if the test convenience is load-bearing. The artifact recommends (a).

```django_strawberry_framework/test/_wrap.py:30-34
def safe_wrap_connection_method(
    connection: BaseDatabaseWrapper,
    method_name: str,
    wrapper: Callable[..., Any],
) -> bool:
```

```django_strawberry_framework/test/_wrap.py:133-137
    current = getattr(connection, method_name)
    if _is_database_failure(current):
        return False
    setattr(connection, method_name, wrapper)
    return True
```

## Low:

### Multi-call idempotency contract is undocumented

The helper has no documented behavior for repeat calls with the same `(connection, method_name)` pair. A consumer who calls `safe_wrap_connection_method(connection, "cursor", w1)` and then later `safe_wrap_connection_method(connection, "cursor", w2)` will get `True` returned twice and `connection.cursor` will end up as `w2` — `w1` is silently overwritten because the helper's only refusal condition is "Django's ``_DatabaseFailure`` is in place at this attribute". The behavior is correct for the intended single-`setUp`-per-test pattern, but the docstring's "Restoration semantics" example (lines 85-110) implies a single-wrap-per-test lifecycle and never says what happens if the consumer wraps twice.

Defer until either (a) a second consumer code path in the example project (or in `django_strawberry_framework/test/`) exercises a multi-wrap pattern, or (b) the planned `GraphQLTestCase` (`docs/GLOSSARY.md:891`, scheduled for `0.0.12`) wraps a connection method on a class that consumers might subclass and double-wrap. The trigger condition is "a second wrap-time site lands inside the package and shares a connection.<method> with an existing consumer wrap". When that lands, the docstring should grow a "Repeat calls overwrite previous wrappers from this helper; only Django's ``_DatabaseFailure`` is treated as immutable. Save the prior method explicitly if you need to restore it." paragraph under "Restoration semantics".

### Docstring "Restoration semantics" example does not pin the `_DatabaseFailure`-already-installed branch

The code-block example at lines 88-110 shows the consumer saving `self._original_cursor = self._connection.cursor` BEFORE calling `safe_wrap_connection_method`. If Django's `setUpClass` already installed `_DatabaseFailure` at the cursor (the exact branch the helper exists to guard), the consumer's `self._original_cursor` is itself a `_DatabaseFailure` wrapper — and the `tearDown` block at lines 107-110 restores the `_DatabaseFailure` wrapper to the cursor under the `if self._wrapped:` guard (which is `False` in this branch, so the restore is correctly skipped). The example is functionally correct, but a casual reader could miss that `self._original_cursor` is a `_DatabaseFailure` in the declined branch and assume the example is buggy. A one-sentence comment in the example saying "(when Django wrapped first, ``self._original_cursor`` is itself a ``_DatabaseFailure`` and ``self._wrapped`` is ``False`` — the ``tearDown`` block correctly skips the restore)" would close the loop.

Defer with no behavioral trigger — pure docstring polish. The trigger condition is "the next time the artifact's comment-pass sub-cycle touches the ``_wrap.py`` docstring's Restoration semantics block". Acting now would re-open the just-closed comment pass that introduced the docstring shape; folding this into the next docstring touch is cheaper than a standalone edit.

### Module-docstring framing depends on `_django_patches.py:120` `_is_database_failure` existing

Line 27 imports `_is_database_failure` from `_django_patches`. The module docstring (lines 17-19) frames the predicate as a load-bearing bridge between the two halves of the defense-in-depth. If a future refactor moved `_is_database_failure` out of `_django_patches` (e.g. into a folder-local `_database_failure.py` per the DRY analysis trigger above), the import path here would need to change and the module docstring's "Both halves share the same private ``_DatabaseFailure`` predicate" sentence would still read correctly but the citation chain `_wrap.py:17-19` → `_django_patches.py:120` would shift. Not a defect today — the citation chain is correct against the current source — but worth pinning in the DRY-analysis trigger above so the future refactor lands both halves atomically.

Defer; gated on the DRY-analysis trigger ("a third Django lifecycle site needs the same `_DatabaseFailure` predicate"). When that trigger fires, the predicate-move must update three sites in one diff: the new home, the import in `_django_patches.py`, and the import + module docstring citation in `_wrap.py`.

## What looks solid

### DRY recap

- **Existing patterns reused.** The wrap-time predicate at `_wrap.py:134` reuses `_is_database_failure` from `_django_patches.py:120-122`, which itself encapsulates the `_DatabaseFailure is not None and isinstance(method, _DatabaseFailure)` shape. The factoring is correct: a sibling-copy `isinstance` check in `_wrap.py` would have re-introduced the bare-symbol-import gap the prior cycle's Medium #2 closed in `_django_patches.py`. The current shape has exactly one defensive `try/except ImportError` for the private symbol in the package (`_django_patches.py:109-117`), and both lifecycle sites consume the predicate through one canonical function.
- **New helpers considered.** A separate `_save_and_wrap_connection_method(connection, method_name, wrapper) -> (callable | None)` helper that returns the saved original (Some/None semantics) for the consumer was considered and rejected for now. The current `bool`-returning contract is simpler and the consumer's `try/finally` save-and-restore idiom (per the docstring example at lines 88-110) is a documented Django pattern that doesn't need package-side help today. Re-triage if a second `0.0.12`-shipped utility (`GraphQLTestCase`) lands and ends up duplicating the save-and-restore boilerplate.
- **Duplication risk in the current file.** None — the file has exactly one function and one predicate call. The `setattr` at line 136 and the `getattr` at line 133 are a paired primitive operating on the same attribute name, which is the canonical Django connection-method-wrap shape and matches `django-debug-toolbar`'s `wrap_cursor` precedent cited at lines 76-79.

### Other positives

- The function signature uses positional-only-friendly ordering (`connection`, `method_name`, `wrapper`) which matches the intuitive "what, where, with what" reading order. No defaulted parameters; the caller must supply all three. Good ergonomics for a defensive helper that should not silently accept defaults.
- Type hints are present on all three arguments and the return. Even with the type-annotation-vs-runtime-behavior Medium above, the explicit `BaseDatabaseWrapper` annotation on `connection` is correct and pins the precise Django-internal type the helper operates on; a consumer passing `connections` (the wrapper container) instead of `connections["default"]` (a `BaseDatabaseWrapper`) would get a type-checker error at the wrap site.
- The module docstring (lines 1-20) is concise and cites `_django_patches` as the canonical home of the defense-in-depth framing rather than duplicating that framing here. Cross-references to the upstream ticket and `django-debug-toolbar` precedent live in `_django_patches.py:29-91` (the package-internal patch module); this module's docstring intentionally stays tighter and forwards. The framing discipline matches the prior cycle's "two-tier visibility" pattern (public surface module = consumer-facing wrap helper; private patch module = full ticket/precedent narrative).
- The test suite at `tests/test/test_wrap.py` (5 tests) covers the four behavioral branches: happy-path install (`test_safe_wrap_connection_method_installs_wrapper_when_no_database_failure`), declined-on-`_DatabaseFailure` (`test_safe_wrap_connection_method_declines_when_database_failure_in_place`), private-symbol-missing fallback (`test_safe_wrap_connection_method_installs_when_database_failure_symbol_missing`), and non-cursor methods (`test_safe_wrap_connection_method_works_on_arbitrary_method_names`). The fifth test `test_safe_wrap_connection_method_pairs_with_unwrap_time_patch_for_defense_in_depth` is the end-to-end composition pin — it wires the wrap-time helper and the unwrap-time patch together against a synthetic narrow-`databases` `TransactionTestCase` subclass, proving the two halves compose. That last test is the load-bearing one for the package's "auto-protected at both ends" promise in the module docstring.
- The `mock.patch.object(_django_patches, "_DatabaseFailure", None)` idiom in the symbol-missing test (`tests/test/test_wrap.py:83`) mocks the predicate-side state via the canonical sentinel introduced by `_django_patches.py:117` (`_DatabaseFailure = None  # type: ignore[assignment,misc]`). Mocks behavior at the predicate boundary (per AGENTS.md line 9 "mock behaviour, not the class") rather than re-implementing the predicate; the helper's `_is_database_failure(current)` call short-circuits via the `_DatabaseFailure is not None` clause and returns the same answer the production path would.
- The function has exactly one branch (the `_is_database_failure(current)` gate). Control flow stays well under the optimizer-folder Medium-tier complexity threshold; the static helper's "control-flow hotspots" line at the shadow overview (108-line function span, 1 branch node) is a docstring-length artifact rather than a complexity signal — the executable body is four lines.

### Summary

`_wrap.py` is the wrap-time half of the package's Trac #37064 defense-in-depth and the file is tightly factored: one function, one predicate call, one branch, and a docstring that defers the heavy framing to `_django_patches.py`. The prior cycle's carry-forward "M1 candidate" (bare `_DatabaseFailure` import at line 23) was pre-fixed in the working tree by the maintainer — the file now imports the shared `_is_database_failure` predicate from `_django_patches`, which already carries the `try/except ImportError` defensive guard from the previous cycle's Medium #2 fix. That collapses the per-file half of the defensive-import-hygiene parallel to a "verified" disposition. The one new Medium is a wrap-time-vs-call-time silent-failure shape introduced by the `wrapper: Callable[..., Any]` type annotation declaring a stricter contract than the runtime path enforces. Three trigger-gated Lows defend the deliberate cross-module factoring against future-reviewer false positives. DRY analysis is cross-folder; canonical resolution home is `rev-test.md` (the folder pass).

---

## Fix report (Worker 2)

### Files touched
- `django_strawberry_framework/test/_wrap.py:132-152` — added `if not callable(wrapper): raise TypeError(...)` early-validate as the first statement of the function body (before the `getattr(connection, method_name)` lookup, so no connection state is touched on the raise path). Added a "Raises" block to the docstring naming the wrap-time-vs-call-time shape and the typo example. Type annotation `Callable[..., Any]` retained — runtime path now matches the annotation.

### Tests added or updated
- `tests/test/test_wrap.py::test_safe_wrap_connection_method_raises_on_non_callable_wrapper` — new regression test pinning that `safe_wrap_connection_method(connection, "cursor", 42)` raises `TypeError` with `match="non-callable wrapper"`, and asserting `connection.cursor` is untouched on the raise path.
- Four pre-existing tests updated to wrap consumer sentinels in `mock.Mock(name=...)` (callable) instead of `mock.sentinel.<name>` (non-callable): `test_safe_wrap_connection_method_installs_wrapper_when_no_database_failure`, `test_safe_wrap_connection_method_declines_when_database_failure_in_place`, `test_safe_wrap_connection_method_installs_when_database_failure_symbol_missing`, `test_safe_wrap_connection_method_works_on_arbitrary_method_names`, and the end-to-end composition test's inline `mock.sentinel.consumer_wrapper` call site. `mock.sentinel.untouched_original` inside the e2e test is kept as the wrapped-original payload because it is never validated by the helper — only `wrapper` flows through the new callable check.

### Validation run
- `uv run ruff format .` — 118 files left unchanged.
- `uv run ruff check --fix .` — All checks passed.
- No pytest per AGENTS.md line 14.

### Notes for Worker 3
- M1 path chosen: Worker 1's recommended path (a) — tighten code to match annotation. Path (b) was explicitly rejected by Worker 1's "The artifact recommends (a)" conclusion at line 26.
- Carry-forward "M1 candidate" from `rev-_django_patches.md` (bare `_DatabaseFailure` import) was already pre-fixed in the working tree per Worker 1's DRY-analysis prose at line 7; not touched this cycle.
- Lows L1-L3 are all explicitly trigger-gated forward-looking carry-forwards per Worker 1's own framing — no in-cycle edit required for the comment pass. L1 trigger = a second wrap-time site lands inside the package and shares a connection.<method> with an existing consumer wrap (two arms: (a) example-project multi-wrap path, or (b) the planned `GraphQLTestCase` at `docs/GLOSSARY.md:891` for `0.0.12`). L2 trigger = next docstring touch on `_wrap.py` Restoration semantics block (pure docstring polish). L3 trigger = the DRY-analysis trigger fires (predicate moves out of `_django_patches`).
- `mock.Mock(name=...)` is the canonical callable test-double idiom and matches AGENTS.md line 9 "mock behaviour, not the class" — the helper never invokes `wrapper`, so a `Mock` whose `__call__` returns the default `Mock()` is structurally indistinguishable from the consumer's real wrapper for the wrap-time predicate.
- Shadow file not used during this fix — the function is 4 executable lines and the artifact's source citations were sufficient.

---

## Verification (Worker 3)

### Logic verification outcome
M1 fix is correctly implemented at the production-code level. `git diff -- django_strawberry_framework/test/_wrap.py` shows: (a) `callable(wrapper)` guard raising `TypeError(f"safe_wrap_connection_method() received a non-callable wrapper: {wrapper!r}")` is the FIRST statement inside the function body (artifact line 134-137), before the `getattr(connection, method_name)` lookup — so no connection state is mutated on the raise path; (b) the error message contains the substring "non-callable wrapper" which matches the regression test's `pytest.raises(TypeError, match="non-callable wrapper")` pin; (c) the docstring grows a "Raises:" block naming `TypeError` and the typo example. Type annotation `Callable[..., Any]` retained — runtime path now matches the annotation, per artifact line 22-23's recommended path (a).

`git diff -- tests/test/test_wrap.py` shows the regression test `test_safe_wrap_connection_method_raises_on_non_callable_wrapper` exists at the bottom of the file, passes `42` as the wrapper argument, asserts the `TypeError` with `match="non-callable wrapper"`, and asserts `connection.cursor is original_cursor` after the raise to pin the no-state-mutation property. Four pre-existing tests migrated from `mock.sentinel.consumer_wrapper` / `mock.sentinel.chunked_wrapper` to `mock.Mock(name="consumer_wrapper")` / `mock.Mock(name="chunked_wrapper")` — `mock.Mock` is callable, satisfying the new guard. `mock.sentinel.untouched_original` inside the end-to-end composition test is correctly retained as the wrapped-original payload (it never flows through the `wrapper` parameter, only through `_DatabaseFailure(sentinel_original, "test message")` as the wrapped target).

### DRY findings disposition
DRY analysis (artifact line 7) defers cross-folder consolidation to `rev-test.md` with a single-arm trigger ("a third Django lifecycle site (e.g. async cursor instrumentation, a `connections[alias].chunked_cursor` wrap at request time, or a future package-owned middleware that wraps a connection method) needs the same `_DatabaseFailure` predicate"). The trigger's three example sites are enumerated for grep-discoverability. Carried forward — no in-cycle edit required.

### Temp test verification
- No temp tests created. Worker 2's regression test is the load-bearing pin for M1 and lives at the permanent suite path (`tests/test/test_wrap.py:163-186`) per AGENTS.md line 6.

### L1-L3 trigger phrasing verification
**Rejection: L1 trigger swap.** Worker 2's `### Notes for Worker 3` (artifact line 104) restates the three Lows' triggers but **swaps L1's trigger with L3's**:

- Worker 2's "L1 trigger" reads: "third Django lifecycle site needs the same `_DatabaseFailure` predicate". This is **L3's** trigger (artifact line 62: "gated on the DRY-analysis trigger ('a third Django lifecycle site needs the same `_DatabaseFailure` predicate')").
- **L1's actual trigger** (artifact line 50) reads: "a second wrap-time site lands inside the package and shares a connection.<method> with an existing consumer wrap", with a verbatim two-arm disjunctive in the preceding sentence: "(a) a second consumer code path in the example project (or in `django_strawberry_framework/test/`) exercises a multi-wrap pattern, or (b) the planned `GraphQLTestCase` (`docs/GLOSSARY.md:891`, scheduled for `0.0.12`) wraps a connection method on a class that consumers might subclass and double-wrap". Neither arm appears in Worker 2's restatement.
- Worker 2's "L2 trigger" ("next docstring touch on `_wrap.py` Restoration semantics block") matches L2's actual trigger at artifact line 56.
- Worker 2's "L3 trigger" ("the DRY-analysis trigger fires (predicate moves out of `_django_patches`)") is a paraphrase of L3's gating prose at line 62, but acceptable because the substantive trigger condition IS the DRY trigger and the DRY trigger phrase is itself preserved verbatim in the artifact's DRY analysis block.

The L1 swap silently drops the multi-call-idempotency-contract finding entirely — the future cycle would grep for "second wrap-time site" / "multi-wrap pattern" / "GraphQLTestCase" / "docs/GLOSSARY.md:891" against `### Notes for Worker 3` and find nothing, then re-derive the multi-wrap deferral from cold (or worse, close it out under the wrong trigger). Per the verifier's own memory pattern (worker-memory/worker-3.md, multiple entries): "disjunctive-arm preservation matters most because future cycles grep these triggers verbatim" / "silently dropping one arm narrows the deferral and is grounds for `revision-needed`". The L1 case is worse than a single arm dropped — both arms of L1's disjunctive are missing and the slot is occupied by L3's trigger.

### CHANGELOG diff
`git diff -- CHANGELOG.md` is empty (0 lines). Awaits the changelog disposition sub-pass after the comment pass is re-accepted.

### Validation run
- `uv run ruff format --check .` — 118 files already formatted.
- `uv run ruff check .` — All checks passed.
- pytest deferred per AGENTS.md line 14 (will run at the cycle-19 final-test-run gate).

### Verification outcome
`revision-needed`.

The M1 logic fix is correct on its own — the production code change, regression test, and four-test sentinel migration are all sound and ruff is clean. The blocker is the L1-L3 trigger restatement in `### Notes for Worker 3`: Worker 2 has placed L3's trigger ("third Django lifecycle site needs the same `_DatabaseFailure` predicate") under the L1 slot, and L1's actual trigger (with its verbatim two-arm disjunctive citing `GraphQLTestCase` at `docs/GLOSSARY.md:891` for `0.0.12`) is missing from the restatement entirely. Worker 2 must rewrite the L1 trigger line in `### Notes for Worker 3` to read verbatim: "L1 trigger = a second wrap-time site lands inside the package and shares a connection.<method> with an existing consumer wrap (two arms: (a) example-project multi-wrap path, or (b) the planned `GraphQLTestCase` at `docs/GLOSSARY.md:891` for `0.0.12`)". L2 and L3 restatements are acceptable as written.

No comment pass or changelog disposition is requested in this revision — the comment pass remains pending until the trigger-phrasing fix lands.

---

## Iteration log

## Verification (Worker 3, pass 2)

### Logic verification outcome
Re-verify scope is the L1 trigger phrasing restatement only. Spot-checked: `### Notes for Worker 3` at artifact line 104 now reads "L1 trigger = a second wrap-time site lands inside the package and shares a connection.<method> with an existing consumer wrap (two arms: (a) example-project multi-wrap path, or (b) the planned `GraphQLTestCase` at `docs/GLOSSARY.md:891` for `0.0.12`)." Both disjunctive arms present and grep-discoverable (`GraphQLTestCase`, `docs/GLOSSARY.md:891`, `0.0.12`, `multi-wrap`, `second wrap-time site` all match the verbatim phrasing previously demanded at pass-1 line 144). L2 ("next docstring touch on `_wrap.py` Restoration semantics block") and L3 ("the DRY-analysis trigger fires (predicate moves out of `_django_patches`)") restatements unchanged from pass 1 and previously accepted.

### Source + tests diff
`git diff --stat` shows `_wrap.py` 23 lines and `tests/test/test_wrap.py` 79 lines — identical scope to pass-1 logic verification (M1 fix preserved, no new logic edits introduced in this revision pass). The `callable(wrapper)` guard, `TypeError` message verbatim, "Raises:" docstring block, regression test `test_safe_wrap_connection_method_raises_on_non_callable_wrapper`, and four-test `mock.sentinel` → `mock.Mock(name=...)` migration all unchanged from prior verify.

### CHANGELOG diff
`git diff -- CHANGELOG.md` empty. Awaits the changelog disposition sub-pass after the comment pass is accepted.

### Validation run
- `uv run ruff format --check .` — 118 files already formatted.
- `uv run ruff check .` — All checks passed.

### Verification outcome
`logic accepted; awaiting comment pass`.

Top-level `Status:` remains `fix-implemented (awaiting comment pass)`. Worker 2's revision restored the verbatim L1 trigger phrasing with both disjunctive arms preserved per Worker 1's original line-50 prose; no other change introduced. Comment pass is the next sub-cycle.

---

## Comment/docstring pass

### Files touched
- None. The logic-pass diff already shipped the docstring update — the new "Raises:" block at `_wrap.py:133-138` names `TypeError`, the wrap-time-vs-call-time surfacing rationale, and the verbatim typo example (`connection.cursor` instead of `lambda: connection.cursor()`). The existing "Args" entry for `wrapper` at `_wrap.py:124-126` already says "The callable that should replace the named method." which is now a hard contract rather than a soft hint. The module docstring (`_wrap.py:1-20`) is scope-stable: the defense-in-depth framing, two-tier visibility, and shared `_DatabaseFailure` predicate are all unaffected by the M1 fix. The new regression test docstring (`tests/test/test_wrap.py:165-174`) already names the wrap-time-vs-call-time pinning and the `Callable[..., Any]` annotation-enforcement framing — no edit needed.

### Per-finding dispositions
- Medium 1 (wrapper type annotation overstates what the helper validates): logic-pass docstring update already landed the "Raises:" block in the same diff as the source fix. Per the cycle-18 logic-pass `## Fix report (Worker 2)` line 90, the docstring growth was bundled with the source change because the new contract is the docstring contract — splitting them would have produced an artifact-without-docstring intermediate state. No further docstring edit needed in this sub-pass.
- Low 1 (multi-call idempotency contract undocumented): trigger-gated forward-looking carry-forward per Worker 1 (artifact line 50). Trigger = a second wrap-time site lands inside the package and shares a connection.<method> with an existing consumer wrap (two arms: (a) example-project multi-wrap path, or (b) the planned `GraphQLTestCase` at `docs/GLOSSARY.md:891` for `0.0.12`). No edit.
- Low 2 (Restoration semantics example does not pin `_DatabaseFailure`-already-installed branch): trigger-gated forward-looking carry-forward per Worker 1 (artifact line 56). Trigger = next docstring touch on `_wrap.py` Restoration semantics block (pure docstring polish). This comment pass did not touch the Restoration semantics block — the M1 diff added a "Raises:" section AFTER the "Args"/"Returns" block, leaving the Restoration semantics example at `_wrap.py:81-116` unchanged. Trigger not satisfied. No edit.
- Low 3 (module-docstring framing depends on `_django_patches.py:120` `_is_database_failure` existing): trigger-gated forward-looking carry-forward per Worker 1 (artifact line 62). Trigger = the DRY-analysis trigger fires (a third Django lifecycle site needs the same `_DatabaseFailure` predicate). No edit.

### Validation run
- `uv run ruff format .` — 118 files left unchanged.
- `uv run ruff check --fix .` — All checks passed.

### Notes for Worker 3
- The "Raises:" block (`_wrap.py:133-138`) is the only docstring growth this cycle and it landed with the logic pass; no second-edit shape exists. Verification can confirm by `git diff -- django_strawberry_framework/test/_wrap.py` showing the docstring delta is exactly the four added lines naming `TypeError`.
- All three Lows are trigger-gated forward-looking per Worker 1's own framing — none of their triggers are satisfied in this cycle. The trigger phrases preserved verbatim above match the artifact's lines 50, 56, and 62 (and the cycle-18 revision-pass L1 trigger restatement at the bottom of `## Fix report (Worker 2)` line 104).
- No callable/non-callable docstring discussion appears in the test docstring at `tests/test/test_wrap.py:165-174` beyond what was already shipped in the logic-pass; the test's framing prose ("the type annotation ``Callable[..., Any]`` is now enforced at runtime") was authored at logic-pass time and remains accurate.

---

## Changelog disposition

### State
`Not warranted`.

### Reason
The M1 fix tightens a contract on `safe_wrap_connection_method` — public API per `docs/GLOSSARY.md:892` (the helper is named in the 0.0.7 entry as "consumer helper exported from `django_strawberry_framework.test`"). However the symbol shipped intra-cycle in the same 0.0.7 release window (commit `61973f8`, "Ship safe_wrap_connection_method consumer helper as wrap-time mirror of Trac #37064 patch"); this Medium is an intra-cycle pre-release correction tightening a brand-new symbol's runtime contract to match its already-shipped type annotation. Per the cycle-1 intra-cycle precedent (worker-memory pattern #5, captured under "0.0.7 cycles 2-12 consolidated merge"), corrections to NEW code in the same release that the release notes themselves describe in their post-correction shape are `Not warranted` — the release notes will say "ships `safe_wrap_connection_method` with `Callable[..., Any]` wrapper validation" as a unified description rather than carrying a separate "fixed: now validates wrapper at wrap time" entry.

Two-citation bar:
- `AGENTS.md` line 16: "Do not update CHANGELOG.md unless explicitly instructed." The dispatch prompt explicitly says "Per cycle-1 precedent: `Not warranted` (intra-cycle pre-release correction)." — no edit authorisation.
- `docs/review/review-0_0_7.md`: silent on changelog authorization for this cycle. No per-cycle line, no folder-pass override.

Precedent chain: the 0.0.7 `Not warranted` chain is now seventeen deep across cycles 1-17 (per the consolidated memory entry); this cycle continues the chain.

### What was done
No `CHANGELOG.md` edit.

Maintainer-paste-ready entry text (safety net for state reversal at Worker 3's verification, per the worker-memory pattern carried forward from rev-_django_patches.md):

#### Suggested CHANGELOG entry (not added — preserved here only in case the maintainer disagrees with `Not warranted` at release time)

```
### Fixed

- `safe_wrap_connection_method` now validates that ``wrapper`` is
  callable at the wrap site, raising ``TypeError`` instead of
  installing a non-callable object that would later fail deep inside
  Django's ORM machinery at the next ``connection.<method>()`` call.
  Tightens the runtime contract to match the already-published
  ``Callable[..., Any]`` type annotation.
```

### Validation run
- `uv run ruff format .` — 118 files left unchanged.
- `uv run ruff check --fix .` — All checks passed.

---

## Verification (Worker 3, pass 3)

### Logic verification outcome
Terminal pass scope is comment pass + changelog disposition. `git diff -- django_strawberry_framework/test/_wrap.py` unchanged from pass 2 (23 lines) — the comment pass correctly recorded `### Files touched: None` because the M1 logic-pass diff already shipped the new "Raises:" docstring block (`_wrap.py:133-138`) inline with the source fix. Verified by re-reading the diff: the four-line "Raises:" hunk names `TypeError`, the wrap-time-vs-call-time surfacing rationale, and the verbatim typo example (`connection.cursor` instead of `lambda: connection.cursor()`) — matching Worker 1's M1 recommended-change prose at artifact lines 22-23. The "Args" entry for `wrapper` ("The callable that should replace the named method.") is now a hard contract rather than a soft hint, which is the docstring shape Worker 1's recommended path (a) implies. Module docstring (`_wrap.py:1-20`) is scope-stable.

L1-L3 trigger restatement in the comment-pass `### Notes for Worker 3` preserves verbatim phrasing from pass 2's accepted block — L1's two-arm disjunctive (`GraphQLTestCase` at `docs/GLOSSARY.md:891` for `0.0.12` + example-project multi-wrap path), L2's "next docstring touch on `_wrap.py` Restoration semantics block", L3's "DRY-analysis trigger fires (predicate moves out of `_django_patches`)" all intact. L2 trigger-not-satisfied claim spot-checked: the M1 "Raises:" block was added AFTER the "Args"/"Returns" block at `_wrap.py:133-138`, leaving the Restoration semantics example at `_wrap.py:81-116` untouched — correct.

### Changelog disposition verification
State: `Not warranted`. `git diff -- CHANGELOG.md` empty (0 lines) — matches.

Two-citation bar cleared:
- `AGENTS.md` line 16: "Do not update CHANGELOG.md unless explicitly instructed." Cited at disposition line 205.
- `docs/review/review-0_0_7.md` silence on changelog authorization: Cited at disposition line 206. Confirmed silent by reading the plan file — line 114 (this cycle's checklist box) has no changelog directive.

Third-leg precedent chain claim ("seventeen deep across cycles 1-17") honest per worker-memory: cycles 1-17 explicitly enumerated across the memory file's consolidated entries. Internal-only framing matches the cycle's diff scope: the M1 fix tightens a runtime contract on a `0.0.7`-intra-cycle-shipped symbol (`safe_wrap_connection_method`, commit `61973f8`) before external publication — qualifies as "intra-cycle pre-release correction" per the cycle-1 precedent invoked at disposition line 202. The maintainer-paste-ready safety-net entry text under `#### Suggested CHANGELOG entry` is present, concise, and accurately describes the post-fix behavior (would let the maintainer flip to "Warranted and edited" at release time if they disagree with the pre-publication framing).

### Source + tests diff
`git diff --stat` shows `_wrap.py` 23 lines and `tests/test/test_wrap.py` 79 lines — identical scope to pass 2. M1 fix (callable guard + `TypeError` message + "Raises:" docstring block + regression test + four-test `mock.sentinel` → `mock.Mock(name=...)` migration) all unchanged.

### Validation run
- `uv run ruff format --check .` — 118 files already formatted.
- `uv run ruff check .` — All checks passed.
- pytest deferred per AGENTS.md line 14 (cycle-19 final-test-run gate).

### Verification outcome
`cycle accepted; verified`. Top-level `Status:` set to `verified`. Checkbox for `django_strawberry_framework/test/_wrap.py` ticked at `docs/review/review-0_0_7.md:114`.
