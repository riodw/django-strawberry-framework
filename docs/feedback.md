# Adversarial Review: `DjangoListField` Argument Surface (spec-050 / card-050)

## Summary verdict

The implementation of [`spec-050-list_field_arguments-0_0_15.md`][spec-050] represents a mature,
rigorously engineered pagination and ordering pipeline for [`DjangoListField`][list-field]. The
ten preceding review-and-remediation cycles successfully resolved foundational architectural
challenges: the request budget authority was completely decoupled from mutable public policy
objects, invocation-scoped order normalization ledgers prevent cross-task leakage without polluting
user context, and async cleanup semantics correctly distinguish recoverable errors from control
signals ([`asyncio.CancelledError`][resource-policy]).

However, this adversarial audit of the complete implementation and [build record][build-050]
reveals critical vulnerabilities, defect handling gaps, and specification-to-code divergences:

1. **P1 — Non-deterministic ordering bypass via raw SQL random functions in `extra`:**
   [`_is_random_order_term`][list-field] only recognizes `"?"` and Django's [`Random`][list-field]
   expression instances. When raw SQL function strings such as `"RAND()"` (SQLite/MySQL) or
   `"RANDOM()"` (PostgreSQL) are injected via `extra(order_by=[...])`, they take precedence in
   [`_selected_ordering`][list-field], evade [`_has_no_random_terms`][list-field], and cause the
   non-zero offset guard to accept non-deterministic pagination.
2. **P2 — Unmapped `"alias"` defect code in `_validate_post_orderset_result`:**
   [`_validate_post_orderset_result`][querysets] validates [`OrderSet`][orders-sets] results
   against [`_seal_or_defect`][querysets], but omits `"alias"` from its explicit defect message
   dictionary. If an alias defect occurs, it triggers a framework defect warning claiming a missing
   arm rather than a clean configuration error.
3. **P2 — Evaluation policy asymmetry between `get_queryset` and `OrderSet.apply_*`:**
   [`_ORDERSET_RESULT_POLICY`][querysets] strictly enforces `require_unevaluated=True`, but
   [`_LIST_ARGUMENT_VISIBILITY_POLICY`][querysets] leaves `require_unevaluated=False`. When
   `get_queryset` returns an already-evaluated queryset, the list argument pipeline silently clones
   the query and discards `_result_cache`, causing redundant queries and leaving the existing
   `"evaluated"` visibility error arm completely unreachable.
4. **P2 — Order normalization purity validation is bypassed when `offset` is absent or zero:**
   [`_order_normalization_scope`][list-field] only opens a capture ledger when `offset > 0`. A
   query supplying `orderBy` with `limit` alone bypasses purity checking for impure
   `_normalize_input` implementations.
5. **P3 — Build record self-contradiction regarding floor verification scope:**
   The [build record][build-050] states in its gate narrative that a narrowed 4-path scope was
   measured as the green floor gate, while its floor scope definition section explicitly declares
   that narrowing the declared 17-path scope is not this card's floor verification.

The implementation cannot be considered final until these findings are resolved and accompanied by
reproducible failure proofs.

## Open findings

### P1-1: Raw SQL random ordering in `extra(order_by=[...])` bypasses the non-zero offset guard

- **Affected symbols:**
  - [`django_strawberry_framework/list_field.py::_is_random_order_term`][list-field]
  - [`django_strawberry_framework/list_field.py::_selected_ordering`][list-field]
  - [`django_strawberry_framework/list_field.py::_has_no_random_terms`][list-field]
  - [`django_strawberry_framework/list_field.py::_check_nonzero_offset_guard`][list-field]

