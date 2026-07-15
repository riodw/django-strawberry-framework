# Bug hunt: 0.0.13

Status: paused — maintainer wrap-up mid-hunt (resume at `optimizer/field_meta.py`)
Mode: autonomous
Baseline commit: `1eb99b967a0ed223380bf3402919160ccff62893`

## Wrap-up note (2026-07-15)

Paused by maintainer. Worker 1 verified through `optimizer/extension.py` (Fixed High, B8
consumer-wins Prefetch nested-key strictness). Scratch cleaned (`docs/bug_hunt/temp-tests/`).
Permanent proofs: package `tests/optimizer/test_extension.py` (no fakeshop `Prefetch(...)`
consumer dogfood yet — live B8 projection/defer cases already in
`examples/fakeshop/test_query/test_library_api.py`). Concurrent dirty left untouched.
No final gate run.

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
    - Status: verified
    - Cycle baseline: HEAD `1eb99b967a0ed223380bf3402919160ccff62893` (fresh hunt dispatch 2026-07-14); live source authoritative, shadow orientation-only. Ignore unrelated dirty paths: deleted `docs/bug_hunt/dicta.md`, untracked `docs/bug_hunt/bug_hunt-0_0_12.md`.
    - Result: Fixed Medium. Sync `DjangoHTTPRequestAdapter.body` try/except wrapper only returned raw bytes after UnicodeDecodeError; UTF-8-decodable non-UTF-8 JSON (BOM-less UTF-16-LE/32, UTF-8 BOM) still returned str and broke json.loads while async bytes succeeded. Fix: `_patched_body` always returns `self.request.body` (async contract). Files: `_cross_web_patches.py`, `tests/test_cross_web_patches.py`, `examples/fakeshop/test_query/test_products_api.py`.
    - Verification: Passed. Temp-reverted production file to HEAD -> 4 permanent proof tests fail (utf16_le/bom package+live); restored -> 26 selected (permanent+scratch+live encoding cases) pass. Fix at correct owner; permanent tests at package + live /graphql tiers.
    - Cleanup: Removed docs/bug_hunt/temp-tests/cross_web_patches/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework___cross_web_patches.stripped.py
    - docs/shadow/current/django_strawberry_framework___cross_web_patches.overview.md
    - Prompt:
        - Use django_strawberry_framework/_cross_web_patches.py as the entry point. Read docs/shadow/current/django_strawberry_framework___cross_web_patches.stripped.py and docs/shadow/current/django_strawberry_framework___cross_web_patches.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/_django_patches.py
    - Status: no-bugs
    - Cycle baseline: HEAD `1eb99b967a0ed223380bf3402919160ccff62893` + verified `_cross_web_patches` fix in working tree (do not revert); ignore unrelated dirty `dicta.md` / `bug_hunt-0_0_12.md`.
    - Result: No bugs. Evidence: live Django 6.0.5 body matches pin; isinstance unwrap guard, allow-list/multi-db/recycle, apply gates, inheritance all correct. 27 permanent+scratch passed (1 multi-db skip under default settings).
    - Verification: Passed. Source unchanged; reran scratch+permanent -> 27 passed, 1 skipped. Unrelated work preserved.
    - Cleanup: Removed docs/bug_hunt/temp-tests/django_patches/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework___django_patches.stripped.py
    - docs/shadow/current/django_strawberry_framework___django_patches.overview.md
    - Prompt:
        - Use django_strawberry_framework/_django_patches.py as the entry point. Read docs/shadow/current/django_strawberry_framework___django_patches.stripped.py and docs/shadow/current/django_strawberry_framework___django_patches.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/_strawberry_patches.py
    - Status: verified
    - Cycle baseline: HEAD `1eb99b96` + verified `_cross_web_patches` working-tree fix; do not revert prior hunt fixes; ignore concurrent dirty dicta/0_0_12.
    - Result: Fixed High. Envelope guard accepted any list; upstream `_validate_batch_request` never type-checks elements then does `item.get("query")` → AttributeError/500 when batching enabled (`[1,2,3]`, `[null]`, mixed). Hidden when batching off (400 "Batching is not enabled" first). Fix: accept list only when every element is dict. Files: `_strawberry_patches.py`, `tests/test_strawberry_patches.py`, `examples/fakeshop/test_query/test_products_api.py`.
    - Verification: Passed. Temp-revert production -> 7 permanent proofs fail; restored -> 30 selected (package+live+scratch) pass. Fix at correct owner; cross_web fix untouched.
    - Cleanup: Removed docs/bug_hunt/temp-tests/strawberry_patches/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework___strawberry_patches.stripped.py
    - docs/shadow/current/django_strawberry_framework___strawberry_patches.overview.md
    - Prompt:
        - Use django_strawberry_framework/_strawberry_patches.py as the entry point. Read docs/shadow/current/django_strawberry_framework___strawberry_patches.stripped.py and docs/shadow/current/django_strawberry_framework___strawberry_patches.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/apps.py
    - Status: no-bugs
    - Cycle baseline: HEAD `1eb99b96` + verified `_cross_web_patches` + `_strawberry_patches` working-tree fixes; do not revert; ignore concurrent dirty dicta/0_0_12.
    - Result: No bugs. Evidence: ready() dispatch order django→strawberry→cross_web; double-ready idempotent; self-heal; global/per-dep opt-out; malformed settings fail-loud; mid-dispatch abort leaves earlier install (fail-loud). 15 scratch + 7 permanent apps tests green.
    - Verification: Passed. Source unchanged; reran scratch+permanent apps tests. Concurrent dirty utils/permissions left untouched.
    - Cleanup: Removed docs/bug_hunt/temp-tests/apps/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__apps.stripped.py
    - docs/shadow/current/django_strawberry_framework__apps.overview.md
    - Prompt:
        - Use django_strawberry_framework/apps.py as the entry point. Read docs/shadow/current/django_strawberry_framework__apps.stripped.py and docs/shadow/current/django_strawberry_framework__apps.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/auth/mutations.py
    - Status: no-bugs
    - Cycle baseline: HEAD `1eb99b96` + verified patch fixes (`_cross_web_patches`, `_strawberry_patches`); do not revert; ignore concurrent dirty (dicta, 0_0_12, utils/permissions if present).
    - Result: No bugs. Evidence: login/logout/register session semantics, failed-login retention, staff get_queryset, async lazy logout, IntegrityError envelope, surrogates all match pinned contracts. Permanent auth suites 50/50 passed.
    - Verification: Passed. Source unchanged; permanent `test_auth_api.py` + `tests/auth/test_mutations.py` -> 50 passed. Scratch probe failures during first verify were bad GraphQL shapes (`ok`/`user` on LoginPayload — fields do not exist); not product defects. Concurrent dirty left untouched.
    - Cleanup: Removed docs/bug_hunt/temp-tests/auth_mutations/ (+ W1 recheck scratch); unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__auth__mutations.stripped.py
    - docs/shadow/current/django_strawberry_framework__auth__mutations.overview.md
    - Prompt:
        - Use django_strawberry_framework/auth/mutations.py as the entry point. Read docs/shadow/current/django_strawberry_framework__auth__mutations.stripped.py and docs/shadow/current/django_strawberry_framework__auth__mutations.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/auth/queries.py
    - Status: no-bugs
    - Cycle baseline: HEAD `1eb99b96` + verified `_cross_web_patches` + `_strawberry_patches`; do not revert; ignore concurrent dirty.
    - Result: No bugs. Evidence: anonymous/authenticated/async/Channels/session/alias me edges match Decision 7; 34 scratch + 11 permanent queries tests green.
    - Verification: Passed. Source unchanged; reran scratch+permanent -> 44 passed. Concurrent dirty (permissions, finalizer) left untouched.
    - Cleanup: Removed docs/bug_hunt/temp-tests/auth_queries/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__auth__queries.stripped.py
    - docs/shadow/current/django_strawberry_framework__auth__queries.overview.md
    - Prompt:
        - Use django_strawberry_framework/auth/queries.py as the entry point. Read docs/shadow/current/django_strawberry_framework__auth__queries.stripped.py and docs/shadow/current/django_strawberry_framework__auth__queries.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/conf.py
    - Status: verified
    - Cycle baseline: HEAD `1eb99b96` + verified patch fixes; do not revert; ignore concurrent dirty (dicta, 0_0_12, permissions, finalizer).
    - Result: Fixed Medium. Signal-only cache invalidation left stale overrides after `del settings.DJANGO_STRAWBERRY_FRAMEWORK` (pytest-django deletes without `setting_changed`). Fix: django-backed live sync via `_live_source` / `_django_backed`; normalize before binding live source. Files: `conf.py`, `tests/base/test_conf.py`.
    - Verification: Passed. Temp-revert -> 2 permanent proofs fail; restored -> 43 permanent pass. Remaining scratch failures assert pre-fix "STALE LIE" expectations (obsolete). Fix at correct owner.
    - Cleanup: Removed docs/bug_hunt/temp-tests/conf/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__conf.stripped.py
    - docs/shadow/current/django_strawberry_framework__conf.overview.md
    - Prompt:
        - Use django_strawberry_framework/conf.py as the entry point. Read docs/shadow/current/django_strawberry_framework__conf.stripped.py and docs/shadow/current/django_strawberry_framework__conf.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/connection.py
    - Status: verified
    - Cycle baseline: HEAD `1eb99b96` + verified fixes (`_cross_web_patches`, `_strawberry_patches`, `conf`); do not revert; ignore concurrent dirty.
    - Result: Fixed Low. Keyset `last: 0` + `after:` reported `hasPreviousPage: true` while offset/Strawberry `edges[-0:]` quirk reports `false`. `_KeysetPage.last_zero_quirk` mirrors offset. Files: `connection.py`, `examples/fakeshop/test_query/test_keyset_api.py`.
    - Verification: Passed. Temp-revert -> 2 live proofs fail; restored -> 45 permanent keyset tests pass. Scratch failures were probe/seed artifacts, not product defects.
    - Cleanup: Removed docs/bug_hunt/temp-tests/connection/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__connection.stripped.py
    - docs/shadow/current/django_strawberry_framework__connection.overview.md
    - Prompt:
        - Use django_strawberry_framework/connection.py as the entry point. Read docs/shadow/current/django_strawberry_framework__connection.stripped.py and docs/shadow/current/django_strawberry_framework__connection.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/exceptions.py
    - Status: verified
    - Cycle baseline: HEAD `1eb99b96` + verified fixes (patches, conf, connection); do not revert; ignore concurrent dirty.
    - Result: Fixed Medium. Hostile unprintable message args made GraphQL-core `located_error` replace typed ConfigurationError/OptimizerError/SyncMisuseError with RuntimeError. `DjangoStrawberryFrameworkError.__init__` sanitizes args so str/repr never raise. Files: `exceptions.py` (+ permanent coverage in `tests/test_exceptions.py`).
    - Verification: Passed. Temp-revert -> 4 permanent proofs fail; restored -> 35 package+scratch pass. Fix at hierarchy root owner.
    - Cleanup: Removed docs/bug_hunt/temp-tests/exceptions/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__exceptions.stripped.py
    - docs/shadow/current/django_strawberry_framework__exceptions.overview.md
    - Prompt:
        - Use django_strawberry_framework/exceptions.py as the entry point. Read docs/shadow/current/django_strawberry_framework__exceptions.stripped.py and docs/shadow/current/django_strawberry_framework__exceptions.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/extensions/debug.py
    - Status: verified
    - Cycle baseline: HEAD `1eb99b96` + verified fixes (patches, conf, connection, exceptions); do not revert; ignore concurrent dirty.
    - Result: Fixed Medium. Teardown always stashed debug payload; parse/validation early-return + sibling teardown raise recovered via get_results() and leaked `extensions.debug` for never-executed ops (sync+async). Fix: stash only when `execution_context.result` is graphql-core `ExecutionResult`. Files: `extensions/debug.py`, `tests/extensions/test_debug.py`.
    - Verification: Passed. Temp-revert -> 3 permanent proofs fail; restored -> 49 pass. Fix at correct owner.
    - Cleanup: Removed docs/bug_hunt/temp-tests/extensions_debug/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__extensions__debug.stripped.py
    - docs/shadow/current/django_strawberry_framework__extensions__debug.overview.md
    - Prompt:
        - Use django_strawberry_framework/extensions/debug.py as the entry point. Read docs/shadow/current/django_strawberry_framework__extensions__debug.stripped.py and docs/shadow/current/django_strawberry_framework__extensions__debug.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/filters/base.py
    - Status: verified
    - Cycle baseline: HEAD `1eb99b96` + verified hunt fixes (patches, conf, connection, exceptions, debug); do NOT revert those. IGNORE all other dirty files (concurrent sessions — filters/sets, orders/sets, registry, utils/*, types/*, middleware, TREE.md, etc.).
    - Result: Fixed Medium. `GlobalIDMultipleChoiceFilter.filter` only treated `[]` as match-nothing for `lookup_expr=="in"`; many-side `exact` delegated to upstream MultipleChoiceFilter which no-ops on empty → silent widen vs ListFilter empty-set contract. Empty-list handling now runs before in/non-in split. Files: `filters/base.py`, `tests/filters/test_base.py`.
    - Verification: Passed. Temp-revert -> empty-exact permanent proof fails; restored -> 85 package+scratch pass.
    - Cleanup: Removed docs/bug_hunt/temp-tests/filters_base/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__filters__base.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__base.overview.md
    - Prompt:
        - Use django_strawberry_framework/filters/base.py as the entry point. Read docs/shadow/current/django_strawberry_framework__filters__base.stripped.py and docs/shadow/current/django_strawberry_framework__filters__base.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/filters/factories.py
    - Status: verified
    - Cycle baseline: HEAD `1eb99b96` + verified hunt fixes including filters/base; do not revert hunt fixes; IGNORE concurrent dirty (esp. filters/sets.py if dirty from another session).
    - Result: Fixed Medium. Layer-6 AutoFilter cache: `filter_fields` vs `fields` and set/frozenset Meta shapes minted duplicate `<Model>AutoFilter` classes → BFS ConfigurationError; dict keys needed `key=repr`. Files: `filters/factories.py`, `tests/filters/test_factories.py`.
    - Verification: Passed. Temp-revert -> collection ImportError on new helper / proofs fail; restored -> 41 pass.
    - Cleanup: Removed docs/bug_hunt/temp-tests/filters_factories/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__filters__factories.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__factories.overview.md
    - Prompt:
        - Use django_strawberry_framework/filters/factories.py as the entry point. Read docs/shadow/current/django_strawberry_framework__filters__factories.stripped.py and docs/shadow/current/django_strawberry_framework__filters__factories.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/filters/inputs.py
    - Status: verified
    - Cycle baseline: HEAD `1eb99b96` + verified hunt fixes through filters/factories; do not revert; IGNORE concurrent dirty.
    - Result: Fixed Medium. `pascal_case` collapsed `field_2`/`field2` → same stem so operator-bag/range GraphQL input types silently collided; also pin `strawberry.input(name=)`. Entry `filters/inputs.py` unchanged; root cause in shared helpers. Files: `utils/strings.py`, `utils/inputs.py`, `tests/utils/test_strings.py`, `tests/filters/test_inputs.py`.
    - Verification: Passed. Temp-revert strings+inputs -> 2 digit_boundary proofs fail; restored -> 11 selected pass.
    - Cleanup: Removed docs/bug_hunt/temp-tests/filters_inputs/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__filters__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__inputs.overview.md
    - Prompt:
        - Use django_strawberry_framework/filters/inputs.py as the entry point. Read docs/shadow/current/django_strawberry_framework__filters__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__filters__inputs.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/filters/sets.py
    - Status: verified
    - Cycle baseline: HEAD `1eb99b96` + verified hunt fixes through filters/inputs (incl. strings/inputs digit-boundary). WARNING: `filters/sets.py` may already be dirty from a concurrent session — hunt the LIVE tree; do NOT revert concurrent edits unless they are your confirmed bug; do not revert hunt fixes.
    - Result: Fixed Medium. Inactive `None`/`UNSET` arms under `or` (and inconsistently `and`/`not`) materialized as match-all and widened past real sibling arms; async pre-walk already skipped them. Files: `filters/sets.py` (preserved concurrent `related_attr="related_filters"`), `tests/filters/test_sets.py`.
    - Verification: Passed. Surgical break of inactive-skip -> permanent proof fails (`['alpha','beta']` vs `['alpha']`); restored -> 100 permanent pass. Concurrent related_attr left intact.
    - Cleanup: Removed docs/bug_hunt/temp-tests/filters_sets/; unrelated work preserved (incl. pre-existing filters_sets_r2/).
    - docs/shadow/current/django_strawberry_framework__filters__sets.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__sets.overview.md
    - Prompt:
        - Use django_strawberry_framework/filters/sets.py as the entry point. Read docs/shadow/current/django_strawberry_framework__filters__sets.stripped.py and docs/shadow/current/django_strawberry_framework__filters__sets.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/forms/converter.py
    - Status: verified
    - Cycle baseline: HEAD `1eb99b96` + verified hunt fixes through filters/sets; do not revert; IGNORE concurrent dirty.
    - Result: Fixed Medium×2. (1) NullBooleanField claimed required while GraphQL allowed omit → TypeError on omit; forced optional + build site honors conversion.required. (2) JSONField collapsed via CharField MRO to str; map to strawberry.scalars.JSON. Files: `forms/converter.py`, `forms/inputs.py`, `tests/forms/test_converter.py`, `tests/forms/test_inputs.py`.
    - Verification: Passed. Temp-revert converter+inputs -> JSON permanent proofs fail; restored -> 69 pass.
    - Cleanup: Removed docs/bug_hunt/temp-tests/forms_converter/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__forms__converter.stripped.py
    - docs/shadow/current/django_strawberry_framework__forms__converter.overview.md
    - Prompt:
        - Use django_strawberry_framework/forms/converter.py as the entry point. Read docs/shadow/current/django_strawberry_framework__forms__converter.stripped.py and docs/shadow/current/django_strawberry_framework__forms__converter.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/forms/inputs.py
    - Status: verified
    - Cycle baseline: HEAD `1eb99b96` + verified hunt fixes including forms/converter (which already edited forms/inputs.py for NullBoolean requiredness). Hunt remaining forms/inputs surface; do not revert converter-owned changes; IGNORE concurrent dirty.
    - Result: Fixed Medium. `_model_column_for` treated reverse relations as columns so extra CharField `items` on Category emitted `itemsId`. Ignore `ForeignObjectRel`. Files: `forms/inputs.py`, `tests/forms/test_inputs.py`. NullBoolean requiredness from converter hunt preserved.
    - Verification: Passed. Surgical remove ForeignObjectRel guard -> permanent reverse-shadow proof fails (`items_id`); restored -> pass.
    - Cleanup: Removed docs/bug_hunt/temp-tests/forms_inputs/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__forms__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__forms__inputs.overview.md
    - Prompt:
        - Use django_strawberry_framework/forms/inputs.py as the entry point. Read docs/shadow/current/django_strawberry_framework__forms__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__forms__inputs.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/forms/resolvers.py
    - Status: no-bugs
    - Cycle baseline: HEAD `1eb99b96` + verified hunt fixes through forms/inputs; do not revert; IGNORE concurrent dirty.
    - Result: No bugs. Evidence: validation→FieldError, Upload/files=, get_form_kwargs, auth-before-decode, visibility, sync/async, Boolean/M2M/file partial updates all match pinned contracts. Permanent `tests/forms/test_resolvers.py` 47/47.
    - Verification: Passed. Source unchanged; permanent 47 passed. Two scratch probe failures were disposable assertion/setup noise (empty-update print probe; datetime naive), not product defects.
    - Cleanup: Removed docs/bug_hunt/temp-tests/forms_resolvers/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__forms__resolvers.stripped.py
    - docs/shadow/current/django_strawberry_framework__forms__resolvers.overview.md
    - Prompt:
        - Use django_strawberry_framework/forms/resolvers.py as the entry point. Read docs/shadow/current/django_strawberry_framework__forms__resolvers.stripped.py and docs/shadow/current/django_strawberry_framework__forms__resolvers.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/forms/sets.py
    - Status: verified
    - Cycle baseline: HEAD `1eb99b96` + verified hunt fixes through forms/resolvers; do not revert; IGNORE concurrent dirty.
    - Result: Fixed Medium. Decision 10 rejected `Meta.operation` only via `vars(meta)` own-keys; inherited Meta parent with `operation` silently accepted. Presence now `hasattr` (MRO-visible like form_class). Files: `forms/sets.py`, `tests/forms/test_sets.py`.
    - Verification: Passed. Surgical revert to vars(meta) -> 4 inherited-operation proofs fail; restored -> 52 pass.
    - Cleanup: Removed docs/bug_hunt/temp-tests/forms_sets/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__forms__sets.stripped.py
    - docs/shadow/current/django_strawberry_framework__forms__sets.overview.md
    - Prompt:
        - Use django_strawberry_framework/forms/sets.py as the entry point. Read docs/shadow/current/django_strawberry_framework__forms__sets.stripped.py and docs/shadow/current/django_strawberry_framework__forms__sets.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/keyset.py
    - Status: verified
    - Cycle baseline: HEAD `1eb99b96` + verified hunt fixes through forms/sets; do not revert; IGNORE concurrent dirty.
    - Result: Fixed Medium. Char/Text `None` encoded as string `"None"` via value_to_string → seekable cursor colliding with real rows. `serialize_cursor_value` / `encode_keyset_cursor` reject NULL loudly; literal `"None"` still round-trips. Files: `keyset.py`, `tests/test_keyset.py`, `examples/fakeshop/test_query/test_keyset_api.py`. Note: working tree also carries concurrent/new `keyset_seek_greater` (not at hunt baseline HEAD) — left intact.
    - Verification: Passed. Permanent null/None codec + live title `"None"` tests pass with fix. Full HEAD revert of keyset.py also drops concurrent `keyset_seek_greater` (collection ImportError) — not used as sole proof; permanent pins exercise the NULL reject path.
    - Cleanup: Removed docs/bug_hunt/temp-tests/keyset/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__keyset.stripped.py
    - docs/shadow/current/django_strawberry_framework__keyset.overview.md
    - Prompt:
        - Use django_strawberry_framework/keyset.py as the entry point. Read docs/shadow/current/django_strawberry_framework__keyset.stripped.py and docs/shadow/current/django_strawberry_framework__keyset.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/list_field.py
    - Status: no-bugs
    - Cycle baseline: HEAD `1eb99b96` + verified hunt fixes through keyset; do not revert; IGNORE concurrent dirty.
    - Result: No bugs. Evidence: empty lists, sync/async, permissions/cascade, RelatedManager, filter/order signature stripping all match documented contracts. Permanent `tests/test_list_field.py` 30/30.
    - Verification: Passed. Source unchanged; permanent 30 passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/list_field/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__list_field.stripped.py
    - docs/shadow/current/django_strawberry_framework__list_field.overview.md
    - Prompt:
        - Use django_strawberry_framework/list_field.py as the entry point. Read docs/shadow/current/django_strawberry_framework__list_field.stripped.py and docs/shadow/current/django_strawberry_framework__list_field.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/management/commands/_imports.py
    - Status: no-bugs
    - Cycle baseline: HEAD `1eb99b96` + verified hunt fixes through list_field; do not revert; IGNORE concurrent dirty (many files).
    - Result: No bugs. Evidence: empty/relative/path-like selectors → CommandError with zero ValueError/TypeError leaks; package vs module contracts hold. Permanent management import suite green.
    - Verification: Passed. Source unchanged; `tests/management/test_imports.py` passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/mgmt_imports/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__management__commands___imports.stripped.py
    - docs/shadow/current/django_strawberry_framework__management__commands___imports.overview.md
    - Prompt:
        - Use django_strawberry_framework/management/commands/_imports.py as the entry point. Read docs/shadow/current/django_strawberry_framework__management__commands___imports.stripped.py and docs/shadow/current/django_strawberry_framework__management__commands___imports.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/management/commands/export_schema.py
    - Status: verified
    - Cycle baseline: HEAD `1eb99b96` + verified hunt fixes through _imports; do not revert; IGNORE concurrent dirty.
    - Result: Fixed Medium+Low. (1) stdout used Django ending=`\n` so redirect≠`--path`/`print_schema` by one newline — use `ending=""`. (2) Whitespace-only `--path` wrote a spaces-named file — reject blank/whitespace. Files: `export_schema.py`, `tests/management/test_export_schema.py`.
    - Verification: Passed. Temp-revert -> 2 permanent proofs fail; restored -> 13 pass.
    - Cleanup: Removed docs/bug_hunt/temp-tests/export_schema/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__management__commands__export_schema.stripped.py
    - docs/shadow/current/django_strawberry_framework__management__commands__export_schema.overview.md
    - Prompt:
        - Use django_strawberry_framework/management/commands/export_schema.py as the entry point. Read docs/shadow/current/django_strawberry_framework__management__commands__export_schema.stripped.py and docs/shadow/current/django_strawberry_framework__management__commands__export_schema.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/management/commands/inspect_django_type.py
    - Status: verified
    - Cycle baseline: HEAD `1eb99b96` + verified hunt fixes through export_schema; do not revert; IGNORE concurrent dirty.
    - Result: Fixed Medium. Bare-name lookup and table title used Python `__name__` only, ignoring `Meta.name`/`graphql_type_name` (e.g. `PublicPatron` failed; title wrong). Lookup matches GraphQL or class name with collision ambiguity; title uses SDL name. Files: `inspect_django_type.py`, `tests/management/test_inspect_django_type.py`, `examples/fakeshop/tests/test_inspect_django_type.py`.
    - Verification: Passed. Temp-revert -> 2 Meta.name permanent proofs fail; restored -> 25 package inspect tests pass.
    - Cleanup: Removed docs/bug_hunt/temp-tests/inspect_django_type/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__management__commands__inspect_django_type.stripped.py
    - docs/shadow/current/django_strawberry_framework__management__commands__inspect_django_type.overview.md
    - Prompt:
        - Use django_strawberry_framework/management/commands/inspect_django_type.py as the entry point. Read docs/shadow/current/django_strawberry_framework__management__commands__inspect_django_type.stripped.py and docs/shadow/current/django_strawberry_framework__management__commands__inspect_django_type.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/middleware/debug_toolbar.py
    - Status: verified
    - Cycle baseline: HEAD `1eb99b96` + verified hunt fixes through inspect; do not revert; IGNORE concurrent dirty (middleware may already be dirty from another session — hunt LIVE, do not revert concurrent).
    - Result: Fixed High. GraphiQL bridge used `document.getElementById("djDebug")` which misses debug-toolbar≥7 shadow DOM (`USE_SHADOW_DOM=True`); panels/`data-request-id` never updated. Template mirrors stock `getDebugElement()` + light-DOM fallback. Files: `templates/.../debug_toolbar.html`, `tests/middleware/test_debug_toolbar.py` (`.py` concurrent dirty left intact aside from trivial docstring if any).
    - Verification: Passed. Temp-revert template to HEAD -> Test 16 `djDebugRoot` assertion fails; restored -> pass. Full middleware suite green with fix.
    - Cleanup: Removed docs/bug_hunt/temp-tests/debug_toolbar_mw/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__middleware__debug_toolbar.stripped.py
    - docs/shadow/current/django_strawberry_framework__middleware__debug_toolbar.overview.md
    - Prompt:
        - Use django_strawberry_framework/middleware/debug_toolbar.py as the entry point. Read docs/shadow/current/django_strawberry_framework__middleware__debug_toolbar.stripped.py and docs/shadow/current/django_strawberry_framework__middleware__debug_toolbar.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/mutations/fields.py
    - Status: no-bugs
    - Cycle baseline: HEAD `1eb99b96` + verified hunt fixes through middleware/debug_toolbar; do not revert; IGNORE concurrent dirty.
    - Result: No bugs. Evidence: abstract targets, subclass-without-own-Meta, registry lifecycle, signature synthesis, create/update/delete/form resolver kwargs all hold. Permanent + scratch 57 passed.
    - Verification: Passed. Source unchanged; permanent fields suite + scratch green.
    - Cleanup: Removed docs/bug_hunt/temp-tests/mutations_fields/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__mutations__fields.stripped.py
    - docs/shadow/current/django_strawberry_framework__mutations__fields.overview.md
    - Prompt:
        - Use django_strawberry_framework/mutations/fields.py as the entry point. Read docs/shadow/current/django_strawberry_framework__mutations__fields.stripped.py and docs/shadow/current/django_strawberry_framework__mutations__fields.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/mutations/inputs.py
    - Status: verified
    - Cycle baseline: HEAD `1eb99b96` + verified hunt fixes through mutations/fields; do not revert; IGNORE concurrent dirty. Note: utils/inputs digit pin already landed via filters/inputs hunt — check whether mutations/inputs still has a parallel gap.
    - Result: Fixed Medium. `pascalize_token` collapsed `field_2`/`field2` → same narrowed mutation input type name (`WidgetField2Input`). Retain underscore-before-digit. Files: `utils/inputs.py` (root), docstring in `mutations/inputs.py`, `tests/mutations/test_inputs.py`, `tests/utils/test_inputs.py`. Field-level wire pin already correct.
    - Verification: Passed. Surgical break of pascalize_token -> 2 digit proofs fail; restored -> 4 digit tests pass.
    - Cleanup: Removed docs/bug_hunt/temp-tests/mutations_inputs/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__mutations__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__mutations__inputs.overview.md
    - Prompt:
        - Use django_strawberry_framework/mutations/inputs.py as the entry point. Read docs/shadow/current/django_strawberry_framework__mutations__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__mutations__inputs.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/mutations/permissions.py
    - Status: verified
    - Cycle baseline: HEAD `1eb99b96` + verified hunt fixes through mutations/inputs; do not revert; IGNORE concurrent dirty (mutations/permissions may be dirty from another session).
    - Result: Fixed High. `DjangoModelPermission.has_permission` used `bool(user.has_perm(...))`; awaitable returns are truthy → silent ALLOW. Now `reject_async_in_sync_context` → SyncMisuseError. Files: `mutations/permissions.py`, `tests/mutations/test_permissions.py`.
    - Verification: Passed. Surgical restore of `bool(user.has_perm)` -> permanent awaitable_has_perm proof fails; restored -> permanent suite green. One scratch live assert used wrong error shape (in-band vs top-level) — not a product defect.
    - Cleanup: Removed docs/bug_hunt/temp-tests/mutations_permissions/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__mutations__permissions.stripped.py
    - docs/shadow/current/django_strawberry_framework__mutations__permissions.overview.md
    - Prompt:
        - Use django_strawberry_framework/mutations/permissions.py as the entry point. Read docs/shadow/current/django_strawberry_framework__mutations__permissions.stripped.py and docs/shadow/current/django_strawberry_framework__mutations__permissions.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/mutations/resolvers.py
    - Status: verified
    - Cycle baseline: HEAD `1eb99b96` + verified hunt fixes through mutations/permissions; do not revert; IGNORE concurrent dirty.
    - Result: Fixed Medium×2. (1) Explicit null on null=False FK (esp blank=True) leaked as __all__/IntegrityError — field-keyed null FieldError at decode. (2) `transaction.atomic()` ignored `router.db_for_write` — now `atomic(using=…)`/`set_rollback(using=…)`. Files: `mutations/resolvers.py`, `tests/mutations/test_resolvers.py`, `examples/fakeshop/test_query/test_products_api.py`.
    - Verification: Passed. Temp-revert -> blank_true FK permanent proof fails (`__all__` vs `targetId`); restored -> 10 selected null/atomic proofs pass.
    - Cleanup: Removed docs/bug_hunt/temp-tests/mutations_resolvers/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__mutations__resolvers.stripped.py
    - docs/shadow/current/django_strawberry_framework__mutations__resolvers.overview.md
    - Prompt:
        - Use django_strawberry_framework/mutations/resolvers.py as the entry point. Read docs/shadow/current/django_strawberry_framework__mutations__resolvers.stripped.py and docs/shadow/current/django_strawberry_framework__mutations__resolvers.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/mutations/sets.py
    - Status: verified
    - Cycle baseline: HEAD `1eb99b96` + verified hunt fixes through mutations/resolvers; do not revert; IGNORE concurrent dirty.
    - Result: Fixed High+Medium. Non-model `Meta.model` and unknown/empty create-update `fields`/`exclude` deferred to finalize (AttributeError/TypeError or late ConfigurationError). Now ConfigurationError at class creation; non-string field entries rejected in `normalize_field_name_sequence`. Files: `mutations/sets.py`, `utils/inputs.py`, `tests/mutations/test_sets.py`.
    - Verification: Passed. Temp-revert sets.py -> unknown/empty fields permanent proofs fail; restored -> 68 pass.
    - Cleanup: Removed docs/bug_hunt/temp-tests/mutations_sets/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__mutations__sets.stripped.py
    - docs/shadow/current/django_strawberry_framework__mutations__sets.overview.md
    - Prompt:
        - Use django_strawberry_framework/mutations/sets.py as the entry point. Read docs/shadow/current/django_strawberry_framework__mutations__sets.stripped.py and docs/shadow/current/django_strawberry_framework__mutations__sets.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/optimizer/_context.py
    - Status: verified
    - Cycle baseline: HEAD `1eb99b96` + verified hunt fixes through mutations/sets; do not revert; IGNORE concurrent dirty.
    - Result: Fixed High. Reused `context_value` leaked `DST_OPTIMIZER_*` sentinels across executions (wrong FK elision stubs + masked N+1). `clear_optimizer_context` at `on_execute` start. Files: `optimizer/_context.py`, `optimizer/extension.py`, `tests/optimizer/test_extension.py`.
    - Verification: Passed. Temp-revert _context+extension -> 5 permanent clear/reused-context proofs fail; restored -> 11 pass.
    - Cleanup: Removed docs/bug_hunt/temp-tests/optimizer_context/; unrelated work preserved.
    - docs/shadow/current/django_strawberry_framework__optimizer___context.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer___context.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/_context.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer___context.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer___context.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/optimizer/extension.py
    - Status: verified
    - Cycle baseline: HEAD `1eb99b96` + verified hunt fixes including optimizer/_context clear; do not revert clear; IGNORE concurrent dirty.
    - Result: Fixed High. B8 consumer-wins Prefetch drop published pre-diff `planned_resolver_keys`, masking nested N+1 under `strictness="raise"`. Publish now runs after `diff_plan_for_queryset`; `prefetch_path_resolver_keys` couple/strip dropped keys (+ FK elisions). Files: `optimizer/extension.py`, `optimizer/plans.py`, `optimizer/walker.py`, `tests/optimizer/test_extension.py`. `on_execute` clear preserved.
    - Verification: Passed. Publish-before-diff revert → permanent nested-keys proof fails; restored → pass. Updated stale B8 cache-integrity test for POST-diff B5 stash vs pre-diff B1 cache. Live library projection/defer B8 suites still green. No live Prefetch-object dogfood in fakeshop (package tier correct per test_query README).
    - Cleanup: Removed docs/bug_hunt/temp-tests/optimizer_extension/; unrelated work preserved.
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

- [ ] django_strawberry_framework/optimizer/selections.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__optimizer__selections.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__selections.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/selections.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__selections.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__selections.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

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

- [ ] django_strawberry_framework/sets_mixins.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__sets_mixins.stripped.py
    - docs/shadow/current/django_strawberry_framework__sets_mixins.overview.md
    - Prompt:
        - Use django_strawberry_framework/sets_mixins.py as the entry point. Read docs/shadow/current/django_strawberry_framework__sets_mixins.stripped.py and docs/shadow/current/django_strawberry_framework__sets_mixins.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/testing/_wrap.py
    - Status: pending
    - Baseline shadow: none (live file added or absent at hunt baseline)
    - Prompt:
        - Use django_strawberry_framework/testing/_wrap.py as the entry point. No baseline shadow exists; hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/testing/client.py
    - Status: pending
    - Baseline shadow: none (live file added or absent at hunt baseline)
    - Prompt:
        - Use django_strawberry_framework/testing/client.py as the entry point. No baseline shadow exists; hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/testing/relay.py
    - Status: pending
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
