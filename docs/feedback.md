# Review feedback — `docs/spec-028-orders-0_0_8.md` (revision 2)

Re-reviewed against the rev2 changeset (rev2 added ~100 lines on top of
rev1 across the revision-history block + targeted edits in every prior
finding's home Decision). Verified each rev1 finding's resolution
against the actual code on disk where applicable. The spec is now
substantively ready to ship; only one cosmetic finding (R1) and a
handful of follow-through misses remain.

Line citations refer to `docs/spec-028-orders-0_0_8.md` revision 2
unless stated otherwise.

---

## Rev1 findings — resolution audit

Every finding from the rev1 review was addressed in rev2. Spot-checked
each fix against the spec body and against the codebase where the spec
claims to cite shipped behavior. Status notation: ✓ resolved cleanly,
~ resolved with a residual follow-through (broken out in the next
section), ✗ regressed.

| Rev1 ID | Status | Where in rev2 |
| --- | --- | --- |
| B1 — subpass order does not match shipped filter code | ✓ | Decision 6 (lines 559–580); Slice 1 (line 90); DoD item 10 (line 1096). Now reads `bind → expand → orphan → materialize`, with explicit "shipped code is the authoritative shape, NOT spec-027 rev8 H1 as written." Verified against `finalizer.py:495–504` docstring. |
| B2 — `except ImportError: return` reintroduces M-core-4 footgun | ✓ | Decision 9 code block (lines 706–717). Both new blocks use `pass` + `else:`; inline comment cites M-core-4 by name. |
| B3 — `_types_by_model` / `_primary_types` are phantom field names | ✓ | Decision 9 code block (lines 671–678). Verbatim copy of `registry.py:43–50`'s actual `_types`, `_primaries`, `_models`, `_enums`, `_definitions`, `_pending`, `_finalized` fields. Inline comment notes this is per B3. |
| H1 — `apply(...)` dispatcher is dead weight | ✓ | Decision 2 sets.py bullet (line 377); Decision 8 sync/async block (line 624); Implementation plan table row 1 (line 919); DoD item 4 (line 1090); KANBAN past-tense body (line 1036). Dropped consistently across the spec. |
| H2 — optimizer projection claim unverified | ✓ | Glossary refs (line 64) carries the retraction with the `grep`-verified citation; Decision 8 step 8 (line 618) restates as "selection-tree-derived only, does not inspect `queryset.query.order_by`"; the `test_library_books_order_preserves_optimizer_cooperation` narrative (line 993) names what the test actually pins. |
| H3 — `__all__` cookbook parity unverified | ✓ | Decision 3 (line 419) carries the verifying citation to `~/projects/django-graphene-filters/django_graphene_filters/orderset.py:271`. The reviewer's claim of divergence is now explicitly named as incorrect — keeps the rev1 disagreement transparent in the audit trail. |
| H4 — position-side-channel leak unnamed | ✓ | Decision 8 step 4 (line 614) names the leak explicitly, argues acceptance for `0.0.8`, points to the `check_*_permission` gate as consumer defense, and defers leak-closing to `0.0.9`. Slice 5 GLOSSARY bullets carry the warning forward. |
| M1 — "7-step pipeline" off-by-one | ~ | Decision 8 body (line 609) corrected to "8-step." Justification list at line 635 still says "The seven-step pipeline reflects this simplification." See R1 below. |
| M2 — flat-shorthand path no live test | ✓ | `test_library_books_order_by_flat_shorthand_path` added (line 998). |
| M3 — `INPUTS_MODULE_PATH` constant + `_input_type_name_for` helper missing | ✓ | Decision 2 inputs.py bullet (line 379) hoists both symbols with citations to the filter side's `filters/inputs.py:53,183`. |
| M4 — `Ordering.resolve()` example missing `OrderBy` import | ✓ | Spec example body (lines 509–526) adds the local `from django.db.models.expressions import OrderBy` import + a multi-line comment explaining `None` vs `True` sentinel semantics. |
| M5 — reverse-FK fixture seeding fragile | ✓ | `test_library_branches_order_by_reverse_fk_relation` rewritten (line 990) to assert the denormalized multiplicity explicitly — multi-shelf Branch seeded; `RelatedOrder` GLOSSARY entry will carry the warning per Slice 5. |
| M6 — permission test single-named, not split | ✓ | Split into `test_order_check_permission_denies_for_active_field` (line 995) and `test_order_check_permission_quiet_for_inactive_field` (line 996). |
| M7 — empty-list / null-direction no-op cases untested | ✓ | `test_order_empty_list_passes_through` (line 999) and `test_order_null_direction_skips_field` (line 1000). |
| M8 — off-Meta-fields ordering intentional but untested | ✓ | `test_order_accepts_field_not_in_djangotype_meta_fields` (line 964) added under `tests/orders/test_sets.py`. |
| M9 — `_helper_referenced_ordersets` location ambiguous | ✓ | Decision 2 (line 380) pins it to `orders/__init__.py` with explicit rationale; Decision 9 (line 697–717) confirms two separate clear blocks per registry-clear. |
| M10 — duplicated KANBAN / CHANGELOG narrative | ✓ | CHANGELOG bullet (line 1043) now reads "see the KANBAN past-tense body above" with a one-line headline. |
| N1 — stale spec link slugs | ✓ | Renumbered: `[spec-027]`, `[spec-020]`, `[spec-018]`, `[spec-015]`, `[spec-025]`, `[spec-028]`. Link defs updated. |
| N2 — `Verified in upstream` block unquoted | ✓ | Decision 4 (lines 443–452) inlines the verbatim strawberry-django ordering symbols. |
| N3 — `_validate_orderset_class` import-cycle requirement | ✓ | DoD item 9 (line 1095) spells out the local in-function `from ..orders.sets import OrderSet` requirement with cycle-explanation. |
| N4 — `tests/orders/` file count inconsistent | ✓ | Decision 2 (line 388) and Decision 13 (line 900) both say "7 files total"; DoD item 11 (line 1097) consistent. |
| N5 — literal `YYYY-MM-DD` placeholder | ✓ | `<DATE>` used throughout Slice 5, Decision 10, DoD item 24. |
| N6 — L5 contingency check as honor-system | ✓ | Decision 10 (line 760–762) names `grep -E 'WIP-ALPHA-[0-9]+-0\.0\.8' KANBAN.md`. |
| N7 — `apply_async` blocking-hook caveat unstated | ✓ | Decision 8 (line 626) carries the mirrored caveat plus a recommended pattern. |
| N8 — proxy / MTI `__all__` semantics unstated | ✓ | Decision 3 (lines 421–425) covers proxy, MTI child, and abstract-model cases. |
| N9 — `noqa: A002` future-convention note | ✓ | Spec body (line 284) carries the convention note explicitly for `aggregate:` / `order:` / `search:` / `input:` future arguments. |
| O1 — `Meta.distinct` shape preview | ✓ | Decision 12 (line 891). |
| O2 — Layer 6 escape-hatch preview | ✓ | Decision 12 (line 892). Explicitly names "the `0.0.8` shape does not foreclose the factory path." |

All 27 rev1 findings closed cleanly except M1 (residual line 635 — see
R1 below). No regressions.

---

## Outstanding follow-throughs

These are small misses from the rev2 sweep. Each is a one- or two-word
edit; none affect the architecture or the implementation plan, but they
will leave the spec internally inconsistent if left.

### R1. M1's "seven-step pipeline" reference at line 635 was missed

Decision 8 body (line 609) correctly says "The 8-step pipeline" after
M1's fix. But the Justification list ten lines later (line 635) still
reads:

> "no related-queryset filter-scope constraint (no `RelatedOrder(queryset=...)`
> parameter — the cookbook's `RelatedOrder` accepts only `orderset` and
> `field_name`). **The seven-step pipeline reflects this simplification.**"

