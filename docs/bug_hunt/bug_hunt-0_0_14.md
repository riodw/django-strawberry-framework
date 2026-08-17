# Bug hunt: 0.0.14

Status: complete
Mode: autonomous
Baseline commit: `054de9dd37a2c4181fb2a91ded57f4823a1b5220`

## Package questions

No maintainer-authored probing questions were supplied: `docs/bug_hunt/dicta.md` exists but is
empty. When this hunt was generated, `scripts/bug_hunt.py::_read_dicta` substituted its
`## Package questions` fallback only when that file was *missing*, so this run emitted an empty
section rather than the fallback text, and this heading was reconstructed during the closeout. The
generator has since been corrected to treat an empty or whitespace-only dicta the same as a missing
one. Exploration was free across the live source; shadow inputs were orientation only.

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
    - Status: verified
    - Cycle baseline: HEAD `054de9dd37a2c4181fb2a91ded57f4823a1b5220`; live target SHA-256 `0ee804a181ccf0b39ff652bd839cdf7c3c6f9736dcef5babb2022a121810fb97`; working-tree status digest `41b6394f2e205e9b7df98540aecc2c5a39d65d37bf5b5949074d866c3746010f`. The target had a pre-existing 8-line-add/3-line-delete concurrent diff at dispatch.
    - docs/shadow/current/django_strawberry_framework___boundary_ordering.stripped.py
    - docs/shadow/current/django_strawberry_framework___boundary_ordering.overview.md
    - Prompt:
        - Use django_strawberry_framework/_boundary_ordering.py as the entry point. Read docs/shadow/current/django_strawberry_framework___boundary_ordering.stripped.py and docs/shadow/current/django_strawberry_framework___boundary_ordering.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed Medium. The middleware enforced the request boundary before Django's `setup()` lifecycle, so setup-derived request-local caps could be skipped after the request was stamped. Files changed: `django_strawberry_framework/_boundary_ordering.py`, `django_strawberry_framework/middleware/request_body.py`, `django_strawberry_framework/views.py`, `examples/fakeshop/test_query/test_transport_api.py`, `tests/test_views.py`.
    - Verification: Passed. Evidence: independent live HTTP checks covered refused and accepted setup-derived caps, one setup lifecycle per request, Django setup failures, sync/async callback bookkeeping, marker fallback, and the minimal boundary protocol.
    - Validation: Worker 1 focused module 219 passed and lifecycle/bookkeeping 7 passed; Worker 0 scratch reproduction 1 passed, permanent focused verification 8 passed, wrapper/async/minimal stress selection 2 passed; ruff and diff checks passed.
    - Cleanup: Removed `docs/bug_hunt/temp-tests/boundary_ordering/`; unrelated concurrent work preserved.

- [x] django_strawberry_framework/_cross_web_patches.py
    - Status: no-bugs
    - Cycle baseline: HEAD `054de9dd37a2c4181fb2a91ded57f4823a1b5220`; live target SHA-256 `c73a65a9eb2f2937a688e88dc362da7de1aec6c9f53e3a8bb88b7911096d7224`; working-tree status digest `df6aaf8a3ca80f4718933a4e8d699ae102bb74293312c1e1cc1d50928788aad2`. The target had a pre-existing 53-line-add/25-line-delete concurrent diff at dispatch.
    - docs/shadow/current/django_strawberry_framework___cross_web_patches.stripped.py
    - docs/shadow/current/django_strawberry_framework___cross_web_patches.overview.md
    - Prompt:
        - Use django_strawberry_framework/_cross_web_patches.py as the entry point. Read docs/shadow/current/django_strawberry_framework___cross_web_patches.stripped.py and docs/shadow/current/django_strawberry_framework___cross_web_patches.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: traced app startup and settings gates, upstream sync/async adapters, package-view isolation, property reversion/idempotence, missing/changed upstream shapes, byte identity and failure propagation, and live upstream/package mounts.
    - Verification: Passed. Worker 0 independently reran 20 unit/hostile probes and 3 live HTTP transport checks; the target hash remained the dispatch baseline.
    - Cleanup: Removed `docs/bug_hunt/temp-tests/cross_web_patches/`; unrelated concurrent work preserved.

- [x] django_strawberry_framework/_django_patches.py
    - Status: verified
    - Cycle baseline: HEAD `054de9dd37a2c4181fb2a91ded57f4823a1b5220`; live target SHA-256 `9a11581e37c921946560aee872d80373c8a475553e3c85d7152da7ab9ecc890a`; working-tree status digest `9fa00cdb8d1e0c298a8d317774a74dc03cb40791aa40646dd51f906336259890`. The target was clean at dispatch.
    - docs/shadow/current/django_strawberry_framework___django_patches.stripped.py
    - docs/shadow/current/django_strawberry_framework___django_patches.overview.md
    - Prompt:
        - Use django_strawberry_framework/_django_patches.py as the entry point. Read docs/shadow/current/django_strawberry_framework___django_patches.stripped.py and docs/shadow/current/django_strawberry_framework___django_patches.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed Medium. Django 6.1 setup wraps the connection feature-list methods, but teardown inferred its list from a consumer subclass's retained legacy attribute and could leave shared connection methods prohibited. Files changed: `django_strawberry_framework/_django_patches.py`, `tests/test_django_patches.py`.
    - Verification: Passed. The validated audited upstream body now selects the matching teardown source; Worker 0 independently covered both supported layouts, the conflicting legacy-subclass reproduction, repeated apply/revert, wrap-time cooperation, and AppConfig startup.
    - Validation: Worker 1 connected checks 34 passed; Worker 0 independent connected checks 34 passed; ruff and diff checks passed.
    - Cleanup: Removed `docs/bug_hunt/temp-tests/django_patches/`; unrelated concurrent work preserved.

- [x] django_strawberry_framework/_request_body.py
    - Status: verified
    - Cycle baseline: HEAD `054de9dd37a2c4181fb2a91ded57f4823a1b5220`; live target SHA-256 `9a4d07e2a6edfad2717d0fa9e5f9c882967f2b896bd79747f66e52afdf260295`; working-tree status digest `41be6cd0f361fc109c681de270f29ee8dd71c3a3cfafafb02978f66bed71a0e8`. The target had a pre-existing 24-line-add/9-line-delete concurrent diff at dispatch.
    - docs/shadow/current/django_strawberry_framework___request_body.stripped.py
    - docs/shadow/current/django_strawberry_framework___request_body.overview.md
    - Prompt:
        - Use django_strawberry_framework/_request_body.py as the entry point. Read docs/shadow/current/django_strawberry_framework___request_body.stripped.py and docs/shadow/current/django_strawberry_framework___request_body.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed Medium: a foreign truthy zero-length result from `request.read()` could repeatedly leave the bounded-read counter unchanged, hanging request handling. The bounded reader now requires an exact `bytes` chunk before any foreign truth or length protocol can run, then fails closed through the existing 413/warning path.
    - Verification: Worker 0 independently inspected the guard, permanent sync/async regression, and disposable hostile-stream reproduction; the repro makes exactly one read and cannot execute its truth or length hooks.
    - Validation: Worker 1 focused view tests 219 passed and live body-cap tests 18 passed; Worker 0 scratch plus permanent selection 2 passed; diff check and ruff passed.
    - Cleanup: Removed `docs/bug_hunt/temp-tests/request_body/`; unrelated concurrent changes retained.

- [x] django_strawberry_framework/_strawberry_patches.py
    - Status: verified
    - Cycle baseline: HEAD `054de9dd37a2c4181fb2a91ded57f4823a1b5220`; live target SHA-256 `8c9b454c838d1ce3b2d42153ada8d9fa20356cb7fce089ed33efd58c52cf7427`; working-tree status digest `ac6b14ef78bf35c223783d4458a0c7fca0f2f5943eefb3618132d3838171aebb`. The target was clean at dispatch.
    - docs/shadow/current/django_strawberry_framework___strawberry_patches.stripped.py
    - docs/shadow/current/django_strawberry_framework___strawberry_patches.overview.md
    - Prompt:
        - Use django_strawberry_framework/_strawberry_patches.py as the entry point. Read docs/shadow/current/django_strawberry_framework___strawberry_patches.stripped.py and docs/shadow/current/django_strawberry_framework___strawberry_patches.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed Medium: a list-valued multipart `map` passed the general batch-envelope guard but Strawberry's upload utility then called `.items()` and leaked an unhandled 500. Sync and async multipart delegates now translate structural traversal failures to Strawberry's ordinary 400 while preserving valid batched operations and non-structural parser errors. Files changed: `django_strawberry_framework/_strawberry_patches.py`, `tests/test_strawberry_patches.py`, `examples/fakeshop/test_query/test_transport_api.py`.
    - Verification: Passed. Worker 0 confirmed the retained pre-fix probe's direct `AttributeError` and live 500 expectations now fail specifically because the patched paths return 400, then independently passed the complete unit lifecycle/shape suite and the live sync/async multipart rows.
    - Validation: Worker 1 `tests/test_strawberry_patches.py` 51 passed and live multipart-map selection 2 passed; Worker 0 independently reran the same 51 and 2; diff check and ruff passed.
    - Cleanup: Removed `docs/bug_hunt/temp-tests/strawberry_patches/`; unrelated concurrent changes retained.

- [x] django_strawberry_framework/apps.py
    - Status: verified
    - Cycle baseline: HEAD `054de9dd37a2c4181fb2a91ded57f4823a1b5220`; live target SHA-256 `70d5aaec41c1057353d6e0b62834920934855462bbf547f6e7a9b997797c558e`; working-tree status digest `0fe3cb389a56020668f30a6e8202ca4879a196a078fc0397772cf0aecee534d0`. The target was clean at dispatch.
    - docs/shadow/current/django_strawberry_framework__apps.stripped.py
    - docs/shadow/current/django_strawberry_framework__apps.overview.md
    - Prompt:
        - Use django_strawberry_framework/apps.py as the entry point. Read docs/shadow/current/django_strawberry_framework__apps.stripped.py and docs/shadow/current/django_strawberry_framework__apps.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed Medium. Reloading an installed upstream-patch module made its import-time capture mistake the package wrapper for the genuine dependency implementation; the next `AppConfig.ready()` then raised false shape drift or silently weakened validation. Each patch module now tags a replacement with its true original and restores that original capture across in-process reloads. Files changed: `django_strawberry_framework/_django_patches.py`, `django_strawberry_framework/_strawberry_patches.py`, `django_strawberry_framework/_cross_web_patches.py`, `tests/test_apps.py`; `apps.py` itself remained dispatch-byte-identical.
    - Verification: Passed. Worker 0 inspected the cross-module original-capture protocol and independently ran the registered AppConfig through two reload/reinstall cycles for every applier, confirming all patches are reinstalled from their genuine upstream originals.
    - Validation: Worker 1 focused application tests 8 passed, connected lifecycle tests 92 passed, and live transport selection 4 passed; Worker 0 independently reran connected 92 and live 4; diff check and ruff passed.
    - Cleanup: Removed `docs/bug_hunt/temp-tests/apps/`; unrelated concurrent changes retained.

- [x] django_strawberry_framework/auth/mutations.py
    - Status: verified
    - Cycle baseline: HEAD `054de9dd37a2c4181fb2a91ded57f4823a1b5220`; live target SHA-256 `32097539c9452c0af42cf2736180685d88f34778b7e10c8e188bd651295f1ee8`; working-tree status digest `129cf00b6e9b2c023a495fd1f6fdaf7d9226bcd9683a0eb070db9dd9f55faf2a`. The target was clean at dispatch.
    - docs/shadow/current/django_strawberry_framework__auth__mutations.stripped.py
    - docs/shadow/current/django_strawberry_framework__auth__mutations.overview.md
    - Prompt:
        - Use django_strawberry_framework/auth/mutations.py as the entry point. Read docs/shadow/current/django_strawberry_framework__auth__mutations.stripped.py and docs/shadow/current/django_strawberry_framework__auth__mutations.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed Medium. Login establishment correctly compensates after its primary failure, but a cancellation raised while flushing that compensation escaped the `Exception` handler and replaced the primary error. Both Django HTTP and Channels HTTP now preserve the primary error and chain cleanup cancellation as its context. Files changed: `django_strawberry_framework/auth/mutations.py`, `tests/auth/test_mutations.py`.
    - Verification: Passed. Worker 0 inspected both compensation paths and independently proved a cleanup `CancelledError` is chained below the original login-signal failure rather than replacing it.
    - Validation: Worker 1 and Worker 0 each ran retained scratch plus focused auth tests: 94 passed; diff check and ruff passed.
    - Cleanup: Removed `docs/bug_hunt/temp-tests/auth_mutations/`; unrelated concurrent changes retained.

