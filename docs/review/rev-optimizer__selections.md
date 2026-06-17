# Review: `django_strawberry_framework/optimizer/selections.py`

Status: verified

## DRY analysis

- None — this module IS the DRY consolidation point its own module docstring (`selections.py:16-19`) and the `walker.py:48-53` / `extension.py:77-83` 0.0.9-DRY-pass comments describe. It single-sources the fragment-vs-field discriminator (`is_fragment`), the `@skip`/`@include` evaluation (`should_include`), the response-key rule (`response_key` / `response_keys`), the fragment-inlining primitive (`included_field_selections`), and the AST-side directive-variable / child-iteration / fragment-resolve helpers; walker, extension, and connection all consume them via `_`-aliases or direct import. The two adapters (AST vs converted) are intentionally explicit per the module docstring's quoted review note ("Keep the adapters explicit, but share the recursion and directive/fragment policies"), so folding them into one polymorphic walker is the anti-goal the file was created to avoid. No additional consolidation candidate exists.

## High:

None.

## Medium:

### Stale TODO anchor: `spec-035 Slice 3` was DEFERRED (no runtime code) and moved to a different card

The only spec-035 change to this file (commit `4241d37d`, the +6-line block at `selections.py #"TODO(spec-035 Slice 3)"`, immediately above `included_field_selections`) instructs a future maintainer to "add a tri-state fragment classifier to this converted selection inliner ... per spec-035 Slice 3". That obligation no longer points at live work: spec-035 is **COMPLETE** (`DONE-035-0.0.10`) and its **Slice 3 (G3 — fragment type-condition narrowing) is explicitly DEFERRED with no runtime code shipped**, moved to the abstract-return optimizer entry card (BACKLOG `polymorphic_interface_connections`).

Evidence:

- `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` Status line: "COMPLETE (card `DONE-035-0.0.10`) — G1 shipped, G2 shipped, Slice 4 doc wrap landed; **G3 deferred**". Decision 6 header block: "**Status: DEFERRED — carry-forward requirements, no runtime code in spec-035.** ... retained verbatim as the design contract for the follow-up *abstract-return optimizer entry* card."
- `KANBAN.md:1463-1465` mark the G3 work "**[DEFERRED - G3 ships no runtime code in spec-035; moved to the abstract-return optimizer entry card (BACKLOG `polymorphic_interface_connections`); see spec-035 Decision 6/7, Revision 3-4.]**".
- Timeline: the TODO was added 2026-06-16 11:59 (`4241d37d`); the spec's Revision 3 deferral landed the same authoring cycle and the spec was subsequently archived to `docs/SPECS/`. The comment is stale relative to its own spec's final disposition.

Why it matters: AGENTS.md #26 requires a staged-slice source-site TODO to "name the active design doc and slice". This TODO names a slice that its own spec retracted, so a future maintainer could implement the classifier "under spec-035 Slice 3" when the active owner is the (unscheduled) abstract-return optimizer entry card — and, critically, the spec records that this narrowing **has no reachable production trigger today** and must not ship until that card first builds the abstract-return production-entry contract (`registry.model_for_type` returns `None` for the interface/union origin, so `extension.py::_optimize` passes the queryset through before the walker runs). Shipping the classifier under the stale anchor would be synthetic-only code the spec deliberately rejected.

