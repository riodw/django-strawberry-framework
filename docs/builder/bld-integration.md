# Build: Cross-slice integration pass — spec-015 (consumer_overrides_scalar / 0.0.6)

Spec reference: `docs/spec-015-consumer_overrides_scalar-0_0_6.md`
Slices reviewed: 1, 2, 3, 4, 5 (all final-accepted before this pass)
Status: final-accepted (re-verified pass 2)

## DRY scan (Worker 1)

### Cross-slice helper duplication

- **`_is_relay_shaped(cls, interfaces)` predicate duplicated verbatim at two sites in `django_strawberry_framework/types/base.py`.** The exact idiom `any(issubclass(i, relay.Node) for i in interfaces) or issubclass(cls, relay.Node)` appears at:
  - `django_strawberry_framework/types/base.py:173` — new H1 Relay collision guard in `DjangoType.__init_subclass__` (added by Slice 1).
  - `django_strawberry_framework/types/base.py:729` — pre-existing `suppress_pk_annotation` in `_build_annotations` (pre-Slice-1, unchanged by this build).

  Both sites are character-for-character identical (verified via grep). Worker 1's Slice 1 plan and Worker 3's Slice 1 review both explicitly flagged this for the integration pass. Worker 1's final-verification accepted the deferral. The two sites have different timing (class-creation-time vs. annotation-synthesis-time) but read the same predicate from the same inputs (`cls`, `interfaces` from `_validate_meta`).

  **Recommendation: consolidate NOW.** Extract a module-scope `_is_relay_shaped(cls, interfaces: tuple) -> bool` helper next to the existing `_NODEID_STRING_RE` / `_has_node_id_marker` / `_id_annotation_is_relay_node_id` cluster in `types/base.py`. Replace both call sites with a single helper call. The extraction is one small helper with two call sites that read the same inputs; the "different timing" framing is not load-bearing — both sites compute the same boolean from the same data, and the predicate's truth value is the contract, not the timing of its computation. Deferring further would entrench the duplication; addressing it now closes the explicit deferral cleanly.

- **No other cross-slice helper duplication.** Slice 2 was pure subtractive (test delete). Slice 3 was docstring-only and explicitly chose to cross-reference rather than duplicate the four-corner narrative — `grep -c "four-corner" django_strawberry_framework/types/base.py` returns `1` (only in `_consumer_assigned_fields`'s docstring). Slices 4 and 5 touched no source code. No new helper signatures were introduced beyond Slice 1's three helpers (`_NODEID_STRING_RE`, `_has_node_id_marker`, `_id_annotation_is_relay_node_id`), each with a single responsibility and one or two call sites.

### Repeated string literals / keys / tuples

Comparing the **Repeated string literals** sections across the fresh static-inspection overviews:

- `django_strawberry_framework/types/base.py`: `4x optimizer_hints`, `2x description`, `2x interfaces`. All three are existing pre-Slice-1 literals (Meta keys + an existing-since-foundation field name); Slice 1's additions did not push any new literal above the 2x threshold inside `base.py`.
- `django_strawberry_framework/types/definition.py`: no repeated literals (the dataclass body is unique field names).
- `tests/types/test_definition_order.py`: `6x relay.NodeID`, `5x GlobalID`, `2x relay.NodeID[int]`, `13x description`, `14x category`, `5x NON_NULL`, `4x PendingRelationAnnotation`, plus several existing-pre-Slice-1 literals.

Cross-file analysis:

- **`relay.NodeID` (6x) and `GlobalID` (5x) in `test_definition_order.py`** — these are the Slice 1 reject-test error-message keyword assertions. Worker 3's Slice 1 review classified them as intentional spec-pinned contract assertions; consolidating into a module-level constant would obscure the per-test contract documentation (each test's reject path is documented inline by the keyword it asserts). **Verdict: keep as-is.** Pinning a contract via inline assertion text is more readable than indirecting through a `_RELAY_ID_KEYWORDS = ("relay.NodeID", "GlobalID")` constant; the spec explicitly required these keyword pins per slice checklist.

