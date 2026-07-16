# DRY review: `django_strawberry_framework/auth/queries.py`

Status: verified

## System trace

`auth/queries.py` is the read-side half of the spec-040 session-auth surface: the
`current_user()` query-field factory, its resolver body `_current_user_resolve_body`, and the
`CurrentUserAlias` bind-materialized return-type namespace (the `make_input_namespace` trio +
its pre-bind `register_subsystem_clear` row). It owns exactly three things:

- **The `me` field factory** — `current_user()` declares the fixed `CurrentUser` permission
  holder via `auth/mutations.py::_declare_fixed_auth_surface` and builds the field via
  `auth/mutations.py::_make_auth_field`, both imported directly (never re-implemented). The
  factory itself adds nothing beyond wiring: no arguments, the lazy `CurrentUserAlias` return
  annotation.
- **The nullable-actor resolver body** — `_current_user_resolve_body` resolves the request
  (`utils/permissions.py::request_from_info`), computes `actor = user if (user is not None and
  user.is_authenticated) else None`, fires the permission gate with `instance=actor` via
  `mutations/resolvers.py::authorize_or_raise` (function-local import to avoid a cycle), and
  returns the actor directly — no `get_queryset` re-run, no re-fetch.
- **The `CurrentUserAlias` namespace** — the one auth-owned `make_input_namespace` consumer:
  `materialize_current_user_alias` pins the resolved user primary as this module's own
  `CurrentUserAlias` global (read by `bind_auth_mutations()` in `auth/mutations.py`);
  `clear_current_user_alias_namespace` is registered as a `before_bind=True` subsystem clear so
  the ledger is empty before every re-materialize.

Connected owners traced, not just named: `auth/mutations.py` (`_AUTH_FAMILY_LABEL`,
`_declare_fixed_auth_surface`, `_make_auth_field`, `_resolve_auth_async`,
`_logout_resolve_body`, `bind_auth_mutations()`'s current-user arm, which reaches back into this
module via a function-local import for `CURRENT_USER_ALIAS_NAME` /
`materialize_current_user_alias`); `mutations/fields.py` (`_lazy_ref`,
`build_lazy_field_signature`, `DjangoMutationField` — the same lazy-ref + signature-injection
machinery `login_mutation` / `logout_mutation` use); `mutations/resolvers.py`
(`authorize_or_raise`, `run_in_one_sync_boundary` via `_make_auth_field`'s dispatcher);
`utils/permissions.py::request_from_info`; `utils/inputs.py::make_input_namespace`
(`materialize_generated_input_class` under the hood); `registry.py::register_subsystem_clear`;
`mutations/permissions.py::DjangoModelPermission.has_permission` (a structurally similar
`getattr(request, "user", None)` read, different responsibility — see Verification);
`tests/auth/test_queries.py`; `examples/fakeshop/apps/accounts/schema.py`;
`examples/fakeshop/test_query/test_auth_api.py`.

## Verification

- **Item-scoped diff was empty at review start.** `git diff HEAD -- django_strawberry_framework/auth/queries.py`
  and `git status --short` both returned nothing before this review's edit (`ITEM_BASELINE` per
  the assignment — `git stash create` was empty, working tree clean vs `HEAD`).
- **The factory + field-construction path is already fully reused by call, not by copy.**
  `_declare_fixed_auth_surface`, `_make_auth_field`, `_lazy_ref`, and
  `build_lazy_field_signature` are imported and called directly from `auth/mutations.py` /
  `mutations/fields.py` — confirmed by reading each definition, not by name similarity. There is
  no parallel field-construction or declaration-ledger logic in this file.
- **The alias namespace is the correct, singular use of `make_input_namespace` for this
  responsibility.** Grepped `make_input_namespace` package-wide: `mutations/inputs.py`,
  `forms/inputs.py`, `rest_framework/inputs.py`, and this module each call it exactly once, for a
  distinct materialized-class ledger (mutation payloads, form-input classes,
  serializer-input classes, and the `CurrentUserAlias` return-type alias respectively). These are
  four *instances* of one shared primitive, not four re-implementations of it — the primitive
  itself is already single-sited in `utils/inputs.py`. No duplication.

Candidates searched and rejected:

1. **The per-module `..._MODULE_PATH` string-literal constant.** `AUTH_QUERIES_MODULE_PATH =
   "django_strawberry_framework.auth.queries"` here structurally mirrors
   `mutations/inputs.py::INPUTS_MODULE_PATH`, `orders/inputs.py::INPUTS_MODULE_PATH`,
   `filters/inputs.py::INPUTS_MODULE_PATH`, `forms/inputs.py::INPUTS_MODULE_PATH`, and
   `rest_framework/inputs.py::SERIALIZER_INPUTS_MODULE_PATH` — six modules, each hand-typing its
   *own* fully-qualified dotted path as a literal for `strawberry.lazy(module_path)` /
   `materialize_generated_input_class`'s `sys.modules[module_path]` lookup. This is not one rule
   represented six times; it is six modules independently stating "this is my own path", which
   Python has no generic self-reference for other than the already-available `__name__` (which
   none of the six currently uses). Replacing the literal with `__name__` at each definition site
   would be a nice small hardening, but it is a *pattern* applied identically at six independent
   sites, not a shared invariant with one true owner — there is no single constant that could
   serve all six modules, and a wrong literal fails loudly and immediately at
   `sys.modules[module_path]` (a `KeyError`) rather than drifting silently. Fixing only this
   target's copy would leave five siblings inconsistent for no shared-ownership reason; this is
   better raised as a whole-package hygiene note for the project integration pass than
   implemented as a single-file consolidation. Not touched here.
2. **`_current_user_resolve_body`'s `getattr(request, "user", None)` read vs
   `mutations/permissions.py::DjangoModelPermission.has_permission`'s identical-looking read.**
   Read both bodies directly: `DjangoModelPermission` branches only on `user is None` before
   `user.has_perm(...)` (write-permission check); it never reads `.is_authenticated` in code (only
   in a docstring sentence). This module's resolver classifies anonymity via
   `user is not None and user.is_authenticated` to decide the *return value* (nullable actor), a
   different responsibility (row/actor visibility vs write-permission gating) with a different
   change axis. Kept separate — confirmed independently, not inherited from the sibling artifact.
3. **The example app's scattered `user.is_authenticated` reads**
   (`examples/fakeshop/apps/products/fields.py`, `forms.py`). These are consumer-authored resolver
   / form logic demonstrating how a *consumer* implements its own visibility rules; the package
   does not and should not own arbitrary consumer resolver bodies. Out of scope.

### The deferred authenticated-actor idiom (evidence for the `auth/` folder pass)

The verified sibling review of `auth/mutations.py` (`dry-file-auth__mutations.md`) identified and
Worker-2-confirmed a genuine 2-line, 2-site idiom shared between `auth/mutations.py::_logout_resolve_body`
and this file's `_current_user_resolve_body`:

```python
user = getattr(request, "user", None)
# mutations.py (bool form):
ok = bool(user is not None and user.is_authenticated)
# queries.py (actor form):
actor = user if (user is not None and user.is_authenticated) else None
```

Re-verified independently in this review (not inherited as a given): grepped the whole package
for `is_authenticated` and for `getattr(request, "user", None)` — exactly these two production
sites carry the full `getattr(...) then is_authenticated` shape; `DjangoModelPermission` reads
`getattr(request, "user", None)` too but never branches on `is_authenticated` (see rejected
candidate 2 above), so it is not a third site.

**Decision: deferred to the `auth/` folder pass, not consolidated here.** Considered
consolidating now (this file is one of the two sites, and `queries.py` already imports from
`mutations.py`, which would be the natural landing owner). Chose not to, for two concrete
reasons:

- `auth/mutations.py` already completed its full Worker-1/Worker-2 cycle in this DRY pass and is
  marked `verified` with an explicitly confirmed empty diff. Reopening it here to add a shared
  helper would revert a closed, independently-verified item outside its assigned step, for a
  benefit (removing one duplicated 2-line boolean expression) that does not clearly outweigh that
  cost.
- The plan's very next item is the `auth/` folder integration pass
  (`dry-folder-auth.md`, currently unchecked in `dry-0_0_13.md`), whose explicit charter is
  exactly this: "duplicated policy split across modules" visible only across the folder's file
  boundary. That pass can weigh the idiom against the *whole* folder's shape (e.g., whether a
  shared `_authenticated_actor_or_none(request)` belongs in `mutations.py`, this module, or a new
  seam) in one holistic pass instead of a partial fix from a single-file review, consistent with
  `DRY.md`'s "do not optimize for fewer lines" ground rule for a 2-line idiom.

**Flag for the folder pass:** the idiom is real, confirmed at exactly two sites
(`auth/mutations.py::_logout_resolve_body`, `auth/queries.py::_current_user_resolve_body`), and
both return different shapes (bool vs actor) from the same underlying "authenticated actor or
None" primitive — a natural shared owner would return the actor, with the bool site reduced to
`actor is not None`. The folder pass should re-check this trace rather than re-derive it from
scratch.

## Opportunities

None — the field factory and alias-namespace lifecycle are thin, fully-reused compositions over
already-single-sited owners (`_declare_fixed_auth_surface`, `_make_auth_field`, `_lazy_ref`,
`build_lazy_field_signature`, `make_input_namespace`, `register_subsystem_clear`,
`request_from_info`, `authorize_or_raise`). The one real, evidence-backed candidate — the
authenticated-actor idiom shared with `auth/mutations.py::_logout_resolve_body` — is deliberately
deferred to the `auth/` folder-integration pass (the next plan item) rather than consolidated
from a single-file review, per the reasoning above. The per-module `MODULE_PATH` literal pattern
is a six-site package-wide hygiene note, not a single-file finding, and is likewise left for the
project pass to consider.

