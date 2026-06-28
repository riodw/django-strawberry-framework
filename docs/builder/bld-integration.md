# Build: Cross-slice integration pass — serializer_mutations / 0.0.13 (039)

Spec reference: `docs/spec-039-serializer_mutations-0_0_13.md`
Build plan: `docs/builder/build-039-serializer_mutations-0_0_13.md`
Status: final-accepted

A consolidation loop IS warranted. The build is integration-clean on every axis except
ONE live cross-slice DRY finding (the `relation_field_error` / `"Invalid id for relation …"`
3-site near-copy), which — with the one-line L1 test cleanup that folds into the same loop —
is exactly the cross-flavor consolidation this pass exists for. Worker 0 should dispatch a
Worker 2 consolidation pass + Worker 3 review, then re-spawn Worker 1 to re-verify and set
`final-accepted`. Everything else verifies clean and needs no rework.

---

## Required pre-work (per BUILD.md "Cross-slice integration pass")

### 1. Prior `bld-slice-*.md` artifacts read in slice order

All five read end-to-end (slices 0→4), all `Status: final-accepted`:

- `bld-slice-0-drf_dependency_gate.md` — DRF dev-dep floor `>=3.17.0` (config-only; no package code).
- `bld-slice-1-serializer_converter_inputs.md` — `serializer_converter.py` + `inputs.py` + the
  four DRY promotions (P1.3 `make_shape_build_cache`, P1.4 `convert_with_mro`, P2.1
  `InputFieldSpec`, P2.2 `make_input_namespace`). Carries the L1 finding (below).
- `bld-slice-2-serializermutation_base.md` — `SerializerMutation` base, `Meta` validation,
  the `register_subsystem_clear` seam (P1.6), the root `__getattr__` export, plus P1.2 / P1.7 /
  P2.6 / P2.7 promotions. One pass-1 Medium (missing guard/waiver integration test) resolved
  test-only in pass 2; `final-accepted` on re-pass.
- `bld-slice-3-resolver_pipeline_live_surface.md` — `resolvers.py` sync/async pipeline +
  products live surface + P1.5 `run_write_pipeline_sync` / P1.1 `visible_related_object` / P2.4
  `field_error` promotions. Carries the `_relation_field_error` finding (below).
- `bld-slice-4-docs_card_wrap.md` — implemented-on-main docs + DB-backed KANBAN card move
  (DONE-039), no version bump. The spec Status header was reconciled to "IMPLEMENTED ON MAIN;
  release deferred to joint 0.0.13 cut" at its final-verification.

### 2. Static inspection helper coverage — CONFIRMED (refreshed this pass)

`scripts/review_inspect.py … --output-dir docs/shadow` was run this pass on every Python file
with review-worthy logic touched by the build (all OK):

`rest_framework/{serializer_converter,inputs,sets,resolvers}.py`, `utils/{converters,inputs,querysets}.py`,
`mutations/{sets,resolvers,inputs}.py`, `forms/{converter,inputs,sets,resolvers}.py`, `registry.py`,
`types/finalizer.py`, `__init__.py`. No file with review-worthy logic was skipped. (Slice 0 was
config-only — `pyproject.toml` + `uv.lock` — correctly no helper run, recorded in its artifact.
Slice 4 was a doc/DB-wrap — no Python logic — correctly skipped.)

### 3. Repeated string literals — cross-overview comparison

The per-file "Repeated string literals" sections were compared across all build-touched overviews.
**Within-file** repeats are all spec-meaningful and intentional: the per-flavor base label
(`DjangoMutation` / `DjangoFormMutation` / `SerializerMutation`) is deliberately per-flavor, and the
`operation` / `permission_classes` / `serializer_class` / `optional_fields` `Meta`-key names are
necessarily restated where each flavor validates them — these mirror the existing model/form pattern
and are NOT build-introduced cross-slice duplication.

The static inspector reports only within-file repeats, so the one genuine **cross-file** repeated
literal was found by direct grep: the relation-decode message `"Invalid id for relation {…!r}."`
appears LIVE in three modules (`forms/resolvers.py`, `rest_framework/resolvers.py`,
`mutations/resolvers.py`). This is finding F-INT-1 below.

### 4. Imports / dependency-direction — one-way boundary CONFIRMED

- `rest_framework/` modules import only from `..utils`, `..mutations`, `..types`, `..relay`,
  `..scalars`, `..exceptions`, `..registry` — and crucially **never from `..forms`** (it mirrors
  `forms/` module-for-module structurally but does not import it; both ride the promoted `utils/`
  helpers). Verified `serializer_converter.py` / `inputs.py` / `sets.py` / `resolvers.py` import
  lists.
- **Reverse-direction guard:** NO `utils/` / `mutations/` / `types/` / `forms/` / `registry.py`
  module imports from `rest_framework/`. The one `rest_framework` reference in `registry.py`
  (`:608`) is the **static string row** `"django_strawberry_framework.rest_framework.inputs"` in
  the `register_subsystem_clear` canonical list — a string, NOT an import (F10: registration never
  forces a DRF import). One-way direction holds.

### 5. Accepted-slice `What looks solid` / `DRY findings` / `Notes for Worker 1` walk

Two deferred follow-ups were explicitly routed to this pass (both confirmed at source below):
F-INT-1 (`_relation_field_error` 3-site near-copy, Slice-3 Worker-3 + Worker-1) and F-INT-2 (L1
vacuous assertion, Slice-1 Worker-3 + Worker-1). No other slice surfaced an unresolved DRY
follow-up; every spec-mandated P1.x/P2.x promotion was verified single-sited at its own slice's
final verification and re-verified here (DRY scan below).

