# Release review feedback - 0.0.12

## Findings

1. [P1] Write-side GlobalID decoding treats a custom Relay NodeID value as a pk.

   The read-side node path correctly treats the decoded id value as whatever
   `resolved_type.resolve_id_attr()` names: `django_strawberry_framework/relay.py::_coerce_pk_or_none`
   explicitly coerces against that field, and
   `django_strawberry_framework/types/relay.py::_resolve_node_default #"id_attr = cls.resolve_id_attr()"`
   filters by that id attr. The write-side helper then returns that same value as
   `DecodeResult.pk` from
   `django_strawberry_framework/relay.py::decode_model_global_id #"pk = _coerce_pk_or_none(resolved_type, node_id)"`,
   but its consumers use it as an actual primary key:
   `django_strawberry_framework/mutations/resolvers.py::coerce_lookup_id #"return result.pk, None"`,
   `django_strawberry_framework/mutations/resolvers.py::locate_instance #"queryset.get(pk=node_id)"`,
   `django_strawberry_framework/mutations/resolvers.py::_relation_membership_error #"queryset.filter(pk__in=query_pks)"`,
   and `django_strawberry_framework/forms/resolvers.py::_visible_related_object #"queryset.filter(pk=pk).first()"`.

   A valid GlobalID for a type declaring something like `name: relay.NodeID[str]`
   is therefore looked up as `pk=<name>` on update/delete and relation writes. It
   usually fails as hidden/missing; worse, if a custom id value overlaps another
   row's pk representation it can target the wrong row. Root fix: do not expose
   the decoded NodeID value as `pk`. Return the resolved type/id attr/coerced id
   value or resolve the visible object through the same id attr, then convert that
   object to the write target's actual assignment value.

2. [P1] Form mutations miss the model mutation path's invalid-Unicode preflight.

   The model mutation decoder rejects unencodable text before any DB-bound
   validation or save via
   `django_strawberry_framework/mutations/resolvers.py::_decode_relations #"text_error = _unencodable_text_error(graphql_name, value)"`.
   The form decoder sends scalar values straight into the bound form at
   `django_strawberry_framework/forms/resolvers.py::_decode_form_data #"provided_data[spec.form_field_name] = raw_choice_value(value)"`.
   For `ModelForm` fields such as
   `examples/fakeshop/apps/products/forms.py::ItemModelForm.Meta #"fields = (\"name\", \"description\", \"category\")"`,
   a lone surrogate can reach `form.is_valid()` constraint queries or `form.save()`
   and raise a raw `UnicodeEncodeError`, bypassing the `{ node: null, errors: [...] }`
   envelope.

   Root fix: apply the same string encodability guard in form scalar decode before
   constructing the form, returning a field-keyed `FieldError` under the input's
   GraphQL field name.

3. [P1] `namedLibraryRecords` leaks restricted branches.

   `examples/fakeshop/apps/library/schema.py::Query.named_library_records` reads
   `models.Branch.objects.order_by("id")` directly and materializes those rows
   into the interface list. That bypasses
   `examples/fakeshop/apps/library/schema.py::BranchType.get_queryset`, which hides
   `city="restricted"` branches from non-staff callers. The current live test only
   seeds visible rows, so it does not catch the bypass.

   Root fix: accept `info` on the resolver and route Branch rows through
   `BranchType.get_queryset(..., info)` before materializing. Add a live
   `/graphql/` regression with a restricted branch.

4. [P2] A `DjangoModelFormMutation` update can finalize an input that can never
   validate when narrowing drops a required non-model form field.

   The create-shaped path guards this with
   `django_strawberry_framework/forms/sets.py::_cached_build_form_input #"guard_create_required_fields(form_class, effective)"`.
   The update path maps to `PARTIAL`, skips that guard, and
   `django_strawberry_framework/forms/inputs.py::build_form_input_class #"required = False if (is_partial and column is not None) else field.required"`
   only keeps required extra fields required if they remain in the generated
   effective input. If `Meta.fields` or `Meta.exclude` removes a required
   column-less field, `_reconstruct_partial_data` cannot reconstruct it because it
   only has model state. The schema finalizes, but every request fails form
   validation.

   Root fix: for `DjangoModelFormMutation` update, fail at bind time when
   narrowing drops a required non-model form field unless `get_form_kwargs` or
   `get_form` is overridden to supply it.

5. [P2] Partial `ModelForm` reconstruction ignores `ModelChoiceField.to_field_name`
   for omitted FK fields.

   Provided relation inputs are decoded through
   `django_strawberry_framework/forms/resolvers.py::_to_form_key_value`, so a
   `ModelChoiceField(to_field_name="slug")` receives the slug value the form will
   validate against. But when that same FK field is omitted on update,
   `django_strawberry_framework/forms/resolvers.py::_reconstruct_partial_data`
   falls through to `model_to_dict(instance, fields=scalar_names)`. For a normal FK,
   that reconstructs the stored pk, not the form field's `to_field_name` value, so
   an omitted FK can fail validation while an explicitly provided unchanged FK
   succeeds.

   Root fix: reconstruct omitted `ModelChoiceField` FK/OneToOne fields from the
   related object and `_to_form_key_value`, the same way the M2M branch already
   reconstructs omitted values.

6. [P2] Mutation/form binding is not retry-idempotent after a later finalization
   failure.

   `django_strawberry_framework/types/finalizer.py::finalize_django_types` documents
   partial-failure recovery, but Phase 2.5 binds mutations before filter/order
   binding and Phase 3. `django_strawberry_framework/mutations/sets.py::bind_mutations`
   clears `_shape_build_cache`, and
   `django_strawberry_framework/forms/sets.py::bind_form_mutations` clears
   `_form_shape_build_cache`, then both rebuild fresh class objects while the
   materialization ledgers in `mutations.inputs` / `forms.inputs` remain populated.
   On rerun, `django_strawberry_framework/utils/inputs.py::materialize_generated_input_class #"if existing is not None:"`
   sees the same generated name backed by a different class object and raises a
   collision, masking the original now-fixed finalization error.

   Root fix: make mutation and form bind reruns reuse the already materialized
   class objects, or clear the relevant materialization ledgers at the start of a
   retry-safe bind pass before re-emitting parked globals. Add a regression where
   finalization fails after mutation binding, the configuration is fixed, and
   `finalize_django_types()` succeeds without `registry.clear()`.

## Sub-agent coverage

- Form construction/input generation reviewer found Finding 4.
- Mutation runtime reviewer found Finding 2.
- Cross-cutting registry/relay/finalizer reviewer found Findings 1 and 6.
- Fakeshop integration reviewer found Finding 3.
- Integrator pass added Finding 5 while reconciling the relation reconstruction
  paths.

## Review commands

- `uv run python scripts/review_changed_python_diffs_against_head.py 0.0.11`
- `uv run python scripts/review_historical_package_snapshot_at_commit.py HEAD`
