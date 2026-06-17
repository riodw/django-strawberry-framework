# Review: `django_strawberry_framework/optimizer/field_meta.py`

Status: verified

## DRY analysis

- Defer-with-trigger: the FK-id-elision predicate, `_target_pk_name`, and the composite-PK guard exist in TWO modules — the build-time canonical producer here (`field_meta.py::FieldMeta._from_field_shape` #"fk_id_elision_eligible=", `field_meta.py::_target_pk_name`, `field_meta.py::_has_composite_pk`) and the walk-time stamped-or-recompute consumers in `walker.py::_can_elide_fk_id` (walker.py:854-889), `walker.py::_target_pk_name` (walker.py:892-900), and the inline composite-PK guard (walker.py:873-880). This is **intentional dual-path today**, not a duplication defect: the `field_meta.py` versions always operate on a resolved `related_model` and compute the canonical value that gets *stamped* onto the dataclass slots; the `walker.py` versions are `getattr(field, "<slot>", None)`-first shims that return the stamped value when present (walker.py:862-864, 894-896) and only recompute from a raw Django descriptor on the test-double / unstamped fallback path. The two predicates are byte-equivalent in their recompute tails (same seven `and` clauses, same composite-PK exclusion), so a single shared predicate would be the DRY shape — but the field_meta side takes a *model* and the walker side takes a *field-or-FieldMeta*, so a naive merge would fuse two different input contracts. **Defer until the walker's raw-descriptor recompute fallback is removed** (i.e. when every `_can_elide_fk_id` / `_target_pk_name` caller is guaranteed to pass a stamped `FieldMeta`); at that point both walker shims collapse to a pure slot read and the recompute logic lives only here. Trigger to grep: "walker's raw-descriptor recompute fallback is removed". Forwarded to the optimizer folder pass (`docs/review/rev-optimizer.md`) for cross-file confirmation since the consolidation spans two files.

## High:

None.

## Medium:

None.

## Low:

### Implicit ordering invariant between `_has_composite_pk` and `_target_pk_name`

`_has_composite_pk` (field_meta.py:244-247) reads `model._meta` with a **raw attribute access** (`model._meta.pk_fields`), while its sibling `_target_pk_name` (field_meta.py:238) defends `_meta` with `getattr(model, "_meta", None)` precisely because resolver-path fabricated `related_model` stand-ins may lack `_meta`. The two are not symmetric. They stay safe only because the `fk_id_elision_eligible` boolean (field_meta.py:211-220) short-circuits `target_pk_name is not None` (line 214) **before** calling `_has_composite_pk(related_model)` (line 219) — and `target_pk_name` is non-`None` only when `_target_pk_name` already resolved `meta.pk.name`, which guarantees `related_model._meta` exists by the time `_has_composite_pk` runs. The invariant is correct but undocumented: a future caller invoking `_has_composite_pk` outside this guarded chain (or a reorder of the `and` clauses placing the composite check before the pk-name check) would `AttributeError` on a `_meta`-less stand-in. Recommend a one-line docstring note on `_has_composite_pk` stating it assumes a `_meta`-bearing model and is only reached after `_target_pk_name` resolves, OR (smaller) mirror the `getattr(model, "_meta", None)` guard so the two helpers read `_meta` identically. Comment-pass nicety; no behavior change and no current bug.

### `Any` typing on `_from_field_shape`'s `field` parameter widens the documented contract

`_from_field_shape(cls, field: Any, ...)` (field_meta.py:163) takes `Any`, while the public `from_django_field` takes the `_DjangoFieldLike` Protocol (field_meta.py:139). The helper's docstring (field_meta.py:164-181) carefully states both call sites "have already established that the input exposes the field-shaped attribute surface" — that surface is exactly `_DjangoFieldLike` plus the `getattr`-defaulted relation attrs. The `Any` annotation is defensible (the resolver-side test-double caller in `types/resolvers.py::_field_meta_for_resolver` at resolvers.py:291 may pass a shape that omits `is_relation`, which is why `is_relation` is passed as a keyword rather than read off the field), so the parameter genuinely cannot be the same Protocol. No change recommended — recording only to note the `Any` is a deliberate consequence of the two-caller contract, not loose typing. Defer permanently unless a third caller lands that shares the full `_DjangoFieldLike` surface, at which point a narrower union annotation would document intent.

## What looks solid

### DRY recap

- **Existing patterns reused.** Relation classification is single-sourced through `utils/relations.py`: `relation_kind`/`is_many_side` properties (field_meta.py:128-136) delegate to `relation_kind` / `is_many_side_relation_kind`, and the nullable cardinality gate (field_meta.py:196) reuses `relation_kind(field) == "reverse_one_to_one"` rather than re-deriving the reverse-O2O shape from raw flags. `accessor_name` is computed via the shared `instance_accessor` helper (field_meta.py:223), the same helper the resolver and prefetch paths consume — so the reverse-relation query-name-vs-accessor split (`utils/relations.py::instance_accessor`) is computed in exactly one place and stamped here. The typed input guard reuses `OptimizerError` (field_meta.py:156) rather than a bare `AttributeError`.
- **New helpers considered.** A merged FK-id-elision predicate shared with `walker.py` was evaluated and explicitly deferred (see `## DRY analysis`) — the field-vs-model input contract divergence makes a merge net-negative until the walker's recompute fallback is removed. No other helper candidate found; the module is already the canonical producer the package docstring (field_meta.py:1-18) names.
- **Duplication risk in the current file.** `target_field` is read once (field_meta.py:184) and consulted twice (lines 187, 209) per the inline comment — the near-duplicate `getattr(target_field, "name"/"attname", None)` reads are intentional sibling extraction of two distinct columns, not a factoring miss. The seven-clause elision boolean (field_meta.py:211-220) mirrors the walker recompute tail by design (single source of the rule's *shape*); divergence risk is mitigated by both being test-pinned.

### Other positives

- **No source change since baseline.** `git log 14910230..HEAD -- field_meta.py` is empty and `git diff HEAD -- field_meta.py` is empty, confirming spec-035's optimizer hardening did not touch this file (as the change context predicted). Reviewed against current source regardless.
- **Defensive `_meta` read is correctly scoped.** `_target_pk_name` (field_meta.py:227-241) reads `_meta` via `getattr` with a documented rationale (resolver-path fabricated `related_model` stand-ins), failing closed to "no resolvable target pk" / elision-disabled rather than raising — the right failure mode for an optimization hint.
- **Cardinality-gated nullable rule is self-consistent and well-documented.** Many-side cardinalities short-circuit to `nullable=False` (field_meta.py:193-194) so a consumer reading `nullable` never has to re-check `many_to_many`/`one_to_many` first; the field docstring (field_meta.py:60-74) explains the `ForeignObjectRel` `null=True` class-default leak this defends against. Every shape (scalar, nullable scalar, forward FK, reverse FK, reverse M2M, forward M2M, forward O2O, reverse O2O) is pinned in `tests/optimizer/test_field_meta.py:31-193`.
- **FK-id-elision metadata is comprehensively gated.** The eligibility boolean excludes many-side, reverse, non-PK `to_field` (`target_field_name == target_pk_name`), auto-created, unresolved-target, and composite-PK relations — and `test_field_meta.py` asserts `fk_id_elision_eligible` for each shape (lines 41, 63, 82, 141, 156, 174, 192).
- **Frozen + slotted dataclass.** `@dataclass(frozen=True, slots=True)` (field_meta.py:50) gives an immutable, low-overhead snapshot — correct for a value cached once per `DjangoType` on `field_map` and read concurrently across requests (no per-request mutation, no shared mutable state). Frozenness is test-pinned (`test_field_meta_is_frozen`, line 221).
- **TYPE_CHECKING import block** (field_meta.py:28-31, `# pragma: no cover`) keeps `django.db.models` and the `RelationKind` alias out of runtime import cost while preserving annotations; runtime imports are limited to `exceptions` and `utils.relations` — strictly inward, no circular-import risk through the optimizer package init.

### Summary

`field_meta.py` is a clean, well-factored canonical producer of optimizer-relevant Django field metadata, unchanged since the review baseline and exhaustively test-pinned across all eight relation shapes. No High or Medium findings. The frozen/slotted dataclass, the cardinality-gated nullable rule, the comprehensively-gated FK-id-elision predicate, and the single-sourced relation classification via `utils/relations.py` are all correct and defensible. Two Lows are recorded: an undocumented `_meta`-resolution ordering invariant between `_has_composite_pk` and `_target_pk_name` (comment-pass nicety, no current bug), and a note that the `Any` typing on `_from_field_shape` is a deliberate two-caller-contract consequence rather than loose typing. The one real DRY opportunity — the dual-path FK-id-elision predicate shared with `walker.py` — is intentional today (build-time stamp vs walk-time stamped-or-recompute) and deferred with an explicit trigger; forwarded to the optimizer folder pass for cross-file confirmation.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
None — no-source-edit cycle.

### Tests added or updated
None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — 270 files unchanged.
- `uv run ruff check --fix .` — all checks passed (only the pre-existing COM812-vs-formatter config warning).

### Notes for Worker 3
- Both Lows are forward-looking / comment-pass-only with no source edit this cycle:
  - **`_has_composite_pk` ordering invariant** — correct today; safe because `fk_id_elision_eligible` short-circuits `target_pk_name is not None` (field_meta.py:214) before `_has_composite_pk(related_model)` (line 219). Recorded as a comment-pass nicety / optional `getattr` mirror; no behavior change.
  - **`Any` on `_from_field_shape`** — deliberate two-caller-contract consequence (resolver-side caller may omit `is_relation`); deferred permanently unless a third full-`_DjangoFieldLike` caller lands.
- The DRY finding (dual-path FK-id elision shared with `walker.py`) is **deferred with an explicit trigger** ("walker's raw-descriptor recompute fallback is removed") and **forwarded to `docs/review/rev-optimizer.md`** for cross-file confirmation. Not an act-now item.
- No GLOSSARY-only fix in scope. GLOSSARY:563 references the elision *stash* mechanism (extension/walker level), accurate relative to this file; TREE.md:218/291 entries accurate.
- Baseline confirmation: `git log 14910230..HEAD -- field_meta.py` empty; `git diff HEAD -- field_meta.py` empty. Spec-035 did not touch this file.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment/docstring edits this cycle. The two Lows note optional comment improvements (a `_has_composite_pk` ordering-invariant note; an `Any`-is-deliberate note) but neither is required for correctness and both are recorded as defer/optional. Existing docstrings are accurate and non-stale: the module docstring, the `FieldMeta` attribute docstrings, the cardinality-gated nullable rationale, and the `_target_pk_name` defensive-`_meta` rationale all match the implementation.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted. No source change this cycle (empty HEAD diff and empty baseline diff), so there is nothing to record. Per AGENTS.md ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan (`docs/review/review-0_0_10.md`) carrying no changelog directive for this item, no changelog entry is warranted.

---

## Verification (Worker 3)

Shadow-file dictum applied: the shadow strips comments and string literals (its `## Repeated string literals: None` and stripped docstrings) and its line numbers do not match source — original `field_meta.py` line numbers and this artifact's references are canonical; the shadow was used only to confirm control flow (one hotspot at `_from_field_shape`, 14 `getattr` / 2 `hasattr` / 1 `len`, single `_meta` raw read at line 246). Shadow not edited.

### Logic verification outcome

Shape #5 no-source-edit cycle. Baseline confirmed clean: `git diff HEAD -- field_meta.py` empty, `git diff 14910230 -- field_meta.py` empty, `git log 14910230..HEAD -- field_meta.py` empty (HEAD `5724429c`). Spec-035 did not touch this file. Reviewed against current source.

- **High / Medium: none.** Confirmed against source and the eight-shape test pin.
- **Low 1 (`_has_composite_pk` / `_target_pk_name` ordering invariant) — genuinely no-action, invariant proven protected.** `_has_composite_pk` has exactly ONE call site package-wide (`grep -rn "_has_composite_pk"` = field_meta.py:219 def+call only), inside the `fk_id_elision_eligible` `and` chain. The chain evaluates left-to-right with short-circuit: `related_model is not None` (213) → `target_pk_name is not None` (214) → ... → `not _has_composite_pk(related_model)` (219). `target_pk_name` (set at 186 from `_target_pk_name`) is non-`None` only when `_target_pk_name` reached `meta.pk.name` (227-241), which requires `getattr(model, "_meta", None)` to be present. Therefore by the time line 219 runs, `related_model._meta` is guaranteed to exist, so `_has_composite_pk`'s raw `model._meta` read (246) cannot `AttributeError`. No path reads `_target_pk_name`/`_has_composite_pk` when the elision boolean is False/unsafe. The documented risk (a future unguarded caller, or a reorder placing the composite check before the pk-name check) is forward-looking, not a current defect. Comment-pass nicety; correctly recorded as defer/optional with no behavior change.
- **Low 2 (`Any` typing on `_from_field_shape`) — genuinely no-action, deliberate two-caller contract.** Confirmed the second caller: `types/resolvers.py::_field_meta_for_resolver` (resolvers.py:291) calls `FieldMeta._from_field_shape(field, is_relation=True)` passing `is_relation` as a keyword (not read off the field), exactly the fabricated-shape caller the artifact and the helper docstring (164-181) describe. The `Any` is a consequence of the two distinct input contracts, not loose typing. Deferred permanently absent a third full-`_DjangoFieldLike` caller; sound.

### DRY findings disposition

The dual-path FK-id-elision predicate (`field_meta.py` build-time canonical producer vs `walker.py` walk-time stamped-or-recompute consumer) is **intentional dual-path, deferred-with-trigger, and forwarded**. Verified directly:
- `walker.py::_can_elide_fk_id` (walker.py:854-889) is `getattr(field, "fk_id_elision_eligible", None)`-first (862-864) and only recomputes from raw Django descriptors on the unstamped/test-double fallback; its recompute tail is the same seven `and` clauses with the composite-PK exclusion as field_meta's boolean (211-220).
- `walker.py::_target_pk_name` (walker.py:892-900) is `getattr(field, "target_pk_name", None)`-first (894-896) with raw `_meta.pk.name` recompute fallback.
- Input-contract divergence is real and confirmed: field_meta helpers take a **model** (`_target_pk_name(model)`, `_has_composite_pk(model)`); walker shims take a **field-or-FieldMeta**. A naive merge would fuse two input contracts — net-negative until the walker's raw-descriptor recompute fallback is removed. Trigger ("walker's raw-descriptor recompute fallback is removed") is falsifiable and grep-able.
- **Forward recorded and correctly disposed.** Forwarded to the optimizer folder pass `docs/review/rev-optimizer.md`, which does not yet exist; the plan box at `review-0_0_10.md:100` (`folder pass: optimizer/ -> docs/review/rev-optimizer.md`) is open `[ ]`. Per the established pattern, a forward to an unopened folder-pass artifact is correctly disposed by the citation here plus the open box; absence of the target file is expected, not a defect. The cross-file claim itself (byte-equivalent recompute tails, divergent input contracts spanning exactly two files) is verified above.

### Metadata-production correctness across relation shapes

All eight shapes pinned in `tests/optimizer/test_field_meta.py`, each asserting `fk_id_elision_eligible` and `target_pk_name`: scalar (line 41), nullable scalar (44-50), forward FK (62-63, eligible True), reverse FK (81-82, False), reverse M2M (140-141, False), forward M2M (155-156, False), forward O2O (173-174, eligible True), reverse O2O (191-192, False). Cardinality-gated nullable rule pinned per shape; frozen-dataclass pinned (`test_field_meta_is_frozen`, 221); typed-input guard pinned (`test_from_django_field_rejects_non_django_input` / `_rejects_partial_shape`, 196-218); accessor-name divergence pinned (98-117). Production logic matches the documented per-shape contract.

### Temp test verification

None used. The ordering-invariant short-circuit and the dual-path contract were provable by source read + grep (single call site; getattr-first shims) without behavioral simulation; the eight-shape production is already exhaustively pinned in the permanent suite. No new test introduced, so pytest not run preemptively.

### Shape #5 terminal checks

1. `git diff --stat HEAD -- django_strawberry_framework/optimizer/field_meta.py` empty (and baseline `14910230` diff empty). No this-cycle edits.
2. Each Worker 2 section opens with `Filled by Worker 1 per no-source-edit cycle pattern.` — confirmed (Fix report, Comment/docstring pass, Changelog disposition).
3. Both Lows are forward-looking/comment-pass with explicit defer dispositions; the DRY is forwarded. No GLOSSARY-only fix in scope (disqualifier absent).
4. Changelog `Not warranted` cites BOTH AGENTS.md and the active plan's silence; `git diff -- CHANGELOG.md` empty — consistent. Internal-only framing matches scope (no public-API surface changed; zero diff).
5. `uv run ruff format --check field_meta.py` = already formatted; `uv run ruff check field_meta.py` = all checks passed (only the pre-existing COM812-vs-formatter config warning).

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `optimizer/field_meta.py` checklist box at `docs/review/review-0_0_10.md:95`.
