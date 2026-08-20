# Build: Catalog cohort A — wrapped `#"substring"` citations (027)

Spec reference: `docs/SPECS/spec-027-filters-0_0_8.md` `## Non-goals` (the `filters/factories.py` pair) and `### Decision 4 — Upstream-primitives parity floor` (the `types/finalizer.py` site). The other three sites cite other cards: `docs/SPECS/spec-046-transport_security-0_0_14.md` `## Edge cases and constraints` + `### Decision 3` + `### Error shapes` (`consumers.py`, `routers.py` x2) and `docs/SPECS/spec-015-relay_interfaces-0_0_5.md` `### Decision 1: where interfaces are applied` (`types/relay.py`).
Status: final-accepted

## Plan (Worker 1)

### Planning lives in the build plan; this cohort had no Worker 1 pass

The contract is [`build-027-filters-0_0_8.md`][plan] `### Catalog-discharge cohorts (added 2026-08-20, post-commit 8a9840dc)`: cohort A's declared file partition and its catalog items (1 Form A, all 6 sites re-derived; item 4's `routers.py:93` site; item 8 scoped to this cohort's own files). Worker 2 chose the repair text per site; the population and the fence came from the dispatch.

**Ownership partition (declared, disjoint):** `django_strawberry_framework/consumers.py`, `routers.py`, `filters/factories.py`, `types/finalizer.py`, `types/relay.py`, plus this artifact. Cohorts B, C and D and an unrelated spec-028 session ran concurrently; nothing outside the partition was written or reverted.

**The `### Dispatched sites checklist` below was authored by Worker 2**, because the cohort has no Worker 1 planning pass to author it. Flagged for Worker 1's audit: the boxes quote the dispatch brief's own site table plus the two additional dispatched items, and every tick is re-derivable from `### Per-site determinations`.

### DRY analysis

Not applicable, stated plainly rather than skipped silently: the diff contains no executable statement, no helper, no constant, no branch, and no test. There is nothing to share, extract, or de-duplicate. The one repeated shape is the *citation text itself* — `filters/factories.py` cites the same spec Non-goal from two docstrings — and it is deliberately not factored into a named constant: a citation is prose at its point of use, and a shared constant would break the `grep`-from-the-source-line property rule 27 exists to provide. Both sites were nevertheless repaired to the **identical** substring, so a single sweep finds both.

### Dispatched sites checklist

- [x] `consumers.py:887` `# Fail closed (spec-046 Edge cases #"A revalidation database error must` — wrapped
- [x] `routers.py:148` `# #"``websocket_revalidation_window`` is meaningless when a custom class is` — wrapped
- [x] `filters/factories.py:15` `Non-goal (``spec-027`` Non-goals #"Auto-generation of ``FilterSet`` from` — wrapped
- [x] `filters/factories.py:148` `standing deferred Non-goal (``spec-027`` Non-goals #"Auto-generation of` — wrapped
- [x] `types/finalizer.py:1383` `and both resolved target type names per spec-027 #"owning `FilterSet`'s` — wrapped
- [x] `types/relay.py:143` `or hostile-metaclass exception (spec-015 Risk note #"surface any` — wrapped
- [x] `routers.py:93` `# Decision 3 / Error shapes)` — the card, and whether it can be established by measurement
- [x] Item 8, scoped to these five files only: unambiguous build-process provenance in comments (review-round id, slice name, pass name, cycle name)

---

## Build report (Worker 2)

### Files touched

Grounded in `git status --porcelain` and in `git diff` against `git show HEAD:<path>` copies held outside the repo. Seven hunks, all comment / docstring text; `git diff --stat` reads **32 insertions, 32 deletions** across the five files.

- `django_strawberry_framework/consumers.py` — one hunk in `_actor_is_current`: the fail-closed comment reflowed so the `spec-046` citation is unbroken.
- `django_strawberry_framework/routers.py` — two hunks. `_MISSING_DJANGO_APPLICATION_HINT`'s comment reflowed so `(spec-046 Decision 3 / Error shapes)` sits on one line; `_WINDOW_WITH_INJECTED_CONSUMER_HINT`'s comment reflowed **and** its substring retargeted (it resolved to zero).
- `django_strawberry_framework/filters/factories.py` — two hunks, the module docstring and `get_filterset_class`'s docstring: same zero-hit citation, same retarget, reflowed onto one line at both sites.
- `django_strawberry_framework/types/finalizer.py` — one hunk in `_format_owner_target_mismatch_error`'s docstring: reflow only; the substring already resolved uniquely.
- `django_strawberry_framework/types/relay.py` — one hunk in `apply_interfaces`'s `Raises:` clause: retargeted from a moved risk-register sentence to the spec's live Decision 1 contract sentence, reflowed onto one line.

