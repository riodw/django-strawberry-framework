# Bug hunt: 0.0.15

Status: in-progress
Mode: autonomous
Run id: `0.0.15-92e4efeb41640f38cae4167de27ae28c2217ef71`
Baseline commit: `92e4efeb41640f38cae4167de27ae28c2217ef71`
Run scope: this run hunts exactly one item, `django_strawberry_framework/utils/querysets.py`, by maintainer instruction. Every other file item, every scenario item, the package integration item and the final gate stay `pending` and are not run here.

## Cycle baseline

`git status --short` at generation. Every path below is concurrent work: never edited, reverted, tidied, or attributed to an item. Worker 0 appends the `CYCLE_BASELINE` stash object once at start and nothing afterwards.

```text
 M AGENTS.md
 M START.md
 M docs/bug_hunt/HUNT.md
 D docs/bug_hunt/bug_hunt-0_0_15.md
 M docs/feedback.md
 M examples/fakeshop/test_query/test_transport_api.py
 M scripts/bug_hunt.py
 M tests/base/__init__.py
 M tests/base/test_conf.py
 M tests/base/test_init.py
 M tests/test_bug_hunt.py
?? docs/bug_hunt/bug_hunt-0_0_1555.md
?? docs/bug_hunt/worker-0.md
?? docs/bug_hunt/worker-1.md
?? docs/bug_hunt/worker-2.md
```

`CYCLE_BASELINE` = `3b5cf55ea5795fd2acf580d40e2adc0c191195b3`

## Package questions

No maintainer-authored probing questions were supplied. Explore the live source freely; shadow inputs are orientation only.

## How to hunt one item
Each file item uses one source file as its entry point into the live system;
scenario items own one cross-file contract. The target is narrow; the
investigation and root-cause fix cross files. `docs/bug_hunt/HUNT.md` is the
method; this brief is a reminder, not a substitute.

- Read the shadow overview and stripped source for baseline orientation, then
  read the complete live target. Shadow markers and stripped line numbers are
  never authoritative.
- Record the contract row for every boundary before probing it: boundary,
  failure class, promised wire shape, masking, rollback, absent unauthorized
  effects. A contract nobody can cite is reported blocked, never fixed.
- Trace callers, dependencies, state, framework hooks, tests, examples, and
  public contracts far enough to understand the target's real behavior. Clean
  layers often fail only when several reasonable assumptions stack together;
  hunt those interactions, not only suspicious local lines.
- Break things, break things, break things, inside the disposable workspace
  copy only: mutate throwaway state, force hostile sequences, interrupt
  lifecycles, and try to make every connected layer fail. A probe that imports
  the shared checkout or opens its database is invalid whatever it found.
- For every extreme, test the opposite extreme and then combine them across
  layers. Discharge every axis of the mandatory matrix. Try to disprove every
  candidate and record only confirmed defects.
- Every claim links to an evidence record: workspace path, imported package
  path, database target, exact command, source digests, collected and executed
  counts, the assertion proving the boundary was reached, a positive control.
- Do not clean up scratch probes, workspaces, or disposable state. Report every
  path and leave it intact so Worker 2 can replay it and Worker 0 can remove it
  only after the item is verified.
- Implement the root-cause fix at the layer that owns the broken invariant in
  the shared tree, attributing every hunk of a dirty path first, including
  connected files when required. Add a permanent behavioral test for every
  production fix at the strongest tier required by `AGENTS.md`.
- After edits run `uv run ruff format .` and `uv run ruff check --fix .`.
- Report evidence, changed files, tests, and validation to Worker 0. Do not edit
  this progress file; Worker 0 runs the mechanical checks, a fresh Worker 2
  verifies, and Worker 0 advances it.

## Hunt items

