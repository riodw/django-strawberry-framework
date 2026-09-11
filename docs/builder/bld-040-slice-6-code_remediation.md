# Build: Slice 6 (cohort B) — code remediation

Spec reference: `docs/SPECS/spec-040-auth_mutations-0_0_13.md` (read-only for this cohort; `## Helper-reuse obligations (DRY)` lead-in and `D-N3`; `## Test plan` rows T.19-T.22; `## Definition of done` item 6). Cohort B may **not** write the spec or its rationale companion — cohort A owns both, concurrently.
Status: final-accepted

## Plan (Worker 1)

This is the **only** cohort of the `040` cycle that ships source changes. Seven findings:
one `CODE-GAP` (`CG-1`), four `TEST-GAP`s (`TG-0`-`TG-3`) from
`docs/builder/bld-040-slice-4-audit_obligations_edges_tests.md`, and two
stranded-citation findings (`F2`, `F3`) from
`docs/builder/bld-040-slice-3-audit_register_current_user.md`.

**Every finding was re-verified at HEAD by this pass** (a finding is a hypothesis until
the source is re-read). Nothing was found moot, no severity moved, and one finding grew:
`F3`'s population is three `_bind_mutation` mentions **plus two `_bind_form_mutation`
siblings on adjacent lines of the same two docstrings** — the same removed-symbol rename,
missed by the Slice-3 grep because it searched only the first spelling. Fix both.

**Four of the five test fixes were additionally proven runnable before being planned**
(`START.md` "Test plan can specify an unrunnable test"). The probe scripts are left in
`docs/builder/temp-tests/040-slice-6/` as working recipes; Worker 2 should read them
before writing the permanent rows, and Worker 3 should treat them as evidence the plan
is executable rather than as tests to promote. Two of them changed this plan — see
`### Test additions / updates`, `TG-3`.

### Scope, ownership, and the two hard prohibitions

