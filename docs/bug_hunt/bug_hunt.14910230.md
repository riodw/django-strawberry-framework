# Distilled Dicta: django_strawberry_framework
Use these prompts to explore one file at a time. They are priorities for investigation, not pass/fail rules; escalate only defects confirmed against the original source. This dicta is distilled from the `0.0.10` permissions/cascade build cycles (Slices 1-5 + integration + final gate) and reflects the concrete pitfalls those cycles actually hit: the cascade foundation, optimizer cooperation, composition pins, products activation, and the doc/card wrap.

## Probing Questions for Code Exploration
The hunter should ask these questions while reading each file, focusing on exploration and hidden defects rather than simple checklist confirmation.

### 1. Cascade Walk Correctness & The Single-Source-of-Truth Predicate
- **Is "cascadable edge" defined in exactly one place?** The walk and the `fields=` validator must both derive their edge set from one `_is_cascadable_edge` predicate — does any branch re-enumerate edges with its own rules, letting validation and the walk silently drift out of lock-step (under- or over-cascading)?
- **Does the scope predicate hold the line at single-column forward FK / OneToOne?** Does `getattr(field, "column", None) is not None` (not a bare `hasattr`) actually exclude Django-6 M2M / `GenericRelation` whose `column` is `None`? Are reverse FK, reverse OneToOne, `GenericForeignKey`, composite-PK, and the MTI `<parent>_ptr` parent-link edge excluded *by construction* rather than by enumeration?
- **Does calling `apply_cascade_permissions(type, qs, info)` directly actually narrow anything?** The function cascades through the model's *forward FK edges* — it does NOT invoke the type's own `get_queryset` hook. On a chain-top model with no cascadable forward FK (e.g. `Category`), is this call a silent no-op returning every row? (This bit a Slice-3 gate pin: narrowing must come from the hook-invocation path `type.get_queryset(qs, info)`, or from a model that genuinely has a cascadable forward FK.)
- **Is the FK constraint composed as an unevaluated `__in` subquery?** Does the walk build `Q(<fk>__in=target_qs) | Q(<fk>__isnull=True)` and leave `target_qs` unevaluated, or does some path call `list(...)` / iterate the target queryset and add a round-trip per edge?
- **Is the nullable-FK disjunct present and load-bearing?** Without `Q(<fk>__isnull=True)`, do NULL-FK rows wrongly drop when the target hook hides everything? (Note: an ORM mirror that omits the `OR isnull` term is only equivalent when the FK is non-nullable — is that assumption actually true for the model under read?)
- **Is the target subquery pinned to the caller's resolved alias?** Does the per-edge base use `related_model._default_manager.using(queryset.db).all()` — `_default_manager` (not `.objects`), and `queryset.db` the *resolved* property (not `_db`)? Under a `.using("shard_b")` caller, does the subquery actually land on that alias?

### 2. Cycle Guard, ContextVar, & Async/Sync Parity
- **Does the `_cascade_seen` ContextVar reset in a `finally` on the root frame — including on exception?** After a root call that raises mid-walk (a reached target hook raising), is the var back to `None`? Does request isolation hold under both WSGI and ASGI?
- **Does each frame discard its own class on exit so sibling edges to the same target both cascade?** Does re-entry on a class already in the seen-set return the partially-narrowed queryset *without raising* (partial narrow, never a `RecursionError`)?
- **Is there exactly one walk implementation?** Is `aapply_cascade_permissions` a `sync_to_async(thread_sensitive=True)` wrap of the *public* sync entry (so the ContextVar install/reset runs inside the asgiref-copied worker thread and never leaks back to the event-loop task), or has a parallel async walk been forked that could drift?
- **Does an async target hook reached from the sync walk raise `SyncMisuseError` with the coroutine closed?** Is the sync-misuse probe delegated to `utils/querysets.py::apply_type_visibility_sync` (one place runs a sync `get_queryset` and rejects an async hook), or has a second `iscoroutine`/`close`/raise site been re-implemented inline that could drift on a data-leak-routing decision?
- **Does the seen-set key on the class object?** A secondary type and its primary are distinct classes — does a cascade rooted on a secondary type that re-reaches its own model resolve via `registry.get` to the *primary* hook and still terminate?

