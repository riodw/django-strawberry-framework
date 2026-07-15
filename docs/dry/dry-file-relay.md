# DRY review: `django_strawberry_framework/relay.py`

Status: verified

ITEM_BASELINE: `83837bed9cbc70c806e409284196e1a4173e9859`

## System trace

`relay.py` owns the consumer-facing root `node(id:)` / `nodes(ids:)` Relay refetch
fields (`DjangoNodeField` / `DjangoNodesField`). Its responsibilities:

- **Field construction guards.** `_validate_node_target` is a thin wrapper over
  `list_field.py::_validate_relay_djangotype_target` (already the single owner
  of the four base DjangoType-target checks plus the Relay-Node-shaped fifth,
  shared with `connection.py::DjangoConnectionField` since the 0.0.9 pass). No
  duplication here - verified this stays a genuine one-line delegation.
- **Decode-to-dispatch pipeline.** `_decode_or_graphql_error` wraps
  `types/relay.py::decode_global_id` (payload-shape decode only) and converts
  every `ConfigurationError` to the wire `GLOBALID_INVALID` error. `_coerce_pk_or_none`
  then coerces the decoded `node_id` string through the resolved type's
  `resolve_id_attr()` field so an uncoercible/out-of-range literal never reaches
  the ORM as a raw crash. `_check_typed_match` enforces the typed-form identity
  guard. The per-call dispatch (`resolve_node`/`resolve_nodes` classmethods,
  sync/async, single vs batched) and the `_stamp_node_type` /
  `_await_and_stamp` type-hint carry for multi-type-per-model dispatch round out
  the two field factories.
- **The mutation write-side decode primitive.** `GlobalIDDecode` / `DecodeResult`
  / `decode_model_global_id` / `_resolve_real_pk` are the non-raising sibling
  contract `mutations/resolvers.py` (`coerce_lookup_id`, `_decode_relation_id_set`)
  and, transitively via `utils/write_values.py::type_check_relation_id`, the
  form and serializer write flavors all consume. This is spec-036 DRY-2's
  already-consolidated single owner for "decode + model-check + pk-coercion" -
  traced through `forms/resolvers.py` and `rest_framework/resolvers.py`
  (neither hand-rolls a competing NodeID/pk-resolution walk; both go through
  `type_check_relation_id` -> `decode_model_global_id`). **Verified: no
  duplication, no action.**
- **Batch reassembly.** `_interleave` / `_check_nodes_result` are the sole
  owner of "reassemble per-type result lists into input order with null
  holes for a batched id lookup." `connection.py` has no analogous
  reassembly (it paginates a queryset, never batches by an arbitrary id set),
  so there is no sibling copy to reconcile. **Verified: no duplication.**

Sibling files traced as evidence (per the assignment, not re-litigated since
they carry their own plan items): `types/relay.py` (the decode/encode/resolver-default
internals `relay.py` sits on top of - traced `decode_global_id`,
`_resolve_id_attr_default`, `_order_nodes`, `install_globalid_typename_resolver`),
`testing/relay.py` (the public `global_id_for` / re-exported `decode_global_id`
test helpers - no coercion logic of its own), `connection.py` (done - the Relay
connection field; shares `_validate_relay_djangotype_target` with this file,
no other overlap), `list_field.py` (done - owns the shared four-check target
guard `relay.py` delegates to).

## Verification

**Searched for the same "raw literal -> Django field value, or nothing"
responsibility system-wide** (concept search, not just name search - grepped
`to_python(` / `run_validators(` across `django_strawberry_framework/`) and
found three independently-grown copies of the identical two-step coercion:

1. `relay.py::_coerce_pk_or_none` - coerces a GlobalID's `node_id` through the
   resolved DjangoType's `resolve_id_attr()` field.
2. `utils/write_values.py::coerce_relation_pk_or_none` - coerces a raw M2M pk
   through `related_model._meta.pk`. Its own docstring already named site 1 as
   "the raw-pk M2M counterpart to `relay.py::_coerce_pk_or_none`" - a
   documented parallel, not an accidental one.
3. `filters/base.py::_coerce_int_in_members` - coerces each `__in` filter
   member through an arbitrary `IntegerField`, with an extra defensive
   `TypeError` in its `except` tuple.

