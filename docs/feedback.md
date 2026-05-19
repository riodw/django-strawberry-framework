# Implementation review - spec-015 consumer scalar overrides (Slice 1)

Scope: reviewed the staged Python diff (`django_strawberry_framework/types/base.py`, `django_strawberry_framework/types/definition.py`, `tests/types/test_definition_order.py`, `tests/types/test_converters.py`, `tests/types/test_base.py`, plus the `pyproject.toml` ruff-config revert) against rev10 of `docs/spec-015-consumer_overrides_scalar-0_0_6.md`.

Test run: `uv run pytest` — 707 passed, 2 skipped, 0 failed. Coverage 99.94% (1 line uncovered — see M1 below).

## Findings

### M1. `_id_annotation_is_relay_node_id`'s `id_hint is None` branch is unreachable and blocks 100% coverage

Reference: `django_strawberry_framework/types/base.py:123-125`.

```python
id_hint = hints.get("id")
if id_hint is None:
    return False          # line 125 — never executed
return _has_node_id_marker(id_hint)
```

The full-suite coverage run shows exactly one uncovered line in the package: `base.py:125`. The call site at `base.py:205` reads:

```python
if has_id_annotation and not _id_annotation_is_relay_node_id(cls):
```

where `has_id_annotation = "id" in cls.__annotations__`. By the time `_id_annotation_is_relay_node_id(cls)` is called, `"id"` is guaranteed to be in `cls.__annotations__`, so `typing.get_type_hints(cls, include_extras=True)` resolves "id" and `hints.get("id")` returns a non-None value. The defensive `if id_hint is None: return False` is dead code under the current call-site precondition.

This breaks the Definition of done's 100% coverage gate. Pick one of three resolutions:

- **Remove the defensive check.** `_has_node_id_marker(None)` already returns False safely — `typing.get_origin(None)` returns None, not `Annotated`, so the conjunction short-circuits. Drop lines 123-124 entirely and call `return _has_node_id_marker(hints.get("id"))` directly.
- **Mark as defensive.** Add `# pragma: no cover` to line 125 with a one-line comment explaining the call-site precondition.
- **Contrive a test that hits the branch.** Construct a class where `typing.get_type_hints` returns a dict missing the "id" key while `"id" in cls.__annotations__` is still True. I cannot construct a realistic call shape that produces that divergence, so this option is least attractive.

The first option (remove) is the cleanest — the check is redundant, not defensive, given that `_has_node_id_marker` already handles None correctly.

### L1. `registry.clear()` between assertions in the typo-lookalike test is unnecessary

Reference: `tests/types/test_definition_order.py:610-640`.

`test_consumer_id_typo_lookalike_nodeid_string_on_relay_node_type_raises` declares two classes (`CategoryNodeNot` with `id: "NotNodeID[int]"`, then `CategoryNodeMy` with `id: "MyNodeID[int]"`) in sequence, both inside `pytest.raises(ConfigurationError)` blocks, with an explicit `registry.clear()` at line 626 between them.

The H1 guard raises at `base.py:206` **before** `base.py:240`'s `registry.register_with_definition(...)` call. Neither class registers with the registry, so there is no state to clear between the two `pytest.raises` blocks. The `_isolate_registry` autouse fixture at `tests/types/test_definition_order.py:29` handles per-test cleanup.

Not a bug — harmless defensive code, no test-correctness impact. Drop the `registry.clear()` call on line 626 if you want the test body to match the contract that the guard fires before registry mutation; keep it as belt-and-suspenders otherwise.

## Positive findings (the implementation got the load-bearing details right)

### `_is_relay_shaped` refactor — single source of truth for the predicate

Reference: `django_strawberry_framework/types/base.py:129-140`.

The spec describes the Relay-shape predicate (`any(issubclass(i, relay.Node) for i in interfaces) or issubclass(cls, relay.Node)`) at two call sites — the H1 guard in `__init_subclass__` and `_build_annotations`'s `suppress_pk_annotation` computation. Rev10 left the contract single-sited at Decision 7's pseudocode but didn't mandate a shared helper. The implementation lifted it into a module-scope `_is_relay_shaped(cls, interfaces)` function called from both `base.py:187` (H1 guard) and `base.py:743` (pk-suppression).

This is a meaningful quality improvement over copy-pasting the disjunction. The two call sites now drift together rather than independently — exactly the property the spec's "single source of truth" framing was reaching for. Worth carrying into the Slice 5 KANBAN body as an unplanned-but-valuable design note.

