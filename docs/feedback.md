# Dirty-tree commit plan

## Problem statement

The working tree contains 129 dirty files: 69 tracked modifications and 60 untracked DRY reports.
The tracked diff is approximately 1,946 insertions and 1,383 deletions across shared utilities,
filters, orders, forms, mutations, authentication, DRF serializers, optimizer planning,
management commands, generated documentation, and the fakeshop database. These changes must be
committed as dependency-ordered, reviewable units rather than one DRY mega-commit.

## Global commit rules

- Stay on the current branch. Do not create or switch branches.
- Stage explicit paths and, where noted, explicit hunks. Never use `git add -A`; the checkout is
  shared with concurrent work.
- Before every commit, inspect `git diff --cached --stat` and `git diff --cached`, run
  `git diff --cached --check`, and verify no unrelated path entered the index.
- After any corrective edit, run `uv run ruff format .` and `uv run ruff check --fix .`, then run
  `uv run python scripts/check_trailing_commas.py --check` and the repository pre-commit hooks
  before committing.
- Do not run pytest unless the maintainer explicitly authorizes it. The focused pytest commands
  below are the suites that should be authorized for each commit; the final authorized gate must
  preserve 100% package coverage.
- Use hunk staging for `django_strawberry_framework/auth/mutations.py`,
  `django_strawberry_framework/filters/sets.py`,
  `django_strawberry_framework/forms/resolvers.py`,
  `django_strawberry_framework/forms/sets.py`,
  `django_strawberry_framework/mutations/resolvers.py`,
  `django_strawberry_framework/optimizer/extension.py`,
  `django_strawberry_framework/optimizer/nested_planner.py`,
  `django_strawberry_framework/optimizer/walker.py`,
  `django_strawberry_framework/orders/sets.py`,
  `django_strawberry_framework/rest_framework/inputs.py`,
  `django_strawberry_framework/rest_framework/resolvers.py`, and
  `django_strawberry_framework/rest_framework/sets.py`, because those files contain changes
  belonging to more than one commit.

## Blocking findings to resolve first

1. `make_meta_validating_metaclass()` currently returns a function-local class named
   `MetaValidatingMetaclass`; this changes the runtime `__name__`, `__qualname__`, module
   addressability, and pickling/introspection behavior of the public mutation/form metaclasses.
   Fix the identity contract at the owner before Commit 4.
2. `filters/inputs.py` now delegates model-field traversal to django-filter's `get_model_field`,
   which may raise `RuntimeError` for unresolved lazy relations where the previous implementation
   returned `None`. Decide and test the intended contract before Commit 6.
3. `optimizer/nested_planner.py` is dirty while its planned report
   `docs/dry/dry-file-optimizer__nested_planner.md` does not exist and the cycle item remains open.
   Complete and independently verify that report before Commits 9-10.
4. `docs/dry/dry-file-auth__mutations.md`, `dry-file-forms__resolvers.md`,
   `dry-folder-auth.md`, `dry-folder-forms.md`, and `dry-folder-mutations.md` contain reopened or
   stale verification language. Reconcile each against the final source diff before its owning
   commit.
5. `docs/dry/dry-file-forms__sets.md` and `dry-folder-forms.md` still describe the metaclass
   factory as deferred although source implements it. Correct the reports only after the metaclass
   identity issue is fixed.
6. `docs/dry/dry-file-management__commands____init__.md` ends with a stray `)`. Correct it before
   Commit 14.
7. `docs/dry/dry-file-testing___wrap.md` is `fix-implemented` while its plan item remains open. It
   cannot enter a verified-audit commit until independent verification closes it.
8. `docs/feedback.md` was a zero-byte truncation of a 241-line review. The explicit request to
   replace it with this plan resolves the empty-placeholder problem, but the old Spec-044 finding
   must already be preserved/resolved elsewhere before the replacement is committed.
