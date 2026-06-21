# Review: `django_strawberry_framework/optimizer/_context.py`

Status: verified

## DRY analysis

- None — the module is itself the DRY resolution. `get_context_value` / `stash_on_context` centralize the context-shape dispatch the docstring describes (`_context.py:14-17`), consumed by both `optimizer/extension.py:60,63` (write) and `types/resolvers.py:45` (read). The five `DST_OPTIMIZER_*` key constants (`_context.py:34-38`) are single-sourced here and imported by every call site (`optimizer/extension.py:52-58`, `types/resolvers.py:39-43`) — no literal is re-spelled. The read-fallback (`get_context_value`) and write-catch-and-chain (`stash_on_context`) blocks are deliberate non-symmetric counterparts (read returns `default`; write chains to the dict path then catches-and-returns), documented inline at `_context.py:131-159`; folding them would conflate two distinct exception contracts, so not a candidate.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** The five `DST_OPTIMIZER_*` string keys (`_context.py:34-38`) are defined once and imported everywhere — `optimizer/extension.py:52-58` (all five, write side), `types/resolvers.py:39-43` (`FK_ID_ELISIONS`/`PLANNED`/`STRICTNESS`, read side). `DST_OPTIMIZER_PLAN` and `DST_OPTIMIZER_LOOKUP_PATHS` are write-only (extension stashes them; only the plan key is also read back at `extension.py:1004`). No key literal is re-spelled at any consumer.
- **New helpers considered.** A single merged read/write dispatcher was rejected: the read path returns `default` on a missing/failed lookup while the write path silently no-ops, and the two swallow different exception sets for different reasons (`get_context_value` catches `TypeError/KeyError/AttributeError` on `__getitem__`; `stash_on_context` splits into a catch-and-chain `setattr` block and a catch-and-return `__setitem__` block). The asymmetry is the contract, not duplication.
- **Duplication risk in the current file.** The two `isinstance(context, dict)` checks (`_context.py:83,88` read; `:127` write) and the parallel "object-first, then mapping" dispatch shape across both functions are intentional read/write mirroring (docstring `_context.py:51-61`, `:98-103`). They must stay parallel so a stash round-trips through the same branch the resolver reads from; collapsing them would couple the two contracts.

### Other positives

- **Read/write symmetry is the central correctness property and it holds.** `dict` instances take the mapping branch first on both sides (`context.get`/`context[key]=`), so a `dict` subclass with separate attribute storage round-trips through one branch; non-`dict` contexts try attribute access first and fall back to `__getitem__`/`__setitem__`. The docstrings spell out exactly why each branch order is load-bearing (e.g. `__slots__` mappings and bridged `StrawberryDjangoContext`).
- **Frozen-context safety is precise, not blanket.** Write swallows only `TypeError` (`MappingProxyType`, frozen dataclass, frozen `pydantic`) and `AttributeError` (Django locked `QueryDict`, a `dict` subclass) — and the comment at `_context.py:155-159` explicitly explains why `KeyError`/`RuntimeError` are deliberately *not* swallowed (a real dict never raises `KeyError` on assignment; a guarded mapping should surface). This is the root-cause posture, not an over-broad `except Exception`.
- **`_MISSING` sentinel correctly distinguishes absent-attribute from explicitly-stashed-`None`** (`_context.py:40-42,84-86`), so a value stashed as `None` is returned rather than triggering the `__getitem__` fallback.
- **Defensive-coerce stance is documented and scoped** (`_context.py:19-27`): the module docstring explicitly contrasts this "upstream genuinely allows absent/None" posture against `conf.py`'s consumer-input posture so the two are not conflated in a future refactor.
- **Test discipline.** Both load-bearing fallback shapes named in the `get_context_value` docstring are pinned: `tests/optimizer/test_extension.py::test_stash_on_non_dict_mapping_reads_correctly` (`__slots__` mapping) and `tests/optimizer/test_extension.py::test_get_context_value_swallows_attribute_error_from_getitem` (bridged-`AttributeError` shape) — both confirmed present. A refactor that removes the `__getitem__` fallback trips these pins.

### Summary

`_context.py` is the shared optimizer↔resolver context dispatch layer and is in excellent shape: two small, well-documented helpers with a clean read/write symmetry, precisely-scoped frozen-context exception swallowing, a sentinel that handles the stashed-`None` edge, and single-sourced `DST_OPTIMIZER_*` key constants consumed by both `optimizer/extension.py` and `types/resolvers.py`. The cycle diff is empty against both the cycle baseline (`12394edec9`) and HEAD, GLOSSARY prose about `dst_optimizer_plan` stashing (lines 588, 1319) accurately describes the optimizer's *use* of these keys without making any claim about the helper signatures, and both ruff commands are clean. Zero High/Medium/Low findings; genuine no-source-edit (shape #5) cycle.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; 289 files left unchanged.
- `uv run ruff check --fix .` — pass; all checks passed.

### Notes for Worker 3
- Zero High/Medium/Low findings; nothing to verify against a fix.
- Cycle diff empty vs both baseline (`12394edec9ad659fb42a3637f1f6306b4ef72c83`) and HEAD — confirmed before assuming shape #5.
- No GLOSSARY-only fix in scope: GLOSSARY references to `dst_optimizer_plan` / context stashing (`docs/GLOSSARY.md:588,1319`) describe the optimizer's *use* of these keys, not the `_context.py` helper signatures, so there is no drift to correct.
- DRY analysis is a single `None —` bullet (the module is the resolution); the read/write asymmetry was considered-and-rejected for merging.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

