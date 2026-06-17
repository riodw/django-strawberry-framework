# Review: `django_strawberry_framework/management/commands/inspect_django_type.py`

Status: verified

## DRY analysis

- **`_render_annotation` (lines 451-467) and `_render_strawberry_type` (lines 373-386) are deliberate parallel renderers, NOT a consolidation target.** They render two different inputs to the same GraphQL-shaped string vocabulary: the first walks Python typing annotations (`typing.get_origin` / `typing.get_args`, `Union`/`UnionType`, `list`), the second walks finalized Strawberry wrappers (`StrawberryOptional` / `StrawberryList`). The shared output grammar (`Name!`, strip-`!` for nullable, `[Inner!]!` for lists) is intentional mirroring of how Strawberry prints SDL — a single renderer would need to branch on input shape per node, re-coupling two type vocabularies the package keeps separate everywhere else. Keep as-is; the module docstring (lines 9-21) and each helper docstring already document the annotation-source split as load-bearing.
- **`_scalar_name` (lines 439-448) is the single shared GraphQL-name resolver** for both renderers via the module-level `_GRAPHQL_SCALAR_NAMES` table — already the correct chokepoint, no further hoist available.
- **The `import_string` / `import_module_symbol` + `raise CommandError(str(e)) from e` shape recurs across this file (lines 105-106, 128-129) and the sibling `export_schema.py` (`handle` body).** Each site catches `(ImportError, AttributeError)` and re-wraps verbatim. Defer a shared `_import_or_command_error(...)` helper until the `management/commands/` folder pass (`rev-management__commands.md`) can weigh both commands together; it is a folder-scope consolidation, not a local defect, and the two sites differ in importer (`import_string` for an object path vs `import_module_symbol` for a selector) so any helper must parameterize the importer callable. Forwarded to the folder pass for triage.

## High:

None.

## Medium:

None.

## Low:

### Unreachable raw-token fallback in the relation-kind label lookup

`_relation_row` (line 242) and `_connection_only_relation_row` (line 286) both compute `_RELATION_KIND_LABELS.get(kind, kind)`, and the comment at lines 58-59 states "Unmapped kinds fall back to the raw token." `RelationKind` (`utils/relations.py:7-12`) is a four-value `Literal` (`"many"`, `"reverse_many_to_one"`, `"reverse_one_to_one"`, `"forward_single"`), and `_RELATION_KIND_LABELS` (lines 60-65) maps all four. So the `.get` fallback can never fire for any value `field_meta.relation_kind` can return today — it is defensive code against a future `RelationKind` member that does not yet exist. This is correct and harmless; flagging only so it is not mistaken for a tested branch.

Defer; the fallback becomes live the moment a fifth `RelationKind` member lands in `utils/relations.py` without a matching `_RELATION_KIND_LABELS` entry. Trigger: when `RelationKind`'s `Literal` gains a member, add the matching label here in the same change (or the operator sees a raw internal token). No action now — adding a label for a non-existent kind would be speculative.

### CHANGELOG entry omits the consumer-authored `__strawberry_definition__` read path

The `[Unreleased]` CHANGELOG entry (`CHANGELOG.md:36`) says the command "reads the resolved annotation from `origin.__annotations__` (so it reflects consumer-authored annotations and overrides, not a `convert_scalar` re-run)." That is accurate for auto-synthesized fields but elides the second authoritative source the code actually uses: consumer-authored fields and `"connection"`-shaped relations read from `origin.__strawberry_definition__` instead (`_consumer_authored_row` line 323, `_connection_only_relation_row` line 282), because their `origin.__annotations__` entry is an unrenderable `StrawberryAnnotation` / forward-ref string. The module docstring (lines 9-21) and the GLOSSARY entry (`docs/GLOSSARY.md:1201`) both describe the two-source split precisely, so this is a CHANGELOG-prose simplification, not a code/docstring drift. Per the cycle's watch-instruction, the **docstrings here do not mis-quote the CHANGELOG** — the code matches its own docstrings; only the CHANGELOG summary is lossy.

Defer to maintainer; CHANGELOG edits are not authorized in review and AGENTS.md forbids touching `CHANGELOG.md` unless explicitly instructed. Maintainer-ready clause to fold into the parenthetical if desired: "(reads the post-finalize record — `origin.__annotations__` for auto-synthesized fields, `origin.__strawberry_definition__` for consumer-authored fields and `"connection"`-shaped relations — not a `convert_scalar` re-run)."

