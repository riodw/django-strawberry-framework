# Review: `django_strawberry_framework/orders/`

Status: verified

Folder pass over `django_strawberry_framework/orders/` for release 0.0.9.
Supersedes any stale prior `rev-orders.md` (the active plan box at
`docs/review/review-0_0_9.md:104` is unchecked). Covers the four in-scope
source files (`base.py`, `factories.py`, `inputs.py`, `sets.py`) plus the
subpackage `__init__.py`, synthesizing the four completed-and-verified sibling
file artifacts (`rev-orders__base.md`, `rev-orders__factories.md`,
`rev-orders__inputs.md`, `rev-orders__sets.md`) and the five shadow overviews.
Cross-folder concerns are forwarded to the project pass
(`rev-django_strawberry_framework.md`), not treated as local defects.

This pass needs a real edit (a `docs/GLOSSARY.md` correction owned by the
folder pass — the forwarded `OrderSet` / `Meta.orderset_class` 0.0.9-pin rot),
so it does NOT collapse to a no-source-edit shape — routed standard
`under-review` for Worker 2.

The orders subsystem is built as a deliberate per-family mirror of `filters/`:
both families parameterize the shared `sets_mixins.py` + `utils/` substrate
through family-named thin wrappers. This pass confirms that parallelism holds
(no divergent re-implementation, no back-edge), adjudicates the deferred DRY
candidates from the sibling artifacts, and records the forwarded GLOSSARY
defect with verbatim replacement text for both entries.

## DRY analysis

- **Cross-family Layer-6 dynamic-cache lift into `utils/inputs.py` (defer).**
  The filter side ships a built-but-unconsumed Layer-6 dynamic-FilterSet cache
  (`filters/factories.py::get_filterset_class` + `_dynamic_filterset_cache` +
  `_make_cache_key` + `_make_hashable` + `_create_dynamic_filterset_class` +
  `_RESERVED_FACTORY_KEYS`); the order side ships **NO Layer-6 surface at all**
  — only the BFS subclass plus a TODO anchor naming the forward-reserved
  `_dynamic_orderset_cache` / `get_orderset_class` (`orders/factories.py:85-96`).
  There is therefore **no duplication to remove today** — the order side has
  zero Layer-6 code. The neutral BFS substrate is already single-sited in
  `utils/inputs.py::GeneratedInputArgumentsFactory`. Defer until BOTH a dynamic
  `OrderSet` cache is actually built AND it shares the filter side's
  `(model, fields, extra_meta)` keying; only then lift the common dynamic-cache
  machinery (cache dict + `_make_cache_key` + `_make_hashable` + reserved-key
  strip + the get/build/store skeleton) into a neutral `utils/inputs.py` helper
  (`make_generated_set_cache_key(safe_meta)` +
  `get_or_build_dynamic_set(cache, reserved_keys, factory, safe_meta)`),
  leaving only the family-specific `_create_dynamic_*_class` per call site.
  Trigger verbatim: "the order dynamic cache lands" (the same trigger carried
  on the `filters/sets.py` and `rev-filters.md` deferred-DRY bullets — this is
  the single cross-family/cross-folder DRY candidate, re-triage at the project
  pass once orders ships its dynamic half). (From `rev-orders__factories.md`
  DRY bullet 1.)

- **Order-side `convert_*` / `normalize` / `_build_input_fields` /
  namespace-clear family vs its filter twin (defer).**
  `orders/inputs.py::_build_input_fields` / `normalize_input_value` /
  `convert_order_field_to_input_annotation` / `materialize_input_class` /
  `clear_order_input_namespace` are deliberate per-family mirrors of
  `filters/inputs.py`'s same-named functions, but they already delegate every
  neutral mechanic to the shared substrate (`utils/input_values.py::iter_active_fields`
  for the dataclass/dict walk + top-level flatten + `None`-skip + leaf/related
  classification; `utils/inputs.py::materialize_generated_input_class` /
  `clear_generated_input_namespace` / `build_strawberry_input_class` /
  `graphql_camel_name` / `iter_set_subclasses` for the lifecycle). What remains
  per-family is genuinely order-specific (leaf is always `Ordering | None`; no
  operator bag; no `and_`/`or_`/`not_` logic layer; no `HIDE_FLAT_FILTERS`).
  Defer until a THIRD set family lands (the aggregates subsystem — `AggregateSet`
  is GLOSSARY-listed as deferred); at three consumers the residual per-family
  converter/normalizer shells become a shared parameterized walker. Acting now
  re-hides each family's distinct leaf semantics behind a config object for a
  two-member family — net-negative. (From `rev-orders__inputs.md` DRY bullet 1.)

