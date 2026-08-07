# Build: R2 — Spec-versus-HEAD reconciliation for spec-001

Spec reference: `docs/SPECS/spec-001-django_types-0_0_1.md` (whole file; 42,483 bytes at pass start,
the byte count `docs/builder/bld-001-r1-rationale_move.md` `### Independent re-derivation` recorded)
Build plan: `docs/builder/build-001-django_types-0_0_1.md` (residual item R2)
Status: final-accepted

**Deviation 3 of the build plan governs this artifact.** R2 has no Worker 2 pass — `BUILD.md`
`## Spec reconciliation` and `worker-1.md` `## Scope` make Worker 1 the only role that may mutate
the spec, and R2's entire deliverable is spec edits. So this single Worker 1 pass **wrote the plan
below AND performed the reconciliation**, and `Status: planned` here means "dispatch Worker 3 for
the audit", not "dispatch a builder". The `## Reconciliation performed` section stands in for the
Worker 2 build report and keeps its subsection names so Worker 3 reads a familiar shape.

---

## Plan (Worker 1)

### Spec status-line re-verification

Re-read `docs/SPECS/spec-001-django_types-0_0_1.md` lines 1-5 at pass start. Confirmed for the third
time in this cycle: **no status/header block.** Line 1 is `# Spec: DjangoType Foundation`, line 2 is
blank, line 3 opens `## Problem statement`. There is no target-release, status, owner, or predecessor
line to falsify or edit, and this pass deletes no predecessor doc a header could point at.

The stale *body* claims that R1 recorded as "R2's axis" are exactly this pass's scope, and they are
enumerated as the dispatched-findings checklist below.

### The two judgement calls, stated up front

The maintainer's dispatch named these as mine and asked for them explicitly.

**1. Spec-001 is not a description of today's whole package.** It owns the `DjangoType`
type-generation foundation. Where a later spec took ownership of a surface, the correction is a
**pointer to the owning spec**, not a restatement — a restatement is a second copy of a contract that
nothing keeps in sync, and this document has already proved it goes stale exactly that way (the
`lazy_ref` candidate list and the `Meta.interfaces` parking claim each existed twice and were each
wrong in one copy). `spec-002-optimizer-0_0_2.md` sets the precedent for the shape with its own O4
extraction ("The O4 design record remains in `docs/SPECS/spec-003-…`"). Where the surface spec-001
still owns simply works differently now, the contract is restated in place.

Applied, this splits the fifteen rows plus the three I added into three dispositions:

