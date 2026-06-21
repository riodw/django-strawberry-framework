# Review: `django_strawberry_framework/mutations/sets.py`

Status: verified

## DRY analysis

- **Operation-verb literals `"create"` / `"update"` / `"delete"` are spelled in three modules; `_VALID_OPERATIONS` is the declared-but-unconsumed single source.** `sets.py #"_VALID_OPERATIONS: frozenset"` (the named single-source set), `mutations/resolvers.py` (`#"meta.operation == \"create\""`:825, `:827` `== "update"`, and the three `_authorize_or_raise(..., "create"/"update"/"delete", ...)` calls at `:908`/`:946`/`:999`), and `mutations/permissions.py::_OPERATION_PERMISSION_ACTION` (dict keyed on the same three literals, `:37-41`). The `sets.py #"Single source\n# of truth"` comment asserts "Slice 3's resolver imports this rather than re-spelling the set" — the resolver does NOT import `_VALID_OPERATIONS` and re-spells each literal inline. Act-now (the comment is the finding below): bring reality into line with the comment by having `resolvers.py` import `_VALID_OPERATIONS` for any operation membership/iteration it does, OR — if the per-operation `if`-dispatch is intentionally literal — narrow the comment to claim only what is true (Slice 3 imports the verb *vocabulary*, e.g. a shared `OPERATIONS` tuple, not necessarily this `frozenset`). The verb *map* (`permissions.py`'s `{"create":"add",...}`) is a distinct concern (verb→Django-perm-codename) and is correctly its own dict — do not fold it into `_VALID_OPERATIONS`; only the bare membership-set is the single-source candidate.

## High:

None.

## Medium:

None.

## Low:

### Stale comment: `_VALID_OPERATIONS` claims a resolver import that does not exist

`sets.py #"Single source"` (the two-line comment above `_VALID_OPERATIONS`) reads: "Single source of truth: Slice 3's resolver imports this rather than re-spelling the set." Grep confirms `_VALID_OPERATIONS` has exactly one referencing module — `sets.py` itself (`git log -S` shows the comment landed in spec-036 commit `b61daa23` and the resolver never imported it). `mutations/resolvers.py` re-spells the three verbs as inline literals (`meta.operation == "create"` at `:825`, `== "update"` at `:827`, and `_authorize_or_raise(..., "create"/"update"/"delete", ...)` at `:908`/`:946`/`:999`). The constant IS a real single source for *its own* validation (`_validate_mutation_meta #"if operation not in _VALID_OPERATIONS"`) and the comment's first sentence ("The three valid `Meta.operation` values") is accurate; only the second sentence's cross-module claim is false. Harmless at runtime (no behaviour depends on the comment), but it misdescribes the module contract and would mislead a future DRY pass into thinking the resolver is already single-sourced.

Recommended change (comment-only, lowest-cost correct fix): drop or rewrite the "Slice 3's resolver imports this" sentence to state the actual contract — `_VALID_OPERATIONS` single-sources *this module's* `Meta.operation` membership check; the resolver dispatches on the verb literals directly. (The higher-quality alternative — actually importing `_VALID_OPERATIONS` into the resolver so the comment becomes true — is the DRY-analysis act-now item above; either resolves the inaccuracy, but the resolver-side change is a cross-module edit owned by `rev-mutations__resolvers.md` / the folder pass, whereas the comment fix is local to this file.)

```django_strawberry_framework/mutations/sets.py:87:88
# The three valid ``Meta.operation`` values (spec-036 Decision 5). Single source
# of truth: Slice 3's resolver imports this rather than re-spelling the set.
```

## What looks solid

### DRY recap

- **Existing patterns reused.** The module routes every shared concern to a canonical primitive rather than re-deriving: input shape/name/cache-key single-sourced through `mutations/inputs.py::mutation_input_shape` (the DRY-1 descriptor) so `_materialize_input_for #"shape = mutation_input_shape"` and `_materialize_merged_input #"shape = mutation_input_shape"` share one identity (`shape.cache_key` / `shape.type_name`); the expected-attr-name set (`_expected_input_attr_names`) is derived from the SAME `editable_input_fields` + `relation_input_annotation` the generator (`build_mutation_input`) uses, so the consumer-input validator cannot drift from the generator; the relation override shape-lock reads `relation_input_annotation`'s emitted annotation (`_annotation_core_is_global_id` peels via the shared `utils/typing.py::unwrap_return_type`) instead of re-deriving "GlobalID iff Relay-Node primary"; `SyncMisuseError` (`utils/querysets`) and `ConfigurationError` (`exceptions`) are the canonical raise types; `DjangoModelPermission` is the shared default seam.
- **New helpers considered.** `_validate_input_class` / `_validate_relation_override_types` split was evaluated as a single validator and correctly kept apart — the first is class-creation-time (name-only, registry-independent, `related_primary_type=None`), the second is phase-2.5 bind-time (needs `registry.get` populated for the id *type*); merging would force a registry lookup at class creation that is not yet reliable. `_materialize_input_for` vs `_materialize_merged_input` share five of six call-shape args but differ in caching semantics (all-generated caches in `_shape_build_cache`; merged is mutation-specific, never cached) and in the override path — folding them would hide the cache-vs-no-cache divergence; kept separate.
- **Duplication risk in the current file.** The repeated `"input_class"` / `"partial_input_class"` literals (overview: 5x each) are the two `Meta` attr names threaded as `attr_name=` for error messages and the create-vs-partial selector — intentional, name-as-data, not extractable. The two `_validate_input_class` call sites (`_validate_mutation_meta` create + partial halves) are deliberate per-attr validations, not a copy to fold.

### Other positives

- **Security/auth posture is fail-loud, never fail-open.** `check_permission` denies as soon as one `permission_class` returns falsy and returns `True` only when all allow; an async `has_permission` returning a (truthy) coroutine is `.close()`d and raised as `SyncMisuseError` — closing the documented authorization-bypass hole where `if not coroutine` would never deny. The async `check_permission` *override* is caught one level up in the resolver's `_authorize_or_raise` (correctly layered, not this file's concern). `permission_classes` is validated + normalized at class creation (`_validate_permission_classes`) so an invalid entry fails at import, not as a request-time `AttributeError` inside `check_permission`.
- **Meta validation is complete and fails loud at class creation.** Unknown-key guard (own-keys-only, no MRO walk, mirroring `types/base.py::_validate_meta`), no-resolvable-model, bad/absent `operation`, `fields`+`exclude` mutual exclusion, bare-string and duplicate-name rejection in `_normalize_field_sequence` (duplicates would otherwise collapse silently under the `frozenset` effective-set key), and the `delete` + `fields`/`exclude` rejection (delete generates no input so a typo'd field would never be validated downstream — rejecting the inapplicable keys is the root-cause posture, not a surface patch).
- **The `_resolve_model` seam is a genuine extension point, not speculative.** Documented as the override hook for the 0.0.12 form / 0.0.13 serializer flavors to supply the model without a literal `Meta.model` and without re-opening base validation; it is consumed today (`_validate_mutation_meta #"mutation_cls._resolve_model(meta)"`), so it earns its place rather than being preemptive plumbing.
- **`_resolve_primary_type` distinguishes the two finalize-time failure modes** (zero registered types → "no type to return"; multiple-without-primary → `Meta.primary` ambiguity) with `types_for` consulted only to phrase the right message, and stays robust even if a model reaches the bind unaudited by Phase-1.
- **`_strawberry_field_shape` is cycle-guarded.** The `of_type` peel loop tracks `id(type_)` in a `seen` set so a cyclic/corrupt wrapper chain terminates instead of spinning — the same defensive ceiling rationale as `utils/typing.py::unwrap_return_type`.
- **`bind_mutations` clears `_shape_build_cache` at the start of each pass** so a stale class from a prior failed/re-run finalize never leaks; the registry uses identity dedup + registration-order list, and `register_mutation` fails loud on a post-finalization declaration (mirroring `TypeRegistry._check_mutable`).

### Summary

`mutations/sets.py` is the largest, most contract-dense file in the new `mutations/` subpackage and it holds up under first-review scrutiny: the metaclass/`Meta`-validation pipeline is complete and fails loud at class creation, the async-bypass guard in `check_permission` closes a real authorization hole, the input-shape/name/cache-key trio is genuinely single-sourced through `mutation_input_shape`, and the relation-override shape-lock is derived from the same generator annotation it polices. GLOSSARY prose for every public symbol (`DjangoMutation`, `DjangoModelPermission`, `Meta.operation`/`model`/`permission_classes`, input-type generation, the `FieldError`/`<Name>Payload` envelope) matches the implementation with no drift. The single finding is a Low: the `_VALID_OPERATIONS` comment claims the Slice 3 resolver imports the set as a single source of truth, but the resolver re-spells the three verb literals inline and never imports it — a stale cross-module claim, harmless at runtime, fixable as a local comment correction (or, the DRY-preferred route, by actually importing the constant resolver-side, which is a cross-module edit owned by the resolver/folder pass).

---

## Fix report (Worker 2)

Consolidated single-spawn pass (shape #4): the sole finding is a comment-accuracy
Low with no logic change, so logic + comment + changelog dispositions are filled
together. The fix is itself a comment correction, recorded under the comment pass
below; this section records the route decision.

### Route decision — chose route A (correct the comment), rejected route B (import the set)

Route B (have `resolvers.py` consume `_VALID_OPERATIONS` so the comment becomes
true) is **not achievable as real DRY** — it is a forced fit. Evidence from the
resolver:

- `mutations/resolvers.py::resolve_mutation #"if meta.operation == \"create\""`
  (:825) and `#"if meta.operation == \"update\""` (:827) are per-operation
  **equality** dispatch against individual literals. A `frozenset` membership set
  cannot replace `== "create"` — `meta.operation == _VALID_OPERATIONS` is a
  category error, and `meta.operation in _VALID_OPERATIONS` would not select a
  branch.
- The three `_authorize_or_raise(..., "create"/"update"/"delete", ...)` calls
  (`:908`/`:946`/`:999`) pass a **single** verb literal as a positional argument;
  they need the one literal, not the 3-element set.

So importing the constant resolver-side would not eliminate a single verb literal —
the comment over-claimed when it said the resolver imports the set "rather than
re-spelling" it. Route A brings the comment into line with reality, which is the
root-cause fix for a finding whose root cause IS the inaccurate comment.

The DRY-analysis act-now alternative (a shared `OPERATIONS` vocabulary tuple the
resolver could iterate) is a genuine cross-module factoring question, but it is
owned by `rev-mutations__resolvers.md` / the folder pass per the artifact's own
scoping note (line 23) and is out of scope for this single-file cycle. The verb
**map** `mutations/permissions.py::_OPERATION_PERMISSION_ACTION` (:37-41) is a
distinct verb→Django-codename concern and is correctly left as its own dict — not
folded, per the artifact and AGENTS.md.

### Files touched

- `django_strawberry_framework/mutations/sets.py:87-92` — rewrote the two-line
  comment above `_VALID_OPERATIONS`. See comment pass below for the disposition.

### Tests added or updated

- None. Comment-only change; no behavior change, so no pinning test is warranted
  (Worker 2 comment dicta: avoid tests for purely internal/documentation edits).
  The existing membership check `_validate_mutation_meta #"if operation not in
  _VALID_OPERATIONS"` (:381) is unchanged and remains the runtime contract.

### Validation run

- `uv run ruff format .` — pass / no-changes (289 files unchanged).
- `uv run ruff check --fix .` — pass (all checks passed).
- `uv.lock` — clean (not touched).

### Notes for Worker 3

- No shadow file used (trivial localized comment edit).
- Route B rejected with evidence above: grep confirms `_VALID_OPERATIONS` is
  referenced only inside `sets.py` (`:89` def, `:381`/`:384` validation use);
  resolver dispatch is equality-against-literal and single-literal authorize args,
  neither of which a membership set can replace. Falsifiable via
  `grep -rn _VALID_OPERATIONS django_strawberry_framework/` and reading
  `resolvers.py:825-827`/`:908`/`:946`/`:999`.
- Cross-module DRY (shared verb vocabulary) deliberately deferred to the
  resolver/folder pass per artifact line 23 — not a rejection, a scope boundary.

---

## Comment/docstring pass

### Files touched

- `django_strawberry_framework/mutations/sets.py:87-92` — replaced the stale
  cross-module claim above `_VALID_OPERATIONS`.

  Before (2 lines):

  ```
  # The three valid ``Meta.operation`` values (spec-036 Decision 5). Single source
  # of truth: Slice 3's resolver imports this rather than re-spelling the set.
  ```

  After: the first sentence (accurate) is kept; the false second sentence is
  replaced with a statement of the actual contract — `_VALID_OPERATIONS` single-
  sources THIS module's membership check only (citing
  `_validate_mutation_meta #"if operation not in _VALID_OPERATIONS"`), and the
  resolver dispatches on the verb literals directly (`== "create"` / `"update"` in
  `mutations/resolvers.py`) so it does not import the constant. Uses symbol-
  qualified refs per AGENTS.md #27; no raw line numbers in the source comment.

### Per-finding dispositions

- DRY analysis (verb-literal spread / `_VALID_OPERATIONS` unconsumed): comment
  corrected to describe the true single-source scope (this module's membership
  check). Cross-module verb-vocabulary factoring deferred to resolver/folder pass.
  `permissions.py::_OPERATION_PERMISSION_ACTION` left as its own dict (distinct
  concern), per artifact.
- Low 1 (stale `_VALID_OPERATIONS` comment): fixed via route A — comment now states
  the actual contract; the false "Slice 3's resolver imports this" claim is removed.

### Validation run

- `uv run ruff format .` — pass / no-changes.
- `uv run ruff check --fix .` — pass.

### Notes for Worker 3

The fix lives entirely in the comment; the `_VALID_OPERATIONS` definition and its
two use sites (`:381`/`:384`) are byte-unchanged.

---

## Changelog disposition

### State

`Not warranted`.

### Reason

The cycle's only edit is a code-comment accuracy correction — internal-only, with
no consumer-visible behavior change, no public symbol change, and no typed-error
contract change. Per `AGENTS.md` #21 ("Do not update CHANGELOG.md unless explicitly
instructed") AND the active review plan's silence on changelog authorization for
this cycle (the dispatch prompt explicitly states CHANGELOG.md is not authorized
this cycle), no changelog entry is warranted.

### What was done

No `CHANGELOG.md` edit.

### Validation run

- `uv run ruff format .` — pass / no-changes.
- `uv run ruff check --fix .` — pass.

---

## Verification (Worker 3)

Consolidated single-spawn shape #4 cycle: one Low (stale/false comment near
`_VALID_OPERATIONS`), no logic change, so logic + comment + changelog verified in
one terminal pass.

