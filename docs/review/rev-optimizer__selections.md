# Review: `django_strawberry_framework/optimizer/selections.py`

Status: verified

## DRY analysis

- **Fold the three fragment-recursing converted-selection walks onto one fragment-descent primitive.** `included_field_selections` (`selections.py::included_field_selections`, src 178-188), `named_children` (`selections.py::named_children`, src 191-204), and `direct_child_selected._check` (`selections.py::direct_child_selected #"def _check"`, src 258-261) each re-spell the same "if `is_fragment(child)`: recurse into `getattr(child, "selections", None) or []`, else handle the field" skeleton with different leaf actions (flatten / name-filter-and-collect / name-match-bool) and different directive policy (see the Medium below). A shared internal generator `_iter_field_descendants(selection, *, through_fragments_only: bool, include_filter: bool)` yielding leaf field selections would let all three become thin leaf-action wrappers and would force a single, deliberate answer to "does this walk honor `@skip`/`@include`?" Defer until the directive-policy inconsistency (Medium below) is resolved — collapsing the three onto one primitive is the natural vehicle for that fix, so do them together rather than extracting first and patching policy after.
- **`edges { node }` unwrap loop is twinned across the two converted-selection consumers.** `walker.py::_connection_node_selections` (walker.py src 1027-1040) and `extension.py::_connection_node_child_selections` (extension.py src 362-375) run byte-near-identical `for edge in named_children(sel,"edges"): for node in named_children(edge,"node"): node_children.extend(node_children_with_runtime_prefix(node, runtime_prefixes=...))` loops; the only divergence is single-path (`extension`, root seam) vs multi-prefix (`walker`, nested) prefix arithmetic. The shared per-pair body already lives here as `node_children_with_runtime_prefix`; the remaining duplication is the prefix-fanout. Defer until a third `edges { node }` unwrap consumer lands (e.g. an aggregate-over-connection seam); then lift the double loop into `selections.py` parameterized on a `prefix_fanout: Callable[[selection], tuple[tuple[str,...],...]]`. Not act-now: the two prefix shapes are load-bearingly different and a 2-site extraction would re-hide the fanout.
- None further — the AST adapter trio (`ast_child_selections` / `resolve_unvisited_fragment` / `directive_variable_names`) is already the single home for the three `extension.py` AST walkers (docstring src 8-10), each primitive has exactly one shape, and the `is_fragment` discriminator is correctly single-sited and shared by all converted-selection walks.

## High:

None.

## Medium:

### `direct_child_selected` ignores `@skip` / `@include`, diverging from every other converted-selection walk

`direct_child_selected._check` (`selections.py::direct_child_selected #"def _check"`, src 258-261) recurses through fragments and matches on `name` with **no `should_include` gate**:

```django_strawberry_framework/optimizer/selections.py:258:261
    def _check(selection: Any) -> bool:
        if is_fragment(selection):
            return any(_check(child) for child in getattr(selection, "selections", None) or [])
        return getattr(selection, "name", None) == name
```

Every sibling converted-selection walk filters disabled selections first: `included_field_selections` gates on `should_include(selection)` before inlining/appending (src 179-187), and `named_children` gates on `should_include(child)` and `should_include` on the fragment shell (src 195-201). `direct_child_selected` does neither — it recurses into a `@skip(if: true)` inline fragment and matches a `totalCount @skip(if: true)` field.

Why it matters: the sole consumer is `connection.py::_total_count_requested` (connection.py src 388-391), which fires the connection's `COUNT` and, the docstring warns (selections.py src 248-255; connection.py src 378-381), can trip a spurious M1-guard raise on a non-queryset source. A consumer who writes `{ totalCount @skip(if: $hideCount) ... }` with `$hideCount = true` expects no count work; today the count still fires. This is exactly the cross-adapter directive drift the module docstring (src 11-14) says this consolidation exists to prevent: "a directive or fragment fix landing on one traversal but not the other produces ... false strictness warnings, or extra `COUNT` work." The directive policy landed on the walker/`included_field_selections` traversal but not on the `totalCount`-detection traversal.

