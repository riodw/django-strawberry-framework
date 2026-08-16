# DRY review: `django_strawberry_framework/utils/write_values.py`

Status: verified

## System trace

Flavor-neutral owner of the **per-value write decode checks** every write
flavor runs before DB-bound work (promoted out of `mutations/resolvers.py` so
the model resolver is not the utility module for form / serializer / auth):

1. **`unencodable_text_error`** — UTF-8 storability preflight; lone surrogate →
   field-keyed `FieldError`, never raw `UnicodeEncodeError` at save /
   authenticate / hasher.
2. **`raw_choice_value`** — choice-enum member → Django choice `.value`
   (spec-036 Decision 6); non-enum / `None` passthrough.
3. **`coerce_relation_pk_or_none`** — raw relation pk through
   `related_model._meta.pk` via `querysets.coerce_field_value_or_none`;
   uncoercible / out-of-range → `None` ("identifies no row").
4. **`type_check_relation_id`** — structural one-id check without DB:
   `GlobalID` → `decode_model_global_id` (non-`OK` → `relation_field_error`) |
   raw pk → `coerce_relation_pk_or_none` (`None` → same error).
5. **`decode_scalar_leaf`** — compose of (1)+(2) in fixed order so a fourth
   flavor cannot mis-order them.
6. **`decode_visible_relation`** — single-relation security spine: skip →
   `type_check_relation_id` → `visible_related_object` → flavor `project`.
7. **`decode_provided_fields`** — kind-dispatch walk over
   `iter_provided_input_fields` + handler map / scalar fallback.

Module charter (docstring): set-level relation guards (visibility / existence /
membership) stay in `mutations/resolvers.py` — model-pipeline contracts, not
neutral value semantics.

Connected surfaces examined:

- **Callers:** `forms/resolvers.py` (`decode_provided_fields` /
  `decode_scalar_leaf` / `decode_visible_relation`);
  `rest_framework/resolvers.py` (same + `type_check_relation_id` for batched
  multi); `mutations/resolvers.py` (`decode_scalar_leaf`,
  `coerce_relation_pk_or_none` via `_coerce_relation_pk_or_none` alias);
  `auth/mutations.py` (`unencodable_text_error` for login credentials +
  register password exclusion seam).
- **Dependencies:** `utils/errors.py` (`field_error` /
  `relation_field_error`); `utils/inputs.py` (`iter_provided_input_fields`);
  `utils/querysets.py` (`coerce_field_value_or_none`,
  `visible_related_object`); function-local `relay.decode_model_global_id` /
  `GlobalIDDecode` (import-cycle avoidance).
- **Siblings (field selection, not value decode):**
  `relay._coerce_pk_or_none` (id-attr field); `filters/base.py`
  `_coerce_int_in_members` (filter column) — both already share
  `coerce_field_value_or_none`.
- **Tests:** `tests/utils/test_write_values.py` (provided / null / omit
  tri-state through the shared layers); choice / Unicode / relation coverage
  via flavor live paths (`tests/mutations/…`, fakeshop `test_query`).

Item baseline `de43a84ee1e1d8644a89142fcb78792bd6764fc2`: target matched
baseline (empty item-scoped diff for the `.py` file). No production edit.

## Verification

Package-wide leftover searches (fresh; not seeded from prior DRY artifacts):

- **`encode("utf-8")` / `UnicodeEncodeError` / unpaired-surrogate wording** —
  sole write-storability site is `unencodable_text_error`. Auth login +
  register password reuse it. `keyset.py` catches `UnicodeEncodeError` on
  cursor base64 `encode("ascii")` — different domain (opaque cursor parse →
  invalid-cursor error), not write input storability.
- **`isinstance(..., Enum)` / `.value` unwrap** — only
  `raw_choice_value` on the write path; filters
  `filters/inputs.py::_unwrap_enum_member` is the only other Enum unwrap
  (see rejected).
- **`coerce_field_value_or_none` / relation-pk coercion** — write raw-pk
  selection is only `coerce_relation_pk_or_none`; mutations set-level raw-pk
  guards call it via the private alias; Relay / filter siblings pick different
  fields and stay put.
