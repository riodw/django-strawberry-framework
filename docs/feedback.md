# Feedback

Review target: `docs/spec-029-consumer_dx_cleanup-0_0_9.md`.

## Findings

### P1 - Slice 1's sweep inventory and validation gate are wrong

The spec's Current state and Slice 1 plan list only a small subset of current
`extensions=[DjangoOptimizerExtension()]` schema-construction sites, but the repo has many more
instance-form `extensions=` calls under `tests/optimizer/test_extension.py`,
`tests/optimizer/test_field_meta.py`, `examples/fakeshop/test_query/test_multi_db.py`,
`examples/fakeshop/test_query/README.md`, and examples/prose in
`django_strawberry_framework/optimizer/extension.py`. As written, a maintainer following the
file list in the implementation table will leave deprecated construction sites behind.

The proposed `grep -rn "DjangoOptimizerExtension()" .` gate is also not valid as a pass/fail
condition. It catches legitimate direct extension instantiation in optimizer unit tests, historical
CHANGELOG/spec prose, and the new spec's own before/after examples. The root-cause fix is to make
the slice target "all `DjangoOptimizerExtension()` calls that occur as elements of a
`strawberry.Schema(..., extensions=[...])` argument" and validate that with either an AST check or a
tighter grep pattern scoped to active source/docs. Direct calls such as
`DjangoOptimizerExtension().plan_relation(...)` and `ext = DjangoOptimizerExtension()` should remain
legal.

Affected spec sections: Current state, Decision 3, Slice 1 test plan, Definition of done.

### P1 - `inspect_django_type` finalized-state semantics are incorrect

The spec repeatedly treats absence of `__django_strawberry_definition__` as the unfinalized
`DjangoType` state. That is not how the package works. `DjangoType.__init_subclass__` assigns
`cls.__django_strawberry_definition__` immediately after registration, before
`finalize_django_types()` runs. Finalization is represented by
`DjangoTypeDefinition.finalized`, which flips inside
`django_strawberry_framework/types/finalizer.py::finalize_django_types`.

This matters for command behavior and tests. A concrete but unfinalized `DjangoType` will have a
definition object with `finalized is False`; an abstract/intermediate subclass with no `Meta` may
have no definition at all. Those should be two distinct error branches. The spec should replace the
"unfinalized means no `__django_strawberry_definition__`" language with an explicit
`definition is None` vs. `not definition.finalized` contract and add tests for both if both are
consumer-visible.

Affected spec sections: Decision 4, Edge cases, Slice 2 test plan, Definition of done.

### P1 - The inspect command cannot produce its promised table from `DjangoTypeDefinition` alone

The output contract says the command walks `DjangoTypeDefinition` / `FieldMeta` and prints the
resolved GraphQL type, nullability, and converter row. The current definition does not store the
synthesized annotation or the converter branch that produced it. After Slice 3, the spec also says
overrides are not persisted on `DjangoTypeDefinition`, yet the command must report post-override
nullability. Re-running `convert_scalar(field, type_name)` from the command will reproduce the
column-native nullability, not a `Meta.nullable_overrides` / `Meta.required_overrides` result, unless
the command separately reads the finalized annotation.

The spec needs to choose and pin a real read source. Viable high-quality options are:

- Read `definition.origin.__annotations__` after finalization for the authoritative resolved
  annotation, and use `selected_fields` / `field_map` only for Django-side metadata and converter
  classification.
- Persist normalized per-field conversion metadata on `DjangoTypeDefinition` during construction
  if the command truly must be a pure-definition reader.

Without that choice, the inspect command will be wrong for Slice 3 overrides and for
consumer-authored fields whose annotations bypass `convert_scalar`.

Affected spec sections: Decision 4, Decision 7, Non-goals, Edge cases, Slice 2 test plan.

### P1 - Slice 3's validation data flow is not implementable as written

Decision 8 proposes `_validate_nullability_overrides(meta, selected_names, consumer_authored_fields,
model)` and says it is called from `_validate_meta` / the field-selection pass. Current
`_validate_meta` runs before `_select_fields`, before `consumer_authored_fields` exists, and before
Relay primary-key suppression is known. The helper signature depends on values that are not
available at `_validate_meta` time.

The spec should split the flow:

- `_validate_meta` shape-checks and normalizes the two override declarations into
  `_ValidatedMeta`.