- **restate** (the surface is still spec-001's): D2, D3, D4, D5, D6, D7, D8, D9, D12, D15, D16, D17, D18
- **point at the owning spec** (a later spec took the surface): D1 in part, and the optimizer half of
  `## N+1 strategy`
- **delete, recorded in the rationale** (the claim is a prediction or a status statement with no
  contract left in it): the `## Current state` status paragraph, `## What this enables immediately
  after implementation`, and four of the five illustrative code blocks

**2. Not every drift row must change the spec, and not every spec edit answers a drift row.** D13's
claim (no fakeshop M2M, dedicated test placeholder skipped) had **already left the spec** with R1's
move and is listed among that entry's *claims the spec no longer makes*; R2 confirmed it against HEAD
and made no edit, because re-editing to "answer" a discharged row adds text that says nothing.
Conversely the two largest stale surfaces are named by **no row at all** — `## Current state` (six of
the spec's twenty-one glossary anchors, and simultaneously D11 and D14) and `## Files to add` (where
D1, D2, D4 and D10 converge under a heading none of them cites). A verified drift table is organized
by *claim*; a section can be wrong four ways at once and never appear in it by name. That is the
reason `R2 owns the full sweep` is in the plan, and the reason this pass read the spec end to end
rather than working the table.

### Re-verification of the plan's fifteen rows against HEAD

`BUILD.md` `## Claims are proven mechanically, never accepted on prose` applies to every row in the
plan's table, so each was re-read at HEAD rather than accepted. **Thirteen hold exactly as tabled.
One is imprecise about the symbol. One I judged already discharged.** Three further rows the table
does not carry were found and are added as D16-D18.

| # | Re-verified at HEAD | Verdict |
|---|---|---|
| D1 | `django_strawberry_framework/types/` (`base.py`, `converters.py`, `definition.py`, `finalizer.py`, `relations.py`, `relay.py`, `resolvers.py`) and `optimizer/` are packages; `registry.py`, `exceptions.py` stayed flat; no root `types.py` / `converters.py` / `optimizer.py` | holds |
| D2 | `grep -rn 'lazy_ref' django_strawberry_framework/` → only `mutations/fields.py:151::_lazy_ref` + its `auth/` callers; nothing in `registry.py` | holds |
| D3 | `registry.py:508::add_pending_relation` / `:513::iter_pending_relations` / `:526::discard_pending`; `types/relations.py:28::PendingRelation`; `types/finalizer.py:746` walks them | holds |
| D4 | `types/base.py:65::DEFERRED_META_KEYS` = `{aggregate_class, fields_class, search_fields}`; `:69::ALLOWED_META_KEYS` contains `filterset_class`, `orderset_class` (17 keys) | holds |
| D5 | wired — but the operative symbol is **`types/relay.py::apply_interfaces`** (injects into `cls.__bases__` at finalizer Phase 2.5, `types/finalizer.py:821`), not `install_is_type_of`, which the table names. `install_is_type_of` is a separate unconditional injection. **Row imprecise; correction made against `apply_interfaces`.** | holds, symbol corrected |
| D6 | `registry.py:185::TypeRegistry.register` takes `primary: bool = False`, appends to `_types[model]`; the three raises are reverse-collision (`:224`), duplicate-primary (`:236`), primary-flag flip (`:229`) | holds |
| D7 | `SCALAR_MAP` carries `BigIntegerField: BigInt`, `JSONField: strawberry.scalars.JSON`; `convert_scalar` step 0b handles `ArrayField` → `list[inner]` and `HStoreField` → JSON via the `_ARRAY_FIELD_CLS` / `_HSTORE_FIELD_CLS` sentinels | holds |
| D8 | `types/converters.py:266::FIELD_OUTPUT_TYPE_MAP` = `{ImageField: DjangoImageType, FileField: DjangoFileType}`; the `SCALAR_MAP` comment at `:249` states the split verbatim | holds |
| D9 | `SCALAR_MAP` still maps the auto-field family to `int`; `types/base.py:1738` `suppress_pk_annotation = _is_relay_shaped(...)` and `:1790` drops the synthesized pk annotation; `types/relay.py::_resolve_globalid_strategy` owns the payload | holds |
| D10 | `ls tests/test_django_types.py tests/test_optimizer.py tests/test_choice_enums.py` → all three absent. All six spec-named choice tests exist **verbatim** in `tests/types/test_converters.py` (`:134`, `:158`, `:173`, `:201`, `:207`, `:316`) | holds |
| D11 | `examples/fakeshop/fakeshop/` does not exist; `examples/fakeshop/apps/products/` does | holds |
| D12 | `types/converters.py:679::convert_choices_to_enum` delegates to `:601::build_enum_from_choices`, shared with `rest_framework/serializer_converter.py`. **Richer than tabled: three rejections (empty / grouped / sanitize-collision), and seven sanitization rules, not four.** Naming rule `f"{type_name}{pascal_case(field.name)}Enum"` unchanged | holds, extended |
| D13 | `library.Book.genres` and `Book.alt_branches` are `ManyToManyField`; `tests/types/test_definition_relations.py:72-78` and `test_definition_order.py:119` cover both directions. **Already discharged by R1's move** — the claim is not in the spec | holds; no spec edit |
| D14 | `examples/fakeshop/apps/products/schema.py` is live, wired into `config.schema`, serving `/graphql/`; only per-line future-`Meta`-key comments remain | holds |
| D15 | `types/base.py:525` `has_custom_get_queryset = _detect_custom_get_queryset(cls)`, stamped **before** the `meta is None` early return at `:527`; `:748::_detect_custom_get_queryset` walks `cls.__mro__` to `DjangoType`; `types/definition.py:150` carries the resolved value | holds |

**Rows added by this pass (not in the plan's table):**

| # | Spec-001 claim | HEAD reality | Evidence |
|---|---|---|---|
| D16 | `PositiveBigIntegerField` -> `int` (in the scalar table *and* in the `SCALAR_MAP` code block) | `-> BigInt` | `types/converters.py:240`; `docs/GLOSSARY.md` "Scalar field conversion" records it as a `0.0.6` breaking wire-format change |
| D17 | `DurationField` -> `datetime.timedelta` and `BinaryField` -> `bytes` | **Neither is in `SCALAR_MAP` at all** — both raise the section's own unsupported-field-type `ConfigurationError` | `types/converters.py` module docstring #"Notably absent from the default map"; pinned by `tests/types/test_converters.py:565::test_convert_scalar_duration_field_raises_unsupported` and `:588::..._binary_field_raises_unsupported` |
| D18 | Under `fields = "__all__"` the products models surface relations on "Property (`category`)" | Property surfaces `category` **and** `entries` | `examples/fakeshop/apps/products/models.py::Entry.property` declares `related_name="entries"` (line 143-147), the same `related_name` as `Entry.item` |

D16 and D17 are the more serious pair: the spec promised a GraphQL mapping for two columns that in
fact fail closed at schema build. D18 is a factual error inside a sentence R1 had just promoted from
narration into contract prose — the argument for re-deriving a promoted claim at the promotion, not
only at the row that names it.

### The anchor constraint, as R1's final verification handed it over

Operative, and re-measured at this pass's start rather than inherited:

```
$ grep -o '\]\[glossary-[a-z0-9_-]*\]' docs/SPECS/spec-001-django_types-0_0_1.md \
    | sort | uniq -c | awk '{print $1}' | sort | uniq -c
  21 1
```

**All 21 anchors carried exactly one spec-body link each. There were no spare links anywhere.** Every
glossary-linked sentence was its anchor's sole link, so any rewrite that touched one had to re-site
it in the same edit. `## Current state` alone held **six of the twenty-one**, which made it the
highest-risk edit in this pass's scope and forced the ordering rule below.

`## [Scalar field conversion][glossary-scalar-field-conversion]` is a heading that doubles as an
anchor's link site, and the rationale cites its slug (`#scalar-field-conversion`) twice. **The
heading text was deliberately not reworded**, so neither the anchor's link nor the slug moved.

### DRY analysis

**Helper inventory checked.** Not applicable in the form `worker-1.md` defines it — that step exists
to prevent duplicated *code* helpers and this item writes no `.py` file and plans none, so the
package-wide AST inventory would answer a question R2 does not ask. The DRY question R2 *does* ask is
the build plan's own preamble rule, "a fact told twice across the spec and its rationale sibling goes
stale in one of them", plus the spec's own self-duplication, and both are answered per row below.

- **Existing patterns reused.** The disposition vocabulary is `spec-002-optimizer-0_0_2.md`'s own
  `## O4 extraction` shape ("the detailed record remains in `<spec>`; keep rationale there rather
  than duplicating it here") and its `## Coordination with spec-001` boundary statement. Reusing an
  existing sibling's shape means a reader who has read spec-002 can read the pointers here. The
  rationale file's entry shape (`Spec: [heading][ref]`, italic `*Moved —*` / `*Alternative
  rejected —*` / `*Claims the spec no longer makes.*` leads) is R1's, continued unchanged.
- **New helpers justified.** None. No source, no test, no script.
- **Duplication risk avoided.** Four, all real here:
  1. **Restating a later spec's contract.** The largest risk in the pass: `## N+1 strategy` could
     have been "corrected" into an accurate description of `spec-002`'s optimizer, producing a second
     copy of O2/O3/O5/O6 that goes stale on spec-002's next edit. Prevented by checking each
     paragraph against `spec-002` first and **pointing** where it is stated there.
  2. **Correcting an illustrative code block instead of deleting it.** A `SCALAR_MAP` literal or a
     `TypeRegistry` class body in a spec is a second copy of the module. Four of the five blocks were
     already wrong for exactly that reason. Prevented by deleting them behind a symbol-qualified
     pointer, each gated on locating every normative rule the block carried in surviving prose first.
  3. **The same fact in the spec and the rationale.** Every explanation of every change lands in the
     rationale only; the spec carries the corrected contract only. The one deliberate exception
     already on record — the `typing.Any` reason clause, which `BUILD.md`'s reader rule and
     `worker-1.md`'s implementation-relevant-why carve-out both claim — is R1's recorded disposition
     and this pass did not disturb it.
  4. **The spec duplicating itself.** `convert_scalar`'s ordering rule was about to be stated three
     times (the new `## Scalar field conversion` prose, `### null=True interaction`, and the naming
     rule); the redundant copy was removed before this pass closed. `## Testing strategy` was
     likewise trimmed so the per-module test inventory lives once, under `## Files to add`.

### Implementation steps

Pin-at-write-time; line numbers are from the pre-R2 spec.

1. **Add every destination link before removing any source link.** `check_spec_glossary.py` accepts
   an anchor with ≥1 link, so adding first and removing second keeps every intermediate state green;
   removing first would red the checker mid-pass and make it useless as a per-edit gate.
2. `## Goal` (39) — link `DjangoType`. `## Non-goals` (43) — link `DjangoConnectionField` and
   `apply_cascade_permissions`, both already named in plain text.
3. `## DjangoType` — restate the pipeline (68, D3); restate the deferred-key rule and rewrite its
   code block (101, 128-140, D4); restate `Meta.interfaces` and re-site `relay-node-integration`
   there (144, D5); refine the abstract-intermediate sentence.
4. `## Scalar field conversion` — correct five table rows (D7, D8, D9, D16, D17); delete the
   `convert_scalar` block (188-237, D1); repair the AutoField row's dangling forward reference.
5. `## Choice field enum generation` — restate `### Algorithm` (207-217, D12); correct
   `### Test surface` (258-260, D10).
6. `## Relation field conversion` — restate the pending-relation mechanism keeping the
   `definition-order-independence` link in place (336, D3); delete the `convert_relation` block
   (340-357, D2); correct the relation set (359, D18).
7. `## Registry` — restate the surface (365-367, D2, D6); delete the `TypeRegistry` block (369-419).
8. `## get_queryset` — restate the O6 sentinel-flip paragraph (443, D15).
9. `## N+1 strategy` — the disposition R1 item 4 reserved: keep the PR #583 carve-out and the
   opt-in surface, point the implementation at `spec-002`, delete the falsified per-slice paragraphs
   and pseudocode; re-site `djangooptimizerextension` and `only-projection` here.
10. `## Current state` → `## Prior art`, removing all six of its anchor links (now re-sited).
11. Delete `## What this enables immediately after implementation` (D14).
12. `## Testing strategy` — restate placement (386, D10); delete the illustrative test module.
13. `## Files to add` / `### Files NOT in this spec` — the un-rowed convergence of D1, D2, D4, D10,
    plus D14's example-schema claims and the `search_fields` coordination note.
14. `## References` and the surviving prior-art paragraphs — `path:NN` to symbol paths (AGENTS.md 27).
15. `## Proposed public surface`, `## Type naming` — module path and shipped-naming corrections.
16. Append the R2 half of the rationale file, keyed by spec heading; add its new link definitions.
17. Extend the spec's one global rationale pointer to name the reconciliation record.
18. Re-run both constraint commands after **every** edit and quote them.

### Test additions / updates

None, and none possible: this item writes no `.py` file. The executable checks standing in for tests
are the two constraint commands, both with a recorded baseline (`OK: 21 terms …` / `OK: 48 done
cards …`, both exit 0), plus `check_trailing_commas.py --check` and `git diff --check`.

### Implementation discretion items

None delegated — there is no Worker 2 pass to delegate to. Every judgement call is decided in
`### Implementation notes`.

### Dispatched findings checklist

R2 is neither a spec slice (spec-001's slices shipped at `0.0.1`) nor a review round, so there is no
`## Slice checklist` to copy verbatim. Per `BUILD.md` `## Review rounds`, `### Dispatched findings
checklist` is the named substitute in this position. One box per drift row plus the two un-rowed
surfaces. **Ticked by Worker 1 in this pass** because Deviation 3 gives it the performer's role;
Worker 3 audits the ticks, Worker 1 re-audits at final verification.

- [x] **D1** — *"Module layout is flat: `types.py`, `converters.py`, `optimizer.py`, `registry.py`"*
      → `types/` and `optimizer/` packages, `registry.py` flat.
      (`django_strawberry_framework/types/base.py`, `types/converters.py`, `optimizer/extension.py`,
      `registry.py::TypeRegistry`)
- [x] **D2** — *"`registry.lazy_ref(model)` is exposed, with three candidate resolution approaches"*
      → no `lazy_ref` on the registry. (`django_strawberry_framework/registry.py::TypeRegistry`;
      the surviving `mutations/fields.py::_lazy_ref` is unrelated)
- [x] **D3** — *"Slice 3 shipped eager-only … consumers must declare related `DjangoType`s in
      dependency order"* → order-independent.
      (`registry.py::TypeRegistry.add_pending_relation`, `::iter_pending_relations`,
      `types/finalizer.py::finalize_django_types`)
- [x] **D4** — *"Deferred-key rejection covers `filterset_class`, `orderset_class`,
      `aggregate_class`, `fields_class`, `search_fields`"* → the first two are allowed.
      (`django_strawberry_framework/types/base.py::DEFERRED_META_KEYS`, `::ALLOWED_META_KEYS`)
- [x] **D5** — *"`Meta.interfaces` is accepted by validation but not yet wired … subclass
      `relay.Node` directly"* → wired. (`django_strawberry_framework/types/relay.py::apply_interfaces`,
      called from `types/finalizer.py` #"if definition.interfaces:"; the table's
      `::install_is_type_of` is a different, unconditional injection)
- [x] **D6** — *"Registering the same model twice should raise `ConfigurationError` by default"* →
      many-to-one with `Meta.primary`; three narrower collisions.
      (`django_strawberry_framework/registry.py::TypeRegistry.register`, `::get`, `::primary_for`)
- [x] **D7** — *"`BigInt`, `ArrayField → list[inner]`, `JSONField`/`HStoreField → JSON` are spec'd
      but not implemented"* → all shipped. (`django_strawberry_framework/types/converters.py::SCALAR_MAP`,
      `::convert_scalar` #"sentinel-guarded postgres type")
- [x] **D8** — *"`FileField` / `ImageField` → `str` (URL/path)"* → structured read-output objects.
      (`django_strawberry_framework/types/converters.py::FIELD_OUTPUT_TYPE_MAP`,
      `::SCALAR_MAP` #"stay ``str`` here on purpose")
- [x] **D9** — *"`AutoField` / `BigAutoField` / `SmallAutoField` → `int`; relay `GlobalID` remapping
      is an open question"* → question settled; pk annotation suppressed on a Relay-Node type.
      (`django_strawberry_framework/types/base.py` #"suppress_pk_annotation = _is_relay_shaped",
      `types/relay.py::_resolve_globalid_strategy`)
- [x] **D10** — *"Tests land in `tests/test_django_types.py`, `tests/test_optimizer.py`,
      `tests/test_choice_enums.py`"* → none exists. (`tests/types/test_base.py`,
      `tests/types/test_converters.py`, `tests/types/test_relations.py`, `tests/test_registry.py`,
      `tests/optimizer/`)
- [x] **D11** — *"Example paths are `examples/fakeshop/fakeshop/products/…`"* →
      `examples/fakeshop/apps/products/…`.
- [x] **D12** — *"`convert_choices_to_enum` rejects grouped choices and sanitizes values"* → naming
      rule unchanged; a third rejection and a shared build core exist.
      (`django_strawberry_framework/types/converters.py::convert_choices_to_enum`,
      `::build_enum_from_choices`, `::_sanitize_member_name`)
- [ ] **D13** — *"no fakeshop model declares an M2M field, so the dedicated test placeholder stays
      skipped"* → M2M shipped. **No spec edit: the claim left the spec with R1's move** and is
      already listed among that entry's *claims the spec no longer makes*. Confirmed against HEAD
      (`examples/fakeshop/apps/library/models.py::Book` #"alt_branches",
      `tests/types/test_definition_relations.py::test_related_target_for_resolves_fk_m2m_and_reverse`)
      and recorded in the rationale's `### Drift rows that changed nothing, and why`.
- [x] **D14** — *"`examples/fakeshop/…/products/schema.py` is a commented-out aspirational block
      awaiting an uncomment"* → live and serving `/graphql/`.
      (`examples/fakeshop/apps/products/schema.py`, wired in `examples/fakeshop/config/schema.py`)
- [x] **D15** — *"O6 flips the sentinel with `if "get_queryset" in cls.__dict__` in
      `__init_subclass__`"* → an MRO walk, stamped before the `Meta`-absent early return.
      (`django_strawberry_framework/types/base.py::_detect_custom_get_queryset`,
      `::DjangoType.__init_subclass__` #"must be stamped BEFORE",
      `types/definition.py::DjangoTypeDefinition.has_custom_get_queryset`)
- [x] **D16 (added)** — the scalar table and its code block map `PositiveBigIntegerField` to `int`;
      HEAD maps it to `BigInt`. (`django_strawberry_framework/types/converters.py::SCALAR_MAP`)
- [x] **D17 (added)** — the scalar table promises `DurationField -> datetime.timedelta` and
      `BinaryField -> bytes`; both are absent from `SCALAR_MAP` and raise.
      (`django_strawberry_framework/types/converters.py` #"Notably absent from the default map")
- [x] **D18 (added)** — the relation set omits Property's `entries` reverse relation.
      (`examples/fakeshop/apps/products/models.py::Entry` #"related_name=\"entries\"")
- [x] **`## Current state` (un-rowed)** — an aspirational schema, a package "containing only
      `conf.py`", and six of the spec's twenty-one glossary anchors. Retitled `## Prior art`; all six
      anchors re-sited into surviving contract prose.
- [x] **`## Files to add` (un-rowed)** — where D1, D2, D4 and D10 converge under a heading no row
      names, plus `### Files NOT in this spec`'s example-schema and `search_fields` claims.

---

## Reconciliation performed (Worker 1, in place of the Worker 2 build pass)

### Files touched

- `docs/SPECS/spec-001-django_types-0_0_1.md` — every correction below.
- `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md` — the appended
  `## Item R2 — reconciliation against the shipped package` half, two factual corrections to R1-era
  prose this pass falsified, and seven new link definitions.
- `docs/builder/bld-001-r2-spec_reconciliation.md` — this artifact.
- `docs/builder/worker-memory/worker-1.md` — one appended entry (gitignored; not part of the diff).

### Byte counts

| File | R1 close | R2 close | Delta |
|---|---|---|---|
| `docs/SPECS/spec-001-django_types-0_0_1.md` | 42,483 | **43,651** | **+1,168** |
| `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md` | 24,011 | 52,961 | +28,950 |

Against HEAD (`52,341`, `git show HEAD:… | wc -c`) the spec is **-8,690 (-16.6%)** across R1 and R2
combined.

**The spec growing is the expected direction for this item and the opposite of R1's.** R1 removed a
deliberative layer; R2 replaces short false claims with correct ones that frequently need a clause of
mechanism (`"O6 adds a single line to `__init_subclass__`"` → an MRO walk plus the two properties that
make it load-bearing) — and it deletes five illustrative code blocks, which pushes the other way. The
net `+1,168` is those two forces nearly cancelling. The rationale carries the whole explanation, which
is why it grew by 25x the spec's delta: that is the mechanism working, not a copy leak, because every
byte of it is prose that was never in the spec.

### What changed, by spec heading

| Spec heading | Disposition | Rows |
|---|---|---|
| `## Current state` → `## Prior art` | Retitled; status paragraph deleted; six anchors re-sited; prior-art survey kept and its refs symbol-qualified | D11, D14, un-rowed |
| `## Goal` | Anchor destination only (`djangotype`) | — |
| `## Non-goals` | Anchor destinations only (`djangoconnectionfield`, `apply_cascade_permissions`) | — |
| `## Proposed public surface` | Module path corrected; later-public-names boundary stated | D1 |
| `## DjangoType` | Pipeline restated; abstract-intermediate rule refined; deferred-key rule + code block restated; `Meta.interfaces` restated | D3, D4, D5 |
| `## Scalar field conversion` | Five table rows corrected; `convert_scalar` block deleted; dangling forward reference answered; self-duplicated ordering sentence removed | D7, D8, D9, D16, D17 |
| `## Choice field enum generation` | `### Algorithm` restated (order, three rejections, seven sanitization rules, shared core); `### Test surface` corrected | D12, D10 |
| `## Relation field conversion` | Pending-relation mechanism restated; `convert_relation` block deleted; relation set corrected | D2, D3, D18 |
| `## Registry` | Many-to-one + three collisions restated; `TypeRegistry` block deleted; `lazy_ref` stated absent | D2, D6 |
| `## get_queryset` | O6 sentinel-flip paragraph restated with its two load-bearing properties | D15 |
| `## N+1 strategy` | Optimizer implementation pointed at `spec-002`; PR #583 carve-out kept; pseudocode + three per-slice paragraphs deleted; opt-in example corrected | R1 note 4 |
| `## Type naming` | Shipped connection naming stated in the present with its owning spec | — |
| `## What this enables immediately after implementation` | **Section deleted** | D14 |
| `## Testing strategy` | Placement restated; illustrative test module deleted; two placement rules stated | D10 |
| `## Files to add` | Module map, `exceptions.py`, registry surface, and all three test bullets corrected | D1, D2, D4, D10 |
| `### Files NOT in this spec` | Shipped-vs-planned split named; `search_fields` note restated against the live example | D14 |
| `## References` | `path:NN` → symbol paths (AGENTS.md 27) | — |

### The five illustrative code blocks, and the rule each deletion was gated on

`BUILD.md` `## Spec rationale extraction`'s over-cut hazard applies to a code block exactly as to
prose. Each deletion was gated on locating every normative rule the block carried in surviving spec
prose **first**:

| Block | Deleted? | Rules it carried, and where they survive |
|---|---|---|
| `convert_scalar` + `SCALAR_MAP` literal | yes | The unsupported-type raise → the present-tense sentence R1's repair 2 added, one paragraph below where the block sat. The choices-then-null ordering → `### null=True interaction`. The map itself → the section's own scalar table, which is normative and now correct. |
| `convert_relation` | yes | Cardinality → the section's own cardinality table, one paragraph above. The lazy-target rule → the restated pending-relation paragraph. |
| `TypeRegistry` | yes | `register` / `get` / enum cache / `clear()` → restated in prose. The collision rule the block encoded was *retracted*, not relocated (D6). |
| `plan_relation` pseudocode | yes | The downgrade rule → the surviving prose rule immediately above it, which states it more precisely than the code did. `spec-002` O6 owns the planner. |
| `tests/test_django_types.py` module | yes | The `registry.clear()` fixture and the live-tier placement → the two placement rules that replaced it, both of which the block taught only by accident. |
| `Meta`-key consumer examples (3 blocks under `## DjangoType`) | **no — corrected** | They illustrate the *consumer* surface this spec owns, so there is no module to defer to. The deferred-key block dropped `filterset_class` / `orderset_class`; the other two were already accurate. |

Python fence count: 12 at HEAD → **7** now (`grep -c '^```python'`), i.e. exactly the five deletions,
R1 having removed none.

### Anchor re-siting: destination named before the source was touched

Six anchors left `## Current state`. Each destination is a sentence where the concept is **normative**
rather than incidental, and each was added before the source paragraph was removed:

| Anchor | New home | Why that sentence |
|---|---|---|
| `djangotype` | `## Goal` | The one sentence that says what the spec adds |
| `djangoconnectionfield` | `## Non-goals` | Already named it in plain text as out of scope |
| `apply_cascade_permissions` | `## Non-goals` | Same |
| `relay-node-integration` | `## DjangoType`, the restated `Meta.interfaces` paragraph | Where the Relay-shape consequence is now stated |
| `djangooptimizerextension` | `## N+1 strategy` opener | Where *this package's* extension is specified — the old site was a sentence about strawberry-graphql-django's same-named class |
| `only-projection` | `## N+1 strategy`, the spec-002 ownership sentence | Where the projection rule is named |

The `## [Scalar field conversion][glossary-scalar-field-conversion]` heading was **not** reworded, so
neither its anchor link nor the `#scalar-field-conversion` slug the rationale cites twice moved.

### Validation run

Both constraint commands were re-run after every edit **group** — fifteen runs across twenty-five
spec edits, never batched to the end, and never more than one section's worth between two runs.
Stating it as "after every edit" would over-claim: several sections were edited two-to-four times
(the `## DjangoType` block was four) before the pair ran. The property that matters held throughout —
**no anchor was ever below one link at any checkpoint**, which the add-destination-before-removing-
source ordering guarantees and the fifteen green runs confirm. Final state:

```
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-001-django_types-0_0_1.md
OK: 21 terms - all have glossary entries and at least one spec link.
exit=0

$ uv run python examples/fakeshop/manage.py import_spec_terms --check
OK: 49 done cards have glossary links.
exit=0

$ uv run python scripts/check_trailing_commas.py --check \
    docs/SPECS/spec-001-django_types-0_0_1.md \
    docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md
exit=0

$ git diff --check -- docs/SPECS/spec-001-django_types-0_0_1.md
exit=0
```

**The 21-term baseline is held exactly. The done-card count moved from 48 to 49 mid-pass, and it is
not this cycle's doing** — the concurrent session wrapped card `DONE-049-0.0.14` (dependency / CI
hardening) while R2 was running, which is why `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`,
`docs/spec-049-dependency_ci_hardening-0_0_14.md` and `examples/fakeshop/db.sqlite3` are dirty below.
The property the constraint actually asserts — **every done card, including `DONE-001-0.0.1`, still
has its glossary links** — holds at exit 0 on both sides of the change. Recording the number that
came back rather than the number the plan predicted is the point: R1's handoff item 2 said to
re-establish this baseline at R2's start rather than inherit it, and the same reasoning says report
what it now is rather than quote a stale 48 that happens to look reassuring.

**The terms CSV was not touched** (`git status` clean for
`docs/SPECS/appx/spec-001-django_types-0_0_1-terms.csv`), and no anchor was rescued by re-adding
narration R1 removed.

No `ruff`: no `.py` file was touched. No `pytest`: no test exists for a Markdown reconciliation and
the plan calls for none.

### Anchor budget after this pass

```
$ grep -o '\]\[glossary-[a-z0-9_-]*\]' docs/SPECS/spec-001-django_types-0_0_1.md \
    | sort | uniq -c | awk '{print $1}' | sort | uniq -c
  20 1
   1 2
```

**21 distinct anchors, 22 body links.** `configurationerror` gained a second link (the restated
`Meta`-validation sentence in `## DjangoType` and the registry-collision sentence in `## Registry`
both raise it, and both name it); the other twenty still carry exactly one each. The constraint R1
handed over therefore still governs everything except that one anchor: **every other
glossary-linked sentence remains its anchor's sole link.** Carry that forward to R3 unchanged.

### Link and anchor resolution

Mechanically re-derived over both files after the last edit:

- Reference-style throughout; no inline `](path)` cross-file links in either body outside code fences.
- One `<!-- LINK DEFINITIONS -->` block each, all 10 canonical group headers present in START.md's
  exact order, empty groups retained (verified positionally).
- Spec: **22 defs / 22 used refs**, 0 undefined, 0 orphaned. Rationale: **18 / 18**, 0 / 0.
- Every path `os.path.exists`-checked on the normalized join from its own file's directory — all 40
  defs across both files resolve on disk.
- Every in-page anchor the rationale cites resolves against a surviving spec `## ` heading, computed
  with the repo's own `scripts/check_spec_glossary.py::github_anchor` rather than by eye. The eight
  R1 anchors still resolve; the seven new ones (`#prior-art`, `#proposed-public-surface`,
  `#get_queryset`, `#type-naming`, `#testing-strategy`, `#files-to-add`, `#references`) resolve too.
  Unresolved set empty.
- Defs alphabetical within every group in both files.
- **The two headings this pass removed or renamed have no inbound anchor anywhere in the repo:**
  `grep -rn 'spec-001-django_types-0_0_1\.md#'` returns only the rationale's own eight-then-fifteen
  defs, none targeting `#current-state` or `#what-this-enables-immediately-after-implementation`.

### Concurrent-session churn observed (not this pass's, not reverted)

The tree carried, at various points during the pass and beyond this cycle's four paths:
`M .github/workflows/kanban-pages.yml`, `M tests/test_ci_governance.py` (both since committed as
`fdfb711f`, *"ci: restore the Pages deploy job's runner and assert every job has one"*), then
`M SECURITY.md`, `M TODAY.md`, `M uv.lock`, and finally — during this pass's own closing minutes — a
full card wrap: `M KANBAN.md`, `M KANBAN.html`, `M docs/GLOSSARY.md`,
`M docs/spec-049-dependency_ci_hardening-0_0_14.md`, `M examples/fakeshop/db.sqlite3`.

Attribution is positive rather than inferred, and the card wrap is identified rather than guessed at:
`git diff -- KANBAN.md` adds `DONE-049-0.0.14 - Dependency and CI hardening`, and `docs/GLOSSARY.md`
gains exactly two lines — the spec-049 surface, not spec-001's. R2's writable list contains no CI,
docs-root, KANBAN, GLOSSARY, lockfile or DB path, and no spec other than spec-001. The only
DB-touching command this pass ran is `import_spec_terms --check`, whose `--check` branch returns
**before** the `with transaction.atomic():` block that performs every write
(`examples/fakeshop/apps/glossary/management/commands/import_spec_terms.py::Command.handle`) — read
verified this pass, not inherited from R1's claim. `AGENTS.md` rule 34: recorded, not reverted, not
edited.

**Consequence for R3, which the plan could not anticipate.** The build plan's
`## Concurrent-writable tracked binary / generated files` says no residual item is expected to write
`db.sqlite3`, `KANBAN.md` / `KANBAN.html` or `docs/GLOSSARY.md`, and that a diff in the glossary
"means drift to investigate, not build output". All four are now dirty from a concurrent card wrap,
so **R3 cannot read a dirty generated doc as evidence of spec-001 drift.** It must diff the semantic
content (`iterdump()` for the DB, a fresh regenerate for the docs) and attribute before concluding,
per `BUILD.md` `### Tracked binary / generated files: churn and concurrent-writer handling`.

**HEAD moved during the pass** (`b29b851e` → `fdfb711f`). Nothing in that commit touches spec-001 or
its companions, and the `52,341`-byte HEAD baseline this artifact cites is unaffected — the spec's
blob is identical in both commits.

### Failability proofs

None; this pass introduced no new boundary, guard, gate, or rejection path. It writes no executable
code.

### Hot-path budget

Not applicable; plan declares no hot path (`build-001-django_types-0_0_1.md` preamble: *"Hot-path
declaration: none"*).

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- **Add-then-remove is the ordering that makes the checker useful.** Every anchor destination landed
  in an earlier edit than the removal of its source, so `check_spec_glossary.py` was green at all
  fifteen checkpoints. Removing first would have made the checker red for most of the pass, and a
  gate that is expected to be red cannot catch the failure it exists for.
- **`## Current state` was retitled rather than rewritten or deleted.** A section named "Current
  state" is a standing promise no shipped spec can keep — this one had been wrong about the package's
  contents for the package's whole life. Its two surviving paragraphs are a prior-art survey, which is
  durable and is what `## What both libraries overlap on` and `## References` already assume sits
  above them. Retitling makes the section's obligation one it can meet. The alternatives (restate as
  the package's present state; delete outright) are recorded in the rationale with why each lost.
- **`## N+1 strategy` was cut, but not all the way.** The spec's own cut-line prediction (now in the
  rationale) names the whole section for lifting. `spec-002` states O2/O3/O5/O6, so those paragraphs
  are pointers now — and three of the five were *also factually wrong*, which makes deleting strictly
  better than maintaining a second copy. But `spec-002` states the O6 rule **without its reason**, and
  its only #572 / #583 mention frames them as the bundling argument. So the PR #583 carve-out —
  *otherwise FK joins bypass per-type visibility filtering and leak rows* — has its sole statement
  here, R1 flagged it as must-survive, and `spec-002` is outside this cycle's write set. It stays.
  Recorded as a rejected alternative so a later cycle whose scope includes `spec-002` can re-open it
  on purpose rather than by accident.
- **The illustrative-block deletions are the pass's largest single judgement**, and the gate was
  mechanical: locate the rule in surviving prose, then delete. Two of the five blocks named a symbol
  that does not exist (`registry.lazy_ref`, `convert_relation`), and one asserted a raise for a key
  that now wires through — a reader copying them gets a `NameError`, then a test asserting an
  impossible exception.
- **`Meta.interfaces` corrected against `apply_interfaces`, not `install_is_type_of`.** The plan's D5
  names the latter. Both exist; only `apply_interfaces` injects into `cls.__bases__` and only it is
  gated on a non-empty `Meta.interfaces`. `install_is_type_of` is unconditional and unrelated to the
  claim. Re-verification is what caught it; the row would otherwise have produced a correct-sounding
  correction naming the wrong symbol.
- **Two R1-era rationale sentences were corrected, not appended around.** The `## How to read this
  file` bullet said reconciliation "is item R2's determination" (now: it has run, and where the record
  is), and the `## Post-slice-7 future work` bullet said the `search_fields` coordination note "stays
  in the spec" (now: its premise was found already discharged, with a forward pointer). Both are
  factual corrections to prose about *this file's own state*, which is the precedent R1's own final
  verification set with its edits 4-7 — not edits to moved spec text, which stays untouched.
- **Every count in this artifact was measured at the moment of writing**, per the practice failure
  R1's handoff item 3 recorded: 21 anchors / 22 links by `uniq -c`; 12 → 7 python fences by `grep -c`;
  22/22 and 18/18 link defs by script; 40 paths by `os.path.exists`; byte counts by `wc -c` against
  the R1 artifact's recorded 42,483 and `git show HEAD:… | wc -c`.

### Notes for Worker 3

- **The audit's sharpest question is over-cut, and it now has two shapes.** The first is R1's: did a
  cut sentence carry the only statement of a rule? The second is R2's and is new: did a *pointer*
  replace a rule that the pointed-at spec does not actually state? Read `### The five illustrative
  code blocks` and the `## N+1 strategy` note first, then check `spec-002-optimizer-0_0_2.md` yourself
  for each lifted paragraph. The PR #583 carve-out is the one that must be in spec-001 and nowhere
  else; if it is missing from `## N+1 strategy`, that is a High.
- **Re-derive D16, D17 and D18 rather than accepting them.** They are this pass's own additions to the
  drift table, so no prior worker verified them. D17 in particular changes a promise consumers could
  have relied on: `DurationField` and `BinaryField` raise. `tests/types/test_converters.py:565` and
  `:588` are the pins.
- **Re-run both constraint commands yourself.** The 21-anchor rule is the one failure mode of this
  pass that stays silent until `import_spec_terms` runs, and this pass moved six anchors.
- The diff to read is `git diff -- docs/SPECS/spec-001-django_types-0_0_1.md` (which contains R1's
  changes too — R1 is uncommitted; the R1 artifact's `### What moved, by spec heading` table
  separates them) plus the untracked
  `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md`. Do not `git stash`, `git checkout` or
  `git restore` anything — the tree carries a concurrent session's work.
- **A passage this pass left alone is not automatically a finding.** `## Suggested implementation
  slices` still names slices, and `## Problem statement` / `## What both libraries overlap on` /
  `## Type naming`'s scope sentence are unchanged because HEAD does not falsify them. A finding needs
  a HEAD-falsified claim, not an unfamiliar one.

### Notes for Worker 1 (spec reconciliation)

Carried into R3 and the final gate.

1. **The anchor constraint, updated.** 21 anchors / 22 body links: `configurationerror` now has two,
   every other anchor exactly one. R3 touches no spec-001 prose by its own scope, but it *does* edit
   `spec-002`, and it must re-run `check_spec_glossary.py` against spec-001 if anything changes there
   anyway.
2. **`spec-002:9` and `spec-002:80` are still open, and R1's Finding 4 hand-over still stands
   unchanged.** Both point into text that lives only in spec-001's rationale. R2 did **not** act on
   them: `spec-002` is outside R2's writable list, exactly as R1 judged. R3 must assign the edit to
   its **Worker 1** pass, not its Worker 2, because `spec-002` is a spec file. The minimum discharge
   is a pointer naming `appx/spec-001-django_types-0_0_1-rationale.md`, not new narration.
3. **A third `spec-002` reference is now in play, and it is a new obligation R2 created.** This pass
   moved the optimizer implementation paragraphs out of spec-001 on the grounds that `spec-002`
   states them. `spec-002-optimizer-0_0_2.md` `## Coordination with spec-001-django_types-0_0_1.md`
   is the natural place to record that the lift finally happened, and R3's Worker 1 pass is already
   editing that file for item 2. Recommend folding it in there rather than opening a fourth pass.
4. **A correctness observation about the package, recorded not fixed** (this cycle changes no source,
   per the plan's build-wide context flags). None found. Every symbol, guard and rejection this pass
   read against the spec behaves as the code's own docstrings claim; the three defects found were all
   in the spec, not the package. The one thing worth a maintainer's eye is a **documentation** gap
   rather than a code one: `DurationField` and `BinaryField` raise `ConfigurationError` on any model
   that declares one, and while `docs/GLOSSARY.md` "Scalar field conversion" and the converter
   module's docstring both say so, `README.md` and `TODAY.md` were not checked by this pass. R3's
   durable-doc audit should include them.
5. **`## Suggested implementation slices` is the last section carrying slice vocabulary, and that is
   deliberate.** R1 decided it (a slice list is a plan; its *status* annotations were the narration
   and those left with R1), and R2 did not re-open it. If a later reader proposes removing it, the
   decision is recorded in both artifacts rather than needing re-derivation.
6. **Re-measure `git status` at R3's start, and expect the generated docs to be dirty.** HEAD moved
   twice during this cycle (`b29b851e`, then `fdfb711f`) and the tree has carried five different
   concurrent-session file sets, ending with an **uncommitted `DONE-049-0.0.14` card wrap** that
   touches `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md` and `examples/fakeshop/db.sqlite3` — the
   four files R3's durable-doc audit reads. Neither "assume clean" nor "assume dirty" survives;
   derive the verification strategy from what R3 actually finds, and attribute every generated-doc
   diff before treating it as spec-001 drift.
7. **The `import_spec_terms --check` baseline is now `OK: 49 done cards`**, not the plan's 48, for
   the same reason. The number is not the contract — exit 0 is — but a later pass that quotes 48 from
   the plan and sees 49 will waste time deciding whether it broke something.

---

## Review (Worker 3)

Audit of the R2 spec-versus-HEAD reconciliation. Everything below was re-derived from the working
tree and from package source — `BUILD.md` `## Claims are proven mechanically, never accepted on
prose` applies to every count and every "HEAD says X" claim in `## Reconciliation performed`, and
this cycle has already lost five asserted counts to re-derivation. Nothing here is read out of the
artifact.

**What was re-derived, and how.** Byte counts by `wc -c` against the working tree and
`git show HEAD:<path> | wc -c` (read-only; no `stash` / `checkout` / `restore`). The eighteen drift
rows against package source directly, never against the spec. Python-fence counts by `grep -c` on
both the working tree and the HEAD copy, with each HEAD fence located by line so the five deletions
are identified rather than inferred. Anchor budget by counting `][glossary-<id>]` **occurrences**.
Link definitions, group headers, alphabetical order, undefined / orphan refs, on-disk path existence
and every in-page anchor by `docs/builder/temp-tests/r2-spec001/links.py` +`anchors.py` (the anchor
check strips reference-link markup from the heading before `check_spec_glossary.py::github_anchor`
— see Low 5). Spec-versus-rationale duplication by a maximal-shared-shingle scan
(`overlap.py`, n=8, fences and link-def blocks stripped). Both constraint commands re-run in full.

### High:

None.

The two defects this audit exists to catch are both absent. **The PR #583 carve-out survives** —
spec line 349, *"otherwise FK joins bypass per-type visibility filtering and leak rows"* — and
reading `spec-002-optimizer-0_0_2.md` end to end confirms the premise for keeping it: its O6 entry
states the rule without the reason, and its only #572 / #583 mention frames them as the bundling
argument. And **no corrected claim is false.** Every one of D1-D18 was re-read against source; all
eighteen hold as the pass states them, including the three the pass added itself.

### Medium:

#### 1. `## Files to add` still narrates the spec's own history

`docs/SPECS/spec-001-django_types-0_0_1.md` #"were single modules when the first slices landed"

The section opener reads: *"File paths … name where each module lives today; `types/` and
`optimizer/` **were single modules when the first slices landed and became packages under the later
restructure**, so a reference to `types.py` or `optimizer.py` in an older document means the package
of the same name."*

The claim is factually true (`git log --diff-filter=AD` confirms `types.py` / `converters.py` /
`optimizer.py` were added at `084b4643` and deleted at `70c7bff2`), and that is exactly the problem:
it is a chronology, and it is the only surviving one in the spec that a reader must apply to work
out what is currently true. `BUILD.md` `## Spec rationale extraction`: *"The spec reads as a clean
current contract, as though it had been right from the start; a reader must never reconstruct what
is currently true by applying a chronology to it."* "where each module lives today" is a version-
tense hedge on top. This is R2's own declared axis, inside a section its checklist ticks, and the
rationale already carries the same fact under `### `## Files to add`` (*"`types.py` and `optimizer.py`
are packages"*), so the spec copy is redundant as well as chronological.

**Recommended change.** State the map in the present with no history: the modules this spec adds are
`django_strawberry_framework/types/` (a package), `optimizer/` (a package), `registry.py`,
`exceptions.py`, `py.typed`. The older-document translation aid, if it is worth keeping at all, is a
rationale sentence — the rationale's `## Files to add` entry is already its home.

#### 2. The lifted optimizer paragraphs carried two rules `spec-002` does not state

`docs/SPECS/spec-001-django_types-0_0_1.md` #"and its family own the optimizer's architecture"

The pass's own `### Notes for Worker 3` names this shape as the audit's second sharpest question —
*"did a pointer replace a rule that the pointed-at spec does not actually state?"* — so I checked
each lifted paragraph against `spec-002`. Three of the five are covered. Two are not:

- **The O5 reason.** The deleted paragraph said `only()` must carry both the local FK column and the
  joined columns, *"without those, Django marks the joined attributes as deferred and triggers an
  extra query the moment the resolver accesses them — a silent N+1 that the optimizer was supposed
  to prevent."* `spec-002` O5 is one sentence of mechanism ("records selected scalar columns and
  required FK connector columns in `OptimizationPlan.only_fields`") and carries no reason.
- **O6's every-branch visibility clause.** The deleted paragraph said *"Every `plan_relation` call
  also runs `target_type.get_queryset(target_qs, info)` … so visibility filtering applies regardless
  of which plan branch fires."* `spec-002` O6 covers only the downgrade branch ("avoids
  `select_related` … emits a `Prefetch` with the target queryset instead"). The surviving spec-001
  rule likewise covers only the would-be-`select_related` case. Nothing now states that the
  many-side prefetch is also visibility-filtered — and that is the same data-isolation family as the
  carve-out the pass correctly kept.

This is not an argument for restoring the paragraphs to spec-001 — the disposition is right, and
HEAD's text had already attributed both to `spec-002` by name. It is an argument that
`### Notes for Worker 1` item 3, as written, will not close it: it asks R3's Worker 1 pass to
*"record that the lift finally happened"* in `spec-002`'s `## Coordination with spec-001`, and a
pass that does literally that leaves both rules stated nowhere.

**Recommended change.** Re-word item 3 to name the two clauses `spec-002` must gain, so the
obligation is discharged by content rather than by a pointer. `spec-002` is outside every writable
list in this cycle, so this is **escalated to Worker 1** rather than held against R2 — see
`### Notes for Worker 1 (spec reconciliation)`.

#### 3. The `extensions=` correction restates `spec-029`'s contract with no pointer

`docs/SPECS/spec-001-django_types-0_0_1.md` #"The callable-factory form in"

The corrected opt-in block and its trailing sentence — *"The callable-factory form in `extensions=`
is what preserves the extension instance's plan cache across operations; the bare-instance form
Strawberry deprecated in `0.316.0` is not the supported spelling"* — is a restatement of
`spec-029-consumer_dx_cleanup-0_0_9.md` Decision 3 (*"Slice 1 adopts the singleton factory
`extensions=` form"*), which owns the plan-cache argument, the per-request `get_extensions`
mechanism, and the deprecation-warning finding. `spec-029` is not named anywhere in spec-001.

That is the exact duplication the pass's own judgement call 1 declares it prevented: *"Where a later
spec took ownership of a surface, the correction is a pointer to the owning spec, not a restatement
— a restatement is a second copy of a contract that nothing keeps in sync."* Every sibling
correction in the pass honours it — `spec-008`, `spec-015`, `spec-018`, `spec-030`, `spec-031`,
`spec-037` are each named at the site of their correction. This one is the single exception, and it
is a second copy of a claim about **upstream version behavior**, which is the copy most likely to
rot.

**Recommended change.** Keep the corrected code block (a consumer example is spec-001's own surface)
and attribute the sentence: *"… owned by `spec-029-consumer_dx_cleanup-0_0_9.md`."*

#### 4. Three asserted counts do not survive re-derivation

`docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md` #"was four steps and is",
#"a 26-method" — and `docs/builder/bld-001-r2-spec_reconciliation.md` #"seven sanitization rules, not four"

`### Implementation notes` asserts *"Every count in this artifact was measured at the moment of
writing"*, discharging R1's handoff item 3. Three counts do not hold:

| Asserted | Re-derived | How |
|---|---|---|
| "seven sanitization rules, not four" (artifact ×2; rationale: *"was four steps and is now seven"*, and *"claims the spec no longer makes … that sanitization is four steps"*) | no unit yields 4 -> 7 | HEAD's spec step 4 enumerates **three** sanitization operations (`str()` coercion, non-identifier -> `_`, `MEMBER_` on leading digit). The corrected spec text enumerates **five** clauses. `types/converters.py::_sanitize_member_name`'s docstring numbers **four** rules. |
| "a 26-method registry" / "the real class carries twenty-six methods" | **27** | `ast` walk of `registry.py::TypeRegistry` -> 27 `FunctionDef`s. 26 only if `__init__` is silently excluded. |
| "a 24-entry scalar map" | **26** (real map) / **23** (the deleted block) | `ast` `len(SCALAR_MAP.keys)` = 26; `grep -c 'models\..*:'` over the HEAD illustrative block = 23. Neither is 24. |

None of these is in the spec, and none changes a contract — all three sit in argumentative positions
(why an illustrative literal is a second copy; how much richer HEAD's sanitizer is). But two live in
the **rationale**, a standing doc, and one of them propagates into a *"claims the spec no longer
makes"* line, which is a factual assertion about what the old spec said. `BUILD.md` makes a stated
count one of the three claim shapes whose unverified assertion is a Medium, and this is the fifth,
sixth and seventh count in this cycle to fail re-derivation.

**Recommended change.** Re-measure and restate all three, or replace each with a form the reader can
re-derive (name the rules rather than counting them; say "every method on `TypeRegistry`" rather
than a number). The `## Choice field enum generation` *"claims the spec no longer makes"* bullet
needs the same correction, since the spec's old claim was three steps, not four.

### Low:

1. **A raw `path:NN` ref survives in the rationale, inside the entry that explains the ban.**
   `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md` #"is `DjangoObjectType` today" reads
   ``(`graphene_django/types.py:132-258` is `DjangoObjectType` today and could be anything
   tomorrow)``. It is a quotation illustrating the banned form, and it is the file's only hit — but
   `AGENTS.md` rule 27 permits the form only in `docs/builder/bld-*.md`, and a repo-wide sweep for
   the pattern lands on it. (For what it is worth the example is accurate: `types.py:132` is
   `class DjangoObjectType` in the named checkout today.) Paraphrase rather than spell it.

2. **The D13 box is ticked though no correction landed in the diff.** `### Dispatched findings
   checklist` D13 is `- [x]` and then says, in the same box, *"No spec edit: the claim left the spec
   with R1's move."* I confirmed both halves — the claim is absent from the spec, and the rationale's
   `### Drift rows that changed nothing, and why` carries it. `BUILD.md` `### Dispatched findings
   checklist` reserves the tick for a box "whose fix actually landed in its diff this pass" and puts
   a deferral in prose instead, so the faithful shape is `- [ ]` plus exactly the sentence already
   written. Transparent, verifiable, and cosmetic — recorded so the audit trail is not silently
   loosened.

3. **"the bare-instance form Strawberry deprecated in `0.316.0`" over-attributes.** What is verified
   (by `spec-029` Decision 3 and by `strawberry/schema/schema.py` #"deprecated and will be removed
   in a future release") is that `0.316.0` — the declared floor — *warns*. Which release introduced
   the deprecation is not established anywhere in this repo, and the standing rule is to audit an
   upstream seam across the published range rather than the one version to hand. "as of `0.316.0`"
   is the provable form.

4. **"Consumer-written forward references are honoured on the same footing" is a new contract
   sentence with no symbol pointer.** `docs/SPECS/spec-001-django_types-0_0_1.md` #"honoured on the
   same footing". The behaviour is real — a consumer-authored annotation lands in
   `types/base.py` #"consumer_authored_fields" and is excluded from relation deferral, pinned by
   `tests/types/test_definition_order.py::test_annotation_only_relation_override_keeps_generated_resolver`
   — but it is **not** the same footing in the mechanical sense: those fields bypass the
   `PendingRelation` pass entirely and rely on Strawberry's own resolution, which is the opposite of
   the sentence immediately preceding it. Of the three spellings named, only the plain annotation
   form has a pin in `tests/types/`; the cross-module `strawberry.lazy` spelling on a `DjangoType`
   relation has none there. Tighten to "are left untouched and resolved by Strawberry" and cite the
   symbol, or drop the third spelling.

5. **`### Link and anchor resolution`'s method claim does not hold for one heading.** The artifact
   says every in-page anchor was "computed with the repo's own
   `scripts/check_spec_glossary.py::github_anchor` rather than by eye". Fed the raw heading
   `## [Scalar field conversion][glossary-scalar-field-conversion]`, that function returns
   `scalar-field-conversionglossary-scalar-field-conversion` — it strips `[` and `]` as non-word
   characters rather than rendering the link, so `#scalar-field-conversion` reads as unresolved. The
   **conclusion is right** (GitHub slugs the rendered label, and my own run with link markup
   stripped first resolves all 15 of 15), but the method as described produces a false negative on
   the one heading in this spec that is itself a link. Worth stating, because the next pass copying
   the method verbatim gets that false negative — I did.

### DRY findings

- **Spec-versus-rationale shared text grew from 150 words / 11 runs to 259 words / 22 runs.**
  Measured with the same maximal-shared-shingle scan R1's final verification used (n=8, fences and
  link-def blocks stripped): 259 shared words against a 5,766-word spec body, 4.5%. There is no
  wholesale copy and no contract leak — the dangerous direction, contract leaving the spec, is
  clean. Classifying the eleven new runs: most are quotation-with-attribution or the minimal
  contrast a *"claims the spec no longer makes"* entry cannot avoid, which is the mechanism working.
  Four are pure restatement of the corrected contract with no framing that says so — the cache-check
  ordering (13w), `Meta.primary` many-to-one (12w), the plan-cache-across-operations clause (10w),
  and the `ChoiceFixture` `app_label` / autouse-`registry.clear()` mechanism (10w + 10w). The plan's
  own preamble rule is "a fact told twice across the spec and its rationale sibling goes stale in
  one of them", and `### DRY analysis` asserts *"the spec carries the corrected contract only"*
  without measuring it. Not a blocker and not worth a rewrite on its own; recorded with the number
  so the next rationale extraction has a baseline and so the assertion is not carried forward as
  measured.
- **Existence challenge: none raised.** This item adds no helper, registry, indirection layer or
  abstraction — it writes no `.py` file. The one structural addition, the `spec-NNN` pointer idiom,
  is `spec-002`'s existing shape reused rather than a new mechanism, which is the right answer.

### The eighteen drift rows, re-derived against source

Each row read against the package, never against the spec. `holds` = the spec's corrected text
matches HEAD.

| # | Evidence re-derived this pass | Verdict |
|---|---|---|
| D1 | `django_strawberry_framework/types/` and `optimizer/` are packages; `registry.py` / `exceptions.py` flat; `git log --diff-filter=AD` confirms the three flat modules existed and were deleted at `70c7bff2` | holds |
| D2 | `grep -rn lazy_ref django_strawberry_framework/` -> only `mutations/fields.py::_lazy_ref` + its `auth/` callers; `registry.py` has none | holds |
| D3 | `registry.py::TypeRegistry.add_pending_relation` / `::iter_pending_relations` / `::discard_pending`; `types/relations.py::PendingRelation`; `types/finalizer.py` Phase 1 | holds |
| D4 | `types/base.py::DEFERRED_META_KEYS` = exactly `{aggregate_class, fields_class, search_fields}`; `::ALLOWED_META_KEYS` = 17 keys incl. `filterset_class` / `orderset_class`; `tests/types/test_base.py` parametrizes the rejection over exactly the three | holds |
| D5 | **The pass's symbol correction is right.** `types/relay.py::apply_interfaces` is the only `__bases__` injection and `types/finalizer.py` #"if definition.interfaces:" is the only gate on it (Phase 2.5, before Phase 3's `strawberry.type`). `::install_is_type_of` is unconditional and unrelated to `Meta.interfaces`. `types/base.py::_is_relay_shaped` is the single predicate both spellings go through, so "equivalent spelling" holds too | holds, plan's symbol was wrong |
| D6 | `registry.py::TypeRegistry.register` appends to `_types[model]`, `primary: bool = False`; exactly three collision raises (reverse, duplicate-primary, primary flip); `::get`'s three return states match the spec sentence verbatim; all three pinned in `tests/test_registry.py` | holds |
| D7 | `SCALAR_MAP` carries `BigIntegerField: BigInt`, `JSONField: strawberry.scalars.JSON`; `convert_scalar` step 0b handles `ArrayField` -> `list[inner]` and `HStoreField` -> JSON | holds |
| D8 | `types/converters.py::FIELD_OUTPUT_TYPE_MAP` = 2 entries (`ImageField`, `FileField`); the `SCALAR_MAP` comment states the split; module docstring confirms "nullable by default" | holds |
| D9 | auto-field family still `int`; `types/base.py` #"suppress_pk_annotation = _is_relay_shaped"; the pk-drop branch's own comment states the pk **stays in `fields`** "so the optimizer's field map still sees it as a connector column" — the spec's clause matches it | holds |
| D10 | `ls` -> all three named files absent; all six named tests present **verbatim** in `tests/types/test_converters.py`; the five-module inventory in `## Files to add` all exist | holds |
| D11 | zero `fakeshop/fakeshop` occurrences left (5 at HEAD); `examples/fakeshop/apps/products/` exists | holds |
| D12 | `::build_enum_from_choices(choice_pairs, enum_name, *, source_label)` signature exact; three rejections in that order; cache-check-first confirmed in `::convert_choices_to_enum`; shared with `rest_framework/serializer_converter.py`; the "order is load-bearing" clause matches `::_sanitize_member_name`'s own docstring | holds (but see Medium 4 on the rule count) |
| D13 | claim absent from the spec; `library.Book.genres` / `alt_branches` are M2M; recorded in the rationale | holds; no spec edit (see Low 2) |
| D14 | `examples/fakeshop/apps/products/schema.py` is live and wired; only per-line `search_fields` comments remain, each individually commented beside `TODO-BETA-047-0.1.2` — which is exactly what the restated `### Files NOT in this spec` note claims | holds |
| D15 | `types/base.py::DjangoType.__init_subclass__` stamps from `::_detect_custom_get_queryset` **before** the `meta is None` return (the source comment says so and names the pinning test); `::_detect_custom_get_queryset` walks `cls.__mro__` and stops at `DjangoType`; `::has_custom_get_queryset` reads `types/definition.py::DjangoTypeDefinition.has_custom_get_queryset` with the negated-sentinel fallback | holds |
| **D16** | `types/converters.py::SCALAR_MAP` #"PositiveBigIntegerField: BigInt". Corroborated independently: `docs/GLOSSARY.md` #"switched from `int` to `BigInt` in `0.0.6`" records it as a breaking wire-format change | **confirmed** |
| **D17** | Neither `DurationField` nor `BinaryField` appears in `SCALAR_MAP` (26 entries, enumerated by `ast`); the module docstring #"Notably absent from the default map" states both and names `strawberry.scalars.Base64` as the plug, exactly as the spec now does; pinned by `tests/types/test_converters.py::test_convert_scalar_duration_field_raises_unsupported` and `::test_convert_scalar_binary_field_raises_unsupported` | **confirmed — the pass's most consumer-visible correction** |
| **D18** | `examples/fakeshop/apps/products/models.py::Entry.property` and `::Entry.item` both declare `related_name="entries"`, so Property surfaces `category` **and** `entries`. The spec's full corrected set — Category(`items`,`properties`), Item(`category`,`entries`), Property(`category`,`entries`), Entry(`property`,`item`) — matches the models exactly | **confirmed** |

### The five deleted code blocks, re-verified

`grep -c '^```python'`: **12** at HEAD, **7** now. Each HEAD fence located by line number, so the
five are identified rather than inferred: `convert_scalar`+`SCALAR_MAP` literal, `convert_relation`,
`TypeRegistry`, the `plan_relation` pseudocode, and the illustrative test module. The four surviving
HEAD blocks (the import example, the enum-reuse example, the `get_queryset` example, the schema
opt-in) are all still present, and none of the R1-removed sections contained a fence — so "R1 having
removed none" holds. The three `Meta`-key consumer blocks were kept and the deferred-key one
correctly dropped `filterset_class` / `orderset_class`.

Each deletion's normative rules located in surviving prose:

- **`convert_scalar`** — the unsupported-type raise survives at #"must raise `ConfigurationError`
  naming the offending field"; the choices-then-null ordering at `### null=True interaction`, and it
  matches `convert_scalar`'s own docstring step order; the map itself is the section's scalar table,
  now correct in all five places the block was wrong. The block's `SCALAR_MAP.get(type(field))`
  exact-type lookup is additionally *superseded* by the new prose #"the lookup walks
  `type(field).__mro__`", which is the shipped behaviour.
- **`convert_relation`** — cardinality survives in the table one paragraph above; the lazy-target
  rule in the restated pending-relation paragraph. The block named `registry.lazy_ref`, which does
  not exist.
- **`TypeRegistry`** — `register` / `get` / enum cache / `clear()` all restated in prose; the
  block's collision rule was retracted by D6, not relocated, and the retraction is recorded in the
  rationale.
- **`plan_relation` pseudocode** — the downgrade rule survives immediately above it, stated more
  precisely than the code was. (Two clauses it carried do **not** survive anywhere — Medium 2.)
- **test module** — the `registry.clear()` fixture and the live-tier placement survive as the two
  explicit placement rules; both are accurate (`tests/types/test_converters.py` carries the autouse
  `registry.clear()`, and the `get_queryset` downgrade is asserted in
  `examples/fakeshop/test_query/test_products_api.py` #"downgrades it to a").

### The 21-anchor constraint — re-run, not accepted

```
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-001-django_types-0_0_1.md
OK: 21 terms - all have glossary entries and at least one spec link.
exit=0

$ uv run python examples/fakeshop/manage.py import_spec_terms --check
OK: 49 done cards have glossary links.
exit=0

$ grep -o '\]\[glossary-[a-z0-9_-]*\]' docs/SPECS/spec-001-django_types-0_0_1.md | sort | uniq -c
      2 ][glossary-configurationerror]
      1 (x20, one per remaining anchor)
```

**21 distinct anchors, 22 body links, `configurationerror` the only anchor with two.** Exactly as
the artifact states, counted by occurrence rather than by matching line. Both raising sentences
(`Meta` validation in `## DjangoType`, registry collisions in `## Registry`) genuinely name it, so
the second link is contract prose and not an anchor rescue. The terms CSV is clean in `git status`,
so no anchor was saved by editing it. `49` is the concurrent session's `DONE-049-0.0.14` wrap, not
this cycle — attributed semantically below.

### Markdown link convention and `AGENTS.md` rule 27

Both files, mechanically:

- Exactly one `<!-- LINK DEFINITIONS -->` marker each; all 10 canonical group headers present in
  START.md's exact order (compared positionally against the literal list, not by membership).
- Defs alphabetical within every group in both files.
- Spec **22 defs / 22 used refs**, rationale **18 / 18**; 0 undefined, 0 orphaned in both.
- All **40** def targets `os.path.exists`-checked on the normalized join from each file's own
  directory (`../GLOSSARY.md` x21 + `appx/…-rationale.md` from `docs/SPECS/`;
  `../spec-001…`x16 + `../spec-002…` + `../../builder/BUILD.md` from `docs/SPECS/appx/`). All resolve.
- No inline `](path)` cross-file link in either body outside fences.
- All **15** in-page anchors the rationale cites resolve against surviving spec headings
  (`#prior-art`, `#proposed-public-surface`, `#djangotype`, `#scalar-field-conversion`,
  `#choice-field-enum-generation`, `#relation-field-conversion`, `#registry`, `#get_queryset`,
  `#n1-strategy`, `#type-naming`, `#testing-strategy`, `#files-to-add`, `#references`, `#goal`,
  `#suggested-implementation-slices`); unresolved set empty. See Low 5 on the method.
- **No inbound reference anywhere in the tree targets a removed spec-001 heading.**
  `grep -rn 'spec-001-django_types-0_0_1\.md#'` over `*.md` / `*.py` / `*.csv` / `*.html` returns
  only the rationale's own 15 defs; the `#current-state` hits elsewhere in `docs/SPECS/` are other
  specs' own in-page anchors.
- **Rule 27:** the spec is clean — zero `path:NN` refs, and the ten sibling specs it names
  (`spec-002`, `-008`, `-015`, `-018`, `-027`, `-028`, `-030`, `-031`, `-034`, `-037`) all exist on
  disk, as do all seven `graphene_django` / `strawberry_django` symbols the rewritten `## References`
  cites, checked in the two checkouts `AGENTS.md` names. The rationale carries one hit — Low 1.

### Byte and fence accounting

| Claim | Re-derived |
|---|---|
| spec 42,483 -> 43,651 (+1,168) | `wc -c` = **43,651**; R1's re-derived close was 42,483; delta +1,168 |
| rationale 24,011 -> 52,961 (+28,950) | `wc -c` = **52,961**; delta +28,950 |
| -8,690 / -16.6% against HEAD | `git show HEAD:<path>` piped to `wc -c` = **52,341**; 43,651 - 52,341 = -8,690 = -16.60% |
| 12 -> 7 python fences | `grep -c` both sides |
| 22/22 and 18/18 link defs, 40 paths | by script, above |
| 21 anchors / 22 links | by occurrence count, above |

Every one holds. Worth saying plainly: the count discipline R1 handed over **did** improve — the
six mechanical claims above are exact where R1 lost five in a row. The three that failed (Medium 4)
are all rhetorical rather than structural, which is a different and smaller failure than R1's.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is empty. `__all__` and the re-export list are
unchanged. Correct: the plan's build-wide context flags forbid any source change in this cycle.

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md` (`AGENTS.md` rule 21 and the plan's context
flags both close it).

### Documentation / release sanity

- Version strings in the reconciled prose are attributions to owning releases and each checks out:
  `filterset_class`/`orderset_class` at `0.0.8` (`spec-027` / `spec-028` are `0_0_8`),
  `apply_interfaces` "since `0.0.5`" (`spec-015` is `0_0_5`), `PositiveBigIntegerField` at `0.0.6`
  (corroborated by `docs/GLOSSARY.md` independently of the spec), `<TypeName>Connection` at `0.0.9`
  (`spec-030`, and `connection.py` #"Connection" builds exactly that name).
- No KANBAN movement, no archival, no release metadata touched. The spec was already archived; no
  move was performed or needed.
- No script-rendered doc regenerated by this pass, so the staging-docstring check does not apply.
- **`docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`, `examples/fakeshop/db.sqlite3` are dirty and it
  is not this cycle.** Attributed semantically rather than assumed: `git diff -- docs/GLOSSARY.md`
  is `+2` lines, both about a hard dependency's declared floor and the `Django>=5.2.16` /
  `strawberry-graphql>=0.316.0` audit rule — the `spec-049` dependency/CI-hardening surface, with no
  spec-001 term touched. `SECURITY.md`, `TODAY.md`, `uv.lock` and
  `docs/spec-049-dependency_ci_hardening-0_0_14.md` are the same card wrap. Recorded, not reverted,
  not edited (`AGENTS.md` rule 34).
- `uv run python scripts/check_trailing_commas.py --check <both files>` -> exit 0.
  `git diff --check -- docs/SPECS/spec-001-django_types-0_0_1.md` -> exit 0.

### `scripts/review_inspect.py`

**Skipped, deliberately.** `BUILD.md` `### When to run the helper during build` triggers on adding a
`.py` file, touching `optimizer/` or `types/`, or adding 30+ lines of logic. This pass writes no
`.py` file and modifies none — the diff is two Markdown files. The helper parses Python as text and
AST and has nothing to report on a Markdown reconciliation. Recorded per `worker-3.md`
`## Static helper use`.

### Failability proofs

**Empty re-run set, and it is legal here.** `BUILD.md` `### What needs a proof` scopes the obligation
to a new boundary, guard, gate, or rejection path a slice introduces. This pass introduces none — it
writes no executable code, so there is nothing whose removal a test could fail on. The build report's
`None; this pass introduced no new boundary` is correct, and the mandatory floor in `worker-3.md`
("re-run every boundary whose recorded count is 3 or fewer, and every security / data-isolation
boundary") is satisfied vacuously because the diff introduces no boundary that meets it. The
executable checks standing in for tests — both constraint commands, `check_trailing_commas --check`,
`git diff --check` — were all re-run independently above rather than accepted from the artifact.

### Hot-path budget

Not applicable; the plan declares `Hot-path declaration: none` and no residual item runs per request,
per resolver, per row, per connection, or per outbound message. Absence of a number is correct here,
not a finding.

### Floor verification

Not applicable; the plan declares `Floor-verification scope: none`. This pass touches no Django /
Strawberry / channels integration seam.

### What looks solid

- **D16, D17 and D18 are the pass's own additions and all three survive independent re-derivation.**
  D17 is the one that matters most to a consumer — the spec promised GraphQL mappings for two column
  types that in fact fail closed at schema build — and it is corroborated three ways: absence from
  the 26-entry `SCALAR_MAP`, the module docstring's own "Notably absent" paragraph naming the same
  `Base64` plug the spec now names, and two pinning tests. The pass found this by reading the map
  against the table row by row instead of working the drift list, which is the practice the plan's
  "R2 owns the full sweep" exists to produce.
- **The D5 symbol correction is right and was worth catching.** `install_is_type_of` is
  unconditional and has nothing to do with `Meta.interfaces`; `apply_interfaces` is the only
  `__bases__` injection and the only step gated on a non-empty tuple. A correction naming the wrong
  symbol would have read entirely plausible.
- **The disposition split (restate / point / delete) is applied consistently and is the right
  shape,** with one exception (Medium 3). Ten sibling specs are named at their correction sites, so
  a reader who arrives at a stale-looking sentence lands on the document that owns it.
- **The PR #583 carve-out decision is correct and correctly reasoned.** I read `spec-002` end to end
  to check the premise rather than accept it: its O6 entry states the rule without the reason, and
  its `## References` frames #572/#583 as the bundling argument. Keeping the sole statement of *why
  the downgrade exists* in spec-001, and recording the deletion alternative as rejected on write-set
  grounds, is the right call on both halves.
- **Anchor handling under the 21-anchor constraint.** Six anchors moved out of the highest-risk
  section and every destination is a sentence where the concept is normative. The
  `djangooptimizerextension` re-site is a genuine improvement: at HEAD that link hung off a sentence
  about *strawberry-graphql-django's* same-named class.
- **`## Current state` -> `## Prior art` is the right instinct.** A section named for the present is
  a promise no shipped spec can keep; retitling makes the obligation one it can meet, and both
  alternatives are recorded with why each lost.
- **Concurrent-session attribution is positive rather than inferred,** including reading
  `import_spec_terms`' `--check` branch to confirm it returns before the `transaction.atomic()`
  write block rather than inheriting R1's claim about it.

### Temp test verification

Three scratch scripts under `docs/builder/temp-tests/r2-spec001/` (gitignored):

- `links.py` — link-definition scaffold, group headers and order, alphabetical order within group,
  undefined / orphan refs, on-disk path existence, inline-link detection, raw `path:NN` sweep. It is
  what surfaced Low 1.
- `anchors.py` — every rationale in-page anchor against the spec's surviving headings, with
  reference-link markup stripped before `check_spec_glossary.py::github_anchor`. It is what surfaced
  Low 5.
- `overlap.py` — maximal-shared-shingle scan between spec and rationale (n=8), the measurement
  behind the DRY finding. Independently written for this pass; it reproduces R1's method rather than
  reusing R1's file (`r1-spec001/` was left untouched).

**Disposition:** none caught a behaviour bug, so none is promotable to a permanent test — there is
no `.py` surface here to pin. Kept as this pass's evidence. R1 already escalated `overlap.py` as a
`scripts/` helper candidate; `links.py` and `anchors.py` belong in the same proposal, since every
spec-plus-rationale pair from here on owes exactly these three checks and both found a real defect
on their first run.

### Notes for Worker 1 (spec reconciliation)

1. **`Escalated:` Medium 2 — the two optimizer rules `spec-002` does not state.** Resolution needs
   an edit to `docs/SPECS/spec-002-optimizer-0_0_2.md`, which is outside every writable list in this
   cycle, so it is escalated rather than held against R2. Resolution paths: **(a)** fold the two
   clauses into `spec-002`'s O5 and O6 entries during R3's Worker 1 pass, which is already opening
   that file for items 2 and 3 below — the cheapest option and the one that closes the obligation by
   content; **(b)** re-home the O6 every-branch visibility clause in spec-001's `## N+1 strategy`
   beside the PR #583 carve-out, on the same "sole statement of a visibility rule" reasoning, and
   leave the O5 reason to a later optimizer cycle; **(c)** record both as a deferral in
   `bld-001-final.md`'s `### Deferred work catalog` and carry them to whichever cycle next opens
   `spec-002`. Whichever is chosen, **item 3 of R2's own notes needs re-wording either way** — as
   written it asks only that the lift be *recorded*, and a pass that does literally that closes
   nothing.
2. **The two inherited `spec-002` obligations are confirmed open and were not acted on.**
   `git status` carries no `spec-002` entry, and both references still point into text that now
   lives only in the rationale: line 9's *"`spec-001…` predicted that the optimizer half of its
   scope would eventually warrant its own document"* (the cut-line prediction, moved by R1) and the
   `## References` bullet on the visibility-leak discussion *"that motivated bundling the optimizer
   with `spec-001…` originally"*. R1's Finding 4 hand-over stands unchanged, and R3 must assign both
   to its **Worker 1** pass because `spec-002` is a spec file. R2 created a third obligation on the
   same file; all three now converge on one pass, which is the right consolidation.
3. **The anchor constraint for R3 is 21 anchors / 22 body links**, `configurationerror` the only one
   with two, re-measured this pass. Unchanged from what R2 handed over.
4. **`import_spec_terms --check` reads `OK: 49 done cards`**, exit 0. Confirmed independently. The
   number is the concurrent session's, not this cycle's; exit 0 is the contract.
5. **A correctness observation about the package: none.** Every symbol, guard and rejection I read
   against the spec behaves as its own docstring and tests claim. I confirm R2's finding that the
   three defects were all in the spec. R2's documentation note stands and I second it: `DurationField`
   and `BinaryField` raise `ConfigurationError` on any model that declares one, and R3's durable-doc
   audit should check `README.md` and `TODAY.md` for a stale promise (`docs/GLOSSARY.md` and the
   converter docstring both state it correctly).
6. **Medium 1 and Medium 3 are both single-sentence fixes inside R2's own write set** and are why
   this is `revision-needed` rather than an accept-with-escalation: they are defects in the
   deliverable on the item's own declared axis, not in the artifact's prose. Medium 4 is three
   numbers in the rationale plus two in the artifact.

### Review outcome

`revision-needed`. Routes back to a **Worker 1** pass, not Worker 2 — the plan's Deviation 3 makes
Worker 1 the only role that may mutate the spec and the rationale, and every in-scope fix below
lands in one of those two files.

Four Mediums. Three are inside R2's write set and are cheap:

- **Medium 1** — delete the module-restructure chronology from `## Files to add`'s opener; the
  rationale already carries the fact.
- **Medium 3** — name `spec-029-consumer_dx_cleanup-0_0_9.md` on the `extensions=` sentence, so the
  one un-pointered restatement joins the other ten.
- **Medium 4** — re-measure or re-form the three counts (sanitization rules 4->7, "26-method"
  registry, "24-entry" scalar map), including the rationale's *"claims the spec no longer makes …
  that sanitization is four steps"* bullet, whose premise is three.

**Medium 2 is escalated, not held** — it needs `spec-002`, which no writable list in this cycle
contains, and R3's Worker 1 pass is already opening that file.

The five Lows are individually small and none blocks on its own; they are listed so the same pass
can sweep them while the files are open. The deliverable itself is sound: every corrected claim is
true at HEAD, the three self-found drift rows are the strongest work in the pass, the code-block
deletions are all safe, the PR #583 carve-out survives, and the anchor and link scaffolding is
exact.

---

## Reconciliation performed (Worker 1, pass 2, in place of the Worker 2 apply-changes pass)

Fresh Worker 1 spawn. I did not write the R2 reconciliation and carry none of its reasoning; the
artifact above is the contract, and Worker 3's `## Review (Worker 3)` is the work list. Deviation 3
routes a `revision-needed` on this item to Worker 1 rather than Worker 2, so this section stands in
for a Worker 2 apply-changes build report and keeps its subsection names. `ARTIFACT.md`
`## Re-pass sections` forbids editing a prior entry, so nothing above was rewritten; the one
exception is the `### Dispatched findings checklist`, whose boxes `BUILD.md` explicitly gives Worker
1 to re-audit, and the top-level `Status:` line.

### Spec status-line re-verification

Re-read `docs/SPECS/spec-001-django_types-0_0_1.md` lines 1-5 at pass start, for the fourth time in
this cycle. **Still no status/header block.** Line 1 is `# Spec: DjangoType Foundation`, line 2 is
blank, line 3 opens `## Problem statement`. Nothing to falsify; this pass deletes no predecessor doc
a header could point at.

### Disposition of the nine findings

| Finding | Disposition |
|---|---|
| **Medium 1** — `## Files to add` narrates the restructure chronology | **Fixed** in the spec; the translation aid re-homed in the rationale |
| **Medium 2** — two lifted rules `spec-002` does not state | **Fixed** — both restored to spec-001 as contract, re-derived against source first (see below for which of the two options was taken and why) |
| **Medium 3** — the `extensions=` sentence restates `spec-029` with no pointer | **Fixed** — `spec-029-consumer_dx_cleanup-0_0_9.md` named at the site |
| **Medium 4** — three asserted counts fail re-derivation | **Fixed** — all three re-measured and re-formed; the rationale's *claims the spec no longer makes* bullet corrected with them |
| **Low 1** — raw `path:NN` inside the rationale's own anti-`path:NN` entry | **Fixed** — paraphrased; both files now sweep clean |
| **Low 2** — D13 ticked with no diff | **Fixed** — un-ticked to `- [ ]`, the box's own sentence left as the deferral |
| **Low 3** — `0.316.0` deprecation over-attribution | **Fixed** — "as of `0.316.0`" |
| **Low 4** — the unpinned forward-reference contract sentence | **Fixed** — tightened to the mechanism that actually runs, symbol cited, the unpinned third spelling dropped |
| **Low 5** — the `github_anchor` method claim | **Accepted, recorded, and the method corrected here** — no file edit; the claim is in a prior artifact entry this pass may not rewrite |

Nothing was rejected. Every finding is either fixed in a writable file or, for Low 5, a claim about a
prior pass's method that this pass restates correctly rather than edits.

### Medium 2 — which resolution, and why

The choice the review poses is: restore the two rules to spec-001 as contract on the PR #583
precedent, or hand them to item R3's Worker 1 pass, which may edit `spec-002`.

**Taken: restore both to spec-001.** The reasoning is the carve-out's own, applied consistently
rather than re-derived. R2 kept the PR #583 derivation in spec-001 for one reason — `spec-002` states
the O6 rule without its reason, and `spec-002` is outside this cycle's write set — and recorded
deleting it as the rejected alternative so a cycle whose scope includes `spec-002` can re-open it
deliberately. These two rules are the same shape: `spec-002`'s O5 entry states the mechanism without
the reason, its O6 entry covers only the downgrade branch, and `spec-002` is outside this pass's
writable list exactly as it was outside R2's. Handing them on makes the discharge a **promise**
rather than a fact, and this cycle has already watched one hand-over fail that way — R2's own item 3
asks that the lift be *recorded* and closes neither rule, which is Worker 3's point. Until a later
pass performs it, a data-isolation rule and a fail-open-shaped projection rule are stated in no
document at all. A rule stated in the wrong spec is a smaller defect than a rule stated nowhere.

Two consequences, both recorded rather than left implicit:

- The rejected alternative is written into the rationale beside the PR #583 one, with the condition
  that would re-open it: **a later cycle that re-homes these two rules to `spec-002` must re-home the
  PR #583 carve-out with them and delete all three from spec-001 in the same change.** Splitting them
  is how the duplication this item exists to remove gets recreated.
- R2's hand-over item 3 is re-worded below (`### Notes for Worker 1`) so R3 inherits the closed
  obligation, not the open one.

**Both rules were re-derived against source before being written, not restored from the deleted
paragraphs** — and that mattered on one of them.

- **The projection rule holds and its reason holds.** `optimizer/plans.py` #"including the FK columns
  required to materialize" records `only_fields` as carrying "the FK columns required to materialize
  `select_related` joins so Django doesn't mark them as deferred and re-query", and
  `optimizer/walker.py::_record_relation_access` states the consequence of dropping the column
  ("reintroduce the N+1") as the reason its call must precede the FK-elision check. Written into
  `## N+1 strategy` immediately after the cardinality list, where `selected scalar columns -> only()`
  already sits.
- **The visibility rule holds; the deleted paragraph's wording for it does not, and was not
  restored.** *"Every `plan_relation` call also runs `target_type.get_queryset(target_qs, info)`"* is
  false at HEAD: `optimizer/walker.py::plan_relation` returns a `(kind, reason)` pair of strings and
  touches no queryset — which is precisely what R2 recorded when it deleted the paragraph as one of
  the three that were "also wrong". The rule underneath it is true:
  `optimizer/walker.py::_build_child_queryset` applies the target type's `get_queryset` (through
  `utils/querysets.py::apply_type_visibility_sync`) to the child queryset of every generated
  `Prefetch`, and `::_plan_prefetch_relation` computes `has_custom_get_queryset` independently of
  *why* the prefetch branch fired, so the ordinary many-side prefetch is filtered on the same footing
  as the downgraded FK. The spec now states that, plus the reason the downgrade exists at all: a
  collapsed FK join is the one branch with no child queryset to apply the hook to. Restoring the
  paragraph verbatim would have re-entered a falsehood R2 correctly removed.

### Files touched

- `docs/SPECS/spec-001-django_types-0_0_1.md` — **five** numbered changes: M1's opener, M2's two new
  `## N+1 strategy` paragraphs, M3+L3 in one sentence, L4's forward-reference sentence.
- `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md` — **eight** numbered changes: M4's
  three counts across three of them, L1's paraphrase, and four entries extended to record M1, M2,
  M3, L3 and L4. Enumerated in `### Spec changes made (Worker 1 only)`; counted off that list
  rather than asserted here.
- `docs/builder/bld-001-r2-spec_reconciliation.md` — this section, the D13 un-tick, and the
  `Status:` line.
- `docs/builder/worker-memory/worker-1.md` — one appended entry (gitignored; not part of the diff).

**No other file was written.** `spec-002-optimizer-0_0_2.md` is clean in `git status` and was read
only.

### Byte counts

| File | R2 pass 1 close | This pass | Delta |
|---|---|---|---|
| `docs/SPECS/spec-001-django_types-0_0_1.md` | 43,651 | **44,502** | **+851** |
| `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md` | 52,961 | 59,706 | +6,745 |

Against HEAD (`52,341`, `git show HEAD:… | wc -c`) the spec is **-7,839 (-14.98%)** across R1 and R2
combined, up from `-8,690` because this pass restores two rules and adds one owning-spec pointer.
Both prior numbers are re-derived, not carried: `wc -c` on the working tree, `git show HEAD:… | wc -c`
for the baseline.

### The three counts, re-measured

Each measured at the moment of writing, by counting occurrences of the shortest distinctive token,
never matching lines.

| Asserted | Re-derived this pass | How |
|---|---|---|
| "seven sanitization rules, not four" / rationale *"was four steps and is now seven"* | **no unit yields 4 -> 7.** HEAD's spec step 4 enumerates **three** operations (`str()` coercion, non-identifier rewrite, leading-digit `MEMBER_`); the corrected spec text enumerates **five** clauses; `types/converters.py::_sanitize_member_name`'s docstring numbers **four** rules, folding the `str()` coercion into rule 1 | `git show HEAD:<spec> > <scratch outside repo>`, read step 4; read the docstring |
| "a 26-method registry" / *"the real class carries twenty-six methods"* | **27** `FunctionDef`s on `registry.py::TypeRegistry`; 26 only if `__init__` is silently excluded | `ast` walk, names listed |
| "a 24-entry scalar map" | **26** in `types/converters.py::SCALAR_MAP`; **23** in the deleted illustrative block. Neither is 24 | `ast` `len(node.value.keys)` = 26; the HEAD block's `models.…:` lines enumerated = 23 |

Worker 3's re-derivations are confirmed exactly on all three. **The fix is re-forming, not
re-numbering** — a count in a standing doc rots the same way whatever its value, and all three sat in
argumentative positions where the number carried no weight:

- The sanitization entry now names the rules on both sides: the spec's rule "stopped at the
  leading-digit `MEMBER_` prefix", HEAD "adds two further rewrites after those". The
  *claims the spec no longer makes* bullet, whose premise was three and not four, now reads *"that
  sanitization ends at the leading-digit `MEMBER_` prefix"*.
- "an illustrative literal of a 26-method registry or a 24-entry scalar map" -> "an illustrative
  literal of every method on `registry.py::TypeRegistry`, or of every entry in
  `types/converters.py::SCALAR_MAP`". The argument is that a literal is a second copy; the size was
  never the point.
- "the real class carries twenty-six methods" -> the deleted block's seven method names listed
  verbatim, followed by the surfaces it omits (the pending-relation trio, the definition store, the
  finalization latch, the class-to-model reverse lookup, the multi-type / primary accessors). A
  reader can re-derive that against `registry.py` without a number to distrust. **I wrote "six-method
  body" first and caught it on the recount before it left the file** — the block's methods are
  `__init__`, `register`, `get`, `lazy_ref`, `register_enum`, `get_enum`, `clear`, which is seven.

### Low 5 — the anchor method, corrected rather than repeated

Worker 3's finding is right and I reproduced it. `scripts/check_spec_glossary.py::github_anchor` fed
the raw heading `## [Scalar field conversion][glossary-scalar-field-conversion]` returns
`scalar-field-conversionglossary-scalar-field-conversion`, because it strips `[` and `]` as
non-word characters instead of rendering the reference link — so `#scalar-field-conversion` reads as
unresolved on the one heading in this spec that is itself a link.

The corrected method, used by this pass and stated here so the next pass copies the working version:
**strip reference-link and inline-link markup from the heading text first, then slug both the
rendered label and the raw heading and accept either.** `docs/builder/temp-tests/r2b-spec001/verify.py`
implements it in six lines. Result: **15 of 15** in-page anchors the rationale cites resolve,
unresolved set empty. No file edit — the claim lives in a prior artifact entry `ARTIFACT.md` forbids
rewriting, so the correction is this restatement.

### Validation run

Both constraint commands re-run after **every** edit group — a pre-pass baseline plus five post-edit
runs across the thirteen numbered changes, never batched to the end. Saying "after every edit" would
over-claim: the two `## N+1 strategy` insertions and the `extensions=` sentence went in as one group
before the pair ran, and the eight rationale changes went in as one group. The property that matters held at
every checkpoint: **no anchor was ever below one link**, and this pass removed no anchor's link site
at all — its five spec edits add prose or rewrite sentences that carry no glossary link. Final
state:

```
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-001-django_types-0_0_1.md
OK: 21 terms - all have glossary entries and at least one spec link.
exit=0

$ uv run python examples/fakeshop/manage.py import_spec_terms --check
OK: 49 done cards have glossary links.
exit=0

$ uv run python scripts/check_trailing_commas.py --check \
    docs/SPECS/spec-001-django_types-0_0_1.md \
    docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md
exit=0

$ git diff --check -- docs/SPECS/spec-001-django_types-0_0_1.md
exit=0
```

`OK: 49 done cards` is unchanged from what R2 handed over, and the count is not the gate — exit 0 is.
The terms CSV was not touched and no anchor was rescued by re-adding narration.

No `ruff`: no `.py` file was written (the one `.py` this pass created is a gitignored temp-test
script under `docs/builder/temp-tests/`). No `pytest`: no test exists for a Markdown reconciliation
and the plan calls for none.

### Anchor budget after this pass

```
$ grep -o '\]\[glossary-[a-z0-9_-]*\]' docs/SPECS/spec-001-django_types-0_0_1.md \
    | sort | uniq -c | awk '{print $1}' | sort | uniq -c
  20 1
   1 2
```

**Unchanged: 21 distinct anchors, 22 body links, `configurationerror` the only anchor with two.**
Every other glossary-linked sentence remains its anchor's sole link. Carry that to R3 unchanged.

### Link and anchor resolution

Mechanically re-derived over both files after the last edit
(`docs/builder/temp-tests/r2b-spec001/verify.py`):

- Reference-style throughout; zero inline `](path)` cross-file links in either body outside fences.
- One `<!-- LINK DEFINITIONS -->` marker each; all 10 canonical group headers present in START.md's
  exact order, compared positionally against the literal list; empty groups retained.
- Spec **22 defs / 22 used refs**, rationale **18 / 18**; 0 undefined, 0 orphaned in both. This pass
  added no link and needed none — every file it names (`spec-029-consumer_dx_cleanup-0_0_9.md`, the
  optimizer and types modules) is named in an inline code span, which the convention leaves inline.
- All **40** def targets `os.path.exists`-checked on the normalized join from each file's own
  directory. All resolve.
- Defs alphabetical within every group in both files.
- All **15** in-page anchors the rationale cites resolve against surviving spec headings, by the
  corrected method above.
- **Rule 27: both files are now clean.** `path:NN` sweep over spec and rationale returns zero hits;
  L1's survivor was the last one. Every symbol path this pass added was verified to resolve:
  `types/base.py::_build_annotations`, `optimizer/walker.py::plan_relation`,
  `::_build_child_queryset`, `::_plan_prefetch_relation`, `::_record_relation_access`,
  `optimizer/plans.py`, `utils/querysets.py::apply_type_visibility_sync`,
  `registry.py::TypeRegistry`, `types/converters.py::SCALAR_MAP`,
  `tests/types/test_definition_order.py::test_annotation_only_relation_override_keeps_generated_resolver`.
  Both `#"…"` substring refs match exactly once in their file (`grep -c` = 1).

### Spec-versus-rationale overlap, re-measured

`docs/builder/temp-tests/r2b-spec001/overlap.py`, maximal shared shingles at n=8, fences and the
link-definition block stripped: **20 runs / 251 overlapping words against a 5,518-word spec body
(4.5%)**. That is this pass's own scanner, independently written, so the numbers are **not**
differenceable against Worker 3's 22 runs / 259 words — a different implementation counts a different
population. What is comparable is the classification: three runs are new and all three are inside the
rationale's *Restored* entry quoting the spec rule it explains (19w projection rule, 8w child-queryset
clause, 8w downgrade clause), which is quotation-with-attribution, the shape the mechanism intends.
Worker 3's four pure-restatement runs are untouched by this pass and stand as recorded.

### Concurrent-session churn observed (not this pass's, not reverted)

`git status --short` at this pass's start, re-measured rather than inherited from R2's list — and it
had moved again:

```
 M KANBAN.html          M KANBAN.md            M SECURITY.md      M TODAY.md
 M docs/GLOSSARY.md     M uv.lock              M examples/fakeshop/db.sqlite3
 M docs/spec-049-dependency_ci_hardening-0_0_14.md
```

The two `-terms.csv` files and `docs/SPECS/spec-048-…md` that R2 recorded as dirty are **clean
again**; `docs/GLOSSARY.md`, `SECURITY.md`, `TODAY.md` and `uv.lock` are dirty where R2's own list
did not carry all of them. HEAD is unmoved at `fdfb711f`, so this is uncommitted concurrent work on
the spec-049 surface, mid-flight. None of it is in this pass's writable list; recorded, not reverted,
not edited (`AGENTS.md` rule 34). The only DB-touching command this pass ran is
`import_spec_terms --check`, whose `--check` branch returns before the writing transaction.

**The lesson R2 recorded holds and is now twice-confirmed: a concurrency snapshot in an artifact is a
snapshot.** R3 must re-measure at its own start; neither "assume clean" nor "assume dirty" nor
"assume R2's list" survives.

### Failability proofs

None; this pass introduced no new boundary, guard, gate, or rejection path. It writes no executable
code.

### Hot-path budget

Not applicable; plan declares no hot path (`build-001-django_types-0_0_1.md` preamble: *"Hot-path
declaration: none"*).

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- **The spec grows again, and that is the shape of Medium 2's resolution.** `+851` bytes: two
  restored rules, one owning-spec pointer, one tightened contract sentence, one shortened opener.
  The rationale takes `+6,745` because every one of those carries its reasoning and its rejected
  alternative there. The ratio is the mechanism working — the spec's number is what every future
  spawn pays.
- **A restored rule is a HEAD claim, so it was re-derived at the restoration.** This is R2's own
  D18 lesson turned on itself: R2 found a factual error inside a sentence R1 had just *promoted*
  from narration into contract. A rule being lifted back out of a deleted paragraph is the same
  event, and it caught the same class of error — the O6 paragraph's operative sentence is false at
  HEAD, so the rule was rewritten against `walker.py` rather than restored.
- **The un-tick of D13 loosens nothing.** `BUILD.md` `### Dispatched findings checklist` reserves
  `- [x]` for a box whose fix landed in the diff, and D13's did not — it landed in R1 and the box's
  own sentence says so. `- [ ]` plus that sentence is the faithful shape, and the deferral reason is
  recorded under `### Spec changes made (Worker 1 only)` below, which is what `BUILD.md` asks for a
  box left open.
- **Low 4 dropped a spelling rather than pinning it.** The obvious alternative was to keep the
  cross-module `strawberry.lazy` spelling and cite a pin. There is none under `tests/types/` for a
  consumer override of a `DjangoType` relation — `strawberry.lazy` is pinned heavily, but in the
  filter / order / form input factories, which is a different mechanism and a different spec. A
  contract sentence with no pin is a claim; dropping it is honest where citing an unrelated pin
  would not be.
- **Every count in this section was measured at the moment of writing**, per the practice failure
  this cycle has now recorded seven times: byte counts by `wc -c` and `git show HEAD:… | wc -c`;
  21/22 anchors by `uniq -c` on occurrences; 27 registry methods and 26 `SCALAR_MAP` entries by
  `ast`; 23 block entries by enumeration; 40 link paths by `os.path.exists`; 15 in-page anchors and
  22/22 + 18/18 defs by script; 20 runs / 251 words by shingle scan. One count was wrong on its
  first writing and corrected before it left the file — see the registry row above.

### Notes for Worker 3

- **The one High-shaped question left is whether the two restored rules are TRUE**, not whether they
  belong. Both were re-derived against source and neither was restored verbatim; the O6 one was
  deliberately rewritten because the deleted paragraph's own sentence is false at HEAD. Re-derive
  both against `optimizer/walker.py` and `optimizer/plans.py` rather than against the spec, and
  treat a mismatch as a High — a false rule newly *added* to a spec is worse than the gap it closes.
- **Check that Medium 2's resolution did not create a duplication.** `spec-002` is clean in
  `git status` and must stay so: if either rule now reads in both specs, the restoration was done
  wrong.
- **Re-run both constraint commands yourself.** This pass moved no anchor's link site, so the
  expected result is *unchanged* from what you measured — 21 anchors, 22 links,
  `configurationerror` the only one with two. A change is a finding.
- **Low 5's method fix is in `docs/builder/temp-tests/r2b-spec001/verify.py`.** If you re-check the
  in-page anchors, use it or reproduce it; feeding a raw reference-link heading to `github_anchor`
  gives a false negative on `#scalar-field-conversion`, as it did to Worker 3.
- The diff to read is `git diff -- docs/SPECS/spec-001-django_types-0_0_1.md` (which contains R1's
  and R2 pass 1's changes too) plus the untracked rationale. Do not `git stash`, `git checkout` or
  `git restore` anything — the tree carries a concurrent session's uncommitted spec-049 work.

### Notes for Worker 1 (spec reconciliation)

Carried into R3 and the final gate. Items 1-3 are the `spec-002` obligations, **all three confirmed
still recorded and still open at this pass's close**, with item 3 re-worded as Worker 3 required.

1. **`spec-002:9` and `spec-002:80` are open and untouched.** Re-read both this pass and both still
   point into text that lives only in spec-001's rationale: line 9's *"predicted that the optimizer
   half of its scope would eventually warrant its own document"* (the cut-line prediction, moved by
   R1) and the `## References` bullet on *"the visibility-leak / `Prefetch` downgrade discussion that
   motivated bundling the optimizer with `spec-001-django_types-0_0_1.md` originally"*. `git status`
   carries no `spec-002` entry. R1's Finding 4 hand-over stands unchanged; R3 must assign the edit to
   its **Worker 1** pass, because `spec-002` is a spec file. Minimum discharge is a pointer naming
   `appx/spec-001-django_types-0_0_1-rationale.md`, not new narration.
2. **The prose lift is still worth recording in `spec-002`.** R2's third obligation. The natural
   site is `## Coordination with `spec-001-django_types-0_0_1.md`` (spec-002's own heading, backticks
   included — R2's note named it without them). This is a *recording*, and on its own it closes no
   rule; see item 3 for what changed.
3. **Re-worded, replacing R2's item 3 as Worker 3's Medium 2 required.** R2's item 3 asked only that
   the lift be recorded, and Worker 3's finding is that a pass doing literally that leaves two rules
   stated nowhere. **That is no longer true: both rules are now contract in spec-001's
   `## N+1 strategy`**, re-derived against source (`optimizer/plans.py` for the projection rule,
   `optimizer/walker.py::_build_child_queryset` / `::_plan_prefetch_relation` for the every-branch
   visibility rule). So R3's `spec-002` pass inherits a **closed** obligation, not an open one, and
   its only remaining duty on this axis is item 2's recording. If that pass decides to re-home the
   two rules into `spec-002`'s O5 and O6 entries anyway, it **must re-home the PR #583 carve-out with
   them and delete all three from spec-001 in the same change** — those three are one decision, and
   splitting them recreates the duplication this item exists to remove. The rejected alternative and
   this condition are on record in the rationale's `## N+1 strategy` entry.
4. **A correctness observation about the package: none.** Every symbol, guard, and branch this pass
   read — `plan_relation`, `_build_child_queryset`, `_plan_prefetch_relation`,
   `_record_relation_access`, `_build_annotations`, `_sanitize_member_name`, `TypeRegistry`,
   `SCALAR_MAP` — behaves as its own docstring and tests claim. The only thing worth a maintainer's
   eye remains R2's **documentation** note, and I second it a second time: `DurationField` and
   `BinaryField` raise `ConfigurationError` on any model that declares one; `docs/GLOSSARY.md` and
   the converter docstring say so, `README.md` and `TODAY.md` have not been checked. R3's
   durable-doc audit should include them.
5. **The anchor constraint for R3 is unchanged: 21 anchors / 22 body links**, `configurationerror`
   the only one with two, re-measured at this pass's close.
6. **`import_spec_terms --check` reads `OK: 49 done cards`**, exit 0, unchanged. The number is not
   the contract; exit 0 is.
7. **Re-measure `git status` at R3's start.** It has now moved three times in this cycle and moved
   again during this pass (see `### Concurrent-session churn observed`), while HEAD stayed at
   `fdfb711f`. Attribute every generated-doc diff before treating it as spec-001 drift.
8. **`docs/builder/temp-tests/r2b-spec001/` carries this pass's two scripts** (`verify.py`,
   `overlap.py`), gitignored. `verify.py` is the corrected anchor method from Low 5 and folds R1's
   and R2's link audits into one file; together with `overlap.py` it is the third data point for the
   standing suggestion that these checks become a `scripts/` helper, since every spec-plus-rationale
   pair from here on owes exactly them.

### Spec changes made (Worker 1 only)

**Five** numbered changes to `docs/SPECS/spec-001-django_types-0_0_1.md` and **eight** to
`docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md`. Counted off the numbered list below after
writing it, not asserted beside it — the first draft of this sentence said four and seven.

**`docs/SPECS/spec-001-django_types-0_0_1.md`**

1. `## Files to add`, the section opener — the *"were single modules when the first slices landed and
   became packages under the later restructure"* clause and the "where each module lives today" hedge
   both removed; the opener now states the current layout flat. Reason: Worker 3 Medium 1 —
   `BUILD.md` `## Spec rationale extraction` forbids a spec chronology outright, and this was the
   last one in the document.
2. `## N+1 strategy`, after the cardinality list — one new paragraph stating that a projection over a
   joined relation must carry the source row's local FK column alongside the joined columns, with the
   deferred-attribute re-query as the reason. Reason: Worker 3 Medium 2, the O5 half. Re-derived
   against `optimizer/plans.py` and `optimizer/walker.py::_record_relation_access`.
3. `## N+1 strategy`, after the downgrade rule — one new paragraph stating that visibility filtering
   is not confined to the downgraded branch: the target type's `get_queryset` reaches the child
   queryset of every generated `Prefetch`, and the downgrade closes the one branch (a collapsed FK
   join) that has no child queryset. Reason: Worker 3 Medium 2, the O6 half. Rewritten against
   `optimizer/walker.py::_build_child_queryset` / `::_plan_prefetch_relation` rather than restored,
   because the deleted paragraph's own sentence is false at HEAD. The same change carries the
   section lead's coherence repair — *"the one rule that had to be settled in the foundation"* ->
   *"the rules"*, since changes 2 and 3 make it three — which is why the spec's delta reads `+851`
   and not the `+854` measured before that clause was re-read.
4. `## N+1 strategy`, the `extensions=` sentence — *"the bare-instance form Strawberry deprecated in
   `0.316.0`"* -> *"the bare-instance form, which Strawberry warns on as of `0.316.0`"*, plus a
   closing clause naming `spec-029-consumer_dx_cleanup-0_0_9.md` as the contract's owner. Reason:
   Worker 3 Medium 3 and Low 3, one sentence, two defects.
5. `## Relation field conversion` — *"Consumer-written forward references are honoured on the same
   footing"* and its three spellings replaced by the mechanism that runs
   (`types/base.py::_build_annotations` skips relation deferral for a consumer-authored name, leaving
   Strawberry to resolve the annotation), with the unpinned cross-module `strawberry.lazy` spelling
   dropped. Reason: Worker 3 Low 4.

**`docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md`** (Worker 1's file; these record this
pass's own spec edits and correct this pass's own prose, never moved spec text)

6. `### `## Files to add`` — the module-map paragraph no longer claims the spec carries the
   translation aid, and a new paragraph carries it here with the commits that make it true. Reason:
   edit 1's explanation must land somewhere, and the rationale is where a chronology is legal.
7. `### `## Relation field conversion`` — new paragraph recording edit 5, why "same footing" was the
   wrong footing, and why the third spelling was dropped rather than pinned.
8. `### `## N+1 strategy`` — new *Restored* entry recording edits 2 and 3, each with the source it
   was re-derived against and the note that the O6 paragraph's original wording was not restored;
   plus the *Alternative rejected — hand both rules to a later pass that may write `spec-002`* entry
   with the re-home-all-three-or-none condition.
9. `### `## N+1 strategy`` — new paragraph recording edit 4's two halves; the pre-existing
   *Corrected — the opt-in example* paragraph's "deprecated at `0.316.0`" softened to "warns on at
   the declared floor `0.316.0`" in the same pass so the file does not contradict itself.
10. `### `## Choice field enum generation`` — *"was four steps and is now seven"* replaced by the
    rules named on both sides, and the *claims the spec no longer makes* bullet's *"that sanitization
    is four steps"* replaced by *"that sanitization ends at the leading-digit `MEMBER_` prefix"*.
    Reason: Worker 3 Medium 4; the old premise was three, not four.
11. `### The two judgement calls the whole pass rests on` — *"a 26-method registry or a 24-entry
    scalar map"* re-formed to name the symbols instead of counting them. Reason: Worker 3 Medium 4.
12. `### `## Registry`` — *"the real class carries twenty-six methods"* replaced by the deleted
    block's seven method names and the surfaces it omits. Reason: Worker 3 Medium 4.
13. `### `## References`` — the raw `graphene_django/types.py:132-258` paraphrased. Reason: Worker 3
    Low 1; `AGENTS.md` rule 27 permits the form only in `docs/builder/bld-*.md`, and a repo-wide
    sweep lands on a quotation as readily as on a live ref.

**Checklist box left open, with its deferral reason** (`BUILD.md` `### Dispatched findings
checklist`): **D13** is now `- [ ]`. Its contract was discharged by R1's rationale move, not by R2's
diff, and the box's own sentence has always said so. No work is deferred — the row is closed, by a
prior pass, and the box records that rather than claiming this cycle's diff did it.

---

## Review (Worker 3, pass 2)

Fresh spawn; I did not write pass 1's review and carry none of its reasoning. Every count, every
"HEAD says X" claim, and every closed finding below was re-derived from the working tree and from
package source — `BUILD.md` `## Claims are proven mechanically, never accepted on prose`. Nothing is
read out of the artifact, including pass 1's own findings, which I re-verified as closed rather than
accepting the disposition table.

**What was re-derived, and how.** Byte counts by `wc -c` and `git show HEAD:<path> | wc -c` into a
scratch path outside the repo (no `stash` / `checkout` / `restore`). Anchor budget by counting
`][glossary-<id>]` **occurrences**. The three re-measured counts by `ast` walk and by enumerating the
HEAD block. Link scaffold, group headers, alphabetical order, undefined / orphan refs, on-disk path
existence and all fifteen in-page anchors by `docs/builder/temp-tests/r2b2-spec001/links2.py` — an
**independently written** slugger that never calls `check_spec_glossary.py::github_anchor`, so it is
not the corrected method under test but a second opinion on it. The two restored optimizer rules by
reading `optimizer/walker.py`, `optimizer/plans.py`, `optimizer/hints.py` and `types/resolvers.py`,
plus a two-row executable proof (`docs/builder/temp-tests/r2b2-spec001/test_hint_visibility.py`).
Both constraint commands re-run in full.

**The nine dispatched findings are all genuinely closed.** M1 (the chronology and the "lives today"
hedge are both gone from `## Files to add`'s opener), M2 (below), M3 (`spec-029-consumer_dx_cleanup-0_0_9.md`
named at the site), M4 (all three re-formed; my re-derivations agree exactly — 27 `FunctionDef`s on
`registry.py::TypeRegistry`, 26 `SCALAR_MAP` entries against 23 in the HEAD block, and no unit that
yields 4 -> 7 sanitization rules: HEAD's step 4 enumerates three operations, the corrected spec five
clauses, `types/converters.py::_sanitize_member_name`'s docstring four), L1 (`path:NN` sweep over
both files returns zero), L2 (D13 is `- [ ]` with its deferral reason recorded under
`### Spec changes made (Worker 1 only)`, which is what `BUILD.md` asks for an open box), L3
(*"warns on as of `0.316.0`"*), L4 (the sentence now names `types/base.py::_build_annotations` and
the unpinned third spelling is gone; the mechanism claim checks out — `#"if name in
consumer_authored_fields"` short-circuits relation deferral), L5 (my independent slugger resolves
**15 of 15** with the unresolved set empty, so the corrected method's conclusion holds under a second
implementation).

**The seven method names in the re-formed Registry entry are exact.** The HEAD block's body is
`__init__`, `register`, `get`, `lazy_ref`, `register_enum`, `get_enum`, `clear` — seven, verbatim,
in that order.

### High:

None.

**The pass's own High-shaped question resolves in its favour, on both halves.** The deleted
paragraph's operative sentence — *"every `plan_relation` call also runs
`target_type.get_queryset(target_qs, info)`"* — **is false at HEAD**:
`optimizer/walker.py::plan_relation` returns a `tuple[str, str]` of `(kind, reason)`, never touches a
queryset, and its only queryset-adjacent call is `::_target_has_custom_get_queryset`. Restoring it
verbatim would have re-entered a falsehood. And the rule the pass wrote instead **is true**:
`::_build_child_queryset` runs `utils/querysets.py::apply_type_visibility_sync` on the child queryset,
`::_plan_prefetch_relation` computes `has_custom_get_queryset` from the target type alone with no
reference to which dispatch produced the prefetch, and both the ordinary many-side walk
(`::_walk_selections` -> `::_dispatch_single_relation`) and the nested-connection planner
(`nested_planner.py` #"build_child_queryset(") reach the same builder. The `select_related` arm is
genuinely unreachable for a custom-`get_queryset` target: `::plan_relation` returns `"prefetch"` for
it, the `force_select` hint passes `prefer_prefetch=_target_has_custom_get_queryset(target_type)`, and
the FK-id elision is guarded by `not _target_has_custom_get_queryset(target_type)`. The O5 half holds
too — `optimizer/plans.py` #"including the FK columns required to materialize" states the rule and
`::_record_relation_access` #"reintroduce the N+1" states the reason, in the spec's own words.

**No duplication was created in `spec-002`.** It is clean in `git status`, and neither restored rule
reads in both specs: `spec-002`'s O5 is the mechanism sentence and its O6 is the downgrade branch,
which is exactly the gap the restoration fills.

### Medium:

#### 1. The restored visibility paragraph's consequence clause is a universal that HEAD falsifies

`docs/SPECS/spec-001-django_types-0_0_1.md` #"so no plan branch can return rows"

The new paragraph reads: *"The target type's `get_queryset` is applied to the child queryset of every
generated `Prefetch`, the ordinary many-side prefetch included, **so no plan branch can return rows
the target type would have filtered out**."*

The first clause is true and is the rule Medium 2 asked for. The clause after it is not. One planner
branch emits a `Prefetch` whose child queryset never meets `apply_type_visibility_sync`:
`optimizer/walker.py::_apply_hint` #"if hint.prefetch_obj is not None:" rebases the consumer's own
`Prefetch` through `::_prefetch_hint_for_path` and appends it, then returns `True` — so
`::plan_relation`, the downgrade, and `::_build_child_queryset` are all skipped. `optimizer/plans.py`
applies no visibility of its own, and the read side does not compensate:
`types/resolvers.py::_make_relation_resolver` #"prefetched.get(accessor_name)" returns Django's
materialised rows straight out of `_prefetched_objects_cache`.

**The answer that must be refused, not a spelling of the input:** a plan whose `prefetch_related`
carries a child queryset for a relation whose target type declares a custom `get_queryset`, where
that queryset's SQL has no predicate from the hook. Proven, two rows, in
`docs/builder/temp-tests/r2b2-spec001/test_hint_visibility.py`:

```
test_hinted_prefetch_skips_target_visibility          PASSED
  lookup: items
  SQL:    SELECT "products_item"... FROM "products_item"      <- no WHERE at all
test_generated_prefetch_child_does_apply_target_visibility PASSED   <- positive control, WHERE present
```

`Meta.optimizer_hints` is a `DjangoType.Meta` key, i.e. the consumer surface family this spec defines,
and spec-001 names no hint anywhere, so a reader has no cue that the universal is bounded. The
behaviour itself is **intentional** (`::_apply_hint` #"Consumer-supplied Prefetch objects commonly
close over" treats the consumer's queryset as authoritative and marks the plan uncacheable for it), so
this is a defect in the deliverable, not in the package — which is why it is a finding here and not a
package-correctness note.

Not High: the rule the finding restored is correct and the paragraph's operative sentence holds; what
fails is one trailing generalisation. But it is a data-isolation claim newly *added* to a standing
contract, which is the shape the pass's own `### Notes for Worker 3` asked me to test hardest.

**Recommended change.** Bound the clause to what the planner itself plans — e.g. *"…the ordinary
many-side prefetch included, so no relation the planner plans for itself can return rows the target
type would have filtered out"* — or drop the clause and let "every generated `Prefetch`" carry the
sentence. Naming the hint exception is optional (a later spec owns that surface); asserting nothing
about it is sufficient.

### Low:

1. **"four of the five were deleted" does not survive re-derivation.**
   `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md` #"and four of the five were deleted"
   The paragraph asserts *"The spec carried five `# illustrative shape` blocks"* and that four were
   deleted, the fifth being the `Meta`-key consumer examples. Re-derived: `grep -c '^```python'` is
   **12** at HEAD and **7** now, and each HEAD fence located by line gives **five** deletions
   (`convert_scalar`+`SCALAR_MAP`, `convert_relation`, `TypeRegistry`, the `plan_relation`
   pseudocode, the test module) with the `Meta`-key examples being **three** further blocks, all
   kept. This artifact's own `### The five illustrative code blocks` table uses that same population.
   No contract turns on it, and it may be a vocabulary conflation rather than a miscount — but it is
   a number in a standing doc that a reader's own re-derivation contradicts, one paragraph after the
   pass re-formed two other counts out of the same sentence. **Recommended change:** state the
   disposition without a count ("every illustrative block that duplicated a module was deleted; the
   `Meta`-key consumer examples were kept and corrected").

2. **The version-tense hedge Medium 1 removed survives one section earlier.**
   `docs/SPECS/spec-001-django_types-0_0_1.md` #"the converter layer now at" reads *"the converter
   layer **now at** `types/converters.py`"*. Medium 1's second half was that *"name where each module
   lives today"* is a version-tense hedge on top of the chronology; `now at` is the same word doing
   the same work, and the rationale's `### `## Proposed public surface`` entry already carries the
   fact that the module moved. Delete the word: *"the converter layer at `types/converters.py`"*.

### DRY findings

- **Spec-versus-rationale overlap: 20 runs / 251 overlapping words against a 5,517-word spec body
  (4.5%).** Re-measured with the pass's own `r2b-spec001/overlap.py` (n=8, fences and link-def blocks
  stripped) so the number is comparable to what it reported, and it reproduces exactly. The dangerous
  direction — contract leaving the spec — is clean. The three runs new since pass 1 are all inside
  the rationale's *Restored* entry quoting the spec rule it explains (19w projection rule, 8w
  child-queryset clause, 8w downgrade clause), which is quotation-with-attribution. Pass 1's four
  pure-restatement runs are untouched and stand as recorded; not worth a rewrite.
- **The accepted duplication is recorded, and I am not re-raising it.** `spec-002`'s O5 mechanism
  sentence and spec-001's new projection rule state one fact in two vocabularies. That is the
  knowingly-taken cost of the restore-here disposition, the alternative is written up in the
  rationale's `## N+1 strategy` entry, and re-litigating a recorded rejected alternative is what
  `worker-3.md` tells me not to do.
- **Existence challenge: none raised.** The item adds no helper, registry, or indirection layer; it
  writes no `.py` file outside gitignored temp tests.

### The binding condition on the rejected alternative — where it lives

Confirmed durable, not scratchpad-only. `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md`
`### `## N+1 strategy``, under *Alternative rejected — hand both rules to a later pass that may write
`spec-002``, carries it in bold: **a later cycle that re-homes these two rules to `spec-002` must
re-home the PR #583 carve-out with them and delete all three from spec-001 in the same change.** The
entry opens `Spec: [N+1 strategy][spec-001-n1]`, so it is keyed to a spec section by heading and by
resolving anchor (`#n1-strategy`), which is `BUILD.md`'s reader rule. The artifact's own copy in
`### Notes for Worker 1` item 3 is the per-cycle echo, not the record.

### The 21-anchor constraint — re-run, not accepted

```
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-001-django_types-0_0_1.md
OK: 21 terms - all have glossary entries and at least one spec link.
exit=0

$ uv run python examples/fakeshop/manage.py import_spec_terms --check
OK: 49 done cards have glossary links.
exit=0

$ grep -o '\]\[glossary-[a-z0-9_-]*\]' <spec> | sort | uniq -c   ->  2 configurationerror, 1 x20
   total occurrences 22, distinct 21
```

**Unchanged: 21 distinct anchors, 22 body links, `configurationerror` the only anchor with two** —
which is the expected result, since this pass's five spec edits add or rewrite prose carrying no
glossary link. Exit 0 on both commands is the gate; `49` is the concurrent session's card wrap and is
not a measurement of this cycle.

### Markdown link convention and `AGENTS.md` rule 27

Independently re-derived (`r2b2-spec001/links2.py`), then cross-checked against the pass's
`r2b-spec001/verify.py`; the two agree on every number.

- One `<!-- LINK DEFINITIONS -->` marker each; all 10 canonical group headers present in START.md's
  exact order, compared positionally; empty groups retained.
- Spec **22 defs / 22 used**, rationale **18 / 18**; 0 undefined, 0 orphaned in both.
- All **40** def targets exist on disk on the normalized join from each file's own directory.
- Alphabetical within every group in both files. No inline `](path)` cross-file link outside fences.
- All **15** rationale-cited in-page anchors resolve against surviving spec headings, computed by a
  slugger that renders reference-link markup rather than stripping brackets. `#scalar-field-conversion`
  resolves.
- **Rule 27: both files sweep clean** — zero `path:NN` hits under a pattern covering
  `.py/.md/.csv/.html/.toml/.yml`. Every symbol path the pass added resolves:
  `types/base.py::_build_annotations`, `optimizer/walker.py::plan_relation` / `::_build_child_queryset`
  / `::_plan_prefetch_relation` / `::_record_relation_access`, `optimizer/plans.py`,
  `utils/querysets.py::apply_type_visibility_sync`,
  `tests/types/test_definition_order.py::test_annotation_only_relation_override_keeps_generated_resolver`
  (`:222`). Both `#"…"` substring refs match exactly once in their file.

### Byte accounting

| Claim | Re-derived |
|---|---|
| spec 43,651 -> 44,502 (+851) | `wc -c` = **44,502** |
| rationale 52,961 -> 59,706 (+6,745) | `wc -c` = **59,706** |
| -7,839 / -14.98% against HEAD | `git show HEAD:<path> \| wc -c` = **52,341**; 44,502 - 52,341 = -7,839 = -14.98% |
| 27 registry methods / 26 `SCALAR_MAP` / 23 in the deleted block | `ast` + enumeration, all three exact |
| 21 anchors / 22 links, 22/22 + 18/18 defs, 40 paths, 15 anchors | above |

Every one holds. The count discipline is now clean two passes running on the structural numbers; the
one that failed (Low 1) is rhetorical and was not among the three this pass re-measured.

### Dispatched findings checklist walk

Eighteen `- [x]` boxes plus the two un-rowed surfaces, one `- [ ]`. D1-D18 were re-derived against
source in pass 1 and this pass changed none of the spec text they cover, so they stand; spot-checked
D16/D17's scalar rows and D5's `types/relay.py::apply_interfaces` again at HEAD, both hold. **D13 is
now `- [ ]` with an adequate reason**: `BUILD.md` `### Dispatched findings checklist` reserves the
tick for a box whose fix landed in *this* diff, D13's contract was discharged by R1's rationale move,
and the one-line deferral is recorded where `BUILD.md` asks for it. The un-tick loosens nothing — the
row is closed, by a prior pass, and the box now says which. The `## Files to add` un-rowed box stays
correctly ticked after M1's edit.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is empty (0 bytes). `__all__` and the re-export
list are unchanged, as the plan's build-wide context flags require.

### CHANGELOG sanity

Not applicable; the pass did not modify `CHANGELOG.md`.

### Documentation / release sanity

- `uv run python scripts/check_trailing_commas.py --check <both files>` -> exit 0.
  `git diff --check -- docs/SPECS/spec-001-django_types-0_0_1.md` -> exit 0.
- Version attributions added this pass check out: `0.316.0` is the declared Strawberry floor, and
  `spec-029-consumer_dx_cleanup-0_0_9.md` exists on disk and owns the `extensions=` construction
  contract.
- **`git status` re-measured at this pass's start and it moved again**: `KANBAN.html`, `KANBAN.md`,
  `SECURITY.md`, `TODAY.md`, `docs/GLOSSARY.md`, `docs/spec-049-dependency_ci_hardening-0_0_14.md`,
  `examples/fakeshop/db.sqlite3`, `uv.lock` are dirty; HEAD is unmoved at `fdfb711f`. **Attributed
  semantically, not assumed:** `git diff -- docs/GLOSSARY.md` is exactly `+2` lines, both about a
  hard dependency's declared floor and the audit-across-the-published-range rule — the spec-049
  surface, no spec-001 term touched; `KANBAN.md` is a full board re-render. Recorded, not reverted,
  not edited (`AGENTS.md` rule 34). The only DB-touching command I ran is `import_spec_terms --check`,
  whose `--check` branch returns before the writing transaction.

### `scripts/review_inspect.py`

**Skipped, deliberately.** `BUILD.md` `### When to run the helper during build` triggers on adding or
modifying a `.py` file in the writable set, on `optimizer/` or `types/`, or on 30+ lines of new logic.
This pass's writable set contains no `.py` file — the diff is two Markdown files — and the helper has
nothing to report on a Markdown reconciliation. Recorded per `worker-3.md` `## Static helper use`.

### Failability proofs

**Empty re-run set, and it is legal here.** The pass introduces no boundary, guard, gate, or rejection
path — it writes no executable code — so the mandatory floor in `worker-3.md` (every boundary with a
recorded count of 3 or fewer, and every security / data-isolation boundary) is satisfied vacuously.
`### Failability proofs`'s *"None; this pass introduced no new boundary"* is correct. The executable
checks standing in for tests (both constraint commands, `check_trailing_commas --check`,
`git diff --check`) were re-run independently above rather than accepted.

### Hot-path budget

Not applicable; the plan declares `Hot-path declaration: none`, and no residual item runs per request,
per resolver, per row, or per outbound message. Absence of a number is correct, not a finding.

### Floor verification

Not applicable; the plan declares `Floor-verification scope: none`.

### What looks solid

- **The refusal to restore the O6 paragraph verbatim is the strongest work in the pass.** Re-deriving
  a rule at the moment it is lifted back into contract prose caught a false operative sentence that a
  faithful restore would have re-entered — the same lesson D18 produced against a promoted claim, now
  turned on the pass's own restoration. Both halves of that judgement survive independent
  verification.
- **Medium 2's resolution is a fourth option the review did not list, and it is argued rather than
  assumed.** "A rule stated in the wrong spec is a smaller defect than a rule stated nowhere", with
  the write set as the decider, is the carve-out's own reasoning applied consistently, and the
  rejected alternative carries a binding re-home-all-three-or-none condition in the durable file. I
  would have accepted (b) as well; this is better, because it discharges by content rather than by
  promise.
- **Medium 4 was fixed by re-forming, not re-numbering,** and no re-formed sentence lost precision:
  naming the seven method names is strictly more checkable than "twenty-six", and naming the two
  further sanitization rewrites is more checkable than "seven". The one surviving number I could find
  in the re-formed text (seven method names) is exact.
- **The self-caught recount** ("I wrote six-method body first and caught it on the recount") is the
  practice working out loud, and it is the reason I believe the other counts were measured rather
  than recalled.
- **Concurrency handling is measured, not inherited** — the `git status` list moved again during this
  pass and the artifact says so instead of quoting R2's snapshot.

### Temp test verification

Three scripts under `docs/builder/temp-tests/r2b2-spec001/` (gitignored):

- `counts.py` — `ast` walks for `registry.py::TypeRegistry`'s method count and `SCALAR_MAP`'s entry
  count. Confirmed both re-measured numbers.
- `links2.py` — link scaffold, group headers, alphabetical order, undefined / orphan refs, on-disk
  existence, and an **independently implemented** GitHub slugger for the in-page anchors. Written so
  the corrected method from L5 is verified by something other than itself.
- `test_hint_visibility.py` — two rows, both passing, run with `-o addopts=""` so no `--cov*` flag
  was used. It is the evidence behind Medium 1 and carries its own positive control.

**Disposition.** None caught a package behaviour bug — Medium 1 is a defect in the spec's prose, and
the behaviour it exposes is the package's intended treatment of a consumer-supplied queryset — so
nothing here is promotable as a fix. `test_hint_visibility.py` does, however, pin a real interaction
that the permanent suite does not (see `### Notes for Worker 1` item 5), and R1's and pass 1's
standing suggestion that the link / anchor / overlap scripts become a `scripts/` helper now has a
fourth data point.

### Notes for Worker 1 (spec reconciliation)

Carried into R3 and the final gate.

1. **The three `spec-002` obligations: recorded state matches reality.** `git status` carries no
   `spec-002` entry and I re-read both references. `spec-002:9` (*"predicted that the optimizer half
   of its scope would eventually warrant its own document"*) and `spec-002:80` (the visibility-leak /
   downgrade discussion *"that motivated bundling the optimizer with `spec-001…` originally"*) are
   **open**, and spec-001 no longer carries the cut-line prediction (`grep` = 0), so both still point
   into rationale-only text. Item 3 is **closed**, correctly: both rules are contract in spec-001's
   `## N+1 strategy` (subject to Medium 1's clause), so R3's Worker 1 pass inherits a recording duty,
   not a rule-stating one. Assign both open items to a **Worker 1** pass — `spec-002` is a spec file.
2. **The re-home condition must travel with any later `spec-002` cycle.** If that cycle re-homes the
   two rules, it takes the PR #583 carve-out with them and deletes all three from spec-001 in one
   change. Durable copy: rationale `### `## N+1 strategy``.
3. **The anchor constraint for R3 is unchanged: 21 anchors / 22 body links**, `configurationerror`
   the only one with two. Re-measured this pass.
4. **`import_spec_terms --check` reads `OK: 49 done cards`, exit 0.** The number is the concurrent
   session's; exit 0 is the contract.
5. **A correctness observation about the package: none — but one test-surface gap, recorded not
   fixed** (this cycle writes no source and no test). No permanent test pins the interaction Medium 1
   turns on: that `OptimizerHint.prefetch(obj)` uses the consumer's queryset verbatim even when the
   target type declares a custom `get_queryset`. `tests/optimizer/test_hints.py` pins that the hint
   carries the object and rejects `to_attr` on a non-consumer-assigned relation, but nothing pins the
   visibility interaction in either direction. Since the behaviour is deliberate
   (`optimizer/walker.py::_apply_hint` #"Consumer-supplied Prefetch objects commonly close over"), a
   row asserting it is a cheap way to stop a future refactor "fixing" it silently. Whether that
   belongs to this package's next optimizer cycle is a maintainer call, not a spec-001 item.
6. **R2's and pass 1's documentation note stands and I second it a third time:** `DurationField` and
   `BinaryField` raise `ConfigurationError` on any model that declares one; `docs/GLOSSARY.md` and
   `types/converters.py`'s module docstring say so, `README.md` and `TODAY.md` remain unchecked. R3's
   durable-doc audit should include them.
7. **Re-measure `git status` at R3's start.** It moved again during this pass while HEAD stayed at
   `fdfb711f`. Attribute every generated-doc diff semantically before treating it as spec-001 drift —
   `docs/GLOSSARY.md`'s current `+2` lines are spec-049's dependency-floor surface.

### Review outcome

`revision-needed`. Routes back to a **Worker 1** pass, not Worker 2 — the plan's Deviation 3 makes
Worker 1 the only role that may mutate the spec and the rationale, and both in-scope fixes land in
those two files.

The pass is otherwise accepted in full: all nine dispatched findings are genuinely closed, every
re-measured count is exact, the anchor and link scaffolding is unchanged and correct, no contract left
the spec, and the restoration judgement — including the refusal to restore a false sentence verbatim —
is the right call and correctly argued. **One Medium and two Lows, all one-sentence edits:**

- **Medium 1** — bound or drop *"so no plan branch can return rows the target type would have
  filtered out"*; `optimizer/walker.py::_apply_hint`'s consumer-supplied-`Prefetch` branch falsifies
  it, proved executably.
- **Low 1** — drop the "four of the five" count from the rationale's illustrative-blocks paragraph
  (the re-derivable answer is five deletions).
- **Low 2** — delete `now` from *"the converter layer now at `types/converters.py`"*.

Nothing is escalated: unlike pass 1's Medium 2, every fix here is inside R2's own writable list.

---

## Reconciliation performed (Worker 1, pass 3, in place of the Worker 2 apply-changes pass)

Fresh Worker 1 spawn. I wrote neither the R2 reconciliation nor pass 2 and carry none of their
reasoning; the artifact is the contract and `## Review (Worker 3, pass 2)` is the work list.
Deviation 3 routes a `revision-needed` on this item to Worker 1, so this section stands in for a
Worker 2 apply-changes build report and keeps its subsection names. `ARTIFACT.md`
`## Re-pass sections` forbids editing a prior entry: nothing above was rewritten, and the only line
outside this section that this pass touched is the top-level `Status:`. The
`### Dispatched findings checklist` is untouched this pass — no box's contract moved (see
`### Dispatched findings checklist, unchanged` below).

### Spec status-line re-verification

Re-read `docs/SPECS/spec-001-django_types-0_0_1.md` lines 1-5 at pass start, for the fifth time in
this cycle. **Still no status/header block.** Line 1 is `# Spec: DjangoType Foundation`, line 2 is
blank, line 3 opens `## Problem statement`. Nothing to falsify; this pass deletes no predecessor doc
a header could point at.

### Disposition of the three findings

| Finding | Disposition |
|---|---|
| **Medium 1** — the restored O6 paragraph's consequence clause over-claims | **Fixed** in the spec, re-derived against source first; the bound and the branch that forces it recorded in the rationale |
| **Low 1** — *"four of the five [illustrative blocks] were deleted"* | **Fixed** — the paragraph re-formed with no count, and the `# illustrative shape` premise dropped with it (it was never five) |
| **Low 2** — the `now at` version-tense hedge in `## Proposed public surface` | **Fixed** — `now` deleted; the move it hedged at is the rationale entry's to carry |

Nothing was rejected.

### Medium 1 — re-derived against source, then bounded

Worker 3's finding is right and I re-derived it from `optimizer/walker.py` rather than from its
proof. The falsifying branch, read at HEAD:

- `::_apply_hint` #"if hint.prefetch_obj is not None:" rebases the consumer's `Prefetch` through
  `::_prefetch_hint_for_path` (which returns either the object itself or a new
  `Prefetch(adjusted_lookup, queryset=prefetch.queryset, ...)` — the consumer's queryset either way),
  appends it via `append_prefetch_unique`, and `return True`s. `::plan_relation`, the downgrade, and
  `::_build_child_queryset` are all downstream of that return and never run for the relation.
- The only site that applies the hook is `::_build_child_queryset` #"apply_type_visibility_sync". Its
  callers are `::_build_prefetch_child_queryset` (which `::_plan_prefetch_relation` calls) and
  `nested_planner.py` #"base_queryset = build_child_queryset(", which takes it as an injected
  callable. Both are planner-built querysets; neither is reachable from the `prefetch_obj` branch.
- The read side compensates for nothing: `types/resolvers.py` contains no `apply_type_visibility`
  call at all (`grep` over the module = 0), and `::_make_relation_resolver`
  #"prefetched.get(accessor_name)" hands back Django's materialised rows.

So the operative sentence holds and the trailing universal does not. **The width that is actually
true is the population `::_build_child_queryset` covers** — the querysets the planner builds — and
that is what the spec now says: *"…the child queryset of every `Prefetch` the planner builds, the
ordinary many-side prefetch included, so a relation the planner builds a queryset for cannot return
rows the target type would have filtered out."* It is re-derivable by a reader against one symbol
rather than against a plan-branch enumeration, which is why it is a better sentence than the one it
replaces and not merely a narrower one.

**The hint exception is deliberately not named in the spec**, and that is the pass's own pointer rule
applied rather than a silence: `Meta.optimizer_hints` is a later spec's surface, spec-001 names no
hint anywhere, and a bounded claim needs no exception clause to be true. Naming it would have owed a
pointer to the owning spec — new scope in the file this item exists to shrink. Worker 3 said the same
("asserting nothing about it is sufficient"); the reasoning here is independent of that.

**Not a package defect, and not recorded as one.** `::_apply_hint` #"Consumer-supplied Prefetch
objects commonly close over" states the intent and marks the plan non-cacheable for it, which is the
discipline `::_plan_prefetch_relation` applies to a custom `get_queryset`. The defect was in the
spec's prose. Worker 3's test-surface observation (its `### Notes for Worker 1` item 5) is carried
forward below unchanged, not acted on — this cycle writes no source and no test.

### Low 1 — re-formed, and the premise was wrong twice

Re-measured before rewriting, each by counting occurrences of the shortest distinctive token:

| Claim in the paragraph | Measured |
|---|---|
| *"The spec carried five `# illustrative shape` blocks"* | `grep -c 'illustrative shape'` on the HEAD copy = **2** (the `converters.py` and `registry.py` blocks). The marker was never the population |
| *"four of the five were deleted"* | `grep -c '^```python'` = **12** at HEAD, **7** now, i.e. **five** deletions. Each HEAD fence located by line: `convert_scalar`+`SCALAR_MAP`, `convert_relation`, `TypeRegistry`, the `plan_relation` pseudocode, the test module |
| *"The fifth block, the `Meta`-key consumer examples"* | those are **three** blocks under `## DjangoType`, all kept. This artifact's own `### The five illustrative code blocks` table already uses that population |
| *"in two cases to the point of naming a symbol that does not exist"* | holds, and is now stated as the symbol: the `convert_relation` and `TypeRegistry` blocks both spell `registry.lazy_ref`, and `grep -rn "lazy_ref" django_strawberry_framework/` returns only `mutations/fields.py::_lazy_ref` and its callers — no registry method |

**Fixed by re-forming, not re-numbering**, the same remedy pass 2 applied to Medium 4's three counts:
the paragraph's argument is that an illustrative literal is a second copy of a module, and no number
carries any of that weight. It now reads *"every block illustrating a package module was deleted"*,
names `registry.lazy_ref` in place of the two-cases count, and refers to the `Meta`-key consumer
examples in the plural without ordinal position.

### Files touched

- `docs/SPECS/spec-001-django_types-0_0_1.md` — **two** numbered changes: Medium 1's consequence
  clause, Low 2's hedge.
- `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md` — **three** numbered changes: Low 1's
  paragraph, the `## N+1 strategy` entry recording Medium 1, the `## Proposed public surface` entry
  recording Low 2.
- `docs/builder/bld-001-r2-spec_reconciliation.md` — this section and the `Status:` line.
- `docs/builder/worker-memory/worker-1.md` — one appended entry (gitignored; not part of the diff).

Counted off the numbered list in `### Spec changes made (Worker 1 only)` after writing it. **No other
file was written**; `spec-002-optimizer-0_0_2.md` carries no `git status` entry and was not opened
this pass.

### Byte counts

| File | Pass 2 close | This pass | Delta |
|---|---|---|---|
| `docs/SPECS/spec-001-django_types-0_0_1.md` | 44,502 | **44,540** | **+38** |
| `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md` | 59,706 | **61,492** | **+1,786** |

Against HEAD (`git show HEAD:… | wc -c` = **52,341**) the spec is **-7,801 (-14.90%)** across R1 and
R2 combined, from `-7,839 (-14.98%)`. Both working-tree numbers by `wc -c` at the moment of writing,
and the rationale's was **re-measured after a late wording fix that shortened it by 18 bytes** — a
byte count written before the file stopped changing is a stale count, not a measured one.
The ratio is again the mechanism working: a one-clause narrowing in the file every spawn reads, its
derivation and its rejected framing in the file only Workers 1 and 3 read.

### Validation run

Both constraint commands run after **each** of the two edit groups — the two spec edits, then the
three rationale edits — and again at close. Not batched to the end. **No pre-edit baseline was run
this pass, and saying otherwise would over-claim**: the baseline is Worker 3's, re-run immediately
before this pass with exit 0 on both and quoted in `## Review (Worker 3, pass 2)`. This pass removed no anchor's
link site: its spec edits rewrite two sentences, neither carrying a glossary link, so the property
that matters (**no anchor ever below one link**) held at every checkpoint by construction as well as
by measurement.

```
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-001-django_types-0_0_1.md
OK: 21 terms - all have glossary entries and at least one spec link.
exit=0

$ uv run python examples/fakeshop/manage.py import_spec_terms --check
OK: 49 done cards have glossary links.
exit=0

$ uv run python scripts/check_trailing_commas.py --check \
    docs/SPECS/spec-001-django_types-0_0_1.md \
    docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md
exit=0

$ git diff --check -- docs/SPECS/spec-001-django_types-0_0_1.md \
    docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md
exit=0
```

`OK: 49 done cards` is unchanged from what pass 2 handed over; exit 0 is the gate, the number is the
concurrent session's. The terms CSV was not touched and no anchor was rescued by re-adding narration.

No `ruff`: no `.py` file was written. No `pytest`: the pass writes no code, and Worker 3's
`test_hint_visibility.py` was read as evidence, not re-run — its conclusion was re-derived from
`optimizer/walker.py` directly instead, which is the stronger check.

### Anchor budget after this pass

```
$ grep -o '\]\[glossary-[a-z0-9_-]*\]' docs/SPECS/spec-001-django_types-0_0_1.md | sort | uniq -c | sort -rn | head -1
   2 ][glossary-configurationerror]
$ ... | wc -l            -> 22 occurrences
$ ... | sort -u | wc -l  -> 21 distinct
```

**Unchanged: 21 distinct anchors, 22 body links, `configurationerror` the only anchor with two.**

### Link and anchor resolution

Re-derived this pass, not carried:

- One `<!-- LINK DEFINITIONS -->` marker in each file; all 10 canonical group headers present in
  START.md's exact order (compared positionally against the list, `True` in both files); empty groups
  retained; alphabetical within every group in both files.
- Spec **22 defs / 22 used**, rationale **18 / 18**; zero undefined, zero orphaned.
- Every def target exists on disk from the citing file's own directory (fragment stripped before the
  existence test — the naive check reports every `../GLOSSARY.md#anchor` as missing).
- All **15** rationale-cited in-page anchors resolve against surviving spec headings, on a slugger
  that renders reference-link markup before slugging (the corrected method from pass 2's Low 5).
  `#proposed-public-surface` and `#n1-strategy`, the two sections this pass edited, both resolve; no
  heading was reworded.
- No inline `](path)` cross-file link outside fences in either file.
- **`AGENTS.md` rule 27: both files sweep clean** — zero hits for
  `[A-Za-z0-9_/.-]+\.(py|md|csv|html|toml|yml):[0-9]+`. Every symbol ref this pass added resolves,
  and each `#"…"` substring matches **exactly once** in its file: `optimizer/walker.py::_apply_hint`
  #"if hint.prefetch_obj is not None:" and #"Consumer-supplied Prefetch objects commonly close over",
  `types/resolvers.py::_make_relation_resolver` #"prefetched.get(accessor_name)",
  `optimizer/walker.py::_prefetch_hint_for_path`, `utils/querysets.py::apply_type_visibility_sync`.

### Dispatched findings checklist, unchanged

This pass ticks and un-ticks nothing. Its two spec edits narrow one clause inside change 3 of pass 2
and delete one word from a sentence no row covers; no box's contract moved in either direction. D13
stays `- [ ]` with the deferral reason pass 2 recorded, which Worker 3 re-audited and accepted.

### Concurrent-session churn observed (not this pass's, not reverted)

Re-measured at this pass's start, as Worker 3's item 7 requires. HEAD is still `fdfb711f`. Dirty and
not mine: `KANBAN.html`, `KANBAN.md`, `SECURITY.md`, `TODAY.md`, `docs/GLOSSARY.md`,
`docs/spec-049-dependency_ci_hardening-0_0_14.md`, `examples/fakeshop/db.sqlite3`, `uv.lock`.
**Attributed semantically, not assumed**: `git diff -- docs/GLOSSARY.md` is `+2` lines, one paragraph
under the hard-dependency entry about a declared floor being an API-compatibility bound and the
audit-across-published-wheels rule — spec-049's surface, no spec-001 term, no anchor this spec links
to renamed. The list has also **shrunk** since the snapshot in my dispatch prompt (two `-terms.csv`
files under `docs/SPECS/appx/` are no longer dirty), which is another session's doing and another
reason to re-measure rather than inherit. Recorded, not reverted, not edited (`AGENTS.md` rule 34).
The only DB-touching command this pass ran is `import_spec_terms --check`, whose `--check` branch
returns before the writing transaction.

### Failability proofs

None; this pass introduced no boundary, guard, gate, or rejection path. It writes no executable code.

### Hot-path budget

Not applicable; the plan declares `Hot-path declaration: none`.

### Floor verification

Not applicable; the plan declares floor-verification scope none.

### Implementation notes

- **A restored rule is a HEAD claim, and so is the CONSEQUENCE drawn from it.** Pass 2 re-derived the
  rule and got it right, then drew a universal from it that another branch of the same module
  falsifies. The rule and its consequence are two claims; a pass that measures one and
  reasons the other has measured half. The remedy that generalises: **write the consequence over the
  population the verified symbol covers** — here `::_build_child_queryset`'s call sites — rather than
  over a category the prose invents ("plan branch"), because the first is re-derivable and the second
  is an enumeration nobody performed.
- **A universal added to a standing contract is the sentence to attack hardest**, and this one was
  added by the pass that was fixing an over-claim of a different shape. The section's opener already
  says `spec-002` owns the planner; a universal quantified over *plan branches* is exactly the claim
  a spec that does not own the planner cannot underwrite.
- **The three findings all sat in prose the two prior passes wrote, not in the original spec.** That
  is the expected shape at this depth of a reconciliation cycle and is an argument for the re-review,
  not against it: R2's own diff is the newest and least-audited text in either file.
- **Every count in this section was measured at the moment of writing**: byte counts by `wc -c` and
  `git show HEAD:… | wc -c`; 21/22 anchors by `uniq -c` on occurrences; 12 -> 7 fences and the two
  `illustrative shape` markers by `grep -c` on a HEAD copy in a scratch path outside the repo; 22/22
  and 18/18 defs, 15 in-page anchors and the on-disk path check by script; `#"…"` uniqueness by
  `grep -c -F`. The two edit counts (two spec, three rationale) were read off the numbered list below
  after it was written.

### Notes for Worker 3

- **The claim to attack is the new bound itself.** *"a relation the planner builds a queryset for"*
  is a population claim: it is true iff `optimizer/walker.py::_build_child_queryset` is the only site
  applying the target type's `get_queryset` to a relation queryset, and iff every planner-built
  `Prefetch` reaches it. Re-derive both directions from `walker.py` and `nested_planner.py` rather
  than from this section; a second uncovered builder would make the new sentence false the same way
  the old one was.
- **Check that nothing else in either file still draws the wide consequence.** `grep` for
  `no plan branch` — the two surviving hits are both in the rationale, one quoting the retracted
  clause and one recording it under *claims the spec no longer makes*, which is the intended shape.
- **Re-run both constraint commands.** The expected result is *unchanged*: 21 anchors, 22 links,
  `configurationerror` the only one with two. A change is a finding.
- **Low 1's population is re-derivable in one command pair**: `grep -c '^```python'` on a HEAD copy
  (12) and on the working tree (7). If you re-check the two-cases claim, `lazy_ref` is the token.
- The diff to read is `git diff -- docs/SPECS/spec-001-django_types-0_0_1.md` plus the untracked
  rationale. Do not `git stash`, `git checkout` or `git restore` anything — the tree carries a
  concurrent session's uncommitted spec-049 work.

### Notes for Worker 1 (spec reconciliation)

Carried into R3 and the final gate. Items 1-3 restate pass 2's hand-over with this pass's
re-confirmation; items 4-7 are unchanged obligations I am not silently dropping.

1. **`spec-002:9` and `spec-002:80` are open, and that recorded state is confirmed rather than
   assumed.** `git status` carries no `spec-002` entry this pass either, and neither reference was
   touched. Both point into text that now lives only in spec-001's rationale. Assign the edit to
   R3's **Worker 1** pass — `spec-002` is a spec file. Minimum discharge is a pointer naming
   `appx/spec-001-django_types-0_0_1-rationale.md`, not new narration.
2. **The third obligation stays closed.** Both optimizer rules are contract in spec-001's
   `## N+1 strategy`; this pass narrowed one clause of one of them and did not move either rule. R3's
   `spec-002` pass inherits a recording duty (pass 2's item 2: the natural site is spec-002's
   ``## Coordination with `spec-001-django_types-0_0_1.md``), not a rule-stating one.
3. **The re-home condition is unchanged and durable.** A later cycle that re-homes the two rules to
   `spec-002` must re-home the PR #583 carve-out with them and delete all three from spec-001 in the
   same change. Record: the rationale's ``### `## N+1 strategy``` entry.
4. **The anchor constraint for R3 is unchanged: 21 anchors / 22 body links**, `configurationerror`
   the only one with two, re-measured at this pass's close.
5. **A correctness observation about the package: none.** Every symbol this pass read — `_apply_hint`,
   `_prefetch_hint_for_path`, `_build_child_queryset`, `_build_prefetch_child_queryset`,
   `_plan_prefetch_relation`, `plan_relation`, `_make_relation_resolver` — behaves as its own
   docstrings and comments claim, the consumer-supplied-`Prefetch` branch included. **Worker 3's
   test-surface gap is carried forward unfixed and unpromoted**: no permanent test pins that
   `OptimizerHint.prefetch(obj)` uses the consumer's queryset verbatim even when the target type
   declares a custom `get_queryset` (`tests/optimizer/test_hints.py` pins the object and the
   `to_attr` rejection, not the visibility interaction). Since the behaviour is deliberate, a row
   asserting it is cheap insurance against a future refactor "fixing" it. A maintainer call for the
   next optimizer cycle, not a spec-001 item, and out of this cycle's write set either way.
6. **The `DurationField` / `BinaryField` documentation note stands, now seconded three times.** They
   raise `ConfigurationError` on any model that declares one; `docs/GLOSSARY.md` and
   `types/converters.py`'s module docstring say so, `README.md` and `TODAY.md` remain unchecked. R3's
   durable-doc audit should include them.
7. **Re-measure `git status` at R3's start.** It moved again during this pass — in both directions —
   while HEAD stayed at `fdfb711f`. Attribute every generated-doc diff semantically before treating
   it as spec-001 drift.

### Spec changes made (Worker 1 only)

**Two** numbered changes to `docs/SPECS/spec-001-django_types-0_0_1.md` and **three** to
`docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md`, counted off the list below after writing
it.

**`docs/SPECS/spec-001-django_types-0_0_1.md`**

1. `## N+1 strategy`, the visibility paragraph — *"the child queryset of every generated `Prefetch`,
   the ordinary many-side prefetch included, so no plan branch can return rows the target type would
   have filtered out"* -> *"the child queryset of every `Prefetch` the planner builds, the ordinary
   many-side prefetch included, so a relation the planner builds a queryset for cannot return rows
   the target type would have filtered out"*. Reason: Worker 3 pass 2 Medium 1 — the universal is
   false at HEAD (`optimizer/walker.py::_apply_hint`'s consumer-supplied-`Prefetch` branch returns
   before `::_build_child_queryset`), and the bounded form is re-derivable against one symbol.
   Re-derived from `walker.py`, `nested_planner.py` and `types/resolvers.py` before writing.
2. `## Proposed public surface` — *"the converter layer now at `types/converters.py`"* -> *"the
   converter layer at `types/converters.py`"*. Reason: Worker 3 pass 2 Low 2; `now at` is a
   version-tense hedge of the shape pass 2's Medium 1 removed from `## Files to add`, and
   `BUILD.md` `## Spec rationale extraction` forbids the spec narrating its own history.

**`docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md`** (Worker 1's file; these record this
pass's own spec edits and correct this pass's predecessors' prose, never moved spec text)

3. ``### `## N+1 strategy``` — the *Restored* entry's second bullet retitled *"Visibility filtering
   on every branch the planner builds"*, its body re-worded to the planner-built population, and a
   new paragraph added recording why the universal was withdrawn: the `_apply_hint` branch that
   falsifies it, the intent comment that makes the behaviour deliberate rather than a package defect,
   the read side adding nothing, and why the hint surface is deliberately not named in the spec. A
   *Claim the spec no longer makes* line closes it. Reason: Medium 1's derivation must be recoverable
   by a later reader, and the rationale is where a withdrawn claim is legal.
4. `### The two judgement calls the whole pass rests on` — the illustrative-code-blocks paragraph
   re-formed with no count: *"four of the five were deleted"* -> *"every block illustrating a package
   module was deleted"*, the false *"five `# illustrative shape` blocks"* premise dropped, the
   two-cases claim restated as the symbol (`registry.lazy_ref`), and the `Meta`-key examples referred
   to in the plural rather than as "the fifth block". Reason: Worker 3 pass 2 Low 1; every number in
   the paragraph was re-measured and the argument needs none of them.
5. ``### `## Proposed public surface``` — new clause recording that the first correction wrote the
   module move as a `now at` hedge, why that is the same defect as a chronology, and that the fact of
   the move is this entry's to carry. Reason: edit 2's explanation must land somewhere.

**Checklist boxes**: none ticked or un-ticked this pass. D13 remains `- [ ]` with pass 2's recorded
deferral reason, which Worker 3 re-audited and accepted.

---

## Review (Worker 3, pass 3)

Fresh spawn. I wrote neither of the prior two reviews and carry none of their reasoning; the artifact
is the contract. **Narrow pass by dispatch**: the substance of R2 was verified in full by passes 1
and 2, so this pass confirms the three closures, re-derives every count pass 3 asserts, and hunts the
new text for fresh defects. Nothing already accepted as closed is re-litigated.

**What was re-derived, and how.** Byte counts by `wc -c` and `git show HEAD:<path> | wc -c` into a
scratch path outside the repo (no `stash` / `checkout` / `restore`). Anchor budget by counting
`][glossary-<id>]` **occurrences**, not matching lines. Fence populations by `grep -c` on the HEAD
copy and the working tree, plus a per-block enumeration that locates each fence and its section.
Link scaffold, group headers, alphabetical order, undefined / orphan refs, on-disk path existence and
every in-page anchor by `docs/builder/temp-tests/r2b3-spec001/links3.py`, written this pass. The
Medium 1 population claim by reading `optimizer/walker.py`, `optimizer/nested_fetch.py`,
`optimizer/nested_planner.py`, `optimizer/plans.py` and `types/resolvers.py` directly — not from pass
2's temp test, which I did not re-run, and not from pass 3's account of them. Both constraint
commands re-run in full.

### The three closures

| Finding | Verdict | Evidence |
|---|---|---|
| **Medium 1** — the over-claiming consequence clause | **Closed, and the bound is true at HEAD** | population claim re-derived in both directions, below |
| **Low 1** — the illustrative-block count | **Closed** | `12 -> 7` python fences = **five** deletions; `illustrative shape` occurs **2** times at HEAD; the re-formed paragraph carries no count |
| **Low 2** — the `now at` hedge | **Closed** | `grep -n "now at"` over the spec = 0; line 55 reads *"the converter layer at `types/converters.py`"* |

### High:

None.

### Medium:

None.

**Medium 1's new sentence is true at HEAD, and the bound is not a relocation of the over-claim.** The
sentence under test:

> The target type's `get_queryset` is applied to the child queryset of every `Prefetch` the planner
> builds, the ordinary many-side prefetch included, so a relation the planner builds a queryset for
> cannot return rows the target type would have filtered out.

Pass 3's `### Notes for Worker 3` names the right test — the claim holds iff
`optimizer/walker.py::_build_child_queryset` is the only site applying the hook to a relation
queryset, **and** every planner-built `Prefetch` reaches it. Both re-derived from source:

- **Only site.** `grep -rn "apply_type_visibility" django_strawberry_framework/optimizer/` returns
  one call, `::_build_child_queryset` #"queryset = apply_type_visibility_sync(target_type, queryset".
  `types/resolvers.py` contains **zero** occurrences of the token, so the read side compensates for
  nothing.
- **Every planner-built `Prefetch` reaches it.** `grep -rn "Prefetch("` over the package gives three
  *construction* sites and one merge site. `::_plan_prefetch_relation` #"append_prefetch_unique(plan.prefetch_related, Prefetch(lookup_path"
  builds its child through `::_build_prefetch_child_queryset`, whose first statement is
  `::_build_child_queryset`. `optimizer/nested_fetch.py::attach_windowed_prefetch` windows
  `request.child_queryset`, which `nested_planner.py` #"base_queryset = build_child_queryset(" builds
  through the same injected callable. `optimizer/plans.py::append_prefetch_unique` is a merge of
  already-built entries, not a construction. The one remaining `Prefetch(` — `::_prefetch_hint_for_path`
  — is the consumer's.
- The bare-lookup arm (`::_plan_prefetch_relation` #"append_unique(plan.prefetch_related, lookup_path)",
  taken when `related_model is None`) appends a **string**, not a `Prefetch`, so it is outside the
  sentence's population rather than a counterexample to it.

**Does a reader still read the sentence as covering the hint path?** I pushed on this, because
`::_prefetch_hint_for_path` genuinely *calls* `Prefetch(adjusted_lookup, queryset=prefetch.queryset,
to_attr=…)` — planner code constructing a `Prefetch` object whose child queryset never meets the
hook. Three things settle it against that reading:

1. **The sentence glosses its own bound.** The trailing clause is *"a relation the planner builds a
   queryset for"*, and on the hint path the planner builds no queryset — it carries the consumer's
   verbatim. The load-bearing data-isolation claim is therefore unambiguous.
2. **The package's own vocabulary agrees.** `optimizer/plans.py::append_prefetch_unique`
   #"``Prefetch(obj)`` and a walker-generated ``Prefetch``" names exactly this distinction, and
   `::_prefetch_hint_for_path`'s docstring is *"Return ``prefetch`` adapted from a type-relative
   lookup to ``full_path``"* — an adaptation of the consumer's object, not a build.
3. **The constructor-call reading is self-refuting.** `::_prefetch_hint_for_path` returns the
   consumer's object **unchanged** when its lookup already matches the full path, and re-instantiates
   only when a rebase is needed. Under "builds == calls the constructor", the identical hint would be
   inside the population or outside it purely by how the consumer spelled the lookup. No coherent
   reader lands there.

Pass 3's decision **not** to name the `Meta.optimizer_hints` exception is right on its own reasoning:
spec-001 names no hint anywhere, naming one would owe a pointer to the owning spec, and a bounded
claim needs no exception clause. That is also what pass 2 recommended, reached independently here.

### Low:

None.

### DRY findings

- **No new duplication.** The pass adds 38 bytes to the spec and 1,786 to the rationale; every added
  byte in the rationale is derivation or a withdrawn claim, which is the file that owns both. The
  ratio is the mechanism working, as pass 3 says.
- **The withdrawn universal is stated once as contract-negative and once as quotation.** `grep -c "no
  plan branch"` -> spec **0**, rationale **2** (line 682 quoting the retracted clause inside the
  derivation, line 696 under *Claim the spec no longer makes*). That is the intended shape, not a
  duplication: one is the argument, one is the index entry `BUILD.md` `## Spec rationale extraction`
  requires.
- **Existence challenge: none raised.** The item adds no helper, registry, or indirection layer, and
  writes no `.py` file outside a gitignored temp script.

### Every count in `## Reconciliation performed (Worker 1, pass 3)`, re-derived

Nine asserted counts, all re-measured against the tree rather than read:

| Asserted | Re-derived |
|---|---|
| spec 44,502 -> **44,540** (+38) | `wc -c` = **44,540** |
| rationale 59,706 -> **61,492** (+1,786) | `wc -c` = **61,492** |
| HEAD spec **52,341**; **-7,801 / -14.90%** | `git show HEAD:… \| wc -c` = **52,341**; 44,540-52,341 = **-7,801** = **-14.905%** |
| **two** spec changes, **three** rationale changes | see the independent byte-arithmetic proof below; all three rationale edits located and read |
| `grep -c '^```python'` = **12** at HEAD, **7** now | **12** / **7**; five deletions |
| `grep -c 'illustrative shape'` = **2** at HEAD | **2** (the `converters.py` and `registry.py` blocks); **0** in the working spec and **0** in the rationale |
| the two `lazy_ref` blocks | enumerated all 12 HEAD fences by line: exactly **2** contain `lazy_ref` (`350-367` relation half, `383-433` registry) |
| **21** anchors / **22** links, `configurationerror` the only double | occurrences **22**, distinct **21**, `configurationerror` = **2** |
| **22/22** and **18/18** defs, **15** in-page anchors, every def target on disk | **22/22**, **18/18**, **15/15**, **40** targets, 0 missing |

**The two-spec-edits claim is provable, not merely plausible.** `len(new clause) - len(old clause)`
= **+42**, `len("now ")` = **-4**, sum **+38** — exactly the measured spec delta. Any third spec edit
this pass would have to net to zero bytes. That is the strongest form of "no other file was written"
available for a tracked file, and it is independent of the section's own prose.

**The struck baseline claim landed.** `### Validation run` now reads *"No pre-edit baseline was run
this pass, and saying otherwise would over-claim"*, and attributes the baseline to pass 2's own
re-run. That is the self-correction the count rule wants, verified present rather than assumed.

### The 21-anchor constraint — re-run, not accepted

```
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-001-django_types-0_0_1.md
OK: 21 terms - all have glossary entries and at least one spec link.
exit=0

$ uv run python examples/fakeshop/manage.py import_spec_terms --check
OK: 49 done cards have glossary links.
exit=0

$ grep -o '\]\[glossary-[a-z0-9_-]*\]' <spec> | wc -l        -> 22
$ grep -o '\]\[glossary-[a-z0-9_-]*\]' <spec> | sort -u | wc -l -> 21
```

**Unchanged, as pass 3 predicted: 21 distinct anchors, 22 body links, `configurationerror` the only
anchor with two.** Exit 0 on both commands is the gate; `49` is the concurrent session's card count
and is not a measurement of this cycle. Neither spec sentence this pass rewrote carried a glossary
link, so the property held by construction as well as by measurement.

### Markdown link convention and `AGENTS.md` rule 27

Re-derived by `docs/builder/temp-tests/r2b3-spec001/links3.py`, written this pass and not shared with
any prior pass's script:

- One `<!-- LINK DEFINITIONS -->` marker each; all 10 canonical group headers present in START.md's
  exact order, compared **positionally**; empty groups retained; alphabetical within every group.
- Spec **22 defs / 22 used**, rationale **18 / 18**; 0 undefined, 0 orphaned, 0 duplicate def ids.
- All **40** def targets exist on disk from each file's own directory (fragment stripped first).
- All **15** rationale-cited in-page anchors resolve against surviving spec headings, on a slugger
  that renders reference-link markup before slugging. `#n1-strategy` and `#proposed-public-surface` —
  the two sections this pass edited — both resolve; no heading was reworded.
- No inline `](path)` cross-file link outside fences in either file.
- **Rule 27: both files sweep clean** — zero hits for
  `[A-Za-z0-9_/.-]+\.(py|md|csv|html|toml|yml):[0-9]+`. Every symbol ref this pass added resolves at
  HEAD (`optimizer/walker.py::_apply_hint`, `::_prefetch_hint_for_path`, `::_build_child_queryset`,
  `::_build_prefetch_child_queryset`, `::_plan_prefetch_relation`, `::plan_relation`,
  `::_record_relation_access`, `types/resolvers.py::_make_relation_resolver`,
  `utils/querysets.py::apply_type_visibility_sync`), and each `#"…"` substring matches **exactly
  once** in its file, checked by `grep -c -F`: #"if hint.prefetch_obj is not None:" (1),
  #"Consumer-supplied Prefetch objects commonly close over" (1), #"prefetched.get(accessor_name)" (1),
  #"including the FK columns required to materialize" (1), #"reintroduce the N+1" (1).

### Low 1's re-formed paragraph, checked against the population it now describes

The paragraph claims *"every block illustrating a package module was deleted"* and that the `Meta`-key
consumer examples were kept. Enumerated every surviving fence by section: `## Proposed public surface`
(imports), `## DjangoType` x3 (`Meta`-key consumer examples), `## Choice field enum generation`
(two consumer `DjangoType`s), `## get_queryset` (a consumer `get_queryset` override),
`## N+1 strategy` (schema construction). **Seven blocks, all consumer surface; none illustrates a
package module.** The claim is exact, and the plural "`Meta`-key consumer examples" is right — there
are three, and no ordinal position is asserted.

### Byte and delta accounting

Every number in the table above holds. The count discipline is clean for a second consecutive pass on
the structural numbers, and pass 3 additionally re-measured the two rhetorical numbers that failed in
pass 2 (`illustrative shape` = 2, not 5) and struck an unperformed-run claim of its own.

### Dispatched findings checklist walk

Unchanged this pass and correctly so: the two spec edits narrow one clause inside pass 2's change 3
and delete one word from a sentence no row covers, so no box's contract moved. Eighteen `- [x]` plus
the two un-rowed surfaces; **D13 stays `- [ ]`** with the deferral reason recorded under
`### Spec changes made (Worker 1 only)`, which is what `BUILD.md` `### Dispatched findings checklist`
asks of an open box. I re-audited nothing in D1-D18 that this pass did not touch — pass 1 and pass 2
derived them against source and this pass changed no text they cover.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is empty (0 bytes). `__all__` and the re-export
list are unchanged, as the plan's build-wide context flags require.

### CHANGELOG sanity

Not applicable; the pass did not modify `CHANGELOG.md`.

### Documentation / release sanity

- `uv run python scripts/check_trailing_commas.py --check <both files>` -> exit 0.
  `git diff --check -- docs/SPECS/spec-001-django_types-0_0_1.md` -> exit 0.
- The surviving `## N+1 strategy` paragraph reads coherently around the narrowed clause: the
  downgrade sentence that follows it (*"the one branch — a collapsed FK join — that has no child
  queryset to apply it to"*) is scoped to the same planner population and is not falsified by the
  hint path, which does have a child queryset (the consumer's).
- **Concurrent-session churn re-measured at this pass's start, attributed semantically, not
  reverted.** HEAD is still `fdfb711f`. Dirty and not this cycle's: `KANBAN.html`, `KANBAN.md`,
  `SECURITY.md`, `TODAY.md`, `docs/GLOSSARY.md`, `docs/spec-049-dependency_ci_hardening-0_0_14.md`,
  `examples/fakeshop/db.sqlite3`, `uv.lock`. The list **has shrunk** relative to my own dispatch
  snapshot — `docs/SPECS/spec-048-secure_output_defaults-0_0_14.md` and both
  `docs/SPECS/appx/*-terms.csv` entries are now clean — which independently confirms pass 3's
  observation that it moved in both directions. `AGENTS.md` rule 34 applies; nothing touched. The
  only DB-reading command I ran is `import_spec_terms --check`.

### `scripts/review_inspect.py`

**Skipped, deliberately**, with the reason the cycle facts give: no `.py` file is in R2's deliverable
writable set — the diff is two Markdown files, and the one `.py` I wrote is a gitignored temp script
under `docs/builder/temp-tests/`, not a package or example module. `BUILD.md` `### When to run the
helper during build` triggers on adding logic to a package `.py` file; there is none. Recorded per
`worker-3.md` `## Static helper use`.

### Failability proofs

**Empty re-run set, and it is legal here.** The pass introduces no boundary, guard, gate, or rejection
path — it writes no executable code — so `worker-3.md`'s mandatory floor (every boundary with a
recorded count of 3 or fewer, plus every security / data-isolation boundary) is satisfied vacuously.
`### Failability proofs`'s *"None; this pass introduced no boundary…"* is correct. The executable
checks standing in for tests (both constraint commands, `check_trailing_commas --check`,
`git diff --check`) were re-run independently above rather than accepted.

### Hot-path budget

Not applicable; the plan declares `Hot-path declaration: none`. Absence of a number is correct.

### Floor verification

Not applicable; the plan declares floor-verification scope none.

### What looks solid

- **The bound was derived from a symbol's call sites, not from a category the prose invented**, and
  that is why it survives an independent re-derivation. "The population `::_build_child_queryset`
  covers" is checkable by one `grep` in two directions; "no plan branch" was an enumeration nobody
  had performed. Pass 3's own implementation note states the generalisable rule and it earns it.
- **The pass re-derived Medium 1 from `walker.py` instead of re-running pass 2's temp test.** A
  reviewer's proof re-executed is one measurement counted twice; a second derivation from source is
  a second measurement. That is the stronger check and it was the right call to say so.
- **Low 1's premise was wrong in a direction nobody asked about.** The finding challenged "four of
  the five"; the pass re-measured and found the *marker* population ("five `# illustrative shape`
  blocks") was itself false — 2 occurrences, never 5 — and dropped the whole numeric frame rather
  than repairing one number inside a false one. Re-forming beat re-numbering for the third time in
  this item.
- **The struck baseline claim.** Deleting an assertion the pass could not stand behind, and saying in
  the artifact that it was struck, is worth more to the next reader than any number in the section.
- **Concurrency handling stayed measured**: the dirty list is re-derived per pass and its shrink was
  noticed, which is the failure mode a snapshot inherited from a dispatch prompt would have hidden.

### Temp test verification

One script under `docs/builder/temp-tests/r2b3-spec001/` (gitignored):

- `links3.py` — link scaffold, positional group-header order, alphabetical order within group,
  undefined / orphan / duplicate def ids, on-disk def-target existence with the fragment stripped,
  inline-`](path)` sweep, rule-27 sweep, and an independently implemented GitHub slugger for the
  in-page anchors. Written this pass; it shares no code with `r2b-spec001/verify.py` or
  `r2b2-spec001/links2.py`.

No `pytest` was run this pass and no `--cov*` flag was used anywhere. **Disposition:** nothing here
caught a package behaviour bug, so nothing is promotable. The standing suggestion that the
link / anchor / overlap scripts become a `scripts/` helper now has a **fifth** data point across R1
and R2 — three cycles of reviewers have each hand-written the same checker.

### Notes for Worker 1 (spec reconciliation)

Carried into R3 and the final gate. Items 1-3 and 5-7 restate pass 3's hand-over with this pass's
re-confirmation; nothing is silently dropped, and nothing is escalated — every finding in this item
is now closed inside R2's own writable set.

1. **`spec-002:9` and `spec-002:80` are open, and confirmed so this pass.** `git status` carries no
   `spec-002` entry and the file was not opened by pass 3. Both references point into text that now
   lives only in spec-001's rationale. **Assign both to a Worker 1 pass in R3** — `spec-002` is a
   spec file, and `worker-1.md` `## Scope` makes Worker 1 the only role that may mutate one. Minimum
   discharge is a pointer naming `appx/spec-001-django_types-0_0_1-rationale.md`, never new
   narration. The third obligation stays **closed**: both optimizer rules are contract in spec-001's
   `## N+1 strategy`, so R3 inherits a recording duty (natural site: spec-002's
   ``## Coordination with `spec-001-django_types-0_0_1.md``), not a rule-stating one.
2. **The re-home condition is durable and must travel.** A later cycle that re-homes the two rules to
   `spec-002` takes the PR #583 carve-out with them and deletes all three from spec-001 in the same
   change. Record: the rationale's ``### `## N+1 strategy``` entry, in bold. Re-confirmed present
   this pass.
3. **The anchor constraint for R3 is unchanged: 21 anchors / 22 body links**, `configurationerror`
   the only one with two. Re-measured at this pass's close. `import_spec_terms --check` reads
   `OK: 49 done cards`, exit 0 — exit 0 is the contract, the number is the concurrent session's.
4. **Test-surface gap, carried forward unfixed and unpromoted for the final gate's deferred-work
   catalog.** No permanent test pins that `OptimizerHint.prefetch(obj)` uses the consumer's queryset
   verbatim even when the target type declares a custom `get_queryset` — i.e. that the hinted
   prefetch child bypasses `utils/querysets.py::apply_type_visibility_sync`. Re-checked this pass:
   `tests/optimizer/test_hints.py` never mentions `get_queryset`; the eight `prefetch_obj` rows in
   `tests/optimizer/test_walker.py` pin inner-selection suppression, connector columns, prefix
   rebasing, non-cacheability, dedupe, and the misconfigured-lookup clean-plan path — none pins the
   visibility interaction in either direction. The behaviour is **deliberate**
   (`optimizer/walker.py::_apply_hint` #"Consumer-supplied Prefetch objects commonly close over"), so
   a row asserting it is cheap insurance against a future refactor "fixing" it silently. Out of this
   cycle's write set (no source, no tests); a maintainer call for the next optimizer cycle.
5. **The `DurationField` / `BinaryField` documentation note stands, now seconded a fourth time.**
   Both raise `ConfigurationError` on any model that declares one; `docs/GLOSSARY.md` and
   `types/converters.py`'s module docstring say so; `README.md` and `TODAY.md` remain unchecked. R3's
   durable-doc audit should include them.
6. **Re-measure `git status` at R3's start.** It moved again — in both directions — while HEAD stayed
   at `fdfb711f`. Attribute every generated-doc diff semantically before treating it as spec-001
   drift; `docs/GLOSSARY.md`'s current diff is spec-049's dependency-floor surface.
7. **A fifth hand-written link/anchor checker.** R1, R2, and all three R2 review passes each wrote
   their own. If a later cycle wants one durable win out of this item, promoting it to `scripts/` is
   it — but it is new scope and belongs to a maintainer, not to R3.

### Review outcome

`review-accepted`. All three findings from pass 2 are genuinely closed; the new bound is true at HEAD
under an independent two-direction re-derivation of the population it quantifies over, and it is not
a relocation of the over-claim — the trailing clause glosses the bound explicitly, the package's own
vocabulary distinguishes a walker-generated `Prefetch` from a hint-supplied one, and the alternative
reading is self-refuting. Every one of the nine counts the pass asserts re-derives exactly, including
the two-spec-edit claim, which the byte arithmetic pins independently of the prose. The anchor budget,
link scaffold, rule-27 sweep, and both constraint commands are unchanged and green.

**No High, Medium, or Low findings, and nothing escalated.** Item R2 goes to Worker 1 for final
verification.

---

## Final verification (Worker 1)

Fresh Worker 1 spawn. I wrote none of the three reconciliation passes and carry none of their
reasoning; the artifact is the contract. Worker 3's pass-3 review closed the item with no findings and
nothing escalated, so **this is the gate on the item, not a fourth review**: nothing already accepted
is re-litigated, and the one check no prior pass performed — reading the reconciled spec end to end as
a reader who has never seen it — is where this pass spent its effort. `ARTIFACT.md` `## Re-pass
sections` forbids editing a prior entry: nothing above was rewritten, and the only line outside this
section that this pass touched is the top-level `Status:`. The `### Dispatched findings checklist` was
audited and needed no change (below).

### Spec status-line re-verification

Re-read `docs/SPECS/spec-001-django_types-0_0_1.md` lines 1-5 at pass start, for the sixth time in this
cycle. **Still no status/header block.** Line 1 is `# Spec: DjangoType Foundation`, line 2 is blank,
line 3 opens `## Problem statement`. There is no target-release, status, owner, or predecessor line to
falsify, and this pass deletes no predecessor doc a header could point at. The check is cheap and it is
recorded rather than skipped, because a stale header is exactly what compounds silently across six
spawns.

### Dispatched findings checklist audit

Walked all twenty-one boxes against the working-tree diff, not against the artifact's account of it.
Each `- [x]` was checked by locating the corrected claim in the spec **and** confirming the falsified
claim is absent, using the shortest distinctive token in each direction rather than a long phrase:

| Box | Falsified claim absent | Corrected claim present |
|---|---|---|
| D1 | no flat `types.py` / `optimizer.py` module claim survives (the one hit for the pattern is `types/base.py`'s intra-package reference to its sibling `converters.py`, not a layout claim) | `## Files to add` opener states the package layout |
| D2 | `lazy_ref` appears twice, both stating its **absence** (`## Registry`, `## Files to add`) | pending-relation trio named at both sites |
| D3 | — | "definition order does not matter" x1 |
| D4 | — | "`aggregate_class`, `fields_class`, and `search_fields` deferred" x1 |
| D5 | — | `types/relay.py::apply_interfaces` x1 |
| D6 | — | "Registration is many-to-one" x1 |
| D7 | — | `BigInt` / `list[inner_type]` / JSON scalar rows, 3 hits |
| D8 | — | `FIELD_OUTPUT_TYPE_MAP` x1 |
| D9 | — | "primary-key annotation is suppressed" x1 |
| D10 | `tests/test_django_types.py` / `test_optimizer.py` / `test_choice_enums.py` = **0** | `tests/types/` inventory present |
| D11 | `fakeshop/fakeshop` = **0** | `examples/fakeshop/apps/products/` present |
| D12 | — | "Three rejections, all `ConfigurationError`" x1 |
| D14 | "aspirational" (case-insensitive) = **0** | `### Files NOT in this spec` states the live example |
| D15 | — | `_detect_custom_get_queryset` x1 |
| D16 | — | `PositiveBigIntegerField` appears once, on the `BigInt` row |
| D17 | — | "deliberately absent from the default map" x1 |
| D18 | — | "Property (`category`, `entries`)" x1 |
| `## Current state` (un-rowed) | heading gone | `## Prior art` x1 |
| `## Files to add` (un-rowed) | restructure chronology gone (Worker 3 pass-2 M1) | present-tense layout |
| `## What this enables …` (un-rowed, inside D14's row) | "What this enables" = **0** | section deleted |

**No over-tick and no under-tick. No box changed state this pass.** Every `- [x]` names a correction
that is genuinely in the diff, and no box left `- [ ]` has a landed contract.

**D13 stays `- [ ]`, and its reason is durable where a later reader will find it.** Worker 3 accepted
the un-tick; my obligation was the *durability* of the reason, since `docs/builder/bld-*.md` is a
per-cycle scratchpad that closes with the cycle. Confirmed: the record lives in
`docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md` `### Drift rows that changed nothing, and
why`, which names the row, quotes what it claimed, cites the HEAD confirmation
(`library.Book.genres` / `alt_branches`, `tests/types/test_definition_relations.py`), and states why no
edit followed. That file is tracked and ships with the spec, so the reason outlives this artifact. The
per-cycle copies (the box's own sentence and pass 2's `### Spec changes made`) are echoes of it, not
the record. Carried forward under `### Spec changes made (Worker 1 only)` below as this gate requires.

### The end-to-end read — the check no prior pass performed

Three passes edited the spec in fragments and three reviews audited those fragments. Nobody had yet
read the result as one document, which is the only vantage point from which a *cross-section*
contradiction is visible: it belongs to no drift row, no finding, and no diff hunk. I read all 508
lines in order, then swept mechanically for the four shapes the dispatch names.

**One real defect, in exactly that class — fixed, spec edit 1 below.**

`## Testing strategy` opened *"Package tests for this surface live under `tests/types/` and
`tests/optimizer/`, with the per-module inventory in "Files to add" below."* `## Files to add`'s
inventory, two sections later, lists `tests/test_registry.py` — which sits directly in `tests/`, not
under either named directory. Both sentences are R2's own new text (HEAD's `## Testing strategy` read
*"All new package tests go in a new root-level file"*, and HEAD names no test module at all), so this
is a defect the reconciliation introduced while correcting D10, on D10's own axis. `tests/test_registry.py`
exists at HEAD, confirmed by `ls tests/`. **A placement rule falsified by the same document's inventory
of the very files it governs is worse than the rule it replaced**, because a reader cannot tell which
half is current — the half-reconciled failure `worker-1.md` `## Review-round custody` names. The
sentence now names the third location.

Fixed here rather than routed back: it is one clause, inside R2's declared write set, on R2's declared
axis, and a `revision-needed` would open a fourth Worker 1 pass and a fourth review for a repair whose
whole content is naming a file that already appears in the spec. `worker-1.md` `## Spec custody` gives
Worker 1 exactly this — edit when the build proves the spec inaccurate, record it under
`### Spec changes made (Worker 1 only)`.

**One count in the standing rationale that a reader's own re-derivation contradicts — fixed by
re-forming, rationale edit 2 below.** The `## Current state` -> `## Prior art` entry read *"Its two
surviving paragraphs are a prior-art survey"*. Measured: the section carries **three** paragraphs
(example project, graphene-django, strawberry-graphql-django); the *survey* is two of them. Same class
as the counts Worker 3 caught in passes 1 and 2, in the same file, and it is the eighth count this
cycle has lost to re-derivation — but it is not merely a bad number. It is the entry that has to
justify why the section's first paragraph belongs under a heading that now says "Prior art", and by
counting it out of existence the entry never made that argument. Re-formed to name what survives and
why all of it is prior art in the sense the heading claims: the fakeshop models predate the spec and
drove it, exactly as the two upstream libraries do. (The same phrase in this artifact's pass-1
`### Implementation notes` is a prior entry I may not rewrite; it is recorded here instead. The
`### `## References`` entry's *"two surviving prior-art paragraphs"* is a different and **correct**
claim — the symbol-path substitution was applied to the graphene and strawberry paragraphs only, and
that is two.)

**The other three shapes, swept and clean:**

- **Contradicting claims.** Beyond the one above, every cross-section pair I could construct holds.
  `scalar_for_field` as "the single lookup shared by field conversion and filter-input conversion" is
  not contradicted by the `FileField` row, because the *scalar* is `str` on both sides and the
  structured output object is layered on top — which is what the row itself says. `ConfigurationError`
  "raised by … optimizer planning failures" beside `OptimizerError` "raised when the optimizer cannot
  plan a relation traversal" reads as near-duplicate at first pass; it is HEAD text unchanged by this
  item and it is **true** — `grep -c "raise ConfigurationError"` over `optimizer/` is 12 (hints 6,
  walker 4, nested_fetch 2), against 11 `raise OptimizerError` package-wide, so the module genuinely
  raises both, configuration-time versus planning-time. Not a finding.
- **Surviving history-narration on R1's or R2's axis.** Swept for 20 markers. `Status:` = 0,
  "Deviation" = 0, "earlier draft" = 0, "now at" = 0, "currently" = 0, "today" = 0, "originally" = 0,
  "later restructure" = 0, "when the first slices" = 0, "as of review" = 0. The four surviving hits are
  all legitimate: three are the one-line rationale pointers `BUILD.md` `## Spec rationale extraction`
  **requires** every decision to keep, and the fourth is `## Suggested implementation slices`' "(Slice 2
  deferred it)" — a plan describing its own ordering, inside the section R1 decided keeps slice
  vocabulary. `### Files NOT in this spec`'s "have since shipped" is chronology about *other* specs,
  load-bearing for which deferred keys are live, and stays.
- **A pointer whose style no longer matches its neighbours.** Eleven owning-spec pointers, all one
  shape — bare filename in a code span plus "owned by" / "owns" — at `## DjangoType`,
  `## Scalar field conversion` (x2), `## Relation field conversion`'s neighbours, `## Registry`,
  `## N+1 strategy` (x2), `## Type naming`, `## Suggested implementation slices`, `## Files to add`,
  `### Files NOT in this spec`. All eleven target files exist on disk (`002`, `008`, `015`, `018`,
  `027`, `028`, `029`, `030`, `031`, `034`, `037`), checked by `ls`. The one un-pointered restatement
  Worker 3 found in pass 1 (`spec-029`) is closed and now reads in the same shape as the other ten.
- **A section left lopsided by its corrections.** Considered and rejected as a defect:
  `## Non-goals` ends with the document-level rationale pointer, which sits oddly under that heading but
  is the conventional "how to read this document" position and is the spec's single global pointer;
  moving it buys nothing and costs a link re-site. `## Prior art`'s three-paragraph shape is answered by
  rationale edit 2 rather than by a spec edit — the heading cannot be reworded, since the rationale
  cites `#prior-art` and a rename would break a resolving anchor to fix a wording preference.

**Two other spec claims spot-verified against source while reading, both hold.**
`pyproject.toml` `[tool.coverage.report] exclude_lines` does carry `raise NotImplementedError`, so
`## Suggested implementation slices`' stub-coverage sentence is true; and the converter symbols
`## Files to add` names (`SCALAR_MAP`, `scalar_for_field`, `convert_field_output`, `convert_scalar`,
`convert_choices_to_enum`, `build_enum_from_choices`, `resolved_relation_annotation`) all exist with
the positional signatures the spec gives — the inventory omits keyword-only parameters uniformly across
all of them, which is an inventory, not a signature claim.

### Division of labour between the two documents

Confirmed, and confirmed as the maintainer framed it rather than as a slogan. The spec states the
contract that holds; the rationale states why it changed and what the spec may no longer claim.

- **The rationale never states a contract the spec does not.** Its twenty entries are keyed to spec
  headings by anchor (all 15 cited anchors resolve), and each carries the three things `BUILD.md`
  requires: the alternatives rejected with why each lost, the changes the section has undergone, and an
  explicit *"Claims the spec no longer makes"* line. The one restored-contract case (`## N+1 strategy`)
  states the rule **in the spec** and the derivation in the rationale, which is the intended split.
- **The spec never explains why.** Its only backward-looking sentences are the four pointers above.
- **The one deliberate exception is on record and I did not disturb it.** The `typing.Any` reason clause
  appears in both files, and the rationale says so explicitly and says why (`worker-1.md`'s
  implementation-relevant-why carve-out: a builder never reads the rationale, so a reason that changes
  how a thing is built has to stay in the spec; an entry recording a rejected alternative has to say
  why it lost). Correct on both halves.
- **The measured residue is Worker 3's four pure-restatement runs** (cache-check ordering,
  `Meta.primary` many-to-one, the plan-cache clause, the `ChoiceFixture` mechanism), recorded across
  two review passes as not worth a rewrite. I re-read all four and agree: each is the minimal contrast a
  *"claims the spec no longer makes"* entry cannot avoid without becoming unintelligible. Recorded, not
  re-litigated. My own rationale edit 2 adds no contract sentence; my edit 1 adds no explanation.

### Validation run

Both constraint commands were run as a **pre-edit baseline**, after each of the two edit groups, and
again at close — five runs, never batched to the end. Neither sentence this pass touched carries a
glossary link, so the property that matters (**no anchor ever below one link**) held by construction as
well as by measurement. Final state:

```
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-001-django_types-0_0_1.md
OK: 21 terms - all have glossary entries and at least one spec link.
exit=0

$ uv run python examples/fakeshop/manage.py import_spec_terms --check
OK: 49 done cards have glossary links.
exit=0

$ uv run python scripts/check_trailing_commas.py --check \
    docs/SPECS/spec-001-django_types-0_0_1.md \
    docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md
exit=0

$ git diff --check -- docs/SPECS/spec-001-django_types-0_0_1.md \
    docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md
exit=0
```

`OK: 49 done cards` is unchanged from what pass 3 handed over. **Exit 0 is the gate; the number is the
concurrent session's** `DONE-049-0.0.14` wrap and is not a measurement of this cycle. The terms CSV was
not touched (`git status` carries no `docs/SPECS/appx/spec-001-django_types-0_0_1-terms.csv` entry) and
no anchor was rescued by re-adding narration.

No `ruff`: no `.py` file was written this pass, and none was created — this pass wrote no temp-test
script, having re-derived every structural number inline. No `pytest`: the item writes no code, and the
plan calls for no focused scope (`### Test additions / updates`: *"None, and none possible"*), so
`## Final verification job` step 5 has an empty set here rather than an unrun one.

### Anchor budget, links, and byte accounting

Every number below measured at the moment of writing.

```
$ grep -o '\]\[glossary-[a-z0-9_-]*\]' docs/SPECS/spec-001-django_types-0_0_1.md | wc -l        -> 22
$ grep -o '\]\[glossary-[a-z0-9_-]*\]' docs/SPECS/spec-001-django_types-0_0_1.md | sort -u | wc -l -> 21
$ ... | sort | uniq -c | awk '$1>1'   -> 2 ][glossary-configurationerror]
```

**Unchanged and confirmed: 21 distinct anchors, 22 body links, `configurationerror` the only anchor
with two.** Every other glossary-linked sentence remains its anchor's sole link. That is the constraint
R3 inherits.

| Claim | Re-derived this pass |
|---|---|
| spec 44,540 -> **44,596** (+56) | `wc -c` = **44,596** |
| rationale 61,492 -> **62,465** (+973) | `wc -c` = **62,465** |
| HEAD spec baseline | `git show HEAD:… \| wc -c` = **52,341** |
| spec against HEAD across R1 + R2 | 44,596 - 52,341 = **-7,745** = **-14.80%**, from `-7,801 / -14.90%` |
| python fences | `grep -c '^```python'` = **7**, unchanged |
| spec link defs | **22 defs / 22 used**, 0 undefined, 0 orphaned |
| rationale link defs | **18 / 18**, 0 undefined, 0 orphaned |
| def targets on disk | **40**, all resolve on the normalized join from each file's own directory (fragment stripped first) |
| group headers | all 10 present in START.md's exact order in both files, compared **positionally**; empty groups retained; alphabetical within every group |
| in-page anchors | **15 of 15** resolve against surviving spec headings, on a slugger that renders reference-link markup before slugging; unresolved set empty |
| `AGENTS.md` rule 27 | **0** hits for `[A-Za-z0-9_/.-]+\.(py\|md\|csv\|html\|toml\|yml):[0-9]+` in either file |
| inline cross-file links | **0** outside fences in either file |

**The `+56` spec delta is provable, not merely plausible.** The inserted string is
``plus `tests/test_registry.py` at the package-test root, `` — 5 + 24 + 27 = **56** characters, exactly
the measured delta. Any second spec edit this pass would have to net to zero bytes. That is the strongest
available form of "one spec edit", and it is independent of this section's prose. Both byte counts were
taken **after** the last wording change, not before: pass 3 recorded that a count written while the file
is still moving is stale rather than measured, and the same trap applies to a final-verification pass
that measures before it finishes writing.

I did **not** re-derive a per-edit count for pass 1's spec changes, and saying "twenty-five" here would
be quoting rather than measuring. Pass 1 records its changes **by heading** (17 headings in
`### What changed, by spec heading`), not by edit; reconstructing a per-edit population from a per-heading
table would be inventing a number nobody counted. Passes 2 and 3 and this pass each carry a numbered list,
and those I counted off the lists: **5 + 2 + 1 = 8** numbered spec changes and **8 + 3 + 2 = 13** numbered
rationale changes.

### Concurrent-session churn observed (not this pass's, not reverted)

Re-measured at this pass's start and again at its close; identical at both, and unchanged from what
pass 3 recorded. HEAD is still `fdfb711f`. Dirty and not this cycle's: `KANBAN.html`, `KANBAN.md`,
`SECURITY.md`, `TODAY.md`, `docs/GLOSSARY.md`, `docs/spec-049-dependency_ci_hardening-0_0_14.md`,
`examples/fakeshop/db.sqlite3`, `uv.lock`. **Attributed semantically, not assumed:**
`git diff --stat -- docs/GLOSSARY.md` is `+2` lines and nothing else — the spec-049 dependency-floor
surface, no spec-001 term, no anchor this spec links to renamed. `AGENTS.md` rule 34: recorded, not
reverted, not edited. The only DB-touching command this pass ran is `import_spec_terms --check`, whose
`--check` branch returns before the writing transaction.

This cycle's own four paths are the only others dirty or untracked:
`docs/SPECS/spec-001-django_types-0_0_1.md` (M), and untracked
`docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md`,
`docs/builder/bld-001-r1-rationale_move.md`, `docs/builder/bld-001-r2-spec_reconciliation.md`,
`docs/builder/build-001-django_types-0_0_1.md`.

### DRY check against prior accepted items

R1 and R2 are the only completed items and neither lands source, so there is no cross-item code
duplication to find. The document-level DRY question — *a fact told twice across the spec and its
rationale sibling goes stale in one of them* — is answered under `### Division of labour` above: the
dangerous direction (contract leaving the spec) is clean, one deliberate exception is on record with its
reason, and four measured pure-restatement runs are recorded as accepted rather than silently carried.
**No new duplication, so no DRY finding blocks acceptance.**

### Failability proofs

None; this pass introduced no boundary, guard, gate, or rejection path. It writes no executable code, so
`BUILD.md` `### What needs a proof` is vacuous here rather than waived, and there is no fail-open shape
to read for in a diff of two Markdown sentences.

### Hot-path budget

Not applicable; the plan declares `Hot-path declaration: none`, and no residual item runs per request,
per resolver, per row, per connection, or per outbound message. Absence of a number is correct here, not
a finding — the cycle facts say so explicitly.

### Floor verification

Not applicable; the plan declares `Floor-verification scope: none`. No pass in this item was assigned a
floor run, so there is no unrun floor claim for this gate to close over. The build-wide statement for
`bld-001-final.md` is therefore `No floor-verification scope declared.`

### Summary

Item R2 reconciled `docs/SPECS/spec-001-django_types-0_0_1.md` against the shipped package at `0.0.14`,
fifty-odd specs after the spec was written. Every claim HEAD falsified is now either restated as the
contract that holds or replaced by a pointer to the spec that took the surface; every explanation of
every change lives in `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md` and nowhere else. All
eighteen drift rows are discharged — fifteen from the plan's verified floor, three the pass found itself
by reading the spec end to end rather than working the table, of which `DurationField` / `BinaryField`
is the most consumer-visible: the spec promised GraphQL mappings for two column types that in fact fail
closed at schema build. Five illustrative code blocks that had each become a stale second copy of a
module were deleted behind symbol-qualified pointers, two of them naming a `registry.lazy_ref` the
registry has never had. `## Current state` — a heading no shipped spec can keep — became `## Prior art`,
and its six glossary anchors were re-sited into contract prose without the anchor budget ever dropping
below one link. Two optimizer rules that the lift to `spec-002` would have left stated in no document
were restored as contract, re-derived against `optimizer/walker.py` rather than restored verbatim,
which caught a sentence that was false at HEAD. The spec is **7,745 bytes smaller than at HEAD
(-14.80%)** while saying more that is true, and the rationale carries the whole 62KB of explanation that
every future spawn no longer pays for.

Three build passes and three reviews closed nine, three, and zero findings respectively. This gate found
one further defect, in the one place the process had no eye on it: a placement rule and an inventory in
different sections of the same document disagreeing about where `tests/test_registry.py` lives — a
contradiction belonging to no drift row, no finding, and no diff hunk, and therefore visible only to a
reader of the whole. Both files now read as one coherent contract plus one coherent record of why it
changed. **`final-accepted`.**

### Spec changes made (Worker 1 only)

**This pass: one spec change and two rationale changes**, counted off the numbered list below after
writing it.

**`docs/SPECS/spec-001-django_types-0_0_1.md`**

1. `## Testing strategy`, the placement sentence — *"live under `tests/types/` and `tests/optimizer/`,
   with the per-module inventory…"* -> *"live under `tests/types/` and `tests/optimizer/`, **plus
   `tests/test_registry.py` at the package-test root**, with the per-module inventory…"*. Reason: the
   end-to-end read found the rule contradicted by `## Files to add`'s own inventory two sections later,
   which lists `tests/test_registry.py`; the file exists at HEAD, so the rule was false as well as
   internally inconsistent. Both sentences are R2's own new text, so this is a defect the reconciliation
   introduced on D10's axis.

**`docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md`** (Worker 1's file; these record this
pass's own spec edit and correct this pass's predecessors' prose, never moved spec text)

2. ``### `## Testing strategy``` — new *Corrected again* paragraph recording edit 1: what the first
   replacement said, which inventory falsifies it, why a rule the same document contradicts is worse
   than the rule it replaced, and that it was found by reading end to end rather than section by
   section. Reason: edit 1's derivation must be recoverable by a later reader, and the rationale is
   where a superseded correction is legal.
3. `### `## Current state` -> `## Prior art`` — *"Its two surviving paragraphs are a prior-art survey"*
   re-formed to name what survives (the example-project fixture and the two-library survey) and to state
   why all of it is prior art in the sense the heading claims. Reason: the section carries **three**
   paragraphs, not two, so the count was wrong in a standing doc; and by counting the first paragraph
   out of existence the entry never made the argument that justifies the retitle. Fixed by re-forming,
   not re-numbering — the third time this item has taken that remedy.

**Across the whole item.** Pass 1's spec changes are recorded by heading in its
`### What changed, by spec heading` (17 headings) and its rationale changes in `### Files touched`;
pass 2 records **5** spec and **8** rationale changes, pass 3 records **2** and **3**, this pass **1**
and **2**. Every one carries its own one-line reason at its own entry, and this gate re-read all of them
against the diff rather than re-listing them here — a fourth copy of thirteen numbered reasons would be
the duplication this item exists to remove.

**Checklist box left open, with its deferral reason** (`BUILD.md` `### Dispatched findings checklist`,
carried into this gate): **D13** is `- [ ]`. **No work is deferred and no target is owed one.** The row's
contract — that the spec no longer claims fakeshop declares no M2M field — was discharged by **R1's
rationale move**, not by R2's diff, and the box records that rather than claiming this cycle's diff did
it. The durable record is the rationale's `### Drift rows that changed nothing, and why`; confirmed
present, and confirmed to carry the HEAD evidence, this pass.

### Notes for Worker 1 (spec reconciliation)

Carried into R3 and the final gate. Items 1-2 are work R3 must schedule; items 3-4 are for the final
gate's `### Deferred work catalog`; items 5-9 are constraints and facts R3 must not lose. Nothing is
escalated — every finding in item R2 is closed inside R2's own writable set.

1. **`spec-002` lines 9 and 80 are open, and both belong to R3's Worker 1 pass — not its Worker 2.**
   Re-read both this pass and re-confirmed open; `git status` carries no `spec-002` entry.
   `docs/SPECS/spec-002-optimizer-0_0_2.md` is a **spec file**, and `worker-1.md` `## Scope` plus
   `BUILD.md` `## Spec reconciliation` make Worker 1 the only role that may mutate one. R3 has real
   Worker 2 work, so this is the assignment that gets mis-routed if it is not stated: **route it to
   Worker 1.** The operative wording, quoted so R3 need not re-derive it:
   - **Line 9**, `## Problem statement`, first sentence: *"`spec-001-django_types-0_0_1.md` predicted
     that the optimizer half of its scope would eventually warrant its own document; running the early
     DjangoType slice tests confirmed it."* The prediction it cites is the spec's own cut-line
     paragraph, which **R1 moved**. It now lives only in
     `appx/spec-001-django_types-0_0_1-rationale.md`, under
     `### Whole-document scope — the optimizer was bundled deliberately (former `## Scope creep into the N+1 problem`)`,
     in the paragraph *"The cut line the spec named for itself, and then took"*.
   - **Line 80**, `## References`, last bullet: *"The visibility-leak / `Prefetch` downgrade discussion
     that motivated bundling the optimizer with `spec-001-django_types-0_0_1.md` originally: issue #572
     and PR #583 on `strawberry-graphql/strawberry-django`."* The bundling discussion is in the same
     rationale entry, under *"Alternative rejected — two specs in lockstep"*.
   - **Minimum discharge for both is a pointer naming the rationale file, not new narration.** A
     sentence pointing at text that is not where it says it is, is the defect; a pointer that resolves
     closes it. Neither reference is wrong about spec-001 — both are wrong about *where the cited text
     lives* — so rewriting the surrounding prose is out of scope.
   - **The third obligation is CLOSED and R3 must not re-open it as a rule-stating duty.** Both optimizer
     rules R2 lifted are now contract in spec-001's `## N+1 strategy`. What remains is optional: a
     *recording* that the prose lift happened, natural site spec-002's own heading
     ``## Coordination with `spec-001-django_types-0_0_1.md``. Since R3's Worker 1 pass is opening that
     file for items above anyway, folding it in there is cheaper than a fourth pass.
   - **If any later cycle re-homes those two rules into `spec-002`, it must re-home the PR #583 carve-out
     with them and delete all three from spec-001 in the same change.** Those three are one decision;
     splitting them recreates the duplication this item exists to remove. Durable record: the rationale's
     ``### `## N+1 strategy``` entry, in bold. Re-confirmed present this pass.

2. **R3's durable-doc audit must check `README.md` and `TODAY.md` for a stale `DurationField` /
   `BinaryField` promise.** Seconded by every pass in this item and now a fifth time. Both column types
   raise `ConfigurationError` on any model that declares one; `docs/GLOSSARY.md` and
   `types/converters.py`'s module docstring both state it correctly; `README.md` and `TODAY.md` have
   **never been checked by any pass in this cycle**. This is the one consumer-visible fact R2 corrected
   that could still be wrong in a doc a consumer actually reads. If a stale promise is there, note that
   `TODAY.md` is currently dirty from the concurrent spec-049 session (`AGENTS.md` rule 34) — attribute
   before editing, and re-measure at R3's start.

3. **For the final gate's `### Deferred work catalog`: the optimizer-hint test-surface gap.** No
   permanent test pins that `OptimizerHint.prefetch(obj)` uses the consumer's queryset **verbatim** when
   the target type declares a custom `get_queryset` — i.e. that the hinted prefetch child bypasses
   `utils/querysets.py::apply_type_visibility_sync`. Re-confirmed by Worker 3 in pass 3:
   `tests/optimizer/test_hints.py` never mentions `get_queryset`, and the eight `prefetch_obj` rows in
   `tests/optimizer/test_walker.py` pin inner-selection suppression, connector columns, prefix rebasing,
   non-cacheability, dedupe, and the misconfigured-lookup clean-plan path — none pins the visibility
   interaction in either direction. The behaviour is **deliberate**
   (`optimizer/walker.py::_apply_hint` #"Consumer-supplied Prefetch objects commonly close over"), which
   is precisely why a row asserting it is cheap insurance against a future refactor "fixing" it silently
   — an unpinned deliberate divergence in a data-isolation path is indistinguishable from a bug to the
   next reader. **Out of this cycle's write set** (the plan's build-wide context flags forbid any source
   or test change), so it is a deferral for the next optimizer cycle and a maintainer call, never a
   spec-001 item. Worker 3's evidence is
   `docs/builder/temp-tests/r2b2-spec001/test_hint_visibility.py` (gitignored; two rows, one a positive
   control).

4. **Also for the catalog: a fifth hand-written link / anchor / overlap checker.** R1, R2 pass 1, and all
   three review passes each wrote their own; this pass wrote a sixth inline. Every spec-plus-rationale
   pair from here on owes exactly these checks (link scaffold, positional group-header order,
   alphabetical order, undefined / orphan defs, on-disk def targets with the fragment stripped, in-page
   anchors on a slugger that **renders** reference-link markup before slugging, inline-link sweep, rule-27
   sweep). Promoting it to `scripts/` is new scope and a maintainer call, not R3's.

5. **The anchor constraint for R3 is unchanged: 21 distinct anchors / 22 body links**, `configurationerror`
   the only anchor with two, every other glossary-linked sentence its anchor's sole link. Re-measured at
   this pass's close. R3 touches no spec-001 prose by its own scope, but it **does** edit `spec-002`, and
   any spec-001 change it makes for any reason re-owes both constraint commands.

6. **`import_spec_terms --check` reads `OK: 49 done cards`, exit 0.** The number is the concurrent
   session's `DONE-049-0.0.14` wrap, not this cycle's; **exit 0 is the contract**. A later pass that
   quotes the plan's `48` and sees `49` will waste time deciding whether it broke something.

7. **Re-measure `git status` at R3's start.** It has moved in both directions during this cycle while
   HEAD stayed at `fdfb711f`; it was identical at this pass's open and close, which is itself only a
   snapshot. Four of the files R3's durable-doc audit reads — `KANBAN.md`, `KANBAN.html`,
   `docs/GLOSSARY.md`, `examples/fakeshop/db.sqlite3` — are dirty from the concurrent card wrap, so **R3
   may not read a dirty generated doc as evidence of spec-001 drift.** Attribute semantically first:
   `docs/GLOSSARY.md`'s current diff is exactly `+2` lines on the dependency-floor surface.

8. **The `github_anchor` false negative is a standing trap, not a closed finding.**
   `scripts/check_spec_glossary.py::github_anchor` fed the raw heading
   `## [Scalar field conversion][glossary-scalar-field-conversion]` returns
   `scalar-field-conversionglossary-scalar-field-conversion`, because it strips brackets as non-word
   characters instead of rendering the link. Strip link markup **first**, then slug. Three consecutive
   passes copied the broken method before it was caught; the function itself is unchanged, so the next
   pass that reaches for it gets the same false negative.

9. **The lesson this gate adds, for whoever reconciles the next spec.** A reconciliation working from a
   drift table corrects **claims**; a contradiction between two *sections* answers to no claim and no
   row, so no pass organized around the table can see it — and neither can a review that audits the same
   fragments. **Read the whole document once, in order, at the end.** It cost one pass and found a defect
   three builds and three reviews had each looked straight past, in text they had themselves written.

### Final verification outcome

`final-accepted`. Every `- [x]` in the `### Dispatched findings checklist` is confirmed landed in the
diff, no box is over-ticked, and the one open box carries a durable reason in a tracked file. The spec's
opening lines still describe the build's state. The end-to-end read found one real defect and one wrong
count in a standing doc, both fixed inside R2's own writable set and both recorded above. Both constraint
commands, the layout check, and `git diff --check` are green after the last edit; the anchor budget, link
scaffold, in-page anchors, and rule-27 sweep are all unchanged and exact. The two documents divide the
labour the maintainer asked for: the spec states the contract, the rationale states why it changed and
what it may no longer claim, and neither restates the other beyond one deliberate, recorded exception.

Item R2 is complete. Worker 0 may mark the plan's R2 box and dispatch R3's planning pass.
