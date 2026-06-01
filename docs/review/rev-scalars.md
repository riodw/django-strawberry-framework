# Review: `django_strawberry_framework/scalars.py`

Status: verified

## DRY analysis

- None — the file has two strict transcoders (`_parse_bigint`, `_serialize_bigint`) and one factory (`strawberry_config`). The two transcoders share the bool-first / int-second branch shape (`scalars.py:46-49`, `scalars.py:75-78`) but the exception families and the surrounding accept-set differ (parser accepts `str`, serializer does not; parser raises `ValueError`, serializer raises `TypeError`), so a shared `_check_int(value, exc_cls)` helper would only collapse two lines while obscuring the deliberate asymmetry the docstrings advertise. `_PACKAGE_SCALAR_MAP` (`scalars.py:90-92`) is a single-entry registry today; promoting it to a shared `_register_package_scalar(...)` helper is premature until a second package-defined scalar lands (the Upload scalar card, `TODO-ALPHA-035-0.0.11`, queued for `0.0.11`). The `dict(_PACKAGE_SCALAR_MAP)` + `merged.update(extra)` pattern at `scalars.py:128-129` is a one-call site; no helper needed. Defer all transcoder/registry consolidation until the second package scalar lands; at that point reconsider whether `_register_package_scalar(newtype, *, name, serialize, parse_value)` and a paired `_strict_int_transcode(value, exc_cls)` collapse the call sites. Trigger: a second `_PACKAGE_SCALAR_MAP` entry is added.

## High:

None.

## Medium:

None.

## Low:

### Stale TODO anchor in module docstring (`TODO-ALPHA-028` is the Ordering subsystem, not the Upload scalar)

The module docstring at `scalars.py:3` reads `Future scalars (e.g. ``Upload`` per TODO-ALPHA-028) land here.` but `TODO-ALPHA-028-0.0.8` is the Ordering subsystem card (`KANBAN.md:99`, `KANBAN.md:133`). The Upload-scalar card is `TODO-ALPHA-035-0.0.11` (`KANBAN.md:613`, `KANBAN.md:925`), queued for `0.0.11` and explicitly cited in the GLOSSARY entry for `strawberry_config` as "next: [`Upload`](#upload-scalar) in `0.0.11`" (`docs/GLOSSARY.md:1014`). This is citation drift, not a behavior bug — a reader following the `TODO-ALPHA-028` anchor lands in the wrong card. Recommended fix: replace `TODO-ALPHA-028` with `TODO-ALPHA-035-0.0.11` in the module docstring. (Side note: `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md:611` independently cites `TODO-ALPHA-029-0.0.11` for the Upload scalar, which is also stale against KANBAN.md but out of scope for this review — flagged as a project-pass follow-up for `rev-django_strawberry_framework.md` since the spec is a docs/SPECS/ archived asset, not source.)

```django_strawberry_framework/scalars.py:1-11
"""Public scalars defined by django-strawberry-framework.

Today: ``BigInt``. Future scalars (e.g. ``Upload`` per TODO-ALPHA-028) land here.
...
"""
```

### Wrong spec citation in `strawberry_config` docstring (collision policy is `spec-025` Decision 4, not `spec-020`)

The `strawberry_config` docstring at `scalars.py:109` reads `collisions with package-defined keys raise ``ValueError`` (per spec-020 Decision 4)`, but `docs/SPECS/spec-020-list_field-0_0_7.md` Decision 4 is "Optimizer cooperation" for `DjangoListField` (`docs/SPECS/spec-020-list_field-0_0_7.md:520`), which is unrelated to scalar-map collision policy. The actual conflict-resolution-policy decision lives in `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` Decision 4 ("Conflict resolution for `extra_scalar_map` collisions", `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md:312`). The helper body matches the spec-025 policy verbatim; only the in-source citation rotted. Recommended fix: replace `spec-020 Decision 4` with `spec-025 Decision 4` in the docstring. A reader chasing the audit trail today lands in the wrong spec.

