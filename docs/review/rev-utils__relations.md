# Review: `django_strawberry_framework/utils/relations.py`

Status: verified

## DRY analysis

- None — the module is the single canonical home for the four-branch Django cardinality classifier and the instance-accessor three-tier read. Every consumer imports from here rather than re-implementing either ladder: `relation_kind` / `is_many_side_relation_kind` are read by `optimizer/walker.py:112, 621-622, 816`, `optimizer/field_meta.py:131, 136, 196`, `optimizer/plans.py:565`, `orders/sets.py:76`, `types/resolvers.py:179, 267`, `types/base.py:1597`, `management/commands/inspect_django_type.py:241, 285`; `instance_accessor` is read by `optimizer/walker.py:479, 608, 1297`, `optimizer/field_meta.py:223`, `types/resolvers.py:265`, `types/finalizer.py:490`; the curated public surface is re-exported once at `utils/__init__.py:29` (consumed by `tests/utils/test_relations.py`). `MANY_SIDE_RELATION_KINDS` is published as one frozenset (`relations.py:14-16`) that `is_many_side_relation_kind` closes over (`relations.py:82`), so "many-side" has exactly one source of truth. No further factoring available without inventing artificial seams.

## High:

None.

## Medium:

None.

## Low:

### L1 — `instance_accessor` precomputed-slot guard treats an empty-string accessor as "present" (forward-looking)

`instance_accessor` (`relations.py:111-113`) reads the precomputed `FieldMeta.accessor_name` slot first and accepts it whenever `precomputed is not None`. For every real shape the package builds this is correct — `FieldMeta.accessor_name` is `None` only on hand-built instances (per `field_meta.py:108-109`: "both builders always populate it"), and a real Django accessor name is never the empty string. The `is not None` check (rather than truthiness) is the right discriminator today: it lets the genuinely-unset hand-built case fall through to the `get_accessor_name` / `name` tiers while a populated slot short-circuits. There is no current code path that can seat `accessor_name=""`. Defer-with-trigger: revisit only if a future builder can produce a `FieldMeta` whose `accessor_name` is the empty string (e.g. a synthetic descriptor); at that point the guard would need to read `precomputed` truthiness instead. No action now — behaviour is correct for every shape the package constructs.

### L2 — `_RelationFieldLike` Protocol's "always present" wording vs. the runtime `getattr(..., False)` defaults (forward-looking)

`_RelationFieldLike` (`relations.py:19-32`) annotates four `bool` attributes and its docstring states every caller hands in a real Django relation field whose flags "are always present," while the body of `relation_kind` (`relations.py:69-75`) still reads each flag through `getattr(field, "<flag>", False)`. The two agree in spirit: the Protocol's narrow annotation is the type-checker contract for the Django call sites, and the `getattr` defaults exist for the `SimpleNamespace` test doubles / any non-Django shape that legitimately omits a flag. No drift exists today. Defer-with-trigger: when a consumer shapes a `_RelationFieldLike` from a non-Django source (or the test surface stops using `SimpleNamespace`), fold the "always present" claim into an `attribute or False` accessor and drop the per-branch `getattr` repetition. (Carried verbatim from the prior cycle's deferred L2; trigger condition unchanged and still unmet.)

### L3 — submodule has no `__all__` while `utils/__init__.py` curates the public surface (forward-looking)

