# Bug hunt: 0.0.15 (2), master list

Status: in-progress
Scope: every finding of the 0.0.15 hunt held in the t3 worktree
(`~/.t3/worktrees/django-strawberry-framework/t3code-1cc21548`, branch `t3code/1cc21548`, never
merged), plus every defect or lead found while migrating those findings to main.
Method, per finding: verify at main HEAD under AGENTS.md rule 35 (contract row, feasible project
shape, wire or configuration input); fix the root cause on main; an independent agent verifies;
land; purge every trace of the finding from t3 (backup first); next.

## Where we are

| Bucket | Done | Open |
|---|---|---|
| t3 defects (sections 1, 2) | 10 | 4 |
| t3 robustness, lint and stale-test rows (section 3) | 0 | 40 rows + 1 blocked naming decision |
| t3 hunt items never finished (section 4) | n/a | 2 |
| Found along the way (sections 5, 6) | 10 fixed, 5 closed as not a defect | 15 |

The t3 hunt itself is not closed: Deep dive 3 is blocked and the final test gate never ran.

## 1. t3 defects, done

| # | Finding (t3 item) | Outcome on main | Commits | t3 purged |
|---|---|---|---|---|
| 1 | Multi-column `ForeignObject` link columns (join_taxonomy) | Fixed: one link-column reader; forward `ForeignObject` exposed, left out of mutation inputs | `fe6a6df0`, `337b3317` | yes |
| 2 | Negative offset cursor (`connection.py`) | Fixed: one offset-cursor decoder; the real defect was a page-cap bypass t3 never saw | `a57bd826` | yes |
| 3 | M2M composite-index advisory (`optimizer/nested_planner.py`) | Fixed: the advisory resolves the window's own partition column | `269b80c0` | yes |
| 4 | Overlap-head lookup binding (`filters/sets.py`, B21 + 5d) | Fixed: form keys decided once; owner-bound flat `RelatedFilter` children run in their filter set | `754ed263`, `9f7ea5dd` | yes |
| 5 | Serializer list element nullability + blank choice (`rest_framework/serializer_converter.py`, D1, D2) | Fixed: list element follows the child's `allow_null`; choice enums carry `BLANK`; D3-D6 judged robustness | `a5dc6ea3` | yes |
| 6 | `reject_combined` on list-relation children (`utils/querysets.py`) | Superseded: main serves a combined hook queryset as its primary-key set | `5c5e32c5` | yes |
| 7 | Directive and default-value charging (`extensions/resource_policy.py`) | Already on main before this effort | not traced | no (record cleanup owed) |
| 8 | Fragment-spread charging (`extensions/resource_policy.py`, stale re-pass) | Already on main before this effort | not traced | no (record cleanup owed) |
| 9 | Cursor presence by `bool()` (`utils/connections.py`) | Already on main before this effort | not traced | no (record cleanup owed) |
| 10 | Mutation window transition under interruption (`schema.py`, scenario) | Already on main before this effort | not traced | no (record cleanup owed) |

## 2. t3 defects, open

