# Review: `django_strawberry_framework/conf.py`

Status: verified

## DRY analysis

- None — `conf.py` is at the minimum surface for its responsibility (one normalization helper `_normalize_user_settings` at `django_strawberry_framework/conf.py:50-83`, one accessor class `Settings` at `django_strawberry_framework/conf.py:86-144`, one signal receiver `reload_settings` at `django_strawberry_framework/conf.py:150-160`). The three `None`-vs-`_normalize_user_settings` call sites (`django_strawberry_framework/conf.py:100`, `django_strawberry_framework/conf.py:110-113`, `django_strawberry_framework/conf.py:123`) are structurally distinct: the constructor and `Settings.reload` use `None` to mean "defer to lazy reload on next access", while `Settings.user_settings`'s `getattr(django_settings, DJANGO_SETTINGS_KEY, None)` uses `None` to mean "missing key on Django settings". Folding the `None` guard into `_normalize_user_settings` itself would require collapsing those two distinct meanings and breaking the lazy-reload contract.

## High:

None.

## Medium:

None.

## Low:

### `__getattr__` recursion risk if the lazy `user_settings` read raises a non-mapping `ConfigurationError`

`Settings.__getattr__` (`django_strawberry_framework/conf.py:125-144`) reads `self.user_settings`. `self.user_settings` is a `@property`, so the access goes through `Settings.user_settings` (the descriptor) without re-entering `__getattr__` — that part is safe today. However, the recently extended docstring (lines 132-137) promises that a malformed `DJANGO_STRAWBERRY_FRAMEWORK` value lets `ConfigurationError` propagate by design. If a future refactor ever replaces the `@property` with a non-descriptor cache attribute (e.g. lazy assignment in `__init__`), `self.user_settings` would route through `__getattr__` and any in-progress lookup that raises `ConfigurationError` would land inside `__getattr__` mid-recursion. Today this is theoretical, not a bug. Worth a single inline comment near `django_strawberry_framework/conf.py:142` ("`self.user_settings` is a descriptor, not a `__getattr__`-driven lookup; keep it a `@property` to avoid recursive lookup on malformed config") to pin the contract for future readers. Not a logic change.

### Cross-module `None`-stance assertion in the module docstring belongs at the project pass

`django_strawberry_framework/conf.py:17-35` documents the package-wide `None` stance ("Two top-level consumer-input seams coerce `None` … `DJANGO_STRAWBERRY_FRAMEWORK = None` (this module …) and `Meta.optimizer_hints = None` in `types/base.py` …"). The local file cannot enforce or test the `types/base.py` half of this claim, and a future drift in `types/base.py` would silently invalidate this docstring. Flag for `docs/review/rev-django_strawberry_framework.md` to (a) confirm the invariant still holds across both seams in 0.0.7 and (b) decide whether the prose should live in a single canonical location (e.g. `AGENTS.md`, `docs/GLOSSARY.md`) rather than duplicated in `conf.py`. This forward was raised in the 0.0.6 cycle as well; if the 0.0.7 project pass declines to relocate, restate as "intentional duplication" so the next review cycle is not asked to re-litigate.

```django_strawberry_framework/conf.py:17-35
Defensive ``None`` stance (package-wide). Two top-level
consumer-input seams coerce ``None`` (and the missing-key case) to an
empty mapping rather than raising: ``DJANGO_STRAWBERRY_FRAMEWORK =
None`` (this module, treated as "no settings configured") and
``Meta.optimizer_hints = None`` in ``types/base.py`` (treated as "no
hints configured"). ...
```

### `_normalize_user_settings` rejects non-mapping values but does not validate keys are strings

`_normalize_user_settings` (`django_strawberry_framework/conf.py:50-83`) is typed `-> dict[str, Any]` and `Settings.user_settings` is typed `dict[str, Any]`, yet a consumer mapping like `{1: "x"}` or `{("a", "b"): "x"}` flows through `isinstance(value, Mapping)` and the `dict()` copy unchanged. `Settings.__getattr__`'s `self.user_settings[name]` lookup with a string `name` would then raise `KeyError` (converted to `AttributeError("Invalid setting: …")`) so the user-facing behavior is benign, but the cached dict violates its declared type. Two reasonable resolutions: (a) document in `_normalize_user_settings`'s docstring that the function trusts the consumer to use string keys (current behavior) and tighten the return annotation to `dict[Any, Any]` if mypy ever opts in; or (b) add an explicit non-string-key check raising `ConfigurationError`. Today (a) is the cheapest fix — no tests in `tests/base/test_conf.py` pin a non-string-key error and no consumer code path produces one. Defer to whichever 0.0.X release first introduces a typed schema for settings keys; quote trigger: "Defer until a settings key is added that needs typed validation; then add a per-key shape check in `_normalize_user_settings` and a test in `tests/base/test_conf.py` pinning the non-string-key rejection." Until then, the gap is documentation-only.

