# DRY review: `django_strawberry_framework/testing/_wrap.py`

Status: verified

## System trace

`testing/_wrap.py` owns the consumer-facing **wrap-time** half of the package's
Trac #37064 defense-in-depth: one public helper,
`safe_wrap_connection_method(connection, method_name, wrapper) -> bool`.

Behavior (9 executable lines after the docstring):

1. Reject a non-callable `wrapper` with `TypeError` at the wrap site.
2. Read `getattr(connection, method_name)`.
3. If `_is_database_failure(current)`, decline (`False`, no mutation).
4. Otherwise `setattr` the wrapper and return `True`.

It does **not** own restoration/`tearDown` hygiene (documented consumer
responsibility), Django's `_add_databases_failures` /
`_remove_databases_failures` lifecycle, or the automatic unwrap-time patch.

Connected seams examined (fresh pass against present-day source):

- `_django_patches.py` — owns `_DatabaseFailure` import tolerance,
  `_is_database_failure` (single predicate both halves share),
  `_patched_remove_databases_failures`, `apply()`, and the canonical
  defense-in-depth framing. Already **verified** zero-edit in this cycle;
  traced here only as the unwrap-time sibling and predicate owner. This
  file does not incorrectly duplicate an unwrap rule that belongs in
  `_wrap`.
- `testing/__init__.py` — re-exports the helper; indexes wrap + points at
  the patch module.
- `testing/client.py` / `testing/relay.py` — sibling public testing
  surfaces (HTTP GraphQL clients; Relay GlobalID helpers). No connection
  method mutation, no shared helpers with `_wrap`.
- `connection.py` — Relay cursor pagination ("cursor" is a GraphQL/keyset
  concept, not `connections[alias].cursor`).
- `middleware/debug_toolbar.py` — GraphQL toolbar middleware; soft-dep
  install gate; does not wrap DB connection methods and has no
  `_DatabaseFailure` / `safe_wrap` references.
- `extensions/debug.py` — brackets `force_debug_cursor` / `queries_log`
  for GraphQL operations; complementary observability seam, not a second
  `_DatabaseFailure`-aware wrap protocol.
- Upstream precedent: `django-debug-toolbar` SQL panel `wrap_cursor`
  (isinstance-guard at *its* wrap site). Ecosystem peer, not a package
  duplicate. Package does not ship its own connection wrapper.
- Tests: `tests/testing/test_wrap.py` (wrap + composition with patched
  teardown); `tests/test_django_patches.py` (unwrap half). Not earnable
  via live `/graphql/` HTTP — the helper is test-instrumentation for DB
  connection attributes, not a GraphQL operation path.

Item-scoped baseline
`git diff 6adf6a7f9acd9f59480d631449cb99042d3c94f0 --
django_strawberry_framework/testing/_wrap.py` is empty (source SHA matches
baseline byte-for-byte).

## Verification

Searches / checks (re-run on present source; not seeded from prior findings):

- Import / call graph: production consumers and package tests import
  `safe_wrap_connection_method` only from
  `django_strawberry_framework.testing` (root re-export). No second wrap
  helper, no raw `isinstance(..., _DatabaseFailure)` at a package wrap
  site. Only package `setattr` on connection methods outside this helper
  is the unwrap loop in `_django_patches` (and its audited upstream body
  pins).
- Predicate already single-sited: `_wrap` imports
  `_django_patches._is_database_failure`; unwrap patch uses the same
  function. Module docstring's "both halves share the same private
  predicate" contract holds in code.
- Lookalikes vs `connection.py` / middleware / `client.py` / `relay.py` /
  `extensions/debug.py` — name or domain adjacency only; distinct
  responsibilities and change axes (confirmed by reading each owner;
  debug_toolbar middleware and debug extension have zero Trac #37064 /
  `_DatabaseFailure` hits).
- Live GraphQL: no permanent live test belongs here; wrap behavior is
  unreachable from a real operation against `/graphql/`. Package tests
  under `tests/testing/test_wrap.py` are the correct tier.
- Trac #37064 live page re-checked: resolution is `invalid` (not
  `wontfix`). Several package strings still say `wontfix` (`_wrap.py`,
  `_django_patches.py`, generated `docs/GLOSSARY.md`,
  `tests/test_django_patches.py`). Recorded below as factual drift, not a
  code-ownership consolidation this item implements (sibling
  `_django_patches` already verified; a one-file string swap would leave
  the other sites wrong).

