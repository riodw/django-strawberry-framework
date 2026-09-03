# Build: Review round 1 — citation residue

Spec reference: `docs/SPECS/spec-038-form_mutations-0_0_12.md` (Decision 7, lines 1080-1365; Decision 8, lines 1366-1607; `## Edge cases and constraints`, lines 1827-1936). Round input: `docs/builder/build-038-form_mutations-0_0_12.md` `## Review round 1 — citation residue`, lines 387-452.
Status: final-accepted

## Plan (Worker 1)

### The round in one paragraph

Slice 2 retired spec-038's `P1` / `P2` / `P3` emphasis labels; the spec carries **0** now.
Comments and docstrings in shipped `.py` source still cite them, so a reader following
`spec-038 Decision 7 P2` finds no such label. `AGENTS.md` rule 27 names the rule broken —
cite a contract by **content**, never by ordinal, because a heading or label rewrite strands
every ordinal. The contract question (which side is wrong) was settled before dispatch: Slice 2
stands, the source changes. This plan re-derives the population, partitions it, and fixes
**32 sites across 8 files** by dropping the sub-ordinal and, where the ordinal was carrying
meaning, restating the contract in one clause from the code.

### Population, re-derived

Worker 0's numbers are treated as observations. Every count below was measured by a heredoc
sweep, printed with its population size, and asserted.

**Instrument.** One regex over the whole `.py` corpus: `\bP[0-9]+(?:[.\-][0-9A-Za-z]+)?\b`.
Occurrences counted, never matching lines — two labels on one line read as one otherwise.
The suffix alternation is what widens the vocabulary past Worker 0's `\bP[123]\b`: without it
`P4`, `P1.6`, `P2-3`, `P1-B`, `P2.7` and `P1.5` are invisible, and one of those is a whole
vocabulary (`spec-040`'s) Worker 0's grep structurally could not see.

| Sweep | Population | Occurrences | Lines |
| --- | --- | --- | --- |
| `django_strawberry_framework/**/*.py` | 111 files | **43** | 42 |
| `tests/**/*.py` + `examples/**/*.py` + `scripts/**/*.py` | 324 files | **29** | 29 |
| whole `.py` corpus | **435 files** | **72** | 71 |
| `docs/**/spec-*.md` | 102 files | 488 | — |
| all tracked `*.md` (`.venv` excluded) | 223 files | 623 | — |

**Reconciliation with Worker 0.** Worker 0 reported 41 package lines over 111 files. Dropping
the one `P4` line (`auth/mutations.py::_make_permission_holder`, spec-040's vocabulary) from my
42 leaves exactly 41 — so Worker 0's figure is right *for the vocabulary its grep could see*,
and the difference is instrument reach, not arithmetic. Worker 0's 11 explicitly-qualified
`spec-038 … P<N>` lines also reproduce exactly. Two things it did not reach:

1. **The example project.** Worker 0's count covered `django_strawberry_framework/` only.
   `examples/fakeshop/` — which is spec-038 Decision 12's own live coverage surface — carries
   **11 more in-scope sites** across `apps/products/forms.py`, `apps/products/schema.py` and
   `test_query/test_products_api.py`. A false citation in a test docstring is the same defect.
2. **Two of the 11 "qualified" citations are line-wrapped**, so a per-line grep classifies them
   as unqualified: `forms/inputs.py` lines 94-95 (`(spec-038` / `Decision 7 P2)`) and lines
   179-180 (`(spec-038 Decision 7` / `P2 - the kwarg-requiring-form fix)`). Worker 0 cited
   `forms/inputs.py #"the kwarg-requiring-form fix"` as an *example of the unqualified class*;
   it is in fact qualified, one line up. This is the anchor-rots-by-line-wrap failure, and the
   sweep must therefore be occurrence-based over whole file text, never line-based.

**Negative / positive controls.** Each sweep asserted `occurrences > 0` so a broken instrument
cannot read as a clean repo. The zero-result sweeps carry live controls:

- bare `#<n>` review-finding residue in spec-038's surface (46 files: `forms/`, `mutations/`,
  `apps/products/`, `test_products_api.py`, `tests/forms/`) → **0 occurrences**. Control: the
  same regex over `django_strawberry_framework/_django_patches.py` → **3** (Django Trac
  `#37064`), so the instrument fires.
- the combined `P<n>#<m>` form the HEAD spec used (`P1#1`, `P2#6`, `P2#3`) → **0** in source.
- `priorit\w*\s+\d` → **0**; `\btier\s+\d` → 3, all prose about a resolution order in
  `tests/types/test_base.py`, not labels.
- lowercase `\bp[0-9]+\b` → 40, every one a local variable or a fixture string
  (`Patron.objects.create(name="p1")`). The vocabulary is closed at uppercase `P<N>` with an
  optional `.M` / `-M` suffix.

### Partition: in scope / out of scope / ambiguous-then-resolved

**In scope — spec-038's label vocabulary: 32 sites, 32 occurrences, 8 files.**

| File | Sites |
| --- | --- |
| `django_strawberry_framework/forms/converter.py` | 2 |
| `django_strawberry_framework/forms/inputs.py` | 8 |
| `django_strawberry_framework/forms/resolvers.py` | 1 |
| `django_strawberry_framework/forms/sets.py` | 9 |
| `django_strawberry_framework/mutations/sets.py` | 1 |
| `examples/fakeshop/apps/products/forms.py` | 4 |
| `examples/fakeshop/apps/products/schema.py` | 2 |
| `examples/fakeshop/test_query/test_products_api.py` | 5 |

Package subtotal 21, example subtotal 11. Arithmetic check: 43 package occurrences − 22
out-of-scope package occurrences (21 lines, one of which carries two labels) = 21. ✓

**Out of scope — another spec's live vocabulary, or not a label at all.**

| Owner | Sites | Evidence for the attribution |
| --- | --- | --- |
| `spec-039` (`P1.1` `P1.5` `P1.6` `P1.7` `P2.2` `P2.3` `P2.7`) | 13 — `forms/inputs.py` ×2, `mutations/inputs.py`, `rest_framework/inputs.py` ×3, `rest_framework/resolvers.py` ×4, `rest_framework/sets.py` ×3, `utils/inputs.py` | Every one names `spec-039` on its own line. `docs/SPECS/spec-039-serializer_mutations-0_0_13.md` still carries **113** P-label occurrences, so each citation **resolves**. Not a defect. |
| `spec-040` (`P1` `P2` `P4`) | 2 lines / 3 occurrences — `auth/mutations.py #"spec-040 D3 /"`, `mutations/fields.py #"D12 / P1 / P2"` | Both name `spec-040`; `spec-040` carries 53 P-label occurrences, so both resolve. Invisible to `\bP[123]\b` in the `P4` case. |
| `spec-033` (`P2-3`) | 2 — `optimizer/nested_planner.py` | The module cites `spec-033` eleven times and no other spec near either site. `spec-033`'s spec carries **0** P-labels, so these are **stranded** — the identical defect, another cycle's. → deferred catalog. |
| `spec-030` (`P1-B`) | 2 — `orders/sets.py`, both naming `spec-030-connection_field-0_0_9` explicitly; plus 3 more in `examples/fakeshop/test_query/test_library_api.py` | `spec-030` carries **0** P-labels. Stranded. Explicitly fenced out of this round by the plan. → deferred catalog. |
| `spec-032` (`the P1 bug` / `the P2 bug`) | 2 — `tests/test_relay_node_field.py` | The file cites `spec-032` three times and no other write-side spec; `spec-032`'s spec carries 0 P-labels (its rationale companion carries 47). Stranded. → deferred catalog. |
| unknown owner | 3 — `tests/test_lateral_pg_parity.py #"P2-4: two callers of ONE extension"`, `examples/fakeshop/apps/library/tests/test_generic_connection_sharded.py #"Pins the P1 fix"`, `examples/fakeshop/test_query/test_library_api.py #"the P0 served it 1"` | No `spec-NNN` appears anywhere in the first two files; the third's line names none. Undecodable by construction. → deferred catalog. |
| `spec-031` / `spec-030`-era `Revision <n> P<n>` | 5 — `examples/fakeshop/test_query/test_library_api.py` | Ordinal-on-ordinal (`Revision 7 P1`). Not spec-038's. → deferred catalog. |
| **not a label** | 4 — `tests/optimizer/test_predicates.py` lines 78-81, `Patron.objects.create(name="P1"…)` | Fixture data. The false-positive class a grep cannot distinguish from its target; excluded by reading, not by pattern. |

**Ambiguous, then resolved.** Nine sites carried a bare `P<N>` with no spec on the same line.
Each was resolved by reading the surrounding code and both candidate specs:

1. `forms/inputs.py #"form still has a discoverable shape, P2)"` — **spec-038.** The enclosing
   module-docstring bullet list is introduced four lines up by `#"The shape is the ``036``
   discipline adapted to forms (spec-038 Decision 7):"`, so the anchor is on the reader's path.
2. `forms/resolvers.py::_reconstruct_partial_data #"(the prior P1 fix)"` — **spec-038.** The
   same docstring cites `spec-038 Decision 8 step 4` nine lines above, and the clause's content
   (reconstruction reads the form's FULL declared field set, not the narrowed input) is
   spec-038 Decision 8's, spec lines 1463-1469. Nothing in `spec-039` states it.
3. `forms/sets.py #"discard the load-bearing P1 reverse map"` — **spec-038.** The comment block
   names `(spec-038)` three lines above and the subject is the form-input build cache's
   `(input_cls, field_specs)` value.
4. `forms/sets.py::DjangoModelFormMutation.build_input #"(the P1 reverse map)"` and
5. `forms/sets.py::DjangoFormMutation.build_input #"decode (the P1 reverse map)"` — **spec-038.**
   Both docstrings cite `(spec-038 waiver)` in the preceding sentence; the reverse map is
   spec-038 Decision 7's `InputFieldSpec` record, spec lines 1169-1200.
6. `forms/sets.py::DjangoFormMutation._validate_meta #"two-base split - P2)"` — **spec-038.**
   The enclosing bullet list cites `Decision 10` and `Decision 11` and the spec's own current
   wording of the same statement reads `#"defeating the two-base split)"` (spec line 328) —
   the ordinal already stripped by Slice 2.
7. `forms/sets.py::DjangoFormMutation._validate_meta #"(Decision 7 P2 - the fixed"` — **spec-038.**
   `Decision 7` names it; only the spec prefix is missing.
8. `forms/sets.py::DjangoFormMutation._validate_meta #"(Edge case P2)"` — **spec-038.** It cites
   a section, not a decision: spec-038 `## Edge cases and constraints` line 1879,
   `**A `ModelForm` placed on the plain `DjangoFormMutation` base.**` — an entry whose own
   ordinal Slice 2 already removed.
9. `utils/querysets.py #"(the P2 retained-state vector)"` — **spec-045, out of scope.** The site
   sits inside `_seal_or_defect`, whose neighbouring comments cite `spec-045 Decision 1` and
   `spec-045 Decision 5`; `utils/querysets.py` carries 38 `spec-045` references against one
   `spec-038`. `spec-045` still carries 4 P-label occurrences, so the citation resolves.

The eleven example-project sites needed the same grading and all resolved to spec-038:
`apps/products/forms.py` opens `#"""Consumer Django forms for the products live form-mutation
surface (spec-038)."""` and names `#"the spec's Decision-12 live matrix"`;
`apps/products/schema.py` carries four `spec-038` references; all five
`test_products_api.py` sites are form-mutation rows (`categoryId`-through-the-form,
partial-update preservation, relation visibility, multipart `Upload`, `get_form_kwargs`),
which is spec-038 Decision 12's declared live matrix and nothing else's.

### What each label meant: nothing

The HEAD spec (`git show HEAD:docs/SPECS/spec-038-form_mutations-0_0_12.md` into a scratch path
outside the repo, 185,851 bytes, 88 `P[123]` occurrences) carries **no legend** for the labels —
no `**P1**` definition line, no priority key, no `Priority` heading. They were appended emphasis
tiers on contract statements (`(P2):** the fallthrough default **raises**`,
`extra field keeps its `field.required`**, P2)`). The rationale companion certifies the same
finding independently: `#"not one of them added a clause"`. So **no in-scope replacement can
lose a WHY that only the ordinal carried** — every site's own sentence already states the
contract. That is what makes the cheapest form (drop the sub-ordinal) the true form at 12 of
the 32 sites, and it is why this is a wording change and never a contract change.

### Per-site replacement decisions

Grouped by the form of the fix. Every replacement was simulated before being written down:
each anchor asserted to occur **exactly once in its file**, and each resulting line measured
against the 99-column limit. That simulation caught three defects in my own first draft —
seven anchors that were not unique, and three replacements that pushed a line over 99 — all
corrected below. Line numbers are pin-at-write-time navigational hints only; 7 of the 8 target
files are baseline-dirty from a concurrent session, so **verify the anchor, not the line
number** (`AGENTS.md` rule 27 is exactly why no citation here is a `path:NN`).

**Group A — drop the sub-ordinal; `spec-038 Decision 7` already locates the contract (12 sites).**
`START.md` "Style Rio cares about" keeps spec decision pointers as permitted provenance, and
Decision 7's heading survived Slice 2 unchanged (`### Decision 7 — Form-field → Strawberry
input mapping: the form is the input source of truth`), so the pointer resolves.

| Site | Anchor (unique in file) | Becomes | Spec text that makes it true |
| --- | --- | --- | --- |
| `forms/converter.py #"this module (spec-038 Decision 7 P1)."` | `this module (spec-038 Decision 7 P1).` | `this module (spec-038 Decision 7).` | Decision 7, spec 1181-1185: the four `kind` constants are defined in `utils/inputs.py` and re-exported by `forms/converter.py`, "which owns the constants and not the record type" |
| `forms/converter.py::convert_form_field` | `` ``String`` - spec-038 Decision 7 P2): `` | `` ``String`` - spec-038 Decision 7): `` | Decision 7, spec 1155: `**The fail-loud contract requires NOT registering a base-`forms.Field` catch-all.**` |
| `forms/inputs.py #"# Decision 7 P2). The bind keys on it"` | `# Decision 7 P2). The bind keys on it` | `# Decision 7). The bind keys on it` | Decision 7, spec 1262-1265: the operation-kind component is the model verb "or the fixed sentinel **`\"form\"`**" |
| `forms/inputs.py::resolve_effective_form_fields` | `` ``base_fields`` (spec-038 Decision 7 P3): `` | `` ``base_fields`` (spec-038 Decision 7): `` | Decision 7, spec 1291-1302: `**`Meta.fields` / `Meta.exclude` are normalized + fail-loud against …`, including the empty-effective-set raise |
| `forms/inputs.py::form_input_type_name` | `form shape (spec-038 Decision 7 P1).` | `form shape (spec-038 Decision 7).` | Decision 7, spec 1251-1284: `**Shape identity + naming + collision (the `036` discipline).**` and the deterministic shape-derived narrowed name |
| `forms/inputs.py::build_form_input_class` | `(spec-038 Decision 7 P2 - so a required` | `(spec-038 Decision 7 - so a required` | Decision 7, spec 1239-1249: a non-model extra form field "keeps its declared `field.required`", so a required extra "stays required on update" |
| `forms/inputs.py::guard_create_required_fields` | `(spec-038 Decision 7 P2, the create-required guard)` | `(spec-038 Decision 7, the create-required guard)` | Decision 7, spec 1303-1316: the create-narrowing raise plus the `get_form_kwargs` / `get_form` waiver |
| `forms/inputs.py::build_form_inputs` | `guard (spec-038 Decision 7 P2).** A bound` | `guard (spec-038 Decision 7).** A bound` | same, spec 1303 |
| `forms/sets.py::_cached_build_form_input` | `` ``guard_required`` - spec-038 Decision 7 P2). `` | `` ``guard_required`` - spec-038 Decision 7). `` | Decision 7, spec 1303-1327: the guard and the one waiver it is keyed on. The guard-before-cache **ordering** is an implementation invariant the comment states itself; the spec owns the guard, which is what the pointer cites |
| `forms/sets.py::_cached_build_form_input` (comment) | `input shape (spec-038 Decision 7 P2). The create` | `input shape (spec-038 Decision 7). The create` | same |
| `forms/sets.py::DjangoFormMutation._validate_meta` | `` ``form_class`` (Decision 7 P2 - the fixed `` | `` ``form_class`` (spec-038 Decision 7 - the fixed `` | Decision 7, spec 1262-1265. The spec prefix is **added**: bare `Decision N` is a repo-wide convention, but spelling it costs one token and removes the anchor-distance question |
| `mutations/sets.py::cached_build_input` | `(spec-038 Decision 7 P2 / spec-039 Decision 7)` | `(spec-038 Decision 7 / spec-039 Decision 7)` | Decision 7, spec 1303-1327. Note the `spec-039` half of this citation is already ordinal-free and resolves; only the spec-038 sub-ordinal is stranded |

**Group B — the ordinal was doing naming work; restate the contract in one clause (5 sites).**
`START.md`: "Removed attribution carried the WHY → restate as one plain clause from the code."
Here the ordinal was the only handle on "which reverse map", so the clause names it by content.

| Site | Anchor | Becomes | Ground |
| --- | --- | --- | --- |
| `forms/sets.py #"discard the load-bearing P1 reverse map."` | `discard the load-bearing P1 reverse map.` | `discard the load-bearing decode reverse map.` | This is the load-bearing invariant the brief flags: the cache value must be the `(input_cls, field_specs)` pair, because caching only `input_cls` loses the specs the decode needs (spec 1169-1200). "load-bearing" and the whole explanation stay; only the ordinal becomes content |
| `forms/sets.py::_cached_build_form_input` | `(spec-038 - the P1 decode reverse map).` | `(spec-038 Decision 7 - the decode reverse map).` | Decision 7, spec 1169: `**Per-field metadata: the `input_attr` → `form_field_name` reverse map.**` The decision pointer is **added** here — the site named the spec but not which decision |
| `forms/sets.py::DjangoModelFormMutation.build_input` | `form-field-keyed payload (the P1 reverse map).` | `form-field-keyed payload (the decode reverse map).` | same, spec 1169-1200 |
| `forms/sets.py::DjangoFormMutation._validate_meta` (comment) | `# Check ``ModelForm`` FIRST (Edge case P2):` | `# Check ``ModelForm`` FIRST (the plain-base edge case):` | `## Edge cases and constraints`, spec 1879: `**A `ModelForm` placed on the plain `DjangoFormMutation` base.**` The comment's next four lines already carry the mechanism |
| `examples/fakeshop/apps/products/forms.py::ItemModelForm` | `input writes through (the P1` / `reverse map)` (wrapped) | `input writes through (the decode` / `reverse map)` | same, spec 1169-1200 |

**Group C — the surrounding sentence already carries the content: delete the parenthetical, or
drop the bare ordinal out of a clause that already names the contract (14 sites).** Deleting
here is not weakening: in each case the same clause states the content immediately before or
after, so the ordinal was pure emphasis. Checked one by one against the source.

| Site | Anchor | Becomes | Why deletion loses nothing |
| --- | --- | --- | --- |
| `forms/inputs.py` (module docstring) | `form still has a discoverable shape, P2), not` | `form still has a discoverable shape), not` | The bullet already says "read with NO instantiation, so a kwarg-requiring form still has a discoverable shape", and the list header cites `spec-038 Decision 7` |
| `forms/inputs.py::get_form_fields` | `(spec-038 Decision 7` / `P2 - the kwarg-requiring-form fix). The overridable` (wrapped) | `(spec-038 Decision 7).` / `The overridable` | "fix" is process provenance `START.md` bars outright; the docstring's own two preceding sentences state the whole contract, and spec 1348-1358 (`**Schema-time field discovery reads `form_class.base_fields`, never an instance …**`) is what the surviving pointer resolves to |
| `forms/resolvers.py::_reconstruct_partial_data` | `from the located row (the prior P1 fix). A file field` | `from the located row. A file field` | "the prior … fix" is banned provenance twice over. The two preceding sentences state the rule, and the same docstring cites `spec-038 Decision 8 step 4` nine lines up — a second pointer here would be a near-copy (see DRY) |
| `forms/sets.py::DjangoFormMutation._validate_meta` | `two-base split - P2).` | `two-base split).` | The spec's own current wording of this statement (line 328) is `defeating the two-base split)` — identical, ordinal-free |
| `forms/sets.py::DjangoFormMutation.build_input` | `decode (the P1 reverse map).` | `decode.` | The same sentence already reads "The reverse-map `field_specs` are stashed on the mutation for the decode" — the parenthetical restated its own subject |
| `examples/.../products/forms.py` (module docstring) | `` ``categoryId``-through-the-form P1 reverse map) `` | `` ``categoryId``-through-the-form reverse map) `` | The phrase already carries its own qualifier |
| `examples/.../products/forms.py` (module docstring) | `for the P2 ``get_form_kwargs``` | `for the ``get_form_kwargs``` | The bullet already names the case in full |
| `examples/.../products/forms.py::StampedItemModelForm` | `a ``user`` kwarg (P2 case).` | `a ``user`` kwarg.` | The next paragraph opens "Models the construction-hook migration case" |
| `examples/.../products/schema.py::CreateItemWithFileViaForm` | `split (the P1 file-routing contract).` | `split (the file-routing contract).` | The same sentence says "routes the uploaded value into the form's `files=`, proving the `data=` / `files=` split" |
| `examples/.../products/schema.py::CreateStampedItemViaForm` | `injecting ``user`` (the P2 case).` | `injecting ``user``.` | The docstring body explains the whole case |
| `examples/.../test_products_api.py::test_create_item_via_form_category_id_writes_through_form_category_field` | `` the form's `category` field (P1 reverse map). `` | `` the form's `category` field. `` | The docstring body says "the form's `category` `ModelChoiceField` reverse-mapped". Deleting rather than rewording is also what keeps this line inside 99 columns |
| `examples/.../test_products_api.py::test_create_item_via_form_relation_id_for_hidden_category_is_field_error` | `RIGHT-PATH / LOAD-BEARING (P1):` | `RIGHT-PATH / LOAD-BEARING:` | The `RIGHT-PATH / LOAD-BEARING` marker is the load-bearing signal and stays; the ordinal added nothing to it |
| `examples/.../test_products_api.py::test_create_item_with_file_via_form_multipart_upload_over_http` | `` a form-backed `Upload` field (P1 file-routing). `` | `` a form-backed `Upload` field. `` | The docstring body describes the multipart transport in full. A `(the file-routing contract)` here would take the line to 111 columns, past even the 110 grace |
| `examples/.../test_products_api.py::test_create_stamped_item_via_form_get_form_kwargs_injects_user` | `drives a kwarg-requiring form (P2).` | `drives a kwarg-requiring form.` | The docstring explains the injection fully |

**Group D — one content restatement in a test comment (1 site).**

| Site | Anchor | Becomes | Ground |
| --- | --- | --- | --- |
| `examples/.../test_products_api.py::test_update_item_via_form_partial_update_preserves_category_and_description` | `(not dropped) - the P1 preservation.` | `(not dropped) - the partial-update preservation.` | Decision 8, spec 1457-1469: the resolver "reconstructs the complete bound payload from the located instance"; the spec's own slice table (line 1813) uses the phrase "partial-update preservation". **Exactly 99 columns** as written — do not lengthen it |

Group totals: A 12 + B 5 + C 14 + D 1 = **32**, matching the measured population and the 32
boxes in `### Dispatched findings checklist`. Counted from the table rows after writing them,
not asserted alongside them.

### DRY analysis

**Helper inventory checked.** Refreshed for the **whole package** this pass —
`docs/shadow/helper-inventory.md`, 2,011 lines over all 111 `django_strawberry_framework/*.py`
modules, generated by the `worker-1.md` heredoc. Shapes searched: `citation`, `label`,
`ordinal`, `provenance`, `spec_ref`, `specref`. Relevant candidates: **none** for this round's
work — the hits (`_safe_transport_label`, `_consumer_converter_label`,
`FilterGenerationProvenance`) are runtime error-message and filter-provenance helpers, unrelated
to source-comment citations. This round adds **no logic at all**, so no helper is proposed and
none is needed.

