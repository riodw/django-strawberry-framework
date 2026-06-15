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