### 3. Optimizer Cooperation & Query-Shape Stability
- **Does the optimizer downgrade `select_related → Prefetch` on hook *presence*, not hook behavior?** Is the downgrade (and `cacheable = False`, and FK-id-elision fallback) keyed on `has_custom_get_queryset()` / `_target_has_custom_get_queryset` — a *plan-time, user-independent* decision? Beware reasoning that "staff short-circuits the hook so the JOIN stays" — the downgrade fires on hook presence regardless of runtime return (this exact premise was false in a Slice-4 plan).
- **Does `_build_child_queryset` thread the live `info` into the nested cascade hook?** If `info` were dropped (passed as `None`), would a `Prefetch` still be planned while transitive narrowing silently broke? A "a Prefetch exists" assertion is non-distinguishing here — does the test actually pin that the request user reaches the nested hook?
- **Does the cascade genuinely add zero round-trips?** Do the nested `__in` subqueries compile inline into the caller's single `SELECT`? Is an absolute query count derived from a real run (not a bare `cascaded == uncascaded` equality), and is it guarded by an `"IN (SELECT"` presence check so a silently-empty walk (which also runs in one query) can't pass?
- **Are plans embedding a cascading hook uncacheable without contaminating ordinary plan caching?** Do non-cascading sibling types keep their B1 hit/miss counters intact?

### 4. Composition Across Pipelines, Gates, & Nested Relations
- **Does the cascade narrow rows first, and the `check_<field>_permission` gates judge input second?** Does a field-gate denial fire on input shape *independent* of whether cascade-hidden rows exist — i.e. is the denial error byte-identical with hidden rows present vs absent (no existence leak)?
- **Does a cascade-hidden *non-nullable* forward FK make the parent row drop, rather than nesting a clean `null`?** A non-null GraphQL field resolving to `None` is a null-violation (`'Item has no category.'`), and `Meta.nullable_overrides` is scalar-only — so forward-FK transitivity is observed by the *parent dropping*, while a to-many list narrows cleanly. Is a test or resolver assuming a forward-FK target nulls out?
- **Do connection `edges` and `totalCount` narrow together?** Is `totalCount` the post-visibility count (seeded so `narrowed != raw`, else the assertion is vacuous)? Do node/nodes refetch of a cascade-hidden row return `null` / a positional null hole with no error?
- **Did any composition behavior require editing `filters/`, `orders/`, `connection.py`, `relay.py`, or `list_field.py`?** The contract is that these honor a cascading `get_queryset` through their *existing* seams — is a source edit masking a seam that doesn't actually compose?

### 5. Consumer Context, Permission Resolution, & Activation Drift
- **Does the hook read the request user the way the live context actually exposes it?** The stock `StrawberryDjangoContext` is a dataclass with `request`/`response` and **no `.user`** — does a hook read `info.context.user` (binding `None`, silently collapsing every staff/`has_perm` branch into the anonymous path), or the canonical `getattr(getattr(info.context, "request", None), "user", None)` that `utils/permissions.py::request_from_info` and the shipped gates use?
- **Do the same broken `info.context.user` forms still lurk in teaching examples?** Are the GLOSSARY `get_queryset` visibility-hook example, `TODAY.md`'s `ItemType` demo, or `GOAL.md` showcase bodies still showing the form that binds `None` against the stock context? A copy-pasted broken example silently grants nobody staff/perm visibility.
- **Do the seeders actually default to public-only?** `seed_data` makes Category/Property `is_private` a deterministic `% 2` 50/50 split and Item/Entry privacy `random.choice([True, False])` — so any anonymous-running assertion that counts full sets or first-by-id rows is at risk once hooks activate. Is an expected row set hardcoded, or re-derived through the equivalent post-cascade ORM query (API == ORM) so it survives the random split?
- **Is a test that asserts a query count keyed off a staff client?** `force_login` adds session + user-lookup queries inside `CaptureQueriesContext` — does a count-sensitive pin stay anonymous to avoid auth-query pollution, reserving staff only for row-content full-set assertions?

### 6. Test Integrity, Isolation, & Placement
- **Does an in-process schema fixture re-register its app schema before composing `config.schema`?** A fixture that `importlib.import_module("config.schema")` returns a *cached, stale* module if a sibling live suite cleared the registry and reloaded only its own app — so a cascading type's `get_queryset` silently drops from the composed schema (the deterministic cross-tree isolation defect the final gate caught). Does the fixture reload its own schema module first, mirroring the live suite's full reload discipline?
- **Could a full-set assertion be *masking* a missing nested narrowing?** A pre-existing test that asserts the un-narrowed full set can hide a real isolation bug (private nested rows leaking through an un-narrowed Prefetch child); does narrowing the expectation expose it?
- **Is the duplicated cascading-schema scaffold genuinely a per-context variant, or a blind copy?** The per-file `_exclude_private` hook bodies and `_make_cascading_item_node` helpers differ by signature, return shape, and harness wiring — is a proposed shared fixture actually *more* surface (≥4 params, cross-file registry-lifecycle coupling) than the local 2-line hook it replaces? Test-locality and per-file `registry.clear()` isolation often outweigh DRY for trivial test scaffolding.
- **Are tests placed and isolated correctly?** Is new scratch work under `docs/builder/temp-tests/<slice>/` (and deleted with `rm`, never `git checkout`)? Does an autouse fixture assert `_cascade_seen` is clean at teardown so a leaked seen-set fails the test rather than flaking a sibling?
- **Is the load-bearing property pinned, or just the wire result?** Where a non-cascade path could produce the same wire output, is the distinguishing property (post-visibility count, child-SQL carries the request user, `IN (SELECT` present, narrowing flips when the hook is removed) actually asserted?

