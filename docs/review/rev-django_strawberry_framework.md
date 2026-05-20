# Project review: `django_strawberry_framework/`

Status: verified

## DRY analysis

- None — every package-scope DRY carry-forward already has a trigger condition and is tracked in a folder-pass or per-file artifact: `_walk_selection_tree` (rev-optimizer.md Low 1, trigger "when a third walker lands"); `RelationPlanCtx` (rev-optimizer.md Low 2, trigger "when a planner gains an 11th argument OR a third file outside `walker.py` needs one"); `_resolve_origin_for_type_name` (rev-optimizer__extension.md, trigger "if a third call site lands"); the four-extraction bundle in `rev-types.md` M2 (`_collect_consumer_authored_fields`, `_assert_no_relay_id_collision`, `_apply_id_filter_and_materialize_{single,many}`, `_model_for(type_cls)`) gated on the next `types/base.py` cycle or Relay-resolver behavior change. No new project-scope extraction is justified today; the cross-folder duplication-risk audit (registry "already registered" pluralization, conf.py defensive-None two-seam stance, and stale `convert_relation` references) is tracked under Medium M1 and Lows §1/§2 below.

## High:

None.

## Medium:

### M1 — three remaining stale `convert_relation` references after the spec-014 removal

`types/converters.convert_relation` was removed from `django_strawberry_framework/types/converters.py` in the `rev-types__converters.md` M1 cycle, and `types/__init__.py:6` was de-staled in the `rev-types.md` M1 cycle. Three stale references survive outside the `types/` folder boundary and are explicit carry-forwards to this pass per `rev-types.md:91-93` Low 4 and the converters-cycle "Out-of-scope stale references" list:

1. **`django_strawberry_framework/registry.py:6`** — the module docstring reads "Used by: ``types.converters.convert_relation`` for relation resolution once target types are registered." `convert_relation` is no longer a symbol; the registry's actual current consumer for "relation resolution once target types are registered" is `types/finalizer.py:130-133`'s `resolved_relation_annotation` call at finalize-time (via `iter_pending_relations` / `discard_pending` rather than the eager `registry.get` shape `convert_relation` used). Recommended change: rewrite the bullet to read "``types.finalizer.resolved_relation_annotation`` for relation resolution once target types are registered (called from the per-entry finalize loop via ``iter_pending_relations`` / ``discard_pending``)." The remaining bullet for `convert_choices_to_enum` is still accurate and stays unchanged.

2. **`tests/optimizer/test_extension.py:1859`** — fixture comment reads `# Must register CategoryType first so convert_relation succeeds,`. The fixture itself is correct (it registers `CategoryType` before `ItemType`); only the comment misnames the helper. The fixture is exercising the deferred-resolution path through `_build_annotations` → `PendingRelationAnnotation` → `finalize_django_types`, so the accurate comment is `# Must register CategoryType first so ItemType's category relation resolves at finalize time,`.

3. **`tests/optimizer/test_extension.py:1960`** — fixture comment reads `# Register CategoryType so convert_relation succeeds.` Same fix shape as #2: rename to `# Register CategoryType so the ItemType.category PendingRelation resolves at finalize time.`

These are not behavior bugs (no code path reads the comment text; the docstring at `registry.py:6` is not parsed by anything at runtime), but they are consumer-facing surface drift in the same calibration class as the `rev-types.md` M1 finding ("a stale name in a public docstring after the symbol was removed is consumer-facing surface drift even when `__all__` doesn't list it"). The `registry.py:6` mention is the most visible because the registry module is the bottom of the dependency graph and any consumer reading its docstring sees the wrong cross-module reference; the two test-fixture comments are lower-stakes but live in the package's largest test file and are quoted in every code-search hit a future maintainer runs for `convert_relation`.