- [x] django_strawberry_framework/auth/queries.py
    - Status: verified
    - Cycle baseline: HEAD `054de9dd37a2c4181fb2a91ded57f4823a1b5220`; live target SHA-256 `e898eb702d2310ed6464e4aff8a2be584151c8d427e8daec475dd8c13a2ace95`; working-tree status digest `4e4e9f8143555dcfdd082c3fa73234b1319b1f2d22538ea55c5bce532ab69907`. The target was clean at dispatch.
    - docs/shadow/current/django_strawberry_framework__auth__queries.stripped.py
    - docs/shadow/current/django_strawberry_framework__auth__queries.overview.md
    - Prompt:
        - Use django_strawberry_framework/auth/queries.py as the entry point. Read docs/shadow/current/django_strawberry_framework__auth__queries.stripped.py and docs/shadow/current/django_strawberry_framework__auth__queries.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed Medium. Direct Strawberry schema execution's normal mapping context (`{"request": HttpRequest}`) was rejected by the shared request resolver, making `current_user()` return a top-level configuration error. The resolver now recognizes a mapping-held Django request before attempting Channels adaptation. Files changed: `django_strawberry_framework/utils/permissions.py`, `tests/utils/test_permissions.py`, `tests/auth/test_queries.py`.
    - Verification: Passed. Worker 0 independently inspected mapping precedence against Django and Channels paths, then ran the disposable direct-schema reproduction plus utility, auth-query, and live auth tests.
    - Validation: Worker 1 focused checks 67 passed; Worker 0 connected replay 68 passed (including retained scratch); diff check and ruff passed.
    - Cleanup: Removed `docs/bug_hunt/temp-tests/auth_queries/`; unrelated concurrent changes retained.

- [x] django_strawberry_framework/auth/sessions.py
    - Status: verified
    - Cycle baseline: HEAD `054de9dd37a2c4181fb2a91ded57f4823a1b5220`; live target SHA-256 `e408121138f103f10067c736ab167c3dfebe4037042cba6298f351a8232d9938`; working-tree status digest `b17f00e85c4b63cdbbdda299df706c3ab166db2605766f6e0f4e4b21dd31ca35`. The target was clean at dispatch.
    - docs/shadow/current/django_strawberry_framework__auth__sessions.stripped.py
    - docs/shadow/current/django_strawberry_framework__auth__sessions.overview.md
    - Prompt:
        - Use django_strawberry_framework/auth/sessions.py as the entry point. Read docs/shadow/current/django_strawberry_framework__auth__sessions.stripped.py and docs/shadow/current/django_strawberry_framework__auth__sessions.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed Low documentation defect; no production-code defect confirmed. The auth glossary incorrectly promised Django's own failure for missing sessions and made AuthenticationMiddleware a direct mutation prerequisite. It now states the owned `SessionMiddleware` configuration guard and AuthenticationMiddleware's later actor-loading role. Files changed: the `auth-mutations` term body in the fakeshop glossary app's database (`examples/fakeshop/db.sqlite3`), which is the source of truth, plus the `docs/GLOSSARY.md` render published by the cycle's doc-regeneration commit. Two record corrections on this item: the original entry named only the generated `docs/GLOSSARY.md`, which a re-render would have discarded had the database not also been corrected; and the database write bypassed `Model.save()`, so the term's `auto_now` `updated_date` still reads `2026-07-30` and does not reflect this change.
    - Verification: Passed. Worker 0 inspected the guard ownership and independently replayed hostile scope/session-lock probes plus permanent session and live auth tests; the implementation kept scope-owned session isolation, cancellation-safe lock identity, and supported transport semantics.
    - Validation: Worker 1 hostile/target selection 36 passed and target/live checks 46 passed; Worker 0 replay 48 passed; diff check and ruff passed.
    - Cleanup: Removed `docs/bug_hunt/temp-tests/auth_sessions/`; unrelated concurrent changes retained.

- [x] django_strawberry_framework/conf.py
    - Status: no-bugs
    - Cycle baseline: HEAD `054de9dd37a2c4181fb2a91ded57f4823a1b5220`; live target SHA-256 `c6d736ba41b4d6012c84f74bd511fdebda247f8d8de885843df0c9a64f165a54`; working-tree status digest `728849659ec84927dd10798caa224a5d3b3502d0700f06e626791cbb2f2059fb`. The target had a pre-existing 19-line-add/6-line-delete concurrent diff at dispatch.
    - docs/shadow/current/django_strawberry_framework__conf.stripped.py
    - docs/shadow/current/django_strawberry_framework__conf.overview.md
    - Prompt:
        - Use django_strawberry_framework/conf.py as the entry point. Read docs/shadow/current/django_strawberry_framework__conf.stripped.py and docs/shadow/current/django_strawberry_framework__conf.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No additional bugs. Evidence: traced Django-backed versus explicit settings caches, replacement/deletion and in-place mutation, signal reload, atomic normalization, strict upstream-gate validation, and all major setting consumers. The dispatch-time concurrent direct-reload correction is consistent with that contract and was preserved.
    - Verification: Passed. Worker 0 independently reran hostile cache/signal probes plus focused settings tests; the live source remained at the dispatch SHA and the concurrent diff was not absorbed.
    - Validation: Worker 1 focused scratch/config 51 passed and connected consumer suite 297 passed; Worker 0 scratch/config 51 passed; diff check and ruff passed.
    - Cleanup: Removed `docs/bug_hunt/temp-tests/conf/`; unrelated concurrent changes retained.

- [x] django_strawberry_framework/connection.py
    - Status: verified
    - Cycle baseline: HEAD `054de9dd37a2c4181fb2a91ded57f4823a1b5220`; live target SHA-256 `f2554a3a69117529fdde92ac9ea3a523d104f5ad39abb25005a4de7c4394f0ba`; working-tree status digest `728849659ec84927dd10798caa224a5d3b3502d0700f06e626791cbb2f2059fb`. The target had a pre-existing 47-line-add/15-line-delete concurrent diff at dispatch.
    - docs/shadow/current/django_strawberry_framework__connection.stripped.py
    - docs/shadow/current/django_strawberry_framework__connection.overview.md
    - Prompt:
        - Use django_strawberry_framework/connection.py as the entry point. Read docs/shadow/current/django_strawberry_framework__connection.stripped.py and docs/shadow/current/django_strawberry_framework__connection.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed Medium. A plain synchronous resolver could return an async-only iterable at runtime and bypass the declaration-based async-generator guard, leaving Strawberry's synchronous Relay slicer to fail with a blank internal assertion. The connection resolver now checks the actual returned source and raises the package's actionable `SyncMisuseError` in synchronous execution while preserving native async execution and dual sync/async iterables such as Django querysets. Files changed: `django_strawberry_framework/connection.py`, `tests/test_connection.py`.
    - Verification: Passed. Worker 0 independently inspected the runtime-source guard and replayed the retained hostile cases for declared and runtime-returned async iterables, async pagination and total-count behavior, plus the complete live connection selection.
    - Validation: Worker 1 focused package/keyset plus scratch checks 96 passed and live connection checks 44 passed; Worker 0 independently reran the same 96 and 44; current target SHA-256 `8db2ac5eb1bca4e5b43b730b6fc31d295696360af73de6791783572a5b2ad75b`; diff check passed.
    - Cleanup: Removed `docs/bug_hunt/temp-tests/connection/`; unrelated concurrent changes retained.

- [x] django_strawberry_framework/consumers.py
    - Status: verified
    - Cycle baseline: HEAD `054de9dd37a2c4181fb2a91ded57f4823a1b5220`; live target SHA-256 `ce804395d6a5c0b6216c2ed0870e7b173790729f2fb1370182c305c29ef74240`; working-tree status digest `4e6e1ae501d76f5614b398ed67b6e36321194b5346410b3bfa9f91e24f24f1d6`. The target had a pre-existing 33-line-add/23-line-delete concurrent diff at dispatch.
    - docs/shadow/current/django_strawberry_framework__consumers.stripped.py
    - docs/shadow/current/django_strawberry_framework__consumers.overview.md
    - Prompt:
        - Use django_strawberry_framework/consumers.py as the entry point. Read docs/shadow/current/django_strawberry_framework__consumers.stripped.py and docs/shadow/current/django_strawberry_framework__consumers.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed Low. The stop-aware result wrapper unconditionally awaited `source.aclose()`, but legacy Strawberry handlers accept valid async iterators that expose no optional `aclose` hook. Cleanup now calls that hook only when present, preserving older async-iterator compatibility. Files changed: `django_strawberry_framework/consumers.py`, `tests/test_routers.py`.
    - Verification: Passed. Worker 0 independently replayed the no-`aclose` scratch, the complete router/consumer suite, and the live fakeshop transport suite; the existing revocation, lifecycle, and protocol behavior remained green.
    - Validation: Worker 1 reported router/consumer 155 passed and live transport 77 passed; Worker 0 independently ran scratch plus `tests/test_routers.py` (156 passed) and `examples/fakeshop/test_query/test_transport_api.py` (77 passed); current target SHA-256 `22e5a83217298db9db6feba751c8d387ccc91a745e9774f9b686ccd3ea3a303b`; diff check passed.
    - Cleanup: Removed `docs/bug_hunt/temp-tests/consumers/`; unrelated concurrent changes retained.

- [x] django_strawberry_framework/error_policy.py
    - Status: verified
    - Cycle baseline: HEAD `054de9dd37a2c4181fb2a91ded57f4823a1b5220`; live target SHA-256 `a51e54e49a159c45bcf494bffe68a59d049d36e09e135ef8ad54f200018294e1`; working-tree status digest `b4ad1bbb8650a809364ea1da1ec80ac681f1efe8dc957fb3870c0b1b2047c5e6`. The target was clean at dispatch.
    - docs/shadow/current/django_strawberry_framework__error_policy.stripped.py
    - docs/shadow/current/django_strawberry_framework__error_policy.overview.md
    - Prompt:
        - Use django_strawberry_framework/error_policy.py as the entry point. Read docs/shadow/current/django_strawberry_framework__error_policy.stripped.py and docs/shadow/current/django_strawberry_framework__error_policy.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed Medium in the connected `extensions/error_policy.py` layer. `masking_is_active()` relied on truthiness for `settings.DEBUG`, so malformed truthy values such as `"False"` or `1` disabled production masking and leaked resolver exception text. The development bypass now opens only for exact boolean `True`; existing fail-closed result-adoption behavior is preserved. Files changed: `django_strawberry_framework/extensions/error_policy.py`, `tests/test_error_policy.py`, `examples/fakeshop/test_query/test_error_policy_api.py`.
    - Verification: Passed. Worker 0 independently replayed hostile configuration and result-shape probes, malformed-`DEBUG` package regressions, and live HTTP masking; literal `DEBUG=True` remains the only pass-through.
    - Validation: Worker 1 reported scratch 10, package 47, and live 18 passed; Worker 0 independently ran scratch + package + live together (75 passed); current target SHA-256 `a51e54e49a159c45bcf494bffe68a59d049d36e09e135ef8ad54f200018294e1`; connected extension SHA-256 `d5b35f1fb384e3894ead23967daf46151628b3fb926f4bd1e5a42e997bf0c852`; diff check passed.
    - Cleanup: Removed `docs/bug_hunt/temp-tests/error_policy/`; unrelated concurrent changes retained.

- [x] django_strawberry_framework/exceptions.py
    - Status: verified
    - Cycle baseline: HEAD `054de9dd37a2c4181fb2a91ded57f4823a1b5220`; live target SHA-256 `c5656f6bd31a6c142f3b5789d2c4487cc12070be6e69e0e17248d254de92348c`; working-tree status digest `754d5037cc989f3bb1e741dad25d69d987c702cb05ff417a46ab53f4eecb010b`. The target was clean at dispatch.
    - docs/shadow/current/django_strawberry_framework__exceptions.stripped.py
    - docs/shadow/current/django_strawberry_framework__exceptions.overview.md
    - Prompt:
        - Use django_strawberry_framework/exceptions.py as the entry point. Read docs/shadow/current/django_strawberry_framework__exceptions.stripped.py and docs/shadow/current/django_strawberry_framework__exceptions.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed Medium. `PathResolutionError` and `LookupValidationError` interpolated model/terminal metadata and diagnostic values with raw attribute access and `repr`, so hostile metadata could replace the promised typed configuration error with a raw exception. Guarded model/terminal labels and safe argument reprs now preserve the typed error while retaining original objects on the exception. Files changed: `django_strawberry_framework/exceptions.py`, `tests/test_exceptions.py`.
    - Verification: Passed. Worker 0 independently replayed hostile metadata/type-name/repr probes and relation callers; constructor diagnostics stayed typed and retained object identity.
    - Validation: Worker 1 reported 124 focused tests passed; Worker 0 ran scratch + `tests/test_exceptions.py` + relation/relay callers (211 passed); current target SHA-256 `29fede7440d5c728f95409053c318d62e97b2ed9b4ed67e441097eef5d164071`; diff check passed.
    - Cleanup: Removed `docs/bug_hunt/temp-tests/exceptions/`; unrelated concurrent changes retained.