**Tried to disprove the duplication** by checking whether the three sites
differ in contract or reason-to-change, not just syntax:

- Read Django's `Field.to_python` across `IntegerField` / `AutoField` /
  `CharField` / `UUIDField` / `DecimalField` (`django/db/models/fields/__init__.py`)
  to confirm every core field wraps a `to_python` failure in `ValidationError`
  already, and that `TypeError` is never raised bare by `to_python` for these
  field types (`_coerce_int_in_members`'s extra `TypeError` catch is a
  defensive superset, not a load-bearing behavioral divergence tied to its
  filter-specific contract).
- Confirmed each site's failure-handling policy is identical: "uncoercible /
  out-of-range -> treat as 'identifies no row'" (dropped from a query, or
  mapped to a not-found/invalid sentinel) - never a raw backend
  `OverflowError`. All three sites' own docstrings state this same invariant
  in near-identical language, independently.
- Confirmed the one genuine axis of variation is **which field** to coerce
  against (a Relay type's resolved id field vs. a related model's pk vs. an
  arbitrary filtered column) - a per-caller decision, not shared knowledge -
  so the consolidation must not fold field-selection into the shared piece.
- Ran the existing live-query regression tests that exercise each site's
  overflow path end-to-end (`examples/fakeshop/test_query/test_scalars_api.py::test_filter_specimens_by_bigint_in_drops_past_64bit_members_no_overflow`
  for the filter site, `tests/mutations/test_resolvers.py::test_raw_pk_m2m_existence_check_coerces_out_of_range_pk_no_overflow`
  for the write-value site, `tests/test_relay_node_field.py::test_coerce_pk_or_none_passes_raw_string_for_non_field_node_id`
  plus the `decode_model_global_id` uncoercible-pk test for the Relay site)
  both before and after the refactor - all pass unchanged, proving behavioral
  equivalence rather than asserting it.