### Logic verification outcome

- **Cycle diff is exactly the comment correction.** `git diff <baseline> -- sets.py`
  and `git diff HEAD -- sets.py` show a single hunk: the two-line comment above
  `_VALID_OPERATIONS` replaced by a five-line accurate comment (+5/-1). Owned-paths
  `--stat` (`django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md`)
  shows ONLY `sets.py`. No other source file touched by this cycle (the unrelated
  `optimizer/walker.py` / `utils/relations.py` maintainer edits per AGENTS.md #33
  are not in scope and not present in the owned-paths stat).
- **`_VALID_OPERATIONS` and its use sites byte-unchanged.** Baseline
  `a00cda16` shows def at `:89` (`frozenset({"create", "update", "delete"})`) and
  uses at `:381`/`:384`; live HEAD shows def at `:93` and uses at `:385`/`:388`
  (shifted only by the +4 comment lines) — identical text:
  `_validate_mutation_meta #"if operation not in _VALID_OPERATIONS"` membership
  test and the `sorted(_VALID_OPERATIONS)` error message. No behavior change.
- **Low (stale comment): ADDRESSED via route A.** Independently confirmed the NEW
  comment is accurate: `grep -rn _VALID_OPERATIONS django_strawberry_framework/`
  returns ONLY `sets.py` (def `:93`, uses `:385`/`:388`, plus the comment cite
  `:89`) — the constant single-sources only this module's membership check. The
  resolver dispatches on verb literals directly: `meta.operation == "create"`
  (resolvers.py:825), `== "update"` (:827), and single-verb positional args to
  `_authorize_or_raise(..., "create"/"update"/"delete", ...)` (:908/:946/:999);
  `grep` confirms resolvers.py has NO `from .sets import` of the constant and never
  references `_VALID_OPERATIONS`. The new comment states exactly this — accurate.
