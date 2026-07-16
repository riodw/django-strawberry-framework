# DRY review: `django_strawberry_framework/auth/__init__.py`

Status: verified

## System trace

`auth/__init__.py` is the opt-in consumer entry point for the session-auth
surface (spec-040): it re-exports `login_mutation` / `logout_mutation` /
`register_mutation` from `auth/mutations.py` and `current_user` from
`auth/queries.py`, and nothing else. The docstring states the structural
contract (spec-040 Decision 3): the package root
(`django_strawberry_framework/__init__.py`) deliberately does not import or
re-export this subpackage, so a consumer who never imports
`django_strawberry_framework.auth` never pays the `django.contrib.auth`
import cost. Verified: `django_strawberry_framework/__init__.py` has no
`from .auth import ...` line and no mention of `auth` at all.

Consumers: `examples/fakeshop/apps/accounts/schema.py` imports exactly the
four names in exactly the order the docstring's example shows
(`current_user, login_mutation, logout_mutation, register_mutation`).
`tests/auth/test_mutations.py` and `tests/auth/test_queries.py` import the
same public names for black-box coverage, plus the submodules directly
(`auth.mutations`, `auth.queries`) for white-box coverage of private
declaration-ledger internals - expected, since those internals are
deliberately NOT part of this file's public contract.

Internally, `auth/queries.py` imports three private names directly from
`auth/mutations.py` (`_AUTH_FAMILY_LABEL`, `_declare_fixed_auth_surface`,
`_make_auth_field`) - a direct sibling-to-sibling import that bypasses
`__init__.py` entirely, exactly as `filters/inputs.py` and
`orders/inputs.py` privately share helpers without routing through their
own `__init__.py`. `types/finalizer.py` reaches `bind_auth_mutations` via
`utils/imports.py::loaded_attr("django_strawberry_framework.auth.mutations",
"bind_auth_mutations")` - a direct submodule dotted path, not an attribute
read off this `__init__.py` - so the finalizer's opt-in-preserving guard
(already single-sited per the `loaded_attr` docstring's "DRY review B1"
history) is unaffected by anything in this file.

## Verification

Diff against baseline `715e9758db709dd36fcfc819afb4bcf76ac43be0` for this
file (and every path touched while tracing it) is empty - nothing in this
cycle or a concurrent session has touched the auth surface.

Compared the file's shape against every other subpackage `__init__.py` in
`django_strawberry_framework/` to check whether the "curated public
re-export via explicit imports + `__all__` tuple" pattern is spelled
independently at each site (a real duplication candidate) or is the
package's one deliberate, already-named idiom:

- `extensions/__init__.py` names the shape explicitly: "Eager re-export
  (docstring + explicit re-export + `__all__`, the `utils/__init__.py` /
  `testing/__init__.py` shape)."