- [x] django_strawberry_framework/extensions/debug.py
    - Status: no-bugs
    - Cycle baseline: HEAD `054de9dd37a2c4181fb2a91ded57f4823a1b5220`; live target SHA-256 `eecb51cd920992afe894b3f33c2e2c49edec2633fdc15a773cabe04dfcc3b01b`; working-tree status digest `1e158c5d88b9388c05749a6f45b8294e788dd9ee789db90e21b838be9ed8ca6d`. The target had a pre-existing 3-line-add/1-line-delete concurrent diff at dispatch.
    - docs/shadow/current/django_strawberry_framework__extensions__debug.stripped.py
    - docs/shadow/current/django_strawberry_framework__extensions__debug.overview.md
    - Prompt:
        - Use django_strawberry_framework/extensions/debug.py as the entry point. Read docs/shadow/current/django_strawberry_framework__extensions__debug.stripped.py and docs/shadow/current/django_strawberry_framework__extensions__debug.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No additional bugs. The existing exact-boolean `settings.DEBUG` gate, cursor-coordinator restoration, nested sync capture, async exception capture, malformed SQL-log degradation, payload caps, and debug-extension lifecycle all held under hostile probes and live requests.
    - Verification: Passed. Worker 0 independently replayed the retained scratch and the package/live debug suites; the target remained at its dispatch SHA and its pre-existing concurrent diff was preserved.
    - Validation: Worker 1 reported scratch + package 72 passed and live 12 passed; Worker 0 independently ran scratch + `tests/extensions/test_debug.py` + `examples/fakeshop/test_query/test_debug_extension_api.py` (84 passed); current target SHA-256 `eecb51cd920992afe894b3f33c2e2c49edec2633fdc15a773cabe04dfcc3b01b`; diff check passed.
    - Cleanup: Removed `docs/bug_hunt/temp-tests/debug/`; unrelated concurrent changes retained.

- [x] django_strawberry_framework/extensions/error_policy.py
    - Status: no-bugs
    - Cycle baseline: HEAD `054de9dd37a2c4181fb2a91ded57f4823a1b5220`; live target SHA-256 `d5b35f1fb384e3894ead23967daf46151628b3fb926f4bd1e5a42e997bf0c852`; working-tree status digest `3a0269e8def517b345249b2c1123244072c5e4da75fd6298369c6619e4bb7cbc`. The target had a pre-existing 26-line-add/7-line-delete concurrent diff at dispatch, including the connected exact-boolean debug gate and fail-closed result-adoption changes.
    - docs/shadow/current/django_strawberry_framework__extensions__error_policy.stripped.py
    - docs/shadow/current/django_strawberry_framework__extensions__error_policy.overview.md
    - Prompt:
        - Use django_strawberry_framework/extensions/error_policy.py as the entry point. Read docs/shadow/current/django_strawberry_framework__extensions__error_policy.stripped.py and docs/shadow/current/django_strawberry_framework__extensions__error_policy.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No additional bugs. The existing masking gate and fail-closed result adoption survived hostile error/result objects, unreadable lists, result subclasses, failed data adoption, malformed `DEBUG`, result-shape filtering, sync/async operation teardown, and live HTTP behavior.
    - Verification: Passed. Worker 0 independently replayed the retained hostile probe and connected package/router/live suites; no additional production delta was needed.
    - Validation: Worker 1 reported scratch + package/live 76 passed; Worker 0 ran scratch + `tests/test_error_policy.py` + `tests/test_routers.py` + live policy tests (231 passed); current target SHA-256 `d5b35f1fb384e3894ead23967daf46151628b3fb926f4bd1e5a42e997bf0c852`; diff check passed.
    - Cleanup: Removed `docs/bug_hunt/temp-tests/extensions_error_policy/`; unrelated concurrent changes retained.

- [x] django_strawberry_framework/extensions/resource_policy.py
    - Status: verified
    - Cycle baseline: HEAD `054de9dd37a2c4181fb2a91ded57f4823a1b5220`; live target SHA-256 `39615dcb2ad970930801bb8d6ee493eb920847dd00d0ea443f82a535b69b56ff`; working-tree status digest `cd6d5226c0ccee560e1c54d91d08ffb8ae6d1cb6ecea245f07aedf7646cb33ee`. The target had a pre-existing 16-line-add/1-line-delete concurrent diff at dispatch.
    - docs/shadow/current/django_strawberry_framework__extensions__resource_policy.stripped.py
    - docs/shadow/current/django_strawberry_framework__extensions__resource_policy.overview.md
    - Prompt:
        - Use django_strawberry_framework/extensions/resource_policy.py as the entry point. Read docs/shadow/current/django_strawberry_framework__extensions__resource_policy.stripped.py and docs/shadow/current/django_strawberry_framework__extensions__resource_policy.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed two Medium defects. Scalar values coerced by GraphQL into list inputs were missing the synthetic list node and family/depth charge, allowing `max_input_nodes` / related bounds to be undercounted. Upload descriptors whose `size` property raised escaped as arbitrary exceptions instead of a fail-closed `ResourceLimitExceeded`; the boundary now wraps that failure with its cause. Files changed: `django_strawberry_framework/extensions/resource_policy.py`, `tests/test_resource_policy.py`.
    - Verification: Passed. Worker 0 independently replayed overlapping extension-instance context cleanup, nested scalar-list coercion, hostile upload descriptors, and the package/live resource-policy matrix.
    - Validation: Worker 1 reported scratch + package 91 passed and package/live 123 passed; Worker 0 independently ran scratch + package + live (126 passed); current target SHA-256 `8365a9bed72d568cb931842e163938f604e221872bfc272d0b5e0d70cf7f5446`; diff check passed.
    - Cleanup: Removed `docs/bug_hunt/temp-tests/resource_policy/`; unrelated concurrent changes retained.

- [x] django_strawberry_framework/filters/base.py
    - Status: verified
    - Cycle baseline: HEAD `054de9dd37a2c4181fb2a91ded57f4823a1b5220`; live target SHA-256 `88315f659586e9d2b6d4cbc395f7a825ceb35cb46602c69552a2746476bcaa7e`; working-tree status digest `cd6d5226c0ccee560e1c54d91d08ffb8ae6d1cb6ecea245f07aedf7646cb33ee`. The target was clean at dispatch.
    - docs/shadow/current/django_strawberry_framework__filters__base.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__base.overview.md
    - Prompt:
        - Use django_strawberry_framework/filters/base.py as the entry point. Read docs/shadow/current/django_strawberry_framework__filters__base.stripped.py and docs/shadow/current/django_strawberry_framework__filters__base.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed Medium. `GlobalIDMultipleChoiceFilter.filter()` leaked raw `TypeError` for iterator, scalar, and object inputs because it called `len()` before validating the container. The new helper accepts only list/tuple containers and returns the package's coded `GLOBALID_INVALID` GraphQL error for malformed shapes. Files changed: `django_strawberry_framework/filters/base.py`, `tests/filters/test_base.py`.
    - Verification: Passed. Worker 0 independently ran the retained adversarial probe and the package filter suite, confirming malformed containers fail closed while valid GlobalID filter behavior remains intact; live library filter/GlobalID coverage also passed.
    - Validation: Worker 1 reported scratch + package 89 passed and live 41 passed; Worker 0 independently ran scratch + package (94 passed) and live filter/GlobalID selection (31 passed); formatter/linter and diff checks passed.
    - Cleanup: Removed `docs/bug_hunt/temp-tests/filters_base/`; unrelated concurrent work preserved.

- [x] django_strawberry_framework/filters/factories.py
    - Status: verified
    - Cycle baseline: HEAD `054de9dd37a2c4181fb2a91ded57f4823a1b5220`; live target SHA-256 `c0053cd8ef90f59991512f29ff96037afce6b92dff473cfdff2e31c24ad41e61`; working-tree status digest `aeecc46f4220c3e4e49a222b3241cbd6aff5d90cd151ce3cb4139df53be639c2`. The target was clean at dispatch.
    - docs/shadow/current/django_strawberry_framework__filters__factories.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__factories.overview.md
    - Prompt:
        - Use django_strawberry_framework/filters/factories.py as the entry point. Read docs/shadow/current/django_strawberry_framework__filters__factories.stripped.py and docs/shadow/current/django_strawberry_framework__filters__factories.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed Medium. `get_filterset_class()` leaked `TypeError` when opaque unhashable `Meta` values or scalar unhashable `fields` entered the dynamic cache key. `_make_hashable()` now uses an identity discriminator for opaque unhashable values and raw fields use the shared normalizer. Files changed: `django_strawberry_framework/filters/factories.py`, `tests/filters/test_factories.py`.
    - Verification: Passed. Worker 0 independently reran the retained unhashable-cache probe and the package factory suite (32 passed); the corrected cache builds and reuses the same opaque object while keeping distinct objects separate.
    - Validation: Worker 1 reported package 32 passed and live filter/product coverage passed; formatter/linter and diff checks passed. Worker 0 independently confirmed the scratch/package matrix and live filter/product selection completed successfully.
    - Cleanup: Removed `docs/bug_hunt/temp-tests/filters_factories/`; unrelated concurrent work preserved.

- [x] django_strawberry_framework/filters/inputs.py
    - Status: verified
    - Cycle baseline: HEAD `054de9dd37a2c4181fb2a91ded57f4823a1b5220`; live target SHA-256 `dc73ae1ef97c8ddd383bc305a7097432c23ee88e0862319781de246a2c5a54dd`; working-tree status digest `d3fff58f0db373d3a353955955957a1a9facae05d43b61b58d097e28200d5614`. The target was already modified by concurrent work at dispatch; preserve unrelated changes and compare against this live baseline.
    - docs/shadow/current/django_strawberry_framework__filters__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__inputs.overview.md
    - Prompt:
        - Use django_strawberry_framework/filters/inputs.py as the entry point. Read docs/shadow/current/django_strawberry_framework__filters__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__filters__inputs.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed Medium. Declared filter attributes ending in a lookup token (for example `name__exact`) were mis-grouped as auto-generated lookup paths, so normalization emitted `name` instead of the declared Django form key and silently dropped the predicate. Safe diagnostic rendering also now prevents hostile `__repr__` implementations from escaping as arbitrary exceptions. Files changed: `django_strawberry_framework/filters/inputs.py`, `tests/filters/test_inputs.py` (preserving concurrent namespace/lifecycle and declared-filter work).
    - Verification: Passed. Worker 0 independently ran the retained adversarial probe and `tests/filters/test_inputs.py` (73 passed), confirming declared-key normalization and typed hostile diagnostics; malformed scalar list inputs remain outside the documented Strawberry-shaped helper contract.
    - Validation: Worker 1 reported 73 package tests passed; formatter/linter and diff checks passed. Worker 0 reran the same package suite and the scratch probe successfully.
    - Cleanup: Removed `docs/bug_hunt/temp-tests/filters_inputs/`; unrelated concurrent work preserved.

