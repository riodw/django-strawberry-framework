# Review - `spec-039-serializer_mutations-0_0_13.md` architecture pass

Date: 2026-06-27.

This review is based on the current `spec-039` revision plus the source-site
`TODO(spec-039 Slice N)` anchors and pseudo-code pass. The spec is now broadly
architecturally sound: it keeps the public surface DRF-shaped and `class Meta`-driven,
keeps DRF soft, reuses the `036` / `038` mutation contracts, folds the resolver and live
products surface into one slice, and makes the main DRY promotions explicit.

There are still several spec corrections to make before production code starts. Most are
not design-fatal, but they are exactly the kind of stale summary wording that causes an
implementer to build the older draft.

## Bottom Line

Proceed with the architecture after the corrections below. The highest-risk remaining
items are:

- the Slice 0 dependency gate is contradicted by older Slice 4 wording;
- one edge-case section still sends Django `ValidationError` down the wrong flattener;
- relation-id summaries still imply a dual-shape GraphQL input instead of the
  one-annotation contract;
- `get_serializer_kwargs` request ownership is ambiguous enough to create actor drift;
- DRF null/default semantics are under-specified.

The `RELAY_GLOBALID_STRATEGY` placement in `types/relay.py` is acceptable if the
implementation follows the current Decision 8 rule: validate once at type/finalization
time, record the effective strategy, and never read or re-validate the setting on the
request path.

## Findings

### H1 - Slice 0 vs Slice 4 is still contradictory

The spec now correctly defines a pre-Slice-1 dependency gate, but older prose remains:
the status block still says "Four slices" and describes Slice 4 as "docs + the soft-dep
wiring + card wrap"; the Goals section still says `uv.lock` is updated in Slice 4. Later
sections say the opposite: Slice 0 adds DRF to the dev group, regenerates `uv.lock`, and
Slice 4 is doc/card-wrap only.

Impact: a worker following the spec top-down could defer the DRF dev dependency until
after Slice 1, then hit import failures or coverage holes in the converter/input tests.

Correction:

- Change the status block to "Slice 0 gate plus four implementation/doc slices."
- Remove "soft-dep wiring" from the Slice 4 status sentence.
- Change the Goals item that says `uv.lock` updates in Slice 4 to say Slice 0.
- Keep Slice 4 limited to implemented-on-main docs, GOAL correction, KANBAN/card wrap,
  and deferred joint-cut release docs.

### H2 - The save-time `ValidationError` edge case still contradicts Decision 8

Decision 8 correctly says save-time validation splits by exception class:

- DRF `rest_framework.exceptions.ValidationError` / `serializers.ValidationError` uses
  `.detail` and the recursive serializer-error flattener.
- Django `django.core.exceptions.ValidationError` uses the flat `036`
  `validation_error_to_field_errors` path over `error_dict` / `messages`.

But the Edge cases section still says a serializer raising DRF or Django
`ValidationError` at `serializer.save()` returns via the recursive flattener and refers
to `.detail`. Django `ValidationError` has no `.detail`.

Impact: this would either raise `AttributeError` or lose Django model-validation
structure if implemented from the edge-case summary.

Correction: rewrite that edge-case bullet to mirror Decision 8 exactly. Add the same
split to the DoD Slice 3 resolver item where it currently summarizes save-time
validation generically.

### H3 - `context["request"]` ownership is ambiguous and can drift from permission auth

Decision 8 says request context is framework-owned, but also allows an override to supply
its own `context["request"]` as an "escape hatch." Those two statements conflict. The
write permission check has already used `request_from_info(info)` as the actor; letting
the serializer validate against a different request object means permission and
validation can disagree about the user/tenant.

Impact: custom validators could see a different actor than the write-auth seam, causing
hard-to-debug authorization inconsistencies and making request-context tests less
meaningful.

Correction: make request ownership strict. The framework should merge context after the
hook and set `context["request"] = request_from_info(...)` unconditionally. If an
override supplies a different `request`, raise `ConfigurationError`; if it supplies the
same object, tolerate it. Consumer-specific context belongs under other keys.

### M1 - Relation-id summaries still imply a dual-shape GraphQL input

