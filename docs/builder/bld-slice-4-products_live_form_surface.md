# Build: Slice 4 — the products live form surface

Spec reference: `docs/SPECS/spec-038-form_mutations-0_0_12.md` (Decision 12, lines 1725-1752; Slice 4 checklist lines 444-462; Edge cases lines 1887-1986; Test plan live-tier lines 1993-2016; impl-plan Slice-4 row line 1874)
Status: final-accepted

## Plan (Worker 1)

This is the **live `/graphql/` acceptance surface** for everything Slices 1-3 built.
Slices 1-3 are `final-accepted`; the package is import-ready — `DjangoFormMutation` /
`DjangoModelFormMutation` are exported from the root
(`django_strawberry_framework/__init__.py` lines 18/44/47), the converter + inputs +
bases + resolver pipeline + the generalized `DjangoMutationField` all ship. **Slice 4
is pure example-project consumer wiring + live HTTP tests.** No package source is
touched.

### DB constraint (build-wide flag — designed around)

`examples/fakeshop/db.sqlite3` is git-tracked AND under a concurrent external writer
(maintainer kanban board work) — see the build-038 baseline-dirty list. **This plan
does NOT modify the committed `db.sqlite3`:**

- The live `test_query/` tier and every example test run against **pytest-django's
  ephemeral test database**, built by applying migrations to a `test_`-prefixed DB —
  NOT the committed `db.sqlite3` (`config/settings.py` line 114: `default` →
  `BASE_DIR / "db.sqlite3"`, but pytest-django creates and tears down a separate test
  DB).
- The minimal products `FileField` + its migration ship as a **source-only `.py`
  migration file**. The test DB applies it automatically at test-DB build. **Worker 2
  must NOT run `manage.py migrate` against the committed `db.sqlite3`, and must NOT
  re-seed it.** `makemigrations` (which only writes a migration `.py`, never touches a
  DB) is fine and is how the migration file is authored.
- No `KANBAN.html` / `KANBAN.md` / `db.sqlite3` edit anywhere in this slice.

### File-field model decision: (B) add a minimal `FileField` to a products model + a source-only migration — RECOMMENDED

