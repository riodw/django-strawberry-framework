# Review: `django_strawberry_framework/` (project pass)

Status: verified

The final synthesis pass before the test-run gate. Supersedes the stale on-disk
0.0.7-era `rev-django_strawberry_framework.md` (`Status: verified`, predates the
0.0.9 surface) wholesale per the recurring stale-artifact pattern; the active
plan box at `review-0_0_9.md:128` was unchecked, confirming the replacement.
This pass ALSO covers the top-level package export surface
`django_strawberry_framework/__init__.py` (`__all__`), which no per-file cycle
reviewed (REVIEW.md scope: top-level `__init__.py` is covered only at the
project pass).

Inputs synthesized: all 8 folder artifacts (`rev-filters.md`,
`rev-management.md`, `rev-management__commands.md`, `rev-optimizer.md`,
`rev-orders.md`, `rev-testing.md`, `rev-types.md`, `rev-utils.md`), each
`Status: verified`, plus the forwarding per-file artifacts they cite. This is a
synthesis, not a re-review: per-file findings already verified are NOT
re-litigated. Every forwarded item below was re-confirmed at LIVE source this
pass (not trusted from the artifacts).

This pass warrants ONE act-now project-level source edit (a `check_permissions`
dead-code cleanup in `orders/sets.py` + its two orphan tests + a stale docstring
line — Medium, item 4 below), so it routes standard `under-review`, NOT a
no-source-edit shape.

## DRY analysis

- **Shared relay field-guard / relay-predicate home (DEFER-with-trigger; do NOT
  act now).** Two cross-cutting relay-shape spellings exist outside their
  natural home:
  1. `list_field.py::_validate_relay_djangotype_target` (`list_field.py:99`) --
     a *relay-target validation* guard living in the non-Relay `list_field`
     module, imported by BOTH `connection.py` (`connection.py:59`, called
     `:1206`) and `relay.py` (`relay.py:63`, thin-wrapped `:166`). Each importer
     carries an explicit naming comment (`connection.py:1200`, `relay.py:160`)
     pointing back at the `list_field.py::_validate_relay_djangotype_target`
     home, so the single-home contract is documented and the two consumers do
     NOT re-spell the body -- this is deliberate single-source-with-cross-
     reference, not duplication.
  2. `management/commands/inspect_django_type.py::_is_suppressed_relay_pk`
     (`inspect_django_type.py:202-211`) -- re-spells the EXACT body of
     `types/base.py::_is_relay_shaped` (`base.py:446`):
     `any(issubclass(i, relay.Node) for i in <interfaces>) or issubclass(<origin/cls>, relay.Node)`.
     `_is_relay_shaped` is module-private to `types/base.py`; the inspect
     command is now a second consumer of that predicate's logic, in a different
     folder, via a hand-copied body.

  **Decision: defer-with-trigger, recorded precisely.** Consolidating would
  destabilize already-verified files for a small (effectively 2-site) re-spell,
  and the two clusters pull in different directions:
  - The `_validate_relay_djangotype_target` placement is already correct
    (single home in `list_field.py`, two cross-referenced importers). The only
    "defect" is that the home module is named for the list field, not relay --
    but moving it would touch 3 verified files (`list_field`, `connection`,
    `relay`) to relocate a function that already has exactly one definition. Not
    worth it at the current consumer count. **Trigger: a fourth relay-target
    consumer lands, OR `list_field.py` is split** -- then lift
    `_validate_relay_djangotype_target` into a neutral relay-guard home (a
    `types/relay.py` helper or a small `_relay_guards.py`) and rewire the (then
    3+) importers.
  - The `_is_relay_shaped` re-spell is the live one: `inspect_django_type` is
    the second site, so the trigger named in `rev-management__commands.md`
    (DRY bullet 2: "a second consumer outside `types/base.py`") is effectively
    armed. **But `_is_relay_shaped` cannot move trivially:** the `types/` folder
    pass (`rev-types.md`, "Relay-shaped predicate cluster") proved the IN-types
    cluster PRINCIPLED -- `_is_relay_shaped(cls, interfaces)` is a TWO-arg
    pre-`__bases__`-injection predicate (must scan `Meta.interfaces` because the
    `Node` base is not yet in the MRO) and is DISTINCT from
    `relay.py::implements_relay_node(type_cls)` (one-arg, post-injection,
    `issubclass(., Node)`); those two must NOT merge. The inspect command's
    re-spell is the *pre-injection two-arg* form against a finalized
    `DjangoTypeDefinition` (`definition.interfaces` / `definition.origin`).
    Promoting `_is_relay_shaped` to a public `types`-package helper (e.g.
    `types/relay.py::is_relay_shaped(interfaces, origin)`) consumed by both
    `types/base.py` and `inspect_django_type` is the right shape -- **but defer
    until the maintainer is willing to take a `types/base.py` edit**, because the
    promotion touches the verified `base.py` (3 internal call sites at
    `:570/:1084/:1558`) for a single external re-speller. **Trigger (quote
    verbatim): "`_is_relay_shaped` promotion is taken up, OR a third relay-shape
    re-spell lands outside `types/base.py`"** -- then promote the two-arg
    predicate to a shared `types`-package helper and import it in both
    `types/base.py` and `inspect_django_type.py`, deleting the inspect re-spell.

  Bias-toward-defer applied per the cycle guidance: both clusters are recorded
  with armed/explicit triggers rather than forced now.

