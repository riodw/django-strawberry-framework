# Build: Slice 1 — schema-validation diagnostics

Spec reference: `docs/spec-032-full_relay-0_0_9.md` (lines 84-87 slice checklist; Decision 8 at lines 402-424; Error shapes lines 255-257; Test plan Slice 1 at lines 545-549; Current state line 139)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

- **Existing patterns reused.**
  - `django_strawberry_framework/types/base.py::_validate_interfaces` (base.py:742-831) is the single touch point; the named branch slots into its existing per-entry loop. `from strawberry import relay` is already imported at base.py:37 — no new import.
  - The message-localization precedent: `_INTERFACES_SHAPE_ERROR_LEAD_IN` + `_interfaces_shape_error` (base.py:726-739) shows the house style for keeping a repeated message fragment single-sourced. The new constant follows that placement (module level, beside it).
  - `ConfigurationError` (`django_strawberry_framework/exceptions.py`) — same exception type every sibling validator raises; the existing `f"{meta.model.__name__}.Meta.interfaces entry …"` message prefix (base.py:818) is the prefix shape the named messages follow.
  - The two re-affirmation pins re-assert already-shipped messages: the generic non-interface rejection at base.py:816-821 and the `Meta.connection` Relay-Node gate in `_validate_connection` (base.py:204-208, message `"…requires a Relay-Node-shaped type; add \`relay.Node\` to \`Meta.interfaces\` or inherit \`relay.Node\` directly."`).
  - Test-side: `tests/types/test_base.py` already carries the `_isolate_registry` autouse fixture (test_base.py:56-60), the `CATEGORY_SCALAR_FIELDS` constant (test_base.py:46-53), and the inline-`DjangoType`-subclass-inside-`pytest.raises` pattern (`test_meta_connection_non_relay_type_raises`, test_base.py:379-387). The new tests reuse all three. The staged TODO anchor at test_base.py:229-241 names the exact eight test names; the source-side TODO anchor sits at base.py:801-814.
- **New helpers justified.** One module-level constant in `types/base.py`: `_RELAY_NON_INTERFACE_HELPERS` — a tuple of `(helper_object, "relay.<Name>", what-it-is/remediation text)` triples for the six helpers. Single responsibility: the named-rejection table. Single call site: the entry loop in `_validate_interfaces`. A table beats six stacked `if entry is relay.X` branches (the naive shape) — one raise site, six data rows.
- **Duplication risk avoided.**
  - Six copy-pasted raise sites in `_validate_interfaces` → avoided by the table + one loop/raise.
  - Six copy-pasted test bodies → acceptable as six named tests (the spec mandates one test per helper), but the class-creation boilerplate may be factored into one small local helper at Worker 2's discretion (see discretion items).
  - The two re-affirmation pins **near-duplicate existing tests** (`tests/types/test_relay_interfaces.py::test_meta_interfaces_rejects_non_interface_classes` at test_relay_interfaces.py:112-122, and `tests/types/test_base.py::test_meta_connection_non_relay_type_raises` at test_base.py:379-387). This is deliberate and spec-mandated: the existing tests match only loose fragments (`"not a Strawberry interface"`, `"relay.Node"`); the new pins assert the *documented full messages* (class-naming, and the add-`relay.Node`-or-remove remediation wording). Worker 3 should treat the overlap as justified, not a DRY finding — the assertion strength differs and the spec's re-affirmation contract requires the message pins to live in `tests/types/test_base.py`.

### Implementation steps

Line numbers are pin-at-write-time navigational hints. Verify against the current source before editing — another worker's pass may have shifted the file since this plan was written.