Recommended change: re-anchor the TODO to the active owner. Replace the `spec-035 Slice 3` reference with the abstract-return optimizer entry card / `BACKLOG.md` `polymorphic_interface_connections`, and add the one-line reachability caveat (an abstract root field never reaches the walker today, so the classifier ships nothing until that card lands the production entry). No `NotImplementedError` pairing is warranted (AGENTS.md #26: pair with `NotImplementedError` only when "the call path must fail loudly") — the default INLINE-all path is correct and complete for every currently-reachable shape; the classifier is purely additive future hardening, so the call path must NOT fail. Keep the design pseudocode (tri-state INLINE / SKIP / RECURSE_FRAGMENTS_ONLY) since it matches Decision 6/7's carry-forward design.

```django_strawberry_framework/optimizer/selections.py:315:320
# TODO(spec-035 Slice 3): add a tri-state fragment classifier to this converted
# selection inliner, but keep the default path byte-for-byte unconditional.
# Pseudocode: no classifier means INLINE-all for extension cache-key and
# connection extraction callers; a walker-supplied classifier returns INLINE,
# SKIP, or RECURSE_FRAGMENTS_ONLY. The recursion mode drops direct fields for an
# unknown composite/union condition while still re-checking nested fragments.
```

## Low:

### `ast_to_converted_selections` FragmentSpread reads `type_condition.name.value` unguarded while the InlineFragment branch guards `None`

`selections.py::ast_to_converted_selections` (the `_convert` inner) builds the inline-fragment shell defensively — `type_condition=(condition.name.value if condition is not None else None)` (`selections.py #"condition.name.value if condition is not None"`) — but the `FragmentSpreadNode` branch dereferences `fragment.type_condition.name.value` (`selections.py #"type_condition=fragment.type_condition.name.value"`) with no `None` guard. This is correct today: per the GraphQL spec a *named* fragment definition always carries a type condition (anonymous conditions are only possible on *inline* fragments), so `fragment.type_condition` is never `None` for a `FragmentDefinitionNode`, and graphql-core validation would reject the operation before the optimizer sees a malformed one. The asymmetry is therefore intentional and safe, not a bug. Defer with trigger: if a future change ever routes a synthesized or non-validated fragment-definition shape through this path (e.g. a test double or a hand-built definition lacking `type_condition`), add the same `is not None` guard the inline branch already has. No action now.

### `with_runtime_prefix` fragment branch omits `arguments`; field branch includes it

`selections.py::with_runtime_prefix` builds the fragment clone without an `arguments` attribute (`selections.py #"type_condition=selection.type_condition"` block) while the field clone sets `arguments=getattr(selection, "arguments", None) or {}`. This is correct — fragments have no arguments, and every downstream walker read of `arguments` is `getattr(sel, "arguments", None) or {}` (`walker.py:1098`, `walker.py:1105`), so a missing attribute degrades to `{}` rather than raising. Recorded as a no-action Low for the audit trail: the absence is deliberate (a fragment-shell `arguments` would be meaningless), and the consumer's defensive `getattr` makes it safe. No action.

## What looks solid

### DRY recap

- **Existing patterns reused.** The module is the canonical home for the selection-traversal primitives consolidated in the 0.0.9 DRY pass (`docs/feedback.md` Major 2): `is_fragment` is the single fragment-vs-field discriminator (`selections.py:273-284`), reused by the walker, the connection `edges { node }` unwrap, and `direct_child_selected`; `should_include` (`selections.py:287-300`) is the single `@skip`/`@include` evaluator shared by `included_field_selections`, `named_children`, and `direct_child_selected`; `directive_variable_names` (`selections.py:242-263`) is the single AST cache-key directive-variable extractor. Consumers import via `_`-aliases (`walker.py:54-60`, `extension.py:85` onward) so existing bodies and tests stay unchanged.
- **Duplication risk in the current file.** The two adapters (AST nodes vs converted selections) deliberately repeat the "iterate children / descend fragments / honor directives" shape rather than sharing one polymorphic walker — the module docstring quotes the originating review decision ("Keep the adapters explicit, but share the recursion and directive/fragment policies so the contracts cannot drift"). This is intentional sibling design: the AST adapter operates on graphql-core nodes for the cache-key/fragment-reachability walk; the converted adapter operates on Strawberry selections for plan-building. Correct as-is.

### Other positives

- **Cycle-safe by construction.** The module imports only `__future__`, `types.SimpleNamespace`, `typing.Any`, and graphql-core AST node types at load time; the single strawberry import (`convert_arguments`/`convert_directives`/`SelectedField`/etc., `selections.py:101-107`) is function-local inside `ast_to_converted_selections`. It imports neither `walker` nor `extension`, removing the prior reverse dependency the docstring describes. No first-party import, no import-time side effect.
- **No ORM surface.** The shadow overview reports zero Django/ORM markers — appropriate; this is pure selection-tree traversal with no queryset, `select_related`, `only`, or `_meta` access. Nothing to audit on the ORM-correctness axis.
- **Reflective access is uniformly defensive.** All 25 `getattr` sites use a `None`/`()`/`[]` default and the `... or default` idiom, so absent attributes (fragment shells lacking `arguments`/`alias`, `SimpleNamespace` clones, `FragmentSpreadNode` lacking `selection_set`) degrade gracefully rather than raising. `isinstance` gates (`InlineFragmentNode` / `FragmentSpreadNode` / `DirectiveNode` / `VariableNode`) are exact node-type checks; `is_fragment`'s `hasattr(..., "type_condition")` duck-type is the documented single discriminator.
- **`ast_to_converted_selections` is a verified faithful mirror.** The docstring pins the load-bearing invariant: for every non-anonymous query the output is byte-identical to Strawberry's `convert_selections` (it builds from Strawberry's own `SelectedField`/`FragmentSpread`/`InlineFragment` dataclasses so `isinstance`-based Strawberry consumers keep working), with the sole deviation being `type_condition=None` for a spec-valid anonymous inline fragment that Strawberry's own converter crashes on. Confirmed against Strawberry's source: `convert_arguments`/`convert_directives` take the raw `GraphQLResolveInfo`, and `prime_selected_fields` correctly passes `raw_info` (not the Strawberry `Info` wrapper) to them.
- **`prime_selected_fields` is honestly documented about its coupling.** The docstring is explicit that it couples to two Strawberry internals (`Info._raw_info`, the `functools.cached_property` dict-slot) and that a future Strawberry rename SILENTLY no-ops rather than failing loudly — and names the live regression net (`test_anonymous_inline_fragment_*` in the fakeshop `test_query` suite). Idempotent: `if not field_nodes or "selected_fields" in info.__dict__: return` guards both the no-field-nodes and already-populated cases.
- **`direct_child_selected` correctly gates on `should_include` AND recurses through fragments only.** The "recurse through fragments only, never into a regular field's sub-selections" contract is the load-bearing rule that keeps an outer connection's `totalCount` predicate from tripping on a deeply nested node-level `totalCount`. Both the fragment-descent and the `@skip`/`@include` gate are pinned: `test_direct_child_selected_ignores_nested_field_selections`, `test_direct_child_selected_honors_skip_include` (covers direct-field-skip, include-false, skip-true-fragment-shell-prunes-subtree, and the keep cases), and `test_direct_child_selected_matches_direct_and_fragment_wrapped`.
- **Test discipline.** `tests/optimizer/test_selections.py` carries a focused test for every public symbol (`ast_child_selections` empty/children, `resolve_unvisited_fragment` resolve-once-then-dedup, `directive_variable_names` skip/include-only + non-directive-object defense, `is_fragment`, `should_include`, `response_key` alias preference, `response_keys` merged-marker fallback, `included_field_selections` inline+directive-filter, `named_children` fragment recursion, `node_children_with_runtime_prefix` clone-with-prefix, and the three `direct_child_selected` cases). Defensive branches (`directive_variable_names` non-directive guard) are explicitly pinned.