- [ ] django_strawberry_framework/_boundary_ordering.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework___boundary_ordering.stripped.py
    - docs/shadow/current/django_strawberry_framework___boundary_ordering.overview.md
    - Prompt:
        - Use django_strawberry_framework/_boundary_ordering.py as the entry point. Read docs/shadow/current/django_strawberry_framework___boundary_ordering.stripped.py and docs/shadow/current/django_strawberry_framework___boundary_ordering.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/_cross_web_patches.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework___cross_web_patches.stripped.py
    - docs/shadow/current/django_strawberry_framework___cross_web_patches.overview.md
    - Prompt:
        - Use django_strawberry_framework/_cross_web_patches.py as the entry point. Read docs/shadow/current/django_strawberry_framework___cross_web_patches.stripped.py and docs/shadow/current/django_strawberry_framework___cross_web_patches.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/_django_patches.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework___django_patches.stripped.py
    - docs/shadow/current/django_strawberry_framework___django_patches.overview.md
    - Prompt:
        - Use django_strawberry_framework/_django_patches.py as the entry point. Read docs/shadow/current/django_strawberry_framework___django_patches.stripped.py and docs/shadow/current/django_strawberry_framework___django_patches.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/_graphql_core_patches.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework___graphql_core_patches.stripped.py
    - docs/shadow/current/django_strawberry_framework___graphql_core_patches.overview.md
    - Prompt:
        - Use django_strawberry_framework/_graphql_core_patches.py as the entry point. Read docs/shadow/current/django_strawberry_framework___graphql_core_patches.stripped.py and docs/shadow/current/django_strawberry_framework___graphql_core_patches.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/_request_body.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework___request_body.stripped.py
    - docs/shadow/current/django_strawberry_framework___request_body.overview.md
    - Prompt:
        - Use django_strawberry_framework/_request_body.py as the entry point. Read docs/shadow/current/django_strawberry_framework___request_body.stripped.py and docs/shadow/current/django_strawberry_framework___request_body.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/_strawberry_patches.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework___strawberry_patches.stripped.py
    - docs/shadow/current/django_strawberry_framework___strawberry_patches.overview.md
    - Prompt:
        - Use django_strawberry_framework/_strawberry_patches.py as the entry point. Read docs/shadow/current/django_strawberry_framework___strawberry_patches.stripped.py and docs/shadow/current/django_strawberry_framework___strawberry_patches.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/apps.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__apps.stripped.py
    - docs/shadow/current/django_strawberry_framework__apps.overview.md
    - Prompt:
        - Use django_strawberry_framework/apps.py as the entry point. Read docs/shadow/current/django_strawberry_framework__apps.stripped.py and docs/shadow/current/django_strawberry_framework__apps.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/auth/mutations.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__auth__mutations.stripped.py
    - docs/shadow/current/django_strawberry_framework__auth__mutations.overview.md
    - Prompt:
        - Use django_strawberry_framework/auth/mutations.py as the entry point. Read docs/shadow/current/django_strawberry_framework__auth__mutations.stripped.py and docs/shadow/current/django_strawberry_framework__auth__mutations.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/auth/queries.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__auth__queries.stripped.py
    - docs/shadow/current/django_strawberry_framework__auth__queries.overview.md
    - Prompt:
        - Use django_strawberry_framework/auth/queries.py as the entry point. Read docs/shadow/current/django_strawberry_framework__auth__queries.stripped.py and docs/shadow/current/django_strawberry_framework__auth__queries.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/auth/sessions.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__auth__sessions.stripped.py
    - docs/shadow/current/django_strawberry_framework__auth__sessions.overview.md
    - Prompt:
        - Use django_strawberry_framework/auth/sessions.py as the entry point. Read docs/shadow/current/django_strawberry_framework__auth__sessions.stripped.py and docs/shadow/current/django_strawberry_framework__auth__sessions.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/conf.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__conf.stripped.py
    - docs/shadow/current/django_strawberry_framework__conf.overview.md
    - Prompt:
        - Use django_strawberry_framework/conf.py as the entry point. Read docs/shadow/current/django_strawberry_framework__conf.stripped.py and docs/shadow/current/django_strawberry_framework__conf.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/connection.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__connection.stripped.py
    - docs/shadow/current/django_strawberry_framework__connection.overview.md
    - Prompt:
        - Use django_strawberry_framework/connection.py as the entry point. Read docs/shadow/current/django_strawberry_framework__connection.stripped.py and docs/shadow/current/django_strawberry_framework__connection.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/consumers.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__consumers.stripped.py
    - docs/shadow/current/django_strawberry_framework__consumers.overview.md
    - Prompt:
        - Use django_strawberry_framework/consumers.py as the entry point. Read docs/shadow/current/django_strawberry_framework__consumers.stripped.py and docs/shadow/current/django_strawberry_framework__consumers.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/error_policy.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__error_policy.stripped.py
    - docs/shadow/current/django_strawberry_framework__error_policy.overview.md
    - Prompt:
        - Use django_strawberry_framework/error_policy.py as the entry point. Read docs/shadow/current/django_strawberry_framework__error_policy.stripped.py and docs/shadow/current/django_strawberry_framework__error_policy.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/exceptions.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__exceptions.stripped.py
    - docs/shadow/current/django_strawberry_framework__exceptions.overview.md
    - Prompt:
        - Use django_strawberry_framework/exceptions.py as the entry point. Read docs/shadow/current/django_strawberry_framework__exceptions.stripped.py and docs/shadow/current/django_strawberry_framework__exceptions.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/extensions/debug.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__extensions__debug.stripped.py
    - docs/shadow/current/django_strawberry_framework__extensions__debug.overview.md
    - Prompt:
        - Use django_strawberry_framework/extensions/debug.py as the entry point. Read docs/shadow/current/django_strawberry_framework__extensions__debug.stripped.py and docs/shadow/current/django_strawberry_framework__extensions__debug.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/extensions/error_policy.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__extensions__error_policy.stripped.py
    - docs/shadow/current/django_strawberry_framework__extensions__error_policy.overview.md
    - Prompt:
        - Use django_strawberry_framework/extensions/error_policy.py as the entry point. Read docs/shadow/current/django_strawberry_framework__extensions__error_policy.stripped.py and docs/shadow/current/django_strawberry_framework__extensions__error_policy.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/extensions/operation_state.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__extensions__operation_state.stripped.py
    - docs/shadow/current/django_strawberry_framework__extensions__operation_state.overview.md
    - Prompt:
        - Use django_strawberry_framework/extensions/operation_state.py as the entry point. Read docs/shadow/current/django_strawberry_framework__extensions__operation_state.stripped.py and docs/shadow/current/django_strawberry_framework__extensions__operation_state.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/extensions/resource_policy.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__extensions__resource_policy.stripped.py
    - docs/shadow/current/django_strawberry_framework__extensions__resource_policy.overview.md
    - Prompt:
        - Use django_strawberry_framework/extensions/resource_policy.py as the entry point. Read docs/shadow/current/django_strawberry_framework__extensions__resource_policy.stripped.py and docs/shadow/current/django_strawberry_framework__extensions__resource_policy.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/filters/base.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__filters__base.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__base.overview.md
    - Prompt:
        - Use django_strawberry_framework/filters/base.py as the entry point. Read docs/shadow/current/django_strawberry_framework__filters__base.stripped.py and docs/shadow/current/django_strawberry_framework__filters__base.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/filters/factories.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__filters__factories.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__factories.overview.md
    - Prompt:
        - Use django_strawberry_framework/filters/factories.py as the entry point. Read docs/shadow/current/django_strawberry_framework__filters__factories.stripped.py and docs/shadow/current/django_strawberry_framework__filters__factories.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/filters/inputs.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__filters__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__inputs.overview.md
    - Prompt:
        - Use django_strawberry_framework/filters/inputs.py as the entry point. Read docs/shadow/current/django_strawberry_framework__filters__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__filters__inputs.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/filters/sets.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__filters__sets.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__sets.overview.md
    - Prompt:
        - Use django_strawberry_framework/filters/sets.py as the entry point. Read docs/shadow/current/django_strawberry_framework__filters__sets.stripped.py and docs/shadow/current/django_strawberry_framework__filters__sets.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/forms/converter.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__forms__converter.stripped.py
    - docs/shadow/current/django_strawberry_framework__forms__converter.overview.md
    - Prompt:
        - Use django_strawberry_framework/forms/converter.py as the entry point. Read docs/shadow/current/django_strawberry_framework__forms__converter.stripped.py and docs/shadow/current/django_strawberry_framework__forms__converter.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/forms/inputs.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__forms__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__forms__inputs.overview.md
    - Prompt:
        - Use django_strawberry_framework/forms/inputs.py as the entry point. Read docs/shadow/current/django_strawberry_framework__forms__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__forms__inputs.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/forms/resolvers.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__forms__resolvers.stripped.py
    - docs/shadow/current/django_strawberry_framework__forms__resolvers.overview.md
    - Prompt:
        - Use django_strawberry_framework/forms/resolvers.py as the entry point. Read docs/shadow/current/django_strawberry_framework__forms__resolvers.stripped.py and docs/shadow/current/django_strawberry_framework__forms__resolvers.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/forms/sets.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__forms__sets.stripped.py
    - docs/shadow/current/django_strawberry_framework__forms__sets.overview.md
    - Prompt:
        - Use django_strawberry_framework/forms/sets.py as the entry point. Read docs/shadow/current/django_strawberry_framework__forms__sets.stripped.py and docs/shadow/current/django_strawberry_framework__forms__sets.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/keyset.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__keyset.stripped.py
    - docs/shadow/current/django_strawberry_framework__keyset.overview.md
    - Prompt:
        - Use django_strawberry_framework/keyset.py as the entry point. Read docs/shadow/current/django_strawberry_framework__keyset.stripped.py and docs/shadow/current/django_strawberry_framework__keyset.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/list_field.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__list_field.stripped.py
    - docs/shadow/current/django_strawberry_framework__list_field.overview.md
    - Prompt:
        - Use django_strawberry_framework/list_field.py as the entry point. Read docs/shadow/current/django_strawberry_framework__list_field.stripped.py and docs/shadow/current/django_strawberry_framework__list_field.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/management/commands/_imports.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__management__commands___imports.stripped.py
    - docs/shadow/current/django_strawberry_framework__management__commands___imports.overview.md
    - Prompt:
        - Use django_strawberry_framework/management/commands/_imports.py as the entry point. Read docs/shadow/current/django_strawberry_framework__management__commands___imports.stripped.py and docs/shadow/current/django_strawberry_framework__management__commands___imports.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/management/commands/export_schema.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__management__commands__export_schema.stripped.py
    - docs/shadow/current/django_strawberry_framework__management__commands__export_schema.overview.md
    - Prompt:
        - Use django_strawberry_framework/management/commands/export_schema.py as the entry point. Read docs/shadow/current/django_strawberry_framework__management__commands__export_schema.stripped.py and docs/shadow/current/django_strawberry_framework__management__commands__export_schema.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/management/commands/inspect_django_type.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__management__commands__inspect_django_type.stripped.py
    - docs/shadow/current/django_strawberry_framework__management__commands__inspect_django_type.overview.md
    - Prompt:
        - Use django_strawberry_framework/management/commands/inspect_django_type.py as the entry point. Read docs/shadow/current/django_strawberry_framework__management__commands__inspect_django_type.stripped.py and docs/shadow/current/django_strawberry_framework__management__commands__inspect_django_type.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/middleware/debug_toolbar.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__middleware__debug_toolbar.stripped.py
    - docs/shadow/current/django_strawberry_framework__middleware__debug_toolbar.overview.md
    - Prompt:
        - Use django_strawberry_framework/middleware/debug_toolbar.py as the entry point. Read docs/shadow/current/django_strawberry_framework__middleware__debug_toolbar.stripped.py and docs/shadow/current/django_strawberry_framework__middleware__debug_toolbar.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/middleware/request_body.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__middleware__request_body.stripped.py
    - docs/shadow/current/django_strawberry_framework__middleware__request_body.overview.md
    - Prompt:
        - Use django_strawberry_framework/middleware/request_body.py as the entry point. Read docs/shadow/current/django_strawberry_framework__middleware__request_body.stripped.py and docs/shadow/current/django_strawberry_framework__middleware__request_body.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/mutations/fields.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__mutations__fields.stripped.py
    - docs/shadow/current/django_strawberry_framework__mutations__fields.overview.md
    - Prompt:
        - Use django_strawberry_framework/mutations/fields.py as the entry point. Read docs/shadow/current/django_strawberry_framework__mutations__fields.stripped.py and docs/shadow/current/django_strawberry_framework__mutations__fields.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/mutations/inputs.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__mutations__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__mutations__inputs.overview.md
    - Prompt:
        - Use django_strawberry_framework/mutations/inputs.py as the entry point. Read docs/shadow/current/django_strawberry_framework__mutations__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__mutations__inputs.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/mutations/operations.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__mutations__operations.stripped.py
    - docs/shadow/current/django_strawberry_framework__mutations__operations.overview.md
    - Prompt:
        - Use django_strawberry_framework/mutations/operations.py as the entry point. Read docs/shadow/current/django_strawberry_framework__mutations__operations.stripped.py and docs/shadow/current/django_strawberry_framework__mutations__operations.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/mutations/permissions.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__mutations__permissions.stripped.py
    - docs/shadow/current/django_strawberry_framework__mutations__permissions.overview.md
    - Prompt:
        - Use django_strawberry_framework/mutations/permissions.py as the entry point. Read docs/shadow/current/django_strawberry_framework__mutations__permissions.stripped.py and docs/shadow/current/django_strawberry_framework__mutations__permissions.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/mutations/resolvers.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__mutations__resolvers.stripped.py
    - docs/shadow/current/django_strawberry_framework__mutations__resolvers.overview.md
    - Prompt:
        - Use django_strawberry_framework/mutations/resolvers.py as the entry point. Read docs/shadow/current/django_strawberry_framework__mutations__resolvers.stripped.py and docs/shadow/current/django_strawberry_framework__mutations__resolvers.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/mutations/sets.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__mutations__sets.stripped.py
    - docs/shadow/current/django_strawberry_framework__mutations__sets.overview.md
    - Prompt:
        - Use django_strawberry_framework/mutations/sets.py as the entry point. Read docs/shadow/current/django_strawberry_framework__mutations__sets.stripped.py and docs/shadow/current/django_strawberry_framework__mutations__sets.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/optimizer/_context.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__optimizer___context.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer___context.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/_context.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer___context.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer___context.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/optimizer/extension.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__optimizer__extension.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__extension.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/extension.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__extension.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__extension.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/optimizer/field_meta.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__optimizer__field_meta.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__field_meta.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/field_meta.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__field_meta.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__field_meta.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/optimizer/hints.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__optimizer__hints.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__hints.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/hints.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__hints.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__hints.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/optimizer/join_taxonomy.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__optimizer__join_taxonomy.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__join_taxonomy.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/join_taxonomy.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__join_taxonomy.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__join_taxonomy.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/optimizer/lateral_fetch.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__optimizer__lateral_fetch.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__lateral_fetch.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/lateral_fetch.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__lateral_fetch.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__lateral_fetch.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/optimizer/nested_fetch.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__optimizer__nested_fetch.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__nested_fetch.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/nested_fetch.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__nested_fetch.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__nested_fetch.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/optimizer/nested_planner.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__optimizer__nested_planner.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__nested_planner.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/nested_planner.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__nested_planner.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__nested_planner.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/optimizer/plans.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__optimizer__plans.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__plans.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/plans.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__plans.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__plans.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/optimizer/predicates.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__optimizer__predicates.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__predicates.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/predicates.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__predicates.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__predicates.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/optimizer/selections.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__optimizer__selections.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__selections.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/selections.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__selections.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__selections.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/optimizer/single_parent_fetch.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__optimizer__single_parent_fetch.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__single_parent_fetch.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/single_parent_fetch.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__single_parent_fetch.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__single_parent_fetch.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/optimizer/walker.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__optimizer__walker.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__walker.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/walker.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__walker.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__walker.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/orders/base.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__orders__base.stripped.py
    - docs/shadow/current/django_strawberry_framework__orders__base.overview.md
    - Prompt:
        - Use django_strawberry_framework/orders/base.py as the entry point. Read docs/shadow/current/django_strawberry_framework__orders__base.stripped.py and docs/shadow/current/django_strawberry_framework__orders__base.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/orders/factories.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__orders__factories.stripped.py
    - docs/shadow/current/django_strawberry_framework__orders__factories.overview.md
    - Prompt:
        - Use django_strawberry_framework/orders/factories.py as the entry point. Read docs/shadow/current/django_strawberry_framework__orders__factories.stripped.py and docs/shadow/current/django_strawberry_framework__orders__factories.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/orders/inputs.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__orders__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__orders__inputs.overview.md
    - Prompt:
        - Use django_strawberry_framework/orders/inputs.py as the entry point. Read docs/shadow/current/django_strawberry_framework__orders__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__orders__inputs.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/orders/sets.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__orders__sets.stripped.py
    - docs/shadow/current/django_strawberry_framework__orders__sets.overview.md
    - Prompt:
        - Use django_strawberry_framework/orders/sets.py as the entry point. Read docs/shadow/current/django_strawberry_framework__orders__sets.stripped.py and docs/shadow/current/django_strawberry_framework__orders__sets.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/permissions.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__permissions.stripped.py
    - docs/shadow/current/django_strawberry_framework__permissions.overview.md
    - Prompt:
        - Use django_strawberry_framework/permissions.py as the entry point. Read docs/shadow/current/django_strawberry_framework__permissions.stripped.py and docs/shadow/current/django_strawberry_framework__permissions.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/registry.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__registry.stripped.py
    - docs/shadow/current/django_strawberry_framework__registry.overview.md
    - Prompt:
        - Use django_strawberry_framework/registry.py as the entry point. Read docs/shadow/current/django_strawberry_framework__registry.stripped.py and docs/shadow/current/django_strawberry_framework__registry.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/relay.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__relay.stripped.py
    - docs/shadow/current/django_strawberry_framework__relay.overview.md
    - Prompt:
        - Use django_strawberry_framework/relay.py as the entry point. Read docs/shadow/current/django_strawberry_framework__relay.stripped.py and docs/shadow/current/django_strawberry_framework__relay.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/resource_policy.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__resource_policy.stripped.py
    - docs/shadow/current/django_strawberry_framework__resource_policy.overview.md
    - Prompt:
        - Use django_strawberry_framework/resource_policy.py as the entry point. Read docs/shadow/current/django_strawberry_framework__resource_policy.stripped.py and docs/shadow/current/django_strawberry_framework__resource_policy.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/rest_framework/hook_context.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__rest_framework__hook_context.stripped.py
    - docs/shadow/current/django_strawberry_framework__rest_framework__hook_context.overview.md
    - Prompt:
        - Use django_strawberry_framework/rest_framework/hook_context.py as the entry point. Read docs/shadow/current/django_strawberry_framework__rest_framework__hook_context.stripped.py and docs/shadow/current/django_strawberry_framework__rest_framework__hook_context.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/rest_framework/inputs.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__rest_framework__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__rest_framework__inputs.overview.md
    - Prompt:
        - Use django_strawberry_framework/rest_framework/inputs.py as the entry point. Read docs/shadow/current/django_strawberry_framework__rest_framework__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__rest_framework__inputs.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/rest_framework/resolvers.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__rest_framework__resolvers.stripped.py
    - docs/shadow/current/django_strawberry_framework__rest_framework__resolvers.overview.md
    - Prompt:
        - Use django_strawberry_framework/rest_framework/resolvers.py as the entry point. Read docs/shadow/current/django_strawberry_framework__rest_framework__resolvers.stripped.py and docs/shadow/current/django_strawberry_framework__rest_framework__resolvers.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/rest_framework/serializer_converter.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__rest_framework__serializer_converter.stripped.py
    - docs/shadow/current/django_strawberry_framework__rest_framework__serializer_converter.overview.md
    - Prompt:
        - Use django_strawberry_framework/rest_framework/serializer_converter.py as the entry point. Read docs/shadow/current/django_strawberry_framework__rest_framework__serializer_converter.stripped.py and docs/shadow/current/django_strawberry_framework__rest_framework__serializer_converter.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/rest_framework/sets.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__rest_framework__sets.stripped.py
    - docs/shadow/current/django_strawberry_framework__rest_framework__sets.overview.md
    - Prompt:
        - Use django_strawberry_framework/rest_framework/sets.py as the entry point. Read docs/shadow/current/django_strawberry_framework__rest_framework__sets.stripped.py and docs/shadow/current/django_strawberry_framework__rest_framework__sets.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/routers.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__routers.stripped.py
    - docs/shadow/current/django_strawberry_framework__routers.overview.md
    - Prompt:
        - Use django_strawberry_framework/routers.py as the entry point. Read docs/shadow/current/django_strawberry_framework__routers.stripped.py and docs/shadow/current/django_strawberry_framework__routers.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/scalars.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__scalars.stripped.py
    - docs/shadow/current/django_strawberry_framework__scalars.overview.md
    - Prompt:
        - Use django_strawberry_framework/scalars.py as the entry point. Read docs/shadow/current/django_strawberry_framework__scalars.stripped.py and docs/shadow/current/django_strawberry_framework__scalars.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/schema.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__schema.stripped.py
    - docs/shadow/current/django_strawberry_framework__schema.overview.md
    - Prompt:
        - Use django_strawberry_framework/schema.py as the entry point. Read docs/shadow/current/django_strawberry_framework__schema.stripped.py and docs/shadow/current/django_strawberry_framework__schema.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/sets_mixins.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__sets_mixins.stripped.py
    - docs/shadow/current/django_strawberry_framework__sets_mixins.overview.md
    - Prompt:
        - Use django_strawberry_framework/sets_mixins.py as the entry point. Read docs/shadow/current/django_strawberry_framework__sets_mixins.stripped.py and docs/shadow/current/django_strawberry_framework__sets_mixins.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/testing/_wrap.py
    - Status: pending
    - Baseline shadow: none (path excluded from the snapshot by its 'test' path filter, not new)
    - Prompt:
        - Use django_strawberry_framework/testing/_wrap.py as the entry point. No baseline shadow exists; hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/testing/client.py
    - Status: pending
    - Baseline shadow: none (path excluded from the snapshot by its 'test' path filter, not new)
    - Prompt:
        - Use django_strawberry_framework/testing/client.py as the entry point. No baseline shadow exists; hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/testing/relay.py
    - Status: pending
    - Baseline shadow: none (path excluded from the snapshot by its 'test' path filter, not new)
    - Prompt:
        - Use django_strawberry_framework/testing/relay.py as the entry point. No baseline shadow exists; hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/types/base.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__types__base.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__base.overview.md
    - Prompt:
        - Use django_strawberry_framework/types/base.py as the entry point. Read docs/shadow/current/django_strawberry_framework__types__base.stripped.py and docs/shadow/current/django_strawberry_framework__types__base.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/types/converters.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__types__converters.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__converters.overview.md
    - Prompt:
        - Use django_strawberry_framework/types/converters.py as the entry point. Read docs/shadow/current/django_strawberry_framework__types__converters.stripped.py and docs/shadow/current/django_strawberry_framework__types__converters.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/types/definition.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__types__definition.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__definition.overview.md
    - Prompt:
        - Use django_strawberry_framework/types/definition.py as the entry point. Read docs/shadow/current/django_strawberry_framework__types__definition.stripped.py and docs/shadow/current/django_strawberry_framework__types__definition.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/types/finalizer.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__types__finalizer.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__finalizer.overview.md
    - Prompt:
        - Use django_strawberry_framework/types/finalizer.py as the entry point. Read docs/shadow/current/django_strawberry_framework__types__finalizer.stripped.py and docs/shadow/current/django_strawberry_framework__types__finalizer.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/types/relations.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__types__relations.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__relations.overview.md
    - Prompt:
        - Use django_strawberry_framework/types/relations.py as the entry point. Read docs/shadow/current/django_strawberry_framework__types__relations.stripped.py and docs/shadow/current/django_strawberry_framework__types__relations.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/types/relay.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__types__relay.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__relay.overview.md
    - Prompt:
        - Use django_strawberry_framework/types/relay.py as the entry point. Read docs/shadow/current/django_strawberry_framework__types__relay.stripped.py and docs/shadow/current/django_strawberry_framework__types__relay.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/types/resolvers.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__types__resolvers.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__resolvers.overview.md
    - Prompt:
        - Use django_strawberry_framework/types/resolvers.py as the entry point. Read docs/shadow/current/django_strawberry_framework__types__resolvers.stripped.py and docs/shadow/current/django_strawberry_framework__types__resolvers.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/utils/canonical.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__utils__canonical.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__canonical.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/canonical.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__canonical.stripped.py and docs/shadow/current/django_strawberry_framework__utils__canonical.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/utils/connections.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__utils__connections.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__connections.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/connections.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__connections.stripped.py and docs/shadow/current/django_strawberry_framework__utils__connections.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/utils/context.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__utils__context.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__context.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/context.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__context.stripped.py and docs/shadow/current/django_strawberry_framework__utils__context.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/utils/converters.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__utils__converters.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__converters.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/converters.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__converters.stripped.py and docs/shadow/current/django_strawberry_framework__utils__converters.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/utils/directives.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__utils__directives.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__directives.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/directives.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__directives.stripped.py and docs/shadow/current/django_strawberry_framework__utils__directives.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/utils/errors.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__utils__errors.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__errors.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/errors.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__errors.stripped.py and docs/shadow/current/django_strawberry_framework__utils__errors.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/utils/execution_mode.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__utils__execution_mode.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__execution_mode.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/execution_mode.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__execution_mode.stripped.py and docs/shadow/current/django_strawberry_framework__utils__execution_mode.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/utils/imports.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__utils__imports.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__imports.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/imports.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__imports.stripped.py and docs/shadow/current/django_strawberry_framework__utils__imports.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/utils/input_values.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__utils__input_values.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__input_values.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/input_values.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__input_values.stripped.py and docs/shadow/current/django_strawberry_framework__utils__input_values.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/utils/inputs.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__utils__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__inputs.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/inputs.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__utils__inputs.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/utils/operation_lease.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__utils__operation_lease.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__operation_lease.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/operation_lease.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__operation_lease.stripped.py and docs/shadow/current/django_strawberry_framework__utils__operation_lease.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/utils/permissions.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__utils__permissions.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__permissions.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/permissions.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__permissions.stripped.py and docs/shadow/current/django_strawberry_framework__utils__permissions.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/utils/policies.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__utils__policies.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__policies.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/policies.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__policies.stripped.py and docs/shadow/current/django_strawberry_framework__utils__policies.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/utils/private_state.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__utils__private_state.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__private_state.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/private_state.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__private_state.stripped.py and docs/shadow/current/django_strawberry_framework__utils__private_state.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [x] django_strawberry_framework/utils/querysets.py
    - Status: verified
    - Iteration: 1 — Worker 1 dispatched. ITEM_BASELINE `f4c98b853f229d3eb459765e8e9d3b9295e87043`; target digest at dispatch `3431cd8de10463bf40172dedc6a25fa15b09c18f`; workspace `<scratch>/hunt-ws/utils-querysets`.
    - Iteration: 1 — Worker 0 evidence table: package imported from `<scratch>/hunt-ws/utils-querysets/django_strawberry_framework/__init__.py` (re-printed by Worker 0 from inside the workspace, not taken on report); database target in-workspace; 4 + 18 tests collected, 0 setup-only errors; depended-on digest at run `3431cd8de10463bf40172dedc6a25fa15b09c18f` = digest at dispatch; positive control fails for the intended reason and passes for the concrete-target case; every claim carries a record link and a reach assertion (`_prefetch_relation_target_or_none(...) is _ProxyCategory`). No `invalid` and no `inconclusive` row fired; passed to Worker 2.
    - Iteration: 1 — Worker 2 dispatched expectation-first: phase 1 withheld Worker 1's diagnosis, the working-tree target, the item diff and Worker 1's workspace; Worker 2 recorded its expectation at `<scratch>/verify/expectation.md`, digest `238f5d024991004834b6c9c72942c32365549916`, before phase 2 handed over the diagnosis and the diff.
    - Defect: `_sealed_prefetch_related_lookups` compared the prefetch child's CONCRETE model against the DECLARED relation target. `_concrete_or_none` always reduces the child, while `_prefetch_relation_target_or_none` returns the raw `related_model`, which for a relation declared to a proxy model is the proxy class. `issubclass(<concrete>, <proxy of that concrete>)` is never true, so every prefetch child of a proxy-targeted relation failed the outer seal closed as `untrusted` -- including the relation's own proxy -- against the docstring's own promise that the check "must never fail-close a prefetch path Django supports". `optimizer/walker.py` keys its prefetch child on `field.related_model`, so the framework's own optimizer synthesised the refused shape with no consumer mistake.
    - Severity: Medium. Reachability: any read selecting a proxy-targeted relation, including through the optimizer with no hand-written `Prefetch`. Actor prerequisites: none. Likelihood: moderate. C/I/A: Availability only -- it fails closed, so no confidentiality or integrity loss. Blast radius: per-schema, every read of the affected path. Confidence: high, reproduced and failability-proved in both directions by two independent workspaces. No CVSS claimed.
    - Result: Fixed Medium. Files changed: `django_strawberry_framework/utils/querysets.py` (`::_sealed_prefetch_related_lookups` -- both operands reduced to their concrete model via the existing `_concrete_or_none`, docstring and inline comment restated to the concrete-table invariant), `tests/utils/test_querysets.py` (three rows: `test_prefetch_child_for_proxy_targeted_relation_seals[proxy]`, `[concrete]`, and the non-widening control `test_prefetch_child_over_unrelated_table_still_fails_for_proxy_target`). Validation: `uv run pytest tests/utils/test_querysets.py --no-cov -n0 -q` -> 319 passed, 3 failed, the 3 being the pre-existing HEAD failures recorded below; failability by reverting the production hunk in the workspace -> the two new rows fail, restored byte-identical, re-run passes; `uv run ruff format .` unchanged, `uv run ruff check --fix .` clean.
    - Verification: Passed. Expected-before-diagnosis: both the proxy-child and concrete-child cases must seal to `(plain QuerySet, None)` with a rebuilt exact `Prefetch` over a sealed child, because a proxy and its concrete model are one table and one row set, so refusing either is what the fail-closed prohibition forbids; predicted cause = asymmetric normalization of the two operands; predicted fix = reduce both to concrete and keep `issubclass` so the MTI-subclass direction still passes, without widening. Evidence: fresh workspace `<scratch>/hunt-ws/utils-querysets-verify`, package `__file__` and database `NAME` printed from inside it, run-time digests `f832cd25ed5b71e2470730e4a2b93bae02e0d29a` / `b78c436e2275c96d02b158c97ed0e3c9642cbb23`; 37 independently written probes across 5 modules, 37 collected / 37 passed / 0 skipped / 0 errors / exit 0 / 3.04s; positive control = reverting the one production expression in the verifier's workspace only -> 11 failures including both new parametrizations, restored byte-identical, re-run green; non-widening held for an unrelated model, a proxy of a DIFFERENT concrete model, a distinct concrete class on the same `db_table`, and both MTI directions; admission held for proxy, concrete, second proxy of the same concrete, proxy-of-proxy, O2O, M2M, self-referential, both reverse spellings, multi-segment and nested paths; the admitted prefetch was proved to actually FETCH the right rows against a seeded table, which the permanent tests do not cover; owner confirmed sole site by sweeping every `related_model` reader and every model-class `issubclass` in the package; one permitted shared-tree run `uv run pytest tests/utils/test_querysets.py --no-cov -n0 -k proxy` -> 4 passed, shared tree otherwise untouched. Cells covered: CPython 3.14.2 / Django 6.1 / SQLite / sync. `unverified`: Django floor, Postgres, `FAKESHOP_SHARDED=1`, ASGI transport.
    - Cleanup: Removed `<scratch>/hunt-ws/utils-querysets`, `<scratch>/hunt-ws/utils-querysets-verify` and `<scratch>/failability/` by explicit path. Retained `<scratch>/verify/` (the pre-diagnosis expectation record) and `<scratch>/headcheck/` (the pristine-HEAD archive backing the open item below) because both back findings Rio has not yet ruled on. No `docs/bug_hunt/temp-tests/` directory was created by this item. Unrelated work preserved: every path in `## Cycle baseline` is untouched, and `examples/fakeshop/db.sqlite3` went dirty mid-item from a concurrent session and was left exactly as found.
    - docs/shadow/current/django_strawberry_framework__utils__querysets.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__querysets.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/querysets.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__querysets.stripped.py and docs/shadow/current/django_strawberry_framework__utils__querysets.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/utils/relations.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__utils__relations.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__relations.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/relations.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__relations.stripped.py and docs/shadow/current/django_strawberry_framework__utils__relations.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/utils/sessions.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__utils__sessions.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__sessions.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/sessions.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__sessions.stripped.py and docs/shadow/current/django_strawberry_framework__utils__sessions.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/utils/strings.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__utils__strings.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__strings.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/strings.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__strings.stripped.py and docs/shadow/current/django_strawberry_framework__utils__strings.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/utils/typing.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__utils__typing.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__typing.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/typing.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__typing.stripped.py and docs/shadow/current/django_strawberry_framework__utils__typing.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/utils/write_transaction.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__utils__write_transaction.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__write_transaction.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/write_transaction.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__write_transaction.stripped.py and docs/shadow/current/django_strawberry_framework__utils__write_transaction.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/utils/write_values.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__utils__write_values.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__write_values.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/write_values.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__write_values.stripped.py and docs/shadow/current/django_strawberry_framework__utils__write_values.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

