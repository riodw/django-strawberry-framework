# Build: Cross-slice integration pass — auth_mutations / 0.0.13 (040)

Spec reference: `docs/spec-040-auth_mutations-0_0_13.md`
Build plan: `docs/builder/build-040-auth_mutations-0_0_13.md`
Status: **final-accepted** (Worker 1 final integration verification: the three consolidation carry-forwards are genuinely discharged in the working-tree diff, the DRY scan remains clean, the public surface is unchanged, and the focused regression suites are green. Worker 0 may now mark the integration checklist box `- [x]` and dispatch the final test-run gate `bld-final.md`).

All three in-spec slices are `final-accepted` (`build-040-…` checklist boxes 1-3 are `- [x]`). This pass runs the six BUILD.md pre-steps, the integration checks, and the tree-wide staged-anchor sweep, then catalogs the three carry-forwards the per-slice final verifications routed here as concrete Worker-2 consolidation work items.

---

## Pre-step results (BUILD.md "Cross-slice integration pass" 1-6)

### Pre-step 1 — read every prior `bld-slice-*.md` in slice order

Read all three in full, walking each artifact's `### What looks solid` / `### DRY findings` / `### Notes for Worker 1` for deferred follow-ups:

- `docs/builder/bld-slice-1-auth_substrate_login_logout.md` (`final-accepted`) — login/logout substrate, the surface-keyed declaration ledger + `bind_auth_mutations()` phase-2.5 wiring, `LoginPayload`/`LogoutPayload` materialization, the `TypeRegistry.clear()` declaration-clear hand row, the fakeshop `accounts` live surface. Deferred follow-ups it recorded: (a) the unused `_build_auth_field(permission_holder=...)` param (Worker-3 Low, routed to this pass); (b) the `resolvers.py` `run_pipeline_async` `TODO(spec-040 Slice 1)` generic-boundary anchor deliberately kept undischarged (auth-local was the plan's P3 safe default; spec Decision 10 P3 "may"), routed to this pass.
- `docs/builder/bld-slice-2-register_current_user.md` (`final-accepted`) — the `Register` rider, `current_user`, the reusable `excluded_input_fields` exclusion seam, the fakeshop `register`/`me` surface. Pass-1 Worker-3 flagged a Medium-tier DRY duplication (`_declare_surface` / `_declare_register_surface` byte-duplicate the normalize+dedupe+conflict branch); **pass 2 CONSOLIDATED it** into the shared `_lookup_or_conflict` primitive (Worker-3 pass-2 `review-accepted`, Worker-1 final verification confirmed sound — 2 callers, conflict message single-sited, login/logout ledger behavior unperturbed). No residual duplication remains from this finding. It re-confirmed the two Slice-1 carry-forwards still open.
- `docs/builder/bld-slice-3-docs_version_cut_wrap.md` (`final-accepted`) — docs + the `0.0.13` version cut + DB card wrap. Worker-3 raised **M1** (stale staging docstrings render into `docs/TREE.md`); Worker-1 final verification adjudicated M1 = defer to THIS integration pass (out-of-scope Slice-1/2 source, TREE is generated, cannot fix in-scope). It re-confirmed the two prior Slice-1 carry-forwards. It also verified the four DB-backed docs are byte-stable renders and `import_spec_terms --check` is OK for all 40 done cards.

### Pre-step 2 — static inspection helper coverage

`scripts/review_inspect.py … --output-dir docs/shadow` was run/refreshed this pass for every Python file the build touched that carries review-worthy logic:

- `django_strawberry_framework/auth/mutations.py` — refreshed this pass (new logic module, ~500 lines).
- `django_strawberry_framework/auth/queries.py` — refreshed this pass.
- `django_strawberry_framework/mutations/resolvers.py` — refreshed this pass (the exclusion-seam edit).
- `django_strawberry_framework/mutations/inputs.py` / `django_strawberry_framework/types/finalizer.py` — refreshed (payload builder / phase-2.5 bind slot).
- `django_strawberry_framework/mutations/fields.py` (the `attach_synthesized_signature` promotion) — Worker-3 ran the helper during Slice 1; the promotion is behavior-preserving (SDL byte-identical, 176 `tests/mutations/` green), so no refresh added signal here.
- `django_strawberry_framework/registry.py` — the auth clear row is a single `_clear_if_importable(...)` string-based hand row (no logic); Slice-1 review covered it. No re-run needed.
- Slice 3 touched no package `.py` logic beyond a one-line `__version__` string edit and a one-item `FAKESHOP_APP_NAMES` tuple addition to `scripts/build_tree_md.py` — the helper was correctly **skipped** for Slice 3 (recorded in that slice's plan, BUILD.md threshold not met). No review-worthy-logic file was left un-inspected.

### Pre-step 3 — cross-slice Repeated-string-literals comparison

Compared the **Repeated string literals** sections across every shadow overview. **No cross-slice DRY candidate.** A literal shared by 2+ files would flag; none of the auth literals appears outside its owning file:

- `auth/mutations.py` repeated literals: `2x "AuthMutation"`, `2x "password"`, `2x "Auth mutations"`, `2x "username"`. All **intra-file** and already adjudicated non-duplication in the Slice-1 review: `"AuthMutation"` = the `_AUTH_FAMILY_LABEL` constant definition vs a human-readable error-message prefix; `"username"` = the gate-`data` key (spec-pinned) vs the GraphQL arg parameter name (semantically distinct — coupling them would over-abstract); `"password"` = the `_PASSWORD` constant usage vs field-name prose; `"Auth mutations"` = the login-arm bind message prefix. `"RegisterInput"` is no longer a repeated literal — Slice-2 pass-2 named it once as `_REGISTER_INPUT` (L2 fix).
- `auth/queries.py`: **None.**
- `mutations/resolvers.py`: `2x "many_to_many"` — pre-existing package internal, unrelated to auth.
- `mutations/inputs.py`: **None.**
- `types/finalizer.py`: the `<unresolved>` / `connection` / `FilterSet` / `OrderSet` / bind-error-message fragments are all **pre-existing** finalizer internals (filters/orders binding), untouched by this build.

No auth literal (`AuthMutation`, `password`, `username`, `Auth mutations`, `RegisterInput`, `CurrentUserAlias`) appears in any other slice's file. **No consolidation warranted.**

### Pre-step 4 — cross-slice Imports comparison (one-way dependency direction)

Compared the **Imports** sections; confirmed a strictly one-way boundary. The auth module depends on `mutations/` + `utils/` + `registry` + `exceptions` — never the reverse:

- `auth/mutations.py` imports (all lower-level): `..exceptions::ConfigurationError`; `..mutations.fields::{DjangoMutationField, _lazy_ref, attach_synthesized_signature}`; `..mutations.inputs::{INPUTS_MODULE_PATH, build_mutation_input, build_payload_type, materialize_mutation_input_class, payload_object_slot}`; `..mutations.resolvers::{_model_decode_step, _model_write_step, authorize_or_raise, field_error, make_resolver_entries, run_write_pipeline_sync}`; `..mutations.sets::{DjangoMutation, _validate_permission_classes, make_declaration_registry, register_mutation as register_model_mutation}`; `..registry::registry`; `..utils.permissions::request_from_info`; plus a **function-local** `from .queries import materialize_current_user_alias` (inside the bind — cycle-safe intra-package sibling call).
- `auth/queries.py` imports: `..mutations.fields::_lazy_ref`; `..registry::register_subsystem_clear`; `..utils.inputs::make_input_namespace`; plus a **function-local** `from .mutations import {_AUTH_FAMILY_LABEL, _CURRENT_USER, _build_auth_field, _declare_surface, _run_in_one_boundary, authorize_or_raise, request_from_info}` (queries reuses the mutations substrate — correct direction: queries → mutations substrate, not vice-versa).
- **No sibling imports outside the documented boundary.** Verified `mutations/*`, `utils/*`, and `registry.py` do NOT import from `auth/`. The only two references to `auth` outside the module are both intentional and boundary-safe: `types/finalizer.py` uses a **function-local** `from ..auth.mutations import bind_auth_mutations` inside `finalize_django_types` (the phase-2.5 slot, mirroring `bind_mutations`/`bind_form_mutations`), and `registry.py::TypeRegistry.clear` names the auth clear via a **string-based** `_clear_if_importable("django_strawberry_framework.auth.mutations", "clear_auth_mutation_registry", …)` hand row (no import statement). Both avoid a top-level cycle. The dependency direction is exactly what the spec requires: auth depends on mutations/utils/registry, not the reverse.

### Pre-step 5 — walk accepted-slice `What looks solid` / `DRY findings` for deferred follow-ups

Walked all three. Deferred follow-ups surfaced (and routed below):

- Slice 1 `Notes for Worker 1`: the `resolvers.py` `run_pipeline_async` `TODO(spec-040 Slice 1)` anchor (carry-forward 2) and the unused `_build_auth_field(permission_holder=...)` param (carry-forward 3).
- Slice 2 `DRY findings` / `Notes for Worker 1`: the `_declare_surface`/`_declare_register_surface` duplication — **resolved in-slice at pass 2** (`_lookup_or_conflict`), NOT a carry-forward. The `build_input`/`RegisterInput` seam note — Worker-1 confirmed faithful to Decision 6's already-worded input-name seam, no spec edit, no carry-forward.
- Slice 3 `Notes for Worker 1` (M1) and Worker-1 final adjudication: the stale staging docstrings that render into `docs/TREE.md` (carry-forward 1).

Note: `Slice 1` already promoted `attach_synthesized_signature` (the one signature-injector shared by `DjangoMutationField` and the auth dispatcher) and `Slice 2` already consolidated `_lookup_or_conflict` — **verified no residual duplication remains from either** (see Integration checks below).

### Pre-step 6 — tree-wide staged-anchor sweep

`grep -rEn 'TODO\(spec-040|TODO-(ALPHA|BETA|STABLE)-040' .` (excluding `KANBAN.md` / `KANBAN.html` / `BACKLOG.md`):

**Exactly ONE surviving `TODO(spec-040 …)` anchor in shipped source:**

```
django_strawberry_framework/mutations/resolvers.py:1465:    # TODO(spec-040 Slice 1): if the auth resolvers need the same one-boundary
```

This is carry-forward 2 (below) — it must be discharged before build close.

**The `TODO-ALPHA-040-0.0.13` hits are all legitimate KANBAN card-id cross-references, NOT staged-work anchors** — they live in archived predecessor specs naming this card:

- `docs/SPECS/spec-036-mutations-0_0_11.md:568`, `docs/SPECS/spec-038-form_mutations-0_0_12.md:{616,888,2278}`, `docs/SPECS/spec-039-serializer_mutations-0_0_13.md:{49,528,1176,1238,1513,2707,3529,3549,3737}` — every one is a `[`TODO-ALPHA-040-0.0.13`][kanban]` reference-style link to the board card (the milestone-prefixed card-id form some specs use to reference a not-yet-Done card at authoring time). These are prose cross-references in **already-shipped** specs, not staged-anchor obligations, and BUILD.md's exclusion intent (KANBAN/BACKLOG naming board cards) extends to these prose card-id refs. No discharge obligation — leave as-is.

The active spec `docs/spec-040-…md` and the `bld-*.md` / `build-040-*.md` cycle artifacts are excluded from the sweep as per-cycle scratch. Their `TODO-ALPHA-040` mentions are card-id references, not source anchors.

---

## Integration checks (BUILD.md)

- **Duplicated helpers across slices — none.** The auth surface is a rider layer; every write-stack helper is reused by call (verified against spec `## Helper-reuse obligations (DRY)` D1-D19 + D-N1-D-N3 across the Slice-1 and Slice-2 reviews). `Slice 1` promoted `attach_synthesized_signature` so `DjangoMutationField` and the auth dispatcher share ONE injector (proved byte-transparent vs `git show HEAD`). `Slice 2` consolidated `_declare_surface` / `_declare_register_surface` into `_lookup_or_conflict` (the normalize+dedupe+conflict-raise is single-sited — `grep "was already declared with different"` returns one hit; Worker-1 confirmed 2 callers, no Slice-1 ledger regression). No residual duplication from either.
- **Inconsistent naming / error handling between slices — none.** All four surfaces gate through `authorize_or_raise` (one denial formatter, the `_primary_type`/holder-`__name__` fallback); all envelope errors ride `field_error` (`login` → empty path → `NON_FIELD_ERROR_KEY`; `register` password → direct `"password"` key; never a hard-coded `"__all__"`). Holder `__name__`s are pinned and test-asserted (`Login` / `Session` / `CurrentUser`). The three distinct bind-arm messages share the `_resolve_user_primary` getter, varying only the leading phrase.
- **Repeated ORM/queryset patterns that should be centralized — none introduced.** Auth adds no new ORM pattern: `login`/`current_user` do NO queryset work (D-N1, source-commented); `register` rides the inherited `refetch_optimized` + the shared `_model_write_step` `full_clean`/`save` tail; the exclusion seam is a parameter on the existing `_model_decode_step`/`_decode_relations` path (one production caller, default path byte-behavior-identical — proved mechanically vs HEAD).
- **Misplaced responsibilities between modules — none.** Auth resolvers/factories live under `auth/`; the write-stack primitives stay under `mutations/`; the phase-2.5 bind slot stays in `types/finalizer.py` (function-local import); the clear row stays in `registry.py` (string-based). One-way dependency direction confirmed (pre-step 4).
- **Missing / too-broad exports introduced by the build — none.** `git diff HEAD -- django_strawberry_framework/__init__.py` changes ONLY the `__version__` string literal (`0.0.12` → `0.0.13`); `__all__` and the re-export list are **unchanged**. Auth is submodule-only (spec Decision 3) — the four factories are re-exported from `auth/__init__.py` only, absent from the package root `__all__`. `tests/base/test_init.py::test_public_api_surface_is_pinned` pins the unchanged tuple. Confirmed across all three slice reviews.
- **Repeated string literals / dict keys / tuple shapes across slices — none.** See pre-step 3.
- **Comments tell one coherent story — MOSTLY, with one residue = carry-forward 1.** The reuse-by-call comments, the three D-N* non-reuse source comments, and the Decision cross-refs read coherently across the new auth code. The exception is the stale "planned by spec-040" / "Slice 1" / "Slice 2" **staging** language in seven source docstrings (and two internal `auth/mutations.py` body comments), which now describe shipped behavior as planned and render into `docs/TREE.md` — cataloged as carry-forward 1.

---

## THREE carry-forwards → concrete Worker-2 consolidation work items

All three require Worker-2 SOURCE edits. Worker 1 plans/records them here; Worker 0 dispatches a Worker-2 consolidation pass, then Worker-3 review, then returns to Worker 1 for the final integration `final-accepted`. **`grep -rEn 'TODO\(spec-040'` must be clean, and the staging docstrings refreshed, before the build closes.**

### Carry-forward 1 (M1) — refresh stale staging docstrings + regenerate `docs/TREE.md` IN THE SAME CHANGE

Seven source files carry "planned by spec-040" / "Slice 1" / "Slice 2" STAGING language describing now-shipped behavior. `docs/TREE.md` is generated by `scripts/build_tree_md.py` and renders its per-file/per-directory descriptions **from these module docstrings' first lines** — so the docstring fix and a TREE regenerate MUST land together in the same change (a hand-edit of `docs/TREE.md` is reverted by the next regenerate). The full verified extent (grepped this pass, broader than the original Slice-3 escalation named):

Module-docstring first lines (each renders into `docs/TREE.md`; TREE line refs in parens):

- `django_strawberry_framework/auth/__init__.py:1` — `"""Opt-in session-auth field factories planned by spec-040.` plus lines 4-5 `"…after Slice 1/2 replace the fail-loud placeholders in mutations.py and queries.py."` → TREE:208, :297. **Both the "planned by spec-040" first line AND the "after Slice 1/2 replace the fail-loud placeholders" body sentence are stale.**
- `django_strawberry_framework/auth/mutations.py:1` — `"""Opt-in session-auth mutation factories (spec-040 Slice 1: login / logout).` → TREE:209, :298. (The module also binds/holds login+logout+register+current_user substrate, so the "Slice 1: login / logout" framing under-describes it.)
- `django_strawberry_framework/auth/queries.py:1` — `"""Opt-in session-auth query factory (spec-040 Slice 2: current_user / me).` → TREE:210, :299.
- `examples/fakeshop/apps/accounts/__init__.py:1` — `"""Schema-only fakeshop accounts app planned by spec-040."""` → TREE:657.
- `tests/auth/test_mutations.py:1` — `"""Package-internal auth mutation tests (spec-040 Slice 1 residue a live query cannot drive).` → TREE:396, :559.
- `tests/auth/test_queries.py:1` — `"""Package-internal current_user tests (spec-040 Slice 2 residue a live query cannot drive).` → TREE:397, :560.
- `examples/fakeshop/test_query/test_auth_api.py:1` — `"""Live /graphql/ auth API acceptance tests (spec-040 Slice 1/2: login/logout/register/me).` → TREE:524.

Additionally (NOT rendered into TREE — internal-comment staleness in the same module, refresh for coherence with pre-step "comments tell one story"):

- `django_strawberry_framework/auth/mutations.py:236` — `"…Auth-local for Slice 1; the…"` (a resolver-body comment).
- `django_strawberry_framework/auth/mutations.py:305-306` — `"…(Slice 2 exercises the register arm; Slice 1 wires the ordering only)…"` (the `bind_auth_mutations` docstring — now that both arms shipped, the "Slice 2 exercises / Slice 1 wires" framing is stale).

**Fix pattern (established this cycle):** mirror the already-completed `tests/auth/__init__.py` refresh (Slice 3 flipped it to `"""Package-internal tests for the opt-in auth subsystem (spec-040)…"""` — "planned" gone, `TODO(spec-040 Slice 1-2)` anchor removed). For each file above: flip "planned by spec-040" / "after Slice 1/2 replace the fail-loud placeholders" to shipped wording, and re-tag the `Slice N` / `Slice 1/2` provenance to non-staging `spec-040` (or `DONE-040-0.0.13` where historical provenance is useful) per AGENTS.md L26 ("shipped behavior folds into `docs/TREE.md` … the staged anchor is removed in the same change that ships the slice"). **Then re-run `scripts/build_tree_md.py`** so `docs/TREE.md` re-renders from the fixed docstrings (and re-verify `build_tree_md.py --check` exits 0 — no behavior change expected).

Precise targets:
- `django_strawberry_framework/auth/__init__.py::<module docstring>` (lines 1, 4-5)
- `django_strawberry_framework/auth/mutations.py::<module docstring>` (line 1) + `::_build_auth_field #"Auth-local for Slice 1"` (line 236) + `::bind_auth_mutations #"Slice 2 exercises the register arm"` (lines 305-306)
- `django_strawberry_framework/auth/queries.py::<module docstring>` (line 1)
- `examples/fakeshop/apps/accounts/__init__.py::<module docstring>` (line 1)
- `tests/auth/test_mutations.py::<module docstring>` (line 1)
- `tests/auth/test_queries.py::<module docstring>` (line 1)
- `examples/fakeshop/test_query/test_auth_api.py::<module docstring>` (line 1)
- Regenerate: `scripts/build_tree_md.py` (run it; `docs/TREE.md` is the output — do NOT hand-edit it).

### Carry-forward 2 — discharge the `resolvers.py::run_pipeline_async` `TODO(spec-040 Slice 1)` anchor

`django_strawberry_framework/mutations/resolvers.py:1465` (inside `run_pipeline_async`) carries a `TODO(spec-040 Slice 1)` inviting the optional generic one-boundary primitive factoring. `Slice 1` deliberately kept the auth async boundary auth-local (`_run_in_one_boundary`) per the plan's P3 safe default (spec Decision 10 P3 says the generic primitive is a "may," not a "must"), so the work the anchor names was **not** taken. Per BUILD.md integration-pass step 6, a `TODO(spec-040 Slice 1)` anchor surviving in shipped source must be **discharged**: the auth async paths already ride one boundary via the auth-local `_run_in_one_boundary`, and the spec (Decision 10 P3) was already edited during Slice-1 final verification to record that auth-local is the shipped shape. So the discharge is: **remove the anchor** (the optional factoring is not being done), OR **re-tag it to non-TODO `spec-040` provenance** (e.g. a plain comment noting the auth async boundary is auth-local by design per Decision 10 P3, with no `TODO(` prefix). Recommended: convert the `TODO(spec-040 Slice 1):` prefix to a non-TODO provenance note (the surrounding pseudocode explaining the generic-primitive shape is worth keeping as a design note, just not as a live TODO). Do NOT change `run_pipeline_async`'s signature or behavior — the mutation-shaped public wrapper stays as-is.

Precise target: `django_strawberry_framework/mutations/resolvers.py::run_pipeline_async #"TODO(spec-040 Slice 1)"` (line ~1465).

### Carry-forward 3 — drop the unused `_build_auth_field(permission_holder=...)` param

`django_strawberry_framework/auth/mutations.py::_build_auth_field` takes `permission_holder: type` as its first positional (line 185) and immediately `del`s it (line 206, comment "captured by the resolver closures, not read here"). The three call sites — `login_mutation` (mutations.py:468), `logout_mutation` (mutations.py:513), and `current_user` (queries.py:98) — each pass it, but the resolver bodies close over the outer `holder = record.holder`, not over this parameter, so it is genuinely dead (the `del` acknowledges it). Drop the parameter and its `del` line, and remove the argument from all three call sites. Low/cosmetic — no behavior impact; a minor API/readability cleanup on the module-internal helper.

Precise targets:
- `django_strawberry_framework/auth/mutations.py::_build_auth_field` — remove the `permission_holder: type` param (line 185) and the `del permission_holder` line (line 206).
- Call sites to update (drop the passed `permission_holder` arg): `django_strawberry_framework/auth/mutations.py::login_mutation #"_build_auth_field("` (line 468), `::logout_mutation #"_build_auth_field("` (line 513), and `django_strawberry_framework/auth/queries.py::current_user #"_build_auth_field("` (line 98).

---

## Cross-slice DRY findings (beyond the three carry-forwards)

**None.** The DRY-scan verdict is clean: no cross-slice duplicated helper, no shared repeated literal / dict key / tuple shape, no cross-slice near-copy. The two in-slice consolidations that already landed (`attach_synthesized_signature` in Slice 1, `_lookup_or_conflict` in Slice 2) leave no residual duplication. The only DRY-adjacent items are carry-forward 1's comment-coherence residue (staging docstrings) — a wording refresh, not a code-duplication fix.

## Spec-changes note (Worker 1 only)

No spec edit made in this integration pass. The two spec edits already made during the per-slice cycles remain the reconciled state: (Slice 1) Decision 10 P3 recorded the auth-local boundary as the shipped shape; (Slice 3 reconciliation) the `docs/spec-040-…-terms.csv` dedup to 30 one-per-anchor rows. Neither carry-forward here requires a spec-body change — carry-forward 1 is source-docstring/generated-doc residue, carry-forward 2 is spec-authorized (Decision 10 P3 already records the auth-local shape), and carry-forward 3 is a cosmetic dead-param removal.

## Routing

**A consolidation loop IS required** (the three carry-forwards are open source edits). Worker 0 must:

1. Dispatch a **Worker 2 consolidation pass** to land carry-forwards 1-3 (M1 docstring refresh + `build_tree_md.py` regenerate in the SAME change; the `resolvers.py:1465` anchor discharge; the `_build_auth_field(permission_holder=...)` dead-param removal). No cross-slice DRY refactor beyond these three.
2. Dispatch a **Worker 3 review pass** over that consolidation diff (must confirm: `grep -rEn 'TODO\(spec-040' --include='*.py'` is clean; `docs/TREE.md` no longer renders "planned by spec-040" / "Slice 1"/"Slice 2" staging strings and `build_tree_md.py --check` exits 0; the three call sites drop the `permission_holder` arg cleanly; `__init__.py` `__all__` still unchanged; the auth suite + `tests/mutations/` stay green).
3. **Return to Worker 1** for a re-run of this integration pass to set `Status: final-accepted` once the three carry-forwards are discharged. Only then does Worker 0 mark the integration checklist box `- [x]` and proceed to the final test-run gate (`bld-final.md`).

Do NOT set `final-accepted` on this artifact while the carry-forwards are unresolved.

---

## Build report (Worker 2)

Consolidation pass landing the three carry-forwards catalogued above. No cross-slice DRY refactor beyond these three; all edits are behavior-neutral (docstring/comment wording + a dead-param removal + a generated-doc regenerate).

### Files touched

Grounded in `git status --short` after both ruff invocations. The nine files below are this pass's diff (the rest of the working tree is the pre-existing Slice-1/2/3 build diff, the 8 `D` spec-039 prior-cycle deletions, the untracked spec-040 build artifacts, and the concurrent-writable DB/KANBAN/GLOSSARY — none of which this pass touched):

**Carry-forward 1 (M1 — staging-docstring/comment refresh + TREE regenerate, same change):**

- `django_strawberry_framework/auth/__init__.py` — module docstring: `"…field factories planned by spec-040."` → `"…field factories (spec-040)."`; the stale body sentence `"…after Slice 1/2 replace the fail-loud placeholders…"` → shipped wording naming the four now-shipped factories.
- `django_strawberry_framework/auth/mutations.py` — module docstring first line `"(spec-040 Slice 1: login / logout)"` → `"+ shared auth substrate (spec-040)"` (the old first line under-described a module that now holds login/logout/register + the shared substrate + the bind); added a body paragraph enumerating the shipped contents. Plus the two internal body comments: `_run_in_one_boundary` docstring `"Auth-local for Slice 1; …deferred (spec Decision 10 P3 'may'…)"` → `"Auth-local by design (spec-040 Decision 10 P3): …a P3 'may', not a 'must', so the auth async boundary stays this one-helper shape…"`; `bind_auth_mutations` docstring `"(Slice 2 exercises the register arm; Slice 1 wires the ordering only)"` → `"(the ordering the register arm depends on)"`.
- `django_strawberry_framework/auth/queries.py` — module docstring `"(spec-040 Slice 2: current_user / me)"` → `"(spec-040: current_user / me)"`; body `"sharing the Slice-1 auth substrate"` → `"sharing the auth substrate"`.
- `examples/fakeshop/apps/accounts/__init__.py` — single-line docstring `"…accounts app planned by spec-040."` → `"…accounts app exercising the session-auth surface (spec-040)."`.
- `tests/auth/test_mutations.py` — module docstring first line `"(spec-040 Slice 1 residue…)"` → `"(spec-040 residue…)"`.
- `tests/auth/test_queries.py` — module docstring first line `"(spec-040 Slice 2 residue…)"` → `"(spec-040 residue…)"`.
- `examples/fakeshop/test_query/test_auth_api.py` — module docstring first line `"(spec-040 Slice 1/2: login/logout/register/me)"` → `"(spec-040: login/logout/register/me)"`; body `"and (Slice 2) the register ->"` → `"and the register ->"`.
- `docs/TREE.md` — **regenerated** via `uv run python scripts/build_tree_md.py` in the SAME change (renders per-file descriptions from the module docstrings' first lines). Now renders the refreshed shipped descriptions at TREE:208-210, :297-299 (auth package), :395-397, :558-560 (`tests/auth/`), :524 (`test_auth_api.py`), :657 (`accounts/`). No `"planned by spec-040"` / `"spec-040 Slice"` staging string remains in TREE.md (verified by grep, no matches). NOT hand-edited.

**Carry-forward 2 (`TODO(spec-040 Slice 1)` anchor discharge):**

- `django_strawberry_framework/mutations/resolvers.py` — `run_pipeline_async` body: the `# TODO(spec-040 Slice 1): …factor the core…` anchor (6 lines) → a non-TODO provenance comment recording that spec-040 kept the auth one-boundary need auth-local (Decision 10 P3 "may", not "must"), pointing at `auth/mutations.py::_run_in_one_boundary`. Design-note content preserved; `TODO(` prefix removed. `run_pipeline_async`'s signature and behavior unchanged (the `return await sync_to_async(...)` line is byte-identical).

**Carry-forward 3 (dead `_build_auth_field(permission_holder=...)` param):**

- `django_strawberry_framework/auth/mutations.py` — `_build_auth_field`: removed the leading `permission_holder: type` param and the `del permission_holder  # captured by the resolver closures, not read here.` line. Dropped the passed `holder` argument at the two mutation call sites (`login_mutation`, `logout_mutation`).
- `django_strawberry_framework/auth/queries.py` — dropped the passed `holder` argument at the `current_user` call site.

  Behavior-preserving: each factory still binds `holder = record.holder` and its resolver closures (`_login_body` / `_logout_body` / `_current_user_body`) close over that outer `holder` for `authorize_or_raise(holder, …)`. The param was genuinely dead (the pre-edit `del` acknowledged it), so removal is a no-op on runtime behavior. `holder` remains a live local in all three factories (ruff raised no unused-variable finding).

### Tests added or updated

None. All three carry-forwards are behavior-neutral cleanups (docstring/comment wording + a dead-param removal + a doc regenerate), so no assertion changed. The dead-param removal needed no test tweak: no test constructs `_build_auth_field` directly (the three in-tree factory call sites were the only callers), and the existing auth suite reaches the synthesized resolver via `T.__strawberry_definition__.fields[i].base_resolver.wrapped_func`, which is unaffected by the private helper's arity.

### Validation run

- `uv run ruff format .` — pass (`308 files left unchanged`; the standing COM812/formatter-conflict warning is pre-existing config noise, not a failure).
- `uv run ruff check --fix .` — pass (`All checks passed!`). Re-run after the TREE regenerate: still `All checks passed!`.
- `uv run python scripts/build_tree_md.py` then `--check` — regenerate wrote `docs/TREE.md`; `--check` exits 0 (`docs/TREE.md is up to date.`), so the docstring fix and TREE render landed together and are byte-stable.
- `grep -rEn 'TODO\(spec-040' --include='*.py' .` — **clean** (no matches, exit 1). The only prior surviving anchor (`resolvers.py` `run_pipeline_async`) is discharged; the Slice-2 `_model_decode_step` anchor was already discharged in the accepted Slice-2 diff.
- `git status --short` classification — identical file set to the pass start; no NEW untracked file and no unrelated tool churn appeared. This pass's 9 files (listed under `### Files touched`) carry my edits; every other modified/deleted/untracked entry is a pre-existing Slice-1/2/3 build file, an 8-file `D` spec-039 prior-cycle deletion, an untracked spec-040 build artifact, or a concurrent-writable DB/KANBAN/GLOSSARY per the task's enumerated baseline — left untouched, not reverted (AGENTS.md rule 34 + the task's explicit "not this pass's churn" list). `docs/TREE.md` changing is the intended M1 regenerate.
- Focused tests (no `--cov*` flags):
  - `uv run pytest tests/auth/ --no-cov -q` — **47 passed**.
  - `uv run pytest examples/fakeshop/test_query/test_auth_api.py --no-cov -q -n0` — **12 passed** (live suite run `-n0` per the transactional-DB requirement).
  - `uv run pytest tests/mutations/ --no-cov -q` — **176 passed** (guards against an over-correction from the `resolvers.py` comment edit; the resolvers module backs the whole mutations stack).

### Implementation notes

- **`auth/mutations.py` module docstring — first-line rewrite is TREE-render-load-bearing.** `scripts/build_tree_md.py::first_python_docstring_sentence` takes the docstring's first non-blank line and requires it to end with `.` (raises `TreeRenderError` otherwise). The new first line ends `"(spec-040)."` and stays a single sentence; the enumerating body paragraph I added is NOT rendered into TREE (the package tree renders only the first sentence; only `apps/<app>/__init__.py` detail-paragraphs feed the "App roles" section, and `accounts/__init__.py` stays single-line so its `detail_paragraphs` returns `[]`). Verified against the script rather than guessing.
- **Carry-forward-2 discharge shape — provenance comment, not deletion.** Chose the artifact's recommended path (re-tag to non-TODO `spec-040` provenance) over a bare delete, because the surrounding note explains WHY the auth boundary stayed auth-local (Decision 10 P3) — useful design context, just not a live TODO. Pointed it at `auth/mutations.py::_run_in_one_boundary` (symbol-qualified per AGENTS.md L27) so the cross-reference cannot drift on a line move.
- **Param-removal ordering.** Removed the `del permission_holder` line together with the signature param (leaving a lone `del` of a now-undefined name would `NameError`); the two-line removal is atomic. Confirmed `holder` is still consumed by each factory's resolver closure before dropping the arg, so the three call sites lose only the redundant first positional.

### Notes for Worker 3

- Shadow/helper: `scripts/review_inspect.py` was NOT re-run this pass — the edits are wording refreshes + a dead-param drop + a doc regenerate, adding zero review-worthy logic (no new branch, no new call, no signature change beyond a param removal). The Pre-step-2 shadow refresh from the integration pass still covers these files.
- To re-verify the discharge cheaply: `grep -rEn 'TODO\(spec-040' --include='*.py' .` (expect no matches) and `uv run python scripts/build_tree_md.py --check` (expect exit 0). Then `git diff -- django_strawberry_framework/mutations/resolvers.py` — the only line touched inside `run_pipeline_async` besides the comment swap is unchanged (the `sync_to_async(...)` return is byte-identical); the large Slice-2 exclusion-seam hunk earlier in that same file is the pre-accepted Slice-2 diff, not this pass.
- `git diff -- django_strawberry_framework/__init__.py` still changes only the `__version__` string (Slice-3 work) — this pass did NOT touch `__all__` or the re-export list; auth stays submodule-only.
- The dead-param drop is a private module-internal helper (`_build_auth_field`), absent from any `__all__`; no public surface moved.

### Notes for Worker 1 (spec reconciliation)

None. No spec-body change is needed: carry-forward 1 was source-docstring / generated-doc residue, carry-forward 2 is already spec-authorized (Decision 10 P3 records the auth-local shape, edited during Slice-1 final verification), and carry-forward 3 is a cosmetic dead-param removal. No plan-vs-implementation drift surfaced — all three carry-forwards landed exactly as catalogued.

---

## Review (Worker 3)

Focused review of the behavior-neutral consolidation diff (the nine scoped files), NOT a re-litigation of the three already-`final-accepted` slices. Verified each of the three carry-forwards was resolved correctly and behavior-neutrally, ran the required regression tests without `--cov*`, and confirmed the public surface.

### Item 1 — staging-docstring/comment refresh + TREE regenerate (M1)

**Verified resolved.** Read all seven refreshed module docstrings and the two `auth/mutations.py` body comments; none describe shipped behavior as "planned" / "after Slice 1/2 replace the fail-loud placeholders" / "Slice N staging" any longer, and all read coherently as shipped:

- `auth/__init__.py::<module docstring>` — first line `"…field factories (spec-040)."`; body now names the four shipped factories and their homes. No "planned" / "after Slice 1/2" residue.
- `auth/mutations.py::<module docstring>` — first line `"Opt-in session-auth mutation factories + shared auth substrate (spec-040)."` (ends `.`, single sentence — TREE-render-safe per `build_tree_md.py::first_python_docstring_sentence`); body enumerates login/logout/register + substrate + bind. No longer under-describes as "Slice 1: login / logout".
- `auth/mutations.py::_run_in_one_boundary` (docstring, ~L239-242) — `"Auth-local by design (spec-040 Decision 10 P3): …a P3 'may', not a 'must'…"`. Reads as a shipped design rationale, not a Slice-1 staging note.
- `auth/mutations.py::bind_auth_mutations` (docstring, ~L309-310) — `"…the register rider's generic ``_resolve_primary_type`` raise (the ordering the register arm depends on)."` The stale "Slice 2 exercises the register arm; Slice 1 wires the ordering only" framing is gone.
- `auth/queries.py::<module docstring>` — `"(spec-040: current_user / me)"`; body `"sharing the auth substrate"` (Slice-1 qualifier dropped).
- `examples/fakeshop/apps/accounts/__init__.py::<module docstring>` — single-line `"…accounts app exercising the session-auth surface (spec-040)."` (stays single-line, so `detail_paragraphs` returns `[]` and it renders one TREE line as before).
- `tests/auth/test_mutations.py` / `tests/auth/test_queries.py::<module docstring>` — first lines `"(spec-040 residue…)"` (Slice-N qualifier dropped).
- `examples/fakeshop/test_query/test_auth_api.py::<module docstring>` — `"(spec-040: login/logout/register/me)"`; the two `TODO(spec-040 Slice 1)` / `TODO(spec-040 Slice 2)` pseudocode anchor blocks are replaced by shipped prose; body `"and (Slice 2) the register ->"` → `"and the register ->"`.

**TREE re-rendered correctly (GENERATED, not hand-edited).** `grep -nE 'planned by spec-040|spec-040 Slice' docs/TREE.md` returns NONE (exit 1). `uv run python scripts/build_tree_md.py --check` prints `docs/TREE.md is up to date.` and exits 0 — the docstring fix and the TREE regenerate landed together and are byte-stable (no pending drift, no hand-edit).

**Inline-provenance-comment read (the remaining `spec-040 Slice N` strings in shipped source).** `grep -rn "spec-040 Slice" --include='*.py'` (excluding `docs/builder/` + `temp-tests/`) returns EXACTLY the eight strings the plan anticipated, and I read each in context:

- `registry.py #"co-clear the auth declaration ledger here"` (L586) — explains WHY the auth clear is a direct hand row, not routed through `register_subsystem_clear` (ledger must survive the pre-bind reset). Design rationale.
- `types/finalizer.py #"bind auth declarations in this exact slot"` (L788) — explains the load-bearing bind ordering (after emit-ledger reset, before `bind_mutations()`). Design rationale. (Note: it retains a parenthetical "and, in Slice 2, register / current_user" — a completed-history clause, reads as shipped, not a to-do.)
- `mutations/resolvers.py #"the reusable exclusion seam (spec-040 Slice 2)"` (L252, L1182) — the `excluded_input_fields` seam docstrings citing the spec slice as the seam's origin/rationale. Design provenance.
- `examples/fakeshop/schema_reload.py` (L40), `config/settings.py` (L47), `config/schema.py` (L25-27, L59) — cite the slice to explain why the accounts app is listed / composed and why it is dependency-independent (references only `auth.User`).

**Verdict: legitimate non-TODO design provenance, acceptable per AGENTS.md L26** — every one cites `spec-<NNN> Slice N` as the *rationale* for a load-bearing decision (bind ordering, co-clear seam, exclusion seam, dependency-safe reload order), carries NO `TODO(` prefix and no `NotImplementedError` pairing, is written in the same idiom the codebase already uses for `spec-036 Slice 4` / `spec-037` / `spec-038` / `spec-039 M1a` (present in the very same `config/schema.py` and `resolvers.py` comments), and does NOT render into TREE (these are body-comment / docstring-body lines, not module-docstring first lines — TREE staging grep is clean). AGENTS.md L26 explicitly sanctions `spec-<NNN>` provenance "where historical context is useful" as the replacement for a staged anchor. **Not a finding.**

### Item 2 — `resolvers.py` anchor discharge

**Verified resolved.** `grep -rEn 'TODO\(spec-040' --include='*.py' .` is clean (exit 1, no matches) — no `TODO(spec-040` anchor survives anywhere in shipped `.py` source. The former `TODO(spec-040 Slice 1)` block inside the async pipeline core (`resolvers.py` ~L1465-1469) is now a non-`TODO(` provenance comment recording that spec-040 kept the auth one-boundary need auth-local (Decision 10 P3 "may", not "must") and pointing at `auth/mutations.py::_run_in_one_boundary` (symbol-qualified, drift-safe per AGENTS.md L27). The wrapper's signature is unchanged and the `return await sync_to_async(sync_body, thread_sensitive=True)(mutation_cls, info, data, id)` line (L1470) is intact — behavior unchanged.

### Item 3 — dead `_build_auth_field(permission_holder=...)` param removal

**Verified resolved and behavior-preserving.** `grep -n permission_holder` across `auth/mutations.py` + `auth/queries.py` returns NOTHING — the param and its `del permission_holder` line are both gone. `_build_auth_field` (mutations.py::`_build_auth_field`, L189) now takes `payload_lazy_ref` as its leading positional. All three call sites pass the lazy ref first with no leading holder arg:

- `login_mutation` (L472): `_build_auth_field(_lazy_ref(_LOGIN_PAYLOAD, …), _sync, _async, params, …)`.
- `logout_mutation` (L516): `_build_auth_field(_lazy_ref(_LOGOUT_PAYLOAD, …), _sync, _async, [], …)`.
- `queries.py::current_user` (L98): `_build_auth_field(_lazy_ref(_CURRENT_USER_ALIAS, …) | None, _sync, _async, [], …)`.

Behavior-preservation confirmed by tracing the closures: each factory binds `holder = record.holder` (e.g. logout L498) and its resolver body calls `authorize_or_raise(holder, …)` (e.g. L504) closing over that outer local, NOT over the removed param. The removed param was `del`'d immediately in the pre-edit code and never read (Slice-1 review + the prior `del` comment both confirmed it dead), so removal is a runtime no-op. `holder` stays a live local in all three factories.

### Regression

No regression. Focused suites, no `--cov*` flags:

- `uv run pytest tests/auth/ tests/mutations/ --no-cov -q` — **223 passed** (47 auth + 176 mutations).
- `uv run pytest examples/fakeshop/test_query/test_auth_api.py --no-cov -q -n0` — **12 passed** (live `/graphql/` suite, `-n0` per the transactional-DB requirement).

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` changes ONLY the `__version__` string literal (`"0.0.12"` → `"0.0.13"`, the Slice-3 version cut). `__all__` and the re-export list are **unchanged** — auth stays submodule-only (spec Decision 3). No new public export introduced by the consolidation.

### CHANGELOG sanity

Not applicable; the consolidation pass did not modify `CHANGELOG.md`.

### Static inspection (helper) disposition

**Skipped, with reason.** The consolidation's only logic change is the `_build_auth_field` param removal (a signature-param drop + two-line `del` removal + three call-site arg drops — well under the 30-line BUILD.md threshold); the `resolvers.py` edit is comment-only, and the remaining eight files are docstring/comment wording + a generated-doc regenerate (zero new branch / call / logic). No file under `optimizer/` or `types/` gained logic. `scripts/review_inspect.py` was correctly not re-run (the Pre-step-2 shadow refresh already covers these files); a re-run would add no signal on behavior-neutral cleanup.

### Temp test verification

None created. All three carry-forwards are behavior-neutral; the existing suites (auth 47 + mutations 176 + live 12) exercise the touched paths, and the dead-param removal has no behavior to pin (no test constructs `_build_auth_field` directly; the auth suite reaches the synthesized resolver via `__strawberry_definition__`, unaffected by the private helper's arity). Nothing to promote. `docs/builder/temp-tests/integration/` was never created — no disposition needed.

### DRY findings

**None.** This pass introduced no new duplication; it is pure consolidation (docstring/comment refresh + a dead-param drop). The two prior in-slice consolidations (`attach_synthesized_signature` in Slice 1, `_lookup_or_conflict` in Slice 2) remain single-sited. Cross-slice DRY was already adjudicated clean by Worker 1's integration catalog above; nothing in the consolidation diff reopens it.

### What looks solid

- The `auth/mutations.py::<module docstring>` first-line rewrite is TREE-render-load-bearing (single sentence ending `.`), and the enumerating body paragraph is added below the first line so it does NOT feed the package-tree render — handled correctly (verified by `--check` exit 0).
- The anchor discharge chose the design-note-preserving path (non-`TODO(` provenance comment) over a bare delete, and symbol-qualified the cross-reference (`::_run_in_one_boundary`) so it cannot drift on a line move.
- The param-removal removed the `del` line atomically with the signature param (a lone `del` of an undefined name would `NameError`), and `holder` remains consumed by every factory's resolver closure.

### New findings

**None.** No High, Medium, or Low finding introduced by the consolidation. All three carry-forwards landed exactly as catalogued; the inline-provenance `spec-040 Slice N` strings are legitimate design provenance, not residual staging vocabulary.

### Review outcome

**review-accepted.** All three carry-forwards are correctly and behavior-neutrally resolved: (1) staging docstrings/comments refreshed as shipped and `docs/TREE.md` re-rendered from them (`--check` exit 0, staging-string grep clean, inline `spec-040 Slice N` provenance judged acceptable per AGENTS.md L26); (2) the `TODO(spec-040 Slice 1)` anchor discharged to a non-TODO provenance comment with `run_pipeline_async`'s signature/behavior unchanged and NO `TODO(spec-040` surviving in any shipped `.py`; (3) the dead `permission_holder` param removed from `_build_auth_field` and all three call sites, proven behavior-preserving (closures close over `record.holder`). No regression (223 focused + 12 live green), public surface unchanged (only `__version__`), no new findings. This acceptance signals Worker 0 to return to Worker 1 for the final integration verification (`final-accepted` is Worker 1's to set — NOT set here).

---

## Final verification (Worker 1)

Re-ran this integration pass over the consolidation diff (Worker 2's build report + Worker 3's `review-accepted`) to confirm the three carry-forwards are genuinely discharged in the working tree, the DRY verdict still holds, the public surface is unchanged, and nothing regressed. All checks pass. **Setting the artifact top-level `Status: final-accepted`.**

### Carry-forward 1 (M1 staging docstrings + TREE) — DISCHARGED

- `grep -nE 'planned by spec-040|spec-040 Slice' docs/TREE.md` → **no matches (exit 1)**. No staging string renders into TREE.
- `uv run python scripts/build_tree_md.py --check` → `docs/TREE.md is up to date.` (**exit 0**) — the docstring refresh and the TREE regenerate are byte-stable and landed together; no pending drift, no hand-edit.
- Read the refreshed docstrings/comments in the working tree: `auth/__init__.py` first line `"…field factories (spec-040)."` + body names the four shipped factories; `auth/mutations.py` first line `"…mutation factories + shared auth substrate (spec-040)."`; the `_run_in_one_boundary` docstring reads as a shipped design rationale ("Auth-local by design (spec-040 Decision 10 P3)…"); the `bind_auth_mutations` docstring dropped the "Slice 2 exercises / Slice 1 wires" staging framing; `auth/queries.py` module first line `"(spec-040: current_user / me)"` + body L3 `"sharing the auth substrate"`; `examples/fakeshop/apps/accounts/__init__.py`, `tests/auth/test_mutations.py`, `tests/auth/test_queries.py`, `examples/fakeshop/test_query/test_auth_api.py` all carry shipped wording (no "planned" / "after Slice 1/2 replace the placeholders" / "Slice N residue" staging). No STAGING vocabulary remains.
- **Remaining inline `spec-040 Slice N` provenance — re-confirmed legitimate (AGENTS.md L26).** `grep -rnE 'spec-040 Slice|Slice-1 auth|planned by spec-040|after Slice' --include='*.py'` (excl. `docs/builder/`, `temp-tests/`) returns exactly the design-provenance strings Worker 3 enumerated (`registry.py #"co-clear the auth declaration ledger"`, `types/finalizer.py #"bind auth declarations in this exact slot"`, `mutations/resolvers.py` ×2 exclusion-seam docstrings, `schema_reload.py`, `config/schema.py` ×2, `config/settings.py`). Each cites the slice as the *rationale* for a load-bearing decision, carries no `TODO(` prefix and no `NotImplementedError` pairing, matches the codebase's existing `spec-036 Slice 2` / `spec-039 Slice 2` idiom, and none renders into TREE. Accepted per AGENTS.md L26 (staged TODO anchors are the removal target; factual `spec-<NNN>` provenance "where historical context is useful" is sanctioned).
- **Minor coherence note (accepted, NOT a blocker):** `auth/queries.py::current_user` function docstring still reads `"sharing the Slice-1 auth machinery"` (`queries.py #"sharing the Slice-1 auth machinery"`), while the module docstring three lines above dropped the qualifier to `"sharing the auth substrate"`. This second occurrence was outside carry-forward 1's cataloged scope (which named only `queries.py::<module docstring>` line 1) and so was not touched by the consolidation. It is factual inline provenance (not staging vocabulary, not a `TODO(` anchor), does NOT render into TREE (`grep 'Slice-1 auth machinery' docs/TREE.md` → exit 1), and sits comfortably within the AGENTS.md L26 provenance idiom. It does not warrant re-opening the consolidation loop; recorded here so the next docstring-touching change can drop the lone qualifier for full within-module coherence.

### Carry-forward 2 (`TODO(spec-040 Slice 1)` anchor) — DISCHARGED

- `grep -rEn 'TODO\(spec-040' --include='*.py' .` → **no matches (exit 1)**. No `TODO(spec-040` anchor survives anywhere in shipped `.py`.
- Read `mutations/resolvers.py::run_pipeline_async` in the working tree: the former `TODO(spec-040 Slice 1)` block is now a plain provenance comment ("spec-040 kept the auth one-boundary need auth-local (Decision 10 P3 'may', not 'must')…") pointing at `auth/mutations.py::_run_in_one_boundary` (symbol-qualified). The `return await sync_to_async(sync_body, thread_sensitive=True)(mutation_cls, info, data, id)` line is intact — signature and behavior unchanged.

### Carry-forward 3 (dead `_build_auth_field(permission_holder=...)` param) — DISCHARGED

- `grep -rnE '\bpermission_holder\b' auth/mutations.py auth/queries.py` → **no matches (exit 1)** for the dead param (the `_make_permission_holder` factory symbol is distinct and stays). No `del permission_holder` line remains.
- `_build_auth_field` (`auth/mutations.py::_build_auth_field`) now takes `payload_lazy_ref: Any` as its leading positional. All three call sites pass the lazy ref first with no leading holder arg: `login_mutation` (`_lazy_ref(_LOGIN_PAYLOAD, …)`), `logout_mutation` (`_lazy_ref(_LOGOUT_PAYLOAD, …)`), and `queries.py::current_user` (`_lazy_ref(_CURRENT_USER_ALIAS, …) | None`).
- **Behavior-preserving:** each factory still binds `holder = record.holder` and its resolver body calls `authorize_or_raise(holder, …)` closing over that outer local (verified in `logout_mutation`: `holder = record.holder` then `authorize_or_raise(holder, info, _LOGOUT, None, instance=None)`), NOT over the removed param. Runtime no-op.

### Public surface + DRY re-confirmation

- `git diff HEAD -- django_strawberry_framework/__init__.py` changes ONLY the `__version__` string (`"0.0.12"` → `"0.0.13"`, the Slice-3 cut). `__all__` and the re-export list are **unchanged** — auth stays submodule-only (spec Decision 3).
- **DRY scan verdict still holds.** The consolidation introduced no new cross-slice duplication: it is a docstring/comment refresh + a dead-param drop + a generated-doc regenerate. The two prior in-slice consolidations (`attach_synthesized_signature`, `_lookup_or_conflict`) remain single-sited; no residual duplication reopened. Comments now tell one coherent story across the auth code (the only wrinkle is the accepted `queries.py:52` provenance qualifier noted above).

### Regression check (no `--cov*` flags)

- `uv run pytest tests/auth/ tests/mutations/ --no-cov -q` → **223 passed** (47 auth + 176 mutations), 8.31s.
- `uv run pytest examples/fakeshop/test_query/test_auth_api.py --no-cov -q -n0` → **12 passed** (live `/graphql/` suite, `-n0` per the transactional-DB requirement), 26.56s.

### Spec status-line re-verification

Spec `docs/spec-040-…md` status line (L72) reads "IN PROGRESS — Slices 1, 2, and 3 … all final-accepted; cross-slice integration pass + final test-run gate remain." This accurately describes the current state (the integration pass completes now; the final test-run gate `bld-final.md` still remains). No spec edit needed this pass.

### Final status

**final-accepted.** The three consolidation carry-forwards are genuinely discharged in the working-tree diff (M1 staging docstrings refreshed + TREE re-rendered byte-stable; the `TODO(spec-040 Slice 1)` anchor converted to a non-TODO provenance comment with `run_pipeline_async` behavior unchanged; the dead `permission_holder` param removed from `_build_auth_field` and all three call sites, behavior-preserving). The DRY scan verdict still holds (no cross-slice duplication introduced), the public surface is unchanged (only `__version__`), the auth code's comments tell one coherent story, and the focused regression suites are green (223 focused + 12 live). One accepted, non-blocking coherence note recorded (the `auth/queries.py:52` inline `Slice-1` provenance qualifier). Worker 0 may now mark the integration checklist box `- [x]` and dispatch the final test-run gate (`bld-final.md`), which will also produce the `### Deferred work catalog`.
