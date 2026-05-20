# Review: `django_strawberry_framework/conf.py`

Status: verified

## DRY analysis

- None — `conf.py` is at the minimum surface for its responsibility (one normalization helper, one accessor class, one signal receiver); the `None`-guard repetition across the three write sites is structural because each site has a different upstream value source (constructor arg vs Django settings vs signal payload).

## High:

None.

## Medium:

None.

## Low:

### `__getattr__` lets `ConfigurationError` escape `hasattr`/`getattr(default=...)` probes

`Settings.__getattr__` (`django_strawberry_framework/conf.py:125-137`) only catches `KeyError`. If the cache is empty and the Django settings value is malformed (non-mapping), the `self.user_settings` access on line 135 raises `ConfigurationError` from `_normalize_user_settings`, which is **not** an `AttributeError`. That means `hasattr(settings, "SOME_KEY")` does not return `False` — it raises `ConfigurationError`; and `getattr(settings, "SOME_KEY", default)` does not return `default` — it raises `ConfigurationError`. This is arguably correct (malformed config should fail loud), and the test suite already pins the raising behavior under `test_settings_user_settings_rejects_non_mapping_django_setting` (`tests/base/test_conf.py:57-64`). Worth a docstring sentence on `__getattr__` noting that `ConfigurationError` can propagate through attribute access for diagnostic clarity; not a logic change.

```django_strawberry_framework/conf.py:125-137
def __getattr__(self, name: str) -> Any:
    if name.startswith("__"):
        raise AttributeError(name)
    try:
        return self.user_settings[name]
    except KeyError:
        raise AttributeError(f"Invalid setting: `{name}`") from None
```

### Module docstring asserts a contract — "Defensive `None` stance (package-wide)" — that is enforced outside this file

The module docstring at `django_strawberry_framework/conf.py:17-35` documents the **two** authorised `None`-coercion seams (here and `Meta.optimizer_hints` in `types/base.py`). That cross-module assertion belongs in the project-pass artifact, not this file's contract — the local file cannot enforce or test the `types/base.py` half of the claim, and a future drift in `types/base.py` would silently invalidate this docstring. Flag for the project-level pass (`docs/review/rev-django_strawberry_framework.md`) to confirm the documented invariant still holds across both seams and consider whether the prose should live in a single canonical location (e.g. `AGENTS.md` or `docs/GLOSSARY.md`) rather than duplicated in the `conf.py` module docstring.

```django_strawberry_framework/conf.py:17-35
Defensive ``None`` stance (package-wide). Two top-level
consumer-input seams coerce ``None`` (and the missing-key case) to an
empty mapping rather than raising: ``DJANGO_STRAWBERRY_FRAMEWORK =
None`` (this module, treated as "no settings configured") and
``Meta.optimizer_hints = None`` in ``types/base.py`` (treated as "no
hints configured"). ...
```

## What looks solid

### DRY recap

- Existing patterns reused: `_normalize_user_settings` is the single shape-contract gate, and it is the only path that produces the cached `dict[str, Any]`. The three write sites (`Settings.__init__` at `django_strawberry_framework/conf.py:100`, `Settings.user_settings` at `django_strawberry_framework/conf.py:110-113`, `Settings.reload` at `django_strawberry_framework/conf.py:123`) all funnel through it, which is the consolidation the module's docstring promises (`django_strawberry_framework/conf.py:70-73`). `ConfigurationError` is reused from `django_strawberry_framework/exceptions.py:24-34` rather than redefined locally. No other helper from the package is currently appropriate to reuse here.
- New helpers a fix might justify: none. The module is already at the minimum surface for its responsibility (one normalization helper, one accessor class, one signal receiver). Extracting any of these further would split a coherent responsibility.
- Duplication risk in the current file: the `None` -> "no settings configured" branch is repeated in three call sites (`django_strawberry_framework/conf.py:100`, `django_strawberry_framework/conf.py:110-113`, `django_strawberry_framework/conf.py:123`) but the repetition is structural — each call site has a different upstream value source (constructor arg vs Django settings vs signal payload) and the `None`-guard is the cheapest local form. Folding them into `_normalize_user_settings` itself would require all three sites to lose the `None`-vs-pass-through distinction (the constructor and `reload` use `None` as "defer to lazy reload" while `user_settings` already passes `None` to mean "missing key"). The current shape is correct; flagging only for the project pass to confirm no other module is repeating the same "coerce None to empty mapping" idiom outside the two seams the module docstring acknowledges.

