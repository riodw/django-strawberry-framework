# Rationale: spec-019 — Consumer override semantics for scalar fields (deliberation, rejected alternatives, change record)

Deliberative companion to [`spec-019-consumer_overrides_scalar-0_0_6.md`][spec-019]. The spec is the contract and states only what holds at `HEAD`; everything that explains **how it got there** lives here: eleven numbered revisions of review feedback, the alternatives each Decision rejected, every claim the spec once made and may no longer make, and the later commits and cards that reshaped what this one landed without ever touching the spec.

Created by the [`docs/builder/BUILD.md`][build] `## Spec rationale extraction` pass.

## Provenance of this record

**This pass performed a MOVE, not a reconstruction.** Spec-019 carried an unusually dense deliberative layer: a 53-line `Revision history (kept inline so the spec is self-contained)` block enumerating eleven review rounds with their H / M / L sub-items, plus **182 inline `rev<N> <H|M|L><n>` attributions** scattered through the Slice checklist, the Decisions, the Edge cases, the Test strategy, the Definition of done, and the verbatim KANBAN and CHANGELOG bodies — a spec that narrated its own history in almost every paragraph. Text marked **Moved** below was **cut** out of the spec, not copied: it exists here and nowhere else.

**Measured byte counts, both with `wc -c`, pinned to commit `435e190e` — the commit that landed this pair — rather than to a working tree:**

| File | Before this pass | After |
|---|---|---|
| `docs/SPECS/spec-019-consumer_overrides_scalar-0_0_6.md` | 181,073 | 104,017 |
| `docs/SPECS/appx/spec-019-consumer_overrides_scalar-0_0_6-rationale.md` | 0 (did not exist) | 48,834 |
| **Pair total** | 181,073 | 152,851 |

**The pair shrank by 28,222 bytes, which is what proves the move was a move and not a copy** — a copy would have left the pair total at or above 181,073. The reduction is falsified and superseded prose that was *deleted* rather than moved: chiefly the retired `typing.get_type_hints` fail-soft apparatus, described at length across six spec sections; the seven successive line-delta estimates; and the per-revision restatements of contracts that later revisions replaced.

**Two measurement points, deliberately not collapsed into one.** The table is the cycle's committed state at `435e190e`. The round that performed the move measured the companion at **47,488** bytes, for a pair total of **151,505** and a net of **-29,568**; the integration pass that followed added 1,346 bytes of custodial corrections to this file, which is the whole of the difference. Both readings are correct for their own moment and neither supersedes the other, so a later pass re-deriving one should not read the gap as drift. **Only the table re-derives.** The whole cycle landed as one commit, so R1's intermediate 47,488 / 151,505 / -29,568 was never a committed state and cannot be recovered from history; it is a historical measurement carried out of that round's artifact, which was itself deleted at closeout. Treat it as attributed, not verifiable, and do not go looking for a commit that shows it.

**Why the table is pinned to a commit and not to a live `wc -c`.** This file has grown since `435e190e`: the closeout pass that deleted the cycle's round artifacts resolved their inbound pointers, which is what put the figures above inline in the first place. Any number this file states about its own current size is invalidated by the edit that states it — the original reason these figures were a forward pointer rather than a table. Pinning to a commit is what makes them re-derivable (`git show 435e190e:<path> | wc -c`) instead of merely asserted, so **do not "correct" the table against a working tree**; a disagreement there is expected and is not drift.

These figures were originally left as a forward pointer into the round artifact, on the reasoning that a byte count written into the file it measures is a count of a file still being written. That reasoning was sound while the pass was running and is spent now that both files are final and committed; the pointer was resolved into the numbers when the round artifacts were deleted at closeout.

`HEAD` at the time of the pass is `09003dc2`. The package is at `0.0.14`; this card shipped at `0.0.6` on 2026-05-19.

**The card shipped as `015`, not `019`.** The build commit is `a357c68c` ("Finish docs/spec-015-consumer_overrides_scalar-0_0_6.md"). The 2026-07-30 board renumber moved the card from `015` to `019` and rewrote the filename and every card reference with it. Both numbers name one card. Three pre-renumber survivors are worth knowing about, because none of them is a defect:

- The landed tests bake `015` into synthetic identifiers: `tests/types/test_definition_order.py` uses `app_label = "test_spec015_unsupported"`, `"test_spec015_grouped_choices"`, `"test_spec015_co_resident"`, and `stub_name = f"spec015_unresolved_relay_stub_{uuid.uuid4().hex}"`. They match the spec's own rev8 M2 recipe, which itself named `spec015_…`. These are test-local synthetic strings with no cross-file consumer.
- `CHANGELOG.md`'s tracking label for this card reads `[015-consumer_override_semantics_scalar_fields-0.0.6]`, and its link definition resolves correctly.
- Revision 10's L2 entry (below) names "`spec-015` Slice 1" in prose.

A reader chasing `git log` for this spec's history should search `spec-015-consumer_overrides_scalar`, not `spec-019`, and will otherwise find nothing.

**Moved** — cut from the spec by this pass, and now only here:

- the whole `Revision history (kept inline so the spec is self-contained)` block, all eleven numbered revisions with their H / M / L sub-items;
- all 182 inline `rev<N> <H|M|L><n>` attributions, each folded into the revision entry or Decision entry it belongs to below;
- Decision 1's "Why two filters rather than one walk-and-bucket loop" and "Why filter on `not field.is_relation`" paragraphs;
- Decision 2's "Why not pass the four sets individually to `_build_annotations`" paragraph;
- Decision 5's two-option enumeration of the skipped test's fate and its recommendation;
- Decision 7's "Rev3 narrowing — what the predicate excludes", "Why `__init_subclass__` and not `_build_annotations` or `_validate_meta`", the `typing.get_type_hints` detection derivation, the "Narrow fail-soft on unresolved forward references" section, the "Marker detection — pinned shape" section, and the "finalize-time alternative was dropped" note;
- Decision 7a's "Why the bypass is the correct contract" paragraph;
- the `## Implementation plan` slice table's line-delta estimates and their per-revision history;
- every "Worker 1 picks during planning" / "Worker 1 may override" hedge (24 occurrences) that a later revision or the build itself resolved.

