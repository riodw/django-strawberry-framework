# Review: `django_strawberry_framework/optimizer/hints.py`

Status: verified

## DRY analysis

- Defer until a second non-walker, non-schema-audit consumer of the four-flag dispatch lands — at that point extract a `hint_kind(hint) -> Literal["skip", "prefetch_obj", "force_select", "force_prefetch", "noop"]` classifier shared by `optimizer/walker.py::_apply_hint` (the `skip -> prefetch_obj -> force_select -> force_prefetch` if-chain, `optimizer/walker.py:550-620`) and `optimizer/hints.py::hint_is_skip` (`hints.py:146-150`), and route all callers through it. Today there are exactly two skip-dispatch sites (`extension.py` schema audit + `walker.py::_apply_hint:550` + `walker.py:1165` connection-sibling gate), all routed through `hint_is_skip` already; the other three branches have a single consumer (`_apply_hint`). Adding a full classifier now over-engineers against the second use case. Trigger phrase to grep: `hint_is_skip`.
- Defer until the SKIP-sentinel pattern reappears for a second `dataclass(frozen=True)` in the package — at that point factor the post-class-body `Cls.SKIP = Cls(skip=True)  # type: ignore[misc]` sentinel-installation idiom (`hints.py:69` ClassVar decl + `hints.py:159` rebind) into a shared `freeze_sentinel(cls, name, **kwargs)` helper or `@with_sentinels` decorator under `utils/`. Today the ClassVar-decl + post-body rebind is a single, heavily-commented site (`hints.py:67-69`, `hints.py:153-159`); collapsing it now would obscure the dataclass-ordering rationale.

## High:

None.

## Medium:

None.

