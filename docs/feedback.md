# Code review — spec-038 form mutations (`0.0.12`)

Scope: a thorough correctness review of the implemented `DjangoModelFormMutation`
(model-backed) and plain `DjangoFormMutation` (model-less) feature against
`docs/SPECS/spec-038-form_mutations-0_0_12.md`. Files read in full:
`forms/inputs.py`, `forms/converter.py`, `forms/resolvers.py`, `forms/sets.py`,
the `mutations/` integration points they call, the example schemas/forms, and the
package + live test suites.

## Verdict

**Solid. No high- or medium-severity correctness bugs found.** The pipeline does
the hard things right: `data=`/`files=` split, partial-update reconstruction from
the located row, relation reverse-map (`categoryId` → form field `category`),
per-branch relation visibility, write-auth before relation decode, deny-by-default
for plain forms, and sync/async parity through the shared `run_pipeline_async`.
The findings below are all **low-severity** edge-case robustness / cross-flavor
consistency notes plus some live-HTTP coverage gaps. None block the release.

### One prior-review candidate, disproven

The earlier draft review flagged a HIGH "partial update clears stored files."
**I tested this empirically and it is a false positive.** A bound `ModelForm`
with an omitted `FileField` (excluded from both `data=` and `files=`,
`forms/resolvers.py:386`) does **not** clear the stored file: Django's
`FileField.clean(data, initial)` returns `initial` when no new upload arrives,
and the bound form's `initial` carries the instance's existing file. I built an
`Item` with an attachment, ran the exact `_reconstruct_partial_data` shape
(`name`-only change, `files={}`, `instance=item`) through the real
`ItemFileModelForm`, saved, and the attachment was **preserved**. The docstring's
`initial`-preservation claim (`forms/resolvers.py:345-348`) is correct.

## Findings (all Low)

### [L1] Cross-flavor divergence: `null` for an M2M relation — FieldError vs silent clear

A model `DjangoMutation` rejects an explicit `null` M2M with a field-keyed error
(`_relation_null_error`, `mutations/resolvers.py:425-426`: `if value is None:
return [], _relation_null_error(field_name)`). The form path instead treats the
same `null` as an empty replace-set / clear (`forms/resolvers.py:257`:
`if values in form_field.empty_values: return [], None`).

So the identical input — `genreIds: null` — yields a `FieldError` on a model
mutation but a **successful clear** on a `ModelFormMutation`. Each behavior is
internally documented (the form path notes that iterating `None` would raise a
top-level `TypeError`, and lets the bound form decide required-ness), so neither
is wrong in isolation — but a consumer using both mutation flavors will hit two
different contracts for the same wire value. Pick one, or document the split.

### [L2] No fail-loud guard against a `<name>_id` input-attr collision

A relation field `foo` is remapped to input attr `foo_id`
(`relation_input_annotation` / `forms/inputs.py:336`), while a non-relation field
keeps its own name (`_simple_triple`, `forms/inputs.py:348`). A `ModelForm` that
both includes FK `foo` (→ `foo_id`) **and** declares an extra form field literally
named `foo_id` produces two specs with `python_attr == "foo_id"`; the input
namespace build (`utils/inputs.py`) writes the second over the first, silently
dropping one input field. Contrived but reachable. The package is otherwise
fail-loud (`ConfigurationError`); a collision check on the assembled
`python_attr` set would keep that contract instead of silently losing a field.

### [L3] `ModelChoiceField(queryset=None)` at class level raises `AttributeError`, not `ConfigurationError`

`_model_less_relation_annotation` does `related_model = field.queryset.model`
unguarded (`forms/inputs.py:328`). Because schema-time discovery reads
`base_fields` without instantiating the form (by design), a perfectly valid Django
idiom — a `ModelChoiceField` whose `queryset` is assigned in `__init__` — has
`queryset is None` in `base_fields` and raises a bare
`AttributeError: 'NoneType' object has no attribute 'model'` at schema build,
breaking the otherwise-consistent fail-loud contract. A `None` check raising
`ConfigurationError` with the form/field name would make this diagnosable.

