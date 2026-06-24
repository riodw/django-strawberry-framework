# Spec: `DjangoListField` (non-Relay list)

Target release: `0.0.7`.
Status: draft (revision 6, post-rev5 scaffolding review).
Owner: package maintainer.
Predecessors: [`docs/GLOSSARY.md`][glossary] (entries [`DjangoType`][glossary-djangotype], [`Meta.fields`][glossary-metafields], [`get_queryset` visibility hook][glossary-get-queryset-visibility-hook], [`DjangoOptimizerExtension`][glossary-djangooptimizerextension], [`Relation handling`][glossary-relation-handling], [`Meta.primary`][glossary-metaprimary], [`Relay Node integration`][glossary-relay-node-integration], [`DjangoListField`][glossary-djangolistfield]), [`KANBAN.md`][kanban] card `DONE-020-0.0.7` (was `DONE-020-0.0.7` until Slice 5's column move), predecessor spec [`docs/SPECS/spec-015-relay_interfaces-0_0_5.md`][spec-011] (Decision 9 — async `get_queryset` shape) and [`docs/SPECS/spec-018-meta_primary-0_0_6.md`][spec-014] (multiple `DjangoType`s per model).
(Rev3 M2: the `Card line:` block that previously appeared here was removed — the quoted sentence was not verbatim from the KANBAN card body; the card is now cited by ID only on the Predecessors line.)

Revision history (kept inline so the spec is self-contained):

- **Revision 1** — initial draft. Pins module location (`list_field.py`), symbol shape (field-descriptor class with `__call__` semantics that returns a `StrawberryField`), default-resolver contract (`Meta.model._default_manager.all()` → `cls.get_queryset(qs, info)`), sync + async `get_queryset` cooperation (mirroring [spec-011][spec-011] Decision 9 verbatim), consumer-resolver override semantics, optimizer cooperation (root-gating, no new walker code), `Meta.primary` interaction (the explicit-`DjangoType`-argument resolves the registry ambiguity), public-export discipline, test placement across `tests/test_list_field.py` + `examples/fakeshop/test_query/test_library_api.py`, and the library-app boilerplate-removal proof.
- **Revision 2** (post-feedback review) — three high-severity corrections plus three medium and two low cleanups; all surfaced in [`docs/feedback.md`][feedback] against revision 1:
  1. **H1**: rev1's "Custom resolver override" said a consumer-supplied `resolver=` owns the queryset completely and `cls.get_queryset(...)` is NOT applied automatically, claiming graphene-django parallelism. The graphene-django source actually applies `get_queryset` to a `QuerySet` (or `Manager`) returned by a consumer resolver too — `graphene_django/fields.py::DjangoListField.list_resolver` calls `maybe_queryset(django_object_type.get_queryset(queryset, info))` on any `QuerySet`, not only the default-manager fallback. Fix: flip the contract to graphene-django parity — apply `target_type.get_queryset(...)` to any `Manager`/`QuerySet` returned by the consumer resolver, NOT only the default manager. Consumer resolvers that want to bypass `get_queryset` return a Python `list` (already-evaluated) instead of a queryset; the field detects this and passes the list through unchanged, the same way `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._optimize #"if not isinstance(result, models.QuerySet):"` does. New Slice 3 test pins the new contract: `test_djangolistfield_consumer_resolver_queryset_return_gets_get_queryset_applied`. Removed test: `test_djangolistfield_consumer_resolver_override_bypasses_default` (the old contract); replaced with the new test. Updated Decision 2 "Custom resolver override" subsection; updated User-facing API; updated Borrowing posture's `maybe_queryset` bullet to correctly cite the graphene-django behavior; updated the Slice 1 checklist resolver-body sub-bullet.
  2. **H2**: rev1's "subclass `strawberry.field`" mechanic is not implementable — `strawberry.field` in the installed Strawberry version is a function, not a class. Rev1 also said `DjangoListField` returns a `StrawberryField` from `__set_name__`, but `__set_name__` cannot replace the already-assigned class attribute with its return value. Fix: rewrite Decision 1 + Decision 2 around one concrete mechanism — `DjangoListField` is a **factory function** that returns `strawberry.field(resolver=..., description=..., ...)`. Consumer usage stays `all_branches: list[BranchType] = DjangoListField(BranchType)` — Strawberry reads the consumer's class-attribute annotation for the outer GraphQL type shape (so `list[BranchType]` → `[BranchType!]!` and `list[BranchType] | None` → `[BranchType!]`); the field factory only owns the resolver wiring. Constructor signature loses `nullable_list=` (the consumer's annotation drives it). Updated Slice 1 and Slice 2 checklists; updated Decision 1 (mechanism subsection); updated Decision 2 (resolver shape + return-type story); dropped `test_djangolistfield_nullable_list_toggle_renders_nullable_outer` and added `test_djangolistfield_nullable_outer_via_consumer_annotation` and `test_djangolistfield_non_nullable_outer_default_via_consumer_annotation` in its place; updated Decision 5 to drop the `nullable_list` bool check.
  3. **H3**: rev1's default-resolver pseudocode `def _default_resolver(type_cls, info)` passes the target `DjangoType` class as the first argument, but Strawberry calls a field resolver with `(root, info, **kwargs)` — the GraphQL root/parent value, not the target type class. As written, `type_cls.__django_strawberry_definition__` would look up the attribute on the `Query` root instance and fail. Fix: capture `target_type` via closure inside the factory function; the resolver signature is the Strawberry-native `(root, info, **kwargs)`. Same fix for the custom resolver example in the User-facing API. Updated Decision 2 pseudocode and the User-facing API examples.
  4. **M1**: rev1's Decision 9 picks `all_library_branches` as the resolver to replace, but that resolver carries `order_by("id")` and the live HTTP test `test_library_relation_override_shapes_http_response_data` in `examples/fakeshop/test_query/test_library_api.py` asserts a deterministic branch order ("Override" before "Override East"). `Branch` has no model-level `Meta.ordering` in `examples/fakeshop/apps/library/models.py`; the default-manager queryset is unordered. Three options were considered: (a) keep `all_library_branches` as `@strawberry.field` and **add** a new sibling field `all_library_branches_via_list_field: list[BranchType] = DjangoListField(BranchType)` that exercises `DjangoListField` independently; (b) use `DjangoListField(BranchType, resolver=...)` with a consumer resolver preserving `order_by("id")` (now safe under the H1 contract because `get_queryset` still applies); (c) add `class Meta: ordering = ("id",)` to `Branch`. Rev2 picks **option (a)** — adds a new field rather than replacing an existing one; zero blast radius on the existing HTTP tests; the new field exercises the default-resolver code path cleanly without the ordering coupling. Updated Decision 9, the Slice 4 checklist, and the Test plan; updated the implementation-plan delta table's Slice 4 row.
  5. **M2**: rev1's live HTTP test plan said "assert `cls.get_queryset` was applied (e.g., the library example's `get_queryset` filter, if added for this test)" — but adding a custom `get_queryset` to `BranchType` changes every `BranchType` path in the library schema (including nested `book → shelf → branch` selections and the existing branch tests). Fix: move `get_queryset` application coverage entirely to package-internal `tests/test_list_field.py`, where a fresh `DjangoType` fixture can declare an isolated `get_queryset`; the live HTTP test in `examples/fakeshop/test_query/test_library_api.py` proves only the end-to-end pipeline (URL routing, view, schema execution) and the optimizer cooperation (planned `select_related` / `prefetch_related` via `assertNumQueries`). Updated Slice 4 checklist and Test plan.
  6. **M3**: rev1 said the contract is for "root and nested fields" but the optimizer extension is explicitly root-gated on `info.path.prev is None` (`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.resolve #"if info.path.prev is not None:"`). A `DjangoListField` used on a nested non-root Strawberry type would be a functional list resolver but would NOT be planned by the existing optimizer hook. Fix: narrow the `0.0.7` contract to **root list fields only**. Goals 1-5, the User-facing API, Decisions 2 and 4, the CHANGELOG entry, the doc-updates section, the Definition of done, and the User-facing description all say "root" — never "nested". A new Decision 4 paragraph says nested non-root usage is functional (the field still produces a list resolver) but is NOT root-optimized in `0.0.7`; the connection card (`DONE-030-0.0.9`) or a follow-up spec can revisit nested optimization. A new test in `tests/test_list_field.py` pins this: `test_djangolistfield_at_root_position_is_optimized`.
  7. **L1**: rev1's Doc updates section adds `list_field.py` to the target on-disk layout in `docs/TREE.md` but doesn't remove the stale `DjangoListField` mention on the existing `connection.py # [alpha] [DjangoConnection][glossary-djangoconnection]Field + DjangoListField` line. Fix: add a Slice 5 doc-updates bullet that removes `DjangoListField` from the `connection.py` line in the target layout so the docs don't advertise two homes for the symbol.
  8. **L2**: rev1's CHANGELOG entry says "non-Relay `list[T]` field for root and nested fields"; after the M3 scope narrowing, this becomes stale and over-promises. Fix: change the bullet to "non-Relay `list[T]` field for **root** Query fields" so the release note matches what is tested and shipped.
- **Revision 3** (post-rev2 review against `feedback2.md`) — the reviewer audited the rev1 draft (not the rev2 update), so several feedback2 items had already been pre-empted by rev2; the rest land here as one high, six medium, and two low corrections:
  1. **(feedback2 H1 — pre-empted by rev2 M1.)** The reviewer flagged that `all_library_branches` carries `order_by("id")` and the rev1 replacement would have dropped it. Rev2 M1 already switched strategy from "replace `all_library_branches`" to "add new sibling `all_library_branches_via_list_field`", so no existing resolver is touched and no ordering is dropped. The new field has no `order_by`, but its HTTP test is order-agnostic (sort by `id` in the assertion — already named in [Decision 9](#decision-9--example-app-migration-posture)). No additional rev3 work required.
  2. **(feedback2 H4 — pre-empted by rev2 H2.)** The reviewer flagged the annotation-vs-`nullable_list=` ambiguity. Rev2 H2 already dropped `nullable_list=` as a constructor argument; outer nullability is solely driven by the consumer's class-attribute annotation. No additional rev3 work required.
  3. **(feedback2 L1 + L4 — pre-empted by rev2 H2.)** The reviewer flagged the `__call__` semantics wording and the `nullable_list` bool-check test recipe. Rev2 H2 already rewrote both — the factory-function shape replaced the `__call__` wording, and the `nullable_list` bool-check test was removed entirely. No additional rev3 work required.
  4. **H1 (feedback2 H3 — partial follow-up to rev2 H2).** Rev2 H2 pinned the factory-function shape (`DjangoListField(...)` returns the value of `strawberry.field(resolver=..., ...)`), and the rev2 Risks entry notes the shape was verified against the installed Strawberry. But the reviewer correctly points out the spec is still sized against an integration mechanism that hasn't been demonstrated end-to-end in this codebase — every example, test, and slice rests on `@strawberry.type` picking up the factory's return value via Strawberry's normal class-attribute discovery. Fix: add a **Slice 0 — Pre-implementation verification** to the [Slice checklist](#slice-checklist) that authors a 10-line `DjangoListField` stub returning `strawberry.field(resolver=lambda root, info: ...)`, assigns it to a Query attribute under `@strawberry.type`, builds a Strawberry schema, and confirms the field appears with the expected GraphQL shape — BEFORE Slice 1 touches `list_field.py` for real. If the factory return value is NOT picked up cleanly, the Risks fallback (directly construct a `StrawberryField` with explicit `python_name` / `type_annotation`) is promoted to Decision 1 and Slice 1 reauthored. Slice 0 has no test commitment and no production code; it's a 10-minute spike at the top of the implementation that de-risks every other slice. Updated [Implementation plan](#implementation-plan) table — Slice 0 has zero line delta (the spike is thrown away after confirmation).
  5. **M1 (feedback2 H2).** The spec uses the term "the joint `0.0.7` cut card" repeatedly (Slice 5 checklist, Definition of done, Decision 10, Risks). There is no separate "joint cut card" in `KANBAN.md` — the five WIP cards (`016`, `017`, `018`, `019`, `045`) are all feature cards; the spec wording invites a reader to look for a sixth card that doesn't exist. Fix: reword every "the joint `0.0.7` cut card" reference to "**the last `0.0.7` card to ship**" so the policy is named without inventing a phantom card. The Decision 10 heading stays "Joint `0.0.7` cut" because it describes the policy, not a card. Five sites updated: Slice 5 checklist, Decision 10 body (×2), Doc updates CHANGELOG bullet, Definition of done item 18. (Adding a real release-cut card to `KANBAN.md` is a separate change that belongs in a follow-up edit to `KANBAN.md`, not this spec — and the rev1 boundary explicitly forbids `KANBAN.md` edits from this spec.)
  6. **M2 (feedback2 M1).** The Spec preamble's `Card line:` block (now removed; previously placed just below the Predecessors line) had the quote in markdown link form — the quoted sentence is not verbatim from the `DONE-020-0.0.7` card body (the card has Why-it-matters bullets, Verified-in-upstream, Definition of done, Files-likely-touched — no one-line summary matching the quoted text). The spec's voice is one of high-fidelity citation; the misattribution stands out. Fix: drop the false quote and cite the card by ID only — the Predecessors line already references the card. Removed the entire `Card line:` block.
  7. **M3 (feedback2 M2).** Decision 5's "registered DjangoType" check (`hasattr(arg, "__django_strawberry_definition__")` is a sufficient discriminator) needs a code-citation anchor. Fix: add a one-line note pointing at `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__ #"cls.__django_strawberry_definition__ = definition"` (the assignment site) so readers don't have to grep to verify the discriminator shape is correct.
  8. **M4 (feedback2 M3).** Several line-number citations are off by 1-2 in rev1/rev2. Verified against `HEAD`: `types/relay.py::_apply_get_queryset_sync` start was off by one (spec was a line later than the actual definition); `types/relay.py::_apply_get_queryset_async` start was likewise off by one; `optimizer/extension.py::DjangoOptimizerExtension._optimize` start was as the spec wrote it (the reviewer's claim was off). The `isinstance(result, models.Manager)` check inside `_optimize` and the `.all()` coercion are both present (the spec's range citation was right). `optimizer/extension.py::_resolve_model_from_return_type` is **defined** at module scope and **called** inside `_optimize` — the spec reads as if the call site is the definition; clarify it's the call site. Fix: sweep the citation block — the previously-misaligned `_apply_get_queryset_sync` range citation becomes the symbol-qualified `django_strawberry_framework/types/relay.py::_apply_get_queryset_sync`; the `raise ConfigurationError` sub-range becomes `django_strawberry_framework/types/relay.py::_apply_get_queryset_sync #"raise ConfigurationError"` (the `raise ConfigurationError` block is shorter than the spec implies); the previously-misaligned `_apply_get_queryset_async` range citation becomes `django_strawberry_framework/types/relay.py::_apply_get_queryset_async`; `_resolve_model_from_return_type` references that read as "definition" become "the helper, called inside `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._optimize #"resolved = _resolve_model_from_return_type(info)"`, is defined at `django_strawberry_framework/optimizer/extension.py::_resolve_model_from_return_type`". Decision 7's `_resolve_model_from_return_type` mention gets the same clarification. Leave correct citations alone (`info.path.prev` check inside `resolve`, `DjangoOptimizerExtension.resolve` body, `DjangoOptimizerExtension._optimize` body, `_resolve_model_from_return_type` definition site).
  9. **M5 (feedback2 M4).** The repo's `CHANGELOG.md` already has a `[0.0.7]` section from prior commits this patch. Slice 5's Doc updates section says "`[0.0.7]` `### Added`: ..." without clarifying append-vs-create. Fix: tighten the bullet to "**Append** to the existing `[0.0.7]` `### Added` subsection; do not create a second `[0.0.7]` heading." Same caveat applies to every `0.0.7` card under the joint cut.
  10. **M6 (feedback2 M5).** Decision 4 says the slice MUST add an optimizer-side test to `tests/test_list_field.py` AND Slice 4 routes the same coverage through the live HTTP test in `examples/fakeshop/test_query/test_library_api.py`. The reviewer flags this as potentially duplicative against `AGENTS.md`'s "Test through real usage" rule. The duplication IS intentional but the spec doesn't justify it: the HTTP test exercises ONE selection shape end-to-end (regression net for "does it work via real GraphQL?"); the package-internal test exercises the contract that the default resolver returns a `QuerySet` (regression net for "did we accidentally return a list?"). Both fail modes can fly past each other in different ways. Fix: keep both tests; add an explicit justification paragraph to [Decision 4](#decision-4--optimizer-cooperation) saying the package-internal test pins the **return-shape** contract while the HTTP test pins the **end-to-end** contract — different regression risks. Drop the prose "this is the regression net against accidentally returning a `list`" wording in favor of the two-fold framing.
  11. **M7 (feedback2 M6).** The `in_async_context` import path is implied but not pinned. The actual path in the installed Strawberry is `from strawberry.utils.inspect import in_async_context` (verified at `django_strawberry_framework/types/relay.py #"from strawberry.utils.inspect import in_async_context"`). Fix: pin the import line in Decision 3 (and in the Slice 1 checklist sub-bullet that mentions the helper) so the reader doesn't have to grep `types/relay.py` to find it. Same import path is reused — no fork.
  12. **L1 (feedback2 L3).** Decision 9's "21 lines for cosmetic gain" wording is arithmetically loose — replacing seven 3-line resolvers with seven 1-line attributes is a -14 line delta, not a +21 line one. Rev2 already rewrote Decision 9 substantially, but the "21 lines" wording is now an "Alternatives considered" line; drop the loose count and just say "churn that doesn't pin the contract any harder than one addition does."
  13. **L2 (feedback2 L5).** The Risks section currently lists eight open questions; some restate Decisions in different words. Rev3 folds three risks into the relevant Decision's "Alternatives considered" block and trims the Risks section to the genuinely open items: (a) the Slice 0 verification outcome (was risk #3); (b) the consumer-resolver `get_queryset` contract (was risk #4 — pre-empted by rev2 H1, kept short); (c) async support helper relocation (was risk #5 — kept). The "ergonomics of explicit-target shape", "null=True on item type", and "DjangoListField(model_class) sugar" items move to Decision 6's Alternatives. Net: Risks section drops from 8 items to 4.
  14. **(feedback2 L2 — no action.)** The reviewer's L2 was a confirmation that the test counts are internally consistent, not a defect. No edit needed.
- **Revision 4** (post-rev3 review against the second pass of [`docs/feedback.md`][feedback]) — three high-severity corrections plus two medium and one low, all surfaced after a closer audit against the installed Strawberry behavior and the live KANBAN card body:
  1. **H1**: rev3's resolver pseudocode and User-facing API examples use `def resolver(root, info, **kwargs)` with `info` unannotated. In the installed Strawberry version, schema construction fails on both shapes — unannotated `info` raises `MissingArgumentsAnnotationsError`; annotated `**kwargs: Any` is treated as a GraphQL argument named `kwargs` and later fails with `Unexpected type 'typing.Any'`. Fix: rewrite every resolver signature in the spec — Slice 1 checklist sub-bullets, Decision 2 pseudocode (both `_default` and `_wrap`), the User-facing API "Custom resolver override" example, and any other resolver-signature mention — to the working shape: `def resolver(root: Any, info: Info)` with imports `from typing import Any` and `from strawberry.types import Info`. Drop `**kwargs` entirely. Justification: the `**kwargs` was a defensive catch-all for hypothetical future GraphQL arguments, but Strawberry treats every parameter as a GraphQL argument by default; arguments belong to the Layer-3 filter/order specs (`DONE-027-0.0.8` / `DONE-028-0.0.8`), not this card. When those cards ship, each will add its named, typed kwargs to the resolver shape explicitly. The pinned signature is `(root, info)` for `0.0.7`.
  2. **H2**: rev3's `_wrap` only checks the **immediate** return of `user_resolver(root, info)` against `isinstance(result, (Manager, QuerySet))`. If the consumer's resolver is `async def`, the immediate return is a coroutine — the isinstance check is False, the wrapper returns the coroutine unchanged, Strawberry awaits the coroutine downstream, and the `target_type.get_queryset(...)` step is silently skipped. The rev2 H1 graphene-django parity contract is therefore broken for async custom resolvers. Fix: rewrite the `_wrap` shape to detect `inspect.iscoroutine(result)` (or `inspect.isawaitable(result)`) and route through an `async def _wrap_async(...)` body that awaits the coroutine before applying the isinstance check and `get_queryset`. Concretely — the factory inspects `user_resolver` with `inspect.iscoroutinefunction(user_resolver)` at construction time and selects the sync or async wrapper accordingly; if detection fails (e.g., the consumer wraps an async function in `functools.partial`), the wrapper falls back to runtime `inspect.iscoroutine(result)` detection and returns an awaitable. Two new Slice 3 tests pin the contract: `test_djangolistfield_async_consumer_resolver_queryset_return_gets_get_queryset_applied` and `test_djangolistfield_async_consumer_resolver_python_list_return_passes_through`. Slice 3 test count goes from 11 to 13.
  3. **H3**: rev3's Decision 9 (rev2 M1's "add-only" posture) no longer satisfies the KANBAN card's Definition of done, which says "Live HTTP coverage **replacing** one of the hand-rolled `all_library_*` resolvers." The add-only strategy preserves test determinism but doesn't remove any boilerplate, so it's an intentional departure from the card text. Three options were considered: (a) reverse the strategy and replace `all_library_branches` via `DjangoListField(BranchType, resolver=lambda root, info: Branch.objects.order_by("id"))` — works under rev2 H1's "consumer-resolver queryset return gets `get_queryset` applied" contract, BUT then the example no longer exercises the **default-resolver** code path (the whole rationale rev2 M1 cited for adding rather than replacing); (b) keep the add-only strategy and explicitly call it out as an intentional departure from the card, and update the card body when the card moves to Done; (c) keep the add-only strategy AND additionally replace one of the other six non-`prefetched` resolvers — but those carry `order_by("id")` too and the same blast-radius applies. Rev4 picks **option (b)** — the test-determinism win from add-only is load-bearing and the card-text update on Done is mechanical. Fix: Decision 9 grows an explicit "Card-text departure" subsection acknowledging that the rev2 M1 add-only posture supersedes the card's "replacing one of the hand-rolled `all_library_*` resolvers" wording. The Slice 5 `KANBAN.md` doc-update bullet gains a sub-bullet requiring the past-tense Done body to use the add-only language. The Definition of done item 5 already says "adds a new root field ... does NOT replace any existing `all_library_*` resolver", which is the active contract; the rev4 work here is purely to make the card-text departure explicit rather than implicit.
  4. **M1**: the Borrowing posture line at the `maybe_queryset` bullet attributes the `Manager → QuerySet` coercion entirely to `DjangoOptimizerExtension._optimize` (`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._optimize #"if isinstance(result, models.Manager):"`), but the field wrapper itself MUST coerce `Manager` before applying `target_type.get_queryset(...)` — otherwise calling `get_queryset(Manager, info)` would pass a `Manager` where a `QuerySet` is expected, and the visibility hook contract degrades for `Model.objects` returns. The Decision 2 pseudocode correctly does `result.all() if isinstance(result, models.Manager) else result` inside `_wrap`, but the borrowing-posture prose contradicts that. Fix: rewrite the borrowing-posture bullet to say the **field wrapper** owns the `Manager → QuerySet` coercion (for visibility-hook correctness) while the **optimizer extension** also coerces (downstream safety net for non-`DjangoListField` root resolvers that happen to return `Model.objects`). Both coercions co-exist; neither replaces the other.
  5. **M2**: the spec preamble's `Status:` line said "draft (revision 1, initial)" — out of sync with the body, which has revisions through rev3 (and now rev4). The Implementation plan paragraph #"ships as five commits" said "ships as five commits" but the table has six rows including Slice 0. Fix: update the status line to "draft (revision 4, post-rev3 review)" and update the implementation-plan prose to "six slices (Slice 0 is a verification spike that does not produce a commit; Slices 1-5 each map to one commit)".
  6. **L1**: two add-vs-replace residues from rev2 M1 still read as if the spec is replacing a resolver — Slice 5's `TODAY.md` bullet says "if the new resolver replaces a hand-rolled one"; Current state's prose says "where one resolver-replacement is enough to pin the contract end-to-end." Fix: rewrite both to the add-only language so they match Decision 9, the Goals, and the Definition of done.
- **Revision 5** (post-rev4 review against the second pass of `feedback2.md`) — three high, four medium, three low. All findings are precision and grounding work; no architectural backtracking:
  1. **H1**: rev4 H2's `_wrap` implementation has a runtime-fallback branch (`if inspect.iscoroutine(result): ...`) for `functools.partial`-wrapped async resolvers that `inspect.iscoroutinefunction` misses, but the Test plan only pins the two construction-time-detected paths. With `fail_under = 100`, the runtime branch is uncovered and breaks the coverage gate. Three options were considered: (a) drop the fallback as YAGNI — `inspect.iscoroutinefunction` covers normal `async def` resolvers; consumers wrapping an async function in `functools.partial` for a resolver are an unusual case and can wrap in `async def` themselves; (b) keep the fallback and add a 14th behavior test; (c) `# pragma: no cover` — but the repo's convention reserves that for genuinely unreachable branches, and a `functools.partial`-wrapped coroutine IS reachable. Rev5 picks **option (a)** — drop the runtime fallback. Updated Decision 2 pseudocode (removes the `if inspect.iscoroutine(result):` branch from the sync `_wrap` body — `_wrap` now does `_post_process_sync(result)` directly), updated Slice 1 checklist's `Optional resolver=` bullet (drops the runtime-fallback sentence), updated rev4 H2's history-entry pseudocode reference to acknowledge the fallback was removed by rev5. The async path stays `inspect.iscoroutinefunction(user_resolver)` at construction time. If a real-world `functools.partial(async_fn, ...)` resolver appears, the consumer wraps it in `async def` (one extra line of consumer code) and gets the full async wrapper behavior; the spec calls this out in the Edge cases section.
  2. **H2**: rev4's Decision 2 carries two different async-detection mechanisms — runtime `in_async_context()` for the default resolver vs construction-time `inspect.iscoroutinefunction(user_resolver)` for the consumer-resolver wrapper. The asymmetry is intentional (Strawberry's class-attribute introspection commits to the resolver's sync-vs-async shape at schema construction, so the consumer wrapper must be statically sync OR async at factory time, while the default body can use the same lazy upgrade pattern `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.resolve` uses), but the spec doesn't explain it. A future maintainer might "harmonize" the two paths and break the design. Fix: add a Decision 2 "Async-detection asymmetry" paragraph after the pseudocode explaining that the two mechanisms target different dispatch sites — the default body dispatches **per-call** (same factory output runs under both `schema.execute_sync` and `await schema.execute`), the consumer wrapper dispatches **per-construction** (Strawberry inspects the resolver signature once at schema construction and commits to async-vs-sync handling globally). Harmonizing them would either force the default into static commitment (loses sync-callability) or force the consumer wrapper into lazy upgrade (an extra coroutine layer per call).
  3. **H3**: rev4 H1 pinned `from strawberry.types import Info` as the canonical import for the `info` annotation, but the assertion is not grounded — Strawberry exposes `strawberry.Info` as a top-level shortcut too, and module paths can shift between minor versions. Fix: add a Slice 0 checkbox that verifies the import path against the installed Strawberry before Slice 1 commits. Concretely: `python -c "from strawberry.types import Info; print(Info.__module__)"` and confirm the import resolves without raising. The factory's own usage at `django_strawberry_framework/types/relay.py #"from strawberry.utils.inspect import in_async_context"` follows the same pattern of grounding helper imports in the existing codebase; Slice 0 confirms `strawberry.types.Info` is similarly stable. If the import fails or schema construction raises `MissingArgumentsAnnotationsError` with `Info`-annotated resolvers, Decision 1 documents the fallback (`strawberry.Info` as the top-level shortcut, OR — less likely — a Strawberry version bump in `pyproject.toml`).
  4. **M1**: Slice 3's delta-table row prose enumeration double-counts "default resolver" / "sync `get_queryset` invocation" (these are one test in the Test plan: `test_djangolistfield_default_resolver_returns_queryset_filtered_by_get_queryset`) and under-counts `Meta.primary` (which is 2 tests in the Test plan: `test_djangolistfield_with_meta_primary_true_returns_primary_queryset` and `test_djangolistfield_with_secondary_target_uses_secondary_get_queryset`). The "13" total is correct by accident, not by alignment. Fix: rewrite the Slice 3 row enumeration to one-to-one match the 13 named Test-plan methods.
  5. **M2**: rev3 M4's line-number sweep got `_apply_get_queryset_async` wrong — claimed a wider span than the symbol actually occupies (the next symbol `_coerce_node_id` starts immediately after). Same applies to the Current-state span. Fix: replace residual `_apply_get_queryset_async` range citations with the symbol-qualified path `django_strawberry_framework/types/relay.py::_apply_get_queryset_async`, and replace the Current-state span citation with the combined `django_strawberry_framework/types/relay.py::_apply_get_queryset_sync` plus `::_apply_get_queryset_async` form at every occurrence.
  6. **M3**: The Test plan's `test_djangolistfield_async_get_queryset_is_awaited` pins the case where the target type's `get_queryset` is `async def` — but the dual-execution edge case (sync `get_queryset` under async schema execution via `await schema.execute(...)`) is NOT pinned. The runtime `in_async_context()` branch in the default resolver depends on this dual shape (in_async_context is True; get_queryset is sync; the wrapper still needs to await the right path). Fix: add a 14th behavior test, `test_djangolistfield_default_resolver_works_under_sync_and_async_schema_execution`, which exercises a sync `get_queryset` under both `schema.execute_sync(...)` and `await schema.execute(...)`. Slice 3 count goes 13 → 14; total Slice 1 tests go 17 → 18. (With H1's option (a) — drop runtime fallback — no other test was needed; M3's single addition is the only test-count delta.)
  7. **M4**: rev4 H2's Decision 2 pseudocode defines `_post_process_sync(result)` and `_post_process_async(result)` as module-level helpers, but their bodies reference `info` — a name that exists only in the `_wrap` wrapper's `(root, info)` parameter list, not in the factory's enclosing scope. An implementer pasting the pseudocode verbatim hits `NameError: name 'info' is not defined` at the first call. Fix: rewrite the helpers to take `info` (and `target_type`) as explicit parameters, and rewrite the `_wrap` call sites to pass them: `_post_process_sync(target_type, result, info)`. Makes the data flow visible and matches how the helpers will actually be implemented.
  8. **L1**: `def DjangoListField(...)` is a PascalCase function name. The repo's `pyproject.toml` selects `N` (pep8-naming) in `[tool.ruff.lint]`'s rule set; rule N802 ("function name should be lowercase") will flag the definition and the slice will fail at the `uv run ruff check --fix .` gate. The PascalCase shape is intentional (it matches graphene-django's `DjangoListField(Field)` class-shaped import surface, and consumers expect to write `DjangoListField(BranchType)`). Fix: add an explicit `# noqa: N802` comment to the `def DjangoListField(...)` line with a brief rationale ("PascalCase for graphene-django parity — consumer usage is `DjangoListField(BranchType)` mirroring the upstream class-import shape; intentional N802 exception"). Slice 1 checklist gains a sub-bullet naming the noqa requirement. Alternative considered: per-file ignore in `pyproject.toml` (rejected — `list_field.py` has only one PascalCase function; per-file ignore is heavier than necessary and would hide future N802 violations in the same file).
  9. **L2**: The rev3 M4 history entry's line-number sweep listed some before/after pairs that read as identical (e.g., the rev3 entry restated the same `_apply_get_queryset_sync` line range on both sides of a "change X → Y" arrow — the entry was describing what rev3 had landed, not what rev3 changed, but the framing was confusing). Fix: tighten the rev3 M4 history entry to only enumerate citations that genuinely shifted (the `raise ConfigurationError` block inside `_apply_get_queryset_sync` was narrower than the original spec implied; the `_apply_get_queryset_async` span was wider than rev3 wrote and was re-tightened by rev5 M2; the `_resolve_model_from_return_type` "definition" wording was reclassified to "called inside `_optimize`, defined at the module-level helper"). The unchanged citations don't belong in a "what changed" entry. (Rev7 line-number-to-symbol sweep: all of these are now symbol-qualified per `AGENTS.md` #"Source references in docs and code comments: use symbol-qualified paths", so the rev3/rev5 line-number history above is preserved for audit but does not name live line numbers anymore.)
  10. **L3**: The Test-plan section's `tests/test_list_field.py` heading descriptor says "Package-internal tests, system-under-test is `django_strawberry_framework`" — slightly redundant. `AGENTS.md` #"package tests, system-under-test is django_strawberry_framework itself" uses the more compact "package tests, system-under-test is `django_strawberry_framework` itself" framing. Fix: trim to match the `AGENTS.md` framing: "Package tests; system-under-test is `django_strawberry_framework`."
- **Revision 6** (post-rev5 scaffolding review against `feedback2.md`) — three high, six medium, three low. All findings surfaced during hands-on scaffolding contact with the rev5 pseudo-code; the issues are precision, placement, and assertion-falsifiability work, not architectural backtracking:
  1. **H1**: rev5's `_default` body wraps the call to `_apply_get_queryset_async` in an inner `async def _async_path()` whose only job is to `await` the coroutine and return the result. But `_apply_get_queryset_async` is already `async def` (defined at `django_strawberry_framework/types/relay.py::_apply_get_queryset_async`) — calling it returns a coroutine that Strawberry's AwaitableOrValue dispatch will await directly. The inner-function wrapper adds an extra `async def` per resolver invocation and an extra coroutine layer with no semantic gain. Fix: collapse to the one-liner `return _apply_get_queryset_async(target_type, qs, info)` inside the `if in_async_context():` branch. Updated Decision 2's `_default` pseudo-code; no test changes required (the contract is unchanged; the implementation just stops adding a redundant wrapper).
  2. **H2**: rev5 M4's Decision 2 pseudo-code is internally contradictory about helper placement — the leading comment says "Module-scope post-processing helpers", but the indentation shows the helpers defined INSIDE `def DjangoListField(target_type, ...):`. An implementer pasting the pseudo-code verbatim will either pick the indentation (factory-scope; `target_type` becomes redundant noise) or pick the comment (module-scope; helpers need de-indenting). Fix: pin **module-scope** placement (preferred per reviewer — referentially transparent helpers, unit-testable independently of the factory, `_apply_get_queryset_*` imports are already importable at module load per Decision 3 Option A). Rewrite the pseudo-code so `_post_process_consumer_sync` / `_post_process_consumer_async` (renamed per H3 below) appear at column 0 OUTSIDE `def DjangoListField(...)`, with explicit `target_type` and `info` parameters per rev5 M4. The factory body imports them by reference and the `_wrap` call sites pass `target_type` (from closure) and `info` (from the resolver's parameter) explicitly.
  3. **H3**: rev5 named the post-processing helpers `_post_process_sync` / `_post_process_async`, implying they handle every queryset return in the field. But `_default` calls `_apply_get_queryset_{sync,async}` directly, bypassing the helpers — only `_wrap` (the consumer-resolver path) uses them. The asymmetry IS justified (`_default` knows `qs` came from `Manager.all()`, so no Manager→QuerySet coercion and no isinstance branching is needed), but the names hide that. Fix: rename to `_post_process_consumer_sync` / `_post_process_consumer_async` so the per-consumer-resolver scope is explicit in the name; a maintainer asking "why doesn't `_default` use these?" gets the answer from the name. Add a one-line comment above the helper definitions documenting the bypass justification.
  4. **M1**: The Risks section claims Strawberry's class-attribute machinery picks up `DjangoListField`'s return value "via `__set_name__`". That's mechanically incorrect — Strawberry performs discovery via `@strawberry.type`'s decorator-time class-body walk (it iterates `cls.__dict__` and converts annotated attributes / `StrawberryField` instances into the type's field list), NOT via the descriptor protocol's `__set_name__` hook. Fix: rewrite the claim to "via `@strawberry.type`'s decorator-time class-body walk, the same way `field = strawberry.field(...)` is discovered today." Accurate without committing to the wrong mechanism. Doesn't affect Slice 0's end-to-end verification, but corrects the spec's design-intent record.
  5. **M2**: Slice 0's "Build a Strawberry schema; confirm the field is picked up with annotation-derived GraphQL type `[BranchType!]!`" leaves the verification mechanism unspecified — an implementer might use `print(schema)` (fragile across Strawberry minor versions), substring assertions against `str(schema)` (also fragile), or an introspection query (robust). Fix: pin the introspection-query mechanism. Provide a concrete query and assertion shape in the Slice 0 checklist that traverses `__type(name: "Query") { fields { name type { kind ofType { ... } } } }` and asserts `kind == "NON_NULL" / "LIST" / "NON_NULL" / "OBJECT"` at the appropriate depths. Robust against SDL formatting drift.
  6. **M3**: The User-facing API's "Custom resolver override" example shows only the sync shape, but rev4 H2 explicitly added async-consumer-resolver support. A consumer reading the User-facing API as their one-stop reference will assume async isn't supported, or they'll have to dig into Decision 2 to learn it is. Fix: add a second code block under "Custom resolver override" demonstrating an `async def` resolver, with a one-line note about the rev4 H2 contract ("async resolvers returning a `QuerySet` receive the same `target_type.get_queryset(...)` treatment as sync resolvers"). Use `asgiref.sync.sync_to_async` in the example since Django's ORM sync-by-default is the typical case.
  7. **M4**: The Edge cases section's `functools.partial` workaround prose is compressed to a single inline phrase: `async def my_resolver(root, info): return await partial(...)`. A reader debugging the silent-skip bug needs a clear before/after to see what changes. Fix: replace the inline phrase with two real code blocks — one showing the broken `DjangoListField(BranchType, resolver=functools.partial(my_async, ...))` shape with a comment explaining why `get_queryset` is silently skipped, and one showing the working `async def _wrapped(root, info): return await my_async(...)` shape. Removes the compressed-prose hostility without changing the YAGNI posture.
  8. **M5**: The Slice 5 doc-updates `GOAL.md` bullet says "Update the migration shape sections to reference `DjangoListField` when relevant" — "when relevant" is unfalsifiable. Verified: `GOAL.md #"### Coming from \`graphene-django\`"` is the migration subsection, and `GOAL.md #"Expose model collections with \`DjangoConnectionField\` or \`DjangoListField\`"` already mentions `DjangoListField` in Success criteria item 2. Fix: name the specific heading — "the 'Coming from `graphene-django`' migration-shape subsection at `GOAL.md #"### Coming from \`graphene-django\`"` — add a one-line bullet under the diff block noting that `DjangoListField` replaces graphene-django's symbol of the same name (the Success criteria mention is already accurate as a forward-pointer)."
  9. **M6**: `test_djangolistfield_at_root_position_is_optimized` is the single regression net for the root-only contract (Decision 4 + rev2 M3), but the Test plan describes it only as "assert the optimizer planned `select_related` / `prefetch_related` (via `assertNumQueries` / SQL-sniffer pattern)" — the specific assertion shape is unpinned. `assertNumQueries(2)` vs `assertNumQueries(<= 5)` vs SQL-string sniffing measure different things; a future refactor that quietly changes the per-query count slides past a permissive `<= 5` shape. Fix: pin the assertion to exact query count via `assertNumQueries(N)` where N is one base SELECT plus one prefetch per `prefetch_related` relation; the test docstring documents the expected count derivation so a future maintainer can update N when the selection shape changes.
  10. **L1**: rev5 H3's Slice 0 `Info` import-verification bullet has a non-falsifiable hedge: "confirm the import resolves and `Info.__module__ == 'strawberry.types.info'` (or the path the installed Strawberry uses)". The "or the path the installed Strawberry uses" parenthetical makes the equality check non-falsifiable — any module path passes. Fix: drop the equality check; keep only the import-resolution success criterion: "confirm `from strawberry.types import Info` raises no `ImportError`; record `Info.__module__` for the post-spike Risks note." False precision removed; no information lost.
  11. **L2**: During the rev5 scaffolding pass, TODO comments were left in six touched files (`django_strawberry_framework/list_field.py`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, `tests/test_list_field.py`, `examples/fakeshop/apps/library/schema.py`, `examples/fakeshop/test_query/test_library_api.py`). Ruff's `ERA001` catches commented-out code but not `# TODO:` markers, so without an explicit cleanup checkbox the TODOs survive to Done. Fix: add "Remove the spec-016 scaffold TODOs at this site" sub-bullets to Slices 1, 3, and 4 covering each affected file.
  12. **L3**: The Implementation plan table's Slice 3 row still says `+260 / -0` (rev5 M3's count) even though that row already inflated by the rev5 M3 14th test. Fix: refresh the line-delta estimate to `+280 / -0` to track the test additions. (A more robust framing would rename the column to "Order-of-magnitude line delta" so future test-count changes don't require table edits; not adopted in rev6 because rev1-rev5 conventions all use the precise-looking shape. Future revisions may switch.)

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the vocabulary used throughout the spec:

- [`DjangoListField`][glossary-djangolistfield] — the entry this card flips from `planned for 0.0.7` to `shipped (0.0.7)` in [Slice 5](#slice-5--promotion--docs--version).
- [`DjangoType`][glossary-djangotype] — the type class the field binds to; the field's queryset is derived from `Meta.model` (see [Decision 2](#decision-2--default-resolver-shape)).
- [`Meta.model`][glossary-metamodel] — the source of `model._default_manager` (see [Decision 2](#decision-2--default-resolver-shape)).
- [`Meta.fields`][glossary-metafields] — independent of this card; `DjangoListField` does not introspect a type's selected fields.
- [`get_queryset` visibility hook][glossary-get-queryset-visibility-hook] — applied to the default queryset before return (see [Decision 3](#decision-3--get_queryset-and-async-symmetry)).
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] — root-gated planning already shipped; the field must return a `QuerySet` so the existing `info.path.prev is None` gate fires (see [Decision 4](#decision-4--optimizer-cooperation)).
- [`Relation handling`][glossary-relation-handling] — many-side relations currently produce `list[T]` via generated resolvers; this card adds the symmetric **root**-list primitive but does NOT change relation-side many-list shapes (see [Decision 7](#decision-7--scope-boundary-vs-relation-list-fields)).
- [`Meta.primary`][glossary-metaprimary] — multiple `DjangoType`s per model; `DjangoListField(SecondaryType)` is the explicit-target shape that side-steps the registry lookup ambiguity (see [Decision 6](#decision-6--metaprimary-interaction)).
- [`Relay Node integration`][glossary-relay-node-integration] — non-Relay list shape is the entire point of this card; the Relay sibling lives under [`DjangoConnectionField`][glossary-djangoconnectionfield] in `DONE-030-0.0.9` (see [Decision 8](#decision-8--out-of-scope-boundary-with-djangoconnectionfield)).
- [`ConfigurationError`][glossary-configurationerror] — raised by the field's constructor when the argument is not a registered `DjangoType` subclass (see [Decision 5](#decision-5--validation--error-shapes)).

Project conventions to follow:

- [`AGENTS.md`][agents] — schema testing via `schema.execute_sync`; live `/graphql/` HTTP coverage in `examples/fakeshop/test_query/`. **Note:** `AGENTS.md` prohibits `CHANGELOG.md` edits without explicit permission; [Slice 5](#slice-5--promotion--docs--version) grants that permission.
- [`CONTRIBUTING.md`][contributing] — 100% coverage target; release-bump checklist.
- [`KANBAN.md`][kanban] — card-ID format; column movement at Slice 5.
- [`docs/TREE.md`][tree] — package layout; tests mirror source one-to-one; flat single-file Layer-3 modules at the package root pair with `tests/test_<module>.py`.

## Slice checklist

Each top-level item maps to one commit in the [Implementation plan](#implementation-plan).

- [ ] Slice 0: Pre-implementation verification (rev3 H1; no code lands; throw-away spike)
  - [ ] **Confirm `info: Info` import path** (rev5 H3; rev6 L1 dropped the non-falsifiable `Info.__module__ == "..."` equality check) — run `python -c "from strawberry.types import Info; print(Info.__module__)"` against the installed Strawberry; confirm the import raises no `ImportError`. Record `Info.__module__` for the post-spike Risks note so a future maintainer can see which module path the installed Strawberry exposed. If the import fails, fall back to `import strawberry; Info = strawberry.Info` and pin that shape in Decision 1. Without this verification, Slice 1's resolver signatures may compile but fail schema construction.
  - [ ] Write a throw-away stub in a sandbox using an annotated module-level resolver (rev6 post-Slice-0 reconciliation — the bare-lambda `lambda root, info: ...` shape originally pinned here raises `MissingArgumentsAnnotationsError` at `strawberry.field(resolver=...)` call time on the installed Strawberry, BEFORE `@strawberry.type`'s class-body walk runs, so the lambda cannot be used to verify the class-body-discovery contract; the annotated `def` shape below is the only viable form and matches the rev4 H1 / Slice 1 pinned `(root: Any, info: Info)` signature):
    ```python
    from typing import Any
    from strawberry.types import Info
    import strawberry

    def _stub_resolver(root: Any, info: Info):
        return target_type.__django_strawberry_definition__.model._default_manager.all()

    def DjangoListFieldStub(target_type):
        return strawberry.field(resolver=_stub_resolver)
    ```
  - [ ] Assign it to a Query attribute under `@strawberry.type`: `all_branches: list[BranchType] = DjangoListFieldStub(BranchType)`.
  - [ ] Build a Strawberry schema and confirm the field is picked up with annotation-derived GraphQL type `[BranchType!]!` (rev6 M2 — verification mechanism pinned to an introspection query rather than `print(schema)` or SDL substring assertions; the latter are fragile across Strawberry minor versions). Concretely: `result = schema.execute_sync('{ __type(name: \"Query\") { fields { name type { kind ofType { kind ofType { kind name } } } } } }')`; locate `fields[name == "allBranches"]`; assert the outer `type.kind == "NON_NULL"`, the wrapped `ofType.kind == "LIST"`, the inner `ofType.ofType.kind == "NON_NULL"`, and the leaf `ofType.ofType.ofType.name == "BranchType"`. Run a real `schema.execute_sync('{ allBranches { id name } }')` query afterward and confirm rows return.
  - [ ] Build a second stub that uses an explicitly annotated resolver — `def resolver(root: Any, info: Info)` with `from strawberry.types import Info` — and confirm Strawberry's schema construction accepts it without raising `MissingArgumentsAnnotationsError` (rev5 H3, the import verification's other half).
  - [ ] Repeat with `list[BranchType] | None` annotation; confirm the rendered type is `[BranchType!]` (nullable outer).
  - [ ] If all shapes work end-to-end: proceed to Slice 1 with the factory-function design intact.
  - [ ] If either shape does NOT work: the Risks fallback (directly construct a `StrawberryField` with explicit `python_name` / `type_annotation`) is promoted to Decision 1; Slice 1 is reauthored before any production code lands.
  - [ ] No tests committed in this slice; the spike is local exploration. The Slice 1 implementation begins only after this Slice's checkboxes are ticked.
- [ ] Slice 1: Module + factory function
  - [ ] New flat module `django_strawberry_framework/list_field.py` (placement decision: see [Decision 1](#decision-1--module-location-mechanism--public-export)) housing the `DjangoListField` symbol.
  - [ ] Implement `DjangoListField` as a **factory function** (rev2 H2 — `strawberry.field` is a function in the installed Strawberry version, not a class, so subclassing it is not viable; and `__set_name__` cannot replace an already-assigned class attribute). The factory returns `strawberry.field(resolver=<wrapped>, description=..., deprecation_reason=..., directives=...)`. Consumer usage is `all_branches: list[BranchType] = DjangoListField(BranchType)` — Strawberry reads the consumer's class-attribute annotation for the outer GraphQL list shape (`list[BranchType]` → `[BranchType!]!`, `list[BranchType] | None` → `[BranchType!]`), so the factory does NOT need to override the annotation.
  - [ ] Suppress `ruff` rule **N802** on the `def DjangoListField(...)` line with `# noqa: N802  # PascalCase for graphene-django parity — consumer usage is `DjangoListField(BranchType)`` (rev5 L1). The repo's `pyproject.toml` enables `N` (pep8-naming) in `[tool.ruff.lint]` and N802 flags PascalCase function names; the PascalCase shape is intentional graphene-django parity. Per-line `noqa` is preferred over a per-file ignore because `list_field.py` only has one PascalCase definition and a wider exception would hide future violations.
  - [ ] Capture `target_type` via closure (rev2 H3, rev4 H1 — the resolver signature is the Strawberry-native `(root: Any, info: Info)`, NOT `(type_cls, info)` or `(root, info, **kwargs)`; `target_type` is looked up from the enclosing scope, not from a first positional argument). Imports: `from typing import Any` and `from strawberry.types import Info` at the top of `list_field.py`. Drop `**kwargs` from every resolver signature in this card; Strawberry treats every parameter as a GraphQL argument by default, and this card does not add any.
  - [ ] Default resolver body — sync path:
    1. `qs = target_type.__django_strawberry_definition__.model._default_manager.all()`
    2. `qs = target_type.get_queryset(qs, info)` — coroutine guard rejected per [Decision 3](#decision-3--get_queryset-and-async-symmetry) (port verbatim from `types/relay.py:_apply_get_queryset_sync` so the same `ConfigurationError` shape covers both Relay and list paths).
    3. `return qs`
  - [ ] Default resolver body — async path:
    1. `qs = target_type.__django_strawberry_definition__.model._default_manager.all()`
    2. `qs = await _apply_get_queryset_async(target_type, qs, info)` — port verbatim from `types/relay.py`.
    3. `return qs`
  - [ ] Async detection uses the same `in_async_context` hook the Relay defaults use — pin the import as `from strawberry.utils.inspect import in_async_context` (rev3 M7; verified at `django_strawberry_framework/types/relay.py #"from strawberry.utils.inspect import in_async_context"`). Same `iscoroutinefunction`/coroutine handling.
  - [ ] Optional `resolver=` constructor argument that overrides the default body. When supplied, wrap the consumer resolver so a `Manager`/`QuerySet` return value is fed through `target_type.get_queryset(qs, info)` (rev2 H1 — graphene-django parity). Detection: `isinstance(result, (models.Manager, models.QuerySet))`. The wrapper itself does the `Manager → QuerySet` coercion via `result.all()` BEFORE applying `get_queryset` (rev4 M1; the optimizer's downstream `Manager` coercion is a safety net, not a substitute). Async consumer resolvers (rev4 H2): inspect `user_resolver` with `inspect.iscoroutinefunction(...)` at factory construction time; if true, build an `async def` wrapper that `await`s the consumer's coroutine BEFORE the `isinstance` check, so an async resolver returning a `QuerySet` still gets `get_queryset` applied. Python `list` returns from sync OR async resolvers pass through unchanged. (Rev5 H1: the rev4 runtime-fallback branch for `functools.partial`-wrapped async resolvers was dropped as YAGNI — `inspect.iscoroutinefunction` covers normal `async def` resolvers; consumers wrapping an async function in `functools.partial` rewrap in `async def` instead.) Optimizer cooperation still applies because the extension is root-gated against `info.path.prev is None` (`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.resolve #"if info.path.prev is not None:"`); a consumer resolver returning a `QuerySet` is planned exactly like the default.
  - [ ] Optional `description=` / `deprecation_reason=` / `directives=` pass-through into the inner `strawberry.field(...)` call so the symbol is feature-comparable to `strawberry.field(...)` at the metadata level.
  - [ ] Re-export from `django_strawberry_framework/__init__.py` in alphabetical order ([Decision 1](#decision-1--module-location-mechanism--public-export)); add `"DjangoListField"` to `__all__`.
  - [ ] Update `tests/base/test_init.py`'s pinned `__all__` assertion.
  - [ ] Remove the spec-016 scaffold TODOs at this site (rev6 L2) — covers `django_strawberry_framework/list_field.py`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`. Ruff's `ERA001` catches commented-out code but not `# TODO:` markers, so explicit cleanup is the only protection against the scaffold TODOs landing in main.
- [ ] Slice 2: Validation
  - [ ] Constructor validates that the argument is a class AND is `issubclass(arg, DjangoType)` AND is registered (`arg.__django_strawberry_definition__` exists) — per [Decision 5](#decision-5--validation--error-shapes). Errors raise `ConfigurationError` with the same `model.Meta.<key> …` shape pattern (`types/base.py:_format_unknown_fields_error` style) reused for consistency.
  - [ ] `resolver=`, when supplied, is callable; otherwise `ConfigurationError`.
  - [ ] Tests for validation cluster live in `tests/test_list_field.py`.
  - [ ] (rev2 H2: dropped — `nullable_list=` is NOT a constructor argument; outer nullability is driven by the consumer's class-attribute annotation.)
- [ ] Slice 3: Optimizer + `get_queryset` cooperation tests
  - [x] Package-internal tests under `tests/test_list_field.py` covering: default-resolver shape, `cls.get_queryset` invocation, sync coroutine rejection, async path awaits sync + async `get_queryset`, **sync consumer `resolver=` return value receives `get_queryset` when it is a `Manager`/`QuerySet`** (rev2 H1), Python-`list` sync consumer returns pass through unchanged (rev2 H1), **async consumer `resolver=` returning a `Manager`/`QuerySet` receives `get_queryset`** (rev4 H2), Python-`list` async consumer returns pass through unchanged (rev4 H2), nullable-outer-via-consumer-annotation produces `[T!]` (rev2 H2), non-nullable-outer default produces `[T!]!` (rev2 H2), `DjangoListField` at root position is optimized (rev2 M3), [FK-id elision][glossary-fk-id-elision] survives, `Meta.primary` interaction (explicit primary, explicit secondary).
  - [x] Remove the spec-016 scaffold TODOs at this site (rev6 L2) — covers the 18 TODO stubs in `tests/test_list_field.py` as they get replaced with real test bodies.
- [ ] Slice 4: Live HTTP coverage
  - [ ] **Add a new** root field — `all_library_branches_via_list_field: list[BranchType] = DjangoListField(BranchType)` — to `examples/fakeshop/apps/library/schema.py` (rev2 M1; do NOT replace the existing `all_library_branches` because its `order_by("id")` is depended on by `test_library_relation_override_shapes_http_response_data`). The other seven `@strawberry.field` resolvers stay unchanged.
  - [ ] Add a new HTTP test in `examples/fakeshop/test_query/test_library_api.py` (or extend an existing test in the same file) asserting: (a) the new field returns the expected branches via `/graphql/`, (b) the optimizer planned `prefetch_related` / `select_related` correctly for a nested selection (via `assertNumQueries` / the existing SQL-sniffer pattern). The `cls.get_queryset` cooperation coverage lives in the package-internal `tests/test_list_field.py` tests (rev2 M2 — adding a real `BranchType.get_queryset` filter would mutate every `BranchType` path in the library schema and is out of scope here).
  - [ ] Remove the spec-016 scaffold TODOs at this site (rev6 L2) — covers `examples/fakeshop/apps/library/schema.py` and `examples/fakeshop/test_query/test_library_api.py`.
- [ ] Slice 5: Promotion + docs + version
  - [ ] Flip [`DjangoListField`][glossary-djangolistfield] from `planned for 0.0.7` to `shipped (0.0.7)` in [`docs/GLOSSARY.md`][glossary]; update the public exports list at the top and the index table.
  - [ ] Update [`README.md`][readme], [`docs/README.md`][docs-readme], [`GOAL.md`][goal], and [`TODAY.md`][today] where `DjangoListField` is currently called out as unshipped or "wait for":
    - `README.md` — the Status section (currently plain prose; surface `DjangoListField` inline at `README.md #"## Status"` alongside the version-pin sentence rather than introducing a bullet list that doesn't match the file's voice — pinned by Slice 5 pass-2 root-cause fix per `AGENTS.md` #"Code is held to the highest standard always").
    - `docs/README.md` — the "Shipped today (`0.0.6`)" → "Shipped today (`0.0.7`)" bullet list under "Today and coming next".
    - `GOAL.md` — Migration shape sections mention `DjangoListField` indirectly through `graphene-django` migration; ensure the migration story is now reachable.
    - `TODAY.md` — drop `DjangoListField` (if listed) from the wait-for list; update the `library` example summary to mention that the new `all_library_branches_via_list_field` root field exercises `DjangoListField`'s default-resolver path (added as a sibling per rev2 M1; no existing resolver was replaced).
  - [ ] `docs/TREE.md` — add `list_field.py` to the current on-disk layout AND to the target layout (a flat single-file Layer-3 module per the TREE convention); add `tests/test_list_field.py` to the current test-tree section. **Remove the `DjangoListField` mention from the existing `connection.py # [alpha] DjangoConnectionField + DjangoListField` line** so the target layout doesn't advertise two homes for the symbol (rev2 L1).
  - [ ] `KANBAN.md` — move `DONE-020-0.0.7` to Done with `DONE-NNN-0.0.7` (next available number; the column-move pass renumbers as usual). The past-tense Done body MUST reflect the add-only posture: "Added a new `all_library_branches_via_list_field` root field via `DjangoListField`" rather than the original card text's "Live HTTP coverage replacing one of the hand-rolled `all_library_*` resolvers" (rev4 H3 — intentional card-text departure per [Decision 9](#decision-9--example-app-migration-posture)'s "Card-text departure" paragraph).
  - [ ] `CHANGELOG.md` — `[0.0.7]` Added entry: `DjangoListField` (non-Relay `list[T]` field for **root Query fields** with default `model._default_manager.all()` resolver, `cls.get_queryset` cooperation in sync + async contexts and on consumer-resolver `Manager`/`QuerySet` returns, optimizer cooperation through root-gating). (rev2 L2 — narrowed wording from "root and nested fields" to "root Query fields" to match the M3 scope narrowing.)
  - [ ] Version bump (deferred to **the last `0.0.7` card to ship**, NOT this card; rev3 M1): see [Decision 10](#decision-10--joint-0_0_7-cut). This card does NOT bump `pyproject.toml`, `django_strawberry_framework/__init__.py`'s `__version__`, or `tests/base/test_init.py`'s version assertion — those move when the last of the five `0.0.7` WIP cards ships.
  - [ ] Final gates:
    - [ ] `uv run ruff format .` passes.
    - [ ] `uv run ruff check --fix .` passes.
    - [ ] `uv run pytest` passes with 100% package coverage (`fail_under = 100`).
    - [ ] One new public export (`DjangoListField`) — the only addition to `__all__` in this slice.

## Problem statement

`DjangoType` users cannot declare a model-backed `list[T]` root field through the package; every root resolver returning a `list[T]` of a `DjangoType` today is hand-rolled. The `library` example schema makes this concrete — `examples/fakeshop/apps/library/schema.py::Query` declares **eight** `@strawberry.field` resolvers, every one of which has the same shape:

```python
@strawberry.field
def all_library_branches(self) -> list[BranchType]:
    return models.Branch.objects.order_by("id")
```

The shape is identical across the seven non-`prefetched` resolvers (`all_library_branches`, `all_library_shelves`, `all_library_books`, `all_library_genres`, `all_library_patrons`, `all_library_membership_cards`, `all_library_loans`) — only the model and target type change. The eighth (`all_library_prefetched_books`) is a separate concern that exercises the queryset-diffing path and intentionally stays as a `@strawberry.field`.

Consequences without a `DjangoListField`:

- Every Django app that wants a model collection through GraphQL writes a one-line root resolver. The library example proves the boilerplate is mechanical and identical.
- `graphene-django` migrants lose a primitive they already know (`/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/fields.py::DjangoListField` — `class DjangoListField(Field)` is the default list shape for graphene-django).
- The `cls.get_queryset(...)` visibility hook is silently bypassed unless the consumer remembers to thread it through every hand-rolled resolver — the [`Optional fakeshop visibility filtering today`][today-optional-fakeshop-visibility-filtering-today] section in `TODAY.md` lays out the exact boilerplate consumers have to write today, and the package has no symbol that does it automatically.
- `TODAY.md`'s "fakeshop should wait for" list (`TODAY.md #"## What the fakeshop example should wait for"`) includes `DjangoConnectionField` but not `DjangoListField`; that omission is symptomatic — the package does not currently distinguish the simple-list case from the Relay-connection case.

`0.0.6` shipped every architectural seam this slice needs: `DjangoTypeDefinition.model` for the queryset source, `cls.get_queryset(...)` for the visibility hook, `DjangoOptimizerExtension`'s root-gated `info.path.prev is None` planning hook (`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.resolve #"if info.path.prev is not None:"`), and the sync + async `_apply_get_queryset_*` ports from spec-011. `0.0.7` populates and applies that seam.

The target is not a full connection/query-field release. The target is to make `list[T]` **root** fields possible in the package's `class Meta` style, while preserving the existing optimizer behavior, the `get_queryset` cooperation contract, and the `Meta.primary` registry semantics. Nested non-root usage of `DjangoListField` is functional (the field still produces a list resolver) but is NOT root-optimized in `0.0.7` per rev2 M3 and [Decision 4](#decision-4--optimizer-cooperation).

## Current state

- `django_strawberry_framework/__init__.py #"__all__"` re-exports [`BigInt`][glossary-bigint-scalar], `DjangoOptimizerExtension`, `DjangoType`, [`OptimizerHint`][glossary-optimizerhint], `__version__`, `auto`, [`finalize_django_types`][glossary-finalize-django-types] — and only those seven. (Historical citation: before `DjangoListField` shipped in `0.0.7`, this re-export tuple did NOT include `DjangoListField`; the spec was authored against that pre-ship state.)
- The `library` example schema at `examples/fakeshop/apps/library/schema.py::Query` carries eight hand-rolled root list resolvers, seven of which share the identical "queryset over model.objects ordered by id" shape (see the [Problem statement](#problem-statement) for the exact code).
- The `products` example schema at `examples/fakeshop/apps/products/schema.py::Query` has the same shape: four `@strawberry.field` resolvers returning `Model.objects.all()` directly. The post-`TODO-ALPHA-022` future shape in the comments (`examples/fakeshop/apps/products/schema.py::Query #"Future shape"`) jumps straight from `@strawberry.field` resolvers to `relay.ListConnection[…] = DjangoConnectionField(…)` — the simpler `DjangoListField` shape is not the documented future target for products because products' design goal is Relay-shaped throughout. `DjangoListField`'s natural example home is the `library` app, where a single new sibling root field (`all_library_branches_via_list_field`) is enough to pin the default-resolver contract end-to-end via the live HTTP test (rev2 M1 — sibling-add, not replacement; see [Decision 9](#decision-9--example-app-migration-posture)).
- `django_strawberry_framework/types/relay.py` defines `_apply_get_queryset_sync` (`django_strawberry_framework/types/relay.py::_apply_get_queryset_sync`) and `_apply_get_queryset_async` (`django_strawberry_framework/types/relay.py::_apply_get_queryset_async`), the helpers that run `cls.get_queryset(...)` in sync and async contexts respectively. The sync helper rejects a coroutine-from-sync mismatch with a `ConfigurationError` (`django_strawberry_framework/types/relay.py::_apply_get_queryset_sync #"raise ConfigurationError"`). These are the helpers the `DjangoListField` default resolver re-uses verbatim — no new sync/async plumbing is invented in this slice.
- `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.resolve` defines the root-gated `resolve` hook keying on `info.path.prev is None`. A field that returns a `Django QuerySet` at the root is planned automatically; a field that returns a Python `list` is not. The `DjangoListField` default resolver MUST return a `QuerySet`, not a Python list, for the optimizer to engage.
- `django_strawberry_framework/registry.py` carries the `Meta.primary`-aware lookup (`primary_for(model)`, `types_for(model)`). `DjangoListField` takes an explicit `DjangoType` argument, NOT a model — this means the registry's primary/secondary ambiguity is irrelevant to the construction path (the consumer named the target type explicitly).
- `django_strawberry_framework/scalars.py` ships `BigInt` as a flat single-file Layer-3 module. The target on-disk layout in `docs/TREE.md #"## django_strawberry_framework (current on-disk layout)"` lists `fieldset.py`, `permissions.py`, `connection.py` as parallel single-file Layer-3 modules under the package root. `list_field.py` slots in next to those.
- `tests/test_registry.py`, `tests/test_scalars.py` (if present) — and per the convention in `docs/TREE.md #"tests/test_<module>.py (flat, at the root)"` ("`tests/test_<module>.py` (flat, at the root) — single-file Layer-3 module tests") — the test home for `DjangoListField` is `tests/test_list_field.py`, parallel to the source module.

## Goals

1. Ship `DjangoListField(TargetType)` as a single new public export from `django_strawberry_framework` — a factory function that returns `strawberry.field(resolver=..., ...)`. The default resolver calls `model._default_manager.all()` and applies `cls.get_queryset(...)`; sync + async paths; consumer-`resolver=` override is supported, and the override's `Manager`/`QuerySet` return value also receives `target_type.get_queryset(...)` (rev2 H1, graphene-django parity).
2. Preserve `DjangoOptimizerExtension`'s root-gated planning for `DjangoListField`-served querysets at **root** Query positions. Nested non-root use of `DjangoListField` works as a resolver but is NOT root-optimized in `0.0.7` (rev2 M3); see [Decision 4](#decision-4--optimizer-cooperation).
3. Preserve the `cls.get_queryset(...)` cooperation contract from spec-011 and [`docs/GLOSSARY.md#get_queryset-visibility-hook`][glossary-get-queryset-visibility-hook]: both the sync and the async paths invoke `cls.get_queryset(qs, info)` before returning, and the same `ConfigurationError` for coroutine-in-sync mismatch from `types/relay.py` fires for `DjangoListField` consumers.
4. Stay tight: no `DjangoConnectionField`, no filter / order / aggregate / search arguments on the field, no auto-upgrade of reverse-FK / M2M relation fields, no node-aware optimizer feature work beyond preserving root-gated planning.
5. **Add** a new `all_library_branches_via_list_field` root field to the `library` example (rev2 M1 — do NOT replace `all_library_branches`, which has `order_by("id")` dependencies in existing HTTP tests) so the package ships a live HTTP-tested example of the default `DjangoListField` resolver without mutating any existing field.

## Non-goals

- `DjangoConnectionField` and the Relay-shaped pagination surface. Tracked under `DONE-030-0.0.9` in [`KANBAN.md`][kanban]. Justification: the connection field shipping in `0.0.9` (not `0.0.7`) is a deliberate sequencing decision — connection-aware optimizer planning (`DONE-033-0.0.9`) is the gating dependency, and the connection field has a much larger API surface (edges / pageInfo / pagination args / connection-aware planning) than the list field.
- Filter / order / search / aggregate input arguments on `DjangoListField`. Those are the Layer-3 read-side primitives tracked in `DONE-027-0.0.8` (filters), `DONE-028-0.0.8` (orders), `TODO-BETA-047-0.1.2` (search), `TODO-BETA-049-0.1.3` (aggregates). Once those subsystems ship, `DjangoListField` will pick up the corresponding input arguments under their own specs — this card is the minimum primitive that exists ahead of those.
- Cascade permissions and field-level permissions. Tracked under `DONE-034-0.0.10`. `DjangoListField`'s relationship to [`apply_cascade_permissions`][glossary-apply-cascade-permissions] is a follow-up spec — the per-type `cls.get_queryset(...)` hook continues to cover row-level visibility today.
- Auto-upgrading reverse-FK / M2M many-side relation fields to `DjangoListField`. Relation many-side fields are already shipped as `list[T]` via generated resolvers (see [`Relation handling`][glossary-relation-handling]); `DjangoListField` is the **root** primitive, not a relation-side replacement. See [Decision 7](#decision-7--scope-boundary-vs-relation-list-fields).
- [Multi-database][glossary-multi-database-cooperation] / sharding-aware queryset routing. Tracked under `DONE-023-0.0.7` (the multi-db cooperation contract). `DjangoListField` uses `model._default_manager.all()` which Django routes through the configured database router automatically; nothing in this card precludes the cooperation contract that lands alongside.
- Pagination, limits, ordering defaults. Out of scope by design — `DjangoListField` returns the unbounded queryset. The Relay-connection field is the right home for pagination.
- A flat-list helper class shape that wraps every `DjangoType` declaration (e.g., `class MyTypeListField(DjangoListField): pass`). Not needed; `DjangoListField(MyType)` at the call site is sufficient.

## Borrowing posture

The two reference packages at the paths given in `docs/TREE.md` ship a similar primitive. The slice should borrow patterns, not implementations.

### From `graphene-django` — borrow the user-facing shape

Local source path: `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/fields.py::DjangoListField` (referenced from `docs/TREE.md #"## graphene_django"`).

- **`DjangoListField` symbol name.** Same name, same role. Justification: `graphene-django` migrants searching the package for the primitive they already use should find it by the same import name.
- **Default-resolver shape — model-derived manager → type-level visibility hook.** `graphene_django/fields.py::DjangoListField` (the `get_manager` / `list_resolver` methods) derives the manager from `_type._meta.model._default_manager`, calls `_type.get_queryset(queryset, info)`, returns the queryset. We borrow this contract verbatim. Justification: the contract is exactly what consumers expect when they read "list field for a `DjangoType`"; the only adaptation is that our `DjangoType.get_queryset` is a `classmethod`, not a `staticmethod` ([`docs/GLOSSARY.md#get_queryset-visibility-hook`][glossary-get-queryset-visibility-hook]).
- **Item-level non-null; outer-level via consumer annotation.** `graphene_django/fields.py::DjangoListField.__init__ #"List(NonNull(_type))"` wraps the type as `List(NonNull(_type))`. We borrow the item-non-null part (Django ORM never returns `None` rows from a queryset); the outer nullability is driven by the **consumer's class-attribute annotation** rather than a constructor kwarg (rev2 H2 — `list[BranchType]` → `[BranchType!]!`, `list[BranchType] | None` → `[BranchType!]`). Justification: Strawberry already reads the class-attribute annotation for the field's GraphQL type; a separate `nullable_list=` toggle would either fight the annotation or silently override it.
- **`maybe_queryset` coercion of `Manager`-shaped returns + `get_queryset` application on consumer-resolver returns.** `graphene_django/fields.py::DjangoListField.list_resolver` calls `maybe_queryset(...)` so a consumer resolver returning `Model.objects` (the Django shorthand) is coerced via `.all()`, AND then applies `_type.get_queryset(queryset, info)` to any `QuerySet` returned. We borrow BOTH halves of this — the **field wrapper itself** performs the `Manager → QuerySet` coercion (`result.all()`) BEFORE applying `target_type.get_queryset(...)` so the visibility hook receives a `QuerySet`, not a `Manager` (rev4 M1). The `DjangoOptimizerExtension._optimize` step's own `Manager` coercion at `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._optimize #"if isinstance(result, models.Manager):"` is a downstream safety net for non-`DjangoListField` root resolvers that happen to return `Model.objects`; the two coercions co-exist (one for visibility-hook correctness inside the field, one for optimizer cooperation at the extension boundary). The `get_queryset` application on consumer-resolver returns is explicit in the field wrapper (rev2 H1 — rev1 incorrectly described graphene-django's behavior and said `DjangoListField` would skip `get_queryset` on consumer returns; that's not what graphene-django does and the visibility-hook contract is too load-bearing to silently drop). Justification: matches graphene-django parity and preserves the documented `get_queryset` contract regardless of whether the consumer supplied a sync OR `async def` custom resolver (rev4 H2). Consumers who genuinely want to bypass `get_queryset` return a Python `list` (already-evaluated) from their resolver; the field detects this and passes the list through unchanged.

### Explicitly do not borrow

- Graphene-django's `wrap_resolve` machinery (`graphene_django/fields.py::DjangoListField.wrap_resolve`). Strawberry's resolver assignment is direct (`strawberry.field(resolver=...)`), and graphene-django's `partial(self.list_resolver, …)` wrapping is the graphene-side equivalent. We use Strawberry's native shape.
- Graphene-django's `_type.of_type.of_type` unwrap dance (`graphene_django/fields.py::DjangoListField.wrap_resolve #"_type.of_type.of_type"`) — the type wrapping is different in Strawberry; we annotate `list[T]` directly.
- `strawberry-graphql-django` does NOT ship a direct `DjangoListField` analogue — its closest primitive is `strawberry_django.field()` returning a `list[T]` of a strawberry-django type. That mechanism is decorator-based and contradicts the `class Meta`-driven posture in [`README.md`][readme] and [`GOAL.md`][goal]. No borrow there.

## User-facing API

The shipped consumer surface in `0.0.7` adds exactly one new public export (`DjangoListField`) to `django_strawberry_framework`. No other public names change.

### Default usage — root list field

```python path=null start=null
import strawberry
from django_strawberry_framework import (
    DjangoListField,
    DjangoOptimizerExtension,
    DjangoType,
    finalize_django_types,
)
from apps.library import models


class BranchType(DjangoType):
    class Meta:
        model = models.Branch
        fields = ("id", "name", "city", "shelves")


@strawberry.type
class Query:
    all_library_branches: list[BranchType] = DjangoListField(BranchType)


finalize_django_types()

schema = strawberry.Schema(
    query=Query,
    extensions=[DjangoOptimizerExtension()],
)
```

Expected GraphQL behavior:

- `Query.allLibraryBranches: [BranchType!]!` (item-non-null + list-non-null by default).
- The resolver returns `Branch._default_manager.all()`, threaded through `BranchType.get_queryset(qs, info)`.
- `DjangoOptimizerExtension` plans `select_related` / `prefetch_related` / [`only()`][glossary-only-projection] for nested selections.
- Async resolvers awaiting `BranchType.get_queryset` work without consumer wiring.

### Custom resolver override

```python path=null start=null
from typing import Any

from strawberry.types import Info


def _branches_with_recent_loans(root: Any, info: Info) -> models.QuerySet:
    return models.Branch.objects.filter(shelves__books__loans__isnull=False).distinct()


@strawberry.type
class Query:
    branches_with_recent_loans: list[BranchType] = DjangoListField(
        BranchType,
        resolver=_branches_with_recent_loans,
    )
```

When `resolver=` is supplied, the consumer's body runs instead of the default `model._default_manager.all()` call. The field then applies `BranchType.get_queryset(qs, info)` to the return value when it is a `Manager` or `QuerySet` (rev2 H1, graphene-django parity per `graphene_django/fields.py::DjangoListField.list_resolver`). Consumers who genuinely want to bypass `get_queryset` return a Python `list` (already-evaluated) from their resolver — the field detects this with `isinstance(result, (Manager, QuerySet))` and passes a non-queryset return through unchanged.

**Async consumer resolvers** (rev4 H2): an `async def` resolver returning a `Manager`/`QuerySet` is awaited before the `isinstance` check, so `get_queryset` is applied to the awaited value — async-vs-sync is not a contract surface. The factory inspects `inspect.iscoroutinefunction(resolver)` at construction time to decide which wrapper shape to build.

```python path=null start=null
# Rev6 M3: async-resolver example. Django's ORM is sync-by-default, so the typical
# shape wraps the queryset construction in ``sync_to_async``. The returned QuerySet
# still receives ``BranchType.get_queryset(...)`` exactly like the sync example above.
from asgiref.sync import sync_to_async


async def _branches_with_recent_loans_async(root: Any, info: Info) -> models.QuerySet:
    return await sync_to_async(
        lambda: models.Branch.objects.filter(
            shelves__books__loans__isnull=False,
        ).distinct()
    )()


@strawberry.type
class Query:
    branches_with_recent_loans_async: list[BranchType] = DjangoListField(
        BranchType,
        resolver=_branches_with_recent_loans_async,
    )
```

Resolver signature is the Strawberry-native `(root: Any, info: Info)` shape (rev4 H1 — `info` MUST be annotated `strawberry.types.Info` or Strawberry's schema construction raises `MissingArgumentsAnnotationsError`; `**kwargs` is NOT a harmless catch-all because Strawberry treats every parameter as a GraphQL argument). Filter / order arguments arrive in future Layer-3 cards under their own specs.

Optimizer cooperation still applies because the optimizer extension is root-gated and runs on whatever queryset the field returns.

### Nullable outer list

The outer-list nullability is controlled by the **consumer's class-attribute annotation** (rev2 H2 — `DjangoListField` does NOT take a `nullable_list=` constructor argument). Strawberry reads the annotation directly to render the GraphQL type:

```python path=null start=null
all_branches: list[BranchType] = DjangoListField(BranchType)                  # [BranchType!]!  (non-null outer)
all_branches_or_none: list[BranchType] | None = DjangoListField(BranchType)   # [BranchType!]   (nullable outer)
```

Item-level non-null is the same in both shapes — Django ORM never returns `None` rows from a queryset.

### Field-level GraphQL metadata

```python path=null start=null
all_library_branches: list[BranchType] = DjangoListField(
    BranchType,
    description="Every branch in the library system, ordered by Django default.",
    deprecation_reason=None,
    directives=(),
)
```

These pass through to the underlying Strawberry field unchanged. Justification: feature-comparable with `strawberry.field(...)` so consumers do not have to fall back to a hand-rolled `@strawberry.field` to attach a description.

## Architectural decisions

### Decision 1 — Module location, mechanism, & public export

**Mechanism (rev2 H2).** `DjangoListField` is a **factory function**, not a class. It returns a `strawberry.field(resolver=<wrapped>, description=..., deprecation_reason=..., directives=...)` with the resolver wrapped per [Decision 2](#decision-2--default-resolver-shape). The consumer's class-attribute annotation (`all_branches: list[BranchType]`) is what Strawberry reads to derive the field's GraphQL type; the factory does not own or override that annotation.

Rev1 sketched two implementation paths that don't survive contact with the installed Strawberry — "subclass `strawberry.field`" (it's a function, not a class) and "return a `StrawberryField` from `__set_name__`" (`__set_name__` cannot replace the already-assigned class attribute with its return value). Neither is viable. The factory-function shape was confirmed against `strawberry.field(...)` returning the right kind of `StrawberryField` for both class-attribute and resolver-attached usage.

**Module location.** `DjangoListField` lives in **`django_strawberry_framework/list_field.py`** (new flat single-file Layer-3 module at the package root), NOT in a hypothetical `connection.py` that does not yet exist.

Justification:

- The card's "Files likely touched" entry lists `list_field.py` and `connection.py` as alternatives; this spec picks `list_field.py`.
- `docs/TREE.md #"## django_strawberry_framework (current on-disk layout)"` documents flat single-file Layer-3 modules at the package root (`fieldset.py`, `permissions.py`, `connection.py`) as the canonical placement when a Layer-3 module is a single file. `list_field.py` slots in next to those.
- `DjangoConnectionField` (`DONE-030-0.0.9`) is the future tenant of `connection.py`. Bundling `DjangoListField` into the same module would either force the connection file to ship two unrelated symbols when it lands, or force a rename / move when the connection card ships. Separating them keeps each module focused and aligns the package tree with the [`docs/TREE.md`][tree] target.
- The mirror rule in `docs/TREE.md #"tests/test_<module>.py (flat, at the root)"` ("`tests/test_<module>.py` (flat, at the root) — single-file Layer-3 module tests") pairs `tests/test_list_field.py` with `list_field.py` automatically.

Public-export surface:

- `django_strawberry_framework/__init__.py` adds `from .list_field import DjangoListField` (alphabetical position between `BigInt` and `DjangoOptimizerExtension`).
- `__all__` gains `"DjangoListField"`. Justification: the public-surface promise in `README.md` says today's names remain stable through `0.1.0`; this card adds, never removes.
- `tests/base/test_init.py`'s pinned `__all__` assertion is updated in the same commit so the surface check stays accurate.

Alternatives considered (and rejected):

- **Bundle into `connection.py` from `DONE-030-0.0.9`**. Rejected: forces `0.0.7` to author a module whose primary tenant ships in `0.0.9`; the `connection.py` API will be substantially richer (edges / pageInfo) and bundling `DjangoListField` there leaks naming ambiguity.
- **Inline into `__init__.py`**. Rejected: `__init__.py` is a re-export hub today, not a module body. Adding a class definition there would violate the existing convention.
- **A `fields/` subpackage with `fields/list_field.py`**. Rejected: the target layout in `docs/TREE.md #"## django_strawberry_framework (current on-disk layout)"` reserves subpackages for Layer-3 subsystems with three-plus modules; a single file is a flat module per the TREE convention.

### Decision 2 — Default resolver shape

The factory function captures `target_type` via closure and builds a wrapped resolver whose signature matches Strawberry's contract (rev2 H3 + rev4 H1 — Strawberry calls a field resolver with `(root, info)` where `info` MUST be annotated `strawberry.types.Info`; `**kwargs` is NOT a harmless catch-all because Strawberry treats every parameter as a GraphQL argument). Sketch:

```python path=null start=null
# django_strawberry_framework/list_field.py
import inspect
from typing import Any, Callable

from django.db import models
from strawberry.types import Info
from strawberry.utils.inspect import in_async_context

from .types.relay import _apply_get_queryset_async, _apply_get_queryset_sync


# Module-scope post-processing helpers (rev6 H2 — pinned at module-scope, NOT inside
# the factory body, so they're referentially transparent and unit-testable independently
# of `DjangoListField(...)`. `target_type` and `info` are explicit parameters per rev5 M4.
# Used ONLY by the consumer-resolver wrapper (`_wrap` below); the default-resolver path
# bypasses these because `qs` is already known to be a QuerySet from `Manager.all()` —
# no coercion or isinstance branching is needed there. The `_consumer` suffix in the
# names makes the per-consumer-resolver scope explicit per rev6 H3.)

def _post_process_consumer_sync(target_type: type, result: Any, info: Info) -> Any:
    if isinstance(result, models.Manager):
        result = result.all()  # field-wrapper Manager → QuerySet coercion (rev4 M1).
    if isinstance(result, models.QuerySet):
        return _apply_get_queryset_sync(target_type, result, info)
    return result  # Python list / generator — pass through.


async def _post_process_consumer_async(target_type: type, result: Any, info: Info) -> Any:
    if isinstance(result, models.Manager):
        result = result.all()
    if isinstance(result, models.QuerySet):
        return await _apply_get_queryset_async(target_type, result, info)
    return result


def DjangoListField(  # noqa: N802  # PascalCase for graphene-django parity (rev5 L1).
    target_type: type,
    *,
    resolver: Callable | None = None,
    description: str | None = None,
    deprecation_reason: str | None = None,
    directives: tuple = (),
):
    # Validate target_type per Decision 5.

    if resolver is None:
        def _default(root: Any, info: Info):
            qs = target_type.__django_strawberry_definition__.model._default_manager.all()
            if in_async_context():
                # Rev6 H1: return the coroutine from `_apply_get_queryset_async` directly.
                # Strawberry's AwaitableOrValue dispatch awaits it; an inner `async def`
                # wrapper would add a redundant coroutine layer with no semantic gain.
                return _apply_get_queryset_async(target_type, qs, info)
            return _apply_get_queryset_sync(target_type, qs, info)
        wrapped = _default
    else:
        user_resolver = resolver
        if inspect.iscoroutinefunction(user_resolver):
            # Async consumer resolver (rev4 H2) — await the coroutine BEFORE the
            # isinstance check, otherwise `isinstance(coroutine, QuerySet)` is False
            # and the get_queryset application gets silently skipped.
            async def _wrap(root: Any, info: Info):
                return await _post_process_consumer_async(
                    target_type, await user_resolver(root, info), info,
                )
        else:
            def _wrap(root: Any, info: Info):
                return _post_process_consumer_sync(target_type, user_resolver(root, info), info)
        wrapped = _wrap

    # (Rev5 H1: the rev4 runtime-fallback branch — `if inspect.iscoroutine(result):` inside
    # the sync `_wrap` body — was removed as YAGNI. `inspect.iscoroutinefunction` covers
    # normal `async def` resolvers; consumers wrapping an async function in `functools.partial`
    # rewrap in `async def` instead. Dropping the fallback keeps the wrapper coverable under
    # the package's 100% gate.)

    return strawberry.field(
        resolver=wrapped,
        description=description,
        deprecation_reason=deprecation_reason,
        directives=directives,
    )
```

Where `_apply_get_queryset_sync` and `_apply_get_queryset_async` are imported from `django_strawberry_framework/types/relay.py` (or relocated to a shared site — see [Decision 3](#decision-3--get_queryset-and-async-symmetry)).

**Async-detection asymmetry — intentional, not a harmonization candidate** (rev5 H2). Two different detection mechanisms appear above:

- The **default** resolver uses **runtime** `in_async_context()` inside a plain `def _default(...)` body that lazily returns either a value or a coroutine. Strawberry handles `AwaitableOrValue` from sync resolvers, so the same factory output dispatches correctly under both `schema.execute_sync(...)` and `await schema.execute(...)`. This is the same pattern the optimizer extension uses at `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.resolve`.
- The **consumer-resolver wrapper** uses **construction-time** `inspect.iscoroutinefunction(user_resolver)` to commit to either an `async def _wrap` or a plain `def _wrap`. The wrapper has to be statically sync OR async at factory time because Strawberry inspects the resolver's signature once at schema construction and commits to async-vs-sync handling globally — an `async def` wrapper lets Strawberry await it directly without going through `AwaitableOrValue`.

Harmonizing the two would either force the default into static commitment (loses sync-callability) or force the consumer wrapper into lazy upgrade (adds an extra coroutine layer per call). Both mechanisms are correct for their respective dispatch sites; a future maintainer noticing the asymmetry should leave it alone.

Justification:

- Queryset source `model._default_manager.all()` matches graphene-django (`graphene_django/fields.py::DjangoListField.get_manager`) and matches our own Relay default resolver shape (`django_strawberry_framework/types/relay.py::_initial_queryset`).
- `cls.get_queryset(qs, info)` is the load-bearing visibility hook documented in [`docs/GLOSSARY.md#get_queryset-visibility-hook`][glossary-get-queryset-visibility-hook]. The field MUST apply it on EVERY queryset-shaped return value — default OR consumer-resolver — to preserve the visibility-hook contract (rev2 H1, graphene-django parity).
- Returning a `QuerySet` (not a Python `list`) from the default path is required for the existing root-gated `DjangoOptimizerExtension` plan to apply — see [Decision 4](#decision-4--optimizer-cooperation). The default path always returns a `QuerySet`; a consumer who deliberately wants to bypass the optimizer can return a Python `list` and the field will pass it through unchanged.
- Sync + async paths are symmetric with the Relay defaults from spec-011 Decision 9 — same `in_async_context()` detection, same coroutine-in-sync rejection, same async-awaits-`get_queryset` contract. Justification: shipping a second async/sync detection mechanism for `DjangoListField` would fragment the codebase; reusing the Relay helpers keeps one source of truth.

Item-level non-null is unconditional — Django ORM never returns `None` rows from a queryset (matches `graphene_django/fields.py::DjangoListField.__init__ #"Django would never return a Set of None"`'s comment).

Outer-level nullability is driven by the **consumer's class-attribute annotation** (rev2 H2): `list[T]` → `[T!]!`; `list[T] | None` → `[T!]`. The factory does NOT take a `nullable_list=` constructor argument because Strawberry already reads the class-attribute annotation; a separate kwarg would either fight or silently override it.

Alternatives considered (and rejected):

- **Default resolver returns a Python `list` after `qs.all()` evaluation**. Rejected: the optimizer would never engage because the root-resolver `_optimize` hook checks `isinstance(result, models.QuerySet)` (`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._optimize #"if not isinstance(result, models.QuerySet):"`). Returning a `list` breaks N+1 cooperation.
- **Skip `cls.get_queryset` application on consumer-resolver returns** (rev1's contract). Rejected by rev2 H1: graphene-django applies `get_queryset` to consumer-resolver `QuerySet` returns too (`graphene_django/fields.py::DjangoListField.list_resolver`); the rev1 contract weakened the visibility hook and incorrectly claimed graphene-django parallelism. The corrected contract still gives consumers an explicit bypass — return a Python `list` — without making the bypass the default.
- **`nullable_list=` constructor argument** (rev1's design). Rejected by rev2 H2 — Strawberry already reads the consumer's class-attribute annotation; a separate kwarg would either fight or silently override that annotation, and the implementation needed to render the schema annotation back into Strawberry would require constructing a `StrawberryField` directly (not via `strawberry.field(...)`), which is a meaningful complexity bump for a shape the consumer can express with one extra `| None`.
- **First-positional `(type_cls, info)` resolver signature** (rev1's pseudocode). Rejected by rev2 H3 — Strawberry calls field resolvers with `(root, info)` (annotated `(root: Any, info: Info)` per rev4 H1), not `(type_cls, info)`. The target type must be captured via closure inside the factory; this is the same shape graphene-django's `partial(self.list_resolver, django_object_type, ...)` uses (`graphene_django/fields.py::DjangoListField.wrap_resolve #"partial("`).
- **Catch-all `**kwargs` in the resolver signature** (rev1 / rev2 / rev3 pseudocode used `**kwargs` defensively). Rejected by rev4 H1 — Strawberry treats every parameter as a GraphQL argument by default; an annotated `**kwargs: Any` is interpreted as a `kwargs` argument and later fails schema construction with `Unexpected type 'typing.Any'`; an unannotated `**kwargs` fails earlier with `MissingArgumentsAnnotationsError`. GraphQL arguments for filter/order/search land in their own Layer-3 specs (`DONE-027-0.0.8` / `DONE-028-0.0.8` / `TODO-BETA-047-0.1.2`) with named, typed kwargs; this card does not anticipate them.
- **Accepting `null=True` on the item type** (folded in from rev2 Risks per rev3 L2). Rejected for `0.0.7` — Django querysets never yield `None` rows, so `list[T | None]` is meaningless at the resolver layer. Revisit if a Layer-3 filter that returns sparse results (e.g., a partial keyed lookup) needs it; not on the current roadmap.

### Decision 3 — `get_queryset` and async symmetry

The sync + async `cls.get_queryset(...)` cooperation is delegated to the existing helpers in `django_strawberry_framework/types/relay.py`:

- `_apply_get_queryset_sync(cls, qs, info)` at `django_strawberry_framework/types/relay.py::_apply_get_queryset_sync` — applies the hook in a sync context; rejects a coroutine return with `ConfigurationError` (the same error the Relay defaults raise per spec-011 Decision 9).
- `_apply_get_queryset_async(cls, qs, info)` at `django_strawberry_framework/types/relay.py::_apply_get_queryset_async` — applies the hook in an async context; awaits awaitables; passes sync returns through.

Async detection re-uses the same `in_async_context` symbol the Relay defaults use — the canonical import is `from strawberry.utils.inspect import in_async_context` (rev3 M7; verified at `django_strawberry_framework/types/relay.py #"from strawberry.utils.inspect import in_async_context"`). The `list_field.py` module imports it from the same site; no fork.

Two options were considered for the placement of these helpers:

- **Option A**: keep them in `django_strawberry_framework/types/relay.py` and have `list_field.py` import them as `from .types.relay import _apply_get_queryset_sync, _apply_get_queryset_async`.
- **Option B**: relocate them to a shared `django_strawberry_framework/utils/get_queryset.py` so both `types/relay.py` and `list_field.py` import from a neutral site.

This spec picks **Option A** for `0.0.7`. Justification: Option B is a refactor with a wider blast radius (`types/relay.py` tests are extensive and reference the helpers by name); the helpers are not part of the public surface (underscore prefix); the cross-module import from `list_field.py` is a single line. Option B becomes the right move when a third call site needs the helpers — likely `DjangoConnectionField` in `DONE-030-0.0.9` — at which point that card folds the relocation into its own slice.

Alternatives considered (and rejected):

- **Inline copies of `_apply_get_queryset_*` in `list_field.py`**. Rejected: two source-of-truth sites for the coroutine-in-sync rejection contract; a future change to the rejection message has to touch both.
- **A new `list_field.py`-local async detection mechanism**. Rejected: would fork the in-tree `in_async_context()` usage and force the test suite to validate the same contract twice.

### Decision 4 — Optimizer cooperation

`DjangoListField` does NOT touch the optimizer source code. The cooperation contract is:

- The default resolver returns a `QuerySet` (not a Python `list`).
- The root-gated `DjangoOptimizerExtension.resolve` hook (`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.resolve`) fires on `info.path.prev is None`; the field site IS a root (top-level `Query` field), so the hook fires.
- `_optimize` (`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._optimize`) accepts both `Manager` and `QuerySet`; the field returns a `QuerySet` so the existing coercion is a no-op.
- The selection-tree walker (`django_strawberry_framework/optimizer/walker.py`) reads the target `DjangoType` from `_resolve_model_from_return_type(info)` — defined at `django_strawberry_framework/optimizer/extension.py::_resolve_model_from_return_type`, called inside `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._optimize #"resolved = _resolve_model_from_return_type(info)"` (rev3 M4 — the call site is where the lookup happens; the definition is where the logic lives). The return-type machinery already handles `list[T]` annotations.
- Plan caching, FK-id elision, `only()` projection, [queryset diffing][glossary-queryset-diffing], strictness mode — all shipped, all apply unchanged.

Justification: the optimizer's contract is "give me a `QuerySet` at the root; I'll walk the selection tree once." `DjangoListField` is a primitive that produces a `QuerySet`; it inherits every shipped optimizer feature for free.

**Scope narrowing — root only in `0.0.7`** (rev2 M3). The optimizer extension is explicitly root-gated on `info.path.prev is None`. A `DjangoListField` used at a **nested non-root** position on a Strawberry type — for example, a child `@strawberry.type` carrying `more_items: list[ItemType] = DjangoListField(ItemType)` — produces a functional list resolver (the default body still runs and `get_queryset` is still applied), but the optimizer's `resolve` hook does NOT fire because `info.path.prev` is not `None`. The `0.0.7` shipped contract is therefore **root list fields only**; nested non-root use works but is not root-optimized. The connection card (`DONE-030-0.0.9`) and any follow-up spec may revisit nested optimization explicitly. Pinned by `test_djangolistfield_at_root_position_is_optimized` in `tests/test_list_field.py` (a sibling negative test for the nested-non-root case is NOT required in `0.0.7` because the contract is "we don't promise optimization there", not "we promise non-optimization there").

The slice MUST add an optimizer-side test (in `tests/test_list_field.py`) that confirms the planned `select_related` / `prefetch_related` for a nested selection on a `DjangoListField`-served collection at the **root** position. The Slice 4 live HTTP test in `examples/fakeshop/test_query/test_library_api.py` covers the same selection shape end-to-end. The duplication is intentional and the two tests pin different contracts (rev3 M6): the package-internal test pins the **return-shape contract** (the default resolver returns a `QuerySet`, not a Python `list` — the regression that breaks N+1 cooperation silently), while the HTTP test pins the **end-to-end contract** (URL routing + view + schema execution + JSON serialization survive the round trip). Both fail modes can fly past each other in different ways — e.g., a refactor that accidentally calls `qs.all()` and returns a list passes the HTTP test (because the rows still come back) but fails the package-internal test (because the optimizer never engaged); a Django middleware change can break the HTTP path without affecting the in-process schema execution. Keeping both is the regression net.

Alternatives considered (and rejected):

- **Bypass the root gate for `DjangoListField`**. Rejected: there is nothing to bypass; the gate already fires at the root.
- **Extend the optimizer hook to recognize nested `DjangoListField` and plan there too**. Rejected: an in-scope optimizer change for `0.0.7`; the connection card has the same need and is the right home for the broader nested-optimization design.
- **Add a `DjangoListField`-specific marker on `info.context`** so the optimizer can recognize the field. Rejected: not needed — the existing return-type machinery already identifies the target type; no marker improves the plan.

### Decision 5 — Validation & error shapes

The `DjangoListField(arg, *, resolver=None, description=None, deprecation_reason=None, directives=())` constructor validates:

- `arg` is a class (`inspect.isclass(arg)`); otherwise `ConfigurationError("DjangoListField requires a DjangoType class; got <repr>.")`.
- `arg` is `issubclass(arg, DjangoType)`; otherwise `ConfigurationError("DjangoListField requires a DjangoType subclass; got <name>.")`.
- `arg` is registered — i.e., `hasattr(arg, "__django_strawberry_definition__")` is `True`; otherwise `ConfigurationError("DjangoListField target <name> is not a registered DjangoType (no __django_strawberry_definition__). This usually means <name>'s `Meta` is missing a `model` declaration.")`. (Rev3 M3 anchor: the attribute is assigned at `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__ #"cls.__django_strawberry_definition__ = definition"` — only when the `DjangoType` subclass carries a `Meta` with a `model`; abstract `DjangoType` bases without that condition pass through `__init_subclass__` without the attribute, so `hasattr(...)` is a sufficient discriminator.)
- `resolver`, when supplied, is callable; otherwise `ConfigurationError("DjangoListField resolver must be callable.")`.

(Rev2 H2: `nullable_list=` is NOT a constructor argument; outer nullability is driven by the consumer's class-attribute annotation. No bool check needed.)

Error site count: one new error site (the `DjangoListField` constructor). All errors raise [`ConfigurationError`][glossary-configurationerror].

The error messages follow the same `<Symbol> <constraint>; got <repr>.` shape pattern that `types/base.py:_format_unknown_fields_error` uses for consistency with the rest of the package's validation surface.

Why not validate at type-decoration / finalization time:

- The validation rules are local to the constructor — no cross-class state is needed.
- Failing at the construction site means the error appears at the line that wrote `DjangoListField(...)`, which is easier to debug than a delayed `finalize_django_types()` error.
- Symmetric with how `OptimizerHint`-related Meta validation fires at type creation today.

Alternatives considered (and rejected):

- **Defer validation to `finalize_django_types()`**. Rejected: the consumer doesn't necessarily call `finalize_django_types()` before they expect `DjangoListField(...)` to either work or fail; delayed errors are harder to localize. Same posture as `OptimizerHint`'s class-creation-time validation.
- **Accept a model class instead of a `DjangoType`**. Rejected: with `Meta.primary` shipped, "model → DjangoType" lookup is ambiguous when multiple `DjangoType`s exist on the same model. Requiring an explicit `DjangoType` argument side-steps this entirely (see [Decision 6](#decision-6--metaprimary-interaction)).

### Decision 6 — `Meta.primary` interaction

`DjangoListField(TargetType)` takes a concrete `DjangoType` subclass as its argument — never a model class. This means:

- For a model with one `DjangoType`, no `Meta.primary` declaration, current behavior — `DjangoListField(TargetType)` is unambiguous and works.
- For a model with multiple `DjangoType`s where one carries `Meta.primary = True` — `DjangoListField(PrimaryType)` and `DjangoListField(SecondaryType)` both work; each is bound to the explicit target's queryset, `get_queryset` hook, and (if any) optimizer hints. No registry lookup happens.
- For a model with multiple `DjangoType`s where the primary ambiguity hasn't been resolved (no `Meta.primary` declared on any) — `finalize_django_types()` raises `ConfigurationError` already (spec-014 Decision); `DjangoListField` is downstream and inherits the same loud failure mode.

Justification:

- The explicit-target shape is the same as how the existing relation-resolver paths handle multi-type-per-model — annotation overrides like `category: AdminCategoryType` and assigned `strawberry.field` relation resolvers can target a secondary type unchanged ([`docs/GLOSSARY.md#metaprimary`][glossary-metaprimary], "Multiple `DjangoType`s, exactly one with `Meta.primary = True` — allowed; relation targets resolve to the primary"). `DjangoListField` follows the same explicit-target shape.
- The optimizer's [plan cache][glossary-plan-cache] keys include the resolver's origin Strawberry type ([`docs/GLOSSARY.md#metaprimary`][glossary-metaprimary] — "a primary-return and a secondary-return resolver on the same model do not share a cached plan"). `DjangoListField(PrimaryType)` and `DjangoListField(SecondaryType)` produce two distinct plans; no cache-poisoning risk.

Tests in `tests/test_list_field.py` must cover:

- `test_djangolistfield_with_meta_primary_true_returns_primary_queryset` — declare two `DjangoType`s on the same model, one with `Meta.primary = True`; `DjangoListField(PrimaryType)` returns rows queried via the primary's `get_queryset`.
- `test_djangolistfield_with_secondary_target_uses_secondary_get_queryset` — declare two types, point the field at the secondary; the secondary's `get_queryset` is applied, not the primary's.

Alternatives considered (and rejected):

- **Accept a model class and look up the primary `DjangoType`**. Rejected: requires a registry call at construction time AND makes the field implicitly subject to `Meta.primary` reordering, which is brittle.
- **Default to the primary when an ambiguous model is passed**. Rejected: same brittleness as above; explicit target is unambiguous.
- **Add `DjangoListField.for_model(Model)` classmethod sugar** (folded in from rev2 Risks per rev3 L2). Rejected for `0.0.7` — the explicit-target shape (`DjangoListField(MyType)`) is the canonical form and matches graphene-django's `DjangoListField(_type)` plus the existing relation-side `category: AdminCategoryType` annotation-override path. Revisit only if real-world `Meta.primary` adopters report ergonomic pain; not on the current roadmap.

### Decision 7 — Scope boundary vs relation list fields

`DjangoListField` is the **root** primitive — it adds a new list-shape field to a `Query` class (or any `@strawberry.type` class). It is NOT the relation-side many-list field; that path is already shipped via generated relation resolvers (see [`docs/GLOSSARY.md#relation-handling`][glossary-relation-handling]):

> reverse `ForeignKey` → `list[target_type]`. The optimizer plans `prefetch_related`. Many-side resolvers return Python lists, not Django managers.

This card does NOT:

- Replace the generated relation resolvers with `DjangoListField`-based plumbing.
- Change the shape of many-side relation fields (still `list[T]`, still returned as Python lists from generated resolvers).
- Auto-upgrade reverse-FK / M2M fields to use `DjangoListField`.

Justification: relation many-side resolvers ship today and are well-tested; rewriting them under `DjangoListField` is a refactor with no consumer-visible benefit and a non-trivial blast radius. The two primitives (root list field via `DjangoListField`, relation list field via generated resolver) live side-by-side cleanly because they target different call sites.

A future spec MAY consider unifying the two — likely when the connection field lands and the relation-side many-list field grows up to a connection auto-upgrade. That decision belongs to the connection spec (`DONE-030-0.0.9`), not this one.

### Decision 8 — Out-of-scope boundary with `DjangoConnectionField`

`DjangoListField` and `DjangoConnectionField` ([`DONE-030-0.0.9`][kanban]) are sibling primitives. Both bind to a `DjangoType`; both apply `cls.get_queryset(...)`; both cooperate with the optimizer.

Boundary line:

- `DjangoListField` returns `list[T!]!` (or `list[T!]`); no pagination, no edges, no `pageInfo`, no Relay arguments.
- `DjangoConnectionField` returns `Connection[T]` with `edges` / `node` / `pageInfo` / `totalCount` and Relay pagination arguments (`first` / `after` / `last` / `before`).
- Filter / order / search / aggregate input arguments are added to BOTH primitives by the relevant Layer-3 spec when those subsystems ship; the input-shape contract is the same across both.

A consumer migrating from `DjangoListField` to `DjangoConnectionField` later:

```diff
- all_branches: list[BranchType] = DjangoListField(BranchType)
+ all_branches: DjangoConnection[BranchType] = DjangoConnectionField(BranchType)
```

Same `DjangoType` argument; same `get_queryset` cooperation; same optimizer integration; richer return shape.

Alternatives considered (and rejected):

- **Single `DjangoField` symbol with a `connection=True/False` argument**. Rejected: the two return shapes are different (`list[T]` vs `Connection[T]`); a single symbol would mean two return-type contracts depending on the boolean, fragmenting the type-annotation story.
- **Inherit `DjangoConnectionField` from `DjangoListField`**. Rejected: the connection field has fundamentally different output-shape machinery (edges, pageInfo) that don't compose well as a subclass; the better factoring is shared helpers (`_apply_get_queryset_sync` / `_apply_get_queryset_async`, future `_optimizer_root_gate` helper) — both fields use the same helpers without an inheritance relationship.

### Decision 9 — Example-app migration posture

This card **adds** a new root field `all_library_branches_via_list_field: list[BranchType] = DjangoListField(BranchType)` to `examples/fakeshop/apps/library/schema.py`'s `Query` class. It does NOT replace any existing `all_library_*` resolver (rev2 M1 — rev1 picked `all_library_branches` for replacement, but that resolver's `order_by("id")` is depended on by `test_library_relation_override_shapes_http_response_data` in `examples/fakeshop/test_query/test_library_api.py`, which seeds two branches and asserts a deterministic order. `Branch` has no model-level `Meta.ordering`, so the default-manager queryset is unordered).

Justification:

- Adding a sibling field keeps the existing seven `@strawberry.field` resolvers and their HTTP-test dependencies untouched. The new field exercises the default `DjangoListField` resolver code path cleanly, in isolation.
- The other seven `all_library_*` resolvers each carry `order_by("id")` for deterministic test ordering; touching any of them without preserving the order would risk flaky HTTP tests. `0.0.7` does NOT migrate them.
- The `all_library_prefetched_books` resolver uses `Book.objects.select_related("shelf").prefetch_related("genres").order_by("id")` — a consumer-shaped queryset. That resolver MUST stay as a hand-rolled `@strawberry.field` to keep exercising the optimizer's queryset-diffing path (`docs/GLOSSARY.md#queryset-diffing`).

The `library` example schema's prose comment near the top of `schema.py` should be updated in the same slice to mention that `all_library_branches_via_list_field` exercises the new `DjangoListField` primitive while the sibling `all_library_*` resolvers continue to exercise the consumer-resolver / queryset-diffing paths.

**Card-text departure** (rev4 H3). The KANBAN card `DONE-020-0.0.7`'s Definition of done says "Live HTTP coverage **replacing** one of the hand-rolled `all_library_*` resolvers". This spec's add-only posture (rev2 M1) is an intentional departure — the test-determinism win from leaving the ordered resolvers untouched is load-bearing, and the alternative (replacement via consumer resolver) would no longer exercise the default-resolver code path. The Slice 5 `KANBAN.md` doc-update bullet requires the past-tense Done body to reflect the actual ship: `all_library_branches_via_list_field` was **added** alongside the existing resolvers, not in place of one. Readers consulting the card after Done see the add-only language, not the original "replacing" wording.

Alternatives considered (and rejected):

- **Replace `all_library_branches` with `DjangoListField(BranchType)`** (rev1's posture). Rejected by rev2 M1 — drops `order_by("id")` and breaks `test_library_relation_override_shapes_http_response_data` ordering assertions. Pinning a new sibling field is the smaller-blast-radius move.
- **Replace `all_library_branches` with `DjangoListField(BranchType, resolver=lambda: Branch.objects.order_by("id"))`**. Rejected: works under the rev2 H1 contract (consumer resolver still gets `get_queryset` applied), but the explicit resolver argument means the field is no longer exercising the **default-resolver** code path — it exercises the consumer-override path. The whole point of the example is to cover the default path with one HTTP test; the consumer-override path is covered in package-internal `tests/test_list_field.py`.
- **Add `class Meta: ordering = ("id",)` to `Branch`**. Rejected: a model-level ordering change touches every `Branch` query in the test suite (admin, services, schema-execute, HTTP), with effects far beyond this card. Out of scope.
- **Replace all seven non-`prefetched` resolvers**. Rejected: churn that doesn't pin the contract any harder than one addition does (rev3 L1; the rev1 "21 lines for cosmetic gain" arithmetic was loose — a -14 net delta is still churn, just less of it). Same `order_by("id")` risk applies to every sibling.
- **Replace one of the `products` resolvers instead**. Rejected: the `products` schema's documented future shape is Relay-shaped (`relay.ListConnection[CategoryType] = DjangoConnectionField(CategoryType)`); `DjangoListField` is not its natural future home. The library app is the right host.

### Decision 10 — Joint `0.0.7` cut

`0.0.7` ships five WIP cards as a bundle: `DONE-020-0.0.7` (this card), `DONE-021-0.0.7` (`apps.py`), `DONE-022-0.0.7` (schema-export management command), `DONE-023-0.0.7` (multi-db cooperation contract), and `DONE-025-0.0.7` (warning-free scalar registration). The version bump in `pyproject.toml #"version ="` and `django_strawberry_framework/__init__.py #"__version__ ="` and `tests/base/test_init.py`'s pinned version assertion is owned by whichever card ships last in the bundle, NOT this card.

Justification:

- Each individual card lands self-contained code, tests, and docs.
- The version bump is the joint cut-over signal; doing it on each card would cause five overlapping bumps competing for `0.0.7`.
- The CHANGELOG `[0.0.7]` Added entries accumulate across the five cards' Slice 5s; each card writes its own Added line under the same `[0.0.7]` heading.

The Definition of done item that previously said "version bump in `pyproject.toml`" for this card is REMOVED from this slice and deferred to the last `0.0.7` card to ship (rev3 M1 — there is no separate release-cut card in `KANBAN.md`; the policy is "whichever feature card ships last owns the bump").

Alternatives considered (and rejected):

- **Each card bumps independently**. Rejected: the five cards' commits would land in arbitrary order, and the version bump would point at whichever card happened to merge last — fragile and surprising.
- **Block all five cards on a single integration commit**. Rejected: cards lose independence; review surface balloons; the value of slicing the work disappears.

## Implementation plan

The slice ships as **six slices** aligned with the [Slice checklist](#slice-checklist), of which Slice 0 is a verification spike that does NOT produce a commit (rev4 M2 — Slice 0 is a throw-away local check that the factory-function shape integrates with `@strawberry.type`; the stub is discarded after confirmation). Slices 1-5 each map to one commit. The per-commit breakdown exists for review legibility; squashing Slices 1-5 into a single PR is acceptable.

| Slice | Files touched | New tests | Approx. line delta |
| --- | --- | --- | --- |
| 0 — Pre-implementation verification (rev3 H1) | (sandbox; no repo files touched) | 0 (throw-away spike; the stub is discarded after the shape is confirmed) | `0 / 0` |
| 1 — Module + factory function | `django_strawberry_framework/list_field.py` (new), `django_strawberry_framework/__init__.py`, `tests/base/test_init.py` | 0 (validation tests land in Slice 2 / 3) | `+150 / -2` |
| 2 — Validation | `django_strawberry_framework/list_field.py`, `tests/test_list_field.py` (new) | 4 validation tests (rev2 H2: dropped the `nullable_list` bool test) | `+80 / -0` |
| 3 — Optimizer + `get_queryset` cooperation tests | `tests/test_list_field.py` | 14 behavior tests (rev5 M1 — one-to-one with the named methods in [Test plan](#test-plan); rev5 M3 — added the dual-execution test): default resolver applies sync `get_queryset`, default resolver awaits async `get_queryset`, default resolver works under both `schema.execute_sync` and `await schema.execute` (rev5 M3), sync coroutine rejection, sync consumer-resolver `QuerySet` return receives `get_queryset` (rev2 H1), sync consumer-resolver Python-`list` return passes through (rev2 H1), async consumer-resolver `QuerySet` return receives `get_queryset` (rev4 H2), async consumer-resolver Python-`list` return passes through (rev4 H2), nullable-outer via consumer annotation renders `[T!]` (rev2 H2), non-nullable-outer default renders `[T!]!` (rev2 H2), `DjangoListField` at root position is optimized (rev2 M3), FK-id elision survives, `Meta.primary` explicit primary returns primary queryset, `Meta.primary` secondary target uses secondary `get_queryset` | `+280 / -0` (rev6 L3) |
| 4 — Live HTTP coverage | `examples/fakeshop/apps/library/schema.py`, `examples/fakeshop/test_query/test_library_api.py` | 1 new HTTP test for the **added** `all_library_branches_via_list_field` field (rev2 M1; no existing resolver is replaced) | `+25 / -0` |
| 5 — Promotion + docs | `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `README.md`, `TODAY.md`, `KANBAN.md`, `CHANGELOG.md` | 0 | `+65 / -12` |

Total expected delta: ~530 lines across the six slices (Slice 0 contributes no repo-resident lines).

The six slices must be authored in order. Slice 0 is a gating check — Slice 1 begins only after the factory-function shape is verified end-to-end (rev3 H1). Slice 4 depends on Slice 1 (the symbol must exist) and Slice 3 (the contracts must be pinned by tests before consuming the symbol from the example app).

## Edge cases and constraints

- **`Meta.primary` ambiguity not resolved at the registry**. `DjangoListField(TargetType)` accepts an explicit `DjangoType` so the registry's primary/secondary state is irrelevant at the field site. If `finalize_django_types()` later raises a `Meta.primary` ambiguity error for the target's model, that error is the one consumers see — not a `DjangoListField`-specific one.
- **Custom managers via `Meta.default_manager_name`**. Django's `_default_manager` honors the model's `default_manager_name` if set; `DjangoListField` inherits this for free. No special-casing.
- **`null=True` on the row's primary key**. Django does not allow nullable single-column primary keys on normal models; if a future Django version adds support, the `DjangoListField` resolver path passes through unchanged because the field doesn't introspect the pk.
- **Model proxies**. Django proxy models share the underlying table; `_default_manager.all()` returns proxy instances. `DjangoListField` works the same way it does for the base model; the consumer just passes the proxy-backed `DjangoType`.
- **Abstract `DjangoType` bases without a `Meta`**. The validation in [Decision 5](#decision-5--validation--error-shapes) catches this via the "registered DjangoType" check — abstract bases don't have `__django_strawberry_definition__` and raise `ConfigurationError` at construction.
- **Multi-database routing**. `model._default_manager.all()` is routed by Django's database router automatically. The multi-db cooperation contract pinned by `DONE-023-0.0.7` already covers the relation-traversal case; root-list fields inherit the same routing behavior because the queryset is the same `Manager.all()` call relations use.
- **[Strictness mode][glossary-strictness-mode] and N+1 detection**. The optimizer's strictness mode operates at the relation-walk level, not the root-resolver level. `DjangoListField`-served root querysets pass through the strictness contract unchanged.
- **`schema.execute_sync` testing**. The field works under both `schema.execute_sync` (synchronous) and `await schema.execute` (asynchronous) call shapes; the in-async-context detection handles both. Pinned by `test_djangolistfield_default_resolver_works_under_sync_and_async_schema_execution` (rev5 M3).
- **`functools.partial`-wrapped async consumer resolvers**. `inspect.iscoroutinefunction(functools.partial(some_async_fn, ...))` returns `False` in current Python versions, so the factory's construction-time detection treats the partial as a sync resolver and builds a sync `_wrap`. If the partial actually returns a coroutine, the sync wrapper passes the coroutine through `_post_process_consumer_sync` (which checks `isinstance(result, QuerySet)`), the isinstance check is False against a coroutine, and the coroutine is returned unchanged — `get_queryset` is silently skipped. Rev5 H1 chose YAGNI here (no runtime fallback) over keeping a branch that would be hard to cover under the 100% gate. Workaround (rev6 M4 — explicit before/after instead of compressed prose):

  ```python path=null start=null
  # DOES NOT WORK as expected — inspect.iscoroutinefunction returns False for
  # functools.partial wrappers, so DjangoListField builds a SYNC _wrap.
  # The partial's coroutine return passes through the sync wrapper
  # unchanged and BranchType.get_queryset(...) is silently skipped.
  field = DjangoListField(
      BranchType,
      resolver=functools.partial(my_async_resolver, some_arg=1),
  )

  # WORKS — rewrap the partial in an explicit ``async def`` so
  # inspect.iscoroutinefunction sees the async shape at factory
  # construction time and DjangoListField builds an async wrapper.
  async def _wrapped(root: Any, info: Info):
      return await my_async_resolver(root, info, some_arg=1)


  field = DjangoListField(BranchType, resolver=_wrapped)
  ```

## Test plan

Tests live in two trees, matching the rules in [`docs/TREE.md`][tree] and [`AGENTS.md`][agents]. Test-tree placement is mandatory.

### `tests/test_list_field.py` (new)

Package tests; system-under-test is `django_strawberry_framework` (rev5 L3 — trimmed to match `AGENTS.md` #"package tests, system-under-test is django_strawberry_framework itself" framing). The file is the flat single-file Layer-3 module's mirror per `docs/TREE.md #"tests/test_<module>.py (flat, at the root)"`.

Validation tests (Slice 2):

- `test_djangolistfield_rejects_non_class_argument` — passing a string, int, instance, etc., raises `ConfigurationError`.
- `test_djangolistfield_rejects_non_djangotype_class` — passing a plain class that doesn't subclass `DjangoType` raises `ConfigurationError`.
- `test_djangolistfield_rejects_djangotype_without_definition` — passing an abstract `DjangoType` base without a `Meta` raises `ConfigurationError`.
- `test_djangolistfield_rejects_non_callable_resolver` — `resolver="not callable"` raises `ConfigurationError`.

(Rev2 H2: the previously-planned `test_djangolistfield_rejects_non_bool_nullable_list` is dropped — `nullable_list=` is no longer a constructor argument.)

Behavior tests (Slice 3):

- `test_djangolistfield_default_resolver_returns_queryset_filtered_by_get_queryset` — declare a `DjangoType` with `get_queryset` filtering on `is_private=False`; assert the field's default resolver returns a queryset that excludes private rows.
- `test_djangolistfield_async_get_queryset_is_awaited` — declare a `DjangoType` with an `async def get_queryset(...)`; assert the field's default resolver awaits the coroutine in an async context and returns the filtered queryset.
- `test_djangolistfield_default_resolver_works_under_sync_and_async_schema_execution` (rev5 M3) — declare a `DjangoType` with a **sync** `get_queryset(...)`; execute the field via `schema.execute_sync(...)` AND via `await schema.execute(...)`; assert both return the filtered queryset. Pins the runtime `in_async_context()` branch in the default resolver (the case where `in_async_context()` is True but `get_queryset` is sync). Without this test, the dual-execution shape promised in the Edge cases section is unverified.
- `test_djangolistfield_sync_path_rejects_coroutine_from_get_queryset` — declare a `DjangoType` with an `async def get_queryset(...)`; assert the sync resolver raises `ConfigurationError` matching the `django_strawberry_framework/types/relay.py::_apply_get_queryset_sync #"raise ConfigurationError"` contract.
- `test_djangolistfield_consumer_resolver_queryset_return_gets_get_queryset_applied` (rev2 H1) — supply a **sync** `resolver=` returning `Model.objects.filter(...)`; assert the resolved field's queryset has been threaded through `target_type.get_queryset(qs, info)` (verifiable by giving the target a `get_queryset` that filters out a known row, then asserting that row is absent from the field's output).
- `test_djangolistfield_consumer_resolver_python_list_return_passes_through` (rev2 H1) — supply a **sync** `resolver=` returning a Python `list[T]`; assert `target_type.get_queryset(...)` is NOT applied (verifiable by including a row that `get_queryset` would have filtered out and asserting it survives).
- `test_djangolistfield_async_consumer_resolver_queryset_return_gets_get_queryset_applied` (rev4 H2) — supply an `async def resolver(...)` returning `Model.objects.filter(...)`; execute through Strawberry's async schema execution; assert the queryset has been threaded through `target_type.get_queryset(qs, info)` exactly the same way as the sync test. Pins that the wrapper awaits the consumer coroutine BEFORE the isinstance check.
- `test_djangolistfield_async_consumer_resolver_python_list_return_passes_through` (rev4 H2) — supply an `async def resolver(...)` returning a Python `list[T]`; assert `target_type.get_queryset(...)` is NOT applied. Pins that the await-then-isinstance ordering is symmetric across return shapes.
- `test_djangolistfield_at_root_position_is_optimized` (rev2 M3) — declare a `DjangoType` with relations; query through a root `DjangoListField` with a nested selection. Assert **exactly** `N` queries via `assertNumQueries(N)` (rev6 M6 — exact count, not `<= N`; a permissive bound would let a refactor that quietly changes the per-query count slide past unnoticed). `N` is one base SELECT plus one extra SELECT per `prefetch_related` relation in the nested selection (e.g., for `{ allBranches { id name shelves { id } } }` against `Branch` with `shelves` as a reverse-FK, `N = 2` — one Branch SELECT, one Shelf prefetch SELECT). The test docstring documents the derivation so a future maintainer who changes the selection shape can recompute `N` deterministically.
- `test_djangolistfield_nullable_outer_via_consumer_annotation` (rev2 H2) — declare a Query field as `field_or_none: list[BranchType] | None = DjangoListField(BranchType)`; assert the rendered GraphQL type is `[BranchType!]` (nullable outer, non-null items).
- `test_djangolistfield_non_nullable_outer_default_via_consumer_annotation` (rev2 H2) — declare a Query field as `field: list[BranchType] = DjangoListField(BranchType)`; assert the rendered GraphQL type is `[BranchType!]!` (non-null outer, non-null items).
- `test_djangolistfield_fk_id_elision_survives` — query `{ allBranches { shelves { id } } }` (or equivalent); assert no JOIN was issued for the `id`-only relation selection (FK-id elision still fires).
- `test_djangolistfield_with_meta_primary_true_returns_primary_queryset` — see [Decision 6](#decision-6--metaprimary-interaction).
- `test_djangolistfield_with_secondary_target_uses_secondary_get_queryset` — see [Decision 6](#decision-6--metaprimary-interaction).

### `examples/fakeshop/test_query/test_library_api.py` (extend)

System-under-test is the live `/graphql/` HTTP endpoint. Coverage MUST be earned here per the `docs/TREE.md #"**Coverage priority.**"` rule ("Any package coverage line in `django_strawberry_framework/` that can be earned by a real-world GraphQL query against fakeshop MUST be earned in `examples/fakeshop/test_query/`").

Add `test_library_branches_via_djangolistfield_optimized_nested_selection` (or extend an existing test) that:

- issues `{ allLibraryBranchesViaListField { id name shelves { id code } } }` against `/graphql/`;
- asserts the response includes every branch row (order-agnostic — sort by `id` in the assertion if needed since the new field has no `order_by`);
- asserts the optimizer planned `prefetch_related("shelves")` for the nested selection (via the existing `assertNumQueries` / SQL-sniffer pattern in `test_library_api.py`).

`cls.get_queryset` cooperation is **not** asserted by this HTTP test (rev2 M2). The library example's real `BranchType` has no custom `get_queryset` today, and adding one would mutate every `BranchType` path in the schema (including nested `book → shelf → branch` selections and existing branch tests). Package-internal `tests/test_list_field.py` has the dedicated coverage with isolated fixtures.

The HTTP test file's reload pattern from [`docs/TREE.md #"HTTP tests that import the project schema"`][tree] must be preserved: clear the global registry, reload app schema modules, then reload the project schema and URLconf. The new test follows this pattern unchanged.

## Doc updates

- [`docs/GLOSSARY.md`][glossary]
  - Flip [`DjangoListField`][glossary-djangolistfield] from `planned for 0.0.7` to `shipped (0.0.7)`.
  - Update the entry body to describe the shipped contract: factory function (not class), `list[T]` annotation on the class attribute drives outer nullability, default `model._default_manager.all()` resolver, `cls.get_queryset(...)` applied in sync + async contexts AND to consumer-resolver `Manager`/`QuerySet` returns (rev2 H1, graphene-django parity), root-only optimizer cooperation (rev2 M3).
  - Update the [Public exports][glossary-public-exports] list near the top to include `DjangoListField`.
  - Update the Index table's status column.

- [`README.md`][readme]
  - Update the "Shipped today" / status bullet list to mention `DjangoListField`.

- [`docs/README.md`][docs-readme]
  - Add `DjangoListField` to the "Shipped today (`0.0.7`)" bullet list.
  - Optional: add a small example in the Quick start section showing the `DjangoListField` shape next to the existing `@strawberry.field` example.

- [`docs/TREE.md`][tree]
  - Add `list_field.py` to the "current on-disk layout" section.
  - Add `list_field.py` to the "target package layout" section as its own flat single-file Layer-3 module bullet.
  - **Remove `DjangoListField` from the existing `connection.py # [alpha] DjangoConnectionField + DjangoListField` line** so the target layout doesn't advertise two homes for the symbol (rev2 L1).
  - Add `tests/test_list_field.py` to the current test-tree section.

- [`GOAL.md`][goal]
  - Update the "Coming from `graphene-django`" migration subsection at `GOAL.md #"### Coming from \`graphene-django\`"` — add a one-line bullet under the existing diff block noting that `DjangoListField` replaces graphene-django's symbol of the same name with no shape change at the migration site (rev6 M5; the Success criteria mention at `GOAL.md #"Expose model collections with \`DjangoConnectionField\` or \`DjangoListField\`"` is already accurate as a forward-pointer and needs no edit).

- [`TODAY.md`][today]
  - Drop `DjangoListField` from the wait-for list if listed there.
  - Update the `library` summary line to mention that the **new** `all_library_branches_via_list_field` root field exercises `DjangoListField`'s default resolver path (rev2 M1; no existing resolver was replaced).

- [`KANBAN.md`][kanban]
  - Move `DONE-020-0.0.7` to the Done column with the next available `DONE-NNN-0.0.7` id; rewrite the body in past tense using the add-only language (rev4 H3 — the card's original "Live HTTP coverage replacing one of the hand-rolled `all_library_*` resolvers" wording is superseded by the actual shipped posture; the Done body says "added `all_library_branches_via_list_field`", not "replaced ...").

- [`CHANGELOG.md`][changelog]
  - **Append** to the existing `[0.0.7]` `### Added` subsection (create the subsection only if absent; do NOT create a second `[0.0.7]` heading — rev3 M5; the repo's `CHANGELOG.md` already has a `[0.0.7]` section from prior commits this patch, and every `0.0.7` card under the joint cut appends to the same shared section): `DjangoListField` — non-Relay `list[T]` field for **root Query fields**, with default `model._default_manager.all()` resolver, `cls.get_queryset(...)` cooperation in sync + async contexts and on consumer-resolver `Manager`/`QuerySet` returns (graphene-django parity), optimizer cooperation via root-gating, outer nullability driven by the consumer's class-attribute annotation, and standard field-level metadata pass-through (`description`, `deprecation_reason`, `directives`). (Rev2 L2: narrowed wording from "root and nested fields" to "root Query fields"; rev2 H2: removed `nullable_list=True` constructor-toggle phrasing; rev2 H1: added the consumer-resolver `get_queryset` parity phrasing.)
  - The version bump entry is owned by **the last `0.0.7` card to ship** per [Decision 10](#decision-10--joint-0_0_7-cut), NOT this slice (rev3 M1).

## Risks and open questions

Each item names a preferred answer for `0.0.7` and a fallback if implementation reveals the preferred answer is wrong.

(Rev3 L2: the rev2 Risks section ran to eight items; many restated decisions in different words. The list below is the trimmed set of **genuinely open** items — questions whose answers can only come from implementation contact. Items that were really restatements of Decisions have been folded into their owning Decision's "Alternatives considered" block: "ergonomics of `DjangoListField(MyType)`" → Decision 6; "`null=True` on item type" → Decision 2's Alternatives; "`DjangoListField(model_class)` sugar" → Decision 6's Alternatives. "Nested non-root usage" stayed in [Decision 4](#decision-4--optimizer-cooperation)'s Scope-narrowing paragraph; the closed item about `list[T]` annotation breaking `_resolve_model_from_return_type` moves to Slice 0's verification scope.)

- **Slice 0 outcome — does the factory-function shape survive contact with `@strawberry.type`?** (Promoted from rev2 Risks item 3 + rev3 H1.) Preferred answer: yes — `DjangoListField(...)` returns the result of `strawberry.field(resolver=..., ...)`, and Strawberry's class-attribute machinery picks up that return value via `@strawberry.type`'s decorator-time class-body walk (it iterates `cls.__dict__` and converts annotated attributes / `StrawberryField` instances into the type's field list), the same way `field = strawberry.field(...)` is discovered today (rev6 M1 — rev5's "via `__set_name__`" claim was mechanically incorrect; `__set_name__` is the descriptor-protocol hook and is not what Strawberry uses for field discovery). Slice 0's pre-implementation spike verifies this end-to-end before Slice 1 touches `list_field.py` for real. Fallback: if the factory return value is NOT picked up cleanly, the alternative is to directly construct a `StrawberryField` with explicit `python_name` / `type_annotation`; that alternative is promoted into Decision 1 and Slice 1 reauthored. **This is the only risk whose outcome is genuinely unknown until implementation contact** — the rev3 H1 fix added Slice 0 specifically to discharge it.
- **The `get_queryset`-on-consumer-resolver-returns contract** (rev2 H1, pinned). Preferred answer: graphene-django parity — apply `target_type.get_queryset(qs, info)` to any `Manager`/`QuerySet` returned by the consumer's resolver; Python `list` returns pass through unchanged. Validated by `test_djangolistfield_consumer_resolver_queryset_return_gets_get_queryset_applied` and `test_djangolistfield_consumer_resolver_python_list_return_passes_through`. Fallback: if real consumers report the queryset-side application is a foot-gun (e.g., they want a fully consumer-shaped queryset including filter behavior the visibility hook would re-apply), a `apply_get_queryset=False` toggle could be added in a follow-up; the default stays "apply" because dropping it silently weakens the visibility-hook contract.
- **Async helper relocation** (rev2 Decision 3 Option B). Preferred answer for `0.0.7`: keep `_apply_get_queryset_*` in `types/relay.py` and import from there. Fallback: if the cross-file import turns brittle (or the connection card needs the same helpers next), relocate to `utils/get_queryset.py`; blast radius is small (one import update in `types/relay.py`).
- **Last-card-to-ship version bump policy** (rev3 M1). Preferred answer: the last of the five `0.0.7` WIP cards to merge owns the bump. Fallback: if real merge sequencing is unclear, a separate `KANBAN.md` edit (out of scope here per the spec boundary) adds an explicit `TODO-ALPHA-XXX-0.0.7 — 0.0.7 release cut` card; this spec doesn't author that edit.

## Out of scope (explicitly tracked elsewhere)

- `DjangoConnectionField` and Relay-shaped pagination: `DONE-030-0.0.9` in [`KANBAN.md`][kanban].
- [`DjangoNodeField`][glossary-djangonodefield] (root-level Relay node lookup): `DONE-030-0.0.9` (same card as connection field per current KANBAN scoping).
- Filter / order / search / aggregate input arguments on the field: `DONE-027-0.0.8` / `DONE-028-0.0.8` / `TODO-BETA-047-0.1.2` / `TODO-BETA-049-0.1.3`.
- Cascade permissions and field-level permissions: `DONE-034-0.0.10`.
- [Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning]: `DONE-033-0.0.9` (note: same-named entry under the connection card).
- Multi-database / sharding-aware queryset routing: cooperation contract `DONE-023-0.0.7`; first-class sharding-aware planning post-`1.0.0` in [`BACKLOG.md`][backlog].
- Auto-upgrade of reverse-FK / M2M relation fields to `DjangoListField`-based plumbing: deferred indefinitely; see [Decision 7](#decision-7--scope-boundary-vs-relation-list-fields).
- Pagination / limits on `DjangoListField`: not on the roadmap; pagination is the connection field's responsibility.

## Definition of done

The card is complete when all of the following are true:

1. `django_strawberry_framework/list_field.py` exists and defines `DjangoListField` as a factory function per [Decision 1](#decision-1--module-location-mechanism--public-export) and [Decision 2](#decision-2--default-resolver-shape) — returns the value of `strawberry.field(resolver=..., description=..., ...)`; closure-captures `target_type`; the resolver signature is the Strawberry-native `(root: Any, info: Info)` shape (rev4 H1 — `Any` from `typing`, `Info` from `strawberry.types`; `**kwargs` is NOT used because Strawberry treats every parameter as a GraphQL argument). Sync and `async def` consumer resolvers are both supported, with the `inspect.iscoroutinefunction`-driven wrapper choice and the runtime `inspect.iscoroutine` fallback per rev4 H2.
2. `django_strawberry_framework/__init__.py` re-exports `DjangoListField` and includes it in `__all__` in alphabetical position.
3. `tests/base/test_init.py`'s `__all__` assertion includes `"DjangoListField"`.
4. `tests/test_list_field.py` exists and contains the 18 tests listed in the [Test plan](#test-plan) (4 validation + 14 behavior; rev4 H2 added the two async-consumer-resolver tests; rev5 M3 added the dual-schema-execution test).
5. `examples/fakeshop/apps/library/schema.py` **adds** a new root field `all_library_branches_via_list_field: list[BranchType] = DjangoListField(BranchType)` to the `Query` class per [Decision 9](#decision-9--example-app-migration-posture); the eight existing `all_library_*` resolvers are unchanged (rev2 M1).
6. `examples/fakeshop/test_query/test_library_api.py` adds a test that asserts the new `DjangoListField`-served field's `/graphql/` response and optimizer plan via the existing `assertNumQueries` / SQL-sniffer pattern. The HTTP test does NOT assert `get_queryset` application — that coverage lives in package-internal `tests/test_list_field.py` with isolated fixtures (rev2 M2).
7. Constructor-time validation rejects non-class, non-`DjangoType`, non-registered, and non-callable-resolver arguments with `ConfigurationError`s matching the message contract in [Decision 5](#decision-5--validation--error-shapes). (Rev2 H2: no `nullable_list=` argument; no `nullable_list` validation.)
8. The default resolver returns a `QuerySet` (not a Python `list`) so the existing root-gated `DjangoOptimizerExtension` plan applies unchanged at the root.
9. The sync path rejects a coroutine return from `cls.get_queryset` with the same `ConfigurationError` shape that `types/relay.py:_apply_get_queryset_sync` raises.
10. The async path awaits the `get_queryset` coroutine and applies the optimizer through the same root-gated hook.
11. A consumer-supplied `resolver=` runs in place of the default body. When the consumer return value is a `Manager` or `QuerySet`, `target_type.get_queryset(qs, info)` is applied (rev2 H1, graphene-django parity); a Python-`list` return passes through unchanged. Both paths are pinned by tests.
12. Outer-list nullability is driven by the consumer's class-attribute annotation (rev2 H2): `list[T]` → `[T!]!`, `list[T] | None` → `[T!]`. Both renderings are pinned by schema-introspection tests.
13. The contract is **root list fields only** in `0.0.7` (rev2 M3). Nested non-root usage is functional but not root-optimized. The CHANGELOG and GLOSSARY entries reflect this scope.
14. `Meta.primary` interaction is covered: a model with multiple `DjangoType`s, one declared primary, is queryable through `DjangoListField(PrimaryType)` AND `DjangoListField(SecondaryType)` independently per [Decision 6](#decision-6--metaprimary-interaction).
15. Package coverage stays at 100% (`pyproject.toml [tool.coverage.report] fail_under = 100`).
16. `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `README.md`, `GOAL.md`, `TODAY.md`, `KANBAN.md`, and `CHANGELOG.md` reflect the shipped state per the [Doc updates](#doc-updates) section. The `docs/TREE.md` target-layout `connection.py` line has `DjangoListField` removed from its bullet (rev2 L1).
17. `KANBAN.md` moves `DONE-020-0.0.7` to Done with the next `DONE-NNN-0.0.7` id and a past-tense body summarizing the shipped scope in **add-only language** (rev4 H3 — the body must say "added `all_library_branches_via_list_field`" not "replaced one of the `all_library_*` resolvers"; the original card text's "replacing" wording is an intentional departure documented in [Decision 9](#decision-9--example-app-migration-posture)'s "Card-text departure" paragraph).
18. The version bump is NOT in this card per [Decision 10](#decision-10--joint-0_0_7-cut); **the last `0.0.7` card to ship** owns `pyproject.toml`, `__version__`, and `tests/base/test_init.py`'s version assertion (rev3 M1 — there is no separate release-cut card; the policy names the owner, not a card).
19. Exactly one new public export (`DjangoListField`) is added; no other public names change.
20. `uv run ruff format .` passes; `uv run ruff check --fix .` passes; `uv run pytest` passes with 100% package coverage.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[backlog]: ../../BACKLOG.md
[changelog]: ../../CHANGELOG.md
[contributing]: ../../CONTRIBUTING.md
[goal]: ../../GOAL.md
[kanban]: ../../KANBAN.md
[readme]: ../../README.md
[today]: ../../TODAY.md
[today-optional-fakeshop-visibility-filtering-today]: ../../TODAY.md#optional-fakeshop-visibility-filtering-today

<!-- docs/ -->
[docs-readme]: ../README.md
[feedback]: ../feedback.md
[glossary-apply-cascade-permissions]: ../GLOSSARY.md#apply_cascade_permissions
[glossary-bigint-scalar]: ../GLOSSARY.md#bigint-scalar
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-connection-aware-optimizer-planning]: ../GLOSSARY.md#connection-aware-optimizer-planning
[glossary-djangoconnection]: ../GLOSSARY.md#djangoconnection
[glossary-djangoconnectionfield]: ../GLOSSARY.md#djangoconnectionfield
[glossary-djangolistfield]: ../GLOSSARY.md#djangolistfield
[glossary-djangonodefield]: ../GLOSSARY.md#djangonodefield
[glossary-djangooptimizerextension]: ../GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-finalize-django-types]: ../GLOSSARY.md#finalize_django_types
[glossary-fk-id-elision]: ../GLOSSARY.md#fk-id-elision
[glossary-get-queryset-visibility-hook]: ../GLOSSARY.md#get_queryset-visibility-hook
[glossary-metafields]: ../GLOSSARY.md#metafields
[glossary-metamodel]: ../GLOSSARY.md#metamodel
[glossary-metaprimary]: ../GLOSSARY.md#metaprimary
[glossary-multi-database-cooperation]: ../GLOSSARY.md#multi-database-cooperation
[glossary-only-projection]: ../GLOSSARY.md#only-projection
[glossary-optimizerhint]: ../GLOSSARY.md#optimizerhint
[glossary-plan-cache]: ../GLOSSARY.md#plan-cache
[glossary-public-exports]: ../GLOSSARY.md#public-exports
[glossary-queryset-diffing]: ../GLOSSARY.md#queryset-diffing
[glossary-relation-handling]: ../GLOSSARY.md#relation-handling
[glossary-relay-node-integration]: ../GLOSSARY.md#relay-node-integration
[glossary-strictness-mode]: ../GLOSSARY.md#strictness-mode
[glossary]: ../GLOSSARY.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-011]: spec-015-relay_interfaces-0_0_5.md
[spec-014]: spec-018-meta_primary-0_0_6.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
