# Review: `django_strawberry_framework/utils/` (folder pass)

Status: verified

## DRY analysis

- None — the three siblings (`relations.py`, `strings.py`, `typing.py`) are each a self-asserted canonical home for their concern, share zero local imports, share zero cross-sibling repeated literals (per shadow overviews: `relations.py` has internal RelationKind-member literals only; `strings.py` and `typing.py` are literal-empty), and are wired to the same dependency-direction contract (utils is a leaf consumed by `optimizer/` and `types/`, never the reverse). Per-file DRY canonical-home framings already named the right resolution homes for every deferred trigger; the folder pass has no act-now consolidation to surface and no cross-sibling helper-extraction candidate today. Three deferred per-file triggers carried forward as a single inventory under `### DRY recap` below so the next cycle can grep them without re-reading three artifacts.

## High:

None.

## Medium:

None.

## Low:

### `utils/__init__.py` re-exports `unwrap_return_type` ahead of any in-package consumer

`utils/__init__.py:22,30-31` re-exports `unwrap_return_type` alongside `unwrap_graphql_type`, but `unwrap_return_type` has zero in-package consumers today — every grep-discoverable consumer routes through `unwrap_graphql_type` at `optimizer/extension.py:344,427`. The dual-export is intentional and documented (`utils/__init__.py:10-14` explicitly names the "upcoming schema-factory consumer" as the rationale, the same trigger Worker 1 deferred three separate `rev-utils__typing.md` Lows under per `worker-memory/worker-1.md:47`). The three-check `__init__.py` pattern (`__all__` honesty, future-exports docstring, consumer-docstring citation chain) lands two-of-three clean and one-of-three partial: `__all__` is honest (`utils/__init__.py:24-32`), the docstring at lines 10-14 names the future-extension framing in exactly the shape `queryset` is named at lines 16-17, but the consumer-docstring citation chain is partial because only one of the two re-exported `typing` helpers has live consumers. Forward-looking only — the asymmetry is intentional and the documentation already absorbs it. Defer until the schema-factory consumer lands and `unwrap_return_type` gets its first call site; at that point the same cycle that adds the call site should also tighten the `utils/__init__.py:10-14` docstring from "upcoming" to "lives at `<call-site>`" to close the citation chain.

### Single trigger fans out three deferred actions across `utils/typing.py`

The schema-factory-consumer trigger named at `utils/__init__.py:13-14` gates three distinct deferred-Low actions inside `rev-utils__typing.md`: (a) the `Optional[list[T]]` / `list[T] | None` peel decision (peel-here vs require-pre-peeled input), (b) `unwrap_return_type`'s first call site landing (which would also close the `__init__.py` citation chain in the Low above), and (c) the `_peel(rt, *, predicates: tuple[...])` consolidation if a third unwrap variant lands alongside. These are recorded individually in `rev-utils__typing.md:20-39` and again in `rev-utils__typing.md:131` (DRY disposition fusing actions a and c under one trigger); the folder-pass record consolidates them as one trigger × three actions so the next cycle that fires the trigger can route all three through a single edit batch instead of three sequential ones. Forward-looking only; defer-with-trigger phrasing preserved verbatim from the per-file artifacts.

### `_check_n1` `kind: str | None` widening vs `is_many_side_relation_kind(kind: RelationKind | None)`

`types/resolvers.py:119-126` declares `_check_n1`'s `kind` keyword-only parameter as `str | None`, which is wider than the `RelationKind | None` signature of `is_many_side_relation_kind` it calls at `types/resolvers.py:144`. Production callers always pass a real `RelationKind` member, so the widening is forward-compatible rather than buggy, but it is the only consumer call site in the package that admits a non-`RelationKind` `str` against the `utils/relations.py:74` contract. Worker 1 surfaced this in `rev-utils__relations.md:23-25` ("Forward to `rev-utils.md` folder pass only if the same wide-`str` admission pattern appears on a second consumer"); the second-consumer trigger has not fired, so the disposition stays forward-looking with the canonical resolution home now named: when a second `str | None`-widened call site lands, tighten `_check_n1`'s `kind` parameter to `RelationKind | None` rather than relaxing the `utils/relations.py` callee signature. Defer until that second consumer surfaces.

## What looks solid

### DRY recap