- **Cross-family Layer-6 dynamic-set cache lift into `utils/inputs.py`
  (DEFER-with-trigger; confirmed STILL deferred).** The filter side ships a
  built-and-tested-but-zero-consumer Layer-6 dynamic-`FilterSet` cache
  (`filters/factories.py`: `get_filterset_class` + `_dynamic_filterset_cache` +
  `_make_cache_key` + `_make_hashable` + `_create_dynamic_filterset_class` +
  `_RESERVED_FACTORY_KEYS`); the order side ships NO Layer-6 surface at all --
  only a TODO anchor (`orders/factories.py:90-91`) naming the forward-reserved
  `_dynamic_orderset_cache` / `get_orderset_class` (grep this pass: zero defs,
  zero callers anywhere in `django_strawberry_framework/`/`tests/`/`examples/`,
  matches only inside that file's own docstring + TODO). Because the order side
  has zero Layer-6 code, there is **nothing to consolidate today** -- the neutral
  BFS substrate is already single-sited in
  `utils/inputs.py::GeneratedInputArgumentsFactory`, and the connection field
  consumes `definition.filterset_class` / `definition.orderset_class` sidecars
  directly (`connection.py` apply_sync/apply_async), never a dynamic factory.
  **Stays deferred. Trigger (verbatim, unchanged from the filters/orders folder
  passes): "the order dynamic cache lands"** -- i.e. when an `OrderSet` dynamic
  cache is actually built AND shares the filter side's `(model, fields,
  extra_meta)` keying; only then lift the common dynamic-cache machinery
  (`_make_cache_key` + `_make_hashable` + reserved-key strip + get/build/store
  skeleton) into `utils/inputs.py` (`make_generated_set_cache_key(safe_meta)` +
  `get_or_build_dynamic_set(...)`), leaving only the family-specific
  `_create_dynamic_*_class`.

- **Dependency-direction narrative: the sanctioned lazy `optimizer/walker.py ->
  types.definition` back-edge (DOC note, no act-now consolidation).** The single
  permitted `optimizer -> types` edge is the in-function lazy import
  `from ..types.definition import origin_has_custom_id_resolver`
  (`optimizer/walker.py:801`), under an explicit cycle-dodge comment, a
  leaf-function read for the definition-less custom-`id`-resolver fallback. The
  `types/__init__.py` docstring was ALREADY softened in the `types/` folder
  cycle (rev-types.md L2, verified) to name this exact exception and scope the
  one-way rule to module-import time. Nothing further to consolidate -- this is
  the correct factoring (the function is single-homed in `types/definition.py`
  and consumed both by the memoized hot path and this fallback). See the Low
  below for the only residual: whether the package-wide dependency-direction
  narrative should canonize it. No shared-helper extraction warranted.

- **No further act-now project-level DRY.** Every other cross-folder candidate
  the folder passes surfaced is intentional family-sibling design (filter/order
  family-named thin wrappers over `sets_mixins.py` + `utils/`; the
  `filter_input_type`/`order_input_type` delegates over the shared
  `utils/inputs.py::build_lazy_input_annotation`; the sync/async twins across
  relay/list_field/connection/filters/orders) or deferred-with-trigger in its
  owning artifact with an unfired trigger. The `utils/` substrate is the
  realized DRY home -- a one-way leaf with zero back-edges.

## High:

None. (Two prior Highs are RESOLVED package-wide, recorded under
`## What looks solid > ### Other positives`; neither is re-opened.)

## Medium:

### `orders/sets.py::OrderSet.check_permissions` is dead production code (reads a never-written `_input_value`); the live order gate fires via the classmethod path

`OrderSet.check_permissions(self, request)` (`orders/sets.py:448-460`) routes
through `type(self)._run_permission_checks(getattr(self, "_input_value", None),
request)`. The instance attribute `_input_value` is **never written anywhere in
production source** -- grep across `django_strawberry_framework/` returns the
read at `orders/sets.py:460` and the docstring mention at `:457`, and ZERO
writers; the only writer in the entire repo is a test
(`tests/orders/test_sets.py:464`, `instance._input_value = input_value`). So in
production `getattr(self, "_input_value", None)` is always `None`,
`_run_permission_checks` hits its `if input_value is None: return` guard
(`orders/sets.py:427-428`), and the bound method is a guaranteed no-op.