```django_strawberry_framework/scalars.py:106-114
    The keyword-only ``extra_scalar_map`` lets consumers register their own
    scalars alongside the package defaults; collisions with package-defined
    keys raise ``ValueError`` (per spec-020 Decision 4). Every other keyword
    argument in ``**config_kwargs`` is forwarded verbatim to
    ``StrawberryConfig(...)`` (e.g. ``auto_camel_case``, ``relay_max_results``).
    Passing ``scalar_map=`` directly is rejected with ``ValueError`` because
    the helper owns that field; route consumer scalars through
    ``extra_scalar_map=`` instead.
    """
```

### Falsy-`Mapping` fast-path skips the copy on consumer subclasses that override `__bool__`

`scalars.py:119` reads `extra = dict(extra_scalar_map) if extra_scalar_map else {}`. The truthiness branch is correct for `None`, plain `dict()`, and `MappingProxyType({})`, but a consumer-supplied `Mapping` subclass whose `__bool__` returns `False` for non-empty content (or `True` for empty content) would take the wrong branch. The runtime impact is minimal — the empty-but-truthy case copies an empty mapping (no-op except a wasted allocation); the non-empty-but-falsy case skips the copy and leaves `extra = {}`, which means a real collision would NOT be caught and the merge would silently drop the consumer's entries. This is a defense-in-depth concern only, not a confirmed bug; today's call sites (the example project, the test suite) all use plain `dict`. Defer until a consumer or test exercises a `Mapping` subclass with a custom `__bool__`; at that point switch to the explicit `extra = dict(extra_scalar_map) if extra_scalar_map is not None else {}` check, which mirrors the explicit-None style the codebase uses for normalization elsewhere (`conf.py::_normalize_user_settings` is the canonical example, `django_strawberry_framework/conf.py:50-83`). Trigger: a `Mapping` subclass with custom `__bool__` lands in tests or examples.

### Module docstring's parser-symmetry claim is asymmetric with serializer's accept-set

The module docstring at `scalars.py:8-10` reads `serialized as a decimal string via Python ``str(int_value)`` so values past GraphQL's signed 32-bit ``Int`` boundary survive transit without truncation. The strict parser / serializer keep the input and output sides symmetric.` But the parser accepts both `int` and decimal-string `str` (`scalars.py:48-57`); the serializer accepts `int` only (`scalars.py:77-78`). The "symmetric" framing is accurate at the wire (the serializer emits a string and the parser accepts a string), but the in-Python accept-set is intentionally asymmetric — pre-serialization values are always `int`, post-parsing values are always `int`, and the string-accepting parser branch exists to receive JSON-stage values. The current wording reads as if the two functions accept the same set; readers who internalize the "symmetric" claim and then read the serializer-rejects-`str` branch will assume the docstring is wrong. Recommended fix: tighten the module-docstring sentence to "The strict parser and serializer keep the **wire-level** input and output sides symmetric (decimal string in, decimal string out), even though the in-Python accept-sets differ — the parser additionally accepts `int` for direct-call sites while the serializer rejects `str` so a schema cannot emit a value the parser would reject." Defer if the next docstring sweep covers it; flag as a Low not a Medium because the behavior is correct and the docstrings on the two functions individually are precise — only the module-level summary is loose.

## What looks solid

### DRY recap

