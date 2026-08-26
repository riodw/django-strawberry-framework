# DRY review: `django_strawberry_framework/sets_mixins.py`

Status: verified

## System trace

The module is the neutral home for the machinery the ``FilterSet`` / ``OrderSet``
families would otherwise copy from each other:

- ``ClassBasedTypeNameMixin.type_name_for`` -- the class-derived GraphQL input-naming
  rule (root + per-field suffixes), shared by both families via
  ``utils/inputs.py::set_input_type_name`` and the operator-bag naming;
  ``utils.strings.pascal_case_or_raise`` carries the conversion + guard it delegates to.
- ``LazyRelatedClassMixin.resolve_lazy_class`` -- string/callable/class target
  resolution; consumed by ``filters/base.py::RelatedFilter`` and
  ``orders/base.py::RelatedOrder`` through ``RelatedSetTargetMixin``.
- ``RelatedSetTargetMixin`` -- idempotent owner-bind (``_bind_owner``) + lazy
  target resolution (``_resolved_target`` / ``_set_target``); the family classes keep
  only zero-logic thin wrappers (``bind_filterset`` / ``.filterset`` vs
  ``bind_orderset`` / ``.orderset``).
- ``collect_related_declarations`` -- the metaclass collect-and-bind step both
  ``filters/sets.py::FilterSetMetaclass`` and ``orders/sets.py::OrderSetMetaclass``
  run, parameterized by collection attr / MRO-merge policy / tombstone reconciliation.
- ``expanded_once`` + ``should_cache_expansion`` -- the class-level expansion cache +
  reentry-guard skeleton and two-condition cache-write gate behind
  ``FilterSet.get_filters`` and ``OrderSet.get_fields``; ``SetLifecycleAttrs.binding_attrs``
  names the reset slots ``utils/inputs.py::clear_generated_input_namespace`` wipes on
  ``registry.clear()``.
- ``ActiveInputPermissionMixin`` + ``ActiveInputPermissionAttrs`` -- the spec-027/028
  Decision-8 permission facade over the mechanics in ``utils/permissions.py``, fed by
  the traversal substrate ``utils/input_values.py`` (``iter_active_fields`` /
``is_inactive_value`` / ``SetInputTraversal``).

Lockstep surfaces: a new set family declares suffixes, ``_lifecycle``, ``_permission``,
and a metaclass calling the shared collector; ``registry.clear()`` resets binding state
through whatever ``_lifecycle`` names. Nothing outside these declarations needs to move.

## Verification

Axis discharge (all five):

1. **Cross-flavor policy mirroring** — searched: ``grep -rn '"related_filters"|"
   "related_orders"'`` across the package mapped every per-family spelling (metaclass
   ``collection_attr``, ``should_cache_expansion(related_attr=...)``, ``_permission
   .related_attr``, normalizer traversal configs, factory ``_related_attr``, finalizer
   owner-binding kwargs). Metaclass remainders after ``collect_related_declarations``
   are genuinely distinct (only the filter side reconciles django-filter's
   ``declared_filters`` and rebuilds ``base_filters``). **Found**: each family stated
   its active-input grammar TWICE — once on ``_permission`` and once in the
   normalizer's ``SetInputTraversal`` construction
   (``filters/sets.py::_NORMALIZE_TRAVERSAL`` module singleton;
   ``orders/inputs.py::normalize_input_value`` inline config) — the exact remainder
   this module exists to prevent. Implemented, see Opportunities.
2. **Sync and async twins** — ruled inapplicable on the target's surface: the module
   contains no ``async`` code and no paired implementations split by an await boundary;
   the facade's async safety is single-sited (both families' ``apply_async`` wrap the
   SAME sync ``_run_permission_checks`` via
   ``utils/querysets.py::run_in_one_sync_boundary``).
3. **Derived rather than repeated knowledge** — searched naming/provenance derivations:
   ``type_name_for`` and ``filters/inputs.py::_pascal_case`` both delegate to the one
   ``pascal_case_or_raise``; ``binding_attrs`` derives its tuple from declared fields;
   ``filters/sets.py::_FORM_KEY_BY_PYTHON_ATTR`` derives once at import. **Found** the
   inverse case: the normalizer configs RE-DERIVED the facts ``_permission`` already
   declares (same finding as axis 1). Fixed.