Recommended change: gate `_check` on `should_include` — for a fragment, skip it (and its subtree) when `should_include(selection)` is `False`; for a field, return `False` when `should_include` is `False` even if the name matches. Cleanest as part of the DRY fold above (`_iter_field_descendants(..., include_filter=True)`), so the `@skip`/`@include` semantics are defined once for all three walks. Add a pinning test under `tests/optimizer/test_selections.py` (e.g. `test_direct_child_selected_honors_skip_include`) asserting a `@skip(if: true)`-decorated direct `totalCount` and a `@skip(if: true)` fragment wrapping `totalCount` both return `False`, plus a live-query analogue in `examples/fakeshop/test_query/` if a connection with `total_count=True` and a skip variable is reachable there.

Verification note for Worker 2/3: confirm against the converted-selection `directives` dict shape that `@skip`/`@include` survive `convert_selections` onto these node-level selections at resolve time (the directives map is what `should_include` reads at src 144). If converted selections at the connection-field child level provably never carry these directives (i.e. Strawberry pre-resolves `@skip`/`@include` before the resolver sees `selected_fields`), the harm is unreachable and this drops to a forward-looking Low keyed to "when a converted-selection consumer first relies on `direct_child_selected` seeing live `@skip`/`@include`." That is a SPEC/runtime fact a single targeted test settles; until settled, the inconsistency between this walk and its two siblings is a real Medium because the three are advertised as sharing one directive policy.

## Low:

### Module docstring attributes the `edges { node }` unwrap to "the connection seam" but the converted-selection unwrap site lives in `extension.py`

The docstring's converted-selection adapter list (src 22-29) says `named_children` / `node_children_with_runtime_prefix` / `with_runtime_prefix` operate "for `optimizer/walker.py` and the connection seam," and the module header comment (src 122-124) names "the connection optimizer seam." In practice the converted-selection edge/node unwrap has two call sites — `walker.py::_connection_node_selections` (nested) and `extension.py::_connection_node_child_selections` (root seam) — both inside `optimizer/`; `connection.py` consumes only `direct_child_selected`. The prose is not wrong (the root seam IS a connection seam), but a reader chasing "the connection seam" may look in `connection.py` and find only the `totalCount` predicate. Minor: tighten the docstring to name `extension.py`'s root-connection seam explicitly alongside the walker, distinct from `connection.py`'s `totalCount` detection. Comment-pass only; no behavior at stake.

### `with_runtime_prefix` fragment branch silently relies on a fragment never being the runtime-prefix leaf

`with_runtime_prefix` (src 207-226) clones a fragment by recursing into its children (src 209-218) and clones a field by attaching `_optimizer_runtime_prefixes` (src 219-226); a fragment shell itself never carries the prefix marker. This is correct — prefixes belong on field leaves — but it is load-bearing and undocumented: if a future caller expected the fragment wrapper to carry the prefix, the marker would be silently absent. One sentence in the docstring ("fragments are descended, never marked; the prefix lands on field leaves only") would lock the invariant. Comment-pass only.

## What looks solid

### DRY recap

- **Existing patterns reused.** This module IS the 0.0.9 DRY consolidation (`docs/feedback.md` Major 2): `walker.py` (src 35-59) and `extension.py` (src 66-87) both import the substrate and keep underscore aliases so existing bodies/tests resolve unchanged, and `extension` no longer imports edge-node helpers back from `walker` (the reverse dependency removed, module docstring src 30-36). `is_fragment` (src 128-139) is correctly the single fragment-vs-field discriminator shared by the walker, the `edges { node }` unwrap, and `direct_child_selected`.
- **New helpers considered.** A single over-generic polymorphic walker over both AST and converted shapes was explicitly considered and rejected by the review the module docstring quotes (src 16-19): "Keep the adapters explicit, but share the recursion and directive/fragment policies." The two-adapter split is the right granularity — the AST shape (`selection_set.selections`, list-shaped `directives`, `FragmentSpreadNode`) and the converted shape (`.selections`, dict-shaped `directives`, duck-typed `type_condition`) are structurally different enough that one walker would be a tangle of branches.
- **Duplication risk in the current file.** The 7x `"selections"` / 4x `"directives"` repeated literals (overview) are attribute names threaded through `getattr`, not dispatch keys — intentional and not constant-extractable. The fragment-recursion shape repeats three times (see DRY analysis) but the leaf actions genuinely differ; the fold is deferred, not act-now.

### Other positives

