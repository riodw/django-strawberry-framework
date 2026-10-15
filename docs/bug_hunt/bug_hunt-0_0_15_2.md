# Bug hunt 0.0.15 (2): to-do list

Every finding from the 0.0.15 hunt in the t3 worktree (never merged), plus bugs found while fixing them.
Each one is verified on main, fixed at the root, checked by a second agent, landed, then deleted from t3.

Progress: 72 done, 155 to do.

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
  reaches the filter as a typed value, so `""` is never skipped and a `"null"` member is never `IS NULL` (`1f4993eb`)
- [x] 48. `BLANK_CHOICE` marker broke under copy / pickle; replaced by the `EnumMemberValue` value object (`1f4993eb`)
- [x] 52. Connection resolvers sent row-hydration and consumer-source exception text to the client; pagination validators now
  raise `PaginationArgumentError` themselves and nothing rewraps a foreign exception (`41969bc3`)
- [x] 12. Nested forward-FK / OneToOne resolvers never checked the request deadline; every package seam that reaches the database
  now checks it first, which also covers the session-auth `login` / `logout` / `me` fields and the `resolve_node` /
  `resolve_nodes` defaults Strawberry's `relay.node()` reaches (`8d4f66bd`)
- [x] 14. `in: []` matched every row on every generated `in` except GlobalID and relation keys (35 families: integer, text,
  choice, date/time/UUID/decimal, FK-id paths, nested branches, nested connection arguments), and a logical arm that constrained
  nothing was TRUE (`not: {}` no rows, `or: [{}, real]` every row). Now `[]` is the empty set as in Django, strawberry-django and
  graphene-django, an inert arm is `Q()`, a raw `?x__in=` keeps django-filter's no-constraint rule (`e09b5ef1`)
- [x] 15. `filters/inputs.py` robustness row (not a defect: the wire cannot deliver the shape): a hand-built range value the
  range filter cannot read (a list, a scalar, an object, a mapping with a key other than `start` / `end`, so also a misspelled
  lookup under a range head) dropped the constraint and `apply_sync` returned every row, against the GLOSSARY / spec-027
  promise that an unknown lookup raises; it now raises `ConfigurationError`, as the list and dict arms already did
  (`a54ad7c8`, in the body of the FBT ratchet commit)
- [x] 16. `forms/` robustness rows (not defects: application Python, no wire input). A `get_form_fields` hook value (or a
  `base_fields` value) whose `__class__` raises escaped `_form_field_basis` raw at declaration and finalize, against the
  `get_form_fields` / `_form_basis_content_identity` docstrings; it is now an invalid field in the typed error (`32b66897`).
  The eight raw `__name__` reads in `forms/sets.py` need no code: no contract row, and the label question is item 26's
- [x] 17. `mutations/` and `auth/mutations.py` robustness rows (not defects: application Python, no wire input). A protected
  `USERNAME_FIELD` / `REQUIRED_FIELDS` entry that is a `str` subclass (an enum member, or one whose repr or ordering raises)
  escaped `derive_register_fields` raw or rendered as an enum repr, against the GLOSSARY / spec-040 refusal naming the
  field; `DjangoMutationField` checked ledger membership by equality, so a drained class equal to its redeclaration built a
  schema whose requests failed. Both fixed (`b4d6e06a`). The raw `__name__` labels, the protocol probe and the Payload
  name need no code: no contract row, and the name question is item 26's
- [x] 18. `optimizer/` robustness rows (not defects: application Python and settings values, no wire input). A
  `prefetch_obj` whose `__class__` raised escaped `_require_prefetch` raw; a strategy selection or `strictness=` value whose
  `__class__` raised or claimed `str` (and a lazy proxy of a name) escaped `resolve_strategy` / `_is_valid_strictness` raw on
  every route, the `NESTED_CONNECTION_STRATEGY` setting included, against their docstrings' typed-error promises. The
  Prefetch test is now a guarded `isinstance` (subclasses and proxies still pass); the str and class tests ask the real
  type (`utils/_narrowing.py::is_str`, `is_class`) (`f788edcf`). `unwindowable_child_queryset_reason` needs no code: no
  contract row, Django-private input