Change to "The eight-step pipeline" so the count matches the numbered
list immediately above it. Same Decision, same sentence, one word.

### R2. "Exactly 10 new live HTTP tests" header at line 985 should read 13

The Test plan's `### examples/fakeshop/test_query/test_library_api.py
(extend)` subsection header at line 985 still reads:

> "Coverage MUST be earned here per the `docs/TREE.md` coverage-priority
> rule. **Exactly 10 new live HTTP tests**:"

Then the body lists 13 tests, line 1002 says "All 13 new live HTTP
tests," DoD item 15 says "exactly 13," the Slice-4 narrative at line 94
says "exactly 13," and the KANBAN past-tense body at line 1036 says
"exactly 13." Update the section header to "**Exactly 13 new live HTTP
tests**" so the count is consistent across the spec.

### R3. Implementation plan table row 4 still says `10` for the Slice 4 new-test count

The Implementation plan table at line 922 has:

| Slice | … | New tests | … |
| --- | --- | --- | --- |
| 4 — Live HTTP coverage in fakeshop | … | **10** (scalar ASC / scalar DESC_NULLS_LAST / forward-FK relation / reverse-FK relation / M2M absolute-import-path RelatedOrder / filter + order composition / optimizer cooperation under `assertNumQueries` / root `get_queryset` honoring / `check_<field>_permission` denial / multi-field priority via list-element ordering) | … |

The count is `10` and the inline test-name enumeration is the rev1 set
of 10. Should be `13` with the inline list extended to include the
three new tests:

- flat-shorthand path (`shelfCode`),
- split-pair active-input-only permission (`denies_for_active_field` +
  `quiet_for_inactive_field` — two tests),
- empty-list + null-direction no-op (`empty_list_passes_through` +
  `null_direction_skips_field` — two tests).

(Note that the split-pair counts as one entry in the rev1 capability
list but as two tests in the count; same for empty/null. 10 + 1 split
+ 1 path + 1 doubled no-op group = 13.)

### R4. Decision 13's high-level capability list at line 898 still enumerates the rev1 10

Decision 13 (line 898):

> "Live HTTP tests (Slice 4) land in `examples/fakeshop/test_query/test_library_api.py`
> and cover: scalar-field ascending order, scalar-field descending order
> with NULLS positioning, forward-FK relation order, reverse-FK relation
> order, M2M relation order through the absolute-import-path `RelatedOrder`
> resolution, composition with the shipped Filtering subsystem,
> composition with the optimizer (…), root `get_queryset` honoring,
> `check_*_permission` denial gate, and multi-field priority ordering."

Add three to the capability list to match the 13 live tests Slice 4
ships: flat-shorthand path, split-pair active-input-only permission
(denies-for-active / quiet-for-inactive), and the two no-op cases
(empty list / null direction). Decision 13 is the conceptual summary of
the live-HTTP test plan; readers cross-referencing it should see the
same shape they'll find in Slice 4 and the Test plan.

---

## New observations introduced by rev2

These are observations on content rev2 *added*, not residuals of rev1
findings. None are blocking; the first two are worth a one-sentence
edit; the third is a YAGNI flag on a forward statement.

### N-new-1. Decision 8 step 4's leak-closing deferral binds two orthogonal 0.0.9 items

The expanded step 4 (line 614) concludes:

> "**Closing this side channel** would require re-deriving every nested
> `RelatedOrder` branch's child visibility queryset and rewriting the
> parent JOIN's `ORDER BY` to operate only on the visibility-scoped
> subset… That work is **deferred** — likely to land alongside the same
> `0.0.9` cohort that ships connection-aware optimizer planning."

The two work items — (a) re-deriving child visibility querysets for
nested `RelatedOrder` ORDER BY, and (b) connection-aware optimizer
planning (per [Out of scope][] line 1075) — are orthogonal. Pinning them
to the same cohort risks future readers thinking the deferral is
already scheduled when it isn't. Recommend rephrasing as "deferred —
likely to a sibling `0.0.9` ordering-permissions card; the connection-
field cohort is the natural integration point but the leak-closing work
is independent of connection-field design."

### N-new-2. Decision 2's rationale for `_helper_referenced_ordersets` placement is slightly hand-wavy

Decision 2 (line 380) explains why the orphan-tracking ledger lives in
`orders/__init__.py` rather than `orders/inputs.py`:

> "placing the ledger in `inputs.py` would force `__init__.py` to import
> from `inputs.py` to mutate it, adding an unnecessary import dependency
> between the two modules."

`orders/__init__.py` already imports `INPUTS_MODULE_PATH` and
`_input_type_name_for` from `orders/inputs.py` per Decision 2's own
inputs.py bullet (line 379) — the import dependency exists either way.
The real reason for the placement is that the *writer* of the ledger
(`order_input_type`) lives in `__init__.py`, so co-locating the ledger
with its writer is a locality argument, not an import-dependency
argument. Recommend rephrasing as "co-located with its only writer
(`order_input_type`) in `__init__.py`, matching the filter side's
arrangement at `filters/__init__.py:48`." Same outcome, cleaner
rationale.

### N-new-3. Decision 12 forward-compat O1 claim about `DEFERRED_META_KEYS` could go stale

Decision 12's forward-compat preview O1 (line 891) says:

> "neither is in `DEFERRED_META_KEYS` today, and the validator's typo
> guard at `_validate_meta` time would reject either as an unknown key
> — that rejection is fine for `0.0.8`."

True today (`base.py:48-55` carries only `orderset_class`,
`aggregate_class`, `fields_class`, `search_fields` in
`DEFERRED_META_KEYS`). But if a future maintainer adds `distinct` or
`distinct_class` to `DEFERRED_META_KEYS` as a no-op pre-promotion step
between rev2's writing and the actual `0.0.9` DISTINCT-ON design, this
statement goes stale silently. Worth a one-line caveat — "this state is
accurate as of `0.0.8`; the `0.0.9` design may add either key to
`DEFERRED_META_KEYS` before its corresponding subsystem ships, per the
deferred-key promotion-gate convention" — so a future reader cross-
checking against the live `DEFERRED_META_KEYS` value sees the disclaimer
before they panic.

---

## Summary

Rev2 closes every rev1 finding — including the three Blocking ones
(B1–B3), where the spec is now consistent with the *shipped* filter
binding at `finalizer.py:495–504` rather than spec-027 rev8's H1
prescription. The Decision-history narrative at the top of the spec
(lines 11–35) gives a clear changelog with line citations so a reader
auditing each finding can verify in one pass.

Remaining work is sweep-residual only: R1–R4 (one-word edits to bring
the "8-step pipeline" and "13 live tests" counts consistent across the
spec) and three observations (N-new-1, N-new-2, N-new-3) that are
phrasing tweaks rather than substantive design concerns. None of them
block implementation.

The spec is ready to ship after R1–R4 are applied. The three N-new
observations can fold into a future review pass or stay as-is.