**Kept in the spec deliberately, against the pull of this move.** [`worker-1.md`][worker-1]'s carve-out for implementation-relevant rationale — the "why" that changes HOW a thing is built — is load-bearing here, and four passages exercised it:

- **Decision 7's guard-placement conclusion.** The guard must run between consumer-field collection and `_build_annotations`, because that is the only point where `cls.__annotations__`, `cls.__dict__`, and the validated `interfaces` tuple are all in hand and the error can still fire at class-creation time. A builder who does not know that puts the check in `_build_annotations` and the error surfaces at the wrong lifecycle point. The *rejected* placements moved here; the requirement stayed.
- **Decision 7's "keyed off the GraphQL field name `id`, not the model pk name."** This is a prohibition on a plausible implementation, not a derivation: a pk-keyed predicate rejects both the advertised `relay.NodeID[...]` escape hatch and every non-`id` custom-pk override.
- **Decision 7a's converter-bypass consequences.** The enumerated list of what `convert_scalar` stops doing for an overridden field is what the tests pin and what the GLOSSARY entry documents; it reads as deliberation but is the contract.
- **Decision 5's placement rule.** "The override matrix lives in one file" is why a new override test goes to `tests/types/test_definition_order.py` rather than beside whatever converter it exercises.

## What the card actually did, and what later cards did to it

### Nothing was skipped in the code

Verified against the working tree at `09003dc2` by this pass, independently of the build plan's pre-dispatch check:

- **Slice 1** — all four contracts landed. `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__` collects `consumer_annotated_scalar_fields`; `django_strawberry_framework/types/definition.py::DjangoTypeDefinition` carries the field in the grouped-by-style order; the union feeds `consumer_authored_fields`; the three module-scope helpers and the Relay `id` collision guard are live. All 19 Slice-1 tests exist under their own names — 18 in `tests/types/test_definition_order.py` and `test_annotation_override_of_arrayfield_with_nested_array_is_allowed` in `tests/types/test_converters.py`, exactly the placement split the spec mandates.
- **Slice 2** — `test_consumer_annotation_overrides_synthesized` is absent from the whole tree; the delete default was taken. `CATEGORY_SCALAR_FIELDS` stayed, because it is read at ~58 other sites in `tests/types/test_base.py`, so the conditional removal sub-check correctly did not fire.
- **Slice 3** — the four-corner matrix docstring is live on `django_strawberry_framework/types/base.py::_consumer_assigned_fields`.
- **Slice 4** — the version quintet is long past `0.0.6`; the package is at `0.0.14` and no stale `0.0.5` string survives at any of the five sites.
- **Slice 5** — the docs half holds end to end: `docs/GLOSSARY.md`'s `Scalar field override semantics` reads `shipped (0.0.6)` with the converter-bypass, Relay-collision, and metadata-limitation paragraphs; the index badge is flipped; `Scalar field conversion`'s MRO-walk paragraph names the annotation override as a parallel recourse to `Meta.exclude`; `Definition-order independence`'s "remain an implementation detail until …" closing sentence is gone; `docs/README.md` and `TODAY.md` both carry the capability; `CHANGELOG.md`'s `## [0.0.6] - 2026-05-19` section carries all five entries. The rev10 L2 temporary `[tool.ruff.lint.per-file-ignores]` ERA001 entry for the two `types/` modules was removed as specified — `pyproject.toml` carries no ERA001 ignore for any package path.

### The `relay.NodeID` detection mechanism was rewritten after the card shipped

This is the largest divergence between what the spec described and what runs, and the reason rev11 must not be read as the last word.

