# DRY review: `django_strawberry_framework/sets_mixins.py`

Status: verified

## System trace

`sets_mixins.py` is the package-root neutral home for machinery shared by the
`FilterSet` and `OrderSet` families (declared free of both `filters/` and
`orders/` so neither subpackage imports from the other). Six exports, three
responsibility groups:

- **Naming.** `ClassBasedTypeNameMixin.type_name_for()` -- the one rule that
  turns `cls.__name__` (+ optional field path) into a generated GraphQL type
  name. Consumed by `FilterSet` / `OrderSet` (which set it as a base and tune
  `_root_type_suffix` / `_field_type_suffix`), and called directly from
  `filters/inputs.py::_input_type_name_for` /
  `filters/inputs.py::_build_input_fields` (bag naming),
  `orders/inputs.py::_input_type_name_for`, and the shared
  `utils/inputs.py::GeneratedInputArgumentsFactory` (three call sites:
  `input_type_name`, the collision-check `target_name`, and the BFS-queue
  `type_name`). Every one of these routes through the mixin; none re-derives
  the PascalCase-suffix rule independently.
- **Lazy target resolution.** `LazyRelatedClassMixin.resolve_lazy_class` (str
  / callable / class -> class, with the two-attempt string import) and
  `RelatedSetTargetMixin` (the idempotent owner-bind + lazy `.filterset` /
  `.orderset` property built on top of it). Consumed by
  `filters/base.py::RelatedFilter` and `orders/base.py::RelatedOrder`, each
  supplying `_target_attr` / `_owner_attr` and a thin family-named
  `bind_<x>set` / `.{x}set` wrapper. `tests/orders/test_composition.py`
  asserts directly that both classes share the identical `LazyRelatedClassMixin`
  object in their MRO (not a parallel copy).
- **Declaration-lifecycle substrate.** `collect_related_declarations` (the
  metaclass collect-and-bind step, parameterized by `inherit_from_bases` since
  `FilterSetMetaclass` rides `django_filters`' own MRO merge while
  `OrderSetMetaclass` is a plain `type` metaclass that must copy base
  declarations manually), `expanded_once` (class-`__dict__` cache + reentry
  guard around `FilterSet.get_filters` / `OrderSet.get_fields`, with an
  optional `on_reentry` fallback the filter side uses for a self-referential
  `RelatedFilter` cycle and the order side does not need), `should_cache_expansion`
  (the two-condition cache-write gate: own-`__dict__` related map + every
  target resolved), and `SetLifecycleAttrs` (the `(owner, cache, guard)` attr-name
  triple each family declares once as `cls._lifecycle`, consumed by
  `utils/inputs.py::clear_generated_input_namespace` via `binding_attrs`
  instead of a re-spelled tuple at the reset call site).

Every one of these six exports already carries an explicit "single-sited /
0.0.9 DRY pass / `docs/feedback.md` Major 3 / DRY review A8" provenance note
in its own docstring -- this module IS the outcome of an earlier DRY pass that
found the filter/order byte-parallel copies and consolidated them here. The
question for this fresh review is whether that consolidation still holds
(no re-fork since) and whether anything NEW has drifted back into
byte-parallel duplication since.

## Verification

Traced every consumer of each export system-wide (not just the two set
families) to check for a third independent implementation of the same rule:

- **Naming.** Searched for every `.type_name_for(` call site and for any
  independent PascalCase-suffix construction near mutation/form/serializer
  input naming. `forms/sets.py` / `mutations/sets.py` have their own
  `<Name>Input` / `<Name>Payload` naming (`_form_input_type_name_for`,
  `build_payload_type`), but that is a **different responsibility** --
  mutation input/payload names derive from the mutation class name and
  operation kind, not from a filter/order field path, and have no
  `_root_type_suffix` / `_field_type_suffix` concept. Confirmed disjoint, not
  a candidate.
