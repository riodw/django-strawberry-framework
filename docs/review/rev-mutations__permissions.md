# Review: `django_strawberry_framework/mutations/permissions.py`

Status: verified

## DRY analysis

- None — the file is a single ~26-line class plus one module-level mapping. The
  one cross-surface concern — resolving the request user from `info` — is already
  single-sited in `utils/permissions.py::request_from_info` and reused here
  (`mutations/permissions.py::DjangoModelPermission.has_permission` line 79), the
  same helper the read-side filter/order permission pipelines call, so user
  resolution stays single-sourced across read and write. The operation->action
  map `_OPERATION_PERMISSION_ACTION` (lines 37-41) is the single Decision-15 verb
  table; `mutations/fields.py` and `mutations/inputs.py` carry their own
  `_OPERATION_INPUT_KIND` for a *different* axis (input-type kind, not perm verb),
  so the two tables are not a merge candidate. Model resolution delegates to
  `mutations/sets.py::DjangoMutation._resolve_model` (the form/serializer override
  seam), not re-implemented here. No literal/near-copy left to hoist.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** `request_from_info(info, family_label="DjangoMutation")`
  (`utils/permissions.py::request_from_info`) is the shared read+write request
  resolver — reused verbatim at `mutations/permissions.py:79` so user extraction is
  single-sited across the filter/order `apply` seam and this mutation
  `check_permission` seam. Model resolution defers to
  `mutations/sets.py::DjangoMutation._resolve_model` (line 83), the documented
  override hook the 0.0.12 form / 0.0.13 serializer flavors replace — so all
  flavors authorize through this one default without re-opening base validation.
- **New helpers considered.** A "build the codename" helper was considered and
  rejected — the `f"{app_label}.{action}_{model_name}"` template (line 85) is the
  Django/DRF `DjangoModelPermissions` codename scheme used exactly once; extracting
  it would add indirection with no second call site.
- **Duplication risk in the current file.** The three-entry verb map
  (`_OPERATION_PERMISSION_ACTION`) reads like the `_OPERATION_INPUT_KIND` map in
  `mutations/fields.py` / `mutations/inputs.py`, but they key different axes
  (perm-action verb vs input-type kind) and would diverge under any future
  operation that needed one without the other — intentionally separate, not a
  near-copy.

### Other positives

- **No fall-through to allow.** Every non-authorized path returns `False` or
  raises; the only `True`-producing expression is `bool(user.has_perm(codename))`
  (line 86). There is no `try/except` swallowing an error into an allow, so a
  resolution failure can never silently authorize a write.
- **Anonymous / unauthenticated denied by construction.** `user is None`
  (AuthenticationMiddleware absent, or `request` with no `.user`) returns `False`
  (lines 80-82); an `AnonymousUser` reaches `has_perm` and returns `False` since it
  holds no perms. Both the safe default — pinned by
  `tests/mutations/test_permissions.py::test_anonymous_user_is_denied` and the
  end-to-end `test_anonymous_create_denied_top_level_error_no_write`.
- **Write authz is genuinely distinct from read visibility.** `has_perm(codename)`
  is a model-level perm check passed a string (no object argument), so it consults
  model permissions only — never `get_queryset`. The GLOSSARY can-view != can-write
  contract holds in code; `test_hidden_row_is_not_found_before_auth_signal_no_existence_leak`
  confirms the visibility lookup runs first (hidden row -> not-found, no auth-signal
  leak) and `test_permission_classes_override_deny_blocks_permitted_caller` confirms
  a deny is honored even for a perm-holding caller (no read-visibility fallback).
- **Per-operation verb isolation pinned.** `add` authorizes only `create`,
  `change` only `update`, `delete` only `delete`
  (`test_create_perm_does_not_authorize_update_or_delete` +
  `test_change_and_delete_perms_authorize_their_operations`); the map itself is
  frozen by `test_operation_action_map_is_pinned`.
- **Fail-loud, not bypass, on the two unreachable edges.** An unknown `operation`
  raises `KeyError` on the map lookup (line 84) and an unresolved model raises
  `AttributeError` on `model._meta` (line 85) — both are upstream-validated away
  (operation is one of three verbs and a resolvable model is required at finalize
  per `mutations/sets.py`), and both fail loud rather than silently allowing, which
  is the correct security posture for a write-authz surface.
