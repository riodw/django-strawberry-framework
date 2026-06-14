# Review: `django_strawberry_framework/scalars.py`

Status: verified

## DRY analysis

- None — the file holds two strict transcoders (`_parse_bigint`, `_serialize_bigint`) and one factory (`strawberry_config`). The two transcoders share the bool-first / int-second branch shape (`scalars.py:49-56`, `scalars.py:82-85`) but the exception families and accept-sets differ deliberately (parser accepts `str` and raises `ValueError`; serializer rejects `str` and raises `TypeError`), so a shared `_strict_int_transcode(value, exc_cls)` helper would collapse only two lines while obscuring the documented input/output asymmetry. `_PACKAGE_SCALAR_MAP` (`scalars.py:97-99`) is a single-entry registry today; promoting it to a `_register_package_scalar(...)` helper is premature until a second package-defined scalar lands. **Defer all transcoder/registry consolidation until the second package scalar lands** (the Upload-scalar card `TODO-ALPHA-035-0.0.11`, queued for `0.0.11`); at that point reconsider whether `_register_package_scalar(newtype, *, name, serialize, parse_value)` and a paired `_strict_int_transcode(value, exc_cls)` collapse the call sites. Trigger: a second `_PACKAGE_SCALAR_MAP` entry is added.

## High:

None.

## Medium:

None.

## Low:

### Falsy-`Mapping` fast-path skips the copy on consumer subclasses that override `__bool__`

`scalars.py:126` reads `extra = dict(extra_scalar_map) if extra_scalar_map else {}`. The truthiness branch is correct for `None`, plain `dict()`, and `MappingProxyType({})`, but a consumer-supplied `Mapping` subclass whose `__bool__` returns `False` for non-empty content would take the wrong branch: `extra` would be left `{}`, so a real collision would NOT be caught and the merge would silently drop the consumer's entries. This is defense-in-depth only, not a confirmed bug — today's call sites (example project, test suite) all pass plain `dict`. Defer until a consumer or test exercises a `Mapping` subclass with a custom `__bool__`; at that point switch to the explicit `extra = dict(extra_scalar_map) if extra_scalar_map is not None else {}`, mirroring the explicit-`None` normalization style used elsewhere in the package (`conf.py::_normalize_user_settings`). Trigger: a `Mapping` subclass with custom `__bool__` lands in tests or examples.

## What looks solid

### DRY recap

- **Existing patterns reused.** The bool-first guard before the int-check (`scalars.py:49-56` and `scalars.py:82-85`) is the canonical Python idiom for not letting `bool` slip through `isinstance(x, int)`; both transcoders carry the same shape and the inline rationale ("bool subclasses int; explicit reject"). The `getattr(k, '__name__', repr(k))` defensive fallback at `scalars.py:131` is the standard idiom for mixed `NewType`/`class`/atypical-object keys under `Mapping[object, ScalarDefinition]`. The `strawberry.scalar(name=, serialize=, parse_value=)` no-warning overload (`scalars.py:91-95`) is reused over the deprecated decorator form, which is what keeps the package import deprecation-free; the converter table (`types/converters.py:66,70`) and the inspect command's SDL-name map (`management/commands/inspect_django_type.py:85`) both import the single `BigInt` `NewType` rather than redeclaring it, so scalar identity is shared package-wide.
- **New helpers considered.** A shared `_strict_int_transcode(value, exc_cls)` collapsing both transcoders — rejected: parser and serializer differ in accept-set (`str` accepted only by the parser) and exception family (`ValueError` vs `TypeError`); a shared helper would carry both as parameters for a two-line saving. A `_register_package_scalar(...)` helper around `strawberry.scalar(...)` — rejected: single call site today, premature until the second package scalar lands. Both deferrals share the same trigger (`TODO-ALPHA-035-0.0.11`, Upload scalar, `0.0.11`).
- **Duplication risk in the current file.** The per-branch f-string error messages across the parser's branches (`scalars.py:54,59-63,65`) and the serializer's branches (`scalars.py:83,86`) look like duplicated string construction but encode deliberately distinct error contexts (the regex-constraint enumeration at lines 59-63 is specific to the string-rejection branch and would be noise on the bool / non-int branches). Keep as-is.

