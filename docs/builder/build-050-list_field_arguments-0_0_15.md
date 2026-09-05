# Build: `DjangoListField` argument surface (`offset`, `limit`, and `orderBy`)

Spec: [`docs/spec-050-list_field_arguments-0_0_15.md`][spec-050]
Rationale: [`docs/spec-050-list_field_arguments-0_0_15-rationale.md`][spec-050-rationale]
Target release: `0.0.15`
Status: complete

## Pre-flight baseline
- Baseline check: clean (`git status --short` empty at pre-flight).
- Static inspection tool smoke test: passed (`scripts/review_inspect.py django_strawberry_framework/list_field.py --output-dir docs/shadow --stdout`).
- Spec glossary consistency check: passed (43 terms checked, exited 0).
- Spec rationale extraction: completed by Worker 1.
  - Spec byte count before: 147,842 bytes (2,056 lines)
  - Spec byte count after: 141,617 bytes (1,979 lines)
  - Rationale byte count: 20,524 bytes (342 lines)

## Slices

- [x] **Slice 1 — argument normalization and typed runtime rejection**
  - [x] `django_strawberry_framework/list_field.py` synthesizes `offset: Int` and
        `limit: Int` on every `DjangoListField`; both are nullable and optional.
  - [x] A package-owned `ListArgumentError` rejects negative and over-ceiling runtime
        values with stable `extensions`; GraphQL's standard `Int` coercion owns wire type
        rejection before the resolver.
  - [x] That class is exported from `django_strawberry_framework/__init__.py`, and
        `tests/base/test_init.py`'s pinned `__all__` tuple, star-import row, and
        export-identity row are updated with it; the version literal and its own assertion
        stay with card 053.
  - [x] Argument wire names are resolved only while building an error, never on a successful
        request.
  - [x] The offset ceiling is `ResourcePolicy.max_list_rows`; no setting key is added.
  - [x] Error payloads derive argument names from the active Strawberry schema rather than
        assuming the default camel-case converter.
- [x] **Slice 2 — Meta-derived `orderBy` and list pipeline**
  - [x] A target carrying `Meta.orderset_class` gains nullable, optional
        `orderBy: [<OrderSet>InputType!]`; a target without that sidecar does not publish a
        meaningless order input.
  - [x] Sync and async paths run visibility, then `OrderSet`, then the offset/order guard,
        then the one raw-list slice.
  - [x] The result of a public `OrderSet.apply_*` override is validated as an unevaluated,
        unsliced, non-projection, non-combined model queryset before the final window; the
        seal gains the new `unevaluated` option, reuses the shipped `reject_combined` one,
        and both new-to-this-boundary codes gain arms at the two visibility message sites.
  - [x] Nonzero offset requires a materially active `orderBy` or still-effective model
        `Meta.ordering` on the post-visibility queryset; no pk tiebreaker and no `DISTINCT`
        are injected.
- [x] **Slice 3 — SQL and unit contracts**
  - [x] `tests/test_list_field.py` pins signature shape, cap arithmetic, direct-call
        runtime errors, helper mechanics, model-ordering state, and no-argument SQL
        parity; wire-reachable sync and async wrapper behavior stays in the live tier.
  - [x] Remove adapter-relevant `DJANGO_ALLOW_ASYNC_UNSAFE` setup from existing package
        tests so it cannot mask a regression in safe async queryset completion; retain an
        override only where a separately named legacy behavior genuinely still requires it.
  - [x] Order input construction continues to use the shipped `OrderSet` factory and orphan
        ledger rather than a list-field-specific input class.
- [x] **Slice 4 — live acceptance**
  - [x] A dedicated `examples/fakeshop/test_query/test_list_field_api.py` drives the sync
        surface over `/graphql/`: ordered offset pages, `orderBy` lists,
        visibility-before-order, limit/cap/error cases, converter naming, and the exceptional
        holder-mounted source shapes. It is the sync counterpart of the async suite rather
        than nineteen more rows inside the broad library application suite.
  - [x] `examples/fakeshop/test_query/test_resource_policy_api.py` pins request-policy
        narrowing over the same field surface.
  - [x] A test-local `AsyncDjangoGraphQLView` mount proves safe async queryset completion,
        configured argument names, async iterable cleanup, and async pipeline parity over
        HTTP without `DJANGO_ALLOW_ASYNC_UNSAFE`.
  - [x] Add the new async live-test path to the card's predicted files, then regenerate the
        tracked-path constants after the path is in the index so governance sees the file.
  - [x] Add the new suite and its shared-helper exemption to
        `examples/fakeshop/test_query/README.md`.
- [x] **Slice 5 — documentation fold-in**
  - [x] Update the list-field docstring and the shipped-surface descriptions in
        `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, and `README.md` where the new
        arguments are enumerated.
  - [x] Update `ResourcePolicy` and bounding-helper docstrings to distinguish returned/skip
        ceilings from total database rows scanned.
  - [x] Update the KANBAN database when the implementation card closes; `TODAY.md` is
        deliberately not edited (no waiting entry exists to move - see Doc updates).
  - [x] Leave the version literal, version assertion, package-version glossary row, release
        wording, and `CHANGELOG.md` to card 053's joint cut; `pyproject.toml` and `uv.lock`
        have no duplicate root-package version to bump.
- [x] **Cross-slice integration pass (Worker 1)**
- [x] **Final test-run gate (Worker 1)** -> [`docs/builder/bld-final.md`][bld-final]

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[spec-050]: docs/spec-050-list_field_arguments-0_0_15.md
[spec-050-rationale]: docs/spec-050-list_field_arguments-0_0_15-rationale.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[bld-final]: bld-final.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
