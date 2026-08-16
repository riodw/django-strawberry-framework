# DRY review: `django_strawberry_framework/utils/converters.py`

Status: verified

## System trace

`utils/converters.py` owns one symbol: `convert_with_mro`. It is the
flavor-agnostic control-flow skeleton for fail-loud field conversion:

1. ordered `isinstance` prechecks (first match wins; handler may return `None`
   to continue);
2. `type(field).__mro__` walk against a caller-supplied registry (most-specific
   registered class wins regardless of dict insertion order);
3. raising fallthrough via `fallthrough_error_factory(field)` — never a silent
   base-class catch-all.

Mechanics only: no `django.forms`, no `rest_framework`, no scalar tables. Each
caller supplies prechecks, registry, and error wording.

**Confirmed consumers (both already on the skeleton):**

- `forms/converter.py::convert_form_field` — relation/file/multi/bare-`Field`
  prechecks, `_SCALAR_FORM_FIELDS` (bare annotations), `_unsupported_form_field`.
- `rest_framework/serializer_converter.py::convert_serializer_field` — nested /
  relation/file/list/multi prechecks, `_SERIALIZER_FIELD_CONVERTERS` (converter
  callables), `_unsupported_serializer_field`.

**Related but separate owner:** `types/converters.py` — `models.Field`-keyed
read-side scalar / file-output conversion (`scalar_for_field`,
`_field_output_type_for`, `convert_scalar`). Same MRO-against-dict *idiom*,
different key space, different surrounding phases, different fallthrough
policies. Independently re-checked from this file's side (see Verification).

**Tests:** `tests/utils/test_converters.py` pins the skeleton in isolation
(precheck order, `None`-continue, most-specific MRO, unregistered-subclass
parent hit, factory raise). Flavor behavior stays in form / serializer tests.

Item baseline `be06bdecf3af783fb18bbd9db249ae8be5ff270a`: target matches baseline
(empty item-scoped diff). No production edits.

## Verification

Searches: `convert_with_mro` / `isinstance_prechecks` / `scalar_registry` /
`fallthrough_error_factory` / `__mro__` across `django_strawberry_framework/`.

Only two production call sites exist — both already delegated. No third
inlined precheck→MRO→raise copy remains under forms/, rest_framework/, or
elsewhere.

Other `__mro__` sites examined and rejected as same-contract duplicates:

| Site | Why not this skeleton |
| --- | --- |
| `types/converters.py::scalar_for_field` | MRO + raise only; empty prechecks would be dead API; key space is `models.Field`; diagnostic needs model/field labels built inline |
| `types/converters.py::_field_output_type_for` | Soft `None` miss — opposite of mandatory raise; adapting would need a mode flag |
| `types/converters.py::convert_scalar` ArrayField/HStoreField branches | Early isinstance that recurse / reject choices / widen nullability — not `handler(field) → conversion` |
| `inspect_django_type._matched_scalar_key` | Diagnostic name of which `SCALAR_MAP` ancestor fired; not conversion |
| `types/base._detect_custom_get_queryset`, `types/relay`, `sets_mixins`, `utils/querysets._rhs_hook_defect` | Class/interface/RHS-hook walks — unrelated domains |

**Strongest rejected candidate — fold `scalar_for_field` (and/or
`_field_output_type_for`) into `convert_with_mro`:**

- **Shared surface is only the 2-line MRO loop.** The load-bearing contract this
  module owns is the *three-phase* fail-loud KIND dispatch (ordered prechecks
  before scalar parents, no catch-all). Form and serializer need that; read-side
  scalar lookup does not.
- **Surrounding phases diverge.** Read side layers ArrayField/HStoreField
  recursion, choice→enum, and null widening *outside* the walk. Form/serializer
  kind prechecks are load-bearing *before* the walk because
  `ModelChoiceField`⊂`ChoiceField` / DRF relation⊂scalar would otherwise collapse
  to `str`.
- **Fallthrough policies oppose.** `_field_output_type_for` returns `None`;
  `convert_with_mro` always raises. Unifying needs a mode flag — forbidden by
  DRY.md for distinct rules.
- **Key spaces stay separate by design** (module docstring): `forms.Field` /
  `serializers.Field` / `models.Field`. Routing read-side through a utils
  skeleton documented as "form + serializer converters" would obscure ownership
  for a thinner shared piece than the three-phase contract.

