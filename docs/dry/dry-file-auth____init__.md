# DRY review: `django_strawberry_framework/auth/__init__.py`

Status: verified

## System trace

The target is the opt-in public import surface of the session-auth subsystem (spec-040
Decision 3). It owns exactly two things and nothing else:

- the four-name export list — `current_user` (from `.queries`) and `login_mutation` /
  `logout_mutation` / `register_mutation` (from `.mutations`), eagerly imported and pinned
  in `__all__`;
- the structural opt-in invariant: the package root deliberately never imports or
  re-exports this module, so importing `django_strawberry_framework.auth` is the only act
  that loads the subsystem (and with it the declaration-ledger and alias-namespace
  `register_subsystem_clear` rows those submodules register at import time).

Consumers traced end to end: production code reaches the factories only through this
surface — `examples/fakeshop/apps/accounts/schema.py` is the sole production importer
(all four names, wired onto the accounts schema). Tests import the public names through
the surface (`tests/auth/test_mutations.py`, `tests/auth/test_queries.py`,
`tests/test_routers.py`) and deep-import internals (`auth.mutations`,
`auth.sessions._SCOPE_LOCK_KEY`) for private state, which is testing, not a second public
path. `types/finalizer.py::loaded_attr("django_strawberry_framework.auth.mutations",
"bind_auth_mutations")` bypasses this package `__init__` on purpose: an already-loaded-only
probe fetching the private bind hook, so an auth-free process never pays the import — a
different contract from the public factory surface, not a parallel enumeration of it.
Prose media describing the surface: `docs/GLOSSARY.md` (export-path note plus the Auth
mutations entry), `README.md`, `docs/README.md`, `CHANGELOG.md` (`0.0.13` row),
spec-040, and the two `docs/TREE.md` subtree views (which omit `__init__.py` rows for
every package, per that document's convention). Lockstep surface: renaming or adding any
factory moves its defining submodule plus this file's import line and `__all__` entry as
one unit; nothing else in code spells the list.

## Verification

Axis discharge:

1. **Cross-flavor policy mirroring** — searched the package's three coexisting
   export-policy shapes: eager root re-exports with a pinned `__all__`
   (`django_strawberry_framework/__init__.py`, pinned by
   `tests/base/test_init.py::test_public_api_surface_is_pinned`), lazy PEP 562 soft
   exports (`_DRF_SOFT_EXPORTS` resolved by name through `require_drf()`), and deliberate
   non-re-export submodule paths (`auth`, `testing.relay`, private `auth.sessions`). These
   encode different dependency economics (always-safe hard deps, guard-gated soft deps,
   structural opt-in), not one policy spelled thrice — each changes for its own reason,
   and no auth factory exists in more than one flavor. Ruled not duplication.
2. **Sync and async twins** — the target carries no executable resolver code; every
   sync/async pair of the subsystem lives behind the single `_make_auth_field` dispatch
   seam in `auth/mutations.py` (its own review unit). A re-export is colorless. Ruled
   inapplicable.
3. **Derived rather than repeated knowledge** — `__all__` hand-lists the same four names
   the two import lines bind: the minimal Python idiom for an eager re-export; deriving
   `__all__` from module globals would delete zero forced sites elsewhere while hiding the
   surface from static readers. Module-path literals checked:
   `"django_strawberry_framework.auth.queries"` is a named constant in `auth/queries.py`
   (consumed by `make_input_namespace`), while the sibling path string sits inline in the
   finalizer's `loaded_attr` probe — each spelled once, consumed once, by disjoint
   owners; hoisting both into a shared constants module would force the finalizer to
   import from `auth`, violating Decision 3's opt-in. Rejected. No fact is derived twice.
4. **Inverse and round-trip pairs** — a pure re-export has no encode/decode half. The
   subsystem's real paired grammars (transport classification vs capability answers;
   `actor_transition` lease vs consumer revalidation checkpoints) live in
   `auth/sessions.py`, `utils/sessions.py`, and `consumers.py`, each with its own review
   pass, and none of their knowledge passes through this file. Ruled inapplicable here.
5. **Contracts restated in another medium** — the four-name surface is enumerated in this
   file (import + `__all__`), the fakeshop schema import block, three test modules'
   imports, GLOSSARY (twice), README, docs/README, CHANGELOG, spec-040, and TREE subtree
   rows. Of these only this file states the export contract; every other site either
   consumes the names (usage is what a public surface exists for, not a restatement of
   it) or describes them in hand-maintained prose (no generated-artifact medium exists
   for auth). Notably nothing in code duplicates the list: no test pins
   `auth.__all__` (unlike the root `__all__`), and grep finds no second module naming all
   four symbols together.

Single-edit-site counts:

- *Posited change: add a fifth factory* (e.g. `change_password_mutation()`): forced edits
  are the def site in `auth/mutations.py` plus one import line and one `__all__` entry in
  this file — within the export layer the count is 1 aggregation site; no second code
  location re-spells the auth export list.