**Rejected candidate: consolidating the trailing `strawberry.field(resolver=...,
description=..., deprecation_reason=..., directives=...)` construction.** This
exact four-line tail appears in both `relay.py` factories, `list_field.py`,
`mutations/fields.py`, and `auth/mutations.py`. Not promoted: each occurrence
is a factory's own return statement forwarding ITS OWN same-named public
parameters to the underlying `strawberry.field(...)` call - there is no
independent rule or invariant here, only a pass-through of Strawberry's own
API surface. A shared wrapper would hide the fact that these are Strawberry
field constructions at the point each factory returns, for a four-line
"saving" that is pure boilerplate rather than repeated business logic (DRY.md:
"Do not optimize for fewer lines... A helper that obscures ownership... makes
the system less DRY").

## Opportunities

**Repeated responsibility:** "Coerce a raw literal to a Django field's Python
value via that field's own `to_python` + `run_validators`; treat an
uncoercible or out-of-range literal as a sentinel failure, never let it reach
the ORM as a raw backend crash."

**Sites:**

- `relay.py::_coerce_pk_or_none` (GlobalID `node_id` -> resolved type's id field).
- `utils/write_values.py::coerce_relation_pk_or_none` (raw M2M pk -> related model's pk).
- `filters/base.py::_coerce_int_in_members` (`__in` filter member -> filtered column).

**Evidence:** All three independently reimplement the identical
`to_python`-then-`run_validators` two-step wrapped in the same
`except (ValueError, ValidationError)` (two sites) / `except (ValidationError,
ValueError, TypeError)` (the third) shape, all three motivated by the exact
same documented invariant (avoid a raw backend `OverflowError` /
`ValueError` from an uncoercible/out-of-range literal), and two of the three
docstrings already cross-reference each other as siblings before this pass -
this was known-parallel code, not coincidental similarity. They change
together: a future backend-crash class discovered against one site (e.g. a
new Django field validator behavior) is a bug in the invariant, not in a
single call site.

**Owner:** `utils/querysets.py::coerce_field_value_or_none` - the existing
neutral, cycle-safe (`django` + `..exceptions` only) substrate module every one
of the three call sites already reaches (`relay.py` imports `model_for` from
it; `write_values.py` already imported `visible_related_object` from it;
adding it to `filters/base.py` introduces no cycle, verified by import-order
inspection and a runtime import smoke test). It already hosts the sibling
"neutral safety wrapper" primitives (`reject_async_in_sync_context`,
`stringified_pks_present`, `pks_all_present`), so this is an extension of an
established pattern, not a new one.

**Consolidation:** Added `coerce_field_value_or_none(field, value) -> Any |
None` to `utils/querysets.py`, catching `(TypeError, ValueError,
ValidationError)` (the safe superset of both prior exception sets - proven
safe because Django core fields wrap `TypeError`/`ValueError` into
`ValidationError` before it escapes `to_python`, so widening the tuple changes
no site's observable behavior). Each of the three sites now delegates to it,
keeping its own field-selection logic (which is the genuine per-caller
variation) at the call site:

- `relay.py::_coerce_pk_or_none` selects `model._meta.pk` or
  `model._meta.get_field(id_attr)` then calls the primitive.
- `utils/write_values.py::coerce_relation_pk_or_none` selects
  `related_model._meta.pk` then calls the primitive (now a one-line body).
- `filters/base.py::_coerce_int_in_members` calls the primitive per element and
  drops `None` results (the stale docstring cross-reference to
  `mutations/resolvers.py::_coerce_relation_pk_or_none` - a name that moved to
  `utils/write_values.py` behind a compatibility alias - was corrected to name
  the real owner while doing this).

**Proof:** New tests in `tests/utils/test_querysets.py`
(`test_coerce_field_value_or_none_returns_coerced_value`,
`test_coerce_field_value_or_none_drops_non_numeric_literal`,
`test_coerce_field_value_or_none_drops_out_of_range_literal`) pin the shared
primitive directly (success, non-numeric, and out-of-range-via-`run_validators`
branches). The pre-existing behavioral tests at all three call sites
(`tests/test_relay_node_field.py`, `tests/mutations/test_resolvers.py`'s
raw-pk-M2M-overflow test, `examples/fakeshop/test_query/test_scalars_api.py`'s
BigInt-`in`-overflow test) were run unchanged after the refactor and still
pass, proving the consolidation preserves every site's observable behavior.

**Risks / non-goals:** Field selection (which field, and how it is resolved -
`resolve_id_attr()` indirection vs. a direct `_meta.pk` vs. an arbitrary
filter-bound column) stays distinct at each call site; this was never
duplicated and is not folded into the shared primitive. The widened exception
tuple is a proven-safe superset, not a behavior change - documented in the
primitive's own docstring so a future reader does not mistake it for
accidental scope creep.

## Judgment

One real, evidence-backed duplication: a three-site "safe field coercion"
primitive that had already partially self-documented its own parallels.
Consolidated at the existing neutral substrate owner (`utils/querysets.py`)
with the field-selection variation correctly left at each call site. Every
other traced concept in `relay.py` (the target-guard delegation, the
write-side `GlobalIDDecode` decode primitive, the batch-reassembly `_interleave`
shape, the `strawberry.field(...)` construction tail) was either already a
correctly single-sourced owner or a rejected candidate with no independent
rule to extract.

## Implementation (Worker 1)

**Owner chosen:** `utils/querysets.py::coerce_field_value_or_none` (new
function; module docstring updated to name the new responsibility).

**Migrated sites:**

- `django_strawberry_framework/relay.py::_coerce_pk_or_none` - delegates;
  docstring trimmed to the field-selection rationale, generic coercion
  mechanics moved to the shared primitive's docstring; dropped the
  now-unused `ValidationError` import.
- `django_strawberry_framework/utils/write_values.py::coerce_relation_pk_or_none` -
  delegates (one-line body); dropped the now-unused `ValidationError` import.
- `django_strawberry_framework/filters/base.py::_coerce_int_in_members` -
  delegates per element; corrected the stale
  `mutations/resolvers.py::_coerce_relation_pk_or_none` cross-reference to name
  the real owner (`utils/write_values.py`) and the new shared primitive.

**Tests added:** `tests/utils/test_querysets.py` - three new focused tests on
`coerce_field_value_or_none` (success / non-numeric / out-of-range), plus a
module-docstring note pointing at the through-schema coverage that already
exercises the consolidated behavior at each call site.

**Behavior kept separate:** field selection at each call site (documented
above); the `filters/base.py` `GlobalIDMultipleChoiceFilter` region in this
same file's diff is unrelated concurrent maintainer work already in flight at
the cycle baseline and was left untouched.

**Validation:** `uv run pytest tests/utils/test_querysets.py
tests/utils/test_write_values.py tests/test_relay_node_field.py
tests/mutations/test_resolvers.py tests/filters/test_base.py
tests/filters/test_sets.py examples/fakeshop/test_query/test_scalars_api.py
-q` - 320 passed, 0 failed. `uv run ruff format .` and `uv run ruff check
--fix .` run repo-wide; no findings in the edited files, no unrelated files
altered (verified by diffing the edited files against the cycle baseline
before and after the repo-wide lint pass). No full `uv run pytest` (not
requested for a file-level item; deferred to the final gate).

**Rejected candidates recorded:** the `strawberry.field(...)` construction
tail (see Verification) - not promoted, no independent invariant to extract.

**Changelog:** Not touched (no maintainer authorization requested or given
for this item).

## Independent verification (Worker 2)

**Re-traced independently**, not from the artifact's narration: read the
complete `relay.py`, the new `utils/querysets.py::coerce_field_value_or_none`,
both migrated call sites (`write_values.py::coerce_relation_pk_or_none`,
`filters/base.py::_coerce_int_in_members`), and grepped the whole package for
`to_python(` / `run_validators` to independently rebuild the candidate list
before reading Worker 1's own search. Found the same three sites and no
fourth.

**Challenged the shared-contract claim on all three axes named in the
assignment:**

- *Exception policy* - read Django's `Field.to_python` for `IntegerField`,
  `AutoField`/`BigAutoField`, `UUIDField`, `CharField`, `DecimalField` in the
  installed Django source; every one wraps its `to_python` failure in
  `ValidationError` before it escapes, so the widened `(TypeError, ValueError,
  ValidationError)` tuple is a proven no-op superset, not a behavior change,
  confirmed with a scratch probe (below) exercising types beyond the three
  production call sites' own field types (`UUIDField`, `DecimalField`,
  `CharField(max_length=3)`, non-string/non-numeric literals like a `dict` and
  a `list`) - every case returned `None` cleanly, no site's `except` tuple was
  ever load-bearing for a case the others' narrower tuple would have crashed
  on.
- *Sentinel semantics* - traced `None` at all three sites to its caller-side
  meaning: `relay.py` maps it to `null` (single) / a positional `null` hole
  (batch) with no query issued; `write_values.py::coerce_relation_pk_or_none`
  excludes the pk from the existence query, landing on the same
  `relation_field_error` a genuinely missing pk gets; `filters/base.py`
  drops the member from the `kept` list before the `__in` predicate is built.
  All three independently converge on "identifies no row," never a raised
  exception at the call site - genuinely one sentinel contract, not three
  coincidentally-`None`-shaped ones.
- *Field selection* - independently confirmed this stays a real per-caller
  axis, not folded away: `relay.py` calls
  `model._meta.pk` OR `model._meta.get_field(id_attr)` (a Relay-typed field
  can name a non-pk column); `write_values.py` calls
  `related_model._meta.pk` unconditionally (no Relay-Node seam on a raw-pk
  relation); `filters/base.py` receives an arbitrary already-resolved
  `model_field` from `get_model_field` (the filtered column, never a pk).
  None of the three field-selection bodies were touched or generalized -
  verified by re-reading each caller's surrounding lines, not just the
  changed 1-3 line bodies.

**Confirmed migration completeness:** grepped the full package (not just the
scoped diff) for `run_validators` and `to_python(` and found exactly the new
primitive's own body plus doc-comment cross-references in the three migrated
sites - no fourth production copy, no site still hand-rolling the pair.
`mutations/resolvers.py::_coerce_relation_pk_or_none` is confirmed as a
pre-existing (pre-dating this pass) compatibility alias for the promoted
`write_values.coerce_relation_pk_or_none`, not a second body - it is a plain
name binding (`_coerce_relation_pk_or_none = coerce_relation_pk_or_none`), so
there is nothing left to migrate there.

**Checked one adjacent near-miss the artifact did not name and confirmed it
is correctly NOT folded in:** `keyset.py::_deserialize_cursor_value` also
calls `field.to_python(raw)` inside a `try`/`except (TypeError,
ValidationError, ValueError)`. Read it closely: it additionally
round-trip-validates via `serialize_cursor_value` and, on any failure
(coercion OR round-trip mismatch), *raises* a `GraphQLError` naming the
argument as malformed - never a silent `None`/drop sentinel, and no
field-selection axis at all (the cursor column is already fixed by the
connection's own ordering). Different sentinel semantics (raise vs. return
`None`) and a different responsibility (tamper/drift detection, not
"safe-or-nothing" coercion) - correctly outside the three-site consolidation,
and calling this out here so it is not mistaken for a missed fourth site in a
future pass.

**Re-challenged the rejected `strawberry.field(...)` tail candidate**
independently: grepped every `strawberry.field(\n        resolver=` shaped
return across the package and found the identical four-line tail in
`relay.py` (both factories), `list_field.py`, `mutations/fields.py`, and
`auth/mutations.py` - five occurrences, matching the artifact's count. Agree
with the rejection: each is a factory forwarding its OWN identically-named
public keyword parameters to Strawberry's own field constructor at its own
return statement; there is no independent rule being repeated, only
API-surface pass-through, and DRY.md's "do not optimize for fewer lines"
ground rule directly covers this. No stronger consolidation candidate found
on independent search either (e.g., a `functools.partial` or decorator
wrapper would hide the Strawberry construction at each factory's actual
return site for a four-line saving).

**Confirmed the concurrent `filters/base.py` empty-list work was not
absorbed or clobbered:** the scoped diff (baseline -> working tree) touches
only the `_coerce_int_in_members` body and the new import; a separate
`git diff <baseline> HEAD` vs. `git diff HEAD` split showed the
`GlobalIDMultipleChoiceFilter` region carries offsetting changes across
those two ranges that net to a literal zero diff against the item baseline
(`git diff <baseline> -- filters/base.py | grep GlobalIDMultipleChoiceFilter`
returns nothing) - i.e. that region is byte-identical to the item baseline in
the current working tree, so Worker 1 correctly treated it as out of scope
and there is nothing of that in-flight work to have absorbed.

**Verified the owner choice:** `utils/querysets.py` is already the
`django`/`..exceptions`-only cycle-safe substrate all three call sites (or
their module) already import from (`relay.py` via `model_for`, `write_values.py`
via `visible_related_object`); `filters/base.py` gained a new import
(`..utils.querysets`) that introduces no cycle - confirmed by the module's
own docstring cycle note and a passing `uv run python -c "import
django_strawberry_framework"` smoke import. The new function sits with the
sibling neutral-wrapper primitives (`reject_async_in_sync_context`,
`stringified_pks_present`, `pks_all_present`) rather than as a new pattern.
Reading the pre-change bodies at all three sites side by side confirms the
new owner is strictly clearer than the three independently-drifting copies:
the module docstring alone now states the shared invariant once, where
previously two of three docstrings repeated the full "`to_python` does not
range-check, `run_validators` catches the range validators, avoiding a raw
`OverflowError`" explanation nearly verbatim and the third had already gone
stale (pre-change `filters/base.py` docstring pointed at
`mutations/resolvers.py::_coerce_relation_pk_or_none`, a name that had already
moved to `utils/write_values.py` - fixed in this same pass).

**Ran and extended validation:** re-ran
`tests/utils/test_querysets.py`, `tests/test_relay_node_field.py`,
`tests/mutations/test_resolvers.py`, `tests/filters/test_base.py`,
`tests/filters/test_sets.py`,
`examples/fakeshop/test_query/test_scalars_api.py -k "bigint_in or
bigint_range"` (325 + 6 passed) directly rather than trusting the artifact's
reported numbers, plus a fresh scratch probe
(`docs/dry/temp-tests/worker2-relay/probe.py`, run and removed) exercising
`coerce_field_value_or_none` against `UUIDField`, `DecimalField`,
`CharField(max_length=3)`, and non-numeric/non-string literals (`dict`,
`list`, `None`) beyond the three production call sites' own field types - all
returned the sentinel `None` cleanly, no raw exception escaped in any case.
`uv run ruff check` and `scripts/check_trailing_commas.py --check` both pass
clean on every edited file; `relay.py` and `utils/write_values.py` no longer
import `ValidationError` and grepping confirms no residual unused import.

**Status: verified**

Plan item `relay.py` checked in `docs/dry/dry-0_0_13.md`.
