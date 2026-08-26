# Bug hunt: 0.0.14

Status: in-progress
Mode: autonomous
Baseline commit: `b99484b339ab871cd4b0259cea9de9a312c8917b`

## Concurrent dirty inventory (Worker 0 note)

Pre-existing concurrent work NOT owned by this hunt — never attribute to an item, never revert,
never absorb into a fix: modified `pyproject.toml` (dynamic-version edit landed mid-setup by another
session; also broke `scripts/bug_hunt.py::_pyproject_version`, worked around with
`--target-release 0.0.14`), `django_strawberry_framework/exceptions.py`,
`django_strawberry_framework/scalars.py`, `tests/filters/test_base.py`,
`tests/filters/test_factories.py`, `tests/filters/test_inputs.py`, `tests/test_exceptions.py`,
`tests/test_resource_policy.py`, `tests/test_scalars.py`, `tests/test_schema.py`,
`tests/test_sets_mixins.py`; untracked `docs/review/rev-*.md`, `docs/review/review-0_0_14.md`,
`tests/mutations/test_operations.py`. Item-scoped diffs are measured against each item's recorded
cycle baseline (working tree at dispatch), not against HEAD alone.

Worker 0 housekeeping (2026-08-25): removed ten stale untracked scratch dirs under
`docs/bug_hunt/temp-tests/` left by the PRIOR, closed 0.0.14 hunt run (dated Aug 22; its progress
file was since deleted): keyset_window_math, package_integration, permissions_sessions, querysets,
resolvers_async_parity, resource_policy_budget, stress, views, write_transaction,
write_values_inputs — so live dispatches cannot collect dead probes.

## Package questions

No maintainer-authored probing questions were supplied. Explore the live source freely; shadow inputs are orientation only.

## How to hunt one file
Each item uses one source file as its entry point into the live system. The
target is narrow; the investigation and root-cause fix may cross files.

- Read the shadow overview and stripped source for baseline orientation, then
  read the complete live target. Shadow markers and stripped line numbers are
  never authoritative.
- Trace callers, dependencies, state, framework hooks, tests, examples, and
  public contracts far enough to understand the target's real behavior. Clean
  layers often fail only when several reasonable assumptions stack together;
  hunt those interactions, not only suspicious local lines.
- Break things, break things, break things. Write messy scratch test files and
  be maximally destructive inside disposable scratch scope: mutate throwaway
  state, force hostile sequences, interrupt lifecycles, and try to make every
  connected layer fail.
- For every extreme, test the opposite extreme and then combine them across
  layers. Try to disprove every candidate and record only confirmed defects.
- Do not clean up scratch probes or disposable state. Report every path and
  leave it intact so Worker 0 can independently verify it and clean it up only
  after the item passes.
- Implement the root-cause fix at the layer that owns the broken invariant,
  including connected files when required. Add a permanent behavioral test for
  every production fix at the strongest tier required by `AGENTS.md`.
- After edits run `uv run ruff format .` and `uv run ruff check --fix .`.
- Report evidence, changed files, tests, and validation to Worker 0. Do not edit
  this progress file; Worker 0 independently verifies fixes and advances it.

## Hunt items

