# Review: `django_strawberry_framework/registry.py`

## High:

None.

## Medium:

### `discard_pending` uses set membership against unhashable `PendingRelation`

`discard_pending` coerces the caller's iterable into a `set` and then runs an `in` check across `self._pending`. This silently assumes `PendingRelation` is hashable. If `PendingRelation` is a mutable dataclass (the common case for "pending" record types collected during `__init_subclass__`) or grows a non-hashable field, both the `set(resolved)` construction and the `pending not in resolved_set` check raise `TypeError` at finalization time — a crash on the normal consumer path, not a test-only path. Even if the type is currently hashable, identity-vs-equality semantics for "the same pending entry" are not pinned down anywhere; relying on `__hash__`/`__eq__` of a sibling module's record type is a brittle cross-module contract. Recommend either: (a) match by `id()` against the existing list, or (b) document and test the hashability requirement on `PendingRelation` and add an assertion here. Either way add a test exercising `discard_pending` with the actual record class produced by the relations module so the contract is pinned.

```django_strawberry_framework/registry.py:125:128
def discard_pending(self, resolved: Iterable[PendingRelation]) -> None:
    """Drop pending records that have been resolved successfully."""
    resolved_set = set(resolved)
    self._pending = [pending for pending in self._pending if pending not in resolved_set]
```

### No test-isolation guard on mutator methods after `mark_finalized`

`mark_finalized` flips `_finalized` but `register`, `register_definition`, `add_pending_relation`, and `register_enum` ignore it. A bug that re-enters the import-time pipeline after finalization (e.g., a late `import` of a module defining a `DjangoType` subclass triggered by a request handler) would silently mutate the registry post-finalization rather than failing loud. The class docstring already states "Do not call `register` or `register_enum` from a request handler or async resolver" — that contract is not enforced. Recommend a single `_check_mutable()` helper called from each mutator that raises `ConfigurationError` when `_finalized` is true. Pair with a test that registers a type, finalizes, then asserts a second registration raises.

```django_strawberry_framework/registry.py:49:72
def register(self, model: type[models.Model], type_cls: type) -> None:
    ...
    self._types[model] = type_cls
    self._models[type_cls] = model
```

## Low:

### Duplicate "is already registered as" message string

Three mutator methods build near-identical "X is already registered as Y" / "is already registered against Y" / "already has a registered DjangoTypeDefinition" messages. The static helper flagged "is already registered as" repeating 2x in this file alone; the same shape will recur in any future `register_*` method. A single `_already_registered(label, name, existing_name)` helper would centralize phrasing and make the test-fixture grep for these messages stable.

```django_strawberry_framework/registry.py:62:70
if model in self._types:
    raise ConfigurationError(
        f"{model.__name__} is already registered as {self._types[model].__name__}",
    )
existing_model = self._models.get(type_cls)
if existing_model is not None and existing_model is not model:
    raise ConfigurationError(
        f"{type_cls.__name__} is already registered against {existing_model.__name__}",
    )
```

### `register_definition` accepts `type_cls` not yet in `_types`

`register_definition` does not require `type_cls` to be present in `_types`/`_models`. It is therefore possible to register a `DjangoTypeDefinition` against a class the registry has never seen as a `DjangoType`. This is unlikely to happen in the normal `__init_subclass__` ordering, but the asymmetry is worth pinning: either document that the caller (the types finalizer) is responsible for ordering, or guard with `if type_cls not in self._models: raise ConfigurationError(...)`. If the design intent is to allow definitions for un-modelled wrapper classes, the docstring should say so explicitly.

```django_strawberry_framework/registry.py:102:107
def register_definition(self, type_cls: type, definition: DjangoTypeDefinition) -> None:
    """Register the collected definition object for ``type_cls``."""
    existing = self._definitions.get(type_cls)
    if existing is not None and existing is not definition:
        raise ConfigurationError(f"{type_cls.__name__} already has a registered DjangoTypeDefinition")
    self._definitions[type_cls] = definition
```