Strongest rejected / deferred candidates:

1. **Collapse wrap helper into `_django_patches` (or reverse).** Disproved:
   wrap is a public testing opt-in; patches are private app-load side
   effects. Merging would either export private patch internals or make
   `AppConfig.ready` / patch imports pull the testing surface. Lifecycle
   sites (instance setattr vs classmethod reimplementation) and audiences
   differ; shared rule is already the predicate.

2. **Trac #37064 framing narrative across `__init__` / `_wrap` /
   `_django_patches`.** Ownership disposition: canonical framing + unwrap
   policy stay in `_django_patches`; wrap API contract + restoration
   example stay in `_wrap`; `__init__` only indexes the public helper and
   points at the patch module. Narrative overlap is intentional surface
   documentation, not a second implementation of wrap/unwrap policy.
   Collapsing prose into the private module would force consumers of the
   public helper to read a private module for the ticket story. No
   production-code consolidation.

3. **Shared `_database_failure` test builder across `test_wrap.py` /
   `test_django_patches.py`.** Disproved for this target: tiny local
   setup keeps each lifecycle suite independently legible; production
   recognition is already one function. (Same judgment as the verified
   `_django_patches` item.)

4. **Adopt debug-toolbar's wrap_cursor / cache-panel sentinel into this
   package as a shared wrap owner.** Disproved: this package does not own
   a connection wrapper of its own; `safe_wrap_connection_method` is the
   cooperative consumer protocol. Toolbar middleware and
   `extensions/debug.py` address GraphQL panel / debug-cursor bracketing,
   not `_DatabaseFailure` clobber prevention.

5. **Fold into `testing/client.py` or `testing/relay.py`.** Disproved:
   orthogonal surfaces (HTTP GraphQL ergonomics / Relay GlobalID minting
   vs DB connection instrumentation).

6. **Move `_is_database_failure` into `_wrap.py` as the "true owner."**
   Disproved: the predicate exists so both halves degrade together when
   Django's private `_DatabaseFailure` symbol moves; the import tolerance
   and symbol live in `_django_patches`. Relocating would invert the
   dependency (private patch module importing the public testing surface)
   or invent a third shared module for one one-liner.

7. **Correct `wontfix` → `invalid` across all citing sites as this
   item's consolidation.** Rejected later: Trac's `invalid` close is
   Django kicking the `isinstance` guard downstream (ticket comment 25).
   Package comments keep `wontfix`. Not `_wrap`-owned executable
   duplication.

No scratch experiment required: the helper body is a straight-line
predicate + setattr; permanent tests already pin install, decline,
missing-symbol degradation, arbitrary method names, wrap↔unwrap
composition, and non-callable `TypeError`. Source unchanged since
ITEM_BASELINE.

## Opportunities

None — wrap-time install/decline policy has a single owner
(`safe_wrap_connection_method`); `_DatabaseFailure` recognition is already
single-sited at `_is_database_failure`; lookalikes are distinct domains.
Narrative framing is an intentional ownership split (patches = canonical
framing + unwrap; `_wrap` = public wrap contract; `__init__` = index), not
a merge candidate.

## Judgment

Proved zero-edit on a fresh re-trace. Responsibility boundaries for
Trac #37064 are already correct at the code level. Ready for Worker 2.

## Implementation (Worker 1)

No tracked source edits. Item-scoped diff vs `ITEM_BASELINE`
(`6adf6a7f9acd9f59480d631449cb99042d3c94f0`) remains empty for
`django_strawberry_framework/testing/_wrap.py` (and for this artifact-only
pass, the only Worker-1 edit path is the artifact itself). No ruff (no
code edits). No changelog. Plan checkbox left unchecked for Worker 2.
Deferred pytest: none owed for a zero-edit; existing
`tests/testing/test_wrap.py` remains the permanent proof suite.

## Iterations

### Prior W1 (interrupted W2) — baseline `9004c8e5c14869945f6da5f98ad80ff820441915`

Status was set `fix-implemented` with proved zero-edit. System trace,
verification, and rejected candidates matched the present judgment
(predicate already shared; wrap/unwrap split intentional; framing /
test-builder / toolbar / client / `wontfix` candidates rejected or
deferred). W2 never completed; this pass re-reviewed present-day source
rather than treating that artifact as truth. Source SHA for
`testing/_wrap.py` is unchanged between that baseline and the current
ITEM_BASELINE.