- **Mechanism:**
  The non-zero offset guard ([`_check_nonzero_offset_guard`][list-field]) enforces that any
  request with `offset > 0` must have a deterministic ordering. It uses
  [`_selected_ordering`][list-field] to inspect the ordering that Django's compiler will actually
  execute. Django compiler precedence dictates that `query.extra_order_by` overrides
  `query.order_by`.

  [`_has_no_random_terms`][list-field] walks the selected ordering terms using
  [`_is_random_order_term`][list-field]:
  ```python
  def _is_random_order_term(term: Any) -> bool:
      if term == "?" or isinstance(term, Random):
          return True
      return isinstance(getattr(term, "expression", None), Random)
  ```
  In Django, raw SQL ordering added via `queryset.extra(order_by=[...])` populates
  `query.extra_order_by` with raw string literals, such as `"RAND()"` (SQLite/MySQL), `"RANDOM()"`
  (PostgreSQL), or `"NEWID()"` (SQL Server).

  When a resolver or hook supplies `extra(order_by=["RAND()"])`:
  1. [`_selected_ordering`][list-field] selects `query.extra_order_by`, yielding `("RAND()",)`.
  2. [`_is_random_order_term("RAND()")`][list-field] evaluates:
     - `term == "?"` -> `False`
     - `isinstance(term, Random)` -> `False`
     - `getattr(term, "expression", None)` -> `None`
  3. [`_is_random_order_term`][list-field] returns `False`, so
     [`_has_no_random_terms`][list-field] returns `True`.
  4. If the client also supplied active `orderBy` terms (or if `queryset.ordered` is true),
     [`has_active_order`][list-field] passes as `True`.
  5. The query executes `ORDER BY RAND(), <client_order> LIMIT N OFFSET M`.

  This directly causes non-deterministic row selection across pagination offsets, violating
  [spec-050 Decision 6][spec-050].

  Furthermore, the [build record][build-050] (lines 174–178) notes that Django spells random orders
  as `RAND()` on SQLite/MySQL and `RANDOM()` on PostgreSQL. However, that observation was only used
  to adjust a test assertion constant (`_RANDOM_ORDER_SQL = "RAND"`), leaving the production
  classifier [`_is_random_order_term`][list-field] completely unaware of string-based SQL random
  functions.

- **Required correction:**
  Extend [`_is_random_order_term`][list-field] to inspect string terms for raw SQL random function
  invocations (e.g. matching `"RAND("`, `"RANDOM("`, `"NEWID("` case-insensitively, or rejecting
  opaque `extra_order_by` SQL clauses when an offset is requested). Add live tests in both
  [`test_list_field_api.py`][live-sync] and [`test_list_field_async_api.py`][live-async] verifying
  that `extra(order_by=["RAND()"])` and `extra(order_by=["RANDOM()"])` are rejected under positive
  offset pagination.

---

### P2-1: Missing `"alias"` arm in `_validate_post_orderset_result` defect map

- **Affected symbols:**
  - [`django_strawberry_framework/utils/querysets.py::_validate_post_orderset_result`][querysets]
  - [`django_strawberry_framework/utils/querysets.py::_seal_or_defect`][querysets]
  - [`django_strawberry_framework/utils/querysets.py::_defect_message`][querysets]

- **Mechanism:**
  [`_validate_post_orderset_result`][querysets] validates and seals querysets returned from
  [`OrderSet.apply_sync`][orders-sets] and [`OrderSet.apply_async`][orders-sets] through
  [`_seal_or_defect`][querysets].

  The canonical sequence of defect codes defined in [`_seal_or_defect`][querysets] comprises nine
  entries:
  `type` -> `table` -> `untrusted` -> `routing` -> `evaluated` -> `sliced` -> `combined` ->
  `projection` -> `alias`.

  When formatting defect messages, [`_validate_post_orderset_result`][querysets] builds:
  ```python
  shape_message = (
      f"{method_name} must return an unevaluated, unsliced, uncombined "
      f"QuerySet of {model_name} rows; got {defect[0]} defect ({defect[1]})."
  )
  messages = dict.fromkeys(
      (
          "type",
          "table",
          "untrusted",
          "evaluated",
          "sliced",
          "combined",
          "projection",
      ),
      shape_message,
  )
  messages["routing"] = f"{method_name} changed database routing intent; {defect[1]}."
  raise ConfigurationError(_defect_message(messages, defect, method_name))
  ```
  `"alias"` is omitted from the `messages` keys.

  If a candidate queryset is returned with an alias defect,
  [`_defect_message`][querysets] detects the missing key and raises:
  `"...which this surface declares no wording for. This is a framework defect: a "
  "seal defect code was added without an arm at this site."`

  The docstring of [`_validate_post_orderset_result`][querysets] specifically claims that this map
  is an exhaustive dispatch so any unhandled code self-names as a framework defect. Here, `"alias"`
  is a valid canonical defect that was omitted from the dictionary.