### Module-scope helpers match the rev8 M1 structure exactly

Reference: `django_strawberry_framework/types/base.py:72-126`.

The three helpers land above `DjangoType`'s class definition in the order rev10 L3 mandated:

1. `_NODEID_STRING_RE = re.compile(r"(?:^|\.)NodeID\[")` at module scope (compiled once per process).
2. `_has_node_id_marker(hint)` returning `typing.get_origin(hint) is Annotated and any(isinstance(arg, NodeIDPrivate) for arg in typing.get_args(hint))` — the rev8 M1 shape exactly.
3. `_id_annotation_is_relay_node_id(cls)` with the try/except `typing.get_type_hints(cls, include_extras=True)` structure and the success path INSIDE the function after the except clause (rev8 M1 fix).

Imports at `base.py:28-36` cover `re`, `typing`, `Annotated`, and `NodeIDPrivate` from `strawberry.relay.types` per rev10 L3.

### Error messages match the test-asserted substrings

- Annotation reject (`base.py:205-212`) contains both `"relay.NodeID"` and `"GlobalID"` — matches `test_consumer_id_annotation_on_relay_node_type_raises`'s assertions and the parallel direct-inheritance test.
- Assigned reject (`base.py:191-204`) contains `"resolve_id"`, `"relay.NodeID"`, and `"display_id"` — matches `test_consumer_id_assigned_strawberry_field_on_relay_node_type_raises`'s three-substring assertion.

### Slice 1 test cluster: 19/19 present with correct shapes

Counted in the test files:

- Four core override tests at `tests/types/test_definition_order.py:338-419`.
- Four converter-bypass tests — three at `tests/types/test_definition_order.py:427-534`, one (nested-ArrayField bypass) at `tests/types/test_converters.py:1040`.
- Eleven Relay-collision tests at `tests/types/test_definition_order.py:542-781` (5 reject + 6 accept).

The rev8 M2 unresolved-string recipe at `tests/types/test_definition_order.py:694-714` implements the synthetic-module / `types.new_class` setup exactly: `uuid`-suffixed stub name, `sys.modules` registration with the "no relay" assertion, `_body` closure setting `__module__`/`__annotations__`/`Meta`, and the `try/finally` with both `sys.modules.pop(stub_name, None)` and `registry.clear()` (rev9 L1 + rev10 M2). No `finalize_django_types()` or schema build, per the guard-only-suppression contract.

The rev8 H1 direct-inheritance reject at `tests/types/test_definition_order.py:559-572` uses `class DirectRelayChild(DjangoType, relay.Node)` with no `Meta.interfaces` — pinning the second half of `_is_relay_shaped`'s disjunction.

### Slice 2 placeholder cleanly deleted

Reference: `tests/types/test_base.py`.

`test_consumer_annotation_overrides_synthesized` and its `@pytest.mark.skip` decorator are gone (`grep` returns no match). `CATEGORY_SCALAR_FIELDS` correctly remains because grep shows it's used by ~25 other tests in the file — the rev6 L3 "grep before deleting" instruction was followed.

### Slice 3 docstring expansion landed

Reference: `django_strawberry_framework/types/base.py:316-339`.

`_consumer_assigned_fields`'s docstring now names all four collection sites and the `consumer_authored_fields` union explicitly. Matches the rev10 Slice 3 contract.

### Temporary `per-file-ignores` for ERA001 removed

Reference: `pyproject.toml`.

The two lines that rev10 L2 added (`"django_strawberry_framework/types/base.py" = ["ERA001"]` and the `definition.py` entry) are removed in the staged diff — the TODO anchors are gone, the pseudo-code is gone, and ERA001 has nothing to flag. Clean reversal.

## Summary

The Slice 1 implementation lands the rev10 spec faithfully:

- All 19 tests present with the correct names, recipes, and assertions.
- Module-scope helpers match the rev8 M1 structure (regex hoisted, `_has_node_id_marker` as the Annotated + NodeIDPrivate check, success path inside the helper).
- Error messages contain the substrings the tests assert.
- Slice 2 placeholder deleted; Slice 3 docstring expanded; ERA001 config revert applied.
- The `_is_relay_shaped` refactor is an unprompted-but-meaningful quality improvement.

One blocker: the `base.py:125` defensive `return False` is dead code and blocks 100% coverage. Removing it (preferred) or marking it `# pragma: no cover` unblocks the Definition of done.

One nit: the `registry.clear()` at `tests/types/test_definition_order.py:626` is unnecessary because the H1 guard raises before registry mutation. Harmless either way.