- **Existing patterns reused.** All three siblings are canonical homes for their concern with zero parallel implementations elsewhere in the package: `RelationKind` / `relation_kind` / `is_many_side_relation_kind` / `MANY_SIDE_RELATION_KINDS` at `utils/relations.py:7-77` consumed by `optimizer/walker.py:14,74,451,623`, `optimizer/field_meta.py:27-29,104,106,111,156`, `types/relations.py:24,53`, `types/resolvers.py:46,144,196`; `snake_case` / `pascal_case` at `utils/strings.py:19-71` consumed by `optimizer/walker.py:15,175,558,695`, `types/base.py:42,174,820`, `types/converters.py:52,292`, `types/finalizer.py:48,194`; `unwrap_graphql_type` / `unwrap_return_type` at `utils/typing.py:14-65` consumed by `optimizer/extension.py:45,344,427` (only `unwrap_graphql_type` has live consumers today; `unwrap_return_type` is exported for the upcoming schema-factory per `utils/__init__.py:13-14`).
- **New helpers considered.** A folder-level shared peeler (`_peel(rt, *, predicates: tuple[...])`) was considered and rejected: the two existing helpers in `utils/typing.py` have intentionally-asymmetric peel-depth (full-peel `while hasattr` loop in `unwrap_graphql_type` vs one-layer `getattr(..., "of_type", None) is not None` gate in `unwrap_return_type`), and the asymmetry encodes consumer-shape difference (graphql-core wrapper stacks are unbounded; Python annotation peel is one-layer-at-a-time so callers can inspect nesting). A third style or third unwrap helper is the explicit trigger for revisiting both; `utils/strings.py:13-15` and `rev-utils__typing.md:38-39` both name the trigger verbatim. A single-side relation-kind predicate (`is_single_side_relation_kind`) mirror was considered and rejected per `rev-utils__relations.md:36` — every package consumer uses the many-side predicate or compares `kind == "reverse_one_to_one"` directly, so the mirror would have only one real consumer.
- **Duplication risk in the current file.** Zero cross-sibling repeated literals. `utils/relations.py`'s shadow overview shows internal `RelationKind`-member literals only (3x `reverse_many_to_one`, 2x each `reverse_one_to_one` / `forward_single` / `auto_created`) — every one is an intentional alias-member or `getattr`-flag-name and `mypy` would catch a typo because `MANY_SIDE_RELATION_KINDS` is annotated `frozenset[RelationKind]`. `utils/strings.py` and `utils/typing.py` shadow overviews both report zero repeated literals. No cross-sibling literal appears in two-plus files — the folder-pass repeated-literal check passes cleanly.

### Other positives

- **One-way dependency direction confirmed.** Every sibling overview reports zero local imports — `utils/relations.py`, `utils/strings.py`, and `utils/typing.py` each rely only on standard-library typing primitives (`typing.Literal`, `typing.Protocol`, `typing.TypeAlias`, `typing.Any`, `typing.get_args`, `typing.get_origin`). No utils sibling imports from `optimizer/`, `types/`, `registry`, `conf`, `scalars`, or any other package module. The leaf direction is structural, not merely aspirational. `utils/__init__.py:20-22` imports only from the three siblings; no relative-up imports exist.
- **`__init__.py` three-check pattern.** `__all__` audit pinned by `tests/utils/test_relations.py:46-50` and `utils/__init__.py:24-32` enumerates exactly the seven re-exported names with no orphans or extras (`RelationKind`, `is_many_side_relation_kind`, `pascal_case`, `relation_kind`, `snake_case`, `unwrap_graphql_type`, `unwrap_return_type`). The docstring at `utils/__init__.py:1-18` names every submodule with its public symbols and explicitly frames the future-extension contract for `queryset` (lines 16-17) and the rationale for the dual `typing` export (lines 10-14). Three-of-three siblings have consumer-citation-chain evidence (relations: 4 consumer call sites; strings: 5 consumer call sites; typing: 2 consumer call sites for `unwrap_graphql_type` with `unwrap_return_type` explicitly framed as forward-export).
- **Test coverage matches public surface.** `tests/utils/test_relations.py` pins all seven branches of `relation_kind`, every `is_many_side_relation_kind` literal + `None`, the `RelationKind` `typing.get_args` literal-membership audit, and the `utils/__init__.py` re-export `__all__` audit. `tests/utils/test_strings.py` pins both helpers' documented input domains plus the asymmetric empty-segment-collapse contract on `pascal_case("")`. `tests/utils/test_typing.py` walks all eight `unwrap_*` branches including the `None` passthrough and the bare-`list` → `Any` sentinel. Three test files, three siblings, no orphan tests or untested branches.
- **Canonical-home framing held three cycles running.** Cycles 28 (`rev-utils__relations.md`), 29 (`rev-utils__strings.md`), and 30 (`rev-utils__typing.md`) each closed as zero-line-footprint consolidated single-spawns with the same shape: 0H/0M/3L all forward-looking, DRY analysis self-asserting canonical-home status, changelog `Not warranted`. The folder pass is the fourth in the chain and inherits the same disposition.