- **Lazy resolution.** Searched every `import_string` / dynamic-class-resolution
  site: `management/commands/_imports.py::import_string_or_command_error`
  translates failures to `CommandError` for CLI dotted-path args (no
  class-vs-callable-vs-string disambiguation, no bound-module fallback);
  `utils/imports.py`'s `import_attr_if_importable` / `loaded_attr` / `import_attr`
  family (explicitly documented as the owner for "reach into a module that
  may not be importable / may not be loaded", per its own module docstring)
  is `importlib.import_module` + `getattr`-based internal deferred-import
  plumbing, not a consumer-supplied lazy class reference. Neither shares
  `resolve_lazy_class`'s contract (str retried against `bound_class.__module__`,
  a bare callable invoked as a zero-arg factory, a class passed through).
  Confirmed disjoint.
- **Lifecycle reset.** Searched every `delattr(` site for a parallel
  class-attribute-reset pattern outside `SetLifecycleAttrs`. Found
  `types/finalizer.py`'s `_suppress_relation_list_form` /
  `_register_relation_connection_teardown` teardown pair, which does
  identity-checked removal of a synthesized relation-connection resolver
  field from a `DjangoType` -- a different lifecycle (per-field synthesis
  teardown, not per-set binding-state reset) with a different owner
  (`DjangoTypeDefinition.relation_connections`, not `_lifecycle`). Confirmed
  disjoint.
- **Reentry / caching.** Confirmed `expanded_once`'s class-level
  cache-and-guard skeleton is distinct from `mutations/sets.py::cached_build_input`
  / the `_shape_build_cache` family (a shape-keyed memoization dict guarding
  *input-class construction*, with no reentry concept) and from
  `forms/sets.py::_cached_build_form_input` (which rides the same
  `cached_build_input` primitive as the mutation side, already single-sited
  there, not here) -- different problems (recursive self-referential
  expansion vs. shape-identity memoization), correctly owned separately.
- **`collect_related_declarations`'s `inherit_from_bases` flag.** Considered
  whether this is the "mode flag reconciling different rules" DRY.md warns
  against. Rejected: the two branches are not an arbitrary switch over
  otherwise-identical behavior -- they encode a real, external, unavoidable
  difference between the two metaclasses' base classes (`django_filters.FilterSetMetaclass`
  performs its own MRO merge into `declared_filters`; the plain `type`
  metaclass performs none), so the flag *documents* a genuine variation
  rather than hiding one. Both call sites (`filters/sets.py`, `orders/sets.py`)
  pass a literal, and the shared tail (own-items override + diamond-tombstone
  reconciliation against direct-base precedence) is identical either way.
- Confirmed the target diff against `ITEM_BASELINE` (`87d227cd2afb3c8c1a54434bf6364c303968d00d`)
  is empty (`git diff <baseline> -- sets_mixins.py` produces no output); the
  file was dirty at dispatch only because that baseline snapshot itself
  carries an uncommitted docstring edit (module summary line, HEAD..baseline
  diff is exactly one line) from concurrent work, not drift introduced after
  dispatch. No overwrite risk for this review.

## Opportunities

None -- every export traced to exactly the two set-family call sites (or the
one shared `utils/inputs.py` factory / clear helper) its own docstring
already claims, and every structurally-similar-looking pattern found
elsewhere in the package (mutation/form input naming, CLI dotted-path
import, best-effort module import, relation-connection teardown, shape-keyed
build caches) was verified to encode a genuinely different contract with a
different owner and different reasons to change. This module is itself the
product of the package's `0.0.9` DRY pass (`docs/feedback.md` Major 3) plus
later single-sitings (DRY review A8, A9, D1); a fresh trace of every consumer
found no new fork and no new duplication that has crept back in since.