9. `uv run python scripts/check_trailing_commas.py --check` currently fails on five over-expanded
   constructs and two non-ASCII em dashes. Resolve the layout failures in
   `django_strawberry_framework/mutations/permissions.py`,
   `django_strawberry_framework/optimizer/join_taxonomy.py`,
   `tests/optimizer/test_join_taxonomy.py`, and two locations in
   `tests/rest_framework/test_resolvers.py`; replace the two em dashes in
   `django_strawberry_framework/management/commands/inspect_django_type.py` with ASCII punctuation.
   Re-run the checker after the owning Commits 2, 12, 13, and 14 are prepared.

## Commit sequence

### 1. Centralize the thread-sensitive sync boundary

**Commit title:** `refactor(async): centralize the thread-sensitive sync boundary`

**Files and hunks:**

- `django_strawberry_framework/utils/querysets.py`
- `tests/utils/test_querysets.py`
- `django_strawberry_framework/schema.py`
- Sync-boundary/import hunks only from `django_strawberry_framework/auth/mutations.py`
- Sync-boundary hunks only from `django_strawberry_framework/filters/sets.py`
- Sync-boundary hunks only from `django_strawberry_framework/orders/sets.py`
- Compatibility re-export and async-call hunks only from
  `django_strawberry_framework/mutations/resolvers.py`
- Off-event-loop assertions only from `tests/filters/test_sets.py`
- `docs/dry/dry-file-auth__mutations.md`
- `docs/dry/dry-file-mutations__resolvers.md`

**Why these belong together:** `utils/querysets.py` becomes the cycle-safe owner of the one
`sync_to_async(thread_sensitive=True)` hop. Every dirty consumer must migrate atomically, while
`mutations.resolvers` preserves historical import identity.

**Review before commit:** Confirm there is exactly one function definition; confirm the mutation
re-export is the same object; make sure no queryset, permission hook, or auth operation evaluates
before entering the worker; reconcile both DRY reports and obtain independent verification.

**Probable checks:** Grep for duplicate definitions and old local `sync_to_async` wrappers; inspect
import cycles; authorize `tests/utils/test_querysets.py`, the async FilterSet/OrderSet tests, schema
mutation execution tests, and auth async tests.

### 2. Harden authorization and plain-form phase boundaries

**Commit title:** `fix(permissions): enforce strict authorization and write-phase boundaries`

**Files and hunks:**

- `django_strawberry_framework/utils/permissions.py`
- `tests/utils/test_permissions.py`
- `django_strawberry_framework/mutations/permissions.py`
- Authorization/auth-alias hunks only from
  `django_strawberry_framework/mutations/resolvers.py`
- Permission, alias-guard, validation-phase, and write-window hunks only from
  `django_strawberry_framework/forms/resolvers.py`
- Phase-boundary tests only from `tests/forms/test_resolvers.py`
- `docs/dry/dry-file-mutations__permissions.md`
- `docs/dry/dry-file-forms__resolvers.md`
- `docs/dry/dry-folder-forms.md`

**Why these belong together:** This is one security contract: permission methods must return real
booleans, permissionless surfaces must not gain auth-alias access, read-only phases must remain
read-only, and only `perform_mutate` receives the pinned write window.

**Review before commit:** Reject awaitables and truthy non-bools consistently for permission
classes, mutation hooks, and `user.has_perm`; verify `permission_classes=[]` neither resolves the
lazy user nor opens auth aliases; confirm the new form restriction is intentional for consumer
validators that previously wrote during validation. Review the pre-existing per-element
`_decode_form_relation_multi` query behavior for N+1 risk even though this diff does not worsen it.

**Probable checks:** Grep for direct `resolve_auth_aliases()` conditionals; authorize permission,
write-transaction, form resolver, divergent-router authorization, and live mutation security
tests.

### 3. Unify generated input-field metadata

**Commit title:** `refactor(inputs): unify generated input field metadata`

**Files and hunks:**

