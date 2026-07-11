# Spec-044 TODO-skeleton review

## Scope and verdict

Reviewed: every TODO comment in the working-tree diff — the four new stub
files (`django_strawberry_framework/extensions/__init__.py`,
`django_strawberry_framework/extensions/debug.py`,
`tests/extensions/__init__.py`, `tests/extensions/test_debug.py`,
`examples/fakeshop/test_query/test_debug_extension_api.py`) and the eight
TODO anchors dropped into tracked files (`CHANGELOG.md`, `GOAL.md`,
`README.md`, `TODAY.md`, `docs/README.md`,
`django_strawberry_framework/__init__.py`, `pyproject.toml`,
`tests/base/test_init.py`, `examples/fakeshop/config/schema.py`), plus the
non-TODO `kanban/constants.py` tracked-path additions that ride the same
diff. Every load-bearing engine and repo claim was checked against the
installed `strawberry-graphql==0.316.0`, Django, and the current
(Revision-7) spec text.

**Verdict: this is a high-fidelity skeleton.** The pseudocode is not a
paraphrase of the spec — it is the spec's contract re-derived against
source, and in the places where the two disagreed, the TODOs are the ones
that are right (the spec's Revision 7 already absorbed those corrections:
zero-arg construction, async result-map precedence, the conditional
double-call path, `callproc()` exclusion, nested-sync attribution). Slice
numbering on all eight doc anchors matches the spec's affected-files table
1:1. Four findings need fixing before Slice 1 starts — one factual error in
a live-test anchor, one gate interaction, one ordering nit, one misleading
rationale — plus two informational notes.

## Findings

### F1 — P0 (factual error): scenario 3's mutation user does not exist

`examples/fakeshop/test_query/test_debug_extension_api.py`, live-behavior
anchor 3:

> create_users(1), choose only the user with the required add permission,
> and authenticate via `with client.login(user):`

`create_users` (`examples/fakeshop/apps/products/services.py:281`) creates
**only per-view-permission users** — one user per `view_*` permission, four
per unit — plus one `staff_<n>` superuser. **No created user carries
`add_item`.** An implementer following this anchor literally will either
find nobody to "choose" or fall back to the superuser, which violates the
spec's D3 least-permission rule ("only the permission a scenario needs" —
a superuser passes every check and proves nothing about the gate).

The repository already has the canonical shape, twice:

- `examples/fakeshop/test_query/test_client_api.py:142-158` — take a
  `create_users` view user (`view_item_1`, explicitly NOT staff), then
  `user.user_permissions.add(Permission.objects.get(codename="add_item",
  content_type__app_label="products"))`;
- `examples/fakeshop/test_query/test_mutation_atomicity.py:295` —
  `_login_with_perm("view_item_1", "add_item")`.

Rewrite the anchor to the grant-on-top precedent: "create_users(1), grant
`add_item` to a non-staff view user (the `test_client_api.py:142`
precedent), authenticate via `with client.login(user):`". No spec change
needed — D3's wording survives because the base user still comes from
`create_users` and ends up holding only the permissions the scenario needs.

### F2 — P1 (gate interaction): the fail-loud stub breaks the coverage gate until Slice 1

`django_strawberry_framework/extensions/debug.py` ends in a module-level
`raise NotImplementedError` (line 210) — deliberately fail-loud, and the
right call. But `pyproject.toml` pins `[tool.coverage.run] source =
["django_strawberry_framework"]` with `fail_under = 100`, and coverage's
source mode reports **never-imported files at 0%**. The stub has exactly
one executable statement and no test imports it, so any full-suite run
between now and Slice 1 fails the coverage gate — and a silently red gate
reads as a regression to whoever hits it first
(`tests/extensions/__init__.py` is docstring-plus-comment only, zero
executable statements, coverage-neutral either way).

Two honest options; pick one explicitly rather than leaving it implicit:

1. **(Recommended)** Add one guard test now — `pytest.raises(NotImplementedError)`
   around `importlib.import_module("django_strawberry_framework.extensions.debug")`.
   Five lines, it pins the fail-loud contract the stub's docstring promises,
   it is exactly the raise-path unit test the live-first mandate carves out
   for unreachable-live behavior, and it is deleted with the stub when
   Slice 1 replaces it.
2. State in the stub's TODO that the coverage gate is expected-red until
   Slice 1, so nobody chases a phantom regression.

Related: the file-level `# ruff: noqa: ERA001` is appropriate for a
pseudocode-comment stub, but it must leave with the stub — the real Slice-1
module should not need commented-out-code suppression. Worth one word in
the TODO so it isn't carried forward by inertia.

### F3 — P2 (ordering): kanban tracked-path insertion breaks the tuple's sort order