One documentation-accuracy note, out of DRY's scope to fix here: the module
docstring's title line has already been fixed to say "shared by the
`FilterSet` and `OrderSet` families" (present tense) -- that edit is now
committed to HEAD and the file is git-clean, so there is no concurrent
working-tree edit left to collide with. What remains stale is the
"future ``orders`` / ``aggregates`` / ``fieldsets``" wording still carried at
three sites -- the module docstring body (`sets_mixins.py #"the future"`), the
`ClassBasedTypeNameMixin` docstring
(`sets_mixins.py::ClassBasedTypeNameMixin #"reuse the exact same naming rule"`),
and the `type_name_for` docstring
(`sets_mixins.py::ClassBasedTypeNameMixin.type_name_for #"per-field naming"`) --
because `orders` has shipped and is now a live consumer (confirmed by
`orders/base.py` / `orders/sets.py` above), not a future subpackage. This is a
genuine source-doc staleness finding the DRY review records, but it is a
docstring-wording correction rather than a duplication finding, so it is left
for the file's next maintainer edit rather than folded into this DRY pass
(which makes no source change).

## Judgment

Zero-edit. `sets_mixins.py` is the correctly-scoped single owner for the
naming, lazy-target-resolution, and declaration-lifecycle rules the
`FilterSet` / `OrderSet` families share; no new duplication was found either
inside the two set families or against any other subsystem. No tracked
change is needed; the item-scoped diff against `ITEM_BASELINE` remains empty
(no edits made this pass).

## Implementation (Worker 1)

No changes. Every candidate considered above was verified disjoint from the
target's owned responsibilities (different contract, different owner, or
already single-sited at a different, correct location). The
docstring-title fix is now committed to HEAD and the file is git-clean, so
there is no concurrent working-tree edit to preserve or collide with; this
review adds no edits to the file.

- **Paths edited:** none (this artifact only).
- **Strongest rejected candidates:** the `forms/sets.py` mutation/payload
  naming helpers (disjoint responsibility from `type_name_for`); the CLI
  `import_string_or_command_error` / `utils/imports.py` best-effort-import
  family (disjoint contract from `resolve_lazy_class`); `types/finalizer.py`'s
  relation-connection teardown `delattr` pair (disjoint lifecycle from
  `SetLifecycleAttrs`); `collect_related_declarations`'s `inherit_from_bases`
  parameter (a genuine-variation parameterization, not a duplication-hiding
  mode flag).
- **Changelog:** not warranted (zero-edit).
- Ran no formatting/lint commands -- no source edits were made.

## Independent verification (Worker 2)

Re-traced independently rather than reviewing only the artifact's claims.

