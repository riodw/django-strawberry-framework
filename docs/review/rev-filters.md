# Review: `django_strawberry_framework/filters/`

Status: verified

Folder pass over `django_strawberry_framework/filters/` for release 0.0.9.
Supersedes the stale 0.0.7 `rev-filters.md` folder artifact (the active plan
box is unchecked). Covers the four in-scope source files (`base.py`,
`factories.py`, `inputs.py`, `sets.py`) plus the subpackage `__init__.py`,
synthesizing the four completed-and-verified sibling file artifacts and the
five shadow overviews. Cross-folder concerns are forwarded to the project
pass (`rev-django_strawberry_framework.md`), not treated as local defects.

This pass needs a real edit (a `docs/GLOSSARY.md` correction owned by the
folder pass), so it does NOT collapse to a no-source-edit shape — routed
standard `under-review` for Worker 2.

## DRY analysis

- **Cross-family Layer-6 dynamic-cache lift into `utils/inputs.py` (defer).**
  `filters/factories.py`'s Layer-6 half (`_make_hashable` / `_make_cache_key`
  / `_create_dynamic_filterset_class` / `get_filterset_class` /
  `_RESERVED_FACTORY_KEYS`) is the filter-side twin of the not-yet-shipped
  order-side dynamic cache; `orders/factories.py #"_dynamic_filterset_cache"`
  only comments the analogy and ships the BFS layer alone. The neutral BFS
  substrate is already single-sited in
  `utils/inputs.py::GeneratedInputArgumentsFactory`; the dynamic-cache half is
  NOT yet shared. Defer until the order side ships its own dynamic cache + a
  working `get_orderset_class`; then lift `_make_hashable` + `_make_cache_key`
  + the reserved-key strip + the cache get/build/store skeleton into
  `utils/inputs.py` (`make_generated_set_cache_key(safe_meta)` +
  `get_or_build_dynamic_set(cache, reserved_keys, factory, safe_meta)`),
  leaving only the family-specific `_create_dynamic_*_class` and the
  per-family module-global cache dict at each call site. Trigger: the
  order-side dynamic-cache half lands. (Carried from
  `rev-filters__factories.md` DRY bullet 2 — a genuine cross-family folder/
  cross-folder DRY candidate; re-triage at the project pass once orders ships.)

- **Unordered-container canonical-sort helper `_sorted_pairs(key=repr)`
  (defer).** Two sort strategies coexist in `filters/factories.py`:
  `_make_cache_key`'s top-level dict/extra-meta branches use bare
  `sorted(...)` (natural tuple order; safe because top-level keys are always
  `str`), while `_make_hashable`'s dict/set branches sort `key=repr` (defends
  the nested mixed-type case). Defer until a third canonical-unordered-
  container site needs the same ordering; then extract a single
  `_sorted_pairs(items)` that always sorts `key=repr` and route all three
  through it so the mixed-key defense is uniform. Not act-now: forcing
  `key=repr` into the top-level branches today buys nothing (keys are
  strings) and the helper for a 2-line body is net-negative. (From
  `rev-filters__factories.md` DRY bullet 1; file-local, recorded here for the
  folder DRY ledger.)

- **Converter-vs-normalizer `isinstance`-ladder twin in `filters/inputs.py`
  (defer).** `convert_filter_to_input_annotation` and `normalize_input_value`
  dispatch on the same six filter-class predicates but with different branch
  order and output domain (a type vs a form-data value) — intentional
  siblings, the same family rule this package applies to every sync/async and
  convert/normalize twin. Defer until a third consumer needs the same
  filter-class -> kind classification; then extract a single
  `classify_filter(filter_instance) -> FilterKind` enum and switch both
  ladders on it. (From `rev-filters__inputs.md` DRY bullet 1.)

