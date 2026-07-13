# DRY review: `django_strawberry_framework/conf.py`

Status: verified

## System trace

`conf.py` is the sole Django-settings boundary for the package. `Settings.__init__` establishes the
lazy-or-explicit cache state; `Settings.user_settings` lazily reads
`django.conf.settings.DJANGO_STRAWBERRY_FRAMEWORK`; `Settings.reload` replaces that state without
rebinding the singleton; and `Settings.__getattr__` translates missing keys into `AttributeError`.
`_normalize_user_settings` owns the accepted top-level shape; `reload_settings` mutates the
module singleton in place when Django emits `setting_changed`. An absent or explicitly `None`
top-level value becomes an empty mapping, a non-mapping raises `ConfigurationError`, and an absent
individual key raises `AttributeError` unless a named reader supplies its domain default.

The five named readers keep setting lookup separate from domain interpretation:

- `upstream_patches_enabled` owns the default-on bool/per-dependency mapping grammar for
  `APPLY_UPSTREAM_PATCHES`. The Django, Strawberry, and cross-web patch modules each pass their
  canonical dependency name before upstream-shape validation; `apps.py` owns startup dispatch.
- `nested_connection_strategy_setting` returns the configured value or `"windowed"`.
  `optimizer/nested_fetch.py::resolve_strategy` owns strategy-name/custom-object validation,
  `DjangoOptimizerExtension.__init__` resolves it once per extension instance, and `on_execute`
  publishes that pinned instance through the strategy `ContextVar`.
- `testing_endpoint_setting` returns the configured value or `"/graphql/"`.
  `testing/client.py::TestClient.__init__` owns constructor precedence, `query(url=...)` owns the
  one-call override, and `GraphQLTestMixin.GRAPHQL_URL` supplies the class-level rung. The async
  client inherits the same construction path.
- `hide_flat_filters_setting` returns the configured value or `False`.
  `filters/inputs.py::_build_input_fields` owns truthiness and the build-time decision to omit only
  expanded children of declared `RelatedFilter` branches.
- `relay_globalid_strategy_setting` returns the configured value or `None`.
  `types/relay.py::_resolve_globalid_strategy` owns
  `Meta.globalid_strategy` -> setting -> `DEFAULT_GLOBALID_STRATEGY` precedence and delegates both
  configured sources to `types/base.py::_validate_globalid_strategy`.

No package module reads `DJANGO_STRAWBERRY_FRAMEWORK` directly or reimplements the lazy cache,
normalization, missing-key translation, or signal refresh.

## Verification

- Searched the package, tests, examples, and standing docs for the top-level Django key, all five
  setting keys, all five readers, direct `conf.settings` access, and repeated defaults. The only
  production reads are the named paths above.
- `tests/base/test_conf.py` pins lazy loading, mapping normalization, `None`, non-mapping failures,
  missing attributes, in-place signal reload, dependency-map validation, and the pytest collection
  guard. Patch suites pin each gate before mutation/shape validation, and `tests/test_apps.py` pins
  all startup dispatches.
- Consumer tests pin the remaining policies at their owners:
  `tests/optimizer/test_nested_fetch.py` covers setting fallback, invalid strategies, eager
  instance pinning, and execution context; `tests/testing/test_client.py` covers endpoint
  precedence and live reload; `tests/filters/test_inputs.py` plus the live library API cover both
  filter shapes; Relay unit and live product API tests cover setting precedence, shared
  validation, and emitted IDs.
- `README.md`, `docs/README.md`, `docs/GLOSSARY.md`, and the fakeshop tests describe or exercise the
  same consumer-visible precedence and defaults. The example settings dict supplies no override,
  so it exercises package defaults rather than maintaining a parallel configuration.
- `git diff --name-status 25407ae81b8f6bbb4d437fa2f9be38bd0d7af10a -- <scoped paths>`
  returned empty for every production, test, example, and standing-doc path used above. Old
  build/review/DRY artifacts and private worker memory were not used as evidence. No scratch test
  was needed because the boundary and each consumer behavior are already executable and directly
  covered.

Rejected candidates:

- The five one-line `getattr(settings, KEY, default)` readers share mechanics, not one policy.
  Their defaults, validation owners, evaluation times, and error contracts differ. A generic
  getter or settings-spec table would retain every call-site decision while hiding the named
  domain boundary.