4. **Inverse and round-trip pairs** — ruled inapplicable: the target owns no
   encode/decode grammar. ``resolve_lazy_class`` is one-directional (string -> class,
   no inverse anywhere). The own-``__dict__`` isolation rule appears as three one-line
   applications (``expanded_once`` read, ``should_cache_expansion``, filter-side
   snapshot accessor) — extracting a helper would obscure a self-documenting rule;
   rejected.
5. **Contracts restated in another medium** — searched GLOSSARY/TREE/docstrings:
   ``docs/GLOSSARY.md``'s ``RelatedOrder`` entry matches ``resolve_lazy_class``'s actual
   fallback contract. **Found**: four docstring sites
   (``utils/input_values.py::is_inactive_value``, ``utils/input_values.py::
   SetInputTraversal.unset_sentinel``, ``utils/permissions.py`` module docstring,
   ``utils/permissions.py::extract_branch_value``) claimed the order side leaves
   ``unset_sentinel=None``, while both order-side call sites pass
   ``strawberry.UNSET`` (defensive; generated order inputs default to ``None`` so the
   arm is inert). Prose had drifted from code; corrected in the same change.

Single-edit-site counts (posited changes):

- *"The order family stops treating ``UNSET`` as an inactive value."* Before the full
  fix: THREE production sites moved together
  (``orders/inputs.py::normalize_input_value``'s config,
  ``orders/inputs.py::_ensure_field_specs._has_active_fields``,
  ``orders/sets.py::OrderSet._permission.unset_sentinel``) plus the four stale prose
  sites. After: ONE site (``OrderSet._permission``). The initial consolidation missed
  ``_has_active_fields``; the revision pass closed it (see Iterations).
- *"Re-binding a related declaration to a divergent owner should raise instead of
  no-op."* ONE site (``RelatedSetTargetMixin._bind_owner``); the eight wrapper lines in
  ``RelatedFilter`` / ``RelatedOrder`` stay untouched — count 1 proves they are surface
  preservation, not duplicated responsibility (strongest rejected candidate).
- *"Add an ``AggregateSet`` third family."* Zero edits to shipped families or this
  module; new declarations only — the extension seam works.

Rejected candidates kept separate: metaclass bodies (filter-side django-filter
reconciliation has no order analogue); ``apply_sync`` / ``apply_async`` pipelines
(family-owned by pinned contract); ``SetLifecycleAttrs`` extended with
``related_attr`` / ``target_attr`` (lifecycle-reset slots and traversal-grammar names
have different consumers; merging widens the descriptor's charter without removing a
site).

Scratch experiment: ``docs/dry/temp-tests/sets_mixins/probe_real_pipeline.py``
(``DJANGO_SETTINGS_MODULE=config.settings PYTHONPATH=examples/fakeshop uv run python
docs/dry/temp-tests/sets_mixins/probe_real_pipeline.py``) executed live
``schema.execute_sync`` filter + orderBy queries through BOTH changed normalizer paths
and fired a gate through the shared facade — all passed.

## Opportunities

### Family active-input grammar was declared twice per family (fixed)

- **Repeated responsibility:** one fact — the grammar that decides which supplied input
  fields are leaf / related / logic and what counts as unsupplied (``field_specs``,
  ``related_attr``, ``logic_keys``, ``unset_sentinel``, ``handle_top_level_list``) —
  must classify IDENTICALLY in the apply pipeline and the permission walk (a divergence
  is a field filtered without its gate), yet each family spelled it once for permissions
  (``_permission``) and once more for normalization.
- **Sites:** ``filters/sets.py`` module singleton ``_NORMALIZE_TRAVERSAL`` +
  ``FilterSet._permission``; ``orders/inputs.py::normalize_input_value`` inline config +
  ``OrderSet._permission``. Prose restatements: the four stale sentinel docstrings above.
- **Evidence:** the posited sentinel change forced two production sites on the
  filter family and three on the order family before the fix (counts above); the
  twin objects agreed today only by discipline, and the prose already had drifted.
- **Owner:** ``sets_mixins.ActiveInputPermissionMixin._input_traversal`` (new) — the one
  translation of the declared ``_permission`` grammar into the ``SetInputTraversal``
  shape ``utils.input_values.iter_active_fields`` consumes; both normalizers and the
  permission walkers classify through it.
