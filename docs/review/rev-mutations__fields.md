# Review: `django_strawberry_framework/mutations/fields.py`

Status: verified

First review of a NEW file in the NEW `mutations/` subpackage (shipped 0.0.11, spec-036 Slice 3). Full first-review scrutiny applied. The file landed in HEAD via the spec-036 build commits; `git diff b6ecad1089a04d518f74116bafb7e6b92ac14b17 -- django_strawberry_framework/mutations/fields.py` is empty AND `git diff HEAD -- …` is empty, so there are zero tracked edits to make this cycle. No correctness bug, no behaviour-changing Medium, GLOSSARY clean — genuine no-source-edit (shape #5).

## DRY analysis

- **Defer-with-trigger — fold `fields.py::_input_type_name` into `inputs.py::mutation_input_shape`.** `_input_type_name` (`django_strawberry_framework/mutations/fields.py:95-124`) independently re-walks `editable_input_fields(model, fields=…, exclude=…)` for the effective names AND `editable_input_fields(model)` for the full set, then calls `mutation_input_type_name(...)` — which is byte-for-byte the same computation `inputs.py::mutation_input_shape` (`django_strawberry_framework/mutations/inputs.py:393-427`) performs to produce `shape.type_name`. This is the DRY-1 drift point the `MutationInputShape` descriptor exists to eliminate (`inputs.py:362-391` docstring names it explicitly), yet the field factory's lazy-`data:` ref re-derives the name out-of-band instead of consuming the single-sourced descriptor. The consolidation shape: have `_input_type_name(meta)` call `mutation_input_shape(meta.model, _OPERATION_INPUT_KIND[meta.operation], fields=meta.fields, exclude=meta.exclude).type_name` and drop the local two-walk re-spelling. Today the names provably agree (identical inputs to `mutation_input_type_name`), so this is correctness-neutral. **Defer until either (a) `mutation_input_type_name`'s signature/identity rule changes, or (b) a fourth caller of the `(model, operation_kind, effective_names, full_names)` name computation lands** — at that point the out-of-band re-spell in `fields.py` becomes the most likely site to drift from the canonical descriptor and should be collapsed first. Quote the trigger verbatim for the next DRY cycle: "Defer until `mutation_input_type_name`'s identity rule changes OR a fourth name-derivation caller lands; then route `_input_type_name` through `mutation_input_shape(...).type_name`."

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** `_lazy_ref` (`fields.py:127-136`) single-sites the `Annotated[name, strawberry.lazy(INPUTS_MODULE_PATH)]` shape so the `data:` arg ref and the `<Name>Payload` return ref use one construction, and pins the module path to the shared `inputs.py::INPUTS_MODULE_PATH` constant (`inputs.py:62`) rather than re-spelling the dotted path. The factory delegates all generation/resolution work outward: input-name selectors to `inputs.py` (`editable_input_fields`, `mutation_input_type_name`), the operation→input-kind map to `sets.py::_OPERATION_INPUT_KIND` (`sets.py:96`), and the pipeline to `resolvers.py::resolve_mutation_{sync,async}` — no logic is re-implemented locally.
- **New helpers considered.** A shared "synthesized-signature" helper across `fields.py` / `relay.py` / `connection.py` was considered and rejected: `relay.py::DjangoNodesField._resolve` uses explicit typed params (`ids: list[strawberry.ID]`) while this factory uses the `**kwargs` + `__signature__`/`__annotations__`-override form (forced by the per-operation variable arg set: create has no `id`, delete has no `data`). The arg sets are genuinely per-family, so a shared signature builder would carry more conditional branching than the three call sites save. Not a candidate.
- **Duplication risk in the current file.** The `operation in ("update", "delete")` / `operation in ("create", "update")` membership tests in `_synthesized_mutation_signature` (`fields.py:167,173`) overlap on each operation appearing in two checks; this is the correct per-arg gating (each GraphQL arg is owned by the set of operations that carry it), not a duplicated literal to hoist. Likewise the `kwargs.get("data"/"id", strawberry.UNSET)` pair in `_resolve` mirrors the resolver's `UNSET`-default kwargs — intentional contract alignment, not drift.

### Other positives

- **No KeyError on `delete`.** `_input_type_name` does `_OPERATION_INPUT_KIND[meta.operation]` (`fields.py:113`), and `_OPERATION_INPUT_KIND` (`sets.py:96`) has only `create`/`update` keys — but `_input_type_name` is reached only inside the `if operation in ("create", "update")` guard in `_synthesized_mutation_signature` (`fields.py:173-174`), so the `delete` operation never indexes the map. The bind side defensively uses `.get(...)` because it is the path that must return `None` for `delete` (`sets.py:630`); the asymmetry is correct, not a latent crash.
- **Name parity with the bind is exact.** The lazy `data:` ref must name the class the phase-2.5 bind actually materializes. `_input_type_name` computes the name from the same `editable_input_fields` + `mutation_input_type_name` inputs the bind feeds through `mutation_input_shape` (`inputs.py:393-427`), and the consumer-merged path materializes under `shape.type_name` (`sets.py:729-730`, `_materialize_merged_input`), never the consumer class `__name__` — so a `Meta.input_class` override does not break the forward-ref resolve. The docstring's claim (`fields.py:95-112`) is verified against both materialize paths.
- **Construction-time validation fires at the assignment line.** `_validate_mutation_target` (`fields.py:70-92`) rejects a non-class / non-`DjangoMutation` / abstract-base (`_mutation_meta is None`) target with a `ConfigurationError` naming `DjangoMutationField`, and deliberately does NOT require the bind outputs (`_input_class` / `_payload_type_name`), which do not exist until finalize — correct for a factory that runs while `@strawberry.type class Mutation` evaluates, before the bind.
- **Single runtime async dispatch.** `_resolve` (`fields.py:208-213`) dispatches on `in_async_context()` per call, mirroring `relay.py::DjangoNodesField._resolve` (`relay.py:445`) — one factory output serves both `schema.execute_sync` and `await schema.execute`, and the docstring correctly explains why only the runtime half of the `DjangoListField` asymmetry applies (no consumer `resolver=` seam to inspect at construction).
- **GLOSSARY accurate, no drift.** The `DjangoMutationField` entry (`docs/GLOSSARY.md:392-396`) documents the no-annotation assignment, the `strawberry.lazy` payload forward-ref, the per-operation signature (`data: <Model>Input!` / `id:` + `data: <Model>PartialInput!` / `id:`), and the async-detection asymmetry — all matching the implementation. Ran the GLOSSARY grep over every public symbol; clean (the `#4`-vs-`#5` separator step).
- **`noqa` discipline.** Both suppressions are justified inline: `N802` for the PascalCase field-factory family parity (`fields.py:185`) and `ARG001` for the Strawberry-bound-but-unused `root` (`fields.py:208`).

### Summary

`fields.py` is a thin, well-factored `DjangoMutationField` factory: it validates the target at the construction line, synthesizes a per-operation resolver signature with single-sited lazy forward-refs, and hands off to the sync/async resolver pipeline via runtime `in_async_context()` dispatch — re-implementing none of the generation or resolution logic. Field construction, argument wiring, resolver hand-off, sync/async dispatch, and the lazy-ref/`get_queryset`-bind cooperation are all correct; the `delete`-path `[meta.operation]` index is provably guarded. No High/Medium/Low findings. One defer-with-trigger DRY-1 candidate: `_input_type_name` re-derives the input name out-of-band instead of consuming `mutation_input_shape(...).type_name`. Zero source edits this cycle (empty diff vs both baseline and HEAD); GLOSSARY clean; genuine no-source-edit shape #5.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; 289 files left unchanged.
- `uv run ruff check --fix .` — pass; all checks passed.

### Notes for Worker 3
- No GLOSSARY-only fix in scope (GLOSSARY `DjangoMutationField` entry at `docs/GLOSSARY.md:392-396` verified accurate; no drift).
- Low dispositions: none — all severities `None.`
- The single DRY-analysis bullet is forward-defer (explicit trigger quoted), not an act-now edit; nothing for Worker 2.
- `git diff b6ecad1089a04d518f74116bafb7e6b92ac14b17 -- django_strawberry_framework/mutations/fields.py` and `git diff HEAD -- …` both empty — confirmed no pending edit despite "NEW file" framing (file landed in HEAD via the spec-036 build commits).

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment/docstring edits. The module docstring and per-symbol docstrings are accurate against the implementation (verified the name-parity, delete-guard, and async-dispatch claims against `inputs.py` / `sets.py` / `resolvers.py` / `relay.py`). The two `noqa` comments are justified. Nothing to change.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted. No source/test/doc edits this cycle (review-only artifact). Per AGENTS.md "Do not update CHANGELOG.md unless explicitly instructed" and the active plan `docs/review/review-0_0_11.md` (silent on changelog for review artifacts), no changelog entry is warranted.

---

## Verification (Worker 3)

### Logic verification outcome
All High / Medium / Low `None.` — independently confirmed genuine on this NEW file, not lazy:

- **Zero-edit proof (shape #5).** `git diff b6ecad1089a04d518f74116bafb7e6b92ac14b17 -- …/mutations/fields.py` empty; `git diff HEAD -- …/mutations/fields.py` empty; `git diff --stat <baseline> -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` fully empty (clean run, no #33 dirt); `git diff -- CHANGELOG.md` empty. Each Worker 2 section opens "Filled by Worker 1 per no-source-edit cycle pattern."
- **Claim 1 — `delete` never KeyErrors (the hard `[meta.operation]` index).** `_input_type_name` (`fields.py::_input_type_name #"_OPERATION_INPUT_KIND[meta.operation]"`) hard-indexes the map, but is reached only inside the `if operation in ("create", "update")` guard in `_synthesized_mutation_signature` (`fields.py::_synthesized_mutation_signature #'if operation in ("create", "update")'`). Confirmed `_OPERATION_INPUT_KIND` (`sets.py #"_OPERATION_INPUT_KIND: dict"`) holds only `create`/`update` keys, so `delete` never reaches the index. The bind side defensively uses `.get(...)` (`sets.py::_materialize_input_for #"_OPERATION_INPUT_KIND.get(meta.operation)"`) precisely because that path MUST return `None` for delete — the asymmetry is correct, not a latent crash. Pinned by `tests/mutations/test_fields.py::test_per_operation_argument_signatures` (asserts `deleteItem` args == `{"id": "ID!"}` — the delete field builds with no `data`, exercising the guarded path).
- **Claim 2 — lazy `data:` forward-ref name equals the phase-2.5-materialized class.** `_input_type_name` computes the name via `mutation_input_type_name(model, operation_kind, effective_names, full_field_names=full_names)` from `editable_input_fields`. Verified the bind materializes under the SAME computation on BOTH paths: all-generated `materialize_mutation_input_class(input_cls.__name__, …)` where `input_cls` is built from `mutation_input_shape(...)` (`sets.py::_materialize_input_for`), and consumer-merged `materialize_mutation_input_class(shape.type_name, merged)` (`sets.py::_materialize_merged_input #"materialize_mutation_input_class(shape.type_name, merged)"`). Both `shape.type_name` and `input_cls.__name__` flow from `mutation_input_shape` → `mutation_input_type_name` with identical inputs, so the ref provably names the materialized class; a `Meta.input_class` override merges under `shape.type_name`, never `consumer.__name__`, so the override does not break the forward-ref resolve. Pinned by `test_payload_lazy_ref_resolves_to_materialized_payload_after_bind` (lazy ref resolves to the materialized module global) and the `mutation_input_type_name` identity tests in `tests/mutations/test_inputs.py` (`test_type_name_full_shape_is_canonical`, `test_type_name_narrowed_shape_is_deterministic_and_distinct`, `test_type_name_token_boundaries_do_not_collide`).
- **Argument wiring / resolver hand-off / sync-async.** `_resolve` reads `kwargs.get("data"/"id", strawberry.UNSET)` and dispatches `in_async_context()` → `resolve_mutation_async` / `resolve_mutation_sync(mutation_cls, info, data=data, id=node_id)`. Confirmed both resolver entry points (`resolvers.py::resolve_mutation_sync`, `resolvers.py::resolve_mutation_async`) take `*, data=UNSET, id=UNSET` — kwarg contract aligned exactly. The `**kwargs` + `__signature__`/`__annotations__`-override form is forced by the per-operation variable arg set; `noqa: ARG001` (unused `root`) and `noqa: N802` (PascalCase factory parity) both justified. Pinned by `test_sync_and_async_resolver_selection` + `test_async_resolver_selection_works`; construction-time `_validate_mutation_target` rejections pinned by `test_non_mutation_target_raises_at_construction` / `test_non_class_target_raises_at_construction` / `test_abstract_base_target_raises_at_construction`.

### DRY findings disposition
The single defer-with-trigger DRY-1 item (fold `_input_type_name` into `mutation_input_shape(...).type_name`) is correctly deferred and correctness-neutral now: the two name computations take identical inputs to `mutation_input_type_name`, so they provably agree today (verified above). The verbatim trigger — "Defer until `mutation_input_type_name`'s identity rule changes OR a fourth name-derivation caller lands; then route `_input_type_name` through `mutation_input_shape(...).type_name`." — is carried forward to the `mutations/` folder pass (`rev-mutations.md`) and the project pass (`rev-django_strawberry_framework.md`). The identity rule is pinned by the three `mutation_input_type_name` tests above, which are the canary if the trigger ever fires.

### Temp test verification
- No temp tests needed; the two load-bearing claims are pinned by existing permanent tests in `tests/mutations/test_fields.py` and `tests/mutations/test_inputs.py`.

### GLOSSARY (#4-vs-#5 gate)
Genuine #5. `docs/GLOSSARY.md #"## \`DjangoMutationField\`"` (entry body) documents the no-annotation assignment, the `strawberry.lazy` payload forward-ref, the per-operation signature (`data: <Model>Input!` create / `id:` + `data: <Model>PartialInput!` update / `id:` delete), and the `DjangoListField` async-detection asymmetry — all matching the module docstring and implementation verbatim. No GLOSSARY drift; no owed edit.

### Validation
- `uv run ruff format --check django_strawberry_framework/mutations/fields.py` — "1 file already formatted".
- `uv run ruff check django_strawberry_framework/mutations/fields.py` — "All checks passed!".

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `mutations/fields.py` checklist box in `docs/review/review-0_0_11.md`.
