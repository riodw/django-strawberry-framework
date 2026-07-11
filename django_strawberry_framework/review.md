# Pre-BETA review: package root modules

Scope of this file: the **root-level** modules that live directly under
`django_strawberry_framework/` and belong to no sub-package -- the pagination
family (`connection.py`, `keyset.py`, `relay.py`, `list_field.py`), the type
registry (`registry.py`), and the infrastructure modules (`routers.py`,
`scalars.py`, `exceptions.py`, `conf.py`, `permissions.py`, `sets_mixins.py`,
`apps.py`, the three `_*_patches.py` shims, `__init__.py`). Each sub-package has
its own `review.md`.

Method: logic-only read of the stripped snapshot in `docs/shadow/current/`
plus the diffs since the `0.0.13` tag in `docs/shadow/diff/`, cross-checked
against the real source for docstring/comment context. No tests were run and
no code was changed (AGENTS.md #14). Findings carry a confidence tag and a
one-line `Verify:` hint; the maintainer writes the exploration scripts.

Bottom line: the pagination/keyset surface is the newest and least-soaked code
in the package (the value-cursor codec shipped in `0e84f5e9`) and deserves the
most scrutiny before BETA. I found no P0 correctness defect, but two behaviors
(the `last: 0` unbounded fetch, the single-process-global registry) are worth a
decision before the API freezes.

## P0 -- correctness suspicions

None found in the root modules.

## P1 -- fix before BETA

### `connection.py::_resolve_keyset_connection` -- `last: 0` triggers an unbounded fetch
Confidence: medium. In the keyset root resolver, `last_zero_quirk` is set for
`last == 0` with no `first`/`before`, and it forces `page_size = None`, hence
`fetch_limit = None`, hence the code lists the *entire* queryset
(`list(fetch_queryset)`) to reproduce strawberry's `edges[-0:]`-serves-all
quirk. On a large table a single `connection(last: 0)` becomes a full-table
scan + full model instantiation. The offset pipeline reaches the same quirk
through a fallback that is itself bounded by `max_results`; the keyset path is
not. Root-cause options: either cap the "serve all" reproduction at
`resolve_relay_max_results(...)` like every other keyset window, or make
`last: 0` return an empty page (the arguably-more-correct Relay reading) rather
than inheriting the upstream bug into a new code path.
Verify: issue `{ conn(last: 0) { edges { node { id } } } }` against a keyset
connection over a large table and watch the row count fetched / SQL emitted.

### `registry.py::TypeRegistry` -- one global registry per process; document the multi-schema/re-entrancy boundary
Confidence: medium (architectural, not a bug). `registry` is a module-level
singleton and `finalize_django_types` flips a single global `_finalized` flag.
Two `strawberry.Schema` instances in one process therefore share one type
registry and one finalization; there is no per-schema isolation. Type
finalization also mutates the consumer's own classes
(`types/finalizer.py::_synthesize_relation_connections` does
`setattr(type_cls, generated, field_obj)` and pops annotations), and those
mutations persist on the class objects across `registry.clear()`. This is
internally consistent and the elaborate `clear()` exists precisely to support
test re-finalization, but for a library heading to BETA the constraint
"one finalized schema per process" (and its implications for multi-tenant /
multi-schema deployments and for consumers who build a schema twice) should be
an explicit, documented contract rather than an emergent property.
Verify: build two schemas with disjoint type sets in one interpreter and assert
whether the second sees the first's synthesized connection fields.

## P2 -- polish / hardening

### `registry.py::TypeRegistry.clear` -- string-referenced teardown fails silently on drift
Confidence: medium. `clear()` reaches into roughly ten other modules' caches by
string module-path/attr via `_clear_if_importable(...)`; when a path no longer
imports, the helper returns `None` and silently no-ops. A cache that gets
renamed or moved therefore stops being cleared with no error, reintroducing the
cross-test-pollution class the project has already fought. `register_subsystem_clear`
already provides a registration-based alternative; migrating the hardcoded
string references onto it (so a cache announces its own teardown at import time)
removes the silent-drift failure mode at the root.
Verify: rename one cached module attr and confirm a full parallel test run still
passes -- if it does, that cache was silently not being cleared.

### `keyset.py::_cursor_aessiv` -- LRU of 4 can thrash under many rotation keys
Confidence: low (perf only, not correctness). The AES-SIV instance cache is
`lru_cache(maxsize=4)` keyed by secret. A deployment mid-rotation with more
than three `SECRET_KEY_FALLBACKS` entries evicts and re-derives HMAC digests on
each decode attempt. Correctness is unaffected (the value is recomputed);
sizing the cache to `1 + len(SECRET_KEY_FALLBACKS)` would remove the churn.
Verify: set several fallbacks and count `salted_hmac` calls across a decode loop.

### `_*_patches.py` -- pin the exact upstream shapes each monkeypatch assumes
Confidence: low. The three patch shims target strawberry/django internals at the
`strawberry-graphql>=0.316.0` floor. Monkeypatches are the most version-fragile
code in any integration package: a minor upstream bump can silently change the
patched symbol's shape so the patch either no-ops or double-applies. Before
BETA, each patch site should assert the upstream shape it depends on (attribute
present, signature arity) and fail loud on mismatch, so a dependency bump
surfaces as a clear error rather than a subtle behavioral drift.
Verify: import the package twice (re-import) and confirm each patch is idempotent
and raises if its target symbol is absent.

## API & consistency notes

- `scalars.py::strawberry_config` cleanly rejects a caller-supplied `scalar_map`
  and key collisions before merging the package `BigInt` scalar -- good guard.
  `BigInt` (de)serializes as a *string* on the wire, which is the correct choice
  for 64-bit ids in JS clients; keep it stable through BETA since changing a
  scalar's wire form is breaking.
- `permissions.py::apply_cascade_permissions` threads the queryset's DB alias
  (`.using(queryset.db)`) into every cascaded visibility subquery and uses a
  `ContextVar`-backed cycle guard -- both correct and multi-DB-safe.
- `conf.py` reads `DJANGO_STRAWBERRY_FRAMEWORK` and raises `AttributeError` on
  missing keys by design (AGENTS.md #19). Confirm the settings values are read
  per-access (not import-time cached) so `override_settings` in consumer tests
  is honored -- worth an explicit note in the module docstring.

## Verified sound (do not re-flag)

- `keyset.py::keyset_seek_q` -- the OR-expansion
  `a CMP v0 OR (a=v0 AND b CMP v1) OR ...` ANDed with the redundant leading
  bound `a CMP= v0` is correct for mixed ASC/DESC and, because the terminal
  column is unique, strictly excludes the cursor row in both directions.
- `keyset.py::_deserialize_cursor_value` -- the `to_python` -> re-`value_to_string`
  == raw canonicalization check cannot reject a legitimately minted cursor,
  because `encode_keyset_cursor` mints via the same `serialize_cursor_value`, so
  the stored form is already canonical. It is a genuine tamper/round-trip guard.
- `keyset.py` crypto path -- AES-SIV is a soft dependency behind
  `require_optional_module`; decode iterates `SECRET_KEY` + `SECRET_KEY_FALLBACKS`
  (always present at the Django 5.2 floor) for rotation and degrades a bad/tampered
  cursor to a clean `GraphQLError`, never a 500.
- `keyset.py::validate_cursor_field_columns` -- enforces local/concrete/
  non-nullable columns with a unique terminal at finalization, so a misdeclared
  `Meta.cursor_field` fails at build time, not first query.
- `connection.py::_keyset_connection_context` -- caches on `cls.__dict__` (not
  `getattr`), so a subclass connection does not inherit a parent's cached state.
- `connection.py` keyset pageInfo -- forward `hasNextPage`=overfetch,
  `hasPreviousPage`=after-supplied; backward inverts; the backward path fetches
  reversed, slices to `page_size`, then re-reverses to ascending. Correct.
- `connection.py::_keyset_order_state` -- fingerprint binds the cursor to *this*
  order (representation-independent), so replaying an `after:` cursor under a
  different `orderBy:` is rejected at decode. Related `__`-path order columns are
  annotated so end-cursors mint without per-row traversal; nullable/JSON/aggregate
  order entries raise a keyset-specific `GraphQLError` rather than paginating wrong.
- `registry.py::register_with_definition` -- rolls back the type registration if
  definition registration raises (restores prior primary). Transactional.
- `scalars.py::_parse_bigint`/`_serialize_bigint` -- reject `bool` explicitly
  (the `bool` is-a `int` footgun) before the int path.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