1. `django_strawberry_framework/types/base.py`: add the module-level `_RELAY_NON_INTERFACE_HELPERS` constant beside `_INTERFACES_SHAPE_ERROR_LEAD_IN` (base.py:726). Six rows, spec Decision 8 order, each carrying the helper object, its display label, and the Decision-8 message text:
   1. `relay.GlobalID` — "a scalar-like id wrapper, not an interface; Relay-Node-shaped types get `id: GlobalID!` automatically from `relay.Node`."
   2. `relay.NodeID` — "an annotation helper for custom id fields (`id: relay.NodeID[int]`), not an interface."
   3. `relay.Connection` — "a generic output type; declare `Meta.connection` / use `DjangoConnectionField` for connection shapes."
   4. `relay.ListConnection` — same remediation as `Connection`.
   5. `relay.Edge` — "a generic output type the connection machinery instantiates; not consumer-declarable."
   6. `relay.PageInfo` — "a generated pagination type; not an interface."
   Each composed message follows the sibling prefix shape: `f"{meta.model.__name__}.Meta.interfaces entry relay.<Name> is …"`, names the helper, says what it is, and names what the consumer probably meant (`relay.Node`; for `Connection` / `ListConnection` additionally `Meta.connection` / `DjangoConnectionField`).
2. In `_validate_interfaces`'s entry loop, insert the named-helper check **immediately after the string-entry rejection (base.py:785-790) and BEFORE the `not isinstance(entry, type)` non-class branch (base.py:791)**. **Placement correction vs the staged TODO pseudocode (base.py:801-814, which sits after the DjangoType check):** `relay.NodeID` is `typing.Annotated[_T, NodeIDPrivate()]` — an `_AnnotatedAlias`, NOT a class (verified against the locked Strawberry 0.316.0: `isinstance(relay.NodeID, type)` is `False`) — so placed where the TODO sits, the NodeID entry would die in the non-class branch (base.py:791-794) without ever reaching the named branch. The other five (all classes: `GlobalID` has no `__strawberry_definition__`; `Connection` / `ListConnection` / `Edge` / `PageInfo` carry `is_interface=False`) reach the generic branch at base.py:816 today; NodeID does not. The early placement satisfies Decision 8's "the named branch fires **before** the generic non-interface rejection" for all six.
3. Match by **identity** (`entry is helper` in a loop over the table), NOT a dict lookup keyed on the entry: `Meta.interfaces` entries can be arbitrary consumer objects (the existing tests pass `object()` instances and ints, and an unhashable entry would make `dict.get(entry)` raise `TypeError` instead of the shape error), and the Annotated alias has nonstandard `__eq__`/`__hash__` semantics — `is` is exact and safe.
4. Remove the staged `TODO(spec-032-full_relay-0_0_9 Slice 1)` comment block (base.py:801-814) in the same change (AGENTS.md: the anchor is removed in the change that ships the slice).
5. Update the `_validate_interfaces` docstring's validation-rules list (base.py:750-762) with one line for the named-helper rejection (cites spec-032 Decision 8).
6. `tests/types/test_base.py`: replace the staged Slice-1 TODO block (test_base.py:229-241) with the eight tests (see Test additions). No other test file changes; `tests/types/test_relay_interfaces.py` is untouched (its existing generic-rejection tests keep passing — they use non-relay entries, which still route through the generic branch).
7. Run `uv run ruff format .` and `uv run ruff check --fix .`; reconcile `git status --short` per the Worker 2 validation-run contract. Trailing-comma rule: the six-row table is ≥4 items, so it carries trailing commas and formats one row per line.

### Test additions / updates

