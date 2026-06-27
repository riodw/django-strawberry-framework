# Review - `spec-039-serializer_mutations-0_0_13.md` deep architecture pass

Date: 2026-06-27.

This pass assumes the current spec-039 revision plus the source-site
`TODO(spec-039 Slice N)` anchors added across the core, fakeshop, and package-test
surfaces. The spec is materially stronger than the earlier drafts: it respects the
Meta-class public surface, uses the existing `DjangoMutation` seams, keeps DRF soft,
folds the resolver and live products surface into one slice, and names the DRY
promotions that would otherwise become third copies.

There are still several issues to fix in the spec before production code starts.

## Bottom line

Architecturally, the card is viable. The largest remaining risks are not "can this be
built?" risks; they are contract precision risks:

- the soft-dependency export plan can break `from django_strawberry_framework import *`
  for consumers without DRF;
- the save-time `ValidationError` handling conflates DRF and Django exception shapes;
- relation-id input wording promises more than GraphQL can actually accept for one
  generated field;
- serializer-only relation fields sit between two contradictory rules;
- the shared write-pipeline abstraction is underspecified enough to become a leaky
  generic framework instead of a small create/update skeleton;
- release docs say "shipped" while the version policy says the package remains
  `0.0.12` until the joint cut.

The `RELAY_GLOBALID_STRATEGY` setting location is not a problem if the implementation
keeps the existing pattern: domain validation in `types/relay.py`, resolved once at
finalization, then read from recorded definition state during query execution.

## Findings

### F1 - High: soft dependency conflicts with adding `SerializerMutation` to `__all__`

The spec pins all three statements:

- `import django_strawberry_framework` succeeds without DRF;
- `SerializerMutation` is added to root `__all__`;
- `from django_strawberry_framework import *` with DRF absent raises the guarded
  `ImportError`.

That is a breaking regression for a consumer who does a star import today and never uses
DRF. The spec's own soft-dependency story says "a consumer who never writes a serializer
mutation never needs DRF"; putting a DRF-gated symbol in `__all__` makes that false for
star imports.

Recommended spec update:

- Do not add `SerializerMutation` to root `__all__` while DRF is a soft dependency.
- Keep `from django_strawberry_framework import SerializerMutation` working through
  root `__getattr__`; named imports do not require `__all__`.
- Add a soft-dependency test for `from django_strawberry_framework import *` under
  simulated DRF absence, asserting it still succeeds and omits `SerializerMutation`.
- Document `SerializerMutation` as a public lazy export, but not a star-import export
  unless DRF becomes a hard dependency.

If the maintainer intentionally wants star import to fail when DRF is absent, the spec
should call that out as an accepted breaking behavior. I do not recommend that.

### F2 - High: save-time `ValidationError` handling conflates DRF and Django shapes

Decision 8 correctly adds save-time validation to the envelope, but the prose says a
DRF `serializers.ValidationError` and a `django.core.exceptions.ValidationError` both
route through the recursive DRF flattener via `.detail`.

That is only true for DRF's exception. Django's `ValidationError` has `message_dict`,
`messages`, and `error_dict` style shapes, not DRF's `.detail` contract. Routing both
through one `.detail` path will either crash or silently lose structure.

Recommended spec update:

- Split save-time validation handling by exception class.
- `rest_framework.exceptions.ValidationError` and `serializers.ValidationError`:
  route `.detail` through `serializer_errors_to_field_errors(...)`.
- `django.core.exceptions.ValidationError`: route through the existing flat
  `mutations/resolvers.py::validation_error_to_field_errors` where possible, or through
  a small adapter that first normalizes Django's `message_dict` / `messages` shape.
- Keep `IntegrityError` on the existing `save_or_field_errors(...)` path.
- Add separate package tests for DRF save-time validation and Django save-time
  validation. They are not the same branch.

### F3 - High: "GlobalID or raw pk" is over-promised for generated relation inputs