- [x] django_strawberry_framework/filters/sets.py
    - Status: verified
    - Cycle baseline: HEAD `054de9dd37a2c4181fb2a91ded57f4823a1b5220`; live target SHA-256 `d6023f96d378d5f1a5abae0792dcb5bcc1a7e14eade7c42b2510eb863af53e99`; working-tree status digest `b52150ef92a2d43d399336300cb123901712e159f78e45359a0bfa4cbb35945f`. The target was already modified by concurrent work at dispatch; preserve unrelated changes and compare against this live baseline.
    - docs/shadow/current/django_strawberry_framework__filters__sets.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__sets.overview.md
    - Prompt:
        - Use django_strawberry_framework/filters/sets.py as the entry point. Read docs/shadow/current/django_strawberry_framework__filters__sets.stripped.py and docs/shadow/current/django_strawberry_framework__filters__sets.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed Medium. Malformed logical-branch elements interpolated raw `repr(element)` while constructing `ConfigurationError`, allowing hostile objects to replace the typed error with arbitrary exceptions. The diagnostic now reuses the safe renderer from `filters.inputs`. The final-gate revision also restores filter ownership semantics: Relay-policy hook overrides are marked consumer-owned, scalar capability overrides retain candidate metadata but remain non-routable, and explicit `filter_overrides` `distinct=False` is preserved while omitted distinct still gets duplicate suppression. Files changed: `django_strawberry_framework/filters/sets.py`, `tests/filters/test_sets.py`.
    - Verification: Passed. Worker 0 reproduced the hostile logical element, corrected the two final-gate regressions, and reran the full package FilterSet suite (514 passed), including sync/async, logical/related, provenance, and distinct behavior.
    - Validation: Worker 1 revision audit passed; formatter/linter and diff checks passed.
    - Cleanup: Removed `docs/bug_hunt/temp-tests/filters_sets/`; unrelated concurrent work preserved.

- [x] django_strawberry_framework/forms/converter.py
    - Status: verified
    - Cycle baseline: HEAD `054de9dd37a2c4181fb2a91ded57f4823a1b5220`; live target SHA-256 `31cf6c9c2fe85d126e78576320284120c5dfee9a3e68ae1093d1e6b52c537e96`; working-tree status digest `623a10499fb9185723144064807893a6251af9114778ae5bfe6cac5c5bcfc19b`. The target was clean at dispatch.
    - docs/shadow/current/django_strawberry_framework__forms__converter.stripped.py
    - docs/shadow/current/django_strawberry_framework__forms__converter.overview.md
    - Prompt:
        - Use django_strawberry_framework/forms/converter.py as the entry point. Read docs/shadow/current/django_strawberry_framework__forms__converter.stripped.py and docs/shadow/current/django_strawberry_framework__forms__converter.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed Medium. Unsupported custom form fields with hostile `__repr__` implementations could escape the intended `ConfigurationError` as `RuntimeError` or `KeyboardInterrupt`. Safe type-name and representation rendering now preserves the typed diagnostic. Files changed: `django_strawberry_framework/forms/converter.py`, `tests/forms/test_converter.py`.
    - Verification: Passed. Worker 0 independently reran hostile `RuntimeError` and `KeyboardInterrupt` probes and the converter package suite (28 passed); both malformed fields now produce the controlled configuration error.
    - Validation: Worker 1 reported 28 focused converter tests and 22 live form-mutation tests; formatter/linter and diff checks passed.
    - Cleanup: Removed `docs/bug_hunt/temp-tests/forms_converter/`; unrelated concurrent work preserved.

- [x] django_strawberry_framework/forms/inputs.py
    - Status: verified
    - Cycle baseline: HEAD `054de9dd37a2c4181fb2a91ded57f4823a1b5220`; live target SHA-256 `ae9b67706066c24c12265bbc7b54cb52145254b7b58808ecb95bc7a39ca48f07`; working-tree status digest `2b73e998ff33bf8999828bbfc266826d0df904b1e061e2b311e81860f8366695`. The target was clean at dispatch.
    - docs/shadow/current/django_strawberry_framework__forms__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__forms__inputs.overview.md
    - Prompt:
        - Use django_strawberry_framework/forms/inputs.py as the entry point. Read docs/shadow/current/django_strawberry_framework__forms__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__forms__inputs.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed Medium. `build_form_inputs()` consumed one-shot `fields`/`exclude` iterables during the first effective-field resolution, then reused the exhausted iterator for the partial input, causing false empty errors or silently widening the second shape. The validated field-name tuple is now reused for both builds. Files changed: `django_strawberry_framework/forms/inputs.py`, `tests/forms/test_inputs.py` (preserving concurrent relation-ID changes).
    - Verification: Passed. Worker 0 independently ran the retained generator probe (both create and partial shapes honor the narrowing) and `tests/forms/test_inputs.py` (46 passed).
    - Validation: Worker 1 reported 46 focused tests and formatter/linter checks; Worker 0 reran the package suite and probe script successfully.
    - Cleanup: Removed `docs/bug_hunt/temp-tests/forms_inputs/`; unrelated concurrent work preserved.

- [x] django_strawberry_framework/forms/resolvers.py
    - Status: no-bugs
    - Cycle baseline: HEAD `054de9dd37a2c4181fb2a91ded57f4823a1b5220`; live target SHA-256 `3ef9d9fb2fa0c313229e391a597f3d41b0b64f3cdcda3058158e3c89cd48abbe`; working-tree status digest `8179ed4e928f0fd1eeb3a8ae3cda0bb10b20d4035426fe06f4a17731c8016866`. The target was clean at dispatch.
    - docs/shadow/current/django_strawberry_framework__forms__resolvers.stripped.py
    - docs/shadow/current/django_strawberry_framework__forms__resolvers.overview.md
    - Prompt:
        - Use django_strawberry_framework/forms/resolvers.py as the entry point. Read docs/shadow/current/django_strawberry_framework__forms__resolvers.stripped.py and docs/shadow/current/django_strawberry_framework__forms__resolvers.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: traced the shared sync/async form write pipeline, relation visibility decoding, partial reconstruction, form validation/error mapping, file split, transaction/write phase, and live upload path; no new defect was confirmed.
    - Verification: Passed. Worker 0 independently reran the optional-extra partial-update probe, `tests/forms/test_resolvers.py` (52 passed), and a live form-upload test.
    - Validation: Worker 1 reported 54 package tests, 2 live multipart form-upload tests, and the adversarial probe; no source or permanent-test changes were needed. Formatter/linter and diff checks passed.
    - Cleanup: Removed `docs/bug_hunt/temp-tests/forms_resolvers/`; unrelated concurrent work preserved.

- [x] django_strawberry_framework/forms/sets.py
    - Status: verified
    - Cycle baseline: HEAD `054de9dd37a2c4181fb2a91ded57f4823a1b5220`; live target SHA-256 `23b7110d854c6c5747497af0b101cb97a74859d8c5c0dcfe580df09a82c446da`; working-tree status digest `972c051cd2d7efbd543274a6c4aabe63b18564d3c59053c6e25d705984020338`. The target was clean at dispatch.
    - docs/shadow/current/django_strawberry_framework__forms__sets.stripped.py
    - docs/shadow/current/django_strawberry_framework__forms__sets.overview.md
    - Prompt:
        - Use django_strawberry_framework/forms/sets.py as the entry point. Read docs/shadow/current/django_strawberry_framework__forms__sets.stripped.py and docs/shadow/current/django_strawberry_framework__forms__sets.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed two Medium defects. `Meta.fields`/`Meta.exclude` one-shot iterators were consumed during class validation and appeared empty at phase-2.5 binding; declarations are now normalized and snapshotted as tuples. Hostile malformed configuration could also escape as raw exceptions: broken permission iterables now map to `ConfigurationError`, and invalid form-class diagnostics use safe representation rendering. Files changed: `django_strawberry_framework/forms/sets.py`, `django_strawberry_framework/mutations/sets.py`, `tests/forms/test_sets.py`.
    - Verification: Passed. Worker 0 independently reran the hostile Meta probe, the forms set/resolver suite (99 passed), and the shared mutation-set suite (66 passed); all malformed cases now fail with typed diagnostics and one-shot narrowing survives bind.
    - Validation: Worker 1 reported 99 focused tests and formatter/linter checks; Worker 0 independently confirmed the scratch behavior and connected suites.
    - Cleanup: Removed `docs/bug_hunt/temp-tests/forms_sets/`; unrelated concurrent work preserved.