### Thread-safety contract for `Settings.user_settings` lazy-load is undocumented

`Settings.user_settings` (`django_strawberry_framework/conf.py:102-114`) reads `self._user_settings`, and if `None`, writes the result of `_normalize_user_settings(...)` back to `self._user_settings`. The check-and-set is **not atomic**: two concurrent threads could both observe `None`, both invoke `_normalize_user_settings`, and both write — the second write wins. Under the default Django settings shape, both `_normalize_user_settings` calls return equal (often identity-equal in the `dict` fast path on `django_strawberry_framework/conf.py:81-82`) dicts, so the race is observably benign for read-only consumers. But `reload_settings` mutates the singleton in-place via `Settings.reload`, and if a `reload_settings` signal fires concurrent with a first attribute lookup on a fresh process, a stale-value-vs-reload-value race is theoretically possible. Django's `setting_changed` signal is documented as test-only (`django.test.signals`), so the race window only opens under `pytest-django`'s `settings` fixture or `override_settings` blocks — both of which run single-threaded by convention. Today this is a latent contract issue, not a bug. Worth a single sentence on `Settings.user_settings`'s docstring ("Not thread-safe; the lazy-load and any concurrent `reload_settings` signal must not race. Django's `setting_changed` signal is test-only, so this is satisfied by Django's test conventions.") so a future async/multi-process consumer is not surprised. Not a logic change.

## What looks solid

### DRY recap

- **Existing patterns reused.** `_normalize_user_settings` (`django_strawberry_framework/conf.py:50-83`) is the single shape-contract gate — all three write sites funnel through it (`Settings.__init__` at `django_strawberry_framework/conf.py:100`, `Settings.user_settings` at `django_strawberry_framework/conf.py:110-113`, `Settings.reload` at `django_strawberry_framework/conf.py:123`). `ConfigurationError` is reused from `django_strawberry_framework/exceptions.py:24` (verified single canonical class for "consumer configuration is malformed") rather than redefined locally.
- **New helpers considered.** None at this granularity. The module is at minimum surface (one validator, one accessor class, one signal receiver). Extracting any further would split a coherent responsibility, and no other module in the package currently needs `_normalize_user_settings` so promoting it to a sibling utility would be premature.
- **Duplication risk in the current file.** The `None` -> "no settings configured" branch appears in three call sites (lines 100, 110-113, 123) but the repetition is structural — each call site has a different upstream value source (constructor arg vs Django settings vs signal payload) and a different meaning of `None` (defer-lazy vs missing-key vs reload-clear). Folding into `_normalize_user_settings` would collapse those distinct meanings. The current shape is correct; flagging only for the project pass to confirm no other module is repeating the same "coerce `None` to empty mapping" idiom outside the two seams the module docstring acknowledges.

### Other positives

