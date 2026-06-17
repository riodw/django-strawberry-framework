# Review: `django_strawberry_framework/filters/` (folder pass)

Status: verified

> **Re-opened folder pass.** This artifact previously closed `verified` against an
> empty cycle diff. Commit `79b74b46` ("consolidate active permission targets") then
> rewrote `filters/sets.py` (~+53 lines) and introduced a new folder-level dependency:
> `filters/sets.py` now imports `utils/permissions.py::active_permission_targets`, a new
> single-pass LEAF/RELATED classifier. The prior folder review predated that edge, so this
> item re-opened. The sections below are REWRITTEN against CURRENT source at HEAD
> (the maintainer's change is committed; `git diff HEAD -- django_strawberry_framework/filters/`
> is empty). The new `filters → utils.permissions` edge got the folder-level
> circular-import and DRY attention the dispatch called for. The four sibling artifacts
> (`base`/`factories`/`inputs`/`sets`) are all `verified` against current source —
> `sets.py` was just re-verified after `79b74b46`. Iteration history is preserved by this
> note + the prior `verified` close (now superseded).

Folder pass over `django_strawberry_framework/filters/`: `base.py`, `factories.py`,
`inputs.py`, `sets.py` (all four sibling artifacts `verified`) plus the folder
`__init__.py` (covered here, not separately). Shadow overviews regenerated this cycle via
`python scripts/review_inspect.py --all --output-dir docs/shadow`. Cycle diff
`git diff HEAD -- django_strawberry_framework/filters/` is EMPTY — the maintainer's commit
is in HEAD, so this is a standing-code folder review against the post-refactor source.

## DRY analysis