- **Existing patterns reused.** The bool-first guard before the int-check (`scalars.py:46-49` and `scalars.py:75-78`) is the canonical Python idiom for not letting `bool` slip through an `isinstance(x, int)` test — both transcoders carry the same shape and the same docstring rationale ("bool subclasses int; explicit reject"). The `getattr(k, '__name__', repr(k))` defensive fallback at `scalars.py:124` is the standard idiom for mixed `NewType`/`class`/atypical-object keys under `Mapping[object, ScalarDefinition]` — pinned in `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md:445` as "defensive-only".
- **New helpers considered.** A shared `_strict_int_transcode(value, exc_cls)` collapsing both transcoders — rejected: the parser and serializer differ in accept-set (`str` accepted only by parser) and exception family (`ValueError` vs. `TypeError`); a shared helper would either ignore the difference or carry both as parameters, and the call-site savings are two lines. A `_register_package_scalar(newtype, *, name, serialize, parse_value)` helper around `strawberry.scalar(...)` — rejected: single call site today; premature until the second package-defined scalar lands. Both deferrals are gated on the same trigger (the Upload scalar card, `TODO-ALPHA-035-0.0.11`, in `0.0.11`).
- **Duplication risk in the current file.** The repeated f-string error-message shape across the parser's three branches (`scalars.py:53-56`, `scalars.py:58`) and the serializer's two branches (`scalars.py:76`, `scalars.py:79`) looks like duplicated string construction but encodes deliberately distinct error contexts — collapsing them through a shared message formatter would lose the per-branch context the messages carry (e.g. the regex constraint enumeration at lines 53-56 is specific to the string-rejection branch and would be noise on the bool / non-int branches). Keep as-is.

### Other positives

- The `_BIGINT_STRING_PATTERN` regex (`scalars.py:24`) is anchored at both ends (`^...$`) AND consumed via `fullmatch` (`scalars.py:51`), giving belt-and-suspenders rejection of trailing-content strings like `"42\n"`. The pattern carries a three-line comment (`scalars.py:21-23`) enumerating exactly what it rejects (PEP 515 underscores, plus signs, Unicode decimal digits, hex/octal/scientific, whitespace) and the corresponding test cases in `tests/test_scalars.py` (lines 152-218) pin each rejection branch — one positive-zero test, one negative-zero rejection, one leading-zero rejection, one leading-plus rejection, one underscore rejection, one Unicode-digit rejection. Coverage is exhaustive across the regex's reject surface.
- The bool-first guard is pinned by four separate tests: `test_bigint_serialize_rejects_bool` and `test_bigint_rejects_python_bool` for both `True` and `False` on both transcoders (`tests/test_scalars.py:60-65, 134-139`). The "bool subclasses int" trap is the kind of silent-correctness bug that breaks downstream consumers in ways that are nearly invisible at the schema layer; double pinning is correct.
- Boundary-value coverage: signed int64 min and max are explicitly pinned for both directions (`tests/test_scalars.py:45-52` for serialize, `tests/test_scalars.py:119-126` for parse) — the same boundaries the live `examples/fakeshop/test_query/test_library_api.py` exercises against `Patron.lifetime_fines_cents` (per `docs/TREE.md:480`). Package-internal tests pin the contract; live HTTP test pins the end-to-end round-trip.
- The `strawberry_config` factory rejects `scalar_map=` directly with a `ValueError` (`scalars.py:115-118`) BEFORE any other validation, so a consumer cannot accidentally bypass the collision-detection policy by passing `scalar_map={...}` through `**config_kwargs`. Pinned three ways by `test_strawberry_config_rejects_scalar_map_kwarg` (`tests/test_scalars.py:381-394`): empty dict, `None`, and a collision payload all raise.
- Each call returns a fresh `StrawberryConfig` with a fresh `scalar_map` dict (`scalars.py:128-130`) — pinned by `test_strawberry_config_independent_call_returns_independent_instance` (`tests/test_scalars.py:332-341`), which asserts both `c1 is not c2` and `c1.scalar_map is not c2.scalar_map`, plus a mutation-isolation check. This is the single property that distinguishes `strawberry_config()` from a module-level singleton and the test pins it correctly.
- `extra = dict(extra_scalar_map) if extra_scalar_map else {}` (`scalars.py:119`) defensively copies the caller's dict; mutation isolation is pinned by `test_strawberry_config_extra_scalar_map_does_not_mutate_caller_dict` (`tests/test_scalars.py:312-319`). The Low above flags only the falsy-`Mapping`-subclass edge case, not the canonical-Mapping copy semantics.
- Deprecation-warning surface is pinned by a subprocess-isolation test (`tests/test_scalars.py:243-266`) that re-imports the package under `-W error::DeprecationWarning` — the comment at `tests/test_scalars.py:246-248` explicitly justifies the subprocess form ("avoids the importlib.reload-doesn't-reload-submodules trap"). The `strawberry.scalar(name=..., serialize=..., parse_value=...)` no-warning overload at `scalars.py:84-88` is the load-bearing implementation choice that keeps this test green; `docs/GLOSSARY.md:40` documents the choice verbatim.
- GLOSSARY drift quick-check on the three required terms: `BigInt` scalar entry (`docs/GLOSSARY.md:174-182`) is aligned with the runtime — strict parser regex matches `scalars.py:24` literally, accept-set / reject-set match the parser body, and the wire-format string-serialization claim matches `_serialize_bigint`'s `str(value)` return. `strawberry_config` entry (`docs/GLOSSARY.md:1010-1047`) is aligned with the factory signature, the `extra_scalar_map=` keyword-only contract, the `scalar_map=` rejection, the collision-raises-`ValueError` policy, and the fresh-instance / mutation-isolation guarantee. `Specialized scalar conversions` entry (`docs/GLOSSARY.md:996-1008`) is aligned with the converter-table mapping (`django_strawberry_framework/types/converters.py:66-70`). No GLOSSARY-only fix in scope — all drift surfaces are in source comments / docstrings, not in glossary prose.
- The `_PACKAGE_SCALAR_MAP` type annotation is `dict[object, ScalarDefinition]` (`scalars.py:90`), matching the upstream `StrawberryConfig.scalar_map: dict[object, ScalarDefinition]` shape exactly. The `extra_scalar_map: Mapping[object, ScalarDefinition] | None` parameter annotation (`scalars.py:97`) widens to `Mapping` at the boundary so consumers can pass `MappingProxyType` / custom subclasses, then narrows back to `dict` via the `dict(extra_scalar_map)` copy at the merge step. The annotation discipline is consistent with the package-wide pattern (`conf.py::__init__` is the sibling — see `docs/review/rev-conf.md` "Low: `Settings.__init__` annotation understates runtime acceptance").