- **Required correction:**
  Include `"alias"` in the `messages` dictionary in
  [`_validate_post_orderset_result`][querysets], providing actionable wording consistent with
  `_visibility_result_error`.

---

### P2-2: Evaluation policy asymmetry between `get_queryset` and `OrderSet.apply_*`

- **Affected symbols:**
  - [`django_strawberry_framework/utils/querysets.py::_LIST_ARGUMENT_VISIBILITY_POLICY`][querysets]
  - [`django_strawberry_framework/utils/querysets.py::_ORDERSET_RESULT_POLICY`][querysets]
  - [`django_strawberry_framework/utils/querysets.py::_visibility_result_error`][querysets]

- **Mechanism:**
  [`_ORDERSET_RESULT_POLICY`][querysets] is defined as:
  ```python
  _ORDERSET_RESULT_POLICY = _SealPolicy(reject_combined=True, require_unevaluated=True)
  ```
  In contrast, [`_LIST_ARGUMENT_VISIBILITY_POLICY`][querysets] is defined as:
  ```python
  _LIST_ARGUMENT_VISIBILITY_POLICY = _SealPolicy(reject_combined=True)
  ```
  `require_unevaluated` remains `False` (default) for list argument visibility.

  If a consumer's `get_queryset` hook evaluates the queryset (e.g. calling `list(queryset)` or
  iterating it):
  1. [`_seal_or_defect`][querysets] does not reject the evaluated queryset because
     `policy.require_unevaluated` is `False`.
  2. [`_seal_or_defect`][querysets] constructs a new `models.QuerySet` using `rebuilt_query` and
     omits `_result_cache`.
  3. The cached evaluation is silently discarded, forcing a duplicate SQL evaluation downstream.

  Moreover, [`_visibility_result_error`][querysets] explicitly implements an `"evaluated"` error
  arm:
  ```python
  "evaluated": (
      f"{name}.get_queryset returned an evaluated queryset ({detail}); "
      f"the visibility contract composes further filters and ordering onto an "
      f"unevaluated lazy query. Return an unevaluated QuerySet."
  )
  ```
  Because [`_LIST_ARGUMENT_VISIBILITY_POLICY`][querysets] leaves `require_unevaluated=False`, this
  error arm is dead code on the list argument path.

- **Required correction:**
  Set `require_unevaluated=True` on [`_LIST_ARGUMENT_VISIBILITY_POLICY`][querysets] so that
  evaluating a queryset inside `get_queryset` fails loudly with the designated configuration error,
  mirroring [`_ORDERSET_RESULT_POLICY`][querysets]. Add a test verifying this rejection.

---

### P2-3: Normalization purity check is skipped when `offset` is absent or zero

- **Affected symbols:**
  - [`django_strawberry_framework/list_field.py::_order_normalization_scope`][list-field]
  - [`django_strawberry_framework/orders/sets.py::OrderSet._input_has_active_terms`][orders-sets]