## What looks solid

### DRY recap

- **Existing patterns reused.** `field_map[snake_case(field.name)]` (line 192) reuses the package-canonical snake_case keying convention verified across `types/base.py:1572`, `types/finalizer.py:417/597`; `snake_case` imported from `utils/strings.py`. `SCALAR_MAP` (line 50) and `BigInt` (line 48) are imported from their canonical modules, not re-listed. `import_module_symbol` mirrors `export_schema`'s schema-import idiom (docstring line 28 names the mirror explicitly).
- **New helpers considered.** A unified `_render(...)` over both annotation and Strawberry-wrapper inputs was evaluated and rejected (see DRY analysis bullet 1) — it re-couples two deliberately-separate type vocabularies. The `_import_or_command_error` helper is deferred to the folder pass, not invented locally.
- **Duplication risk in the current file.** The `2x "no (list)"` literal (`_relation_row` line 243, `_consumer_nullable` line 399) and `2x "relation:"` prefix (lines 242, 286) are intentional sibling rows in the same output table; both render the same column convention and a named constant would add indirection without removing a real near-copy. The `2x __name__` (lines 146, 448) are unrelated reflective reads (registry diagnostic message vs scalar-name fallback).

### Other positives

- **Dispatch ordering in `_resolve_row` (lines 175-199) is correctness-load-bearing and well-documented.** Suppressed-Relay-pk check first (a relation pk on a Relay type would otherwise `KeyError` in `_relation_row`), then consumer-authored, then auto relation/scalar — the docstring (lines 178-191) explains why each precedes the next. `_is_suppressed_relay_pk` reads `definition.interfaces` and the `relay.Node` subclass check, matching the suppression logic in the converter pipeline.
- **The `"connection"`-shape branch never indexes the deleted annotation.** `_suppressed_connection_name` (lines 247-263) guards `if field.name in origin.__annotations__: return None` first, then inverts `relation_connections` to find the synthesized sibling, so a `relation_shapes = {<rel>: "connection"}` field renders from `__strawberry_definition__` rather than `KeyError`-ing on the popped list annotation. Pinned package-side (`tests/management/test_inspect_django_type.py::test_inspect_connection_only_relation_shape_renders_row`) against real fakeshop models in registry isolation, because no example type ships the shape.
- **`UNRESOLVED` sentinel handling is honest.** `_consumer_authored_row` (lines 325-333) raises `CommandError` with a concrete `--schema` recovery hint rather than printing Strawberry's `UNRESOLVED` sentinel as a bogus type — matching that `finalize_django_types()` does not force forward-ref resolution (schema-build does). Pinned by `test_inspect_unresolved_forward_ref_relation_raises_command_error`.
- **Every `CommandError` branch is tested.** Bad dotted path, bad `--schema` selector, ambiguous bare name, unregistered bare name, non-DjangoType symbol, abstract/no-Meta base (no definition), unfinalized definition, UNRESOLVED forward ref, and the connection-only render — all pinned in `tests/management/test_inspect_django_type.py`. Happy paths (by-name, by-dotted-path, `--schema`, choice enum, relation rows, consumer-authored rows, Relay pk row, resolved-annotation-not-field-null) live in `examples/fakeshop/tests/test_inspect_django_type.py` via `call_command`, honoring the AGENTS.md prefer-the-example-project test placement rule.
- **`BaseCommand.handle()` signature is correct** (`def handle(self, *args: object, **options: object) -> None`), `add_arguments` registers the positional `type` and optional `--schema` with help text, and the required-positional `options["type"]` direct-index vs optional `options.get("schema")` asymmetry is the correct argparse contract (same calibration as the export_schema sibling cycle).
- **Bare-name ambiguity message is operator-grade** (lines 143-152): names every colliding `module.qualname (model …)` and tells the operator to pass a dotted path to disambiguate; the unregistered-name message points at `--schema` or a dotted path. Both are actionable.

### Summary