### Summary

`scalars.py` is a 130-line module with a tight, single-purpose surface: one public scalar (`BigInt`), one private package registry (`_PACKAGE_SCALAR_MAP`), and one public factory (`strawberry_config`). Logic is correct end-to-end, the bool-first / int-second / `fullmatch`-regex pattern is the right shape, the factory's `scalar_map=`-rejection precedes the collision check so the policy cannot be bypassed, and every behavioral branch is pinned by `tests/test_scalars.py` (43 test cases across parser, serializer, factory, import-surface, and deprecation-warning). No High or Medium issues. Four Lows, all comment / docstring drift requiring real source edits — a stale TODO anchor (`TODO-ALPHA-028` → `TODO-ALPHA-035-0.0.11`), a wrong spec citation (`spec-020 Decision 4` → `spec-025 Decision 4`), a defense-in-depth falsy-`Mapping` deferral, and a module-docstring symmetry-claim refinement. Each requires a source edit at comment-pass time, so this routes through the standard three-spawn cycle (not shape #5). The two citation drifts are higher-signal than the other two — both point a reader at the wrong audit-trail anchor — but neither rises to Medium because the code itself is correct and the spec-025 / KANBAN sources of truth are unambiguous.

---

## Fix report (Worker 2)

Consolidated single-spawn pass — three comment/docstring Lows applied (Lows 1, 2, 4); Low 3 deferred per the artifact's explicit trigger phrasing.