- **Consolidation:** deleted the filter module singleton and the order inline config;
  ``FilterSet._normalize_input`` now passes ``cls._input_traversal()``,
  ``normalize_input_value`` passes ``orderset_cls._input_traversal()``. Values still
  flow by reference (``field_specs`` stays the map the family ``inputs`` module mutates
  in place). ``ActiveInputPermissionAttrs`` keeps its exploded, self-documenting shape.
- **Proof:** permanent tests in ``tests/test_sets_mixins.py``:
  ``test_family_input_traversal_is_derived_from_the_permission_config`` (values +
  ``field_specs`` identity for both families),
  ``test_order_normalizer_consumes_the_family_permission_traversal`` (spy proves the
  normalizer receives the DERIVED config, sentinel identity included),
  ``test_filter_normalizer_has_no_parallel_module_traversal`` (blocks reintroducing the
  twin). Plus the scratch live-pipeline probe above. Deferred: ``uv run pytest`` (not
  authorized for this item).
- **Risks / non-goals:** the per-request ``SetInputTraversal`` construction replaces a
  module singleton (frozen 5-slot dataclass; negligible, and the singleton's real
  invariant — by-reference ``field_specs`` — is preserved and now pinned);
  ``factories.py::_related_attr`` and the finalizer's ``related_attr=`` literals name
  the public collection attribute where each consumes it and are out of scope;
  ``ActiveInputPermissionAttrs``' public shape is deliberately unchanged.

## Judgment

``sets_mixins`` had already absorbed the expensive duplication (naming, lazy targets,
metaclass collection, expansion lifecycle, permission facade); what remained was one
quiet twin per family — the normalizer re-stating the grammar ``_permission`` declares —
plus prose that had drifted from the shipped sentinel configuration. Both are now
single-sited at the mixin and pinned by tests; every probing axis was searched or ruled
out against the target's real surface, and the rejected candidates (thin family
wrappers, ``__dict__`` isolation applications, metaclass remainders, family pipelines)
are independent by counted evidence, not by resemblance. Concurrent mid-task additions
to ``tests/test_sets_mixins.py`` (two new tests using the exploded attrs shape) were
left intact — the chosen owner shape required no change to them.

## Implementation (Worker 1)

Tracked edits (baseline ``560641152f85e972d1789d86f4e9142e95b1f7aa``; concurrent dirty
files elsewhere untouched):

- ``django_strawberry_framework/sets_mixins.py`` — add
  ``ActiveInputPermissionMixin._input_traversal`` deriving the canonical
  ``SetInputTraversal`` from ``_permission``; import ``SetInputTraversal``.
- ``django_strawberry_framework/filters/sets.py`` — delete the ``_NORMALIZE_TRAVERSAL``
  singleton; ``FilterSet._normalize_input`` uses ``cls._input_traversal()``; drop the
  now-unused ``SetInputTraversal`` import.
- ``django_strawberry_framework/orders/inputs.py`` — ``normalize_input_value`` uses
  ``orderset_cls._input_traversal()``; drop the inline config and unused import;
  docstring points at the family declaration.
- ``django_strawberry_framework/utils/input_values.py`` /
  ``django_strawberry_framework/utils/permissions.py`` — correct the four stale
  "order side leaves it ``None``" sentinel claims to the shipped behavior.
- ``tests/test_sets_mixins.py`` — three new permanent tests (above); existing pins
  untouched and still valid.

Post-edit hygiene run: ``uv run ruff format .`` / ``uv run ruff check --fix .`` /
``scripts/check_trailing_commas.py`` — clean. ``uv run pytest`` deferred per cycle rules.

## Independent verification (Worker 2)

Verdict: **revision-needed** — the implemented consolidation itself verifies (equivalence,
ownership, tests, docstring fix all independently confirmed), but the sentinel
single-edit-site count does not survive recount: one production site still re-states the
declared grammar and is unrecorded.

Diff attribution (baseline ``5606411``): every hunk in the six scoped files belongs to this
item except two concurrent tests in ``tests/test_sets_mixins.py``
(``test_collect_related_declarations_base_declarations_precedence``,
``test_active_input_permission_mixin_field_paths_and_branches`` — exploded-attrs additions,
correctly left intact). Other dirty paths (``schema.py``, ``GLOSSARY.md``, scripts, DBs) are
out-of-scope concurrent work.

Independently proved:

