# Build: final test-run gate (036 residual-reconciliation cycle)

Spec reference: `docs/SPECS/spec-036-mutations-0_0_11.md`
Rationale companion: `docs/SPECS/appx/spec-036-mutations-0_0_11-rationale.md`
Build plan: `docs/builder/build-036-mutations-0_0_11.md`
Status: final-accepted

Written by Worker 1 per `docs/builder/BUILD.md` `## Final test-run gate` and `docs/builder/worker-1.md`
`## Final test-run gate`. Every command below was run in this pass, in the order that section gives, and
recorded with its own exit code. **No `--cov*` flag was passed to any invocation** and no coverage number
was inspected, per `docs/builder/BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool`.
No `git stash` / `git checkout` / `git restore` / `git worktree`. This pass edited no `.py` file, no
spec, and no standing doc; it wrote this artifact, `docs/builder/bld-036-integration.md`, the appended
`## Final verification (Worker 1)` in `docs/builder/bld-036-review-3-code_repair.md`, and
`docs/builder/worker-memory/worker-1-036.md`.

## Gate results

| # | command | result |
|---|---|---|
| 1 | `uv run pytest --no-cov -q` | **4 failed, 7119 passed, 42 skipped** in 69.81s — all four pre-existing and attributable to the concurrent session; see below |
| 2 | `uv run python examples/fakeshop/manage.py check` | **PASS**, exit 0 — `System check identified no issues (0 silenced).` |
| 3 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | **PASS**, exit 0 — `No changes detected` |
| 4 | `uv run ruff format --check .` | **PASS**, exit 0 — `438 files already formatted` |
| 5 | `uv run ruff check .` | **PASS**, exit 0 — `All checks passed!` |
| 6 | `git diff --check` | **exit 2 tree-wide / exit 0 scoped** — the plan's recorded baseline exception; both readings below |

Supplementary read-only gates, run because this cycle's own output includes the spec pair and because R3
recorded a citation figure a later pass would otherwise inherit:

| command | result |
|---|---|
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-036-mutations-0_0_11.md` | `OK: 38 terms`, exit 0 — unchanged across Slice 0, R2, and this gate |
| `uv run python scripts/check_citations.py` | `OK: 933 citations resolve (776 in 435 .py files, 157 in KANBAN.md)`, exit 0 — the same figure R3 recorded, so its two new `path::QualifiedName` citations resolve and neither is wrapped across a line |
| `uv run python scripts/check_trailing_commas.py --check docs/builder/bld-036-*.md` | exit 0 — `bld-*.md` artifacts are **excluded from the source-layout rules** by name, so no link-def scaffold obligation applies to them (which is why several of this cycle's artifacts correctly carry no `<!-- LINK DEFINITIONS -->` block) |

### Gate 6, both readings

**Tree-wide: exit 2.** Four trailing-whitespace lines in a baseline-dirty out-of-scope maintainer
document (`docs/feedback2.md:3-6`), all four inside a `+` line of the concurrent session's own
uncommitted work. This is the exception the build plan's preamble records verbatim under
`**git diff --check baseline exception:**`, so `docs/builder/worker-1.md`'s clause — a lint/diff failure
blocks `final-accepted` **unless a pre-flight baseline exception was recorded in the plan's preamble** —
applies and the gate is not blocked. Not fixed, not reverted, per `AGENTS.md` rule 34.

**Scoped to this cycle's own files: exit 0.** `git diff --check` over R3's six test files plus the spec
pair plus this cycle's artifacts produces no output. So no whitespace error and no conflict marker in
anything this cycle wrote.

## The four suite failures are pre-existing and NOT this cycle's

`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose` is explicit that a
**failing test is not worker-verifiable at `HEAD`** — reproducing it needs the whole tree at `HEAD`, and
this tree is legitimately dirty with a concurrent session's uncommitted work across 106 paths. So the
evidence available is recorded and the claim is **escalated to the maintainer**, the only party who can
run a clean `HEAD` tree. Recording plus escalating discharges the obligation; nothing here was fixed,
re-pinned, or graded against this cycle, which `AGENTS.md` rule 34 and the plan's maintainer-set scope
both forbid.

**1. `tests/optimizer/test_walker.py::test_divergent_key_windows_shared_payload_uses_none_key`** — the
row asserts a plain tuple where the value is now a `ConnectionWindowBounds`. Attribution, re-derived in
this pass:

```shell
$ git show HEAD:django_strawberry_framework/optimizer/nested_planner.py | grep -c ConnectionWindowBounds   # 0
$ grep -c ConnectionWindowBounds django_strawberry_framework/optimizer/nested_planner.py                   # 5
$ git diff --numstat HEAD -- django_strawberry_framework/optimizer/nested_planner.py                       # 31  32
```

The class does not appear in that planner at `HEAD` at all and appears five times live, in a file dirty
`31/32` and named on the plan's `### Baseline-dirty out-of-scope files` list. The failing row's `def` sits
at line **3568** while R3's only two hunks in that file are `@@ -25,6 +25,7 @@` (one import) and
`@@ -4771,30 +4772,80 @@` (the G2 block), so the row is not in this cycle's diff. R3 deliberately left
it alone rather than re-pinning a production contract that is mid-flight in another session, and that was
the right call: the fix belongs to the pass that owns the behavior.