- [ ] django_strawberry_framework/views.py
    - Status: pending
    - docs/shadow/current/django_strawberry_framework__views.stripped.py
    - docs/shadow/current/django_strawberry_framework__views.overview.md
    - Prompt:
        - Use django_strawberry_framework/views.py as the entry point. Read docs/shadow/current/django_strawberry_framework__views.stripped.py and docs/shadow/current/django_strawberry_framework__views.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.

## Scenarios

- [ ] Scenario: Pagination window semantics
    - Status: pending
    - Prompt:
        - connection.py, keyset.py, relay.py: cursor round trips fix schema, order and key context; first/last/after/before algebra; a bigger document never charges less on a named charge dimension. Hunt the contract across every entry point; implement every confirmed root-cause fix.

- [ ] Scenario: Authorization and visibility across actors
    - Status: pending
    - Prompt:
        - utils/querysets.py seal, mutations/permissions.py, resource_policy.py, optimizer/_context.py: forbidden rows absent across actor switches, prefetch and reverse relations, cache reuse across executions, awaitable truthiness, point-in-time authorization. Hunt the contract across every entry point; implement every confirmed root-cause fix.

- [ ] Scenario: Transaction and session lifecycle under interruption
    - Status: pending
    - Prompt:
        - utils/write_transaction.py, the three write pipelines, consumers.py: locks, rollback, commit hooks, cancellation, sync_to_async boundaries, failure during failure handling. Hunt the contract across every entry point; implement every confirmed root-cause fix.