### 7. Public API, Generated Docs, & Comment/Spec Drift
- **Are the only `__all__` growths the two spec-authorized cascade symbols?** Is the `tests/base/test_init.py` exports pin the *only* version-frozen file touched, with `__version__` untouched at `0.0.9` (the joint cut owns the bump — no `## [0.0.10]` heading, only `[Unreleased]`)?
- **Are generated docs edited via the DB + regenerate, never by hand?** `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html` render from `examples/fakeshop/db.sqlite3` — a hand-edit silently reverts on the next regenerate, and a raw SQL insert skips the `post_save` side-row. Is the DB the source of truth, and does a second regenerate produce a byte-clean diff?
- **Does a terms-CSV duplicate anchor hard-fail the card close?** `check_spec_glossary` tolerates dual rows sharing an anchor, but `import_spec_terms::_load_rows` raises `CommandError` on the duplicate — does a shared-entry symbol (e.g. `aapply_cascade_permissions` documented inside `apply_cascade_permissions`) carry one CSV row, not two?
- **Does the prose describe the *final* behavior?** Does the GLOSSARY/CHANGELOG/docstring scope read "single-column forward FK / OneToOne" (never "FK / M2M")? Do stale card-body refs (`docs/spec-permissions.md` vs `docs/spec-034-permissions-0_0_10.md`, FieldSet `044` vs `046`) get fixed in *one* cross-surface sweep rather than partial-fixed?
- **Is a reused error message accurate-but-generic on the new surface?** The `SyncMisuseError` text names "the Relay node defaults" while serving three surfaces (Relay defaults, list-field defaults, cascade) — is that misleading enough to justify touching shared source, or is the reuse correct and the message merely non-specific?

## Severity Calibration Priorities
The hunter should prioritize findings by severity, escalating confirmed critical issues immediately and documenting maintainability issues with clear follow-up conditions.

### Priority 1: High (Data-Visibility Correctness, Security, & API Stability)
- A hook reading the request user from a context attribute that is always `None` (e.g. `info.context.user` against the stock `StrawberryDjangoContext`) — collapsing staff/permission branches into the anonymous path is a silent data-visibility-correctness defect, not cosmetic.
- A cascade walk that fails to narrow (a no-op direct call on a chain-top model, a dropped `info` breaking transitivity, a missing `__isnull` disjunct wrongly dropping NULL-FK rows, or a missing alias pin querying the wrong DB).
- An existence leak: a gate denial whose error differs depending on whether a cascade-hidden row exists.
- Cycle-guard failures: a `RecursionError`, a non-reset `_cascade_seen` ContextVar leaking across requests, or a raise where a partial-narrow is required.
- A test-isolation defect where a stale composed schema drops a cascading hook (cross-tree pollution), or a full-set assertion masking a real nested-narrowing leak.
- `__all__` / public-surface or `__version__` changes outside spec authorization; a duplicate-anchor CSV that blocks the canonical card close.

*Action:* Fix the root cause directly and back it with a robust, permanent pinning test unless the finding itself proves a test is impossible. Prefer the lowest-surface root-cause fix (e.g. align to `request_from_info` convention) over a non-canonical shim.

### Priority 2: Medium (Performance, Query-Shape, & Fragility)
- A cascade that adds query round-trips (materialized target querysets, `list(...)` on a subquery) instead of composing inline `__in` subqueries.
- Query-shape pins that aren't distinguishing: a bare `cascaded == uncascaded` count, a "Prefetch exists" assertion that survives a dropped `info`, or a `totalCount` seeded so `narrowed == raw`.
- Expected row sets hardcoded against the random `is_private` seeder split instead of re-derived through the post-cascade ORM (API == ORM).
- Comment/spec/doc drift on a public-contract symbol: a "FK / M2M" scope error, a stale spec filename or card number, a broken `info.context.user` teaching example a consumer would copy.
- Generated-doc divergence (DB vs committed rendered file) that a regenerate would revert.

*Action:* Address during implementation when local to the prompted file, or record the exact sibling/spec dependency that blocks a one-file fix. Treat broken consumer-facing examples on a documented surface as more than cosmetic.

### Priority 3: Low (Locality, Clarity, & Polish)
- Per-file test-scaffold duplication (a 2-line cascading hook, a per-context `_make_cascading_item_node`) where test-locality and registry-isolation outweigh a shared fixture — note it, do not force consolidation.
- A reused error message that is accurate but non-specific on a new surface (the `SyncMisuseError` "Relay node defaults" text on the cascade path), where the pinned test asserts type-name + error + closed-coroutine, not the recourse wording.
- Minor naming, typing, or comment polish that does not alter behavior.