The spec repeatedly says a relation id accepts a `GlobalID` or a raw pk. Internally, a
decoder can support both. Publicly, a generated GraphQL input field has one annotation.
If the related primary `DjangoType` is Relay-shaped and the input annotation is
`GlobalID`, a raw integer pk cannot pass GraphQL variable coercion in a live HTTP
request. Existing products tests already show malformed `GlobalID` strings becoming
top-level coercion errors before the resolver sees them.

Recommended spec update:

- Reword the public contract to: the generated annotation is strategy dependent:
  Relay targets expose `GlobalID`; non-Relay/raw-pk targets expose the raw pk scalar.
- The resolver helper may accept both shapes because it is shared and package tests can
  exercise synthetic direct-call branches, but live GraphQL only reaches the shape
  admitted by the generated annotation.
- Keep raw-pk / non-Relay relation decode tests in `tests/rest_framework/`, not live
  products, unless fakeshop adds a real non-Relay relation field.
- Update Decision 7, Decision 8, and the test plan so "accepts both" never reads like a
  promise for one generated GraphQL field.

### F4 - Medium: serializer-only relation fields are not defined

The spec says serializer-only fields with no model column become input fields and are
validated by the serializer. It also says relation fields need a backing Django model
field resolved through one-segment `source`, and dotted/source-star relation fields fail
because the backing column cannot be resolved.

That leaves a real DRF pattern undefined: a write-only `PrimaryKeyRelatedField` with a
`queryset` that is not a model field and is consumed by custom `create()` / `update()`.
That is a serializer-only field, but it is also a relation.

Recommended spec update, choose one explicitly:

- Preferred: support serializer-only relation fields when the DRF field has a concrete
  `queryset.model`; use that model as the relation target for id annotation and
  visibility checks, while preserving the declared serializer field name for
  `provided_data`.
- Alternative: reject serializer-only relation fields for `0.0.13` and say
  "serializer-only fields are supported for scalar/file fields only; relation fields
  must resolve to a one-segment model source."

The current text implies both support and rejection.

### F5 - Medium: serializer error field names are ambiguous

The reverse map records GraphQL input name, generated input attr, serializer field name,
source, and kind. The resolver uses it to decode `categoryId` into serializer key
`category`. But the error-flattener section does not decide whether a serializer error
on `category` should return:

- `FieldError(field="category")`, matching DRF/form field names; or
- `FieldError(field="categoryId")`, matching what the GraphQL client sent.

Both can be defended. The spec must choose. Leaving it implicit will cause drift between
decode errors, serializer validation errors, and renamed-field errors.

Recommended spec update:

- Preferred: map serializer error paths back to GraphQL input paths when an input field
  exists in the reverse map. That gives clients errors keyed to their submitted field
  names (`categoryId`, `fullName`) and aligns with relation decode errors.
- Preserve `"__all__"` for non-field errors.
- If an error references a serializer field not present in the input surface, keep the
  serializer path because there is no GraphQL input path to report.
- Add live tests for a renamed scalar or relation field error, not only a plain `name`
  error, so the choice is locked.

If the spec chooses serializer names instead, state that explicitly and test it.

### F6 - Medium: `run_write_pipeline_sync` risks becoming an over-broad abstraction

The DRY goal is right: the authorize-before-decode order is security-sensitive and
should not be copied a third time. The current P1.5 wording, however, sometimes reads as
if one skeleton should cover model create/update/delete, model-form create/update, plain
form, and serializer create/update.

Those are not all the same shape:

- delete has no `data`, no relation decode, and a snapshot-before-delete payload;
- plain form has no model instance, no primary type, and no optimizer re-fetch;
- model mutations run `full_clean()` and M2M assignment;
- serializer mutations run `is_valid()` and `serializer.save()`.

Recommended spec update:

- Scope `run_write_pipeline_sync(...)` to model-backed create/update flavors only.
- Exclude delete and plain form from the shared skeleton unless a smaller common
  helper naturally falls out.