### 6. Staged-anchor sweep (MANDATORY) — CLEAN

`grep -rEn 'TODO\(spec-039|TODO-(ALPHA|BETA|STABLE)-039' .` (+ the card-id form
`TODO-ALPHA-039-0.0.13`), excluding `KANBAN.md` / `KANBAN.html` / `BACKLOG.md` and the per-cycle
`docs/builder/` scratch + the active `docs/spec-039-*` files:

- **Package source / tests / examples / scripts: ZERO staged `TODO(spec-039 …)` or
  `TODO-…-039` anchors.** Every Slice-0..4 staged anchor was discharged in the slice that shipped
  its work (verified per-slice; re-confirmed here):
  `grep -rEn 'TODO\(spec-039|TODO-(ALPHA|BETA|STABLE)-039' django_strawberry_framework/ tests/ examples/ scripts/`
  → no matches. (`rest_framework/` carries no TODO/FIXME at all.)
- The only remaining matches tree-wide are **prose markdown link references** in the ARCHIVED
  predecessor specs `docs/SPECS/spec-036-mutations-0_0_11.md` and
  `docs/SPECS/spec-038-form_mutations-0_0_12.md` — `[`TODO-ALPHA-039-0.0.13`][kanban]`-style
  links naming the board card. These are NOT staged work-anchors in shipped source/tests/comments;
  they are historical-record cross-references to the kanban card-id, which legitimately still reads
  `TODO-ALPHA-039` in those archived docs (the card's RELEASE is deferred to the joint `0.0.13`
  cut, so its public board status flip is F8-deferred — Slice 4 moved the live DB card to
  `DONE-039` via the ORM, but does not rewrite already-archived sibling specs). Not a finding.

**Sweep result: CLEAN** (no undischarged staged anchor in any shipped source / test / comment).

---

## The integration checks (per BUILD.md)

### Export surface — CONFIRMED (no over-broad export)

- `django_strawberry_framework/__init__.py::__all__` is byte-unchanged from its documented
  pre-build set; `SerializerMutation` is **NOT** in `__all__` (F1). Verified live:
  `'SerializerMutation' in d.__all__` → `False`; `hasattr(d, 'SerializerMutation')` → `True`
  (resolvable by NAME through the root `__getattr__`).
- The ONLY public-surface change is the PEP-562 root `__getattr__` (`__init__.py:40-65`) routing
  `SerializerMutation` through `require_drf()`, non-memoizing. `import django_strawberry_framework`
  succeeds without DRF; `from … import *` stays DRF-free. This is the single net-new public surface
  the spec authorizes (Decision 12 / F1 / DoD 8). No other module gained or broadened an export.

### Duplicated helpers across slices — SINGLE-SITED (one finding: F-INT-1)

Every spec-mandated promotion is defined EXACTLY ONCE (grep-verified at source this pass):

| Helper | Single owning site |
| --- | --- |
| `convert_with_mro` (P1.4) | `utils/converters.py:28` |
| `InputFieldSpec` (P2.1) | `utils/inputs.py:54` |
| `make_input_namespace` (P2.2) | `utils/inputs.py:91` |
| `make_shape_build_cache` (P1.3) | `utils/inputs.py:144` |
| `NON_DELETE_WRITE_OPERATIONS` (P1.2) | `mutations/sets.py:112` |
| `reject_unknown_meta_keys` (P2.7) | `mutations/sets.py:134` |
| `_hook_overridden` (P2.6) | `mutations/sets.py:151` |
| `cached_build_input` (P1.7) | `mutations/sets.py:165` |
| `build_and_stash_input` (P1.7) | `mutations/sets.py:200` |
| `register_subsystem_clear` / `iter_subsystem_clears` (P1.6) | `registry.py:72` / `:88` |
| `run_write_pipeline_sync` (P1.5) | `mutations/resolvers.py:113` |
| `field_error` (P2.4) | `mutations/resolvers.py:843` |
| `visible_related_object` (P1.1) | `utils/querysets.py:208` |

Forked-copy guards all 0: no `_VALID_SERIALIZER_OPERATIONS`, `_VALID_FORM_OPERATIONS`,
`_cached_build_serializer_input`, `_build_and_stash_serializer_input`. `_serializer_shape_build_cache`
is the legitimate Slice-1 `make_shape_build_cache()` pair (`rest_framework/inputs.py:693`), not a
hand-rolled fork.

The ONE duplicated-helper finding is F-INT-1 (`relation_field_error`), below — and it is a
PRE-EXISTING two-site (forms + model) pattern at HEAD that Slice 3 extended to a third site
following the established shape, surfaced for cross-flavor consolidation exactly here.

### Inconsistent naming / error handling between slices — NONE

`rest_framework/` mirrors `forms/` method-for-method (`_resolve_model` / `_validate_meta` /
`build_input` / `input_type_name` / `input_module_path` / `resolve_sync` / `resolve_async`), uses
the same `ConfigurationError` raising discipline, the same `FieldError` envelope + `NON_FIELD_ERROR_KEY`
sentinel, and the same per-flavor base-label message shape via the shared
`non_delete_operation_error` builder. Error keying is consistent: relation errors key to the GraphQL
input name (F5), non-field errors normalize to `"__all__"` at every level via the shared sentinel.