**This is NOT a security hole -- the live order-side permission gate is sound.**
The real gate fires from the apply pipeline via the CLASSMETHOD path:
`apply_sync` calls `cls._run_permission_checks(input_value, request)`
(`orders/sets.py:566`) and `apply_async` calls it under `sync_to_async`
(`orders/sets.py:605`), in both cases with the freshly-normalized `input_value`
in hand and BEFORE `order_by`/`.annotate` touch the queryset. The connection
field drives ordering through `definition.orderset_class.apply_sync/async`, so
the classmethod gate is the one that runs in every real request. The bound
method is a parallel cookbook-compatibility entry point
(`django_graphene_filters/orderset.py::AdvancedOrderSet.check_permissions`) that
was ported with an instance-state assumption (`self._input_value`) the 0.0.9
apply pipeline never satisfies -- it normalizes and passes `input_value`
explicitly rather than parking it on the instance.

Severity rationale: **Medium (dead code needing consolidation/removal)**, not
High -- there is no missed gate (the classmethod path is proven to fire) and no
data-isolation risk. It is promoted above Low because the dead surface is a
*permission* method whose presence misleads a reader into believing the
bound-method form is a live gate, and it is pinned by two orphan tests that
assert behavior no production path exercises -- a maintainability + false-coverage
hazard on a security-adjacent surface. The filter side's `check_permissions`
(`filters/sets.py:1290`) is genuinely live (django-filter form-data threading,
real consumers + tests at `test_sets.py:1424/1771`); the order side has no such
consumer.

**Recommended change (act-now, project-level cleanup -- the project pass is the
authorising scope for a cross-folder dead-code removal that no single file cycle
owned):**

1. Remove `OrderSet.check_permissions` (`orders/sets.py:448-460`) -- the
   bound-method delegate. The live gate (`_run_permission_checks` via
   `apply_sync`/`apply_async`) is unaffected.
2. Remove the two orphan tests that only exercise the removed method by manually
   seeding `_input_value`:
   `tests/orders/test_sets.py::test_orderset_check_permissions_instance_method_delegates`
   (`:448-466`) and
   `tests/orders/test_sets.py::test_orderset_check_permissions_instance_tolerates_no_input_value`
   (`:470-480`), plus the section comment header at `:443-444`.