### Other positives

- `_normalize_user_settings` is a tight, single-responsibility validator with four explicit branches and a docstring that names each one (`django_strawberry_framework/conf.py:50-83`). All three write sites funnel through it, so the shape contract is enforced uniformly.
- The `dict` fast-path preserves identity (`django_strawberry_framework/conf.py:81-82`) — the docstring explicitly calls out the consumer expectation that "tests that capture the same dict by reference observe their mutations". This is the right call for a settings module: consumers do mutate the live dict during tests via `pytest-django`'s `settings` fixture, and copying would silently break those mutations.
- `Settings.__getattr__` short-circuits dunder names (`django_strawberry_framework/conf.py:132-133`), so `copy`, `deepcopy`, `inspect`, and Sphinx-style probes get a clean `AttributeError` instead of the "Invalid setting" message. The test `test_settings_dunder_lookup_raises_plain_attributeerror` (`tests/base/test_conf.py:109-114`) pins this.
- `reload_settings` mutates the singleton in place rather than rebinding the module global (`django_strawberry_framework/conf.py:152-153`). The docstring at lines 144-151 explains why, and the test `test_reload_settings_updates_already_imported_reference` (`tests/base/test_conf.py:87-101`) pins the `from .conf import settings` contract — a regression to rebinding would surface immediately.
- The signal-connect import-time side effect uses `dispatch_uid` (`django_strawberry_framework/conf.py:161`), guaranteeing idempotence under re-import, and the comment at lines 156-160 justifies why `AppConfig.ready()` is not a viable home (test-bootstrap import order). `test_setting_changed_receiver_uses_dispatch_uid` (`tests/base/test_conf.py:136-145`) pins the no-op re-connect.
- The `setting_changed` receiver signature accepts `**kwargs` (`django_strawberry_framework/conf.py:143`), which absorbs Django's `sender` and `enter` keyword arguments without coupling to the signal's payload shape.
- Static helper was run (`scripts/review_inspect.py` against `django_strawberry_framework/conf.py`, output under `docs/shadow/`); no control-flow hotspots, no Django/ORM markers, and only the expected reflective-access sites (two `isinstance` calls and one `getattr` in `_normalize_user_settings` / `user_settings`).

### Summary

`conf.py` is in good shape for a 0.0.6 review: a single normalization gate (`_normalize_user_settings`) enforces the shape contract for the consumer-facing settings dict, the `Settings` accessor preserves dict identity for `pytest-django`'s live-mutation pattern, dunder probes short-circuit cleanly, the signal receiver mutates in place to honour the documented `from .conf import settings` import pattern, and the connect call is idempotent. No High or Medium logic findings. The two Low items are docstring-polish suggestions: (1) note in `__getattr__` that `ConfigurationError` can propagate through attribute access on malformed Django settings, and (2) defer the "package-wide `None` stance" cross-module invariant to the project-pass artifact, where it can actually be enforced across both seams.

---

## Fix report (Worker 2)

### Files touched

- None. Both Low findings deferred — finding 1 is a docstring-only update reserved for the comment pass per the standing review-order rule (logic first, comments second); finding 2 is explicitly flagged for the project-pass artifact (`docs/review/rev-django_strawberry_framework.md`).

### Tests added or updated

- None. No logic change; existing tests in `tests/base/test_conf.py` already pin every relevant branch per the artifact's `What looks solid` section.

### Validation run

- `uv run ruff format .` — pass/no-changes (100 files left unchanged).
- `uv run ruff check --fix .` — pass/no-changes (all checks passed).

### Notes for Worker 3

- No shadow file was used during this pass; the artifact's reasoning was clear and no comment-stripped view was needed for a no-op logic disposition.
- Explicit interpretation of the two Low findings: finding 1 ("`__getattr__` lets `ConfigurationError` escape `hasattr`/`getattr(default=...)` probes") is a **comment-pass item** — Worker 1 labelled it a docstring-polish suggestion and the behavior is already test-pinned by `tests/base/test_conf.py::test_settings_user_settings_rejects_non_mapping_django_setting`. Finding 2 ("Defensive `None` stance (package-wide)") is a **project-pass forward** — Worker 1 explicitly says "Flag for the project-level pass" because the cross-module assertion cannot be enforced from within `conf.py` alone.
- Confirmation: no logic change is needed in this pass. The artifact contains zero High/Medium findings and both Low findings are deferred by their own descriptions.