### Other positives

- The `_BIGINT_STRING_PATTERN` regex (`scalars.py:27`) is anchored at both ends (`^...$`) AND consumed via `.fullmatch()` (`scalars.py:58`), giving belt-and-suspenders rejection of trailing-content strings like `"42\n"`. The pattern carries a three-line comment (`scalars.py:24-26`) enumerating exactly what it rejects (PEP 515 underscores, plus signs, Unicode decimal digits, hex/octal/scientific, whitespace), and the parser docstring reject-list (`scalars.py:37-47`) matches the regex behavior exactly. `[0-9]` (not `\d`) is the right choice — it rejects Unicode/fullwidth digits.
- The bool-first guard is sound and justified: `bool` is checked before `int` in both functions because `bool` subclasses `int`; the inline comment (`scalars.py:50-53`) explains why the parser raises `ValueError` (not `TypeError`) on bool — uniform `ValueError` for invalid input, matching the GraphQL `parse_value` contract — and the `# noqa: TRY004` is a legitimate contract decision, not a lint workaround.
- The parse/serialize asymmetry is deliberate and documented at module level (`scalars.py:8-13`): the serializer rejects `str` so a schema cannot emit a value the parser would reject, keeping the wire sides symmetric (decimal string in, decimal string out) even though the in-Python accept-sets differ. The serializer docstring (`scalars.py:74-80`) restates the contract at the call site.
- `strawberry_config()` is collision-safe, ownership-safe, and per-call isolated: `scalar_map=` is rejected up front (`scalars.py:122-125`) BEFORE the collision check, so a consumer cannot bypass collision detection by routing through `**config_kwargs`; `extra_scalar_map` collisions with package keys raise an actionable `ValueError` (`scalars.py:128-133`, spec-025 Decision 4); and every call builds a fresh `merged` dict from `dict(_PACKAGE_SCALAR_MAP)` (`scalars.py:135`) with the input copied via `dict(extra_scalar_map)` (`scalars.py:126`), so neither the package map nor a caller's mapping is mutated and returned configs share no state — matching the GLOSSARY's "fresh `StrawberryConfig` instance with a fresh `scalar_map` dict" guarantee. Keyword-only `extra_scalar_map` plus `**config_kwargs` passthrough composes cleanly.
- No import-time side effects beyond intended registration: module import builds one compiled regex, one `ScalarDefinition`, and one literal dict — all pure, no Django app-registry or ORM access (shadow overview confirms zero Django/ORM markers, zero control-flow hotspots). Safe to import before `django.setup()`.
- The `_PACKAGE_SCALAR_MAP` annotation `dict[object, ScalarDefinition]` (`scalars.py:97`) matches the upstream `StrawberryConfig.scalar_map` shape; the `extra_scalar_map: Mapping[object, ScalarDefinition] | None` parameter (`scalars.py:104`) widens to `Mapping` at the boundary so consumers can pass `MappingProxyType`/subclasses, then narrows back to `dict` via the copy at the merge step.
- **GLOSSARY drift quick-check: clean.** Grepped `docs/GLOSSARY.md` for `BigInt`, `strawberry_config`, `scalar_map`, `extra_scalar_map`. The `BigInt scalar` entry (`docs/GLOSSARY.md:192`) matches the runtime — the `^(0|-?[1-9][0-9]*)$` regex, the strict accept/reject sets, the wire-level string serialization, and the `Int cannot represent non 32-bit signed integer` boundary note all align with the source. The `strawberry_config` entry (`docs/GLOSSARY.md:1211`) matches the factory signature, the `scalar_map=`/`extra_scalar_map=` ownership split, the collision `ValueError`, the `**config_kwargs` passthrough, and the per-call fresh-dict / mutation-isolation guarantee. No verbatim replacement text needed; no GLOSSARY-only fix in scope.