- **Mechanism:**
  [`_order_normalization_scope`][list-field] opens the task-local capture ledger only when:
  ```python
  if (
      args_record.order_by_supplied
      and orderset_class is not None
      and args_record.offset is not None
      and args_record.offset > 0
  ):
      from .orders.sets import capture_applied_order_normalization
      return capture_applied_order_normalization()
  ```
  When a query supplies `orderBy: [...]` with `limit: 10` and no `offset` (or `offset: 0`):
  1. No capture ledger is opened.
  2. [`_check_nonzero_offset_guard`][list-field] returns immediately:
     ```python
     if args_record.offset is None or args_record.offset <= 0:
         return
     ```
  3. Consequently, [`OrderSet._input_has_active_terms`][orders-sets] is never invoked.

  Because [`_input_has_active_terms`][orders-sets] is the only caller that asserts
  `_normalize_input` purity (`applied_data == data_check`), an impure or non-deterministic
  `_normalize_input` override will execute completely undetected as long as the client does not
  supply a positive offset. The purity contract of `OrderSet` is therefore coupled to client query
  parameters rather than being an invariant of ordering execution.

- **Required correction:**
  Clarify this coupling in [spec-050][spec-050] as an intentional performance optimization, or
  ensure that normalization purity is verified whenever `orderBy` is supplied regardless of
  `offset`.

---

### P3-1: Internal contradiction in `build-050-list_field_arguments-0_0_15.md` regarding floor scope

- **Affected symbols:**
  - [`docs/builder/DONE/build-050-list_field_arguments-0_0_15.md`][build-050]

- **Mechanism:**
  In `build-050-list_field_arguments-0_0_15.md`, line 120 records:
  `| floor | focused scope, Python 3.10.19 / Django 5.2.16 / strawberry 0.316.0 | 463 passed |`
  Lines 122–126 explain:
  "The floor run is the focused scope for the seam this round touched... rather than the
  thirteen-path scope recorded below... tests/test_resource_policy.py, tests/test_list_field.py,
  examples/fakeshop/test_query/test_list_field_api.py,
  examples/fakeshop/test_query/test_list_field_async_api.py."

  However, lines 135–152 under `### Floor-verification scope` state:
  "the scope is this plan's to declare, and it is the set of modules whose seams this card actually
  moved... A floor run that narrows this set is not this card's floor verification."

  These two passages contradict each other: the text simultaneously asserts that narrowing the
  declared 17-path scope invalidates floor verification, while reporting a narrowed 4-path scope as
  its sole passing floor gate.

- **Required correction:**
  Harmonize the build record prose. State whether the 17-path floor scope was executed and passed,
  or explicitly update the build record's definition of the valid floor verification scope.

---

### P3-2: Synchronous wrapper returns an unawaited coroutine for `AsyncIterable`

- **Affected symbols:**
  - [`django_strawberry_framework/list_field.py::DjangoListField::_wrap`][list-field]

- **Mechanism:**
  In [`DjangoListField::_wrap`][list-field], when `user_resolver` is synchronous
  (`is_async_callable(user_resolver)` is `False`), the wrapper is defined as a synchronous function
  `def _wrap(...)`.

  When `user_resolver` returns an async-only iterable (e.g. an async generator) and the query is
  executed asynchronously (`in_async_context()` is `True`):
  ```python
  source = user_resolver(root, info)
  if is_async_only_iterable(source):
      reject_async_iterable_in_sync_context(source, flavor_noun="DjangoListField")
      return _resolve_async_iterable(source, info, args_record)
  ```
  `reject_async_iterable_in_sync_context` only raises when `not in_async_context()`. Under async
  execution, it passes through.
  `_wrap` then calls `return _resolve_async_iterable(source, info, args_record)`.
  Because `_resolve_async_iterable` is an `async def` function, calling it without `await` from
  inside a synchronous `def _wrap` returns an unawaited coroutine object.

  While GraphQL-core's async executor checks `inspect.isawaitable(result)` and awaits it, returning
  a naked coroutine from a synchronous resolver function violates Python type signatures and causes
  unawaited coroutine warnings if `field.base_resolver` is called directly in Python.

- **Required correction:**
  Document that `_wrap` deliberately relies on GraphQL-core's async field executor to await
  awaitables returned from synchronous wrappers, or ensure synchronous field wrappers cleanly
  reject async iterables unless declared with an async resolver.

## Test and documentation gaps