- **`del <unused-args>` future-extension affordance in `orders/inputs.py`
  (defer).** `convert_order_field_to_input_annotation` and `_build_input_fields`
  carry `model_field` / `owner_definition` parameters reserved-but-unused
  (spec-028 Decision 12 DISTINCT-ON / per-type direction enum). This is
  signature shape-symmetry with `filters/inputs.py::convert_filter_to_input_annotation`,
  not duplicated logic — nothing to extract until the reserved arguments are
  consumed. Defer until the Decision-12 distinct-on / per-type-enum extension
  lands and the converter body branches on `model_field`; re-triage whether the
  order and filter converters can then share a typed dispatch. (From
  `rev-orders__inputs.md` DRY bullet 2.)

- **`apply_sync` / `apply_async` shared post-permission tail in `orders/sets.py`
  (defer).** `apply_sync` (`sets.py:565-576`) and `apply_async` (`sets.py:604-618`)
  share a six-line tail verbatim (`_normalize_input` -> empty-guard ->
  `get_flat_orders` -> `_resolve_order_expressions` -> `not expressions` guard
  -> conditional `annotate` + `order_by`); they diverge only in the permission
  step (sync direct `_run_permission_checks` call vs `await sync_to_async(...)`).
  This is the package's canonical sync/async-twin shape (relay / list_field /
  connection / filters) — the awaitable-unwrap makes a 2-site extraction
  net-negative and the divergent permission-check line is load-bearing. Defer
  until a third apply surface lands (e.g. a streaming/bulk variant); collapse
  the tail into a `_finish_order(cls, queryset, input_value)` helper then. Do
  NOT act now. (From `rev-orders__sets.md` DRY bullet 1.)

- **Order/filter `_run_permission_checks` prologue twin (defer).** The
  `OrderSet._run_permission_checks` prologue (`sets.py:427-446`: None-guard,
  `_fired` init, `bare` allocation, single `run_active_input_permission_checks`
  call) is a near-mirror of the filter side minus the `and`/`or`/`not` logical
  recursion and depth cap. The shared core already lives in
  `utils/permissions.py::run_active_input_permission_checks`; the remaining
  per-family prologue divergence (filter has logic recursion + depth cap, order
  has neither) is exactly the load-bearing difference. Defer until a third set
  family (`AggregateSet`) lands its own `_run_permission_checks`; re-triage a
  `_run_permission_checks_prologue` helper then. (From `rev-orders__sets.md`
  DRY bullet 2.)

- **`order_input_type` / `filter_input_type` shared-helper delegate (no action
  — intentional family sibling, recorded).** `orders/__init__.py::order_input_type`
  delegates wholesale to `utils/inputs.py::build_lazy_input_annotation`
  (`orders/__init__.py:76-84`), threading the family-specific
  `ledger=_helper_referenced_ordersets`, `expected_base=OrderSet`,
  `family_name="order_input_type"`, and `module_path=INPUTS_MODULE_PATH` — the
  one-for-one twin of `filters/__init__.py::filter_input_type`. The 0.0.9 DRY
  pass already single-sited the body; the two family-named wrappers are
  addressability-by-design (consumer-facing helper names), not duplication. No
  trigger — this is a stable intentional sibling. (Recorded so a future DRY
  cycle does not re-flag it.)

## High:

None.

## Medium:

### GLOSSARY `OrderSet` (918) AND `Meta.orderset_class` (806) both version-pin the deferred Layer-6 / connection-field surface to `0.0.9`, but at `0.0.9` that surface either did not ship (Layer 6) or already shipped (the connection field)

Two parallel public-contract GLOSSARY entries carry now-false `0.0.9`
version-pin prose about the same deferred dynamic-`OrderSet` / connection-field
surface. This is the forwarded finding from the `orders/factories.py` file pass
(`rev-orders__factories.md`), consolidated here for a one-sweep fix. (The
parallel `RelatedOrder` entry at `:1004` was already corrected in the filters
folder pass — do NOT re-touch it.)

Source facts (confirmed this pass against live source, not trusted from the
sibling artifacts):

- We are AT release `0.0.9` (`pyproject.toml:4` `version = "0.0.9"`,
  `django_strawberry_framework/__init__.py:25` `__version__ = "0.0.9"`).
- The Layer-6 dynamic-`OrderSet` surface never shipped:
  `grep -rn "get_orderset_class\|_dynamic_orderset_cache"` across
  `django_strawberry_framework/`, `tests/`, `examples/` returns matches ONLY
  inside `orders/factories.py`'s own docstring (line 18) and TODO comment
  (lines 90-91) — i.e. prose references, ZERO symbol definitions and ZERO
  callers. The factory file pass already reworded those two prose sites to a
  version-agnostic "standing deferred non-goal" (`rev-orders__factories.md`,
  `verified`); the GLOSSARY is the remaining stale surface.