### Summary

`django_strawberry_framework/utils/` is a three-sibling leaf folder housing seven public symbols (`RelationKind`, `relation_kind`, `is_many_side_relation_kind`, `snake_case`, `pascal_case`, `unwrap_graphql_type`, `unwrap_return_type`) re-exported through `utils/__init__.py`. Each sibling is the canonical home for its concern with the consumer citation chain documented in the per-file artifacts; the three-check `__init__.py` pattern lands clean (`__all__` honest, future-exports docstring matching the GLOSSARY roadmap, consumer-docstring citation chain complete for six-of-seven symbols and explicitly forward-framed for the seventh per `utils/__init__.py:10-14`). One-way dependency direction (utils → standard library only; consumed by `optimizer/` and `types/`) is confirmed structural via zero local imports across all three sibling overviews. Zero cross-sibling repeated literals. Zero High/Medium findings. Three forward-looking Lows: the `unwrap_return_type` consumer-citation gap is intentional and absorbed by the docstring (defer until the schema-factory consumer lands), the schema-factory trigger fans out three actions in `utils/typing.py` (consolidate as one trigger × three actions for the next cycle that fires it), and the `_check_n1` `kind: str | None` widening vs `is_many_side_relation_kind(kind: RelationKind | None)` is a single-consumer-site forward-compatible widening with the second-consumer trigger gating folder-level consolidation.

---

## Fix report (Worker 2)

Consolidated single-spawn — folder pass with 0H/0M/3L all forward-looking and DRY analysis `None` (self-asserted canonical-home). No source edit. The cycle qualifies for the consolidated shape per `worker-2.md:166` ("no-findings file/folder/project pass") and `worker-2.md:163` ("all Lows are explicitly forward-looking per Worker 1's own prose"). Folder pass is the fourth in the four-cycle utils/ chain (cycles 28-30 closed identically); precedent now 31 deep.

### Files touched

- None (no source edit; artifact-only consolidated no-op).

### Tests added or updated