- `django_strawberry_framework/utils/inputs.py`
- `django_strawberry_framework/forms/__init__.py`
- `django_strawberry_framework/forms/converter.py`
- Input metadata/decode hunks from `django_strawberry_framework/forms/inputs.py`
- Target-name/decode hunks from `django_strawberry_framework/forms/resolvers.py`
- InputFieldSpec documentation hunk from `django_strawberry_framework/forms/sets.py`
- `tests/forms/test_converter.py`
- Input-metadata hunks from `tests/forms/test_inputs.py`
- `docs/dry/dry-file-forms____init__.md`
- `docs/dry/dry-file-forms__converter.md`
- `docs/dry/dry-file-forms__inputs.md`

**Why these belong together:** The form-only `FormInputFieldSpec` is replaced by the neutral
`InputFieldSpec.target_name` owner, while shared required-field and collision mechanics remain in
`utils/inputs.py`.

**Review before commit:** Grep for remaining `FormInputFieldSpec` and `.form_field_name` use;
verify model, form, and serializer meanings of `target_name`, `source`, and nested specs remain
distinct; fix the doubled whitespace in the collision-helper docstring; confirm relation discovery
stays build-time and introduces no request-time ORM work.

**Probable checks:** Authorize form converter/input tests plus mutation and serializer
input-generation regressions that consume the shared dataclass.

### 4. Unify mutation declaration and input-shape lifecycle

**Commit title:** `refactor(mutations): unify declaration and input-shape lifecycle`

**Files and hunks:**

- `django_strawberry_framework/mutations/__init__.py`
- `django_strawberry_framework/mutations/inputs.py`
- `django_strawberry_framework/mutations/sets.py`
- Metaclass-consumer hunk from `django_strawberry_framework/forms/sets.py`
- `tests/mutations/test_sets.py`
- `docs/dry/dry-file-forms__sets.md`
- `docs/dry/dry-file-mutations____init__.md`
- `docs/dry/dry-file-mutations__fields.md`
- `docs/dry/dry-file-mutations__inputs.md`
- `docs/dry/dry-file-mutations__sets.md`
- `docs/dry/dry-folder-mutations.md`

**Why these belong together:** Operation vocabulary, generated input names, declaration
registries, shape-cache clearing, and the shared validating-metaclass lifecycle must change
atomically across model and plain-form mutation families.

**Review before commit:** Resolve the metaclass identity blocker first. Verify model and form
declaration registries remain disjoint, registry clears invalidate every generated shape,
post-finalization registration still fails, and operation/name derivation has one owner. Reconcile
the folder reports against the final implementation rather than their older item baselines.

**Probable checks:** Add/pin metaclass `__name__`, `__qualname__`, `__module__`, import
addressability, and pickling expectations as appropriate; authorize `tests/mutations/test_sets.py`
and form set/metaclass tests.

### 5. Single-source authenticated actor classification

**Commit title:** `refactor(auth): single-source authenticated actor classification`

**Files and hunks:**

- Actor-helper/logout hunks from `django_strawberry_framework/auth/mutations.py`
- `django_strawberry_framework/auth/queries.py`
- `docs/dry/dry-file-auth__queries.md`
- `docs/dry/dry-folder-auth.md`

**Why these belong together:** Logout and current-user must use the same definition of missing or
anonymous actors without coupling that rule to model-permission policy.

**Review before commit:** Confirm lazy `request.user` is forced once inside the worker boundary,
anonymous and missing-user behavior remains indistinguishable, and session mutations preserve
their existing payloads. Reconcile the reopened folder report and obtain independent verification.

**Probable checks:** Authorize auth query/mutation tests and live HTTP session-auth tests for
anonymous, inactive, authenticated, login, and logout paths.

### 6. Consolidate filter predicate and input ownership

**Commit title:** `refactor(filters): consolidate predicate and input ownership`

**Files and hunks:**

