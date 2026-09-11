# Build: Slice 4 — conformance audit C (helper-reuse obligations, edge cases, test plan, DoD)

Spec reference: `docs/SPECS/spec-040-auth_mutations-0_0_13.md` (`## Slice checklist` blockquote at 241-254; `## Implementation plan` 1728-1748; `## Helper-reuse obligations (DRY)` 1749-1858; `## Edge cases and constraints` 1859-2024; `## Test plan` 2025-2203; `## Doc updates` 2204-2253; `## Out of scope (explicitly tracked elsewhere)` 2254-2286; `## Definition of done` 2287-2416 — all post-edit)
Status: final-accepted

## Plan (Worker 1)

A **retrospective conformance audit**, not a build. It ships no source change. Its
instrument is the Definition-of-done checklist plus the conformance matrix below; its
output is spec edits (`SPEC-STALE` rows), one recorded `CODE-GAP` and three recorded
`TEST-GAP`s for the code-fix cohort, and hand-offs to Slice 5.

This is the third audit slice and matches the instrument Slices 2 and 3 established.
It adds one verdict they did not carry — **`TEST-GAP`** — and that verdict is the
point of the slice: a `## Test plan` row the shipped suite does not actually assert,
or an obligation nothing would catch the violation of, is a `TEST-GAP`, never a
`CONFORMS`.

### DRY analysis

**Helper inventory checked.** Refreshed package-wide against the working tree for
this pass by sweeping every symbol the obligations name, rather than re-running the
AST dump — the obligations ARE a helper inventory, and the recurring defect Slices 2
and 3 both hit is a named private helper that died while its invariant survived. The
sweep was mechanical and is the settling evidence for the whole `## Helper-reuse
obligations (DRY)` block:

```shell
for s in request_from_info _AUTH_FAMILY_LABEL reject_async_in_sync_context \
  _PERMISSION_ASYNC_RECOURSE check_permission _mutation_meta \
  _validate_permission_classes _make_permission_holder authorize_or_raise \
  _primary_type build_payload_type payload_object_slot iter_provided_input_fields \
  excluded_input_fields _model_decode_step _decode_relations _unprovided_exclude \
  _full_clean_or_field_errors save_or_field_errors validate_password set_password \
  field_error NON_FIELD_ERROR_KEY refetch_optimized input_type_name build_input \
  materialize_mutation_input_class _lazy_ref make_input_namespace \
  make_declaration_registry _resolve_primary_type types_for \
  run_in_one_sync_boundary is_async_callable SyncMisuseError \
  validation_error_to_field_errors editable_input_fields derive_register_fields \
  input_field_required; do
  n=$(rg -c --glob '*.py' -- "$s" . | awk -F: '{s+=$2} END {print s+0}')
  printf "%-40s %s\n" "$s" "$n"
done
```

**39 symbols swept; 38 resolve, exactly one returns 0: `excluded_input_fields`.**
That is the fourth instance of the cycle's recurring shape (after `_resolve_auth_async`,
the `excluded_input_fields` parameter as Decision 6 named it, and `_bind_mutation`) and
the only dangling name in the whole obligations block — the D17 / P3 and D12 / P1 / P2
staleness Slices 2 and 3 routed here is a **description** defect, not a dangling symbol:
every symbol those two items name still resolves, and what moved is the number of call
sites and the shape of the single-siting claim.

- **Existing patterns reused.** None to introduce. The audit *verified* reuse, and the
  verification is the matrix. Three obligations are satisfied one level deeper than the
  spec described — `D7` through `_model_write_step` rather than
  `_full_clean_or_field_errors` / `save_or_field_errors` directly, `D6` through the
  bind-declared `EXCLUDED` field kind rather than a decode parameter, `D3 / P4`'s
  normalization one frame up in `_declare_auth_surface` — and in every case the reuse is
  stronger, not weaker, than the sentence claimed.
- **New helpers justified.** None. A docs-only pass; the slice writes no `.py`.
- **Duplication risk avoided.** Two, both real. (1) The transport contract: four
  sections in this slice's scope carried a transport claim (`## Edge cases`'s anonymous
  logout, sessionless, and async-contexts bullets, and `## Out of scope`'s Channels
  bullet). Every one now **points at** Decision 11 and states none of its own, so
  Slice 5 writes it once — the fence Slice 2 set for Decisions 2 / 4 / 5, extended to
  the sections. (2) The privilege rejection: Slice 3 put it in Decision 6, and its
  `## Edge cases` home omitted it. Stating it twice in full would have been the
  duplication, so the edge case states the rule and names the module-level protected set
  without re-deriving Decision 6's two-layer argument.

### Implementation steps

1. Re-verify the spec's status/header lines (`docs/SPECS/spec-040-auth_mutations-0_0_13.md:1-111`).
2. Copy the spec's `## Definition of done` items verbatim as `- [ ]` boxes (this slice
   audits no `## Slice checklist` block of its own); tick only what `HEAD` proves.
3. Decompose the seven in-scope sections into individual normative statements; grade each
   against source read directly.
4. Grade every `## Test plan` row three ways: does a test exist, does it assert what the
   row claims, and **would it fail if the behaviour were removed?**
5. Sweep every symbol named by an obligation (above); a dangling name is `SPEC-STALE`,
   restated by the invariant it protects.
6. Edit the spec for every `SPEC-STALE` row; append the explanation to the rationale
   companion, keyed by spec heading and anchor.
7. Record every `CODE-GAP` / `TEST-GAP` without touching source or tests.
8. Discharge the seven items Slices 2 and 3 handed forward; route what belongs to Slice 5.

Line numbers in this artifact are pin-at-write-time navigational hints (per-cycle
scratchpad; raw `path:NN` is permitted here and nowhere else).

### Test additions / updates

None — this pass writes no test. The three `TEST-GAP` rows below specify tests for the
code-fix cohort to write; this slice may not write them. Focused read-only run performed
as evidence:

- `uv run pytest tests/auth examples/fakeshop/test_query/test_auth_api.py --no-cov -q`
  → **210 passed** in 9.48s (8 workers). No `--cov*` flag.

### Implementation discretion items

None. Every verdict below is decided.

### Spec slice checklist (verbatim)

This slice audits no `## Slice checklist` block of its own, so the spec's
`## Definition of done` items stand in, copied verbatim as `- [ ]` boxes. A box is
ticked only where the contract it states is proved to hold at `HEAD` by the cited
symbol-qualified path. Items 1 and 7 are quoted **post-edit** — the corrected text is
the contract this slice audits against, and each correction is recorded under
`### Spec changes made (Worker 1 only)`.

**Spec + companion CSV**

- [x] 1. `docs/spec-040-auth_mutations-0_0_13.md` (this document; archived post-ship to
      `docs/SPECS/spec-040-auth_mutations-0_0_13.md`) and its companion
      `spec-040-auth_mutations-0_0_13-terms.csv` exist — the companion archived to
      `docs/SPECS/appx/` per `AGENTS.md` rule 26, alongside the rationale companion
      `…-rationale.md`;
      `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-040-auth_mutations-0_0_13.md`
      reports `OK: <N> terms`.

      *Proof:* all three files exist at the stated paths
      (`docs/SPECS/spec-040-auth_mutations-0_0_13.md`,
      `docs/SPECS/appx/spec-040-auth_mutations-0_0_13-terms.csv`,
      `docs/SPECS/appx/spec-040-auth_mutations-0_0_13-rationale.md`); the gate returns
      `OK: 30 terms - all have glossary entries and at least one spec link.` (exit 0),
      re-run after this slice's edits.

**Slice 1 — auth substrate + `login` / `logout`, earned live**

- [x] 2. `django_strawberry_framework/auth/` ships `login_mutation()` /
      `logout_mutation()` as field factories with the declaration ledger,
      `bind_auth_mutations()` wired into `types/finalizer.py` phase 2.5 in the pinned
      slot (pre-bind reset loop → `bind_auth_mutations()` → `bind_mutations()` →
      `bind_form_mutations()`), `LoginPayload` / `LogoutPayload` materialized through the
      ONE `build_payload_type` builder onto the existing `mutations.inputs` emit ledger —
      **surface-keyed: each payload only when its surface was declared** — (no new
      pre-bind `register_subsystem_clear` row in Slice 1), the auth **declaration** ledger
      cleared by a full-clear-only `register_subsystem_clear` row beside
      `clear_mutation_registry` / `clear_form_mutation_registry` (no `before_bind`), the
      login / logout permission holders (pinned `__name__`s `Login` / `Session`) reusing
      `authorize_or_raise` / `check_permission` by call, the **surface-keyed** user-model
      primary-type bind validation for the Slice-1-declarable surfaces (the login arm's
      auth-specific message; the logout-only exemption binding with no user type and
      resolving no primary) — with the bind ordering wired so the Slice-2 register /
      `current_user` arms are reachable when those factories land (their coverage is DoD
      items 4–5, **not** this one), the AllowAny default (the empty permission-class list
      via `unset_default=()` — no `AllowAny` class exists or is added) +
      `permission_classes=` seam through the standard `check_permission` machinery (the
      conflict / cache key being `permission_classes` alone — presentation kwargs
      excluded), and sync + async resolver pairs over `django.contrib.auth` — failed
      authentication returning the ONE `"__all__"`-keyed `FieldError`. **In the same
      commit**, the fakeshop `accounts` surface exposes `login` / `logout`,
      `"apps.accounts.schema"` joins `schema_reload.py`'s `_PROJECT_APP_SCHEMA_MODULES`
      (so the complete-reload fixtures preserve the auth surface after a
      `registry.clear()`), and `test_query/test_auth_api.py` earns every reachable branch
      live.

      *Proof:* graded in full by Slice 2's 63-row matrix (rows D3.1-D3.4, D5.1-D5.20,
      D9.1-D9.15), which found **0 `CODE-GAP`**. Re-confirmed here at the seams this
      slice's obligations touch: `types/finalizer.py:1077-1097` runs
      `iter_subsystem_clears(before_bind=True)` → `bind_auth()` → `bind_mutations()` →
      `bind_form_mutations()` in that literal order;
      `auth/mutations.py::bind_auth_mutations` materializes each payload under a
      `by_surface.get(...) is not None` arm and resolves the primary only when
      `user_typed` is non-empty;
      `auth/mutations.py #"register_subsystem_clear(clear_auth_mutation_registry, owner="auth.declarations")"`
      passes no `before_bind`; `::_declare_auth_surface #"unset_default=()"`;
      `rg "AllowAny" django_strawberry_framework/` → 0 hits.

- [x] 3. `tests/auth/test_mutations.py` mirrors the module for the package-only residue
      (ledger, bind validation, post-finalize raise, async, sessionless,
      `SyncMisuseError`).

      *Proof:* 97 test functions; one row per named item —
      `::test_same_args_factory_calls_dedupe_to_one_cached_holder` /
      `::test_registry_clear_drains_ledger_and_resets_conflict_state` (ledger),
      `::test_login_only_schema_without_user_type_raises_the_login_arm_error` /
      `::test_logout_only_schema_binds_with_no_user_type_and_no_orphan_payloads` (bind
      validation), `::test_factory_after_finalize_raises_the_standing_configuration_error`
      (post-finalize), `::test_async_login_and_logout_run_in_one_sync_boundary` (async),
      `::test_sessionless_request_surfaces_djangos_own_error` (sessionless — see
      **TG-0** below: the row exists and is named correctly by this DoD item, but its
      assertion is non-distinguishing),
      `::test_async_has_permission_raises_sync_misuse_never_a_silent_allow`
      (`SyncMisuseError`). Ticked because the box's contract is that the file *mirrors*
      the module for that residue, which it does; the strength of one of those rows is a
      `## Test plan` finding, recorded as `TG-0`.

**Slice 2 — `register` + `current_user`, earned live**

- [x] 4. `register_mutation()` synthesizes the cached `Register` rider (`__name__ =
      "Register"`, so the unchanged machinery emits `RegisterPayload` — there is no
      payload-name seam; `DjangoMutation` rider: `create` over `get_user_model()`,
      `Meta.fields = (USERNAME_FIELD, *REQUIRED_FIELDS, "password")` via the
      directly-testable `derive_register_fields(user_model)` helper (delegating
      unknown-field rejection to `editable_input_fields`) with `email` optional per
      `input_field_required`, `RegisterInput` via the input-name seam, privilege columns
      structurally absent) — **overriding `resolve_sync` AND `resolve_async`** to ride
      `run_write_pipeline_sync` with the password-aware step pair (the `decode_step`
      returns `(user, m2m_assignments, exclude, raw_password)` with `password` captured
      through the provided-marker-preserving exclusion seam — the AR-H2 exclude
      calculation still counts it as provided; the `write_step` runs
      `validate_password(raw_password, user)` → `set_password(raw_password)` →
      `full_clean()` → `save()`; the `036` pipeline exposes no per-instance write hook),
      plaintext never persisted **on either path** (asserted: model decode never receives
      `password`), a **conflicting second call with a different `permission_classes`
      raising `ConfigurationError`**, and **every same-`permission_classes` factory call
      re-registering the cached rider into the mutation ledger** (identity-deduped,
      reload-safe) — exposed through the unchanged `DjangoMutationField`, with the `036`
      payload re-fetch (by pk, no visibility filter, G2-gated). `current_user()` returns
      the nullable session actor without a `get_queryset` re-run. **In the same commit**,
      the live suite covers the register → login → `me` → logout round trip, the
      duplicate-username and weak-password envelopes, the hashed-storage assertion, and
      anonymous `me: null`.

      *Proof:* graded step by step by Slice 3's 91-row matrix at the release tree, **0
      `CODE-GAP`**. Re-confirmed at the seams this slice touches:
      `auth/mutations.py::_synthesize_register_rider` (the `Register` class body, its
      `input_type_name` / `build_input` / `resolve_sync` / `resolve_async` overrides),
      `::_register_decode_step` (the extended four-tuple), `::_register_write_step`
      (`set_password` before the shared tail), `::register_mutation` (the double
      re-record). Live rows:
      `test_auth_api.py::test_register_login_me_logout_round_trip_and_hashed_storage`,
      `::test_duplicate_username_register_envelope_keys_to_username`,
      `::test_weak_password_register_envelope_keys_to_password_not_all`,
      `::test_anonymous_me_is_null_not_an_error`.

      One clause is **weaker than the box reads** and is graded in the matrix rather than
      un-ticking: "privilege columns structurally absent" is true for the stock model and
      is backed for a custom one by an explicit `ConfigurationError`
      (`::_REGISTER_PROTECTED_FIELDS`), which Slice 3 folded into Decision 6. The
      contract landed; the DoD sentence describes only its structural half.