- [x] django_strawberry_framework/keyset.py
    - Status: no-bugs
    - Cycle baseline: HEAD `054de9dd37a2c4181fb2a91ded57f4823a1b5220`; live target SHA-256 `64b126906979ade29a3b4773e4c338343f4d3c6ce90eb5b04f7ad29c4bf825c5`; working-tree status digest `b178001e827f599a5d11fbcbd1a5f1c2552a4a29fcbf681d188d5b95e3065f3a`. The target was clean at dispatch.
    - docs/shadow/current/django_strawberry_framework__keyset.stripped.py
    - docs/shadow/current/django_strawberry_framework__keyset.overview.md
    - Result: No production defect found. Hostile malformed/foreign/tampered cursor inputs uniformly returned the documented GraphQLError; valid cursors round-tripped. Reviewed cursor validation, AES-SIV fallback rotation, scalar serialization, mixed-direction ORM/raw-SQL seek parity, null/JSON/relation restrictions, root/nested/async/lateral paths, ordering fingerprints, and visibility-aware replay. Independent verification: scratch probe passed; `tests/test_keyset.py tests/test_connection.py` 127 passed; live `examples/fakeshop/test_query/test_keyset_api.py` 25 passed. Removed exact scratch directory after verification.
    - Prompt:
        - Use django_strawberry_framework/keyset.py as the entry point. Read docs/shadow/current/django_strawberry_framework__keyset.stripped.py and docs/shadow/current/django_strawberry_framework__keyset.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/list_field.py
    - Status: no-bugs
    - Cycle baseline: HEAD `054de9dd37a2c4181fb2a91ded57f4823a1b5220`; live target SHA-256 `7e6b91116029a5fb0f22c1192fa45a6a0c8bc4fb28f68e4c8014f7306815af43`; working-tree status digest `aa4e5efceeeac0a3c066206bc5854912854859e489afd8bcfd8132140c696d51`. The target was clean at dispatch.
    - docs/shadow/current/django_strawberry_framework__list_field.stripped.py
    - docs/shadow/current/django_strawberry_framework__list_field.overview.md
    - Result: No additional reachable defect found after the existing async-iterable/resource-bound fix. Audited validation, sync/async resolver dispatch, visibility sealing, lazy queryset limits, malformed awaitables, iterator closure, and live list-field queries. Independent verification: edge probes passed; `tests/test_list_field.py` 44 passed; live list-field selection 1 passed. The hostile metaclass diagnostic case was confirmed as an out-of-boundary raw exception under existing project precedent. Removed exact scratch directory after verification.
    - Prompt:
        - Use django_strawberry_framework/list_field.py as the entry point. Read docs/shadow/current/django_strawberry_framework__list_field.stripped.py and docs/shadow/current/django_strawberry_framework__list_field.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/management/commands/_imports.py
    - Status: no-bugs
    - Cycle baseline: HEAD `054de9dd37a2c4181fb2a91ded57f4823a1b5220`; live target SHA-256 `9ec5d519b05b7cb0dbef9eb7ac351a81cd8448eeb92cec984216cdf5c3dae4b0`; working-tree status digest `d107330f30f04b1df81f1a462a18529cda66d7ba1f3625226e3fe17a872c54bb`. The target was clean at dispatch.
    - docs/shadow/current/django_strawberry_framework__management__commands___imports.stripped.py
    - docs/shadow/current/django_strawberry_framework__management__commands___imports.overview.md
    - Result: No defect found. Audited Strawberry selector and Django dotted-path resolution, malformed/relative/empty paths, missing symbols, nested symbols, import-error translation, pass-through of non-import failures, and both command callers. Independent verification: adversarial probe passed; connected management-command suite passed 74 tests. Removed exact scratch directory after verification.
    - Prompt:
        - Use django_strawberry_framework/management/commands/_imports.py as the entry point. Read docs/shadow/current/django_strawberry_framework__management__commands___imports.stripped.py and docs/shadow/current/django_strawberry_framework__management__commands___imports.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/management/commands/export_schema.py
    - Status: verified
    - Cycle baseline: HEAD `054de9dd37a2c4181fb2a91ded57f4823a1b5220`; live target SHA-256 `4afd92fda4522b5098a2344d8cd3c65ab11cb8a026c310c834adddcd87a4e0b6`; working-tree status digest `d107330f30f04b1df81f1a462a18529cda66d7ba1f3625226e3fe17a872c54bb`. The target was clean at dispatch.
    - docs/shadow/current/django_strawberry_framework__management__commands__export_schema.stripped.py
    - docs/shadow/current/django_strawberry_framework__management__commands__export_schema.overview.md
    - Result: Fixed a Low-severity error-boundary defect: an embedded NUL in `--path` raised raw `ValueError("embedded null byte")`; the write branch now translates both `OSError` and `ValueError` to `CommandError`. Permanent live fakeshop regression added. Independent verification: hostile probe passed; connected management-command suite passed 75 tests. Removed exact scratch directory after verification.
    - Prompt:
        - Use django_strawberry_framework/management/commands/export_schema.py as the entry point. Read docs/shadow/current/django_strawberry_framework__management__commands__export_schema.stripped.py and docs/shadow/current/django_strawberry_framework__management__commands__export_schema.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/management/commands/inspect_django_type.py
    - Status: no-bugs
    - Cycle baseline: HEAD `054de9dd37a2c4181fb2a91ded57f4823a1b5220`; live target SHA-256 `5b4a00ed1231f07ca98363df9ebcddb6eb07477b9f657531aaefc42af2bf732a`; working-tree status digest `7bb8f676155aaeab989dfe96b47ff3a0b5e0d2dbc3f1759bbca5d659dcc288d6`. The target was clean at dispatch.
    - docs/shadow/current/django_strawberry_framework__management__commands__inspect_django_type.stripped.py
    - docs/shadow/current/django_strawberry_framework__management__commands__inspect_django_type.overview.md
    - Result: No confirmed defect. Audited schema/type selector dispatch, registry/finalization lifecycle, custom naming/scalar maps, relation/connection rows, Relay primary keys, consumer-authored fields, unresolved annotations, and malformed command inputs. Independent verification: helper probe passed; package and fakeshop command suite passed 40 tests. Removed exact scratch directory after verification.
    - Prompt:
        - Use django_strawberry_framework/management/commands/inspect_django_type.py as the entry point. Read docs/shadow/current/django_strawberry_framework__management__commands__inspect_django_type.stripped.py and docs/shadow/current/django_strawberry_framework__management__commands__inspect_django_type.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/middleware/debug_toolbar.py
    - Status: verified
    - Cycle baseline: HEAD `054de9dd37a2c4181fb2a91ded57f4823a1b5220`; live target SHA-256 `4ee8d8c2365d755224392a6e558fdfae83934f9b49fa6f9a1ea9bd6c486264af`; working-tree status digest `7bd3bb709f71fed45021336cb3b953d226a86986638d54f51c4d9f64adbafb09`. The target was clean at dispatch.
    - docs/shadow/current/django_strawberry_framework__middleware__debug_toolbar.stripped.py
    - docs/shadow/current/django_strawberry_framework__middleware__debug_toolbar.overview.md
    - Result: Fixed a Medium response-integrity defect: already encoded responses (e.g. gzip HTML) were appended with unencoded GraphiQL markup, corrupting the body. `_postprocess` now leaves any `Content-Encoding` response untouched; permanent package regression added. Independent verification: encoded-body scratch repro passed; package middleware suite 18 passed; live toolbar suite 8 passed. Removed exact scratch directory after verification.
    - Prompt:
        - Use django_strawberry_framework/middleware/debug_toolbar.py as the entry point. Read docs/shadow/current/django_strawberry_framework__middleware__debug_toolbar.stripped.py and docs/shadow/current/django_strawberry_framework__middleware__debug_toolbar.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/middleware/request_body.py
    - Status: verified
    - Cycle baseline: HEAD `054de9dd37a2c4181fb2a91ded57f4823a1b5220`; live target SHA-256 `af0ee4de619c74214b6cb14791d771b3a3019e2babe5b94e99838d62630d6fa2`; working-tree status digest `5269314036fcc6b7fdc1ebc804d745adb737f989bdc546c6b6df3f77335fdd02`. The target was clean at dispatch.
    - docs/shadow/current/django_strawberry_framework__middleware__request_body.stripped.py
    - docs/shadow/current/django_strawberry_framework__middleware__request_body.overview.md
    - Result: Fixed a Medium lifecycle defect: duplicate boundary middleware entries re-ran setup/body-boundary side effects and overwrote the prepared view instance for one request. `process_view()` now returns when `_BOUNDARY_ENFORCED` is already present; permanent regression added. Independent verification: duplicate-entry probe changed from two runs to one; selected view/middleware tests 31 passed; live transport suite 77 passed. Removed exact scratch directory after verification.
    - Prompt:
        - Use django_strawberry_framework/middleware/request_body.py as the entry point. Read docs/shadow/current/django_strawberry_framework__middleware__request_body.stripped.py and docs/shadow/current/django_strawberry_framework__middleware__request_body.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/mutations/fields.py
    - Status: verified
    - Cycle baseline: HEAD `054de9dd37a2c4181fb2a91ded57f4823a1b5220`; live target SHA-256 `54d6810f86c0b2a836293cfaadc742a16bff14f8cde9f0ad5a75c48b2a625048`; working-tree status digest `5269314036fcc6b7fdc1ebc804d745adb737f989bdc546c6b6df3f77335fdd02`. The target was clean at dispatch.
    - docs/shadow/current/django_strawberry_framework__mutations__fields.stripped.py
    - docs/shadow/current/django_strawberry_framework__mutations__fields.overview.md
    - Result: Fixed a Medium configuration-boundary defect: invalid `DjangoMutationField()` targets with hostile `__repr__` escaped as raw `RuntimeError`; rejected-target diagnostics now use `_safe_arg_repr` and preserve `ConfigurationError`. Permanent package regression added. Independent verification: hostile and registry-lifecycle probes passed; package field tests 13 passed; live create/update/delete selection 2 passed. Removed exact scratch directory after verification.
    - Prompt:
        - Use django_strawberry_framework/mutations/fields.py as the entry point. Read docs/shadow/current/django_strawberry_framework__mutations__fields.stripped.py and docs/shadow/current/django_strawberry_framework__mutations__fields.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/mutations/inputs.py
    - Status: verified
    - Cycle baseline: HEAD `054de9dd37a2c4181fb2a91ded57f4823a1b5220`; live target SHA-256 `a79eb45b2603a24e235cfc4a5dab9327cf4344975cc03a84eca3b20caacf61c0`; working-tree status digest `a31897e63d8cd26d6704098f7dde461160fe4c6106321003814015d780c082a3`. The target was clean at dispatch.
    - docs/shadow/current/django_strawberry_framework__mutations__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__mutations__inputs.overview.md
    - Result: Fixed two Medium one-shot-iterator defects. `editable_input_fields()` now snapshots `fields`/`exclude` before validation and narrowing; `build_mutation_input()` snapshots `overrides` before repeated membership checks. Permanent package regressions added. Independent verification: mutation-input package suite 50 passed; live product mutation and custom-input selection 4 passed. Worker scratch was removed after its probe verification.
    - Prompt:
        - Use django_strawberry_framework/mutations/inputs.py as the entry point. Read docs/shadow/current/django_strawberry_framework__mutations__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__mutations__inputs.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/mutations/permissions.py
    - Status: verified
    - Cycle baseline: HEAD `054de9dd37a2c4181fb2a91ded57f4823a1b5220`; live target SHA-256 `dc96f83e91619a955297cbcfa1c256724a69db42f42b60f497f5836f79d4785c`; working-tree status digest `5248509ff1c344e8540d953cb69a7076638dfd5fd119d3d40190e0684aec91e4`. The target was clean at dispatch.
    - docs/shadow/current/django_strawberry_framework__mutations__permissions.stripped.py
    - docs/shadow/current/django_strawberry_framework__mutations__permissions.overview.md
    - Result: Fixed a Medium authorization error-boundary defect: non-bool permission results with hostile `__repr__` escaped as raw exceptions; `_require_sync_bool_auth_result()` now uses `_safe_arg_repr` and preserves `ConfigurationError`. Permanent package regression added. Independent verification: hostile/invalid-operation probes 3 passed; package permission suite 20 passed; live permission-focused product suite 11 passed. Removed exact scratch directory after verification.
    - Prompt:
        - Use django_strawberry_framework/mutations/permissions.py as the entry point. Read docs/shadow/current/django_strawberry_framework__mutations__permissions.stripped.py and docs/shadow/current/django_strawberry_framework__mutations__permissions.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/mutations/resolvers.py
    - Status: verified
    - Cycle baseline: HEAD `054de9dd37a2c4181fb2a91ded57f4823a1b5220`; live target SHA-256 `12a7af8a798738989b2a0b8a83b4451424af97293a8c7ed3e511d264e3be8f8d`; working-tree status digest `df823202586d41eef59bf463380905851957fa1eab35beb9c1162c882ca6aa26`. The target was clean at dispatch.
    - docs/shadow/current/django_strawberry_framework__mutations__resolvers.stripped.py
    - docs/shadow/current/django_strawberry_framework__mutations__resolvers.overview.md
    - Result: Fixed a Medium drift-diagnostic defect: hostile primary-key representations from authorization/write hooks could escape as raw exceptions in update/delete diagnostics. Both paths now use `_safe_arg_repr`; permanent regressions added. Independent verification: hostile PK probe passed; resolver suite 69 passed; live create/update/delete product suite 49 passed. Removed exact scratch directory after verification.
    - Prompt:
        - Use django_strawberry_framework/mutations/resolvers.py as the entry point. Read docs/shadow/current/django_strawberry_framework__mutations__resolvers.stripped.py and docs/shadow/current/django_strawberry_framework__mutations__resolvers.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/mutations/sets.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__mutations__sets.stripped.py
    - docs/shadow/current/django_strawberry_framework__mutations__sets.overview.md
    - Prompt:
        - Use django_strawberry_framework/mutations/sets.py as the entry point. Read docs/shadow/current/django_strawberry_framework__mutations__sets.stripped.py and docs/shadow/current/django_strawberry_framework__mutations__sets.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No confirmed production defect. Meta validation, declaration registration/finalization, input overrides, relation-shape checks, payload binding, and materialization/cache seams remained coherent under malformed configuration probes.
    - Verification: Passed. Worker 1 ran the dedicated mutation-set suite (76 passed) and lint; Worker 0 independently ran mutation package coverage (209 passed) and live create/update/delete coverage (57 passed). Ruff format/check and diff check passed.
    - Cleanup: No item scratch remained; unrelated concurrent changes retained.

- [x] django_strawberry_framework/optimizer/_context.py
    - Status: no-bugs
    - Cycle baseline: HEAD `054de9dd37a2c4181fb2a91ded57f4823a1b5220`; live target SHA-256 `3185fe5aa0003baffcabd7bbe7bdcdc440344f9f968abe9f7abf273e23f05157`; working-tree status digest `8938e7cd26ca0b2004dc190840a9961d6246ee4bd41187aea4672734caf4b849`. The target was clean at dispatch.
    - docs/shadow/current/django_strawberry_framework__optimizer___context.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer___context.overview.md
    - Result: No additional defect found. Audited optimizer context key vocabulary, object/dict/slots-mapping dispatch, immutable mapping behavior, `None`, start-of-execution reset, and nested publish lifecycle. Independent verification: shape/lifecycle probe passed; package context-selection 29 passed; live optimizer query selection passed. Removed exact scratch directory after verification.
    - Prompt:
        - Use django_strawberry_framework/optimizer/_context.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer___context.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer___context.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/optimizer/extension.py
    - Status: verified
    - Cycle baseline: HEAD `054de9dd37a2c4181fb2a91ded57f4823a1b5220`; live target SHA-256 `64be2bb6b11ac2dc8de505c707142e2175eaf2d0091e46f7213002914521ebee`; working-tree status digest `2d57d3c8f75caf5bd506b28d9e967dd81c837e57f92f4a316ed05882884f9fc3`. The target was clean at dispatch.
    - docs/shadow/current/django_strawberry_framework__optimizer__extension.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__extension.overview.md
    - Result: Fixed a Medium cache-key robustness defect: hostile `__hash__`, mapping/iteration, metaclass checks, and `repr` behavior could escape while freezing custom GraphQL variable values. The freezer now uses safe type identities, opaque fallbacks, and unordered structural forms without hostile `repr` sorting. Permanent optimizer regression added. Independent verification: hostile cache probe passed; targeted optimizer cache/context selection 27 passed; live optimizer query passed. Removed exact scratch directory after verification.
    - Prompt:
        - Use django_strawberry_framework/optimizer/extension.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__extension.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__extension.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/optimizer/field_meta.py
    - Status: verified
    - Cycle baseline: HEAD `054de9dd37a2c4181fb2a91ded57f4823a1b5220`; live target SHA-256 `6fbd912db51ed636fdc06a37286b24202d9ce79484e9ef14ae16fd8d449ebc4e`; working-tree status digest `9f7cfb1d6d3f5f99116f507d2eee15a4aa22a810efd91fb7ff4379c2c4c8972f`. The target was clean at dispatch.
    - docs/shadow/current/django_strawberry_framework__optimizer__field_meta.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__field_meta.overview.md
    - Result: Fixed a malformed-descriptor boundary defect: hostile required attributes or representations now become the documented `OptimizerError` with a safe type label instead of leaking raw exceptions. Added permanent regression coverage. Worker scratch plus independent hostile probe passed; focused field-meta and generic-foreign-key coverage passed (30 tests total). The exact disposable scratch directory was removed after verification.