**2-4. `tests/orders/test_inputs.py::test_ensure_field_specs_derives_the_unset_sentinel_from_the_family_declaration`,
`tests/test_sets_mixins.py::test_permission_family_config_stays_on_each_set_class`,
`tests/test_sets_mixins.py::test_filter_normalizer_honors_a_subclass_unset_sentinel_override`** — one
traceback, `TypeError: ActiveInputPermissionAttrs.__init__() got an unexpected keyword argument
'unset_sentinel'`. Attribution, re-derived in this pass and sharper than the class-level claim:

```shell
$ git show HEAD:django_strawberry_framework/sets_mixins.py | grep -c unset_sentinel   # 7  (incl. the field decl)
$ grep -c unset_sentinel django_strawberry_framework/sets_mixins.py                   # 5  (decl gone)
$ git diff --numstat HEAD -- django_strawberry_framework/sets_mixins.py               # 41  39
```

At `HEAD`, `django_strawberry_framework/sets_mixins.py::ActiveInputPermissionAttrs` declares
`unset_sentinel: Any = None`; the concurrent session's dirty copy has **removed** it, and the failure's
own `repr` shows the value now living on the nested `SetInputTraversal` instead — a field moved between
dataclasses with the tests not yet re-pinned. `tests/orders/test_inputs.py` is **clean at `HEAD`**
(`git status --short` reports nothing for it), so it is a `HEAD`-vintage test failing against uncommitted
production code, which is as direct as this evidence gets. `tests/test_sets_mixins.py` is itself dirty
`28/18` with the same session's partial re-pin. All three files, and `orders/`, are on the plan's
baseline-dirty list and in no cohort's write set.

**None of the four is in R3's diff, and the sweep found no new failure.** 7,119 rows pass. Every row R3
added or rewrote passes, including the three live rows that also pass at the floor.

## Floor verification — corroborated read-only, not re-run

The plan declares **one** floor-verification scope for the whole cycle, conditional on what R3 repaired,
and assigns it to **R3's builder pass**, which discharged it. `docs/builder/BUILD.md` `## Floor
verification` makes this gate the **backstop confirming it happened**, not a second owner, so it is
confirmed rather than rebuilt:

- Venv, outside the repository, built with an explicit `--python` so the shared `.venv` was never
  mutated: `<scratchpad>/dsf-floor-036`.
- Resolved versions read back in this pass by `uv pip list --python <venv>/bin/python` plus
  `<venv>/bin/python -V`: **Python 3.10.19**, `django 5.2.16`, `strawberry-graphql 0.316.0`,
  `graphql-core 3.2.12`. These are exactly the floor `docs/builder/BUILD.md` `## Floor verification`
  states canonically — read there, never from memory — and a genuinely different point in the supported
  range from the shared `.venv`.
