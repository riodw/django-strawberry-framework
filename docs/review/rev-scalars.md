# Review: `django_strawberry_framework/scalars.py`

Status: verified

## DRY analysis

- None — the module has three single-responsibility symbols with no internal near-copies: `_parse_bigint` and `_serialize_bigint` are deliberately asymmetric (parser accepts `int`+`str`, serializer accepts `int` only) so their shared shape is the `isinstance(value, bool)` reject-then-`isinstance(value, int)` ladder, but folding that into a shared guard would couple two contracts that must diverge (the documented input/output symmetry rule at `scalars.py:9-13`). The `dict(...)` copy + `_PACKAGE_SCALAR_MAP.keys() & extra.keys()` collision check in `strawberry_config` is a single site. No repeated literals (shadow overview reports 0). The `BigInt` name string lives once as `name="BigInt"` at `scalars.py::_BIGINT_SCALAR_DEFINITION`; the `inspect_django_type.py:85` and converter-table references key off the `BigInt` symbol, not a duplicated literal.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** `BigInt` is the single canonical scalar symbol; `types/converters.py:66,70` map both `BigIntegerField` and `PositiveBigIntegerField` to it by symbol reference, and `management/commands/inspect_django_type.py:85` renders it from `__name__`. The `_PACKAGE_SCALAR_MAP` dict (`scalars.py:97-99`) is the one registration source `strawberry_config` reads — consumers (`examples/fakeshop/config/schema.py:41`, all `tests/` schema builders) bind scalars exclusively through the factory, never re-declaring the map.
- **New helpers considered.** Considered extracting the `isinstance(bool)`→`isinstance(int)` ladder shared by `_parse_bigint` and `_serialize_bigint`; rejected because the parser and serializer accept-sets are intentionally asymmetric (parser also accepts `str`, serializer rejects it) per the documented symmetry contract, so a shared guard would re-couple them and obscure the divergence.
- **Duplication risk in the current file.** The literal `"BigInt"` appears in `name=` and in error messages, but each is a distinct human-facing string (scalar name vs. parser/serializer diagnostic text); these are intentional sibling strings, not a hoistable constant. Shadow overview reports 0 repeated literals.

### Other positives

- **BigInt bounds correctness is unbounded-by-design and verified.** `BigInt` is arbitrary-precision (Python `int`), serialized as a decimal string via `str(value)` so it survives GraphQL's signed 32-bit `Int` boundary and JS's 53-bit safe-integer limit. The 64-bit edges are pinned both in package tests (`tests/test_scalars.py:47,52,121,126` cover `-2**63` and `2**63 - 1`) and over a live `/graphql/` round-trip (`examples/fakeshop/test_query/test_scalars_api.py`, boundary values intentionally exceeding `2**53 - 1`). No truncation path exists — `int(value)` after a strict regex match cannot lose precision.
- **Strict parser rejects every documented hostile input.** The regex `^(0|-?[1-9][0-9]*)$` (`scalars.py:27`) with `.fullmatch` rejects leading zeroes, `-0`, `+1`, underscores (PEP 515), Unicode/fullwidth digits, whitespace padding, and scientific/hex notation — each enumerated in the docstring and each pinned in `tests/test_scalars.py:154-218`. The `bool`-before-`int` ordering (`scalars.py:49,55`) correctly handles `bool` being an `int` subclass; the `noqa: TRY004` is justified inline because the parser uniformly raises `ValueError` for invalid *values* per the GraphQL `parse_value` contract.
- **Serializer asymmetry is deliberate and contract-protective.** `_serialize_bigint` raises `TypeError` for `str`/`float`/`Decimal`/`bool`/`None` (`scalars.py:82-86`), so a schema can never emit a value its own parser would reject. The outbound `bool` rejection is pinned end-to-end at the schema boundary (`tests/types/test_converters.py:635-652` asserts `"BigInt cannot serialize bool"` in `result.errors`).
- **`strawberry.scalar(name=...)` no-warning overload is used.** Registration goes through the `cls is None and name is not None` branch (`.venv/.../strawberry/types/scalar.py:254-266`), which returns a `ScalarDefinition` directly with no `DeprecationWarning` — matching the GLOSSARY claim (GLOSSARY.md:48). `parse_literal` is left `None`; graphql-core derives it from `parse_value` via `value_from_ast_untyped`, and the AST-literal input path is covered end-to-end by `test_scalars_api.py:543` (string literal) and `:579` (JSON-int literal) plus the example app's `scalar_specimen_by_signed_big(signed_big: BigInt)` input-position field.
- **`strawberry_config` ownership guards are airtight.** It rejects a directly-passed `scalar_map=` kwarg (`scalars.py:122-125`), rejects `extra_scalar_map` keys colliding with package scalars (`scalars.py:127-134`), defensively copies the caller dict (`dict(extra_scalar_map)`, no caller-dict mutation), and forwards every other kwarg verbatim to `StrawberryConfig`. Each call returns a fresh config with a fresh merged dict (no cross-call leakage). All four behaviors — collision, `scalar_map=` rejection, caller-dict immutability, instance independence, kwarg passthrough — are pinned in `tests/test_scalars.py:301-400`.
- **`StrawberryConfig` type shape is correct.** `_PACKAGE_SCALAR_MAP: dict[object, ScalarDefinition]` keys on the `BigInt` `NewType` object (the form `StrawberryConfig.scalar_map` expects), `extra_scalar_map` is keyword-only and typed `Mapping[object, ScalarDefinition] | None`, and the merged result is passed as `scalar_map=`. `__all__`/exports verified at `__init__.py:32,47` and `tests/base/test_init.py:36,51`.

