# spec-034 Permissions - Second Implementation Review

Reviewed the post-build permissions implementation against `docs/spec-034-permissions-0_0_10.md`
and the repo rules in `AGENTS.md`. Scope was the live tree, with emphasis on the
new public cascade helper, fakeshop activation, tests, and card-completion docs.

No `pytest` run was performed; `AGENTS.md` says not to run pytest unless explicitly
asked. The findings below are from source/diff review.

## Findings

### H1 - The 034 change bumped package version state even though the spec assigns that to the joint 0.0.10 cut

`docs/spec-034-permissions-0_0_10.md::Decision 13 #"No slice edits"` is explicit:
`pyproject.toml`, `django_strawberry_framework/__init__.py` `__version__`,
`tests/base/test_init.py::test_version`, and `uv.lock` are not owned by this card.
The same rule is repeated in the Definition of done and Slice 5 doc-update section.
`KANBAN.md #"WIP-ALPHA-035-0.0.10"` still shows the optimizer robustness sibling as
WIP, so the joint `0.0.10` cut has not completed.

Current tree violates that boundary:

- `pyproject.toml #"version = \"0.0.10\""` is bumped.
- `django_strawberry_framework/__init__.py #"__version__ = \"0.0.10\""` is bumped.
- `uv.lock #"name = \"django-strawberry-framework\""` is bumped to `0.0.10`.
- `tests/base/test_init.py::test_version` still asserts `0.0.9`, so the version pin
  would fail as written.

This is both a release-process bug and a direct test failure. The root fix is to
revert the version-file edits until the actual joint `0.0.10` release cut, not to
paper over it by changing `test_version` now. If the maintainer intends this commit
to be the joint cut, then `WIP-ALPHA-035-0.0.10` and the release docs need to be
closed in the same change and `test_version` must be updated as part of that cut.

### H2 - New catalog tests hand-roll products rows instead of going through the products services

`AGENTS.md` is explicit for catalog/auth coverage: the first line is
`seed_data(N)` or `create_users(N)` from `apps.products.services`, and tests must
not hand-roll `Category` / `Item` / `Property` / `Entry` / `User` rows outside the
seed-helper exception. The spec repeats the real-service requirement for Slice 4.

The new live cascade coverage starts with `create_users(1)`, but then builds the
catalog graph directly in `examples/fakeshop/test_query/test_products_api.py::_seed_cascade_split`
with `models.Category.objects.create`, `models.Property.objects.create`,
`models.Item.objects.create`, and `models.Entry.objects.create`. The same direct
products-model setup appears in the new package-level pins, including:

- `tests/test_permissions.py::test_transitive_cascade_two_deep`
- `tests/test_permissions.py::test_fields_scopes_walk`
- `tests/test_connection.py::test_connection_over_cascading_type_narrows_edges_and_total_count`
- `tests/test_list_field.py::test_list_field_default_resolver_applies_cascade`
- `tests/test_relay_node_field.py::test_node_refetch_of_cascade_hidden_row_returns_null`
- `tests/optimizer/test_extension.py::test_cascading_target_downgrades_join_to_prefetch`

This creates a second, test-local catalog factory shape that bypasses the products
service contract. It also makes future seeder changes invisible to the tests that
claim to exercise fakeshop behavior. The high-quality fix is to move the
deterministic cascade fixture into `examples/fakeshop/apps/products/services.py`
as a named seed helper, then call that helper from the live/app tests after
`create_users(1)` or `seed_data(N)`. For package-internal tests that need tiny
bespoke graphs rather than products acceptance behavior, use synthetic managed
models as the file already does for non-catalog shapes, instead of hand-rolling
the products catalog models.

### M1 - The multi-DB alias test does not actually observe the cascade subquery alias

`tests/test_permissions.py::test_multi_db_subquery_pinned_to_caller_alias` is meant
to pin Decision 8: every target visibility subquery must be built with
`.using(queryset.db)`. The implementation does that correctly in
`django_strawberry_framework/permissions.py::_walk #"using(queryset.db)"`, but the
test does not prove it.