Writable this cohort (from the build plan's `## Ownership partition for the Slice 5 /
Slice 6 cohorts`): `django_strawberry_framework/auth/mutations.py`,
`django_strawberry_framework/auth/queries.py`,
`django_strawberry_framework/mutations/sets.py`,
`django_strawberry_framework/mutations/resolvers.py`, `tests/auth/test_mutations.py`,
`tests/auth/test_queries.py`, `examples/fakeshop/test_query/test_auth_api.py`, this
artifact, `docs/builder/worker-memory/worker-{1-040-codefix,2-040,3-040}.md`, and
`docs/builder/temp-tests/040-slice-6/`.

1. **Never weaken an assertion to make a test pass, and never change production code to
   satisfy a stale test.** The only production edits this slice authorizes are comments:
   `CG-1`'s new comment plus `F2`/`F3`'s restatements. If a planned row cannot be made to
   pass without a production behaviour change, that is a finding for the integration pass
   recorded under `### Notes for Worker 1 (spec reconciliation)` — not a licence.
2. **No `--cov*` flag in any command** (`docs/builder/BUILD.md` `## Coverage is the
   maintainer's gate, not a worker's tool`). `--no-cov` is required because `pytest.ini`
   auto-applies `--cov`.

`uv run ruff format <files>` / `uv run ruff check --fix <files>` are scoped to this
cohort's own files, **never `.`** — a repo-wide auto-fix would rewrite the concurrent
`spec-050` session's untracked files.

Two files outside the writable list are touched **transiently, by a failability mutation
only** (`TG-1`: `django_strawberry_framework/types/finalizer.py`; `TG-3`:
`django_strawberry_framework/types/resolvers.py`). `docs/builder/BUILD.md`
`## Failability proofs` licenses exactly this, and `scripts/prove_failability.py` restores
and byte-compares each one inside the same pass. **No edit may survive in either file**;
`git status --short` at the end of the pass must not list them. This is recorded here
rather than treated as a silent widening of the partition.

### Hot-path declaration

**None**, per the build plan's `### Slice 6 declarations`, and this pass confirms it: the
only production edits are comments, which change no executed statement (proven by the
inverse proof in `### Failability obligation, per finding`). Every other change is a test
row, and test rows are not on any consumer's hot path.

### Floor-verification scope

**None**, per the build plan's `### Slice 6 declarations`, and this pass confirms it: no
production behaviour changes, so there is no version-dependent seam for a floor run to
exercise.

### DRY analysis

**Helper inventory checked.** Refreshed for the **whole package** (not `utils/` alone) at
this pass via `docs/builder/worker-1.md` `### Package-wide helper inventory before helper
planning`, written to `docs/shadow/helper-inventory-040-slice-6.md` (2,070 lines over
every `django_strawberry_framework/**/*.py`). Shapes searched: `loaded_attr` / `import`,
`subprocess`, `strict`, `protect` / `privileg`, `session`. Relevant candidates found, each
then read at source:

- `django_strawberry_framework/utils/imports.py::loaded_attr` — "Return `module_path`'s
  `attr_name` only when the module is ALREADY loaded"; its three siblings
  (`import_attr_if_importable`, `import_attr`, `require_optional_module`) are the
  alternatives it was chosen over. This is `TG-1`'s boundary, called once, at
  `django_strawberry_framework/types/finalizer.py::finalize_django_types #"bind_auth = loaded_attr("`.
- `django_strawberry_framework/auth/sessions.py::require_session` — `TG-0`'s boundary,
  called once, at `django_strawberry_framework/auth/mutations.py::_transport_prologue`.
- `django_strawberry_framework/auth/mutations.py::_REGISTER_PROTECTED_FIELDS` — `TG-2`'s
  boundary, read once, at `::derive_register_fields`.
- `django_strawberry_framework/types/resolvers.py::_check_n1` — `TG-3`'s boundary; the
  `strictness == "raise"` arm raises `OptimizerError(f"Unplanned N+1: {field_name}{suffix}")`.
- `django_strawberry_framework/mutations/sets.py::bind_write_declarations`,
  `::bind_mutation_outputs`, `::bind_mutations`, and
  `django_strawberry_framework/forms/sets.py::bind_form_mutations` — the real names of the
  seam `F3`'s three docstrings still call `_bind_mutation` / `_bind_form_mutation`.

**No new package helper is proposed or needed.** This slice adds no production logic at
all; the inventory's job here was to find the real symbol names `F3` must restate and to
confirm each `TEST-GAP` boundary is single-sited, which it did on both counts.

**Existing patterns reused (test side).** Four of the five test fixes need an isolated
throwaway schema. **The suite already has that idiom and the plan reuses it by name**
rather than letting a fifth spelling be invented:

- `tests/auth/test_mutations.py::_finalize_schema` — `finalize_django_types()` then
  `DjangoSchema(query=…, mutation=…, error_policy={"enabled": False})`. The masking opt-out
  is load-bearing for `TG-0`, whose assertion reads the real `ConfigurationError` message.
- `tests/auth/test_mutations.py::_login_logout_schema` — declares the user type, builds a
  `login`/`logout` `Mutation`, delegates to `_finalize_schema`. Already carries `declare=`
  and `query_type=` seams.
- `tests/auth/test_mutations.py::_declare_user_type` — already carries a `fields=` seam
  ("the default identity trio, or a `last_login`-exposing variant"), which `TG-3` uses to
  add a relation column without touching any other row.
- `tests/auth/test_queries.py::_me_schema` / `::_declare_user_type` — the same pair for the
  `current_user` surface.
- `tests/auth/test_mutations.py::_unique_app_label` — the per-call `app_label` counter
  `TG-2`'s test-scoped model needs; already used by the existing helper-level row.
- `tests/auth/test_mutations.py` autouse `_isolate_registry` — `registry.clear()` around
  every row. `TG-2` depends on it (`::_declare_auth_surface` caches per-surface, so a
  ledger left live from a prior row would short-circuit `_synthesize_register_rider` and
  the raise would never be reached).
- The **subprocess-isolation idiom** exists twice inside `tests/auth/`:
  `tests/auth/test_mutations.py::test_registry_clear_does_not_import_the_auth_subsystem`
  and `tests/auth/test_sessions.py::test_auth_submodule_import_stays_channels_free`, plus
  near-copies in `tests/base/test_init.py` and
  `tests/rest_framework/test_soft_dependency.py`. There is **no shared helper**; every
  copy spells `subprocess.run([sys.executable, "-c", "import django, os, sys; …"], …)`
  inline.
- `DjangoOptimizerExtension(strictness="raise")` is an **established suite-wide idiom**:
  `rg -n 'strictness="raise"' tests/` returns hits in `tests/test_permissions.py`,
  `tests/test_connection.py`, `tests/test_relay_connection.py`, `tests/optimizer/*`. The
  canonical shape is `strawberry.Schema(query=Q, extensions=[lambda: ext])` over a
  pre-constructed `ext` (`tests/test_permissions.py #"ext = DjangoOptimizerExtension(strictness=\"raise\")"`).
  **`rg -in 'strict'` across `tests/auth/` and `examples/fakeshop/apps/accounts/` still
  returns 0** — the idiom exists, just not in the auth suites, which is exactly `TG-3`.
- **No existing privilege-rejection assertion** beyond the one helper-level row `TG-2`
  names (`::test_derive_register_fields_rejects_privilege_fields`). Confirmed by reading;
  nothing to reuse and nothing to duplicate.

**New shared helper justified: exactly one, file-local.**
`tests/auth/test_mutations.py::_auth_free_subprocess(body)` — single responsibility: run
one `python -c` snippet in a fresh process with `examples/fakeshop` on `sys.path`,
`DJANGO_SETTINGS_MODULE=config.settings`, and `django.setup()` already done, then assert
`returncode == 0` with `stdout`/`stderr` in the failure message. Call sites: the existing
`::test_registry_clear_does_not_import_the_auth_subsystem` (refactored onto it — a
relocation claim, see the proof obligation below) and `TG-1`'s new parametrized row. This
**removes** an in-file near-copy rather than adding one.

It is deliberately **file-local, not hoisted to `tests/auth/_helpers.py`**, because
`_helpers.py` and `conftest.py` are **not on cohort B's writable list**. Hoisting it —
and consolidating the `tests/base/` and `tests/rest_framework/` copies with it — is
recorded in `### Out-of-scope observations` as an integration-pass candidate. Condition
that would justify extracting it later: a third caller outside `tests/auth/test_mutations.py`,
which by construction cannot land in this cohort.

**Duplication risk a naive implementation would introduce, and how the plan prevents it:**

| Risk | Prevention |
|---|---|
| A second inline `subprocess.run([sys.executable, "-c", …])` block in `test_mutations.py` for `TG-1` | `_auth_free_subprocess` above, with the existing row refactored onto it in the same pass |
| A second, differently-spelled throwaway-schema builder for `TG-3` | Extend the **existing** `_finalize_schema` / `_login_logout_schema` / `_me_schema` with one keyword-only `optimizer=None` seam each. No new builder |
| A second privilege-model declaration diverging from `PrivilegeRequiredUser` | `TG-2`'s new row declares the **same shape** beside the existing helper-level row and reuses `_unique_app_label()`; the two rows differ only in what they call (`derive_register_fields` vs `register_mutation`) |
| A hand-rolled `assert "Unplanned N+1" in …` spelled two ways across two files | Both `TG-3` rows assert the **same** two properties in the same order: the message substring `"Unplanned N+1: groups"` and the error `path` (`["me", "groupsConnection"]` / `["login", "node", "groupsConnection"]`) |

**Accepted duplication, named.** `TG-3` needs a registered `DjangoType` over
`django.contrib.auth.models.Group` in **both** `tests/auth/test_queries.py` and
`tests/auth/test_mutations.py`. A shared declaration would have to live in
`tests/auth/_helpers.py`, which this cohort may not write. The two files **already**
carry deliberate per-file copies of `_declare_user_type` for the same reason, and the
repo has a recorded precedent for the call
(`tests/test_permissions.py #"Re-declared locally, matching its sibling hooks above rather than sharing one"`).
So: one five-line `_declare_group_type()` per file, matching each file's existing
`_declare_user_type` spelling. Recorded as an integration-pass consolidation candidate,
not left to Worker 2's discretion.

**Cross-cohort shared shapes: none.** Cohort A writes English about transports in the
spec and its rationale companion; cohort B writes Python comments and test rows. The build
plan already declares this; this pass re-derived it against the two cohorts' file lists and
agrees.

### Implementation steps

Line numbers below are **pin-at-write-time navigational hints** — verify against current
source before editing. This tree is worked concurrently and a raw `path:NN` is valid only
inside this per-cycle artifact (`AGENTS.md` rule 27).

Do the three comment-only findings first (steps 1-3): they are independent, they carry no
failability loop, and landing them first keeps the inverse proof's before/after pair clean
before any test file changes.

#### Step 1 — `CG-1`: give `D-N3` its source comment

`django_strawberry_framework/auth/mutations.py::_synthesize_register_rider` (~1171-1200),
beside the `Meta.fields = register_fields` narrowing inside the synthesized `Register`
class body (~1196).

Add one `#` comment naming `D-N3` and stating the invariant, matching the idiom of the two
comments that already exist (`::_login_authenticate #"(the actor-not-lookup rule, D-N1)"`
and `::_register_write_step #"(the D-N2 deliberate non-reuse:"`). The invariant, in the
spec's corrected words (`docs/SPECS/spec-040-auth_mutations-0_0_13.md:1851-1857`, read-only):
the rider wires **no** relation-visibility helper of its own — the narrowed `Meta.fields`
carries no relation input, and a custom model whose `REQUIRED_FIELDS` names a forward FK
gets the standard `<field>_id` input through the shared decode's own relation handling — so
registration never acquires a second, auth-local visibility rule.

**Do not** "fix" this by editing the spec to say two `D-N` points carry a comment. That is
the fix-the-doc-not-the-code shortcut `AGENTS.md` rule 5 forbids, and the spec is cohort
A's file in any case.

Postcondition: `rg -n 'D-N1|D-N2|D-N3' django_strawberry_framework/` returns **four** hits,
one of them `D-N3`. Record the command and its output in the build report.

#### Step 2 — `F2`: restate five stranded `Revision N` citations as the invariant

`START.md` `## Style Rio cares about` decides the shape: review-round attribution is banned
in code, and "Removed attribution carried the WHY → restate as one plain clause from the
code." So the fix is **not** to re-point these at the rationale companion. A `spec-<NNN>`
decision pointer is explicitly **kept** vocabulary; the `Revision N` half is what must go.
In three of the five sites the WHY is already fully stated by the clause that follows, so
the parenthetical is deleted outright; in the other two the decision pointer is retargeted
to the Decision that actually owns the claim.

| # | Site | Current text | Replacement |
|---|---|---|---|
| 2.1 | `django_strawberry_framework/auth/mutations.py #"the Revision-7 reload"` (module docstring, ~24) | `… same-args cache and conflict state (the Revision-7 reload`<br>`finding): draining it drains the cache, so a post-…` | Delete the parenthetical. The sentence becomes `… same-args cache and conflict state: draining it drains the cache, so a post-``registry.clear()`` re-declaration with different ``permission_classes`` mints a fresh holder / rider instead of tripping a stale conflict raise.` — the WHY was always the clause after the colon |
| 2.2 | `django_strawberry_framework/mutations/resolvers.py #"spec-040 Revision-7 marker fix"` (`::_model_decode_step` docstring, ~861) | `… and silently drop it from the exclude calculation - the`<br>`spec-040 Revision-7 marker fix)` | End the parenthetical at `exclude calculation)`. The `spec-040` pointer is not lost: the same paragraph already opens `Specs with kind ``EXCLUDED`` are the spec-040 D6 exclusion seam` |
| 2.3 | `examples/fakeshop/test_query/test_auth_api.py #"spec-040 Revision 5"` (`::test_weak_password_register_envelope_keys_to_password_not_all` docstring, ~234) | `… keys it to ``password`` directly (spec-040 Revision 5) - asserted …` | `(spec-040 Decision 6)` — Decision 6 is `register_mutation()`'s decision and owns the direct `field_error("password", …)` keying (spec `### Decision 6` at 1088; obligations `D8` / `D-N2`) |
| 2.4 | `examples/fakeshop/test_query/test_auth_api.py #"spec-040 Revision 7 #3"` (`::test_complete_reload_preserves_the_auth_surface` docstring, ~403) | `Pins the ``"apps.accounts.schema"`` ``_PROJECT_APP_SCHEMA_MODULES`` row`<br>`(spec-040 Revision 7 #3): without it a post-clear rebuild raises the …` | Delete the parenthetical; the colon clause already states the WHY in full |
| 2.5 | `tests/auth/test_mutations.py #"spec-040 Revision 4"` (`::test_register_arm_error_survives_a_reload_cycle` docstring, ~637) | `Pins the every-call auth-ledger re-record (spec-040 Revision 4): were the …` | `(spec-040 Decision 8)` — the production code already attributes this exact half to Decision 8: `::register_mutation #"the auth ledger, so the spec-040 Decision 8"` |

Postcondition, run as a **quoted** glob (an unquoted one aborts under zsh and prints
nothing, which reads identically to a clean tree — `START.md` `## Instruments that lie`):
`rg -n --glob '*.py' 'spec-040 Revision|Revision-7 reload' .` returns **0**. Record the
command, the glob quoting, and the count in the build report.

#### Step 3 — `F3`: restate three docstrings by the seam's real symbol

`ab821ae0 refactor: single-site the duplicated class-label, bind, and fetch seams` removed
`_bind_mutation`; `rg -n 'def _bind_mutation' .` confirms it exists nowhere at HEAD.
`_bind_form_mutation` likewise never exists at HEAD. The real symbols, from the helper
inventory and read at source:

- the model-backed drain entry is `django_strawberry_framework/mutations/sets.py::bind_mutations`;
- the model-less drain entry is `django_strawberry_framework/forms/sets.py::bind_form_mutations`;
- the **one** drain both ride, and the caller of the `build_input` seam, is
  `django_strawberry_framework/mutations/sets.py::bind_write_declarations`;
- the payload half is `django_strawberry_framework/mutations/sets.py::bind_mutation_outputs`.

| # | Site | Current | Replacement |
|---|---|---|---|
| 3.1 | `django_strawberry_framework/mutations/sets.py::DjangoMutation.build_input` (~1234) | `The overridable input-materialization seam ``_bind_mutation`` calls at`<br>`phase 2.5.` | `` `_bind_mutation` `` → `` `bind_write_declarations` ``. Verified: `::bind_write_declarations` is what calls `mutation_cls.build_input(meta, object_type)` |
| 3.2 | `django_strawberry_framework/mutations/sets.py::bind_mutation_outputs` (~1649-1652) | `- model-backed (``_bind_mutation``): …`<br>`- model-less (``_bind_form_mutation``): …` | `` `_bind_mutation` `` → `` `bind_mutations` ``; `` `_bind_form_mutation` `` → `` `bind_form_mutations` ``. Both names already appear correctly in the sibling `::bind_write_declarations` docstring, so this makes the two agree |
| 3.3 | `django_strawberry_framework/mutations/resolvers.py::payload_cls_for` (~1260-1261) | `(the ``ModelForm`` via the ``036`` ``_bind_mutation``,`<br>`the plain via ``_bind_form_mutation``)` | Same two substitutions; leave `the ``036``` in place (a `spec-NNN` decision pointer is kept vocabulary and rewriting it is out of scope) |

**`F3`'s population is five mentions across three docstrings, not three mentions.** The
Slice-3 finding counted only the `_bind_mutation` spelling; the two `_bind_form_mutation`
siblings sit on adjacent lines of the same two docstrings and are the same removed-symbol
rename. Fix all five in the same edit.

Postcondition: `rg -n '_bind_mutation|_bind_form_mutation' .` returns only the two
**test names** `tests/mutations/test_sets.py::test_bind_mutation_outputs_stashes_model_less_payload_and_slots`
and `::test_model_and_plain_form_binds_ride_bind_mutation_outputs` — which name the live
`bind_mutation_outputs`, are not the removed symbol, and are **not** cohort B's file.
Record the command and the surviving hits.

#### Step 4 — `TG-0`: make the sessionless rows distinguish the shipped boundary

`tests/auth/test_mutations.py`.

1. **Rewrite `::test_sessionless_request_surfaces_djangos_own_error` in place**: rename it
   to state the shipped contract (suggested
   `::test_sessionless_login_raises_the_configuration_error_naming_both_middlewares`; the
   exact name is Worker 2's, see `### Implementation discretion items`), replace its
   docstring, and strengthen its assertions per `### Test additions / updates`. Keep its
   setup (`RequestFactory().post("/graphql/")` with no `SessionMiddleware`, `request.user = AnonymousUser()`).
2. **Add the logout twin** beside it, driving `_LOGOUT_Q` through the same sessionless
   request. This is not padding: the two rows are what make the boundary pinned rather than
   weakly pinned (see `### Failability obligation, per finding`), and the logout row pins a
   claim nothing else does — `::_transport_prologue`'s own docstring says "logout ignores
   the returned session … but still runs `require_session` for its rejection side effect".
3. **Fix the two surviving statements of the superseded contract in the same file**, both
   of which currently say Django's raw error is what surfaces:
   - the module docstring's `#"the sessionless edge"` clause (~9) — it only names the edge,
     so re-read it and adjust only if the rename leaves it wrong;
   - `::_finalize_schema`'s docstring `#"Django's own sessionless ``AttributeError``"` (~167)
     — this one is flatly falsified by `auth/sessions.py::require_session`. Restate it as
     the package's own `ConfigurationError`. Leave the rest of that docstring (the
     `error_policy={"enabled": False}` justification) untouched; it is still correct and
     `TG-0`'s assertion depends on it.

**Do not** add a Channels-scope twin. `tests/auth/test_sessions.py` already carries four
direct `require_session` rows including the Channels one
(`::test_require_session_none_channels_session_raises`,
`::test_require_session_returns_the_present_channels_session`,
`::test_require_session_missing_django_middleware_raises_with_the_session_substring`,
`::test_require_session_returns_the_present_django_session`), so Slice 4's conditional
"add … if it does not already carry one" resolves to **no**. That file is also not on
cohort B's writable list.

#### Step 5 — `TG-1`: pin the finalizer's already-loaded-only reach

`tests/auth/test_mutations.py`.

1. Extract `_auth_free_subprocess(body: str) -> None` (see `### DRY analysis`) and refactor
   `::test_registry_clear_does_not_import_the_auth_subsystem` onto it. This is a
   **relocation claim** and owes the mechanical proof in
   `docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`:
   the snippet the refactored row sends must reproduce the original's byte-for-byte
   (quote both in the build report).
2. **Fix that row's docstring**: it claims "the finalizer's bind is guarded on `sys.modules`"
   while its body only calls `registry.clear()` and never finalizes. Narrow it to the clear
   half, which is what it actually performs.
3. Add the new parametrized row. Details in `### Test additions / updates`.

#### Step 6 — `TG-2`: pin the privilege rejection at `register_mutation()`

`tests/auth/test_mutations.py`, beside
`::test_derive_register_fields_rejects_privilege_fields`. Details in
`### Test additions / updates`.

#### Step 7 — `TG-3`: a relation under `me` and under `login { node { … } }`, under strictness

`tests/auth/test_queries.py` (the `me` row) and `tests/auth/test_mutations.py` (the `login`
row). Each file gains a local `_declare_group_type()` and an `optimizer=` seam on its
existing schema builder. Details and the verified query shapes in
`### Test additions / updates`.

#### Step 8 — validation

- `uv run ruff format <the files this pass touched>` then `uv run ruff check --fix <the same files>`. **Never `.`**
- `uv run pytest tests/auth/ --no-cov` and
  `uv run pytest examples/fakeshop/test_query/test_auth_api.py --no-cov`
- `git status --short`: every modified file must appear in `### Files touched`. Anything
  else — `docs/feedback.md`, `docs/SPECS/spec-040-*`, the `spec-050` cycle's files — is
  concurrent work: **stop-and-report, never revert** (`AGENTS.md` rule 34).
- The two transiently-mutated files (`types/finalizer.py`, `types/resolvers.py`) must **not**
  appear.

### Test additions / updates

Every row below pins its path, node id, assertion shape, and the tree it belongs in with
the reason. `AGENTS.md` rule 10 and `examples/fakeshop/test_query/README.md`'s coverage
rule make the live tier the first choice; each package-tier placement below therefore
carries a live-**unreachability** argument that this pass **re-verified** rather than
inheriting, because "the fixture cannot reach it" is a fixture gap, not unreachability
(`START.md`).

#### `TG-0` — two rows, `tests/auth/test_mutations.py`

| Node id | Assertion shape |
|---|---|
| `::test_sessionless_login_raises_the_configuration_error_naming_both_middlewares` (renamed from `::test_sessionless_request_surfaces_djangos_own_error`) | Setup unchanged. Then assert **the class and the text**: `isinstance(res.errors[0].original_error, ConfigurationError)` **and** that the message names **both** `"SessionMiddleware"` and `"AuthMiddlewareStack"`. Keep an assertion on the `"session"` substring only as a subordinate check — alone it is the non-distinguishing assertion this finding is about |
| `::test_sessionless_logout_raises_the_configuration_error_naming_both_middlewares` (new) | Same request, `_LOGOUT_Q`, same two assertions. Pins `::_transport_prologue`'s "logout still runs `require_session` for its rejection side effect" claim |

Verified runnable: `docs/builder/temp-tests/040-slice-6/test_probe_tg0.py` and
`…/test_probe_tg0_logout.py`. Both produce
`original_error` = `django_strawberry_framework.exceptions.ConfigurationError` with message
`The auth session boundary has no session for the django_http transport; install Django's
SessionMiddleware (and, for Channels, wrap the scope in AuthMiddlewareStack) so
login/logout can mutate a real session.` **Do not pin the whole message string** — pin the
two middleware names and the class, so a reworded-but-still-correct message does not break
the row while a removed boundary does.

**Tree: package `tests/`, and the live tier is genuinely unreachable.** Re-verified: the
fakeshop aggregate runs `SessionMiddleware` on every `/graphql/` request
(`examples/fakeshop/config/settings.py` `MIDDLEWARE`), and the live tier drives requests
through `django.test.Client`, which cannot omit a configured middleware. A sessionless
request is not constructible against fakeshop without removing middleware from the example
project's settings, which would falsify every other live auth row. This is unreachability,
not a fixture gap.

#### `TG-1` — one parametrized row (2 node ids), `tests/auth/test_mutations.py`

| Node id | Assertion shape |
|---|---|
| `::test_finalize_in_an_auth_free_process_never_imports_the_auth_subsystem[finalize]` | Through `_auth_free_subprocess`: insert `examples/fakeshop` on `sys.path`, `DJANGO_SETTINGS_MODULE=config.settings`, `django.setup()`, declare a **non-auth** `DjangoType` (a `Group`-backed one is fine — it is not the auth *module*), call `finalize_django_types()`, then `assert "django_strawberry_framework.auth.mutations" not in sys.modules, sorted(m for m in sys.modules if "auth" in m)` |
| `::…[schema]` | Same, but the driver is a full `DjangoSchema(query=Q)` build over a non-auth Query after the finalize — the other real consumer entry into phase 2.5 |

**The finalize call is what makes the row distinguishing.** Without it the assertion passes
under either implementation, which is precisely why the existing
`::test_registry_clear_does_not_import_the_auth_subsystem` does not cover this. The
parametrization is **not** padding to reach two rows: the two ids are the two ways a
consumer actually reaches the phase-2.5 bind, they can regress independently, and
`START.md` `## Instruments that lie` requires parametrize rather than a loop precisely so
each is its own node id.

Verified runnable: this pass ran the `[finalize]` body as a bare subprocess and it exits 0
at HEAD (recorded in this artifact's planning notes; Worker 2 re-runs it as a real row).

**Tree: package `tests/`, and the live tier is structurally incapable.** Re-verified: the
assertion is about the contents of a **fresh process's `sys.modules`**, which no
in-request assertion can observe; and the fakeshop aggregate schema composes
`apps.accounts.schema`, which imports the auth module at schema-build time, so the live
process can never exhibit the negative case at all. Unreachability confirmed on both
counts.

#### `TG-2` — one row, `tests/auth/test_mutations.py`

| Node id | Assertion shape |
|---|---|
| `::test_register_mutation_rejects_a_protected_required_field_at_the_factory_call` | Declare a test-scoped `PrivilegeRequiredUser` matching the existing row's shape (`username` / `password` / `is_staff`; `USERNAME_FIELD = "username"`; `REQUIRED_FIELDS = ("is_staff",)`; `app_label = _unique_app_label()`). `monkeypatch.setattr(auth_mutations, "get_user_model", lambda: PrivilegeRequiredUser)`. Then `with pytest.raises(ConfigurationError, match=r"cannot auto-expose protected user field\(s\) \['is_staff'\]")`: `register_mutation()`. Assert the raise happens **at the factory call** — no bind, no finalize, nothing after it in the `with` block |

Verified runnable: `docs/builder/temp-tests/040-slice-6/test_probe_tg2.py` passes at HEAD.
The monkeypatch seam works because `get_user_model` is bound into the module namespace at
`django_strawberry_framework/auth/mutations.py #"from django.contrib.auth import get_user_model"`
and read at `::_synthesize_register_rider #"user_model = get_user_model()"`. The autouse
`_isolate_registry` fixture is required: `::_declare_auth_surface` returns a ledger-cached
class for a repeat declaration, so a live ledger would skip synthesis entirely.

The monkeypatch is licensed here because the spec's own test plan rules out the real
alternative ("a test-scoped model passed as the argument — no second Django project, no
`AUTH_USER_MODEL` swap") and the rider takes no model argument, making the module-level
`get_user_model` the narrowest available substitute (`AGENTS.md` rule 10: mock only when
the real path is impossible, and mock behaviour not the class).

**Tree: package `tests/`.** Re-verified: fakeshop pins the stock `auth.User`
(`examples/fakeshop/config/settings.py` declares no `AUTH_USER_MODEL`), whose
`REQUIRED_FIELDS` is `["email"]` — no protected column — so the branch is unreachable from
any real query without swapping the example project's user model. Unreachability
confirmed.

#### `TG-3` — two rows, one per surface

**This pass's probes changed the planned query shape.** Slice 4 suggested selecting
`auth.User`'s `groups`; the M2M is actually surfaced by the type machinery as
`groupsConnection`, so a literal `{ me { groups { … } } }` is a **GraphQL validation
error**, not a strictness raise — a row that would have looked like it pinned the contract
while pinning a typo. The verified shapes are below.

| Node id | Assertion shape |
|---|---|
| `tests/auth/test_queries.py::test_an_unplanned_relation_under_me_is_strictness_visible` | Declare `_declare_group_type()` (a `DjangoType`/`relay.Node` over `django.contrib.auth.models.Group`, `fields=("id", "name")`) and the user type with `fields=("id", "username", "groups")`. Build the `me` schema with `DjangoOptimizerExtension(strictness="raise")` installed. Seed a user in a group, authenticate through `_session_request(user=…)`, execute `{ me { groupsConnection { edges { node { name } } } } }`. Assert `res.errors is not None`, that `res.errors[0].message` contains `"Unplanned N+1: groups"`, and that `res.errors[0].path == ["me", "groupsConnection"]` |
| `tests/auth/test_mutations.py::test_an_unplanned_relation_under_login_node_is_strictness_visible` | Same declarations via the file's own `_declare_group_type()` and `_declare_user_type(fields=("id", "username", "groups"))`. Build the login/logout schema with the same armed optimizer. Execute `mutation { login(username: …, password: …) { node { groupsConnection { edges { node { name } } } } errors { field } } }` against `_session_request()`. Assert the same message substring and `res.errors[0].path == ["login", "node", "groupsConnection"]` |

Verified runnable: `docs/builder/temp-tests/040-slice-6/test_probe_tg3.py` and
`…/test_probe_tg3_login.py`. Both produce
`GraphQLError('Unplanned N+1: groups (not window-planned; resolving per-parent)')` at
exactly those paths. **Pin the substring `"Unplanned N+1: groups"` and the path, not the
full parenthetical reason** — the reason text is the optimizer's, not auth's, and pinning
it would make an auth row fail on an unrelated optimizer reword.

Two rows, one per surface, so they regress independently (Decision 7's closing sentence and
the `## Edge cases` deep-selection bullet are two separate claims).

**Seams this requires**, each an extension of an existing helper rather than a new one:

- `tests/auth/test_mutations.py::_finalize_schema` — add keyword-only `optimizer=None`;
  when given, pass `extensions=[lambda: optimizer]` to `DjangoSchema`. Thread the same
  kwarg through `::_login_logout_schema`. Every existing caller is unchanged.
- `tests/auth/test_queries.py::_me_schema` — change the signature to
  `def _me_schema(*, optimizer=None, **current_user_kwargs)` and pass `extensions=` the
  same way. **Note the signature hazard**: today it is `_me_schema(**current_user_kwargs)`
  and forwards everything to `current_user(...)`, so `optimizer` must be keyword-only and
  explicitly popped or it would be forwarded into `current_user` and raise.
- `tests/auth/test_queries.py::_declare_user_type` — add a `fields=("id", "username", "email")`
  default seam, mirroring `tests/auth/test_mutations.py::_declare_user_type`, which already
  has one. Existing callers are unchanged.
- One `_declare_group_type()` per file (the accepted duplication named in
  `### DRY analysis`).

**Tree: package `tests/`, and this is the placement where live-first points the other way,
so the argument is load-bearing.** Both halves re-verified at source this pass:

1. **Strictness cannot be armed live.** It is a `DjangoOptimizerExtension(strictness=…)`
   **construction** argument, and `examples/fakeshop/config/schema.py #"_optimizer = DjangoOptimizerExtension()"`
   constructs it at the `"off"` default on a module-level singleton the live tier reuses. A
   `/graphql/` request cannot turn it on; only a differently-constructed schema can.
2. **There is no relation to select live.** `examples/fakeshop/apps/accounts/schema.py::UserType`
   declares `fields = ("id", "username", "email")` and its own docstring pins it as "the
   authenticated read surface" — widening it to expose `groups` would change the example
   project's public authenticated read surface to serve a test, which
   `examples/fakeshop/test_query/README.md` and the module's own docstring both forbid.

Either fact alone makes the live tier unreachable; together they make it unreachable twice.
This is unreachability, not a fixture gap: no fixture change short of rebuilding fakeshop's
schema and widening its auth surface could reach it.

#### Temp / scratch tests for Worker 3

`docs/builder/temp-tests/040-slice-6/` already holds five Worker-1 scratch files:
`test_probe_tg0.py`, `test_probe_tg0_logout.py`, `test_probe_tg2.py`, `test_probe_tg3.py`,
`test_probe_tg3_login.py`, plus the inverse-proof instrument `ast_identity.py`. They are
**planning evidence, not deliverables**: Worker 3 may run them to confirm the plan was
executable, and they are deleted at cycle closeout. Worker 2 owns the manifest at
`docs/builder/temp-tests/040-slice-6/proofs.json`.

### Failability obligation, per finding

The build plan's `### Slice 6 declarations` sets this slice's rule, and this pass confirms
the reasoning: **the slice introduces no new boundary**, so `docs/builder/BUILD.md`'s
new-boundary rule does not fire — but **every `TEST-GAP` fix owes a proof anyway, because
the finding IS that the boundary is unpinned.**

**Mechanism.** `uv run python scripts/prove_failability.py docs/builder/temp-tests/040-slice-6/proofs.json --output <report>`,
with `--scratch-root` pointing **outside** the repository. **Read `--help` for the manifest
schema and the complete list of refused shortcuts**; this plan deliberately does not
restate it. The tool runs the unmutated baseline by default, refuses a row-hiding scope
(`--cov`, `-x`, `--maxfail`), names any live mutation in `ACTIVE-MUTATION.json`, and emits
the `### Failability proofs` block with every measured field filled in. Run it
**per boundary, reverting before the next** — never several mutations at once.

**Acceptance rule Worker 2 must meet, per fix:**

- Mutating the named boundary must fail **2 or more** test rows at the recorded scope,
  counted as **node ids** (`len()` of the listed ids, never an asserted number). **0 or 1
  is weakly pinned and is `revision-needed`** — it means the fix did not close the gap it
  was dispatched against.
- **The dispatched row must itself be in the failing set.** A count of two made up entirely
  of pre-existing rows proves the boundary was already pinned and the new row changed
  nothing. Worker 2 lists the ids; Worker 3 checks the new row's id is among them.
- **Collection / setup errors must be 0.** A proof carrying any is not a valid count at all.
- The revert is proved by byte comparison, and **neither `types/finalizer.py` nor
  `types/resolvers.py` may carry a surviving edit** at the end of the pass.

| Fix | Boundary to mutate | The mutation | Scope as run | Expected failing rows |
|---|---|---|---|---|
| `TG-0` | `django_strawberry_framework/auth/mutations.py::_transport_prologue #"session = sessions.require_session(request, transport)"` | Replace with `session = getattr(request, "session", None)` — the probe is gone from the login/logout path while `::require_session` itself is untouched, so the four direct rows in `tests/auth/test_sessions.py` cannot inflate the count | `uv run pytest tests/auth/ --no-cov` | the two new `TG-0` rows (2) |
| `TG-1` | `django_strawberry_framework/types/finalizer.py::finalize_django_types #"bind_auth = loaded_attr("` | Replace the `loaded_attr` lookup with a plain function-local `from ..auth.mutations import bind_auth_mutations` and call it directly (dropping the `is not None` guard) | `uv run pytest tests/auth/ --no-cov` | both parametrized `TG-1` ids (2) |
| `TG-2` | `django_strawberry_framework/auth/mutations.py::_REGISTER_PROTECTED_FIELDS` | Empty the frozenset (`frozenset()`) — the intersection then never matches and `::derive_register_fields` never raises | `uv run pytest tests/auth/ --no-cov` | the existing `::test_derive_register_fields_rejects_privilege_fields` **and** the new `TG-2` row (2) |
| `TG-3` | `django_strawberry_framework/types/resolvers.py::_check_n1 #"raise OptimizerError(f\"Unplanned N+1: {field_name}{suffix}\")"` | Delete the raise (leave the `"warn"` arm) — strictness `"raise"` becomes silent | `uv run pytest tests/auth/ --no-cov` | the two new `TG-3` rows (2) |

**Scope note.** Every mutation is recorded at `tests/auth/` rather than at a single file,
because `TG-2`'s expected pair spans two rows in one file while `TG-3`'s spans two files;
one scope for all four makes the four records comparable by node-id set. Worker 3 re-runs
**at the scope Worker 2 recorded** and compares id sets, never numbers.

**`CG-1`, `F2` and `F3` owe no failability proof. Do not invent one.** They are
comment-only; a comment is not a boundary and there is nothing to remove. They owe the
**inverse** proof instead (`START.md` `## Instruments that lie`: "Comment/docstring-only
edit owes INVERSE proof: AST identity w/ docstrings stripped"), which is the positive
obligation that replaces it:

For each of the four files whose only change this pass is a comment or docstring —
`django_strawberry_framework/auth/mutations.py`,
`django_strawberry_framework/mutations/sets.py`,
`django_strawberry_framework/mutations/resolvers.py`, and
`examples/fakeshop/test_query/test_auth_api.py` — copy the pre-edit file to a scratch path
**outside** the repository, make the edit, then run:

```shell
uv run python docs/builder/temp-tests/040-slice-6/ast_identity.py <before.py> <after.py>
```

It must print `IDENTICAL` (exit 0). Anything else means the "comment-only" edit changed
executable code, which is `revision-needed`. The instrument was written and verified by
this pass. `tests/auth/test_mutations.py` is **excluded** from this check — it also gains
real test rows, so AST identity cannot hold there by design; say so in the build report
rather than skipping it silently.

### Boundary count

**New boundaries introduced by this slice: zero.** Enumerated: the three comment
restatements add no guard, cap, rejection path, or validation branch; the five test fixes
add rows that *pin* four boundaries that already exist at HEAD
(`::require_session` via `::_transport_prologue`, `::loaded_attr` via
`::finalize_django_types`, `::_REGISTER_PROTECTED_FIELDS`, and `::_check_n1`'s raise). A
test row is not a boundary.

**Split question, answered: one unit.** The trigger `docs/builder/BUILD.md`
`### Slice splitting` actually keys on is the **builder's** load — one mutate / run /
count-rows / revert / byte-compare loop per boundary. Here that is **four** loops (one per
`TEST-GAP`), plus four AST-identity checks that are single commands. Four is under the
"roughly five or more" prompt, and — more to the point — the eight findings are one unit
by content: they are the entire residue of a 276-row audit, they share one review cycle,
and six of the eight touch one file (`tests/auth/test_mutations.py`), so splitting would
hand two builders the same file and destroy the ownership partition the cycle already
declared. The diff is small (three docstring/comment edits, five test rows, four helper
seams) and reviewable in one pass.

The one thing that would change this answer: if Worker 2 finds a planned row needs a
production behaviour change to pass. That is a **stop-and-report** to Worker 0 and a plan
revision, not a licence and not a split performed mid-pass.

### Implementation discretion items

Assessed and decided to belong to Worker 2 — each is a stylistic or naming choice between
equally valid shapes, never an architectural question:

- **The exact renamed node-id text** for `TG-0`'s row and the names of the four new rows,
  provided each states the **shipped** contract and carries no process provenance
  (`START.md` `## Style Rio cares about`: no severity labels, no round or worker
  attribution, no slice numbering in a test name or docstring). The names in
  `### Test additions / updates` are suggestions.
- **`_auth_free_subprocess`'s signature** — whether it takes the snippet as one string or
  as a list of statements it joins, and whether the fakeshop path is computed inside it or
  passed in. Single responsibility is fixed; the spelling is not.
- **The `optimizer=` seam's parameter name** on `_finalize_schema` / `_me_schema`
  (`optimizer=` vs `extension=`), provided the **same** name is used in both files.
- **Whether `TG-1`'s `[schema]` parametrization builds `DjangoSchema` or plain
  `strawberry.Schema`** in the subprocess, provided the finalize actually runs and the
  assertion is on `sys.modules`.
- **Where the two `_declare_group_type()` helpers sit** within their files, and whether the
  `Group` type is Relay-backed, provided both files spell it the same way and the relation
  resolves.
- **Whether `TG-3`'s rows seed one group or several**, provided at least one row exists so
  the relation is non-empty and the resolver is actually entered.

Not discretionary, and stated here so it is not mistaken for style: the **assertion shapes**
in `### Test additions / updates`, the **tree** each row lands in, the **mutation and scope**
in `### Failability obligation, per finding`, and the decision **not** to touch
`tests/auth/_helpers.py`, `tests/auth/conftest.py`, `tests/auth/test_sessions.py`, the spec,
or the rationale companion.

### Out-of-scope observations for the integration pass

Recorded, not acted on. None is a defect this cohort may fix.

- **`spec-042 Revision N` citations in `tests/middleware/test_debug_toolbar.py`** — five
  hits (lines ~21, 111, 475, 509, 523). Same defect shape as `F2`, different spec, different
  owner. **Deliberately out of this population.** Not touched.
- **Bare `Revision N P<n>` citations in `examples/fakeshop/test_query/test_library_api.py`**
  — five hits (~2749, 3830, 3885, 4026, 4041). Same shape again, and that file belongs to
  the **concurrently active `spec-050` cycle**. Not touched, and must not be.
- **`tests/auth/test_sessions.py #"# Revision guards: hostile __class__ and hostile transport.value (hunt 0_0_14 rev)"`**
  — a section comment carrying bug-hunt round provenance, which `START.md`
  `## Style Rio cares about` bans in code. Not in `F2`'s population (it cites no spec) and
  not on cohort B's writable list. For the maintainer.
- **The subprocess-isolation idiom is a four-way near-copy** across
  `tests/auth/test_mutations.py`, `tests/auth/test_sessions.py`, `tests/base/test_init.py`,
  and `tests/rest_framework/test_soft_dependency.py`. This slice consolidates the two
  `tests/auth/test_mutations.py` copies into a file-local helper; hoisting that helper to
  `tests/auth/_helpers.py` and folding in the other two files is an integration-pass
  candidate, blocked here only by the ownership partition.
- **`_declare_user_type` is already duplicated** between `tests/auth/test_mutations.py` and
  `tests/auth/test_queries.py`, and this slice adds a matching `_declare_group_type` pair.
  Same blocker, same candidate.
- **No spec defect was found by this pass.** The `D-N3` wording at
  `docs/SPECS/spec-040-auth_mutations-0_0_13.md:1851-1857` is the contract `CG-1`'s comment
  restates, and it reads correctly at HEAD. Recorded explicitly so a later pass does not
  read the absence as an unaudited item.

### Dispatched findings checklist

One box per finding dispatched to cohort B, quoting the finding as Slice 4 / Slice 3 stated
it, with the symbol-qualified path Worker 0's verification pass recorded. **Boxes stay
`- [ ]` at planning.** Worker 2 ticks `- [x]` only a box whose fix landed in its diff this
pass and states any deferral in the build report rather than ticking; Worker 3 walks the
list (a box the diff does not address with no recorded deferral is a Medium finding, and so
is a box ticked with no matching fix); a later Worker 1 pass audits every tick at final
verification.

- [x] **`CG-1`** (Low, `CODE-GAP`) — "`## Definition of done` item 6 — 'the three deliberate non-reuse points carry their source comment'": only two do; `D-N3`'s was never written, at `HEAD` or at `3a294082`. Fix: one comment at `django_strawberry_framework/auth/mutations.py::_synthesize_register_rider`, beside the `Meta.fields = register_fields` narrowing. Verified at HEAD by this pass: `rg -n 'D-N1|D-N2|D-N3' django_strawberry_framework/` returns three hits (`auth/queries.py`, `auth/mutations.py` ×2) and none is `D-N3`.
- [x] **`TG-0`** (Medium, `TEST-GAP`) — "the only assertion on the error is `assert "session" in res.errors[0].message.lower()`, which holds both with the probe and with the pre-`c8346750` raw `AttributeError` path. The test's name and docstring assert the **superseded** contract". Boundary: `django_strawberry_framework/auth/sessions.py::require_session`, reached at `django_strawberry_framework/auth/mutations.py::_transport_prologue`. Row: `tests/auth/test_mutations.py::test_sessionless_request_surfaces_djangos_own_error`. Verified at HEAD.
- [x] **`TG-1`** (Medium, `TEST-GAP`) — "replacing it with a plain function-local import leaves **zero** rows failing … `::test_registry_clear_does_not_import_the_auth_subsystem` exercises only `registry.clear()` — its docstring's claim to cover 'the finalizer's bind' is not performed by its body". Boundary: `django_strawberry_framework/types/finalizer.py::finalize_django_types #"bind_auth = loaded_attr("`. Verified at HEAD by this pass: the docstring claims the finalizer's bind while the subprocess body never finalizes.
- [x] **`TG-2`** (Medium, `TEST-GAP`) — "deleting the intersection fails exactly one row, `tests/auth/test_mutations.py::test_derive_register_fields_rejects_privilege_fields`, which calls the helper directly. Weakly pinned by `BUILD.md`'s 0-or-1 rule." Boundary: `django_strawberry_framework/auth/mutations.py::_REGISTER_PROTECTED_FIELDS`, reached from `::derive_register_fields` and in production from `::_synthesize_register_rider #"register_fields = derive_register_fields(user_model)"`. Verified at HEAD.
- [x] **`TG-3`** (Medium, `TEST-GAP`) — "no query anywhere selects a relation under `me` or under `login { node { … } }`, and no auth test turns strictness on, so the claim is pinned by construction alone". Boundaries: `django_strawberry_framework/auth/queries.py::_current_user_resolve_body` and `django_strawberry_framework/auth/mutations.py::_login_result_payload` (both return raw, unplanned instances), observed through `django_strawberry_framework/types/resolvers.py::_check_n1`. Verified at HEAD: `rg -in 'strict'` across `tests/auth/` and `examples/fakeshop/apps/accounts/` returns 0.
- [x] **`F2`** — "five `spec-040 Revision N` citations in shipped source and tests now decode against nothing in the spec", because Slice 1 moved the revision history into the rationale companion. Sites: `django_strawberry_framework/auth/mutations.py #"the Revision-7 reload"`; `django_strawberry_framework/mutations/resolvers.py #"spec-040 Revision-7 marker fix"`; `examples/fakeshop/test_query/test_auth_api.py #"spec-040 Revision 5"` and `#"spec-040 Revision 7 #3"`; `tests/auth/test_mutations.py #"spec-040 Revision 4"`. Verified at HEAD by this pass with a quoted glob: exactly those five. Fix shape is set by `START.md` `## Style Rio cares about` — restate the invariant, never retarget at the rationale file.
- [x] **`F3`** — "three `mutations/*.py` docstrings still name the removed `_bind_mutation`", a symbol `ab821ae0 refactor: single-site the duplicated class-label, bind, and fetch seams` deleted. Sites: `django_strawberry_framework/mutations/sets.py::DjangoMutation.build_input`, `django_strawberry_framework/mutations/sets.py::bind_mutation_outputs`, `django_strawberry_framework/mutations/resolvers.py::payload_cls_for`. Verified at HEAD: no `def _bind_mutation` exists anywhere. **Widened by this pass**: the same two docstrings also name `_bind_form_mutation`, equally removed — five mentions in three docstrings, all five in scope.

---

## Build report (Worker 2)

### Files touched

Grounded in `git status --short`, run after both ruff invocations.

- `django_strawberry_framework/auth/mutations.py` — `CG-1`: the `D-N3` source comment beside
  the `Meta.fields = register_fields` narrowing in `::_synthesize_register_rider`. `F2` 2.1:
  the module docstring's `Revision-7 reload` parenthetical deleted (the WHY was always the
  clause after the colon). Comment/docstring only.
- `django_strawberry_framework/mutations/sets.py` — `F3` 3.1 / 3.2: `_bind_mutation` ->
  `bind_write_declarations` in `::DjangoMutation.build_input`; `_bind_mutation` ->
  `bind_mutations` and `_bind_form_mutation` -> `bind_form_mutations` in
  `::bind_mutation_outputs`. Docstring only.
- `django_strawberry_framework/mutations/resolvers.py` — `F2` 2.2: the
  `spec-040 Revision-7 marker fix` parenthetical ended at `exclude calculation)` in
  `::_model_decode_step`. `F3` 3.3: the same two symbol substitutions in `::payload_cls_for`
  (`the ``036``` left in place). Docstring only.
- `examples/fakeshop/test_query/test_auth_api.py` — `F2` 2.3: `(spec-040 Revision 5)` ->
  `(spec-040 Decision 6)`. `F2` 2.4: the `spec-040 Revision 7 #3` parenthetical deleted.
  Docstring only.
- `tests/auth/test_mutations.py` — `F2` 2.5 (`(spec-040 Revision 4)` ->
  `(spec-040 Decision 8)`); `TG-0` (one row rewritten in place, one twin added, plus the two
  surviving statements of the superseded contract); `TG-1` (the `_auth_free_subprocess`
  extraction, the existing subprocess row refactored onto it and its docstring narrowed, and
  the new parametrized row); `TG-2` (one new row); `TG-3` (`_declare_group_type`, the
  `optimizer=` seam on `::_finalize_schema` / `::_login_logout_schema`, and the `login` row).
- `tests/auth/test_queries.py` — `TG-3`: a `fields=` seam on `::_declare_user_type`, a local
  `::_declare_group_type`, `declare=` / `optimizer=` seams on `::_me_schema`, and the `me` row.

**Not touched, and net-zero at the end of the pass:**
`django_strawberry_framework/types/finalizer.py` and
`django_strawberry_framework/types/resolvers.py` carried a transient failability mutation
each, applied and restored inside `scripts/prove_failability.py`. Confirmed:

```shell
$ git diff --stat -- django_strawberry_framework/types/finalizer.py \
      django_strawberry_framework/types/resolvers.py
(no output)
$ git status --short -- django_strawberry_framework/types/
(no output)
```

Neither appears in `git status --short`, and no `ACTIVE-MUTATION.json` marker survives in the
scratch root (only `pristine/` remains).

### Tests added or updated

`TG-0` — `tests/auth/test_mutations.py`

- `::test_sessionless_login_raises_the_configuration_error_naming_both_middlewares` (renamed
  from `::test_sessionless_request_surfaces_djangos_own_error`, setup unchanged) — pins the
  **class** (`isinstance(res.errors[0].original_error, ConfigurationError)`) **and** that the
  message names both `"SessionMiddleware"` and `"AuthMiddlewareStack"`. The old
  `"session" in message.lower()` is kept as a subordinate check; alone it held under the
  superseded raw-`AttributeError` path too, which is the finding.
- `::test_sessionless_logout_raises_the_configuration_error_naming_both_middlewares` (new) —
  same request, `_LOGOUT_Q`, same two assertions. Pins `::_transport_prologue`'s claim that
  logout still runs `require_session` for its rejection side effect alone.
- The two surviving statements of the superseded contract were fixed in the same file:
  `::_finalize_schema`'s docstring now names the package's own `ConfigurationError`
  (`auth/sessions.py::require_session`) instead of "Django's own sessionless
  ``AttributeError``". The module docstring's `#"the sessionless edge"` clause was re-read
  and left as-is: it names the edge only and is not falsified by the rename.

`TG-1` — `tests/auth/test_mutations.py`

- `::test_finalize_in_an_auth_free_process_never_imports_the_auth_subsystem[finalize]` and
  `[schema]` (new, parametrized) — both drive a real consumer entry into phase 2.5 inside a
  fresh process (a bare `finalize_django_types()`, and a full `DjangoSchema(query=Q)` build)
  and then assert `"django_strawberry_framework.auth.mutations" not in sys.modules`, with the
  sorted auth-ish module list as the failure message. The finalize is what makes the row
  distinguishing; parametrized rather than looped so each is its own node id.
- `::test_registry_clear_does_not_import_the_auth_subsystem` refactored onto
  `::_auth_free_subprocess` and its docstring narrowed to the clear half — it claimed to cover
  "the finalizer's bind" while its body only calls `registry.clear()`.

`TG-2` — `tests/auth/test_mutations.py`

- `::test_register_mutation_rejects_a_protected_required_field_at_the_factory_call` (new) —
  a test-scoped `PrivilegeRequiredUser` matching the existing helper-level row's shape and
  `_unique_app_label()`, `monkeypatch.setattr(auth_mutations, "get_user_model", ...)`, and
  `pytest.raises(ConfigurationError, match=...)` around a bare `register_mutation()` with
  nothing after it in the `with` block — so the raise is pinned **at the factory call**, not
  at a later bind or finalize.

`TG-3` — one row per surface

- `tests/auth/test_queries.py::test_an_unplanned_relation_under_me_is_strictness_visible`
- `tests/auth/test_mutations.py::test_an_unplanned_relation_under_login_node_is_strictness_visible`

Both assert the same two properties in the same order: the message substring
`"Unplanned N+1: groups"` and the error `path` (`["me", "groupsConnection"]` /
`["login", "node", "groupsConnection"]`). The plan's verified diagnostic was used verbatim —
the `groups` M2M surfaces as `groupsConnection`, so the literal `{ me { groups { … } } }` the
Slice-4 finding suggested would have been a GraphQL **validation** error and would have passed
as though strictness had fired.

Supporting seams (extensions of existing helpers, no new builder):
`tests/auth/test_mutations.py::_finalize_schema` and `::_login_logout_schema` gained a
keyword-only `optimizer=`; `tests/auth/test_queries.py::_me_schema` gained keyword-only
`declare=` and `optimizer=` (keyword-only and explicitly consumed, or they would be forwarded
into `current_user(...)` and raise); `tests/auth/test_queries.py::_declare_user_type` gained
the `fields=` seam its `test_mutations` twin already had; one five-line `_declare_group_type()`
per file (the accepted per-file duplication the plan named); and
`tests/auth/test_mutations.py::_auth_free_subprocess`, which **removes** an in-file near-copy
rather than adding one.

### Validation run

```shell
$ uv run ruff format django_strawberry_framework/auth/mutations.py \
      django_strawberry_framework/mutations/sets.py \
      django_strawberry_framework/mutations/resolvers.py \
      tests/auth/test_mutations.py tests/auth/test_queries.py \
      examples/fakeshop/test_query/test_auth_api.py
6 files left unchanged

$ uv run ruff check --fix <the same six paths>
All checks passed!

$ uvx pre-commit run --files <the same six paths>
kanban tracked path constants ................ Passed
source layout (py trailing commas + ascii-only; md link-def scaffold; ...) Passed
ruff format .................................. Passed
ruff check ................................... Passed
kanban anchors collision-free ................ Passed
citations resolve (AGENTS.md rule 27) ........ Passed
```

`source-layout` rewrote once on its first invocation (`tests/auth/test_mutations.py:473:
should collapse (< threshold, over-exploded)` — the `@pytest.mark.parametrize` list) and was
re-run until it rewrote nothing; the run above is the stable second run.

**Instrument note.** `uv run ruff format $FILES` with the paths in a shell variable failed
with `No such file or directory (os error 2)`: this shell does not word-split, so the whole
string arrived as one path — and the same invocation of `uvx pre-commit --files $FILES`
reported `ruff format (no files to check) Skipped`, which reads exactly like a clean pass
(`START.md` `## Instruments that lie`, zsh word-splitting). Every command recorded here passes
its paths explicitly.

Focused tests (never any `--cov*` flag; `--no-cov` because `pytest.ini` auto-applies `--cov`):

```shell
$ uv run pytest tests/auth/ --no-cov -q                                  195 passed
$ uv run pytest examples/fakeshop/test_query/test_auth_api.py --no-cov -q  21 passed
$ uv run pytest tests/mutations/ tests/types/ --no-cov -q                939 passed
```

`tests/mutations/` and `tests/types/` were run because the `F3` docstring edits land in
`mutations/sets.py` / `mutations/resolvers.py` and the two transient mutations landed in
`types/`; both are green, confirming nothing survived either.

`git status --short` after both ruff invocations lists six files this pass modified, all
slice-intended and all in `### Files touched`:

```
 M django_strawberry_framework/auth/mutations.py
 M django_strawberry_framework/mutations/resolvers.py
 M django_strawberry_framework/mutations/sets.py
 M examples/fakeshop/test_query/test_auth_api.py
 M tests/auth/test_mutations.py
 M tests/auth/test_queries.py
```

It also lists files this pass did **not** touch, which is expected and is reported rather than
acted on (`AGENTS.md` rule 34): `docs/SPECS/spec-040-auth_mutations-0_0_13.md` and the
untracked `docs/SPECS/appx/spec-040-auth_mutations-0_0_13-rationale.md` (cohort A, writing as
this pass ran); `django_strawberry_framework/list_field.py`,
`django_strawberry_framework/orders/sets.py`,
`django_strawberry_framework/utils/querysets.py`, `docs/GLOSSARY.md`, `docs/feedback.md`,
`docs/spec-050-list_field_arguments-0_0_15.md`, `docs/builder/bld-final.md`,
`docs/builder/bld-slice-3-sql_and_unit_contracts.md`, `examples/fakeshop/db.sqlite3`,
`examples/fakeshop/test_query/test_list_field_api.py`,
`examples/fakeshop/test_query/test_list_field_async_api.py`,
`examples/fakeshop/test_query/test_multi_db.py`, `tests/orders/test_sets.py`,
`tests/test_list_field.py`, `tests/utils/test_querysets.py` (the concurrent `spec-050`
session); and the `040` cycle's own untracked artifacts. **Nothing was reverted, checked out,
stashed, or tidied.** No baseline failure was observed: every scope this pass ran was green
before its mutation (recorded per entry below).

### Failability proofs

Procedure, mechanized by `scripts/prove_failability.py`: the target is copied to a scratch path OUTSIDE the repo before any mutation; the mutation site is located by an exact anchor asserted to match exactly once (any other count aborts the entry without writing); the same focused scope is run unmutated first, so rows already failing before the mutation are differenced out of the count; both runs' pytest exit codes are read, because a run that collected nothing or blew up emits no `FAILED` lines and would otherwise be recorded as a measured zero; both runs use `--no-cov`; the file is restored from the pre-mutation copy in a `finally` and the restore is proved by `filecmp.cmp(shallow=False)` plus a SHA-256 comparison. One boundary at a time, restored before the next. `git` is never invoked - the tree is legitimately dirty, so an empty `git diff` is unachievable and forcing one would destroy the build's own work.

| # | Boundary | File mutated | Mutation applied | Rows failed | Errors | Scope as run | Restore proof |
|---|---|---|---|---|---|---|---|
| 1 | `django_strawberry_framework/auth/mutations.py::_transport_prologue` | `django_strawberry_framework/auth/mutations.py` | `session = sessions.require_session(request, transport)` -> `session = getattr(request, "session", None)` - builder's description (unverified prose): the session probe weakened to a getattr default, so login/logout no longer reject a sessionless request; ::require_session itself is untouched | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/auth/` | filecmp.cmp(shallow=False) True; sha256 669f89884200b006... == 669f89884200b006... (vs pre-mutation copy) |
| 2 | `django_strawberry_framework/types/finalizer.py::finalize_django_types` | `django_strawberry_framework/types/finalizer.py` | `bind_auth = loaded_attr("django_strawberry_framework.auth.mutations", "bind_auth_mutations") if bind_auth is not None...` -> `from ..auth.mutations import bind_auth_mutations bind_auth_mutations()` - builder's description (unverified prose): the already-loaded-only loaded_attr reach replaced by a plain function-local import, so phase 2.5 imports the auth subsystem unconditionally | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/auth/` | filecmp.cmp(shallow=False) True; sha256 5ee9ea3c8a3ed6cc... == 5ee9ea3c8a3ed6cc... (vs pre-mutation copy) |
| 3 | `django_strawberry_framework/auth/mutations.py::_REGISTER_PROTECTED_FIELDS` | `django_strawberry_framework/auth/mutations.py` | `_REGISTER_PROTECTED_FIELDS = frozenset( { "groups", "is_active", "is_staff", "is_superuser", "user_permissions", }, )` -> `_REGISTER_PROTECTED_FIELDS = frozenset()` - builder's description (unverified prose): the protected-field frozenset emptied, so the intersection never matches and ::derive_register_fields never raises | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/auth/` | filecmp.cmp(shallow=False) True; sha256 669f89884200b006... == 669f89884200b006... (vs pre-mutation copy) |
| 4 | `django_strawberry_framework/types/resolvers.py::_check_n1` | `django_strawberry_framework/types/resolvers.py` | `if strictness == "raise": raise OptimizerError(f"Unplanned N+1: {field_name}{suffix}")` -> `if strictness == "raise": pass` - builder's description (unverified prose): the "raise" arm's raise deleted, so strictness="raise" becomes silent; the "warn" arm is left intact | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/auth/` | filecmp.cmp(shallow=False) True; sha256 71a71b5629e85a29... == 71a71b5629e85a29... (vs pre-mutation copy) |

Verdicts:

1. `django_strawberry_framework/auth/mutations.py::_transport_prologue` - inside Worker 3's mandatory re-run floor (<= 3 rows)
2. `django_strawberry_framework/types/finalizer.py::finalize_django_types` - inside Worker 3's mandatory re-run floor (<= 3 rows)
3. `django_strawberry_framework/auth/mutations.py::_REGISTER_PROTECTED_FIELDS` - inside Worker 3's mandatory re-run floor (<= 3 rows)
4. `django_strawberry_framework/types/resolvers.py::_check_n1` - inside Worker 3's mandatory re-run floor (<= 3 rows)

Failing node ids, per boundary (the count above is `len()` of this list):

1. `django_strawberry_framework/auth/mutations.py::_transport_prologue`
   - file mutated: `django_strawberry_framework/auth/mutations.py`
   - pytest summary: `======================== 2 failed, 193 passed in 4.53s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 195 passed in 4.52s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/auth/test_mutations.py::test_sessionless_login_raises_the_configuration_error_naming_both_middlewares`
   - `tests/auth/test_mutations.py::test_sessionless_logout_raises_the_configuration_error_naming_both_middlewares`
2. `django_strawberry_framework/types/finalizer.py::finalize_django_types`
   - file mutated: `django_strawberry_framework/types/finalizer.py`
   - pytest summary: `======================== 2 failed, 193 passed in 4.60s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 195 passed in 4.57s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/auth/test_mutations.py::test_finalize_in_an_auth_free_process_never_imports_the_auth_subsystem[finalize]`
   - `tests/auth/test_mutations.py::test_finalize_in_an_auth_free_process_never_imports_the_auth_subsystem[schema]`
3. `django_strawberry_framework/auth/mutations.py::_REGISTER_PROTECTED_FIELDS`
   - file mutated: `django_strawberry_framework/auth/mutations.py`
   - pytest summary: `======================== 2 failed, 193 passed in 4.60s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 195 passed in 4.59s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/auth/test_mutations.py::test_derive_register_fields_rejects_privilege_fields`
   - `tests/auth/test_mutations.py::test_register_mutation_rejects_a_protected_required_field_at_the_factory_call`
4. `django_strawberry_framework/types/resolvers.py::_check_n1`
   - file mutated: `django_strawberry_framework/types/resolvers.py`
   - pytest summary: `======================== 2 failed, 193 passed in 4.60s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 195 passed in 4.57s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/auth/test_mutations.py::test_an_unplanned_relation_under_login_node_is_strictness_visible`
   - `tests/auth/test_queries.py::test_an_unplanned_relation_under_me_is_strictness_visible`

A boundary whose removal fails 0 or 1 rows is **weakly pinned** and is `revision-needed` per `docs/builder/BUILD.md` - the fix is more or better-targeted rows, never a weaker boundary. A boundary at 3 rows or fewer is inside Worker 3's mandatory independent re-run floor. A proof carrying collection or setup errors, or whose pytest run exited anything but 0 or 1 (nothing collected, interrupted, internal error, usage error), is not a valid count at all - and a 0 from such a run is not a zero-row result: resolve it and re-run.

Every `<fill in ...>` above is a judgement no tool can make and MUST be replaced by hand before this subsection is submitted: weakly pinned and harness-impossible are the two possible readings of a zero-row result and they prescribe opposite responses (more rows, versus a production-call-site invariant assertion plus a recorded harness limitation), so a record that does not name one reads as self-contradictory.

**Acceptance, per entry.** All four: **2** failing node ids (the `len()` of the listed ids),
**0** collection/setup errors, pytest exit code 1 on the mutant and 0 on the pre-mutation
baseline (`195 passed`, so 0 pre-existing failing rows were differenced out), and the
**dispatched row is itself in the failing set** — `TG-0`'s two new rows, `TG-1`'s two
parametrized ids, `TG-2`'s new row alongside the pre-existing helper-level row, and `TG-3`'s
two new rows. None is weakly pinned; there is no zero-row entry and so no `why 0` judgement to
make. Manifest: `docs/builder/temp-tests/040-slice-6/proofs.json`. Scratch root (outside the
repository): `/private/tmp/claude-501/.../scratchpad/failability`.

**Transient-mutation conditions, each met.** One mutation live at a time and restored before
the next (the tool enforces the order and restores in a `finally`); no mutation live across
the `Status:` transition — every restore was proved before this report was written; each
revert proved by `filecmp.cmp(shallow=False)` plus SHA-256 against the pre-mutation copy; and
`git diff --stat` on `types/finalizer.py` and `types/resolvers.py` is empty (see
`### Files touched`). Post-proof anchor re-check, run after the tool finished:

```shell
$ grep -c 'session = sessions.require_session(request, transport)' \
      django_strawberry_framework/auth/mutations.py            -> 1
$ grep -c 'bind_auth = loaded_attr(' django_strawberry_framework/types/finalizer.py -> 1
$ grep -c 'raise OptimizerError(f"Unplanned N+1: {field_name}{suffix}")' \
      django_strawberry_framework/types/resolvers.py           -> 1
```

**The inverse proof, for the comment-only findings (`CG-1`, `F2`, `F3`).** These owe no
failability proof — a comment is not a boundary and there is nothing to remove. Each of the
four files whose only change is a comment or docstring was copied to a scratch path **outside**
the repository before the edit, and AST identity with docstrings stripped was verified after
the edits, and **again after the four failability proofs had finished** (so the restores are
covered by it too):

```shell
$ uv run python docs/builder/temp-tests/040-slice-6/ast_identity.py <before> <after>
django_strawberry_framework/auth/mutations.py        IDENTICAL
django_strawberry_framework/mutations/sets.py        IDENTICAL
django_strawberry_framework/mutations/resolvers.py   IDENTICAL
examples/fakeshop/test_query/test_auth_api.py        IDENTICAL
```

`tests/auth/test_mutations.py` is **excluded** from this check, as the plan requires it to be:
it also gains real test rows and helper seams, so AST identity cannot hold there by design.
Its `F2` 2.5 edit is a one-line docstring substitution visible in the diff.

**Postconditions the plan set for the three comment-only findings**, each run and recorded:

```shell
$ rg -n 'D-N1|D-N2|D-N3' django_strawberry_framework/          # CG-1: four hits, one D-N3
django_strawberry_framework/auth/queries.py:8:   ... the actor-not-lookup rule, D-N1) and no
django_strawberry_framework/auth/mutations.py:616:  ... (the actor-not-lookup rule, D-N1).
django_strawberry_framework/auth/mutations.py:1109: (the D-N2 deliberate non-reuse: ...
django_strawberry_framework/auth/mutations.py:1197: # The narrowing wires NO relation-visibility helper of its own (D-N3): it

$ rg -n --glob '*.py' 'spec-040 Revision|Revision-7 reload' . | wc -l   # F2
0
# positive control, because an empty grep is indistinguishable from a grep that ran on
# nothing (START.md "Instruments that lie"): the same quoted-glob invocation against a
# scratch file containing `# spec-040 Revision 5` returns 1 hit.

$ rg -n '_bind_mutation|_bind_form_mutation' --glob '*.py' .            # F3
tests/mutations/test_sets.py:1850:def test_bind_mutation_outputs_stashes_model_less_payload_and_slots():
tests/mutations/test_sets.py:1866:def test_model_and_plain_form_binds_ride_bind_mutation_outputs():
```

The two surviving `F3` hits are **test names** naming the live `bind_mutation_outputs`, not the
removed symbol, and are not this cohort's file.

**The relocation claim for `TG-1`'s extraction**, proved mechanically rather than asserted
(`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`): the
snippet `::test_registry_clear_does_not_import_the_auth_subsystem` now sends through
`::_auth_free_subprocess` is byte-for-byte the string it sent before —

```
len(before) == len(after) == 360
sha256 both: 0073128a2522fc78809f2de3c7ff8f58c30456ab5a8e7b6d0a6e579717339e3f
```

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- **`tests/auth/test_queries.py::_me_schema` needed a masking opt-out, not only an
  `extensions=` seam.** The plan named the `optimizer=` kwarg and the assertion shape
  (`res.errors[0].message` contains `"Unplanned N+1: groups"`); with only `extensions=` added,
  the row failed with `assert 'Unplanned N+1: groups' in 'An unexpected error occurred.'` —
  `::_me_schema` builds a bare `DjangoSchema(query=Query)`, so the spec-048 response boundary
  masked exactly the message under test. The seam therefore also passes
  `error_policy={"enabled": False}`, which is the same opt-out
  `tests/auth/test_mutations.py::_finalize_schema` already applies to every schema it builds
  and which the plan's own probe used. Scoped to the optimizer branch: with no optimizer
  `::_me_schema` returns the unchanged bare schema, so every pre-existing `me` row keeps
  masking on and is untouched. The `path` half of the assertion was correct under masking too,
  which is why the message half is the load-bearing one.
- **`optimizer=` over `extension=`**, the same spelling in both files, per the plan's
  discretion item. It takes a **constructed** extension (not a factory) because strictness is a
  construction argument and the call site is where the reader needs to see `strictness="raise"`;
  the `lambda: optimizer` factory Strawberry wants is built inside the helper.
- **`_auth_free_subprocess(body: str)`** takes the snippet as one string and computes the
  fakeshop path internally. The prologue is the existing row's prologue verbatim, so the
  relocation is a pure extraction (proved above); new callers pass a multi-line body, which
  `python -c` accepts, so the two TG-1 driver bodies read as ordinary source rather than as a
  `"; "`-joined one-liner.
- **`TG-1`'s `[schema]` parametrization builds `DjangoSchema`**, not plain
  `strawberry.Schema` — that is the entry a real consumer uses, and the plan left the choice
  open provided the finalize actually runs.
- **The parametrization carries a `label` parameter it deletes.** `ids=["finalize", "schema"]`
  supplies the node ids; the `label` argument exists only so the two-tuple parametrize reads
  symmetrically, and is `del`'d with a one-line reason rather than silently ignored.
- **`_declare_group_type` is Relay-backed (`DjangoType, relay.Node`)** and spelled identically
  in both files, matching each file's existing `_declare_user_type`. The plan left Relay-vs-not
  to discretion; Relay matches the sibling and the relation resolves.
- **Each `TG-3` row seeds exactly one group.** One row is enough for the relation to be
  non-empty and the per-parent resolver to be entered, which is what the diagnostic keys on.
- **`CG-1`'s comment is a `#` comment inside the `Meta` body**, where the plan placed it,
  rather than a docstring clause — `D-N1` and `D-N2` are docstring clauses because their sites
  are docstrings; here the site is a class body, so a `#` comment is the matching idiom. It
  states the invariant in the spec's corrected words and carries no process provenance.

### Notes for Worker 3

- **Re-run scope for every proof is `tests/auth/`**, exactly as recorded in the table — all
  four entries are at 2 rows and therefore inside your mandatory independent re-run floor. The
  manifest is committed at `docs/builder/temp-tests/040-slice-6/proofs.json`; re-running it
  needs `--scratch-root` pointing outside the repository. Compare **node-id sets**, not counts.
- **Two of the four mutations land outside cohort B's writable list**
  (`types/finalizer.py`, `types/resolvers.py`), under Worker 0's transient-only authorization
  recorded in the build plan's `### Slice 6 planning pass`. If you re-run them, the same
  conditions bind you: one live at a time, reverted before the next, net zero at the end.
- **The five Worker-1 probe files in `docs/builder/temp-tests/040-slice-6/` are planning
  evidence, not deliverables.** None was promoted; the permanent rows were written fresh
  against the suite's own helpers. `ast_identity.py` is the instrument for the comment-only
  findings and was used as-is.
- **`tests/auth/_helpers.py` and `tests/auth/conftest.py` were not touched**, per the plan's
  deliberate exclusion. The accepted consequence is the per-file `_declare_group_type` pair,
  which the plan named in advance and routed to the integration pass.
- No shadow file was generated by this pass; the plan's helper inventory
  (`docs/shadow/helper-inventory-040-slice-6.md`) is Worker 1's and was read, not rewritten.
- **Nothing was deferred.** All seven dispatched boxes are ticked, each against a fix in this
  pass's diff.

### Notes for Worker 1 (spec reconciliation)

- **One implementation deviation from the plan, small and mechanical**, recorded here as well
  as in `### Implementation notes` because it changes a line the plan wrote:
  `tests/auth/test_queries.py::_me_schema`'s new seam passes `error_policy={"enabled": False}`
  alongside `extensions=`, not `extensions=` alone. Without it the plan's own assertion shape
  cannot hold — the response boundary masks the optimizer's message. The plan's probe
  (`docs/builder/temp-tests/040-slice-6/test_probe_tg3.py`) already built its schema that way,
  so this is the plan's intent made explicit rather than a departure from it. No spec text is
  affected.
- **No spec gap, conflict, or unstated assumption surfaced.** `D-N3`'s wording in
  `docs/SPECS/spec-040-auth_mutations-0_0_13.md` `## Helper-reuse obligations (DRY)` is the
  contract `CG-1`'s comment restates and it reads correctly against the code; `## Definition of
  done` item 6's "the three deliberate non-reuse points carry their source comment" is now
  true. No planned row needed a production behaviour change to pass, so the plan's
  stop-and-report trigger never fired.
- **No hot path was found** in a slice the plan declared non-hot-path, and no
  version-dependent seam was found in one it declared floor-scope-none. Both declarations hold.

---

## Review (Worker 3)

### Independent failability re-run — mutations recorded BEFORE they are made

All four recorded boundaries measured **2** failing rows, so all four sit inside the
mandatory re-run floor (`docs/builder/worker-3.md`: every boundary at 3 rows or fewer) and
**all four are re-run by this pass**. None is accepted on Worker 2's record alone. Re-run
at the scope Worker 2 recorded (`tests/auth/`) and compared as **node-id sets**.

Mechanism: `uv run python scripts/prove_failability.py
docs/builder/temp-tests/040-slice-6/proofs.json --only <n> --scratch-root <outside-repo>`,
one entry at a time, each restored and byte-proved before the next. The tool runs the
anchor check first (so a live prior mutation aborts the entry having written nothing),
copies the target outside the repo, runs the unmutated baseline, mutates, runs, restores in
a `finally`, and proves the restore by `filecmp.cmp(shallow=False)` + SHA-256. `git` is
never invoked: the tree is legitimately dirty with this build's work and a concurrent
`spec-050` session's.

The four mutations, stated before application (each one removes the boundary; none merely
perturbs code near it):

1. `django_strawberry_framework/auth/mutations.py::_transport_prologue` —
   `session = sessions.require_session(request, transport)` replaced by
   `session = getattr(request, "session", None)`. The rejection disappears from the
   login/logout path; `auth/sessions.py::require_session` itself is untouched, so
   `tests/auth/test_sessions.py`'s four direct rows cannot inflate the count.
2. `django_strawberry_framework/types/finalizer.py::finalize_django_types` — the
   `loaded_attr(...)` lookup and its `if bind_auth is not None:` guard replaced by
   `from ..auth.mutations import bind_auth_mutations` + a direct call. The
   already-loaded-only reach is gone; phase 2.5 imports the auth subsystem
   unconditionally. **Outside cohort B's writable list**, under the source carve-out.
3. `django_strawberry_framework/auth/mutations.py::_REGISTER_PROTECTED_FIELDS` — the
   five-name frozenset replaced by `frozenset()`. The intersection never matches, so
   `::derive_register_fields` never raises.
4. `django_strawberry_framework/types/resolvers.py::_check_n1` — the `"raise"` arm's
   `raise OptimizerError(...)` replaced by `pass`, leaving the `"warn"` arm intact.
   Strictness `"raise"` becomes silent. **Outside cohort B's writable list**, under the
   source carve-out.

Carve-out conditions bound to this pass: one mutation live at a time, reverted inside the
same pass, revert proved by byte comparison, and
`git diff --stat -- django_strawberry_framework/types/` empty at the end. Results below
under `### Independent failability re-run — results`.

### Independent failability re-run — results

All four re-run, none accepted on Worker 2's record alone. Node-id **sets** compared, not
totals. Every set is **identical** to Worker 2's, at the same scope, with the same
pre-mutation baseline (`195 passed`, exit 0) and the same 0 collection/setup errors.

| # | Boundary | W2 rows | W3 rows | Node-id set | Errors | Restore proof |
|---|---|---|---|---|---|---|
| 1 | `django_strawberry_framework/auth/mutations.py::_transport_prologue` | 2 | 2 | **identical** | 0 | `filecmp.cmp(shallow=False)` True; sha256 `669f8988…` == `669f8988…` |
| 2 | `django_strawberry_framework/types/finalizer.py::finalize_django_types` | 2 | 2 | **identical** | 0 | `filecmp.cmp(shallow=False)` True; sha256 `5ee9ea3c…` == `5ee9ea3c…` |
| 3 | `django_strawberry_framework/auth/mutations.py::_REGISTER_PROTECTED_FIELDS` | 2 | 2 | **identical** | 0 | `filecmp.cmp(shallow=False)` True; sha256 `669f8988…` == `669f8988…` |
| 4 | `django_strawberry_framework/types/resolvers.py::_check_n1` | 2 | 2 | **identical** | 0 | `filecmp.cmp(shallow=False)` True; sha256 `71a71b56…` == `71a71b56…` |

Scope for all four, as Worker 2 recorded it:
`uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/auth/`.

The sets, re-measured by this pass:

1. `::test_sessionless_login_raises_the_configuration_error_naming_both_middlewares`,
   `::test_sessionless_logout_raises_the_configuration_error_naming_both_middlewares`
   (both `tests/auth/test_mutations.py`).
2. `tests/auth/test_mutations.py::test_finalize_in_an_auth_free_process_never_imports_the_auth_subsystem[finalize]`
   and `…[schema]`.
3. `tests/auth/test_mutations.py::test_derive_register_fields_rejects_privilege_fields`
   (pre-existing) and `::test_register_mutation_rejects_a_protected_required_field_at_the_factory_call`
   (the dispatched row).
4. `tests/auth/test_mutations.py::test_an_unplanned_relation_under_login_node_is_strictness_visible`
   and `tests/auth/test_queries.py::test_an_unplanned_relation_under_me_is_strictness_visible`.

**The dispatched row is in the failing set for every entry.** None is weakly pinned; there
is no zero-row entry and so no `why 0` judgement. Each mutation genuinely removes its
boundary rather than perturbing code near it: #1 swaps a raising probe for a `getattr`
default, #2 replaces an already-loaded-only lookup and its `is not None` guard with an
unconditional import, #3 empties the frozenset the intersection reads, #4 deletes the
`"raise"` arm's raise.

**Carve-out conditions met.** `scripts/prove_failability.py` was run `--only <n>`, one entry
at a time, each with its own anchor check first; `--scratch-root` pointed outside the
repository; every exit code was 0. After all four:
`git status --short -- django_strawberry_framework/types/` and
`git diff --stat -- django_strawberry_framework/types/` are both empty, no
`ACTIVE-MUTATION.json` marker survives in the scratch root, and cohort B's own diffstat is
byte-for-byte what it was before the re-runs (361 insertions / 72 deletions over the same
six files). `git checkout` / `stash` / `restore` were never used.

**Post-re-run green:** `uv run pytest tests/auth/ --no-cov -q` → 195 passed;
`… examples/fakeshop/test_query/test_auth_api.py --no-cov -q` → 21 passed;
`… tests/mutations/ tests/types/ --no-cov -q` → 939 passed.

### Dispatched findings checklist walk

All seven boxes ticked by Worker 2; each tick has a matching fix in the diff, verified
independently:

| Box | Landed | Evidence re-derived by this pass |
|---|---|---|
| `CG-1` | yes | `rg -n 'D-N1\|D-N2\|D-N3' django_strawberry_framework/` → 4 hits, one `D-N3` at `auth/mutations.py:1197`. See the Medium finding on its wording |
| `TG-0` | yes | Row renamed and strengthened; logout twin added; `::_finalize_schema`'s falsified `AttributeError` docstring restated. Proof #1 |
| `TG-1` | yes | `::_auth_free_subprocess` extracted, existing row refactored onto it and its docstring narrowed, parametrized row added. Proof #2 |
| `TG-2` | yes | Factory-level row added beside the helper-level one. Proof #3 |
| `TG-3` | yes | One row per surface, both under an armed optimizer. Proof #4 |
| `F2` | yes | `rg -n --glob '*.py' 'spec-040 Revision\|Revision-7 reload' .` → **0** (re-run by this pass) |
| `F3` | yes | `rg -n '_bind_mutation\|_bind_form_mutation' --glob '*.py' .` → only the two `tests/mutations/test_sets.py` **test names**, which name the live `bind_mutation_outputs` |

No box is ticked without a fix, and nothing in the diff is unaccounted for by a box.

### High:

None.

### Medium:

#### `CG-1`'s `D-N3` comment drops the scope clause the spec added to resolve this exact contradiction

`django_strawberry_framework/auth/mutations.py:1197-1201` (inside
`::_synthesize_register_rider`'s synthesized `Meta` body).

The landed comment reads:

```django_strawberry_framework/auth/mutations.py:1197
# The narrowing wires NO relation-visibility helper of its own (D-N3): it
# carries no relation input, and a custom model whose ``REQUIRED_FIELDS``
# names a forward FK gets the standard ``<field>_id`` input through the
# shared decode's own relation handling - so registration never acquires a
# second, auth-local visibility rule.
```

The spec's corrected `D-N3` reads "**The stock user model's** narrowed `Meta.fields`
carries no relation input at all, and a custom model whose `REQUIRED_FIELDS` names a
forward FK gets the standard `<field>_id` input …". The qualifier is not decoration: the
rationale companion records that Slice 4 found `D-N3`'s reason clause *contradicting*
`## Edge cases and constraints` precisely because the unqualified form ("the narrowed
`Meta.fields` has no relation inputs") cannot be true alongside the Custom-user-models
edge case, and the fix was to scope it. The comment compresses the corrected sentence and
drops the scope, so `it carries no relation input, and a custom model … gets the standard
<field>_id input` reads as a general claim immediately contradicted by its own conjunct —
the retired form, restated in code.

The normative half ("wires NO relation-visibility helper of its own") and the conclusion
("never acquires a second, auth-local visibility rule") are both correct, and Definition of
done item 6 is satisfied by the comment's existence, so this is not a contract-delivery
failure. It matters because the rationale names the concrete harm for the identical
sentence: it "invites a later audit to record a violation where there is none" — which is
how this finding class costs a future cycle a pass.

Recommended change: restore the scope, e.g. `the stock user model's narrowing carries no
relation input at all, and a custom model whose ``REQUIRED_FIELDS`` names a forward FK …`.
No test expectation changes; the file's AST-identity inverse proof still applies.

**Escalated to Worker 1** rather than held at `revision-needed` — see
`### Notes for Worker 1 (spec reconciliation)`. Cohort A is editing
`docs/SPECS/spec-040-auth_mutations-0_0_13.md` concurrently, so the wording this comment
must track is not settled inside cohort B's pass; the spec custodian is the role that can
land the two together.

### Low:

#### The `TG-1` parametrization carries a dead `label` argument

`tests/auth/test_mutations.py:471-487` (the `@pytest.mark.parametrize` block and
`del label` inside
`::test_finalize_in_an_auth_free_process_never_imports_the_auth_subsystem`).

`ids=["finalize", "schema"]` already supplies both node-id suffixes, so the two-tuple
`("label", "driver")` parametrization exists only to be discarded by `del label` plus a
comment explaining the discard — three mechanisms for one naming job, and an argument with
no reader. The simpler shape produces identical node ids:

```tests/auth/test_mutations.py:471
@pytest.mark.parametrize(
    "driver",
    [_FINALIZE_DRIVER_BODY, _SCHEMA_DRIVER_BODY],
    ids=["finalize", "schema"],
)
def test_finalize_in_an_auth_free_process_never_imports_the_auth_subsystem(driver):
```

No behavior or node id changes, so no test expectation moves. Recorded for the integration
pass rather than held: it is a readability simplification in a file the integration pass
already re-opens for the `_declare_group_type` / subprocess-idiom consolidations below.

#### The build report's independence claim for `TG-1`'s two ids does not hold

`### Tests added or updated` and `### Implementation notes` describe `[finalize]` and
`[schema]` as "the two ways a consumer actually reaches the phase-2.5 bind" that "can
regress independently". Checked against source: `finalize_django_types()` is not invoked by
`DjangoSchema.__init__` (`django_strawberry_framework/schema.py::DjangoSchema.__init__`
sets the execution context and the two policy extensions and calls `super().__init__`; no
finalize), and `_SCHEMA_DRIVER_BODY` therefore calls `finalize_django_types()` **itself**
before building the schema. `[schema]` is a strict superset of `[finalize]`, not a second
entry point, and both ids reach the `loaded_attr` boundary through the same call.

The rows are still worth having — `[schema]` covers "auth stays unimported through a full
consumer build", a real and distinct regression surface — and the arithmetic rule is met
(2 node ids, both failing under the mutation, re-verified by this pass). Only the recorded
rationale is inaccurate, and it would be read as fact by the next audit of this area.
Recommended change: none to the test; correct the sentence when Worker 1 audits the
artifact, so the record says what the second id actually buys.

### DRY findings

**Intra-file near-copies the ownership partition does NOT excuse.** The plan carefully named
the *cross-file* duplication it could not avoid (`_declare_group_type`, because
`tests/auth/_helpers.py` is outside cohort B's writable list) and routed it to the
integration pass — correct, and confirmed landed exactly as planned: one five-line
`_declare_group_type()` per file, spelled identically, matching each file's existing
`_declare_user_type`. It did not consider two duplications introduced **inside**
`tests/auth/test_mutations.py`, which cohort B owns outright:

- **The `PrivilegeRequiredUser` declaration and its rejection regex, twice.**
  `tests/auth/test_mutations.py:1213-1234` (`::test_derive_register_fields_rejects_privilege_fields`)
  and `:1237-1267` (`::test_register_mutation_rejects_a_protected_required_field_at_the_factory_call`)
  carry byte-identical 9-line model bodies and a byte-identical six-line
  `pytest.raises(ConfigurationError, match=…)` regex. The regex is the clearest half: a
  reworded production message costs a two-site sweep in one file. Recommended shape — a
  file-local `_PROTECTED_FIELD_REJECT` regex constant read by both rows, and (optionally) a
  `_privilege_required_user()` factory returning a freshly declared model with
  `_unique_app_label()`, since Django's app registry requires distinct classes.
- **The sessionless-`ConfigurationError` assertion block, twice.**
  `tests/auth/test_mutations.py:942-946` and `:962-966` repeat the same four assertions
  (`isinstance(... ConfigurationError)`, `"SessionMiddleware"`, `"AuthMiddlewareStack"`,
  `"session" in message.lower()`). The static helper's repeated-literal section shows the
  two middleware names arriving at `2x` each with this slice. A file-local
  `_assert_sessionless_configuration_error(res)` collapses it and keeps the two rows'
  difference (login vs logout query) as the only thing that reads as different.

Severity is DRY-tier, not correctness: neither entrenches duplicated **logic**, and each
row's self-containment is the established idiom of this file (it already carries
`CustomLoginUser`, `PrivilegeRequiredUser`, and `BrokenRequiredUser` as independent inline
models). **Disposition:** recorded as a deferred follow-up for Worker 1 to weigh at final
verification / the integration pass, alongside the cross-file items the plan already routed
there — the same pass already re-opens this file for the `_declare_group_type` hoist and the
four-way subprocess-idiom consolidation, so folding these in costs nothing extra and
splitting them across two loops would.

**Existence challenge, raised and answered.** `::_auth_free_subprocess` is the one new
helper. It should exist: it has two real callers in its own file, it *removes* an in-file
near-copy rather than adding one, and its extraction was proved byte-for-byte
(`len(before) == len(after) == 360`, one sha256) rather than asserted. The seams
(`optimizer=`, `declare=`, `fields=`) are keyword-only extensions of helpers that already
existed and carried the same seam shape — no new builder, no new indirection layer. Nothing
here warrants a deletion challenge.

**Cross-cohort duplication: none.** Cohort A's diff is `docs/SPECS/spec-040-*.md` and its
rationale companion (prose); cohort B's is Python comments and test rows. There is no
shared guard, rejection path, error-message shape, or status-code choice to compare.

**Pre-existing, not this slice's:** `tests/auth/test_mutations.py:2508`'s `_CH_LOGOUT`
duplicates `:300`'s `_LOGOUT_Q` byte-for-byte. Present at `HEAD`, untouched by this diff,
recorded so the integration pass can pick it up.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty**: no change to `__all__`
and no change to the re-export list. Consistent with the slice's own scope — every
production edit in the diff is a comment or docstring, proved by AST identity below.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

Verified rather than assumed: `git diff -- CHANGELOG.md` is empty.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces.

Verified rather than assumed: the six files in `### Files touched` are the complete set this
cohort's diff touches. `docs/SPECS/spec-040-auth_mutations-0_0_13.md` and the untracked
`docs/SPECS/appx/spec-040-auth_mutations-0_0_13-rationale.md` are dirty in the tree, but
they are **cohort A's** concurrent work, not this slice's, and were read-only for this
review. The `spec-050` session's files (`list_field.py`, `orders/sets.py`,
`utils/querysets.py`, `docs/GLOSSARY.md`, `docs/feedback.md`, `examples/fakeshop/db.sqlite3`,
`docs/builder/bld-final.md`, and their tests) were neither edited, reverted, stashed, nor
checked out.

### What looks solid

- **The four failability records survive an independent re-run without a single
  discrepancy.** Same scope, same baseline, same node-id sets, 0 collection errors, every
  restore byte-proved. That is the strongest possible reading of the mandatory floor and it
  is rare enough to say out loud.
- **`TG-3` takes the path it claims, proved two ways.** Mutating `_check_n1`'s raise fails
  exactly the two `TG-3` rows (a validation-error row would be untouched by that mutation),
  and a review probe confirms the landed spelling produces a real
  `OptimizerError` as `original_error` at `path == ["me", "groupsConnection"]` while the
  `{ me { groups { name } } }` spelling the Slice-4 finding suggested yields a GraphQL
  validation error with `original_error is None`, `path is None`, and no `"Unplanned N+1"`
  anywhere in the message. The plan's query-shape correction was load-bearing and the rows
  could not have passed on a validation error. `BUILD.md` `### Query-shape tests must pin
  the load-bearing property`'s right-path rule is satisfied: both queries are minimal and
  carry no sidecar argument that could route the selection to a fallback.
- **The `error_policy={"enabled": False}` deviation is a legitimate harness configuration,
  not a weakened assertion.** Three independent checks: (i) the row still fails when the
  strictness boundary is removed — re-run #4 above, so the opt-out did not make the row
  unfalsifiable; (ii) blast radius is exactly one caller — the seam applies the opt-out only
  on the `optimizer is not None` branch, and all 17 other `_me_schema(…)` call sites in
  `tests/auth/test_queries.py` still take the unchanged `return DjangoSchema(query=Query)`
  path, so every pre-existing `me` row keeps masking on; (iii) it hides nothing the row was
  supposed to see — the policy's only job is replacing an unexpected exception's message
  with a stable one plus a correlation id, masking is pinned on its own in
  `tests/test_error_policy.py` and the live tier, and this is the identical opt-out
  `tests/auth/test_mutations.py::_finalize_schema` already applies to every schema it
  builds, with the reason written in its docstring.
- **The `extensions=` seam is genuinely inert when unused.** `DjangoSchema.__init__` reads
  `kwargs.get("extensions")` and `_with_resource_policy_extension` normalizes with
  `installed = [] if extensions is None else list(extensions)` — with an explicit comment
  saying truthiness must not be used — so `_finalize_schema`'s new unconditional
  `extensions=[]` is indistinguishable from omitting the kwarg. No behavior change for the
  13 existing `_finalize_schema` callers.
- **The inverse proof reproduces, and its instrument can fail.** Re-running
  `docs/builder/temp-tests/040-slice-6/ast_identity.py` against `git show HEAD:<path>`
  (read-only, into a scratch path outside the repo) prints `IDENTICAL` for
  `auth/mutations.py`, `mutations/sets.py`, `mutations/resolvers.py`, and
  `test_auth_api.py`. The exclusion of `tests/auth/test_mutations.py` is honest — it prints
  `DIFFERENT`, as does `tests/auth/test_queries.py`, both because they gain real rows. A
  positive control (one appended `X_CONTROL = 1` on an otherwise-identical copy) prints
  `DIFFERENT` and exits 1, so a green reading is evidence rather than a control that cannot
  fail.
- **`F2`'s fix shape is right at all five sites.** Three parentheticals were deleted where
  the surrounding clause already carried the WHY in full (`auth/mutations.py`'s module
  docstring — the WHY is the post-colon clause; `mutations/resolvers.py::_model_decode_step`
  — the WHY is "naively popping it pre-walk would mark it unprovided and silently drop it
  from the exclude calculation", and the paragraph still opens with its `spec-040 D6`
  pointer; `test_auth_api.py::test_complete_reload_preserves_the_auth_surface` — the WHY is
  the post-colon `LazyType KeyError` clause). Two were **retargeted, not deleted**, and both
  attributions check out: `Revision 5` → `Decision 6`, which owns `D-N2`, the
  "register's password error must NOT route through `validation_error_to_field_errors`"
  non-reuse the row asserts; `Revision 4` → `Decision 8`, which the production code itself
  already cites for the same half
  (`auth/mutations.py::register_mutation #"the auth ledger, so the spec-040 Decision 8"`).
  No information was lost at any site.
- **`F3`'s five substitutions are the right symbols, checked at source.**
  `bind_write_declarations` is what calls `mutation_cls.build_input(meta, object_type)`;
  `bind_mutations` is the model-backed rider and `bind_form_mutations` the model-less one;
  and `forms/sets.py::bind_form_mutations`'s own docstring states "The `ModelForm` flavor
  rides `bind_mutations()` … so it is NOT bound here", which is exactly what
  `resolvers.py::payload_cls_for` now says. Leaving `the ``036``` in place was correct —
  a `spec-NNN` pointer is kept vocabulary.
- **Every live-tier unreachability argument re-verified independently, not inherited.**
  `TG-0`: `examples/fakeshop/config/settings.py:95` lists `SessionMiddleware` in
  `MIDDLEWARE` and `django.test.Client` cannot omit a configured middleware. `TG-1`: the
  assertion is about a fresh process's `sys.modules`. `TG-2`: `rg -n AUTH_USER_MODEL
  examples/fakeshop/config/` returns nothing, so fakeshop runs stock `auth.User`
  (`REQUIRED_FIELDS == ["email"]`, no protected column) and the branch is unreachable from
  a real query. `TG-3`: `examples/fakeshop/config/schema.py:73` builds a module-level
  `_optimizer = DjangoOptimizerExtension()` at the default strictness that the live tier
  reuses, and `examples/fakeshop/apps/accounts/schema.py:31` pins
  `fields = ("id", "username", "email")` with a docstring forbidding `"__all__"`. Both
  halves hold; unreachability, not a fixture gap.
- **No fail-open shape in the diff.** Every new decision reads `optimizer is not None` /
  `if optimizer is None` rather than truthiness, on a value whose absence is meaningful;
  `_auth_free_subprocess` pairs `check=False` with an explicit `returncode == 0` assertion
  carrying `stdout`/`stderr`, so a subprocess that dies for an unrelated reason fails the
  row rather than passing it; no clamp, no `getattr` default standing in for meaningful
  absence, no `or` fallback over a legitimately falsy left operand, no broad `except` around
  a check. The only `getattr` default in play was the transient mutation itself.
- **No process provenance anywhere in the new code.** A sweep of all six files for
  `worker N` / `slice N` / `round N` / severity labels / `TG-`/`CG-`/`F2`/`F3` / `bld-` /
  "as of 0.0." / "previously," returns zero hits, and all six files are ASCII-clean.
  `uv run python scripts/check_citations.py --check` → `OK: 979 citations resolve`.
- **The rename stranded nothing.** `rg 'sessionless_request_surfaces'` across the whole tree
  returns hits only inside this cycle's own `bld-040-slice-*.md` per-cycle artifacts, which
  are the record of the finding as raised and are exempt from the citation gate and the
  style rule. Independently swept for `path #"substring"` citers of every reworded docstring
  line: none exists outside those artifacts.
- **Independent staleness sweep found nothing.** Run against the whole tree rather than the
  slice's file list: no example-model field set changed (the production diff is
  AST-identical), and no wire-shape conversion landed — the `groups` exposure is a
  test-local `DjangoType`, not fakeshop's `UserType`. `rg -i 'revision[ -][0-9]'` over every
  `.py` returns 10 hits, all of them the two populations the plan explicitly declared out of
  scope (`tests/middleware/test_debug_toolbar.py` → `spec-042`;
  `examples/fakeshop/test_query/test_library_api.py` → the concurrent `spec-050` session's
  file). Neither was touched.
- **Boundary count and split answer hold.** The slice introduces no new boundary; the four
  proofs pin four boundaries that already exist at HEAD, which is the correct reading of
  `BUILD.md`'s obligation for a `TEST-GAP` remediation.

### Temp test verification

- `docs/builder/temp-tests/040-slice-6/test_w3_tg3_right_path.py` — written by this review to
  answer the right-path question directly. Two rows, both passing: the landed
  `groupsConnection` spelling raises a real `OptimizerError` as `original_error` at
  `path == ["me", "groupsConnection"]`; the `{ me { groups { name } } }` spelling raises a
  GraphQL validation error with `original_error is None`, `path is None`, and no
  `"Unplanned N+1"` substring. **Disposition: deleted at cycle closeout, not promoted.** It
  caught no bug — it is a negative control for an assertion the permanent rows already carry
  in distinguishing form, and promoting it would pin the optimizer's internals from an auth
  suite, which is the coupling the plan deliberately avoided by asserting only the
  `"Unplanned N+1: groups"` substring and the path.
- `docs/builder/temp-tests/040-slice-6/ast_identity.py` — Worker 1's instrument, re-run by
  this review over all six files plus a positive control. Kept for the cycle; deleted at
  closeout.
- Worker 1's five `test_probe_*.py` planning probes — read as evidence the plan was
  executable, not run as deliverables and not promoted. Worker 2's report confirms the
  permanent rows were written fresh against the suite's own helpers, and the diff bears that
  out (every new row uses `_finalize_schema` / `_login_logout_schema` / `_me_schema` /
  `_declare_user_type` / `_unique_app_label`, not probe code).
- `docs/builder/temp-tests/040-slice-6/proofs.json` — Worker 2's manifest, re-run unmodified
  by this pass.

### Static helper use

`uv run python scripts/review_inspect.py tests/auth/test_mutations.py --output-dir docs/shadow`
and the same for `tests/auth/test_queries.py` — required because both add 50+ lines of new
logic outside `django_strawberry_framework/` (`+247/-42` and `+86/-7` by `git diff
--numstat`). Its **Repeated string literals** section is what surfaced the
`SessionMiddleware` / `AuthMiddlewareStack` pair arriving at `2x` and is cited in
`### DRY findings` above.

**Skipped, with reason:** the three production files under review
(`auth/mutations.py`, `mutations/sets.py`, `mutations/resolvers.py`) — their entire
contribution is comment and docstring text, proved AST-identical, so there is no
review-worthy logic for an AST overview to report. `examples/fakeshop/test_query/test_auth_api.py`
— same, two docstring lines. No file under `optimizer/` or `types/` is touched by the
slice's permanent diff (the two `types/` files carried transient proof mutations only, net
zero), so that trigger does not fire.

### Notes for Worker 1 (spec reconciliation)

- **Escalated — `CG-1`'s `D-N3` comment wording (Medium, above).** Resolution requires spec
  context this cohort cannot settle: cohort A is editing
  `docs/SPECS/spec-040-auth_mutations-0_0_13.md` concurrently, so the sentence the comment
  must track is still moving. Paths to pick between: **(a)** re-loop Worker 2 to restore the
  "stock user model's" scope on the comment's first conjunct, matching whatever `D-N3`
  wording cohort A lands — the one-clause fix, no test expectation change, and the file's
  AST-identity proof still holds; **(b)** accept the comment as a deliberate compression,
  and record in the rationale companion that the code comment states the stock case and the
  custom case as a contrast rather than a general claim, so a future audit does not read it
  as the retired form. (a) is the recommendation: the rationale already names the concrete
  harm of the unqualified sentence, and paying it twice in two media is the avoidable half.
- **The build report's `TG-1` independence claim is inaccurate (Low, above).** Please correct
  it at final verification rather than carrying it forward: `DjangoSchema` does not
  auto-finalize, so `[schema]` reaches the `loaded_attr` boundary through the same
  `finalize_django_types()` call `[finalize]` does and is a superset of it, not a second
  entry. What `[schema]` genuinely buys is coverage of the full consumer build staying
  auth-free. The two node ids and the 2-row count are real and re-verified; only the
  rationale overstates.
- **DRY follow-up for the integration pass.** Two intra-file near-copies in
  `tests/auth/test_mutations.py` that the ownership partition does **not** excuse (the
  duplicated `PrivilegeRequiredUser` + rejection regex, and the duplicated sessionless
  assertion block), plus the `label`-argument simplification. The plan already routed the
  cross-file items (`_declare_group_type`, the `_declare_user_type` pair, the four-way
  subprocess idiom) to that pass; these belong in the same loop, since it re-opens the same
  file. Details and recommended shapes in `### DRY findings`.
- **No spec gap, conflict, or unstated assumption found by this review.** `D-N3`'s contract
  reads correctly against the code; `## Definition of done` item 6 is satisfied (all three
  non-reuse points now carry a source comment); the live-first exception each package-tier
  placement claims is genuine and re-verified. The one artifact-vs-spec drift worth noting
  is navigational only: the plan cites `D-N3` at `…spec-040…:1851-1857` while it now sits at
  `:1984-1990` under cohort A's concurrent edits. Raw `path:NN` is legal in a per-cycle
  artifact and the citation is correct by content; no action needed.
- **Hot-path and floor declarations both confirmed.** The production diff changes no
  executed statement (AST-identical across all four production files), so there is no hot
  path to budget and no version-dependent seam to run at the floor. `Not applicable` is
  correct in both subsections.

### Review outcome

`review-accepted`, with one Medium finding transparently escalated to Worker 1 under
`### Notes for Worker 1 (spec reconciliation)` and every Low / DRY finding recorded with its
disposition.

The gate, item by item: every dispatched box is closed by a fix in the diff and none is
ticked without one; every boundary in the diff carries a recorded failability proof,
every record was audited against all of `### What gets recorded`, none is weakly pinned,
and the mandatory floor was met by re-running **all four** — none accepted on Worker 2's
record alone — with identical node-id sets; the comment-only findings' inverse proof was
re-run with a positive control; the public-surface check is clean; CHANGELOG and
documentation sanity are both not-applicable and verified so; no temp test caught a bug
needing promotion; the static helper ran where required and every skip is recorded; the
plan declares no hot path and no floor scope, and this review confirms both. The Medium is
escalated rather than held because its resolution turns on wording cohort A has not
finished landing, which is exactly the case `worker-3.md`'s acceptance gate reserves the
escalation route for.

---

## Final verification (Worker 1)

**Outcome: `revision-needed`.** Three one-clause defects, all inside cohort B's own
writable files, all of the same class the cycle was commissioned to close: prose that is
false standing next to code that is correct. Nothing in the diff's *behaviour* is wrong —
every test row lands, every proof holds under independent re-derivation, every postcondition
re-runs clean. What fails is the wording of three of the things this slice shipped.

The escalated Medium is **not** intentionally rejected; it is upheld, with the exact
replacement text pinned below. One of Worker 3's two Lows is re-graded upward, because the
inaccurate claim it names is not confined to the artifact — it is also in a shipped test
docstring, which Worker 3's write-up did not notice.

### The escalated Medium — upheld, `revision-needed`

`CG-1`'s landed comment at `django_strawberry_framework/auth/mutations.py::_synthesize_register_rider`
(inside the synthesized `Meta` body, beside `fields = register_fields`) must carry the scope
clause. Read independently this pass, in this order:

1. **Spec `D-N3`** (`docs/SPECS/spec-040-auth_mutations-0_0_13.md:1984-1990`): "register wires
   **no** relation-visibility helper of its own. **The stock user model's** narrowed
   `Meta.fields` carries no relation input at all, and a custom model whose `REQUIRED_FIELDS`
   names a forward FK gets the standard `<field>_id` input through the shared decode's own
   relation handling — so **the rider inherits whatever the shared path does and adds
   nothing**, which is what keeps registration from acquiring a second, auth-local visibility
   rule."
2. **The Custom-user-models edge case** (`:2030-2036`): "a `REQUIRED_FIELDS` entry that is a
   forward FK becomes the standard `<field>_id` input (the model-column converter's relation
   rule)."
3. **The rationale companion's Slice-4 entry**
   (`docs/SPECS/appx/spec-040-auth_mutations-0_0_13-rationale.md:1517-1524`): the item's reason
   clause was "the narrowed `Meta.fields` has no relation inputs"; "Both cannot be true", so
   the false reason was dropped and the scope added. It names the concrete harm: the
   unqualified form "invites a later audit to record a violation where there is none."
4. **The landed comment** (`django_strawberry_framework/auth/mutations.py:1197-1201`): "The
   narrowing wires NO relation-visibility helper of its own (D-N3): **it carries no relation
   input**, and a custom model whose `REQUIRED_FIELDS` names a forward FK gets the standard
   `<field>_id` input …".

The comment's second clause is the retired sentence, verbatim in substance, and it is
contradicted by the comment's own next conjunct one line later. This is not a compression
that lost decoration; it is the specific proposition the spec deleted **this same cycle**,
reinstated in a second home by the pass that was dispatched to honour that spec. The comment
also drops the bridging clause ("the rider inherits whatever the shared path does and adds
nothing"), which is the inference that makes the conclusion follow — without it the reader is
handed a contradiction and a conclusion with nothing joining them.

**Why the accept-and-record path is refused.** Worker 3's option (b) — keep the comment and
gloss it in the rationale companion — is the fix-the-doc-not-the-code shortcut `AGENTS.md`
rule 5 forbids, and this artifact's own `#### Step 1` already forbids it by name ("**Do not**
'fix' this by editing the spec"). It would also pay the rationale's named harm twice, in two
media, to avoid a one-clause edit.

**Why the escalation's own premise has expired.** Worker 3 escalated rather than holding
because "cohort A is editing `docs/SPECS/spec-040-auth_mutations-0_0_13.md` concurrently, so
the wording this comment must track is not settled inside cohort B's pass." That was true when
the review ran. It is not true now: cohort A closed Slice 5 `final-accepted`, and `D-N3` reads
at HEAD exactly as quoted above. The sentence the comment must track has stopped moving, which
removes the only ground the review offered for not holding the slice.

**Weighed on the cycle's own standard, not on effort.** `CG-1` existed because a comment was
missing — a Low. Shipping the comment with the reason the spec had just retired converts a
missing-comment Low into a false-comment defect, which is a net regression on the exact
dimension the finding was raised on. A 276-row audit produced one code gap; closing it with a
restatement of the falsehood the audit itself removed is not closing it.

**Exact replacement, so the builder has nothing to re-invent.** Replace the five comment lines
at `django_strawberry_framework/auth/mutations.py:1197-1201` with these seven, at the same
12-space indent, ASCII-only, longest line 87 characters:

```python
            # The narrowing wires NO relation-visibility helper of its own (D-N3): the
            # stock user model's narrowed ``Meta.fields`` carries no relation input at
            # all, and a custom model whose ``REQUIRED_FIELDS`` names a forward FK gets
            # the standard ``<field>_id`` input through the shared decode's own relation
            # handling - so the rider inherits whatever the shared path does and adds
            # nothing, which is what keeps registration from acquiring a second,
            # auth-local visibility rule.
```

No test expectation moves; the file's AST-identity inverse proof still applies and must be
re-run. The `CG-1` postcondition is unchanged: `rg -n 'D-N1|D-N2|D-N3' django_strawberry_framework/`
still returns four hits, one of them `D-N3`.

### Disposition of the two Low findings

#### Low 1 — the dead `label` argument: **fix in this re-loop**, not the integration pass

`tests/auth/test_mutations.py:471-488`. Confirmed by reading: `ids=["finalize", "schema"]`
already supplies both node-id suffixes, the `("label", "driver")` two-tuple exists only to be
discarded, and `del label` plus its explanatory comment are two further mechanisms serving the
same naming job. Worker 3's recommended shape is correct and produces identical node ids.

Worker 3 routed it to the integration pass on the ground that the pass already re-opens this
file. That reasoning was sound while the slice was being accepted; it is not now. A Worker 2
apply-changes pass is being dispatched into this exact file for the Medium above, so fixing it
here costs one edit and removes a defect from the integration pass's inbox rather than adding
one. Apply Worker 3's shape verbatim:

```python
@pytest.mark.parametrize(
    "driver",
    [_FINALIZE_DRIVER_BODY, _SCHEMA_DRIVER_BODY],
    ids=["finalize", "schema"],
)
def test_finalize_in_an_auth_free_process_never_imports_the_auth_subsystem(driver):
```

with the `del label` line and its comment removed. Node ids are unchanged, so the `TG-1`
failability record's node-id set survives verbatim and needs no re-measurement.

#### Low 2 — the `[finalize]` / `[schema]` independence claim: **re-graded to Medium, fix in this re-loop**

Worker 3's finding is correct and I re-derived it at source rather than accepting it:
`django_strawberry_framework/schema.py::DjangoSchema.__init__` resolves the two policies, sets
`execution_context_class`, installs the two extensions and calls `super().__init__` — it never
finalizes, and `rg -c 'finalize' django_strawberry_framework/schema.py` returns 0 for the whole
module. `_SCHEMA_DRIVER_BODY` therefore calls `finalize_django_types()` itself before building
the schema. `[schema]` is a strict superset of `[finalize]`; both reach the `loaded_attr`
boundary through the same call, and the boundary cannot regress under one without regressing
under the other.

**What Worker 3 missed, and why the grade moves.** The review located the claim in
`### Tests added or updated` and `### Implementation notes` and recommended "none to the test;
correct the sentence when Worker 1 audits the artifact". But the same sentence is in the
**shipped test docstring**:

```tests/auth/test_mutations.py:479
    never pays for it. Both consumer entries into phase 2.5 are driven -- a bare
    ``finalize_django_types()`` and a full ``DjangoSchema`` build -- because they
    can regress independently. A plain function-local import in the finalizer
    would load the subsystem under either one.
```

A false claim in a shipped docstring beside correct code is `CG-1`'s defect class exactly, not
an artifact-hygiene item, and `docs/builder/BUILD.md` `## Claims are proven mechanically,
never accepted on prose` applies to it with full force: the next audit of this area reads a
docstring as measured. Correcting only the artifact would leave the dominant copy live —
`START.md`'s "Partial claim fix = dominant residual defect".

The spec is **not** the source of the error and needs no edit: its test-plan row
(`docs/SPECS/spec-040-auth_mutations-0_0_13.md:2319-2328`) says "**finalizes** (or builds a
schema)", a parenthetical alternative driver, and claims no independence. The docstring
overstated beyond its own contract.

**Exact replacement** for the docstring's third sentence onward, at the same 4-space indent,
longest line 80 characters:

```python
    never pays for it. Two drivers reach that one lookup: a bare
    ``finalize_django_types()``, and a full ``DjangoSchema`` build, which
    finalizes first and then adds schema construction on top - a superset, not a
    second entry point, since ``DjangoSchema`` does not finalize on its own. The
    second driver is here because the whole consumer build must stay auth-free,
    not because the two can fail apart. A plain function-local import in the
    finalizer would load the subsystem under either one.
```

**The artifact half is corrected here, in this append-only section**, since
`docs/builder/ARTIFACT.md` forbids editing prior entries: the `### Tests added or updated`
sentence "the two ids are the two ways a consumer actually reaches the phase-2.5 bind, they
can regress independently" and the matching `### Implementation notes` bullet are **inaccurate
as recorded**. What `[schema]` genuinely buys is that a full consumer build stays auth-free.
The two node ids, the 2-row count and the failability set are real and re-verified; only the
rationale overstated.

### Standing final-verification duties

#### 1. Artifact, iteration history, and diff

Read in full: the Plan, Worker 2's build report, Worker 3's review, and
`git diff -- <the six files in "### Files touched">`. The diff is
`361 insertions / 72 deletions` across the six files — byte-for-byte the figure Worker 3
recorded after its own re-runs, so nothing moved between the review and this pass.

#### 2. Every planned step implemented or intentionally rejected

All eight implementation steps landed. Step 4's third sub-item was answered rather than
mechanically applied — the module docstring's `#"the sessionless edge"` clause was re-read and
left as-is because the rename does not falsify it, which is the plan's own instruction
("re-read it and adjust only if the rename leaves it wrong"). Step 4's "do not add a Channels
twin" and Step 3's "leave `the ``036``` in place" prohibitions were both honoured; I confirmed
the latter in the diff. One deviation is recorded and correct: `_me_schema`'s optimizer branch
also passes `error_policy={"enabled": False}`, without which the plan's own assertion shape
cannot hold. I verified its blast radius is the optimizer branch only — the `optimizer is None`
path still returns the unchanged bare `DjangoSchema(query=Query)`.

#### 3. Dispatched findings checklist audit — all seven ticks stand, none un-ticked

Every `- [x]` was re-derived independently this pass, not accepted from Worker 2's report or
Worker 3's walk:

| Box | Tick verdict | Evidence re-derived by this pass |
|---|---|---|
| `CG-1` | **stands** | `rg -n 'D-N1\|D-N2\|D-N3' django_strawberry_framework/` → 4 hits, one `D-N3` at `auth/mutations.py:1197`. The box's contract was "one comment at `::_synthesize_register_rider`"; it landed |
| `TG-0` | **stands** | Row renamed and strengthened (class + both middleware names asserted); logout twin present; `::_finalize_schema`'s falsified `AttributeError` docstring restated to the package's own `ConfigurationError` |
| `TG-1` | **stands** | `::_auth_free_subprocess` extracted, existing row refactored onto it, its docstring narrowed to the clear half, parametrized row added |
| `TG-2` | **stands** | Factory-level row present beside the helper-level one, raising at a bare `register_mutation()` with nothing after it in the `with` block |
| `TG-3` | **stands** | One row per surface, both under `DjangoOptimizerExtension(strictness="raise")`, both asserting message substring + `path` |
| `F2` | **stands** | `rg -n --glob '*.py' 'spec-040 Revision\|Revision-7 reload' .` → **0**. Positive control: the same invocation against a scratch directory holding a `# spec-040 Revision 5` line returns 13 hits, so the instrument is live and the 0 is a measurement, not a grep that ran on nothing |
| `F3` | **stands** | `rg -n --glob '*.py' '_bind_mutation\|_bind_form_mutation' .` → only `tests/mutations/test_sets.py:1850` and `:1866`, both **test names** naming the live `bind_mutation_outputs` |

**No box is un-ticked and no `- [ ]` remains, so no deferral reason is owed.** Stated
explicitly because the `revision-needed` could be misread as an over-tick finding: it is not.
`CG-1`'s dispatched contract — that a `D-N3` source comment exist at that site — genuinely
landed. The defect is the comment's **content**, which is a Medium against the spec, not a
false completion claim against the checklist. Un-ticking it would misrecord what happened and
would tell the next pass to write a comment that already exists.

#### 4. DRY against prior accepted slices

**Cross-slice: none possible, and none found.** Slices 1-5 were Worker-1-only prose passes over
the spec and its rationale companion; this is the cycle's only source-bearing slice, so there
is no prior accepted slice carrying a helper, literal, or shape this one could duplicate. I
confirmed the negative rather than assuming it: the four closed slices' artifacts record zero
`.py` edits between them.

**Intra-slice, and Worker 3's two DRY findings re-derived at source:**

- `tests/auth/test_mutations.py:1216-1234` and `:1247-1267` carry byte-identical nine-line
  `PrivilegeRequiredUser` bodies and a byte-identical six-line
  `pytest.raises(ConfigurationError, match=…)` regex. Confirmed by reading both.
- `:938-946` and `:958-966` repeat the same four sessionless assertions. Confirmed.
- The cross-file `_declare_group_type` pair landed exactly as the plan named it in advance, and
  the `_declare_user_type` pair it matches is pre-existing.

**Disposition: routed to the integration pass, not to this re-loop** — a decided answer, not
silence. The two intra-file copies differ from the `label` item above in that their correct
shape is not settled inside cohort B: a `_privilege_required_user()` factory and a
`_assert_sessionless_configuration_error(res)` helper are the same kind of thing as the
four-way subprocess idiom and the `_declare_group_type` pair, all of which want
`tests/auth/_helpers.py`, which is outside this cohort's writable list. Landing file-local
versions now guarantees the integration pass rewrites them again in the same file. The
condition that would change this answer: if the integration pass decides **not** to open
`_helpers.py`, both collapse to file-local helpers and should land then, in one loop over this
file rather than two.

Neither entrenches duplicated **logic**, so neither is a High or a blocker on its own; the
slice is held for the three prose defects above, not for these.

#### 5. Failability record — complete for all four boundaries

Confirmed present and complete against every field `docs/builder/BUILD.md`
`### What gets recorded` requires. Worker 3 re-ran all four at Worker 2's scope and reported
identical node-id sets; my delta is the record audit, field by field:

| Required field | Present for all four? |
|---|---|
| Boundary, symbol-qualified path | yes — `::_transport_prologue`, `::finalize_django_types`, `::_REGISTER_PROTECTED_FIELDS`, `::_check_n1` |
| Exact mutation applied (removes the boundary, not merely perturbs near it) | yes — each stated as the before → after text; each genuinely removes the boundary |
| Failing node ids **listed**, and the focused scope as run | yes — enumerated per boundary; scope `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/auth/` for all four, so the four records are comparable as sets |
| Collection / setup error count, **separately** | yes — `0` on every entry |
| Pre-mutation state of that same scope | yes — `195 passed`, exit 0, `pre-existing failing rows excluded from the count: 0` on every entry |
| Revert proved by **byte-comparison**, command and result | yes — `filecmp.cmp(shallow=False)` True plus a SHA-256 pair per entry, against the pre-mutation copy taken outside the repository |
| **why 0** on a zero-row result | not owed — no entry is zero-row, and the report says so explicitly rather than leaving it ambiguous |

None is weakly pinned (all four at 2 rows, `len()` of a listed set rather than an asserted
number), and the **dispatched row is in the failing set for every entry** — including `TG-2`,
where the pair is the pre-existing helper-level row plus the new factory-level one rather than
two pre-existing rows.

**Both transient mutations are gone, confirmed by me rather than read from the report:**

```shell
$ git diff --stat -- django_strawberry_framework/types/
(no output)
$ git status --short -- django_strawberry_framework/types/
(no output)
$ find . -name 'ACTIVE-MUTATION.json'
(no output)
```

**The one relocation claim in the slice, proved by me rather than accepted.** Per
`docs/builder/worker-1.md` `### Verifying relocation / promotion claims`, I re-ran `TG-1`'s
extraction proof myself against `git show HEAD:tests/auth/test_mutations.py` read into a
scratch path outside the repository: the prologue `::_auth_free_subprocess` builds plus the
body the refactored call site passes reconstructs the HEAD inline literal exactly —
`len == 360` both sides, `sha256 0073128a2522fc78809f2de3c7ff8f58c30456ab5a8e7b6d0a6e579717339e3f`
both sides, with a positive control confirming the HEAD file really carries the fragments
compared. Worker 2's figures reproduce.

**The inverse proof re-run independently, with a control.** `ast_identity.py` against
`git show HEAD:<path>` for each production file: `auth/mutations.py`, `mutations/sets.py`,
`mutations/resolvers.py` and `examples/fakeshop/test_query/test_auth_api.py` all print
`IDENTICAL`; `tests/auth/test_mutations.py` prints `DIFFERENT`, as the plan says it must. A
positive control (one appended `X_CONTROL = 1` on an otherwise-identical copy) prints
`DIFFERENT` and exits 1, so the four green readings are evidence rather than a control that
cannot fail. **The production diff changes no executed statement**, which is what makes the
hot-path and floor-scope declarations of `none` correct rather than merely declared.

One cosmetic residue, recorded and not blocking: line 888 of this artifact still carries
`scripts/prove_failability.py`'s own boilerplate instruction about replacing `<fill in …>`
placeholders. There are no unfilled placeholders — it is the tool's explanatory line left in a
submitted subsection. Worth deleting at the next pass over this file; it is not a missing
field.

#### 6. Fail-open read of the diff

Read for the catalogued shapes rather than inferred from the green suite:

- **Clamps** — none. No `max(…, 0)` / `min(…, limit)` anywhere in the diff.
- **`getattr` defaults standing in for meaningful absence** — none in the permanent diff. The
  only one in play (`getattr(request, "session", None)`) was the `TG-0` *mutation*, applied to
  demonstrate the fail-open and reverted; it is the shape the boundary exists to prevent, and
  it is absent from the tree (`grep` for the `require_session` anchor returns exactly 1).
- **`or` fallbacks over a legitimately falsy left operand** — none.
- **Bare / over-broad `except` around a check** — none; the diff adds no `try`.
- **Truthiness on a value whose absence differs from emptiness** — deliberately avoided at both
  new decision sites: `_finalize_schema` reads `if optimizer is not None`, `_me_schema` reads
  `if optimizer is None`. A truthiness test would have been the natural spelling and is not
  what landed. This also matches the invariant `schema.py::_with_resource_policy_extension`
  states in its own comment ("Do not use truthiness to normalize the consumer's iterable …
  `None` is the only omitted-value spelling"), which I read at source to confirm the new
  unconditional `extensions=[]` on `_finalize_schema` is genuinely indistinguishable from
  omitting the kwarg — `installed = [] if extensions is None else list(extensions)` yields `[]`
  either way, so the 13 pre-existing callers are unaffected.
- **A default reached because input was incoherent rather than absent** — none.
- `_auth_free_subprocess` pairs `check=False` with an explicit `assert result.returncode == 0`
  carrying `stdout` / `stderr`. `check=False` alone would have been the fail-open: a subprocess
  dying for an unrelated reason would pass the row. It does not.

**No fail-open shape landed.**

#### 7. Focused tests (no `--cov*` flag; `--no-cov`, since `pytest.ini` auto-applies `--cov`)

```shell
$ uv run pytest tests/auth/ --no-cov -q                                    195 passed
$ uv run pytest examples/fakeshop/test_query/test_auth_api.py --no-cov -q   21 passed
$ uv run pytest tests/mutations/ tests/types/ --no-cov -q                  939 passed
```

All three run and pass, at counts identical to Worker 2's and Worker 3's. **No failure to
difference against the concurrent `spec-050` session**, so the attribution question did not
arise. Read-only lint confirmation on the six files (never `--fix`):
`uv run ruff format --check` → `6 files already formatted`; `uv run ruff check` →
`All checks passed!`.

#### 8. Staged-anchor sweep

```shell
$ rg -n 'TODO\(spec-040' . --glob '!KANBAN.md' --glob '!KANBAN.html' --glob '!BACKLOG.md'    3 hits
$ rg -n 'TODO-(ALPHA|BETA|STABLE)-040' . --glob '!KANBAN.md' --glob '!KANBAN.html' --glob '!BACKLOG.md'   2 hits
```

**No staged anchor survives in source, tests, or comments.** All five hits are prose *about*
the anchor discipline, in Markdown: the spec's own Definition-of-done sentence at
`:1879`; `bld-040-slice-4-…md:357` quoting it; and three rationale-companion bullets (`040`
at `:1161` and `:1352`, `038` at `:307`) recording an anchor's discharge or a card citation.
Instrument checked before the reading was trusted: the same sweep for `TODO\(spec-` with no
number returns **152** hits, so the pattern matches this corpus and the narrow result is a
measurement rather than a sweep that ran on nothing.

#### 9. Spec reconciliation — no spec edit needed

Nothing cohort B landed falsifies a sentence in the settled spec. Checked specifically, since
cohort A closed it and any edit here would be a cross-slice correction:

- **Definition of done item 6** (`:2544-2551`) claims "the three deliberate non-reuse points
  carry their source comment". Before this slice that was false; it is now **true** — the spec
  was always right and the tree was short, which is why the cycle routed it as a code gap
  rather than a spec weakening. The sentence needs no edit, and the rationale companion's
  Slice-4-dated observation that "at `HEAD` only two do" stays: it is a dated observation under
  `docs/builder/BUILD.md` `### `## Current state`: observations stand, predictions do not`, in
  a history file, not a live claim.
- **The Sessionless / middleware-less edge case** (`:2096-2111`) and the **test plan's
  sessionless row** (`:2314-2318`) already demand exactly what `TG-0` landed — the
  `ConfigurationError` "asserted by **class and by the actionable middleware text**, not merely
  by the substring `"session"`". Slices 4 and 5 folded this in; the rows conform to it.
- **The test plan's finalizer row** (`:2319-2328`) says "**finalizes** (or builds a schema)" —
  a parenthetical alternative driver. It makes no independence claim, so Low 2's false
  docstring is a code defect and not a spec defect. Confirmed by reading the row.
- **The `TG-0` rename stranded no spec citation.** `rg -n 'sessionless_request_surfaces' .`
  returns hits only inside this cycle's own `bld-040-slice-*.md` per-cycle artifacts, which
  record the finding as raised and are exempt from both the citation gate and the `path::Symbol`
  rule. The spec never cited the old node id.
- **`F2`'s two retargeted attributions check out.** `Revision 5` → `Decision 6`, which owns the
  direct `field_error("password", …)` keying via `D-N2`; `Revision 4` → `Decision 8`, which the
  production code already cites for the same half.

### What the re-loop hands back

Worker 0 dispatches one Worker 2 apply-changes pass and one Worker 3 re-review. The Worker 2
pass has **three edits, all in cohort B's existing writable files, none behavioural**:

1. `django_strawberry_framework/auth/mutations.py:1197-1201` — replace the five `D-N3` comment
   lines with the seven pinned above, verbatim.
2. `tests/auth/test_mutations.py` — replace the `test_finalize_in_an_auth_free_process_never_imports_the_auth_subsystem`
   docstring's independence sentence with the pinned replacement above.
3. `tests/auth/test_mutations.py` — drop the `label` parametrize member and its `del label`
   line, per Worker 3's shape above.

Obligations that ride with them, and nothing else:

- **Re-run the inverse proof** for `django_strawberry_framework/auth/mutations.py`
  (`ast_identity.py` against `git show HEAD:` into a scratch path outside the repo). Edit 1 is
  comment-only and must stay AST-identical; it owes no failability proof, and **inventing one
  is wrong** — a comment is not a boundary.
- **No failability re-measurement is owed.** Edits 2 and 3 change a docstring and a
  parametrize member; node ids are unchanged by construction (`ids=` already supplied them), so
  all four recorded node-id sets survive verbatim. Re-run `uv run pytest tests/auth/ --no-cov`
  to confirm 195 still pass and the two `[finalize]` / `[schema]` ids still exist.
- **Re-run the `CG-1` postcondition** (`rg -n 'D-N1|D-N2|D-N3' django_strawberry_framework/` →
  four hits, one `D-N3`).
- Ruff scoped to the touched files, **never `.`** — the concurrent `spec-050` session's
  untracked files are in this tree.

Handed to the **integration pass**, unchanged from what the Plan and the review already routed
there, plus one addition:

- the cross-file `_declare_group_type` pair and the pre-existing `_declare_user_type` pair;
- the four-way subprocess-isolation near-copy across `tests/auth/test_mutations.py`,
  `tests/auth/test_sessions.py`, `tests/base/test_init.py`, `tests/rest_framework/test_soft_dependency.py`;
- **new here:** the two intra-file near-copies in `tests/auth/test_mutations.py` (the duplicated
  `PrivilegeRequiredUser` body + rejection regex, and the duplicated sessionless assertion
  block), with the condition recorded above that decides whether they land file-local or in
  `_helpers.py`;
- `tests/auth/test_mutations.py:2508`'s `_CH_LOGOUT` duplicating `:300`'s `_LOGOUT_Q`
  byte-for-byte, pre-existing at HEAD;
- the `spec-042 Revision N` population in `tests/middleware/test_debug_toolbar.py` and the
  bug-hunt round provenance comment in `tests/auth/test_sessions.py` — both out of this
  cohort's population, for the maintainer;
- `bld-040-slice-1-rationale_extraction.md`'s link to the retired Decision 11 anchor, and
  Slice 4's two un-edited `WIP-ALPHA-040-0.0.13` sites, both already on Worker 0's list.

### Summary

The slice shipped what it was dispatched to ship: `D-N3`'s missing source comment, five
restated `Revision N` citations, five corrected removed-symbol docstring mentions, and seven
new or rewritten test rows closing four unpinned boundaries — every one of them proved failable
at two rows with a byte-compared revert, independently re-run by Worker 3 and re-audited here.
The production diff changes no executed statement, no fail-open shape landed, both transient
`types/` mutations are gone, all seven dispatched boxes are correctly ticked, and every focused
scope is green.

It is held at `revision-needed` for three one-clause prose defects in its own files: the `D-N3`
comment restates the unqualified reason the spec deleted this same cycle; the `TG-1` docstring
claims two node ids can regress independently when `DjangoSchema` does not auto-finalize and
`[schema]` is a strict superset of `[finalize]`; and the `TG-1` parametrization carries an
argument nothing reads. The first is the escalated Medium, upheld rather than rejected — its
escalation rested on cohort A's wording still moving, and cohort A has closed. The second is
re-graded upward from Worker 3's Low because the inaccurate claim is not only in the artifact,
which the review checked, but in a shipped docstring, which it did not.

Status: `revision-needed`.

### Spec changes made (Worker 1 only)

**None.** Duty 9 found nothing cohort B landed that falsifies a sentence in the now-settled
spec, so no cross-slice correction to `docs/SPECS/spec-040-auth_mutations-0_0_13.md` or its
rationale companion was necessary or made. The five checks that produced that answer are
enumerated under `#### 9. Spec reconciliation` above. Definition-of-done item 6's clause is
made **true** by this slice rather than falsified by it, which is the outcome the code-gap
routing was chosen to produce; weakening the spec to match the tree would have been the
shortcut `AGENTS.md` rule 5 forbids, and the `D-N3` finding above is the same rule applied to
the comment.

No `- [ ]` box remains in `### Dispatched findings checklist`, so no deferral reason is owed
under this heading.

---

## Build report (Worker 2, pass 2)

Three edits, all pinned verbatim by `## Final verification (Worker 1)`: the `D-N3` comment's
seven replacement lines, the `TG-1` docstring's replacement sentences, and Worker 3's
parametrize shape. Nothing was re-worded, nothing else was opened, and **no checklist box was
touched** — all seven were already `- [x]` and Worker 1 audited them; `CG-1`'s tick is not an
over-tick, because its dispatched contract (a comment at that site) landed and the defect was
the content.

### Files touched

Grounded in `git status --short`, run after both ruff invocations.

- `django_strawberry_framework/auth/mutations.py` — the five `D-N3` comment lines inside the
  synthesized `Meta` body of `::_synthesize_register_rider` replaced by Worker 1's seven pinned
  lines. Comment only; no other hunk in this pass.
- `tests/auth/test_mutations.py` — two edits to
  `::test_finalize_in_an_auth_free_process_never_imports_the_auth_subsystem`: the docstring's
  independence sentence replaced by Worker 1's pinned text, and the parametrization narrowed to
  `"driver"` with the `del label` line and its comment removed.

`django_strawberry_framework/types/finalizer.py` was mutated **transiently** by the `TG-1`
re-proof and is net-zero:

```shell
$ git diff --stat -- django_strawberry_framework/types/
(no output)
$ git status --short -- django_strawberry_framework/types/
(no output)
$ find . -name 'ACTIVE-MUTATION.json'
(no output)
$ grep -c 'bind_auth = loaded_attr(' django_strawberry_framework/types/finalizer.py
1
```

`types/resolvers.py` was not touched at all this pass — only the `TG-1` proof was re-run.

**The landed `D-N3` comment**, at the same 12-space indent, ASCII-only, longest line 88
characters (`# the standard ``<field>_id`` input through the shared decode's own relation`),
under the project's 99 limit:

```python
            # The narrowing wires NO relation-visibility helper of its own (D-N3): the
            # stock user model's narrowed ``Meta.fields`` carries no relation input at
            # all, and a custom model whose ``REQUIRED_FIELDS`` names a forward FK gets
            # the standard ``<field>_id`` input through the shared decode's own relation
            # handling - so the rider inherits whatever the shared path does and adds
            # nothing, which is what keeps registration from acquiring a second,
            # auth-local visibility rule.
```

Per-line lengths as measured after placement: 86, 86, 87, 88, 85, 80, 41. Non-ASCII byte count
in the whole file: **0** (measured over the file's bytes, not eyeballed). It now carries the
scope clause (`the stock user model's`) and the bridging clause (`the rider inherits whatever
the shared path does and adds nothing`) the retired sentence had dropped, so the second conjunct
no longer contradicts the third.

### Tests added or updated

**No test row was added, removed, or renamed.** Both edits are inside one existing row:

- `tests/auth/test_mutations.py::test_finalize_in_an_auth_free_process_never_imports_the_auth_subsystem`
  — docstring's third sentence onward replaced with Worker 1's pinned text. The false
  "they can regress independently" claim is gone; the replacement states what `[schema]`
  genuinely buys (a superset driver, because `DjangoSchema` does not finalize on its own, kept
  so the whole consumer build is proved auth-free). Longest replacement line 80 characters.
- The same row's parametrization is now `"driver"` over
  `[_FINALIZE_DRIVER_BODY, _SCHEMA_DRIVER_BODY]` with `ids=["finalize", "schema"]` unchanged;
  the `("label", "driver")` two-tuple, the `label` parameter, and the `del label` line with its
  comment are all gone.

Node ids confirmed unchanged by collection, not inferred:

```shell
$ uv run pytest tests/auth/ --no-cov -q --collect-only | grep never_imports_the_auth_subsystem
<Function test_finalize_in_an_auth_free_process_never_imports_the_auth_subsystem[finalize]>
<Function test_finalize_in_an_auth_free_process_never_imports_the_auth_subsystem[schema]>
```

### Validation run

Every path passed explicitly — never through a shell variable, which is the trap the prior pass
hit (`START.md` `## Instruments that lie`), and never `.`, which would rewrite the concurrent
`spec-050` session's files.

```shell
$ uv run ruff format django_strawberry_framework/auth/mutations.py tests/auth/test_mutations.py
2 files left unchanged

$ uv run ruff check --fix django_strawberry_framework/auth/mutations.py tests/auth/test_mutations.py
All checks passed!

$ uvx pre-commit run --files django_strawberry_framework/auth/mutations.py tests/auth/test_mutations.py
kanban tracked path constants ................ Passed
source layout (py trailing commas + ascii-only; md link-def scaffold; ...) Passed
ruff format .................................. Passed
ruff check ................................... Passed
kanban anchors collision-free ................ Passed
citations resolve (AGENTS.md rule 27) ........ Passed
```

`source-layout` **rewrote nothing on its first invocation** this pass (unlike pass 1, where the
over-exploded `@pytest.mark.parametrize` list forced a re-stage); the hook was nevertheless run
a second time with identical output, so the "re-run until it rewrites nothing" condition is met
by measurement rather than by assumption. The narrowed parametrize list is three members on
three lines, which `source-layout` accepts unchanged.

Focused tests (no `--cov*` flag anywhere; `--no-cov` because `pytest.ini` auto-applies `--cov`):

```shell
$ uv run pytest tests/auth/ --no-cov -q                                    195 passed
$ uv run pytest examples/fakeshop/test_query/test_auth_api.py --no-cov -q   21 passed
```

195 is the same count Worker 2 pass 1, Worker 3 and Worker 1 all recorded, which is the expected
result of a pass that adds no row.

`git status --short` after both ruff invocations lists the two files this pass modified, both
slice-intended and both in `### Files touched` above. It also lists, unchanged and untouched:
the four other cohort-B files still dirty from pass 1
(`django_strawberry_framework/mutations/resolvers.py`, `…/mutations/sets.py`,
`examples/fakeshop/test_query/test_auth_api.py`, `tests/auth/test_queries.py`); cohort A's
`docs/SPECS/spec-040-auth_mutations-0_0_13.md` and its untracked rationale companion; and the
concurrent `spec-050` session's files (`django_strawberry_framework/list_field.py`,
`…/orders/sets.py`, `…/utils/querysets.py`, `docs/GLOSSARY.md`, `docs/feedback.md`,
`docs/spec-050-list_field_arguments-0_0_15.md`, `docs/builder/bld-final.md`,
`docs/builder/bld-slice-3-sql_and_unit_contracts.md`, `examples/fakeshop/db.sqlite3`,
`examples/fakeshop/test_query/test_list_field_api.py`, `…/test_list_field_async_api.py`,
`…/test_multi_db.py`, `tests/orders/test_sets.py`, `tests/test_list_field.py`,
`tests/utils/test_querysets.py`). **Nothing was reverted, checked out, stashed, or tidied**
(`AGENTS.md` rule 34). Two changes in that set moved since pass 1 —
`docs/builder/bld-slice-3-sql_and_unit_contracts.md` is now modified and the pass-1 untracked
`docs/builder/bld-003-final.md` is gone — which is the `spec-050` session working, reported
rather than acted on.

### Failability proofs

**No new boundary; none introduced by this pass.** Edit 1 is a comment, edits 2 and 3 a
docstring and a dead parameter. The three other recorded boundaries (`TG-0`, `TG-2`, `TG-3`)
were **not** re-run, as Worker 1 directed: nothing in this pass touches their rows or their
production sites.

`TG-1`'s proof **was** re-run, because edit 3 changes the parametrization that *produces* its
two node ids — Worker 1 judged them unchanged, and this pass confirms rather than infers it.
One entry, one mutation, `--scratch-root` outside the repository, restored and byte-compared
inside the tool:

```shell
$ uv run python scripts/prove_failability.py docs/builder/temp-tests/040-slice-6/proofs.json \
      --only 2 --scratch-root <scratchpad>/failability-pass2 \
      --output docs/builder/temp-tests/040-slice-6/pass2-tg1-proof.md
EXIT=0
```

| # | Boundary | File mutated | Mutation applied | Rows failed | Errors | Scope as run | Restore proof |
|---|---|---|---|---|---|---|---|
| 2 | `django_strawberry_framework/types/finalizer.py::finalize_django_types` | `django_strawberry_framework/types/finalizer.py` | the already-loaded-only `loaded_attr` reach (plus its `is not None` guard) replaced by a plain function-local `from ..auth.mutations import bind_auth_mutations` and a direct call, so phase 2.5 imports the auth subsystem unconditionally | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/auth/` | `filecmp.cmp(shallow=False)` True; sha256 `5ee9ea3c8a3ed6cc…` == `5ee9ea3c8a3ed6cc…` (vs the pre-mutation copy) |

Failing node ids (the count is the `len()` of this list):

- `tests/auth/test_mutations.py::test_finalize_in_an_auth_free_process_never_imports_the_auth_subsystem[finalize]`
- `tests/auth/test_mutations.py::test_finalize_in_an_auth_free_process_never_imports_the_auth_subsystem[schema]`

- pytest summary: `2 failed, 193 passed`; pytest exit code 1.
- pre-mutation state of that same scope: `195 passed`, exit code 0; pre-existing failing rows
  differenced out: 0.
- collection / setup errors: **0**.
- No zero-row entry, so no `why 0` judgement is owed.

**Node-id set compared against the record, not the count.** The set above is **identical**, id
for id, to the pass-1 record at `### Failability proofs` entry 2 and to Worker 3's independent
re-run — `[finalize]` and `[schema]`, in the same scope. Dropping the `label` member changed the
parametrize argnames, not the ids, exactly as `ids=` already supplying them predicts. The
dispatched rows are themselves the failing set, and 2 rows clears the 0-or-1 weakly-pinned rule.

This run's report is written to `docs/builder/temp-tests/040-slice-6/pass2-tg1-proof.md` and is
labelled **PARTIAL RECORD** by the tool, because `--only` selected 1 of 4 manifest entries. The
other three entries' complete records stand unchanged in `## Build report (Worker 2)`
`### Failability proofs`, re-run independently by Worker 3 and field-audited by Worker 1; this
pass changed nothing they measure.

**The inverse proof, for the two comment/docstring-only halves.** Run against
`git show HEAD:<path>` written to a scratch path outside the repository:

```shell
$ uv run python docs/builder/temp-tests/040-slice-6/ast_identity.py <HEAD copy> <working tree>
django_strawberry_framework/auth/mutations.py     IDENTICAL   (exit 0)
tests/auth/test_mutations.py                      DIFFERENT   (exit 1)
```

`django_strawberry_framework/auth/mutations.py` prints `IDENTICAL`, so this pass's whole
production diff — pass 1's docstring edits plus this pass's comment replacement — changes no
executed statement. `tests/auth/test_mutations.py` prints `DIFFERENT`, and it **must**:
recorded rather than skipped silently, per the plan. Two independent reasons, only one of which
existed at pass 1: it legitimately gained real test rows and helper seams, **and** this pass
removed a parameter and a `del` statement, which are executable code. The docstring half of its
change is invisible to this instrument by construction (docstrings are stripped before the
comparison), which is why the parametrize half is verified by node-id collection above instead.

**Positive control, so `IDENTICAL` is a measurement and not an instrument that cannot fail**
(`START.md` `## Instruments that lie`): the same command over
`django_strawberry_framework/auth/mutations.py` and a copy of it with one appended
`X_CONTROL = 1` prints `DIFFERENT` and exits 1.

**`CG-1`'s postcondition re-run**, unchanged from what the plan set:

```shell
$ rg -n 'D-N1|D-N2|D-N3' django_strawberry_framework/          # four hits, one D-N3
django_strawberry_framework/auth/queries.py:8:   ... the actor-not-lookup rule, D-N1) and no
django_strawberry_framework/auth/mutations.py:616:  ... (the actor-not-lookup rule, D-N1).
django_strawberry_framework/auth/mutations.py:1109: (the D-N2 deliberate non-reuse: ...
django_strawberry_framework/auth/mutations.py:1197: # The narrowing wires NO relation-visibility helper of its own (D-N3): the
```

`F2`'s and `F3`'s postconditions were not re-run: this pass touches neither population, and
neither edit adds a `Revision N` citation or a removed-symbol mention.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope **none** — no production behaviour
changes, so there is no version-dependent seam for a floor run to exercise. Re-confirmed for
this pass by the AST-identity `IDENTICAL` above: the production edit changes no executed
statement at all.

### Implementation notes

- **All three replacement texts were applied verbatim from
  `## Final verification (Worker 1)`.** No re-wording, no re-indenting, no "improvement" — the
  texts are pinned precisely because each carries an invariant a paraphrase would drop, and the
  defect this re-loop exists to fix was a paraphrase that dropped one.
- **The comment stayed a `#` comment inside the `Meta` body**, where pass 1 placed it and where
  Worker 1's pinned block is indented to sit. Only its five lines were replaced; the
  `fields = register_fields` line it annotates and the `permission_classes` line below are
  untouched.
- **The docstring's first two sentences were kept.** Worker 1 pinned "the docstring's third
  sentence onward", so the `spec-040 Decision 3` pointer and the `loaded_attr` mechanism
  sentence stay exactly as they were; only the false claim and the sentence carrying it moved.
- **`del label` was removed with the parameter, not left behind.** Worker 3's shape removes the
  reason the statement existed; keeping it would have been an unused-name error, and keeping the
  parameter without the `del` would have been an unused argument. Both mechanisms served the one
  naming job `ids=` already does.

### Notes for Worker 3

- **Re-run scope for the one re-proved boundary is `tests/auth/`**, unchanged, and its report is
  at `docs/builder/temp-tests/040-slice-6/pass2-tg1-proof.md` (labelled PARTIAL RECORD by the
  tool, for the `--only 2` reason stated above). `types/finalizer.py` remains the one file
  outside cohort B's writable list touched this pass, transient-only, and it is byte-clean —
  the same conditions bind an independent re-run.
- **Nothing else in the slice was reopened.** The four failability proofs, the seven checklist
  ticks and the `error_policy` harness decision all stand; the three DRY items and the
  `_helpers.py` question remain routed to the integration pass exactly as Worker 1 left them.
- **No box was ticked or un-ticked this pass.** All seven were already `- [x]`.
- **Line 888's `<fill in …>` boilerplate residue** that Worker 1 recorded as cosmetic is inside
  a prior entry, which `docs/builder/ARTIFACT.md` forbids editing, so it is still there. Not
  carried into this report: the block above ends at the `why 0` line with the judgement made
  rather than the placeholder.

### Notes for Worker 1 (spec reconciliation)

- **One instruction could not be followed as written, and it changed nothing about the work.**
  The dispatch's required reading named
  `docs/SPECS/appx/spec-040-auth_mutations-0_0_13-rationale.md` around its `D-N3` entry.
  `docs/builder/worker-2.md` `## Required reading` lists the spec's `-rationale.md` companion
  as a **forbidden read** for this role, and that role file is the standing contract. It was not
  read. Nothing was lost: the replacement text was pinned verbatim, and `D-N3` plus the
  **Custom user models** edge case were read at source in
  `docs/SPECS/spec-040-auth_mutations-0_0_13.md` — the landed comment's scope clause and
  bridging clause now match `D-N3` word for word in substance, and its `<field>_id` clause
  matches the edge case's "a `REQUIRED_FIELDS` entry that is a forward FK becomes the standard
  `<field>_id` input (the model-column converter's relation rule)".
- **No spec gap, conflict, or unstated assumption surfaced**, and no spec text is affected by any
  of the three edits. `## Definition of done` item 6 stays true — the comment is still present
  at `::_synthesize_register_rider`; only its wording changed.
- **No plan-vs-implementation drift.** Every edit was pinned; there was no discretion to
  exercise and none was taken.

Status: built.

---

## Review (Worker 3, pass 2)

Scope of this pass: the three fixes Worker 1 pinned, plus their blast radius. The pass-1
review of everything else stands and is not reopened.

### Independent failability re-run — the mutation, recorded BEFORE it is made

One boundary is re-run this pass: **`django_strawberry_framework/types/finalizer.py::finalize_django_types`**
(`TG-1`). It is inside the mandatory floor (`docs/builder/worker-3.md`: every boundary at
3 rows or fewer; Worker 2 recorded 2), and fix 2 edits the parametrization that *produces*
its two node ids, so the node-id set is exactly what could have moved. The other three
boundaries (`TG-0`, `TG-2`, `TG-3`) are **not** re-run: nothing in the pass-2 diff touches
their rows or their production sites, they were each re-run independently by this reviewer
at pass 1 with matching node-id sets, and Worker 1 field-audited all four records.

The mutation, stated before application — it removes the boundary rather than perturbing
code near it:

- `django_strawberry_framework/types/finalizer.py::finalize_django_types` — the
  `loaded_attr("django_strawberry_framework.auth.mutations", "bind_auth_mutations")` lookup
  **and** its `if bind_auth is not None:` guard replaced by
  `from ..auth.mutations import bind_auth_mutations` plus a direct call, so phase 2.5
  imports the auth subsystem unconditionally instead of reaching it only when already
  loaded. This file is **outside cohort B's writable list**, touched under
  `docs/builder/worker-3.md`'s source carve-out: recorded here before the edit, one
  mutation at a time, reverted inside this pass, revert proved by byte comparison, and
  `git diff --stat -- django_strawberry_framework/types/` empty afterwards.

Mechanism: `uv run python scripts/prove_failability.py
docs/builder/temp-tests/040-slice-6/proofs.json --only 2 --scratch-root <outside-repo>`,
which runs the anchor check first (so a live prior mutation aborts the entry having written
nothing), copies the target outside the repository, runs the unmutated baseline, mutates,
runs, restores in a `finally`, and proves the restore by `filecmp.cmp(shallow=False)` plus
SHA-256. `git checkout` / `stash` / `restore` are never used: the tree is legitimately dirty
with this build's work and the concurrent `spec-050` session's.

### Independent failability re-run — results

| Boundary | W2 pass-1 rows | W2 pass-2 rows | W3 pass-2 rows | Node-id set | Errors | Restore proof |
|---|---|---|---|---|---|---|
| `django_strawberry_framework/types/finalizer.py::finalize_django_types` | 2 | 2 | **2** | **identical** to both | 0 | `filecmp.cmp(shallow=False)` True; sha256 `5ee9ea3c8a3ed6cc…` == `5ee9ea3c8a3ed6cc…` (vs the pre-mutation copy outside the repo) |

Scope as run, unchanged from Worker 2's record:
`uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/auth/`.

The set, re-measured by this pass:

- `tests/auth/test_mutations.py::test_finalize_in_an_auth_free_process_never_imports_the_auth_subsystem[finalize]`
- `tests/auth/test_mutations.py::test_finalize_in_an_auth_free_process_never_imports_the_auth_subsystem[schema]`

- mutant: `2 failed, 193 passed`, pytest exit 1; pre-mutation state of that same scope:
  `195 passed`, pytest exit 0, so 0 pre-existing failing rows were differenced out.
- collection / setup errors: **0** (independently corroborated: `uv run pytest tests/auth/
  --no-cov -q --collect-only` reports `195 tests collected`, and the unmutated
  `uv run pytest tests/auth/ --no-cov -q` reports `195 passed`).
- no zero-row entry, so no `why 0` judgement is owed.
- the dispatched rows **are** the failing set, and 2 clears the 0-or-1 weakly-pinned rule.

**Every field `docs/builder/BUILD.md` `### What gets recorded` requires is present in Worker 2's
pass-2 record**, audited field by field: boundary by symbol-qualified path; the exact mutation,
which removes the reach rather than perturbing code near it; the failing node ids **listed**
with the scope as run; the collection/setup error count separately (`0`); the pre-mutation state
of that same scope; the revert proved by byte comparison; and an explicit statement that no
`why 0` is owed. The `PARTIAL RECORD` label the tool stamped on the `--only 2` report is correct
and is discharged here: the other three boundaries are named above as accepted on the pass-1
records, which this reviewer re-ran independently at pass 1 with matching sets and Worker 1
field-audited.

**Where the second pair of eyes landed this pass:** re-run — `types/finalizer.py::finalize_django_types`.
Accepted on the standing pass-1 records — `auth/mutations.py::_transport_prologue`,
`auth/mutations.py::_REGISTER_PROTECTED_FIELDS`, `types/resolvers.py::_check_n1`.

**Carve-out conditions met.** One mutation, made only after the record above; restored inside
this pass by the tool's `finally` and byte-proved; afterwards
`git diff --stat -- django_strawberry_framework/types/` and
`git status --short -- django_strawberry_framework/types/` are both **empty**, no
`ACTIVE-MUTATION.json` survives anywhere in the tree, and the anchor is back to exactly one
occurrence (`grep -c 'bind_auth = loaded_attr(' django_strawberry_framework/types/finalizer.py`
→ `1`; `prove_failability.py --check-anchors-only --only 2` exits 0). Cohort B's own diffstat is
unchanged by the re-run: `6 files changed, 365 insertions(+), 72 deletions(-)`.
`git checkout` / `stash` / `restore` were never used.

### Pinned-text verification, character for character

Not by paraphrase: each landed block was extracted to a scratch file outside the repository and
`diff`ed against the block Worker 1 pinned in `## Final verification (Worker 1)`.

| Fix | Pinned at | Landed at | Result |
|---|---|---|---|
| 1 — `D-N3` comment | artifact `:1609-1615` | `django_strawberry_framework/auth/mutations.py:1197-1203` | `diff` empty; both files sha1 `732ba895f31d9fbecd3a7372dd52d9b4aefab640`. Worker 2's own quotation of it in `## Build report (Worker 2, pass 2)` `### Files touched` (`:2041-2047`) also diffs empty against both |
| 2 — parametrize shape | artifact `:1638-1643` (Worker 3's pass-1 shape, endorsed verbatim by Worker 1) | `tests/auth/test_mutations.py:471-476` | `diff` empty |
| 3 — `TG-1` docstring | artifact `:1687-1693` | `tests/auth/test_mutations.py:482-488` | `diff` empty |

No silent improvement of pinned wording: zero characters differ in any of the three.

Worker 2's stated numbers re-derived rather than accepted (`BUILD.md` `## Claims are proven
mechanically`): the comment's per-line lengths measure `86, 86, 87, 88, 85, 80, 41` — exactly the
figures reported — and the docstring's longest replacement line is `80`, also as reported. Both
files carry **0** non-ASCII lines (`LC_ALL=C grep -c '[^ -~]'`), so `AGENTS.md` rule 17's
ASCII-only rule for `.py` holds.

### Fix 1 resolves the defect, not merely reworded

Read in this order, at source, this pass:

1. **Spec `D-N3`** (`docs/SPECS/spec-040-auth_mutations-0_0_13.md`, `## Helper-reuse obligations (DRY)`):
   "register wires **no** relation-visibility helper of its own. **The stock user model's**
   narrowed `Meta.fields` carries no relation input at all, and a custom model whose
   `REQUIRED_FIELDS` names a forward FK gets the standard `<field>_id` input through the shared
   decode's own relation handling — so **the rider inherits whatever the shared path does and
   adds nothing**, which is what keeps registration from acquiring a second, auth-local
   visibility rule."
2. **The Custom-user-models edge case** (`## Edge cases and constraints`): "a `REQUIRED_FIELDS`
   entry that is a forward FK becomes the standard `<field>_id` input (the model-column
   converter's relation rule)."
3. **The rationale companion's `D-N3` entry**: the retired reason was the unqualified "the
   narrowed `Meta.fields` has no relation inputs"; "Both cannot be true", so the item "drops the
   false reason, stating instead that the rider inherits the shared decode's relation handling
   and adds nothing."
4. **The landed comment.**

Clause by clause, the landed comment now carries **both** clauses whose absence was the finding:

- the **scope clause** — `the stock user model's narrowed ``Meta.fields`` carries no relation
  input at all`. Present, and word for word the spec's qualifier. This is what stops conjunct 2
  from being the retired general proposition;
- the **bridging clause** — `so the rider inherits whatever the shared path does and adds
  nothing`. Present. It is the inference that joins the FK conjunct to the conclusion, which
  pass 1's comment jumped over.

**Internal consistency, which is the actual test:** conjunct 2 is now scoped to the stock user
model and conjunct 3 speaks about a custom model, so the two no longer contradict each other,
and the conclusion (`never acquires a second, auth-local visibility rule`) follows through the
bridging clause rather than sitting beside an unexplained contradiction. The comment is a
faithful restatement of the **current** `D-N3`, which cohort A has closed and which does not
move again. The one wording difference from the spec is the subject — `The narrowing wires` for
the spec's `register wires` — which is correct in place, since the comment annotates the
`fields = register_fields` narrowing and names the rider explicitly one clause later.

`CG-1`'s postcondition re-run by this pass: `rg -n 'D-N1|D-N2|D-N3' django_strawberry_framework/`
→ four hits, one `D-N3`, at `auth/mutations.py:1197`.

### Fix 2 changed no behaviour beyond removing dead weight

- **Both node ids still exist and still mean what they meant.** `uv run pytest tests/auth/
  --no-cov -q --collect-only` collects `test_finalize_in_an_auth_free_process_never_imports_the_auth_subsystem[finalize]`
  and `[schema]` — the same two ids, because `ids=["finalize", "schema"]` supplied them before
  and after. The re-run above is the stronger evidence: the same two ids are what fail when the
  boundary is removed, so the ids still *reach* the boundary and are not merely present.
- **No other row referenced the removed parameter.** `_FINALIZE_DRIVER_BODY`,
  `_SCHEMA_DRIVER_BODY` and `_AUTH_UNIMPORTED_ASSERT` have exactly one reader each, all inside
  this parametrization (`grep -rn` across `tests/`, `examples/`, `django_strawberry_framework/`),
  and `del label` exists nowhere in `tests/` any more (the only `label` hits in the file are
  `_unique_app_label`, an unrelated pre-existing helper).
- **The row's body is untouched**: `_auth_free_subprocess(driver + _AUTH_UNIMPORTED_ASSERT)`.
  The parametrize list, its `ids=`, and the assertion are the same; only the argnames string,
  the dead parameter and its `del` went.
- `uv run pytest tests/auth/ --no-cov -q` → **195 passed**, the same count every prior pass
  recorded, which is what a pass adding no row must produce;
  `uv run pytest examples/fakeshop/test_query/test_auth_api.py --no-cov -q` → **21 passed**.

### AST-identity re-check, with its positive control

Run by this pass against `git show HEAD:<path>` written to a scratch path **outside** the
repository (never `git checkout`, per `BUILD.md` `## Claims are proven mechanically`):

```shell
$ uv run python docs/builder/temp-tests/040-slice-6/ast_identity.py <HEAD copy> <working tree>
django_strawberry_framework/auth/mutations.py      IDENTICAL   (exit 0)
tests/auth/test_mutations.py                       DIFFERENT   (exit 1)
```

`auth/mutations.py` is `IDENTICAL` with docstrings stripped, so the **whole** production diff
against HEAD — pass 1's module-docstring `F2` edit plus pass 2's seven-line comment replacement —
changes no executed statement. Confirmed by reading the diff as well as by the instrument:
`git diff -- django_strawberry_framework/auth/mutations.py` is two hunks, one module docstring
and one `#` comment block, with `fields = register_fields` and `permission_classes` untouched
beside it.

`tests/auth/test_mutations.py` is legitimately `DIFFERENT`, and **both** stated reasons are the
real ones, checked in the diff rather than accepted: (a) pass 1 added real rows, the
`_auth_free_subprocess` helper and the `optimizer=` / `declare=` seams; (b) pass 2 removed a
function parameter and a `del` statement, which are executable code that a docstring-stripped
AST can see. The docstring half of pass 2's change is invisible to this instrument by
construction, which is why node-id collection above carries that half instead.

**Controls, so neither reading is an instrument that cannot fail** (`START.md` `## Instruments
that lie`):

- **positive** — the HEAD copy of `auth/mutations.py` versus the same file with one appended
  `X_CONTROL = 1`: `DIFFERENT`, exit 1. The instrument can fail;
- **negative** — the same HEAD copy versus itself with one appended `#` comment: `IDENTICAL`,
  exit 0. So `DIFFERENT` is not what this instrument prints for any edit at all.

### High:

None.

### Medium:

None.

### Low:

None.

Both pass-1 Lows are closed: the dead `label` argument is gone (verified above), and the
`[finalize]` / `[schema]` independence claim is gone from the **shipped docstring** — the half
this reviewer failed to follow into the source at pass 1 — with Worker 1 having corrected the
artifact half in its own section. The replacement docstring's substantive claim was re-derived
rather than accepted: `rg -c 'finalize' django_strawberry_framework/schema.py` returns **0**, so
`DjangoSchema` does not finalize on its own, and `_SCHEMA_DRIVER_BODY` calls
`finalize_django_types()` itself before `DjangoSchema(query=Q)` — `[schema]` is a superset
driver, exactly as the new text says.

Carried forward from this, as a reading discipline rather than a finding: a false claim recorded
in an artifact is frequently also live in the code, and the artifact is the cheaper place to
notice it. Every prose claim graded in this pass was chased to its source file before being
graded.

### DRY findings

**No new duplication arrived with the fixes.** The pass-2 delta is one comment block, one
docstring, one argnames string and two deleted lines; it adds no logic, no literal, no helper,
and no branch. Nothing in it can be a near-copy of anything.

**The two intra-file near-copies stand, routed to the integration pass — still the right call,
re-derived this pass rather than inherited:**

- `tests/auth/test_mutations.py:1218-1226` and `:1250-1258` — the `PrivilegeRequiredUser` bodies
  are still byte-identical (`diff` of the two nine-line regions is empty), with their identical
  `pytest.raises(ConfigurationError, match=…)` regex;
- `tests/auth/test_mutations.py:943-948` and `:963-968` — the sessionless assertion blocks are
  still byte-identical (`diff` empty).

Neither was touched this pass, so **neither was made worse**. Worker 1's ground for deferring
them also still holds: their correct shape depends on whether `tests/auth/_helpers.py` is opened,
and `_helpers.py` is **not** on cohort B's writable list (the Plan's `### Scope, ownership, and
the two hard prohibitions` enumerates that list and `_helpers.py` is absent from it). Landing
file-local versions now would guarantee the integration pass rewrites them a second time in the
same file. The condition that flips the answer is recorded unchanged: if the integration pass
decides not to open `_helpers.py`, both collapse to file-local helpers and should land there, in
one loop over this file rather than two.

The remaining routed items are unchanged and not re-argued: the cross-file `_declare_group_type`
pair, the four-way subprocess-isolation near-copy, and the pre-existing `_CH_LOGOUT` / `_LOGOUT_Q`
byte-duplicate.

**Existence challenge:** none raised this pass. The pass introduces no helper, registry, token,
or indirection layer; `::_auth_free_subprocess` was challenged and answered at pass 1 and is
unchanged.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty**: no change to `__all__` and
no change to the re-export list. Consistent with a pass whose entire production delta is one
comment block, proved AST-identical above.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

Verified rather than assumed: `git diff -- CHANGELOG.md` is empty.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces.

Verified rather than assumed: this pass's two modified files are
`django_strawberry_framework/auth/mutations.py` and `tests/auth/test_mutations.py`. The spec
edits dirty in the tree (`docs/SPECS/spec-040-auth_mutations-0_0_13.md` and its rationale
companion) are **cohort A's** closed work and were read-only here; the `spec-050` session's files
were neither edited, reverted, stashed nor checked out (`AGENTS.md` rule 34).

### What looks solid

- **Three pinned texts, three character-identical landings.** The failure mode this check exists
  to catch — a builder silently improving pinned wording — did not occur in any of the three,
  including the one where the pinned block is a comment whose indentation and hyphenation a
  formatter could plausibly have touched.
- **The `D-N3` comment is now a faithful restatement of a settled spec sentence**, carrying the
  scope clause and the bridging clause, and internally consistent conjunct to conjunct. The
  defect class the slice exists to remove — false prose beside correct code — is closed at this
  site rather than reworded.
- **The re-proved boundary's node-id set is stable across three independent measurements** (W2
  pass 1, W3 pass 1, W2 pass 2) and a fourth here, at one scope, with the same `195 passed`
  baseline and 0 collection errors each time. Removing the parametrize member changed the
  argnames and not the ids, exactly as `ids=` already supplying them predicts.
- **Worker 2 re-ran the one proof its own edit could have invalidated and left the other three
  alone**, which is the correct scoping: re-measuring untouched boundaries would have added
  noise, and skipping this one would have left the ids' reach asserted rather than measured.
- **Both instruments used here were controlled before their readings were trusted** — the
  AST-identity check in both directions, and the anchor check that precedes the mutation.
- **The transient mutation left nothing behind.** `types/` is byte-clean by diff, by status, by
  anchor count and by the tool's own byte comparison.
- Worker 2 reported the `spec-050` session's churn (`bld-slice-3-…md` now modified,
  `bld-003-final.md` gone) rather than acting on it — the correct handling under rule 34.

### Temp test verification

- No new temp test was written this pass; none was needed. The re-run used
  `scripts/prove_failability.py` over the existing manifest
  `docs/builder/temp-tests/040-slice-6/proofs.json`, and the inverse proof used the existing
  `docs/builder/temp-tests/040-slice-6/ast_identity.py`.
- This pass's own tool report is written outside the repository, in the session scratchpad
  (`…/failability-w3-pass2/w3-pass2-tg1.md`), so it adds nothing to the tree. Worker 2's
  `docs/builder/temp-tests/040-slice-6/pass2-tg1-proof.md` was read and matches the record.
- Disposition of the whole `temp-tests/040-slice-6/` directory: unchanged from pass 1 — probe
  scripts and the identity helper stay as gitignored cycle scratch, promoted nowhere. Nothing in
  it is the sole proof of shipped behaviour; every behaviour they probed is pinned by a permanent
  row in `tests/auth/`.

### Static helper use

`scripts/review_inspect.py` was **not** re-run this pass, and the skip is recorded with its
reason: `docs/builder/BUILD.md` `### When to run the helper during build` triggers it for a new
`.py` file, a file under `optimizer/` or `types/`, or 30+ lines of new logic in a package file /
50+ outside it. This pass adds **zero** lines of logic anywhere — one comment block, one
docstring, one argnames string, two deletions — and its production file is proved AST-identical
to HEAD. The pass-1 overviews (including `docs/shadow/helper-inventory-040-slice-6.md`) are
unchanged by a delta that alters no executable token in the package, so re-running would
reproduce them byte for byte.

### Notes for Worker 1 (spec reconciliation)

- **No spec edit is implied by this pass.** The landed comment now tracks `D-N3` as it reads at
  the settled spec; nothing cohort B shipped falsifies a spec sentence, and Definition-of-done
  item 6 stays true (a `D-N3` comment exists at `::_synthesize_register_rider`; only its wording
  changed).
- **Worker 2's one flagged instruction conflict is confirmed harmless.** The dispatch named the
  rationale companion as required reading for a role whose own standing file lists it as a
  forbidden read; Worker 2 followed the role file and did not read it. Nothing was lost: the
  replacement text was pinned verbatim, and this reviewer — for whom the companion **is**
  permitted reading — checked the `D-N3` entry and confirms the landed comment matches what that
  entry says the item was corrected to. Worth reconciling the dispatch template against
  `worker-2.md` so the next builder is not handed the same conflict.
- **Still routed to the integration pass, unchanged:** the two intra-file near-copies in
  `tests/auth/test_mutations.py`, the cross-file `_declare_group_type` pair, the four-way
  subprocess-isolation near-copy, and the pre-existing `_CH_LOGOUT` / `_LOGOUT_Q` duplicate — with
  the `_helpers.py` condition recorded above deciding the first two's shape.
- **Cosmetic, unchanged and not blocking:** the `<fill in …>` boilerplate line inside the pass-1
  `### Failability proofs` block is still there, because `docs/builder/ARTIFACT.md` forbids
  editing prior entries. There are no unfilled placeholders in it.

### Review outcome

`review-accepted`. All three pinned fixes landed character for character; fix 1 carries the scope
and bridging clauses and is internally consistent, so it resolves the defect rather than rewording
it; the re-run `TG-1` record carries every required field and its node-id set is identical to
Worker 2's at the same scope with 0 collection errors; fix 2 is behaviour-neutral with both node
ids intact and no other reader of the removed parameter; the AST-identity claims re-check with a
working positive control; no new fail-open shape and no new duplication arrived; and the two
deferred DRY items stand correctly routed and unworsened. No High, Medium, or Low finding remains
open.

Status: review-accepted.

---

## Final verification (Worker 1, pass 2)

**Outcome: `final-accepted`.** The three defects the prior final verification held the slice for
are closed, and closed as pinned rather than as paraphrased. One cross-slice spec correction was
necessary and is recorded under `### Spec changes made (Worker 1 only)`: re-asking the
reconciliation question against the *changed* comment text — rather than inheriting last pass's
`None` — turned up the retired `D-N3` reason clause still alive at its parallel site in
Decision 6's own body.

### 1. The three pinned replacements — re-derived, not accepted

Worker 3 reported character-for-character `diff` equality. I re-ran the comparison myself rather
than reading its acceptance as discharge, extracting both sides to a scratch path outside the
repository:

| Fix | Pinned block | Landed block | Result |
|---|---|---|---|
| 1 — `D-N3` comment | this artifact `:1609-1615` | `django_strawberry_framework/auth/mutations.py:1197-1203` | `diff` empty; both sha1 `732ba895f31d9fbecd3a7372dd52d9b4aefab640` |
| 2 — parametrize shape | this artifact `:1638-1643` | `tests/auth/test_mutations.py:471-476` | `diff` empty; both sha1 `7867c6835f1b07e26ca62e372873e682c36ad681` |
| 3 — `TG-1` docstring | this artifact `:1687-1693` | `tests/auth/test_mutations.py:482-488` | `diff` empty; both sha1 `87e49ad9455f11248610789ca106521c74a8a0f9` |

Instrument controlled before the readings were trusted: the same `diff` over the pinned block
versus a copy of it with one appended `# control` line reports a difference. A `diff` that cannot
fail is a passing proof (`START.md` `## Instruments that lie`). Worker 3's sha1 for fix 1
reproduces exactly; fixes 2 and 3 it reported as `diff`-empty without a digest, and the digests
above are this pass's own.

**`D-N3` re-derived as its author, which is the part a byte comparison cannot answer.** Character
equality proves the builder applied my text; it says nothing about whether my text resolves the
contradiction or relocates it. Read in order, at source, this pass:

1. spec `D-N3` (`docs/SPECS/spec-040-auth_mutations-0_0_13.md:1986-1992`);
2. the **Custom user models** edge case (`:2032-2041`);
3. the rationale companion's `D-N3` entry (the retired reason, and "Both cannot be true");
4. the landed comment.

Clause by clause the landed comment now reads: conjunct 1 normative (**no** auth-local
relation-visibility helper); conjunct 2 scoped to the **stock** user model; conjunct 3 the custom
model's `REQUIRED_FIELDS` forward FK taking the standard `<field>_id` input; then the bridging
clause ("the rider inherits whatever the shared path does and adds nothing") and the conclusion.
Conjuncts 2 and 3 no longer address the same population, so they cannot contradict each other, and
the conclusion now follows through the bridge instead of sitting beside an unexplained pair. The
only divergence from the spec sentence is the subject (`The narrowing wires` for `register
wires`), correct in place because the comment annotates the `fields = register_fields` narrowing
and names the rider one clause later, and the ASCII hyphen for the spec's em dash, which
`AGENTS.md` rule 17 requires in `.py`.

**Resolved, not relocated — proved by sweep rather than by reading the one site.** The retired
proposition has exactly one surviving spelling in the package:
`grep -rn 'no relation input' django_strawberry_framework/` returns **1** hit, and it is the
scoped one at `auth/mutations.py:1198`. The same sweep across `docs/SPECS/` is what found the
parallel site the spec still carried — see duty 6.

### 2. The re-run `TG-1` failability record — complete, and the failing set unchanged

My delta is the record audit, not a third run. Worker 2's pass-2 entry and the tool report at
`docs/builder/temp-tests/040-slice-6/pass2-tg1-proof.md` were audited field by field against
`docs/builder/BUILD.md` `### What gets recorded`:

| Required field | Present |
|---|---|
| Boundary, symbol-qualified | yes — `django_strawberry_framework/types/finalizer.py::finalize_django_types` |
| Exact mutation applied, removing the boundary | yes — the `loaded_attr` reach **and** its `is not None` guard replaced by a function-local `from ..auth.mutations import bind_auth_mutations` plus a direct call |
| Failing node ids **listed** + scope as run | yes — `[finalize]`, `[schema]`; scope `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/auth/` |
| Collection / setup errors, separately | yes — `0` |
| Pre-mutation state of that same scope | yes — `195 passed`, exit 0, 0 rows differenced out |
| Revert proved by byte comparison | yes — `filecmp.cmp(shallow=False)` True plus a SHA-256 pair against the pre-mutation copy taken outside the repository |
| **why 0** | not owed; the record says so rather than leaving it ambiguous |

The failing set is **unchanged** across all four measurements now on record (Worker 2 pass 1,
Worker 3 pass 1, Worker 2 pass 2, Worker 3 pass 2): the same two node ids, at the same scope, with
the same baseline and 0 errors. The tool's `PARTIAL RECORD` stamp on the `--only 2` run is correct
and is discharged twice in the artifact — Worker 2 names where the other three boundaries' records
stand, and Worker 3 names which one it re-ran and which three it accepted on the pass-1 records it
had itself re-run.

Confirmed by me directly, rather than read from either report:

```shell
$ git diff --stat -- django_strawberry_framework/types/                 (no output)
$ git status --short -- django_strawberry_framework/types/              (no output)
$ find . -name 'ACTIVE-MUTATION.json'                                   (no output)
$ grep -c 'bind_auth = loaded_attr(' django_strawberry_framework/types/finalizer.py       1
$ grep -c 'raise OptimizerError(f"Unplanned N+1: {field_name}{suffix}")' \
      django_strawberry_framework/types/resolvers.py                                      1
$ grep -c 'session = sessions.require_session(request, transport)' \
      django_strawberry_framework/auth/mutations.py                                       1
$ uv run pytest tests/auth/ --no-cov -q --collect-only | grep never_imports_the_auth_subsystem
<Function test_finalize_in_an_auth_free_process_never_imports_the_auth_subsystem[finalize]>
<Function test_finalize_in_an_auth_free_process_never_imports_the_auth_subsystem[schema]>
```

All three mutated anchors are back to exactly one occurrence, so no boundary is missing from the
tree. Cohort B's diffstat is `6 files changed, 365 insertions(+), 72 deletions(-)` — the figure
Worker 3 recorded after its pass-2 re-run, so nothing moved between that review and this pass.

### 3. Dispatched findings checklist — seven `- [x]`, none over-ticked, no `- [ ]`

`grep -c '^- \[x\] \*\*'` = **7**; `grep '^- \[ \]'` = **0 hits** in the whole artifact. Every tick
was re-derived at pass 1 and the three contracts this re-loop touched were re-derived again here:
`CG-1`'s comment exists at `::_synthesize_register_rider` (`rg -n 'D-N1|D-N2|D-N3'
django_strawberry_framework/` → four hits, one `D-N3`), `TG-1`'s two node ids still collect and
still fail under the mutation, and nothing in the pass-2 diff removed a `TG-0` / `TG-2` / `TG-3`
row.

**No box is over-ticked and none was un-ticked across the whole slice.** Restating the pass-1
ruling because a two-pass `revision-needed` on `CG-1` invites the opposite reading: `CG-1`'s
dispatched contract was that a `D-N3` source comment exist at that site. It landed at pass 1 and
the defect was the comment's **content**, which pass 2 fixed. Un-ticking would have been a false
record of what happened and would have told the builder to write a comment that already existed.
No deferral reason is owed under `### Spec changes made (Worker 1 only)` for a checklist box.

### 4. No fail-open shape, no new duplication, from the three fixes

The pass-2 delta is one `#` comment block, one docstring, one argnames string, and two deletions —
it contains no expression at all, so there is no clamp, `getattr` default, `or` fallback, broad
`except`, or truthiness test to grade. Read rather than inferred from the green suite; a sweep of
every added line across the whole six-file cohort diff for the catalogued shapes returns one hit,
and it is the word `exception` inside a docstring. The two decision sites the slice does add
(`if optimizer is not None` / `if optimizer is None`) were graded at pass 1 and are untouched here.

`del label` is gone: `grep -rn '\bdel label\b' tests/` → **0**. Worth recording the instrument, not
just the result — the unanchored `grep -rn 'del label' tests/` returns **9** hits, every one of
them the substring inside `model label`. A word-boundary-free sweep here would have reported the
fix as not landed.

No new duplication: the delta adds no logic, literal, helper, or branch, so nothing in it can be a
near-copy. The two intra-file near-copies were not touched and so were not made worse; `diff` of
each pair's regions is still empty, which is the condition under which deferring them stays honest.

### 5. Focused tests

```shell
$ uv run pytest tests/auth/ examples/fakeshop/test_query/test_auth_api.py --no-cov -q
216 passed in 9.18s
```

216 = the 195 + 21 every prior pass recorded, which is what a re-loop adding no row must produce.
**Nothing failed, so no attribution question against the concurrent `spec-050` session arose** —
recorded as a fact about this run, not as a claim that the two never interact.

### 6. Spec reconciliation — ONE cross-slice correction, and why it was necessary

Last pass answered `None`. Re-asked against the changed comment text rather than inherited, the
answer is no longer `None`.

The landed `D-N3` comment now states the **scoped** claim in shipped source. Sweeping the settled
spec for that claim's other homes — the sweep the comment's own wording makes obvious and which no
prior pass ran — found the retired proposition alive in **Decision 6's own body**
(`docs/SPECS/spec-040-auth_mutations-0_0_13.md`, `### Decision 6`): "Because the narrowed set has
**no relation inputs** (`groups` / `user_permissions` are excluded), register wires **none** of
the relation-visibility helpers …; they return for free via the inherited decode **only if** a
consumer ever widens `Meta.fields`". Both halves are the sentence Slice 4 deleted from `D-N3`:

- `django_strawberry_framework/auth/mutations.py::derive_register_fields` rejects only the five
  protected names, so a custom model may place a forward FK in `REQUIRED_FIELDS`;
- the **Custom user models** edge case says that entry "becomes the standard `<field>_id` input",
  with no widening at all.

So the unqualified reason is false for the same case that made it false in `D-N3`, and the
"only if a consumer ever widens" clause is false on its face beside the edge case. Three of a
contract's five homes now disagreed: the obligations list (corrected), the edge case (correct),
and the Decision (uncorrected).

**Why it was missed and why this pass is where it surfaces.** Slice 3's audit row `D6.10` graded
only Decision 6's **normative** clause ("register wires none of the relation-visibility helpers")
and never its reason; Slice 4 graded the reason, but at `D-N3`. Neither pass held both halves of
the same Decision at once. `START.md` `## Instruments that lie`: "Partial claim fix = dominant
residual defect. One spelling fixed, parallel site still live → cycle reopens."

**Why I edited rather than routed it.** `docs/builder/worker-1.md` `## Review-round custody` makes
reconciling *every* sentence a decision falsifies a custodian duty in the same pass, and calls a
half-reconciled spec worse than an un-updated one because the reader cannot tell which half is
current. I am the custodian and the only role that may write the spec; routing a known
contradiction to the integration pass would have left the shipped comment stating the scoped
contract while the Decision it points at stated the retired one. The edit is minimal, preserves
the normative half and the `D-N3` pointer verbatim, and touched no other sentence.

Nothing else reconciles. Re-checked against the changed text specifically:

- **Definition of done item 6** (`:2552`) — "the three deliberate non-reuse points carry their
  source comment" is still **true**; pass 2 changed the comment's wording, not its existence.
- **The test plan's finalizer row** — says "**finalizes** (or builds a schema)", a parenthetical
  alternative driver, and makes no independence claim. The pass-2 docstring replacement therefore
  falsifies nothing there; it moves the docstring *toward* the spec's own weaker wording.
- **The parametrize change** touches no spec sentence: node ids are unchanged, and the spec names
  no argnames.
- `check_citations.py --check` → `OK: 979 citations resolve`;
  `check_spec_glossary.py --spec docs/SPECS/spec-040-auth_mutations-0_0_13.md` → `OK: 30 terms`;
  `check_trailing_commas.py --check` over both edited Markdown files → exit 0. Explicit paths
  passed, never a bare repo-wide run, which would auto-fix the concurrent session's files.

### 7. The Worker 0 dispatch error — resolved, and it cost nothing

Worker 0's apply-changes dispatch listed the spec's `-rationale.md` companion in Worker 2's
required reading. `docs/builder/BUILD.md` `## Required reading per worker` marks that file
**never** for Worker 2, and `### Who reads it, and when` says the exclusion *is* the point of the
rationale move. Worker 2 declined the read, cited the rule, and recorded the refusal; Worker 3
confirmed the entry. Worker 0 has already logged the error in the build plan. My assessment, which
is the open half:

- **Nothing in the pass was compromised.** Worker 2's entire task was to apply three blocks of
  text pinned verbatim, and all three landed character-identical (duty 1). No content the rationale
  carries could have changed that output, so the counterfactual read has no effect to point at.
- **The check the rationale exists to enable was still performed, by the role that owns it.**
  Worker 3, for whom the companion **is** permitted reading, read the `D-N3` entry and confirmed
  the landed comment matches what that entry says the item was corrected to. The verification did
  not go unperformed; it went to the right desk.
- **Compliance would have been the defect.** Reading it would have put the deliberative layer in
  front of the one role the move exists to keep it away from, and the refusal is the mechanism
  working. The worker was right and the dispatch was wrong, which is exactly how Worker 0 recorded
  it.
- **The one thing the episode did not cost, stated so it is not later mis-attributed:** the
  Decision-6 residual in duty 6 was **not** missed because of this. The rationale's `D-N3` entry
  names only `D-N3` by heading; finding the parallel site required grepping the spec, which is the
  custodian's duty, not the builder's, and it is discharged above.
- One navigational nit for Worker 0, recorded rather than fixed because the build plan is not this
  pass's file: the plan's entry attributes the required-reading matrix to
  `docs/builder/worker-1.md`. The matrix lives in `docs/builder/BUILD.md`; `worker-1.md` points at
  it. The ruling is right either way.

**Disposition: closed.** The integration pass and the maintainer should read this as a resolved
item, not an open one. The standing fix is the one Worker 0 already named — walking the matrix
column by column when building a spawn prompt.

### What the integration pass inherits from this slice

Enumerated here at artifact top level, each with the condition that would change the answer, so
the items survive the slice rather than closing with the review section that raised them.
`docs/builder/BUILD.md` `## Cross-slice integration pass` step 5 walks every accepted artifact's
`DRY findings`, and all three DRY items below are also live in Worker 3's pass-2 `### DRY
findings`, re-derived there rather than inherited — so they are reachable by both routes.

1. **`tests/auth/test_mutations.py` — the duplicated `PrivilegeRequiredUser` body and its
   `pytest.raises(ConfigurationError, match=…)` regex** (`:1218-1226` / `:1250-1258`, `diff`
   empty). **Condition:** if the integration pass opens `tests/auth/_helpers.py`, the model factory
   and the regex constant belong there; if it decides **not** to open `_helpers.py`, both collapse
   to file-local helpers and should land in that same loop, not a later one.
2. **`tests/auth/test_mutations.py` — the duplicated sessionless-`ConfigurationError` assertion
   block** (`:943-948` / `:963-968`, `diff` empty). Same condition, same loop.
3. **The cross-file `_declare_group_type` pair**, plus the pre-existing `_declare_user_type` pair
   it matches, across `tests/auth/test_mutations.py` and `tests/auth/test_queries.py`. Accepted
   deliberately at plan time because `tests/auth/_helpers.py` is outside cohort B's writable list.
   **Condition:** the hoist is available the moment `_helpers.py` is writable; nothing else blocks
   it.
4. The four-way subprocess-isolation near-copy (`tests/auth/test_mutations.py`,
   `tests/auth/test_sessions.py`, `tests/base/test_init.py`,
   `tests/rest_framework/test_soft_dependency.py`) — this slice already collapsed the two copies
   inside its own file into `::_auth_free_subprocess`.
5. `tests/auth/test_mutations.py:2508`'s `_CH_LOGOUT` duplicating `:300`'s `_LOGOUT_Q`
   byte-for-byte. Pre-existing at HEAD, untouched by this diff.
6. For the maintainer, out of this cohort's population: the `spec-042 Revision N` citations in
   `tests/middleware/test_debug_toolbar.py`, and the bug-hunt round-provenance comment in
   `tests/auth/test_sessions.py`.
7. Already on Worker 0's list: `bld-040-slice-1-rationale_extraction.md`'s link to the retired
   Decision 11 anchor, and Slice 4's two un-edited `WIP-ALPHA-040-0.0.13` sites.
8. Cosmetic, unfixable in place: line 888's `<fill in …>` tool boilerplate inside the pass-1
   `### Failability proofs` block. There are no unfilled placeholders;
   `docs/builder/ARTIFACT.md` forbids editing a prior entry, so it stays.

**One instrument hazard for whoever runs the integration pass, since it would fail silently.**
`docs/builder/BUILD.md` `## Cross-slice integration pass` step 1 names
`docs/builder/bld-slice-*.md`. This cycle's artifacts are `bld-040-slice-<N>-*.md`, and the
concurrently active `spec-050` cycle's artifacts **are** `bld-slice-1-*.md` … `bld-slice-5-*.md`,
sitting in the same directory right now. A literal glob would read five artifacts of the wrong
cycle and report a clean sweep. Read this cycle's artifacts by the names in the build plan's
`## Artifact list`. Also note the build plan's own "Open for the integration pass" list carries
only items 7 above; items 1-6 live in this artifact, which the plan's artifact list names.

### Summary

The re-loop closed all three defects the prior verification held the slice for, and closed them as
pinned: the `D-N3` comment now carries the scope clause and the bridging clause and is internally
consistent conjunct to conjunct; the `TG-1` docstring no longer claims two node ids can regress
independently; the dead `label` argument is gone with its `del`. All three landed character for
character against the pinned text, verified here with a controlled `diff`. The re-run `TG-1`
failability record carries every required field and its node-id set is identical across four
independent measurements; `types/` is byte-clean by diff, by status, and by anchor count, and no
`ACTIVE-MUTATION.json` survives anywhere. Seven checklist boxes stand correctly ticked, none
over-ticked, none open. No fail-open shape and no new duplication arrived with the fixes, and the
focused scope is green at 216.

The slice also produced one thing no pass before it could: writing the scoped `D-N3` claim into
shipped source is what exposed the same retired claim still standing in Decision 6's body, three
homes of one contract disagreeing. That is corrected as a cross-slice edit into cohort A's closed
work and recorded below.

Status: `final-accepted`.

### Spec changes made (Worker 1 only)

**One correction, into cohort A's closed work, as duty 6 proved necessary.**

1. `docs/SPECS/spec-040-auth_mutations-0_0_13.md` `### Decision 6`, the
   `Meta.fields` narrowing bullet (`:1138-1145` after the edit; `:1138-1143` before it).
   **Reason:** the bullet carried the reason clause Slice 4 retired from `D-N3` — "the narrowed
   set has **no relation inputs**" plus "they return for free via the inherited decode **only if**
   a consumer ever widens `Meta.fields`" — both falsified by the **Custom user models** edge case,
   since `::derive_register_fields` rejects only the five protected names and a `REQUIRED_FIELDS`
   forward FK therefore takes the standard `<field>_id` input with no widening. The reason is now
   scoped to the **stock** user model and states that whatever relation handling a narrowed set
   needs comes for free via the inherited decode, matching `D-N3` and the edge case. The normative
   half ("register wires **none** of the relation-visibility helpers"), the helper list, and the
   `D-N3` pointer are unchanged. **Triggered by:** Slice 6's `D-N3` source comment, whose scoped
   wording is what made the parallel site visible.
2. `docs/SPECS/appx/spec-040-auth_mutations-0_0_13-rationale.md` `## Decision 6`,
   `### Changes this Decision underwent`. **Reason:** the correction above owes its retraction
   record in the companion, keyed to the Decision it belongs to
   (`docs/builder/BUILD.md` `## Spec rationale extraction`). Two inserted bullets, nothing
   rewritten or deleted: one post-ship entry stating what the Decision carried, why it was false,
   why Slice 3's `D6.10` row did not catch it, and what replaced it; one `**No longer claims:**`
   bullet naming the two retired propositions.

No source file, test, or checklist box was edited by this pass. Gates re-run after both edits:
`check_citations.py --check` → `OK: 979 citations resolve`; `check_spec_glossary.py --spec …` →
`OK: 30 terms`; `check_trailing_commas.py --check` over both files → exit 0.

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
