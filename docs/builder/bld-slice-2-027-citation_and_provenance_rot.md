# Build: Slice 2 — Citation and provenance rot in `.py` files

Spec reference: `docs/SPECS/spec-027-filters-0_0_8.md` (whole file; this slice edits no spec text — it retires code citations that point INTO the spec)
Status: final-accepted

## Plan (Worker 1)

### What this slice is

Comment and docstring text only, across 19 `.py` files. **No executable statement changes.** Three defect classes, all citation / provenance rot in the filtering card's owned surface:

- **D12** — the pre-renumber card id (`spec-021`, `DONE-021-0.0.8`) still names this card.
- **D13** — raw spec line numbers in comments and docstrings, forbidden by [`AGENTS.md`][agents] rule 27 and already rotted.
- **D14** — build-process provenance (review-round ids, finding ids) in comments, plus one mangled docstring.

The build plan [`build-027-filters-0_0_8.md`][build-027] `## Pre-dispatch verification` states each finding's population. **Every population below was re-derived against `HEAD` during this planning pass and every one of the three counts was wrong in the brief.** The corrected counts, their causes, and the per-site inventory are the contract; the brief's numbers are superseded.

### Spec status-line re-verification (Worker 1, every spawn)

`docs/SPECS/spec-027-filters-0_0_8.md` lines 1-9 were read at the start of this pass. The `Status:` line is still the single build-progress paragraph that opens `in progress` and narrates Slices 1-3 / 4 / 4a / 5 / 6 as they landed — falsified by the card being `DONE-027-0.0.8`. **No edit made, and none is owed by this pass:** build-plan finding D2 assigns it to Slice 3, Slice 1 already recorded it as deliberately left standing, and this cycle's brief fences Slice 2 out of both the spec and the rationale. The `Target release`, `Owner`, and `Predecessors` lines are accurate, and the rationale-companion pointer Slice 1 added resolves. Recorded here so the re-verification is on disk rather than assumed.

### Re-derived populations (this is the contract, not the brief's numbers)

| Finding | Brief said | Re-derived | Cause of the gap |
|---|---|---|---|
| D12 | 27 occurrences / 9 files | **30 occurrences / 12 files** | 27 `spec-021` confirmed exactly. Three further prose citations spell the card id as `DONE-021-0.0.8` in files the brief did not name. |
| D13 | 11 occurrences / 4 files | **17 occurrences / 6 files** | Two citations WRAP across a line break (`spec-021\n    line 665`) and are invisible to a single-line grep; two `filters/inputs.py` sites and two shared-substrate sites were outside the brief's file list. |
| D14 | 3 occurrences / 3 files | **20 occurrences at 19 sites / 6 files** (+ 1 mangled docstring) | Two separate vocabulary gaps. (a) The brief swept `round-N` / `Finding N` only; review-**finding** ids in the `H<n>` / `M<n>` form (`Decision 4 M6`, `Decision 4 M1`, `Decision 4 M5`, `Decision 4 H1`, `the H3 bug`) are the same defect and outnumber the round-N form. (b) **My own first sweep was case-sensitive on `Finding` and missed four LOWERCASE ids** (`(finding 3)` twice and `(finding 1)` in `filters/sets.py`, `(finding 1)` in `tests/filters/test_sets.py`). One line, `filters/base.py:253`, carries two tokens — hence 20 occurrences at 19 sites. |

**Two instrument lessons are baked into the scan below; do not re-run a narrower one.** A citation wrapped across a line break is invisible to `grep -n`, and a case-sensitive `Finding` pattern misses the lowercase spelling of the same id. Both under-counted a population during this planning pass — the second one under-counted a population **I had just re-derived myself**.

**The line-wrap hazard is the load-bearing one.** `grep -n 'spec-021 line'` returns 3 hits in `tests/filters/test_finalizer.py`; the file carries 5. The two it misses are a citation split by the docstring's own wrap. Every re-derivation in this plan, and every post-fix count Worker 2 owes, therefore runs against whitespace-flattened text, never `grep -n` alone.

**A second consequence, and the reason it matters here more than usual:** this slice DELETES text from prose lines, so several lines get shorter and want re-wrapping. `ruff format` does not reflow comments or docstrings, so the re-wrap is Worker 2's by hand — and a hand re-wrap is exactly what creates a wrapped citation. See `### Implementation steps` step 6.

### Verified: no hit belongs to `spec-021-apps-0_0_7`

All 27 `spec-021` occurrences were read individually in context. Every one sits in filtering prose: `FilterSet` declarations, `Meta.filterset_class` resolution, Layer-2 `RelatedFilter` resolution, the live filter HTTP tests, and the `Meta.filterset_class` promotion gate (which is **spec-027 Decision 7**, confirmed by reading `docs/SPECS/spec-027-filters-0_0_8.md` heading `### Decision 7 — Meta.filterset_class promotion gate`). None means `docs/SPECS/spec-021-apps-0_0_7.md`, the Django `AppConfig` card. **Every one of the 27 is rewritten.**

### Scope boundary (state this rule before touching anything)

The boundary that decides in-scope from out-of-scope is **which card the citation names**, not which directory the file sits in:

- **In scope** — a citation naming THIS card (`spec-021` meaning the filtering card, `DONE-021-0.0.8`, `spec-027`), or build-process provenance inside a filtering-card-owned file (`django_strawberry_framework/filters/`, `tests/filters/`, `examples/fakeshop/apps/library/filters*.py`). This is why `django_strawberry_framework/utils/inputs.py` #"Spec-027 line 247" is IN scope even though `utils/` is the shared substrate serving both `filters/` and `orders/`: the citation is to spec-027, and Slice 1 already renumbered the spec it points into.
- **Out of scope** — a citation naming a DIFFERENT card's spec, wherever it lives. Recorded below for the deferred-work catalog, never fixed here.

### Out of scope — record, do not fix

Worker 2 must NOT touch any of these. They are listed so Worker 1's `### Deferred work catalog` at the final gate can carry them, and so their survival in a post-fix sweep is not read as an unfinished contract.

| Site | What it is | Why out of scope |
|---|---|---|
| `django_strawberry_framework/mutations/inputs.py` #"spec-036 L3-1" (2 occurrences, at the `_is_decodable_fk` docstring and its lead-in comment) | Same defect class — a review-finding id / raw ref | Names **spec-036**, the mutations card. A different card's files. |
| `django_strawberry_framework/orders/inputs.py` (`spec-028 Decision 3 line 452`, `Spec Edge cases line 980`), `orders/sets.py` (4 cookbook `lines NN-MM` refs), `orders/factories.py` #"Decision 4 H1" | D13 / D14 defect class | Names **spec-028** (orders) or upstream cookbook line numbers. Different card. |
| `django_strawberry_framework/rest_framework/*.py` (`H3`/`H4`/`H5`/`M2`/`M3`), `forms/inputs.py` #"M3", `mutations/{resolvers,sets}.py` #"M3", `connection.py` #"M1", `types/base.py` #"the H1 collision guard", `_strawberry_patches.py` (`L45`/`L52`) | D14 defect class | Other cards' owned files. |
| `tests/forms/`, `tests/mutations/`, `tests/rest_framework/`, `tests/optimizer/`, `tests/orders/`, `tests/test_views.py`, `tests/test_relay_connection.py` `Finding N` / `line NN` refs | D13 / D14 defect class | Other cards' test trees. |
| `examples/fakeshop/test_query/test_library_api.py` #"Spec line 1038" and #"spec line\n    1039" (in `test_root_get_queryset_runs_before_order_apply`) | Raw spec line refs | The enclosing docstring opens `Spec-028 test plan`. These are **spec-028** refs that happen to live in a file this slice edits. Leave them. |
| `examples/fakeshop/test_query/test_kanban_api.py` — 5 occurrences of `DONE-021-0.0.8` (lines ~169, ~186, ~558, ~687, ~1261) | Looks like D12 | **Test fixture DATA, not a citation.** The string is a `raw_text=` value the test itself creates on a `CardReference` / `BoardDocCardReference` row plus the assertions that read it back; it exercises the card-reference parser and means nothing about this card. Rewriting it is meaningless churn, and rewriting only half of a create/assert pair breaks the test. |

### The 19 writable files (the complete list; nothing else may be edited)

| # | File | D12 | D13 | D14 | Other |
|---|---|---|---|---|---|
| 1 | `django_strawberry_framework/filters/base.py` | - | - | 4 (3 sites) | - |
| 2 | `django_strawberry_framework/filters/factories.py` | - | 1 | 1 (same site) | - |
| 3 | `django_strawberry_framework/filters/inputs.py` | - | 4 | 4 (1 site shared with D13) | - |
| 4 | `django_strawberry_framework/filters/sets.py` | - | 5 | 5 | - |
| 5 | `django_strawberry_framework/utils/inputs.py` | - | 1 | - | - |
| 6 | `tests/filters/test_factories.py` | - | 1 | - | - |
| 7 | `tests/filters/test_finalizer.py` | 5 | 5 (same 5 sites) | - | - |
| 8 | `tests/filters/test_inputs.py` | 1 | - | 1 (different site) | - |
| 9 | `tests/filters/test_sets.py` | - | - | 5 | - |
| 10 | `tests/types/test_base.py` | 1 | - | - | - |
| 11 | `tests/types/test_definition_order.py` | 1 | - | - | mangled docstring (same site) |
| 12 | `tests/types/fixtures/shelf_module.py` | 1 | - | - | - |
| 13 | `tests/types/fixtures/branch_module.py` | 1 | - | - | - |
| 14 | `examples/fakeshop/apps/library/filters.py` | 4 | - | - | - |
| 15 | `examples/fakeshop/apps/library/filters_genre.py` | 1 | - | - | - |
| 16 | `examples/fakeshop/test_query/test_library_api.py` | 12 | - | - | - |
| 17 | `examples/fakeshop/apps/products/filters.py` | 1 (`DONE-021`) | - | - | - |
| 18 | `examples/fakeshop/apps/kanban/filters.py` | 1 (`DONE-021`) | - | - | - |
| 19 | `examples/fakeshop/test_query/test_products_api.py` | 1 (`DONE-021`) | - | - | - |
| | **Totals** | **30** | **17** | **20 / 19 sites** | 1 |

Overlaps are real, not double-counting: 5 sites are both D12 and D13; 2 sites are both D13 and D14; 1 site is both D12 and the mangled docstring. Roughly **59 distinct edit sites** across the 19 files.

### DRY analysis