- **Reflective access is uniformly defensive.** All 19 `getattr` sites use a `None`/`()`/`[]` default and the `or` idiom (`... or ()`, `... or []`, `... or {}`), so `directives=None`, absent `selections`, and empty collections all degrade to a no-op loop rather than an `AttributeError`. `resolve_unvisited_fragment` guards `node.name` being absent (src 87), an unnamed/already-visited/undefined fragment (src 88-92), and only mutates `visited_fragments` on success (src 93) — the shared cycle-detection contract its docstring promises (src 79-83).
- **`directive_variable_names` is correctly narrow.** Only `("skip","include")` directives (src 113), only `VariableNode`-valued args (src 116), defensive against a non-`DirectiveNode` in the collection (src 110, pinned by `test_directive_variable_names_ignores_non_directive_objects`). This is the right plan-cache-key surface — non-selection-shaping variables stay out (GLOSSARY "Variable filtering," docs/GLOSSARY.md:956).
- **`response_keys` fallback is sound.** `getattr(..., "_optimizer_response_keys", None) or (response_key(selection),)` (src 165-167) returns the merged-key list when present (always non-empty — `_merge_aliased_selections` seeds it with one key at walker.py src 924 and only appends) and a single-key tuple otherwise; the falsy-`or` can never yield an empty tuple.
- **Termination is guaranteed.** `resolve_unvisited_fragment`'s visited-set mutation makes fragment recursion in the AST walkers monotone (a re-spread is a no-op); the converted-selection recursions (`included_field_selections`, `named_children`, `direct_child_selected._check`, `with_runtime_prefix`) descend a finite already-converted selection tree with no back-edges. No depth guard is needed.
- **Cycle-safety claim holds.** Imports are stdlib + graphql-core AST node types only (overview Imports; no first-party imports); `walker` and `extension` depend on this module and it depends on neither, matching the docstring (src 30-36). Zero Django/ORM markers (overview) — correct for a pure selection-tree substrate.
- **Test discipline.** `tests/optimizer/test_selections.py` has a dedicated direct test for every public helper, including the two trickiest edges: `test_direct_child_selected_ignores_nested_field_selections` (the fragment-only-descent invariant) and `test_directive_variable_names_ignores_non_directive_objects`.

### Summary

A clean, well-documented 0.0.9 consolidation that does what its docstring claims: one home for the AST and converted-selection traversal primitives, two explicit adapters, no reverse `extension`->`walker` dependency, defensive reflective access throughout, and dedicated per-helper test coverage. The substrate is genuinely shared by its three advertised consumers — the AST cache-key walk (`extension.py`), the converted-selection plan walker (`walker.py`), and the connection `totalCount` detection (`connection.py`). One real Medium: `direct_child_selected` is the lone converted-selection walk that does NOT honor `@skip`/`@include`, diverging from `included_field_selections` / `named_children` and from the module docstring's own promise that the three walks share one directive policy — a `@skip`-ped `totalCount` would still fire the count (severity gated on whether converted selections at the connection-child level ever carry live skip/include directives at resolve time, which a single test settles). Two comment-pass Lows and two deferred DRY folds (the fragment-recursion skeleton — the natural vehicle for the Medium fix — and the `edges { node }` double loop). No GLOSSARY drift: the GLOSSARY describes the behaviors (plan-cache selection-shape keys at docs/GLOSSARY.md:955-956, `totalCount` selection-gating at :297, relation `<field>Connection` synthesis at :233) but names none of this module's symbols, so no entry to reconcile.

---

## Fix report (Worker 2)

### Verdict: REAL Medium (settled empirically)

The Medium's gating question — "do converted selections at the connection-child
resolve point carry live, already-evaluated `@skip`/`@include`?" — resolves to
**YES**. `info.selected_fields` is `convert_selections(info, info.field_nodes)`
(strawberry `types/info.py::Info.selected_fields` -> `types/nodes.py::convert_selections`):
it walks the RAW graphql-core `field_nodes`, and `convert_directives` records each
directive's evaluated args (`{"skip": {"if": True}}`, variable resolved through
`convert_value`) onto the `SelectedField`/`InlineFragment`/`FragmentSpread` WITHOUT
dropping the node. Strawberry does NOT pre-resolve `@skip`/`@include` before the
resolver sees selections — so a `totalCount @skip(if: true)` reaches
`direct_child_selected` with its directive live, and the ungated `_check` matched
it by name and fired the connection `COUNT`.

