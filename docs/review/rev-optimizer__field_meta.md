# Review: `django_strawberry_framework/optimizer/field_meta.py`

Status: verified

## DRY analysis

- **Defer-with-trigger: collapse the reverse-O2O nullable test onto already-read flags instead of re-calling `relation_kind(field)`.** In `field_meta.py::FieldMeta._from_field_shape` (`field_meta.py:196-198`) the nullable branch evaluates `relation_kind(field) == "reverse_one_to_one"`, which re-reads `one_to_one` and `auto_created` off the raw descriptor via `getattr`, while the same method already extracts `is_m2m`/`is_o2m` (`field_meta.py:188-189`), reads `auto_created` (`field_meta.py:191`), and reads `one_to_one` (`field_meta.py:204`) on its own. The reverse-O2O predicate is exactly `one_to_one and auto_created`, so the branch could read it from locals. NOT act-now: routing through `relation_kind` keeps the single canonical cardinality classifier (`utils/relations.py::relation_kind`) as the only place that owns the `one_to_one and auto_created` → `"reverse_one_to_one"` rule; re-spelling it inline would duplicate the classifier's branch logic locally — the exact anti-DRY this package avoids. Defer until `relation_kind` gains a 6th cardinality, OR until a future derivation also needs the resolved `kind` inside `_from_field_shape`; at that trigger, compute `kind = relation_kind(field)` once at the top and reuse it for both the nullable gate and the new consumer.

## High:

None.

## Medium:

None.

## Low:

### `_has_composite_pk` reads `model._meta` directly while its sibling `_target_pk_name` reads it defensively

`_target_pk_name` (`field_meta.py:238`) reads `getattr(model, "_meta", None)` and returns `None` when `_meta` is absent, because — per its own docstring — `FieldMeta` is also built from fabricated field shapes on the resolver path (`types/resolvers.py::_field_meta_for_resolver`) whose `related_model` may be a lightweight stand-in without `_meta`. `_has_composite_pk` (`field_meta.py:246`) instead reads `model._meta.pk_fields` as a bare attribute access. Today this is safe: `_has_composite_pk(related_model)` is only reached inside the `fk_id_elision_eligible` conjunction (`field_meta.py:211-220`) after `target_pk_name is not None` has already short-circuited the `and` chain, and `target_pk_name` is non-`None` only when `_target_pk_name` found a live `_meta` — so any descriptor reaching `_has_composite_pk` is guaranteed to carry `_meta`. The asymmetry is therefore harmless, but it is a latent footgun: a future caller invoking `_has_composite_pk` outside that guarded conjunction (a new elision-eligibility variant, or a direct unit probe with a stand-in `related_model`) would hit `AttributeError` on `model._meta`, not the graceful `False` the sibling helper models. Recommended change (maintainability only, no behavior change today): mirror the defensive read — `meta = getattr(model, "_meta", None); if meta is None: return False` — so the two module-private `_meta`-reading helpers share one access discipline. Forward-looking; not actionable until a second `_has_composite_pk` call site lands.

### Module docstring's `__init_subclass__` / `field_map` build-site label is a cross-file pin to re-verify next cycle

The module docstring (`field_meta.py:11-17`) asserts the map is "Built once per `DjangoType` at class-creation time (in `__init_subclass__`)" and "stored canonically on `DjangoTypeDefinition.field_map`". This is a cross-file claim about `types/base.py`'s build site. It reads accurate against the current `field_map` consumption (`field_map[snake_case(field.name)]` at `types/base.py:1565` confirms a pre-built map exists at finalize time). Calibration from prior cycles (exceptions.py `OptimizerError` version-pin rot; export_schema `CHANGELOG-23` token rot): site- and version-pinned docstring labels rot across releases. No edit warranted this cycle — the label matches live source — but flagged so the next reviewer re-greps `__init_subclass__` vs. the actual builder hook if `types/base.py`'s class-creation site is renamed. Recorded-intent Low, no action.

## What looks solid

### DRY recap