- No comment or docstring changes warranted. The module-, function-, and inline-comment documentation is accurate against the code: the `get_context_value` docstring's named test pins both exist, the `stash_on_context` catch-and-chain vs catch-and-return distinction (`_context.py:131-159`) matches the two `except` blocks exactly, and no TODO/stale-spec anchors are present (static overview reports 0 TODOs).

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

- **Not warranted** — no source, test, GLOSSARY, or CHANGELOG edits this cycle (review-only, zero findings). AGENTS.md #21 forbids unsolicited CHANGELOG edits, and the active plan `docs/review/review-0_0_11.md` records no changelog obligation for this item.

---

## Verification (Worker 3)

### Logic verification outcome
Zero High/Medium/Low findings — nothing to verify against a fix. Each Worker 2 section opens `Filled by Worker 1 per no-source-edit cycle pattern.` per shape #5. Independently confirmed the `None.` severities are genuine, not a missed defect:

- **Read/write symmetry holds.** `get_context_value` (`_context.py:45-92`) and `stash_on_context` (`:95-160`) both dispatch `dict`-first (mapping branch) then non-`dict` attribute-first with item-access fallback. A `dict` write routes through `__setitem__` and reads back through `.get`; a non-`dict` mapping whose `setattr` fails routes through `__setitem__` and reads back through `context[key]` after the `_MISSING` sentinel falls through. Round-trip parallelism verified at source.
- **`_MISSING` sentinel** (`:40-42`, `:84-86`) correctly distinguishes absent-attribute from explicitly-stashed-`None`: `getattr(context, key, _MISSING)` returns a stashed `None` value rather than falling to the `__getitem__` path.
- **Frozen-context swallow is precisely scoped.** Read catches `(TypeError, KeyError, AttributeError)` on `__getitem__` (`:91`). Write splits into catch-and-chain `(AttributeError, TypeError)` on `setattr` (`:131`) and catch-and-return `(TypeError, AttributeError)` on `__setitem__` (`:149`). `KeyError`/`RuntimeError` are deliberately NOT swallowed on the write path (comment `:155-159`: a real dict never raises `KeyError` on assignment; a guarded mapping should surface). Root-cause posture, not blanket `except Exception`.
- **Single-sourced key constants confirmed.** `grep -rn "DST_OPTIMIZER_"` proves the five `DST_OPTIMIZER_*` literals are defined once in `_context.py:34-38` and imported (never re-spelled) at `optimizer/extension.py:53-57` (all five, write side) and `types/resolvers.py:40-42` (`FK_ID_ELISIONS`/`PLANNED`/`STRICTNESS`, read side). `DST_OPTIMIZER_PLAN`/`LOOKUP_PATHS` write-only; plan read back at `extension.py:976` write / consumed for introspection. No literal duplication.
- **Test pins exist and exercise the load-bearing shapes.** `tests/optimizer/test_extension.py::test_stash_on_non_dict_mapping_reads_correctly` (`:3147`) uses a `__slots__` mapping (forces `setattr` failure → `__setitem__`, then `_MISSING`-fallthrough read via `__getitem__`); `::test_get_context_value_swallows_attribute_error_from_getitem` (`:3175`) raises `AttributeError` from `__getitem__` and asserts `default` is returned. Both read against live source confirm a refactor removing the fallback or narrowing the except tuple trips them.

### DRY findings disposition
Single `None —` bullet: the module IS the DRY resolution (centralized context-shape dispatch consumed by both extension write and resolvers read). The merged read/write dispatcher rejection is sound — read returns `default` while write no-ops, and the two swallow different exception sets for different reasons (the asymmetry is the contract). No forward owed.

### Temp test verification
- None used. Zero-edit cycle; no behavior suspicion to prove.
- Disposition: n/a.

### #4-vs-#5 gate
Genuine shape #5, not a missed #4. GLOSSARY `dst_optimizer_plan` prose is accurate and makes NO claim about `_context.py` helper signatures: `docs/GLOSSARY.md:588` describes the optimizer's *use* (`info.context.dst_optimizer_plan.fk_id_elisions`), and `:1319` describes the introspection stash ("Planned resolver keys and lookup paths are stashed on `info.context`"). Both describe the optimizer's use of the keys, not the dispatch helpers — no drift to correct, no GLOSSARY-only fix owed (a GLOSSARY-only fix would be disqualifying for #5).

### Zero-edit proof
`git diff 12394edec9ad659fb42a3637f1f6306b4ef72c83 -- django_strawberry_framework/optimizer/_context.py` empty AND `git diff HEAD -- <target>` empty; `git show HEAD:.../_context.py | diff` reports IDENTICAL. Target absent from `git diff --stat <baseline> -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` (stat fully clean this run, no #33 dirt). `git diff -- CHANGELOG.md` empty. `uv run ruff format --check` (1 file already formatted) + `uv run ruff check` (all checks passed) clean.

### Verification outcome
- `cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box.