1. **Missing test for raw SQL random ordering:**
   Neither [`test_list_field_api.py`][live-sync] nor [`test_list_field_async_api.py`][live-async]
   exercises `extra(order_by=["RAND()"])` or `extra(order_by=["RANDOM()"])`. The existing suite
   only tests `extra(order_by=["?"])`.
2. **Missing test for evaluated querysets in `get_queryset`:**
   No live or unit test verifies whether an evaluated queryset returned by `get_queryset` is
   rejected when list arguments are present.
3. **Missing test for `OrderSet.apply_*` returning a divergent alias:**
   No test covers an `OrderSet.apply_sync` override returning a queryset routed to an unexpected
   database alias, leaving the missing `"alias"` arm in `_validate_post_orderset_result` unprobed.
4. **Direct invocation test for `field.base_resolver`:**
   No unit test validates direct calling of `field.base_resolver` with an async generator under
   async execution.

## AGENTS.md and GOAL.md assessment

| Rule | Verdict | Evidence |
| --- | --- | --- |
| DRF first, Strawberry second; consumer configuration through `Meta` | Pass | `orderBy` derives from `Meta.orderset_class`; `DjangoListField` uses clean parameterization. |
| Root-cause repair, never a test-only workaround | Pass | Previous policy budget and async cleanup fixes addressed root causes. |
| Live-first for query-reachable behavior | Pass | Shipped fields and holder schemas are tested over HTTP in `test_query/`. |
| Test placement follows ownership | Pass | Private mechanics are in `tests/`; live GraphQL execution is in `examples/fakeshop/test_query/`. |
| Fakeshop seed discipline | Pass | Live tests use `services.seed_data(N)` or `create_users(N)`. |
| Coverage remains package-only at `fail_under=100` | Pass | Gate standards are preserved in pyproject configuration. |
| No pytest unless explicitly requested | Pass | Pytest was not run during this review pass. |
| Run formatting and lint after edits | Pass | All tools format cleanly. |
| Preserve concurrent work | Pass | Concurrent working tree changes in `tests/` were left unmutated. |
| Standing-doc source references use symbol paths | Pass | Reference links use symbol paths and canonical group headers. |

## Required correction order and acceptance gate

1. **Fix `_is_random_order_term`:** Extend the random term classifier to inspect string terms for
   raw SQL random functions (`RAND()`, `RANDOM()`, `NEWID()`), closing the offset guard bypass.
2. **Add `"alias"` to `_validate_post_orderset_result`:** Ensure all nine canonical defect codes
   have explicit message arms.
3. **Harmonize evaluation policy:** Set `require_unevaluated=True` on
   `_LIST_ARGUMENT_VISIBILITY_POLICY` so evaluated querysets in `get_queryset` fail closed.
4. **Reconcile build record floor scope:** Update
   `docs/builder/DONE/build-050-list_field_arguments-0_0_15.md` to eliminate the contradiction
   between the recorded floor run and the floor scope definition.
5. **Add regression tests:** Add live test rows for raw SQL random ordering rejection and
   evaluated `get_queryset` rejection.
6. **Execute final gate:** Once fixes land, run `ruff format`, `ruff check`,
   `scripts/check_trailing_commas.py`, `scripts/check_citations.py`, and the full test suites.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[goal]: ../GOAL.md
[start]: ../START.md

<!-- docs/ -->
[glossary]: GLOSSARY.md
[spec-050]: spec-050-list_field_arguments-0_0_15.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[build-050]: builder/DONE/build-050-list_field_arguments-0_0_15.md

<!-- django_strawberry_framework/ -->
[list-field]: ../django_strawberry_framework/list_field.py
[orders-sets]: ../django_strawberry_framework/orders/sets.py
[querysets]: ../django_strawberry_framework/utils/querysets.py
[resource-policy]: ../django_strawberry_framework/resource_policy.py

<!-- tests/ -->

<!-- examples/ -->
[live-async]: ../examples/fakeshop/test_query/test_list_field_async_api.py
[live-readme]: ../examples/fakeshop/test_query/README.md
[live-sync]: ../examples/fakeshop/test_query/test_list_field_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
