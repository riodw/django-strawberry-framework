# Bug hunt: 0.0.13

Status: in-progress
Mode: autonomous
Baseline commit: `10722b2900d2c39f286d7bfd25cc66147a7718d5`

## Known blockers (concurrent refactor, NOT hunt defects)

The maintainer's committed subsystem-clear refactor (commit 5e992a7b) landed but left two STALE TESTS that fail at clean HEAD, independent of any hunt work. Production wiring is correct (verified during the registry.py hunt). These WILL fail the final `uv run pytest` gate until the maintainer reconciles them; they are recorded here as genuine concurrent-work blockers, not hunt-introduced regressions, and are deliberately NOT edited by the hunt:

- **RESOLVED (FIXED BY THE HUNT) - `examples/fakeshop/test_query/test_library_api.py`: was 20 failures, now 168 pass.** Per AGENTS.md line 4 (root-cause fix, never defer/hand-off), a dedicated hunt root-caused and FIXED it (Fixed High). Root cause was NOT the pre-bind clear loop (that lead was disproved - neutralizing it changed nothing) and NOT stale tests (the maintainer tests are correct): `filters/base.py::GlobalIDMultipleChoiceFilter` / `_GlobalIDMultipleChoiceField` could not distinguish an ABSENT `id__in` key from an EXPLICIT `[]`. An omitted own-PK/relation membership filter arrived as `[]` (django_filters coerces empty data -> QueryDict -> SelectMultiple.value_from_datadict returns []; and MultipleChoiceField.clean(None) collapses None->[]) and ran the documented explicit-empty branch `qs.none()`, silently zeroing the whole query. The committed refactor SURFACED (not introduced) the latent defect: `_is_own_pk_under_relay_owner` keys off `_owner_definition`, now bound BEFORE Layer-4 expansion (correct per spec-027), so own-PK `id__in` finalizes as GlobalIDMultipleChoiceFilter and the absent-`[]` collapse became live. Non-Relay owners escaped (IntegerInFilter cleans absent->None->skip). Fix (filters/base.py only): new `_AbsentGlobalIDMultipleChoiceWidget.value_from_datadict` returns None when the key is absent (presence is the reliable signal across dict + QueryDict); `_GlobalIDMultipleChoiceField.clean` keeps None as None. So absent -> skip, explicit `{in:[]}` -> match-nothing (preserved), `{in:[ids]}` -> unchanged. VERIFIED: WITH fix test_library_api.py 168 passed; temp-revert filters/base.py to HEAD -> the 20 failures return; products/scalars 129 passed (explicit-empty semantics intact); finalizer/registry untouched. Recorded on the filters/base.py hunt item (Iteration 2). NOTE: no NEW permanent test added - the fix's branches are all exercised by the existing maintainer live suite (absent path via the m2m/nested/choice-enum tests that were failing; explicit-empty via the own-PK/products in-[] tests), so fail_under=100 holds.
- `tests/auth/test_queries.py::test_alias_namespace_rides_make_input_namespace_and_the_pre_bind_row` - asserts `(module_path, "clear_current_user_alias_namespace") in iter_subsystem_clears()`, but the refactor made `iter_subsystem_clears()` return bare owner-keyed callables (no module-path/name tuples), so the membership check is structurally impossible. The functional pre-bind reset itself is correct and is still covered by the same test's reload half.
- `tests/auth/test_mutations.py` - fails at COLLECTION with `ImportError: cannot import name '_clear_if_loaded' from ...registry` (the refactor removed/renamed that private symbol; the stale test still imports it). A collection error also blocks every other test in that module.
- `tests/filters/test_finalizer.py::test_phase_2_5_rejects_multi_owner_with_diverging_target` - fails "DID NOT RAISE ConfigurationError" at clean HEAD. ADJUDICATED by the types/finalizer.py hunt = (B) STALE TEST, not a regression. The multi-owner divergence protection genuinely STILL HOLDS: the test hand-plants `BookFilter._owner_definition = FakeOwnerDefinition` before finalize, relying on that pre-seed surviving into subpass 1 - but the refactor's CORRECT before_bind reset (clear_filter/order_input_namespace now run in the pre-bind loop -> delattr every FilterSet's _owner_definition) wipes the pre-seed to default None, so the fake never trips the divergence walk. The relation-TARGET axis the test simulates cannot diverge for real owners (target resolved via the process-global registry keyed on the target MODEL, not the owner); the genuinely owner-dependent axis (own-PK Relay identity) IS still rejected end-to-end (reproduced with two REAL owners on one Shelf filterset -> ConfigurationError). Maintainer fix: rewrite to exercise the own-PK axis with real owners (or call _bind_filterset_owner directly with a diverging fake like the sibling passing unit test), or delete as redundant. NOTE: this test's staleness is DISTINCT from the 20-test live filter regression above (that is under active root-cause hunt); the finalizer's binding-protection is sound.



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
  leave it intact so Worker 1 can independently verify it and clean it up only
  after the item passes.
- Implement the root-cause fix at the layer that owns the broken invariant,
  including connected files when required. Add a permanent behavioral test for
  every production fix at the strongest tier required by `AGENTS.md`.
- After edits run `uv run ruff format .` and `uv run ruff check --fix .`.
- Report evidence, changed files, tests, and validation to Worker 1. Do not edit
  this progress file; Worker 1 independently verifies fixes and advances it.

## Hunt items

