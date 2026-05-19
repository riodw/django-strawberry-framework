# Review feedback - spec-015 consumer scalar overrides

Scope: reviewed revision 7 of `docs/spec-015-consumer_overrides_scalar-0_0_6.md` against the current `DjangoType` / Relay pipeline and the installed Strawberry `relay.NodeID` implementation.

## Findings

### H1. Direct `relay.Node` inheritance is in the guard contract but not pinned by the new tests

Reference: `docs/spec-015-consumer_overrides_scalar-0_0_6.md:75`, `:446-449`, `:684`, `:710-721`.

The guard contract says a Relay-shaped type is either `Meta.interfaces` containing `relay.Node` or a class that directly subclasses `relay.Node`. The proposed tests, however, only describe the `Meta.interfaces = (relay.Node,)` shape.

That leaves a behavior gap: an implementation could accidentally check only `interfaces` and still pass every new collision test, while `class CategoryNode(DjangoType, relay.Node): id: int ...` would fall through to the downstream Strawberry error surface the guard is meant to replace.

Add at least one direct-inheritance guard test, or parametrize the core reject path over both declaration styles:

- `class Meta: interfaces = (relay.Node,)`
- `class CategoryNode(DjangoType, relay.Node)` with no `Meta.interfaces`

The minimum high-value pin is the annotation reject path for direct inheritance (`id: int` raises `ConfigurationError` at class creation). The assigned-`id` reject path could be parametrized the same way if you want full symmetry.

### M1. The `_id_annotation_is_relay_node_id` pseudocode is mechanically wrong and under-specified

Reference: `docs/spec-015-consumer_overrides_scalar-0_0_6.md:517-608`.

The helper pseudocode has two problems that are easy for Worker 1 to copy into broken production code.

First, the `id_hint = hints.get("id")` success path is indented under nothing after `_NODEID_STRING_RE = re.compile(...)`, so the code block is not syntactically coherent. The regex constant should live outside the helper, and the `id_hint` block should remain inside the `try` success path after the `except` block.

Second, the marker-detection prose says to check "both the direct `relay.NodeID[T]` form (`typing.get_origin` returns NodeID-related marker) and the `Annotated[T, NodeIDPrivate]` form." In the installed Strawberry, `relay.NodeID[int]` is already `typing.Annotated[int, NodeIDPrivate()]`; `typing.get_origin(relay.NodeID[int])` is `typing.Annotated`, and the reliable marker is an instance of `strawberry.relay.types.NodeIDPrivate` in `typing.get_args(...)`.

Tighten the spec to the concrete implementation shape:

- import `re`, `typing`, `typing.Annotated`, and `NodeIDPrivate` from `strawberry.relay.types`;
- define `_NODEID_STRING_RE` at module scope;
- implement `_has_node_id_marker(hint)` as `typing.get_origin(hint) is Annotated and any(isinstance(arg, NodeIDPrivate) for arg in typing.get_args(hint))`;
- put the `id_hint = hints.get("id")` success path inside `_id_annotation_is_relay_node_id`.

The tests would catch a bad marker implementation eventually, but the spec currently points at an impossible `get_origin` branch.

### M2. The unresolved string test recipe needs a precise class/module construction

Reference: `docs/spec-015-consumer_overrides_scalar-0_0_6.md:115-116`, `:630`, `:718`.

The guard-only test for `id: "relay.NodeID[int]"` with `relay` not importable is conceptually right, but the spec leaves the setup to "types.new_class or synthetic stub module" without spelling out the critical detail: `typing.get_type_hints(cls, include_extras=True)` resolves class strings through `cls.__module__` globals.

Make the test recipe explicit enough that it cannot accidentally become the resolved-string end-to-end test:

- create a synthetic module name and register a `types.ModuleType` in `sys.modules`;
- do not put `relay` in that module's globals;
- build the `DjangoType` with `types.new_class(...)` and set `__module__` to the synthetic module inside `exec_body` before class creation completes;
- set `__annotations__ = {"id": "relay.NodeID[int]"}` and a normal `Meta` in that namespace;
- assert only class creation succeeds, then clean up `sys.modules`.

Without that specificity, the test can easily run in the real test module where `relay` is imported and accidentally exercise the resolved end-to-end path instead of the fail-soft branch.

### L1. Decision 7a still says the bypass contract has three mandatory tests

Reference: `docs/spec-015-consumer_overrides_scalar-0_0_6.md:665`, compared with `:673`, `:703-708`, and `:725`.

Revision 7 consistently describes four converter-bypass tests elsewhere: unsupported scalar, grouped choices, nested `ArrayField`, and the cross-type enum-cache test. Decision 7a's closing sentence still says "the three Slice 1 tests" and lists only the first three.

Update that sentence to say four tests and include `test_annotation_override_does_not_populate_shared_enum_cache_for_co_resident_types`. This is low risk, but it is exactly the kind of stale count that causes implementation checklists to drift.

### L2. The test-placement wording still contains a small contradiction

Reference: `docs/spec-015-consumer_overrides_scalar-0_0_6.md:692`, `:708`, `:723-725`, and Definition of done around `:734`.

The Test strategy opens with "All new tests land in `tests/types/test_definition_order.py`", then carves out the `ArrayField` exception and says the cross-type enum-cache test may live in either `test_definition_order.py` or `test_converters.py`. Later, the Definition of done treats the cross-type cache test as living in the override-contract host by default.

This is not a behavior bug, but it is avoidable ambiguity. Pick one placement for the cross-type cache test in every section. The spec already leans toward `tests/types/test_definition_order.py`; make that mandatory unless there is a concrete fixture reason to move it.
