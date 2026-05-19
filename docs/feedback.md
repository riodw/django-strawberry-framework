# Final review feedback - spec-015 consumer scalar overrides

## M1. Test Strategy says eleven Relay tests, but lists only ten

The updated spec now consistently says Slice 1 has 19 tests: 4 core + 4 converter-bypass + 11 Relay-collision tests. The Slice checklist and Edge cases section include the rev8 direct-inheritance reject test, `test_consumer_id_annotation_on_direct_relay_node_subclass_raises`.

The Test strategy section still omits that bullet from the detailed Relay list. `docs/spec-015-consumer_overrides_scalar-0_0_6.md:755-766` says "Eleven Relay-collision tests" but enumerates only ten names, skipping the direct-inheritance reject case. That makes the section internally inconsistent and easy for Worker 1 to under-implement if they work from the Test strategy instead of the Slice checklist.

Recommendation: add a bullet immediately after `test_consumer_id_annotation_on_relay_node_type_raises`:

- `test_consumer_id_annotation_on_direct_relay_node_subclass_raises` - direct `class DirectRelayChild(DjangoType, relay.Node)` declaration, no `Meta.interfaces`, `id: int`, raises `ConfigurationError` with the same message contract as the `Meta.interfaces` variant.

## M2. Rev9 registry cleanup reached the spec but not the TODO anchor

Revision 9 L1 correctly adds `registry.clear()` to the unresolved-NodeID-shaped-string test recipe because `types.new_class(...)` registers a `DjangoType` against `Category` even though the test only asserts class creation.

The in-tree TODO at `tests/types/test_definition_order.py:388-404` still only cleans up `sys.modules.pop(stub_name, None)`. It should also mention `registry.clear()` in the same `finally` block, or explicitly say the file's standard fixture teardown handles registry cleanup.

Recommendation: update the TODO pseudo-code to include:

- `registry.clear()` in `finally`, alongside `sys.modules.pop(stub_name, None)`.
- A short note that the cleanup prevents the synthetic `UnresolvedRelayChild` from leaking into later co-resident-type tests.

## L1. `_FakeUnsupportedField` placement is now slightly inconsistent

Revision 9 L2 says Worker 1 may add `_FakeUnsupportedField` in `tests/types/test_definition_order.py` by default, or in `tests/types/test_converters.py` if preferred. But three downstream sections now imply only the nested-`ArrayField` bypass test is allowed outside `test_definition_order.py`:

- `tests/types/test_definition_order.py` TODO says "18 of 19 Slice 1 tests land here" and only names the ArrayField bypass as the external test.
- Test strategy says all new tests land in `tests/types/test_definition_order.py`, with the single exception of the nested-`ArrayField` bypass test.
- Definition of done names `tests/types/test_converters.py` only for the nested-`ArrayField` bypass test.

Recommendation: make `_FakeUnsupportedField` fixture/test placement mandatory in `tests/types/test_definition_order.py`, unless there is a concrete fixture reason comparable to the `_FakeArrayField` case. That keeps the 18-of-19 count and the "single exception" rule true.

## L2. Expanded TODO pseudo-code currently trips ERA001

`uv run ruff check --fix .` now fails on the spec TODO pseudo-code blocks in `django_strawberry_framework/types/base.py` and `django_strawberry_framework/types/definition.py`. The failures are all `ERA001 Found commented-out code`, mostly around the exact helper and guard pseudo-code in the TODO anchors.

The project instructions allow TODO-anchored pseudo-code for staged future slices, so this is not a design problem. It is still worth deciding whether this branch should be lint-clean before Slice 1 lands.

Recommendation: either add targeted `# noqa: ERA001` suppressions to the pseudo-code lines that ruff flags, or explicitly leave this as an accepted temporary lint failure until the TODO anchors are replaced by real code.