## Integration and final gate


- [ ] Package integration
    - Status: pending
    - Prompt:
        - Hunt the final live package across boundaries, including public exports and `__init__.py` files; implement every confirmed root-cause fix.

- [ ] Final test gate
    - Status: pending
    - Owner: Worker 0
    - Prompt:
        - Run `uv run pytest`; require a passing suite and 100% configured package coverage.

## Owned changes

Path, item, symbols for every tracked edit or new file a verified item landed. A later item may build on a path listed here; any other dirty hunk is external.

| Path | Item | Symbols |
|---|---|---|
| `django_strawberry_framework/utils/querysets.py` | `utils/querysets.py` | `::_sealed_prefetch_related_lookups` (relation-target comparison, its docstring and its inline comment) |
| `tests/utils/test_querysets.py` | `utils/querysets.py` | `::test_prefetch_child_for_proxy_targeted_relation_seals`, `::test_prefetch_child_over_unrelated_table_still_fails_for_proxy_target`, and the module-level `managed = False` fixture models they declare |

No new files. `examples/fakeshop/db.sqlite3` is NOT in this ledger: it went dirty mid-item from a concurrent session, no item touched it, and it is external work.

## Open for Rio

Recorded, not acted on. This run's scope was the single `utils/querysets.py` item, so neither of these was hunted or fixed.