- None (no source edit; existing `tests/utils/test_relations.py`, `tests/utils/test_strings.py`, `tests/utils/test_typing.py` already pin every public symbol enumerated in `utils/__init__.py:24-32` per the artifact's `### Test coverage matches public surface` block).

### Validation run

- `uv run ruff format .` — pass / no changes (118 files left unchanged)
- `uv run ruff check --fix .` — pass / no changes (All checks passed)

### Notes for Worker 3

- Shadow file used — None this pass (folder-pass; the three per-sibling shadow overviews under `docs/shadow/utils/` were referenced inside Worker 1's artifact body, but Worker 2 made no source edit so re-reading was unnecessary).
- Intentionally-rejected findings with contradicting evidence — None. All three Lows are forward-looking with explicit defer-with-trigger phrasing from Worker 1; no in-cycle edit required.
- Deferred findings and their trigger conditions — three forward-looking Lows, each carrying a verbatim trigger from Worker 1's prose:
  - L1 (`utils/__init__.py` re-exports `unwrap_return_type` ahead of any in-package consumer; `rev-utils.md:19-21`). Trigger verbatim: "Defer until the schema-factory consumer lands and `unwrap_return_type` gets its first call site; at that point the same cycle that adds the call site should also tighten the `utils/__init__.py:10-14` docstring from 'upcoming' to 'lives at `<call-site>`' to close the citation chain." Canonical resolution home: `utils/__init__.py:10-14` docstring tightening, paired with the new `unwrap_return_type` call site in the schema-factory consumer cycle.
  - L2 (Single trigger fans out three deferred actions across `utils/typing.py`; `rev-utils.md:23-25`). Trigger verbatim (from `utils/__init__.py:13-14`): the schema-factory consumer's first call site landing. Three fan-out actions (per `rev-utils__typing.md:20-39,131`): (a) the `Optional[list[T]]` / `list[T] | None` peel decision (peel-here vs require-pre-peeled input), (b) `unwrap_return_type`'s first call site landing (also closes the `__init__.py` citation chain in L1), and (c) the `_peel(rt, *, predicates: tuple[...])` consolidation if a third unwrap variant lands alongside. Canonical routing: the next cycle that fires the trigger should route all three through a single edit batch instead of three sequential ones.
  - L3 (`_check_n1` `kind: str | None` widening vs `is_many_side_relation_kind(kind: RelationKind | None)`; `rev-utils.md:27-29`). Trigger verbatim (from `rev-utils__relations.md:23-25`): "Forward to `rev-utils.md` folder pass only if the same wide-`str` admission pattern appears on a second consumer." The folder pass has now confirmed the second-consumer trigger has NOT fired — `_check_n1` at `types/resolvers.py:119-126` remains the only consumer admitting a non-`RelationKind` `str` against the `utils/relations.py:74` contract. Canonical resolution home (named verbatim in `rev-utils.md:29`): "when a second `str | None`-widened call site lands, tighten `_check_n1`'s `kind` parameter to `RelationKind | None` rather than relaxing the `utils/relations.py` callee signature." Defer until that second consumer surfaces.

---

## Comment/docstring pass

Batched into this consolidated single-spawn — qualifies per `worker-2.md:166` (no-findings folder pass) and `worker-2.md:163` (all Lows forward-looking with verbatim defer phrasing). No source edit, so no docstring touched.

### Files touched

- None.

### Per-finding dispositions

- L1 (`utils/__init__.py` re-exports `unwrap_return_type` ahead of any in-package consumer): no docstring edit. Worker 1's own prose at `rev-utils.md:21` reads verbatim "The dual-export is intentional and documented (`utils/__init__.py:10-14` explicitly names the 'upcoming schema-factory consumer' as the rationale, the same trigger Worker 1 deferred three separate `rev-utils__typing.md` Lows under per `worker-memory/worker-1.md:47`)" and "Forward-looking only — the asymmetry is intentional and the documentation already absorbs it." Both self-adjudicate against an in-cycle edit (per pattern 11 in `worker-memory/worker-2.md`).
- L2 (Single trigger fans out three deferred actions across `utils/typing.py`): no docstring edit. Worker 1's own prose at `rev-utils.md:25` reads verbatim "the folder-pass record consolidates them as one trigger × three actions so the next cycle that fires the trigger can route all three through a single edit batch instead of three sequential ones. Forward-looking only; defer-with-trigger phrasing preserved verbatim from the per-file artifacts." The folder-pass artifact body IS the consolidation record per pattern (d) in `worker-memory/worker-2.md` (folder-pass-as-DRY-consolidator) — re-recapping inside a sibling docstring would invert its role.
- L3 (`_check_n1` `kind: str | None` widening): no docstring edit. Worker 1's prose at `rev-utils.md:29` reads verbatim "the second-consumer trigger has not fired, so the disposition stays forward-looking with the canonical resolution home now named" and "Defer until that second consumer surfaces." Self-adjudicates against an in-cycle edit; the canonical resolution home is recorded in `## Notes for Worker 3` for the trigger-satisfying cycle.

### Validation run

- `uv run ruff format .` — pass / no changes
- `uv run ruff check --fix .` — pass / no changes

### Notes for Worker 3

Comment pass is structurally a no-op — no source edit landed in the logic pass, so no docstring contract changed. The folder-pass artifact body at `rev-utils.md:33-37` (the `### DRY recap` block) IS the consolidation narrative for the three forward-looking Lows; per pattern (d) re-recapping inside a sibling docstring would invert the folder-pass artifact's role.

---

## Changelog disposition

Batched into this consolidated single-spawn per dispatch authorisation; consolidation rule still satisfied — the comment pass was structurally a no-op (no source edit, no docstring contract change), so the changelog disposition has nothing behavioural to describe.

### State

`Not warranted`.

### Reason

Cites BOTH required citations per `worker-2.md:251-258`:

- `AGENTS.md` line 21: "Do not update CHANGELOG.md unless explicitly instructed."
- The active plan `docs/review/review-0_0_7.md` is silent on changelog authorization for this cycle — the dispatch prompt names changelog as "Not warranted" up front and no `Warranted and edited` authorisation is recorded against cycle 31 in the plan.

Reinforcing third citation (per pattern (f) in `worker-memory/worker-2.md`): zero-line-footprint consolidated single-spawn with the module's self-asserted DRY canonical-home status. This is the strongest variant of `Not warranted` — precedent chain is now 31 deep across the 0.0.7 release window (every prior cycle in this window closed `Not warranted`), zero source edit landed this cycle, and the artifact's DRY analysis self-asserts the canonical-home status of all three siblings at `rev-utils.md:7` ("None — the three siblings ... are each a self-asserted canonical home for their concern").

### What was done

No `CHANGELOG.md` edit. There is no consumer-visible change to record: zero source files touched, zero tests added or modified, zero behaviour change. The three forward-looking Lows are recorded under `## Notes for Worker 3` with verbatim trigger phrases and canonical resolution homes named, so the trigger-satisfying future cycles can route the work without re-derivation.

### Validation run

- `uv run ruff format .` — pass / no changes
- `uv run ruff check --fix .` — pass / no changes

---

## Iteration log

(No re-passes — consolidated single-spawn closed on first dispatch.)

---

## Verification (Worker 3)

### Logic verification outcome

Consolidated single-spawn no-op verified. `git diff -- django_strawberry_framework/utils/` is empty (no source edit landed this cycle); `git status` shows no `utils/` paths modified or untracked. All three Lows are forward-looking with Worker 1's verbatim defer-with-trigger phrasing preserved by Worker 2 in `### Notes for Worker 3`:

- L1 (`utils/__init__.py` re-exports `unwrap_return_type` ahead of any in-package consumer): trigger preserved verbatim — "Defer until the schema-factory consumer lands and `unwrap_return_type` gets its first call site; at that point the same cycle that adds the call site should also tighten the `utils/__init__.py:10-14` docstring from 'upcoming' to 'lives at `<call-site>`' to close the citation chain."
- L2 (Single trigger fans out three deferred actions across `utils/typing.py`): three-action fan-out (a/b/c) preserved verbatim against `rev-utils__typing.md:20-39,131`; trigger remains the schema-factory consumer's first call site landing per `utils/__init__.py:13-14`.
- L3 (`_check_n1` `kind: str | None` widening vs `is_many_side_relation_kind(kind: RelationKind | None)`): trigger preserved verbatim from `rev-utils__relations.md:23-25` — "Forward to `rev-utils.md` folder pass only if the same wide-`str` admission pattern appears on a second consumer." Folder pass confirms second-consumer trigger has NOT fired; canonical resolution home named verbatim ("tighten `_check_n1`'s `kind` parameter to `RelationKind | None` rather than relaxing the `utils/relations.py` callee signature").

### DRY findings disposition

`## DRY analysis` is `None` (self-asserted canonical-home for all three siblings). The `### DRY recap` block at `rev-utils.md:33-37` IS the consolidation narrative — three forward-looking triggers from per-file artifacts (cycles 28-30) carried forward verbatim under a single inventory so the next cycle that fires any trigger can grep them without re-reading three artifacts. Folder pass acts as DRY-consolidator per pattern (d) — no cross-sibling helper-extraction candidate today; the `_peel(rt, *, predicates: tuple[...])` consolidation and `is_single_side_relation_kind` mirror were both considered and rejected with verbatim trigger phrasing.

### Temp test verification

- None — no temp tests required for a zero-source-edit folder pass.

### Verification outcome

`cycle accepted; verified` — logic + comments + changelog disposition all accepted in the consolidated single-spawn. Top-level `Status: verified`; checklist box at `review-0_0_7.md:129` marked. Changelog `Not warranted` cleared three legs: AGENTS.md:21 cited, active plan silence on cycle 31 confirmed, thirty-one-cycle precedent chain dominant.