- **Equivalence both families.** Reconstructed both baseline configs verbatim from the diff;
  frozen-dataclass equality against ``cls._input_traversal()`` holds field-by-field for
  ``FilterSet`` and ``OrderSet``, with ``field_specs`` by-reference identity. Defaults line up:
  filter side omits ``handle_top_level_list`` on both old and new paths (``False`` via dataclass
  defaults; ``ActiveInputPermissionAttrs`` and ``SetInputTraversal`` defaults match);
  order side's derived ``logic_keys=frozenset()`` equals the old omitted-kwarg default.
- **Caching semantics.** The baseline singleton had exactly ONE consumer
  (``filters/sets.py`` ``_normalize_input``). Its real invariant — by-reference ``field_specs``
  that ``inputs.py`` mutates in place — is preserved because nothing rebinds ``_field_specs``
  anywhere in the package (swept) and ``_permission.field_specs`` binds that same imported dict.
  Per-apply cost is one frozen 5-slot dataclass construction; no behavioral caching lost.
- **Consumption.** Spy over the REAL entry points with real fakeshop classes
  (``ItemFilter._normalize_input``, ``orders.inputs.normalize_input_value(ItemOrder, ...)``)
  captured configs equal to the family derivation with sentinel identity. Permission walkers
  consume ``_permission`` directly through the mixin's thin delegates;
  ``utils/permissions.py::active_permission_targets`` assembles its config from caller kwargs,
  never literals — declaration → walker and declaration → normalizer are single-sourced.
- **Live pipeline** (read-only, existing rows): ``schema.execute_sync`` filter + ``orderBy``
  queries resolve correctly through the new derivation.
- **Docstring fix accurate**: generated order leaves are ``Ordering | None``
  (``orders/inputs.py::convert_order_field_to_input_annotation``), so "defaults to ``None``" is
  true, and both order-side sentinel consumers receive ``UNSET`` only via
  ``OrderSet._permission.unset_sentinel``. Four prose sites fixed = four diff hunks across the
  two utils files.
- **Tests at the right tier**: these pins (derivation values + identity, consumption spy,
  twin-absence) have no HTTP expression; behavior equivalence is already covered end-to-end by
  the live-query suites. The stub-family spy pins derivation-from-``_permission`` generically
  because ONE mixin implementation serves both families. Existing pins untouched and valid.
- **Rejected candidates re-probed**: wrappers remain zero-logic over ``_bind_owner``
  (count 1 confirmed, ``sets_mixins.py:190-193``); ``__dict__`` applications self-contained
  (``expanded_once`` read / guard / ``should_cache_expansion``); metaclass remainders genuinely
  distinct (filter-only django-filter reconciliation).

Why revision-needed:

- ``orders/inputs.py::normalize_input_value``'s local helper
  ``_ensure_field_specs._has_active_fields`` re-states the declared grammar twice more:
  hardcoded ``unset_sentinel=strawberry.UNSET`` at two expressions plus a manual
  ``isinstance(value, list)`` recursion mirroring ``handle_top_level_list=True``. It is NOT a
  leaf wire-format defense like ``filters/inputs.py:582/770/772`` (those guard per-value
  coercion inside the family-owned pipeline and are correctly distinct; the filter side also
  has no warm-up analogue — specs build eagerly at finalize). It answers the classifier's own
  question ("is anything supplied?") and must agree exactly: a miss skips spec building and the
  normalizer silently discards active fields while gates still fire — the exact divergence this
  finding's Evidence section names.
- Reachable today, not only under the posited change: ``_permission`` is a documented per-class
  declaration; a consumer subclass overriding ``_permission.unset_sentinel`` gets normalizer +
  walker classification from the override but warm-up gating from the hardcoded ``UNSET``.
- Recount of *"the order family stops treating UNSET as an inactive value"*: before THREE
  production sites (inline normalizer config + ``OrderSet._permission`` + ``_has_active_fields``),
  after TWO — not "ONE" as recorded. Root fix is small: derive sentinel and list-shape truth from
  ``orderset_cls._permission`` inside ``_ensure_field_specs`` (safe: any class reaching
  ``normalize_input_value`` carries ``_permission``), or record the remainder as a rejected
  candidate with a boundary argument that survives the subclass-override case; either way the
  artifact's count must be corrected.
- Matrix remains discharged on real evidence (no async in the module; no round-trip pair;
  GLOSSARY entry matches the lazy-target fallback; axes 1/3 findings fixed; axis 5 prose now
  accurate). The review was deep — this is an evidence-precision defect plus one unnamed
  remainder candidate, not a shallow search.