- **Three logical-branch (`and`/`or`/`not`) walkers in `filters/sets.py`
  (defer).** The iteration skeleton repeats three times
  (`_run_permission_checks`, `_evaluate_logic_tree`,
  `_collect_nested_visibility_querysets_async`) with a different per-branch
  action each (recurse perm-check / `&=`/`|=`/`~&` a `Q` / await a visibility
  derive). A shared `_for_each_logic_branch(tree, on_and, on_or, on_not)`
  driver could host the shape. Defer until a fourth logical-branch consumer
  lands OR the branch set changes (a `xor`/`nand` arm); the sync-vs-async and
  `Q`-algebra-vs-side-effecting divergence makes a callback-threaded
  extraction net-negative today. The `_LOGIC_KEYS` source-of-truth and the
  wire strings are already single-sited in `inputs.py`; only the iteration
  skeleton repeats. (From `rev-filters__sets.md` DRY bullet 2.)

- **Sync/async visibility-derive twin in `filters/sets.py` (defer, no
  trigger).** `_derive_related_visibility_querysets_sync` / `_async` share
  `_iter_visibility_steps`; only the `apply_type_visibility_*` call and the
  child `apply_sync`/`apply_async` await differ. Do NOT extract — the
  await-unwrap makes a single-body collapse net-negative, the same calibration
  this package applies to the `relay.py` / `list_field.py` sync/async twins.
  Recorded so a future DRY cycle does not re-flag it. (From
  `rev-filters__sets.md` DRY bullet 3.)

## High:

None.

## Medium:

### GLOSSARY `RelatedFilter` (994) AND `RelatedOrder` (1004) both over-claim a `ConfigurationError` "naming both attempts" for unqualified-name resolution failure

Both sibling GLOSSARY entries describe the unqualified-name lazy-resolution
failure mode identically and incorrectly. The `## RelatedFilter` entry
(`docs/GLOSSARY.md:994`) says the unqualified form will "fail loud with a
`ConfigurationError` naming both attempts if neither resolves"; the
`## RelatedOrder` entry (`docs/GLOSSARY.md:1004`) says the same with the
`ConfigurationError` link form. Neither is what the code does.

Source facts (confirmed this pass, not trusted from the sibling artifacts):

- `sets_mixins.py::LazyRelatedClassMixin.resolve_lazy_class`
  (`sets_mixins.py #"return import_string(path)"`) — on the first attempt's
  `ImportError` it retries `import_string(f"{bound_class.__module__}.{class_ref}")`
  and lets that **raw `ImportError` propagate unchanged** (no rewrap); when
  `bound_class` is falsy it re-`raise`s the ORIGINAL first-attempt
  `ImportError`. Either way the surfaced error names only **one** path (the
  module-prefixed second attempt, or the bare first attempt) — never "both
  attempts." The method's own docstring
  (`sets_mixins.py #"the original ``ImportError`` propagates unchanged"`)
  states this explicitly.
- The `ConfigurationError` rewrap lives a layer up, in the shared finalize-time
  helper `types/finalizer.py::_bind_sidecar_sets`
  (`finalizer.py #"references an unresolved"`) — invoked by both
  `_bind_filtersets` and `_bind_ordersets` (the 0.0.9 DRY pass, so it is the
  single shared rewrap site, NOT a per-family `_finalize_set_family` /
  `_bind_ordersets` body). Its `except ImportError as exc:` raises
  `ConfigurationError(f"Cannot finalize Django types: {spec.expand_label_noun}
  {set_cls.__qualname__} references an unresolved {spec.related_noun} target.
  {exc}")`. The interpolated `{exc}` is the raw `ImportError` message — i.e.
  the resolved (module-prefixed) path only. It names the offending **set**, not
  both attempted import paths.

So both entries are wrong on two counts: (1) the resolver does not rewrap into
`ConfigurationError` at all (the rewrap is finalize-time, a layer up); and (2)
no surfaced message names "both attempts" — the propagated/rewrapped message
carries only the single resolved-path `ImportError`.