- `_normalize_user_settings` is a tight, single-responsibility validator with four explicit branches and a docstring (`django_strawberry_framework/conf.py:50-83`) that names each one. Branch coverage is complete: `None` (line 75-76), non-`Mapping` raising `ConfigurationError` (lines 77-80), `dict` fast path (lines 81-82), other `Mapping` copy-to-dict (line 83). All three write sites funnel through it.
- The `dict` fast path preserves identity (`django_strawberry_framework/conf.py:81-82`) — consumers who hold a reference to the live dict (typical for `pytest-django`'s `settings` fixture) see their own mutations. Copying would silently break that contract.
- `Settings.__getattr__` short-circuits dunder names (`django_strawberry_framework/conf.py:139-140`) so `copy`, `deepcopy`, `inspect`, and Sphinx-style probes get a clean `AttributeError` instead of "Invalid setting". `test_settings_dunder_lookup_raises_plain_attributeerror` (`tests/base/test_conf.py:109-114`) pins this.
- `Settings.__getattr__` only catches `KeyError` and converts to `AttributeError` (`django_strawberry_framework/conf.py:141-144`). `ConfigurationError` from malformed Django settings is allowed to propagate through `hasattr` / `getattr(default=...)` probes by design — the docstring at lines 132-137 explicitly states this. `test_settings_user_settings_rejects_non_mapping_django_setting` (`tests/base/test_conf.py:57-64`) pins the raising behavior.
- `reload_settings` (`django_strawberry_framework/conf.py:150-160`) mutates the singleton in place rather than rebinding the module global; `test_reload_settings_updates_already_imported_reference` (`tests/base/test_conf.py:87-101`) pins the `from .conf import settings` import contract — a regression to rebinding would surface immediately.
- The signal-connect import-time side effect uses `dispatch_uid=_DISPATCH_UID` (`django_strawberry_framework/conf.py:168`), guaranteeing idempotence under re-import, and the inline comment at lines 163-167 justifies why `AppConfig.ready()` is not a viable home (test-bootstrap import order). `test_setting_changed_receiver_uses_dispatch_uid` (`tests/base/test_conf.py:136-145`) pins the no-op re-connect.
- `reload_settings`'s signature accepts `**kwargs: Any` (`django_strawberry_framework/conf.py:150`), absorbing Django's `sender` / `enter` payload without coupling to the signal's keyword shape — future Django releases adding signal kwargs will not break the receiver.
- No preemptively-populated keys: `examples/fakeshop/config/settings.py:172-174` declares `DJANGO_STRAWBERRY_FRAMEWORK = {}` with a "No settings yet — placeholder for future options." comment. No code path elsewhere in the package reads `conf.settings.<KEY>`, so the AGENTS.md "add settings keys only when the feature lands" rule holds for 0.0.7.
- Coverage in `tests/base/test_conf.py` is exhaustive across the file's surface: invalid-attribute (line 16-19), valid-attribute (22-25), lazy-load triggered (32-37), preset value (40-42), `Mapping` accepted (45-47), `None` Django setting (50-54), non-mapping Django setting raises (57-64), reload-in-place via signal (72-77), reload-skip on unrelated key (80-84), `from .conf import settings` import pattern under reload (87-101), dunder probe (109-114), `reload()` with dict (117-120), `reload(None)` (123-126), `reload` rejects non-mapping (129-133), and `dispatch_uid` idempotence (136-145).
- Static helper was run (`scripts/review_inspect.py` against `django_strawberry_framework/conf.py`, output at `docs/shadow/django_strawberry_framework__conf.overview.md`): no control-flow hotspots, no Django/ORM markers, and only the expected reflective-access sites (two `isinstance` calls in `_normalize_user_settings`, one `getattr` in `Settings.user_settings`). No TODO anchors. No repeated string literals.

### Summary

`conf.py` is unchanged in 0.0.7 since the 0.0.6 cycle closed (`git diff 5f0ffa5^...HEAD -- django_strawberry_framework/conf.py` is empty). The file is in good shape: a single normalization gate enforces the shape contract for the consumer-facing settings dict, the `Settings` accessor preserves dict identity for `pytest-django`'s live-mutation pattern, dunder probes short-circuit cleanly, the signal receiver mutates in place to honour the documented `from .conf import settings` import pattern, and the connect call is idempotent. AGENTS.md invariants hold: missing keys raise `AttributeError`, reload behaves correctly under `@override_settings`, no preemptively-populated keys. No High or Medium logic findings. The four Lows are all documentation-grade: (1) inline-comment the `@property`-vs-`__getattr__` recursion contract; (2) defer the package-wide `None`-stance prose decision to the project pass (carried forward from 0.0.6); (3) defer non-string-key validation until a settings key needs typed validation; (4) docstring-flag the thread-safety contract on the lazy-load. None of the four require a logic change.

---

## Fix report (Worker 2)

### Files touched
- None for logic. This cycle qualified for the consolidated single-spawn pattern: all four Lows are documentation-grade per Worker 1's own prose ("Worth a single inline comment...", "Flag for `docs/review/rev-django_strawberry_framework.md`", explicit "Defer until..." trigger, "Worth a single sentence on... docstring"). No logic change required.

### Tests added or updated
- None. No behaviour change. Existing `tests/base/test_conf.py` coverage (lines 16-145) is already exhaustive across the surface and continues to pin the documented contracts.

### Validation run
- `uv run ruff format .` — pass (118 files left unchanged on the no-op pre-edit invocation; consolidated post-edit invocation reports no changes).
- `uv run ruff check --fix .` — pass (All checks passed).
- No focused pytest invocation — no behaviour change and standing `START.md` rule is formatting only.

### Notes for Worker 3
- Shadow file: `docs/shadow/django_strawberry_framework__conf.overview.md` was consulted (no control-flow hotspots, no Django/ORM markers, only the expected reflective-access sites). Not edited.
- No false-premise rejections.
- L2 forwarded to `docs/review/rev-django_strawberry_framework.md` per Worker 1's instruction (project pass owns the cross-module `None`-stance decision).
- L3 deferred per Worker 1's quote trigger ("Defer until a settings key is added that needs typed validation; then add a per-key shape check in `_normalize_user_settings` and a test in `tests/base/test_conf.py` pinning the non-string-key rejection.").
- L1 and L4 landed in the same spawn as docstring/comment-only touches under the Comment/docstring pass below.

---

## Comment/docstring pass

### Files touched
- `django_strawberry_framework/conf.py:108-113` — added a four-line paragraph to `Settings.user_settings`'s docstring naming the thread-safety contract (lazy-load check-and-set is not atomic; satisfied by Django's test-only `setting_changed` convention).
- `django_strawberry_framework/conf.py:141-146` — added a four-line inline comment inside `Settings.__getattr__`'s `try` block pinning the `@property`-vs-`__getattr__` recursion contract ("keep it a `@property` to avoid recursive lookup on malformed config raising `ConfigurationError` inside this handler").

