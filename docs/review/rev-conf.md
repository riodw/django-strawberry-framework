# Review: `django_strawberry_framework/conf.py`

Status: verified

## DRY analysis

- None — the three cache-write sites (`Settings.__init__`, `Settings.user_settings`, `Settings.reload`) already funnel through a single `_normalize_user_settings` helper at `django_strawberry_framework/conf.py:50-83`, the `DJANGO_STRAWBERRY_FRAMEWORK` literal is centralized as `DJANGO_SETTINGS_KEY`, and the `setting_changed` `dispatch_uid` is centralized as `_DISPATCH_UID`. The short-circuit set in `__getattr__` (`django_strawberry_framework/conf.py:147`) is a recursion guard local to that handler, not a duplicated shape; lifting it to a module constant would obscure the guard's intent for zero call-site savings.

## High:

None.

## Medium:

None.

## Low:

### `Settings.__init__` annotation understates runtime acceptance

`Settings.__init__`'s parameter annotation is `Mapping[str, Any] | None` (`django_strawberry_framework/conf.py:89`), but the runtime path delegates to `_normalize_user_settings`, which deliberately accepts `Any` so that a non-mapping (e.g. `"bad"`, `[...]`) raises `ConfigurationError` rather than silently absorbing via the old `or {}` fallback. The docstring states this directly ("Non-mapping values raise `ConfigurationError`"). The annotation mismatch is intentional — type-checkers steer consumers toward the correct shape while runtime stays fail-loud. Defer until a third caller (besides `__init__` and `reload`) gains an `Any`-typed boundary; at that point declare a `_UserSettingsInput: TypeAlias = Mapping[str, Any] | None` and let mypy carry the "explicitly broader at runtime" comment on the alias instead of repeating it across three docstrings. Trigger: a third public entry point accepting raw user-settings input lands.

### Module-level singleton hides reload coupling from static readers

`reload_settings` (`django_strawberry_framework/conf.py:162-172`) mutates the module-level `settings` singleton constructed at line 159. The wiring is correct and documented in the module docstring + `reload_settings` docstring, but a grep-only reader following `settings` references will not see the mutation site without reading the signal-connect at line 180. Defer until a second module-level mutator of the singleton lands (e.g. a future `register_runtime_override(...)` helper); at that point pull both mutators into a `_singleton` namespace or add a `# Singleton mutators: ...` index comment at the singleton-construction site. Trigger: a second non-signal mutator of `settings` is introduced.

## What looks solid

### DRY recap

- **Existing patterns reused.** `_normalize_user_settings` (`django_strawberry_framework/conf.py:50-83`) is the single normalization helper called from `Settings.__init__` (line 100-101), `Settings.user_settings` lazy load (line 118-121), and `Settings.reload` (line 131). `DJANGO_SETTINGS_KEY` (line 46) and `_DISPATCH_UID` (line 47) are reused by the error message at line 79, the lazy-read at line 120, the signal-key compare at line 171, and the `dispatch_uid` argument at line 180.
- **New helpers considered.** Pulling `{"user_settings", "_user_settings", "reload"}` into a module constant — rejected: the set is a recursion guard local to `__getattr__` (`django_strawberry_framework/conf.py:147`) and only meaningful at that call site; CPython 3.12 frozenset-folds constant set literals so there is no per-call construction cost either. Naming it adds indirection for zero readability or perf gain.
- **Duplication risk in the current file.** The `Mapping`/`dict` fast-path branches in `_normalize_user_settings` (`django_strawberry_framework/conf.py:81-83`) look like duplicated isinstance checks but encode distinct intent — preserve `dict` identity for tests that mutate the same reference vs. copy other `Mapping` instances into a plain `dict`. Collapsing them to a single `dict(value)` would break the identity-preservation contract called out in the helper's docstring.

### Other positives

- Module docstring (`django_strawberry_framework/conf.py:1-36`) carries the package-wide "defensive `None` stance" charter — explicitly delineates the two top-level seams that coerce `None` to `{}` (this module + `Meta.optimizer_hints`) from the reflective-descriptor `or {}` reads in the optimizer subpackage, and tags `None`-tightening as future-slice work. This is a load-bearing design-decision record; do not edit casually.
- `__getattr__` (`django_strawberry_framework/conf.py:133-156`) has a layered defense: dunder + descriptor-name short-circuit, then a try-except that catches **only** `KeyError`, with the inline comment at lines 150-153 explaining why `self.user_settings` must stay a `@property` (a `__getattr__`-driven lookup would recurse on malformed config). Two regression tests pin the recursion guards: `test_settings_uninitialized_user_settings_does_not_recurse` (`tests/base/test_conf.py:152-156`) and `test_settings_normalization_attribute_error_does_not_recurse` (`tests/base/test_conf.py:159-168`).
- `_normalize_user_settings`'s branch structure (`django_strawberry_framework/conf.py:75-83`) is testable end-to-end: `None`-branch covered by `test_settings_user_settings_falsy_falls_back_to_empty_dict`, non-`Mapping` branch by `test_settings_user_settings_rejects_non_mapping_django_setting` and `test_settings_reload_rejects_non_mapping_value`, `dict` fast path implicitly by every `Settings({...})` construction, and `Mapping` copy path by `test_settings_user_settings_accepts_mapping_values` using `MappingProxyType`.
- Signal wiring at module load (`django_strawberry_framework/conf.py:175-180`) carries a five-line comment justifying why `AppConfig.ready()` is not a viable home (consumers may import `conf` before app loading during test bootstrap) and why `dispatch_uid` is the idempotency guarantee. `test_setting_changed_receiver_uses_dispatch_uid` (`tests/base/test_conf.py:140-149`) pins the idempotent-connect property.
- `reload_settings` (`django_strawberry_framework/conf.py:162-172`) mutates the existing singleton rather than rebinding the module global — `test_reload_settings_updates_already_imported_reference` (`tests/base/test_conf.py:91-105`) pins this contract end-to-end, including the `bound_settings is conf.settings` identity assertion.
- GLOSSARY drift quick-check: `docs/GLOSSARY.md` has no entry for the `conf` module, the `settings` singleton, `_normalize_user_settings`, or `DJANGO_STRAWBERRY_FRAMEWORK` as a settings-key surface (the only `DJANGO_STRAWBERRY_FRAMEWORK` mentions are the package name and `INSTALLED_APPS` string at `docs/GLOSSARY.md:1079`). The `ConfigurationError` entry at `docs/GLOSSARY.md:194-209` lists six type-creation / finalization examples; the new "non-mapping `DJANGO_STRAWBERRY_FRAMEWORK` value" trigger is a settings-import-time case that does not fit the existing examples list, but the entry's "Raised at type-creation or finalization time when consumer configuration is invalid or inconsistent" lead sentence + open-ended example list reads as illustrative rather than exhaustive. Do NOT widen the lead sentence to "type-creation, finalization, or settings-import time" until the public-API documentation surfaces user-facing guidance about the settings dict (per AGENTS.md "Add settings keys only when the feature that needs them lands" — there are currently zero settings keys, so the consumer-visible settings-dict contract is unstable). Forward to the project-level pass (`rev-django_strawberry_framework.md`) as a glossary follow-up if a future slice exposes the first real settings key.