## Judgment

Zero-edit review. `auth/queries.py` introduces no duplicated responsibility that a truer owner
inside this file should hold; every reuse obligation is discharged by call against existing
single-sited owners, and the sole genuine cross-file candidate (the actor idiom) is traced here
as evidence and explicitly deferred to the upcoming `auth/` folder pass, which is better
positioned to choose its owner without reopening the already-verified `auth/mutations.py`. Ready
for Worker 2.

## Implementation (Worker 1)

No source changes. The item-scoped diff (`git diff HEAD -- django_strawberry_framework/auth/queries.py`)
remains empty after this review — confirmed by re-running the diff after writing this artifact.
No new tests were added because no behavior changed; the existing `tests/auth/test_queries.py`
and `examples/fakeshop/test_query/test_auth_api.py` suites already exercise every responsibility
traced above (alias namespace lifecycle, injected return typing, surface-keyed bind, permission
gate variants, sync/async resolution, and the live `login` / `logout` / `register` / `me` round
trip). `ruff format` / `ruff check --fix` were not run since no files changed. No changelog entry
warranted (no behavior change). Setting `Status: fix-implemented` per the workflow's "proved
zero-edit" clause — ready for Worker 2's independent verification.

## Independent verification (Worker 2)

**Scoped diff.** Re-ran `git diff HEAD -- django_strawberry_framework/auth/queries.py` and
`git status --short -- django_strawberry_framework/auth/queries.py` myself (`ITEM_BASELINE` per
the assignment is `HEAD`) — both empty. Confirmed zero-edit independently, not inherited from the
artifact's claim.

**Re-traced `current_user` ownership through every connected owner named in the artifact**, reading
each definition rather than trusting the name:

- `auth/mutations.py`: read `_declare_fixed_auth_surface`, `_make_auth_field`,
  `_declare_auth_surface`, `_make_permission_holder`, and `bind_auth_mutations()`'s
  `current_user` arm (the function-local `from .queries import CURRENT_USER_ALIAS_NAME,
  materialize_current_user_alias`, needed because `queries.py` imports `mutations.py` first).
  `current_user()` calls the first two by reference with no re-implementation; the return
  annotation's `CurrentUserAlias` lazy ref is pinned only by the bind arm, confirmed to fire only
  when `"current_user"` is in `by_surface` (the surface-keyed bind the artifact describes).
- `mutations/fields.py`: read `_lazy_ref` and `build_lazy_field_signature` bodies directly —
  confirmed `_lazy_ref` takes `module_path` as a parameter specifically so the auth factories (and
  `queries.py`) can each name their own namespace, and `build_lazy_field_signature` is the same
  builder `DjangoMutationField` uses for the write flavor. No parallel signature-injection code in
  `queries.py`.
- `mutations/permissions.py`: read `DjangoModelPermission.has_permission` in full. It reads
  `getattr(request, "user", None)` and branches only on `user is None` before `user.has_perm(...)`;
  `is_authenticated` appears in that file's docstring only, never in an executed branch. This is
  the load-bearing fact behind rejected candidate 2 and the "exactly two sites" claim for the
  deferred idiom — verified by reading the code, not the artifact's characterization of it.
- `utils/inputs.py::make_input_namespace`: read the body. Confirmed it is the single owner of the
  `(ledger, materialize_fn, clear_fn)` trio shape and that its docstring itself documents the
  pre-spec-039 duplication this already closed (mutation + form inputs hand-mirrored the shape
  before this helper existed). Grepped `make_input_namespace(` package-wide: exactly four call
  sites (`mutations/inputs.py`, `forms/inputs.py`, `rest_framework/inputs.py`, this module),
  matching the artifact's claim exactly — four *instances* of one primitive, not a re-implementation
  anywhere.
- `tests/auth/test_queries.py` and `examples/fakeshop/test_query/test_auth_api.py`: read both in
  full. `tests/auth/test_queries.py` earns the alias-namespace lifecycle, the injected return
  typing, the surface-keyed bind's no-orphan-payload guarantee, both permission-gate variants (the
  AllowAny-null vs gated-`GraphQLError` axes), the async lazy-user-forcing boundary, and the
  visibility-hook non-interaction (`test_me_composes_with_login_in_one_schema_without_visibility_rerun`).
  The live suite earns the real `/graphql/` round trip (`me` after login, `me` null after logout,
  `me` null anonymous, post-reload survival). No gap between what the artifact claims is tested and
  what is actually asserted.

**Independently searched for missed consolidation** beyond the artifact's own candidate list:

- Grepped the whole package for `is_authenticated` and `getattr(request, "user", None)` myself
  (not reusing the artifact's grep output) — confirmed the exact same result set: two production
  sites carry the full `getattr(...)` + `.is_authenticated` shape
  (`auth/mutations.py::_logout_resolve_body`, `auth/queries.py::_current_user_resolve_body`), one
  more site (`DjangoModelPermission`) reads `getattr` but never checks `.is_authenticated`, and the
  example app's `apps/products/fields.py` / `forms.py` carry ten more `is_authenticated` reads that
  are unambiguously consumer resolver/form logic (visibility rules over a `products` app, nothing
  to do with the session-auth surface this package owns). No fourth production site missed.
- Grepped `MODULE_PATH\s*=` and the full `INPUTS_MODULE_PATH`/`SERIALIZER_INPUTS_MODULE_PATH` name
  independently — confirmed exactly six per-module dotted-path literal constants
  (`mutations/inputs.py`, `orders/inputs.py`, `filters/inputs.py`, `forms/inputs.py`,
  `rest_framework/inputs.py`'s `SERIALIZER_INPUTS_MODULE_PATH`, this file's
  `AUTH_QUERIES_MODULE_PATH`), matching the artifact's count precisely, and confirmed none of the
  six use `__name__` today. Agree this is six independent self-references (each module stating its
  own path for its own `strawberry.lazy` / `sys.modules` lookup), not one invariant with a single
  possible owner — a `__name__`-based hardening would be identical, repeated boilerplate at each
  definition site, not a consolidation with a narrower owner. Correctly left to the project pass as
  a hygiene note rather than a single-file fix.
- Read `auth/__init__.py`: confirms the package root does not import `auth/` at all (spec-040
  Decision 3's structural opt-in), so there is no hidden second export surface for `current_user`
  to duplicate.

**Challenged the deferral of the 2-site authenticated-actor idiom directly**, rather than accepting
the sibling artifact's conclusion: read `dry-file-auth__mutations.md` in full. It is marked
`Status: verified` with Worker 2 (myself, in a separate pass) having independently re-confirmed the
same "exactly two sites, `DjangoModelPermission` is not a third" grep result and the same deferral
reasoning. Re-checked the live state of the plan: `dry-folder-auth.md` does not yet exist and the
`auth/` folder-integration item in `dry-0_0_13.md` is still unchecked — so the deferral has a real,
currently-open landing site, not a promise that could be silently dropped. Weighed consolidating
now anyway (this file already imports from `mutations.py`, so the edge exists) against the cost of
reopening an already-verified sibling item outside its assigned step, for a 2-line idiom, against
`DRY.md`'s explicit "do not optimize for fewer lines" ground rule and the cycle rule that "every
revision returns to Worker 1" (reopening `auth/mutations.py` here would require exactly that, off
the assigned target). Agree with the deferral: the folder pass is the correct owner-selection point
because it can weigh the two different return shapes (bool vs actor) against the whole folder's
shape in one pass, and doing it here would only look at half the folder.

**Tried to break the result** with a few angles the artifact does not explicitly rule out:

- Does `_current_user_resolve_body` re-run any queryset visibility hook that could silently change
  behavior between the docstring's claim and the code? Read the body: no `get_queryset` call
  anywhere in `queries.py`; `test_me_composes_with_login_in_one_schema_without_visibility_rerun`
  pins exactly this via a `get_queryset` that hides every row and asserts `me` still returns the
  actor. Holds.
- Does the async dispatch path (`_resolve_auth_async` in `mutations.py`, called from
  `_make_auth_field._resolve`) ever run `_current_user_resolve_body` outside the one
  `sync_to_async` boundary, risking a `SynchronousOnlyOperation` on the lazy user? Read
  `_make_auth_field._resolve` and `_resolve_auth_async`: the whole `resolve_body` (gate + actor
  read) runs inside `run_in_one_sync_boundary` on the async path;
  `test_async_gated_me_forces_the_lazy_user_inside_the_one_sync_boundary` pins this with a
  `SimpleLazyObject` and a recording gate. Holds.
- Could `AUTH_QUERIES_MODULE_PATH` drift from the module's real dotted path (e.g. after a future
  package rename) without the six-site literal pattern's claimed "fails loudly" property actually
  firing? Confirmed `materialize_generated_input_class` (`utils/inputs.py`) does a bare
  `sys.modules[module_path]` lookup with no fallback — a wrong literal raises `KeyError`
  immediately at the first bind, not a silent drift. Holds.

No challenge to any rejected or deferred candidate survives re-inspection; no missed consolidation
opportunity was found against `mutations/`, `utils/`, or the example app; the deferred idiom's
landing site is confirmed still open; and the item-scoped diff is independently confirmed empty.

Status: verified.