- `django_strawberry_framework/filters/__init__.py`
- `django_strawberry_framework/filters/base.py`
- `django_strawberry_framework/filters/inputs.py`
- Remaining non-boundary hunks from `django_strawberry_framework/filters/sets.py`
- `tests/filters/test_inputs.py`
- Remaining non-boundary hunks from `tests/filters/test_sets.py`
- `docs/dry/dry-file-filters____init__.md`
- `docs/dry/dry-file-filters__base.md`
- `docs/dry/dry-file-filters__factories.md`
- `docs/dry/dry-file-filters__inputs.md`
- `docs/dry/dry-file-filters__sets.md`
- `docs/dry/dry-folder-filters.md`

**Why these belong together:** Empty-list semantics, distinct-plus-lookup application, logic-field
naming, model-field path resolution, lifecycle prose, and FilterSet normalization are one
filter-family consolidation.

**Review before commit:** Resolve the lazy/unresolved relation behavior change. Verify empty
restrictive membership matches no rows, excluded empty membership matches all rows, invalid
integer members cannot widen a filter, `distinct()` still prevents duplicate parent rows, and
logic-key arity cannot drift from `_LOGIC_KEYS`. Check permission hooks for bounded query counts
and N+1 behavior.

**Probable checks:** Authorize filter base/input/set tests and live GraphQL filter tests; add a
lazy relation regression if that model state is supported.

### 7. Single-source ordering direction and lifecycle rules

**Commit title:** `refactor(orders): single-source direction and lifecycle rules`

**Files and hunks:**

- `django_strawberry_framework/orders/__init__.py`
- `django_strawberry_framework/orders/inputs.py`
- Remaining non-boundary hunks from `django_strawberry_framework/orders/sets.py`
- `tests/orders/test_inputs.py`
- `docs/dry/dry-file-orders____init__.md`
- `docs/dry/dry-file-orders__base.md`
- `docs/dry/dry-file-orders__factories.md`
- `docs/dry/dry-file-orders__inputs.md`
- `docs/dry/dry-file-orders__sets.md`
- `docs/dry/dry-folder-orders.md`

**Why these belong together:** Direction classification, Min/Max selection for to-many paths,
concrete-field import ownership, and namespace-clear documentation are one order-family contract.

**Review before commit:** Prefer a precise `self.name.startswith("ASC")` rule over substring
membership; verify all six enum values, null-position variants, to-many Min/Max choice, and
multiple to-many order terms. Inspect generated SQL for join multiplication and assert constant
query counts.

**Probable checks:** Authorize order input/set tests and live ordered connection tests with
multiple related rows and null positioning.

### 8. Unify ORM and lateral keyset seek planning

**Commit title:** `refactor(keyset): unify ORM and lateral seek planning`

**Files and hunks:**

- `django_strawberry_framework/keyset.py`
- `tests/test_keyset.py`
- `django_strawberry_framework/optimizer/lateral_fetch.py`
- `docs/dry/dry-file-optimizer__lateral_fetch.md`
- `docs/dry/dry-file-optimizer__nested_fetch.md`

**Why these belong together:** `KeysetSeek` is the dialect-neutral plan; ORM `Q` and parameterized
PostgreSQL SQL are renderers of that same plan. `lateral_fetch.py` cannot compile independently
from the new keyset API.

**Review before commit:** Treat this as high SQL-correctness risk. Verify after/before, ASC/DESC,
mixed and uniform directions, duplicate leading values, scalar/UUID/date/decimal/string
preparation, row-value versus OR expansion, counted-keyset downgrade, and cross-strategy cursor
replay. Confirm non-null cursor enforcement and collation semantics. No per-parent query loop
should appear.

**Probable checks:** Authorize keyset, lateral-fetch, PostgreSQL parity, and live connection tests;
compare result PK sequences from ORM and lateral renderers, not just SQL strings; use PostgreSQL
`EXPLAIN (ANALYZE, BUFFERS)` for composite-index behavior.

### 9. Centralize Strawberry schema/config access

**Commit title:** `refactor(optimizer): centralize Strawberry schema config access`

**Files and hunks:**