- Recorded results, reproduced by Worker 3 to the same figures: `3 passed` on the three new live rows
  (`-k "missing_change_perm or missing_delete_perm or snapshot_carries_connection_child"`) and
  `132 passed` on the whole `examples/fakeshop/test_query/test_products_api.py`.

The scope was declared, it was run by the owning pass, and the environment it names still exists and
resolves as recorded. No unrun floor claim closes this gate.

## Deferred work catalog

The next spec author's reading list. Walked from every `bld-036-*.md` artifact's spec-reconciliation
notes, `What looks solid`, `DRY findings`, and `Notes for Worker 1` sections, plus this cycle's own
integration pass. **21 items.** Each carries its source artifact section, the licensing decision or spec
line where one exists, and a one-line description. Every figure was re-derived in this pass unless the
bullet says otherwise.

**Structural / corpus**

1. **The `0.0.14` write hardening has no owning spec, and `spec-036` is not it.** Source: R1c
   `### The headline`, R2 deferred item 1. Nine specs carry the `0_0_14` filename segment and **none**
   scopes the completion-spanning transaction, the `DjangoSchema` requirement, `Meta.select_for_update`'s
   lock semantics, single-write-alias pinning, the retryable `conflict` envelope, the immutable
   authorized-pk snapshot, the phased alias guard, the strict-`bool` authorization contract, or the
   point-in-time authorization rule; the corpus-wide grep's top hit is **`spec-039`** (10 occurrences),
   the serializer card at `0.0.13`. Licensed by **Maintainer Decision A — CORRECT CLAIMS ONLY** (build
   plan `## Maintainer decisions`), which deferred **10 of R1c's rows** (`X3` partial, `X4`-`X12`, with
   `X13` partially discharged) on the ground that folding them in would make `spec-036` retroactively the
   spec for a pipeline it never scoped. A future author should treat `spec-036`'s corrected Decisions 8,
   10 and 15 as the **boundary of what `036` claims**, not as that spec's outline. **This is a recurrence
   of a known class** — a surface with no owning spec silently inverts the specs describing it —
   previously homed on cards `051` / `052` / `064` by the `033` cycle.
2. **The broken Decision-8 anchor slug is live in two sibling specs.** Source: Slice 0 `### Notes for
   Worker 1` item 4, R2 deferred item 5. `docs/SPECS/spec-038-form_mutations-0_0_12.md` (**36** uses) and
   `docs/SPECS/spec-039-serializer_mutations-0_0_13.md` (**34** uses) both spell
   `#decision-8--…-optimizer-refetch` while their own heading reads "optimizer re-fetch", which slugs to
   `optimizer-re-fetch` — so all 70 resolve to nothing, exactly as `spec-036`'s 16 did before Slice 0
   repaired them. Out of this cycle's scope (it owns `spec-036`); R2 notes the repair is cheap only while
   every use sits in files one pass owns.
3. **No automated gate greps for a staged anchor, anywhere.** Source: R1a `### Medium:` second finding,
   R3 `### Notes for Worker 1`. Re-derived: `grep -rl 'TODO(spec-'` over `scripts/`,
   `.pre-commit-config.yaml`, and `.github/workflows/` returns **nothing**. That absence is the mechanism
   by which this card's two anchors survived four release lines, and the obligation exists only as a
   per-cycle worker action in `docs/builder/BUILD.md`'s integration pass. A repo-wide stale-anchor check
   would touch `scripts/` and CI config, both outside this cycle's maintainer-set scope. **Worth a card.**
4. **24 staged `TODO(spec-<NNN>)` anchors survive tree-wide for other specs, one of them shipped.**
   Source: R3 `### What looks solid`, this cycle's integration pass prerequisite 6. Re-derived by
   occurrence: **22 `spec-050`**, **1 `spec-060`**, **1 `spec-035`**. `spec-050` is the active in-flight
   spec so its anchors are legitimate staged work; `spec-060` is unshipped; **`spec-035` shipped in
   `0.0.10`**, so that one is the same defect this cycle discharged twice, still live in another card's
   file. Recorded, not discharged — out of scope, and pairs with item 3.
