# Alpha Review Feedback: B2 Forward-FK-id elision

## Scope reviewed

- `django_strawberry_framework/optimizer/extension.py`
- `django_strawberry_framework/optimizer/plans.py`
- `django_strawberry_framework/optimizer/walker.py`
- `django_strawberry_framework/types/resolvers.py`
- `examples/fakeshop/fakeshop/products/schema.py`
- `tests/optimizer/test_extension.py`
- `tests/optimizer/test_plans.py`
- `tests/optimizer/test_walker.py`
- `tests/types/test_resolvers.py`
- `docs/spec-optimizer_beyond.md`

## Findings

### 1. FK with `to_field` pointing at a non-PK column produces a stub with the wrong PK

Priority: P1

In `_build_fk_id_stub` ([resolvers.py:74-78](django_strawberry_framework/types/resolvers.py:74)) the stub is built as `field.related_model(pk=related_id)` where `related_id = getattr(root, field.attname)`. For a `ForeignKey(..., to_field="code")`, `field.attname` is the source column that stores the *target's `code` value*, not its PK. Constructing `Related(pk=<code value>)` therefore creates a stub whose `.pk` / `.id` is wrong, and any GraphQL `id` resolver (especially Relay GlobalID, `to_global_id(type, instance.pk)`) will return a value that points at the wrong row — silent data corruption rather than a query error.

Recommended fix:

- Gate elision in `_can_elide_fk_id` on `field.target_field` being the related model's primary key (i.e., `field.target_field is field.related_model._meta.pk`), or
- Build the stub by setting the actual `target_field` attribute instead of `pk`.
- Add a regression test using a `ForeignKey(..., to_field=...)` model.

Relevant code:

- `django_strawberry_framework/types/resolvers.py:69-78`
- `django_strawberry_framework/optimizer/walker.py:271-278`

### 2. Elision check is hard-coded to the literal Django field name `"id"`

Priority: P2

`_walk_selections` only elides when `_selected_scalar_names(...) == {"id"}` ([walker.py:198](django_strawberry_framework/optimizer/walker.py:198)). The contract is "the only column requested is one already on the source row," which is really "the target's PK column." Models whose PK is renamed (e.g. `uuid = models.UUIDField(primary_key=True)`, no implicit `id`) will never elide even though the optimization is still valid, because the GraphQL field name surfaces as `uuid` and the literal-string match fails. Conversely, if a model has both a renamed PK and a regular field literally named `id`, the elision triggers on the wrong column.

Recommended fix:

- Replace the `{"id"}` literal with `{model._meta.pk.name}` (or accept either `pk` or the actual PK field name).
- Add a test with a model whose PK is not named `id`.

Relevant code:

- `django_strawberry_framework/optimizer/walker.py:195-201`

### 3. Stub `Model(pk=…)` leaves `_state.adding = True`

Priority: P2

`field.related_model(pk=related_id)` yields an instance with `_state.adding=True` and `_state.db=None`, which is the marker Django uses for "never persisted". Downstream code that branches on `instance._state.adding` (custom `__str__`, signal handlers attached to types via `Meta.interfaces`, permission checks, audit logging) will now see "new object" semantics for what is actually a loaded row. For an `id`-only selection this rarely matters, but if any consumer extension reads state — or if a future feature on the same type chain accesses an attribute that triggers an unintended behavior — this becomes a hard-to-trace bug.

Recommended fix:

- After constructing the stub, set `stub._state.adding = False; stub._state.db = router.db_for_read(field.related_model)` (or just `"default"`), matching what `Model.from_db` does.

Relevant code:

- `django_strawberry_framework/types/resolvers.py:74-78`

### 4. Custom `resolve_id` / non-`pk`-derived id resolvers silently break under elision

Priority: P2