- `django_strawberry_framework/utils/__init__.py`
- `django_strawberry_framework/utils/typing.py`
- `django_strawberry_framework/utils/connections.py`
- `tests/utils/test_typing.py`
- Schema/config hunks from `django_strawberry_framework/optimizer/extension.py`
- Schema/config hunks from `django_strawberry_framework/optimizer/nested_planner.py`
- Schema/config hunks from `django_strawberry_framework/optimizer/walker.py`
- `docs/dry/dry-folder-optimizer.md`
- The new, independently verified `docs/dry/dry-file-optimizer__nested_planner.md`

**Why these belong together:** Brittle `_strawberry_schema` and `.config` traversal receives one
utility owner while planner `None` and resolver default-100 behavior remain distinct.

**Review before commit:** Complete the missing nested-planner report. Add a contract test for an
explicitly present `_strawberry_schema=None`; confirm wrapped schema precedence, direct config
fallback, and caller choice between `strawberry_schema_from_info()` and
`schema_config_from_info()`. Grep so raw private-attribute traversal remains only in the utility
owner.

**Probable checks:** Authorize utility typing/connections and optimizer
extension/nested-planner/walker tests, including Relay max-results resolution.

### 10. Consolidate optimizer selection traversal and lifecycle state

**Commit title:** `refactor(optimizer): consolidate selection traversal and lifecycle state`

**Files and hunks:**

- `django_strawberry_framework/optimizer/__init__.py`
- Remaining selection/lifecycle hunks from `django_strawberry_framework/optimizer/extension.py`
- Remaining selection hunks from `django_strawberry_framework/optimizer/nested_planner.py`
- `django_strawberry_framework/optimizer/selections.py`
- `tests/optimizer/test_extension.py`
- `tests/optimizer/test_selections.py`
- `docs/dry/dry-file-optimizer____init__.md`
- `docs/dry/dry-file-optimizer___context.md`
- `docs/dry/dry-file-optimizer__extension.md`
- `docs/dry/dry-file-optimizer__selections.md`

**Why these belong together:** Relay `edges -> node` composition, fragment resolution, AST child
iteration, and active-optimizer lifecycle state must have one owner.

**Review before commit:** Exercise the same named fragment at multiple depths with aliases,
directives, pagination variables, and cyclic-fragment validation. Verify runtime prefixes preserve
strictness/FK-id ledger keys and that removing the obsolete lifecycle ContextVar does not affect
concurrent executions. Query-count live tests are required to catch masked N+1 regressions.

**Probable checks:** Authorize extension/selections/nested connection tests plus live root and
nested connection query-count coverage.

### 11. Centralize optimizer field metadata and path ledgers

**Commit title:** `refactor(optimizer): centralize field metadata and path ledgers`

**Files and hunks:**

- `django_strawberry_framework/optimizer/field_meta.py`
- Remaining metadata/ledger hunks from `django_strawberry_framework/optimizer/walker.py`
- `tests/optimizer/test_field_meta.py`
- `tests/optimizer/test_walker.py`
- `docs/dry/dry-file-optimizer__field_meta.md`
- `docs/dry/dry-file-optimizer__walker.md`

**Why these belong together:** `FieldMeta` becomes authoritative for FK-elision and target-PK
values, including stamped `None`, while select/prefetch resolver-key ledgers share append-unique
semantics.

**Review before commit:** Confirm a stamped `None` never falls through to raw Django metadata;
verify MTI parent links, custom primary keys, fabricated metadata, resolver-key deduplication, and
strictness attribution. A wrong ledger can mark an unplanned relation as planned and hide an N+1.

**Probable checks:** Authorize field-meta/walker tests and live custom-PK/FK-id-elision query-count
tests.

### 12. Share optimizer hint and windowability invariants

**Commit title:** `refactor(optimizer): share hint and windowability invariants`

**Files and hunks:**

- `django_strawberry_framework/optimizer/hints.py`
- `django_strawberry_framework/optimizer/join_taxonomy.py`
- `django_strawberry_framework/optimizer/plans.py`
- `tests/optimizer/test_join_taxonomy.py`
- `docs/dry/dry-file-optimizer__hints.md`
- `docs/dry/dry-file-optimizer__join_taxonomy.md`
- `docs/dry/dry-file-optimizer__plans.md`