5. **184 review-finding tags across 34 grammars survive inside `spec-036`'s contract prose.** Source:
   Slice 0 `### Held-back passages`, item 1. An open **maintainer call**: a tag (`AR-H#` / `Major-#` /
   `Medium-#` / `CR-#` / `DRY-#` / `Low-1` / `P1`-`P2`) is a lookup key into the rationale companion
   rather than a chronology, both precedent companions left the shape standing, and stripping 184
   parentheticals in 34 grammars is a rewrite rather than a cut-and-paste. If a later pass is told to
   strip them, measure **occurrences** across all 34 grammars, never lines.

**Code-side, each ready to fix and each blocked only by ownership or by a dirty file**

6. **`mutations/inputs.py::FieldError`'s docstring still claims the type is frozen and byte-identical.**
   Source: R2 deferred item 4. Verified in this pass: the docstring reads "Defined and frozen here
   (spec-036 Decision 7) so … reuse the byte-identical type" at
   `django_strawberry_framework/mutations/inputs.py #"reuse the byte-identical type"` — **three lines
   above the two additive fields (`codes`, `path`) it then documents**. The spec no longer says that; the
   docstring does, and it is the last surviving statement of the retired freeze inside shipped source.
   **One correction to R2's own note:** it says the concurrent session is not editing this file; the file
   is in fact baseline-dirty `31/38`, so the item is out of scope on the baseline-dirty rule and not
   merely on partition grounds.
7. **`mutations/resolvers.py::_full_clean_or_field_errors`'s docstring says `exclude=None` for create,
   which its only caller contradicts.** Source: R1c `N8`, R2 deferred item 4 (companion). Verified live at
   `django_strawberry_framework/mutations/resolvers.py #"``exclude=None`` for create"`. Fix the docstring,
   **not** the behavior — the spec text was corrected by R2 to state that `exclude` is computed for both
   operations. File dirty `11/6`; needs its own dispatch.
8. **`examples/fakeshop/apps/products/services.py::create_users`' docstring calls `staff_<n>` a
   superuser.** Source: R3 `### Notes for Worker 1`. Verified: the docstring says
   `#"Also creates one ``staff_<n>`` superuser per unit"` while the code sets `#"is_staff=True,"` and no
   superuser flag, and `::delete_users` **never deletes superusers**
   (`#"qs = User.objects.exclude(is_superuser=True)"`), so a reader trusting the docstring expects
   `staff_<n>` to survive `delete_users all`. `test_products_api.py::_login_with_perm`'s own docstring
   states the opposite, correctly, and the whole live write-authorization tier depends on `staff_<n>`
   **not** short-circuiting on superuser. The file is **clean at `HEAD`** and so technically inside this
   cycle's file-type scope, but it is unrelated to any `spec-036` contract, so widening the cycle for it
   was declined. **A ready-to-fix one-liner** for whichever pass next opens the fakeshop seed helpers.
9. **`mutations/inputs.py::_audit_mutation_input_surface` falls back to Strawberry's `to_camel_case`
   while its sibling uses the package's `graphql_camel_name`.** Source: R1a `### Low:` first finding.
   **VERIFIED AND REJECTED — do not re-raise.** The finding inverts the contract. This audit predicts the
   name the SCHEMA will publish for a field carrying no explicit `name=`, and Strawberry's
   `NameConverter.get_graphql_name` routes that through `apply_naming_config` → `to_camel_case`, so
   Strawberry's converter is the only correct one here. Substituting the package caser would make the
   audit *miss* a real collision: a consumer-authored `field_2` beside a package-pinned `field2` reports
   two distinct names under `graphql_camel_name` and one collision under `to_camel_case`, and the SDL
   Strawberry actually emits is a single `field2` — the silent overwrite the guard exists to reject. The
   sibling at `#"graphql_camel_name(python_name)"` is answering a different question (which Django column
   an input attr maps to), not the same one differently. The `field_2` / `field2` distinction the finding
   cites is real and is preserved by the generated-input builder pinning every package-derived wire name
   explicitly, which is why the fallback is reached only for consumer-authored fields. Closed 2026-09-01
   by direct SDL measurement; the invariant now sits in that function's own docstring so the next reader
   does not re-derive it.

**Test-quality and DRY, all deferred to the pass that next opens the file for its own reasons**