- None at folder scope. The `79b74b46` refactor IS a DRY consolidation and it lands the
  permission-target plumbing at its maximally-factored, single-sited shape: the new
  `utils/permissions.py::active_permission_targets` is the one single-pass LEAF/RELATED
  classifier that both `active_permission_field_paths` and `active_related_branches`
  (`utils/permissions.py::active_permission_field_paths`, `::active_related_branches`) now wrap, and
  that `run_active_input_permission_checks` consumes once per level. The FilterSet-side
  `_active_permission_targets` (`filters/sets.py::FilterSet._active_permission_targets`) and its
  `_active_permission_field_paths` LEAF slice are thin delegates to that shared core — they
  are NOT intra-`filters/` duplication. The folder's one genuine cross-sibling consolidation
  candidate — the filter/order family wrappers (`FilterSet`/`OrderSet` twins of
  `_iter_input_items`, `_request_from_info`, `_iter_active_related_branches`,
  `_active_permission_field_paths`, the now-added `_active_permission_targets` twin, the alias
  block, and the `_make_hashable`/`_make_cache_key`/`get_*_class` Layer-6 trio) — is a
  CROSS-FOLDER (`filters/` ↔ `orders/`) relationship, not an intra-`filters/` duplication. It
  is already deferred-with-trigger in the sibling artifacts: `rev-filters__factories.md`
  (trigger: "the `orders/factories.py` Layer-6 TODO anchor is resolved",
  `orders/factories.py` #"TODO(spec-028-orders-0_0_8 Decision 12") and the cycle-11/cycle-12
  `sets_mixins`/`base` notes (trigger: "re-confirm all 3 families share the params when
  AggregateSet / fieldsets WIP-ALPHA-028 lands"). Per the dispatch, the filter/order
  cross-folder relationship (including the post-refactor `_active_permission_targets` twin)
  belongs to the project pass — forwarded by citation to
  `docs/review/rev-django_strawberry_framework.md`, not re-opened here. Within `filters/`
  itself every shared mechanism is single-sited (see `### DRY recap`); there is no
  intra-folder helper duplicated across two siblings to hoist.

## High:

None.

## Medium:

None.

## Low:

None. (The four sibling artifacts each carry one no-action Low — `base`'s defensive
double-`getattr` in `RelatedFilter.get_queryset`, `factories`'s `_make_cache_key`
`key=repr` asymmetry, `inputs`'s `_iter_filterset_subclasses` alias + `construct_search`
deferred helper, `sets`'s `_q_for_branch` async stash-miss fallback. All are local
pre-empt-re-flag notes already verified no-action at file scope; none is a folder-level
defect and none recurs as a folder-wide pattern. The `79b74b46` refactor introduced no new
Low at any scope — `sets.py`'s re-verified artifact carries the same single no-action Low it
had before.)

## What looks solid

### DRY recap

- **Existing patterns reused (folder-wide).** Every reusable mechanism in the folder is a
  thin delegate to a single-sited helper OUTSIDE the folder, so no two siblings re-implement
  the same logic: the generated-input substrate (`FieldSpec`/`build_input_class`/
  `_camel_case`/`iter_set_subclasses`/`materialize`/`clear`) is aliased+delegated from
  `..utils.inputs` in `inputs.py:57-60` and the BFS argument factory subclasses
  `..utils.inputs.GeneratedInputArgumentsFactory` in `factories.py`; the apply pipeline's
  traversal/permission/visibility primitives delegate to `..utils.permissions`,
  `..utils.input_values`, `..utils.querysets`, and `..sets_mixins`; the lazy related-target
  binding is parameterized through `..sets_mixins.RelatedSetTargetMixin` in `base.py:393-394`;
  the GlobalID strategy frozensets are read from the canonical
  `..types.relay.MODEL_LABEL_STRATEGIES`/`TYPE_NAME_STRATEGIES` in `base.py:47`; and the
  `__init__.py::filter_input_type` body is shared with `orders/__init__.py::order_input_type`
  via `..utils.inputs.build_lazy_input_annotation` (`__init__.py:75-83`). The `79b74b46`
  refactor STRENGTHENED this property at the permission layer: the new single-pass
  `active_permission_targets` (`utils/permissions.py::active_permission_targets`) makes the
  LEAF/RELATED classification rule single-sited in `..utils.permissions`, with
  `FilterSet._active_permission_targets` / `_active_permission_field_paths`
  (`filters/sets.py::FilterSet._active_permission_targets`, `filters/sets.py:1289`) reduced to
  thin per-family delegates. The 0.0.9 DRY pass (`docs/feedback.md` Major 1 + 3) drove the
  original convergence; the folder pass confirms it is complete and the refactor extended it,
  not residual.
- **New helpers considered (folder-wide).** The `79b74b46` refactor already extracted the
  right shared helper — `active_permission_targets` — at the correct level (`..utils`,
  consumed by both `filters/sets.py` and `orders/sets.py`), so there is no folder-internal
  helper to hoist from it. A folder-internal shared helper for the three `and`/`or`/`not`
  branch-unrolling loops in `sets.py` (`_collect_nested_visibility_querysets_async` /
  `_run_permission_checks` / `_evaluate_logic_tree`) was considered and rejected at file scope
  (each unrolls the same three branches with divergent per-branch operator semantics — async
  derive vs perm recursion vs `Q` `&`/`|`/`~` composition); confirmed correct at folder scope
  too — no second sibling shares that loop shape, so it is a within-`sets.py` concern, not a
  folder hoist. The `normalize_input_value` pair (`filters/inputs.py` vs `orders/inputs.py`)
  remains intentionally NOT a shared traversal: the filter side is a flat isinstance-ladder
  mapping ONE raw value to django-filter form-data by filter class (`inputs.py:412-460`),
  while the order side walks the input DATACLASS via `..utils.input_values.iter_active_fields`.
  Different abstraction levels (value-shape adapter vs structure walker), no shared body. This
  is a `filters/`↔`orders/` cross-folder pair regardless, so the disposition is recorded for
  the project pass; the within-`filters/` finding is that nothing in this folder duplicates it.
- **Duplication risk in the folder (cross-sibling literals).** Ran the folder-pass
  repeated-literal check across the four sibling shadow overviews + `__init__.py` (regenerated
  this cycle). The only literals recurring in 2+ files are the family labels
  `FilterSet`/`filterset` (`inputs.py` 2x, `sets.py` 3x, `factories.py` 2x as `filterset`).
  Every occurrence is one of: (a) a reference to the `FilterSet` class itself (imported from
  `.sets`, the single canonical definition); (b) the family-label string passed to the shared
  `materialize_generated_input_class` / `clear_generated_input_namespace` substrate
  (`inputs.py:824`/`882`); or (c) the `_related_target_attr = "filterset"` BFS slot in
  `factories.py` whose `orderset` twin the shared base parameterizes. None is a string-keyed
  dispatch constant that two siblings re-type independently. The `79b74b46` refactor added NO
  new cross-file string literal — `active_permission_targets` is imported as a symbol, not a
  string, and `_active_permission_targets` is a method name, not a repeated literal in any
  shadow. The per-file literals flagged in the overviews
  (`contains`/`istartswith`/`week_day`/`field_name` in `inputs.py`;
  `related_filters`/`_owner_definition`/`is_relation` in `sets.py`) appear in ONE sibling each
  — intra-file role splits already cleared in the per-file artifacts, not folder-level.

### Other positives

- **The new `filters → utils.permissions` edge is one-way and acyclic — re-confirmed for the
  re-open.** `utils/permissions.py` imports only `__future__`, stdlib
  (`collections.abc`, `functools`, `typing`), `django.http`, `..exceptions`, and
  `.input_values` (`utils/permissions.py:26-35`) — ZERO imports back into `filters/` at load
  time or in-function. The only `filters` tokens in the module are comment/docstring
  references (`utils/permissions.py:59`, `:217`, `:315`), not imports. So the
  `filters/sets.py → ..utils.permissions` edge (`filters/sets.py:46-54`, pulling
  `active_permission_targets` + 6 siblings) is a strict outward/upward dependency:
  `filters/sets.py → utils/permissions.py → {exceptions, utils.input_values}`. `orders/sets.py`
  shares the identical outward edge (`orders/sets.py:42`), so the two families fan IN to the
  shared `utils` core; there is no fan-out from `utils` back to either family. No cycle is
  introduced by the refactor.
- **Folder-internal dependency direction stays one-way and acyclic.** Load-time intra-folder
  edges: `inputs.py → .base` (`inputs.py:44`); `sets.py → {.base, .inputs}`
  (`sets.py:60-61`); `factories.py → {.inputs, .sets}` (`factories.py:36-37`); `__init__.py →
  {.base, .inputs, .sets}` (`__init__.py:20,35,36`). `base.py` imports no `filters/` sibling.
  Topological order `base → inputs → sets → factories`, strictly acyclic; no sibling imports
  `factories` or `__init__`. The `base.py → ..types.relay` / `..types.definition` edge is the
  documented safe acyclic `filters → types` direction (`base.py:41-47`); `types/relay.py`
  reaches back into `filters`/`registry` only via in-function imports, so no load cycle.
  `inputs.py`'s `..types.converters` imports are local-in-function for the same reason.
  Empirically verified: `import django_strawberry_framework.filters` succeeds (no
  circular-import error), `__all__` length 16, sorted.
- **`__init__.py` export surface is consistent and minimal (unchanged by the refactor).**
  `__all__` (`__init__.py:86-103`) is a sorted 16-name tuple of exactly the consumer-facing
  surface: the `base` primitives, the `FilterSet`/`FilterSetMetaclass` pair, and the
  `filter_input_type` Decision-11 helper. The internal-only re-imports
  `INPUTS_MODULE_PATH`/`_input_type_name_for` (`__init__.py:35`) and
  `_helper_referenced_filtersets` (`__init__.py:44`) are deliberately NOT in `__all__` — they
  exist for the `filter_input_type` body and the finalizer's phase-2.5 orphan check, documented
  inline (`__init__.py:38-43`). The `Filter` re-export is documented as a deliberate plain
  re-export of `django_filters.Filter` (NOT a subclass) that shadows the upstream name
  (`__init__.py:9-14`). `79b74b46` added/renamed only private `_`-prefixed helpers inside
  `sets.py`, none of which surface through `__init__.py` — the export surface is byte-identical
  to the prior pass.
- **The duck-typed permission contract holds across both families.** Both
  `FilterSet._active_permission_targets` (`filters/sets.py:1292`) and
  `OrderSet._active_permission_targets` (`orders/sets.py:350`) define the method, so the
  `cls._active_permission_targets(...)` call in the shared
  `utils/permissions.py::run_active_input_permission_checks` (`utils/permissions.py:325`)
  resolves on either family. The folder-level concern the new edge could have raised — a
  FilterSet-only method that the shared core assumes exists on every family — is satisfied:
  the order twin lands the symmetric method in the same commit.
- **Naming + error-handling are consistent across siblings.** All four siblings raise the
  single `..exceptions.ConfigurationError` for misconfiguration and `TypeError` only for
  consumer-declaration misuse (`filter_input_type` non-`FilterSet` arg). The family-label
  naming (`FilterSet`/`filterset`/`FilterInputType`) is applied uniformly and its asymmetry vs
  the `orders/` twin (`OrderSet`/`orderset`) is exactly what the shared `utils`/`sets_mixins`
  bases parameterize. No naming drift between siblings; the refactor's new private helper names
  (`_active_permission_targets`, `active_permission_targets`) follow the existing
  family-method / utils-function split.
- **Comment consistency.** The cross-family provenance comments are consistent and accurate:
  `__init__.py:69-74` names the shared `order_input_type` twin and the 0.0.9 DRY-pass
  `build_lazy_input_annotation` helper; `base.py:41-46` documents the import-cycle direction;
  `sets.py`'s new delegate docstrings (`_active_permission_targets`,
  `_active_permission_field_paths`) name `utils/permissions.py::active_permission_targets` as
  the shared core, matching the `orders/sets.py` twin docstrings. Each sibling's deferred-surface
  comments name the same future cards consistently.

### Summary

Re-opened folder pass over `filters/` (`base`/`factories`/`inputs`/`sets` + `__init__.py`)
after commit `79b74b46` rewrote `filters/sets.py` and introduced a new
`filters/sets.py → utils/permissions.py::active_permission_targets` dependency. All four
per-file artifacts are `verified` against current source (`sets.py` just re-verified post-refactor)
and the cycle diff against HEAD is empty. The headline re-open question — does the new
`filters → utils.permissions` edge create a cycle — is answered NO: `utils/permissions.py`
imports only stdlib/django/`..exceptions`/`.input_values` with zero back-edge into `filters/`,
so the edge is a strict outward dependency and both filter and order families fan IN to the
shared `utils` core. The refactor is a DRY consolidation that strengthens the folder's
"every shared mechanism delegates to a single-sited helper outside the folder" property at the
permission layer, and it preserves the duck-typed contract by landing the symmetric
`_active_permission_targets` method on the OrderSet twin in the same commit. Folder-internal
dependency direction stays one-way/acyclic (`base → inputs → sets → factories`,
empirically import-clean), the `__init__.py` export surface is unchanged (the minimal sorted
16-name consumer set, internal helpers excluded), error-handling and family-label naming stay
consistent across siblings, and the regenerated folder-pass repeated-literal check found no
new cross-file string-keyed dispatch constant (the refactor imports a symbol, not a literal).
The one genuine consolidation candidate (the filter/order family wrappers, now including the
`_active_permission_targets` twin, plus the re-confirmed `normalize_input_value` pair) is a
`filters/`↔`orders/` CROSS-FOLDER relationship, already deferred-with-trigger in the sibling
artifacts and forwarded to the project pass `docs/review/rev-django_strawberry_framework.md`
per the dispatch — not an intra-folder defect. No High, no Medium, no folder-level Low.
No-findings folder pass with an empty cycle diff (shape #3 → no-source-edit shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
None — no-source-edit cycle.

### Tests added or updated
None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; 270 files left unchanged.
- `uv run ruff check .` — pass; "All checks passed!" (the COM812/formatter-conflict notice is
  pre-existing config noise, not a result of this cycle).

### Notes for Worker 3
- Re-opened folder pass after commit `79b74b46` ("consolidate active permission targets").
  `git diff HEAD -- django_strawberry_framework/filters/` is EMPTY — the maintainer's change is
  committed; this is standing-code folder review against HEAD. Shadow overviews regenerated this
  cycle (`python scripts/review_inspect.py --all --output-dir docs/shadow`).
- **Import-direction verdict on the new `filters → utils.permissions` edge: ONE-WAY, ACYCLIC.**
  `utils/permissions.py` imports only `__future__`, stdlib, `django.http`, `..exceptions`,
  `.input_values` (`utils/permissions.py:26-35`); zero imports back into `filters/` (the three
  `filters` mentions are comment/docstring text). `filters/sets.py:46-54` and `orders/sets.py:42`
  both depend OUTWARD on the shared `..utils.permissions` core. No cycle. Empirically:
  `import django_strawberry_framework.filters` succeeds, `__all__` len 16, sorted.
- No High / no Medium / no folder-level Low. The four siblings' per-file no-action Lows were
  each verified no-action in their own `verified` artifacts; none recurs as a folder pattern; the
  refactor introduced no new Low.
- DRY = None at folder scope. The refactor IS a DRY consolidation (single-sited
  `active_permission_targets`). The filter/order family-wrapper consolidation — now including the
  new `_active_permission_targets` twin and the re-confirmed `normalize_input_value` pair — is a
  CROSS-FOLDER relationship, already deferred-with-trigger in `rev-filters__factories.md`
  (trigger: order-side Layer-6 TODO resolved) and the cycle-11/12 sibling notes (trigger:
  AggregateSet/fieldsets WIP-ALPHA-028 lands). Forwarded by citation to the project pass
  `docs/review/rev-django_strawberry_framework.md`; NOT re-opened here.
- Duck-typed contract: both `FilterSet._active_permission_targets` (`filters/sets.py:1292`) and
  `OrderSet._active_permission_targets` (`orders/sets.py:350`) define the method the shared
  `run_active_input_permission_checks` (`utils/permissions.py:325`) calls — the order twin lands
  in the same commit, so the shared core's assumption holds for both families.
- `__init__.py` export surface unchanged by the refactor (private `_`-prefixed helpers only).
  No GLOSSARY-only fix in scope — `filter_input_type` (GLOSSARY:494) and the
  `FilterSet`/`RelatedFilter`/`Meta.filterset_class` entries were verified accurate in the
  per-file artifacts; the refactor renamed only private helpers, none documented public contract.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment/docstring edits warranted at
folder scope — the `__init__.py` module docstring, the `filter_input_type` docstring, the
ledger lifecycle comment block (`__init__.py:38-43`), and the cross-family provenance comment
(`__init__.py:69-74`) are accurate and consistent with the siblings; `sets.py`'s new delegate
docstrings (`_active_permission_targets` / `_active_permission_field_paths` naming
`utils/permissions.py::active_permission_targets` as the shared core) match the `orders/sets.py`
twin and were already cleared in the re-verified `rev-filters__sets.md`. The per-file artifacts
cleared each sibling's comments.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — no source change this
cycle (empty folder diff against HEAD; the maintainer's `79b74b46` refactor predates this review
and is the maintainer's to changelog if desired). Per AGENTS.md "Do not update CHANGELOG.md
unless explicitly instructed" and the active plan `docs/review/review-0_0_10.md` carrying no
changelog directive for review cycles.

---

## Verification (Worker 3)

Terminal verification of the RE-OPENED `filters/` folder pass (shape #5, no-source-edit;
baseline HEAD `5724429c`). Independently confirmed every load-bearing claim.

### Logic verification outcome
No-findings folder pass (High 0 / Medium 0 / Low 0 at folder scope), so there is no per-finding
disposition to audit. Instead the load-bearing standing-code claims were each independently
re-derived:

- **Import-cycle verdict on the new `filters → utils.permissions` edge: NO CYCLE — confirmed by
  reading the actual import lines.** `utils/permissions.py` import block (lines 26-35) is exactly
  `__future__`, `collections.abc`, `functools.lru_cache`, `typing.Any`, `django.http.HttpRequest`,
  `..exceptions.ConfigurationError`, `.input_values` — ZERO back-edge into `filters/`. The only
  `filters` tokens in the module (lines 59, 217, 315) are comment/docstring text, not imports
  (grep-confirmed). `filters/sets.py:46-47` and `orders/sets.py:41-42` both depend OUTWARD on
  `..utils.permissions`, so both families fan IN to the shared core; no fan-out back. The edge is
  strictly `filters/sets.py → utils/permissions.py → {exceptions, utils.input_values}`.
- **Empirically import-clean.** `import django_strawberry_framework.filters` (under Django setup)
  succeeds with no circular-import error; `__all__` length 16 and `list(__all__) == sorted(...)`
  both true — the artifact's surface claim is byte-exact (`ArrayFilter … validate_range`).
- **Duck-typed `_active_permission_targets` contract holds on both families.** The shared call
  site `cls._active_permission_targets(input_value)` (`utils/permissions.py:325`, inside
  `run_active_input_permission_checks`) resolves on whichever family `cls` is; both
  `filters/sets.py:1292` and `orders/sets.py:350` define the method (grep-confirmed). The order
  twin lands in the same commit, so the shared core's assumption is satisfied for both.
- **Cross-folder DRY forward is genuinely cross-folder.** `grep -rln "def _active_permission_targets"`
  returns exactly two paths in two distinct folders (`filters/sets.py`, `orders/sets.py`) — the
  family-wrapper consolidation (now including this twin) is a `filters/`↔`orders/` relationship,
  correctly forwarded to the project pass `rev-django_strawberry_framework.md`, not an intra-folder
  defect. The forward-target artifact does not yet exist (project pass unopened); that is the
  expected forward-by-citation + open-box pattern, not a gap.

### DRY findings disposition
None at folder scope, accepted. The `79b74b46` refactor IS a DRY consolidation that strengthens
the folder's "every shared mechanism delegates to a single-sited helper outside the folder"
property at the permission layer; the one genuine consolidation candidate is cross-folder and
forwarded. Verified the cross-folder claim directly (two-folder grep above).

### Temp test verification
None needed — no behavior change to prove (empty cycle diff; the fused-walk behavior was already
proven equivalent in the just-closed `rev-filters__sets.md` re-verify). No temp tests created.

### Shape #5 checks
1. `git diff HEAD -- django_strawberry_framework/filters/` is EMPTY (confirmed). Working-tree
   dirty paths (`management/`, KANBAN, specs, db.sqlite3) touch no `filters/` file — they are
   closed sibling cycles (`rev-management__commands.md`) / concurrent maintainer work, not a
   rejection trigger.
2. All three Worker 2 sections start with `Filled by Worker 1 per no-source-edit cycle pattern.`
   (lines 220, 267, 280).
3. No Low at folder scope to phrase; the four per-file no-action Lows are forwarded by citation
   to their own `verified` artifacts. No GLOSSARY-only fix present (refactor renamed private
   helpers only; GLOSSARY entries verified accurate in per-file artifacts) — not disqualifying.
4. Changelog `Not warranted` cites BOTH AGENTS.md ("Do not update CHANGELOG.md unless explicitly
   instructed") AND the active plan's silence (`review-0_0_10.md`, no changelog directive);
   `git diff -- CHANGELOG.md` empty. "Not warranted" framing honest — no public surface changed
   (`__all__` byte-identical, private-helper renames only).
5. `uv run ruff format --check django_strawberry_framework/filters/` → 5 files already formatted
   (COM812 notice is pre-existing config noise); `uv run ruff check django_strawberry_framework/filters/`
   → "All checks passed!".

### Verification outcome
cycle accepted; verified — sets top-level `Status: verified` AND marks the re-opened `filters/`
folder-pass checklist box. Import-cycle verdict: the new `filters → utils.permissions` edge is
one-way and acyclic; no cycle introduced.