- **Existing patterns reused.** `_from_field_shape` is the single shared shape-builder consumed by both the canonical `from_django_field` entry point (`field_meta.py:160`) and the resolver-side test-double fallback `types/resolvers.py::_field_meta_for_resolver` (`types/resolvers.py:229`); the cardinality-gated nullable rule, the `getattr`-defaulted relation-shape reads, and the FK-id elision derivation all live in that one method so the two call sites cannot drift (documented `field_meta.py:178-181`). Cardinality classification is delegated wholesale to `utils/relations.py::relation_kind` / `is_many_side_relation_kind` (the `relation_kind` / `is_many_side` properties, `field_meta.py:128-136`) rather than re-spelled; accessor-name divergence is delegated to `utils/relations.py::instance_accessor` (`field_meta.py:223`). No relation-shape logic is duplicated against the walker or resolver layers.
- **New helpers considered.** Folding the reverse-O2O nullable predicate off `relation_kind` into inline `one_to_one and auto_created` was evaluated and rejected (would duplicate the classifier's branch logic locally) — recorded as a defer-with-trigger DRY bullet, not an act-now extraction. Mirroring `_target_pk_name`'s defensive `_meta` read into `_has_composite_pk` was evaluated and deferred (single call site, currently guarded) — recorded as a forward-looking Low.
- **Duplication risk in the current file.** The two module-private `_meta`-reading helpers (`_target_pk_name`, `_has_composite_pk`) read the same descriptor attribute with divergent defensiveness — intentional-but-asymmetric, documented as the Low above. The 14 `getattr` reflective reads are the deliberate "no per-shape branching" strategy for the four documented input shapes (forward field, reverse FK, M2M, O2O), not a near-copy family. Zero repeated string literals (shadow overview confirms).

### Other positives

- **Reflective-access audit clean (shadow "Calls of interest": 14x `getattr` / 2x `hasattr` / 1x `len`).** Every `getattr` carries a safe default matching the documented "read defensively" contract (`_DjangoFieldLike` docstring, `field_meta.py:34-44`). The two `hasattr` calls (`field_meta.py:155`) are the explicit guard converting a late walker `AttributeError` into a typed, call-site `OptimizerError` naming the bad input — exactly the documented intent, test-pinned (`tests/optimizer/test_field_meta.py::test_from_django_field_rejects_non_django_input`, `::test_from_django_field_rejects_partial_shape`).
- **`_meta` ORM marker (shadow, `field_meta.py:246`) justified.** Composite-PK detection reads `_meta.pk_fields` with a `getattr` default and a `len(...) > 1` test, correctly modelling Django 5.2+ `CompositePrimaryKey` (`pk_fields` is a tuple) vs. pre-5.2 (`pk_fields` absent → `getattr` default `None` → returns `False`). Forward-compatible and backward-safe.
- **GFK / unresolved-target path is graceful by construction.** A `GenericForeignKey` (`related_model=None`) builds a valid `FieldMeta` (`related_model=None`, `target_pk_name=None`, `fk_id_elision_eligible=False`) without raising — the hard rejection is owned upstream at consumption time in `types/base.py` (`types/base.py:1566-1572`), keeping `FieldMeta` a pure metadata snapshot with no policy. Proxy models inherit `_meta.pk` from the concrete model, so `_target_pk_name` resolves correctly with no special-casing.
- **`fk_id_elision_eligible` conjunction is conservative and correctly ordered (`field_meta.py:211-220`).** It excludes many-side relations, reverse relations (`auto_created`), non-PK `to_field` connectors (`target_field_name == target_pk_name`), unresolved targets (`related_model is not None` / `target_pk_name is not None`), and composite PKs — each gate test-pinned across the forward-FK / one-to-one / reverse-FK / M2M / scalar cases. The `and` ordering guarantees `_has_composite_pk` is only reached on a `related_model` already proven to carry `_meta`.
- **Cardinality-gated `nullable` rule is self-consistent and well-defended.** Many-side cardinalities short-circuit to `False` (manager/queryset is never `None`; renders `list[...]`), reverse-O2O short-circuits to `True` (related row may be absent), everything else follows `field.null` with a `False` default — defending against `ForeignObjectRel`'s class-level `null=True` leaking through (docstring `field_meta.py:64-74`, pinned by `test_from_django_field_reverse_one_to_one_is_nullable`, `test_from_django_field_reverse_many_to_many`, `test_from_django_field_many_to_many`).
- **Frozen, slotted dataclass with `is_relation=False` default-first ordering (`field_meta.py:50`)** is correct for an immutable per-`DjangoType` cached snapshot — no request-scope or mutable state, process-safe to cache on the definition (`test_field_meta_is_frozen`). `TYPE_CHECKING`-gated `models` / `RelationKind` imports (`field_meta.py:28-31`) keep the runtime import surface to `exceptions` + `utils.relations`, no import-time Django coupling.

### Summary

`FieldMeta` is a clean, immutable metadata snapshot that centralizes Django relation-shape derivation behind one shared `_from_field_shape` builder, delegating cardinality classification and accessor naming to `utils/relations` rather than re-deriving them. `_meta` reflection is correct across all relation kinds (forward FK, reverse FK, M2M both directions, forward/reverse O2O), composite-pk detection is forward/backward-version-safe, GFK and proxy models are handled gracefully without special-casing, and the `OptimizerError` guard converts a would-be late walker `AttributeError` into a typed call-site failure. No High, no Medium. Two forward-looking Lows (defensive-`_meta` asymmetry between the two private helpers; a site-pinned docstring label to re-verify) and one defer-with-trigger DRY bullet (reverse-O2O nullable predicate vs. `relation_kind`), none requiring a source edit this cycle. No-source-edit cycle (shape #5): zero edits to any tracked file; both ruff commands clean.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format --check django_strawberry_framework/optimizer/field_meta.py` — `1 file already formatted` (pass; the COM812-formatter-conflict line is the standing repo-wide config notice, not a file issue).
- `uv run ruff check django_strawberry_framework/optimizer/field_meta.py` — `All checks passed!`

### Notes for Worker 3
Shadow overview used: `docs/shadow/django_strawberry_framework__optimizer__field_meta.overview.md` (+ `.stripped.py`). Per-Low dispositions: (1) `_has_composite_pk` defensive-`_meta` asymmetry — forward-looking, currently safe by the `fk_id_elision_eligible` `and`-ordering guard (`field_meta.py:211-220`); no edit. (2) module docstring `__init_subclass__` / `field_map` build-site label — verified accurate vs. live `types/base.py:1565`; recorded-intent re-check next cycle, no edit. DRY bullet is defer-with-trigger, no edit. No GLOSSARY-only fix in scope: `docs/GLOSSARY.md` carries no entry for any `field_meta.py` public symbol (`FieldMeta`, `from_django_field`, `fk_id_elision_eligible`, `target_pk_name`, `reverse_connector_attname`, `accessor_name`, `_has_composite_pk` all absent); the composite-PK / FK-id-elision prose at `docs/GLOSSARY.md:541,1063,1068` describes downstream plan/finalizer behavior, not this module's API, and reads accurate. Stale prior-cycle `rev-optimizer__field_meta.md` (Jun 4, `Status: verified`, 0.0.7-era) replaced wholesale per the recurring stale-artifact pattern; active plan box `review-0_0_9.md:93` confirmed unchecked.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment/docstring edits warranted: the module, class, and method docstrings accurately describe implemented behavior (nullable cardinality gate, FK-id elision conjunction, `_meta` defensive reads, the four documented input shapes), and the two inline comments (`field_meta.py:182-183` target-field read-once; `field_meta.py:192` nullable-rule pointer) are correct and non-restating. The site-pinned `__init_subclass__` label was verified against live source, not edited.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. **Not warranted** — no source change this cycle (review-only, zero tracked-file edits). Per `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan's silence on changelog edits for review cycles, no `CHANGELOG.md` entry is warranted.

---

## Verification (Worker 3)

### Logic verification outcome
Shape #5 no-source-edit cycle. `git diff --stat 0872a20 -- field_meta.py` empty (byte-unchanged from baseline); CHANGELOG diff empty. No High/Medium. Both Lows verified as correctly forward-looking / recorded-intent, neither a live defect:

- **`_has_composite_pk` vs `_target_pk_name` `_meta`-asymmetry (riskiest Low).** Confirmed safe-today AND correctly forward-looking via live repro. A `from_django_field` call whose `related_model` is a stand-in lacking `_meta` yields `target_pk_name=None`, `fk_id_elision_eligible=False`, **no raise** — the `fk_id_elision_eligible` `and`-chain (`field_meta.py::FieldMeta._from_field_shape`, `field_meta.py:211-220`) short-circuits at `target_pk_name is not None` (3rd conjunct) before `_has_composite_pk` is ever evaluated. Independently confirmed the footgun is real-but-hypothetical: a direct `_has_composite_pk(StandIn)` call (the future unguarded site the Low describes) raises `AttributeError` on `model._meta`. So the asymmetry is harmless under every live call path and the Low's "not actionable until a second call site lands" disposition is correct.
- **Module docstring `__init_subclass__` / `field_map` build-site label (recorded-intent Low).** Cross-file pin to `types/base.py`; flagged for next-cycle re-grep, no edit warranted — accurate vs live source. Correct disposition.

### DRY findings disposition
Single defer-with-trigger bullet (collapse reverse-O2O nullable test onto already-read `one_to_one`/`auto_created` locals instead of re-calling `relation_kind(field)`). Correctly NOT act-now: routing through `relation_kind` (`utils/relations.py::relation_kind`) keeps the single canonical cardinality classifier from being re-spelled inline. Deferred; no edit.

### Temp test verification
- Live no-DB probes under `/tmp` (transient, outside repo): `/tmp/repro_fieldmeta.py` (and-chain short-circuit safety + forward-footgun confirmation), `/tmp/repro_fieldmeta2.py` (composite-PK across 3 version regimes, GFK degenerate, OptimizerError guard). Not promoted — behavior already pinned by the permanent suite (see below).
- Cited test pins all grep-match at `tests/optimizer/test_field_meta.py`: `test_from_django_field_rejects_non_django_input:196`, `test_from_django_field_rejects_partial_shape:211`, `test_field_meta_is_frozen:221`, `test_from_django_field_reverse_one_to_one_is_nullable:183`, `test_from_django_field_reverse_many_to_many:120`, `test_from_django_field_many_to_many:145`.

### Cross-checks
- Composite-PK detection (`_has_composite_pk`, `field_meta.py:244-247`): live-confirmed 5.2+ tuple `len>1`→True, `len==1`→False, pre-5.2 absent→`getattr` default `None`→False. Forward/backward version-safe.
- GFK degenerate (`related_model=None`): builds a valid `FieldMeta` (`related_model=None`, `target_pk_name=None`, `fk_id_elision_eligible=False`), no raise.
- `OptimizerError` guard (`field_meta.py:155-159`): live-confirmed it fires on inputs missing `name`/`is_relation`, message names the bad input.
- Sibling-cycle attribution: wider owned-scope diff (`django_strawberry_framework/`, `tests/`, `docs/GLOSSARY.md`, `CHANGELOG.md`) dirty only at conf.py, exceptions.py, filters/factories.py, filters/sets.py, list_field.py, management/commands/inspect_django_type.py (+ its test), docs/GLOSSARY.md — all CLOSED sibling cycles (per-file `rev-*.md` verified, `[x]` in review-0_0_9.md). `field_meta.py` itself byte-unchanged, so "Files touched: None" holds.
- Ruff: `format --check` → `1 file already formatted`; `check` → `All checks passed!` (COM812 notice is the standing repo-wide config warning).
- Changelog: `git diff -- CHANGELOG.md` empty; **Not warranted** cites BOTH `AGENTS.md` and the active plan's silence. Internal-only framing honest (zero source change).

### Verification outcome
cycle accepted; verified

---

## Iteration log

(none)