10. **The 9-site denial-assertion block in `examples/fakeshop/test_query/test_products_api.py` wants an
    `_assert_denied(response)` helper.** Source: R3's Worker 3 review `### DRY findings`, judged in
    `docs/builder/bld-036-integration.md` under `### The `_assert_denied(response)` helper`. Re-derived:
    **7** occurrences at `HEAD`, **9** live. Deferred deliberately: consolidating widens a repair cycle's
    diff into seven pre-existing rows in a file clean at `HEAD`, and three of the sites carry a
    site-specific comment explaining that the denial nulls the whole `data` rather than producing an
    in-band `FieldError` — the distinction those rows exist to pin, which a helper name would hide unless
    the comments move to the call sites. The helper does clear the existence challenge on its merits
    (9 callers); it wants a pass that can also decide where that explanation lives.
11. **The grant-a-codename block in the same file is a three-way near-copy.** Source: R1d `### DRY
    findings` item 1. Two of the three are byte-identical six-line blocks; they do not reuse
    `_login_with_perm` for a real reason (they need the **user object**, not a logged-in `Client`), so the
    right shape is to split the existing helper — `_grant_perms(username, *codenames) -> User`, with
    `_login_with_perm` calling it — which also collapses three function-local `Permission` imports into
    one module-level import. Ownership is spread across `spec-043` / `spec-038` / `spec-039`, so no cohort
    of this cycle owns it.
12. **GlobalID type-name literals in the live suite are unnamed.** Source: R1d `### DRY findings` item 2.
    `products.category` 40x, `products.item` 21x — every `_global_id("products.category", …)` re-spells a
    wire contract a model rename would silently break in 40 places while the helper signature stays
    valid. Cheapest readable shape: two module constants or two thin wrappers beside `_global_id`, **not**
    a generalized factory. Same-file work.
13. **One inline mutation document duplicates a module-level wire constant.** Source: R1d `### DRY
    findings` item 3. `::test_create_item_via_serializer_multipart_upload_to_attachment` builds a local
    `createItemViaSerializer` document while `#"_CREATE_ITEM_VIA_SERIALIZER"` already spells that field at
    module level. The selections genuinely differ today, so it is not a duplicate — recorded because the
    file's own convention is "each wire contract spelled once", and two spellings is how that erodes.
14. **`types/finalizer.py::finalize_django_types` is 326 lines / 29 branch nodes with phase 2.5 as an
    inline statement sequence.** Source: R1b `DRY-3`, R2 deferred item 7. Many cards' accretion, not
    `036`'s; extracting phase 2.5 into named phase functions is a plan-level call for a future
    finalizer-decomposition spec.
15. **`mutations/sets.py`'s flavor-label and `Meta`-key literals.** Source: R1b `### Low:` Low-1. The
    flavor label `"DjangoMutation"` is hard-spelled 17x, load-bearing inside error text pinned
    byte-identically (so a rename-the-literal change, never a reword); and
    `::_materialize_merged_input` re-spells the operation-to-override-attribute mapping that
    `mutations/operations.py::_OPERATION_INPUT_OVERRIDE_ATTR` already owns, differing only in its key.
    File baseline-dirty; the cross-file literal comparison in the integration pass confirms this is
    single-file work, not cross-slice.

**Escalated contract-level questions — the maintainer's, recorded so they are not re-argued**

16. **Should `FieldError` / `NON_FIELD_ERROR_KEY` live in `mutations/inputs.py` at all?** Source: R1a
    `N6`, R2 deferred item 2, integration pass prerequisite 4. Re-derived at `HEAD`: the flavor-neutral
    `utils/` layer three write flavors plus `auth` share depends **upward** on one flavor's package at
    three sites (`utils/errors.py:33` `TYPE_CHECKING`, `utils/errors.py:57` **function-local**,
    `utils/write_values.py:42` `TYPE_CHECKING`), the function-local one paid specifically to dodge an
    import cycle. Three resolution paths recorded by R1a (leave; move to `utils/errors.py` with a
    re-export keeping both import paths and `__all__` byte-identical; move to a new neutral root module).
    Contract-level, and `FieldError` is a public root export whose module identity a consumer may have
    pinned. R2's Decision-7 edit deliberately states where the **constructors** live rather than where the
    type should, so the spec no longer implies an answer.