### Repeated ORM/queryset patterns that should be centralized — NONE outstanding

The object-returning related-visibility pattern was the one ORM duplication risk; it is centralized
in `utils/querysets.py::visible_related_object` (P1.1), called by both the form and serializer
relation decoders. The model raw-pk path keeps its own `_raw_pk_relation_error` membership/visibility
body (a different signature/behavior — set membership vs single-object resolve), correctly NOT folded
(it is the message literal, not the queryset logic, that duplicates — see F-INT-1).

### Misplaced responsibilities between modules — NONE

Shared mechanics live in `utils/` (converter skeleton, input specs, namespaces, caches, querysets) and
`mutations/` (the write-pipeline skeleton, the meta-validation helpers, the leaf error ctor, the
clear-seam registration target in `registry.py`). `rest_framework/` holds only its genuinely-new
logic (the DRF-field converter, the serializer input descriptor, the serializer pipeline callbacks,
the recursive `serializer_errors_to_field_errors` flattener). The seam centerpiece
`register_subsystem_clear` correctly lives in `registry.py` with string rows (F10).

### Repeated string literals / dict keys / tuple shapes — one finding (F-INT-1)

See pre-work step 3. The only cross-file repeated executable literal introduced/extended by the build
is the relation-decode message (F-INT-1). Within-file Meta-key repeats are intentional per-flavor.

### Comments telling one coherent story — YES

The `rest_framework/` docstrings consistently cite the spec-036/038 precedents they reuse and the
spec-039 decisions they implement; the `register_subsystem_clear` seam comments (registry/finalizer)
tell one story about the string-row F10 design; the relocated/promoted helper bodies carry
provenance comments pointing at their form-local origins. No contradictory narrative surfaced.

---

## Findings

### F-INT-1 (consolidation item) — `relation_field_error` 3-site near-copy / `"Invalid id for relation …"` repeated literal

**A real, LIVE cross-flavor DRY finding worth a consolidation loop.** Confirmed at source this pass:

- `django_strawberry_framework/forms/resolvers.py::_relation_field_error` (`:128-138`) — body
  `return FieldError(field=graphql_name, messages=[f"Invalid id for relation {graphql_name!r}."])`
  (with a function-local `from ..mutations.inputs import FieldError`; return-typed `Any`). LIVE: 3
  call sites (`:192`, `:197`, `:201`).
- `django_strawberry_framework/rest_framework/resolvers.py::_relation_field_error` (`:151-159`) —
  **byte-identical executable body** (module-level `FieldError` import; return-typed `FieldError`).
  LIVE: 3 call sites (`:220`, `:225`, `:229`).
- `django_strawberry_framework/mutations/resolvers.py::_raw_pk_relation_error` (`:671`) — carries
  the **same message literal** `f"Invalid id for relation {field_name!r}."` (`:515`, inside the
  function's membership-error construction). LIVE: caller at `:465`. (This helper's surrounding
  body — set-membership / visibility resolution — is genuinely different and must NOT be folded;
  only the leaf `FieldError` + message construction duplicates.)