Scratch probe: ``docs/dry/temp-tests/sets_mixins/w2_equiv_probe.py``
(``DJANGO_SETTINGS_MODULE=config.settings PYTHONPATH=examples/fakeshop uv run python
docs/dry/temp-tests/sets_mixins/w2_equiv_probe.py``) — baseline-reconstruction equality,
consumption spies, live pipeline: all passed. ``uv run pytest`` deferred per cycle rules.

### Re-verification pass (Worker 2)

Verdict: **verified**. The revision closes the defect; every check re-run independently.

- **Fix confirmed.** ``orders/inputs.py::_ensure_field_specs`` derives its warm-up gate
  from ``orderset_cls._input_traversal()`` via
  ``any(utils.input_values.iter_active_fields(...))`` — the hardcoded sentinel AND the
  hand-rolled list flatten are both gone; the only remaining ``strawberry.UNSET``
  strings in the file are this history's docstring.
- **Independent recount** (every ``strawberry.UNSET`` / ``unset_sentinel`` hit in
  ``django_strawberry_framework/`` classified): *"the order family stops treating
  UNSET as an inactive value"* is now exactly **ONE** site —
  ``orders/sets.py::OrderSet._permission`` (``unset_sentinel=UNSET``). Everything else
  is either declaration-consuming mechanics (``sets_mixins.ActiveInputPermissionMixin
  ._input_traversal``, ``sets_mixins.py::_extract_branch_value`` /
  ``_iter_active_related_branches``, ``utils/input_values.py::is_inactive_value`` /
  ``iter_active_fields``, ``utils/permissions.py`` walkers — all parameterized, no
  literals) or out of scope: filter-family leaf wire-format defenses
  (``filters/inputs.py::normalize_input_value`` #"single defensive line",
  range-axis patch skips, ``filters/sets.py`` logic-branch / shape-validator /
  operator-bag-partial-supply / defensive-identity guards — per-value or per-branch
  arms inside family-owned pipelines, not grammar restatements; same class my first
  verdict already blessed), resolver-argument arity at the GraphQL boundary
  (``utils/connections.py`` / ``connection.py`` before/after/first/last/filter/
  order_by suppliedness — Strawberry's own omitted-arg convention), the shared
  generated-input omittability default and mutation ``UNSET`` strip
  (``utils/inputs.py``), the write/mutation pipelines (``auth/mutations.py``,
  ``forms/``, ``rest_framework/``), and unrelated module-local cache markers
  (``registry.py::GLOBALID_SETTING_UNSET``, ``conf.py::_LIVE_UNSET``). No violation
  remains. Filter-family declaration count stays ONE (``filters/sets.py::
  FilterSet._permission``).
- **Test critique.** ``tests/orders/test_inputs.py::
  test_ensure_field_specs_derives_the_unset_sentinel_from_the_family_declaration``
  proves override divergence end-to-end in three legs: (1) a field valued with the
  overridden marker normalizes to ``[]`` and fires NO gate — gate, normalizer, and
  walker share one classification; (2) on a fresh ledger, a ``UNSET``-valued field —
  invisible to the old hardcoded gate — raises ``ConfigurationError`` ("invalid order
  direction"), which simultaneously proves the warm-up gate classified it SUPPLIED,
  specs were built (leaf validation needs ``field.spec.django_source_path``), and the
  leaf layer refuses loudly instead of the silent ``spec is None`` discard; (3)
  ``_run_permission_checks`` on the identical input fires ``check_title_permission``
  — apply/gate agreement. Re-hardcode failure mode verified by trace: leg 2 would
  return ``[]`` with no exception, failing ``pytest.raises``. Tier correct
  (sentinel-overriding subclass unreachable from real fakeshop queries); imports and
  namespace hygiene consistent with sibling tests.
- **Equivalence holds.** Both families still declare ``unset_sentinel=UNSET``
  (``orders/sets.py::OrderSet._permission``, ``filters/sets.py::FilterSet._permission``);
  for every shipped input shape the derived walk answers the old helper's question
  identically. The only observable delta is malformed-direct-call error TIMING
  (warm-up raises one statement earlier; same type/message from both entry points).
  No shipped-behavior change.
- **Artifact accuracy.** Verification bullet (THREE → ONE with the missed-site note),
  Opportunities Evidence line, and Iteration 2's counts (order THREE → ONE; filter
  TWO → ONE) match code reality as recounted above.

``uv run pytest`` deferred per cycle rules.

## Iterations

### Iteration 2 (revision pass, Worker 1)

- **Defect (Worker 2 verdict):** the recorded sentinel single-edit-site count failed
  recount. ``orders/inputs.py::normalize_input_value``'s inner helper
  ``_ensure_field_specs._has_active_fields`` hardcoded
  ``unset_sentinel=strawberry.UNSET`` at two expressions and manually mirrored the
  ``handle_top_level_list`` flattening to answer the classifier's own "is anything
  supplied?" question. The divergence was reachable TODAY, not only under the posited
  change: a consumer subclass overriding ``_permission.unset_sentinel`` got
  normalizer + walker classification from the override while this warm-up gate kept
  the hardcoded sentinel, so a miss skipped spec building, the normalizer silently
  discarded the fields (the ``spec is None`` skip), and the permission gates still
  fired. Recount confirmed: THREE production sites before the consolidation (inline
  normalizer config + ``OrderSet._permission`` + ``_has_active_fields``), TWO after —
  not one.
- **Root cause and fix:** the warm-up gate re-stated the declared grammar beside the
  classifier instead of asking the classifier. Fixed at the true owner,
  ``orders/inputs.py::_ensure_field_specs``: it now derives EVERY grammar fact it
  needs from the family's own declaration via ``orderset_cls._input_traversal()`` by
  running the SAME ``utils.input_values.iter_active_fields`` walk the normalizer and
  permission walkers run; the mirrored mini-walk is deleted entirely (both the
  hardcoded sentinel AND the hand-rolled list flatten). Any class reaching
  ``normalize_input_value`` already evaluates ``_input_traversal()`` on its next
  statement, so no new requirement is introduced.
- **Equivalence per family:** both shipped families declare
  ``unset_sentinel=UNSET`` (filter side omits ``handle_top_level_list``, order side
  sets it ``True``), so the derived walk answers the old helper's question
  identically for every input shape: whole-input inactive, top-level list flattening
  with inactive-element skips, dict/dataclass walk, non-walkable inputs (nothing
  supplied), and short-circuit on first active field. The only observable delta is
  error TIMING for malformed direct-call inputs (e.g. a scalar list element): the
  classifier's ``ConfigurationError`` now surfaces during warm-up instead of one
  statement later — same exception type and message from both entry points
  (``normalize_input_value`` and ``_run_permission_checks``), because both
  immediately run the identical classifier walk. Subclass-override divergence is the
  only semantic change, and it moves toward apply/gate agreement.
- **Permanent test:** ``tests/orders/test_inputs.py::
  test_ensure_field_specs_derives_the_unset_sentinel_from_the_family_declaration``
  (package tier — a sentinel-overriding subclass is unreachable from any real
  fakeshop query) — a family whose ``_permission.unset_sentinel`` is overridden via
  ``dataclasses.replace(OrderSet._permission, ...)`` is honored end-to-end: the
  overridden marker normalizes as unsupplied (and fires no gate); a
  ``UNSET``-valued field — invisible to the old hardcoded gate — is classified
  SUPPLIED: specs are built, the leaf layer refuses the non-direction loudly
  (``ConfigurationError``), and ``check_title_permission`` fires for the same
  input. Existing pins re-checked and intact: the three consolidation pins in
  ``tests/test_sets_mixins.py`` (derivation values + ``field_specs`` identity, the
  consumption spy — whose stub family flows through the new warm-up unchanged — and
  twin absence) plus every order-side sentinel/list-shape pin in
  ``tests/orders/test_inputs.py`` (``UNSET`` / ``None`` / list / mapping shapes
  behave exactly as before).
- **Counts recorded:** *"The order family stops treating ``UNSET`` as an inactive
  value"*: before THREE production sites (inline normalizer config +
  ``OrderSet._permission`` + ``_ensure_field_specs._has_active_fields``), after ONE
  (``OrderSet._permission``). Filter-family count unchanged at TWO before /
  ONE after (no warm-up analogue). The Verification bullet and the Opportunities
  Evidence line are corrected accordingly; prior sections stand unaltered otherwise.
- **Hygiene:** ``uv run ruff format .`` / ``uv run ruff check --fix .`` /
  ``scripts/check_trailing_commas.py`` clean. Status set to fix-implemented;
  re-verification left open for Worker 2.