**Why these belong together:** Prefetch validation and the set of windowable relation kinds are
shared planning invariants, not caller-owned vocabularies.

**Review before commit:** Verify custom `Prefetch` lookup/`to_attr`, conflicting hint flags, every
relation taxonomy member, window partition ownership, and unchanged behavior in the clean
hint/plan test modules.

**Probable checks:** Authorize optimizer hint, join-taxonomy, plans, and nested-window tests.

### 13. Unify DRF writable-source ownership

**Commit title:** `refactor(drf): unify writable-source ownership and write-surface verification`

**Files and hunks:**

- `django_strawberry_framework/rest_framework/inputs.py`
- `django_strawberry_framework/rest_framework/resolvers.py`
- `django_strawberry_framework/rest_framework/serializer_converter.py`
- `django_strawberry_framework/rest_framework/sets.py`
- `tests/rest_framework/test_converter.py`
- `tests/rest_framework/test_inputs.py`
- `tests/rest_framework/test_resolvers.py`
- `docs/dry/dry-file-rest_framework____init__.md`
- `docs/dry/dry-file-rest_framework__inputs.md`
- `docs/dry/dry-file-rest_framework__resolvers.md`
- `docs/dry/dry-file-rest_framework__serializer_converter.md`
- `docs/dry/dry-file-rest_framework__sets.md`
- `docs/dry/dry-folder-rest_framework.md`

**Why these belong together:** Root/nested source ownership, `source="*"` rejection, collision
diagnostics, injected fields, runtime agreement, intent instrumentation, serializer construction,
and write-surface attestation form one security boundary.

**Review before commit:** Confirm `_write_surface_specs()` cannot turn a private pre-bind caller
into a raw `AttributeError`; if the lifecycle precondition is real, fail with a package
`ConfigurationError`. Grep exact diagnostic pins. Verify injected fields participate in
schema/runtime agreement and relation attestation without broadening writable input. Review
relation scoping for bounded queries and N+1 behavior.

**Probable checks:** Authorize all three dirty DRF test modules plus serializer mutation live
GraphQL tests, nested serializer tests, relation visibility, source collision, write witness, and
attestation suites.

### 14. Align inspect_django_type with canonical Relay metadata

**Commit title:** `fix(command): align inspect_django_type with canonical Relay metadata`

**Files and hunks:**

- `django_strawberry_framework/management/commands/inspect_django_type.py`
- `tests/management/test_inspect_django_type.py`
- `docs/dry/dry-file-management____init__.md`
- `docs/dry/dry-file-management__commands____init__.md`
- `docs/dry/dry-file-management__commands___imports.md`
- `docs/dry/dry-file-management__commands__export_schema.md`
- `docs/dry/dry-file-management__commands__inspect_django_type.md`
- `docs/dry/dry-folder-management.md`
- `docs/dry/dry-folder-management__commands.md`

**Why these belong together:** The command must use the same Relay-shape predicate that suppressed
the model primary key during type synthesis; the management audit reports document the
consolidation and rejected alternatives.

**Review before commit:** Remove the stray `)` from the command-package report. Verify direct
`DjangoType, relay.Node` inheritance, `Meta.interfaces`, custom Node subclasses, registry fixture
isolation, and the private-helper rename boundary.

**Probable checks:** Authorize package and fakeshop inspect-command tests, including cold
`--schema` imports and connection-only relation shapes.

### 15. Reconcile glossary source and rendered output

**Commit title:** `docs(glossary): reconcile command and cascade permission entries`

**Files and hunks:**

- `examples/fakeshop/db.sqlite3`
- `docs/GLOSSARY.md`

**Why these belong together:** The SQLite source and rendered glossary are currently split in
opposite directions: the database's sole changed row is the `apply_cascade_permissions` body from
the recent cascade hardening, while the rendered Markdown adds the current `inspect_django_type`
SDL-name contract. They must land atomically so source and render return to parity.

