# Build: Cross-slice integration pass

Spec reference: `docs/spec-016-list_field-0_0_7.md` (active spec; all six slice checklists at spec lines 94-163; `docs/builder/BUILD.md` "Cross-slice integration pass" mandate at BUILD.md:509-531; "DRY FIRST" rule at BUILD.md:22-23 — Worker 1 re-checks DRY across slices at the integration pass).
Status: final-accepted

## Plan (Worker 1)

The integration pass is Worker-1-only. The mandate (BUILD.md:509-531) requires Worker 1 to:

1. Read every prior `docs/builder/bld-slice-*.md` artifact in slice order. **Done** — Slices 0-5 walked end-to-end via the `Plan`, `Build report`, `Review`, and `Final verification` sections of each artifact.
2. Confirm the static inspection helper has been run, or explicitly skipped with a recorded reason, for every Python file with review-worthy logic touched by the build.
3. Compare the **Repeated string literals** sections across every shadow overview for cross-slice DRY signals.
4. Compare the **Imports** sections across every shadow overview to confirm one-way dependency direction.
5. Walk every accepted slice artifact's `What looks solid` / `DRY findings` / `Notes for Worker 1 (spec reconciliation)` sections for deferred follow-ups.

### Static inspection helper runs (refreshed at this pass)

Per the prompt's mandated invocations:

- `uv run python scripts/review_inspect.py django_strawberry_framework/list_field.py --output-dir docs/shadow` — pass. Output at `docs/shadow/django_strawberry_framework__list_field.{overview.md,stripped.py}`.
- `uv run python scripts/review_inspect.py tests/test_list_field.py --output-dir docs/shadow` — pass. Output at `docs/shadow/tests__test_list_field.{overview.md,stripped.py}`.
- `uv run python scripts/review_inspect.py examples/fakeshop/apps/library/schema.py --output-dir docs/shadow` — pass. Output at `docs/shadow/examples__fakeshop__apps__library__schema.{overview.md,stripped.py}`.
- `uv run python scripts/review_inspect.py examples/fakeshop/test_query/test_library_api.py --output-dir docs/shadow` — pass. Output at `docs/shadow/examples__fakeshop__test_query__test_library_api.{overview.md,stripped.py}`.