Empirical probe (temp live fakeshop tests, since deleted) against
`allLibraryGenresConnection` (`Meta.connection = {"total_count": True}`) with
`CaptureQueriesContext`, BEFORE the fix:

- `totalCount @skip(if: true)` -> response correctly omits `totalCount` (Strawberry
  excludes it from output) BUT **1 `COUNT(` query fired** — a spurious DB hit.
- `totalCount @include(if: $show)` with `$show=false` -> same: field omitted,
  **COUNT still fired**. (variable-driven directive, also live.)

AFTER the fix both fire **0** COUNT queries; the `@skip(if: false)` control still
fires 1 and returns `totalCount == 3`. The false "fires the COUNT" claim is
therefore CONFIRMED, not disproven — this was a genuine spurious-query / wrong
selection-gating bug, exactly the cross-adapter directive drift the module
docstring says this consolidation exists to prevent.

### Files touched
- `django_strawberry_framework/optimizer/selections.py:258-263` (`direct_child_selected._check`) — added a leading `if not should_include(selection): return False` gate, matching the `should_include` gate `included_field_selections` (src 180) and `named_children` (src 195) already apply. For a fragment shell this prunes the whole subtree when `@skip(if: true)` / `@include(if: false)`; for a field it returns `False` even on a name match when the directive excludes it. The DRY fold onto `_iter_field_descendants` the artifact suggests is explicitly DEFERRED (DRY bullet 1), so the gate is applied inline, consistent with the two siblings.

### Tests added or updated
- `tests/optimizer/test_selections.py::test_direct_child_selected_honors_skip_include` — package-internal pin on the helper: direct `@skip(if: true)` and `@include(if: false)` fields return `False`; a `@skip(if: true)` fragment shell hides its `totalCount` subtree; `@skip(if: false)` / `@include(if: true)` still match (no over-pruning).
- `examples/fakeshop/test_query/test_library_api.py::test_genre_connection_total_count_skip_include_no_count` — the permanent live pin (AGENTS.md-preferred): three excluded shapes (direct `@skip(if: true)`, variable-driven `@include(if: $show=false)`, named-fragment-wrapped `@skip(if: true)`) each issue ZERO `COUNT(` SQL and omit the field; the `@skip(if: false)` control fires exactly 1 COUNT and returns `totalCount == 3`. Sits beside the existing `test_genre_connection_total_count_omitted_no_count` (the absence-case sibling).

### Validation run
- `uv run ruff format .` — pass / no-changes (265 files unchanged).
- `uv run ruff check --fix .` — pass / all checks passed (only the standing COM812 formatter-conflict warning).
- Focused tests (single nodes, not a suite): both new tests pass. Pre-fix probe reproduced the spurious COUNT; post-fix probe shows 0 COUNT on excluded, 1 COUNT + `totalCount == 3` on the kept control.

