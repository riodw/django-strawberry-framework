# Bug hunt 0.0.15 (2): to-do list

Every finding from the 0.0.15 hunt in the t3 worktree (never merged), plus bugs found while fixing them.
Each one is verified on main, fixed at the root, checked by a second agent, landed, then deleted from t3.

Progress: 55 done, 81 to do.

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
  raise `PaginationArgumentError` themselves and nothing rewraps a foreign exception (`41969bc3`)
- [x] 12. Nested forward-FK / OneToOne resolvers never checked the request deadline; every package seam that reaches the database
  now checks it first, which also covers the session-auth `login` / `logout` / `me` fields and the `resolve_node` /
  `resolve_nodes` defaults Strawberry's `relay.node()` reaches (`8d4f66bd`)
- [x] 14. `in: []` matched every row on every generated `in` except GlobalID and relation keys (35 families: integer, text,
  choice, date/time/UUID/decimal, FK-id paths, nested branches, nested connection arguments), and a logical arm that constrained
  nothing was TRUE (`not: {}` no rows, `or: [{}, real]` every row). Now `[]` is the empty set as in Django, strawberry-django and
  graphene-django, an inert arm is `Q()`, a raw `?x__in=` keeps django-filter's no-constraint rule (`e09b5ef1`)
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
  says inputs follow the converter): Rio's 2026-09-25 decision already homes it on `TODO-BETA-077-0.1.7`, no code
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
  attestation compares the column with it (this commit)
- [x] 88. A lone surrogate inside a list element or a JSON key or value skipped the decode text preflight (top-level `str`
  only) and reached the backend raw as a masked top-level `UnicodeEncodeError` (fakeshop `setCardFiles` paths; on Postgres an
  `ArrayField` of text or an `HStoreField` in every write flavor; a serializer `ListField(child=CharField())` element was
  already refused by DRF); the preflight now walks every list element and dict key and value, keyed to the leaf's dotted path
  (`ea0eea70`)
- [x] 130. A model `DjangoMutation` (and register) wrote the related pk into a `to_field` relation's column: a wrong row
  linked silently (including one the visibility scope hides) or a payload FieldError, for a FK, a OneToOne and an M2M whose
  through model's target-side foreign key has a `to_field`; the one visibility query now also reads the key the relation
  stores and that key is written (this commit)

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

- [ ] 89. The grouped-choices `ArrayField` refusal tells a list column to "declare a flat ChoiceField", which cannot write a list
- [ ] 90. Nested list-of-choice serializer shapes (`ListField(child=MultipleChoiceField)`, `ListField(child=ListField(child=ChoiceField))`)
  still publish `[[String!]!]`; an enum there needs a deeper element unwrap than item 43's one level
- [ ] 92. A consumer `save()` raising Django's `ValidationError` escapes the ModelForm flavor as a masked top-level error, while the
  serializer flavor maps it into the envelope
- [ ] 97. A `FilterSet` declaring `{"<fo>": ["exact", "isnull"]}` over a forward `ForeignObject` raises django-filter's
  `AssertionError: unrecognized field type ForeignObject` at class creation, where a `ForeignKey` builds `isnull`
- [ ] 100. A random `"?"` order (hook `order_by("?")` or `Meta.ordering = ["?"]`) on an optimized nested offset connection
  raises "Cannot resolve keyword '?' into field" (masked), reversed or not, `first:` or `last:`; the root path serves it
- [ ] 101. `manage.py import_spec_terms --check` fails on spec-020's terms CSV on main (seen at `eb30dd7e`)
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
- [ ] 128. `django_strawberry_framework/testing/relay.py::global_id_for` annotates `schema: Schema | None` with `Schema`
  imported only under `TYPE_CHECKING` and no `from __future__ import annotations`: importing the public module raises
  `NameError` on Python 3.10-3.13 (the floor run of `test_library_api.py` fails at collection; 3.14's lazy annotations hide it)
- [ ] 131. ModelForm: a declared `ModelChoiceField` without `to_field_name` over a `to_field` ForeignKey fails every partial
  update that omits it ("Select a valid choice"): `forms/resolvers.py::_reconstruct_partial_data` refills it with the stored
  `to_field` value while the bound field resolves by pk (its docstring claims the attname is the key the field resolves)
- [ ] 132. A `SerializerMutation` whose `Meta.fields` narrowing keeps a relation to a Relay-Node type fails schema build
  (`TypeError: Mutation fields cannot be resolved. '<...>PartialInput'`), create and update, e.g. `Shelf.branch`; a non-Relay
  target builds
- [ ] 133. A `PrimaryKeyRelatedField` to a model whose pk is a `OneToOneField` (`PatronProfile`) is refused at schema build
  ("Unsupported Django field type 'OneToOneField' on PatronProfile.patron"); a FK to such a model cannot be written by a
  serializer mutation (fails loud)
- [ ] 135. A malformed GlobalID in an `[ID!]` list input (`genres: ["not-base64!!"]`) is a masked top-level error in the
  model, ModelForm and serializer flavors: Strawberry's `convert_argument` raises `GlobalIDValueError` before any package
  decode, where a single malformed id gets the field-keyed envelope
- [ ] 137. ModelForm and serializer flavors: a relation id naming a visible row whose `to_field` key is `NULL` clears an
  optional relation silently (the form binds `None`; the serializer's descriptor assignment stores `NULL`), where the model
  flavor refuses it as the relation error since item 130; `forms/resolvers.py::_to_form_key_value` also falls back to
  `obj.pk` when `to_field_name` does not resolve on the row

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
- [ ] 46. Postgres: `ListField(child=ChoiceField)` over an `ArrayField` is refused (parked: needs a Postgres run)
- [ ] 47. Postgres: `serializer_choice_field=MultipleChoiceField` over an `ArrayField` is unusable (parked: needs a Postgres run)
- [ ] 93. CHANGELOG entry for item 44: a ModelForm mutation over a non-text choice column with `blank=True, null=False` answers
  `null` (or an omitted field with no default) with a field-keyed `null` FieldError instead of "An unexpected error occurred."
- [ ] 94. The package's 228 `except BaseException` guards follow two postures: about 90 hostile-metadata guards turn a
  `KeyboardInterrupt` / `SystemExit` into a typed error (pinned, e.g. `serializer_field_description`), while `utils/directives.py`
  and the await-side guards let control signals propagate (pinned the other way). No upstream library converts them at
  configuration time. One policy (re-raise control signals first, or narrow to `Exception`), or keep the split?
- [ ] 96. CHANGELOG entry for item 95: a nested keyset connection over a type whose `get_queryset` or manager orders pages and
  mints cursors under that order, so its cursors now replay on the root connection; `DeclaredCursorState` is renamed `CursorState`
- [ ] 98. CHANGELOG entry for item 51: an `OrderSet` over a forward `ForeignObject` orders it by every carrier column (a
  multi-column link no longer errors), `Meta.fields = "__all__"` publishes the `ForeignObject` leaf, and naming a reverse
  `GenericRel` in a `DjangoMutation`'s `fields` / `exclude` raises the unknown-field error instead of the `ForeignObject` one
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

## Hunt not finished in t3

- [ ] 29. The hunt's final test gate was never run

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
