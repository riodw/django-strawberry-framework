# Review: `django_strawberry_framework/scalars.py`

Status: verified

## DRY analysis

- None — the module is already minimally factored. `_parse_bigint` and `_serialize_bigint` are intentional asymmetric siblings (parser accepts `int`+`str`, serializer accepts `int` only; the docstring at `django_strawberry_framework/scalars.py:11-17` documents why the accept-sets differ), so no shared validation helper would be DRY without erasing that asymmetry. The two `dict(...)` calls in `strawberry_config` (`scalars.py:144` snapshot of `extra`, `scalars.py:153` fresh copy of `_PACKAGE_SCALAR_MAP`) build different dicts for different purposes (caller-input normalization vs. per-call fresh package map) and are not duplication. `_PACKAGE_SCALAR_MAP` is a single-entry registry by design (only `BigInt` needs mapping; `Upload` resolves through Strawberry's `DEFAULT_SCALAR_REGISTRY`); no second registry exists to consolidate against.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** `_PACKAGE_SCALAR_MAP` (`scalars.py:115-117`) is the single source of truth for package-mapped scalars; `strawberry_config` (`scalars.py:120-155`) is the sole registration path consumers use, and it copies the map per call (`dict(_PACKAGE_SCALAR_MAP)` at `scalars.py:153`) so no caller mutation leaks across schemas. `Upload` deliberately reuses Strawberry's `DEFAULT_SCALAR_REGISTRY` rather than adding a redundant `_PACKAGE_SCALAR_MAP` row (verified: `Upload in DEFAULT_SCALAR_REGISTRY` returns `True`).
- **New helpers considered.** A shared BigInt validation helper across `_parse_bigint` / `_serialize_bigint` was considered and rejected — the two functions raise different exception types (`ValueError` vs `TypeError`, matching the GraphQL `parse_value` / `serialize` contracts) and accept deliberately different input sets; folding them would obscure the documented input/output symmetry contract.
- **Duplication risk in the current file.** The two `dict(...)` calls in `strawberry_config` (`scalars.py:144`, `scalars.py:153`) are distinct constructions (caller-input copy vs fresh package-map copy), not a near-copy; correct as written.

### Other positives

- `Upload` re-export is correct. `from strawberry.file_uploads.scalars import Upload, UploadDefinition` (`scalars.py:25`) plus `__all__` (`scalars.py:35-40`) re-exports the built-in scalar with no scalar-map registration, exactly as the module docstring and the inline comment (`scalars.py:29-34`) describe. Confirmed at runtime that `Upload` is keyed in Strawberry's `DEFAULT_SCALAR_REGISTRY`, so an `Upload`-annotated field resolves in any schema with no `_PACKAGE_SCALAR_MAP` entry. The deliberate contrast with `BigInt` (which IS absent from the default registry and MUST be mapped) is sound.
- Strict-on-both-sides BigInt scalar: `_parse_bigint` rejects `bool` before the `int` check (`scalars.py:67`, since `bool` subclasses `int`), rejects `float`/leading-zero/underscore/plus/Unicode-digit strings via the `^(0|-?[1-9][0-9]*)$` anchored `fullmatch`, and `_serialize_bigint` rejects `str` so a schema cannot emit a value the parser would refuse — the input/output symmetry contract holds.
- `strawberry_config` ownership guards are complete: `scalar_map=` in `**config_kwargs` raises `ValueError` (`scalars.py:140-143`); `extra_scalar_map` keys colliding with package keys raise `ValueError` with a readable, sorted, name-resolved message (`scalars.py:145-152`); every other kwarg forwards verbatim to `StrawberryConfig`. The keyword-only `extra_scalar_map` + `**config_kwargs` passthrough compose cleanly.
- GLOSSARY is fully current: the `Upload` scalar entry (`docs/GLOSSARY.md:1357-1361`), `BigInt` scalar (`219-225`), and `strawberry_config` (`1265-1303`) all match the implementation, including the "no `_PACKAGE_SCALAR_MAP` entry because `DEFAULT_SCALAR_REGISTRY` owns it" contrast and the `scalar_map=`/`extra_scalar_map=` ownership rules. The grep-GLOSSARY-for-public-symbols step (the discriminator between shape #4 and shape #5) found no drift — genuine shape #5.

### Summary

`scalars.py` is a small, high-discipline module: a strict-both-sides `BigInt` scalar, a single-source `_PACKAGE_SCALAR_MAP`, and a well-guarded `strawberry_config` factory, plus the spec-037 `Upload`/`UploadDefinition` re-export. The `Upload` re-export and the "no scalar-map entry needed" handling are both correct and runtime-verified against Strawberry's `DEFAULT_SCALAR_REGISTRY`. Both `git diff` against the cycle baseline (`44b3325f`) and against HEAD are empty — the `Upload` work already landed in HEAD (commit `7d39523b`), so this cycle produces zero source edits. GLOSSARY is accurate with no drift. No High / Medium / Low findings; genuine no-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — no changes (289 files left unchanged).
- `uv run ruff check --fix .` — pass (All checks passed!).

### Notes for Worker 3
Shape #5 no-source-edit cycle. Both `git diff 44b3325f17f98f0db566e6ee89214232c2bc4c1f -- django_strawberry_framework/scalars.py` and `git diff HEAD -- …` are empty; the `Upload` re-export work already landed in HEAD. Zero findings (all severities `None.`). Load-bearing claim re-verified at runtime: `Upload in DEFAULT_SCALAR_REGISTRY` is `True`, so the `Upload` re-export needs no `_PACKAGE_SCALAR_MAP` entry — the module's central correctness claim. No GLOSSARY-only fix in scope — GLOSSARY `Upload` scalar / `BigInt` / `strawberry_config` entries all match implementation (no drift). No per-Low dispositions (no Lows raised).

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment/docstring edits. The module docstring (`scalars.py:1-18`), the `Upload` re-export comment (`scalars.py:29-34`), the BigInt regex comment (`scalars.py:42-44`), the TRY004 suppression rationale (`scalars.py:68-72`), and the `_parse_bigint` / `_serialize_bigint` / `strawberry_config` docstrings all accurately describe current behavior. No stale spec references, no obsolete TODOs.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted. No source edits this cycle (both diffs empty). Per AGENTS.md "Do not update CHANGELOG.md unless explicitly instructed" and the active plan `docs/review/review-0_0_11.md` carrying no changelog directive for this item.

---

## Verification (Worker 3)

### Logic verification outcome
No High / Medium / Low findings to address — all severities `None.`, and confirmed genuine (not lazy) by an independent logic read of the full module:
- **`_parse_bigint`**: bool rejected before the int check (bool subclasses int), int passthrough, string gated by the anchored `^(0|-?[1-9][0-9]*)$` fullmatch (rejects float/leading-zero/underscore/plus/Unicode-digit/`-0`), else-`ValueError`. The TRY004 suppression on the bool raise is correct (uniform `ValueError` parse_value contract).
- **`_serialize_bigint`**: bool rejected, int → `str(value)`, else `TypeError` — strict on output so a schema cannot emit a value the parser would refuse; input/output symmetry contract holds.
- **`strawberry_config`**: `scalar_map=` in kwargs → `ValueError`; `extra_scalar_map` key collision with package keys → sorted name-resolved `ValueError`; fresh `dict(_PACKAGE_SCALAR_MAP)` per call (no caller-mutation leak); all other kwargs forwarded verbatim.

Load-bearing claims independently re-verified at runtime against the installed strawberry-graphql (`strawberry.schema.types.scalar.DEFAULT_SCALAR_REGISTRY`):
- `Upload in DEFAULT_SCALAR_REGISTRY` → **True**, and `Upload not in _PACKAGE_SCALAR_MAP` → so the re-export needs no scalar-map entry (the module's central correctness claim).
- `BigInt in DEFAULT_SCALAR_REGISTRY` → **False**, and `BigInt in _PACKAGE_SCALAR_MAP` → True; the deliberate contrast is sound — BigInt MUST be mapped.
- `__all__ == ['BigInt', 'Upload', 'UploadDefinition', 'strawberry_config']`; `UploadDefinition` re-exported. The `scalar_map=` and collision guards both raise `ValueError` at runtime.

### DRY findings disposition
Single DRY item is the justified `- None`: the `_parse_bigint` / `_serialize_bigint` asymmetry (different accept-sets, different exception types per the GraphQL parse_value/serialize contracts) correctly resists a shared helper; the two `dict(...)` calls in `strawberry_config` build different dicts; `_PACKAGE_SCALAR_MAP` is a single-entry registry with no second registry to consolidate. Module at DRY floor — no carry-forward.

### Temp test verification
- No temp tests created. No source edit, no new behavior to pin; `tests/test_scalars.py` present (the standing permanent suite). Disposition: none needed.

### Shape #5 gate
- Zero-edit proof both ways: `git diff 44b3325f…  -- django_strawberry_framework/scalars.py` empty AND `git diff HEAD -- …` empty; `scalars.py` absent from `git diff --stat 44b3325f… -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` (stat empty). `git diff HEAD -- CHANGELOG.md` empty.
- Each Worker 2 section opens `Filled by Worker 1 per no-source-edit cycle pattern.` (Fix report / Comment-docstring pass / Changelog disposition). No GLOSSARY-only fix in scope.
- Changelog `Not warranted` cites BOTH AGENTS.md #21 and plan silence — accepted.
- `uv run ruff format --check` and `uv run ruff check` both pass on `scalars.py`.

### #4-vs-#5 gate (genuine #5, not a missed #4)
The only GLOSSARY hunk vs HEAD is at line 305 (relation-cardinality validation) — the standing AGENTS.md #33 concurrent-maintainer work, outside scalars.py territory. The three scalars-owned GLOSSARY entries read accurate against live source:
- `Upload` scalar (1357-1361): "no `_PACKAGE_SCALAR_MAP` entry because it already resolves through `DEFAULT_SCALAR_REGISTRY` — the deliberate contrast with `BigInt`" — runtime-confirmed true.
- `BigInt` scalar (219-225): strict parser/serializer rules and wire-format prose match `_parse_bigint`/`_serialize_bigint`.
- `strawberry_config` (1265-1301): `scalar_map=` refusal, collision `ValueError`, kwargs passthrough, fresh map per call — all match source + runtime.
No owed GLOSSARY edit; genuine shape #5.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `scalars.py` checklist box `- [x]` in `docs/review/review-0_0_11.md`.
