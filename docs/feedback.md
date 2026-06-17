# Review - Alpha split against GOAL.md and upstream parity

Reviewer pass: 2026-06-17. Scope: cross-check the newly split Alpha cards
`036` through `044` against `GOAL.md`, then verify the claimed parity surfaces in:

- `~/projects/strawberry-django-main/strawberry_django`
- `~/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django`

Follow-up correction: after the maintainer note, this pass re-read the full
`docs/spec-036-mutations-0_0_11.md` document from title through link
definitions. Revision 2 of that spec already folds in the main mutation-contract
corrections; the open items below are stale docs/card references or one
non-normative test-plan phrase that should be brought back into sync with the
spec.

No tests run; this is a planning and source-audit pass.

## Verdict

The `0.0.11` -> `0.0.14` split is correct and should stay in Alpha.

`GOAL.md` success criterion 6 explicitly requires declarative mutations from
auto-generated inputs, `ModelForm`, and `ModelSerializer`, with one shared
`errors: list[FieldError]` envelope plus `Upload` for file/image fields. That
maps cleanly to:

- `0.0.11`: `036` core `DjangoMutation` + `037` upload/file/image mapping.
- `0.0.12`: `038` form/model-form mutations.
- `0.0.13`: `039` DRF serializer mutations + `040` auth mutations.
- `0.0.14`: `041` router + `042` debug-toolbar middleware + `043` test client + `044` response debug extension.

The split also respects the `GOAL.md` non-goals: borrow upstream behavior, but
do not become a decorator-first framework, a Graphene runtime, or a thin wrapper
around `strawberry-graphql-django`.

## GOAL.md cross-reference

- `GOAL.md` north star is "DRF-shaped, class Meta-driven" integration. That
  supports keeping `DjangoMutation`, form mutation, and serializer mutation on
  this package's `class Meta` surface rather than copying
  `strawberry_django`'s decorator/field-verb API.
- `GOAL.md` success criterion 6 is the strongest reason not to leave forms,
  serializers, uploads, or the shared error envelope as vague follow-ups. They
  are first-class parity requirements.
- `GOAL.md` success criterion 7 and the target Fakeshop example justify the
  migration-support cards: serializer mutations for DRF users, auth mutations
  exercised by the example users, file/image upload mutations, and test/migration
  helpers for consumers moving from either upstream.
- The Beta Layer-3 items (`FieldSet`, `AggregateSet`, `search_fields`) still
  belong after the Alpha parity line. The split does not change the `0.1.0`
  alpha -> beta meaning; it only makes the remaining Alpha patches reviewable.

## Upstream verification

Confirmed in `strawberry_django`:

- `strawberry_django/mutations/mutations.py` exposes `create`, `update`,
  `delete`, `input_mutation`, and related field-verb helpers.
- `strawberry_django/mutations/fields.py::DjangoMutationBase` and the
  `DjangoCreateMutation` / `DjangoUpdateMutation` / `DjangoDeleteMutation`
  classes own the generated mutation field machinery.
- `strawberry_django/mutations/resolvers.py` owns sync/async write behavior,
  relation input parsing, `full_clean()` handling, and save/delete paths.
- `strawberry_django/fields/types.py::DjangoFileType`,
  `strawberry_django/fields/types.py::DjangoImageType`, and
  `strawberry_django/fields/types.py #"files.FileField: Upload"` verify the
  upload/file/image card.
- `strawberry_django/auth/mutations.py::resolve_login`,
  `strawberry_django/auth/mutations.py::resolve_logout`,
  `strawberry_django/auth/mutations.py::DjangoRegisterMutation`, and
  `strawberry_django/auth/queries.py::current_user` verify the auth card.
- `strawberry_django/routers.py::AuthGraphQLProtocolTypeRouter` verifies the
  Channels router migration-aid card.
- `strawberry_django/middlewares/debug_toolbar.py::DebugToolbarMiddleware`
  verifies the debug-toolbar middleware card.
- `strawberry_django/test/client.py::TestClient` and
  `strawberry_django/test/client.py::AsyncTestClient` verify the test-client
  card, including multipart upload support.

Confirmed in `graphene_django`:

- `graphene_django/forms/mutation.py::DjangoFormMutation` and
  `graphene_django/forms/mutation.py::DjangoModelFormMutation` verify the form
  mutation card.
- `graphene_django/forms/mutation.py::fields_for_form` and
  `graphene_django/forms/converter.py::convert_form_field` verify the form-field
  conversion surface.
