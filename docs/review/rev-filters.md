# Review: `django_strawberry_framework/filters/` (folder pass)

Status: verified

Folder pass over `django_strawberry_framework/filters/`: `base.py`, `factories.py`,
`inputs.py`, `sets.py` (all four sibling artifacts `verified`) plus the folder
`__init__.py` (covered here, not separately). Cycle diff
`git diff 43f7589ad36fa49d930ed2c4de13743b3f6c2fce -- django_strawberry_framework/filters/`
is EMPTY — standing-code folder review, no source touched this cycle.

## DRY analysis

- None at folder scope. The folder's one cross-sibling consolidation candidate — the
  filter/order family wrappers (`FilterSet`/`OrderSet` twins of `_iter_input_items`,
  `_request_from_info`, `_iter_active_related_branches`, `_active_permission_field_paths`,
  the alias block, and the `_make_hashable`/`_make_cache_key`/`get_*_class` Layer-6 trio) —
  is a CROSS-FOLDER (`filters/` vs `orders/`) relationship, not an intra-`filters/`
  duplication, and is already deferred-with-trigger in the sibling artifacts:
  `rev-filters__factories.md` (trigger: "the `orders/factories.py` Layer-6 TODO anchor is
  resolved", `orders/factories.py` #"TODO(spec-028-orders-0_0_8 Decision 12") and the
  cycle-11/cycle-12 `sets_mixins`/`base` notes (trigger: "re-confirm all 3 families share
  the params when AggregateSet / fieldsets WIP-ALPHA-028 lands"). Per the dispatch, the
  filter/order cross-folder relationship belongs to the project pass — forwarded by citation
  to `docs/review/rev-django_strawberry_framework.md`, not re-opened here. Within `filters/`
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
defect and none recurs as a folder-wide pattern.)

## What looks solid

### DRY recap

- **Existing patterns reused (folder-wide).** Every reusable mechanism in the folder is a
  thin delegate to a single-sited helper OUTSIDE the folder, so no two siblings re-implement
  the same logic: the generated-input substrate (`FieldSpec`/`build_input_class`/
  `_camel_case`/`iter_set_subclasses`/`materialize`/`clear`) is aliased+delegated from
  `..utils.inputs` in `inputs.py:57-60` and the BFS argument factory subclasses
  `..utils.inputs.GeneratedInputArgumentsFactory` in `factories.py`; the apply pipeline's
  traversal/permission/visibility primitives delegate to `..utils.permissions`,
  `..utils.input_values`, `..utils.querysets`, and `..sets_mixins` in `sets.py:651-1288`;
  the lazy related-target binding is parameterized through `..sets_mixins.RelatedSetTargetMixin`
  in `base.py:393-394`; the GlobalID strategy frozensets are read from the canonical
  `..types.relay.MODEL_LABEL_STRATEGIES`/`TYPE_NAME_STRATEGIES` in `base.py:47`; and the
  `__init__.py::filter_input_type` body is shared with `orders/__init__.py::order_input_type`
  via `..utils.inputs.build_lazy_input_annotation` (`__init__.py:75-83`). The 0.0.9 DRY pass
  (`docs/feedback.md` Major 1 + 3) already drove this convergence; the folder pass confirms
  it is complete, not residual.
- **New helpers considered (folder-wide).** A folder-internal shared helper for the three
  `and`/`or`/`not` branch-unrolling loops in `sets.py`
  (`_collect_nested_visibility_querysets_async` / `_run_permission_checks` /
  `_evaluate_logic_tree`) was considered and rejected at file scope (each unrolls the same
  three branches with divergent per-branch operator semantics — async derive vs perm
  recursion vs `Q` `&`/`|`/`~` composition); confirmed correct at folder scope too — there is
  no second sibling that shares that loop shape, so it is a within-`sets.py` concern, not a
  folder hoist. The `normalize_input_value` pair (`filters/inputs.py` vs `orders/inputs.py`)
  was re-examined at folder scope per the dispatch and CONFIRMED intentionally NOT a shared
  traversal: the filter side is a flat isinstance-ladder mapping ONE raw value to
  django-filter form-data by filter class (`inputs.py:412-460`), while the order side walks
  the input DATACLASS via `..utils.input_values.iter_active_fields`. Different abstraction
  levels (value-shape adapter vs structure walker), no shared body — folding them would
  invent a false abstraction. This is a `filters/`↔`orders/` cross-folder pair regardless, so
  the disposition is recorded for the project pass; the within-`filters/` finding is simply
  that nothing in this folder duplicates it.
- **Duplication risk in the folder (cross-sibling literals).** Ran the folder-pass
  repeated-literal check across the four sibling shadow overviews. The only literal recurring
  in 2+ files is the family label `FilterSet`/`filterset` (`inputs.py` 2x, `sets.py` 3x,
  `factories.py` 2x as `filterset`). Every occurrence is one of: (a) a reference to the
  `FilterSet` class itself (imported from `.sets`, the single canonical definition); (b) the
  family-label string passed to the shared `materialize_generated_input_class` /
  `clear_generated_input_namespace` substrate (`inputs.py:824`/`882`); or (c) the
  `_related_target_attr = "filterset"` BFS slot in `factories.py` whose `orderset` twin the
  shared base parameterizes. None is a string-keyed dispatch constant that two siblings
  re-type independently, so there is no cross-file const to hoist. The per-file literals
  flagged in the overviews (`contains`/`istartswith`/`week_day`/`field_name` in `inputs.py`;
  `related_filters`/`_owner_definition`/`is_relation` in `sets.py`) appear in ONE sibling
  each — intra-file role splits already cleared in the per-file artifacts, not folder-level.

### Other positives

- **Dependency direction is one-way and acyclic.** Folder-pass import comparison across the
  four siblings + `__init__.py`: all imports point OUTWARD/upward
  (`..utils`, `..types`, `..exceptions`, `..registry`, `..sets_mixins`, `..conf`) or sideways
  in a single direction — `factories.py` → `.sets`, `inputs.py` → `.sets`. `base.py` imports
  no `filters/` sibling; `sets.py` imports no `filters/` sibling. `__init__.py` aggregates all
  four (`.base`, `.inputs`, `.sets`) plus `..utils.inputs`. No sibling imports `factories` or
  `__init__`, so there is no intra-folder cycle. The `base.py` → `..types.relay` /
  `..types.definition` edge is the documented safe acyclic `filters → types` direction
  (`base.py:41-46`); `types/relay.py` reaches back into `filters`/`registry` only via
  in-function imports, so no load cycle. `inputs.py`'s `..types.converters` imports are
  local-in-function for the same reason (`inputs.py:267`/`292`).
- **`__init__.py` export surface is consistent and minimal.** `__all__` (`__init__.py:86-103`)
  is a sorted tuple of exactly the consumer-facing surface: the `base` primitives, the
  `FilterSet`/`FilterSetMetaclass` pair, and the `filter_input_type` Decision-11 helper. The
  internal-only re-imports `INPUTS_MODULE_PATH`/`_input_type_name_for` (`__init__.py:35`) and
  `_helper_referenced_filtersets` (`__init__.py:44`) are deliberately NOT in `__all__` —
  they exist for the `filter_input_type` body and the finalizer's phase-2.5 orphan check, and
  the module docstring + inline comments (`__init__.py:38-43`) document the ledger's
  `registry.clear()` lifecycle and the finalizer wiring. The `Filter` re-export is documented
  as a deliberate plain re-export of `django_filters.Filter` (NOT a subclass) that shadows the
  upstream name (`__init__.py:9-14`) — an intentional namespace surface, not drift.
- **Naming + error-handling are consistent across siblings.** All four siblings raise the
  single `..exceptions.ConfigurationError` for misconfiguration (factories' `model is None`
  guard, sets' mixed-model `combine` guard, the `__init__` orphan check) and `TypeError` only
  for consumer-declaration misuse (`filter_input_type` non-`FilterSet` arg). The family-label
  naming (`FilterSet`/`filterset`/`FilterInputType`) is applied uniformly and its asymmetry
  vs the `orders/` twin (`OrderSet`/`orderset`) is exactly what the shared `utils`/`sets_mixins`
  bases parameterize. No naming drift between siblings.
- **Comment consistency.** The cross-family provenance comments are consistent and accurate:
  `__init__.py:69-74` names the shared `order_input_type` twin and the 0.0.9 DRY-pass
  `build_lazy_input_annotation` helper; `base.py:41-46` documents the import-cycle direction;
  `inputs.py` documents the deferred-card `construct_search` and the alias-block addressability
  contract. Each sibling's deferred-surface comments name the same future cards
  (`Meta.search_fields` → 0.1.2, Layer-6 auto-gen → spec-027 Non-goal) consistently.

### Summary

Folder pass over `filters/` (`base`/`factories`/`inputs`/`sets` + `__init__.py`); all four
per-file artifacts are `verified` and the cycle diff against the baseline is empty. The folder
is structurally clean at folder scope: dependency direction is strictly one-way and acyclic
(siblings depend on `.sets` and outward on `..utils`/`..types`/`..sets_mixins`, never on each
other circularly), the `__init__.py` export surface is the minimal sorted consumer set with
internal helpers correctly excluded, error-handling (`ConfigurationError` vs `TypeError`) and
family-label naming are consistent across siblings, and the cross-family provenance comments
agree. The folder-pass repeated-literal check found no cross-file string-keyed dispatch
constant to hoist — the only 2+-file literal (`FilterSet`/`filterset`) is in every case a class
reference, a family-label arg to the already-single-sited `utils.inputs` substrate, or a
parameterized slot, not duplicated logic. The one genuine consolidation candidate (the
filter/order family wrappers, including the `normalize_input_value` pair re-confirmed as
intentionally NOT a shared traversal) is a `filters/`↔`orders/` CROSS-FOLDER relationship,
already deferred-with-trigger in the sibling artifacts and forwarded to the project pass
`docs/review/rev-django_strawberry_framework.md` per the dispatch — not an intra-folder defect.
No High, no Medium, no folder-level Low. No-findings folder pass with an empty cycle diff
(shape #3 → no-source-edit shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
None — no-source-edit cycle.

### Tests added or updated
None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; 267 files left unchanged.
- `uv run ruff check --fix .` — pass; All checks passed (COM812/formatter-conflict warning is
  pre-existing config noise, not a result of this cycle).

### Notes for Worker 3
- Folder pass; cycle diff `git diff 43f7589ad36fa49d930ed2c4de13743b3f6c2fce --
  django_strawberry_framework/filters/` is EMPTY (and `--stat` empty over the same path).
  Standing-code folder review, no source touched.
- No High / no Medium / no folder-level Low. The four siblings' per-file no-action Lows were
  each verified no-action in their own `verified` artifacts; none recurs as a folder pattern.
- DRY = None at folder scope. The filter/order family-wrapper consolidation (incl. the
  `normalize_input_value` pair, re-confirmed intentionally NOT a shared traversal per the
  dispatch) is a CROSS-FOLDER relationship, already deferred-with-trigger in
  `rev-filters__factories.md` (trigger: order-side Layer-6 TODO resolved) and the
  cycle-11/12 sibling notes (trigger: AggregateSet/fieldsets WIP-ALPHA-028 lands). Forwarded by
  citation to the project pass `docs/review/rev-django_strawberry_framework.md`; NOT re-opened
  here.
- Import-direction confirmed one-way/acyclic; `__init__.py` export surface consistent (no
  GLOSSARY-only fix in scope — `filter_input_type` GLOSSARY:494 and `FilterSet`/`RelatedFilter`/
  `Meta.filterset_class` entries were verified accurate in the per-file artifacts, no drift).

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment/docstring edits warranted at
folder scope — the `__init__.py` module docstring, the `filter_input_type` docstring, the
ledger lifecycle comment block (`__init__.py:38-43`), and the cross-family provenance comment
(`__init__.py:69-74`) are accurate and consistent with the siblings; the per-file artifacts
already cleared each sibling's comments.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — no source change this
cycle (empty folder diff against the baseline). Per AGENTS.md "Do not update CHANGELOG.md unless
explicitly instructed" and the active plan `docs/review/review-0_0_10.md` carrying no changelog
directive for review cycles.

---

## Verification (Worker 3)

### Logic verification outcome
No-findings folder pass (shape #3 -> no-source-edit shape #5): High / Medium / Low all 0 at
folder scope. Nothing to address; the four siblings' per-file no-action Lows are each closed in
their own `verified` artifacts and none recurs as a folder-wide pattern (re-read the Low section
and confirmed each is one-sibling-local, not a folder defect).

Independently re-derived the three folder-level structural claims rather than trusting the prose:

- **Import direction one-way / acyclic — CONFIRMED, with a wording note.** Parsed all five files
  and separated load-time imports from TYPE_CHECKING / in-function ones. Load-time intra-folder
  edges are: `inputs -> base`; `sets -> {base, inputs}`; `factories -> {inputs, sets}`; `base`
  imports no filters sibling. Topological order `base -> inputs -> sets -> factories`, strictly
  acyclic. The `inputs -> sets` reference at `inputs.py:64` is TYPE_CHECKING-only (under
  `if TYPE_CHECKING:`) and the `inputs.py:629` `.base` import is in-function — neither executes at
  module load, so no load cycle. Verified empirically: `import django_strawberry_framework.filters`
  succeeds (no circular-import error), `__all__` length 16. NOTE: the artifact's prose "`sets.py`
  imports no `filters/` sibling" is imprecise — `sets.py` does import `.base` and `.inputs` at
  lines 60-61, and `factories.py` imports `.inputs` (line 36) in addition to `.sets`. This
  understates the edge set but does NOT contradict the load-bearing conclusion (one-way, acyclic,
  no intra-folder cycle), which is correct. Not a rejection trigger; recorded for accuracy.
- **`__init__.py` `__all__` is the minimal sorted consumer surface — CONFIRMED.** Programmatically
  verified `__all__` (16 names) is sorted. The three internal-only re-imports
  (`INPUTS_MODULE_PATH`, `_input_type_name_for` at `__init__.py:35`; `_helper_referenced_filtersets`
  at `__init__.py:44`) are all confirmed ABSENT from `__all__` — correctly excluded as
  body-internal / finalizer-wiring helpers, not consumer surface.
- **Cross-folder DRY forward is genuinely cross-folder — CONFIRMED.** `def normalize_input_value`
  exists once in `filters/inputs.py:412` and once in `orders/inputs.py:260` (two folders), not
  twice within `filters/`. The Layer-6 family-wrapper consolidation candidate likewise spans
  `filters/factories.py` <-> `orders/factories.py`. The defer-with-trigger is recorded verbatim in
  the sibling artifact `rev-filters__factories.md` and keyed to the anchor at
  `orders/factories.py:85` (`# TODO(spec-028-orders-0_0_8 Decision 12; standing deferred non-goal):`),
  confirmed present. Both Layer-6 surfaces are presently unconsumed, so hoisting now would build
  shared machinery for two non-shipped surfaces — deferral is sound. The project-pass artifact
  `rev-django_strawberry_framework.md` does not yet exist; that is the expected later cycle item,
  and the forward is by citation to where it will live with the binding trigger held in the
  closed sibling artifact. Not a defect.

Independently confirmed there is NO missed in-folder consolidation: extracted every `def`/`async
def` name across the four siblings; zero names appear in 2+ files — no duplicated helper body to
hoist. The folder-wide DRY recap (every shared mechanism delegates to a single-sited helper
OUTSIDE the folder via `..utils`/`..sets_mixins`/`..types`) holds; the only 2+-file literal
(`FilterSet`/`filterset`) is in every case a class reference, a family-label arg to the
already-single-sited `utils.inputs` substrate, or the parameterized `_related_target_attr` slot —
not a string-keyed dispatch constant.

### DRY findings disposition
None at folder scope (correct). The single genuine consolidation candidate (filter/order family
wrappers incl. the `normalize_input_value` pair) is a `filters/` <-> `orders/` cross-folder
relationship, deferred-with-trigger in the sibling artifacts and forwarded by citation to the
project pass. No intra-folder duplication to act on.

### Temp test verification
- None. No-source-edit cycle, no behavior to pin; the folder-level claims are verifiable by AST
  parse + import smoke + grep, all run above.
- Disposition: n/a.

### Shape #5 checks
1. Cycle diff `git diff <baseline> -- django_strawberry_framework/filters/` empty; `--stat` over
   `django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` empty; broad
   `git diff --stat <baseline>` fully empty (no dirty tree this cycle).
2. Each Worker 2 section opens with `Filled by Worker 1 per no-source-edit cycle pattern.` (Fix
   report / Comment-docstring pass / Changelog disposition). Confirmed.
3. No GLOSSARY-only fix in scope (all Lows no-action or forwarded; none is a GLOSSARY-only edit).
4. Changelog `Not warranted` cites BOTH AGENTS.md and the active plan's silence; `git diff --
   CHANGELOG.md` empty. Confirmed.
5. `uv run ruff format --check django_strawberry_framework/filters/` -> 5 files already formatted;
   `uv run ruff check django_strawberry_framework/filters/` -> All checks passed. (COM812
   formatter-conflict warning is pre-existing config noise.)

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `filters/` folder-pass
checklist box at `docs/review/review-0_0_10.md:85`. The folder is structurally clean at folder
scope: import direction one-way/acyclic (load-time edges only, empirically import-clean),
`__init__.py` `__all__` the minimal sorted consumer surface with internal helpers excluded, no
intra-folder duplicated helper body, and the one genuine consolidation candidate correctly
forwarded as cross-folder. Zero edits, shape #5 preamble/ruff/changelog all met.