- **`relay.NodeID` (6x) in test file vs `relay.NodeID[<pk_type>]` in error messages in source.** The source error messages at `base.py:178-190` and `:192-198` include the `relay.NodeID[<pk_type>]` phrasing as guidance text, and the tests assert the `relay.NodeID` substring matches. This is two sides of one contract (source emits the keyword; tests pin that the keyword is emitted). No DRY action needed — splitting "keyword to emit" from "keyword to assert" would create a new indirection-by-constant for zero readability gain.

- **`PendingRelationAnnotation` (4x in test_definition_order)** — pre-existing fixture pattern; not introduced by Slice 1.

- **`NON_NULL` (5x in test_definition_order)** — introduced by Slice 1's four end-to-end introspection tests + the cross-type cache test. The literal is the GraphQL spec's `NON_NULL` kind discriminator; it appears identically in `tests/types/test_converters.py` (`5x NON_NULL` in that file's existing introspection tests). Cross-file repetition of the GraphQL kind discriminator is unavoidable — the introspection-query response keys are part of the GraphQL contract.

- **No new cross-file repeated literal exceeded the 2x intra-file threshold.** The `_is_relay_shaped` predicate's two call sites are NOT a "repeated literal" finding (the predicate is a code expression, not a string literal); they are the helper-duplication finding above.

### Inconsistent naming or error handling

- **None observed.** The H1 guard's two error messages (assigned-side at `base.py:178-190` and annotation-side at `:192-198`) follow the same `f"{cls.__name__}: cannot override the id field on a relay.Node-shaped type..."` opening and end with the same "or remove relay.Node from Meta.interfaces" recourse. The error class (`ConfigurationError`) matches the rest of the package's type-creation-time validation surface. Worker 3's Slice 1 review confirmed the error-message keyword overlap is intentional contract pinning, not drift.

- **Slice 3's docstring update consolidated the narrative voice.** The canonical four-corner narrative lives in `_consumer_assigned_fields`'s docstring; `_build_annotations`'s docstring cross-references via "See `_consumer_assigned_fields` for the four-corner override contract that populates `consumer_authored_fields`". No "two voices of the same story" risk.

- **Slice 5's narrative voices across FEATURES.md / KANBAN / CHANGELOG / TODAY / docs/README.md** are intentionally separate audiences of the same contract (Worker 3's Slice 5 review verified cross-file consistency). The resolver-backed sibling-field workaround example appears identically in KANBAN, FEATURES, and CHANGELOG; this is a documentation-narrative repetition, not a code-duplication concern.

### Module responsibility boundaries

- **Slice 1 added all new logic to `django_strawberry_framework/types/base.py`** (the three module-scope helpers, the collection line, the union splat, the H1 guard) — the same module that already owns `DjangoType.__init_subclass__`. No cross-module dependency direction shift.

- **`django_strawberry_framework/types/definition.py`** gained one new dataclass field (`consumer_annotated_scalar_fields: frozenset[str]`). Definition's imports are unchanged from the foundation slice (`field_meta`, `hints`, `models`, dataclass, `Any/Literal`). The new field is consumed by Slice 1 tests via the `__django_strawberry_definition__` attribute on the registered type; no consumer-facing import surface change.

- **No sibling module started importing from outside the documented boundary.** The Slice 1 imports section in the fresh shadow overview shows `from strawberry.relay.types import NodeIDPrivate` as the only new third-party import — a single Strawberry-internal symbol used by the H1 guard's marker-detection. This is consistent with the package's existing strawberry-relay dependency (already imported as `from strawberry import relay` at the same site).

- **Tests in `tests/types/test_definition_order.py`** gained `sys`, `types`, `uuid`, `django.db.models`, `strawberry.relay`, `_build_annotations`, `NodeIDPrivate`-adjacent imports (only `relay`, no direct `NodeIDPrivate`). The `_build_annotations` import is a whitebox import for the synthesis-skip test; standard practice and matches sibling test_converters.py.

### Public-surface check

Confirmed: `git diff -- django_strawberry_framework/__init__.py` returns empty across the entire build. `__all__` is unchanged through Slices 1-5. No new public exports were introduced. Spec sub-check (Definition of done) "No new public top-level symbol; no new `Meta.*` key; `django_strawberry_framework/__init__.py.__all__` is unchanged" verified end-to-end.