A 468-line diagnostic management command that reads — never re-derives — the post-finalize introspection surface to print a per-field GraphQL resolution table. The cycle diff against the baseline is empty (standing code, first review this release). Logic is clean: argument shape-dispatch (dotted path via `import_string` vs unique bare-name registry lookup), the most-specific-first row dispatch with documented Relay-pk and consumer-authored short-circuits, and the connection-only branch that reads the synthesized sibling rather than the suppressed annotation. All cross-referenced definition attributes (`field_map`, `selected_fields`, `finalized`, the four `consumer_*` frozensets, `relation_connections`, `consumer_authored_fields`) and FieldMeta attributes (`relation_kind`, `is_relation`, `is_many_side`, `nullable`) were verified to exist with matching shapes; `field_map`'s `snake_case` keying matches the package convention. The two renderers are correct parallel mirrors, not duplication. Test discipline is exemplary across both trees with every `CommandError` branch pinned. No High or Medium. Two forward-looking Lows (an unreachable-today relation-kind label fallback; a lossy-but-not-wrong CHANGELOG summary line, deferred to the maintainer since CHANGELOG edits are unauthorized) and one folder-scope DRY forward (the shared import-or-CommandError shape with `export_schema`). No source edit warranted — qualifies as a no-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — 267 files left unchanged.
- `uv run ruff check --fix .` — All checks passed.

### Notes for Worker 3
- **Low 1 (unreachable relation-kind label fallback):** forward-looking, trigger-gated on a fifth `RelationKind` `Literal` member landing without a matching `_RELATION_KIND_LABELS` entry. No edit now; adding a label for a non-existent kind would be speculative.
- **Low 2 (CHANGELOG summary omits the `__strawberry_definition__` read path):** deferred to maintainer — AGENTS.md forbids touching `CHANGELOG.md` without explicit instruction. The code matches its own docstrings and the GLOSSARY (`docs/GLOSSARY.md:1201`) is precise; only the CHANGELOG one-liner is lossy. Maintainer-ready clause preserved verbatim in the Low body.
- **DRY forward (import-or-CommandError shape shared with `export_schema`):** folder-scope, forwarded by citation to `rev-management__commands.md`; do not open as a local defect.
- No GLOSSARY-only fix in scope — GLOSSARY entry at line 1201 is accurate, no drift.
- Shadow overview used: `docs/shadow/django_strawberry_framework__management__commands__inspect_django_type.overview.md`.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment or docstring edits warranted — every docstring matches the code's real behavior (the module docstring's two-source annotation/`__strawberry_definition__` split, the `_resolve_row` dispatch-order rationale, the connection-only branch explanation, and the `UNRESOLVED` raise rationale are all accurate). The lines-58-59 "Unmapped kinds fall back to the raw token" comment describes correct (if currently-unreachable) defensive code and is left as-is per Low 1's defer.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. **Not warranted.** No source change this cycle (cycle diff against baseline empty); AGENTS.md forbids `CHANGELOG.md` edits unless explicitly instructed, and the active plan (`docs/review/review-0_0_10.md`) authorizes no changelog work. Low 2's CHANGELOG-prose observation is recorded for the maintainer but is not an edit this cycle performs.

---

## Verification (Worker 3)

### Logic verification outcome
Terminal-verify, shape #5 (no-source-edit). Baseline = HEAD; working tree clean. `git diff HEAD -- django_strawberry_framework/management/commands/inspect_django_type.py` empty; `git diff --stat HEAD -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` empty for all paths. Zero edits confirmed.

High 0 / Medium 0 — concur after independent source read.

- **DjangoType lookup is correct.** `handle` reads the registration attribute `__django_strawberry_definition__` (set at `types/base.py::__init_subclass__` line 649, read defensively at line 683), distinct from Strawberry's native `__strawberry_definition__`. The two attributes are used for two distinct purposes and never conflated: registration/finalization state vs. finalized Strawberry field metadata. The `definition is None` (abstract/no-Meta base) and `finalized is False` guards each map to a tested `CommandError` branch.
- **The two read paths are correct and match their docstrings.** `origin.__annotations__` for auto-synthesized scalar/relation rows (`_scalar_row` line 292, `_relation_row` line 240); `origin.__strawberry_definition__.fields` for consumer-authored fields (`_consumer_authored_row` line 323) and `"connection"`-shaped relations (`_connection_only_relation_row` line 282). The connection-only branch never indexes the popped list annotation: `_suppressed_connection_name` guards `if field.name in origin.__annotations__: return None` (line 260) before inverting `relation_connections`. Verified `relation_connections` is the `{generated: name}` map set in `types/finalizer.py::_record_relation_connection` (line 349) and documented at `types/definition.py:86`; the command's inverted lookup `(gen for gen, rel in connections.items() if rel == field.name)` (line 263) reads it correctly.
- **snake_case keying matches the package convention.** `field_map[snake_case(field.name)]` (line 192) mirrors the construction site `field_map = {snake_case(f.name): FieldMeta.from_django_field(f) ...}` (`types/base.py:488`) and the canonical read sites (`types/base.py:1388`, `:1572`). No keying drift.
- **All cross-referenced FieldMeta/definition attributes exist** with matching shapes: `relation_kind`, `is_relation`, `is_many_side`, `nullable` (FieldMeta); `field_map`, `selected_fields`, `finalized`, `relation_connections`, `consumer_authored_fields`, and the four `consumer_{annotated,assigned}_{scalar,relation}_fields` frozensets (definition).

