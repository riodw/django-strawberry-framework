# DRY review: `django_strawberry_framework/testing/_wrap.py`

Status: fix-implemented

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

Connected seams examined:

- `_django_patches.py` — owns `_DatabaseFailure` import tolerance,
  `_is_database_failure` (single predicate both halves share),
  `_patched_remove_databases_failures`, `apply()`, and the canonical
  defense-in-depth framing. Already verified zero-edit in this cycle.
- `testing/__init__.py` — re-exports the helper; indexes wrap + points at
  the patch module. Prior deferral #7 (Trac framing across `__init__` /
  `_wrap` / `_django_patches`) evaluated here.
- `testing/client.py` — GraphQL HTTP client / mixin family; no connection
  method mutation, no shared helpers with `_wrap`.
- `connection.py` — Relay cursor pagination ("cursor" is a GraphQL/keyset
  concept, not `connections[alias].cursor`).
- `middleware/debug_toolbar.py` — GraphQL toolbar middleware; soft-dep
  install gate; does not wrap DB connection methods.
- `extensions/debug.py` — brackets `force_debug_cursor` / `queries_log`
  for GraphQL operations; complementary observability seam, not a second
  `_DatabaseFailure`-aware wrap protocol.
- Upstream precedent: `django-debug-toolbar` SQL panel `wrap_cursor`
  (isinstance-guard at *its* wrap site). Ecosystem peer, not a package
  duplicate.
- Tests: `tests/testing/test_wrap.py` (wrap + composition with patched
  teardown); `tests/test_django_patches.py` (unwrap half). Not earnable
  via live `/graphql/` HTTP — the helper is test-instrumentation for DB
  connection attributes, not a GraphQL operation path.

Item baseline
`git diff 9004c8e5c14869945f6da5f98ad80ff820441915 --
django_strawberry_framework/testing/_wrap.py` is empty.

## Verification

Searches / checks:

- Import / call graph: production consumers and package tests import
  `safe_wrap_connection_method` only from
  `django_strawberry_framework.testing` (root re-export) or, for white-box
  predicate work, `_django_patches._is_database_failure`. No second wrap
  helper, no raw `isinstance(..., _DatabaseFailure)` at a package wrap
  site.
- Predicate already single-sited: `_wrap` imports
  `_django_patches._is_database_failure`; unwrap patch uses the same
  function. Module docstring's "both halves share the same private
  predicate" contract holds in code.
- Lookalikes vs `connection.py` / middleware / `client.py` /
  `extensions/debug.py` — name or domain adjacency only; distinct
  responsibilities and change axes (confirmed by reading each owner).
- Live GraphQL: no permanent live test belongs here; wrap behavior is
  unreachable from a real operation against `/graphql/`. Package tests
  under `tests/testing/test_wrap.py` are the correct tier.
- Trac #37064 live page: resolution is `invalid` (not `wontfix`). Several
  package strings still say `wontfix` (`_wrap.py`, `_django_patches.py`,
  `docs/GLOSSARY.md`, `tests/test_django_patches.py`). Recorded below as
  factual drift, not a code-ownership consolidation this item implements
  (sibling `_django_patches` already closed zero-edit in this cycle;
  GLOSSARY is generated; a one-file string swap would leave the other
  sites wrong).

Strongest rejected / deferred candidates:

1. **Collapse wrap helper into `_django_patches` (or reverse).** Disproved:
   wrap is a public testing opt-in; patches are private app-load side
   effects. Merging would either export private patch internals or make
   `AppConfig.ready` / patch imports pull the testing surface. Lifecycle
   sites (instance setattr vs classmethod reimplementation) and audiences
   differ; shared rule is already the predicate.

2. **Trac #37064 framing narrative across `__init__` / `_wrap` /
   `_django_patches` (prior deferral).** Ownership disposition: canonical
   framing + unwrap policy stay in `_django_patches`; wrap API contract +
   restoration example stay in `_wrap`; `__init__` only indexes the public
   helper and points at the patch module. Narrative overlap is intentional
   surface documentation, not a second implementation of wrap/unwrap
   policy. Collapsing prose into the private module would force consumers
   of the public helper to read a private module for the ticket story.
   No production-code consolidation.

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

5. **Fold into `testing/client.py`.** Disproved: orthogonal surfaces
   (HTTP GraphQL ergonomics vs DB connection instrumentation).

6. **Correct `wontfix` → `invalid` across all citing sites as this
   item's consolidation.** Deferred: factual disposition drift is real
   (ticket closed `invalid`), but it is standing-doc / comment accuracy
   spanning already-verified `_django_patches`, generated GLOSSARY, and
   tests — not a duplicated executable responsibility owned by `_wrap`.
   Folder pass or a maintainer docs pass can sync the resolution string
   in one sweep; implementing a partial fix here would widen concurrent-
   dirty risk without changing wrap ownership.

No scratch experiment required: the helper body is a straight-line
predicate + setattr; permanent tests already pin install, decline,
missing-symbol degradation, arbitrary method names, wrap↔unwrap
composition, and non-callable `TypeError`.

## Opportunities

None — wrap-time install/decline policy has a single owner
(`safe_wrap_connection_method`); `_DatabaseFailure` recognition is already
single-sited at `_is_database_failure`; lookalikes are distinct domains.
Prior framing deferral resolved as ownership split (patches = canonical
framing + unwrap; `_wrap` = public wrap contract; `__init__` = index), not
as a merge.

## Judgment

Proved zero-edit. Responsibility boundaries for Trac #37064 are already
correct at the code level. Ready for Worker 2.

## Implementation (Worker 1)

No tracked source edits. Item-scoped diff vs `ITEM_BASELINE`
(`9004c8e5c14869945f6da5f98ad80ff820441915`) remains empty for
`django_strawberry_framework/testing/_wrap.py`. Artifact only. No ruff
(no code edits). No changelog. Plan checkbox left unchecked for Worker 2.