### Test-tree consistency

- **Inline `models.Model` `Meta` convention drift** flagged by Worker 3's Slice 1 Low finding: the four inline test-models added by Slice 1 to `tests/types/test_definition_order.py` (`UnsupportedFieldOwner` at `:430-434`, `GroupedChoiceOwner` at `:459`, `CoResidentChoiceOwner` at `:486`) set `app_label` only. The sibling pattern in `tests/types/test_converters.py` consistently sets `managed = False` alongside `app_label` (the converter-host file has 9+ inline models, all with both). Tests pass either way under the test runner (Django's test runner does not migrate test-only models so `managed = False` is informationally redundant under pytest), but the convention is "both" elsewhere in the test tree.

  **Recommendation: defer.** Stylistic-only convention drift; no functional difference under the test runner. The three test models are inline-defined inside test-function bodies, scoped to single tests via `Meta.app_label` namespacing; the lack of `managed = False` does not change test behavior. Consolidating would touch three Slice 1 test functions for cosmetic-only gain. If a future test author standardizes test-model declarations across the tree (a separate cleanup card), these three sites should land in the same change. Recording here as deferred follow-up; not load-bearing for this build's closeout.

- **`_introspect_field_type` test-helper duplication** flagged by Worker 3's Slice 1 DRY finding. The helper is defined at `tests/types/test_converters.py:434` and used 18 times in that file. Four near-copies of the same `__type(name: "<TypeName>") { fields { name type { kind name ofType { kind name } } } }` introspection-query pattern were inlined by Slice 1 in `tests/types/test_definition_order.py` at:
  - `:413` — `test_annotation_only_scalar_override_survives_strawberry_finalization`
  - `:518-521` — `test_annotation_override_does_not_populate_shared_enum_cache_for_co_resident_types` (uses GraphQL alias `__overrideTwo:` for two types in one query)
  - `:685` — `test_consumer_id_resolved_string_relay_nodeid_annotation_on_relay_node_type_is_accepted_end_to_end`
  - `:775` — `test_inherited_id_annotation_on_relay_node_subclass_is_handled_by_pk_suppression`

  The four near-copies vary slightly: the `:518-521` site uses GraphQL aliases to query two types in one introspection request; the other three are single-type queries. The walk-pattern after execute (`{f["name"]: f["type"] for f in ...}`) is also inlined separately in each test. Promoting `_introspect_field_type` to `tests/types/conftest.py` would let both test files consume it.

  **Recommendation: defer.** Although the introspection-query shape is duplicated, the four sites have legitimate variation (single-type vs alias-multi-type queries). Worker 1's Slice 1 plan explicitly preferred inline-introspection over cross-file imports for the test-body-readability reason; Worker 3 concurred. A shared helper would need either a `types: list[str]` parameter to handle the alias case or two separate helpers; either shape adds API surface for marginal gain. The duplication stays inside the test tree and is bounded; aligning it across `test_converters.py` and `test_definition_order.py` is a candidate for a future test-infrastructure card but not load-bearing for this build's closeout.

- **No new test-placement convention violations.** The 18 Slice 1 tests in `test_definition_order.py` and the 1 Slice 1 test in `test_converters.py` match the spec's placement contract (rev6 L3 + rev8 L2 + rev10 L1). Slice 2's deletion in `test_base.py` cleanly removed the previously-skipped test without orphaning imports.

### Decision

**Consolidation needed for one item; the other items are intentional deferrals.**

The integration pass identifies one clear consolidation candidate to land NOW via a Worker 2 → Worker 3 loop:

- **`_is_relay_shaped(cls, interfaces)` helper extraction in `django_strawberry_framework/types/base.py`.** Extract a module-scope helper next to the existing `_NODEID_STRING_RE` / `_has_node_id_marker` / `_id_annotation_is_relay_node_id` cluster, then replace the two call sites (`:173` and `:729`) with the helper call. Both sites use the exact same idiom; both read the same inputs; the predicate is well-localized. Worker 1 (this pass) and Worker 3 (Slice 1 review) both pre-flagged this for integration-pass action; the deferred call was always "decide at integration, not at Slice 1." Decision: consolidate.