**Why it is a finding now (not before):** spec-036 froze it as a model-path helper, spec-038 added
the byte-identical forms copy; this build's Slice 3 added the third byte-identical
`rest_framework/` copy. The spec import manifest (line ~2892) promoted the leaf `field_error(path,
messages)` ctor (P2.4 — done) but did NOT list `_relation_field_error` for promotion, and the
consolidation spans the 036 model path, so each slice correctly deferred it to this cross-slice pass
(Slice-3 Worker-3 DRY finding + Slice-3 Worker-1 final-verification "Deferred work for the
integration pass", and Worker-1 memory carry-in #1). Confirmed LIVE (not dead code) per the
worker-1.md "grep the readers before recommending consolidation" rule: all three helpers have live
callers.

**Single-site target (recommended consolidation):** add a shared leaf ctor
`relation_field_error(graphql_name)` in `mutations/resolvers.py`, sited **beside the P2.4-promoted
`field_error`** (`mutations/resolvers.py:843`), returning
`FieldError(field=graphql_name, messages=[f"Invalid id for relation {graphql_name!r}."])` — so the
message text + leaf shape single-site once, exactly as P2.4 did for the generic leaf. Then re-point
all three flavors:

1. `forms/resolvers.py::_relation_field_error` → either delete the local helper and call the shared
   `relation_field_error` directly at its 3 call sites, OR make it a one-line re-export that
   delegates (prefer delete-and-call-direct unless the local name aids readability — Worker 2's call;
   the form suite must stay byte-equivalent — the rendered message is identical).
2. `rest_framework/resolvers.py::_relation_field_error` → same re-point (delete-and-call-direct or
   thin delegate); the serializer relation-decode behavior + message are unchanged.
3. `mutations/resolvers.py::_raw_pk_relation_error` → build its `FieldError` via the shared
   `relation_field_error(field_name)` so the message literal is no longer re-spelled there. The
   surrounding membership/visibility logic stays put.

**Acceptance for the loop:** the message text exists in exactly ONE place; `grep -rn "Invalid id for
relation" django_strawberry_framework/` returns a single executable-literal site (the shared ctor)
plus only docstring/comment mentions; the `036` model + `038` form + `039` serializer resolver suites
(`tests/mutations/`, `tests/forms/`, `tests/rest_framework/`, the live `test_products_api.py`) all
stay green UNCHANGED (byte-equivalence proof). No new public export. This is exactly the cross-flavor
single-siting the integration pass is for.

### F-INT-2 (consolidation item, folds into the same loop) — L1 vacuous-tautology test assertion

`tests/rest_framework/test_inputs.py:620` (`::test_allow_null_field_is_nullable_even_when_required`)
reads:

```python
assert field.default is UNSET.__class__() or field.default is not UNSET
```

`UNSET` is a singleton, so `UNSET.__class__() is UNSET` is True, and the line reduces to
`(field.default is UNSET) or (field.default is not UNSET)` — a tautology that passes for ANY value
and pins NOTHING. Confirmed at source this pass (Slice-1 Worker-3 L1 + Slice-1/Slice-3 Worker-1
carry-ins). **Not a coverage gap:** the load-bearing M2 contract (a `required=True, allow_null=True`
field is nullable WITHOUT an UNSET default, so it must be provided) is already pinned by line 619
(`assert _is_optional(field)`) and line 622 (`assert field.default is not UNSET`). The fix is a
one-line cleanup: delete line 620 (619+622 already pin the contract) or rewrite it to assert the
actual `field.default` identity. Folds into the F-INT-1 consolidation loop at zero marginal cost
(both touch the resolver/test surface; Worker 2's same pass can do both, Worker 3 reviews both).

### No other findings

No High/Medium DRY, naming, error-handling, responsibility, export, or comment-coherence finding.
The build is integration-clean apart from F-INT-1 + F-INT-2.

---

## Deferred-work catalog seeds (for `bld-final.md` `### Deferred work catalog`)

These are NOT integration findings to fix in this build — they are catalog entries for the next
spec author / the joint cut. Recorded here so `bld-final.md` can build its catalog from this ledger:

1. **Licensed joint-cut docs deferral (F8 / Decision 14).** The package version bump `0.0.12 →
   0.0.13`, the GLOSSARY `shipped (0.0.13)` status flip (Slice 4 set `status_text="implemented on
   main, releasing in \`0.0.13\`"` with the FK kept `planned`), the `README.md` / `docs/README.md`
   "Coming next" → "Shipped today" move (README Status → `0.0.13`), and the `CHANGELOG.md` release
   bullets are ALL deferred to the joint `0.0.13` cut shared with `WIP-ALPHA-040-0.0.13`. The card
   `CHANGELOG.md` edit additionally requires an explicit maintainer prompt (`AGENTS.md` "Do not
   update CHANGELOG.md unless explicitly instructed"). Source: Slice-0..4 build-plan flags + Slice-4
   final verification.
2. **Out-of-scope board-hygiene note (`planning_state` on done cards).** A `planning_state="In
   progress"` residue on done cards (DONE-038 precedent) was observed out-of-scope by Slice-4
   final verification; not this build's to fix. Catalog only.

(F-INT-1 and F-INT-2 above are NOT deferred — they are this build's consolidation loop, to land
before `bld-final.md`. If for any reason the loop is declined by the maintainer, they convert to
catalog entries; otherwise they are discharged in-build.)

---

## Verdict

`Status: revision-needed`. One consolidation loop:

- **F-INT-1** — promote a shared `relation_field_error(graphql_name)` leaf ctor in
  `mutations/resolvers.py` (beside `field_error`); re-point `forms/resolvers.py::_relation_field_error`,
  `rest_framework/resolvers.py::_relation_field_error`, and
  `mutations/resolvers.py::_raw_pk_relation_error`'s message construction; prove the model/form/
  serializer suites stay byte-equivalent.
- **F-INT-2** — fix the one-line vacuous assertion at `tests/rest_framework/test_inputs.py:620`
  (delete it or rewrite to assert the real `field.default` identity), folded into the same loop.

Worker 0: dispatch Worker 2 (consolidation) + Worker 3 (review), then re-spawn Worker 1 to re-run
this integration pass and set `final-accepted`. Everything else (staged-anchor sweep, export surface,
single-sited promotions, one-way imports, comment coherence) is verified clean and needs no rework.

---

## Build report (Worker 2)

Consolidation pass discharging F-INT-1 + F-INT-2 exactly as scoped. No anchors discharged, no
version bump, no scope broadening.

### Files touched

Grounded in `git status --short` (the tree carries Slice 0–4's accepted-but-uncommitted work; my
consolidation diff is confined to these four files):

- `django_strawberry_framework/mutations/resolvers.py` — **F-INT-1 single-site.** Added the shared
  leaf ctor `relation_field_error(graphql_name) -> FieldError` (`:864`), sited immediately after the
  P2.4-promoted `field_error` (`:843`), returning
  `FieldError(field=graphql_name, messages=[f"Invalid id for relation {graphql_name!r}."])` — the
  single home for the message text + leaf shape. Re-pointed the model-path leaf ctor
  `_relation_error` (`:511`) to `return relation_field_error(field_name)` (kept the local name +
  its 2 call sites `:457`/`:561` and the transitive `_raw_pk_relation_error` path untouched).
- `django_strawberry_framework/forms/resolvers.py` — **F-INT-1 re-point.** `_relation_field_error`
  (`:128`) now `return relation_field_error(graphql_name)`; removed the function-local
  `from ..mutations.inputs import FieldError` (no other executable `FieldError(` use remained in the
  file) and added `relation_field_error` to the existing `..mutations.resolvers` import block (`:107`).
  Kept the local `_relation_field_error` name + its 3 call sites (`:192`/`:197`/`:201`).
- `django_strawberry_framework/rest_framework/resolvers.py` — **F-INT-1 re-point.**
  `_relation_field_error` (`:151`) now `return relation_field_error(graphql_name)`; added
  `relation_field_error` to the existing `..mutations.resolvers` import block (`:122`). The
  module-level `FieldError` import stays (22 annotation/docstring references). Kept the local name +
  its 3 call sites (`:220`/`:225`/`:229`).
- `tests/rest_framework/test_inputs.py` — **F-INT-2.** Deleted the vacuous-tautology line
  (`assert field.default is UNSET.__class__() or field.default is not UNSET`) in
  `test_allow_null_field_is_nullable_even_when_required`. The real M2 contract stays pinned by the
  adjacent `assert _is_optional(field)` and `assert field.default is not UNSET`; the explanatory
  comment was kept. `UNSET` is still referenced 11× elsewhere, so the import is untouched.

### Tests added or updated

No tests added. One vacuous assertion deleted (F-INT-2). No production-behavior test was changed —
the model/form/serializer suites staying green UNCHANGED is the byte-equivalence proof for the
re-point.

### Spec slice checklist (verbatim)

This integration artifact carries no `### Spec slice checklist (verbatim)` section (it is the
cross-slice consolidation artifact, not a slice). Nothing to tick.

### Validation run

- `uv run ruff format .` — **PASS** (295 files left unchanged; the COM812-vs-formatter warning is a
  pre-existing config note, not a change).
- `uv run ruff check --fix .` — **PASS** ("All checks passed!"; no autofix churn).
- `git status --short` after both ruff runs — my consolidation diff is confined to the four files
  above; no tool churn introduced, nothing reverted. Did NOT touch `docs/feedback.md`,
  `examples/fakeshop/db.sqlite3`, or any file outside scope (those entries pre-date this pass —
  Slice 0–4's accepted work).
- Acceptance gate: `grep -rn "Invalid id for relation {" django_strawberry_framework/` → **one**
  executable-literal site (`mutations/resolvers.py:877`, inside the shared ctor). The other three
  `"Invalid id for relation"` matches tree-wide are docstring/comment mentions only.
- **Focused tests (no `--cov`):**
  `uv run pytest tests/mutations tests/forms tests/rest_framework examples/fakeshop/test_query/test_products_api.py --no-cov`
  → **545 passed** in ~105s. The model + form + serializer suites all green with no production-test
  edit = the byte-equivalence proof for all three re-points.

### Implementation notes

- **Model re-point target is `_relation_error`, not `_raw_pk_relation_error`** (small spec
  reconciliation — see Notes for Worker 1). The artifact named `_raw_pk_relation_error` as the model
  re-spelling site, but grep showed the executable message literal lives in the model-path leaf ctor
  `_relation_error` (`:511`, the `FieldError(...messages=[f"Invalid id for relation …"])` body);
  `_raw_pk_relation_error` reaches it transitively via `_relation_membership_error → _relation_error`
  and never re-spells the literal itself. Re-pointing `_relation_error` is the correct, minimal
  single-siting: it covers BOTH of `_relation_error`'s direct callers (`:457` wrong-type, `:561`
  membership) AND the `_raw_pk_relation_error` path, with the surrounding membership/visibility logic
  untouched. Outcome is identical to the artifact's intent (one message site) and the model suite is
  byte-equivalent.
- **Kept the per-flavor local `_relation_field_error` / `_relation_error` names as thin delegates**
  rather than deleting them and calling `relation_field_error` directly at the 6 call sites. The
  artifact left this to Worker 2's call ("delete-and-call-direct OR thin delegate"). The local names
  carry flavor-specific provenance docstrings (the form/serializer AR-H4 / 036-038 contract notes,
  the model wrong/hidden/missing collapse) that read better at the decode call sites than a bare
  cross-module call, and a thin delegate keeps each flavor's 3 call sites untouched — so the diff is
  minimal and the per-flavor narrative survives. All three docstrings were updated to state they are
  aliases of the single-sourced shared ctor.
- **Forward reference is fine.** `_relation_error` (`:511`) calls `relation_field_error` (defined
  later at `:864`); both are module-level functions resolved at call time, well after import, so the
  ordering does not matter.

### Notes for Worker 3

- No `scripts/review_inspect.py` shadow file was used for this pass — the four edits are
  small, mechanically-obvious delegations + one test-line deletion, evaluable from the diff alone.
- The byte-equivalence proof is the 545-test focused run (model + form + serializer suites green with
  zero production-test edits). The only test change is the F-INT-2 vacuous-line deletion.
- Acceptance to re-confirm: `grep -rn "Invalid id for relation {" django_strawberry_framework/`
  returns exactly one executable site (`mutations/resolvers.py:877`).

### Notes for Worker 1 (spec reconciliation)

- **F-INT-1 model re-point site differs from the artifact's prose (mechanically-obvious, in-contract
  drift).** The artifact (F-INT-1 / Verdict) named `mutations/resolvers.py::_raw_pk_relation_error`
  as the model site that "re-spells the same message" and asked to re-point "its message
  construction." In fact the message literal is NOT in `_raw_pk_relation_error`'s body — it lives in
  the model-path leaf ctor `_relation_error` (`:511`), which `_raw_pk_relation_error` reaches
  transitively through `_relation_membership_error → _relation_error`. I re-pointed `_relation_error`
  (the actual literal site), which single-sites the message for the entire model path including the
  `_raw_pk_relation_error` flow, with `_raw_pk_relation_error`'s membership/visibility body untouched.
  This is the smaller, more faithful change and the artifact's acceptance gate (one message site,
  byte-equivalent model suite) is met. Flagging for your final-verification audit — the outcome
  matches the artifact's intent exactly; only the named function moved by one delegation hop.
- No other drift. F-INT-2 was deletion exactly as the artifact expected (619+622 already pin the
  contract).

---

## Review (Worker 3)

Narrow review of the consolidation diff (the 4 files the loop touched). Slice 0–4's
accepted-but-uncommitted work in the working tree is out of scope; `docs/feedback.md` and
`db.sqlite3` ignored per dispatch.

### High:

None.

### Medium:

None.

### Low:

None.

### F-INT-1 single-siting — CONFIRMED (one executable message site)

`grep -rn "Invalid id for relation" django_strawberry_framework/` returns exactly FOUR matches,
exactly ONE of which is executable:

- `mutations/resolvers.py:877` — the ONE executable site, inside the shared leaf ctor
  `relation_field_error(graphql_name)` (`:864`), sited immediately after the P2.4 `field_error`
  ctor (`:846`). Body: `return FieldError(field=graphql_name, messages=[f"Invalid id for relation {graphql_name!r}."])`.
- `mutations/resolvers.py:517` and `:874` — docstring mentions (the `_relation_error` and
  `relation_field_error` docstrings).
- `forms/resolvers.py:184` — a docstring/comment mention only (a `_to_form_key_value`-area note),
  not executable.

`grep -rn "def relation_field_error" django_strawberry_framework/` → defined exactly once
(`mutations/resolvers.py:864`). The 3 flavors re-point onto it as minimal thin delegates, call sites
and per-flavor docstrings preserved:

- `forms/resolvers.py::_relation_field_error` (`:129`) → `return relation_field_error(graphql_name)`;
  `relation_field_error` added to the `..mutations.resolvers` import block (`:107`); the prior
  function-local `from ..mutations.inputs import FieldError` removed. 3 call sites unchanged.
- `rest_framework/resolvers.py::_relation_field_error` (`:152`) →
  `return relation_field_error(graphql_name)`; import added (`:122`); module-level `FieldError`
  import retained (used in annotations). 3 call sites unchanged.
- `mutations/resolvers.py::_relation_error` (`:511`) → `return relation_field_error(field_name)`
  (the model-path delegate).

### Worker 2's in-contract correction (`_relation_error`, not `_raw_pk_relation_error`) — VERIFIED CORRECT AND COMPLETE

The artifact named `_raw_pk_relation_error` as the model re-spelling site. Worker 2 found the
executable literal actually lives in the model-path leaf ctor `_relation_error` and re-pointed that
instead. Verified by tracing the call chain in `mutations/resolvers.py`:

- `_raw_pk_relation_error` (`:674`) ends `return _relation_membership_error(...)` (`:734`) — its
  membership/visibility body does NOT re-spell the literal.
- `_relation_membership_error` (`:537`) returns `_relation_error(field_name)` (`:564`) on a missing
  member.
- `_relation_error` (`:519`) → `relation_field_error(field_name)` → the shared ctor.

So the entire model path — including the raw-pk flow (`_raw_pk_relation_error` →
`_relation_membership_error` → `_relation_error`) AND `_relation_error`'s direct callers (`:457`
wrong-type, `:461` via `_relation_visibility_error → _relation_membership_error`) — now routes
through the shared ctor. `_raw_pk_relation_error`'s membership/visibility body is untouched
(confirmed: neither `_raw_pk_relation_error` nor `_relation_membership_error` appears as a changed
`+`/`-` line in the working-tree diff for `mutations/resolvers.py`). This is the correct, complete,
minimal single-siting; no caller's semantics changed. Worker 2's choice is the smaller and more
faithful change and the artifact's acceptance gate is met. No finding.