- [x] 5. `tests/auth/` covers the internals residue (factory cache, the
      reload-idempotence cycle with `register` present in the second schema and a prior
      conflicting-`permission_classes` raise not surviving the clear, the register-arm /
      current-user-arm no-`UserType` error messages — pinned distinct from login's, the
      coverage moved here from Slice 1 — plus the register-only / current-user-only
      surface-keyed binds, `derive_register_fields` custom user-model field-set derivation
      (a test-scoped model, no `AUTH_USER_MODEL` swap), the exclusion-seam provided-marker
      test, validator-mapping shapes, hash-ordering, the sync + async
      plaintext-never-persisted pair, lazy-user forcing, and the `me` / `register` gate
      variants on isolated throwaway schemas).

      *Proof, one row per named item:*
      `tests/auth/test_mutations.py::test_register_factory_recache_and_reregister_on_every_call`
      (cache), `::test_reload_idempotence_cycle_rebuilds_the_full_auth_surface` +
      `::test_register_arm_error_survives_a_reload_cycle` +
      `::test_registry_clear_drains_ledger_and_resets_conflict_state` (reload cycle and
      the conflict reset), `::test_register_only_schema_without_user_type_raises_the_register_arm_error`
      and `tests/auth/test_queries.py::test_current_user_only_schema_without_user_type_raises_its_own_arm`
      (the two distinct arms),
      `::test_register_only_surface_keyed_bind_emits_no_login_logout_payloads` +
      `test_queries.py::test_current_user_only_bind_emits_no_login_logout_payloads`
      (surface-keyed binds),
      `::test_derive_register_fields_custom_username_and_required_fields` (custom model),
      `::test_exclusion_seam_captures_password_and_preserves_the_provided_marker`
      (provided marker),
      `::test_weak_password_register_envelope_keys_to_password_not_all` (validator
      mapping), `::test_sync_register_never_persists_the_plaintext_and_hashes_before_full_clean`
      + `::test_async_register_never_persists_the_plaintext` (the sync/async pair and the
      hash ordering),
      `test_queries.py::test_async_gated_me_forces_the_lazy_user_inside_the_one_sync_boundary`
      (lazy-user forcing), `::test_gated_register_denies_with_the_standard_create_string`
      + `test_queries.py::test_gated_me_denies_the_anonymous_caller_with_the_exact_pinned_string`
      (gate variants).

**Cross-cutting — no regression**

