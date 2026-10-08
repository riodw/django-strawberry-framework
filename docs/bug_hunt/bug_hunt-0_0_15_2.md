# Bug hunt 0.0.15 (2): to-do list

Every finding from the 0.0.15 hunt in the t3 worktree (never merged), plus bugs found while fixing them.
Each one is verified on main, fixed at the root, checked by a second agent, landed, then deleted from t3.

Progress: 32 done, 48 to do.

## Done

- [x] 1. Multi-column `ForeignObject` links (`fe6a6df0`, `337b3317`)
- [x] 2. Negative offset cursor, and the page-cap bypass behind it (`a57bd826`)
- [x] 3. M2M composite-index advisory names the wrong column (`269b80c0`)
- [x] 4. Filter lookups binding to the wrong field on overlapping names (`754ed263`, `9f7ea5dd`)
- [x] 5. Serializer list nulls and blank choice (`a5dc6ea3`)
- [x] 6. `reject_combined` on list-relation children: replaced by a better design (`5c5e32c5`)
- [x] 7. Directive and default-value cost charging: already fixed on main
- [x] 8. Fragment-spread cost charging: already fixed on main
- [x] 9. Cursor presence checked by truthiness: already fixed on main
- [x] 10. Mutation window under interruption: already fixed on main
- [x] 11. Mutation errors name the Django field instead of the input field (`7517eab2`)
- [x] 13. Consumer `Prefetch` hint over a type that hides rows: already fixed on main (`5d4cdb3b`, `00563dd0`)
- [x] 30. Flat `RelatedFilter` leaf returned hidden rows (`90fc7118`)
- [x] 31. Relations without a `RelatedFilter` returned hidden rows (`37dcbf70`, `eddfeab1`, `c7d0ca02`)
- [x] 32. Ordering by a hidden related row (`70118090`)
- [x] 33. spec-058 builders and `graph.apply` re-entrancy (`d58420d8`, `adacb26c`)
- [x] 34. `RelatedFilter` pointing at a model its relation does not reach (`9131486f`)
- [x] 35. Serializer choice field accepting values the column's enum can't show (`a6ace786`)
- [x] 36. `MultipleChoiceField` over a single-value choice column (`f218d7ee`)
- [x] 37. Combined hook queryset rejecting `F()` / `OrderBy` ordering (`22900492`)
- [x] 38. `Choices.__empty__` produced a `_None` enum member (`3ed5ee48`)
- [x] 39. Offset page-cap bypass (`a57bd826`)
- [x] 40. Five leads closed as not bugs (Django's own behavior in each case)
- [x] 41. `test_relations` tests failing when run alone (`cab934a0`, other session)
- [x] 58. HIGH. Fragment spreads expanded but never charged: an 857-byte request cost 1.9 s of CPU, doubling per level (`3cc1b249`)
- [x] 59. Two `RelatedFilter` / `RelatedOrder` declarations on one relation made flat leaves and order terms read the wrong one;
  a set now declares each relation once, and refuses a longer declaration that takes over a branch's paths (`ddf8ef8b`)
- [x] 60. One `OrderSet` on two types of the same model kept the first type's visibility; a second owner is now refused when
  either hides rows, as on the filter side, and a subclass binds its own owner (`8ab6c921`)
- [x] 72. A set bound to a type over a proxy model read the concrete model's primary type on a path re-entering its table; re-entry
  now matches by table, and a set shared by an MTI parent and child type is refused (`9d5e2a04`)
- [x] 62. A declared flat `ChoiceField` over a grouped-choices column was refused since item 35; the write-side check now reads the
  column's flattened values, and its refusal no longer claims a GraphQL enum exists (`bf112a0c`)
- [x] 65. `iExact: BLANK` and every other single-value lookup on a choice column dropped the predicate; every enum member now
  reaches the filter as a typed value, so `""` is never skipped and a `"null"` member is never `IS NULL` (`309d4f04`)
- [x] 48. `BLANK_CHOICE` marker broke under copy / pickle; replaced by the `EnumMemberValue` value object (`309d4f04`)
- [x] 52. Connection resolvers sent row-hydration and consumer-source exception text to the client; pagination validators now
  raise `PaginationArgumentError` themselves and nothing rewraps a foreign exception (`72065173`)

## To do: t3 hunt findings

- [ ] 12. Nested forward-FK / OneToOne resolvers never check the request deadline
- [ ] 14. README says `in: []` matches nothing; it matches every row on integer, text and choice columns (flat), and on a nested
  `shelves.condition in: []` only parents with a child. Check which is right

## To do: t3 robustness rows

40 low-priority rows, mostly guards against classes with broken `__name__` / `__eq__` / metaclasses. Expected outcome: most are
not real bugs and just get deleted from t3. One checkbox per area:

- [ ] 15. `filters/inputs.py` (1 row)
- [ ] 16. `forms/` (2 rows)
- [ ] 17. `mutations/` and `auth/mutations.py` (4 rows)
- [ ] 18. `optimizer/` (2 rows)
- [ ] 19. `rest_framework/` (2 rows)
- [ ] 20. Filter and order sets (8 rows)
- [ ] 21. `routers.py`, `list_field.py` (2 rows)
- [ ] 22. `types/` (7 rows)
- [ ] 23. `utils/` (9 rows)
- [ ] 24. Trailing-comma lint in two test files (2 rows)
- [ ] 25. Stale test-fixture row in `tests/utils/test_querysets.py`: likely already covered by item 41
- [ ] 27. Unfiled leads from the same family (triage with the rows above)

## To do: found along the way

- [ ] 42. `auto_camel_case=False` still produces camelCase mutation inputs (unverified)
- [ ] 43. `ListField(child=ChoiceField(...))` shows up as `String`, not an enum
- [ ] 44. `IntegerField(choices, blank=True, null=False)` in a ModelForm mutation: optional startup check
- [ ] 45. Postgres: plain `ChoiceField` over an `ArrayField` builds, then the save fails
- [ ] 46. Postgres: `ListField(child=ChoiceField)` over an `ArrayField` is refused
- [ ] 47. Postgres: `serializer_choice_field=MultipleChoiceField` over an `ArrayField` is unusable
- [ ] 49. `serializer_field_description` re-raises `KeyboardInterrupt`
- [ ] 50. SKIP hint drops relation columns from `.only()`, so every row is fetched again (unverified)
- [ ] 51. `OrderSet` `"__all__"` leaves out `ForeignObject` fields (unverified)
- [ ] 56. Two writable serializer fields can write the same FK column (`category` and `source="category_id"`)
- [ ] 74. A consumer `select_related` on a forward FK the query never selects, combined with the optimizer's `.only()`, raises
  Django's "cannot be both deferred and traversed" (`Entry.objects.select_related("property")` with `{ entries { value item { name } } }`)
- [ ] 80. `_guard_source_not_pre_sliced` and three `_finalize_queryset` catches turn a consumer QuerySet or ordering fault into a
  deliberate `GraphQLError` naming the exception class: no `correlationId`, class name on the wire (robustness; no text leaks)
- [ ] 81. `decode_offset_cursor` checks `relay.Edge.CURSOR_PREFIX`, not the connection's `edge_class.CURSOR_PREFIX`: a custom Edge
  prefix turns a foreign `arrayconnection:` cursor into a masked error instead of the cursor message (robustness, fails closed)

## To do: holes found re-checking the fixes

- [ ] 61. Three `FilterSet`s in a `RelatedFilter` cycle: the flat filters exposed depend on type declaration order
- [ ] 63. `after` cursor at `sys.maxsize - 1 - page` with `first: 0` / `last: 0` raises Strawberry's assert instead of an empty page
- [ ] 64. Two cursor-decoder guards no test pins (`isascii`, the nested-window decode)
- [ ] 66. Index advisory on a multi-table-inheritance child names an order column that lives on the parent table
- [ ] 67. Nested serializer: a Django error raised in `create()` for a child is keyed to a renamed root input
- [ ] 70. Argument-less directives are re-walked on every fragment expansion (about 80 ms at the token bound; bounded, robustness)

## Waiting on you

- [ ] 26. A mutation whose `__name__` raises publishes a `<MetaclassName>Payload` type instead of failing. Fail, or keep?
- [ ] 53. Docs (parked): README async section, a hand-written `@strawberry.field` returning a QuerySet runs synchronously
- [ ] 54. Docs (parked): glossary, a sliced combinator branch on SQLite raises Django's own `DatabaseError`
- [ ] 57. CHANGELOG entry for item 11: model, ModelForm, plain-form and register errors now use the input name (`categoryId`, not `category`)
- [ ] 68. A model's default manager hides rows from declared filter hops but not from undeclared filter hops or ordering. Make them
  agree, or keep?
- [ ] 69. CHANGELOG entry for item 1: `Meta.exclude=["parent"]` on a mutation over a `ForeignObject` model now raises
- [ ] 71. CHANGELOG entry for item 59: two `RelatedFilter`s or `RelatedOrder`s naming one relation now raise at class creation, and a
  longer one (`shelf__branch` beside `shelf`) raises at expansion when the shorter branch's target set reaches `branch`
- [ ] 75. CHANGELOG entry for item 72: a `FilterSet` or `OrderSet` shared by an MTI parent and child type now raises at finalize, and
  a concrete type's path through an FK declared to a proxy (`BranchNote.branch`) reads the bound type, not the proxy's type
- [ ] 76. CHANGELOG entry for item 62: a `SerializerMutation` whose serializer declares a flat `ChoiceField` over a grouped-choices
  column binds again (checked against the column's flattened values); a refused value now reads "which does not list it", and a
  serializer field taking a grouped column's read enum is refused with a remedy to declare a flat `ChoiceField`
- [ ] 77. The read enum refuses a grouped-choices column, though group labels are presentation like choice labels. Flatten it on
  the read side too (retires the `str`-override carve-out and the write-side grouped refusal), or keep?
- [ ] 78. CHANGELOG entry for item 65: every lookup on a choice column treats each enum member as a value (`iExact: BLANK`
  matches blank rows only, a `"null"` member matches `"null"`); raw form data and declared `ChoiceFilter`s are unchanged
- [ ] 79. CHANGELOG entry for item 52: connection fields no longer send consumer-source or row-hydration exception text to the
  client; pagination rejections keep their messages and are the new public `PaginationArgumentError`
- [ ] 73. A set subclass used only as a `RelatedFilter` / `RelatedOrder` target, never wired to a type, inherits its base's owner and
  that owner's visibility. Keep, or fall back to the target model's registered type?

## Hunt not finished in t3

- [ ] 28. Deep dive 3 (authorization on deferred paths) is blocked; its findings are items 12 and 13
- [ ] 29. The hunt's final test gate was never run

## Addendum: handoff 2026-10-08 (item 12 and the request-rejection precedence)

Written at the close of one chat for whoever picks this up next. Nothing here is landed on main.

### Where the work is

Scratch under `/private/tmp` is wiped by a reboot, so everything is copied to `~/dst-handoff/2026-10-08/`:

- `0001-fix-resolvers-nested-forward-FK-OneToOne-and-reverse.patch`: commit `7595d578`, the item 12 fix (also kept in the main repo as
  `refs/scratch/fix12`). Based on `85ba203e`; main has moved since (at least `cdc760b5`), so rebase and re-carve
  `examples/fakeshop/db.sqlite3` (its only DB change is glossary rows: the "Execution resource policy" body plus new terms 587
  `check_deadline` and 588 `bounded_rows`; `glossary_item12.py` replays them).
- `admission-wip.patch` and `admission-wip-status.txt`: the UNCOMMITTED, UNFINISHED precedence implementation, `git diff HEAD` on top of
  `7595d578` (new files included). It was snapshotted while an Opus Medium implementer was still mid-task: code, both new test files
  and spec-030/032/047 edits existed; glossary, KANBAN, AGENTS, START, README and CHANGELOG had not been started, and no test had
  run. Treat it as a draft to review, not a finished change.
- `admission-design.md`: the approved design (read this first).
- `item12-gather-report.md`: item 12 facts and probes.
- `hotpath12_bench.py`, `before_run1.json`/`.log`: hot-path harness and the BEFORE numbers.
- `probe12.py`, `probeMCF_*.py`: the probes behind the findings below.

The live clone was
`/private/tmp/claude-501/-Users-riordenweber-projects-django-strawberry-framework/df9d661e-0eaa-4a60-9fbe-5e28dd0c0d33/scratchpad/fix12`.
The implementer was stopped and its last state committed as `970d054a` (`refs/scratch/admission-wip` in the main repo; also `0001-wip-admission-*.patch` in the handoff dir). It stopped while running the generators, so the glossary, KANBAN and constants may be half-updated. Start from that commit, not `admission-wip.patch`.

### Item 12: done in the clone, not landed

- Verdict: a defect under AGENTS rule 37. The contract row is the `ResourcePolicy` `execution_deadline_seconds` docstring plus
  spec-047 Decision 9, which says every seam about to reach the database checks the deadline first. The shape is `DjangoSchema` with
  a deadline and no optimizer (or an unplanned relation). The wire input is `{ allLibraryBooks { title shelf { code } } }` on the
  `/rp-deadline/` test mount: 5 queries after the deadline, no error.
- Fix (`7595d578`): `check_deadline(info)` is the first statement of `forward_resolver` and `reverse_one_to_one_resolver` in
  `types/resolvers.py::_make_relation_resolver`, checked on every call. There are no checks inside the async closures. The wire
  message now reads "before this field reached the database".
- Docs: the "collection resolvers" wording in the glossary and the `check_deadline` docstring is retired. Two audited exclusions
  are added: the file resolver, and hand-written resolvers, which are trusted code (GOAL.md "Trust boundary") and opt in via
  `check_deadline` / `bounded_rows`.
- Tests are written but NOT run, in `test_resource_policy_api.py`:
  - forward FK, forward O2O, reverse O2O and many-side rows;
  - an unarmed control;
  - an optimizer-mounted pin, which distinguishes a check at the resolver head from one on the lazy path only;
  - async O2O rows.
- Hot path: `check_deadline` costs about 300 ns per call, +24% to +46% per resolver call and about +1% end to end at 100 rows.
  The AFTER number has not been taken:
  `<tree>/.venv/bin/python ~/dst-handoff/2026-10-08/hotpath12_bench.py --tree <tree> --json after_run1.json`.
- Unmeasured idea: an early return when neither the budget nor the context mirror holds a deadline. It would skip 4 of the 8 calls.
- After landing: tick 12, purge D-3A-1 from t3 (outside auto mode, backup first), and tick 28 if 13 and 12 were its only findings.

### The request-rejection precedence

**Why the question kept coming back.** "Which error wins: `first`/`last` or the deadline?" came up 14 times since 2026-08. The
order of per-field checks was never chosen. It falls out of Strawberry's `ConnectionExtension.resolve` running the package resolver
(visibility, FilterSet, OrderSet) before `resolve_connection` (guard, deadline, bounds). Every seam is hand-ordered differently, and
no test pairs two rejections.

**Approved by Rio (all 7 decisions):**

- **One order.** P0 is document admission, P1 field-argument errors, P2 the deadline, P3 the consumer pipeline, P4 slice and
  database.
- **One seam.** A new `admission.py` (`admit_connection_page`, `admit_list_page`, `admit_node_refetch`). Connections enter it through
  a package `DjangoConnectionExtension(ConnectionExtension)` built with `strawberry.field(extensions=...)`, which replaces both
  `relay.connection(` calls (`connection.py`, `types/finalizer.py`).
- **Node fields** decode the id before the deadline.
- **`first` + `last`** raises `PaginationArgumentError`, with the same message as today.
- **Doc home** is spec-047 Decision 14 plus a glossary entry "Request rejection precedence", plus one AGENTS.md line.
- **Landing order:** item 12 lands first.
- **CHANGELOG:** entries for both changes. The text is in `admission-design.md` decision 7.

**A defect this closes.** On a connection, a consumer `ModelChoiceFilter` validates (and queries) before the deadline check. The
shipped `allLibraryGenresConnection(filter: {books: {shelf: {homeBranch: {exact: $pk}}}})` ran its branch lookup after an expired
deadline. With an invalid pk it answers `FILTER_INVALID` instead of the deadline rejection. Give it its own item number when this
lands.

**Wire changes.** Only requests that are invalid in two ways change; the table is in `admission-design.md`.

**What the next agent does:**
1. Finish the implementation from the clone or `admission-wip.patch` against the design.
2. Write the live matrix test `examples/fakeshop/test_query/test_admission_api.py`.
3. Write `tests/test_admission.py`.
4. Prove failability with two mutations: swapping P1 and P2, and moving admission after `next_`.

**Watch when finishing:**
- Reproduce everything `relay.connection()` sets up beyond the extension.
- Do not leak the admitted page across parents or concurrent async fields.
- `bounded_rows` / `bounded_rows_async` are public API and keep their deadline check.
- Keyset: the cursor's shape and signature belong to P1; the column-fingerprint match stays at the seek.
- The walker's plan-time catch in `optimizer/nested_planner.py`.

### Rules that bit this chat

- AGENTS rules 15/16: no pytest unless Rio asks, and when asked, targeted files only.
  - Before every run, `pgrep -fl '[p]ytest|[b]asedpyright'` must print nothing (any project; a medtrics pytest was running) and at
    least 35% memory must be free.
  - Three subagents ran a light probe without gating on that check. Briefs must tell them to gate on it, not just print it.
- Work in a private `git clone --no-local` with its own `uv sync`. Never write the main checkout's tracked
  `examples/fakeshop/db.sqlite3`.
- Landing through a concurrently dirty main:
  1. Rebase in scratch and re-carve the DB rows by UPDATE/INSERT.
  2. `merge --ff-only` only when no dirty file overlaps; otherwise commit through a private index.
  3. Never `git commit --only`.
- No `Co-Authored-By` footer (AGENTS rule 33). No branches. CHANGELOG only when Rio says so (this time Rio did).
- Always run a verifier agent over an implementer's commit before landing.

### Other open threads

- Items 78 and 79 (CHANGELOG for 65 and 52) still need Rio. Focused pytest runs for items 65 and 52 were never run since landing.
- t3 worktree `~/.t3/worktrees/django-strawberry-framework/t3code-1cc21548` still sits at `67027892`.
  - A fast-forward to current main is large and conflicts in 5 files; Rio has not authorized it.
  - Backup: `~/t3code-1cc21548-pre-ff.tgz`.
- Main-repo refs `refs/scratch/fix65`, `fix52` and `land` are superseded and can be deleted. Keep `refs/scratch/fix12` until item 12
  lands.
- Robustness rows noted, not filed:
  - The `get_queryset` hooks and `check_*_permission` hooks run before the deadline check (trusted code).
  - Strawberry's native `relay.node()` has no deadline check (Strawberry's surface, not this package's).


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