Severity rationale: this is a public-contract documented-symbol prose defect on
TWO shipped public declarations (`RelatedFilter` / `RelatedOrder`,
`shipped 0.0.8`). The file-level reviews scored the single-entry version Low
(it mis-states a failure exception type/message of a rarely-hit misconfig
branch, not a success-path contract). Promoted to **Medium** at the folder pass
because the defect is duplicated verbatim across two parallel public-contract
symbol entries and is the one finding this pass exists to consolidate — Worker 2
should fix both in one sweep so the sibling entries stay parallel. It is a
GLOSSARY edit (a real tracked-file edit), so this pass routes `under-review`,
not a no-source-edit shape.

Verbatim replacement text (Worker 2 lifts both directly):

**GLOSSARY `RelatedFilter` entry (994)** — replace the sentence beginning "The
unqualified-name form is resolved lazily via Layer 2's module-fallback
resolution …" through "… if neither resolves." with:

> The unqualified-name form is resolved lazily via Layer 2's module-fallback resolution — try as an absolute import path first, fall back to prepending the binding `FilterSet`'s `__module__`; if that second attempt also fails, the raw `ImportError` from the module-prefixed path propagates unchanged (the resolver does not rewrap it into a [`ConfigurationError`](#configurationerror), and the surfaced error names only that single attempted path, not both). The finalize-time rewrap into a [`ConfigurationError`](#configurationerror) happens a layer up, when `finalize_django_types()` expands the binding `FilterSet` and names the offending set rather than both import attempts.

**GLOSSARY `RelatedOrder` entry (1004)** — replace the clause beginning "the
unqualified-name form is resolved lazily — try as an absolute import path
first, fall back to prepending the binding `OrderSet`'s `__module__`, fail
loud with a [`ConfigurationError`](#configurationerror) naming both attempts if
neither resolves." with:

> the unqualified-name form is resolved lazily — try as an absolute import path first, fall back to prepending the binding `OrderSet`'s `__module__`; if that second attempt also fails, the raw `ImportError` from the module-prefixed path propagates unchanged (the resolver does not rewrap it into a [`ConfigurationError`](#configurationerror), and the surfaced error names only that single attempted path, not both). The finalize-time rewrap into a [`ConfigurationError`](#configurationerror) happens a layer up, when `finalize_django_types()` expands the binding `OrderSet` and names the offending set rather than both import attempts.

The sentence in the `RelatedOrder` entry that correctly attributes the shared
Layer-2 resolution to `sets_mixins.LazyRelatedClassMixin` (rather than
`filters.base`) is accurate and stays; only the trailing "fail loud … naming
both attempts" clause is replaced.

## Low:

### `filters/factories.py` Layer-6 dynamic-cache surface has zero source consumers at 0.0.9 — resolved deferred at the file pass; recorded for the project pass only

The file pass (`rev-filters__factories.md`) raised a Medium-with-verification:
`get_filterset_class` + the `_dynamic_filterset_cache` half are built-and-tested
but consumed by no non-test source path at 0.0.9, while two docstrings claimed
the owning connection-field surface "lands in `0.0.9`." Worker 2 confirmed
**case (1) DEFERRED** (not a wiring gap): `spec-030`'s `DjangoConnectionField`
reads the already-resolved `definition.filterset_class` sidecar directly
(`connection.py #"definition.filterset_class.apply_sync"`), the
auto-FilterSet-from-`Meta.fields` surface is a standing `spec-027` Non-goal, and
no later spec owns the consumer. The docstrings were corrected to the accurate
deferred state and that file artifact is `verified`. There is **no wiring gap to
forward** — the absence of a consumer is the documented intended deferred state.
Recorded here only so the project pass is aware the filter subsystem ships a
build-and-test-only Layer-6 surface; no folder-level action. No new finding.

### `filters/__init__.py` export surface — reviewed, no defect

The subpackage `__init__.py` (the file the folder pass covers) re-exports the
public filter primitives from `base.py`, the `FilterSet` / `FilterSetMetaclass`
pair from `sets.py`, and the Decision-11 `filter_input_type` consumer helper.
`__all__` (a 16-element tuple) matches the imported-and-defined names exactly —
every entry resolves (`ArrayFilter`, `ArrayFilterMethod`, `Filter`, `FilterSet`,
`FilterSetMetaclass`, `GlobalIDFilter`, `GlobalIDMultipleChoiceFilter`,
`LazyRelatedClassMixin`, `ListFilter`, `ListFilterMethod`, `RangeField`,
`RangeFilter`, `RelatedFilter`, `TypedFilter`, `filter_input_type`,
`validate_range`), and no imported-but-private helper (`INPUTS_MODULE_PATH`,
`_input_type_name_for`, `build_lazy_input_annotation`) leaks into `__all__`.
The `filter_input_type` body delegates to the shared
`utils/inputs.py::build_lazy_input_annotation` (the 0.0.9 DRY pass), threading
the family-specific `ledger=_helper_referenced_filtersets`,
`expected_base=FilterSet`, and `module_path=INPUTS_MODULE_PATH` — the twin of
`orders/__init__.py::order_input_type`, an intentional family sibling, not
duplication. The module docstring's `Filter` re-export caveat (it IS
`django_filters.Filter`, a deliberate namespace shadow, not a subclass) is
accurate against the `from .base import ... Filter` re-export chain. No
High/Medium/Low export, circular-import, or comment defect in the `__init__.py`.

## What looks solid

### DRY recap

- **Existing patterns reused (folder-wide).** The 0.0.9 DRY consolidation is
  fully realized across the folder: the neutral generated-input mechanics
  (BFS walk, collision check, idempotent input-object cache, subclass-rejection
  guard, materialization, namespace-clear, camel-case, subclass-iteration) are
  single-sited in `utils/inputs.py::GeneratedInputArgumentsFactory` and
  `utils/inputs.py` module helpers; `filters/factories.py::FilterArgumentsFactory`
  and `filters/inputs.py` re-export them under the spec-027 Decision 9
  domain-named aliases rather than re-spelling. The owner-bind + lazy-target
  resolution machinery is single-sited in
  `sets_mixins.RelatedSetTargetMixin` / `LazyRelatedClassMixin`, consumed by
  `filters/base.py::RelatedFilter` through family-named thin wrappers
  (`bind_filterset` / `.filterset` / `get_queryset`). The metaclass declaration
  collection, expansion cache + reentry guard, and lifecycle-attr names funnel
  through `sets_mixins.collect_related_declarations` / `expanded_once` /
  `SetLifecycleAttrs`. The active-input traversal and per-field/per-branch
  permission core route through `utils/input_values` and `utils/permissions`.
  Strategy frozensets (`MODEL_LABEL_STRATEGIES` / `TYPE_NAME_STRATEGIES`) are
  imported from `types/relay.py`, not re-spelled. `LOOKUP_NAME_MAP` /
  `_LOGIC_KEYS` are single-sourced in `filters/inputs.py` and imported by
  `filters/sets.py`. `INPUTS_MODULE_PATH` is the single pinned module-path
  constant shared by the factory, `_build_logic_fields`, and `__init__.py`'s
  `filter_input_type`.
- **New helpers considered (folder-wide).** Four cross-file consolidations were
  evaluated and deferred-with-trigger or recorded as intentional twins (see
  `## DRY analysis`): the cross-family Layer-6 cache lift, the `_sorted_pairs`
  canonical-sort helper, the converter/normalizer ladder classifier, and the
  three-way logic-branch walker driver. None clears the act-now bar this cycle;
  each twin's divergence (sync/async await, `Q`-algebra vs side effect,
  branch-order, output domain) makes extraction net-negative until its trigger
  fires.
- **Duplication risk across the folder.** The cross-sibling repeated literals
  surfaced by the shadow overviews are all intentional, not constants to hoist:
  `FilterSet` (in `inputs.py` + `sets.py`) is the imported class name used in
  `isinstance`/`issubclass` guards and forward-ref subclass iteration, not a
  string constant; `"filterset"` (2x in `factories.py`) is the
  `_rename_noun` / `_related_target_attr` family-hook pair (distinct knobs
  sharing a token); `"related_filters"` (6x in `sets.py`) names a
  django-filter-managed attribute threaded as the `collection_attr` /
  `related_attr` argument to the shared collectors; `filter_input_type` (2x in
  `__init__.py`) is the symbol name plus the `family_name=` argument. No literal
  appears in two+ files as a genuine shared constant candidate.

### Other positives

- **One-way dependency direction confirmed; no back-edge.** Cross-sibling import
  comparison (shadow overviews) shows the expected DAG: `filters/` depends
  outward on `sets_mixins.py`, `utils/` (`inputs`, `input_values`, `permissions`,
  `querysets`), `types/` (`relay`, `definition`, `converters`), `registry`,
  `conf`, and `exceptions` — and NONE of those import back into `filters/`. The
  folder-pass focus's stated expectation (shared mechanisms in `sets_mixins.py`
  + `utils/` are a one-way dependency) holds with no back-edge. Intra-folder the
  files form an acyclic chain `base <- inputs <- sets <- factories <- __init__`;
  the only module-top first-party import that could close a cycle
  (`filters/base.py -> types/relay.py`) is justified inline because
  `types/relay.py` reaches into `filters`/`registry` only via in-function
  imports, so no load cycle closes (`filters/inputs.py`'s `types/converters`
  imports are likewise in-function at the call sites).