### Per-finding dispositions
- Low 1 (`__getattr__` recursion risk if the lazy `user_settings` read raises a non-mapping `ConfigurationError`): **accept-and-edit**. Worker 1 explicitly suggested "a single inline comment near `django_strawberry_framework/conf.py:142`" with quoted text. Landed at `conf.py:141-145` inside the `try` block so the comment sits next to the `self.user_settings` access it constrains.
- Low 2 (Cross-module `None`-stance assertion in the module docstring belongs at the project pass): **forward-to-project-pass**. Worker 1 explicitly instructed "Flag for `docs/review/rev-django_strawberry_framework.md`". No edit in `conf.py` this cycle; the project pass will (a) confirm the invariant holds across both seams and (b) decide whether the prose should be relocated to a single canonical location. If the project pass declines to relocate, the carry-forward from 0.0.6 should be restated as "intentional duplication" so 0.0.8 is not asked to re-litigate.
- Low 3 (`_normalize_user_settings` rejects non-mapping values but does not validate keys are strings): **defer-with-trigger**. Worker 1 quoted the trigger verbatim: "Defer until a settings key is added that needs typed validation; then add a per-key shape check in `_normalize_user_settings` and a test in `tests/base/test_conf.py` pinning the non-string-key rejection." Until a settings key with typed validation lands, the gap is documentation-only and the user-facing behaviour (`KeyError` -> `AttributeError("Invalid setting: ...")`) is benign. No edit this cycle.
- Low 4 (Thread-safety contract for `Settings.user_settings` lazy-load is undocumented): **accept-and-edit**. Worker 1 explicitly suggested "a single sentence on `Settings.user_settings`'s docstring" with quoted text. Landed at `conf.py:108-113` as a four-line paragraph (one sentence per Worker 1, expanded to a paragraph to preserve the rationale chain — "not atomic" -> "test-only signal" -> "satisfied by Django's test conventions"). Reflects final approved behaviour; no claim about thread safety beyond the test-convention narrowness.

### Validation run
- `uv run ruff format .` — pass (118 files left unchanged; consolidated single invocation covered both docstring edits).
- `uv run ruff check --fix .` — pass (All checks passed).

