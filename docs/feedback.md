# Feedback: `docs/spec-028-orders-0_0_8.md`

Reviewed the updated spec against the current ordering source, tests, generated docs, glossary CSV/checker, and reference-style links.

The previous state-model and version-boundary problems are materially improved: the spec now clearly says this is the shipped `0.0.8` implementation record, the slice checklist is checked, the pre-implementation state is labeled as historical, and the `0.0.9` language is framed as follow-up planning.

## Blocking

1. Decision 8's async permission-hook contract contradicts the shipped implementation.

   The spec still says async ordering does **not** wrap permission hooks:

   - `docs/spec-028-orders-0_0_8.md #"`OrderSet.apply_async` does **not** wrap consumer hooks"`
   - `docs/spec-028-orders-0_0_8.md #"a consumer hook that issues a blocking ORM call ... WILL block the event loop"`
   - `docs/spec-028-orders-0_0_8.md #"N7 — `apply_async` blocking-hook caveat added"`

   The shipped code and tests say the opposite:

   - `django_strawberry_framework/orders/sets.py::OrderSet.apply_async #"await sync_to_async(cls._run_permission_checks, thread_sensitive=True)"`
   - `django_strawberry_framework/orders/sets.py::OrderSet.apply_async #"so a consumer's `check_*_permission` hook that performs a blocking ORM read does not block the event loop"`
   - `tests/orders/test_sets.py::test_orderset_apply_async_runs_check_permission_in_sync_to_async`

   Fix Decision 8 and the revision-history note so they describe the shipped behavior: `apply_async` resolves the request synchronously, then dispatches `_run_permission_checks` through `sync_to_async(thread_sensitive=True)`, while parsing and `queryset.order_by(...)` remain unwrapped because they are pure queryset construction.

   The same section should also stop saying the apply pipeline calls `cls.check_permissions(input_value, request)`:

   - `docs/spec-028-orders-0_0_8.md #"The apply pipeline calls `cls.check_permissions(input_value, request)`"`
   - `django_strawberry_framework/orders/sets.py::OrderSet.apply_sync #"cls._run_permission_checks(input_value, request)"`
   - `django_strawberry_framework/orders/sets.py::OrderSet.check_permissions #"type(self)._run_permission_checks(getattr(self, \"_input_value\", None), request)"`

   The correct shipped contract is: `apply_sync` / `apply_async` call the classmethod `_run_permission_checks(input_value, request)`; the instance method `check_permissions(self, request)` exists only as a cookbook-compatible delegate that reads `self._input_value`.

## High

2. The test plan still names tests that do not exist, and at least one claimed behavior test appears missing.

   Examples of stale or missing names in the spec:

   - `docs/spec-028-orders-0_0_8.md #"`test_check_permission_fires_parent_relation_gate_on_active_branch`"`
   - `docs/spec-028-orders-0_0_8.md #"`test_check_permission_fires_child_field_gate_on_active_nested_field`"`
   - `docs/spec-028-orders-0_0_8.md #"`test_check_permissions_only_fires_for_active_order_fields`"`
   - `docs/spec-028-orders-0_0_8.md #"`test_apply_extracts_request_from_info_context_request_attribute`"`
   - `docs/spec-028-orders-0_0_8.md #"`test_order_input_type_resolver_wraps_as_list_under_strawberry_schema`"`
   - `docs/spec-028-orders-0_0_8.md #"`test_order_accepts_field_not_in_djangotype_meta_fields`"`

   Current source has different names for several of these:

   - `tests/orders/test_sets.py::test_orderset_check_permission_active_relatedorder_branch_fires_parent_gate`
   - `tests/orders/test_sets.py::test_orderset_check_permission_active_relatedorder_branch_fires_child_gate`
   - `tests/orders/test_sets.py::test_orderset_check_permission_denies_for_active_field`
   - `tests/orders/test_sets.py::test_orderset_request_from_info_reads_context_request_attribute`
   - `tests/orders/test_inputs.py::test_order_input_type_returns_element_annotation_for_orderset_subclass`

   More importantly, `rg` found no source test named `test_order_accepts_field_not_in_djangotype_meta_fields`, and I did not find an obvious equivalent assertion covering "order on columns not selectable by the `DjangoType`". Either add the test the spec claims, or downgrade that paragraph from "pinned by test" to "documented behavior". The same applies to the dedicated SDL wrapper test: the fakeshop schema uses `list[order_input_type(...)]`, but the exact unit test named in the spec does not exist.

3. Raw line-number references remain in the standing spec.

   The spec acknowledges this but treats revision-history breadcrumbs as exempt:

   - `docs/spec-028-orders-0_0_8.md #"Revision-history breadcrumbs retain their raw line refs as historical context"`
   - `docs/spec-028-orders-0_0_8.md #"Revision-history breadcrumbs intentionally retained as historical context"`

   The repo instruction does not exempt revision-history sections inside standing specs. Current examples:

   - `docs/spec-028-orders-0_0_8.md #"[`finalizer.py:478-600`][finalizer]"`
   - `docs/spec-028-orders-0_0_8.md #"[`registry.py:43-50`][registry]"`
   - `docs/spec-028-orders-0_0_8.md #"[`filters/inputs.py:53,183`][filters-inputs]"`
   - `docs/spec-028-orders-0_0_8.md #"`types/base.py:88`"`
   - `docs/spec-028-orders-0_0_8.md #"line 635"`

   Convert these to symbol-qualified or unique-substring references. If the project intentionally wants historical raw-line breadcrumbs inside revision history, update the repo convention first; otherwise this spec remains non-compliant.

## Medium

4. The implementation-plan table still says `clear_order_input_namespace` clears module globals.

   The stale table entry says:

   - `docs/spec-028-orders-0_0_8.md #"`clear_order_input_namespace` clears module globals"`

   The shipped lifecycle says globals stay parked:

   - `docs/spec-028-orders-0_0_8.md #"leaves materialized module globals parked"`
   - `django_strawberry_framework/orders/inputs.py::clear_order_input_namespace #"Materialized class objects are intentionally left parked"`
   - `tests/orders/test_inputs.py::test_clear_order_input_namespace_leaves_module_globals_parked`

   Change the Slice 2 table row to say it clears ledgers/caches and leaves module globals parked. Also consider adding `_field_specs` to DoD items 6 and 10's clear list, because the implementation clears it and Decision 9 already documents it.

5. The status line says "three" closure pieces but lists four.

   The Status line says:

   - `docs/spec-028-orders-0_0_8.md #"The real close was three INDEPENDENT pieces"`

   It then enumerates `(a)`, `(b)`, `(c)`, and `(d)`. Change "three" to "four" or merge two bullets. This is editorial, but it sits in the first paragraph of the final implementation record.

## Verified

- `uv run python scripts/check_spec_glossary.py --spec docs/spec-028-orders-0_0_8.md` passes: 44 terms, all linked.
- All 104 reference-style link definitions are used and resolve to existing repo targets or external URLs.
- The live fakeshop ordering test count is 14 by function name in `examples/fakeshop/test_query/test_library_api.py`.
- `tests/orders/` has the expected seven files.
- `django_strawberry_framework/orders/__init__.py` now matches the intended export split: `OrderSetMetaclass` remains in `__all__`; `OrderArgumentsFactory` is not imported/re-exported from the package entry point.
- I did not run pytest; repo instructions say not to run pytest unless explicitly asked.
