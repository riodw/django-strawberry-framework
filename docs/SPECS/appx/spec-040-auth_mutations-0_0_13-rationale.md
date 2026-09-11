# Rationale companion: spec-040 (Auth mutations — `login_mutation` / `logout_mutation` / `register_mutation` / `current_user`)

Companion to [`docs/SPECS/spec-040-auth_mutations-0_0_13.md`][spec-040]. It carries
that spec's **deliberative layer** and nothing else: the authoring revision history
that produced the contract across seven revisions, every Decision's justification,
every alternative a Decision rejected and why it lost, the claims individual
Decisions once made and may no longer make, and the risk / open-question
deliberation that settled the card's design questions. The spec carries the
contract; this file carries how the contract was arrived at. Neither duplicates the
other — the text here **left** the spec.

Read this when checking a finished implementation against the reasoning that
produced it, or before re-opening a settled question. Worker 2 never reads it
([`docs/builder/BUILD.md`][build-md] `### Who reads it, and when`).

**How later passes append to this file.** Each Decision below carries a
`### Changes this Decision underwent` section. A reconciliation pass that finds the
spec stale against `HEAD` — a guard that shipped differently, a helper that never
landed where the Decision said it would, a default a later card inverted — appends a
`**Post-ship:**` bullet there, naming the shipped behaviour and the card or commit
that changed it. A Decision a reconciliation checked and found still true earns a
bullet too, saying so: a measured no-change and an unexamined one read identically
otherwise. Findings belonging to no single Decision go under
[Non-Decision deliberation](#non-decision-deliberation). **This is where the *why* of
every reconciliation edit the rest of this cycle makes to the spec belongs, and it is
the only place it belongs.** Slices 2–5 of the `040` retrospective cycle correct the
spec to state the shipped contract directly; each correction's explanation — what the
spec said before, what falsified it, which commit or card did — appends here, never
to the spec, which never narrates its own history
([`docs/builder/BUILD.md`][build-md] `## Spec rationale extraction`). Nothing needs
restructuring to take an addition.

## Provenance of this record

Created by Slice 1 of the `040` retrospective reconciliation cycle, whose plan is
[`docs/builder/build-040-auth_mutations-0_0_13.md`][build-040] and whose record of the
move itself is the per-cycle artifact
[`docs/builder/bld-040-slice-1-rationale_extraction.md`][bld-040-slice-1].
`spec-040` shipped in `0.0.13` with a [`-terms.csv`][spec-040-terms] companion and no
`-rationale.md` sibling — the one archived spec of its generation missing one, since
`docs/SPECS/appx/` carries rationale files for `036`, `037`, `038`, `039` and
`044`–`048`. This file closes that gap. Nothing in it is new reasoning: every passage
below was cut from the spec in the same pass that created this file, except the
framing paragraphs, the `### Changes this Decision underwent` summaries, and the
[Non-Decision deliberation](#non-decision-deliberation) entries, which are this pass's
own and say so. The `036` / `037` / `038` / `039` companions are the four
immediately-preceding executions of the same move and this file matches their shape.

The spec was verified byte-identical to `HEAD` before the first edit
(`git show HEAD:docs/SPECS/spec-040-auth_mutations-0_0_13.md` into a scratch path
outside the repo, diffed clean against the working copy) at **207,790 bytes, 2,879
lines**. It stood at **164,391 bytes, 2,302 lines** when the move finished:
**47,313 bytes cut** by five routes, of which **45,936 bytes** are reproduced here
and **1,377 bytes** were deleted rather than moved (a 62-byte preamble line, its
1-byte blank, and 1,314 bytes of chronology attribution), with **3,914 bytes** of
pointers, link definitions, two restored clauses and two rewritten passages added
back, for a net **43,399 bytes** removed.

- **The whole `Revision history (kept inline so the spec is self-contained):`
  block** — its preamble, the blank line under it, and **seven** `Revision` entries,
  317 lines, **25,717 bytes**. The seven entries are reproduced under
  [Revision history](#revision-history) below, byte-for-byte, **25,654 bytes** of
  them; the 62-byte preamble line was **deleted, not moved** — its claim that the
  history is kept inline is exactly what this move made untrue — and so was the
  1-byte blank line between them.
- **Eight contiguous `Justification` blocks** carrying **nine** `Justification`
  labels, **4,712 bytes**, under eight of the twelve Decisions. Reproduced under each
  Decision's heading; the labels were inline paragraph prefixes rather than
  standalone lines, so they were stripped and the sections open lower-case, except
  [Decision 7](#decision-7--current_user-returns-the-session-actor-nullable-and-does-not-re-run-get_queryset)'s
  two, whose `for nullable-not-raising` / `for skipping visibility` qualifiers carry
  which half of the Decision each paragraph defends and became bold leads.
- **Twelve `Alternatives considered (and rejected):` blocks**, one under every
  Decision, carrying **35** rejected alternatives, **11,324 bytes**. All twelve labels
  stood on their own line and all twelve became `###` headings here.
- **The body of `## Risks and open questions`** — its preamble plus **six** items,
  **4,246 bytes**. Every item is written as a preferred-answer / fallback pair, which
  is a build-time deliberation instrument rather than a contract, so the body moved
  and the spec keeps the heading and a pointer here.
- **Thirty-eight chronology attributions** — 36 parentheticals and two mid-sentence
  clauses — **1,314 bytes**, deleted rather than moved (see
  [Non-Decision deliberation](#non-decision-deliberation)); what each one recorded is
  in this file's `### Changes this Decision underwent` sections instead.

**The census used the shortest distinctive token, not the label phrase.**
`grep -oc 'ustification'` over the pre-move spec finds **9** occurrences and
`grep -oc 'lternatives'` finds **12** — every one of them a block label, so neither
word appears anywhere else in the spec and neither count is a vocabulary sample of a
larger population. **The pairing is NOT 1:1**: all twelve Decisions carry an
alternatives block, but
[Decision 1](#decision-1--spec-filename-and-canonical-naming),
[Decision 10](#decision-10--sync--async-session-work-through-one-sync_to_asyncthread_sensitivetrue-boundary),
[Decision 11](#decision-11--transport-contract-classify-first-refuse-a-transport-that-cannot-honour-the-surface-truthfully)
and
[Decision 12](#decision-12--this-card-owns-the-0013-version-bump-and-completes-the-joint-cut)
carry no `Justification` block at all (they argue inside the Decision body and open
straight into their rejections), which is why those four carry an explicit `None.`
below — the `037` execution of this move established that convention so a later
reader cannot mistake a genuine absence for a chunk the move dropped. The 35 rejected
alternatives are the top-level `- **` bullets inside the twelve blocks:
1 / 2 / 3 / 2 / 5 / 5 / 3 / 4 / 4 / 1 / 2 / 3 for Decisions 1–12.

**Every in-page anchor was swept, and 31 occurrences were re-pointed across the two
files — 24 here and 7 in the spec.** The moved text carries **82** anchor occurrences across 15 distinct anchors.
Fifty-five are `#decision-N--…` slugs and three are `#risks-and-open-questions`; all
58 resolve locally here, because the twelve Decision headings are reproduced
character-for-character from the spec (only the `###` became `##`, which does not
change a GitHub slug) and this file carries its own
[Risks and open questions](#risks-and-open-questions) heading. The remaining **24**
occurrences, across eight anchors, name spec sections this file does not have
(`#test-plan` ×8, `#edge-cases-and-constraints` ×7, `#borrowing-posture` ×3,
`#slice-checklist` ×2, and one each of `#goals`, `#user-facing-api`,
`#definition-of-done`, `#out-of-scope-explicitly-tracked-elsewhere`); each was
rewritten as a reference-style link into the spec. In the other direction, the spec's
**seven** surviving `[Risks](#risks-and-open-questions)` uses were re-pointed here,
deliberately: every one promises the reader *deliberation* — a preferred reading, a
recorded follow-on, a doc gap the cut chose to note rather than reconcile — and that
deliberation is here, so leaving them would have landed a reader on a spec heading
containing only a pointer back to this file. The spec keeps its
`## Risks and open questions` heading and its pointer paragraph, and has **no**
inbound in-page anchors on it any more. No spec heading was renamed, so no other
in-page anchor moved: a post-move sweep resolves **all** of the spec's remaining
anchor occurrences against its own headings.

**No fragment had to be held back, and the terms-CSV coupling is why that is worth
saying.** `uv run python scripts/check_spec_glossary.py --spec
docs/SPECS/spec-040-auth_mutations-0_0_13.md` requires every term in
[`spec-040-auth_mutations-0_0_13-terms.csv`][spec-040-terms] to keep at least one
**link** in the spec, and the `038` execution of this move discovered that a spec's
`-terms.csv` therefore silently pins which prose the move may not take. All 30 terms
were checked link-by-link against the cut before any text was removed: the deepest
losses are
[`DjangoMutation`][glossary-djangomutation] (24 uses → 19),
[`DjangoMutationField`][glossary-djangomutationfield] (19 → 16) and
[`ConfigurationError`][glossary-configurationerror] (16 → 15), and the smallest
surviving count for any term is **1**, so no term was left at zero and no clause
needed holding back. One link definition — `feedback2`, whose only use was inside the
Revision 2 entry — fell orphaned in the spec and was pruned there; it is a
source-path label rather than a CSV-pinned glossary anchor, so pruning it is safe,
and it is defined here instead.

**Reconciliation against `HEAD` is a separate pass, and it has not run yet.** This
move checked nothing against the tree. The cycle's Slices 2–4 audit the shipped code
against every normative claim in the spec and Slice 5 folds every post-`0.0.13`
correction to the auth surface into it; their findings append to this file as
`**Post-ship:**` bullets under each Decision, plus entries under
[Non-Decision deliberation](#non-decision-deliberation).

## Revision history

Seven revisions produced the contract: an initial draft from the card body, then six
review passes, the last of them a pre-build round graded against scaffolded fail-loud
stubs. The block below is the spec's own, verbatim; its preamble line — which claimed
the history was "kept inline so the spec is self-contained" — was deleted rather than
moved, that claim being exactly what this move made untrue. Each Decision's
`### Changes this Decision underwent` section below reads this history down onto the
Decision it changed.

- **Revision 1** — initial draft authored from the [`WIP-ALPHA-040-0.0.13`][kanban]
  card body via the [`docs/SPECS/NEXT.md`][next] flow (2026-07-01). Pinned: the
  canonical structured filename
  ([Decision 1](#decision-1--spec-filename-and-canonical-naming)); the card-scope
  boundary — session auth only, Channels / websocket auth deferred to the `0.0.14`
  router card, no token / JWT surface, no new `DjangoType` `Meta` key or settings key
  ([Decision 2](#decision-2--card-scope-boundary-session-auth-ships-token-auth-stays-out-no-new-meta--settings-key));
  the four card-named factories at the `django_strawberry_framework.auth` submodule
  path with **no package-root re-export** (opt-in by import, the card's own DoD)
  ([Decision 3](#decision-3--consumer-surface-four-field-factories-at-the-auth-submodule-path-opt-in-by-import-no-root-re-export));
  the `auth/` module + `tests/auth/` mirror
  ([Decision 4](#decision-4--module-and-test-locations-auth-mirroring-the-upstream-trio-testsauth-mirroring-source));
  the login / logout shapes on the frozen envelope with the **anonymous-allowed
  default** as the deliberate, documented inversion of the family's deny-by-default
  ([Decision 5](#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design));
  `register_mutation` riding [`DjangoMutation`][glossary-djangomutation] as a narrow
  `create` over `get_user_model()` with `validate_password` + `set_password` — not a
  fourth flavor
  ([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor));
  `current_user` returning the session actor, nullable, without a
  [`get_queryset`][glossary-get_queryset-visibility-hook] re-run
  ([Decision 7](#decision-7--current_user-returns-the-session-actor-nullable-and-does-not-re-run-get_queryset));
  the user-model primary-[`DjangoType`][glossary-djangotype] requirement validated
  loudly at bind
  ([Decision 8](#decision-8--the-user-models-primary-djangotype-is-required-validated-at-bind));
  the declaration ledger + `bind_auth_mutations()` phase-2.5 bind + the
  [`register_subsystem_clear`][registry] rows
  ([Decision 9](#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows));
  sync + async twin paths
  ([Decision 10](#decision-10--sync--async-session-work-through-one-sync_to_asyncthread_sensitivetrue-boundary));
  the session-transport constraints and the deliberate non-borrow of upstream's
  Channels fallback
  ([Decision 11](#decision-11--transport-contract-classify-first-refuse-a-transport-that-cannot-honour-the-surface-truthfully));
  and **this card owning the `0.0.13` version bump + the joint-cut completion**
  ([Decision 12](#decision-12--this-card-owns-the-0013-version-bump-and-completes-the-joint-cut)).
  Two card-body tensions are carried into
  [Risks and open questions](#risks-and-open-questions) rather than silently
  reconciled (the card's bare symbol list vs the factory-call consumer shape; the
  [`docs/TREE.md`][tree] target layout carrying no `auth/` row for this card), each
  with a preferred reading.
- **Revision 2** — applied a code-review pass ([`docs/feedback2.md`][feedback2];
  every finding re-verified against the package source before editing —
  `run_write_pipeline_sync`'s `decode_step` / `write_step` parameters, the
  hard-wired `_model_decode_step` / `_model_write_step` lambdas in
  `_run_pipeline_sync`, `_resolve_primary_type`'s generic no-DjangoType message,
  and `make_declaration_registry`'s identity dedupe were all confirmed).
  **Foundational (security / shape-setting) fixes:** **(P1)** the register
  password step now has a **named seam** — [`DjangoMutation`][glossary-djangomutation]
  exposes no per-instance write hook and its default create steps would persist
  the **plaintext** password, so `DjangoRegisterMutation` overrides
  `resolve_sync` **and** `resolve_async` and rides the shared
  `run_write_pipeline_sync` skeleton with a password-aware `decode_step` /
  `write_step` pair; the "no new pipeline / foundation unchanged" framing is
  corrected to "reuses the skeleton via a custom step pair," and the
  plaintext-never-persisted test is required on **both** the sync and async paths
  ([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor));
  **(P2)** the user-type bind validation is made **reachable for `register`** —
  `bind_auth_mutations()` now runs **before** `bind_mutations()` in phase 2.5 and
  validates all three user-typed surfaces from the auth ledger with the
  auth-specific message, so the generic `_resolve_primary_type` error (naming
  `DjangoRegisterMutation` and the raw model class) can no longer pre-empt it,
  with a test pinning register's exact error distinct from login's
  ([Decision 8](#decision-8--the-user-models-primary-djangotype-is-required-validated-at-bind)
  / [Decision 9](#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows));
  **(P2)** the cached rider's reload story is pinned — **every**
  `register_mutation()` call re-registers the cached class into the mutation
  ledger (identity-deduped, so a live ledger is a no-op and a cleared one
  re-appends), closing the second-finalize path where `register` would silently
  drop out of the schema, with a finalize → `registry.clear()` → re-declare →
  finalize reload-idempotence test
  ([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)).
  Plus: **(P3)** the consumer `UserType` field selection is cautioned as **the
  authenticated read surface** (exclude `password` and privilege columns; the
  GLOSSARY entry carries the caution)
  ([Decision 8](#decision-8--the-user-models-primary-djangotype-is-required-validated-at-bind));
  and **(P3)** Decision 5 now states plainly that `login` skips **both**
  visibility **and** the optimizer re-fetch (its node is the raw `authenticate()`
  instance, not optimizer-planned — asymmetric with `register`'s G2-planned
  re-fetch, deliberately)
  ([Decision 5](#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design)).
- **Revision 3** — applied a second code-review pass (every finding re-verified against the package source before editing — the
  `registry.py` `_subsystem_clears` phase contract — the finalizer's pre-bind reset
  replays only the `before_bind=True` rows, never a declaration registry — the
  `_bind_mutation` /
  `_synthesized_mutation_signature` payload name derived solely from
  `mutation_cls.__name__` (no payload-name seam), `_validate_permission_classes`'s
  class-local permission storage, `authorize_or_raise`'s
  `mutation_cls().check_permission` + `_primary_type` requirements, and
  `run_write_pipeline_sync`'s `decode_step(instance) -> decoded` /
  `write_step(instance, decoded)` seam signatures were all confirmed).
  **Foundational (lifecycle / seam) fixes:** **(P1, A)** the auth **declaration**
  ledger clear is a **full-clear-only** `register_subsystem_clear` row — registered
  without `before_bind`, so `TypeRegistry.clear()` replays it while the finalizer's
  pre-bind reset (which runs *before* `bind_auth_mutations()` reads the ledger) never
  reaches it — beside the `mutations.declarations` / `forms.declarations` rows; the
  `LoginPayload` / `LogoutPayload` emit ledger rides the existing `mutations.inputs`
  pre-bind row, and the only net-new **pre-bind** row is the
  `current_user` generated-alias namespace (a genuine emit ledger); the bind order
  is pinned exactly (pre-bind reset loop → `bind_auth_mutations()` →
  `bind_mutations()` → `bind_form_mutations()`) and the retry contract restated
  (declarations SURVIVE a re-finalize; emit artifacts are drained and rebuilt)
  ([Decision 9](#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows)).
  **(P1, B)** the synthesized register rider's concrete `__name__` is pinned to
  **`Register`** (module-internal) so the unchanged machinery emits `RegisterPayload`
  (there is **no** payload-name seam — the payload name derives only from
  `mutation_cls.__name__`); the `DjangoRegisterMutation` name is reserved for the
  possible consumer-facing subclassable base follow-on, and Decision 8's generic-error
  wording is corrected to name `Register`
  ([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)
  / [Decision 8](#decision-8--the-user-models-primary-djangotype-is-required-validated-at-bind)).
  **Seam-and-contract fixes:** **(P2, E/F)** the permission enforcement carrier for
  the three non-mutation fields (`login` / `logout` / `current_user`) is **named** —
  a tiny module-internal holder class carrying the duck-typed `_mutation_meta`-shaped
  state (normalized `permission_classes` + the operation string) plus `_primary_type`,
  reusing `DjangoMutation.check_permission` / `authorize_or_raise` /
  `reject_async_in_sync_context` **by call**, with the operation strings (`"login"` /
  `"logout"` / `"current_user"`) and the denial-message shapes pinned, and
  `current_user`'s gate (a query resolver, not `run_write_pipeline_sync`) plus its
  `instance` / anonymous-denial semantics resolved; `DjangoModelPermission`'s
  incompatibility with the model-less auth fields is documented (request-time raise,
  the `DenyAll` precedent), not factory-time guarded
  ([Decision 5](#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design)
  / [Decision 7](#decision-7--current_user-returns-the-session-actor-nullable-and-does-not-re-run-get_queryset)).
  **(P2, G)** the per-field-permission-vs-fixed-payload-name collision is pinned —
  because the fixed `RegisterPayload` / `LoginPayload` / … names cannot serve two
  distinct permission-specialized classes, each auth surface is **one declaration per
  process**: a second call with a *different* `permission_classes` raises a
  [`ConfigurationError`][glossary-configurationerror] (a same-args call returns the
  identity-deduped cached class)
  ([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)).
  **(P3, D)** the register password handoff is made explicit — the `decode_step`
  returns an extended decoded tuple `(user, m2m_assignments, exclude, raw_password)`
  (mirroring `_model_decode_step`'s shape) rather than an implicit closure, with a
  unit assertion the model decode never receives `password` in
  `scalar_and_fk_attrs`
  ([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)).
  **(P3, K)** the "login while already authenticated" edge case is corrected to
  Django's three-branch truth (anonymous→user cycles the session key; a *different*
  user or a session-auth-hash mismatch flushes; a same-user re-login with a matching
  hash keeps the key; `rotate_token` rotates only the CSRF token)
  ([Edge cases][spec-040-edges]). **(P3, L)** the auth test plan
  restates the repo's first-line seed-helper rule (every
  `test_auth_api.py` test opens with `create_users(N)`, even the register /
  anonymous-`me` cases) ([Test plan][spec-040-test-plan]).
- **Revision 4** — applied a third code-review pass (every load-bearing reuse claim re-grounded against the package source before editing
  — `_resolve_primary_type`'s generic no-`DjangoType` raise naming `mutation_cls.__name__`,
  `check_permission` passing `type(self)` as the `has_permission` `mutation` positional,
  and `authorize_or_raise` threading `data` / `instance` straight into the gate were all
  re-confirmed).
  **Foundational (lifecycle) fix:** **(P2, reload)** the register rider now re-records
  into **both** declaration ledgers on **every** factory call — the mutation ledger (for
  binding) **and** the auth ledger (for [Decision 8](#decision-8--the-user-models-primary-djangotype-is-required-validated-at-bind)
  coverage), identity-deduped on both — so after a `registry.clear()` + re-declare the
  register-arm auth-specific error still pre-empts `_resolve_primary_type`'s generic
  message on the second finalize; this closes the path where the auth-ledger record could
  have been written once (behind the cache guard) and left stale, letting the register
  arm silently regress on the reload path the complete-reload fixtures exercise every
  test. The reload-idempotence test is extended to assert the register-arm auth error on
  a post-clear second finalize, not merely `register`'s presence
  ([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)
  / [Decision 8](#decision-8--the-user-models-primary-djangotype-is-required-validated-at-bind)
  / [Test plan][spec-040-test-plan]).
  **Seam-and-contract fixes:** **(P2, composability scope)** Decision 5's
  `DjangoModelPermission` caution is broadened to the general rule — the `mutation`
  positional a custom `has_permission` receives on `login` / `logout` / `current_user`
  is the internal permission holder, **not** a [`DjangoMutation`][glossary-djangomutation]
  (no `Meta.model` / `_resolve_model`), so [Goal 3][spec-040-goals] composability holds for gates
  keyed on `info` / `operation` / `data` but a gate that introspects the mutation object
  raises at request time (documented, the `DenyAll` precedent), with a live test
  ([Decision 5](#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design)).
  **(P3, gate payload)** the `data` / `instance` each field passes into
  `authorize_or_raise` is pinned — `login` passes `data = {"username": username}`
  (never the password) + `instance=None` so an account-scoped rate-limit / lockout gate
  can read the attempted username; `logout` passes `data=None` / `instance=None`;
  `current_user` `data=None` / `instance=<request user | None>`; a live test asserts the
  login gate sees the username
  ([Decision 5](#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design)).
  **(P3, GOAL criterion 4)** Decision 8's caution now states that `get_queryset`
  row-redaction does **not** reach `me` / `login.node` (only field selection governs
  those surfaces — a deliberate, sound carve-out from success-criterion 4), and the
  Out-of-scope FieldSet claim is scoped: field gates compose on `register`'s planned
  node "like any other type," but `login.node` / `me`'s raw, unplanned instances are
  flagged for re-examination when field gates land
  ([Decision 8](#decision-8--the-user-models-primary-djangotype-is-required-validated-at-bind)
  / [Out of scope][spec-040-oos]). Plus a
  [Borrowing posture][spec-040-borrowing] scope note grounding the single-upstream
  parity in the [`GOAL.md`][goal] north-star (the cookbook reference carries no auth
  surface; this card advances the fakeshop target-example direction, adjacent to the
  six-file north-star shape).
- **Revision 5** — applied a fourth code-review pass.
  The one genuinely new finding was **(P1, error keying)**: `validate_password` raises
  a **list-style** `ValidationError` (a bare message list, **no** `error_dict`), and
  the shared `validation_error_to_field_errors` mapper's non-dict branch keys such an
  error to the `"__all__"` sentinel via `field_error("", …)` — **not** `password`
  ([`mutations/resolvers.py`][mutations-resolvers] `::validation_error_to_field_errors`
  #"return [field_error(\"\", list(exc.messages)…)]", re-confirmed against source). So
  the register `write_step` now maps the validator failure to a `password`-keyed
  [`FieldError`][glossary-fielderror-envelope] **directly** at the `validate_password`
  call site (`field_error("password", exc.messages, codes=…)`), never routing it
  through the generic mapper, and the weak-password tests (live + mirrored) assert the
  key is `password`, not `"__all__"`
  ([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)
  / [Edge cases][spec-040-edges] / [Test plan][spec-040-test-plan]). The review's
  other items were verified **already addressed** by Revisions 2–4 and required no
  change: the plaintext-password decode-pop + unit assertion (Rev 2/3,
  [Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)),
  the duck-typed-holder "never introspect the `mutation` object" rule + test (Rev 4,
  [Decision 5](#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design)),
  the declaration-ledger-on-`TypeRegistry.clear()` vs emit-ledger-on-pre-bind split
  (Rev 3, [Decision 9](#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows)),
  the `current_user` bind-materialized lazy alias + its emit-ledger row
  ([Decision 7](#decision-7--current_user-returns-the-session-actor-nullable-and-does-not-re-run-get_queryset)
  / [Decision 9](#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows)),
  the async lazy-user forcing inside the `sync_to_async` boundary
  ([Decision 7](#decision-7--current_user-returns-the-session-actor-nullable-and-does-not-re-run-get_queryset)
  / [Edge cases][spec-040-edges]), and the first-line `create_users(N)`
  seed rule (Rev 3, [Test plan][spec-040-test-plan]).
- **Revision 6** — applied a fifth code-review pass (Round 2; both new findings re-grounded against source before editing).
  **(P2, return-typing mechanism)** the way the custom `login` / `logout` /
  `current_user` factories attach their unresolved-at-class-body-time return types is
  now pinned to the **field family's own signature-injection idiom**:
  [`DjangoMutationField`][glossary-djangomutationfield] builds a per-resolver
  `inspect.Signature` + `__annotations__` with a `strawberry.lazy` `Annotated` return
  ref and assigns them onto its dispatcher (`_resolve.__signature__` /
  `_resolve.__annotations__`, [`mutations/fields.py`][mutations-fields] — re-confirmed),
  so the auth factories do the same; `current_user`'s ref is
  `Optional[Annotated["CurrentUserAlias", strawberry.lazy("…auth.queries")]]` with
  `bind_auth_mutations()` calling the `auth.queries` alias namespace materializer
  (`materialize_current_user_alias("CurrentUserAlias", primary_type)`) → SDL
  `me: UserType`
  ([Decision 7](#decision-7--current_user-returns-the-session-actor-nullable-and-does-not-re-run-get_queryset)
  / [Decision 9](#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows)).
  **(P2, async gate boundary)** Decision 10 now pins that the permission gate runs
  **inside** the `sync_to_async(thread_sensitive=True)` boundary on the async path, not
  before it — decisively for `current_user`, whose gate argument `instance=request.user`
  forces the `SimpleLazyObject` as it is computed (a sync ORM touch that would raise
  `SynchronousOnlyOperation` outside the boundary); the async dispatcher wraps the whole
  gate-then-session block in one sync helper, and the
  [`SyncMisuseError`][glossary-syncmisuseerror] guard still fires inside that sync worker
  ([Decision 10](#decision-10--sync--async-session-work-through-one-sync_to_asyncthread_sensitivetrue-boundary)
  / [Edge cases][spec-040-edges] / [Test plan][spec-040-test-plan]). The Round-2
  review's other points — the Revision-5 error-keying / plaintext-pop / lifecycle-split
  confirmations and the P3 session-rotation "rely on Django's native `auth.login` /
  `auth.logout`" note — were verified **already addressed** (the latter by the
  three-branch [Edge cases][spec-040-edges] entry + the
  [Borrowing posture][spec-040-borrowing] "borrow the session semantics as-is") and
  required no change.
- **Revision 7** — applied the verified pre-build review round
  (every item re-grounded against the scaffolded
  fail-loud stubs — the `auth/mutations.py` / `auth/queries.py` TODO pseudocode,
  [`schema_reload.py`][schema-reload]'s `_PROJECT_APP_SCHEMA_MODULES`, and
  `resolvers.py::_model_decode_step`'s AR-H2 exclude calculation — before
  editing). **Foundational (build-critical) fixes:** **(#1)** the bind is now
  **surface-keyed** — the ledger records which of the four surfaces was declared
  and `bind_auth_mutations()` performs only the work those surfaces need
  (logout-only resolves no user primary; a partial schema emits no orphan sibling
  payloads), resolving the Decision 8 / Decision 9 tension the scaffold's
  unconditional pseudocode exposed, with the logout-only / login-only /
  register-only / current-user-only package tests
  ([Decision 8](#decision-8--the-user-models-primary-djangotype-is-required-validated-at-bind)
  / [Decision 9](#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows)
  / [Test plan][spec-040-test-plan]); **(#2)** the live plan is cut to the **canonical
  AllowAny default surface** — the one-declaration-per-process rule makes gated
  variants of the same fixed-payload field unreachable in the one aggregated
  fakeshop schema, so all permission-gate coverage moves to `tests/auth/`
  isolated throwaway schemas (the documented genuinely-unreachable-live placement,
  not a live-first weakening) ([Test plan][spec-040-test-plan]); **(#3)** Slice 1 adds
  `"apps.accounts.schema"` to [`schema_reload.py`][schema-reload]'s
  `_PROJECT_APP_SCHEMA_MODULES` in the same commit that composes accounts into
  [`config/schema.py`][config-schema] (pre-empting the helper's own documented
  `LazyType` `KeyError` / dropped-surface failure mode), with a live
  reload-preservation test ([Slice checklist][spec-040-slices]); **(#4)** the
  conflict / cache key is pinned to the **schema-affecting declaration args only**
  (the normalized `permission_classes`) — `description` / `deprecation_reason` /
  `directives` are per-field presentation kwargs the shared signature helper
  partitions out, never a false-`ConfigurationError`
  ([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)
  / [Edge cases][spec-040-edges]); **(#5)** Slice 1's checklist /
  DoD no longer reference Slice-2-only surfaces — the register-arm /
  current-user-arm validation coverage moves to Slice 2 while Slice 1 wires the
  bind ordering that keeps those arms reachable
  ([Slice checklist][spec-040-slices] / [Definition of done][spec-040-dod]).
  **Also folded in:** **(#6)** the register exclusion seam must **preserve the
  provided-marker** — the AR-H2 `_unprovided_exclude` still counts `password` as
  provided, so the seam is "extract with marker preserved," never "pop before
  decode," with a helper-level test
  ([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor));
  **(#7)** the "AllowAny" wording is aligned — no `AllowAny` class exists or is
  added; the default is the empty-list semantics via
  `_validate_permission_classes(..., unset_default=())`
  ([Decision 5](#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design));
  **(#8)** the holder `__name__`s are pinned (`Login` / `Session` /
  `CurrentUser`) and the four exact denial strings documented — logout's, whose
  target IS the holder name, reads `"Not authorized to logout Session."`
  ([Decision 5](#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design));
  **(#9)** the register field derivation is factored as the directly-testable
  `derive_register_fields(user_model)` helper with the exact ordering rule,
  delegating rejection to `editable_input_fields` — testable with a test-scoped
  model, no `AUTH_USER_MODEL` swap
  ([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor));
  **(#10)** the `node` / `result` wording is scoped — `node` is the fakeshop
  Relay-backed rendering, `me` carries no slot at all, and tests must not encode
  `node` as the generic contract
  ([User-facing API][spec-040-api] / [Test plan][spec-040-test-plan]); **(#13)** the
  holder / rider same-args cache and conflict state ARE the surface-keyed
  declaration ledger drained by its full-clear-only row — a prior
  conflicting-`permission_classes` raise does not survive a clear, asserted by
  the reload-idempotence test
  ([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)
  / [Decision 9](#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows)).
  The round's **(#11)** (`types/relay.py` strategy resolution) was verified a
  non-issue requiring no spec-040 edit, and **(#12)** (the bare-holder `mutation`
  argument hazard) was verified **already addressed** by Revision 4's Decision 5
  generalization ("key on `info` / `operation` / `data`, never on the mutation
  object") and required no change.

## Decision 1 — Spec filename and canonical naming

Spec: [Decision 1 — Spec filename and canonical naming][spec-040-d1].

### Justification (moved from the spec)

None. This Decision carried no `Justification:` block in the spec.
The absence is the spec's, not this move's — four of the twelve
Decisions state their reasoning inside the Decision body and open
straight into their rejected alternatives.

### Alternatives considered (and rejected)

- **An unstructured `docs/spec-auth_mutations.md`.** Rejected: the structured name
  sorts with its card and version on disk and matches every spec since `spec-020`.

### Changes this Decision underwent

- **Revision 1** pinned the canonical structured filename and the `auth_mutations`
  topic slug over an unstructured `docs/spec-auth_mutations.md`. No later revision
  touched this Decision.
- **Post-ship:** the spec was archived to `docs/SPECS/` and its `-terms.csv` companion
  to `docs/SPECS/appx/`, which is why the Decision body now names both the authoring
  path and the archived one.
- **Post-ship (Slice 2 conformance audit, this cycle):** re-checked against `HEAD` —
  the authoring path, the post-ship archived path, and the
  `spec-<NNN>-<topic>-<X_Y_Z>` naming all still hold. No change.
- **Post-ship (integration pass, this cycle) — the card was named twice, by two
  different ids.** The Decision derived `NNN` from `WIP-ALPHA-040-0.0.13` while the
  spec's own opening line already named the same card `DONE-040-0.0.13`, so one
  document named one card two ways and only one of the two ids resolves on the board
  today. Flipped to the current id — the clean prefix-flip class, the same one
  `## Out of scope`'s `041` / `043` citations took in Slice 4. The derivation itself
  (the number comes from the card) is unchanged, because the card's *number* is what
  is stable and its prefix is what rots.
- **No longer claims:** that the board carries a `WIP-ALPHA-040-0.0.13` card.

## Decision 2 — Card-scope boundary: session auth ships; token auth stays out; no new `Meta` / settings key

Spec: [Decision 2 — Card-scope boundary: session auth ships; token auth stays out; no new `Meta` / settings key][spec-040-d2].

### Justification (moved from the spec)

the card's DoD names exactly the four symbols + tests + the opt-in
doc line; every candidate extension either belongs to an already-scheduled card
(`041` for Channels, `043` for the test client) or has no upstream analog to claim
parity against (token auth, password reset) — and [`START.md`][start]'s
resist-scope-creep rule applies squarely.

### Alternatives considered (and rejected)

- **Fold in the Channels fallback now** (upstream carries it inline). Rejected: the
  package has no Channels surface until `041`; an untestable fallback (no ASGI
  router to exercise it) would ship dead lines against a 100% coverage gate.
- **Ship a `password_change` mutation while here.** Rejected: no upstream analog in
  either reference package (the Alpha parity rule would be satisfied by fabrication),
  and the consumer composes it from [`DjangoMutation`][glossary-djangomutation]
  today.

### Changes this Decision underwent

- **Revision 1** pinned the card-scope boundary — session auth ships, Channels /
  token auth stay out, no new `Meta` or settings key. No later revision touched this
  Decision.
- **Post-ship (Slice 2 conformance audit, this cycle):** the "does not ship
  Channels/websocket auth" half is falsified. `c8346750 feat(auth): harden the session
  lifecycle across transports` added `django_strawberry_framework/auth/sessions.py`, so
  the auth surface now classifies a request into Django HTTP / Channels HTTP / Channels
  WebSocket and answers a per-surface capability question about each. The Decision now
  points at Decision 11 for *which* transports the four fields accept and how an
  unsupported one is rejected, so the transport contract is stated once, in one place;
  the `0.0.14` router card still owns the ASGI-transport story itself. Every other
  clause was re-checked mechanically and holds: no token/JWT or password-change/reset
  flow exists, `types/base.py`'s `ALLOWED_META_KEYS` / `DEFERRED_META_KEYS` carry no
  auth key, and `conf.py` carries no auth settings key.
- **Post-ship (Slice 5 reconciliation, this cycle) — the heading still carried the
  claim the body had already given up.** Slice 2 converted the body's Channels clause
  into a pointer at Decision 11 but left the heading reading "session auth ships;
  Channels / token auth stay out", which is the first thing a reader of the decision
  list sees and now contradicts Decision 11 at a glance. Renamed to "token auth stays
  out", which is the half that is still true; the card-scope framing and every other
  clause are unchanged, and the four in-page anchors plus this file's `[spec-040-d2]`
  definition and mirrored heading moved in the same pass. Decision 11 is the only home
  of a transport answer, heading included.
- **No longer claims:** that the card's auth surface is Channels-agnostic, or that
  websocket auth is wholly outside it.

## Decision 3 — Consumer surface: four field factories at the `auth` submodule path, opt-in by import, no root re-export

Spec: [Decision 3 — Consumer surface: four field factories at the `auth` submodule path, opt-in by import, no root re-export][spec-040-d3].

### Justification (moved from the spec)

the card's DoD is explicit — "Documented as opt-in: consumers must
import explicitly; auth mutations are not injected into every schema." A
submodule-only path makes the opt-in **structural** rather than merely documented,
and the package already has the precedent: the `testing.relay` helpers are
deliberately not re-exported from their parent either ([`docs/GLOSSARY.md`][glossary]
"NOT re-exported from the `testing` root, by design"). The snake_case factory names
are the card's own symbol names, and the factory-call shape mirrors upstream's
consumer surface (`login = auth.login()` upstream ↔ `login = login_mutation()`
here), keeping the migration diff one import line.

### Alternatives considered (and rejected)

- **Root exports (`from django_strawberry_framework import login_mutation`).**
  Rejected: the root `__all__` is the pinned always-available surface; auth is
  opt-in by card mandate, and the root would also eagerly import `auth/` (and
  `django.contrib.auth`) for every consumer, used or not.
- **PascalCase mutation classes the consumer wires through
  [`DjangoMutationField`][glossary-djangomutationfield]
  (`login = DjangoMutationField(LoginMutation)`).** Rejected for `login` / `logout`:
  their argument signatures (`username:` / `password:`; no arguments) do not fit the
  factory's synthesized `data:` / `id:` signatures, so they would need signature
  special-cases inside the shared factory — a worse trade than two self-contained
  field factories. `register` **does** ride
  [`DjangoMutationField`][glossary-djangomutationfield] internally
  ([Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)).
- **A `strawberry_django`-style module of loose resolvers the consumer wraps
  themselves.** Rejected: hands the payload/envelope work back to the consumer —
  the exact boilerplate the card exists to absorb.

### Changes this Decision underwent

- **Revision 1** pinned the four field factories at the `auth` submodule path with
  no package-root re-export. No later revision touched this Decision.
- **Post-ship (Slice 2 conformance audit, this cycle):** re-checked mechanically and
  still true — `django_strawberry_framework/__init__.py` names no auth symbol in
  `__all__`, in its module namespace, or in the PEP 562 lazy-export map its
  `__getattr__` consults, and no package module imports `auth` (the only two greps that
  look like it are a docstring in `utils/sessions.py` and an unrelated
  `auth_aliases_for_permission_classes` import). The finalizer's phase-2.5 bind reaches
  `bind_auth_mutations()` through `utils/imports.py::loaded_attr`, which reads
  `sys.modules` and never imports, so the structural opt-in survives every finalize.
  No change to this Decision.

## Decision 4 — Module and test locations: `auth/` mirroring the upstream trio; `tests/auth/` mirroring source

Spec: [Decision 4 — Module and test locations: `auth/` mirroring the upstream trio; `tests/auth/` mirroring source][spec-040-d4].

### Justification (moved from the spec)

the module split mirrors the upstream trio the card's `Verified in
upstream` section names (`mutations.py` / `queries.py`; upstream's `utils.py`
content — request/user extraction — already exists in this package as
[`utils/permissions.py::request_from_info`][utils-permissions], which the resolvers
reuse rather than re-spelling). The card's DoD names both `django_strawberry_framework/auth/`
and `tests/auth/` verbatim.

### Alternatives considered (and rejected)

- **A single flat `auth.py`.** Rejected: the module carries two distinct surfaces
  (mutations + a query helper) plus a bind; the trio keeps each file one-purpose and
  mirrors the upstream layout a migrant greps for.
- **A set-family layout (`auth/sets.py` / `auth/resolvers.py` / `auth/inputs.py`).**
  Rejected: auth is not a declarative set family — there is no consumer-declared
  class to collect, validate, and expand; forcing the family layout onto four fixed
  factories manufactures indirection.

### Changes this Decision underwent

- **Revision 1** pinned the `auth/` trio (`__init__.py` / `mutations.py` /
  `queries.py`) and the `tests/auth/` mirror. No later revision touched this
  Decision, though Revision 3's holder naming and Revision 6's alias namespace both
  added named contents to those files.
- **Post-ship (Slice 2 conformance audit, this cycle):** the enumeration was
  incomplete against `HEAD`. `c8346750 feat(auth): harden the session lifecycle across
  transports` added a fourth source module, `auth/sessions.py`, and a fourth package
  test module, `tests/auth/test_sessions.py`; both are now listed. The Decision states
  only where the module lives and that it is private — its contract stays Decision
  11's — so the two cannot drift apart.
- **No longer claims:** that `auth/` is exactly the three-module trio, or that
  `tests/auth/` is exactly `test_mutations.py` + `test_queries.py`.

## Decision 5 — `login` / `logout`: session mutations on the frozen envelope, anonymous-allowed by design

Spec: [Decision 5 — `login` / `logout`: session mutations on the frozen envelope, anonymous-allowed by design][spec-040-d5].

### Justification (moved from the spec)

the envelope transport (rather than upstream's raised
`ValidationError`) is the [Cross-subsystem
invariants][glossary-cross-subsystem-invariants] requirement — "the `FieldError`
envelope is shared across every mutation flavor for a consistent client contract";
a client already handling `{ node, errors }` from every write handles a failed
login with zero new code paths.

### Alternatives considered (and rejected)

- **Raise `GraphQLError` on bad credentials (upstream's shape).** Rejected: a wrong
  password is an *expected* outcome, and the package's contract routes expected
  write outcomes through the envelope; top-level errors are reserved for
  authorization denials and malformed requests.
- **A `data: LoginInput!` argument for family consistency.** Rejected: the
  generated-input machinery exists to derive shapes from models/forms/serializers;
  a fixed two-credential signature derives from nothing, and flat arguments match
  both upstream and the plain GraphQL ergonomics of the most-called mutation in any
  schema.
- **Distinguish "no such user" from "wrong password".** Rejected: an
  account-enumeration oracle; upstream, Django's own `AuthenticationForm`, and this
  spec all deliberately refuse.
- **Return the user from `logout` (symmetry with `login`).** Rejected: upstream
  returns a bool; the session is gone and the only useful fact is whether one
  existed. `{ ok, errors }` carries exactly that.
- **Default `permission_classes` to the family's deny.** Rejected as a
  contradiction: nobody could ever log in. The inversion is explicit, single-sited
  in the factories, and documented in the GLOSSARY entry.

### Changes this Decision underwent

- **Revision 1** pinned the `login` / `logout` shapes on the frozen envelope and the
  anonymous-allowed default as the deliberate, documented inversion of the family's
  deny-by-default.
- **Revision 2** stated plainly that `login` skips **both** visibility **and** the
  optimizer re-fetch — its node is the raw `authenticate()` instance, asymmetric with
  `register`'s G2-planned re-fetch.
- **Revision 3** named the permission carrier: a module-internal holder class
  carrying the duck-typed `_mutation_meta` shape plus `_primary_type`, reusing
  `check_permission` / `authorize_or_raise` / `reject_async_in_sync_context` by call,
  with the operation strings and denial-message shapes pinned, and
  `DjangoModelPermission`'s incompatibility documented as a request-time raise rather
  than a factory-time guard.
- **Revision 4** broadened that incompatibility to the general rule — the `mutation`
  positional a custom `has_permission` receives on the three model-less fields is the
  holder, not a [`DjangoMutation`][glossary-djangomutation], so a gate must key on
  `info` / `operation` / `data` and never on the mutation object — and pinned the
  per-field gate payload (`login` passes `data = {"username": username}`, never the
  password).
- **Revision 5** re-verified the duck-typed-holder rule and its test as already
  addressed; no change.
- **Revision 7** aligned the "AllowAny" wording and pinned the holder `__name__`s
  (`Login` / `Session` / `CurrentUser`) with the four exact denial strings.
- **Post-ship (Slice 2 conformance audit, this cycle) — the permission holder's
  signature.** The Decision named the single-sited helper
  `_make_permission_holder(operation, primary_type, permission_classes)`. What shipped
  in `fa704722 Finish spec-040` takes `(operation, holder_name, permission_classes)`:
  the holder `__name__` is the genuine per-field input (Revision 7 pinned `Login` /
  `Session` / `CurrentUser` as test-asserted denial-string contracts), while
  `_primary_type` cannot be a constructor argument at all, because the user primary is
  unresolved at class-body time and is assigned by `bind_auth_mutations()`. The
  Decision now states the shipped signature and where `_primary_type` comes from.
- **Post-ship (Slice 2 conformance audit, this cycle) — the holder is sealed.**
  `a8f31a2d fix: harden framework boundaries and validation` sealed both halves of the
  holder's authorization state: `_AuthMutationMetaSnapshot` refuses attribute rebinding
  and deletion after `__init__`, and `_SealedAuthHolderMeta` refuses rebinding or
  deleting the holder class's `_mutation_meta` head. The reason is this Decision's own
  contract — a custom `has_permission` receives the holder class itself, so an unsealed
  slot let one request's hook replace the validated permission set for every later
  request on that surface. The Decision now states the sealing; without it the spec
  described a mutable carrier the code refuses to be.
- **Post-ship (Slice 2 conformance audit, this cycle) — the storability preflight.**
  `a6f5a6cb fix(auth): reject unencodable credentials` added a preflight between the
  gate and `authenticate`: a non-UTF-8-encodable `username` or `password` (a lone
  surrogate) would otherwise crash `authenticate` into a raw `UnicodeEncodeError` from
  the `USERNAME_FIELD` lookup or the hasher's `.encode()`. It short-circuits to the
  byte-identical undifferentiated envelope through the same shared
  `unencodable_text_error` primitive the write side uses, so the preflight is not an
  enumeration oracle of its own. Added as resolver step 3 and as an `### Error shapes`
  row.
- **Post-ship (Slice 2 conformance audit, this cycle) — `logout`'s `ok`.**
  `c537b2dc refactor(auth): single-source authenticated actor classification` replaced
  the Decision's `ok = user.is_authenticated` with the ONE shared
  `_authenticated_actor_or_none` anonymity definition `current_user`'s nullable return
  also derives from, so a request with no `user` attribute at all classifies as
  anonymous rather than raising, and the two fields cannot drift. `44b33e9f fix(auth):
  enhance logout handling for anonymous requests and session flushing` pinned the
  payload-before-mutation ordering the Decision now states.
- **Post-ship (Slice 2 conformance audit, this cycle) — the transport prologue.**
  `c8346750` made both resolvers open with a transport prologue that runs *before* the
  gate. The numbered steps now say so and point at Decision 11 rather than restating
  it; the prologue's own contract is Slice 5's to write, once.
- **No longer claims:** that an `AllowAny` class exists or is added. Revision 7
  retracted that reading — "AllowAny" is shorthand for the empty-list semantics
  produced by `_validate_permission_classes(..., unset_default=())`, and the
  implementation must not mint such a primitive.
- **Post-ship (Slice 5 reconciliation, this cycle) — step 5's anonymity enumeration
  spelled one transport.** It named "a request with no `user` attribute at all
  (`SessionMiddleware` without `AuthenticationMiddleware`)" and "a request whose `user`
  is unauthenticated", which between them do not cover the Channels shape: the
  adapter always *has* a `user` property and returns `None` from it when the scope
  carries no middleware-loaded user, so neither listed arm describes it even though
  `_authenticated_actor_or_none` has classified it as anonymous since `c537b2dc`.
  Decision 7's twin sentence already named both shapes after Slice 3's edit, so the two
  Decisions disagreed about one classification they explicitly share. Step 5 now names
  the adapter shape as well. A cross-slice correction into a decision Slice 2 closed,
  recorded here rather than left as an invisible overwrite.
- **No longer claims:** that authorization is the first thing either resolver does, or
  that the holder's validated permission set can be rebound after declaration.

## Decision 6 — `register_mutation()` rides `DjangoMutation`: a narrow `create` over `get_user_model()` with password hashing — NOT a fourth flavor

Spec: [Decision 6 — `register_mutation()` rides `DjangoMutation`: a narrow `create` over `get_user_model()` with password hashing — NOT a fourth flavor][spec-040-d6].

### Justification (moved from the spec)

the three-flavor DRY review is the
standing warning — "every new write flavor re-spells the same ~8 pieces of glue."
The register flavor dodges the *kit* by being a rider: no new converter (the
model-column converter covers `AbstractBaseUser` columns), no new input generator
(standard `Meta.fields` narrowing), no new orchestration (the shared skeleton) —
only the one step pair the password work genuinely requires. This is also the
upstream shape verbatim — `DjangoRegisterMutation(DjangoCreateMutation)` overriding
the create step with `validate_password` + a `set_password` pre-save hook — adapted
to the package's seams, plus the validator-gets-the-user improvement noted in
[Borrowing posture][spec-040-borrowing].

### Alternatives considered (and rejected)

- **A consumer-facing subclassable base instead of a factory** (`class MyRegister(
  DjangoRegisterMutation): class Meta: ...`, where `DjangoRegisterMutation` is the
  reserved public base — distinct from the internal `Register` concrete class).
  Rejected for `0.0.13`: the card names
  the factory symbol, the no-argument default covers the parity case, and a naive
  consumer-declared `DjangoMutation` over the user model is a *plaintext-password
  foot-gun* (the generated create would store `password` verbatim — the exact
  default-pipeline behavior the rider's step pair exists to prevent) — the factory
  keeps the safe path the obvious path. A customization surface is a recorded
  follow-on ([Risks](#risks-and-open-questions)).
- **A `pre_save` / per-instance write hook added to the `036` base instead of the
  resolver-seam override.** Rejected: widening the frozen
  [`DjangoMutation`][glossary-djangomutation] base for one internal consumer
  re-opens a shipped contract; the per-flavor `resolve_sync` / `resolve_async`
  seam plus `run_write_pipeline_sync`'s `decode_step` / `write_step` parameters
  exist for exactly this, and the form / serializer flavors already prove the
  shape. (A public write hook, if consumer demand materializes, is its own card.)
- **Include `email` unconditionally.** Rejected: `REQUIRED_FIELDS` already includes
  it for the default user model; hardcoding it would break custom user models that
  deliberately omit it. The `(USERNAME_FIELD, *REQUIRED_FIELDS, "password")` set is
  model-derived, not assumed.
- **The narrowed-shape deterministic input name.** Rejected: `RegisterInput` is the
  consumer-facing SDL contract a migrant expects; the deterministic
  `UserEmailPasswordUsernameInput` name is collision-proof but reads like generated
  debris. The name seams exist precisely for flavors to pin friendlier names
  ([`spec-038`][spec-038]'s `<FormClass>Input` precedent); the materialize ledger's
  distinct-shape collision raise still guards a consumer's own `RegisterInput`.
- **Validate the password with no user context (upstream's call).** Rejected:
  `validate_password(password, user)` with the constructed instance lets
  `UserAttributeSimilarityValidator` reject `password == username` — strictly better
  validation for one argument.

### Changes this Decision underwent

- **Revision 1** pinned `register_mutation()` as a narrow `create` rider over
  `get_user_model()` with `validate_password` + `set_password` — not a fourth flavor.
- **Revision 2** gave the password step a named seam: the rider overrides
  `resolve_sync` **and** `resolve_async` and rides `run_write_pipeline_sync` with a
  password-aware `decode_step` / `write_step` pair, because the `036` create pipeline
  exposes no per-instance write hook and its default steps would persist the
  plaintext. The same revision pinned the every-call re-register into the mutation
  ledger.
- **Revision 3** pinned the synthesized rider's `__name__` to `Register` (so the
  unchanged machinery emits `RegisterPayload` — there is no payload-name seam), made
  each auth surface one declaration per process with a
  [`ConfigurationError`][glossary-configurationerror] on a conflicting
  `permission_classes`, and made the password handoff an explicit decoded tuple
  `(user, m2m_assignments, exclude, raw_password)` rather than an implicit closure.
- **Revision 4** extended the every-call re-record to **both** ledgers — the mutation
  ledger for binding and the auth ledger for Decision 8's coverage — closing the path
  where the auth-ledger record was written once behind the cache guard and left stale.
- **Revision 5** corrected the error keying: `validate_password` raises a list-style
  `ValidationError` with no `error_dict`, and the shared
  `validation_error_to_field_errors` mapper keys such an error to the `"__all__"`
  sentinel, so the write step builds the `password`-keyed leaf itself at the
  `validate_password` call site.
- **Revision 7** pinned the conflict / cache key to the schema-affecting declaration
  args only, required the exclusion seam to **preserve the provided-marker**, factored
  the field derivation into the directly-testable `derive_register_fields(user_model)`
  helper, and made the declaration ledger itself the holder / rider cache and conflict
  state so a `registry.clear()` drains it.
- **Post-ship (Slice 3 conformance audit, this cycle) — privilege columns are now
  policy-checked as well as structural.** The Decision claimed privilege escalation was
  "structurally unreachable, **not** policy-checked". That held only because the
  derivation reads the *stock* user model: `derive_register_fields` takes the model as
  an argument precisely so a custom one can be used, and a custom model listing
  `is_staff` (or any of the other four) in `REQUIRED_FIELDS` would have made the column
  client-selectable on a public registration surface. `a40f0d33 Harden auth
  registration and deployment guidance` closed that with an explicit
  `_REGISTER_PROTECTED_FIELDS` intersection raising a `ConfigurationError` naming the
  offending field(s) and the model. The Decision now states both layers, and `is_active`
  is inside the protected set rather than only in the narration.
- **Post-ship (Slice 3 conformance audit, this cycle) — the exclusion seam became a
  field kind.** The Decision specified the seam as "an `excluded_input_fields`
  parameter threaded through the existing `_model_decode_step` into
  `_decode_relations`", which is what shipped. `31625ac7 refactor(mutations): ride the
  shared decode spine in the model write flavor` moved the model flavor onto the same
  `decode_provided_fields` spine the form and serializer flavors already rode, and the
  per-request parameter became a bind-time `EXCLUDED` kind on the stashed
  `InputFieldSpec` records (`mutation_input_field_specs(…, excluded_attrs=…)`), routed
  by a handler beside the scalar / FK / M2M handlers. Both invariants the Decision
  cared about survived intact and are what the rewritten text pins: ONE shared walk
  rather than a fork, and the provided-marker preserved. The refactor also added a
  guard the Decision never asked for — `_model_write_step` unpacks the three-tuple
  strictly, so an `EXCLUDED` spec introduced without a paired flavor write step raises
  instead of silently discarding the captured value.
- **Post-ship (Slice 3 conformance audit, this cycle) — the write step gained a
  password preflight.** The Decision's "`validate_password` + `set_password` are the
  ONLY auth-specific steps" was falsified by the seam's own consequence: routing
  `password` around the shared decode also routes it around that decode's scalar
  checks. `a6f5a6cb fix(auth): reject unencodable credentials` added the storability
  preflight (a lone surrogate passes every configured validator, then crashes the
  hasher's `.encode()` into a top-level `UnicodeEncodeError`) and `a8f31a2d fix: harden
  framework boundaries and validation` added the absent-value and non-`str` guards.
  All three return the `password`-keyed envelope and reuse the shared leaf
  constructors, so the Decision's actual point — no auth-specific error *handling* —
  is unchanged; the sentence counting the steps was not.
- **Post-ship (Slice 3 conformance audit, this cycle) — `_bind_mutation` was
  renamed.** The Decision named `_bind_mutation` as the caller of
  `build_payload_type(mutation_cls.__name__, …)`. `ab821ae0 refactor: single-site the
  duplicated class-label, bind, and fetch seams` split that function into the shared
  `bind_write_declarations` drain plus the `bind_mutation_outputs` payload half, which
  both write-declaration ledgers now ride; the no-payload-name-seam contract the
  Decision rests on is untouched, and the Decision now names the surviving symbol.
- **Post-ship (Slice 6 final verification, this cycle) — the Decision carried `D-N3`'s
  retired reason clause at its own parallel site.** Slice 4 corrected `D-N3` because
  "the narrowed `Meta.fields` has no relation inputs" contradicts the **Custom user
  models** edge case, but the same proposition was live in this Decision's own body
  ("Because the narrowed set has **no relation inputs** … they return for free via the
  inherited decode **only if** a consumer ever widens `Meta.fields`"), where Slice 3's
  audit had graded only the normative half (`D6.10`) and never the reason. A custom
  model may place a forward FK in `REQUIRED_FIELDS` —
  `django_strawberry_framework/auth/mutations.py::derive_register_fields` rejects only
  the five protected names — so that entry takes the standard `<field>_id` input with
  no widening at all. The Decision now scopes the reason to the **stock** user model and
  states that whatever relation handling a narrowed set needs comes for free via the
  inherited decode, matching `D-N3` and the edge case. Surfaced by the code comment
  `D-N3` now carries: one spelling fixed while a parallel site stayed live is what
  reopens a cycle.
- **No longer claims:** that the register rider adds "no new pipeline" and leaves the
  foundation wholly unchanged (Revision 2 corrected this to "reuses the skeleton via a
  custom step pair"); that the concrete registered class is named
  `DjangoRegisterMutation` (Revision 3 pinned it to `Register` and reserved the older
  name for a possible consumer-facing base); and that the seam may simply pop
  `password` before the decode walk (Revision 7 showed that marks the column
  unprovided and drops it from `full_clean`).
- **No longer claims:** that privilege escalation is unreachable by structure alone
  and needs no policy check; that the exclusion seam is a per-request
  `excluded_input_fields` parameter; that the write step's only auth-specific work is
  `validate_password` + `set_password`; that a helper partitions the factory kwargs
  into three classes (each factory's own keyword-only signature does, and the shared
  signature builder only ever sees the GraphQL-argument class — this was inaccurate on
  its own date, not drift); or that `_bind_mutation` is the symbol that mints the
  payload name.
- **No longer claims:** that the narrowed register field set has no relation inputs
  unconditionally, or that the inherited decode's relation handling is reached only by
  a consumer widening `Meta.fields` — both are true of the stock user model and false
  of a custom model whose `REQUIRED_FIELDS` names a forward FK.

## Decision 7 — `current_user()` returns the session actor, nullable, and does not re-run `get_queryset`

Spec: [Decision 7 — `current_user()` returns the session actor, nullable, and does not re-run `get_queryset`][spec-040-d7].

### Justification (moved from the spec)

**Nullable, not raising:** upstream raises `ValidationError("User is
not logged in.")`; this package's read posture is nullable-by-contract
(`node(id:)` returns `null` for hidden/missing; the file/image output object is
null-by-default) — an anonymous session is an expected state, not an error, and a
nullable `me` is the shape every GraphQL client library expects to branch on.
**Skipping visibility:** `get_queryset` scopes *lookups of other
rows*; `me` is the actor themselves. A directory-shaped hook ("non-staff see only
public profiles") must not make `me` return `null` for a logged-in user — that
breaks the one query every authenticated SPA fires first. The same
actor-not-lookup reasoning already governs the `036` re-fetch exception and
Decision 5's login payload; this spec makes it uniform across the three
actor-returning surfaces.

### Alternatives considered (and rejected)

- **Raise on anonymous (upstream's shape).** Rejected: expected state ≠ error; the
  nullable contract is the package's standing read posture.
- **Run the type's `get_queryset` over a `pk=user.pk` queryset.** Rejected: hides
  the actor from themselves under directory-shaped visibility hooks, and costs a
  query to re-fetch a row the middleware already loaded.
- **A `viewer`-style wrapper type.** Rejected: nothing to carry beyond the user;
  the consumer can compose their own wrapper trivially.

### Changes this Decision underwent

- **Revision 1** pinned `current_user()` as the nullable session-actor read with no
  [`get_queryset`][glossary-get_queryset-visibility-hook] re-run.
- **Revision 3** resolved the query-surface gate: `current_user` runs
  `authorize_or_raise` first with `data=None` and `instance=<request user | None>`, so
  a denial is a `GraphQLError` while allowed-but-anonymous is `null` — two distinct
  axes.
- **Revision 5** re-verified the bind-materialized lazy alias and the async lazy-user
  forcing as already addressed; no change.
- **Revision 6** pinned the return-typing mechanism to the field family's own
  signature-injection idiom (`_resolve.__signature__` / `__annotations__` with a
  `strawberry.lazy` `Annotated` return ref built by the shared `_lazy_ref` helper) and
  gave the `CurrentUserAlias` slot to a `make_input_namespace` trio rather than a
  hand-rolled `setattr` / `delattr` pair.
- **Post-ship (Slice 3 conformance audit, this cycle) — the nullable return is now a
  shared classification, not an inline `is_authenticated` read.** The Decision returned
  the actor "when `user.is_authenticated`" and `null` "otherwise (anonymous / no
  session)", which described an inline two-line read and left three shapes unstated.
  `3120dc5a fix(auth): handle absent request user gracefully in current user resolver`
  made a request with no `user` attribute read `null` instead of raising;
  `c537b2dc refactor(auth): single-source authenticated actor classification` moved the
  rule into the ONE `_authenticated_actor_or_none` definition `logout`'s `ok` also
  derives from, so the two fields cannot drift; and the hostile-state containment
  (`6873dac6 fix(auth): fail closed on a hostile authentication state`, extended by
  `a8f31a2d fix: harden framework boundaries and validation` to the truthiness read)
  made a raising `user` descriptor, `is_authenticated` read, legacy callable, or
  truthiness collapse to `null` rather than escape. The direction matters and the
  Decision now states it: hostile collapses to anonymous, never to authenticated, and
  any other exception still propagates so a store outage is not disguised as an
  anonymous read.
- **Post-ship (Slice 3 conformance audit, this cycle) — what the ONE field helper
  actually single-sites.** The Decision said "the whole resolve-request → gate →
  session-work → inject-signature dispatcher is single-sited in ONE auth
  field-construction helper". That was never true, on its own date included:
  `_make_auth_field` has always owned the dispatch seam and the signature injection
  while request resolution, the gate and the session work lived in the per-surface
  `resolve_body` it is handed. `c8346750 feat(auth): harden the session lifecycle
  across transports` widened the gap by splitting that one body into a real sync body
  and a real async body, which is exactly the per-transport specialization point the
  seam exists to provide. The Decision now names the two halves separately rather than
  claiming one helper contains both.
- **Post-ship (Slice 5 reconciliation, this cycle) — the no-queryset-work clause named
  one transport's loader.** "The returned object is `request.user`, already loaded by
  `AuthenticationMiddleware`" is the Django HTTP spelling of a claim whose point is that
  the resolver performs no queryset work at all. Over a Channels scope the actor is the
  `AuthMiddlewareStack`-populated scope user reached through the same
  `request_from_info` contract, and `auth/queries.py` has no transport branch of any
  kind — which is precisely what makes `current_user` transport-neutral in Decision 11's
  table. The clause now names the invariant (the transport's own middleware already
  loaded the actor) and both spellings under it. A cross-slice correction into a
  decision Slice 3 closed, recorded rather than overwritten silently.
- **No longer claims:** that `current_user`'s anonymity rule is an inline
  `user.is_authenticated` read owned by this field, that one helper contains the
  request resolution, the gate and the session work as well as the dispatch and
  signature injection, or that the actor it returns is always `request.user`.

## Decision 8 — The user model's primary `DjangoType` is required, validated at bind

Spec: [Decision 8 — The user model's primary `DjangoType` is required, validated at bind][spec-040-d8].

### Justification (moved from the spec)

resolving through the registry is what every flavor does with its
payload type; a package-provided fallback `UserType` would pick a field selection
(privacy surface!) on the consumer's behalf — the wrong side of the "no silent
schema decisions" line. Failing at bind (not at first query) is the
materialize-before-`Schema` discipline: a missing type is a configuration error,
and configuration errors surface at finalization, loudly, with a named fix.

### Alternatives considered (and rejected)

- **Ship a minimal package `UserType` fallback.** Rejected: the package would be
  choosing which user columns a schema exposes — a security-adjacent default no
  library should pick silently. (A documented optional helper could be a follow-on
  if consumers ask.)
- **Type the user surface as an opaque `JSON` / generic object when no type is
  registered.** Rejected outright: "a system that silently weakens rich relations
  into generic placeholders" is a named [`GOAL.md`][goal] non-goal.
- **Scope the auth-specific validation to `login` / `current_user` and let
  `register` surface the generic `bind_mutations()` error.** Rejected: the three
  user-typed surfaces should fail uniformly, and the generic message names the
  internal rider class and the raw model class without the
  `get_user_model()` / `Meta.primary` recourse — worse exactly for the consumer
  most likely to hit it (one who wired auth first, types second).
- **Police the consumer's `UserType` selection (reject `password` in
  `Meta.fields` when auth is bound).** Rejected: the type may serve non-auth,
  legitimately privileged surfaces; a hard reject would make the auth import
  change the validity of an unrelated declaration. The caution is documentation,
  like the `038` file-clearing scope note.

### Changes this Decision underwent

- **Revision 1** pinned the user model's primary [`DjangoType`][glossary-djangotype]
  as required, validated loudly at bind.
- **Revision 2** made the validation reachable for `register` by ordering
  `bind_auth_mutations()` before `bind_mutations()`, and added the caution that the
  consumer's `UserType` field selection IS the authenticated read surface.
- **Revision 3** corrected the generic-error wording to name the synthesized
  `Register` class.
- **Revision 4** closed the reload path (the auth-ledger every-call re-record keeps the
  register arm alive on a second finalize) and added the asymmetry note: a
  `UserType.get_queryset` written to row-redact gives no protection on `me` /
  `login.node`, a deliberate carve-out from the [`GOAL.md`][goal] success criterion
  that reads and writes share one hook.
- **Revision 7** made the logout exemption **structural** rather than a message branch
  by keying the bind on the declared surfaces, and moved the register-arm /
  current-user-arm coverage to Slice 2, where those factories exist.
- **No longer claims:** that the generic `_resolve_primary_type` message names
  `DjangoRegisterMutation` (Revision 3), or that `logout` is exempted by a branch in
  the validation rather than by never being asked for a user primary at all
  (Revision 7).
- **Post-ship (Slice 3 conformance audit, this cycle):** re-checked against `HEAD` —
  every claim still holds and no edit was made. The shared-getter reuse
  (`registry.get`, with `registry.types_for` consulted only to split the two messages),
  the surface-keyed structural exemption for a logout-only ledger, the
  bind-before-`bind_mutations()` ordering that keeps the register arm reachable, the
  distinct register / login / current-user arm messages on both the first and a
  post-reload second finalize, and the read-surface caution (including its
  `get_queryset`-does-not-reach-`me`/`login.node` asymmetry, carried in the
  [`docs/GLOSSARY.md`][glossary] entry as the Decision says) were each settled against
  source and tests. Recorded because a measured no-change and an unexamined one read
  identically otherwise.
- **Post-ship (integration pass, this cycle) — the read-surface caution opened on a
  retracted premise, and the ordering argument carried a chronology.** Two one-clause
  corrections, neither touching the Decision's contract. (a) The caution's lead-in read
  "the register input side is safe by construction (privilege columns structurally
  unreachable, Decision 6)" — the unqualified proposition Slice 3 retired from
  Decision 6 itself, restated at a second home. It now says the account-control columns
  are kept off the generated input by Decision 6's **two** layers, which is what the
  pointer resolves to. (b) The bind-ordering paragraph attributed the wrong order to
  "an earlier draft", a chronology attribution of the class Slice 1 removed 38 of,
  spelled in a vocabulary that sweep could not see; the counterfactual reasoning it
  introduces is implementation-relevant and stays, the attribution does not.
- **No longer claims:** that account-control columns are unreachable by structure
  alone, or that the bind ordering has a draft history worth recording in the spec.

## Decision 9 — Bind lifecycle: a declaration ledger + `bind_auth_mutations()` at phase 2.5 + registered clear rows

Spec: [Decision 9 — Bind lifecycle: a declaration ledger + `bind_auth_mutations()` at phase 2.5 + registered clear rows][spec-040-d9].

### Justification (moved from the spec)

this is the established lifecycle split for every generated-at-bind
surface (mutation inputs / payloads, filter / order inputs, relation connections) —
declaration registries clear on `TypeRegistry.clear()`, emit ledgers clear pre-bind.
Inventing a second lifecycle for auth would be gratuitous divergence, and giving
the declaration ledger `before_bind=True` breaks both the first finalize
(declarations drained before the auth bind) and the recover-in-place retry.
Payload materialization reuses the single builder + emit ledger so name collisions
(a consumer's own `Login` mutation class also emitting `LoginPayload`) hit the
standard distinct-shape collision raise rather than a silent overwrite
([Edge cases][spec-040-edges]).

### Alternatives considered (and rejected)

- **Materialize both fixed payloads whenever any auth declaration exists** (the
  scaffold's first bind pseudocode, guarding only `current_user`). Rejected on the
  Revision-7 surface-keyed finding: it breaks the logout-only exemption (a
  logout-only schema would resolve — and raise on — `get_user_model()`'s missing
  primary), and it emits orphan payloads for partial schemas (a register-only
  schema would still materialize `LoginPayload`, colliding with a consumer's own
  distinct-shape `LoginPayload`). It was also an internal spec tension — Decision 8
  exempted logout while this Decision read as unconditional — resolved by keying
  the ledger and the bind on the declared surfaces.
- **Register the auth declaration ledger with `before_bind=True`** (the
  Revision-2 draft). Rejected on the P1 finding: those rows are drained by the
  pre-bind reset loop *before* `bind_auth_mutations()` runs, so the auth
  declarations would be gone before the bind reads them (breaking the first
  finalize); moving the bind ahead of the reset instead would let the reset wipe the
  `mutations.inputs` emit ledger after `LoginPayload` materialized, silently voiding
  the distinct-shape collision guard and the retry contract. The declaration-clear
  is a full-clear-only row, matching the mutation / form flavors.
- **Resolve types eagerly at factory-call time.** Rejected: breaks definition-order
  independence — the factory would demand the user type be declared first, the
  exact constraint `finalize_django_types()` exists to remove.
- **A dedicated auth payload namespace.** Rejected: `build_payload_type` already
  owns payload materialization + collision policy in one ledger; a second namespace
  forks the collision story.

### Changes this Decision underwent

- **Revision 1** pinned the declaration ledger, the phase-2.5
  `bind_auth_mutations()`, and the [`register_subsystem_clear`][registry] rows.
- **Revision 2** ordered `bind_auth_mutations()` before `bind_mutations()` so
  Decision 8's auth-specific message cannot be pre-empted.
- **Revision 3** split the two clear lifecycles exactly: the auth **declaration**
  ledger is a full-clear-only row (no `before_bind`), the `LoginPayload` /
  `LogoutPayload` emit artifacts ride the existing `mutations.inputs` pre-bind row,
  and the only net-new pre-bind row is the `current_user` generated-alias namespace.
  It also pinned the bind order end to end and restated the retry contract.
- **Revision 5** re-verified the declaration-vs-emit split and the alias row as
  already addressed; no change.
- **Revision 6** pinned that the bind calls the `auth.queries` alias namespace
  materializer.
- **Revision 7** made the bind **surface-keyed** — each artifact materialized only
  when its surface was declared — and made the declaration ledger the holder / rider
  cache and conflict state.
- **Post-ship (Slice 2 conformance audit, this cycle):** the two clear lifecycles were
  re-derived against `HEAD` and both hold exactly as written — the auth declaration
  ledger's row is `register_subsystem_clear(clear_auth_mutation_registry,
  owner="auth.declarations")` with no `before_bind`, while the `CurrentUserAlias`
  namespace's row in `auth/queries.py` carries `before_bind=True`. So does the pinned
  phase-2.5 order (pre-bind reset -> `bind_auth_mutations()` -> `bind_mutations()` ->
  `bind_form_mutations()`) and the surface-keyed bind's four arms.
- **Post-ship (Slice 2 conformance audit, this cycle) — the opt-in-preserving lookup.**
  The Decision was silent on *how* the finalizer reaches the bind, and the silence was
  load-bearing: the obvious reading (the function-local import every sibling binder
  uses, and the shape the finalizer used at ship) would load `auth/mutations.py` — and
  through it `django.contrib.auth` — in every process that finalizes, which silently
  converts Decision 3's structural opt-in into an unconditional import. What ships is
  `utils/imports.py::loaded_attr`, an already-loaded-only lookup that never imports on
  a consumer's behalf. The Decision now states it, and why.
- **No longer claims:** that the auth declaration ledger may carry `before_bind=True`
  (Revision 3 showed the pre-bind reset would drain it before the bind reads it), or
  that both fixed payloads materialize whenever any auth declaration exists
  (Revision 7 showed that breaks the logout-only exemption and emits orphan payloads
  for partial schemas).

## Decision 10 — Sync + async: session work through one `sync_to_async(thread_sensitive=True)` boundary

Spec: [Decision 10 — Sync + async: session work through one `sync_to_async(thread_sensitive=True)` boundary][spec-040-d10].

### Justification (moved from the spec)

None. This Decision carried no `Justification:` block in the spec.
The absence is the spec's, not this move's — four of the twelve
Decisions state their reasoning inside the Decision body and open
straight into their rejected alternatives.

### Alternatives considered (and rejected)

- **Native-async auth via Django's `aauthenticate` / `alogin`** (Django ≥ 5.0).
  Rejected for `0.0.13`: the package's write family standardized on the one
  `sync_to_async` boundary; adopting the native-async auth APIs is a
  family-wide decision (it would apply equally to `036`'s pipeline) and belongs to
  a dedicated async card, not a divergence smuggled in here. Recorded in
  [Risks](#risks-and-open-questions).

### Changes this Decision underwent

- **Revision 1** pinned the sync + async pair with the session work behind one
  `sync_to_async(thread_sensitive=True)` boundary.
- **Revision 6** moved the permission gate **inside** that boundary, decisively for
  `current_user`, whose `instance=request.user` gate argument forces the
  `SimpleLazyObject` as it is computed.
- **Post-ship (during the `0.0.13` build):** the optional `run_in_one_sync_boundary`
  factoring this Decision offered as a P3 follow-on WAS taken — the generic
  `run_in_one_sync_boundary(fn, *args, **kwargs)` primitive landed in
  [`mutations/resolvers.py`][mutations-resolvers], `run_pipeline_async` rides it as its
  boundary core with the pinned `036` AR-M4 wording undisturbed, and the auth async
  paths share it rather than an auth-local copy. The `TODO(spec-040 Slice 1)` anchor at
  `::run_pipeline_async` that invited the factoring was discharged in the same change.
- **Rationale extraction (this cycle's Slice 1):** the spec carried that outcome as a
  `**Build note (Worker 1):**` amendment block sitting after a sentence that still
  offered the factoring as something a follow-on **may** do. The Decision now states
  the shipped shape directly and the chronology is the bullet above; the
  `## Helper-reuse obligations (DRY)` `D17 / P3` item, which still called the primitive
  "an optional follow-on", was corrected in the same pass so the two agree.
- **Post-ship (Slice 2 conformance audit, this cycle) — the primitive moved.**
  `5e0c53b2 refactor(async): centralize the thread-sensitive sync boundary` relocated
  `run_in_one_sync_boundary` out of `mutations/resolvers.py` to
  [`utils/querysets.py`][utils-querysets], beside its sibling
  `reject_async_in_sync_context`, so read-side callers (`filters/`, `orders/`, root
  `permissions.py`, `schema.py`) can reuse it without a root-into-subpackage import; it
  stays importable from `mutations/resolvers.py` for historical importers. The bullet
  above, written at extraction time, named the old home — corrected in the Decision.
- **Post-ship (Slice 2 conformance audit, this cycle) — the one shared auth async
  helper is gone, the one-boundary invariant is not.** `c8346750 feat(auth): harden the
  session lifecycle across transports` deleted `_resolve_auth_async`, the single auth
  async helper this Decision named, and gave each fixed field a real sync body and a
  real async body as separate seams (`_login_resolve_body_async`,
  `_logout_resolve_body_async`, and `_sync_bridged_async_body` for `current_user`), so
  a native per-transport async path can be specialized without touching the dispatch
  seam. Re-counted at `HEAD`: every one of those bodies, and the register rider's
  `resolve_async`, enters the thread-sensitive boundary exactly once per resolution and
  none of them spells `sync_to_async` itself. The Decision now pins the **count**, not
  the call site — which is the invariant D17 was actually protecting.
- **Post-ship (integration pass, this cycle) — `D19` was corrected at its obligations
  home and left live here.** The Decision's closing clause said
  [`SyncMisuseError`][glossary-syncmisuseerror] "**is imported** from its public path
  (`django_strawberry_framework` / `.types`), never redefined in `auth/`". Slice 4
  restated the `D18 / D19` obligation as the **prohibitions** they are, with the
  vacuity stated outright, precisely because no such import exists — `auth/` reaches
  the guards that raise `SyncMisuseError` by call, and `rg "SyncMisuseError"
  django_strawberry_framework/auth/` returns two docstring mentions, zero imports and
  zero definitions. So the obligations list and this Decision asserted opposite things
  about one contract, and a later audit reading the Decision would record a violation
  where there is none — the harm the Slice-4 restatement was written to prevent. The
  Decision now states the prohibition in the obligations list's own words, and the
  `D18` clause beside it is tagged a prohibition rather than a reuse directive so the
  two homes share one vocabulary. Caught only by reading the two homes against each
  other: neither sentence is wrong on its own page.
- **No longer claims:** that the shared primitive is optional, that it lives under
  `mutations/`, that one auth async helper is the single site of the boundary call, or
  that `auth/` imports `SyncMisuseError` from anywhere.

## Decision 11 — Transport contract: classify first, refuse a transport that cannot honour the surface truthfully

Spec: [Decision 11 — Transport contract: classify first, refuse a transport that cannot honour the surface truthfully][spec-040-d11].

### Justification (moved from the spec)

None. This Decision carried no `Justification:` block in the spec.
The absence is the spec's, not this move's — four of the twelve
Decisions state their reasoning inside the Decision body and open
straight into their rejected alternatives.

### Alternatives considered (and rejected)

- **Borrow the `try: channels import` fallback now.** Rejected: unreachable until
  `041`; a soft-dep guard defending a path nothing exercises.
- **A bespoke "sessions not configured" `ConfigurationError` probe.** Rejected:
  duplicates Django's own error surface and adds a false-confidence check
  (middleware order, custom session backends, and subpath configs make a reliable
  probe larger than the feature).

### Changes this Decision underwent

- **Revision 1** pinned the session-transport constraint and the deliberate
  non-borrow of upstream's Channels fallback. No later revision touched this
  Decision.
- **Post-ship (Slice 5 reconciliation, this cycle) — this Decision inverted, and the
  heading inverted with it.** It claimed one supported transport (`SessionMiddleware` +
  `AuthenticationMiddleware` on the `/graphql/` request path), no probe of any kind
  ("a sessionless deployment hitting `auth.login` gets Django's own error"), and a
  deliberate non-borrow of the Channels path on the grounds that "the package has no
  Channels surface until the `0.0.14` router card" so the code would be dead and
  untestable under the 100% gate. Each clause was true when written and none is true
  now. `c8346750 feat(auth): harden the session lifecycle across transports` created
  `django_strawberry_framework/auth/sessions.py` — a whole module inside the `auth/`
  package this spec owns, which the Decision named nowhere — carrying the three-mode
  `Transport` classification, the missing-session pre-check the Decision had explicitly
  ruled out, the per-scope `asyncio.Lock`, and the two session-engine capability
  answers; it also added the Channels establishment / teardown paths, so upstream's
  **capability** is now used even though its fallback **shape** is still refused. The
  Decision is rewritten to the shipped contract: the prologue's fixed
  classify → capability → session order, the per-surface support table, the reason each
  refusal is a refusal rather than a gap, the per-transport persistence asymmetry and
  its fail-closed compensation, the one scope-owned lock, the sync / async hop, and the
  boundary this surface shares with `spec-046`. The **heading** carried the falsified
  claim too ("the Channels fallback is NOT borrowed"), so it was renamed; every in-page
  anchor into it, in both files, moved in the same pass, as did the mirrored heading and
  `Spec:` line here.
- **Post-ship (Slice 5 reconciliation, this cycle) — what later commits added on top of
  `c8346750`, folded into the rewrite rather than narrated in the spec.**
  `44b33e9f fix(auth): enhance logout handling for anonymous requests and session
  flushing` made the teardown unconditional and idempotent for an anonymous request;
  `2a62d8b5 Keep login compensation reachable for a BaseException cleanup failure`
  widened the compensation arms to `BaseException` and made a cleanup failure re-raise
  the original with the cleanup chained through `__context__`;
  `6873dac6 fix(auth): fail closed on a hostile authentication state` and
  `eed67f6c fix(auth): contain hostile objects at the session boundary` made the
  classification, the session read, the scope read and the transport label containment
  boundaries that collapse a hostile object to the denied answer rather than letting it
  escape;
  `05a08e31 fix(transport): linearize actor transitions against the whole protected
  send` and `0fa6501d fix(consumers): refuse stale actor reads across a same-connection
  logout` put the WebSocket teardown inside the connection actor lease and fixed the
  lock order; and `dde7c857 fix(transport): correct the transport contracts stated in
  code and pin them with new rows` removed the code's own claim that the package
  router's async consumer serves HTTP — since `spec-046` it serves none — and pointed
  `classify_transport`'s rejection at the view for HTTP and the router for WebSocket.
  The spec states the resulting contract flat; this bullet is the only place the
  sequence is recorded.
- **Boundary with [`spec-046`][spec-046], deliberately not duplicated.** The actor
  lease, the outbound-frame revalidation checkpoints, the positive-window cache, the
  `4403` close, and the argument for why a lock private to a consumer would have given
  no ordering at all are that card's decisions (its Decisions 11 and 16) and are cited,
  not restated — a verbatim second copy rots twice, and this cycle already measured that
  failure mode in the spec's own `D17` home-of-the-primitive claim. What `spec-040`
  states is the effect a consumer of the **auth** surface observes: a same-connection
  `logout` is a connection-scoped revocation event, so the socket closes at its next
  protected checkpoint and the `logout` payload does not reach the client. The lock
  order is named (scope session lock OUTER, actor lease INNER) because
  `auth/mutations.py::_channels_logout` is the only site that holds both and the rule
  binds an auth-side body; its derivation stays in `spec-046`.
- **The per-surface answers are a table on purpose.** `docs/README.md` carries a
  consumer-facing five-row table with `login` and `logout` answered separately per row,
  and the prose form of the same content had already drifted across four spec sections
  before this cycle fenced them into pointers. The spec's own table adds the
  `register` / `current_user` column the consumer-facing one has no need for, because
  the transport-neutrality of those two fields is a **contract** — nothing in
  `auth/queries.py` branches on transport — and the cheapest place to falsify a future
  edit that adds a branch is a column that says so.
- **No longer claims:** that `SessionMiddleware` + `AuthenticationMiddleware` on a
  Django request path is the only supported transport; that the package adds no
  session pre-flight check; that upstream's Channels login / logout capability is not
  borrowed; that the auth surface has no Channels surface to reach; or that the
  `0.0.14` router card inherits the question of whether auth extends to consumer-scope
  sessions — it was answered, in code, with a classification and two refusals.

## Decision 12 — This card owns the `0.0.13` version bump AND completes the joint cut

Spec: [Decision 12 — This card owns the `0.0.13` version bump AND completes the joint cut][spec-040-d12].

### Justification (moved from the spec)

None. This Decision carried no `Justification:` block in the spec.
The absence is the spec's, not this move's — four of the twelve
Decisions state their reasoning inside the Decision body and open
straight into their rejected alternatives.

### Alternatives considered (and rejected)

- **Defer the bump to a separate release-alignment card.** Rejected: no such card
  exists; `039` already deferred *to this card by name* — a second deferral orphans
  the cut.
- **Bump in Slice 1.** Rejected: the version moves after the feature it describes,
  the same reason every prior cut-owning spec staged it last.
- **Split the `039` flips into their own commit ahead of this card.** Rejected: the
  flips advertise a released `0.0.13` and are only truthful in the same cut that
  moves the version — landing them early recreates the mismatch F8 existed to
  prevent.

### Changes this Decision underwent

- **Revision 1** pinned this card as the owner of the `0.0.13` version bump and of the
  joint-cut completion the sibling `0.0.13` serializer card deferred to it. No later
  revision touched this Decision.
- **Post-ship (Slice 3 conformance audit, this cycle):** verified **at the cut**, at
  `3a294082 Release 0.0.13`, and unedited. All five quintet members read `0.0.13`
  there, and every joint-cut flip the Decision names landed: the
  [`docs/GLOSSARY.md`][glossary] [`SerializerMutation`][glossary-serializermutation]
  status, the [`README.md`][readme] **Status** line and both READMEs' "Coming next" →
  "Shipped today" moves for the serializer flavor and the auth surface, and the
  `CHANGELOG.md` `0.0.13` bullets for both cards. The package has since moved to
  `0.0.15` and `pyproject.toml` no longer carries a `[project].version` literal at all
  (hatchling derives it from `__version__`, so the quintet is now a quartet) — but the
  Decision states what **this card's Slice 3 did**, which it did, so a later release
  and a later single-sourcing do not falsify it. Nothing here is a present-tense claim
  about the tree, so nothing was rewritten; this bullet exists so the next reader knows
  the difference was examined rather than missed.

## Risks and open questions

Moved verbatim from the spec, which keeps the heading and a pointer here. Every item
is a preferred-answer / fallback pair for the `0.0.13` cut — a build-time
deliberation instrument rather than a contract — and two of the six are card-citation
tensions the cut chose to record rather than silently reconcile.

Each item names a preferred answer for the `0.0.13` cut and a fallback if
implementation reveals it is wrong.

- **The card's symbol list vs the factory-call shape.** The card DoD names
  `login_mutation`, `logout_mutation`, `register_mutation`, `current_user` as the
  deliverables without pinning whether they are fields or factories. Preferred
  reading
  ([Decision 3](#decision-3--consumer-surface-four-field-factories-at-the-auth-submodule-path-opt-in-by-import-no-root-re-export)):
  zero-argument-callable **factories** (`login = login_mutation()`), matching both
  the package's field-factory idiom and upstream's `login = auth.login()` call
  shape, and giving every symbol the `permission_classes=` seam the card's
  composability DoD requires. Fallback: pre-built field *instances* — rejected
  unless the maintainer prefers them, because instances cannot carry per-schema
  `permission_classes`. Recorded per the [`docs/SPECS/NEXT.md`][next] "prefer the
  card, surface the conflict" rule.
- **[`docs/TREE.md`][tree] carries no `auth/` row for this card.** The target
  layout annotates every other WIP/TODO card's planned paths but reserves nothing
  for `TODO-ALPHA-040`; the card body, by contrast, names
  `django_strawberry_framework/auth/` explicitly. Preferred reading: the card is
  authoritative (the TREE row is an omission from the `0.0.14`-era annotation
  sweep); Slice 3 adds the rows. No fallback needed — the two sources do not
  actually conflict on substance.
- **Custom authentication backends with non-`username` credential kwargs.**
  `authenticate(request, username=, password=)` covers `ModelBackend` and every
  backend honoring the conventional kwargs (including email-login models via
  `USERNAME_FIELD`). A backend wanting different credential *names* (a
  `token=`-shaped backend) cannot ride `login_mutation()`. Preferred answer: out of
  scope — that consumer hand-writes their login mutation today exactly as before
  this card. Fallback: a `credential_fields=` factory kwarg mapping GraphQL
  arguments onto `authenticate` kwargs — a contained, additive follow-on if
  demanded.
- **A register customization surface.** The no-arg factory covers the parity case;
  a consumer wanting extra profile fields at registration has no seam short of
  hand-writing a mutation (with the plaintext-password foot-gun named in
  [Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)).
  Preferred answer for `0.0.13`: ship the factory as specced; record the demand.
  Fallback / follow-on: expose `DjangoRegisterMutation` as a documented
  subclassable base (its password write step inherited), the upstream shape — a
  small additive card, sequenced on real consumer need.
- **Native-async auth APIs** (`aauthenticate` / `alogin` / `alogout`, Django ≥
  5.0, in-support on the package's `Django>=5.2` floor). Preferred answer
  ([Decision 10](#decision-10--sync--async-session-work-through-one-sync_to_asyncthread_sensitivetrue-boundary)):
  keep the family's single `sync_to_async` boundary for `0.0.13`; adopting
  native-async session APIs is a family-wide decision for a dedicated card.
  Fallback: none needed — the boundary is correct, just not maximally concurrent.
- **Channels / websocket sessions.** Deferred to the `0.0.14` router card
  ([Decision 11](#decision-11--transport-contract-classify-first-refuse-a-transport-that-cannot-honour-the-surface-truthfully));
  the risk is a consumer on ASGI websockets expecting upstream's fallback.
  Preferred answer: document the constraint in the GLOSSARY entry now; `041`
  decides whether to extend auth to consumer-scope sessions. Fallback: a fast
  follow-on porting upstream's `channels_auth` fallback once `041` gives it a
  reachable transport.
- **Where the live surface lives.** Preferred answer: a new schema-only fakeshop
  `apps/accounts/` (clean domain split; products stays the catalog vehicle per
  [`TODAY.md`][today]'s scope rule). Fallback: fold the auth fields into
  [`config/schema.py`][config-schema] directly if a models-less app proves awkward
  under fakeshop's app conventions — a mechanical relocation, settled in Slice 1.

## Spec sections outside the Decisions — changes they underwent

Keyed by spec heading and anchor, the same way each `### Changes this Decision
underwent` is keyed to its Decision. Every entry below is the *why* of an edit a
reconciliation slice of the `040` retrospective cycle made to a spec section that
belongs to no single Decision; the spec itself carries only the corrected contract.
Each bullet names its slice or pass, and the per-cycle record of each is
[`docs/builder/bld-040-slice-4-audit_obligations_edges_tests.md`][bld-040-slice-4],
[`docs/builder/bld-040-slice-5-later_spec_reconciliation.md`][bld-040-slice-5] and
[`docs/builder/bld-040-integration.md`][bld-040-integration].

### [`## Key glossary references`][spec-040-glossary-refs]

- **Post-ship (Slice 5, this cycle) — a "does not reach into" bullet that the surface
  reaches into.** The `DjangoGraphQLProtocolRouter` / `TestClient` entry said
  "Channels / websocket login (upstream's `channels_auth` fallback) waits for the router
  card". The router card shipped (`DONE-041-0.0.14`), and `c8346750` then taught the auth
  surface to classify and serve its scopes. The bullet keeps the card-scope fact it was
  written for — this card ships neither the router nor the test-client helpers — and
  hands the transport answer to Decision 11 instead of asserting one.
- **Post-ship (integration pass, this cycle) — three orientation bullets still described
  the pre-cut tree.** The `Auth mutations` bullet said "Slice 3 flips the entry to
  `shipped (0.0.13)`" while the spec's own header already stated the glossary carries it
  as shipped; the `SerializerMutation` bullet said "Slice 3 flips its GLOSSARY status";
  and the `docs/TREE.md` convention bullet said the target layout "does **not** yet
  reserve `django_strawberry_framework/auth/` … (a gap … Slice 3 fixes)". All three were
  true when written and all three describe work this card's own Slice 3 completed —
  Slice 3's audit verified each at `3a294082`. Unlike `## Current state`, this section
  carries no vintage header, so a present-tense claim here is read as current: each now
  states the shipped fact and names Slice 3 as what produced it, rather than promising
  it. This is the class Slice 2's edit 1 fixed at the header line and no pass swept for
  at its parallel sites.

### [`## Goals`][spec-040-goals]

- **Post-ship (integration pass, this cycle) — Goal 4 carried the retired absolute
  privilege claim, and named four of five columns.** It read "privilege-bearing columns
  (`is_staff`, `is_superuser`, `groups`, `user_permissions`) are structurally
  unreachable" — the proposition Slice 3 retired from Decision 6 (a custom model may
  place one of them in `USERNAME_FIELD` / `REQUIRED_FIELDS`, which is why
  `a40f0d33` added an explicit rejection), with `is_active` missing from a set
  `auth/mutations.py::_REGISTER_PROTECTED_FIELDS` states as five names. Two defects in
  one sentence: a claim the companion already records as retracted, and an enumeration
  short by a member. Goal 4 now states both layers and all five names, pointing at
  Decision 6. `## Goals` was in no audit slice's scope, which is how a fixed claim's
  parallel site survived three audits and a reconciliation slice.
- **No longer claims:** that account-control columns are unreachable by structure alone,
  or that there are four of them.

### [`## Non-goals`][spec-040-non-goals]

- **Post-ship (Slice 5, this cycle) — a non-goal whose own condition has been met.**
  "Channels / websocket authentication … is deliberately not borrowed **until** the
  `0.0.14` router card gives the package a Channels story" was a conditional, and the
  condition is now satisfied, so as written it read as a present-tense claim that
  WebSocket auth is outside the surface — which is the opposite of Decision 11's
  refusal-with-a-reason. Restated as the card-scope non-goal it always was (this card
  ships no router, no consumer, no scope handling) plus the one thing still genuinely
  not borrowed on any transport: the *fallback shape*.

### [`## Borrowing posture`][spec-040-borrowing]

- **Post-ship (Slice 5, this cycle) — "the `channels_auth` fallback … deferred to the
  router card" is two claims, and only one survived.** The **capability** —
  `channels.auth`'s `login` / `logout` — is used today, on a classified Channels scope.
  What is still refused is the **shape**: upstream attempts a Channels path after the
  Django path fails and sniffs the consumer scope for a user, i.e. it diagnoses the
  transport from the failure it caused. This package classifies first and enters no path
  speculatively, which is also why `auth/sessions.py`'s module docstring can promise that
  the transport is never detected by catching `AttributeError`. Both the
  `### Explicitly do not borrow` bullet and the `get_current_user` borrow bullet now say
  which half is which; the second additionally records that `me` needs no scope branch
  because the shared `request_from_info` contract already resolves either request shape.

### [`### Error shapes`][spec-040-api]

- **Post-ship (Slice 5, this cycle) — two shipped rejections the table did not carry.**
  `auth/mutations.py::_WEBSOCKET_LOGIN_UNSUPPORTED` and `::_WEBSOCKET_LOGOUT_UNSUPPORTED`
  are `ConfigurationError`s raised in the transport prologue, and the table is the
  spec's one map from a case to where it lands. Slice 2 found them and deliberately
  added neither row, so the rejection contract would be written once, with the Decision
  that owns it; the two rows land here. Both say *before authentication* / *before any
  session mutation* and both say the refusal is a top-level error rather than the
  failed-login envelope, because that distinction is the whole reason their wording is
  free while the envelope's is byte-pinned.
- **Post-ship (integration pass, this cycle) — the third transport-capability refusal
  was still missing.** Slice 5 added the two WebSocket rows and left the
  missing-session-middleware refusal out, so the table carried two of the three
  refusals the Decision 11 support matrix enumerates while its own job is to map every
  documented failure to where it lands. The absent row is the one a misconfigured
  deployment actually hits. Added, pointing at Decision 11 for the per-transport
  behaviour and at `## Edge cases` for the message contract, and naming that `register`
  / `me` are unaffected — which is the half a reader of the table alone would otherwise
  have to infer. Found by grading the *absence* against Decision 11's five-row table,
  not by re-reading the rows that are there.

### [`## Slice checklist`][spec-040-slices] — the post-ship blockquote

- **Post-ship (Slice 4, this cycle) — the retired-artifact pointer was worse than
  dangling.** Slice 1 graded this blockquote, left it in the spec as a reading
  instruction about the document's own conventions, and recorded the dangling pointer
  for the reconciliation slices. Discharged here. The pointer named
  `docs/builder/bld-slice-*.md`, `bld-integration.md` and `bld-final.md`; the `0.0.13`
  cycle's build plan and its three slice artifacts
  (`bld-slice-1-auth_substrate_login_logout.md`,
  `bld-slice-2-register_current_user.md`, `bld-slice-3-docs_version_cut_wrap.md`) were
  **deleted at `ed2693f9`**, the `spec-041` cycle's pre-flight artifact reset, and were
  never moved to `docs/builder/DONE/` — so the record survives only in git history at
  the release commit `3a294082`, which the blockquote now names with the `git show`
  form [`START.md`][start] "Retiring a per-cycle artifact strands inbound refs"
  prescribes. The sharper half: `docs/builder/` is **reused by whichever cycle is
  active**, so those exact paths exist in the working tree today and describe an
  entirely different card. A reader following the old pointer would not have found
  nothing; they would have found someone else's build and had no signal it was the
  wrong one. That is why the replacement carries an explicit "do not read the
  unprefixed `bld-*.md` files as this card's record" clause rather than only a
  retarget.

### [`## Helper-reuse obligations (DRY)`][spec-040-helpers] — `D6`, `D7`, `D17 / P3`, `D18 / D19`, `D-N3`

- **Post-ship (Slice 4, this cycle) — `D6`'s named parameter no longer exists.** The
  item threaded `excluded_input_fields={"password"}` "through `_model_decode_step` /
  `_decode_relations`". `rg -n --glob '*.py' excluded_input_fields` returns **0** across
  the whole tree: `31625ac7` replaced the per-call parameter with a bind-time `EXCLUDED`
  field kind, stashed by the rider's `build_input` seam through
  `mutation_input_field_specs(..., excluded_attrs=...)` and honoured by the ONE shared
  decode spine. The invariant the item protects — one decoder, the raw value never a
  constructed model attr, the provided-marker preserved so `_unprovided_exclude` still
  counts `password` as provided — is intact and is what the item now states; the
  parameter was only ever the mechanism that happened to hold it. This is the same
  correction [Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)
  took in Slice 3, made in the obligations checklist so the two homes agree; Slice 3
  handed the re-grade forward for exactly that reason.
- **Post-ship (Slice 4, this cycle) — `D7` named the wrong delegate and undercounted the
  auth-specific steps.** The item said the `write_step` delegates to
  `_full_clean_or_field_errors` / `save_or_field_errors` directly; at `HEAD` it delegates
  to `mutations/resolvers.py::_model_write_step`, which is what calls those two — a
  reuse one level deeper than the item described, not a weaker one. And "only
  `validate_password` + `set_password` are auth-specific" was falsified by `a6f5a6cb` /
  `a8f31a2d`, which added the unstorable-password preflight (itself the shared
  `unencodable_text_error` primitive, so the DRY claim survives the correction). Slice 3
  made the matching Decision 6 edit; this is its obligations-checklist half.
- **Post-ship (Slice 4, this cycle) — `D17 / P3` described a single call site that
  `c8346750` deleted.** The item said the boundary is "single-sited across the three".
  `_resolve_auth_async`, the one shared auth async helper, is gone; six auth call sites
  now invoke `run_in_one_sync_boundary` directly (`_sync_bridged_async_body`, the login
  and logout async bodies' two arms each, and the register rider's `resolve_async`). The
  item now states what `rg` can still settle and what the removal did not change: no auth
  module spells `sync_to_async` itself (**0** hits under `auth/`), the primitive's home is
  [`utils/querysets.py`][utils-querysets], and one resolution enters the boundary exactly
  once with the gate inside it. Slice 2 routed this here after making the corresponding
  [Decision 10](#decision-10--sync--async-session-work-through-one-sync_to_asyncthread_sensitivetrue-boundary)
  edit; the two homes now agree, which is what the hand-off asked for.
- **Post-ship (Slice 4, this cycle) — `D18 / D19` read as claims about call sites that do
  not exist.** Slice 2 graded both **vacuously** satisfied and asked whether an obligation
  with no call site should still be stated. Ruling: yes, and it is restated as the
  prohibition it always was. `is_async_callable`-over-`inspect.iscoroutinefunction` and
  never-redefine-`SyncMisuseError` are constraints on what the auth surface may do, so
  they stay live the moment a future edit adds such a site; deleting them because nothing
  exercises them today would retire the constraint precisely when it is cheapest to keep.
  What changed is the reading: the old wording ("`SyncMisuseError` **is imported** from
  its public path") asserts an import that does not exist and invites a later audit to
  record a violation where there is none. The item now says so explicitly.
- **Post-ship (Slice 4, this cycle) — `D-N3`'s reason clause contradicted
  [`## Edge cases and constraints`][spec-040-edges].** The item justified the non-reuse
  with "the narrowed `Meta.fields` has no relation inputs", while the **Custom user
  models** edge case states that a `REQUIRED_FIELDS` entry which is a forward FK becomes
  the standard `<field>_id` input. Both cannot be true. The normative half — register
  wires no relation-visibility helper of its own — holds either way, so the item keeps it
  and drops the false reason, stating instead that the rider inherits the shared decode's
  relation handling and adds nothing. This is the defect class cross-checking the five
  homes of a contract exists to catch: neither sentence is wrong on its own page.

### [`## Edge cases and constraints`][spec-040-edges]

- **Post-ship (Slice 4, this cycle) — the failure-class count moved from three to four.**
  `a6f5a6cb` added the credential storability preflight, whose short-circuit reaches the
  same undifferentiated envelope, and `tests/auth/test_mutations.py::test_all_four_failure_classes_share_one_byte_identical_envelope`
  asserts all four payloads byte-identical. "All three collapse" was a stated count that
  a later card falsified.
- **Post-ship (Slice 4, this cycle) — two bullets spelled one transport's mechanism as
  the contract.** **Anonymous logout** named `auth.logout` (the Django HTTP teardown) and
  **Async contexts** asserted that the session work runs inside the
  `sync_to_async(thread_sensitive=True)` boundary. `c8346750` gave both a per-transport
  split: the Channels teardown is `channels.auth.logout` under a per-scope lock, and on a
  Channels HTTP login the establishment is awaited natively *after* the boundary the gate
  and `authenticate` ran in. Both bullets now state the transport-neutral invariant — the
  observational `ok` with empty `errors`; one boundary per resolution with the gate inside
  it — and point at
  [Decision 11](#decision-11--transport-contract-classify-first-refuse-a-transport-that-cannot-honour-the-surface-truthfully)
  for the split, so the transport contract is still written once, in Slice 5's Decision.
- **Post-ship (Slice 4, this cycle) — the sessionless bullet was false in both halves.**
  It said Django's own error surfaces and "the package adds no probe". `c8346750` added
  `auth/sessions.py::require_session`, a pre-check that fires before any credential or
  session work and raises an actionable `ConfigurationError` naming `SessionMiddleware`
  and `AuthMiddlewareStack` — precisely a probe, and the right one: without it the
  absence surfaced downstream as a raw `AttributeError` off a `None` session. Worth
  recording beyond the correction: the bullet's own test claim ("pins that the error is
  Django's, not a swallowed pass") is pinned by an assertion —
  `"session" in res.errors[0].message.lower()` — that passes under **either** contract,
  so the suite could not have told the reader which one shipped. The bullet now requires
  the row to assert the error's class and its actionable text.
- **Post-ship (Slice 4, this cycle) — the `REQUIRED_FIELDS` bullet omitted the privilege
  rejection.** `a40f0d33` added `_REGISTER_PROTECTED_FIELDS` and the raise
  `derive_register_fields` drives; Slice 3 folded it into Decision 6 and this bullet, its
  edge-case home, still described only the `editable_input_fields` delegation. The same
  omission is live in [`docs/GLOSSARY.md`][glossary]'s auth entry and is recorded there as
  a maintainer finding — the glossary is DB-backed and outside this cycle's scope fence.

### [`## Test plan`][spec-040-test-plan]

- **Post-ship (Slice 4, this cycle) — the live enumeration under-described the suite it
  governs.** `examples/fakeshop/test_query/test_auth_api.py` carries 21 rows; the plan
  named roughly half. The unenumerated rows are not incidental — the four login /
  re-login session-handling branches, the three unstorable-credential rows, the
  password-similarity rejection, the decode-failure envelope, the dict-form validator
  error, and the real-CSRF row are each the sole live pin of a documented behaviour, and
  a plan that does not name them cannot be used to notice one being deleted. Added.
- **Post-ship (Slice 4, this cycle) — three required rows the plan never asked for, each
  a boundary the shipped suite does not pin.** Recorded in full, with the assertion shape
  and the tree each belongs in, in
  [`bld-040-slice-4-audit_obligations_edges_tests.md`][bld-040-slice-4]; the spec now
  states them as contract so the gap has a durable home rather than dying with this
  cycle's artifact. In short: (a) the finalizer's `loaded_attr` reach — the existing
  subprocess row exercises only `registry.clear()` and its docstring claims a finalize
  coverage it does not perform, so swapping the phase-2.5 lookup for a plain import keeps
  every auth row green while
  [Decision 3](#decision-3--consumer-surface-four-field-factories-at-the-auth-submodule-path-opt-in-by-import-no-root-re-export)'s
  structural opt-in is void; (b) the privilege rejection at `register_mutation()` rather
  than only at the helper, which one row pins today; (c) a deep selection under `me` and
  under `login { node { … } }` with strictness on, which nothing selects anywhere — every
  `me` query in every tree is `{ me { username } }`. All three are `tests/auth/` rows, not
  live ones, and the plan says why for each, since the live-first mandate's default is the
  other way.
- **Post-ship (Slice 5, this cycle) — the plan named no transport row at all.** Decision 4
  gained `tests/auth/test_sessions.py` in Slice 2, but the `## Test plan` never described
  what that file must hold, and the plan's five homes for a contract are exactly what
  makes a deleted assertion noticeable. The shipped coverage is substantial — 51 rows in
  `tests/auth/test_sessions.py` plus the Channels / WebSocket rows in
  `tests/auth/test_mutations.py` — so this is a description gap, not a coverage gap, and
  no `TEST-GAP` was recorded. The row states the classification / capability / lock
  obligations and the two resolver-level refusals, and says why the whole block is
  `tests/auth/` work: fakeshop is WSGI-only and mounts no `asgi.py`, so no Channels scope
  is reachable from a real query — the same documented live-first exception the
  permission-gate variants already take, for an unrelated reason.

### `## Doc updates`

- **Post-ship (Slice 4, this cycle) — the Slice 1–2 bullet named an artifact that has
  never existed anywhere in the example project.** It promised "the fakeshop `accounts`
  app README breadcrumbs"; `ls examples/fakeshop/apps/*/README.md` matches nothing, at
  `HEAD` or at `3a294082`, for **any** app. This is a planning fiction rather than a
  dropped deliverable: the breadcrumbs did land, in the `accounts` app's module
  docstrings, which is also where [`docs/TREE.md`][tree] reads them from — a better home
  than a README the tree generator cannot see. No Definition-of-done item rests on the
  bullet, so nothing downstream was falsified by it; the bullet now names what shipped.
- **Post-ship (Slice 5, this cycle) — "the no-Channels constraint" as a doc obligation.**
  The Slice 3 bullet listed what the [`docs/GLOSSARY.md`][glossary] auth entry must
  carry, and one item was the *absence* of a transport. Slice 3's audit confirmed the
  obligation was honoured at the cut, so this is not a dropped deliverable; it is an
  obligation stated in a vocabulary the surface has outgrown, and a reader checking the
  glossary against it today would find an entry describing the opposite. Reworded to
  "the session-transport constraint", pointing at Decision 11 — true of what shipped at
  the cut and of what the entry carries now, and it stays true the next time the
  transport answer moves.

### [`## Out of scope (explicitly tracked elsewhere)`][spec-040-oos]

- **Post-ship (Slice 4, this cycle) — two card ids named a lifecycle that ended.** The
  Channels-router and test-client bullets cited `TODO-ALPHA-041-0.0.14` and
  `TODO-ALPHA-043-0.0.14`; both are `DONE-…-0.0.14` on the board today. These are the
  clean prefix-flip class the [`KANBAN.md`][kanban] catalogue of this defect calls class
  (c) — live forward-reference prose, not a quotation and not a lifecycle-transition
  sentence — so they were flipped rather than de-tensed, following the precedent the
  `spec-039` residual cycle set for its own `DONE-043-0.0.14` pointer. The
  Channels bullet additionally carried a transport claim ("upstream's `channels_auth`
  fallback ports there if at all") that `auth/sessions.py` falsified; it now points at
  Decision 11 and states no transport contract of its own, the same treatment Slice 2 gave
  Decision 2.

### [`## Definition of done`][spec-040-dod]

- **Post-ship (Slice 4, this cycle) — item 7 was a present-tense claim about a number
  later cards move.** "The version quintet reads `0.0.13`" is false at any `HEAD` past
  this card's cut, and [`docs/builder/BUILD.md`][build-md] ``### `## Current state`:
  observations stand, predictions do not`` gives a Definition-of-done item no vintage
  exemption: a stale figure there is a false completion claim. Slice 3 verified all five
  members read `0.0.13` at `3a294082`, so the fact is sound and only its tense was wrong;
  the item now states it as a claim about the cut and says so explicitly, which is what
  makes it permanently checkable.
- **Post-ship (Slice 4, this cycle) — item 1 named only one companion and one location.**
  The `-terms.csv` archived to `docs/SPECS/appx/` rather than beside the spec
  ([`AGENTS.md`][agents] rule 26), and the spec now has a second companion — this file —
  which item 1 could not have anticipated and which a reader checking the DoD against the
  tree would otherwise read as an unaccounted-for file.
- **Item 6's three-`D-N*`-source-comments clause was graded and deliberately left
  alone.** It claims "the three deliberate non-reuse points carry their source comment";
  at `HEAD` only two do (`D-N1` twice, `D-N2` once — `rg 'D-N3' django_strawberry_framework/`
  returns 0), and `git show 3a294082:django_strawberry_framework/auth/mutations.py` shows
  the same, so `D-N3`'s comment was never written. That makes it the one **code gap** this
  cycle has found: the spec is right and the tree is short, so weakening the spec to say
  "two" would be exactly the fix-the-test-not-the-code shortcut [`AGENTS.md`][agents]
  forbids. Recorded for the code-fix cohort in
  [`bld-040-slice-4-audit_obligations_edges_tests.md`][bld-040-slice-4] instead.
  **Discharged:** Slice 6 wrote the `D-N3` comment at
  `auth/mutations.py::_synthesize_register_rider`, so item 6's clause is now true and
  the observation above is dated rather than live.
- **Post-ship (integration pass, this cycle) — item 4 restated the retired absolute
  privilege claim.** Its parenthetical read "privilege columns structurally absent" —
  the proposition Slice 3 retired from Decision 6, and that Slice 6 then found still
  live in Decision 6's own body. Slice 4 graded the clause `CONFORMS` on the ground
  that the contract landed and the sentence states only its structural half, and that
  reading is what let a third home of a retracted claim survive. A Definition-of-done
  item is a completion claim, so a half-true one is a false completion claim in the
  same way item 7's tense was. It now names Decision 6's two layers.
- **No longer claims:** that only two `D-N*` points carry a source comment, or that
  account-control columns are absent from the register input by structure alone.

## Non-Decision deliberation

Findings and provenance that belong to no single Decision.

- **The spec narrated its own history in two vocabularies, and only one of them was
  decodable.** Beyond the seven-entry revision block, `spec-040` carried **38**
  inline chronology attributions in surviving prose — 36 parentheticals such as
  `(the Revision-7 wording fix)`, `(the P2 seam fix)` and `(the P1 review finding,
  folded in)`, plus two mid-sentence clauses that used an em dash rather than
  parentheses and that a parenthetical-shaped sweep alone does not see — each
  tagging a normative sentence with the round that produced it. The
  `Revision-N` half decoded **against the very block this move removed**, so
  leaving them would have stranded every citer in a file that no longer contains
  their referent; the bare `P1`–`P3` half decoded against review-round priority
  tiers that were never in the spec at all. Both are the
  review-round attribution [`START.md`][start] "Style Rio cares about" bans from
  standing prose, and the three sibling specs that have been through this move
  (`038`, `039`, `046`) carry **zero** such labels. All 38 were removed in this
  pass; what each recorded is a bullet under its Decision's
  `### Changes this Decision underwent` instead. **Four look-alike parentheticals
  were verified before being touched and deliberately kept**: `(the helper-reuse
  review's D3 / P4 reuse directive)`, `(the helper-reuse review's D12 / P1 / P2
  reuse directive)`, `(the helper-reuse review's D1–D19 / P1–P4 / D-N1–D-N3
  directives)`, and the `D17 / P3` reference in
  [Decision 10](#decision-10--sync--async-session-work-through-one-sync_to_asyncthread_sensitivetrue-boundary).
  Their `P1`–`P4` are a **different** vocabulary sharing the spelling: they are
  compound labels of the spec's own `## Helper-reuse obligations (DRY)` checklist
  (`D3 / P4`, `D12 / P1 / P2`, `D17 / P3`), defined inside the spec and cited by it,
  so they are spec-internal cross-references rather than round attribution. A sweep
  keyed on the spelling alone would have deleted four live cross-references.
- **Two removals took a clause with them, and both were restored without the
  label.** `(the Revision-7 stable-denial-string fix — the denial strings are
  test-asserted contracts)` and the `## Test plan` pair `(the auth-ledger every-call
  re-record closing the reload regression, Revision-4 P2)` / `(the cache / conflict
  state IS the ledger, Revision-7)` each carried substantive reasoning beside the
  attribution. Under [`docs/builder/BUILD.md`][build-md] `## Spec rationale
  extraction`'s implementation-relevance carve-out that reasoning stays, so the three
  clauses were rewritten into the surviving sentences as plain statements and only the
  round tags were dropped. The other 35 removals took nothing but provenance.
- **One amendment block existed, and moving its narration alone would have left the
  spec offering the thing it had already shipped.**
  [Decision 10](#decision-10--sync--async-session-work-through-one-sync_to_asyncthread_sensitivetrue-boundary)
  ended with a `**Build note (Worker 1):**` paragraph recording that the optional
  `run_in_one_sync_boundary` factoring "WAS taken", immediately after a sentence still
  saying a follow-on **may** take it — and the spec's own
  `## Helper-reuse obligations (DRY)` `D17 / P3` item still called the primitive "an
  optional follow-on". Three statements of one contract, two of them stale. The
  Decision now states the shipped shape directly, `D17 / P3` was corrected to match in
  the same pass, and the chronology is a `**Post-ship**` bullet under that Decision.
  This is the one shape a pure cut-and-paste could not discharge: removing the
  amendment without rewriting what it amended would have made the spec *more* wrong,
  not less.
- **The `-terms.csv` coupling bound this move and cost it nothing.** `spec-038`'s
  execution had to hold two clauses back in the spec because three glossary terms had
  their only link inside prose the move was taking. `spec-040` needed none: the
  30-term check was run link-by-link against the planned cut before any text was
  removed and every term kept at least one surviving link, the tightest margin being
  a term with exactly one. Worth recording because the coupling is invisible from
  either document — a spec's companion CSV silently decides which prose the rationale
  move may take, and the failure surfaces as a gate exit 1 rather than as a reading
  error.
- **Every moved block was checked against the carve-out, and the normative statement
  each one explains survives in the spec.** The two rejected alternatives most at risk
  of taking a contract with them were
  [Decision 6](#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor)'s
  ("a `pre_save` / per-instance write hook added to the `036` base" — rejected because
  widening the frozen base for one internal consumer re-opens a shipped contract) and
  [Decision 9](#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows)'s
  ("register the auth declaration ledger with `before_bind=True`" — rejected because
  the pre-bind reset would drain the declarations before the bind reads them). Both
  Decision bodies state the requirement normatively without the rejection: Decision 6's
  body pins the `resolve_sync` / `resolve_async` override riding
  `run_write_pipeline_sync` with its own step pair, and Decision 9's body pins the
  full-clear-only row and says in its own words why draining declarations pre-bind
  would break the first finalize. Neither move can produce the defect its rejection
  warns about.
- **The `## Slice checklist`'s post-ship blockquote was graded and left in the spec,
  with one inbound reference now dangling.** It explains that the `- [ ]` boxes are
  preserved as authored and that the completion record lives in the build artifacts —
  a reading instruction about the document's own conventions rather than deliberation
  about a decision, so it is not this move's to take. But it points at
  `docs/builder/bld-slice-*.md`, `bld-integration.md` and `bld-final.md`, which were
  retired when the `0.0.13` build cycle closed; under [`START.md`][start] "Retiring a
  per-cycle artifact strands inbound refs" that pointer now needs either a `git show
  <commit>:<path>` retarget or de-linking. Recorded for the reconciliation slices,
  which own it; this pass did not touch it.
- **`## Current state` and `## Borrowing posture` were graded and deliberately
  stayed.** `## Current state` is five dated **observations** of the pre-build repo,
  which stand under [`docs/builder/BUILD.md`][build-md] ``### `## Current state`:
  observations stand, predictions do not`` — the header dates them — and it carries no
  predictions about the build's outcome. `## Borrowing posture` reads like
  deliberation but is not: its three sub-sections enumerate what the implementation
  borrows semantically from
  [`strawberry_django/auth/`][upstream-auth-mutations], what it borrows structurally
  from the package's own write family, and the four things it must **not** borrow —
  including the deliberate improvement of passing the constructed user instance to
  `validate_password(password, user)`, which a builder who never reads it implements
  the upstream way. That is the carve-out's central case, and the sibling specs that
  have been through this move (`038`, `039`, `046`) all keep their borrowing posture
  in the spec.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../../AGENTS.md
[goal]: ../../../GOAL.md
[kanban]: ../../../KANBAN.md
[readme]: ../../../README.md
[start]: ../../../START.md
[today]: ../../../TODAY.md

<!-- docs/ -->
[feedback2]: ../../feedback2.md
[glossary-configurationerror]: ../../GLOSSARY.md#configurationerror
[glossary-cross-subsystem-invariants]: ../../GLOSSARY.md#cross-subsystem-invariants
[glossary-djangomutation]: ../../GLOSSARY.md#djangomutation
[glossary-djangomutationfield]: ../../GLOSSARY.md#djangomutationfield
[glossary-djangotype]: ../../GLOSSARY.md#djangotype
[glossary-fielderror-envelope]: ../../GLOSSARY.md#fielderror-envelope
[glossary-get_queryset-visibility-hook]: ../../GLOSSARY.md#get_queryset-visibility-hook
[glossary-serializermutation]: ../../GLOSSARY.md#serializermutation
[glossary-syncmisuseerror]: ../../GLOSSARY.md#syncmisuseerror
[glossary]: ../../GLOSSARY.md
[tree]: ../../TREE.md

<!-- docs/SPECS/ -->
[next]: ../NEXT.md
[spec-038]: ../spec-038-form_mutations-0_0_12.md
[spec-040-api]: ../spec-040-auth_mutations-0_0_13.md#user-facing-api
[spec-040-borrowing]: ../spec-040-auth_mutations-0_0_13.md#borrowing-posture
[spec-040-d10]: ../spec-040-auth_mutations-0_0_13.md#decision-10--sync--async-session-work-through-one-sync_to_asyncthread_sensitivetrue-boundary
[spec-040-d11]: ../spec-040-auth_mutations-0_0_13.md#decision-11--transport-contract-classify-first-refuse-a-transport-that-cannot-honour-the-surface-truthfully
[spec-040-d12]: ../spec-040-auth_mutations-0_0_13.md#decision-12--this-card-owns-the-0013-version-bump-and-completes-the-joint-cut
[spec-040-d1]: ../spec-040-auth_mutations-0_0_13.md#decision-1--spec-filename-and-canonical-naming
[spec-040-d2]: ../spec-040-auth_mutations-0_0_13.md#decision-2--card-scope-boundary-session-auth-ships-token-auth-stays-out-no-new-meta--settings-key
[spec-040-d3]: ../spec-040-auth_mutations-0_0_13.md#decision-3--consumer-surface-four-field-factories-at-the-auth-submodule-path-opt-in-by-import-no-root-re-export
[spec-040-d4]: ../spec-040-auth_mutations-0_0_13.md#decision-4--module-and-test-locations-auth-mirroring-the-upstream-trio-testsauth-mirroring-source
[spec-040-d5]: ../spec-040-auth_mutations-0_0_13.md#decision-5--login--logout-session-mutations-on-the-frozen-envelope-anonymous-allowed-by-design
[spec-040-d6]: ../spec-040-auth_mutations-0_0_13.md#decision-6--register_mutation-rides-djangomutation-a-narrow-create-over-get_user_model-with-password-hashing--not-a-fourth-flavor
[spec-040-d7]: ../spec-040-auth_mutations-0_0_13.md#decision-7--current_user-returns-the-session-actor-nullable-and-does-not-re-run-get_queryset
[spec-040-d8]: ../spec-040-auth_mutations-0_0_13.md#decision-8--the-user-models-primary-djangotype-is-required-validated-at-bind
[spec-040-d9]: ../spec-040-auth_mutations-0_0_13.md#decision-9--bind-lifecycle-a-declaration-ledger--bind_auth_mutations-at-phase-25--registered-clear-rows
[spec-040-dod]: ../spec-040-auth_mutations-0_0_13.md#definition-of-done
[spec-040-edges]: ../spec-040-auth_mutations-0_0_13.md#edge-cases-and-constraints
[spec-040-glossary-refs]: ../spec-040-auth_mutations-0_0_13.md#key-glossary-references
[spec-040-goals]: ../spec-040-auth_mutations-0_0_13.md#goals
[spec-040-helpers]: ../spec-040-auth_mutations-0_0_13.md#helper-reuse-obligations-dry
[spec-040-non-goals]: ../spec-040-auth_mutations-0_0_13.md#non-goals
[spec-040-oos]: ../spec-040-auth_mutations-0_0_13.md#out-of-scope-explicitly-tracked-elsewhere
[spec-040-slices]: ../spec-040-auth_mutations-0_0_13.md#slice-checklist
[spec-040-terms]: spec-040-auth_mutations-0_0_13-terms.csv
[spec-040-test-plan]: ../spec-040-auth_mutations-0_0_13.md#test-plan
[spec-040]: ../spec-040-auth_mutations-0_0_13.md
[spec-046]: ../spec-046-transport_security-0_0_14.md

<!-- docs/builder/ -->
[bld-040-integration]: ../../builder/bld-040-integration.md
[bld-040-slice-1]: ../../builder/bld-040-slice-1-rationale_extraction.md
[bld-040-slice-4]: ../../builder/bld-040-slice-4-audit_obligations_edges_tests.md
[bld-040-slice-5]: ../../builder/bld-040-slice-5-later_spec_reconciliation.md
[build-040]: ../../builder/build-040-auth_mutations-0_0_13.md
[build-md]: ../../builder/BUILD.md

<!-- django_strawberry_framework/ -->
[mutations-fields]: ../../../django_strawberry_framework/mutations/fields.py
[mutations-resolvers]: ../../../django_strawberry_framework/mutations/resolvers.py
[registry]: ../../../django_strawberry_framework/registry.py
[utils-permissions]: ../../../django_strawberry_framework/utils/permissions.py
[utils-querysets]: ../../../django_strawberry_framework/utils/querysets.py

<!-- tests/ -->

<!-- examples/ -->
[config-schema]: ../../../examples/fakeshop/config/schema.py
[schema-reload]: ../../../examples/fakeshop/schema_reload.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[upstream-auth-mutations]: ../../../../strawberry-django-main/strawberry_django/auth/mutations.py