- [x] 19. `rest_framework/` robustness rows (not defects: consumer hook and serializer Python, no wire input). A field-map,
  `nested_fields` or hook-return value whose `__class__` raised, a non-string hook key whose `__repr__` raised, a hostile
  `write_alias` and a hostile `save()` return escaped raw against their docstring / GLOSSARY / spec-039 typed-error
  promises; the frozen hook view passed `__class__` spoofs and lazy proxies of immutables by reference against its
  fails-closed promise; and a kept serializer field named by a non-identifier or a keyword passed class creation, then raised
  an unnamed `SyntaxError` at finalize. Mapping and Field tests are now guarded `isinstance` (proxies still pass); the
  freeze, the alias and the saved result ask the real type; renders use the guarded repr; kept input names are checked at
  class creation, root and nested (`5cbe15de`). The raw `__name__` labels need no code (item 26's); `_error_node_children`'s
  `str(key)` needs none: no contract row, and DRF keeps detail keys as given
- [x] 28. Deep dive 3 (authorization on deferred paths): findings 12 and 13 done; `VenueBadgeType` and `VenueSponsorType` now
  hide marked rows, and live rows prove none leaks through the no-`related_name` reverse accessors (`16a8c179`)
- [x] 50. A SKIP hint (and a consumer-assigned relation, and the nested-connection SKIP arm) left the relation's key column out of
  `.only()`, so each row refetched it before the relation's own query (2N+1, async errors on a non-pk link); every traversed
  relation now keeps its link columns, as does a consumer `prefetch_related` (generic foreign keys included) (`548059b3`)
- [x] 74. A consumer `select_related` the selection never reads made the optimizer's `.only()` defer the column the JOIN traverses
  (masked "cannot be both deferred and traversed", even for `{ allLibraryPrefetchedBooks { title } }`); the `.only()` writers now load
  each joined row whole: root, planned children, scalar-only nested windows, both one-to-one directions, second hops (`13de7c4c`)
- [x] 83. A consumer `.only()` / `.defer()` met the plan's projection badly on both sides: the root dropped the plan's columns
  (every selected column outside the consumer's set lazy-loaded per row, async errors) and a planned child replaced its hook's
  `.only()`. Both now load the union under a `QUERY` operation; a hook's `prefetch_related` no longer collides with the
  planned `Prefetch`, and `{ allLibraryPatrons { name card { __typename } } }` no longer hits the masked FieldError shipped
  since 0.0.7 (`548059b3`)
- [x] 42. `auto_camel_case=False` keeps every generated input camelCase (82 mutation, 3,487 filter, 124 order fields) while
  Strawberry-owned names follow it; FieldError keys still match the published names. Not a defect under rule 37 (no shipped doc
  says inputs follow the converter): the maintainer's 2026-09-25 decision already homes it on `TODO-BETA-077-0.1.7`, no code
- [x] 43. A serializer `ListField(child=ChoiceField(...))` published `[String!]`; it now publishes the field's generated enum like a
  `MultipleChoiceField`. Fixed with it: `MultipleChoiceField(allow_blank=True)` refused its own `BLANK` (list members reached DRF
  unwrapped); `raw_choice_value` now unwraps a list element-wise (`a9dec21d`)
- [x] 44. A `DjangoModelFormMutation` over a non-text choice column with `blank=True, null=False` answered `null` (or an omitted
  field with no default) with a masked top-level error, since `form.save()` raised `ValueError` / `ValidationError`; it now returns
  the field-keyed `null` FieldError the model flavor gives. Django keeps the shape on purpose, so no startup check (`6c31c5e3`)
- [x] 49. `serializer_field_description` converts (does not re-raise) a `KeyboardInterrupt` from hostile field metadata into
  `ConfigurationError`, by design and pinned since `3470fb7f`. Not a defect under rule 37 (no contract row, application Python, no
  wire input), no code; the package-wide policy question is item 94
- [x] 95. A nested keyset connection whose target `get_queryset` (or manager) orders differently from `Meta.cursor_field`
  windowed by that order but sought and minted by the declared one, so a forward page 2 silently dropped rows; the window now
  derives its cursor vocabulary from the order it pages by through the resolver the root uses (`5197d03d`)
- [x] 51. An `OrderSet` leaf over a multi-column forward `ForeignObject` raised a masked `FieldError` on every `orderBy`, and
  `"__all__"` dropped every forward `ForeignObject` (a side effect of `7000d920`); a leaf now orders by one term per carrier
  column as Django's `order_by` does, `"__all__"` publishes it again, and a link naming no visible target sorts as missing
  instead of being dropped by an inner join (`0eb96efe`)
- [x] 99. A connection target whose `get_queryset` (or manager) returns a `.reverse()`d queryset compiled reversed SQL while
  the keyset seek, the minted cursors and the optimized nested window (keyset and offset) read the forward terms, so pages
  repeated and lost rows with no error; the order ladder now materializes the reverse of the forward total order as explicit
  terms first, keeping the page-1 `ORDER BY` byte-identical (`b005a7ee`)
- [x] 56. Two writable serializer fields aliasing one model field (`category` beside `source="category_id"`, a pk field
  beside `source="pk"`) passed every ownership guard, which compared spellings; the class-creation guard, the input walker
  and the runtime guard now key a source by the model field it resolves to, at every depth (`bcfe561e`)
- [x] 80. Four connection catches turned a consumer source or `Meta.ordering` fault into a deliberate `GraphQLError` naming the
  exception class (no `correlationId`, no log line); they are deleted, so the fault reaches the error policy as itself and is
  masked with a `correlationId`, as on the list field and the optimized nested path (`29c1f670`)
- [x] 81. A `DjangoConnection` subclass whose edge class declares its own `CURSOR_PREFIX` (mounted with `relay.connection`)
  refused its own offset cursors past page 1 and served or masked a foreign `arrayconnection:` cursor; every offset decode
  now reads the connection's own edge-class prefix, so it pages and a foreign cursor gets the cursor error (`23a9229c`)
- [x] 87. A ModelForm field over a choice column published the column's read enum whatever the form admitted, so a declared
  narrower `ChoiceField` advertised members the form refused; it now publishes exactly the column values the form's own
  `valid_value` admits (a generated `<InputTypeName><FieldName>Enum` when fewer), and a field admitting no non-empty column
  value, or a `MultipleChoiceField` over a single-value choice column, is refused at schema build (`889e7c7a`)
- [x] 103. A writable relation field bound to its `attname` (`cat = PrimaryKeyRelatedField(source="category_id")`, or a
  `category_id` field with the source defaulted) published a create input every request failed with a masked TypeError; it
  is refused at schema build with the remedy `source="category"`, root, nested and injected (`f8ff159c`)
- [x] 116. Under `globalid_strategy="type"` a `NameConverter` that renames object types broke GlobalID round trips: ids
  carried the converted name while `node`, `nodes`, mutations and GlobalID filters decoded by the plain name (refused, or
  another type's rows read and written on a collision); they now decode by the executing schema's published name
  (`e05b2436`)
- [x] 119. Two `prove_failability.py` runs on one tree could both own it: `RUN.lock` was created empty and its pid
  written after, so a second run read no pid, unlinked the lock as stale and claimed it (a silent 0-row proof, or a
  mutation left in the tree with a passing restore proof), and a run without `--scratch-root` took no lock at all; a
  kernel `flock` on the repository root is now held for the whole run (`ce338eec`)
- [x] 106. A `to_field` ForeignKey written through a declared `PrimaryKeyRelatedField` failed every non-null create and
  update (the attestation compared the stored `to_field` value with the pk) and, with an integer `to_field`, passed a
  wrong-row write; the snapshot captures the key the relation stores, the walk refuses it re-pointed in place and the
  attestation compares the column with it (`4ce779e1`)
- [x] 88. A lone surrogate inside a list element or a JSON key or value skipped the decode text preflight (top-level `str`
  only) and reached the backend raw as a masked top-level `UnicodeEncodeError` (fakeshop `setCardFiles` paths; on Postgres an
  `ArrayField` of text or an `HStoreField` in every write flavor; a serializer `ListField(child=CharField())` element was
  already refused by DRF); the preflight now walks every list element and dict key and value, keyed to the leaf's dotted path
  (`ea0eea70`)
- [x] 130. A model `DjangoMutation` (and register) wrote the related pk into a `to_field` relation's column: a wrong row
  linked silently (including one the visibility scope hides) or a payload FieldError, for a FK, a OneToOne and an M2M whose
  through model's target-side foreign key has a `to_field`; the one visibility query now also reads the key the relation
  stores and that key is written (`6a8713d6`)
- [x] 89. The serializer refusal of a field taking a grouped-choices column's read enum offered "declare a flat
  ChoiceField" over an `ArrayField` whose `base_field` is grouped too, where a `ChoiceField` writes one value into the list
  column; over such an array it now names a declared `MultipleChoiceField` or `ListField(child=ChoiceField)`, each element
  checked against the `base_field`'s flattened values (`6f1a6cd4`)
- [x] 139. Two `workspace.py` runs of one address started during the copy's first sync both synced it: the second decided
  its sync before waiting for the copy's lock and resynced over the first run's edits (silently, its header said "copy is
  fresh"); a killed `--fresh` sync left the copy marked ready and half-mirrored, and a run whose copy was released while it
  waited ran in another address's copy; the sync is now decided under the copy's lock, every sync marks the copy syncing
  first, and a run whose copy no longer holds its address refuses with exit 125 (`4ed767bb`)
- [x] 140. `workspace.py release` and `gc` probed a copy's lock, dropped it and then unbound or deleted: `gc` without
  `--force` deleted active work (about 98% of runs started with it), deleted the lock files a waiter held so two runs owned
  one copy, and a probe or a racing run recreated an unmarked flow folder; every command now holds a shared lock on the
  flow folder, `gc` holds it exclusive through the removal (marker last), `release` keeps each copy's lock through its
  state write, `lock_is_busy` and `gc --force` are gone (`4ed767bb`)
- [x] 90. Nested list-of-choice serializer shapes (`ListField(child=MultipleChoiceField)`,
  `ListField(child=ListField(child=ChoiceField))`) publish `[[String!]!]` by spec-039's one-level peel
  (`serializer_choice_source`). Not a defect under rule 37 (no contract row: spec-039 states `list[list[str]]`; no wire input
  writes a wrong value): they are reachable only as serializer-only fields, DRF checks every leaf with a field-keyed error
  (`f.0.0`), declared over any column they are refused at build, and neither graphene-django nor strawberry-django types nested
  choice lists as enums; no code. Found probing it: items 151-154
- [x] 128. `testing/relay.py::global_id_for` annotated `schema` with a `TYPE_CHECKING`-only `Schema` in a module without
  `from __future__ import annotations`, so importing the public module raised `NameError` on Python 3.10-3.13 (the CI floor
  cell failed collection; nothing static caught it); the annotation is quoted (`7413c7b5`) and ruff `TC004` (quoting fix)
  now fails an eager annotation naming a `TYPE_CHECKING`-only import (`1cee08c4`); unreleased (no CHANGELOG
  entry). Found fixing it: item 212
- [x] 131. A ModelForm update that omitted a declared `ModelChoiceField` without `to_field_name` over a
  `ForeignKey(to_field=...)` / `OneToOneField(to_field=...)` refilled it with the stored `to_field` value where the field
  resolves by pk: "Select a valid choice" on every such partial update, or, when that value equals another row's pk, a
  silent re-link to that row (including one the related type hides); the refill now reads `model_to_dict` only when the
  form field's key names the column the FK stores, and otherwise rebinds the related row by the field's own key, as a
  provided value decodes (`b2f8d05c`). Released in 0.0.13 and 0.0.14: item 214
- [x] 61. `RelatedFilter` cycles (two or more `FilterSet`s, and sets pointing into one) published flat filters decided by
  which type registered first: the first-expanded set's re-entry fallback was cached into every other member, so a flat
  filter validated in one registration order and was unknown in another (fakeshop's library inputs moved with it). A flat
  path now follows `RelatedFilter`s until it reaches a filter set already on it, whose own filters end it there, so each set
  publishes one surface in every order, the largest any order published (`6b5d43d4`); CHANGELOG item 215; filed 216, 217
- [x] 63. An offset `after` cursor whose page ended on `sys.maxsize` failed Strawberry's last-only `assert last is not None`
  (the cursor at `sys.maxsize - 1 - N`, N the page the engine is handed: `first: N`, `last: 0` as `first: 0`, the cap with no
  page argument), and one ending past it overran `islice`'s stop on a generator source or a 64-bit `LIMIT` under a
  `sys.maxsize` page cap: a masked unexpected error on root, consumer-resolver and per-parent connections, sync and async.
  `offset_engine_arguments` now hands the engine every forward page ending at most at `sys.maxsize - 1`, so every accepted
  cursor serves the past-the-end page the optimized window serves (`60825338`); CHANGELOG item 218; filed 219
- [x] 188. Re-checked at `8ca6a481`: a nested list whose `get_queryset` returns `union()` / `intersection()` /
  `difference()` no longer raises `NotSupportedError`; the combined result is served as its pk set, optimizer on and off
  (`5c5e32c5`, item 6; `test_combined_visibility_api.py` 199 passed)
- [x] 189. Re-checked at `8ca6a481`: an overlapping declared and generated lookup runs the generated one, two lookups on
  one key both apply, and `{"id": {"gt": 999}}` on a generated-only field filters (`754ed263`, `9f7ea5dd`, item 4)
- [x] 192. Re-checked at `8ca6a481`: an `allow_blank` serializer `ChoiceField` publishes a `BLANK` member that writes `""`
  (`a5dc6ea3`, item 5)
- [x] 195. Re-checked at `8ca6a481`: `test_audit_marks_target_parse_failure_as_incomplete` and the three `async_executor`
  rows in `tests/utils/test_querysets.py` pass; no fix commit identified (possibly stale when filed)

## Outside review of the fixes

An outside review of the fixes since the hunt, by finding id (C-number). History only: not counted in Progress. Items with a
tracker number are recorded there; open remainders and new defects are filed as items 146-150.

| Finding | Outcome | Commits |
|---|---|---|
| C11. A nested keyset window paged by `get_queryset`'s order but sought and minted by `Meta.cursor_field` | Item 95 | `5197d03d` |
| C11, reversed. A `.reverse()`d `get_queryset` order paged with forward cursor terms | Item 99 | `b005a7ee` |
| C8. A relation pk prefix on a GlobalID filter path skipped model validation | Fixed | `d03a7c79` |
| C45. A nested combinator projecting `.values()` raised a raw SQL error | Fixed | `1bd0f0f4` |
| C48. The public test clients could not serialize a `Mapping` of variables | Fixed | `d5f0d6f7` |
| C54. The `RangeFilter` input cache failed on an unhashable filter subclass | Fixed: the cache is gone | `702c6b67` |
| C57. A renaming `NameConverter` broke type-strategy GlobalID round trips | Item 116 | `e05b2436` |
| C33. Relay's sync refusal left the async `resolve_node` coroutine unawaited | Fixed | `f35a441c` |
| C41. `review_plan --changed` omitted deleted modules | Fixed | `96164e29` |
| C53. `count_queries` compared reports of different executed operations | Fixed | `48ca8bec` |
| C46. Two `prove_failability.py` runs could both own the tree | Item 119 | `ce338eec` |
| C3. A run queued during a copy's first sync resynced over the edits made since | Item 139 | `4ed767bb` |
| C4. `workspace.py release` / `gc` dropped active work after their busy check | Item 140 | `4ed767bb` |
| C9. A qualified or aliased `DjangoOptimizerExtension` evaded the governance gate | Fixed | `40a0fb96` |
| C55. A negative definition test passed with its production guard removed | Fixed | `ae18e793` |
| C31. A concurrent ledger test shared one `Context` across threads | Fixed | `dfc32247` |
| C40. A reverse one-to-one visibility test lost the planned optimizer path | Fixed | `962c61b9` |
| C6. Docs: MySQL's ASC `NULL` placement was reversed | Fixed | `f4c9f78a` |
| C16. Docs: the migration plan mapped the page cap to the raw-list cap | Fixed | `fce3ab31` |
| C17. Docs: explicit-null update timing promised no earlier DB work | Fixed | `e1b1e202` |
| C18. Docs: the edges-only rationale claimed an N+1 fetch | Fixed | `fe884e44` |
| C19. Docs: the offset-only plan left the high mark unchanged | Fixed | `4a736809` |
| C20. Docs: the limit-only plan promised null on a non-null outer list | Fixed | `affe41dc` |
| C25. Docs: the live-test README reversed the ruff fix / format order | Fixed | `56ecb877` |
| C28. Docs: the serializer reverse one-to-one cardinality example was inverted | Fixed | `00bb2482` |
| C42. The item-diff check omitted new untracked files (now included); staging alone still changes its seal | Partial; remainder item 146 | `acb6c25a` |
| C24. The KANBAN glossary inliner linked terms inside existing links | Partial; remainder item 147 | `09d0caa0` |
| C44. The test-model census conflated same-named classes across scopes (fixed); imports still resolve through one flat map | Partial; remainder item 148 | `f7000986` |
| C15. An in-place change to the settings `OrderedDict` stays stale | Not a defect: configuration is trusted after construction; only an exact `dict` source is held by reference (other mappings are copied by design, per `conf.py::_normalize_user_settings`), and replacing or overriding the setting reloads (`override_settings` fires `setting_changed`) | none |

## To do: t3 robustness rows

29 low-priority rows across items 20-25 plus item 27's unfiled leads (the rows behind items 15-19 are done and item
26's moved to "Waiting on you"), mostly guards against classes with broken `__name__` / `__eq__` / metaclasses.
Expected outcome: most are not real bugs and just get deleted from t3. One checkbox per area:

- [ ] 20. Filter and order sets (8 rows)
- [ ] 21. `routers.py`, `list_field.py` (2 rows)
- [ ] 22. `types/` (7 rows)
- [ ] 23. `utils/` (9 rows)
- [ ] 24. Trailing-comma lint in two test files (2 rows; main passes `scripts/check_trailing_commas.py --check` at
  `8ca6a481`, so these are t3-only)
- [ ] 25. Stale test-fixture row in `tests/utils/test_querysets.py` (item 41's fix `cab934a0` did not touch this file)
- [ ] 27. Unfiled leads from the same family (triage with the rows above)

## To do: found along the way

- [ ] 92. A consumer `save()` raising Django's `ValidationError` escapes the ModelForm flavor as a masked top-level error, while the
  serializer flavor maps it into the envelope
- [ ] 97. A `FilterSet` declaring `{"<fo>": ["exact", "isnull"]}` over a forward `ForeignObject` raises django-filter's
  `AssertionError: unrecognized field type ForeignObject` at class creation, where a `ForeignKey` builds `isnull`
- [ ] 100. A random `"?"` order (hook `order_by("?")` or `Meta.ordering = ["?"]`) on an optimized nested offset connection
  raises "Cannot resolve keyword '?' into field" (masked), reversed or not, `first:` or `last:`; the root path serves it
- [ ] 101. `manage.py import_spec_terms --check` fails on spec-020's terms CSV on main (seen at `eb30dd7e`); a later run
  reported eight specs failing (020, 027, 028, 032, 036, 037, 043 and one more)
- [ ] 107. A writable primary-key relation (MTI parent link, OneToOne `primary_key=True`) in an update input fails at request
  time instead of at class creation
- [ ] 108. A serializer-only source over the default `create()` / `update()` (`gs = PrimaryKeyRelatedField(many=True,
  source="genres_id")`) builds; create raises a masked TypeError and update is a silent no-op
- [ ] 109. `pid = PrimaryKeyRelatedField(source="pk")` over a relation primary key builds and every create raises a masked
  TypeError: `backing_model_field` does not resolve `"pk"`, while `write_source_key` does
- [ ] 110. The item-56 alias message labels an owner `'category_id' (source 'category_id')` when the name and the source match
- [ ] 111. A GenericForeignKey own-name `PrimaryKeyRelatedField(source="content_object")` raises `AttributeError` in
  `_require_relation_primary` (`related_model` is None) instead of `ConfigurationError`
- [ ] 113. On a connection the consumer pipeline (visibility, `FilterSet`, `OrderSet`) runs before the deadline check: past the
  deadline, `allLibraryGenresConnection(filter: {books: {shelf: {homeBranch: {exact: $pk}}}})` runs the `ModelChoiceFilter`
  branch lookup, and an invalid pk answers `FILTER_INVALID` instead of the deadline rejection; item 114 closes it
- [ ] 114. Request-rejection precedence (design approved 2026-10-08, all 7 decisions;
  `~/dst-handoff/2026-10-08/admission-design.md`, which also holds the wire-change table and the CHANGELOG text):
  - One order: P0 document admission, P1 field-argument errors, P2 the deadline, P3 the consumer pipeline, P4 slice and database.
    One seam: a new `admission.py` (`admit_connection_page`, `admit_list_page`, `admit_node_refetch`); connections enter it
    through a package `DjangoConnectionExtension(ConnectionExtension)` built with `strawberry.field(extensions=...)`, replacing
    both `relay.connection(` calls (`connection.py`, `types/finalizer.py`). Node fields decode the id before the deadline;
    `first` + `last` keeps `PaginationArgumentError` and its message. Doc home: spec-047 Decision 14, a glossary entry
    "Request rejection precedence", one AGENTS.md line.
  - Draft: `refs/scratch/admission-wip` (`970d054a`), unfinished and never run, cut before many landings; its glossary,
    KANBAN and constants may be half-regenerated. Still to write: `examples/fakeshop/test_query/test_admission_api.py`,
    `tests/test_admission.py`, failability (swap P1 and P2; move admission after `next_`).
  - Watch: reproduce everything `relay.connection()` sets up beyond the extension; never leak the admitted page across parents
    or concurrent async fields; `bounded_rows` / `bounded_rows_async` are public and keep their deadline check; the keyset
    cursor's shape and signature are P1 while the column-fingerprint match stays at the seek; the walker's plan-time catch in
    `optimizer/nested_planner.py`.
  - Text this changes: `8d4f66bd` documents `get_queryset`, `check_*_permission` and consumer `FilterSet` / `OrderSet`
    running before the deadline (connections, `DjangoListField`, the many-side re-check) as trusted application code. Under
    strictness `"raise"` past the deadline a forward FK / OneToOne hop reports the deadline while a many-side hop reports the
    N+1 error (`_check_n1` runs before `bounded_rows`). A generated mutation's transaction opens before the write pipeline's
    check (an audited exclusion in `8d4f66bd`).
  - Open: decision D-A (a deferred pending-source marker instead of the approved `DjangoConnectionExtension` subclass) was
    never ratified and D-B (the keyset rejection class) never chosen; this item's seam text follows the answer. The verified
    31-file implementation of the marker design is on no commit or ref and was not found in scratch; recover or re-create it.
    Also: it adds a second deadline read per parent (about 270 ns on many-side relations, unmeasured); writes check the
    deadline before `coerce_lookup_id`, and this item never names writes; nested resolvers call
    `getattr(root, accessor).all()` before admission, so consumer manager code runs ahead of P1 / P2.
- [ ] 115. Item 12's hot-path AFTER number was never taken (BEFORE: `check_deadline` about 300 ns per call, +24% to +46% per
  resolver call, about +1% end to end at 100 rows): `<tree>/.venv/bin/python ~/dst-handoff/2026-10-08/hotpath12_bench.py
  --tree <tree> --json after_run1.json`. Unmeasured: return early when neither the budget nor the context mirror holds a
  deadline (skips 4 of the 8 calls)
- [ ] 120. `prove_failability.py` has no SIGTERM / SIGHUP handler: a terminated run leaves its mutation in the tree and
  its `ACTIVE-MUTATION.json` marker; recovery is by hand from `restore_with`
- [ ] 121. A crashed `prove_failability.py` run without `--scratch-root` leaves its marker in its own `failability-*`
  directory, so the next default-mode run is not refused and reads the mutated tree; a `pre_image` or `reverse_patch`
  entry would copy the mutated bytes as pristine
- [ ] 122. `prove_failability.py` names pristine copies `pristine/<label-digest>__<path>`, the same path for every run of
  one tree under one `--scratch-root` (harmless while the tree lock excludes concurrent runs)
- [ ] 123. BUILD.md "Mechanized: `scripts/prove_failability.py`" says the tool's default scratch is "a bare `/tmp` path";
  it is a fresh `failability-*` directory under `TMPDIR`
- [ ] 124. ModelForm: an explicit `null` on a declared non-required choice field (or `CharField`) over a non-blank text
  choice column stores `""` (Django skips model validation for an empty value on a non-required form field), and the read
  enum then cannot serialize the row ("cannot represent value: ''"); the serializer flavor refuses the analogue at build
- [ ] 125. ModelForm: no check that a declared field's kind agrees with its column beyond choice columns
  (`MultipleChoiceField` over a non-choice text column, a single `ChoiceField` over an `ArrayField` of choices,
  `IntegerField` over a text column); the serializer flavor checks agreement in `_model_backed_scalar_annotation`
- [ ] 126. A plain `Form` `ChoiceField` publishes `String`, while a serializer-only `ChoiceField` publishes a generated enum
- [ ] 127. Lead: a serializer single `ChoiceField` over an `ArrayField` may skip
  `_reject_choice_values_the_column_does_not_list` (`column.choices` is `None`) and publish a scalar enum
- [ ] 132. A `SerializerMutation` whose `Meta.fields` narrowing keeps a relation to a Relay-Node type fails schema build
  (`TypeError: Mutation fields cannot be resolved. '<...>PartialInput'`), create and update, e.g. `Shelf.branch`; a non-Relay
  target builds
- [ ] 133. A `PrimaryKeyRelatedField` to a model whose pk is a `OneToOneField` (`PatronProfile`) is refused at schema build
  ("Unsupported Django field type 'OneToOneField' on PatronProfile.patron"); a FK to such a model cannot be written by a
  serializer mutation (fails loud)
- [ ] 135. A malformed GlobalID in a relation input, single (`categoryId: "not-base64!!"`) or an `[ID!]` element
  (`genres: ["not-base64!!"]`), is a masked top-level error with `data: null` in the model, ModelForm and serializer
  flavors: Strawberry raises `GlobalIDValueError` at the mutation resolver before any package decode, so the field-keyed
  envelope (which a well-formed but missing, wrong-type or hidden id gets) never applies;
  `test_products_api.py::test_create_item_malformed_category_id_is_top_level_coercion_error` pins the outcome but its
  docstring says variable coercion
- [ ] 137. ModelForm and serializer flavors: a relation id naming a visible row whose `to_field` key is `NULL` clears an
  optional relation silently (the form binds `None`; the serializer's descriptor assignment stores `NULL`), where the model
  flavor refuses it as the relation error since item 130; `forms/resolvers.py::_to_form_key_value` also falls back to
  `obj.pk` when `to_field_name` does not resolve on the row
- [ ] 141. `workspace.py baseline` records the ITEM_BASELINE sha before it waits for the copy's lock and syncs, so the
  `before` copy can come from a later tree than the recorded sha
- [ ] 142. A SIGKILLed `workspace.py` leaves its command running without any lease (its fds are not inherited), so `gc`
  or `release` can remove or unbind the copy under a still-running pytest
- [ ] 143. The macOS `$TMPDIR` purge deletes a flow's `.dsf-ws` marker after about 3 idle days, so START.md's "gc the flow
  before reuse" refuses ("carries no marker") until a run writes it again
- [ ] 144. `workspace.py gc`'s Postgres `stop_if_idle` runs after the flow lease is released and can race another flow
  creating a database
- [ ] 145. `workspace.py status` can raise `FileNotFoundError` reading `state.json` while a `gc` removes the flow
- [ ] 146. `workspace.py::item_diff` emits the tracked and staged diff first, then the untracked files: staging an unchanged
  added file moves it into the first group, so the diff order and its seal change and `diff --check` fails after staging
  alone; the diff should be one baseline-versus-content diff independent of the index
- [ ] 147. `scripts/build_kanban_md.py::GlossaryInliner._protected` does not protect URI or email autolinks:
  `Read <https://example.com/?q=DjangoListField>.` gets a glossary link inside the URI autolink, changing its destination
  (`<DjangoListField@example.com>` likewise); a later plain mention must still link (the test's mention must not be
  followed by `.`, which `TERM_BOUNDARY_AFTER` reads as a path character). `09d0caa0` already protects `[...]` groups with
  quoted titles, nested-parenthesis destinations, shortcut references and double-backtick code spans
- [ ] 148. `scripts/census_test_models.py::_import_map` folds every import in a file into one flat map, so an import's effect
  ignores scope and position: a function-local `import ... as Model` replaces the module-level one (a real module-level
  Django model drops out of the census), the converse makes a plain class count as a model, and a module-level import after
  its use rebinds earlier bases; imports should resolve through the same scoped, position-aware bindings as class
  declarations. Scoping also ignores `if` / `try` alternative declarations, assignments, parameters and comprehension /
  lambda scopes. The census still assumes a function runs after its enclosing scope finished, so a factory called before a
  later rebinding of its base counts the base but not the child (documented in `_census_tree`, pinned by
  `FACTORY_BEFORE_REBINDING_SEES_FINAL`); decide whether that stays an accepted approximation or gets a flow-aware resolver
- [ ] 149. `scripts/count_queries.py` with a `--query` document that lacks the `--operation-name` (an anonymous `query { ... }`,
  or a named document without that name) raises an uncaught `CannotGetOperationTypeError` from `execute_sync` and exits 1,
  the "scales with cardinality" code, instead of printing NOT MEASURED and exiting 2
- [ ] 150. `docs/bug_hunt/pbugs.md`'s Postgres scrutiny line has `DESC` `NULL` placement backwards: SQLite sorts `NULL`s
  last on `DESC` and Postgres first
- [ ] 151. A declared `MultipleChoiceField`, `ListField(child=ChoiceField)` or single `ChoiceField` over a nested
  `ArrayField(ArrayField(<choices>))` builds, where every other field and flavor refuses the nested array, and writes a flat
  list (or a scalar) into the 2-D column, unchecked against the inner `base_field`'s choices (`choices=[("zzz", ...)]` stores
  `["zzz"]`): `rest_framework/serializer_converter.py::_model_backed_scalar_annotation` returns the declared enum before
  `convert_scalar`'s nested refusal, and `_multiple_choice_element_column` stops at the inner `ArrayField` (item 127's path)
- [ ] 152. A declared `ListField(child=ChoiceField(allow_null=True))` over an `ArrayField` whose `base_field` is NOT NULL
  publishes `[XEnum]` and stores a `null` element (no database constraint covers an array element), so every later read of the
  row's field fails "Cannot return null for non-nullable field" (with the field selected in the same mutation, the write rolls
  back behind that top-level error): `_reject_choice_values_the_column_does_not_list` leaves `None` to the column
- [ ] 153. A serializer field built by a `get_fields()` override or `Meta.extra_kwargs` (`child=`) is not consumer-declared
  (`_is_consumer_declared`), so its input takes the backing column's read type whatever the field validates
  (`ListField(child=MultipleChoiceField)` over a flat choices `ArrayField` publishes `[XEnum!]`, an `IntegerField` over a choice
  column publishes the enum) and every non-empty write is refused field-keyed; robustness, item 125 is the ModelForm analogue
- [ ] 154. `rest_framework/inputs.py::_fingerprint_converter_extra` records only a `ListField`'s direct child class and
  `allow_null`, so a `get_serializer_for_schema()` that drifts a nested `ListField` leaf (`IntegerField` vs `CharField`, or its
  `allow_null`) passes the bind's drift guard and schema construction raises a raw `TypeError: Mutation fields cannot be
  resolved`; `serializer_schema_fingerprint`'s docstring claims every SDL axis
- [ ] 155. Specs 030, 031 and 032 (lines naming the "uv.lock-resolved" Strawberry) and the spec-030 / spec-032 rationale
  companions name strawberry-graphql 0.324.0; `uv.lock` resolves 0.327.7. Re-check each claim against the locked release
- [ ] 156. `CaptureQueriesContext` records no queries on the async transport, so an async query-count assertion passes
  vacuously
- [ ] 157. A consumer `Prefetch` / `OptimizerHint.prefetch` that wins over the optimizer's plan makes six grid cells issue more
  queries optimizer-on than optimizer-off (52 vs 51, worst 180 vs 51, `Item.entries`); a policy question against spec-035's
  consumer-wins rule (BACKLOG B8 covers only the opt-in merge)
- [ ] 158. Outside QUERY operations (operation gate closed: mutation, subscription, a mutation's post-write re-fetch) a planned
  child keeps the hook's consumer `.only()` and gains no link columns, so selected columns lazy-load row by row (fails on
  async); read from code, not reproduced, unreachable from fakeshop
- [ ] 159. A default manager that returns a combined queryset is still refused on the nested-relation path when no
  `get_queryset` hook is involved (`optimizer/nested_fetch.py` returns `"combined"` and leaves the relation unplanned)
- [ ] 160. A one-sided declared range (`range: {start: ...}` or only `end`) compiles to `BETWEEN x AND NULL` and returns no rows
  (`filters/base.py::RangeFilter`); seen early in the fixes, re-check on HEAD
- [ ] 161. A declared `django_filters.RangeFilter` writes `_0` / `_1` keys while the installed django-filter widget may read
  `_min` / `_max`, so its bounds are ignored (`filters/inputs.py` documents the positional keys on purpose); check the
  installed django-filter's key names before fixing
- [ ] 162. A NaN bound on a declared range reaches the model field and raises a raw `ValidationError` instead of
  `FILTER_INVALID`: `filters/base.py::RangeField` overrides only `to_python` and never cleans its bounds with the column's
  form field
- [ ] 163. The `get_queryset` hook receives a plain `QuerySet`, so a project `QuerySet` method raises `AttributeError`; README,
  GLOSSARY and the `DjangoType.get_queryset` docstring never say so (recommend `queryset & Model.objects.<method>()`)
- [ ] 164. Fakeshop's plain `strawberry.field` roots that return QuerySets (`allLibraryPrefetchedBooks`,
  `allLibraryCardsProjected`, `allLibraryCardsDeferred`) raise `SynchronousOnlyOperation` on `/graphql-async/` for any
  selection; item 53 covers only the README wording
- [ ] 165. Item 12's deadline checks fail forward-FK and one-to-one hops inside a mutation payload (rolling back a write that
  used to commit) and error subscription frames past the budget; spec-047 Decision 9 states both (`8d4f66bd`) but no test
  pins either; the async deadline rows also cannot tell a head check from a check inside the `sync_to_async` closure
- [ ] 166. Fixture gaps: the async many-side tests miss a broken prefetch-cache lookup in `types/resolvers.py::many_resolver`;
  no fakeshop reverse many-to-many without `related_name` has an unhooked target (lost with item 28's fixture); no fakeshop
  to-many name repeats at two depths with different targets (the window resolver-key collision is pinned only by a
  two-root-field row); no shipped fakeshop keyset type orders in its hook (the C11 live rows use a test-local schema)
- [ ] 167. Strawberry's native `relay.node()` raises an unexpected error on a model-label GlobalID (`products.category`);
  check whether the package emits one (the spec-032 rationale says it does under the model strategy)
- [ ] 168. Robustness: `types/relay.py::_resolve_id_default` falls back to `getattr` and can lazy-load a deferred custom
  `NodeID` column or one annotated on a relation name (an audited exclusion in `resource_policy.py`, no row)
- [ ] 169. Robustness: `workspace.py release` and `gc` raise an uncaught `NotADirectoryError` when a regular file sits at the
  flow path (`scripts/workspace.py::_lock_flow_dir` catches only `FileNotFoundError`; `main` catches only `WorkspaceError`)
- [ ] 170. No test runs `workspace.py prove` (`scripts/workspace.py::_cmd_prove`); its flow lease and copy lock are pinned only
  through `execute`; add a `main(["prove", ...])` row and a two-run contention row
- [ ] 171. No tool measures coverage of a diff's changed lines without the full-tree gate (a mutation spanning two sites
  needs no hand script: `prove_failability.py` entries take `"sites": [...]`)
- [ ] 172. START.md's resource-gate rule has no working probe: `pgrep -f` self-matches multi-line command lines and
  `memory_pressure` prints "System-wide memory free percentage", which the rule does not parse
- [ ] 173. The KANBAN "Before a release" checklist (BoardDoc 11) runs `ruff format .` before `ruff check --fix .`, the reverse
  of AGENTS and pre-commit; reverse it through the DB and re-render (archived specs 015, 034, 041, 042, 044, 046 and 057 keep
  the old order as history)
- [ ] 174. BACKLOG `stable_cursor_field` describes the shipped `Meta.cursor_field` keyset cursors as future work
- [ ] 175. spec-050 Decision 9, its rationale and KANBAN's contract sentence say only "a positive offset raises the low mark";
  the high mark moves too (row 21, fixed by C19, says both)
- [ ] 176. Async execution without `DjangoOptimizerExtension`: a nested connection under a `DjangoListField` root leaves a
  coroutine in `result.data` (`_resolve_keyset_connection.<locals>._resolve_async` never awaited); a `DjangoConnectionField`
  parent and the optimizer-on run are fine; pre-existing, check whether optimizer-off async is a supported configuration
- [ ] 177. The test clients copy only the top level of `variables`: a non-dict `Mapping` nested inside raises `TypeError` (not
  JSON serializable), and under `files=` the placeholder walk fails with `AssertionError ... cannot descend`
- [ ] 178. `review_plan.py scope` "Folders touched" (`ScopeReport.folders`) omits a rename's old folder and still names a
  deleted package's integration item, while `--changed` covers both; REVIEW.md says `scope` lists the same changes
- [ ] 179. Test strength: C31's ledger test still passes with `_NormalizationLedger.publish`'s lock removed (`list.append` is
  atomic under the GIL), though the class says "The lock is not decoration"; the C9 governance gate does not catch a
  `typing.cast(...)` wrapper (undocumented, beside the documented set-literal, rebinding, `getattr` and factory limits);
  one non-contention row of `tests/test_prove_failability.py` mocks `fcntl.flock` where AGENTS allows mocks only for an
  impossible real path
- [ ] 180. Strictness `"raise"`: a hook-order cursor on a relation the strictness gates refuse counts as malformed, so a real
  per-parent access goes unflagged (pinned as intended by
  `test_hook_order_cursor_on_a_refused_keyset_relation_keeps_its_per_parent_page`)
- [ ] 181. `utils/querysets.py::applied_order` ignores `extra_order_by`, so a reversed queryset ordered by `extra(order_by=)`
  compiles flipped
- [ ] 182. `scripts/clean_up.py` and the `review_*` generators `rmtree` / unlink their own folders with no lock (no concurrent
  writer known; robustness)
- [ ] 183. `ruff format` on an explicit `.md` path rewrites its fenced blocks: pyproject's `exclude` does not stop explicit
  paths
- [ ] 184. `tests/base/test_conf.py` crashes the coverage tracer on Python 3.14's default core (`COVERAGE_CORE=ctrace` needed)
- [ ] 185. WebSocket residuals after `1b6a09b1`: a sync caller blocked in `async_to_sync` keeps the shared connection, and the
  Postgres steady-ping lost-write test has never run; the async mutation window has no owning spec or card
- [ ] 186. docs/README.md has no consumer-`Prefetch` / `.only()` cooperation sentence and no inert-arm sentence (GLOSSARY has
  both: "`only()` cooperation", from item 83's `548059b3`, and "Membership leaves")
- [ ] 187. The C11 keyset fixes were never run on PostgreSQL's LATERAL path, and the workspace / prove_failability `flock` rows
  never on Linux or NFS locally (CI runs the rows on ubuntu)
- [ ] 190. Seen at `87dc1df7`, re-check: an out-of-range datetime, an invalid regex and a regex on a UUID field raise uncoded
  errors
- [ ] 191. A malformed relation GlobalID (item 135) nulls the whole response, so a sibling mutation earlier in the same
  document stays committed while `data` is `null` (`{ a: createItem(valid) b: createItem(malformed) }`, variable or
  literal id; re-checked at `8ca6a481`)
- [ ] 193. Seen at `87dc1df7`, re-check: directive argument values, variable-definition directives and defaults used only from
  untyped positions are uncharged by the resource budget, and a 200 KB literal reaches a custom scalar's `parse_literal`
  (item 7 was closed as already fixed)
- [ ] 194. An enter-side cancel defect was reported early in the fixes but never reproduced, and the report names no site
  (which hook, sync or async): name it or drop it. (`last: 0` answering `hasNextPage: true` while rows exist is the
  deliberate `first: 0` page since `dbf0a870`)
- [ ] 212. No static gate for a name defined inside a `TYPE_CHECKING` block (a `TypeVar`, `Protocol` or `TypeAlias`) used in
  an eager annotation of a module without `from __future__ import annotations`: it raises `NameError` at import on 3.10-3.13
  while ruff (`TC004` covers imports only, `F821` sees a binding) and basedpyright pass; six package modules define such names
  (all quoted today); only the floor run of `tests/base/test_init.py` catches it
- [ ] 213. `filters/inputs.py` docstrings carry process provenance START.md bans: `_require_list_container` ("The previous
  arms SPLATTED ...") and the GlobalID list arm ("The previous implementation eagerly decoded ..."); restate each as the
  invariant, and sweep the older filter tests for the same wording
- [ ] 221. `auth/mutations.py::derive_register_fields` still dedups and intersects the consumer's `USERNAME_FIELD` /
  `REQUIRED_FIELDS` entries by their own `__hash__` / `__eq__`: an unhashable or raising entry escapes raw, and a `str`
  subclass whose `__eq__` is always False slips past the protected-field refusal (`('username', 'is_staff', 'password')`).
  Reading each entry through its base `str` slot at the read closes both but returns base `str` names
- [ ] 222. Class membership by equality outside the mutation ledgers: `registry.py::TypeRegistry.register`
  (`type_cls in existing_types`) and `filters/sets.py` (`if cls in path`) dispatch a metaclass `__eq__`; check each against
  the identity contract its store records under
- [ ] 224. `DjangoOptimizerExtension(strictness=)` accepts a `str` subclass by content but stores the value itself, so
  `extension.py` (`self.strictness != "off"`) and `types/resolvers.py` (`strictness == "raise"` / `"warn"`) dispatch the
  consumer's `__eq__` on every request; storing the matched vocabulary constant (as `resolve_strategy` returns registry
  instances) closes it
- [ ] 225. `forms/inputs.py::_form_field_basis` checks identifier names over the whole basis before `Meta.fields` /
  `Meta.exclude` narrowing, so a narrowed-away non-identifier form field is refused although it never becomes an input
  attribute; the serializer flavor checks only the kept set (`rest_framework/inputs.py::resolve_effective_serializer_fields`)
- [ ] 226. A nested serializer's own `.fields` map gets none of the field-map checks the root gets
  (`rest_framework/inputs.py::read_nested_serializer_fields`): no plain-`str` key gate, no `serializers.Field` test before
  `writable_serializer_fields` reads `.read_only` and a bare `isinstance(field, HiddenField)`, and it catches `Exception`, not
  `BaseException`
- [ ] 227. `exceptions.py::_safe_predicate(isinstance, ...)` evaluates a lazy proxy and turns any exception raised while doing
  so into `False`, the package's own `ConfigurationError` included (a lazy `save()` return ran write SQL and its alias-guard
  error was replaced by "not a ... instance"); relevant to item 94's posture
- [ ] 228. `exceptions.py::_safe_arg_repr` does not bound length, so a `got {...}` tail can carry a megabyte repr into the
  message (a custom `save()` returning a large string)

## To do: holes found re-checking the fixes

- [ ] 64. Cursor-decoder guards: the `isascii` term in `utils/connections.py::decode_offset_cursor` is redundant behind
  `str(position) != raw` (drop it or keep it), and no live row pins a malformed nested-window cursor
- [ ] 66. Index advisory on a multi-table-inheritance child names an order column that lives on the parent table
- [ ] 67. Nested serializer: a Django error raised in `create()` for a child is keyed to a renamed root input
- [ ] 70. Argument-less directives are re-walked on every fragment expansion (about 80 ms at the token bound; bounded, robustness)

## Waiting on you

- [ ] 26. A mutation class whose `__name__` raises, is not a `str`, is a format-hostile `str` subclass, or is not a
  GraphQL name: fail at declaration with a typed error, or keep? At HEAD the model and form flavors fail raw at declaration
  (`mutations/sets.py::DjangoMutation._validate_meta`, `forms/sets.py::DjangoModelFormMutation._validate_meta`,
  `forms/sets.py::DjangoFormMutation._validate_meta`), and a hostile form class name fails a valid declaration through
  `forms/inputs.py::resolve_effective_form_fields`. Only a rename after declaration reaches `DjangoMutationField` (the
  `<Name>Payload` ref), `bind_mutation_outputs` and every request (`mutations/resolvers.py::run_write_pipeline_sync`). A
  non-identifier name (`type("Create Item", ...)`) raises a raw `SyntaxError` at `DjangoMutationField`, and
  `"Create-Item"` fails only at schema build. Input and payload names derive from `__name__`, so the answer covers every
  flavor, the auth riders' user-model labels (`auth/mutations.py::derive_register_fields`,
  `_resolve_user_primary_or_raise`, and the eager subject in `mutations/inputs.py::editable_input_fields`) and the GraphQL
  names
- [ ] 229. Input field names that are Python identifiers but not GraphQL names (`"é"`, a leading `__`, and on Python
  3.10-3.13 NFKC-unnormalized identifiers such as `"ａ"`) pass both mutation flavors' class-creation checks and fail later
  with graphql-core's or the stdlib's raw error. Add a GraphQL-name check on kept input names in both flavors, or keep the
  identifier-only rule?
- [ ] 220. A `Meta.permission_classes` entry whose `__name__` raises is accepted at declaration, then every request raises it
  raw: `mutations/permissions.py::run_permission_classes` computes `owner=permission_class.__name__` before it knows the
  result is a bool (the request user's class name in `DjangoModelPermission.has_permission` likewise), and the conflict
  message in `auth/mutations.py` renders permission-class names raw. Read the label only on the failure branch, reject at
  declaration, or keep?
- [ ] 53. Docs (parked): docs/README.md, the async paragraph under `DjangoListField`:
  a hand-written `@strawberry.field` returning a QuerySet runs synchronously
- [ ] 54. Docs (parked): glossary, a sliced combinator branch on SQLite raises Django's own `DatabaseError`
- [ ] 57. CHANGELOG entry for item 11: model, ModelForm, plain-form and register errors, and a `ValidationError` raised
  during a serializer save, now use the input name (`categoryId`, not `category`)
- [ ] 68. A model's default manager hides rows from declared filter hops but not from undeclared filter hops or ordering. Make them
  agree, or keep?
- [ ] 69. CHANGELOG entry for item 1: `Meta.exclude=["parent"]` on a mutation over a `ForeignObject` model now raises
- [ ] 71. CHANGELOG entry for item 59: two `RelatedFilter`s or `RelatedOrder`s naming one relation now raise at class creation, and a
  longer one (`shelf__branch` beside `shelf`) raises at expansion when the shorter branch's target set reaches `branch`
- [ ] 75. CHANGELOG entry for item 72: a `FilterSet` or `OrderSet` shared by an MTI parent and child type now raises at finalize, and
  a concrete type's path through an FK declared to a proxy (`BranchNote.branch`) reads the bound type, not the proxy's type
- [ ] 76. CHANGELOG entry for item 62: a `SerializerMutation` whose serializer declares a flat `ChoiceField` over a grouped-choices
  column binds again (checked against the column's flattened values); a refused value now reads "which does not list it", and a
  serializer field taking a grouped column's read enum is refused with a remedy to declare a flat `ChoiceField` (over an
  `ArrayField` whose `base_field` is grouped, a `MultipleChoiceField` or `ListField(child=ChoiceField)`)
- [ ] 77. The read enum refuses a grouped-choices column, though group labels are presentation like choice labels. Flatten it on
  the read side too (retires the `str`-override carve-out and the write-side grouped refusal), or keep?
- [ ] 78. CHANGELOG entry for item 65: every single-value lookup on a choice column (`exact`, `iExact`, `contains`, `gt`,
  ...) treats each enum member as a value (`iExact: BLANK`
  matches blank rows only, a `"null"` member matches `"null"`); raw form data and declared `ChoiceFilter`s are unchanged
- [ ] 79. CHANGELOG entry for item 52: connection fields no longer send consumer-source or row-hydration exception text to the
  client; pagination rejections keep their messages and are the new public `PaginationArgumentError`
- [ ] 73. A set subclass used only as a `RelatedFilter` / `RelatedOrder` target, never wired to a type, inherits its base's owner and
  that owner's visibility. Keep, or fall back to the target model's registered type?
- [ ] 84. `range: []` applies no constraint on every generated `range` (and `range: [1]` is a validation error), where Django
  raises on both. Make `[]` an arity error like `[1]`, or keep?
- [ ] 85. A nested branch that constrains nothing (`shelves: {}`, `shelves: { condition: { in: null } }`) still keeps only parents
  with a visible child (`_apply_related_constraints`), at the top level and inside `and` / `or` / `not`; strawberry-django treats
  it as no condition. Make it the identity, or keep (and state it in spec-027 Decision 8)?
- [ ] 86. CHANGELOG entry for item 14: an explicit `in: []` on every generated membership lookup matches no rows (integer, text,
  choice, date and every other column type used to return every row); `not: {}` matches every row and `or: [{}, real]` is the real
  arm; a declared `ModelMultipleChoiceFilter` `[]` inside `not` now matches every row; raw `?x__in=` is unchanged
- [ ] 91. CHANGELOG entry for item 43: a serializer `ListField(child=ChoiceField)` publishes a list of the field's generated enum
  (clients send enum names, not strings: `[a]`, `[MEMBER_1]`), and `MultipleChoiceField(allow_blank=True)` accepts `BLANK` as `""`
- [ ] 45. Postgres: plain `ChoiceField` over an `ArrayField` builds, then the save fails (parked: needs a Postgres run)
- [ ] 46. Postgres: a declared `ListField(child=<non-choice scalar>)` over an `ArrayField` is refused at build ("Unsupported
  Django field type 'ArrayField'": the agreement check in `_model_backed_scalar_annotation` calls `scalar_for_field`, which
  has no `ArrayField` entry); a `ChoiceField` child builds (parked: needs a Postgres run)
- [ ] 47. Postgres: `serializer_choice_field=MultipleChoiceField` over an `ArrayField` is unusable (parked: needs a Postgres run)
- [ ] 93. CHANGELOG entry for item 44: a ModelForm mutation over a non-text choice column with `blank=True, null=False` answers
  `null` (or an omitted field with no default) with a field-keyed `null` FieldError instead of "An unexpected error occurred."
- [ ] 94. The package's 231 `except BaseException` guards follow two postures: about 90 hostile-metadata guards turn a
  `KeyboardInterrupt` / `SystemExit` into a typed error (pinned, e.g. `serializer_field_description`), while `utils/directives.py`
  and the await-side guards let control signals propagate (pinned the other way). No upstream library converts them at
  configuration time. One policy (re-raise control signals first, or narrow to `Exception`), or keep the split?
- [ ] 96. CHANGELOG entry for item 95: a nested keyset connection over a type whose `get_queryset` or manager orders pages and
  mints cursors under that order, so its cursors now replay on the root connection
- [ ] 98. CHANGELOG entry for item 51: an `OrderSet` over a forward `ForeignObject` orders it by every carrier column (a
  multi-column link no longer errors) and `Meta.fields = "__all__"` publishes the `ForeignObject` leaf
- [ ] 102. CHANGELOG entry for item 99: a connection over a type whose `get_queryset` or manager returns a `.reverse()`d
  queryset pages every row once and its cursors replay, root and nested; the order served is unchanged, an `orderBy:` beside
  such a hook stays inverted (Django `order_by()` semantics)
- [ ] 104. CHANGELOG entry for item 56: a `SerializerMutation` whose serializer has two writable fields writing one model
  field through an alias (`source="category_id"` beside `category`, `source="pk"` beside the pk field) now raises
  `ConfigurationError` at class creation, and again at runtime when `get_fields()` adds the alias
- [ ] 105. CHANGELOG entry for item 80: a connection whose source or model ordering raises (a project `QuerySet` whose `query`
  raises, a related manager on an unusable pk, a non-iterable `Meta.ordering`) is masked with the policy message and a
  `correlationId` instead of a `GraphQLError` naming the exception class
- [ ] 112. CHANGELOG entry for item 103: a `SerializerMutation` whose serializer binds a writable relation field to its
  `attname` (`source="category_id"`, or a `category_id` `PrimaryKeyRelatedField` with no `source`) now raises
  `ConfigurationError` at schema build; bind the relation instead (`source="category"`)
- [ ] 117. CHANGELOG entry for item 116: under `globalid_strategy="type"` with a `NameConverter` that renames object types,
  ids decode by the schema-published type name; `decode_global_id` and `testing.global_id_for` take an optional `schema=`
  (`global_id_for(..., schema=)` emits the published name and raises `ConfigurationError` for a type the schema does not
  publish), and the inherited-closure `type` child emits the published name
- [ ] 118. CHANGELOG entry for item 81: a `DjangoConnection` subclass whose edge class declares its own `CURSOR_PREFIX` pages
  with its own offset cursors and answers a foreign `arrayconnection:` cursor with the cursor error; stock connections are
  unchanged
- [ ] 129. CHANGELOG entry for item 87: a ModelForm mutation whose form declares a choice field narrower than its column
  publishes a generated enum of only the column values the form admits (static choices; callable and `__init__`-assigned
  choices keep the column enum), and a field admitting none of the column's non-empty values, or a `MultipleChoiceField`
  over a single-value choice column, raises `ConfigurationError` at schema build
- [ ] 134. CHANGELOG entry for item 106: a `SerializerMutation` writing a `ForeignKey(to_field=...)` through a declared
  `PrimaryKeyRelatedField` now saves (every non-null create and update was a masked error); a validator, nested write or
  custom `create()` / `update()` that re-points a validated relation's stored key is refused with `ConfigurationError`
- [ ] 136. CHANGELOG entry for item 88: a lone surrogate anywhere in a list or `JSON` input value (an element, a dict key or
  value, any depth) is a field-keyed `invalid` error at decode, keyed to the leaf's dotted path (`tags.1`; a bad dict key to
  the dict); a `JSON` value carrying one is refused on every backend, and a serializer `ListField(child=CharField())` element
  gets the package's message instead of DRF's
- [ ] 138. CHANGELOG entry for item 130: a model `DjangoMutation` or register mutation writing a `ForeignKey(to_field=...)`
  / `OneToOneField(to_field=...)`, or an M2M whose through model keys the target by a `to_field`, stores the key of the row
  its id names (it stored the pk: a wrong row, or a payload error); a visible row whose `to_field` key is `NULL` is the
  relation error
- [ ] 214. CHANGELOG entry for item 131: a `ModelForm` update omitting a declared `ModelChoiceField` without
  `to_field_name` over a `ForeignKey(to_field=...)` / `OneToOneField(to_field=...)` keeps the stored relation (it failed
  "Select a valid choice", or re-linked the row whose pk equals the stored key); an omitted generated relation field no
  longer reads the related row
- [ ] 215. CHANGELOG entry for item 61: through a `RelatedFilter` cycle each filter set publishes the same flat filters
  whichever type is registered first (a flat path ends at the first set it reaches twice); flat filter inputs on cycle
  members grow (fakeshop: +965 flat fields), none is removed
- [ ] 218. CHANGELOG entry for item 63: an offset `after` cursor near `sys.maxsize` serves the empty past-the-end page under
  `first: N`, `last: 0` or no page argument on every source (one index per page size, and on a generator source every
  index past it, raised a masked unexpected error); a page cap of `sys.maxsize` serves its rows with no page argument
- [ ] 223. CHANGELOG entries for items fixed before an entry was filed with each fix (each changes 0.0.14 behaviour;
  confirm each against the tag when writing): 2 (a negative or malformed offset cursor is refused and no longer bypasses
  the page cap), 4 (a filter lookup binds to its own filter when declared and generated names overlap), 5 (a serializer
  list's elements follow the child's `allow_null`), 13 (a consumer `Prefetch` hint over a type whose `get_queryset` hides
  rows is scoped by that hook), 30 and 31 (a flat `RelatedFilter` leaf, and a relation no `RelatedFilter` declares, no
  longer return rows the target type hides), 32 (`orderBy` through a relation no longer sorts by rows the target type
  hides), 34 (a `RelatedFilter` whose target model its relation does not reach raises at expansion), 35 (a serializer
  choice field admitting a value the column's read enum cannot represent raises `ConfigurationError` at build), 36 (a
  serializer `MultipleChoiceField` over a single-value choice column is refused at build), 38 (a `Choices.__empty__` enum
  no longer carries a `_None` member), 58 (a fragment spread is charged against `max_selections`, and only the selected
  operation's walk expands) and 60 (one `OrderSet` on two types is refused when either hides rows)
- [ ] 196. CHANGELOG entries for items 6 (combined querysets served as their pk set), 12 (the deadline message reads "before
  this field reached the database"; login, logout, me and `relay.node()` reject past the deadline), 50 and 83 (planned
  `.only()` writers no longer drop selected columns), 74 (a consumer `select_related` the selection never reads no
  longer errors), 15 (a hand-built range filter value that is not a `start` / `end` mapping or input object raises
  `ConfigurationError` instead of filtering nothing), 16 (a form field basis value whose `__class__` raises is reported
  as an invalid field in `ConfigurationError`) and 17 (`register_mutation()` names a protected field declared as a `str`
  subclass by its value; `DjangoMutationField` refuses a class drained by `registry.clear()` even when it compares equal
  to its redeclaration) and 18 (`OptimizerHint` prefetch and strategy values, `nested_connection_strategy=`,
  `NESTED_CONNECTION_STRATEGY` and `strictness=` values whose `__class__` raises or claims `str`, and lazy proxies of a
  strategy or strictness name, raise the typed error instead of a raw `RuntimeError` / `TypeError`) and 19 (a kept
  serializer input field named by a non-identifier or a keyword is refused at class creation instead of a raw `SyntaxError`
  at finalize; serializer hook values whose `__class__` raises are typed; lazy proxies and `__class__` spoofs in hook data
  fail the frozen view closed; a non-`str` `context["write_alias"]` is a conflict)
- [ ] 197. The per-parent visibility paths (`types/resolvers.py::_visible_many_rows`, `_visible_related_object`, relation
  connections, `resolver=`) never narrow the hook's result to the source's rows, so a hook that ignores its input shows other
  parents' rows or the wrong to-one object. Decide the contract (narrow at the five seams, with a live row for an
  input-ignoring hook)
- [ ] 198. Under strictness `"raise"`, a backward keyset page whose hook order cannot anchor a cursor reports the N+1 error
  instead of the keyset error; decide and state it in spec-033 and GLOSSARY
- [ ] 199. A nested keyset window given a cursor minted under a third order calls the target `get_queryset` hook one extra
  time on the error path (same query count and error as before); accept or fix
- [ ] 200. After item 14, a list with one valid member gives the wrong answer in two grid cells; pin the contract, then fix or
  record it
- [ ] 201. C57 choices awaiting your ruling: `schema=` stays optional; under a swap converter four cross-schema cells stay wrong
  (documented); an ambiguous unpublished plain type name now refuses where it was accepted. Accept or change
- [ ] 202. Failability rows that each kill a mutant with one row only: C3+C4 mutants 4, 5, 7 and 8 (8 only by a 30 s timeout),
  C57's rebased run at 1 of 10 entries, three precedence mutants graded weakly pinned. Accept or add rows
- [ ] 203. Fold the implementer notes into START.md: items 14 and 83, C11, C46, C57 and C3+C4 (plan-to-resolver channels key
  by `resolver_key`, never `to_attr`; a nested window under the async view needs an async `DjangoConnectionField` root; a
  harness written against a prototype API fails as a `TypeError` that reads as a regression; a subprocess test that signals
  before its syscall flakes)
- [ ] 204. Dive-3 HIGH (a consumer `Prefetch` hint over a hiding target bypassed its `get_queryset`, fixed as item 13): decide
  disclosure and give SECURITY.md a path for a maintainer-found finding; 0.0.14 is affected (its
  `optimizer/walker.py::_apply_hint` installs the consumer `Prefetch` queryset and marks the relation planned)
- [ ] 205. Upstream Strawberry: interface `resolve_type` looks Node-subclass instances up by raw name, so a converter that
  renames interfaces breaks their GlobalIDs; `ConnectionExtension` runs the resolver before `SliceMetadata` validates
  `first` / `last` (context #4510). File upstream or record as known gaps
- [ ] 206. spec-045 was amended in place with no new card, while card 045 asks a numbered security decision for such changes
- [ ] 207. Earlier open questions with no row: nullable payloads (card 056), and the HUNT negative-offset cursor fix on
  list sources being off by one (the `FieldError.field` name was settled by item 11; items 1 and 51 support a multi-column
  `ForeignObject`, the reverse fallback kept)
- [ ] 216. A dense `RelatedFilter` graph publishes a flat surface factorial in its size (path-relative expansion over every
  simple path: six sets each related to every other give about 11k flat keys per set, seven about 94k); decide a stated
  bound or a per-declaration opt-out of flat copies
- [ ] 217. A subclass of a `FilterSet` in a `RelatedFilter` cycle publishes one lap more than its parent (the cycle closes at
  the parent class, not the subclass); decide whether a subclass should close the cycle at itself
- [ ] 219. Strawberry's own `ListConnection` (0.327.7 and 0.334.4) fails `assert last is not None` when `after + 1 + first`
  equals `sys.maxsize` (its `SliceMetadata` last-only sentinel) and overruns `islice`'s stop past it on an iterator source;
  the package now keeps its pages clear of both. Report it upstream?

## Hunt not finished in t3

- [ ] 29. The hunt's final test gate was never run (the Postgres and sharded runs included)
- [ ] 208. t3 is behind main (0 ahead, 106 behind at `8ca6a481`): a file-by-file sync (overlapping `8d4f66bd`) is due, its dive-3 BLOCKED
  text purge and hunt-doc edit are uncommitted, it still carries the superseded refuse-combined patch, and two of its test
  pairs assert opposite outcomes (a hostile `__eq__` drift check; a hostile file replacement). Then decide removing the
  dry-0015 worktree, `~/t3code-1cc21548-pre-ff.tgz` and, after item 114 lands, `refs/scratch/admission-wip`
- [ ] 209. The hunt's owned-changes ledger misses `field_name_map` and `check_deadline`, six files and the dive-5 pins;
  `filters/inputs.py` and the two-lookup raise are behaviour changes filed as robustness; eight items from the hunt's
  test-run notes were never folded back
- [ ] 210. The truthful-reads migration and its fixes sit uncommitted in the hunt worktree; decide whether it and the
  remaining robustness rows (items 20-25, 27) go to main
- [ ] 211. A repo-wide `ruff check --fix .` / `ruff format .` rewrote 30 untracked `.py` files of hunt evidence (11 in the
  sealed deep-3 directory) with no copy kept; evidence trees need excluding from ruff, or AGENTS rule 17 needs explicit paths

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