- **Helper inventory checked.** Deliberately skipped, and the skip is the honest record rather than a claim: `worker-1.md` `### Package-wide helper inventory before helper planning` gates *helper planning*, and this slice proposes **no** helper, shared constant, validation branch, coercion utility, or test helper — it changes no executable statement in any of the 19 files. Nothing exists for the inventory to prevent. The condition that would reverse this: any site whose repair needs a code change rather than a text change, which Worker 2 must escalate under `### Implementation discretion items` rather than write.
- **Existing patterns reused.** The replacement vocabulary is not invented here. Three forms already used correctly elsewhere in the package are reused verbatim in shape:
  - `spec-NNN Decision N` — already the dominant correct form (e.g. `django_strawberry_framework/mutations/inputs.py` #"spec-036 Decision 6", #"spec-036 Decision 7"). 66 `spec-027` occurrences already exist across 12 `.py` files, most in this form.
  - `path/to/file.py::QualifiedName` — the [`AGENTS.md`][agents] rule-27 symbol ref, gated by `scripts/check_citations.py` (737 citations resolve at `HEAD`).
  - Bare invariant prose with no pointer — the majority of `django_strawberry_framework/filters/base.py`'s own comments.
- **New helpers justified.** None.
- **Duplication risk avoided.** The characteristic failure of a mechanical citation sweep is a **half-applied** rewrite: some sites get `spec-027`, others get a Decision name, others get a symbol ref, and a later reader cannot tell which form is intended. The plan prevents it by fixing ONE form per defect class up front (`### Replacement rules`) and by giving a per-site table with the exact target text, so Worker 2 chooses nothing that this plan has not already decided.

### Replacement rules (decided here; Worker 2 applies, it does not choose)

Applied in this priority order at every site:

1. **A raw spec line number is DELETED, never renumbered.** Slices 1 and 3 renumber the whole spec, so any number written now is wrong twice over. Replace with a Decision reference **only when the Decision's body at `HEAD` was read and confirmed to state the cited contract** — the per-site table below records that confirmation for every site, so Worker 2 does not re-derive it.
2. **A review-round or finding id is DELETED** (`H1`, `M1`, `M5`, `M6`, `H3`, `round-3`, `round-6`, `Finding 1`, `Finding 2`). Slice 1 moved every one of these into `docs/SPECS/appx/spec-027-filters-0_0_8-rationale.md`, so at `HEAD` they resolve to nothing even inside the spec. Keep the **reason**, drop the **provenance**: the surviving sentence states the invariant that is true now, in the present tense, with no claim about how the code came to be.
3. **A citation that must survive becomes `spec-027`**, and where the reference is load-bearing enough to want a target, prefer a **symbol-qualified source ref** (`path::QualifiedName`, `path::QualifiedName #"unique substring"`, `path #"unique substring"`) over any `spec-NNN` reference. A symbol ref is gated by `scripts/check_citations.py`; a `spec-NNN` ref is gated by nothing.
4. **`spec-021` -> `spec-027` is byte-length-preserving.** Prefer the bare token swap wherever the sentence is otherwise correct — it cannot reflow a line and therefore cannot create a wrapped citation.
5. **ASCII only.** `scripts/check_trailing_commas.py` enforces ASCII-only `.py` source. Use `--` for a dash and straight quotes, matching the surrounding code. No em dash, no curly quote, no arrow glyph.
6. **Present tense, no history.** Never `now`, `no longer`, `previously`, `an earlier`, `corrected to`. A comment states the invariant as though it had always been true.

### Implementation steps

Line numbers are pin-at-write-time navigational hints, measured during this planning pass. Verify against the current source before editing — three concurrent sessions are working this tree.

1. **Baseline the focused test scope BEFORE any edit.** Run the exact command in `### Test additions / updates` and record its result in the build report. This is the only way to attribute a later failure: the fakeshop schema-registry cross-test pollution class is order-dependent and pre-existing, and `git stash` is forbidden in this tree, so a pre-edit baseline is the cheapest attribution instrument available.
2. **D12, the bulk swap (22 sites).** `spec-021` -> `spec-027` and `Spec-021` -> `Spec-027` at the 22 sites that carry no line number, per the table in `### Per-site inventory — D12`. Byte-length-preserving; no line can reflow.
3. **D12 + D13 combined (5 sites, `tests/filters/test_finalizer.py`).** These five sites carry BOTH tokens; rewrite each whole per the table in `### Per-site inventory — D13`. Two of them are the wrapped `spec-021\n    line 665` citations.
4. **D12 extension, the `DONE-021-0.0.8` prose citations (3 sites).** `DONE-021-0.0.8` -> `DONE-027-0.0.8` in `examples/fakeshop/apps/products/filters.py`, `examples/fakeshop/apps/kanban/filters.py`, `examples/fakeshop/test_query/test_products_api.py`. Also byte-length-preserving. **Do not touch `examples/fakeshop/test_query/test_kanban_api.py`** (out-of-scope table above).
5. **D13 remaining (12 sites) and D14 (15 sites)** per their tables. Two sites are simultaneously D13 and D14 (`filters/factories.py` #"Decision 4 H1 / spec-027 lines 579-584" and `filters/inputs.py` #"Decision 4 M5 (line 591)"); each is one edit, not two.
6. **Re-wrap by hand every prose line a deletion shortened.** `ruff format` does not reflow comments or docstrings, so a deletion leaves a ragged line the formatter will not fix. Two hard constraints on the re-wrap:
   - Line length 99 (E501 graced to 110 for lines the formatter cannot break). Every edited line stays within 99.
   - **A `path::Symbol` citation must never be split across a line break.** `scripts/check_citations.py` cannot see a wrapped citation, so a wrapped one is both unresolvable to a reader and invisible to the gate. If a citation does not fit, shorten the surrounding prose, never the citation.
7. **Repair the mangled docstring** in `tests/types/test_definition_order.py::test_filterset_class_resolves_across_module_boundary` per `### Per-site inventory — the mangled docstring`.
8. **Run the verification battery** in `### Verification Worker 2 owes`, including the re-derived post-fix counts.

### Per-site inventory — D12 (`spec-021` / `Spec-021`, 27 occurrences, 9 files)

Bare token swap `spec-021` -> `spec-027`, `Spec-021` -> `Spec-027`, unless the row says otherwise.

| File | Line (pin) | Current text fragment | Action |
|---|---|---|---|
| `examples/fakeshop/test_query/test_library_api.py` | 836 | `# Live HTTP filter coverage for the library FilterSet declarations (spec-021).` | swap |
| " | 861 | `"""Spec-021: scalar-field filter clause + ``iContains`` lookup name."""` | swap |
| " | 985 | `"""Spec-021: choice-enum filter clause coerces via Strawberry enum."""` | swap |
| " | 1048 | `"""Spec-021: ``ShelfType`` is non-Relay so ``shelf.id`` is a scalar PK."""` | swap |
| " | 1070 | `"""Spec-021: ``GenreType`` is Relay-Node so ``genres.id`` is a GlobalID."""` | swap |
| " | 1353 | `"""Spec-021: reverse-FK filter (``shelves.code``) routes through ``ShelfFilter``."""` | swap |
| " | 1357 | `# topic="permanent collection")`` constraint per spec-021 - seed both` | swap |
| " | 1385 | `"""Spec-021: ``and_`` / ``not_`` Python attrs surface as ``and`` / ``not``."""` | swap |
| " | 1423 | `"""Spec-021: ``select_related`` / ``prefetch_related`` survive ``.filter(...)``."""` | swap |
| " | 1464 | `# per spec-021.` | swap |
| " | 1474 | `"""Spec-021: ``RelatedFilter(queryset=...)`` scopes the parent only."""` | swap |
| " | 1505 | `"""Spec-021: ``BookFilter.genres`` resolves via the Layer-2 absolute path."""` | swap |
| `examples/fakeshop/apps/library/filters.py` | 1 | `"""FilterSet declarations for the library acceptance app (spec-021).` | swap |
| " | 10 | `(spec-021).` | swap |
| " | 81 | `spec-021.` (end of `BookFilter` docstring sentence) | swap |
| " | 143 | `# an ``@`` sign per spec-021.` | swap |
| `examples/fakeshop/apps/library/filters_genre.py` | 6 | `resolution per spec-021. The single same-module unqualified-name branch is` | swap |
| `tests/filters/test_inputs.py` | 1305 | `` `Meta.fields` traversal with no nested alternative (spec-021's intentional flat`` | swap |
| `tests/types/test_base.py` | 399 | `"""``Meta.filterset_class`` ships in spec-021 (Decision-7 promotion gate)."""` | swap. `Decision-7` is CORRECT and stays: spec-027's `### Decision 7 — Meta.filterset_class promotion gate` states exactly this. Normalize the spelling to `spec-027 Decision 7` so the file uses one form. |
| `tests/types/fixtures/shelf_module.py` | 4 | `` ``Meta.filterset_class`` resolution path under spec-021.`` | swap |
| `tests/types/fixtures/branch_module.py` | 5 | `` ``Meta.filterset_class`` resolution path under spec-021.`` | swap |
| `tests/types/test_definition_order.py` | 1447 | `after the autouse-fixture ``registry.clear()``. Pins spec-021` | handled by the mangled-docstring repair below, not by a bare swap |
| `tests/filters/test_finalizer.py` | 18, 314, 333, 395, 798 | five sites carrying both a `spec-021` token and a raw line number | handled in the D13 table |

**D12 extension — `DONE-021-0.0.8` prose citations (3 occurrences, 3 files).** Swap to `DONE-027-0.0.8` (byte-length-preserving):

| File | Line (pin) | Current text fragment |
|---|---|---|
| `examples/fakeshop/apps/products/filters.py` | 29 | ``(``DONE-021-0.0.8``) per-field permission gate; the permissions subsystem`` |
| `examples/fakeshop/apps/kanban/filters.py` | 7 | ``tree -- it exercises the cross-relation filter path from ``DONE-021-0.0.8`` far`` |
| `examples/fakeshop/test_query/test_products_api.py` | 9 | ``  ``DONE-021-0.0.8`` filter permission hook) -- including the regression`` |

### Per-site inventory — D13 (raw spec line numbers, 17 occurrences, 6 files)

Each row's **Decision target was confirmed by reading that Decision's body in `docs/SPECS/spec-027-filters-0_0_8.md` at `HEAD`.** Worker 2 applies the text; it does not need to re-derive the mapping.

| File | Line (pin) | Current | Replace with | Confirmation |
|---|---|---|---|---|
| `filters/inputs.py` | 294 | `Per spec-027 Decision 4 M5 (line 591), a ``ChoiceFilter`` whose source` | `Per spec-027 Decision 4, a ``ChoiceFilter`` whose source` | Decision 4's converter table row for `ChoiceFilter` states the `ConfigurationError` for a non-`Choices` source. Also a D14 site (`M5`). |
| `filters/inputs.py` | 461 | `# unknown form-field shape raises per spec-027 line 595.` | `# unknown form-field shape raises per spec-027 Decision 4.` | Decision 4's converter table row for `Filter(method=<callable>)`: "if the form field is unknown, raises `ConfigurationError` naming the filter and method". |
| `filters/inputs.py` | 592 | `target GraphQL type (spec-027 L603) before any queryset clause runs.` | `target GraphQL type (spec-027 Decision 4) before any queryset clause runs.` | Decision 4's "Strawberry-specific `GlobalIDFilter`" block pins the `type_name` validation before any queryset clause. |
| `filters/inputs.py` | 688 | `Per spec-027 Decision 4 line 594: Django's ``RangeWidget.value_from_datadict``` | `Per spec-027 Decision 4: Django's ``RangeWidget.value_from_datadict``` | Decision 4's converter table row for `RangeFilter` pins the positional `name_0` / `name_1` keys explicitly. |
| `filters/sets.py` | 1524 | `Own-PK branch (spec-027 L566-567 + L607): when ``field`` is the` | `Own-PK branch (spec-027 Decision 4): when ``field`` is the` | Decision 4's first bullet covers "FK / **PK** whose owning `FilterSet`'s target `DjangoType` ... implements `relay.Node` -> `GlobalIDFilter`". |
| `filters/sets.py` | 1855 | `(own-PK branch per spec-027 L566-567). For relation fields a` | `(own-PK branch per spec-027 Decision 4). For relation fields a` | same as above |
| `filters/sets.py` | 1989 | `Own-PK branch per spec-027 L566-567 + L607: when a ``FilterSet``` | `Own-PK branch per spec-027 Decision 4: when a ``FilterSet``` | same as above |
| `filters/sets.py` | 2217 | `# Per spec-027 L518-605 (per-field operator bag), top-` | `# Per spec-027 Decision 3 Layer 5 (per-field operator bag), top-` | Decision 3's Layer 5 is the BFS schema build that produces the per-field operator-bag input classes. |
| `filters/sets.py` | 2465 | ```` ``<rel>__in=<intersected>`` clause is computed (spec-027 L668-678).```` | ```` ``<rel>__in=<intersected>`` clause is computed (spec-027 Decision 8).```` | Decision 8 steps 3 and 4a pin exactly this ordering ("the join's right-hand side is the visibility-scoped child queryset"). |
| `filters/factories.py` | 23 | `(Decision 4 H1 / spec-027 lines 579-584). The finalizer materializes the` | `(spec-027 Decision 4). The finalizer materializes the` | Decision 4's "Where the conditional runs" block states the `FILTER_DEFAULTS`-on-`FilterSet`-not-factory rule. Also a D14 site (`H1`). |
| `utils/inputs.py` | 775 | `call. Spec-027 line 247 explicitly drops the ``replace_csv_filters`` rewrap` | `call. Spec-027 explicitly drops the ``replace_csv_filters`` rewrap` | The statement lives in the spec's `### Explicitly do not borrow` section, NOT in any Decision — so there is no Decision to name. Drop the pointer to a bare `spec-027`; the following clause already gives the reason ("Strawberry's typed input handles `list[T]` natively"). |
| `tests/filters/test_factories.py` | 531 | `"""Per spec line 247, the cookbook's ``replace_csv_filters`` rewrap is dropped.` | `"""The cookbook's ``replace_csv_filters`` rewrap is dropped per spec-027.` | Same statement, same section. Also normalizes the bare `spec` to the card id. |
| `tests/filters/test_finalizer.py` | 18 | `contract per spec-021 line 822).` | `contract per spec-027 Decision 9).` | Decision 9 is `Input-class namespace vs TypeRegistry and lifecycle` and owns the cycle-safe `registry.clear()` integration. |
| `tests/filters/test_finalizer.py` | 314 | `(per spec-021 line 1030's companion to` + next line `` ``test_phase_2_5_rejects_multi_owner_with_diverging_pk_identity``). `` | `(the companion to` + `` `tests/filters/test_finalizer.py::test_phase_2_5_rejects_multi_owner_with_diverging_pk_identity`). `` | Symbol ref preferred over any spec ref per rule 3. **Verified: that test is defined at `tests/filters/test_finalizer.py:158`.** Keep the whole `path::Symbol` on one line. |
| `tests/filters/test_finalizer.py` | 333-334 | `` ``_owner_definition`` slot stores the FIRST binding per spec-021 `` / `` line 665.`` (WRAPPED) | `` ``_owner_definition`` slot stores the FIRST binding (`django_strawberry_framework/types/finalizer.py::_bind_filterset_owner`).`` | **Verified: `_bind_filterset_owner` is defined at `django_strawberry_framework/types/finalizer.py:1220`.** The spec states the rule in Decision 6 subpass 2 ("the owner slot stores the FIRST binding"), but the symbol ref is the gated form and names where the behavior lives. Keep the citation on one line. |
| `tests/filters/test_finalizer.py` | 395-396 | same wrapped citation, in a `#` comment | same replacement | as above |
| `tests/filters/test_finalizer.py` | 798 | `spec-021 lines 416 + 1030 and the package's "finalize-time errors` | `spec-027 Decision 3 Layer 2 and the package's "finalize-time errors` | Decision 3's Layer 2 is `LazyRelatedClassMixin.resolve_lazy_class`, the `ImportError` source this sentence re-wraps. |