### Notes for Worker 3
- Both edits are docstring/comment-only and describe behaviour that the existing tests already pin (`tests/base/test_conf.py:50-64` for the malformed-config propagation through `__getattr__`; `tests/base/test_conf.py:72-101` for the `from .conf import settings` reload contract that the thread-safety note narrows).
- The L1 comment uses the exact quote Worker 1 supplied (`self.user_settings` is a descriptor, not a `__getattr__`-driven lookup; keep it a `@property` to avoid recursive lookup on malformed config). Reformatted to fit the 110-column line and the inline-comment placement.
- The L4 paragraph uses Worker 1's exact quote as the spine ("Not thread-safe; the lazy-load and any concurrent `reload_settings` signal must not race. Django's `setting_changed` signal is test-only, so this is satisfied by Django's test conventions.") and adds a one-clause pointer to the two test idioms (`override_settings`, `pytest-django`'s `settings` fixture) so a future async/multi-process consumer reading the docstring knows where the test-convention narrowness applies.
- No TODO anchor added (KANBAN check: no active slice owns thread safety or non-string-key validation; per Worker 2's comment dicta a TODO anchor pointing at no real slice is worse than no anchor).

---

## Changelog disposition

### State
`Not warranted`.

### Reason
Cycle's edits are docstring/comment-only: a four-line paragraph on `Settings.user_settings` and a four-line inline comment in `Settings.__getattr__`. Both describe pre-existing behaviour pinned by existing tests; no behavioural change, no public-API contract change, no error-message change, no consumer-visible surface drift. Cite (a) `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed") and (b) `docs/review/review-0_0_7.md` is silent on changelog authorization for the `rev-conf.md` cycle item. Third leg: the prior 0.0.7 cycles (`rev-_django_patches.md`, `rev-apps.md`) both closed as `Not warranted` for analogous internal/docstring-only edits, setting precedent for the in-flight 0.0.7 release.

### What was done
No `CHANGELOG.md` edit.

### Validation run
- `uv run ruff format .` — pass (no changes).
- `uv run ruff check --fix .` — pass (All checks passed).

---

## Verification (Worker 3)

### Logic verification outcome
No logic change in this cycle — `git diff -- django_strawberry_framework/conf.py` is comment-only at exactly two sites: a four-line docstring paragraph appended to `Settings.user_settings` (lines 110-114) and a four-line inline comment inside `Settings.__getattr__`'s `try` block (lines 148-151). No source line was altered; no test was added or modified. Per-Low disposition:

- **Low 1 (recursion contract)** — accepted. Worker 2's inline comment at `conf.py:148-151` reproduces Worker 1's quoted suggestion ("`self.user_settings` is a descriptor (`@property`), not a `__getattr__`-driven lookup; keep it a `@property` to avoid recursive lookup on malformed config raising `ConfigurationError` inside this handler"). Placement is correct — directly above the `return self.user_settings[name]` call the constraint protects.
- **Low 2 (cross-module `None`-stance forward)** — accepted-as-forward. Worker 2 carried this to `docs/review/rev-django_strawberry_framework.md` per Worker 1's explicit instruction and called out the 0.0.6 carry-forward plus the "restate as 'intentional duplication' if the project pass declines to relocate" guard so 0.0.8 is not asked to re-litigate. No `conf.py` edit this cycle is consistent with Worker 1's "Flag for `docs/review/rev-django_strawberry_framework.md`" framing.
- **Low 3 (non-string-key validation deferral)** — accepted-as-deferred. Worker 2's disposition prose quotes the deferral trigger verbatim ("Defer until a settings key is added that needs typed validation; then add a per-key shape check in `_normalize_user_settings` and a test in `tests/base/test_conf.py` pinning the non-string-key rejection."). The trigger is grep-discoverable in the artifact at `## Low` and the disposition cites Worker 1's exact wording.
- **Low 4 (thread-safety docstring)** — accepted. Worker 2's docstring paragraph at `conf.py:110-114` uses Worker 1's exact spine ("Not thread-safe; the lazy-load check-and-set and any concurrent `reload_settings` signal must not race. Django's `setting_changed` signal is test-only, so this is satisfied by Django's test conventions.") plus a one-clause pointer naming the two test idioms (`override_settings`, `pytest-django` `settings` fixture) that exercise the lazy-load path. The pointer is purely descriptive — it does not promise thread safety beyond the test-convention narrowness.

Consolidated single-spawn qualification was sound: all four Lows are documentation-grade per Worker 1's own prose ("Worth a single inline comment…", "Flag for `docs/review/rev-django_strawberry_framework.md`", explicit defer-with-trigger, "Worth a single sentence on… docstring"), no logic change is required, and Worker 2's two edits land exactly where Worker 1 named them. Re-running three sub-passes would have produced no new signal.

### DRY findings disposition
No DRY findings to action — Worker 1's DRY analysis recorded none and the comment-only edits preserve the single-normalization-gate / single-accessor-class / single-receiver shape unchanged. The structural distinction between the three `None` call sites (constructor / lazy property / signal reload) remains intact.

### Temp test verification
- None used. Behaviour pinned by `tests/base/test_conf.py` is unchanged and the existing test surface (lines 16-145) already covers every contract the two docstring/comment edits describe.
- Disposition: N/A.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `conf.py` checklist box in `docs/review/review-0_0_7.md`.

`git diff -- CHANGELOG.md` is empty, matching the recorded `Not warranted` disposition. The disposition cites AGENTS.md ("Do not update CHANGELOG.md unless explicitly instructed"), the active plan's silence on changelog authorization for the `rev-conf.md` cycle item, and the in-flight 0.0.7 precedent from the prior two cycles (`rev-_django_patches.md`, `rev-apps.md`) — three citations clear the two-citation bar. The "internal-only" framing is honest: docstring/comment-only edits do not change `conf.py`'s public API (`Settings`, `settings`, `reload_settings`, `ConfigurationError`) or its observable behaviour.

`uv run ruff format --check .` — pass (118 files already formatted; COM812 conflict warning is a long-standing config note, not a regression).
`uv run ruff check .` — pass (All checks passed).
Pytest not run — no behaviour change, no test added, and AGENTS.md "do not run pytest after edits" applies.