- **Async-bypass guard lives at the right layer.** This file's `has_permission` is
  sync by design; the coroutine-truthiness bypass (`if not has_permission(...)`
  treating an `async def` deny as ALLOW) is closed one level up in
  `mutations/sets.py::DjangoMutation.check_permission` via `inspect.iscoroutine` ->
  `SyncMisuseError`, pinned by `test_async_has_permission_is_rejected_not_bypassed`
  and `test_async_check_permission_override_is_rejected_not_bypassed`. Correct
  separation — the bypass risk is in the caller's dispatch loop, not in the leaf
  check.
- **Docstrings are accurate and load-bearing.** The module + class + method
  docstrings precisely state the verb map, the anonymous-denied default, the
  read/write separation, and the Slice-2-ships-class / Slice-3-wires-enforcement
  split; none promise behavior the body does not deliver. `del data, instance` with
  the explanatory comment makes the spec-signature-only parameters explicit.

### Summary

`DjangoModelPermission.has_permission` is a tight, correct, security-sound default
write-authorization check: it maps the mutation operation to the Django
`add`/`change`/`delete` model-permission verb, checks `user.has_perm(codename)`,
and denies on every non-authorized path (anonymous, missing user, missing perm)
with no fall-through to allow and no fallback to read visibility. User resolution
and model resolution are both delegated to single-sited seams
(`request_from_info`, `_resolve_model`), and the async-bypass hazard is correctly
handled by the caller in `sets.py`. The file is byte-identical to both the
per-cycle baseline (`d04b7a95`) and HEAD — zero tracked edits this cycle — and the
GLOSSARY/README contract (`DjangoModelPermission` entry, can-view != can-write,
exported from the package root) matches the implementation with no drift. No
High/Medium/Low findings; this is a clean first-review of new write-authz
production code.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; 289 files left unchanged.
- `uv run ruff check --fix .` — pass; all checks passed.

### Notes for Worker 3
- No GLOSSARY-only fix in scope. Grepped `docs/GLOSSARY.md` for all three public
  symbols (`DjangoModelPermission`, `permission_classes`, `check_permission`) plus
  `README.md` / `docs/README.md`: the `DjangoModelPermission` entry (GLOSSARY:376-390)
  and the mutations README paragraph (docs/README.md:123) describe verb map,
  anonymous-denied default, can-view != can-write separation, empty-`[]` AllowAny
  opt-out, sync-only / async-rejected hook, and package-root export — all match the
  implementation; no drift, no edit warranted.
- `git diff d04b7a95...HEAD -- django_strawberry_framework/mutations/permissions.py`
  and `git diff HEAD -- <target>` both empty; file exists at baseline. Genuine
  shape #5 (the spec-036 mutations work landed in HEAD before this cycle's baseline).
- Zero H/M/L findings; nothing forwarded to the folder or project pass.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment/docstring changes. The module, class, and `has_permission` docstrings
plus the `_OPERATION_PERMISSION_ACTION` comment and the `del data, instance` inline
comment are accurate and non-redundant; no stale references, no TODO anchors, no
promises the body does not keep.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted. No source/test/doc edits this cycle (AGENTS.md: update CHANGELOG only
when explicitly instructed; the active plan `docs/review/review-0_0_11.md` defines a
read-only review pass and is silent on changelog edits).

---

## Verification (Worker 3)

### Logic verification outcome

Zero-edit shape #5 confirmed and security-audited with maximum rigor (new write-authz
surface). No source/test edit this cycle:
- `git diff d04b7a95 -- django_strawberry_framework/mutations/permissions.py` empty.
- `git diff HEAD -- django_strawberry_framework/mutations/permissions.py` empty.
- File exists at baseline (`git cat-file -e` ok) — genuine #5, not a new-file artifact gap.
- `git diff HEAD -- CHANGELOG.md` empty (matches "Not warranted").
- Owned-paths `--stat` vs baseline dirt: only `utils/relations.py` (1 line) — a
  non-target sibling (owned by `rev-utils__relations.md`), out of scope per diff-scoping;
  not a rejection trigger.

Independent security audit of `DjangoModelPermission.has_permission` — all `None.`
severities confirmed genuine, no path falls through to allow:
- **No fall-through to allow.** The single `True`-producing expression is
  `bool(user.has_perm(codename))` (line 86); `user is None -> False` (lines 81-82). No
  `try/except` swallows a resolution failure into an allow.
  (`test_user_lacking_perm_is_denied`, `test_user_with_add_perm_allowed_for_create`.)