- [ ] 6. The full suite is green at the 100% coverage gate (`fail_under = 100`);
      `ruff format` + `ruff check` are clean; the `036` / `038` / `039` mutation surfaces
      and the read side are unchanged. Every Helper-reuse obligation (the helper-reuse
      review's D1–D19 / P1–P4 / D-N1–D-N3 directives) is satisfied — the auth code routes
      through the named write-stack / `utils/` helpers and does not re-spell them, and the
      three deliberate non-reuse points carry their source comment.

      **Not ticked, for two independent reasons, one of which is a real gap.**

      (a) The coverage half is **not verifiable by any worker**: `docs/builder/BUILD.md`
      `## Coverage is the maintainer's gate, not a worker's tool` forbids every `--cov*`
      flag in every pass. Recorded, not deferred — it is the maintainer's gate by
      construction.

      (b) The last clause is **false at `HEAD` and was false at the cut**:
      `rg -n 'D-N1|D-N2|D-N3' django_strawberry_framework/` returns three hits, and none
      of them is `D-N3` (`auth/queries.py:8` and `auth/mutations.py:616` are `D-N1`;
      `auth/mutations.py:1109` is `D-N2`).
      `git show 3a294082:django_strawberry_framework/auth/mutations.py | grep -n 'D-N'`
      returns the same two, so the `D-N3` comment was **never written**. Recorded as
      **CG-1** below; the spec is right and the tree is short, so the box stays open
      rather than the contract being weakened to match.

      The obligations half is otherwise proved by the 40-row obligations block of the
      matrix: the enumeration `D1–D19 / P1–P4 / D-N1–D-N3` was counted member by member
      against the section (19 `D` labels across 18 bullets, `P1`–`P4`, `D-N1`–`D-N3`) and
      is exact.

**Slice 3 — docs + the `0.0.13` version cut + card wrap**

- [x] 7. The version quintet **moved to `0.0.13` at this card's cut** — all five members
      (`pyproject.toml`, `__version__`, `tests/base/test_init.py::test_version`, the
      GLOSSARY version line, the `uv.lock` package entry) read `0.0.13` at the release
      commit; later cards move them on, so this item is a claim about the cut, never about
      `HEAD`. The Auth mutations GLOSSARY entry is `shipped (0.0.13)` with the implemented
      contract; the `039`-deferred flips land (`SerializerMutation` → `shipped (0.0.13)`,
      `docs/README.md` / `README.md` "Shipped today" + Status → `0.0.13`); `TODAY.md` /
      `GOAL.md` / `docs/TREE.md` updated as pinned in Doc updates; `CHANGELOG.md` carries
      the `0.0.13` bullets **only under an explicit maintainer instruction**; `KANBAN.md`
      records `DONE-040-0.0.13` with this spec as its `SpecDoc` (DB edit + re-render).

      *Proof:* Slice 3 audited this item read-only at `3a294082 Release 0.0.13` and found
      **all five quintet members reading `0.0.13` and every `039`-deferred joint-cut flip
      landed** — its Slice-3 checklist block is 6 of 6 with symbol-qualified proofs.
      `KANBAN.md:2141` / `:2234`-style Done rows confirm the card wrap survives at `HEAD`
      (`DONE-040-0.0.13`). The item is ticked against the cut, which is what it now says
      it claims; the pre-edit present tense was false at any later `HEAD` and is the
      reason for the edit.

**Tick count: 6 of 7.** One box (item 6) stays `- [ ]`; its deferral reason is recorded
under `### Spec changes made (Worker 1 only)` and its code half is `CG-1`.

### Conformance matrix

One row per normative statement, decomposed to the individual statement level.
Verdicts: `CONFORMS` / `SPEC-STALE` (code right, spec moves) / `CODE-GAP` (spec right,
code moves) / `TEST-GAP` (both right, nothing pins it) / `UNPROVABLE`.

#### `## Slice checklist` — the post-ship blockquote (3 rows)

| # | Claim (spec, quoted) | Settling citation | Verdict |
|---|---|---|---|
| SC.1 | "the `- [ ]` boxes below are preserved as-authored and are intentionally not toggled here" | every box in the section is `- [ ]`; the convention matches `START.md` #"boxes stay unticked; Status = truth" | `CONFORMS` |
| SC.2 | the completion record "lives in the build artifacts (`docs/builder/bld-slice-*.md`, `bld-integration.md`, `bld-final.md`)" | `git ls-tree --name-only 3a294082 docs/builder/` lists `build-040-auth_mutations-0_0_13.md` + `bld-slice-1-auth_substrate_login_logout.md` / `bld-slice-2-register_current_user.md` / `bld-slice-3-docs_version_cut_wrap.md` / `bld-integration.md` / `bld-final.md`; `git log --oneline --diff-filter=D --all -- 'docs/builder/build-040-auth_mutations-0_0_13.md'` → `ed2693f9` deleted them at the `spec-041` cycle's pre-flight reset, and nothing was moved to `docs/builder/DONE/` (`git log --all -- 'docs/builder/DONE/build-040*'` → empty) | **`SPEC-STALE`** |
| SC.3 | "all slices are `final-accepted` per the status line at the top of this document" | spec line 71 reads `**SHIPPED (0.0.13) — all slices final-accepted; …**` | `CONFORMS` |

**SC.2 — what the spec should say instead** (and now does, `spec-040:241-254`): the
record was retired with the cycle and survives only in git history at `3a294082`, named
with the `git show <commit>:<path>` form `START.md` prescribes — **plus** an explicit
warning not to read the unprefixed `bld-*.md` files in the working tree as this card's
record. The sharper half of this row is not that the pointer dangles but that it does
**not**: `docs/builder/` is reused by whichever cycle is active, so
`bld-slice-1-argument_normalization.md` … `bld-final.md` exist today and describe the
concurrent `spec-050` card. A reader following the old pointer would have found a
complete-looking build for the wrong card, with no signal.

#### `## Implementation plan` (6 rows)

| # | Claim | Settling citation | Verdict |
|---|---|---|---|
| IP.1 | "Slices 1 and 2 each land package code **and its live fakeshop surface in one commit**" | Slice 2's and Slice 3's checklist audits both proved the same-commit landing at the release tree | `CONFORMS` |
| IP.2 | "Line deltas are planning estimates" / "Total expected delta: ~`+940 / -60`" | self-labelled as estimates; an intent statement, not a measurement of the shipped tree | `CONFORMS` |
| IP.3 | Slice 1 touches `examples/fakeshop/config/settings.py` to install the app | `examples/fakeshop/config/settings.py:80` — `"apps.accounts.apps.AccountsConfig"` | `CONFORMS` |
| IP.4 | Slice 1's accounts app is "`Query.me`-less for now" | `examples/fakeshop/apps/accounts/schema.py::Query` carries `me` today; the claim is scoped to Slice 1 and Slice 2's own row adds it | `CONFORMS` |
| IP.5 | Slice 2 pins "the `RegisterInput` input-name-seam override" | `::_synthesize_register_rider` → `Register.input_type_name` / `Register.build_input` re-pin `_REGISTER_INPUT_NAME` | `CONFORMS` |
| IP.6 | "Staged-but-not-implemented seams follow the `AGENTS.md` design-doc anchor discipline (a source-site `TODO(spec-040 Slice N)` comment naming this spec, removed in the slice that ships it)" | `rg -n 'TODO\(spec-040' .` → 2 hits, both prose (this very sentence, and a rationale bullet recording an anchor's discharge); `rg -n 'TODO-(ALPHA\|BETA\|STABLE)-040' .` excluding the board files → 2 hits, both prose in rationale companions. **Zero staged anchors survive in source, tests or comments.** | `CONFORMS` |

#### `## Helper-reuse obligations (DRY)` (40 rows)

| # | Claim | Settling citation | Verdict |
|---|---|---|---|
| H.1 | section lead-in: "each item is single-sited in the decision it cross-references" | all 18 bullets carry a `[Decision N](#…)` cross-reference; no item states a contract without one | `CONFORMS` |
| H.2 | lead-in: "The three `D-N*` items … carry a source comment" | `rg -n 'D-N1\|D-N2\|D-N3' django_strawberry_framework/` → 3 hits, **none** `D-N3`; same at `3a294082` | **`CODE-GAP`** (CG-1) |
| D1 | every auth resolver reads the request via `request_from_info(info, family_label=_AUTH_FAMILY_LABEL)`, one shared label constant, never a re-spelled `info.context.request` walk | `auth/mutations.py::_AUTH_FAMILY_LABEL` (one definition) consumed by `::_transport_prologue`, `::_login_resolve_body_async`, `::_logout_resolve_body_async`, `queries.py::_current_user_resolve_body`; `rg "context.request" django_strawberry_framework/auth/` → 0 hits | `CONFORMS` |
| D2 | the async-permission-hook guard (`reject_async_in_sync_context` + `_PERMISSION_ASYNC_RECOURSE`) is reused **by call** through the bound `check_permission`; no new recourse string | `::_make_permission_holder #"check_permission": DjangoMutation.check_permission`; `mutations/sets.py::DjangoMutation.check_permission` → `run_permission_classes` → `mutations/permissions.py::_require_sync_bool_auth_result #"recourse=_PERMISSION_ASYNC_RECOURSE"`; `rg "recourse" django_strawberry_framework/auth/` → 0 hits | `CONFORMS` |
| D3/P4.a | the permission holder binds `DjangoMutation.check_permission` | `::_make_permission_holder` class dict | `CONFORMS` |
| D3/P4.b | it builds `_mutation_meta` via `_validate_permission_classes(..., unset_default=())` | `::_declare_auth_surface #"_validate_permission_classes(label, permission_classes, unset_default=())"` normalizes one frame up and the normalized tuple is what `::_AuthMutationMetaSnapshot` is constructed from; the reuse is intact, one call site for all four surfaces | `CONFORMS` |
| D3/P4.c | "synthesized by ONE `_make_permission_holder(...)` helper, not three class bodies" | `rg -n '_make_permission_holder' django_strawberry_framework/` → 3 hits: the `def`, a docstring, and the single `lambda` call in `::_declare_fixed_auth_surface`. One synthesis site for `Login` / `Session` / `CurrentUser`. (The elided argument list is why this item, unlike Decision 5's D5.14 sentence, did not go stale on the signature change) | `CONFORMS` |
| D4 | all four surfaces gate through `authorize_or_raise`; the denial message rides the existing `_primary_type` / holder-`__name__` fallback, no auth-specific formatter | `auth/mutations.py:632` (login), `:819` (logout), `queries.py:88` (current_user), and `mutations/resolvers.py:276` inside `run_write_pipeline_sync` (register); `rg "Not authorized" django_strawberry_framework/auth/` → 0 hits | `CONFORMS` |
| D5.a | `LoginPayload` / `LogoutPayload` via `build_payload_type` + `payload_object_slot` on the existing `mutations.inputs` emit ledger | `::bind_auth_mutations #"object_slot=payload_object_slot(primary)"` and `#"build_payload_type("Logout", object_type=None, object_slot=None)"`, each followed by `materialize_mutation_input_class` | `CONFORMS` |
| D5.b | "no new clear row" for the payloads | no `register_subsystem_clear` call under `auth/` other than the declaration row and the `current_user` alias row (D15) | `CONFORMS` |
| D5.c | "`RegisterPayload` never named explicitly" | `rg -n 'RegisterPayload' django_strawberry_framework/` → 5 hits, **all** in comments/docstrings; no string literal in executable code. The name derives from `Register.__name__` | `CONFORMS` |
| D6.a | register's decode reuses the ONE shared decode spine rather than forking a second decoder | `::_register_decode_step` calls `mutations/resolvers.py::_model_decode_step`, which reaches `utils/write_values.py`'s `iter_provided_input_fields` UNSET-strip walk; no auth-local decoder exists | `CONFORMS` |
| D6.b | "threads `excluded_input_fields={"password"}` through `_model_decode_step` / `_decode_relations`" | `rg -c --glob '*.py' excluded_input_fields .` → **0** across the whole tree. The mechanism is a bind-time `EXCLUDED` field kind: `::Register.build_input #"excluded_attrs=_REGISTER_EXCLUDED_INPUT_FIELDS"` → `mutations/inputs.py:554 #"kind = EXCLUDED if python_name in excluded"` → `mutations/resolvers.py:439 #"EXCLUDED: decoded_into(excluded_values, _model_excluded_decode)"` | **`SPEC-STALE`** |
| D6.c | "with the provided-marker preserved (the AR-H2 `_unprovided_exclude` calculation still counts `password` as provided)" | `mutations/resolvers.py:888 #"exclude = _unprovided_exclude(model, provided)"` with the EXCLUDED values folded into `provided`; pinned by `tests/auth/test_mutations.py::test_exclusion_seam_captures_password_and_preserves_the_provided_marker` | `CONFORMS` |
| D7.a | the `write_step` "delegates `full_clean()` / `save()` / `IntegrityError` to the shared path (`_full_clean_or_field_errors` / `save_or_field_errors`)" | `::_register_write_step #"return resolvers._model_write_step(instance, (user, m2m_assignments, exclude))"` — the delegate is `_model_write_step`, which is what calls `_full_clean_or_field_errors` (`mutations/resolvers.py:922`) and `save_or_field_errors`. The reuse is one level deeper than stated, and stronger (M2M rides it too) | **`SPEC-STALE`** |
| D7.b | "only `validate_password` + `set_password` are auth-specific" | `::_register_write_step` also runs a three-guard password preflight — `None`, non-`str`, and `unencodable_text_error("password", raw_password)` — added by `a6f5a6cb` / `a8f31a2d`. The preflight is itself the shared write-side primitive, so the DRY claim survives; the enumeration does not | **`SPEC-STALE`** |
| D8.a | "register's password error uses `field_error("password", …)` directly" | `::_register_write_step #"return [resolvers.field_error("password", exc.messages, codes=codes)]"` | `CONFORMS` |
| D8.b | "`login`'s failure error uses `field_error("", …)` (empty path → `NON_FIELD_ERROR_KEY`)" | `::_failed_login_payload #"resolvers.field_error("", _INCORRECT_CREDENTIALS_MESSAGE)"` | `CONFORMS` |
| D8.c | "neither hard-codes `"__all__"`" | `rg -n '"__all__"' django_strawberry_framework/auth/` → 3 hits, **all** in docstrings explaining the sentinel; zero in executable code | `CONFORMS` |
| D9.a | "register's re-fetch rides the inherited `refetch_optimized`" | `::_run_register_pipeline_sync` rides `run_write_pipeline_sync` unchanged, whose `mutations/resolvers.py:330` calls `refetch_optimized`; `rg "refetch_optimized" django_strawberry_framework/auth/` → 1 hit, a docstring | `CONFORMS` |
| D9.b | "`login` / `current_user` do no queryset work" | `::_login_result_payload` returns the raw `authenticate()` instance; `queries.py::_current_user_resolve_body` returns `_authenticated_actor_or_none(request)`. No manager, queryset, or `get_queryset` call on either path | `CONFORMS` |
| D10/D11 | "`RegisterInput` is named via the `input_type_name` / `build_input` seams and materialized via the inherited `materialize_mutation_input_class`; no new input namespace for register" | `::Register.input_type_name` returns `_REGISTER_INPUT_NAME`; `::Register.build_input` re-pins the shape's `type_name` and calls `materialize_mutation_input_class`; `rg "make_input_namespace" django_strawberry_framework/auth/` → 1 hit, in `queries.py` for the `current_user` alias only | `CONFORMS` |
| D12/P1/P2.a | "the lazy return refs are built by `_lazy_ref`" | `auth/mutations.py:997` / `:1025` and `queries.py:117`, all `_lazy_ref(...)` from `mutations/fields.py:154` | `CONFORMS` |
| D12/P1/P2.b | "the field-dispatcher construction is single-sited in ONE auth helper" | `::_make_auth_field` is the only construction site; `login_mutation`, `logout_mutation` and `queries.py::current_user` each call it once. **Re-graded directly against `::_make_auth_field` per Slice 3's hand-off item 6, not against Decision 7's text.** The obligation claims single-siting of the *dispatcher construction*, which holds; Decision 7's stale sentence claimed single-siting of the whole "resolve-request → gate → session-work → inject-signature" dispatcher, which never did. The two are different claims and only the Decision's was wrong — Slice 3 corrected it, and no obligations-side edit is owed | `CONFORMS` |
| D12/P1/P2.c | "`_lazy_ref` + the `__signature__` / `__annotations__` injection are promoted to shared machinery" | `::_make_auth_field #"signature, annotations = build_lazy_field_signature(arguments, return_annotation)"` — the promoted helper lives in `mutations/fields.py` and is shared with `DjangoMutationField` | `CONFORMS` |
| D13 | the `CurrentUserAlias` namespace is owned by a `make_input_namespace` trio (its `materialize_fn` pins the alias, its `clear_fn` is the `register_subsystem_clear` row); no hand-rolled `setattr` / `delattr` | `queries.py:48-52` unpacks the trio; `rg "setattr\|delattr" django_strawberry_framework/auth/` → 0 hits. Pinned by `tests/auth/test_queries.py::test_alias_namespace_rides_make_input_namespace_and_the_pre_bind_row` | `CONFORMS` |
| D14 | the auth declaration ledger is a `make_declaration_registry("AuthMutation")` instance; every-call re-record on both ledgers via `.register` | `::_auth_declaration_registry = make_declaration_registry(_AUTH_FAMILY_LABEL)` with `_AUTH_FAMILY_LABEL == "AuthMutation"`; `::register_mutation` calls `record_mutation_declaration(rider_cls)` **and** `register_auth_mutation(rider_cls)` on every call | `CONFORMS` |
| D15.a | the current_user alias's `register_subsystem_clear` row carries `before_bind=True` | `queries.py:60-64` | `CONFORMS` |
| D15.b | the auth declaration ledger's row carries no `before_bind`, beside the mutation / form declaration clears | `auth/mutations.py #"register_subsystem_clear(clear_auth_mutation_registry, owner="auth.declarations")"`; `registry.py` defaults it `False`. Pinned by `::test_declarations_survive_the_pre_bind_reset` | `CONFORMS` |
| D16.a | `bind_auth_mutations()` resolves the primary via `registry.get(get_user_model())`, "the same getter `_resolve_primary_type` uses" | `::_resolve_user_primary_or_raise #"primary = registry.get(user_model)"`; `mutations/sets.py::_resolve_primary_type` uses the same getter | `CONFORMS` |
| D16.b | "`registry.types_for` is consulted only to split no-type vs ambiguous-type messages" | `::_resolve_user_primary_or_raise #"if registry.types_for(user_model):"` — reached only after `primary is None`, and only to choose between the two messages | `CONFORMS` |
| D17/P3.a | "the async fields wrap gate-then-work in ONE `sync_to_async(thread_sensitive=True)` boundary" | counted per async path at `HEAD` (Slice 2's D10.2 row, re-confirmed): `current_user` 1, login Django-HTTP 1, login Channels-HTTP 1, logout Django-HTTP 1, logout Channels 1, register rider 1. The gate is inside the boundary on every one | `CONFORMS` |
| D17/P3.b | "single-sited across the three" | `_resolve_auth_async`, the one shared auth async helper, was deleted by `c8346750`. Six auth sites now call `run_in_one_sync_boundary` directly: `::_sync_bridged_async_body:393`, `::_login_resolve_body_async:771` and `:778`, `::_logout_resolve_body_async:966` and `:967`, `::Register.resolve_async:1259`. Also "the three" undercounts: four auth surfaces have async paths | **`SPEC-STALE`** |
| D17/P3.c | "that boundary is the generic `run_in_one_sync_boundary` primitive shared with the `036` wrapper rather than an auth-local copy" | `rg "sync_to_async" django_strawberry_framework/auth/` → **0** hits; the primitive is defined once at `utils/querysets.py::run_in_one_sync_boundary` and imported by `schema.py`, `permissions.py`, `filters/sets.py`, `orders/sets.py`, `mutations/resolvers.py` and `auth/mutations.py`. The no-copy half holds and is now stated with the home Slice 2's Decision 10 edit pinned; "shared with the `036` wrapper" understates a far wider reuse | **`SPEC-STALE`** (folded into the D17.b edit) |
| D18 | "any async-callable detection uses `is_async_callable`" | `rg "iscoroutinefunction" django_strawberry_framework/auth/` → 0 hits. Auth has **no** such call site: `::_authenticated_actor_or_none` inspects a *result* with `inspect.isawaitable`, the case Decision 10 explicitly carves out. **Vacuously satisfied** | **`SPEC-STALE`** (the wording, not the constraint) |
| D19 | "`SyncMisuseError` is imported from its public path, never redefined" | `rg "SyncMisuseError" django_strawberry_framework/auth/` → 2 docstring mentions, 0 definitions, 0 imports. "Never redefined" holds; "is imported from its public path" asserts an import that does not exist, because the guards raising it are reused by call | **`SPEC-STALE`** (same edit) |
| D-N1 | "`current_user` / `login` must NOT scope through `get_queryset` / the visibility helpers (they return the actor, not a lookup)" | `rg "get_queryset\|apply_type_visibility" django_strawberry_framework/auth/*.py` → 3 hits, all docstrings stating the non-reuse. Carries its source comment (`queries.py:8`, `mutations.py:616`). Pinned by `tests/auth/test_queries.py::test_me_composes_with_login_in_one_schema_without_visibility_rerun` | `CONFORMS` |
| D-N2 | "register's password error must NOT route through `validation_error_to_field_errors`" | `rg "validation_error_to_field_errors" django_strawberry_framework/auth/` → 1 hit, the `::_register_write_step` docstring stating the non-reuse; the code keys directly. Carries its source comment (`mutations.py:1109`). Pinned by `::test_weak_password_register_envelope_keys_to_password_not_all` and `::test_dict_form_validator_error_still_keys_to_password_not_a_crash` | `CONFORMS` |
| D-N3.a | "register wires none of the relation-visibility helpers" | no relation-visibility helper is imported or called anywhere under `auth/`; the rider inherits the shared decode's handling | `CONFORMS` |
| D-N3.b | reason clause: "(the narrowed `Meta.fields` has no relation inputs)" | contradicted by `## Edge cases and constraints` #"a `REQUIRED_FIELDS` entry that is a forward FK becomes the standard `<field>_id` input" — true for a custom model, and `derive_register_fields` takes the model as an argument. Both sentences cannot hold | **`SPEC-STALE`** |

**What the spec should say instead:**

- **D6.b** — the exclusion is a **bind-declared `EXCLUDED` field kind**, stashed by the
  rider's `build_input` seam and honoured by the ONE shared decode spine; the invariant
  (one decoder, raw value never a constructed model attr, provided-marker preserved) is
  what the item pins. Written at `spec-040:1778-1785`.
- **D7.a / D7.b** — the delegate is the shared model write tail `_model_write_step`
  (which is what calls `_full_clean_or_field_errors` / `save_or_field_errors` / M2M), and
  the auth-specific steps are exactly the password preflight, `validate_password` and
  `set_password`. Written at `spec-040:1786-1792`.
- **D17.b / D17.c** — no auth module spells `sync_to_async`; every auth async path reaches
  the boundary through the generic primitive, whose home is `utils/querysets.py`; the
  invariant is the **count, not the call site** — one resolution, one boundary, gate
  inside — and re-introducing an auth-local wrapper would be a second definition of the
  discipline rather than a reuse of it. Written at `spec-040:1825-1835`.
- **D18 / D19** — restated as the **prohibitions** they are, with the vacuity stated
  outright, so a later audit does not read the missing import as a violation. Ruling on
  Slice 2's hand-off item 12: an obligation with no call site **stays**, because it
  constrains what the surface may do and is cheapest to keep while nothing exercises it.
  Written at `spec-040:1836-1843`.
- **D-N3.b** — the false reason clause is dropped; the item states that the rider inherits
  the shared decode's relation handling and adds nothing of its own, which is what keeps
  registration from acquiring a second auth-local visibility rule. Written at
  `spec-040:1851-1857`.

#### `## Edge cases and constraints` (22 rows)

| # | Claim | Settling citation | Verdict |
|---|---|---|---|
| E.1 | "Wrong credentials / unknown user / inactive user. **All three** collapse into the ONE `"__all__"`-keyed envelope entry" | four failure classes reach it at `HEAD` — the storability preflight (`::_login_authenticate #"unencodable_text_error("username", username) is not None"`) is the fourth, and `::test_all_four_failure_classes_share_one_byte_identical_envelope` asserts all four byte-identical | **`SPEC-STALE`** (the count) |
| E.2 | the inactive-user case is covered by `ModelBackend` returning `None` | `test_auth_api.py::test_inactive_user_gets_the_same_envelope` | `CONFORMS` |
| E.3 | "Login while already authenticated" — the three-branch session handling (cycle / flush / retain) | `::_django_http_login_establish` delegates to Django's native `login`; live rows `::test_login_anonymous_to_auth_cycles_key_preserves_anon_data_and_pins_backend`, `::test_login_as_different_user_flushes_old_session_and_data`, `::test_relogin_same_user_matching_hash_retains_the_session_key`, `::test_relogin_same_user_mismatched_hash_flushes_and_replaces` — plus four Channels twins in `tests/auth/` | `CONFORMS` |
| E.4 | "`rotate_token(request)` always runs but rotates the **CSRF** token, not the session key" | Django's own `login`; `::test_login_and_logout_face_djangos_real_csrf_check` exercises the real check live | `CONFORMS` |
| E.5 | "Anonymous logout. `ok: false`, empty errors; `auth.logout` still runs" | `::_logout_observation #"ok = _authenticated_actor_or_none(request) is not None"` and `::_django_http_logout`; but the teardown is `auth.logout` only on Django HTTP — a Channels scope runs `::_channels_logout` under the per-scope lock (`c8346750`) | **`SPEC-STALE`** (one transport's spelling as the contract) |
| E.6 | "idempotent by construction" | `::test_channels_http_anonymous_logout_is_false_but_flushes_residue`, `test_auth_api.py::test_logout_round_trip_and_anonymous_logout` | `CONFORMS` |
| E.7 | "Duplicate username on register" → `USERNAME_FIELD`-keyed `FieldError`, `IntegrityError` fallback through `save_or_field_errors` | `::_register_write_step` → `_model_write_step`; `test_auth_api.py::test_duplicate_username_register_envelope_keys_to_username` | `CONFORMS` |
| E.8 | "Password validator failures" — one `password` key, **not** via `validation_error_to_field_errors` | `::_register_write_step #"return [resolvers.field_error("password", exc.messages, codes=codes)]"`; live `::test_weak_password_register_envelope_keys_to_password_not_all` | `CONFORMS` |
| E.9 | "Custom user models." `USERNAME_FIELD` / `REQUIRED_FIELDS` drive the field set; an FK entry becomes `<field>_id`; `authenticate`'s `username` kwarg maps onto `USERNAME_FIELD` | `::derive_register_fields`; `::_login_authenticate #"auth.authenticate(request, username=username, password=password)"`; `::test_derive_register_fields_custom_username_and_required_fields` | `CONFORMS` |
| E.10 | "`REQUIRED_FIELDS` naming `password`-adjacent or unusable columns" — dedup + `editable_input_fields` delegation, "no silent drops" | both hold (`::derive_register_fields #"deduped = tuple(dict.fromkeys(names))"`, `#"editable_input_fields(user_model, fields=deduped)"`), but the bullet omits the protected-field rejection `a40f0d33` added (`::_REGISTER_PROTECTED_FIELDS`), which Slice 3 folded into Decision 6 and not here | **`SPEC-STALE`** |
| E.11 | "Payload-name collisions." The three payloads + `RegisterInput` materialize through the standard emit ledger; the surface-keyed bind means the collision can fire only when the surface is declared | `::bind_auth_mutations` (each arm guarded); `::test_login_only_bind_emits_no_orphan_logout_payload`, `::test_register_only_surface_keyed_bind_emits_no_login_logout_payloads` | `CONFORMS` |
| E.12 | "One auth surface of each kind per process" — a different-`permission_classes` second call raises | `::_reject_conflicting_permission_classes`; `::test_conflicting_permission_classes_second_call_raises` | `CONFORMS` |
| E.13 | "Factory called after finalization" — the standing raise, for both the ledger factories and the lazy `Register` synthesis | `::test_factory_after_finalize_raises_the_standing_configuration_error` | `CONFORMS` |
| E.14 | "Two calls to the same factory." The key is the normalized `permission_classes` only; presentation kwargs excluded; a same-key call is idempotent | `::_reject_conflicting_permission_classes` docstring + body; `::test_presentation_kwargs_never_enter_the_conflict_key`, `::test_same_args_factory_calls_dedupe_to_one_cached_holder` | `CONFORMS` |
| E.15 | the conflict state "does **not** survive a `registry.clear()`" | `::_declared_auth_surface` reads through `iter_auth_mutations()`; `::test_registry_clear_drains_ledger_and_resets_conflict_state` | `CONFORMS` |
| E.16 | "Password never on the model instance." The raw value travels only as the fourth element of the decoded tuple | `::_register_decode_step #"return user, m2m_assignments, exclude, excluded_values.get("password")"`; `::test_exclusion_seam_captures_password_and_preserves_the_provided_marker` | `CONFORMS` |
| E.17 | "No registered user `DjangoType`." Bind-time raise naming the fix; a logout-only schema is exempt | `::_resolve_user_primary_or_raise` (both messages); `::test_logout_only_schema_binds_with_no_user_type_and_no_orphan_payloads` | `CONFORMS` |
| E.18 | "Sessionless / middleware-less deployments. Django's own error surfaces …; **the package adds no probe**." | `auth/sessions.py::require_session` **is** a probe: it pre-checks `getattr(request, "session", None) is None` before any credential or session work and raises an actionable `ConfigurationError` naming `SessionMiddleware` / `AuthMiddlewareStack`. Added by `c8346750` | **`SPEC-STALE`** |
| E.19 | "The `tests/auth/` sessionless edge pins that the error is Django's, not a swallowed pass." | `::test_sessionless_request_surfaces_djangos_own_error` asserts only `"session" in res.errors[0].message.lower()` — true under Django's raw failure **and** under the package's probe. Non-distinguishing | **`TEST-GAP`** (TG-0) |
| E.20 | "Async contexts. The permission gate **and** the session work run inside one `sync_to_async(thread_sensitive=True)` boundary" | the gate is always inside (`::_login_authenticate` / `::_logout_prologue` / `queries.py::_current_user_resolve_body`), but on a Channels HTTP login the establishment is awaited natively **after** that boundary (`::_login_resolve_body_async #"await _channels_http_login_establish(request, session, user)"`) | **`SPEC-STALE`** |
| E.21 | `current_user` forces the lazy user inside the boundary, including the gate's `instance` argument; an `async def has_permission` still raises `SyncMisuseError` | `queries.py::_current_user_resolve_body` computes `actor` before the gate, inside the bridged body; `::test_async_gated_me_forces_the_lazy_user_inside_the_one_sync_boundary`, `::test_async_permission_hook_rejected_inside_the_sync_worker_too` | `CONFORMS` |
| E.22 | "The register payload under visibility" / "`login` under a consumer permission gate" / "Deep selections under `login { node { … } }`" / "Reload / re-finalize cycles" | `::_run_register_pipeline_sync` (the `036` own-write re-fetch); `::_login_authenticate` gates before `authenticate` (`::test_gated_login_denies_with_the_exact_pinned_string_before_authenticate`); the login node is the raw `authenticate()` instance (`::_login_result_payload`); `::test_reload_idempotence_cycle_rebuilds_the_full_auth_surface`. **The strictness-visibility half of the deep-selection bullet is true by construction and pinned by nothing** — see TG-3 | `CONFORMS` |

**What the spec should say instead:** written at `spec-040:1861-1870` (four failure
classes, with the preflight named), `:1879-1883` (anonymous logout stated
transport-neutrally, pointing at Decision 11), `:1904-1913` (the protected-field
rejection folded into the `REQUIRED_FIELDS` bullet), `:1963-1978` (the session pre-check
stated as what it is, with the test obligation sharpened to the error's class and text),
`:1979-1991` (async contexts restated as the count invariant plus the gate's placement,
pointing at Decisions 10 and 11 for the split).

#### `## Test plan` (24 rows)

| # | Claim | Does a test exist? | Does it assert the claim, and would it fail if the behaviour were removed? | Verdict |
|---|---|---|---|---|
| T.1 | placement lead-in: live-first, `tests/auth/` "holds only what a realistic request cannot drive" | — | The package tier's additions since the cut (`test_sessions.py`, the Channels rows) are all transport / lock / compensation behaviour a fakeshop `/graphql/` request cannot drive. Boundary respected | `CONFORMS` |
| T.2 | "**First-line seed-helper rule.** Every `test_auth_api.py` test opens with `create_users(N)`" | yes | measured: **21 of 21** test functions call `create_users(` within their opening lines; 0 hand-roll a `User` | `CONFORMS` |
| T.3 | login happy path — payload user in the slot, session cookie established, follow-up `me` sees the user | `::test_login_happy_path_sets_session_and_me_sees_the_user` | asserts all three; removing the session establishment drops the follow-up `me`. Strongly pinned | `CONFORMS` |
| T.4 | wrong-password AND unknown-username byte-identical `"__all__"` envelope | `::test_wrong_password_and_unknown_username_return_identical_envelope` | shape equality between two live responses; splitting the message into two would fail it | `CONFORMS` |
| T.5 | inactive user: same envelope | `::test_inactive_user_gets_the_same_envelope` | same equality | `CONFORMS` |
| T.6 | logout `ok: true` then session gone; anonymous logout `ok: false` | `::test_logout_round_trip_and_anonymous_logout` | both halves; inverting the `ok` observation fails it | `CONFORMS` |
| T.7 | register → login → `me` → logout round trip; stored password hashed | `::test_register_login_me_logout_round_trip_and_hashed_storage` | asserts `check_password` true and the raw string absent from the column; removing `set_password` fails it | `CONFORMS` |
| T.8 | duplicate-username keyed to `username`; weak-password keyed to `password`, **not** `"__all__"` | `::test_duplicate_username_register_envelope_keys_to_username`, `::test_weak_password_register_envelope_keys_to_password_not_all` | both assert the key list explicitly; routing through the generic mapper keys to `"__all__"` and fails. Slice 3 counted 2 rows | `CONFORMS` |
| T.9 | anonymous `me: null` | `::test_anonymous_me_is_null_not_an_error` | asserts `null` rather than an error | `CONFORMS` |
| T.10 | "the live suite covers only the canonical default surface" + the placement-exception argument | — | `examples/fakeshop/config/schema.py` composes one aggregate; the one-declaration-per-process rule is enforced by `::_reject_conflicting_permission_classes`. The exception is real, not a convenience | `CONFORMS` |
| T.11 | the complete-reload fixture path preserves the auth surface | `::test_complete_reload_preserves_the_auth_surface` | drives `reload_all_project_app_schemas` and re-queries; dropping `"apps.accounts.schema"` from `_PROJECT_APP_SCHEMA_MODULES` is the documented failure mode it pins | `CONFORMS` |
| T.12 | SDL assertions for the four generated types, with the `node`-vs-`result` slot caveat | `::test_generated_auth_type_shapes` | asserts the field sets, including `"node" not in logout_fields` | `CONFORMS` |
| T.13 | the live enumeration as a whole | — | the section names roughly half of the 21 live rows. Unenumerated and each the sole live pin of a documented behaviour: the four login / re-login branches, three unstorable-credential rows, the similarity rejection, the decode-failure envelope, the dict-form validator error, the real-CSRF row | **`SPEC-STALE`** |
| T.14 | package: ledger mechanics — record / dedupe, declarations survive the pre-bind reset, the reload-idempotence cycle incl. the register arm and the conflict reset, the conflicting-declaration raise keyed on `permission_classes` only | `::test_same_args_factory_calls_dedupe_to_one_cached_holder`, `::test_declarations_survive_the_pre_bind_reset`, `::test_reload_idempotence_cycle_rebuilds_the_full_auth_surface`, `::test_register_arm_error_survives_a_reload_cycle`, `::test_registry_clear_drains_ledger_and_resets_conflict_state`, `::test_conflicting_permission_classes_second_call_raises`, `::test_presentation_kwargs_never_enter_the_conflict_key` | every clause has its own row; Slice 3's boundary reasoning shows the every-call double re-record fails one row per ledger | `CONFORMS` |
| T.15 | package: bind validation, surface-keyed — the no-primary raise fired ahead of `bind_mutations()`, the logout-only exemption, the three distinct arms, the post-finalize raise | `::test_login_only_schema_without_user_type_raises_the_login_arm_error`, `::test_register_only_schema_without_user_type_raises_the_register_arm_error`, `test_queries.py::test_current_user_only_schema_without_user_type_raises_its_own_arm`, `::test_logout_only_schema_binds_with_no_user_type_and_no_orphan_payloads`, `::test_ambiguous_user_primary_raises_the_set_meta_primary_message`, `::test_factory_after_finalize_raises_the_standing_configuration_error` | the arms are asserted distinct from each other and from the generic `_resolve_primary_type` message | `CONFORMS` |
| T.16 | package: permission-gate coverage on isolated throwaway schemas — exact denial strings, the `me` gate, the `data["username"]` gate, the mutation-introspection raise | `::test_gated_login_denies_with_the_exact_pinned_string_before_authenticate`, `::test_gated_logout_denies_with_the_session_holder_string`, `::test_gated_register_denies_with_the_standard_create_string`, `test_queries.py::test_gated_me_denies_the_anonymous_caller_with_the_exact_pinned_string`, `::test_login_gate_sees_the_attempted_username_and_never_the_password`, `::test_gate_introspecting_the_mutation_object_raises_on_the_model_less_fields` | strings asserted verbatim; the password-absence assertion is positive (`"password" not in data`) | `CONFORMS` |
| T.17 | package: the register rider — cache identity, `derive_register_fields` direct for default and custom, the `editable_input_fields` delegation, the exclusion seam, `validate_password` receiving the instance, plaintext-never-persisted on both paths, hash-before-`full_clean` | `::test_register_factory_recache_and_reregister_on_every_call`, `::test_derive_register_fields_default_user_model`, `::test_derive_register_fields_custom_username_and_required_fields`, `::test_derive_register_fields_rejects_unknown_names_via_editable_input_fields`, `::test_exclusion_seam_captures_password_and_preserves_the_provided_marker`, `test_auth_api.py::test_password_similar_to_username_is_rejected_with_user_context`, `::test_sync_register_never_persists_the_plaintext_and_hashes_before_full_clean`, `::test_async_register_never_persists_the_plaintext` | every clause pinned; Slice 3's boundary reasoning shows the hash-ordering swap fails both overrides independently | `CONFORMS` |
| T.18 | package: sync/async — both paths, the one-boundary discipline, the async-`has_permission` rejection, lazy-user forcing, the injected-signature return typing | `::test_async_login_and_logout_run_in_one_sync_boundary`, the four `_sync_boundary_spy` dispatch rows, `::test_async_has_permission_raises_sync_misuse_never_a_silent_allow`, `::test_async_permission_hook_rejected_inside_the_sync_worker_too`, `test_queries.py::test_async_gated_me_forces_the_lazy_user_inside_the_one_sync_boundary`, `::test_injected_return_annotation_resolves_to_the_concrete_user_type` | the spy rows assert the boundary is entered exactly once per resolution, which is the count invariant D17 now states | `CONFORMS` |
| T.19 | package: "the sessionless-request edge (Django's error propagates, not swallowed)" | `::test_sessionless_request_surfaces_djangos_own_error` | the assertion is `"session" in res.errors[0].message.lower()`. It passes whether the package probes or Django fails downstream, and it passed **before** `c8346750` added the probe and **after** — so it distinguishes nothing about the contract it names | **`TEST-GAP`** (TG-0) |
| T.20 | the finalizer's opt-in-preserving reach (Decision 9's `loaded_attr`, added to the spec by Slice 2) | no row | `types/finalizer.py #"bind_auth = loaded_attr("django_strawberry_framework.auth.mutations", "bind_auth_mutations")"` is reachable only through a finalize. `::test_registry_clear_does_not_import_the_auth_subsystem` runs a subprocess that calls `registry.clear()` and nothing else — its docstring claims "the finalizer's bind is guarded on `sys.modules`" but it never finalizes. `tests/utils/test_imports.py` pins `loaded_attr` the helper, never the call site. Replacing the lookup with a plain function-local import keeps every auth row green | **`TEST-GAP`** (TG-1) |
| T.21 | the privilege rejection (Decision 6, added by Slice 3) | one row, helper-level | `::test_derive_register_fields_rejects_privilege_fields` calls `derive_register_fields(PrivilegeRequiredUser)` directly. Deleting the `_REGISTER_PROTECTED_FIELDS` intersection fails exactly **one** row, and nothing proves the raise reaches the consumer through `register_mutation()` | **`TEST-GAP`** (TG-2) |
| T.22 | strictness visibility of deep selections under `me` and under `login { node { … } }` (Decision 7's closing sentence and the `## Edge cases` deep-selection bullet) | no row | every `me` selection in every tree is scalar-only — `rg 'me *\{' examples/fakeshop/test_query/test_auth_api.py tests/auth/*.py` returns exactly three, all `{ me { username } }`; `rg -in 'strict'` across the auth suites and the `accounts` app returns **0**. The fakeshop `UserType` selects `("id", "username", "email")` — no relation exists to select — and `examples/fakeshop/config/schema.py #"_optimizer = DjangoOptimizerExtension()"` constructs `DjangoOptimizerExtension()` at the `strictness="off"` default | **`TEST-GAP`** (TG-3) |
| T.23 | cross-cutting: "the full suite green at `fail_under = 100`" | — | forbidden to this pass (`BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool`) | `UNPROVABLE` |
| T.24 | cross-cutting: "`ruff format` + `ruff check` clean"; "the `036` / `038` / `039` surfaces and the read side unchanged (`tests/mutations/` stays green untouched)" | — | `uv run ruff check <auth surface>` → `All checks passed!`; `uv run ruff format --check <same>` → `14 files already formatted`. The unchanged-surfaces half was proved by the cut's own final gate and is not re-derivable read-only here | `CONFORMS` |

#### `## Doc updates` (8 rows)

| # | Claim | Settling citation | Verdict |
|---|---|---|---|
| DU.1 | "Each slice owns its doc edits"; the `CHANGELOG.md` edit needs an explicit maintainer prompt | the caveat is restated in Slice 3's own bullet and in DoD 7 | `CONFORMS` |
| DU.2 | "Slice 1–2 (inline with code): docstrings + the fakeshop `accounts` app **README** breadcrumbs" | `ls examples/fakeshop/apps/*/README.md` matches **nothing**, at `HEAD` or at `3a294082`, for any app — the example project has no app-level READMEs at all. The breadcrumbs landed in `examples/fakeshop/apps/accounts/schema.py`'s module docstring, which is also what `docs/TREE.md` renders from | **`SPEC-STALE`** |
| DU.3 | "no repo-level doc flips yet (the surface is unreleased mid-card)" | Slice 3 audited the cut and found every flip in Slice 3's commit, none earlier | `CONFORMS` |
| DU.4 | Slice 3: GLOSSARY `Auth mutations` → `shipped (0.0.13)` with the implemented contract, `SerializerMutation` → `shipped (0.0.13)`, version line, Index rows, submodule-exports note | Slice 3's checklist block, 6 of 6 at `3a294082` | `CONFORMS` |
| DU.5 | Slice 3: `docs/README.md` / `README.md` "Coming next" → "Shipped today", Status → `0.0.13` | same | `CONFORMS` |
| DU.6 | Slice 3: `TODAY.md` / `GOAL.md` flips | same | `CONFORMS` |
| DU.7 | Slice 3: `docs/TREE.md` gains `auth/`, `tests/auth/`, the `accounts` app, `test_auth_api.py` | same | `CONFORMS` |
| DU.8 | Slice 3: `KANBAN.md` card wrap via DB edit + re-render, never a hand-edit | `KANBAN.md` carries `DONE-040-0.0.13` with the spec as its `SpecDoc` | `CONFORMS` |

**DU.2 — what the spec should say instead** (and now does, `spec-040:2210-2216`): the
Slice 1–2 doc obligation is docstrings only, the `accounts` app's own module docstrings
carrying the breadcrumbs, with the reason no README is owed. Not a dropped deliverable —
a planning fiction: no fakeshop app has ever had one, and no DoD item rests on it.

#### `## Out of scope (explicitly tracked elsewhere)` (7 rows)

| # | Claim | Settling citation | Verdict |
|---|---|---|---|
| O.1 | Channels ASGI router + websocket/consumer-scope auth — `DjangoGraphQLProtocolRouter` (`TODO-ALPHA-041-0.0.14`) | `KANBAN.md:79` — `DONE-041-0.0.14`, Done. Additionally the "websocket/consumer-scope auth … ports there if at all" half is falsified by `auth/sessions.py`, which classifies and answers per-transport capability inside this card's own module | **`SPEC-STALE`** |
| O.2 | `TestClient` / `GraphQLTestCase` (`TODO-ALPHA-043-0.0.14`); "the live auth tests use the raw Django test client's session support today" | `KANBAN.md:77` — `DONE-043-0.0.14`, Done. The second half still holds: `test_auth_api.py` imports `django.test.Client` | **`SPEC-STALE`** (the card id only) |
| O.3 | Token / JWT auth and password-change / reset — no upstream analog, `BACKLOG.md` material | `rg` under `django_strawberry_framework/auth/` finds no such symbol (Slice 2 row D2.3) | `CONFORMS` |
| O.4 | A package-provided `UserType` default — the consumer declares their own | `examples/fakeshop/apps/accounts/schema.py::UserType` is the consumer's; nothing ships in the package | `CONFORMS` |
| O.5 | A register customization surface — recorded follow-on | no subclassable base or extra-fields seam exists; `DjangoRegisterMutation` is reserved, not shipped (`::_synthesize_register_rider` docstring) | `CONFORMS` |
| O.6 | Field-level read gates (`FieldSet` / per-field permission hooks) — `0.1.1`; `login.node` / `me` to be re-examined when they land | names a version, not a card id, so the `046`→`059` renumber the board catalogues does not rot it | `CONFORMS` |
| O.7 | A new `DjangoType` `Meta` key or settings key | `types/base.py::ALLOWED_META_KEYS` / `::DEFERRED_META_KEYS` carry nothing auth-related; `rg "auth\|session" django_strawberry_framework/conf.py` → 0 (Slice 2 rows D2.4 / D2.5) | `CONFORMS` |

**O.1 / O.2 — what the spec should say instead** (and now does,
`spec-040:2256-2265`): both cards named by their current `DONE-…-0.0.14` ids — the clean
prefix-flip class (c) the `KANBAN.md` catalogue of this defect defines, following the
precedent the `spec-039` residual cycle set. The Channels bullet now carries **no**
transport claim of its own and points at Decision 11, so Slice 5's rewrite needs no
second edit here.

#### `## Definition of done` (12 rows)

| # | Claim | Settling citation | Verdict |
|---|---|---|---|
| DoD.1a | the spec and its `-terms.csv` companion exist | both exist; the CSV at `docs/SPECS/appx/` per `AGENTS.md` rule 26, which item 1 did not name | **`SPEC-STALE`** |
| DoD.1b | `check_spec_glossary.py` reports `OK: <N> terms` | `OK: 30 terms - all have glossary entries and at least one spec link.` (exit 0) | `CONFORMS` |
| DoD.2 | the Slice-1 substrate contract, in full | Slice 2's 63-row matrix, 0 `CODE-GAP`; re-confirmed at this slice's seams (see checklist item 2) | `CONFORMS` |
| DoD.3 | `tests/auth/test_mutations.py` mirrors the module for the named residue | one row per named item (see checklist item 3); the sessionless row's strength is `TG-0`, not a failed mirror | `CONFORMS` |
| DoD.4a | the `Register` rider contract, in full | Slice 3's 91-row matrix, 0 `CODE-GAP` | `CONFORMS` |
| DoD.4b | "privilege columns structurally absent" | true for the stock model; for a custom one the guarantee is the explicit `::_REGISTER_PROTECTED_FIELDS` raise, which Slice 3 added to Decision 6 and which this sentence does not carry | `CONFORMS` (the contract landed; the sentence states only its structural half, already corrected at its Decision home) |
| DoD.5 | `tests/auth/` covers the Slice-2 internals residue | one row per named item (see checklist item 5) | `CONFORMS` |
| DoD.6a | "The full suite is green at the 100% coverage gate (`fail_under = 100`)" | no worker may run a coverage flag | `UNPROVABLE` |
| DoD.6b | "`ruff format` + `ruff check` are clean" | `All checks passed!` / `14 files already formatted` over the auth surface | `CONFORMS` |
| DoD.6c | "Every Helper-reuse obligation (D1–D19 / P1–P4 / D-N1–D-N3) is satisfied — the auth code routes through the named helpers and does not re-spell them" | the enumeration is exact (19 `D` labels across 18 bullets, `P1`–`P4`, `D-N1`–`D-N3`, counted member by member); the routing half is proved by the 40-row obligations block, where every divergence is the spec's description and none is the code re-spelling a helper | `CONFORMS` |
| DoD.6d | "the three deliberate non-reuse points carry their source comment" | only two do; `D-N3`'s was never written, at `HEAD` or at `3a294082` | **`CODE-GAP`** (CG-1) |
| DoD.7 | "The version quintet **reads** `0.0.13`" + the GLOSSARY / README / TODAY / GOAL / TREE / CHANGELOG / KANBAN clauses | every clause verified by Slice 3 read-only at `3a294082` and honoured; but the present tense is false at any later `HEAD`, and `BUILD.md` ``### `## Current state`: observations stand, predictions do not`` gives a DoD item no vintage exemption | **`SPEC-STALE`** (the tense) |

### Verdict tally

Row counts are the `len()` of each block above, re-counted member by member as this
table was written: `## Slice checklist` blockquote = 3, `## Implementation plan` = 6,
`## Helper-reuse obligations (DRY)` = 40, `## Edge cases and constraints` = 22,
`## Test plan` = 24, `## Doc updates` = 8, `## Out of scope` = 7,
`## Definition of done` = 12. Sum: 122.

| Verdict | Rows | Distinct findings |
|---|---|---|
| `CONFORMS` | 93 | — |
| `SPEC-STALE` | 20 | 20 |
| `CODE-GAP` | 2 | **1** (`CG-1`, graded in two sections) |
| `TEST-GAP` | 5 | **4** (`TG-0`–`TG-3`; `TG-0` graded in two sections) |
| `UNPROVABLE` | 2 | 2 |
| **Total rows** | **122** | |

93 + 20 + 2 + 5 + 2 = 122.

Every non-`CONFORMS` row, listed so each count is re-derivable rather than asserted:

- **`SPEC-STALE` (20):** SC.2 · D6.b · D7.a · D7.b · D17/P3.b · D17/P3.c · D18 · D19 ·
  D-N3.b · E.1 · E.5 · E.10 · E.18 · E.20 · T.13 · DU.2 · O.1 · O.2 · DoD.1a · DoD.7.
- **`CODE-GAP` (2 rows, 1 finding):** H.2 and DoD.6d, the section lead-in and the DoD
  item stating the same contract — both `CG-1`.
- **`TEST-GAP` (5 rows, 4 findings):** E.19 and T.19 are the same gap graded at its edge
  case and at its test-plan row (`TG-0`); T.20 is `TG-1`, T.21 is `TG-2`, T.22 is `TG-3`.
- **`UNPROVABLE` (2):** T.23 and DoD.6a, the two halves of the one coverage claim no
  worker may measure.

The 20 `SPEC-STALE` rows are discharged by **16** of the 17 content edits below: four
edits carry two rows each (D7.a + D7.b; D17/P3.b + D17/P3.c; D18 + D19; O.1 + O.2) and
twelve carry one, so 8 + 12 = 20. The seventeenth edit (edit 14) is driven by the
`TEST-GAP` rows rather than by a stale sentence: it writes the three missing rows into
`## Test plan` as contract and sharpens the sessionless row's obligation, so the gaps
have a durable home rather than dying with this artifact.

**Direction of every divergence.** Seventeen of the twenty are post-release movement
(`a6f5a6cb`, `a8f31a2d`, `c8346750`, `31625ac7`, `a40f0d33`, `ed2693f9`, and the two
board lifecycle flips). **Three were inaccurate on their own date** — D-N3.b's reason
clause (contradicted by an edge case authored in the same spec), DU.2's app README (no
fakeshop app has ever had one), and DoD.1a's companion location (`AGENTS.md` rule 26
has always put it under `appx/`). None of the three needed a commit to falsify it, and
each is labelled as such in the companion.

### Boundary-removal reasoning (read-only)

No mutation was applied — this pass may not mutate source. For each boundary a claim
rests on, whether a test would fail if it were removed, by reading. This is the section
the four `TEST-GAP`s come out of.

- **`utils/imports.py::loaded_attr` at the phase-2.5 bind** (T.20). Replacing
  `types/finalizer.py #"bind_auth = loaded_attr(...)"` with
  `from ..auth.mutations import bind_auth_mutations` inside the same function would
  change **no** observable behaviour in any test: every auth test imports the auth module
  by construction, and every non-auth test would now merely import it too, which nothing
  asserts against. **Rows that should fail and do not: zero.** The one row whose docstring
  claims this coverage —
  `tests/auth/test_mutations.py::test_registry_clear_does_not_import_the_auth_subsystem`
  — runs a subprocess that calls `registry.clear()` and asserts the module is absent from
  `sys.modules`; it never calls `finalize_django_types()` or builds a schema, so the
  finalizer's guard is never executed inside it. `tests/utils/test_imports.py`'s four
  `loaded_attr` rows pin the helper's own semantics and say nothing about where it is
  called. Decision 3's structural opt-in would be silently void. **TG-1.**
- **The `_REGISTER_PROTECTED_FIELDS` intersection** (T.21). Deleting it makes
  `derive_register_fields(PrivilegeRequiredUser)` return
  `("username", "is_staff", "password")` instead of raising, failing
  `::test_derive_register_fields_rejects_privilege_fields` — **one row**, at the helper
  level only. Slice 3 recorded this and routed it here. Confirmed: no row drives
  `register_mutation()` against such a model, so nothing proves the raise reaches the
  consumer at declaration time rather than dying inside a helper nobody calls that way.
  **TG-2.**
- **Strictness visibility of deep selections** (T.22). Nothing to remove — the behaviour
  is structural (the actor is a raw, non-optimizer-planned instance, so nested relations
  resolve per-field and the strictness accounting sees them). The gap is that **no query
  anywhere selects a relation under `me` or under `login { node { … } }`, and no auth test
  turns strictness on**, so the claim is pinned by construction alone and a future change
  that routed `me` through a planner would falsify two Decisions with a green suite.
  **TG-3.**
- **`auth/sessions.py::require_session`** (E.19 / T.19). Removing the pre-check restores
  the pre-`c8346750` behaviour: a sessionless request reaches `auth.login` and fails with
  a raw `AttributeError` off a `None` session, whose GraphQL error message also contains
  the substring `"session"`. `::test_sessionless_request_surfaces_djangos_own_error`
  asserts only `"session" in res.errors[0].message.lower()`, so it passes **before and
  after** the boundary exists — an assertion that passes either way, which is worthless
  by `BUILD.md` `## Failability proofs`'s own standard. The test's name and docstring
  additionally assert the **opposite** contract from the one that shipped. **TG-0.**
- **The `EXCLUDED` field kind** (D6.b/c). Removing the `excluded_attrs` argument at
  `::Register.build_input` makes `password` an ordinary scalar spec, so the shared decode
  constructs it onto the model and `::test_exclusion_seam_captures_password_and_preserves_the_provided_marker`
  fails on both of its assertions, with
  `::test_model_decode_step_without_exclusion_keeps_the_historical_three_tuple` guarding
  the tuple-arity side. Strongly pinned — the invariant survived the refactor **and** kept
  its rows.
- **The `_make_auth_field` dispatch split** (D12.b). Collapsing the sync/async split fails
  the four `_sync_boundary_spy` rows plus
  `::test_bridged_async_body_is_a_real_coroutine_function` and
  `::test_auth_field_sdl_signatures_are_unchanged_by_the_dispatch_split`. Strongly pinned.
- **The `unset_default=()` AllowAny default** (D3/P4.b). Changing it to the write family's
  deny-by-default fails every live row in `test_auth_api.py` (all 21 drive the ungated
  surface). Strongly pinned, by a very wide margin.

### Recorded gaps — for the code-fix cohort

**Do not fix these here.** This slice may not touch `.py`. Each is written so a builder
can act on it without this artifact's author. Worker 0 is already holding two confirmed
`.py` items (Slice 3's `F2` and `F3`) for a code-fix cohort; these fold into the same
dispatch. This slice does **not** set `revision-needed` to make that happen.

#### CG-1 — `D-N3` carries no source comment (`CODE-GAP`)

- **Spec claim at stake:** `## Helper-reuse obligations (DRY)` lead-in — "The three
  `D-N*` items are deliberate **non**-reuse … so they carry a source comment" — and
  `## Definition of done` item 6 — "the three deliberate non-reuse points carry their
  source comment".
- **Evidence:** `rg -n 'D-N1|D-N2|D-N3' django_strawberry_framework/` returns three hits,
  none `D-N3` (`auth/queries.py:8` and `auth/mutations.py:616` are `D-N1`;
  `auth/mutations.py:1109` is `D-N2`).
  `git show 3a294082:django_strawberry_framework/auth/mutations.py | grep -n 'D-N'`
  returns the same two, so it was never written — this is a dropped deliverable at the
  cut, not post-ship drift, and the **only** one this cycle's 276 graded rows have found.
- **Severity: Low.** By the letter of `BUILD.md` `## Severity definitions` a spec-contract
  violation is High, but the contract violated here is a **comment obligation with no
  behavioural consequence**, which is exactly Low's "comments or docstrings stale or wrong
  but not load-bearing". The real cost is DoD item 6 being a false completion claim, which
  this artifact fixes by leaving the box open.
- **Smallest faithful fix:** one comment at the site the non-reuse actually applies —
  `django_strawberry_framework/auth/mutations.py::_synthesize_register_rider`, beside the
  `Meta.fields = register_fields` narrowing — naming `D-N3` and stating the invariant in
  the spec's corrected words: the rider wires no relation-visibility helper of its own and
  inherits the shared decode's relation handling, so registration never acquires a second
  auth-local visibility rule. **Do not** instead edit the spec to say "two": that is the
  fix-the-doc-not-the-code shortcut `AGENTS.md` rule 5 forbids.
- **No test is owed.** A comment is not behaviour; `check_citations.py` cannot see it
  (the label is not a `path::Symbol`), so this is exactly the class that rots ungated.

#### TG-0 — the sessionless row asserts nothing distinguishing (`TEST-GAP`)

- **Spec claim at stake:** `## Edge cases and constraints` (the sessionless bullet, as
  corrected by this slice) and `## Test plan`'s package-internal sessionless row.
- **Symbol-qualified path:** `tests/auth/test_mutations.py::test_sessionless_request_surfaces_djangos_own_error`,
  pinning `django_strawberry_framework/auth/sessions.py::require_session`.
- **Evidence:** the only assertion on the error is
  `assert "session" in res.errors[0].message.lower()`, which holds both with the probe and
  with the pre-`c8346750` raw `AttributeError` path. The test's name and docstring assert
  the **superseded** contract ("Django's error propagates … no bespoke probe").
- **Severity: Medium** — a missing test for an important branch, and a name that
  actively misdescribes the shipped boundary.
- **Exact assertion shape:** keep the row's setup (a `RequestFactory().post("/graphql/")`
  with no `SessionMiddleware`), and assert the **class and the text**: that the raised
  error is the package's `ConfigurationError` (or, through `schema.execute_sync`, that
  `res.errors[0].original_error` is one) and that the message names both
  `SessionMiddleware` and `AuthMiddlewareStack`. Rename the row and rewrite its docstring
  to state the shipped contract. Add the Channels-scope twin if `tests/auth/test_sessions.py`
  does not already carry one.
- **Tree:** `tests/auth/test_mutations.py` (beside the existing row).
  `AGENTS.md` rule 10 justification: the fakeshop aggregate always runs with
  `SessionMiddleware` installed, so a sessionless request is not constructible through a
  real `/graphql/` request against it.

#### TG-1 — the finalizer's `loaded_attr` reach is pinned by no test (`TEST-GAP`)

- **Spec claim at stake:** Decision 3's structural opt-in ("the auth module is never
  imported by the package root, so a consumer who doesn't use auth never pays its
  import") and Decision 9 step 2 (the `loaded_attr` reach, added to the spec by Slice 2).
- **Symbol-qualified path:** `django_strawberry_framework/types/finalizer.py #"bind_auth = loaded_attr("django_strawberry_framework.auth.mutations", "bind_auth_mutations")"`.
- **Evidence:** replacing it with a plain function-local import leaves **zero** rows
  failing. `tests/auth/test_mutations.py::test_registry_clear_does_not_import_the_auth_subsystem`
  exercises only `registry.clear()` — its docstring's claim to cover "the finalizer's
  bind" is not performed by its body — and `tests/utils/test_imports.py`'s `loaded_attr`
  rows pin the helper, never the call site.
- **Severity: Medium** — a missing test for an important branch; the boundary it leaves
  unpinned is a documented public contract (a consumer who never imports `auth` must
  never pay `django.contrib.auth`'s import), not merely an internal one.
- **Exact assertion shape:** a subprocess row, modelled on the existing clear-path row so
  the result is deterministic regardless of what the worker already imported. The
  subprocess must: insert `examples/fakeshop` on `sys.path`, set
  `DJANGO_SETTINGS_MODULE=config.settings`, `django.setup()`, declare or import a
  **non-auth** `DjangoType`, call `finalize_django_types()` (or build a `DjangoSchema`
  over a non-auth query), and then
  `assert "django_strawberry_framework.auth.mutations" not in sys.modules`. **The finalize
  call is what makes the row distinguishing** — without it the assertion passes under
  either implementation. Assert the subprocess's return code with its stdout/stderr in the
  failure message, as the existing row does. While there, fix the existing row's docstring:
  it claims a finalize coverage it does not perform.
- **Tree:** `tests/auth/test_mutations.py` (beside `::test_registry_clear_does_not_import_the_auth_subsystem`).
  `AGENTS.md` rule 10 justification: the assertion is about the contents of a **fresh
  process's `sys.modules`**, and the fakeshop aggregate schema composes
  `apps.accounts.schema`, which imports the auth module — so a live `/graphql/` request
  against fakeshop cannot reach this line's negative case at all.

#### TG-2 — the privilege rejection is pinned only at the helper (`TEST-GAP`)

- **Spec claim at stake:** Decision 6's two-layer privilege statement (added by Slice 3)
  and the `## Edge cases` `REQUIRED_FIELDS` bullet (added by this slice).
- **Symbol-qualified path:** `django_strawberry_framework/auth/mutations.py::_REGISTER_PROTECTED_FIELDS`,
  reached from `::derive_register_fields` and, in production, from
  `::_synthesize_register_rider #"register_fields = derive_register_fields(user_model)"`.
- **Evidence:** deleting the intersection fails exactly one row,
  `tests/auth/test_mutations.py::test_derive_register_fields_rejects_privilege_fields`,
  which calls the helper directly. Weakly pinned by `BUILD.md`'s 0-or-1 rule.
- **Severity: Medium** — a missing test for an important branch, and the branch is a
  privilege-escalation guard, so a silent regression exposes `is_staff` / `is_superuser`
  as public registration input.
- **Exact assertion shape:** a second row that drives `register_mutation()` itself.
  Monkeypatch `django_strawberry_framework.auth.mutations.get_user_model` to return a
  test-scoped model whose `REQUIRED_FIELDS` names a protected column (reuse the
  `PrivilegeRequiredUser` shape and `_unique_app_label()` from the existing row), then
  `with pytest.raises(ConfigurationError, match=r"cannot auto-expose protected user
  field\(s\) \['is_staff'\]")`: `register_mutation()`. Assert the raise happens **at the
  factory call**, before any bind. The monkeypatch is licensed here because the spec's own
  test plan rules out the real alternative — "a test-scoped model passed as the argument —
  no second Django project, no `AUTH_USER_MODEL` swap" — and the module-level
  `get_user_model` seam is the narrowest substitute for the argument the rider does not
  take.
- **Tree:** `tests/auth/test_mutations.py` (beside the helper-level row).
  `AGENTS.md` rule 10 justification: fakeshop pins the stock `auth.User`, whose
  `REQUIRED_FIELDS` names no protected column, so the branch is unreachable from any real
  query without swapping the example project's user model.

#### TG-3 — no deep selection under `me` or `login { node { … } }`, and no strictness anywhere (`TEST-GAP`)

- **Spec claim at stake:** Decision 7's closing sentence (an unplanned nested selection
  under `me` is `Strictness mode`-visible like any non-root object) and the `## Edge cases`
  deep-selection bullet for `login { node { … } }`.
- **Symbol-qualified paths:** `django_strawberry_framework/auth/queries.py::_current_user_resolve_body`
  (returns the raw actor) and `django_strawberry_framework/auth/mutations.py::_login_result_payload`
  (returns the raw `authenticate()` instance) — neither is optimizer-planned, which is
  what makes the nested relation strictness-visible.
- **Evidence:** `rg 'me *\{' examples/fakeshop/test_query/test_auth_api.py tests/auth/*.py`
  returns exactly three hits, all `{ me { username } }`; `rg -in 'strict'` across
  `test_auth_api.py`, `tests/auth/*.py` and `examples/fakeshop/apps/accounts/` returns
  **0**. The claim is pinned by construction and nothing else.
- **Severity: Medium** — a missing test for an important branch; two Decisions rest on it,
  and a future change routing `me` or `login.node` through a planner would falsify both
  with a green suite.
- **Exact assertion shape:** build a throwaway schema in the test (the pattern the gate
  rows already use: `registry.clear()`, declare types, finalize) with a user type that
  **selects a relation** — the simplest is a test-scoped `DjangoType` over a model with a
  forward FK, or `auth.User`'s `groups` if the converter accepts it — composed into a
  `DjangoSchema` whose `DjangoOptimizerExtension(strictness="raise")` is armed. Then
  execute `{ me { <relation> { <field> } } }` as an authenticated request and assert the
  strictness diagnostic fires (the raise, with the resolver key naming the relation);
  repeat for `mutation { login(...) { node { <relation> { <field> } } } }`. Two rows, one
  per surface, so they can regress independently.
- **Tree:** `tests/auth/test_queries.py` (the `me` row) and `tests/auth/test_mutations.py`
  (the `login` row). `AGENTS.md` rule 10 justification, and it is load-bearing here
  because the live-first default points the other way: strictness is a
  `DjangoOptimizerExtension(strictness=...)` **construction** argument, and
  `examples/fakeshop/config/schema.py #"_optimizer = DjangoOptimizerExtension()"` constructs `DjangoOptimizerExtension()` at the
  `"off"` default — a live `/graphql/` request cannot turn it on. Separately, the fakeshop
  `UserType` selects `("id", "username", "email")` and deliberately excludes `password`
  and the privilege columns, so there is no relation to select under `me` without widening
  the example's authenticated read surface, which its own module docstring pins as the
  thing it must not do.

### Notes for Worker 1 (spec reconciliation)

**The seven inherited items, discharged.**

1. *(Slice 1 / Slice 2 item 9)* The `## Slice checklist` blockquote's retired-artifact
   pointer. **Done** — row SC.2, spec edit 1. The finding is sharper than "the files were
   retired": `docs/builder/` is reused per cycle, so those exact paths exist today and
   describe the concurrent `spec-050` card, which is why the replacement carries an
   explicit do-not-read clause as well as the `git show 3a294082:<path>` retarget.
2. *(Slice 2 item 10)* The `## Test plan` owes a row pinning the finalizer's `loaded_attr`
   reach. **Done** — row T.20, `TG-1`, and the required row is now spec contract
   (`## Test plan`, package-internal). Confirmed by reading: **0 rows fail** if the lookup
   becomes a plain import, and the one row whose docstring claims that coverage does not
   perform it.
3. *(Slice 2 item 11)* `D17 / P3` vs Decision 10's corrected home. **Done** — rows
   D17/P3.b and D17/P3.c, spec edit 5. The two homes now agree: no auth module spells
   `sync_to_async`, the primitive lives in `utils/querysets.py`, and the invariant is the
   count.
4. *(Slice 2 item 12)* Whether `D18` / `D19`, vacuously satisfied, should still be stated.
   **Ruled: yes, restated as prohibitions** — spec edit 6. A constraint on what the surface
   may do stays live the moment a future edit adds such a site, and the old wording
   (`SyncMisuseError` "**is imported** from its public path") asserted an import that does
   not exist, inviting a later audit to record a violation where there is none.
5. *(Slice 3 item 3)* The `## Test plan` owes a deep `me { … }` selection under strictness.
   **Done** — row T.22, `TG-3`, now spec contract. Two findings the hand-off could not
   have known: the fakeshop `UserType` has **no relation to select**, and the aggregate
   schema runs at `strictness="off"`, so the row is genuinely `tests/auth/` work and the
   spec now records why.
6. *(Slice 3 item 4)* A second row for the privilege rejection. **Done** — row T.21,
   `TG-2`, now spec contract, with the `get_user_model` monkeypatch seam named and
   justified against the spec's own no-`AUTH_USER_MODEL`-swap rule.
7. *(Slice 3 items 5 and 6)* Re-grade `D6` / `D7` and `D12` / `P1` / `P2` against Slice 3's
   edits. **Done.** `D6` and `D7` were both stale and are corrected (spec edits 3 and 4) so
   the obligation and Decision 6 agree. `D12 / P1 / P2` was graded **directly against
   `::_make_auth_field`**, as the hand-off asked, and **conforms**: the obligation claims
   single-siting of the *dispatcher construction*, which holds, while Decision 7's stale
   sentence claimed single-siting of the whole resolve/gate/session/inject dispatcher,
   which never did. Different claims; only the Decision's was wrong, and Slice 3 already
   fixed it. **No obligations-side edit was owed, and none was made** — recorded explicitly
   so a later pass does not read the absence as an unaudited item.

**Hand-offs to Slice 5 (Decision 11 — transport). Decision 11 was not read, edited, or
cited beyond a pointer.**

8. `auth/sessions.py::require_session` now has an `## Edge cases` home that states what it
   does and points here for the per-transport behaviour. Slice 5 owes Decision 11 the
   contract: which transports it accepts a missing session on, the Django-vs-Channels
   `session is None` shapes it collapses, and the `_safe_transport_label` naming in the
   message. The message's substring promise (`"session"`) is stated in the edge case; do
   not restate it in Decision 11, restate only what the edge case points at.
9. The anonymous-logout and async-contexts edge cases now point at Decision 11 for the
   per-transport split (which teardown runs; whether the session work rides the sync
   boundary or is awaited natively after it). Neither carries a transport claim of its own,
   so Slice 5's rewrite needs no second edit to `## Edge cases`.
10. `## Out of scope`'s Channels bullet no longer says the websocket/consumer-scope auth
    story is out of scope — it now scopes itself to the **router card** and defers the
    transport contract to Decision 11. If Slice 5's Decision 11 enumerates per-surface
    transport support, that list is the only place the WebSocket `login` and signed-cookie
    `logout` rejections should appear; Slice 2 already routed both constants
    (`::_WEBSOCKET_LOGIN_UNSUPPORTED`, `::_WEBSOCKET_LOGOUT_UNSUPPORTED`) and their two
    `### Error shapes` rows there, and this slice added neither.
11. Slice 3's item 7 stands unchanged: `current_user` is transport-neutral and belongs in
    Decision 11's per-surface table as "every transport, read-only, no session mutation".
    This slice's E.21 and T.18 rows confirm it — `queries.py` has no transport branch.

**Closed decisions this pass touched prose about, without editing them.**

12. **Decision 1** (Slice 2's, closed) carries `WIP-ALPHA-040-0.0.13` at `spec-040:798`,
    describing how the filename's `NNN` derives from the card. The card is
    `DONE-040-0.0.13` today. It reads as a derivation statement about the naming rather
    than a live lifecycle claim, and it is outside this slice's fence, so **no edit was
    made**. Recorded so the correction is visible rather than an invisible overwrite.
13. The `## Slice checklist`'s Slice-3 card-wrap sub-bullet (`spec-040:403`) reads
    "`WIP-ALPHA-040-0.0.13` → Done with the next `DONE-040-0.0.13` id". This is the
    class-(a) lifecycle-transition shape the `KANBAN.md` catalogue of this defect defines,
    where **neither** prefix is true and a flip falsifies a real record — the fix is
    de-tensing, not flipping. The sub-bullets of `## Slice checklist` are outside this
    slice's fence (only the blockquote is mine), so **no edit was made**. If a later pass
    de-tenses it, `spec-040:59`, `:496` and `:1701` are quotations of `spec-039`'s text and
    must be left verbatim.

**Findings for the maintainer — out of scope for this cycle's edits.**

- **F4 — `docs/GLOSSARY.md`'s auth entry is short of the privilege-rejection correction in
  a second way.** Slice 3's F1 already records that the entry repeats the falsified
  structural-only framing and omits `is_active`. This slice adds that the same entry is now
  also out of step with the `## Edge cases` `REQUIRED_FIELDS` bullet, not only with
  Decision 6 — so whatever change next touches that entry should take both. Still a DB edit
  plus `scripts/build_glossary_md.py`, still outside this cycle's scope fence, still the
  maintainer's.
- **F5 — `tests/auth/test_mutations.py::test_registry_clear_does_not_import_the_auth_subsystem`'s
  docstring asserts coverage its body does not perform.** Carried inside `TG-1` as part of
  that fix, and named separately because it is the instrument-that-lies shape `START.md`
  catalogues: a reader auditing Decision 3 finds a row whose docstring says both paths are
  covered and stops looking. It is the reason this gap survived the `0.0.13` cycle's own
  review.

**Working-tree note (stop-and-report, no action taken).** `git status --short` at the end
of this pass shows fifteen files this slice did not write, all the concurrent `spec-050`
session's: `docs/feedback.md`, `docs/GLOSSARY.md`, `docs/spec-050-list_field_arguments-0_0_15.md`,
`docs/builder/bld-final.md`, `docs/builder/bld-slice-3-sql_and_unit_contracts.md`,
`examples/fakeshop/db.sqlite3`, and nine `.py` files under `django_strawberry_framework/`,
`tests/` and `examples/fakeshop/test_query/`. The set **grew during this pass** (it was
seven at the start), which is itself the signal that it is another session's work in
flight. None is on this slice's writable list and no file in this pass touched any of them
— concurrent maintainer work per `AGENTS.md` rule 34. **Not reverted.** One of them,
`django_strawberry_framework/utils/querysets.py`, hosts `run_in_one_sync_boundary`, which
rows D17/P3.a–c grade; `git diff HEAD -- django_strawberry_framework/utils/querysets.py`
shows the concurrent edit touches neither that function nor any `def` line, so every D17
verdict holds against `HEAD` as well as against the working tree.

### Spec changes made (Worker 1 only)

All in `docs/SPECS/spec-040-auth_mutations-0_0_13.md`; line numbers are post-edit. Every
"why" appended to `docs/SPECS/appx/spec-040-auth_mutations-0_0_13-rationale.md` under the
new `## Spec sections outside the Decisions — changes they underwent`, keyed by spec
heading and anchor exactly as each `### Changes this Decision underwent` is keyed to its
Decision.

| # | Spec lines | Change | Reason |
|---|---|---|---|
| 1 | 241-254 | `## Slice checklist` blockquote: the retired `bld-*.md` pointer replaced by the `git show 3a294082:<path>` retarget naming the five real artifact filenames, plus an explicit "do not read the unprefixed `bld-*.md` files in the working tree as this card's record" | Row SC.2 — the artifacts were deleted at `ed2693f9`, never moved to `DONE/`, and `docs/builder/` is reused per cycle, so the old pointer resolved to another card's build |
| 2 | 2210-2216 | `## Doc updates`: the Slice 1–2 bullet's "`accounts` app README breadcrumbs" replaced by docstrings-only, naming what the docstrings carry and why no README is owed | Row DU.2 — no fakeshop app has ever had a README |
| 3 | 1778-1785 | `D6`: the `excluded_input_fields` parameter replaced by the bind-declared `EXCLUDED` field kind honoured by the ONE shared decode spine, provided-marker clause kept | Row D6.b — `rg` returns 0 for the parameter tree-wide |
| 4 | 1786-1792 | `D7`: the delegate corrected to `_model_write_step` (which calls the two named helpers), and the auth-specific enumeration corrected to preflight + `validate_password` + `set_password` | Rows D7.a, D7.b |
| 5 | 1825-1835 | `D17 / P3`: restated as "no auth module spells `sync_to_async`" + the primitive's `utils/querysets.py` home + the count-not-call-site invariant, with the re-introduction of an auth-local wrapper named as the thing it forbids | Rows D17/P3.b, D17/P3.c (Slice 2 hand-off 11) |
| 6 | 1836-1843 | `D18 / D19`: restated as prohibitions, with the vacuity stated outright | Rows D18, D19 (Slice 2 hand-off 12) |
| 7 | 1851-1857 | `D-N3`: the false reason clause dropped; the invariant restated as inheriting the shared decode's relation handling and adding nothing | Row D-N3.b — the clause contradicted the **Custom user models** edge case |
| 8 | 1861-1870 | `## Edge cases`: three failure classes → four, with the storability preflight named and the byte-identical assertion cited | Row E.1 |
| 9 | 1879-1883 | `## Edge cases`: anonymous logout restated transport-neutrally ("the transport's native teardown"), pointing at Decision 11 | Row E.5 |
| 10 | 1904-1913 | `## Edge cases`: the `REQUIRED_FIELDS` bullet gains the protected-field rejection | Row E.10 |
| 11 | 1963-1978 | `## Edge cases`: the sessionless bullet restated as the pre-check it is, with `current_user`'s exemption, and the test obligation sharpened to the error's class and actionable text | Rows E.18, E.19 |
| 12 | 1979-1991 | `## Edge cases`: async contexts restated as the count invariant + the gate's placement, pointing at Decisions 10 and 11 for the per-transport split | Row E.20 |
| 13 | 2057-2069 | `## Test plan`: the live enumeration completed — the four login / re-login branches, the three unstorable-credential rows, the similarity rejection, the decode-failure envelope, the dict-form validator error, the real-CSRF row | Row T.13 |
| 14 | 2163-2198 | `## Test plan`: the sessionless row's obligation sharpened, and three required rows added as contract — the finalizer's opt-in-preserving reach, the privilege rejection at `register_mutation()`, and the strictness-visible deep selections — each with its tree and the reason live is unreachable | Rows T.19, T.20, T.21, T.22 (`TG-0`–`TG-3`) |
| 15 | 2256-2265 | `## Out of scope`: both card ids flipped to `DONE-041-0.0.14` / `DONE-043-0.0.14`; the Channels bullet scoped to the router card and its transport claim replaced by a pointer to Decision 11 | Rows O.1, O.2 |
| 16 | 2297-2303 | `## Definition of done` item 1: the `appx/` archive location and the rationale companion named | Row DoD.1a |
| 17 | 2403-2407 | `## Definition of done` item 7: the version quintet restated as a claim about the cut, with why it is never a claim about `HEAD` | Row DoD.7 |

**Deferral reason for the one un-ticked checklist box** (`### Spec slice checklist
(verbatim)` item 6, per `ARTIFACT.md`'s one-line-deferral rule): DoD item 6's coverage
clause is structurally unverifiable by any worker (`BUILD.md` `## Coverage is the
maintainer's gate, not a worker's tool`) and its source-comment clause is falsified by
`CG-1`, which is `.py` work this slice may not perform. **Target: the code-fix cohort**
Worker 0 is assembling, which owns `CG-1` alongside Slice 3's `F2` and `F3`.

No link definition was added to the spec: every reference the edits use
(`[glossary-configurationerror]`, `[glossary-djangotype]`, `[glossary-strictness-mode]`,
`[utils-querysets]`, `[utils-typing]`, `[utils-inputs]`, `[mutations-resolvers]`,
`[glossary-syncmisuseerror]`, `[spec-040-rationale]`, `[agents]`, `[config-schema]`,
`[tree]`) was already defined and in use.

Rationale companion: one new top-level section, `## Spec sections outside the Decisions —
changes they underwent`, with seven `###` sub-sections keyed by spec heading and anchor
(`## Slice checklist`, `## Helper-reuse obligations (DRY)`, `## Edge cases and
constraints`, `## Test plan`, `## Doc updates`, `## Out of scope`, `## Definition of
done`). Every entry names what the section claimed, the commit or board change that
falsified it (`a6f5a6cb`, `a8f31a2d`, `c8346750`, `31625ac7`, `a40f0d33`, `ed2693f9`,
`DONE-041-0.0.14`, `DONE-043-0.0.14`), and what it may no longer claim; the three that
were inaccurate on their own date say so explicitly rather than borrowing a commit. The
`D-N3` code gap earns a **deliberately-left-alone** bullet under the Definition-of-done
sub-section, per the companion's own rule that a measured no-change and an unexamined one
read identically otherwise. Three link definitions added: `[agents]` under `<!-- Root -->`
and `[bld-040-slice-4]` under `<!-- docs/builder/ -->` and `[spec-040-helpers]` under
`<!-- docs/SPECS/ -->`, each alphabetical within its group.

**No spec edit touched Decision 11, Decisions 1-10, Decision 12, the `## Slice checklist`
sub-bullets, `## Current state`, `## Borrowing posture`, `## User-facing API`, or
`### Error shapes`.**

---

## Final verification (Worker 1)

No `CODE-GAP` requiring an in-slice fix (the one found is `.py` work routed to the
code-fix cohort per the dispatch's closing rule), so this closes as a Worker-1-only
slice. No Worker 2 or Worker 3 pass is owed **by this slice**.

- **Spec status-line re-verification:** `docs/SPECS/spec-040-auth_mutations-0_0_13.md:1-111`
  re-read at the start of this pass. The `Status:` line
  (`**SHIPPED (0.0.13) — all slices final-accepted; cross-slice integration pass + final
  test-run gate green.**`), the three-slice summary, the owner line, the predecessors
  block, and the rationale-companion pointer Slice 1 added all still describe the build's
  current state. Slice 2's edit 1 already corrected the one falsified header claim (the
  GLOSSARY status). **No header edit was owed and none was made.**
- **Definition-of-done checklist (standing in for the slice checklist):** **6 of 7**
  ticked, each with a symbol-qualified proof. One box left `- [ ]` with its deferral reason
  recorded above.
- **Conformance matrix:** 122 rows — 93 `CONFORMS`, 20 `SPEC-STALE`, 1 `CODE-GAP` (across
  2 rows), 4 `TEST-GAP` (across 5 rows), 2 `UNPROVABLE`. Every `SPEC-STALE` row was
  discharged by an edit in this pass; none was deferred.
- **DRY check across this slice and Slices 1-3:** no new duplication. The transport
  contract stayed single-sited — four sections in this slice's scope carried a transport
  claim and all four now point at Decision 11, extending the fence Slice 2 set for
  Decisions 2 / 4 / 5. The privilege rejection is stated once in full (Decision 6) and once
  by reference (the edge case). The `loaded_attr` contract is stated once (Decision 9, by
  Slice 2) and its test obligation once (`## Test plan`, by this slice).
- **Existing tests still run:**
  `uv run pytest tests/auth examples/fakeshop/test_query/test_auth_api.py --no-cov -q`
  → **210 passed**, 0 failed, 0 errors. No `--cov*` flag.
- **Fail-open shapes:** read the audited surface for the catalogued shapes. Two candidates,
  neither fail-open. `::_authenticated_actor_or_none`'s four narrow `except` arms return
  `None`, which is the **anonymous** — i.e. denied — answer, and every other exception
  propagates (Slice 2 graded this; re-read and confirmed unchanged).
  `sessions.py::require_session` guards on the **answer** (`session is None`) rather than
  on one spelling of a bad request, and its `except BaseException` arm around the
  `getattr` raises rather than permitting. No finding.
- **Hot-path:** the plan declares none by default and this slice changes no executable
  code. **Not applicable; no re-declaration is owed.**
- **Floor verification:** the plan declares none by default, same condition. **No floor
  scope owed by this slice.**
- **Staged-anchor sweep** (`AGENTS.md` rule 26 / `BUILD.md` `## Cross-slice integration
  pass` step 6): `rg -n 'TODO\(spec-040' .` → 2 hits, both prose about the discipline
  (`spec-040:1746` and a rationale bullet recording an anchor's discharge);
  `rg -n 'TODO-(ALPHA|BETA|STABLE)-040' .` excluding `KANBAN.md` / `KANBAN.html` /
  `BACKLOG.md` → 2 hits, both prose in rationale companions. **Nothing is staged.**
- **Gates run:**
  - `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-040-auth_mutations-0_0_13.md`
    → `OK: 30 terms - all have glossary entries and at least one spec link.` (exit 0)
  - In-page anchors, both files: 155 `](#…)` refs in the spec and 78 in the companion, **0
    missing** against the real heading slugs.
  - Reference-style link convention: every `][label]` has a definition and every definition
    a use, in both files; all ten canonical group headers present in both; every definition
    path resolves on disk; new definitions alphabetical within their group.
  - `uvx pre-commit run --files …` — see below.
  - `git status --short` — only files on the writable list, plus the concurrent session's
    baseline-dirty set, untouched.
- **Spec reconciliation:** done in-pass; 17 edits recorded above.
- **Final status:** `final-accepted`.

### Summary

A read-only conformance audit of `spec-040`'s helper-reuse obligations, edge cases, test
plan, definition of done, implementation plan, doc updates, out-of-scope list, and the
`## Slice checklist` blockquote against the shipped tree — 122 rows, the third and last
audit slice of the cycle.

**The `0.0.13` build dropped exactly one thing it planned, and it is a comment.** Across
this cycle's three audit slices and 276 graded rows (63 + 91 + 122), `D-N3`'s source comment is the only
`CODE-GAP`: it was never written, at the cut or since, while the two obligations claiming
all three exist — the section lead-in and DoD item 6 — read as satisfied. Everything else
the spec planned shipped.

**What this slice adds that the other two could not: four `TEST-GAP`s.** The finalizer's
opt-in-preserving `loaded_attr` reach fails **zero** rows if removed, and the one test
whose docstring claims to cover it never finalizes. The sessionless edge is pinned by an
assertion that passes under both the shipped contract and the superseded one, with the
test's own name asserting the superseded one. The privilege rejection is pinned by one
row, at the helper. And the strictness-visibility claim two Decisions rest on is pinned by
nothing at all — every `me` query in every tree is `{ me { username } }`, and strictness
appears in no auth test. All four are now spec contract, with the assertion shape, the
tree, and the live-unreachability reason recorded for the code-fix cohort.

Twenty `SPEC-STALE` rows were discharged by sixteen edits, with a seventeenth writing the
missing test rows into the spec as contract. Seventeen of the twenty ran the cycle's
familiar direction — the code moved after release and the spec did not — and **three were
inaccurate on their own date**: `D-N3`'s reason clause contradicted an edge case authored
in the same document, the Slice 1–2 doc obligation promised an app README no fakeshop app
has ever had, and DoD item 1 named a companion location `AGENTS.md` rule 26 had already
fixed. All seven items Slices 2 and 3 handed forward are discharged, four hand-offs go to
Slice 5, and Decision 11 was never read or edited, so the transport contract still gets
written once.

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