- Define a precise callback contract:
  - `decode_step(ctx) -> decoded data | list[FieldError]`;
  - `write_step(ctx, decoded) -> saved instance | list[FieldError]`;
  - the skeleton owns atomicity, locate, not-found payload, authorization before
    `decode_step`, refetch, and payload construction.
- Require existing model and form behavior to stay byte-equivalent under their current
  tests before serializer code lands.

Without that boundary, the abstraction could become technical debt even though the DRY
intent is correct.

### F7 - Medium: `get_serializer_kwargs`, `partial=True`, and `context` precedence are underspecified

Decision 8 says construction goes through `get_serializer_kwargs(...)`, injects
`context={"request": ...}`, and injects `partial=True` on update. It does not say what
happens when a consumer override returns its own `context`, omits `data`, passes
`partial=False`, or passes `instance`.

`partial=True` is not just a default; it is the update contract. Context is less rigid
but is the default path for request-aware validators and `CurrentUserDefault`.

Recommended spec update:

- Define the default hook return shape exactly: `data`, optional `instance`, and
  `context` containing the request.
- State whether a consumer override owns the entire kwargs dict or whether framework
  kwargs are merged after the hook.
- Preferred: the resolver enforces `partial=True` for update after calling the hook,
  and raises `ConfigurationError` if the hook tries to set `partial=False`.
- Preferred: merge default request context with any override-provided `context`, with
  override keys winning except for `request` unless explicitly documented otherwise.
- Add tests for an override that adds a custom kwarg while preserving request context,
  and an override that tries to disable partial update.

### F8 - Medium: Slice 4 public docs conflict with the joint version-bump policy

Decision 14 says no version file changes in this card because the `0.0.13` version bump
belongs to the joint cut with auth mutations. Slice 4 still says README/docs move the
serializer flavor to "Shipped today" and glossary status to `shipped (0.0.13)`.

That can leave the repository advertising a shipped `0.0.13` public feature while
`pyproject.toml`, `__version__`, and `tests/base/test_init.py::test_version` still say
`0.0.12`.

Recommended spec update:

- Split "implementation docs" from "release docs".
- In this card's Slice 4, update internal architecture docs (`docs/TREE.md`,
  `TODAY.md`, possibly `docs/GLOSSARY.md`) to "implemented for upcoming 0.0.13" or
  equivalent if the feature is merged before the joint cut.
- Defer public README "shipped today", glossary `shipped (0.0.13)`, and changelog
  release language to the joint `0.0.13` cut, unless the maintainer explicitly wants
  unreleased-main docs to advertise future-version behavior.
- Keep the GOAL.md example correction in this card, because the current example would
  be wrong once the code lands.

### F9 - Medium: HiddenField behavior under partial update should not be a live proof

The spec mentions `HiddenField(default=CurrentUserDefault())` as a possible request
context proof. DRF hidden fields are subtle under `partial=True`; they are not a stable
way to prove update-time request context in a serializer mutation.

Recommended spec update:

- Use an explicit `validate()` or `validate_<field>()` branch that reads
  `self.context["request"]` for the required live context test.
- Keep `HiddenField` covered as an input-generation/drop rule and, if desired, a
  create-only serializer behavior.
- Do not make the live update context proof depend on HiddenField default behavior.

### F10 - Low: `register_subsystem_clear` registration timing needs a precise rule

The registration seam is the right direction, but "the serializer input namespace
registers at import" leaves a timing edge: a clear target only exists after the module
that registers it has been imported. That is usually okay because stale serializer
ledger state implies `rest_framework.inputs` was already imported in a previous failed
bind, but the spec should make the invariant explicit.

Recommended spec update:

- Either define the subsystem-clear targets centrally as static `(module_path, attr)`
  rows that do not require importing DRF modules at registration time; or
- state the import-time registration invariant: once a subsystem has created state that
  must be cleared, its module has been imported and has registered its clear function.
- Add retry-idempotence tests that fail after serializer input materialization, rerun
  finalization, and prove the serializer ledger was cleared.

### F11 - Low: DRF version floor must be a precondition, not a Slice 4 surprise