### `model_for_type` accepts `None` for caller convenience

The "returns `None` for `None`" branch is documented but is a small Hyrum's-law trap — every caller that relies on it locks the registry into pipelining `Optional[type]` forever. Consider whether the caller in `DjangoOptimizerExtension` could do its own `is None` short-circuit instead, narrowing the registry signature to `type[models.Model] | None = model_for_type(self, type_cls: type)`. Localized polish; not blocking.

```django_strawberry_framework/registry.py:78:90
def model_for_type(self, type_cls: type | None) -> type[models.Model] | None:
    ...
    if type_cls is None:
        return None
    return self._models.get(type_cls)
```

### `iter_pending_relations` exposes mutable internal list

`iter_pending_relations` yields directly from `self._pending`. Callers cannot mutate the list through the iterator (good), but a caller storing the iterator while another code path calls `discard_pending` will observe a stale view. Worth a one-line docstring note that pending records can be mutated by `discard_pending` between yields.

```django_strawberry_framework/registry.py:121:123
def iter_pending_relations(self) -> Iterator[PendingRelation]:
    """Yield pending relation records in collection order."""
    yield from self._pending
```

## What looks solid

- Bidirectional `_types`/`_models` mapping with conflict detection on both directions (registering same class against two models, registering same model twice) is the right shape for an O(1) reverse lookup and is well-tested by the existing duplicate-registration messages.
- Re-registering the *same* enum class for `(model, field_name)` is a no-op (line 158 identity check); this preserves the documented `get_enum`-then-`register_enum` retry pattern in `convert_choices_to_enum`.
- `clear()` resets every dict and list, including `_finalized`, so test isolation via the autouse fixture is complete; no field will leak across tests.
- `TYPE_CHECKING`-guarded imports of `DjangoTypeDefinition` and `PendingRelation` correctly avoid a registry → types/relations import cycle at module load time.
- The class docstring is honest about the no-lock decision and ties it to the import-time-only mutator contract — that's the right level of design transparency.
- Static helper run on this file (188 lines, ≥150 threshold). No control-flow hotspots, no reflective-access calls of concern, no TODO comments.

---

### Summary:

`registry.py` is a clean, small, well-documented process-global singleton with sound bidirectional mapping and explicit thread-safety reasoning. The two Medium findings are (1) `discard_pending` quietly assumes `PendingRelation` is hashable, which couples this module to the relations module's record shape and will crash the consumer path if that shape drifts, and (2) the `_finalized` flag is set but never enforced, so the import-time-only mutator contract is documented but not guarded. Lows are message-string duplication, an asymmetric `register_definition` precondition, a small `None`-pipelining convenience in `model_for_type`, and a stale-view note for `iter_pending_relations`. Folder-pass follow-up: confirm `PendingRelation`'s hashability contract when reviewing `types/relations.py`, and check whether other registries/finalizers in the package reuse the "is already registered" phrasing so the helper-function consolidation can be done once at folder scope.

## Verification

PASS. Both Medium findings addressed: `discard_pending` switched to identity match via `id()` (decouples from `PendingRelation` hashability), and `_check_mutable()` is invoked from every mutator (`register`, `register_definition`, `add_pending_relation`, `discard_pending`, `register_enum`) to enforce the post-`mark_finalized` contract. Lows resolved or rationally deferred: (a) `_already_registered` helper centralizes the three collision messages; (b) `register_definition` asymmetry now documented in the docstring (caller-orders contract); (c) `iter_pending_relations` stale-view note added; (d) `model_for_type` `None`-pipeline kept as-is — acceptable since flagged "not blocking" and untouched. Tests: `test_discard_pending_uses_identity_match_with_real_pending_relation` pins identity semantics with two equal-value `PendingRelation` records; `test_mutators_reject_calls_after_mark_finalized` exercises all five mutators post-finalize. `uv run pytest tests/test_registry.py -q` -> 27 passed; `registry.py` reports 100% line coverage. Coverage gate failure in the run is expected from running a single test file (full suite gates the package).
