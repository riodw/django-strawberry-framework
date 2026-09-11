# Build: Slice 3 — conformance audit B (`register_mutation` + `current_user`)

Spec reference: `docs/SPECS/spec-040-auth_mutations-0_0_13.md` (Decisions 6, 7, 8 at lines 1084-1487; Decision 12 at lines 1717-1750; `## User-facing API` / `### Error shapes` register + `me` paragraphs at lines 727-781; `## Slice checklist` Slice 2 + Slice 3 blocks at lines 322-399)
Status: final-accepted

## Plan (Worker 1)

A **retrospective conformance audit**, not a build. It ships no source change. Its
instrument is the checklist plus the conformance matrix below; its output is spec
edits (`SPEC-STALE` rows), hand-offs to later slices, and — had there been any — code
gaps. There were none.

Slice 2 found every divergence running one direction and this pass deliberately did
not inherit that prior: the maintainer named this half — a synthesized class, a cached
rider, a narrowed field derivation, a bind-materialized return alias — as where a
planned feature could most plausibly have shipped partially. So every Decision-6
pipeline step was graded **individually and in order** against source, and the
`0.0.13` release tree (`3a294082`) was read directly wherever the current shape and
the spec disagreed, to separate "never built" from "built, then moved".

The answer is the same as Slice 2's, but measured rather than assumed: **nothing was
dropped.** Every step Decision 6 specifies is present at `3a294082`, including the
ones the spec states most narrowly (the four-tuple decode hand-off, the
provided-marker-preserving exclusion seam, `set_password` before `full_clean`, the
plaintext assertion on both resolver paths). Four of the six Decision-6 divergences
are post-release movement; two were inaccurate on their own date.

### DRY analysis

**Helper inventory checked.** Refreshed package-wide against `HEAD` for this pass by
reading the register/`current_user` surface and its callees directly rather than
re-running the AST dump. Shapes searched: `derive_register_fields` /
`editable_input_fields` / `input_field_required` (the narrowing), `_model_decode_step`
/ `_decode_relations` / `decode_provided_fields` / `iter_provided_input_fields` /
`mutation_input_field_specs` / `excluded_attrs` / `EXCLUDED` (the exclusion seam),
`run_write_pipeline_sync` / `_run_pipeline_sync` / `_model_write_step` /
`_full_clean_or_field_errors` / `save_or_field_errors` (the skeleton and the shared
tail), `field_error` / `null_field_error` / `unencodable_text_error` /
`validation_error_to_field_errors` (the envelope leaf ctors), `build_payload_type` /
`bind_mutation_outputs` / `bind_write_declarations` / `materialize_generated_input_class`
/ `make_input_namespace` (the bind and emit ledgers), `_lazy_ref` /
`build_lazy_field_signature` (the signature injection), and
`_authenticated_actor_or_none` (the shared anonymity rule). Every relevant candidate
was found already reused **by call**. No new helper is proposed and none could be:
this slice writes no `.py`.

- **Existing patterns reused.** None to introduce. The audit *verified* reuse:
  `auth/mutations.py::derive_register_fields` delegates the unknown/non-editable
  reject to `mutations/inputs.py::editable_input_fields`;
  `::_register_decode_step` rides `mutations/resolvers.py::_model_decode_step`;
  `::_register_write_step` closes through `resolvers._model_write_step`;
  `::_run_register_pipeline_sync` rides `resolvers.run_write_pipeline_sync`;
  `queries.py::_current_user_resolve_body` reuses
  `mutations.py::_authenticated_actor_or_none` and
  `mutations/resolvers.py::authorize_or_raise`.
- **New helpers justified.** None. A docs-only pass.
- **Duplication risk avoided.** Two, both documentation duplications. (a) The
  anonymity rule could end up stated in Decision 5 *and* Decision 7; Slice 2 wrote it
  into Decision 5, so Decision 7's rewrite **points at** that one statement rather
  than re-deriving it. (b) The sync/async body split could end up stated in
  Decision 7 *and* Decision 10; Slice 2 wrote it into Decision 10, so Decision 7's
  rewrite points there too. Neither Decision now carries a second copy.

### Implementation steps

1. Re-verify the spec's status/header lines (`docs/SPECS/spec-040-auth_mutations-0_0_13.md:1-111`).
2. Copy the spec's `## Slice checklist` Slice 2 and Slice 3 sub-bullets verbatim; tick
   only what is proved landed. Slice 3's boxes are doc / version-cut obligations over
   files this cycle's scope fence forbids editing — audit them **read-only**, at the
   release commit where the obligation was due, and report.
3. Decompose Decisions 6, 7, 8, 12 and the register / `me` half of
   `## User-facing API` / `### Error shapes` into individual normative claims. Grade
   Decision 6's pipeline **step by step, in order**, against source read directly.
4. For every disagreement, read `git show 3a294082:<path>` before writing a verdict —
   the release tree is what separates "never built" from "built, then moved".
5. Edit the spec for every `SPEC-STALE` row; append the explanation to the rationale
   companion under the owning Decision.
6. Discharge Slice 2's two hand-offs (items 7 and 8 of its
   `### Notes for Worker 1`).

Line numbers in this artifact are pin-at-write-time navigational hints (per-cycle
scratchpad; raw `path:NN` is permitted here and nowhere else).

### Test additions / updates

None — this pass writes no test. Focused read-only run performed as evidence:

- `uv run pytest tests/auth examples/fakeshop/test_query/test_auth_api.py --no-cov -q`
  → **210 passed** in 15.53s (8 workers). No `--cov*` flag.

### Implementation discretion items

None. Every verdict below is decided.

### Spec slice checklist (verbatim)

The spec's `## Slice checklist` **Slice 2** and **Slice 3** blocks, copied verbatim. A
box is ticked only where the contract it states is proved landed by the cited
symbol-qualified path. **Slice 3's boxes name files this cycle may not edit**; they
are audited read-only at `3a294082 Release 0.0.13`, the commit where each obligation
was due, and the finding is reported rather than fixed.