- **Scoped diff.** `git diff 87d227cd2afb3c8c1a54434bf6364c303968d00d -- \`
  `django_strawberry_framework/sets_mixins.py` is empty -- confirmed. The
  one-line module-docstring title change ("shared across the FilterSet /
  OrderSet / AggregateSet family" -> "shared by the `FilterSet` and
  `OrderSet` families") is now committed to HEAD, so `git diff HEAD --
  sets_mixins.py` is also empty and the file is git-clean -- there is no
  concurrent working-tree edit left to reconcile or collide with, and the
  earlier "concurrent dirty = baseline" framing no longer applies. No edit was
  made or needed to reconcile it.
- **Naming.** Re-grepped every `type_name_for(` call site
  (`filters/inputs.py`, `orders/inputs.py`, `utils/inputs.py`) -- all three
  route through the mixin as claimed. Independently checked the one
  near-miss the artifact's own grep would surface:
  `forms/sets.py::_form_input_type_name_for` matches the search string
  `type_name_for` as a substring only; it is a private module-level function
  keyed on `(meta, operation_kind)` with no `_root_type_suffix` /
  `_field_type_suffix` concept and no relationship to
  `ClassBasedTypeNameMixin` -- confirmed disjoint, not a missed call site.
- **Lazy resolution.** Confirmed `filters/base.py::RelatedFilter` and
  `orders/base.py::RelatedOrder` both inherit `RelatedSetTargetMixin` and
  supply only `_target_attr` / `_owner_attr` (`("_filterset",
  "bound_filterset")` vs. `("_orderset", "bound_orderset")`) plus a
  thin family-named wrapper -- no independent re-implementation in either
  file. Read `tests/orders/test_composition.py`'s
  `test_lazy_related_class_mixin_is_shared_not_duplicated` and confirmed it
  asserts object identity (`filter_mixin is order_mixin is
  LazyRelatedClassMixin`), not just a name/behavior match -- a real
  regression guard against exactly the byte-parallel re-fork this module
  exists to prevent. Independently checked
  `management/commands/_imports.py::import_string_or_command_error` (raises
  `CommandError` for a dotted path with no module separator; no
  string-retry-against-a-bound-module, no callable/class branch) --
  confirmed disjoint from `resolve_lazy_class`'s three-way dispatch.
- **Lifecycle.** Confirmed `filters/sets.py` and `orders/sets.py` each
  declare exactly one `SetLifecycleAttrs` instance as `cls._lifecycle`, and
  that `utils/inputs.py::clear_generated_input_namespace` reads
  `set_root._lifecycle.binding_attrs` rather than a re-spelled tuple.
  Confirmed both `get_filters` / `get_fields` route through the same
  `expanded_once` skeleton with matching `cache_attr` / `guard_attr` drawn
  from `_lifecycle`, and both `should_cache_expansion` call sites pass the
  matching `related_attr` / `target_slot` pair for their family. Confirmed
  `collect_related_declarations`'s `inherit_from_bases` literal at each call
  site (`filters/sets.py` passes `False` + `class_items` +
  `base_declarations_attr="declared_filters"`; `orders/sets.py` passes
  `True` with no override) matches the docstring's stated rationale for the
  upstream-metaclass-MRO-merge asymmetry -- not an arbitrary mode flag.
- **Independent search for a missed consolidation.** Grepped for any
  `AggregateSet` / `FieldSet` implementation that might have landed and
  duplicated this machinery instead of consuming it: none exists yet (the
  one `FieldSet` hit, in `types/definition.py`'s `fields_class` docstring,
  is a forward-reserved slot for a not-yet-built card, consistent with
  `sets_mixins.py`'s own "future subpackages" docstring language --
  no production duplication to find). Grepped every `pascal_case_or_raise` /
  `pascal_case` call site package-wide; all route through the single
  `utils/strings.py` primitive already, so there is no PascalCase-suffix
  logic anywhere that reimplements `type_name_for` instead of calling it.
  Re-checked `types/finalizer.py`'s only mention of
  `LazyRelatedClassMixin` -- a docstring note about rewrapping the
  `ImportError` `resolve_lazy_class` can raise, not a second
  implementation.
- **Challenged rejected candidates.** Tried to argue each rejection back
  into scope and could not: `_form_input_type_name_for` differs on both
  input shape (mutation operation kind, not filter/order field path) and
  suffix policy (no `_root_type_suffix` distinction at all), so merging it
  into `ClassBasedTypeNameMixin` would force a mode flag onto the mixin for
  no shared benefit; `import_string_or_command_error` differs on error
  channel (`CommandError` for a CLI operator, not `ConfigurationError` /
  bare `ImportError` for a class-reference consumer) and has no
  bound-module retry, so folding it into `resolve_lazy_class` would need a
  parameter threading a different exception type through a class-resolution
  contract; `types/finalizer.py`'s relation-connection `delattr` pair
  resets a per-field synthesized-resolver attribute keyed on identity
  checks against `DjangoTypeDefinition.relation_connections`, an entirely
  different owner and cardinality than `SetLifecycleAttrs`'s fixed
  three-attribute per-set-class tuple. All three rejections hold.

No missed consolidation opportunity found; every consumer traced matches
the artifact's account exactly, the scoped diff is empty, and the
zero-edit judgment is independently reproducible.

**Status: verified**