- [x] django_strawberry_framework/optimizer/hints.py
    - Status: verified
    - docs/shadow/current/django_strawberry_framework__optimizer__hints.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__hints.overview.md
    - Result: Fixed two defensive-contract defects: hostile metaclass `__name__` access during invalid `Prefetch` validation and hostile `.skip`/`__bool__` behavior during skip dispatch now remain within the documented `ConfigurationError` and fail-safe predicate contracts. Added permanent hint regressions. Independent hostile probe, hint tests, connected walker/extension hint tests (45 total), and the live fakeshop optimizer-hint query passed. Removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/optimizer/join_taxonomy.py
    - Status: verified
    - docs/shadow/current/django_strawberry_framework__optimizer__join_taxonomy.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__join_taxonomy.overview.md
    - Result: Fixed the classifier's documented fail-closed contract: malformed relation metadata, broken GenericRelation/through lookups, and hostile relation attributes now degrade to unresolved or unsupported join facts instead of leaking raw exceptions. Added permanent taxonomy regressions. Independent malformed-metadata probe passed; package connector/taxonomy/advisory coverage passed (81 selected with 35 expected skips), and live optimizer/relation coverage passed (42). Removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/optimizer/lateral_fetch.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__optimizer__lateral_fetch.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__lateral_fetch.overview.md
    - Result: No additional defect found. The lateral recognizer, SQL builder, fallback paths, single-parent seam, join taxonomy, keyset handling, and fakeshop strategy callers were traced. Independent helper probe passed; lateral plus single-parent package suites passed (126), live optimizer strategy coverage passed (1), and the PostgreSQL parity selection remained cleanly skipped without a service (35 skips). Removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/optimizer/nested_fetch.py
    - Status: verified
    - docs/shadow/current/django_strawberry_framework__optimizer__nested_fetch.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__nested_fetch.overview.md
    - Result: Fixed a Medium strategy-lifecycle bug: a valid consumer strategy whose `__bool__` returned false was silently replaced by the default windowed strategy. `active_strategy()` now distinguishes a falsey strategy from the empty `None` context. Added permanent regression coverage. Independent lifecycle probe and connected strategy/unwindowable tests passed (29 selected), plus the live optimizer strategy check; removed the exact disposable scratch directory.

- [x] django_strawberry_framework/optimizer/nested_planner.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__optimizer__nested_planner.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__nested_planner.overview.md
    - Result: No additional defect found. Fallback classification, pagination/keyset normalization, strategy dispatch, index advisory tri-state, relation joins, and resolver/to-attr bookkeeping were traced. Independent pagination probe passed; planner/strategy/walker and nested-index selection passed (111), connected connection/plans/taxonomy coverage passed (192). Removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/optimizer/plans.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__optimizer__plans.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__plans.overview.md
    - Result: No additional defect found. Plan construction/finalization/merge/apply lifecycle, indexed deduplication, projection pruning, strictness/FK-elision coupling, deterministic and reverse ordering, pagination markers/probes/counts, keyset windows, relation partitioning, and lookup-path flattening were traced. Independent scratch and plan tests passed (113), live library window/keyset coverage passed (2). Removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/optimizer/predicates.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__optimizer__predicates.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__predicates.overview.md
    - Result: No confirmed defect found. Correlated inner-root construction, DB routing, reserved alias collision/repetition, model/database guards, combined-query rejection, row-preserving `EXISTS` semantics, and filter/walker callers were traced. Independent scratch and package/filter coverage passed (297); live related/flat-leaf row-semantics coverage passed (31). Removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/optimizer/selections.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__optimizer__selections.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__selections.overview.md
    - Result: No confirmed defect found. AST conversion (including anonymous inline fragments), per-execution memo lifecycle, directive and fragment traversal/cycle guards, response-key/runtime-prefix propagation, Relay edge/node extraction, and totalCount/hasNextPage observability were traced through walker, connection, relay, and live callers. The worker scratch was already absent; independent package/walker coverage passed (199) and live anonymous-fragment coverage passed (5).