`examples/fakeshop/apps/kanban/constants.py` inserts
`"examples/fakeshop/test_query/test_debug_extension_api.py"` **after**
`test_debug_toolbar_api.py`, but `extension` sorts before `toolbar` — this
is now the only unsorted adjacent pair in an otherwise fully sorted
`TRACKED_FILE_PATHS` tuple (verified programmatically across the whole
tuple). Move the line up one position. The four package/test additions and
both `TRACKED_DIRECTORY_PATHS` additions are correctly placed.

Adjacent observation: the spec's affected-files table implies this
constants edit (the Slice-2 `TREE.md` row depends on the
`TrackedPath.is_current` updates it feeds) but never lists
`kanban/constants.py` itself. A one-line table addition would close the
gap between "files the diff touches" and "files the spec names".

### F4 — P2 (misleading rationale): the traceback justification states a false constraint

`extensions/debug.py` stub, section 5:

> The explicit traceback is required because serialization occurs after
> the original except block.

The *pin* (three explicit arguments,
`traceback.format_exception(type(exc), exc, exc.__traceback__)`) is fine —
explicit and floor-proof, and the spec's D4 requires it. The *reason* is
wrong: `exc.__traceback__` persists on the exception object, so even the
one-argument `format_exception(exc)` form works after the except block on
every supported Python. What actually breaks post-except is the
ambient-state family — `traceback.format_exc()` / `sys.exc_info()` — which
is empty once the handler exits. State that as the reason, or a future
reader will cargo-cult a constraint that doesn't exist and resist the
one-argument form for the wrong reason if the style ever changes.

## Informational notes (no action required, recorded so nobody "fixes" them)