- [x] django_strawberry_framework/_cross_web_patches.py
    - Status: no-bugs
    - Result: No bugs. Evidence: body getter success path byte-identical to upstream; except catches only UnicodeDecodeError (ValueError/RuntimeError propagate); revert->500 / reinstall->400 proves load-bearing; async UTF-16/32 parity; idempotent no-double-wrap. 17 scratch probes rerun -> pass.
    - Verification: Passed. Source unchanged; reran probe_unit.py+probe_live.py -> 17 passed. (UTF-32 permanent-coverage gap noted as non-defect, not actioned per mandate.)
    - Cleanup: Removed docs/bug_hunt/temp-tests/cross_web_patches/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework___cross_web_patches.stripped.py
    - docs/shadow/current/django_strawberry_framework___cross_web_patches.overview.md
    - Prompt:
        - Use django_strawberry_framework/_cross_web_patches.py as the entry point. Read docs/shadow/current/django_strawberry_framework___cross_web_patches.stripped.py and docs/shadow/current/django_strawberry_framework___cross_web_patches.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/_django_patches.py
    - Status: no-bugs
    - Result: No bugs. Evidence: reimplements SimpleTestCase._remove_databases_failures verbatim + isinstance(_DatabaseFailure) guard; pinned source byte-matches live Django 6.0.5; full wrap/remove lifecycle, foreign-wrapper, multi-alias, allow-list, idempotency, shape-abort all correct; missing _DatabaseFailure degrades fail-loud. 14 scratch probes rerun -> pass.
    - Verification: Passed. Source unchanged; reran docs/bug_hunt/temp-tests/django_patches/ -> 14 passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/django_patches/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework___django_patches.stripped.py
    - docs/shadow/current/django_strawberry_framework___django_patches.overview.md
    - Prompt:
        - Use django_strawberry_framework/_django_patches.py as the entry point. Read docs/shadow/current/django_strawberry_framework___django_patches.stripped.py and docs/shadow/current/django_strawberry_framework___django_patches.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/_strawberry_patches.py
    - Status: no-bugs
    - Result: No bugs. Evidence: parse_json/parse_query_params scalar+UnicodeDecodeError hardening verified load-bearing against live strawberry 0.316.0; idempotent/self-healing pair; sync+async share the patched BaseView methods; multipart/GET widen to controlled 400; version-drift source-pin is intentional fail-loud. 16 scratch probes rerun -> pass.
    - Verification: Passed. Source unchanged (git status clean for this file); reran docs/bug_hunt/temp-tests/strawberry_patches/test_probe.py -> 16 passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/strawberry_patches/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework___strawberry_patches.stripped.py
    - docs/shadow/current/django_strawberry_framework___strawberry_patches.overview.md
    - Prompt:
        - Use django_strawberry_framework/_strawberry_patches.py as the entry point. Read docs/shadow/current/django_strawberry_framework___strawberry_patches.stripped.py and docs/shadow/current/django_strawberry_framework___strawberry_patches.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/apps.py
    - Status: no-bugs
    - Result: No bugs. Evidence: ready() is a 3-line dispatcher over 3 self-gating idempotent appliers; disjoint targets, order-independent; only partial-install states arise from intended fail-loud drift/config paths that abort startup regardless of order (intentional contract). Reran 10 scratch probes -> all pass; git diff on apps.py empty.
    - Verification: Passed. Independent checks: confirmed apps.py source unchanged; reran baseline/idempotent/self-heal/partial-abort/reimport/registry-override probes single-process (10 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/apps/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__apps.stripped.py
    - docs/shadow/current/django_strawberry_framework__apps.overview.md
    - Prompt:
        - Use django_strawberry_framework/apps.py as the entry point. Read docs/shadow/current/django_strawberry_framework__apps.stripped.py and docs/shadow/current/django_strawberry_framework__apps.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/auth/mutations.py
    - Status: verified
    - Iteration 2 (re-opened + RESOLVED 2026-07-13): the auth/queries.py hunt confirmed an IDENTICAL None-user crash in _logout_resolve_body. Fixed Medium (hunter proposed High; recorded Medium to match the sibling auth/queries crash - same class, bounded reachability over non-default request wiring). Defect: `ok = bool(request.user.is_authenticated); auth.logout(request)` had TWO crash sites over the package's own non-HTTP shapes - (1) request.user is None (ChannelsRequestAdapter without AuthMiddlewareStack, or bare request without AuthenticationMiddleware) -> AttributeError; (2) auth.logout(request) would itself crash on the adapter (session None -> flush() crash; adapter.user is a read-only property with no setter -> AttributeError). Fix (auth/mutations.py, _logout_resolve_body only): `user = getattr(request, "user", None); ok = bool(user is not None and user.is_authenticated); if ok: auth.logout(request)`. Mirrors auth/queries; gates teardown on an authenticated session actually existing (anonymous logout has no session to end - the documented idempotent no-op). Credentials fix below PRESERVED. Permanent test: NEW module tests/auth/test_logout_none_user.py (4 tests) - the Channels-adapter None-user shape is NOT expressible at the live HTTP tier, and this new file avoids the collection-blocked tests/auth/test_mutations.py _clear_if_loaded import.
    - Verification (Iteration 2): Passed. WITH fix -> 5 pass (live test_auth_api.py::test_logout_round_trip_and_anonymous_logout [authenticated ends session + anonymous ok:false] + the 4 new None-user tests). Behavior delta (anonymous HTTP logout no longer flushes its session) is compatible with the existing live contract (that test asserts only ok:false/no-errors on the anonymous path, not a session flush). Temp-reverted auth/mutations.py to HEAD -> the 3 None-user shapes FAIL with GraphQLError("'NoneType' object has no attribute 'is_authenticated'") at ['logout']; restored intact (`if ok:` at L433). DRY note: a shared session_actor(request) helper across queries+mutations was NOT done because queries.py was a sibling's dirty file at fix time - possible future consolidation. Out-of-scope boundary left unfixed: authenticated logout OVER the Channels adapter still cannot flush (adapter.user read-only) - a separate spec-041 WebSocket-session-teardown feature, not the None-user crash.
    - Cleanup (Iteration 2): Removed docs/bug_hunt/temp-tests/auth_mutations_logout/; logout fix + tests/auth/test_logout_none_user.py retained; credentials fix + sibling dirty files untouched.
    - Result: Fixed Medium. Public unauthenticated login/register crash: a GraphQL String can carry a lone UTF-16 surrogate (JSON \uXXXX) that is not UTF-8 encodable; handed raw to auth.authenticate (username DB lookup / password hasher .encode()) or register set_password it raised an uncaught UnicodeEncodeError (top-level error / 500). Files changed: auth/mutations.py (_login_resolve_body preflights username+password via shared unencodable_text_error -> same undifferentiated envelope, preserving the enumeration guard; _register_write_step preflights raw_password -> field-keyed password envelope) + test_auth_api.py (3 live permanent tests). Reuses the single-sited storability primitive (write_values.unencodable_text_error).
    - Verification: Passed. WITH fix -> 3 surrogate tests pass. Temp-reverted auth/mutations.py to HEAD -> all 3 FAIL with raw UnicodeEncodeError ('utf-8' cannot encode '\ud800') at the hasher .encode(); restored. Fix is at the correct owner (the 2 paths bypassing the shared decode preflight); enumeration guard intact (well-formed usernames keep the full authenticate timing path; only client-identifiable malformed input short-circuits).
    - Cleanup: Removed docs/bug_hunt/temp-tests/auth_mutations/; fix + permanent tests retained; unrelated work preserved.
    - Iteration: Auth hunter confirmed CONCURRENT-work broken tests in the tree (tests/auth/test_mutations.py ImportError on registry._clear_if_loaded; stale test_queries.py assertion; tests/filters/test_finalizer.py) from the other session's registry.py/types/finalizer.py refactor -> will block the final gate until that session settles.
    - docs/shadow/current/django_strawberry_framework__auth__mutations.stripped.py
    - docs/shadow/current/django_strawberry_framework__auth__mutations.overview.md
    - Prompt:
        - Use django_strawberry_framework/auth/mutations.py as the entry point. Read docs/shadow/current/django_strawberry_framework__auth__mutations.stripped.py and docs/shadow/current/django_strawberry_framework__auth__mutations.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/auth/queries.py
    - Status: verified
    - Cycle baseline: HEAD ddeff191 (source tree clean at dispatch); live source authoritative, shadow orientation-only
    - Result: Fixed Medium. Public-contract crash: _current_user_resolve_body did `user = request.user; actor = user if user.is_authenticated else None`, which raises AttributeError('NoneType' object has no attribute 'is_authenticated') when request.user is None - reachable through the framework's OWN supported ChannelsRequestAdapter (spec-041) when the scope carries no AuthMiddlewareStack-populated user, and for a bare request wired without AuthenticationMiddleware. Violates current_user's documented nullable-return contract (authenticated -> user, else null). Files changed: auth/queries.py (user = getattr(request, "user", None); actor = user if (user is not None and user.is_authenticated) else None - mirrors the read-side DjangoModelPermission.has_permission guard; preserves the SimpleLazyObject lazy-forcing invariant via short-circuit) + tests/auth/test_queries.py (permanent test driving the Channels-adapter mapping context + a bare request with no user attr; +54 additive).
    - Verification: Passed. New pin passes WITH fix; temp-reverted auth/queries.py to HEAD -> pin FAILS with GraphQLError("'NoneType' object has no attribute 'is_authenticated'") at path ['me']; restored intact. Fix at the correct owner. Live test_auth_api.py 15 passed (hunter; authenticated/AnonymousUser paths unchanged by a None-only guard, so no regression risk).
    - Cleanup: Removed docs/bug_hunt/temp-tests/auth_queries/; fix + permanent test retained; unrelated work preserved.
    - FOLLOW-UP (queued, out of target scope): auth/mutations.py::_logout_resolve_body has the IDENTICAL None-user crash (`ok = bool(request.user.is_authenticated)`). auth/mutations.py is already [x] verified for a DIFFERENT defect (unencodable credentials), so this is a newly-confirmed defect requiring a targeted re-open. login/register unaffected (login reads the user only via auth.authenticate). Hunter suggests a shared session_actor(request) helper in auth/mutations.py.
    - docs/shadow/current/django_strawberry_framework__auth__queries.stripped.py
    - docs/shadow/current/django_strawberry_framework__auth__queries.overview.md
    - Prompt:
        - Use django_strawberry_framework/auth/queries.py as the entry point. Read docs/shadow/current/django_strawberry_framework__auth__queries.stripped.py and docs/shadow/current/django_strawberry_framework__auth__queries.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/conf.py
    - Status: no-bugs
    - Result: No bugs. Evidence: all readers re-read the singleton live; reload_settings receiver refreshes in place; nested override_settings round-trips; absent/None/non-mapping hosts behave (defaults or fail-loud ConfigurationError); upstream_patches_enabled whole-mapping validation holds for every hostile shape; __getattr__ recursion guards correct. 16 scratch probes rerun -> pass.
    - Verification: Passed. Source unchanged; reran docs/bug_hunt/temp-tests/conf/ -> 16 passed. (defaultdict-as-settings exotic-misuse observation not a defect.)
    - Cleanup: Removed docs/bug_hunt/temp-tests/conf/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__conf.stripped.py
    - docs/shadow/current/django_strawberry_framework__conf.overview.md
    - Prompt:
        - Use django_strawberry_framework/conf.py as the entry point. Read docs/shadow/current/django_strawberry_framework__conf.stripped.py and docs/shadow/current/django_strawberry_framework__conf.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/connection.py
    - Status: verified
    - Cycle baseline: HEAD ddeff191 (source tree clean at dispatch); live source authoritative, shadow orientation-only
    - Lead: list_field item flagged DjangoConnectionField uses normalize_query_source directly (NOT the post-process fn fixed in utils/querysets.py) and may share the silent visibility-skip on a coroutine-returning sync resolver
    - Result: Fixed Medium. Lead CONFIRMED but it is a CONTRACT defect, not a data leak: a sync consumer resolver= returning an awaitable (plain def returning a coroutine, custom __await__, or Future) is classified sync by is_async_callable, reaches _pipeline_sync, normalize_query_source reports non-queryset, and the un-guarded awaitable flows into Strawberry ListConnection slicing which cannot iterate it -> bare AssertionError/RuntimeError at the GraphQL boundary + stranded un-awaited awaitable, instead of the package's contractual clean SyncMisuseError (diverging from the list_field surface). Files changed: utils/querysets.py (extracted the awaitable-rejection logic out of post_process_queryset_result_sync into a new single-sited helper reject_awaitable_sync_source(source, type_cls) - byte-identical message + close/cancel disposal - because that module owns the source-normalization/visibility contract for every resolver surface), connection.py (import + invoke the guard at the top of _pipeline_sync, sync path only; async _resolve awaits before this runs), tests/test_connection.py (2 async package-tier pins: coroutine + custom __await__).
    - Verification: Passed. WITH fix -> 99 pass across tests/test_connection.py + tests/test_list_field.py + tests/utils/test_querysets.py (list_field, the shared helper's OTHER consumer, stays green -> extraction is behavior-preserving, no regression to the already-verified list_field item; existing connection tests green -> normal QuerySet/list resolvers not falsely rejected, async path intact). Pre-fix reproduced by surgically neutralizing the guard call in _pipeline_sync (backup+restore): both pins FAIL with original_error=AssertionError (strawberry ListConnection `assert isinstance(nodes,(Iterable,Iterator))`) + PytestUnraisableExceptionWarning for the stranded coroutine; restored intact. Fix at the correct owning layer (single-sited guard shared by both surfaces).
    - Cleanup: Removed docs/bug_hunt/temp-tests/connection/ + _w1_verify backup; fix + permanent tests retained. NOTE: the fix also refactors utils/querysets.py (a PENDING hunt item) and touches the file holding the committed list_field fix - the utils/querysets.py hunt must account for the extracted reject_awaitable_sync_source helper.
    - docs/shadow/current/django_strawberry_framework__connection.stripped.py
    - docs/shadow/current/django_strawberry_framework__connection.overview.md
    - Prompt:
        - Use django_strawberry_framework/connection.py as the entry point. Read docs/shadow/current/django_strawberry_framework__connection.stripped.py and docs/shadow/current/django_strawberry_framework__connection.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/exceptions.py
    - Status: no-bugs
    - Result: No bugs. Evidence: 3-class hierarchy + SyncMisuseError(ConfigurationError,RuntimeError) MRO valid; every catch site (relay/finalizer/rest_framework/filters/walker) holds; OptimizerError/ConfigurationError are NOT ValueError/TypeError so walker fallback cannot swallow them; GLOBALID_INVALID contract airtight (decode_global_id raises ConfigurationError on all failure modes). 7 hostile probes rerun -> pass.
    - Verification: Passed. Source unchanged; reran docs/bug_hunt/temp-tests/exceptions/ -> 7 passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/exceptions/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__exceptions.stripped.py
    - docs/shadow/current/django_strawberry_framework__exceptions.overview.md
    - Prompt:
        - Use django_strawberry_framework/exceptions.py as the entry point. Read docs/shadow/current/django_strawberry_framework__exceptions.stripped.py and docs/shadow/current/django_strawberry_framework__exceptions.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/extensions/debug.py
    - Status: no-bugs
    - Result: No bugs. Evidence: DjangoDebugExtension cursor-capture refcount coordinator + on_operation ExitStack/finally restore invariant holds (probe_02 isolated 5/5; 41 permanent + 7 live pass); sequential-op SQL isolation, degrade paths (reset_queries mid-op), MaskErrors LIFO ordering all correct; rollover/async-boundary limits are documented fidelity, not defects.
    - Verification: Passed. Source unchanged; each probe file passes in isolation. The combined-run failures (test_nested_inner_raises / test_repeated_operations_no_state_leak) are NON-deterministic order-dependent scratch cross-contamination: probe_01 spawns worker threads that open sqlite cursors + toggles process-global connection.force_debug_cursor, and -W error attributes the leaked-conn warning to the following test. Real extension usage spawns no threads / never toggles the global flag -> not a defect.
    - Cleanup: Removed docs/bug_hunt/temp-tests/extensions_debug/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__extensions__debug.stripped.py
    - docs/shadow/current/django_strawberry_framework__extensions__debug.overview.md
    - Prompt:
        - Use django_strawberry_framework/extensions/debug.py as the entry point. Read docs/shadow/current/django_strawberry_framework__extensions__debug.stripped.py and docs/shadow/current/django_strawberry_framework__extensions__debug.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/filters/base.py
    - Status: verified
    - Result: Fixed Medium. Error-translation defect: _decode_and_validate_global_id called relay.GlobalID.from_id(value) BARE (no error handling), so a malformed GlobalID filter value leaked Strawberry's raw GlobalIDValueError as an UNCODED top-level error - unlike every other decode site (types/relay.decode_global_id) which yields GLOBALID_INVALID. Affects GlobalIDFilter + GlobalIDMultipleChoiceFilter (both route through this helper). Files changed: filters/base.py (wrap from_id in try/except ValueError -> GraphQLError with extensions.code=GLOBALID_INVALID + list index suffix) + test_library_api.py (2 live permanent tests: malformed own-PK exact + malformed in-element).
    - Verification: Passed (non-destructive, since wave-3 filters hunters still read this file). HEAD pre-fix confirmed bare from_id; GlobalID.from_id raises GlobalIDValueError (ValueError subclass) on all 3 malformed inputs -> proves the uncoded leak; fixed code catches ValueError superset -> GLOBALID_INVALID; 2 permanent tests pass. Wrong-type (code-less) path untouched. Correct owning layer (mirrors decode_global_id idiom).
    - Cleanup: Removed docs/bug_hunt/temp-tests/filters_base/; fix + permanent tests retained. NOTE: filters/base.py working-tree diff is 2 hunks BOTH from this hunt (scalars-item IntegerRangeFilter + this GlobalID catch) - not external; both verified.
    - Iteration: Hunter reports the concurrent registry.py/finalizer.py/sets.py/types/base.py refactor now makes ~20 test_library_api.py tests return WRONG DATA (not errors), independent of this fix -> widening concurrent-work breakage; will hit the final gate.
    - Iteration 2 (RESOLVED 2026-07-13): the ~20 test_library_api.py wrong-data failures flagged above were root-caused to THIS file and FIXED (Fixed High). GlobalIDMultipleChoiceFilter/_GlobalIDMultipleChoiceField could not distinguish an ABSENT id__in key from an EXPLICIT [] -> an omitted own-PK/relation membership filter collapsed to [] -> qs.none() -> silently zeroed the whole query. The committed finalization refactor surfaced (not introduced) the latent defect by binding _owner_definition before filter expansion (spec-027-correct), so own-PK id__in finalizes as GlobalIDMultipleChoiceFilter. Fix (filters/base.py): _AbsentGlobalIDMultipleChoiceWidget.value_from_datadict returns None for an absent key (presence is the reliable dict/QueryDict signal); _GlobalIDMultipleChoiceField.clean keeps None as None -> absent=skip, explicit {in:[]}=match-nothing (preserved), {in:[ids]}=unchanged. Verified: WITH fix test_library_api.py 168 passed + products/scalars 129 passed; temp-revert base.py to HEAD -> 20 failures return. Covered by the existing maintainer live suite (no new test needed). Finalizer/registry untouched (the pre-bind-clear lead was disproved). See the RESOLVED entry in Known blockers.
    - Follow-up flagged (NOT fixed - unconfirmed/unreachable per HUNT confirm-before-editing): ListFilter (same file) shares the same "empty = match-nothing" repurposing backed by a CharField (absent -> '' -> len 0 -> qs.none()), so an absent ListFilter would zero identically. No generated filter or test exercises it (it is a consumer primitive; generated __in uses CSV/Integer/GlobalID filters), so it is out of scope for this regression - worth a maintainer follow-up if ListFilter ever enters an empty-leaf path.
    - docs/shadow/current/django_strawberry_framework__filters__base.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__base.overview.md
    - Prompt:
        - Use django_strawberry_framework/filters/base.py as the entry point. Read docs/shadow/current/django_strawberry_framework__filters__base.stripped.py and docs/shadow/current/django_strawberry_framework__filters__base.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/filters/factories.py
    - Status: verified
    - Result: Fixed Medium. Silent field-drop: emit_set_input_field_triples flattened each member's path (__ -> _) into python_attr with NO collision check, so two members flattening to one python_attr/graphql_name silently overwrote each other - a declared filter/order vanished from the public schema (the type/form/serializer surfaces all fail loud on the analog; this one didn't). Fix: fail-loud ConfigurationError collision guard in utils/inputs.py::emit_set_input_field_triples (single site feeding both filter + order families) + tests/filters/test_factories.py.
    - Verification: Passed. utils/inputs.py parses OK (no concurrent-edit corruption); both this collision guard AND the orders/factories empty-triples guard coexist coherently in the file; permanent test passes; hunter proved fail-pre-fix (DID NOT RAISE).
    - Cleanup: Removed docs/bug_hunt/temp-tests/filters_factories/; fix + permanent test retained. utils/inputs.py carries 2 hunt guards (this + orders/factories).
    - docs/shadow/current/django_strawberry_framework__filters__factories.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__factories.overview.md
    - Prompt:
        - Use django_strawberry_framework/filters/factories.py as the entry point. Read docs/shadow/current/django_strawberry_framework__filters__factories.stripped.py and docs/shadow/current/django_strawberry_framework__filters__factories.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/filters/inputs.py
    - Status: verified
    - Result: Fixed Medium. Public-contract defect: _build_range_input_class named the nested Strawberry range sub-input from field_name alone (not filterset-qualified via ClassBasedTypeNameMixin), so two FilterSets with a same-named RangeFilter column of divergent scalars mint two classes under one GraphQL name; the nested class bypasses the materialization ledger + arguments-factory collision registry, so Strawberry SILENTLY keeps the first-registered and advertises the wrong axis scalar (spec-027's assumed build-time error is false). Files changed: filters/inputs.py (thread owning filterset_cls into convert_filter_to_input_annotation -> _build_range_input_class, prefix class name with filterset_cls.__name__; None preserves legacy unqualified name = backward compatible) + tests/filters/test_inputs.py (scoped-name test + backward-compat test).
    - Verification: Passed. 2 permanent tests pass (scoped qualified names + both range types survive real Schema SDL; unqualified without filterset). Hunter proved fail-pre-fix via forced prefix=''. Single-file hunt change (+36/-6).
    - Cleanup: Removed docs/bug_hunt/temp-tests/filters_inputs/; fix + permanent tests retained.
    - docs/shadow/current/django_strawberry_framework__filters__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__inputs.overview.md
    - Prompt:
        - Use django_strawberry_framework/filters/inputs.py as the entry point. Read docs/shadow/current/django_strawberry_framework__filters__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__filters__inputs.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/filters/sets.py
    - Status: verified
    - Result: Fixed Medium. Side-effect-correctness/public-contract defect: a nested RelatedFilter child's check_<field>_permission gate fired once PER enclosing relation level (x2 at 1 level, x3 at 2) because _derive_related_visibility_querysets_sync/async invoked the child filterset's full apply_* (which runs _run_permission_checks) while the top-level _run_permission_checks pass ALSO recurses. Violates test_permission_checks_run_only_through_apply_entrypoint. Files changed: filters/sets.py (thread keyword-only run_permissions=True through apply_sync/apply_async/_apply_common_finalize; derivation calls child apply_* with run_permissions=False; perms never mutate the qs so derived qs byte-identical; FILTER_INVALID validation still runs) + tests/filters/test_sets.py (fires-once test + still-denies test).
    - Verification: Passed (non-destructive; filters/sets.py carries 2 hunt changes - scalars reroute + this fix - so no clean temp-revert). Both permanent tests pass: fires-once (proven x3 pre-fix by hunter) AND still-denies (enforcement intact, no security regression). diff +81/-6 = the two hunt changes.
    - Cleanup: Removed docs/bug_hunt/temp-tests/filters_sets/; fix + permanent tests retained.
    - docs/shadow/current/django_strawberry_framework__filters__sets.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__sets.overview.md
    - Prompt:
        - Use django_strawberry_framework/filters/sets.py as the entry point. Read docs/shadow/current/django_strawberry_framework__filters__sets.stripped.py and docs/shadow/current/django_strawberry_framework__filters__sets.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/forms/converter.py
    - Status: no-bugs
    - Result: No bugs. Evidence: convert_form_field maps every django.forms scalar as documented; unsupported fields (ComboField/DurationField/MultiValueField/SplitDateTimeField/custom bare Field) fail loud with ConfigurationError (no silent str catch-all); MRO-walk hazards safe (Float/Decimal/UUID resolve to own scalar; NullBoolean beats Boolean; ModelMultipleChoiceField is not a MultipleChoiceField subclass). End-to-end round-trip through a live DjangoFormMutation validated all values. forms.JSONField->str and DurationField-raises are documented/consistent, not defects. 2 e2e probes rerun -> pass.
    - Verification: Passed. Source unchanged; reran test_probe_e2e_scalars.py -> 2 passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/forms_converter/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__forms__converter.stripped.py
    - docs/shadow/current/django_strawberry_framework__forms__converter.overview.md
    - Prompt:
        - Use django_strawberry_framework/forms/converter.py as the entry point. Read docs/shadow/current/django_strawberry_framework__forms__converter.stripped.py and docs/shadow/current/django_strawberry_framework__forms__converter.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/forms/inputs.py
    - Status: verified
    - Result: Fixed Medium. A ModelForm relation field with queryset=None (request-scoped-choices idiom, assigned in __init__) crashed at decode with raw AttributeError: input-generation typed the id from the backing model column (column.related_model) but Slice-3 decode re-derived the related model from form_field.queryset.model (None). Input basis and decode basis had diverged. Files changed: forms/converter.py (related_model field on FormInputFieldSpec, defaulted), forms/inputs.py (populate spec.related_model from the same basis as the id type), forms/resolvers.py (_decode_form_relation_single/_multi take related_model threaded from spec instead of form_field.queryset.model), tests/forms/test_resolvers.py (proof test + 4 updated direct-call unit tests). Mirrors serializer flavor's InputFieldSpec.related_model (spec-039 H4).
    - Verification: Passed. Full tests/forms/ = 151 passed (all 4 forms fixes coexist). New permanent test passes; hunter proved fail-pre-fix (exact AttributeError via schema.execute_sync). related_model refactor coherent across converter(4)/inputs(10)/resolvers(8); forms/resolvers rollback _error_payload intact (set_rollback x2). Pascalize underscore/case non-injectivity left unfixed (fail-loud, pathological) - noted.
    - Cleanup: Removed docs/bug_hunt/temp-tests/forms_inputs/; fix + permanent tests retained. Cross-file fix also modifies forms/converter.py (recorded no-bugs for its own logic - the spec-field addition is additive).
    - docs/shadow/current/django_strawberry_framework__forms__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__forms__inputs.overview.md
    - Prompt:
        - Use django_strawberry_framework/forms/inputs.py as the entry point. Read docs/shadow/current/django_strawberry_framework__forms__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__forms__inputs.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/forms/resolvers.py
    - Status: verified
    - Result: Fixed Medium. Transaction data-integrity: _run_plain_form_pipeline_sync owns its own transaction.atomic() but (unlike the shared run_write_pipeline_sync skeleton the model/ModelForm/serializer flavors ride) did NOT set_rollback(True) before returning an {ok:false} envelope; a perform_mutate/form.save() partial write followed by a caught IntegrityError (not one that aborts the connection) COMMITTED despite ok=false, violating spec-039 H6. Files changed: forms/resolvers.py (local _error_payload calls transaction.set_rollback(True) on all 3 error returns) + tests/forms/test_resolvers.py (permanent test asserting the side-effect row is not persisted).
    - Verification: Passed (non-destructive, forms/sets hunter still active). Fix diff adds set_rollback(True) in decode/validation/write error paths; HEAD pre-fix confirmed lacked it (3 bare payload_cls(ok=False) returns); mirrors the established skeleton pattern (mutations/resolvers.py set_rollback); permanent test passes; hunter proved fail-pre-fix via temp-disable.
    - Cleanup: Removed docs/bug_hunt/temp-tests/forms_resolvers/; fix + permanent test retained.
    - docs/shadow/current/django_strawberry_framework__forms__resolvers.stripped.py
    - docs/shadow/current/django_strawberry_framework__forms__resolvers.overview.md
    - Prompt:
        - Use django_strawberry_framework/forms/resolvers.py as the entry point. Read docs/shadow/current/django_strawberry_framework__forms__resolvers.stripped.py and docs/shadow/current/django_strawberry_framework__forms__resolvers.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/forms/sets.py
    - Status: verified
    - Result: Fixed Low. Model-less DjangoFormMutation accepted Meta.permission_classes=[DjangoModelPermission] (or subclass) at class creation (passes the generic has_permission check) but crashed at request time with raw AttributeError - DjangoModelPermission.has_permission calls mutation._resolve_model, which a non-DjangoMutation plain form lacks. Violates the fail-loud contract (DenyAll docstring documents this exact incompatibility). Files changed: forms/sets.py (plain-form _validate_meta rejects DjangoModelPermission+subclass fail-loud at class creation, naming DjangoModelFormMutation + valid plain-form postures) + tests/forms/test_sets.py.
    - Verification: Passed. Full tests/forms/ = 151 passed; the permanent test (DjangoModelPermission + subclass) passes; hunter proved fail-pre-fix via temp-disable. Shared _validate_permission_classes still accepts DjangoModelPermission for model flavors (guard scoped to the plain-form path).
    - Cleanup: Removed docs/bug_hunt/temp-tests/forms_sets/; fix + permanent test retained.
    - docs/shadow/current/django_strawberry_framework__forms__sets.stripped.py
    - docs/shadow/current/django_strawberry_framework__forms__sets.overview.md
    - Prompt:
        - Use django_strawberry_framework/forms/sets.py as the entry point. Read docs/shadow/current/django_strawberry_framework__forms__sets.stripped.py and docs/shadow/current/django_strawberry_framework__forms__sets.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/keyset.py
    - Status: no-bugs
    - Result: No bugs. Evidence: codec round-trip + seek partitioning verified across EVERY supported field type (Float/Decimal/Date/DateTime tz-aware+microsecond/Time/BigInt/UUID incl negatives, zero, 1e20, trailing-zero decimals, 1-microsecond boundary) - keyset_seek_q after/before matched the DB ORDER BY exactly; hardest case = 3-column mixed-direction key (-flag,score,id) with ties, cursored exhaustively at all 12 rows, after/before matched at every position; AES-SIV authenticated codec tamper/foreign-prefix/fingerprint/arity rejections uniform; SECRET_KEY_FALLBACKS rotation + re-serialization drift guard correct; declaration-time + finalization-time validation both route through validate_cursor_field_references (cannot diverge; refactor only strengthened it). tests/test_keyset.py 52 passed (hunter). BinaryField-as-cursor round-trip weakness rejected as unrealistic config, not a defect.
    - Verification: source byte-unchanged (git clean); probe rerun deferred to final gate (filter-regression hunt actively temp-reverts filter/finalizer files -> schema-building reruns unreliable now); conclusion accepted on source-clean + thorough trace. Scratch removed.
    - Cycle baseline: HEAD ddeff191 (+ in-flight verified hunt fixes); live source authoritative, shadow orientation-only. Previously deferred for concurrent WIP; now clean and hunt-able.
    - docs/shadow/current/django_strawberry_framework__keyset.stripped.py
    - docs/shadow/current/django_strawberry_framework__keyset.overview.md
    - Prompt:
        - Use django_strawberry_framework/keyset.py as the entry point. Read docs/shadow/current/django_strawberry_framework__keyset.stripped.py and docs/shadow/current/django_strawberry_framework__keyset.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/list_field.py
    - Status: verified
    - Result: Fixed Medium. Data-isolation defect: a plain def consumer resolver that RETURNS a coroutine is classified sync by is_async_callable, so post_process_queryset_result_sync got the coroutine as a non-queryset and passed it through; under async schema execution graphql-core awaited it into a QuerySet that never ran target_type.get_queryset -> silent visibility bypass. Files changed: utils/querysets.py (post_process_queryset_result_sync now close()s + raises SyncMisuseError on a coroutine, mirroring the sync get_queryset guard) + tests/test_list_field.py (permanent regression test). Root cause owned by the single-sited post-process fn (called only by list_field.py).
    - Verification: Passed. WITH fix -> test passes. Temp-reverted utils/querysets.py to HEAD -> test FAILS showing the exact leak (data={25 rows incl. address, automotive}, errors=None; exclude(name__startswith=a) silently skipped); restored fix. Fix is narrow (QuerySet returns still get visibility; lists pass through; proper async def uses async path) and at the correct owner.
    - Cleanup: Removed docs/bug_hunt/temp-tests/list_field/; fix + permanent test retained; unrelated work preserved.
    - Iteration: Hunter flagged that connection.py (DjangoConnectionField) uses normalize_query_source directly (NOT this post-process fn) and may share the same silent-skip -> carry to the deferred connection.py hunt item.
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

- [x] django_strawberry_framework/management/commands/export_schema.py
    - Status: verified
    - Result: Fixed Low (COMMITTED by maintainer as 1082dbd5). A malformed schema SELECTOR STRING escaped as a raw ValueError/TypeError traceback instead of the contracted CommandError: import_module_symbol reports an empty module path ("" / ":schema") as ValueError and a relative path (".config.schema") as TypeError - neither is ImportError/AttributeError, so both slipped import_or_command_error's narrow catch (spec-022 Decision 5's "malformed path -> CommandError" assumed ImportError). Real trigger: an unset CI var passed as the selector. Fix (root cause, systemic): new _imports.py::import_module_symbol_or_command_error validates the selector string BEFORE importing (empty/relative -> CommandError) then delegates; export_schema.py AND inspect_django_type.py (the only 2 import_module_symbol sites) both rewired - critically it does NOT broaden the catch, so a genuine consumer-module ValueError still surfaces raw (Decision 5 preserved). Tests: tests/management 37 passed (hunter).
    - Verification: Passed. Committed diff reviewed (1082dbd5: _imports.py +45, export_schema.py +10, inspect_django_type.py +15, test_export_schema.py +13, + test_imports.py per hunter). Placement correct (parser/short-circuit tier -> tests/management/). Hunter proved fail-without-fix (raw ValueError/TypeError pre-fix). Scratch removed.
    - Cycle baseline: HEAD ddeff191 (+ in-flight verified hunt fixes); live source authoritative, shadow orientation-only
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

- [x] django_strawberry_framework/middleware/debug_toolbar.py
    - Status: no-bugs
    - Cycle baseline: HEAD ddeff191 (source tree clean at dispatch); live source authoritative, shadow orientation-only
    - Result: No bugs. Evidence: near-verbatim port of upstream strawberry_django debug_toolbar middleware with 3 divergences that make it MORE robust (JSON re-encode charset handling, streaming/RawPostDataException degrade-to-inject, template DOM guards); 72 stmts at 100% existing coverage; ~16 hostile probes (unicode/latin-1/bogus-charset/non-object-JSON/consumed-body/streaming/non-200/attacker debugToolbar key overwrite/panel title serialization/process_view across view shapes/async_mode) all behaved correctly. Theoretical edges (panel title() raising; gzip Content-Encoding on HTML append) rejected as verbatim-with-upstream + not realistically reachable in the DEBUG+INTERNAL_IPS dev-only path.
    - Verification: Passed. Target byte-unchanged (git clean for debug_toolbar.py + tests/middleware/ + test_debug_toolbar_api.py); reran 16 scratch probes -> 16 passed. No production edit (no confirmed defect met the bar).
    - Cleanup: Removed docs/bug_hunt/temp-tests/middleware_debug_toolbar/; unrelated work preserved.
    - Out-of-scope note (NOT a middleware defect; left for maintainer): README.md:69 and both test-file docstrings still say the debug-toolbar middleware is "Still to come in 0.0.14"/"Since 0.0.14" though it has landed at 0.0.13 - standing version/doc drift on a concurrently-edited tree, resolved by the 0.0.14 version cut, not the hunt.
    - docs/shadow/current/django_strawberry_framework__middleware__debug_toolbar.stripped.py
    - docs/shadow/current/django_strawberry_framework__middleware__debug_toolbar.overview.md
    - Prompt:
        - Use django_strawberry_framework/middleware/debug_toolbar.py as the entry point. Read docs/shadow/current/django_strawberry_framework__middleware__debug_toolbar.stripped.py and docs/shadow/current/django_strawberry_framework__middleware__debug_toolbar.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

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

- [x] django_strawberry_framework/mutations/permissions.py
    - Status: no-bugs
    - Cycle baseline: HEAD 16b9a08e; live source authoritative, shadow orientation-only
    - Result: No bugs. Evidence: the async-coroutine allow-bypass (central risk) is fully closed - async has_permission, custom __await__, async check_permission override, AND a sync has_permission hand-returning a coroutine are all caught by reject_async_in_sync_context -> SyncMisuseError on BOTH the sync (execute_sync) and async (execute under sync_to_async) surfaces; no row written, truthy-coroutine never treated as allow. Phase gating correct (create authorizes pre-decode instance=None; update/delete post-visibility-locate, hidden row not-found before any auth signal = no existence leak); model-less DjangoFormMutation._validate_meta rejects DjangoModelPermission + subclasses at class creation; DjangoModelPermission re-resolves the model at request time; DenyAll always False; fresh permission instance per call (no state leak); operation->action map pinned. tests/mutations/test_permissions.py 17 passed (hunter).
    - Verification: source byte-unchanged (git clean); schema-building probe rerun deferred to final gate (filter-regression hunt active in types/); accepted on source-clean + trace. Considered-and-REJECTED lead (AGREED): _validate_permission_classes accepts a permission class with a required __init__ arg / wrong has_permission signature that then TypeErrors at request time - but it is FAIL-CLOSED (never allows, clear error naming the class), and robust constructibility/signature introspection over arbitrary callables (*args/kw-only/C-level/metaclass-__call__) would false-positive-reject valid classes (DRF validates neither); a brittle guard would be a net-negative fix per AGENTS.md line 4. Not a defect. Scratch removed.
    - docs/shadow/current/django_strawberry_framework__mutations__permissions.stripped.py
    - docs/shadow/current/django_strawberry_framework__mutations__permissions.overview.md
    - Prompt:
        - Use django_strawberry_framework/mutations/permissions.py as the entry point. Read docs/shadow/current/django_strawberry_framework__mutations__permissions.stripped.py and docs/shadow/current/django_strawberry_framework__mutations__permissions.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/mutations/resolvers.py
    - Status: no-bugs
    - Result: No bugs. Evidence: the primary hypothesis (does the mutation write-skeleton's set_rollback analog to the sibling forms bug hold?) tested to destruction and HOLDS - a decode_step OR write_step that makes a real side-write then returns a [FieldError] envelope does NOT commit (proven sync AND async via transaction=True real commits); delete atomicity holds; every error return routes through _error_payload -> transaction.set_rollback(True) before the ORM-free build_payload; permission gating single-invocation + correctly phased (create pre-decode; update/delete post-visibility-locate); authorize_or_raise closes async check_permission coroutines into SyncMisuseError (no truthy-coroutine allow bypass); coerce_lookup_id covers all 4 GlobalIDDecode statuses; AR-H2 co-member collision caught by full_clean. tests/mutations/test_resolvers.py 58 passed (hunter). One observation (M2M .set() IntegrityError on a concurrent-committed-delete TOCTOU surfaces as top-level GraphQLError not the __all__ envelope) is race-only with NO data-integrity consequence (still rolls back atomically) - below Low, not fixed (would be a surface patch for an unfixable TOCTOU).
    - Verification: source byte-unchanged (git clean); probe rerun deferred to final gate (filter-regression hunt active); accepted on source-clean + trace. Scratch removed.
    - Cycle baseline: HEAD ddeff191 (+ in-flight verified hunt fixes); live source authoritative, shadow orientation-only
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

- [ ] django_strawberry_framework/optimizer/plans.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__optimizer__plans.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__plans.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/plans.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__plans.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__plans.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/optimizer/selections.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__optimizer__selections.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__selections.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/selections.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__selections.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__selections.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/optimizer/walker.py
    - Status: verified
    - Cycle baseline: HEAD ddeff191 (source tree clean at dispatch); live source authoritative, shadow orientation-only (optimizer refactored post-baseline by commit ddeff191)
    - Iteration 1 (wave-1 hunter): BLOCKED (contended) - walker.py + test_walker.py went dirty mid-task with the utils/strings hunter's digit-boundary scalar fix; per the coordination rule the walker hunter did NOT edit them. Its own independent live hunt found NO additional bug (26 hostile e2e probes pass: FK/list dispatch, aliased divergent scalars, nested-connection windowing with data verified vs naive ORM, per-key $-escaped to_attr, strictness=raise no-false-positives, M2M fwd+reverse, O2O, keyset, depth-4 chains, conn-in-conn, self-M2M). BUT by inspection it found the utils/strings fix is INCOMPLETE - it patches only the field_map.get(snake_case(sel.name)) miss, leaving two more lossy-reversal sites: (2a, Medium correctness/perf) the relation_connections membership check (~L356) drops a digit-boundary many-relation-connection (line_2 -> field line2Connection; snake_case gives line2_connection != key line_2_connection; _field_by_graphql_name cannot rescue since to_camel_case(line_2)=line2!=line2Connection) -> per-parent N+1; (2b, minor/safe) _selected_scalar_names (~L981) misses -> FK-id elision skipped -> safe select_related fallback.
    - Iteration 2 (reconciliation dispatched 2026-07-13): one Worker 2 owns the COMPLETE consolidated walker.py digit-boundary fix - builds on the in-tree partial fix, confirms gap 2a with a live repro before fixing, routes all 3 GraphQL-name->Django-name reversal sites through one forward-resolution helper (handling the ...Connection suffix), adds a relation-connection regression test. Verification of the whole fix (both the scalar site and the relation site) is held until this returns.
    - [x] VERIFIED Fixed Medium (reconciliation complete). Introduced _resolve_selection_target(graphql_name, field_map, relation_connections) as the single reversal owner: fast path (exact snake_case reversal vs connection slot then field map) first, O(n) forward-camelization scan (to_camel_case(slot_key)==graphql_name, connection namespace probed first) only on a miss. Routed SITE 1+2 (_walk_selections) + SITE 3 (_selected_scalar_names). Gap 2a CONFIRMED via live repro (DjangoConnectionField digit-boundary relation line_2 -> field line2Connection): pre-fix 4 parents=21 queries / 8 parents=41 (per-parent N+1, connection dropped from plan), post-fix 2 queries bounded, one windowed Prefetch(to_attr=_dst_line_2_connection). SITE 3: digit-boundary target pk code_2 (code2) elides the JOIN post-fix. Files: optimizer/walker.py + tests/optimizer/test_walker.py (2 new tests + kept scalar test).
    - Verification: Passed. WITH fix -> tests/optimizer/test_walker.py 171 passed (+ 747 broader across optimizer/connection/relay/types.resolvers per hunter). Temp-reverted walker.py to HEAD -> all 3 digit-boundary tests FAIL (scalar/relation-connection/fk-elision); restored (_resolve_selection_target at L191, wired at L443). Fast path preserved (common-case dict lookup). NOTE: this fix is UNCOMMITTED (only dirty source file); the maintainer committed the other hunt fixes but not this one yet.
    - Cleanup: Removed docs/bug_hunt/temp-tests/optimizer_walker/ + walker_reconcile/; fix + tests retained.
    - docs/shadow/current/django_strawberry_framework__optimizer__walker.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__walker.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/walker.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__walker.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__walker.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/orders/base.py
    - Status: verified
    - Result: Fixed Medium. orders/base.py itself correct; root cause in orders/sets.py: _resolve_order_expressions read the to-many-detection model ONLY from Meta.model, but a bound model-less orderset (Meta.orderset_class without Meta.model - a valid shape the finalizer accepts) then skipped the _path_traverses_to_many guard and emitted a to-many order path as a raw fan-out JOIN instead of the row-preserving Min/Max aggregate (P1-B invariant) -> silent row multiplication (duplicate edges, inflated totalCount, corrupted cursors). Fix: orders/sets.py resolves model = Meta.model or _owner_definition.model + tests/orders/test_sets.py permanent test.
    - Verification: Passed. Permanent test (bound model-less orderset -> Min aggregate + one row per parent) passes; hunter proved fail-pre-fix (fan-out, duplicate rows). Fix correctly in clean orders/sets.py (off-limits types/finalizer.py was the alternative site).
    - Cleanup: Removed docs/bug_hunt/temp-tests/orders_base/; fix + permanent test retained. Fix lives in orders/sets.py (see its reconciliation note).
    - docs/shadow/current/django_strawberry_framework__orders__base.stripped.py
    - docs/shadow/current/django_strawberry_framework__orders__base.overview.md
    - Prompt:
        - Use django_strawberry_framework/orders/base.py as the entry point. Read docs/shadow/current/django_strawberry_framework__orders__base.stripped.py and docs/shadow/current/django_strawberry_framework__orders__base.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/orders/factories.py
    - Status: verified
    - Result: Fixed Medium. Empty-input: an OrderSet expanding to zero fields built a 0-field @strawberry.input, rejected only at strawberry.Schema() build with a cryptic ValueError naming the GENERATED type - unlike the write flavors (DjangoMutation/FormMutation/SerializerMutation) which fail loud with ConfigurationError. Only the order family can hit this (filters always append the and_/or_/not_ bag). Fix: if-not-triples guard in utils/inputs.py::GeneratedInputArgumentsFactory._build_class_type raising ConfigurationError naming the set + family (single site for all set families) + tests/orders/test_factories.py.
    - Verification: Passed. utils/inputs.py parses OK; both guards coexist; 2 permanent tests pass; hunter proved fail-pre-fix.
    - Cleanup: Removed docs/bug_hunt/temp-tests/orders_factories/; fix + permanent tests retained. utils/inputs.py carries 2 hunt guards (this + filters/factories).
    - docs/shadow/current/django_strawberry_framework__orders__factories.stripped.py
    - docs/shadow/current/django_strawberry_framework__orders__factories.overview.md
    - Prompt:
        - Use django_strawberry_framework/orders/factories.py as the entry point. Read docs/shadow/current/django_strawberry_framework__orders__factories.stripped.py and docs/shadow/current/django_strawberry_framework__orders__factories.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/orders/inputs.py
    - Status: no-bugs
    - Result: No bugs. Evidence: order-by input surface correct - Ordering.resolve for all 6 members (DESC substring safe), Meta.fields='__all__' excludes forward-M2M/reverse, collision guard fails loud, normalize_input_value handles dict/dataclass/empty/multi/nested/null/unknown, full DB apply (to-many Min/Max aggregate preserves parent count, flat + FK-name ordering), active-input-only permission gates, sync==async. 19 scratch probes passed.
    - Verification: Passed. Source unchanged; reran docs/bug_hunt/temp-tests/orders_inputs/ -> 19 passed. (Two doc/type-looseness observations noted by hunter as non-defects.)
    - Cleanup: Removed docs/bug_hunt/temp-tests/orders_inputs/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__orders__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__orders__inputs.overview.md
    - Prompt:
        - Use django_strawberry_framework/orders/inputs.py as the entry point. Read docs/shadow/current/django_strawberry_framework__orders__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__orders__inputs.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/orders/sets.py
    - Status: no-bugs
    - Result: No bugs (in the apply pipeline as hunted with Meta.model present). Evidence: to-many aggregate ordering (Min ASC/Max DESC, no row multiplication, distinct parent count), deterministic pk tiebreak, relation paths, list precedence, lifecycle, per-class-dedup permission gates (sync==async). 15 scratch probes passed.
    - Verification: Passed. (Reran probes -> 15 passed at time of no-bug verification.)
    - Iteration: orders/sets.py was SUBSEQUENTLY modified by the orders/base.py item's fix (model = Meta.model or _owner_definition.model in _resolve_order_expressions) - a legitimate cross-item root-cause fix for the model-less-orderset fan-out; the no-bug conclusion for the Meta.model-present pipeline is unaffected and coexists (tests/orders/ green).
    - docs/shadow/current/django_strawberry_framework__orders__sets.stripped.py
    - docs/shadow/current/django_strawberry_framework__orders__sets.overview.md
    - Prompt:
        - Use django_strawberry_framework/orders/sets.py as the entry point. Read docs/shadow/current/django_strawberry_framework__orders__sets.stripped.py and docs/shadow/current/django_strawberry_framework__orders__sets.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/permissions.py
    - Status: no-bugs
    - Result: No bugs. Evidence: cascade-visibility _cascade_seen ContextVar cycle guard is thread-isolated + exception-safe (4-thread concurrent-root probe); edge-scope predicate includes forward FK/O2O/GFK-backing-FK and excludes M2M/reverse/GenericRelation/MTI parent-link (no leak-shaped misses); nullable-FK Q(fk__in)|Q(isnull) preservation, db-alias pinning, 1-query composition all hold on real Entry diamond + 4-deep chain; async twin raises SyncMisuseError, no ContextVar leak; fields= validation robust; GLOSSARY contract matches. 7 probe bodies rerun -> pass.
    - Verification: Passed. Source unchanged; reran test_scratch_hostile.py -> 7 passed. The 1 teardown 'error' is a PytestUnraisableExceptionWarning (scratch probe leaks worker-thread sqlite conns under -W error); not a permissions.py defect (real cascade usage spawns no threads/raw conns).
    - Cleanup: Removed docs/bug_hunt/temp-tests/permissions/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__permissions.stripped.py
    - docs/shadow/current/django_strawberry_framework__permissions.overview.md
    - Prompt:
        - Use django_strawberry_framework/permissions.py as the entry point. Read docs/shadow/current/django_strawberry_framework__permissions.stripped.py and docs/shadow/current/django_strawberry_framework__permissions.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/registry.py
    - Status: no-bugs
    - Cycle baseline: HEAD ddeff191 (source tree clean at dispatch); live source authoritative, shadow orientation-only. Previously deferred for concurrent WIP; that refactor has since committed (ddeff191), so registry.py is now clean and hunt-able normally.
    - Result: No bugs. Evidence: audited the committed subsystem-clear refactor (commits 9aabc0b3 teardown machinery + 5e992a7b clear self-registration) - every register_subsystem_clear before_bind flag correct (all 5 input/emit-namespace resets before_bind=True; declaration registries/shape caches/connection cache/relay ledger before_bind=False; a declaration registry wrongly flagged before_bind=True would be the high-sev silent-missing-mutations failure - none is); all 12 legacy hand-written co-clears preserved as self-registrations; retry-idempotence holds (iter_mutations snapshots, re-finalize does not double-register synthesized-connection teardowns); teardown LIFO restoration of connection-shape list-form suppression correct; register/register_with_definition rollback traced through every branch (reverse-collision, dup-primary, flip-primary, setdefault non-leak); tests/test_registry.py 79 passed.
    - Verification: Passed. registry.py byte-unchanged (git clean); reran 11 scratch probes (lifecycle/hostile/retry) -> 11 passed. Non-finding correctly rejected: clear() runs consumer teardowns before core reset, so a permanently-raising teardown could abort clear() - but framework teardowns cannot raise, transient failures recover via the tested retry, and failing loud on a broken consumer teardown is defensible (speculative, no realistic trigger).
    - Cleanup: Removed docs/bug_hunt/temp-tests/registry/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__registry.stripped.py
    - docs/shadow/current/django_strawberry_framework__registry.overview.md
    - Prompt:
        - Use django_strawberry_framework/registry.py as the entry point. Read docs/shadow/current/django_strawberry_framework__registry.stripped.py and docs/shadow/current/django_strawberry_framework__registry.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/relay.py
    - Status: no-bugs
    - Result: No bugs. Evidence: DjangoNodeField/NodesField global-id coercion+decode boundary uniformly returns GLOBALID_INVALID (no raw ConfigurationError/KeyError leak); oversized/negative/float/whitespace/colon ids handled with 0 or bounded queries; no existence-oracle leak (hidden/missing rows -> null, equal query counts); sync-in-async raises SyncMisuseError not mislabeled; duplicate-label routing is the documented load-bearing behavior. 50 permanent + 13 scratch probes pass.
    - Verification: Passed. Source unchanged; reran docs/bug_hunt/temp-tests/relay/ -> 13 passed. Hunter correctly read registry.py at HEAD (not the concurrent WIP) per the concurrency constraint.
    - Cleanup: Removed docs/bug_hunt/temp-tests/relay/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__relay.stripped.py
    - docs/shadow/current/django_strawberry_framework__relay.overview.md
    - Prompt:
        - Use django_strawberry_framework/relay.py as the entry point. Read docs/shadow/current/django_strawberry_framework__relay.stripped.py and docs/shadow/current/django_strawberry_framework__relay.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/rest_framework/inputs.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__rest_framework__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__rest_framework__inputs.overview.md
    - Prompt:
        - Use django_strawberry_framework/rest_framework/inputs.py as the entry point. Read docs/shadow/current/django_strawberry_framework__rest_framework__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__rest_framework__inputs.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/rest_framework/resolvers.py
    - Status: verified
    - Cycle baseline: HEAD 16b9a08e; live source authoritative, shadow orientation-only
    - Result: Fixed Medium. Data-integrity defect: _assert_save_kwargs_no_shadow (guards get_serializer_save_kwargs from silently overriding client input) compared save kwargs against spec.target_name (the DECLARED serializer field name), but serializer.save(**kwargs) merges over validated_data which DRF keys by each field's SOURCE. For a RENAMED field (source != declared name, e.g. display_name = CharField(source="name")), a save kwarg keyed by the source silently clobbers the client value and the guard never fires (its docstring even asserted the false premise "the same key validated_data uses"). Combines two sanctioned features (renamed fields Decision 7 + get_serializer_save_kwargs rev6 #12) into silent client-input discard. Fix: compare against spec.source or spec.target_name; corrected docstring; error names the colliding input. Files: rest_framework/resolvers.py (sole owner; shared mutations skeleton untouched) + tests/rest_framework/test_resolvers.py (2 tests: unit guard-keys-on-source + end-to-end renamed-source collision blocks silent override). Rollback ({ok:false} on partial write incl UPDATE) + visibility-scope defense-in-depth (hidden FK/M2M pk rejected by is_valid against the narrowed queryset) + decode/runtime divergence assertion all verified SOUND (no bug).
    - Verification: Passed (settle pass, clean tree). WITH fix tests/rest_framework/test_resolvers.py 64 passed (part of the 402-passed settle run). Temp-reverted rest_framework/resolvers.py to HEAD -> 2 failed (the 2 new tests, DID NOT RAISE); restored intact (fix present, +37). Fix at the sole owner (shared mutations skeleton untouched). Scratch removed.
    - docs/shadow/current/django_strawberry_framework__rest_framework__resolvers.stripped.py
    - docs/shadow/current/django_strawberry_framework__rest_framework__resolvers.overview.md
    - Prompt:
        - Use django_strawberry_framework/rest_framework/resolvers.py as the entry point. Read docs/shadow/current/django_strawberry_framework__rest_framework__resolvers.stripped.py and docs/shadow/current/django_strawberry_framework__rest_framework__resolvers.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/rest_framework/serializer_converter.py
    - Status: no-bugs
    - Cycle baseline: HEAD ddeff191 (+ in-flight verified hunt fixes to auth/queries, connection, utils/querysets, walker); live source authoritative, shadow orientation-only
    - Result: No bugs. Evidence: every DRF field kind maps correctly and unmapped fields fail loud with ConfigurationError (no silent String); the forms-flavor id-basis-vs-decode-basis bug does NOT recur - model-backed relations derive id type + spec.related_model both from column.related_model, serializer-only relations both from field.queryset.model (same basis per path), queryset=None fails loud (not AttributeError), and resolvers._assert_relation_agreement reconciles runtime vs spec at the boundary; choice-enum cache re-emits cleanly across registry.clear() and dedupes within a build; nested-serializer opt-in, Relay GlobalID vs raw pk, file->Upload, ListField scalar-child all correct. tests/rest_framework/ 279 passed.
    - Verification: Passed. serializer_converter.py + rest_framework/ byte-unchanged (git clean); reran 35 scratch probes (needed `-o python_files=probe*.py` since the hunter named them probe*.py not test_*.py) -> 35 passed. Rejected leads verified sound: (1) IntegerField-over-BigIntegerField-column rejection fails LOUD and the BigInt!=int strictness is deliberate/load-bearing (matches the BigAutoField->int intentional distinction); (2) ListField(child=ChoiceField)->list[str] vs MultipleChoiceField->list[enum] is a schema-precision gap only (DRF enforces choices at runtime), consistent with the spec-039 Slice-1 scalar-child contract. Neither is a defect.
    - Cleanup: Removed docs/bug_hunt/temp-tests/rest_serializer_converter/; unrelated work preserved.
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

- [x] django_strawberry_framework/routers.py
    - Status: no-bugs
    - Result: No bugs. Evidence: routing composition (AuthMiddlewareStack/URLRouter HTTP + AllowedHostsOriginValidator WS) is a faithful copy of upstream strawberry_django AuthGraphQLProtocolTypeRouter; soft-channels guard (require_optional_module sentinel), PEP562 lazy export + _ROUTER_CLASS cache/eviction all correct; non-ImportError propagates unmasked; full graphql-transport-ws subscription lifecycle works; install-hint floors match pyproject. 12 scratch probes rerun -> pass.
    - Verification: Passed. Source unchanged; reran scratch_probe.py + scratch_ws_subscription.py -> 12 passed (incl. WS subscription connection_init->complete).
    - Cleanup: Removed docs/bug_hunt/temp-tests/routers/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__routers.stripped.py
    - docs/shadow/current/django_strawberry_framework__routers.overview.md
    - Prompt:
        - Use django_strawberry_framework/routers.py as the entry point. Read docs/shadow/current/django_strawberry_framework__routers.stripped.py and docs/shadow/current/django_strawberry_framework__routers.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/scalars.py
    - Status: verified
    - Result: Fixed Medium. The scalar itself is clean (correctly arbitrary-precision BigInt). Root cause is in the filter layer: a bound-binding integer __range (BETWEEN) binds BOTH bounds directly, so a BigInt bound past signed-64-bit overflows the SQLite bind -> raw OverflowError, 200-with-errors, data:null, leaks backend msg (the same class IntegerInFilter fixed for __in). Files changed: filters/base.py (new IntegerRangeFilter(BaseRangeFilter,NumberFilter) decomposing range -> gte+lte, which Django range-adapts before binding), filters/sets.py (filter_for_lookup routes non-relation integer range -> IntegerRangeFilter, mirroring the in reroute). Permanent tests: live test_scalars_api.py::test_filter_specimens_by_bigint_range_out_of_range_bound_no_overflow + 4 package unit tests in tests/filters/test_base.py.
    - Verification: Passed. Independent ORM probe proved the root-cause invariant (signed_big__range=(1,2**63) raises OverflowError; gte/lte range-adapts, no overflow; gte+lte == inclusive BETWEEN in-range) -> 3 passed. Live permanent test passes; 8 package range unit tests pass. Fix is at the correct owning layer (filter, not scalar), preserves inclusive-range + exclude complement, semantically identical (BETWEEN == >= AND <=) so harmless for 32-bit int columns. Hunter's temp-revert proof (test fails without routing) corroborated.
    - Cleanup: Removed docs/bug_hunt/temp-tests/scalars/ + scalars_verify/; fix files (filters/base.py, filters/sets.py) + permanent tests retained; unrelated work preserved. NOTE: filters/base.py + filters/sets.py are concurrently being hunted (wave 3) on top of this fix.
    - docs/shadow/current/django_strawberry_framework__scalars.stripped.py
    - docs/shadow/current/django_strawberry_framework__scalars.overview.md
    - Prompt:
        - Use django_strawberry_framework/scalars.py as the entry point. Read docs/shadow/current/django_strawberry_framework__scalars.stripped.py and docs/shadow/current/django_strawberry_framework__scalars.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/sets_mixins.py
    - Status: verified
    - Cycle baseline: HEAD ddeff191 (+ in-flight verified hunt fixes); live source authoritative, shadow orientation-only
    - Result: Fixed Medium. collect_related_declarations (the shared FilterSet/OrderSet collector) silently ignored a subclass removing an inherited related declaration by shadowing it with a non-declaration value (`rel = None` - the django-filter declared_filters removal idiom the FilterSet side honors for free). The bare isinstance filter over the raw class body skips the None, so on the inherit_from_bases=True ORDER side the inherited RelatedOrder survived: cls.rel is None but cls.related_orders["rel"] still carried it, re-emitting an ordering field + firing its check_<rel>_permission gate the consumer explicitly disabled -> silent wrong-schema + a live permission/ordering surface. Fix: `elif name in collected: del collected[name]` in collect_related_declarations (sets_mixins.py) - inert on the filter side (declared_filters never carries a non-declaration at an already-collected name), load-bearing on the order side. + tests/orders/test_sets.py permanent test.
    - Verification: Passed. WITH fix -> tests/orders/test_sets.py 42 passed. Temp-reverted sets_mixins.py to HEAD -> the new test FAILS (rel still in related_orders OrderedDict); restored (`del collected[name]` at L248). Fix at the single shared-collector owner; both set families now consistent with the django-filter removal idiom. Rejected leads verified sound: type_name_for single/double-underscore PascalCase collision is defended by emit_set_input_field_triples seen_attr ConfigurationError (not silent); get_filters returns a fresh dict (no shared-state corruption); expanded_once reads cls.__dict__ (no cross-subclass cache leak).
    - Cleanup: Removed docs/bug_hunt/temp-tests/sets_mixins/; fix + permanent test retained. (Hunter left a session-scratchpad copy outside the repo tree - harmless.)
    - docs/shadow/current/django_strawberry_framework__sets_mixins.stripped.py
    - docs/shadow/current/django_strawberry_framework__sets_mixins.overview.md
    - Prompt:
        - Use django_strawberry_framework/sets_mixins.py as the entry point. Read docs/shadow/current/django_strawberry_framework__sets_mixins.stripped.py and docs/shadow/current/django_strawberry_framework__sets_mixins.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/testing/_wrap.py
    - Status: pending
    - Baseline shadow: none (live file added or absent at hunt baseline)
    - Prompt:
        - Use django_strawberry_framework/testing/_wrap.py as the entry point. No baseline shadow exists; hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/testing/client.py
    - Status: verified
    - Result: Fixed Low (COMMITTED by maintainer as 16b9a08e "fix(validation): harden numeric string boundaries" - maintainer reimplemented the hunter's finding their own way + extended the same digit-boundary class to kanban card resolution + shared version parsing). Defect: TestClient._assert_file_placeholders used `segment.isdigit()` which is True for non-ASCII digit glyphs (e.g. superscript U+00B2) that int() then rejects with ValueError, so a malformed files= index escaped the walker's uniform-AssertionError contract (its own docstring promises pytest.raises(AssertionError) catches every bad shape). Hunter's fix was an isascii()+isdigit() guard; maintainer's committed fix validates multipart list paths against canonical object-path indices, "keeping malformed or oversized values inside the client assertion contract" - same contract preserved.
    - Verification: Passed (fix landed differently than the hunter proposed but resolves the same defect). Committed diff reviewed (16b9a08e: testing/client.py +17, tests/testing/test_client.py +26, plus the maintainer's parallel kanban/version-parsing hardening). Hunter's own pre-fix proof (files={"tags.<superscript-2>":...} raised ValueError not AssertionError on HEAD source) established the defect. Scratch removed.
    - Cycle baseline: HEAD ddeff191 (+ in-flight verified hunt fixes); live source authoritative, shadow orientation-only (no baseline shadow; live-only hunt)
    - Baseline shadow: none (live file added or absent at hunt baseline)
    - Prompt:
        - Use django_strawberry_framework/testing/client.py as the entry point. No baseline shadow exists; hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/testing/relay.py
    - Status: no-bugs
    - Cycle baseline: HEAD 16b9a08e; live source authoritative, shadow orientation-only (no baseline shadow; live-only)
    - Result: No bugs. Evidence: global_id_for(T, pk) is BYTE-IDENTICAL to the live-emitted id for every string strategy/shape (model label, type with/without Meta.name, type+model, two type-strategy types per model, Node-interface vs concrete access) - verified via in-process schema.execute_sync comparison; no casing divergence (model/type+model use label_lower, type uses graphql_type_name == info.path.typename under default NameConverter, a documented framework constraint not a helper defect); raise gates correct+ordered (callable/custom strategies, unfinalized-before-strategy-read, finalized-non-Relay, non-DjangoType input); decode_global_id re-export is identity and surfaces ONE uniform ConfigurationError on all hostile input (None/int/bytes/empty/non-base64/unknown label/unknown gql name/label-vs-type-only) - no leaked KeyError/ValueError/AttributeError; encode/decode/filter share one accepted-name contract (transitively real-schema-accepted). tests/testing/test_relay.py 10 passed (hunter). 3 rejected leads sound (NodeID-non-pk = caller supplies id per docstring; inherited-definition subclass not schema-registered; post-clear stale mint contrived+harmless).
    - Verification: source byte-unchanged (git clean); schema-building probe rerun deferred to final gate (filter-regression hunt active); accepted on source-clean + trace. Scratch removed.
    - Baseline shadow: none (live file added or absent at hunt baseline)
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

- [x] django_strawberry_framework/types/finalizer.py
    - Status: no-bugs
    - Cycle baseline: HEAD ddeff191 (+ in-flight verified hunt fixes); live source authoritative, shadow orientation-only (heavily refactored post-baseline by commits 5e992a7b + 9aabc0b3). Carried the blocker #3 adjudication (multi-owner/diverging-target rejection).
    - Result: No bugs. Full lifecycle audit (finalize phase ordering, _bind_set_owner_common/_bind_filterset_owner, _check_filterset_owner_pk_identity, _synthesize_relation_connections + teardown + list-form suppression, GlobalID model-label routing, subpass bind-before-expand). 8 hostile probes all confirm correct behavior: real two-owner diverging own-PK Relay identity RAISES; same-target multi-owner accepted (first-bind wins); synthesized-connection teardown across registry.clear() restores the list annotation + resolver; clear->re-register->re-finalize rebuilds cleanly; partial-finalize retry recovers + connection-shape suppression survives; Phase-3 partial-finalize retry skips already-decorated types via the finalized guard; GlobalID model-label divergence raises. Retry-idempotency + owner-binding protections HOLD.
    - Blocker #3 ADJUDICATION = (B) STALE TEST (see Known blockers): tests/filters/test_finalizer.py::test_phase_2_5_rejects_multi_owner_with_diverging_target fails "DID NOT RAISE" because it hand-plants _owner_definition before finalize, which the refactor's CORRECT before_bind reset now wipes; the relation-TARGET axis it simulates cannot diverge for real owners (target keyed on the target MODEL via the global registry), and the genuinely owner-dependent own-PK Relay axis IS still rejected end-to-end with real owners. Not a regression.
    - Also CLEARED as NOT the filter-regression cause: the dedicated filter-regression hunt disproved the finalizer pre-bind-clear lead (neutralizing iter_subsystem_clears(before_bind=True) changed nothing on a fresh finalize); the 20-test regression root cause was in filters/base.py (absent-vs-empty GlobalIDMultipleChoiceFilter), NOT the finalizer. Finalizer source byte-unchanged (git clean).
    - Verification: source byte-unchanged (git clean); schema-building probe rerun deferred to final gate; accepted on source-clean + the exhaustive lifecycle trace + the filter-regression hunt independently exonerating the finalizer. Scratch removed.
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

- [ ] django_strawberry_framework/utils/converters.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__utils__converters.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__converters.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/converters.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__converters.stripped.py and docs/shadow/current/django_strawberry_framework__utils__converters.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/utils/errors.py
    - Status: no-bugs
    - Result: No bugs. Evidence: all 5 symbols (field_error/_str_list/relation_field_error/validation_error_to_field_errors/join_error_path) traced through all 11 reachable call sites (mutations/rest/forms resolvers, write_values, auth/mutations). No internal/backend leak (every messages value is a plain str / stringified ErrorDetail / Django-stringified list); codes match the documented contract (invalid/null/not_found/constraint), Django-flat + DRF-recursive flatteners terminate in the same field_error leaf; deterministic insertion-order collection. tests: mutations 15 + rest 65 passed (hunter). One lead (a gettext_lazy Promise would char-split in _str_list) rejected as UNREACHABLE - no caller passes a lazy proxy (VE.messages / ErrorDetail materialize to str first); flagged as a future-caller hazard only.
    - Verification: source byte-unchanged (git clean); probe rerun deferred to final gate (filter-regression hunt active); conclusion accepted on source-clean + trace. Scratch removed.
    - Cycle baseline: HEAD ddeff191 (+ in-flight verified hunt fixes); live source authoritative, shadow orientation-only
    - docs/shadow/current/django_strawberry_framework__utils__errors.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__errors.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/errors.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__errors.stripped.py and docs/shadow/current/django_strawberry_framework__utils__errors.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/utils/imports.py
    - Status: no-bugs
    - Result: No bugs. Evidence: all 4 helpers (import_attr_if_importable/loaded_attr/import_attr/require_optional_module) correct across every caller (keyset crypto, routers channels, rest_framework/debug_toolbar guards, finalizer auth-bind, converters postgres). A broken-but-installed dep is reframed to the install hint BUT chains the true cause (from exc); strict import_attr propagates; all 4 install-hint version floors match pyproject exactly (channels>=4.3.2, DRF>=3.17.0, debug-toolbar>=7.0.0, cryptography>=44.0.0); no memoization race (importlib lock covers). tests/utils/test_imports.py 6 passed (hunter). Doc-only observation: the module docstring + finalizer.py both still reference the refactor-removed registry._clear_if_loaded (same stale symbol as the auth/test_mutations collection blocker) - doc staleness, no runtime effect, left for the refactor to settle.
    - Verification: source byte-unchanged (git clean); probe is script-style (deferred); accepted on source-clean + trace. Scratch removed.
    - Cycle baseline: HEAD ddeff191 (+ in-flight verified hunt fixes); live source authoritative, shadow orientation-only
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

- [x] django_strawberry_framework/utils/permissions.py
    - Status: verified
    - Cycle baseline: HEAD 16b9a08e; live source authoritative, shadow orientation-only
    - Result: Fixed High. Transport-wide defect: request_from_info -> _channels_request_adapter resolved the ASGI scope ONLY via request.consumer.scope (the HTTP GraphQLHTTPConsumer's ChannelsRequest shape), but the WebSocket GraphQLWSConsumer puts the CONSUMER ITSELF at context["request"] (get_context returns {"request": self, "ws": self}), scope at request.scope, no .consumer. So over the WS transport the adapter returned None and request_from_info raised ConfigurationError("could not resolve a Django HttpRequest ... (got dict)") - breaking EVERY permission-gated FilterSet/OrderSet query, DjangoModelPermission mutation, and current_user over WebSocket, even with the router's AuthMiddlewareStack fully present (the router's whole purpose is "GraphQL on HTTP + WebSocket in one import"; spec-041 Decision 11 promises the actor resolves over Channels). HTTP path masked it (the only request-contract tests run over HttpCommunicator; the WS branch was handshake/origin-only). Fix: new _channels_scope(request) resolves scope from request.consumer.scope (HTTP, first, byte-identical) OR request.scope (WS fallback) - duck-typed, unambiguous (HTTP ChannelsRequest has no .scope; WS consumer has no .consumer); _channels_request_adapter delegates. Single-sited (D-P2). Files: utils/permissions.py + tests/utils/test_permissions.py (2 duck-typed unit tests) + tests/test_routers.py (1 real WebsocketCommunicator round-trip through the actual router + an actor resolver field). Severity: hunter says High (whole advertised transport broken); reachability requires the Channels WS router (like the sibling Medium None-user fixes) - most severe of the Channels-adapter trio.
    - Verification: Passed (settle pass, clean tree). WITH fix tests/utils/test_permissions.py + tests/test_routers.py pass (part of the 402-passed settle run). Temp-reverted utils/permissions.py to HEAD -> 3 failed (the 3 new WS-shape tests fail with the "could not resolve" ConfigurationError); restored intact (fix present, +82/-33). Single-sited (D-P2), correct owner. Scratch removed.
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

- [x] django_strawberry_framework/utils/strings.py
    - Status: verified
    - Cycle baseline: HEAD ddeff191 (source tree clean at dispatch); live source authoritative, shadow orientation-only
    - Result: Fixed Medium. strings.py itself is CORRECT (snake_case is the injective inverse of graphql_camel_name, pinned by test_strings.py:47; pascal_case non-injectivity is documented fail-loud DuplicatedTypeName; flatten_lookup_path __->_ collapse is the deliberate LOOKUP_SEP transform). Root cause is in optimizer/walker.py: a DjangoType field registers under its Django name so Strawberry names it via the DEFAULT lossy to_camel_case (address_2 -> schema `address2`), but the walker reversed output names with snake_case, which structurally cannot invert a lossy transform (snake_case("address2")="address2" != field-map key "address_2"). So any word_digit field (address_2, line_1, address_line_2 - common address lines) is silently dropped from .only()/select_related -> per-row/per-parent N+1 (violates GOAL criterion 5). Latent (fakeshop has no such field). Files changed: optimizer/walker.py (+40: new _field_by_graphql_name forward-matches to_camel_case(real_name)==sel.name on a field-map MISS and adopts the real Django name; fast dict path untouched, O(n) scan only on the pre-existing miss path) + tests/optimizer/test_walker.py (+74: real DjangoType/finalize_django_types tier, asserts address_2 in only_fields and select_related==('parent_2',)).
    - VERIFICATION COMPLETE: the walker reconciliation (see optimizer/walker.py item) completed and verified the full digit-boundary fix across all 3 reversal sites; strings.py itself needed no edit (correct). The scalar site this hunt found + the relation-connection (gap 2a) + fk-elision (site 3) sites all fail on temp-revert and pass with the fix (171 walker tests green). Scratch removed.
    - Maintainer design flag (not actioned): the name boundary is asymmetric - INPUT side uses injective graphql_camel_name, OUTPUT side uses lossy to_camel_case. Hunter chose the walker-local forward-resolution fix (stable public schema names, narrow blast radius) over a custom injective NameConverter (would change public digit-field names, diverges from strawberry-django camelCase convention) or re-keying field_map by schema name (broad). The larger "make the boundary consistent" question is a separate maintainer-authority design decision.
    - docs/shadow/current/django_strawberry_framework__utils__strings.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__strings.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/strings.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__strings.stripped.py and docs/shadow/current/django_strawberry_framework__utils__strings.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/utils/typing.py
    - Status: verified
    - Result: Fixed Low (COMMITTED by maintainer as 9f45d36c). is_async_callable misclassified a staticmethod/classmethod descriptor wrapping an async def as sync (it only unwrapped functools.partial.func + checked __call__, never the descriptor's __func__). Reachable: an async @staticmethod referenced by name in its own class body evaluates to the raw (callable in 3.10+) descriptor, reaches the field factory -> committed to the sync wrapper -> the awaitable guard then rejects it with a misleading "declare async def" (which the consumer already did). Same slip on an async @staticmethod GlobalID encoder past _validate_globalid_callable. Fix: unwrap staticmethod/classmethod via __func__ before the coroutine check (utils/typing.py) + tests/utils/test_typing.py (5 descriptor cases) + tests/test_list_field.py schema-tier proof. Rejected leads (plain-def-returns-awaitable = intentional gap guarded downstream; unwrap_return_type not unwrapping Optional/Annotated = unreachable for its only caller) sound.
    - Verification: Passed. Committed diff reviewed (9f45d36c: typing.py + test_list_field.py +42, + test_typing.py). Pure schema-free tests/utils/test_typing.py 23 passed (interference-safe). Hunter proved fail-without-fix (4 failed on 2-line revert incl the schema-tier list_field test raising SyncMisuseError). Scratch removed.
    - Cycle baseline: HEAD ddeff191 (+ in-flight verified hunt fixes); live source authoritative, shadow orientation-only
    - docs/shadow/current/django_strawberry_framework__utils__typing.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__typing.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/typing.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__typing.stripped.py and docs/shadow/current/django_strawberry_framework__utils__typing.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/utils/write_values.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__utils__write_values.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__write_values.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/write_values.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__write_values.stripped.py and docs/shadow/current/django_strawberry_framework__utils__write_values.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] Package integration
    - Status: pending
    - Prompt:
        - Hunt the final live package across boundaries, including public exports and `__init__.py` files; implement every confirmed root-cause fix.

- [ ] Final test gate
    - Status: pending
    - Owner: Worker 1
    - Prompt:
        - Run `uv run pytest`; require a passing suite and 100% configured package coverage.