All eight land in `tests/types/test_base.py` (the spec's named coverage home for this slice). They are package-only by design: type-creation `ConfigurationError`s cannot appear in the example schema (Test plan / Cross-subsystem invariants), so no live `test_query/` test exists for this slice. Names are pinned by the Test plan (spec lines 545-549) and the staged TODO:

- `test_interfaces_rejects_relay_globalid_named` — `interfaces = (relay.GlobalID,)` on a `DjangoType` subclass raises `ConfigurationError`; assert the message contains `relay.GlobalID`, the "scalar-like id wrapper" description, and the `relay.Node` remediation.
- `test_interfaces_rejects_relay_nodeid_named` — same shape for `relay.NodeID`; assert `relay.NodeID` + "annotation helper" + remediation. (This is the test that locks the placement fix: without step 2's early placement it would see the unnamed "must contain interface classes" message.)
- `test_interfaces_rejects_relay_connection_named` — assert `relay.Connection` + "generic output type" + both `Meta.connection` and `DjangoConnectionField` named.
- `test_interfaces_rejects_relay_listconnection_named` — assert `relay.ListConnection` + the same connection-surface remediation.
- `test_interfaces_rejects_relay_edge_named` — assert `relay.Edge` + the machinery-instantiated / not-consumer-declarable description.
- `test_interfaces_rejects_relay_pageinfo_named` — assert `relay.PageInfo` + "generated pagination type".
- `test_interfaces_rejects_non_interface_class_named` (re-affirmation pin) — a plain `@strawberry.type` class (NOT a relay helper) in `Meta.interfaces` still takes the generic branch; assert the message **names the offending class** and contains "is not a Strawberry interface". No behavior change; pins the documented message.
- `test_connection_key_requires_relay_node` (re-affirmation pin) — `Meta.connection = {"total_count": True}` on a non-Relay-Node type raises; assert the full documented remediation "requires a Relay-Node-shaped type" + "add `relay.Node` to `Meta.interfaces` or inherit `relay.Node` directly". No behavior change; pins the documented message.

Each test builds the type the real-usage way (inline `class XType(DjangoType)` with `model = Category`, `fields = CATEGORY_SCALAR_FIELDS` inside `pytest.raises`), matching the sibling `test_meta_connection_*` pattern in the same file. No temp/scratch tests are required for development; Worker 3 may, if it wants a throwaway probe, drop a temp test under `docs/builder/temp-tests/slice-1/` confirming an unhashable entry (e.g. a list inside the interfaces tuple) still produces the must-contain-interface-classes error with no `TypeError` from the named-branch lookup (the identity-loop design makes this hold by construction).

### Implementation discretion items

Assessed and decided as Worker 2's choice — equally valid shapes, no architectural weight:

- The exact container shape of `_RELAY_NON_INTERFACE_HELPERS` (tuple of 3-tuples vs tuple of small NamedTuples) and whether the message text is stored whole or composed from a label + description pair — as long as matching is identity-based, there is exactly one raise site, and the six Decision-8 message fragments land verbatim.
- Whether the six named tests share a small local class-builder helper for the `Meta` boilerplate or each inline the four-line class — six inline copies are acceptable; a helper is fine if it stays in-file and obvious.
- `pytest.raises(..., match=...)` regex vs `str(excinfo.value)` substring assertions (mind regex-escaping the backticks/parentheses in the documented messages if `match=` is used).

### Notes for Worker 1 (spec reconciliation)

- **Spec-vs-codebase nuance, resolved in-plan (no spec edit during planning):** the spec's Current state (line 139, "the six `strawberry.relay` helpers the card names all take that generic path today") and Decision 8 (line 413, "All six already *fail* today through `_validate_interfaces`'s generic … branch") are inaccurate for `relay.NodeID`: it is an `Annotated` alias, not a class, so today it fails through the earlier "must contain interface classes" **non-class** branch (base.py:791-794), not the generic non-interface branch. The Decision-8 contract (named branch fires before the generic rejection, all six named) is unaffected and fully implementable; the plan pins the corrected branch placement (Implementation step 2). At final verification, consider a one-line spec wording fix to Current state line 139 / Decision 8 line 413 ("all six already fail — five through the generic non-interface branch, `NodeID` through the non-class branch") recorded under `### Spec changes made (Worker 1 only)`.

### Spec slice checklist (verbatim)

- [x] [`django_strawberry_framework/types/base.py::_validate_interfaces`][base] gains a named-helper rejection branch: each of `relay.GlobalID`, `relay.NodeID`, `relay.Connection`, `relay.ListConnection`, `relay.Edge`, `relay.PageInfo` appearing in [`Meta.interfaces`][glossary-metainterfaces] raises [`ConfigurationError`][glossary-configurationerror] **naming the helper** and explaining what it is instead (a scalar / an annotation helper / a generic output type) and what the consumer probably meant (`relay.Node`, or [`Meta.connection`][glossary-metaconnection] / [`DjangoConnectionField`][glossary-djangoconnectionfield] for connection shapes). Today all six fall into the generic "is not a Strawberry interface" rejection; the named branch fires **before** the generic one.
- [x] Re-affirmation coverage for the two already-shipped diagnostics the card enumerates: a non-Strawberry-interface class in `Meta.interfaces` is rejected naming the class ([`spec-011`][spec-011]-era behavior), and `Meta.connection` on a non-Relay-Node type is rejected with the add-`relay.Node`-or-remove-the-key remediation ([`spec-030`][spec-030] Decision 8). No behavior change; the tests pin the documented messages.
- [x] Package coverage: [`tests/types/test_base.py`][test-types-base] — one named-rejection test per helper (six), plus the two re-affirmation pins.

### Static inspection (BUILD.md-mandated)

`uv run python scripts/review_inspect.py django_strawberry_framework/types/base.py --output-dir docs/shadow` was run during this planning pass (base.py is 1377 lines and under `types/` — both triggers apply). Findings used:

- `_validate_interfaces` is already a control-flow hotspot (90 lines, 13 branch nodes). The table + single-raise design adds ~2 branch nodes, not 6 — keep it that way.
- The three staged `TODO(spec-032…)` comments in base.py are at shadow-confirmed sites: line 79 (Slice 3, untouched), line 549 (Slice 3, untouched), line 801 (Slice 1 — removed by this slice).
- Repeated-string-literals section shows no existing literal this slice would re-repeat; the six new message strings are each single-occurrence by design (table rows).
- Shadow line numbers are not canonical; all line refs in this artifact are original-source pins (allowed in this per-cycle scratchpad).

---

## Build report (Worker 2)

### Files touched

- `django_strawberry_framework/types/base.py` — added the module-level named-rejection table (`_RELAY_NON_INTERFACE_HELPERS`, with the shared `_RELAY_NON_INTERFACE_REMEDIATION` tail and the shared `_RELAY_CONNECTION_HELPER_DESCRIPTION` for the `Connection` / `ListConnection` rows) beside `_INTERFACES_SHAPE_ERROR_LEAD_IN`; inserted the identity-matched named-helper rejection loop in `_validate_interfaces` immediately after the string-entry rejection and before the non-class branch (the plan's step-2 placement correction for `relay.NodeID`); added one docstring rule line citing spec-032 Decision 8; removed the staged `TODO(spec-032-full_relay-0_0_9 Slice 1)` anchor block.
- `tests/types/test_base.py` — replaced the staged Slice-1 TODO block with the eight tests plus the small in-file `_declare_category_type_with_interface` helper; added top-level `import strawberry` and `from strawberry import relay` imports (existing function-local `from strawberry import relay` imports in older tests were left untouched per the no-unrelated-cleanup rule).

### Tests added or updated

- `tests/types/test_base.py::test_interfaces_rejects_relay_globalid_named` — `relay.GlobalID` named + "scalar-like id wrapper" + the automatic-`id: GlobalID!`-from-`relay.Node` fragment.
- `tests/types/test_base.py::test_interfaces_rejects_relay_nodeid_named` — `relay.NodeID` named + "annotation helper" fragment + the add-`relay.Node` remediation (locks the early-branch placement: the `Annotated` alias never reaches the non-class rejection).
- `tests/types/test_base.py::test_interfaces_rejects_relay_connection_named` — `relay.Connection` + "generic output type" + `Meta.connection` + `DjangoConnectionField`.
- `tests/types/test_base.py::test_interfaces_rejects_relay_listconnection_named` — same connection-surface remediation for `relay.ListConnection`.
- `tests/types/test_base.py::test_interfaces_rejects_relay_edge_named` — machinery-instantiated / not-consumer-declarable description.
- `tests/types/test_base.py::test_interfaces_rejects_relay_pageinfo_named` — "generated pagination type" description.
- `tests/types/test_base.py::test_interfaces_rejects_non_interface_class_named` — re-affirmation pin: generic branch still names the offending class + "is not a Strawberry interface".
- `tests/types/test_base.py::test_connection_key_requires_relay_node` — re-affirmation pin: full documented `Meta.connection` gate remediation ("requires a Relay-Node-shaped type" + add-`relay.Node`-or-inherit wording).

### Validation run

- `uv run ruff format .` — pass (1 file reformatted: `tests/types/test_base.py`, blank-line normalization of my own new code; slice-intended).
- `uv run ruff check --fix .` — pass ("All checks passed!", no fixes applied).
- `git status --short` after both ruff invocations: `M django_strawberry_framework/types/base.py` (slice-intended), `M tests/types/test_base.py` (slice-intended), `?? docs/builder/bld-slice-1-validation_diagnostics.md` + `?? docs/builder/build-032-full_relay-0_0_9.md` (this build's own artifacts), and the eight `D docs/builder/*.md` deletions which are the build plan's documented pre-flight cleanup baseline (workers do not restore). No unrelated tool churn; nothing reverted.
- Focused tests: `uv run pytest tests/types/test_base.py --no-cov` — 99 passed (includes the eight new tests). `uv run pytest tests/types/test_relay_interfaces.py --no-cov` — 115 passed (existing generic-rejection tests unaffected, as the plan predicted).

### Implementation notes

- Table shape: tuple of plain 3-tuples `(helper_object, "relay.<Name>", description)` typed `tuple[tuple[object, str, str], ...]` (`object` because `relay.NodeID` is not a `type`). Chose plain tuples over NamedTuples — three positional fields unpacked at one call site didn't justify a named class (plan discretion item 1).
- Remediation tail: the plan requires every message to name `relay.Node` as what the consumer probably meant, but the Decision-8 fragments for `NodeID` / `Edge` / `PageInfo` don't mention it. Rather than fork per-row remediation text, all six messages share one module-level suffix `_RELAY_NON_INTERFACE_REMEDIATION` ("If the goal is a Relay-Node-shaped type, add `relay.Node` to `Meta.interfaces` instead.") appended after the verbatim Decision-8 description. One literal, uniform shape; `GlobalID`'s description also mentions `relay.Node` (verbatim from Decision 8), so that message names it twice — accepted as the cost of the single-suffix DRY shape.
- `Connection` / `ListConnection` share `_RELAY_CONNECTION_HELPER_DESCRIPTION` (Decision 8 row 4: "same remediation as `Connection`") so the literal exists once.
- Tests use `str(excinfo.value)` substring assertions rather than `pytest.raises(match=...)` (plan discretion item 3) — the documented messages are backtick/paren-heavy and substring checks avoid regex escaping noise.
- Test boilerplate: one in-file helper `_declare_category_type_with_interface(entry)` shared by the six named tests and the non-interface-class pin (plan discretion item 2); the `Meta.connection` pin inlines its own class because its Meta shape differs (no `interfaces` key).

### Notes for Worker 3

- No shadow files were used or regenerated this pass; the plan's static-inspection findings (single-raise-site, ~2 added branch nodes) were followed as written — the new code in `_validate_interfaces` is one `for` + one `if` + one raise.
- The named branch sits between the string-entry rejection and the `not isinstance(entry, type)` branch — earlier than the staged TODO's position — per the plan's step-2 placement correction for the `relay.NodeID` `Annotated` alias. `test_interfaces_rejects_relay_nodeid_named` is the test that fails if the branch is moved back down.
- The two re-affirmation pins deliberately near-duplicate `tests/types/test_relay_interfaces.py::test_meta_interfaces_rejects_non_interface_classes` and `tests/types/test_base.py::test_meta_connection_non_relay_type_raises`; the plan's DRY analysis pre-justifies the overlap (full-message pins vs loose-fragment matches).
- The `git status --short` `D docs/builder/*.md` entries are the build plan's pre-flight cleanup, not this slice's churn.

### Notes for Worker 1 (spec reconciliation)

- Confirmed the plan's Worker 1 finding against the locked Strawberry install: `isinstance(relay.NodeID, type)` is `False` (`typing._AnnotatedAlias`); the other five helpers are classes. The spec's Current state (line 139) and Decision 8 (line 413) wording ("all six … take the generic path / fail through the generic branch") remains inaccurate for `NodeID` exactly as the plan recorded — the suggested one-line spec wording fix still applies.
- Small, mechanically obvious drift (recorded per worker-2.md): the shared remediation suffix means the `NodeID` / `Edge` / `PageInfo` messages carry remediation text beyond their verbatim Decision-8 fragments, and the `GlobalID` message names `relay.Node` twice (once in its verbatim fragment, once in the suffix). The verbatim fragments themselves land unmodified. If Worker 1 prefers fragment-only messages for the three rows whose fragments already read as complete sentences, it is a row-text-only change with matching test-assertion updates.

---

## Review (Worker 3)

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

- **Message-prefix fragment `".Meta.interfaces entry "` now appears twice** (the new named raise at `base.py::_validate_interfaces` #"entry {label} is" and the pre-existing generic raise at `base.py::_validate_interfaces` #"entry {entry.__name__} is not a"). Shadow overview confirms `2x '.Meta.interfaces entry'` under Repeated string literals. Not blocking: the house precedent (`_INTERFACES_SHAPE_ERROR_LEAD_IN`) constant-izes a lead-in shared by three+ raise sites; a 2x f-string prefix constant would hurt readability more than it saves. **Deferred follow-up for Worker 1 to weigh at the integration pass** (if Slice 3's `_validate_relation_shapes` grows a third `…Meta.<key> entry…` shape, revisit).
- The plan's pre-justified overlaps hold as described: the two re-affirmation pins near-duplicate `tests/types/test_relay_interfaces.py::test_meta_interfaces_rejects_non_interface_classes` and `tests/types/test_base.py::test_meta_connection_non_relay_type_raises`, but assert the *full documented messages* where the existing tests match loose fragments. Verified both source messages against the pin assertions character-for-character (connection gate: "requires a Relay-Node-shaped type; add \`relay.Node\` to \`Meta.interfaces\` or inherit \`relay.Node\` directly."; generic branch names the class via `entry.__name__`). Justified, not a finding.
- `_RELAY_CONNECTION_HELPER_DESCRIPTION` and `_RELAY_NON_INTERFACE_REMEDIATION` single-source the two fragments that would otherwise repeat (Connection/ListConnection shared row text; the six-message remediation tail). One raise site, six data rows — the table shape the plan mandated landed exactly.
- Test boilerplate: the six named tests plus the non-interface-class pin share `_declare_category_type_with_interface`; the `Meta.connection` pin correctly inlines its own class (different Meta shape). No copy-paste residue.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is empty (0 lines). No new public exports; matches the slice (Decision 8 ships no new surface — `DjangoNodeField`/`DjangoNodesField` exports belong to Slice 2).

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces.

### What looks solid

- **The NodeID placement correction is real and correctly handled.** The named branch sits after the string-entry rejection and before the `not isinstance(entry, type)` branch; `relay.NodeID` (a `typing.Annotated` alias, not a class) would otherwise die unnamed in the non-class branch. `test_interfaces_rejects_relay_nodeid_named` locks the placement — it fails if the branch moves below the non-class check.
- **Identity matching (`entry is helper`) over dict lookup** is the right call: unhashable consumer entries cannot raise `TypeError`, and the `Annotated` alias's nonstandard `__eq__`/`__hash__` is sidestepped. Verified by temp probe (below).
- **All six Decision-8 message fragments land verbatim** — checked each row of `_RELAY_NON_INTERFACE_HELPERS` against the spec's Decision 8 list 1–6 (markdown link syntax correctly stripped from the Connection row). Connection/ListConnection both name `Meta.connection` and `DjangoConnectionField`.
- **Spec slice checklist walk: all three boxes ticked, all three contracts present in the diff.** (1) named branch with all six helpers, fires before the generic rejection; (2) both re-affirmation pins with the documented full messages; (3) `tests/types/test_base.py` carries exactly the eight Test-plan-named tests. No over-ticks, no silently un-addressed sub-checks.
- **Hotspot budget held.** Static inspection (re-run this pass): `_validate_interfaces` is 90 lines / 15 branch nodes — the plan predicted 13 + ~2; the new code is one `for` + one `if` + one raise. Django/ORM marker walk over the touched region (base.py 739–878): the only marker is the pre-existing `DjangoType`-subclass rejection branch (justified, untouched); the slice adds no ORM/queryset behavior.
- The staged Slice-1 TODO anchors (source + test) are removed in the same change, per AGENTS.md; the Slice-3 anchors are untouched.
- Focused runs confirm Worker 2's report: `uv run pytest tests/types/test_base.py tests/types/test_relay_interfaces.py --no-cov` — 214 passed (no regression in the existing generic-rejection tests).

### Temp test verification

- `docs/builder/temp-tests/slice-1/test_unhashable_entry_probe.py` — the plan-suggested probe: an unhashable `Meta.interfaces` entry (`[1, 2]`) produces the existing "must contain interface classes" shape error with no `TypeError` from the named branch. Passed (1 passed).
- Disposition: **deleted after the pass.** It proves a by-construction property of the identity loop and exercises no new branch — the non-class rejection path is already permanently pinned by existing tests (`object()` / int entries in `tests/types/test_relay_interfaces.py`). Not promoted.

### Notes for Worker 1 (spec reconciliation)

- Echoing the plan's and Worker 2's already-recorded item: spec Current state (line 139) and Decision 8 (line 413) say all six helpers take the generic non-interface path today; `relay.NodeID` actually fails through the earlier non-class branch. The suggested one-line wording fix stands.
- Worker 2's shared-remediation-suffix drift note: the suffix is what satisfies the slice checklist's "what the consumer probably meant (`relay.Node`, …)" requirement for the `NodeID` / `Edge` / `PageInfo` rows, whose verbatim Decision-8 fragments never name `relay.Node` — so I read the suffix as contract-required, not gold-plating. The only cosmetic cost is `GlobalID` naming `relay.Node` twice. Recommend accepting as-shipped; a fragment-only trim for the three "complete-sentence" rows would *weaken* checklist conformance.
- DRY deferral for the integration pass: the 2x `".Meta.interfaces entry "` prefix (see DRY findings) — revisit only if Slice 3 adds a third occurrence of the shape.

### Review outcome

`review-accepted` — no High/Medium/Low findings; DRY observations recorded as deferred follow-ups for Worker 1; all three spec sub-checks verified against the diff; public-surface check clean; focused tests pass.

---

## Final verification (Worker 1)

- **Spec slice checklist audit:** all three `- [x]` boxes verified against the working-tree diff — no over-ticks, no un-ticked landed boxes, no deferrals. (1) The named-helper rejection branch is in `django_strawberry_framework/types/base.py::_validate_interfaces` (identity-matched loop over `_RELAY_NON_INTERFACE_HELPERS`, all six helpers, single raise site), placed after the string-entry rejection and **before** the `not isinstance(entry, type)` non-class branch — satisfying "fires before the generic one" for all six including the `Annotated`-alias `relay.NodeID`; each message names the helper, carries its verbatim Decision-8 description, and ends with the `relay.Node` remediation (`Connection`/`ListConnection` additionally name `Meta.connection` / `DjangoConnectionField`). (2) Both re-affirmation pins land with the documented full messages and no behavior change. (3) `tests/types/test_base.py` carries exactly the eight Test-plan-named tests (six named rejections + two pins). The staged Slice-1 TODO anchors (source + test) are removed in the same change; Slice-3 anchors untouched.
- **DRY check:** first slice of the build — no prior accepted slices to cross-check. Within the slice: one raise site + six data rows; `_RELAY_NON_INTERFACE_REMEDIATION` and `_RELAY_CONNECTION_HELPER_DESCRIPTION` single-source the repeatable fragments; tests share `_declare_category_type_with_interface`. Worker 3's deferred item — the 2x `".Meta.interfaces entry "` f-string prefix — is confirmed as a correctly-deferred integration-pass watch item (revisit only if Slice 3's `_validate_relation_shapes` adds a third occurrence); not a blocker now, a constant for a 2x prefix would hurt readability.
- **Tests:** `uv run pytest tests/types/test_base.py tests/types/test_relay_interfaces.py --no-cov` — **214 passed** (matches Worker 2's and Worker 3's runs; no regressions in the existing generic-rejection tests). No coverage flags used.
- **Spec reconciliation:** the recorded NodeID wording inaccuracy is real (confirmed by both Worker 2 and Worker 3 against the locked Strawberry 0.316.0: `relay.NodeID` is a `typing._AnnotatedAlias`, not a class, so it failed via the non-class branch pre-slice, not the generic non-interface branch). Spec edited — see below. The shared remediation-suffix shape (Worker 2's drift note) is **accepted as-shipped**: the slice checklist requires every message to say "what the consumer probably meant (`relay.Node`, …)", and the `NodeID` / `Edge` / `PageInfo` Decision-8 fragments never name `relay.Node` — the suffix is what satisfies that contract (Worker 3's reading concurred; trimming it would weaken checklist conformance). The only cosmetic cost is `GlobalID` naming `relay.Node` twice. No spec edit needed for it; Decision 8's prose already describes exactly this outcome.
- **Final status:** `final-accepted`.

### Summary

Slice 1 ships the six named schema-validation diagnostics (spec-032 Decision 8): `relay.GlobalID` / `relay.NodeID` / `relay.Connection` / `relay.ListConnection` / `relay.Edge` / `relay.PageInfo` in `Meta.interfaces` are each rejected by a `ConfigurationError` naming the helper, what it actually is, and the remediation — via an identity-matched table (`_RELAY_NON_INTERFACE_HELPERS`) with a single raise site in `_validate_interfaces`, placed before the non-class branch so the `Annotated`-alias `NodeID` is named too. Two re-affirmation pins lock the already-shipped generic non-interface-class message and the `Meta.connection` Relay-Node gate message. Eight new tests in `tests/types/test_base.py`; no public-surface change; no behavior change outside the upgraded messages.

### Spec changes made (Worker 1 only)

- `docs/spec-032-full_relay-0_0_9.md` line 139 (Current state) — corrected "the six … helpers … all take that generic path today" to "all fail today — five through that generic path … while `NodeID` (a `typing.Annotated` alias, not a class) fails through the earlier 'must contain interface classes' non-class branch". Triggered by Slice 1 (plan + Worker 2 + Worker 3 all confirmed the inaccuracy against Strawberry 0.316.0).
- `docs/spec-032-full_relay-0_0_9.md` line 413 (Decision 8) — same correction ("five through the generic … branch, `NodeID` through the earlier non-class branch"), plus a parenthetical noting the named branch fires before the non-class branch so `NodeID` is named too. Triggered by Slice 1.
- `docs/spec-032-full_relay-0_0_9.md` line 5 (status line) — "planned — not started" updated to "in build — Slice 1 implemented (final-accepted in the build cycle, uncommitted); Slices 2–7 not started" per the worker-1.md per-spawn status-line re-verification rule. Triggered by Slice 1 final verification.

`scripts/check_spec_glossary.py --spec docs/spec-032-full_relay-0_0_9.md` re-run after the edits: OK (38 terms).
