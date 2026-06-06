# Review - last commit `47a3c75`

## Findings

### P2 - Annotation-only relation forward refs can still render as `UNRESOLVED!`

`django_strawberry_framework/management/commands/inspect_django_type.py::Command._consumer_authored_row #"field_type = next(sf.type"` now reads consumer-authored fields from `origin.__strawberry_definition__.fields`, which fixes assigned relation/scalar overrides and direct-class annotation overrides. It does not handle the annotation-only relation forward-ref case.

That corner is part of the existing public override contract: `tests/types/test_definition_order.py::test_consumer_id_resolved_relay_nodeid_with_unresolved_sibling_annotation_is_accepted` and `tests/types/test_definition_order.py::test_consumer_non_id_scalar_override_on_relay_node_type_is_accepted` already exercise unresolved sibling annotations / forward-ref relation annotations at type-definition time. After `finalize_django_types()` alone, Strawberry can still leave the field metadata type as its unresolved sentinel; the command then prints `UNRESOLVED!` as if it were a resolved GraphQL type.

I reproduced the shape with a synthetic finalized type:

```python
class ItemType(DjangoType): ...
class CatType(DjangoType):
    items: list["ItemType"]
    class Meta:
        model = Category
        fields = ("id", "items")

finalize_django_types()
call_command("inspect_django_type", "CatType")
```

The `items` row prints `UNRESOLVED!`. If a Strawberry schema is built, Strawberry raises an unresolved-field error instead, which confirms this is not a valid resolved GraphQL type. The command should not silently report it as a field type.

Recommended fix: detect Strawberry's unresolved sentinel in `_consumer_authored_row` / `_render_strawberry_type` and raise `CommandError` with a concrete hint to import a schema via `--schema` or make the forward ref globally resolvable. If the intended contract is "the command only works after a Strawberry schema has been constructed," then tighten the command's validation and docs accordingly; `definition.finalized is True` is not sufficient for this corner. Add a package test for an annotation-only relation forward ref so this does not regress.

### P3 - Combined annotation plus `strawberry.field` is labeled as annotation-only

`django_strawberry_framework/management/commands/inspect_django_type.py::_consumer_converter_label #"source = \"annotation\" if annotated else \"strawberry.field\""` treats any field present in the annotated set as `consumer annotation`, even when the field is also in the assigned-`strawberry.field` set.

That can happen with the normal Strawberry idiom:

```python
class BothType(DjangoType):
    name: str = strawberry.field(resolver=lambda root: "x")
```

The command renders the row as `consumer annotation (scalar)`, hiding the assigned `strawberry.field` override. This is not a runtime break, but the converter column is supposed to name the row that produced the field. Prefer `consumer annotation + strawberry.field (scalar)` for the overlap, or prioritize the assigned-field label when a `StrawberryField` is present. Add a small unit test for the overlap case.

### P3 - The command module docstring is now stale

`django_strawberry_framework/management/commands/inspect_django_type.py #"origin.__annotations__"` still says the command reads the resolved GraphQL annotation from `origin.__annotations__` as the authoritative record. That is no longer true for consumer-authored assigned fields; the new implementation correctly reads those from finalized Strawberry field metadata.

Update the module docstring so future work does not reintroduce the old assumption. The current code comments in `_consumer_authored_row` are accurate; the top-level contract text just needs to catch up.

## What Looks Correct

- The previous P1 is substantially fixed for assigned scalar, assigned relation, annotation-only scalar, optional scalar, and unsupported-field scalar override cases.
- The dispatch order in `Command._resolve_row` is right: Relay-suppressed pk first, then consumer-authored fields, then auto relation/scalar rows.
- The live `BranchType.shelves` smoke output is correct: `[ShelfType!]!`, `no (list)`, `consumer strawberry.field (relation)`.
- Normal auto rows still render correctly for `BookType`: scalar rows use matched `SCALAR_MAP` keys, choice rows use `choice enum`, and relation rows use the friendly relation labels.
- The `bld-final.md` closing summary now matches the resolved full-gate state instead of repeating the old kanban failure exception as current.
- The kanban fixture comment now uses a symbol-qualified source reference.

## Review Scope

Reviewed `HEAD~1..HEAD` for:

- `django_strawberry_framework/management/commands/inspect_django_type.py`
- `tests/management/test_inspect_django_type.py`
- `examples/fakeshop/tests/test_inspect_django_type.py`
- `examples/fakeshop/test_query/test_kanban_api.py`
- `docs/builder/bld-final.md`

Validation I ran:

- `uv run python examples/fakeshop/manage.py inspect_django_type BranchType --schema config.schema`
- `uv run python examples/fakeshop/manage.py inspect_django_type BookType --schema config.schema`
- two ad hoc `manage.py shell -c` command checks for the forward-ref relation and annotation-plus-assignment label cases

I did not run pytest or the full gate during this review.