- **Route B correctly rejected.** `meta.operation == "create"` is equality dispatch
  against an individual literal and `_authorize_or_raise(..., "create", ...)` passes
  a single verb; a frozenset membership set cannot replace either, so importing
  `_VALID_OPERATIONS` resolver-side eliminates zero verb literals — route B is a
  forced fit, not real DRY. Worker 2's evidence is grep-discoverable and reconfirmed.
  The cross-module shared-verb-vocabulary factoring (a shared `OPERATIONS` tuple) is
  correctly deferred to the resolver/folder pass per artifact scoping (line 23); the
  verb→Django-codename map `permissions.py::_OPERATION_PERMISSION_ACTION` is a
  distinct concern correctly left as its own dict.

### DRY findings disposition

The DRY-analysis verb-literal-spread item is resolved by route A (comment now
describes the true single-source scope). The cross-module shared-verb-vocabulary
concern is **forwarded** to the `mutations/` folder pass and project pass
(rev-django_strawberry_framework.md) — out of scope for this single-file cycle.

### Temp test verification

- None used. Comment-only change with no behavior change; the runtime contract
  (`_validate_mutation_meta` membership check) is unchanged. No pinning test
  warranted — correct per the comment-only edit dictum.

### Comment verification

The new comment describes the final approved behavior, removes the false
cross-module claim ("Slice 3's resolver imports this"), keeps the accurate first
sentence, uses symbol-qualified refs per AGENTS.md #27 (no raw line numbers), and
stays within scope. Accurate and not stale.

### Changelog verification

`git diff -- CHANGELOG.md` is empty. Disposition is `Not warranted`, citing BOTH
AGENTS.md #21 and the plan/dispatch silence on changelog authorization. The
internal-only framing matches the diff scope (a code-comment correction, no
public-API/typed-error surface change). Correct state, both citations present.

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the
`mutations/sets.py` checklist box in `docs/review/review-0_0_11.md`.