### Notes for Worker 3
- Shadow file used: `docs/shadow/django_strawberry_framework__optimizer__selections.overview.md` (overview only; line numbers cited are from the original source).
- Live-query test vehicle: named fragment SPREAD (`...CountFields @skip(if: true)`), NOT an anonymous inline fragment. Reason: an anonymous inline fragment (`... { ... }`, `name=None`) placed directly under a `DjangoConnectionField` selection crashes the resolver with `'NoneType' object has no attribute 'name'` — and it does so EVEN WITH NO DIRECTIVE and even wrapping a node-level field, so it is a PRE-EXISTING, UNRELATED walker bug (unguarded `sel.name` on the converted-selection plan path in `optimizer/walker.py`, e.g. around `walker.py:247` / `:919`), NOT caused by this Medium and not fixed by this gate. Out of scope for this artifact; flagged as a separate background task. Worker 3: the FRAG case in the live test uses a named fragment precisely to avoid that orthogonal crash.
- Diff is LOGIC-BEARING: one executable guard line in `selections.py` plus the two tests. `git diff --stat` vs baseline `0872a20f` for this cycle's files: `selections.py` +2, `test_library_api.py` +96, `test_selections.py` +50.
- `uv.lock` untouched. The many other dirty files in the working tree are concurrent worker/maintainer work (AGENTS.md #33) — out of scope, not mine.
- Docstring on `direct_child_selected` (src 244-256) is now incomplete (says nothing about `@skip`/`@include`) but not wrong; deferred to the comment pass per the standard cycle.

---

## Verification (Worker 3) — logic pass

### Logic verification outcome

**Medium (`direct_child_selected` ignores `@skip`/`@include`) — fix accepted, logic holds.**

- **Gating premise confirmed real (bug is genuine).** Independently re-ran both new tests against
  baseline source (`git stash` of `selections.py` only, tests left at post-fix) and the bug
  reproduces: the package-internal `test_direct_child_selected_honors_skip_include` fails
  `True is False` (ungated `_check` matches `totalCount @skip(if: true)` by name); the live
  `test_genre_connection_total_count_skip_include_no_count` fails case (1) `assert 1 == 0` — a
  spurious `COUNT(` SQL fired for `totalCount @skip(if: true)` against `allLibraryGenresConnection`
  (`Meta.connection={"total_count": True}`). This confirms converted selections at the
  connection-child resolve point DO carry live, already-evaluated `@skip`/`@include` (Strawberry's
  `convert_selections` does not pre-drop the node), so the Medium is a real spurious-COUNT bug, not a
  false premise.
- **Fix suppresses it (post-fix).** Restored fix → both tests pass; the live case shows 0 `COUNT(` for
  the three excluded shapes (direct `@skip(if: true)`, variable-driven `@include(if: $show=false)`,
  named-fragment-wrapped `@skip(if: true)`).
- **Gate matches the sibling gate (consistency, not ad-hoc).** The one added line
  (`selections.py::direct_child_selected #"if not should_include(selection)"`, src 259-260) calls the
  SAME `should_include` helper (src 142-155) that `included_field_selections` applies first (src 180)
  and `named_children` applies first (src 195), placed FIRST before the `is_fragment` discriminator —
  identical structure. For a `@skip(if: true)` fragment shell the gate returns `False` before
  recursing, pruning the whole subtree; for a field it returns `False` on name match when the
  directive excludes. Confirmed at source.
- **No over-suppression.** Control `@skip(if: false)` (live) fires exactly 1 COUNT and returns
  `totalCount == 3`; no-directive control (`test_direct_child_selected_matches_direct_and_fragment_wrapped`)
  still passes; `@include(if: true)` fragment case still matches (test :235). `should_include`'s own
  truth table is pinned by `test_should_include_honors_skip_and_include` (:122).

### Low findings disposition
Both Lows (docstring "connection seam" attribution; `with_runtime_prefix` fragment-never-marked
invariant) are comment-pass only, correctly deferred to the comment pass. Not logic-bearing.

### DRY findings disposition
Both DRY bullets (fold the three fragment-recursing walks onto `_iter_field_descendants`; the
`edges { node }` double-loop) stay DEFERRED per the artifact, with triggers intact. The fix applies
the gate inline, consistent with the two siblings — the correct choice given the fold is deferred.

### Temp test verification
No temp test files needed. Reproduction driven via `git stash` of the source-only hunk plus the two
permanent tests (pre-fix fail / post-fix pass). Both tests are placed per AGENTS.md: the live
fakeshop pin in `examples/fakeshop/test_query/test_library_api.py` (preferred; inline `_seed_genres`
per the library no-services rule, sits beside the absence-case sibling
`test_genre_connection_total_count_omitted_no_count`) and the package-internal helper pin in
`tests/optimizer/test_selections.py` (the helper's `should_include` semantics are genuinely
unreachable as a unit otherwise). Assertions pin the right surface.

### Validation
- `uv run pytest tests/optimizer/test_selections.py -k honors_skip_include --no-cov` → 1 passed
  (post-fix); fails pre-fix.
- `uv run pytest examples/fakeshop/test_query/test_library_api.py -k ...skip_include_no_count --no-cov`
  → 1 passed (post-fix); fails pre-fix at case (1).
- `git diff --stat` baseline `0872a20f` for cycle files: `selections.py` +2, `test_selections.py` +50,
  `test_library_api.py` +96 — matches Fix report; logic-bearing.
- Ruff format `--check` + check on all three files: clean (standing COM812 formatter-conflict warning only).
- `git diff -- CHANGELOG.md` empty (changelog disposition is the later pass).

### Verification outcome
`logic accepted; awaiting comment pass` — sets top-level `Status: logic-accepted`. Checklist box NOT
marked (interim pass). Docstring on `direct_child_selected` (silent on `@skip`/`@include`) is now
incomplete-but-not-wrong, correctly deferred to the comment pass.

---

## Verification (Worker 3) — comment pass

### No logic changed since logic-accept
`git diff 0872a20f -- selections.py` confirms the ONLY executable delta is the logic-pass guard
`if not should_include(selection): return False` placed FIRST in `_check` (src 275-276) — byte-identical
to the logic-accept line, unchanged this pass. The comment-pass diff is docstring text only across the
three blocks (module docstring src 29-32; `with_runtime_prefix` src 213-216; `direct_child_selected`
src 266-271). No logic changed → not `revision-needed` on that axis.

### Docstring accuracy (3 changes)
- **(a) `direct_child_selected` directive-gate paragraph (src 266-271):** accurate. Matches the `_check`
  body (gate first → fragment recurse → name match) and the logic-accept findings — explains WHY the
  walk needs the gate (converted selections carry live `@skip`/`@include`; an excluded `totalCount` must
  not fire COUNT), not WHAT the line does, so non-restating. **No-inline-comment decision matches sibling
  idiom:** confirmed the two sibling gates `included_field_selections` (src 183) and `named_children`
  (src 198) carry bare uncommented `if not should_include(...)` lines, so an inline comment on the
  now-consistent `_check` gate would over-comment; rationale correctly lives at docstring tier.
- **(b) module docstring three-named-consumers tightening (src 29-32):** accurate, grep-confirmed at
  source. walker.py nested windows = `walker.py:1028-1035` (`_named_children`/`_node_children_with_runtime_prefix`);
  extension.py root-connection seam edges{node} unwrap = `extension.py:365-370` (same pair); connection.py
  `totalCount` via `direct_child_selected` = `connection.py:389` — and that is the ONLY consumer of
  `direct_child_selected`, so the "(`direct_child_selected` only)" qualifier holds. Resolves the Low's
  reader-confusion (chasing "the connection seam" no longer lands in `connection.py` expecting the unwrap).
- **(c) `with_runtime_prefix` fragments-never-marked invariant (src 213-216):** correct. The fragment
  branch (src 218-227) builds a `SimpleNamespace` with NO `_optimizer_runtime_prefixes`; only the field
  branch (src 228-235) attaches the marker. "Fragments are descended, never marked; the marker lands on
  field leaves only" matches the body exactly.

### Validation
- `git diff 0872a20f -- selections.py`: +20/-2, one executable guard line + 3 docstring blocks. Matches
  the Comment/docstring pass Fix report.
- Ruff format `--check` + check on selections.py: clean (standing COM812 formatter-conflict warning only).

### Verification outcome
`comments accepted; awaiting changelog disposition` — sets top-level `Status: comments-accepted`.
Checklist box NOT marked (interim pass). No logic changed since logic-accept; the 3 docstring changes are
accurate and non-restating, no-inline-comment matches sibling idiom.

---

## Verification (Worker 3) — terminal pass

Closes the Medium multi-pass (logic-accepted + comments-accepted recorded above; changelog
disposition = Not warranted). Bare `Status: fix-implemented` on entry → terminal-verify.

### Cycle diff scope confirmed
`git diff 0872a20f --stat` for the cycle's three files: `selections.py` +20/-2, `test_selections.py`
+50, `test_library_api.py` +96 (166 insertions, 2 deletions total). Source delta is EXACTLY the
intended change — ONE executable guard line (`if not should_include(selection): return False`, src
275, placed FIRST in `_check`) plus 3 docstring blocks (module-docstring three-named-consumers
tightening src 26-32; `with_runtime_prefix` fragments-never-marked invariant src 211-216;
`direct_child_selected` directive-gate paragraph src 266-271). No other source/test files touched in
the cycle scope. Matches the Fix report and both interim passes byte-for-byte.

### Every finding addressed-or-rejected-with-evidence
- **Medium (spurious COUNT) — fixed at root cause.** The fix is the `should_include` gate inside
  `_check` (the `should_include` predicate itself at src 145-158), not a surface patch — it makes
  `direct_child_selected` apply the SAME gate, in the SAME first position, as its two sibling
  converted-selection walks `included_field_selections` (gate at src 183) and `named_children` (gate
  at src 198), both re-confirmed as uncommented one-liners at source this pass. Two tests pin it:
  package-internal `test_direct_child_selected_honors_skip_include` (3 excluded shapes → False, 2
  controls → True) and live `test_genre_connection_total_count_skip_include_no_count` (3 excluded
  shapes → 0 COUNT SQL + field omitted, control `@skip(if: false)` → 1 COUNT + `totalCount == 3`).
- **2 comment-tier Lows — applied/forward-looking.** Low 1 (module-docstring "connection seam"
  mis-attribution) applied src 26-32; Low 2 (`with_runtime_prefix` fragment-never-marked invariant)
  applied src 211-216. Both accurate vs the body (re-verified at source) and non-restating.
- **2 DRY bullets — deferred with triggers intact.** `_iter_field_descendants` fold (the natural
  vehicle for the Medium; gate applied inline since the fold is deferred) and the `edges { node }`
  double-loop (third-consumer trigger). Correct per the artifact.

### Changelog `Not warranted` justified
`git diff -- CHANGELOG.md` is EMPTY (re-confirmed this pass). Disposition cites both required pillars
(AGENTS.md #21 + active-plan/per-file-cycle silence). Internal-only framing matches the diff scope:
the fix is a correctness/perf fix internal to NEW-in-0.0.9 surface (`DjangoConnectionField` +
`Meta.connection` opt-in `totalCount`), today (2026-06-13) IS the 0.0.9 release date, so no released
public contract delta to preserve — folds into the new feature's Added entry, correctly NOT
"deferred to maintainer."

### Re-affirm (focused, no source edit)
- Post-fix tests both pass: `pytest tests/optimizer/test_selections.py -k honors_skip_include`
  → 1 passed; `pytest examples/fakeshop/test_query/test_library_api.py -k skip_include_no_count`
  → 1 passed.
- Load-bearing proof WITHOUT editing tracked source (per dispatch "Do NOT edit source/tests"): a
  no-edit `uv run python` probe drove the REAL shipped `direct_child_selected` (3 excluded shapes →
  False, 2 controls `@skip(if:false)`/`@include(if:true)` → True, no over-suppression) AND
  reconstructed the baseline ungated `_check` inline to confirm it WOULD spuriously match the
  `totalCount @skip(if: true)` field and fragment — proving the guard line is load-bearing. The live
  test (which actually issues the COUNT query) corroborates the suppression at the SQL layer.
- Ruff `format --check` + `check` on all three cycle files: clean (standing COM812 formatter-conflict
  warning only).

### Temp test verification
One gitignored probe `docs/review/temp-tests/selections/reaffirm.py` used for the no-edit
load-bearing re-affirm, since deleted. Both permanent tests sit at the AGENTS.md-correct trees (live
fakeshop pin + package-internal helper pin); no promotion needed.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the
`optimizer/selections.py` checklist box in `docs/review/review-0_0_9.md`.

---

## Comment/docstring pass

### Files touched
- `django_strawberry_framework/optimizer/selections.py::direct_child_selected` (docstring, src 265-272) — appended a directive-gate paragraph: `direct_child_selected` is gated on `should_include` like `included_field_selections` / `named_children`; converted selections carry live, already-evaluated `@skip`/`@include`, so a `totalCount @skip(if: true)` (or a `@skip`-ped fragment wrapping it) must NOT fire the connection `COUNT`; an excluded field returns `False` even on a name match and an excluded fragment shell prunes its subtree. Documents the WHY of the logic-pass gate at the docstring tier. NO inline comment was added to the `_check` body's gate line — per dispatch and local idiom, the sibling gates (`included_field_selections` src 180, `named_children` src 195) are uncommented one-liners, so an inline comment on the now-consistent `_check` gate would over-comment relative to its siblings; the rationale lives in the docstring instead.
- `django_strawberry_framework/optimizer/selections.py` (module docstring, src 24-32) — Low 1: tightened the converted-selection adapter consumer attribution from "`optimizer/walker.py` and the connection seam" to three named consumers — `optimizer/walker.py` (nested connection windows), `optimizer/extension.py`'s root-connection seam (the `edges { node }` unwrap), and `connection.py`'s `totalCount` detection (`direct_child_selected` only). Resolves the reader confusion the Low named: a reader chasing "the connection seam" no longer lands in `connection.py` expecting the unwrap (which lives in `extension.py`).
- `django_strawberry_framework/optimizer/selections.py::with_runtime_prefix` (docstring, src 211-216) — Low 2: added one sentence locking the load-bearing invariant — fragments are descended, never marked; the `_optimizer_runtime_prefixes` marker lands on field leaves only; a fragment shell carrying the prefix would be meaningless.

### Per-finding dispositions
- Medium 1 (`direct_child_selected` directive gate): logic already landed and was logic-accepted; this pass documents it at the docstring tier and matches the sibling idiom (no inline comment on the one-liner). Applied.
- Low 1 (module docstring "connection seam" mis-attribution): applied — comment-pass-only per the artifact's own framing.
- Low 2 (`with_runtime_prefix` fragment-never-marked invariant): applied — comment-pass-only per the artifact's own framing.
- DRY 1 (`_iter_field_descendants` fold) and DRY 2 (`edges { node }` double loop): stay DEFERRED with triggers intact (not comment-pass items).
- GLOSSARY: no edit — the artifact reported no GLOSSARY drift (the GLOSSARY names none of this module's symbols), confirmed.

### Validation run
- `uv run ruff format .` — pass / no-changes (265 files unchanged).
- `uv run ruff check --fix .` — pass / all checks passed (standing COM812 formatter-conflict warning only).
- No pytest (comment pass; AGENTS.md forbids). Docstring-only edits, no executable change this pass.

### Notes for Worker 3
- This pass is docstring-only. `git diff` vs HEAD for this pass: `selections.py +20/-2`, all three hunks are docstring text (module-docstring consumer list, `with_runtime_prefix` docstring, `direct_child_selected` docstring). The single executable line vs baseline `0872a20f` (the logic-pass `should_include` guard in `_check`) is unchanged this pass and remains the only logic-bearing line.
- Deliberate no-inline-comment on the `_check` gate is per the dispatch instruction "do NOT over-comment a now-consistent one-liner if the siblings are uncommented" — sibling gates at src 180/195 carry no inline comment; rationale moved to the `direct_child_selected` docstring instead.
- `uv.lock` untouched. Other dirty files in the tree are concurrent worker/maintainer work (AGENTS.md #33), out of scope.
- Shadow used: `docs/shadow/django_strawberry_framework__optimizer__selections.overview.md` (overview only; cited line numbers are original-source).

---

## Changelog disposition

### State
`Not warranted`.

### Reason
Cites BOTH required pillars:

- **AGENTS.md #21** ("Do not update CHANGELOG.md unless explicitly instructed") — no
  authorization for a `CHANGELOG.md` edit this cycle.
- **Active plan silence** — this is a per-file cycle (`rev-optimizer__selections.md`),
  and a per-file cycle is NEVER the authorising scope; it forwards any changelog drift to
  the project pass. The dispatch prompt explicitly forbade editing `CHANGELOG.md` this pass.

Substantive judge (warranted-vs-not): the fix added a `should_include` directive gate so a
directive-excluded `totalCount` (`@skip(if: true)` / `@include(if: false)`) on a connection no
longer fires a spurious `COUNT(*)`. Both the `DjangoConnectionField` connection field and the
`Meta.connection` opt-in `totalCount` are NEW-in-0.0.9 surface (`CHANGELOG.md ## [0.0.9]` Added
entries — `**`DjangoConnectionField` (Relay connection field).**` and `**`Meta.connection`
opt-in `totalCount`.**`). Today (2026-06-13) IS the `## [0.0.9] - 2026-06-13` release date, so
this surface has never shipped under a released public contract. The spurious-COUNT bug is a
correctness/perf fix INTERNAL to that not-yet-released feature — there is no released
public-contract delta to preserve. A same-release internal correctness fix folds into the new
feature's own Added entry, not a standalone `Fixed` note. So this is NOT "Warranted but deferred
to maintainer": deferred-to-maintainer would require the bug to have escaped in 0.0.8 or earlier
(a real consumer-visible regression against a shipped contract), which it did not.

### What was done
No `CHANGELOG.md` edit.

### Validation run
- `uv run ruff format .` — pass / no-changes (no source/test/doc edit this pass).
- `uv run ruff check --fix .` — pass / no-changes.

---

## Iteration log

_None yet._