`relations.py` exposes `RelationKind`, `MANY_SIDE_RELATION_KINDS`, `_RelationFieldLike`, `relation_kind`, `is_many_side_relation_kind`, and now `instance_accessor` to a `from .relations import *` consumer (no `__all__` gate). The curated package-root surface is the three symbols re-exported at `utils/__init__.py:29, 34-37` (`RelationKind` / `is_many_side_relation_kind` / `relation_kind`); `instance_accessor` is deliberately submodule-public only (imported by path, not re-exported at the package root) which matches its internal-seam role. Sibling submodules (`utils/strings.py`, `utils/typing.py`) likewise carry no `__all__`, so this is consistent house style, not a defect. Defer-with-trigger: revisit when the sibling utils submodules grow an `__all__`, or when a fourth package-root public symbol lands here. (Carried verbatim from the prior cycle's deferred L3; trigger unchanged and still unmet.)

## What looks solid

### DRY recap

- **Existing patterns reused.** Canonical home for both the four-branch cardinality classifier and the instance-accessor three-tier read; every optimizer / types / orders / management / registry consumer imports from here (call sites enumerated in `## DRY analysis`). `MANY_SIDE_RELATION_KINDS` is the single source of truth for "many-side" membership; `is_many_side_relation_kind` closes over it (`relations.py:82`) so the predicate cannot drift from the literal. `FieldMeta.accessor_name` is precomputed via this same `instance_accessor` helper at `field_meta.py:223`, so the frozen-snapshot slot is consistent-by-construction with the live-descriptor read — no second accessor-derivation site.
- **New helpers considered.** Considered folding the four-branch dispatch into a `tuple[predicate, kind]` table; rejected — the `one_to_many` branch is a two-step composite test (`one_to_many` then `auto_created`) that does not fit a flat predicate table, and the straight-line if-chain reads more clearly. Considered collapsing `_RelationFieldLike` into a `TypedDict`; rejected — Django relation fields are class instances, not mappings, so the Protocol is the correct typing shape.
- **Duplication risk in the current file.** `getattr(field, "<flag>", False)` repeats across the `relation_kind` branches (`relations.py:69, 71, 72, 75`) and `getattr(field, "<attr>", None)` twice in `instance_accessor` (`relations.py:111, 114`), but each call reads a distinct attribute; folding through a `_flag(field, name)` helper would obscure the branch structure rather than DRY meaningful code. Intentional sibling-line repetition.

### Other positives

- **Stale-artifact L1 already merged — NOT re-raised.** The prior 0.0.7 on-disk artifact's lone substantive Low (the docstring did not explain the `one_to_many=True, auto_created=False → "many"` defensive fallback) is ALREADY FIXED in live source: `relations.py:54-61` carries the four-reason paragraph ("Any `one_to_many=True` shape without `auto_created` falls back to `"many"` as a defensive mapping; stock Django relation descriptors never produce that combination…") and cites the pinning test `test_relation_kind_classifies_one_to_many_as_many` by qualified path. Classic resolved-Low trap per the worker-1 recurring calibration — diffed live source first, did not re-raise.
- **`instance_accessor` (0.0.9 addition, absent from the prior artifact) verified correct.** Three-tier read precisely matches the two field shapes the package passes around: (1) precomputed `FieldMeta.accessor_name` slot wins (a frozen `FieldMeta` cannot answer `get_accessor_name()` live — the builders precompute it via this same helper at `field_meta.py:223`); (2) raw Django reverse-relation descriptor answers `get_accessor_name()`; (3) forward fields / test doubles fall back to `name`. The Round-4 S3 split (reverse FK without `related_name`: query name `"book"` vs instance accessor `"book_set"`) is the load-bearing reason this helper exists — `getattr(root, field.name)` would `AttributeError` and `prefetch_related` would reject the query name. All three tiers test-pinned: `test_relations.py:107` (get_accessor_name), `:118` (name fallback), `:124` (precomputed-slot wins over a deliberately-wrong live lookup). The docstring's "ONLY for the seams Django resolves against the instance" scoping matches the actual consumers (Phase-2 resolver `getattr` at `resolvers.py:265-283`, spec-032 synthesized relation connections, optimizer prefetch paths at `walker.py:479/608/1297`).
- **`is_many_side_relation_kind` is `None`-safe.** `kind in MANY_SIDE_RELATION_KINDS` returns `False` for `None` (frozenset membership, no `TypeError`); test-pinned at `test_relations.py:82`. The `RelationKind | None` annotation honestly admits the optional input the optimizer can hand it.
- **GFK is a task red-herring — confirmed absent by design, not a gap.** The prompt names "GFK" as a classification target, but `relation_kind` has no GenericForeignKey branch and needs none: GFK is rejected upstream at `types/base.py:1574` with a `ConfigurationError` (`related_model is None` guard) before any `relation_kind` call, so a GFK descriptor never reaches this classifier. M2M and reverse-M2M both legitimately map through the existing tokens (forward M2M → `"many"` via `many_to_many=True`; reverse M2M is an `auto_created` `one_to_many` descriptor → `"reverse_many_to_one"`). The 4-token `RelationKind` literal is the complete contract; no missing branch.
- **`_meta` reflection correctness.** This file performs no `_meta` access itself (zero ORM markers in the shadow overview); all `_meta` reflection lives in the callers (`field_meta.py`, `base.py`). The classifier reads only the four cardinality flags Django stamps directly on the field/rel descriptor (`many_to_many` / `one_to_many` / `one_to_one` / `auto_created`), the correct minimal contract — it stays decoupled from `_meta` traversal.
- **Closed-literal typing discipline.** `RelationKind` is a `TypeAlias` over a closed `Literal`; strict type-checkers flag any caller passing an unenumerated string. `from __future__ import annotations` (`relations.py:3`) demotes the parameter/return annotations to forward references, so the `Protocol` import is purely for the class base — no runtime cost on the hot classification path.
- **Re-export identity pinned.** `test_utils_init_reexports_match_submodule` (`test_relations.py:70-74`) asserts `utils.relation_kind is utils.relations.relation_kind` (identity, not equality) for all three re-exported symbols, so a future wrapper/shim would surface as a failure.
- **GLOSSARY drift quick-check: clean.** Zero `docs/GLOSSARY.md` hits for `relation_kind`, `RelationKind`, `is_many_side_relation_kind`, `MANY_SIDE_RELATION_KINDS`, `_RelationFieldLike`, or `instance_accessor`. These are internal mechanics; consumer-visible relation behaviour is documented under `Relation handling` without naming the helper symbols. No GLOSSARY edit in scope — correct convention per the internal-mechanics calibration.

### Summary

`utils/relations.py` is a focused 118-line module hosting the four-branch Django relation cardinality classifier (`relation_kind`), its closed-literal alias (`RelationKind`), the `None`-safe many-side predicate (`is_many_side_relation_kind`) over the single-source `MANY_SIDE_RELATION_KINDS` frozenset, and the 0.0.9-added three-tier `instance_accessor` (the Round-4 S3 query-name-vs-accessor seam). All logic verified correct against live source and the full `tests/utils/test_relations.py` grid. The prior 0.0.7 artifact's substantive Low is already merged into the live docstring (not re-raised per the resolved-Low calibration); the prompt's "FK/reverse-FK/O2O/M2M/reverse-M2M/GFK" framing is looser than the actual 4-token contract — GFK is rejected upstream by design, not a missing branch. No High, no Medium; three forward-looking Lows (empty-accessor guard, Protocol-vs-`getattr` wording, submodule `__all__`), all defer-with-trigger with unmet triggers. No source edit warranted → no-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass (265 files unchanged).
- `uv run ruff check --fix .` — pass (All checks passed).

### Notes for Worker 3
- L1 (empty-string accessor guard): forward-looking defer-with-trigger; trigger = a future builder seats `FieldMeta.accessor_name=""`. No path exists today; `is not None` guard correct for every constructed shape.
- L2 (Protocol "always present" vs `getattr` defaults): forward-looking defer-with-trigger; trigger = a `_RelationFieldLike` shaped from a non-Django source. Carried verbatim from prior cycle; unmet.
- L3 (submodule `__all__`): forward-looking defer-with-trigger; trigger = sibling utils submodules adopt `__all__` OR fourth package-root public symbol lands here. Carried verbatim from prior cycle; unmet.
- Prior 0.0.7 artifact's substantive L1 (fallback-branch docstring) ALREADY merged into live source (`relations.py:54-61`) — deliberately NOT re-raised.
- No GLOSSARY-only fix in scope (zero hits for any target symbol — internal mechanics, correct convention).
- Shadow overview at `docs/shadow/django_strawberry_framework__utils__relations.overview.md` consulted; module is 118 lines, outside `optimizer/` and `types/`, single control-flow hotspot (`relation_kind`, 5 branches) — no Medium-tier complexity concern.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment/docstring edits warranted. The `relation_kind` fallback paragraph and the `instance_accessor` three-tier rationale are already complete and accurate in live source; the `FieldMeta.accessor_name` field docstring (`field_meta.py:101-109`) correctly cross-references this helper. No stale comments, no restating-the-obvious, no docstring overpromise.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted. Per AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") AND the active plan `docs/review/review-0_0_9.md` is silent on changelog authorization for this cycle. No source edit was made; behaviour is unchanged.

---

## Verification (Worker 3)

### Logic verification outcome
No-source-edit cycle (shape #5). `git diff --stat 0872a20 -- django_strawberry_framework/utils/relations.py` is EMPTY (byte-unchanged); "Files touched: None" holds. The owned-paths diff stat shows other dirty files (conf.py, connection.py, exceptions.py, filters/factories.py, filters/sets.py, list_field.py, inspect_django_type.py, optimizer/extension.py, optimizer/selections.py, optimizer/walker.py, orders/factories.py, orders/inputs.py, types/__init__.py, types/base.py, types/finalizer.py, types/relay.py, docs/GLOSSARY.md, tests/management/*, tests/optimizer/test_selections.py) — every hunk attributes to a closed verified+`[x]` sibling cycle (logged in worker-3 memory accepted-cycles); none touch `relations.py`. `git diff -- CHANGELOG.md` empty.

Independently verified the two load-bearing claims LIVE (`DJANGO_SETTINGS_MODULE=config.settings`, all fakeshop models, 161 relation fields):
- **4-token `RelationKind` contract complete; GFK absent by design.** All four tokens observed (`forward_single`/`many`/`reverse_many_to_one`/`reverse_one_to_one`); none escaped the closed literal. GFK rejected UPSTREAM: `types/base.py #"is a GenericForeignKey"` raises `ConfigurationError` on the `related_model is None` guard (base.py:1573-1579) BEFORE `field_meta.relation_kind` is read at the `PendingRelation(...)` construction (base.py:1597) — a GFK descriptor never reaches `relation_kind`, so the missing branch is correct, not a gap. M2M→`"many"`, reverse-M2M→`"reverse_many_to_one"` confirmed via the existing tokens.
- **`instance_accessor` consistent-by-construction with `FieldMeta.accessor_name`.** Over all 161 relation fields, `FieldMeta.from_django_field(f).accessor_name == instance_accessor(f)` (zero mismatches) — the slot is derived through this same helper at `field_meta.py:223` (`accessor_name=instance_accessor(field)`). Precomputed-slot tier round-trips (`instance_accessor(fm) == fm.accessor_name`, zero failures). Round-4 S3 split is REAL: 6 reverse-FK-without-`related_name` fields where query name != instance accessor (`group`→`group_set`, `user`→`user_set`, `logentry`→`logentry_set`). `is_many_side_relation_kind(None) is False` (frozenset membership, no TypeError).

Three tiers test-pinned: `tests/utils/test_relations.py::test_instance_accessor_uses_get_accessor_name_for_reverse_relations` (:107), `::test_instance_accessor_falls_back_to_name_for_forward_fields` (:118), `::test_instance_accessor_prefers_precomputed_field_meta_slot` (:124, decisive — deliberately-wrong live `get_accessor_name` proves slot precedence). Fallback branch pinned at `::test_relation_kind_classifies_one_to_many_as_many` (:35); reexport identity at `::test_utils_init_reexports_match_submodule` (:70); None-safety at `::test_is_many_side_relation_kind_matches_list_valued_shapes` (:77).

Three Lows confirmed forward-looking with UNMET triggers: L1 (empty-string accessor guard — no path seats `accessor_name=""`; `is not None` correct today); L2 (Protocol "always present" vs `getattr` defaults — no non-Django `_RelationFieldLike` source; carried verbatim, all verbatim trigger phrasing present); L3 (submodule `__all__` — confirmed `relations.py`/`strings.py`/`typing.py` carry NO `__all__`, consistent house style). No GLOSSARY-only fix: `grep -c` over `docs/GLOSSARY.md` for all six target symbols = 0 (internal mechanics, correct convention).

### DRY findings disposition
DRY analysis = "None" (single canonical home; `MANY_SIDE_RELATION_KINDS` is the sole many-side source `is_many_side_relation_kind` closes over). Nothing to carry forward.

### Temp test verification
- None used — claims verified via one ephemeral `uv run python` probe (no files written) and grep of the live test grid.
- Disposition: n/a.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `utils/relations.py` checklist box in `docs/review/review-0_0_9.md`.

---

## Iteration log

(No re-passes yet.)