**Existing patterns reused.** The single reusable pattern is the spec's own already-swept
wording. Slice 2 rewrote each of these contract statements once, ordinal-free
(`docs/SPECS/spec-038-form_mutations-0_0_12.md` lines 328, 1155, 1169, 1239, 1251, 1291, 1303,
1348, 1879), and every replacement above quotes or tracks that wording rather than inventing a
second phrasing. Reusing the spec's spelling is what stops the source and the spec drifting
apart a second time.

**Duplication risk this round would introduce, and how the plan prevents it.** Real and
specific: four sites name the same object with four different phrasings
(`the load-bearing P1 reverse map`, `the P1 decode reverse map`, `the P1 reverse map` ×2), and
two more name file routing two ways. A per-site fix by six independent judgements produces six
near-copies. Two wordings are therefore **fixed here, not left to the builder**:

- **the reverse map → `the decode reverse map`**, at `forms/sets.py #"discard the load-bearing"`,
  `forms/sets.py::_cached_build_form_input`, `forms/sets.py::DjangoModelFormMutation.build_input`
  and `examples/.../products/forms.py::ItemModelForm`. Two sites are exceptions with a stated
  reason: `forms/sets.py::DjangoFormMutation.build_input` deletes the parenthetical instead,
  because the host sentence already says "for the decode" and repeating "decode" reads badly;
  and `products/forms.py`'s module-docstring bullet keeps its own qualifier
  (`the ``categoryId``-through-the-form reverse map`), which is a different phrase, not a
  near-copy.
- **file routing → `the file-routing contract`**, used once at
  `products/schema.py::CreateItemWithFileViaForm`. The `test_products_api.py` site deletes
  instead, for the column budget; one live wording, not two.
- **the decision pointer → `spec-038 Decision 7`**, one spelling at all 12 Group A sites plus
  the two Group B sites that gain it. That single spelling *is* the DRY answer: twelve
  hand-rolled variants is the failure mode.

**Existence challenge.** Worth stating, since Worker 3 owns it: the alternative to fixing 32
comments is deleting them. Rejected — these comments carry the mechanism (the guard-before-cache
ordering, the reverse-map rationale, the `ModelForm`-checked-first reason), which is exactly the
implementation-relevant "why" `BUILD.md` `## Spec rationale extraction` says must stay in reach
of the code. The ordinal is the only thing that has to go.

### Implementation steps

Comment and docstring text only. No executable line is touched.

1. **Copy all 8 target files to a scratch path outside the repo before editing anything** —
   `/private/tmp/claude-501/-Users-riordenweber-projects-django-strawberry-framework/<session>/scratchpad/pristine/`,
   named by the path with `/` → `_`. These pristine copies are the reference for the inverse
   proof in `### Failability proofs`. A `git show HEAD:` reference will **not** work: 7 of the 8
   files are baseline-dirty with a concurrent session's executable changes, so HEAD-vs-tree
   comparison diverges for reasons that are not this round's.
2. **Assert every anchor before writing any file.** For each of the 32 anchors in the tables
   above, confirm `text.count(anchor) == 1` in its file. A partial match aborts the whole pass
   with nothing written (`START.md`: "Enumerate, never grep-count, before writing"). Every
   anchor was verified unique at plan time; a concurrent session can still have moved one, and
   that must abort rather than fuzzy-match.
3. **Apply the 32 replacements** exactly as the tables give them. Three are two-line
   (line-wrapped) edits: `forms/inputs.py::get_form_fields`, `forms/inputs.py #"# Decision 7 P2)"`
   (single-line, but its `spec-038` sits on the line above — do not "repair" that line), and
   `examples/.../products/forms.py::ItemModelForm`.
4. **Re-measure every changed line against 99 columns.** All 32 were simulated at plan time and
   fit; `test_products_api.py`'s Group D site lands at exactly 99, so re-check it specifically.
   `E501` is graced to 110 only for lines the formatter cannot break — a comment is not one.
5. **Sweep for retirement, occurrence-based.** `\bP[0-9]+(?:[.\-][0-9A-Za-z]+)?\b` over all 8
   files must go **21 → 0** for the five package files and **11 → 0** for the three example
   files; print each file's before and after count. Whole-`.py`-corpus occurrences must go
   **72 → 40** (the 40 being the out-of-scope partition above, unchanged). A sweep that prints
   nothing proves nothing — print the population size.
6. **Run the inverse AST-identity proof** (`### Failability proofs`) and record it.
7. `uv run ruff format <the 8 files>` then `uv run ruff check --fix <the same 8 files>` —
   **scoped to these files, never `.`**; the tree carries a concurrent session's work and one
   file (`tests/rest_framework/test_sets.py`) was unparseable at the integration pass, which
   fails a whole-tree ruff invocation.
8. `uv run python scripts/check_trailing_commas.py --check <the 8 files>` — it also enforces
   ASCII-only `.py` source and the line length read from `pyproject.toml`. Every replacement
   above is ASCII; confirm rather than assume.
9. `uv run python scripts/check_citations.py` — it cannot see an ordinal citation
   (`path::Symbol`-only, by its own docstring), so it is a **regression check on the `::Symbol`
   citations these edits sit beside**, not a check on this round's defect. Green here says
   nothing about the fix; say so in the build report rather than citing it as evidence.
10. `git status --short` after both ruff invocations: every modified file must be one of the 8
    and appear in `### Files touched`. Anything else is a **stop-and-report, never a revert** —
    7 of the 8 files are already dirty from a concurrent session, so tidying churn destroys
    their work.

### Test additions / updates

**No test is added or changed as a test.** Five of the 32 sites live in
`examples/fakeshop/test_query/test_products_api.py`, but every one is a docstring or comment;
no assertion, node id, parametrization, fixture, or test name changes, so no test's failability
or coverage changes. Collection is the one thing that can break (a mangled docstring is a
`SyntaxError`), so the pass runs:

- `uv run pytest examples/fakeshop/test_query/test_products_api.py --collect-only -q --no-cov` —
  collection succeeds and the node-id count is **unchanged** before and after. Record both
  counts; an equal count with no absolute number is the vacuous assertion `BUILD.md`
  `### Query-shape tests must pin the load-bearing property` warns about.
- `uv run pytest tests/forms/ --no-cov` — the package tests for the four `forms/` modules, as a
  no-op confirmation.
- `uv run pytest examples/fakeshop/test_query/test_products_api.py --no-cov` — the live rows
  whose docstrings changed.

No `--cov*` flag in any invocation; `--no-cov` is required because `pytest.ini` auto-applies
`--cov`.

### Implementation discretion items

Assessed and decided as Worker 2's:

- Whether to apply the 32 edits by hand or through one assert-all-then-write script. The
  script is safer at this count and is what step 2 describes, but the mechanism is Worker 2's.
- The scratch subdirectory name under the session scratchpad for the pristine copies.

Nothing else. The replacement wording at every one of the 32 sites is fixed by the tables above
and is **not** discretionary — six near-copies of one clause is exactly what a per-site
judgement produces, and the concurrent-cohort argument in `worker-1.md` `### DRY analysis shape`
applies to a single builder making 32 independent small calls just as much.

### Dispatched findings checklist

One box per site, quoting the citation as it currently reads. Boxes stay `- [ ]` at planning;
Worker 2 ticks only a box whose fix landed in its diff; Worker 1 audits every tick at final
verification. All 32 belong to the single cohort `citation_residue`.

- [x] `django_strawberry_framework/forms/converter.py #"this module (spec-038 Decision 7 P1)."` — module-level re-export comment; false `P1`
- [x] `django_strawberry_framework/forms/converter.py::convert_form_field #"``String`` - spec-038 Decision 7 P2):"` — fail-loud dispatch; false `P2`
- [x] `django_strawberry_framework/forms/inputs.py #"form still has a discoverable shape, P2), not"` — module docstring; bare `P2`
- [x] `django_strawberry_framework/forms/inputs.py #"# Decision 7 P2). The bind keys on it"` — `FORM` sentinel comment; false `P2`, `spec-038` wrapped onto the line above
- [x] `django_strawberry_framework/forms/inputs.py::get_form_fields #"P2 - the kwarg-requiring-form fix). The overridable"` — false `P2` plus banned "fix" provenance
- [x] `django_strawberry_framework/forms/inputs.py::resolve_effective_form_fields #"``base_fields`` (spec-038 Decision 7 P3):"` — false `P3`
- [x] `django_strawberry_framework/forms/inputs.py::form_input_type_name #"form shape (spec-038 Decision 7 P1)."` — false `P1`
- [x] `django_strawberry_framework/forms/inputs.py::build_form_input_class #"(spec-038 Decision 7 P2 - so a required"` — false `P2`
- [x] `django_strawberry_framework/forms/inputs.py::guard_create_required_fields #"(spec-038 Decision 7 P2, the create-required guard)"` — false `P2`
- [x] `django_strawberry_framework/forms/inputs.py::build_form_inputs #"guard (spec-038 Decision 7 P2).** A bound"` — false `P2`
- [x] `django_strawberry_framework/forms/resolvers.py::_reconstruct_partial_data #"from the located row (the prior P1 fix). A file field"` — bare `P1` plus banned "prior … fix" provenance
- [x] `django_strawberry_framework/forms/sets.py #"discard the load-bearing P1 reverse map."` — module-level cache comment; bare `P1` on a load-bearing invariant
- [x] `django_strawberry_framework/forms/sets.py::_cached_build_form_input #"``guard_required`` - spec-038 Decision 7 P2)."` — false `P2`
- [x] `django_strawberry_framework/forms/sets.py::_cached_build_form_input #"(spec-038 - the P1 decode reverse map)."` — spec named, decision missing, bare `P1`
- [x] `django_strawberry_framework/forms/sets.py::_cached_build_form_input #"input shape (spec-038 Decision 7 P2). The create"` — false `P2` (comment, distinct from the docstring site above)
- [x] `django_strawberry_framework/forms/sets.py::DjangoModelFormMutation.build_input #"form-field-keyed payload (the P1 reverse map)."` — bare `P1`
- [x] `django_strawberry_framework/forms/sets.py::DjangoFormMutation._validate_meta #"two-base split - P2)."` — bare `P2`
- [x] `django_strawberry_framework/forms/sets.py::DjangoFormMutation._validate_meta #"``form_class`` (Decision 7 P2 - the fixed"` — decision named, spec missing, false `P2`
- [x] `django_strawberry_framework/forms/sets.py::DjangoFormMutation._validate_meta #"# Check ``ModelForm`` FIRST (Edge case P2):"` — cites a spec section by ordinal
- [x] `django_strawberry_framework/forms/sets.py::DjangoFormMutation.build_input #"decode (the P1 reverse map)."` — bare `P1`, fully redundant parenthetical
- [x] `django_strawberry_framework/mutations/sets.py::cached_build_input #"(spec-038 Decision 7 P2 / spec-039 Decision 7)"` — false spec-038 `P2`; the spec-039 half already resolves
- [x] `examples/fakeshop/apps/products/forms.py #"``categoryId``-through-the-form P1 reverse map)"` — module docstring, Decision-12 live matrix; bare `P1`
- [x] `examples/fakeshop/apps/products/forms.py #"for the P2 ``get_form_kwargs``"` — module docstring; bare `P2`
- [x] `examples/fakeshop/apps/products/forms.py::ItemModelForm #"input writes through (the P1"` — class docstring, wrapped; bare `P1`
- [x] `examples/fakeshop/apps/products/forms.py::StampedItemModelForm #"a ``user`` kwarg (P2 case)."` — class docstring; bare `P2`
- [x] `examples/fakeshop/apps/products/schema.py::CreateItemWithFileViaForm #"split (the P1 file-routing contract)."` — bare `P1`
- [x] `examples/fakeshop/apps/products/schema.py::CreateStampedItemViaForm #"injecting ``user`` (the P2 case)."` — bare `P2`
- [x] `examples/fakeshop/test_query/test_products_api.py::test_create_item_via_form_category_id_writes_through_form_category_field #"the form's `category` field (P1 reverse map)."` — bare `P1`
- [x] `examples/fakeshop/test_query/test_products_api.py::test_update_item_via_form_partial_update_preserves_category_and_description #"(not dropped) - the P1 preservation."` — bare `P1`
- [x] `examples/fakeshop/test_query/test_products_api.py::test_create_item_via_form_relation_id_for_hidden_category_is_field_error #"RIGHT-PATH / LOAD-BEARING (P1):"` — bare `P1`
- [x] `examples/fakeshop/test_query/test_products_api.py::test_create_item_with_file_via_form_multipart_upload_over_http #"a form-backed `Upload` field (P1 file-routing)."` — bare `P1`
- [x] `examples/fakeshop/test_query/test_products_api.py::test_create_stamped_item_via_form_get_form_kwargs_injects_user #"drives a kwarg-requiring form (P2)."` — bare `P2`

Count: **32 boxes**, matching the 32-site population and the group totals (12 + 5 + 14 + 1).

### Ownership partition

**One cohort, `citation_residue`.** Every file it may write:

- `django_strawberry_framework/forms/converter.py`
- `django_strawberry_framework/forms/inputs.py`
- `django_strawberry_framework/forms/resolvers.py`
- `django_strawberry_framework/forms/sets.py`
- `django_strawberry_framework/mutations/sets.py`
- `examples/fakeshop/apps/products/forms.py`
- `examples/fakeshop/apps/products/schema.py`
- `examples/fakeshop/test_query/test_products_api.py`
- `docs/builder/bld-038-review-1-citation_residue.md` (its own artifact sections)

Nothing else. Files **explicitly not** in the partition even though they carry P-labels:
`orders/sets.py`, `optimizer/nested_planner.py`, `auth/mutations.py`, `mutations/fields.py`,
`mutations/inputs.py`, `rest_framework/*.py`, `utils/inputs.py`, `utils/querysets.py`,
`tests/test_relay_node_field.py`, `tests/test_lateral_pg_parity.py`,
`tests/optimizer/test_predicates.py`, `examples/fakeshop/test_query/test_library_api.py`,
`examples/fakeshop/apps/library/tests/test_generic_connection_sharded.py`. Every dispatched
finding appears in exactly one cohort's list, per `BUILD.md`
`### Dispatched findings checklist`.

The two spec files and the worker memory file stay **Worker 1's alone**; Worker 2 writes neither.

### Slice split: one unit

Answered in writing per `BUILD.md` `### Slice splitting`, and the answer is **do not split**.

- **New boundary count: 0.** Not a small number — zero. The round adds no guard, cap, rejection
  path, or validation branch; it edits 6 comments and 26 docstrings. The boundary-count trigger
  cannot fire.
- **Diff shape:** 32 single- or double-line replacements over 8 files, every one mechanically
  verifiable by an occurrence sweep. That is well inside sensible review.
- **What makes them one unit:** one defect class (a stranded sub-ordinal), one already-settled
  contract question, and — the load-bearing reason — **one shared wording decision**. The
  reverse-map clause spans `forms/sets.py` (three sites) and `examples/.../products/forms.py`
  and `test_products_api.py`; the file-routing clause spans `products/schema.py` and
  `test_products_api.py`. A split by vocabulary (qualified vs bare) puts four `forms/sets.py`
  sites in both halves, so the partition would not even be disjoint; a split by tree
  (package vs example) separates the two ends of both shared clauses, and concurrent cohorts
  cannot see each other's diffs. Either split manufactures the near-copies this plan exists to
  prevent.

### Failability proofs

**Ruling: no failability proof is owed, and an inverse proof is owed instead.**

`BUILD.md` `### What needs a proof, and what does not` scopes the obligation to "every new
boundary, guard, gate, or rejection path a slice introduces" and exempts doc edits and
relocated bodies. This round introduces none. The ruling is **measured, not asserted**: all 32
sites were classified by AST plus `tokenize`, giving **6 COMMENT + 26 DOCSTRING + 0 executable**,
with a positive control (`forms/sets.py` line 43, a real module-level statement) correctly
classifying as executable. So the exemption applies on evidence.

`START.md` "Instruments that lie" then imposes the inverse: "Comment/docstring-only edit owes
INVERSE proof: AST identity w/ docstrings stripped." Worker 2 runs exactly this and records the
output. The command, validated at plan time:

```shell
# Written once to a scratch path OUTSIDE the repo, e.g. $SCRATCH/ast_identity.py
uv run python - <<'PY'
import ast
import subprocess
import sys
from pathlib import Path

FILES = [
    "django_strawberry_framework/forms/converter.py",
    "django_strawberry_framework/forms/inputs.py",
    "django_strawberry_framework/forms/resolvers.py",
    "django_strawberry_framework/forms/sets.py",
    "django_strawberry_framework/mutations/sets.py",
    "examples/fakeshop/apps/products/forms.py",
    "examples/fakeshop/apps/products/schema.py",
    "examples/fakeshop/test_query/test_products_api.py",
]
PRISTINE = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/dsf-r1-pristine")


def digest(src):
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = node.body
            if body:
                first = body[0]
                if (
                    isinstance(first, ast.Expr)
                    and isinstance(first.value, ast.Constant)
                    and isinstance(first.value.value, str)
                ):
                    node.body = body[1:] or [ast.Pass()]
    return ast.dump(ast.fix_missing_locations(tree), include_attributes=False)


bad = 0
for rel in FILES:
    before = (PRISTINE / rel.replace("/", "_")).read_text()
    after = Path(rel).read_text()
    same = digest(before) == digest(after)
    bad += not same
    print(f"{'IDENTICAL' if same else 'DIVERGED '}  {rel}")
print(f"\nfiles compared: {len(FILES)}  diverged: {bad}")
sys.exit(1 if bad else 0)
PY
```

Required result: **8 IDENTICAL, diverged 0, exit 0.** A single `DIVERGED` row means an
executable line moved and is `revision-needed`.

**The instrument was controlled at plan time, and the first control did not fire.** My first
attempt mutated a string that does not exist in the file I aimed it at, so both rows printed
IDENTICAL and the control read as a pass — `START.md`: "control that didn't run ≡ one that
passed". Re-run against real anchors (asserted `count == 1` first), it behaves correctly:

| Control mutation applied to a pristine copy | Result | Reading |
| --- | --- | --- |
| `forms/converter.py`, docstring text `spec-038 Decision 7 P2` → `the fail-loud dispatch contract` | `IDENTICAL` | correct — the digest is deliberately blind to docstring text |
| `forms/sets.py`, executable `_ALLOWED_PLAIN_FORM_META_KEYS` → `_ALLOWED_PLAIN_FORM_META_KEYS_X` | `DIVERGED`, exit 1 | correct — the digest catches any executable change |

Worker 2 must re-run **both** control rows against its own pristine copies before trusting the
real run, and record them. The digest is blind to docstrings by design, so an unbroken control
is indistinguishable from an instrument that compares nothing. The repository files were
untouched by the plan-time controls (verified: `git diff` on `forms/converter.py` empty, both
mutated anchors still present in the working tree at their original counts).

### Hot-path budget

**Not applicable; declared not hot-path.** Ground: the round changes 6 comments and 26
docstrings and 0 executable lines, proved by the AST/tokenize classification above. Nothing
runs per request, per resolver, per row, per connection, or per outbound message, because
nothing runs at all. Docstrings do occupy interpreter memory as `__doc__`, and the net change
there is a **reduction** (every replacement is the same length or shorter but for four sites,
all under 30 characters). `worker-1.md`: "Judge hot-path by what the code runs inside, not by
diff size" — here the code runs nothing new inside anything.

### Floor verification

**Scope: `none`.** Ground: `BUILD.md` `### When it is required` scopes it to a slice touching a
Django / Strawberry / channels integration seam — request/response handling, view or ASGI
plumbing, upload or body parsing, session/auth, queryset or expression compilation, schema and
type construction against Strawberry internals, consumer or middleware wiring. The round's diff
contains no executable line, so it touches no seam on any version, and a floor run would
execute code byte-identical to what the shared `.venv` run executes. Docs and comment-only
changes are the section's own named `none` case.

For the record, since the declaration must never rest on remembered numbers: the supported
floor is Django **5.2.16** on Python **3.10** with strawberry-graphql **0.316.0**
(`BUILD.md` `## Floor verification`, the single canonical statement). The shared `.venv` is
**not** the floor and currently carries, read with `uv pip list` this pass: `django 6.1`,
`strawberry-graphql 0.324.0`, `channels 4.3.2`, `djangorestframework 3.18.0`, on Python
**3.14.2** (`uv run python -c "import sys; print(sys.version)"`). No floor venv is built and
the shared `.venv` is not mutated.

### Concurrent-writer hazard the builder must plan around

**7 of the 8 target files are baseline-dirty** from the concurrent session the plan's
`## Baseline-dirty out-of-scope files` records: `forms/inputs.py`, `forms/resolvers.py`,
`forms/sets.py`, `mutations/sets.py`, `apps/products/forms.py`, `apps/products/schema.py`,
`test_query/test_products_api.py`. Only `forms/converter.py` is clean. Consequences, all
already folded into `### Implementation steps`:

- The pristine reference for the inverse proof is a **pre-edit copy**, never `git show HEAD:`.
- Line numbers in this plan are navigational only; anchors are authoritative.
- ruff and the trailing-comma checker run **scoped to the 8 files**, never over the tree.
- Unexpected churn is stop-and-report, never revert.

**The concurrent hunks touch none of the 32 sites**, verified read-only: for each of the 8
files, `git show HEAD:<path>` into a scratch path outside the repo, then the same occurrence
sweep on both copies — HEAD and working tree carry identical P-label counts (2/2, 10/10, 1/1,
9/9, 1/1, 4/4, 2/2, 5/5). So the fix lands on the shipped contract, not on uncommitted work.

### Spec changes made (Worker 1 only)

One custodial edit, in my own writable surface.

**`docs/SPECS/appx/spec-038-form_mutations-0_0_12-rationale.md` — 9 lines, ordinal parentheticals
removed. 82,413 → 82,360 bytes (−53).**

The `docs/**/*.md` sweep found the companion Slice 0 created still carrying **14** P-label
occurrences, on 10 lines. Nine of those lines are the moved `## Risks and open questions` body,
where the labels are the same undecodable emphasis tiers Slice 2 swept from the spec — and the
companion's own `**Post-ship:**` bullet asserts they "were removed" while nine of them stood
eleven lines above it. That is a self-falsifying instrument in a standing, committed document,
and `START.md` "Style Rio cares about" bars severity labels from standing prose outright.
Provably content-free to delete: the same bullet certifies `#"not one of them added a clause"`,
which I re-verified against the HEAD spec's absence of any legend.

