# Spec 035 Review Feedback

Target: [Spec 035][spec-035].

Scope: second pass after the maintainer revisions, with the test-placement claims checked
against the live HTTP coverage rule in the [fakeshop test-query README][test-query-readme].

## Findings

### Major 1 - G3 test placement still overclaims package-only coverage

The revised spec still says G3 needs synthetic union / interface schemas and is not reachable
by a single live products GraphQL query, so all G3 coverage belongs in `tests/optimizer/`.
That is too broad under the [test-query README][test-query-readme].

The fakeshop schema already exposes a real optimized connection path through
[library schema][library-schema] `Query.all_library_genres_connection`, and the live suite
already has [test_library_api.py][test-library-api]
`test_typed_inline_fragment_under_connection_field_still_resolves` proving that
`... on GenreType` under `edges { node { ... } }` is a valid `/graphql/` shape. G3's own test
list includes matching-type fragments and connection-wrapped fragments. At least that subset
is reachable over the real HTTP stack and should not be earned only through synthetic
package tests.

Recommended fix: split Decision 8, the Test Plan, and the DoD by reachability. Keep the
synthetic package tests for sibling concrete exclusion, unknown composite fallback,
secondary-type primary-fragment behavior, same-named relation regression, and strictness
internals. Add a live `examples/fakeshop/test_query/` test, using the
`_reload_project_schema_for_acceptance_tests` fixture pattern, for the concrete reachable
case: a typed fragment on `GenreType` under `allLibraryGenresConnection` that selects a
relation such as `books { title }` and asserts the optimizer-planned SQL shape rather than
only response success. That would directly exercise
[selections.py][selections] `included_field_selections` and [walker.py][walker]
`_walk_selections` through `/graphql/`.

### Medium 1 - G2 needs an explicit future live-test handoff

The package-only G2 tests are justified for this card because the fakeshop schema has no
mutation surface yet. The spec is also clear that G2 exists to protect the upcoming
`0.0.11` mutation cohort. Once a fakeshop mutation returning a queryset exists, the
[test-query README][test-query-readme] makes live `/graphql/` coverage mandatory for the
consumer-visible behavior.

Recommended fix: add a precise handoff in the G2 Test Plan or Out-of-scope section: no live
test lands in this card because no mutation operation is exposed, but the first mutation
card must add or migrate a live `examples/fakeshop/test_query/` acceptance test using the
reload fixture pattern. That test should prove a mutation queryset response keeps
`select_related` / `prefetch_related` while carrying no deferred loading. Without that
handoff, the spec can leave the write-side surface with only package-internal proof after it
becomes live-reachable.

### Minor 1 - Standing-doc line-number anchors remain

The revised spec fixed most behavioral issues, but it still preserves raw line-number
citations in the revision history, parity checkpoint, and risks section. This is a standing
design doc, so the repository source-reference convention still applies: use
symbol-qualified paths or unique-substring anchors, and reserve raw line numbers for
per-cycle scratch artifacts.

Recommended fix: rewrite local card-citation corrections to symbol-qualified references and
replace upstream line-number prose with stable behavior descriptions or external permalinks.
The audit evidence can stay, but the design doc should make the behavior the contract, not
the old line location.

## Check Run

- `uv run python scripts/check_spec_glossary.py --spec docs/spec-035-optimizer_hardening-0_0_10.md`
  passed: `OK: 21 terms - all have glossary entries and at least one spec link.`

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[spec-035]: spec-035-optimizer_hardening-0_0_10.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[selections]: ../django_strawberry_framework/optimizer/selections.py
[walker]: ../django_strawberry_framework/optimizer/walker.py

<!-- tests/ -->

<!-- examples/ -->
[library-schema]: ../examples/fakeshop/apps/library/schema.py
[test-library-api]: ../examples/fakeshop/test_query/test_library_api.py
[test-query-readme]: ../examples/fakeshop/test_query/README.md

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