### Summary

`selections.py` is in excellent logical shape: the file is the single, cycle-safe home for the two selection-traversal adapters, every reflective access is defensive, the `ast_to_converted_selections` anonymous-inline-fragment mirror and `prime_selected_fields` priming are correct and honestly documented about their Strawberry coupling, and every public symbol has focused test coverage. The this-cycle HEAD diff is empty and the only spec-035 change was a +6-line TODO comment. That comment is the one real finding: a **Medium** stale-anchor defect — the `TODO(spec-035 Slice 3)` block names a slice its own spec explicitly **DEFERRED with no runtime code**, moved to the abstract-return optimizer entry card / BACKLOG `polymorphic_interface_connections`, so per AGENTS.md #26 it must be re-anchored to the active owner with the reachability caveat (and no `NotImplementedError`, since the default path is complete). Two no-action Lows record intentional, safe asymmetries (named-fragment `type_condition` deref, fragment-clone missing `arguments`). `Status: under-review` for the Worker 2 comment re-anchor.

---

## Fix report (Worker 2)

### Logic pass — no logic findings, no source edits

Worker 1 recorded High 0, Medium 1, Low 2 with **no logic findings**. The HEAD cycle diff for the target is empty (`git diff HEAD -- django_strawberry_framework/optimizer/selections.py` returns nothing). The single real finding (Medium) is a **stale TODO-anchor** comment defect and the two Lows are no-action audit-trail records; all three are comment/docstring-scope and per the cycle plan are deferred to the comment pass that runs **after** Worker 3 accepts logic.