Two items are recorded as intentional deferrals for the maintainer and future spec authors:

- **`_introspect_field_type` test-helper promotion to `tests/types/conftest.py`** — deferred because the four near-copies have legitimate variation (alias-multi-type vs single-type queries) and a parametrized shared helper would add API surface for marginal gain. Worth a future test-infrastructure card if more callers surface.

- **Inline test-model `Meta` convention alignment** — deferred because the drift is stylistic-only with no functional impact under the test runner. Worth folding into a future test-tree-wide cleanup card if one ships.

**Consolidation work for Worker 2 (next pass):**

Implement `_is_relay_shaped` helper extraction in `django_strawberry_framework/types/base.py`:

1. **Add a new module-scope helper** above `class DjangoType` (immediately after the existing `_id_annotation_is_relay_node_id` helper at the end of the helper cluster). The helper signature and body:
   ```python
   def _is_relay_shaped(cls: type, interfaces: tuple) -> bool:
       """Return True when ``cls`` or any entry in ``interfaces`` is a Relay-Node-shaped type.

       Single source of truth for the predicate that drives both the H1
       Relay ``id`` collision guard at ``DjangoType.__init_subclass__`` and
       the synthesized-``id``-annotation suppression branch in
       ``_build_annotations``. Both call sites compute the same boolean
       from the same inputs at different timings (class-creation-time vs.
       annotation-synthesis-time); centralizing the predicate keeps the
       Relay-shape contract single-sited.
       """
       return any(issubclass(i, relay.Node) for i in interfaces) or issubclass(cls, relay.Node)
   ```

2. **Replace the call site at `django_strawberry_framework/types/base.py:173`** (inside `DjangoType.__init_subclass__`, the H1 guard). Change:
   ```python
   relay_shaped = any(issubclass(i, relay.Node) for i in interfaces) or issubclass(cls, relay.Node)
   ```
   to:
   ```python
   relay_shaped = _is_relay_shaped(cls, interfaces)
   ```

3. **Replace the call site at `django_strawberry_framework/types/base.py:729`** (inside `_build_annotations`, the `suppress_pk_annotation` computation). Change:
   ```python
   suppress_pk_annotation = any(issubclass(i, relay.Node) for i in interfaces) or issubclass(cls, relay.Node)
   ```
   to:
   ```python
   suppress_pk_annotation = _is_relay_shaped(cls, interfaces)
   ```
   Preserve the surrounding inline-comment block at `:725-728` and `:730-734` verbatim — those comments document the local reasoning (interface-class validation, `pk_name` naming choice) and complement the helper's docstring.

4. **No test additions or updates required.** The behavior is unchanged; the existing 19-test Slice 1 cluster (specifically the 11 Relay-collision tests for the H1 guard call site and the existing `test_relay_interfaces.py` suite for the `_build_annotations` suppression call site) exercises both branches. The consolidation is a pure refactor with identical truth-value semantics; no new branches or behaviors are introduced.

5. **Validation expectations.** `uv run ruff format .` and `uv run ruff check --fix .` should be no-ops or report only the slice-intended `types/base.py` edit. Focused tests for confirmation:
   - `uv run pytest tests/types/test_definition_order.py --no-cov -q` (the H1 guard call site)
   - `uv run pytest tests/types/test_relay_interfaces.py --no-cov -q` (the `_build_annotations` suppression call site)
   - `uv run pytest tests/types/ --no-cov -q` (full types/ tree to confirm no regression)

The consolidation is one small commit (one new helper + two single-line call-site replacements) with no behavior change. Worker 2 transcribes mechanically; Worker 3 reviews the diff against this artifact's consolidation spec. After Worker 3 accepts, Worker 1 (re-spawned) flips the status to `final-accepted`.

---

## Consolidation pass artifacts (added after Worker 2 / Worker 3 loop completes)

_To be appended below this line by Worker 2's build report and Worker 3's review pass once the consolidation lands. Status: `planned` until consolidation is final-accepted._

---

## Build report (Worker 2)

### Files touched

- `django_strawberry_framework/types/base.py` — extracted module-scope helper `_is_relay_shaped(cls, interfaces)` immediately after the existing `_id_annotation_is_relay_node_id` helper (above `class DjangoType`); replaced two duplicated predicate sites with calls to the helper.