### [L4] Plain-form `ChoiceField` becomes `String`, dropping the enum contract

`forms/converter.py` maps a model-less `forms.ChoiceField` to `str`, so a plain
`forms.Form` choice field generates a free-form `String` input rather than a
generated GraphQL enum — asymmetric with the ModelForm path, where a column's
`choices` is routed through the read-side enum. It's documented as intentional,
but the wire contract for a plain-form choice loses schema-level value safety
(clients can submit any string and rely on form validation to reject it). Worth
either generating an enum for plain-form choices or noting the asymmetry in the
form-mutation docs.

## Live-HTTP coverage gaps (logic is unit-tested; only end-to-end exercise is missing)

The package tests in `tests/forms/test_resolvers.py` are strong and cover the
subtle paths — partial-update FK preservation + constraint
(`:931`), omitted-M2M preservation (`:963`), and the `to_field_name` M2M
reconstruction edge (`:1018`). The gaps below are about the **live `/graphql/`**
matrix the spec test plan calls for, not the logic:

- **M2M preservation on partial update — no live test.** `CreateShelfViaForm` is
  create-only and the products `ItemModelForm` has no M2M, so the M2M
  reconstruction branch (`forms/resolvers.py:388-391`) is never exercised over
  HTTP. Covered at the schema/unit level only. Add an `updateShelfViaForm` (or
  M2M-bearing update form) live test.
- **`ImageField` → `Upload` — only a text `FileField` is tested live.**
  `test_create_item_with_file_via_form_multipart_upload_over_http`
  (`test_products_api.py:2536`) is a strong multipart test but uses a plain-text
  `FileField` and explicitly skips image-dimension assertions. The spec names
  `ImageField → Upload`; no live image test exists.
- **Optional/blank field NOT cleared on omission — no distinct live case.** The
  preservation test covers a required-blank scalar (`description`); a genuinely
  optional field left non-cleared on a partial update isn't asserted live.

## Things I checked and found correct (not bugs)

- **`to_field_name` relations work.** The decode resolves the object by pk/GlobalID
  then re-keys via `_to_form_key_value` → `obj.serializable_value(to_field_name)`
  (`forms/resolvers.py:172-183`), so the bound form receives the right key. The
  wire id being pk/GlobalID (not the `to_field_name` value) is a deliberate,
  consistent choice across the read and write surfaces.
- **Write-auth runs before relation decode** on both flavors
  (`forms/resolvers.py:443→445`, `:486→494`) — an unauthorized caller cannot probe
  related-object visibility.
- **Relation visibility on every branch** via `visibility_scoped_related_queryset`
  (`_visible_related_object`, `forms/resolvers.py:142-169`); a hidden FK target
  becomes a field-keyed `FieldError`. Live-tested for both GlobalID
  (`test_products_api.py:2475`) and raw-pk (`test_library_api.py:4473`) paths.
- **`data=`/`files=` split** is correct (`forms/resolvers.py:327-328`, `:453-458`).
- **Plain-form deny-by-default + `{ ok, errors }`** envelope is correct
  (`forms/sets.py:747-751`; live `test_products_api.py:2645,2691`).
- **Sync/async parity** — `resolve_form_async` delegates the identical sync body
  (incl. `transaction.atomic()`) through `run_pipeline_async`; no divergence.
- **Error envelope** reuses the `036` `validation_error_to_field_errors` so a
  form's `NON_FIELD_ERRORS` keys to `"__all__"` identically to a model
  `full_clean()` failure.

## Already addressed

The prior review's only actionable item (example schemas hand-rolling allow-all
permission classes) was resolved in commit `639a3012` — examples now use the
framework-native `permission_classes = []` opt-out.

## Bottom line

No high- or medium-severity correctness problems. The write-side now behaves like
the same package as the read-side: declarative `Meta`, generated inputs,
shared permission/visibility seams, and a shared error envelope. Recommended
follow-ups are all low-priority: decide the L1 `null`-M2M contract split, add the
three fail-loud / asymmetry guards (L2–L4), and close the live-HTTP coverage gaps
(M2M-update, ImageField, optional-blank).
