# Review: `django_strawberry_framework/registry.py`

## High:

None.

## Medium:

None.

## Low:

### `register` does not guard against the same `type_cls` registering against two models

`register` checks `model in self._types` but not `type_cls in self._models`. If the same `DjangoType` subclass were ever registered twice against different models, the second call would silently overwrite the existing entry in `self._models`, leaving `model_for_type` returning the wrong model for the original subclass. In practice this is unreachable today because `DjangoType.__init_subclass__` calls `register` exactly once per subclass with `cls` as the `type_cls`, so a single class cannot reach this branch. The guard is a cheap correctness pin against future code paths (e.g., manual re-registration helpers, schema-scoped registries listed in `iter_types`'s docstring as future work).

Recommended: raise `ConfigurationError` in `register` if `type_cls in self._models` and the existing model differs from `model`. No new test needed unless the guard is added; if added, pin it with a unit test on `TypeRegistry.register`.

```django_strawberry_framework/registry.py:33:49
def register(self, model: type[models.Model], type_cls: type) -> None:
    ...
    if model in self._types:
        raise ConfigurationError(
            f"{model.__name__} is already registered as {self._types[model].__name__}",
        )
    self._types[model] = type_cls
    self._models[type_cls] = model
```

### `register_enum` silently overwrites on duplicate keys

`register_enum` does not check whether an entry for `(model, field_name)` already exists; the second call overwrites the first. The only call site (`converters.convert_choices_to_enum`) checks `get_enum` first, so collisions should not occur in normal flow. As with `register`, this is a future-proofing pin: if a code path in a later spec calls `register_enum` directly without the cache check, the silent overwrite could produce two `DjangoType`s pointing at different `Enum` classes for the same column — a hard-to-diagnose schema mismatch.

Recommended: either no change (current behavior is documented and the call path is correct) or add an `if key in self._enums and self._enums[key] is not enum_cls: raise ConfigurationError(...)` guard. Defer the decision to the maintainer; this is purely defensive.

```django_strawberry_framework/registry.py:106:117
def register_enum(
    self,
    model: type[models.Model],
    field_name: str,
    enum_cls: type[Enum],
) -> None:
    ...
    self._enums[(model, field_name)] = enum_cls
```

### Thread-safety not documented

The registry is a process-global singleton with unprotected dict mutations. In typical Django use, registration happens at import time (single-threaded), so the absence of locking is fine. But the docstring should pin this assumption explicitly so future contributors do not call `register` from a request handler or async resolver and get a torn read. Comment polish — defer to comment pass.

```django_strawberry_framework/registry.py:25:31
class TypeRegistry:
    """Process-global registry of generated GraphQL types and enums."""

    def __init__(self) -> None:
        self._types: dict[type[models.Model], type] = {}
        self._models: dict[type, type[models.Model]] = {}
        self._enums: dict[tuple[type[models.Model], str], type[Enum]] = {}
```

### `lazy_ref` docstring lists three competing strategies but no decision

The `lazy_ref` docstring enumerates three viable approaches (`Annotated[..., strawberry.lazy(...)]`, string-annotation rewrite in `_build_annotations`, registry-tracked pending-relation record) and the body raises `NotImplementedError`. That is the correct AGENTS.md pattern for a deferred slice (TODO anchor + `NotImplementedError`), but the docstring reads as design notes rather than a public-API contract. Comment polish — defer.

```django_strawberry_framework/registry.py:79:104
def lazy_ref(self, model: type[models.Model]) -> Any:
    """Return a forward reference resolved at schema build.
    ...
    raise NotImplementedError("lazy_ref pending future slice (definition-order independence)")
```

## What looks solid

- Two-direction mapping (`_types` forward, `_models` reverse) gives `model_for_type` an O(1) lookup, which is the hot path for `DjangoOptimizerExtension.resolve_type` per the docstring.
- Duplicate-model registration raises `ConfigurationError` with the conflicting class name, which makes import-time conflicts trivial to diagnose.
- `model_for_type(None)` returns `None` as a deliberate optimizer-pipeline shortcut, with a docstring explaining why the extra guard would be wasteful.
- `iter_types()` exposes a public iterator instead of leaking `_types` directly — that is the right escape hatch for future schema-scoped filtering.
- `clear()` is documented as test-only and points at the autouse fixture pattern, matching AGENTS.md's "test through real usage" guidance.
- File honors AGENTS.md's "registry.py owns the model→type registry" boundary; no Strawberry imports leak in.
- `OptimizerError` and `ConfigurationError` come from `.exceptions`, preserving the bottom-of-the-import-graph rule for the exceptions module.
- 100% line coverage in the package suite.

---

### Summary:

Tight, single-responsibility registry with explicit forward and reverse mappings, deterministic duplicate-model handling, and a deliberately documented test-only `clear()`. No correctness or performance issues at any meaningful severity. The Low items are defensive guards (`register` doesn't reject the same class against two models; `register_enum` doesn't reject mismatched re-registration) plus comment polish for thread-safety expectations and the `lazy_ref` design notes. Address guards if the maintainer wants the future-proofing; otherwise, the comment-pass tweaks are sufficient.

---

### Worker 3 verification

- Low fix 1: `register` now also rejects re-registering the same `type_cls` against a different model. Same-class same-model is still a no-op for the reverse map, so `__init_subclass__` retries (theoretical) do not break.
- Low fix 2: `register_enum` now rejects a *different* enum class for an existing `(model, field_name)` key but allows re-registering the *same* class (idempotent), preserving the `get_enum`-then-`register_enum` cache pattern in `convert_choices_to_enum`.
- Tests added in `tests/test_registry.py`:
  - `test_register_same_class_against_two_models_raises` pins the new `register` guard and that the original mapping is preserved.
  - `test_register_enum_same_class_is_idempotent` pins the no-op re-register path so the converter call site does not regress.
  - `test_register_enum_different_class_for_same_key_raises` pins the new `register_enum` guard and that the original cache is preserved.
- Comment polish: `TypeRegistry` class docstring now explains why mutations are unguarded (import-time only) and warns against calling `register` / `register_enum` from request handlers or async resolvers.
- Comment polish (deferred to future cycle if needed): `lazy_ref` docstring still enumerates three strategies; the maintainer can choose one when the slice ships, and removing the design notes prematurely would lose context.
- Validation: `uv run ruff format` and `uv run ruff check` clean; `uv run pytest -q` -> 343 passed, 4 skipped, 100% coverage (gain of 3 tests, all in `tests/test_registry.py` which is an allowed location per AGENTS.md).
- CHANGELOG: not updated. Defensive guards are not user-visible behavior changes for any current code path; AGENTS.md forbids changelog edits without explicit instruction.
- Scope: changes confined to `django_strawberry_framework/registry.py` and `tests/test_registry.py`.
- Checkbox in `docs/review/review-0_0_3.md`: marked `- [x]`.