The form-backed `Upload` test (the P1 file-routing contract — prove `data=`/`files=`
split validates + writes through the **form's** `files=`) needs a model with a file
column that an `ItemModelForm`-style `ModelForm` covers. Two options were weighed:

- **(A) Reuse `apps/scalars/models.py::MediaSpecimen`** (`attachment` FileField +
  `image` ImageField, SQLite-compatible, migration already in place from spec-037 —
  `apps/scalars/migrations/0001_initial.py`). ZERO new migration. **Rejected as the
  primary path** because: (1) it splits the live form surface across `products` +
  `scalars`, contradicting Decision 12's deliberate narrowing of the live tier to
  `test_products_api.py` ("this spec narrows it to the existing `test_products_api.py`
  inside that directory, since products already carries the `Item` constraint and the
  `036` `Mutation` wiring", lines 1737-1740); (2) `MediaSpecimen` already has a
  shipped model-driven `Upload` mutation (`apps/scalars/schema.py::CreateMediaSpecimen`
  + `test_uploads_api.py::test_multipart_create_uploads_real_files_over_http`) — adding
  a *form* mutation there would muddy the spec-037 surface and require a second reload
  fixture in a second file; (3) the spec's prose, edge cases, and the Slice-3
  carry-forward are all products-centric (`ItemModelForm`, `Item.unique_item_per_category`).
- **(B) Add a minimal `FileField` to a small products model + a source-only
  migration.** **CHOSEN.** Decision 12 / Slice-4 checklist explicitly authorizes it:
  *"If `Item` (or a small example model) needs a file column for the multipart test,
  add the minimal `FileField` + migration here"* (lines 451-452), and the impl-plan
  Slice-4 row budgets *"a minimal file column/migration if needed for the multipart
  test"* (line 1874). It keeps the ENTIRE live form surface in `products` /
  `test_products_api.py`, matching the spec's narrowing.

**(B) sub-decision — which products model gets the file column.** A `FileField` is
sufficient (the P1 contract is about routing an `Upload` into `files=`, not about
image dimensions — `ImageField` would pull Pillow + width/height assertions that add
nothing to the routing proof and that `test_uploads_api.py` already covers for the
model-driven path). Add a single nullable `FileField` named `attachment` (with
`upload_to="product_media/"`, `null=True, blank=True` so it stays optional and the
existing `seed_data`/`Item.objects.create` calls are unaffected) to a small products
model. **Recommend a NEW tiny model `ProductDoc` (or `ItemAttachment`)** rather than a
column on `Item`, OR a column on `Item` — **left to Worker 2's discretion** within the
constraint below. Rationale for offering both: a column on `Item` is the most
spec-literal ("`Item` ... needs a file column"), but `Item` is heavily exercised by
`seed_data` and the existing 036 mutation tests, so a separate small model isolates the
file surface and avoids any risk of perturbing the `unique_item_per_category` /
partial-update assertions. **Constraint binding either choice:** the column MUST be
nullable/optional so no existing `Item.objects.create(...)` / `seed_data` call breaks,
and the migration is **source-only**. See `### Implementation discretion items`.

NOTE this as confirming (not contradicting) the spec — the spec leans products-centric
and authorizes the products file column explicitly; (A) reuse-`MediaSpecimen` is the
considered-and-rejected alternative, NOT a spec-reconciliation candidate.

### DRY analysis

- **Existing patterns reused (cite file:line).**
  - **Seeding (AGENTS.md non-negotiable):** every catalog/auth test opens with
    `seed_data(N)` / `create_users(N)` / `seed_cascade_split()` from
    `apps.products.services` (services.py `seed_data` line 147, `create_users` line
    259, `seed_cascade_split` line 423). Never hand-roll `Category`/`Item`/`User`.
  - **The reload fixture + HTTP helpers** in `test_products_api.py`:
    `_reload_products_project_schema` (line 42) + the autouse
    `_reload_project_schema_for_acceptance_tests` (line 73); `_post_graphql` (line 79);
    `_assert_graphql_data` (line 91); `_global_id` (line 108); `_login` (line 1788);
    `_login_with_perm` (line 112); `_staff_client` (line 100). The new form tests reuse
    ALL of these verbatim — the `apps.products.schema` reload already covers the new
    form mutations once they are wired into `products/schema.py::Mutation`, so **no new
    fixture is needed.**
  - **The model-driven mutation tests are the exact assertion-shape templates to
    mirror** for the form flavor (same envelope, same wire contract):
    - relation-visibility (hidden `Category` → `FieldError` on `categoryId`):
      `test_create_item_relation_id_for_hidden_category_is_field_error` (line 694) — the
      P1 invariant template, including the visible-public-category success contrast.
    - `categoryId` wrong-type → field-keyed error:
      `test_create_item_wrong_type_global_id_on_category_id_is_field_error` (line 584).
    - `"__all__"` sentinel on the unique constraint:
      `test_create_item_unique_constraint_envelope_uses_all_sentinel` (line 388).
    - partial-update collision on a one-field change:
      `test_update_item_partial_collision_on_unique_constraint_changing_only_name`
      (line 424) — the right-path partial-update template.
    - write-auth (anonymous denied / missing-perm denied):
      `test_create_item_anonymous_is_denied_top_level_error_no_write` (line 458),
      `test_create_item_missing_model_perm_is_denied_no_write` (line 493).
    - visibility-scoped update not-found:
      `test_visibility_scoped_update_delete_hidden_private_row_is_not_found` (line 528).
  - **The raw multipart-upload transport pattern** is fully demonstrated in
    `examples/fakeshop/test_query/test_uploads_api.py::test_multipart_create_uploads_real_files_over_http`
    (lines 204-261): the GraphQL-multipart `operations` / `map` / numbered-file POST
    via `django.test.Client`, `SimpleUploadedFile`, `override_settings(MEDIA_ROOT=...)`,
    `client.force_login`. **The new products form-backed `Upload` test copies this
    transport shape** (the `{operations, map, "0": SimpleUploadedFile(...)}` POST body),
    pointing `map` at `variables.data.<fileField>`. Cite this file:line as the reused
    pattern.
  - **The `Mutation` wiring + lazy-payload discipline** is shown in
    `apps/products/schema.py` (existing `CreateItem`/`UpdateItem`/... line 232-272 +
    the `@strawberry.type class Mutation` line 256) and `apps/scalars/schema.py`
    (`CreateMediaSpecimen` line 286 + its `Mutation` line 301). The form mutations are
    added the same way: declare the `DjangoModelFormMutation`/`DjangoFormMutation`
    subclass, expose via `DjangoMutationField`, add to the products `Mutation` type.
    `config/schema.py` already composes `Mutation(ProductsMutation, ScalarsMutation)`
    (line 35) and calls `finalize_django_types()` (line 50) — the form bind
    (`bind_form_mutations()`, Slice 2) already runs inside that finalize, so **NO
    `config/schema.py` edit is needed** as long as the form mutations land on the
    existing `apps.products.schema.Mutation` (confirmed below).
  - **The `get_form_kwargs(info, *, data, files, instance=None)` override seam** ships
    on both form bases (`forms/sets.py` `_default_get_form_kwargs` + the `get_form_kwargs`
    class attr at lines 454/701). The P2 `user`-injection form overrides it to add
    `user=<request user>`; the override ALSO waives the create-required guard
    (`_form_kwargs_overridden`, forms/sets.py line 227, consumed at lines 446/695).

- **New helpers justified.** **None in package source.** In `products/forms.py` (new
  example module) the only net-new constructs are the consumer forms themselves
  (`ItemModelForm`, a plain contact/action `Form`, the kwarg-requiring form, and the
  file-form). In `test_products_api.py` the new tests reuse every existing helper; the
  only candidate new local helper is a tiny multipart-POST wrapper, but it is a
  near-copy of `test_uploads_api.py`'s inline body — **do NOT extract a cross-file
  shared helper** (the two files have independent reload fixtures and live in the same
  tier; a shared upload helper would couple `test_products_api.py` to
  `test_uploads_api.py`). Worker 2 may inline the multipart POST in the single products
  upload test, mirroring `test_uploads_api.py`'s inline shape. If Worker 2 finds 2+
  multipart tests land in `test_products_api.py`, a file-LOCAL `_post_multipart(...)`
  helper is justified then (named condition for later extraction).

- **Duplication risk avoided.** The naive risk is **copying `test_uploads_api.py`
  wholesale** (its `_png_bytes`, its read-side SDL introspection tests, its
  `CreateMediaSpecimen` model-driven path). The products upload test needs ONLY the
  multipart-transport skeleton against a **form-backed** mutation — not the read-side or
  the Pillow image machinery. Plan: a `FileField` (not `ImageField`) so no Pillow / no
  `_png_bytes`; a plain text `SimpleUploadedFile`; assert the file landed + `errors ==
  []`, nothing about width/height. Second risk: **re-deriving the wire-contract query
  strings** — instead, define module-level form-mutation query-string constants
  alongside the existing `_CREATE_ITEM` (line 142) etc., named distinctly
  (`_CREATE_ITEM_VIA_FORM`, ...), so the form field-name and `errors { field messages }`
  envelope are spelled once.

### Implementation steps

Line numbers are pin-at-write-time navigational hints; verify against current source
before editing.

1. **`examples/fakeshop/apps/products/forms.py` (NEW).** Add Django forms (no package
   imports beyond `from django import forms`; Meta-classes-everywhere applies to the
   package's consumer surface, but these are plain Django forms, declared the standard
   Django way):
   - `class ItemModelForm(forms.ModelForm)` over `models.Item` with
     `class Meta: model = Item; fields = (...)` covering `name`, `description`,
     `category` (the FK that drives the `categoryId`-through-the-form P1 reverse map),
     and the file field if the file column lands on `Item` (see step 2 / discretion).
     Add a `clean_<field>` method (e.g. `clean_name` rejecting some sentinel value) for
     the field-level `form.errors`-keyed-to-the-field live case. The model's
     `unique_item_per_category` `UniqueConstraint` (models.py line 70) surfaces through
     `ModelForm`'s `_post_clean` → `validate_constraints()` as a `NON_FIELD_ERRORS`
     entry → the `"__all__"` sentinel (no custom `clean()` needed — the constraint
     surfaces automatically; a `clean()` may be added if Worker 2 wants an explicit
     cross-field path, discretion).
   - A **plain `Form`** (e.g. `class ContactForm(forms.Form)`) with a couple of fields
     (a `CharField`, an `EmailField`) and a `clean_<field>` or `clean()` that can fail,
     for the plain-form success/validation-failure `{ok, errors}` shapes. It is
     model-less, so its `DjangoFormMutation` MUST declare an explicit
     `Meta.permission_classes` (edge case lines 1980-1983 — no `DjangoModelPermission`
     default with no model). Use `AllowAny` or an equivalent already-shipped permission
     so the success path is reachable for any caller (confirm an `AllowAny`-style class
     exists in the package permission surface; if only `DjangoModelPermission` ships,
     the plain form needs a trivial allow-all `permission_classes` — Worker 2 discretion
     on which shipped class; if none is allow-all, define a 3-line local
     `class _AllowAny: def has_permission(self, *a, **k): return True` in the example
     `forms.py` or `schema.py`).
   - A **kwarg-requiring form** for the P2 `get_form_kwargs`-injects-`user` case: a form
     whose `__init__(self, *args, user=None, **kwargs)` pops `user` and uses it (e.g. a
     `clean()` that requires `user.is_authenticated`, or stamps the user). Schema-time
     discovery reads `base_fields` (no instantiation), so the required-kwarg `__init__`
     is fine at bind. This may be a `ModelForm` over the products file/`Item` model OR a
     plain `Form` — pick whichever pairs naturally with the construction-hook test
     (discretion); the spec's P2 case (lines 1956-1961) is construction-hook-agnostic.
   - The **file-form** (the form driving the multipart `Upload` test): a `ModelForm`
     over whichever model carries the `FileField` (step 2), with the file column in its
     `Meta.fields`. Its converter maps the `FileField` → `Upload` (Slice 1), and the
     resolver routes it into `files=` (Slice 3). This may BE `ItemModelForm` if the file
     column lands on `Item`, collapsing two forms into one.

2. **The minimal `FileField` + source-only migration (decision B).** Add a nullable
   `FileField` to the chosen products model in
   `examples/fakeshop/apps/products/models.py` (a column on `Item`, OR a new tiny model
   — discretion, see below). The column: `attachment = models.FileField(
   upload_to="product_media/", null=True, blank=True)` (optional so existing
   `seed_data` / `Item.objects.create` calls are unaffected). Then author the migration
   with `uv run python examples/fakeshop/manage.py makemigrations products` — this
   writes a NEW `examples/fakeshop/apps/products/migrations/000N_*.py` file ONLY (the
   current latest is `0001_initial.py`); it does **NOT** touch any DB. **Do NOT run
   `migrate`.** The ephemeral test DB applies the migration automatically.
   - If a NEW model is chosen, also expose its `DjangoType` in
     `products/schema.py` ONLY if a read path is needed (the form mutation's payload
     `result`/`node` slot needs the model's primary `DjangoType` to exist in the
     registry — a `DjangoModelFormMutation` resolves its payload object through the
     primary-type lookup, spec Decision 6). **Critical wiring check:** a
     `DjangoModelFormMutation` over a model with NO registered primary `DjangoType`
     raises the no-registered-primary-type error (Slice 2 `test_sets.py` covers it). So
     the file-form's model MUST have a `DjangoType` registered in `products/schema.py`.
     If the file column lands on `Item`, `ItemType` (line 91) already is the primary —
     zero new type. If a new model, add a minimal `DjangoType` for it (Relay-shaped or
     not; non-Relay gives the payload a `result` slot, Relay gives `node`).

3. **`examples/fakeshop/apps/products/schema.py` (extend).** Add:
   - `class CreateItemViaForm(DjangoModelFormMutation): class Meta: form_class = ItemModelForm; operation = "create"`
   - `class UpdateItemViaForm(DjangoModelFormMutation): class Meta: form_class = ItemModelForm; operation = "update"`
   - the plain-form mutation:
     `class SubmitContact(DjangoFormMutation): class Meta: form_class = ContactForm; permission_classes = (<allow-all>,)`
     (NO `operation` — the plain base rejects any `Meta.operation`, edge case lines
     1962/Decision 10).
   - the `get_form_kwargs`-override mutation (P2): a `DjangoModelFormMutation` /
     `DjangoFormMutation` over the kwarg-requiring form that overrides
     `get_form_kwargs` to inject `user=info.context.request.user`. The override is on the
     MUTATION subclass (it is the `get_form_kwargs` owner), e.g.:
     `def get_form_kwargs(self, info, *, data, files, instance=None): kw = super().get_form_kwargs(info, data=data, files=files, instance=instance); kw["user"] = info.context.request.user; return kw`
   - the file-form mutation if distinct from `CreateItemViaForm` (only if the file
     column is on a separate model).
   - Import the forms: `from . import forms` (or `from .forms import ...`).
   - Add each as an unannotated `DjangoMutationField(...)` field on the EXISTING
     `@strawberry.type class Mutation` (line 256) — e.g. `create_item_via_form =
     DjangoMutationField(CreateItemViaForm)`, etc. Update the `Mutation` docstring to
     mention the form surface. `config/schema.py` needs NO edit (it composes
     `ProductsMutation` already, line 35; the form bind runs inside the existing
     `finalize_django_types()`).
   - Import the bases: add `DjangoFormMutation, DjangoModelFormMutation` to the existing
     `from django_strawberry_framework import (...)` block (line 42).

4. **`examples/fakeshop/test_query/test_products_api.py` (extend).** Add the live matrix
   (see `### Test additions / updates`). Define module-level form-mutation query-string
   constants alongside `_CREATE_ITEM` (line 142). Reuse the existing fixture + helpers.

5. **Ruff after edits** (AGENTS.md): `uv run ruff format .` + `uv run ruff check --fix .`
   (Worker 2's responsibility; recorded here so the plan is complete). Do NOT run
   pytest after edits (AGENTS.md).

### Test additions / updates

All in `examples/fakeshop/test_query/test_products_api.py`, all
`@pytest.mark.django_db(transaction=True)`, all seeded via `seed_data`/`create_users`/
`seed_cascade_split` first line, all using the existing reload fixture + `_post_graphql`
/ `_login_with_perm` / `_global_id` helpers. Each bullet pins the load-bearing assertion
shape. The wire envelope for the `ModelForm` flavor is `{ node|result, errors { field
messages } }`; for the plain form it is `{ ok, errors { field messages } }`.

- **`createItemViaForm` happy path.** A permitted caller (`_login_with_perm(
  "view_item_1", "add_item")`) creates an `Item` through the form. Assert
  `result["errors"] == []`, the object slot (`node`/`result`) carries the created
  `name`, and the row exists in the DB.
- **`updateItemViaForm` happy path / non-colliding partial update.** Mirror
  `test_update_item_non_colliding_partial_update` (line 196). Update one field; assert
  success envelope + the DB row updated.
- **`categoryId` validates + writes through the form's `category` field (P1 reverse
  map).** A `createItemViaForm` with `categoryId: <visible category GlobalID>` succeeds
  and the created `Item.category` is the right `Category`. **Load-bearing:** assert the
  written row's `category_id` equals the submitted category pk AND (right-path) that the
  category was set via the form's `category` field — pin by asserting the success uses
  the `categoryId` input arg name (the generated input field) and the resulting
  `Item.category` matches; the model-driven mirror is at line 584/694. This is NOT a raw
  model setattr — the test query goes through the GraphQL `categoryId` arg only.
- **Partial-update preservation — RIGHT-PATH / LOAD-BEARING.** A `name`-only
  `updateItemViaForm` preserves `category` (FK) and `description` (scalar). **Pin the
  load-bearing property:** after the update, `refresh_from_db()` and assert
  `item.category_id` and `item.description` are UNCHANGED from their seeded values while
  `item.name` IS the new value. Keep the mutation's `data:` to ONLY `{name: ...}` so the
  test can only exercise the reconstruction path (it cannot accidentally pass `category`
  through). Mirror `test_update_item_partial_collision...` (line 424) for the structure.
- **Partial-update one-field collision fires `unique_item_per_category` — RIGHT-PATH /
  LOAD-BEARING.** Two `Item`s `A`/`B` under one category; `updateItemViaForm(A, {name:
  "B"})` returns `node`/`result` null + exactly one `errors` entry keyed `"__all__"`,
  and `A`'s name is unchanged in the DB. Keep `data:` to `{name: "B"}` only so the
  unchanged `category` co-participates via the reconstruction (the right-path proof —
  if reconstruction dropped `category`, the constraint would NOT fire). Direct mirror of
  line 424.
- **`form.errors` envelope — field-level.** A `createItemViaForm` triggering the
  `clean_<field>` error (submit the sentinel value `clean_name` rejects) returns
  `node`/`result` null + one `errors` entry whose `field` is the FORM field name (e.g.
  `name`), `messages` non-empty. No top-level GraphQL error.
- **`form.errors` envelope — `"__all__"` sentinel on create.** A duplicate
  `(category, name)` `createItemViaForm` returns the `"__all__"`-keyed `FieldError`
  (mirror line 388). Pin `errors[0]["field"] == "__all__"`, no second row written.
- **Write authorization (three sub-cases in one or split tests).** (a) anonymous
  `createItemViaForm` → top-level `payload["errors"]` present, `payload["data"] is
  None`, `"Not authorized"` in the message, no write (mirror line 458). (b) a caller
  holding only `view_item` (lacks `add_item`) → same top-level denial, no write (mirror
  line 493). (c) a permitted caller (`add_item`) → success. The `ModelForm` flavor
  inherits `DjangoModelPermission`, so the perm codenames are `add_item`/`change_item`.
- **Visibility-scoped `update` → not-found.** A caller who holds `change_item` but
  cannot SEE a private `Item` (use `seed_cascade_split()`'s `item_under_private`) gets
  `node`/`result` null + `errors` keyed `["id"]`, row unchanged; the same update
  succeeds for `item_under_public`. Mirror line 528.
- **Relation visibility — hidden `Category` GlobalID → field-keyed `FieldError` (P1
  restored invariant) — LOAD-BEARING / RIGHT-PATH.** A permitted writer (`add_item`)
  submitting a HIDDEN `Category` GlobalID as `categoryId` to `createItemViaForm` gets
  the SAME field-keyed `FieldError` on `categoryId` the model-driven mutation returns
  (mirror line 694). **Pin:** `[e["field"] for e in result["errors"]] == ["categoryId"]`,
  `node`/`result` null, no write; and the SAME caller's create against the VISIBLE
  public category SUCCEEDS (the contrast that proves the form's default
  `Category.objects.all()` queryset is NOT the only guard — the decode visibility query
  is). Use `seed_cascade_split()`'s `private_cat` / `public_cat`. This is the headline
  P1 invariant for the slice — mark it right-path: the test query must submit a
  well-formed-but-hidden GlobalID (not a malformed one) so it can only exercise the
  visibility-decode path, not a parse-failure path. (Spec test plan line 2005-2008.)
- **Raw `django.test.Client` multipart upload to a form-backed `Upload` field (P1
  file-routing).** Mirror `test_uploads_api.py::test_multipart_create_uploads_real_files_over_http`
  (lines 204-261): under `override_settings(MEDIA_ROOT=tmp_path)`, a permitted caller
  (force-login; needs the model `add` perm) POSTs `{operations: json, map: json, "0":
  SimpleUploadedFile("doc.txt", b"...", content_type="text/plain")}` to `/graphql/` with
  `map` = `{"0": ["variables.data.attachment"]}` and the mutation's `variables.data` =
  `{..., "attachment": None}`. **Pin the load-bearing property:** assert `errors == []`,
  the row exists with the file attached (`obj.attachment.name` endswith `"doc.txt"`,
  `attachment` readable), proving the resolver split routed the `Upload` into the form's
  `files=` (NOT `data=`) and the form validated + wrote it. Use a `FileField` + a plain
  text `SimpleUploadedFile` (no Pillow / no image-dimension assertions — those belong to
  the already-shipped `test_uploads_api.py`).
- **Write-time `IntegrityError` → `FieldError` envelope (P1).** A valid
  `form.save()` that hits a DB constraint at write returns the null-object +
  `FieldError` envelope via `_save_or_field_errors`, NEVER a top-level `GraphQLError` /
  500. The reliable way to provoke this live: a create whose form-level validation
  cannot catch a residual constraint — e.g. construct two requests racing the unique
  constraint, OR (simpler, deterministic) a path where `full_clean`/`is_valid` passes
  but `save()` raises. **Worker 2 discretion on the provocation mechanism;** the
  load-bearing assertion is fixed: `response.status_code == 200`, `"errors" not in
  payload` (no top-level), `result["node"/"result"] is None`, `len(result["errors"]) ==
  1`. If a deterministic live `IntegrityError` proves hard to provoke through the form
  (form validation tends to pre-empt the constraint), this single sub-check MAY be
  deferred to the package-internal `tests/forms/test_resolvers.py` tier (which Slice 3
  already plans for `_save_or_field_errors` via a `form.save()` raising `IntegrityError`,
  spec test-plan line 2060-2062) — record the deferral reason and cite that the unit
  tier owns the mapper proof. Live preference per AGENTS.md is to earn it here if a
  realistic request reaches it.
- **`get_form_kwargs` override injecting `user` (P2).** A mutation over the
  kwarg-requiring form whose `get_form_kwargs` override adds `user=info.context.request.
  user` succeeds for a logged-in caller. **Pin:** the form receives the user (assert the
  user-stamped side effect, e.g. the created row's owner/stamp, OR that a form requiring
  `user.is_authenticated` validates only because the user was injected). Drives the form
  whose `__init__` requires `user` — proving schema-time `base_fields` discovery did NOT
  instantiate the form (the bind succeeded) and the runtime construction hook supplied
  the kwarg. (Spec test-plan line 2011-2012.)
- **Plain `Form` mutation — success shape.** `submitContact` with valid data: assert
  `payload["data"]["submitContact"]["ok"] is True` and `errors == []`. (Spec line
  2013-2014.)
- **Plain `Form` mutation — validation-failure shape.** `submitContact` with data
  failing a `clean_<field>`: assert `ok is False` and `errors` carries a field-keyed
  entry (the form field name, `messages` non-empty). No top-level error.

**Temp tests for Worker 3:** the multipart upload test and the `IntegrityError` test are
the two trickiest live shapes; Worker 3 may want a scratch temp test under
`docs/builder/temp-tests/slice-4/` to confirm the multipart `map` wiring and the
`IntegrityError` provocation before accepting. Note for Worker 3: the `FileField`
migration is source-only — verify via `manage.py makemigrations --check --dry-run`
(clean after the migration lands) that model state is migration-consistent, and NEVER
run `migrate` against `db.sqlite3`.

### Implementation discretion items

Items Worker 1 has assessed and decided belong to Worker 2:

- **Where the file column lands:** a nullable `FileField` on `Item` (most spec-literal)
  vs a new tiny products model (isolates the file surface from the heavily-exercised
  `Item`). Either is correct; the binding constraints are (1) the column is
  nullable/optional so no existing `seed_data`/`Item.objects.create` breaks, (2) the
  migration is source-only, (3) the file-form's model has a registered primary
  `DjangoType` in `products/schema.py` (free if on `Item`; one minimal type if a new
  model).
- **`FileField` vs `ImageField`:** `FileField` recommended (the routing proof needs no
  image dimensions; `ImageField` pulls Pillow). Worker 2 may use `ImageField` if it
  prefers symmetry with `MediaSpecimen`, but then must add the Pillow `_png_bytes`
  helper — not worth it.
- **The plain form's allow-all permission class:** which shipped permission (if any) is
  allow-all, vs a 3-line local allow-all class in the example. Plain `DjangoFormMutation`
  REQUIRES an explicit `Meta.permission_classes` (no model default), so SOME class must
  be named; the choice of which is Worker 2's.
- **Whether the kwarg-requiring (P2) form is a `ModelForm` or a plain `Form`,** and
  whether it reuses one of the other forms or is its own class.
- **Whether `ItemModelForm` carries a custom `clean()`** in addition to the
  `clean_<field>` (the `unique_item_per_category` `"__all__"` case surfaces from
  `_post_clean` automatically; an explicit `clean()` is optional).
- **The `IntegrityError` provocation mechanism** (and the documented fallback to the
  unit tier if a deterministic live provocation is not feasible).
- **Field naming / query-string constant names** in the test file.
- **Whether the multipart POST is inlined (one upload test) or factored to a
  file-local helper (only if 2+ multipart tests land).**

### Static-helper skip (recorded)

Per BUILD.md "When to run the helper during build", Worker 1 runs the planning helper
only when the plan adds logic to a package `.py` file ≥150 LOC or under `optimizer/` /
`types/`. **Slice 4 adds NO package logic** — every new file is example-project consumer
code (`apps/products/forms.py`, `apps/products/schema.py` edits, `apps/products/models.py`
file-column edit, `test_products_api.py` edits), all outside
`django_strawberry_framework/`. Example-project files trigger only Worker 3's review
helper at ≥50 new lines (BUILD.md line 427). **Helper SKIPPED at planning; reason: no
package source touched.** Worker 3 runs the review helper on `forms.py` / `schema.py` /
`test_products_api.py` per its own ≥50-line trigger.

### Spec slice checklist (verbatim)

The spec's Slice 4 nested sub-bullets from `## Slice checklist` (lines 444-462), copied
verbatim. Every box stays `- [ ]` during planning; Worker 2 ticks each as it lands.

- [x] [`examples/fakeshop/apps/products/forms.py`][products-forms] (new): an
  `ItemModelForm` (`forms.ModelForm` over `Item`, with a `clean_<field>`) and a
  plain `Form` (e.g. a small contact / action form); `products/schema.py` gains a
  `DjangoModelFormMutation` (create + update) and a `DjangoFormMutation`;
  `config/schema.py` already wires `mutation=Mutation` ([`spec-036`][spec-036] Slice 4).
  If `Item` (or a small example model) needs a file column for the multipart test,
  add the minimal `FileField` + migration here.
- [x] [`test_products_api.py`][test-products-api] (seeded via `seed_data` /
  `create_users`): live `/graphql/` create / update through the `ModelForm`
  mutation; `categoryId` validating + writing through the form's `category` field;
  **partial-update preservation** (a `name`-only update preserves `category` /
  `description`, and `unique_item_per_category` fires on a one-field change); the
  `form.errors` envelope (`clean_<field>` keyed to the field; the constraint error
  keyed to `"__all__"`); write authorization; the visibility-scoped `update`; **a
  raw `django.test.Client` multipart upload** to a form-backed `Upload` field
  (the P1 file-routing contract); and the plain `Form` mutation's **success**
  (`ok: true`) **and** validation-failure (`ok: false`, field-keyed `errors`) shapes.

### Notes for Worker 1 (spec reconciliation)

No spec-vs-codebase gaps found. Every symbol the slice needs exists or is a Slice-1-3
deliverable: `DjangoFormMutation` / `DjangoModelFormMutation` exported from root
(`__init__.py` 18/44/47); `get_form_kwargs` override + waiver seam shipped
(`forms/sets.py` 227/454/701); plain-form `{ok, errors}` payload + ModelForm
`{node|result, errors}` payload shipped (`mutations/inputs.py` build_payload_type
object_type=None at 579); `bind_form_mutations()` wired into the existing
`finalize_django_types()` (config/schema.py 50). `Item.unique_item_per_category`
(models.py 70) gives the `"__all__"` live case. `seed_cascade_split` (services.py 423)
gives the hidden private rows for both the relation-visibility and visibility-scoped-update
cases. The multipart transport pattern is proven (`test_uploads_api.py` 204-261).

Two items to note (neither blocks the plan):

1. **File-field model — confirms the spec, not a reconciliation candidate.** Decision 12
   leans products-centric and explicitly authorizes the products file column (lines
   451-452). Decision B (products column + source-only migration) is the spec-faithful
   path; (A) reuse-`MediaSpecimen` was considered and rejected (splits the live surface
   across apps, contradicting the Decision-12 narrowing to `test_products_api.py`). No
   spec edit needed.
2. **DB constraint is build-wide and already documented** in the build plan preamble;
   this plan re-states it (source-only migration, no `migrate`, no `db.sqlite3` edit) so
   Worker 2 cannot miss it.

Spec status line (lines 42-45) re-verified: "Slices 1-2 built and accepted ... Slices
3-5 remain." This is now STALE — Slice 3 is `final-accepted`. **This is a planning pass;
Worker 1 does not edit the spec in a planning pass** (per the dispatch). The status-line
correction (3-5 → 4-5 remain) is recorded here for the final-verification pass to apply
when this slice touches the spec, OR for the next spec-touching slice; flagging it so it
is not lost. (Per worker-1.md "Spec status-line re-verification", stale status lines are
fixed when a pass edits the spec; no spec edit is licensed in this planning pass.)

---

## Build report (Worker 2)

### Files touched

- `examples/fakeshop/apps/products/forms.py` (NEW) — four consumer Django forms:
  `ItemModelForm` (`ModelForm` over `Item`, `Meta.fields = name/description/category`,
  `clean_name` rejecting the `REJECTED_ITEM_NAME` sentinel for the field-level case; the
  `unique_item_per_category` constraint surfaces automatically via `_post_clean`, no
  custom `clean()`); `ContactForm` (plain `forms.Form` with `subject` `CharField` +
  `email` `EmailField` + a `clean_subject`); `StampedItemModelForm` (`ModelForm` over
  `Item` whose `__init__` REQUIRES a `user` kwarg, `clean()` requires
  `user.is_authenticated`, `save()` stamps the row's `description`) for the P2
  `get_form_kwargs` case; `ItemFileModelForm` (`ModelForm` over `Item` carrying the
  nullable `attachment` `FileField`) for the multipart `Upload` test.
- `examples/fakeshop/apps/products/models.py` — added a nullable `attachment =
  models.FileField(upload_to="product_media/", null=True, blank=True)` to `Item`
  (discretion choice: column on `Item`, NOT a new model — `ItemType` is already the
  registered primary `DjangoType`, so zero new type; nullable so `seed_data` /
  `Item.objects.create` are unaffected). `upload_to` mirrors
  `scalars/models.py::MediaSpecimen` (SQLite-compatible TEXT relative-name storage).
- `examples/fakeshop/apps/products/migrations/0002_item_attachment.py` (NEW) — the
  source-only migration generated by `makemigrations products`. The committed
  `db.sqlite3` was NOT touched (verified: `db.sqlite3` / `KANBAN.html` never appear in
  `git status --short`); the ephemeral pytest-django test DB applies it automatically.
- `examples/fakeshop/apps/products/schema.py` — imported `DjangoFormMutation` /
  `DjangoModelFormMutation` + `from . import ... forms ...`; added `CreateItemViaForm` /
  `UpdateItemViaForm` (`DjangoModelFormMutation` over `ItemModelForm`),
  `CreateItemWithFileViaForm` (over `ItemFileModelForm`), `CreateStampedItemViaForm`
  (over `StampedItemModelForm`, with a `get_form_kwargs` override injecting
  `user=info.context.request.user`), `SubmitContact` (`DjangoFormMutation` over
  `ContactForm`, explicit `Meta.permission_classes = (AllowAny,)`), a 3-line local
  `AllowAny` permission class, and the five `DjangoMutationField` fields on the existing
  `Mutation` type. No `config/schema.py` edit needed (it composes `ProductsMutation`
  already; `bind_mutations()` / `bind_form_mutations()` run inside the existing
  `finalize_django_types()` — confirmed by SDL introspection).
- `examples/fakeshop/test_query/test_products_api.py` — added the live form-mutation
  matrix (15 tests); imported `REJECTED_ITEM_NAME` + `SimpleUploadedFile`; added the
  four module-level query-string constants (`_CREATE_ITEM_VIA_FORM`,
  `_UPDATE_ITEM_VIA_FORM`, `_CREATE_STAMPED_ITEM_VIA_FORM`, `_SUBMIT_CONTACT`). Reused
  the existing reload fixture + `_post_graphql` / `_login_with_perm` / `_login` /
  `_global_id` helpers verbatim (no new fixture needed — the `apps.products.schema`
  reload already covers the new mutations once wired).

### Tests added or updated

All in `examples/fakeshop/test_query/test_products_api.py`, all
`@pytest.mark.django_db(transaction=True)`, all seeded `create_users` / `seed_data` /
`seed_cascade_split` first line:

- `test_create_item_via_form_happy_path` — `createItemViaForm` create + `node` re-fetch.
- `test_create_item_via_form_category_id_writes_through_form_category_field` — P1 reverse
  map: `categoryId` → form `category` field; `created.category_id == submitted pk`.
- `test_update_item_via_form_non_colliding_partial_update` — `name`-only update succeeds.
- `test_update_item_via_form_partial_update_preserves_category_and_description` —
  RIGHT-PATH/LOAD-BEARING: `data:` is `{name}` ONLY; `category_id` + `description`
  unchanged after `refresh_from_db()`.
- `test_update_item_via_form_partial_collision_fires_unique_constraint_on_name_change` —
  RIGHT-PATH/LOAD-BEARING: `{name: "FormB"}` only; the reconstructed unchanged `category`
  co-participates → `"__all__"`-keyed `FieldError`, row unchanged.
- `test_create_item_via_form_clean_field_error_is_field_keyed` — `clean_name` →
  `errors[0].field == "name"`, no top-level error, no write.
- `test_create_item_via_form_unique_constraint_envelope_uses_all_sentinel` — duplicate
  create → `"__all__"` sentinel.
- `test_create_item_via_form_anonymous_is_denied_top_level_error_no_write` — top-level
  `Not authorized`, `data` null, no write.
- `test_create_item_via_form_missing_model_perm_is_denied_no_write` — `view_item_1`
  lacking `add_item` → top-level denial, no write.
- `test_update_item_via_form_visibility_scoped_hidden_private_row_is_not_found` — hidden
  private `Item` → not-found `FieldError` on `id`; visible public row succeeds.
- `test_create_item_via_form_relation_id_for_hidden_category_is_field_error` —
  RIGHT-PATH/LOAD-BEARING headline P1: well-formed-but-hidden `Category` GlobalID →
  `["categoryId"]`-keyed `FieldError`, no write; the SAME caller's create against the
  visible public category succeeds.
- `test_create_item_with_file_via_form_multipart_upload_over_http` — raw
  `django.test.Client` multipart POST (`operations` / `map` →
  `["variables.d.attachment"]` / `SimpleUploadedFile`); `errors == []`, row exists with
  `attachment.name endswith "doc.txt"` and the bytes round-trip (proving the `data=` /
  `files=` split routed the `Upload` into the form's `files=`).
- `test_create_stamped_item_via_form_get_form_kwargs_injects_user` — P2: the override
  injects `user`; the created row's `description == "stamped by view_item_1"` (the user
  reached the form; bind never instantiated the kwarg-requiring form).
- `test_submit_contact_plain_form_success_shape` — plain `Form` success: `ok is True`,
  `errors == []`.
- `test_submit_contact_plain_form_validation_failure_shape` — plain `Form` failure:
  `ok is False`, `errors[0].field == "subject"`.

### Validation run

- `uv run ruff format .` — pass (stable / idempotent after the trailing-comma fixer ran;
  final run: 0 reformatted, 277 unchanged).
- `uv run ruff check --fix .` — pass (`All checks passed!`; 1 auto-fixed during the pass).
- `scripts/check_trailing_commas.py` (the mandatory AGENTS.md layout enforcer, separate
  from ruff) — ran the auto-fixer on `products/forms.py` + `products/schema.py` (it
  collapsed the under-threshold tuples and exploded the `Mutation` field list + the
  import block); my slice-intended files are CLEAN on `--check` afterward. The remaining
  `--check` violations live only in `tests/forms/test_resolvers.py` /
  `forms/resolvers.py` (Slice 1-3 files, out-of-scope — NOT mine).
- `git status --short` after both ruff invocations — classified below. No tool churn to
  revert: every ruff/trailing-comma change is part of my intended slice diff.
  - **Slice-intended (stay in diff):** `products/forms.py` (new),
    `products/migrations/0002_item_attachment.py` (new), `products/models.py`,
    `products/schema.py`, `test_query/test_products_api.py`, this artifact.
  - **Out-of-scope prior-slice / build accepted diff (NOT mine, do not revert):** all
    `django_strawberry_framework/*` (Slices 1-3), `tests/mutations/*` + `tests/forms/`
    (Slices 1-3), `docs/SPECS/spec-038...md`, `docs/builder/bld-slice-1/2/3*.md` +
    `build-038*.md`, the deleted `037` / prior `bld-*` artifacts (pre-flight cleanup).
  - **Concurrent / external (LEAVE per dispatch):** `docs/feedback.md` (M — explicitly
    "do NOT touch"). `examples/fakeshop/db.sqlite3` and `KANBAN.html` do NOT appear in
    `git status` — UNTOUCHED, as required.
- Focused tests (no `--cov*`): `uv run pytest examples/fakeshop/test_query/test_products_api.py --no-cov`
  → **71 passed** (56 pre-existing + 15 new). The test DB applied `0002_item_attachment`
  automatically.
- `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run products`
  → `No changes detected` (exit 0) — model state is migration-consistent; no `migrate`
  run, `db.sqlite3` untouched.

### Implementation notes

- **File column on `Item`, not a new model** (discretion item). `ItemType` is already the
  registered primary `DjangoType` for `Item`, so the file-form's model has a registered
  primary type for free (the binding constraint) and the payload uses the `node` slot
  (Relay-shaped). The nullable column leaves `seed_data` / every existing
  `Item.objects.create` untouched (the other binding constraint).
- **Dedicated `ItemFileModelForm` rather than collapsing the file column into
  `ItemModelForm`.** Keeps the create/update/partial-update/category-reverse-map tests
  driving a narrow `name/description/category` input (no spurious `attachment` field on
  the everyday form) while the multipart test drives its own form. The plan explicitly
  allowed either; this isolates the file surface.
- **`FileField` (not `ImageField`)** per the plan recommendation — the routing proof
  needs no image dimensions / Pillow; a plain-text `SimpleUploadedFile` suffices.
- **3-line local `AllowAny`** in `schema.py` — the package ships no allow-all permission
  class (only `DjangoModelPermission`), and a plain `DjangoFormMutation` requires an
  explicit `Meta.permission_classes`; the allow-all opens the `submitContact` success
  path to any caller (a plain form's authorization is a consumer choice, per Decision 11).
- **`StampedItemModelForm` is the P2 kwarg-requiring form** (a `ModelForm`, discretion
  choice). Its `save()` stamps `description = "stamped by <username>"` so the live test
  pins the *user-stamped side effect* — proof the injected user reached the form, not just
  that the create succeeded.
- **Multipart `map` uses `variables.d.attachment`** (not `variables.data.attachment`) —
  the GraphQL variable is named `$d` in the query string (matching the repo's existing
  `_post_graphql` `variables={"d": ...}` convention), so the multipart `map` path must
  reference `d`, not `data`.
- **The multipart test reads the stored file via `attachment.open("rb")` in a `with`
  block.** A bare `created.attachment.read()` leaves the `FieldFile`'s underlying handle
  open, which the suite's `-W error` posture catches as a
  `PytestUnraisableExceptionWarning` (a leaked-file finalizer) on the *next* test. The
  context-managed open closes it deterministically.
- **No `config/schema.py` edit** — confirmed by SDL introspection that all five form
  fields, their generated inputs (`ItemModelFormInput` / `ItemModelFormPartialInput` /
  `ItemFileModelFormInput` / `StampedItemModelFormInput` / `ContactFormInput`), and
  payloads (`node`-slot for the `ModelForm` flavors, `{ ok, errors }` for `submitContact`)
  materialize inside the existing `finalize_django_types()`.

### Notes for Worker 3

- The live `IntegrityError` sub-check is DEFERRED to the package tier (see Notes for
  Worker 1 below) — it is the one Slice-4 contract NOT landed live, with the deferral
  reason and the owning unit tests cited. Every other Decision-12 / Test-plan live
  contract landed and passes.
- `scripts/review_inspect.py` was NOT run during build: `products/forms.py` is a
  pure-form-definition module (Django form classes + two tiny `clean_*` methods + a
  3-line `save`), well under any complexity hotspot, and outside
  `django_strawberry_framework/`. Worker 3 runs the review helper per its own
  ≥50-new-line trigger on `forms.py` / `schema.py` / `test_products_api.py`.
- The `makemigrations products` invocation emits a harmless `Formatters failed to launch`
  warning (Django tries to shell out to `black`, which is not installed in this venv);
  the migration `.py` was still written correctly and ruff/the trailing-comma fixer
  formatted it afterward. Not an error.

### Notes for Worker 1 (spec reconciliation)

- **Live `IntegrityError` sub-check DEFERRED to the package tier (plan-authorized
  fallback).** The plan (and spec Test-plan line 2014-2016) allow this single sub-check
  to fall back to `tests/forms/test_resolvers.py` if a deterministic live
  `IntegrityError` cannot be provoked through the form. For `Item`, the ONLY DB
  constraint is `unique_item_per_category`, which the `ModelForm`'s `_post_clean` →
  `validate_constraints()` catches BEFORE `save()` (surfacing as the `"__all__"`
  envelope, already covered live by
  `test_update_item_via_form_partial_collision_fires_unique_constraint_on_name_change`
  and `test_create_item_via_form_unique_constraint_envelope_uses_all_sentinel`). There is
  no realistic single live request where `form.is_valid()` passes but `form.save()`
  raises `IntegrityError`, so a live test would have to mock `form.save` to raise — which
  is exactly the package-tier shape. The `_save_or_field_errors` IntegrityError→envelope
  mapper proof is owned by `tests/forms/test_resolvers.py::test_modelform_save_integrity_error_maps_to_envelope`
  (ModelForm `node`-null envelope) and `::test_plain_form_perform_mutate_integrity_error_maps_to_envelope`
  (plain `{ ok: false }`), both shipped in Slice 3. Recommend final verification accept
  the deferral (AGENTS.md live-priority rule permits the unreachable-live line to fall
  back to the tier that owns the mapper).
- **No spec gaps found.** Every symbol the slice needed exists; the SDL materializes
  exactly the Decision-12 surface. The file-field-on-`Item` choice confirms the spec
  (Decision 12 explicitly authorizes the products file column); reuse-`MediaSpecimen` was
  the considered-and-rejected alternative per the plan, not a reconciliation candidate.
- **Stale spec status-line (lines 42-45) carry-forward.** The plan flagged the spec
  status line "Slices 3-5 remain" as stale (Slice 3 is `final-accepted`). This build pass
  did not edit the spec (Worker 2 cannot), so the correction (now `4-5 remain`, or `5
  remains` once this slice is final-accepted) is still pending a Worker-1 spec-touching
  pass. Flagging it again so it is not lost.

---

## Review (Worker 3)

Reviewed the Slice-4 artifact + the working-tree diff for the example-project files only
(`products/forms.py` [new], `products/models.py`, `products/schema.py`,
`products/migrations/0002_item_attachment.py` [new], `test_products_api.py` [+15 tests]).
Confirmed NO package (`django_strawberry_framework/`) source change is attributable to
this slice — every `django_strawberry_framework/*` and `tests/{mutations,forms}/*` diff is
cumulative Slices 1-3 (the `__init__.py` two-export add + `__version__` still `0.0.11` are
Slice-2's, per my Slice-3 memory entry).

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

Clean. No duplication introduced.
- The new tests reuse every existing fixture/helper verbatim (`_post_graphql`,
  `_assert_graphql_data`, `_login`, `_login_with_perm`, `_global_id`, the autouse
  `_reload_project_schema_for_acceptance_tests`); the multipart POST is inlined in the
  single upload test (mirroring `test_uploads_api.py`), not extracted to a cross-file
  shared helper — the right call per the plan's named extraction condition (extract only
  if 2+ multipart tests land; only one did).
- The four module-level query-string constants (`_CREATE_ITEM_VIA_FORM`, etc.) spell each
  wire contract once, named distinctly from the `036` `_CREATE_ITEM` family.
- The 3-line local `AllowAny` in `schema.py` is NOT a DRY miss: the package ships only
  `DjangoModelPermission` (verified — `mutations/permissions.py` has no allow-all class),
  and a plain `DjangoFormMutation` requires an explicit `Meta.permission_classes` (Decision
  11 / edge case). Its `has_permission(info, mutation, operation, data, instance)` signature
  matches the seam exactly. A one-time consumer-side class, nothing to reuse.
- `ItemFileModelForm` is kept distinct from `ItemModelForm` (rather than collapsing the
  file column into the everyday form) — the plan explicitly allowed either; isolating the
  `attachment` field off the create/update/partial-update input surface is the cleaner choice.

### Public-surface check

`django_strawberry_framework/__init__.py` is UNCHANGED by Slice 4. The only diff there is
the Slice-2 form-export add (`DjangoFormMutation` / `DjangoModelFormMutation`) and
`__version__` is still `0.0.11` (the version cut is Slice 5). No package export, no
`__version__`, no public surface touched by THIS slice.

### CHANGELOG sanity

Not applicable (no package release in this slice; the CHANGELOG edit + `0.0.12` cut are
Slice 5).

### Documentation / release sanity

The new migration `0002_item_attachment.py` is faithful, minimal, and source-only:
- A single `migrations.AddField` adding `attachment =
  models.FileField(blank=True, null=True, upload_to="product_media/")`, byte-consistent
  with the model edit on `Item`. `dependencies = [("products", "0001_initial")]` is correct
  (0001 was the latest existing migration).
- `makemigrations --check --dry-run products` → `No changes detected` (exit 0): model state
  is migration-consistent.
- The committed `db.sqlite3` was NOT migrated: `PRAGMA table_info(products_item)` on the
  committed DB shows NO `attachment` column (cols stop at `category_id`), proving Worker 2
  ran `makemigrations` (writes a `.py` only) but never `migrate` against it. The
  `db.sqlite3` git churn is `0 insertions / 0 deletions` (same byte size) and the DB is full
  of `kanban_*` tables — the concurrent external kanban writer (build-wide flag), correctly
  left untouched.
- `seed_data` is unaffected: the column is nullable/blank, so existing `Item.objects.create`
  calls don't break — confirmed by 71 passing and the happy-path test asserting
  `created.description == ""`.

### What looks solid

- **Relation visibility (right-path) — genuinely right-path, the slice's headline value.**
  `test_create_item_via_form_relation_id_for_hidden_category_is_field_error` submits a
  well-formed-but-HIDDEN `Category` GlobalID as `categoryId` and asserts
  `[e["field"] for e in result["errors"]] == ["categoryId"]` + no write, then the SAME
  caller's create against the VISIBLE public category SUCCEEDS. I additionally proved
  (temp test) that `ItemModelForm.fields["category"].queryset` is the unscoped
  `Category.objects.all()` and WOULD accept the private category — so the `FieldError`
  comes from the resolver's `get_queryset` visibility decode (the P1 security guard), not
  the form's own queryset. Not vacuous: the visible-cat contrast and the unscoped-queryset
  fact together pin the right path.
- **Partial-update preservation + collision (right-path).** Both update tests send a
  MINIMAL `data: {name: ...}` (only `name`), so they can only take the partial-reconstruction
  path. Preservation test asserts `category_id` + `description` unchanged after
  `refresh_from_db()`; collision test changes only `name` to a colliding value and gets the
  `"__all__"`-keyed `FieldError` with the row unchanged — which is only possible if
  reconstruction supplied the unchanged `category` into the composite constraint. A
  full-payload `data:` would not prove partial semantics; these do.
- **Multipart `Upload` (P1 file-routing).** Raw `django.test.Client` POST with
  `{operations, map, "0": SimpleUploadedFile("doc.txt", b"form upload bytes", ...)}` and
  `map = {"0": ["variables.d.attachment"]}` (the `$d` variable name matches the repo's
  `_post_graphql` convention). Asserts `errors == []`, the row exists, AND round-trips the
  bytes via a context-managed `attachment.open("rb")` (the deterministic close avoids the
  `-W error` leaked-file-finalizer trap). It proves the file landed (not just a 200), so the
  `data=`/`files=` split routed the `Upload` into the form's `files=`.
- **`form.errors` envelope.** `clean_name` → field-keyed (`["name"]`); the
  `unique_item_per_category` constraint → `"__all__"` (both create and partial-update
  variants) — surfaces automatically through `_post_clean` → `validate_constraints`.
- **Write-auth.** Anonymous denied + missing-`add_item` denied both assert a TOP-LEVEL
  `payload["errors"]` with `data is None` + `"Not authorized"` + no write (not a FieldError);
  permitted (`add_item`) succeeds. Codenames `add_item`/`change_item` per the inherited
  `DjangoModelPermission`.
- **Visibility-scoped `update`.** Holds `change_item` but cannot see the private `Item` →
  not-found `FieldError` on `id`, row unchanged; the same update succeeds for the visible
  public row.
- **`get_form_kwargs` injecting `user` (P2).** `StampedItemModelForm.__init__` requires
  `user`; the override injects `info.context.request.user`; the created row's `description`
  is stamped `"stamped by view_item_1"` — pins the user-stamped side effect (proof the user
  reached the form, and that schema-time `base_fields` discovery never instantiated the
  kwarg-requiring form).
- **Plain `Form`.** `submitContact` success → `ok: true`, empty `errors`; failure (blank
  `clean_subject`) → `ok: false`, field-keyed `["subject"]`.
- **`seed_data`/`create_users` first-line rule (AGENTS.md):** all 15 new tests open with
  `create_users(1)` as the first body line (verified per-test). No model text field was
  touched, so the TextField-vs-CharField rule does not apply; the nullable `FileField`
  doesn't perturb the 56 pre-existing `Item` tests (all still pass).

### Temp test verification

- `uv run pytest examples/fakeshop/test_query/test_products_api.py --no-cov` → **71 passed**
  (56 pre-existing + 15 new).
- Ran the 6 highest-value new tests individually (multipart, hidden-category, partial
  preserve, partial collision, stamped-user, plain-form failure) → all pass.
- Temp test (`docs/builder/temp-tests/slice-4/`, now removed) confirmed
  `ItemModelForm.category` queryset is unscoped `Category.objects.all()` — the right-path
  proof for the relation-visibility test. Temp tests removed; `db.sqlite3` / `KANBAN.html`
  untouched.
- Ran the review-inspect helper on `forms.py` + `schema.py` (≥50 new lines each, outside
  the package): both report 0 control-flow hotspots in the new code; `forms.py` is pure form
  definitions (0 ORM markers, 0 TODOs); `schema.py`'s 15 TODOs + 8 `getattr()` are all in the
  PRE-EXISTING `get_queryset` scaffolding (lines 34-198), none in the Slice-4 form-mutation
  additions (258+). Shadow files in `docs/shadow/`.
- `ruff check` / `ruff format --check` / `scripts/check_trailing_commas.py` all clean on the
  five Slice-4 files (the COM812 advisory is a pre-existing repo config note, not a finding).

### IntegrityError deferral — legitimate

Worker 2's deferral of the live write-time `IntegrityError` sub-check to the package tier is
sound. For `Item`, the only DB constraint is `unique_item_per_category`, which
`ModelForm._post_clean` → `validate_constraints()` catches BEFORE `save()` (surfacing as the
`"__all__"` envelope, covered live by two tests). No realistic single live request reaches a
`form.save()` IntegrityError — provoking it would require mocking `form.save`, which is
exactly the package-tier shape. The cited package tests exist and genuinely prove the
`_save_or_field_errors` mapper:
`tests/forms/test_resolvers.py::test_modelform_save_integrity_error_maps_to_envelope`
(L699 — patches `forms.ModelForm.save` to raise, asserts `node` null + `"__all__"`,
`res.errors is None`) and `::test_plain_form_perform_mutate_integrity_error_maps_to_envelope`
(L721 — `perform_mutate` raises, asserts `ok: false` + `"__all__"`). AGENTS.md live-priority
permits the unreachable-live line to fall back to the tier owning the mapper. Accepted.

### Verbatim checklist audit

Both `### Spec slice checklist (verbatim)` boxes are ticked `- [x]` and match the spec's
Slice 4 sub-bullets (lines 446-462) word-for-word. Every claim is satisfied by the diff:
`forms.py` ships `ItemModelForm` (+`clean_name`) + a plain `ContactForm`; `schema.py` gains
`DjangoModelFormMutation` (create+update) and a `DjangoFormMutation`; the file column +
source-only migration landed; the live matrix covers create/update, `categoryId`-through-form,
partial-update preservation + collision, the `form.errors` envelope (field + `"__all__"`),
write-auth, visibility-scoped update, the raw multipart `Upload`, and plain-form
success/failure. No box overclaims.

### Notes for Worker 1

- **Escalated:** the stale spec status-line (`spec-038` lines 42-45: "Slices 3-5 remain")
  carried forward by both Worker 1's plan and Worker 2's build report. Slice 3 is
  `final-accepted` and Slice 4 is now `review-accepted`, so the line should become
  "Slice 5 remains" (or `4-5` until Slice 4 is final-accepted) when a Worker-1 spec-touching
  pass next runs. Not a Slice-4 defect (no spec edit is licensed in a review pass); flagged so
  it is not lost.

### Review outcome

**review-accepted.** Zero High/Medium/Low. The three core right-path contracts
(relation-visibility, partial-update preservation/collision, multipart `Upload`) are
genuinely right-path and load-bearing. The migration is faithful, minimal, and source-only;
the committed `db.sqlite3` is untouched. The `IntegrityError` deferral is legitimate and the
package-tier coverage it cites exists. Verbatim boxes match. No package source touched. All 71
tests pass; lint/format/trailing-comma clean. One item escalated to Worker 1 (the stale spec
status line — non-blocking).

---

## Final verification (Worker 1)

### Summary

Slice 4 ships the **live `/graphql/` acceptance surface** for the form-mutation
pipeline Slices 1-3 built — pure example-project consumer wiring + live HTTP tests,
**no package source touched** (independently confirmed: every `django_strawberry_framework/*`
and `tests/{mutations,forms}/*` diff is cumulative Slices 1-3; `__version__` is still
`0.0.11`, the bump is Slice 5). New: `examples/fakeshop/apps/products/forms.py` (four
consumer forms — `ItemModelForm` with `clean_name` + the auto-surfacing
`unique_item_per_category` constraint, the model-less plain `ContactForm`,
`StampedItemModelForm` for the P2 `get_form_kwargs`-injects-`user` case, and
`ItemFileModelForm` carrying the nullable `attachment` `FileField`). Modified:
`products/models.py` (+nullable `attachment` `FileField` on `Item`), `products/schema.py`
(five `DjangoMutationField`s — `CreateItemViaForm`/`UpdateItemViaForm`/`CreateItemWithFileViaForm`/`CreateStampedItemViaForm` `DjangoModelFormMutation`s + the
plain `SubmitContact` `DjangoFormMutation` with a 3-line local `AllowAny`), and
`test_products_api.py` (+15 live tests). New source-only migration
`0002_item_attachment.py`.

**Verdict: `final-accepted`.**

- **Spec slice checklist audit — both verbatim boxes correctly ticked, no over-ticks.**
  Box 1 (`forms.py` + `schema.py` + the file column/migration) and Box 2 (the live
  matrix in `test_products_api.py`) both genuinely landed in the diff — verified
  symbol-by-symbol. `forms.py` ships `ItemModelForm` (+`clean_name`) + a plain
  `ContactForm`; `schema.py` gains a `DjangoModelFormMutation` (create + update) and a
  `DjangoFormMutation`; the minimal `FileField` + source-only migration landed; the live
  matrix covers create/update, `categoryId`-through-form, partial-update preservation +
  one-field collision, the `form.errors` envelope (field-level + `"__all__"`), write-auth,
  visibility-scoped update, the raw multipart `Upload`, and plain-form success/failure.
  No box claims more than the diff delivers.

- **Live-test quality (the slice's whole point) — the three core right-path contracts
  confirmed genuinely right-path + load-bearing.**
  - *Relation-visibility* (`test_create_item_via_form_relation_id_for_hidden_category_is_field_error`,
    line 2475): submits a **well-formed-but-hidden** `Category` GlobalID via the GraphQL
    `categoryId` arg, asserts `[e["field"] for e in result["errors"]] == ["categoryId"]`
    + no write, AND contrasts with the SAME caller succeeding against the visible public
    category. The error comes from the resolver's `get_queryset` visibility decode, NOT
    the form's own unscoped `Category.objects.all()` queryset (the visible-cat contrast
    is what makes it non-vacuous; Worker 3 additionally proved the form queryset would
    have accepted the private cat). Right-path, not via the form's queryset. ✓
  - *Partial-update preservation* (line 2225): `data:` is `{name}` ONLY; after the update
    pins `item.category_id` + `item.description` UNCHANGED via `refresh_from_db()` while
    `name` is the new value — proves the `model_to_dict` reconstruction supplies the
    omitted FK/scalar. ✓
  - *Partial collision* (line 2263): `data:` is `{name: "FormB"}` ONLY; the `"__all__"`
    constraint can only fire because the reconstructed unchanged `category`
    co-participates in the composite constraint; row unchanged. ✓
  - *Multipart upload* (`test_create_item_with_file_via_form_multipart_upload_over_http`,
    line 2535): a raw `django.test.Client` GraphQL-multipart POST with
    `map = {"0": ["variables.d.attachment"]}` routes the `SimpleUploadedFile` into the
    form's `files=`; asserts `errors == []`, the row exists, and the bytes round-trip via
    a context-managed `attachment.open("rb")` (deterministic close vs the `-W error`
    leaked-file trap). Proves the `data=`/`files=` split, not just a 200. ✓
  - The live `IntegrityError` sub-check is the ONE Slice-4 live contract not landed live —
    **plan-authorized deferral** (the plan's Test-additions + spec Test-plan lines 2014-2016
    license the fallback to the package tier when no deterministic live provocation exists;
    `Item`'s only constraint is `unique_item_per_category`, caught by `_post_clean` BEFORE
    `save()`). It is **recorded, not silently dropped** (Worker 2's Notes for Worker 1,
    Worker 3's "IntegrityError deferral — legitimate" section), and the cited
    package-tier mapper tests genuinely exist:
    `tests/forms/test_resolvers.py::test_modelform_save_integrity_error_maps_to_envelope`
    (L699) + `::test_plain_form_perform_mutate_integrity_error_maps_to_envelope` (L721).
    Deferral accepted; carried to `bld-final.md`'s deferred-work catalog.

- **Migration faithful + source-only — independently confirmed.** `0002_item_attachment.py`
  is a single `migrations.AddField` of `attachment = models.FileField(blank=True,
  null=True, upload_to="product_media/")` with `dependencies = [("products", "0001_initial")]`,
  byte-consistent with the `Item` model edit. The committed `db.sqlite3`'s
  `products_item` table has NO `attachment` column (`PRAGMA table_info` →
  `[id, name, description, is_private, created_date, updated_date, category_id]`) — proving
  `makemigrations` (writes a `.py` only) ran but `migrate` never touched the committed DB.
  `db.sqlite3` / `KANBAN.html` / `KANBAN.md` are NOT part of the Slice-4 intended diff
  (the `git status` shows them dirty as the concurrent kanban writer's work per the build
  preamble — left untouched, not reverted, per AGENTS.md rule 34). The ephemeral
  pytest-django test DB applied the migration automatically (71 passed).

- **DRY across Slices 1-4 — clean.** Slice 4 adds NO package source, so it introduces no
  package duplication. The new tests reuse every existing fixture/helper verbatim; the
  3-line local `AllowAny` is a one-time consumer class (the package ships no allow-all);
  the multipart POST is inlined (only one upload test — the plan's named extraction
  condition, 2+ tests, was not met). The integration-pass DRY candidates from prior
  slices (`_form_shape_build_cache`↔`_shape_build_cache`;
  `normalize_form_field_sequence`↔`mutations/sets.py::_normalize_field_sequence`; the bare
  `"form"` operation literal; the Slice-1 `queryset=None` Low) are all package-internal
  Slices 1-3 items — Slice 4 touched none of them, so they remain **correctly deferred to
  the integration pass** (not re-flagged here as blockers).

- **Tests pass.** `uv run pytest examples/fakeshop/test_query/test_products_api.py --no-cov`
  → **71 passed** (56 pre-existing + 15 new) in 47s; the test DB applied
  `0002_item_attachment` automatically. `uv run pytest tests/forms/ --no-cov` →
  **119 passed** in 1s (no package-tier regression).

### Spec changes made (Worker 1 only)

- `docs/SPECS/spec-038-form_mutations-0_0_12.md` lines 42-45 (status line) — Slice 4
  triggered (per-spawn stale-status rule, escalated by Worker 3). Was "Slices 1–2 built
  and accepted … Slices 3–5 remain"; now reads "Slices 1–4 built and accepted (… the
  resolver pipeline + `DjangoMutationField` exposure; the products live form surface),
  only Slice 5 remains." Reason: Slices 3 and 4 are `final-accepted`; the prior line was
  stale (Worker 3's escalated item). Minimal + faithful; no contract change.
  `scripts/check_spec_glossary.py --spec docs/SPECS/spec-038-form_mutations-0_0_12.md`
  re-run after the edit → exit 0 (`OK: 31 terms`, matching the pre-flight baseline).