- The connection-field surface (`spec-030`) that the prose names as the
  would-be consumer DID ship at `0.0.9` (`connection.py::DjangoConnectionField`)
  and it resolves ordering from the **already-resolved** `definition.orderset_class`
  sidecar directly: `connection.py:870-871` (`apply_sync`), `:895-896`
  (`apply_async`), and `:949-950` (`order_input_type(definition.orderset_class)`).
  It never calls a dynamic factory and never builds an `OrderSet` from
  `model` / `fields`. spec-028 Decision 12 deferred Layer 6 to the `0.0.9`
  connection-field card, which chose the **explicit `Meta.orderset_class`
  declaration** path over a dynamic factory — so Layer 6 is a settled
  standing-deferred non-goal, not an in-flight `0.0.9` deliverable.

The two stale clauses:

- **`## OrderSet` (`docs/GLOSSARY.md:918`)** — the last clause of the first
  paragraph reads "… cycle-safe lazy resolution via the five-layer port +
  Layer 6 deferred to `0.0.9`." Layer 6 was deferred to the `0.0.9`
  connection-field card, which resolved it as a non-goal — it did NOT ship at
  `0.0.9`, so "deferred to `0.0.9`" is now-false (the release elapsed and the
  surface was abandoned, not delivered). (The forwarded note cited "~line 919";
  the live clause is on line 918 — line numbers drift between cycles, grep the
  symbol.)