| # | Finding | State | Next step |
|---|---|---|---|
| 11 | `FieldError.field` keying (t3 "Package integration" item): validator-origin errors (`full_clean`, `form.errors`, the serializer's save-time Django `ValidationError`) key by the Django, form or model-column name, while decode errors and DRF `serializer.errors` key by the GraphQL input name; an FK input `categoryId` comes back as `category`, a `Meta.input_class` rename as the old name | Defect re-confirmed at HEAD on model, ModelForm, plain form (stock kanban `setCardStatus`), register and serializer save-time; design researched, see [Item 11 design](#item-11-design-pending-approval) | Maintainer approves the design points, then implement; t3 holds a 5-file fix to read, not port |
| 12 | Deadline not checked on nested forward-FK / OneToOne / reverse-OneToOne resolvers, sync and async (t3 Deep dive 3, Worker 1-A, Low) | t3 fix exists only as a workspace patch; `types/resolvers.py` has no deadline check at HEAD | Re-verify at HEAD, then root-cause fix |
| 13 | Consumer `Prefetch` hint over a target type that hides rows served hidden rows (t3 Deep dive 3, Worker 1-B, HIGH, sealed) | Probably fixed on main by `5d4cdb3b` (a hinted `Prefetch` is scoped by the target type's `get_queryset`) | Confirm against the sealed t3 evidence, then purge |
| 14 | README empty-list rule over-generalized for integer `in: []` (t3 Deep dive 4 docs lead: t3 executed ALL rows against the sentence's NONE) | Unverified at HEAD (README section "Four empty-value rules") | Probe at HEAD; fix doc or code |

### Item 11 design, pending approval

Probe findings at HEAD:

- The split is two key spaces, not casing: the FK suffix (`category` / `categoryId`) and a
  `Meta.input_class` rename have no casing relation.
- Model and form flavors never produce nested error paths; only the serializer nests, and it
  already re-keys at every depth.
- `__all__` cannot collide with a Django field name.
- Re-keying must apply only at the three validator sites (`_full_clean_or_field_errors`,
  `_form_errors_to_field_errors`, the serializer `except DjangoValidationError` branch). A decode
  error already carries a GraphQL name, and under a swapped rename a blanket re-key would rewrite it
  wrong.
- No first-party client reads `FieldError.field`.
- A trial patch moved every probe row to the GraphQL name. Full suite: 3 failures, all tests that
  pin today's Django-name key:
  - `test_update_item_via_form_explicit_null_category_id_is_the_form_required_error` in
    `examples/fakeshop/test_query/test_products_api.py`
  - `test_get_form_kwargs_queryset_scoping_leaves_the_generated_input_shape_unchanged` in
    `tests/forms/test_resolvers.py`
  - `test_partial_update_validates_scalar_field_named_id_suffix` in
    `tests/mutations/test_resolvers.py`

Proposed design:

- **Shared mapper.** One mapper in `utils/errors.py`, `build_error_key_map(specs, *, key_of=None)`
  plus `rekey_error_segment`, promoted from `rest_framework/resolvers.py` `_build_reverse_map` /
  `_rekey_segment`.
- **Mapper input.** `validation_error_to_field_errors(exc, key_map=None)`; `None` keeps today's
  verbatim keying for the kanban service-error caller.
- **Key per flavor.**
  - model: the model field name of `spec.input_attr`;
  - form: `target_name`;
  - serializer save-time: `source or target_name`.
- **Register** goes through the model tail.
- **Required parameters.** Internal helpers take the mutation class as a required parameter, so a
  forgotten call site fails loudly.
- **Lazy map.** The map is built on the error path only.
- **`path` is unchanged** (split of `field`).

t3's fix finds the same three key functions but builds four separate maps, defaults the map to
`None` at every helper (a forgotten site silently keeps the defect), adds one test and changes no
docs.

Decisions for the maintainer:

1. The rule covers every flavor, not only the serializer. Rewrite:
   - spec-036 Decision 7 and Decision 8 step 4;
   - spec-038 Decision 8 step 4 and its test-plan rows;
   - spec-039 Decision 8;
   - spec-040's `USERNAME_FIELD` row.
2. Wire-value change for model, ModelForm, plain-form and register clients (e.g. `category` becomes
   `categoryId`); whether it goes in the CHANGELOG is the maintainer's call.
3. No `CAMELCASE_ERRORS`-style setting: keys are always the input name, and `__all__` stays as is,
   not graphene's `_All__`.
4. An error on a field the input does not expose keeps its validator-side name (recommended), or
   folds into `__all__`.
5. A rename onto an unexposed field's Django name makes two errors share one key: document it
   (recommended), or refuse it at build.
6. Board card `TODO-ALPHA-051-0.0.15`: "casing" becomes "keying"; add `forms/resolvers.py` and
   `auth/mutations.py` to its likely files.

## 3. t3 robustness, lint and stale-test rows, open

Ledger at t3: 4 defect / 37 robustness / 2 lint / 1 stale-test rows. Robustness rows are mostly
hostile-`__name__` / `__mro__` / `__eq__` / metaclass guards and safe-label swaps; each is expected
to fail rule 35 (no feasible shape under supported public API) and be purged from t3 with nothing
ported, but each still needs that verdict.

| # | Area (t3 files) | Rows |
|---|---|---|
| 15 | `filters/inputs.py` range-shape fail-loud guard | 1 |
| 16 | `forms/inputs.py`, `forms/sets.py` | 2 |
| 17 | `mutations/fields.py`, `mutations/resolvers.py`, `mutations/sets.py`, `auth/mutations.py` | 4 |
| 18 | `optimizer/hints.py`, `optimizer/nested_fetch.py` | 2 |
| 19 | `rest_framework/resolvers.py`, `rest_framework/sets.py` | 2 |
| 20 | `sets_mixins.py` (2 passes), `filters/base.py`, `orders/base.py`, `orders/inputs.py`, `orders/sets.py`, `filters/sets.py` (2 passes) | 8 |
| 21 | `routers.py`, `list_field.py` | 2 |
| 22 | `types/base.py` (3 passes incl. an arm-deletion pass), `types/converters.py`, `types/definition.py`, `types/finalizer.py` (2 passes) | 7 |
| 23 | `utils/directives.py`, `utils/errors.py`, `utils/input_values.py`, `utils/inputs.py`, `utils/policies.py`, `utils/querysets.py`, `utils/strings.py`, `utils/sessions.py`, `utils/write_transaction.py` | 9 |
| 24 | Lint: trailing-comma layout in `tests/rest_framework/test_sets.py`, `tests/types/test_base.py` | 2 |
| 25 | Stale test: collection-time model fixture isolation (`tests/utils/test_querysets.py` proxy-target fixtures) | 1 (check against item 41) |
| 26 | Blocked for the maintainer: a mutation whose `__name__` raises publishes a `<MetaclassName>Payload` type instead of failing (`mutations/fields.py`, `mutations/sets.py`, review 5d); the degraded name can collide with a real type | Decision |
| 27 | Robustness leads the ledger forwarded, never filed: hostile-`__str__` dict key and hostile-`__repr__` `save()` return in `rest_framework/resolvers.py`; non-string hostile annotation key and keyset cursor evil-str in `types/base.py`; N1-N5 adjacent-gate liars; lying non-raising `__mro__`; Node-shaped hostile `__mro__` at relay seams; `resolve_lazy_class` hostile `__module__`; `Meta.fields` raising liar end to end; order-dependent cross-model FilterSet-inheritance silent bind; filters-loud / orders-silent posture divergence (Deep dive 4) | Triage with the rows above |

## 4. t3 hunt items never finished

| # | Item | State |
|---|---|---|
| 28 | Deep dive 3: authorization on the deferred paths | Blocked; its two findings are items 12 and 13 |
| 29 | Final test gate | Pending; never run |

## 5. Found along the way, done

| # | Finding | Commits |
|---|---|---|
| 30 | Flat `RelatedFilter` leaf served hidden rows (flat `shelfHomeBranch` skipped its own queryset) | `90fc7118` (pk-IN attempt `616bb8e1` reverted by `162da650`) |
| 31 | Relations no `RelatedFilter` declares served hidden rows | `37dcbf70`, `eddfeab1`, `c7d0ca02` |
| 32 | Ordering by a related row the target type hides | `70118090` |
| 33 | spec-058 builders and `graph.apply` re-entrancy | `d58420d8`, `adacb26c` |
| 34 | `RelatedFilter` whose target model its relation does not correlate | `9131486f` |
| 35 | Serializer choice field admitting a value its column's read enum cannot represent | `a6ace786` |
| 36 | `MultipleChoiceField` over a single-value choice column | `f218d7ee` |
| 37 | Combined hook queryset refused an `F()` / `OrderBy` ordering with a false message; a foreign-key name ordered wrongly | `22900492` |
| 38 | `Choices.__empty__` published a `_None` member (filter `exact: _None` applied no constraint; writes skipped the null guard) | `3ed5ee48` |
| 39 | Offset page-cap bypass (found inside item 2) | `a57bd826` |
| 40 | Closed as not a defect: async `SynchronousOnlyOperation` (fakeshop sync root resolvers); sliced combinator branch on SQLite (Django's own refusal); INNER JOIN row drop on a dangling `null=False` link (Django `select_related`); `IntegerField(choices, blank=True, null=False)` through a ModelForm raising `ValueError` (Django's ModelForm fails identically); stored non-member choice values written by app code | n/a |

## 6. Found along the way, open

| # | Finding | Class |
|---|---|---|
| 41 | `tests/utils/test_relations.py` reverse-link cases fail standalone: the test imports its link models in the body and the conftest registry restore unregisters them | Test bug; fix running in a separate session |
| 42 | With `auto_camel_case=False`, generated mutation input fields stay camelCase | Defect candidate, unverified |
| 43 | `ListField(child=ChoiceField(...))` publishes `String`, never the enum | Gap |
| 44 | `IntegerField(choices, blank=True, null=False)` through a ModelForm mutation: optional refuse-at-build hardening | Robustness |
| 45 | Postgres only: a plain `ChoiceField` over an `ArrayField` builds, then the save fails | Robustness |
| 46 | Postgres only: `ListField(child=ChoiceField)` over an `ArrayField` refused as unsupported | Robustness |
| 47 | Postgres only: `serializer_choice_field=MultipleChoiceField` on a ModelSerializer over an `ArrayField` is unusable | Robustness |
| 48 | `BLANK_CHOICE` marker loses identity through copy or pickle | Robustness |
| 49 | `serializer_field_description` re-raises `KeyboardInterrupt` | Robustness |
| 50 | SKIP hint drops the relation carrier columns from `.only()`, so each row is re-fetched | Defect candidate, unverified |
| 51 | `OrderSet` `"__all__"` leaves out `ForeignObject` fields | Defect candidate, unverified |
| 52 | Connection resolvers' broad `except` sends raw exception text to the client (`connection.py` fallback, window and keyset paths) | Defect candidate, unverified |
| 53 | Docs: README async section should say a hand-written `@strawberry.field` returning a QuerySet completes synchronously (use `DjangoListField(resolver=...)` or an async resolver) | Parked by the maintainer |
| 54 | Docs: glossary should say a sliced combinator branch on SQLite surfaces Django's own `DatabaseError` | Parked by the maintainer |
| 55 | t3 record housekeeping: hunt record counts, `:NNN` citations and DRY prose for items 7-10 and 13 | Owed with each purge |


<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