3. Remove the stale `_input_value` line from the module-level docstring that
   frames the bound method as a shipped surface -- the `orders/sets.py` module
   docstring bullet at `orders/sets.py:16` ("Add the ``check_permissions``
   instance method + the classmethod") should drop the instance-method half so
   it names only the live classmethod gate.

**Alternative considered and rejected:** keeping the method but wiring
`_input_value` so the bound form becomes live. Rejected -- the apply pipeline
deliberately passes `input_value` explicitly (no instance state parked across
the resolve), and adding a write of `_input_value` to make a redundant second
entry point live would manufacture mutable per-instance request-scoped state for
no consumer. AGENTS.md "root-cause fix, never the wrong abstraction" favors
removing the dead delegate over resurrecting it.

**Test impact:** after removal, no production behavior changes (the method was a
no-op); the two removed tests asserted only the dead path. The live order-gate
coverage (`tests/orders/test_sets.py` apply-pipeline tests +
`tests/orders/test_inputs.py` normalize tests) is untouched. If the maintainer
prefers to KEEP the cookbook-compat surface for API parity with the cookbook
port, the fallback is to demote this to a forwarded Low and leave it -- but the
default recommendation is removal, because a dead permission method with
false-coverage tests is a worse maintainability state than a missing
cookbook-parity affordance no consumer uses.

## Low:

### Package-wide dependency-direction narrative does not canonize the one sanctioned `optimizer -> types` lazy back-edge

The `types/__init__.py` module docstring was corrected this release
(`rev-types.md` L2, verified) to scope the "optimizer must not import back from
`types/`" rule to module-import time and name the single permitted exception
(`optimizer/walker.py:801`'s in-function `origin_has_custom_id_resolver`
fallback). That fix is local to the `types/__init__.py` docstring. The
package-wide import-DAG narrative -- wherever a contributor first learns the
dependency-direction story (`GOAL.md` / `README.md` positioning, or a future
`docs/` architecture note) -- does not mention the sanctioned lazy back-edge, so
a contributor auditing the DAG from the top-level story could still conclude the
edge is a violation. **Forward-looking, no act-now edit:** there is no single
canonical "import DAG" doc today to amend, and the in-source docstring (the place
a reader actually checks when touching `walker.py` or `types/`) is now accurate.
Recorded as a Low so it is not re-discovered as untriaged. Re-triage when a
package-wide architecture/dependency-direction doc is authored (or the existing
`GOAL.md`/`README.md` grows an explicit import-DAG section); canonize the lazy
back-edge there as the documented pattern at that point. Non-contract (no
GLOSSARY surface).

### Both order- and filter-side Layer-6 dynamic-set surfaces are deferred non-goals -- recorded for project awareness

Carried up from `rev-filters.md` and `rev-orders.md`: the filter side ships a
build-and-test-only Layer-6 dynamic-`FilterSet` cache with zero source consumers
(documented deferred non-goal -- the connection field uses the explicit
`Meta.filterset_class` sidecar), and the order side ships no Layer-6 code at all
(only a TODO anchor pointing at the filter surface as the shape to mirror). Both
are settled standing-deferred non-goals per spec-027/spec-028 Decision 12, not
wiring gaps. No project-level action; the cross-family DRY lift is the
deferred-with-trigger item in `## DRY analysis` ("the order dynamic cache
lands"). Recorded only so the project pass is on record that the package
deliberately carries one built-but-unconsumed surface (filters) and one
reserved-but-unbuilt surface (orders), both gated on the same future trigger.

## What looks solid

### DRY recap

- **Existing patterns reused (package-wide).** The 0.0.9 DRY consolidation is
  fully realized and one-way: `utils/` is the cross-cutting leaf substrate
  (`relations` / `strings` / `typing` / `input_values` / `permissions` /
  `inputs` / `querysets` / `connections`) that every subsystem imports back from
  rather than re-spelling, with ZERO back-edges into `utils/` (verified at the
  utils folder pass -- the only sibling-subsystem token in `utils/*.py` is a
  comment, not an import). The filter and order families are deliberate
  per-family mirrors parameterizing the shared `sets_mixins.py` + `utils/`
  substrate through family-named thin wrappers (`bind_filterset`/`bind_orderset`,
  `filter_input_type`/`order_input_type` both delegating to
  `utils/inputs.py::build_lazy_input_annotation`); the optimizer's
  `selections.py` is the 0.0.9 home that removed the reverse `extension <-
  walker` edge; `types/` single-sources the GlobalID strategy vocabulary
  (base), storage slot (definition), stamp+encode+decode (relay), and audit-read
  (finalizer) one-owner-per-concern.
- **New helpers considered (package-wide).** No act-now project-level extraction
  beyond the two recorded in `## DRY analysis` (both deferred-with-trigger): the
  shared relay field-guard/predicate home and the cross-family Layer-6 cache
  lift. Every per-folder defer-with-trigger bullet (the optimizer fragment-walk
  folds, the filter/order converter-normalizer ladders, the sync/async apply
  tails, the postgres-contrib folds, the `_target_for_field` funnel) gates on an
  explicit unfired trigger and would obscure rather than clarify at the current
  site count.
- **Duplication risk across folders.** No string/key/tuple literal is shared as
  a genuine constant candidate across two+ folders: the cross-sibling repeats
  the shadow overviews surfaced are all intentional family parameterization
  (`filterset`/`orderset` hook-name pairs; `related_filters`/`related_orders`
  collection-attr tokens; `filter_input_type`/`order_input_type` symbol+arg; the
  relation-kind token vocabulary in `relations.py`) or reflective attribute
  names duck-typed at the call site, not constants to hoist. The single genuine
  cross-folder body re-spell is `_is_relay_shaped` (handled as the deferred DRY
  item above).

### Other positives

- **Public export surface (`__init__.py` `__all__`) is consistent with the
  public-contract docs -- VERIFIED.** `__version__ = "0.0.9"`
  (`__init__.py:25`) matches `pyproject.toml:4` `version = "0.0.9"` (AGENTS.md
  "bump both together" satisfied). `__all__` is a 14-element tuple: `BigInt`,
  `DjangoConnection`, `DjangoConnectionField`, `DjangoListField`,
  `DjangoNodeField`, `DjangoNodesField`, `DjangoOptimizerExtension`,
  `DjangoType`, `OptimizerHint`, `SyncMisuseError`, `__version__`, `auto`,
  `finalize_django_types`, `strawberry_config`. Every one resolves to a live
  import (`auto` re-exported from strawberry as the DRF-shaped convenience
  surface; `SyncMisuseError`'s chain `utils/querysets.py` origin -> `types/relay`
  re-export -> `types/__init__` -> top-level is consistent at every hop). Each of
  the 12 documentable exports (`__version__` is metadata, `auto` is covered too)
  has a `## ` GLOSSARY heading -- `#bigint`, `#djangoconnection`,
  `#djangoconnectionfield`, `#djangolistfield`, `#djangonodefield`,
  `#djangonodesfield`, `#djangooptimizerextension`, `#djangotype`,
  `#optimizerhint`, `#syncmisuseerror`, `#finalize_django_types`,
  `#strawberry_config`, plus `auto` at `#auto-typed-annotations`. **No exported
  symbol is missing from the docs, and no GLOSSARY/README-documented top-level
  package symbol is absent from `__all__`** -- the only documented top-level
  handle deliberately NOT in `__all__` is `logger` (`__init__.py:13`), and that
  omission is intentional and self-documented (the inline comment at
  `__init__.py:7-12` states it is the consumer-facing logging key but withheld
  from `__all__`; subpackages re-export it via `from .. import logger`).
  `SyncMisuseError` appears in GLOSSARY (the contract surface) but not in
  README/docs/README prose -- correct, it is an error class documented under its
  own entry. Export-vs-docs verdict: **consistent, no drift, no missing/extra
  symbol.**
- **Settings/config boundary is clean.** `conf.py` reads
  `DJANGO_STRAWBERRY_FRAMEWORK` from the consumer's settings dict and raises
  `AttributeError` on a missing key (AGENTS.md-codified); no key is preemptively
  populated (the `RELAY_GLOBALID_STRATEGY` strategy setting is read defensively
  via `getattr` and re-validated through the shared
  `types/relay.py::_validate_globalid_strategy`, the same validator the `Meta`
  path uses -- single-sourced). The `conf.py` file cycle closed clean (two
  cosmetic Lows). No subsystem reaches around `conf.settings` to read the
  consumer settings dict directly.
- **Optimizer / type / registry responsibility boundaries are coherent.**
  `registry` keys on model identity (so `registry.clear()` never wrong-hits;
  type-identity caches are evicted, model-keyed `_enums` are not); `types/` owns
  definition metadata + finalize + GlobalID + relation-shape synthesis;
  `optimizer/` owns plan/window/selection traversal and the runtime N+1
  `OptimizerError`; the `ConfigurationError` (build/config) vs `OptimizerError`
  (runtime N+1) vs `SyncMisuseError` (sync-context misuse) vs the
  `UnwindowableConnection` control-flow sentinel split is uniform across the
  whole package by blast radius. The one sanctioned `optimizer -> types` lazy
  back-edge is the documented exception (DRY note above).
- **RESOLVED package-wide outcome #1 -- optimizer anonymous-inline-fragment High
  (FIXED, do not re-open).** An anonymous inline fragment (`... { ... }`,
  `type_condition=None`) under any optimized field crashed the resolver
  (`'NoneType' object has no attribute 'name'`) on BOTH the connection and the
  middleware list paths, because `extension.py::apply_to` routed selection
  conversion through Strawberry's `convert_selections`. Fixed at root cause in
  the optimizer folder cycle (`rev-optimizer.md`, verified): a fragment-aware
  `ast_to_converted_selections` adapter + a `prime_selected_fields` cached-slot
  primer in `optimizer/selections.py`, rewired at `extension.py::apply_to` and
  `connection.py::_resolve_connection_fast_path`, no try/except, pinned by four
  live fakeshop tests. It escaped a released contract (the list path shipped in
  0.0.7/0.0.8) -- a maintainer-deferred `### Fixed` CHANGELOG entry is preserved
  verbatim in `rev-optimizer.md` (changelog disposition: "Warranted but deferred
  to maintainer"). Recorded here as a resolved package-wide outcome; the
  maintainer-ready CHANGELOG text lives in `rev-optimizer.md`, not re-authored
  here (project pass does not touch CHANGELOG.md).
- **RESOLVED package-wide outcome #2 -- connection `after`+`last` cursor-parity
  High (FIXED, Not-warranted, do not re-open).** `utils/connections.py`'s
  `after`+`last` pageInfo split (the reverse predicate omitting `after is None`)
  was fixed at root cause in the `utils/connections.py` file cycle and verified
  with a live wire-parity pin (`rev-utils.md`). New-in-0.0.9 surface that never
  escaped a released contract -> changelog Not-warranted. Recorded as resolved;
  not re-opened.
- **Recurring-bug-class note: "a selection/cursor shape the windowed/converted
  path mishandles."** The two Highs this release were the same class -- a valid
  GraphQL selection-or-pagination shape that the package's windowing/conversion
  layer represented incompletely (the anonymous fragment with `type_condition =
  None` that `convert_selections` could not model; the `after`+`last` combo the
  reverse-window predicate did not guard). Worth a package-wide note for future
  reviewers: when reviewing the optimizer/connection conversion + window-bounds
  surfaces, ENUMERATE the full input space (every fragment shape x every
  first/last/after/before/0 pagination combo) against the LIVE engine and
  simulate BOTH consumer page-flag/selection-conversion paths -- both Highs hid
  from row-equality / typed-fragment / pure-last-only tests precisely because the
  mishandled shape was the un-enumerated corner. Both are now fixed and pinned;
  the note is calibration for the next cycle, not an open finding.
- **Package-wide test discipline is consistent.** Coverage source is
  `django_strawberry_framework` only (example app outside the gate, AGENTS.md);
  every High this release earned a live `/graphql` fakeshop pin per "test through
  real usage." No package-wide test gap surfaced beyond the order-side
  `check_permissions` orphan-test issue (the Medium -- those two tests pin a dead
  path and should be removed with the method, not a coverage gap to fill).

### Summary

The package is in excellent shape at 0.0.9. All eight folder passes are
`verified`; the project synthesis confirms a clean, strictly one-way dependency
architecture -- `utils/` the cross-cutting leaf, the filter/order families
faithful per-family mirrors over `sets_mixins.py` + `utils/`, the optimizer a
one-way DAG with `selections.py` the 0.0.9 selection-traversal home, and `types/`
single-owner-per-concern for definition/GlobalID/relation-shape -- with exactly
one sanctioned `optimizer -> types` lazy back-edge that the `types/__init__.py`
docstring already documents. The top-level export surface is correct:
`__version__` matches `pyproject.toml` at 0.0.9, the 14-element `__all__`
resolves entirely, every documentable export has a GLOSSARY entry, no documented
top-level symbol is missing from `__all__` (the only out-of-`__all__` handle,
`logger`, is intentionally and self-documentedly withheld), and
`SyncMisuseError`'s re-export chain is consistent at every hop. The
settings/config boundary (`conf.py` / `DJANGO_STRAWBERRY_FRAMEWORK` /
`RELAY_GLOBALID_STRATEGY` via the shared validator) is clean with no
preemptive-population, and the `ConfigurationError`/`OptimizerError`/
`SyncMisuseError`/`UnwindowableConnection` vocabulary split is uniform by blast
radius. Both release Highs are RESOLVED and not re-opened (the optimizer
anonymous-inline-fragment crash -- maintainer-deferred CHANGELOG entry preserved
in `rev-optimizer.md`; the `after`+`last` cursor-parity -- Not-warranted), and
they share a recurring bug class worth a forward calibration note (a
selection/cursor shape the windowed/converted path mishandles). The ONE act-now
project-level finding is a Medium: `OrderSet.check_permissions`
(`orders/sets.py:448-460`) is dead production code reading a never-written
`_input_value` (the live order gate fires via the classmethod
`_run_permission_checks` from `apply_sync`/`apply_async`, proven; NOT a security
hole) -- recommend removing the bound method, its two orphan tests
(`tests/orders/test_sets.py:448/470`), and the stale module-docstring line, with
a keep-as-Low fallback if the maintainer wants cookbook-parity. Two Lows are
forward-looking (the dependency-direction narrative canonization; the dual
deferred Layer-6 surfaces). The two DRY items (shared relay field-guard/predicate
home; cross-family Layer-6 cache lift) are both defer-with-trigger with explicit,
recorded triggers -- biased toward defer because consolidating either would
destabilize many already-verified files for a small re-spell. `Status:
under-review` -- the `check_permissions` dead-code Medium warrants an act-now
source+test edit, so Worker 2 implements before this pass can verify.

---

## Fix report (Worker 2)

Consolidated single-spawn: a pure dead-code deletion (the Medium) with no
comment/changelog contract interaction — the docstring line repair is part of
the removal itself, and the two Lows are forward-looking per Worker 1's own
prose. Logic + comment + changelog dispositions folded into one pass.

### Files touched

- `django_strawberry_framework/orders/sets.py::OrderSet.check_permissions` —
  REMOVED the dead bound-method delegate (was `orders/sets.py:448-460`). It read
  `getattr(self, "_input_value", None)`, an instance attribute NEVER written in
  production source, so `_run_permission_checks` always hit its `if input_value
  is None: return` guard and the method was a guaranteed no-op. The live order
  gate is the classmethod path `apply_sync` (`:566` pre-removal) /
  `apply_async` calling `cls._run_permission_checks(input_value, request)` with
  the input passed as an ARGUMENT — left untouched.
- `django_strawberry_framework/orders/sets.py` module docstring (was `:16-20`)
  — dropped the "Add the ``check_permissions`` instance method + the
  classmethod pipeline" framing's instance-method half; the bullet now reads
  "Add the classmethod permission pipeline (…)", naming only the live gate.

### Tests added or updated

- REMOVED `tests/orders/test_sets.py::test_orderset_check_permissions_instance_method_delegates`
  (was `:447-467`) — the only test that manually seeded `instance._input_value`
  (the sole `_input_value` writer in the entire repo) to make the dead bound
  method fire.
- REMOVED `tests/orders/test_sets.py::test_orderset_check_permissions_instance_tolerates_no_input_value`
  (was `:470-480`) — asserted the no-op early-return of the same dead method.
- REMOVED the section comment header "Slice 2 - check_permissions instance
  method (cookbook compatibility)" (was `:442-444`) that framed the removed
  group.
- No test added: this is a removal of false-coverage tests for a no-op. The live
  order-gate coverage (apply-pipeline tests + `tests/orders/test_inputs.py`
  normalize tests) is untouched.

### Validation run

- `uv run ruff format .` — pass / no-changes (265 files unchanged).
- `uv run ruff check --fix .` — pass / All checks passed.
- `git diff --stat` vs baseline `0872a20`: `orders/sets.py` 2 insertions / 16
  deletions; `tests/orders/test_sets.py` 41 deletions.
- Did NOT run pytest (per AGENTS.md / role; final-gate cycle runs the suite).

### Notes for Worker 3

- **Diff is logic-bearing** (a production source removal). The removed method was
  proven a no-op, so no behaviour changes, but it is a source edit not a doc-only
  one.
- **Grep proof the surface was dead (re-confirmed at live source this pass):**
  - `grep -rn "_input_value" django_strawberry_framework/ tests/ examples/` — the
    ONLY writer of the `_input_value` attribute was the test at
    `tests/orders/test_sets.py:464` (now removed). All production hits were
    `normalize_input_value` (a different symbol, substring match) plus the
    docstring/read in the removed method. Zero production writers.
  - `grep -rn "check_permissions" django_strawberry_framework/orders/ tests/orders/`
    after removal — ZERO hits. Pre-removal the orders-side bound method had only
    two callers, both the removed tests (`tests/orders/test_sets.py:466`, `:480`).
- **Classmethod gate path untouched.** `apply_sync` /
  `apply_async` → `cls._run_permission_checks(input_value, request)` (input as
  argument) is the live gate and was not edited.
- **Filter twin untouched and confirmed functional.** `filters/sets.py:1290`
  `FilterSet.check_permissions(self, request, requested_fields=None)` delegates
  with real bound-form data (django-filter form threading) and has live
  consumers + tests (`tests/filters/test_sets.py:1437`, `:1782`). Different
  signature, different (live) behaviour — NOT touched.
- **Orphan sweep:** all imports in `tests/orders/test_sets.py` still used after
  removal (`HttpRequest` 9 uses, `pytest` 14, `OrderArgumentsFactory` 14,
  `object.__new__` survives at the remaining site). No orphaned imports/fixtures.
- `uv.lock` clean (not touched).

---

## Verification (Worker 3)

### Logic verification outcome

Terminal verification of the project-level pass's ONE act-now edit (the Medium:
`OrderSet.check_permissions` dead-code removal). No commit since baseline
(`git diff --stat 0872a20 HEAD` on owned paths EMPTY — both edits are working-tree
mods); cycle diff matches the Fix report (sets.py 2 ins / 16 del, test_sets.py 41
del).

**Dead-code re-confirmed at live source (independent grep, not trusted from
artifact):**
- `grep "_input_value\s*=" django_strawberry_framework/` → ZERO production
  writers. All production `_input_value` hits are substring matches inside the
  unrelated `normalize_input_value` symbol. Post-removal the lone test writer
  (`test_sets.py:464`, `instance._input_value = input_value`) is gone — the only
  remaining `_input_value` token in tests is `test_sets.py:428`, a
  `normalize_input_value` docstring substring, not the attribute. So the read at
  the removed `:460` had ZERO writers anywhere → guaranteed no-op, genuinely dead.
- `grep check_permissions` in `orders/` + `tests/orders/` → ZERO post-removal.
  Whole-package only the filter twin survives (`filters/sets.py:1290`, distinct
  signature with `requested_fields`, live django-filter form threading) — UNtouched
  by this cycle.
- **Live order gate UNTOUCHED:** `_run_permission_checks` is invoked as a
  classmethod with `input_value` passed as an ARGUMENT at `apply_sync`
  (`orders/sets.py:552`) and `apply_async` (`:591`, under `sync_to_async`), both
  pre-mutation. These lines sit in unchanged diff context. The removed bound
  method never fed this path. Removed code was NOT reachable → removal sound.

**Coverage-cliff check (no surviving production line lost its sole cover):** The
two removed tests built an OrderSet via `object.__new__(...)` and called the
now-removed bound `check_permissions`. Every OTHER production line they touched is
still covered by surviving siblings:
- OrderSet construction / metaclass / `OrderArgumentsFactory`: covered by
  `test_sets.py:272/277`, `:331/339/349` (dedup), `:430/435`, and dozens of
  `class X(OrderSet)` definitions.
- `_run_permission_checks` + per-field `check_*_permission` dispatch: covered live
  by `test_orderset_apply_async_runs_check_permission_in_sync_to_async` (`:300`,
  `check_title_permission` raises → propagates), the per-class dedup test (`:328`,
  `check_code_permission`/`check_shelf_permission` fire once via `apply_sync:356`),
  and `test_composition.py:215` (`BookOrder.apply_sync`).
- The two removed tests were the SOLE cover ONLY of the removed method body
  (former `:448-460`), which is gone with the method. **No surviving production
  line lost its only cover** — coverage does not regress.

Lows 1 (dependency-direction narrative canonization) and 2 (dual deferred Layer-6
surfaces) are forward-looking per Worker 1's own prose; no act-now edit, correctly
not implemented.

### DRY findings disposition

Both DRY items (shared relay field-guard/predicate home; cross-family Layer-6 cache
lift) are defer-with-trigger with explicit recorded triggers — no act-now
consolidation, correct. Confirmed.

### Sibling-cycle attribution

Owned-path diff stat is exactly this cycle's edit. The broader working-tree dirt
(filters/sets.py, types/*, optimizer/*, utils/connections.py, GLOSSARY, feedback*
deletes, etc.) attributes to closed sibling cycles / concurrent maintainer work
(AGENTS.md #33): e.g. `filters/sets.py` (+10/-6) is the `rev-filters__sets.md`
`get(form_key) or get(suffixed_key)` collapse Low (verified+[x]), NOT a
`check_permissions` change. None of it is owned by this project pass; the pass
authored only the orders/sets.py + test_sets.py removal.

### Temp test verification

None required — the verdict rests on independent grep (zero prod writers, zero
prod callers, live classmethod gate as unchanged context) plus the surviving-test
coverage inventory. No focused pytest run (per AGENTS.md / role; final-gate cycle
owns the suite). Orphan sweep confirmed: `object.__new__` now ZERO uses (builtin,
never imported → no dangling import); `HttpRequest` (7), `pytest` (13), factory +
model imports all still consumed. Module docstring edit accurate (names only the
live classmethod gate). Ruff format-check + check pass on owned paths (COM812
warning standing/expected). `git diff -- CHANGELOG.md` empty; `Not warranted`
disposition cites both AGENTS.md and plan silence, framing honest (internal
dead-code removal, no consumer-visible change).

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the
project-level pass checklist box (`review-0_0_9.md:128`).

---

## Comment/docstring pass

Folded into the consolidated logic pass — the only docstring touch (the module
docstring bullet's instance-method half) is intrinsic to the removal, not a
separate comment-contract decision, so there is no independent comment pass to
run.

### Files touched

- `django_strawberry_framework/orders/sets.py` module docstring — see Fix report
  (dropped the instance-method half of the permission-pipeline bullet).

### Per-finding dispositions

- Medium (`OrderSet.check_permissions` dead code): IMPLEMENTED — method + 2
  orphan tests + section comment + stale docstring line removed.
- Low 1 (dependency-direction narrative canonization): forward-looking per
  Worker 1's prose ("no act-now edit"; re-triage when a package-wide
  architecture/import-DAG doc is authored). No edit.
- Low 2 (dual deferred Layer-6 surfaces): recorded-for-awareness only, "no
  project-level action". No edit.

### Validation run

- `uv run ruff format .` — pass / no-changes.
- `uv run ruff check --fix .` — pass.

### Notes for Worker 3

Nothing beyond the Fix report.

---

## Changelog disposition

### State

`Not warranted`.

### Reason

The cycle's only edit is the removal of dead production code (a no-op bound
method, proven never to fire) plus its two false-coverage tests and a stale
docstring line. No consumer-visible behaviour changes — the live order
permission gate (the classmethod `_run_permission_checks` path) is unchanged, so
nothing a release note would describe. Per AGENTS.md ("Do not update
CHANGELOG.md unless explicitly instructed") AND the active plan's silence on
changelog authorization for this cycle, no edit is warranted. The project-pass
carve-out (a Medium recommending a CHANGELOG rename/drift sweep) does not apply —
this Medium recommends a code removal, not a CHANGELOG edit.

### What was done

No `CHANGELOG.md` edit.

### Validation run

- `uv run ruff format .` — pass / no-changes.
- `uv run ruff check --fix .` — pass.

---

## Iteration log