This pass makes **zero source edits**.

### Files touched
- None. No source file edited this pass.

### Tests added or updated
- None. No behavior change.

### Carried to comment pass (no edit this pass)
- **Medium — stale TODO anchor** (`selections.py #"TODO(spec-035 Slice 3)"`, the +6-line block above `included_field_selections`): re-anchor from the DEFERRED `spec-035 Slice 3` to the active owner (abstract-return optimizer entry card / `BACKLOG.md` `polymorphic_interface_connections`), add the one-line reachability caveat (an abstract root field never reaches the walker today, so the classifier ships nothing until that card lands the production entry), keep the tri-state INLINE/SKIP/RECURSE_FRAGMENTS_ONLY pseudocode, and add NO `NotImplementedError` (default INLINE-all path is complete; the call path must NOT fail). Comment-only change.
- **Low 1 — no action**: `ast_to_converted_selections` FragmentSpread `type_condition.name.value` unguarded deref is correct (named fragment definitions always carry a type condition; graphql-core validation rejects malformed ops before the optimizer). Deferred with trigger only.
- **Low 2 — no action**: `with_runtime_prefix` fragment clone omitting `arguments` is correct (fragments have no arguments; every downstream read is defensive `getattr(sel, "arguments", None) or {}`). Recorded for audit trail only.

### Validation run
- `uv run ruff format .` — pass / no-changes (270 files left unchanged; the standing COM812-vs-formatter warning is pre-existing config noise, not a failure).
- `uv run ruff check --fix .` — pass / no-changes (All checks passed!).
- No focused tests run (no source change; logic pass per role file does not run pytest).

### Notes for Worker 3
- No shadow file used this pass (no fix implemented).
- No false-premise rejections — there were no logic findings to apply.
- `uv.lock` untouched by the ruff runs (`git diff HEAD -- uv.lock` empty).
- Out-of-scope dirty files in the working tree at dispatch (management/commands fixes, sibling rev-*.md artifacts, fakeshop library changes) are presumptively concurrent maintainer/other-worker work per AGENTS.md #33 — left untouched.

---

## Verification (Worker 3)

### Logic verification outcome

Logic-verify only (TODO text disposition deferred to the later comment-verify per worker-3.md). Independently re-read source + shadow (`docs/shadow/django_strawberry_framework__optimizer__selections.overview.md`); confirmed zero source edits (`git diff HEAD -- django_strawberry_framework/optimizer/selections.py` empty).

No missed logic High/Medium in the selection-tree parsing. Spot-checks against source:

- **spec-035 +6-line change is genuinely a comment, not runtime code.** Lines 315-320 are `#`-prefixed lines between `response_keys` (ends 312) and `included_field_selections` (starts 321) — no `NotImplementedError`, no statement, no behavior. Shadow corroborates: "executable marker lines: 0", TODO inventory at line 315 only. The change introduced zero behavior; logic is unaffected.
- **Fragment / inline-fragment handling consistent.** `_convert` (selections.py:112-142): InlineFragmentNode guards `condition is not None` before `type_condition`; the anonymous-`None` shell flows through `is_fragment`'s `type_condition` duck-type (selections.py:284) into the inliner. FragmentSpreadNode's unguarded `fragment.type_condition.name.value` (selections.py:126) is Low 1 — correct, not a defect: a named `FragmentDefinitionNode` always carries a type condition (anonymous conditions are inline-only per the GraphQL spec) and graphql-core validation rejects malformed ops before the optimizer runs.
- **Alias handling correct.** `response_key` (selections.py:305) prefers `alias` then `name`; `SelectedField` built with `alias=getattr(node.alias, "value", None)` (selections.py:137).
- **Cycle-safe.** `resolve_unvisited_fragment` (selections.py:230-238) returns `None` on not-a-spread / no-name / already-visited / undefined, mutates the shared `visited_fragments` only on success — shared set across recursive descents stops fragment cycles. `ast_child_selections` returns `()` for spread nodes (no `selection_set`), so per-child loops no-op.
- **`ast_to_converted_selections` mirror faithful.** Built from Strawberry's own `SelectedField` / `FragmentSpread` / `InlineFragment` dataclasses; recursion reimplemented at all depths; sole deviation is `type_condition=None` for spec-valid anonymous inline fragments — matches the docstring's load-bearing byte-identical-for-non-anonymous invariant.
- **Reflective access uniformly defensive.** All getattr sites use `None`/`[]`/`()` defaults with the `... or default` idiom. Low 2 (`with_runtime_prefix` fragment branch omits `arguments`, selections.py:367-375) is safe — every downstream read is defensive `getattr(sel, "arguments", None) or {}`.

Medium finding (stale `TODO(spec-035 Slice 3)` anchor) is a comment-scope defect correctly carried to the comment pass; it does not affect logic. Both Lows are intentional, safe asymmetries recorded no-action.

### DRY findings disposition

Worker 1 recorded "None — this module IS the DRY consolidation point" (one justified single). No DRY action this cycle; nothing to carry forward.

### Temp test verification

None. Logic pass with zero source edits; no behavior to pin. No temp tests created.

### Verification outcome

`logic accepted; awaiting comment pass` — sets top-level `Status: logic-accepted`. Checklist box NOT marked (interim sub-pass).

---

## Verification (Worker 3, comment pass)

### Diff scope — comment-only, no logic line

`git diff HEAD -- django_strawberry_framework/optimizer/selections.py` shows exactly one hunk: the -6/+12 TODO-comment block above `included_field_selections`. Every changed line is `#`-prefixed; the `def included_field_selections(...)` signature and body are untouched. No logic line touched. (a) holds.

### Active-owner confirmation (independent)

- **BACKLOG card exists and is the live owner.** `BACKLOG.md:1060` `### \`polymorphic_interface_connections\`` is a real, unscheduled card. `BACKLOG.md:1079` "Carries forward (spec-035 G3 deferral): this card is the scheduled home for the deferred G3 — fragment type-condition narrowing from spec-035 (Decisions 6–7) … G3 therefore ships *with* this card, never before it." `BACKLOG.md:1081` defines **R1 — abstract-return entry contract (the precondition)** verbatim — the exact reachability gate the new comment cites. The card is the genuine active owner.
- **spec-035 Slice 3 / G3 is genuinely DEFERRED and complete, so the old anchor was stale.** `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md:5` Status: "COMPLETE (card `DONE-035-0.0.10`) … G3 deferred." `:226` Decision 6 header: "Status: DEFERRED — carry-forward requirements, no runtime code in spec-035 … retained verbatim as the design contract for the follow-up *abstract-return optimizer entry* card (the BACKLOG `polymorphic_interface_connections` work)." Slice checklist `:57` "[deferred] Slice 3: G3 … moved to the abstract-return optimizer entry card; no runtime code in spec-035." No working-location copy remains (`ls docs/spec-035*` → no matches); archived to `docs/SPECS/`. The old `TODO(spec-035 Slice 3)` pointed at a slice its own spec retracted — confirmed stale.
- **KANBAN corroborates the move verbatim.** `KANBAN.md:1463-1465,1501` "[DEFERRED - G3 ships no runtime code in spec-035; moved to the abstract-return optimizer entry card (BACKLOG `polymorphic_interface_connections`); see spec-035 Decision 6/7, Revision 3-4.]".

### New comment accuracy — reachability caveat verified against source

The new block's load-bearing claim ("an abstract root field never reaches the walker today — `registry.model_for_type` returns `None` for the abstract origin, so `_optimize` passes the queryset through before this inliner runs … R1") is accurate against live source, not just against the spec prose:

- `registry.py:242` `def model_for_type(self, type_cls) -> type[models.Model] | None` — returns `None` for an unregistered (abstract) origin.
- `extension.py:625-626` `model = registry.model_for_type(origin)` / `if model is None:` inside `_resolve_model_from_return_type` (returns `None`).
- `extension.py:803-810` `_optimize`: `resolved = _resolve_model_from_return_type(info)` / `if resolved is None: … return result` — passes the queryset through **before** `apply_to`/the walker. Confirmed the passthrough precedes `self.apply_to(...)` at `:811`.

The caveat names R1 and `registry.model_for_type` correctly; no inaccuracy introduced.

### AGENTS.md #26 / #18 compliance

- #26: the re-anchored TODO names the active doc/card (`BACKLOG polymorphic_interface_connections — the abstract-return optimizer entry card`). No `NotImplementedError` is needed and none was added — the default INLINE-all path is complete and the call path must NOT fail (the abstract field never reaches the inliner today), so #26's "pair with `NotImplementedError` only when the call path must fail loudly" is correctly NOT triggered. The tri-state INLINE / SKIP / RECURSE_FRAGMENTS_ONLY pseudocode is retained, matching Decision 6/7's carry-forward design. (c) holds.
- #18 / ERA001: the block remains a proper TODO-anchored pseudocode comment (exempt); `uv run ruff check django_strawberry_framework/optimizer/selections.py` → "All checks passed!". No `noqa` needed. ERA001-safe. (d) holds.

The two Lows correctly received no comment edit (intentional, safe asymmetries per the artifact). No new inaccuracy in any comment.

### Verification outcome

`comments accepted; awaiting changelog disposition` — sets top-level `Status: comments-accepted`. Checklist box NOT marked (interim sub-pass).

---

## Comment/docstring pass

### Files touched
- `django_strawberry_framework/optimizer/selections.py #"TODO(BACKLOG polymorphic_interface_connections"` — re-anchored the single +6-line TODO block above `included_field_selections` from the DEFERRED `spec-035 Slice 3` to the active owner card. Comment-only; no logic line touched.

### Re-anchor (old vs new)

Old anchor (verbatim first line):
```
# TODO(spec-035 Slice 3): add a tri-state fragment classifier to this converted
```

New anchor (verbatim first two lines):
```
# TODO(BACKLOG polymorphic_interface_connections — the abstract-return optimizer
# entry card): add a tri-state fragment classifier to this converted selection
```