- **N1 — `_ActiveCapture` immutability vs "increment".** Stub section 2
  lists `_ActiveCapture(saved_force_debug_cursor, depth)` among the
  "small immutable private records", but section 3 says
  "replace/increment state to depth + 1". "Replace" is the operative word
  — if an implementer reads "increment" as a mutable `depth` field, the
  immutability claim dies silently. One clarifying phrase ("replace with a
  new record at depth + 1") removes the ambiguity. Test anchor 15's
  "synchronize ... until coordinator depth is 2" reads private coordinator
  state, which is consistent with the mechanics suite's declared
  private-helper import rule.
- **N2 — TypedDicts re-spell the wire keys, and that is spec-blessed.**
  Stub section 1's `_DebugSQLRow` / `_DebugExceptionRow` / `_DebugPayload`
  TypedDicts spell the six SQL keys, three exception keys, and two payload
  keys a second time, next to D4/D5's "serializer/builder is the single
  source of the wire spelling". This is not a violation: the spec's D-N8
  explicitly allows "private `TypedDict`s and the small internal state
  records ... where they aid static readability" — annotation-only
  duplication, no runtime shape. Recorded so a future DRY sweep neither
  deletes the TypedDicts nor "consolidates" the serializer literals into
  them.

## Verified-correct claims (checked against source, not just the spec)

Everything below was confirmed against the installed
`strawberry-graphql==0.316.0` and Django sources; the skeleton can be
trusted on these points.

1. **Zero-argument construction, post-assignment of `execution_context`**
   (stub §8; mechanics anchor 8). `Schema.get_extensions` instantiates
   class-form entries with zero arguments
   (`strawberry/schema/schema.py:392-394`, `ext()`), then the execute paths
   assign `extension.execution_context = execution_context` before
   creating the runner (`schema.py:594`, `:701`, `:924` — all three
   execution colors). `SchemaExtension.__init__` accepts an *optional*
   `execution_context` kwarg and its body is literally `...`
   (`strawberry/extensions/base_extension.py:27-29`) — it binds nothing.
   The stub's "do not claim `SchemaExtension.__init__` binds that context"
   is exactly right, and the spec's Revision-7 D6/Decision-7 wording now
   agrees.
2. **Merge semantics trio** (stub §9; mechanics anchors covering
   precedence/overlay/replacement, spec scenario 14). List-order
   later-wins merge: `data.update(extension.get_results())` in extension
   order (`strawberry/extensions/runner.py:43-51` sync, `:53-60` async).
   Async-only final overlay: `data.update(ctx.extensions_results)` runs
   *after* the extension loop (`runner.py:59`) and the sync variant has no
   equivalent — the anchor's "assert the sync runner has no equivalent
   overlay" is a real asymmetry. Replacement, not merge:
   `result.extensions = await extensions_runner.get_extensions_results(...)`
   (`schema.py:565`) assigns over any pre-existing map, and the sync paths
   construct fresh `ExecutionResult(extensions=...)` objects
   (`schema.py:741`, `:763`, `:813`, `:818`).
3. **The conditional double-call path** (mechanics anchor 9, spec
   scenario 11). Structurally confirmed in `schema.py:612-672`: a
   validation failure `return await self._handle_execution_result(...)`
   sits *inside* `async with extensions_runner.operation():`, so the
   return expression (first `get_results` call) evaluates before
   `__aexit__` runs teardown; if teardown then raises, the
   `except Exception` handler calls `_handle_execution_result` a second
   time with a coerced `PreExecutionError` — second `get_results` call,
   stash now present. The anchor's insistence that the double call is tied
   to this specific path ("separately prove a generic recovery path does
   not automatically imply two calls") matches the control flow.
4. **`callproc()` exclusion** (stub §4). Django's `CursorDebugWrapper`
   carries the upstream comment "XXX callproc isn't instrumented at this
   time" and wraps only `execute` / `executemany`
   (`django/db/backends/utils.py:118+`). Already documented in the spec's
   Edge cases; the stub restates it faithfully.
5. **`finalize_django_types()` per-build calls are safe** (live anchor).
   The function entry-guards on `registry.is_finalized()`
   (`django_strawberry_framework/types/finalizer.py:575+`), so "run it
   before each probe schema build" costs a no-op after the first build in
   a reloaded registry. Safe as written.
6. **Probe URLconf activation** (live anchor). `pytest-django>=4.5.2` is a
   dev dependency, so the module-level
   `pytestmark = pytest.mark.urls(__name__)` shape is available; it
   replaces exactly the per-request `override_settings(ROOT_URLCONF)` /
   `clear_url_caches()` blocks `test_multi_db.py:160/194` repeats, which is
   the single-siting the spec's D3 now pins.
7. **Slice numbering on every doc anchor matches the spec table 1:1.**
   `CHANGELOG.md` → 3; `GOAL.md` criterion-7 rescope → 2; `README.md` /
   `docs/README.md` / `TODAY.md` status rewrites → 3;
   `config/schema.py` docstring → 2; the strawberry `>=0.316.0` floor → 1
   (with the package version explicitly deferred); the version quintet
   (`pyproject` + `__version__` + `tests/base/test_init.py` + glossary
   version row + `uv.lock` root entry) → 3, and the root-`__init__` anchor
   correctly repeats the no-root-export rule (Decision 5). The CHANGELOG
   anchor's "edit grant, not permission to write early" framing matches
   the spec's Slice-3 grant language.
8. **Scenario coverage is complete in both directions.** Live anchors 1–7
   map onto the spec's request-driving scenarios 1–7 (including the
   `isSelect`-filter-never-positional rule, the `settings.DEBUG is False`
   pre-assertion, the optimizer singleton-factory composition shape, and
   the happy-path-only `_debug` accessor with absence tests reading the
   envelope directly). Mechanics anchors map onto spec scenarios 8–15,
   including the Revision-7 additions (merge precedence/replacement,
   nested-sync attribution). The floor-run anchor keeps node-id selection,
   never a copied script. No spec scenario is orphaned; no anchor invents
   an unspecified scenario.
9. **Coordinator and serializer pseudocode match the DRY pins.**
   Connection-object-identity keying (never alias), lock covering the
   state transition and flag write together, immutable snapshot records
   consumed at teardown (never a second `connections.all()` positional
   match), the `min(snapshot, len(entries))` clamp, fresh containers per
   operation, the immutable class-level `_payload = None` sentinel with
   instance shadowing, `{} if payload is None else {"debug": payload}`,
   wire keys as serializer literals, `_SLOW_QUERY_SECONDS = 10` with
   strict `>` (anchor: False at exactly 10.0), `str(type(exc))` /
   stripped-lowercase `select` sniff, executemany rows verbatim with
   `isSelect` False, and imports restricted to stdlib + `django.db` +
   `graphql` + `strawberry.extensions` — each checked against D4–D6,
   D-N6/D-N8, and Decisions 4/7/8/10.

## Required edits before Slice 1

1. Rewrite live anchor 3 to the grant-`add_item`-on-top shape
   (`test_client_api.py:142` precedent); do not imply `create_users`
   yields a mutation-permissioned user (F1).
2. Decide the stub-coverage posture: add the five-line
   `pytest.raises(NotImplementedError)` import guard (recommended) or
   state the expected-red gate in the stub TODO (F2). Note the `ERA001`
   suppression leaves with the stub.
3. Reorder `test_debug_extension_api.py` above `test_debug_toolbar_api.py`
   in `TRACKED_FILE_PATHS`; optionally add `kanban/constants.py` to the
   spec's affected-files table (F3).
4. Fix the traceback rationale to name the real constraint (ambient
   `sys.exc_info()` state, not the exception's own `__traceback__`) (F4).
5. Optional wording: "replace with a new record at depth + 1" in stub §3
   (N1).

No new production abstraction, dependency, or test helper is warranted by
anything in this diff — the skeleton already refuses all of them in the
right places.