---

## Verification (Worker 3)

### Logic verification outcome

- High: None — accepted.
- Medium: None — accepted.
- Low #1 (`__getattr__` `ConfigurationError` propagation docstring): deferred to comment pass — accepted. Worker 1 explicitly labels it a docstring-polish suggestion (not a logic change), and the raising behavior is already test-pinned by `tests/base/test_conf.py::test_settings_user_settings_rejects_non_mapping_django_setting`. Comment-pass home is the correct application of the logic-first/comments-second rule.
- Low #2 ("Defensive `None` stance (package-wide)" cross-module assertion): deferred to project pass — accepted. The Low section of the artifact already cites `docs/review/rev-django_strawberry_framework.md` by path, so the project pass will see the forward when it runs.
- Diff check: `git status` shows only the two expected untracked maintainer-seeded review artifacts (`docs/review/rev-conf.md`, `docs/review/review-0_0_6.md`). `git diff --stat` and `git diff -- django_strawberry_framework/ tests/` both return empty — no package source or test changes landed, consistent with Worker 2's no-op disposition.
- Spot-checked `What looks solid` claims against `django_strawberry_framework/conf.py`: dict identity preservation (lines 81-83), `__getattr__` dunder short-circuit (lines 132-133), `reload_settings` in-place mutation (lines 152-153), `dispatch_uid` on `setting_changed.connect` (line 161), and signal receiver `**kwargs` (line 143). All match the source.

### DRY findings disposition

Worker 1's three DRY bullets — no new helpers, no in-file duplication, and structural `None`-guard repetition at three call sites being correct — require no action at the logic pass. The cross-file `None`-coercion question is appropriately forwarded to the project pass via the Low #2 finding. Accepted.

### Temp test verification

- None used. No temp tests needed for a no-op pass; existing `tests/base/test_conf.py` coverage is sufficient per the artifact's `What looks solid` section.

### Verification outcome

logic accepted; awaiting comment pass

---

## Comment/docstring pass

### Files touched

- `django_strawberry_framework/conf.py:125-144` — extended the `Settings.__getattr__` docstring with a paragraph noting that only `KeyError` is converted to `AttributeError`, and that a malformed `DJANGO_STRAWBERRY_FRAMEWORK` value lets `ConfigurationError` escape through `hasattr`/`getattr(default=...)` probes by design. No logic changes.

### Finding 1 disposition

Docstring updated as described. The new sentences describe the existing behavior that is already test-pinned by `tests/base/test_conf.py::test_settings_user_settings_rejects_non_mapping_django_setting` (`tests/base/test_conf.py:57-64`). Google convention preserved; line length ≤110.

### Finding 2 disposition

Intentionally not edited in this comment pass. Worker 1's Low-section guidance was: "Flag for the project-level pass (`docs/review/rev-django_strawberry_framework.md`) to confirm the documented invariant still holds across both seams and consider whether the prose should live in a single canonical location (e.g. `AGENTS.md` or `docs/GLOSSARY.md`) rather than duplicated in the `conf.py` module docstring." The module docstring stays as-is until the project pass decides whether to relocate the cross-module assertion.

### Validation run

- `uv run ruff format .` — pass (100 files left unchanged; only the standing `COM812`-vs-formatter advisory, unchanged from prior passes).
- `uv run ruff check --fix .` — pass (all checks passed).

### Notes for Worker 3

- No shadow file used; the docstring edit was localised and the artifact's Low #1 description named the exact site (`django_strawberry_framework/conf.py:125-137`).
- Please confirm the new docstring sentences accurately describe the existing behavior pinned by `tests/base/test_conf.py::test_settings_user_settings_rejects_non_mapping_django_setting`.
- Finding 2 deliberately untouched; carry it forward to the project pass per Worker 1's explicit instruction.

---

## Changelog disposition

- **Warranted?** Not warranted.
- **Reason:** The cycle's only source change is a docstring sentence on `Settings.__getattr__` (`django_strawberry_framework/conf.py:125-144`) clarifying that `ConfigurationError` can propagate through `hasattr` / `getattr(default=...)` when the Django settings dict is malformed. The behavior itself is unchanged from earlier releases; the cycle adds no logic, no API surface, no test coverage, and no user-visible contract. Per `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed.") and per the active plan `docs/review/review-0_0_6.md` (no changelog authorization for this cycle item), no edit is made.
- **What was done:** No `CHANGELOG.md` edit. Disposition recorded in this artifact. The existing `[0.0.6] - 2026-05-19` entry in `CHANGELOG.md` is left untouched; the maintainer may roll the docstring clarification into the next user-visible 0.0.6 entry at their discretion.
- **Validation run:**
  - `uv run ruff format .` — pass / no-changes (100 files left unchanged; only the standing `COM812`-vs-formatter advisory, unchanged from prior passes).
  - `uv run ruff check --fix .` — pass / no-changes (all checks passed).
  - `pytest` intentionally not run, per `worker-2.md` Validation dicta and `START.md`.