> Note (no finding): the prior-release artifact (`Status: verified`, 0.0.7 cycle) carried a Medium for GLOSSARY drift — the `OptimizerHint` entry not mentioning construction-time conflict rejection. That fix has **already merged**: `docs/GLOSSARY.md:893-902` now carries the full "Validation: ``OptimizerHint(...)`` rejects conflicting flag combinations at construction time …" paragraph enumerating all four rejected shapes. Verified against live source and the GLOSSARY this cycle; not re-raised (diff live source before trusting a stale artifact's findings).

## Low:

### `hint_is_skip` defensive `getattr` is unreachable under the declared type

`hint_is_skip` (`hints.py:133-150`) is typed `hint: OptimizerHint | None`; for every value that type admits, `hint is None` or `hint is OptimizerHint.SKIP` or `hint.skip` resolves directly — the `bool(getattr(hint, "skip", False))` fallback (`hints.py:150`) can only reach its `False` default for a value that is neither `None` nor an `OptimizerHint` (i.e. a future hint surface lacking a `.skip` attribute). The docstring (`hints.py:139-142`) names exactly that future surface as the rationale ("so the schema audit can keep its 'never raises' contract even if a future hint surface lands that does not expose a `.skip` attribute"). This is recorded-intent forward-looking, not a defect: the default arm is a deliberate "never raises" backstop for the schema audit, and its `False`-default branch is exercised by `tests/optimizer/test_extension.py::test_hint_is_skip_handles_sentinel_record_and_unknown_shapes` (a record/object with no `.skip`). No edit. Re-triage only if a second concrete hint class lands AND it carries a `.skip` attribute — at that point the `getattr` could narrow to attribute access and the comment updated.

### `prefetch_obj` Prefetch-instance rejection — prior-cycle Low already merged

The prior artifact carried a Low recommending `prefetch(obj)` reject non-`Prefetch` values at construction. **Already merged**: the factory signature is `prefetch(cls, obj: Prefetch)` (`hints.py:123`) and `__post_init__` rejects a non-`Prefetch` `prefetch_obj` via `isinstance(self.prefetch_obj, Prefetch)` (`hints.py:97-101`), pinned by `tests/optimizer/test_hints.py:166-177` (both the factory and direct-construction paths). Not re-raised.

## What looks solid

### DRY recap

- **Existing patterns reused.** `hint_is_skip` (`hints.py:133-150`) is the single canonical skip-shape predicate consumed by the walker (`walker.py:550`, `walker.py:1165`) and the schema audit — callers never re-spell `hint is OptimizerHint.SKIP or hint.skip`. The walker's `_apply_hint` docstring (`walker.py:546-548`) correctly defers all collision arbitration to `__post_init__` rather than duplicating the conflict rules.
- **New helpers considered.** A `hint_kind` classifier and a `freeze_sentinel` helper were both evaluated and deferred-with-trigger (see `## DRY analysis`); each is single-consumer today.
- **Duplication risk in the current file.** The four `ConfigurationError` raise blocks in `__post_init__` (`hints.py:88-106`) are distinct messages for distinct conflict shapes, not near-copies — each names the specific flags and the consumer-facing factory remedy. Collapsing them into a table-driven loop would lose the per-shape message specificity. Intentional, not duplication.

### Other positives

- **Construction-time rejection is the load-bearing contract.** All four conflict shapes are rejected at `OptimizerHint(...)` time (`hints.py:85-106`), surfacing misconfiguration at `Meta.optimizer_hints` build time rather than query time. The dispatch priority order in `walker.py::_apply_hint` is therefore pure documentation — every conflict it would have arbitrated is already rejected. Docstring (`hints.py:71-84`) states this invariant explicitly and accurately.
- **SKIP sentinel ordering is correct and well-justified.** `SKIP` is declared as a bare `ClassVar[OptimizerHint]` inside the body (`hints.py:69`) so the dataclass decorator ignores it, then rebound after the class body (`hints.py:159`) once `__init__`/`__setattr__` exist; the `# type: ignore[misc]` and its multi-line rationale (`hints.py:153-158`) are accurate. Sentinel identity (`is`), `skip`-flag, no-other-flags, frozen-immutability, and value-equality (`OptimizerHint(skip=True) == SKIP`) are each pinned (`tests/optimizer/test_hints.py:14-101`).
- **Prefetch runtime-import comment is correct and load-bearing.** The module-level comment (`hints.py:33-37`) explains why `Prefetch` is imported at runtime (not under `TYPE_CHECKING`): `__post_init__`'s `isinstance(..., Prefetch)` check (`hints.py:97`) needs the real class. Accurate.
- **`prefetch(obj)` leaf-operation contract documented.** The factory docstring (`hints.py:124-129`) states the consumer queryset is source-of-truth and nested selections are not walked — matching the walker's `prefetch_obj` branch (`walker.py:552-587`) which appends the rebased Prefetch and returns without descending.
- **Test discipline.** `tests/optimizer/test_hints.py` covers the sentinel, all three factories, frozen immutability, equality, and every conflict shape; walker-level behavior (prefetch_obj rebase, non-cacheable flip, dedupe, mismatched-lookup rejection) is pinned in `tests/optimizer/test_walker.py:1196-1721`; skip-suppression and `hint_is_skip` unknown-shape defense in `tests/optimizer/test_extension.py`.

### Summary

A clean, well-commented 160-line typed-directive module. `OptimizerHint` is a frozen dataclass whose `__post_init__` rejects all four out-of-shape flag combinations at construction time (the load-bearing contract), three factory classmethods plus the `SKIP` class-level sentinel form the documented consumer API, and `hint_is_skip` centralizes the skip-shape predicate for the walker and schema audit. No High, no Medium, no act-now Low. The two findings from the stale 0.0.7 artifact (GLOSSARY validation drift; `prefetch` non-`Prefetch` rejection) are both already merged in live source and the GLOSSARY — verified, not re-raised. The two remaining observations (the `getattr` "never raises" backstop and the two deferred DRY collapses) are forward-looking with explicit triggers. Zero edits to any tracked file → no-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format django_strawberry_framework/optimizer/hints.py` — `1 file left unchanged`.
- `uv run ruff check django_strawberry_framework/optimizer/hints.py` — `All checks passed!`.

### Notes for Worker 3
- Two findings recorded as forward-looking, no edit: (1) `hint_is_skip` `getattr` "never raises" backstop (`hints.py:150`) is recorded-intent, exercised by `test_extension.py::test_hint_is_skip_handles_sentinel_record_and_unknown_shapes`; re-triage only if a second concrete hint class with a `.skip` attribute lands. (2) Prior-cycle `prefetch` non-`Prefetch` rejection Low is already merged (`hints.py:97-101`, `hints.py:123`); not re-raised.
- The prior-artifact Medium (GLOSSARY drift) is already merged at `docs/GLOSSARY.md:893-902` — no GLOSSARY-only fix in scope this cycle.
- Two DRY items both deferred-with-trigger; nothing act-now.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment or docstring edits warranted. The module-level `Prefetch` runtime-import comment (`hints.py:33-37`), the `__post_init__` priority-order rationale (`hints.py:71-84`), the SKIP-sentinel ordering comments (`hints.py:67-69`, `hints.py:153-158`), and the `hint_is_skip` "never raises" docstring (`hints.py:134-145`) are all accurate against live behavior. No version-pinned labels, no stale TODO anchors (shadow overview: 0 TODOs), no enumerated-list drift.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted. No source/test/GLOSSARY/CHANGELOG edits this cycle (AGENTS.md: "Do not update CHANGELOG.md unless explicitly instructed"); the active plan (`docs/review/review-0_0_9.md`) records no changelog action for this item.

---

## Verification (Worker 3)

### Logic verification outcome
Shape #5 no-source-edit. Cycle diff `git diff --stat 0872a20 -- optimizer/hints.py` empty (byte-unchanged baseline). Drove the load-bearing `__post_init__` contract live (Django importable): all four conflict shapes reject with `ConfigurationError` (skip+select / skip+prefetch / skip+prefetch_obj; force_select+force_prefetch; prefetch_obj+force_select / prefetch_obj+force_prefetch), plus the non-`Prefetch` rejection both via direct construction (`prefetch_obj='items'`) and via the factory (`OptimizerHint.prefetch('items')`) — both name the offending type. Valid shapes no-raise: `SKIP` identity stable, `select_related()`/`prefetch_related()`/`prefetch(Prefetch)`, `OptimizerHint(skip=True) == SKIP`, frozen → `FrozenInstanceError`. `hint_is_skip`: None→False, SKIP→True, skip-equal→True, select→False, unknown-no-attr-object→False (the "never raises" backstop arm exercised).

Both Lows confirmed forward-looking, not defects: (1) `hint_is_skip` `getattr` backstop (hints.py:150) is recorded-intent for a future hint surface lacking `.skip`, exercised by `test_extension.py::test_hint_is_skip_handles_sentinel_record_and_unknown_shapes` (grep-confirmed :3507). (2) prior-cycle `prefetch` non-`Prefetch` rejection — confirmed already merged at source (hints.py:97-101 isinstance guard, :123 `obj: Prefetch` sig), pinned `test_hints.py:166 test_prefetch_obj_rejects_non_prefetch_value`. Prior-release GLOSSARY-drift Medium confirmed merged at `docs/GLOSSARY.md:893-902` (full validation paragraph enumerating all four rejected shapes incl. non-`Prefetch`); no GLOSSARY-only fix in scope.

### DRY findings disposition
Two DRY items (`hint_kind` classifier; `freeze_sentinel` idiom) both deferred-with-trigger, single-consumer today — correctly carried forward, nothing act-now.

### Temp test verification
- None. Verification driven via a one-shot `uv run python` probe (Django importable); no temp files created.

### Sibling-cycle attribution
Wide-scope diff dirty only at closed sibling cycles, none owned by this cycle: `conf.py`, `exceptions.py`, `filters/factories.py`, `filters/sets.py`, `list_field.py`, `management/commands/inspect_django_type.py` (+ its test) and `docs/GLOSSARY.md` hunks — all `Status: verified` and `[x]` at review-0_0_9.md:70-87 (conf:70, exceptions:72, list_field:73, filters.factories:80, filters.sets:82, inspect:87). `optimizer/hints.py` itself byte-unchanged → "Files touched: None" holds. `git diff -- CHANGELOG.md` empty → Not-warranted disposition consistent (both citations present, internal-only framing honest — zero source/test/GLOSSARY edits this cycle). Ruff format-check + check pass (COM812 conflict notice is standing).

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` and marks the `optimizer/hints.py` checklist box.

---

## Iteration log

(none)