**Both Lows are genuinely no-action this cycle:**

- **Low 1 (unreachable relation-kind label fallback) — forward-trigger-gated with a valid trigger.** `RelationKind` is exactly the 4-value `Literal` at `utils/relations.py:7-12` (`"many"`, `"reverse_many_to_one"`, `"reverse_one_to_one"`, `"forward_single"`), and `_RELATION_KIND_LABELS` (lines 60-65) maps all four. The `.get(kind, kind)` fallback (lines 242, 286) cannot fire for any value `relation_kind` returns today — confirmed by reading both files. The trigger ("a fifth `RelationKind` member lands without a matching label, in the same change") is genuine and falsifiable; adding a label for a non-existent kind now would be speculative. No-action correct.
- **Low 2 (CHANGELOG summary omits the `__strawberry_definition__` read path) — maintainer-deferred changelog matter, not a source defect.** The cited entry has drifted from `CHANGELOG.md:36` to `CHANGELOG.md:42` (concurrent maintainer commits inserted the `DjangoConnectionField` block above it — AGENTS.md #33 out-of-scope work), but the cited prose is verbatim intact: "reads the resolved annotation from `origin.__annotations__` ... not a `convert_scalar` re-run". The premise — that this one-liner elides the second authoritative source — holds. The source code matches its own docstrings (module docstring lines 9-21 document both paths) and the GLOSSARY entry (`docs/GLOSSARY.md:1209`) is precise (documents both `origin.__annotations__` and `origin.__strawberry_definition__`, the `"connection"`-shape exception, and the `UNRESOLVED` raise). So only the CHANGELOG summary is lossy; this is a maintainer changelog decision, not a code/docstring drift. AGENTS.md forbids unauthorized `CHANGELOG.md` edits and the active plan authorizes none. No-action correct; line-number drift is cosmetic.

### Docstring accuracy
No mis-attribution. Module docstring (lines 9-21), `_resolve_row` dispatch-order rationale (lines 178-191), `_relation_row` / `_suppressed_connection_name` / `_connection_only_relation_row` connection-shape explanations, the `_consumer_authored_row` UNRESOLVED rationale, and the lines-58-59 "unmapped kinds fall back to the raw token" comment all match the code's real (and for the fallback, currently-unreachable-but-correct defensive) behavior. The comment pass no-op is justified.

### DRY findings disposition
- Bullet 1 (parallel `_render_annotation` / `_render_strawberry_type` renderers) and bullet 2 (shared `_scalar_name` chokepoint) — concur: deliberate parallel mirrors over two distinct input vocabularies; a unified renderer would re-couple them. Not a consolidation target.
- Bullet 3 (shared import-or-CommandError shape with `export_schema`) — forwarded by citation to the folder pass `rev-management__commands.md`. That artifact does not yet exist but its checklist box is planned and open (`docs/review/review-0_0_10.md:90`, `[ ]`); a forward-by-citation is recorded in this artifact's DRY analysis for the folder pass to triage, which is the correct disposition (not a local defect). Soundly recorded.

### Temp test verification
- No temp tests required — no-source-edit cycle, every claim verified by source/artifact cross-read.

### Shape #5 checklist
1. Baseline diff empty for all owned paths — confirmed.
2. Each Worker 2 section opens with `Filled by Worker 1 per no-source-edit cycle pattern.` — confirmed (Fix report, Comment/docstring pass, Changelog disposition).
3. Every Low has verbatim trigger phrasing (Low 1) or is a maintainer-deferred changelog matter (Low 2); the DRY item is forwarded. No GLOSSARY-only fix present.
4. Changelog `Not warranted` cites BOTH AGENTS.md and the active plan's silence; `git diff -- CHANGELOG.md` empty — confirmed. Internal-only framing matches the empty diff scope.
5. `uv run ruff format --check` (1 file already formatted) + `uv run ruff check` (All checks passed) on the target — both clean.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box.