---

## Iteration log

## Verification (Worker 3, pass 2)

### Comment verification outcome

- Diff scope: `git diff -- django_strawberry_framework/conf.py` shows only an added paragraph inside `Settings.__getattr__`'s docstring (lines 131-137 in the new file). No other source edits; no test edits; `_normalize_user_settings`, `Settings.__init__`, `Settings.user_settings`, `Settings.reload`, `reload_settings`, and the module docstring (including the "Defensive `None` stance (package-wide)" prose at lines 17-35) are untouched. No scope creep.
- Behavior cross-check: the new sentences match the actual call chain — `__getattr__` reads `self.user_settings` (line 142), the property body lazily delegates to `_normalize_user_settings(getattr(django_settings, DJANGO_SETTINGS_KEY, None))` (`django_strawberry_framework/conf.py:110-114`), and `_normalize_user_settings` raises `ConfigurationError` on a non-mapping (`django_strawberry_framework/conf.py:77-80`). Only `KeyError` is converted to `AttributeError` (`django_strawberry_framework/conf.py:143-144`), so `ConfigurationError` does propagate through `hasattr` / `getattr(default=...)` probes as the docstring claims.
- Test pin: `tests/base/test_conf.py::test_settings_user_settings_rejects_non_mapping_django_setting` (`tests/base/test_conf.py:57-64`) asserts the raising behavior via `with pytest.raises(ConfigurationError, match="DJANGO_STRAWBERRY_FRAMEWORK.*list")`, which is exactly the behavior the new docstring sentences describe. No new test needed for a docstring-only addition.
- Style: Google-convention voice consistent with the surrounding docstring; all new lines ≤110 chars; no logic change in the method body.
- Finding 1: docstring updated — accepted.
- Finding 2: intentionally not edited in `conf.py` — accepted. The "Defensive `None` stance (package-wide)" prose at `django_strawberry_framework/conf.py:17-35` is untouched, matching Worker 1's explicit forward-to-project-pass instruction. Carry the cross-module assertion review into `docs/review/rev-django_strawberry_framework.md`.
- Sanity validation: `uv run ruff check django_strawberry_framework/conf.py` reports `All checks passed!`.

### Verification outcome

comments accepted; awaiting changelog disposition

## Verification (Worker 3, pass 3)

### Changelog verification outcome

- Diff scope confirmed: `git diff --stat -- django_strawberry_framework/ tests/ CHANGELOG.md` shows only `django_strawberry_framework/conf.py` modified (+7 lines). `CHANGELOG.md` is untouched. `git diff -- django_strawberry_framework/conf.py` confirms the only change is the appended paragraph inside `Settings.__getattr__`'s docstring (lines 131-137 in the new file); no logic, no API, no test, no other source edit, no scope creep across the cycle.
- Disposition prose check: the `## Changelog disposition` section explicitly records "Not warranted", names the cycle's single change (docstring-only sentence on `Settings.__getattr__`), and states "No `CHANGELOG.md` edit" under "What was done". The rationale cites `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed.") and the active plan `docs/review/review-0_0_6.md` (no changelog authorization for this cycle item) — both required citations are present.
- Validation: both `uv run ruff format .` and `uv run ruff check --fix .` recorded as pass / no-changes in the changelog disposition section. `pytest` intentionally not run per `START.md` and `worker-2.md` validation dicta — accepted.
- `CHANGELOG.md` body cross-check: the existing `[0.0.6] - 2026-05-19` entry is unchanged from prior state; no review-cycle additions were smuggled in. Maintainer discretion to fold the docstring clarification into a future entry is correctly preserved.
- Cycle scope sanity: the only source diff for the entire cycle (across logic, comment, and changelog passes) is the `Settings.__getattr__` docstring addition. Internal-only, non-user-visible, no contract change — "Not warranted" disposition is the right call.

### Verification outcome

cycle accepted; verified
