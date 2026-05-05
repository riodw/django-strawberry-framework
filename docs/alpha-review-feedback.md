# Alpha review feedback

## Optimizer plan-cache key correctness follow-up

Scope reviewed: commits `cbe1519` through `9ba0b64`, limited to changed Python files. Both issues below are in `django_strawberry_framework/optimizer/extension.py` and affect B1 plan-cache correctness.

### Finding 1 — Fragment-spread directives are omitted from the directive-variable cache key

`_walk_directives()` collects directives on ordinary AST nodes before recursing, but when a child is a `FragmentSpreadNode` it jumps directly to the fragment definition. That misses directives attached to the spread itself, such as `...ItemBits @include(if: $show)`.

Why this matters: `_build_cache_key()` includes only variables collected by `_collect_directive_var_names()`. If a spread-level `@skip` or `@include` variable is omitted, two executions with different values for that variable can share one cached plan even though they select different fields.

Confirmed reproduction: parsing `query Q($show: Boolean!) { allItems { ...ItemBits @include(if: $show) } } fragment ItemBits on ItemType { category { name } }` and calling `_collect_directive_var_names(operation, fragments=fragments)` currently returns `frozenset()` instead of `frozenset({"show"})`.

Fix spec:

- Update `_walk_directives()` so a `FragmentSpreadNode` child has its own directives processed before the walker descends into the referenced fragment definition.
- Keep the existing behavior that directives inside the fragment definition are also collected.
- Avoid double-count concerns by continuing to collect into a `set[str]`.
- Add a focused unit test in `tests/optimizer/test_extension.py` where a named fragment spread carries `@include(if: $show)` or `@skip(if: $show)` and assert `_collect_directive_var_names(...) == frozenset({"show"})`.
- Add, if practical, a cache-key-level test proving the directive variable changes `_build_cache_key()` relevant-vars when the directive sits on the spread rather than inside the fragment body.

### Finding 2 — Multi-operation documents collide in the plan cache

`_build_cache_key()` uses `hash(loc.source.body)` when source location is present. For a GraphQL document with multiple operations, `loc.source.body` is the full document, not the selected operation. Two operations in the same document can therefore share the same document hash when they have the same root response path and target model.

Why this matters: plan shape depends on the selected operation's AST. If `query A { allItems { name } }` warms the cache before `query B { allItems { category { name } } }`, operation B can reuse A's scalar-only plan and lose the relation optimization.

Confirmed reproduction: parsing `query A { allItems { name } } query B { allItems { category { name } } }` and building keys for both operation definitions with the same `path=("allItems",)` and target model currently produces equal cache keys.

Fix spec:

- Change the document component of `_build_cache_key()` to hash the selected operation AST, not the full source body.
- Prefer `hash(print_ast(operation))` unconditionally for correctness. If performance becomes a concern later, introduce a small helper that slices the operation's source range rather than using the whole source body.
- Include the selected operation name in the hashed material or rely on `print_ast(operation)`, which includes named operation text. The key requirement is that distinct operation definitions in the same document produce distinct document components when their ASTs differ.
- Update the `_build_cache_key()` docstring and comments so they no longer claim the source-body hash represents the selected query string.
- Add a direct test in `tests/optimizer/test_extension.py` with two named operations in one parsed document:
  - `query A { allItems { name } }`
  - `query B { allItems { category { name } } }`
  Build synthetic infos for each operation with the same root path and target model, then assert the cache keys differ.
- Consider an integration test if the direct test is not sufficient: execute the same multi-operation document once with `operation_name="A"` and once with `operation_name="B"` and assert the extension records two cache misses and two cache entries.

## Pseudocode for regression tests

### Fragment-spread directive variable collection

```python
def test_collect_directive_var_names_includes_fragment_spread_directives():
    doc = parse(
        "query Q($show: Boolean!) { "
        "  allItems { ...ItemBits @include(if: $show) } "
        "} "
        "fragment ItemBits on ItemType { category { name } }"
    )
    operation = first_operation_definition(doc)
    fragments = fragment_definitions_by_name(doc)

    names = _collect_directive_var_names(operation, fragments=fragments)

    assert names == frozenset({"show"})
```

```python
def test_cache_key_includes_fragment_spread_directive_variable_value():
    doc = parse(
        "query Q($show: Boolean!) { "
        "  allItems { ...ItemBits @include(if: $show) } "
        "} "
        "fragment ItemBits on ItemType { category { name } }"
    )
    operation = first_operation_definition(doc)
    fragments = fragment_definitions_by_name(doc)
    info_false = SimpleNamespace(
        operation=operation,
        fragments=fragments,
        variable_values={"show": False},
        path=SimpleNamespace(key="allItems", prev=None),
    )
    info_true = SimpleNamespace(
        operation=operation,
        fragments=fragments,
        variable_values={"show": True},
        path=SimpleNamespace(key="allItems", prev=None),
    )

    assert DjangoOptimizerExtension._build_cache_key(info_false, Item) != (
        DjangoOptimizerExtension._build_cache_key(info_true, Item)
    )
```

### Multi-operation document cache-key separation

```python
def test_cache_key_differs_for_named_operations_in_same_document():
    doc = parse(
        "query A { allItems { name } } "
        "query B { allItems { category { name } } }"
    )
    operation_a = operation_definition_named(doc, "A")
    operation_b = operation_definition_named(doc, "B")
    info_a = SimpleNamespace(
        operation=operation_a,
        fragments={},
        variable_values={},
        path=SimpleNamespace(key="allItems", prev=None),
    )
    info_b = SimpleNamespace(
        operation=operation_b,
        fragments={},
        variable_values={},
        path=SimpleNamespace(key="allItems", prev=None),
    )

    assert DjangoOptimizerExtension._build_cache_key(info_a, Item) != (
        DjangoOptimizerExtension._build_cache_key(info_b, Item)
    )
```

```python
@pytest.mark.django_db
def test_cache_separates_operation_names_in_same_document():
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

    schema = strawberry.Schema(query=Query, extensions=[ext])
    document = (
        "query A { allItems { name } } "
        "query B { allItems { name category { name } } }"
    )

    result_a = schema.execute_sync(document, operation_name="A")
    result_b = schema.execute_sync(document, operation_name="B")

    assert result_a.errors is None
    assert result_b.errors is None
    assert ext.cache_info().misses == 2
    assert ext.cache_info().hits == 0
    assert ext.cache_info().size == 2
```