- [x] django_strawberry_framework/optimizer/single_parent_fetch.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__optimizer__single_parent_fetch.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__single_parent_fetch.overview.md
    - Result: No confirmed correctness defect found. Plan-time eligibility, runtime shape recognition, projection/select-related guards, single-parent deduplication, fallback to the windowed body, and live alias/router behavior were traced. Independent scratch (after avoiding an already-used persistent probe name) passed; package plus live fakeshop coverage passed (48). Removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/optimizer/walker.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__optimizer__walker.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__walker.overview.md
    - Result: No confirmed correctness defect found. Relation routing, prefetch/select planning, strictness/FK-elision metadata coupling, fallback shapes, runtime-prefix/alias merging, and downstream connection behavior were traced. Independent walker suite passed (179), live optimizer/products/library selections passed (115), and the worker smoke probe passed. Removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/orders/base.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__orders__base.stripped.py
    - docs/shadow/current/django_strawberry_framework__orders__base.overview.md
    - Result: No confirmed defect found. Lazy target resolution, owner binding/rebinding idempotence, target setter behavior, and connected OrderSet consumers were traced. Independent scratch and related order suites passed (55). Removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/orders/factories.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__orders__factories.stripped.py
    - docs/shadow/current/django_strawberry_framework__orders__factories.overview.md
    - Result: No confirmed defect found. BFS input construction, source/name collision handling, idempotent cache behavior, metadata normalization, and dynamic OrderSet generation were traced. Independent scratch and factory/input/finalizer coverage passed (106). Removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/orders/inputs.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__orders__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__orders__inputs.overview.md
    - Result: No confirmed defect found. Direction resolution, generated input annotations, provenance tracking, recursive normalization, materialization, namespace lifecycle, connected OrderSet composition, and live library ordering were traced. Independent scratch and order input/set/composition coverage passed (85 selected; worker connected total 282), plus 20 live ordering tests. Removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/orders/sets.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__orders__sets.stripped.py
    - docs/shadow/current/django_strawberry_framework__orders__sets.overview.md
    - Result: No confirmed defect found. Declaration expansion/binding, active permission gates, to-many Min/Max aggregate ordering, null directions, and sync/async application were traced. Independent scratch and order/permission coverage passed (105 selected, 1 expected skip); live ordering coverage passed (20). Removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/permissions.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__permissions.stripped.py
    - docs/shadow/current/django_strawberry_framework__permissions.overview.md
    - Result: No additional defect found. Queryset sealing and root/edge validation, ContextVar traversal isolation, cycle/GFK/MTI handling, alias routing, async boundary, registered-target composition, and filter/order/mutation visibility callers were traced. Independent scratch and main permissions suite passed (63, 1 expected skip); live cascade/permission coverage passed (10 selected). Removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/registry.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__registry.stripped.py
    - docs/shadow/current/django_strawberry_framework__registry.overview.md
    - Result: No confirmed defect found. Registration/primary semantics, definitions, pending relations, teardown and subsystem clear callbacks, enum caching, finalization/retry behavior, GlobalID lookup, and cross-subsystem lifecycle were traced. Independent registry probe and suite passed (80); removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/relay.py
    - Status: verified
    - docs/shadow/current/django_strawberry_framework__relay.stripped.py
    - docs/shadow/current/django_strawberry_framework__relay.overview.md
    - Result: Fixed a Medium sync/async boundary defect: consumer `async def resolve_node(s)` overrides reached synchronous Relay fields as raw awaitables, leaking a coroutine/TypeError and warning. Both root fields now use the shared typed sync-misuse rejection (which closes the coroutine) while preserving async execution. Permanent single/batch regressions were added. Independent scratch confirmed `SyncMisuseError` with no warning; Relay package coverage passed (46), connected Relay/connection coverage passed (133 selected), and live Relay/node coverage passed (18). Removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/resource_policy.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__resource_policy.stripped.py
    - docs/shadow/current/django_strawberry_framework__resource_policy.overview.md
    - Result: No confirmed defect found. Immutable policy normalization, request-context stashing/cleanup, narrowing, deadline checks, hostile values/uploads, sync/async collection bounds, and connected schema, extension, Relay, mutation, form, and transport seams were traced. Independent scratch plus package and live policy coverage passed (125 tests). Removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/rest_framework/hook_context.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__rest_framework__hook_context.stripped.py
    - docs/shadow/current/django_strawberry_framework__rest_framework__hook_context.overview.md
    - Result: No confirmed defect found. Frozen hook-context dataclasses, serializer resolver construction, consumer hooks, upload metadata, DRF set/schema lifecycle, lazy exports, sync/async execution, and hostile mutation attempts were traced. Independent scratch and resolver/set/soft-dependency coverage passed (225 tests); the separate input-suite failure was pre-existing concurrent work outside this item. Removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/rest_framework/inputs.py
    - Status: verified
    - docs/shadow/current/django_strawberry_framework__rest_framework__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__rest_framework__inputs.overview.md
    - Result: Fixed a Medium one-shot selector exhaustion defect. Serializer `fields` / `exclude` iterators and nested selector iterators were consumed during create-shape construction or class validation, leaving partial builds or phase-2.5 bind with false empty selections. The root fix normalizes top-level and nested selectors once, stores immutable snapshots through `SerializerMutation`, and reuses them for every shape. Permanent input/set regressions were added. Independent scratch passed; input/set/resolver coverage passed (286), and live serializer GraphQL coverage passed (27). Removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/rest_framework/resolvers.py
    - Status: verified
    - docs/shadow/current/django_strawberry_framework__rest_framework__resolvers.stripped.py
    - docs/shadow/current/django_strawberry_framework__rest_framework__resolvers.overview.md
    - Result: Fixed a Low malformed-extension-point defect: serializer mapping hooks returning `None`, sequences, or unmaterializable mappings leaked raw `TypeError` from `dict(...)` into GraphQL. A shared `_hook_mapping` boundary now raises typed `ConfigurationError` for all three hooks, with permanent regressions. Independent scratch passed; resolver package coverage passed (139), and live serializer coverage passed (27). Removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/rest_framework/serializer_converter.py
    - Status: verified
    - docs/shadow/current/django_strawberry_framework__rest_framework__serializer_converter.stripped.py
    - docs/shadow/current/django_strawberry_framework__rest_framework__serializer_converter.overview.md
    - Result: Fixed three related Medium converter-boundary defects. Model-backed relations now reject serializer/model cardinality mismatches at schema time; malformed public converter registrations are typed and cannot leak raw errors or smuggle relation/file kinds through the scalar registry; hostile `help_text`/constraint metadata now raises `ConfigurationError` instead of escaping during schema construction. Permanent regressions were added. Independent scratch passed; connected converter/input/set coverage passed (231), and live serializer coverage passed (27). Removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/rest_framework/sets.py
    - Status: verified
    - docs/shadow/current/django_strawberry_framework__rest_framework__sets.stripped.py
    - docs/shadow/current/django_strawberry_framework__rest_framework__sets.overview.md
    - Result: Fixed a Medium schema-hook boundary defect: malformed `get_serializer_for_schema()` results leaked raw `AttributeError`/`TypeError` or silently accepted non-string/mismatched field-map keys. Typed validation now materializes the map, checks DRF field values, string keys, bound-name consistency, hostile mappings, and safe diagnostics. Permanent regressions were added. Independent scratch passed; sets/input coverage passed (157), and live serializer coverage passed (27). Removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/routers.py
    - Status: verified
    - docs/shadow/current/django_strawberry_framework__routers.stripped.py
    - docs/shadow/current/django_strawberry_framework__routers.overview.md
    - Result: Fixed two Medium and one Low router defects. Lazy router-class construction is now serialized so concurrent first access yields one class identity; websocket URL patterns are validated as strings and compiled eagerly with typed hostile-input errors; callable consumer factories whose `__signature__` descriptor fails now fall through to the actual call. Independent hostile/concurrency scratch passed and the router suite passed (163). Removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/scalars.py
    - Status: verified
    - docs/shadow/current/django_strawberry_framework__scalars.stripped.py
    - docs/shadow/current/django_strawberry_framework__scalars.overview.md
    - Result: Fixed Medium scalar-boundary defects. BigInt parsing/serialization now bypasses hostile `int`/`str` subclass dunders and uses safe diagnostics; `strawberry_config(extra_scalar_map=...)` materializes hostile mappings safely and renders collision keys without trusting consumer metadata. Permanent regressions were added. Independent hostile/large-value scratch passed; scalar/converter/live upload/resource-policy coverage passed (52 scalar tests; 244 connected tests). Removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/schema.py
    - Status: verified
    - docs/shadow/current/django_strawberry_framework__schema.stripped.py
    - docs/shadow/current/django_strawberry_framework__schema.overview.md
    - Result: Fixed a Medium extension-boundary defect: `_with_resource_policy_extension()` used truthiness (`extensions or []`), invoking hostile/stateful `__bool__` implementations and allowing extension entries to be suppressed or raw exceptions to escape. It now treats only `None` as omitted and materializes other iterables directly. Independent hostile/lifecycle scratch passed; policy/error suites passed (140), mutation transaction/field and live atomicity coverage passed (71). Removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/sets_mixins.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__sets_mixins.stripped.py
    - docs/shadow/current/django_strawberry_framework__sets_mixins.overview.md
    - Result: No confirmed defect found. Naming guards, lazy relation target resolution, owner binding, MRO/tombstone/diamond declaration collection, expansion caching/reentry, lifecycle resets, active permission traversal, finalization, and real filter/order paths were traced. Independent scratch and shared set/permission coverage passed (388 tests, 1 expected skip); live kanban/keyset coverage passed (85). Removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/testing/_wrap.py
    - Status: verified
    - Baseline shadow: none. The file existed at the hunt baseline; the snapshot helper
      (`scripts/review_historical_package_snapshot_at_commit.py`) filters out every path containing
      `test`, so the whole `testing/` subpackage is excluded from `docs/shadow/current/`. This item
      originally carried the generator's stock "live file added or absent at hunt baseline" reason,
      which was false; the generator now distinguishes the two causes and reports the right one.
    - Result: Fixed a Low error-contract defect: a non-callable wrapper with hostile `__repr__` escaped the documented `TypeError` boundary. The helper now emits a stable TypeError without interpolating user-controlled repr. Independent scratch passed and the complete testing suite passed (45). Removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/testing/client.py
    - Status: verified
    - Baseline shadow: none, for the same `testing/` snapshot exclusion recorded above; the file
      existed at the hunt baseline.
    - Result: Fixed two testing-client edge defects: explicitly supplied falsy clients were replaced by defaults (`is not None` now selects them), and hostile multipart placeholder/path values could escape the documented `AssertionError` through raw repr. All multipart diagnostics now use safe representations. Independent scratch passed; package client/wrap/relay coverage passed (48), and live client acceptance passed (11 selected). Removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/testing/relay.py
    - Status: verified
    - Baseline shadow: none, for the same `testing/` snapshot exclusion recorded above; the file
      existed at the hunt baseline.
    - Result: Fixed a Low diagnostics defect: `global_id_for()` interpolated an unregistered input with raw repr, allowing hostile `__repr__` to escape its promised `ConfigurationError`. It now uses safe argument rendering. Independent malformed-ID scratch passed; Relay/DRF coverage passed (150), and live GlobalID/node coverage passed (20). Removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/types/base.py
    - Status: verified
    - docs/shadow/current/django_strawberry_framework__types__base.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__base.overview.md
    - Result: Fixed Medium Meta-validation defects. Hostile values/descriptors now produce typed safe errors across filter/order/connection/cursor/relation/global-ID/interface validation; mixed or hostile connection keys are normalized safely; broken cursor sequences are typed; field-name collections reject non-strings early; and `Meta.connection` is snapshotted defensively instead of retaining caller mutation. Permanent hostile/malformed/snapshot regressions were added. Independent scratch passed; base coverage passed (153), related type/Relay coverage passed (313), and live library/transport GraphQL coverage passed (274). Removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/types/converters.py
    - Status: verified
    - docs/shadow/current/django_strawberry_framework__types__converters.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__converters.overview.md
    - Result: Fixed Medium malformed/hostile conversion defects. Choice entries are validated and snapshotted before enum generation; malformed pairs and hostile choice string/repr/boolean behavior now yield typed `ConfigurationError`; unsupported fields and array/HStore/nullable metadata use safe labels; and registry/name generation cannot trust hostile field metadata. Permanent converter regressions were added. Independent scratch passed; type/DRF converter coverage passed (153), and live scalar/upload coverage passed (38). Removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/types/definition.py
    - Status: verified
    - docs/shadow/current/django_strawberry_framework__types__definition.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__definition.overview.md
    - Result: Fixed Medium type-definition boundary defects. Invalid/hostile `Meta.name` values are validated and normalized as typed configuration errors; direct `graphql_type_name` validates safely; malformed related names fail closed; and custom-ID checks tolerate malformed PK names and hostile resolver descriptors without raw exceptions. Permanent definition/base regressions were added. Independent scratch passed; definition/base coverage passed (172), registry/finalizer/connection coverage passed (309), and live library GraphQL coverage passed (197). Removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/types/finalizer.py
    - Status: verified
    - docs/shadow/current/django_strawberry_framework__types__finalizer.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__finalizer.overview.md
    - Result: Fixed Medium finalizer diagnostics/lifecycle defects. Hostile model/class metadata, malformed annotation keys/maps, pending relation names, incomplete registry entries, and sidecar expansion failures now fail through typed safe diagnostics; relation/owner/connection labels no longer trust consumer metadata. Permanent finalizer regressions were added. Independent scratch passed; finalizer/registry/filter/order coverage passed (137), and live library coverage passed (197). Removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/types/relations.py
    - Status: verified
    - docs/shadow/current/django_strawberry_framework__types__relations.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__relations.overview.md
    - Result: Fixed a Medium equality/hash contract defect: `PendingRelation` had value equality but identity hashing, so equal records could coexist in sets and violate Python’s hash invariant. A guarded value-consistent hash now tolerates unhashable Django relation descriptors. Independent scratch passed; relation/registry/definition-order coverage passed (130), and the full types suite passed (477). Removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/types/relay.py
    - Status: verified
    - docs/shadow/current/django_strawberry_framework__types__relay.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__relay.overview.md
    - Result: Fixed five Medium Relay robustness defects. Hostile class/model names and metaclasses now produce safe typed errors; callable GlobalID encoders normalize hostile `str` subclasses; malformed GlobalID inputs/slots fail through `ConfigurationError`; and hostile node-hint descriptors fall back to ordinary `isinstance` dispatch. Permanent Relay regressions were added. Independent scratch passed; interface/node/testing coverage passed (196), and live GlobalID/node coverage passed (11). Removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/types/resolvers.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__types__resolvers.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__resolvers.overview.md
    - Result: No confirmed defect found. Relation/file resolver generation, FK-ID elision, deferred-column safety, strict N+1 behavior, prefetch/accessor handling, resource/deadline bounds, visibility ownership, sync/async boundaries, custom overrides, finalization/rebuild lifecycle, malformed metadata, and hostile model descriptors were traced. Independent scratch passed; resolver/connection/resource coverage passed (285). Removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/utils/connections.py
    - Status: verified
    - docs/shadow/current/django_strawberry_framework__utils__connections.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__connections.overview.md
    - Result: Fixed a Medium resource-policy bypass: nested connection SQL windows used schema `max_page_size` before request-policy narrowing, so a policy cap of 5 could fetch 101 rows per parent. `derive_connection_window_bounds()` now resolves the effective relay cap before `SliceMetadata` builds the window. Independent scratch passed; connection/keyset/utils coverage passed (136), and live window/connection/pagination coverage passed (47). Removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/utils/context.py
    - Status: verified
    - docs/shadow/current/django_strawberry_framework__utils__context.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__context.overview.md
    - Result: Fixed a Medium fail-closed context defect: hostile object descriptors or mapping `.get()` methods could abort resource/optimizer setup instead of yielding the caller’s default. Ordinary access failures are now swallowed as unavailable keys while `BaseException` cancellation/process-control signals still propagate; writes retain their narrow contract. Permanent context regressions were added. Independent scratch passed; context/resource/optimizer coverage passed (250). Removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/utils/converters.py
    - Status: verified
    - docs/shadow/current/django_strawberry_framework__utils__converters.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__converters.overview.md
    - Result: Fixed two Medium hostile-metaclass conversion defects. MRO lookup now bypasses consumer metaclass `__getattribute__` hooks, and registry matching scans keys by identity so hostile class hashing/equality cannot abort dispatch. Unsupported form/serializer fields retain typed `ConfigurationError` paths. Independent scratch passed; shared/forms/DRF converter coverage passed (123), and live library form/serializer coverage passed (38) plus product coverage (41). Removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/utils/errors.py
    - Status: verified
    - docs/shadow/current/django_strawberry_framework__utils__errors.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__errors.overview.md
    - Result: Fixed Medium error-normalization defects. Hostile string subclasses and malformed Django `ValidationError` metadata could leak raw exceptions; paths/messages/codes, hostile iterables, malformed error-dict entries, and relation/path joining now normalize safely while preserving standard shapes. Permanent error regressions were added. Independent scratch passed; shared mutation/form/DRF/error coverage passed (265), and live error-policy coverage passed (18). Removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/utils/imports.py
    - Status: verified
    - docs/shadow/current/django_strawberry_framework__utils__imports.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__imports.overview.md
    - Result: Fixed a Medium optional-import boundary defect: hostile `str` subclasses could break `sys.modules` hashing or install-hint rendering. All import helpers now normalize string subclasses before import, lookup, attribute access, and wrapped `ImportError` construction. Permanent regressions were added. Independent scratch passed; connected registry/converter/optimizer/DRF/debug-toolbar coverage passed (295). Removed the exact disposable scratch directory after verification.

- [x] django_strawberry_framework/utils/input_values.py
    - Status: verified
    - docs/shadow/current/django_strawberry_framework__utils__input_values.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__input_values.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/input_values.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__input_values.stripped.py and docs/shadow/current/django_strawberry_framework__utils__input_values.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed Medium traversal defects. Hostile mapping/dataclass/list protocols, malformed field names, and nested order lists could escape raw exceptions, bypass validation, or recurse indefinitely; traversal now uses safe built-ins, validates shapes and keys, and fails closed with typed `ConfigurationError`. A stale `_walk_error` call-site signature that turned hostile field-spec lookups into `TypeError` was also corrected. Files changed: `django_strawberry_framework/utils/input_values.py`, `tests/utils/test_input_values.py`.
    - Verification: Passed. Worker 0 independently reproduced the hostile field-spec failure before correction, then ran the retained hostile probe and utility/filter/order/permission/live product selection; 518 passed, 1 skipped. Ruff format/check and diff check passed.
    - Cleanup: Removed `docs/bug_hunt/temp-tests/utils_input_values/`; unrelated concurrent changes retained.

- [x] django_strawberry_framework/utils/inputs.py
    - Status: verified
    - docs/shadow/current/django_strawberry_framework__utils__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__inputs.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/inputs.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__utils__inputs.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed Medium generated-input robustness defects. Hostile metadata containers/repr hooks escaped cache-key canonicalization; hostile field-name iterators escaped normalization; malformed generated field triples escaped raw `TypeError`. Shared helpers now use built-in container traversal, safe sort keys/identity fallbacks, typed sequence errors, and validated field triples/kwargs. Files changed: `django_strawberry_framework/utils/inputs.py`, `tests/utils/test_inputs.py`.
    - Verification: Passed. Worker 0 reproduced all five original hostile failures, then reran the retained scratch, package/factory/input selection (309 passed), and live fakeshop mutation/filter/product selection (151 passed). Ruff format/check and diff check passed.
    - Cleanup: Removed `docs/bug_hunt/temp-tests/utils_inputs/`; unrelated concurrent changes retained.