- `mutations/__init__.py` / `forms/__init__.py` cross-reference each other
  ("Mirrors the `filters/__init__.py` / `orders/__init__.py` re-export
  idiom").
- `filters/__init__.py`, `orders/__init__.py`, `optimizer/__init__.py`,
  `types/__init__.py`, `utils/__init__.py`, `testing/__init__.py` all use
  the identical three-part shape: docstring explaining what is/isn't
  exported and why, `from .submodule import Name, ...`, and an alphabetical
  `__all__` tuple/list.
- `auth/__init__.py` follows the exact same three-part shape (docstring with
  rationale, direct imports, alphabetical `__all__`) with zero deviation:
  same import style, same alphabetical `__all__` ordering, same "state what
  is deliberately excluded and why" docstring convention the opt-in
  subsystems (`extensions/`, `rest_framework/`) also use for their own
  root-exclusion rationale.

This is Python's own package-export mechanism, not a helper this codebase
implements - there is no function body, validation rule, or lifecycle to
extract into a shared owner. `DRY.md` explicitly warns against optimizing
for fewer lines when the result "obscures ownership... or needs mode flags
to reconcile different rules"; a `build_public_exports(*names)` wrapper
here would do exactly that for zero behavioral gain, while each
`__init__.py`'s docstring already carries the file-specific rationale
(auth's root-exclusion reasoning differs from extensions' or optimizer's,
even though the export *mechanism* is identical).

Checked for content drift between the docstring's worked example and real
call sites: the docstring's `from django_strawberry_framework.auth import
(current_user, login_mutation, logout_mutation, register_mutation)` example
matches `examples/fakeshop/apps/accounts/schema.py`'s actual import
character-for-character (including name order), so the docstring is not a
stale or independently-drifting description of the contract.

Rejected candidate: cross-referencing this file against the sibling
`extensions/__init__.py` "eager re-export... shape" callout, i.e. adding a
line naming `auth/__init__.py` alongside `utils/__init__.py` /
`testing/__init__.py` in that shared-shape sentence. Rejected: the
cross-reference list in `extensions/__init__.py` is already incomplete by
that standard (it also omits `mutations/__init__.py`, `forms/__init__.py`,
`filters/__init__.py`, `orders/__init__.py`, `optimizer/__init__.py`,
`types/__init__.py`, all of which use the identical shape), so this is a
pre-existing, package-wide documentation-completeness question that belongs
to whichever file first named the shape (`extensions/__init__.py`) or to
the project integration pass - not to `auth/__init__.py`, which owns no
part of that cross-reference list and would only be one more inconsistent
partial mention if edited in isolation.

## Opportunities

None - the file is a correctly-conforming instance of the package's one
public-re-export idiom, verified against every sibling subpackage
`__init__.py` and against its only real consumer. The 20 lines encode
exactly one rule (which four names are the auth public surface) with one
authoritative statement (the `__all__` tuple, backed 1:1 by the `from`
imports directly above it) and no parallel representation exists anywhere
else in the repository - `mutations.py` and `queries.py` define the
functions being re-exported, not a second contract for what the auth
public surface is.

## Judgment

Zero-edit review. `auth/__init__.py` is a minimal, non-duplicative instance
of a well-established, self-documenting package-wide convention; the
diff-scoped item is empty and no source, test, or doc change is warranted.

## Independent verification (Worker 2)

Re-ran the scoped diff independently: `git diff 715e9758db709dd36fcfc819afb4bcf76ac43be0`
against `auth/__init__.py`, `auth/mutations.py`, `auth/queries.py`, the root
`__init__.py`, `types/finalizer.py`, every sibling subpackage `__init__.py`
named in the artifact (`extensions/`, `mutations/`, `forms/`, `filters/`,
`orders/`, `optimizer/`, `types/`, `utils/`, `testing/`), and the consumers
(`examples/fakeshop/apps/accounts/schema.py`, `tests/auth/test_mutations.py`,
`tests/auth/test_queries.py`) returns empty. `git status --porcelain` on the
same paths shows only the two auth test files as `M` against `HEAD`
(pre-existing docstring rewording already baked into the baseline commit,
confirmed by diffing `HEAD` against the baseline directly - unrelated to this
cycle) and confirms `auth/__init__.py` itself is untouched. Baseline holds.

Independently re-traced the responsibility rather than trusting the artifact's
description:

- Read `auth/__init__.py`, `auth/mutations.py`, and `auth/queries.py` in full.
  The `__init__.py` re-exports exactly the four names its `__all__` states;
  the import list and `__all__` tuple are 1:1 and alphabetical, matching every
  other curated-re-export sibling.
- Confirmed the root `django_strawberry_framework/__init__.py` has no `auth`
  reference anywhere (import, `__all__`, `_DRF_SOFT_EXPORTS`, docstring) -
  the structural opt-in claim holds.
- Confirmed the sibling-private-import analogy: `filters/sets.py` imports
  `_LOGIC_KEYS` / `_field_specs` directly from `filters/inputs.py`, and
  `orders/sets.py` imports `_field_specs` directly from `orders/inputs.py` -
  both bypass their own `__init__.py` for a private name exactly as
  `auth/queries.py` imports `_AUTH_FAMILY_LABEL` / `_declare_fixed_auth_surface`
  / `_make_auth_field` directly from `auth/mutations.py`. The artifact's
  original prose pointed at `filters/inputs.py` / `orders/inputs.py` as the
  analogy sites rather than `filters/sets.py` / `orders/sets.py` (the inputs
  modules are themselves consumers of `.base`, not producers of a
  sibling-private-import edge) - a citation-precision slip, not a wrong
  claim: the pattern (private sibling-to-sibling imports bypassing a
  subpackage's own `__init__.py`) is real, repeated at least twice elsewhere
  in the tree, and does not change the zero-edit judgment for this file since
  the file itself performs no such import.
- Confirmed `types/finalizer.py` reaches `bind_auth_mutations` through
  `utils/imports.py::loaded_attr("django_strawberry_framework.auth.mutations",
  "bind_auth_mutations")` - a dotted submodule path, never through this
  `__init__.py` - so nothing here participates in that lazy-load contract.
- Read every sibling subpackage `__init__.py` the artifact cites
  (`extensions/`, `utils/`, `testing/`, plus `optimizer/__init__.py`, checked
  independently and not cited in the artifact) and confirmed all use the same
  docstring-rationale + explicit-import + alphabetical-`__all__` shape with
  file-specific rationale text - the mechanism is Python's own import/`__all__`
  system, not a hand-rolled helper, so there is no function body or lifecycle
  rule to extract into one owner.
- Confirmed `rest_framework/__init__.py` is NOT the same three-part shape (it
  has no `__all__` re-export at all; it is a raising-guard-on-import module) -
  the artifact's cross-reference to `rest_framework/` was scoped only to the
  shared "explain the root-exclusion rationale in the docstring" convention,
  not the export shape, and that narrower claim holds.
- Checked `docs/TREE.md`: no subpackage (`filters/`, `forms/`, `mutations/`,
  `optimizer/`, `middleware/commands/`, etc.) lists its own `__init__.py` as a
  separate tree line - the folder-line comment stands in for it uniformly.
  `auth/`'s tree entry follows the identical convention, so the absence of an
  explicit `auth/__init__.py` line is not a project-wide documentation gap
  this file introduces or that Worker 1 missed.
- Grepped for the one literal this file's re-exported functions are keyed
  under (`"AuthMutation"` / `_AUTH_FAMILY_LABEL`) and confirmed it is
  single-sited in `auth/mutations.py` only - no second definition for this
  `__init__.py` to duplicate or launder.
- Tried to break the zero-edit conclusion by looking for a plausible edit
  that would improve the file: a `build_public_exports()` wrapper (rejected
  in the artifact - correctly, since it would hide the alphabetical `__all__`
  /import 1:1 correspondence behind a mode-flag-free but purpose-free
  indirection for a 20-line file); reordering the docstring's worked example
  to match `__all__`'s alphabetical order instead of the mutation-before-query
  grouping it currently uses - rejected on inspection, since the docstring
  order matches the real call site's import order in
  `examples/fakeshop/apps/accounts/schema.py` character-for-character, and
  changing it would make the docstring diverge from its only consumer instead
  of converging with it.
- Confirmed no missed consolidation: this file has no rule, transformation,
  cache, or lifecycle phase of its own to consolidate. Its only content is
  the four-name public surface list, stated once as an `__all__` tuple backed
  1:1 by the imports directly above it - the artifact's "Opportunities: None"
  finding is correct as written.

No challenge to the rejected candidate survives re-inspection: the
`extensions/__init__.py` cross-reference sentence is genuinely incomplete
against six-plus siblings using the identical shape (confirmed independently
by reading `mutations/__init__.py`, `forms/__init__.py`, `filters/__init__.py`,
`orders/__init__.py`, `types/__init__.py` in addition to `optimizer/__init__.py`
above), so fixing it from `auth/__init__.py` alone would still leave an
incomplete list and would be an edit to a file this review does not own.
Correctly left to the project integration pass or to whichever file first
named the shape.

Status: verified.