1. **Three pre-existing test failures at the baseline commit, and a coverage hole behind them.** `tests/utils/test_querysets.py::test_reject_async_iterable_in_sync_context_names_the_flavor`, `..._passes_sync_sources` and `..._noop_under_async_execution` fail at pristine `92e4efeb`. Both workers reproduced them independently, Worker 2 from a clean `git archive 92e4efeb` tree, so they predate this hunt and are not caused by the fix above. Commit `92e4efeb` made `async_executor` a required keyword-only argument of `reject_async_iterable_in_sync_context`; both live callers (`django_strawberry_framework/fields/connection.py`, `django_strawberry_framework/fields/list_field.py`) pass it, so production is correct and this is a stale-test gap that commit left behind. It is not cosmetic: because those three tests error, `django_strawberry_framework/utils/querysets.py` sits at 99% with the whole `reject_async_iterable_in_sync_context` region uncovered, so the final gate will fail on both the suite and the 100% coverage requirement. Needs its own item; no worker in this run was authorized to repair another commit's tests.
2. **Live-tier fixture gap for the prefetch relation-target family.** The two new rows landed at package tier in `tests/utils/test_querysets.py`, where all eleven pre-existing rows of this contract already live. Worker 2 ruled accept for this item and Worker 0 did not override it. The reason the live tier is unreachable is a fixture gap, not unreachability: fakeshop declares no relation targeting a proxy model, and `ProxyBranch` is deliberately unexposed. Promoting would need a new example model, a migration, a registered `DjangoType` and a write to the tracked `db.sqlite3` -- a design decision with its own blast radius. Per START.md "Item routed forward w/o NAMED owner dies", this needs a NAMED card before the hunt closes; Worker 0 did not create one because board edits write the concurrently-dirty `examples/fakeshop/db.sqlite3` and are Rio's.
3. **Unvalidated lead, offered with provenance, never a result.** Worker 2 noticed `django_strawberry_framework/types/finalizer.py #"not issubclass(definition.model, set_model)"` is a structurally similar declared-vs-concrete comparison on the FilterSet/OrderSet owner binding. It is outside this item's contract row, and START.md "Verified and rejected" already covers adjacent FilterSet seeding behavior. Not probed.

