# Feedback: `docs/spec-019-multi_db-0_0_7.md` revision 2
Revision 2 addresses the major rev1 concerns: implicit-router `_db` semantics are corrected, generated child `Prefetch` alias inheritance is no longer claimed as shipped behavior, the null-FK and no-`_state` branches are split, fakeshop tests are explicitly live HTTP, and the glossary checker passes:

`uv run python scripts/check_spec_glossary.py --spec docs/spec-019-multi_db-0_0_7.md` → `OK: 17 terms — all have glossary entries and at least one spec link.`

Remaining feedback is now about consistency and implementability, not the core direction.

## High-priority fixes

### 1. Goal 1 still contains stale broad wording
`## Goals` item 1 still says the consumer can rely on:

- “`Prefetch` chains respect routing”
- “`get_queryset` downgrade respects routing”
- “strictness mode tracks the originating connection”

Those phrases contradict the rev2 corrections in Decision 3:

- generated child `Prefetch` querysets do **not** inherit the root queryset alias;
- consumer-provided `Prefetch(queryset=...)` aliases are the pinned behavior;
- strictness is connection-agnostic and does not track routing.

Recommended replacement:

> Ship `docs/spec-019-multi_db-0_0_7.md` documenting the cooperation contract: `router.db_for_read` on FK-id elision stubs, explicit `.using(alias)` preservation through `OptimizationPlan.apply`, consumer-provided `Prefetch(queryset=...)` alias round-trip via `OptimizerHint.prefetch(...)`, and strictness-mode behavior remaining unchanged for rows loaded from non-default aliases.

### 2. Move the direct `_check_n1(...)` test out of `tests/optimizer/test_multi_db.py`
Revision 2 correctly moves `_build_fk_id_stub(...)` tests to `tests/types/test_resolvers.py`, but it still places `test_strictness_check_is_connection_agnostic_under_using` in `tests/optimizer/test_multi_db.py` while directly exercising `_check_n1(...)`.

`_check_n1(...)` lives in `django_strawberry_framework/types/resolvers.py`, so a direct unit test for it belongs in `tests/types/test_resolvers.py` under the same mirror-rule logic used for `_build_fk_id_stub(...)`.

Choose one of these shapes:

1. **Direct unit test:** move the strictness test into `tests/types/test_resolvers.py`. Slice 1 becomes five resolver-level tests and two optimizer-plan-level tests.
2. **Optimizer-level test:** keep a strictness-related test in `tests/optimizer/test_multi_db.py`, but exercise it through `DjangoOptimizerExtension(strictness="raise")` and a GraphQL execution path rather than directly importing `_check_n1(...)`.

Do not keep a direct `_check_n1(...)` unit test in the optimizer test module.

### 3. Decision 5 still describes package-internal tests as if they are only `tests/optimizer/test_multi_db.py`
Decision 5 opens with:

> `tests/optimizer/test_multi_db.py` does NOT depend on `FAKESHOP_SHARDED=1`...

But Slice 1 is now split across `tests/types/test_resolvers.py` and `tests/optimizer/test_multi_db.py`. Update the decision heading/body to refer to package-internal tests generally, then specify:

- resolver-level router-call tests live in `tests/types/test_resolvers.py`;
- optimizer-plan alias-preservation tests live in `tests/optimizer/test_multi_db.py`;
- neither uses `FAKESHOP_SHARDED=1` or a second SQLite database.

Also soften “both files mock `router.db_for_read`” in the Slice checklist. The optimizer-plan tests should not all need a router mock; only router-call tests should patch the router.

### 4. The live HTTP harness conflicts with the copied reload fixture
The spec currently wants:

- copy `_reload_project_schema_for_acceptance_tests` from `test_library_api.py`;
- declare a module-level `_MultiDbTestQuery`, `_test_schema`, and `urlpatterns`;
- use that temp schema for live HTTP tests.

That can produce stale registry/schema interactions:

- the copied autouse fixture clears the registry before each test and reloads project schema modules;
- a module-level test schema built before that fixture runs may hold DjangoType classes whose registry entries were cleared;
- the fixture reloads `apps.library.schema`, `config.schema`, and `config.urls`, but it does not rebuild the test module’s `_test_schema`.

Recommended fix: make the temp schema/URLConf construction happen after the registry reload, inside a test fixture that runs after the autouse reload fixture. Two safe patterns:

1. Build the test schema inside a fixture and route the temp URLConf to a module-level mutable/current schema holder.
2. Avoid declaring new DjangoType classes in the test module; import the freshly reloaded `BookType` from `apps.library.schema` after the reload fixture and build the test `Query`/schema from that.