- [x] **Slice 2 — `register_mutation` + `current_user`, earned live**
  - [x] `auth/mutations.py` grows `register_mutation()` — synthesizing (and caching)
        a [`DjangoMutation`][glossary-djangomutation] subclass whose `__name__` is
        pinned to `Register` (so the unchanged machinery emits `RegisterPayload` —
        no payload-name seam) over `get_user_model()`,
        `operation = "create"`, `Meta.fields` narrowed to
        `(USERNAME_FIELD, *REQUIRED_FIELDS, "password")` via the directly-testable
        `derive_register_fields(user_model)` helper (`email` optional per
        `input_field_required`), **overriding `resolve_sync` / `resolve_async`** to
        ride `run_write_pipeline_sync` with the password-aware step pair (the
        `decode_step` captures `password` through the provided-marker-preserving
        exclusion seam and returns
        `(user, m2m_assignments, exclude, raw_password)`; the write step runs
        `django.contrib.auth.password_validation.validate_password(raw_password, user)`
        — failures → `password`-keyed [`FieldError`][glossary-fielderror-envelope]s
        — then `set_password(raw_password)` **before** `full_clean()` / `save()`; the
        `036` pipeline has no per-instance write hook to reuse), with **every**
        same-`permission_classes` factory call re-registering the cached rider into the mutation
        ledger (identity-deduped; reload-safe) and a conflicting-`permission_classes`
        second call raising [`ConfigurationError`][glossary-configurationerror]
        ([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)).

        *Proof, clause by clause:* `auth/mutations.py::_synthesize_register_rider`
        defines `class Register(DjangoMutation)` with
        `#"model = user_model"` / `#"operation = "create""` /
        `#"fields = register_fields"`; `::register_mutation` routes through
        `::_declare_auth_surface #"_synthesize_register_rider"`, which returns the
        ledger-cached class on a same-args repeat;
        `::derive_register_fields #"names = [user_model.USERNAME_FIELD, *user_model.REQUIRED_FIELDS, "password"]"`
        + `#"deduped = tuple(dict.fromkeys(names))"`;
        `mutations/inputs.py::input_field_required #"return not field.blank"` gives
        `email` its optionality (pinned live by
        `test_auth_api.py::test_generated_auth_type_shapes`);
        `Register.resolve_sync` / `Register.resolve_async` both exist and both route
        to `::_run_register_pipeline_sync`, which calls
        `mutations/resolvers.py::run_write_pipeline_sync` with
        `decode_step=` / `write_step=`;
        `::_register_decode_step` returns
        `#"return user, m2m_assignments, exclude, excluded_values.get("password")"`;
        `::_register_write_step` runs `#"validate_password(raw_password, user)"`,
        maps failure through `#"resolvers.field_error("password", exc.messages, codes=codes)"`,
        then `#"user.set_password(raw_password)"` before delegating to
        `resolvers._model_write_step`;
        `::register_mutation #"record_mutation_declaration(rider_cls)"` +
        `#"register_auth_mutation(rider_cls)"` are the every-call re-records;
        `::_reject_conflicting_permission_classes` raises the conflict.
        Rows: `tests/auth/test_mutations.py::test_register_factory_recache_and_reregister_on_every_call`
        (cache identity, both ledger counts, and the conflicting-`permission_classes`
        raise in one row), `::test_sync_register_never_persists_the_plaintext_and_hashes_before_full_clean`,
        `::test_async_register_never_persists_the_plaintext`,
        `::test_exclusion_seam_captures_password_and_preserves_the_provided_marker`,
        `::test_register_input_name_is_pinned_and_payload_derives_from_the_rider_name`.
  - [x] `auth/queries.py` — the `current_user()` field factory: nullable
        session-actor return typed via a bind-materialized lazy alias, **no**
        [`get_queryset`][glossary-get_queryset-visibility-hook] re-run
        ([Decision 7](#decision-7--current_user-returns-the-session-actor-nullable-and-does-not-re-run-get_queryset)).

        *Proof:* `auth/queries.py::current_user` returns
        `_make_auth_field(..., return_annotation=_lazy_ref(CURRENT_USER_ALIAS_NAME, AUTH_QUERIES_MODULE_PATH) | None)`;
        the alias is materialized at bind by
        `auth/mutations.py::bind_auth_mutations #"materialize_current_user_alias(CURRENT_USER_ALIAS_NAME, primary)"`
        onto the `queries.py` `make_input_namespace` trio; the resolver body
        `queries.py::_current_user_resolve_body` issues no queryset call of any kind.
        Rows: `tests/auth/test_queries.py::test_injected_return_annotation_resolves_to_the_concrete_user_type`,
        `::test_allow_any_default_returns_null_for_anonymous_and_the_user_when_authenticated`,
        `::test_me_composes_with_login_in_one_schema_without_visibility_rerun`.
  - [x] **In the same commit:** the fakeshop live surface grows `register` + `me`
        fields and [`test_auth_api.py`][test-query-readme] covers the full
        register → login → `me` → logout round trip, the duplicate-username
        envelope, the weak-password envelope (fakeshop's
        `AUTH_PASSWORD_VALIDATORS`), and the anonymous `me → null` case.

        *Proof:* `examples/fakeshop/apps/accounts/schema.py::Query #"me = current_user()"`
        and `::Mutation #"register = register_mutation()"`. One live row per named
        case: `test_auth_api.py::test_register_login_me_logout_round_trip_and_hashed_storage`,
        `::test_duplicate_username_register_envelope_keys_to_username`,
        `::test_weak_password_register_envelope_keys_to_password_not_all`,
        `::test_anonymous_me_is_null_not_an_error`.
  - [x] Mirrored package tests under `tests/auth/` for the internals (the
        password-hash write step with the **plaintext-never-persisted assertion on
        both the sync and async paths**, the validator → envelope mapping shapes
        (a `password`-keyed leaf, **not** the `"__all__"` sentinel the generic
        `validation_error_to_field_errors` mapper produces for a list-style error),
        the exclusion-seam provided-marker test, the factory cache identity, the
        **reload-idempotence cycle** (finalize → `registry.clear()` → re-declare →
        finalize, `register` present in the second schema; a prior
        conflicting-`permission_classes` raise does not survive the clear), the
        register-arm / current-user-arm no-`UserType` error messages (pinned
        distinct from login's — the coverage moved here from Slice 1, where these
        factories do not yet exist) plus the register-only / current-user-only
        surface-keyed binds, and `derive_register_fields` for the default AND a
        custom-`USERNAME_FIELD` / custom-`REQUIRED_FIELDS` test-scoped model).

        *Proof, one row per named item:*
        `tests/auth/test_mutations.py::test_sync_register_never_persists_the_plaintext_and_hashes_before_full_clean`
        + `::test_async_register_never_persists_the_plaintext` (both paths);
        `test_auth_api.py::test_weak_password_register_envelope_keys_to_password_not_all`
        (the `password`-keyed leaf, asserted `== ["password"]`, so the `"__all__"`
        sentinel would fail it);
        `::test_exclusion_seam_captures_password_and_preserves_the_provided_marker`
        (+ its negative twin `::test_model_decode_step_without_exclusion_keeps_the_historical_three_tuple`);
        `::test_register_factory_recache_and_reregister_on_every_call` (cache
        identity); `::test_reload_idempotence_cycle_rebuilds_the_full_auth_surface`
        (`register(data: RegisterInput!): RegisterPayload!` asserted present in the
        SECOND schema's SDL) + `::test_register_arm_error_survives_a_reload_cycle` +
        `::test_registry_clear_drains_ledger_and_resets_conflict_state` (the conflict
        state does not survive the clear);
        `::test_register_only_schema_without_user_type_raises_the_register_arm_error`
        (which also asserts the generic `_resolve_primary_type` wording is ABSENT) +
        `tests/auth/test_queries.py::test_current_user_only_schema_without_user_type_raises_its_own_arm`;
        `::test_register_only_surface_keyed_bind_emits_no_login_logout_payloads` +
        `tests/auth/test_queries.py::test_current_user_only_bind_emits_no_login_logout_payloads`;
        `::test_derive_register_fields_default_user_model` +
        `::test_derive_register_fields_custom_username_and_required_fields`.
- [x] **Slice 3 — docs + the `0.0.13` version cut + card wrap**
  - [x] The version quintet moves `0.0.12` → `0.0.13`: [`pyproject.toml`][pyproject],
        `__version__` in [`__init__.py`][init],
        [`tests/base/test_init.py::test_version`][test-base-init], the
        [`docs/GLOSSARY.md`][glossary] package-version line, and the
        `django-strawberry-framework` `version` entry inside `uv.lock`
        ([Decision 12](#decision-12--this-card-owns-the-0013-version-bump-and-completes-the-joint-cut)).

        *Proof, read-only at `3a294082 Release 0.0.13`, all five:*
        `git show 3a294082:pyproject.toml` → `version = "0.0.13"`;
        `…:django_strawberry_framework/__init__.py` → `__version__ = "0.0.13"`;
        `…:tests/base/test_init.py` → `assert __version__ == "0.0.13"`;
        `…:docs/GLOSSARY.md` → `Current package version: \`0.0.13\``;
        `…:uv.lock` → the `django-strawberry-framework` entry's `version = "0.0.13"`.
  - [x] The `039`-deferred joint-cut release flips land: the GLOSSARY
        [`SerializerMutation`][glossary-serializermutation] status →
        `shipped (0.0.13)`; [`docs/README.md`][docs-readme] / [`README.md`][readme]
        move the serializer flavor **and** the auth surface from "Coming next
        (`0.0.13`)" to "Shipped today" (README **Status** → `0.0.13`);
        [`CHANGELOG.md`][changelog] carries the `0.0.13` release bullets for both
        cards — **only when the maintainer prompt explicitly requests the
        `CHANGELOG.md` edit**.

        *Proof, read-only at `3a294082`:* GLOSSARY index row
        `| [\`SerializerMutation\`](#serializermutation) | shipped (\`0.0.13\`) |`;
        `docs/README.md` `**Shipped today** (\`0.0.13\`):` with the next block reading
        `**Coming next — remaining alpha (\`0.0.14\`):**`; `README.md` `## Status` →
        `**\`0.0.13\`, single-maintainer, alpha-quality.**` naming both the serializer
        flavor and the opt-in session-auth mutations as the newest shipped surface;
        `CHANGELOG.md` `## [0.0.13] - 2026-07-06` carrying **two** `### Added` bullets
        (serializer mutations; session-auth mutations) plus the
        `### Changed` version bullet. The conditional permission was evidently
        granted — the entry exists.
  - [x] [Auth mutations][glossary-auth-mutations] GLOSSARY entry flips to
        `shipped (0.0.13)` with the implemented contract (the four factories, the
        submodule-only import path, the AllowAny default and its rationale, the
        envelope semantics); the Index row updates; a submodule-exports note is
        added beside the `testing` note (auth symbols are **not** root exports,
        [Decision 3](#decision-3--consumer-surface-four-field-factories-at-the-auth-submodule-path-opt-in-by-import-no-root-re-export)).

        *Proof, read-only:* at `3a294082` the index row reads
        `| [Auth mutations](#auth-mutations) | shipped (\`0.0.13\`) |` and the
        submodule-exports note sits directly below the `testing.relay` note. Both
        survive at `HEAD` (`docs/GLOSSARY.md:97` index row; `:81` the note, one line
        below `:78`'s `testing` note; the `## Auth mutations` body carries all four
        factories, the submodule-only path, the AllowAny inversion and its reason,
        and the envelope semantics). **One staleness found — reported, not fixed:**
        see finding **F1** below.
  - [x] [`docs/TREE.md`][tree] gains the `auth/` package rows, the `tests/auth/`
        tree, the fakeshop `accounts` app, and the live `test_auth_api.py` row
        (closing the target-layout gap recorded in
        [Risks and open questions][rationale-risks]); [`TODAY.md`][today] notes the shipped
        auth surface under its capabilities-not-exercised-by-products section (the
        `accounts` app owns the live demonstration); [`GOAL.md`][goal]'s fakeshop
        paragraph flips "auth mutations exercised by the existing test users" from
        future to shipped.

        *Proof, read-only at `3a294082`, one per named file:* `docs/TREE.md` carries
        `├── auth/    # Opt-in session-auth field factories (spec-040).`, the
        `tests/auth/` subtree with both module rows,
        `├── accounts/    # Schema-only fakeshop accounts app exercising the session-auth surface (spec-040).`,
        and `├── test_auth_api.py              # Live \`/graphql/\` auth API acceptance tests (spec-040).`;
        `TODAY.md` carries `- **Session-auth mutations** (shipped \`0.0.13\`) …` naming
        the `accounts` app as the live demonstration and products as declaring no auth
        surface; `GOAL.md`'s fakeshop paragraph reads
        `\`ModelSerializer\`-driven mutations (\`0.0.13\`) and session-auth mutations exercised by the existing test users (the \`accounts\` app, \`0.0.13\`) now ship.`
  - [x] [`KANBAN.md`][kanban] card wrap: `WIP-ALPHA-040-0.0.13` → Done with the next
        `DONE-040-0.0.13` id and its `SpecDoc` pointing at this spec (kanban DB edit
        + `scripts/build_kanban_md.py` / `build_kanban_html.py` re-render, never a
        hand-edit).

        *Proof, read-only at `3a294082`:* the Done index row
        `| \`DONE-040-0.0.13\` - Auth mutations (login / logout / register) | [spec-040-auth_mutations-0_0_13.md](docs/spec-040-auth_mutations-0_0_13.md) |`
        and the card body `### [DONE-040-0.0.13 - Auth mutations (login / logout / register)](KANBAN.html#auth_mutations_login_logout_register)`.
        No `WIP-ALPHA-040` id survives. The `SpecDoc` target is the pre-archival
        `docs/` path, correct at the cut (`AGENTS.md` rule 26 archives specs at the
        NEXT spec's Step 8, not at the completing card's merge).

**Tick count: 12 of 12.** Slice-2 block: **5 of 5** (the parent box plus its four
sub-bullets). Slice-3 block (audited read-only, out of scope for edits): **6 of 6**
(the parent box plus its five sub-bullets). No box is left `- [ ]`; no deferral reason
is owed. **The `0.0.13` build dropped nothing it planned, on either half.**

One note the ticks do not carry, because the box as written is satisfied: the
`## Slice checklist` blockquote preceding these blocks still points at retired
`bld-slice-*.md` / `bld-integration.md` / `bld-final.md` artifacts. **Slice 4 owns
it** (routed by Slice 1, restated by Slice 2); not re-raised here.

### Conformance matrix

One row per normative claim. Verdicts: `CONFORMS` / `SPEC-STALE` (code right, spec
moves) / `CODE-GAP` (spec right, code moves) / `UNPROVABLE`.

#### Decision 6 — `register_mutation()` rides `DjangoMutation`

Graded step by step, in the order the Decision states the pipeline.

| # | Claim (spec, quoted short) | Settling citation | Verdict |
|---|---|---|---|
| D6.1 | "synthesizes (once, cached) a concrete package-declared subclass of `DjangoMutation`" | `auth/mutations.py::_synthesize_register_rider` → `class Register(DjangoMutation)`; cached through `::_declare_auth_surface` reading the ledger | `CONFORMS` |
| D6.2 | "whose **`__name__` is pinned to `Register`**" | the class statement is literally `class Register`; asserted by `tests/auth/test_mutations.py::test_register_factory_recache_and_reregister_on_every_call #"rider.__name__ == "Register""` | `CONFORMS` |
| D6.3 | "`Meta.model = get_user_model()`" | `::_synthesize_register_rider #"user_model = get_user_model()"` → `Meta.model = user_model` | `CONFORMS` |
| D6.4 | "`Meta.operation = "create"`" | `::_synthesize_register_rider #"operation = "create""` | `CONFORMS` |
| D6.5 | "`Meta.fields` narrowed to `(USERNAME_FIELD, *REQUIRED_FIELDS, "password")` … **a directly-testable helper, `derive_register_fields(user_model) -> tuple[str, ...]`**: it takes the model as an argument — never reading `get_user_model()` inline" | `::derive_register_fields(user_model)`; the only `get_user_model()` call is in the *caller*, `::_synthesize_register_rider`. Pinned on a test-scoped model by `::test_derive_register_fields_custom_username_and_required_fields` | `CONFORMS` |
| D6.6 | "the rule is exact: `USERNAME_FIELD` first, then each distinct `REQUIRED_FIELDS` entry in declaration order, then `password` exactly once, deduplicated" | `::derive_register_fields #"names = [user_model.USERNAME_FIELD, *user_model.REQUIRED_FIELDS, "password"]"` + `#"deduped = tuple(dict.fromkeys(names))"` (insertion-ordered dedupe). The custom-model row asserts `("email", "nickname", "password")` from a `REQUIRED_FIELDS` that repeats BOTH the username field and `password` | `CONFORMS` |
| D6.7 | "Unknown / non-editable / reverse names are rejected … by **delegating to the standard `editable_input_fields` validation** …, never re-implemented" | `::derive_register_fields #"editable_input_fields(user_model, fields=deduped)"` — a delegation, no local name check. `::test_derive_register_fields_rejects_unknown_names_via_editable_input_fields` | `CONFORMS` |
| D6.8 | "`email` optional per `input_field_required`" (`## User-facing API`, `#"return not field.blank"`) | `mutations/inputs.py::input_field_required #"return not field.blank"` — the cited substring still resolves. Live: `test_auth_api.py::test_generated_auth_type_shapes` asserts `email` is a bare `String` while `username` / `password` are `NON_NULL` | `CONFORMS` |
| D6.9 | "The generated input therefore **cannot** carry `is_staff` / `is_superuser` / `is_active` / `groups` / `user_permissions` — privilege escalation is structurally unreachable, **not policy-checked**" | `::derive_register_fields` now runs `#"protected = sorted(_REGISTER_PROTECTED_FIELDS.intersection(deduped))"` and raises `ConfigurationError` on a hit — an explicit policy check, added because the model is an *argument*: a custom model listing `is_staff` in `REQUIRED_FIELDS` made the column reachable. `::_REGISTER_PROTECTED_FIELDS` holds exactly the five names. `::test_derive_register_fields_rejects_privilege_fields`. Added by `a40f0d33 Harden auth registration and deployment guidance` | **`SPEC-STALE`** |
| D6.10 | "register wires **none** of the relation-visibility helpers (`relation_kind` / `is_forward_many_to_many` / `visible_related_object(s)`)" | `rg "relation_kind\|is_forward_many_to_many\|visible_related_object" django_strawberry_framework/auth/` → **0** hits across all four `auth/` modules | `CONFORMS` |
| D6.11 | "`Meta.permission_classes` defaulted to the explicit AllowAny …, overridable through the factory's `permission_classes=` kwarg" | `::_declare_auth_surface #"_validate_permission_classes(label, permission_classes, unset_default=())"`, whose result is what `::_synthesize_register_rider(permission_classes)` writes onto `Meta` | `CONFORMS` |
| D6.12 | "the class's fixed `RegisterInput` / `RegisterPayload` names cannot serve two distinct permission-specialized classes (`build_payload_type` mints a fresh payload per class, and `materialize_generated_input_class` raises on a second distinct class under an existing name)" | `mutations/inputs.py::build_payload_type` builds a new type per call; `utils/inputs.py::materialize_generated_input_class #"if existing is not None:"` raises `ConfigurationError` for a different class under one name | `CONFORMS` |
| D6.13 | "a same-`permission_classes` `register_mutation()` call returns the identity-deduped cached class, but a second call with a **different** `permission_classes` raises a `ConfigurationError` naming the conflict" | `::_declare_auth_surface` returns `declared_cls` on the cached path; `::_reject_conflicting_permission_classes` raises naming both class-name lists and the factory. `::test_register_factory_recache_and_reregister_on_every_call` asserts the same object back, `count == 1` on **both** ledgers, and the raise | `CONFORMS` |
| D6.14 | "the shared signature helper partitions the factory kwargs into three classes — resolver GraphQL args \| declaration args \| Strawberry field kwargs — and only the declaration args enter the key" | The **key** half holds (`::_reject_conflicting_permission_classes` compares only normalized `permission_classes`). The **mechanism** half does not: `mutations/fields.py::build_lazy_field_signature(arguments, return_ref)` receives only the GraphQL-argument class and partitions nothing. The partition is each factory's own keyword-only signature routing one class to each consumer. Identical at `3a294082` — inaccurate on its own date, not drift | **`SPEC-STALE`** |
| D6.15 | "`login_mutation(description="A")` after `login_mutation(description="B")` is the cached-idempotent path with the new field metadata, never a false-`ConfigurationError`" | presentation kwargs never reach `::_declare_auth_surface`; `tests/auth/test_mutations.py::test_presentation_kwargs_never_enter_the_conflict_key` | `CONFORMS` |
| D6.16 | "the key's state is the surface-keyed declaration ledger itself, drained by its full-clear-only row … after a `registry.clear()` a re-declaration with a *different* `permission_classes` mints a fresh holder / rider rather than tripping a stale conflict raise" | `::_declared_auth_surface` iterates `iter_auth_mutations()`, never a separate dict; `::test_registry_clear_drains_ledger_and_resets_conflict_state` | `CONFORMS` |
| D6.17 | "`DjangoMutation` exposes **no per-instance write hook** — `_run_pipeline_sync` hard-wires the model `decode_step` / `write_step` as module-level lambdas" | `mutations/resolvers.py::_run_pipeline_sync` passes `decode_step=lambda instance: _model_decode_step(...)` and `write_step=lambda instance, decoded: _model_write_step(...)`; no hook parameter exists on `DjangoMutation` | `CONFORMS` |
| D6.18 | "the synthesized `Register` class overrides **both `resolve_sync` and `resolve_async`**" | `::_synthesize_register_rider` → `Register.resolve_sync` and `Register.resolve_async`, both `@classmethod`, the second a real `async def` | `CONFORMS` |
| D6.19 | "rides the shared `run_write_pipeline_sync` skeleton with its own step pair" — rides, does not fork | `::_run_register_pipeline_sync #"return run_write_pipeline_sync("` — the shared function, called with `decode_step=` / `write_step=`. No forked orchestration exists anywhere under `auth/`: `rg "transaction.atomic\|open_write_pipeline\|refetch_optimized" django_strawberry_framework/auth/` → 0 hits | `CONFORMS` |
| D6.20 | "the `decode_step` pops `password` out of the model attrs and returns the extended tuple `(user, m2m_assignments, exclude, raw_password)` … the raw password travels as explicit decoded state, never an implicit closure" | `::_register_decode_step #"return user, m2m_assignments, exclude, excluded_values.get("password")"`; `run_write_pipeline_sync` passes only the decode return into `write_step` | `CONFORMS` |
| D6.21 | "the provided-field iteration goes through [`iter_provided_input_fields`] (the same walk `_decode_relations` opens with)" | The ONE-walk invariant holds, but `_decode_relations` now opens with `utils/write_values.py::decode_provided_fields`, which is what calls `iter_provided_input_fields`. At `3a294082` `_decode_relations` called it directly. Moved by `31625ac7 refactor(mutations): ride the shared decode spine in the model write flavor` | **`SPEC-STALE`** |
| D6.22 | "a small reusable **exclusion seam**: an `excluded_input_fields` parameter threaded through the existing `_model_decode_step` into `_decode_relations`, **not** a fork of the decoder" | That parameter is **gone**. It existed and was passed at `3a294082` (`git show 3a294082:django_strawberry_framework/auth/mutations.py` #"excluded_input_fields=_REGISTER_EXCLUDED_INPUT_FIELDS"); `31625ac7` replaced it with a bind-time kind — `Register.build_input #"excluded_attrs=_REGISTER_EXCLUDED_INPUT_FIELDS"` stashes `password` as `mutations/inputs.py::EXCLUDED`, and `resolvers.py::_decode_relations #"EXCLUDED: decoded_into(excluded_values, _model_excluded_decode)"` routes it. **The "not a fork" half is intact** | **`SPEC-STALE`** |
| D6.23 | "The seam **must preserve the provided-marker** … the register seam is 'extract the protected input value *with its provided-marker preserved*' … and a focused helper-level test pins exactly that (value captured, marker preserved, attr absent from `model(**scalar_and_fk_attrs)`)" | `resolvers.py::_model_decode_step #"provided \|= {model_fields[attr].name for attr in excluded_values}"` folds the captured names back in before `_unprovided_exclude`. `::test_exclusion_seam_captures_password_and_preserves_the_provided_marker` asserts all three clauses in one row (`excluded_values == {"password": "raw-secret"}`, `target.password == ""`, `"password" not in exclude` while `"email" in exclude`) | `CONFORMS` |
| D6.24 | "`validate_password(raw_password, user)`" receives the **constructed** user | `::_register_write_step #"validate_password(raw_password, user)"` where `user` is the decode's constructed instance. Live proof that the argument is load-bearing: `test_auth_api.py::test_password_similar_to_username_is_rejected_with_user_context` (a user-less call cannot produce that rejection) | `CONFORMS` |
| D6.25 | on failure, "maps the raised error to a `password`-keyed `FieldError` **directly, not through the generic `validation_error_to_field_errors` mapper**" via `field_error("password", exc.messages, codes=[leaf.code for leaf in exc.error_list if leaf.code])` | `::_register_write_step #"return [resolvers.field_error("password", exc.messages, codes=codes)]"` with `#"codes = [leaf.code for leaf in exc.error_list if leaf.code]"` — byte-identical to the spec's expression. `test_auth_api.py::test_weak_password_register_envelope_keys_to_password_not_all` asserts the field list is exactly `["password"]`, so the `"__all__"` sentinel fails the row | `CONFORMS` |
| D6.26 | "It then runs `user.set_password(raw_password)` **before** `full_clean()` / `save()`" | `::_register_write_step` — `#"user.set_password(raw_password)"` precedes the `resolvers._model_write_step` call that owns `full_clean` → `save`. Ordering pinned behaviourally by `::test_sync_register_never_persists_the_plaintext_and_hashes_before_full_clean` (a 147-char password would fail the 128-char column check if the raw value were validated) | `CONFORMS` |
| D6.27 | "**`validate_password` + `set_password` are the ONLY auth-specific steps**" | Three further auth-specific guards now precede them in `::_register_write_step`: `#"return [null_field_error("password")]"`, the non-`str` `#"field_error("password", "Invalid password.", codes=FIELD_ERROR_CODE_INVALID)"`, and `#"unencodable_text_error("password", raw_password)"`. They exist *because* of D6.22's seam — `password` bypasses the shared decode's `decode_scalar_leaf`. Added by `a6f5a6cb fix(auth): reject unencodable credentials` and `a8f31a2d fix: harden framework boundaries and validation`. The Decision's actual point — no auth-specific error *handling* — survives: all three return the standard leaves | **`SPEC-STALE`** |
| D6.28 | "the `full_clean()` + `save()` + `IntegrityError` mapping are delegated to the shared write path (`_full_clean_or_field_errors` / `save_or_field_errors`), so the duplicate-`USERNAME_FIELD` unique error and the concurrent-race `IntegrityError` come back through the standing envelope with no auth-specific error handling" | `::_register_write_step #"return resolvers._model_write_step(instance, (user, m2m_assignments, exclude))"`, which runs `_full_clean_or_field_errors` then `save_or_field_errors`. Live: `test_auth_api.py::test_duplicate_username_register_envelope_keys_to_username` | `CONFORMS` |
| D6.29 | "The plaintext exists only in memory and never reaches a model column (a unit assertion pins that the model decode never receives `password` in `scalar_and_fk_attrs`)" | `::test_exclusion_seam_captures_password_and_preserves_the_provided_marker #"assert target.password == """` — the constructed instance carries the column default, not the raw value | `CONFORMS` |
| D6.30 | "the **plaintext-never-persisted test is required on both the sync and the async path** — the async twin is a separate override and can regress independently" | Two rows, one per override: `::test_sync_register_never_persists_the_plaintext_and_hashes_before_full_clean` and `::test_async_register_never_persists_the_plaintext`, each asserting `password not in stored.password` **and** `stored.check_password(...)` | `CONFORMS` |
| D6.31 | "The **input** name is pinned to `RegisterInput` via the `input_type_name` / `build_input` name seams" | `Register.input_type_name` returns `::_REGISTER_INPUT_NAME`; `Register.build_input #"pinned = shape._replace(type_name=_REGISTER_INPUT_NAME)"`. Live SDL: `test_auth_api.py::test_generated_auth_type_shapes` introspects `RegisterInput` | `CONFORMS` |
| D6.32 | "The **payload** name has **no seam**: `_bind_mutation` calls `build_payload_type(mutation_cls.__name__, …)` and `DjangoMutationField`'s synthesized signature builds `f"{mutation_cls.__name__}Payload"`" | The second half holds: `mutations/fields.py #"_lazy_ref(f"{mutation_cls.__name__}Payload", INPUTS_MODULE_PATH)"`. The first does not: `_bind_mutation` no longer exists (present at `3a294082`; split by `ab821ae0 refactor: single-site the duplicated class-label, bind, and fetch seams` into `mutations/sets.py::bind_write_declarations` + `::bind_mutation_outputs`, the latter carrying `#"build_payload_type("` / `#"mutation_cls.__name__,"`) | **`SPEC-STALE`** |
| D6.33 | "with `__name__ = "Register"` the unchanged machinery emits `RegisterPayload` for free — no payload-name seam is added" | `::test_register_input_name_is_pinned_and_payload_derives_from_the_rider_name`; live SDL row asserts `register(data: RegisterInput!): RegisterPayload!` | `CONFORMS` |
| D6.34 | "The `DjangoRegisterMutation` name is reserved … it is not the concrete registered class" | `rg "DjangoRegisterMutation" django_strawberry_framework/ tests/ examples/` → exactly **1** hit, a docstring line in `::_synthesize_register_rider`. No such class exists | `CONFORMS` |
| D6.35 | "the register rider reuses … the `run_write_pipeline_sync` **skeleton** — the `transaction.atomic()` boundary, the authorize-before-decode security ordering, the envelope short-circuits with rollback, and the closing `refetch_optimized` → `build_payload` steps" | `mutations/resolvers.py::run_write_pipeline_sync` owns all four and the register call supplies only the two step kwargs. Live proof the short-circuit is the shared one: `test_auth_api.py::test_register_decode_failure_returns_the_field_keyed_envelope` (a surrogate `username` short-circuits at the shared decode, keyed to `username`, before any password work) | `CONFORMS` |
| D6.36 | "registration + phase-2.5 bind via `bind_mutations()` (the class IS a `DjangoMutation`)" and "exposure via `DjangoMutationField` (the factory returns `DjangoMutationField(Register)` internally)" | `::register_mutation #"return DjangoMutationField("`; `::bind_auth_mutations`'s closing comment states the register arm does no auth-side emit work, and `mutations/sets.py::bind_mutations` binds it like any other declaration | `CONFORMS` |
| D6.37 | "the post-save `refetch_optimized` by pk without visibility (the `036` own-write exception … the brand-new anonymous-created user is exactly the row a staff-only `UserType.get_queryset` would hide)" | the skeleton's success tail; `auth/` adds no re-fetch of its own (`rg "refetch_optimized" django_strawberry_framework/auth/` → 0). Live: the register round-trip row returns `node { username }` on a schema whose `UserType` has no `get_queryset` override, and the contrast is stated in `## User-facing API` | `CONFORMS` |
| D6.38 | "The synthesized class is created **lazily on first factory call** (not at module import)" | `::_synthesize_register_rider` is a function reached only from `::_declare_auth_surface`'s miss branch; no module-level `Register` exists. Corroborated by `::test_registry_clear_does_not_import_the_auth_subsystem` (Slice 2's D3.3) | `CONFORMS` |
| D6.39 | "**Every factory call — cached or not — re-records into BOTH declaration ledgers**", both identity-deduped | `::register_mutation` calls `record_mutation_declaration(rider_cls)` and `register_auth_mutation(rider_cls)` unconditionally, after `_declare_auth_surface` returns; dedupe at `mutations/sets.py::make_declaration_registry #"if declaration_cls not in store"`. `::test_register_factory_recache_and_reregister_on_every_call` asserts `count == 1` on both after two calls | `CONFORMS` |
| D6.40 | "A reload-idempotence test pins the cycle …, asserting **both** that `register` is present in the second schema AND — for a no-`UserType` schema — that the second finalize still fires the register-arm auth-specific error" | Both halves, one row each: `::test_reload_idempotence_cycle_rebuilds_the_full_auth_surface` (asserts the SDL substring `register(data: RegisterInput!): RegisterPayload!` after `registry.clear()` + re-declare) and `::test_register_arm_error_survives_a_reload_cycle` | `CONFORMS` |
| D6.41 | "Calls after `finalize_django_types` raise the standing declare-after-finalize `ConfigurationError`" | both `register_auth_mutation` and `record_mutation_declaration` are `make_declaration_registry` registers carrying the post-finalize reject; `::test_factory_after_finalize_raises_the_standing_configuration_error` | `CONFORMS` |

**What the spec should say instead:**

- **D6.9** — account-control state is kept off the public registration surface by
  **two** layers, because the derivation reads the model: for the stock user model the
  narrowed set never names the five columns (structural), and because a **custom**
  model may place one of them in `USERNAME_FIELD` / `REQUIRED_FIELDS`,
  `derive_register_fields` rejects the derived tuple with a `ConfigurationError`
  naming the offending field(s) and the model, directing the consumer to server-owned
  registration logic. The protected set is one module-level frozenset, so the five
  names are stated once. Written at `spec-040:1104-1117`.
- **D6.14** — each factory's own keyword-only signature is what partitions its kwargs
  into the three classes, and each class reaches exactly one consumer: GraphQL args to
  the shared signature builder, declaration args to the ONE declaration path, field
  kwargs straight to `strawberry.field`. Only the declaration args enter the key
  **because only the declaration path sees them**. Written at `spec-040:1145-1151`.
- **D6.21 / D6.22** (one edit) — the provided-field iteration goes through the ONE
  shared decode spine every write flavor rides (`decode_provided_fields` over
  `iter_provided_input_fields`), and the seam is a **field kind declared at bind and
  honoured by the shared walk**, not a per-request parameter: `build_input` stashes
  `password` as kind `EXCLUDED` through `mutation_input_field_specs(…,
  excluded_attrs=…)`, and `_decode_relations` routes every `EXCLUDED` spec to its own
  dest beside the scalar / FK / M2M dests. `_model_decode_step` returns the extended
  four-tuple only for specs carrying that kind and the historical three-tuple
  otherwise, and `_model_write_step` unpacks the three-tuple **strictly**, so an
  `EXCLUDED` spec introduced without a paired flavor write step raises instead of
  silently discarding the value. Written at `spec-040:1182-1199`.
- **D6.27** (two edits) — the write step **preflights the captured value before
  touching it**, because riding the exclusion seam is exactly what routes `password`
  around the shared decode's own scalar checks that every other input scalar still
  runs through. Three guards, each returning the `password`-keyed envelope: absent →
  the standard null-field leaf; non-`str` → an `invalid`-coded leaf; non-UTF-8-encodable
  → the SAME shared `unencodable_text_error` primitive the model decode uses. The
  "ONLY auth-specific steps" sentence becomes "the password preflight,
  `validate_password` and `set_password`", with the preflight's own reuse stated so it
  cannot read as a licence to spell new checks. Written at `spec-040:1211-1223` and
  `:1237-1240`, plus the matching `### Error shapes` row at `:775`.
- **D6.32** — the payload name is minted by the phase-2.5 bind's payload half,
  `mutations/sets.py::bind_mutation_outputs`, which both write-declaration ledgers
  ride. The no-seam contract is unchanged. Written at `spec-040:1256-1259`.

#### Decision 7 — `current_user()` returns the session actor, nullable

| # | Claim | Settling citation | Verdict |
|---|---|---|---|
| D7.1 | "`current_user()` returns a query **field** (not a mutation)" | `queries.py::current_user` returns `_make_auth_field(...)` → a `strawberry.field`, assigned as `Query.me` in `examples/fakeshop/apps/accounts/schema.py::Query` | `CONFORMS` |
| D7.2 | "whose resolver reads the request user via the same `request_from_info` extraction" | `queries.py::_current_user_resolve_body #"request_from_info(info, family_label=_AUTH_FAMILY_LABEL)"` — the same one module-level label constant `login` / `logout` use | `CONFORMS` |
| D7.3 | "the user object, typed as the user model's primary `DjangoType`, when `user.is_authenticated`" | `::_current_user_resolve_body #"return actor"`; the type comes from the bind-materialized alias pinned to `primary`. `tests/auth/test_queries.py::test_allow_any_default_returns_null_for_anonymous_and_the_user_when_authenticated` | `CONFORMS` |
| D7.4 | "`null` otherwise (anonymous / no session)" | The parenthetical under-describes "otherwise". `#"actor = _authenticated_actor_or_none(request)"` also answers `None` for a request with **no `user` attribute** (`3120dc5a fix(auth): handle absent request user gracefully in current user resolver`, single-sourced by `c537b2dc refactor(auth): single-source authenticated actor classification`) and for a **hostile** `user` descriptor / `is_authenticated` read / legacy callable / truthiness raising one of five exception types (`6873dac6`, extended by `a8f31a2d`), while any other exception propagates. Rows: `::test_me_is_null_not_a_crash_when_the_request_user_is_absent`, `::test_hostile_user_descriptor_raising_collapses_to_anonymous_null`, `::test_legacy_callable_is_authenticated_raising_collapses_to_anonymous_null` | **`SPEC-STALE`** |
| D7.5 | "permission-gated like the other three, but its enforcement site is the query resolver, not `run_write_pipeline_sync`" | the gate is a direct `authorize_or_raise` call in `::_current_user_resolve_body`; no pipeline is entered (`rg "run_write_pipeline_sync" django_strawberry_framework/auth/queries.py` → 0) | `CONFORMS` |
| D7.6 | "It accepts `permission_classes=` through the same module-internal permission holder" | `::current_user #"_declare_fixed_auth_surface("current_user", "CurrentUser", permission_classes)"` — the shared fixed-field path, holder minted by `mutations.py::_make_permission_holder` | `CONFORMS` |
| D7.7 | "its resolver runs `authorize_or_raise(holder_cls, info, "current_user", data=None, instance=<the request user, or None when anonymous>)` **first** — a denial is a top-level `GraphQLError`" | `::_current_user_resolve_body #"resolvers.authorize_or_raise(holder_cls, info, "current_user", None, instance=actor)"` (the `data` argument passed positionally); `mutations/resolvers.py::authorize_or_raise` raises `GraphQLError`. `::test_gated_me_denies_the_anonymous_caller_with_the_exact_pinned_string` | `CONFORMS` |
| D7.8 | "Only after the gate passes does the nullable-return rule apply … the two axes are distinct — `permission_classes` denial → `GraphQLError`; allowed-but-anonymous → `null`" | the `return actor` statement is unreachable when the gate raises; the two rows above pin one axis each | `CONFORMS` |
| D7.9 | "The AllowAny default … means the unset case gates nothing … a consumer who wants `me` to require authentication supplies a `permission_classes=[IsAuthenticated]`-style class, which denies the anonymous caller with the `GraphQLError` instead of `null`" | `unset_default=()` in the shared declaration path; the gated row denies with the exact pinned string, the ungated row returns `null` | `CONFORMS` |
| D7.10 | "The return annotation is `<UserPrimaryType> \| None` via a bind-materialized `strawberry.lazy` alias, attached through the **same signature-injection idiom the field family already uses**" | `::current_user #"return_annotation=_lazy_ref(CURRENT_USER_ALIAS_NAME, AUTH_QUERIES_MODULE_PATH) \| None"` → `mutations.py::_make_auth_field #"_resolve.__signature__ = signature"` / `#"_resolve.__annotations__ = annotations"`, both from `mutations/fields.py::build_lazy_field_signature`. `::test_injected_return_annotation_resolves_to_the_concrete_user_type` | `CONFORMS` |
| D7.11 | "That `Annotated[…, strawberry.lazy(…)]` return ref is built by the shared `_lazy_ref(type_name, module_path)` helper … not a hand-spelled `Annotated[...]`" | `queries.py` imports `_lazy_ref` from `..mutations.fields`; `rg "Annotated" django_strawberry_framework/auth/` → 0 hits | `CONFORMS` |
| D7.12 | "the whole resolve-request → gate → session-work → inject-signature dispatcher is **single-sited in ONE auth field-construction helper** the three factories share, not copied per field" | `::_make_auth_field` owns only the dispatch seam and the signature injection; request resolution, the gate and the session work live in the per-surface bodies it is handed. **Also true at `3a294082`**, where the parameter was `resolve_body=` and the body did all three — inaccurate on its own date; `c8346750 feat(auth): harden the session lifecycle across transports` widened the gap by splitting that body into `sync_body` / `async_body`. The single-siting claim itself holds for what the helper does own | **`SPEC-STALE`** |
| D7.13 | "`_lazy_ref` and the `_resolve.__signature__` / `__annotations__` injection assignment are promoted to shared machinery rather than re-spelled in `auth/`" | both imported from `mutations/fields.py`; `build_lazy_field_signature`'s own docstring names `DjangoMutationField` and the auth factories as its two callers | `CONFORMS` |
| D7.14 | "The `"CurrentUserAlias"` slot is owned by a `make_input_namespace("django_strawberry_framework.auth.queries", "AuthMutation")` trio, not a hand-rolled `setattr` / `delattr` pair" | `queries.py #"make_input_namespace(AUTH_QUERIES_MODULE_PATH, _AUTH_FAMILY_LABEL)"` with `AUTH_QUERIES_MODULE_PATH == "django_strawberry_framework.auth.queries"` and `_AUTH_FAMILY_LABEL == "AuthMutation"`; `rg "setattr\|delattr" django_strawberry_framework/auth/queries.py` → 0. `::test_alias_namespace_rides_make_input_namespace_and_the_pre_bind_row` | `CONFORMS` |
| D7.15 | "`bind_auth_mutations()` pins the alias by calling that trio's `materialize_fn("CurrentUserAlias", primary_type)` — which sets the module global through the blessed `materialize_generated_input_class` parked-global path — and the trio's `clear_fn` empties the ledger" | `mutations.py::bind_auth_mutations #"materialize_current_user_alias(CURRENT_USER_ALIAS_NAME, primary)"`; `utils/inputs.py::make_input_namespace` routes `materialize_fn` through `materialize_generated_input_class` and `clear_fn` through `ledger.clear()` | `CONFORMS` |
| D7.16 | "Because that `clear_fn` is the alias namespace's pre-bind `register_subsystem_clear` row, the ledger is empty before each re-materialize, so a *different* `UserType` class object on a reload's second finalize does not trip the distinct-class collision guard" | `queries.py #"before_bind=True,"` on the `register_subsystem_clear` call; the reload rows (`::test_reload_idempotence_cycle_rebuilds_the_full_auth_surface`, live `::test_complete_reload_preserves_the_auth_surface`) exercise a second finalize with a freshly declared `UserType` and no collision raise | `CONFORMS` |
| D7.17 | "Strawberry resolves the lazy ref to the concrete `UserType` at schema build and the SDL reads `me: UserType`" | `::test_injected_return_annotation_resolves_to_the_concrete_user_type`; live `test_auth_api.py::test_register_login_me_logout_round_trip_and_hashed_storage` selects `me { username }` against the fakeshop `UserType` | `CONFORMS` |
| D7.18 | "`login` / `logout` attach their `LoginPayload` / `LogoutPayload` return refs the same way, into the `mutations.inputs` namespace" | `mutations.py::login_mutation` / `::logout_mutation` use `_lazy_ref(..., INPUTS_MODULE_PATH)`; `::bind_auth_mutations` materializes both through `materialize_mutation_input_class` | `CONFORMS` |
| D7.19 | "The resolver performs **no queryset work**: no `get_queryset` re-run, no re-fetch — the returned object is `request.user`, already loaded by `AuthenticationMiddleware` (lazily; the resolver's `is_authenticated` access forces it, the upstream trick)" | `rg "get_queryset\|refetch\|objects\." django_strawberry_framework/auth/queries.py` → 0 hits; the only attribute touched is `is_authenticated`, inside `_authenticated_actor_or_none`, on the resolver's own stack. `::test_me_composes_with_login_in_one_schema_without_visibility_rerun`; `::test_async_gated_me_forces_the_lazy_user_inside_the_one_sync_boundary` pins the forcing site | `CONFORMS` |
| D7.20 | "Nested relation selections under `me { ... }` resolve through the type's generated resolvers as usual (an unplanned deep selection is visible to Strictness mode like any non-root object)" | Settled by construction: `me` returns a plain model instance typed as the consumer's `DjangoType`, and `auth/` wraps no field resolver (`rg "strawberry.field\|resolver=" django_strawberry_framework/auth/queries.py` reaches only the root dispatcher), so every nested field is served by `types/resolvers.py`, which is where `_strictness_for` reads the mode. **No test row exercises a deep `me { … }` selection under strictness** — routed to Slice 4 (hand-off 3) | `CONFORMS` |

**What the spec should say instead:**

- **D7.4** — the resolver classifies the request through the ONE shared anonymity
  definition `logout`'s `ok` also derives from (pointing at Decision 5, which Slice 2
  wrote, rather than restating it), and "otherwise" is spelled out: a request with no
  `user` attribute at all reads `null` rather than raising, and a hostile actor —
  descriptor, `is_authenticated` read, legacy callable, or truthiness raising
  `TypeError` / `ValueError` / `AttributeError` / `KeyError` / `IndexError` —
  collapses to `null` too. The direction is stated because it is the whole point:
  hostile is anonymous, **never** authenticated, and any other exception still
  propagates so a store outage is not disguised as an anonymous read. Written at
  `spec-040:1324-1345`.
- **D7.12** — what is single-sited in the ONE field-construction helper is the
  sync-vs-async **dispatch seam** plus the signature / annotation injection; the
  per-surface request resolution, gate and session work live in the sync and async
  resolver **bodies** that helper is handed, which is what makes them the
  per-transport specialization point without the dispatch seam changing (pointing at
  Decision 10, which Slice 2 wrote). Written at `spec-040:1375-1383`.

#### Decision 8 — the user model's primary `DjangoType` is required, validated at bind

| # | Claim | Settling citation | Verdict |
|---|---|---|---|
| D8.1 | "`login_mutation()`, `register_mutation()`, and `current_user()` all type their user surface as the **primary** `DjangoType` registered for `get_user_model()`" | `::bind_auth_mutations #"user_typed = ["` lists exactly `("login", "register", "current_user")`; `login` and `current_user` receive `primary` directly, `register`'s `Meta.model = get_user_model()` routes it through `_resolve_primary_type` | `CONFORMS` |
| D8.2 | "`bind_auth_mutations()` validates at phase 2.5, **and only when the surface-keyed ledger carries a user-typed surface** — a logout-only ledger never performs the lookup at all, so the exemption is structural, not a message branch" | `::bind_auth_mutations #"if user_typed:"` guards the single `_resolve_user_primary_or_raise` call. `tests/auth/test_mutations.py::test_logout_only_schema_binds_with_no_user_type_and_no_orphan_payloads` | `CONFORMS` |
| D8.3 | "it resolves the user primary via `registry.get(get_user_model())` — **the same getter `_resolve_primary_type` uses**, so 'what counts as a registered primary' stays single-sited and only the raise *message* differs" | `::_resolve_user_primary_or_raise #"primary = registry.get(user_model)"` beside `mutations/sets.py::_resolve_primary_type #"primary = registry.get(model)"` — the same call, two messages | `CONFORMS` |
| D8.4 | "It consults `registry.types_for` **only** to split the no-registered-type message from the multiple-types-without-primary ambiguity message" | `::_resolve_user_primary_or_raise #"if registry.types_for(user_model):"` appears once, after the `primary is not None` early return, and selects only which of two `ConfigurationError`s is raised | `CONFORMS` |
| D8.5 | "finalization fails with a `ConfigurationError` naming the missing registration and the fix ('declare a `DjangoType` with `Meta.model = get_user_model()`; mark it `Meta.primary = True` if the model has several')" | `::_resolve_user_primary_or_raise #"declare a DjangoType with Meta.model = get_user_model() "` + `#"(mark it Meta.primary = True if the model has several types)"`. Both clauses present, and the message additionally names the consumer-written factory via `::_SURFACE_FACTORY_NAMES` | `CONFORMS` |
| D8.6 | "`logout_mutation()` is exempt — its `{ ok, errors }` payload references no user type, so a logout-only schema needs no user type and resolves no primary" | `"logout"` is absent from the `user_typed` tuple; the logout arm builds its payload with `object_type=None`. Same test row as D8.2 | `CONFORMS` |
| D8.7 | "**The validation must run BEFORE `bind_mutations()` to be reachable for `register`** … `_resolve_primary_type`'s no-registered-type raise is a **generic** message naming the internal `Register` class … with no `get_user_model()` / `Meta.primary` recourse" (`#"the mutation has no type to return"`) | `mutations/sets.py #"registered DjangoType; the mutation has no type to return. Declare a "` — the cited substring resolves. Ordering proved by `types/finalizer.py`'s phase-2.5 sequence (Slice 2's D9.5) and, behaviourally, by `::test_register_only_schema_without_user_type_raises_the_register_arm_error`, which asserts the generic wording is **absent** | `CONFORMS` |
| D8.8 | "Tests pin the **exact** error a no-`UserType` schema produces for `register` specifically, distinct from `login`'s — **on both the first finalize and a post-reload second finalize**" | `::_REGISTER_ARM_ERROR` and `::_LOGIN_ARM_ERROR` are separate regex constants in the test module; `::test_register_only_schema_without_user_type_raises_the_register_arm_error` (first finalize) and `::test_register_arm_error_survives_a_reload_cycle` (second) | `CONFORMS` |
| D8.9 | "**The user type's field selection IS the authenticated read surface** … a `fields = "__all__"` over the user model surfaces the password **hash**, `is_superuser` / `is_staff`, and `last_login` through `LoginPayload.node`, `RegisterPayload.node`, and `me` … This is doc-only guidance — the package does not police the consumer's selection" | No `Meta.fields` policing exists on the read side (`rg "__all__" django_strawberry_framework/auth/` → 0). The example follows the guidance: `examples/fakeshop/apps/accounts/schema.py::UserType #"fields = ("id", "username", "email")"`, with the module docstring stating the reason | `CONFORMS` |
| D8.10 | "the Slice 3 GLOSSARY entry carries the same caution" | `docs/GLOSSARY.md` `## Auth mutations` #"The consumer `UserType`'s field selection IS the authenticated read surface" — present at `3a294082` and at `HEAD`, including the `password`/privilege-column exclusion direction | `CONFORMS` |
| D8.11 | "because `me` and `login.node` deliberately skip `get_queryset`, a `UserType.get_queryset` written to **row-redact** gives **no** protection on those two surfaces — only the field selection governs what a logged-in actor sees of *themselves* there" | `queries.py::_current_user_resolve_body` (D7.19) and `mutations.py::_login_result_payload` (Slice 2's D5.20) both return the in-hand object with no visibility call. The GLOSSARY entry carries the same asymmetry note | `CONFORMS` |
| D8.12 | "the register payload's re-fetch is likewise by-pk-without-visibility, but that is the `036` own-write exception, not a general read-gate bypass" | the skeleton's `refetch_optimized` tail (D6.37); the distinction is stated in `## User-facing API` and in `::_run_register_pipeline_sync`'s docstring | `CONFORMS` |

No `SPEC-STALE` row. **Decision 8 is the one Decision in this slice's scope that
needed no edit at all** — recorded as a measured no-change in the rationale companion,
since a checked claim and an unexamined one read identically otherwise.

#### Decision 12 — this card owns the `0.0.13` version bump and completes the joint cut

Graded per `docs/builder/BUILD.md` `### "## Current state": observations stand,
predictions do not`. A completed version-cut obligation is an **observation**: true on
its own date, merely historical now, and therefore not stale. Every row below was
settled read-only at `3a294082 Release 0.0.13`, the commit where the obligation was
due — never at `HEAD`, which would grade the wrong tree.

| # | Claim | Settling citation | Verdict |
|---|---|---|---|
| D12.1 | "`040` is now the **lone non-Done `0.0.13` card**: `039` is Done" | `git show 3a294082:KANBAN.md` carries `DONE-039-0.0.13` and `DONE-040-0.0.13` and no `WIP-ALPHA-040`; dated observation, honoured | `CONFORMS` |
| D12.2 | "Slice 3 therefore aligns the version quintet: `pyproject.toml` `[project].version`" | `git show 3a294082:pyproject.toml` → `version = "0.0.13"` under `[project]`. **Now historical**: `HEAD`'s `pyproject.toml` carries no version literal at all — hatchling derives it from `__version__` via `[tool.hatch.version]`, so the quintet is a quartet today (`AGENTS.md` rule 31). The Decision states what Slice 3 did, which it did | `CONFORMS` |
| D12.3 | "`__version__` in `__init__.py`" | `git show 3a294082:django_strawberry_framework/__init__.py` → `__version__ = "0.0.13"` | `CONFORMS` |
| D12.4 | "`tests/base/test_init.py::test_version`" | `git show 3a294082:tests/base/test_init.py` → `assert __version__ == "0.0.13"` | `CONFORMS` |
| D12.5 | "the `docs/GLOSSARY.md` package-version line" | `git show 3a294082:docs/GLOSSARY.md` → ``Current package version: `0.0.13`.`` | `CONFORMS` |
| D12.6 | "the `django-strawberry-framework` `version` entry inside `uv.lock`" | `git show 3a294082:uv.lock` → the package's own entry reads `version = "0.0.13"` | `CONFORMS` |
| D12.7 | "the GLOSSARY `SerializerMutation` status flips … to `shipped (0.0.13)`; `docs/README.md` / `README.md` move the serializer flavor **and** the new auth surface from 'Coming next' to 'Shipped today' (README **Status** version line → `0.0.13`)" | GLOSSARY index row `shipped (0.0.13)`; `docs/README.md` `**Shipped today** (0.0.13):` with the next block naming `0.0.14`; `README.md` `## Status` → `**0.0.13, single-maintainer, alpha-quality.**` naming both surfaces | `CONFORMS` |
| D12.8 | "`CHANGELOG.md` carries the `0.0.13` release bullets covering **both** cards … the edit must be explicitly named in the Slice 3 maintainer prompt — this spec describes it but cannot authorize it" | `git show 3a294082:CHANGELOG.md` → `## [0.0.13] - 2026-07-06` with two `### Added` bullets (serializer flavor; session-auth surface) and the `### Changed` version bullet. The permission was evidently granted; the conditional itself is a rule about the *prompt*, not a claim about the tree | `CONFORMS` |
| D12.9 | "`0.0.13` is a routine patch cut, not a milestone (`X.Y.0`) rollover, so no `alpha constraint` lifts or milestone-prose flips apply. The bump moves only in Slice 3 … never in Slice 1" | `0.0.13` is a patch segment; `git log -S'__version__ = "0.0.13"'` attributes the literal to the release/doc-slice commits, not to the Slice-1 substrate commit | `CONFORMS` |

#### `## User-facing API` / `### Error shapes` — the `register` and `me` paragraphs

| # | Claim | Settling citation | Verdict |
|---|---|---|---|
| U.1 | the SDL block's `register(data: RegisterInput!): RegisterPayload!` and `me: UserType` | `test_auth_api.py::test_reload_idempotence_cycle_rebuilds_the_full_auth_surface` asserts the register signature verbatim; `::test_generated_auth_type_shapes` introspects `RegisterInput` / `RegisterPayload` | `CONFORMS` |
| U.2 | `input RegisterInput { username: String!  email: String  password: String! }` — the field set, order, and nullability | `derive_register_fields(User) == ("username", "email", "password")` (`tests/auth/test_mutations.py::test_derive_register_fields_default_user_model`); nullability pinned by `::test_generated_auth_type_shapes` | `CONFORMS` |
| U.3 | "`username` and `password` are non-null …; `email` is **optional** … each `REQUIRED_FIELDS` entry follows the standard `input_field_required` rule (`#"return not field.blank"`)" | citation resolves (D6.8); the rationale ("`REQUIRED_FIELDS` governs `createsuperuser`'s interactive prompts, not model-level required-ness") is stable design prose | `CONFORMS` |
| U.4 | "`register(data:)` creates the account: password validated against `AUTH_PASSWORD_VALIDATORS` (failures keyed to `password`)" | `::_register_write_step` (D6.25); live `test_auth_api.py::test_weak_password_register_envelope_keys_to_password_not_all` under fakeshop's configured validators | `CONFORMS` |
| U.5 | "the user-model `full_clean()` envelope for everything else (a duplicate username keys to `username`)" | D6.28; `::test_duplicate_username_register_envelope_keys_to_username` | `CONFORMS` |
| U.6 | "the password stored hashed, and the created user returned in the uniform slot — re-fetched optimizer-planned like every other create" | D6.26 / D6.30 / D6.37; `::test_register_login_me_logout_round_trip_and_hashed_storage` | `CONFORMS` |
| U.7 | "`me` returns the session user typed as the consumer's `UserType`, or `null` for an anonymous request" | D7.3 / D7.17; `::test_anonymous_me_is_null_not_an_error`. (The under-described "otherwise" is D7.4's row and is fixed in the Decision, where the contract belongs, not restated here) | `CONFORMS` |
| U.8 | "Each factory accepts `permission_classes=` (default: allow-any …): `register_mutation(permission_classes=[InviteOnly])` gates registration through the same `has_permission` seam every write flavor uses" | `::register_mutation(permission_classes=…)` → `Meta.permission_classes` on the rider, i.e. the standard `DjangoMutation.check_permission` path; `tests/auth/test_mutations.py::test_gated_register_denies_with_the_standard_create_string` | `CONFORMS` |
| U.9 | `### Error shapes` rows for `register` (validator failure → `password`; duplicate username → `USERNAME_FIELD`) and for anonymous `me` (→ `null`, never an error) | the three live rows named above | `CONFORMS` |

The `### Error shapes` table carried **no** row for a non-UTF-8-encodable `register`
password, a live-reachable case (`test_auth_api.py::test_register_surrogate_password_keys_to_password_not_a_crash`).
Added as part of the D6.27 discharge rather than as its own verdict row, since it is
the same divergence seen from the table side.

### Verdict tally

Row counts are the `len()` of each block above, re-counted as this table was written:
D6 = 41, D7 = 20, D8 = 12, D12 = 9, `## User-facing API` / `### Error shapes` = 9.

| Verdict | Count |
|---|---|
| `CONFORMS` | 83 |
| `SPEC-STALE` | 8 |
| `CODE-GAP` | **0** |
| `UNPROVABLE` | 0 |
| **Total rows** | **91** |

The eight `SPEC-STALE` rows, listed so the count is re-derivable rather than asserted:
D6.9, D6.14, D6.21, D6.22, D6.27, D6.32, D7.4, D7.12. They are discharged by **nine**
content edits below (D6.21 + D6.22 are one edit; D6.27 takes three — a new preflight
paragraph, the corrected "ONLY auth-specific steps" sentence, and an `### Error shapes`
row).

**Direction of every divergence.** Six of the eight are post-release movement
(`a40f0d33`, `31625ac7` ×2, `a6f5a6cb` + `a8f31a2d`, `ab821ae0`, `3120dc5a` +
`c537b2dc` + `6873dac6`). **Two were inaccurate on their own date** (D6.14 and D7.12,
both verified identical at `3a294082`) — the first rows in this cycle that are not
post-ship drift, which is why each is labelled as such in the companion. None is a
`CODE-GAP`: nothing Decision 6, 7, 8 or 12 planned is missing from the shipped tree.

### Boundary-removal reasoning (read-only)

No mutation was applied — this pass may not mutate source. For each boundary a claim
rests on, whether a test would fail if it were removed, by reading:

- **The privilege rejection** (D6.9): deleting the `_REGISTER_PROTECTED_FIELDS`
  intersection makes `derive_register_fields(PrivilegeRequiredUser)` return
  `("username", "is_staff", "password")` instead of raising, so
  `::test_derive_register_fields_rejects_privilege_fields` fails. **One row.** Weakly
  pinned by the `0 or 1` rule — but this is an audit, not a boundary-introducing pass,
  and the rule governs boundaries a slice *introduces*. Recorded as a coverage
  observation for Slice 4, which owns `## Test plan`: a second row (the same custom
  model reaching `register_mutation()` end to end, so the raise is proved to surface at
  declaration rather than only from the helper) would lift it.
- **The exclusion seam's provided-marker fold** (D6.23): removing
  `#"provided \|= {model_fields[attr].name for attr in excluded_values}"` marks
  `password` unprovided, so `_unprovided_exclude` adds it to `exclude` and
  `::test_exclusion_seam_captures_password_and_preserves_the_provided_marker` fails on
  `assert "password" not in exclude`. One row directly — plus the strict three-tuple
  unpack in `_model_write_step`, whose removal is caught by
  `::test_model_decode_step_without_exclusion_keeps_the_historical_three_tuple`.
- **`set_password` before `full_clean`** (D6.26): swapping the order makes the
  147-character password fail the `password` column's `max_length` check, so
  `::test_sync_register_never_persists_the_plaintext_and_hashes_before_full_clean`
  fails on a non-empty `errors` list. The async twin fails independently. Two rows,
  one per override — exactly the independence the Decision's "can regress
  independently" clause asks for.
- **The `password`-keyed error construction** (D6.25): routing the `ValidationError`
  through `validation_error_to_field_errors` instead keys it to `"__all__"`, so both
  `::test_weak_password_register_envelope_keys_to_password_not_all` and
  `::test_dict_form_validator_error_still_keys_to_password_not_a_crash` fail on
  `[error["field"] for error in payload["errors"]] == ["password"]`. Two rows.
- **The every-call double re-record** (D6.39): dropping either call leaves a drained
  ledger with no re-add, so `::test_register_arm_error_survives_a_reload_cycle`
  (auth ledger) or `::test_reload_idempotence_cycle_rebuilds_the_full_auth_surface`
  (mutation ledger) fails. One row per ledger — the two-ledger split the Decision
  insists on is exactly what makes them separable.
- **The shared anonymity classifier's absent-`user` arm** (D7.4): restoring the
  pre-`3120dc5a` `user = request.user; actor = user if user.is_authenticated else None`
  raises `AttributeError` out of the resolver, failing
  `::test_me_is_null_not_a_crash_when_the_request_user_is_absent` and
  `::test_me_accepts_a_regular_mapping_context_with_a_django_request`; the hostile arms
  add `::test_hostile_user_descriptor_raising_collapses_to_anonymous_null`,
  `::test_async_hostile_truthiness_collapses_to_anonymous_null`, and the three legacy-callable
  rows. Strongly pinned.
- **The surface-keyed `current_user` bind arm** (D7.15 / D8.2): removing the
  `current_user_holder is not None` guard materializes an alias for a schema that
  declared no `me`, which
  `tests/auth/test_queries.py::test_current_user_only_bind_emits_no_login_logout_payloads`'s
  sibling rows in `tests/auth/test_mutations.py` detect through the orphan-payload
  assertions.

### Notes for Worker 1 (spec reconciliation)

**Slice 2's two hand-offs, discharged.**

1. *(Slice 2 item 7)* Decision 7's `current_user` contract is audited here — 20 rows,
   one `SPEC-STALE` (D7.4, the under-described nullable "otherwise") plus D7.12's
   single-siting sentence. Slice 2's D5.16 gate-payload row is not re-graded.
2. *(Slice 2 item 8)* Confirmed: `::_REGISTER_PROTECTED_FIELDS` and the privilege
   rejection `derive_register_fields` drives were **absent from Decision 6's text**.
   Row D6.9, edit 1. The stock-model structural argument the Decision made was correct
   and is kept; what it missed is that the helper takes the model as an *argument*, so
   a custom model could reintroduce the column — which is why `a40f0d33` added the
   check. The spec now states both layers.

**Hand-offs to Slice 4 (helper-reuse obligations, edge cases, test plan, DoD).**

3. **`## Test plan` owes a row for a deep `me { … }` selection under Strictness mode.**
   Decision 7's closing sentence claims an unplanned nested selection under `me` is
   visible to [Strictness mode][glossary-strictness-mode] like any non-root object.
   It is true by construction (row D7.20) and pinned by nothing: no test selects a
   relation under `me` at all, let alone with strictness on. Same shape as Slice 2's
   `loaded_attr` finding — the code is right, the test plan is short.
4. **`## Test plan` owes a second row for the privilege rejection.** See
   *Boundary-removal reasoning* above: the boundary is pinned by exactly one row, at
   the helper level only. A row driving `register_mutation()` against a custom user
   model whose `REQUIRED_FIELDS` names a protected column would pin that the raise
   reaches the consumer at declaration time.
5. **The D6 / D7 helper-reuse obligations should be re-graded against this slice's
   edits.** Decision 6's `D6` reuse directive (the shared UNSET-strip walk) and `D7`
   (`validate_password` + `set_password` as the only auth-specific steps) are both
   cited inside the sentences edits 3 and 5 rewrote. Slice 4 owns
   `## Helper-reuse obligations (DRY)` and must confirm the `D6` / `D7` items there
   still agree with the corrected Decision text, exactly as it must for `D17` / `P3`
   (Slice 2's item 11). A directive and its Decision disagreeing inside one spec is
   the defect `## Edge cases`-vs-Decision cross-checking exists to catch.
6. **`D12` / `P1` / `P2` is cited by Decision 7's rewritten sentence.** The obligation
   text ("the whole resolve-request → gate → session-work → inject-signature
   dispatcher … single-sited") may carry the same inaccuracy the Decision did. Slice 4
   should grade the obligation against `mutations.py::_make_auth_field` directly, not
   against the Decision.

**Hand-off to Slice 5 (transport).**

7. Nothing in this slice's scope states a transport contract, and none was added.
   `register` and `current_user` are transport-neutral in the spec and in the code:
   the register rider rides the shared write skeleton with no transport prologue, and
   `queries.py::_current_user_resolve_body` resolves the request through
   `request_from_info` and classifies it through the shared helper, which is what makes
   `me` work over the Channels adapter without a branch of its own. If Slice 5's
   Decision 11 rewrite enumerates per-surface transport support, `current_user` belongs
   in it as "every transport, read-only, no session mutation" — and that is the only
   place it should be stated.

**Findings for the maintainer — out of scope for this cycle's edits.**

- **F1 — `docs/GLOSSARY.md`'s `## Auth mutations` entry repeats the framing row D6.9
  falsified.** It reads "the privilege columns (`is_staff` / `is_superuser` / `groups`
  / `user_permissions`) are unreachable by construction", which (a) omits `is_active`,
  which IS in `::_REGISTER_PROTECTED_FIELDS`, and (b) states the structural layer as
  the whole story, exactly as the spec did before edit 1. The glossary is generated
  from the fakeshop `glossary` app DB and is on this cycle's out-of-scope list, so no
  edit was made. The fix is a DB edit plus `scripts/build_glossary_md.py`, and it
  should land with whatever change next touches that entry.
- **F2 — five `spec-040 Revision N` citations in shipped source and tests now decode
  against nothing in the spec.** Slice 1 moved the revision history to the rationale
  companion; the companion preserves the `Revision N` numbering, so the *content*
  survives, but every citer names `spec-040`, which no longer contains it. Sites:
  `django_strawberry_framework/auth/mutations.py #"(the Revision-7 reload"`;
  `django_strawberry_framework/mutations/resolvers.py #"spec-040 Revision-7 marker fix"`;
  `tests/auth/test_mutations.py:637`; `examples/fakeshop/test_query/test_auth_api.py:234`
  and `:403`. This is the "stripping a label vocabulary is a rename that strands every
  citer" shape, and Slice 1's sweep covered the spec's own inline attributions only —
  it could not have seen the code-side citers, which no gate checks (`check_citations.py`
  is `path::Symbol`-only). Separately, `AGENTS.md` "No process provenance in code"
  arguably forbids the round attribution outright, in which case the fix is deletion
  rather than retargeting. Either way it is a `.py` edit and therefore the maintainer's
  call, not this cycle's.
- **F3 — three `mutations/*.py` docstrings still name the removed `_bind_mutation`.**
  `mutations/sets.py` (twice: the `build_input` seam note and `bind_mutation_outputs`'s
  own bullet) and `mutations/resolvers.py` cite a symbol `ab821ae0` deleted. Harmless
  to behavior, invisible to `check_citations.py` (the mentions are backticked prose,
  not `path::Symbol`), and out of this cycle's scope. Noted because row D6.32 is the
  spec-side half of the same rename and it would be odd to fix one without recording
  the other.

**Working-tree note (stop-and-report, no action taken).** `git status --short` at the
end of this pass shows `M docs/feedback.md` alongside this cycle's own files. It was
already dirty in this session's opening snapshot, it is not on this slice's writable
list, and no file in this pass touched it — concurrent maintainer work per `AGENTS.md`
rule 34. **Not reverted.** The build plan's pre-flight recorded a clean baseline at
`d3b91c8d`; the tree has since moved (the concurrent `spec-050` cycle committed its
work), so the plan's "baseline-dirty: none" line describes that commit, not now.

### Spec changes made (Worker 1 only)

All in `docs/SPECS/spec-040-auth_mutations-0_0_13.md`; line numbers are post-edit.
Every "why" appended to `docs/SPECS/appx/spec-040-auth_mutations-0_0_13-rationale.md`
under the owning Decision's `### Changes this Decision underwent`.

| # | Spec lines | Change | Reason |
|---|---|---|---|
| 1 | 1104-1117 | Decision 6: "structurally unreachable, not policy-checked" replaced by the two-layer statement — structural for the stock model, an explicit `ConfigurationError` rejection for a custom model that names a protected column in `USERNAME_FIELD` / `REQUIRED_FIELDS`, from one module-level frozenset | Row D6.9 (Slice 2 hand-off 8) |
| 2 | 1145-1151 | Decision 6: the kwarg partition re-attributed from "the shared signature helper" to each factory's own keyword-only signature, with each class's single consumer named and the key rule restated as its consequence | Row D6.14 — the helper receives only the GraphQL-argument class |
| 3 | 1182-1199 | Decision 6: the exclusion seam restated as a bind-declared `EXCLUDED` field kind honoured by the ONE shared `decode_provided_fields` spine, with the extended-vs-historical tuple rule and the strict three-tuple unpack guard | Rows D6.21, D6.22 — the `excluded_input_fields` parameter no longer exists |
| 4 | 1211-1223 | Decision 6: new write-step lead-in — the three-guard password preflight and why the seam makes it necessary | Row D6.27 |
| 5 | 1237-1240 | Decision 6: "`validate_password` + `set_password` are the ONLY auth-specific steps" → "the password preflight, `validate_password` and `set_password`", with the preflight's own reuse stated | Row D6.27 |
| 6 | 775 | `### Error shapes`: new row for an unstorable `password` on `register` | Row D6.27, table side |
| 7 | 1256-1259 | Decision 6: `_bind_mutation` → the phase-2.5 bind's payload half, `mutations/sets.py::bind_mutation_outputs` | Row D6.32 — the symbol was removed by `ab821ae0` |
| 8 | 1324-1345 | Decision 7: the nullable return restated as the ONE shared classification (pointing at Decision 5), with "otherwise" spelled out — absent `user` attribute, hostile actor, the fail-closed direction, and the propagate-everything-else rule | Row D7.4 |
| 9 | 1375-1383 | Decision 7: the single-siting claim narrowed to the dispatch seam + signature injection, with the per-surface sync / async bodies named as the specialization point (pointing at Decision 10) | Row D7.12 |

No link definition was added to the spec: every reference the edits use
(`[glossary-configurationerror]`, `[utils-write-values]`, `[utils-inputs]`,
`[mutations-inputs]`, `[mutations-sets]`) was already defined and in use.

Rationale companion: post-ship bullets appended under Decisions 6, 7, 8 and 12 —
four change bullets plus a second `No longer claims` bullet for Decision 6, two change
bullets plus a `No longer claims` bullet for Decision 7, and a *checked-and-still-true*
bullet for Decisions 8 and 12 (per the companion's own rule that a measured no-change
and an unexamined one read identically otherwise). Each names what the Decision
claimed, the commit that changed it (`a40f0d33`, `31625ac7`, `a6f5a6cb`, `a8f31a2d`,
`ab821ae0`, `3120dc5a`, `c537b2dc`, `6873dac6`, `c8346750`), and what it may no longer
claim; the two on-their-own-date inaccuracies say so explicitly rather than borrowing a
commit. Two link definitions added there: `[readme]` under `<!-- Root -->` and
`[glossary-serializermutation]` under `<!-- docs/ -->`, both alphabetical within their
group.

**No spec edit touched Decision 11, Decisions 1-5, Decisions 9-10, Decision 8,
Decision 12, `## Helper-reuse obligations (DRY)`, `## Edge cases and constraints`,
`## Test plan`, `## Definition of done`, or the `## Slice checklist`.**

---

## Final verification (Worker 1)

No `CODE-GAP` row, so this closes as a Worker-1-only slice
(`docs/builder/build-040-auth_mutations-0_0_13.md` `## Artifact list`). No Worker 2 or
Worker 3 pass is owed.

- **Spec status-line re-verification:** `docs/SPECS/spec-040-auth_mutations-0_0_13.md:1-111`
  re-read at the start of this pass. The `Status:` line
  (`**SHIPPED (0.0.13) — all slices final-accepted; …**`), the three-slice summary, the
  owner line, the predecessor list, the `docs/GLOSSARY.md` status sentence (Slice 2's
  edit 1), and the rationale-companion pointer (Slice 1's) all still describe the
  build's state. **No edit owed.**
- **Spec slice checklist:** 12 of 12 boxes `- [x]` — Slice-2 block 5 of 5, Slice-3
  block 6 of 6 — each with a symbol-qualified or `git show`-at-`3a294082` proof. No box
  left `- [ ]`; no deferral reason owed. Every Slice-3 doc obligation was honoured at
  the cut, so nothing routes to the maintainer as unhonoured; the one doc finding (F1)
  is a *later* staleness in `docs/GLOSSARY.md`, not a missed obligation.
- **Conformance matrix:** 91 rows — 83 `CONFORMS`, 8 `SPEC-STALE`, 0 `CODE-GAP`,
  0 `UNPROVABLE`. Every `SPEC-STALE` row was discharged by an edit in this pass; none
  was deferred.
- **DRY check across this slice and Slices 1-2:** no new duplication. The two live
  risks — the anonymity rule stated in both Decision 5 and Decision 7, and the
  sync/async body split stated in both Decision 7 and Decision 10 — were avoided by
  making Decision 7 point at Slice 2's single statements in each case. No edit in this
  pass restates a contract another Decision owns, and no edit touched a Decision
  Slice 2 closed.
- **Existing tests still run:**
  `uv run pytest tests/auth examples/fakeshop/test_query/test_auth_api.py --no-cov -q`
  → **210 passed**, 0 failed, 0 errors, 15.53s. No `--cov*` flag (`BUILD.md`
  `## Coverage is the maintainer's gate, not a worker's tool`).
- **Fail-open shapes:** read the audited surface for the catalogued shapes. Three
  candidates, none a finding. (a) `::_register_decode_step #"excluded_values.get("password")"`
  is a `getattr`-default shape on a value whose absence is meaningful — but the absent
  case is caught immediately downstream by `::_register_write_step`'s
  `#"if raw_password is None:"` returning the null-field leaf, so absence exits to the
  envelope rather than being coerced into a permit. (b) `::_register_write_step`'s
  `#"if not isinstance(raw_password, str):"` guards the **answer** (a value that cannot
  be hashed) rather than one spelling of bad input. (c)
  `::_authenticated_actor_or_none`'s five-exception arms return `None`, which is the
  *anonymous*, i.e. denied, side — hostile classifies as anonymous, never as
  authenticated, and every other exception propagates. Slice 2 graded (c) the same way;
  restated here only because Decision 7's rewritten text now makes the direction a
  stated contract rather than an implementation detail. No finding.
- **Relocation / promotion claims:** one in scope, proved rather than accepted.
  Decision 6 claims the register rider "rides, does not fork" the shared skeleton.
  Verified by reading both sides rather than by the docstring: `auth/mutations.py`
  contains no `transaction.atomic`, `open_write_pipeline`, `refetch_optimized`,
  `locate_instance` or `build_payload` call (`rg` → 0 hits each), and
  `::_run_register_pipeline_sync` calls `run_write_pipeline_sync` with only the two
  step kwargs. The `0.0.13` tree is identical in this respect
  (`git show 3a294082:django_strawberry_framework/auth/mutations.py`), so the claim was
  true at ship and is true now.
- **Hot-path:** the plan declares none by default, and this slice produced no code gap,
  so nothing lands on the per-request resolver path. **Not applicable; no
  re-declaration is owed.**
- **Floor verification:** the plan declares none by default, same condition. **No floor
  scope owed by this slice.** (The floor versions are stated only in
  `docs/builder/BUILD.md` `## Floor verification` and were not needed.)
- **Gates run:**
  - `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-040-auth_mutations-0_0_13.md`
    → `OK: 30 terms - all have glossary entries and at least one spec link.` (exit 0)
  - In-page anchors, both files: every `](#…)` target resolves against a real heading
    (spec: 144 refs / 34 headings, 0 missing; rationale: 74 refs / 20 headings, 0
    missing).
  - Reference-style link convention: every `][label]` has a definition and every
    definition a use, in both files (0 undefined, 0 unused); all ten canonical group
    headers present and in order in both; the two new definitions alphabetical within
    their group.
  - `uvx pre-commit run --files docs/SPECS/spec-040-auth_mutations-0_0_13.md docs/SPECS/appx/spec-040-auth_mutations-0_0_13-rationale.md docs/builder/bld-040-slice-3-audit_register_current_user.md` —
    pass, and pass again with no rewrite on a second run.
  - `git status --short` — this cycle's files plus `M docs/feedback.md`, which is
    concurrent maintainer work reported above and deliberately untouched.
- **Spec reconciliation:** done in-pass; 9 edits recorded above.
- **Final status:** `final-accepted`.

### Summary

A read-only conformance audit of `spec-040`'s Decisions 6, 7, 8 and 12, the Slice-2 and
Slice-3 checklist blocks, and the `register` / `me` half of `## User-facing API` /
`### Error shapes` against the shipped tree. **Nothing was dropped or forgotten:** all
twelve checklist boxes are proved landed, including the six Slice-3 doc and
version-cut obligations audited read-only at `3a294082 Release 0.0.13`, where all five
version-quintet members and every joint-cut release flip were honoured. Decision 6's
pipeline was graded step by step and every step it specifies is present at the release
commit, the narrowest ones included. Of 91 rows, 8 are `SPEC-STALE` and none is a
`CODE-GAP`: six are post-release movement (the privilege rejection, the exclusion seam
becoming a field kind, the password preflight, the `_bind_mutation` split, and the
shared anonymity classifier) and **two were inaccurate on their own date** — the first
such rows in this cycle, which is why the prior that all drift runs one direction was
worth not inheriting. The spec now states the shipped contract directly for the
two-layer privilege guard, the bind-declared exclusion seam, the write step's
password preflight, the surviving bind symbol, the full nullable-`me` classification
and its fail-closed direction, and what the ONE auth field helper actually single-sites.
Decision 8 needed no edit and is recorded as a measured no-change. Five items were
handed to Slice 4, one to Slice 5, and three findings to the maintainer.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[changelog]: ../../CHANGELOG.md
[goal]: ../../GOAL.md
[init]: ../../django_strawberry_framework/__init__.py
[kanban]: ../../KANBAN.md
[pyproject]: ../../pyproject.toml
[readme]: ../../README.md
[today]: ../../TODAY.md

<!-- docs/ -->
[docs-readme]: ../README.md
[glossary-auth-mutations]: ../GLOSSARY.md#auth-mutations
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-djangomutation]: ../GLOSSARY.md#djangomutation
[glossary-fielderror-envelope]: ../GLOSSARY.md#fielderror-envelope
[glossary-get_queryset-visibility-hook]: ../GLOSSARY.md#get_queryset-visibility-hook
[glossary-serializermutation]: ../GLOSSARY.md#serializermutation
[glossary-strictness-mode]: ../GLOSSARY.md#strictness-mode
[glossary]: ../GLOSSARY.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[rationale-risks]: ../SPECS/appx/spec-040-auth_mutations-0_0_13-rationale.md#risks-and-open-questions

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->
[test-base-init]: ../../tests/base/test_init.py

<!-- examples/ -->
[test-query-readme]: ../../examples/fakeshop/test_query/README.md

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