The new block keeps the tri-state INLINE / SKIP / RECURSE_FRAGMENTS_ONLY pseudocode unchanged and adds the one-line reachability caveat the artifact required: "an abstract (interface/union) root field never reaches the walker today — `registry.model_for_type` returns `None` for the abstract origin, so `_optimize` passes the queryset through before this inliner runs; the classifier therefore ships nothing until that card first builds the abstract-return production-entry contract (R1)." No `NotImplementedError` added — the default INLINE-all path is complete and the call path must NOT fail (AGENTS.md #26: pair with `NotImplementedError` only when the call path must fail loudly).

### Active-owner confirmation (per role-file: confirm before writing)
- spec-035 is COMPLETE and archived to `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` (Status line: "COMPLETE (card `DONE-035-0.0.10`) … G3 deferred"; Decision 6 header: "Status: DEFERRED — carry-forward requirement, no runtime code in spec-035"). No live `docs/spec-035*` working-location copy remains.
- Active owner is real and unscheduled in BACKLOG: `BACKLOG.md #"### \`polymorphic_interface_connections\`"` (the abstract-return optimizer entry card), with R1 (the abstract-return entry contract / precondition) defined there.
- `KANBAN.md` G3 lines confirm the move verbatim: "moved to the abstract-return optimizer entry card (BACKLOG `polymorphic_interface_connections`); see spec-035 Decision 6/7, Revision 3-4."
- Reachability caveat verified against spec-035 Decision 6 Revision 3: "registry.model_for_type(origin) returns None … so _optimize passes the queryset through before the walker runs."

### Per-finding dispositions
- Medium 1 (stale `TODO(spec-035 Slice 3)` anchor): re-anchored to BACKLOG `polymorphic_interface_connections` / abstract-return optimizer entry card; reachability caveat added; pseudocode retained; no `NotImplementedError`. Comment-only.
- Low 1 (`ast_to_converted_selections` FragmentSpread `type_condition.name.value` unguarded deref): no comment edit — per the artifact this asymmetry is intentional and safe (named fragment definitions always carry a type condition; graphql-core validation rejects malformed ops before the optimizer). Deferred with trigger only; confirmed no comment change warranted.
- Low 2 (`with_runtime_prefix` fragment clone omits `arguments`): no comment edit — per the artifact the absence is deliberate (fragments have no arguments) and safe (every downstream read is defensive `getattr(sel, "arguments", None) or {}`). No-action audit record; confirmed no comment change warranted.

### Validation run
- `uv run ruff format .` — pass / no-changes (270 files left unchanged; the standing COM812-vs-formatter warning is pre-existing config noise, not a failure).
- `uv run ruff check --fix .` — pass (All checks passed!).

### Notes for Worker 3
- Incremental diff this pass is the single TODO-comment block only: `git diff HEAD -- django_strawberry_framework/optimizer/selections.py` shows the -6/+12 comment replacement and no logic lines.
- No shadow file used this pass (comment re-anchor only).
- `uv.lock` untouched by the ruff runs (`git diff HEAD -- uv.lock` empty).
- ERA001-safe: the block remains a proper TODO-anchored comment (AGENTS.md #18 exempts TODO-anchored pseudocode blocks); ruff check passed clean.
- Out-of-scope dirty files in the working tree (sibling rev-*.md, management/commands, fakeshop) are presumptively concurrent maintainer/other-worker work per AGENTS.md #33 — left untouched.

---

## Changelog disposition

### State
`Not warranted`.

### Reason
This cycle's only edit was an internal-only comment change: re-anchoring a stale `TODO(spec-035 Slice 3)` block to the active owner card (`BACKLOG polymorphic_interface_connections` / the abstract-return optimizer entry card). No behavior change, no public-API surface change, no typed-error contract change, no symbol added or removed — the `included_field_selections` signature and body are untouched and the default INLINE-all path is byte-for-byte unchanged. A staged-slice TODO re-anchor is exactly the internal-comment category that does not surface to a consumer.

The disposition cites BOTH mandatory anchors:

- **AGENTS.md #21** — "Do not update CHANGELOG.md unless explicitly instructed." Nothing in this cycle instructs a CHANGELOG edit.
- **Active-plan silence** — the dispatch prompt and the artifact carry no CHANGELOG authorization for this cycle, and a per-file pass is never the authorising scope (CHANGELOG drift, were any present, forwards to the project pass). There is no drift to forward regardless: the change is consumer-invisible.

### What was done
No `CHANGELOG.md` edit. `git diff HEAD -- CHANGELOG.md` is empty (confirmed clean at dispatch).

### Validation run
- No source touched this pass (disposition-only). Per the dispatch prompt, ruff was not re-run.
- `git diff HEAD -- CHANGELOG.md` — empty (no edit).

---

## Verification (Worker 3, terminal)

### Cycle-closure check — full standard cycle (Medium + 2 no-action Lows)

Terminal verify over the whole cycle (logic-accepted + comments-accepted + changelog disposition all recorded above). Confirmed sound for closure.

- **Final diff is TODO-comment-only.** `git diff HEAD -- django_strawberry_framework/optimizer/selections.py` (HEAD `58ca2def`) is exactly one hunk: the -6/+12 TODO block above `included_field_selections`. Every changed line is `#`-prefixed; the `def included_field_selections(...)` signature and body are untouched. No logic line, no test change. `git diff HEAD -- CHANGELOG.md` empty (matches `Not warranted`).
- **Diff-stat dirty paths attribute to a CLOSED sibling cycle.** `git diff --stat HEAD` over `django_strawberry_framework/`+`tests/` shows `management/commands/_imports.py`, `export_schema.py`, `inspect_django_type.py`, `tests/management/test_imports.py` dirty — these attribute to the closed sibling cycle `rev-management__commands.md` (verified, `[x]` at review-0_0_10.md:90; plus the two file children `[x]` at :88-89). Not this cycle's edits; this file's own diff is the single comment hunk.
- **Medium fully addressed — TODO re-anchored to the active owner.** New anchor `TODO(BACKLOG polymorphic_interface_connections — the abstract-return optimizer entry card)` names the live, unscheduled card (`BACKLOG.md:1060` `### \`polymorphic_interface_connections\``). The stale `spec-035 Slice 3` is genuinely DEFERRED and complete: `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md:5` "COMPLETE … G3 deferred", `:47` "Slice 3 (G3) is DEFERRED — its design retained below as carry-forward requirements but no runtime code lands here", `:226` Decision 6 "Status: DEFERRED — carry-forward requirements, no runtime code in spec-035 … retained verbatim as the design contract for the follow-up abstract-return optimizer entry card (the BACKLOG `polymorphic_interface_connections` work)". No working-location copy remains (`ls docs/spec-035*` → no matches; archived to `docs/SPECS/`). The old anchor pointed at a slice its own spec retracted — confirmed stale.
- **Reachability caveat accurate against LIVE source (not just spec prose).** The new comment's load-bearing claim ("an abstract … root field never reaches the walker today — `registry.model_for_type` returns `None` for the abstract origin, so `_optimize` passes the queryset through before this inliner runs … R1") verified end-to-end: `django_strawberry_framework/registry.py:242` `def model_for_type(self, type_cls) -> type[models.Model] | None` (returns `None` for an unregistered/abstract origin); `extension.py:48` `from ..registry import registry`; `extension.py:625` `model = registry.model_for_type(origin)` inside `_resolve_model_from_return_type`; `extension.py:803-811` `_optimize` `resolved = _resolve_model_from_return_type(info)` / `if resolved is None: … return result` — the passthrough `return result` precedes `self.apply_to(...)` at `:812`. (The comment-pass prose at this file's line 150 cited `optimizer/registry.py` and `extension.py:625-626/803-810`; the symbol actually lives at top-level `registry.py:242` and the lines drifted by one — cosmetic path/line imprecision in the verification prose; the symbol-qualified reference `registry.model_for_type` in the actual SOURCE comment is correct and the chain holds. Not a rejection trigger.)
- **AGENTS.md #26 compliant.** Re-anchored TODO names the active doc/card; no `NotImplementedError` added and none warranted — the default INLINE-all path is complete and the abstract field never reaches the inliner today, so the call path must NOT fail (#26: pair with `NotImplementedError` only when the call path must fail loudly). Tri-state INLINE / SKIP / RECURSE_FRAGMENTS_ONLY pseudocode retained (matches Decision 6/7 carry-forward design).
- **Two Lows correctly no-action.** Low 1 (FragmentSpread `type_condition.name.value` unguarded deref) and Low 2 (`with_runtime_prefix` fragment clone omits `arguments`) received no comment edit — both intentional, safe asymmetries per the artifact (named fragment defs always carry a type condition + graphql-core validation rejects malformed ops; downstream `arguments` reads are defensive `getattr(..., None) or {}`). No GLOSSARY-only fix present.
- **Changelog `Not warranted` justified with both citations.** Disposition cites AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") AND active-plan silence; `git diff HEAD -- CHANGELOG.md` empty. Internal-only framing is honest — the change is a comment re-anchor with zero public-API surface, so `Not warranted` is the correct state (not "deferred to maintainer").
- **Ruff clean.** `uv run ruff format --check django_strawberry_framework/optimizer/selections.py` → "1 file already formatted"; `uv run ruff check …/selections.py` → "All checks passed!". TODO-anchored pseudocode block is ERA001-exempt (AGENTS.md #18); no `noqa` needed.
- **Nothing regressed.** No source/test/behavior change this cycle; no pytest run warranted (comment-only, no test introduced).

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `optimizer/selections.py` checklist box at `docs/review/review-0_0_10.md:98`.

---

## Iteration log

_None yet._