The spec should pin one of these patterns. A static module-level `_test_schema` is risky with the existing reload contract.

### 5. The temp URLConf instructions need to be more concrete
`override_settings(ROOT_URLCONF=<this_module_name>)` is directionally right, but implementers need a real module object/path.

Pin one concrete form, for example:

- define `urlpatterns` at module level;
- use `override_settings(ROOT_URLCONF=__name__)`;
- call `clear_url_caches()` after entering the override and again in `finally`/fixture teardown.

If the schema is built dynamically per test, the module-level URLConf needs a stable view that reads the current schema from a holder, or the URLConf must be rebuilt/reloaded in a way Django actually sees.

## Medium-priority consistency fixes

### 6. Problem statement and glossary-reference language still over-broaden `get_queryset` routing
The problem statement still says:

> the optimizer's `Prefetch` downgrade for `get_queryset` hooks runs against whatever queryset the consumer's hook returned (which carries its own `_db`)

That is only safe if the hook explicitly returns a queryset with an alias, or if you are talking about preserving a consumer-provided queryset. It should not imply root queryset `_db` flows into generated child querysets.

Recommended rewrite:

> The generated `Prefetch` downgrade uses the queryset returned by the target type’s `get_queryset`; if that hook explicitly returns a `.using(alias)` queryset, the alias is preserved. The root queryset alias is not threaded into generated child querysets in this card.

Also update the `get_queryset visibility hook` glossary-reference bullet similarly.

### 7. Current state still says the FK-id stub “inherits the routing context”
Current state says:

> so the stub inherits the routing context of the parent row when one exists

The more precise rev2 contract is that the package forwards the parent row as `instance=` and the router decides. Replace with:

> so consumer routers can consult the parent row as an `instance=` hint; the stub’s `_state.db` is whatever the router returns.

### 8. Decision 3 justification still cites the old KANBAN wording as if unchanged
Decision 3’s justification says the four-axis list maps to the KANBAN bullets including:

- “strictness mode tracking originating connection”
- “`get_queryset` downgrade respecting routing”

Because rev2 deliberately narrowed those meanings, add a parenthetical:

> The KANBAN wording is interpreted through the narrower rev2 contract: strictness remains active but does not route, and generated `get_queryset` prefetches do not inherit the parent alias.

### 9. Doc-update snippets should use the narrowed wording everywhere
The `docs/README.md` forward-pointer still says:

> what the package guarantees under `.using()`, `Prefetch` chains, and `get_queryset` downgrades

That wording reintroduces the broad rev1 claim. Suggested replacement:

> For the cooperation contract these shards run against — explicit `.using()` preservation, FK-id elision router hints, consumer-provided `Prefetch(queryset=...)` aliases, and strictness behavior under non-default aliases — see ...

Do the same in the planned `docs/GLOSSARY.md` body update: make sure the four bullets match Decision 3’s narrowed axes, not the rev1 phrasing.

### 10. The KANBAN Done-body path explanation is probably overcomplicated
Decision 1 says the Done body points at `docs/SPECS/spec-019...` because the close-out flow happens after Step 8 archives the spec.

But implementation close-out and spec-author Step 8 are separate workflows in this repo’s actual usage, and the active WIP card currently points at `docs/spec-019...`. To avoid future confusion, make the rule simpler:

- while the spec is active, references point to `docs/spec-019...`;
- after the archive pass moves it, references point to `docs/SPECS/spec-019...`;
- any KANBAN Done body should point wherever the file actually lives at the time of the edit.

Do not imply the implementation Slice 3 necessarily occurs after a future spec-author Step 8 unless that is an explicit project rule.

## Low-priority cleanups

### 11. Revision history is now very long
The revision 2 history is useful, but it consumes a large amount of the spec before the actual content begins. Consider compressing it into a shorter summary and letting `docs/feedback.md` remain the detailed review artifact.

This is not a correctness issue, but it will make the final spec easier to use during implementation.

### 12. The checker passes; no CSV changes required
The terms CSV now removes the bad `Meta.preferred_database` anchor and includes `OptimizerHint`. The glossary checker passes. No further terms CSV changes are needed unless the spec text changes materially.

## Bottom line
Revision 2 is much closer. Before implementation, fix the stale broad wording in Goals / docs updates, move or reframe the direct `_check_n1(...)` test, and make the live HTTP temp-schema harness compatible with the registry reload fixture. After those changes, the spec should be implementable without production code changes.