**What the spec described** (revisions 4 through 8, and rev11's own fix): detection ran `typing.get_type_hints(cls, include_extras=True)` inside a `try` / `except (NameError, AttributeError)`, with a **fail-soft** branch covering two named sub-cases — "the `id` annotation itself failed to resolve" (match the raw string against `_NODEID_STRING_RE`) and "some other annotation on the class failed to resolve while `id` is directly resolved" (delegate to `_has_node_id_marker` on the resolved object) — and a success path that returned `_has_node_id_marker(hints.get("id"))`.

**What `HEAD` does**: `django_strawberry_framework/types/base.py::_id_annotation_is_relay_node_id` does not call `typing.get_type_hints` at all. It reads `cls.__annotations__["id"]` directly and dispatches on `isinstance(raw, str)` — string form to the `_NODEID_STRING_RE` token match, resolved form to `_has_node_id_marker`. The `try` / `except`, the `hints` mapping, and the entire "fail-soft" vocabulary are gone.

**Why it changed**: commit `2bcd7f96` ("refactor: simplify `_id_annotation_is_relay_node_id` function for clarity and consistency - this fixes a coverage difference on Python3.10", 2026-05-21, two days after the card shipped). `typing.get_type_hints` handles nested forward references differently on Python 3.10 versus 3.11+, which left one branch of the helper reachable only on the newer interpreter — a coverage divergence at the supported floor, under a `fail_under = 100` gate. Reading the annotation directly removes the interpreter dependence entirely: the function's behavior is now identical on every supported Python version.

**What did NOT change**: the observable contract. Every one of the eleven Relay tests pins the same accept / reject verdicts and not one test name moved. The two "fail-soft sub-cases" collapse into the two arms of the `isinstance(raw, str)` dispatch — a NodeID-shaped string is accepted whether or not it would have resolved, and a directly-resolved `Annotated[int, NodeIDPrivate]` is accepted regardless of what a sibling annotation does, because a sibling annotation is now never consulted. The change is a simplification that happens to make the sibling-annotation case true by construction rather than by a recovery path.

**Consequences for the record:**

- **Rev11 is moot.** Its M1 dropped `if id_hint is None: return False` from the `hints.get("id")` delegation. The `hints` path no longer exists, so neither does the line rev11 removed. The helper instead subscripts `cls.__annotations__["id"]` and documents the call site's `has_id_annotation` precondition, deliberately preferring a loud `KeyError` from a future precondition-violating caller over a misleading `False`.
- **The retired vocabulary survives at four places in one test file, across three tests.** `tests/types/test_definition_order.py` carries: the name `test_consumer_id_unresolved_nodeid_shaped_string_on_relay_node_type_passes_guard_only`; the name `test_consumer_id_resolved_relay_nodeid_with_unresolved_sibling_annotation_is_accepted`, plus an inline comment inside that test reading "the fail-soft annotation walk accepts the directly-resolved NodeID-marked id even when another annotation on the same class fails to resolve"; and the docstring of a **third** test, `test_consumer_id_unresolved_non_nodeid_string_on_relay_node_type_raises`, reading "raises via the fail-soft regex reject". The two names are drawn from fail-soft sub-cases 1 and 2. All three tests still pin real, current contracts — a NodeID-shaped string is accepted by shape alone, an unresolved sibling annotation is irrelevant, and a non-NodeID string is rejected by the regex — but each carries vocabulary the mechanism no longer has. The occurrence count is four, not three: the file, not the number of tests, is the unit a future rename would open. Not renamed; recorded in the deferred-work catalog.
- **Rev6 H1's entire argument is now historical.** It fixed a real bug in the rev5 fail-soft branch (a resolved `id: relay.NodeID[int]` was falsely rejected whenever any sibling annotation failed to resolve). The bug class cannot recur under the current mechanism, because nothing on the class other than `id` is ever evaluated.

### Later cards reshaped three of this card's surfaces without touching the spec

- **`_is_relay_shaped` became a named module-scope helper.** Decision 7 and the Slice 1 checkbox describe the Relay-shape predicate inline as `any(issubclass(i, relay.Node) for i in interfaces) or issubclass(cls, relay.Node)`, computed at the guard. `HEAD` extracts `django_strawberry_framework/types/base.py::_is_relay_shaped`, whose docstring names it the single source of truth for both the collision guard and `_build_annotations`'s `suppress_pk_annotation`; commit `74d4a5b7` added a third consumer in the connection-validation path. The predicate is byte-equivalent; the single-siting is a later DRY improvement.
- **Both `consumer_annotated_*` comprehensions gained an `auto_annotated_fields` exclusion.** Decision 1's sample and the Slice 1 checkbox show `field.is_relation and field.name in consumer_annotations`. `HEAD` adds `and field.name not in auto_annotated_fields` to both, because an `auto`-typed annotation is a request for the model-inferred type, not a consumer override, and must not enter `consumer_authored_fields`. Landed with the later `auto`-typed-annotations card; this card's contract is unchanged.
- **`consumer_authored_fields` stopped being `_build_annotations`'s exclusive consumer.** Decision 2 stated it was "the only short-circuit input to `_build_annotations`". At `HEAD` the same union is additionally passed to `_validate_nullability_override_targets`, `_validate_filesystem_path_targets`, and `_validate_relation_shape_targets` (later `0.0.9` / `0.0.14` cards). Decision 2's *conclusion* — one union rather than four sets — held up and was reused three more times; only its exclusivity claim rotted.
- **`_consumer_assigned_fields` takes `cls`, not `cls.__dict__`.** The `## Current state` block and Decision 6's prose both showed `_consumer_assigned_fields(cls.__dict__, fields)`. `HEAD`'s signature is `_consumer_assigned_fields(cls: type, fields: tuple[Any, ...])`, and the function reads `cls.__dict__` internally. Decision 6's responsibility split is otherwise intact.
- **The guard's control flow was flattened.** Decision 7's pseudocode wrapped both reject paths in `if has_id_annotation or has_id_assignment:` and expressed the annotation-side accept as `if _id_annotation_is_relay_node_id(cls): pass  # Accept.` with the raise in the `else`. `HEAD` drops the outer conjunction and writes the annotation reject directly as `if has_id_annotation and not _id_annotation_is_relay_node_id(cls):`. Semantically identical; the `pass  # Accept.` branch that rev6 M2 argued about no longer exists in any form.

## Entries keyed to the spec

Each heading below names the spec section it belongs to. Anchors are the spec's own in-page anchors.

### The `Status:` line

The spec carried `Status: draft (revision 11, post-build maintainer-feedback pass)` for the whole of its shipped life. It was never a contract statement — a shipped card's spec is not a draft — and by the time this pass ran it named a revision whose one fix had been superseded. Replaced with the shipped state.

### `Revision history`, revisions 1-11

Moved whole. The block is the chronology the spec is not allowed to carry; every inline `rev<N> <H|M|L><n>` attribution elsewhere in the spec pointed back into it.

- **Revision 1** — initial draft. Surfaced the scalar/relation asymmetry in `_build_annotations`, pinned the symmetric annotation-only contract for scalars, confirmed the assigned-`strawberry.field` scalar contract already shipped in `0.0.5` and stayed unchanged, and proposed landing the previously-skipped `test_consumer_annotation_overrides_synthesized` as the proof.
- **Revision 2** (post-feedback review) — **H1**: rev1's Relay `id` edge case claimed a consumer `id: int` on a `Meta.interfaces = (relay.Node,)` type "would still raise `NodeIDAnnotationError` at finalization", which mis-ordered the lifecycle; the consumer-authored short-circuit runs before pk-suppression, so finalization succeeds and `strawberry.Schema(...)` fails later with a Strawberry-side `ValueError`. A schema-build `ValueError` is the wrong UX surface for a `DjangoType`-level configuration mistake, so the collision guard was added. **H2**: rev1's "no change to `_build_annotations` body" reading was too narrow — the short-circuit bypasses every `convert_scalar` validation, not just the enum-cache side effect; Decision 7a was added to pin the bypass explicitly with three new tests. **M1**: the end-to-end test's introspection assertion (`type.name == "Int"`) missed non-null unwrapping; rewritten to unwrap through `kind == "NON_NULL"`. **L1**: Slice 1's insertion-point instruction contradicted Decision 3's sample; the grouped-by-style order was picked and both sites aligned.
- **Revision 3** (post-rev2 review) — **H1**: rev2's guard predicate (`pk_name in consumer_annotated_scalar_fields or …`) was too broad. It rejected the advertised `id: relay.NodeID[int]` escape hatch (which lands in `consumer_annotated_scalar_fields` because `id` is a model pk field, so the guard would fire against the very pattern the error message recommends) and every non-`id` primary-key override (e.g. `code: str` on `models.CharField(primary_key=True)`, where the GraphQL fields are `id: ID!` and `code: String!` and there is no collision). The existing `tests/types/test_relay_interfaces.py::test_composite_pk_with_explicit_node_id_annotation_is_accepted` uses `name: relay.NodeID[str]` — the same shape rev2's guard would have rejected. Narrowed to the three-part predicate keyed off the GraphQL field name `"id"`. **M1**: the unsupported-field-type test recipe suggested `myfield: bytes`; Strawberry rejects `bytes` at schema construction, which would have failed for a reason unrelated to the bypass contract. Changed to `str`/`int`. **M2**: the `ArrayField` bypass test needs the existing `_ARRAY_FIELD_CLS` monkeypatch + `_FakeArrayField` fixture, so it was routed to `tests/types/test_converters.py` where they live. **L1**: four downstream cross-references were stale (status badge, two "Slice 6" references, the "no new error sites" glossary claim, and the implementation-plan table's Slice 1 row).
- **Revision 4** (post-rev3 review) — **H1**: rev3 left the detection mechanism as a choice between class-creation-time `typing.get_args` inspection and a finalize-time `cls.resolve_id_attr()` probe, without noticing the option contradicted the rest of the spec (the reject test asserts pre-`finalize_django_types()` failure and the CHANGELOG says `__init_subclass__` time). Option (ii) was dropped; class-creation time was pinned. Raw `get_args` was rejected too, because a stringified `id: "relay.NodeID[int]"` is a string that `get_args` cannot inspect, so a raw check would falsely reject the escape hatch in that form. `typing.get_type_hints(cls, include_extras=True)` was chosen — **since superseded outright by commit `2bcd7f96`, see above.** **M1**: rev3's pseudocode rejected any `id = <StrawberryField>` on a Relay-shaped type, banning the currently-working `@strawberry.field def id(self) -> relay.GlobalID: ...` pattern. Two contracts were considered — (a) ban all assigned `id` overrides, recourse being `@classmethod resolve_id`; (b) inspect the StrawberryField's return-type annotation and accept `relay.GlobalID` / `strawberry.ID`. **(a) was picked**: simpler, consistent with the annotation-side "use the supported escape hatch" framing. Landed as a `Changed` CHANGELOG entry rather than `Added` because it is a small intentional behavior change. **M2**: `has_id_annotation = id_annotation is not None` fails to detect `id: None`; changed to the key-presence check `"id" in cls.__annotations__`. **L1**: test-count arithmetic ("nine" against ten listed) corrected.
- **Revision 5** (post-rev4 review) — **M1**: rev4's fail-soft path returned `True` for *any* unresolved forward reference, so a typo like `id: "SomeMissingType"` would pass the guard and fall through to the Strawberry-side `ValueError` the guard exists to replace. Narrowed to accept only strings syntactically containing `"NodeID["`. **L1**: the Decision 7 heading and its six anchor references still carried a rev3-era suffix after rev4 substantially expanded the contract; renamed to the rev-neutral form. **L2**: the coverage and placement language ignored the rev4 M2 allowance for the `ArrayField` test's placement.
- **Revision 6** (post-rev5 review) — **H1**: rev5's fail-soft falsely rejected a directly-resolved `id: relay.NodeID[int]` whenever an unrelated annotation on the same class failed to resolve, because `typing.get_type_hints` evaluates every annotation on the class and walks the MRO. The realistic trigger is `id: relay.NodeID[int]` alongside `items: list["AdminItemType"]`. Reproduced locally against the on-disk `strawberry.relay`. Fixed by falling back to `_has_node_id_marker(raw)` on the not-a-string branch. **M1**: rev4's blanket assigned-`id` ban removed the only path for attaching `description` / `deprecation_reason` / `directives` to the Relay-supplied `id`. Two options: (a) acknowledge the loss and document a sibling-field workaround; (b) loosen the ban to allow metadata-only assignments by inspecting the StrawberryField's `base_resolver` and `type_annotation`. **(a) was picked** — smaller-touch, keeps the guard simple, and field-level metadata on the Relay `id` is a rare use case. **M2**: `if has_id_annotation and _id_annotation_is_relay_node_id(cls):` carried a dead conjunction (the assigned branch has already raised by that point, so `has_id_annotation` must be True). **M3**: rev4 M2's rationale claimed `cls.__annotations__["id"]` is "literally `None`" for `id: None`; Python evaluates it to `<class 'NoneType'>`. The key-presence fix was right; the reasoning was wrong. **L1**: the inheritance corner was named in the edge cases but not pinned by a test. **L2**: Decision 7a's cross-type cache behavior change was flagged but only the single-type case was pinned; a dedicated cross-type test was added. **L3**: line-delta estimates were stale, and every "Worker 1 picks during planning" recommendation was promoted to a default.
- **Revision 7** (post-rev6 review) — **H1**: two problems in the fail-soft accept path. The `"NodeID[" in raw` substring check accepted prefixed lookalikes (`id: "NotNodeID[int]"`, `id: "MyNodeID[int]"`); and the contract framing conflated the resolved-string and fail-soft sub-cases, because the fail-soft path suppresses only the package's own error while Strawberry's downstream resolution still runs. Fixed by tightening to the token-shaped regex `(?:^|\.)NodeID\[`, splitting the stringified-NodeID accept test into a resolved-end-to-end variant and an unresolved-guard-only variant, and adding a typo-lookalike reject test. **M1**: rev6's inheritance test asserted a Strawberry `ValueError` that does not actually fire — pk-suppression strips the synthesized `id` and the post-merge reassignment leaves the child with no `id` key at all, so Strawberry applies the Relay-supplied `id: GlobalID!` and `resolve_id_attr()` falls back to `"pk"`. The test contract was inverted to assert schema construction succeeds. **M2**: every sibling-field workaround example used `display_id: ID = strawberry.field(description="…")`, which attaches metadata but defines no value source and fails at query time; rewritten to the resolver-backed form. **L1**: the choice-enum edge-case bullet named the single-type test as the pin for cross-type behavior.
- **Revision 8** (post-rev7 review) — **H1**: the ten Relay tests only exercised the `Meta.interfaces` declaration shape, so an implementation wiring only the `interfaces` half of the guard predicate would pass every test while letting `class CategoryNode(DjangoType, relay.Node): id: int` fall through. A direct-inheritance reject test was added. **M1**: the pseudocode was mechanically broken and semantically under-specified — the module-scope regex was followed by a function-body block dangling at module scope where `hints` is not in scope, and the marker-detection prose pointed at a non-existent "direct `relay.NodeID[T]`" `get_origin` branch (in the installed Strawberry, `relay.NodeID[T]` **is** `typing.Annotated[T, NodeIDPrivate()]`, so both forms collapse to one detection key). Restructured, and `_has_node_id_marker` pinned as the single check. **M2**: the unresolved-string test recipe left the load-bearing mechanism to "Worker 1 picks" — that `typing.get_type_hints` resolves string annotations through `sys.modules[cls.__module__].__dict__`, so the test must set `cls.__module__` to a synthetic module with no `relay` symbol. The `TYPE_CHECKING` option was dropped because it cannot produce that condition. Without the recipe the test would have run in the real test module where `relay` IS imported, exercised the resolved-string path, and false-passed while pinning nothing. **L1**: Decision 7a's closing line said "three" bypass tests where every other site said four. **L2**: the cross-type cache test's placement was hedged across three sites; mandated to `tests/types/test_definition_order.py`.
- **Revision 9** (post-rev8 TODO-anchoring pass) — **L1**: the unresolved-string recipe cleaned up `sys.modules` but not the package registry, leaving a stale synthetic type registered against `Category` that could poison the cross-type cache test; `registry.clear()` was added to the same `try/finally`. **L2**: the `_FakeUnsupportedField(models.Field)` fixture was referenced as though it existed; it did not, so the recipe was rewritten as an explicit fixture-creation step.
- **Revision 10** (post-rev9 final review) — **M1**: the Test strategy's Relay list said "Eleven" and enumerated ten; the rev8 direct-inheritance test was present in four other sections but missed here. **M2**: rev9 L1's `registry.clear()` addition landed in the spec but not in the matching in-tree TODO anchor, so a builder reading the TODO as ground truth would have written the test without it. **L1**: allowing `_FakeUnsupportedField` in either test file would have broken the "18 of 19 tests land in `test_definition_order.py`" count and the "single exception" rule; mandated to the override-contract host. **L2**: the expanded TODO pseudo-code blocks tripped 38 `ERA001` failures under `uv run ruff check`. Three options were weighed — per-line `# noqa: ERA001` on 38 lines, accepting the temporary failure, or a scoped `[tool.ruff.lint.per-file-ignores]` entry in `pyproject.toml` naming `spec-015` Slice 1 as the reason. **The per-file-ignore was picked**, removed atomically by the Slice 1 commit that replaced the TODO bodies with real code. Confirmed removed: `pyproject.toml` carries no ERA001 ignore for any package path.
- **Revision 11** (post-build maintainer-feedback pass) — **M1**: rev8 M1's pseudocode wrapped the `hints.get("id")` lookup in an `if id_hint is None: return False` guard that was unreachable under the sole call site's precondition and redundant given `_has_node_id_marker(None)` already returns False safely; the uncovered line blocked the 100% coverage gate, so the guard was dropped and the call delegated directly. **Superseded outright** — see "The `relay.NodeID` detection mechanism was rewritten after the card shipped" above; the `hints` path this fix edited no longer exists. The same feedback flagged a Low nit about `registry.clear()` placement inside one test, deliberately left out of the spec as test-file-local.

### `## Current state`

The `## Current state` section stays in the spec as the pre-card baseline the Decisions are read against, but its `_consumer_assigned_fields(cls.__dict__, fields)` call sample was a true description of the code at authoring time and is false at `HEAD` (the signature now takes `cls`). Corrected in place rather than moved: a builder reading it needs the current shape, and the historical shape is recorded here.

### [Decision 1 — Annotation-only scalar override collection][spec-019-d1]

**Rejected: a single walk-and-bucket loop.** One `for` loop with an `if`/`else` inside would compress the two comprehensions into one construct, but it loses the visual symmetry with the existing relation collection one line above and makes the two override paths look like they do different things. They do not — they are the same logic with a polarity flip.

**Rejected: `field.is_relation is False`.** Django's `Field.is_relation` is documented as a bool but is sometimes accessed before model loading completes; the `not` form is bool-coercion-safe where the explicit comparison is not, and the existing `_build_annotations` code already uses bare `if field.is_relation:`.

**Claim the decision may no longer make.** Its post-Slice-1 sample shows the comprehension filtering only on `field.is_relation` (or its negation) and `field.name in consumer_annotations`. At `HEAD` both comprehensions carry a third clause, `and field.name not in auto_annotated_fields`, added by the later `auto`-typed-annotations card. The spec's sample has been corrected to match; the two-comprehension shape and the polarity-flip reasoning are unaffected.

### [Decision 2 — `consumer_authored_fields` union shape][spec-019-d2]

**Rejected: passing the four sets individually to `_build_annotations`.** The function only needs the union — it does not distinguish the four corners. Four parameters would force it to recompute the union or switch on provenance, neither of which it needs.

**Claim the decision may no longer make.** It stated `consumer_authored_fields` is "the only short-circuit input to `_build_annotations`", which was true when written and is now false in the stronger direction: the union is *also* consumed by `_validate_nullability_override_targets`, `_validate_filesystem_path_targets`, and `_validate_relation_shape_targets`, all added by later `0.0.9` / `0.0.14` cards. The exclusivity claim rotted; the design choice it justified was vindicated three times over. The spec's sentence is reworded to state the single-union shape without the exclusivity.

### [Decision 3 — `DjangoTypeDefinition.consumer_annotated_scalar_fields` field][spec-019-d3]

The grouped-by-style field order (annotated-relation, annotated-scalar, assigned-relation, assigned-scalar) was the rev2 L1 resolution of a contradiction between Decision 3's sample and Slice 1's insertion-point instruction, which had disagreed since rev1. The cosmetic re-order of the two existing `consumer_assigned_*` lines landed in the same commit as the new field.

### [Decision 5 — Test placement and the skipped test's fate][spec-019-d5]

**Rejected: unskip and keep `test_consumer_annotation_overrides_synthesized` as a smoke-test sibling.** It adds no coverage the Slice 1 cluster does not already have, and a one-line smoke test sitting alone in `tests/types/test_base.py` invites future drift between two locations for one contract. Rev6 L3 promoted the delete recommendation to the default, and the build took it.

### [Decision 6 — Why `_consumer_assigned_fields` stays the way it is][spec-019-d6]

**Claim the decision may no longer make.** Its prose described the helper as taking and walking `cls.__dict__`. At `HEAD` the signature is `_consumer_assigned_fields(cls: type, fields: tuple[Any, ...])` and the `cls.__dict__` read moved inside. The responsibility split the decision exists to state — assignments from `cls.__dict__`, annotations from `cls.__annotations__`, two independent input channels — is unchanged.

### [Decision 7 — Relay `id` override collision][spec-019-d7]

**Rejected placements** (rev2/rev3 deliberation; the conclusion stays in the spec because it changes where a builder puts the code):

1. **In `_validate_meta`** — too early. It runs over the `Meta` class only and has access to neither `consumer_annotations` nor `cls.__dict__`; threading the check through would widen its signature for a single-purpose check.
2. **In `_build_annotations`** — too late and wrong-layered. Its job is annotation synthesis, not configuration validation; detecting the collision there would entangle consumer override, Relay suppression, and conflict detection inside one per-field loop.

**Rejected: a finalize-time `cls.resolve_id_attr()` probe** (rev4 H1). It cannot satisfy the class-creation-time raise contract the reject test and the CHANGELOG both assert.

**Rejected: raw `typing.get_args(cls.__annotations__["id"])`** (rev4 H1). Under PEP 563 or an explicit string annotation the value is the string `"relay.NodeID[int]"`; `get_args` on a string returns `()` and the marker check fails, so the guard would reject the documented escape hatch in stringified form. The replacement chosen at the time was `typing.get_type_hints(cls, include_extras=True)`, whose `include_extras=True` preserves the `Annotated[T, NodeIDPrivate]` marker through resolution.

**The `get_type_hints` mechanism is itself retired.** Commit `2bcd7f96` replaced it with a direct `cls.__annotations__["id"]` read dispatching on `isinstance(raw, str)`; the reasoning is under "The `relay.NodeID` detection mechanism was rewritten after the card shipped" above. The rejection of raw `get_args` still holds in the current code — the string branch exists precisely because a string cannot be introspected as a type — but it is now handled by an explicit `isinstance` arm rather than by an exception path.

**Rejected: banning `id` by model pk name rather than by GraphQL field name** (rev2's predicate, narrowed by rev3 H1). Two false-positive classes it produced:

1. `id: relay.NodeID[int]` — the advertised escape hatch. `id` is a model pk field, so a `NodeID[int]` annotation lands in `consumer_annotated_scalar_fields` through the same collection path, and a pk-keyed guard fires against the exact pattern its own error message recommends.
2. Non-`id` primary-key overrides. On a model with `code = models.CharField(primary_key=True)`, a consumer `code: str` override produces `id: ID!` (from Relay) and `code: String!` (from the consumer) — no `Node.id` collision at all. The existing `tests/types/test_relay_interfaces.py::test_composite_pk_with_explicit_node_id_annotation_is_accepted` confirms the framework's broader contract that `relay.NodeID` annotations land on any attribute, not just `"id"`.

**Rejected: inspecting the assigned StrawberryField's return-type annotation to allow `relay.GlobalID` / `strawberry.ID` assignments** (rev4 M1, option b). Rejected for a uniform ban: simpler guard, consistent with the annotation-side "use the supported escape hatch" framing, and the error message can name `resolve_id` as the alternative. The cost is real and was accepted with eyes open — see the next entry.

**Rejected: loosening the ban for metadata-only `id = strawberry.field(...)` assignments** (rev6 M1, option b). The ban removes the only route for attaching `description` / `deprecation_reason` / `directives` to the Relay-supplied `id`, and neither named alternative (`@classmethod resolve_id`, `id: relay.NodeID[<pk_type>]`) attaches field metadata. Option (a) — acknowledge the loss and document a resolver-backed sibling field — was picked as the smaller-touch answer for a rare use case. The workaround example itself was wrong through rev6: `display_id: ID = strawberry.field(description="…")` attaches metadata but defines no value source, so Strawberry's default resolver looks up `display_id` as an attribute on the returned model instance and fails at query time. Rev7 M2 corrected every occurrence to the resolver-backed decorator form.

**Retired vocabulary.** The "two fail-soft sub-cases", the `NameError` / `AttributeError` framing, the `try` / `except` structure, the `hints` mapping, and rev11's `hints.get("id")` delegation are all gone from the code and now from the spec. What survives of that deliberation is the *behavior* it argued toward: a NodeID-shaped string is accepted by shape alone (with the token-boundary regex rejecting `"NotNodeID[int]"` and `"MyNodeID[int]"`, the rev7 H1 tightening of rev6's plain substring test), a resolved `Annotated[T, NodeIDPrivate]` is accepted by marker, and an unrelated annotation on the class cannot influence either verdict.

**Retired claim: the guard's control-flow shape.** The pseudocode's outer `if has_id_annotation or has_id_assignment:` wrapper and its `if _id_annotation_is_relay_node_id(cls): pass  # Accept.` / `else: raise` shape do not exist at `HEAD`; the annotation reject is written directly as `if has_id_annotation and not _id_annotation_is_relay_node_id(cls):`. Rev6 M2's dead-conjunction argument is moot in that form.

**Retired claim: the Relay-shape predicate is computed inline at the guard.** At `HEAD` it is `django_strawberry_framework/types/base.py::_is_relay_shaped`, a named module-scope helper and the single source of truth for the guard, for `_build_annotations`'s `suppress_pk_annotation`, and (since `74d4a5b7`) for the connection-validation path. The predicate body is byte-equivalent to the spec's inline disjunction.

### [Decision 7a — Converter validation bypass][spec-019-d7a]

**Why the bypass is the correct contract** (moved; the enumerated consequences stay in the spec because they are what the tests pin):

1. **Consistency with the relation override path.** Annotation-only relation overrides already bypass `convert_relation` entirely — the same `if field.name in consumer_authored_fields: continue` short-circuit fires before any relation-side validation. The scalar contract should match rather than invent an asymmetry.
2. **Override is escape, not augmentation.** The point of an override is to escape the package's auto-conversion. If `convert_scalar`'s validations still fired on overridden fields, an unsupported scalar would keep raising even when the consumer supplied a perfectly valid manual annotation — defeating the purpose.

The heading lost its `(H2 fix)` suffix in this pass; the anchor above is the current one.

### `## Implementation plan` — the slice table's estimates

The table's `Approx. line delta` column carried per-revision estimate churn (`+30/-1` → `+55/-1` → `+75/-1` → `+90/-1` → `+95/-1` → `+185/-1` → `+225/-1`, with a "Total expected delta" paragraph tracking `~80` → `~140` → `~290` → `~305`). Every figure was a pre-build estimate for work that has shipped; none of them describes the diff that landed. The estimates are moved here as a record and dropped from the spec, which keeps the table's Files / Tests / Notes columns.

### `## Slice checklist` — Slice 4's Prior-`0.0.6`-card note

The note read: "`0.0.6` carries three cards (`spec-013-deferred_scalars`, `spec-014-meta_primary`, this card)." Both filenames are pre-2026-07-30-renumber artifacts. Today `spec-013` is the archived real-M2M stub and `spec-014` is the testing-shift spec; the files intended are `spec-017-deferred_scalars-0_0_6.md` and `spec-018-meta_primary-0_0_6.md`. The `0.0.6` line actually carries **four** cards, `DONE-016` through `DONE-019`.

Rewritten in the spec to post-renumber **card ids** rather than filenames, on the precedent of the spec-018 residual cycle, which reconciled its own copy of the same note the same way. `KANBAN.md`'s `[spec-011]` renumber-sweep bullet tracks this cluster and already records spec-018's removal from it; spec-019's occurrence leaves the population with this edit (`grep -c spec-013` on this spec goes 1 → 0), which the sweep card should re-derive rather than carry forward from an older reading.

### `## Slice checklist` — Slice 5's self-referential KANBAN instruction

The instruction read "move `DONE-019-0.0.6` → `DONE-019-0.0.6`", and the matching Definition-of-done item read "`KANBAN.md` shows `DONE-019-0.0.6` …; `DONE-019-0.0.6` is no longer present." The renumber rewrote both halves of an original `WIP-…-015` → `DONE-015` instruction into the same string, producing an instruction to move a card to itself and a done-condition that is self-contradictory. Same defect class the spec-017 and spec-018 residual cycles each found in their own closeout slices. Both sites are rewritten in the spec to state the landed end state.

### `## Slice checklist` — Slice 5's archive bullet and CHANGELOG target

Two framings the release falsified:

- The archive bullet said the spec stays at its working location and archival is "the maintainer's call". The spec is archived at `docs/SPECS/`, its terms CSV at `docs/SPECS/appx/`, and its link-definition block is already re-relativized (`../../AGENTS.md`, `../GLOSSARY.md`) — a later spec author's `docs/SPECS/NEXT.md` Step 8 sweep did the move.
- Slice 5 and the Definition of done both said the five CHANGELOG entries land under `[Unreleased]`. They sit under `## [0.0.6] - 2026-05-19`, which is expected after the release cut; the spec was simply the last carrier of the pre-release framing.

### `DONE-019-0.0.6` — the verbatim KANBAN body

The body is reproduced in the spec's Slice 5 as the drop-in text. Its Relay paragraph described the `typing.get_type_hints` mechanism and both fail-soft sub-cases at length; the spec's copy is rewritten to the landed mechanism so a reader diffing the spec against the code is not told two different stories.

**The live `KANBAN.md` card carries no mechanism description, so nothing there was falsified.** The card body is DB-backed (`scripts/build_kanban_md.py` renders `KANBAN.md` from the fakeshop kanban app's DB), and the DB stores only the **first line** of each of this drop-in's bullets: the live Relay item is the single line "**`relay.Node` `id` collision rejected at type-creation time.** A consumer", and every sentence describing detection lives on continuation lines the import never carried. Measured, not inferred: `get_type_hints` and `fail-soft` each occur **0** times in `KANBAN.md`, **0** times in `KANBAN.html`, and **0** times in any text column of any table in `examples/fakeshop/db.sqlite3`. There is therefore no KANBAN-side deferred item for this card, and no DB edit or regenerate is owed.

### `CHANGELOG.md` — the `[0.0.6]` Relay-guard `Added` entry

The shipped entry asserted "Detection uses `typing.get_type_hints(cls, include_extras=True)` with a fail-soft fallback for unresolved forward references that distinguishes …" — a false claim about shipped code in a shipped doc, false since `2bcd7f96` landed two days after the release. Corrected in place to the landed mechanism, minimally: one sentence, no restructuring of the entry, no other bullet touched, and the `[015-consumer_override_semantics_scalar_fields-0.0.6]` tracking label left alone (it belongs to the renumber-sweep cluster `KANBAN.md` tracks, and half-fixing a cluster leaves it divergently rather than uniformly wrong).

The permission for the edit is this spec's own Slice 5, which grants CHANGELOG access for this card's entries explicitly, overriding [`AGENTS.md`][agents] rule 21's default prohibition.

`docs/GLOSSARY.md`'s `Scalar field override semantics` entry was read end to end for the same defect and names no detection mechanism — it states the contract (`id: relay.NodeID[...]` accepted in direct, PEP 563 / stringified, and mixed forms) without saying how detection works. Correct as written; no edit.

### `## Test strategy` — the two mechanism-named tests

`test_consumer_id_unresolved_nodeid_shaped_string_on_relay_node_type_passes_guard_only` and `test_consumer_id_resolved_relay_nodeid_with_unresolved_sibling_annotation_is_accepted` are named for the retired fail-soft sub-cases. The spec's descriptions of both are rewritten to the landed mechanism, and the spec now records the landed test names and the `spec015_*` synthetic identifiers as **the landed spelling**, not as a recipe to follow. Renaming either the tests or the identifiers is a code edit with no correctness payoff, and is routed to the deferred-work catalog instead.

## Reconciliation record — what the spec now says, and why

Every edit this pass made to the spec, beyond the rationale move itself, was enumerated with its finding number in the round artifact, under `### Spec changes made (Worker 1 only)`: 25 numbered entries. That artifact was deleted at closeout, so the full enumeration now lives only in commit `435e190e`, which added it and the spec edits together. The short form, which is self-sufficient:

| Spec surface | Was | Is |
|---|---|---|
| `Status:` line | `draft (revision 11, post-build maintainer-feedback pass)` | shipped state |
| Goals bullet 5, Decision 7, Slice 1 helper checkbox, Edge cases Relay bullet, Test strategy coverage paragraph, KANBAN body, CHANGELOG body | `typing.get_type_hints` + two fail-soft sub-cases | direct `cls.__annotations__["id"]` read, `isinstance(raw, str)` dispatch |
| Decision 7 + Slice 1 checkbox | inline Relay-shape disjunction | `_is_relay_shaped(cls, interfaces)` |
| Decision 1 sample + Slice 1 checkbox | two-clause comprehensions | three-clause, with the `auto_annotated_fields` exclusion |
| `## Current state` + Decision 6 | `_consumer_assigned_fields(cls.__dict__, fields)` | `_consumer_assigned_fields(cls, fields)` |
| Decision 2 | "the only short-circuit input to `_build_annotations`" | one union, read by `_build_annotations` and three later validators |
| Slice 5 + Definition of done | `DONE-019-0.0.6` → `DONE-019-0.0.6` | the landed Done-section end state |
| Slice 5 archive bullet | "stays at its working location" | archived at `docs/SPECS/` |
| Slice 5 + Definition of done | CHANGELOG `[Unreleased]` | `## [0.0.6] - 2026-05-19` |
| Slice 4 Prior-`0.0.6`-card note | three cards, pre-renumber filenames | four cards, post-renumber card ids |

### What this cycle deliberately did not fix

- **The `spec015_*` identifiers in `tests/types/test_definition_order.py`.** Three `app_label`s and one stub-module prefix. Test-local synthetic strings with no cross-file consumer; renaming them is a code edit with no correctness payoff and a real collision risk against a concurrent session's dirty copy of that file. The spec records the landed spelling.
- **The retired fail-soft vocabulary in `tests/types/test_definition_order.py` — four occurrences across three tests.** Two test names, one inline comment, and one docstring; see "The `relay.NodeID` detection mechanism was rewritten after the card shipped" above for the enumeration. Same file, same reasoning as the `spec015_*` identifiers. All three tests pin current, correct contracts under retired vocabulary.

**Not deferred, because it does not exist:** `KANBAN.md`'s live `DONE-019-0.0.6` body. It was expected to carry the retired-mechanism paragraph and does not — the rendered card, the HTML board, and the kanban DB all carry zero occurrences of `get_type_hints` and `fail-soft`, because the DB holds only the first line of each drop-in bullet. Recorded here so a later reader does not re-open a KANBAN item that has nothing behind it.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../../AGENTS.md

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-019-d1]: ../spec-019-consumer_overrides_scalar-0_0_6.md#decision-1--annotation-only-scalar-override-collection
[spec-019-d2]: ../spec-019-consumer_overrides_scalar-0_0_6.md#decision-2--consumer_authored_fields-union-shape
[spec-019-d3]: ../spec-019-consumer_overrides_scalar-0_0_6.md#decision-3--djangotypedefinitionconsumer_annotated_scalar_fields-field
[spec-019-d5]: ../spec-019-consumer_overrides_scalar-0_0_6.md#decision-5--test-placement-and-the-skipped-tests-fate
[spec-019-d6]: ../spec-019-consumer_overrides_scalar-0_0_6.md#decision-6--why-_consumer_assigned_fields-stays-the-way-it-is
[spec-019-d7]: ../spec-019-consumer_overrides_scalar-0_0_6.md#decision-7--relay-id-override-collision
[spec-019-d7a]: ../spec-019-consumer_overrides_scalar-0_0_6.md#decision-7a--converter-validation-bypass
[spec-019]: ../spec-019-consumer_overrides_scalar-0_0_6.md

<!-- docs/builder/ -->
[build]: ../../builder/BUILD.md
[worker-1]: ../../builder/worker-1.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
