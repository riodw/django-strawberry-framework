# Review — spec-038 form mutations vs. `test_query/README.md` live-coverage rule

Scope: do the spec-038 form-mutation changes honor the coverage discipline that
`examples/fakeshop/test_query/README.md` mandates — *"Any coverage line in
`django_strawberry_framework/` that can be earned by a real-world GraphQL query
against the fakeshop schema MUST be earned here. … only fall back to [in-process /
package tests] when the code path is genuinely unreachable from a live `/graphql/`
request. Mock only when the real path is impossible (mock behaviour, not the
class)."*

I read the live suite (`examples/fakeshop/test_query/test_products_api.py`), the
package suite (`tests/forms/test_resolvers.py`, `tests/mutations/test_resolvers.py`),
the example forms/schema (`apps/products/forms.py`, `apps/products/schema.py`), and
checked which fakeshop primaries are Relay- vs non-Relay-shaped.

## Verdict

**Substantially compliant on the mainline; three runtime branches are earned in the
wrong place.** The form-mutation *pipeline* is genuinely earned live — 15 live
`/graphql/` tests cover create / partial-update / file upload / construction-hook /
plain-form / auth-deny / visibility-scoped-not-found / hidden-relation. The
genuinely-unreachable paths are correctly held in package/in-process tests, and the
one place mocking is used mocks *behaviour*, per the README. But three runtime
branches that **are** reachable against the fakeshop schema are earned only in
`tests/forms/` — those are README violations in the letter ("first place to add a
test … only fall back when genuinely unreachable").

## Compliant (credit)

- **Real HTTP stack.** Every live form test posts to `/graphql/` via
  `django.test.Client` through `_post_graphql`, under the autouse
  `_reload_project_schema_for_acceptance_tests` fixture (registry clear → app-schema
  reload → `config.schema` reload → `config.urls` reload + URL-cache clear) — exactly
  the pattern the README pins. No schema is hand-built; no `DjangoType`/mutation class
  is mocked.
- **Mainline pipeline earned live.** `test_products_api.py` covers, over real HTTP:
  `createItemViaForm` happy path + `categoryId`-through-the-form reverse map;
  `updateItemViaForm` partial preserve + `unique_together` collision; `clean_<field>`
  field-keyed error; constraint → `"__all__"` sentinel; anonymous + missing-perm deny
  (no write); visibility-scoped hidden-row not-found; hidden-**Relay**-relation field
  error; multipart `Upload` over HTTP; `get_form_kwargs`-injects-`user`; plain-form
  `{ ok errors }` success + validation-failure.
- **Sanctioned mocking only.** The save-time `IntegrityError` cases
  (`tests/forms/test_resolvers.py::test_modelform_save_integrity_error_maps_to_envelope`,
  `::test_plain_form_perform_mutate_integrity_error_maps_to_envelope`) use
  `mock.patch.object(..., side_effect=IntegrityError(...))` / a `raise` in a
  `perform_mutate` override — they mock the *behaviour* (a post-validation DB race),
  not the class, which is precisely the README's allowance for an otherwise-impossible
  real path.

## Findings — live-reachable branches earned only in package tests

### [High] Raw-pk relation visibility is package-only, but fakeshop has non-Relay primaries to host it live

`forms/resolvers.py::_visible_related_object` (the `registry.get(...)` non-Relay
branch), the raw-pk arm of `forms/resolvers.py::_decode_form_relation_single` /
`::_decode_form_relation_multi`, and the model-path twin
`mutations/resolvers.py::_raw_pk_relation_error` are the spec's headline security fix
(visibility on the raw-pk branch). They are earned **only** in package tests
(`tests/forms/test_resolvers.py::test_relation_visibility_raw_pk_single_hidden_rejected`
/ `_multi`, `tests/mutations/test_resolvers.py::test_create_raw_pk_*`).

This is **not** genuinely unreachable: fakeshop already exposes many non-Relay-Node
primaries (`apps/glossary/schema.py`, `apps/kanban/schema.py`,
`apps/library/schema.py::ShelfType` / `BranchType` / `PatronType`,
`apps/scalars/schema.py`). The only reason the live suite can't reach this branch is
that the products form mutations relate through `category` (the **Relay**
`CategoryType`, → `categoryId` GlobalID). A form mutation whose `ModelChoiceField`
targets a model with a registered non-Relay primary would generate a raw-pk input and
exercise the branch over real HTTP.

- **Fix:** add a fakeshop `ModelForm` (or model mutation) whose relation targets a
  non-Relay primary, plus a live test that hides the target via `get_queryset` and
  asserts the field-keyed error — single and multi. The package tests then become
  redundant belt-and-suspenders rather than the sole earner.

### [Medium] `to_field_name` relation conversion is package-only and unreachable from the current schema

`forms/resolvers.py::_to_form_key_value` (the `to_field_name`-set branch,
`obj.serializable_value(...)`) and its per-element use in multi reconstruction are
covered only by `tests/forms/test_resolvers.py::test_to_field_name_relation_validates_by_target_field`
(+ the partial-update `to_field_name` test). No fakeshop form sets `to_field_name`
anywhere (confirmed: zero `to_field_name` / `to_field=` occurrences under
`examples/fakeshop/`), so the branch is not earnable against the current schema even
though it is a runtime path a live query would hit.

- **Fix:** give one fakeshop form a `ModelChoiceField(..., to_field_name="slug")`
  (or a `ForeignKey(to_field=...)`-backed field) and add a live test that submits the
  id and asserts the row is resolved by the target field — single and multi.

### [Low] Plain-form deny-by-default (`DenyAll`) deny path is package-only

The model-less `DjangoFormMutation` deny-by-default posture
(`forms/sets.py` unset `permission_classes` → `mutations/permissions.py::DenyAll`,
and the `False`-returning arm of `DjangoFormMutation.check_permission`) is earned only
in `tests/forms/test_resolvers.py::test_plain_form_unset_permission_classes_denies_by_default`
/ `::test_plain_form_write_auth_denial_names_mutation_class`. The live `SubmitContact`
declares an explicit `AllowAny`, so its `check_permission` only ever returns `True`
live — the deny arm and the `DenyAll` default never run over HTTP.

- **Fix:** register a second plain `DjangoFormMutation` in fakeshop with no
  `Meta.permission_classes` (or a denying class) and assert the top-level denial
  live. Low priority — it's a small branch — but it is live-reachable, so per the
  README it belongs in `test_query/` first.

## Correctly NOT in `test_query/` (genuinely unreachable — not findings)

- **Async pipeline.** `forms/resolvers.py::resolve_form_async` + the
  `sync_to_async(thread_sensitive=True)` wrapper + the async-`get_queryset`
  `SyncMisuseError` guard. The README's live surface is the sync `django.test.Client`;
  there is no async/ASGI live surface in `test_query/` (no `async def test_`, no
  `AsyncClient`), so the async path is genuinely unreachable from this directory and
  correctly earned in package tests. (If an ASGI live surface is ever added, the async
  happy path should migrate here.)
- **Class-creation `ConfigurationError` guards.** The create-required-narrowing guard,
  `fields`/`exclude` fail-loud, unknown-`Meta`-key, empty-effective-set, `ModelForm`-
  on-plain-base reject, `operation`-on-plain-base reject, converter unknown-field
  raise. These fire at schema-build / class-creation time, not from a runtime query, so
  they are unreachable via `/graphql/` and correctly live in `tests/forms/test_sets.py`
  / `test_converter.py`.
- **Save-time `IntegrityError`.** A post-validation DB race cannot be triggered
  deterministically over HTTP; the behaviour-mock package tests are the README's
  sanctioned fallback.

## Method / caveats

- Confirmed the live suite uses the reload fixture + real `Client` and mocks nothing
  by class; confirmed fakeshop exposes non-Relay primaries (so Finding [High] is
  reachable) and zero `to_field_name` forms (so Finding [Medium] is currently
  unreachable-by-omission).
- Did **not** run `pytest` or per-test coverage (per `AGENTS.md`); the
  earned-only-in-package claims are reasoned from the fakeshop schema's relation
  shapes (Relay `category` only) and the existence of dedicated package tests for the
  raw-pk / `to_field_name` / deny-default branches. A per-test coverage diff would
  confirm them precisely.
- No code or tests changed.