17. **Should `mutations/sets.py` own the cross-flavor write substrate?** Source: R1b `DRY-1` / `N10`,
    R1c `L1`, R2 deferred item 2, integration pass prerequisite 4. Re-derived at `HEAD` by AST: **25
    distinct symbols** imported out by `forms/sets.py` (23), `rest_framework/sets.py` (17) and
    `auth/mutations.py` (4); each of the six named helpers occurs **exactly once** inside
    `django_strawberry_framework/mutations/` — the `def` — so all six genuinely have zero in-subpackage
    caller. `sets_mixins.py` is the exact precedent and the home Decision 4 predicted. **One arithmetic
    correction that does not touch the substance:** R1b and the plan both say 4 private-by-name symbols;
    the distinct union is **3** (`_ValidatedMutationMeta`, `_hook_overridden`,
    `_validate_permission_classes`) — which is also R1b's own printed enumeration — and the per-importer
    occurrence count is 6. A count wrong in its *subject* rather than its digits.

**Out-of-scope doc surfaces still carrying retired claims**

18. **`spec-036-mutations-0_0_11-terms.csv` omits two shipped glossary headings.** Source: Slice 0
    `### Notes for Worker 1` item 2, R1d note 7, R2 deferred item 3. Verified: `docs/GLOSSARY.md` at
    `HEAD` carries `## \`DjangoModelPermission\`` (line 688) and `## \`DjangoMutationField\`` (line 708),
    while the CSV has **no row for either** (its single hit on those names is inside the
    `DjangoConnectionField` row's description). R2 corrected the spec's stale *argument* that they cannot
    be listed; the CSV itself is outside this cycle's scope — not a `.py` file, and `import_spec_terms`
    writes the kanban DB. **Note that a green `check_spec_glossary` does not prove the CSV is importable
    by a done-card wrap**: the checker validates the terms the CSV lists, not that the CSV lists every
    term the spec's card shipped.
19. **`docs/GLOSSARY.md` has no `DjangoSchema` entry and no mention of `FieldError.codes` / `.path`, and
    `CHANGELOG.md` `## [0.0.12]` still calls the envelope "byte-identical".** Source: R1d notes 13,
    R2 deferred item 3. The `CHANGELOG` line is the most misleading of the three, because it is a
    released note asserting exactly what this cycle retired. All three files are excluded by the
    maintainer-set scope; maintainer follow-up.
20. **DoD item 6 (and these four suite failures) need the maintainer's clean-`HEAD` tree.** Source: R1d
    note 10, R2's stated reading, and `## The four suite failures` above. "The full suite is green at the
    100% coverage gate; `ruff format` + `ruff check` are clean; no B1-B8 optimizer regression" is a
    runtime claim in a tree carrying another session's work, with coverage flags forbidden to workers.
    R2 applied R1d's option (a) — read as a historical claim about the card, like Decision 13 — so no spec
    edit follows; the *current-tree* half is what needs the clean run.

**Process observations — recorded only; this cycle lands no agentflow edits**

21. Two, both from the cycle's own execution. (a) Source: R3's Worker 3 review `### Notes for Worker 1`
    — `docs/builder/BUILD.md`'s fenced failability loop puts the anchor check **before** the pre-mutation
    copy, while `scripts/prove_failability.py` copies first and then verifies the anchor. The outcome is
    equivalent (an unmatched anchor aborts the entry before anything is written, and the copy is a read),
    but a worker following the prose and a worker running the tool are performing two different orderings
    while the prose's stated rationale is specifically about the copy. Worth one sentence in whichever
    cycle next edits that section, under `## The corpus ratchet`. (b) Source: build plan
    `### Process defect in Worker 0's own dispatch, recorded` — three concurrent same-role cohorts were
    pointed at one shared memory file and it was **clobbered rather than appended**. Cycle-scoped-per-role
    was the wrong granularity for concurrent same-role cohorts; per-cohort files would have been correct.
    No content was lost, because every cohort's findings live in its own artifact — which is exactly why
    `docs/builder/BUILD.md` makes the artifact the contract and memory a private notebook.

### Struck from the catalog: items the artifacts route forward that this cycle CLOSED

Carried here so the next author does not go fix something that is fixed, and so a later reader does not
read the routing as still-open:

- **The AR-M7 package mirror's decoupling from `optimizer/extension.py::mutation_payload_child_selections`**
  (R1d's Medium, R2 deferred item 6) — **closed by R3's Repair 5.** The mirror now derives its selection
  through that production entry point; Worker 3 verified mechanically that the symbol had exactly one
  occurrence in `tests/` / `examples/` at `HEAD`, inside a docstring, so the same mutation failed **0**
  rows before the repair and fails **3** after.
- **The package suite's blindness to a phase-2.5 ordering regression** (R1b's Medium-1) — **closed by
  R3's Repair 6b.** `tests/mutations/test_inputs.py` now carries a relation target declaring Relay
  through `Meta.interfaces = (relay.Node,)` (`::test_fk_to_meta_interfaces_relay_target_uses_globalid_id`)
  plus the payload-slot consequence at a second call site
  (`::test_meta_interfaces_primary_binds_a_node_slot_payload`), where `git grep -c 'interfaces' HEAD --
  'tests/mutations/*.py'` had been **0** across all eight modules.
- **The `FieldError` field set having no gate at all** (R1a's headline Medium) — **closed by R3's
  Repair 6a**, with two independently-failing rows (the Python attribute set, and the wire-name set as it
  reaches a client off a generated payload).
- **The two undischarged `TODO(spec-036 Slice N)` anchors** (R1a row 82, R1b High-1, R1c M5, R1d note 12)
  — **closed by R3's Repairs 1 and 2**; `grep -rn --include='*.py' 'TODO(spec-036' .` returns nothing.
- **The live write-authorization denial matrix pinned for `create` only** (R1d's SKIPPED row S4.7) —
  **closed by R3's Repair 3**; all three operations now have a live denial row, so DoD item 5's clause is
  true as written and must not be softened to match the old gap.
- **Two DRY findings R1a raised and then found already closed in the concurrent session's work** — the
  bare `codes=` literals in `utils/errors.py` (now `FIELD_ERROR_CODE_*` constants plus
  `null_field_error()` / `coded_error_extensions()`) and `editable_input_fields`' hand-rolled narrowing
  walk (now routed through `utils/inputs.py::resolve_effective_fields`). Reported as
  already-closed-in-flight per the plan's own rule; **not** this cycle's work and not open.

## Summary

Six gate commands run, five clean and one carrying only the baseline exception the plan recorded in
advance. The full sweep is **7,119 passed / 42 skipped / 4 failed**, and all four failures are the
concurrent session's uncommitted production work outrunning its own test re-pins — attributed
mechanically at the occurrence level (`ConnectionWindowBounds` 0 at `HEAD` / 5 live in a file dirty
`31/32`; `unset_sentinel` declared on `ActiveInputPermissionAttrs` at `HEAD` and removed live in a file
dirty `41/39`, with one of the three failing test files **clean at `HEAD`**), recorded as
not-worker-verifiable-at-`HEAD`, and escalated to the maintainer rather than graded against this cycle.
Nothing in R3's diff fails. Floor verification was owned and discharged by R3's builder pass and is
corroborated read-only here at the canonical floor (Python 3.10.19 / django 5.2.16 /
strawberry-graphql 0.316.0), with the shared `.venv` unmutated. The `### Deferred work catalog` carries
**21 items** and, deliberately, a second list of **six** items the artifacts route forward that this
cycle actually closed — because a catalog that carries closed work is as expensive to the next author as
one that drops open work.

The cycle's own yield, for the record: `spec-036` now states the contract that ships (66 routable rows,
56 discharged, 10 deferred under an explicit maintainer decision), its deliberative layer lives in a
companion keyed to every Decision, and the two contracts the code had genuinely skipped are closed by
six test files carrying zero production lines.

Final status: `final-accepted`.