- **Responsibility boundaries are clean.** The input/factory/set split is
  coherent: `inputs.py` owns the converter/normalizer pair + builders + the
  `FieldSpec`/`build_input_class` aliases; `factories.py` owns the BFS
  arguments-factory specialization + the (deferred-consumer) Layer-6 dynamic
  FilterSet cache; `sets.py` owns the `FilterSet`/metaclass declaration, Meta
  validation, and the sync/async apply pipeline; `base.py` owns the filter
  primitives + `RelatedFilter` lazy resolution. No file reaches across that
  boundary to re-implement another's surface.
- **Error-handling vocabulary is consistent.** Every misuse/misconfig raise
  across the folder uses the package's typed `ConfigurationError` (missing
  `model` in `factories.py`; unsupported own-PK GlobalID lookup, mixed-base-model
  `&`, and depth-cap in `sets.py`) or the `SyncMisuseError` /
  `ConfigurationError` subclass family (the `apply` sync dispatcher's
  class-based rethrow). No file invents a parallel exception type or
  substring-matches an error string. The one cross-file inconsistency is the
  GLOSSARY prose (the Medium), not the source.
- **Naming is consistent across the family.** The filter/order family-named
  thin-wrapper pattern (`bind_filterset` / `.filterset`;
  `filter_input_type` / `order_input_type`) is applied uniformly, and the
  per-family parameterization of the shared mixin
  (`_target_attr`/`_owner_attr`) deliberately differs only in the bound
  attribute names — intentional, not drift.