*Action:* Polish inline when safe and scoped, or frame with a clear, verbatim **trigger condition** (for example, *"hoist the shared cascading-schema fixture only if a fourth file rebuilds it"* or *"generalize the SyncMisuseError message only if a fourth surface reuses it"*) so future passes can find and consolidate it.

## How to review a single file
Each prompt below targets exactly one source file. Treat it as a focused
review pass, not a tour:

- Read the `.overview.md` shadow first. It is a structural index -
  quick-scan counts, imports, symbols, control-flow hotspots, executable
  Django/ORM marker lines, calls of interest, and repeated executable
  string literals - pulled from the AST without executing the file. Use
  it to plan the read, not as the source of truth.
- Read the `.stripped.py` shadow next. Comments and docstring statements
  are removed, and other string literals are replaced, so the executable
  structure is easier to scan. **Line numbers in the stripped file are
  not canonical.** Cite original source-file line numbers in every
  finding and every fix.
- Open the original source file alongside (named in the prompt) and
  reconcile the shadow view against the real code before declaring a
  defect.
- Confirm every defect against the actual source. No speculation, no
  "this might be wrong". If you cannot reproduce the failure shape
  mentally or with a quick read, drop the finding and move on. Silence
  on a marker line is acceptable; speculative defects pollute the
  checklist.

For each confirmed defect:

- Classify severity using the criteria in the dicta header above.
- Edit the original source file directly. Stay within the file the
  prompt names - if the fix needs sibling changes, surface that as a
  question rather than expanding the diff unilaterally.
- For **High**-severity fixes, add or update a test that pins the
  corrected behavior under the correct test tree per AGENTS.md
  "Test placement is mandatory". Do not rely on validation alone.
- For **Medium** / **Low** fixes that change a documented contract,
  update the relevant docstring or comment in the same pass so the
  prose matches the final behavior.
- Run `uv run ruff format <file>` and `uv run ruff check <file>` on
  any source file you touched.

When the file is done, tick its checkbox `- [x]` so the next prompt is
obvious.

## Per-file prompts

- [x] django_strawberry_framework/_django_patches.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/test_django_patches.py -q → 12 passed; upstream-fidelity + API-surface probes confirmed against live Django 6.0.5.
    - docs/shadow/current/django_strawberry_framework___django_patches.stripped.py
    - docs/shadow/current/django_strawberry_framework___django_patches.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework___django_patches.stripped.py and docs/shadow/current/django_strawberry_framework___django_patches.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/_django_patches.py

- [x] django_strawberry_framework/apps.py
    - Result: No issues. Files changed: none; validation: confirmed AppConfig.name matches package dir and ready() lazy-imports the idempotent _django_patches.apply (target present); no cascade/context-user concerns apply.
    - docs/shadow/current/django_strawberry_framework__apps.stripped.py
    - docs/shadow/current/django_strawberry_framework__apps.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__apps.stripped.py and docs/shadow/current/django_strawberry_framework__apps.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/apps.py

- [x] django_strawberry_framework/conf.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/base/test_conf.py -q → 17 passed; verified recursion-safe __getattr__, normalization branches, lazy-load/reload contract, and setting_changed wiring.
    - docs/shadow/current/django_strawberry_framework__conf.stripped.py
    - docs/shadow/current/django_strawberry_framework__conf.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__conf.stripped.py and docs/shadow/current/django_strawberry_framework__conf.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/conf.py

- [x] django_strawberry_framework/connection.py
    - Result: No issues. Files changed: none; validation: read-only reconciliation against utils/querysets.py, optimizer/plans.py, types/resolvers.py; confirmed visibility-hook routing single-sited, async-count awaits before guard-raise (ResourceWarning-safe), window cursor math and _check_n1 signature correct.
    - docs/shadow/current/django_strawberry_framework__connection.stripped.py
    - docs/shadow/current/django_strawberry_framework__connection.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__connection.stripped.py and docs/shadow/current/django_strawberry_framework__connection.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/connection.py

- [x] django_strawberry_framework/exceptions.py
    - Result: No issues. Files changed: none; validation: grep over package confirmed all exception importers resolve to the three defined names; __all__ matches defined symbols, hierarchy and docstrings correct.
    - docs/shadow/current/django_strawberry_framework__exceptions.stripped.py
    - docs/shadow/current/django_strawberry_framework__exceptions.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__exceptions.stripped.py and docs/shadow/current/django_strawberry_framework__exceptions.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/exceptions.py