### Tests added or updated

- None. The new helper is exercised by the existing tests at both call sites:
  - H1 Relay collision guard call site in `DjangoType.__init_subclass__`: covered by Slice 1's 11 Relay-collision tests (5 reject + 6 accept) in `tests/types/test_definition_order.py`.
  - `_build_annotations` pk-suppression call site: covered by the pre-existing `tests/types/test_relay_interfaces.py` suite (35+ tests covering `Meta.interfaces`, direct-relay subclasses, composite-pk scenarios, and the synthesized-`id`-suppression branch).

### Validation run

- `uv run ruff format .` — pass (100 files left unchanged; trailing-comma layout for the helper was preserved by ruff)
- `uv run ruff check --fix .` — pass (`All checks passed!`)
- `git status --short` after both ruff invocations:
  - Slice-intended (this consolidation): `django_strawberry_framework/types/base.py`
  - Carry-over from prior Slices 1-5 (not yet committed by maintainer; out of scope for this consolidation):
    - `CHANGELOG.md`
    - `KANBAN.md`
    - `TODAY.md`
    - `django_strawberry_framework/types/definition.py`
    - `docs/FEATURES.md`
    - `docs/README.md`
    - `pyproject.toml`
    - `tests/types/test_base.py`
    - `tests/types/test_converters.py`
    - `tests/types/test_definition_order.py`
  - Untracked carry-over from prior Slices 1-5 (not yet committed by maintainer; out of scope):
    - `docs/builder/bld-integration.md` (this artifact — currently untracked because the build plan only commits artifacts once they're finalized)
    - `docs/builder/bld-slice-1-annotation_scalar_overrides.md`
    - `docs/builder/bld-slice-2-unskip_consumer_annotation_test.md`
    - `docs/builder/bld-slice-3-document_override_contract.md`
    - `docs/builder/bld-slice-4-version_bump_quintet.md`
    - `docs/builder/bld-slice-5-docs_kanban_changelog_archive.md`
    - `docs/builder/build-015-consumer_overrides_scalar-0_0_6.md`
- Focused tests run: `uv run pytest tests/types/test_definition_order.py tests/types/test_relay_interfaces.py --no-cov -q` — 96 passed in 2.79s. Confirms both the new H1-guard tests (Slice 1) and the pre-existing pk-suppression tests still pass with the helper extraction.

### Implementation notes

- Helper signature: `def _is_relay_shaped(cls: type, interfaces: tuple[type, ...]) -> bool:` — `tuple[type, ...]` is the precise interfaces type (`_validate_meta` returns a tuple of interface classes, and the existing call sites take `interfaces` from `_validate_meta`'s return). The plan in the integration artifact specified `tuple` plain; tightening to `tuple[type, ...]` is consistent with the helper-cluster sibling `_id_annotation_is_relay_node_id(cls: type) -> bool` annotation style. No behavior delta.
- Helper body is the literal expression `any(issubclass(i, relay.Node) for i in interfaces) or issubclass(cls, relay.Node)` lifted verbatim from both call sites — single source of truth for the Relay-shape predicate.
- Helper placement: immediately after `_id_annotation_is_relay_node_id` (which itself sits at the end of the existing helper cluster `_NODEID_STRING_RE` / `_has_node_id_marker` / `_id_annotation_is_relay_node_id` above `class DjangoType`). This keeps all four Relay-shape-related module-scope helpers grouped together; a maintainer looking for "Relay-shape predicates" finds them in one contiguous block.
- The two call sites: `relay_shaped = _is_relay_shaped(cls, interfaces)` at `types/base.py:187` (was the H1 guard inside `__init_subclass__`, originally pinned at `:173` pre-helper-extraction); `suppress_pk_annotation = _is_relay_shaped(cls, interfaces)` at `types/base.py:743` (was the `_build_annotations` pk-suppression site, originally pinned at `:729` pre-helper-extraction). The surrounding inline-comment blocks at `:723-728` and `:730-734` of the second call site are preserved verbatim — they document the local reasoning (interface-class validation, `pk_name` naming choice) and complement the helper's docstring.

### Notes for Worker 3

- The new `_is_relay_shaped` helper is exercised by two code paths with different timings (class-creation-time vs. annotation-synthesis-time) but identical inputs and outputs at both. Verify that both code paths behave identically after the extraction — no regression in either the H1 guard's reject paths (5 reject tests in `test_definition_order.py`) or the pk-suppression's accept paths (the `test_relay_interfaces.py` suite, especially the inherited-id-annotation case at `test_inherited_id_annotation_on_relay_node_subclass_is_handled_by_pk_suppression`).
- The helper's type hint (`interfaces: tuple[type, ...]`) is tighter than the integration plan's `tuple` plain. This is a non-architectural tightening; if Worker 3 prefers the looser form for consistency with some other style guide, it can be relaxed without behavior change.
- Did not run `scripts/review_inspect.py`. This is a single-file two-line-replacement + one-helper-add change; the diff is small enough to read directly. No shadow file used during implementation.

### Notes for Worker 1 (spec reconciliation)

- None. The consolidation is a pure refactor with no behavior change; the spec contract is unchanged. No spec edits expected.

---

## Review (Worker 3)

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

- **Consolidation lands cleanly.** The `_is_relay_shaped(cls, interfaces)` helper at `django_strawberry_framework/types/base.py:129-140` is the single source of truth for the Relay-Node-shape predicate. `grep -n "issubclass(i, relay.Node)" django_strawberry_framework/types/base.py` returns exactly 1 hit — line 140, inside the helper body. Both prior call sites (the H1 guard in `__init_subclass__` at `:187`, the `suppress_pk_annotation` in `_build_annotations` at `:743`) now read `relay_shaped = _is_relay_shaped(cls, interfaces)` and `suppress_pk_annotation = _is_relay_shaped(cls, interfaces)` respectively. The duplication the integration scan flagged is gone.
- **No new DRY findings introduced.** The helper is a pure mechanical lift of a 2x-duplicated expression into a single named function. No new literals, no new helpers beyond the one promoted, no new imports. The static-inspection overview's `Repeated string literals` section still shows only the pre-existing 4x `optimizer_hints`, 2x `description`, 2x `interfaces` (all Meta-key + field-name literals predating Slice 1) — the consolidation added zero new repeated literals.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` returns empty. `__all__` and the re-export list are unchanged. The new helper is module-private (`_is_relay_shaped` — leading underscore) and is not exported. No public-surface change.

### CHANGELOG sanity

Not applicable; integration consolidation did not modify CHANGELOG.md.

### Documentation sanity

Not applicable; integration consolidation did not modify docs/release/KANBAN/archive surfaces.

### What looks solid

- **Helper placement.** `_is_relay_shaped` at line 129-140 sits immediately after `_id_annotation_is_relay_node_id` (line 90-126), grouping all four Relay-shape-related module-scope helpers (`_NODEID_STRING_RE`, `_has_node_id_marker`, `_id_annotation_is_relay_node_id`, `_is_relay_shaped`) into one contiguous block above `class DjangoType` at line 143. A maintainer searching for "Relay-shape predicates" finds them in one place.
- **Helper signature consistency.** `def _is_relay_shaped(cls: type, interfaces: tuple[type, ...]) -> bool:` matches the sibling helper style (`_id_annotation_is_relay_node_id(cls: type) -> bool`). Worker 2's note about tightening the integration plan's plain `tuple` to `tuple[type, ...]` is the right call — `_validate_meta` returns a `tuple[type, ...]` (line 495 signature), so the helper's annotation matches the actual input type.
- **Helper body preserves short-circuit semantics.** The body `any(issubclass(i, relay.Node) for i in interfaces) or issubclass(cls, relay.Node)` is character-for-character lifted from both original call sites. The `any(...)` short-circuits the generator; the `or` short-circuits the second `issubclass`. Both halves of the predicate evaluate in the same order as the originals — no subtle reordering that could change behavior for an edge case (e.g., a `cls` that raises on `issubclass` would now raise from inside the helper, but only if `interfaces` is empty or every entry already returned `False`, identical to the original).
- **Comment-block preservation.** The 18-line comment cluster at `:725-742` documenting `suppress_pk_annotation`'s reasoning (interfaces-vs-direct-inheritance, why `issubclass` per entry rather than `relay.Node in interfaces` membership) survives verbatim around the new call site at `:743`. The follow-on `pk_name` comment block at `:744-751` is also intact. The helper's docstring at `:130-138` complements (does not duplicate) the local reasoning.
- **Call-site call-shape consistency.** Both call sites use identical argument ordering: `_is_relay_shaped(cls, interfaces)`. No positional/keyword drift between the two.
- **Test coverage.** Focused tests confirm both code paths still pass: `uv run pytest tests/types/test_definition_order.py tests/types/test_relay_interfaces.py --no-cov -q` → 96 passed in 2.79s. The H1 guard's 11 Relay-collision tests (5 reject + 6 accept) in `test_definition_order.py` exercise the `__init_subclass__` call site; the `test_relay_interfaces.py` suite (35+ tests including the inherited-id-annotation case) exercises the `_build_annotations` pk-suppression call site.
- **Cumulative-diff hygiene.** Worker 2 explicitly classified each carry-over file in `git status --short` as out-of-scope (Slices 1-5 not yet committed by maintainer). The slice-intended diff is the single `django_strawberry_framework/types/base.py` hunk set. Net line accounting: helper adds 12 lines (def + docstring + body); two call sites collapse from a multi-token expression to a single function call (-1 line each at the predicate-expression level). Net for the consolidation is small positive (~+10 lines), consistent with the integration-plan expectation.

### Temp test verification

Not applicable; no temp tests needed for the helper extraction.

### Notes for Worker 1 (spec reconciliation)

None. The consolidation is a pure refactor with identical truth-value semantics at both call sites; no spec reconciliation needed. The spec contract for the H1 Relay collision guard (Slice 1 Decision 7) and the pk-suppression branch (pre-Slice-1 behavior) is preserved character-for-character.

### Review outcome

`review-accepted`. The `_is_relay_shaped` helper extraction lands the deferral Worker 1 (Slice 1 plan) and Worker 3 (Slice 1 review) both flagged for the integration pass. The duplication is gone, the placement matches the existing helper-cluster grouping, the focused tests still pass, the public surface is unchanged, and the comment-block reasoning around both call sites is preserved verbatim. Setting artifact `Status:` to `review-accepted`.

---

## Final verification (Worker 1)

- **Slice 1 deferral #1 — `_is_relay_shaped` extraction**: PASS. Consolidated on-disk. `_is_relay_shaped(cls: type, interfaces: tuple[type, ...]) -> bool` defined at `django_strawberry_framework/types/base.py:129-140`. Two call sites at `:187` (H1 guard inside `DjangoType.__init_subclass__`) and `:743` (`suppress_pk_annotation` inside `_build_annotations`). `grep -n "issubclass(i, relay.Node)" django_strawberry_framework/types/base.py` returns exactly one hit (line 140, inside the helper body), confirming the duplication is fully resolved. Worker 3 accepted the consolidation under the integration-pass review section above.
- **Slice 1 deferral #2 — `_introspect_field_type` shared test helper**: DEFERRED (recorded above under "Test-tree consistency"). Rationale captured: four near-copies in `tests/types/test_definition_order.py` have legitimate variation (alias-multi-type vs single-type queries); a parametrized shared helper would add API surface for marginal gain. Worth a future test-infrastructure card if more callers surface. Confirmed in the integration artifact's `### Test-tree consistency` subsection.
- **Slice 1 deferral #3 — test-placement convention drift (`managed`/`app_label`)**: DEFERRED (recorded above under "Test-tree consistency"). Rationale captured: stylistic-only convention drift with no functional impact under the test runner. Worth folding into a future test-tree-wide cleanup card if one ships. Confirmed in the integration artifact's `### Test-tree consistency` subsection.
- **DRY scan confirmation**: PASS. Re-walked the DRY scan after the helper consolidation landed. No cross-slice DRY issues remain open. The one mandated consolidation (`_is_relay_shaped`) has been implemented and review-accepted; the other two surfaced items are intentional deferrals with rationale, not unresolved findings. Repeated string literals, module boundaries, error-message consistency, and the public-surface check are all clean across Slices 1-5 plus the consolidation pass.
- **Existing tests still pass — broader scope**: PASS. `uv run pytest tests/types/ tests/base/ --no-cov -q` → 259 passed / 2 skipped (the 2 skips are pre-existing `test_converters` skips, not introduced or affected by this build). Both helper call sites are pinned by existing tests (the H1 guard's 11 Relay-collision tests + the `_build_annotations` pk-suppression's 35+ tests in `test_relay_interfaces.py`).
- **Spec reconciliation**: PASS — no edit needed. The integration-pass DRY consolidation is a pure refactor with identical truth-value semantics at both call sites; the spec contract for the H1 Relay collision guard (Slice 1 Decision 7) and the pk-suppression branch (pre-Slice-1 behavior) is preserved character-for-character. The spec is settled at rev10; integration-pass DRY consolidation does not change the contract. Spec status-line check: line 4 still says "draft (revision 10, post-rev9 review)" — accurate at this point (final test-run gate still ahead).
- **Final status**: `final-accepted`. Worker 3 accepted the consolidation and the broader-scope focused tests pass.

### Summary

The cross-slice integration pass closed cleanly. One DRY consolidation — extracting `_is_relay_shaped(cls, interfaces)` in `django_strawberry_framework/types/base.py` to centralize the Relay-Node-shape predicate that was duplicated verbatim between the new H1 collision guard (Slice 1) and the pre-existing `_build_annotations` pk-suppression branch — was implemented by Worker 2, accepted by Worker 3, and verified by Worker 1. Two other surfaced items (the `_introspect_field_type` shared test helper, and the inline test-model `managed`/`app_label` convention drift) are recorded as intentional deferrals with rationale in the DRY scan's `### Test-tree consistency` subsection. The 259-test focused sweep (`tests/types/` + `tests/base/`) confirms no regression. The spec contract is unchanged. Integration pass `Status: final-accepted`.

### Spec changes made (Worker 1 only)

None.

---

## Final verification (Worker 1, pass 2 — post-revision re-verification)

Triggered by the Slice 1 maintainer-feedback revision. Re-verified that the revision's two atomic edits did not affect this pass's findings.

- `_is_relay_shaped` helper and both call sites: unchanged. `grep -n "_is_relay_shaped\|issubclass(i, relay.Node)" django_strawberry_framework/types/base.py` returns exactly four lines — the helper definition at `:126`, its body's `issubclass(i, relay.Node)` at `:137` (sole occurrence in the file), and the two call sites at `:184` (H1 guard inside `__init_subclass__`) and `:740` (`suppress_pk_annotation` inside `_build_annotations`). The single-source-of-truth contract for the Relay-shape predicate is preserved.
- DRY scan: unchanged. The pass-2 revision is two atomic edits — M1 collapses a three-line dead block to a single delegation line in `_id_annotation_is_relay_node_id`'s success path, and L1 removes one unnecessary `registry.clear()` call in `test_consumer_id_typo_lookalike_nodeid_string_on_relay_node_type_raises`. Neither edit introduces duplication; neither edit touches the helper-cluster surface, the call-site surface, or any module-boundary shape.
- Spec rev 11 internal consistency: confirmed. Decision 7 pseudocode lands the leaner shape (`return _has_node_id_marker(hints.get("id"))`) and the revision-history entry for rev 11 is present at the bottom of the revision history block. The Slice 1 pass-2 final-verification artifact records both edits on disk (`grep "id_hint"` → 0 hits in `base.py`; `registry.clear()` in `test_definition_order.py` shows only the autouse-fixture sites at `:32`/`:34` and the rev8-M2-recipe `finally` at `:712`).

### Summary

The Slice 1 pass-2 edits (M1 dead-code removal + L1 test cleanup) are localized to `_id_annotation_is_relay_node_id` and `test_consumer_id_typo_lookalike_nodeid_string_on_relay_node_type_raises`; neither touches the integration pass's consolidation surface. Status re-`final-accepted`.

### Spec changes made (Worker 1 only)

None in this pass; the rev 11 edit was recorded in the Slice 1 artifact's Maintainer-feedback revision plan section.