The cycle-prior `docs/shadow/django_strawberry_framework__types__relay.overview.md` (refreshed by Slice 1's planning pass) remains in the shadow tree as a read-only reference for the `_apply_get_queryset_{sync,async}` helpers reused by Slice 1's factory.

Slice coverage of the helper:

- Slice 0 (pre-impl spike): no `.py` files committed; helper N/A. Recorded skip with reason in `bld-slice-0-preimpl_verification.md:178-180`.
- Slice 1 (`list_field.py` + `__init__.py` + `tests/base/test_init.py`): helper run on `list_field.py` at Worker 3 review-time (`bld-slice-1-module_factory.md:355-374`); skipped for `__init__.py` and `tests/base/test_init.py` with recorded reason "low-surface; pure re-export / pin assertion". Confirmed appropriate.
- Slice 2 (`list_field.py` + `tests/test_list_field.py`): Worker 3 skipped helper on `list_field.py` with recorded reason "Slice 2 delta is ~18 logic lines, under the 30-line threshold for files under `django_strawberry_framework/`" (`bld-slice-2-validation.md:251-255`). The post-Slice-2 surface of `list_field.py` was captured by Worker 2's own re-run during Slice 3 planning (recorded in `bld-slice-3` artifact at lines 38-50). Skipped for `tests/test_list_field.py` with role-file test-tree exemption. Appropriate.
- Slice 3 (`tests/test_list_field.py` only): Worker 3 ran the helper on `list_field.py` to confirm zero production-source drift (`bld-slice-3-optimizer_get_queryset_tests.md:342-346`); skipped for `tests/test_list_field.py` with role-file test-tree exemption. Appropriate.
- Slice 4 (`examples/fakeshop/apps/library/schema.py` + `examples/fakeshop/test_query/test_library_api.py`): Worker 1's planning pass ran the helper on both files (`bld-slice-4-live_http_coverage.md:29-31`); Worker 3 skipped re-run with recorded reason "diff under 30/50-line thresholds; planning shadow output is current" (`bld-slice-4-live_http_coverage.md:242-247`). Appropriate.
- Slice 5 (Markdown-only): helper N/A. Recorded skip with reason "every touched file is Markdown" (`bld-slice-5-promotion_docs_version.md:18` and `:222`). Appropriate.

Coverage is complete. Every Python file with review-worthy logic that was touched during the build has been inspected at least once during planning or review, and the integration pass refreshed all four for this scan.

## DRY scan

The integration scan walks the four shadow overviews (`list_field.overview.md`, `test_list_field.overview.md`, `library/schema.overview.md`, `test_library_api.overview.md`) plus the carry-forward observations Slice 1-5 surfaced.

### Repeated string literals

The shadow overviews surface the following non-empty `Repeated string literals` sections. Cross-file analysis:

#### Intra-file literals (all four shadow overviews)

- `django_strawberry_framework/list_field.py` — **zero** repeated string literals (confirmed at `docs/shadow/django_strawberry_framework__list_field.overview.md` "Repeated string literals: None"). No cross-file pressure from production source.
- `examples/fakeshop/apps/library/schema.py` — **zero** repeated string literals.
- `tests/test_list_field.py` — 8 intra-file repeated literals: `{ allCategories { id name } }` (9x), `allCategories` (9x), `expected at least one non-filtered Category row` (5x), `DJANGO_ALLOW_ASYNC_UNSAFE` (3x), `NON_NULL` (3x), `CategoryType` (2x), `category` (2x), `ItemType.category@allItems.category` (2x).
- `examples/fakeshop/test_query/test_library_api.py` — 22 intra-file repeated literals; the only Slice-4-introduced repeats are `ListField West` (2x) and `ListField East` (2x). Every other repeat (`Speculative`, `library_shelf`, `Override`, `subtitle`, etc.) pre-dates this card.

#### Cross-file overlap (the load-bearing question per BUILD.md:517-518)

Cross-product walk of the four overviews' `Repeated string literals` sections: **zero string literal appears in two or more files in the build's diff**. The candidate literals checked individually:

- `allCategories` — only `tests/test_list_field.py` (the package-internal behavior tests). The HTTP test uses `allLibraryBranchesViaListField`; the example schema uses no string literals at all.
- `allLibraryBranchesViaListField` — only `examples/fakeshop/test_query/test_library_api.py:533` (single mention); the example schema declares the field via Python attribute name (`all_library_branches_via_list_field`), which Strawberry converts to the camelCase GraphQL field name at schema-build time — not a literal in `schema.py`.
- `ListField West` / `ListField East` — only `examples/fakeshop/test_query/test_library_api.py` (the new HTTP test's seed names). Slice 4 specifically chose these strings so they cannot collide with `test_library_relation_override_shapes_http_response_data`'s pre-existing `Override` / `Override East` seed names (recorded in `bld-slice-4-live_http_coverage.md:190` and the Worker 3 review at line 228); the seed-name choice is itself a cross-test DRY-discipline win, not a violation.
- `CategoryType`, `ItemType`, `BranchType`, `_CategoryType` — these are GraphQL-type identifiers Strawberry derives from `cls.__name__`. They reuse across the build's tests because the build's tests reuse the same set of `apps.products` and `apps.library` models, which is the spec-pinned discipline (`AGENTS.md` line 6: "First line of every catalog/auth test: `seed_data(N)` or `create_users(N)`"). Not duplication; intentional reuse of the example-app fixture surface.
- `__django_strawberry_definition__` — appears in `list_field.py:75` (Slice 2 guard) and in `types/base.py:245` (assignment site referenced by Slice 2's planning citation). Per Slice 2's final-verification check at `bld-slice-2-validation.md:282`, extraction to a module-level constant would obscure the directly-greppable protocol-style attribute name; the spec at line 548 uses the literal verbatim; **accept with reason** (protocol-attribute strings are by-design grep-anchored; lifting to a constant trades clarity for one less occurrence).

**Disposition: zero cross-slice repeated-literal DRY candidates surface.** The build is clean on this axis.

### Imports

Cross-file import direction walk (one row per file in the build's diff):

| File | Imports list (highlights) | Cross-folder direction | Verdict |
|---|---|---|---|
| `django_strawberry_framework/list_field.py` | `inspect`, `Callable` from `collections.abc`, `Any` from `typing`, `strawberry`, `django.db.models`, `strawberry.types.Info`, `strawberry.utils.inspect.in_async_context`, `.exceptions.ConfigurationError`, `.types.DjangoType`, `.types.relay._apply_get_queryset_{sync,async}` | Imports from `.exceptions` and `.types` only (NOT from `.optimizer/` and NOT from `examples/` / `tests/`); imports from the package boundary down into Strawberry / Django, never sideways across `optimizer/types` | Clean. One-way: `list_field.py` → `.exceptions`, `.types`, `.types.relay`. No reverse import from `.types.relay` or `.exceptions` into `list_field.py` would surface (verified: `grep -rn "from .list_field\|from django_strawberry_framework.list_field" django_strawberry_framework/types/ django_strawberry_framework/optimizer/ django_strawberry_framework/exceptions.py` returns zero hits). |
| `django_strawberry_framework/__init__.py` | Adds `from .list_field import DjangoListField  # noqa: E402` | Pure re-export at the package top level | Clean. The top-level `__init__.py` is the consolidation point for the public surface; importing `list_field` here is the documented boundary. |
| `tests/test_list_field.py` | `pytest`, `strawberry`, `apps.products.{services,models}`, `asgiref.sync.sync_to_async`, `django.db.models.Prefetch`, `strawberry.types.Info`, `django_strawberry_framework.{DjangoListField, DjangoOptimizerExtension, DjangoType, finalize_django_types}`, `django_strawberry_framework.exceptions.ConfigurationError`, `django_strawberry_framework.registry.registry` | Tests import from `apps.products` (the example-app fixture per `AGENTS.md` line 6) and the package public surface plus two sub-package leaves (`.exceptions`, `.registry`). | Clean. The `tests/` tree imports DOWN into the package; the package never imports from `tests/`. Reaching into `.exceptions` and `.registry` (not just the top-level `__all__`) is documented at `bld-slice-2-validation.md:11` ("the top-level `__init__.py:28-37` `__all__` deliberately does NOT re-export `ConfigurationError`; consumers and tests reach into `.exceptions`") and follows the precedent at `tests/test_registry.py:5-7`. |
| `examples/fakeshop/apps/library/schema.py` | `strawberry`, `strawberry.relay`, `apps.library.models`, `django_strawberry_framework.{DjangoListField, DjangoType, OptimizerHint}` | Example app imports from the package (one-way). | Clean. The example-app schema imports `DjangoListField` from the package's public surface — exactly the integration the spec is selling. |
| `examples/fakeshop/test_query/test_library_api.py` | `base64`, `importlib`, `sys`, `pytest`, `apps.library.models`, `django.db.{connection,test.Client,test.utils.CaptureQueriesContext,urls.clear_url_caches}`, `django_strawberry_framework.registry.registry` | HTTP test imports from the example app and Django; reaches into `.registry` for the reload-pattern autouse fixture. | Clean. The HTTP-test file deliberately does NOT module-level import classes from `apps.library.schema` (it reloads them per the comment block at `test_library_api.py:25-26`), and it deliberately does NOT import from `tests/` (the two test trees are isolated per `AGENTS.md` line 6). |

**Cross-folder direction check:** every cross-folder import in the build's diff is **outward from the package or downward into the package**. No reverse imports (no `.types/` → `list_field`, no `.optimizer/` → `list_field`, no `examples/` → `tests/`, no `tests/` → `examples/`). The boundary documented in `docs/TREE.md` is honored end-to-end.

**Verdict: clean.** No cross-folder import boundary violation. No new reverse-import direction introduced by any slice.

### Symbols / helpers

Cross-file symbol-overlap walk (looking for accidentally-parallel helper names across files):

- `_post_process_consumer_sync` / `_post_process_consumer_async` (`list_field.py:31` and `:39`) — module-level helpers; defined only in `list_field.py`. No parallel implementation under `types/relay.py` or anywhere else in the package (`grep -rn "_post_process_consumer" django_strawberry_framework/` returns 4 hits, all in `list_field.py`). No drift.
- `_apply_get_queryset_sync` / `_apply_get_queryset_async` (`types/relay.py:199-237`) — Slice 1 imports them; Slice 3 tests pin the rejection-message contract from `types/relay.py:215-216` via substring assertion. **No duplication** — the helpers stay at the single source of truth in `types/relay.py`. The cross-spec consolidation candidate (relocate to `utils/get_queryset.py` per Decision 3 Option B) remains deferred to a future card with a third call site, exactly as the spec licenses at line 513.
- `_isolate_global_registry` autouse fixture — `tests/test_list_field.py:37` and `tests/test_registry.py:35` are bytewise-identical (modulo docstring). This is the repo-wide pattern Slice 2's review surfaced (recorded as Low; `bld-slice-2-validation.md:209-220`) and Slice 3's review walked end-to-end (`bld-slice-3-optimizer_get_queryset_tests.md:308`). Repo-wide grep at integration time: `grep -rln "registry.clear()" tests/` returns 14 files (the 13-site count in the Slice-3 carry-forward is now 14 because Slice 2 added `tests/test_list_field.py`). See "Deferred follow-ups" below.
- `_post_graphql`, `_assert_graphql_data`, `_seed_branch_with_two_shelves`, `_seed_library_graph`, `_decode_global_id`, `_field_type`, `_reload_project_schema_for_acceptance_tests` (`examples/fakeshop/test_query/test_library_api.py:18-86`) — helpers private to that test file; no parallel names under `tests/` or under any other test-query file (only one file lives at `examples/fakeshop/test_query/` today). No drift.
- `CategoryType` / `ItemType` / `BranchType` / `_CategoryType` / `_T` / `_PrimaryCategoryType` / `_SecondaryCategoryType` — Strawberry type names declared at function scope inside `tests/test_list_field.py` for per-test isolation. The names overlap with `BranchType` from `examples/fakeshop/apps/library/schema.py:61`, but they live in different modules with the autouse-registry-clear fixture clearing state between tests; the overlap is name-shadowing inside an isolated test scope, not duplication. Both Slice 3's review (`bld-slice-3` artifact at lines 308-310) and Slice 4's review (`bld-slice-4` artifact at lines 250-259) called this out and concurred that the inline declarations are intentional repetition that keep each test self-readable.
- `Query` (the `@strawberry.type` root) — declared at function scope inside every behavior test in `tests/test_list_field.py`, and at module scope in `examples/fakeshop/apps/library/schema.py:83`. Same name-shadowing-in-isolated-scope pattern as the type-name discussion above. No drift; both names compile and execute under separate Strawberry schemas.

**Verdict: no overlapping helper names that warrant consolidation.** The `_apply_get_queryset_*` reuse is exactly the DRY win Decision 3 Option A pre-committed to; the `_isolate_global_registry` pattern is a 14-site repo-wide concern (see Deferred follow-ups).

### Deferred follow-ups

Walking every prior slice artifact's `### What looks solid`, `### Notes for Worker 1 (spec reconciliation)`, `### Implementation notes`, and `### DRY findings` sections, the following items were explicitly deferred during the build. Each item is dispositioned here.

1. **`_isolate_global_registry` autouse fixture pattern duplicated across 14 sites in `tests/`** — surfaced as a Low in Slice 2 review (`bld-slice-2-validation.md:207-220`), re-confirmed during Slice 3 review (`bld-slice-3-optimizer_get_queryset_tests.md:308` — "13 sites" at Slice-3-review time; the count is now 14 with Slice 2's `tests/test_list_field.py` addition), carried forward in `worker-memory/worker-1.md` at the Slice 3 entry. The right consolidation shape would be a `tests/conftest.py` providing the autouse fixture once for the whole `tests/` tree. Disposition: **accept with reason** at this build cycle. Three reasons reinforce the disposition:
   - **Bounded constraint, not a single-slice introduction.** The pattern is 14 sites repo-wide and pre-dates this card. Consolidating it would require touching 12 files (`tests/test_*` siblings) outside spec-016's scope; that diff blast radius is exactly the kind of cross-test impact `AGENTS.md` discipline forbids landing inside an unrelated card.
   - **`tests/conftest.py` does not exist at HEAD.** Slice 3 verified via `ls tests/conftest.py` returning no such file. Introducing one as part of spec-016 would silently change the test-tree's import-time behavior for every test under `tests/` — a structural change that belongs to its own spec with its own contract.
   - **Honors the AGENTS.md line 4 directive.** The directive forbids surface-patches and partial consolidations. The root-cause-correct fix is a separate refactor spec that consolidates all 14 sites in one atomic change; the spec author can then audit each call site, confirm `registry.clear()` is the only semantic shared, and move the fixture once. That spec is the right shape — partial consolidation here would leave 12 sibling sites duplicating the same pattern and produce inconsistency rather than reduce it. Surfaced to `bld-final.md`'s `### Deferred work catalog` as a next-spec candidate.

2. **`BranchType.shelves` consumer-override resolver bypasses prefetch cache; contributes `+2` to the N=4 baseline in Slice 4's HTTP test** — flagged by Worker 3 in Slice 4 review (`bld-slice-4-live_http_coverage.md:268-272`) and recorded by Worker 1 final verification in the same artifact at lines 282-283 plus `### Spec changes made (Worker 1 only)` at lines 296-300. Disposition: **accept with reason** at this build cycle. The override resolver at `examples/fakeshop/apps/library/schema.py:65-67` (`return list(self.shelves.order_by("-code"))`) pre-dates this card; its behavior is the documented baseline for `test_library_relation_override_shapes_http_response_data` (also `len(captured) == 4`); refactoring it to consult `self._prefetched_objects_cache` before re-evaluating the relation manager would mutate every `BranchType` path in the schema (the same cross-test blast-radius `rev2 M2` cited against adding `BranchType.get_queryset` to this card). The N=4 baseline pinned with an explicit docstring derivation per rev6 M6 is the right shape for Slice 4; the optimizer-cooperation refactor of the override belongs to a separate spec. Surfaced to `bld-final.md`'s `### Deferred work catalog`.

3. **`Prefetch` import placement** — Slice 3 pass-1 review found `from django.db.models import Prefetch` declared inline inside a test body; under the AGENTS.md root-cause-fix directive, Worker 1 routed to `revision-needed` and Worker 2 pass-2 hoisted the import to the module-top third-party band (`bld-slice-3-optimizer_get_queryset_tests.md:393-426`, pass-2 build report). Disposition: **landed**, no further action.

4. **`README.md` Status section was a vacuous no-op in Slice 5 pass-1** — Worker 3 routed to `revision-needed` under the AGENTS.md root-cause-fix directive (`bld-slice-5-promotion_docs_version.md:240-260`); Worker 2 pass-2 appended a prose sentence at `README.md:45` surfacing `DjangoListField` alongside the version-pin sentence (`bld-slice-5-promotion_docs_version.md:324-358`). Disposition: **landed**, no further action. Spec line 149 was also tightened by Worker 1 in the same final-verification pass to record the file's actual shape so future card builds see "the Status section (currently plain prose; surface `DjangoListField` inline at `README.md:45` …)" rather than the original "shipped-today bullet list under 'Status'" assumption.

5. **`docs/README.md` Coming-in-`0.1.0` bullet narrowing** — Worker 2 narrowed the bullet to drop `DjangoListField` for internal consistency with the new shipped-today bullet (`bld-slice-5-promotion_docs_version.md:172` and `:220`). Worker 3 review confirmed this is correct (`bld-slice-5-promotion_docs_version.md:293`): leaving `DjangoListField` claimed in BOTH "Shipped today" AND "Coming in `0.1.0`" would be internally contradictory. Disposition: **landed**, no further action.

6. **Spec line 6 Predecessors `WIP-ALPHA-016-0.0.7` → `DONE-016-0.0.7`** — Worker 1's per-spawn status-line re-verification caught the stale WIP reference once Slice 5's column move landed; recorded under `Spec changes made (Worker 1 only)` at `bld-slice-5-promotion_docs_version.md:437`. Disposition: **landed**, no further action.

7. **`_apply_get_queryset_*` relocation to `utils/get_queryset.py` per Decision 3 Option B** — explicitly licensed by spec line 513 as the right move "when a third call site needs the helpers". `DjangoConnectionField` (`TODO-ALPHA-022-0.0.9`) is the third call site on the horizon. Disposition: **accept with reason** at this build cycle (only two call sites today: `types/relay.py` + `list_field.py`); flag in `bld-final.md`'s deferred-work catalog as the natural trigger when card 022 ships.

8. **Slice 0 spec line 96 lambda-vs-annotated-resolver drift** — Worker 1 already edited spec line 96 during Slice 0 final verification to replace the bare-lambda example with the annotated module-level resolver shape (`bld-slice-0-preimpl_verification.md:331-334`). Disposition: **landed**, no further action.

## Cross-slice checks

Per BUILD.md:521-528, the integration pass enumerates the following checks:

### Duplicated helpers across slices

None. Slice 1 introduced `_post_process_consumer_sync` / `_post_process_consumer_async` as module-level helpers per rev6 H2; no subsequent slice re-implemented them or shipped a parallel helper. Slice 1 reuses `_apply_get_queryset_sync` / `_apply_get_queryset_async` from `types/relay.py:199` / `:225` via import; no fork. Slice 2 added four inline `ConfigurationError` guards (no helper extracted — justified by spec lines 557-561 keeping validation at the construction site). Slices 3 and 4 added zero new helpers. Slice 5 is Markdown-only.

### Inconsistent naming or error handling between slices

Names land coherently end-to-end:

- The factory is named `DjangoListField` everywhere (Slice 1 + Slice 4 + every doc surface in Slice 5).
- The new sibling field is `all_library_branches_via_list_field` in `apps/library/schema.py` (Slice 4) and the GraphQL field name `allLibraryBranchesViaListField` in the HTTP test query (Slice 4) and the KANBAN Done body (Slice 5) and the GLOSSARY entry (Slice 5).
- The two module-level helpers in `list_field.py` carry the `_consumer` suffix per rev6 H3 (Slice 1); no subsequent slice introduced a sibling helper that would have collided.
- The `ConfigurationError` shape pattern `<Symbol> <constraint>; got <repr>.` (Slice 2 spec line 555) is used at all four Slice-2 guards verbatim; no error-shape drift across the four sites.

Error-handling discipline is coherent:

- `ConfigurationError` (spec Decision 5) is the only exception class raised by `DjangoListField`'s construction path (Slice 2) and the sync coroutine-rejection (Slice 1 via `_apply_get_queryset_sync` reuse).
- The rejection-message substring `returned a coroutine in a sync resolver context` is pinned by Slice 3's `test_djangolistfield_sync_path_rejects_coroutine_from_get_queryset` against `types/relay.py:215-216`'s production string — Slice 3 asserts the production helper's error verbatim, never re-rolling it. This is the cross-slice DRY contract Decision 3 Option A bought.

No drift.

### Repeated ORM/queryset patterns

The cross-file ORM-marker walk surfaces:

- `_default_manager.all()` — `list_field.py:94` (default-resolver body) AND `_apply_get_queryset_sync` / `_apply_get_queryset_async` consume the result. The single line at `list_field.py:94` is the canonical default-queryset shape per Decision 2 (spec line 432); not repeated elsewhere in the build's diff.
- `isinstance(result, models.Manager)` / `isinstance(result, models.QuerySet)` — `list_field.py:32, 34, 40, 42` (the two `_post_process_consumer_*` helpers). The same isinstance pair fires for sync and async; this is the rev2 H1 + rev4 M1 contract and the symmetric pair is the right shape per the async-detection-asymmetry justification at Decision 2 spec lines 472-477 (preserved in the in-source comment at `list_field.py:83-90`). The duplication is intentional per rev6 H2 / rev6 H3; collapsing would force a runtime branch on `in_async_context()` inside what the spec explicitly pins as a per-construction-static choice (Slice 1 review at `bld-slice-1-module_factory.md:390-391`). **Accept with reason.**
- `prefetch_related("shelves")` — `examples/fakeshop/test_query/test_library_api.py:553-557` (Slice 4) AND `bld-slice-3-optimizer_get_queryset_tests.md:251` (the package-internal optimizer-cooperation test asserting `prefetch_related[0].prefetch_to == "items"`). Different relations; not duplication. The deeper "is the optimizer planning correctly?" question is pinned twice — once in-process (Slice 3) and once over HTTP (Slice 4) — but that is the **two-fold framing** Decision 4 + rev3 M6 (spec line 534) explicitly required as the right shape: the package-internal test pins the return-shape contract, the HTTP test pins the end-to-end contract.

No repeated ORM/queryset pattern that should be centralized.

### Misplaced responsibilities

The slice boundaries align with the production-code module boundary:

- Slice 1 owns the factory + the public re-export.
- Slice 2 owns validation at the construction site (no validation logic landed anywhere else).
- Slice 3 owns the package-internal behavior tests in `tests/test_list_field.py` (no behavior tests added to `examples/`).
- Slice 4 owns the live HTTP test and the example-app schema add-only edit (no example-app changes from any other slice).
- Slice 5 owns the docs + KANBAN + CHANGELOG sweep (no doc/KANBAN edits from any other slice except the spec-status-line refresh Worker 1 owns per the standing role).

Cross-slice walkthrough confirms no responsibility-shift drift. The `BranchType.get_queryset` non-introduction was discussed and rejected at Slice 4 review (`bld-slice-4` artifact at lines 49-50 and 198-199) precisely because adding it would have moved the `get_queryset` cooperation coverage out of `tests/test_list_field.py` (its Slice 3 home) into the example app — a misplaced responsibility that the rev2 M2 spec line 17 explicitly forbids.

### Missing or too-broad exports

`git diff HEAD -- django_strawberry_framework/__init__.py` shows exactly one addition: `DjangoListField`, inserted into `__all__` in alphabetical position between `BigInt` and `DjangoOptimizerExtension` (Slice 1). The corresponding `tests/base/test_init.py:35-44` assertion was updated in the same slice (Slice 1) and re-confirmed unchanged across Slices 2-5 (`bld-slice-5-promotion_docs_version.md:211`).

No widening of the public surface from `_post_process_consumer_*` (correctly module-private; not in `__all__`), `_apply_get_queryset_*` (the helpers stayed private under `types/relay.py`), `ConfigurationError` (not re-exported at the top level by design — Slice 2 imports it from `.exceptions`).

Slice 5's `__all__` final-gate check at spec line 161 ("one new public export — the only addition to `__all__` in this slice") is satisfied by Slice 1's prior addition; Slice 5 itself adds zero public symbols. Verified clean.

### Repeated string literals / dictionary keys / tuple shapes across slices

Covered under "Repeated string literals" above. **Zero cross-slice repeats.** The intra-file repeats inside `tests/test_list_field.py` (the `{ allCategories { id name } }` query string used by ~9 sibling behavior tests) and `examples/fakeshop/test_query/test_library_api.py` are within-file patterns where lifting to a module-level constant would obscure the per-test selection-shape difference each test is pinning. Slice 3 review accepted the inline-introspection-query duplication for the same reason (`bld-slice-3-optimizer_get_queryset_tests.md:310`).

### Whether comments tell one coherent story across the new code

Walked the in-source comments across the four touched Python files plus the eight Markdown files:

- `list_field.py:25-28` documents the `_default`-bypasses-`_post_process_consumer_*`-helpers reasoning per rev6 H3.
- `list_field.py:60-66` documents the four-guard ordering and the `__django_strawberry_definition__` discriminator anchor.
- `list_field.py:83-90` documents the async-detection asymmetry (rev5 H2) and points readers at spec Decision 2's "Async-detection asymmetry" subsection without duplicating the spec text.
- `list_field.py:96-99` documents the rev6 H1 collapsed one-liner reasoning.
- `list_field.py:109-112` documents the rev4 H2 await-then-isinstance ordering.

Five in-source comment blocks, each anchored to a specific revision-history entry, each pointing into the spec rather than duplicating it. No conflicting narrative across the blocks.

Markdown sweep (Slice 5):

- `docs/GLOSSARY.md` entry, `docs/README.md` shipped-today bullet, `README.md` Status sentence, `GOAL.md` migration bullet, `TODAY.md` library summary, `KANBAN.md` DONE-016 body, `CHANGELOG.md` Added bullet — all use the same load-bearing anchor phrases ("non-Relay `list[T]` factory for root Query fields", "factory function", "`cls.get_queryset(...)` cooperation in sync + async contexts", "graphene-django parity", "outer nullability driven by the consumer's class-attribute annotation"). The seven surfaces are coherent without drifting into slightly-different phrasings.

No comment-coherence finding.

## Integration outcome

`final-accepted`. The cross-slice DRY scan, import-direction check, symbol-overlap walk, and deferred-follow-ups audit all close cleanly. Zero consolidation-loop-triggering findings. Two follow-ups accepted with reason for the `bld-final.md` deferred-work catalog (the 14-site `_isolate_global_registry` repo-wide pattern; the `BranchType.shelves` consumer-override prefetch-cache bypass), one already-licensed cross-spec deferral (Decision 3 Option B `utils/get_queryset.py` relocation when a third call site appears). No Worker 2 consolidation pass dispatch is required; no Worker 3 review pass is required.

### Summary

The integration scan found two genuine repeated patterns (the `_isolate_global_registry` autouse fixture across 14 sites in `tests/`, and the `BranchType.shelves` consumer-override resolver bypassing the prefetch cache) and both are accepted-with-reason at this slice scope under the AGENTS.md root-cause-fix directive: the right fix for each is its own separate spec with the appropriate blast radius (a refactor spec for the fixture; a follow-up card with its own contract for the override), not a partial consolidation inside spec-016's scope. Every other cross-slice axis — cross-file repeated string literals, cross-folder import direction, overlapping helper names, naming and error-handling consistency, ORM/queryset patterns, responsibility placement, public-export surface, in-source comment coherence — is clean. The build is ready for the final test-run gate (`bld-final.md`).

### Spec changes made (Worker 1 only)

No spec edits required at integration. The spec status line at line 4 (`draft (revision 6, post-rev5 scaffolding review)`) was re-verified at the start of this spawn and remains accurate; the per-slice ship state is tracked separately by Worker 0's build plan, which the maintainer commits alongside the source diff. The two spec edits Worker 1 made during Slice 5 (spec line 6 Predecessors flip from `WIP-ALPHA-016-0.0.7` to `DONE-016-0.0.7`; spec line 149 README sub-bullet tightening to match the file's prose shape) remain accurate after the integration scan — neither needs further refinement at this pass.