| Line | Was | Is |
| --- | --- | --- |
| 936 | `RESOLVED, no longer open (P2).**` | `RESOLVED, no longer open.**` |
| 945 | `RESOLVED (P1).**` | `RESOLVED.**` |
| 957 | `RESOLVED (P1).**` | `RESOLVED.**` |
| 965 | ``RESOLVED (P1, a restored `036` `` | ``RESOLVED (a restored `036` `` |
| 974 | `RESOLVED (P2 / P3).**` | `RESOLVED.**` |
| 984 | `RESOLVED (P1, security).**` | `RESOLVED (security).**` |
| 992 | `RESOLVED (P1).**` | `RESOLVED.**` |
| 997 | `RESOLVED (P2).**` | `RESOLVED.**` |
| 1005 | `RESOLVED (P2 / P3).**` | `RESOLVED.**` |

Lines 965 and 984 kept their content clauses (`a restored 036 …`, `security`) and lost only the
ordinal. Applied assert-all-then-write: each of the 9 anchors asserted to occur exactly once on
its own line first — necessary, because `RESOLVED (P1).**` occurs on three lines and
`RESOLVED (P2 / P3).**` on two, so a file-wide replace would have been wrong.

**Line 1102 was deliberately left alone.** It reads `` `spec-038` keyed its emphasis to `P1` /
`P2` / `P3` priority tiers `` — the sentence *describing* the retired spelling, which is the one
sentence a blanket rewrite destroys (`START.md` "Sweep both files of a pair"). Companion
P-label occurrences: **14 → 3**, all three on that one descriptive line.

Postconditions verified: `uv run python scripts/check_spec_glossary.py --spec
docs/SPECS/spec-038-form_mutations-0_0_12.md` → `OK: 31 terms - all have glossary entries and at
least one spec link.`; `^#` swept for non-headings → none; 1,246 lines, unchanged.

**`docs/SPECS/spec-038-form_mutations-0_0_12.md` — no change.** Its status/header lines
(re-verified this spawn per `worker-1.md` `## Spec status-line re-verification`) still describe
the build's state; the spec carries 0 P-label occurrences, and the source is what changes this
round. `docs/SPECS/appx/spec-038-form_mutations-0_0_12-terms.csv` untouched.

### Deferred work catalog input

Six items. Each names an owner, per `START.md` "Item routed forward w/o NAMED owner dies".

1. **`orders/sets.py`'s two `spec-030 … P1-B` citations are stranded.** `spec-030-connection_field-0_0_9`
   carries **0** P-label occurrences, so both citations are false in shipped source — the
   identical defect this round fixes, left by that cycle. Sites:
   `django_strawberry_framework/orders/sets.py #"(``spec-030-connection_field-0_0_9`` P1-B). Scalar columns"`
   and `#"multiplied (``spec-030-connection_field-0_0_9`` P1-B); ``None``"`. Fenced out by the
   plan's round-1 scope. **Owner: the maintainer**, to route onto a `spec-030` follow-up card —
   the cycle fence bars this round from KANBAN and the kanban DB, so no board home can be
   created from inside it.
2. **Three more stranded `P1-B` citations in the same vocabulary**, missed by a
   `django_strawberry_framework/`-only sweep:
   `examples/fakeshop/test_query/test_library_api.py #"from ``spec-030-connection_field-0_0_9`` P1-B."`,
   `#"(``spec-030-connection_field-0_0_9`` P1-B): ordering by"`, and
   `#"the ``spec-030-connection_field-0_0_9`` P1-B contract."` plus one bare
   `#"does not multiply nodes (P1-B)."`. Same class, same owner; they belong in the same fix as
   item 1 so `spec-030`'s retirement can be proved at 0 rather than half-fixed.
3. **`optimizer/nested_planner.py`'s two `P2-3` citations are stranded.** `spec-033` carries 0
   P-label occurrences. Sites: `#"covering the general page (the P2-3 false-coverage defect);"`
   and `#"naming a duplicated column (the P2-3 defect)."` **Owner: the maintainer**, a `spec-033`
   follow-up card.
4. **`tests/test_relay_node_field.py`'s `the P1 bug` / `the P2 bug`** — `spec-032` carries 0
   P-label occurrences in its spec (47 in its rationale companion), so these are stranded.
   **Owner: the maintainer**, a `spec-032` follow-up card.
5. **Three P-labels naming no spec at all**, undecodable without their author:
   `tests/test_lateral_pg_parity.py #"P2-4: two callers of ONE extension"`,
   `examples/fakeshop/apps/library/tests/test_generic_connection_sharded.py #"Pins the P1 fix:"`,
   `examples/fakeshop/test_query/test_library_api.py #"the P0 served it 1"`. Neither of the first
   two files contains a single `spec-NNN` reference. **Owner: the maintainer** — resolving these
   needs the authoring cycle, which no worker can recover.
6. **`AGENTS.md` rule 27's ordinal half has no gate, and that is why this round exists.**
   `scripts/check_citations.py` resolves `path::Symbol` references only, and says so in its own
   docstring; `docs/` is deliberately out of its scope. Nothing in the repo can see a
   `spec-NNN … <ordinal>` citation, so the class recurs silently on every spec sweep — the
   `START.md` "Rule w/o gate rots" shape, whose stated remedy is the missing gate rather than
   the sites. A gate would need a policy call (which ordinal vocabularies are legitimate,
   whether `Decision N` / `DoD N` / `step N` stay permitted, whether `docs/` enters scope), so
   it is a **contract-level question, not a worker's call** (`BUILD.md`
   `### Contract-level findings are escalated as maintainer decisions before dispatch`).
   **Owner: the maintainer.** Concrete shape if wanted: extend `check_citations.py` to flag
   `spec-<NNN>` followed within one line by an ordinal token not on an allowlist, resolved
   against that spec's live text. Deliberately **not** attempted in this round — a new gate is
   scope this round's brief does not carry, and 32 fixed sites with an ungated rule is still
   strictly better than 32 false citations.

### Notes for Worker 1 (spec reconciliation)

Nothing outstanding at plan time. One thing to re-check at final verification: whether Worker 2's
retirement sweep reports the whole-corpus figure **72 → 40** and not merely "0 in the files I
touched" — the second reads as a clean repo while leaving the out-of-scope partition unmeasured,
and the difference between the two is the entire deferred catalog above.

---

## Build report (Worker 2)

All 32 sites landed as the plan's tables give them: 32 replacements over 8 files, 33 changed
output lines (one site is a two-line wrapped edit), 0 executable lines. No wording was invented
per site - the plan's fixed spellings (`spec-038 Decision 7`, `the decode reverse map`,
`the file-routing contract`) were used verbatim, so the four reverse-map sites and the two
file-routing sites carry one wording each rather than six near-copies.

### Files touched