- **Anonymous / unauthenticated denied.** `user is None -> False`; an `AnonymousUser`
  reaches `has_perm` and returns `False` (holds no perms). Pinned by
  `test_anonymous_user_is_denied` + `test_anonymous_create_denied_top_level_error_no_write`.
- **Write authz never consults `get_queryset`.** `has_perm(codename)` is passed a string
  only (no object arg) — a pure model-level perm check, never row visibility. The
  can-view != can-write contract holds in code; pinned by
  `test_hidden_row_is_not_found_before_auth_signal_no_existence_leak` (visibility lookup
  first; hidden row -> not-found, no auth-signal leak) and
  `test_permission_classes_override_deny_blocks_permitted_caller` (deny honored over a
  perm-holder, no read-visibility fallback).
- **Per-operation verb mapping correct.** `_OPERATION_PERMISSION_ACTION` =
  `{create:add, update:change, delete:delete}`, frozen by
  `test_operation_action_map_is_pinned`; isolation pinned by
  `test_create_perm_does_not_authorize_update_or_delete` +
  `test_change_and_delete_perms_authorize_their_operations`.
- **Unreachable edges fail loud, not silent-allow.** Unknown `operation` -> `KeyError`
  on the map lookup (line 84); unresolved model -> `AttributeError` on `model._meta`
  (line 85). Both upstream-validated (`sets.py::_validate_mutation_meta` pins operation
  to the three verbs and requires a resolvable model), and both fail loud — the correct
  posture for a write-authz leaf.
- **Async-coroutine bypass guard lives one layer up in `sets.py::check_permission`.**
  This file's `has_permission` is sync by design; the truthy-coroutine bypass is closed
  at `sets.py` (lines 557-564): `inspect.iscoroutine(allowed)` -> `allowed.close()` +
  `raise SyncMisuseError`. Pinned by `test_async_has_permission_is_rejected_not_bypassed`
  (an async `has_permission` deny raises, no row written) and
  `test_async_check_permission_override_is_rejected_not_bypassed` (async
  `check_permission` override caught one level up). Correct separation — the bypass risk
  is in the caller's dispatch loop, not the leaf check.
- **User resolution single-sited.** `request_from_info(info, family_label="DjangoMutation")`
  (line 79) returns the request and never an allow signal: it resolves
  `info.context.request` / bare `HttpRequest` or raises `ConfigurationError`; the leaf
  then reads `getattr(request, "user", None)`. Shared verbatim with the read-side
  filter/order seam — confirmed family-neutral message (no `.apply` suffix).

### GLOSSARY (#4-vs-#5 gate)

Genuine #5, not a missed #4. The `DjangoModelPermission` entry (GLOSSARY:380) reads
accurate vs live source: verb map (`add`/`change`/`delete`), anonymous-denied safe
default, can-view != can-write separation, top-level `GraphQLError` on denial (not a
`FieldError` entry), unset -> `[DjangoModelPermission]` default, explicit empty `[]`
AllowAny opt-out, and the sync-only / async-rejected-`SyncMisuseError` hook contract —
all match `permissions.py` + `sets.py::check_permission`. The `FieldError`-envelope
(GLOSSARY:499) and `DjangoMutation` (GLOSSARY:388) cross-references to it are consistent.
No drift; no GLOSSARY-only fix owed.

### DRY findings disposition

DRY analysis `- None` confirmed genuine: user resolution single-sited in
`utils/permissions.py::request_from_info` (reused at line 79), model resolution delegated
to `sets.py::DjangoMutation._resolve_model` (line 83 — the 0.0.12/0.0.13 flavor seam),
the verb map is the single Decision-15 table (distinct axis from
`_OPERATION_INPUT_KIND`). No literal/near-copy to hoist; nothing forwarded to folder or
project pass.

### Temp test verification

None — no behavior suspicion required a temp test; the existing
`tests/mutations/test_permissions.py` suite (Slice 2 class-behavior + Slice 3
enforcement) pins every audited path.

### Validation

`uv run ruff format --check` (1 file already formatted) + `uv run ruff check` (all checks
passed) on the target. Pytest not run preemptively (no test introduced; existing tests
read directly and grep-confirmed by name).

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the
`mutations/permissions.py` checkbox in `docs/review/review-0_0_11.md`.