- `UPSTREAM_PATCH_DEPENDENCIES` and the three explicit `AppConfig.ready()` calls name the same
  dependencies for different reasons: one validates consumer input; the other owns import order
  and lifecycle dispatch. A dynamic registry would couple `conf.py` to startup imports and obscure
  the explicit dispatcher. Membership validation and dispatch tests already fail if either
  responsibility drifts.
- The repeated word `"windowed"` is not duplicate parsing. One occurrence is the consumer-setting
  fallback; the window strategy singleton and no-active-context fallback are executable optimizer
  behavior. They intentionally remain valid without a configured extension.
- Top-level `None` normalization and `Meta.optimizer_hints = None` both produce empty mappings, but
  they have separate inputs, lifecycles, errors, and owners. Unifying them would couple Django
  settings state to type-definition normalization.
- Repeated settings dictionaries in tests independently prove cache refresh, validation, schema
  build-time behavior, and HTTP-visible behavior. Sharing those fixtures would make the distinct
  lifecycle assertions less legible without removing production knowledge.

## Opportunities

None — each setting is read through one boundary, interpreted by its domain owner, and covered at
the strongest reachable tier. The apparent repetitions either encode distinct lifecycle
responsibilities or are reader-facing/test representations that should remain explicit.

## Judgment

The module already provides the correct true-owner split: `conf.py` owns Django integration,
normalization, defaults, and the patch-toggle grammar; consumers own domain validation and
application. No production or permanent-test consolidation is warranted.

## Independent verification (Worker 3)

Revision needed. The source ownership and executable behavior otherwise hold: the five readers are
the only package paths for these keys; missing keys, top-level normalization, singleton-preserving
`setting_changed` reloads, global/per-dependency patch gates, constructor/setting nested-strategy
precedence, test-client endpoint precedence, filter build-time truthiness, and Relay
`Meta` -> setting -> package-default precedence all re-traced to the stated consumers. The rejected
generic-reader, patch-registry, `"windowed"`, `None`-normalization, and shared-test-fixture
candidates remain correctly rejected because their policies, lifecycles, or failure contracts
differ.

The claimed docs/example alignment is not complete:

- `docs/GLOSSARY.md:1366` says a callable GlobalID encoder is per-type only, but
  `django_strawberry_framework/conf.py::relay_globalid_strategy_setting` accepts a callable and
  `django_strawberry_framework/types/relay.py::_resolve_globalid_strategy` validates and uses it
  from `RELAY_GLOBALID_STRATEGY`; `tests/types/test_relay_interfaces.py:2165` explicitly proves
  the callable setting succeeds. Reproduce with
  `git grep -n -F 'a callable is per-type only' -- docs/GLOSSARY.md` and compare that test. The
  generated glossary must be corrected at its source and re-rendered, not hand-edited.
- `examples/fakeshop/config/settings.py:229` still says the package has “No settings yet” although
  this boundary now owns five live keys. The empty mapping correctly exercises defaults, but its
  explanatory representation is stale.

The isolated no-bytecode probe covering normalization, missing-key errors, signal-driven identity
preservation, patch-map validation, endpoint restoration, explicit nested-strategy precedence, and
thin Relay/filter readers passed. The baseline command
`git diff --name-status 25407ae81b8f6bbb4d437fa2f9be38bd0d7af10a -- <all traced paths>` was
empty. Return to Worker 1 because the zero-edit review missed tracked documentation/example work;
after the review records that scope, Worker 2 should implement it. Leave `conf.py` open.

## Iterations

### Worker 1 revision after independent verification

Both missed tracked representations reproduce at baseline
`25407ae81b8f6bbb4d437fa2f9be38bd0d7af10a`. They do not change the rejected
production-code abstractions above; they replace the original zero-edit judgment with two
implementation-ready owner-alignment fixes.

#### Relay callable-setting contract

**Repeated responsibility.** The accepted value shape of `RELAY_GLOBALID_STRATEGY` is represented
by the executable validator and again by the generated consumer glossary. Those representations
must describe the same setting contract.