A thinner `lookup_mro(field, registry)` helper was also considered and rejected:
two lines of Python idiom do not justify a third layer between this skeleton and
callers; the form/serializer lockstep risk lives in precheck ordering + no
catch-all, already single-sited here.

**Also rejected:** extracting a shared fallthrough message template across
`_unsupported_form_field` / `_unsupported_serializer_field` /
`scalar_for_field`. Nouns and remediation differ (form field / serializer
`field_name` / `Model.field` + `SCALAR_MAP`); wording belongs with each flavor.

## Opportunities

None — the three-phase fail-loud converter-dispatch contract already has one
owner (`convert_with_mro`); both form and serializer consumers already ride it;
remaining MRO walks encode different responsibilities (read-side scalar lookup,
soft file-output map, diagnostics, class/interface/RHS policy) that must stay
separate.

## Judgment

This file is already at its correct ownership boundary. Spec-039's promotion of
the skeleton single-sited the GOAL "unmapped field RAISES" control flow for the
two write-side converters. Independently re-checking from this side confirms
the types-side MRO walks must not merge here. Zero production edits.

## Implementation (Worker 1)

Proved zero-edit. No `.py` changes; no ruff; no permanent-test additions
(existing `tests/utils/test_converters.py` already owns the skeleton). Deferred
pytest: none required for this item. No CHANGELOG.

Item-scoped diff vs `be06bdecf3af783fb18bbd9db249ae8be5ff270a`: empty for
`django_strawberry_framework/utils/converters.py`. Only new path this worker
touches is this artifact.

Ready for Worker 2.

## Independent verification (Worker 2)

Re-traced `convert_with_mro` independently against present-day source, both
write-side callers, the types-side MRO walks, and a package-wide search for
leftover inlined precheck→MRO→raise copies.

**Zero-edit confirmed.** Item-scoped
`git diff be06bdecf3af783fb18bbd9db249ae8be5ff270a -- django_strawberry_framework/utils/converters.py`
is empty.

**Both consumers already ride the skeleton; no leftovers.** Production
`convert_with_mro` importers are exactly `forms/converter.py::convert_form_field`
and `rest_framework/serializer_converter.py::convert_serializer_field` (plus
`tests/utils/test_converters.py`). Neither `forms/` nor `rest_framework/` retains
a `for klass in type(...).__mro__` walk — only docstring mentions of the idiom
remain in `forms/converter.py`. Both callers supply ordered kind prechecks,
flavor registries (`_SCALAR_FORM_FIELDS` / `_SERIALIZER_FIELD_CONVERTERS`), and
flavor fallthrough factories.

**Rejected candidates challenged and upheld.**

- Fold `types/converters.py::scalar_for_field` /
  `_field_output_type_for` into this skeleton: shared surface is only the
  two-line MRO loop. `scalar_for_field` has no ordered kind prechecks (empty
  prechecks would be dead API against this module's three-phase contract);
  key space is `models.Field` / `SCALAR_MAP`; fallthrough builds
  `Model.field` + `SCALAR_MAP` remediation inline. `_field_output_type_for`
  soft-returns `None` — opposite of mandatory raise; unifying needs a mode
  flag. `convert_scalar`'s ArrayField/HStoreField `isinstance` branches recurse
  / reject choices / widen nullability — not `handler(field) → conversion`.
- Thinner `lookup_mro(field, registry)`: would sit between this skeleton and
  callers for idiom only; lockstep risk for form+serializer is precheck
  ordering + no catch-all, already single-sited here.
- Shared fallthrough message template across `_unsupported_form_field` /
  `_unsupported_serializer_field` / `scalar_for_field`: nouns and remediation
  differ (form field repr / serializer `field_name` + Meta.fields|exclude /
  `Model.field` + `SCALAR_MAP`). Wording belongs with each flavor.

**Other `__mro__` sites re-checked and kept separate:**
`inspect_django_type._matched_scalar_key` (diagnostic ancestor name),
`types/base._detect_custom_get_queryset`, `types/relay` / `types/finalizer`
interface membership, `sets_mixins`, `utils/querysets._rhs_hook_defect` —
class/interface/RHS-hook domains, not field-conversion dispatch.

**Missed-consolidation search:** no third production caller; no bypass of
`convert_with_mro` on the write-side converters; no second three-phase
fail-loud KIND-dispatch owner. Zero-edit judgment stands.