- **Sibling file artifacts all `verified` with no open High/Medium.** `base.py`,
  `inputs.py`, `sets.py`, `factories.py` each closed clean: base/inputs were
  shape #5 no-source-edit; sets landed one trivial semantics-preserving
  operator-bag `.get` collapse (768-case exhaustive equivalence proof);
  factories landed docstring-only deferred-state corrections. No file-level
  finding remains unresolved that the folder pass must escalate.

### Summary

A well-factored subpackage at 0.0.9. The four source files form a clean acyclic
chain over the shared `sets_mixins.py` + `utils/` substrate with a confirmed
one-way dependency direction and no back-edge; the input/factory/set/primitive
responsibility split is coherent; error-handling routes uniformly through the
typed `ConfigurationError` / `SyncMisuseError` family; and the cross-sibling
repeated literals are all intentional family parameterization, not constants to
hoist. The `__init__.py` export surface (`__all__` of 16, the
`filter_input_type` shared-helper delegate, the `Filter` namespace-shadow
caveat) is accurate with no leak. The one finding the folder pass must act on is
the forwarded GLOSSARY defect: the `RelatedFilter` (994) AND `RelatedOrder`
(1004) entries BOTH claim the unqualified-name resolution failure raises a
`ConfigurationError` "naming both attempts," but `sets_mixins.py::resolve_lazy_class`
propagates a raw `ImportError` naming only the module-prefixed second attempt and
the `ConfigurationError` rewrap lives a layer up in
`types/finalizer.py::_bind_sidecar_sets` (naming the offending set, not both
paths). Recorded as Medium (a public-contract symbol prose defect duplicated
across two parallel shipped entries) with verbatim replacement text for both, so
Worker 2 can fix them in one sweep. Five DRY opportunities are all
deferred-with-trigger or intentional twins. No High; no source-logic, ORM, or
circular-import defect.