- [x] django_strawberry_framework/filters/base.py
    - Result: No issues. Files changed: none; validation: uv run python -m pytest tests/ -k filter -q → 283 passed; reconciled ArrayFilter/ListFilter empty-value short-circuits, _target_definition_for routing, globalid strategy mapping, and RelatedFilter mixin wiring against sibling APIs.
    - docs/shadow/current/django_strawberry_framework__filters__base.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__base.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__filters__base.stripped.py and docs/shadow/current/django_strawberry_framework__filters__base.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/filters/base.py

- [x] django_strawberry_framework/filters/factories.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/filters/test_factories.py -q → 22 passed; confirmed cache-key/hashability logic (dict-branch sort asymmetry unreachable since fields keys are unique strings), reserved-kwarg strip, and normalization paths.
    - docs/shadow/current/django_strawberry_framework__filters__factories.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__factories.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__filters__factories.stripped.py and docs/shadow/current/django_strawberry_framework__filters__factories.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/filters/factories.py

- [x] django_strawberry_framework/filters/inputs.py
    - Result: No issues. Files changed: none; validation: pytest tests/filters/test_inputs.py → 62 passed, tests/filters + fakeshop → 273 passed; verified isinstance-ladder ordering parity (no primitive overlap), relation-walk, enum-unwrap, global-id re-encode, and range-cache paths via live hierarchy probes.
    - docs/shadow/current/django_strawberry_framework__filters__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__inputs.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__filters__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__filters__inputs.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/filters/inputs.py

- [x] django_strawberry_framework/filters/sets.py
    - Result: No issues. Files changed: none; validation: uv run ruff check (informational) → passed; confirmed canonical request_from_info user resolution, single-sited sync-misuse delegation, permission double-dispatch + dedup + recursion, and unevaluated pk__in subquery related-constraint build. Note (not a defect): _iter_visibility_steps does not thread parent DB alias into child_base; scoped to the FilterSet path, not the cascade walk.
    - docs/shadow/current/django_strawberry_framework__filters__sets.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__sets.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__filters__sets.stripped.py and docs/shadow/current/django_strawberry_framework__filters__sets.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/filters/sets.py

- [x] django_strawberry_framework/list_field.py
    - Result: No issues. Files changed: none; validation: read-only grep confirmed imported utils/querysets symbols match signatures; verified async/sync dispatch parity, info threading, strict origin-based own-class guard, and default-resolver QuerySet contract.
    - docs/shadow/current/django_strawberry_framework__list_field.stripped.py
    - docs/shadow/current/django_strawberry_framework__list_field.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__list_field.stripped.py and docs/shadow/current/django_strawberry_framework__list_field.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/list_field.py

- [x] django_strawberry_framework/management/commands/export_schema.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/management/test_export_schema.py -q → 5 passed; verified Schema isinstance guard and all three --path branches (stdout / empty-string CommandError / file write) plus OSError wrapping. Minor non-actionable docstring attribution note (Priority 3, no trigger).
    - docs/shadow/current/django_strawberry_framework__management__commands__export_schema.stripped.py
    - docs/shadow/current/django_strawberry_framework__management__commands__export_schema.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__management__commands__export_schema.stripped.py and docs/shadow/current/django_strawberry_framework__management__commands__export_schema.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/management/commands/export_schema.py

- [x] django_strawberry_framework/management/commands/inspect_django_type.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/management + fakeshop inspect tests → 21 passed; verified _resolve_row dispatch order, annotation/type rendering rstrip("!") for scalar+list, nullability, and scalar-name lookup.
    - docs/shadow/current/django_strawberry_framework__management__commands__inspect_django_type.stripped.py
    - docs/shadow/current/django_strawberry_framework__management__commands__inspect_django_type.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__management__commands__inspect_django_type.stripped.py and docs/shadow/current/django_strawberry_framework__management__commands__inspect_django_type.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/management/commands/inspect_django_type.py

- [x] django_strawberry_framework/optimizer/_context.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/optimizer/test_extension.py -k "stash or context" → 16 passed; verified read/write dict-first symmetry, scoped exception tuples (write intentionally not swallowing KeyError), and frozen/mapping shape handling.
    - docs/shadow/current/django_strawberry_framework__optimizer___context.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer___context.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__optimizer___context.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer___context.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/optimizer/_context.py

- [x] django_strawberry_framework/optimizer/extension.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/optimizer/test_extension.py -q → 129 passed; verified cache-key construction, depth-aware AST walk + cycle guard, sync/async resolve gate, on_execute ContextVar reset-in-finally, and union plan semantics.
    - docs/shadow/current/django_strawberry_framework__optimizer__extension.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__extension.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__optimizer__extension.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__extension.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/optimizer/extension.py

- [x] django_strawberry_framework/optimizer/field_meta.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/optimizer/test_field_meta.py -q → 17 passed; verified cardinality-gated nullable rule, FK-id-elision guards (M2M/reverse/composite-PK/unresolved), and reachability of _has_composite_pk's direct _meta read.
    - docs/shadow/current/django_strawberry_framework__optimizer__field_meta.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__field_meta.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__optimizer__field_meta.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__field_meta.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/optimizer/field_meta.py