- [x] django_strawberry_framework/utils/permissions.py
    - Status: verified
    - docs/shadow/current/django_strawberry_framework__utils__permissions.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__permissions.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/permissions.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__permissions.stripped.py and docs/shadow/current/django_strawberry_framework__utils__permissions.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed Medium request-context robustness defects. Hostile Channels scope descriptors/mappings and `info.context` descriptors leaked raw exceptions, while arbitrary mapping request values could bypass request validation. Scope probing is now fail-closed and typed; mapping contexts require `HttpRequest` or a valid Channels shape; established request-like attribute wrappers remain supported for mutation permissions. Files changed: `django_strawberry_framework/utils/permissions.py`, `tests/utils/test_permissions.py`.
    - Verification: Passed. Worker 0 reproduced each hostile path, caught and corrected a nine-test compatibility regression during verification, then reran scratch plus connected permissions/filter/order/mutation tests (385 passed) and live auth/product requests (138 passed). Ruff format/check and diff check passed.
    - Cleanup: Removed `docs/bug_hunt/temp-tests/utils_permissions/`; unrelated concurrent changes retained.

- [x] django_strawberry_framework/utils/querysets.py
    - Status: verified
    - docs/shadow/current/django_strawberry_framework__utils__querysets.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__querysets.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/querysets.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__querysets.stripped.py and docs/shadow/current/django_strawberry_framework__utils__querysets.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed Medium typed-boundary defects. Hostile manager routing/`.all()` behavior and hostile Query/model metadata escaped raw exceptions during normalization and visibility sealing; manager coercion and model/table diagnostics now fail closed with typed `ConfigurationError` and safe labels. Files changed: `django_strawberry_framework/utils/querysets.py`, `tests/utils/test_querysets.py`.
    - Verification: Passed. Worker 0 independently ran the retained hostile probe, package queryset/list/Relay coverage (431 passed), and live library/product transport coverage (315 passed). Ruff format/check and diff check passed.
    - Cleanup: Removed `docs/bug_hunt/temp-tests/utils_querysets/`; unrelated concurrent changes retained.

- [x] django_strawberry_framework/utils/relations.py
    - Status: verified
    - docs/shadow/current/django_strawberry_framework__utils__relations.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__relations.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/relations.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__relations.stripped.py and docs/shadow/current/django_strawberry_framework__utils__relations.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed Medium relation-boundary defects. Hostile flags, path splitting/path metadata, lookup/transform methods, accessors, composite metadata, and unhashable cache keys now fail closed with typed errors and safe diagnostics. Real Django `None` relation flags retain their original false semantics. Files changed: `django_strawberry_framework/utils/relations.py`, `tests/utils/test_relations.py`.
    - Verification: Passed. Worker 0 reproduced the hostile scratch failures, corrected a 62-test compatibility regression during verification, then reran the scratch, package relation/filter/order selection (550 passed), and live library/product selection (315 passed). Ruff format/check and diff check passed.
    - Cleanup: Removed `docs/bug_hunt/temp-tests/utils_relations/`; unrelated concurrent changes retained.

- [x] django_strawberry_framework/utils/sessions.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__utils__sessions.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__sessions.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/sessions.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__sessions.stripped.py and docs/shadow/current/django_strawberry_framework__utils__sessions.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No production defects. Session middleware guards, request/Channels classification, signed-cookie and server-side capability handling, scope-owned isolation, lock cancellation/serialization, and login/logout compensation remained correct; the only confirmed issue was the already-corrected glossary contract.
    - Verification: Passed. Worker 0 replayed hostile session/lock probes and ran session/mutation/live auth coverage (139 passed); ruff format/check and diff check passed.
    - Cleanup: Item-owned scratch was already removed after its earlier verification; unrelated concurrent changes retained.

- [x] django_strawberry_framework/utils/strings.py
    - Status: verified
    - docs/shadow/current/django_strawberry_framework__utils__strings.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__strings.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/strings.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__strings.stripped.py and docs/shadow/current/django_strawberry_framework__utils__strings.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed Medium hostile string-subclass defects. Cache-key hashing and overridden string methods could escape raw exceptions from ``snake_case``, ``pascal_case``, and ``flatten_lookup_path``; inputs are normalized through safe exact-string conversion before cache/method dispatch, with typed errors for non-strings. The full ``snake_case`` ``lru_cache`` API remains available. Files changed: ``django_strawberry_framework/utils/strings.py``, ``tests/utils/test_strings.py``.
    - Verification: Passed. Focused string/import/input/filter/order/mutation coverage (210 passed), caller coverage (149 passed), and live relation-filter checks (3 passed). Ruff format/check and diff check passed.
    - Cleanup: Item scratch was removed after verification; unrelated concurrent changes retained.

- [x] django_strawberry_framework/utils/typing.py
    - Status: verified
    - docs/shadow/current/django_strawberry_framework__utils__typing.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__typing.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/typing.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__typing.stripped.py and docs/shadow/current/django_strawberry_framework__utils__typing.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed Medium nested-wrapper detection. Async callable predicates unwrapped only one wrapper ordering, so ``staticmethod(functools.partial(async callable instance))`` was misclassified as synchronous. Inspection now repeatedly unwraps the supported ``partial``/``staticmethod`` layers, with permanent coroutine and async-generator regressions. Files changed: ``django_strawberry_framework/utils/typing.py``, ``tests/utils/test_typing.py``.
    - Verification: Passed. Worker 0 reproduced both misclassifications before the fix, then reran retained scratch plus package typing tests (47 passed); ruff format/check and diff check passed.
    - Cleanup: Removed ``docs/bug_hunt/temp-tests/utils_typing/``; unrelated concurrent changes retained.

- [x] django_strawberry_framework/utils/write_transaction.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__utils__write_transaction.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__write_transaction.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/write_transaction.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__write_transaction.stripped.py and docs/shadow/current/django_strawberry_framework__utils__write_transaction.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No confirmed production defect. Alias pinning, managed-transaction refusal, read-only authorization barriers, write-phase guards, row locks, target snapshots, and conflict handling remained coherent under hostile SQL classification and transaction probes.
    - Verification: Passed. Worker 0 reran the connected write-transaction/form/serializer/auth package selection (336 passed); Worker 1 hostile SQL/CTE/fingerprint probes also passed. Ruff format/check and diff check passed.
    - Cleanup: No item scratch remained; unrelated concurrent changes retained.

- [x] django_strawberry_framework/utils/write_values.py
    - Status: verified
    - docs/shadow/current/django_strawberry_framework__utils__write_values.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__write_values.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/write_values.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__write_values.stripped.py and docs/shadow/current/django_strawberry_framework__utils__write_values.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed Medium relation-container error leakage. The shared batched relation decoder allowed malformed or hostile iterables to raise raw exceptions before the field-error boundary. It now materializes the input inside the relation-error boundary, preserving the one-query visibility contract for valid sets and mapping malformed containers to the normal field-keyed error. Files changed: ``django_strawberry_framework/utils/write_values.py``, ``tests/utils/test_write_values.py``.
    - Verification: Passed. Worker 0 ran utility/model/form/serializer coverage (264 passed) and live mutation/relation coverage (63 passed); ruff format/check and diff check passed.
    - Cleanup: No scratch remained; unrelated concurrent changes retained.

- [x] django_strawberry_framework/views.py
    - Status: verified
    - docs/shadow/current/django_strawberry_framework__views.stripped.py
    - docs/shadow/current/django_strawberry_framework__views.overview.md
    - Prompt:
        - Use django_strawberry_framework/views.py as the entry point. Read docs/shadow/current/django_strawberry_framework__views.stripped.py and docs/shadow/current/django_strawberry_framework__views.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed Medium lifecycle ordering defect and found no additional issue. Boundary middleware now prepares the exact mounted view instance through ``setup`` before measuring, then dispatches that instance through an opaque mount handoff; setup-derived caps cannot be bypassed by a second instance. Files changed: ``django_strawberry_framework/views.py``, ``django_strawberry_framework/_boundary_ordering.py``, ``tests/test_views.py``, and live transport coverage.
    - Verification: Passed. Worker 0 ran package view coverage (220 passed) and the complete live transport suite (77 passed); hostile lifecycle/read cases remained green. Ruff format/check and diff check passed.
    - Cleanup: No item scratch remained; unrelated concurrent changes retained.

- [x] Package integration
    - Status: no-bugs
    - Prompt:
        - Hunt the final live package across boundaries, including public exports and `__init__.py` files; implement every confirmed root-cause fix.
    - Result: No additional package defect. Public exports/version, lazy DRF names, AppConfig metadata and idempotent ready/reload patch dispatch remained coherent across fresh imports and reloads.
    - Verification: Passed. Worker 1 ran the core package initialization/app selection (13 passed); Worker 0 independently ran package initialization, app lifecycle, URL, and schema-command coverage (19 passed). Ruff format/check and diff check passed.
    - Cleanup: No item scratch remained; unrelated concurrent changes retained.

- [x] Final test gate
    - Status: verified
    - Owner: Worker 0
    - Prompt:
        - Run `uv run pytest`; require a passing suite and 100% configured package coverage.
    - Iteration: The first review run exposed teardown poisoning in a hostile model-name regression and then completed with incomplete coverage. The regression now restores immutable model metadata explicitly, reachable defensive behavior has permanent coverage, and impossible exact-built-in fallback branches were removed without changing valid or hostile-input behavior.
    - Result: Passed. The authoritative suite completed with 6074 passed, 40 skipped, and 0 xfailed, and configured package coverage reached exactly 100% (15524 statements, 0 missed).
    - Verification: Worker 0 independently reran the complete suite after the final revisions. Ruff formatting and lint, the hunt-scoped source-layout check, and diff whitespace validation passed.
    - Cleanup: Item scratch is empty; unrelated concurrent changes were retained.

## Closeout (2026-08-17)

Required by `docs/bug_hunt/HUNT.md`, omitted when the file was first set to `Status: complete`, and
added here after an independent re-verification of every item against the committed tree.

Coverage of the hunt itself is complete: the 93 items map one-to-one onto the 93 non-`__init__.py`
Python files in the live package, with no file unhunted and no item naming a file the package does
not contain.

- Confirmed fixes: 62 source files. One further item (`auth/sessions.py`) was a documentation-only
  correction, and two items (`error_policy.py`, `apps.py`) placed their fixes entirely in connected
  files rather than in the named target.
- No-bug items: 31, counting the package-integration item now recorded as `no-bugs`.
- Blockers: none. No item reached `blocked`, and no item closed at `revision-needed`.
- Severity spread across the 62 code fixes: 52 Medium, 5 Low, one recording both a Medium and a Low
  defect, and 4 (`optimizer/field_meta.py`, `optimizer/hints.py`, `optimizer/join_taxonomy.py`,
  `testing/client.py`) recorded with no severity grade, deviating from the stock result line. No
  fix was graded High or Critical.
- Final validation, re-confirmed on 2026-08-17 against the committed tree: `uv run pytest` gives
  6096 passed, 40 skipped, 0 xfailed, and 100% configured package coverage (15556 statements,
  0 missed). The higher counts than the gate recorded are the concurrently-committed review and DRY
  cycles, not hunt work. `pragma: no cover` fell from 39 to 36 across the cycle, so the gate reached
  100% without buying coverage with suppressions.
- Item-owned scratch: confirmed gone. `docs/bug_hunt/temp-tests/` is empty.
- Unrelated work left untouched: the concurrent review cycle (`docs/review/`), the DRY consolidation
  cycle, and the spec residual cycles all landed in the same working tree and were preserved, as
  each item's cleanup line states. Spot-checked survival of a hunt fix through a later concurrent
  refactor: `filters/factories.py`'s unhashable-cache discriminator now lives in
  `utils/inputs.py::make_hashable_meta_value` after the DRY consolidation folded it into the shared
  normalizer, and the identity discriminator survived intact.

Record fidelity, stated rather than back-filled, because the missing material cannot be reconstructed
without inventing it:

- 56 items carry no `Cycle baseline` line, which HUNT.md requires before dispatch. The field stops
  after `optimizer/field_meta.py` and never resumes, so for those items the separation between
  item-owned and concurrent change is not recorded and is no longer recoverable.
- 43 items carry no `Prompt` block, a contiguous run from `optimizer/field_meta.py` through
  `utils/imports.py`; the blocks resume afterwards.
- 34 of the verified items carry no separate `Verification` / `Validation` / `Cleanup` lines. Their
  evidence is present but compressed into the single `Result` line, so this is a formatting
  deviation from the stock lines rather than missing evidence.
- Seven items pin a `current target SHA-256`. Four still match the committed file; three no longer
  do, because later commits legitimately touched those files after the item closed -
  `connection.py` and `exceptions.py` through the review cycle's diagnostic-rendering guard, and
  `extensions/resource_policy.py` through the review cycle's nested-operation policy-context fix.
  The fingerprints are left as recorded, since they pin what was verified rather than what HEAD
  holds; each of those three fixes was re-confirmed present on 2026-08-17 by inspection.
