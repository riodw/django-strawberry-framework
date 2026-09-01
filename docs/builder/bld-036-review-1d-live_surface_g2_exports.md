# Build: R1d — conformance audit: products live write surface, the `spec-035` G2 handoff, public exports, the Definition of done

Spec reference: `docs/SPECS/spec-036-mutations-0_0_11.md` (Slices 4-5; Decisions 1, 2, 5, 13; `## Test plan`; `## Current state`; `## Out of scope`; DoD items 1, 5, 6, 7, 8)
Rationale companion: `docs/SPECS/appx/spec-036-mutations-0_0_11-rationale.md` (read; Decisions 1/2/5/13 + `## Risks and open questions`)
Status: final-accepted

This is a **conformance audit** under `docs/builder/build-036-mutations-0_0_11.md` (the `036`
residual-reconciliation cycle). No source or test file was edited. The cohort writes exactly one
file, this artifact, plus `docs/builder/worker-memory/worker-3-036.md`.

## Method — every grade measures `HEAD`, not the working tree

Snapshot commit **`7426e7e7d8aa447e89fee75088447d6a506dec12`**, materialized read-only outside the
repo at
`/private/tmp/claude-501/-Users-riordenweber-projects-django-strawberry-framework/f4a12072-1e3a-4913-8249-dd800f1972ce/scratchpad/head-036/`
(hereafter `<snap>`). No `git stash` / `git checkout` / `git restore` / `git worktree` was used
anywhere in this pass.

Snapshot integrity was re-proved per file rather than assumed — every territory file was piped from
`git show HEAD:<path>` and byte-compared against the snapshot copy:

```shell
$ for f in examples/fakeshop/apps/products/schema.py examples/fakeshop/config/schema.py \
    django_strawberry_framework/__init__.py tests/base/test_init.py \
    examples/fakeshop/test_query/test_products_api.py tests/optimizer/test_walker.py \
    django_strawberry_framework/optimizer/walker.py; do
    git show HEAD:$f | cmp -s - <snap>/$f && echo "OK  $f" || echo "DIFF $f"; done
OK  (all seven)
```

Working-tree baseline re-verified independently rather than taken from the prompt:

```shell
$ git status --short | wc -l
110
$ git status --short -- examples/fakeshop/test_query/test_products_api.py \
    examples/fakeshop/apps/products/ examples/fakeshop/config/schema.py \
    django_strawberry_framework/__init__.py tests/base/test_init.py \
    django_strawberry_framework/optimizer/walker.py tests/optimizer/test_walker.py
 M django_strawberry_framework/optimizer/walker.py
```

So in this territory only `optimizer/walker.py` is baseline-dirty; the other six are clean at `HEAD`
and live == `HEAD` for them. `docs/GLOSSARY.md`, `docs/TREE.md`, `README.md`, `docs/README.md`,
`KANBAN.md` and `KANBAN.html` are baseline-dirty and were read **only** through `git show HEAD:` —
never the working copy, never edited.