- `DjangoType.__init_subclass__` selects fields, computes consumer-authored sets and Relay
  suppression state, then validates unknown/excluded/consumer-authored/relation/suppressed targets.
- `_build_annotations` receives the normalized override sets and passes the computed
  `force_nullable` into `convert_scalar`.

That keeps the existing "shape gates run once" invariant and avoids re-reading raw `Meta` attrs in
multiple places.

Affected spec sections: Decision 8, Implementation plan, Definition of done.

### P2 - Dotted-path resolution is underspecified and the proposed helper does not match the examples

The spec says dotted paths are resolved with Strawberry's `import_module_symbol` or Django's
`import_string`, "the same mechanism `export_schema.py` uses." Those are not equivalent. The local
`import_module_symbol` accepts `module:symbol`, or `module` plus a default symbol name; it does not
resolve `apps.library.schema.PatronType` as written in the spec's user-facing API and tests.

If the public command accepts Django-style dotted objects, pin `django.utils.module_loading.import_string`
as the primary resolver. If it accepts Strawberry selector syntax, change the examples to
`apps.library.schema:PatronType`. Mixing the two in the spec will produce an implementation that
passes one example and fails the other.

Affected spec sections: User-facing API, Decision 4, Slice 2 test plan.

### P2 - Bare registered-name lookup needs a first-class ambiguity error

The registry can hold multiple `DjangoType` classes with the same `__name__` from different modules.
The spec currently treats registered-name collisions as a future fallback only "if confusing." A
diagnostic command must not return the first matching class by registry iteration order. That would
make `inspect_django_type PatronType` dependent on import order.

Make the contract: bare-name lookup succeeds only when exactly one registered type has that
`__name__`; zero matches is unresolvable; multiple matches raises `CommandError` listing candidates
and asking for a dotted path. Add package-internal coverage for the ambiguity branch.

Affected spec sections: Decision 4, Risks and open questions, Slice 2 test plan.

### P2 - The live HTTP nullability-override host is underdesigned

The spec says the scalars app is the natural live-HTTP host and suggests a fakeshop `DjangoType`
declares both override directions. Mutating the existing `ScalarSpecimenType` /
`NullableScalarSpecimenType` is likely to break existing live tests that intentionally pin baseline
non-null and nullable introspection, plus all-null wire-format behavior for
`NullableScalarSpecimen`.

The spec should say exactly where the acceptance type lives. If it introduces a second
`DjangoType` for an existing model, it must also address the multi-type registry rule by setting a
primary type deliberately. If it modifies the existing types, it must name which existing assertions
change and why that is desirable. A dedicated acceptance-only type/query is cleaner, but the
`Meta.primary` interaction must be part of the plan.

Affected spec sections: Current state, Test plan, Edge cases.

### P2 - The companion CSV intentionally omits the card's new public surfaces

The spec's Risk section says `Meta.nullable_overrides`, `Meta.required_overrides`, and
`inspect_django_type` are omitted from `docs/spec-029-consumer_dx_cleanup-0_0_9-terms.csv` because
the glossary headings do not exist yet. That makes the checker green by dropping the most important
new terms from the audit ledger.

Either add planned glossary headings before the checker run, or make the DoD honest that the
companion CSV is intentionally incomplete until Slice 2 / Slice 3 doc updates land. The current DoD
claim that the CSV anchors every project-specific term is not true.

Affected spec sections: Risks and open questions, Definition of done, companion CSV.

### P3 - The illustrative inspect output uses a non-existent `PatronType` field

The `inspect_django_type PatronType` example includes `membership_status`, but
`examples/fakeshop/apps/library/models.py::Patron` has no such field and
`examples/fakeshop/apps/library/schema.py::PatronType` does not select it. Use a real choice-bearing
field such as `BookType.circulation_status` for the choice-row example, or keep the `PatronType`
example limited to `id`, `name`, `lifetime_fines_cents`, `card`, and `loans`.

Affected spec sections: User-facing API, Slice 2 test plan.

## Overall

The spec is directionally strong on API shape: Meta-based nullability overrides, class/factory
`extensions=`, scalar-only relation deferral, and no per-card version bump are the right calls. The
main blockers are implementability details where the text promises behavior the current metadata
surfaces do not support. Fix the Slice 1 inventory/gate, define the inspect command's authoritative
annotation source, and rewrite the Slice 3 validation flow before implementation starts.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