The test checks `result.db == "shard_b"` and then constructs a fresh
`AliasTarget._default_manager.using(result.db).all()` inside the assertion block.
That fresh queryset is not the queryset used by the cascade. A broken
implementation that built the target subquery from the default alias could still
leave `result.db == "shard_b"` and still satisfy the fresh-base assertion.

The fix is to make the target hook capture the `qs.db` it actually receives and
assert it equals `"shard_b"`, or otherwise inspect the real RHS queryset produced
by the walk. As written, the dedicated upstream-invariant pin can pass while the
invariant it names is broken.

### M2 - The no-existence-leak gate test still uses a no-op cascade path

`tests/test_permissions.py::test_gate_denial_no_existence_leak` calls
`apply_cascade_permissions(category_type, Category.objects.all(), _INFO)` directly.
`Category` is the top of the products chain and has no cascadable forward edge, so
that direct cascade call does not invoke `category_type.get_queryset` and does not
drop the private row. The gate then raises on input shape before row evaluation,
which means the byte-identical error assertion passes even if no cascade narrowing
happened at all.

This is the same causal weakness the integration pass already fixed in the other
gate-composition tests. Rebuild this pin over a shape where cascade visibility
actually changes the queryset, such as an `Item` queryset narrowed through a hidden
`Category`, then assert both the passing and denying paths against that genuinely
cascade-narrowed queryset.

### M3 - The docs disagree with the implemented `view_item` semantics

The code and the revised live test now establish a specific per-edge rule:
`examples/fakeshop/apps/products/schema.py::ItemType.get_queryset` returns
non-private items for a `view_item` user without cascading into `Category`, and
`examples/fakeshop/test_query/test_products_api.py::test_cascade_view_item_user_matrix`
asserts an entry whose only private linkage is `item.category` survives when its
property is public.

Several standing docs still say the broader or opposite thing:

- `TODAY.md #"a view_<model> user sees non-private rows but still loses entries under hidden targets"`
  implies every per-model permission user still loses rows under hidden targets.
- `docs/spec-034-permissions-0_0_10.md #"test_cascade_view_item_user_matrix"` still
  says entries drop when the entry-level cascade reaches a hidden category through
  `item`, even though the Revision 7 ledger and the test body now say the drop is
  through `property`.
- `KANBAN.md #"Status: In progress"` appears under the `DONE-034-0.0.10` card,
  leaving the generated board internally inconsistent.

Pick the intended semantics and make the docs match it. If model-level view
permission is meant to bypass target-category cascade for that edge, update the
spec/TODAY/KANBAN wording to the exact per-edge matrix. If the intended security
contract is that `view_item` still respects `CategoryType` visibility, then the
product hook should call `apply_cascade_permissions` after its own
`is_private=False` filter and the current test expectation should flip.

### L1 - Stale permissions TODOs survived the Slice 5 doc/comment cleanup

There are still comments that point readers at already-shipped or renumbered
permissions work:

- `examples/fakeshop/apps/products/schema.py #"TODO-ALPHA-034-0.0.10 permissions"` in
  the module docstring still presents permissions as a future Layer-3 card.
- `examples/fakeshop/apps/products/schema.py #"Future: drop this entry"` ties the
  field-level permission story to `TODO-ALPHA-034-0.0.10`, but the spec moved
  read-side field gates to the FieldSet card.
- `examples/fakeshop/apps/products/filters.py #"TODO-ALPHA-027-0.0.10 permissions"`
  still names a stale card id and describes a queryset-scoping permission variant
  as owned by the permissions slice.

These are low severity, but they matter in this repo because TODO anchors are used
as design-doc breadcrumbs. Sweep the remaining products comments and retarget them
to the shipped `DONE-034-0.0.10` behavior or the deferred FieldSet card, as
appropriate.

## Notes

The core cascade implementation in `django_strawberry_framework/permissions.py`
is coherent on the main contract: one `_is_cascadable_edge` predicate, registry
primary lookup, `has_custom_get_queryset()` skip, nullable-FK-preserving `Q` shape,
`queryset.db` alias pinning, and one sync-misuse path via
`utils/querysets.py::apply_type_visibility_sync`. I did not find a production bug
inside the walk itself. The blocking issues are release-boundary/test-rule drift
and test assertions that do not fully prove the contracts they name.