**No test was run in this pass.** A run would exercise the dirty tree and therefore say nothing about
`HEAD`; the only commands executed were read-only greps, `git show`, `scripts/check_spec_glossary.py`
(DoD item 1's own command) and `scripts/review_inspect.py`.

---

## Review (Worker 3)

### Graded contract inventory

Grades use the plan's vocabulary exactly. Citations are `AGENTS.md` rule-27 symbol-qualified;
raw `path:NN` appears only as inline review convenience, never in a citation.

| # | Contract (spec territory) | Grade | Evidence at `HEAD` |
|---|---|---|---|
| S4.1 | Slice 4: `products/schema.py` gains a `Mutation` type with `create_item` / `update_item` / `delete_item` as `DjangoMutationField`s | CONFORMS | `examples/fakeshop/apps/products/schema.py::Mutation #"create_item = DjangoMutationField(CreateItem)"` plus `update_item` / `delete_item`; the three `DjangoMutation` subclasses are `::CreateItem` / `::UpdateItem` / `::DeleteItem`, each a nested `class Meta` with `model` + `operation` |
| S4.2 | "(and at least one `Category` write)" | CONFORMS | `examples/fakeshop/apps/products/schema.py::CreateCategory` exposed as `::Mutation #"create_category = DjangoMutationField(CreateCategory)"` |
| S4.3 | "`config/schema.py` wires `mutation=Mutation` into **`strawberry.Schema(...)`**" | SUPERSEDED | `examples/fakeshop/config/schema.py #"schema = DjangoSchema("` — the schema is built as `DjangoSchema`, not `strawberry.Schema`, and the module comment states the reason: "the write pipeline refuses to run under a plain Schema". `mutation=Mutation` is wired. Attribution: the `0.0.14` cut (`CHANGELOG.md` `## [0.0.14]` `#"BREAKING: generated mutations require"`), whose release header names design cards `DONE-041`-`DONE-049`; no single card owns the requirement in the CHANGELOG text |
| S4.4 | "(each test seeded via `seed_data` / `create_users`)" | CONFORMS | Measured, not asserted — see `### Re-derived counts` row 1: 63 mutation-posting tests, 62 carry `seed_data(` / `create_users(` / `seed_cascade_split(`, the 1 residue is a false positive with no mutation in it |
| S4.5 | Live `/graphql/` create / update / delete coverage | CONFORMS | `examples/fakeshop/test_query/test_products_api.py::test_create_item_happy_path`, `::test_update_item_non_colliding_partial_update`, `::test_delete_item_happy_path` (the delete row also pins the pre-deletion snapshot with the relation populated and the id preserved) |
| S4.6 | The validation-error envelope, incl. the AR-H2 partial-update collision on `unique_item_per_category` | CONFORMS | `…::test_create_item_unique_constraint_envelope_uses_all_sentinel` and `…::test_update_item_partial_collision_on_unique_constraint_changing_only_name` |
| S4.7 | **Write authorization (AR-H3): anonymous denied AND a caller lacking the `add` / `change` / `delete` model perm denied, while a permitted caller succeeds** | **SKIPPED** (partial — the `change` / `delete` denial rows) | See `### The SKIPPED row, with its burden of proof`. Live denial rows exist for `create` only; the permitted-caller half is complete for all three operations |
| S4.8 | The visibility-scoped update/delete (a caller who cannot *see* a private `Item` gets not-found) | CONFORMS | `…::test_visibility_scoped_update_delete_hidden_private_row_is_not_found` — pins update **and** delete against a hidden row (`node is None`, `errors[].field == ["id"]`, row unchanged / still present) with the write perm deliberately **held**, plus a positive contrast on the visible row |
| S4.9 | A wrong-type `GlobalID` on `categoryId` → `FieldError` (AR-H4) | CONFORMS | `…::test_create_item_wrong_type_global_id_on_category_id_is_field_error`, with sibling rows for the `id:` argument on update (`…::test_update_item_wrong_type_global_id_on_id_is_field_error`) and delete |
| S4.10 | A `CaptureQueriesContext` assertion: relations kept, bounded query count, no accidental lazy query | CONFORMS | `…::test_g2_mutation_response_keeps_relation_with_bounded_query_count` — absolute count 14 with a per-query breakdown in-comment, plus the load-bearing property asserted directly (exactly 1 real `products_item` SELECT and 2 real `products_category` SELECTs, so an N+1 or deferred lazy refetch adds rows and fails). Not an observability-only assertion |
| S5.1 | Slice 5: GLOSSARY promotes `DjangoMutation` / Input type generation / `FieldError` envelope to `shipped (0.0.11)` | CONFORMS | `git show HEAD:docs/GLOSSARY.md` — `## \`DjangoMutation\``, `## Input type generation`, `## \`FieldError\` envelope`, each `**Status:** shipped (\`0.0.11\`)` |
| S5.2 | GLOSSARY adds the net-new `DjangoMutationField` **and `DjangoModelPermission` / write-auth** entries with Public-exports + Index rows | CONFORMS | `## \`DjangoMutationField\`` and `## \`DjangoModelPermission\`` both present; Public-exports bullet and Index row for `DjangoMutationField` both present |
| S5.3 | GLOSSARY pins the final public names (inputs / payload `node`·`result` slot / `FieldError` / `<field>_id` / `"__all__"` sentinel) | CONFORMS | Named in the `DjangoMutation` / `DjangoMutationField` / `FieldError` envelope / Input type generation entries at `HEAD` |
| S5.4 | Append the G2-handoff-discharged note to the `only()` projection entry | CONFORMS | `docs/GLOSSARY.md` `## \`only()\` projection` `#"the G2 mutation gate is exercised **live** by the products write surface"` |
| S5.5 | `docs/README.md` / `README.md`: "move mutations from **'Coming next'** to **'Shipped today'**" | STALE-DESCRIPTION | The contract is satisfied — `README.md #"All three mutation flavors ship today"` and `docs/README.md #"mutations + auto-generated \`Input\` types (new in \`0.0.11\`)"` — but neither heading the clause names exists at `HEAD`: `README.md`'s sections are `## Status` / `## Get started`, and `docs/README.md`'s is `## Today and coming next`. A reader following the clause finds no such headings |
| S5.6 | `GOAL.md`: the DRF-migration mutation diff references a shipped base | CONFORMS | `GOAL.md #"The \`DjangoMutation\` base ships today (\`0.0.11\`)"`, with `::CreateCategory` still the declared shape |
| S5.7 | `TODAY.md`: products demonstrates a write surface | CONFORMS | `TODAY.md #"**\`DjangoMutation\` write surface**"` plus the "Mutations on products today" section the spec names |
| S5.8 | `CHANGELOG.md` `[Unreleased]` bullets only if the Slice 5 prompt requested it | CONFORMS (historical) | `CHANGELOG.md` carries a `## [0.0.11] - 2026-06-19` section describing the mutation foundation; the heading promotion is the joint cut's, consistent with the spec's own `Status:` line |
| S5.9 | `KANBAN.md`: card to Done with the structured `SpecDoc` reference | CONFORMS | `git show HEAD:KANBAN.md` `#"### [DONE-036-0.0.11 - Mutations + auto-generated Input types]"`, `- Status: Done` |
| S5.10 | "**No version-file edits**" in Slice 5 | CONFORMS (historical) | See D13.a |
| D1 | Decision 1: the spec lives at `docs/SPECS/spec-036-mutations-0_0_11.md` | CONFORMS | The file is at that path with companions `…-terms.csv` / `…-rationale.md` under `docs/SPECS/appx/` |
| D2.a | Decision 2: this card ships the model-driven foundation end-to-end (base, generated inputs, resolvers, envelope, optimizer + permission composition, products live surface) | CONFORMS | `django_strawberry_framework/mutations/` carries `inputs.py` / `sets.py` / `resolvers.py` / `fields.py` / `permissions.py`; the products live surface is S4.1-S4.10 |
| D2.b | "**Uploads** … This card leaves an input-converter seam (a per-field-type input mapping) so 037 plugs `Upload` in without re-opening the generator" | SUPERSEDED | `DONE-037-0.0.11` shipped and the seam is filled: `docs/README.md #"the generated \`DjangoMutation\` input mapping of \`FileField\` / \`ImageField\` editable columns"`. Consequently `examples/fakeshop/apps/products/models.py::Item #"attachment = models.FileField("` is on the write surface while `::CreateItem` declares no `Meta.exclude` — so Decision 6's CR-6 arm ("the generator raises `NotImplementedError` for a `FileField` / `ImageField`") no longer describes `HEAD`. The generator half is **R1a's** row; recorded here because the falsifying evidence is in my territory |
| D2.c | "**Form-based mutations** — `0.0.12`" | CONFORMS | `django_strawberry_framework/forms/sets.py`; the spec already spells the card `DONE-038-0.0.12` |
| D2.d | "**DRF serializer + auth mutations** — `0.0.13`" | STALE-DESCRIPTION | Both shipped; the spec's own `## Out of scope` still spells them `TODO-ALPHA-039-0.0.13` / `TODO-ALPHA-040-0.0.13` (see OS3) |
| D2.e | "The **`FieldError` envelope is defined and frozen in this card**" so the flavors "reuse the byte-identical type" | SUPERSEDED | The **sharing** holds and is provable: exactly one `class FieldError` exists in the whole snapshot (`django_strawberry_framework/mutations/inputs.py::FieldError`), and `forms/` / `rest_framework/` / `auth/` all import from `..mutations.inputs` (e.g. `django_strawberry_framework/rest_framework/resolvers.py #"from ..mutations.inputs import NON_FIELD_ERROR_KEY, FieldError"`). The **freeze** does not: the type grew two additive fields — `::FieldError #"codes: list[str] = strawberry.field(default_factory=list)"` and `#"path: list[str] = strawberry.field(default_factory=list)"`. Attribution: commit `951945b7` (2026-07-01, the `0.0.14` write-side hardening — its body names `select_for_update` and the DRF matrix); no card id in the message. The live wire contract already selects the new field: `examples/fakeshop/test_query/test_products_api.py #"errors { field messages codes }"` |
| D5.a | Decision 5: **four** net-new public symbols re-exported from the root and added to `__all__` | CONFORMS | `django_strawberry_framework/__init__.py #"__all__ = ("` carries `DjangoModelPermission`, `DjangoMutation`, `DjangoMutationField`, `FieldError`; the import is `#"from .mutations import ("` |
| D5.b | `DjangoMutationField` is assigned **without** a class-attribute annotation and types the field from the generated `<Name>Payload` via a `strawberry.lazy` forward-ref | CONFORMS | `examples/fakeshop/apps/products/schema.py::Mutation` assigns 13 unannotated `DjangoMutationField(...)` attributes; `docs/GLOSSARY.md` `## \`DjangoMutationField\`` states the same contract |
| D5.c | The operation is selected by `Meta.operation` ∈ `{"create","update","delete"}`, not a base class per operation | CONFORMS | `::CreateItem` / `::UpdateItem` / `::DeleteItem` differ only in `operation`; no per-operation base class exists in `django_strawberry_framework/mutations/sets.py` |
| D5.d | `_resolve_model(meta)` is a forward-compat seam so the `038` / `039` flavors supply the model differently | CONFORMS | Base `django_strawberry_framework/mutations/sets.py::DjangoMutation._resolve_model`, overridden at `django_strawberry_framework/forms/sets.py #"def _resolve_model"` and `django_strawberry_framework/rest_framework/sets.py #"def _resolve_model"` — exactly the predicted consumers |
| D13.a | Decision 13: no slice edits `pyproject.toml`, `__version__`, `tests/base/test_init.py::test_version`, or `uv.lock` | CONFORMS (historical) | Graded as a **historical claim about the card**, the only readable one: `HEAD` is far past `0.0.11` (`django_strawberry_framework/__init__.py #"__version__ = \"0.0.15\""`, `tests/base/test_init.py::test_version` asserting `"0.0.15"`). `pyproject.toml #"dynamic = [\"version\"]"` + `[tool.hatch.version]` confirms the single-source rule the Decision rests on is intact |
| D13.b | No `CHANGELOG.md` release heading promoted by this card | CONFORMS (historical) | `CHANGELOG.md` `## [0.0.11] - 2026-06-19` exists and is the joint cut's, matching the spec's own `Status:` line |
| TP.1 | `## Test plan`: placement follows the `test_query/` README live-HTTP-priority rule | CONFORMS | The live consumer behavior is in `examples/fakeshop/test_query/test_products_api.py`; package-internal mechanics are under `tests/mutations/`; `examples/fakeshop/test_query/README.md #"Sibling live suites now cover the other fakeshop apps"` names the suite |
| TP.2 | "**every** live fakeshop mutation test starts with `seed_data(N)` / `create_users(N)`" | CONFORMS | Same measurement as S4.4 — a positively-spelled universal, so it was checked by enumerating the population, not by a negative-vocabulary sweep |
| TP.3 | Live tier owns: success payloads, the validation envelope, **write-authorization behavior**, `GlobalID` behavior, response shape, bounded query count | CONFORMS except the authorization denial axis | Every other named item is pinned (S4.5, S4.6, S4.9, S4.10); the authorization gap is S4.7 |
| TP.4 | Package tier owns generated-class caches and shape-derived naming | CONFORMS | `tests/mutations/test_inputs.py` exists at `HEAD` and is **R1a's** territory to grade cell by cell; recorded here only as "the assignment is honored, the tier exists" |
| TP.5 | Package tier owns duplicate-name `ConfigurationError`s | CONFORMS | Same — `tests/mutations/test_inputs.py` / `test_sets.py`, R1a / R1b territory |
| TP.6 | Package tier owns the **exact** `only_fields` / `deferred_loading` plan state (AR-M7) | CONFORMS | `tests/optimizer/test_walker.py::test_mutation_refetch_plan_drops_only_keeps_relations` asserts `plan.only_fields == ()`, `plan.select_related == ("category",)`, `plan.prefetch_related != ()` **and** the applied queryset's `query.deferred_loading == (frozenset(), True)` — the exact state, not observability. See the Medium finding on how it reaches that plan |
| TP.7 | Package tier owns custom-input mapping failures | CONFORMS | R1a / R1b territory (`tests/mutations/test_inputs.py`, `test_sets.py`) |
| TP.8 | Package tier owns async-pipeline internals | CONFORMS | R1c territory (`tests/mutations/test_resolvers.py`) |
| TP.9 | Package tier owns the `transaction.atomic` rollback boundary | CONFORMS with a superseded premise | `tests/mutations/test_write_transaction.py` exists (R1c's to grade); the *boundary itself* moved at `0.0.14` — the transaction now spans response completion under `DjangoSchema`, and the live proof of that lives in `examples/fakeshop/test_query/test_mutation_atomicity.py`, a file the spec's ownership split does not know about. Routed to R1c / R2 |
| TP.10 | Package tier owns M2M behavior "**because products exposes no M2M model**" | CONFORMS | The premise re-derived at `HEAD`: `grep -c 'ManyToMany' <snap>/examples/fakeshop/apps/products/models.py` → **0** (the other fakeshop apps do have them: glossary 2, library 2, kanban 4, scalars 0). The stated reason still holds |
| TP.11 | `tests/optimizer/test_walker.py` (extend) — a mutation re-fetch queryset produces a plan with empty `only_fields` while select/prefetch survive | CONFORMS | Same node id as TP.6, plus `::test_mutation_queryset_drops_only_keeps_select_prefetch`, `::test_mutation_to_one_relation_applies_no_only`, `::test_mutation_to_many_prefetch_no_deferred_loading`, `::test_mutation_scalar_only_connection_window_no_only` and `::test_only_gate_is_query_only` (`_enable_only_for_operation(MUTATION) is False`) |
| DoD1.a | DoD 1: the spec is at the canonical structured filename with its `-terms.csv`, and `check_spec_glossary.py` reports `OK: <N> terms` | CONFORMS | Command run **as written**: `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-036-mutations-0_0_11.md` → `OK: 38 terms - all have glossary entries and at least one spec link.`, **exit 0**. (The precedent cycle's pre-archive-path failure does not recur here) |
| DoD1.b | "The net-new symbols **without a glossary heading yet** — `DjangoMutationField` and `DjangoModelPermission` — are intentionally absent from the CSV" | STALE-DESCRIPTION | Both now have headings: `git show HEAD:docs/GLOSSARY.md` carries `## \`DjangoModelPermission\`` and `## \`DjangoMutationField\``, so the stated *reason* for the omission is false. The CSV itself is outside this cycle's scope (maintainer call); the stale argument is R2's. Same defect Slice 0 flagged in the moved Risks item |
| DoD5.a | DoD 5: "Products exposes a `Mutation` (**create/update/delete over at least `Item` and `Category`**)" | STALE-DESCRIPTION | `Category` has **create only** at `HEAD`; there is no `updateCategory` / `deleteCategory` on the shipped surface. The authorizing `## Slice checklist` asks only for "at least one `Category` write", which *is* satisfied — so the DoD overstates the contract the slice was built against. Under the literal DoD reading alone this is a code gap; see `### The DoD-5 second reading` for the burden of proof and R2's two options |
| DoD5.b | DoD 5's live matrix (happy paths, envelope + AR-H2, non-colliding partial update, write auth, visibility scoping, wrong-type `GlobalID`, the `CaptureQueriesContext` G2 assertion) | CONFORMS except write auth | S4.5-S4.10; the write-authorization cell is S4.7 (SKIPPED, partial) |
| DoD6 | DoD 6: full suite green at `fail_under = 100`, `ruff` clean, no B1-B8 optimizer regression, no read-side surface change | Not worker-verifiable at `HEAD` | Per `docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`, a runtime/test claim is not worker-verifiable in a tree carrying 110 dirty paths, and coverage flags are forbidden. Recorded and escalated rather than graded — see `### Notes for Worker 1` |
| DoD7 | DoD 7: GLOSSARY / docs/README / README / GOAL / TODAY / CHANGELOG / KANBAN all reflect the shipped state | CONFORMS | S5.1-S5.9, all read through `git show HEAD:` |
| DoD8.a | DoD 8: the version boundary — `pyproject.toml`, `__version__`, `test_version`, `uv.lock` unchanged, no release heading promoted | CONFORMS (historical) | D13.a / D13.b. **Historical reading applied**, stated explicitly because the live reading is trivially false at `0.0.15` |
| DoD8.b | DoD 8: "The **four** net-new public symbols … are added to `__all__` and the `__all__` exports pin is updated accordingly" | CONFORMS | All four in `django_strawberry_framework/__init__.py #"__all__ = ("`; the pin is `tests/base/test_init.py::test_public_api_surface_is_pinned` (full 37-name tuple) and the identity pin `::test_reexported_types_resolve_to_canonical_subpackage_definitions` asserts each of the four `is` its `django_strawberry_framework.mutations` definition. "Four net-new" survives later cards: the `SerializerMutation` family is a lazy `__getattr__` export deliberately **absent** from `__all__` (`#"_DRF_SOFT_EXPORTS"`), and the later additions (`DjangoSchema`, `DjangoMutationExecutionContext`, the policy symbols) are other cards' and are attributed as such in the pin's own comment |
| CS1.a | `## Current state`: "**No `mutations/` module, no write resolvers, no input generation** … neither exists on disk. The package root `__init__.py` exports no mutation symbol and `__all__` names none" | CONFORMS (dated observation) | False at `HEAD` and licensed to be: `## Current state` opens "A true description of the repo as this spec is authored", and `docs/builder/BUILD.md` `### \`## Current state\`: observations stand, predictions do not` keeps a falsified observation. It reads present-tense, so R2 should consider a tense pass — but the clause is not a defect |
| CS1.b | The same bullet's quotation of `docs/TREE.md`: `mutations/` and `tests/mutations/` are both "planned by `TODO-ALPHA-036-0.0.11`" | STALE-DESCRIPTION | `git show HEAD:docs/TREE.md` now renders `├── mutations/    # Mutations subsystem - the write side (spec-036).` — the quoted string is gone from the source it quotes, so the quotation resolves to nothing a reader can check |
| CS2 | "The set-family layout is the precedent" — `filters/` and `orders/` are each a four-module subpackage (`base` / `factories` / `inputs` / `sets`) | CONFORMS | `ls <snap>/django_strawberry_framework/filters` and `…/orders` → exactly `__init__.py`, `base.py`, `factories.py`, `inputs.py`, `sets.py` in both |
| CS3.a | "`types/base.py` holds `DEFERRED_META_KEYS = {"aggregate_class", "fields_class", "search_fields"}` and `ALLOWED_META_KEYS`" — membership and location | CONFORMS | `django_strawberry_framework/types/base.py #"DEFERRED_META_KEYS: frozenset[str] = frozenset("` with exactly `{"aggregate_class", "fields_class", "search_fields"}`; `#"ALLOWED_META_KEYS: frozenset[str] = frozenset("` beside it |
| CS3.b | The same clause's **spelling** of the literal (`= {...}`) | STALE-DESCRIPTION (Low) | The declaration is a typed `frozenset(...)` call at `HEAD`, so the quoted source line does not exist. Membership is unchanged, which is what Decision 12 actually depends on; R1b owns the byte-unchanged-ness half |
| CS4 | "The G2 gate is already in place and waiting for this card" — `walker.py::_enable_only_for_operation`, shipped `0.0.10` | CONFORMS | `django_strawberry_framework/optimizer/walker.py #"def _enable_only_for_operation"` at `HEAD` (read from the snapshot — this file is baseline-dirty, so the live copy was deliberately not used) |
| CS5 | "The permission seam is shipped … the four products `schema.py` types already call the cascade inside their hooks" | CONFORMS | `grep -c 'apply_cascade_permissions' <snap>/examples/fakeshop/apps/products/schema.py` → 9 (import + the four types' hooks and their docstrings) |
| CS6 | "`Meta.primary` resolution is shipped … `registry.py::TypeRegistry` resolves via `get(model)` / `primary_for(model)`" | CONFORMS | `django_strawberry_framework/registry.py::TypeRegistry.get` and `::TypeRegistry.primary_for` both present |
| CS7.a | "**The products write target is connections-only today** … there is **no** `Mutation` type" | CONFORMS (dated observation) | Falsified at `HEAD` (S4.1) and licensed as a dated observation, same rule as CS1.a. Reads present-tense; R2's tense call |
| CS7.b | The same bullet: "`config/schema.py` constructs `strawberry.Schema(query=..., ...)` with no `mutation=`" | STALE-DESCRIPTION | Doubly stale: `mutation=` is wired **and** the constructor is `DjangoSchema`. The forward-looking half of the same claim is the SUPERSEDED row S4.3, so R2 must fix both together or the spec will describe two different schema classes |
| CS8 | "The four models (`Category` / `Item` / `Property` / `Entry`) are **plain editable Django models** with FK relations and `UniqueConstraint`s — a realistic write surface (the `unique_item_per_category` constraint exercises the create error path)" | STALE-DESCRIPTION | The constraint half holds (`examples/fakeshop/apps/products/models.py::Item.Meta #"constraints = ["` with `unique_item_per_category`, exercised by S4.6). "Plain" no longer does: `::Item #"attachment = models.FileField("` puts a file column on the model, which is the whole reason D2.b is superseded |
| CS9 | "**The sibling `0.0.11` card is unshipped.** `TODO-ALPHA-037-0.0.11` … is **planned, not started**" | STALE-DESCRIPTION | `git show HEAD:KANBAN.md #"### [DONE-037-0.0.11 - Upload scalar and file / image field mapping]"`. This is a live claim about another card's state, not an observation of the pre-build repo, so the vintage licence does not cover it |
| OS1 | `## Out of scope`: `Upload` scalar + file/image mapping → `DONE-037-0.0.11`, "this card leaves a per-field input-converter seam for it" | CONFORMS | Card id already correct in this clause; the seam was consumed (D2.b) |
| OS2 | Form-based mutations → `0.0.12` (`DONE-038-0.0.12`) | CONFORMS | Card id correct; `django_strawberry_framework/forms/` shipped |
| OS3 | DRF serializer + auth mutations → `0.0.13`, spelled `TODO-ALPHA-039-0.0.13` / `TODO-ALPHA-040-0.0.13` | STALE-DESCRIPTION | `git show HEAD:KANBAN.md` carries `### [DONE-039-0.0.13 - DRF serializer mutations (\`SerializerMutation\`)]` and `### [DONE-040-0.0.13 - Auth mutations (login / logout / register)]`. Note for R2: this class is **already carded** — see `### Re-derived counts` row 4 |
| OS4 | "**Nested writes / bulk mutations** … **not on the alpha roadmap**; `0.0.11` writes one root model with relations as existing ids" | SUPERSEDED | The nested half shipped at `0.0.13`: `django_strawberry_framework/rest_framework/inputs.py::NestedSerializerConfig` is an opt-in, descriptor-keyed, **recursive** nested serializer input (`Meta.nested_fields = {"items": NestedSerializerConfig(...)}`), root-exported lazily via `django_strawberry_framework/__init__.py #"_DRF_SOFT_EXPORTS"`. Attribution: `spec-039` / `DONE-039-0.0.13`. Bulk / batch is still out, so the clause needs splitting, not deleting |
| OS5 | Field-level *read* gates (`FieldSet.check_<field>_permission`) → deferred to `0.1.1`; write authorization is **not** deferred | CONFORMS | `0.1.1` has not shipped (`__version__ == "0.0.15"`); `docs/GLOSSARY.md` `## \`FieldSet\`` is still `**Status:** planned for \`0.1.1\``. The clause names no card id, so it escaped the renumber rot that hit the `046`→`059` FieldSet citations elsewhere in the corpus |
| OS6 | Relay `clientMutationId` / single-`input` wrapping not adopted | CONFORMS | `grep -rio 'clientMutationId\|client_mutation_id' <snap>/{django_strawberry_framework,tests,examples}` → **0** occurrences |
| OS7 | Version bump owned by the joint `0.0.11` cut | CONFORMS (historical) | D13.a / D13.b |

#### Summary count

Re-derived mechanically from the rendered table rather than tallied by hand, because a count asserted
in the same breath as the thing it counts is routinely wrong
(`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`). The row ids
are unique, so the id column is the population and the grade column is the partition:

```shell
$ awk '/^\| # \| Contract/,/^#### Summary count/' <this file> \
    | grep -E '^\| (S4|S5|D1|D2|D5|D13|TP|DoD|CS|OS)' > /tmp/rows.txt
$ wc -l < /tmp/rows.txt
70
$ awk -F'|' '{gsub(/^ +| +$/,"",$4); print $4}' /tmp/rows.txt | sort | uniq -c | sort -rn
  43 CONFORMS
   9 STALE-DESCRIPTION
   6 CONFORMS (historical)
   4 SUPERSEDED
   2 CONFORMS (dated observation)
   1 STALE-DESCRIPTION (Low)
   1 Not worker-verifiable at `HEAD`
   1 CONFORMS with a superseded premise
   1 CONFORMS except write auth
   1 CONFORMS except the authorization denial axis
   1 **SKIPPED** (partial — the `change` / `delete` denial rows)
```

| grade | rows | which spellings collapse into it |
|---|---|---|
| **Total rows** | **70** | the 70 unique row ids `S4.1` … `OS7` |
| CONFORMS | 54 | 43 plain + 6 `(historical)` + 2 `(dated observation)` + 1 `with a superseded premise` (TP.9) + 2 `except (the) write auth(orization denial axis)` (TP.3, DoD5.b), whose exception is routed through S4.7 |
| SUPERSEDED | 4 | S4.3, D2.b, D2.e, OS4 |
| STALE-DESCRIPTION | 10 | 9 plain + 1 `(Low)` (CS3.b) |
| RENAMED | 0 | — (one RENAMED candidate exists on **R1b's** inventory, not mine: Decision 4's `tests/test_permissions.py` path — see note 12) |
| **SKIPPED** | **1** | S4.7 |
| Not worker-verifiable at `HEAD` | 1 | DoD6 — deliberately outside all five grades, recorded and escalated |

54 + 4 + 10 + 0 + 1 + 1 = **70**, which is the measured row count.

**Routing totals:** 15 rows route to R2 (4 SUPERSEDED + 10 STALE-DESCRIPTION + the DoD6 escalation),
1 routes to R3 (S4.7), 54 need no action.

### Re-derived counts

Every figure this artifact states, with the command that produced it. Where a claim is spelled
positively (`every`, `all`), the population was **enumerated** rather than swept for a negative
vocabulary.

1. **"Every live fakeshop mutation test starts with `seed_data(N)` / `create_users(N)`"** (rows S4.4,
   TP.2). A Python pass over `<snap>/examples/fakeshop/test_query/test_products_api.py` split the file
   at `^def test_`, kept every block that posts a mutation (contains `mutation(` or a
   `_CREATE_/_UPDATE_/_DELETE_` wire constant), and checked each for `seed_data(` / `create_users(` /
   `seed_cascade_split(`: **63 mutation-posting tests, 62 seeded, 1 residue**. The residue —
   `::test_get_query_with_pathologically_nested_param_returns_400_not_500` — was read in full and
   posts no mutation (it is a GET-parse row; it matched on a `param` fixture in its signature), so the
   universal holds at 63/63 of the real population.
2. **The authorization-denial population** (row S4.7). `grep -rc 'Not authorized'` across
   `<snap>/examples/fakeshop/test_query/*.py` → 3 files with any hits (`test_client_api.py` 2,
   `test_error_policy_api.py` 2, `test_products_api.py` 9); the 9 attribute to **8** tests, all of
   them `create`. The message is the single denial string, so this is a population, not a vocabulary
   sample.
3. **The spec's surviving `TODO-ALPHA-*` ids.** `grep -ohE 'TODO-(ALPHA|BETA)[A-Za-z0-9._-]*'` →
   **13** occurrences at `HEAD`, **8** in the spec after Slice 0's move (2 `036`, 2 `037`, 1 `038`,
   2 `039`, 1 `040`) plus 4 in the new companion. The `HEAD` figure agrees with `KANBAN.md`'s own
   measured "036=13".
4. **The territory source file's rotted card ids.**
   `git show HEAD:examples/fakeshop/apps/products/schema.py | grep -o 'TODO-BETA-[0-9]*-[0-9.]*' | sort | uniq -c`
   → `TODO-BETA-046-0.1.1` **7**, `TODO-BETA-047-0.1.2` **5**, `TODO-BETA-049-0.1.3` **6**,
   `TODO-BETA-062-0.1.5` **1** = **19**. The first 18 are the board's already-carded "18 rotted
   occurrences"; the 19th needs only the renumber's +1. Confirmation, not a new finding.
5. **M2M in products** (row TP.10). `grep -c 'ManyToMany'` per fakeshop app `models.py` → products
   **0**, glossary 2, library 2, kanban 4, scalars 0. The test plan's stated reason holds.
6. **`clientMutationId`** (row OS6). `grep -rio 'clientMutationId\|client_mutation_id'` over
   `<snap>/{django_strawberry_framework,tests,examples}` → **0**.
7. **`FieldError` is one class** (row D2.e). `grep -rn 'class FieldError' <snap>` → **1**
   (`django_strawberry_framework/mutations/inputs.py::FieldError`); the token occurs **171** times
   across package `.py` files, spread forms 8 / auth 2 / rest_framework 27 / mutations 66 / utils 55.
8. **`mutation_payload_child_selections` is untested by name** (Medium finding).
   `grep -rno` over `<snap>/{django_strawberry_framework,tests,examples}` → **6** occurrences: 2 in
   `optimizer/extension.py` (definition + docstring), 3 in `mutations/resolvers.py`, 1 in
   `tests/optimizer/test_walker.py` — that one inside a docstring.
9. **Public exports** (rows D5.a, DoD8.b). `django_strawberry_framework/__init__.py #"__all__ = ("`
   holds **37** names; `tests/base/test_init.py::test_public_api_surface_is_pinned` asserts the same
   37-name tuple. All four `spec-036` symbols present in both.

### The SKIPPED row, with its burden of proof

**S4.7 — the live write-authorization denial matrix is pinned for `create` only.**

The contract, twice stated. `## Test plan`, live tier:
"**write authorization** (AR-H3) — an anonymous request is denied (top-level error, no write) and a
caller lacking the `add` / `change` / `delete` model perm is denied while a permitted caller
succeeds". DoD item 5 repeats it: "**write authorization** (anonymous denied, a caller missing the
`add`/`change`/`delete` model perm denied, a permitted caller succeeds — AR-H3)". A Definition-of-done
item gets no vintage licence (`docs/builder/BUILD.md` `### \`## Current state\`: observations stand,
predictions do not`), so this is a live completion claim.

**The cells, checked against real test node ids** (never against a test's name or docstring):

| operation | permitted caller succeeds | anonymous denied | lacks the model perm denied |
|---|---|---|---|
| `create` (`add_item`) | `test_products_api.py::test_create_item_happy_path` (grants `add_item` explicitly) | `::test_create_item_anonymous_is_denied_top_level_error_no_write` | `::test_create_item_missing_model_perm_is_denied_no_write` |
| `update` (`change_item`) | `::test_update_item_non_colliding_partial_update` (grants `change_item`) | **none** | **none** |
| `delete` (`delete_item`) | `::test_delete_item_happy_path` (grants `delete_item`) | **none** | **none** |

**Where I looked.**

1. Per-file occurrence sweep of the denial message across the whole live tier —
   `grep -rc 'Not authorized' <snap>/examples/fakeshop/test_query/*.py` → only three files have any:
   `test_client_api.py` 2, `test_error_policy_api.py` 2, `test_products_api.py` 9.
2. Attribution of every one of those 9 to a test and to the operations its body touches (a Python
   pass over the file's `def test_` blocks, not a line grep). All **8** tests that assert a denial
   post a **create**: `createItem` (3, one of them the `TestClient.login()` bracket), `createItemViaForm`
   (2), `createItemViaSerializer` (2), `submitPing` (1). Zero post `updateItem` or `deleteItem`.
3. The negative update/delete rows that *do* exist were read in full and are a different contract:
   `::test_visibility_scoped_update_delete_hidden_private_row_is_not_found` deliberately **holds**
   `change_item` + `delete_item` so the visibility miss is isolated from an authorization denial (its
   own docstring says so), and `::test_update_item_wrong_type_global_id_on_id_is_field_error` /
   `::test_update_item_malformed_id_is_field_error_no_coercion_crash` are decode rows.
4. Sibling-tier check, so the gap is not merely relocated: the package tier **does** pin the
   per-operation codename matrix — `tests/mutations/test_permissions.py::test_create_perm_does_not_authorize_update_or_delete`
   and `::test_change_and_delete_perms_authorize_their_operations`, plus
   `::test_operation_action_map_is_pinned`. So the *behavior* is implemented and pinned; what is
   missing is the tier the spec assigns it to.

**Why the absence is real rather than a search miss.** The denial surface has exactly one message
string (`"Not authorized"`, asserted in all 8 rows), so a row asserting a denial cannot avoid it; the
message sweep is therefore a population, not a vocabulary sample. Two independent instruments agree:
the message sweep and the per-test operation attribution.

**What would have to exist.** Two live rows in `examples/fakeshop/test_query/test_products_api.py`,
each ~20 lines and each reusable from the existing helpers:

- `test_update_item_missing_change_perm_is_denied_no_write` — `_login_with_perm("view_item_1", "add_item")`
  (holds `add`, lacks `change`), post `_UPDATE_ITEM` against a visible row, assert
  `payload["data"] is None`, `"Not authorized" in payload["errors"][0]["message"]`, and the row
  unchanged in the DB. Holding `add_item` is what makes the row distinguishing: it proves the check is
  per-operation rather than "any products write perm".
- `test_delete_item_missing_delete_perm_is_denied_no_write` — the same shape over `_DELETE_ITEM`, and
  the row still present afterwards.

An anonymous update/delete pair is optional: the anonymous arm is operation-independent in
`DjangoModelPermission` (no `request.user`), so one anonymous row per operation adds little, and the
honest minimum is the two missing-codename rows. Repair is confined to a test file that is **clean at
`HEAD`**, so `docs/builder/build-036-mutations-0_0_11.md`'s conditional hot-path declaration resolves
to **`none`** and no floor run is implicated.

**Live-tree re-check owed before repair** (the plan's rule): `test_products_api.py` is clean at `HEAD`
and clean in the working tree as of this pass, so the concurrent session has not closed it — but R3
must re-check immediately before writing, because the concurrent session is actively extending the
write surface.

### The DoD-5 second reading

DoD 5 says "create/update/delete over at least `Item` **and** `Category`". At `HEAD` the shipped
products surface exposes `createCategory` and nothing else for `Category`
(`examples/fakeshop/apps/products/schema.py::Mutation` — the 13 fields are 4 `DjangoMutation` writes,
4 form writes, 2 plain-form writes, 3 serializer writes; only one names `Category`).

Where I looked, and what makes this a description defect rather than a code gap: the authorizing
`## Slice checklist` sub-bullet asks for "`create_item` / `update_item` / `delete_item` (**and at
least one `Category` write**)", which is satisfied exactly. A repo-wide sweep for the missing
operations (`grep -rn 'updateCategory\|deleteCategory\|UpdateCategory\|DeleteCategory' <snap>/{examples,tests,django_strawberry_framework}`,
13 hits) finds them only in two places, neither of them the shipped surface: `tests/mutations/test_resolvers.py`
declares ad-hoc `UpdateCategory` / `DeleteCategory` classes as fixtures, and
`examples/fakeshop/test_query/test_multi_db.py` builds a **test-local** schema exposing
`updateCategory` behind `FAKESHOP_SHARDED` (it teardown-restores the default schema).

So R2 has two options and should pick deliberately:

1. **Reword DoD 5** to match its own slice checklist ("create/update/delete over `Item`, plus at least
   one `Category` write"). Recommended — it makes the DoD state the contract the build was accepted
   against.
2. **Treat it as a code gap** and route `updateCategory` / `deleteCategory` to R3. Costs two mutation
   classes, two `Mutation` fields and their live rows, and widens the shipped example schema for a
   contract nothing else asks for.

Graded STALE-DESCRIPTION on option 1's reading, with option 2 recorded so the choice is visible.

### High:

None.

### Medium:

#### The `AR-M7` package mirror asserts the exact state from a hand-built selection, not from the mutation code path

`tests/optimizer/test_walker.py::test_mutation_refetch_plan_drops_only_keeps_relations` is the
package half of the G2 handoff and it does assert the exact state (`only_fields == ()`,
`select_related == ("category",)`, `prefetch_related != ()`, `deferred_loading == (frozenset(), True)`).
But it reaches that plan by handing `plan_optimizations` a **hand-written** selection list plus a
hand-built `info` (`::_op_info(OperationType.MUTATION)`), and its own docstring says so: "The exact
selection **mirrors** what `mutation_payload_child_selections` hands `plan_optimizations`".

The coupling is unpinned. `mutation_payload_child_selections` is defined at
`django_strawberry_framework/optimizer/extension.py #"def mutation_payload_child_selections"` and
called from `django_strawberry_framework/mutations/resolvers.py`; a token sweep across the package,
`tests/` and `examples/` finds **6** occurrences and **not one of them is executable test code** —
the only occurrence under `tests/` is inside that docstring. So if the production flattening changed
(node children no longer flattened to the node-type selection, or the mutation `info` no longer
reaching the planner), the mirror would keep passing while claiming to mirror something it no longer
mirrors.

Why Medium and not High: the live tier does exercise the real path, and its absolute-count assertion
(S4.10) is distinguishing — a lost `select_related` shows up as extra `products_category` SELECTs.
The exposure is that the *exact-state* tier, the one AR-M7 created specifically because the live tier
cannot pin columns, is the tier decoupled from production.

Recommended change (test-only, no production change): drive the mirror's selection through
`mutation_payload_child_selections` rather than restating it, or add one row asserting that the
helper's output for a `createItem { node { name category { name } entries { name } } }` document
equals the selection list the mirror uses. Test expectation: the new row fails if the flattening
changes shape.

Owner: `tests/optimizer/test_walker.py` is in my territory for the G2 mirror only; the helper is
optimizer code (`extension.py`), so route the production-side reading to whoever opens `optimizer/`
next. This cycle should record it, not repair it — it is not a SKIPPED contract (the spec's stated
contract *is* asserted), so it does not qualify for R3 under the plan's conditional scope.

#### Two `TODO(spec-036 Slice N)` staged anchors survive at `HEAD` in shipped test files

`docs/builder/BUILD.md` `## Cross-slice integration pass` step 6 and `AGENTS.md` rule 26 both require
a staged anchor to be removed in the change that ships its slice. Two are still live:

```shell
$ git grep -nE 'TODO\(spec-036|TODO-ALPHA-036' HEAD -- '*.py'
HEAD:tests/mutations/__init__.py:3:# TODO(spec-036 Slice 1): keep mutation package tests in this mirror package.
HEAD:tests/test_permissions.py:43:# TODO(spec-036 Slice 3): add the package-level permission pin for mutation
```

Both files are clean in the working tree, so this is not concurrent-session churn.

- `tests/mutations/__init__.py #"TODO(spec-036 Slice 1)"` — Slice 1 shipped and the mirror package is
  populated; the anchor plus its four-line `Pseudocode:` block is pure residue.
- `tests/test_permissions.py #"TODO(spec-036 Slice 3)"` — this one also mis-describes `HEAD`. The pin
  it stages ("declare a mutation target type whose `get_queryset` hides a real row through
  `apply_cascade_permissions`, run the mutation lookup helper against that row, and assert the
  resolver receives the same not-found `FieldError` shape") **exists**, but in two other files:
  `tests/mutations/test_permissions.py::test_hidden_row_is_not_found_before_auth_signal_no_existence_leak`
  and live at `test_products_api.py::test_visibility_scoped_update_delete_hidden_private_row_is_not_found`.
  Decision 4's test-location clause names `tests/test_permissions.py` as the home for "the
  lookup-scoping pin", so the behavior is pinned at a different path than the spec cites.

Owner: Decision 4 is **R1b's** spec territory and the two files belong to R1b / R1c; I found them
because the anchor sweep is not partitioned. Routed below. The Decision 4 path clause is a RENAMED
candidate on R1b's inventory, not mine — I deliberately did not grade it as a row here, to keep the
cohorts' findings partitioned the way the files are.

#### The `FieldError` widening is documented nowhere a consumer reads

`::FieldError` gained `codes` and `path` (row D2.e) and the live products wire already selects
`codes`. Neither field appears in `git show HEAD:docs/GLOSSARY.md` `## \`FieldError\` envelope`
(which still says the type "carries a `field: str` path and `messages: list[str]`") nor anywhere in
`git show HEAD:CHANGELOG.md` (`grep -n 'codes'` returns two hits, neither about `FieldError`).
Meanwhile `CHANGELOG.md` `## [0.0.12]` still describes forms populating "the **byte-identical**
`FieldError` envelope `036` froze".

This is a public-surface documentation gap on a shipped, client-visible wire type. Both files are
outside this cycle's scope to edit (`docs/GLOSSARY.md` is DB-generated and baseline-dirty;
`CHANGELOG.md` needs explicit permission), so it is recorded and routed, never fixed.

### Low:

#### `## Current state` reads present-tense throughout

CS1.a and CS7.a are licensed as dated observations, but four bullets are written in the present
indicative ("neither exists on disk", "there is **no** `Mutation` type", "is planned, not started")
under a section header whose dating clause is one line long. A reader landing mid-document takes them
as current — which is exactly what happened to Slice 0. R2's cheapest fix is a tense pass on the
whole section rather than clause-level surgery; that keeps the dated observations (which must stay)
while removing the false present.

#### `docs/GLOSSARY.md`'s `only()` projection note is version-scoped to `0.0.11`

`## \`only()\` projection` says "As of `0.0.11` the G2 mutation gate is exercised **live** by the
products write surface". True, and the discharge is permanent — but the sentence will read as a
historical note once a reader is several versions on. Cosmetic; recorded only because DoD 7 named
that exact edit and this cohort owns release/doc sanity.

### DRY findings

Evidence from `scripts/review_inspect.py`, run per `docs/builder/BUILD.md` `### When to run the
helper during build` (this pass adds no source, so the helper was run for **repeated-literal and
import-boundary evidence** as `docs/builder/worker-3.md` `## Static helper use` licenses):

```shell
$ uv run python scripts/review_inspect.py examples/fakeshop/test_query/test_products_api.py --output-dir docs/shadow   # exit 0
$ uv run python scripts/review_inspect.py examples/fakeshop/apps/products/schema.py --output-dir docs/shadow           # exit 0
```

Both target files are clean at `HEAD`, so the helper's live read and the snapshot agree. Shadow files
used: `docs/shadow/examples__fakeshop__test_query__test_products_api.overview.md` and
`docs/shadow/examples__fakeshop__apps__products__schema.overview.md` (read: **Repeated string
literals**, **Imports**).

1. **The grant-a-codename block is a three-way near-copy** (Medium). The helper's **Imports** section
   shows `from django.contrib.auth.models import Permission` at four sites — one inside the helper
   `test_products_api.py::_login_with_perm`, and three function-local repeats at
   `::test_create_item_login_bracket_via_test_client`,
   `::test_create_item_with_file_via_form_multipart_upload_over_http` and
   `::test_create_item_via_serializer_multipart_upload_to_attachment`. The last two are
   **byte-identical** six-line blocks (`get_user_model().objects.get(username="view_item_1")` →
   `user_permissions.add(Permission.objects.get(codename="add_item", content_type__app_label="products"))`
   → re-fetch by pk "drop the stale perm cache"), and the first is the same block spelled with a
   local `User` alias. They did not reuse `_login_with_perm` for a real reason: they need the **user
   object**, not a logged-in `Client`. So the right shape is to split the existing helper rather than
   force reuse — extract `_grant_perms(username, *codenames) -> User`, have `_login_with_perm` call
   it, and let the three sites call it directly; the local `Permission` imports then collapse to one
   module-level import. Note the ownership spread: one site is `spec-043` (`TestClient`), one
   `spec-038` (form multipart), one `spec-039` (serializer multipart), so no single cohort of this
   cycle owns the consolidation — it is a deferred follow-up for whichever pass next opens this file.
2. **Type-name and codename literals are unnamed** (Low). Repeated string literals in the same
   overview: `categoryId` 46x, `view_item_1` 42x, `products.category` 40x, `add_item` 31x,
   `products.item` 21x, `change_item` 17x. The GlobalID type labels are the load-bearing ones — every
   `_global_id("products.category", …)` re-spells a wire contract that a model rename would silently
   break in 40 places while the helper signature stays valid. Cheapest readable shape: two module
   constants beside `_global_id` (or two thin wrappers `_category_gid(pk)` / `_item_gid(pk)`), not a
   generalized factory.
3. **One inline mutation string duplicates the module's wire-contract constants** (Low).
   `::test_create_item_via_serializer_multipart_upload_to_attachment` builds a local `mutation = "…
   createItemViaSerializer(data: $d) …"` while `#"_CREATE_ITEM_VIA_SERIALIZER"` already spells that
   field's contract at module level. The selections genuinely differ (`node { name }` vs
   `node { name category { name } }`), so this is not a duplicate today — but the file's own stated
   convention is "each wire contract is spelled once", and two spellings of one field name is how
   that convention erodes. Leave or hoist; no correctness risk.
4. **The existence challenge, answered rather than raised.** `test_products_api.py`'s three helpers
   (`_staff_client`, `_global_id`, `_login_with_perm`) each have many real callers (`_login_with_perm`
   alone is used across the create/update/delete/visibility/G2 rows), so none is a one-caller
   indirection worth deleting. No abstraction in this territory earns the challenge, and per
   `docs/builder/worker-3.md` `### The existence challenge` there is deliberately no per-review
   write-up requirement — this bullet exists only to say the question was asked of the helpers I
   actually read, not to manufacture a justification.
5. **No cross-cohort duplication check is possible from this cohort.** R1a-R1d are read-only and add
   no code, so `docs/builder/worker-3.md` `### Cross-cohort duplication review` has no diffs to
   compare. Recorded so the integration pass does not read its absence as a skipped check.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty** (the file is clean at `HEAD`; the
`git status --short` scoped read at the top of this artifact confirms it is not among the 110 dirty
paths). This pass changes nothing, so `__all__` and the re-export list are unchanged by definition.

Substantively, the surface was audited against the spec rather than merely diffed:

- The four `spec-036` symbols are all present in `django_strawberry_framework/__init__.py #"__all__ = ("`
  — `DjangoModelPermission`, `DjangoMutation`, `DjangoMutationField`, `FieldError` — imported from
  `.mutations` (Decision 5, DoD 8).
- The pin is current: `tests/base/test_init.py::test_public_api_surface_is_pinned` asserts the whole
  37-name tuple, and `::test_reexported_types_resolve_to_canonical_subpackage_definitions` asserts
  identity against `django_strawberry_framework.mutations` for all four — so a stray parallel
  definition would fail, not just a membership change.
- "Four net-new" is not falsified by later cards: `SerializerMutation` and the six other DRF names are
  lazy `__getattr__` exports deliberately **absent** from `__all__`
  (`#"_DRF_SOFT_EXPORTS"`), pinned by `::test_star_import_preserves_namespace_hygiene` and
  `::test_dynamic_getattr_non_memoization`.
- Decision 5's surviving-justification numeral ("keeps the public symbol count at three") no longer
  lives in the spec — Slice 0 moved it, and the companion already flags it under Decision 5's
  `### Changes this Decision underwent`. `__all__` decides, and it says **four**. No R2 action beyond
  not resurrecting the sentence.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

This cohort owns archived-spec and release-metadata sanity. All reads through `git show HEAD:`.

- **Version strings and card ids match the package version after the slice.** `__version__ == "0.0.15"`,
  `tests/base/test_init.py::test_version` asserts the same string, `pyproject.toml` declares
  `dynamic = ["version"]` with `[tool.hatch.version] path = "django_strawberry_framework/__init__.py"`
  — the single-source rule `AGENTS.md` rule 31 and Decision 13 both rest on is intact, and no second
  version literal exists.
- **The archived spec's own verification command passes.** DoD 1's command, run verbatim:
  `OK: 38 terms`, exit 0. The precedent cycle's pre-archive-path failure does not recur — the DoD
  already names the `docs/SPECS/` path.
- **Archival is verified, not performed.** `docs/SPECS/spec-036-mutations-0_0_11.md` with
  `docs/SPECS/appx/spec-036-mutations-0_0_11-terms.csv` and `…-rationale.md` beside it; the live
  follow-up sources of truth (`docs/GLOSSARY.md`, `KANBAN.md`, `CHANGELOG.md`) all carry the shipped
  state (S5.1-S5.9).
- **Stale card ids inside the spec, measured.** See `### Re-derived counts` rows 3-4. Two of the eight
  surviving `TODO-ALPHA-*` ids are in my territory and graded (OS3); the rest belong to other
  sections and to a board-owned sweep.
- **Stale card ids in a territory source file, measured and already carded.**
  `examples/fakeshop/apps/products/schema.py` carries 19 `TODO-BETA-*` ids at `HEAD`:
  `TODO-BETA-046-0.1.1` x7, `TODO-BETA-047-0.1.2` x5, `TODO-BETA-049-0.1.3` x6 (all three renumbered
  away — live referents `059` / `060` / `062`), plus one `TODO-BETA-062-0.1.5` needing only the +1 to
  `066`. My re-derivation matches the board's own measurement to the occurrence
  (`KANBAN.md` records "18 rotted occurrences … beside one `TODO-BETA-062-0.1.5`"), so this is
  **already carded and must not be re-raised as a new finding** — and it is a renumber, never a
  lifecycle flip.
- **No obsolete "coming soon" wording in the surfaces DoD 7 named.** `README.md`, `docs/README.md`,
  `GOAL.md` and `TODAY.md` all describe the mutation foundation as shipped; the only residue is the
  DoD's own reference to headings that no longer exist (S5.5).
- **Script-rendered docs.** This pass regenerates nothing. Noted for R2: `docs/GLOSSARY.md`,
  `docs/TREE.md`, `KANBAN.md` and `KANBAN.html` are baseline-dirty from the concurrent session and
  this cycle's maintainer-set scope forbids touching them, so every doc-side finding above is a
  route, not a fix.

### What looks solid

- **The live mutation suite is the strongest tier in this territory.** The wire contracts are spelled
  once as module constants (`#"_CREATE_ITEM"` / `#"_UPDATE_ITEM"` / `#"_DELETE_ITEM"` /
  `#"_CREATE_CATEGORY"`), the fixture rule holds across all 63 mutation-posting tests, and the
  negative rows are genuinely distinguishing rather than smoke tests — the visibility row holds the
  write perm on purpose so it cannot pass for the wrong reason, and the denial rows assert both the
  top-level error shape and that no row was written.
- **The G2 live assertion is exactly what `docs/builder/BUILD.md` `### Query-shape tests must pin the
  load-bearing property, not observability` asks for**: an absolute count derived from a real run
  (with the derivation written out query by query in-comment), plus direct per-table SELECT counts, so
  an N+1 or a deferred lazy refetch adds rows and fails. It is not an equality-only or
  response-shape-only assertion.
- **Public exports are pinned twice** — membership and identity — which is why "four net-new symbols"
  is still a checkable claim four releases later.
- **The `_resolve_model` forward-compat seam paid off exactly as Decision 5 predicted**: two real
  overrides in `forms/sets.py` and `rest_framework/sets.py`, no re-opening of the base validation.
- **The spec's own package/live ownership split held under two more cards.** The `038` and `039`
  flavors added live rows to the same suite in the same shapes (happy path / envelope / auth /
  visibility / relation-id), which is evidence the split is a usable division and not a slogan.

### Temp test verification

No temp tests were created. Nothing in this territory needed a scratch test to demonstrate: the two
findings that turn on "does an assertion exist" were settled by node-id enumeration, and the one that
turns on coupling (`mutation_payload_child_selections`) was settled by an occurrence sweep showing the
symbol appears in no executable test line.

**No failability mutation was performed, and the reason is recorded rather than left implicit.** This
pass introduces no boundary, and Worker 2 recorded no proof for this cohort (R1 lands no source), so
`docs/builder/worker-3.md` `### Reading is necessary, not sufficient` leaves the mandatory re-run set
legitimately **empty**. The one boundary I would otherwise have mutated — the G2 gate at
`django_strawberry_framework/optimizer/walker.py #"def _enable_only_for_operation"` — lives in a
**baseline-dirty** file carrying the concurrent session's work, and the build plan's
`### Baseline-dirty out-of-scope files` forbids touching it. Mutating a test file instead would prove
nothing about a boundary. So: no mutation, by rule, not by omission.

### Notes for Worker 1 (spec reconciliation)

Every SUPERSEDED / STALE-DESCRIPTION row appears below with the **exact spec text that is wrong** and
what it should say, because R2 authors the edit from this file on disk.

**1. SUPERSEDED — Slice 4, the schema constructor (row S4.3).**
Spec text (`## Slice checklist`, Slice 4, first sub-bullet): "`config/schema.py` wires
`mutation=Mutation` into `strawberry.Schema(...)`."
Should say: `config/schema.py` wires `mutation=Mutation` into `DjangoSchema(...)` — a schema exposing
generated mutations must be built as `DjangoSchema`, whose execution context holds each mutation's
transaction open through GraphQL response completion; the write pipeline refuses to run under a plain
`strawberry.Schema`. Attribution for the `**Post-ship:**` bullet under Decision 9 (or Decision 8):
the `0.0.14` cut, `CHANGELOG.md` `## [0.0.14]` `#"BREAKING: generated mutations require"`, release
header naming design cards `DONE-041`-`DONE-049`; no single card owns it in the CHANGELOG text.
**Fix this together with note 6** — the same spec currently describes `strawberry.Schema` in two
places, one forward-looking and one as a `## Current state` observation.

**2. SUPERSEDED — Decision 2, the envelope freeze (row D2.e).**
Spec text (Decision 2, final paragraph): "the **`FieldError` envelope is defined and frozen in this
card** … so the flavor cards inherit one client contract instead of three", and the spec's opener
"reuse the byte-identical type".
Should say: the envelope is defined here and **shared** — every flavor returns the one
`mutations/inputs.py::FieldError` type — but it is not frozen: `codes: list[str]` and
`path: list[str]` were added later as additive, default-empty fields, so a client selecting only
`field` / `messages` is unaffected while a client can now branch on structured codes and path
segments. Drop "byte-identical". Attribution: commit `951945b7` (2026-07-01, the `0.0.14` write-side
hardening pass); no card id in the commit message. Evidence the widening is live in the wire contract:
`examples/fakeshop/test_query/test_products_api.py #"errors { field messages codes }"`.

**3. SUPERSEDED — Decision 2's upload seam (row D2.b).**
Spec text (Decision 2, first bullet): "**Uploads** … This card leaves an input-converter seam (a
per-field-type input mapping) so 037 plugs `Upload` in without re-opening the generator."
Should say the seam **was** consumed: `DONE-037-0.0.11` shipped the `FileField` / `ImageField` →
`Upload` mutation-input mapping through that seam. The consequence lands on **Decision 6**, whose CR-6
arm still says "the generator raises `NotImplementedError` for a `FileField` / `ImageField` *before*
it consults the override set" and "a file column is removed from the write surface only via
`Meta.exclude`" — falsified by `examples/fakeshop/apps/products/models.py::Item #"attachment = models.FileField("`
sitting on a live write surface whose `::CreateItem` declares no `Meta.exclude`. Decision 6 is
**R1a's** row; I state the falsifying evidence here so R2 has it from whichever cohort reports first.

**4. SUPERSEDED — `## Out of scope`, nested writes (row OS4).**
Spec text: "**Nested writes / bulk mutations** (strawberry-django's `ParsedObject` /
`ParsedObjectList` connect-create-disconnect, batch create) — not on the alpha roadmap; `0.0.11`
writes one root model with relations as existing ids."
Should split: `0.0.11` writes one root model with relations as existing ids, and **nested serializer
inputs shipped at `0.0.13`** as an explicit, descriptor-keyed opt-in
(`django_strawberry_framework/rest_framework/inputs.py::NestedSerializerConfig`,
`Meta.nested_fields = {...}`; a nested field not named there still fails loud). **Bulk / batch
mutations remain out.** Attribution: `spec-039` / `DONE-039-0.0.13`.

**5. STALE-DESCRIPTION — `## Out of scope` card ids (row OS3), and Decision 2's `0.0.13` clause (row D2.d).**
Spec text: "`SerializerMutation` — `0.0.13`, [`TODO-ALPHA-039-0.0.13`]" and "[Auth mutations] —
`0.0.13`, [`TODO-ALPHA-040-0.0.13`]".
Should say `DONE-039-0.0.13` and `DONE-040-0.0.13` (both cards are Done at `HEAD`).
**Coordination warning:** this class is already owned by a board card —`KANBAN.md` carries a measured
deferred item for the 75 `TODO-ALPHA/BETA-*` ids across `spec-034`-`spec-039` (spec-036's share
measured at 13 at `HEAD`; 8 survive the Slice 0 move) which classifies each site as
flip / de-tense / leave-verbatim. R2 should flip only these two (clean class-(c) pointers) and leave
the rest, in particular:
- `## Current state` `#"planned by \`TODO-ALPHA-036-0.0.11\`"` — a **verbatim quotation** of
  `docs/TREE.md`, leave-verbatim class (see note 6b);
- Slice 5's `#"move [\`TODO-ALPHA-036-0.0.11\`][kanban] to Done"` — a card-wrap instruction, true in
  its own tense, de-tense rather than flip;
- Decision 2's `#"reused unchanged by"` parenthetical quoting the card DoD's own
  `TODO-ALPHA-039-0.0.13` / `TODO-ALPHA-038-0.0.12` — a quotation of card text, leave verbatim.

**6. STALE-DESCRIPTION — `## Current state`, clause by clause.**
- **6a (row CS9).** "**The sibling `0.0.11` card is unshipped.** [`TODO-ALPHA-037-0.0.11`] … is
  planned, not started". A live claim about another card, not a dated observation of this repo, so no
  vintage licence. Should say the sibling shipped as `DONE-037-0.0.11` and supplies the
  `FileField` / `ImageField` → `Upload` input mapping on the surface this card generates.
- **6b (row CS1.b).** "[`docs/TREE.md`]'s *target* layout reserves … (both "planned by
  `TODO-ALPHA-036-0.0.11`")". The quoted string is gone from `docs/TREE.md`, which now renders
  `mutations/    # Mutations subsystem - the write side (spec-036).` Either mark the quotation as
  pre-ship or re-point it at TREE's current line; do not silently update the quotation marks around
  text TREE no longer contains.
- **6c (row CS7.b).** "`config/schema.py` constructs `strawberry.Schema(query=..., ...)` with no
  `mutation=`". Both halves are now false. Fix with note 1 so the spec does not name two different
  schema classes.
- **6d (row CS8).** "The four models … are **plain editable Django models** with FK relations and
  `UniqueConstraint`s". `Item` now carries `attachment = models.FileField(...)`. Drop "plain" or say
  "plus, as of `0.0.11`'s sibling card, one `FileField` on `Item`".
- **6e (row CS3.b).** "`types/base.py` holds `DEFERRED_META_KEYS = {"aggregate_class",
  "fields_class", "search_fields"}`". Membership and location are right; the declaration is a typed
  `DEFERRED_META_KEYS: frozenset[str] = frozenset({...})` at `HEAD`. Low priority — R1b owns the
  byte-unchanged-ness claim and may prefer to fix the spelling once, there.
- **6f (Low, whole section).** Four bullets read present-indicative under a one-line dating clause.
  A tense pass over `## Current state` is cheaper and safer than clause surgery, and it preserves the
  dated observations `docs/builder/BUILD.md` says must stay.

**7. STALE-DESCRIPTION — DoD 1's CSV rationale (row DoD1.b).**
Spec text: "The net-new symbols without a glossary heading yet — `DjangoMutationField` and
`DjangoModelPermission` (added in Slice 5) — are intentionally absent from the CSV".
Should say: both symbols now have `docs/GLOSSARY.md` headings, so the omission from
`spec-036-mutations-0_0_11-terms.csv` no longer has the stated reason; whether the CSV gains them is a
**maintainer call** (the CSV is outside this cycle's scope, and `import_spec_terms` writes the kanban
DB). Same defect Slice 0 flagged in the moved Risks item — fix both spellings or neither.

**8. STALE-DESCRIPTION — DoD 5's Category scope (row DoD5.a).** Two options, recorded in full under
`### The DoD-5 second reading`. Recommended: reword DoD 5 to "create/update/delete over `Item`, plus
at least one `Category` write", matching its own `## Slice checklist`.

**9. STALE-DESCRIPTION — Slice 5 / DoD 7's doc-section names (row S5.5).**
Spec text: "[`docs/README.md`] / [`README.md`] (move mutations from "Coming next" to "Shipped
today")".
Should name the sections that exist: `README.md` `## Status` (whose "Coming from DRF + django-filter?"
paragraph and `0.0.11` bullet carry the shipped wording) and `docs/README.md` `## Today and coming
next`. The obligation was discharged; only the section names rotted.

**10. Escalated: DoD 6 is not worker-verifiable in this tree.** "The full suite is green at the 100%
coverage gate; `ruff format` + `ruff check` are clean; no B1-B8 optimizer regression" is a runtime
claim, and per `docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`
only the maintainer can run a clean `HEAD`. The working tree carries 110 dirty paths from a concurrent
session covering the whole mutation surface, and coverage flags are forbidden to workers. Recorded and
escalated; no grade asserted. Resolution paths for W1: (a) accept it as a historical claim about the
card, as D13 is accepted; (b) ask the maintainer for a clean-`HEAD` gate run.

**11. Escalated: the `transaction.atomic` ownership line is stale in the `## Test plan` (row TP.9).**
The split assigns "the `transaction.atomic` rollback boundary" to package tests. At `HEAD` the
boundary itself moved — the transaction spans GraphQL response completion under `DjangoSchema` — and
the live tier now carries `examples/fakeshop/test_query/test_mutation_atomicity.py`, whose own header
records that it began as `xfail(strict=True)` regressions and lost the markers when the `0.0.14`
work landed. The spec's ownership split does not know that file exists. R1c owns the boundary's
Decision text (Decision 8 / AR-M4); the **`## Test plan` sentence** is mine to route, and R2 should
edit them in one pass so the tier assignment and the Decision agree.

**12. Escalated (Medium, out-of-territory): two `TODO(spec-036 Slice N)` anchors survive at `HEAD`.**
Full evidence in the Medium finding above. `tests/mutations/__init__.py` (Slice 1) is pure residue;
`tests/test_permissions.py` (Slice 3) additionally mis-describes `HEAD`, because the pin it stages
exists at `tests/mutations/test_permissions.py::test_hidden_row_is_not_found_before_auth_signal_no_existence_leak`
and live at `test_products_api.py::test_visibility_scoped_update_delete_hidden_private_row_is_not_found`,
while **Decision 4** still cites `tests/test_permissions.py` as that pin's home. Owning cohort:
**R1b** (Decision 4, test locations) with **R1c** for the file. Two dispositions are needed —
delete the anchors (a `.py` edit, in scope for this cycle) and decide whether Decision 4's path is
RENAMED or the pin should move.

**13. Escalated (Medium): the `FieldError` widening is undocumented.** `codes` / `path` appear in no
`docs/GLOSSARY.md` entry and no `CHANGELOG.md` line at `HEAD`, while `CHANGELOG.md` `## [0.0.12]`
still calls the envelope "byte-identical". Both files are out of this cycle's scope, so this is a
maintainer follow-up, not an R2 edit. Pairs with note 2.

**14. For the deferred-work catalog, not for R2.** The AR-M7 package mirror's decoupling from
`mutation_payload_child_selections` (Medium finding above) is a **test-quality** finding, not a
SKIPPED contract: the spec's stated exact-state contract *is* asserted. It therefore falls outside
R3's conditional scope in this cycle and belongs in `bld-036-final.md`'s `### Deferred work catalog`,
routed to whichever pass next opens `optimizer/`.

### Review outcome

`review-accepted`.

The cohort's job was to grade, and it graded 70 contracts against `HEAD` with one SKIPPED row carrying
its burden of proof, 4 SUPERSEDED, 10 STALE-DESCRIPTION, and every one of the 15 routable rows written
into `### Notes for Worker 1 (spec reconciliation)` above with the exact spec text and its
replacement. Three Medium findings are recorded; none is a defect in this pass's own output (this pass
produced no diff), and each is routed to its owning cohort or to the maintainer with a resolution
path, per `docs/builder/worker-3.md` `### Acceptance gate`'s escalation clause. Worker 1 performs the
final verification.


---

## Final verification (Worker 1)

Performed in the R2 pass, `docs/builder/bld-036-review-2-spec_reconciliation.md`, which combines spec
reconciliation with this cohort's final verification — the same combined role the precedent cycle's R2
performed. The audit's own contract is `docs/builder/build-036-mutations-0_0_11.md` `## Conformance
grading vocabulary`; there is no `### Spec slice checklist (verbatim)` and no diff to audit, because
every R1 cohort is read-only over source and tests.

**Counts re-derived, not accepted.** Each cohort's grade tally was recomputed by parsing this file's
own inventory table row by row (row-id pattern per cohort, grade cell normalized), off the rendered
table rather than from the summary paragraph:

```
rows=70  CONFORMS=54  SUPERSEDED=4  STALE-DESCRIPTION=10  SKIPPED=1  RENAMED=0
        + 1 graded "Not worker-verifiable at HEAD" (DoD6), deliberately outside the five grades
```

Matches this file's stated table exactly, and 54+4+10+1+1 = 70 = the row count.

**One evidence-cell correction, which does not move the grade.** Row `D2.e` attributes `codes` / `path`
to "commit `951945b7` (2026-07-01, the `0.0.14` write-side hardening)". That commit is not `0.0.14`
work: `git show 951945b7:django_strawberry_framework/__init__.py` reads `__version__ = "0.0.12"` and
`git show 951945b7 --stat` carries `docs/spec-039-serializer_mutations-0_0_13.md`, so the owner is the
DRF-serializer flavor card, two months earlier. **R1a's attribution for the same commit is the correct
one.** The SUPERSEDED grade, the row's routing, and its recommended replacement all stand unchanged;
the companion records the correction so the wrong attribution does not propagate. Not grounds for
`revision-needed` — the row's contract finding is right and its fix landed as recommended.

**The SKIPPED row (`S4.7`) carries its burden of proof and is accepted as real.** Two independent
instruments agree (a whole-tier occurrence sweep of the single denial message string, and a per-test
attribution of all 8 asserting rows to the operations their bodies post), the sibling-tier check
confirms the behavior *is* pinned at package tier so what is missing is the tier the spec assigns it to,
and the two missing rows are named concretely with the fixture that makes them expressible. It is in
R3's declared scope and R3 is adding them.

**Both stated readings were adopted, and the artifact says which.** DoD 5 is reworded to match its own
slice checklist (this cohort's option 1, its recommendation) rather than treated as a code gap; Decision
13 / DoD 8 and DoD 6 are read as **historical claims about the card**, the only readable reading at
`0.0.15`, with no spec edit following. This cohort's clause-by-clause `## Current state` grading is what
made that section reconcilable at all: dated observations stood, three falsified predictions were
rewritten, and the `docs/TREE.md` quotation was dropped rather than silently re-worded inside its own
quotation marks.

**Note 11 (`TP.9`) was taken in the same pass as the Decision-8 boundary**, so the `## Test plan` tier
assignment and the Decision now agree rather than describing two different boundaries. All 15 routable
rows are discharged in the spec.


**Method audited and accepted.** Every grade cites the read-only `HEAD` snapshot at
`7426e7e7d8aa447e89fee75088447d6a506dec12` or a `git show HEAD:<path>` read; no `git stash` /
`git checkout` / `git restore` / `git worktree` appears anywhere in the pass; the decision to decline a
failability mutation on baseline-dirty territory files is recorded with its reason rather than skipped
silently, and is the right call under `AGENTS.md` rule 34 — a `cp`-and-restore round trip spanning a
pytest run would have reverted any concurrent write landing inside the window.

**Every routable row reached R2 on disk** under `### Notes for Worker 1 (spec reconciliation)`, with the
pre-fix spec text and a recommended replacement — which is the obligation
`docs/builder/BUILD.md` `### Cohorting, naming, and closure` records two prior builders as having
missed. Nothing had to be re-derived from a return report.

Final status: `final-accepted`.


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