- **`decode_model_global_id` / `type_check_relation_id` /
  `relation_field_error`** — form/serializer single spine and serializer multi
  structural half go through `type_check_relation_id`. Model
  `_decode_relation_id_set` keeps its own GlobalID loop + set-level raw-pk
  contract (see rejected).
- **`iter_provided_input_fields` / kind dispatch** — form + serializer route
  through `decode_provided_fields`; model `_decode_relations` walks the same
  UNSET strip but keeps model-attr / FK-index / exclusion-seam / M2M-assignment
  routing locally (see rejected).
- **Exports:** not re-exported from `utils/__init__.py` (callers import the
  module directly). Mutations still re-exports
  `coerce_relation_pk_or_none` / `decode_scalar_leaf` for in-module use;
  `type_check_relation_id` is imported there with `# noqa: F401` claiming
  form/serializer/tests consumers — those consumers already import from
  `write_values` (deferred; mutations file is concurrent dirty work).

No scratch experiments required: ownership and call-graph evidence were
decisive.

Strongest rejected candidates:

- **Fold `filters/inputs.py::_unwrap_enum_member` into `raw_choice_value`.**
  Identical one-liner (`Enum` → `.value`, else passthrough). Different
  ownership and change axis: write decode (composed inside
  `decode_scalar_leaf` with Unicode preflight; feeds model/form/serializer
  bound data) vs filter wire → django-filter form clean (list unwrap at call
  sites, no storability compose). `write_values` charter is write-flavor
  primitives; pulling filters in expands the module past its owner. A new
  shared one-line utils helper would optimize line count, not a lockstep
  contract.
- **Route model `_decode_relation_id_set` through `type_check_relation_id`.**
  GlobalID half matches (non-`OK` → `relation_field_error`). Raw-pk half does
  **not**: `type_check` errors immediately on uncoercible pk; the model set
  path collects raw values then drops uncoercible members inside
  `_raw_pk_relation_error` / membership before `pk__in` (same not-found
  envelope, different per-id vs set-level timing). Module docstring already
  records the deliberate non-use. Partial GlobalID-only reuse would obscure
  that split for ~4 lines of already-shared `decode_model_global_id`.
- **Route model `_decode_relations` through `decode_provided_fields`.**
  Near-parallel walk, different key space and side effects: model attrs +
  `fk_by_attr` / `m2m_by_name` index, `excluded_input_fields` capture,
  explicit-null + naive-datetime compose around `decode_scalar_leaf`, M2M
  assignment list — not a `{spec.kind: handler}` reverse map. Forcing it
  through the form/serializer dispatcher needs mode flags.
- **Collapse `coerce_relation_pk_or_none` into call sites /
  `coerce_field_value_or_none`.** The one-liner is the named write-domain
  owner of *which* field (`_meta.pk`), sibling to Relay id-attr and filter
  column selection. Deleting it would re-scatter field choice.
- **Merge form multi (per-element `decode_visible_relation`) with serializer
  multi (batch `type_check` + `visible_related_objects`).** Documented
  intentional divergence: form needs objects for `to_field_name`; serializer
  needs one `pk__in`. Only the per-id spine is shared.
- **Inline `raw_choice_value` into `decode_scalar_leaf` only.** Separate
  primitive keeps the Decision-6 unwrap rule named and independently
  documented; compose order still owned by `decode_scalar_leaf`.

## Opportunities

None — the seven primitives already own write-side Unicode preflight, choice
unwrap, raw relation-pk field selection, structural relation-id check,
scalar-leaf compose, single-relation visibility spine, and form/serializer
kind-dispatch. Leftover similar shapes (filter enum unwrap, Relay/filter
coercion field pickers, model set-level relation guards, model decode walk,
keyset cursor Unicode) are distinct contracts that should not change with
this module.

## Judgment

Proved zero-edit. `utils/write_values.py` is the true owner of neutral
per-value write decode; form / serializer / model scalar leaf / auth
storability already terminate here. No leftover inline Unicode preflight,
choice unwrap, or form/serializer decode walk remains on the write path.
Ready for Worker 2.