Decision 7 / Decision 8 now correctly say generated relation fields carry exactly one
annotation: Relay `GlobalID` for a Relay-shaped target, otherwise the raw-pk scalar. The
shared decode helper accepts both only because package-internal tests need to exercise
the raw-pk/non-Relay branch.

Older wording remains in the Slice 3 and DoD summaries: "each relation id — `GlobalID`
or raw pk" without the generated-field qualifier. Those same summaries also mention
target resolution only via backing FK `source`, omitting serializer-only relation fields
whose target comes from `field.queryset.model`.

Impact: implementers may over-permissively accept both id shapes on one live GraphQL
field, or skip serializer-only relation support despite Decision 7 requiring it.

Correction:

- In Slice 3 and DoD summaries, say "the generated input exposes one strategy-dependent
  shape; the shared decoder helper accepts both for reused/package-only branches."
- Include both relation-target sources everywhere relation decode is summarized:
  backing FK via one-segment `source`, or serializer-only `field.queryset.model`.

### M2 - DRF null/default semantics are under-specified

The converter/input sections derive requiredness from `field.required`, but do not pin
`allow_null`, visible serializer `default`, `CreateOnlyDefault`, or `allow_blank`.
These are important because GraphQL input nullability and DRF requiredness are not the
same axis.

Examples:

- `required=True, allow_null=True` means "the client must provide the key, but may send
  null" in DRF. Plain GraphQL input types cannot express that exactly as both required
  and nullable without careful Strawberry/default handling; omission must still reach
  DRF as "missing" so the serializer can raise the required error.
- `required=False, default=...` should be omittable and let DRF apply the default.
- `allow_blank=True` is a serializer validation rule for strings, not GraphQL
  nullability.

Impact: the generated SDL can either reject valid DRF `null` values too early or
silently allow omission that only fails later, depending on how the builder interprets
annotation vs default.

Correction: add a dedicated "Nullability and defaults" paragraph to Decision 7:

- annotation nullability follows `allow_null`;
- omission/default behavior follows `field.required` and DRF defaults;
- omitted fields are stripped/left absent so DRF can distinguish missing from explicit
  `None`;
- explicit `None` is preserved;
- `allow_blank` is not encoded in GraphQL and remains serializer validation;
- add tests for `required=True + allow_null=True`, `required=False + default`, and
  `allow_blank=True`.

### M3 - Relation targets without a primary `DjangoType` are not pinned

The spec repeatedly says relation visibility is enforced through the related primary
`DjangoType.get_queryset`, but the promoted form helper currently has a fallback path for
no registered primary type: it uses the model default manager. For serializer relations,
the converter must decide at build time whether a target without a primary type is
allowed.

Impact: if a relation write silently falls back to the default manager, the spec's
"visibility-scoped relation decode" promise is overstated. If implementation instead
raises, tests based on the promoted helper may surprise the worker.

Correction: pin the contract. Preferred high-quality answer: serializer relation fields
require a registered primary `DjangoType` for the target model; otherwise class creation
raises `ConfigurationError` naming the serializer field and target model. If preserving
the form fallback is required, add an explicit helper parameter so serializer decode can
choose the stricter contract without changing form behavior.

### M4 - The `register_subsystem_clear` fallback invites the debt the spec is trying to remove

The DRY section makes `register_subsystem_clear(module_path, attr)` a P1 promotion, and
the TODO anchors now point at the static clear-target registry. But the Slice 2 text still
allows a fallback where finalizer and registry receive two hand-edits if the seam is "out
of slice budget."

Impact: this is a permanent two-list synchronization hazard, and adding the serializer
would make it a third subsystem relying on manually mirrored clears. That is exactly the
technical debt the spec identifies.

Correction: remove the fallback. Make the static `(module_path, attr)` clear registry a
Slice 2 requirement. The registry must store strings only and resolve through
`_clear_if_importable` so DRF is not imported while absent.

### M5 - Current-state prose understates the cross-module DRY work

The "Context" section says this card creates `rest_framework/` and
`tests/rest_framework/` and "adds no module outside them beyond products-example wiring
and the soft-dep edit." That is no longer true. The spec requires `utils/converters.py`,
`utils/inputs.py`, `mutations/sets.py`, `mutations/resolvers.py`, `utils/querysets.py`,
`forms/*`, `registry.py`, and `types/finalizer.py` edits for the DRY promotions.