## Outcomes

Filled by Worker 0 at closeout before any scratch is removed. This run is NOT closed out: by maintainer instruction it hunted exactly one item and stopped before the package integration item and the final gate, both of which remain `pending`, so `Status:` stays `in-progress` and no whole-package clearance is claimed.

One item reached a terminal status.

- **Fixed:** `django_strawberry_framework/utils/querysets.py` -- proxy-targeted prefetch relation refused fail-closed. Medium, factors on the item. Owner file `django_strawberry_framework/utils/querysets.py::_sealed_prefetch_related_lookups`, the sole site in the package carrying the asymmetry. Permanent tests at package tier in `tests/utils/test_querysets.py`. Evidence records: Worker 1 target digest `3431cd8de10463bf40172dedc6a25fa15b09c18f` at probe time; Worker 2 run-time digests `f832cd25ed5b71e2470730e4a2b93bae02e0d29a` and `b78c436e2275c96d02b158c97ed0e3c9642cbb23`, pre-diagnosis expectation `238f5d024991004834b6c9c72942c32365549916`.
- **Scenarios:** none hunted, none appended. No report named a cross-file contract lacking a standing scenario item; the optimizer reachability finding falls under standing scenario 2, which already names `utils/querysets.py` and remains `pending`.
- **Stale re-verifications:** none. No verified item's digests moved.
- **Cells covered:** CPython 3.14.2 / Django 6.1 / SQLite / sync. **`unverified`:** Django floor, Postgres, `FAKESHOP_SHARDED=1`, ASGI transport -- none authorized for this run.
- **Unexamined scope:** every other file item, all three standing scenario items, the package integration item and the final gate. They were never dispatched.
- **Gate record:** not run, by instruction. See "Open for Rio" item 1 for a known blocker.
- **Net source change vs cycle baseline:** two tracked files, `+74 / -4`, both in the ledger above.
- **Concurrent work:** untouched. Every path in `## Cycle baseline` is as found; `examples/fakeshop/db.sqlite3` went dirty mid-run from another session and was left alone; `docs/bug_hunt/bug_hunt-0_0_15.md` and `docs/bug_hunt/bug_hunt-0_0_1555.md` were never opened or written.