### Files touched
- `django_strawberry_framework/scalars.py:3` — Low #1: replaced `TODO-ALPHA-028` with `TODO-ALPHA-035-0.0.11` in the module docstring (verified anchor exists at `KANBAN.md:613`).
- `django_strawberry_framework/scalars.py:9-13` — Low #4: tightened the module-docstring symmetry sentence to make wire-level symmetry vs. in-Python accept-set asymmetry explicit, using the artifact's recommended wording verbatim.
- `django_strawberry_framework/scalars.py:108` — Low #2: replaced `spec-020 Decision 4` with `spec-025 Decision 4` in the `strawberry_config` docstring (verified `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` Decision 4 exists at line 312).

### Tests added or updated
- None. All three edits are docstring polish with no logic change; `grep` of `tests/test_scalars.py` for `TODO-ALPHA-028`, `spec-020 Decision 4`, `spec-025 Decision 4`, and `symmetric` returned no matches — no test pins the rewritten docstring text.

### Validation run
- `uv run ruff format .` — pass / no-changes (183 files left unchanged).
- `uv run ruff check --fix .` — pass (All checks passed!).
- pytest — not run per AGENTS.md and the dispatch prompt.

### Notes for Worker 3
- Anchors verified on disk before edit: `TODO-ALPHA-035-0.0.11` exists in `KANBAN.md` (multiple sites, including the card header at `KANBAN.md:613`); `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` Decision 4 exists at line 312 (`Conflict resolution for extra_scalar_map collisions`).
- Low #3 (falsy-`Mapping` fast-path on consumer subclasses with custom `__bool__`) is **deferred per the artifact's own trigger phrasing**: "Defer until a consumer or test exercises a `Mapping` subclass with a custom `__bool__`." No source edit made; the artifact records the trigger condition.
- The Low #1 prose also flagged a sibling drift in `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md:611` (`TODO-ALPHA-029-0.0.11` for the Upload scalar, also stale against KANBAN.md) and the artifact explicitly punts it to `rev-django_strawberry_framework.md` as a project-pass follow-up — staying inside the scalars.py scope per the "no unrelated cleanup" rule.
- No shadow file used during implementation (edits were purely textual docstring fixes).
- `git status` is clean re: `uv.lock`; the only modified tracked files outside this cycle's scope are pre-existing dirty paths (`docs/feedback.md`, `docs/spec-028-orders-0_0_8.md`, `docs/GLOSSARY.md`, sibling `exceptions.py` and `list_field.py` from earlier cycle items) which I did not touch.

---

## Verification (Worker 3)

Terminal-verify of the consolidated single-spawn pass.

### Logic verification outcome

All three in-cycle Lows (1, 2, 4) are addressed with source edits matching the artifact's recommendations verbatim:

- **Low #1** (stale TODO anchor): `scalars.py:3` now reads `TODO-ALPHA-035-0.0.11`. Anchor confirmed on disk at `KANBAN.md:613` (`### [TODO-ALPHA-035-0.0.11 — Upload scalar and file / image field mapping]`).
- **Low #2** (wrong spec citation): `scalars.py:111` now reads `per spec-025 Decision 4`. Anchor confirmed on disk at `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md:312` (`### Decision 4 — Conflict resolution for extra_scalar_map collisions`).
- **Low #3** (falsy-`Mapping` fast-path): deferred per the artifact's explicit trigger phrasing ("Defer until a consumer or test exercises a `Mapping` subclass with a custom `__bool__`"). No source edit made; deferral is artifact-authorized, not Worker 2 discretion.
- **Low #4** (module-docstring symmetry claim): `scalars.py:9-13` rewritten using the artifact's recommended wording verbatim — wire-level symmetry preserved, in-Python accept-set asymmetry now explicit.

Scoped diff against `django_strawberry_framework/scalars.py` matches the Worker 2 fix-report file-list exactly (one hunk at module docstring, one hunk at `strawberry_config` docstring). No drive-by edits, no unrelated cleanup. Other dirty paths in the working tree (`exceptions.py`, `list_field.py`, `docs/GLOSSARY.md`, `docs/feedback.md`, `docs/spec-028-orders-0_0_8.md`) belong to sibling cycle items or pre-existing maintainer work — out of scope per the dispatch and not touched by this cycle.