- [x] django_strawberry_framework/optimizer/hints.py
    - Result: No issues. Files changed: none; validation: behavioral probe confirmed all four hint shapes construct, all conflict combinations rejected by __post_init__, hint_is_skip handles all branches, SKIP sentinel + frozen-dataclass hashing correct; docstring priority order matches walker._apply_hint.
    - docs/shadow/current/django_strawberry_framework__optimizer__hints.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__hints.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__optimizer__hints.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__hints.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/optimizer/hints.py

- [x] django_strawberry_framework/optimizer/plans.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/optimizer/test_plans.py -q → 86 passed; traced _IndexedList dedup, runtime_path_from_path index-skipping, apply_window_pagination range filtering, order-by reversal, and plan-diff reconciliation; reverse-branch missing limit>=0 guard confirmed harmless (last always non-negative).
    - docs/shadow/current/django_strawberry_framework__optimizer__plans.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__plans.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__optimizer__plans.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__plans.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/optimizer/plans.py

- [x] django_strawberry_framework/optimizer/selections.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/optimizer/test_selections.py -q → 14 passed; verified ast_to_converted_selections mirrors Strawberry convert_selections, should_include skip/include identity checks, and direct_child_selected fragment-only recursion.
    - docs/shadow/current/django_strawberry_framework__optimizer__selections.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__selections.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__optimizer__selections.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__selections.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/optimizer/selections.py

- [x] django_strawberry_framework/optimizer/walker.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/optimizer/test_walker.py -q → 119 passed; confirmed downgrade/cacheable/FK-elision keyed on hook presence (plan-time), live info threaded into nested hooks, unevaluated __in composition, and non-mutating alias merge.
    - docs/shadow/current/django_strawberry_framework__optimizer__walker.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__walker.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__optimizer__walker.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__walker.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/optimizer/walker.py

- [x] django_strawberry_framework/orders/base.py
    - Result: No issues. Files changed: none; validation: runtime probe (in /tmp, removed) → ALL PROBES PASSED; verified RelatedOrder mixin parameterization (_orderset/bound_orderset) mirrors filter twin, idempotent owner-bind, lazy target resolution, and .orderset property seam consumed by orders/factories.
    - docs/shadow/current/django_strawberry_framework__orders__base.stripped.py
    - docs/shadow/current/django_strawberry_framework__orders__base.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__orders__base.stripped.py and docs/shadow/current/django_strawberry_framework__orders__base.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/orders/base.py

- [x] django_strawberry_framework/orders/factories.py
    - Result: No issues. Files changed: none; validation: inline smoke test → all assertions passed; verified OrderArgumentsFactory family hooks (fresh per-family dict + distinct _type_orderset_registry), operator-bag omission (Decision 8), and clear-namespace lifecycle references match.
    - docs/shadow/current/django_strawberry_framework__orders__factories.stripped.py
    - docs/shadow/current/django_strawberry_framework__orders__factories.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__orders__factories.stripped.py and docs/shadow/current/django_strawberry_framework__orders__factories.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/orders/factories.py

- [x] django_strawberry_framework/orders/inputs.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/orders/test_inputs.py -q → 40 passed + Book-model field probe; verified Ordering.resolve direction/nulls mapping, column-filter excluding M2M/reverse FK, and related-branch ORM-path (field_name) derivation.
    - docs/shadow/current/django_strawberry_framework__orders__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__orders__inputs.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__orders__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__orders__inputs.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/orders/inputs.py

- [x] django_strawberry_framework/orders/sets.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/orders/test_sets.py -q → 38 passed; verified canonical request_from_info usage, permission target_attr=orderset/related_attr=related_orders wiring, to-many Min/Max aggregate selection, cache-write gate, and async/sync parity.
    - docs/shadow/current/django_strawberry_framework__orders__sets.stripped.py
    - docs/shadow/current/django_strawberry_framework__orders__sets.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__orders__sets.stripped.py and docs/shadow/current/django_strawberry_framework__orders__sets.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/orders/sets.py

- [x] django_strawberry_framework/permissions.py
    - Result: No issues. Files changed: none; validation: ContextVar construction probe ok; verified single _is_cascadable_edge predicate (validator+walk), column-based scope excluding M2M/reverse/parent_link, unevaluated Q(__in)|isnull constraint on resolved alias, root-finally ContextVar reset + per-frame discard cycle guard, and sync_to_async wrap of the single sync entry.
    - docs/shadow/current/django_strawberry_framework__permissions.stripped.py
    - docs/shadow/current/django_strawberry_framework__permissions.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__permissions.stripped.py and docs/shadow/current/django_strawberry_framework__permissions.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/permissions.py