The stub only has `pk` set; every other model attribute is the field default. If a `DjangoType` defines a custom `id` resolver that depends on any other column (composite ids, hashed/encoded ids built from `name`+`pk`, tenant-scoped ids reading `instance.tenant_id`, etc.), elision will return wrong values without warning because the resolver receives a stub model whose other fields are defaults, not what's in the database.

The current `has_custom_get_queryset` guard catches visibility filters but not custom id resolution.

Recommended fix:

- Either extend the guard to also skip elision when `CategoryType` defines its own `resolve_id` / `id` strawberry field with a non-default resolver, or
- Document this constraint explicitly in `spec-optimizer_beyond.md` under B2 (the spec mentions "potential GlobalID interaction" but not custom id resolvers).

Relevant code:

- `django_strawberry_framework/optimizer/walker.py:195-199`
- `docs/spec-optimizer_beyond.md` B2 section

### 5. `_is_fk_id_elided` checks two name variants where one suffices

Priority: P3

`_is_fk_id_elided` tests `field_name in elisions or _get_relation_field_name(info) in elisions` ([resolvers.py:64-65](django_strawberry_framework/types/resolvers.py:64)). At depth-1 the walker only stores the bare Django field name and the resolver closure already passes the snake_cased Django field name, so both lookups always agree. The fallback is dead code today and obscures the contract: it implies "we sometimes get aliased names here" when we don't.

When O4 (nested prefetch chains) lands, elisions will be stored as dotted/`__` paths (e.g. `parent__child`) and *neither* lookup form will match — both will need a different join key. The current second lookup gives the false impression that depth-N is already partly handled.

Recommended fix:

- Drop the second lookup, or
- Add a comment that explicitly says "depth-1 only; revisit when O4 lands."

Relevant code:

- `django_strawberry_framework/types/resolvers.py:60-65`

### 6. `examples/fakeshop` adds an unused import purely as a packaging smoke test

Priority: P3

`examples/fakeshop/fakeshop/products/schema.py` now imports `DjangoOptimizerExtension` and `DjangoType` and re-exports them via `__all__` without using them in `Query`. The inline comment explains the intent ("pre-flight import only — surfaces real-world packaging / import-graph gaps"), but:

- Linters (ruff `F401`, pyflakes) will flag this; if the example is part of CI it'll either need a per-file ignore or a `noqa` comment.
- A runtime `import` at the bottom of a module that's imported anyway gives the same signal as a dedicated `tests/test_packaging_imports.py` that does `import django_strawberry_framework as dst; assert dst.DjangoOptimizerExtension`. The dedicated test communicates intent better and survives example refactors.

Recommended fix:

- Move the smoke test to a real test under `tests/` and revert the example file, or
- Add `# noqa: F401` on the import line and a TODO referencing the slice that wires it into `Query`.

Relevant code:

- `examples/fakeshop/fakeshop/products/schema.py:182-200`

### 7. Spec rationale text is now mismatched with the actual ordering

Priority: P3

`spec-optimizer_beyond.md` previously said "B2 last among the perf items"; the diff rewrites this to "B2 landed after O5+O6+B5". That's accurate but B6 is also marked done in the same checklist, so "after … B5" alone understates which slices preceded B2. Minor — readers reconstructing the slice timeline from this paragraph will be slightly off.

Recommended fix:

- Update the rationale paragraph to list the actually-shipped predecessors (O5, O6, B5, B7, B3, B4, B6), or generalize to "after the surrounding optimizer slices".

Relevant doc:

- `docs/spec-optimizer_beyond.md:227`

## Overall assessment

B2 is a meaningful optimization and the test coverage of the happy path, fragment path, custom-`get_queryset` downgrade, null-FK, and strictness integration is solid. The P1 risk is the `to_field` case: today's stub silently emits wrong ids for any FK that doesn't point at the target's PK. The P2 issues (literal `"id"`, `_state.adding`, custom id resolvers) are correctness gaps that are unlikely to fire in the fakeshop example but will bite real schemas.