### Summary

`scalars.py` is a 138-line module with a tight single-purpose surface: one public scalar (`BigInt`), one private package registry (`_PACKAGE_SCALAR_MAP`), one public factory (`strawberry_config`). Logic is correct end-to-end — bool-first/int-second guards in both directions, an anchored ASCII-only `fullmatch` regex, a factory that rejects `scalar_map=` before the collision check so the policy cannot be bypassed, and per-call fresh-dict isolation with no shared mutable state. No import-time Django coupling. The four prior-cycle Lows (stale `TODO-ALPHA-028` anchor, `spec-020`→`spec-025` citation, module-docstring symmetry wording) are already merged into the current source and verified resolved — the module docstring reads `TODO-ALPHA-035-0.0.11`, the factory docstring reads `spec-025 Decision 4`, and the symmetry sentence already distinguishes wire-level symmetry from in-Python accept-set asymmetry. No High or Medium. One Low carries forward unchanged: the falsy-`Mapping` fast-path defense-in-depth deferral, gated on its explicit trigger. No source edit is warranted this cycle, so this qualifies as a no-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
None — no-source-edit cycle.

### Tests added or updated
None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass, 265 files left unchanged (no edits made).
- `uv run ruff check --fix .` — pass, All checks passed (no edits made).

### Notes for Worker 3
- The single Low (falsy-`Mapping` fast-path on consumer subclasses with custom `__bool__`) is explicitly deferred per its own trigger phrasing: "Defer until a consumer or test exercises a `Mapping` subclass with a custom `__bool__`." No edit warranted; today's call sites all pass plain `dict`.
- No GLOSSARY-only fix in scope — the GLOSSARY drift quick-check came back clean for `BigInt`, `strawberry_config`, `scalar_map`, and `extra_scalar_map` (entries at `docs/GLOSSARY.md:192` and `docs/GLOSSARY.md:1211`).
- The four Lows raised in the prior (0.0.7) review cycle are already merged into current source (`scalars.py:3` reads `TODO-ALPHA-035-0.0.11`; `scalars.py:117` reads `spec-025 Decision 4`; the module-docstring symmetry sentence at `scalars.py:8-13` already distinguishes wire-level vs in-Python accept-sets). Nothing to re-apply.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment/docstring defects found: the module docstring, both transcoder docstrings, and the `strawberry_config` docstring all match the implementation and the GLOSSARY. Prior-cycle citation/anchor/symmetry drifts are already resolved in current source.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