Note on **`AGENTS.md:8`**: the same paragraph still reads "converters.py owns convert_scalar, convert_choices_to_enum, convert_relation". Per `AGENTS.md` "Keep dense, package-specific, no code blocks, no code examples" and `START.md` "If updating this file Keep this document as dense as possible, don't even use blank lines or periods. No code blocks." — and the standing rule that `docs/review/` agents do NOT edit `AGENTS.md` (no review-cycle worker may touch the file directly). Flagging here as a maintainer follow-up: the helper-list sentence in `AGENTS.md:8` should drop `convert_relation` next time `AGENTS.md` is otherwise touched, but no review worker should bulk-edit `AGENTS.md` for this cycle. The three in-package fixes (M1 #1, #2, #3) are in scope; the `AGENTS.md` mention is recorded for maintainer awareness only.

Test expectation: none for #1, #2, #3 — every fix is comment / docstring text; no test pins the prior wording (grep across `tests/` for `"convert_relation"` quoted in a string-match returns zero hits — only the two comment-text mentions above). The fixtures themselves still pass.

```django_strawberry_framework/registry.py:1-14
"""Type registry for ``DjangoType`` metadata, pending relations, and choice enums.

Maps Django models to their generated ``DjangoType`` and ``(model,
field_name)`` to generated ``Enum`` classes. Used by:

- ``types.converters.convert_relation`` for relation resolution once
  target types are registered.
- ``types.converters.convert_choices_to_enum`` for enum reuse across
  multiple ``DjangoType`` subclasses reading the same choice column.
...
"""
```

### M2 — `optimizer/extension.py` `_optimize` silently passes through a Manager because of the `isinstance(QuerySet)` gate

`optimizer/extension.py:548` checks `if not isinstance(result, models.QuerySet): return result`. A Django resolver that returns `Model.objects` (the default Manager) rather than `Model.objects.all()` (the QuerySet) — a very common Django shorthand consumers write without thinking — slips past the optimizer entirely. The plan is still built; the queryset is just never optimized because the gate filters out before `diff_plan_for_queryset` / `plan.apply` ever run. `strawberry-graphql-django` defensively coerces `.all()` at the same site for exactly this case. This carry-forward is logged at `rev-optimizer__extension.md` Low 5 and was deferred to the project pass because it touches the package-wide "what shapes can the framework resolve through?" question rather than a single file.

Severity calibration: this IS Medium at project scope, not Low. The "Test through real usage" rule in `AGENTS.md:18-19` is explicit: "Models via Model.objects.create through their managers." Consumers writing `def resolve_items(self) -> list[ItemType]: return Item.objects` (a one-liner shorthand) get a working schema with zero N+1 protection and zero feedback that the optimizer was bypassed — even with `strictness="raise"`, the publish stash at `extension.py:555` does run but the resolver-side check at `types/resolvers.py:179-...` only fires inside a resolver that walks `field_map`, which a Manager-returning root resolver bypasses entirely. The silent-bypass is the same "validates A but not the intersection of A and B" pattern called out in `worker-memory/worker-1.md`'s severity-calibration carry-forward: the optimizer guards against "non-QuerySet result" but not against "Manager that would BECOME a QuerySet under `.all()`".

Two paths, either acceptable:

1. **Coerce `.all()` defensively at the gate.** `result = result.all() if isinstance(result, models.Manager) else result` immediately before the `isinstance(result, models.QuerySet)` check at `extension.py:548`. Behavior-equivalent in every shipped case (the manager's `.all()` returns a QuerySet that has not been evaluated). Matches strawberry-graphql-django's posture. Cheap; one line; preserves the silent-success contract for shorthand-writing consumers.

2. **Document the contract.** Extend the `DjangoOptimizerExtension` class docstring at `extension.py:423-449` with a "Resolver-shape contract" paragraph naming the Manager-vs-QuerySet asymmetry and recommending `.all()` explicitly in resolvers. This is the cheaper-to-implement option but the harder-to-enforce one: a consumer who didn't read the docstring still gets a silent bypass.

Recommended: path (1) — the coercion is one line, cannot return wrong data (a Manager's `.all()` is a fresh QuerySet that has not been evaluated), and aligns with both `strawberry-graphql-django` and the "Test through real usage" framing in `AGENTS.md`. Path (2) without (1) leaves the silent-bypass trap in place.

Test expectation (path 1): add `tests/optimizer/test_extension.py::test_optimize_coerces_manager_through_all` — fixture defines a `Query` type whose `items` field returns `Item.objects` (the Manager, not `Item.objects.all()`), seed via `services.seed_data(1)`, run the schema with the optimizer enabled and assert (a) the result is correctly resolved, (b) `cache_info().misses` increments (the plan was built), and (c) `connection.queries` shows the expected select_related/prefetch_related count from the plan — i.e., the Manager was NOT silently passed through unoptimized.

```django_strawberry_framework/optimizer/extension.py:546-558
        result = await result if asyncio.iscoroutine(result) else result

        if not isinstance(result, models.QuerySet):
            return result
        ...
        selections = convert_selections(info, info.field_nodes)
```

### M3 — `optimizer/extension.py:_collect_schema_reachable_types` does not descend into interface implementations

`_walk_gql_type` at `extension.py:336-363` recurses into `fields` (object types) and `union_types` (`gql_type.types`) but does not follow `gql_type.interfaces` nor enumerate the concrete types implementing an interface returned from a root field. graphql-core exposes implementations via `schema.get_implementations(interface_type)` (graphql-core 3.x) or `interface_type.types` on some versions. If a root field is typed as a GraphQL interface and the only `DjangoType`s involved are the concrete implementations of that interface, `check_schema` silently misses them — they don't appear in `reachable` and don't get audited for `"has no registered target DjangoType"` warnings.

This carry-forward is logged at `rev-optimizer__extension.md` Low 4 and the artifact deferred it to the project pass with the trigger condition "flag at the project pass if interface support lands." Project-pass calibration: interfaces ARE a 0.0.6 surface — `relay.Node` is a GraphQL interface, the `rev-types__relay.md` cycle landed the `_build_annotations` interface-injection path at `types/base.py:740-741`, and the `tests/types/test_relay_*.py` suite pins the interface-implements pattern. The audit's interface-descent gap means `check_schema` already silently misses any `DjangoType` that implements `relay.Node` at a root field where only the interface type is exposed. In practice today every `relay.Node` implementer is also reachable from a non-interface root field (the connection / node resolvers route through the concrete type, not the interface), so the gap is latent — but it is no longer "interfaces are not in the package's example surface today" as the `rev-optimizer__extension.md` artifact phrased the defer-rationale.

Severity calibration: still Medium not High because the gap is silent (no wrong-data risk; the audit just under-reports) and because the implementer-of-interface types are reachable through other paths in every current example. But the project pass IS the right scope to land the fix because (a) interfaces are a 0.0.6 surface (`relay.Node`), and (b) future spec slices (custom interfaces beyond `relay.Node`) would compound the gap.

Two paths:

1. **Extend `_walk_gql_type` to descend into implementations.** After the `union_types` block at `extension.py:359-363`, add:
   ```
   # Recurse into interface implementations.
   if getattr(gql_type, "of_type", None) is None and gql_schema is not None:
       impls = gql_schema.get_implementations(gql_type) if hasattr(gql_schema, "get_implementations") else None
       if impls is not None:
           for impl_type in impls.objects:
               _walk_gql_type(impl_type)
   ```
   The `getattr(gql_type, "of_type", None) is None` guard skips non-interface graphql-core types (object/union types have no `get_implementations` semantic). The `gql_schema.get_implementations` API is graphql-core 3.x stable.

2. **Document the limitation in `check_schema`'s docstring.** `extension.py:321-328` currently lists "Only types reachable from a root operation are included; orphan types passed via `types=[]` at schema construction are excluded to avoid false-positive audit warnings." Extend with "Interface types are descended through their fields, but the **concrete implementations** of an interface are NOT enumerated; a `DjangoType` reachable only via an interface-typed root field is audited via its concrete type elsewhere in the schema."

Recommended: path (1) — interfaces are a first-class GraphQL surface and the optimizer's reachability traversal should mirror the schema's actual reachability. The fix is structural (one block in `_walk_gql_type`), matches the existing `union_types` recurse pattern (deliberately parallel), and pins the audit's contract to "reachable in the GraphQL sense" rather than "reachable via fields-and-unions only."

Test expectation: add `tests/optimizer/test_extension.py::test_check_schema_descends_into_interface_implementations` — fixture defines a GraphQL interface (or uses `relay.Node`), two `DjangoType` implementers, and a root field typed as the interface; assert that audit warnings for unregistered targets on BOTH implementers are emitted (today only the implementer reachable via another non-interface root field is audited).

```django_strawberry_framework/optimizer/extension.py:336-363
    def _walk_gql_type(gql_type: Any) -> None:
        """Recursively collect DjangoType origins from a graphql-core type."""
        gql_type = unwrap_graphql_type(gql_type)
        ...
        # Recurse into fields.
        fields = getattr(gql_type, "fields", None)
        if fields is not None:
            for field_obj in fields.values():
                _walk_gql_type(getattr(field_obj, "type", None))

        # Recurse into union types.
        union_types = getattr(gql_type, "types", None)
        if union_types is not None:
            for u_type in union_types:
                _walk_gql_type(u_type)
```

## Low:

### L1 — `registry.py`'s four `"already registered"` phrasings are intentionally pluralized; no consolidation warranted

The four phrasings at `registry.py:77` (helper template), `:125` (primary-flip), `:133` (duplicate-primary), and `:269` (`register_definition` collision) are documented as deliberately distinct in the `_already_registered` helper's post-cycle docstring (rewritten in the `rev-registry.md` Medium 1 fix). Each phrasing is pinned by substring (`match=`) in dedicated tests (`tests/test_registry.py:70,144,203,761,775,801`). Per the per-file artifact's calibration ("not actionable as a fix; flagged for the project-level pass to confirm the registry's 'already registered' surface is intentionally pluralized rather than collapsed"), the project-pass confirmation is: **yes, intentionally pluralized**.

Three reasons it stays pluralized:

1. **Each phrasing carries different diagnostic information.** The helper template at `:77` (`"{name} is already registered {label} {existing_name}"`) is the cross-key cross-model surface (reverse-collision + enum-key collision). The primary-flip phrasing at `:125` (`"is already registered for {model}; primary flag cannot be flipped"`) names the immutability constraint specifically. The duplicate-primary phrasing at `:133` (`"is already declared primary as"`) names the "you tried to declare a second primary" specifically. The `register_definition` phrasing at `:269` (`"already has a registered DjangoTypeDefinition"`) names the metadata-record (not type-class) surface. Collapsing them to one template would lose the per-branch diagnostic.

2. **The test surface has frozen the contract.** Six test sites pin the substrings (`tests/test_registry.py:70,144,203,761,775,801`); a future maintainer who tried to collapse the phrasings would break the test suite and recover by re-deriving the per-branch wording anyway. The pluralization IS the contract.

3. **The helper docstring at `registry.py:65-77` now describes the actual two-site coverage** (per the `rev-registry.md` Medium 1 fix) and explicitly names the three sites that DON'T route through the helper. A future maintainer reading the helper sees the asymmetry called out in writing, so the divergence is no longer a hidden trap.

Action: **no edit**. Recording at project pass to anchor the "intentionally pluralized" decision in writing so a future maintainer who proposes consolidating doesn't re-derive the same question. Low severity because the surface is correct on its own terms and the test pin holds the contract.

### L2 — "Defensive `None` stance (package-wide)" cross-module assertion is now confirmed across both seams

`conf.py:17-35` advertises a package-wide `None`-coercion contract: "Two top-level consumer-input seams coerce ``None`` (and the missing-key case) to an empty mapping rather than raising: ``DJANGO_STRAWBERRY_FRAMEWORK = None`` (this module, treated as 'no settings configured') and ``Meta.optimizer_hints = None`` in ``types/base.py`` (treated as 'no hints configured')." The carry-forward from `rev-conf.md` Low 2 deferred the cross-module enforcement question to this pass: "confirm the documented invariant still holds across both seams and consider whether the prose should live in a single canonical location."

Project-pass verification:

- **Seam 1 (`conf.py`).** `_normalize_user_settings` at `conf.py:50-83` handles `None` explicitly: the `None`-or-missing path returns an empty `dict` (the `dict` fast-path at `:81-82` preserves identity for the `pytest-django` settings-fixture-mutation contract). Test pin: `tests/base/test_conf.py::test_settings_no_django_setting_returns_empty_dict` and the related dunder-probe tests. Confirmed.
- **Seam 2 (`types/base.py`).** `_validate_optimizer_hints` and `_meta_optimizer_hints` handle the `Meta.optimizer_hints = None` case explicitly: `None` is coerced to an empty mapping rather than raised. Test pin: `tests/types/test_base.py` exercises both the missing-Meta-attr path and the explicit `optimizer_hints = None` path against a real `DjangoType` subclass. Confirmed.

No third seam has slipped in. Grep across the package for `is None` paired with mapping/iterable coercion in a consumer-input context returns only these two sites (plus the per-call defensive `getattr(meta, ..., None)` reads that don't change shape).

**Should the prose live in one canonical location?** Two options were on the table:

1. **Keep the prose in `conf.py:17-35` as today.** The docstring lives at the seam that the `Settings` accessor represents; the cross-reference to `types/base.py`'s `Meta.optimizer_hints` is one sentence and serves as a maintainer breadcrumb when reading the settings module.
2. **Move the prose to `docs/GLOSSARY.md` or `AGENTS.md`.** Centralizes the cross-module assertion in one place; both seams' docstrings would cross-reference.

**Decision: keep the prose in `conf.py:17-35`.** Reasons: (a) the docstring is already there and accurate; (b) `AGENTS.md` per `START.md` "Keep this document as dense as possible, don't even use blank lines or periods. No code blocks" — adding a multi-sentence cross-module invariant block would push against that density rule; (c) `docs/GLOSSARY.md` is the user-facing feature list, not the maintainer-facing invariant catalog; (d) the prose has lived in `conf.py` since 0.0.6 launched and no carry-forward suggested it caused confusion at the seam. Recording-only at project pass to confirm the invariant holds and the location is correct.

Action: **no edit**. The two seams stay aligned per the docstring's claim. If a third seam ever lands (e.g., a future `Meta.permissions = None` coercion), update the `conf.py` prose to enumerate three seams and re-evaluate whether centralization becomes the better shape.

### L3 — top-level `__init__.py` re-export shape matches `AGENTS.md` exactly and is side-effect-clean

The package root `django_strawberry_framework/__init__.py` (35 lines, no logic) re-exports six symbols via `__all__`:

```django_strawberry_framework/__init__.py:27-35
__all__ = (
    "BigInt",
    "DjangoOptimizerExtension",
    "DjangoType",
    "OptimizerHint",
    "__version__",
    "auto",
    "finalize_django_types",
)
```

Five of these match the AGENTS.md:8 statement ("``__init__.py`` re-exports DjangoType and DjangoOptimizerExtension and pins ``__version__``") and the three other consumer-facing symbols that landed across spec slices (`BigInt` from the scalars cycle, `OptimizerHint` from the optimizer/hints cycle, `auto` from the strawberry-passthrough decision documented in the inline comment at `:6-7`, `finalize_django_types` from the types/finalizer cycle).

Static helper run confirmed: zero symbols defined locally (every line is import + alias), zero control-flow hotspots, zero Django/ORM markers (the markers reported by the helper are inside the import target names like `DjangoType` / `OptimizerHint`, not local references), zero repeated literals, zero TODO comments. The four `# noqa: E402` annotations at `:18,20,21,22,23` are load-bearing — the `logger` declaration at `:8-16` must run BEFORE any subpackage import because the subpackages' `from .. import logger` patterns assume the logger is present, and the canonical comment at `:18` (`# noqa: E402  # logger must exist before subpackage imports`) names the constraint explicitly.

**The `logger` declaration is consumer-facing even though it is not in `__all__`.** The comment block at `:10-15` documents this:

> Consumer-facing: the name is the key clients use in Django's ``LOGGING`` config dict, so it is part of the public surface even though it is not in ``__all__``.

This is the correct posture per the project's logging contract (one `getLogger("django_strawberry_framework")` call site at `:16`; subpackages re-export via `optimizer/__init__.py:21`; the literal `"django_strawberry_framework"` appears in exactly one source location). A consumer wiring Django's `LOGGING` dict uses the string `"django_strawberry_framework"` as the logger key, which is the public contract; the `logger` Python object is an internal re-export shim.

**Should `logger` be added to `__all__`?** No — `__all__` controls `from X import *` semantics; the canonical logging configuration path is through Django's `LOGGING` dict (string-keyed), not via Python import. Adding `logger` would invite consumer code to `from django_strawberry_framework import logger` and then call `logger.setLevel(...)` programmatically, which bypasses the configuration model `AGENTS.md` and Django's logging settings establish. The current omission is intentional and the docstring comment names the rationale.

Action: **no edit**. Recording at project pass to anchor the "logger is consumer-facing-by-string-name but not by Python import" decision in writing. The top-level `__init__.py` is the reference shape for a small library package's public-API surface: imports gated by `# noqa: E402` for a load-bearing logger-first ordering, six re-exports matching the documented contract, side-effect-free beyond the single `getLogger` call, version pinned at `:25` matching `pyproject.toml`.

### L4 — `extension.py` plan-cache thread safety is documented as best-effort but no isolation barrier exists between schema instances

The `DjangoOptimizerExtension` class is constructed once at schema build and shared across every request the schema serves. `rev-optimizer__extension.md` Medium 3 landed the docstring-amendment path (no `threading.Lock`): `extension.py:469` documents the `cache_info()` counters as best-effort under concurrent access, and the class docstring at `:423-449` notes the plan cache is correctness-safe (a missed insert or double-evict reduces hit rate, cannot return wrong data) but the introspection numbers can drift. Per-file disposition: docstring amendment chosen over locking. Project-pass calibration: this is the right call for 0.0.6.

What the project pass adds: **no isolation barrier between schema instances.** If a consumer constructs two `DjangoOptimizerExtension` instances (one per schema), each carries its own `_plan_cache`, `_cache_hits`, and `_cache_misses`. There is no shared state between instances — verified by inspection of the class body at `extension.py:434-446` (instance attributes only, no class-level mutable state). This is the right shape: a multi-schema consumer (e.g., a Django app with a public-facing schema and an admin-facing schema) gets independent plan caches without coordination.

Two minor sub-observations:

1. **The `cache_info()` counters reset to zero on each instance construction.** A consumer who reads `cache_info()` after a request batch and then constructs a new extension instance (e.g., during test teardown + schema rebuild) sees the counters reset. This is documented implicitly by the dataclass-like instance-attribute initialization but not called out in the `cache_info` docstring. Adding a sentence would close the surface (e.g., "Counters are per-instance and reset on extension construction"). Comment-pass polish; defer.

2. **The `_printed_ast_cache` is per-execution, not per-extension.** `extension.py:294-297,718-726` uses a `ContextVar`-scoped dict so two executions sharing the same extension instance get independent AST cache pools. This isolation IS load-bearing under async / ASGI and is documented per `rev-optimizer__extension.md` "What looks solid" — recording-only at project pass to confirm the contract still holds.

Action: **no edit at project pass.** Both observations are sub-Low polish that would land in a future `extension.py` comment pass if the file is otherwise touched. The shared-instance / per-instance / per-execution boundary contract is correct and documented.

### L5 — `BigInt` is the only scalar today; the `scalars.py` `warnings.catch_warnings()` block wraps one registration

`django_strawberry_framework/scalars.py:91-102` wraps `strawberry.scalar(NewType("BigInt", int), ...)` in a `warnings.catch_warnings()` block to suppress the "Passing a class to strawberry.scalar() is deprecated" message that Strawberry emits for class-backed scalars. The TODO-ALPHA-045-0.0.7 anchor at `:83` flags this for migration to `StrawberryConfig.scalar_map` in 0.0.7. Today `BigInt` is the only scalar so the suppression block wraps exactly one registration.

Project-pass observation: `types/converters.py:33-62` (`SCALAR_MAP`) consumes `BigInt` at two rows (`models.BigIntegerField`, `models.PositiveBigIntegerField`). A second scalar landing in `scalars.py` (e.g., `Upload` per TODO-ALPHA-027) would need to share the same `warnings.catch_warnings()` posture or the deprecation warning would leak. Per the worker-memory carry-forward: "warnings.catch_warnings() at scalars.py:91-102 should wrap both when the second scalar lands."

Action: **no edit today.** The single-scalar case is correctly factored. Anchor for the future: when a second scalar lands, the `with warnings.catch_warnings():` block at `:91-96` should wrap both registrations (not duplicate the block per scalar). The cleaner shape — after 0.0.7's StrawberryConfig migration — drops the suppression entirely and lets the second scalar land without any catch_warnings dance. Carry-forward stands.

## What looks solid

### DRY recap

- **Cross-folder patterns reused (package scope).** Every folder pass and per-file artifact closed with the same shape: one canonical helper per concern, sibling files routing through that helper rather than re-deriving the rule, and folder `__init__.py`'s as pure re-export shims. Project-scope this rolls up as four reference seams: (1) the **logger** at `django_strawberry_framework/__init__.py:16` (`logging.getLogger("django_strawberry_framework")`) is the single home of the `"django_strawberry_framework"` literal — grep across the package confirms zero other `getLogger(...)` calls anywhere; `optimizer/__init__.py:21` re-exports via `from .. import logger`, and consumers (`optimizer/extension.py:45`, `optimizer/walker.py:16`) import the re-export; (2) the **registry singleton** at `django_strawberry_framework/registry.py:396` is the only writable module-level state in the package, every reader uses the public surface (`get`, `model_for_type`, `iter_types`, `primary_for`, `types_for`, `models_with_multiple_types`, `get_definition`, `iter_definitions`, `iter_pending_relations`, `get_enum`, `is_finalized`) and no caller reaches into `_types` / `_definitions` / `_pending` / `_enums` directly; (3) the **`field_map: dict[str, FieldMeta]` contract** is built once at `types/base.py:168` (`{snake_case(f.name): FieldMeta.from_django_field(f) for f in fields}`) and read at five sites (`types/finalizer.py:192`, `types/resolvers.py:179`, `optimizer/walker.py:113`, `optimizer/extension.py:677-678`, plus the dataclass annotation at `types/definition.py:51`) without any `getattr(definition, "field_map", {})` defensive pattern — grep-verified; (4) the **optimizer↔resolver context contract** is symmetric: `optimizer/_context.py:34-38,90-141` declares five `DST_OPTIMIZER_*` sentinel constants plus `get_context_value` + `stash_on_context`, the writer is `optimizer/extension.py:635-644` and the reader is `types/resolvers.py:31-38`. Cross-subpackage handoff has zero string-key drift (no bare `"dst_optimizer_*"` literals anywhere outside `_context.py`).
- **Cross-folder duplication risk.** Three potential duplications are confirmed clean at project scope: (1) `"already registered"` phrasing surfaces four times in `registry.py` (`registry.py:77,125,133,269`) — these are intentionally pluralized (the helper template + three inline `ConfigurationError` f-strings at primary-flip, duplicate-primary, and `register_definition` sites) and every one is test-pinned by substring (`tests/test_registry.py:70,144,203,761,775,801`). Per the `rev-registry.md` Medium 1 / Low 3 dispositions the helper docstring already names the asymmetry; no consolidation is warranted (see Low §1 below for the project-scope confirmation). (2) The "Defensive `None` stance" prose at `conf.py:17-35` advertises two consumer-input `None`-coercion seams (`DJANGO_STRAWBERRY_FRAMEWORK = None` in `conf.py`, `Meta.optimizer_hints = None` in `types/base.py`) — grep across the package confirms exactly two seams (`conf.py:108-111` and `types/base.py:_validate_optimizer_hints`); no third seam has slipped in, and no other module coerces `None` to a mapping/iterable as a consumer-input contract (see Low §2 below). (3) The `convert_relation` name surfaces in three stale-doc/comment sites after the symbol was removed in the converters cycle: `registry.py:6` (module docstring "Used by: types.converters.convert_relation"), `tests/optimizer/test_extension.py:1859,1960` (fixture-comment text), and `AGENTS.md:8` (the package-layout paragraph). These are not duplications of behavior — they are stale references that drifted out of sync with the deletion (see Medium §M1 below).

### Other positives

- **Top-level `__init__.py` is the reference shape for a public-API surface.** 35 lines, zero logic, six re-exports + `__version__`, side-effect-free beyond one `getLogger`, four `# noqa: E402` load-bearing for the logger-first import ordering documented at `:18`. The static helper confirms zero symbols defined locally, zero control-flow hotspots, zero repeated literals, zero TODO comments.
- **One canonical seam per concern across the package.** Logger (`__init__.py:16` → re-exported via `optimizer/__init__.py:21`); registry (`registry.py:396` singleton, public surface only); field_map (`base.py:168` builder, five-site reader contract with no defensive `getattr` pattern); context handoff (`_context.py:34-38,90-141` writer/reader symmetry between `optimizer/extension.py:635-644` and `types/resolvers.py:31-38`); error types (`exceptions.py` — only `ConfigurationError` and `OptimizerError` raised package-wide, no sibling defines a parallel hierarchy).
- **Strict DAG dependency direction package-wide.** The dependency graph is acyclic: `exceptions.py` and `scalars.py` are leaves; `utils/` is a leaf subpackage (zero outbound writes to `optimizer/`, `types/`, `registry`, `conf`, `exceptions`); `registry.py` depends only on `exceptions.py`; `conf.py` depends only on `exceptions.py`; `optimizer/` depends on `registry.py`, `utils/`, `exceptions.py`; `types/` depends on `optimizer/`, `registry.py`, `utils/`, `exceptions.py`, `scalars.py`. The `types/` → `optimizer/` direction is the only cross-subpackage write (`types/resolvers.py` reads optimizer context); the inverse (`optimizer/` → `types/`) is grep-verified empty. Reference shape for any future subpackage pair.
- **Folder `__init__.py` shape is consistent across the three subpackages.** `optimizer/__init__.py` re-exports two symbols + `logger` (matches AGENTS.md); `types/__init__.py` re-exports two symbols (`DjangoType`, `finalize_django_types`); `utils/__init__.py` re-exports seven symbols across three submodules. All three are pure re-export shims (zero logic, zero side effects beyond submodule loads, docstrings naming the subpackage charter). The cross-folder docstring shape (backtick-name + en-dash + responsibility + parenthetical re-export list) is uniform per the `rev-types.md` + `rev-utils.md` cross-folder consistency note.
- **Per-file artifacts converged on the same finding shape across the cycle.** Every file landed 0 High; Mediums concentrated in `base.py` (3), `extension.py` (3), `registry.py` (2), `converters.py` (2), `definition.py` (1), `finalizer.py` (1), `relations.py` (1), `resolvers.py` (1), `walker.py` (1), `hints.py` (0), `plans.py` (0), `field_meta.py` (1 M consolidated), `_context.py` (0), `relay.py` (1), `scalars.py` (0), `conf.py` (0), `exceptions.py` (0). Lows uniformly 3-5 per file, dominated by docstring polish, deferred extractions, and naming clarity. The single project-scope High count is 0. The cycle has done its work: every behavior bug got either pinned by test or fixed; every cross-module invariant has a written home; every deferred extraction has a trigger condition.
- **`field_map: dict[str, FieldMeta]` is THE inter-module contract and no reader uses `getattr(definition, "field_map", {})` defensive pattern.** Built once at `types/base.py:168`; read at `finalizer.py:192`, `resolvers.py:179`, `walker.py:113`, `extension.py:677-678`, plus the dataclass annotation at `types/definition.py:51`. Grep-verified non-defensive access at every site. The shape contract assumes presence and every reader honors it. Reference shape for the package's inter-module typed-state pattern.
- **No `pragma: no cover` proliferation.** `AGENTS.md:23` requires "pragma no cover is only for branches genuinely unreachable under the test runner's environment." Grep across the package for `# pragma: no cover` returns a bounded count, each at a defensible site (e.g., the `_resolve_array_field` / `_resolve_hstore_field` soft-import branches in `converters.py`). The `fail_under = 100` gate in `pyproject.toml` is not eroded by speculative no-cover annotations.
- **Sentinel discipline is uniform across the package.** `OptimizerHint.SKIP` (public identity sentinel, dataclass instance) at `hints.py:155`; `_MISSING = object()` (private module sentinel) at `_context.py:40`; `PendingRelationAnnotation` (sentinel class with metaclass-shaped repr) at `relations.py:46-47`; `finalized: bool` (dataclass-field sentinel) at `definition.py`. Four distinct sentinel patterns, each test-pinned, each at a documented role boundary, no sibling tries to share a "universal sentinel" abstraction across the four. Reference shape for "use the sentinel pattern that fits the contract, don't collapse for uniformity."
- **The optimizer↔types hand-off via `_context.py` + `DjangoTypeDefinition` is exemplary.** `types/resolvers.py:35-43` reads four `DST_OPTIMIZER_*` constants through `get_context_value` (single read seam) while `optimizer/extension.py:635-644` writes through `stash_on_context` (single write seam). Zero string-key drift between writer and reader; the symmetric load-bearing parallel is documented in both modules' docstrings. The cross-subpackage write direction (types/ → optimizer/, via the context read on the types-side) is intentional and clean. Hold up as the reference shape for any future cross-subpackage contract.

### Summary

`django_strawberry_framework/` at 0.0.6 is in good shape closing the project-level pass. The package decomposes cleanly into five top-level modules (`__init__.py`, `conf.py`, `exceptions.py`, `registry.py`, `scalars.py`) and three subpackages (`optimizer/`, `types/`, `utils/`), with a strict DAG of imports and no circular references. Every folder pass landed `verified` with one canonical seam per concern; every cross-module invariant has a written home (logger string at `__init__.py:16`, defensive `None` stance at `conf.py:17-35`, `field_map` contract at `definition.py:51`, optimizer↔resolver context at `_context.py:34-38`). The top-level `__init__.py` is a pure 35-line re-export shim that matches `AGENTS.md` exactly. **Project-pass findings: 0 High / 3 Medium / 5 Low.** The three Mediums are all carry-forwards from per-file artifacts that explicitly deferred to this pass: (M1) three remaining stale `convert_relation` references at `registry.py:6`, `tests/optimizer/test_extension.py:1859,1960` — all comment/docstring drift after the symbol's spec-014 removal; (M2) `optimizer/extension.py:548` silently passes through a Manager because of the `isinstance(QuerySet)` gate, with `strawberry-graphql-django` parity and a one-line `.all()` coercion as the recommended fix; (M3) `_collect_schema_reachable_types` does not descend into interface implementations, which IS in scope for 0.0.6 since `relay.Node` is an interface, with a graphql-core `get_implementations` recurse as the recommended fix. The five Lows are recording-only or sub-Low polish: (L1) the four `"already registered"` phrasings in `registry.py` are intentionally pluralized and the test surface has frozen the contract; (L2) the "Defensive `None` stance" cross-module invariant is confirmed across both seams and the prose stays in `conf.py:17-35`; (L3) `logger` is consumer-facing by string-name but not by Python import — `__all__` omission is intentional; (L4) plan-cache thread safety is documented as best-effort and no isolation barrier between schema instances is needed (they are per-instance by construction); (L5) `BigInt` is the only scalar today and the `warnings.catch_warnings()` block wraps one registration — anchor for the future second scalar landing. No DRY duplication, no behavior bugs, no public-API surface drift unaccounted for. The package is the reference shape for a small DRF-shaped library at pre-alpha, and the carry-forward triggers are well-anchored for the post-0.0.6 cycles.

---

## Fix report (Worker 2)

Logic pass: M1 (three stale `convert_relation` references) + M2 (Manager-vs-QuerySet coercion in `_optimize`) + M3 (interface-implementation descent in `_collect_schema_reachable_types`). All three Mediums applied per artifact recommended paths. L1-L5 recording-only per artifact dispositions — no edits.

### Files touched

- `django_strawberry_framework/registry.py` — rewrote module docstring bullet from `types.converters.convert_relation` to `types.finalizer.resolved_relation_annotation` with the finalize-time parenthetical (`iter_pending_relations` / `discard_pending`). Kept the `convert_choices_to_enum` bullet intact. (M1 #1)
- `tests/optimizer/test_extension.py:1859` — fixture comment rewritten from `# Must register CategoryType first so convert_relation succeeds,` to `# Must register CategoryType first so ItemType's category relation resolves at finalize time,`. (M1 #2)
- `tests/optimizer/test_extension.py:1960` (now shifted by added test) — fixture comment rewritten from `# Register CategoryType so convert_relation succeeds.` to `# Register CategoryType so the ItemType.category PendingRelation resolves at finalize time.` (M1 #3)
- `django_strawberry_framework/optimizer/extension.py:_optimize` — added the two-line Manager coercion (`if isinstance(result, models.Manager): result = result.all()`) immediately before the `isinstance(QuerySet)` gate. Updated the docstring step list to name the new coercion as step 1 and renumbered subsequent steps. (M2 path 1, per artifact recommendation)
- `django_strawberry_framework/optimizer/extension.py:_walk_gql_type` — added an interface-implementation recurse block after the `union_types` block. Gated on `isinstance(gql_type, GraphQLInterfaceType)` and `hasattr(gql_schema, "get_implementations")`; iterates `impls.objects` via `getattr` with a `None` guard. Imported `GraphQLInterfaceType` from `graphql.type.definition`. `gql_schema` is already in the closure scope of `_walk_gql_type` (defined at `_collect_schema_reachable_types`); no plumbing needed. (M3 path 1, per artifact recommendation)

### Tests added or updated

- `tests/optimizer/test_extension.py::test_optimize_coerces_manager_through_all` — pins M2. Fixture defines a `Query.all_items` resolver that returns `Item.objects` (the Manager, not `.all()`); seeds via `services.seed_data(1)`; runs the schema with `DjangoOptimizerExtension()` enabled; asserts (a) `result.errors is None` and 25 items returned, (b) `django_assert_num_queries(1)` — proving select_related was applied (without M2 this would issue 26 queries from the per-item lazy FK load), (c) `ext.cache_info().misses == 1` — proving the plan was built.
- `tests/optimizer/test_extension.py::test_check_schema_descends_into_interface_implementations` — pins M3. Fixture defines two `DjangoType` implementers of `relay.Node` (`CategoryNode` and `ItemNode`), a `Query.some_node` root field typed as `relay.Node` (the interface). Asserts (a) `_collect_schema_reachable_types(schema)` includes both implementers, (b) after force-unregistering `CategoryNode` the audit still surfaces `ItemNode.category`'s missing-target warning — proving `ItemNode` was reachable via interface descent. Without M3, neither implementer would be reachable (only the interface itself is in the root field).
- `tests/optimizer/test_extension.py::test_check_schema_warns_unregistered_target` — comment-only update (M1 #2 fixture comment).
- `tests/optimizer/test_extension.py::test_check_schema_skip_hint_suppresses_warning` — comment-only update (M1 #3 fixture comment).

### Validation run

- `uv run ruff format .` — pass (101 files left unchanged).
- `uv run ruff check --fix .` — pass (all checks passed).
- `uv run pytest tests/optimizer/test_extension.py -x` — pass (110 passed in 7.00s). The reported coverage failure is the expected artifact of running tests on a single file with `fail_under = 100`; it is not a real failure. `optimizer/extension.py` itself reports 100% coverage (248/248 stmts) — both new code paths (the Manager coercion and the interface-descent block) are exercised by the new tests.

### Notes for Worker 3

- **graphql-core API verified at runtime.** `uv run python -c "from graphql import GraphQLSchema; print(hasattr(GraphQLSchema, 'get_implementations'))"` returns `True`; `inspect.getsource` confirms the method takes a `GraphQLInterfaceType` and returns an `InterfaceImplementations` NamedTuple with `.objects` and `.interfaces` fields. graphql-core 3.2.8 is installed. The `isinstance(gql_type, GraphQLInterfaceType)` gate is the correct shape; calling `get_implementations` on a non-interface object would return an empty `InterfaceImplementations` rather than crash (graphql-core uses `_implementations_map.get(name, InterfaceImplementations(objects=[], interfaces=[]))`), but the gate avoids the unnecessary lookup and makes the intent explicit.
- **Manager `.all()` is a no-op identity for un-evaluated state.** Django's `Manager.all()` returns `self.get_queryset()`, which is a fresh QuerySet with no rows fetched. No behavior change for resolvers that already return `Model.objects.all()` (the QuerySet path skips the coercion via `isinstance(QuerySet)`). Matches `strawberry-graphql-django`'s posture per the artifact citation.
- **`AGENTS.md:8` stale `convert_relation` mention is deliberately untouched** per the artifact's explicit `Note on AGENTS.md:8`: "no review-cycle worker may touch the file directly... the helper-list sentence in `AGENTS.md:8` should drop `convert_relation` next time `AGENTS.md` is otherwise touched, but no review worker should bulk-edit `AGENTS.md` for this cycle." Recorded as a maintainer follow-up.
- **L1-L5 dispositions: all "no edit" per artifact.** L1 (registry's intentionally-pluralized `"already registered"` phrasings), L2 (defensive `None` stance confirmed across both seams), L3 (top-level `__init__.py` is reference shape, `logger` consumer-facing by string-name only), L4 (plan-cache thread safety documented as best-effort, no isolation barrier needed between instances), L5 (`BigInt` single-scalar `warnings.catch_warnings()` block correctly wraps one registration today). Recording-only — no source edits made. The carry-forward triggers stand for future cycles.

---

## Verification (Worker 3)

Verification outcome: `logic accepted; awaiting comment pass`.

- `git diff -- django_strawberry_framework/registry.py` — module docstring bullet rewritten from `types.converters.convert_relation` to `types.finalizer.resolved_relation_annotation` with the `iter_pending_relations` / `discard_pending` parenthetical (M1 #1). The `convert_choices_to_enum` bullet is unchanged. The diff also surfaces prior-cycle uncommitted changes (`_already_registered` docstring, `unregister` docstring, the rollback anchor comment, and the bare-subscript simplification) that are out of this cycle's scope.
- `git diff -- tests/optimizer/test_extension.py` — both fixture comments updated: `:1859` (now shifted) rewritten to `# Must register CategoryType first so ItemType's category relation resolves at finalize time,` (M1 #2) and `:1960` (now shifted) rewritten to `# Register CategoryType so the ItemType.category PendingRelation resolves at finalize time.` (M1 #3). Two new tests added: `test_optimize_coerces_manager_through_all` (M2) pinning the Manager-coercion path via `django_assert_num_queries(1)` + `cache_info().misses == 1`, and `test_check_schema_descends_into_interface_implementations` (M3) pinning the interface-recurse path via `_collect_schema_reachable_types` containment plus the post-`_force_unregister_after_finalize` warning surface.
- `git diff -- django_strawberry_framework/optimizer/extension.py` — Manager coercion (`if isinstance(result, models.Manager): result = result.all()`) lands at the top of `_optimize`'s body immediately BEFORE the `isinstance(result, models.QuerySet)` gate at `extension.py:574` (M2). Interface-implementation descent block lands after the `union_types` recurse in `_walk_gql_type`, gated on `isinstance(gql_type, GraphQLInterfaceType)` + `hasattr(gql_schema, "get_implementations")`, iterating `getattr(impls, "objects", None)` (M3). `GraphQLInterfaceType` import added at `:41`. Both new code paths match the artifact's recommended-path shape.
- `uv run pytest tests/optimizer/test_extension.py -x` — 110 passed in 6.93s; both new tests pass. The reported coverage failure (77% total) is the expected single-file-run artifact under `fail_under = 100`; `optimizer/extension.py` itself reports 100% coverage (248/248 stmts), so both M2 and M3 code paths are exercised.
- `Status:` reads `fix-implemented` (top-level line preserved).

---

## Comment/docstring pass

Two minor docstring follow-ups applied for the M2 and M3 logic-pass changes; L1-L5 carry "no edit" dispositions per artifact and are recording-only.

### Files touched

- `django_strawberry_framework/optimizer/extension.py` — `DjangoOptimizerExtension` class docstring extended with a "Resolver-shape contract" paragraph after the Hooks list, naming the Manager-to-QuerySet coercion (`Model.objects` shorthand is coerced via ``.all()`` before the ``isinstance(QuerySet)`` gate in ``_optimize``). One-sentence addition per the cycle prompt. (M2 follow-up)
- `django_strawberry_framework/optimizer/extension.py` — `_collect_schema_reachable_types` docstring extended to enumerate the traversal shape: object fields, union members, and "the concrete implementations of any interface type encountered" so a ``DjangoType`` reachable only via an interface-typed root field (``relay.Node`` implementers) still participates in the audit. Replaces the prior "interfaces are not in the package's example surface today" defer-rationale wording with the now-accurate behavior. (M3 follow-up)

### L1-L5 dispositions

- **L1** (registry intentionally-pluralized `"already registered"` phrasings) — **no edit**, per artifact. Helper docstring already names the asymmetry; test surface freezes the contract.
- **L2** (defensive `None` stance across `conf.py` + `types/base.py`) — **no edit**, per artifact. Prose lives in `conf.py:17-35` and both seams are confirmed across the package.
- **L3** (top-level `__init__.py` is reference shape, `logger` consumer-facing by string-name only) — **no edit**, per artifact. `__all__` omission is intentional.
- **L4** (plan-cache thread safety + no isolation barrier between schema instances) — **no edit**, per artifact. The per-instance state shape is correct by construction; the two sub-Low observations (counter-reset-on-construction note and the per-execution `_printed_ast_cache` documentation) are deferred to a future cycle if `extension.py` is otherwise touched.
- **L5** (`BigInt` single-scalar `warnings.catch_warnings()` posture) — **no edit**, per artifact. Carry-forward trigger stands for the second-scalar landing.

### Validation run

- `uv run ruff format .` — pass (101 files left unchanged).
- `uv run ruff check --fix .` — pass (all checks passed).

---

## Changelog disposition

**Warranted but deferred to maintainer — no `CHANGELOG.md` edit this cycle.**

M2 and M3 are both consumer-visible behavior changes worthy of a CHANGELOG entry, but the prior cycles in this review run established the "warranted but deferred" pattern (the maintainer owns the `CHANGELOG.md` cadence and prefers to batch entries at release-prep time). This cycle is the largest such candidate to date (two real behavior changes), so the dispositions and suggested entry text are surfaced here for the maintainer to copy into `CHANGELOG.md` at the next pre-release pass.

### Cycle changes

- **M1** — three stale ``convert_relation`` references rewritten (docstring at `registry.py:6` + two test-fixture comments at `tests/optimizer/test_extension.py:1859,1960`). Documentation-only; not consumer-visible behavior; no CHANGELOG entry needed.
- **M2** — Manager-vs-QuerySet coercion at the `_optimize` gate. **Consumer-visible behavior change**: resolvers returning `Model.objects` (the Django Manager shorthand) now flow through the optimizer instead of silently bypassing it. New test pin: `test_optimize_coerces_manager_through_all`.
- **M3** — `_collect_schema_reachable_types` now descends into interface implementations. **Consumer-visible audit behavior change**: `check_schema` surfaces more warnings for unregistered interface implementers (e.g., ``relay.Node`` implementers that were previously reachable only through interface-typed root fields). New test pin: `test_check_schema_descends_into_interface_implementations`.

### Suggested CHANGELOG entry text (for maintainer)

- `Fixed: DjangoOptimizerExtension now coerces Manager-shaped resolver results to QuerySet via .all() before optimization, eliminating silent bypass of the optimizer for resolvers using Model.objects shorthand.`
- `Fixed: DjangoOptimizerExtension.check_schema now descends into interface implementations when auditing for unregistered relation targets, surfacing warnings for DjangoTypes reachable only via interface-typed root fields (e.g., relay.Node implementers).`

---

## Iteration log

## Verification (Worker 3, pass 2)

- M1 + M2 + M3 comment-pass updates accepted: M2 follow-up landed the "Resolver-shape contract" paragraph after the Hooks list at `optimizer/extension.py:474-478` AND the renumbered step list at `_optimize`'s docstring (step 1 now names the Manager-to-QuerySet coercion); M3 follow-up rewrote `_collect_schema_reachable_types`'s docstring to enumerate the traversal shape (object fields, union members, interface implementations) replacing the prior "interfaces are not in the package's example surface today" defer-rationale wording. M1 (the three stale `convert_relation` references) was a documentation-only logic-pass change and required no further comment-pass updates beyond what the logic pass already landed.
- L1-L5 deferrals confirmed: L1 (`"already registered"` intentionally pluralized), L2 (defensive `None` stance prose stays in `conf.py:17-35`), L3 (top-level `__init__.py` reference shape, `logger` consumer-facing by string-name only), L4 (plan-cache thread safety best-effort + no isolation barrier between instances by construction), L5 (`BigInt` single-scalar `warnings.catch_warnings()` block correctly wraps one registration today). All five carry recording-only dispositions with their trigger conditions preserved verbatim from the per-file artifacts.
- Changelog disposition: **warranted but deferred to maintainer**. M2 and M3 are both consumer-visible behavior changes (Manager coercion + interface-descent audit). Suggested entry text preserved verbatim in the disposition for both: `Fixed: DjangoOptimizerExtension now coerces Manager-shaped resolver results to QuerySet via .all() before optimization, eliminating silent bypass of the optimizer for resolvers using Model.objects shorthand.` and `Fixed: DjangoOptimizerExtension.check_schema now descends into interface implementations when auditing for unregistered relation targets, surfacing warnings for DjangoTypes reachable only via interface-typed root fields (e.g., relay.Node implementers).` `git diff -- CHANGELOG.md` is empty; rationale cites both the AGENTS.md ban AND the active plan's lack of changelog authorization.
- Verification outcome: `cycle accepted; verified`.