- [x] django_strawberry_framework/registry.py
    - Result: No issues. Files changed: none; validation: uv run python -m pytest tests/ -k registry -q → 82 passed; verified clear() co-clear targets all importable, register rollback snapshot logic, get() ambiguity handling, and intended fail-loud _clear_if_importable scope.
    - docs/shadow/current/django_strawberry_framework__registry.stripped.py
    - docs/shadow/current/django_strawberry_framework__registry.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__registry.stripped.py and docs/shadow/current/django_strawberry_framework__registry.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/registry.py

- [x] django_strawberry_framework/relay.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/test_relay_node_field.py tests/testing/test_relay.py -q → 47 passed; verified visibility delegation (no info.context.user), async/sync awaitable gating, batch decode→typecheck→coerce ordering (no existence leak), and _check_nodes_result 1:1 positional contract.
    - docs/shadow/current/django_strawberry_framework__relay.stripped.py
    - docs/shadow/current/django_strawberry_framework__relay.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__relay.stripped.py and docs/shadow/current/django_strawberry_framework__relay.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/relay.py

- [x] django_strawberry_framework/scalars.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/test_scalars.py -q → 43 passed; probed BigInt regex edge cases (leading-zero/-0/+/underscore/unicode/scientific/whitespace), bool-before-int parse ordering, serialize symmetry, and strawberry_config scalar_map handling.
    - docs/shadow/current/django_strawberry_framework__scalars.stripped.py
    - docs/shadow/current/django_strawberry_framework__scalars.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__scalars.stripped.py and docs/shadow/current/django_strawberry_framework__scalars.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/scalars.py

- [x] django_strawberry_framework/sets_mixins.py
    - Result: No issues. Files changed: none; validation: grep confirmed no class-level default for bound_filterset/bound_orderset (hasattr idempotency guard safe); verified MRO-merge declaration collection, expanded_once reentry guard cleared in finally, and resolve_lazy_class branches.
    - docs/shadow/current/django_strawberry_framework__sets_mixins.stripped.py
    - docs/shadow/current/django_strawberry_framework__sets_mixins.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__sets_mixins.stripped.py and docs/shadow/current/django_strawberry_framework__sets_mixins.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/sets_mixins.py

- [x] django_strawberry_framework/types/base.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/types/test_base.py -q → 112 passed, tests/types + test_permissions → 405 passed/3 skipped; verified identity get_queryset hook, _detect_custom_get_queryset MRO walk + flag/definition agreement, meta/field validators keying, and annotation-inheritance non-pitfall.
    - docs/shadow/current/django_strawberry_framework__types__base.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__base.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__types__base.stripped.py and docs/shadow/current/django_strawberry_framework__types__base.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/types/base.py

- [x] django_strawberry_framework/types/converters.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/types/test_converters.py -q → 53 passed, 2 skipped; verified scalar_for_field MRO walk, convert_scalar null tri-state + sentinel dispatch ordering, member-name sanitization rules, and enum collision detection.
    - docs/shadow/current/django_strawberry_framework__types__converters.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__converters.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__types__converters.stripped.py and docs/shadow/current/django_strawberry_framework__types__converters.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/types/converters.py

- [x] django_strawberry_framework/types/definition.py
    - Result: No issues. Files changed: none; validation: grep/runtime probes confirmed registry methods + _resolve_id_default present; verified related_target_for is the general (correct-by-design) relation resolver distinct from cascade predicate, finalize-gated per-field cache, and relay id-resolver default comparison.
    - docs/shadow/current/django_strawberry_framework__types__definition.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__definition.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__types__definition.stripped.py and docs/shadow/current/django_strawberry_framework__types__definition.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/types/definition.py

- [x] django_strawberry_framework/types/finalizer.py
    - Result: No issues. Files changed: none; validation: import probe OK; verified _synthesize_relation_connections re-entrancy + collision guards, intentional filterset/orderset _meta asymmetry, snake-key field-map consistency, cycle-safe related-filter audit walk, and finalize-last lifecycle.
    - docs/shadow/current/django_strawberry_framework__types__finalizer.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__finalizer.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__types__finalizer.stripped.py and docs/shadow/current/django_strawberry_framework__types__finalizer.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/types/finalizer.py

- [x] django_strawberry_framework/types/relations.py
    - Result: No issues. Files changed: none; validation: isolated probe confirmed __hash__ = object.__hash__ survives frozen-dataclass decorator (identity hashing for unhashable django_field) and discard_pending uses id() identity; pure finalization scaffolding, no cascade surface.
    - docs/shadow/current/django_strawberry_framework__types__relations.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__relations.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__types__relations.stripped.py and docs/shadow/current/django_strawberry_framework__types__relations.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/types/relations.py