The spec now names the CI matrix and `filterwarnings = error`, which is good. The
implementation table still places the dev dependency in Slice 4, after Slice 1-3 code
and tests conceptually exist.

Recommended spec update:

- Treat the DRF version-floor probe as a Slice 0 / pre-Slice-1 gate.
- Record the exact tested floor before writing converter code.
- If a targeted warning ignore is needed for DRF-origin warnings, add it in the same
  dependency-change slice before code imports DRF in tests.

Otherwise Slice 1 can be blocked late by dependency support rather than design.

## Configuration and performance assessment

The existing `RELAY_GLOBALID_STRATEGY` placement is sound:

- `django_strawberry_framework/conf.py` is a generic settings reader. It validates the
  top-level `DJANGO_STRAWBERRY_FRAMEWORK` shape, not domain-specific values.
- `django_strawberry_framework/types/relay.py::_resolve_globalid_strategy` owns the
  Relay-domain validation. That is the right layer because it shares the same validator
  as `Meta.globalid_strategy`.
- The setting branch is called during finalization by
  `types/relay.py::install_globalid_typename_resolver`, then the effective strategy is
  recorded on the type definition.
- Query-time encode/decode paths use the captured strategy or
  `definition.effective_globalid_strategy`; they do not need to re-read or re-validate
  `conf.settings`.

So the lazy read does not introduce meaningful runtime overhead or query-time
thread-safety risk as long as serializer relation decoding follows the existing Relay
decode APIs and does not call `_resolve_globalid_strategy(...)` during request handling.

Recommended spec update:

- Add a sentence to Decision 7 or Decision 8: serializer relation decode must consume
  the recorded GlobalID strategy through existing Relay helpers and must not read
  `conf.settings.RELAY_GLOBALID_STRATEGY` or call `_resolve_globalid_strategy(...)` on
  the query path.
- Add a test only if new serializer code touches GlobalID decode directly: monkeypatch
  `_resolve_globalid_strategy` to fail after finalization and assert a serializer
  relation mutation still resolves through recorded strategy state.

Do not move `RELAY_GLOBALID_STRATEGY` domain validation into `conf.py`; that would make
the generic settings layer aware of Relay semantics and duplicate the per-type
`Meta.globalid_strategy` validator.

## Test and documentation gaps

The test plan is mostly consistent with `examples/fakeshop/test_query/README.md`, but
these updates should be made before implementation:

- Add the star-import soft-dependency test from F1.
- Split DRF and Django save-time validation tests from F2.
- Clarify which relation-id shapes can be live-tested versus package-tested from F3.
- Add at least one renamed-field error-path test from F5.
- Add hook precedence tests from F7.
- Keep request-context proof on explicit `validate()` logic, not HiddenField partial
  behavior, per F9.
- Split release documentation wording per F8 so public docs do not claim a released
  `0.0.13` feature while the package still reports `0.0.12`.

## Proposed spec patch list

1. Decision 12: remove `SerializerMutation` from `__all__` or explicitly accept the
   star-import break. Preferred: omit it from `__all__` while keeping named lazy import.
2. Decision 8: split save-time DRF `ValidationError` from Django `ValidationError`.
3. Decisions 7/8: reword relation id "GlobalID or raw pk" as generated-shape-specific
   public behavior plus broader internal helper behavior.
4. Decision 7: decide serializer-only relation fields: support via `field.queryset.model`
   or reject explicitly.
5. Decision 8: decide and test serializer error path names, preferably GraphQL input
   names when reverse-map data exists.
6. DRY obligations P1.5: scope `run_write_pipeline_sync` to model-backed create/update
   and define callback contracts.
7. Decision 8: define `get_serializer_kwargs` merge and `partial=True` precedence.
8. Slice 4 docs: separate implemented-on-main docs from released-version docs.
9. Decision 13/test plan: use `validate()` for request-context live proof.
10. Decision 6/P1.6: pin subsystem-clear registration timing.
11. Decision 12/implementation plan: move DRF floor verification to a pre-Slice-1 gate.