### Summary

`scalars.py` is a small, single-responsibility module shipping the `BigInt` scalar and the `strawberry_config()` factory. The cycle diff against the baseline is empty (file unchanged this cycle), so this is a standing-code re-review. BigInt's serialize/parse correctness, arbitrary-precision bounds (verified past both the 32-bit and 53-bit limits, signed and unsigned), strict-rejection regex, deliberate input/output asymmetry, and the no-warning `strawberry.scalar(name=...)` registration path all check out and are pinned by an unusually thorough test suite spanning package unit tests, in-process schema round-trips, and live `/graphql/` HTTP tests. The `strawberry_config` factory's ownership guards (collision, `scalar_map=` rejection, caller-dict immutability, kwarg passthrough, instance independence) are all covered. GLOSSARY entries for `BigInt` (GLOSSARY.md:210-216) and `strawberry_config` (GLOSSARY.md:1231-1269) match the implementation verbatim — no drift. No High, Medium, or Low findings; qualifies as a no-findings (shape #1) + no-source-edit (shape #5) cycle.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass, no changes (267 files unchanged).
- `uv run ruff check --fix .` — pass, no changes (all checks passed).

### Notes for Worker 3
- No-findings file: every severity `None.`; no source/test/GLOSSARY/CHANGELOG edit in scope.
- Cycle diff `git diff c73b3d67fa8624349c202f400caf5c21ca08f32e -- django_strawberry_framework/scalars.py` is empty — file unchanged this cycle.
- No GLOSSARY-only fix in scope: GLOSSARY.md:210-216 (`BigInt`) and 1231-1269 (`strawberry_config`) match the source verbatim.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment/docstring changes — the module, parser, serializer, and factory docstrings accurately describe behavior (verified against the implementation and the live test suite); the `noqa: TRY004` comment is justified and current.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — no source edit was made this cycle (review-only, empty diff). Per AGENTS.md "Do not update CHANGELOG.md unless explicitly instructed" and the active plan (`docs/review/review-0_0_10.md`) is silent on a changelog entry for this item.

---

## Verification (Worker 3)

> Shadow-file dicta acknowledged: `docs/shadow/django_strawberry_framework__scalars.overview.md` strips comments/string tokens, so its line numbers are non-canonical. Original-source and artifact line references treated as canonical; shadow used only for control-flow/symbol counts (3 symbols, 0 control-flow hotspots, 0 repeated literals — all matched against source).

### Logic verification outcome
No-findings file: every High / Medium / Low reads `None.`; nothing to address or reject. Independently re-derived the dispatch-named load-bearing claims against source + tests rather than trusting the artifact prose:

- **BigInt bounds + strict-rejection.** Serialization is `str(value)` over arbitrary-precision Python `int` (`scalars.py:85`) — no truncation path exists. 64-bit edges pinned at `tests/test_scalars.py:47,52` (serialize `±2**63`) and `:121,126` (parse). Hostile-input rejections all pinned: `+1` (`:185`), `-0` (`:207`), leading-zero `01`/`007`/`-01` (`:199`), underscore `1_000`/`-1_000` (`:178,180`), `1e3`/`0x10`/`abc`/`1.9` (`:166-169`), whitespace-padded (`:157`), float `-1.0` (`:149`). Regex `^(0|-?[1-9][0-9]*)$` with `.fullmatch` (`scalars.py:27,58`) is consistent with each.
- **Parser/serializer asymmetry is deliberate.** Confirmed in source: `_parse_bigint` accepts `int` (`:55-56`) AND decimal `str` (`:57-64`); `_serialize_bigint` accepts `int` only and raises `TypeError` for everything else (`:84-86`). Both reject `bool` before the `int` check (`:49,82`) — correct given `bool` is an `int` subclass. Folding the shared ladder would re-couple the divergent accept-sets; DRY=None is sound.
- **`strawberry_config` ownership guards.** `scalar_map=` kwarg rejected structurally (`:122-125`, pinned `test_strawberry_config_rejects_scalar_map_kwarg` `:381-394` across `{}`/`None`/payload); collision check `_PACKAGE_SCALAR_MAP.keys() & extra.keys()` (`:127`, pinned `:322`); caller dict defensively copied via `dict(extra_scalar_map)` (`:126`, pinned no-mutation test `:312`); fresh merged dict per call (`:135`, pinned independent-instance test `:332-341`). All four hold.
- **No-warning `strawberry.scalar(name=...)` overload.** Re-read `.venv/.../strawberry/types/scalar.py`: the `cls is None and name is not None` branch returns a `ScalarDefinition` directly with NO `warnings.warn` (the deprecation `warnings.warn` lives only in the `wrap()` class-passing path below it). Registration at `scalars.py:91-95` passes `name=` with no `cls`, so it takes the no-warning branch — matches GLOSSARY.md:48 verbatim.

### DRY findings disposition
DRY=None confirmed. Three single-responsibility symbols; the only candidate hoist (the `bool`→`int` isinstance ladder) is correctly rejected because parser and serializer accept-sets must diverge. `"BigInt"` literal appears as `name=` and in distinct diagnostic strings — intentional siblings, not a hoistable constant. Shadow overview reports 0 repeated literals.

### Temp test verification
- No temp tests required — all claims verified by reading source + grepping existing pinned tests in `tests/test_scalars.py`.

### Shape #5 checks
1. `git diff --stat c73b3d67fa8624349c202f400caf5c21ca08f32e -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` — empty over all cycle-owned paths. `git diff c73b3d67... -- django_strawberry_framework/scalars.py` — empty.
2. Each Worker 2 section (`Fix report`, `Comment/docstring pass`, `Changelog disposition`) opens with `Filled by Worker 1 per no-source-edit cycle pattern.` ✓
3. No Low present (all `None.`); no GLOSSARY-only fix. GLOSSARY anchors `#bigint-scalar` and `#strawberry_config` exist and match the source. ✓
4. Changelog `Not warranted` cites BOTH AGENTS.md and the active plan's silence; `git diff -- CHANGELOG.md` empty. The cycle made no edits, so "internal-only / no source edit" framing is honest. ✓
5. Ruff: per Worker 2's empty-diff cycle the format/check are trivially clean (no changed lines); not re-run since no edit exists to lint.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `scalars.py` checklist box in `docs/review/review-0_0_10.md`.