- `graphene_django/rest_framework/mutation.py::SerializerMutation`,
  `graphene_django/rest_framework/mutation.py::fields_for_serializer`, and
  `graphene_django/rest_framework/serializer_converter.py::convert_serializer_field`
  verify the serializer mutation card.
- `graphene_django/types.py::ErrorType` is the shape to mirror for the shared
  `FieldError` envelope: a field name plus a list of message strings.
- `graphene_django/utils/testing.py::graphql_query`,
  `graphene_django/utils/testing.py::GraphQLTestMixin`,
  `graphene_django/utils/testing.py::GraphQLTestCase`, and
  `graphene_django/settings.py #"TESTING_ENDPOINT"` verify the test-client and
  endpoint-setting claims.
- `graphene_django/debug/middleware.py::DjangoDebugMiddleware`,
  `graphene_django/debug/middleware.py::DjangoDebugContext`,
  `graphene_django/debug/types.py::DjangoDebug`, and
  `graphene_django/debug/sql/tracking.py::wrap_cursor` verify the in-response
  debug card.

## Open corrections after full spec re-read

1. `KANBAN.md` card `036` still has stale error-envelope references.

   The card body says the envelope is reused by `031 / 032 / 033`, which are the
   shipped Relay cards, not mutation flavors. The corrected wording should name
   downstream flavor cards: `038` form mutations, `039` serializer mutations,
   and `040` auth mutations. `037` upload should remain a sibling `0.0.11` card,
   not an error-envelope reuser.

2. `KANBAN.md` card `036` repeats `039` and links the envelope note to `037`.

   The repeated text says "reused unchanged by `039`, `038`, and `039`" and one
   related link points at upload card `037`. Correct to `038`, `039`, and `040`
   if the card is listing all downstream envelope consumers.

3. `KANBAN.md` cards `038`, `039`, and `040` mention "028's mutation infra".

   `028` is the ordering subsystem. These notes should point to `036`'s mutation
   foundation.

4. `KANBAN.md` card `054` still says `TODO-ALPHA-035` owns the mutation base.

   The card reference already points to `TODO-ALPHA-036-0.0.11`, but the prose
   says `TODO-ALPHA-035` in the foundation seam, files likely touched, dependency
   text, and card-reference body. Update the prose to `TODO-ALPHA-036`.

5. `KANBAN.md` has an incidental stale cascade-permissions reference.

   The aggregate/card text says `apply_cascade_permissions`
   composes with `TODO-ALPHA-033-0.0.10`. The shipped permissions card is
   `DONE-034-0.0.10`; update that reference in the kanban DB.

6. `README.md` still compresses DRF serializer mutations into `0.0.11`.

   The "Coming from DRF + django-filter?" paragraph says mutations are on the
   `0.0.11` roadmap "including a DRF-serializer flavor via
   `Meta.serializer_class`." With the split, it should say the `DjangoMutation`
   foundation is `0.0.11` and the DRF serializer flavor is `0.0.13`.
   `docs/README.md` already reflects the split correctly.

7. `docs/GLOSSARY.md` still describes `Input` as "every field required".

   `docs/spec-036-mutations-0_0_11.md::Decision 6` now correctly says create
   inputs require only fields with no usable Django `default`, `blank`, or
   `null`. Update the glossary entry for "Input type generation" so it does not
   resurrect the rejected blanket-required contract.

8. `docs/spec-036-mutations-0_0_11.md` has one stale test-plan phrase.

   The `test_inputs.py` bullet still says "`Input` all-required /
   `PartialInput` all-optional shapes." Correct it to "required/optional shape
   by Django default/blank/null rules; `PartialInput` all-optional." The
   normative Decision 6 and Definition of Done already carry the stronger
   default/blank/null contract.

9. `docs/GLOSSARY.md` `GraphQLTestCase` under-attributes the parity surface.

   It currently says it mirrors `strawberry-django`'s test client. The
   `GraphQLTestCase` name and mixin-first shape are from
   `graphene_django/utils/testing.py`; the Strawberry side supplies
   `TestClient` / `AsyncTestClient`. The glossary should name both.

## No correction needed

- The `0.0.11` -> `0.0.14` split itself is validated by `GOAL.md` and by the
  upstream package layout.
- Keeping the router symbol name distinct (`DjangoGraphQLProtocolRouter` instead
  of `AuthGraphQLProtocolTypeRouter`) is aligned with the `GOAL.md` non-goal of
  not being a thin wrapper around `strawberry-graphql-django`.
- The response-debug card is correctly graphene-only parity. `strawberry_django`
  has the debug-toolbar middleware, but no equivalent in-response
  `DjangoDebug` object.