### Summary

`conf.py` is a focused 180-line module with one normalization helper, one settings class, one signal receiver, and one module-level singleton, all routed through a single shape contract. The recursion guards in `__getattr__` are belt-and-suspenders (dunder short-circuit + descriptor-name short-circuit + `KeyError`-only catch) and both belt and suspenders are pinned by regression tests. No High or Medium issues. The two Lows are forward-looking with explicit triggers (a third raw-input callsite for the annotation alias; a second non-signal mutator for the singleton index). No source/test/GLOSSARY edits are warranted in this cycle.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
None — no-source-edit cycle.

### Tests added or updated
None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — no changes to format (no source edits in this cycle).
- `uv run ruff check --fix .` — no changes to fix (no source edits in this cycle).

### Notes for Worker 3
- Both Lows are forward-looking with explicit, greppable trigger conditions (third raw-input callsite; second non-signal mutator of the `settings` singleton). Neither is actionable today.
- No GLOSSARY-only fix in scope. The `ConfigurationError` glossary entry (`docs/GLOSSARY.md:194-209`) reads as illustrative not exhaustive, and AGENTS.md "Add settings keys only when the feature that needs them lands" + zero shipped settings keys in `0.0.7` justifies deferral of any glossary expansion until the first real settings key surfaces. Forwarded as a project-pass follow-up signal for `rev-django_strawberry_framework.md`.
- Shadow overview at `docs/shadow/django_strawberry_framework__conf.overview.md` was up to date; no re-run.

---

## Verification (Worker 3)

### Logic verification outcome
Shape #5 no-source-edit cycle. No High/Medium findings to verify. Both Lows are forward-looking deferrals with verbatim, greppable trigger phrasing ("Trigger: a third public entry point accepting raw user-settings input lands." for the annotation alias; "Trigger: a second non-signal mutator of `settings` is introduced." for the singleton index). Neither is actionable today. Spot-verified the `What looks solid` claims against source: `_normalize_user_settings` at `conf.py:50-83`, `DJANGO_SETTINGS_KEY`/`_DISPATCH_UID` at `conf.py:46-47`, `__getattr__` recursion-guard set at `conf.py:147`, signal connect at `conf.py:180`. All five cited regression tests exist verbatim in `tests/base/test_conf.py` (`test_settings_uninitialized_user_settings_does_not_recurse`, `test_settings_normalization_attribute_error_does_not_recurse`, `test_setting_changed_receiver_uses_dispatch_uid`, `test_reload_settings_updates_already_imported_reference`, `test_settings_user_settings_accepts_mapping_values`).

### DRY findings disposition
`None — …` DRY justified: three cache-write sites already funnel through `_normalize_user_settings`; `DJANGO_STRAWBERRY_FRAMEWORK` and dispatch UID are already centralized as constants; the `__getattr__` recursion-guard set is local-intent and lifting it would obscure meaning. No action.

### Temp test verification
None — no temp tests created (no-source-edit cycle, no behavior to probe).

### Verification outcome
- `cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box

Shape #5 five-check outcomes:
1. `git diff --stat HEAD -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` empty.
2. All three Worker 2 sections open with `Filled by Worker 1 per no-source-edit cycle pattern.`
3. Both Lows carry verbatim trigger phrasing; no GLOSSARY-only fix in scope (forwarded as project-pass follow-up).
4. Changelog `Not warranted` cites both AGENTS.md and `docs/review/review-0_0_7.md` silence.
5. `uv run ruff format --check .` reports "183 files already formatted"; `uv run ruff check .` reports "All checks passed!".

GLOSSARY citation `docs/GLOSSARY.md:194-209` for `ConfigurationError` spot-verified — entry's open-ended example list reads as illustrative, so the deferral until a real settings key surfaces is the correct call.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment/docstring edits required — the module docstring's "defensive `None` stance" charter, the `__getattr__` inline recursion-guard comment, and the signal-connect five-line justification are all current and load-bearing.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — no source, test, or GLOSSARY edits in this cycle (AGENTS.md "Do not update CHANGELOG.md unless explicitly instructed" + `docs/review/review-0_0_7.md` is silent on changelog for this artifact).

---

## Iteration log