**Sites.** The executable owner is
`django_strawberry_framework/types/base.py::_validate_globalid_strategy`, reached for the setting by
`django_strawberry_framework/types/relay.py::_resolve_globalid_strategy` after the thin
`django_strawberry_framework/conf.py::relay_globalid_strategy_setting` read.
`tests/types/test_relay_interfaces.py::test_callable_setting_well_formed_accepted` and its invalid
callable siblings pin that path; `README.md` also states the callable setting shape. The stale
projection is the `RELAY_GLOBALID_STRATEGY` `GlossaryTerm` row (`id=519`) in tracked
`examples/fakeshop/db.sqlite3`, rendered into `docs/GLOSSARY.md` by
`scripts/build_glossary_md.py`.

**Evidence.** The reader return type includes `Callable`; `_resolve_globalid_strategy` passes a
non-`None` setting into the same validator used by `Meta`; that validator accepts sync four-argument
callables for either source; and the acceptance test finalizes a type whose setting callable emits
`"from-setting"`. In contrast, the glossary row/output says “a callable is per-type only.”
A read-only SQLite query located that exact phrase in row 519, proving the generated file and its
relational source both need correction rather than a hand edit to `docs/GLOSSARY.md`.

**Owner.** The executable accepted-value rule remains
`types/base.py::_validate_globalid_strategy`; no production change is needed. The durable
documentation owner is the tracked glossary database row, with `docs/GLOSSARY.md` as its generated
projection.

**Consolidation.** Worker 2 should update row 519's body to state that the setting accepts the same
three strings or a sync `(type_cls, model, root, info) -> str` callable, with the same shared
validation and schema-finalization lifetime as the `Meta` path, then regenerate
`docs/GLOSSARY.md` through `scripts/build_glossary_md.py`. Do not hand-edit only the rendered file.

**Proof.** Keep the existing callable-setting acceptance and invalid-callable tests unchanged; run
their focused slice. Query row 519 and grep the rendered glossary to prove the false
“per-type only” claim is gone, regenerate the glossary a second time to prove the projection is
stable, and run the repository formatting/source-layout checks required for the tracked edits.

**Risks / non-goals.** Do not narrow the setting to strings, move validation into `conf.py`, change
the `Meta` precedence, or imply callable IDs gain a decode path; callable strategies remain
encode-only. Do not add a second validator or a documentation-only workaround.

#### Fakeshop default-settings representation

**Repeated responsibility.** The example project explains what its
`DJANGO_STRAWBERRY_FRAMEWORK` mapping represents, while `conf.py` owns the actual live key
inventory and defaults. The example comment must not assert an inventory fact that changes every
time a package setting lands.

**Sites.** `django_strawberry_framework/conf.py` now defines and reads five live keys.
`examples/fakeshop/config/settings.py` deliberately supplies an empty mapping so normal fakeshop
execution exercises those defaults, while focused tests use Django settings overrides. Its comment
still says “No settings yet - placeholder for future options.”

**Evidence.** The empty mapping is valid and should remain: all named readers fall back through
`Settings.__getattr__`, and the package/live tests exercise overrides independently. Only the
comment is false. The exact stale line is present in the assigned baseline, and every involved
tracked path otherwise matches that baseline.

**Owner.** `conf.py` owns which keys exist; the example settings file owns only whether fakeshop
overrides any of them. Its comment should describe that local choice, not duplicate the package
inventory.

**Consolidation.** Worker 2 should replace the inventory claim with stable intent such as
“Intentionally empty: fakeshop exercises package defaults; focused tests override individual
settings.” Keep the mapping empty and do not enumerate the five current keys.

**Proof.** Grep the example settings file to prove “No settings yet” is gone, confirm the mapping
remains empty, and run formatting/source-layout checks. No new permanent test is warranted for a
comment-only correction; the existing reader and consumer tests already prove the behavior it
describes.

**Risks / non-goals.** Do not add example overrides merely to demonstrate settings, duplicate the
current key list in another comment, change fakeshop runtime behavior, or edit production/tests as
part of this correction.

### Worker 2 implementation

Both findings reproduced in the assigned baseline and the live checkout before editing. A read-only
query found the false “a callable is per-type only” contract in glossary term 519, and the baseline
example settings file contained the stale “No settings yet” comment. The executable ownership also
reproduced: `conf.py` is a thin reader, `types/relay.py::_resolve_globalid_strategy` applies the
setting precedence, and `types/base.py::_validate_globalid_strategy` remains the one validator for
both setting and `Meta` callables.