Impact: reviewers can underestimate the blast radius or reject required changes as
scope creep.

Correction: replace that sentence with the accurate boundary: the new consumer-facing
subpackage is `rest_framework/`, but the card deliberately promotes shared internals in
`utils/`, `mutations/`, `forms/`, `registry.py`, and `types/finalizer.py` to avoid third
copies.

## Missing Edge Cases

- **Nullable required serializer fields:** covered in M2; needs explicit mapping and
  tests.
- **Serializer relation target with no primary type:** covered in M3; needs a pinned
  build-time result.
- **Context mutation by hooks:** covered in H3; the hook must not be able to change the
  request actor.
- **Serializer field name collisions after GraphQL camel/id suffixing:** the spec covers
  id-like suffixes, but should explicitly say two declared serializer fields that produce
  the same GraphQL input name raise `ConfigurationError` before materialization. This is
  the serializer analog of the form collision guard.
- **`source` collisions:** if two serializer fields have distinct declared names but the
  same one-segment `source`, both may be valid DRF patterns for read/write customization.
  The spec should state whether the reverse map allows this and lets DRF resolve it, or
  rejects duplicate writable `source` paths to avoid double-writing one model attr.

## Configuration And Performance Assessment

The `RELAY_GLOBALID_STRATEGY` setting location is not a runtime performance problem in
the architecture currently described.

The safe model is:

- `types/relay.py` validates/resolves the strategy when the `DjangoType` definition is
  built/finalized.
- The resolved value is recorded as `effective_globalid_strategy` on the type/definition.
- Serializer relation decode receives the target type/definition and consumes that
  recorded value.
- The resolver never reads `conf.settings.RELAY_GLOBALID_STRATEGY` and never calls
  `_resolve_globalid_strategy(...)` during query execution.

Under that model there is no per-request setting lookup, no repeated validation, and no
new thread-safety issue. The setting object remains a configuration-time concern, not a
request-path dependency.

The risk is implementation drift, not the anchor location. Keep the test already planned:
after finalization, monkeypatch `types/relay.py::_resolve_globalid_strategy` to fail and
assert serializer relation decode still works from recorded state. Also grep the
serializer resolver for `conf.settings` and `_resolve_globalid_strategy` in Slice 3.

## Test And Documentation Gaps

- **The DRF floor check is not a normal pytest assertion.** The spec requires proving a
  DRF version imports and runs warning-free across Python 3.10-3.14 and Django
  5.2-6.0/latest under `filterwarnings = error`. The current test suite will not prove
  that without running the CI matrix or a dedicated probe. Add a Slice 0 acceptance
  artifact: either a small script or explicit `uv` commands, and state where the chosen
  floor is recorded.
- **Live-vs-package resolver split is feasible.** Existing fakeshop live tests already
  cover `/graphql/`, auth users, seeded products data, multipart upload precedent, and
  query capture. No major rewrite is needed, but the spec should keep repeating that
  reachable create/update branches belong in `examples/fakeshop/test_query`, not
  `tests/rest_framework`.
- **Soft-dependency absent tests are feasible but need isolation discipline.** The spec
  correctly requires evicting both `rest_framework*` namespaces and deleting any bound
  root `SerializerMutation`. Keep the non-memoization requirement; otherwise a passing
  test can be a stale import.
- **Docs must not advertise release status early.** The F8 split is correct. The stale
  Slice 4 wording is the doc gap to fix, not the underlying policy.

## Recommended Spec Edits Before Code

1. Normalize all Slice 0 / Slice 4 wording across Status, Goals, Slice checklist,
   Implementation plan, Doc updates, and DoD.
2. Fix the write-time `ValidationError` edge-case bullet to split DRF and Django
   exception classes.
3. Tighten `get_serializer_kwargs` context merging so `context["request"]` cannot drift
   from the permission actor.
4. Update all relation-id summaries to the one-generated-shape contract and include
   serializer-only `queryset.model` target resolution.
5. Add null/default semantics for `allow_null`, `required`, DRF defaults, explicit
   `None`, omission, and `allow_blank`.
6. Pin relation-target behavior when no primary `DjangoType` exists.
7. Make `register_subsystem_clear` mandatory, not a budget-dependent fallback.
8. Correct the current-state prose to include the shared-helper promotion blast radius.