- [x] django_strawberry_framework/_boundary_ordering.py
    - Status: no-bugs
    - Cycle baseline: HEAD `b99484b3` + concurrent dirty inventory above (dispatch 2026-08-25).
    - Result: No bugs. Evidence: live target + both writers/readers traced (`views.py::_RequestBodyBoundaryMixin.as_view`, `middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware.process_view`); Django 6.1 `CsrfViewMiddleware.process_view` truthiness contract executed; matrix discharged (5/5 probed or reasoned inapplicable); candidates disproved (head/get aliasing parity, sandwiched-middleware over-strictness, async override sabotage — all coherent with stated contracts). Scratch: 25 probes green; permanent tiers re-run by W0: tests/test_views.py 222 passed, fakeshop test_transport_api.py 77 passed. Concurrent session expanded its footprint mid-item (AGENTS.md, __init__.py, scripts/bug_hunt.py, test_bug_hunt.py, test_init.py, uv.lock now also dirty) — unrelated, preserved.
    - Verification: Passed. W0 independently re-ran scratch suite (25 passed) and full tests/test_views.py (222 passed) on the live tree; confirmed zero production changes by this item (diff vs cycle baseline shows only pre-existing concurrent dirt).
    - Cleanup: Removed docs/bug_hunt/temp-tests/boundary_ordering/ (5 probe files + __pycache__); unrelated/concurrent work preserved.
    - docs/shadow/current/django_strawberry_framework___boundary_ordering.stripped.py
    - docs/shadow/current/django_strawberry_framework___boundary_ordering.overview.md
    - Prompt:
        - Use django_strawberry_framework/_boundary_ordering.py as the entry point. Read docs/shadow/current/django_strawberry_framework___boundary_ordering.stripped.py and docs/shadow/current/django_strawberry_framework___boundary_ordering.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/_cross_web_patches.py
    - Status: no-bugs
    - Cycle baseline: HEAD `b99484b3` + concurrent dirty inventory above; items 1 closed no-bugs with zero production changes (dispatch 2026-08-25).
    - Result: No bugs. Evidence: upstream cross-web 0.7.0 read from .venv matches the docstring-pinned shape (patch aimed correctly, not stale); sole consumer path traced (strawberry sync_base_view.parse_http_body -> HTTPException translation); full encoding matrix executed over the wire on 4 mounts x 2 patch states reproducing every docstring claim; four-state joint-pair square pinned; reload/idempotence self-heal verified; package-mount constancy held. Matrix discharged 5/5.
    - Verification: Passed. W0 independently re-ran scratch suite + permanent tiers: tests/test_cross_web_patches.py 14 passed; wire matrix passes solo. W0 additionally diagnosed a combined-run ordering failure between scratch files: adapter_matrix axis-5 leaves the patch uninstalled after a disabling-config apply() (pytest-django restores settings, not class attributes), so wire_parity's restore-bookkeeping assert sees False -- scratch-owned destructive state per HUNT.md, NOT a package defect (the assert's False answer was factually correct; apply()'s one-shot load-time contract holds; no auto-reheal promised or needed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/cross_web_patches/ (3 probe files); unrelated/concurrent work preserved.
    - docs/shadow/current/django_strawberry_framework___cross_web_patches.stripped.py
    - docs/shadow/current/django_strawberry_framework___cross_web_patches.overview.md
    - Prompt:
        - Use django_strawberry_framework/_cross_web_patches.py as the entry point. Read docs/shadow/current/django_strawberry_framework___cross_web_patches.stripped.py and docs/shadow/current/django_strawberry_framework___cross_web_patches.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/_django_patches.py
    - Status: no-bugs
    - Cycle baseline: HEAD `b99484b3` + concurrent dirty inventory above; items 1-2 closed no-bugs with zero production changes (dispatch 2026-08-25). Concurrent session additionally dirtied docs/SPECS/spec-030-connection_field-0_0_9.md and tests/forms/test_sets.py mid-item — unrelated, preserved.
    - Result: No bugs. Evidence: installed Django 6.1 `_remove_databases_failures` body matches the audited connection-feature pin via the module's own dedent+compare path; pins also verified against real 5.2.x/6.0.x sources (no spurious drift raise on any supported version); three-tier validation ordering proven to never half-install; reimplemented teardown behaviorally identical to upstream except the two documented strictly-defensive divergences. Matrix discharged 5/5 (descriptor shapes/signatures, delattr-vs-None vs absent symbols, drift lexical boundaries, hostile method-list surfaces with upstream-parity exception types, delattr'd settings). Multi-alias matrices in both DB modes; 8-thread concurrent apply(); reload-window fail-loud + heal.
    - Verification: Passed. W0 re-ran scratch+permanent (72 passed, 1 skipped default mode; 37 passed FAKESHOP_SHARDED=1) and independently reproduced pin fidelity through `_validate_upstream_shape`'s exact comparison (initial raw-substring check was methodologically wrong — dedent semantics — corrected before concluding).
    - Cleanup: Removed docs/bug_hunt/temp-tests/django_patches/ (3 probe files + __pycache__); unrelated/concurrent work preserved.
    - docs/shadow/current/django_strawberry_framework___django_patches.stripped.py
    - docs/shadow/current/django_strawberry_framework___django_patches.overview.md
    - Prompt:
        - Use django_strawberry_framework/_django_patches.py as the entry point. Read docs/shadow/current/django_strawberry_framework___django_patches.stripped.py and docs/shadow/current/django_strawberry_framework___django_patches.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/_request_body.py
    - Status: verified
    - Cycle baseline: HEAD `b99484b3` + concurrent dirty inventory above; items 1-3 closed no-bugs (dispatch 2026-08-25).
    - Result: Fixed Medium. `_measured_remaining` classified a stream reporting positions but having NO `seek` method as CORRUPTED instead of UNMEASURABLE: the doomed end-seek raised AttributeError, the request was refused 413 despite nothing having moved, and the log falsely claimed the probe moved the stream. Reachable when consumer middleware installs a forward-only position-reporting body stream (both production Django streams unaffected). Fix: guarded `_lacks_seek` helper consulted after the position gates -> UNMEASURABLE -> bounded read; seek-present-but-failing stays conservative CORRUPTED. Files: `django_strawberry_framework/_request_body.py` (+42, incl. docstring bullet), `tests/test_views.py` (purely additive hunks: 3 tests x sync/async views + 2 hostile fixture streams).
    - Verification: Passed. W0 temp-reverted production file -> 4/6 new permanent rows fail pre-fix (2 unreadable-attribute rows correctly pass both ways); restored -> tests/test_views.py 229 passed with _request_body.py at 100% module coverage; fakeshop test_transport_api.py 77 passed. W0's own attacks: absent seek / explicit seek=None -> UNMEASURABLE with provably unmoved stream; hostile raising capability read -> conservative CORRUPTED; non-callable seek -> contained fail-closed rung-4 path. Concurrent-session marker-stamping hunks in tests/test_views.py identified and excluded from item scope.
    - Cleanup: Removed docs/bug_hunt/temp-tests/request_body/ (Worker-1 probes + Worker-0 verify probe); unrelated/concurrent work preserved.
    - docs/shadow/current/django_strawberry_framework___request_body.stripped.py
    - docs/shadow/current/django_strawberry_framework___request_body.overview.md
    - Prompt:
        - Use django_strawberry_framework/_request_body.py as the entry point. Read docs/shadow/current/django_strawberry_framework___request_body.stripped.py and docs/shadow/current/django_strawberry_framework___request_body.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/_strawberry_patches.py
    - Status: verified
    - Cycle baseline: HEAD `b99484b3` + concurrent dirty inventory + item-4 fix (dispatch 2026-08-25). Iteration note: first Worker-1 dispatch was cancelled mid-flight by an environment interruption after implementing fixes + partial probes; re-dispatch re-derived, verified the inherited footprint, and completed the hunt. Concurrent maintainer advanced HEAD to `5564f92b` (docs commits) during the item — snapshot baseline stays `b99484b3`, live tree authoritative.
    - Result: Fixed Medium x2 (inherited from cancelled sibling, independently re-proved). (1) RecursionError escaped upstream `parse_json` as unhandled 500 on pathologically nested bodies (~150 KB here) at all eight call sites; now translated to the same controlled HTTPException 400 via new shared `_translated_parse_json`, also wired into GET variables/extensions parses. (2) RecursionError escaped the upload utility's unconditional copy.deepcopy on valid-JSON operations nested past the recursion limit (~KB); multipart delegates' translation tuple gained RecursionError with provenance scoping keeping it client-input-only. Files: `_strawberry_patches.py`, `tests/test_strawberry_patches.py` (+6), `examples/fakeshop/test_query/test_transport_api.py` (+3 wire rows), `test_products_api.py` (+2).
    - Verification: Passed. W0 temp-reverted production -> 5 deep/nested permanent tests fail pre-fix; restored -> tests/test_strawberry_patches.py + test_views.py 290 passed, module 100% across suite (line 416 covered via tests/test_apps.py reload tier); live tiers 202 passed. W0's own attacks: depth sweep 800/1500/20000 over live /graphql wire -> controlled 400s; __cause__ provenance preserved; deep GET variables -> 400; deep multipart map -> controlled.
    - Cleanup: Removed docs/bug_hunt/temp-tests/strawberry_patches/ (10 sibling/re-dispatch probe files + W0 verify probe; one sibling instrument noted broken-at-120k-depth was scratch-only, superseded by permanent proofs).
    - docs/shadow/current/django_strawberry_framework___strawberry_patches.stripped.py
    - docs/shadow/current/django_strawberry_framework___strawberry_patches.overview.md
    - docs/shadow/current/django_strawberry_framework___strawberry_patches.stripped.py
    - docs/shadow/current/django_strawberry_framework___strawberry_patches.overview.md
    - Prompt:
        - Use django_strawberry_framework/_strawberry_patches.py as the entry point. Read docs/shadow/current/django_strawberry_framework___strawberry_patches.stripped.py and docs/shadow/current/django_strawberry_framework___strawberry_patches.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/apps.py
    - Status: no-bugs
    - Cycle baseline: HEAD `b99484b3` + working tree at dispatch 2026-08-25 (concurrent maintainer advancing HEAD with docs commits). Iteration note: first dispatch cancelled mid-flight by environment interruption after partial probes; re-dispatch finished the interrupted probe, completed the matrix.
    - Result: No bugs. Evidence: 6-statement dispatcher fully executable-pinned — dispatch order django->strawberry->cross_web; per-applier self-gating (global/per-dep matrix incl. delattr'd settings); idempotence/self-heal (ready x2/x3, revert-under-disable heals); import isolation; populate end-to-end (default/disabled/duplicate/no-apps/instance-entry/config-class-path); midway-raising applier leaves exact applied prefix then heals; 8-thread race converges; missing-dep fail-loud contract holds. Matrix discharged (axis 3 reasoned inapplicable: no text scanning).
    - Verification: Passed. W0 reran scratch+permanent (45 passed; 104 passed across the four patch/app tiers); confirmed zero production footprint (git diff empty on target + test_apps.py). Two leads recorded for the pending conf.py item: __class__-spoofing liar bool passes isinstance and silently disables; hostile-Mapping iteration escapes as raw RuntimeError instead of typed ConfigurationError — both conf.py-owned boundaries, deferred to that item's dispatch.
    - Cleanup: Removed docs/bug_hunt/temp-tests/apps/ (9 files + __pycache__); unrelated/concurrent work preserved.
    - docs/shadow/current/django_strawberry_framework__apps.stripped.py
    - docs/shadow/current/django_strawberry_framework__apps.overview.md
    - docs/shadow/current/django_strawberry_framework__apps.stripped.py
    - docs/shadow/current/django_strawberry_framework__apps.overview.md
    - Prompt:
        - Use django_strawberry_framework/apps.py as the entry point. Read docs/shadow/current/django_strawberry_framework__apps.stripped.py and docs/shadow/current/django_strawberry_framework__apps.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/auth/mutations.py
    - Status: no-bugs
    - Cycle baseline: HEAD `b99484b3` + working tree at dispatch (concurrent maintainer advancing HEAD to a12c6422; re-checked live). Items 1-6 closed: four no-bugs, two verified Medium fixes. Iteration note: two successive Worker-1 dispatches cancelled mid-flight by environment interruptions, each leaving an unreported production diff (seam-factory refactor of the register rider). Worker-0 audited the inherited diff directly against live source.
    - Result: No bugs. Evidence: hand-spelled Register rider pair already carries the family's correct four-parameter seam signature (cls, info, *, data, id) and the one-boundary async contract (run_in_one_sync_boundary, thread_sensitive=True), identical to the factory's make_resolver_entries output via run_pipeline_async; the only behavioral delta (UNSET-default tolerance on a direct call without id) is unreachable through the field dispatcher which always passes data= and id=. Differential wire matrices (p6) printed byte-identical across both trees: sync+async success, duplicate-username, weak-password, null-email, surrogate-password, over-column and long-password cases all identical; seam-provenance observations confirm the async boundary and transaction semantics are the same. 43 scratch probes (p1-p6) all green — config/transport, hostile backends/gates, register shape matrix, login concurrency, live wire — plus permanent tiers. The inherited seam-factory diff is a DRY/style improvement with no confirmed defect, so per HUNT.md not applied.
    - Verification: Passed. W0 reran every leftover scratch probe individually (11+10+11+2+6+3 = 43 passed) and independently executed the differential report (p6) confirming has_module_entries=False and direct_call_without_id TypeError are the only head-vs-fixed deltas — both unreachable. W0 also reran permanent auth tiers: tests/auth 142 passed; examples/fakeshop/test_query/test_auth_api.py 20 passed. Confirmed zero production changes retained for this item (working tree matches HEAD; inherited diff deliberately not kept). Matrix discharged (all 5 axes probed via p1-p6).
    - Cleanup: Removed docs/bug_hunt/temp-tests/auth_mutations/ (6 probe files + __pycache__); unrelated/concurrent work preserved.
    - docs/shadow/current/django_strawberry_framework__auth__mutations.stripped.py
    - docs/shadow/current/django_strawberry_framework__auth__mutations.overview.md
    - docs/shadow/current/django_strawberry_framework__auth__mutations.stripped.py
    - docs/shadow/current/django_strawberry_framework__auth__mutations.overview.md
    - Prompt:
        - Use django_strawberry_framework/auth/mutations.py as the entry point. Read docs/shadow/current/django_strawberry_framework__auth__mutations.stripped.py and docs/shadow/current/django_strawberry_framework__auth__mutations.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/auth/queries.py
    - Status: verified
    - Cycle baseline: HEAD `b99484b3` + working tree at dispatch (concurrent maintainer at a12c6422; re-checked live). Items 1-7 closed: five no-bugs, two verified Medium fixes. Previous item 7 (auth/mutations) had been closed no-bugs after Worker-0 audit of its seam refactor; this item found two real defects whose root cause lives in auth/mutations.py — allowed cross-file fix per HUNT.md.
    - Result: Fixed Medium + Low (both rooted in `auth/mutations.py::_authenticated_actor_or_none` / `_make_auth_field`, discovered through `auth/queries.py` entry point). (1) Medium: hostile `request.user` descriptor or `user.is_authenticated` raising TypeError/ValueError/AttributeError/KeyError/IndexError escaped as unhandled top-level GraphQLError with raw hostile message instead of stable anonymous `null` (fail-closed nullable contract). Affects `current_user` and `logout.ok` via shared helper. (2) Low: `_make_auth_field` forwarded `directives` without validating shape — bare string iterated char-wise then crashed late as AttributeError on SDL print, and hostile `__iter__` raising mid-iteration escaped as raw ValueError/TypeError instead of typed ConfigurationError. Files: `django_strawberry_framework/auth/mutations.py` (root-cause owner: +54 lines — import inspect, safe repr, directives validation + wrap, authenticated-actor containment with callable/awaitable handling), `tests/auth/test_queries.py` (+52 lines: 2 permanent tests).
    - Verification: Passed. W0 temp-reverted production (kept new tests) → both hostile tests fail pre-fix (hostile user → GraphQLError, hostile directives → ValueError not ConfigurationError); restored → 118 auth tests passed (15 queries incl. 2 new + 103 mutations), 39 scratch probes passed, 20 live auth_api passed. W0 additionally verified that OperationalError and other non-contained exceptions still propagate (not swallowed) and that normal authenticated me still returns. Coverage: auth/queries.py 100%, auth/mutations.py fix lines covered (overall 53% with only this tier, remaining uncovered lines belong to other auth surfaces not exercised by this item). Concurrent-dirty files (filters/sets, orders/inputs, schema, etc.) identified and excluded from item scope.
    - Cleanup: Removed docs/bug_hunt/temp-tests/auth_queries/ (6 probe files + __pycache__ + W0 verify probe); unrelated/concurrent work preserved.
    - docs/shadow/current/django_strawberry_framework__auth__queries.stripped.py
    - docs/shadow/current/django_strawberry_framework__auth__queries.overview.md
    - docs/shadow/current/django_strawberry_framework__auth__queries.stripped.py
    - docs/shadow/current/django_strawberry_framework__auth__queries.overview.md
    - Prompt:
        - Use django_strawberry_framework/auth/queries.py as the entry point. Read docs/shadow/current/django_strawberry_framework__auth__queries.stripped.py and docs/shadow/current/django_strawberry_framework__auth__queries.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/auth/sessions.py
    - Status: verified
    - Cycle baseline: HEAD `b99484b3` + working tree at dispatch (concurrent at a12c6422). Items 1-8 closed: six no-bugs, three verified fixes (items 4: Medium, 5: Medium x2, 8: Medium+Low with cross-file root cause).
    - Result: Fixed High. 12 exception-containment escapes in `auth/sessions.py` now fail closed as `ConfigurationError` (10 initial + 2 revision). Files: `django_strawberry_framework/auth/sessions.py` (+182, `_safe_transport_label` helper, guarded `isinstance`/`scope`/`scope_type`/`transport.value`/`isinstance`/`lock`/`issubclass`), `tests/auth/test_sessions.py` (+366, 27 new permanent tests across two iterations, 53 total, module 136 stmts 100%).
    - Verification: Passed. W0 independently re-ran `probe_hostile_scope.py` 15/15 PASS; hostile `__class__` → `ConfigurationError` (was `TypeError`), hostile `transport.value` → `ConfigurationError` (was `ValueError`), body `ValueError`/`CancelledError` still propagate correctly through `scope_session_lock`, lock release verified; `tests/auth/test_sessions.py` 53 passed 100% on `auth/sessions.py` (136 stmts), `tests/auth` 171 passed; `ruff format` 432 unchanged, `ruff check` pass. Pre-fix probe showed 10 DEFECT, post-fix 0. New guards are at the correct owning layer (`auth/sessions.py`).
    - Cleanup: Removed docs/bug_hunt/temp-tests/auth_sessions/ (probe_hostile_scope.py, test_worker0_verify.py, __pycache__); unrelated/concurrent work preserved (mutations/schema/utils_sessions/etc. remain dirty per cycle baseline).
    - docs/shadow/current/django_strawberry_framework__auth__sessions.stripped.py
    - docs/shadow/current/django_strawberry_framework__auth__sessions.overview.md
    - Prompt:
        - Use django_strawberry_framework/auth/sessions.py as the entry point. Read docs/shadow/current/django_strawberry_framework__auth__sessions.stripped.py and docs/shadow/current/django_strawberry_framework__auth__sessions.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Iteration: 2 — W0 revision 2026-08-26 added `isinstance`/`transport.value` guards + 8 tests; verified 2026-08-26.

- [x] django_strawberry_framework/conf.py
    - Status: verified
    - Cycle baseline: HEAD `b99484b3` + working tree at dispatch (concurrent at a12c6422). Items 1-9 closed: seven no-bugs, four verified fixes (items 4,5,8,9).
    - Result: Fixed Medium+Medium. (1) `type(configured) is bool` defeats `__class__`-spoofing liar bool that bypassed `isinstance` and silently disabled patches; (2) guarded `isinstance`/`dict()`/`__iter__`/`__getitem__`/`isinstance(name,str)` with defensive `dict` copy in `_normalize_user_settings` + `Settings.__getattr__` + `upstream_patches_enabled` so hostile `Mapping` iteration never escapes as `RuntimeError`/`ValueError`. Files: `django_strawberry_framework/conf.py` (+~60, `type is bool/dict` checks, `dict` copy sanitization, `try/except → ConfigurationError`), `tests/base/test_conf.py` (+240, 10 new tests, 58 total, 143 stmts 100%).
    - Verification: Passed. W0 re-ran `tests/base/test_conf.py` 58 passed 100% on conf.py (143 stmts), `probe_axes.py` 9/9 PASS, `probe_matrix.py` 16/16 PASS; `tests/test_apps.py` 8 passed; W0 additional probes: `EvilMapping` hostile `__getitem__` after copy → `ConfigurationError`, generator not mapping → `ConfigurationError`, `HostileIterOnly` dict-subclass hostile `__iter__` correctly sanitized via `dict()` copy (exact `dict` return is safe), one-shot generator neutralized via defensive copy. `ruff format` 1 file reformatted, `ruff check` 4 fixed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/conf/ (probe_axes.py, probe_matrix.py, __pycache__); unrelated/concurrent work preserved.
    - docs/shadow/current/django_strawberry_framework__conf.stripped.py
    - docs/shadow/current/django_strawberry_framework__conf.overview.md
    - Prompt:
        - Use django_strawberry_framework/conf.py as the entry point. Read docs/shadow/current/django_strawberry_framework__conf.stripped.py and docs/shadow/current/django_strawberry_framework__conf.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/connection.py
    - Status: verified
    - Cycle baseline: HEAD `b99484b3` + working tree at dispatch (concurrent at a12c6422). Items 1-10 closed: seven no-bugs, five verified fixes (items 4,5,8,9,11).
    - Result: Fixed Medium (5 gaps: directives string/hostile → `ConfigurationError`; `query.is_sliced`/`order_by` hostile → `GraphQLError`; `effective_connection_order`/`qs.order_by(*ordered)` hostile → `GraphQLError`; `_keyset_order_ref` hostile → `None`; pagination `ValueError`/`TypeError` → `GraphQLError`). Files: `django_strawberry_framework/connection.py` (+~112, `ConfigurationError`/`GraphQLError` containment at 7 sites), `tests/test_connection.py` (+363, 11 new tests, 89 total), `examples/fakeshop/test_query/test_connection_pagination_api.py` (new, 6 live `/graphql` pagination containment tests).
    - Verification: Passed. W0 re-ran `tests/test_connection.py` 89 passed, `connection.py` new branches covered, `examples/fakeshop/test_query/test_connection_pagination_api.py` 6 passed; `ruff format/check` 2 fixed; scratch `test_probe_directives.py`/`test_probe_live_pagination.py` 17/19 passed — 2 failures are scratch-construction defects (bare `OverCapNode` type `TypeError` and `test_pagination_first_last_both_hostile` probe defect) NOT package escapes, confirmed by live tier passing; `tests/test_relay_connection.py` 116 passed, `tests/test_keyset_connection.py` 20 passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/connection/ (2 probe files + __pycache__); unrelated/concurrent work preserved.
    - docs/shadow/current/django_strawberry_framework__connection.stripped.py
    - docs/shadow/current/django_strawberry_framework__connection.overview.md
    - Prompt:
        - Use django_strawberry_framework/connection.py as the entry point. Read docs/shadow/current/django_strawberry_framework__connection.stripped.py and docs/shadow/current/django_strawberry_framework__connection.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/consumers.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__consumers.stripped.py
    - docs/shadow/current/django_strawberry_framework__consumers.overview.md
    - Prompt:
        - Use django_strawberry_framework/consumers.py as the entry point. Read docs/shadow/current/django_strawberry_framework__consumers.stripped.py and docs/shadow/current/django_strawberry_framework__consumers.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/error_policy.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__error_policy.stripped.py
    - docs/shadow/current/django_strawberry_framework__error_policy.overview.md
    - Prompt:
        - Use django_strawberry_framework/error_policy.py as the entry point. Read docs/shadow/current/django_strawberry_framework__error_policy.stripped.py and docs/shadow/current/django_strawberry_framework__error_policy.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/exceptions.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__exceptions.stripped.py
    - docs/shadow/current/django_strawberry_framework__exceptions.overview.md
    - Prompt:
        - Use django_strawberry_framework/exceptions.py as the entry point. Read docs/shadow/current/django_strawberry_framework__exceptions.stripped.py and docs/shadow/current/django_strawberry_framework__exceptions.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/extensions/debug.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__extensions__debug.stripped.py
    - docs/shadow/current/django_strawberry_framework__extensions__debug.overview.md
    - Prompt:
        - Use django_strawberry_framework/extensions/debug.py as the entry point. Read docs/shadow/current/django_strawberry_framework__extensions__debug.stripped.py and docs/shadow/current/django_strawberry_framework__extensions__debug.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/extensions/error_policy.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__extensions__error_policy.stripped.py
    - docs/shadow/current/django_strawberry_framework__extensions__error_policy.overview.md
    - Prompt:
        - Use django_strawberry_framework/extensions/error_policy.py as the entry point. Read docs/shadow/current/django_strawberry_framework__extensions__error_policy.stripped.py and docs/shadow/current/django_strawberry_framework__extensions__error_policy.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/extensions/resource_policy.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__extensions__resource_policy.stripped.py
    - docs/shadow/current/django_strawberry_framework__extensions__resource_policy.overview.md
    - Prompt:
        - Use django_strawberry_framework/extensions/resource_policy.py as the entry point. Read docs/shadow/current/django_strawberry_framework__extensions__resource_policy.stripped.py and docs/shadow/current/django_strawberry_framework__extensions__resource_policy.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/filters/base.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__filters__base.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__base.overview.md
    - Prompt:
        - Use django_strawberry_framework/filters/base.py as the entry point. Read docs/shadow/current/django_strawberry_framework__filters__base.stripped.py and docs/shadow/current/django_strawberry_framework__filters__base.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/filters/factories.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__filters__factories.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__factories.overview.md
    - Prompt:
        - Use django_strawberry_framework/filters/factories.py as the entry point. Read docs/shadow/current/django_strawberry_framework__filters__factories.stripped.py and docs/shadow/current/django_strawberry_framework__filters__factories.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/filters/inputs.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__filters__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__inputs.overview.md
    - Prompt:
        - Use django_strawberry_framework/filters/inputs.py as the entry point. Read docs/shadow/current/django_strawberry_framework__filters__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__filters__inputs.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/filters/sets.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__filters__sets.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__sets.overview.md
    - Prompt:
        - Use django_strawberry_framework/filters/sets.py as the entry point. Read docs/shadow/current/django_strawberry_framework__filters__sets.stripped.py and docs/shadow/current/django_strawberry_framework__filters__sets.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/forms/converter.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__forms__converter.stripped.py
    - docs/shadow/current/django_strawberry_framework__forms__converter.overview.md
    - Prompt:
        - Use django_strawberry_framework/forms/converter.py as the entry point. Read docs/shadow/current/django_strawberry_framework__forms__converter.stripped.py and docs/shadow/current/django_strawberry_framework__forms__converter.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/forms/inputs.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__forms__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__forms__inputs.overview.md
    - Prompt:
        - Use django_strawberry_framework/forms/inputs.py as the entry point. Read docs/shadow/current/django_strawberry_framework__forms__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__forms__inputs.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/forms/resolvers.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__forms__resolvers.stripped.py
    - docs/shadow/current/django_strawberry_framework__forms__resolvers.overview.md
    - Prompt:
        - Use django_strawberry_framework/forms/resolvers.py as the entry point. Read docs/shadow/current/django_strawberry_framework__forms__resolvers.stripped.py and docs/shadow/current/django_strawberry_framework__forms__resolvers.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/forms/sets.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__forms__sets.stripped.py
    - docs/shadow/current/django_strawberry_framework__forms__sets.overview.md
    - Prompt:
        - Use django_strawberry_framework/forms/sets.py as the entry point. Read docs/shadow/current/django_strawberry_framework__forms__sets.stripped.py and docs/shadow/current/django_strawberry_framework__forms__sets.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/keyset.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__keyset.stripped.py
    - docs/shadow/current/django_strawberry_framework__keyset.overview.md
    - Prompt:
        - Use django_strawberry_framework/keyset.py as the entry point. Read docs/shadow/current/django_strawberry_framework__keyset.stripped.py and docs/shadow/current/django_strawberry_framework__keyset.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/list_field.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__list_field.stripped.py
    - docs/shadow/current/django_strawberry_framework__list_field.overview.md
    - Prompt:
        - Use django_strawberry_framework/list_field.py as the entry point. Read docs/shadow/current/django_strawberry_framework__list_field.stripped.py and docs/shadow/current/django_strawberry_framework__list_field.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/management/commands/_imports.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__management__commands___imports.stripped.py
    - docs/shadow/current/django_strawberry_framework__management__commands___imports.overview.md
    - Prompt:
        - Use django_strawberry_framework/management/commands/_imports.py as the entry point. Read docs/shadow/current/django_strawberry_framework__management__commands___imports.stripped.py and docs/shadow/current/django_strawberry_framework__management__commands___imports.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/management/commands/export_schema.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__management__commands__export_schema.stripped.py
    - docs/shadow/current/django_strawberry_framework__management__commands__export_schema.overview.md
    - Prompt:
        - Use django_strawberry_framework/management/commands/export_schema.py as the entry point. Read docs/shadow/current/django_strawberry_framework__management__commands__export_schema.stripped.py and docs/shadow/current/django_strawberry_framework__management__commands__export_schema.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/management/commands/inspect_django_type.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__management__commands__inspect_django_type.stripped.py
    - docs/shadow/current/django_strawberry_framework__management__commands__inspect_django_type.overview.md
    - Prompt:
        - Use django_strawberry_framework/management/commands/inspect_django_type.py as the entry point. Read docs/shadow/current/django_strawberry_framework__management__commands__inspect_django_type.stripped.py and docs/shadow/current/django_strawberry_framework__management__commands__inspect_django_type.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/middleware/debug_toolbar.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__middleware__debug_toolbar.stripped.py
    - docs/shadow/current/django_strawberry_framework__middleware__debug_toolbar.overview.md
    - Prompt:
        - Use django_strawberry_framework/middleware/debug_toolbar.py as the entry point. Read docs/shadow/current/django_strawberry_framework__middleware__debug_toolbar.stripped.py and docs/shadow/current/django_strawberry_framework__middleware__debug_toolbar.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/middleware/request_body.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__middleware__request_body.stripped.py
    - docs/shadow/current/django_strawberry_framework__middleware__request_body.overview.md
    - Prompt:
        - Use django_strawberry_framework/middleware/request_body.py as the entry point. Read docs/shadow/current/django_strawberry_framework__middleware__request_body.stripped.py and docs/shadow/current/django_strawberry_framework__middleware__request_body.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/mutations/fields.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__mutations__fields.stripped.py
    - docs/shadow/current/django_strawberry_framework__mutations__fields.overview.md
    - Prompt:
        - Use django_strawberry_framework/mutations/fields.py as the entry point. Read docs/shadow/current/django_strawberry_framework__mutations__fields.stripped.py and docs/shadow/current/django_strawberry_framework__mutations__fields.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/mutations/inputs.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__mutations__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__mutations__inputs.overview.md
    - Prompt:
        - Use django_strawberry_framework/mutations/inputs.py as the entry point. Read docs/shadow/current/django_strawberry_framework__mutations__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__mutations__inputs.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/mutations/operations.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__mutations__operations.stripped.py
    - docs/shadow/current/django_strawberry_framework__mutations__operations.overview.md
    - Prompt:
        - Use django_strawberry_framework/mutations/operations.py as the entry point. Read docs/shadow/current/django_strawberry_framework__mutations__operations.stripped.py and docs/shadow/current/django_strawberry_framework__mutations__operations.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/mutations/permissions.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__mutations__permissions.stripped.py
    - docs/shadow/current/django_strawberry_framework__mutations__permissions.overview.md
    - Prompt:
        - Use django_strawberry_framework/mutations/permissions.py as the entry point. Read docs/shadow/current/django_strawberry_framework__mutations__permissions.stripped.py and docs/shadow/current/django_strawberry_framework__mutations__permissions.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/mutations/resolvers.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__mutations__resolvers.stripped.py
    - docs/shadow/current/django_strawberry_framework__mutations__resolvers.overview.md
    - Prompt:
        - Use django_strawberry_framework/mutations/resolvers.py as the entry point. Read docs/shadow/current/django_strawberry_framework__mutations__resolvers.stripped.py and docs/shadow/current/django_strawberry_framework__mutations__resolvers.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/mutations/sets.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__mutations__sets.stripped.py
    - docs/shadow/current/django_strawberry_framework__mutations__sets.overview.md
    - Prompt:
        - Use django_strawberry_framework/mutations/sets.py as the entry point. Read docs/shadow/current/django_strawberry_framework__mutations__sets.stripped.py and docs/shadow/current/django_strawberry_framework__mutations__sets.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/optimizer/_context.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__optimizer___context.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer___context.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/_context.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer___context.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer___context.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/optimizer/extension.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__optimizer__extension.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__extension.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/extension.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__extension.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__extension.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/optimizer/field_meta.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__optimizer__field_meta.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__field_meta.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/field_meta.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__field_meta.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__field_meta.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/optimizer/hints.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__optimizer__hints.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__hints.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/hints.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__hints.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__hints.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/optimizer/join_taxonomy.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__optimizer__join_taxonomy.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__join_taxonomy.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/join_taxonomy.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__join_taxonomy.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__join_taxonomy.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/optimizer/lateral_fetch.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__optimizer__lateral_fetch.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__lateral_fetch.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/lateral_fetch.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__lateral_fetch.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__lateral_fetch.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/optimizer/nested_fetch.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__optimizer__nested_fetch.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__nested_fetch.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/nested_fetch.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__nested_fetch.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__nested_fetch.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/optimizer/nested_planner.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__optimizer__nested_planner.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__nested_planner.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/nested_planner.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__nested_planner.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__nested_planner.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/optimizer/plans.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__optimizer__plans.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__plans.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/plans.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__plans.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__plans.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/optimizer/predicates.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__optimizer__predicates.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__predicates.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/predicates.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__predicates.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__predicates.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/optimizer/selections.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__optimizer__selections.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__selections.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/selections.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__selections.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__selections.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/optimizer/single_parent_fetch.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__optimizer__single_parent_fetch.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__single_parent_fetch.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/single_parent_fetch.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__single_parent_fetch.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__single_parent_fetch.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/optimizer/walker.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__optimizer__walker.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__walker.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/walker.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__walker.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__walker.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/orders/base.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__orders__base.stripped.py
    - docs/shadow/current/django_strawberry_framework__orders__base.overview.md
    - Prompt:
        - Use django_strawberry_framework/orders/base.py as the entry point. Read docs/shadow/current/django_strawberry_framework__orders__base.stripped.py and docs/shadow/current/django_strawberry_framework__orders__base.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/orders/factories.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__orders__factories.stripped.py
    - docs/shadow/current/django_strawberry_framework__orders__factories.overview.md
    - Prompt:
        - Use django_strawberry_framework/orders/factories.py as the entry point. Read docs/shadow/current/django_strawberry_framework__orders__factories.stripped.py and docs/shadow/current/django_strawberry_framework__orders__factories.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/orders/inputs.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__orders__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__orders__inputs.overview.md
    - Prompt:
        - Use django_strawberry_framework/orders/inputs.py as the entry point. Read docs/shadow/current/django_strawberry_framework__orders__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__orders__inputs.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/orders/sets.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__orders__sets.stripped.py
    - docs/shadow/current/django_strawberry_framework__orders__sets.overview.md
    - Prompt:
        - Use django_strawberry_framework/orders/sets.py as the entry point. Read docs/shadow/current/django_strawberry_framework__orders__sets.stripped.py and docs/shadow/current/django_strawberry_framework__orders__sets.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/permissions.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__permissions.stripped.py
    - docs/shadow/current/django_strawberry_framework__permissions.overview.md
    - Prompt:
        - Use django_strawberry_framework/permissions.py as the entry point. Read docs/shadow/current/django_strawberry_framework__permissions.stripped.py and docs/shadow/current/django_strawberry_framework__permissions.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/registry.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__registry.stripped.py
    - docs/shadow/current/django_strawberry_framework__registry.overview.md
    - Prompt:
        - Use django_strawberry_framework/registry.py as the entry point. Read docs/shadow/current/django_strawberry_framework__registry.stripped.py and docs/shadow/current/django_strawberry_framework__registry.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/relay.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__relay.stripped.py
    - docs/shadow/current/django_strawberry_framework__relay.overview.md
    - Prompt:
        - Use django_strawberry_framework/relay.py as the entry point. Read docs/shadow/current/django_strawberry_framework__relay.stripped.py and docs/shadow/current/django_strawberry_framework__relay.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/resource_policy.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__resource_policy.stripped.py
    - docs/shadow/current/django_strawberry_framework__resource_policy.overview.md
    - Prompt:
        - Use django_strawberry_framework/resource_policy.py as the entry point. Read docs/shadow/current/django_strawberry_framework__resource_policy.stripped.py and docs/shadow/current/django_strawberry_framework__resource_policy.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/rest_framework/hook_context.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__rest_framework__hook_context.stripped.py
    - docs/shadow/current/django_strawberry_framework__rest_framework__hook_context.overview.md
    - Prompt:
        - Use django_strawberry_framework/rest_framework/hook_context.py as the entry point. Read docs/shadow/current/django_strawberry_framework__rest_framework__hook_context.stripped.py and docs/shadow/current/django_strawberry_framework__rest_framework__hook_context.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/rest_framework/inputs.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__rest_framework__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__rest_framework__inputs.overview.md
    - Prompt:
        - Use django_strawberry_framework/rest_framework/inputs.py as the entry point. Read docs/shadow/current/django_strawberry_framework__rest_framework__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__rest_framework__inputs.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/rest_framework/resolvers.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__rest_framework__resolvers.stripped.py
    - docs/shadow/current/django_strawberry_framework__rest_framework__resolvers.overview.md
    - Prompt:
        - Use django_strawberry_framework/rest_framework/resolvers.py as the entry point. Read docs/shadow/current/django_strawberry_framework__rest_framework__resolvers.stripped.py and docs/shadow/current/django_strawberry_framework__rest_framework__resolvers.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/rest_framework/serializer_converter.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__rest_framework__serializer_converter.stripped.py
    - docs/shadow/current/django_strawberry_framework__rest_framework__serializer_converter.overview.md
    - Prompt:
        - Use django_strawberry_framework/rest_framework/serializer_converter.py as the entry point. Read docs/shadow/current/django_strawberry_framework__rest_framework__serializer_converter.stripped.py and docs/shadow/current/django_strawberry_framework__rest_framework__serializer_converter.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/rest_framework/sets.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__rest_framework__sets.stripped.py
    - docs/shadow/current/django_strawberry_framework__rest_framework__sets.overview.md
    - Prompt:
        - Use django_strawberry_framework/rest_framework/sets.py as the entry point. Read docs/shadow/current/django_strawberry_framework__rest_framework__sets.stripped.py and docs/shadow/current/django_strawberry_framework__rest_framework__sets.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/routers.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__routers.stripped.py
    - docs/shadow/current/django_strawberry_framework__routers.overview.md
    - Prompt:
        - Use django_strawberry_framework/routers.py as the entry point. Read docs/shadow/current/django_strawberry_framework__routers.stripped.py and docs/shadow/current/django_strawberry_framework__routers.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/scalars.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__scalars.stripped.py
    - docs/shadow/current/django_strawberry_framework__scalars.overview.md
    - Prompt:
        - Use django_strawberry_framework/scalars.py as the entry point. Read docs/shadow/current/django_strawberry_framework__scalars.stripped.py and docs/shadow/current/django_strawberry_framework__scalars.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/schema.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__schema.stripped.py
    - docs/shadow/current/django_strawberry_framework__schema.overview.md
    - Prompt:
        - Use django_strawberry_framework/schema.py as the entry point. Read docs/shadow/current/django_strawberry_framework__schema.stripped.py and docs/shadow/current/django_strawberry_framework__schema.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/sets_mixins.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__sets_mixins.stripped.py
    - docs/shadow/current/django_strawberry_framework__sets_mixins.overview.md
    - Prompt:
        - Use django_strawberry_framework/sets_mixins.py as the entry point. Read docs/shadow/current/django_strawberry_framework__sets_mixins.stripped.py and docs/shadow/current/django_strawberry_framework__sets_mixins.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/testing/_wrap.py
    - Status: pending
    - Baseline shadow: none (path excluded from the snapshot by its 'test' path filter, not new)
    - Prompt:
        - Use django_strawberry_framework/testing/_wrap.py as the entry point. No baseline shadow exists; hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/testing/client.py
    - Status: pending
    - Baseline shadow: none (path excluded from the snapshot by its 'test' path filter, not new)
    - Prompt:
        - Use django_strawberry_framework/testing/client.py as the entry point. No baseline shadow exists; hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/testing/relay.py
    - Status: pending
    - Baseline shadow: none (path excluded from the snapshot by its 'test' path filter, not new)
    - Prompt:
        - Use django_strawberry_framework/testing/relay.py as the entry point. No baseline shadow exists; hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/types/base.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__types__base.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__base.overview.md
    - Prompt:
        - Use django_strawberry_framework/types/base.py as the entry point. Read docs/shadow/current/django_strawberry_framework__types__base.stripped.py and docs/shadow/current/django_strawberry_framework__types__base.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/types/converters.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__types__converters.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__converters.overview.md
    - Prompt:
        - Use django_strawberry_framework/types/converters.py as the entry point. Read docs/shadow/current/django_strawberry_framework__types__converters.stripped.py and docs/shadow/current/django_strawberry_framework__types__converters.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/types/definition.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__types__definition.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__definition.overview.md
    - Prompt:
        - Use django_strawberry_framework/types/definition.py as the entry point. Read docs/shadow/current/django_strawberry_framework__types__definition.stripped.py and docs/shadow/current/django_strawberry_framework__types__definition.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/types/finalizer.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__types__finalizer.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__finalizer.overview.md
    - Prompt:
        - Use django_strawberry_framework/types/finalizer.py as the entry point. Read docs/shadow/current/django_strawberry_framework__types__finalizer.stripped.py and docs/shadow/current/django_strawberry_framework__types__finalizer.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/types/relations.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__types__relations.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__relations.overview.md
    - Prompt:
        - Use django_strawberry_framework/types/relations.py as the entry point. Read docs/shadow/current/django_strawberry_framework__types__relations.stripped.py and docs/shadow/current/django_strawberry_framework__types__relations.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/types/relay.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__types__relay.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__relay.overview.md
    - Prompt:
        - Use django_strawberry_framework/types/relay.py as the entry point. Read docs/shadow/current/django_strawberry_framework__types__relay.stripped.py and docs/shadow/current/django_strawberry_framework__types__relay.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/types/resolvers.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__types__resolvers.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__resolvers.overview.md
    - Prompt:
        - Use django_strawberry_framework/types/resolvers.py as the entry point. Read docs/shadow/current/django_strawberry_framework__types__resolvers.stripped.py and docs/shadow/current/django_strawberry_framework__types__resolvers.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/utils/connections.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__utils__connections.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__connections.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/connections.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__connections.stripped.py and docs/shadow/current/django_strawberry_framework__utils__connections.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/utils/context.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__utils__context.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__context.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/context.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__context.stripped.py and docs/shadow/current/django_strawberry_framework__utils__context.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/utils/converters.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__utils__converters.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__converters.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/converters.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__converters.stripped.py and docs/shadow/current/django_strawberry_framework__utils__converters.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/utils/errors.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__utils__errors.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__errors.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/errors.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__errors.stripped.py and docs/shadow/current/django_strawberry_framework__utils__errors.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/utils/imports.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__utils__imports.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__imports.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/imports.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__imports.stripped.py and docs/shadow/current/django_strawberry_framework__utils__imports.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/utils/input_values.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__utils__input_values.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__input_values.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/input_values.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__input_values.stripped.py and docs/shadow/current/django_strawberry_framework__utils__input_values.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/utils/inputs.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__utils__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__inputs.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/inputs.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__utils__inputs.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/utils/permissions.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__utils__permissions.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__permissions.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/permissions.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__permissions.stripped.py and docs/shadow/current/django_strawberry_framework__utils__permissions.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/utils/querysets.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__utils__querysets.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__querysets.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/querysets.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__querysets.stripped.py and docs/shadow/current/django_strawberry_framework__utils__querysets.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/utils/relations.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__utils__relations.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__relations.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/relations.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__relations.stripped.py and docs/shadow/current/django_strawberry_framework__utils__relations.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/utils/sessions.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__utils__sessions.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__sessions.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/sessions.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__sessions.stripped.py and docs/shadow/current/django_strawberry_framework__utils__sessions.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/utils/strings.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__utils__strings.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__strings.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/strings.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__strings.stripped.py and docs/shadow/current/django_strawberry_framework__utils__strings.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/utils/typing.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__utils__typing.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__typing.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/typing.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__typing.stripped.py and docs/shadow/current/django_strawberry_framework__utils__typing.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/utils/write_transaction.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__utils__write_transaction.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__write_transaction.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/write_transaction.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__write_transaction.stripped.py and docs/shadow/current/django_strawberry_framework__utils__write_transaction.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/utils/write_values.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__utils__write_values.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__write_values.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/write_values.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__write_values.stripped.py and docs/shadow/current/django_strawberry_framework__utils__write_values.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/views.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__views.stripped.py
    - docs/shadow/current/django_strawberry_framework__views.overview.md
    - Prompt:
        - Use django_strawberry_framework/views.py as the entry point. Read docs/shadow/current/django_strawberry_framework__views.stripped.py and docs/shadow/current/django_strawberry_framework__views.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] Package integration
    - Status: pending
    - Prompt:
        - Hunt the final live package across boundaries, including public exports and `__init__.py` files; implement every confirmed root-cause fix.

- [ ] Final test gate
    - Status: pending
    - Owner: Worker 0
    - Prompt:
        - Run `uv run pytest`; require a passing suite and 100% configured package coverage.