### Per-site inventory — D14 (build-process provenance, 20 occurrences at 19 sites, 6 files)

| File | Line (pin) | Current | Replace with |
|---|---|---|---|
| `filters/base.py` | 13 | `` `strawberry.relay.GlobalID.from_id(value)` per Decision 4 M6.`` | `` `strawberry.relay.GlobalID.from_id(value)` per spec-027 Decision 4.`` |
| `filters/base.py` | 251-253 | `Sharing the derivation keeps the two siblings from drifting apart the way an earlier per-method copy let the empty-``node_id`` guard reach only one of them (round-6 Finding 1).` | `Sharing the derivation keeps the two siblings from drifting apart: a per-method copy would let the empty-``node_id`` guard reach only one of them.` — drops the finding id AND the historical claim, keeps the reason. Re-wrap the whole sentence. |
| `filters/base.py` | 687 | `per spec-027 Decision 4 M6. The Graphene-only` | `per spec-027 Decision 4. The Graphene-only` |
| `filters/factories.py` | 23 | `(Decision 4 H1 / spec-027 lines 579-584)` | `(spec-027 Decision 4)` — same edit as the D13 row; one edit, not two |
| `filters/inputs.py` | 260 | `# table at spec-027 Decision 4 M1 lists CharField as a recognized` | `# table in spec-027 Decision 4 lists CharField as a recognized` |
| `filters/inputs.py` | 294 | `Per spec-027 Decision 4 M5 (line 591),` | `Per spec-027 Decision 4,` — same edit as the D13 row; one edit, not two |
| `filters/inputs.py` | 411 | `Implements the Decision-4 M1 conversion table. Kind order is` | `Implements the spec-027 Decision 4 conversion table. Kind order is` |
| `filters/inputs.py` | 870-871 | `` # operator-bag leaf is optional (``optional_field_kwargs`` - the`` / `# Finding 2 required-by-default rule).` | `` # operator-bag leaf is optional (``optional_field_kwargs``); an`` / `# omitted ``default`` would build a REQUIRED field.` |
| `filters/sets.py` | 921 | ```` ``registry.clear()`` resets filters and metadata together (finding 3). It is```` | ```` ``registry.clear()`` resets filters and metadata together. It is```` |
| `filters/sets.py` | 951 | `a non-model path (finding 1 -- a declared field_name must never turn a` / `working declaration into a finalization failure).` | `a non-model path (a declared ``field_name`` must never turn a` / `working declaration into a finalization failure).` — drops the id, keeps the reason |
| `filters/sets.py` | 1203 | `# cache so filters + metadata reset together (finding 3).` | `# cache so filters + metadata reset together.` |
| `filters/sets.py` | 1674 | `` # rebased relation path instead of a stale ``"target__pk"`` (Finding 2). The`` | `` # rebased relation path instead of a stale ``"target__pk"``. The`` |
| `filters/sets.py` | 3439-3440 | `message consumers can match on. Class-based dispatch closes the` / `round-3 loop: no substring-matching against a constant string.` | `message consumers can match on. Class-based dispatch, not` / `substring-matching against a constant string.` (the brief's exact guidance — keep the reason, drop the round id) |
| `tests/filters/test_inputs.py` | 158-159 | `Each carries an explicit ``default=None`` so it stays OPTIONAL under the` / `Finding 2 rule that an omitted ``default`` now builds a REQUIRED field.` | `Each carries an explicit ``default=None`` so it stays OPTIONAL: an` / `omitted ``default`` builds a REQUIRED field.` (drops the finding id and the tense-marker `now`) |
| `tests/filters/test_sets.py` | 747 | `"""Finding 2: an expanded ``to_field`` GlobalID leaf compiles against the rebased path.` | `"""An expanded ``to_field`` GlobalID leaf compiles against the rebased path.` |
| `tests/filters/test_sets.py` | 6127 | `# permitted non-model declared prefixes (finding 1): their expanded,` | `# permitted non-model declared prefixes: their expanded,` |
| `tests/filters/test_sets.py` | 4567-4568 | `` # / ``.type_cls`` (the H3 bug read those nonexistent attrs and`` / `# dropped every owner-aware resolution to the registry fallback).` | `` # / ``.type_cls``; reading those nonexistent attrs would drop`` / `# every owner-aware resolution to the registry fallback.` |
| `tests/filters/test_sets.py` | 6833 | `# Finding 1 - capability travels through the RelatedFilter EXPANSION boundary.` | `# Capability travels through the RelatedFilter EXPANSION boundary.` |
| `tests/filters/test_sets.py` | 6871 | `Finding 1: a CHILD ``FilterSet`` overriding ``filter_for_lookup`` (so the` | `A CHILD ``FilterSet`` overriding ``filter_for_lookup`` (so the` |

**Note on `tests/filters/test_sets.py`'s four sites.** Their `Finding N` / `H3` ids may originate in a LATER card's review round (the capability-gate work) rather than spec-027's. That does not change the disposition: the defect is that a review-round id resolves to nothing for a future reader, the files are this card's owned test tree, and the repair is identical either way. They are in scope on the file-ownership half of the scope boundary, not the citation half.

### Per-site inventory — the mangled docstring

`tests/types/test_definition_order.py::test_filterset_class_resolves_across_module_boundary`, lines ~1447-1449. Current, verbatim:

```text
    after the autouse-fixture ``registry.clear()``. Pins spec-021
    The contract that the finalizer's filter-binding pass works
    across module boundaries without ``ImportError``.
```

`Pins spec-021` and `The contract that ...` are two halves of one sentence that a half-applied edit split. Replace the three lines with one coherent sentence:

```text
    after the autouse-fixture ``registry.clear()``. Pins the spec-027
    contract that the finalizer's filter-binding pass works across
    module boundaries without ``ImportError``.
```

This discharges the `spec-021` occurrence at line 1447 and the mangled sentence in one edit.

### Test additions / updates

**No test is added, changed in behavior, or renamed.** Nine of the nineteen files are test modules, but every edit in them is docstring or comment text; no assertion, fixture, parametrization, or node id moves.

The focused scope, run **twice** — once as a pre-edit baseline (implementation step 1) and once after the edits:

```shell
uv run pytest tests/filters/ tests/types/test_base.py tests/types/test_definition_order.py \
  examples/fakeshop/test_query/test_library_api.py \
  examples/fakeshop/test_query/test_products_api.py \
  examples/fakeshop/test_query/test_kanban_api.py --no-cov
```

Why this scope and no wider: it is every test module this slice edits, plus every live module whose imported source this slice edits — `examples/fakeshop/apps/library/filters*.py` feeds `test_library_api.py`, `apps/products/filters.py` feeds `test_products_api.py`, `apps/kanban/filters.py` feeds `test_kanban_api.py`, and `tests/types/fixtures/{shelf,branch}_module.py` feed `test_definition_order.py`. **No `--cov*` flag** — coverage is the maintainer's gate (`BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool`), and `--no-cov` is required because `pytest.ini`'s `addopts` auto-applies `--cov`.

**Temp/scratch tests:** none appropriate. A comment edit is not observable by any test, which is why the static gates below stand in for a test in this slice.

**Attribution rule for a failure.** If the post-edit run fails or errors, compare against the step-1 baseline before touching anything. A live-schema `DuplicatedTypeName` / `LazyType KeyError` collection error in a mixed `test_query/` scope is a known order-dependent pre-existing class; if it appears in BOTH runs it is not this slice's. If it appears only in the post-edit run, that is a real regression — stop and report, and never `git stash` / `git checkout` / `git restore` to investigate (three concurrent sessions are writing this tree).

### Verification Worker 2 owes

Record each in `### Validation run` with its pass/fail and the exact command:

1. `uv run python scripts/check_citations.py` — must exit 0. Baseline at the start of this planning pass: `OK: 737 citations resolve (662 in 422 .py files, 75 in KANBAN.md).` The two new `path::Symbol` refs this slice adds should raise the `.py` count; a DROP in the count means a citation wrapped across a line break and went invisible.
2. `uv run python scripts/check_trailing_commas.py --check <the 19 touched files>` — must exit 0. This is where ASCII-only `.py` source is enforced. Baseline: exit 0 on all of them.
3. `uv run ruff format <the 19 touched files>` then `uv run ruff check --fix <the same 19 files>` — **scoped to this slice's own files, never `.`** (three concurrent sessions).
4. `git status --short` after both ruff invocations. Every modified file must appear in `### Files touched`. The tree carries another session's work at baseline: `docs/SPECS/appx/spec-024-*-rationale.md`, `docs/SPECS/spec-024-*.md`, `docs/SPECS/spec-026-*.md`, `docs/builder/build-025-*.md`, four deleted `docs/builder/bld-*-025-*.md`, `examples/fakeshop/apps/scalars/models.py`, `examples/fakeshop/test_query/test_scalars_api.py`. Those are **not** this slice's and are never reverted or tidied — report, do not clean.
5. **Re-derived post-fix counts**, run against whitespace-flattened text so a wrapped citation cannot hide:

```shell
uv run python - <<'PY'
import re, pathlib
CARD = re.compile(r'spec-021|Spec-021|DONE-021-0\.0\.8')
LINEREF = re.compile(
    r'spec(?:-\d{3})?\s+(?:Decision \d+ )?(?:[HML]\d+ )?\(?(?:lines?\s+\d+|L\d{2,4})', re.I)
# re.I on the whole PROV pattern is deliberate: the lowercase spelling
# ``(finding 3)`` is the same defect as ``Finding 3`` and a case-sensitive
# pattern missed four sites during planning.
PROV = re.compile(r'round[- ]\d+|\bfinding \d+\b|Decision[- ]\d+ [HML]\d+|\bthe [HML]\d+ bug\b', re.I)
SCOPE = ('django_strawberry_framework/filters', 'django_strawberry_framework/utils/inputs.py',
         'tests/filters', 'tests/types', 'examples/fakeshop/apps/library',
         'examples/fakeshop/apps/products/filters.py', 'examples/fakeshop/apps/kanban/filters.py',
         'examples/fakeshop/test_query/test_library_api.py',
         'examples/fakeshop/test_query/test_products_api.py')
# Deliberate survivors: spec-028 (orders) refs that live inside a file this slice
# edits for other reasons. They are OUT of scope; see the out-of-scope table.
EXPECTED = {'Spec line 1038', 'spec line 1039'}
card_total = 0
for p in sorted(pathlib.Path('.').rglob('*.py')):
    if '.venv' in p.parts:
        continue
    # Strip the leading ``#`` of every line BEFORE flattening: a citation
    # wrapped inside a ``#`` comment block puts a ``#`` between the spec token
    # and the line number, which a plain whitespace flatten cannot bridge.
    flat = re.sub(r'\s+', ' ', re.sub(r'\n[ \t]*#', '\n', p.read_text(errors='ignore')))
    hits = CARD.findall(flat)
    if p.as_posix() == 'examples/fakeshop/test_query/test_kanban_api.py':
        print(f'EXCLUDED (fixture data) {p}: {len(hits)}')
        continue
    card_total += len(hits)
    if hits:
        print(f'D12 {p}: {len(hits)} {hits}')
    if p.as_posix().startswith(SCOPE):
        for label, pat in (('D13', LINEREF), ('D14', PROV)):
            h = [x for x in pat.findall(flat) if x not in EXPECTED]
            if h:
                print(f'{label} {p}: {len(h)} {h}')
print(f'D12 total (excluding test_kanban_api.py fixture data): {card_total}')
PY
```

Expected after the fix: `D12 total ... : 0`, and no `D13` or `D14` row printed. The `EXCLUDED` line must read `5` — if it reads anything else, `test_kanban_api.py` was edited and must be reverted to `HEAD` for that file only.

**Baselines this script prints at `HEAD`, measured during planning** — Worker 2 should reproduce these before editing, as proof the instrument works before trusting its zero: `D12=30`, `D13=17`, `D14=20`. If a pre-edit run disagrees with any of those three, the instrument or the tree moved; stop and report rather than proceeding against an unexplained baseline.

**The script is necessary, not sufficient.** It took three corrections during planning (line-wrap in a docstring, lowercase `finding`, line-wrap inside a `#` comment block), and each correction revealed sites a previous version reported as absent. A green run therefore confirms the tables were applied; it does not prove no fourth blind spot exists. The per-site tables are the contract; the script is the check on it.

6. State in the build report that the artifact `docs/builder/bld-slice-2-027-citation_and_provenance_rot.md` itself quotes `spec-021` many times. A repo-wide grep without `--include='*.py'` will hit this file; that is expected and correct — a per-cycle scratchpad is exempt from rule 27 (`START.md` "Temp artifact conventions"), and the scan above is `.py`-only for exactly this reason.

### `scripts/review_inspect.py` — recorded skip

**Skipped, with reason.** `BUILD.md` `### When to run the helper during build` requires it of Worker 1 "when the plan adds logic to any existing `.py` file of 150+ source lines, or to any file under `optimizer/` or `types/`". **This slice adds no logic to any `.py` file** — every edit is comment or docstring text and no executable statement changes. The helper's own output would be identical before and after, because `<stem>.stripped.py` replaces every comment and string-literal token with `...`. The same reason discharges Worker 3's trigger. `BUILD.md` permits the recorded skip for a file whose disposition is "no review-worthy logic"; that disposition holds for all nineteen files here.

### Failability proofs

**This slice introduces no new boundary, guard, gate, or rejection path.** Worker 2's `### Failability proofs` subsection therefore reads exactly:

```text
None; this pass introduced no new boundary.
```

Do not manufacture a proof for a comment edit. The mutate / run / count-rows / revert / byte-compare loop has nothing to mutate: removing a comment changes no test outcome by construction, so every such "proof" would be a zero-row result with no boundary behind it.

### Boundary count and the split question

**Estimated new boundaries: 0.** `BUILD.md` `### Slice splitting` requires the split question answered in writing rather than answered by splitting. The answer: **one unit.** The 19 files are ~59 text edits sharing a single decision — which citation forms this card's code is allowed to use — and splitting them would put half the corpus on one form and half on another between passes, which is the exact half-applied state `### DRY analysis` identifies as the characteristic failure. There is no independent risk profile to separate: no boundary, no behavior, no test outcome moves. The diff is large by line count and trivially reviewable by shape, which is the opposite of the case splitting exists for.

### Hot-path budget

**Not applicable; the build plan declares no hot path, and this slice does not change it.** Nothing here runs per request, per resolver, per row, per connection, or per outbound message — nothing here runs at all. Worker 2 writes `Not applicable; plan declares no hot path.`

### Floor verification

**Not applicable; the build plan declares floor-verification scope `none`.** No Django / Strawberry / channels integration seam is touched, because no executable statement is touched. Worker 2 writes `Not applicable; plan declares floor-verification scope none.`

### Implementation discretion items

Deliberately narrow. Every citation target in the three per-site tables is **decided**, not delegated — the Decision numbers were confirmed against the spec body during this planning pass and the two symbol refs were confirmed to resolve. What is Worker 2's:

- **Where a re-wrapped sentence breaks.** The tables give the replacement text, not its line breaks. Choose the wrap that reads best within 99 columns, subject to the one hard rule that a `path::Symbol` citation stays on one line.
- **Whether to keep or drop a now-redundant connective** when a deletion leaves a stub (`the way an earlier ...`, `- the`, a dangling `and`). Prefer the shortest reading that keeps the invariant intact.
- **Ordering of the edits within a file.** Independent.

What is NOT discretion, and must be escalated to Worker 1 under `### Notes for Worker 1 (spec reconciliation)` rather than decided:

- Any site whose repair appears to need an executable-statement change.
- Any `spec-021` hit that, read in context, turns out to mean `docs/SPECS/spec-021-apps-0_0_7.md` after all. This planning pass read all 27 and found none, but a re-derivation that disagrees is a finding, not a discrepancy to smooth over.
- Any citation target in the tables that does not match the Decision body when Worker 2 reads it. The mapping was confirmed here; a disagreement means one of us is wrong and Worker 1 owns the resolution.

### Spec slice checklist (verbatim)

The spec's own `## Slice checklist` has no entry for this cycle — `027` shipped as `DONE-027-0.0.8` and its six slices are all closed (the same condition Slice 1 recorded). This slice's contract comes from the build plan's checklist line for Slice 2 and from the per-site tables above. The boxes below are that contract. **Worker 2 ticks each box in the same build report that lands it; Worker 1 audits the ticks at final verification.**

- [x] Every one of the 27 `spec-021` / `Spec-021` occurrences across the 9 files in `### Per-site inventory — D12` is retired; the post-fix `.py` population of `spec-021` / `Spec-021` is 0.
- [x] The 3 `DONE-021-0.0.8` prose citations in `examples/fakeshop/apps/products/filters.py`, `examples/fakeshop/apps/kanban/filters.py`, and `examples/fakeshop/test_query/test_products_api.py` read `DONE-027-0.0.8`.
- [x] `examples/fakeshop/test_query/test_kanban_api.py` is UNCHANGED; its 5 `DONE-021-0.0.8` occurrences are fixture data and survive deliberately.
- [x] All 17 raw spec-line-number references in `### Per-site inventory — D13` are DELETED, not renumbered; each site carries either the confirmed `spec-027 Decision N` reference from the table, a symbol-qualified source ref, or no pointer at all.
- [x] The two wrapped `spec-021 line 665` citations in `tests/filters/test_finalizer.py` (lines ~333 and ~395) are both retired — the ones a single-line grep cannot see.
- [x] All 20 build-process provenance occurrences (19 sites) in `### Per-site inventory — D14` are DELETED (`H1`, `M1`, `M5`, `M6`, `H3`, `round-3`, `round-6`, `Finding 1`, `Finding 2`, and the LOWERCASE `finding 1` / `finding 3` spellings); each surviving sentence states the invariant in the present tense with no claim about how the change came to be.
- [x] The four lowercase-`finding` sites (`filters/sets.py` lines ~921, ~951, ~1203 and `tests/filters/test_sets.py` line ~6127) are retired — the ones a case-sensitive sweep cannot see.
- [x] `tests/types/test_definition_order.py::test_filterset_class_resolves_across_module_boundary`'s docstring reads as one coherent sentence stating what the test pins.
- [x] No executable statement changed in any of the 19 files; no test renamed, no assertion altered, no fixture moved.
- [x] Every new `path::Symbol` citation sits entirely on one line and resolves under `scripts/check_citations.py`.
- [x] Every edited line is ASCII-only, and within 99 columns except where an unbreakable `path::Symbol` citation forces the E501-graced 110 ceiling. (Reworded at final verification from `Every edited line is ASCII-only and within 99 columns.`; see `### Spec changes made (Worker 1 only)` item 2.)
- [x] `uv run python scripts/check_citations.py` exits 0.
- [x] `uv run python scripts/check_trailing_commas.py --check <the 19 touched files>` exits 0.
- [x] `uv run ruff format` and `uv run ruff check --fix` were run **scoped to this slice's own files**, never `.`, and `git status --short` afterwards shows no file outside `### Files touched`.
- [x] The focused test scope in `### Test additions / updates` was run as a pre-edit baseline AND after the edits, and both results are recorded.
- [x] The re-derived post-fix count script printed `D12 total ... : 0`, no `D13` row, no `D14` row, and `EXCLUDED (fixture data) ... : 5`.
- [x] No file outside the 19 in `### Files touched` was edited; nothing under `django_strawberry_framework/mutations/`, `orders/`, `rest_framework/`, `forms/`, or the other cards' test trees was touched.

---

## Build report (Worker 2)

Every site in the plan's three per-site tables was applied. **19 files, 59 distinct edit
sites** (the plan's estimate, confirmed by per-file tally: base 3, factories 1, inputs 7,
sets 10, utils/inputs 1, test_factories 1, test_finalizer 5, test_inputs 2, test_sets 5,
test_base 1, test_definition_order 1, shelf_module 1, branch_module 1, library/filters 4,
filters_genre 1, test_library_api 12, products/filters 1, kanban/filters 1,
test_products_api 1). Nothing outside the writable list was touched; nothing was deferred
except the one recorded column-width deviation below.

### Files touched

Grounded in `git status --short` after both ruff invocations (the full listing is under
`### Validation run`).

- `django_strawberry_framework/filters/base.py` — D14 x3: two `Decision 4 M6` -> `spec-027 Decision 4`; the `round-6 Finding 1` sentence rewritten to state the invariant (`a per-method copy would let the empty-``node_id`` guard reach only one of them`) and re-wrapped 3 lines -> 2.
- `django_strawberry_framework/filters/factories.py` — the single D13+D14 site: `(Decision 4 H1 / spec-027 lines 579-584)` -> `(spec-027 Decision 4)`, plus a contained 2-line re-wrap of the shortened paragraph.
- `django_strawberry_framework/filters/inputs.py` — 7 sites. D13 x4 (`Decision 4 M5 (line 591)`, `line 595`, `L603`, `Decision 4 line 594`) all resolved to bare `spec-027 Decision 4`; D14 x4 (`Decision 4 M1` x2, the shared `M5` site, `Finding 2`). The `Finding 2` comment became `an omitted ``default`` would build a REQUIRED field.` One 2-line re-wrap at the `ChoiceFilter` docstring.
- `django_strawberry_framework/filters/sets.py` — 10 sites. D13 x5 (`L566-567 + L607` x2, `L566-567`, `L518-605`, `L668-678`) -> `spec-027 Decision 4` / `Decision 3 Layer 5` / `Decision 8` per the table; D14 x5 (`finding 3` x2, `finding 1`, `Finding 2`, `round-3`).
- `django_strawberry_framework/utils/inputs.py` — D13 x1: `Spec-027 line 247` -> bare `Spec-027` (the statement lives in the spec's `### Explicitly do not borrow`, not in a Decision — confirmed by reading that section), with a 2-line re-wrap.
- `tests/filters/test_factories.py` — D13 x1: `Per spec line 247` -> `per spec-027`, normalized to the card id.
- `tests/filters/test_finalizer.py` — 5 sites, each carrying BOTH a `spec-021` token and a raw line number. Two are the wrapped `spec-021\n    line 665` citations (docstring + `#` comment), both replaced with the one-line symbol ref `django_strawberry_framework/types/finalizer.py::_bind_filterset_owner`; one replaced with the one-line symbol ref to the sibling test; two resolved to `spec-027 Decision 9` and `spec-027 Decision 3 Layer 2`.
- `tests/filters/test_inputs.py` — D12 x1 (`spec-021's intentional flat shape`) and D14 x1 (`Finding 2` rule sentence, also dropping the tense-marker `now`).
- `tests/filters/test_sets.py` — D14 x5 (`Finding 2`, `the H3 bug`, `finding 1`, `Finding 1` x2).
- `tests/types/test_base.py` — D12 x1, normalized to the single form `spec-027 Decision 7`.
- `tests/types/test_definition_order.py` — the mangled docstring repaired as one coherent sentence, discharging the `spec-021` occurrence in the same edit.
- `tests/types/fixtures/shelf_module.py`, `tests/types/fixtures/branch_module.py` — D12 x1 each, bare token swap.
- `examples/fakeshop/apps/library/filters.py` (4), `filters_genre.py` (1), `examples/fakeshop/test_query/test_library_api.py` (12) — D12 bare token swaps, byte-length-preserving.
- `examples/fakeshop/apps/products/filters.py`, `examples/fakeshop/apps/kanban/filters.py`, `examples/fakeshop/test_query/test_products_api.py` — the 3 `DONE-021-0.0.8` -> `DONE-027-0.0.8` prose citations, byte-length-preserving.

**Deliberately NOT touched, per the plan's out-of-scope table:**
`examples/fakeshop/test_query/test_kanban_api.py` (5 `DONE-021-0.0.8` fixture-data occurrences, verified still 5); `test_library_api.py` #"Spec line 1038" / #"spec line 1039" (verified still present at lines 2206-2207, inside the `Spec-028 test plan` docstring); every `mutations/`, `orders/`, `rest_framework/`, `forms/`, `types/base.py`, `connection.py`, `_strawberry_patches.py` site and the other cards' test trees.

### Tests added or updated

None. No test was added, renamed, re-parametrized, or had an assertion changed. Nine of the
nineteen files are test modules; every edit in them is docstring or comment text.

### Validation run

1. **Pre-edit focused baseline** (implementation step 1), run BEFORE any edit:

   ```shell
   uv run pytest tests/filters/ tests/types/test_base.py tests/types/test_definition_order.py \
     examples/fakeshop/test_query/test_library_api.py \
     examples/fakeshop/test_query/test_products_api.py \
     examples/fakeshop/test_query/test_kanban_api.py --no-cov -q
   ```

   Result: **`1084 passed in 61.54s`**, exit 0. No collection error, no pre-existing failure —
   so the known order-dependent `DuplicatedTypeName` / `LazyType KeyError` class did not
   appear at this scope and any post-edit failure would have been attributable.

2. **Pre-edit re-derivation of the plan's baselines**, run before editing to prove the
   instrument works before trusting its zero. Printed `D12 total ... : 30`, `D13 total: 17`,
   `D14 total: 20`, `EXCLUDED (fixture data) ... : 5` — **all four match the plan exactly**,
   per-file and per-token (the printed hit lists reproduced the plan's tables site for site).

3. `uv run ruff format <the 19 files>` — **pass**, `19 files left unchanged`. Scoped to this
   slice's own files; never `.`.

4. `uv run ruff check --fix <the same 19 files>` — **pass**, `All checks passed!`. No fix
   applied (nothing to fix).

5. `uv run python scripts/check_trailing_commas.py --check <the 19 files>` — **pass**, exit 0.
   This is the ASCII-only `.py` gate; no non-ASCII character was introduced (independently
   confirmed by a byte scan of every added line — 0 hits).

6. `uv run python scripts/check_citations.py` — **pass**, exit 0:
   `OK: 740 citations resolve (665 in 422 .py files, 75 in KANBAN.md).`
   The plan's baseline was `737 (662 in .py files)`. The `.py` count **rose by 3**, matching
   the 3 new `path::Symbol` refs this slice adds (`::_bind_filterset_owner` x2 plus the
   sibling-test ref). A drop would have meant a citation wrapped across a line break and went
   invisible; it rose, so none did.

7. `git status --short` after both ruff invocations — **every modified file is slice-intended
   and appears in `### Files touched`.** The 19 are all `M`. The remaining entries are, in
   full, and none is this pass's:
   - this cycle's other slices / Worker 0: `docs/SPECS/spec-027-filters-0_0_8.md` (M, Slice 1),
     `docs/SPECS/appx/spec-027-filters-0_0_8-rationale.md` (??, Slice 1),
     `docs/builder/bld-slice-1-027-*.md`, `bld-slice-2-027-*.md` (this artifact),
     `build-027-filters-0_0_8.md`.
   - the three concurrent sessions' baseline-dirty work, exactly as the plan's item 4 lists it:
     `docs/SPECS/appx/spec-024-*-rationale.md`, `docs/SPECS/spec-024-*.md`,
     `docs/SPECS/spec-026-*.md`, `docs/SPECS/appx/spec-026-*-rationale.md`,
     `docs/builder/build-025-*.md`, `build-026-*.md`, four deleted `bld-*-025-*.md`,
     `bld-final-026.md`, `bld-integration-026.md`, `bld-slice-{1,2,3}-026-*.md`,
     `examples/fakeshop/apps/scalars/models.py`, `examples/fakeshop/test_query/test_scalars_api.py`.

   **Nothing was reverted, tidied, or `git checkout`-ed.** No `git stash` / `checkout` /
   `restore` / `worktree` was run at any point in this pass.

8. **Post-fix re-derivation** (the plan's script, verbatim, against whitespace-flattened text
   with the `#`-strip so a citation wrapped inside a comment block cannot hide):

   ```text
   EXCLUDED (fixture data) examples/fakeshop/test_query/test_kanban_api.py: 5
   D12 total (excluding test_kanban_api.py fixture data): 0
   ```

   **No `D12` per-file row, no `D13` row, no `D14` row printed, and `EXCLUDED` reads 5** — the
   three in-scope populations are closed and the fenced-out fixture data is intact.

9. **Post-edit focused run**, same command as step 1: **`1084 passed in 65.76s`**, exit 0.
   Identical pass count to the baseline, zero failures, zero collection errors.

10. **Executable-token identity proof** (not required by the plan; run because "no executable
    statement changed" is a claim, and `BUILD.md` `## Claims are proven mechanically` treats a
    relocated-or-unchanged claim as needing a token diff rather than prose). For each of the 19
    files, `git show HEAD:<path>` was read read-only into memory, both versions tokenized with
    `tokenize.generate_tokens`, and every `COMMENT` / `NL` token plus every statement-position
    docstring `STRING` dropped. Result: **`IDENTICAL` for all 19, `executable-token
    divergences: 0`.** No `git checkout`, no stash, no scratch file inside the repo.

11. `uv run pytest tests/types/test_base.py --no-cov -q` — **`160 passed`**, re-run after a
    late one-line docstring normalization in that file (see `### Implementation notes`), with
    steps 3-6 and 10 all re-run green afterwards.

### Failability proofs

None; this pass introduced no new boundary.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- **One line exceeds 99 columns, deliberately, and its checklist box is left un-ticked.**
  `tests/filters/test_finalizer.py`, inside
  `test_phase_2_5_accepts_multi_owner_with_identical_target`'s docstring, carries the citation
  `` `tests/filters/test_finalizer.py::test_phase_2_5_rejects_multi_owner_with_diverging_pk_identity` ``
  at **102 columns**. The citation token alone is 96 characters, so at the docstring's 4-space
  indent the line cannot reach 99 with the citation intact, whatever the surrounding prose does
  — I re-wrapped the sentence so the citation sits alone on its line, which is the minimum
  achievable. The plan's rule 6 fixes the priority explicitly ("If a citation does not fit,
  shorten the surrounding prose, never the citation"), and `AGENTS.md` line 17 graces E501 to
  110 via `max-line-length = 110` for exactly the lines the formatter cannot break; `ruff check`
  passes. It is the ONLY added line over 99 across all 19 files (measured over every `+` line of
  the diff). The box `Every edited line is ASCII-only and within 99 columns.` is therefore left
  `- [ ]` rather than over-ticked: the ASCII half landed everywhere, the 99 half has this one
  licensed exception. The alternative — dropping the `tests/filters/` prefix to
  `test_finalizer.py::test_...`, which `scripts/check_citations.py` would still resolve via the
  citing file's own directory — was rejected because that script's own docstring names a bare
  basename as the ambiguity rule 27 exists to remove.
- **Re-wrap policy: minimal and contained.** `ruff format` does not reflow comments or
  docstrings, so five deletions left ragged lines. I re-wrapped only where the deletion left a
  genuinely short stub, and each re-wrap is contained to the 2-3 lines already being edited so
  no cascade reflows a neighbouring paragraph — a cascading reflow is exactly what wraps a
  citation across a line break. Sites re-wrapped: `filters/base.py` (3 lines -> 2),
  `filters/factories.py` (2 lines), `filters/inputs.py` `_choice_enum_from_filter` docstring
  (2 lines), `utils/inputs.py` (2 lines), `tests/filters/test_finalizer.py` (the two
  `_bind_filterset_owner` sites and the sibling-test site). Every other shortened line was left
  as-is: it stayed within the surrounding paragraph's rhythm and re-wrapping it would have been
  churn with a wrap hazard attached.
- **`filters/base.py:251-253` connective.** The plan left "whether to keep or drop a
  now-redundant connective" to discretion. Dropping `the way an earlier per-method copy let ...`
  leaves a dangling clause, so the sentence is recast in the counterfactual present ("a
  per-method copy **would** let ..."), which keeps the reason intact and states no claim about
  how the code came to be.
- **`filters/sets.py:951` `field_name`.** The plan's replacement text quotes the identifier as
  ``field_name`` in double backticks where the original had it bare. Applied as the plan wrote
  it — it matches the surrounding docstring's convention for identifiers.
- **`tests/types/test_base.py:399` form normalization.** The plan's row says "Normalize the
  spelling to `spec-027 Decision 7` so the file uses one form." My first pass wrote
  `spec-027 (Decision 7 promotion gate)`, which carries both tokens but not as the one
  contiguous form the plan named; I corrected it to
  `` ships per spec-027 Decision 7 (promotion gate) `` and re-ran every gate. Recorded because
  the intermediate state existed on disk between two gate runs.
- **The three symbol refs were confirmed to resolve before being written**, not after:
  `_bind_filterset_owner` is defined at `django_strawberry_framework/types/finalizer.py:1220`
  and `test_phase_2_5_rejects_multi_owner_with_diverging_pk_identity` at
  `tests/filters/test_finalizer.py:158`. `check_citations.py` then confirmed all three
  mechanically (the +3 delta in item 6).
- **Every Decision target in the plan's D13 table was re-read against the spec body at `HEAD`
  before the text was applied**, per the escalation rule in `### Implementation discretion
  items`. All twelve mappings hold — `Decision 4`'s converter-table rows for `ChoiceFilter`
  (spec line 503), `Filter(method=...)` (507), `RangeFilter` (506), the `GlobalIDFilter`
  `type_name`-before-queryset-clause rule (515), the FK/PK Relay-Node first bullet (478) and
  the "Where the conditional runs" block (491); `Decision 3` Layer 5 (402) and Layer 2 (396);
  `Decision 8` steps 3 / 4a (607, 609); `Decision 9`'s lifecycle / cycle-safe clear (630-643);
  `Decision 6` subpass 1's "the owner slot stores the FIRST binding" (557); and the
  `replace_csv_filters` statement, confirmed to live in `### Explicitly do not borrow` (185)
  and in no Decision, which is why that site drops to a bare `spec-027`. **Nothing to escalate.**
- **No `spec-021` hit turned out to mean `docs/SPECS/spec-021-apps-0_0_7.md`.** Every one was
  read in context while editing; all sit in filtering prose, agreeing with the plan's own
  reading of all 27.

### Notes for Worker 3

- The diff is large by line count (75 insertions / 76 deletions across 19 files) and trivially
  reviewable by shape: **every hunk is comment or docstring text.** Item 10 of
  `### Validation run` is the mechanical proof — executable-token identity against `HEAD` for
  all 19 files — so a re-run of that check is cheaper than reading 151 changed lines for a
  smuggled statement.
- **The re-derivation script is necessary, not sufficient**, as the plan says: it took three
  corrections during planning and a green run confirms the tables were applied, not that no
  fourth blind spot exists. If you want an independent instrument, the two blind spots already
  known are line-wrap (flatten whitespace AND strip a leading `#` before matching) and case
  (`finding` as well as `Finding`).
- Three fenced-out populations will still show up in any repo-wide sweep and are **correct**
  survivors: `test_kanban_api.py`'s 5 `DONE-021-0.0.8` fixture-data strings (a create/assert
  pair — rewriting half breaks the test), `test_library_api.py`'s `Spec line 1038` /
  `spec line 1039` (spec-028 refs inside a `Spec-028 test plan` docstring), and every
  other-card site in the plan's out-of-scope table.
- This artifact itself quotes `spec-021` many times. A repo-wide grep without
  `--include='*.py'` will hit it; that is expected and correct — a per-cycle scratchpad is
  exempt from rule 27 (`START.md` "Temp artifact conventions"), which is why the scan is
  `.py`-only.
- `scripts/review_inspect.py` was not run. The plan records the skip with its reason (the
  helper's output is identical before and after, because `<stem>.stripped.py` replaces every
  comment and string-literal token with `...`), and that same reason discharges your trigger.
- No temp test was created; `docs/builder/temp-tests/` is untouched by this pass.

### Notes for Worker 1 (spec reconciliation)

No spec gap, conflict, or unstated assumption surfaced. Every Decision this slice's citations
now point at states the contract the citing comment claims it states — the twelve confirmations
are enumerated in `### Implementation notes`. Two items for the record:

- **The 102-column citation line is a plan-vs-implementation tension the plan itself resolved,
  not drift.** The plan's `### Implementation steps` step 6 sets a 99-column hard constraint AND
  a "never shorten the citation" hard constraint, and at this one site they cannot both hold. I
  applied the plan's own stated priority (citation wins) and left the checklist box un-ticked
  rather than over-ticking. **Where it lives:** the artifact's `### Spec slice checklist
  (verbatim)`, final-but-four box. **Current wording:** `Every edited line is ASCII-only and
  within 99 columns.` **Recommended replacement:** `Every edited line is ASCII-only, and within
  99 columns except where an unbreakable `path::Symbol` citation forces the E501-graced 110
  ceiling.` No spec text is implicated — this is an artifact-checklist wording matter for your
  audit, not a spec edit.
- **No amendment is owed to `docs/SPECS/spec-027-filters-0_0_8.md` by this slice.** The Slice-3
  surfaces (D1-D11) were not touched and not re-derived here; this pass read only the Decision
  bodies it needed to confirm citation targets, and found them accurate as written.

<!-- LINK DEFINITIONS -->

<!-- Root -->

[agents]: ../../AGENTS.md

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

[build-027]: build-027-filters-0_0_8.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

---

## Review (Worker 3)

### What I re-derived independently vs accepted on Worker 2's record

Re-derived from scratch with instruments written here, not copied from the plan:

- **"No executable statement changed" (all 19 files, not a subset).** Tokenized `git show HEAD:<path>` (read into memory, no scratch file inside the repo) and the working-tree file, dropped `COMMENT` / layout tokens, then dropped every `STRING` token whose whole logical line is that string (the docstring definition). `IDENTICAL` for all 19; **executable-token divergences: 0.** This is the claim the whole slice rests on and it holds.
- **The citation delta, as a SET rather than the net figure.** Worker 2's `+3` is a net, and an added-three / lost-one reads as `+3` too. I built the `path::Symbol` multiset for every `.py` file at `HEAD` and in the working tree and differenced them: **3 added, 0 removed, tree-wide.** The three added are `types/finalizer.py::_bind_filterset_owner` x2 and the sibling-test ref, all in `tests/filters/test_finalizer.py`. Because the citation regex is line-bounded by construction, the fact that all three MATCH is itself the proof that none is wrapped across a line break, and the empty removed-set is the proof that no pre-existing citation went invisible under the net.
- **The three post-fix populations, with a different instrument.** Rather than re-run the plan's regex-over-flattened-text script, I swept the `COMMENT` and `STRING` **tokens** of each file. Tokenizing sidesteps both known blind spots at once and by construction rather than by patch: a citation wrapped inside a docstring and one wrapped across consecutive `#` lines both land in one flat string, because comment markers and newlines are never part of a token's semantic text. Result on the 19 files: **D12 zero, D13 zero in-scope, D14 zero.**
- **The D12 sweep run repo-wide, deliberately NOT against the slice's file list** (`worker-3.md` "Test staleness": the tree a slice missed is by definition the one that cannot appear in its diff). Every `.py` file outside `.venv`: the only surviving occurrences anywhere are the **5 fenced-out fixture-data strings in `test_kanban_api.py`**. No tree outside the enumerated 19 was carrying this card id.
- **The three fenced-out populations survived.** `test_kanban_api.py` = 5 `DONE-021-0.0.8` (unchanged, and absent from `git status`); `test_library_api.py` #"Spec line 1038" / #"spec line 1039" both present; the out-of-scope trees untouched.
- **Gates and tests.** `scripts/check_citations.py` -> `OK: 740 citations resolve (665 in 422 .py files, 75 in KANBAN.md)`, exit 0. `scripts/check_trailing_commas.py --check <the 19>` -> exit 0. `uv run ruff check` over the slice's trees -> `All checks passed!`. Focused scope re-run at the plan's exact command with `--no-cov`: **`1084 passed in 61.59s`**, matching both of Worker 2's runs.
- **Line width and ASCII, measured over every `+` line of the diff.** Exactly one added line exceeds 99 columns (the 102-column citation line); zero non-ASCII bytes.
- **Every Decision body the new citations name, read at `HEAD`** — see `### Citation-target audit` below.

Accepted on Worker 2's record without re-running: the **pre-edit** baseline (`1084 passed`) and the pre-edit population re-derivation (`D12=30 / D13=17 / D14=20 / EXCLUDED=5`). Neither is re-derivable now without destroying the slice's work, and both are corroborated: the post-edit run I reproduced returns the identical `1084 passed`, and the plan's own `HEAD` measurements are independently confirmed by my `git show HEAD:` token pass.

### Failability proofs

**Audited; the `None; this pass introduced no new boundary.` entry is correct, and my re-run set is legally empty.** This is not accepted on prose: the executable-token identity check above proves mechanically that no statement, branch, guard, comparison, or raise moved in any of the 19 files, so there is no boundary in the diff for the mandatory floor to select. `BUILD.md` `### What needs a proof, and what does not` puts doc edits outside the obligation explicitly, and `worker-3.md` permits an empty re-run set exactly when "the diff introduces no boundary that meets the floor". No transient source mutation was made in this pass, so the source carve-out went unused.

### `scripts/review_inspect.py`

**Skip confirmed still valid against the actual diff, not assumed.** `BUILD.md` `### When to run the helper during build` fires Worker 3's trigger on a new `.py` file, on a file under `django_strawberry_framework/optimizer/` or `django_strawberry_framework/types/`, or on 30+/50+ lines of new logic. The diff adds no file; touches no file under the **package's** `types/` or `optimizer/` (the four `tests/types/` files are the test tree, not the gated package trees); and adds **zero** lines of logic, which the token-identity check establishes mechanically rather than by inspection. No shadow file was generated or read in this pass.

### Citation-target audit

Every Decision the slice's new or rewritten citations name was opened at `HEAD` and read against the sentence citing it. Twelve of thirteen hold:

- `filters/base.py` (x2) `spec-027 Decision 4` for `relay.GlobalID.from_id(value)` -- Decision 4's "Strawberry-specific `GlobalIDFilter`" block states that decode verbatim. Holds.
- `filters/factories.py` `spec-027 Decision 4` for "resolved filter instances, NOT a parallel `FILTER_DEFAULTS` map" -- Decision 4's "Where the conditional runs" block states it near-verbatim, including "the two cannot drift". Holds.
- `filters/inputs.py` `Decision 4` x5 (`CharField` conversion-table row, `ChoiceFilter` non-`Choices` raise, the conversion table itself, unknown-form-field raise, `RangeWidget` positional `name_0`/`name_1`) -- each maps to a specific row of Decision 4's converter table. Holds.
- `filters/inputs.py` `type_name` validated "before any queryset clause runs" -- Decision 4's `GlobalIDFilter` block uses that exact phrase. Holds.
- `filters/sets.py` x3 own-PK branch `Decision 4` -- Decision 4's first bullet covers "FK / **PK** whose owning `FilterSet`'s target `DjangoType` ... implements `relay.Node` -> `GlobalIDFilter`". Holds.
- `filters/sets.py` `Decision 3 Layer 5` for the per-field operator bag -- Layer 5's `LOOKUP_NAME_MAP` table and the `galaxyName: { exact: ... }` nested-bag shape are both there, and the lookup spellings the comment lists (`exact` / `i_contains` / `in_`) are that table's own. Holds.
- `filters/sets.py` `Decision 8` for `<rel>__in=<intersected>` ordering -- Decision 8 steps 3 and 4a state the visibility-scoped right-hand side and the before-instantiation constraint. Holds.
- `utils/inputs.py` and `tests/filters/test_factories.py` bare `spec-027` for `replace_csv_filters` -- confirmed the statement lives in `### Explicitly do not borrow` ("Strawberry's typed input handles `list[T]` natively ...; the function is dropped") and in no Decision, so declining to name one is right, not a shortcut.
- `tests/filters/test_finalizer.py` `Decision 9` for the cycle-safe `registry.clear()` -- Decision 9's "Import-cycle-safe integration" bullet with the local import under `except ImportError`. Holds.
- `tests/types/test_base.py` `spec-027 Decision 7 (promotion gate)` -- Decision 7 is titled the promotion gate and its item 3 is the `ALLOWED_META_KEYS` promotion, which is what the test asserts. Holds.

The thirteenth is the Low below.

### High:

None.

### Medium:

None.

### Low:

#### `Decision 3 Layer 2` does not state the re-wrap the sentence attributes to it

```tests/filters/test_finalizer.py:795:798
    ``LazyRelatedClassMixin.resolve_lazy_class`` raises
    ``ImportError`` at Layer-2 resolution time. The phase-2.5 binding
    pass re-wraps the ``ImportError`` as ``ConfigurationError`` per
    spec-027 Decision 3 Layer 2 and the package's "finalize-time errors
    are ``ConfigurationError``" convention; ...
```

Decision 3's Layer 2 body states only the two-step resolution ("try as absolute path via `import_string`; on `ImportError`, retry with `bound_class.__module__` prefix"). It is the `ImportError`'s **source**; it says nothing about a `ConfigurationError` re-wrap. Decision 6's subpass 1 does not state it either -- its `ConfigurationError`s are the non-`FilterSet`-subclass and owner-incompatibility raises. The spec DOES pin this contract, but in the `## User-facing API` error-surface bullet (`RelatedFilter("UnknownFilter")` ... -> `ConfigurationError` "at finalization"), which is not a Decision and therefore has no `Decision N` name to cite.

Why it matters, and why it is only Low: the plan's own `### Replacement rules` rule 1 permits a Decision reference "**only when** the Decision's body at `HEAD` was read and confirmed to state the cited contract", and the plan's D13 confirmation column for this row is honest that Layer 2 is "the `ImportError` source this sentence re-wraps" -- which is a different claim from the one the sentence makes. A reader who follows the citation lands on a paragraph that does not contain the contract. Against that: the citation resolves, names the right mechanism, and the sentence's second half ("and the package's 'finalize-time errors are `ConfigurationError`' convention") already carries the rationale unaided. It is strictly better than the `spec-021 lines 416 + 1030` it replaced.

Recommended change, either of: (a) drop the Decision qualifier to `per spec-027 and the package's "finalize-time errors are ``ConfigurationError``" convention`; or (b) keep the Decision-3 pointer but attach it to the clause it does govern -- `raises ``ImportError`` at Layer-2 resolution time (spec-027 Decision 3 Layer 2); the phase-2.5 binding pass re-wraps it as ``ConfigurationError`` per the package's "finalize-time errors are ``ConfigurationError``" convention`. No test expectation changes -- the assertion below the docstring already pins the `ConfigurationError` with the `ImportError` on `__cause__`.

**Escalated to Worker 1** rather than held at `revision-needed`: the target text is Worker 1's (the plan fixed it in the D13 table and told Worker 2 not to choose), and the alternative resolution -- adding the re-wrap sentence to Decision 3 Layer 2 so the existing citation becomes true -- is a spec edit only Worker 1 may make, on a surface Slice 3 owns. Worker 2 applied the plan faithfully; there is nothing here for a re-build pass to do.

### The 102-column deviation: judged acceptable, not a finding

`worker-3.md` frames this as "a box left open with a recorded deferral is not automatically a defect, but a box left open silently is a Medium." It is the loudest possible non-silence: an `### Implementation notes` bullet, a `### Notes for Worker 1` entry with a recommended checklist rewording, and the box left `- [ ]` rather than over-ticked. I verified the substance rather than the disclosure:

- Measured: the citation token is **94** characters (the build report says 96 -- immaterial, and it does not move the conclusion). At the docstring's 4-space indent, `    ` + backtick + 94 + backtick = **100 columns with nothing else on the line at all**, so 99 is unreachable with the citation intact regardless of how the surrounding prose is wrapped or where `).` goes.
- `AGENTS.md` line 17 graces E501 to 110 for precisely "lines the formatter cannot break"; `uv run ruff check` passes; it is the only added line over 99 in the entire diff, which I measured independently over every `+` line.
- The rejected alternative is real -- `check_citations.py` resolves a citation's file half against the citing file's own directory, so the basename form `test_finalizer.py::test_...` would resolve and would fit at 88 columns. Worker 2 recorded the rejection and its reason. I would have made the same call for a different reason than the one given: the script's bare-basename warning is written about **upstream** trees, but the fuller point stands that a `tests/`-rooted path is the unambiguous rule-27 spelling. Either way this is a plan-level preference, not a defect, and Worker 1's recommended box rewording resolves it cleanly.

### DRY findings

None against this diff. The plan's stated DRY control was preventing a **half-applied** sweep -- some sites landing on `spec-027 Decision N`, others on a symbol ref, others on bare prose, with no reader-visible rule. Reading all 19 files' hunks side by side, the applied forms are exactly the three the plan fixed, and each is used where the plan said: a Decision name where a Decision states the contract, a symbol ref where the behavior has a home in code, bare `spec-027` where the statement lives outside every Decision. No new helper, constant, registry, or indirection layer exists in this diff to raise an existence challenge against.

Two adjacent duplication classes exist in these files but are **pre-existing at `HEAD` and outside every dispatched population**; both are recorded under `### Notes for Worker 1` for the deferred-work catalog rather than charged to this pass.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` is **empty** -- the file is untouched by this slice, so `__all__` and the re-export list are unchanged. Consistent with a slice whose executable-token diff is empty by proof.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces.

### Spec slice checklist walk

All 17 boxes walked. **16 ticked, each with a matching change in the diff** (no box ticked without an implementation): the D12 population is zero repo-wide; the 3 `DONE-021-0.0.8` prose citations read `DONE-027-0.0.8`; `test_kanban_api.py` is absent from `git status` with its 5 occurrences intact; all 17 D13 refs are deleted rather than renumbered; both wrapped `spec-021 line 665` citations are gone; the D14 sites tally to 19 sites carrying 20 tokens (`filters/base.py` carries `round-6` and `Finding 1` on one line), all retired; all four lowercase-`finding` sites are retired; the mangled docstring reads as one sentence; no executable statement changed; all three new symbol refs sit on one line and resolve; both gates exit 0; ruff was scoped and `git status` carries nothing outside `### Files touched`; both focused runs are recorded; the post-fix scan reads `D12 total: 0` / no `D13` / no `D14` / `EXCLUDED: 5`; nothing outside the 19 was edited.

**One box left `- [ ]`** ("Every edited line is ASCII-only and within 99 columns") with a recorded, reasoned deferral -- see the section above. Not a Medium: `worker-3.md`'s Medium is for a *silently* unaddressed sub-check.

### What looks solid

- **The claim under review holds under an instrument that did not come from the build report.** A comment-only slice's entire risk surface is "did a statement move", and the answer is no, in all 19 files, by token identity against pristine `HEAD` with no `git checkout` / `stash` / `restore` / `worktree` anywhere in this pass.
- **The mangled-docstring repair reads correctly against what the test asserts.** `test_filterset_class_resolves_across_module_boundary` asserts that `finalize_django_types()` does not raise, that both sibling modules' `filterset_class` slots resolve to their own `FilterSet`s, and that phase-2.5 wired `_owner_definition` on both. "Pins the spec-027 contract that the finalizer's filter-binding pass works across module boundaries without `ImportError`" is an accurate one-sentence statement of exactly that, and the split-sentence artifact is gone.
- **The deletions leave sentences that parse and are true.** I read every site whose provenance clause was removed. `filters/base.py`'s counterfactual recast ("a per-method copy **would** let the empty-`node_id` guard reach only one of them") is the right move -- it keeps the whole reason while making no claim about how the code came to be. `filters/sets.py:951`, `test_sets.py:6127`, `test_sets.py:4567` and `test_inputs.py:158` all read as complete present-tense invariants with the id gone.
- **The re-wrap discipline is the correct one and is visible in the result.** Containing each re-wrap to the 2-3 lines already being edited, rather than reflowing the paragraph, is what kept a cascading reflow from wrapping a citation -- and the empty removed-citation set is the evidence that it worked. Several edited lines are left slightly short as a consequence; that is the right trade and it is recorded as such.
- **Both fenced-out populations that look exactly like in-scope work survived**, including the `test_kanban_api.py` create/assert pair where rewriting one half would have broken the test.

### Temp test verification

None created. `docs/builder/temp-tests/slice-2-027/` was not used: every question this review raised was answerable by reading source against the spec or by a mechanical diff against `HEAD`, and a comment edit is not observable by any test -- which is the same reason the plan gave for standing the static gates in for one. Disposition: nothing to promote.

### Notes for Worker 1 (spec reconciliation)

1. **Escalated (Low, above): `tests/filters/test_finalizer.py` #"per" `spec-027 Decision 3 Layer 2`** attributes the `ImportError` -> `ConfigurationError` re-wrap to a Decision body that does not state it. Two resolution paths, both yours: reword the citation (option (a) or (b) in the finding), or add the re-wrap sentence to Decision 3 Layer 2 so the citation becomes true. The second is a Slice-3 spec surface.

2. **`filters/sets.py::FilterSet.apply` -- the spec and the code disagree, and this slice's edit sits on top of the disagreement.** The docstring now reads "Class-based dispatch, not substring-matching against a constant string", and the code does exactly that (`except SyncMisuseError as exc:`). But spec-027 Decision 8's `apply`-dispatcher paragraph still specifies the shape the code deliberately replaced: "the dispatcher uses an explicit catch-and-rethrow mechanism: `apply` calls `apply_sync` inside a `try / except RuntimeError as exc:` block. If `exc.args[0]` matches the sync-misuse sentinel ... pinned as a module-level constant". The comment is right and the spec is stale. Worker 2 could not have seen this -- it was retiring a `round-3` token, not auditing Decision 8 -- and the site's `Decision 8` opener is pre-existing. This is a genuine code-vs-spec divergence for the Slice-3 catalog.

3. **Deferred-work catalog, class one: history-narrating prose with no finding id.** The plan's `### Replacement rules` rule 6 bans `now` / `no longer` / `previously` / `an earlier` / `corrected to` in comments, and my memory of this repo's standing rule is the same ("comments state the invariant, never how the change came to be"). D14's vocabulary was ids (`round-N`, `Finding N`, `H<n>`/`M<n>`), so id-less history prose was invisible to it. Sweeping the 19 files' comment and string tokens for that vocabulary returns roughly **65 occurrences across 15 of the 19 files** -- e.g. `filters/inputs.py::_encode_global_id_input` #"The previous implementation eagerly decoded the object", which sits three lines below a citation this slice rewrote, and `tests/filters/test_sets.py` alone carries about 21. Deliberately NOT charged to this pass: it is a population an order of magnitude larger than D14, it was never dispatched, and re-deriving it properly (many hits are legitimate contrast prose inside a test explaining what a fixture is NOT, not build provenance) is a planning job. **Re-derive it before carding it** -- my 65 is one instrument's raw hit count, not an audited population.

4. **Deferred-work catalog, class two: `Decision N` references naming no card.** Now that this slice has normalized its own sites to `spec-027 Decision N`, the in-scope files carry **18** pre-existing bare `Decision N` refs with no card prefix (`filters/factories.py` #"Layer 6 of Decision 3", `filters/inputs.py` #"Decision 3 Layer 5", `filters/sets.py` #"Decision 8 step 6", `tests/filters/test_inputs.py` #"consumer helper (Decision 11)", and others). Two of them are actively ambiguous: `utils/inputs.py` #"no operator bag, Spec Decision 8" x2 sit in the shared substrate serving both `filters/` and `orders/` and mean **spec-028**'s Decision 8, not spec-027's. Same defect shape as D12 -- a reference that resolves to the wrong card for a future reader.

5. **The out-of-scope table has a gap worth closing before it is read as a closed contract.** `examples/fakeshop/test_query/test_products_api.py` carries **5 raw spec-line refs** the plan's table never records -- #"identical to the `036` model-driven path (line 388)", #"the `036` anonymous denial (line 458)", #"(mirror line 493)", #"(mirror line 528)", #"(mirror line 694)". They are correctly untouched (they name spec-036, the mutations card, per the scope boundary's card-not-directory rule, and they sit in the file's `036` form-mutation mirror block), but the plan's own stated purpose for that table is "so their survival in a post-fix sweep is not read as an unfinished contract" -- and these will survive every future sweep of a file this slice edited. Add them to the catalog.

6. **No amendment is owed to the spec by this slice's own text.** Twelve of the thirteen Decision targets state the contract their citing sentence claims; the thirteenth is item 1.

### Review outcome

`review-accepted`, with the single Low finding transparently escalated to Worker 1 per `worker-3.md` "Acceptance gate" -- its resolution needs spec context Worker 2 cannot supply, and the text in question is the plan's own, so a re-build pass has nothing to act on. No High or Medium findings. Every acceptance-gate condition is met: no boundary exists in the diff for a failability proof to cover (proven, not assumed); every checklist tick has a matching change and the one open box carries a recorded deferral I judged licensed by `AGENTS.md`'s E501 grace; the public-surface check is clean; the helper skip is confirmed valid against the actual diff; no temp test needs promotion.

---

## Final verification (Worker 1)

### Spec status-line re-verification (Worker 1, every spawn)

`docs/SPECS/spec-027-filters-0_0_8.md` lines 1-9 re-read at the start of this pass. Unchanged since the planning pass and unchanged by this slice: the `Status:` line is still the build-progress paragraph that opens `in progress`, falsified by the card being `DONE-027-0.0.8`. **Still no edit owed by this pass** — build-plan finding D2 assigns it to Slice 3, and this cycle's brief fences Slice 2 out of both the spec and the rationale. `Target release`, `Owner`, `Predecessors`, and Slice 1's rationale-companion pointer all still resolve.

### Spec slice checklist audit

All 17 boxes audited against the working-tree diff, not against the build report. **17 ticked**; one of those was ticked by this pass after a wording correction (below). No box was found ticked without a matching change, so nothing was un-ticked and nothing is silently deferred.

The audit ran on four instruments, all re-derived here rather than read off Worker 2's or Worker 3's record:

| Instrument | Result |
|---|---|
| Plan's re-derivation script, verbatim, over whitespace-flattened `#`-stripped text | `D12 total: 0`, no `D13` row, no `D14` row, `EXCLUDED (fixture data) ... : 5` |
| Executable-token identity vs `HEAD` for all 19 files (`git show HEAD:<path>` read into memory; `COMMENT` / layout tokens and statement-position docstring `STRING`s dropped) | `IDENTICAL` for 19/19, **divergences: 0**. Re-run for `tests/filters/test_finalizer.py` after this pass's own edit: still `IDENTICAL` |
| `scripts/check_citations.py` | `OK: 740 citations resolve (665 in 422 .py files, 75 in KANBAN.md).` exit 0 — the same 740 Worker 2 and Worker 3 measured, so this pass's edit added and removed no citation |
| Every `+` line of `git diff HEAD -- '*.py'` measured for width and non-ASCII bytes | exactly one added line over 99 columns in this slice's files (the 102-column citation line in `tests/filters/test_finalizer.py`); **0 non-ASCII bytes**. The second over-99 line in the diff is `examples/fakeshop/apps/scalars/models.py`, a concurrent session's file, not this slice's |

Per-box confirmations that needed reading rather than a script: the 3 `DONE-021-0.0.8` prose citations read `DONE-027-0.0.8` in `apps/products/filters.py`, `apps/kanban/filters.py`, `test_query/test_products_api.py`; `test_query/test_kanban_api.py` is absent from `git status --short` with its 5 fixture-data occurrences intact; the D13 population tallies 17 across 6 files (inputs 4, sets 5, factories 1, `utils/inputs.py` 1, `test_factories.py` 1, `test_finalizer.py` 5) and every one is DELETED rather than renumbered; the D14 population tallies 20 tokens at 19 sites across 6 files (base 3, factories 1, inputs 4, sets 5, `test_inputs.py` 1, `test_sets.py` 5), `filters/base.py` carrying `round-6` and `Finding 1` on one line; both wrapped `spec-021 line 665` citations are gone; all four lowercase-`finding` sites are retired; the `test_definition_order.py` docstring reads as one sentence; `git status --short` carries no `.py` file outside the 19 except the two the concurrent scalars session owns.

**Every citation target the slice writes was re-confirmed against the spec at `HEAD` by this pass, not accepted from the plan or from Worker 3's audit.** `### Decision 3` Layer 5 (the BFS schema build with the `LOOKUP_NAME_MAP` table), Layer 2 (the two-step module-fallback resolution), `### Decision 4`, `### Decision 7`, `### Decision 8`, `### Decision 9` and the non-Decision `### Explicitly do not borrow` section (which carries the `replace_csv_filters` drop, and is why two sites correctly name no Decision) all exist and all say what their citing sentence claims — with the one exception this pass resolved below.

### The one reworded box

Worker 2 left `Every edited line is ASCII-only and within 99 columns.` open and recommended a rewording; Worker 3 judged the deviation licensed. **Decision: accept the rewording and tick, rather than record a deferral.** A deferral under `ARTIFACT.md` must cite a target (future slice / future spec / maintainer follow-up) and there is none — the line is permanently licensed, not postponed. Measured independently here: the citation token `tests/filters/test_finalizer.py::test_phase_2_5_rejects_multi_owner_with_diverging_pk_identity` is **94** characters (Worker 2's build report says 96 and Worker 3 measured 94; 94 is correct), so at the docstring's 4-space indent the line's floor is `4 + 1 + 94 + 1 = 100` columns with nothing else on it, and 99 is unreachable with the citation intact. `pyproject.toml` line 203 sets `max-line-length = 110`, `uv run ruff check` passes, and it is the only added line over 99 in this slice. The box as originally written encoded a rule stricter than the project's own; the correction is to the plan text I authored, and the original wording is preserved verbatim inside the box so the record shows exactly what changed.

### Escalated Low — resolved by comment retarget

**Route taken: retarget the citation in `tests/filters/test_finalizer.py`. No spec edit, and nothing handed to Slice 3 for it.**

Worker 3's finding is confirmed by direct reading, not accepted on its prose. `docs/SPECS/spec-027-filters-0_0_8.md` `### Decision 3` Layer 2 states only the two-step resolution ("try as absolute path via `import_string`; on `ImportError`, retry with `bound_class.__module__` prefix"). The `ImportError` -> `ConfigurationError` re-wrap contract is pinned in the `### Error shapes` bullet under `## User-facing API`: "`RelatedFilter("UnknownFilter")` where `"UnknownFilter"` cannot be resolved by Layer 2's module-fallback -> `ConfigurationError`(...) at finalization." Layer 2 is the `ImportError`'s source; it is not the re-wrap contract.

The alternative — adding the re-wrap sentence to Decision 3 Layer 2 so the existing citation becomes true — is **rejected, and Slice 3 should not re-open it**: the contract is already stated once, in `### Error shapes`. Duplicating a contract across two spec surfaces creates the half-reconciled state that is worse than either half alone. Citing `### Error shapes` by name instead was also rejected: a section title is not a gated citation form and Slice 3 may rewrite section prose, so it would trade today's wrong pointer for tomorrow's rotted one.

Applied Worker 3's option (b) — attach the Decision pointer to the clause it does govern and let the re-wrap rest on the package convention the sentence already names. In `tests/filters/test_finalizer.py::test_phase_2_5_unresolved_related_filter_raises_at_finalize`'s docstring:

```text
    ``LazyRelatedClassMixin.resolve_lazy_class`` raises ``ImportError``
    at Layer-2 resolution time (spec-027 Decision 3 Layer 2). The
    phase-2.5 binding pass re-wraps it as ``ConfigurationError`` per the
    package's "finalize-time errors are ``ConfigurationError``"
    convention; the original ``ImportError`` is preserved on
    ``__cause__`` so the failure mode is loud AND grep-stable against
    the sibling formatter convention.
```

No assertion, node id, or fixture moved; the executable-token identity check was re-run for this file after the edit and still reads `IDENTICAL`. `ruff format` / `ruff check --fix` / `check_trailing_commas.py --check` / `check_citations.py` all re-run green, scoped to that one file. Every edited line is under 99 columns and ASCII-only. The re-derivation script still prints `D12 total: 0` with no `D13` and no `D14` row, so the retarget introduced no new instance of the populations this slice closed.

### DRY check across this slice and Slice 1

No new duplication. The two slices have **disjoint file sets** — Slice 1 wrote `docs/SPECS/spec-027-filters-0_0_8.md` and `docs/SPECS/appx/spec-027-filters-0_0_8-rationale.md`; Slice 2 wrote 19 `.py` files and no `.md`. The one live coupling between them is that Slice 2's new `spec-027 Decision N` citations point into text Slice 1 rewrote, and every target was re-resolved above.

The plan's stated DRY control was preventing a **half-applied** sweep, and the applied result holds it: a Decision name where a Decision states the contract (13 sites), a symbol ref where the behavior has a home in code (3 sites), and bare `spec-027` where the statement lives outside every Decision (2 sites — `utils/inputs.py` and `tests/filters/test_factories.py`, both the `replace_csv_filters` drop). No fourth form appears anywhere in the diff. No helper, constant, or indirection layer exists in this diff to raise an existence challenge against.

### Focused test run

```shell
uv run pytest tests/filters/ tests/types/test_base.py tests/types/test_definition_order.py \
  examples/fakeshop/test_query/test_library_api.py \
  examples/fakeshop/test_query/test_products_api.py \
  examples/fakeshop/test_query/test_kanban_api.py --no-cov -q
```

**`1084 passed in 61.51s`**, exit 0, run after this pass's own edit to `test_finalizer.py`. No `--cov*` flag. Identical pass count to Worker 2's pre-edit baseline, Worker 2's post-edit run, and Worker 3's re-run; no collection error, so the order-dependent `DuplicatedTypeName` / `LazyType KeyError` class did not appear at this scope.

### Failability, fail-open, and floor confirmations

- **Failability record exists and is correct.** `None; this pass introduced no new boundary.` is not accepted on prose: the executable-token identity check proves mechanically that no statement, branch, guard, comparison, or raise moved in any of the 19 files, so there is no boundary in the diff for the mandatory floor to select.
- **No fail-open shape landed.** By the same proof — the diff contains no expression at all, only comment and docstring text.
- **Floor verification: none owed, and the artifact records it rather than leaving it blank.** The build plan's preamble declares `Floor-verification scope: none`, the plan section states `Not applicable; the build plan declares floor-verification scope none.`, and Worker 2's `### Floor verification` carries the literal `Not applicable; plan declares floor-verification scope none.` No slice in this cycle touches a Django / Strawberry / channels integration seam, because no slice changes an executable statement. **No floor venv is owed by any pass in this cycle**, and the final gate inherits that declaration rather than a blank.
- **Staged-anchor sweep.** `grep -rn 'TODO(spec-027' .` returns nothing outside this cycle's own artifacts; this slice is not the doc-wrap slice and staged none.

### Final status

`final-accepted`.

### Summary

Slice 2 retired every citation and provenance defect in the filtering card's owned `.py` surface: 30 pre-renumber card ids (27 `spec-021` / `Spec-021` plus 3 `DONE-021-0.0.8` prose citations), 17 raw spec line numbers deleted rather than renumbered, 20 build-process provenance tokens at 19 sites, and one mangled docstring, across 19 files and roughly 59 edit sites. Every population was measured at 30 / 17 / 20 rather than the brief's 27 / 11 / 3, the gap being two line-wrapped citations, four lowercase `finding` spellings, and the `H<n>` / `M<n>` finding-id form the brief's vocabulary never swept. Nothing executable moved: token identity against `HEAD` holds for all 19 files. Three new `path::Symbol` citations were added and none removed, all resolving under `scripts/check_citations.py`. The three fenced-out populations survived deliberately — `test_kanban_api.py`'s 5 fixture-data strings, `test_library_api.py`'s two spec-028 line refs, and every other card's owned files. Final verification resolved the one escalated finding by retargeting a Decision pointer to the clause it governs, and reworded one checklist box that encoded a stricter rule than `AGENTS.md`'s own E501 grace.

### Spec changes made (Worker 1 only)

**No edit was made to `docs/SPECS/spec-027-filters-0_0_8.md` or `docs/SPECS/appx/spec-027-filters-0_0_8-rationale.md` by this pass.** Slice 3 owns the spec reconciliation, and splitting it across two diffs is exactly what this cycle's brief fences against. Two changes were made outside the spec and are recorded here because this is the section that owns Worker 1's non-artifact edits:

1. **`tests/filters/test_finalizer.py::test_phase_2_5_unresolved_related_filter_raises_at_finalize` docstring** — the `spec-027 Decision 3 Layer 2` pointer moved from the re-wrap clause to the `ImportError`-source clause it actually governs. Reason: Decision 3 Layer 2's body states only the two-step module-fallback resolution; the re-wrap contract lives in the `### Error shapes` bullet, a non-Decision surface. This is the escalated Low, resolved on the comment side so no spec edit is needed. Comment text only; no executable token changed.
2. **`### Spec slice checklist (verbatim)`, the ASCII / 99-column box** — reworded to `Every edited line is ASCII-only, and within 99 columns except where an unbreakable `path::Symbol` citation forces the E501-graced 110 ceiling.` and ticked. Reason: the original wording was stricter than `AGENTS.md` line 17, which graces E501 to 110 for lines the formatter cannot break; the sole affected line is a 94-character citation whose minimum achievable width at a 4-space docstring indent is 100 columns. The original wording is preserved verbatim inside the box.

### Notes for Worker 1 (spec reconciliation)

**The consolidated Slice-3 inheritance list. Every item below was re-derived during this pass; where a count differs from the source that handed it forward, the corrected figure and the cause are stated. Slice 3 still owes a re-derivation of anything it acts on — this list is a claim, not a measurement.**

Slice 2 itself owes the spec nothing. Twelve of the thirteen Decision targets its citations name state the contract their citing sentence claims; the thirteenth was resolved on the comment side (above) and is **not** a Slice-3 item.

**A. Build-plan findings D2-D11, all still standing.** Slice 1 left every one deliberately; Slice 2 touched none. They are stated in full in `build-027-filters-0_0_8.md` `## Pre-dispatch verification` and re-listed in `bld-slice-1-027-rationale_extraction.md` `### Notes for Worker 1`. One of them is re-derived here because Worker 3 hit it from a second direction:

1. **D5 is confirmed, at the exact lines.** `docs/SPECS/spec-027-filters-0_0_8.md` Decision 8 line 620 pins the retired mechanism verbatim — `apply` calling `apply_sync` inside `try / except RuntimeError as exc:`, matching `exc.args[0]` against a module-level sentinel string, and re-raising with the target type name interpolated. Line 618 and line 607 name `types/relay.py::_apply_get_queryset_sync` / `_apply_get_queryset_async`, and line 952 (DoD item 4) restates the `try / except RuntimeError:` shape a fourth time. At `HEAD`: `grep -rn "_apply_get_queryset_sync" --include='*.py'` over the tree returns **zero** hits; the misuse signal is the typed `django_strawberry_framework/utils/querysets.py::SyncMisuseError` (line 116, `class SyncMisuseError(ConfigurationError, RuntimeError)`); `filters/sets.py::FilterSet.apply` catches that class; and its rethrow message is `"FilterSet.apply called against async get_queryset; use apply_async instead."` with **no** target type interpolated. **The comment this slice edited is right and the spec is stale, in four places, not one** — Decision 8 at 607, 618, 620 and DoD item 4 at 952.

**B. Slice 1's two additional hand-forwards, both re-verified at `HEAD`.**

2. **`[pyproject]` is repaired; do not re-derive it as new rot.** Defined at `docs/SPECS/spec-027-filters-0_0_8.md:987` as `../../pyproject.toml`. It was dangling at `HEAD` before Slice 1 (used in `## Borrowing posture` and Decision 5, defined nowhere), so the repair is of pre-existing rot.
3. **`[fakeshop-test-library-reload]` still points at the wrong file.** Line 1084 defines it as `../../examples/fakeshop/test_query/test_library_api.py`, identical to `[fakeshop-test-library]` on line 1085. The fixture is at `examples/fakeshop/test_query/conftest.py:72::_reload_project_schema_for_acceptance_tests`; `test_library_api.py` only mentions it in comments. Correcting the def is half the fix — build-plan D11's Test-plan-footnote claim naming `test_library_api.py::_reload_project_schema_for_acceptance_tests` is the other half, and both must land together or the spec is half-reconciled.

**C. Worker 3's four remaining routed items, re-derived. Two of the four counts were wrong.**

4. **History-narrating prose with no finding id — a real class, but the population is instrument-dependent and unaudited.** Worker 3 reported "roughly 65 occurrences across 15 of the 19 files". My own token sweep of the same 19 files, over `COMMENT` and `STRING` tokens with the vocabulary `no longer` / `previously` / `the previous` / `an earlier` / `corrected to` / `used to` / `formerly` / `now fires` / `now builds` / `now that`, returns **54 hits across 11 files** (`tests/filters/test_sets.py` 13, `test_products_api.py` 11, `test_library_api.py` 10, `filters/sets.py` 4, `test_finalizer.py` 4, `tests/types/test_base.py` 3, and 2 or 1 each in five more). **Neither number is the population.** They differ because the vocabulary differs, and both include legitimate contrast prose (a test docstring explaining what a fixture is NOT is not build provenance). The confirmed exemplar both sweeps agree on: `django_strawberry_framework/filters/inputs.py::_encode_global_id_input` #"The previous implementation eagerly decoded the object", which sits three lines below a citation this slice rewrote. **Card it only after a planning pass audits hit-by-hit; do not card a raw hit count.**
5. **`Decision N` references naming no card — the class is real and Worker 3's count of 18 is a substantial under-derivation.** My token sweep over the same 19 files returns **83** raw `Decision N` / `Decision-N` occurrences with no adjacent `spec-NNN` prefix. The gap is not a blind spot in Worker 3's instrument so much as a scope difference: most of the 83 belong to **other cards** — `test_library_api.py` carries ~16 that are the Relay-connection card's Decisions, `test_products_api.py` ~11 that are the mutations / optimizer cards', `tests/types/test_base.py` ~11 that are spec-028's and spec-032's. **So the defect is card attribution, not count**: this population cannot be swept by number at all, only resolved site by site against the card whose file it sits in. The two genuinely ambiguous sites Worker 3 named are confirmed: `django_strawberry_framework/utils/inputs.py` lines 1708 and 1733, both `no operator bag, Spec Decision 8`, sit in the shared substrate serving `filters/` and `orders/` and both mean **spec-028** Decision 8 (verified — `docs/SPECS/spec-028-orders-0_0_8.md:723` `### Decision 8 - Cooperation with filtering, get_queryset, and the optimizer` is the section that states "no operator-bag"), not spec-027's.
6. **The out-of-scope table's gap is real and the count is exact.** `examples/fakeshop/test_query/test_products_api.py` carries **5** raw spec-line refs the plan's out-of-scope table never records, at lines 2948, 2984, 3015, 3051, 3098 — #"identical to the `036` model-driven path (line 388)", #"the `036` anonymous denial (line 458)", #"(mirror line 493)", #"(mirror line 528)", #"(mirror line 694)". All five name spec-036 (the mutations card) and sit in that file's `036` form-mutation mirror block, so they are correctly untouched under the card-not-directory scope boundary. They belong in the deferred-work catalog because they will survive every future sweep of a file this slice edited.
7. **Worker 3's item 1 (the Decision 3 Layer 2 citation) is CLOSED, not inherited.** Resolved above by comment retarget; the spec-edit alternative was considered and rejected with a recorded reason. Slice 3 should not re-open it.