- [x] django_strawberry_framework/types/relay.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/types/test_relay_interfaces.py tests/test_relay_node_field.py -q → 160 passed (relay.py 100% line cov); verified visibility delegation (no info.context.user), single-sited sync-misuse probe, decode_global_id error uniformity, and list(qs) materializes narrowed set not a subquery.
    - docs/shadow/current/django_strawberry_framework__types__relay.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__relay.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__types__relay.stripped.py and docs/shadow/current/django_strawberry_framework__types__relay.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/types/relay.py

- [x] django_strawberry_framework/types/resolvers.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/types/test_resolvers.py -q → 27 passed (resolvers.py 98%); verified relation-kind routing (forward/reverse-O2O single vs many-side), accessor-vs-field-name vocabulary, _check_n1 kind passing, and guarded FK-id elision stub.
    - docs/shadow/current/django_strawberry_framework__types__resolvers.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__resolvers.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__types__resolvers.stripped.py and docs/shadow/current/django_strawberry_framework__types__resolvers.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/types/resolvers.py

- [x] django_strawberry_framework/utils/connections.py
    - Result: No issues. Files changed: none; validation: probe over 10 pagination shapes matched documented (offset,limit,reverse) contract incl. after+last → UnwindowableConnection. Note (theoretical, not escalated): reverse/raise guards use `before is None`/`after is not None` vs SliceMetadata truthiness; diverges only for empty-string cursors, which the framework never emits.
    - docs/shadow/current/django_strawberry_framework__utils__connections.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__connections.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__utils__connections.stripped.py and docs/shadow/current/django_strawberry_framework__utils__connections.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/utils/connections.py

- [x] django_strawberry_framework/utils/input_values.py
    - Result: No issues. Files changed: none; validation: invariant probe → basic invariants OK; verified single-sited is_inactive_value rule, dict/dataclass/non-walkable distinction in iter_input_items, guarded related-branch lookups, and disjoint logic/related/leaf marker sets.
    - docs/shadow/current/django_strawberry_framework__utils__input_values.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__input_values.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__utils__input_values.stripped.py and docs/shadow/current/django_strawberry_framework__utils__input_values.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/utils/input_values.py

- [x] django_strawberry_framework/utils/inputs.py
    - Result: No issues. Files changed: none; validation: read-only reconciliation against call sites (filters/inputs, orders/inputs, sets_mixins); verified build_strawberry_input_class kwarg handling, camel-name edge cases, idempotent materialization collision detection, BFS dedup/collision consistency, and namespace clear.
    - docs/shadow/current/django_strawberry_framework__utils__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__inputs.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__utils__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__utils__inputs.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/utils/inputs.py

- [x] django_strawberry_framework/utils/permissions.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/utils/test_permissions.py -q → 8 passed; confirmed request_from_info reads context.request (not info.context.user), per-class dedup parent/child double-dispatch keyed on distinct sets, and fire-then-record dedup ordering.
    - docs/shadow/current/django_strawberry_framework__utils__permissions.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__permissions.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__utils__permissions.stripped.py and docs/shadow/current/django_strawberry_framework__utils__permissions.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/utils/permissions.py

- [x] django_strawberry_framework/utils/querysets.py
    - Result: No issues. Files changed: none; validation: read + existing pin test review + grep for single-sited usage; verified apply_type_visibility_sync closes coroutine before raising SyncMisuseError (iscoroutine precise check), async path awaits via isawaitable, _default_manager (not .objects), and all 8 consumers delegate here.
    - docs/shadow/current/django_strawberry_framework__utils__querysets.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__querysets.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__utils__querysets.stripped.py and docs/shadow/current/django_strawberry_framework__utils__querysets.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/utils/querysets.py

- [x] django_strawberry_framework/utils/relations.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/utils/test_relations.py -q → 11 passed (100% line cov), ruff check + format --check passed; verified relation_kind classification against all live Django 6.0.5 descriptors and instance_accessor three-tier read.
    - docs/shadow/current/django_strawberry_framework__utils__relations.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__relations.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__utils__relations.stripped.py and docs/shadow/current/django_strawberry_framework__utils__relations.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/utils/relations.py

- [x] django_strawberry_framework/utils/strings.py
    - Result: No issues. Files changed: none; validation: python probe over docstring examples + acronym/underscore edge cases → OK; snake_case and pascal_case match documented behavior exactly.
    - docs/shadow/current/django_strawberry_framework__utils__strings.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__strings.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__utils__strings.stripped.py and docs/shadow/current/django_strawberry_framework__utils__strings.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/utils/strings.py

- [ ] django_strawberry_framework/utils/typing.py
    - docs/shadow/current/django_strawberry_framework__utils__typing.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__typing.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__utils__typing.stripped.py and docs/shadow/current/django_strawberry_framework__utils__typing.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/utils/typing.py