**Everything else in `git status --porcelain`, classified. Nothing was touched or reverted.**

| Path(s) | Owner |
|---|---|
| the five files above | **this cohort** |
| `mutations/fields.py`, `mutations/resolvers.py`, `mutations/sets.py`, `orders/sets.py` | cohort B (`bld-slice-7-027-raw_line_refs.md`) |
| `orders/__init__.py`, `orders/factories.py`, `utils/inputs.py` | cohort C (`bld-slice-8-027-decision_attribution.md`) |
| `docs/SPECS/spec-055-search_fields-0_1_2.md`, `docs/builder/bld-slice-9-027-spec_055_refs.md` | cohort D |
| `docs/builder/build-027-filters-0_0_8.md` | Worker 0 |
| `orders/base.py`, `orders/inputs.py`, `types/base.py`, `docs/SPECS/spec-028-orders-0_0_8.md`, `docs/SPECS/appx/spec-028-orders-0_0_8-rationale.md`, `docs/builder/bld-slice-1-028-*`, `bld-slice-2-028-*`, `build-028-*`, `examples/fakeshop/apps/library/orders.py`, `examples/fakeshop/test_query/test_library_api.py`, `tests/orders/*`, `tests/test_registry.py` | the concurrent spec-028 session, baseline-dirty per the plan's declaration and `AGENTS.md` rule 34 |

All five of this cohort's files were **clean against `HEAD`** when the pass began (`cmp` of each against `git show HEAD:<path>`, five for five), so one baseline suffices and every proof below is against `HEAD` directly.

### Tests added or updated

None. The diff adds no executable statement and no contract, so there is nothing new for a test to pin. The existing suite is the regression check and was run (`### Validation run`).

### Per-site determinations

Every substring was re-derived against the named spec at its current state, **before** editing, with `grep -oF <substring> <spec> | wc -l` — occurrences, not matching lines. Card ids were checked against `docs/SPECS/` by content, not by number.

| # | Site | Cited substring at `HEAD` | Hits | Determination | After |
|---|---|---|---|---|---|
| 1 | `consumers.py::_actor_is_current` | `A revalidation database error must fail closed` | **1** | **resolves** — wrapped only | reflowed unbroken; text unchanged |
| 2 | `routers.py` `_WINDOW_WITH_INJECTED_CONSUMER_HINT` | ` ``websocket_revalidation_window`` is meaningless when a custom class is injected` | **0** | **zero-hit** — two independent causes (below) | retargeted to `#"is meaningless when a custom class"`, **1** hit |
| 3 | `filters/factories.py` module docstring | `Auto-generation of ``FilterSet`` from ``Meta.fields``` | **0** | **zero-hit** — backtick spelling | retargeted to `` #"Auto-generation of `FilterSet`" ``, **1** hit |
| 4 | `filters/factories.py::get_filterset_class` | same as 3 | **0** | **zero-hit**, same cause | same retarget, **1** hit |
| 5 | `types/finalizer.py::_format_owner_target_mismatch_error` | `` owning `FilterSet`'s target `DjangoType` `` | **1** | **resolves** — wrapped only | reflowed unbroken; text unchanged |
| 6 | `types/relay.py::apply_interfaces` | `` surface any `TypeError` as a `ConfigurationError` `` | **0** | **zero-hit** — the sentence left the spec | retargeted to `#"never as a raw layout error"`, **1** hit |

Site-by-site, with the cause and the card check:

1. **`consumers.py`, spec-046.** Spec line 2915, under `## Edge cases and constraints` (2769), so the citation's own heading name holds. Card check: `spec-046` is `transport_security-0_0_14`, which owns WebSocket session revalidation — the behavior the guarded `except` implements. Reflow only.
2. **`routers.py`, spec-046 — zero for two reasons, both measured.** The cited text uses the file's RST idiom (``` ``websocket_revalidation_window`` ```) while the markdown spec uses single backticks; **and** the spec's own sentence wraps mid-phrase (line 2999 ends at "a custom class is", line 3000 opens "injected.**"), so no single line ever carried the full phrase. The retarget `is meaningless when a custom class` is backtick-free and line-internal, occurs **1** time, and sits under `## Edge cases and constraints`, so the citation's heading name still holds. Contract check: spec line 2999-3004 states "The constructor rejects that combination rather than silently ignoring the window — a knob that does nothing is worse than an error. An explicit `0.0` is accepted alongside an injected class" — exactly the comment's two claims.
3, 4. **`filters/factories.py`, spec-027 — zero on backtick spelling.** Spec line 137, under `## Non-goals` (130), reads "**Auto-generation of `FilterSet` from `Meta.fields` without declaring an explicit class.**" — single backticks. Three candidate substrings were measured: `Auto-generation of` (1), `` Auto-generation of `FilterSet` `` (1), and the full clause `` Auto-generation of `FilterSet` from `Meta.fields` `` (1). The middle one was chosen: unique, descriptive enough to identify the bullet, and short enough to sit on one line inside a docstring wrapped at ~70 columns, which the full clause is not. Both sites take the **same** substring so one sweep finds both. Card check: `spec-027` is `filters-0_0_8`, and the cited Non-goal is this card's own.
5. **`types/finalizer.py`, spec-027 — resolves.** `` owning `FilterSet`'s target `DjangoType` `` occurs **1** time, spec line 494, inside `### Decision 4 — Upstream-primitives parity floor` (482). Two shorter variants were rejected for ambiguity, measured rather than assumed: `` owning `FilterSet` `` and `` owning `FilterSet`'s `` occur **2** times each, `` target `DjangoType` `` **8** times. The cited form is already the unique one, so this is a reflow with no text change.
6. **`types/relay.py`, spec-015 — zero because the sentence left the spec.** The cited phrase occurs **0** times in `docs/SPECS/spec-015-relay_interfaces-0_0_5.md`, and the spec carries no "Risk" heading at all: the risk register was moved to `docs/SPECS/appx/spec-015-relay_interfaces-0_0_5-rationale.md` by that card's rationale extraction. That companion's own addendum records this exact citation as a known casualty and reports it "**not** restored to the spec — the sentence belongs to the moved risk register", quoting it verbatim so the citation resolves inside the companion. Two options, both measured:
   - **retarget to the companion** — rejected. The phrase occurs **2** times there (the addendum's disposition table quotes it, and the verbatim bullet carries it), so it fails rule 27's uniqueness without being extended to include surrounding words that only exist in one of the two.
   - **retarget to the spec's own live statement of the same contract** — chosen. Spec line 237, inside `### Decision 1: where interfaces are applied` (232), reads "A `TypeError` from the base assignment — Python rejecting the resulting MRO or instance layout — is surfaced as a `ConfigurationError` naming the offending interface, never as a raw layout error." That is precisely what the docstring's `Raises:` clause claims. `never as a raw layout error` occurs **1** time; the alternative anchor `naming the offending interface` occurs **2** and was rejected on that measurement.

   The heading was corrected with the substring: `Risk note` no longer exists, `Decision 1` does. The card is right — `spec-015` is `relay_interfaces-0_0_5`, and this file's six other `spec-015` citations all resolve (`### Post-edit resolution sweep`).

### `routers.py:93` — the card IS named; the defect is the same wrap

The dispatch brief reports this site as carrying `# Decision 3 / Error shapes)` "with no card named, so a reader cannot resolve which spec's Decision 3 it means". **Measured, that premise does not hold**, and the correction is worth stating because it is the same instrument artifact this whole cohort exists to repair: line 92 ends `...``django_application`` (spec-046` and line 93 opens `# Decision 3 / Error shapes).` The card is named — on the previous line. A line-scoped read cannot see it, exactly as a line-scoped read cannot see a wrapped `#"..."`.

So no card id was invented and none had to be inferred. Both targets were verified anyway: `### Decision 3 — \`django_application\` is required; omission fails at construction with no compatibility fallback` is spec-046 line 993, and `### Error shapes` is line 863 — and Decision 3 itself points at the same section ("with the message shape in [Error shapes](#error-shapes)"), so the pairing in the comment is the spec's own. The repair is the reflow: `(spec-046 Decision 3 / Error shapes)` is now unbroken on one line.

### Item 8 — build-process provenance in these five files: population **0**

Swept, not assumed. Three greps over the five files, case-insensitive:

- the dispatch's own vocabulary — `review round|round N|rev-NN|slice N|pass N|worker N|adversarial|closeout|R1|this cycle|build cycle|bld-`;
- narration vocabulary — `this pass|prior pass|feedback|the reviewer|a review|revision|as of <date>|history|historically|originally|previously|was added|landed in/with/ahead|during the build|integration pass|audit pass`;
- artifact-path vocabulary — `docs/review|docs/builder|docs/dry|TODO(|Worker|cohort|dispatched by|per the review`.

Three candidates surfaced and all three were rejected on reading, none of them members of the class:

- `filters/factories.py` "the cache plumbing was landed ahead of that consumer" and "Built-and-tested ahead of that consumer" — states the current state of Layer 6 (machinery with no source consumer), which is load-bearing for the reader; names no round, slice, pass, or cycle.
- `types/finalizer.py::_audit_secondary_model_label_collapse` "This pass only warns about the legal-but-surprising collapse" — "pass" here is the **finalization** pass, i.e. the function itself, contrasted with its hard-error sibling in the previous sentence. Runtime vocabulary, not build vocabulary.
- `consumers.py` "the first then emit its previously ..." — frame-ordering prose.

The `Subpass 1..4` / `subpass 2.5` labels throughout `types/finalizer.py` (17 occurrences) are likewise the finalizer's own algorithm phases, named in both the spec and the code, and are not provenance. Nothing was rewritten for item 8, and the fence was not widened.

### Validation run

Every command from the repository root. `pre-commit` is not on `PATH`; the config header names `uvx`.

| Check | Command | Result |
|---|---|---|
| Format (scoped, never `.`) | `uv run ruff format <the five files>` | `5 files left unchanged`, exit **0** |
| Lint (scoped) | `uv run ruff check --fix <the five files>` | `All checks passed!`, exit **0** |
| Source layout / ASCII-only | `uv run python scripts/check_trailing_commas.py --check <the five files>` | exit **0** |
| Citation gate | `uv run python scripts/check_citations.py` | `OK: 772 citations resolve (695 in 422 .py files, 77 in KANBAN.md).` exit **0** |
| Hooks | `uvx pre-commit run --files <the five files>` | all five hooks **Passed** (kanban tracked path constants; source layout; ruff format; ruff check; citations resolve) |
| Churn classification | `git status --porcelain` before and after | see `### Files touched`; no unexpected churn, nothing reverted |
| Focused tests | `uv run pytest tests/test_routers.py tests/types tests/filters tests/test_registry.py examples/fakeshop/test_query/test_transport_api.py --no-cov -q` | **1356 passed in 21.96s** |

No `--cov*` flag was used anywhere.

**On the citation gate's count, honestly.** 772 / 695 is higher than the 742 / 665 the prior cohort recorded, and this pass cannot claim the delta is not its own by pointing at a number it never measured before editing. What it can do is measure its own contribution directly, which is the stronger check: the `path::Symbol` citation count per file is **identical** to `HEAD` for all five files (20 / 6 / 5 / 3 / 5), and so is the `#"` substring-citation count (3 / 1 / 2 / 7 / 8). This pass therefore added and removed **no** citation of either form; the gate's growth belongs to the three concurrent cohorts, whose files are in the same repo-wide scan.

**Focused-scope justification, from the importing surface.** `grep -rln` over `tests/` and `examples/` for `consumers|routers|DjangoGraphQLProtocolRouter` and for `types.finalizer|finalize_django_types|types.relay|filters.factories|FilterArgumentsFactory|get_filterset_class` names the importers. The scope above takes the direct mirror of each touched module — `tests/test_routers.py` (routers + consumers construction seam), `examples/fakeshop/test_query/test_transport_api.py` (the live WebSocket transport surface those two modules implement), `tests/types/` (finalizer + relay, including `test_relay_interfaces.py`, which exercises `apply_interfaces`), `tests/filters/` (the factories mirror), and `tests/test_registry.py` (the registry lifecycle that drives finalization). It deliberately excludes `tests/orders/` and the library live tests: those are baseline-dirty with the concurrent spec-028 session's work, so a failure there would be unattributable, and no order-side surface is in this diff.

### Census, precondition and postcondition

The instrument is the dispatch's own: a per-line pass over every package `.py` file flagging each `#"` with no closing `"` later on the same line. Script under this session's scratchpad, outside the repo.

| Run | Scope | Wrapped citations |
|---|---|---|
| Precondition, re-derived before any edit | `django_strawberry_framework/` (108 files) | **6** — the same 6 sites and line numbers the dispatch brief tabled |
| Postcondition | `django_strawberry_framework/` (108 files) | **0** |
| Postcondition, this cohort's files alone | the five files | **0** |
| Control | the five `git show HEAD:` copies, re-scanned after the edits | **6** — the instrument still finds them, so the 0 above is the tree changing, not the instrument breaking |

The control row is the point: a postcondition of 0 from an instrument that has silently stopped matching is worthless, so the same script was pointed at the pristine copies in the same run.

**Two further wrapped citations exist outside the package and outside this fence**, recorded for whoever owns them rather than repaired: `tests/test_relay_connection.py:2591` (`` walker.py::_plan_connection_relation #"resolver_key(type_cls, `` ...) and `examples/fakeshop/apps/kanban/schema.py:359` (`` optimizer/walker.py #"if `` ...). The dispatch's population was package `.py` only; both are in another cohort's or another card's surface. (`scripts/build_kanban_md.py` and `scripts/prove_failability.py` also match the naive pattern, but those are `"#"` string literals in code, not citations — a false-positive class the reader should know the instrument has.)

### Post-edit resolution sweep

Every `#"..."` citation in the five files, re-extracted with a tokenizing sweep that flattens each run of consecutive `COMMENT` tokens and each `STRING` token whole before matching — so a wrapped citation is still extracted and reported as wrapped — then resolved by occurrence count against the spec or path its own block names.

| File | substring citations | resolving to exactly 1 | wrapped |
|---|---|---|---|
| `consumers.py` | 3 | 2 + 1 unresolved-target (below) | 0 |
| `routers.py` | 1 | 1 | 0 |
| `filters/factories.py` | 2 | 2 | 0 |
| `types/finalizer.py` | 7 | 7 | 0 |
| `types/relay.py` | 8 | 7 + 1 unresolved-target (below) | 0 |

The two "unresolved target" rows are instrument limits, not defects, and both are pre-existing at `HEAD`: `consumers.py` #"join(value) for name" names no path or card inside its own bullet (the target is Django's ASGI header adapter, named earlier in the same docstring), and `types/relay.py`'s `` strawberry_django/relay/utils.py::resolve_model_nodes #"def map_results" `` points at the upstream checkout at `~/projects/strawberry-django-main`, outside this repo. Neither is wrapped and neither is in this cohort's item set; both are left alone.

### Failability proofs

None; this pass introduced no new boundary.

Discharged mechanically rather than on prose: the executable-token identity below shows the diff contains no statement, branch, guard, comparison, or `raise` for the mandatory floor to select.

### Executable-token identity, and the challenge set that earns it

`tokenize` each file; drop `COMMENT`, `NL`, `NEWLINE`, `INDENT`, `DEDENT`, `ENCODING`, `ENDMARKER`, and every **statement-position** `STRING` (a bare string expression statement, i.e. a docstring); compare the remaining `(type, string)` sequence against `git show HEAD:<path>`. A `STRING` in any other position — a call argument, an assignment RHS, a dict value — is **kept**, so a changed module path inside a call is a divergence rather than a silent pass. No `git checkout` / `git stash` / `git restore` / `git worktree` was used.

| File | Verdict vs `HEAD` | Exec tokens |
|---|---|---|
| `django_strawberry_framework/consumers.py` | **IDENTICAL** | 1750 |
| `django_strawberry_framework/routers.py` | **IDENTICAL** | 832 |
| `django_strawberry_framework/filters/factories.py` | **IDENTICAL** | 232 |
| `django_strawberry_framework/types/finalizer.py` | **IDENTICAL** | 5567 |
| `django_strawberry_framework/types/relay.py` | **IDENTICAL** | 2367 |

**Challenge set.** Six mutations, each applied to a copy outside the repo (never to the production file, so no mutation ever sat in a tree three other sessions are writing), each landing confirmed by `diff` before the instrument was run, and each **expected verdict asserted before the verdict was read**.

| Case | Mutation | Asserted | Measured |
|---|---|---|---|
| 1 — operator flip | `consumers.py` `if window > 0.0` -> `if window >= 0.0` | DIVERGENT | **DIVERGENT**, index 707: `(OP, '>')` != `(OP, '>=')` |
| 2 — inserted statement | `factories.py` + `_CHALLENGE_INSERTED = 1` at class-body top | DIVERGENT | **DIVERGENT**, 232 vs 235 tokens, index 70 |
| 3 — deleted statement | `factories.py` - `_collision_registry_attr = "_type_filterset_registry"` | DIVERGENT | **DIVERGENT**, 232 vs 229 tokens, index 98 |
| 4 — docstring rewrite | `factories.py::FilterArgumentsFactory._build_input_triples` docstring replaced wholesale | IDENTICAL | **IDENTICAL**, 232 vs 232 |
| 5 — comment rewrite | `factories.py` "Layer 6 -- dynamic-FilterSet cache" banner comment replaced wholesale | IDENTICAL | **IDENTICAL**, 232 vs 232 |
| 6 — **non-statement-position string** | `factories.py` `make_dynamic_set_getter(auto_name_suffix="AutoFilter", ...)` -> `"AutoFilterX"` | DIVERGENT | **DIVERGENT**, index 182: `'"AutoFilter"'` != `'"AutoFilterX"'` |

Six for six. Case 6 is the one a naive statement-position filter — or a filter that drops *every* `STRING` — reports as identical while a real behavior change (a generated class-name suffix on the public dynamic-FilterSet surface) sails through; cases 4 and 5 are what stop the instrument from being vacuously strict. The pair is why the verdict table above is evidence rather than an assertion.

### Hot-path budget

Not applicable; the dispatch declares no hot path, and executable-token identity means nothing executes differently.

### Floor verification

Not applicable; the dispatch declares floor-verification scope none, and a comment-only diff touches no Django / Strawberry / channels seam.

### Implementation notes

- **A citation quotes its target's own spelling, so the backtick count is part of the anchor.** Two of the three zero-hit sites failed for nothing but that: the `.py` files use RST double backticks, and a markdown spec uses single ones. Every repaired substring now reproduces the spec's own characters, which is why they resolve; where a single-backtick fragment now sits inside a double-backtick paragraph it looks slightly foreign, and that is deliberate — matching the paragraph would break the anchor again. Precedent for the mixed spelling is `types/finalizer.py`'s untouched `` #"owning `FilterSet`'s target `DjangoType`" ``.
- **Retarget over drop-to-heading, everywhere it was possible.** The dispatch licensed dropping `#"..."` and citing the heading alone when no unique substring exists. That case never arose: all three zero-hit sites had a unique, line-internal, backtick-faithful substring available in the live spec. Every repaired citation therefore still pins a *sentence*, not just a section, which is what makes a reword detectable next cycle.
- **`relay.py` cites the spec, not the rationale companion, even though the companion holds the original words.** The companion's own record says the sentence was deliberately not restored to the spec because it is deliberation. A shipped docstring's `Raises:` clause should cite the **contract**, and spec-015 Decision 1 states that contract in one sentence; citing the deliberative companion would also have needed an extended substring to beat the 2-occurrence ambiguity there.
- **Minimal reflow, but reflow was unavoidable.** A wrapped citation cannot be repaired without moving a line break, so each hunk re-wraps only its own paragraph and leaves the enclosing comment/docstring alone. Line widths were matched to what each file already uses (~78 for `consumers.py`/`routers.py` comments, ~70 for the `factories.py` docstrings, ~74 for the `finalizer.py` docstring); the widest line this pass writes is 94 characters, under the 99-column limit, and `ruff format` left all five files unchanged.
- **`consumers.py` keeps its citation on the hunk's first line at 94 columns rather than being re-wrapped narrower.** Splitting that line is the only way to make it look like its neighbours, and splitting it is the defect.

### Notes for Worker 3

- **The scratchpad is shared across cohorts, and it cost this pass an instrument.** The dispatch handed every cohort the same scratchpad path, so a first `census_027.py` was silently overwritten by a different cohort's file of that name mid-pass — the failure surfaced as a traceback from *someone else's* code and a hardcoded file list. Everything this pass relies on was rebuilt under a private `cohortA-027/` subdirectory. A reviewer re-running any cohort's script by filename should assume the name may now hold another cohort's content, and re-derive rather than re-run.
- **The dispatch brief's `routers.py:93` framing is wrong, and its wrongness is this cohort's own defect class** (`### routers.py:93` above). The card was already named, one line up. Nothing was invented; the fix was the same reflow.
- **The census has a documented false-positive class** — `"#"` as a string literal in code (`scripts/build_kanban_md.py`, `scripts/prove_failability.py`) — and a documented blind spot it does *not* have: it flags `#"` at the start of a comment line, which an instrument that strips leading `#` markers misses. Both are recorded under `### Census`.
- No shadow file was used. `scripts/review_inspect.py` was **skipped**: this pass adds no logic, and the helper's `<stem>.stripped.py` replaces every comment and string-literal token with `...`, so its output is provably invariant under this diff — the executable-token identity table is the mechanical evidence for the skip.
- The `#"` shape at line-start now appears nowhere in this cohort's files: every repaired citation sits mid-line after its heading name, so a `#`-stripping resolver cannot mangle it either.

### Notes for Worker 1 (spec reconciliation)

No spec-027 edit is needed for anything this pass landed; every repaired citation was made to fit the spec as it stands. Two items concern surfaces fenced from this cohort.

- **`docs/SPECS/appx/spec-015-relay_interfaces-0_0_5-rationale.md`, `### Four \`#"unique substring"\` anchors the reconciliation retired, and seven citations that quote them`, the fourth table row.**
  - Current wording: "**not** restored to the spec — the sentence belongs to the moved risk register, and putting deliberation back would undo the move. Quoted verbatim below instead, so the citation resolves inside this companion."
  - Recommended replacement: "**not** restored to the spec — the sentence belongs to the moved risk register, and putting deliberation back would undo the move. Quoted verbatim below for the record; the shipped citation in `types/relay.py::apply_interfaces` now anchors on Decision 1's `never as a raw layout error`, which states the same contract and occurs once, because the phrase occurs **twice** in this companion and so cannot satisfy rule 27's uniqueness here."
  - Reason: the row's stated remedy does not work as stated. Quoting the phrase verbatim *below* the row that also quotes it makes the companion carry it twice, so a citation aimed at the companion is ambiguous — measured, not inferred: `grep -oF` returns **2**. The disposition (do not restore deliberation to the spec) is right and is unaffected; only the claim that the citation resolves here is wrong. `spec-015` and its companion belong to another card, so this is recorded rather than edited.
- **`docs/SPECS/spec-046-transport_security-0_0_14.md`, `## Edge cases and constraints`, the bullet beginning "**A positive `websocket_revalidation_window` is meaningless when a custom class is".**
  - Current wording: the bullet's bolded lead wraps mid-phrase across two source lines ("... when a custom class is" / "injected.** ...").
  - Recommended replacement: re-wrap the bullet so the bolded sentence "A positive `websocket_revalidation_window` is meaningless when a custom class is injected." sits on one source line.
  - Reason: not cosmetic. A spec sentence shipped source quotes is an interface, and a sentence that wraps mid-phrase can only be cited by a fragment of itself — which is exactly the compromise `routers.py` now carries (`is meaningless when a custom class`, cut at the source line's end rather than at a natural clause boundary). Re-wrapping would let the citation name the whole claim. `spec-046` is another card's spec, so this is recorded rather than edited.

### Deliberately not done

- **No repair outside the five-file partition**, including the two wrapped citations in `tests/test_relay_connection.py` and `examples/fakeshop/apps/kanban/schema.py`, and the two unresolved-target citations that are pre-existing at `HEAD`. Recorded above with their locations.
- **No item-8 rewrite**, because the measured population in these files is 0. Three candidate sentences were examined and rejected with reasons rather than being silently passed over.
- **No `spec-046` or `spec-015` edit**, and no edit to the `spec-015` rationale companion: both are other cards' surfaces. Routed to `### Notes for Worker 1` with quoted current wording and recommended replacements.
- **No `--cov*` run, no `pytest` beyond the justified focused scope, no repo-wide `ruff` write mode, and no `git stash` / `checkout` / `restore` / `worktree` / `add` / `commit`.**

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

[plan]: build-027-filters-0_0_8.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