`Not warranted` — no source change this cycle. Per `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan `docs/review/review-0_0_9.md`'s silence on changelog authorization for review-only cycles, no `CHANGELOG.md` edit is in scope.

---

## Verification (Worker 3)

### Logic verification outcome
Independently re-derived every claim from source + a live transcode harness; no source edit this cycle (shape #5).

- **bool-before-int guards** (`scalars.py:49-56` parser, `scalars.py:82-85` serializer): confirmed load-bearing. Live run — `_parse_bigint(True)`/`(False)` both raise `ValueError("BigInt does not accept boolean values")`; `_serialize_bigint(True)` raises `TypeError`. bool is checked before int (bool ⊂ int), so without the guard a bool would slip through `isinstance(x, int)`. The `# noqa: TRY004` is a documented contract decision (uniform `ValueError` for invalid parse input), not a lint workaround.
- **anchored ASCII regex** (`scalars.py:27` `^(0|-?[1-9][0-9]*)$`, consumed via `.fullmatch()` `scalars.py:58`): live-tested accept/reject — accepts `0`,`42`,`-42`,`-1`; rejects `-0`,`00`,`01`,`007`,`+1`,`1_000`,`1.9`,`1e3`,`0x10`,` 5`,`5\n`,`''`, and Unicode/fullwidth digit strings (`١٢٣`,`１２３`). `[0-9]` (not `\d`) + `^...$` + `fullmatch` give belt-and-suspenders trailing-content rejection. Parser docstring reject-list (`scalars.py:37-47`) matches behavior exactly.
- **serializer str-rejection / wire symmetry**: `_serialize_bigint('5')` raises `TypeError` while `_parse_bigint('5')` returns `5` — the documented in-Python asymmetry (parser accepts `str`+`int`, serializer accepts `int` only) that keeps the wire sides symmetric so a schema cannot emit a value the parser would reject. Matches module docstring (`scalars.py:8-13`).
- **`strawberry_config()` scalar_map rejection + fresh-dict isolation + collision check**: `scalar_map={}` rejected up-front (`scalars.py:122-125`) BEFORE the collision check, so consumers cannot bypass collision detection via `**config_kwargs`. Two calls yield distinct `scalar_map` dict objects, neither is `_PACKAGE_SCALAR_MAP` (which stays len 1 after calls) — per-call isolation holds. Redeclaring `BigInt` via `extra_scalar_map` raises the actionable `ValueError` naming the key (`scalars.py:128-134`).
- **import-time Django coupling**: none. Shadow overview reports zero Django/ORM markers, zero control-flow hotspots; module import builds one compiled regex, one `ScalarDefinition`, one literal dict — all pure. Safe before `django.setup()`. Shared `BigInt` identity confirmed: `types/converters.py:51` and `management/commands/inspect_django_type.py:48` both import the single NewType rather than redeclaring.
- **the lone forward-looking Low** (falsy-`Mapping` fast-path, `scalars.py:126`): empirically reproduced with a `dict` subclass whose `__bool__` returns `False` for non-empty content — the entry is silently dropped (`extra` left `{}`, collision check + merge skip it). This is a real latent defect, but NO current call path exercises it (example project + test suite all pass plain `dict`). The deferral carries verbatim trigger phrasing ("a `Mapping` subclass with custom `__bool__` lands in tests or examples") and the proposed fix (`extra = dict(extra_scalar_map) if extra_scalar_map is not None else {}`, mirroring `conf.py::_normalize_user_settings`) is sound. Per AGENTS.md no-premature-change posture for a defense-in-depth Low with no live consumer, deferral is correct — no source edit warranted.

### DRY findings disposition
The "None" disposition holds. A shared `_strict_int_transcode(value, exc_cls)` would collapse only two lines while parameterizing the genuine accept-set divergence (`str` accepted by parser only) and exception family (`ValueError` vs `TypeError`) — verified distinct in the live harness. `_register_package_scalar(...)` is premature at one registry entry. Both deferrals carry the explicit trigger "a second `_PACKAGE_SCALAR_MAP` entry is added" (`TODO-ALPHA-035-0.0.11`, Upload scalar, `0.0.11`) — anchor confirmed present in source (`scalars.py:3`) and corroborated by spec-025 and GLOSSARY.

### Temp test verification
- No persisted temp test files; verification used an ephemeral inline `uv run python` harness (regex matrix, transcoder matrix, factory isolation/collision/scalar_map-rejection, and falsy-`Mapping` reproduction). Nothing to promote — the behaviors exercised are all already pinned by the existing suite and the lone defect is correctly deferred.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box.

Shape #5 bookkeeping: scalars.py diff vs baseline `0872a20f` empty; owned-paths `--stat` (django_strawberry_framework/, tests/, docs/GLOSSARY.md, CHANGELOG.md) empty; only dirty tracked files are rev-*.md artifacts + deleted root `feedback2/3.md` (AGENTS.md #33 concurrent-maintainer work, out of scope). Every Worker 2 section opens with `Filled by Worker 1 per no-source-edit cycle pattern.`; changelog `Not warranted` cites both AGENTS.md and the active plan's silence; ruff `format --check` and `check` both pass. GLOSSARY entries (`docs/GLOSSARY.md:198`, `:1211`) aligned.

---

## Iteration log

_Append-only — Worker 2 re-passes and Worker 3 re-verifications land here._