**Review before commit:** Confirm the database diff remains exactly one existing row
(`glossary_glossaryterm` rowid 440) with only `body` and `updated_date` changed; no users, sessions,
products, kanban rows, schema, migrations, or row counts may change. Confirm the glossary command
entry matches active `NameConverter`, `Meta.name`, Python-name fallback, and ambiguity behavior.

**Probable checks:** Run the glossary renderer/checker in check mode, `PRAGMA integrity_check`,
`PRAGMA foreign_key_check`, row-count and row-level diff scripts, and the Markdown link/spec
checker. Authorize inspect-command tests if not already run for Commit 14.

### 16. Align the DRY workflow with test authorization

**Commit title:** `docs(dry): align review workflow with test authorization`

**Files and hunks:**

- `docs/dry/DRY.md`

**Why these belong together:** This is a process-policy correction independent of runtime changes:
workers may suggest or defer pytest, but may run it only with explicit maintainer authorization.

**Review before commit:** Ensure formatting and Ruff remain mandatory after edits, final coverage
remains 100% once pytest is authorized, and the wording does not imply that artifact authors ran
checks they only recorded.

**Probable checks:** Run Markdown/source-layout and link-definition checks; no pytest is relevant.

### 17. Record verified DRY audit progress

**Commit title:** `docs(dry): record verified audit progress`

**Files and hunks:**

- `docs/dry/dry-0_0_13.md`
- `docs/dry/dry-file-exceptions.md`
- `docs/dry/dry-file-extensions____init__.md`
- `docs/dry/dry-file-extensions__debug.md`
- `docs/dry/dry-folder-extensions.md`
- `docs/dry/dry-file-middleware____init__.md`
- `docs/dry/dry-file-middleware__debug_toolbar.md`
- `docs/dry/dry-folder-middleware.md`
- `docs/dry/dry-file-testing____init__.md`
- `docs/dry/dry-file-testing___wrap.md`

**Why these belong together:** These are cycle-level progress or zero-edit audit artifacts with no
dirty production source to accompany. They should land only after source commits and after every
status reflects final source.

**Review before commit:** Do not present the cycle as complete: schema, nested planner, hook
context, write transaction, and later project passes remain open. Close `testing/_wrap.py`
independently before checking it. Verify every `[x]` points to a `Status: verified` artifact whose
recorded source hash matches final source; every pending or `fix-implemented` item remains
unchecked. Confirm the exception report's recompute-from-current-`.args` narrative matches
production and tests.

**Probable checks:** Run the DRY exporter's check mode, Markdown/source-layout/link checks, and
source-hash validation. Authorize focused exception and testing-wrap tests only if needed to close
their reports.

### 18. Record the dirty-tree commit plan

**Commit title:** `docs(review): record the dirty-tree commit plan`

**Files and hunks:**

- `docs/feedback.md`

**Why these belong together:** The file is intentionally repurposed from the truncated Spec-044
review into this maintainer-requested commit decomposition. Keeping it isolated makes the planning
record easy to retain, revise, or remove without coupling it to runtime behavior.

**Review before commit:** Confirm the old Spec-044 P0 CI finding and unrun-check record were
resolved or preserved elsewhere. Update this plan if corrective edits change any path ownership or
commit boundary. Ensure every one of the other 128 dirty paths is named exactly once, except
explicitly hunk-split files named in multiple commits.

**Probable checks:** Run Markdown/source-layout/link checks and a script comparing
`git status --porcelain` paths against paths listed in this document; no pytest is relevant.

## Final integration gate

After Commit 17 is ready and only with explicit pytest authorization, run the repository's
documented complete test/coverage pipeline and require 100% package coverage. Then run all
pre-commit hooks, the trailing-comma checker, generated glossary/tree/kanban checks that apply, and
`git status --short`. Review the complete commit range to confirm dependency order, no accidental
binary churn, no orphaned imports, no stale DRY status claims, and no N+1 regression in
filter/order permissions, serializer relation scoping, optimizer selection prefixes, or keyset
pagination.

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