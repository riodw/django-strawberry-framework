# Review - last commit `513b269`

## Findings

### P1 - `inspect_django_type` does not handle consumer-authored selected fields

`django_strawberry_framework/management/commands/inspect_django_type.py::Command._resolve_row`
still routes every selected relation through `_relation_row` and every selected scalar through
`_scalar_row` unless it is the Relay-suppressed pk. It never checks
`DjangoTypeDefinition.consumer_authored_fields`.

That is not just a labeling nit. `django_strawberry_framework/types/base.py::_build_annotations`
intentionally skips auto-synthesis for consumer-authored relation and scalar fields, and
`django_strawberry_framework/types/base.py::_consumer_assigned_fields` documents this as a
four-corner public override contract. Existing tests already pin the dangerous shape:
`tests/types/test_definition_order.py::test_assigned_scalar_field_override_keeps_consumer_resolver`
asserts that an assigned scalar override does **not** appear in `CategoryType.__annotations__`.

Result: a valid finalized `DjangoType` can make the new command fail or lie:

- Consumer-assigned scalar field, e.g. `@strawberry.field def name(...) -> str`: `_scalar_row`
  indexes `origin.__annotations__["name"]`, but that annotation is deliberately absent, so the
  command raises `KeyError`.
- Consumer-assigned relation field, e.g. `@strawberry.field def items(...) -> list[ItemType]`:
  `_relation_row` has the same `origin.__annotations__[field.name]` assumption.
- Consumer-annotated scalar field, e.g. `description: int` over a `TextField`: the command may print
  the resolved annotation correctly, but the converter column still reports `SCALAR_MAP[TextField]`
  even though no `SCALAR_MAP` converter fired.
- Unsupported model fields with a consumer-authored annotation can reach the new
  `_matched_scalar_key` fallback on a finalized type, contrary to that helper's docstring claim that
  the fallback is unreachable for finalized types.

This violates the Slice 2 command contract: the command is supposed to print every selected field
with the resolved GraphQL type and the row that produced it. For consumer-authored fields, the row is
not `SCALAR_MAP` or the relation auto-converter; it is the consumer override.

Recommended fix: branch on `field.name in definition.consumer_authored_fields` before the relation /
scalar converter branches in `_resolve_row`. Use the existing definition metadata to label the
converter accurately, for example `consumer annotation` vs `consumer strawberry.field`, with scalar
vs relation detail if helpful. For annotation-only overrides, `origin.__annotations__` is usable. For
assigned-field overrides, read the finalized Strawberry field metadata instead of assuming
`origin.__annotations__` contains the field. Add package or example command coverage for at least:
assigned scalar, assigned relation, annotation-only scalar whose annotation differs from the Django
field converter, and annotation-only unsupported scalar field.

### P3 - `bld-final.md` still ends with the old red-gate summary

`docs/builder/bld-final.md #"The final gate is green on every command except"` still says the final
gate is green except for the pre-existing kanban failures. The post-feedback section at the top says
the kanban failures are resolved and the new full gate is `1391 passed, 3 skipped, 0 failed`.

The historical failed gate table is fine because the new top note explicitly labels it as the
`2d1f296` snapshot. The bottom summary should be updated to match the current state: the follow-up
gate is fully green, and the old kanban failures are historical/resolved.

### P3 - New code comment uses a non-symbol-qualified source reference

`examples/fakeshop/test_query/test_kanban_api.py #"apps/kanban/signals.py:"` adds a source reference
split across two comment lines. Repo convention asks code comments to use symbol-qualified source
references, so this should be rewritten as something like
`examples/fakeshop/apps/kanban/signals.py::_validate_done_card_has_glossary_link`.

This is low severity, but it is exactly the kind of small reference drift the standing-doc/source
reference rule is trying to prevent.

## What Looks Correct

- The kanban fixture fix is the right direction. The signal invariant stays in production code, and
  the tests now seed the glossary link before flipping a card to `done`.
- The `transaction.atomic()` placement in
  `examples/fakeshop/apps/kanban/tests/test_signals.py::test_done_card_last_glossary_link_cannot_be_deleted_or_moved`
  is correct: `pytest.raises` enters first and the atomic savepoint exits first, so the expected
  `ValidationError` rolls back before the next protected operation runs.
- The `--schema` cold-path test now evicts cached schema modules before clearing the registry, which
  exercises the real import-time registration/finalization path instead of relying on an already
  imported module.
- The added command failure tests cover the previously unhit `--schema` import failure and bare-name
  registry-miss branches.
- `_RELATION_KIND_LABELS` matches the current internal `relation_kind` tokens: `"many"`,
  `"forward_single"`, `"reverse_many_to_one"`, and `"reverse_one_to_one"`. Existing relation-kind
  tests also pin those tokens.
- The MRO scalar label improvement is correct for auto-synthesized scalar fields: a subclass of
  `TextField` should report the matched `TextField` `SCALAR_MAP` row, not the subclass name.

## Review Scope

Reviewed `HEAD~1..HEAD` for:

- `django_strawberry_framework/management/commands/inspect_django_type.py`
- `tests/management/test_inspect_django_type.py`
- `examples/fakeshop/tests/test_inspect_django_type.py`
- `examples/fakeshop/apps/kanban/tests/test_signals.py`
- `examples/fakeshop/test_query/test_kanban_api.py`
- `docs/builder/bld-final.md`
- `docs/builder/build-029-consumer_dx_cleanup-0_0_9.md`

I did not run pytest or the full gate during this review. The commit message records the full gate as
green, but the P1 above is a missing valid-shape test case rather than a failure in the tested happy
paths.