The durable glossary owner, term 519 in `examples/fakeshop/db.sqlite3`, now documents the three
string strategies plus the synchronous `(type_cls, model, root, info) -> str` schema-wide callable,
shared finalization-time validation, and the callable form's encode-only boundary.
`docs/GLOSSARY.md` was regenerated through `uv run python scripts/build_glossary_md.py`; it was not
hand-edited. Before the database update, rendering to a temporary path matched the current tracked
glossary byte-for-byte, proving concurrent glossary changes were already represented in the
database. The generated before/after diff then contained only term 519's two corrected paragraphs.
A second temporary render matched the updated tracked glossary byte-for-byte.

`examples/fakeshop/config/settings.py` retains an empty
`DJANGO_STRAWBERRY_FRAMEWORK` mapping and now states the stable local intent: fakeshop exercises
package defaults while focused tests override individual settings. No production code, exports, or
tests changed. The existing acceptance test and four invalid-callable tests already cover the real
setting path, so no permanent test was added; the rejected generic-reader, patch-registry,
`"windowed"`, `None`-normalization, and shared-fixture candidates remain separate for the lifecycle
and policy reasons recorded above.

Validation:

- `uv run pytest tests/types/test_relay_interfaces.py -k 'callable_setting'`: all five selected
  tests passed, then the intentionally focused run exited nonzero because whole-package coverage was
  27.18%, below the repository-wide 100% gate.
- `uv run pytest --no-cov tests/types/test_relay_interfaces.py -k 'callable_setting'`: 5 passed.
- Canonical temporary re-render plus `cmp`: passed; the updated projection is stable.
- `uv run python scripts/check_trailing_commas.py --check docs/GLOSSARY.md
  examples/fakeshop/config/settings.py docs/dry/dry-file-conf.md`: passed.
- `uv run ruff format .`: 352 files left unchanged.
- `uv run ruff check --fix .`: all checks passed.
- Status snapshots before and after both Ruff commands were identical, so neither introduced
  unrelated checkout changes.

The correction changes no shipped behavior and does not merit a changelog entry. `CHANGELOG.md` was
not edited. The item is ready for Worker 3's independent verification; Worker 2 has not marked the
plan item.

### Worker 3 final verification

Verified. The callable-setting contract independently re-traces from
`conf.py::relay_globalid_strategy_setting` through
`types/relay.py::_resolve_globalid_strategy` to the shared
`types/base.py::_validate_globalid_strategy`: the setting accepts the three named strategies or a
synchronous four-argument callable, freezes the result at schema finalization, and leaves callable
strategies encode-only. The existing acceptance, wrong-arity, async-function, async-callable-object,
and partial-wrapped-async-callable tests all passed (`5 passed`); the complete settings-boundary
file also passed (`40 passed`), both with `--no-cov`.

The authoritative SQLite row 519 now states that schema-wide callable contract accurately, and
`PRAGMA integrity_check` returned `ok`. Two fresh renders through
`scripts/build_glossary_md.py` were byte-identical to each other and to `docs/GLOSSARY.md`
(`2a18964301cfcd8e2e94835d8938c199e2d0d7c70ec9753d0f41d6b611f86aa1`), proving the standing
document is the deterministic canonical projection rather than a hand edit. The stale
“a callable is per-type only” claim is absent.

`examples/fakeshop/config/settings.py` still supplies an empty
`DJANGO_STRAWBERRY_FRAMEWORK` mapping and its comment now describes only stable local intent:
fakeshop exercises package defaults while focused tests override individual settings. The stale
“No settings yet” inventory claim is absent, and the scoped diff passes `git diff --check`.

The complete item-scoped delta from
`25407ae81b8f6bbb4d437fa2f9be38bd0d7af10a` is limited to glossary row 519 and its rendered
`RELAY_GLOBALID_STRATEGY` paragraphs, the stable-intent example comment, and this preserved DRY
record/plan routing. The database/render correction is already in `77370fa1`; the example comment
remains in the worktree. Glossary rows 488–489, the corresponding ordering-documentation hunk in
that shared commit, and all other dirty/untracked files are concurrent adjacent work and are not
absorbed into this item. No production fix or permanent test changed for the revision. No further
Worker 1 or Worker 2 return is required.
