# Spec 035 Review Feedback

Target: [Spec 035][spec-035].

## Findings

### Major 1 - G2 does not define a complete `.only()` kill switch

Decision 4 says non-`QUERY` operations suppress `only_fields` across the whole plan tree, but the mechanism narrows to "scalar columns are never appended" and relies on `django_strawberry_framework/optimizer/walker.py::_ensure_connector_only_fields` no-op behavior. That misses existing projection writers.

The current walker writes or applies column projection through more than scalar leaves: `django_strawberry_framework/optimizer/walker.py::_walk_selections` appends Relay custom-pk and scalar columns, `django_strawberry_framework/optimizer/walker.py::_record_relation_access` appends FK connector columns on every relation traversal, `django_strawberry_framework/optimizer/walker.py::_ensure_connector_only_fields` appends prefetch connector columns, and `django_strawberry_framework/optimizer/walker.py::_project_scalar_only_window` calls `.only(...)` directly for scalar-only nested connection windows. If Slice 2 only blocks scalar appends, a mutation selecting a relation can still get non-empty `only_fields`, and scalar-only relation connections can still apply `.only(...)` without touching `OptimizationPlan.only_fields`.

Recommended fix: make Decision 4 require an explicit projection gate threaded through every `_walk_selections` call and every helper that writes or applies projection, or add a plan-level `enable_only` flag that all projection writers must check. Keep FK-id elision enabled, but do not let connector-column helpers populate `only_fields` when projection is disabled. Add tests that inspect the applied querysets, not just the root plan tuple: root to-one relation, to-many `Prefetch.queryset.query.deferred_loading`, and scalar-only nested connection windows should all prove no `.only()` is applied under mutation/subscription.

### Major 2 - G3 primary-type-name matching violates GraphQL type-condition semantics

Decision 6 accepts the model's registered primary type name when planning a secondary type over the same model. That is not how GraphQL type conditions work. A fragment condition matches the runtime GraphQL type or an abstract type it belongs to, not the Django model. If a resolver returns `SecondaryItemType`, a `... on PrimaryItemType` fragment should not inline just because both types map to `Item`.

Inlining primary-type fragments for a secondary reintroduces the over-planning class G3 is supposed to remove. It can plan fields or relations that the secondary does not expose, and it can cross distinct `get_queryset`, `relation_shapes`, or field-override contracts. The existing plan cache already includes the origin Strawberry type, so there is no cache reason to blur primary and secondary types.

Recommended fix: the accept set should be the current planning type's own GraphQL name plus abstract interfaces it actually implements. If `source_type is None`, `django_strawberry_framework/optimizer/walker.py::_resolve_field_map` already routes to `registry.get(model)`, so the primary type naturally accepts its own name when it is the current planning type. Drop the model-primary-name accept rule, update the companion CSV's `Meta.primary` note, and add a secondary-return regression where `... on PrimaryType` is skipped while a primary-return plan still accepts it.

### Major 3 - G3 under-specifies abstract type conditions outside `Meta.interfaces`

Decision 6 says a non-matching `type_condition` is skipped outright. That is safe for known sibling object types, but it is not enough for every valid abstract GraphQL shape. A fragment can be conditioned on a union, or on an interface a `DjangoType` implements through direct inheritance rather than the `Meta.interfaces` tuple. Skipping the whole subtree for an unknown abstract condition can under-plan valid nested fragments that do match the current concrete type.

Recommended fix: either narrow the supported scope explicitly or define a conservative fallback. For registry-known object type names and known implemented interface names, skip non-matches. For unknown composite condition names, recurse into nested fragments without accepting direct fields, or record the shape as out of scope and test the fallback behavior. Also define interface-name collection from finalized Strawberry metadata or the class MRO, not only the raw `Meta.interfaces` tuple, so direct interface inheritance remains consistent with the package's existing interface support.

### Medium 1 - The spec cannot grant `CHANGELOG.md` edit permission by itself

The spec repeatedly says Slice 4 "grants" the per-card `CHANGELOG.md` edit permission. That conflicts with the repository instruction that `CHANGELOG.md` is edited only when explicitly instructed. A standing design doc can describe required release-note work, but it should not be treated as an active user instruction for a future agent turn.

Recommended fix: rephrase the Slice 4 sections to say the maintainer prompt for Slice 4 must explicitly include the `CHANGELOG.md` edit. Keep the planned bullets, but remove wording that implies the spec itself grants permission.

### Minor 1 - Standing-doc source references still use line-number anchors

The spec intentionally records audit anchors, but it still contains standing-doc references to old local line-number anchors and upstream optimizer line numbers. `AGENTS.md` requires standing docs and specs to use symbol-qualified paths or unique substrings rather than raw line-number references; raw line numbers are reserved for per-cycle scratchpads.

Recommended fix: convert local references to symbol-qualified form such as `django_strawberry_framework/optimizer/walker.py::_walk_selections #"unknown-name guard"` or `path #"unique substring"`. If upstream line numbers are valuable as audit evidence, keep them in a review scratchpad or replace them with stable external permalinks plus prose that the behavior, not the line number, is the contract.

## Check Run

- `uv run python scripts/check_spec_glossary.py --spec docs/spec-035-optimizer_hardening-0_0_10.md` - passed: `OK: 21 terms`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[spec-035]: spec-035-optimizer_hardening-0_0_10.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