- *Posited change: rename `current_user()`*: def site + this file's import + `__all__`
  entry + genuine usage sites (fakeshop schema lines binding `me`, test imports). Usage
  sites move under any conceivable design; the re-export layer itself contributes exactly
  one site. Count came back 1 for the layer.
- *Rejected experiment: funnel tests through the surface only* — the deep imports reach
  private fixtures (`_SCOPE_LOCK_KEY`, ledger internals) that the surface intentionally
  does not export; forcing them through `auth.__all__` would widen the public contract to
  serve tests. Independence, not duplication.

Strongest rejected candidates: the finalizer's inline `"django_strawberry_framework.auth.mutations"`
literal vs `AUTH_QUERIES_MODULE_PATH` (disjoint owners, once each; consolidation would
break the opt-in import direction); the name collision between `auth.register_mutation()`
(the public factory) and `mutations/sets.py::register_mutation` (a ledger-register
method) — same token, unrelated contracts, already disambiguated by the
`record_mutation_declaration` alias at import; the missing `auth.__all__` pin test
(an asymmetry vs the pinned root surface, but adding one is new coverage, not
de-duplication, so out of scope for a DRY cycle).

## Opportunities

None — the target is a two-line aggregation whose only stated rule (four names, opt-in
structural import) has exactly one implementation and one aggregation site. Every posited
change to the surface came back at count 1 for the export layer; the apparent parallels
(the root `__init__` export machinery, the finalizer's `loaded_attr` probe, the docs
prose) were each disproved as holding a different contract — hard-dep exports, a
private already-loaded bind hook, and description respectively. The subsystem's real
duplication risks (sync/async bodies, transport grammar, anonymity definition) are
consolidated inside `auth/mutations.py` / `auth/sessions.py`, not across this surface.

## Independent verification (Worker 2)

Scoped diff against the cycle baseline `bcf3e28` is empty for
`django_strawberry_framework/auth/__init__.py` (zero-edit result confirmed at the file level).

Independently re-traced and confirmed:

- The target is exactly the two-line aggregation + four-name `__all__`; the three factories live
  at `auth/mutations.py::login_mutation`, `::logout_mutation`, `::register_mutation` (847 / 876 /
  1135) and `current_user` in `auth/queries.py`. The package root names `auth` nowhere, and a
  package-wide grep finds no always-loaded module importing `.auth` — the only core touchpoint is
  the finalizer's probe, which `utils/imports.py::loaded_attr` confirms is already-loaded-only
  (`sys.modules.get`, never imports). The opt-in invariant genuinely holds structurally.
- Deep-import challenge: every deep path (`tests/auth/*` privates `_auth_declarations`,
  `bind_auth_mutations`, `_SCOPE_LOCK_KEY`, `_register_decode_step`/`_register_write_step`;
  `tests/auth/conftest.py`; the finalizer probe) fetches internals under a different contract;
  no site imports any of the four public names through the deep path. The only other code
  enumeration of auth module paths, `tests/test_routers.py::_AUTH_SUBSYSTEM_MODULES`, asserts the
  import boundary (modules NOT in `sys.modules`) — it lists submodule paths, not exported symbols,
  and does not move when a factory is added: an assertion of this file's invariant, not a second
  statement of its export rule.
- Re-probed rejected candidates: (1) finalizer literal `"django_strawberry_framework.auth.mutations"`
  vs `AUTH_QUERIES_MODULE_PATH` — two different strings, each spelled once by disjoint owners with
  no shared change axis; hoisting adds a location without removing duplication. (2) The
  `register_mutation` collision is real but unrelated-contract: the ledger alias is a bound-method
  name at `mutations/sets.py #"register_mutation = _mutation_declaration_registry.register"`,
  already disambiguated by the `record_mutation_declaration` import alias. (3) Confirmed nothing
  pins `auth.__all__` (only the root pin test and a permissions-`__all__` assertion exist) — new
  coverage, not dedup.
- Axis discharge re-judged against the real surface: axis 1's three shapes verified in source
  (root eager exports + pinned `__all__`; root PEP 562 `_DRF_SOFT_EXPORTS` through
  `require_drf()`; deliberate non-re-export); axis 5 verified that GLOSSARY carries prose only,
  TREE.md omits `__init__.py` rows per convention, and no generated artifact enumerates auth.
- Own recount (posited change: rename `logout_mutation` → `end_session_mutation`): forces the def
  site, ONE aggregation location (this file's import line + `__all__` entry), and consumer sites
  (`examples/fakeshop/apps/accounts/schema.py`, test imports) that move under any design. No
  second location re-spells the export list; count of one holds.

Verdict: zero-edit result proved; search quality is behavioral, not textual. Status set to
`verified`.

## Judgment

This file is the boundary where the auth subsystem's single-sourcing is declared, not
repeated: the four-name list exists here once, the opt-in invariant is enforced by
absence (root non-import) rather than by a second mechanism, and the one deliberate
bypass (the finalizer's loaded-module probe) fetches a private hook under a documented
different contract. Zero-edit result, proved: all five axes discharged, with two posited
changes returning single-edit-site counts of 1.
