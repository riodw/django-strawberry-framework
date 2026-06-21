# Review: `django_strawberry_framework/mutations/permissions.py`

Status: verified

DRIFT RE-REVIEW. This file was verified earlier in the 0.0.11 cycle, then the
maintainer committed concurrent DRY commit `5065960e` ("Share the permission
async-recourse string between both seams", +15 lines) which added the shared
`_PERMISSION_ASYNC_RECOURSE` constant to this module. Current source re-reviewed
from scratch. The +15 lines are already in HEAD and in the per-cycle baseline
(`git diff 1d8de0c -- …permissions.py` and `git diff HEAD -- …permissions.py`
are both empty), so this drift re-review records zero source edits — shape #5.

## DRY analysis

- None — this module is now the *single source of truth* for both
  permission-contract literals. `_OPERATION_PERMISSION_ACTION`
  (`mutations/permissions.py:37-41`) is the one operation→Django-action map, and
  the `5065960e` commit moved `_PERMISSION_ASYNC_RECOURSE`
  (`mutations/permissions.py:52-56`) here precisely to dedupe a byte-identical
  inline copy that previously lived in both `mutations/resolvers.py`
  (`_authorize_or_raise`) and `mutations/sets.py`
  (`DjangoMutation.check_permission`). Both seams now import it
  (`mutations/resolvers.py:96` → consumed at `:1026`; `mutations/sets.py:65` →
  consumed at `:564`). The DRY shape this file would otherwise be a candidate for
  has already been realized by the commit under review; there is no further
  consolidation to extract here.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** `has_permission` reuses the read-side request
  resolver `utils/permissions.py::request_from_info`
  (`mutations/permissions.py:30,94`) so user resolution stays single-sited across
  read and write seams. The async-coroutine guard is *not* hand-rolled here:
  both consuming seams route the shared `_PERMISSION_ASYNC_RECOURSE` through the
  canonical `utils/querysets.py::reject_async_in_sync_context`
  (`utils/querysets.py:58-91`), which owns the `inspect.iscoroutine` check, the
  `value.close()`, and the `SyncMisuseError` message template — so neither the
  guard logic nor the message prefix can drift across the three sync seams
  (`get_queryset`, `check_permission`, `has_permission`).
- **New helpers considered.** None needed. The two module-level literals are now
  each single-sited and imported by their consumers; extracting anything further
  (e.g. the `f"{app_label}.{action}_{model_name}"` codename format) would create
  a one-caller indirection with no second call site to justify it — Django's
  codename scheme is referenced by the adjacent comment, not duplicated as logic.
- **Duplication risk in the current file.** None. The `5065960e` commit removed
  the only duplication risk (the inline recourse-string copies in `resolvers.py`
  and `sets.py`); a grep for the recourse text now hits only
  `mutations/permissions.py:53-54`. The other `cannot await an async …` strings
  at `resolvers.py:106` and `querysets.py:145` are the distinct *`get_queryset`*
  recourse, not copies of this permission recourse — correctly separate.

### Other positives

- **No permission bypass introduced by `5065960e`.** Verified end to end:
  - `mutations/resolvers.py::_authorize_or_raise` (`:1021-1031`) wraps
    `mutation_cls().check_permission(...)` in `reject_async_in_sync_context(...,
    recourse=_PERMISSION_ASYNC_RECOURSE)`. A coroutine return is closed and
    raised as `SyncMisuseError` *before* the `if not allowed` branch, so an
    `async def check_permission` can never reach the truthy-coroutine path that
    would silently allow.
  - `mutations/sets.py::DjangoMutation.check_permission` (`:551-568`) wraps each
    `permission_class().has_permission(...)` in the same guard with the same
    shared recourse; an `async def has_permission` entry is rejected one level
    down before the `if not allowed: return False` branch.
  - The guard (`utils/querysets.py:86-90`) raises on `inspect.iscoroutine(value)`
    unconditionally and only returns the original value otherwise — there is no
    code path where a coroutine is coerced to `True`/allow. The fail-closed
    semantics of `has_permission` itself are unchanged: `user is None →
    False` (`permissions.py:96-97`), and the default delegates to
    `user.has_perm(codename)` so an anonymous / unauthenticated user is denied.
- **Shared recourse string is correct and accurate.** The wording
  (`permissions.py:52-56`) names the real recourse — "redefine has_permission /
  check_permission as a sync method returning a bool" — and matches the contract
  both seams enforce. The final raised message reads
  `"{owner}.{method} returned a coroutine in a sync {context} context. {recourse}"`
  (`utils/querysets.py:89`), so each seam names its own offending hook while the
  shared tail stays identical.
- **Module placement of the constant is the right home.** `sets.py` already
  imported `DjangoModelPermission` from this leaf module (`sets.py:65`), and
  `resolvers.py` already imported from it, so hoisting the constant here adds no
  new import edge and introduces no circular-import risk — `permissions.py`
  imports only `..utils.permissions` (one local edge) and `typing`.
- **Contract docstrings stay accurate.** The module / class / method docstrings
  still correctly describe write-authorization as a first-class contract
  *separate* from `get_queryset` visibility, the `create→add / update→change /
  delete→delete` mapping, and the anonymous-denied safe default — all consistent
  with `_OPERATION_PERMISSION_ACTION` and `has_permission`'s body.
- **GLOSSARY in sync.** `docs/GLOSSARY.md` `#djangomodelpermission` (lines
  376-388) accurately documents the `add`/`change`/`delete` mapping, the
  `[DjangoModelPermission]` safe default vs explicit-empty `[]` AllowAny opt-out,
  the top-level `GraphQLError` (not `FieldError`) denial surface, and the
  must-be-synchronous-or-`SyncMisuseError` rule. No drift on any documented
  public-contract symbol. The two private constants
  (`_OPERATION_PERMISSION_ACTION`, `_PERMISSION_ASYNC_RECOURSE`) carry no GLOSSARY
  entry — correct, both are `_`-prefixed internals.

### Summary

Clean drift re-review of a security-sensitive write-authorization surface. The
maintainer's concurrent DRY change (`5065960e`) is correct: it moves the
async-recourse string to this leaf permission module and imports it into both
the `resolvers._authorize_or_raise` and `sets.DjangoMutation.check_permission`
seams, eliminating a byte-identical inline duplicate while keeping the wording
single-sourced. The coroutine-bypass guard remains the canonical
`reject_async_in_sync_context` helper, which closes the orphaned coroutine and
raises `SyncMisuseError` before any truthy-coroutine path could allow — so **no
permission bypass is introduced**, and the fail-closed semantics
(`user is None → False`, anonymous denied) are intact. `permissions.py` itself
is byte-identical against both the per-cycle baseline and HEAD, no High / no
behavior-changing Medium, no findings — shape #5 (no-source-edit cycle).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; `289 files left unchanged`.
- `uv run ruff check --fix .` — pass; `All checks passed!`.

### Notes for Worker 3
- Drift re-review of `5065960e` (shared `_PERMISSION_ASYNC_RECOURSE` constant).
  Verified the constant has exactly two cross-module consumers
  (`resolvers.py:1026`, `sets.py:564`), both routed through
  `utils/querysets.py::reject_async_in_sync_context`, which closes any coroutine
  and raises `SyncMisuseError` before any allow path — no permission bypass.
- `permissions.py` is empty-diff vs baseline `1d8de0c` AND vs HEAD; the +15
  lines are cumulative-in-HEAD, not a pending edit.
- All severities `None.`; the single DRY bullet is `None —` (the module is now
  the single source of truth; the consolidation was the commit under review).
- No GLOSSARY-only fix in scope: `#djangomodelpermission` (GLOSSARY:376-388) is
  accurate and in sync; private constants carry no entry (correct).
- Out of scope but noted: an unrelated uncommitted edit exists in
  `mutations/sets.py` (the sibling RE-OPENED item's prior verified comment fix
  per plan line 111); not touched here.

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment or docstring
changes needed — the module / class / method docstrings and the two constant
comments accurately describe current behavior, and the recourse-string comment
(`permissions.py:43-51`) correctly documents the dual-seam single-source intent
of `5065960e`.

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted —
no source edit this cycle (zero tracked-file edits). Internal DRY refactor is
already committed by the maintainer (`5065960e`); CHANGELOG updates are
maintainer-driven and the active plan (`docs/review/review-0_0_11.md`) records no
changelog task for this item, per AGENTS.md ("Do not update CHANGELOG.md unless
explicitly instructed").

---

## Verification (Worker 3)

DRIFT RE-VERIFICATION of a security-sensitive write-authorization leaf, shape #5
(no-source-edit). Verified with security rigor: a permission bypass would be a High.

### Logic verification outcome

All High / Medium / Low are `None.` — independently confirmed genuine, not lazy:

- **Zero-edit proof (two ways).** `git diff 891e03ba… -- …/mutations/permissions.py`
  empty AND `git diff HEAD -- …/mutations/permissions.py` empty. The owned-paths
  `--stat` (`django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md`)
  vs baseline is **fully clean** this run — no #33 dirt, no sibling hunks to
  attribute. The +15 `5065960e` lines are cumulative-in-HEAD, not a pending edit.
- **Shared recourse single-sourced.** `grep -rn _PERMISSION_ASYNC_RECOURSE
  django_strawberry_framework/` returns exactly 5 hits: the definition
  (`permissions.py:52`) + exactly the two import seams (`resolvers.py:96`,
  `sets.py:65`) + their two consumption sites (`resolvers.py:1026`,
  `sets.py:564`). No third consumer; no inline copy survives anywhere.
- **No bypass at seam 1 (`resolvers.py::_authorize_or_raise`, :1021-1031).** The
  hook call `mutation_cls().check_permission(...)` is the FIRST positional arg to
  `reject_async_in_sync_context(...)`, so the guard evaluates the coroutine-check
  before the `if not allowed:` branch (:1028) is ever reached. An `async def
  check_permission` override is `.close()`d and raised as `SyncMisuseError`, never
  coerced truthy → allow.
- **No bypass at seam 2 (`sets.py::DjangoMutation.check_permission`, :551-568).**
  Same wrapping: each `permission_class().has_permission(...)` is the wrapped arg;
  guard fires before `if not allowed: return False` (:566-567). An `async def
  has_permission` entry is rejected one level down before the deny branch.
- **Guard fails closed (`utils/querysets.py::reject_async_in_sync_context`,
  :86-91).** `if inspect.iscoroutine(value): value.close(); raise SyncMisuseError`
  unconditionally; otherwise returns `value` unchanged. No path coerces a
  coroutine to True/allow. Message template
  `"{owner}.{method} returned a coroutine in a sync {context} context. {recourse}"`
  (:89) keeps the shared tail identical while each seam names its own hook.
- **Leaf fail-closed semantics intact (`permissions.py:94-101`).** `user is None →
  return False` (:96-97). The ONLY True-producer is `bool(user.has_perm(codename))`
  (:101), passed a STRING codename with no object arg → pure model-perm check, so
  an anonymous / unauthenticated user (no perms) is denied. Unknown `operation` →
  `KeyError` at `_OPERATION_PERMISSION_ACTION[operation]` (:99); unresolved model →
  `AttributeError` (:98): both fail LOUD, never silent-allow.
- **Test coverage matches the risk.** Both no-bypass seams are pinned by name in
  `tests/mutations/test_permissions.py`:
  `test_async_has_permission_is_rejected_not_bypassed` (:389, sets.py seam),
  `test_async_check_permission_override_is_rejected_not_bypassed` (:424, resolvers
  seam). Fail-closed pinned by `test_anonymous_user_is_denied` (:90) +
  `test_anonymous_create_denied_top_level_error_no_write` (:215). Verb-map +
  per-operation isolation pinned (:90-132). No pytest run needed — no new test
  introduced, and the no-bypass behavior is already named-test-pinned.

### DRY findings disposition

Single DRY bullet is the justified `None —` — confirmed correct. `5065960e` was
itself the DRY consolidation: the byte-identical inline recourse strings that
previously lived in both `resolvers.py` and `sets.py` are gone (grep proves the
text now resolves only to `permissions.py:52-56`). This module is the single
source of truth for both permission-contract literals; no further consolidation
to extract. The constant's home here adds no new import edge (both seams already
imported from this leaf — `sets.py:65` also pulls `DjangoModelPermission`), so no
circular-import risk.

### Temp test verification

- None used. The no-bypass behavior is already pinned by the two named tests
  above; an independent source read of both seams' dispatch ordering plus the
  guard body was sufficient. No suspicion required a temp test.

### Changelog disposition (verified)

`git diff -- CHANGELOG.md` empty. "Not warranted" cites BOTH AGENTS.md ("Do not
update CHANGELOG.md unless explicitly instructed") AND the active plan's silence
on a changelog task for this item — both present. The "internal-only" framing is
honest: zero source edits this cycle and the `5065960e` DRY move is internal
(the recourse string is a private `_`-prefixed constant, not a public-API
surface). Correct state.

### GLOSSARY

`#djangomodelpermission` (GLOSSARY:376-388) read accurate vs live source: verb
map (`create→add` / `update→change` / `delete→delete`), anonymous-denied safe
default, can-view ≠ can-write separation, top-level `GraphQLError` (not
`FieldError`) denial surface, unset→`[DjangoModelPermission]` vs explicit
`[]`-AllowAny opt-out, and the must-be-synchronous-or-`SyncMisuseError` rule. No
drift. Both private constants (`_OPERATION_PERMISSION_ACTION`,
`_PERMISSION_ASYNC_RECOURSE`) correctly carry no GLOSSARY entry (`_`-prefixed
internals). No GLOSSARY-only fix in scope.

### Validation

- `uv run ruff format --check …/permissions.py` — `1 file already formatted`.
- `uv run ruff check …/permissions.py` — `All checks passed!`.

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the
re-opened `mutations/permissions.py` checkbox `[x]` in `docs/review/review-0_0_11.md`.