Item-scoped diff vs `de43a84ee1e1d8644a89142fcb78792bd6764fc2`: artifact only
(`docs/dry/dry-file-utils__write_values.md`);
`django_strawberry_framework/utils/write_values.py` unchanged.

Deferred findings (out of this item's edit scope — concurrent dirty
`mutations/resolvers.py` / `forms/resolvers.py`):

- Dead `type_check_relation_id` re-export + `# noqa: F401` in
  `mutations/resolvers.py` (comment claims form/serializer/tests; none import
  it from mutations). Candidate delete on the mutations DRY item / when that
  file is free.
- `forms/resolvers.py` module docstring still narrates decode as calling
  `_coerce_relation_pk_or_none` directly; transitively true via
  `decode_visible_relation` → `type_check_relation_id`, but the public spine
  name has moved.

Deferred pytest: none required (no production edit). Existing coverage:
`tests/utils/test_write_values.py`; choice / Unicode / relation paths via
flavor tests and fakeshop live queries.

## Independent verification (Worker 2)

**Outcome: verified** (zero-edit claim holds).

Scoped diff vs `ITEM_BASELINE`
`de43a84ee1e1d8644a89142fcb78792bd6764fc2`:
`django_strawberry_framework/utils/write_values.py` is byte-identical
(`cmp` clean; `git diff` empty). Artifact-only cycle record.

Independent re-trace (present-day callers, not Worker 1 narration):

- Form / serializer import `decode_provided_fields`, `decode_scalar_leaf`,
  `decode_visible_relation` from this module; serializer multi also calls
  `type_check_relation_id` then batched `visible_related_objects`.
- Model `_decode_relations` uses `decode_scalar_leaf` for scalars and keeps
  local FK/M2M/exclusion/null/datetime routing; set guards call
  `_coerce_relation_pk_or_none` (= `coerce_relation_pk_or_none`).
- Auth login + register password call `unencodable_text_error` directly
  (password exclusion seam; not a full scalar leaf).
- Tests import from `utils.write_values`, not mutations. No
  `utils/__init__.py` re-export.

Leftover searches (fresh): sole write-path `encode("utf-8")` /
unpaired-surrogate wording is here; sole write-path `Enum` unwrap is
`raw_choice_value` (filters keep `_unwrap_enum_member`); keyset
`UnicodeEncodeError` is cursor `encode("ascii")` only.

Challenges to rejected candidates — **all upheld**:

1. **`_unwrap_enum_member` ↔ `raw_choice_value`.** Bodies match
   (`Enum` → `.value`). Filters use it for wire → django-filter clean
   (list-mapped at call sites, no Unicode compose). Folding into
   `write_values` expands the write-flavor charter; a third one-line helper
   is line-count, not a lockstep write contract.
2. **`_decode_relation_id_set` → `type_check_relation_id`.** GlobalID half
   matches. Raw-pk half does not: set decoder appends raw values and coerces
   later inside `_raw_pk_relation_error` / existence (drop from `pk__in`,
   membership vs full input); `type_check` errors immediately on
   uncoercible. Docstring already records the deliberate non-use.
3. **`_decode_relations` → `decode_provided_fields`.** Same
   `iter_provided_input_fields` walk, different key space / side effects
   (exclusion seam, `fk_by_attr` / `m2m_by_name`, explicit-null +
   naive-datetime around the shared leaf). Not a `{kind: handler}` map.

Deferred items — **correctly not this file**:

- Dead `type_check_relation_id` `# noqa: F401` re-export in
  `mutations/resolvers.py`: no consumer imports it from mutations
  (form/serializer/tests use `write_values`). Lives on the mutations module
  (plan item already closed); deleting it is not a `write_values` edit.
  Note: that file is clean vs HEAD now (Worker 1's "concurrent dirty" was
  situational); ownership still blocks this item.
- Stale forms module docstring (`_coerce_relation_pk_or_none` /
  `decode_model_global_id` wording): `forms/resolvers.py` is concurrent
  dirty; public spine is already `decode_visible_relation`.

No missed write-path consolidation found. Plan checkbox may close.