---

## Fix report (Worker 2)

Consolidated single-spawn (REVIEW shape #4: one real GLOSSARY prose fix, no
source-logic/test change; High 0, source-Medium 0, one doc-Medium, Lows
no-action/recorded-only). The Medium's two-entry verbatim replacement is a
semantics-preserving documentation correction, so logic + comment + changelog
collapse into this single spawn.

### Files touched
- `docs/GLOSSARY.md` — `## RelatedFilter` entry (the unqualified-name resolution
  sentence) and `## RelatedOrder` entry (the trailing "fail loud … naming both
  attempts" clause). Both replaced verbatim with the artifact's Medium-body text.
  Located by content (the `naming both attempts` clause), not bare line number —
  a sibling cycle's `## DjangoConnection` edit (`docs/GLOSSARY.md:289`, not mine)
  also appears in the baseline diff; my two hunks are scoped only to 994/1004.

### Source re-confirmation before lifting (Medium premise verified accurate)
- `sets_mixins.py::LazyRelatedClassMixin.resolve_lazy_class`
  (`sets_mixins.py #"return import_string(class_ref)"`, body lines 129-136):
  first attempt `import_string(class_ref)`; on `ImportError`, **if `bound_class`**
  retries `import_string(f"{bound_class.__module__}.{class_ref}")` and lets that
  **raw `ImportError` propagate unchanged** (no rewrap); else bare `raise`
  re-raises the ORIGINAL first-attempt `ImportError`. Either way the surfaced
  error names ONE path, never "both attempts." Confirmed by the method docstring
  (`sets_mixins.py #"the original \`ImportError\` propagates unchanged"`, line 124).
- `types/finalizer.py::_bind_sidecar_sets`
  (`finalizer.py #"references an unresolved"`, lines 1200-1205): `except
  ImportError as exc:` raises `ConfigurationError(f"Cannot finalize Django types:
  {spec.expand_label_noun} {set_cls.__qualname__} references an unresolved
  {spec.related_noun} target. {exc}") from exc`. `{exc}` is the single raw
  `ImportError` message; the rewrap names the offending **set**, not both import
  paths. Shared by `_bind_filtersets` (line 1347) and `_bind_ordersets`
  (line 1287) via the 0.0.9 DRY `_SidecarBindingSpec` — single shared rewrap site,
  confirming the artifact's "a layer up, not per-family" framing.
- Artifact's verbatim text is accurate on both counts — **no correction needed**.

### Tests added or updated
- None. Pure GLOSSARY prose fix, zero executable lines; `scripts/check_spec_glossary.py`
  (the standing GLOSSARY/spec integrity check) is the relevant guard and the edit
  introduces no new cross-file links to trip it.

### Validation run
- `uv run ruff format .` — pass (265 files left unchanged; standing COM812
  formatter-conflict warning only).
- `uv run ruff check --fix .` — pass (All checks passed).
- No pytest (per AGENTS.md / worker-2.md hard rule).

### Notes for Worker 3
- No shadow file used (prose-only edit; source re-confirmed by direct read of
  `sets_mixins.py:113-139` and `finalizer.py:1185-1212`).
- `git diff 0872a20f -- docs/GLOSSARY.md` shows THREE hunks: lines 994 + 1004 are
  this cycle; the line-289 `## DjangoConnection` hunk is a prior/sibling cycle's
  edit (worker-0 connection.py GLOSSARY fix), NOT mine — out of scope, left as-is
  per AGENTS.md #33 (concurrent in-progress work).
- Link convention: both replacements use only in-page anchors
  (`](#configurationerror)`, already a live heading) and inline-code
  `finalize_django_types()` (no link). No inline cross-file `](path)` link
  introduced; no `<!-- LINK DEFINITIONS -->` block change needed.
- `uv.lock` NOT in `git status` — untouched, no restore needed.

---

## Comment/docstring pass

Folded into the consolidated spawn (shape #4). The edit IS the GLOSSARY-prose
correction; there is no separate source comment/docstring to update — the
source docstrings already describe the correct behavior:
`sets_mixins.py::resolve_lazy_class` docstring (lines 114-127) already states
"the original `ImportError` propagates unchanged," and `finalizer.py`'s
module/`_bind_sidecar_sets` docstrings already attribute the
`ConfigurationError` rewrap to finalize time. The GLOSSARY was the sole stale
surface; only it was edited.

### Per-finding dispositions
- Medium (RelatedFilter 994 + RelatedOrder 1004 over-claim): FIXED — both entries
  replaced with the artifact's verbatim text; sibling entries kept parallel.
- Low (factories.py Layer-6 zero-consumer): no action — resolved-deferred at the
  file pass, recorded for project-pass awareness only; no folder action.
- Low (`__init__.py` export surface): no action — reviewed, no defect.
- All five DRY items: deferred-with-trigger / intentional twins — preserved
  unchanged, no edit.

### Validation run
- `uv run ruff format .` — pass.
- `uv run ruff check --fix .` — pass.

### Notes for Worker 3
Comment pass is a no-op beyond the GLOSSARY edit itself; source docstrings were
already accurate (verified, not assumed).

---

## Changelog disposition

### State
`Not warranted`.

### Reason
AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") AND the
active plan is silent on changelog authorization for this cycle (dispatch
explicitly forbade editing CHANGELOG.md and directed recording disposition in the
artifact). A folder-pass cycle is NEVER the authorising scope per the worker-2
changelog dicta — CHANGELOG drift forwards to the project pass. Additionally the
edit is a semantics-preserving documentation correction with zero behaviour
change (no consumer-visible contract shift), so no release note is warranted on
its own merits either.

### What was done
No `CHANGELOG.md` edit.

### Validation run
- `uv run ruff format .` — pass.
- `uv run ruff check --fix .` — pass.

---

## Verification (Worker 3)

Terminal-verify, consolidated shape #4 (bare `fix-implemented`; one real GLOSSARY-prose
fix, no source/test change). Source reality re-confirmed independently, not trusted from
the artifact or sibling files.

### Logic verification outcome
- **Source reality (independently confirmed).** `sets_mixins.py::LazyRelatedClassMixin.resolve_lazy_class`
  (read 113-139): `import_string(class_ref)` first; on `ImportError`, if `bound_class`
  retries `import_string(f"{bound_class.__module__}.{class_ref}")` and lets that **raw
  `ImportError` propagate unchanged** — NO `ConfigurationError` rewrap; if `bound_class`
  falsy, bare `raise` re-raises the ORIGINAL first-attempt `ImportError`. Either branch
  surfaces exactly ONE path, never "both attempts." Docstring line 124 ("the original
  `ImportError` propagates unchanged") corroborates. The rewrap lives a layer up in
  `types/finalizer.py::_bind_sidecar_sets` (read 1198-1205): the spec-driven
  `except ImportError as exc:` raises `ConfigurationError(f"...{set_cls.__qualname__}
  references an unresolved {spec.related_noun} target. {exc}") from exc` — `{exc}` is the
  single raw `ImportError` message, naming the offending **set** via `set_cls.__qualname__`,
  not both import paths. The `spec`-parameterized body is the single shared site for both
  `_bind_filtersets`/`_bind_ordersets`, confirming the "a layer up, not per-family" framing.
- **Both GLOSSARY entries now accurate.** Baseline diff (`git diff 0872a20f -- docs/GLOSSARY.md`)
  shows the 994 `RelatedFilter` and 1004 `RelatedOrder` hunks each replace the old
  "fail loud with a `ConfigurationError` naming both attempts" clause with prose that
  matches the source: raw `ImportError` propagates unchanged, resolver does not rewrap,
  surfaced error names the single attempted path, finalize-time rewrap a layer up naming
  the offending set. Neither entry claims "naming both attempts" any longer. Verbatim text
  matches the Medium-body replacement exactly.
- High 0 (none); the single doc-Medium FIXED; both Lows (factories.py Layer-6 zero-consumer
  resolved-deferred at the file pass, recorded project-pass-only; `__init__.py` export
  surface reviewed-no-defect) correctly no-action.

### DRY findings disposition
All five DRY bullets are deferred-with-trigger or intentional twins (cross-family Layer-6
cache lift; `_sorted_pairs` canonical-sort; converter/normalizer ladder classifier;
three-way logic-branch walker; sync/async visibility-derive twin). None clears the act-now
bar this cycle; no source edit — confirmed `filters/__init__.py` and all four source files
carry no folder-pass hunk in the baseline diff. The Layer-6 deferred-consumer Low is
correctly NOT actioned (documented intended deferral, no wiring gap to forward).

### Sibling-cycle attribution
Baseline diff stat over owned paths shows dirty source files all attributable to CLOSED
sibling cycles (each `verified` + `[x]` in `docs/review/review-0_0_9.md`):
- `conf.py` -> rev-conf.md (review-0_0_9.md:70, `[x]`)
- `exceptions.py` -> rev-exceptions.md (:72, `[x]`)
- `list_field.py` -> rev-list_field.md (:73, `[x]`)
- `filters/factories.py` -> rev-filters__factories.md (:80, `[x]`)
- `filters/sets.py` -> rev-filters__sets.md (:82, `[x]`)
- `docs/GLOSSARY.md:289` `## DjangoConnection` hunk -> rev-connection.md (:71, `[x]`)
This cycle's only hunks are GLOSSARY 994 + 1004; "Files touched: docs/GLOSSARY.md only" holds.

### Link convention
No inline cross-file `](path)` link introduced; both replacements use only the in-page
`](#configurationerror)` anchor (target heading present) and inline-code
`finalize_django_types()`. No `<!-- LINK DEFINITIONS -->` block change.

### Temp test verification
None used — pure GLOSSARY prose fix, zero executable lines; behavior re-confirmed by direct
source read, not by a probe.

### Changelog disposition
`Not warranted`. `git diff -- CHANGELOG.md` empty (confirmed). Disposition cites BOTH
AGENTS.md #21 AND the active plan's silence on changelog authorization for this cycle;
semantics-preserving doc-only correction, no consumer-visible contract shift, so internal-only
framing is honest. Accepted.

### Validation
- `uv run ruff format --check .` — pass (265 files already formatted; standing COM812 warning only).
- `uv run ruff check .` — pass (All checks passed!).
- No pytest (per AGENTS.md / role rules; no test introduced).

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the filters folder-pass
checklist box.

---

## Iteration log