- **`## Meta.orderset_class` (`docs/GLOSSARY.md:806`)** — the "Consumer wiring"
  paragraph reads "… surfaces an `orderBy: [<T>OrderInputType!]` argument on
  plain `@strawberry.field` resolvers that opt in … (and on
  [`DjangoConnectionField`](#djangoconnectionfield) once it ships in `0.0.9`)."
  The connection field DID ship at `0.0.9` (it is the current release), so the
  future-tense "once it ships in `0.0.9`" is now-false version-pin rot — the
  parenthetical should state the connection field now supports the argument.

Why it matters: this is a contract-accuracy defect on two shipped public
declarations (`OrderSet` / `Meta.orderset_class`, both `shipped 0.0.8`), not a
correctness bug. A maintainer reading either entry at `0.0.9` would either
(a) believe Layer 6 / the connection-field order surface is still pending
delivery this release and go looking for missing wiring, or (b) build the
dynamic factory under the belief the spec still mandates it — when the spec's
actual resolution (explicit `orderset_class` per connection field) already
shipped. Same version-pinned-prose rot class as `exceptions.py::OptimizerError`
("raise sites in 0.0.7") and `optimizer/extension.py` (comment "0.1.2").

Severity rationale: the file passes scored the single-clause version this Low
(version-pinned-docstring rot). Promoted to **Medium** at the folder pass
because the defect is duplicated across TWO parallel public-contract symbol
entries and is the consolidation reason this folder pass exists — Worker 2
should fix both in one sweep so the sibling prose stays parallel and the
`OrderSet` / `Meta.orderset_class` / `order_input_type` / `Ordering` cluster
reads consistently. It is a `docs/GLOSSARY.md` edit (a real tracked-file edit),
so this pass routes `under-review`, not a no-source-edit shape. (Same
folder-level escalation calibration as the filters pass, which promoted the
twin `RelatedFilter`/`RelatedOrder` Low to a folder Medium.)

Verbatim replacement text (Worker 2 lifts both directly):

**GLOSSARY `OrderSet` entry (918)** — in the first paragraph, replace the
trailing clause:

> cycle-safe lazy resolution via the five-layer port + Layer 6 deferred to `0.0.9`.

with:

> cycle-safe lazy resolution via the five-layer port. Layer 6 (dynamic `OrderSet` generation against a connection-field meta dict) is a standing deferred non-goal: the connection field ([`DjangoConnectionField`](#djangoconnectionfield)) resolves ordering from the already-resolved [`Meta.orderset_class`](#metaorderset_class) sidecar directly rather than auto-generating an `OrderSet`, so no dynamic order factory is shipped.

**GLOSSARY `Meta.orderset_class` entry (806)** — in the "Consumer wiring"
paragraph, replace the parenthetical:

> (and on [`DjangoConnectionField`](#djangoconnectionfield) once it ships in `0.0.9`).

with:

> (and on [`DjangoConnectionField`](#djangoconnectionfield), which resolves ordering from this already-resolved sidecar directly).

Both replacements use only existing in-page anchors
(`](#djangoconnectionfield)`, `](#metaorderset_class)` — both live headings)
and inline code; no inline cross-file `](path)` link is introduced, so the
`<!-- LINK DEFINITIONS -->` block needs no change.

## Low:

### `orders/factories.py` mirror-target cross-reference points at the equally-unconsumed filters Layer-6 surface — resolved at the file pass, recorded for project-pass awareness only

The `orders/factories.py` TODO (`:92-93`) points the reader at
`filters/factories.py::get_filterset_class` / `_dynamic_filterset_cache` as the
shape to mirror if Layer 6 is ever revived. That filter surface is itself
built-but-unconsumed at `0.0.9` (the `filters/factories.py` file-pass Medium,
resolved-deferred). The cross-reference is correct as a structural pointer, but
a maintainer following it lands on an equally-unconsumed surface. The file pass
(`rev-orders__factories.md`) already recast the deferral as a non-goal and left
the pointer intact and accurate; no folder-level action. Recorded here only so
the project pass is aware both order- and filter-side Layer-6 are deferred
non-goals (filter built-and-tested-but-unconsumed; order not built at all).
Forward-looking: re-check this pointer if the filters Layer-6 cache is ever
removed or wired. No new finding.

### `orders/inputs.py` `_field_specs` cross-file comment — verified at the sets pass, no defect

The `orders/inputs.py` `_field_specs` comment (`:109-113`) claims the table is
"consulted at runtime by `normalize_input_value` (and indirectly by
`OrderSet._active_permission_field_paths`)". The `inputs.py` file pass recorded
this as a forward-looking Low to confirm at the `orders/sets.py` pass. The
`orders/sets.py` pass (`rev-orders__sets.md`) verified the permission core
routes through `utils/permissions.py::run_active_input_permission_checks` with
`active_permission_field_paths` as a single-sited delegate (`sets.py:287-446`),
consistent with the comment's intent. No stale-comment edit warranted; the
cross-file claim is accurate. No new finding.

### `orders/__init__.py` export surface — reviewed, no defect

The subpackage `__init__.py` (the file this folder pass covers) re-exports
`RelatedOrder` from `base.py`, the `OrderSet` / `OrderSetMetaclass` pair from
`sets.py`, the `Ordering` enum from `inputs.py`, and the Decision-11
`order_input_type` consumer helper. `__all__` (a 5-element tuple:
`OrderSet`, `OrderSetMetaclass`, `Ordering`, `RelatedOrder`,
`order_input_type`) matches the imported-and-defined public names exactly, and
no imported-but-private helper (`INPUTS_MODULE_PATH`, `_input_type_name_for`,
`build_lazy_input_annotation`) leaks into `__all__` — the leading `_` flags the
two private re-exports, mirroring `filters/__init__.py`. The `order_input_type`
body delegates to the shared `utils/inputs.py::build_lazy_input_annotation`
(the 0.0.9 DRY pass), threading the family-specific
`ledger=_helper_referenced_ordersets`, `expected_base=OrderSet`,
`family_name="order_input_type"`, `expected_label="an OrderSet"`, and
`module_path=INPUTS_MODULE_PATH` — the one-for-one twin of
`filters/__init__.py::filter_input_type`, an intentional family sibling, not
duplication. `OrderArgumentsFactory` is deliberately NOT re-exported (advanced
consumers import it from `orders.factories` directly, exactly as the filter
side keeps `FilterArgumentsFactory` out of `filters/__init__.py`). The
`_helper_referenced_ordersets` ledger lives co-located with its only writer
(`order_input_type`) and is co-cleared by `registry.clear()`, matching the
filter side's two-block layout. No High/Medium/Low export, circular-import, or
comment defect in the `__init__.py`.

## What looks solid

### DRY recap

- **Existing patterns reused (folder-wide).** The 0.0.9 DRY consolidation is
  fully realized across the orders folder, in lockstep with `filters/`. The
  neutral generated-input mechanics (BFS walk, per-class collision check,
  idempotent input-object cache, subclass-rejection guard, materialization,
  namespace-clear, camel-case, subclass-iteration) are single-sited in
  `utils/inputs.py::GeneratedInputArgumentsFactory` and `utils/inputs.py` module
  helpers; `orders/factories.py::OrderArgumentsFactory` (`factories.py:64-82`)
  supplies only the six family hook attrs + two caches + the operator-bag-omitting
  `_build_input_triples` override, and `orders/inputs.py` re-exports the shared
  helpers under spec-028 Decision 9 domain-named aliases rather than re-spelling.
  The owner-bind + lazy-target resolution machinery is single-sited in
  `sets_mixins.RelatedSetTargetMixin` / `LazyRelatedClassMixin`, consumed by
  `orders/base.py::RelatedOrder` through family-named thin wrappers
  (`bind_orderset` / `.orderset` getter+setter). The metaclass declaration
  collection, expansion cache + reentry guard, and lifecycle-attr names funnel
  through `sets_mixins.collect_related_declarations` / `expanded_once` /
  `SetLifecycleAttrs` (`sets.py:103-118, 171-175, 220-225`). The active-input
  traversal (`utils/input_values.iter_active_fields`) and per-field/per-branch
  permission core (`utils/permissions.run_active_input_permission_checks`,
  `target_attr="orderset"`) are shared with the filter side. Cardinality
  classification is wholly delegated to `utils/relations.relation_kind` /
  `is_many_side_relation_kind`. `INPUTS_MODULE_PATH` is the single pinned
  module-path constant shared by `inputs.py`, `factories.py`, and
  `__init__.py`'s `order_input_type`.
- **New helpers considered (folder-wide).** Six consolidations were evaluated
  and deferred-with-trigger or recorded as intentional twins (see
  `## DRY analysis`): the cross-family Layer-6 cache lift, the order-side
  converter/normalizer family lift, the `del <unused-args>` affordance, the
  sync/async apply tail, the order/filter `_run_permission_checks` prologue, and
  the `order_input_type`/`filter_input_type` delegate. None clears the act-now
  bar this cycle; each twin's divergence (awaitable-unwrap, branch-order, output
  domain, two-member-family residual semantics) makes extraction net-negative
  until its trigger fires. There is NO act-now folder DRY this pass.
- **Duplication risk across the folder.** The cross-sibling repeated literals
  surfaced by the shadow overviews are all intentional family parameterization,
  not constants to hoist: `orderset` (2x in `factories.py`) is the
  `_rename_noun` / `_related_target_attr` family-hook pair (distinct knobs
  sharing a token); `OrderSet` (2x in `inputs.py`) passes two distinct kwargs
  (`family_label` collision-message label vs `set_class_name` resolved class
  name); `related_orders` (5x in `sets.py`) names the metaclass-managed
  attribute threaded as the `collection_attr` / `related_attr` argument to the
  shared collectors/delegates; `order_input_type` (2x in `__init__.py`) is the
  symbol name plus the `family_name=` argument. No literal appears in two+ files
  as a genuine shared constant candidate — exactly mirroring the filters folder
  finding (`filterset` / `related_filters` / `FilterSet` / `filter_input_type`).

### Other positives

- **One-way dependency direction confirmed; no back-edge.** Cross-sibling
  import comparison (shadow overviews) shows the expected DAG: `orders/` depends
  outward on `sets_mixins.py`, `utils/` (`inputs`, `input_values`, `permissions`,
  `relations`), `types/definition` (TYPE_CHECKING), `exceptions`, and `asgiref`
  — and NONE of those import back into `orders/`. The folder-pass focus's stated
  expectation (shared mechanisms in `sets_mixins.py` + `utils/` are a one-way
  dependency) holds. Intra-folder the files form an acyclic chain
  `base <- inputs <- sets <- factories <- __init__`; the one runtime cycle that
  could close (`orders/sets.py` <-> `orders/inputs.py`) is broken by the
  in-function local import at `sets.py:248`
  (`from .inputs import _get_concrete_field_names_for_order`), and `inputs.py`'s
  `OrderSet` / `DjangoTypeDefinition` imports are TYPE_CHECKING-only. Crucially,
  `orders/base.py` imports the lazy mixin from `..sets_mixins`, NOT from
  `filters.base` — the neutral shared module per spec-028 Revision 4 H1,
  deliberately avoiding dragging the filter subsystem into the order import
  graph (pinned by `test_related_order_imports_lazy_mixin_from_sets_mixins_not_filters_base`).
- **Responsibility boundaries are clean and parallel to filters.** The
  input/factory/set/primitive split is coherent: `inputs.py` owns the `Ordering`
  enum + converter/normalizer pair + builders + the `FieldSpec`/`build_input_class`
  aliases + materialize/clear lifecycle; `factories.py` owns the BFS
  arguments-factory specialization (and the deferred-non-goal Layer-6 anchor);
  `sets.py` owns the `OrderSet`/metaclass declaration, Meta validation, the
  to-many fan-out aggregate defense, and the sync/async apply pipeline;
  `base.py` owns `RelatedOrder` lazy resolution. No file reaches across that
  boundary to re-implement another's surface, and each maps one-for-one onto its
  filter twin.
- **The to-many fan-out defense is the headline data-correctness surface and is
  correct.** `orders/sets.py::_resolve_order_expressions` (`sets.py:497-535`)
  routes a to-many ordering path through `.annotate(<alias>=Min/Max(path))` +
  order-by-alias instead of a raw `order_by("rel__col")`, forcing a GROUP BY on
  the parent so exactly one row per parent survives — preventing the fan-out
  JOIN that would silently duplicate/skip nodes under positional cursors and
  inflate `totalCount` (docs/feedback.md P1-B). `Min`=asc / `Max`=desc is the
  correct monotone choice; the enumerate-keyed alias `_dst_order_{index}_{path}`
  avoids annotation collisions. Verified live at the SQL layer in the
  `orders/sets.py` file pass (aggregate form emits `GROUP BY`, raw order_by does
  not). This is the one piece of genuinely order-specific logic with no filter
  analogue — correctly local to `sets.py`, not a shared-substrate candidate.
- **Error-handling vocabulary is consistent with the family.** The only
  misconfig raise in the folder (`OrderSet` Meta validation `"__all__"` with an
  absent `Meta.model`, `sets.py:252-256`) uses the package's typed
  `ConfigurationError`; the `OrderArgumentsFactory` collision check raises
  `ConfigurationError` via the shared base. No file invents a parallel exception
  type or substring-matches an error string. The order side has NO `apply(...)`
  dispatcher / `SyncMisuseError` translation (that is filter-only — django-filter
  form-data threading), a deliberate documented divergence, not drift.
- **Naming is consistent across the family.** The order/filter family-named
  thin-wrapper pattern (`bind_orderset` / `.orderset`; `order_input_type` /
  `filter_input_type`) is applied uniformly, and the per-family parameterization
  of the shared mixin (`_target_attr = "_orderset"` / `_owner_attr =
  "bound_orderset"`) deliberately differs only in the bound attribute names —
  intentional, not drift. The metaclass collection-ordering divergence is
  principled: `OrderSetMetaclass` passes `inherit_from_bases=True` (plain `type`
  does no MRO merge) where `FilterSetMetaclass` passes `False` (django-filter
  pre-merges `declared_filters`).
- **Sibling file artifacts all `verified` with no open High/Medium.** `base.py`
  and `sets.py` closed as shape #5 no-source-edit cycles; `factories.py` and
  `inputs.py` each landed a docstring-only deferred-state / mirror-alignment
  correction. No file-level finding remains unresolved that the folder pass must
  escalate beyond the consolidated GLOSSARY Medium.

### Summary

A well-factored subpackage at 0.0.9 that mirrors `filters/` faithfully. The
four source files form a clean acyclic chain (`base <- inputs <- sets <-
factories <- __init__`) over the shared `sets_mixins.py` + `utils/` substrate
with a confirmed one-way dependency direction and no back-edge (and a
deliberate `..sets_mixins`-not-`filters.base` import that keeps the two Layer-3
families decoupled); the input/factory/set/primitive responsibility split is
coherent and parallel to the filter twin; error-handling routes uniformly
through the typed `ConfigurationError` family; and the cross-sibling repeated
literals are all intentional family parameterization, not constants to hoist.
The order-specific to-many fan-out aggregate defense — the headline
data-correctness surface — is correct and proven live. The `__init__.py` export
surface (`__all__` of 5, the `order_input_type` shared-helper delegate, the
deliberately-omitted `OrderArgumentsFactory`) is accurate with no leak. The one
finding the folder pass must act on is the forwarded GLOSSARY defect: the
`OrderSet` (918) AND `Meta.orderset_class` (806) entries both version-pin the
deferred dynamic-`OrderSet` / connection-field surface to `0.0.9` — but Layer 6
never shipped (it is a settled standing-deferred non-goal; the `0.0.9`
connection field chose the explicit `Meta.orderset_class` sidecar path,
`connection.py:870-871/895-896/949-950`) and the connection field itself DID
ship at `0.0.9`, so both clauses are now-false. Recorded as Medium (a
public-contract prose defect duplicated across two parallel shipped entries)
with verbatim replacement text for both, so Worker 2 fixes them in one sweep.
(The parallel `RelatedOrder` entry at `:1004` was already corrected in the
filters folder pass — not re-touched.) Six DRY opportunities are all
deferred-with-trigger or intentional twins; no act-now folder DRY. No High; no
source-logic, ORM, or circular-import defect.

---

## Fix report (Worker 2)

Consolidated single-spawn (shape #4, GLOSSARY-prose only): no source/test
change, two version-pin-rot clause replacements in `docs/GLOSSARY.md`, lifted
verbatim from this artifact's Medium body. All three Worker 2 sections filled in
one pass; bare `Status: fix-implemented`.

### Files touched

- `docs/GLOSSARY.md:918` (`## OrderSet` entry, first paragraph trailing clause)
  — replaced "cycle-safe lazy resolution via the five-layer port + Layer 6
  deferred to `0.0.9`." with "cycle-safe lazy resolution via the five-layer
  port. Layer 6 (dynamic `OrderSet` generation against a connection-field meta
  dict) is a standing deferred non-goal: the connection field
  ([`DjangoConnectionField`](#djangoconnectionfield)) resolves ordering from the
  already-resolved [`Meta.orderset_class`](#metaorderset_class) sidecar directly
  rather than auto-generating an `OrderSet`, so no dynamic order factory is
  shipped." Verbatim per artifact Medium.
- `docs/GLOSSARY.md:806` (`## Meta.orderset_class` entry, "Consumer wiring"
  paragraph parenthetical) — replaced "(and on
  [`DjangoConnectionField`](#djangoconnectionfield) once it ships in `0.0.9`)."
  with "(and on [`DjangoConnectionField`](#djangoconnectionfield), which
  resolves ordering from this already-resolved sidecar directly)." Verbatim per
  artifact Medium.

Located by content, not line number (lines confirmed at 918 and 806 in current
tree). Both replacements use only existing in-page anchors
(`#orderset` self, `#djangoconnectionfield` at `:293` `## `DjangoConnectionField``,
`#metaorderset_class` at `:800` `## `Meta.orderset_class``) and inline code —
no inline cross-file `](path)` link introduced, so the `<!-- LINK DEFINITIONS
-->` block needs no change. `RelatedOrder`:1004 not touched (already corrected
in the filters folder pass per the baseline diff).

### Source-confirmation (premise re-verified before editing)

- Version is `0.0.9` (`pyproject.toml:4`, `__init__.py:25`).
- `get_orderset_class` / `_dynamic_orderset_cache`: `grep -rn` across
  `django_strawberry_framework/` + `tests/` + `examples/` returns matches ONLY
  in `orders/factories.py` (docstring `:18`, TODO `:90-91`) — zero defs, zero
  callers. Layer 6 never shipped.
- Connection field shipped at `0.0.9` and uses `definition.orderset_class`
  directly: `connection.py` `_pipeline_sync` (`if order_by_input is not None
  and definition.orderset_class is not None: qs =
  definition.orderset_class.apply_sync(...)`), `_pipeline_async` (`await
  definition.orderset_class.apply_async(...)`), and
  `list[order_input_type(definition.orderset_class)] | None` in the synthesized
  signature. No dynamic factory call; no build-from-`model`/`fields`. The
  artifact's verbatim text is accurate — no correction needed.

### Tests added or updated

None. GLOSSARY-prose-only change; no behaviour change; no test surface.

### Validation run

- `uv run ruff format .` — pass / no-changes (265 files left unchanged).
- `uv run ruff check --fix .` — pass (All checks passed!; the standing COM812
  formatter-conflict warning is pre-existing config noise, unrelated).
- `git diff --stat -- docs/GLOSSARY.md` — 1 file changed, +6/-6 (the two clause
  replacements only).
- `uv.lock` — clean (not modified).

### Notes for Worker 3

- No shadow file used (prose-only edit).
- No false-premise rejection; both verbatim clauses matched source exactly and
  the artifact's replacement text was accurate against live `connection.py` /
  `orders/factories.py`.
- Anchor validity: `#metaorderset_class` and `#djangoconnectionfield` resolve to
  the `## `Meta.orderset_class`` (`:800`) and `## `DjangoConnectionField``
  (`:293`) headings (GitHub strips backticks/dots/case); `#orderset` is the
  entry's own heading. All in-page, no LINK-block touch.

---

## Comment/docstring pass

Folded into the consolidated single-spawn. The sole cycle edit IS prose
(GLOSSARY entries) — there is no separate code-comment/docstring surface to
re-pass after a logic change, because there was no logic change. The
`orders/factories.py` module-docstring + TODO version-pin rot (the sibling
prose) was already reworded to a "standing deferred non-goal" at the
`orders/factories.py` file pass (`rev-orders__factories.md`, verified) and is
out of this folder pass's edit scope.

### Files touched

- (same as Fix report) `docs/GLOSSARY.md` — the two clause replacements double
  as the comment/docstring pass for this folder.

### Per-finding dispositions

- Medium (GLOSSARY `OrderSet` 918 + `Meta.orderset_class` 806 dual version-pin
  rot): FIXED — both clauses replaced verbatim per the artifact, in one sweep,
  keeping the `OrderSet` / `Meta.orderset_class` / `order_input_type` /
  `Ordering` cluster parallel.
- Low (`orders/factories.py` mirror-target cross-reference): no action — recorded
  at the file pass for project-pass awareness only; pointer correct and intact.
- Low (`orders/inputs.py` `_field_specs` cross-file comment): no action —
  verified accurate at the `orders/sets.py` pass; no stale-comment edit.
- Low (`orders/__init__.py` export surface): no action — reviewed, no defect.
- All six DRY candidates: deferred-with-trigger or intentional twins; no act-now
  folder DRY.

### Validation run

- `uv run ruff format .` — pass / no-changes.
- `uv run ruff check --fix .` — pass.

### Notes for Worker 3

Comment pass is fully subsumed by the single prose edit; nothing further.

---

## Changelog disposition

### State

`Not warranted`.

### Reason

The cycle's only edit is documentation prose — two now-false version-pin clauses
in `docs/GLOSSARY.md` corrected to describe the already-shipped `0.0.9` reality
(Layer 6 is a settled standing-deferred non-goal; the connection field resolves
ordering from the `Meta.orderset_class` sidecar directly). No source, no test,
no consumer-visible behaviour change — internal-only doc accuracy. Cites BOTH:
(1) `AGENTS.md` #21 "Do not update CHANGELOG.md unless explicitly instructed",
and (2) the active plan's silence — this is a per-folder cycle, which per the
changelog dicta is NEVER the authorising scope and forwards any `CHANGELOG.md`
drift to the project pass; the dispatch prompt and artifact authorise only the
`docs/GLOSSARY.md` edit, not a `CHANGELOG.md` edit.

### What was done

No `CHANGELOG.md` edit.

### Validation run

- `uv run ruff format .` — pass / no-changes.
- `uv run ruff check --fix .` — pass.

---

## Verification (Worker 3)

### Logic verification outcome

No source-logic change this cycle (shape #4, GLOSSARY-prose only). The folder
pass's sole edit is the two version-pin-rot clause replacements. Independently
re-confirmed every premise the rewording rests on:

- **Deferred Layer-6 surface ABSENT.** `grep -rn
  "get_orderset_class\|_dynamic_orderset_cache"` over
  `django_strawberry_framework/` + `tests/` + `examples/` matches ONLY
  `orders/factories.py` docstring (`:18`) + TODO (`:90-91`) prose — zero symbol
  defs, zero callers. The "standing deferred non-goal / no dynamic order factory
  is shipped" wording is accurate.
- **`connection.py` uses the explicit `definition.orderset_class` sidecar, not a
  dynamic factory.** `apply_sync` (`:870-871`), `apply_async` (`:895-896`), and
  `order_input_type(definition.orderset_class)` (`:949-950`) all read the
  already-resolved sidecar; `grep "get_orderset_class\|_dynamic_orderset"`
  against `connection.py` = no match. So "resolves ordering from the
  already-resolved sidecar directly" is correct for BOTH entries.
- **Neither rewritten clause version-pins `0.0.9`** (or any version): the `^+`
  lines of the two cycle hunks contain no `0.0.x` token.

### DRY findings disposition

Six DRY candidates all deferred-with-trigger or recorded as intentional family
twins (cross-family Layer-6 cache lift; order-side converter/normalizer family;
`del <unused-args>` affordance; sync/async apply tail; `_run_permission_checks`
prologue; `order_input_type`/`filter_input_type` delegate). None clears the
act-now bar for a two-member family. No act-now folder DRY — concurred.

### Folder-pass conclusions (spot-checked)

- filters↔orders parallelism faithful: one-way DAG (`base <- inputs <- sets <-
  factories <- __init__` over `sets_mixins.py` + `utils/`), no back-edge,
  shared-substrate reuse via family-named thin wrappers; `orders/base.py`
  imports the lazy mixin from `..sets_mixins` not `filters.base`.
- `orders/__init__.py` `__all__` (5 names: `OrderSet`, `OrderSetMetaclass`,
  `Ordering`, `RelatedOrder`, `order_input_type`) matches public surface; no
  private leak; `OrderArgumentsFactory` deliberately not re-exported.
- No real folder-level defect missed.

### Diff scope (shape #4)

`git diff <baseline> -- docs/GLOSSARY.md`: this cycle owns exactly the two hunks
— `## Meta.orderset_class` (`:806`, "Consumer wiring" parenthetical) and
`## OrderSet` (`:918`, first-paragraph trailing clause). Both replacements use
only in-page anchors (`#djangoconnectionfield`, `#metaorderset_class`,
`#orderset` — all live headings); no inline cross-file `](path)` link
introduced, `<!-- LINK DEFINITIONS -->` untouched. The other GLOSSARY hunks
attribute to closed sibling cycles: line-286 `DjangoConnection` -> rev-connection.md;
lines 991/1001 `RelatedFilter`/`RelatedOrder` -> rev-filters.md (verified, `[x]`
at `review-0_0_9.md:83`); line-1178 inspect -> rev-management__commands__inspect_django_type.md.
`RelatedOrder` (`:1004`) NOT touched by this cycle. No source/test edit owned by
this pass: the dirty `orders/factories.py` + `orders/inputs.py` source hunks
attribute to closed siblings rev-orders__factories.md (`[x]` `:101`) /
rev-orders__inputs.md (`[x]` `:102`); the folder pass's own "Files touched:
`docs/GLOSSARY.md` only" holds. All other dirty source/test paths are closed
verified+`[x]` siblings; `feedback2/3.md` deletes = AGENTS #33 concurrent work.

### Changelog disposition

`git diff -- CHANGELOG.md` empty. `Not warranted` cites BOTH AGENTS #21 and the
active plan's silence (per-folder cycle is never the authorising scope). Framing
honest — GLOSSARY-prose-only, no consumer-visible behaviour change. Accepted.

### Temp test verification

None used (prose-only edit).

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the
orders/ folder-pass checklist box. ruff format-check + check pass (COM812 =
standing config noise). Both version-pin-rot entries fixed in one sweep,
parallel prose preserved; `RelatedOrder`:1004 untouched.

---

## Iteration log