Grounded in `git status --short` and in a `diff` against the pre-edit pristine copies (the
authoritative instrument here, since 7 of the 8 files are baseline-dirty with a concurrent
session's executable work and `git diff` shows theirs as well as mine).

| File | Sites | Changed lines vs pristine | What changed |
| --- | --- | --- | --- |
| `django_strawberry_framework/forms/converter.py` | 2 | 2 | dropped the `P1` / `P2` sub-ordinal from the re-export comment and the `convert_form_field` fail-loud-dispatch docstring |
| `django_strawberry_framework/forms/inputs.py` | 8 | 9 | 6 sub-ordinals dropped; the module-docstring bullet and the `get_form_fields` docstring lost a redundant parenthetical (the latter also lost the banned "fix" provenance) |
| `django_strawberry_framework/forms/resolvers.py` | 1 | 1 | `_reconstruct_partial_data` lost `(the prior P1 fix)` - banned provenance, restating its own two preceding sentences |
| `django_strawberry_framework/forms/sets.py` | 9 | 9 | 4 sub-ordinals dropped; 3 restated by content (`the decode reverse map` x2, `the plain-base edge case`); 2 redundant parentheticals deleted; the `_validate_meta` snapshot citation gained its missing `spec-038` prefix |
| `django_strawberry_framework/mutations/sets.py` | 1 | 1 | `cached_build_input`'s `load-bearing ordering (spec-038 Decision 7 P2 / spec-039 Decision 7)` lost only the spec-038 sub-ordinal; the `load-bearing ordering` invariant and the spec-039 half are untouched |
| `examples/fakeshop/apps/products/forms.py` | 4 | 4 | 3 redundant parentheticals / bare ordinals deleted; `ItemModelForm`'s wrapped `(the P1 / reverse map)` restated as `(the decode / reverse map)` |
| `examples/fakeshop/apps/products/schema.py` | 2 | 2 | `(the P1 file-routing contract)` -> `(the file-routing contract)`; `(the P2 case)` deleted |
| `examples/fakeshop/test_query/test_products_api.py` | 5 | 5 | 4 bare ordinals deleted from docstrings (the `RIGHT-PATH / LOAD-BEARING` marker kept); the partial-update comment restated as `the partial-update preservation` |

`diff` against pristine over all 8 files: **66 `<`/`>` lines = 33 removed + 33 added**, and
nothing else. Re-run after every gate, so no concurrent write landed in these files mid-pass.

**Every replacement was checked against the spec's CURRENT text**, not against the plan's row.
The nine anchors the plan cites all still stand at HEAD-of-working-tree spec: `### Decision 7 -
Form-field -> Strawberry input mapping: the form is the input source of truth` (spec line 1080)
survives; `**The fail-loud contract requires NOT registering a base-`forms.Field` catch-all.**`
(1155); `**Per-field metadata: the `input_attr` -> `form_field_name` reverse map.**` (1169);
`which owns the constants and not the record type` (1183-1185); the extra field that
`keeps its declared `field.required`` (1244-1248); `**Shape identity + naming + collision (the
`036` discipline).**` (1251) with the `the fixed sentinel **`"form"`**` component (1262-1264);
`**`Meta.fields` / `Meta.exclude` are normalized + fail-loud against `form_class.base_fields`.**`
(1291); `**A `create` narrowing that drops a required form field is rejected.**` plus its
`get_form_kwargs` / `get_form` waiver (1303-1327); `**Schema-time field discovery reads
`form_class.base_fields`, never an instance` (1348); the Decision 8 reconstruction that
`reconstructs the complete bound payload from the located instance` (1457) and `reads the form's
FULL declared field set` (1464); `defeating the two-base split)` (328); `**A `ModelForm` placed
on the plain `DjangoFormMutation` base.**` (1879); and the slice-table phrase
`partial-update preservation` (1813). The spec carries **0** P-label occurrences, measured this
pass, so no replacement restores an ordinal.

**No WHY was lost.** Each of the 32 sites was read in context before editing, and in every case
the mechanism sits in the same clause or the adjacent sentence: `forms/sets.py`'s cache comment
keeps `the load-bearing` qualifier and its whole "caching only `input_cls` would discard" chain;
`mutations/sets.py::cached_build_input` keeps `load-bearing ordering` verbatim and the guard-
before-cache explanation under it; `forms/sets.py::DjangoFormMutation._validate_meta`'s
`# Check ``ModelForm`` FIRST` comment keeps the four lines of sibling-class reasoning beneath it;
`test_products_api.py`'s `RIGHT-PATH / LOAD-BEARING` marker survives with only the ordinal gone.

### Tests added or updated

**None as tests.** Five sites live in `examples/fakeshop/test_query/test_products_api.py` but
every one is a docstring or comment, so no assertion, node id, parametrization, fixture, or test
name changes. Proved two ways rather than asserted:

- `def test_` definitions in that file: **118 in the pristine copy, 118 in the working tree**.
- `uv run pytest examples/fakeshop/test_query/test_products_api.py --collect-only -q --no-cov` ->
  **135 tests collected** (118 functions, the remainder parametrized cases), collection clean.
- the docstring-stripped AST digest is **IDENTICAL** for that file, which is a stronger statement
  than an equal node count: no `def` moved, changed name, or changed decoration.

### Validation run

Every write-mode invocation was scoped to the 8 files; nothing ran over `.`. The file list was
passed as a zsh **array** - the first attempt used a bare `$F` scalar and every tool reported
`No such file or directory` on the whole joined string, the exact word-splitting failure
`START.md` "Instruments that lie" names. That failure was loud rather than silent here only
because the tools error on a missing path; the sweeps in this pass all use a Python heredoc.

- `uv run ruff format <the 8 files>` - **pass**, `8 files left unchanged` (so the edits needed no
  reformat and produced no churn to attribute).
- `uv run ruff check --fix <the same 8 files>` - **pass**, `All checks passed!`, nothing fixed.
- `uv run python scripts/check_trailing_commas.py --check <the 8 files>` - **pass**, exit 0
  (this is also the ASCII-only `.py` gate and reads the 99-column limit from `pyproject.toml`).
- `uv run pytest tests/forms examples/fakeshop/test_query/test_products_api.py -n0 --no-cov` -
  **398 passed** in 25.96s.
- `uv run pytest --no-cov` (full parallel) - **7268 passed, 40 skipped, 0 failed, 0 collection
  errors** in 68.16s. See the note below: the four failures the prior pass recorded as
  pre-existing are **gone**.
- `uv run python examples/fakeshop/manage.py check` - `System check identified no issues
  (0 silenced).`
- `uv run python scripts/check_citations.py --check` - `OK: 938 citations resolve (785 in 435
  .py files, 153 in KANBAN.md).` Identical to the baseline the plan recorded. **This gate says
  nothing about this round's defect**: by its own docstring it resolves `path::Symbol` references
  only and cannot see an ordinal citation. It is a regression check on the `::Symbol` citations
  sitting beside the edits, and green here is not evidence the fix worked.
- `uvx pre-commit run --files <the 8 files>` - all six hooks **Passed** (kanban tracked path
  constants, source layout, ruff format, ruff check, kanban anchors, citations resolve).
- `git status --short` - **163 dirty paths**, up from the plan's 116 baseline; the concurrent
  session has kept writing. All 8 of my files appear as ` M` and every one is in the table above.
  Nothing outside the declared partition is mine: the only instrument that can say so in a tree
  this dirty is the pristine-copy diff, and it accounts for exactly 66 lines across the 8 files.
  **No revert, no `git stash` / `checkout` / `restore` / `worktree` was run.**

**Full-sweep population moved, and the direction matters.** The prior pass measured 4 failed /
7240 passed / 40 skipped; this pass measures 0 failed / 7268 passed / 40 skipped. The four
`ActiveInputPermissionAttrs … 'unset_sentinel'` rows are no longer failing and 28 rows were
added, both from the concurrent session's own work on `sets_mixins.py` - not from this round,
which changed no executable line. There is no fifth failure and no collection error, so the
population did not silently shrink. The escalation those four carried is now moot at the working
tree, but it was never worker-verifiable at HEAD and remains Worker 0's to close.

### Retirement proof, and the out-of-scope partition proved unchanged

Instrument: `\bP[0-9]+(?:[.\-][0-9A-Za-z]+)?\b`, **occurrences** counted over whole file text
(never matching lines - two labels on one line read as one otherwise), via a
`uv run python - <<'PY'` heredoc that prints its population size and every per-file count.

**Re-derived, not accepted from the plan.** My own pre-edit measurements: **43** package
occurrences over **110** package `.py` files, **72** occurrences over the **437** tracked `.py`
files. The plan recorded 43 / 111 and 72 / 435. The occurrence counts reproduce exactly; the
two file-population figures differ because the corpus itself grew - the concurrent session has
added files since the plan was written (`git ls-files '*.py'` at plan time vs now). Worth stating
rather than smoothing over: a population figure is a property of the measurement moment.

| Scope | Before | After |
| --- | --- | --- |
| the 32 in-scope sites | 32 | **0** |
| all 8 target files (34 = 32 in-scope + spec-039's `P1.6` / `P2.2` in `forms/inputs.py`) | 34 | **2** |
| whole tracked `.py` corpus (437 files) | 72 | **40** |

Per-file, before -> after: `forms/converter.py` 2->0, `forms/inputs.py` 10->2 (residue
`['P1.6', 'P2.2']`, spec-039's, out of scope by the plan's partition), `forms/resolvers.py` 1->0,
`forms/sets.py` 9->0, `mutations/sets.py` 1->0, `apps/products/forms.py` 4->0,
`apps/products/schema.py` 2->0, `test_products_api.py` 5->0.

**Out-of-scope vocabularies, each proved unchanged** (expected -> measured, all `ok`, 0 drifted):
`auth/mutations.py` 1->1 (spec-040 `P4`), `mutations/fields.py` 2->2 (spec-040),
`mutations/inputs.py` 1->1 (spec-039), `optimizer/nested_planner.py` 2->2 (spec-033 `P2-3`),
`orders/sets.py` 2->2 (spec-030 `P1-B`), `rest_framework/inputs.py` 3->3,
`rest_framework/resolvers.py` 4->4, `rest_framework/sets.py` 3->3 (all spec-039),
`utils/inputs.py` 1->1, `utils/querysets.py` 1->1 (spec-045),
`apps/library/tests/test_generic_connection_sharded.py` 1->1,
`test_query/test_library_api.py` 10->10, `tests/optimizer/test_predicates.py` 4->4 (fixture
data, not labels), `tests/test_lateral_pg_parity.py` 1->1, `tests/test_relay_node_field.py` 2->2
(spec-032). Subtotal **38 expected, 38 measured**. Arithmetic closes: 38 out-of-scope elsewhere
+ 2 spec-039 labels inside `forms/inputs.py` = **40**, which is the corpus figure. So the
corpus went 72 -> 40 and every occurrence that survived is one the partition says must.

**Live control on the retirement sweep**, so an instrument that had stopped matching could not
read as a clean repo: the same regex over `django_strawberry_framework/orders/sets.py` still
returns **2**. A separate sweep of the 31 distinctive **old** phrases across all **709** tracked
non-binary files returns **0 residue**, with its own positive control (the new phrase
`the decode reverse map` returns **2** occurrences in `.py`, the two `forms/sets.py` sites that
must carry it; the `forms/sets.py` cache comment reads `the load-bearing decode reverse map` and
`products/forms.py` wraps across two lines, so neither matches that exact control string).

That same 709-file sweep is also the **citer postcondition** `START.md` requires after editing a
cited file: no `#"substring"` citation anywhere in tracked source, specs, or standing docs quotes
any of the 32 old phrases, so no citation was stranded by these rewrites.

### Failability proofs

**Ruling: no forward failability proof is owed; the inverse proof is, and it is recorded below.**

`BUILD.md` `### What needs a proof, and what does not` scopes the obligation to a new boundary,
guard, gate, or rejection path, and exempts doc edits. This pass introduces none. **Re-derived
mechanically rather than taken from the plan:** every changed line was classified by `ast` plus
`tokenize` against the working tree, keyed off the pristine-copy diff, giving **6 COMMENT + 27
DOCSTRING + 0 EXECUTABLE** over 33 changed lines (32 sites; `forms/inputs.py::get_form_fields`
spans two docstring lines, which is why the line tally is 27 where the plan's site tally is 26).
Positive control on the classifier: `django_strawberry_framework/forms/sets.py:105`, the real
module-level `_ALLOWED_PLAIN_FORM_META_KEYS` assignment, classifies **EXECUTABLE**. **No edit
touched an executable line**, so nothing rides the inverse proof that should have owed its own.

- **Inverse proof - AST identity with docstrings stripped.** Reference: the **pre-edit pristine
  copies** taken to
  `/private/tmp/claude-501/-Users-riordenweber-projects-django-strawberry-framework/<session>/scratchpad/pristine/`
  **before** any edit, named by path with `/` -> `_`. Not `git show HEAD:` - 7 of the 8 files
  carry a concurrent session's uncommitted executable changes, so a HEAD comparison would report
  their diff as mine. Script: `<scratchpad>/ast_identity.py` (the plan's validated digest -
  strip the leading string-constant `Expr` from every `Module` / `FunctionDef` /
  `AsyncFunctionDef` / `ClassDef` body, then `ast.dump(..., include_attributes=False)`).
  **Result: 8 IDENTICAL, files compared 8, diverged 0, exit 0.**
- **Controls run FIRST, and the executable one fires.** `START.md`: a control that cannot fail is
  equivalent to a passing proof, and the plan records that its own first control did not fire.
  All three controls mutate a **copy in memory** and never the repository.

| Control | Mutation | Result | Reading |
| --- | --- | --- | --- |
| 1 - docstring blindness | `forms/converter.py` docstring text `spec-038 Decision 7 P2` -> `the fail-loud dispatch contract` (anchor asserted to occur exactly once first) | 8 IDENTICAL, exit 0 | correct; the digest is deliberately blind to docstring text |
| 2 - **the control that must fail** | `forms/sets.py` executable `_ALLOWED_PLAIN_FORM_META_KEYS: frozenset[str]` -> `_ALLOWED_PLAIN_FORM_META_KEYS_X: frozenset[str]` | **DIVERGED on `forms/sets.py`, diverged 1, exit 1** | correct; the digest catches any executable change, so the IDENTICAL result above is a measurement and not a vacuous one |
| 3 - comment blindness | `forms/sets.py` comment text `discard the load-bearing P1 reverse map.` -> its replacement | 8 IDENTICAL, exit 0 | correct; comments are absent from the AST, which is what makes the inverse proof valid for the 6 comment sites too |

  Control 2's **first** attempt aborted rather than passing: the anchor
  `_ALLOWED_PLAIN_FORM_META_KEYS =` occurs **0** times in that file (the real line is annotated,
  `: frozenset[str] =`), and the harness asserts anchor uniqueness before mutating, so it printed
  `ABORT: control anchor is not unique; the control could not fire` and exited 2. Recorded
  because a control harness without that assertion would have printed 8 IDENTICAL and been read
  as a firing control - the same failure the plan reports hitting.

- No mutation was ever applied to a repository file, so no revert was needed and none was
  performed; the pristine copies remain byte-identical to the pre-edit files and the working
  tree's only delta versus them is the 66-line comment/docstring diff above.

### Hot-path budget

**Not applicable; zero executable lines.** Nothing runs per request, per resolver, per row, per
connection, or per outbound message, because nothing new runs at all: 6 comments and 27 docstring
lines changed, 0 executable lines, measured by the `ast` + `tokenize` classification above with
its EXECUTABLE positive control, and independently corroborated by the docstring-stripped AST
digest being identical across all 8 files.

### Floor verification

**Not applicable; plan declares floor-verification scope `none`.** The diff contains no
executable line, so it touches no Django / Strawberry / channels integration seam on any version.
For the record, and read this pass rather than recalled: the supported floor is Django
**5.2.16** on Python **3.10** with strawberry-graphql **0.316.0** (`BUILD.md`
`## Floor verification`, the single canonical statement). The shared `.venv` is **not** the floor
and currently carries, per `uv pip list`: `django 6.1`, `strawberry-graphql 0.324.0`,
`channels 4.3.2`, `djangorestframework 3.18.0`, on Python **3.14.2**
(`uv run python -c "import sys; print(sys.version)"`). No floor venv was built; the shared
`.venv` was not mutated.

### Implementation notes

- **Applied as one assert-all-then-write script**, the mechanism the plan left to my discretion
  (`<scratchpad>/apply.py`). Phase 1 asserts all 32 anchors occur **exactly once** in their file
  and prints every count, aborting with nothing written on any partial match; phase 2 re-asserts
  `count == 1` immediately before each individual `replace(..., 1)`; phase 3 re-measures line
  length. All 32 were unique on the first run, so the plan's warning about 7 non-unique anchors
  did not recur - the plan had already corrected them. Two pairs needed the distinguishing prefix
  the plan supplies rather than the bare phrase: `the P1 reverse map).` occurs twice in
  `forms/sets.py` (as `payload (the P1 reverse map).` and `decode (the P1 reverse map).`), and a
  blanket replace of either would have been wrong.
- **Line length re-measured against only the 33 changed lines**, not the whole file. A whole-file
  measure reports 48 lines over 99 in these 8 files, every one pre-existing and inside the E501
  grace, and reading that as a failure of this pass would have been a false positive. Of my 33:
  the longest is `test_products_api.py`'s Group D comment at **exactly 99** columns, as the plan
  predicted - so it must not be lengthened. Nothing else exceeds 96. `ruff format` then left all
  8 files unchanged, confirming no line needed re-wrapping.
- **The two-line wrapped edits were applied as multi-line anchors**, so the wrap is exactly the
  shape the plan's tables give: `forms/inputs.py::get_form_fields` becomes
  `... (spec-038 Decision 7).` / `The overridable`, and `products/forms.py::ItemModelForm`
  becomes `... (the decode` / `reverse map)`. Worth one flag for Worker 3: literal compliance
  leaves `forms/inputs.py`'s second line as a 19-column `The overridable` mid-paragraph, and
  `forms/sets.py` similarly ends two wrapped docstring paragraphs on short lines
  (`two-base split).`, `decode.`). `ruff format` does not reflow docstring prose, so these persist
  as written. I did **not** reflow them: the plan fixes the replacement text and reflowing would
  also re-break the exact line a future `#"substring"` citation might quote. If the reviewer
  prefers a reflow, it is a pure-whitespace follow-up with no wording change.
- `forms/sets.py::DjangoFormMutation._validate_meta` and
  `forms/sets.py::_cached_build_form_input` each **gained** a citation component rather than only
  losing one (`spec-038` prefix; `Decision 7`), per Group A row 12 and Group B row 2. Both now
  spell the full pointer, so neither depends on anchor distance.

### Notes for Worker 3

- **Read the diff against the pristine copies, not `git diff`.** 7 of the 8 files are
  baseline-dirty with a concurrent session's executable work, so `git diff` on them is mixed.
  The pristine copies are at
  `/private/tmp/claude-501/-Users-riordenweber-projects-django-strawberry-framework/<session>/scratchpad/pristine/`,
  path-flattened with `/` -> `_`; `diff` against them shows exactly 33 removed + 33 added lines
  and nothing else. The inverse-proof script sits beside them as `ast_identity.py` and takes the
  reference directory as `argv[1]` plus `real` or `control ...` as `argv[2]`.
- **The one proof to re-run is control 2**, the executable mutation: if it does not print
  `DIVERGED` and exit 1, the 8-IDENTICAL real result means nothing. Both other controls are
  supposed to print IDENTICAL (the digest is blind to docstrings and comments by construction).
  Note the anchor must be the annotated form `_ALLOWED_PLAIN_FORM_META_KEYS: frozenset[str]`.
- **`scripts/check_citations.py` green is not evidence for this round.** It resolves
  `path::Symbol` only and structurally cannot see an ordinal citation. The retirement proof (32
  -> 0 in scope, 72 -> 40 corpus, 38 out-of-scope occurrences unchanged) is the evidence.
- **The four full-sweep failures recorded in prior passes no longer fail.** 0 failed / 7268
  passed / 40 skipped this pass; the concurrent session's `sets_mixins.py` work resolved them and
  added 28 rows. Do not read the changed population as this round's doing - no executable line
  changed here, and the AST-identity proof is the mechanical statement of that.
- `forms/inputs.py` retains **2** P-labels after this pass (`P1.6`, `P2.2`, both naming
  `spec-039` on their own lines, both resolving against a spec that still carries its labels).
  That is the partition's intent, not missed residue.

### Notes for Worker 1 (spec reconciliation)

No spec amendment is required by this pass. Every replacement was verified against the spec's
current text before it was written (the anchor list is in `### Files touched`), and each is a true
statement of what the spec now says. Three observations routed forward, none of them an
amendment:

1. **The plan's Group C ground for `forms/inputs.py::get_form_fields` is slightly off, and the
   edit is still right.** The plan says "fix" is process provenance `START.md` bars, which is
   true of the source comment - but the **spec itself** still carries the same phrase, at
   `## Decisions` -> `### Decision 7 - Form-field -> Strawberry input mapping: the form is the
   input source of truth`: current wording `**Schema-time field discovery reads
   `form_class.base_fields`, never an instance (the kwarg-requiring-form fix).**` So the deleted
   phrase was not unresolvable, merely banned in source. **Recommended replacement:** in the
   spec, `**Schema-time field discovery reads `form_class.base_fields`, never an instance (the
   kwarg-requiring-form case).**` - the same bracket content with `fix` (a process word) replaced
   by `case`, matching how `## Edge cases and constraints` names the same situation. Custodian's
   call; nothing in source depends on it.
2. **The whole-corpus retirement figure is 72 -> 40, and the out-of-scope 40 is itemized
   per file** in `### Retirement proof`, which is what the plan's own note for you asked to be
   able to check. The 40 is exactly the deferred catalog's population plus spec-039's and
   spec-045's live vocabularies; no in-scope occurrence survives.
3. **Two population figures in the plan are now stale by growth, not by error.** The plan records
   111 package `.py` files and a 435-file corpus; this pass measures **110** and **437**. The
   occurrence counts (43 package, 72 corpus) reproduce exactly. The concurrent session has been
   adding and moving files, so any file-population number in this cycle's artifacts is a property
   of its measurement moment. No artifact edit is requested - flagged so a later reader does not
   grade the difference as a miscount.

---

## Review (Worker 3)

**Reference discipline first, because `git show HEAD:` is not a clean reference here.** 7 of the
8 files carry a concurrent session's uncommitted executable work, so a HEAD-vs-tree diff reports
their changes as this round's. I did not accept Worker 2's pristine copies on trust either;
I established my own reference and then proved the pristine set legitimate against it:

- `git show HEAD:<path>` for all 8 files into a scratch path outside the repo
  (`<scratchpad>/w3-r1/head/`), plus a worktree snapshot. No `git stash` / `checkout` /
  `restore` / `worktree` was run at any point.
- Line-delta arithmetic closes exactly: HEAD -> pristine is **502** `<`/`>` lines (the concurrent
  session's work, `forms/converter.py` alone clean at 0), HEAD -> worktree is **568**, and
  568 - 502 = **66** = the round's 33 removed + 33 added. So the pristine copies are
  HEAD + concurrent and carry none of this round's edits, and no concurrent write landed in
  these 8 files after the snapshot.
- The P-label census agrees per file between HEAD and pristine (2/2, 10/10, 1/1, 9/9, 1/1, 4/4,
  2/2, 5/5, total **34/34**), so the concurrent hunks touch none of the 32 sites.

On that reference the round's whole diff is **33 removed + 33 added lines over 8 files and
nothing else** — reproduced independently, matching the build report.

### High:

None.

### Medium:

#### The census had a second blind spot: 16 stranded ordinal citations in three vocabularies, none homed

`django_strawberry_framework/forms/inputs.py #"(spec-039 Md1), shared with the"`,
`django_strawberry_framework/forms/sets.py #"(spec-039 Md7), shared with the"`,
`django_strawberry_framework/mutations/sets.py::construction_kwargs #"(spec-039 Md7)."`

The plan's out-of-scope table certifies spec-039's citations with "Every one names `spec-039` on
its own line. … so each citation **resolves**. Not a defect." That certification was reached with
`\bP[0-9]+(?:[.\-][0-9A-Za-z]+)?\b`, which **structurally cannot see** `Md1`. It is the same
instrument-reach failure the plan itself diagnosed in Worker 0's `\bP[123]\b`, one vocabulary
further out.

I re-derived the population with a different instrument — resolve every
`spec-<NNN> <ordinal-token>` citation in tracked `.py` against that spec's own live text
(934 such citations examined over 437 files; the shape deferred-catalog item 6 proposes as a
gate). Result:

| Vocabulary | Sites | In spec-NNN's spec | In its rationale companion | Catalogued |
| --- | --- | --- | --- | --- |
| `spec-038 P<N>` | **0** | — | — | retired by this round |
| `spec-030 P1-B` | 5 | 0 | yes | yes (items 1-2) |
| `spec-039 Md1` / `Md2` / `Md3` / `Md4` / `Md5` / `Md7` | **14** | **0** | **0** | **no** |
| `spec-044 D4-D5` (`tests/extensions/test_debug.py`) | 1 | 0 | 0 | **no** |
| `spec-048 D1` (`examples/fakeshop/test_query/test_uploads_api.py`) | 1 | 0 | 0 | **no** |

`Md<n>` appears **once** in all 195 tracked `.md` files, and that one occurrence is itself a
citation (`docs/SPECS/appx/spec-036-mutations-0_0_11-rationale.md #"`Md5` promotions"`), not a
definition. `git show HEAD:docs/SPECS/spec-039-serializer_mutations-0_0_13.md` carries 0, so the
vocabulary was never in that spec — these are not labels a later cycle will strand, they are
false already, in shipped source, in 8 package files.

**Why it matters.** Three of the 14 `Md<n>` sites sit inside this round's own writable set, in
files the round edited, and the round records no deferral for the class. `START.md`
"Partial claim fix = dominant residual defect" is the exact shape: one spelling retired to 0
while a parallel live spelling in the same files stays unrecorded, so the cycle reopens.
`BUILD.md` `## Claims are proven mechanically` fixes Medium for the published-closure claim
("The vocabulary is closed at uppercase `P<N>` with an optional `.M` / `-M` suffix"), which is
false. Deferred item 6 names the *class* (an ungated ordinal citation) and softens this to
Medium rather than High, but it does not enumerate these sites, and items 1-5 enumerate every
other stranded vocabulary — so the omission reads as "measured and absent", not "out of scope".

**Recommended change — no source edit.** These belong to spec-039's / spec-044's / spec-048's
own cycles exactly as `spec-030 P1-B` does; fixing them here would repeat the half-fix this
round is correcting. Record them in `### Notes for Worker 1 (spec reconciliation)` as catalog
input with a named owner (the maintainer, onto a `spec-039` follow-up card for the 14, and one
each for `spec-044` / `spec-048`), and narrow the plan's spec-039 certification to the
`P<N>.<M>` labels it actually measured. Verifiable by re-running the resolver above and
asserting spec-038's row stays at 0.

#### The 111/435 -> 110/437 difference is instrument, not corpus growth

`docs/builder/bld-038-review-1-citation_residue.md` `### Notes for Worker 1 (spec reconciliation)`
item 3, and `### Retirement proof, and the out-of-scope partition proved unchanged` #"the corpus
itself grew"

The build report states as fact: "Two population figures in the plan are now stale by growth,
not by error. … The concurrent session has been adding and moving files". Measured this pass:

```
git ls-files 'django_strawberry_framework/*.py'          -> 110
Path("django_strawberry_framework").rglob("*.py")        -> 111
rglob over django_strawberry_framework/ tests/ examples/ scripts/  -> 435
git ls-files '*.py'                                      -> 437
in rglob but not tracked: ['django_strawberry_framework/utils/canonical.py']
tracked .py outside those four trees: ['conftest.py', 'docs/dry/export_dry_review.py', 'line_count.py']
```

The plan's **111 and 435 both reproduce live, this minute** — they are `rglob` readings.
Worker 2's 110 and 437 are `git ls-files` readings. The whole difference is one untracked file
the concurrent session added (counted by `rglob`, invisible to `git ls-files`) and three
tracked root-level files (the reverse). Nothing is stale. `scripts/check_citations.py --check`
independently prints `435 .py files` this pass, from the same four-tree `rglob`.

The self-check the report skipped: a package count that **fell** (111 -> 110) cannot be explained
by "the corpus grew" at all, and that decrement was published beside the growth story.
`START.md` "Instruments that lie": "State instrument input before trusting output; state PATTERN
as parameter of any published figure", and "Count right in every digit, wrong in SUBJECT."
`BUILD.md` `## Claims are proven mechanically` fixes Medium for a stated count asserted rather
than verified — and this one is not merely unverified, it is falsified by one command.

**Recommended change.** Correct that paragraph to name each figure's instrument and withdraw the
"stale by growth" characterization; the report already says "No artifact edit is requested",
which is what would leave the false cause standing permanently in a tracked cycle artifact for
Worker 1 to act on. Nothing in the retirement proof depends on it: the occurrence counts (43
package, 72 corpus, 40 after) all reproduce exactly.

### Low:

#### One orphaned 19-column docstring line — the reflow flag, ruled

`django_strawberry_framework/forms/inputs.py::get_form_fields #"The overridable"`

Worker 2 flagged three short lines and did not reflow. Graded individually:

| Site | Columns | Position | Ruling |
| --- | --- | --- | --- |
| `forms/inputs.py::get_form_fields #"The overridable"` | 19 | **mid-paragraph**, prose continues on the next two lines | genuine orphan — **fix** |
| `forms/sets.py::DjangoFormMutation._validate_meta #"two-base split)."` | 26 | **paragraph-final** (next line opens a new bullet) | correct as-is |
| `forms/sets.py::DjangoFormMutation.build_input #"decode."` | 15 | **paragraph-final** (next line is `"""`) | correct as-is |
| `forms/resolvers.py::_reconstruct_partial_data #"from the located row. A file field"` | 64 | mid-paragraph, under-full by 35 | reads as an ordinary wrap; leave |

So two of the three flagged spots are not defects: a wrapped prose paragraph's last line is
short by construction. The one real orphan has a fix that touches **two lines and reflows no
other text** — join it onto the line above:

```django_strawberry_framework/forms/inputs.py:179:180
    discoverable, request-independent stable field shape (spec-038 Decision 7). The overridable
    ``get_form_fields(cls)`` classmethod on the base delegates here for its
```

95 columns, inside 99, and `ruff format` does not reflow docstring prose so it persists as
written. **The trade-off Worker 2 raised is real in general and empirically nil here:** I
resolved every `#"substring"` citation in the tree (1,447 examined over 709 files) against these
four lines — **0 overlap**, so no citation anywhere breaks on the join.

#### "Inside the E501 grace" is wrong for 11 of the 48 long lines

`docs/builder/bld-038-review-1-citation_residue.md` `### Implementation notes` #"inside the E501
grace"

The count is right — **48** lines over 99 across the 8 files, and I confirmed **none** of them is
one of this round's 33 added lines. But 11 run past the 110 grace (longest **137**, e.g.
`examples/fakeshop/apps/products/schema.py:189`). They pass because
`pyproject.toml [tool.ruff.lint.per-file-ignores]` disables `E501` outright for `tests/**/*.py`
and `examples/**/*.py` — not because of the grace. Harmless to this round; recorded so a later
reader does not infer a 137-column allowance. Correct the clause to name the per-file ignore.

### DRY findings

None. The round adds zero executable lines, so it can introduce no duplicated logic, and the
shared-wording decision the plan made rather than delegating is the right call and held:

- `the decode reverse map` — **2** occurrences in tracked `.py`, the two `forms/sets.py` sites
  the plan named; `products/forms.py` carries the wrapped variant and `products/forms.py`'s
  module bullet keeps its own distinct qualifier, both as the plan reasoned.
- `the file-routing contract` — **1** occurrence, as planned (the `test_products_api.py` site
  deletes instead, for the column budget).
- `the plain-base edge case` — **1**. `partial-update preservation` — **3**, and the phrase is
  the spec's own (spec lines 441 / 1813 / 2249), so this is vocabulary reuse, not a new spelling.
- `reverse map` is already a 99-occurrence house term across the package; the round introduced no
  competing phrasing.

No existence challenge. The plan pre-answered it (delete the 32 comments instead) and the answer
is right: each carries a mechanism — the guard-before-cache ordering, the reverse-map rationale,
the `ModelForm`-checked-first reason — that the code does not otherwise state.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty**: `__all__` and the re-export
list are unchanged. No new public exports.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Worker 2's diff touches none of those surfaces. Worker 1's one custodial edit in its own writable
surface is verified mechanically rather than accepted:
`docs/SPECS/appx/spec-038-form_mutations-0_0_12-rationale.md` now carries **3** P-label
occurrences on **1** line (1102, `#"keyed its emphasis to `P1` / `P2` / `P3` priority tiers"` —
the sentence *describing* the retired spelling, correctly preserved per `START.md` "Sweep both
files of a pair"), `RESOLVED (P` residue **0**, 1,245 lines, **82,360 bytes** — every figure
matching Worker 1's record. `uv run python scripts/check_spec_glossary.py --spec
docs/SPECS/spec-038-form_mutations-0_0_12.md` -> `OK: 31 terms - all have glossary entries and at
least one spec link.` The active spec carries **0** P-label occurrences over 2,408 lines.

### What looks solid

**Every one of the 32 replacements is true of the spec's current text.** I checked each against
the live spec rather than against the plan's row. Grading the four groups on their own terms:

- **Group A (12) — `spec-038 Decision 7` alone does locate each contract.** The heading survives
  verbatim at spec line 1080 and `Decision 7` occurs 28 times in the live spec. Each site's
  contract is inside it: the four `kind` constants re-exported by `forms/converter.py`
  (1182-1185); the no-catch-all fail-loud registry (1155-1167); the `"form"` operation sentinel
  (1261-1265); `Meta.fields` / `Meta.exclude` normalized + fail-loud (1291-1301); the
  deterministic shape-derived name (1251-1289); the non-model extra keeping its declared
  `field.required` (1244-1249); the create-required-narrowing raise and its one
  `get_form_kwargs` / `get_form` waiver (1303-1315). `START.md` "Bare `Decision N` = repo-wide
  convention … Grade by ANCHOR presence, never distance" is satisfied at all 12 — the `spec-038`
  anchor is on the line — and since Slice 2 left the spec with no sub-anchors, there is no finer
  true citation available; each comment's own sentence carries the payload and the pointer is
  corroboration.
- **`mutations/sets.py::cached_build_input #"load-bearing ordering"` is the load-bearing site and
  it held.** The invariant phrase, the guard-before-cache explanation under it, and the
  already-ordinal-free `spec-039 Decision 7` half are all untouched; only the spec-038
  sub-ordinal went. Decision 7 owns the guard and its "raises … **at class creation**" timing
  (1308-1309), which is what "PER declaration" restates; the before-the-cache-lookup half is an
  implementation invariant the comment states itself, exactly as the plan reasoned.
  I confirmed `spec-039` does carry a `### Decision 7` (its line 1976), so neither half is
  half-broken.
- **Group B (5) restates by content, accurately.** `the decode reverse map` tracks spec 1169
  (`**Per-field metadata: the `input_attr` -> `form_field_name` reverse map.**`) and 1199-1203
  (the decode produces the form-field-keyed dict); `the plain-base edge case` tracks the
  `## Edge cases and constraints` entry at 1879. Both `forms/sets.py` sites that **gained** a
  component (`spec-038` prefix; `Decision 7`) now spell the full pointer.
- **Group C (14) lost no WHY.** Read each in context: the mechanism sits in the same clause or
  the adjacent sentence every time. The two banned-provenance deletions are the ones worth
  naming — `get_form_fields` keeps "a form whose `__init__` requires constructor kwargs …
  still has a discoverable, request-independent stable field shape", and
  `_reconstruct_partial_data` keeps two sentences stating the reconstruction rule plus its
  `spec-038 Decision 8` pointer nine lines up (spec 1457/1464 confirm both), so neither deletion
  removed the reason the code is shaped that way.
- **Group D (1)** uses the spec's own phrase and lands at **exactly 99** columns, as planned.
- **No residual stranded spec-038 ordinal in the 8 files.** Every other spec-ordinal citation
  they carry resolves: `Decision 6` / `7` / `8` / `10` / `11` / `13` all exist in spec-038, and
  `Decision 8 step 4` resolves (spec 1399-1400). The 2 surviving `forms/inputs.py` labels are
  spec-039's `P2.2` (line 108, `spec-039` on the line) and `P1.6` (line 160, `spec-039` on the
  line above inside the same comment block), and both resolve — 6 and 10 occurrences in
  spec-039. That is the partition's intent, not residue.

**Line budget.** All 33 changed lines re-measured: **0 over 99**, longest exactly **99**
(the Group D comment), next 96. `uv run ruff format --check .` -> `438 files already formatted`.

**Classification and the hot-path / floor declarations rest on measured ground, not on the
declaration.** Independently classified the 33 changed lines with `ast` + `tokenize`:
**6 COMMENT + 27 DOCSTRING + 0 EXECUTABLE**, reproducing the build report exactly, with
`forms/sets.py:105` (`_ALLOWED_PLAIN_FORM_META_KEYS: frozenset[str] = …`) classifying
**EXECUTABLE** as a positive control. Zero executable lines means the hot-path declaration
(`none`) and the floor-verification scope (`none`) are both correct on the ground: nothing runs
per request / resolver / row / connection / message, and no Django / Strawberry / channels seam
is touched on any version. Floor facts per `docs/builder/BUILD.md` `## Floor verification`
(the single canonical statement): Django **5.2.16** on Python **3.10** with strawberry-graphql
**0.316.0**. The shared `.venv` is not the floor and carries, read with `uv pip list` this pass:
`django 6.1`, `strawberry-graphql 0.324.0`, `channels 4.3.2`, `djangorestframework 3.18.0`,
`django-filter 26.1`, on Python **3.14.2**. No floor venv built; shared `.venv` not mutated.

**Retirement and non-interference, re-derived with a live control on every sweep.**

| Scope | Measured this pass |
| --- | --- |
| the 32 in-scope sites | **32 -> 0** (each anchor present exactly once pre-edit, absent now) |
| the 8 target files | **34 -> 2**, the 2 being spec-039's resolving `P1.6` / `P2.2` |
| whole tracked `.py` corpus (`git ls-files '*.py'` = **437** files) | **72 -> 40** over 16 files |
| out-of-scope, HEAD vs worktree, 15 files | **38 / 38, 0 drifted** |

Counted as **occurrences over whole file text**, never matching lines, via a
`uv run python - <<'PY'` heredoc that prints its population size and asserts a non-zero total —
no `for f in $FILES` scalar anywhere. Live negative control on every sweep:
`django_strawberry_framework/orders/sets.py` still returns **2**, asserted, so an instrument that
had stopped matching could not read as a clean repo. Every named out-of-scope vocabulary is
present and untouched at its HEAD count: spec-030 `P1-B`, spec-039 `P1.1` / `P1.5` / `P1.7` /
`P2.2` / `P2.3` / `P2.7`, spec-040 `P4`, spec-033 `P2-3`, spec-032's `P1` / `P2`, spec-045's
`P2`, and `tests/optimizer/test_predicates.py`'s 4 fixture-data hits (`Patron` names, not
citations). Arithmetic closes: 38 elsewhere + 2 inside `forms/inputs.py` = 40.

**The inverse proof re-run, and the control fires in my own hands.** No forward failability proof
is owed — `BUILD.md` `### What needs a proof, and what does not` scopes the obligation to a new
boundary, guard, gate, or rejection path, and 0 executable lines can introduce none; the mandatory
re-run floor (`worker-3.md`, every boundary at <= 3 rows) is therefore **legally empty**. The
inverse proof `START.md` owes instead ("Comment/docstring-only edit owes INVERSE proof: AST
identity w/ docstrings stripped") I re-ran with my **own** digest script
(`<scratchpad>/w3-r1/w3_inverse.py`), against the pristine reference I proved legitimate above:

| Run | Mutation | Result | Reading |
| --- | --- | --- | --- |
| real | none | **8 IDENTICAL, compared 8, diverged 0, exit 0** | no executable line moved in any of the 8 files |
| control 1 | docstring text in `forms/sets.py` | 8 IDENTICAL, exit 0 | correct; blind to docstrings by design |
| control 2 | executable `_ALLOWED_PLAIN_FORM_META_KEYS: frozenset[str]` -> `…_X` | **DIVERGED on `forms/sets.py`, diverged 1, exit 1** | **the control fired** |
| control 3 | comment text in `forms/sets.py` | 8 IDENTICAL, exit 0 | correct; comments absent from the AST |
| control 4 | executable `def test_create_stamped_item_via_form_get_form_kwargs_injects_user` -> `…_X` | **DIVERGED on `test_products_api.py`, diverged 1, exit 1** | fires in the **example** file too, not only in `forms/sets.py` |

I added control 4 deliberately: Worker 2's single firing control lived in one package file, so it
proved the digest detects an executable change *there* and said nothing about the other seven.
Both firing controls assert anchor uniqueness before mutating and abort otherwise — the
`ABORT … exit 2` near-miss Worker 2 recorded (anchor `_ALLOWED_PLAIN_FORM_META_KEYS =` occurring
**0** times because the real line is annotated) is exactly the failure that assertion exists to
catch, and recording it was right. **No repository file was mutated at any point** in my re-run:
every control mutates a copy in memory, so the carve-out was never exercised and there is nothing
to revert.

**No proof mutation survives anywhere.** Swept all 709 readable tracked files for
`_ALLOWED_PLAIN_FORM_META_KEYS_X`, both control docstring strings, the control comment string and
`injects_user_X`: **0 hits**, with `_ALLOWED_PLAIN_FORM_META_KEYS` itself at **5** occurrences as
the positive control that the sweep was reading anything. No `ACTIVE-MUTATION.json` anywhere in
the tree.

**The citer postcondition is discharged, by a stronger instrument than the one claimed.** Worker 2
swept 31 distinctive old phrases over 709 files and argues that discharges `AGENTS.md` rule 27's
postcondition. That argument is **sound but narrower than the obligation**: it can only catch a
citation quoting one of those exact phrases, and `scripts/check_citations.py` is `::Symbol`-only
so it cannot corroborate. I ran the direct form instead — extract every `path #"substring"`
citation in the tree and resolve the substring against the named file, then difference the result
against the pristine copies:

- 709 files scanned, **730** path-qualified substring citations found.
- **0** classified `BROKEN-BY-THIS-ROUND` — no citation that resolved before the 33 edits fails
  after them.
- 128 unresolved citations exist tree-wide, every one already broken pre-edit and overwhelmingly
  in `docs/builder/DONE/` plans and archived specs. Not this round's, and independent
  corroboration for deferred item 6: the ungated `#"substring"` half of rule 27 has a large live
  population.

**`### Dispatched findings checklist` audit: clean.** Parsed all **32** boxes, all `- [x]`, and
tested each tick mechanically — its quoted anchor occurs **exactly once** in that file's
pre-edit copy and **zero** times now. **0** rows where a ticked fix is not provably landed, and
**0** unaddressed boxes. No over-tick, no silent deferral.

**Sweeps, all green, and the population did not shrink.**

- `uv run pytest --no-cov` (full parallel) -> **7268 passed, 40 skipped, exit 0**, 78.85s. No
  `ERROR` / `FAILED` line and no collection-error summary, so no module silently dropped its
  rows: 7,308 nodes ran against the 7,284 the prior pass measured (7240 + 4 + 40), i.e. the
  population **grew** by 24 while the 4 `unset_sentinel` failures went away. Both are the
  concurrent session's `sets_mixins.py` work, not this round's — the AST-identity proof above is
  the mechanical statement that this round changed no executable line, so it cannot have moved a
  test result either way. Worker 2's read is correct.
- `uv run pytest examples/fakeshop/test_query/test_products_api.py --collect-only -q --no-cov` ->
  **135 tests collected**, and `def test_` count **118 pristine / 118 worktree** — both figures
  reproduced, so no node id, name, or parametrization moved.
- `uv run python examples/fakeshop/manage.py check` -> `System check identified no issues (0 silenced).`
- `uv run python scripts/check_citations.py --check` -> `OK: 938 citations resolve (785 in 435
  .py files, 153 in KANBAN.md).` **Green here is not evidence for this round's fix** — by its own
  source it matches `([\w][\w./]*\.py)::([A-Za-z_][\w.]*)` only and cannot see an ordinal
  citation. Worker 2 said so itself rather than banking it, which is the right call.
- `uv run ruff format --check .` -> `438 files already formatted`; `uv run ruff check .` ->
  `All checks passed!` (read-only, no `--fix`, nothing written).
- `uvx pre-commit run --files <the 8 files>` -> all six hooks **Passed**.

**Static inspection helper: skipped, with the reason recorded per file.** `BUILD.md`
`### When to run the helper during build` fires for Worker 3 on a new `.py` (none), an existing
`.py` under `optimizer/` or `types/` (none touched), or 30+ new logic lines inside the package /
50+ outside it. This round adds **0** lines of logic anywhere, so no trigger fires — and the
decisive reason is structural rather than arithmetic: `review_inspect.py` emits the source with
`#` comments removed and every string-literal token, docstrings included, replaced by `...`, so
it is **blind to 100% of this round's content** and its repeated-string-literal section cannot
see a comment near-copy. Per-file skips, all "no review-worthy logic added; comment/docstring
text only, proved by the AST-identity result above":
`forms/converter.py`, `forms/inputs.py`, `forms/resolvers.py`, `forms/sets.py`,
`mutations/sets.py`, `examples/fakeshop/apps/products/forms.py`,
`examples/fakeshop/apps/products/schema.py`,
`examples/fakeshop/test_query/test_products_api.py`. No shadow file was generated, read, or cited
this pass.

### Temp test verification

None written. `docs/builder/temp-tests/round-1/` was not created: with 0 executable lines there is
no behavior for a temp test to distinguish, and every question this pass had was answerable by a
measurement (the census resolver, the AST digest, the citation resolver), all of which live in
`<scratchpad>/w3-r1/` outside the repo and close with this pass.

### Notes for Worker 1 (spec reconciliation)

1. **Worker 2's routed item 1 is correctly characterized, and the source edit does not depend on
   it.** The spec does still carry the phrase, at
   `docs/SPECS/spec-038-form_mutations-0_0_12.md` #"**Schema-time field discovery reads
   `form_class.base_fields`, never an instance" (line 1348-1349), where it reads
   `(the kwarg-requiring-form fix)`. So the deleted parenthetical was resolvable and merely
   banned in source, and the plan's Group C ground overstates it. `fix` -> `case` is a reasonable
   custodial edit and matches how `## Edge cases and constraints` names the situation; it is your
   call. Either way `get_form_fields`'s own docstring states the whole contract, so the deletion
   stands on its own ground.
2. **Worker 2's routed item 2 checks out.** 72 -> 40 with the 40 itemized: 38 out-of-scope
   occurrences over 15 files (HEAD-verified unchanged) + 2 spec-039 labels inside
   `forms/inputs.py`. No in-scope occurrence survives. This is the figure the plan's own note for
   you asked for, and it is the right one.
3. **Worker 2's routed item 3 is wrong — see the Medium above.** Do **not** restate the plan's
   111 / 435 as stale. Both reproduce live under `rglob`; 110 / 437 is `git ls-files`. If you
   normalize the artifacts, normalize on the *instrument*, not on the number.
4. **Escalated (catalog input Worker 2 cannot write, since the catalog is your section):** the
   16 stranded ordinal citations in the Medium above — 14 `spec-039 Md1`/`Md2`/`Md3`/`Md4`/`Md5`/
   `Md7` across `forms/inputs.py`, `forms/sets.py`, `mutations/sets.py`, `mutations/resolvers.py`,
   `rest_framework/inputs.py`, `rest_framework/resolvers.py`, `rest_framework/sets.py`,
   `utils/inputs.py`, `utils/querysets.py`; 1 `spec-044 D4-D5` in `tests/extensions/test_debug.py`;
   1 `spec-048 D1` in `examples/fakeshop/test_query/test_uploads_api.py`. Resolution paths:
   (a) three catalog entries with the maintainer named as owner, mirroring items 1-3's shape, and
   the plan's spec-039 certification narrowed to the `P<N>.<M>` labels it measured; or (b) fold
   them into item 6 as the population that gate would catch on day one. Not a source fix in this
   round either way — they are other cycles' the way `spec-030 P1-B` is.
5. **Corroboration for deferred item 6, if you want a number for it:** the ungated `#"substring"`
   half of rule 27 currently carries **128** unresolved citations tree-wide over 730
   path-qualified ones, mostly in `docs/builder/DONE/` and archived specs. The ordinal half is
   16 (above). A gate resolving `spec-<NNN> <ordinal>` against that spec's live text is
   ~40 lines and would have caught both classes; the policy call it needs is still the
   maintainer's.

### Review outcome

`revision-needed`.

Two Medium findings and two Low findings, none of them in the 32 replacements themselves. The
substance of the round is correct and provably so: all 32 sites landed, every replacement is true
of the spec's current text, 32 -> 0 in scope with 38/38 out-of-scope occurrences unmoved, the
inverse proof holds with two independent executable controls firing in my hands, no citation was
stranded, and every gate is green. What is not accepted is the artifact's account of itself — a
published closure claim that a whole live ordinal vocabulary falsifies, in three of the round's
own files with no deferral recorded, and a physical cause asserted for a purely instrumental
count difference. Both are Worker 2's to correct in its own report (the catalog half routed to
Worker 1 above), neither needs spec context, and neither touches a source line. The `Low`
reflow fix is two lines with a measured-nil citation hazard.

---

## Build report (Worker 2 — apply-changes pass)

Three Worker 3 findings, one of which touches a source line. Dispositions up front, each
argued below: **Low — closed** (one docstring line joined, 19 columns merged into 95);
**Medium 2 — corrected here** (the growth explanation is withdrawn; the cause is two
instruments measuring two populations); **Medium 1 — catalogued, not fixed in source**, with the
population re-derived rather than accepted, which moved the count from 16 to **38** and found
that one of Worker 3's own three groups actually resolves.

The two `Low`-flagged short lines Worker 3 ruled paragraph-final
(`forms/sets.py::DjangoFormMutation._validate_meta #"two-base split)."` and
`forms/sets.py::DjangoFormMutation.build_input #"decode."`) are **unchanged by design**, as is
`forms/resolvers.py::_reconstruct_partial_data #"from the located row. A file field"`. Worker 3's
correction to the E501 clause is accepted and not repeated: 11 of the 48 pre-existing long lines
run past 110 because `pyproject.toml [tool.ruff.lint.per-file-ignores]` disables `E501` outright
for `tests/**/*.py` and `examples/**/*.py`, **not** because of the 110 grace. No line of this
round's is affected either way; the one file this pass edited carries **0** lines over 99
(longest exactly 99).

### Files touched

One file. Grounded in `git status --short` and in `diff` against a pre-edit pristine copy taken
to `<scratchpad>/pristine2/` **before** the edit (38,632 bytes, `cksum` equal to the working-tree
file at copy time), which is the authoritative instrument because this file is baseline-dirty
with a concurrent session's executable work.

| File | Sites | Changed lines vs pristine | What changed |
| --- | --- | --- | --- |
| `django_strawberry_framework/forms/inputs.py` | 1 | 2 removed + 1 added | `get_form_fields`'s docstring: the orphaned 19-column `The overridable` joined onto the line above it |

The joined line reads
`#"discoverable, request-independent stable field shape (spec-038 Decision 7). The overridable"`
at **95** columns, reproducing Worker 3's measurement exactly. `ruff format` left the file
unchanged afterwards, so no reflow followed. Nothing else in the paragraph moved: the three lines
above and the two below are byte-identical to the pristine copy, and the file's longest line is
**99** with **0** lines over 99.

**The reflow hazard was re-measured, not inherited.** `START.md` warns that a `#"substring"`
citation breaks on reflow and is ungated. My own sweep: **1,434** `#"..."` citations over the
**709** text files among the **711** tracked paths, of which **0** quote text lying on either of
the two joined lines. Worker 3 measured 1,447 over the same 709 files; the difference is the
population moving under a concurrent session, and the answer — zero overlap — is the same. The
sweep carried a positive control on its own matching logic (the probe
`request-independent stable field shape`, which *is* on the target line, was detected; an
undetected probe aborts the assert). A second reason the join is safe, structural rather than
measured: both fragments remain substrings of the merged line, so even a citation quoting either
half would still resolve.

### Tests added or updated

**None.** The change is one docstring line in package source; no assertion, node id,
parametrization, fixture, or test name is touched. Corroborated by the docstring-stripped AST
digest below being IDENTICAL, which is a stronger statement than an unchanged test count.

### Validation run

Every write-mode invocation was scoped to the single file; nothing ran over `.`.

- `uv run ruff format django_strawberry_framework/forms/inputs.py` — **pass**,
  `1 file left unchanged`.
- `uv run ruff check --fix <same file>` — **pass**, `All checks passed!`, nothing fixed.
- `uv run python scripts/check_trailing_commas.py --check <same file>` — **pass**, exit 0 (also
  the ASCII-only `.py` gate; it reads the 99-column limit from `pyproject.toml`).
- `uv run pytest tests/forms -n0 --no-cov` — **263 passed** in 1.87s.
- `uv run pytest --no-cov` (full parallel) — **7268 passed, 40 skipped, 0 failed, 0 collection
  errors** in 65.54s. Same population as the prior pass, so nothing silently shrank; a broken
  module would surface as a collection error rather than as a smaller pass count.
- `uv run python examples/fakeshop/manage.py check` — `System check identified no issues
  (0 silenced).`
- `uv run python scripts/check_citations.py --check` — `OK: 938 citations resolve (785 in 435
  .py files, 153 in KANBAN.md).` Identical to baseline. **Green here is not evidence for this
  round**: by its own docstring it resolves `path::Symbol` only and structurally cannot see an
  ordinal citation. Note its `435 .py files` — that is a four-tree `rglob` reading, and it is the
  direct third-party corroboration of Medium 2 below.
- `uvx pre-commit run --files <same file>` — all six hooks **Passed**.
- `git status --short` — **174** dirty paths, up from the 163 the prior pass recorded; the
  concurrent session has kept writing. `django_strawberry_framework/forms/inputs.py` appears as
  ` M`; `docs/builder/bld-038-review-1-citation_residue.md` appears as `??` (a new, not-yet-
  committed cycle artifact). Nothing outside the declared ownership list is mine, and in a tree
  this dirty the only instrument that can say so is the pristine-copy diff, which accounts for
  exactly 3 lines in exactly 1 file. **No revert, and no `git stash` / `checkout` / `restore` /
  `worktree` at any point.**

**In-scope retirement still holds at 0 after the edit, and no out-of-scope vocabulary moved.**
Instrument: `\bP[0-9]+(?:[.\-][0-9A-Za-z]+)?\b`, occurrences over whole file text, via a
`uv run python - <<'PY'` heredoc that prints its population and asserts its own counts.
Population: **437** tracked `.py` files (`git ls-files '*.py'`).

| Scope | Measured this pass |
| --- | --- |
| the 32 in-scope sites | **0** |
| residue inside the 8 target files | **2**, both in `forms/inputs.py` (`P1.6`, `P2.2`, spec-039's, out of scope by the partition) |
| whole tracked `.py` corpus | **40** over 16 files |
| out-of-scope files | **15** files, **38** occurrences; expected 38, measured 38, **0 drifted** |

Live control on that sweep, so a stopped instrument could not read as a clean repo: the same
regex over `django_strawberry_framework/orders/sets.py` returns **2** (`P1-B`, `P1-B`), and the
sweep asserts it — a control returning 0 aborts the run.

### Medium 1 — catalogued with named owners, no source edit; and the population was wrong in both directions

**Disposition: catalogued.** Worker 3's recommendation is followed — these are other cycles'
citations exactly as `spec-030 P1-B` is, and most of their files sit outside this round's
partition. The three that sit inside it (`forms/inputs.py`, `forms/sets.py`, `mutations/sets.py`)
belong to spec-039's vocabulary, not spec-038's; fixing them here would be the same half-fix this
round exists to correct. The entries are in `### Deferred work catalog input (Worker 2 —
apply-changes pass)` below, each with an owner written out in prose, because `START.md` "Past
mistakes" is explicit that an item routed forward without a named owner dies and this cycle's
fence bars the kanban DB.

**I re-derived the population before writing it** (`BUILD.md` `## Claims are proven
mechanically`), and it did not reproduce. My resolver: for every `spec-<NNN>` mention in tracked
`.py`, take the ordinal that follows it on the same line — either a `KEYWORD N` phrase
(`Decision 7`, `DoD 4`, `Slice 2`, `scenario 4`) or a bare label token (`Md1`, `P1-B`, `P3a`,
`L3-1`, `H4`, `SR-3`, `D4-D5`) — and resolve it against that spec's own live text, accepting the
en-dash twin of any hyphenated form. Population **437** tracked `.py` files, **972** such
citations examined, **909** resolved. The unresolved remainder was then graded **by reading**,
which is where two corrections come from:

- **Over-report.** `spec-044 D4-D5` (`tests/extensions/test_debug.py #"Deliberate test rules
  (spec-044 D4-D5):"`) **resolves.** spec-044 ships `- [ ] **D4** — the two wire serializers are
  module-level functions` and `- [ ] **D5** — every remaining debug rule is single-sited` under
  its DRY-obligations section, and the spec writes the range itself as `D4–D5` with an **en
  dash**. The source spells it `D4-D5` with an ASCII hyphen because `AGENTS.md` requires
  ASCII-only `.py` source. So that resolver was comparing an ASCII hyphen against an en dash —
  the same class of instrument-reach failure this round has now hit at four different widths.
  Removed from the stranded set.
- **Under-report, by a wide margin.** Worker 3's 16 is 14 `Md<n>` + 1 spec-044 (above) + 1
  spec-048. The graded stranded population is **38 occurrences over 22 files in 7 spec
  vocabularies**, of which **5** (`spec-030 P1-B`) are already homed by catalog items 1-2, so
  **33 are new**.

Graded stranded set, measured as this line was written:

| Vocabulary | Occurrences | In that spec's live text | In its companion |
| --- | --- | --- | --- |
| `spec-039 Md1` / `Md2` / `Md3` / `Md4` / `Md5` / `Md7` | **14** | 0 | 0 |
| `spec-039 M1a` | **4** | 0 | 0 |
| `spec-039 H4` | **1** | 0 | 0 |
| `spec-039 SR-3` | **1** | 0 | 0 |
| `spec-030 P1-B` | **5** | 0 | 5 (rationale) |
| `spec-030 P3a` / `P3b` | **2** | 0 | 7 (rationale) |
| `spec-036 L3-1` / `M3-1` / `FV-1` | **4** | 0 | 0 |
| `spec-011 Decision 4` / `Decision 7` | **4** | 0 (spec-011 has **no** Decision section) | 0 |
| `spec-016 Decision 4` | **1** | 0 (spec-016 has **no** Decision section) | 0 |
| `spec-043 scenario 4` | **1** | 0 in any case | 0 |
| `spec-048 D1` | **1** | 0 | 0 |
| **`spec-038 P<N>`** | **0** | — | — |

spec-038's row is **0** under a second, independent instrument — the round's fix confirmed
without reusing the census that scoped it.

Four groups the resolver flagged and reading cleared, recorded so the next reader does not chase
them:

- **`TODO(spec-050 slice 1..5)` — 22 occurrences, not defects.** `AGENTS.md` explicitly keeps
  live `TODO(spec-NNN slice N)` anchors, and every one resolves against spec-050's own
  `Slice 1`..`Slice 5`. The resolver missed them only on **case**.
- **`spec-028 DoD 4(c)` — 2 occurrences, true.** spec-028's `## Definition of done` is a numbered
  list whose item 4 sub-item (c) is `**NO ``apply(...)`` dispatcher**`, exactly what
  `orders/sets.py` cites. The literal string `DoD 4` is absent because the spec numbers with
  `4.`; this is `START.md`'s "Bare `Decision N` / `DoD N` = repo-wide convention, not defect",
  graded by anchor presence.
- **`spec-044 Test plan 1-7`** — the `## Test plan` section exists and the ordinal is a range over
  its rows, so the reader's path is established. Same convention case.
- **`spec-099-example-0_0_9` — 4 occurrences, fixture data.** A deliberately nonexistent spec path
  in `apps/glossary/tests/test_import_spec_terms.py`. The false-positive class a pattern cannot
  distinguish from its target; excluded by reading.

**Which instrument found what, so nobody re-runs a blind one.** Four instruments have now been
pointed at this defect class and each has its own blind spot — which is the standing lesson this
finding illustrates: **a census glob can have more than one blind spot**, and there is no reason
to expect the second to be the last.

- Worker 0's `\bP[123]\b` could not see a suffixed label (`P4`, `P1.6`, `P2-3`, `P1-B`).
- The plan's `\bP[0-9]+(?:[.\-][0-9A-Za-z]+)?\b` fixed that and still cannot see a non-`P`
  vocabulary (`Md1`, `L3-1`, `D1`) **nor** a letter-suffixed one — `P3a` / `P3b` fail its
  trailing `\b` outright, so those two sites were invisible to the very census that certified
  spec-030's, even though `P1-B` in the same vocabulary was caught.
- Worker 3's `spec-<NNN> <ordinal>` resolver reached the `Md<n>` family but compared literal
  strings, so an en-dash range read as unresolved (`spec-044 D4-D5`), and it did not reach
  `M1a` / `H4` / `SR-3` or the `Decision N`-into-a-spec-with-no-Decisions cases.
- **This resolver's own blind spot, stated rather than left for the next reader:** it requires
  the spec stem and the ordinal on **one line**. Every bare ordinal whose spec is named elsewhere
  in the file — precisely catalog items 3, 4 and 5 (`spec-033 P2-3`, `spec-032`'s `the P1 bug`,
  the three unattributable ones) — is invisible to it. It and the P-label census are
  complementary; neither alone is the population.

### Medium 2 — corrected: the 111/435 -> 110/437 difference is instrument, not physical growth

**Disposition: corrected here.** A prior build report is never edited, so the correction lives in
this section. **I withdraw the prior pass's explanation.** Its `### Retirement proof` said "the
corpus itself grew" and its `### Notes for Worker 1` item 3 said "stale by growth, not by error"
while asking for no artifact change. Both are wrong. There is no stale figure, and **the
stale-figure item routed to Worker 1 is dropped** — there are two instruments measuring two
different populations, and nothing for the custodian to normalize except the instrument names.

Measured this pass:

| Reading | Instrument | Value |
| --- | --- | --- |
| package `.py` | `git ls-files 'django_strawberry_framework/*.py'` | **110** |
| package `.py` | `Path("django_strawberry_framework").rglob("*.py")` | **111** |
| corpus `.py` | `git ls-files '*.py'` | **437** |
| corpus `.py` | `rglob` over the four trees | **435** |

The plan's 111 and 435 are `rglob` readings and both still reproduce; the prior pass's 110 and
437 are `git ls-files` readings. The whole delta is one **untracked** file the concurrent session
added (`django_strawberry_framework/utils/canonical.py`, counted by `rglob`, invisible to
`git ls-files`) plus three tracked root-level `.py` files outside the four trees (`conftest.py`,
`docs/dry/export_dry_review.py`, `line_count.py` — the reverse direction). Independent
corroboration from a gate with no stake in it: `scripts/check_citations.py --check` printed
`435 .py files` again this pass, from its own four-tree `rglob`.

**The tell was there to be read and the prior pass did not read it:** a package count that
**fell** (111 -> 110) cannot be explained by growth, and that decrement was published in the same
paragraph as the growth story. The occurrence counts never depended on it — 43 package, 72
corpus, 40 after, all reproducing exactly — which is precisely why the false cause could ride
along unchallenged. `START.md` "state PATTERN as parameter of any published figure" is the rule;
every population figure in this section names its instrument.

### Deferred work catalog input (Worker 2 — apply-changes pass)

Input to `bld-final.md`'s `### Deferred work catalog`, additive to the plan's six items. Every
entry carries the sites, the instrument that found it, the instrument that missed it, and a named
owner in prose. **33 new stranded-ordinal occurrences** across seven items; the counts were
measured as these lines were written, by the resolver described under Medium 1, and are
re-derivable by re-running it and asserting spec-038's row stays at 0.

7. **`spec-039`'s `Md<n>` label vocabulary is stranded in 14 shipped sites.** `spec-039 Md1` x3 —
   `django_strawberry_framework/forms/inputs.py #"(spec-039 Md1), shared with the"`,
   `rest_framework/inputs.py`, `utils/inputs.py::guard_dropped_required`; `Md2` x3 —
   `mutations/resolvers.py`, `rest_framework/resolvers.py`, `utils/querysets.py`; `Md3` x2 —
   `rest_framework/resolvers.py`, `utils/querysets.py`; `Md4` x2 — `utils/querysets.py` (both);
   `Md5` x1 — `rest_framework/inputs.py`; `Md7` x3 — `forms/sets.py`,
   `mutations/sets.py::construction_kwargs`, `rest_framework/sets.py`.
   `docs/SPECS/spec-039-serializer_mutations-0_0_13.md` carries **0** `Md<n>` occurrences, its
   `-terms.csv` companion 0, and `git show HEAD:` of the spec 0 — so these were **never** labels
   there and are false already, independently of this cycle. `Md<n>` appears once in all tracked
   `.md` and that one occurrence is itself a citation, not a definition. **Found by** the
   `spec-<NNN> <ordinal>` resolver (Worker 3's, re-derived here). **Missed by** the plan's
   `\bP[0-9]+(?:[.\-][0-9A-Za-z]+)?\b` census, which structurally cannot match a non-`P` prefix —
   which is why the plan's out-of-scope table certified spec-039's citations as resolving. That
   certification is true of the `P<N>.<M>` labels it measured and **not** of this vocabulary.
   **Owner: the maintainer**, onto a `spec-039` follow-up card; spec-039's own residual cycle has
   not run, so its vocabulary sweep is the natural home. This round's fence bars KANBAN and the
   kanban DB, so prose is the only home available from inside it.
8. **`spec-039` carries three further stranded ordinals in vocabularies nobody has swept.**
   `M1a` x4 — `forms/resolvers.py`, `mutations/resolvers.py` x2, `rest_framework/resolvers.py`;
   `H4` x1 — `rest_framework/resolvers.py #"for a serializer-only relation - spec-039 H4"`;
   `SR-3` x1 — `tests/rest_framework/test_converter.py`. Zero occurrences of each in spec-039 and
   its companion. `H4` and `SR-3` read as review-severity labels, which `START.md` "Style Rio
   cares about" bars from standing prose outright, so the fix is content restatement rather than
   a spelling repair. **Found by** the resolver here; **missed by** both the P-label census
   (wrong prefix) and Worker 3's pass (not enumerated). **Owner: the maintainer**, the same
   `spec-039` follow-up card as item 7 — they must move together so spec-039's retirement can be
   proved at 0 rather than half-fixed.
9. **Two more `spec-030` sites, in a letter-suffixed spelling both prior instruments were blind
   to.** `tests/test_connection.py #"(``spec-030-connection_field-0_0_9`` P3a)"` and
   `tests/test_registry.py #"cycle-safe local import (``spec-030-connection_field-0_0_9`` P3b)"`.
   spec-030 carries **0** `P3a` / `P3b` (its rationale companion carries 4 and 3) — the identical
   shape as the `P1-B` pair in catalog items 1-2. **Found by** the resolver here. **Missed by**
   the plan's census for a mechanical reason worth recording: `\bP[0-9]+...\b` cannot match `P3a`
   at all, because no word boundary exists between `3` and `a` — so the census that *did* catch
   `P1-B` in the same file family was structurally incapable of catching these. **Owner: the
   maintainer**, folded into catalog items 1-2's `spec-030` card so all seven sites retire in one
   pass.
10. **`spec-036`'s `L3-1` / `M3-1` / `FV-1` are stranded, and two of the three are banned
    severity labels.** `mutations/inputs.py #"never indexed as a decode-able FK (spec-036 L3-1)"`,
    `utils/relations.py::is_forward_concrete_relation #"(spec-036 L3-1)"`,
    `mutations/sets.py #"FK-to-field-name reversal, spec-036 M3-1"`,
    `tests/mutations/test_resolvers.py #"(spec-036 FV-1)"`. spec-036's live label vocabulary is
    `AR-H4` / `AR-M1` / `AR-M3` / `Major-2` / `Medium-1`; it carries **0** `L3-1`, `M3-1`, `L3` or
    `FV`. `L<n>` / `M<n>` are Low / Medium review-round labels with a round index, exactly what
    `START.md` bars from standing prose. **Found by** the resolver here; **missed by** the P-label
    census (wrong prefix). **Owner: the maintainer**, a `spec-036` follow-up card. spec-036's
    residual cycle has already run and left these, which is the argument for catalog item 6's
    gate rather than another manual sweep.
11. **Four `spec-011` citations are a renumber artifact a closed cycle already recorded, and still
    live.** `types/base.py #"``_validate_interfaces`` (spec-011 Decision 4)"`, `types/base.py` x2
    `#"(spec-011 Decision 7 #"` (the connector-column docstring and the matching inline comment),
    and `types/resolvers.py #"# FK-id elision (spec-011 Decision 7)"`.
    `docs/SPECS/spec-011-stale_placeholder_cleanup-0_0_4.md` is a 3,430-byte stub with **no
    Decision section at all**; the true target is
    `docs/SPECS/spec-015-relay_interfaces-0_0_5.md`, whose `### Decision 4: validation` and
    `### Decision 7: optimizer and projection invariants` are exactly what the sites mean and
    which carries the quoted substring (spec-015 line 340; spec-011 carries it 0 times).
    **Prior art, named so this is not re-derived a third time:**
    `docs/builder/DONE/build-015-relay_interfaces-0_0_5.md` finding **F14** records the whole
    class — a commit renamed `spec-011-relay_interfaces-0_0_5.md` to `spec-015-...` without
    sweeping citations — and puts it at 8 sites. Re-measured here: **still exactly 8** `spec-011`
    occurrences in tracked `.py` (the 4 ordinal ones above plus `types/base.py` x2
    substring-only, `tests/filters/test_sets.py`, `tests/types/test_base.py`), so F14 was
    catalogued and never actioned. **Owner: the maintainer** — F14 lives in a `DONE/` plan, and an
    item whose only home is a closed cycle's artifact is the "routed forward without a named
    owner" failure `START.md` names; this entry re-homes it.
12. **`spec-016 Decision 4` is stranded.**
    `examples/fakeshop/test_query/test_library_api.py #"Pins the end-to-end contract (spec-016
    Decision 4,"`. `docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md` carries **0** Decision
    headings, so the ordinal names nothing. **Found by** the resolver here; **missed by** the
    P-label census (not a `P` label) and by Worker 3 (not enumerated). **Owner: the maintainer**,
    a `spec-016` follow-up card — or, if the correct target turns out to be another spec, the same
    renumber-artifact treatment item 11 needs.
13. **`spec-043 scenario 4` and `spec-048 D1` are stranded, one site each.**
    `examples/fakeshop/test_query/test_products_api.py #"spec-043 scenario 4: ``TestClient.login()``
    scopes write auth to the bracket."` — spec-043 carries no `scenario 4` in any case.
    `examples/fakeshop/test_query/test_uploads_api.py #"publishes ``path`` in the live schema
    (spec-048 D1)."` — spec-048 and its companion carry **0** `D1`. Note the first sits in a file
    **this round edited**, in a docstring, and was deliberately not touched: it is spec-043's
    vocabulary, not spec-038's. **Found by** the resolver here (spec-048 also by Worker 3);
    **missed by** the P-label census. **Owner: the maintainer**, one follow-up card each against
    `spec-043` and `spec-048`.

**The structural remedy is catalog item 6's gate, not a fifth sweep.** Four instruments, four
blind spots, and the graded population moved 11 -> 41 -> 16 -> 38 across them. `START.md` "Rule
w/o gate rots" says the root-cause fix is the missing gate rather than the sites, and the policy
call that gate needs — which ordinal vocabularies are legitimate, and whether `Decision N` /
`DoD N` / `TODO(spec-NNN slice N)` stay permitted, which the readings above show they should — is
the maintainer's.

### Failability proofs

**Ruling: no forward failability proof is owed; the inverse proof is, and it is recorded here.**
`BUILD.md` `### What needs a proof, and what does not` scopes the obligation to a new boundary,
guard, gate, or rejection path and exempts doc edits. This pass changes **one docstring line** —
measured, not asserted: the docstring-stripped AST digest below is IDENTICAL, which is the
mechanical statement that no executable line moved.

- **Inverse proof — AST identity with docstrings stripped.** Reference: the **pre-edit pristine
  copy** at `<scratchpad>/pristine2/django_strawberry_framework_forms_inputs.py`, taken before any
  edit and `cksum`-equal to the working-tree file at that moment. **Not `git show HEAD:`** — this
  file carries a concurrent session's uncommitted executable changes, so a HEAD comparison would
  report their diff as mine. Script: `<scratchpad>/ast_identity_pass2.py` (the plan's validated
  digest: strip the leading string-constant `Expr` from every `Module` / `FunctionDef` /
  `AsyncFunctionDef` / `ClassDef` body, then `ast.dump(..., include_attributes=False)`).
  **Result: `IDENTICAL django_strawberry_framework/forms/inputs.py`, files compared 1, diverged 0,
  exit 0.**
- **Controls run FIRST, and the executable one fires.** `START.md`: a control that cannot fail is
  equivalent to a passing proof, and a control that did not run is equivalent to one that passed.
  All three mutate a copy **in memory** and never a repository file; each asserts its anchor
  occurs exactly once and aborts with exit 2 otherwise.

| Control | Mutation | Result | Reading |
| --- | --- | --- | --- |
| 1 — **the control that must fail** | executable `CREATE_SHAPED_KINDS: frozenset[str]` -> `CREATE_SHAPED_KINDS_X: frozenset[str]` (anchor asserted to occur exactly once) | **`DIVERGED`, diverged 1, exit 1** | correct; the digest catches any executable change, so the IDENTICAL result above is a measurement and not a vacuous one |
| 2 — docstring blindness | docstring text `request-independent stable field shape` -> uppercased | `IDENTICAL`, exit 0 | correct; the digest is deliberately blind to docstring text, which is what makes it the right instrument for this edit |
| 3 — comment blindness | comment text `# Decision 7). The bind keys on it` -> uppercased | `IDENTICAL`, exit 0 | correct; comments are absent from the AST |

**The abort guard fired before control 1 did, and that is the recorded near-miss.** The first
control aimed at `_FORM_INPUT_KIND_SCALAR`, which occurs **0** times in this file; the harness
printed `ABORT: control anchor is not unique; the control could not fire` and exited **2** rather
than printing IDENTICAL. That is the same failure the prior pass hit on
`_ALLOWED_PLAIN_FORM_META_KEYS =`, in a different file with a different anchor — a harness without
the uniqueness assert would have reported a passing proof both times. The anchor was then
re-derived from the file itself and asserted unique before use.

No mutation was ever applied to a repository file, so no revert was needed and none was performed.
Post-gate check: all three control anchors still occur exactly once in the working tree, and the
working tree's only delta versus the pristine copy is the 3-line docstring diff.

### Hot-path budget

**Not applicable; zero executable lines.** Nothing runs per request, per resolver, per row, per
connection, or per outbound message, because nothing new runs at all: one docstring line joined to
its predecessor, corroborated by the docstring-stripped AST digest being IDENTICAL with its
executable control firing.

### Floor verification

**Not applicable; plan declares floor-verification scope `none`,** and this pass touches no
integration seam on any version because it changes no executable line. For the record, read this
pass rather than recalled: the supported floor is Django **5.2.16** on Python **3.10** with
strawberry-graphql **0.316.0** (`BUILD.md` `## Floor verification`, the single canonical
statement). The shared `.venv` is **not** the floor and carries, per `uv pip list` this pass:
`django 6.1`, `strawberry-graphql 0.324.0`, `channels 4.3.2`, `djangorestframework 3.18.0`, on
Python **3.14.2**. No floor venv was built; the shared `.venv` was not mutated.

### Implementation notes

- **The join was applied as a three-line anchor**, not a two-line one, so the following line
  (the `` ``get_form_fields(cls)`` classmethod`` sentence) was part of the match and is provably
  unmoved. A two-line anchor would have left the same bytes, but the diff could not then
  distinguish "joined" from "joined and re-wrapped".
- **Line length was re-measured against the whole file, deliberately, and that is safe here.** The
  prior pass's rule — measure only the changed lines, because a whole-file measure reports 48
  pre-existing long lines across the 8 files — does not bite for this file: it carries **0** lines
  over 99 and its longest is exactly **99**. So the whole-file measure is the stronger statement
  in this one case, and it was taken.
- **The two paragraph-final short lines in `forms/sets.py` were not touched.** Worker 3's ruling
  is right on the mechanism: a wrapped prose paragraph's last line is short by construction, and
  joining one would be a change with no defect behind it.

### Notes for Worker 3

- **Read the diff against `<scratchpad>/pristine2/`, not `git diff`.** `forms/inputs.py` is
  baseline-dirty with a concurrent session's executable work, so `git diff` on it is mixed.
  Against the pristine copy this pass is **2 removed + 1 added** lines and nothing else.
- **The one proof to re-run is control 1**, the executable mutation: if
  `CREATE_SHAPED_KINDS: frozenset[str]` -> `CREATE_SHAPED_KINDS_X` does not print `DIVERGED` and
  exit 1, the IDENTICAL real result means nothing. Controls 2 and 3 are supposed to print
  IDENTICAL. `<scratchpad>/ast_identity_pass2.py` takes the reference directory as `argv[1]` and
  `real` or `control <anchor> <replacement>` after it.
- **The Medium-1 population is 38, not 16, and `spec-044 D4-D5` is not one of them.** If you
  re-run your resolver, accept the en-dash twin of a hyphenated range before grading a range
  unresolved — spec-044 writes `D4–D5` and ASCII-only `.py` source cannot. This resolver's own
  blind spot is stated under Medium 1: it needs the spec stem and the ordinal on one line, so it
  cannot see catalog items 3-5 at all.
- **`scripts/check_citations.py` green is still not evidence for this round** (`::Symbol`-only).
  Its `435 .py files` line is, however, direct third-party corroboration of the Medium-2
  correction.
- The four full-sweep failures earlier passes recorded remain gone: 0 failed / 7268 passed / 40
  skipped, identical to the prior pass, 0 collection errors.

### Notes for Worker 1 (spec reconciliation)

No spec amendment is required by this pass. Three items, all routed on disk:

1. **Withdraw the prior pass's routed item 3.** There is no stale figure. Do **not** restate the
   plan's 111 / 435 as stale: both reproduce live under `rglob`, and 110 / 437 is `git ls-files`.
   If you normalize population figures across this cycle's artifacts, normalize on the
   **instrument name**, not on the number. The prior pass's physical-growth cause is withdrawn in
   `### Medium 2` above; a package count that fell cannot be explained by growth.
2. **Narrow the plan's spec-039 certification when you touch it.** It lives in `### Partition: in
   scope / out of scope / ambiguous-then-resolved`, the out-of-scope table's `spec-039` row, whose
   current wording is "Every one names `spec-039` on its own line. ... so each citation
   **resolves**. Not a defect." That is true of the `P<N>.<M>` labels the census measured and
   false of spec-039's `Md<n>` / `M1a` / `H4` / `SR-3` citations, which resolve against nothing.
   **Recommended replacement:** "Every one names `spec-039` on its own line, and each of the
   **`P<N>.<M>`** labels resolves against spec-039's 113 live P-label occurrences. Not a defect.
   This certification covers the `P` vocabulary only — spec-039's `Md<n>` / `M1a` / `H4` / `SR-3`
   citations resolve against nothing and are catalogued." The entries are items 7-8 above.
3. **The prior pass's routed item 1 stands unchanged** — `fix` -> `case` in the spec's
   `### Decision 7` parenthetical `#"(the kwarg-requiring-form fix)"`. Nothing in source depends
   on it, and the docstring this pass reflowed is the very one whose deletion of that phrase was
   at issue: the reflow does not touch it.

---

## Review (Worker 3 — re-review)

**This pass is a resumption, not a second review** (`docs/builder/BUILD.md`
`### Recovery from interrupted subagent runs`). A prior invocation of this role completed the
same re-review's verification work and was killed before writing its section; it wrote nothing to
disk and left no live source mutation. Every finding and figure below was derived in this pass,
from the artifact and the tree, with its own instruments. Scope is the apply-changes diff only —
one file, one docstring line join. Everything the prior `## Review (Worker 3)` accepted stays
accepted and was not re-opened.

**Reference discipline.** `django_strawberry_framework/forms/inputs.py` is baseline-dirty with a
concurrent session's executable work, so `git show HEAD:` cannot say what Worker 2 changed — it
would report their diff as this round's. I used the same pre-edit pristine copy Worker 2 recorded,
after proving it is the right reference rather than accepting it: it is byte-identical (`cksum`
`2048820725 38632`) to the pass-1 worktree snapshot the prior review took at 16:48, and the live
file's whole delta against it is the 3 lines below. No `git stash` / `checkout` / `restore` /
`worktree` at any point.

```
diff <pristine2>/django_strawberry_framework_forms_inputs.py django_strawberry_framework/forms/inputs.py
179,180c179
<     discoverable, request-independent stable field shape (spec-038 Decision 7).
<     The overridable
---
>     discoverable, request-independent stable field shape (spec-038 Decision 7). The overridable
```

**2 removed + 1 added, in 1 file, and nothing else in the tree is this pass's.** The other 7
target files are byte-identical to the pass-1 snapshot (`0` changed lines each, measured
file-by-file), which is the mechanical statement that the apply-changes pass touched one file and
that no concurrent write landed in any of the 8 since. Live file 38,628 bytes against pristine
38,632: the join drops a newline plus four indent spaces and inserts one space, net -4, and no
character of either fragment changed — so this is a reflow and not also a reword.

### High:

None.

### Medium:

#### One catalogued stranded citation is a false positive: `spec-043 scenario 4` resolves

`examples/fakeshop/test_query/test_products_api.py::test_create_item_login_bracket_via_test_client #"spec-043 scenario 4: ``TestClient.login()`` scopes write auth to the bracket."`,
catalogued at `docs/builder/bld-038-review-1-citation_residue.md`
`### Deferred work catalog input (Worker 2 — apply-changes pass)` item 13.

Item 13 grades this site stranded on the ground that "spec-043 carries no `scenario 4` in any
case." The literal string is indeed absent — and the ordinal resolves anyway.
`docs/SPECS/spec-043-test_client-0_0_14.md` `## Test plan` opens
`#"The numbered scenarios below are the behaviours this card must prove"`, splits them as
`#"**Sync request shapes (scenarios 1–5)**"`, and numbers the list `1.`…`5.`, where item 4
reads
`#"4. **`login()` scoping.** `seed_data(1)`, a write-auth-gated products"` and continues
`#"denied anonymous (top-level error), succeeds inside"` / `#"`with client.login(user_with_perm):`, denied again after the block"`.
The citing docstring is a near-verbatim restatement of exactly that row. So `spec-043 scenario 4`
names a real, findable contract and is not a defect.

**Why it matters, and why it is Medium rather than Low.** This is the same string-comparison
failure Worker 2 correctly caught one row earlier in the same grading pass: `spec-028 DoD 4(c)`
was cleared with the explicit reasoning "The literal string `DoD 4` is absent because the spec
numbers with `4.`", and `spec-044 Test plan 1-7` was cleared on the identical convention. The
structurally identical spec-043 case was graded the other way in the same section, so the
published population is wrong and one catalog row would route a non-defect to the maintainer as
work. `BUILD.md` `## Claims are proven mechanically` fixes Medium for a published count that does
not survive re-derivation, and `START.md` "Bare `Decision N` / `DoD N` = repo-wide convention, not
defect. Grade by ANCHOR presence, never distance" is the rule the row misapplies.

**Corrected population, measured as this line was written** (instrument and controls under
*What looks solid*): strike the `spec-043 scenario 4` row and the graded stranded set is
**37 occurrences over 21 files in 6 spec vocabularies**, of which 5 (`spec-030 P1-B`) are already
homed by catalog items 1-2, so **32 new** — not 38 / 22 / 7 and 33. Every other row reproduces
exactly, per-token and per-file.

**Recommended change — no source edit, and no Worker 2 re-pass.** The catalog lands in Worker 1's
`bld-final.md`, and a prior build report is never edited, so Worker 2 could only restate this in a
third report. Routed to Worker 1 under `### Notes for Worker 1 (spec reconciliation)` with an
`Escalated:` prefix: drop the `spec-043` half of item 13, keep the `spec-048 D1` half, and carry
37 / 21 / 6 and 32-new. Re-derivable by the per-token census in *What looks solid*.

### Low:

#### Item 11's prior-art clause is wrong: F14 is already homed on a live card

`docs/builder/bld-038-review-1-citation_residue.md`
`### Deferred work catalog input (Worker 2 — apply-changes pass)` item 11, the clause
#"F14 lives in a `DONE/` plan, and an item whose only home is a closed cycle's artifact is the".

Item 11's measurements are all right (verified below), but its account of the prior art is not.
`docs/builder/DONE/build-015-relay_interfaces-0_0_5.md` does not leave F14 in the plan: it says
#"already homed on a live card" and #"F14's `[spec-011]` cluster stays on", and the bullet is live
in the board today at `KANBAN.md #"The `[spec-011]` renumber artifact reaches six live-code sites"`
— under `### [TODO-ALPHA-051-0.0.15 - Upstream parity-gap closure]`'s successor card
`TODO-ALPHA-053-0.0.15 - Boundary hardening and system-wide DRY squeeze` (card heading at
`KANBAN.md:301`, bullet at `:341`), whose text carries the same 8-occurrences-across-4-files
population with per-file counts **and** a re-derivation trap the catalog entry does not carry
forward (`git grep -oh '\[spec-011\]' | wc -l` reports **9**, the extra row being git's
`Binary file examples/fakeshop/db.sqlite3 matches` line). A second card carries the documentation
half (`KANBAN.md:582`, which also states #"The six package-source and test occurrences are carried
by `TODO-ALPHA-053-0.0.15`").

Low rather than Medium: the owner named (the maintainer) is not wrong, the entry does not lose the
item, and re-homing an already-homed item is duplication rather than loss. But a reader acting on
item 11 as written would create a second card for scheduled work and would re-derive a population
whose counting trap is already recorded. Item 11 is also the **only** one of items 7-13 in this
position — I checked the board for every other catalogued token (`Md1`, `Md7`, `M1a`, `L3-1`,
`M3-1`, `FV-1`, `P3a`, `P3b`, `SR-3`, `spec-016 Decision`, `scenario 4`, `spec-048 D1`, `P1-B`):
**0** hits each in `KANBAN.md`, against a live control of **8** for `spec-011`. So the rest of the
catalog's "not homed anywhere" premise holds; this one entry is the exception.

**Recommended change:** replace the orphanhood clause with a pointer at the live card, and keep
the entry (its value is the re-measurement, not the re-homing). Routed to Worker 1 with the
Medium above.

### DRY findings

None. This pass changes one docstring line and adds zero executable lines, so it can introduce no
duplicated logic, no repeated literal, and no near-copy. No existence challenge: nothing was
abstracted.

The prior review's DRY findings (`None`, with the shared-wording decisions re-measured) are
untouched by a line join and were not re-opened.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty**: `__all__` and the re-export
list are unchanged. No new public exports.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. The apply-changes diff
is one package-source docstring line; the artifact itself is this cycle's own scratchpad.

### What looks solid

**Prior-finding dispositions, one line each.**

| Prior finding | Disposition |
| --- | --- |
| **Low** — the orphaned 19-column `#"The overridable"` line | **closed cleanly.** Merged line 95 columns, file's longest exactly **99**, **0** lines over 99, `ruff format --check` clean, and the diff is 2 removed + 1 added with every other byte of the file identical |
| **Low** — `forms/sets.py::DjangoFormMutation._validate_meta #"two-base split)."` (paragraph-final) | **correctly left alone.** Still present at **26** columns, file byte-identical to the pass-1 snapshot |
| **Low** — `forms/sets.py::DjangoFormMutation.build_input #"decode."` (paragraph-final) | **correctly left alone.** Still present at **15** columns, same file, same proof |
| **Low** — `forms/resolvers.py::_reconstruct_partial_data #"from the located row. A file field"` (ordinary wrap) | **correctly left alone.** Still present at **64** columns, file byte-identical to the pass-1 snapshot |
| **Low** — the "inside the E501 grace" clause | **correctly corrected**, and accepted without repetition: 11 of the 48 pre-existing long lines pass on `pyproject.toml [tool.ruff.lint.per-file-ignores]`, not the 110 grace. Re-measured: `examples/fakeshop/apps/products/schema.py` longest **137**, **11** lines over 99 |
| **Medium 1** — the 16 stranded ordinal citations | **correctly catalogued, with one false-positive row** (the Medium above). Owners named in prose at all seven items; no source edited; the exoneration is right |
| **Medium 2** — instrument vs physical growth | **correctly corrected, and the withdrawal is explicit**, not merely superseded |

**The `spec-044 D4-D5` exoneration is exactly right, and doubly so.** Verified independently of
Worker 2's resolver. `docs/SPECS/spec-044-debug_extension-0_0_14.md` ships
`#"- [ ] **D4** — the two wire serializers are **module-level functions**, not"` and
`#"- [ ] **D5** — every remaining debug rule is **single-sited inside"`, and writes the range
itself with an **en dash** at two sites (`#"inside `debug.py` itself (D4–D5), (b) conformance with the package's established"`
and `#"([DRY D4–D5](#helper-reuse-obligations-dry)): assertions re-spell the wire"`). Measured:
ASCII `D4-D5` in the spec **0**, en-dash `D4–D5` **2**, `**D4**` **1**, `**D5**` **1**, bare `D4`
**7**, bare `D5` **4**, control `D9` **0**. The citing source
(`tests/extensions/test_debug.py #"Deliberate test rules (spec-044 D4-D5):"`) carries the ASCII
hyphen **1** time, the en dash **0**, and `str.isascii()` on the whole file is `True` — the
`AGENTS.md` ASCII-only `.py` rule is what forces the spelling, so a literal-string resolver was
comparing a hyphen against an en dash. Second, independent ground the entry does not claim: even
with no en-dash allowance, `spec-044` is on the line and both `D4` and `D5` exist as labels, so
`START.md` "grade by ANCHOR presence, never distance" clears it too. **A citation was correctly
returned to the resolving set.**

**The graded stranded population, re-derived per token rather than by re-running the resolver.**
Instrument: for each catalogued `(spec, token)` pair, count occurrences of the token on any line
naming that spec, over the **437** tracked `.py` files (`git ls-files '*.py'`), with a
`uv run python - <<'PY'` heredoc that prints its population and asserts it. Every one of the 20
rows reproduced Worker 2's count exactly, file-for-file:

- `spec-039`: `Md1` 3, `Md2` 3, `Md3` 2, `Md4` 2, `Md5` 1, `Md7` 3, `M1a` 4, `H4` 1,
  `SR-3` 1 = **20**
- `spec-030`: `P1-B` 5, `P3a` 1, `P3b` 1 = **7**
- `spec-036`: `L3-1` 2, `M3-1` 1, `FV-1` 1 = **4**
- `spec-011`: `Decision 4` 1, `Decision 7` 3 = **4**; `spec-016 Decision 4` **1**;
  `spec-043 scenario 4` **1** (the false positive); `spec-048 D1` **1**

Totals as published: **38 occurrences, 22 distinct files, 7 distinct spec vocabularies**, 5 already
homed, **33 new** — all four reproduce. **Corrected for the false positive: 37 / 21 / 6 and 32
new.** Each token's absence from its named spec was confirmed the other way too: `Md1`…`Md7`,
`M1a`, `H4`, `SR-3` are **0** in spec-039 and it has no rationale companion, while spec-039's real
label vocabulary is `F1`/`F6`/`F8`/`F9`/`F10`/`F11`/`M4`/`G2`/`P3`; `L3-1`/`M3-1`/`FV-1` are **0**
in spec-036 against its live `AR-H4` 14 / `AR-M1` 10 / `Major-2` 7 / `Medium-1` 3;
`P3a`/`P3b` are **0** in spec-030 and **4** / **3** in its rationale companion, the same shape as
`P1-B`'s 0 / 5; `spec-011` carries **0** occurrences of the string `Decision` in its whole
3,430-byte body; `spec-016` has **0** Decision headings; `spec-048` carries **0** `D1`. The
renumber target checks out: `docs/SPECS/spec-015-relay_interfaces-0_0_5.md` has both
`### Decision 4` and `### Decision 7` and carries `_validate_interfaces` **1** time where spec-011
carries it **0**.

**Item 11's 4-vs-8 is subject, not drift — and item 11 states both subjects, which is what makes
it right.** Enumerated every `spec-011` occurrence in tracked `.py`: **8**, at
`types/base.py` x5, `types/resolvers.py` x1, `tests/filters/test_sets.py` x1,
`tests/types/test_base.py` x1 — file-for-file identical to F14's recorded population in
`docs/builder/DONE/build-015-relay_interfaces-0_0_5.md` and to the board bullet's per-file counts.
Of those 8, exactly **4** carry an ordinal (`(spec-011 Decision 4)` at `types/base.py:1241`;
`(spec-011 Decision 7 …)` at `:1854` and `:1975`; `# FK-id elision (spec-011 Decision 7)` at
`types/resolvers.py:650`); the other 4 are two `spec-011 #"substring"` citations
(`types/base.py:1108`, `:1110`), one bare `(spec-011)` (`tests/filters/test_sets.py:550`), and one
`spec-011-era` prose mention (`tests/types/test_base.py:535`). So **the population did not move,
the instruments differ in subject, and neither count is wrong**: F14 counts every mention of a
renumbered spec (all 8 are the renumber artifact), this catalog counts the ones whose ordinal
resolves against nothing (4). This is `START.md` "Count right in every digit, wrong in SUBJECT",
and item 11 avoids it by publishing both figures with their populations enumerated. Its
"still exactly 8, never actioned" is true. Only the orphanhood clause is wrong (the `Low` above).

**All four of Worker 2's read-cleared exclusions hold, spot-checked individually.**

- **`TODO(spec-050 slice N)` — 22 occurrences, correctly excluded.** Measured 22 across 13 files
  (`utils/querysets.py` 6, `list_field.py` 3, `resource_policy.py` 3, ten more at 1 each), citing
  slice numbers 1-5 only, and `docs/spec-050-list_field_arguments-0_0_15.md` carries
  `Slice 1`..`Slice 5` (2/1/2/2/9 occurrences) and no `Slice 6`. `AGENTS.md` rule 26 requires a
  staged anchor to name its doc and slice, so these are the form the rule mandates, not residue.
- **`spec-028 DoD 4(c)` — 2 occurrences, correctly excluded.** Both in
  `django_strawberry_framework/orders/sets.py`. spec-028's `## Definition of done` item 4 sub-item
  (c) reads verbatim `#"(c) **NO ``apply(...)`` dispatcher** (dropped — the filter side's"`,
  which
  is precisely what both sites cite. Anchor present, target findable.
- **`spec-044 Test plan 1-7` — correctly excluded, and it resolves more exactly than the entry
  claims.** The one site is `examples/fakeshop/test_query/test_debug_extension_api.py`'s module
  docstring, and spec-044's `## Test plan` says
  `#"Scenarios 1–7 live in"` / `` #"`examples/fakeshop/test_query/test_debug_extension_api.py`; scenarios 8–15" ``
  — it names that exact file for scenarios 1–7. Note the spec writes `1–7` with an en dash
  and the
  source `1-7` with a hyphen: the same class as the `D4-D5` exoneration, one more corroboration of
  it.
- **`spec-099-example-0_0_9` — 4 occurrences, correctly excluded.** All four in
  `examples/fakeshop/apps/glossary/tests/test_import_spec_terms.py`, three as
  `spec_path = "docs/SPECS/spec-099-example-0_0_9.md"` and one as
  `_make_done_card_with_spec("docs/SPECS/spec-099-example-0_0_9.md")`, feeding
  `import_spec_terms`' missing-CSV and card-reconcile paths. **0** files named `spec-099` exist in
  `docs/` or `docs/SPECS/` — the nonexistence is the fixture's point.

No **over-broad** exclusion, then. The one grading error runs the other way, and is the Medium
above.

**Catalog items 7-13 graded against `BUILD.md` `## Final test-run gate` and `START.md`'s
named-owner rule.**

| Item | Sites | Description | Licensing spec clause | Owner named in prose |
| --- | --- | --- | --- | --- |
| 7 (`spec-039 Md<n>`, 14) | symbol- or substring-qualified, all 14 | yes | none exists (another cycle's defect) | **the maintainer**, a `spec-039` follow-up card |
| 8 (`spec-039 M1a`/`H4`/`SR-3`, 6) | all 6 | yes | none exists | **the maintainer**, same `spec-039` card, with the must-move-together reason |
| 9 (`spec-030 P3a`/`P3b`, 2) | both | yes | none exists | **the maintainer**, folded into items 1-2's `spec-030` card |
| 10 (`spec-036 L3-1`/`M3-1`/`FV-1`, 4) | all 4 | yes | none exists | **the maintainer**, a `spec-036` follow-up card |
| 11 (`spec-011 Decision 4`/`7`, 4) | all 4 | yes, plus prior art | none exists | **the maintainer** — owner right, prior-art clause wrong (`Low` above) |
| 12 (`spec-016 Decision 4`, 1) | the site | yes | none exists | **the maintainer**, a `spec-016` follow-up card |
| 13 (`spec-043`/`spec-048`, 2) | both | yes | none exists | **the maintainer**, one card each — but the `spec-043` half is a non-defect (`Medium` above) |

Every item carries its sites, a one-line description, the instrument that found it **and** the
instrument that missed it, and an owner written out in prose. None cites a licensing spec clause,
correctly: no clause of spec-038 licenses deferring another spec's citation defect, and
`BUILD.md`'s requirement is "the spec line that licenses the deferral (**if any**)". The source
artifact section is the heading they sit under. The kanban DB and `KANBAN.md` are barred by this
cycle's fence, which the entries say, so prose is the only home reachable from inside the round —
`START.md` "Item routed forward w/o NAMED owner dies" is satisfied at all seven.

**Item 13's untouched site was right to be untouched.** The `spec-043 scenario 4` docstring sits in
`examples/fakeshop/test_query/test_products_api.py`, a file this round edited, and the round left
it alone because it is spec-043's vocabulary rather than spec-038's. Correct on the partition, and
now correct for a second reason: it is not a defect at all. That file is byte-identical to the
pass-1 snapshot, so nothing in it moved this pass either way.

**The reflow-hazard argument: right answer, over-claimed warrant.** Worker 2's structural argument
is that "both fragments remain substrings of the merged line, so even a citation quoting either
half would still resolve." That is true, and it is **not** what makes the join safe, because it is
true of *every* line join by construction — including one that also reflowed the lines below,
where citations quoting the reflowed text would break while the property still held. What actually
discharges `START.md`'s ungated `#"substring"` hazard here is two measurements, both re-derived
this pass:

1. **No citation anywhere quotes text on either joined line.** My own extractor over
   `git ls-files`: **711** tracked paths, **709** readable as text, **1,434** `#"…"`
   citations —
   reproducing Worker 2's three figures exactly (the prior review's 1,447 was the same instrument
   on a population the concurrent session has since moved). **0** quote text lying on either
   joined line, in either direction (citation-in-line and line-in-citation both tested). Positive
   control on the matcher itself: a synthetic citation of `request-independent stable field shape`,
   which *is* on the target line, is detected — so a matcher that had stopped matching could not
   read as zero.
2. **No citation spans the old line break**, which is the case the substring argument cannot
   reach: **0** citations contain `Decision 7). The overridable`, and **0** contain both
   `Decision 7).` and `overridable`. Nor could one: `START.md` requires a citation to
   "quote text on ONE source line", so a substring crossing the break would have had to carry a
   newline plus line 180's four-space indent and could not have resolved *before* the join either.
   The join is therefore strictly permissive: it creates newly-resolvable substrings and
   destroys
   none.

And the third leg, which no sweep can supply: **nothing else moved.** The 3-line diff above is the
whole delta, so there is no reflowed neighbour for a citation to have been quoting. Worker 2's
three-line anchor is what bought that, and it is the right discipline; the substring sentence is
the one part of its argument that carries no weight.

**The inverse proof re-run, with the control firing in my own hands.** No forward failability proof
is owed — `BUILD.md` `### What needs a proof, and what does not` scopes the obligation to a new
boundary, guard, gate, or rejection path, and this pass introduces none, so `worker-3.md`'s
mandatory re-run floor (every boundary at <= 3 rows) is **legally empty**. The inverse proof
`START.md` owes for a comment/docstring-only edit I re-ran with my **own** digest script
(`<scratchpad>/w3r/inverse.py`: strip the leading string-constant `Expr` from every `Module` /
`FunctionDef` / `AsyncFunctionDef` / `ClassDef` body, then `ast.dump(include_attributes=False)`),
against the pristine reference proved legitimate above.

| Run | Mutation | Result | Reading |
| --- | --- | --- | --- |
| real | none | **IDENTICAL, compared 1, diverged 0, exit 0** | no executable line moved |
| control 1 (Worker 2's anchor) | executable `CREATE_SHAPED_KINDS: frozenset[str]` -> `CREATE_SHAPED_KINDS_X: …` | **DIVERGED, diverged 1, exit 1** | **fires**; Worker 2's control reproduces |
| control 2 (**my own** anchor) | executable `def get_form_fields(form_class` -> `def get_form_fields_X(form_class` | **DIVERGED, diverged 1, exit 1** | **fires** on a second, independently chosen executable token |
| control 3 | docstring text `The overridable` -> uppercased | IDENTICAL, exit 0 | correct; blind to docstring text by design, which is what makes it the right instrument |
| control 4 | comment text `Module path the ``strawberry.lazy(...)`` marker references` -> uppercased | IDENTICAL, exit 0 | correct; comments are absent from the AST |
| control 5 (the abort guard) | anchor `_FORM_INPUT_KIND_SCALAR`, which occurs **0** times | **ABORT, exit 2** | reproduces Worker 2's recorded near-miss exactly; without this assert a control that could not fire would have printed a passing proof |

So the IDENTICAL result is a measurement, not a vacuous one, and it is corroborated by a control
in a second location rather than one. **The three changed lines are independently classified**, by
`ast` + `tokenize` rather than by reading: pristine 179 **DOCSTRING**, pristine 180 **DOCSTRING**,
live 179 **DOCSTRING** — **0 EXECUTABLE**, with the classifier's own controls firing
(`forms/inputs.py:105` `CREATE_SHAPED_KINDS: frozenset[str]` -> EXECUTABLE, `:171`
`def get_form_fields(form_class` -> EXECUTABLE, `:81` the module comment -> COMMENT). Zero
executable lines is what makes the inverse proof cover the whole change, and it puts the plan's
hot-path declaration (`none`) and floor-verification scope (`none`) on measured ground: nothing
runs per request / resolver / row / connection / message, and no integration seam is touched on
any version.

**No mutation reached a repository file.** Every control mutated an in-memory copy, so the Worker 3
source carve-out was never exercised and there was nothing to revert. Proved by byte comparison
rather than asserted: `cksum django_strawberry_framework/forms/inputs.py` reads
`3767357841 38628` **before and after** all five controls, and the file's only delta versus
pristine is still the 3-line docstring diff. No `ACTIVE-MUTATION.json` anywhere in the tree, and
no `docs/builder/temp-tests/round-1/` was created.

**Floor facts, read this pass rather than recalled.** The supported floor is Django **5.2.16** on
Python **3.10** with strawberry-graphql **0.316.0** (`docs/builder/BUILD.md`
`## Floor verification`, the single canonical statement). The shared `.venv` is **not** the floor
and carries, per `uv pip list` this pass: `django 6.1`, `strawberry-graphql 0.324.0`,
`channels 4.3.2`, `djangorestframework 3.18.0`, `django-filter 26.1`, on Python **3.14.2**. No
floor venv built; the shared `.venv` was not mutated.

**Retirement and non-interference, re-derived with a live control on every sweep.** Instrument:
`\bP[0-9]+(?:[.\-][0-9A-Za-z]+)?\b`, **occurrences over whole file text** and never matching
lines, in a `uv run python - <<'PY'` heredoc that prints its population size and asserts its
counts — no `for f in $FILES` scalar anywhere. Population: **437** tracked `.py` files.

| Scope | Measured this pass |
| --- | --- |
| in-scope `spec-038 … P<N>` (P-label on any line naming `spec-038`), corpus-wide | **0** |
| residue inside the 8 target files | **2**, both in `forms/inputs.py` (`P2.2` line 108, `P1.6` line 160) |
| whole tracked `.py` corpus | **40** over 16 files |
| out-of-scope: 15 files, HEAD vs worktree | HEAD **38** / worktree **38**, **0** drifted |

Arithmetic closes: 38 out-of-scope + 2 inside the targets = **40**. Two live controls, both
asserted so a dead instrument aborts rather than reading as a clean repo: the same regex over
`django_strawberry_framework/orders/sets.py` returns **2** (`P1-B`, `P1-B`), and the *in-scope*
instrument — the one that returns 0 — returns **5** when pointed at `spec-030` instead of
`spec-038`, so its zero is a reading and not a silence. The 2 survivors resolve: spec-039 carries
`P2.2` **6** times and `P1.6` **10** times (control `P9.9` -> 0), and each site names `spec-039`
on its own line or the line above inside the same comment block. That is the partition's intent,
not residue.

**Medium 2's numbers reproduce exactly, and the withdrawal is explicit rather than merely
superseded.** Measured live: `git ls-files 'django_strawberry_framework/*.py'` **110**,
`Path("django_strawberry_framework").rglob("*.py")` **111**, `git ls-files '*.py'` **437**,
`rglob` over the four trees **435**. The set difference is exactly what the report says: one
untracked file in `rglob` but not tracked (`django_strawberry_framework/utils/canonical.py`) and
three tracked `.py` outside the four trees (`conftest.py`, `docs/dry/export_dry_review.py`,
`line_count.py`); nothing tracked is missing from `rglob`. Both directions of arithmetic close:
111 = 110 + 1, and 437 = 435 - 1 + 3. `scripts/check_citations.py --check` printed
`785 in 435 .py files` again this pass from its own four-tree `rglob`, third-party corroboration
with no stake in it. The withdrawal is legible to someone reading both reports rather than only
the second: `### Medium 2` states "**I withdraw the prior pass's explanation**", names both wrong
sentences, and says "**the stale-figure item routed to Worker 1 is dropped**"; the routed list
repeats it as item 1, "**Withdraw the prior pass's routed item 3.**" A prior report is never
edited, and this is the correct shape for the correction.

**`### Dispatched findings checklist` audit: still clean.** **32** boxes, **32** `- [x]`, **0**
`- [ ]`. This pass added no box and un-ticked none, and its one edit is not a checklist item —
the
`Low` reflow was a review finding, not a dispatched box. No over-tick, no silent deferral. Worker
1's `## Final verification (Worker 1)` placeholder is untouched.

**Sweeps, all green, and the population did not shrink.**

- `uv run pytest --no-cov` (full parallel) -> **7296 passed, 40 skipped, 0 failed**, 73.33s.
  Grepped the output for `^ERROR`, `errors during collection` and `^FAILED`: **0** matches, and
  `uv run pytest --collect-only -q --no-cov` reports **7334 tests collected** with no error
  summary, stable across two consecutive runs. So no module silently dropped its rows. Against
  Worker 2's **7268 passed / 40 skipped** the population **grew** by 28 — the concurrent
  session's
  work, which the AST-identity proof above rules out this round having caused either way. The
  2-node gap between 7,336 run outcomes and 7,334 collected nodes is an instrument difference
  between the xdist run and single-process collection, and it runs in the *surplus* direction, so
  it cannot be hiding a dropped module.
- `uv run python examples/fakeshop/manage.py check` ->
  `System check identified no issues (0 silenced).`
- `uv run python scripts/check_citations.py --check` ->
  `OK: 938 citations resolve (785 in 435 .py files, 153 in KANBAN.md).` Identical to baseline.
  **Green here is not evidence for this round**: the gate matches `path::Symbol` only and
  structurally cannot see an ordinal citation. It is cited for its population line, not its
  verdict.
- `uv run ruff format --check .` -> `438 files already formatted`; `uv run ruff check .` ->
  `All checks passed!` Read-only, no `--fix`, nothing written.
- `uv run python scripts/check_trailing_commas.py --check
  django_strawberry_framework/forms/inputs.py` -> exit **0** (also the ASCII-only `.py` gate;
  it reads the 99-column limit from `pyproject.toml`).
- `uvx pre-commit run --files django_strawberry_framework/forms/inputs.py` -> all six hooks
  **Passed**.
- `git diff --check -- django_strawberry_framework/forms/inputs.py` -> exit **0**. Tree-wide the
  command flags trailing whitespace in exactly one baseline-dirty file a concurrent session owns,
  outside this round's diff and pre-existing; not this round's to touch and recorded rather than
  cleaned.
- `git status --short` -> **178** dirty paths, up from the 174 Worker 2 recorded; the concurrent
  session is still writing. `forms/inputs.py` is ` M`; nothing outside the declared ownership list
  is this pass's, and the pristine-copy diff is the only instrument in a tree this dirty that can
  say so.

**Static inspection helper: skipped, explicitly, with the reason.** `BUILD.md`
`### When to run the helper during build` fires for Worker 3 on a new `.py` file (**none**), an
existing `.py` under `optimizer/` or `types/` (**none touched**), or 30+ new logic lines inside the
package / 50+ outside it — this pass adds **0** lines of logic, measured by the AST-identity
result, so no trigger fires. The decisive reason is structural rather than arithmetic:
`scripts/review_inspect.py` emits the source with `#` comments removed and every string-literal
token, docstrings included, replaced by `...`, so it is **blind to 100% of this pass's
content** —
one docstring line — and its repeated-string-literal section cannot see a docstring at all.
Per-file skip, the single file: `django_strawberry_framework/forms/inputs.py` — "no review-worthy
logic added; one docstring line joined, proved by the docstring-stripped AST digest being
IDENTICAL with two executable controls firing." No shadow file was generated, read, or cited this
pass, and `docs/shadow/` was not written.

### Temp test verification

None written; `docs/builder/temp-tests/round-1/` was not created and does not exist. With 0
executable lines changed there is no behavior a temp test could distinguish, and every question
this pass had was answerable by measurement: the per-token citation census, the `#"…"`
citation
extractor, the AST digest and line classifier, the P-label sweep. All of those live in
`<scratchpad>/w3r/` outside the repo and close with this pass.

### Notes for Worker 1 (spec reconciliation)

No spec amendment is required by this pass, and none of the below touches
`docs/SPECS/spec-038-form_mutations-0_0_12.md`, its companion, or its terms CSV.

1. **Escalated — strike one row from the deferred-work catalog and re-publish its population.**
   `spec-043 scenario 4`
   (`examples/fakeshop/test_query/test_products_api.py::test_create_item_login_bracket_via_test_client`)
   **resolves**: spec-043's `## Test plan` numbers its scenarios `1.`…`5.` and item 4 is
   `#"4. **`login()` scoping.**"`, which the citing docstring restates almost verbatim. It is the
   same convention case Worker 2 itself used to clear `spec-028 DoD 4(c)` and
   `spec-044 Test plan 1-7`. Resolution paths: (a) drop the `spec-043` half of item 13, keep the
   `spec-048 D1` half, and carry the corrected totals **37 occurrences / 21 files / 6
   vocabularies, 32 new** (from 38 / 22 / 7, 33); or (b) keep the row explicitly re-graded as a
   *cleared* convention case beside the other three, so the next reader sees why it was raised and
   dropped. (a) is the smaller catalog; (b) preserves the lesson that a string resolver
   over-reports in both directions. Either way the corrected population figure must travel with
   it — 38 and 33 are published in three places in Worker 2's section. This is escalated rather
   than looped because the catalog's home is your `bld-final.md` and a prior build report is never
   edited: Worker 2 cannot correct it except by writing a third report.
2. **Escalated — item 11's prior-art clause, and the pointer worth carrying instead.** F14 is not
   orphaned in a `DONE/` plan. The `[spec-011]` source/test cluster is live on the board at
   `KANBAN.md #"The `[spec-011]` renumber artifact reaches six live-code sites"`, under
   `TODO-ALPHA-053-0.0.15 - Boundary hardening and system-wide DRY squeeze`, with the same 8
   occurrences across 4 files, per-file counts, and a re-derivation trap (`wc -l` reports **9**;
   the extra row is git's binary-file line for `examples/fakeshop/db.sqlite3`) that item 11 does
   not carry. `docs/builder/DONE/build-015-relay_interfaces-0_0_5.md` says so itself
   (#"already homed on a live card"), though it names `TODO-ALPHA-051-0.0.15` where the board today
   renders the bullet under `053` — worth one line in the catalog so the next reader does not
   chase the older id. Recommended: keep item 11 for its re-measurement, replace the
   orphanhood clause with the card pointer. I verified this is the **only** catalogued item
   already homed: every other token returns 0 hits in `KANBAN.md` against a control of 8 for
   `spec-011`.
3. **Worker 2's routed item 1 (withdraw the prior pass's stale-figure item 3) is correct and I
   re-derived it.** 110 / 111 / 437 / 435 all reproduce live, the set difference is exactly one
   untracked file plus three tracked root-level files, and both arithmetics close. Normalize on the
   instrument name, never on the number, and do **not** restate the plan's 111 / 435 as stale.
4. **Worker 2's routed item 2 (narrow the plan's spec-039 certification) is correct and its
   recommended replacement text is accurate on the ground.** spec-039 carries `P2.2` 6 times and
   `P1.6` 10 times, so the `P<N>.<M>` half of the certification is true; `Md<n>` / `M1a` / `H4` /
   `SR-3` are 0 in the spec and it has no rationale companion, so the other half is false. If you
   adopt the replacement wording, its "113 live P-label occurrences" figure is the one number in it
   I did not re-derive — measure it as you write it.
5. **Worker 2's routed item 3 (the prior pass's routed item 1 stands) is correct.** The spec still
   carries `#"(the kwarg-requiring-form fix)"` inside `### Decision 7`, the deleted parenthetical
   was resolvable and merely banned in source, and this pass's join is in the same docstring but
   does not touch that phrase — verified by the 3-line diff.
6. **Corroboration for catalog item 6, refreshed.** The ungated `#"substring"` half of
   `AGENTS.md` rule 27 carries **1,434** citations over the 709 readable of 711 tracked paths; the
   ordinal half is 37 (corrected). A gate resolving `spec-<NNN> <ordinal>` against that spec's live
   text would need two things this cycle has now demonstrated it must have, or it will publish
   false positives of its own: an **en-dash-tolerant** range comparison (the `spec-044 D4-D5` and
   `spec-044 Test plan 1-7` cases) and a **numbered-list** resolution step, not a literal string
   search (the `spec-028 DoD 4(c)` and `spec-043 scenario 4` cases). Both are corrections this
   round derived by reading; a gate that skipped them would reproduce exactly the errors graded
   here. The policy call remains the maintainer's.

### Review outcome

`review-accepted`.

The apply-changes pass is correct in its source edit and in its two corrections, and provably so:
the diff is 2 removed + 1 added lines in one file with every other byte identical, the merged line
is 95 columns in a file whose longest is exactly 99 with 0 over it, the three left-alone short
lines are untouched at 26 / 15 / 64 columns, the inverse proof is IDENTICAL with an executable
control firing at two independent anchors and the abort guard reproducing its recorded near-miss,
all three changed lines classify DOCSTRING with 0 EXECUTABLE, the retirement holds at 0 in scope
with 38/38 out-of-scope occurrences unmoved against HEAD, no citation in the tree is stranded by
the join, and every gate is green with the test population grown rather than shrunk and 0
collection errors.

**Prior findings: Low closed cleanly; Medium 2 correctly corrected with an explicit withdrawal;
Medium 1 correctly catalogued, with one false-positive row.** The `spec-044 D4-D5` exoneration is
right and clears a citation. The 4-vs-8 item-11 discrepancy is subject rather than drift, and
item 11 publishes both subjects, which is what makes it right.

**Why this accepts rather than loops, stated deliberately.** The two open items are a catalog row
naming a non-defect and a mis-described prior art in another catalog row. Neither is a false
exoneration, a missing owner, or an unfixed source defect — the three things that would make
another loop buy correctness. Both live in a section whose destination is Worker 1's
`bld-final.md`, and a prior build report is never edited, so a Worker 2 re-pass could not fix
either: it could only append a third report restating what is written above, and Worker 1 would
still be the one to act. Every item that mattered to the round's own contract — the 32
replacements, the retirement to 0, the inverse proof, the citer postcondition, the checklist — is
measured and closed. So the residual imprecision is graded here, routed with resolution paths, and
the round hands to Worker 1 rather than spending a spawn on more measurement.

---

## Final verification (Worker 1)

Every figure below was measured in this pass, from the tree, with its own instrument and its own
live control. Nothing is carried from an earlier pass on the strength of an earlier pass having
said it — the round is five passes deep, which is the depth at which a number starts reading as
measured because somebody upstream wrote it down.

**Reference discipline.** `git show HEAD:` is not a usable reference for what this round changed:
7 of the 8 target files carry a concurrent session's uncommitted **executable** hunks. So I
proved the pre-edit pristine set legitimate before using it, rather than accepting it from either
builder pass. Per file, diff lines HEAD→pristine / HEAD→worktree / pristine→worktree, and the
P-label census at each of the three points:

| File | HEAD→pris | HEAD→tree | pris→tree | P@head | P@pris | P@tree |
| --- | --- | --- | --- | --- | --- | --- |
| `django_strawberry_framework/forms/converter.py` | 0 | 4 | 4 | 2 | 2 | 0 |
| `django_strawberry_framework/forms/inputs.py` | 76 | 93 | 17 | 10 | 10 | 2 |
| `django_strawberry_framework/forms/resolvers.py` | 21 | 23 | 2 | 1 | 1 | 0 |
| `django_strawberry_framework/forms/sets.py` | 30 | 48 | 18 | 9 | 9 | 0 |
| `django_strawberry_framework/mutations/sets.py` | 109 | 111 | 2 | 1 | 1 | 0 |
| `examples/fakeshop/apps/products/forms.py` | 36 | 44 | 8 | 4 | 4 | 0 |
| `examples/fakeshop/apps/products/schema.py` | 54 | 58 | 4 | 2 | 2 | 0 |
| `examples/fakeshop/test_query/test_products_api.py` | 176 | 186 | 10 | 5 | 5 | 0 |
| **totals** | **502** | **567** | **65** | **34** | **34** | **2** |

Three things this fixes in place. HEAD→pristine is **502**, identical to the figure the first
review measured, so the concurrent session has written nothing into these 8 files since that
snapshot. The arithmetic closes exactly — 567 − 502 = **65** — so the round's entire delta in
these files is 65 diff lines (33 added, 32 removed: 66 at pass 1, less one line where the
apply-changes pass joined two docstring lines into one) **and nothing else**. And the P-label
census is identical at HEAD and at pristine, file for file, 34/34, which is the mechanical
statement that the concurrent hunks touch none of the 32 sites: the fix landed on the shipped
contract, not on uncommitted work.

### `### Dispatched findings checklist` audit

**32 boxes parsed, 32 `- [x]`, 0 `- [ ]`. No over-tick, no un-ticked box, no deferral owed.**
Verified against the diff rather than against the re-review's report of it, and tested in **both
directions** — an absence test alone cannot distinguish "the fix landed" from "a concurrent
session deleted the line":

- **Negative half.** For each box, its quoted anchor (the citation as it read before the round)
  occurs **exactly 1** time in that file's pristine copy and **0** times in the working tree.
  32/32.
- **Positive half.** For each of the 32 rows of the plan's Group A-D tables, the planned
  replacement text is **present** in the live file. 32/32, including both two-line wrapped edits
  (`examples/fakeshop/apps/products/forms.py` `#"input writes through (the decode"` / `#"reverse
  map)"` on lines 49-50, and `forms/inputs.py::get_form_fields` where the join has put
  `#"(spec-038 Decision 7). The overridable"` on one line).
- **Live control on the positive instrument.** My first run of it parsed six `Becomes` cells
  wrongly (it kept the markdown backticks) and printed `MISSING` for exactly those six. A
  positive-presence sweep that cannot print `MISSING` is indistinguishable from one that matches
  everything, and that misparse is the control that it can.

Both halves ran over the artifact's own parsed table rows and box list, not a hand-copied list,
so the population is the artifact's and the count is `len()` of it.

### The two items the re-review routed here

**1. `spec-043 scenario 4` — the re-review is right, and the correction does not go far enough.
One more row of the same class falls: `spec-048 D1`.**

Confirmed on its own ground. `docs/SPECS/spec-043-test_client-0_0_14.md` `## Test plan` opens
`#"The numbered scenarios below are the behaviours this card must prove"`, splits them
`#"**Sync request shapes (scenarios 1–5)"`, numbers the list `1.`…`5.`, and item 4 reads
`#"4. **`login()` scoping.** `seed_data(1)`, a write-auth-gated products"` — continuing through
the denied-anonymous / `with client.login(user_with_perm):` / denied-again bracket that the
citing docstring at
`examples/fakeshop/test_query/test_products_api.py::test_create_item_login_bracket_via_test_client`
restates almost clause for clause. `spec-043` is on the line, `## Test plan` exists, item 4
exists: `START.md` "grade by ANCHOR presence, never distance" clears it, the same way Worker 2
itself cleared `spec-028 DoD 4(c)` and `spec-044 Test plan 1-7`. The re-review's grading of its
own section is correct and its judgement not to spend a builder loop on it is correct.

**And the rule it applies clears one more catalogued row.** `spec-048 D1`
(`examples/fakeshop/test_query/test_uploads_api.py #"publishes ``path`` in the live schema
(spec-048 D1)."`) was graded stranded on the ground that spec-048 carries **0** occurrences of
the literal token `D1` — which is true, and is the same string-comparison artifact. `D<N>` is a
**measured repo-wide shorthand for `Decision <N>`**, not this one site's invention: 26
`spec-<NNN> … D<N>` citations exist in tracked `.py`, and in **20** of them the named spec
carries a matching `### Decision <N>` heading (`spec-040` ×12, `spec-041` ×3, `spec-044` ×2,
`spec-053` ×2, `spec-048` ×1). spec-048 ships
`### Decision 1 — `path` leaves the safe default for two composed opt-in types`, whose first
listed property is `**The field is gone from the SDL, not merely null.**` over `DjangoFileType` /
`DjangoImageType` — precisely what the citing docstring asserts. It resolves. Not a defect.

I then applied the same test to **every** remaining catalogued row, because a rule that clears
two rows is a rule that has to be run against all of them. None of the rest has a resolution
path, measured token by token against the named spec *and* its rationale companion:

| Row | In the spec | In its companion | Resolution path |
| --- | --- | --- | --- |
| `spec-039` `Md1`/`Md2`/`Md3`/`Md4`/`Md5`/`Md7`/`M1a`/`H4`/`SR-3` | 0 each | **no companion exists** | none — bare `Md` is 0 in the spec too, and `Md`/`H`/`SR` expand to no section it has |
| `spec-036` `L3-1`/`M3-1`/`FV-1` (and bare `L3`/`M3`/`FV`) | 0 each | 0 each | none |
| `spec-030` `P1-B`/`P3a`/`P3b` | 0 each | 5 / 4 / 3 | companion-only, which is the shape items 1-2 already record |
| `spec-011` `Decision 4`/`Decision 7` | the string `Decision` occurs **0** times in the whole 3,440-byte stub | 0 | none |
| `spec-016` `Decision 4` | 0 `### Decision N` headings, `Decision` 0 | 1 | none |

**Corrected population, measured as this line was written:** strike both false positives and the
graded stranded set is **36 occurrences over 20 files in 5 spec vocabularies**, of which 5
(`spec-030 P1-B`) are already homed by catalog items 1-2, so **31 are new** — not 38 / 22 / 7 and
33, and not the re-review's 37 / 21 / 6 and 32 either. Both struck rows were each the sole
catalogued occurrence in their file, which is what makes the file count fall by one apiece
(22 → 21 → 20). Every one of the other 18 per-token rows reproduces exactly, file for file, and
the instrument's `spec-038` control rows (`P1`, `P2`, `P3` on a line naming `spec-038`) return
**0** — the round's own fix confirmed by an instrument that never scoped it. Pass B's
`### Deferred work catalog` carries 36 / 20 / 5 and 31-new, and re-grades both `spec-043 scenario
4` and `spec-048 D1` as *cleared convention cases* beside `spec-028 DoD 4(c)` and
`spec-044 D4-D5`, rather than dropping them silently: the lesson that a literal-string resolver
over-reports in **both** directions is the one thing a future gate has to be built knowing.

**2. Item 11's prior-art clause — the re-review is right; the board reference verifies, and one
detail in it needs correcting too.** Read-only; `KANBAN.md` is fenced and was not edited.

The live-code half of the `[spec-011]` cluster is on the board today. Card heading at
`KANBAN.md:300`, `### [TODO-ALPHA-053-0.0.15 - Boundary hardening and system-wide DRY squeeze]`;
the bullet at `:341` opens `#"The `[spec-011]` renumber artifact reaches six live-code sites"`
and carries the same per-file counts (`types/base.py` five, `types/resolvers.py` one, plus
`tests/types/test_base.py` and `tests/filters/test_sets.py`), attributes them to
`docs/builder/bld-011-final.md`, and states the re-derivation trap in its own words: the
population is 8 occurrences across 4 files but `git grep -oh '\[spec-011\]' | wc -l` reports one
more than the token count, the extra row being git's `Binary file examples/fakeshop/db.sqlite3
matches` line. So item 11's orphanhood clause is wrong and the re-review's Low grading of it is
right — the entry's value is its re-measurement, not its re-homing.

Two corrections to that account, both measured here. **The trap's mechanism reproduces; its
numbers do not, and the numbers were never the point.** `git grep -oh '\[spec-011\]' | wc -l`
returns **42** today, of which **41** are the literal token and **1** is the binary-file line —
the +1 inflation is exactly as described, but the board's `9 vs 8` is its 2026-08-17 reading of a
population that has since grown to 41 (mostly `docs/builder/DONE/` plans and archived specs).
The catalog must carry the **mechanism** and the per-file counts, never the tree-wide total.
Note also that the bracketed spelling `[spec-011]` occurs **0** times in tracked `.py`: that
command measures the documentation tree, and the 8-occurrence source/test population is a
different measurement. **And the second card is `056`, not `057`.** The documentation half's
bullet renders at `KANBAN.md:582` under
`### [TODO-ALPHA-056-0.0.17 - Alpha documentation-debt discharge]`, and it does say
`#"The six package-source and test occurrences are carried by `TODO-ALPHA-053-0.0.15`"` — while
the `:341` bullet says the documentation half is owned by `TODO-ALPHA-057-0.1.0`. One of the two
board bullets is stale about the other's card id. Read-only observation, recorded in Pass B's
catalog for the maintainer; nothing here touches the board.

**The 4-vs-8 verdict holds: subject, not drift.** Enumerated every `spec-011` occurrence in the
**437** tracked `.py` files: **8**, at `types/base.py` ×5, `types/resolvers.py` ×1,
`tests/filters/test_sets.py` ×1, `tests/types/test_base.py` ×1 — file for file what F14 and the
board bullet record. Of those 8, exactly **4** carry an ordinal
(`types/base.py #"``_validate_interfaces`` (spec-011 Decision 4)."`,
`#"connector column (spec-011 Decision 7"`, its matching inline comment, and
`types/resolvers.py #"# FK-id elision (spec-011 Decision 7)"`) and **4** do not: two
`spec-011 #"substring"` citations in `types/base.py`, one bare `(spec-011)` in
`tests/filters/test_sets.py`, and one `spec-011-era` prose mention in `tests/types/test_base.py`.
Live control: `spec-015` returns **30** occurrences over the same population, so the instrument
was reading. Two counts, two subjects, neither wrong — and item 11 publishes both, which is what
makes it right.

### The load-bearing claims, re-derived

**In-scope retirement is 0.** Instrument: `\bP[0-9]+(?:[.\-][0-9A-Za-z]+)?\b` counted as
**occurrences over whole file text**, never matching lines, in a `uv run python - <<'PY'`
heredoc that prints its population size and asserts every count. Population **437** tracked
`.py` files (`git ls-files '*.py'`). A P-label on any line naming `spec-038`, corpus-wide:
**0**. **Live control on the instrument that returns zero** — the same instrument aimed at
`spec-030` instead returns **5**, so the zero is a reading and not a silence.

**The out-of-scope vocabularies are unchanged.** 15 files carry out-of-scope occurrences;
HEAD **38** / worktree **38**, **0 drifted**, per file: `auth/mutations.py` 1/1,
`mutations/fields.py` 2/2, `mutations/inputs.py` 1/1, `optimizer/nested_planner.py` 2/2,
`orders/sets.py` 2/2, `rest_framework/inputs.py` 3/3, `rest_framework/resolvers.py` 4/4,
`rest_framework/sets.py` 3/3, `utils/inputs.py` 1/1, `utils/querysets.py` 1/1,
`apps/library/tests/test_generic_connection_sharded.py` 1/1, `test_query/test_library_api.py`
10/10, `tests/optimizer/test_predicates.py` 4/4, `tests/test_lateral_pg_parity.py` 1/1,
`tests/test_relay_node_field.py` 2/2. Residue inside the 8 target files: **2**, both in
`forms/inputs.py` (`P1.6`, `P2.2`, spec-039's, resolving, out of scope by the partition).
Arithmetic closes: 38 + 2 = **40** = the whole-corpus figure, measured independently.

**Zero executable lines changed in the round.** I ran my own docstring-stripped AST-identity
digest (strip the leading string-constant `Expr` from every `Module` / `FunctionDef` /
`AsyncFunctionDef` / `ClassDef` body, then `ast.dump(include_attributes=False)`) over all 8
files against the pristine reference proved legitimate above: **8 IDENTICAL, compared 8,
diverged 0, exit 0**. Four controls, run in my own hands, because a docstring-stripped digest is
blind by design and an unbroken control is indistinguishable from an instrument comparing
nothing:

| Control | Mutation (applied to an in-memory copy only) | Result | Reading |
| --- | --- | --- | --- |
| A | executable `_ALLOWED_PLAIN_FORM_META_KEYS: frozenset[str]` → `…_W1` in `forms/sets.py` | **DIVERGED on `forms/sets.py`, diverged 1, exit 1** | fires in a package file |
| B | executable `class CreateItemWithFileViaForm` → `…W1` in `apps/products/schema.py` | **DIVERGED on `apps/products/schema.py`, diverged 1, exit 1** | fires in an **example** file too, so the digest is not proven only in one location |
| C | docstring text `this module (spec-038 Decision 7).` → other text | 8 IDENTICAL, exit 0 | correct; blind to docstring text by design |
| D | anchor `_NO_SUCH_SYMBOL_ANYWHERE`, which occurs 0 times | **ABORT, exit 2** | the uniqueness assert fires; without it a control that could not fire would have printed a passing proof |

No mutation ever reached a repository file; every control mutates a copy in memory. Swept the
tree for both control suffixes afterwards — **0** hits, so no proof residue survives anywhere.

### Prior findings and the builders' on-disk amendment lists

Confirmed discharged (`worker-1.md` `## Review-round custody`): every item both builders recorded
under `### Notes for Worker 1 (spec reconciliation)` is acted on here or in Pass B.

- **Low (the 19-column orphan)** — closed. `forms/inputs.py:179` now reads
  `#"discoverable, request-independent stable field shape (spec-038 Decision 7). The
  overridable"`, and the file carries **0** lines over 99 with its longest at exactly 99. The
  three lines Worker 3 ruled paragraph-final or ordinary wraps are untouched.
- **Medium 2 (instrument vs growth)** — correctly withdrawn, and re-derived here:
  `git ls-files 'django_strawberry_framework/*.py'` **110** vs `rglob` **111**; `git ls-files
  '*.py'` **437** vs four-tree `rglob` **435**. The plan's 111 / 435 are `rglob` readings and
  both still reproduce. Nothing is stale, and no artifact figure is normalized on a number — the
  correction is that every population figure names its instrument.
- **Medium 1 (the stranded-ordinal class)** — catalogued with named owners, no source edit,
  which is the right disposition: fixing another spec's citations here is the half-fix this round
  exists to correct. Population corrected above.
- **The plan's `spec-039` certification is narrowed here rather than by rewriting the plan.**
  Its out-of-scope table reads "Every one names `spec-039` on its own line. … so each citation
  **resolves**. Not a defect." That is true of the **`P<N>.<M>`** labels its census measured —
  spec-039 carries `P2.2` and `P1.6` live — and **false** of spec-039's `Md<n>` / `M1a` / `H4` /
  `SR-3` citations, which resolve against nothing and are catalogued as items 7-8. A prior
  section of this artifact is not edited (`ARTIFACT.md`: never edit prior entries), and the plan
  section is no exception just because I wrote it; the narrowing lives here and in Pass B's
  catalog.
- **`fix` → `case`** — applied, recorded below.

### Verdict

`final-accepted`. The round's contract is closed on measured ground: 32/32 boxes provably landed
in both directions, in-scope retirement 0 under an instrument with a firing control, 38/38
out-of-scope occurrences unmoved against HEAD, 65 diff lines total with 0 executable among them
and the inverse proof's controls firing in two independent locations. The two routed items are
ruled — one confirmed and extended by a second false positive of the same class, one confirmed
with its board pointer verified read-only — and both travel to Pass B's catalog with corrected
figures. No source defect remains and no source edit is owed, so nothing here routes back through
a builder loop.

### Summary

Review round 1 retired every stranded `spec-038 … P<N>` ordinal citation from shipped source: 32
sites across 8 files, 5 in the package and 3 in the example project, fixed by dropping the
sub-ordinal where `spec-038 Decision 7` already located the contract, restating the contract in
one clause where the ordinal was the only handle on it, and deleting the parenthetical where the
host sentence already carried the content. Two sites gained a missing citation component rather
than only losing one. `AGENTS.md` rule 27's ordinal half — the rule this round enforces — still
has no gate, which is the round's one escalation to the maintainer.

### Spec changes made (Worker 1 only)

**`docs/SPECS/spec-038-form_mutations-0_0_12.md` line 1349 — one word. 177,321 → 177,322 bytes,
2,408 lines unchanged.**

`**Schema-time field discovery reads `form_class.base_fields`, never an instance (the
kwarg-requiring-form fix).**` → `… (the kwarg-requiring-form case).**`. Both builder passes
routed this and both left it as the custodian's call. Taking it: the round deleted the same
phrase from `forms/inputs.py::get_form_fields` **because** `fix` is process provenance
`START.md` "Style Rio cares about" bars from standing prose, and the spec is a standing document
under the same rule — leaving it there is the half-swept pair `START.md` warns about ("Sweep both
files of a pair"). `case` is the spec's own vocabulary for this situation, at
`#"(kwarg-requiring, the ``get_form_kwargs`` case)"` and at `## Edge cases and constraints`
`#"**A form whose ``__init__`` requires constructor kwargs.**"`, so the sentence gains no new
term. Applied assert-once-then-write: the anchor was asserted to occur exactly **1** time and
the replacement **0** times before any byte was written.

Postconditions, all verified after the write: `uv run python scripts/check_spec_glossary.py
--spec docs/SPECS/spec-038-form_mutations-0_0_12.md` → `OK: 31 terms - all have glossary entries
and at least one spec link.`; `diff` against a pre-edit copy taken outside the repo shows exactly
one changed line; `^#` swept for non-headings → **0**; and the citer postcondition
`AGENTS.md` rule 27 requires — `kwarg-requiring-form fix` now occurs in **0** of the 709 readable
tracked paths, with the new spelling found in 1 as the positive control that the sweep was
reading anything.

**`docs/SPECS/appx/spec-038-form_mutations-0_0_12-rationale.md` — no change this pass** (82,360
bytes, 1,245 lines, the 3 remaining P-label occurrences all on the one line that *describes* the
retired spelling, as the plan pass recorded).
`docs/SPECS/appx/spec-038-form_mutations-0_0_12-terms.csv` untouched.

**Spec status-line re-verification** (`worker-1.md`, every spawn): lines 1-12 of the spec still
describe the build's state — `#"Shipped in `0.0.12` (card [`DONE-038-0.0.12`][kanban])."` — and
the companion's opening paragraph still describes what it carries. No status edit owed.

**Deferral reasons: none owed.** All 32 checklist boxes are `- [x]` and provably landed, so no
box needs a deferral line.

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