### Fresh W1 (this pass) — baseline `6adf6a7f9acd9f59480d631449cb99042d3c94f0`

Re-traced wrap vs unwrap ownership against verified `_django_patches`,
`testing/__init__.py`, sibling testing modules, debug toolbar middleware,
debug extension, and both permanent test suites. Re-confirmed ticket
resolution `invalid`. Added explicit rejection of relocating
`_is_database_failure` into `_wrap`. No consolidations warranted; status
remains `fix-implemented` for Worker 2.

## Independent verification (Worker 2)

Outcome: **verified** (zero-edit claim holds).

**Scoped diff.**
`git diff 6adf6a7f9acd9f59480d631449cb99042d3c94f0 --
django_strawberry_framework/testing/_wrap.py` is empty. Present-day SHA
`3c61c9aa…04502ed6` matches the baseline blob byte-for-byte.

**Re-trace (independent of W1 narrative).**

- `_wrap.py` owns only wrap-time install/decline:
  non-callable `TypeError` → `getattr` → `_is_database_failure` decline →
  else `setattr` + `True`. Restoration/`tearDown` remains consumer hygiene
  (docstring example only).
- `_django_patches.py` still owns `_DatabaseFailure` import tolerance,
  `_is_database_failure`, `_patched_remove_databases_failures` (unwrap
  `setattr(..., method.wrapped)` behind the same predicate), `apply()`,
  and canonical framing. `testing/__init__.py` re-exports the helper and
  indexes the patch module; it does not reimplement wrap policy.
- Package `setattr` on connection methods: only
  `safe_wrap_connection_method` (wrap) and the unwrap loop / audited
  upstream body pins in `_django_patches`. No second wrap helper; no raw
  `isinstance(..., _DatabaseFailure)` at a package wrap site.
- `testing/client.py`, `testing/relay.py`, `middleware/debug_toolbar.py`,
  and `extensions/debug.py` have zero `_DatabaseFailure` /
  `safe_wrap` / Trac #37064 hits (fresh grep).

**Challenges to rejected / deferred candidates (source evidence).**

1. **Merge wrap ↔ patches.** Rejected holds: public testing opt-in vs
   private `AppConfig.ready` side effect; different mutation sites
   (instance setattr vs classmethod reimplementation). Shared rule is
   already `_is_database_failure`.
2. **Move predicate into `_wrap`.** Rejected holds: symbol + import
   tolerance live in `_django_patches`; relocating would invert
   private→public dependency or invent a third module for a one-liner.
3. **Fold into client/relay.** Rejected holds: orthogonal surfaces
   (HTTP GraphQL / Relay GlobalID vs DB connection instrumentation).
4. **Adopt toolbar wrap ownership / cache-panel sentinel.** Rejected
   holds: package does not ship its own connection wrapper; toolbar
   middleware and debug extension address GraphQL panel / debug-cursor
   bracketing, not `_DatabaseFailure` clobber prevention. Verified
   `_django_patches` item already recorded the same boundary.
5. **Collapse Trac framing prose.** Rejected holds: intentional surface
   documentation split (patches = canonical framing + unwrap; `_wrap` =
   public contract + restore example; `__init__` = index). Not a second
   executable policy.
6. **Shared `_database_failure` test builder.** Rejected holds: tiny
   local builders keep wrap vs unwrap suites independently legible;
   production recognition is one function.
7. **`wontfix` → `invalid` string drift.** Rejected: Trac's `invalid`
   close is Django kicking the `isinstance` guard downstream (ticket
   comment 25). Package comments keep `wontfix`. Not `_wrap`-owned
   executable duplication.

**Missed consolidation search.** Independently grepped
`safe_wrap_connection_method`, `_is_database_failure`,
`isinstance(.*_DatabaseFailure)`, and `setattr(connection` across
`django_strawberry_framework/`. No additional wrap-time owner, parallel
predicate, or connection-method wrap protocol turned up. Lookalike
"unwrap" helpers elsewhere (`utils/typing.py`, optimizer selection
unwrap, etc.) are GraphQL/type unwrapping — different domain.

**Remaining issues.** None for this item. Deferred `wontfix`→`invalid`
was later rejected: Trac's `invalid` close is Django kicking the
`isinstance` guard downstream (ticket comment 25). Package comments
keep `wontfix`.

Plan checkbox marked `[x]`.