### Byte-equivalence — CONFIRMED GREEN

`uv run pytest tests/mutations tests/forms tests/rest_framework examples/fakeshop/test_query/test_products_api.py --no-cov`
→ **545 passed** in 105s (matches Worker 2's report). The model + form + serializer suites stay green
with zero production-test edits (the only test change is the F-INT-2 deletion), which IS the
behavior-preserving proof for all three re-points.

### F-INT-2 (L1 vacuous tautology) — CONFIRMED, no coverage lost

`tests/rest_framework/test_inputs.py::test_allow_null_field_is_nullable_even_when_required` (`:611`):
the vacuous `assert field.default is UNSET.__class__() or field.default is not UNSET` line was
deleted. The adjacent assertions still pin the real M2 contract:

- `:619` `assert _is_optional(field)` — the annotation is `T | None` (nullable from `allow_null`).
- `:621` `assert field.default is not UNSET` — required: no UNSET default fabricated, so it must be
  provided.

Non-vacuity of the survivor verified: `utils/inputs.py` (`#"a required field gets NO class default"`,
`:265`-`:287`) shows a required field gets no class default (so `.default is not UNSET`), while the
companion `test_field_with_default_is_optional_no_fabricated_default` (`:624`) asserts the inverse
(`field.default is UNSET` for `required=False`). The two are distinguishing; the M2 contract stays
pinned. No real coverage lost. The explanatory comment was kept.

### DRY findings

No NEW duplication. The relation-decode message literal + leaf `FieldError` construction is now
single-sourced in `relation_field_error` (`mutations/resolvers.py:864`), co-located with the P2.4
`field_error` generic-leaf ctor. The three per-flavor local names (`_relation_field_error` ×2 +
`_relation_error`) survive as one-line thin aliases — Worker 2's discretionary choice, explicitly
authorized by the artifact ("delete-and-call-direct OR thin delegate"). Acceptable: each alias
carries flavor-specific provenance docstrings (036/038/039 contract notes) that read better at the
decode call sites than a bare cross-module call, all 6 call sites stay untouched, and the diff is
minimal. The delegates own no logic beyond the single delegating return.

### Static inspection helper

Skipped, with reason recorded. The consolidation adds < 30 lines of new executable logic to any
`django_strawberry_framework/` file: `mutations/resolvers.py` gains one shared ctor (a single
`return` statement) plus a one-line delegation in `_relation_error`; `forms/` and `rest_framework/`
each gain a one-line delegation + an import edit; the test file is a one-line deletion. BUILD.md
requires the helper at ≥30 lines of new logic — far under threshold, so a reasoned skip per BUILD.md
"Static inspection helper" judgment clause. (Coverage of every build-touched logic file was already
confirmed in this artifact's pre-work step 2.)

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py`: the only diff present is the Slice-2 PEP-562
`__getattr__` (a TODO-comment → implementation swap), which is accepted Slice-2 work, NOT the
consolidation — the consolidation's 4-file scope excludes `__init__.py`. The `__all__` tuple is
byte-unchanged (grep for added/removed quoted members → zero); `SerializerMutation` remains absent
from `__all__`. The consolidation introduced no public-surface change. Confirmed.

### CHANGELOG sanity

Not applicable; consolidation did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; consolidation did not modify docs/release/KANBAN/archive surfaces.

### What looks solid

- Single executable message site achieved; the model raw-pk path correctly routes through the shared
  ctor transitively without folding the genuinely-different membership/visibility body.
- Byte-equivalence proven by 545 green tests with zero production-test edits.
- Delegates are minimal and the per-flavor narrative survives in docstrings.
- `relation_field_error` correctly sited beside `field_error` so both leaf ctors are co-located.

### Temp test verification

No temp tests created. The 545-test focused run was the byte-equivalence proof; no review suspicion
required isolating a behavior.

### Notes for Worker 1 (spec reconciliation)

- Worker 2's in-contract correction (model re-point at `_relation_error`, not `_raw_pk_relation_error`)
  is verified correct, complete, and byte-equivalent — recorded above for your final-verification
  audit. The outcome matches the artifact's intent exactly; only the named function moved by one
  delegation hop. No spec edit implied.

### Review outcome

`review-accepted`. The consolidation single-sites the relation-decode message to exactly one
executable site, re-points all three flavors as minimal byte-equivalent delegates (545 tests green,
zero production-test edits), correctly routes the model raw-pk path through the shared ctor via
Worker 2's verified `_relation_error` correction, deletes the F-INT-2 vacuous tautology without
losing coverage, introduces no new duplication, and leaves the public surface unchanged. No
High/Medium/Low findings.

---

## Integration re-verification (Worker 1)

Narrow re-verification of the consolidation loop (Worker 2 applied, Worker 3 set `review-accepted`).
Confirms F-INT-1 + F-INT-2 are closed, re-runs the byte-equivalence proof, re-confirms the
staged-anchor sweep, and finalizes the deferred-work catalog. No source/test edits by me; no spec
edit needed (status header already accurate — see below).

### Spec status-line re-verification — accurate, no edit

`docs/spec-039-…md:3-4` reads "Implemented on main; release deferred to the joint `0.0.13` cut
(card `DONE-039-0.0.13`)" — reconciled by Slice 4's final verification and still accurate to the
current state. No status-line edit required this pass.

### F-INT-1 (relation-decode message single-siting) — CLOSED

`grep -rn "Invalid id for relation" django_strawberry_framework/` → FOUR matches, **exactly ONE
executable**:

- `mutations/resolvers.py:877` — the ONE executable literal, inside the shared leaf ctor
  `relation_field_error(graphql_name)` (`:864`), sited immediately after the P2.4 `field_error` ctor:
  `return FieldError(field=graphql_name, messages=[f"Invalid id for relation {graphql_name!r}."])`.
- `mutations/resolvers.py:517`, `:874`, `forms/resolvers.py:184` — docstring/comment mentions only.

`grep -rn "def relation_field_error" django_strawberry_framework/` → defined exactly once
(`mutations/resolvers.py:864`). The three flavors are thin one-line delegates onto it, call sites and
per-flavor provenance docstrings preserved (verified by reading each body):

- `forms/resolvers.py::_relation_field_error` (`:129`) → `return relation_field_error(graphql_name)`;
  `relation_field_error` imported from `..mutations.resolvers` (`:107`); 3 call sites unchanged
  (`:193`/`:198`/`:202`).
- `rest_framework/resolvers.py::_relation_field_error` (`:152`) → `return relation_field_error(graphql_name)`;
  import added (`:122`); module-level `FieldError` import retained (annotations); 3 call sites unchanged
  (`:223`/`:228`/`:232`).
- `mutations/resolvers.py::_relation_error` (`:511`) → `return relation_field_error(field_name)` (the
  model-path delegate).

**Worker 2's correction (`_relation_error`, not `_raw_pk_relation_error`) — VERIFIED to fully
single-site the model path including the raw-pk flow.** Traced the call chain at source: every model
relation-error route terminates at `_relation_error` → `relation_field_error`, and no intervening body
re-spells the literal:

- direct wrong-type: `:457` → `_relation_error(field_name)`.
- raw-pk flow: `:465` → `_raw_pk_relation_error` (`:674`, body returns `_relation_membership_error`,
  no literal) → `_relation_membership_error` (`:537`, `:564` returns `_relation_error`).
- existence: `_relation_existence_error` (`:637`) → `_relation_membership_error` → `_relation_error`.
- visibility: `_relation_visibility_error` (`:568`) → `_relation_membership_error` → `_relation_error`.

So `_raw_pk_relation_error`'s membership/visibility body is genuinely-different and correctly NOT
folded; only the leaf message is single-sourced. F-INT-1 is RESOLVED.

### F-INT-2 (L1 vacuous tautology) — CLOSED, no coverage lost

`grep -n "UNSET.__class__()" tests/rest_framework/test_inputs.py` → no match (the line
`assert field.default is UNSET.__class__() or field.default is not UNSET` is deleted). The real M2
contract is still pinned by the adjacent survivors in
`test_allow_null_field_is_nullable_even_when_required`:

- `:619` `assert _is_optional(field)` — nullable via `allow_null` (annotation `T | None`).
- `:621` `assert field.default is not UNSET` — `required=True` fabricates no UNSET default, so it must
  be provided.

Non-vacuity confirmed against the companion `:632`/`:634` (`required=False` → `field.default is UNSET`),
which asserts the inverse — the two are distinguishing. F-INT-2 is RESOLVED.

### Byte-equivalence — CONFIRMED GREEN

`uv run pytest tests/mutations tests/forms tests/rest_framework examples/fakeshop/test_query/test_products_api.py --no-cov`
→ **545 passed in 105.94s** (matches Worker 2 + Worker 3). Model + form + serializer suites green with
zero production-test edits (the only test change is the F-INT-2 deletion) — the behavior-preserving
proof for all three re-points.

### Staged-anchor sweep (post-consolidation) — STILL CLEAN

`grep -rEn 'TODO\(spec-039|TODO-(ALPHA|BETA|STABLE)-039' django_strawberry_framework/ tests/ examples/ scripts/`
→ **ZERO matches**. No staged anchor in any shipped source / test / example / script. The only
tree-wide hits remain prose markdown link-references in the archived predecessor specs
(`docs/SPECS/spec-036|038`) naming the board card-id and the per-cycle `docs/builder/` scratch +
active `docs/spec-039-*` files — not staged work-anchors. The consolidation introduced no new anchor.

### Public-surface — UNCHANGED

The consolidation's 4-file scope excludes `__init__.py`; `SerializerMutation` remains absent from
`__all__` and resolvable only via the root `__getattr__` (per the integration-pass body above). No
export drift this loop.

### Finalized deferred-work catalog (for `bld-final.md` `### Deferred work catalog`)

These are NOT this build's to fix — catalog entries for the next spec author / the joint cut:

1. **Licensed joint-cut docs deferral (F8 / Decision 14).** The package version bump `0.0.12 →
   0.0.13`; the GLOSSARY `shipped (0.0.13)` status flip (Slice 4 set `status_text="implemented on
   main, releasing in \`0.0.13\`"` with the FK kept `planned`); the `README.md` / `docs/README.md`
   "Coming next" → "Shipped today" move (README Status → `0.0.13`); and the `CHANGELOG.md` release
   bullets are ALL deferred to the joint `0.0.13` cut shared with `WIP-ALPHA-040-0.0.13`. The
   `CHANGELOG.md` edit additionally requires explicit maintainer authorization (`AGENTS.md` "Do not
   update CHANGELOG.md unless explicitly instructed"). Source: Slice-0..4 build-plan flags + Slice-4
   final verification + the deferred-work seeds above.
2. **Out-of-scope board-hygiene note (`planning_state` on done cards).** A `planning_state="In
   progress"` residue on done cards (DONE-038 precedent) was observed out-of-scope by Slice-4 final
   verification; not this build's to fix. Catalog only.

### Resolved this pass (moved out of the deferred catalog)

- **F-INT-1** — RESOLVED. Shared `relation_field_error(graphql_name)` leaf ctor single-sites the
  relation-decode message + leaf shape (`mutations/resolvers.py:864`); all three flavors re-point as
  byte-equivalent delegates; the model raw-pk path routes through it transitively via the verified
  `_relation_error` correction. One executable message site; 545 tests green with zero production-test
  edits.
- **F-INT-2** — RESOLVED. The vacuous tautology at `tests/rest_framework/test_inputs.py` is deleted;
  the M2 contract stays pinned by the two adjacent survivors. No coverage lost.

### Summary

The consolidation loop closed both findings exactly as scoped, byte-equivalently. F-INT-1: one
executable relation-decode message site (`mutations/resolvers.py:877`), three thin delegates, the
model raw-pk flow correctly routed through the shared ctor via Worker 2's in-contract `_relation_error`
correction (membership/visibility body untouched). F-INT-2: vacuous line deleted, contract still
pinned. Byte-equivalence: 545 passed, zero production-test edits. Staged-anchor sweep: still CLEAN
(zero in shipped trees). Public surface: unchanged. Spec status header: accurate, no edit. Two
catalog entries handed to `bld-final.md` (licensed joint-cut docs deferral; out-of-scope board
hygiene); F-INT-1 + F-INT-2 moved to "resolved this pass". `Status: final-accepted`. The
integration pass is closed.