### DRY findings disposition

The artifact's lone DRY bullet was a forward-looking "None" with two named deferrals (`_strict_int_transcode` and `_register_package_scalar`) both gated on the same trigger: a second `_PACKAGE_SCALAR_MAP` entry landing. The trigger is the Upload-scalar card (`TODO-ALPHA-035-0.0.11`) in `0.0.11`. No edit warranted in this cycle; the trigger phrasing is now anchored to the corrected TODO card via Low #1's edit, so the future DRY-consolidator has a grep-discoverable path to the deferral site.

### Temp test verification

None created. The three edits are pure docstring text changes; no behavior surface needed a temp-test probe and none of the Lows promised one. `tests/test_scalars.py` already pins every behavioral branch the docstrings describe (per the artifact's "What looks solid" enumeration).

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `scalars.py` checklist box in `docs/review/review-0_0_7.md`.

Changelog disposition verified: `git diff -- CHANGELOG.md` is empty; the artifact's `Not warranted` state cites both AGENTS.md ("Do not update CHANGELOG.md unless explicitly instructed") AND the active plan / dispatch prompt's explicit instruction ("Changelog disposition: Not warranted (internal docstring polish only) citing both AGENTS.md + active plan silence"). The internal-only framing is honest — three citation/anchor fixes and one symmetry-claim refinement, no public-API or behavior change.

Ruff outcomes plausible on spot-check: edits are docstring-only with no trailing-comma surface touched; each new line fits the 110-cap E501 grace; no import or symbol changes that would surface a check finding.

---

## Comment/docstring pass

Folded into the consolidated single-spawn — all three in-cycle Lows (1, 2, 4) are docstring polish; there is no logic-pass / comment-pass split for this artifact.

### Files touched
- `django_strawberry_framework/scalars.py:3` — Low #1 TODO-anchor citation fix.
- `django_strawberry_framework/scalars.py:9-13` — Low #4 module-docstring symmetry-claim refinement.
- `django_strawberry_framework/scalars.py:108` — Low #2 `spec-020` → `spec-025` Decision 4 citation fix.

### Per-finding dispositions
- High: none.
- Medium: none.
- Low #1 (`TODO-ALPHA-028` → `TODO-ALPHA-035-0.0.11`): applied verbatim per the artifact's recommendation; KANBAN.md anchor verified on disk.
- Low #2 (`spec-020 Decision 4` → `spec-025 Decision 4`): applied verbatim per the artifact's recommendation; spec-025 Decision 4 anchor verified on disk at line 312.
- Low #3 (falsy-`Mapping` fast-path): **deferred** per the artifact's explicit trigger phrasing ("Defer until a consumer or test exercises a `Mapping` subclass with a custom `__bool__`"). No edit made.
- Low #4 (module-docstring symmetry claim): applied using the artifact's recommended wording verbatim — wire-level symmetry preserved, in-Python accept-set asymmetry now explicit.

### Validation run
- `uv run ruff format .` — pass / no-changes.
- `uv run ruff check --fix .` — pass.

### Notes for Worker 3
Nothing beyond the Fix-report Notes above.

---

## Changelog disposition

### State
`Not warranted`.

### Reason
The cycle's edits are internal-only docstring polish — three citation/anchor fixes and one symmetry-claim refinement. No consumer-visible behavior change, no public-symbol change, no contract change. Per AGENTS.md ("Do not update CHANGELOG.md unless explicitly instructed") AND the active plan's silence on changelog authorization for this cycle (the dispatch prompt explicitly states `Changelog disposition: Not warranted (internal docstring polish only) citing both AGENTS.md + active plan silence`), no `CHANGELOG.md` edit is in scope.

### What was done
No `CHANGELOG.md` edit.

### Validation run
- `uv run ruff format .` — pass / no-changes.
- `uv run ruff check --fix .` — pass.

---

## Iteration log

_Append-only — Worker 2 re-passes and Worker 3 re-verifications land here._
